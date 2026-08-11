# 설치형 데스크톱 앱 (Electron)

웹게임을 브라우저 없이 **더블클릭으로 켜는 앱**으로 감싼 것이다.
게임 내용·화질은 웹판과 **같다**(같은 `dist/` 를 그대로 담는다. 압축·축소 단계가 없다).

    맥    desktop/out/mac-arm64/검 게임.app        ·  desktop/out/sword-game-0.1.0-mac-arm64.dmg
    윈도우 desktop/out/sword-game-0.1.0-win-x64-setup.exe  ·  ...-win-x64.zip

---

## 굽는 법

    python3 tools/build_desktop.py             # 맥 .app + .dmg
    python3 tools/build_desktop.py --win       # 윈도우 설치본 + zip
    python3 tools/build_desktop.py --all       # 둘 다
    python3 tools/build_desktop.py --dir       # 포장 없이 .app 만(빠름)
    python3 tools/build_desktop.py --skip-web  # dist/ 재생성 없이 지금 dist 를 담는다

공정은 셋이다.

1. `tools/build_deploy.py` 로 `dist/` 를 굽는다 — **웹 배포와 같은 파이프라인이다.**
   웹에 올라간 것과 앱에 든 것이 갈리지 않게 하려고 통로를 하나로 뒀다.
2. `dist/` → `desktop/game/` 으로 복사한다(`.vercel`·`vercel.json` 같은 배포 설정만 뺀다).
3. `desktop/` 에서 electron-builder 를 돌린다 → `desktop/out/`.

`--skip-web` 은 **web/ 를 누가 고치는 중일 때** 쓴다. dist 를 다시 구우면 남의 미완성 코드가
앱에 실린다. 지금 dist 가 성한 걸 알면 `--skip-web` 이 안전하다.

개발 중에는 굽지 말고 그냥 켜는 게 빠르다.

    cd desktop && npm start        # 지금 desktop/game/ 을 그대로 띄운다
    cd desktop && npm run dev      # ?dev 게이트 켜짐(로스터 전체·개발자도구·미리보기)

---

## 구조

    desktop/
      package.json        electron·electron-builder 버전 + 패키징 설정
      electron-main.js    메인 프로세스(로컬 서버 + 창 + 바깥길 차단)
      build/              아이콘(icon.icns / icon.ico / icon.png) ← 저장소에 넣는다
      game/               dist/ 복사본 ← .gitignore
      node_modules/       ← .gitignore
      out/                산출물 ← .gitignore

### 왜 file:// 이 아니라 로컬 서버인가

게임은 ES 모듈로 짜여 있고 `level.js` 는 `fetch('./level1.json')` 을 쓴다.
`file://` 에서는 둘 다 막힌다(모듈은 origin 이 null 이라 CORS 위반, fetch 는 file 스킴 거부).
그래서 메인 프로세스가 **127.0.0.1 의 빈 포트**(`listen(0)`)에 게임 폴더를 정적 서버로 띄우고
그 주소를 창에 물린다. 커스텀 프로토콜(`app://`)도 되지만 모듈 해석·MIME 이 브라우저와
미묘하게 갈릴 수 있다. **로컬 HTTP 는 웹에서 돌던 환경과 바이트 단위로 같다** — 화질·동작이
웹판과 같아야 한다는 게 전제라 안전한 쪽을 골랐다.

포트는 고정하지 않는다(고정하면 다른 프로그램과 부딪히고 두 벌을 못 켠다).
바인딩은 `127.0.0.1` 뿐이라 같은 와이파이의 남이 파일을 받아 갈 수 없다.

### 바깥으로 나가는 길은 다 막았다

- `webRequest.onBeforeRequest` — 게임 주소·`blob:`·`data:` 말고는 **전부 취소**하고 콘솔에 적는다.
  게임 자산이 전부 로컬이라 정상 동작에서는 한 건도 안 걸린다. 걸리는 줄이 있으면 그게 곧
  "밖으로 새는 자산" 이라는 증거다.
