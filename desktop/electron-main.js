// ── 검 게임 데스크톱 껍데기 (Electron 메인 프로세스) ───────────────────────────
//
// 하는 일은 셋뿐이다.
//   1) 게임 파일(game/ = dist/ 복사본)을 127.0.0.1 임의 포트에 정적 서버로 띄운다
//   2) 그 주소를 여는 창 하나를 만든다
//   3) 창 밖으로 나가는 길(외부 요청·새 창·다른 주소 이동)을 전부 막는다
//
// ★왜 file:// 이 아니라 로컬 서버인가
//   게임은 ES 모듈(`<script type="module">`)로 짜여 있고 level.js 는 fetch 로
//   level1.json 을 받는다. file:// 에서는 둘 다 막힌다(모듈은 origin 이 null 이라
//   CORS 위반, fetch 는 file 스킴 거부). 커스텀 프로토콜(app://)로도 되지만
//   모듈 해석·MIME 처리에서 브라우저와 미묘하게 갈릴 수 있다.
//   **로컬 HTTP 서버는 웹에서 돌던 환경과 바이트 단위로 같다.** 웹판과 화질·동작이
//   같아야 한다는 게 이 작업의 전제라 가장 안전한 쪽을 골랐다.
//
// ★포트는 0(운영체제가 빈 포트를 준다). 고정 포트로 두면 다른 프로그램과 부딪히고,
//   두 벌을 동시에 켜면 뒤엣것이 못 뜬다.
//
// ★서버는 127.0.0.1 에만 바인딩한다. 0.0.0.0 으로 열면 같은 와이파이의 남이
//   내 게임 파일을 받아 갈 수 있다.

const { app, BrowserWindow, Menu, shell, session } = require('electron');
const http = require('node:http');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');

// ── 개발 모드 게이트 ───────────────────────────────────────────────────────────
// 웹판의 ?dev 관례를 그대로 옮긴다. 평시 빌드에서는 개발자도구가 아예 없다
// (webPreferences.devTools:false 라 단축키·메뉴·코드 어느 쪽으로도 안 열린다).
//   개발자용으로 열 때: npm run dev   또는   .../검 게임.app/Contents/MacOS/검\ 게임 --dev
const DEV = process.argv.includes('--dev') || process.env.SWORDGAME_DEV === '1';

// 게임 파일 뿌리. asar 안에 있어도 electron 의 fs 가 알아서 app.asar.unpacked 로 돌린다.
const GAME_DIR = path.join(__dirname, 'game');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',   // ★모듈은 이 타입이 아니면 브라우저가 거부한다
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.glb': 'model/gltf-binary',
  '.gltf': 'model/gltf+json',
  '.bin': 'application/octet-stream',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ktx2': 'image/ktx2',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.ttf': 'font/ttf',
  '.otf': 'font/otf',
  '.mp3': 'audio/mpeg',
  '.ogg': 'audio/ogg',
  '.wav': 'audio/wav',
  '.m4a': 'audio/mp4',
  '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

/** 요청 경로를 게임 폴더 안의 실제 파일로 옮긴다. 폴더 밖으로 나가면 null. */
function resolveInside(urlPath) {
  let rel;
  try {
    rel = decodeURIComponent(urlPath.split('?')[0].split('#')[0]);
  } catch {
    return null;
  }
  if (rel === '/' || rel === '') rel = '/index.html';
  // ★경로 탈출 방어. 로컬 전용이라도 열어 둘 이유가 없다.
  const full = path.join(GAME_DIR, path.normalize(rel).replace(/^(\.\.[/\\])+/, ''));
  const rootWithSep = GAME_DIR.endsWith(path.sep) ? GAME_DIR : GAME_DIR + path.sep;
  if (full !== GAME_DIR && !full.startsWith(rootWithSep)) return null;
  return full;
}

