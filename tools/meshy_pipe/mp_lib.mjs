// Meshy 이미지→3D 파이프 공용 도구. ★이름 충돌 방지로 전부 mp_ 접두어.
//
// 방식(중요): 세션 공유 Playwright MCP 도 오너 크롬도 쓰지 않는다. MCP 프로필을 복제한
// **독립 크롬**을 mp_open.mjs 가 띄워 두고(원격 디버깅 포트), 단계 스크립트들은
// connectOverCDP 로 그 창에 붙었다 떨어진다. 브라우저를 매번 새로 띄우면
// Meshy 의 무거운 WebGL 워크스페이스를 매번 다시 로드해야 해서 느리고 잘 깨진다.
//
// 돌리는 법
//   1) node tools/meshy_pipe/mp_open.mjs &     # 창을 띄우고 살려 둔다
//   2) node tools/meshy_pipe/mp_probe.mjs      # 붙어서 상태를 읽는다
import { chromium } from '/Users/lbj/Documents/real-estate-agent/node_modules/playwright/index.mjs';

export const PROFILE = '/Users/lbj/Library/Caches/ms-playwright-mcp/meshy-clone-0813';
export const CDP = 'http://127.0.0.1:9333';
export const WORKSPACE = 'https://www.meshy.ai/ko/workspace?model-tab=image';
export const ROOT = '/Users/lbj/Documents/gameproject';
export const SRC_DIR = ROOT + '/incoming/codex_dgprops';
export const OUT_DIR = ROOT + '/incoming/meshy_dgprops';
export const LOG_DIR = ROOT + '/renders/history/v99_wave16/meshy_log';

export const PROPS = ['pillar_intact', 'pillar_broken', 'arch_gate', 'altar', 'brazier',
  'rubble_large', 'rubble_small', 'coping_chunk', 'quoin_corner'];

export const sleep = ms => new Promise(r => setTimeout(r, ms));

// 열려 있는 창에 붙는다. 페이지가 여럿이면 meshy.ai 를 고른다.
export async function attach() {
  const b = await chromium.connectOverCDP(CDP);
  const ctx = b.contexts()[0];
  const pages = ctx.pages();
  let page = pages.find(p => p.url().includes('meshy.ai')) || pages[0];
  if (!page) page = await ctx.newPage();
  return { b, ctx, page };
}

// 크레딧 잔액. ★생성 버튼 클릭의 유일한 영수증이다(LOG.md: 클릭 삼킴 → 연타 금지).
//   헤더의 data-testid=header-credit-btn 하나만 본다(옆 알림 뱃지 "11" 을 크레딧으로
//   오독한 사고가 있었다 - 좌표나 "top 근처 숫자" 같은 헐거운 규칙 금지).
export async function credits(page) {
  return await page.evaluate(() => {
    const el = document.querySelector('[data-testid=header-credit-btn]');
    if (!el) return null;
    const m = (el.textContent || '').replace(/[^0-9,]/g, '').replace(/,/g, '');
    return m ? Number(m) : null;
  });
}

// 화면 텍스트 덤프(스크린샷이 타임아웃 나는 무거운 사이트라 이게 1차 관측 수단).
export async function dump(page, sel = 'body') {
  return await page.evaluate((s) => {
    const root = document.querySelector(s);
    if (!root) return '(없음)';
    const out = [];
    const walk = (el, d) => {
      for (const c of el.children) {
        const own = [...c.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).filter(Boolean).join(' ');
        const r = c.getBoundingClientRect();
        if (own && r.width > 0 && r.height > 0) {
          out.push(`${' '.repeat(Math.min(d, 8))}[${c.tagName.toLowerCase()}${c.getAttribute('role') ? '/' + c.getAttribute('role') : ''}] ` +
            `(${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}x${Math.round(r.height)}) ${own.slice(0, 90)}`);
        }
        if (d < 40) walk(c, d + 1);
      }
    };
    walk(root, 0);
    return out.join('\n');
  }, sel);
}

// 스크린샷. WebGL 로 프리즈하면 예외를 삼키고 null 을 돌려준다(진행을 막지 않는다).
export async function shot(page, name, opts = {}) {
  const path = LOG_DIR + '/' + name + '.png';
  try {
    await page.screenshot({ path, timeout: 25000, ...opts });
    return path;
  } catch (e) {
    console.log('  (스샷 실패: ' + e.message.split('\n')[0] + ')');
    return null;
  }
}

// ─── 화면 조작 3원칙(2026-08-13 사고에서 얻음) ────────────────────────────────
// ① 카드 선택은 **진짜 마우스 클릭**이라야 한다. el.click() 은 리액트가 무시한다
//    (JS 클릭이 먹은 줄 알고 8번을 같은 모델에 텍스처 구워 80cr 을 태웠다).
// ② '텍스처 편집' 전체화면이 떠 있으면 뒤의 모든 클릭이 막힌다. Escape 로는 안 닫힌다 - X 버튼.
// ③ 고른 뒤에는 반드시 **바뀌었는지 확인**한다. 뷰어 하단 썸네일의 uploads/<id> 가 신원이다.