- `setWindowOpenHandler` / `will-navigate` — 새 창·다른 주소 이동 금지.
- 권한 요청(카메라·위치·알림) 전부 거절.
- `contextIsolation: true` · `nodeIntegration: false` · `sandbox: true` — 게임 코드에 node 권한이 없다.
- `devTools: false` — **평시 빌드에는 개발자 도구가 아예 없다**(단축키·메뉴·코드 어느 쪽으로도 안 열린다).
  `--dev` 를 주면 열린다. 웹판 `?dev` 관례를 그대로 옮긴 것이고, `--dev` 일 때만 게임도 `?dev` 로 연다.

### 창

1280×800 으로 뜨고 최소 800×540. 리사이즈된다.
전체화면은 **F11**(윈도우 관례)과 **Ctrl+Cmd+F**(맥 관례) 둘 다 받는다. 메뉴 `보기` 에도 있다.
메뉴는 최소한만 둔다(맥: 앱 메뉴 + 보기 / 윈도우: 보기 + 파일, `autoHideMenuBar`).
`보기 > 창 크기 되돌리기` 로 1280×800 가운데로 복귀한다.

---

## 확인한 것 (2026-08-12, MacBook Pro M1 / macOS 15.7.3)

| 항목 | 결과 |
|---|---|
| 부팅 | `검 게임.app` 더블클릭 → 로딩 → 1층 시작. 게임 화면 정상 |
| 전투 | 방향키 이동 · Z 3연타 · X 수면참 · C 횡일섬 · R 재시작 전부 동작 |
| 콘솔 | JS 에러 0 · 미처리 예외 0 · `console.error` 0 |
| 네트워크 | 요청 100건 = `127.0.0.1:<포트>` 68 + `blob:` 32. **외부 호스트 0건** |
| 창 | 1280×772 ↔ 전체화면 1440×900 (캔버스 1920×1158 ↔ 2160×1350) 왕복 정상 |
| dmg | 마운트 → `검 게임.app` + Applications 심볼릭 링크. 서명 검증 통과 |

용량

    맥    검 게임.app                          332 MB
          sword-game-0.1.0-mac-arm64.dmg       157 MB
    윈도우 win-unpacked/                        411 MB
          sword-game-0.1.0-win-x64-setup.exe   135 MB   (NSIS 설치본)
          sword-game-0.1.0-win-x64.zip         174 MB   (무설치)

게임 자산은 54 MB 다. 나머지는 Electron 런타임(크로미움)이다. 웹은 이걸 브라우저가
이미 갖고 있어서 안 세지만 설치형은 같이 들고 다닌다 — 스팀 게임이 다 그렇다.

네트워크 검증은 `--remote-debugging-port` 로 붙어 `Network.requestWillBeSent` 를 전부 받아 적었다.
`blob:` 32건은 three.js `GLTFLoader` 가 glb 안의 텍스처를 꺼내며 만드는 것이고(`createObjectURL`
→ 곧바로 `revokeObjectURL`), 그래서 `ERR_ABORTED` 로 끝난다. 웹판에서도 똑같이 난다.
폰트도 자산도 전부 앱 안에 있어서 **랜선을 뽑아도 그대로 돈다.**

기록: `renders/history/v99_wave13/desktop/` (창모드·전체화면·전투·재시작 스크린샷, 네트워크 보고)

---

## ★함정

### 앱 이름을 한글로 두면 맥 빌드가 실행 즉시 죽는다

`build.productName` 을 `"검 게임"` 으로 두면 `.app` 은 멀쩡히 만들어지는데
**켜자마자 SIGTRAP(exit 133)으로 죽는다.** 그것도

- 콘솔에 한 줄도 안 남고 (`--enable-logging` 을 줘도 로그 파일조차 안 생긴다)
- `app.whenReady()` 전에 죽어서 내 코드가 손댈 구석이 없고
- 크래시 리포트에는 `EXC_BREAKPOINT` 만 찍혀서 원인이 안 보인다.