/** game/ 를 127.0.0.1 의 빈 포트에 띄우고 주소를 돌려준다. */
function startGameServer() {
  return new Promise((resolve, reject) => {
    const server = http.createServer(async (req, res) => {
      if (req.method !== 'GET' && req.method !== 'HEAD') {
        res.writeHead(405).end();
        return;
      }
      const file = resolveInside(req.url || '/');
      if (!file) {
        res.writeHead(403).end();
        return;
      }
      let stat;
      try {
        stat = await fsp.stat(file);
        if (stat.isDirectory()) {
          stat = await fsp.stat(path.join(file, 'index.html'));
        }
      } catch {
        // ★404 는 조용히 넘기지 않는다. 배포 필터(build_deploy.py)가 glb 하나를
        //   빠뜨리면 여기 찍힌 줄이 유일한 단서다.
        console.warn('[server] 404', req.url);
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('404');
        return;
      }
      const target = stat.isDirectory() ? path.join(file, 'index.html') : file;
      const type = MIME[path.extname(target).toLowerCase()] || 'application/octet-stream';
      const headers = {
        'Content-Type': type,
        'Content-Length': String(stat.size),
        // 설치본은 파일이 안 바뀐다. 그래도 캐시를 안 걸어 둔다 —
        // 재설치·패치 때 옛 파일이 남는 사고가 캐시 이득보다 비싸다(웹판 ?v= 관례와 같은 이유).
        'Cache-Control': 'no-store',
      };
      if (req.method === 'HEAD') {
        res.writeHead(200, headers).end();
        return;
      }
      // Range 요청(오디오·비디오 탐색)은 현재 자산에 없지만 들어와도 안 깨지게 받아 둔다.
      const range = req.headers.range;
      if (range) {
        const m = /^bytes=(\d*)-(\d*)$/.exec(range);
        if (m) {
          const start = m[1] ? parseInt(m[1], 10) : 0;
          const end = m[2] ? parseInt(m[2], 10) : stat.size - 1;
          if (start < stat.size && end < stat.size && start <= end) {
            res.writeHead(206, {
              ...headers,
              'Content-Length': String(end - start + 1),
              'Content-Range': `bytes ${start}-${end}/${stat.size}`,
              'Accept-Ranges': 'bytes',
            });
            fs.createReadStream(target, { start, end }).pipe(res);
            return;
          }
        }
      }
      res.writeHead(200, headers);
      fs.createReadStream(target).pipe(res);
    });

    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ server, origin: `http://127.0.0.1:${port}` });
    });
  });
}

let mainWindow = null;
let gameOrigin = '';

/** 창 밖으로 나가는 길을 전부 막는다(오프라인 보증 + 최소한의 방어). */
function lockDown() {
  const ses = session.defaultSession;

  // ①외부로 나가는 요청 차단. 게임 자산은 전부 로컬이라 정상 동작에서는 한 건도 안 걸린다.
  //   걸리는 줄이 있으면 그게 곧 "밖으로 새는 자산"이라는 증거다.
  ses.webRequest.onBeforeRequest((details, cb) => {
    const u = details.url;
    const ok =
      u.startsWith(gameOrigin) ||
      u.startsWith('devtools://') ||
      u.startsWith('blob:') ||
      u.startsWith('data:') ||
      u.startsWith('chrome-extension://');
    if (!ok) {
      console.warn('[net] 외부 요청 차단:', u);
      cb({ cancel: true });
      return;
    }
    cb({});
  });

  // ②권한(카메라·위치·알림 등) 전부 거절. 게임은 아무것도 안 쓴다.
  ses.setPermissionRequestHandler((_wc, _perm, cb) => cb(false));
  ses.setPermissionCheckHandler(() => false);
}