// 뷰어 하단 썸네일에 박힌 "원본 콘셉트 이미지 id". 지금 뷰어가 무엇을 들고 있는지의 유일한 표식.
// ★좌표로 찾지 말 것. 창 크기가 바뀌면 푸터 줄의 y 가 통째로 움직여 신원 확인이 조용히 null 이 된다
//   (브라우저를 다시 띄운 뒤 "자산을 못 찾았다"가 난 원인). src 에 uploads/ 가 박힌 작은 썸네일로 찾는다.
export async function viewerSource(page) {
  return await page.evaluate(() => {
    for (const x of document.querySelectorAll('img')) {
      if (!/\/uploads\//.test(x.src)) continue;
      const r = x.getBoundingClientRect();
      if (r.width === 0 || r.width > 60) continue;          // 큰 것은 왼쪽 생성폼의 미리보기다
      if (r.left < 340 || r.left > 1010) continue;           // 가운데 뷰어 칸
      return (x.src.match(/uploads\/([0-9a-f-]+)\./) || [])[1];
    }
    return null;
  });
}

// 뷰어 아래 도구 막대 글자. '텍스처 +10' 이면 아직 무텍스처 모델, '+50' 이면 이미 텍스처된 것.
export async function barText(page) {
  return await page.evaluate(() => (document.querySelector('[data-testid=viewer-bottom-bar]')?.innerText || '').replace(/\s+/g, ' ').trim());
}

// 전체화면 편집기가 떠 있으면 X 로 닫는다.
export async function closeModal(page) {
  const open = await page.evaluate(() => document.body.innerText.includes('텍스처 편집'));
  if (!open) return false;
  const box = await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      const r = btn.getBoundingClientRect();
      if (r.top > 75 && r.top < 110 && r.left > 1340 && r.width > 20 && r.width < 45) return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
    }
    return null;
  });
  if (box) { await page.mouse.click(box.x, box.y); await sleep(2500); }
  return true;
}

// 좌표를 얻어 진짜로 클릭한다(스크롤이 멈춘 뒤 좌표를 다시 잰다 - 스무스 스크롤 함정).
export async function clickAt(page, boxFn, settle = 1200) {
  await page.evaluate(boxFn.scroll || (() => {}));
  await sleep(settle);
  const box = await page.evaluate(boxFn.rect);
  if (!box) return false;
  await page.mouse.move(box.x, box.y);
  await sleep(400);
  await page.mouse.click(box.x, box.y);
  return true;
}

// 작업 id 로 카드를 골라 뷰어에 띄운다. 바뀐 게 확인될 때까지 기다린다.
//   expect: 그 소품의 원본 이미지 id 를 알고 있으면 넘긴다. 이미 그게 떠 있으면 그대로 인정하고,
//           아니면 "그 값이 될 때까지" 기다린다(막연한 '바뀜'보다 강한 확인).
export async function selectCard(page, taskId, expect = null) {
  const before = await viewerSource(page);
  if (expect && before === expect) return { ok: true, source: before, note: '이미 선택돼 있었다' };
  await page.evaluate((t) => {
    for (const c of document.querySelectorAll('[data-testid=assets-card]')) {
      const img = c.querySelector('img');
      if (img && img.src.includes(t)) { c.scrollIntoView({ block: 'center', behavior: 'instant' }); return; }
    }
  }, taskId);
  await sleep(1500);
  const box = await page.evaluate((t) => {
    for (const c of document.querySelectorAll('[data-testid=assets-card]')) {
      const img = c.querySelector('img');
      if (img && img.src.includes(t)) {
        const r = c.getBoundingClientRect();
        if (r.top < 60 || r.bottom > 1000) return null;
        return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
      }
    }
    return null;
  }, taskId);
  if (!box) return { ok: false, why: '카드를 화면에서 못 찾음' };
  await page.mouse.move(box.x, box.y); await sleep(500);
  await page.mouse.click(box.x, box.y);
  for (let i = 0; i < 15; i++) {
    await sleep(800);
    const now = await viewerSource(page);
    if (expect ? now === expect : (now && now !== before)) return { ok: true, source: now };
  }
  const now = await viewerSource(page);
  return { ok: false, why: '뷰어가 안 바뀜(전 ' + before + ' 후 ' + now + ')', source: now };
}

// ★다운로드는 playwright 의 download 이벤트에만 맡기면 안 된다. connectOverCDP 로 붙었다 떨어지는
//   방식에서는 아티팩트 임시 폴더가 앞 연결의 것이라 파일이 사라져 saveAs 가 ENOENT 로 깨진다
//   (9건 중 8건이 이 이유로 실패했다). 크롬에게 **받을 폴더를 직접 지정**하고 그 폴더를 지켜본다.
export async function setDownloadDir(page, dir) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dir, eventsEnabled: true });
  return cdp;
}

// 폴더에 새로 생긴 파일이 "다 받아졌을 때" 그 경로를 돌려준다(.crdownload 가 사라지고 크기가 멎을 때).
export async function waitNewFile(fs, dir, before, timeoutMs = 300000) {
  const t0 = Date.now();
  let last = -1, stable = 0;
  while (Date.now() - t0 < timeoutMs) {
    const now = fs.readdirSync(dir).filter(f => !before.has(f));
    const done = now.filter(f => !f.endsWith('.crdownload'));
    if (done.length) {
      const p = dir + '/' + done[0];
      const sz = fs.statSync(p).size;
      if (sz > 0 && sz === last) { stable++; if (stable >= 3) return p; } else { stable = 0; }
      last = sz;
    }
    await sleep(1000);
  }
  return null;
}

export function stamp() {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}