원인은 **`CFBundleName` 이 ASCII 가 아니면 안 된다**는 것이다(크로미움이 이 값으로
헬퍼 프로세스 경로를 만든다). 서명·asar 무결성은 무고하다 — 둘 다 껐다 켜 보며 확인했다.
실험으로 좁힌 결과:

    CFBundleName 한글 + 헬퍼 한글  →  죽음
    CFBundleName 한글 + 헬퍼 ASCII →  죽음      ← 헬퍼 이름은 범인이 아니다
    CFBundleName ASCII + CFBundleDisplayName 한글 → 산다

그래서 지금 구조는 이렇다.

    productName            SwordGame          (CFBundleName·실행파일·헬퍼 = ASCII)
    mac.extendInfo         CFBundleDisplayName = "검 게임"
    빌드 마지막            SwordGame.app -> 검 게임.app 로 **번들 이름만** 바꾼다
    dmg 단계               -c.productName=검 게임 로 dmg 안 이름도 한글로

번들 폴더 이름은 서명에 안 묶여 있어서 바꿔도 `codesign --verify` 가 통과한다.
파인더·독·창 제목·앱 메뉴 전부 「검 게임」으로 보인다.

### 서명을 안 붙이면 arm64 맥에서 안 뜬다

electron-builder 는 인증서가 없으면 서명을 건너뛴다(`skipped macOS application code signing`).
그 상태로 두면 **dmg 로 옮겨 받은 쪽에서** 게이트키퍼에 걸린다. 그래서 빌드 스크립트가
`codesign --force --deep --sign -` 로 ad-hoc 서명을 직접 붙이고 `--verify --deep --strict`
로 확인한다. **dmg 를 말기 전에** 붙여야 dmg 안엣것도 성하다(그래서 맥은 2단 빌드다).

로컬 실행에는 ad-hoc 로 충분하다. 남에게 배포하거나 스팀에 올릴 때는 정식 서명·공증이 필요하다(아래).

### 그 밖에

- **`asar` 는 켜 두되 `game/**` 은 unpack 한다.** 게임 자산 54MB 를 asar 안에 넣어도 돌긴 하지만,
  꺼내 두면 앱 속을 열어 파일을 직접 확인할 수 있다(사고 났을 때 이게 크다).
- **stdout 이 안 보인다.** 설치본에는 개발자 도구가 없으니 상태를 보려면 터미널에서 켜라.
  `open -a "검 게임.app" --stdout /tmp/o --stderr /tmp/e` 또는 실행 파일을 직접 부른다.
- **터미널에서 켜면 창이 뒤에 뜬다.** `open -a` 로 켜면(=런치서비스를 거치면) 앞으로 나온다.
  스크립트로 켜고 스크린샷을 찍을 때 이걸로 몇 번 헛짚었다.
- `fs.Stats constructor is deprecated` 경고 한 줄이 stderr 에 뜬다. Electron 의 asar 계층이
  Node 26 에서 내는 것이고 게임과 무관하다.

---

## 윈도우

이 맥에서 교차 빌드한다. electron-builder 가 NSIS 를 **맥용 바이너리로 받아 쓰기 때문에
wine 없이도 설치본(.exe)이 나온다.**

    python3 tools/build_desktop.py --win

산출물

    desktop/out/sword-game-0.1.0-win-x64-setup.exe   설치본(설치 위치 선택 · 바탕화면/시작메뉴 바로가기)
    desktop/out/sword-game-0.1.0-win-x64.zip         압축본(설치 없이 풀어서 실행)
    desktop/out/win-unpacked/                        풀린 상태

확인한 것(2026-08-12): 교차 빌드 성공. `SwordGame.exe` + `resources/app.asar` +
`resources/app.asar.unpacked/game/` 26개 항목(맥 빌드와 같은 목록) 확인. zip 166 파일.
윈도우용 아이콘(`build/icon.ico`)도 exe 에 박혔다.