function buildMenu() {
  const isMac = process.platform === 'darwin';
  const viewSub = [
    {
      // ★F11 은 윈도우 관례, Ctrl+Cmd+F 는 맥 관례다. 둘 다 받는다.
      label: '전체화면',
      accelerator: isMac ? 'Control+Command+F' : 'F11',
      click: () => mainWindow && mainWindow.setFullScreen(!mainWindow.isFullScreen()),
    },
    { type: 'separator' },
    { label: '창 크기 되돌리기 (1280×800)', click: () => {
      if (!mainWindow) return;
      mainWindow.setFullScreen(false);
      mainWindow.unmaximize();
      mainWindow.setSize(1280, 800);
      mainWindow.center();
    } },
  ];
  if (DEV) {
    viewSub.push(
      { type: 'separator' },
      { role: 'reload', label: '다시 불러오기' },
      { role: 'toggleDevTools', label: '개발자 도구' },
    );
  }

  const template = [];
  if (isMac) {
    template.push({
      // ★app.name 을 쓰면 'SwordGame' 이 뜬다(패키지 이름은 ASCII 로 묶여 있다 —
      //   한글로 두면 맥 빌드가 죽는다. package.json 의 주의 문구 참고).
      //   사람이 보는 이름은 여기서 못 박는다.
      label: '검 게임',
      submenu: [
        { role: 'about', label: '검 게임 정보' },
        { type: 'separator' },
        { role: 'hide', label: '가리기' },
        { role: 'hideOthers', label: '다른 앱 가리기' },
        { type: 'separator' },
        { role: 'quit', label: '종료' },
      ],
    });
  }
  template.push({ label: '보기', submenu: viewSub });
  if (!isMac) {
    template.push({ label: '파일', submenu: [{ role: 'quit', label: '종료' }] });
  }
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 800,
    minHeight: 540,
    // 첫 프레임 전까지 흰 판이 번쩍이면 안 된다. index.html 의 바탕과 같은 남색으로 채운다.
    backgroundColor: '#0b1024',
    title: '검 게임',
    show: false,
    autoHideMenuBar: true,          // 윈도우·리눅스: 메뉴바 숨김(Alt 로 잠깐 보임)
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      devTools: DEV,                // ★평시 빌드에서는 개발자도구 자체가 없다
      backgroundThrottling: false,  // 창을 가려도 게임 루프가 안 늘어지게
    },
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    // ★게임은 켜자마자 앞으로 나와야 한다. 파인더에서 더블클릭하면 저절로 그렇게 되지만
    //   터미널·스크립트로 켜면 뒤에서 조용히 떠서 "안 켜졌다" 로 읽힌다.
    app.focus({ steal: true });
    mainWindow.focus();
    // 창 위치·크기를 한 줄 남긴다. 설치본에는 개발자도구가 없어서
    // 화면 문제(잘림·엉뚱한 자리)를 물어볼 때 이 줄이 유일한 좌표 단서다.
    console.log('[window]', JSON.stringify(mainWindow.getBounds()));
  });

  // 새 창·외부 링크는 앱 안에서 열지 않는다(기본 브라우저로 넘기지도 않는다 — 열 링크가 없다).
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  // 게임 주소 밖으로 이동 금지.
  mainWindow.webContents.on('will-navigate', (e, url) => {
    if (!url.startsWith(gameOrigin)) e.preventDefault();
  });

  // F11 은 맥에서도 눌리는 사람이 있다. 메뉴 가속기와 별개로 한 번 더 받는다.
  mainWindow.webContents.on('before-input-event', (e, input) => {
    if (input.type !== 'keyDown') return;
    if (input.key === 'F11') {
      e.preventDefault();
      mainWindow.setFullScreen(!mainWindow.isFullScreen());
    }
  });

  // 렌더러 콘솔을 메인 콘솔로 끌어올린다. 설치본에서 개발자도구가 없으니
  // 터미널에서 켜면(`검 게임.app/Contents/MacOS/검 게임`) 이 줄로 상태를 본다.
  // ★console-message 는 electron 버전에 따라 인자 모양이 둘이다(옛: level,message / 새: 이벤트객체).
  //   둘 다 받아 둔다. 여기서 터지면 콘솔 검증 자체를 못 한다.
  mainWindow.webContents.on('console-message', (...args) => {
    const e = args[0];
    const lv = e && e.level !== undefined ? e.level : args[1];
    const msg = e && e.message !== undefined ? e.message : args[2];
    const name = typeof lv === 'number' ? (['debug', 'info', 'warning', 'error'][lv] || lv) : lv;
    console.log(`[renderer:${name}] ${msg}`);
  });
  mainWindow.webContents.on('render-process-gone', (_e, d) => {
    console.error('[renderer] 죽음:', d.reason, d.exitCode);
  });

  // ★쿼리는 안 붙인다. 웹판의 ?dev 게이트가 그대로 살아 있어야 평시 로스터(검사 1명)가 뜬다.
  //   개발 모드에서만 ?dev 를 붙여 로스터·미리보기·품질 조절을 연다.
  mainWindow.loadURL(gameOrigin + '/index.html' + (DEV ? '?dev' : ''));
}

// GPU 관련: 기본값 그대로 둔다. 웹판(크롬)과 같은 경로로 돌아야 화질이 같다.
app.whenReady().then(async () => {
  try {
    const started = await startGameServer();
    gameOrigin = started.origin;
    console.log('[server]', gameOrigin, '←', GAME_DIR);
  } catch (err) {
    console.error('[server] 못 띄움:', err);
    // 서버가 안 뜨면 게임도 못 뜬다. file:// 폴백은 어차피 모듈에서 막히니 여기서 끝낸다.
    app.quit();
    return;
  }
  lockDown();
  buildMenu();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  // 맥이라도 창을 닫으면 끝낸다. 게임 하나짜리 앱이 독에 남아 있을 이유가 없다.
  app.quit();
});