**한계: 실행 검증은 못 했다.** 맥에는 윈도우가 없다. 산출물 존재와 압축 내용물까지만 확인했다.
윈도우 머신에서 처음 켜 볼 때 볼 것 세 가지.

1. SmartScreen 경고 — 서명을 안 했으니 "Windows에서 PC를 보호했습니다" 가 뜬다.
   `추가 정보 → 실행` 으로 넘어간다. 없애려면 코드 서명 인증서(EV 면 즉시)가 필요하다.
2. 방화벽 창 — 로컬 서버를 열지만 `127.0.0.1` 바인딩이라 방화벽이 안 물어야 정상이다. 뜨면 거절해도 게임은 돈다.
3. 그래픽 드라이버 — WebGL2 가 안 서면 검은 화면이 된다. 드라이버 업데이트가 먼저다.

윈도우 머신이나 CI 에서 직접 굽고 싶다면(권장: 서명까지 하려면 어차피 윈도우가 편하다)

    git clone <repo> && cd <repo>
    python tools\build_deploy.py
    cd desktop && npm install
    npx electron-builder --win --x64

GitHub Actions 예: `runs-on: windows-latest` → `npm ci` → `npx electron-builder --win --x64`.
서명은 `CSC_LINK`(pfx base64) + `CSC_KEY_PASSWORD` 를 secrets 에 넣으면 electron-builder 가 알아서 한다.

arm64 윈도우(Snapdragon X 등)를 챙기려면 `--win --arm64` 를 같이 준다. 지금은 x64 만 굽는다.

---

## 스팀으로 갈 때 할 일

지금 구조는 **스팀 빌드로 그대로 이어진다**. 스팀은 "실행 파일이 든 폴더"를 올리는 방식이라
`out/mac-arm64/검 게임.app` 과 `out/win-unpacked/` 가 그대로 depot 내용물이 된다.

1. **Steamworks 등록** — 앱 ID 발급($100 등록비), 상점 페이지, 연령 등급.
2. **depot 구성** — 플랫폼별로 depot 을 나눈다(win64 / macos). `steamcmd` 의 `app_build.vdf`
   에 `ContentRoot` 를 `desktop/out/win-unpacked` 로 잡으면 된다. 지금 산출물이 곧 depot 이다.
3. **서명·공증**
   - 맥: 정식 Developer ID 인증서로 서명 + `notarytool` 공증 + staple.
     `CSC_IDENTITY_AUTO_DISCOVERY=false` 를 빼고 `CSC_LINK`/`CSC_NAME` 을 주면 electron-builder 가 한다.
     공증은 `mac.notarize` 옵션. **스팀 맥 빌드는 공증이 사실상 필수다**(안 하면 유저 쪽에서 안 열린다).
   - 윈도우: 코드 서명 인증서. 없으면 SmartScreen 경고를 유저가 매번 넘긴다.
4. **Steamworks SDK 붙이기** — 업적·클라우드 세이브·오버레이를 쓸 거면 `steamworks.js` 같은
   네이티브 바인딩을 `desktop/` 의존성에 넣는다. 네이티브 모듈이 생기므로 그때부터
   `@electron/rebuild` 가 실제로 일을 하고, 플랫폼별로 굽는 머신이 필요해진다.
   오버레이는 Electron 창에 안 뜨는 경우가 있다 — 그때는 `--in-process-gpu` 를 검토한다.
5. **자동 업데이트는 스팀에 맡긴다** — electron-updater 를 붙이지 마라. 스팀이 패치를 배급하는데
   앱이 따로 자기를 업데이트하면 두 벌이 싸운다. 스팀 외 배포를 병행할 때만 나눠 붙인다.
6. **세이브 데이터** — 지금은 저장이 없다. 생기면 `app.getPath('userData')` 아래에 두고
   스팀 클라우드에 그 경로를 등록한다.
7. **이름** — 스팀 상점명과 `productName` 은 따로 간다. `productName` 은 ASCII 로 두는 게 안전하다(위 함정).
