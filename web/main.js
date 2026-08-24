// 검 게임 조작 프로토타입 — three.js
//  - WASD 이동 / Shift 달리기 / Space 베기(3연타 콤보) / 마우스 시점
//  - 칼끝 궤적을 매 프레임 샘플링해 물의 호흡 리본을 실시간 생성(Blender 에서 쓴 원리 그대로)
import * as THREE from './lib/three.module.js';
import { GLTFLoader } from './lib/GLTFLoader.js';
import { EffectComposer } from './lib/postprocessing/EffectComposer.js';
import { RenderPass } from './lib/postprocessing/RenderPass.js';
import { UnrealBloomPass } from './lib/postprocessing/UnrealBloomPass.js';
import { OutputPass } from './lib/postprocessing/OutputPass.js';

// ── glb 캐시 버전표 ────────────────────────────────────────────────────────
// ★2026-08-12 사고. 배포본 vercel.json 이 glb 에 `max-age=31536000, immutable` 을 준다.
//   그런데 배포는 **같은 URL(/basic2.glb)에 내용만 갈아끼운다.** 한 번 다녀간
//   브라우저는 옛 glb 를 1년 동안 재검증 없이 쓴다 - 크롬 hard reload 로도 안 뚫린다
//   (immutable 은 강제 새로고침조차 무시하라는 뜻이다).
//   실측: 같은 브라우저에서 fetch('./basic2.glb') 960,560바이트(8월 초 판) /
//   fetch('./basic2.glb?dev') 4,866,016(새 판). 그래서 평시 접속 화면의 시작
//   캐릭터가 알몸·맨손이었고 X·C 스킬 슬롯이 사라졌다(옛 glb 에 옷·칼·클립이 없다).
//   ★`?dev` 로 열면 멀쩡했던 건 고쳐서가 아니다. 아래 로더가 페이지 쿼리를 glb URL 에
//     그대로 붙이는 바람에 **캐시 엔트리가 갈렸을 뿐**이다(우연한 은폐).
//
//   고치는 법은 URL 에 내용 해시를 박는 것이다. 내용이 바뀌면 URL 이 바뀌므로
//   옛 캐시를 볼 일이 없고, 그제서야 immutable 이 안전해진다(그리고 최적이 된다).
// ★이 표는 **빈 채로 커밋한다.** tools/build_deploy.py 가 dist/ 복사본에서
//   아래 한 줄만 md5 표로 바꾼다(개발용 web/ 은 무버전 그대로여야 편하다).
//   빌드가 이 줄을 글자 그대로 찾으므로 생김새를 바꾸지 말 것.
const GLB_VER = {};

// glb 경로에 버전을 붙인다. 키는 web/ 기준 상대경로다('basic2.glb', 'props/tree.glb').
// ★표에 없으면(=개발판) 예전 그대로 페이지 쿼리를 물려준다. 로컬 python http.server 는
//   Cache-Control 을 안 주고 Last-Modified 만 줘서 브라우저가 휴리스틱 캐시를 한다
//   (오래된 파일일수록 오래 신선하다고 친다). 다시 구운 glb 가 안 보이던 이유이고,
//   ?dev 로 여는 관행이 그걸 뚫고 있었다. 그 편의는 그대로 남긴다.
function glbUrl(p) {
  const i = p.indexOf('?');
  const clean = i < 0 ? p : p.slice(0, i);
  const v = GLB_VER[clean.replace(/^\.?\//, '')];
  if (v) return clean + '?v=' + v;              // 배포: 해시 하나로 통일(?dev 와 안 섞인다)
  return i < 0 ? p + location.search : p;       // 개발: 옛 규칙 그대로
}

// ★props.js·enemy.js·boss.js 도 glb 를 직접 읽는다. 셋을 각각 고치는 대신
//   three.js 로더의 공식 훅에 한 번 건다. manager 를 따로 안 준 로더는 전부
//   DefaultLoadingManager 를 쓰므로(Loader 생성자) 모든 glb 요청이 여기를 지난다.
//   .glb 만 본다 - tex/ png·json 은 손대지 않는다(그쪽은 immutable 이 아니라 무죄다).
// ★반드시 아래 동적 import 보다 **먼저** 걸어야 한다. enemy.js·boss.js 는 모듈
//   최상단에서 곧바로 goblin.glb·boss.glb 를 읽는다(import 하는 순간 요청이 나간다).
THREE.DefaultLoadingManager.setURLModifier(u => /\.glb(\?|$)/.test(u) ? glbUrl(u) : u);

// 요괴·전투는 별도 모듈(main.js 가 이미 2천 줄이다).
// 페이지 쿼리(?v=..)를 그대로 물려준다. 안 그러면 main.js 만 새로 받고 enemy.js 는
// 캐시된 옛것이 돌아서 고친 게 반영 안 된 것처럼 보인다(index.html 이 쓰는 수법 그대로).
const { createEnemySystem } = await import('./enemy.js' + location.search);
// 증표·탈출(= 한 층을 깨는 루프)도 별도 모듈이다. 쿼리를 물려주는 이유는 위와 같다.
// ★13차. 맵이 둘이 됐고 **층 진행 모듈은 맵이 고른다.**
//     초원(level1, ?map=field) -> boss.js   : 각귀를 잡고 떨어진 증표를 문으로 반출
//     던전(level2, 기본)       -> level2.js : 보스가 없고 제단의 증표를 계단으로 반출
//   두 파일은 export 이름(createBossSystem)·api 게터·HUD DOM id 가 **같다.** 그래서
//   갈리는 곳이 이 세 줄뿐이고 ui.js·enemy.js·아래 main.js 는 어느 쪽인지 모른다.
//   ★level.js 를 여기서 한 번 부르지만 아래 '맵' 절이 **같은 URL** 로 다시 부르므로
//     브라우저가 같은 모듈 인스턴스를 준다(URL 이 다르면 갈린다 - 이 레포의 오랜 함정).
const _levelMod = await import('./level.js' + location.search);
const { createBossSystem } = await import(
  (_levelMod.mapName() === 'level1' ? './boss.js' : './level2.js') + location.search);
// 수풀 은신(리그 오브 레전드 규칙 + 소리). enemy.js 도 **같은 URL** 로 불러
// 같은 인스턴스를 본다. 여기서 플레이어 상태를 넣고, 요괴 쪽에서 canSee 로 읽는다.
const stealth = await import('./stealth.js' + location.search);
// 손맛(히트스톱·흔들림·처치 연출)과 소리. 둘 다 같은 캐시버스팅 규칙을 쓴다.
// ★FX_V18 = 18차 「이아이도 일섬」 스위치. **정의는 feel.js 한 곳**이고 여기서는
//   수입해서 쓴다(스위치가 두 벌이면 반드시 어긋난다). 1 = 일섬 · 0 = 17차 귀멸 판.
const { createFeel, FX_V18 } = await import('./feel.js' + location.search);
const { createSfx } = await import('./sfx.js' + location.search);

// ── 개발 모드 스위치 ──
// ★한 군데서만 정한다. 예전엔 location.search.includes('dev') 를 필요할 때마다 따로
//   물어봐서, 게이트를 새로 걸 때 어디는 켜지고 어디는 안 켜지는 일이 생겼다.
//   지금은 이 값 하나가 캐릭터 명단(S4)·우상단 상태줄(S5)·조작 안내·검증 창구를 전부 문다.
//   ★선언 위치가 파일 맨 위인 이유: CHAR_LIST 같은 **모듈 최상위 상수**가 이 값을 읽는다.
//   아래쪽에 두면 TDZ 로 모듈이 통째로 죽는다.
const DEV = location.search.includes('dev');

// ── 렌더 스케일 (2026-08-10 9차. 건틀릿 성능 격차) ──
// ★레티나에서 devicePixelRatio 2 를 그대로 쓰면 그리는 픽셀이 **4배**다. 실기 M1
//   1280x800 에서 18~29fps 가 나온 첫째 원인이 필레이트였다(폴리곤이 아니다).
//   기본 상한을 1.5 로 내린다. 1.5 는 "계단이 안 보이는 하한"으로, 여기에
//   멀티샘플 8x 가 겹쳐 있어 1.0 과 달리 가장자리가 살아 있다.
//   ?q=<수> 로 덮어쓴다(?q=1 성능 / ?q=2 스크린샷용). 값은 0.75~3 으로 가둔다.
// ★v96 회귀 조사. 심사에서 "1600x900 · devicePixelRatio 2.5 인데 내부 4000x2250" 이
//   관측됐다. 실측으로 재현해 보니 **캡은 멀쩡했다** — 같은 창·같은 DPR 에서 캡이
//   물려 pixelRatio 1.5 · 캔버스 2400x1350 이 나온다(renders/history/v96_wave10/fx/checks2.json).
//   4000x2250 이 나오는 경로는 딱 하나, `?q=2.5` 였다(1600 x 2.5 = 4000).
//   그건 스크린샷용 초과샘플 손잡이인데 평범한 URL 에 섞여 들어가면 그대로 프로덕션
//   화질·성능이 된다. 그래서 **올리는 쪽은 ?dev 에서만** 되게 막는다(내리는 쪽은 늘 된다 —
//   느린 기계에서 ?q=1 로 성능을 사는 길은 남겨야 한다).
const Q_BASE = 1.5;
const Q_RAW = parseFloat(new URLSearchParams(location.search).get('q'));
const Q_OVERRIDE = (Q_RAW > 0) ? Math.max(0.75, Math.min(3, Q_RAW)) : 0;
const DPR_CAP = Q_OVERRIDE ? (DEV ? Q_OVERRIDE : Math.min(Q_OVERRIDE, Q_BASE)) : Q_BASE;
const cv = document.getElementById('cv');
const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, DPR_CAP));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
// 2000 년대 게임처럼 보이는 원인은 폴리곤만이 아니다. 그림자·블룸·톤매핑이 없으면
// 화면이 납작하다. 셋 다 코드로만 붙는다.
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
// ── 맵이 둘이다 ──
// ★13차B. 던전(level2)과 초원(level1)은 **빛이 정반대**라 배경·안개·조명을 갈라야 한다.
//   1차 던전이 "회색 상자"였던 기계적 원인의 절반이 여기였다: 어두운 팔레트를
//   구워 놓고 **아침 햇살 조명**(반구 1.55 따뜻 + 해 2.35 + 하늘색 배경) 밑에서
//   렌더했다. 정점색으로 아무리 어둠을 칠해도 따뜻한 해가 그 위를 덮는다.
// ★level.js 의 mapName() 과 **같은 규칙**이다. 여기서 다시 푸는 이유는 조명이
//   level.js import(아래 await) 보다 먼저 서기 때문이다. 규칙이 갈리면 조명만
//   초원인 던전이 생기므로, 바꿀 일이 있으면 두 곳을 같이 고칠 것.
const IS_DUNGEON = (() => {
  const m = (new URLSearchParams(location.search).get('map') || '').toLowerCase();
  return !(m === 'field' || m === 'level1');
})();
// ── 아침 산야 (초원) ──
// 2026-08-10. 오너: "맵도 1층이니까 개방감 있게. 너무 답답한 느낌이야.
//   SAO, 게임 속 바바리안의 **첫 층에 온 것 같은 느낌**."
// 밤색(#04060c) 배경 + 파란 안개는 "깊은 던전"의 그림이다. 1층은 그러면 안 된다.
// 배경·안개·조명을 옅은 하늘빛 아침으로 통째로 옮긴다. 배경색과 안개색은
// **같은 값**이어야 한다(다르면 화면 끝에서 지형이 안개색으로 사라졌다가
// 배경색으로 한 번 더 갈아타서 띠가 생긴다).
// ── 색색의 석조 회랑 (던전. 14차 브롤스타즈·포트나이트 화풍) ──
// ★★14차. 오너 "브롤스타즈, 포트나이트 풍의 그림체 맵을 원했는데 지금과 많이 다르다."
//   정본이 incoming/codex_dungeon2/ 로 갈렸다. 배경도 같이 갈린다:
//   컨셉의 빈 공간은 **검정이 아니라 깊은 남보라**(실측 #1a1636, 화면의 13.6%)다.
//   0x0b1420(13차)은 그 자리를 검게 죽여서 벽 위가 구멍으로 보인다.
// ★15차. 0x1a1636 -> 0x0b1020. 컨셉의 빈 공간 실측은 #080b0f ~ #06060b 이고
//   우리 화면은 그보다 한 단 밝게 둔다(벽 위가 완전한 구멍이 되면 안 된다).
const SKY = IS_DUNGEON ? 0x0b1020 : 0x9fc2d8;
scene.background = new THREE.Color(SKY);
// ★안개 거리는 **카메라 거리에 물려 있다.** near 가 카메라-플레이어 거리보다 멀어야
//   플레이어 자신이 안개를 먹지 않는다. 카메라가 34m 였던 시절 값이 34~66 이었고,
//   dist 를 24 로 당기면서 26~48 로 다시 계산했다(아래 CAM 주석 참고).
//   지금 시점에서 화면에 보이는 지면은 카메라에서 22.5m(화면 아래끝) ~ 32.6m(위끝)다.
//   플레이어(24m)는 0%, 화면 위끝이 30% 정도 먹어 깊이감만 남는다.
//   ★값 자체는 아래 CAM 블록에서 dist 를 읽어 다시 세팅한다(한 군데서 정하게).
scene.fog = new THREE.Fog(SKY, 26, 48);

const camera = new THREE.PerspectiveCamera(46, innerWidth / innerHeight, 0.1, 200);

// ---------- 후처리 ----------
// 블룸은 **밝은 부분만** 번지게 한다. 칼 이펙트가 빛나 보이는 건 이게 있어야 한다.
// 임계값을 낮게 잡으면 옷까지 번져서 뿌예지므로 0.85 로 높게 둔다.
// ★EffectComposer 는 **자체 렌더타겟**에 그린다. WebGLRenderer 의 antialias:true 는
// 기본 프레임버퍼에만 걸리므로, 컴포저를 붙이는 순간 계단이 전부 살아난다.
// 멀티샘플 타겟을 직접 만들어 넘겨야 한다.
// ★samples 8 -> 4 -> **초과샘플 있으면 2 / 없으면 4** (2026-08-11 소반 실측.
//   원자료 renders/history/v94_wave9/soban_msaa/):
//   ① 이 기계(ANGLE/Metal)의 GL_MAX_SAMPLES 는 **4** 다. three 가 maxSamples 로 잘라 쓰므로
//      "8" 은 처음부터 4 로 돌고 있었다 — s8 과 s4 의 화면 차이가 **0px**(비트 동일)이다.
//      즉 9차 성능 파도가 잰 -24% 는 8->4 가 번 게 아니라 아래 "두 타겟 samples" 줄이
//      번 것이었고, 그건 절감이 아니라 **격프레임 MSAA 끄기**였다(그 주석 참고).
//   ② 그래서 단수를 정직하게 내린다. DPR_CAP 1.5 로 그린 뒤 화면에 얹을 때 1.5배 축소가
//      한 번 더 걸리므로(=화소 2.25배 초과샘플) 2x 와 4x 가 눈으로 구별이 안 된다.
//      사람이 보는 1280x720 화소로 재면 s2 는 s4 대비 >12/255 차이 0.13%(1,218px)
//      · RMSE 0.96/255 뿐이다(8배 확대 크롭도 구별 불가).
//   ③ 반대로 축소가 없는 화면(외장 비레티나 = pixelRatio 1)에서는 격차가 보인다
//      (가장자리 회복 52%뿐. 확대 크롭에서 계단이 눈에 띈다). 그쪽은 4 로 둔다 —
//      화소가 2.25배 적어서 4샘플이 오히려 싸다(pixelRatio 1·4샘플 21.0ms
//      < pixelRatio 1.5·2샘플 29.2ms).
//   ★2 를 못 쓰는 GPU 는 스펙상 **위로** 올림한다(4 가 된다). 화질이 나빠지는 쪽으로는 안 샌다.
const MSAA = renderer.getPixelRatio() >= 1.4 ? 2 : 4;
const _rt = new THREE.WebGLRenderTarget(
  innerWidth * renderer.getPixelRatio(), innerHeight * renderer.getPixelRatio(),
  { type: THREE.HalfFloatType, samples: MSAA });
const composer = new EffectComposer(renderer, _rt);
composer.addPass(new RenderPass(scene, camera));
// ★임계값은 **씬 밝기에 물려 있다.** 밤 팔레트에서 0.93 이면 이펙트만 번졌지만,
//   아침 산야로 바꾸면서 밝은 흙바닥까지 임계값을 넘어 화면 전체가 뿌예졌다.
//   1.02 로 올려 "가산합성으로 1을 넘긴 것 = 이펙트"만 번지게 하고,
//   그만큼 세기를 올려 감청 궤적·붓질이 밝은 배경 위에서도 또렷하게 남는다.
const bloom = new UnrealBloomPass(
  new THREE.Vector2(innerWidth, innerHeight), 0.46, 0.55, 1.02);
composer.addPass(bloom);
composer.addPass(new OutputPass());
// ★★시작 크기 사고 (9차 성능 실측. handoff_perf.md 2-1. 이번 파도 제일 큰 성능 레버):
//   EffectComposer 는 **렌더타겟을 직접 받으면 그 크기를 CSS 크기로 오해**한다.
//   _rt 는 이미 device 픽셀(1920x1200)인데 addPass 에서 pixelRatio(1.5)를 한 번 더
//   곱해 2880x1800 을 패스에 먹인다. UnrealBloomPass 는 받은 크기의 절반부터 밉을
//   쌓으므로 밉 0단이 640x400 이어야 할 것이 **1440x900**(면적 2.25배)이 됐다.
//   창을 한 번 리사이즈하면 아래 resize 핸들러가 고쳐 주지만, 평소에 리사이즈할 일이
//   없으니 게임은 **늘 틀린 크기로** 돌고 있었다.
//   실측: 후처리가 한 프레임에 훑는 픽셀 6.05Mpx -> 1.19Mpx (-80%).
//   ★값 튜닝이 아니다. 리사이즈 핸들러와 **같은 크기**를 시작에도 한 번 먹이는 것뿐이다.
bloom.setSize(innerWidth, innerHeight);
// ★★두 타겟의 samples 는 **반드시 같아야 한다** (2026-08-11 소반. 30Hz 깜빡임의 정체):
//   이 체인에서 needsSwap 인 패스는 마지막 OutputPass 하나뿐이라(RenderPass·UnrealBloomPass
//   는 둘 다 needsSwap=false) composer.render() 한 번에 스왑이 **정확히 한 번** 일어나고,
//   그 상태가 다음 render 까지 남는다. 게다가 RenderPass 는 writeBuffer 가 아니라
//   **readBuffer 에** 씬을 그린다. 그래서 씬이 앉는 자리가 rt2 -> rt1 -> rt2 로 프레임마다
//   바뀐다. 여기서 rt2 만 samples=0 으로 꺼 두면 **한 프레임 걸러 MSAA 없는 화면**이 된다.
//   실측(세계 정지, 같은 태스크 안 연속 렌더 6장): 1↔3↔5 는 완전 동일, 1↔2↔4↔6 은
//   2,942 CSS화소(0.32%)가 최대 108/255 · 평균 21.8 로 흔들렸다. 흔들리는 화소는 정확히
//   바위·수풀·플레이어의 **실루엣 가장자리**뿐이라, 눈에는 윤곽이 30Hz 로 떠는 것으로 보인다.
//   ★함정: "둘째 타겟은 안 쓰니까 꺼도 된다"가 거짓이다. 안 쓰이는 것은 writeBuffer 쪽인데
//     그 자리를 rt1 과 rt2 가 **번갈아** 맡는다. 절감하고 싶으면 한쪽을 끄지 말고
//     **양쪽 단수를 같이 낮출 것**(위 MSAA 상수).
//   ★계측 함정도 같이 사라진다: 예전에는 정지 화면 A/B 에서 이 흔들림이 통째로 "이펙트
//     마스크 6,633px" 로 잡혔다(v94 9B-2 가 한 장당 두 번 그려서 우회했다).
if (composer.renderTarget2) composer.renderTarget2.samples = composer.renderTarget1.samples;

// ---------- 손맛 · 소리 ----------
// ★scene·camera·bloom 이 다 선 뒤에 만든다(전멸 순간 블룸을 펄스로 밀어야 해서 필요).
const feel = createFeel({ scene, camera, bloom });
const sfx = createSfx();
// ★자동재생 정책: 사용자 입력 **전에는** AudioContext 가 suspended 라 소리가 안 난다.
//   첫 입력에서 만들고 resume 한다. 이 세 줄이 없으면 "구현했는데 소리가 안 나는"
//   상태가 되고, 그 상태는 코드만 봐서는 절대 안 보인다.
for (const ev of ['keydown', 'pointerdown', 'touchstart']) {
  addEventListener(ev, () => sfx.unlock(), { passive: true });
}

// ---------- 조명 ----------
// 아침 햇살. 하늘은 옅은 하늘색, 바닥 반사는 마른 흙색이다.
// ★밤 팔레트에서는 아랫빛이 0x0a1018(거의 검정)이라 그늘이 통째로 죽어 있었다.
//   1층은 "그늘도 밝은" 곳이라 아랫빛을 흙색으로 올려야 답답함이 풀린다.
// ★★13차B 던전 분기. 세 등의 **윗면 조도 합**을 초원 실측(tools/color_contract.py 의
//   IRRADIANCE 0.99)과 같은 자로 환산하면 이렇다.
//       초원  E = (0.99, 0.99, 1.00)   휘도 0.99   파랑/빨강 1.01
//       던전  E = (0.39, 0.56, 0.86)   휘도 0.55   파랑/빨강 2.21
//   즉 **절반 밝기에 두 배 푸른** 빛이다. blender/s40_dungeon1.py 의 팔레트는
//   이 E 로 ACES 를 역산해서 뽑은 값이라, 여기 숫자를 바꾸면 던전 색이 통째로 밀린다.
//   ★해를 남기는 이유: 캐릭터 발밑 접지 그림자가 이 게임 손맛의 일부다(v90).
//     대신 각도를 훨씬 세워(2.5,12,3.5) 그림자를 짧게 만든다 - 던전에서 긴 그림자가
//     대각으로 누우면 그 순간 실외가 된다.
// ★★14차 던전 개정. 세 등을 통째로 갈았다.
//       13차  E = (0.391, 0.565, 0.864)  휘도 0.55  R/B 0.45   ← 차고 어두운 달빛
//       14차  E = (0.877, 0.831, 0.983)  휘도 0.85  R/B 0.89   ← 밝은 중립광
//   컨셉의 어둠은 **조명이 어두워서**가 아니라 벽 알베도가 보라·코발트라서 어둡다.
//   조명으로 어둠을 만들면 바닥까지 같이 죽어서 "못 보겠는 던전"이 된다(13차가 그랬다:
//   통로 컷 휘도 하위 25% 가 0.0024).
//   ★반구광의 **아랫빛을 보라**로 둔 것이 이 판의 핵심 한 줄이다. 수직면(벽)은
//     sky/ground 반반을 받으므로 벽만 보라로 가라앉고 바닥(윗면)은 밝게 남는다 =
//     컨셉의 "바닥 Y 0.31 : 벽 Y 0.04" 비율이 조명에서 저절로 나온다.
//   ★2차 조정. 첫 판 (0xbcc6f0/0x5b4a86 2.20 · 0xffeacb 1.55) 은 E R/B 0.89 로
//     **중립보다 찼다**. 판정에서 밝은 띠 R/B 가 3.7(컨셉 7.6~9.9)로 나왔다.
//     윗빛만 조금 데운다(R/B 0.89 -> 1.11). 더 데우면 **벽까지 갈색**이 되어
//     보라 석조가 사라진다(안 B·C 를 계산해 보고 버린 이유가 그것이다:
//     벽면 E R/B 가 1.68 까지 뜬다).
// ★★★15차(롤·나혼렙). 오너가 14차 브롤 방향을 기각했다. 던전 조명을 다시 갈았다.
//       14차  E_top (0.993,0.830,0.895) Y0.87 · E_wall (0.469,0.374,0.540) Y0.41
//       15차  E_top (1.036,0.911,0.913) Y0.92 · E_wall (0.427,0.396,0.524) Y0.39
//   ★2차 조정. 아랫빛 0x4d4070->0x6a5a90 · 키 2.35->2.70. **캐릭터가 수직면**
//     이라 E_wall 이 캐릭터 밝기를 정한다. 1차 값에서는 캐릭터/바닥이 1.45~3.05 로
//     자리마다 갈려 2.5배 계약을 못 지켰다(맵은 PAL 이 같이 내려 상쇄한다).
//   ★윗면 조도는 **거의 그대로** 두고 수직면만 25% 어둡게 했다. 이유가 계약이다:
//     캐릭터 밝기는 윗면 조도가 정하고(실측 4자리 x 4조명 = 캐릭터 휘도 0.19~0.27),
//     처방전 A표가 **캐릭터/바닥 2.5배 이상**을 요구한다. 조명을 통째로 내리면
//     캐릭터까지 같이 죽어서 그 계약이 깨진다(14차가 정확히 그 함정에 빠져 1.39배였다).
//     맵을 어둡게 만드는 일은 조명이 아니라 **팔레트(s40 의 PAL)** 가 한다.
//   ★반구광 아랫빛을 짙은 보라(0x6a5a90)로 두고 세기를 올려, 수직면(벽)만
//     찬 보랏빛 어둠에 잠기게 한다. 컨셉 실측이 그렇다 — 최암 15% #080b0f(H216) ·
//     최명 3% #90713c(H38). 어두우면 차고 밝으면 뜨겁다.
//   ★이 숫자를 건드리면 tools/color_contract.py 의 IRR_DUNGEON(_WALL) 과
//     blender/s40_dungeon1.py 의 PAL 이 같이 거짓이 된다. 셋은 한 짝이다.
scene.add(IS_DUNGEON
  ? new THREE.HemisphereLight(0x9aaee0, 0x6a5a90, 1.95)
  : new THREE.HemisphereLight(0xcfe4f2, 0x5b5140, 1.55));
const key = IS_DUNGEON
  ? new THREE.DirectionalLight(0xffe3b4, 2.70)            // 횃불 쪽에서 오는 따뜻한 키
  : new THREE.DirectionalLight(0xfff0d4, 2.35);           // 따뜻한 해
key.position.set(...(IS_DUNGEON ? [2.5, 12, 3.5] : [5, 9, 4]));
key.castShadow = true;
// ★그림자 맵 크기 (9차 성능 실측. handoff_perf.md 3):
//   2048 -> 1024 는 씬 1패스 중앙값 -18.6%(18쌍 중 14쌍 개선)지만, 상자가 ±10m 라
//   텍셀이 9.8 -> 19.6mm 로 두 배가 되어 **캐릭터 발밑 접지 그림자**가 뭉갠다
//   (그 접지가 이 게임 손맛의 일부다 - v90). 그래서 타협점 1536(텍셀 13mm)을 쓴다.
//   ?q=1(성능 확인)에서는 1024 까지 내린다.
const SHADOW_MAP = (Q_OVERRIDE > 0 && Q_OVERRIDE < 1.25) ? 1024 : 1536;
key.shadow.mapSize.set(SHADOW_MAP, SHADOW_MAP);
// ★그림자 상자는 카메라 시야에 물려 있다. 화면 밖까지 덮으면 텍셀만 굵어지고,
//   좁으면 걸어가는 동안 그림자가 끊겼다 붙었다 한다.
//   시점 개정(dist 34 -> 24) 후 한 화면이 18.0 x 14.8m 라 반폭 9.0m / 앞뒤 11.2·3.6m 다.
//   ±10 이면 화면 전체를 덮고도 1m 여유가 남는다(2048 맵 기준 텍셀 11.7 -> 9.8mm 로
//   오히려 선명해졌다).
key.shadow.camera.near = 1; key.shadow.camera.far = 44;
key.shadow.camera.left = -10; key.shadow.camera.right = 10;
key.shadow.camera.top = 10; key.shadow.camera.bottom = -10;
key.shadow.bias = -0.0012;
key.shadow.normalBias = 0.02;
scene.add(key);
scene.add(key.target);       // 캐릭터를 따라가게(범위가 좁아야 그림자가 선명하다)
// 반대쪽 하늘빛. 그림자 쪽 실루엣이 배경에 녹지 않게 잡아 주는 역할이라 남긴다.
// 밤에는 진한 파랑(0x66aaff)이었는데 아침에는 옅게 깔아야 색이 안 튄다.
const rim = IS_DUNGEON
  ? new THREE.DirectionalLight(0x6f5cc4, 0.55)            // 보라 반사광
  : new THREE.DirectionalLight(0x9dc8ee, 0.55);
rim.position.set(-6, 4, -5);
scene.add(rim);

// ---------- 맵 ----------
// ★플레이스홀더 평면(120x120)과 격자는 걷어냈다. 맵 바닥이 y=0.02 라 y=0 짜리 평면을
//   같이 두면 z-fighting 이 난다(블렌더가 바닥을 2cm 띄워 놓은 이유가 바로 그거였다).
// ★여기서 await 하는 이유: 아래 코드가 스폰 지점과 요괴 무리 좌표를 맵에서 받아 쓴다.
//   main.js 는 top-level await 를 쓰는 모듈이라 이렇게 순서를 세울 수 있다.
//   쿼리(?v=..)를 물려주는 것도 enemy.js 와 같은 이유다(맵만 캐시된 옛것이 남으면
//   충돌 좌표와 보이는 벽이 어긋난다).
const level = await import('./level.js' + location.search);
await level.loadLevel(scene);
window.__level = level;

// ---------- 상태 ----------
const keys = {};
// ── 층 돌파 게이트 ──
// v72 QA #15: "층 돌파" 패널이 뜬 채로 계속 걸어다닐 수 있었다. 판이 끝났는데 조작이
// 살아 있으면 패널이 그냥 떠 있는 글자가 된다. 돌파 뒤에는 R(재시작)만 받는다.
// ★상태는 boss 를 **읽기만** 한다(boss.js 는 안 건드리는 파일이다). boss 는 아래쪽에서
//   const 로 선언되므로 로딩 중 TDZ 를 피하려고 window.__boss 로 돈다(R 키와 같은 이유).
function isCleared() {
  return !!(window.__boss && window.__boss.cleared);
}
// ── 한 판 다시 시작 (2026-08-10 9차. 연출UI S2 "매번 8.3초 암전") ──
// 심사에서 사망·R·클리어가 전부 **전체 페이지 리로드**로 보였다. 실제로 코드에는
// location.reload 가 한 줄도 없다(그 건은 handoff 에 규명을 적었다). 문제는 그게 아니라
// **되돌리는 창구가 세 군데로 흩어져 있어서 무엇이 리셋되는지 아무도 몰랐다**는 것이다.
// 그래서 한 함수로 모은다. R 키·클리어 뒤 R·검증 창구가 전부 여기를 지난다.
//   자리      : toSpawn()          — 스폰 지점 + 카메라
//   체력·요괴 : enemies.reset()    — 체력 만땅 · 무리 전원 재배치 · 새는 통 초기화
//   처치 수   : enemies.resetKills()— 판 기준으로 0
//   보스·증표 : boss.restart()     — 체력 · 증표 · 소요 시간
//   내 상태   : 공격·대시·점프·콤보·궤적·선입력
// ★window.__boss / window.__enemy 로 도는 이유는 아래 R 키 주석과 같다(TDZ).
function resetRun() {
  toSpawn();
  const E = window.__enemy, B = window.__boss;
  if (E) { if (E.reset) E.reset(); if (E.resetKills) E.resetKills(); }
  if (B && B.restart) B.restart();
  attacking = false; heavy = false; atkClip = null; atkStruck = false; atkHitT = -99;
  stepLeft = 0; stepDist = 0;
  coastLeft = 0; punchLeft = 0; hsLeft = 0;   // ★관성·카메라 펀치·히트스톱도 판을 넘기면 안 된다
  _uw.on = false; camLift = 0; camOccT = 0;   // ★벽 빼내기 목표·카메라 가림 완화도 판을 넘기면 안 된다
  dashLeft = 0; dashGone = 0; dashReadyT = -99; dashIfUntil = -99;
  restoreDashTs();
  vy = 0; grounded = true; jumping = false;
  comboStep = 0; comboWindow = 0; resetCombo(null);
  clearBuffer();
  trailBuf.length = 0; spray.length = 0;
  if (hurtDirEl) { hurtDirEl.classList.remove('on'); hurtDirT = 0; }
  sfx.stopTell();                  // 보스 예고음이 판을 넘어 이어지면 안 된다
  // ★주머니와 바닥에 널린 물건도 판을 넘기지 않는다(이 판의 리셋 문화 그대로).
  if (window.__items) window.__items.reset();
  if (window.__arrows) window.__arrows.reset();      // ★21차. 날아가던 화살도 판과 함께 지운다
  // ★22차 멀티. 남의 화살·궤적도 같이 지운다. window 로 도는 이유는 위 두 줄과 같다
  //   (mpFx 는 아래에서 const 로 선언되므로 여기서 이름을 직접 쓰면 TDZ 다).
  if (window.__mpfx) window.__mpfx.reset();
}
addEventListener('keydown', e => {
  keys[e.code] = true;
  // ── 클립 미리보기 패널(개발용). 아래 정의는 '클립 미리보기 패널' 절에 있다 ──
  // 여기 세 키는 원래 게임이 안 쓰던 키라 모드와 무관하게 받아도 기존 조작이 안 변한다.
  // ★v96 회귀 수정. 이 셋은 **개발용**이다. ?dev 가 아닌 프로덕션에서 P 를 누르면
  //   플레이어 눈앞에 파란 개발자 클립 패널이 열렸다(심사 지적). 게이트를 되돌린다.
  //   Escape·, . 도 같이 문다 - 미리보기가 안 켜지면 셋 다 할 일이 없다.
  if (DEV && e.code === 'Escape') { exitPreview(); return; }
  if (DEV && e.code === 'KeyP') { e.preventDefault(); togglePreview(); return; }
  if (DEV && (e.code === 'Comma' || e.code === 'Period')) {
    // 정지 상태에서 1/30 초씩 앞뒤로. 미리보기가 아니면 아무 일도 안 한다.
    if (preview.on) { e.preventDefault(); stepFrame(e.code === 'Period' ? 1 : -1); }
    return;
  }
  // ── 층 돌파 뒤 ──
  // R 만 살아 있다. 이동키는 keys[] 에 적히지만 아래 루프가 무시하고(cleared),
  // 공격·점프는 이 return 이 막는다(버퍼로 새는 경로는 try* 안쪽에서 한 번 더 막는다).
  if (isCleared()) {
    if (e.code === 'Space' || e.code === 'Tab' || /^Arrow/.test(e.code)) e.preventDefault();
    if (e.code === 'KeyR') resetRun();
    return;
  }
  // ★숫자키 충돌: 1~7 은 원래 칼 교체다(스킬이 아니라 무기 슬롯).
  //   그래서 **미리보기 중일 때만** 클립 선택으로 돌린다. 평소 조작은 지금과 100% 같다.
  //   8·9 는 원래 아무 데도 안 쓰였으므로 정상 모드에선 그대로 무시한다.
  if (/^Digit[1-9]$/.test(e.code)) {
    const n = +e.code.slice(5) - 1;
    if (preview.on) previewClipAt(n);
    else if (n < 7) equipSword(n);
    return;
  }
  // 미리보기 중에는 전투·점프 입력을 막는다. 저것들이 current 를 가로채면
  // 고른 클립이 그 자리에서 끊긴다(이동 입력은 루프에서 무시한다).
  // 칼 교체·캐릭터 교체·제자리는 애니 상태를 안 건드리므로 열어둔다.
  if (preview.on) {
    if (e.code === 'Space' || e.code === 'Tab' || /^Arrow/.test(e.code)) e.preventDefault();
    if (e.code === 'Tab') equipSword((swordIdx + 1) % SWORDS.length);
    if (e.code === 'KeyR') toSpawn();
    if (e.code === 'KeyF' && DEV) { e.preventDefault(); cycleChar(); }   // 개발용(S4)
    return;
  }
  // 방향키 조작으로 바꾸면서 Space 를 점프에 내줬다. 베기는 Z 로.
  // ★9차: 이동키를 누른 채면 **대시(회피)**, 아니면 예전대로 점프였다.
  // ★★17차(오너 지시): **Space 는 이동 중이든 아니든 언제나 점프**다. 이 줄은 안 바꾼다 -
  //   회피 스위치(DASH_ON=false)가 tryDash 첫 줄에서 false 를 돌려주므로 갈래가 하나로
  //   합쳐진다. 스위치를 켜면 옛 조작(이동 중 = 회피)이 이 줄 그대로 돌아온다.
  if (e.code === 'Space') { e.preventDefault(); if (!tryDash()) tryJump(); }
  if (e.code === 'KeyZ') { e.preventDefault(); tryAttack(); }
  if (e.code === 'KeyQ' || e.code === 'KeyX') { e.preventDefault(); tryHeavy(); }
  if (e.code === 'KeyE' || e.code === 'KeyC') { e.preventDefault(); tryWide(); }
  if (/^Arrow/.test(e.code)) e.preventDefault();      // 화면 스크롤 방지
  if (e.code === 'Tab') { e.preventDefault(); equipSword((swordIdx + 1) % SWORDS.length); }
  // R = 제자리 + 층 재시작. 보스 체력·증표·소요 시간이 전부 처음으로 돌아간다.
  // ★window.__boss 로 도는 이유: boss 는 아래쪽에서 const 로 선언되므로 로딩 중에
  //   키가 눌리면 TDZ 로 터진다. typeof 로도 못 막는다(const 는 typeof 도 던진다).
  if (e.code === 'KeyR') resetRun();
  // F = 캐릭터 교체. ★개발용이다(S4). 평시에는 **아무 일도 안 한다** — 안내에도 안 띄우므로
  //   "눌렀는데 반응이 없다"가 아니라 "그런 키가 없다"로 읽힌다. preventDefault 도 안 한다.
  if (e.code === 'KeyF' && DEV) { e.preventDefault(); cycleChar(); }
  // M = 음소거. HUD 의 마지막 줄이 상태를 그대로 보여준다.
  if (e.code === 'KeyM') { e.preventDefault(); setMute(sfx.toggleMute()); }
});
// ── 26차: Z(기본 3연타) 봉인 (2026-08-25 오너 "z 스킬은 없애고 x 스킬 ... 다시해줘") ──
// DASH_ON 과 같은 문법이다: 갈림은 tryAttack 첫 줄 하나뿐이고, 콤보 표(ATK_STEP_T/
// ATK_STEP_COMMIT)·배율(enemy.js SKILL_MUL.Attack)·Attack 클립·원격 재생(mp.js)은
// 전부 산 채로 남는다(다른 캐릭터·복귀 대비. 스위치를 켜면 그대로 돌아온다).
// ★궁수(개발용 F 전환)의 Z 는 화살 발사라 남긴다 — 봉인은 검사 기본기만이다.
// 같이 접히는 것: 계기판 Z 칸(mountSpaceChip 옆), 아래 조작 안내 Z 줄(#hZatk),
// 홈 화면 조작 요약(home.js)의 Z 표기. ★선언이 여기(파일 앞)인 이유: 바로 아래
// top-level 블록이 모듈 평가 때 읽는다 — DASH_ON 자리(전투 절)에 두면 TDZ 다.
const SKILL_Z_ON = false;
// 조작 안내의 F 줄은 개발용이라 기본이 숨김이다(index.html). ?dev 에서만 켠다.
{
  const fRow = document.getElementById('hFchar');
  if (fRow && DEV) fRow.style.display = '';
}
// 조작 안내의 Z 줄도 기본 숨김이다(26차 Z 봉인). 스위치를 켜면 여기서 다시 펼쳐진다.
{
  const zRow = document.getElementById('hZatk');
  if (zRow && SKILL_Z_ON) zRow.style.display = '';
}
// ★sfx 는 이 파일 위쪽에서 만들어지지만 HUD 요소는 index.html 에 있다.
const muteEl = document.getElementById('mute');
function setMute(on) {
  // ★안내의 다른 줄이 전부 **동작형**("이 안내 접기", "베기")인데 이 줄만 상태형이라
  //   말투가 혼자 달랐다(건틀릿 연출UI S8). 누르면 무슨 일이 나는지로 적는다.
  //   구조도 index.html 의 새 안내 구조(.ks / .t)를 따른다.
  if (muteEl) muteEl.innerHTML = '<span class="ks"><span class="k">M</span></span>'
    + '<span class="t">소리 ' + (on ? '켜기' : '끄기') + '</span>';
}
setMute(false);
addEventListener('keyup', e => { keys[e.code] = false; });

// ── 고정 쿼터뷰 (리그 오브 레전드 기준) ──
// 시점이 매번 달라지면 맵을 외울 수가 없고, 수풀에 숨었는지 같은 판단도
// 시점 따라 달라진다. 그래서 각도를 고정한다. 플레이어는 카메라를 못 돌린다.
//
// ★이 값은 "시점을 먼저 고르고 끝"이 아니라 **한 화면에 뭐가 들어와야 하는지**를
//   먼저 계산하고 거기서 역산했다. 근거는 전부 이 레포의 실측값이다.
//
//   필요한 지면 범위 (renders/history/v56_camera 에 렌더 증거)
//     전방 >= 9m : 무리 어그로가 7.0m(enemy.js AGGRO_RADIUS)다. 무리가 화면에
//                  들어온 뒤 판단할 틈이 있어야 하니 어그로선보다 2m 는 더 봐야 한다.
//     후방 >= 6m : 궁수·힐러가 뒤에 선다. 요괴 정지거리 1.2m(ENEMY_ATK_RANGE 0.95
//                  + 몸집 0.25)와 무리 반경 2.6m 밖이어야 하니 5.5~6.5m 뒤가 제자리다.
//     폭   >= 18m: 요괴 5마리가 반경 2.6m 로 퍼지고 탱커가 옆을 잡고 검사가 측면을
//                  도는 교전 하나가 폭 7~8m 다. 좌우 지형까지 읽으려면 이만큼 필요하다.
//                  대신 무리 간격이 17m 이상이라 폭을 이보다 크게 벌리면 두 무리가
//                  한 화면에 들어와 "한 무리만 떼어낸다"가 깨진다.
//   => 필요 지면 = 깊이 15~16m x 폭 18~21m. 지금 값은 이 안에서 고른 것이다.
//
// pitch 0.90rad = 지면에서 51.6도. LoL 이 56도인데 4도 눕혔다. 우리 캐릭터가 1.75m
//   라 56도로 세우면 필요한 깊이 16m 를 확보하는 순간 캐릭터가 화면 세로의 7.6%
//   까지 작아진다. 51.6도면 같은 깊이에서 9.0% 로 LoL 대역(9~11%)에 들어온다.
//   각을 더 세우면(1.15rad 등) 캐릭터도 작아지고 보이는 범위도 같이 줄어 둘 다 잃는다.
// ── 2026-08-10 개정 (오너: "너무 위에서 보는 느낌이다. 롤 느낌으로") ──
// 옛 값 fov 20 / dist 34 는 **각이 문제가 아니라 원근이 죽은 것**이 문제였다.
// 화각 20도에 34m 면 거의 정사영이라 지도를 내려다보는 그림이 되고, 게다가 카메라가
// 캐릭터를 정면으로 겨눠서 캐릭터 몸통이 화면 정중앙(세로 49%)에 박혀 있었다.
// LoL 은 (1) 세로 화각이 40도 가까워 원근이 살아 있고 (2) 챔피언이 화면 아래쪽에 서고
// 전방이 넓다. 둘 다 고친다.
//
//   dist 24 / fov 24 : 거리를 10m 당기고 화각을 넓혔다. 위/아래 원근 왜곡비가
//     1.33 -> 1.45 로 올라간다(LoL 실측 대역 1.32~1.65 의 한가운데). 화각을 더
//     넓히면(30도) 같은 폭을 유지하려고 거리를 18m 까지 당겨야 하는데, 그러면
//     왜곡비가 1.7 을 넘어 화면 위쪽 벽이 눈에 띄게 기운다.
//   pitch 0.86rad = 49.3도. 옛 51.6도보다 2.3도 눕혔다(= 덜 내려다본다).
//   lead 1.25m : **바라보는 지점을 캐릭터보다 1.25m 앞으로** 옮긴다. 이것만으로
//     캐릭터 몸통이 화면 세로 49% -> 39% 로 내려가고 전방 시야가 10.1 -> 10.9m 로
//     넓어진다. 옛 시점에서 "캐릭터가 정중앙"이던 건 카메라가 가슴 높이를 정확히
//     겨누고 있어서였다(camTarget = 캐릭터 위치 그대로).
//     ★lead 1m 당 캐릭터가 화면 세로로 8% 씩 내려간다. 1.75 를 넘기면 후방이
//     3.4m 밑으로 떨어져 등 뒤 1.2m 에 붙은 고블린 말고는 아무것도 안 보인다.
//
// 제약 충족치(브라우저 __probe() 실측, 1600x900):
//   전방 10.89m (>= 9 필요) · 후방 3.86m · 폭 18.13m (18~21)
//   캐릭터 세로 10.91% (9~11.5) · 왜곡비 1.448 (<= 1.45) · 몸통 화면 아래에서 39.4%
// ★후방은 6.14 -> 3.86 으로 줄었다. 이건 감수한 것이다. 옛 "후방 6m" 기준은
//   파티(궁수·힐러가 뒤에 선다) 전제였는데 지금은 솔로 대 고블린이고, 오너 지시가
//   "전방이 넓게"다. 등 뒤 교전 거리(정지 1.2m)는 3.86m 안에 넉넉히 들어온다.
// yaw 0 = 맵 격자와 정면으로 맞춘다. 맵이 축 정렬 96x96 이라 3.2m 통로가 화면과
//   나란히 놓이고 캐릭터 등이 정면으로 보인다. yaw 45도(마름모)도 렌더해 봤는데
//   통로가 화면을 대각으로 가르고 캐릭터가 옆등으로 보여서 LoL 과 멀어진다.
const CAM = { yaw: 0.0, pitch: 0.86, dist: 24.0, fov: 24, lead: 1.25 };
let yaw = CAM.yaw, pitch = CAM.pitch, dist = CAM.dist, lead = CAM.lead;
camera.fov = CAM.fov;
camera.updateProjectionMatrix();
// 휠 확대만 남긴다. 회전은 아예 없다.
// ★LoL 은 확대 폭이 좁고 대부분 최대로 당긴 상태로 고정해 쓴다. 그래서 **기본값이
//   제일 먼 쪽**(24)이고 안쪽으로만 3m 열어준다.
//   위에 적은 제약 대역(폭 18~21m / 캐릭터 9~11.5%)은 **기본값 기준**이다.
//   21m 까지 당기면 폭 15.9m / 캐릭터 12.4% 로 대역을 벗어나는데, 이건 "가까이
//   들여다보는" 선택지라서 그렇게 둔다. 전방 시야만은 확대 구간 전체에서
//   9.5m 이상이라(어그로 7m + 판단 여유 2m) 요괴가 화면 밖에서 달려들지는 않는다.
// ── 2026-08-10 9차 개정: 줌 폭을 18~32 로 연다 (지형 심사 8위 "부감 불가") ──
// 옛 대역(21~24)은 "기본이 제일 먼 쪽"이라 **한 발짝도 물러설 수 없었다.** 심사에서
// 지형·동선을 읽으려고 뒤로 빼려는 시도가 전부 벽에 부딪혔다.
//   18 : 교전 확대. 폭 13.6m / 캐릭터 세로 14.5% — 롤 대역 밖이지만 "들여다보는" 선택지다
//   24 : 기본값. 위에 적은 제약 계산이 전부 이 값 기준이다
//   32 : 부감. 폭 24.2m / 캐릭터 8.2% — 무리 둘이 한 화면에 들어오므로 길 찾기용이다
// ★pitch·yaw 는 그대로 고정이다(롤처럼 각도는 못 돌린다). 거리만 연다.
// ★안개·그림자 상자는 **거리에서 역산**하므로 아래 applyDist() 한 군데서만 정한다.
const DIST_MIN = 18.0, DIST_MAX = 32.0;
// 안개 near 를 카메라-플레이어 거리보다 2m 뒤에 두면 플레이어는 0% 로 남고,
// 화면 위끝 지면이 30% 정도 먹어 깊이감만 생긴다. 32m 로 빼도 이 관계가 유지된다.
// 그림자 상자도 같이 넓힌다(24m 에서 ±10m 였다. 안 넓히면 부감에서 화면 가장자리
// 그림자가 통째로 잘린다. 텍셀은 그만큼 굵어지지만 부감은 원래 세밀함이 필요 없다).
function applyDist() {
  // ★던전은 안개가 **훨씬 빨리** 닫힌다. 컨셉에서 화면 위쪽 벽은 이미 남색 어둠에
  //   녹아 있고 그게 "깊이"의 정보다. near 는 초원과 같이 플레이어 뒤에 둔다
  //   (여기를 당기면 캐릭터가 안개를 먹어 실루엣이 흐려진다).
  scene.fog.near = dist + (IS_DUNGEON ? 4 : 2);
  // ★14차. 던전 안개를 17 -> 30 으로 넓혔다. 안개색이 배경색(#1a1636, 어둡다)이라
  //   좁으면 화면 위쪽 절반이 통째로 그 어둠으로 덮인다 — 밝은 카툰과 정면으로 싸운다.
  scene.fog.far = dist + (IS_DUNGEON ? 38 : 30);
  const half = 10 * (dist / CAM.dist);
  const sc = key.shadow.camera;
  sc.left = -half; sc.right = half; sc.top = half; sc.bottom = -half;
  sc.far = 20 + dist;
  sc.updateProjectionMatrix();
}
addEventListener('wheel', e => {
  const d0 = dist;
  dist = Math.max(DIST_MIN, Math.min(DIST_MAX, dist + e.deltaY * 0.010));
  if (dist !== d0) applyDist();
}, { passive: true });
applyDist();
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
  _rt.setSize(innerWidth * renderer.getPixelRatio(), innerHeight * renderer.getPixelRatio());
  bloom.setSize(innerWidth, innerHeight);
});

// 속성 표. 팔레트 순서 = 짙은심 / 진한 / 중간 / 밝은1 / 밝은2 / 최명 / 코어
//   wrap  : 칼을 감는 리본을 쓸 것인가 (기본칼은 안 쓴다)
//   spray : 흩날리는 조각 양 배수
//   style : 0 = 칠한 2D 원소 효과, 1 = 평범한 검기(단순 3단 흰빛)
//   tGain : 궤적 리본 **폭** 배수 (없으면 1). 칼끝 바깥으로 얼마나 부푸는가
//   tAlpha: 궤적 **알파** 배수 (없으면 1)
// ★tGain·tAlpha 는 2026-08-10 2차 QA(S6) 때 생겼다. 그전에는 칼마다 궤적 상수가
//   따로 없었다(7자루가 폭·알파를 통째로 공유). 그래서 "어떤 칼만 크다"를 조절할
//   손잡이 자체가 없었다. 기본값 1 이라 안 적은 칼은 예전과 100% 같다.
// ★밝기 계단 구조는 전 속성이 같다. 구조까지 바꾸면 "칠한 그림" 느낌이 깨진다.
const HEX = h => [parseInt(h.slice(0,2),16)/255, parseInt(h.slice(2,4),16)/255, parseInt(h.slice(4,6),16)/255];
const ELEMENTS = {
  // 1번 기본칼: 원소 없음. 감는 리본도 없고 조각도 없다. 뒤에 남는 꼬리만.
  // 기본칼 검기. 회색이면 칙칙해서 밝은 하늘색으로(오너 지시).
  // style=1 셰이더는 안쪽부터 uPal[6](흰 심) - uPal[5] - uPal[3](가장자리) 세 단만 쓴다.
  // ★v94. 1번 칼 하한(심사: "1번 녹슨 칼은 이펙트가 사실상 안 보인다").
  //   ① 0번 자리를 **진짜 먹**(#0A1220)으로. 이 자리가 style=1 셰이더의 바깥 한 겹,
  //      곧 획의 경계선이다. 옛 값 #2A5A7A 는 중간 명도 청회색이라 밝은 산야 배경에
  //      그대로 녹았다(= 형태를 정의하는 선이 없었다).
  //   ② tGain/tAlpha 하한. 다른 칼들은 텍스처(찢긴 가장자리·구멍)를 입어 면적이
  //      작아도 읽히는데, 이 칼은 절차로 얇은 호 하나만 그린다. 폭·알파를 올려서
  //      "봉인칼이라 수수하다"와 "안 보인다" 사이의 선을 넘게 한다.
  plain:  { p:['0A1220','3E86AE','62A8CE','7FD4F5','A8E4FA','D8F4FF','FFFFFF'],
            wrap:0, spray:0.0, style:1, tGain:1.28, tAlpha:1.0 },
  // ★★v99(11-FX-B). 물 팔레트를 통째로 갈았다 — **채도 상향**. 여기가 그 손잡이다.
  //   증상: 획 화소의 화면 채도 중앙이 0.21~0.27 이라 밝은 모래 배경 위에서
  //         "물빛"이 아니라 연회색 판으로 읽혔다(오너가 그림체를 칭찬한 v95 는 0.31~0.48).
  //   ★진범은 팔레트 숫자가 아니라 **ACES 톤매핑**이었다. 셰이더가 내는 색은 선형으로
  //     취급되고, renderer.toneMapping = ACESFilmicToneMapping 이 밝은 쪽을 흰색으로
  //     말아 올리면서 **채도를 통째로 먹는다.** 옛 값을 통과시켜 보면:
  //         #4884A2 원채도 0.556 -> 화면 #86AAB6 채도 **0.264**
  //         #549CBA        0.548 -> 화면 #92B5BF        **0.232**
  //         #72C0E4        0.500 -> 화면 #A7C2CA        **0.173**
  //     그래서 "팔레트 채도 0.55" 라는 옛 기록은 화면에 대한 참말이 아니었다.
  //     ACES 를 지나고도 채도가 남으려면 **빨강을 비우고 초록·파랑으로 밝기를 든다**
  //     (같은 화면 휘도에서 시안 계열이 가장 채도를 지킨다. 밝기를 R 이 지면 곧 흰색이 된다).
  //   그래서 값을 화면(=ACES 통과 후)에서 역산해 골랐다. 괄호가 화면에 앉는 값이다:
  //     0 먹     #112F54 -> (#2C5F86 휘도 87  채도 0.67)   6 흰심 #E8F2FA -> (#CCCECF 206 0.02)
  //     1 감청   #186095 -> (#4693B0     133      0.60)
  //     2 중간   #1E81B1 -> (#59A8BB     153      0.52)
  //     3 밝은1  #239DCC -> (#69B6C3     166      0.46)
  //     4 밝은2  #38A5D0 -> (#80B9C5     174      0.35)
  //     5 최명   #3BCCF9 -> (#8BC5CE     186      0.32)
  //   ★색상(b/g 비)은 원작 밴드의 회전을 그대로 옮겼다 — 먹 1.78 -> 감청 1.55 ->
  //     시안 1.38 -> 1.30 -> 1.22. 한 색상으로 통일하면 밴드가 한 판으로 뭉친다.
  //   ★휘도는 옛 값보다 **감청만 올렸다**(112 -> 133). 획 면적의 대부분이 꼬리인데
  //     꼬리가 감청으로 내려앉으므로(셰이더 ls 계단), 이 자리가 낮으면 획 평균 휘도가
  //     배경(모래 ~156) 아래로 뒤집힌다(v98 실측 -8.9). 나머지는 낮추거나 유지했다.
  //   ★블룸은 안 건드렸다(오너 판정 보류). 어차피 진범이 아니다 - 블룸 임계는 1.02 라
  //     1.0 을 안 넘는 획 자체는 거의 안 번진다.
  water:  { p:['112F54','186095','1E81B1','239DCC','38A5D0','3BCCF9','E8F2FA'], wrap:1, spray:1.0, style:0 },
  // 불은 물과 정반대 구조다. 물은 바깥에 흰 포말이 붙지만 불은 **안쪽이 가장 뜨겁고**
  // 바깥으로 갈수록 식어 검붉게 스러진다. 경계도 매끈한 호가 아니라 혀다. style=2
  fire:   { p:['4A0E08','8C1A0C','C4321A','E85E1C','F58C22','FFC63E','FFF0C8'], wrap:1, spray:1.1, style:2, rise:1 },
  ice:    { p:['0E3A52','1A5C7A','3E93B4','6FBAD2','9AD6E6','C8EEF6','FFFFFF'], wrap:1, spray:1.3, style:0 },
  poison: { p:['14320E','24521A','47892E','6FB343','96D160','C6EC93','E9FBC8'], wrap:1, spray:0.8, style:0 },
  earth:  { p:['33231A','55392A','856046','A97F5C','C69D77','E0C3A0','F2E2CC'], wrap:1, spray:1.2, style:0 },
  // ★어둑(7번)만 폭·알파를 줄여 둔다(2차 QA S6 "보라 리본이 화면을 덮는다").
  //   원인은 상수가 아니라 **경로**였다: 백아·홍염은 구운 손그림 텍스처를 입어서
  //   가장자리가 찢겨 있고 구멍이 뚫려 있는데(uUseTex=1), 텍스처가 없는 칼은
  //   절차 분기로 리본을 **꽉 채워** 칠한다. 같은 지오메트리인데 어둑만 통판으로 보이는 이유다.
  //   팔레트(어두운 보라)는 그대로 두고 면적만 줄인다. 값은 실측으로 골랐다
  //   (Z 연타 최악 프레임 덮임 9.31% -> 백아 8.40% 아래로).
  dark:   { p:['140E1E','261A38','452F63','63478C','8467B0','AC93D0','E4DCF2'],
            wrap:1, spray:0.6, style:0, tGain:0.72, tAlpha:0.82 },
};
const PAL = {};
for (const k in ELEMENTS) PAL[k] = ELEMENTS[k].p.map(h => new THREE.Vector3(...HEX(h)));
// ── 손그림 파도 텍스처 ──
// GLSL 노이즈로는 붓 느낌이 안 나온다(3번 실패). 원본 프레임을 픽셀 클러스터링한
// 색(#1E82AA 청록 / #285AA0 파랑 / #001428 잉크 / #C8D2D2 포말)으로 오프라인에서
// 그려 구운 텍스처를 입는다. 리본의 띠 구조·갓선·포말·찢긴 가장자리가 다 그림에 있다.
const texLoader = new THREE.TextureLoader();
const WAVETEX = {
  water: texLoader.load('./tex/wave_water.png'),
  fire: texLoader.load('./tex/wave_fire.png'),
};
for (const k in WAVETEX) {
  WAVETEX[k].wrapS = THREE.RepeatWrapping;
  WAVETEX[k].wrapT = THREE.ClampToEdgeWrapping;
  WAVETEX[k].colorSpace = THREE.SRGBColorSpace;
}

// ── 참격 그림은 여기서 안 읽는다 (v92) ──
// 예전에는 이 자리에서 tex/brush_slash.png(옛 붓자국 한 장)와 tex/hit_spark.png
// (초승달에 겹치던 별빛)를 읽어 feel.js·arcMat 에 넘겼다. 셋 다 없앴다:
//   · 참격은 v91 부터 플립북 시트(tex/slash_flip.png)이고 그 시트는 feel.js 가 직접 읽는다
//   · 초승달(가산합성)과 별빛은 v92 에서 그 플립북으로 통째로 갈렸다
// 그래서 여기 남아 있던 setTimeout(0) 지연 로드 한 뭉치가 통째로 죽은 코드였다
// (TDZ 를 피하려고 setTimeout 을 쓰던 자리 - 이제 참조할 대상 자체가 없다).

let curEl = ELEMENTS.water;
function setElement(name) {
  const e = ELEMENTS[name] || ELEMENTS.water;
  curEl = e;
  const p = PAL[name] || PAL.water;
  trailMat.uniforms.uPal.value = p;
  trailMat.uniforms.uStyle.value = e.style;
  const wt = WAVETEX[name];
  trailMat.uniforms.uTex.value = wt || WAVETEX.water;
  trailMat.uniforms.uUseTex.value = wt ? 1 : 0;
  wrapMat.uniforms.uPal.value = p;
  wrapMat.uniforms.uStyle.value = e.style;
  sprayMat.uniforms.uPal.value = p;
  sprayMat.uniforms.uRise.value = e.rise || 0;
  // ★18차. 접점 파열의 색 계단도 이 칼의 팔레트에서 온다(안 물리면 불칼에서도
  //   시안 파열이 터진다). 인자는 **선형 vec3** - uPal 과 같은 자다(feel.js 주석 참조).
  //   ★자리는 궤적 코어와 **같은 칸**에서 뽑는다(흰심 6 · 시안 3 · 중간 2 · 감청 1).
  //   5번(최명)은 어느 칼이든 거의 흰색이라 흰 심 옆에 두면 두 단이 뭉친다.
  if (FX_V18 && feel.setBurstPalette) feel.setBurstPalette(p[6], p[3], p[2], p[1]);
}

// ═══════════════════════════════════════════════════════════════════════════
// 칼 이펙트 **4벌 선택 메뉴** (12-FX-D. ?fx=a|b|c|d · 기본 a)
//
// 오너가 이펙트를 네 번 다시 주문했고 매번 한 가지 해석으로 구현한 것이 어긋났다.
// ("v95 너무 큼" -> "너무 줄임" -> "별똥별로" -> "다 이상해, 다시 만들어")
// 그래서 이번 판은 **해석을 하나 더 하지 않는다.** 뚜렷이 다른 네 벌을 같이 얹고
// 오너가 눈으로 고른다. 고르고 나면 진 셋을 지우고 이 표를 상수로 펴면 된다.
//
// 네 벌이 **공통으로 지키는 것**(오너가 일관되게 말한 것):
//   · 이펙트는 **칼이 지나간 자리**를 따라 표현된다. 화면에 붕 뜬 큰 판은 없다
//     (모든 가닥의 발원이 칼끝 궤적 _c 이고, 리치 3.2m·부채꼴 ±75° 안에서만 그린다).
//   · 귀멸 계열 = 먹으로 형태를 정의하고 평칠한다(그라데이션·반투명 유리 부채 금지).
//   · 과대 금지 = BODY_R 안에는 한 화소도 안 그리고 OUT_R 밖으로도 안 나간다.
//   · **처치 백색 패널·진홍 초승달 문법은 네 벌 공통이고 한 글자도 안 건드렸다**
//     (그 자리는 feel.js 소유다).
//
// 손잡이는 전부 아래 표 한 곳에 모았다. 셰이더는 uMode 로 갈린다.
//   mode 0 = A 혜성 정제   1 = B 귀멸 리본   2 = C v95 정박판   3 = D 샤프 잔광
// ═══════════════════════════════════════════════════════════════════════════
// ★★18차. 벌이 하나 늘었다 — **V 이아이도 일섬**(FX_TABLE.v · mode 4).
//   기본값이 FX_V18 로 갈린다:
//     FX_V18 = 1 -> 기본 v(일섬).  ?fx=b 로 **17차 B 리본을 그대로 열람**한다(A/B 대조).
//     FX_V18 = 0 -> 기본 b. 이 함수가 내는 값이 17차와 **문자 하나 안 다르다.**
//   a/c/d 대조군 셋은 어느 쪽에서도 손대지 않는다(?fx= 로 그대로 열린다).
const FX_STYLE = (() => {
  const v = (new URLSearchParams(location.search).get('fx') || '').toLowerCase();
  if (v === 'a' || v === 'c' || v === 'd') return v;
  if (v === 'b') return 'b';                 // 옛 귀멸 리본 열람 창구
  if (v === 'v') return FX_V18 ? 'v' : 'b';  // 스위치가 내려가 있으면 v 를 못 연다
  return FX_V18 ? 'v' : 'b';
})();
const RIBBON_V2 = 1;  // 0 = B 리본과 봉인칼 호를 16차 2라운드 직전 그림으로 함께 롤백
const FX_TABLE = {};
{
  // ── A 혜성 정제 ── 현행(11차 혜성판)의 소폭 개선. 가장 저위험.
  //   폭을 한 단 키우고(방의 46%) · 흰 심이 꼬리까지 관통(화소 하한 보장) ·
  //   머리 말림(호쿠사이 갈퀴) 강화(손가락 갈래를 굵고 잦게. 셰이더 clawAmp).
  // ★★2026-08-11. cfg 의 단위가 바뀌었다(오너 지시 "칼은 짧은데 효과가 길다").
  //   w     = 반폭. **칼이 쓸고 간 방(칼끝 반경 - 몸 반경)의 비율**이다. 미터가 아니다.
  //   inset = 바깥 가장자리가 칼끝에서 안쪽으로 물러난 양(같은 방 비율).
  //           0 = 칼끝에 붙은 마루(포말·갈퀴). 클수록 몸 쪽에 눕는 겹 획.
  //   계약: inset + 2w <= 1 이면 획이 통째로 [몸 반경 .. 칼끝 반경] 안에 든다.
  //   ★아래 half 값은 이제 **표시용**이다(판정지에 적는 대표 폭 비율).
  const HA = 0.46;
  FX_TABLE.a = {
    key: 'a', name: 'A 혜성 정제', mode: 0, half: HA, trailMax: 34,
    ladder:  [1.00, 1.00, 1.00, 0.98, 0.94, 0.88, 0.80, 0.70, 0.60, 0.48, 0.34],
    // ★2026-08-11 오너 지시 2항("꼬리가 칼보다 길게 남는다"). 수명(칸 수)은 그대로 두고
    //   **폭 사다리만** 뒤에서 급히 내렸다(꼬리 끝 0.16 -> 0.06). 칸은 살아 있되 면적이 없다.
    ladderW: [1.00, 1.00, 0.97, 0.92, 0.84, 0.74, 0.62, 0.48, 0.34, 0.18, 0.06],
    profile: 'comet', comet: { head: 0.26, nose: 0.70, tailp: 1.45, tail: 0.04 },
    offK: [0.30, 0.70], headSpan: 0.52, alpha: 'binary', tipK: 1.03,
    bodyR: 0.82, outR: 3.50, sprayK: 1.0, wrapK: 1.0,
    cfg: [
      // 갈퀴(호쿠사이 claw) = **칼끝에 붙은 마루**. 그래서 inset 0.
      // ★말림은 폭이 아니라 갈래(셰이더 clawAmp)에서 나온다. 1차 시도에서 폭으로
      //   키웠더니 흰 판때기가 됐다(실측 크롭).
      { kind: 2, at: 0.96, w: 0.09, inset: 0.00, headOnly: 1, lifeK: 0.72 },
      // 본 획: 마루 바로 안쪽. 방의 3분의 2를 쓴다.
      { kind: 0, at: 0.90, w: HA,   inset: 0.02, headOnly: 0, lifeK: 1.00 },
      // 겹 획: 더 안쪽에 눕는 둘째 붓(먹 외곽선이 가닥마다 제 경계를 그어 준다).
      { kind: 1, at: 0.84, w: 0.22, inset: 0.34, headOnly: 0, lifeK: 0.86 },
    ],
  };
  // ── B 귀멸 리본 ── 애니의 "물이 흐르는 띠" 인상에 가장 근접한 판.
  //   궤적을 따라 **두툼한 물 리본**이 지나가고 그 안에서 wave_water 질감이
  //   길이 방향으로 흐른다(UV 스크롤. 1/24 로 끊어 흘려야 CG 가 안 된다).
  //   바깥 가장자리에 흰 포말 점 + 전체를 먹으로 두른다.
  // ★A 와 다른 점은 **길이 방향 단면**이다. A(혜성)는 앞쪽이 최대이고 뒤가 급히
  //   빠지는데, 리본은 코가 두껍고(nose 0.78) 몸통이 길게 간다(tailp 1.18).
  //   그래서 "머리만 밝은 별똥별"이 아니라 "흐르는 띠"로 읽힌다.
  // 수명 11칸 = 0.458초(지시 0.4~0.5초).
  // ★1차 시도 반성: 꼬리 지수를 0.72 로 두니 **꼬리까지 두툼한 넓은 깃발**이 되어
  //   오너가 두 번 지적한 '판때기'로 읽혔다(실측 크롭 z3). 리본은 두툼하되
  //   **흐르는 띠**여야 하므로 꼬리를 제대로 빼도록 고쳤다.
  const HB = 0.48;
  FX_TABLE.b = {
    key: 'b', name: 'B 귀멸 리본', mode: 1, half: HB, trailMax: 34,
    ladder:  [1.00, 1.00, 1.00, 1.00, 0.98, 0.95, 0.90, 0.83, 0.73, 0.58, 0.36],
    // ★리본이라 A 보다는 늦게 빠지되(몸통이 길게 사는 것이 이 벌의 정체성) 꼬리 끝은
    //   같이 얇힌다(0.36 -> 0.12). 오너 지시 2항.
    ladderW: [1.00, 1.00, 1.00, 0.98, 0.94, 0.88, 0.80, 0.70, 0.56, 0.38, 0.12],
    profile: 'comet', comet: { head: 0.32, nose: 0.78, tailp: 1.18, tail: 0.06 },
    offK: [0.45, 0.55], headSpan: 0.55, alpha: 'binary', tipK: 1.03,
    // ★16-FX. sprayK 1.0 -> 0. 오너 지시 "물방울이 튀기듯이 그거 너무별로야".
    //   spawnSpray 가 `if (!ink) count *= FX.sprayK` 이므로 이 한 자리는 **물보라만**
    //   죽인다(처치의 붉은 먹물 튐 spawnInk 는 ink=1 이라 배수를 안 탄다 - 그대로 산다).
    //   흰 거품은 이제 feel.js 의 포말 마루층이 리본 바깥면에 붙여 그린다.
    bodyR: 0.82, outR: 3.50, sprayK: 0.0, wrapK: 1.0,
    cfg: RIBBON_V2 ? [
      // 바깥 마루의 inset 0 은 feel.js 포말 정박 계약이다. 본 리본은 기존 기하를
      // 그대로 두고, 안쪽 겹 리본 한 가닥만 더해 독립 먹 경계를 만든다.
      { kind: 2, at: 0.95, w: 0.09, inset: 0.00, headOnly: 1, lifeK: 0.80 },
      { kind: 0, at: 0.90, w: HB,   inset: 0.02, headOnly: 0, lifeK: 1.00 },
      { kind: 1, at: 0.84, w: 0.16, inset: 0.64, headOnly: 0, lifeK: 0.86 },
    ] : [
      // 포말 마루 = 칼끝에 붙는다. 리본 본체는 그 바로 안쪽에서 방을 넓게 쓴다.
      { kind: 2, at: 0.95, w: 0.09, inset: 0.00, headOnly: 1, lifeK: 0.80 },
      { kind: 0, at: 0.90, w: HB,   inset: 0.02, headOnly: 0, lifeK: 1.00 },
    ],
  };
  // ── C v95 정박판 ── 오너가 "그림체 좋았다"던 9차(v95)의 **풍성한 밴드 채색**만
  //   가져오고, v95 가 같이 갖고 있던 화면좌표 붓자국·허공 판때기는 안 가져온다.
  //   원본 소스 = renders/history/v98_wave12/fx_restore/v95_source/main.js
  // 가져온 것: 다섯 가닥 · 구운 손그림이 색을 통째로 담당(ct = tx.rgb) ·
  //   나이 4단 양자화 · pow 1.18 채도 · 굵은 먹 밴드(머리 굵고 꼬리 얇게) ·
  //   테이퍼 (1 - 0.78 un^2) · 알파 3단 계단 · 수명 여섯 칸(0.25초).
  // 안 가져온 것: at 0.62(칼 중간) 발원 · off 1.16m 부채 · SCREEN_STROKE 화면 겹.
  //   at 은 전부 0.86~0.98(칼끝)로 당기고 off 는 OUT_R 예산 안으로 조였다.
  const HC = 0.28;
  FX_TABLE.c = {
    key: 'c', name: 'C v95 정박판', mode: 2, half: HC, trailMax: 22,
    ladder:  [1.00, 1.00, 0.92, 0.78, 0.34, 0.18],
    // ★C 는 원래 여섯 칸(0.25초)이라 꼬리가 짧다. 그래도 마지막 두 칸을 한 단 더 얇혔다.
    ladderW: [1.00, 1.00, 0.92, 0.74, 0.22, 0.08],
    profile: 'v95', comet: null,
    offK: [0.72, 0.28], headSpan: 0.42, alpha: 'v95', tipK: 1.03,
    bodyR: 0.82, outR: 3.50, sprayK: 1.15, wrapK: 1.0,
    // ★v95 는 다섯 붓이 **나란히 겹쳐 그어진** 그림이다. 그 배치를 방 비율로 옮겼다 —
    //   칼끝에서부터 마루 · 바깥 몸통 · 가는 심 · 안쪽 몸통 · 손 언저리 순으로 눕는다.
    cfg: [
      { kind: 1, at: 0.96, w: 0.09, inset: 0.00, headOnly: 0, lifeK: 0.80 },
      { kind: 0, at: 0.92, w: 0.30, inset: 0.05, headOnly: 0, lifeK: 0.94 },
      { kind: 2, at: 0.90, w: 0.05, inset: 0.32, headOnly: 0, lifeK: 0.88 },
      { kind: 0, at: 0.88, w: HC,   inset: 0.40, headOnly: 0, lifeK: 1.00 },
      { kind: 1, at: 0.86, w: 0.14, inset: 0.66, headOnly: 1, lifeK: 0.72 },
    ],
  };
  // ── D 샤프 잔광 ── 대조군. 밝은 코어 한 획 + 짧은 잔광. 밴드도 붓결도 없다.
  //   롤·상용 액션 게임의 문법이다(귀멸 문법이 아닌 쪽을 한 칸 놓아 봐야 오너가
  //   "귀멸 계열이 맞다"를 눈으로 확인할 수 있다).
  // ★네 벌 중 여기만 알파가 부드럽다(잔광이 그 자체로 목적이라). 그래도 1/24
  //   계단은 지킨다 - 60fps 로 미끄러지면 그 순간 통째로 CG 가 된다.
  const HD = 0.20;
  FX_TABLE.d = {
    key: 'd', name: 'D 샤프 잔광', mode: 3, half: HD, trailMax: 20,
    ladder:  [1.00, 1.00, 0.90, 0.74, 0.52, 0.30],
    ladderW: [1.00, 0.94, 0.80, 0.60, 0.36, 0.12],
    profile: 'comet', comet: { head: 0.10, nose: 0.82, tailp: 2.10, tail: 0.03 },
    offK: [0.30, 0.70], headSpan: 0.42, alpha: 'soft', tipK: 1.03,
    bodyR: 0.82, outR: 3.50, sprayK: 0.40, wrapK: 0.50,
    cfg: [
      { kind: 0, at: 0.92, w: HD, inset: 0.03, headOnly: 0, lifeK: 1.00 },
    ],
  };
  // ═══════════════════════════════════════════════════════════════════════
  // ── V 이아이도 일섬 (18차. 오너 지시 "기존 무시하고 새로. 귀멸처럼 말고") ──
  //
  // **두툼한 리본의 정반대다.** 네 벌(A~D)이 공유하던 전제 — 궤적을 면으로 채우고
  // 먹으로 두른다 — 를 여기서만 버린다. 대신 거합(居合)의 한 순간을 그린다:
  //   형태  칼끝 궤적을 따르는 **가는 코어**(흰~시안) 한 줄 + 바깥 **블루 글로우** 한 겹.
  //         코어 반폭 0.105(방 비율) = B 리본(0.48)의 **22%**. 지시의 "1/4 이하".
  //         양끝은 바늘이다(코 0.30 · 꼬리 0.00 · 지수 2.30 = 급감쇠).
  //   시간  **5칸 = 0.208초.** B 는 11칸(0.458초)이었다. 베는 순간 번쩍 서고 사라진다.
  //   색    흰 코어 -> 시안 -> 딥블루 감쇠. 먹선이 **없다**(먹은 귀멸의 언어다).
  //         UI 의 시스템 시안(#56D8FF)·던전 마력 웅덩이와 같은 언어로 맞췄다.
  //   합성  **가산(Additive)**. 네 벌은 전부 NormalBlending(평칠)이었다 — 그 문법에서
  //         '섬광'은 원리상 안 나온다. 코어는 선형 1.7~2.0 이라 블룸 문턱(1.02)을
  //         넘겨 그 한 줄만 번진다(tools/aces_screen.py 역산. 선형 1.0 = 화면 209).
  // ★물보라(sprayK)와 감김 리본(wrapK)을 **둘 다 0** 으로 내린다. 둘 다 물의 언어라
  //   섬광 한 줄 옆에 서면 그림이 두 벌로 갈린다(오너: "물방울 튀기는 거 너무 별로").
  //   feel.js 의 포말 마루도 같은 이유로 FX_V18 게이트에서 끊는다.
  // ★trailMax 16 = 0.267초 보관. 수명이 5칸(0.208초)이라 60fps 에서 살아 있는 표본이
  //   12.5개다. 34(B) 를 그대로 두면 마디 140개 중 앞 37% 만 살고 나머지가 헛 지오메트리다.
  const HV = 0.105;
  FX_TABLE.v = {
    key: 'v', name: 'V 이아이도 일섬', mode: 4, half: HV, trailMax: 16,
    // 5칸 = 0.208초. 세기는 앞 두 칸만 온전하고 뒤 세 칸에서 급히 빠진다.
    ladder:  [1.00, 1.00, 0.86, 0.52, 0.22],
    // 폭도 같이 빠진다. 마지막 칸은 0.16 이라 면적이 아니라 **선**만 남는다.
    ladderW: [1.00, 0.96, 0.74, 0.42, 0.16],
    profile: 'comet', comet: { head: 0.09, nose: 0.30, tailp: 2.30, tail: 0.00 },
    offK: [0.30, 0.70], headSpan: 0.40, alpha: 'flash', tipK: 1.03,
    bodyR: 0.82, outR: 3.50, sprayK: 0.0, wrapK: 0.0,
    cfg: [
      // 코어: 칼끝에서 방의 10% 안쪽에 서는 가는 심. 이게 곧 '일섬'이다.
      { kind: 0, at: 0.94, w: HV,  inset: 0.10, headOnly: 0, lifeK: 1.00 },
      // 글로우: 코어를 감싸는 한 겹. 바깥 가장자리는 칼끝에 정박(inset 0)하고
      // 안쪽으로 넓게 눕는다. 색이 딥블루라 면적이 넓어도 무게가 안 실린다.
      { kind: 1, at: 0.94, w: 0.30, inset: 0.00, headOnly: 0, lifeK: 0.78 },
    ],
  };
}
const FX = FX_TABLE[FX_STYLE];

// ---------- 칼 궤적(물의 호흡) ----------
// 목표는 "빛나는 띠"가 아니라 **납작하게 칠한 2D 파도 그림**이다.
// 예전엔 AdditiveBlending 이라 겹칠수록 흰색으로 타서 번쩍였고, 정점 색 2개를
// 그라데이션으로 섞을 뿐이라 줄무늬가 없었다. 레퍼런스(water-breathing.mp4
// c_06 프레임)의 리본 단면을 픽셀로 재보면 이렇게 칠해져 있다:
//   연하늘 → 밝은시안 → 진파랑 → 남색 → 아주진한남색 → 흰선 → 밝은시안 → 흰 포말(제일 넓음)
// 경계는 흐리지 않고 딱 끊긴다. 그래서 색 계단은 프래그먼트에서 계산한다
// (정점 보간으로 하면 아무리 색을 넣어도 그라데이션이 된다).
// ── 24fps 양자화 (v92) ──
// ★참격·임팩트 컷·속도선은 v91 에서 전부 1/24 로 끊어 그리게 바꿨는데(feel.js)
//   화면에서 제일 크게 보이는 **궤적 리본만 60fps 로 매끈하게** 자라고 있었다.
//   그래서 다 고쳤는데도 "효과가 그대로"로 읽혔다. 여기가 그 마지막 조각이다.
// 두 가지를 한다:
//   1) **프레임 홀드**: 같은 1/24 칸 안에서는 리본을 아예 다시 안 그린다.
//      60fps 화면에서 같은 그림이 2~3프레임 붙들려 있고(3-2-3-2), 그게 계단감이다.
//   2) **폭·알파 양자화**: 마디의 세기를 1/24 로 끊는다. 굵기와 알파가 같은 계단을
//      밟아야 리본이 여러 겹이 아니라 한 장으로 읽힌다.
// ★히트스톱은 저절로 물린다. 이 시계가 게임시간(gameT)이라 멈춘 동안은 칸 번호가
//   안 바뀌고, 리본은 **그 한 장을 붙들고 있는다**(연출 의도 그대로).
//   셰이더 안의 재시딩도 이미 floor(uT*24.0) 이라 같은 칸에서 같은 씨앗이 나온다.
const FX_FPS = 24;
// ★22차 멀티. 여기 있던 trailQFrame·trailHold 는 rig 필드(R.q·R.hold)로 옮겼다 -
//   사람마다 제 칸 번호를 가져야 하기 때문이다(전역 한 벌이면 두 번째 사람의
//   호출이 첫 번째 사람의 칸을 이미 써먹은 것으로 보고 통째로 건너뛴다).
// ★v94. 64 -> 22. 수명이 여섯 칸(0.25초)으로 짧아졌으므로 60fps 에서 살아 있는
//   샘플은 15개뿐이다. 64를 그대로 두면 마디 220개 중 앞 4분의 1만 살아 있고
//   나머지는 알파 0 인 헛 지오메트리가 된다(길이 방향 테이퍼·텍스처 스크롤이
//   전부 앞 4분의 1 안에서만 일어나 꼬리가 안 빠진다).
// ★v98(11차). 22 -> 34. 수명을 다섯 칸 -> **열한 칸**(0.458초)으로 늘렸다(오너 지시
//   "꼬리감을 위해 8~14칸"). 60fps 에서 열한 칸이면 살아 있는 샘플이 27.5개라
//   22로는 꼬리가 버퍼 앞에서 잘려 나간다. 보관은 34(0.567초)로 여유를 둔다.
// ★12-FX-D. 벌마다 수명이 다르므로 보관 수도 표에서 온다(A/B 34 · C 22 · D 20).
const TRAIL_MAX = FX.trailMax;     // 보관 샘플 수(원본)
const RIBS = 140;                  // 실제로 그리는 마디 수. 원본을 곡선 보간해 늘린다.
                                   // 34개를 그대로 이으면 빠른 호에서 각이 눈에 띈다.
// ── v96. 가닥 다섯 -> 하나 -> **셋** (오너 직접 지시가 두 번 왔다) ──
// 1차(10-FX) 지시: "이펙트 효과가 칼 근처에서만 나타나야 하는데 뭔 화면의 1/3 덮는
//   수준이여." -> 다섯 가닥(off 최대 1.16m x gain)이 만들던 **부채**를 한 가닥으로 줄였다.
// 2차(10-FX-B) 지시: "칼 이펙트 너무 줄여놨는데? 그림체나 이런 것들 좋았는데 아예
//   간소하게 바뀌었네... 모양이 좀 이상하고 큰 게 문제였지."
//   즉 **크기가 아니라 모양**이 문제였고, 한 가닥으로 줄이면서 그림체까지 깎였다.
// 그래서 지금은 이렇게 갈랐다 —
//   · 모양(1차에서 얻은 것)은 그대로 지킨다: 칼끝 궤적 발원 · 양끝이 뾰족한 호 ·
//     리치 3.2m/±75° 정합 · 닫힌 다각형 덩어리 금지 · 화면좌표 붓자국 없음
//   · 그림체(9차에서 좋았던 것)를 되살린다: 한 획이 아니라 **겹친 붓 셋**이고
//     가닥마다 제 먹 외곽선과 제 흰 심을 가진다(9차 프레임이 그렇게 칠해져 있다)
//   · 크기는 9차와 10차의 **중간점**(아래 TRAIL_HALF 한 숫자로 조인다)
// ★셋은 다 **같은 칼끝 궤적에서** 자란다. 9차처럼 화면 좌표로 몸 옆 허공에 띄우지
//   않는다 - 그 문법은 원리상 "칼 근처"일 수가 없어서 1차 지시로 폐기됐다.
// ★12-FX-D. 가닥 수도 표에서 온다(A 3 · B 2 · C 5 · D 1). 지오메트리 크기가
//   여기서 정해지므로 벌 전환은 새로고침(?fx=..)이다 - 그래서 한 벌만 메모리에 산다.
const STRANDS = FX.cfg.length;
const trailBuf = [];               // {a:Vec3, b:Vec3, t:number}  ★로컬 플레이어의 샘플 통
const segs = RIBS - 1;
const vtxCount = STRANDS * RIBS * 2;
// ── 이 마디의 반폭(m). 먹 외곽선이 **화면에서 늘 한 겹 이상** 살아남게 하는 자다 ──
// ★셰이더는 폭 좌표를 0..1 로만 안다. 그래서 "먹을 바깥 14%"로 적으면 획이 굵을 땐
//   먹이 20px 판때기가 되고(그게 9차의 '어두운 판때기'), 가늘 땐 0px 가 되어 형태를
//   정의하는 선이 사라진다(그게 10차 태생·소멸 프레임의 먹선 0%). 반폭을 미터로
//   넘기고 uPxPerM 과 곱해 **화소로 환산**하면 두 실패가 같이 없어진다(halfArr).
// ══════════════════════════════════════════════════════════════════════════
// ★★22차 멀티. 궤적 한 벌 = **rig** (2026-08-20)
// 예전에는 이 배열들이 전부 모듈 전역 **한 벌**이었다. 남의 칼에도 같은 궤적을
// 그리려면 사람마다 제 버퍼가 있어야 해서 그릇만 factory 로 뺐다.
// ★계산은 여전히 **한 벌**이다(buildRibbon 하나). 여기서 만드는 건 그릇뿐이고,
//   그래서 두 벌이 어긋날 자리가 원리적으로 없다 - 이 레포가 반복해서 배운 것
//   ("스위치도 계산도 한 곳에서만")을 그대로 지킨 모양이다.
// ★한 벌의 무게(실측 계산): 정점 STRANDS(3) x RIBS(140) x 2 = 840개,
//   Float32 속성 다섯 = pos 10,080B + uv 6,720B + alpha/seed/half 3,360B x 3 =
//   **약 26.9KB** + 인덱스 2,502개. 원격 4명이어도 108KB 다.
function makeTrailRig(buf) {
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(vtxCount * 3);
  const uv = new Float32Array(vtxCount * 2);    // x=길이(0=최신), y=폭(0=칼날쪽,1=바깥)
  const alp = new Float32Array(vtxCount);
  const seed = new Float32Array(vtxCount);
  const half = new Float32Array(vtxCount);
  const idx = [];
  for (let s = 0; s < STRANDS; s++) {
    const off = s * RIBS * 2;
    for (let i = 0; i < segs; i++) {
      const a = off + i * 2;
      idx.push(a, a + 2, a + 3, a, a + 3, a + 1);
    }
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aUV', new THREE.BufferAttribute(uv, 2));
  geo.setAttribute('aAlpha', new THREE.BufferAttribute(alp, 1));
  geo.setAttribute('aSeed', new THREE.BufferAttribute(seed, 1));
  geo.setAttribute('aHalf', new THREE.BufferAttribute(half, 1));
  geo.setIndex(idx);
  return {
    buf: buf || [], geo, pos, uv, alp, seed, half,
    mat: null, mesh: null,
    q: -1, hold: 0,          // 1/24 칸 번호 · 붙들고 지나간 렌더 프레임 수
    clock: 0,                // 이 벌의 시계(초). 로컬 = gameT, 원격 = 벽시계(아래 주석)
    pos3: new THREE.Vector3(), yaw: 0, charH: 2.4,
    gain: 1, el: null, clip: null,
    dbg: false,              // window.__trailDbg 를 쓰는 벌(로컬 하나뿐)
  };
}
const LOCAL_RIG = makeTrailRig(trailBuf);
LOCAL_RIG.dbg = true;
const trailGeo = LOCAL_RIG.geo;     // 옛 이름 별칭(아래 trailMesh 가 이 이름으로 쓴다)

const trailMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, side: THREE.DoubleSide,
  // ★★18차. 일섬도 **평칠(Normal)**로 그린다. 가산을 먼저 해 보고 되돌린 자리다:
  //   가산이면 어두운 던전에서는 근사한데 **밝은 초원에서 통째로 씻긴다**(실측 T14 —
  //   풀밭 위에서 획이 흰 실오라기로 남았다). 가산은 배경보다 밝게만 할 수 있어서
  //   배경이 이미 밝으면 올릴 여지가 없다.
  //   평칠이면 두 가지가 같이 된다 —
  //     ① 코어는 **선형 1.85 를 그대로 프레임버퍼에 쓴다**. 문턱 1.02 를 넘으므로
  //        블룸은 가산 때와 똑같이 문다(번쩍임을 안 잃는다).
  //     ② 바깥 글로우(짙은 파랑, 알파 0.35)는 밝은 배경에서 **어둡게** 앉아 형태를
  //        정의하는 테가 된다. 가산으로는 원리상 못 하는 일이다.
  //   ★그래서 이 벌도 blending 은 네 벌과 같다(아래 삼항은 지금 항등이지만, 다시
  //     가산으로 돌려 볼 자리를 남겨 둔다).
  blending: THREE.NormalBlending,
  uniforms: { uPal: { value: null }, uStyle: { value: 0 }, uT: { value: 0 },
              uTex: { value: null }, uUseTex: { value: 0 },
              // ★12-FX-D. 네 벌의 채색 분기(0=A 혜성 · 1=B 리본 · 2=C v95 · 3=D 잔광).
              //   ★18차. 4 = V 일섬(가산 섬광). 기하(폭·수명·가닥)는 updateTrail 이,
              //   그림은 여기가 가른다.
              uMode: { value: FX.mode },
              uRibbonV2: { value: RIBBON_V2 },
              // ★18차 기술 변주(mode 4 전용). updateTrail 이 매 칸 갱신한다.
              //   uBolt 1 = 내려찍기(X). 코어를 계단 지그재그로 갉아 **수직 낙뢰**로 읽힌다.
              //   uSharp  = 코어 밝기 배수. 횡일섬(C)은 한 단 더 예리하게 든다.
              uBolt: { value: 0 },
              uSharp: { value: 1 },
              // 1m 가 화면에서 몇 화소인가(플레이어 깊이 기준). updateTrail 이 매 칸 갱신
              uPxPerM: { value: 50 } },
  vertexShader: `
    attribute float aAlpha;
    attribute vec2 aUV;
    attribute float aSeed;
    attribute float aHalf;
    varying vec2 vUV; varying float vA; varying float vSeed; varying float vHalf;
    void main(){ vUV = aUV; vA = aAlpha; vSeed = aSeed; vHalf = aHalf;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `
    varying vec2 vUV; varying float vA; varying float vSeed; varying float vHalf;
    uniform vec3 uPal[7];
    uniform float uStyle;      // 1 = 평범한 검기, 2 = 불꽃
    uniform float uT;
    uniform sampler2D uTex;
    uniform float uUseTex;
    uniform float uMode;       // 0=A 혜성 · 1=B 리본 · 2=C v95 · 3=D 잔광 · 4=V 일섬
    uniform float uRibbonV2;   // 1=B·봉인칼 V2 · 0=둘 다 직전 채색
    uniform float uBolt;       // 18차. 1 = 내려찍기(낙뢰 지그재그)
    uniform float uSharp;      // 18차. 코어 밝기 배수(기술별)
    uniform float uPxPerM;
    #define C_DK2 uPal[0]
    #define C_DK1 uPal[1]
    #define C_MID uPal[2]
    #define C_LT1 uPal[3]
    #define C_LT2 uPal[4]
    #define C_LT3 uPal[5]
    #define C_WHT uPal[6]

    float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
    float noise(vec2 p){
      vec2 i = floor(p), f = fract(p);
      f = f*f*(3.0-2.0*f);
      return mix(mix(hash(i), hash(i+vec2(1,0)), f.x),
                 mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
    }
    // ★18차. 채도 밀기(mode 4 전용). 휘도는 그대로 두고 색만 밖으로 민다.
    //   왜 필요한가 — ACES 는 **밝을수록 채도를 먹는다**(tools/aces_screen.py 역산).
    //   봉인칼 팔레트의 시안 자리(#7FD4F5)는 화면에서 채도 0.11 로 앉아 그냥 흰 실선이
    //   된다(실측). 2.10 으로 밀면 봉인칼 감청 자리가 #2AB2CB(채도 0.79)까지 서고,
    //   **색상(hue)은 안 건드리므로** 불칼은 주황 그대로다(#EE9B22).
    vec3 fsat(vec3 c, float k){
      float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
      return max(vec3(0.0), vec3(l) + (c - vec3(l)) * k);
    }

    // ───────────────────────────────────────────────────────────
    // 원작이 물을 그리는 방식 (water-breathing.mp4 실측 + 프레임 육안):
    //  1. 모든 물 형태에 **짙은 남색 잉크 외곽선**, 바로 안쪽에 밝은 갓선.
    //     이게 빠지면 이펙트가 배경에 녹아 '반투명 CG 띠'가 된다.
    //  2. 리본은 길이 방향으로 **비틀리며**(뫼비우스) 폭이 죄었다 풀린다.
    //  3. 내부는 가닥 4~6 개. 가닥마다 관 음영 + 자기 윤곽선.
    //  4. 포말은 흰 덩어리에 남색 윤곽 + 배경이 비치는 구멍.
    //  5. 24fps 로 다시 그린다 (매끈한 60fps 흐름이 곧 CG 티다).
    // ───────────────────────────────────────────────────────────

    float strand(float u, float v, float sd, float fk, float spread, float thick,
                 out float tone, out float vc)
    {
      float h1 = hash(vec2(fk * 3.1 + sd, 1.0));
      float h2 = hash(vec2(fk * 5.7 + sd, 2.0));
      float h3 = hash(vec2(fk * 7.3 + sd, 3.0));
      float u0 = h1 * 0.40;
      float u1 = u0 + 0.40 + h2 * 0.62;
      float s = (u - u0) / max(u1 - u0, 1e-3);
      tone = 0.0; vc = 0.0;
      if (s < 0.0 || s > 1.0) return 0.0;
      float taper = pow(sin(3.14159265 * s), 0.40);       // 붓자국: 양끝이 뾰족
      vc = (fk + 0.5) * spread + (noise(vec2(u * 3.4 + fk * 9.0 + sd, 5.0)) - 0.5) * 0.17;
      float hw = thick * (0.62 + 0.55 * h3) * taper;
      float d = abs(v - vc) / max(hw, 1e-4);
      if (d > 1.0) return 0.0;
      tone = 1.0 - d * d;                                  // 관 음영
      return 1.0;
    }

    void main(){
      if (uMode > 0.5 && uMode < 1.5 && uRibbonV2 > 0.5) {
        if (!(vA > 0.004)) discard;
      } else {
        if (vA <= 0.004) discard;
      }
      float u = vUV.x, v = vUV.y;
      // ★vSeed 는 이제 **가닥 번호**다. 0 = 본 획 / 1 = 겹 획 / 2 = 마루 심선.
      //   (v96 의 kind 0/1/2 = 몸통/포말/가는 심 은 가닥이 하나뿐이던 시절의 이름이고
      //    그 셋은 지금 본 획의 **밴드**로 들어와 있다.)
      float kind = floor(vSeed + 0.5);
      float sd = vSeed * 2.7 + 1.0 + floor(uT * 24.0) * 0.31;

      // ═══════════════════════════════════════════════════════════════════
      // ★★V 이아이도 일섬 (uMode 4. 18차)
      //
      // 여기 아래 네 벌(A~D)이 공유하는 것을 이 분기는 **하나도 안 쓴다** —
      // 먹 외곽선(ow/rw)도, 편측 밴드 계단(bt)도, 손그림 텍스처(uTex)도 없다.
      // 그리는 것은 딱 둘이다:
      //   kind 0  코어 — 가운데가 흰 심(선형 1.7~2.0. 블룸 문턱 1.02 를 넘긴다)이고
      //                  바깥으로 시안 두 단. **화소 하한**을 걸어 얇은 마디에서도
      //                  심이 안 사라지게 한다(먹선을 화소로 잡던 것과 같은 원리).
      //   kind 1  글로우 — 딥블루 한 겹. 부드럽게 빠지되(pow) 밝기가 낮아 면적이
      //                  넓어도 무게가 안 실린다. 코어를 감싸는 후광 노릇만 한다.
      // ★가산이라 **알파가 곧 세기**다. 계단(vA)이 1/24 로 끊기므로 섬광도 계단으로
      //   꺼진다(60fps 로 매끈하게 빠지면 그 순간 CG 발광체가 된다).
      // ★스타일(칼) 분기를 안 탄다 — 봉인칼(style 1)·불(style 2)도 같은 문법으로
      //   그리되 색은 제 팔레트에서 온다. 그래서 칼 일곱 자루의 정체가 그대로 산다.
      // ═══════════════════════════════════════════════════════════════════
      if (uMode > 3.5) {
        float dE = 1.0 - abs(v - 0.5) * 2.0;        // 0 = 가장자리, 1 = 한가운데
        float halfPx = max(1.0, vHalf * uPxPerM);
        // 길이 방향 감쇠. **계단 다섯 단**(u 는 살아 있는 창 기준 0..1)
        float ls = min(1.0, floor(u * 5.0) / 4.0);
        if (kind > 0.5) {
          // ── 글로우 한 겹 ──
          // ★코어에 **붙어서** 빠져야 후광이 된다. 지수를 올릴수록 코어 옆에 몰린다
          //   (1.45 로 두면 넓고 평평하게 깔려서 '파란 판'이 하나 더 생긴다).
          float g = pow(max(0.0, dE), 2.10);
          if (!(g > 0.03)) discard;
          // ★평칠이라 **어두운 파랑**이어야 한다(가산일 때는 밝을수록 좋았다).
          //   바깥이 짙어야 밝은 초원에서 획의 테가 서고, 어두운 던전에서는 코어의
          //   후광으로 읽힌다. 안쪽(코어 쪽)으로 갈수록 시안으로 올라간다.
          vec3 cg = mix(fsat(C_DK1, 2.10) * 0.55, fsat(C_MID, 2.10) * 0.95, g);
          gl_FragColor = vec4(cg, vA * (0.10 + 0.62 * g) * (1.0 - 0.55 * ls));
          return;
        }
        // ── 코어 ──
        // ★낙뢰(X 내려찍기)는 **가장자리를 계단으로 갉아** 지그재그를 만든다.
        //   매끈한 사인으로 흔들면 뱀이 되고, 계단으로 끊으면 번개가 된다.
        float cut = 0.0;
        if (uBolt > 0.5) {
          float seg = floor(u * 9.0);
          cut = 0.30 * hash(vec2(seg + sd * 0.7, 3.0)) * step(0.5, v)
              + 0.22 * hash(vec2(seg + sd * 1.9, 7.0)) * step(v, 0.5);
        }
        float dN = (dE - cut) / max(1.0 - cut, 1e-3);
        if (!(dN > 0.02)) discard;
        // 흰 심의 폭. **화소 하한**을 건다 - 가는 마디에서 심이 통째로 사라지면
        // 남는 것이 옅은 시안 실오라기뿐이라 "안 보인다"가 된다(10차의 병).
        // ★★1차 실측에서 2.4/halfPx·하한 0.34 로 뒀더니 코어가 반폭의 82% 를 먹어
        //   획이 통째로 **흰 실선**이 됐다(시안이 화면에 한 화소도 안 남았다).
        //   지금은 흰 심을 ±1.8화소로 조이고 그 바깥을 시안 두 단으로 채운다.
        float cw = clamp(1.8 / halfPx, 0.24, 0.62);
        // ★색을 **한 단씩 아래에서** 뽑는다(LT3->LT1, LT1->MID). 팔레트 위 칸(LT3)은
        //   어느 칼이든 거의 흰색이라(봉인칼 #D8F4FF · 물 #3BCCF9) 흰 심 옆에 두면
        //   두 단이 한 색으로 뭉친다. 시안은 LT1(#7FD4F5 / #239DCC) 자리에 있다.
        vec3 c;
        if (dN > 1.0 - cw) c = C_WHT * (1.85 * uSharp);
        else if (dN > 0.28) c = fsat(C_LT1, 2.10) * 1.25;
        else c = fsat(C_MID, 2.10) * 0.95;
        // 꼬리는 밝기가 계단으로 빠지고 시안 -> 감청으로 내려앉는다(바늘 끝).
        c = mix(c, fsat(C_DK1, 2.10) * 0.90, 0.55 * ls);
        c *= 1.0 - 0.42 * ls;
        // 가장자리 한 겹만 부드럽게 닫는다(1픽셀. 자로 자른 획은 판때기로 읽힌다)
        float ea = smoothstep(0.0, 0.05, dN);
        gl_FragColor = vec4(c, vA * ea);
        return;
      }

      if (uStyle > 0.5 && uStyle < 1.5) {
        if (uMode > 0.5 && uMode < 1.5 && uRibbonV2 > 0.5) {
          // 16차 리본 R3 봉인칼. 원소색 대신 uPal에서 뽑은 무채 먹 계단으로 칠한다.
          // 본 획은 전폭, 안쪽 겹 획은 어둡게 쓰고 바깥 마루는 포말 자리를 위해 버린다.
          float pDE = 1.0 - abs(v - 0.5) * 2.0;
          float pCut = (kind < 0.5 ? 0.10 : 0.06) * noise(vec2(u * 9.0 + sd, 4.0));
          float pDN = (pDE - pCut) / max(1.0 - pCut, 1e-3);
          float pEA = smoothstep(0.0, 0.004, pDN);
          if (!(pEA > 0.02)) discard;
          float pHalfPx = max(1.5, vHalf * uPxPerM);
          float pOw = clamp(3.0 / pHalfPx, 0.10, 0.30);

          float pInkY = dot(C_DK2, vec3(0.299, 0.587, 0.114)) * 0.70;
          float pDarkY = dot(C_DK1, vec3(0.299, 0.587, 0.114)) * 0.38;
          float pMidY = dot(C_MID, vec3(0.299, 0.587, 0.114)) * 0.48;
          float pLightY = dot(C_LT1, vec3(0.299, 0.587, 0.114)) * 0.62;
          vec3 P_K = vec3(pInkY);
          vec3 P_D = vec3(pDarkY);
          vec3 P_M = vec3(pMidY);
          vec3 P_L = vec3(pLightY);
          vec3 P_H = C_WHT * 0.70;
          vec3 pc = v < 0.18 ? P_K : (v < 0.42 ? P_D : (v < 0.66 ? P_M
            : (v < 0.84 ? P_L : (v < 0.92 ? P_H : P_K))));

          // 한 화소 안팎의 내부 먹선으로 평칠 단을 분리한다. 겹 획은 한 단 더 눌러
          // 원소 리본이 아니라 봉인된 칼의 잔흔으로 남긴다.
          float pSeamW = clamp(0.24 / pHalfPx, 0.008, 0.035);
          float pSeamD = min(min(abs(v - 0.18), abs(v - 0.42)),
                             min(abs(v - 0.66), abs(v - 0.84)));
          if (kind < 1.5 && pSeamD < pSeamW) pc = P_K;
          if (kind > 0.5 && kind < 1.5) pc = mix(pc, P_K, 0.35);
          // 포말이 서는 tipR 바깥 0.08m를 비운다. kind 2의 기하 정박 계약은
          // 유지하되 봉인칼 V2에서만 래스터를 버린다(B 리본은 아래 분기에서 그대로 사용).
          if (kind > 1.5) discard;
          if (pDN < pOw) pc = P_K;
          gl_FragColor = vec4(pc, vA * pEA);
          return;
        }

        // --- 평범한 검기: 원소 없이 얇고 깔끔한 흰빛 호 ---
        // ★v92. 여기도 끝을 흐리지 않고 **선으로 끊는다**. 바깥 한 겹은 먹(uPal[0]).
        // ★v94. 1번 녹슨 칼(plain)이 style=1 이다. 심사: "1번 칼은 이펙트가 사실상
        //   안 보인다." 원인 두 가지를 여기서 같이 고친다.
        //     ① 바깥 한 겹이 uPal[0] 인데 그게 먹이 아니라 중간 명도 청회색이었다
        //        -> 팔레트 0번을 진짜 먹으로 바꿨다(ELEMENTS.plain 참조)
        //     ② 먹 띠가 폭의 20% 뿐이라 경계가 배경에 녹았다 -> 32% 로 넓힌다
        // ★v97. 봉인칼은 **본 획 한 가닥만** 그린다(동반선 둘은 여기서 버린다).
        //   원소 칼과 같은 겹을 주면 "1번 칼이 제일 화려하다"가 된다.
        if (kind > 0.5) discard;
        float hw = 0.5 * (0.30 + 0.70 * (1.0 - u));
        float q = abs(v - 0.5) / hw;
        float ea = 1.0 - smoothstep(0.992, 1.0, q);
        if (!(ea > 0.02)) discard;
        vec3 cc = q < 0.26 ? uPal[6] : (q < 0.50 ? uPal[5] : (q < 0.68 ? uPal[3] : uPal[0]));
        gl_FragColor = vec4(cc, vA * (1.0 - 0.35 * u) * ea);
        return;
      }

      // ═══════════════════════════════════════════════════════════════════
      // v97 (10-FX-B) — 10차의 뼈대 위에 9차의 그림체
      //
      // 지키는 것(10차에서 얻은 모양): 획의 **폭은 지오메트리가 정한다**
      //   (updateTrail 의 taper. 양끝이 뾰족한 렌즈꼴). 여기서는 획을 가로지르는
      //   **밴드만** 칠한다. 닫힌 다각형 덩어리는 여기서 만들지 않는다.
      // 되살리는 것(9차에서 오너가 좋아한 그림체): 한 획 안의 **다층 평칠 밴드**.
      //   짙은 감청 먹선 -> 밝은 갓선 -> 감청 -> 시안 -> 흰 심. 경계는 흐리지 않고
      //   딱 끊는다(원작 프레임 실측. 그래서 색 계단은 정점이 아니라 여기서 만든다).
      // ★10차가 "간소해졌다"는 인상의 정체는 밴드 수가 아니라 **획이 6~13px 였다**는
      //   것이다. 다섯 단을 칠해도 한 단이 1px 면 눈에는 흰 실 한 오라기다.
      //   그래서 이번 판은 폭을 되돌리고(중간점) 그 안을 일곱 단으로 칠한다.
      // ★★셰이더 문자열 안에는 **역따옴표를 절대 쓰지 마라**(LOG 함정 정본. 셋째 재발
      //   까지 갔다). node --check 는 통과하고 **브라우저 모듈 파서만** SyntaxError 를 낸다.
      // ★먹 밴드를 '반폭의 44%'로 잡던 옛 식(v95)은 단면의 88% 가 먹이라 형태를
      //   정의하는 선이 아니라 **어두운 판때기**였다(휘도 -30~-93 의 진범). 반대로
      //   '바깥 20%' 고정(v96)은 굵은 획에서 20px 판때기가 되고 가는 획에서 0px 가 된다.
      //   지금은 **화소로** 잡는다(uPxPerM x vHalf). 굵든 가늘든 먹은 늘 2~3화소다.
      // ═══════════════════════════════════════════════════════════════════
      bool fire = uStyle > 1.5;
      {
        // ── 획을 가로지르는 자리 ──
        // dE : 가장자리까지의 거리(0 = 가장자리, 1 = 한가운데). 붓 갉음·먹선·알파 컷이 쓴다.
        // bt : **편측** 좌표(0 = 칼 쪽 안쪽 가장자리, 1 = 바깥 가장자리). 색 계단이 쓴다.
        // ★★v98(11차). 색 계단을 dE(대칭)에서 bt(편측)로 옮긴 것이 이번 그림체의 핵심이다.
        //   원작 밴드를 수직으로 잘라 색 런을 압축해 읽으면 계단이 **한 방향**이다
        //   (renders/history/v97_wave11/fx_research.md 3. 1080폭 프레임 실측):
        //     칼 쪽 먹 #0a2647 4% -> 짙은 감청 2% -> 감청 2% -> 시안 #2ba1d0 32%
        //     -> 밝은 시안 #34b4db 30% -> 전이 6% -> **바깥 가장자리에 흰 심 #dff1fc 21%**
        //   대칭으로 칠하면 흰 심이 한가운데를 관통하고 먹이 양쪽에 대칭으로 깔린다 =
        //   "빛나는 관"이지 "먹으로 그린 물"이 아니다. 오너가 좋아한 9차 그림체의
        //   정체도 이 편측 계단이었다(수차 컷 실측. ref_frames/ref_band_wheel.png).
        float dE = 1.0 - abs(v - 0.5) * 2.0;
        float bt = v;
        // 가장자리를 붓처럼 갉는다. 자로 그은 띠가 아니라 붓이 지나간 자리여야 한다.
        // ★씨앗 sd 에 floor(uT*24) 가 들어 있어 **1/24 마다 다시 갉인다**(작화 계단).
        float cut = (kind < 0.5 ? 0.17 : 0.10) * noise(vec2(u * 9.0 + sd, 4.0));
        // ★갈퀴(kind 2)는 **바깥 가장자리만** 굵게 갉아 손가락 3~7개로 가른다.
        //   호쿠사이 파도의 claw 다 - 마루가 말려 갈퀴가 되고 끝에서 물방울이 떨어진다.
        //   말림은 꼬리가 아니라 **진행 방향 마루(머리)**에 있다(fx_research.md 5).
        // ★12-FX-D. A(mode 0)는 **머리 말림을 강화한다**(오너 주문). 갈래를 굵고(0.55)
        //   잦게(u*6.5) 갉아 손가락이 5~9개로 갈라지게 한다. 나머지 벌은 현행 값.
        float clawAmp = (uMode < 0.5) ? 0.62 : 0.38;
        float clawFrq = (uMode < 0.5) ? 6.5 : 5.0;
        if (kind > 1.5) cut += clawAmp * noise(vec2(u * clawFrq + sd * 3.0, 7.0)) * step(0.5, v);
        float dN = (dE - cut) / max(1.0 - cut, 1e-3);
        // ★끝을 넓게 흐리면 다시 '반투명 CG 띠'다. 1픽셀 폭만 남긴다
        //   (계단은 씬 타겟 MSAA 가 받는다. v94 에서 0.006 으로 정한 그 폭이다).
        float ea = smoothstep(0.0, 0.004, dN);
        if (!(ea > 0.02)) discard;
        // ── 먹 외곽선 폭을 화소로 잡는다 ──
        // 이 마디의 반폭이 화면에서 몇 화소인가. 밴드 좌표(dN)는 0..1 이므로
        // "먹 2.4화소"는 dN 으로 2.4/halfPx 다. 상·하한은 그림이 무너지지 않는 범위.
        float halfPx = max(1.5, vHalf * uPxPerM);
        float ow = clamp(3.6 / halfPx, 0.10, 0.30);    // 먹 한 겹(화면에서 늘 3~4화소)
        float rw = ow + clamp(1.8 / halfPx, 0.050, 0.13);  // 그 바로 안쪽 밝은 갓선

        // ═══════════════════════════════════════════════════════════════
        // B 귀멸 리본 (uMode 1)
        // 애니의 "물이 흐르는 띠". 두툼한 리본 하나가 궤적을 따라 지나가고
        // 그 안에서 손그림 질감이 **길이 방향으로 흐른다**(UV 스크롤).
        // ★스크롤은 1/24 로 끊는다. 60fps 로 미끄러지면 그 한 가지 때문에
        //   판 전체가 CG 로 읽힌다(v92 가 궤적만 60fps 로 두고 겪은 일).
        // ★질감은 색을 정하지 않고 **밴드 자리를 밀고 당긴다**. 색까지 맡기면
        //   팔레트 계단이 텍스처 밝기에 통째로 묻힌다(v94 함정). 흐르는 인상은
        //   경계가 움직이는 데서 나오지 밝기가 흔들리는 데서 나오지 않는다.
        // ═══════════════════════════════════════════════════════════════
        if (uMode > 0.5 && uMode < 1.5) {
          float sc = floor(uT * 24.0) / 24.0;
          vec2 tuv = vec2(u * 1.30 - sc * 0.62 + vSeed * 0.17, clamp(bt, 0.02, 0.98));
          float tlum = 0.5, talp = 1.0;
          if (uUseTex > 0.5) {
            vec4 tx = texture2D(uTex, tuv);
            tlum = dot(tx.rgb, vec3(0.30, 0.59, 0.11));
            talp = tx.a;
          } else {
            tlum = noise(vec2(u * 7.0 - sc * 3.4 + sd, bt * 3.0));
          }
          if (uRibbonV2 < 0.5) {
            // 롤백 경로: 16차 2라운드 직전 B 채색을 그대로 보존한다.
            if (uUseTex > 0.5 && talp < 0.30 && bt < 0.58) discard;
            float bs = clamp(bt + (tlum - 0.5) * 0.55, 0.0, 1.0);
            vec3 c;
            if (kind > 1.5) {
              c = bs < 0.50 ? C_LT3 : C_WHT;
            } else {
              c = bs < 0.42 ? C_DK1 : bs < 0.64 ? C_MID : bs < 0.78 ? C_LT1
                : bs < 0.90 ? C_LT2 : C_LT3;
              float ws = min(0.90, 1.0 - clamp(3.4 / halfPx, 0.06, 0.18));
              if (bs > ws) c = C_WHT;
              c *= 0.74 + 0.44 * tlum;
              float fo = noise(vec2(u * 13.0 + sd * 3.0, bt * 4.0 + sd));
              if (bt > 0.62) {
                if (fo > 0.62) c = C_WHT;
                else if (fo > 0.54) c = C_DK2 * 0.55;
              }
            }
            if (dN < ow) c = C_DK2 * 0.42;
            else if (dN < rw) c = C_LT3;
            if (uStyle > 1.5) {
              float hl = noise(vec2(u * 26.0 + sd * 5.0, v * 14.0));
              if (hl < 0.06 + 0.30 * u) discard;
            }
            float ls = min(1.0, floor(u * 4.0) / 3.0);
            c = mix(c, C_DK1, 0.30 * ls);
            gl_FragColor = vec4(c, vA * ea);
            return;
          }

          // 16차 리본 V2. feel.js 포말이 바깥 흰 밴드를 맡으므로 본체는 낮은
          // 명도 사다리와 먹 이음선으로 받친다. 텍스처는 경계만 흔들고 밝기는 못 올린다.
          if (uUseTex > 0.5 && talp < 0.30 && kind < 1.5 && bt < 0.58) discard;
          float bw = clamp(bt + (tlum - 0.5) * 0.14, 0.0, 1.0);
          vec3 B_K = C_DK2 * 0.24;
          vec3 B_N = C_DK1 * 0.30;
          vec3 B_M = C_MID * 0.42;
          vec3 B_C = C_LT1 * 0.82;
          float outerOw = ow * 0.72;
          vec3 c;
          if (kind > 1.5) {
            // 바깥 마루 안내선은 흰색을 쓰지 않는다. 포말 아래의 어두운 받침이다.
            c = bw < 0.55 ? B_N : B_C;
          } else if (kind > 0.5) {
            // 안쪽 겹 리본은 장식용 두 번째 시안판이 아니라 독립 먹 경계다.
            c = (bw < 0.20 || bw > 0.82) ? B_K : B_N;
          } else {
            // 안쪽이 가려져도 K/N이 남도록 바깥 절반에도 먹과 감청을 한 번 더 놓는다.
            c = bw < 0.12 ? B_K : bw < 0.30 ? B_N : bw < 0.44 ? B_M
              : bw < 0.61 ? B_C : bw < 0.69 ? B_K : bw < 0.84 ? B_C : B_N;

            // 흰 심은 머리 세 구간에서 폭 12% -> 8% -> 4% -> 0 으로 사라진다.
            float ub = floor(clamp(u, 0.0, 0.999) * 8.0);
            float whiteW = ub < 1.0 ? 0.12 : (ub < 2.0 ? 0.08 : (ub < 3.0 ? 0.04 : 0.0));

            // 약 1px 내부 먹선. 이미 먹인 경계에는 중복선을 긋지 않는다.
            float seamW = clamp(0.26 / halfPx, 0.008, 0.040);
            float seamD = min(abs(bw - 0.30), min(abs(bw - 0.44), abs(bw - 0.84)));
            if (seamD < seamW) c = B_K;

            // 흰 심을 외곽선 바로 안쪽의 dN 구간으로 옮긴다. 폭이 얇아져도 외곽 먹이
            // 먼저 차지한 자리와 겹치지 않아 12% -> 8% -> 4%가 실제로 남는다.
            if (whiteW > 0.0 && bt > 0.5 && dN >= outerOw
                && dN < outerOw + 2.0 * whiteW) c = C_WHT;
          }

          // 안쪽은 3.6px, 포말 쪽은 2.6px 먹으로 닫는다. 밝은 갓선은 포말과 겹치므로 없다.
          if (bt < 0.5 && dN < ow) c = B_K;
          else if (bt >= 0.5 && dN < outerOw) c = B_K;
          if (uStyle > 1.5) {
            float hl = noise(vec2(u * 26.0 + sd * 5.0, v * 14.0));
            if (hl < 0.06 + 0.30 * u) discard;
          }
          gl_FragColor = vec4(c, vA * ea);
          return;
        }

        // ═══════════════════════════════════════════════════════════════
        // C v95 정박판 (uMode 2)
        // 색을 **구운 손그림에 통째로 맡긴다**(ct = tx.rgb). v95 의 풍성함은
        // 밴드를 코드로 잘 나눠서가 아니라 그 텍스처에 이미 평칠로 그려져 있어서다
        // (연하늘-시안-진파랑-남색-흰 포말 + 갓선 + 찢긴 가장자리).
        // 여기서 밝기를 다시 뭉개면 그 띠 구조가 한 색으로 합쳐진다(v92 실측).
        // ★v95 원본과 다른 유일한 점은 **자리**다 - 이 가닥들은 전부 칼끝 궤적에서
        //   자란다. v95 는 여기에 더해 화면좌표 붓자국을 얹었고 그것이 '허공 판때기'였다.
        // ═══════════════════════════════════════════════════════════════
        if (uMode > 1.5 && uMode < 2.5) {
          float aq = floor(u * 4.0) / 4.0;        // 꼬리로 갈수록 한 단씩 가라앉는다
          vec3 c;
          if (uUseTex > 0.5) {
            vec2 tuv = vec2(u * 1.35 + floor(uT * 24.0) * 0.041 + vSeed * 0.13,
                            clamp(bt, 0.02, 0.98));
            vec4 tx = texture2D(uTex, tuv);
            if (tx.a < 0.45) discard;             // 알파는 유/무만 가른다(v95 문법)
            c = pow(tx.rgb * (1.0 - 0.30 * aq), vec3(1.18));
          } else {
            // 텍스처 없는 칼(얼음·독·흙·어둑)은 v95 의 절차 계단을 그대로 쓴다
            c = bt < 0.12 ? C_LT3 : bt < 0.30 ? C_LT2 : bt < 0.50 ? C_LT1
              : bt < 0.70 ? C_MID : bt < 0.88 ? C_DK1 : C_DK2;
            c *= (1.0 - 0.30 * aq);
          }
          // ── 굵은 먹 밴드(v95 문법: 머리 굵고 꼬리 얇게) ──
          // ★원본은 반폭의 44% 였는데 그러면 단면의 88% 가 먹이라 '어두운 판때기'가
          //   된다(v96 실측 휘도 -30~-93). 여기서는 상한 0.32 와 화소 하한으로 조인다.
          float ow2 = clamp(mix(0.30, 0.14, u), min(0.26, 3.4 / halfPx), 0.32);
          if (dN < ow2) c = C_DK2 * 0.45;
          gl_FragColor = vec4(c, vA * ea);
          return;
        }

        // ═══════════════════════════════════════════════════════════════
        // D 샤프 잔광 (uMode 3)
        // 밝은 코어 한 획 + 짧은 잔광. 밴드도 붓결도 포말도 없다(대조군).
        // ★네 벌 중 여기만 알파가 길이 방향으로 빠진다. 그게 '잔광'의 정의다.
        //   그래도 1/24 계단은 지킨다(vA 가 계단이고 여기서는 배수만 곱한다).
        // ═══════════════════════════════════════════════════════════════
        if (uMode > 2.5) {
          float coreW = clamp(3.2 / halfPx, 0.14, 0.55);
          vec3 c = dN > 1.0 - coreW ? C_WHT : (dN > 0.34 ? C_LT3 : C_LT1);
          float ow3 = clamp(1.6 / halfPx, 0.04, 0.14);
          if (dN < ow3) c = C_DK1;                // 형태선 한 겹만(먹 아님)
          float fade = 1.0 - 0.55 * min(1.0, u * 1.2);
          gl_FragColor = vec4(c, vA * ea * (0.40 + 0.60 * fade));
          return;
        }

        vec3 c;
        if (kind < 1.5) {
          // ── 본 획·겹 획: 일곱 단 평칠 ──
          // 먹 -> 갓선 -> 짙은 감청 -> 감청 -> 밝은 시안 -> 더 밝은 시안 -> 흰 심.
          // ★흰 심이 한가운데를 **관통**해야 획이 배경보다 밝다(10차가 얻은 것. 유지).
          //   동시에 바깥 한 겹이 반드시 먹이라 '먹으로 그린 만화'로 읽힌다(9차의 그림체).
          // cs = 흰 심이 시작하는 자리. 머리는 넓고(0.82) 꼬리로 갈수록 좁아진다(0.90).
          // ★1차 시도에서 cs 0.70 으로 뒀더니 획이 통째로 **흰 판**으로 읽혔다(실측 크롭).
          //   물 팔레트는 2~5번이 다 밝은 하늘색이라, 흰 심이 넓으면 남는 것이 없다.
          //   감청(C_DK1)·중간(C_MID)을 넓히고 심을 좁혀야 '파란 물'로 읽힌다.
          // ★★겹 획(kind 1)도 같은 일곱 단으로 칠한다. 2차 시도에서 이것만 두 단
          //   (밝은 몸통 + 밝은 심)으로 뒀더니 획 바깥 절반이 **연한 물웅덩이**가 되어
          //   전체가 지면에 깔린 옅은 판으로 읽혔다(실측 크롭 c_hoeng·kill).
          //   붓이 둘이면 밴드도 둘이어야 '겹쳐 그은 두 획'이 된다.
          // ★v98. 편측 계단 다섯 단. ws = **흰 심이 시작하는 자리(바깥에서)**.
          //   머리에서 0.78(= 바깥 22%. 실측 21%)이고 꼬리로 가면 1.10 이 되어
          //   **흰 심이 아예 없어진다.** 실측이 그렇다 - 머리는 흰색(휘도 0.96),
          //   꼬리는 감청(0.64)이다. 별똥별의 밝은 머리가 여기서 나온다.
          // ★밴드의 **명도 배분은 v97 그대로** 두고 자리만 편측으로 편다.
          //   오너가 좋아한 그림체가 그 배분이다("그림체는 딱 좋았어"). 1차 시도에서
          //   원작 단면의 화소 비율(짙은 감청 8% · 시안 62%)을 그대로 옮겼다가
          //   획이 통째로 **연회색 판**이 됐다(실측 크롭 z2). 원작의 '시안'은 채도 0.79 인
          //   #2ba1d0 인데 게임 물 팔레트의 같은 자리(#4884A2 · #549CBA)는 채도 0.55 라
          //   같은 비율로 깔면 색이 아니라 회색으로 읽힌다. **비율이 아니라 무게를 옮긴다.**
          // ★2차 시도에서 v97 배분(짙은 감청 46%)을 그대로 옮겼더니 **획 휘도-배경이
          //   -5** 로 뒤집혔다(실측). 이유는 배분이 아니라 **길이**다 - 수명이 두 배가
          //   되면서 획 면적의 대부분이 꼬리가 되는데, 꼬리를 감청으로 내려앉히는 몫까지
          //   겹쳐 평균이 배경 아래로 내려갔다. 이 게임 배경은 밝은 모래·풀밭이라
          //   어두운 획은 곧 **바닥에 묻은 얼룩**이다(원작은 밤이라 반대다).
          //   그래서 안쪽 감청을 46% -> 30% 로 줄이고 꼬리에도 얇은 흰 심을 남긴다.
          // ★3차 조정. 물 획의 **채도**를 실측으로 맞춘다. 오너가 그림체를 칭찬한 v95 의
          //   획은 채도 중앙 0.31~0.48 이고 원작 수차 밴드는 0.56 이다. v97 0.20~0.24 ·
          //   v98 0.21~0.27 로 한참 아래였다(같은 자로 잰 실측).
          // ★★v99. **이 밴드 비율은 손대지 않았다.** 채도를 올린 손잡이는 여기가 아니라
          //   ELEMENTS.water 팔레트다(그 주석에 ACES 역산표가 있다). 여기 비율을 만지면
          //   전임이 두 번 밟은 함정으로 곧장 간다 — 짙은 단을 넓히면 획이 배경보다
          //   어두워져 **바닥 얼룩**이 되고, 원작 단면 비율(시안 62%)을 그대로 옮기면
          //   **연회색 판**이 된다. 채도는 비율이 아니라 색의 무게로 옮기는 것이 맞다.
          // ★★12-FX-D (A 정제). 오너 주문 "흰 심 관통 또렷". 옛 값(0.82 -> 0.96)은
          //   꼬리에서 심이 **아예 없어졌다**(0.96 이면 남는 폭이 4%. 화면 10px 획에서
          //   0.4화소라 안티에일리어싱에 통째로 먹힌다). 두 가지를 같이 고친다:
          //     ① 머리를 넓히고(0.82 -> 0.76) 꼬리 상한을 0.90 으로 낮춘다
          //     ② **화소 하한**을 건다 - 어떤 마디에서도 흰 심이 3화소 아래로 안 간다.
          //   먹선을 화소로 잡은 것과 같은 원리다(비율로 잡으면 가는 마디에서 0 이 된다).
          float ws = min(mix(0.80, 0.92, min(1.0, u * 1.3)),
                         1.0 - clamp(3.0 / halfPx, 0.06, 0.20));
          c = bt < 0.38 ? C_DK1
            : bt < 0.62 ? C_MID
            : bt < 0.74 ? C_LT1
            : bt < ws   ? C_LT3
            : C_WHT;
          // 겹 획은 본 획보다 한 단 짙게(같은 밝기로 겹치면 경계가 안 보인다)
          if (kind > 0.5) c *= 0.88;
        } else {
          // ── 갈퀴(마루 심선) ──
          // 얇으니 두 단만. 여기에 다섯 단을 칠하면 한 단이 1px 라 죽이 된다.
          // ★9차의 동반 획은 화면 좌표라 몸 옆 허공에 떴다. 이 가닥들은 같은 칼끝
          //   궤적에서 자라므로 늘 획 옆에 붙는다 - 그게 이번 판의 유일한 차이다.
          // ★12-FX-D (A 정제). 1차 시도에서 흰 끝을 0.42 로 넓혔다가 갈퀴가 통째로
          //   흰 띠가 됐다(실측 크롭). 흰색은 **손가락 끝**에만 둔다 - 물방울이
          //   떨어지는 자리다. 갈래 자체는 clawAmp 가 낸다.
          c = bt < 0.68 ? C_LT3 : C_WHT;
        }
        // ── 가장자리 두 겹은 늘 먹·갓선(화소 고정) ──
        // ★색 계단보다 **뒤에** 덮어쓴다. 형태를 정의하는 선이라 어떤 밴드보다 우선한다.
        //   촬영감독 테라오 유이치(공식 인터뷰): "이펙트를 위에 얹어 화려하게 하면서도
        //   **선을 남기는 것**." 먹선은 장식이 아니라 발광에 안 먹히도록 지키는 대상이다.
        if (dN < ow) c = C_DK2 * 0.42;
        else if (dN < rw) c = C_LT3;
        if (uUseTex > 0.5 && kind < 1.5) {
          // 구운 손그림에서는 **알파(찢긴 가장자리·구멍)와 붓결만** 빌린다.
          // ★색까지 텍스처에 맡기면 위 밴드가 통째로 텍스처 밝기에 묻힌다(v94 의 함정:
          //   "색 계단이 한 칸에 들어온다"). 텍스처는 밝기 변조로만 쓴다.
          // ★찢긴 구멍은 **흰 심 바깥에서만** 뚫는다. 심까지 뚫으면 획이 토막나고
          //   그 순간 배경보다 밝은 관통선이 끊긴다(10차가 지킨 것을 깨지 않는다).
          vec2 tuv = vec2(u * 1.05 + floor(uT * 24.0) * 0.037 + vSeed * 0.13,
                          clamp(v, 0.02, 0.98));
          vec4 tx = texture2D(uTex, tuv);
          // ★v98. 구멍 조건을 dN(대칭) -> bt(편측)로. 흰 심이 이제 **바깥 가장자리**에
          //   있으므로, 옛 조건은 그 심을 그대로 뚫어서 머리의 흰 코어가 토막났다.
          if (tx.a < 0.32 && bt < 0.66) discard;       // 찢긴 구멍(파란 몸통에만)
          float tl = dot(tx.rgb, vec3(0.30, 0.59, 0.11));
          c *= 0.80 + 0.42 * tl;                       // 붓결(질감). 대비를 한 단 올렸다
        } else if (fire) {
          // 불은 속이 뚫린다. 꼬리로 갈수록 성기게.
          float hl = noise(vec2(u * 26.0 + sd * 5.0, v * 14.0));
          if (hl < 0.06 + 0.30 * u) discard;
        }
        // 꼬리는 한 단씩 가라앉고 **감청으로 내려앉는다**. ★계단으로. 매끈하게 흐리면
        // 그라데이션이 된다.
        // ★v98. 3단 -16% -> 5단. 실측: 머리 휘도 0.96 · 꼬리 0.64 이고 색도 파랑으로 간다.
        //   밝기만 낮추면 회색 꼬리가 되므로 감청(C_DK1)으로 섞은 뒤에 한 번 더 낮춘다.
        // ★몫은 실측 비(머리 휘도 0.96 : 꼬리 0.64 = 0.67배)에 맞춘다. 2차 시도의
        //   0.55 + 0.18 은 0.45배까지 떨어뜨려 획 전체가 배경보다 어두워졌다.
        float ls = min(1.0, floor(u * 5.0) / 4.0);
        c = mix(c, C_DK1, 0.40 * ls);
        c *= 1.0 - 0.10 * ls;
        gl_FragColor = vec4(c, vA * ea);
      }
    }`
});
const trailMesh = new THREE.Mesh(trailGeo, trailMat);
trailMesh.frustumCulled = false;
trailMesh.renderOrder = 3;
scene.add(trailMesh);
LOCAL_RIG.mat = trailMat;           // ★rig 는 위에서 만들었고 재질은 여기서 붙인다
LOCAL_RIG.mesh = trailMesh;
// ★검증 창구(?dev 없이도 연다. 읽기 전용). 궤적 정점에 NaN 이 한 톨 들어가면
//   블룸이 그 점을 **사각형으로** 번지게 한다(v88 '검은 번쩍'의 기전). 안정성 표본이
//   이 값을 센다 - 있으면 그 인덱스, 없으면 -1.
window.__trailNaN = () => {
  const pa = LOCAL_RIG.pos;        // ★22차. 옛 전역 posArr = 로컬 rig 의 position 배열
  for (let i = 0; i < pa.length; i++) if (!Number.isFinite(pa[i])) return i;
  return -1;
};

// ---------- 칼을 휘감는 리본 (리듬체조 리본) ----------
// 궤적(trail)은 "지나간 자취"라서 칼이 멈춰 있으면 아무것도 안 보인다.
// 이 리본은 **기를 모으는 표시**다. 칼을 세워 모으는 동안 칼날을 축으로 감겨 있다가,
// 베는 순간 확 퍼지며 사라진다(그 힘이 파도로 나가는 것이므로 꼬리로 남기지 않는다).
//   coil = 1 -> 칼을 감고 있다(느릴 때)   coil = 0 -> 터져서 사라짐(빠를 때)
// coil 을 칼끝 속도로 자동 계산하므로 3연타/일격기 둘 다 그냥 동작한다.
// 한 가닥이면 그냥 감은 끈처럼 보인다. 두 가닥을 서로 어긋나게(위상 반대 +
// 감는 횟수도 다르게) 두면 서로 교차하며 얽혀서 물줄기 둘이 휘감는 그림이 된다.
const WRAP_N = 140;                 // 가닥당 마디
const WRAP_STRANDS = 2;
//              위상차,           감는 횟수, 반지름 배율, 폭 배율, 색조(0=밝게 1=짙게)
// ★v96. 폭 배율을 한 단 내렸다(1.00/0.82 -> 0.66/0.54). 반지름은 위 spec_R0 에서
//   줄였고, 폭까지 그대로 두면 가는 반지름에 굵은 띠가 감겨 '흰 덩어리'가 된다.
const WRAP_CFG = [
  { phase: 0.0,        turns: 3.4, rad: 1.00, w: 0.66, tone: 0.0 },
  { phase: Math.PI,    turns: 2.7, rad: 0.82, w: 0.54, tone: 1.0 },
];
const wrapGeo = new THREE.BufferGeometry();
const wPos = new Float32Array(WRAP_STRANDS * WRAP_N * 2 * 3);
const wUV = new Float32Array(WRAP_STRANDS * WRAP_N * 2 * 2);
const wTone = new Float32Array(WRAP_STRANDS * WRAP_N * 2);
const wIdx = [];
for (let sIdx = 0; sIdx < WRAP_STRANDS; sIdx++) {
  const off = sIdx * WRAP_N * 2;
  for (let i = 0; i < WRAP_N - 1; i++) {
    const a = off + i * 2;
    wIdx.push(a, a + 2, a + 3, a, a + 3, a + 1);
  }
}
wrapGeo.setAttribute('position', new THREE.BufferAttribute(wPos, 3));
wrapGeo.setAttribute('aUV', new THREE.BufferAttribute(wUV, 2));
wrapGeo.setAttribute('aTone', new THREE.BufferAttribute(wTone, 1));
wrapGeo.setIndex(wIdx);

const wrapMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, side: THREE.DoubleSide,
  blending: THREE.NormalBlending,
  uniforms: { uFade: { value: 0 }, uPal: { value: null }, uStyle: { value: 0 } },
  vertexShader: `
    attribute vec2 aUV;
    attribute float aTone;
    varying vec2 vUV; varying float vTone;
    void main(){ vUV = aUV; vTone = aTone;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `
    varying vec2 vUV; varying float vTone;
    uniform float uFade;
    uniform float uStyle;
    uniform vec3 uPal[7];
    #define C_DK2 uPal[0]
    #define C_DEEP uPal[1]
    #define C_MID uPal[2]
    #define C_CY1 uPal[4]
    #define C_WHT uPal[6]
    float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
    float noise(vec2 p){
      vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
      return mix(mix(hash(i), hash(i+vec2(1,0)), f.x),
                 mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
    }
    void main(){
      if (uFade <= 0.01) discard;
      float u = vUV.x, v = vUV.y;
      // 끝으로 갈수록 가늘어지며 뜯긴다(리본 끝의 나풀거림)
      // 좌우 대칭으로 자르면 그냥 '끈'이다. 파도는 한쪽(마루)만 부풀고 뜯긴다.
      float sd = vTone * 5.3 + 1.0;
      float len = mix(1.0, 0.42, u);                    // 끝으로 갈수록 가늘어짐
      // 안쪽(칼에 붙는 쪽): 완만하게 물결친다
      float inner = 0.5 - len * (0.30 + 0.10 * sin(u * 21.0 + sd * 3.0));
      // 바깥쪽(마루): 굵게 부풀었다 잦아들고, 가장자리가 뭉게뭉게 뜯긴다
      float swell = 0.34 + 0.46 * (0.5 + 0.5 * sin(u * 9.0 + sd * 2.0))
                  + 0.26 * noise(vec2(u * 15.0 + sd, 2.0));
      float outer = 0.5 + len * swell;
      float lump  = noise(vec2(u * 34.0 + sd * 7.0, 5.0)) * 0.6
                  + noise(vec2(u * 74.0 + sd * 3.0, 9.0)) * 0.4;
      outer -= len * 0.30 * (1.0 - lump);               // 마루 끝이 들쭉날쭉
      if (v < inner || v > outer) discard;

      float t = (v - inner) / max(1e-4, outer - inner);
      vec3 c;
      if (uStyle > 1.5) {
        // 불꽃 감김: 물처럼 **마루 끝에 흰 포말**을 두면 안 된다. 불은 정반대로
        // 칼에 붙는 안쪽이 가장 뜨겁고(흰-노랑) 바깥 끝이 식어 검붉게 스러진다.
        float k = vTone < 0.5 ? t : clamp(t * 1.12 - 0.06, 0.0, 1.0);
        if      (k < 0.14) c = uPal[6];
        else if (k < 0.30) c = uPal[5];
        else if (k < 0.48) c = uPal[4];
        else if (k < 0.66) c = uPal[3];
        else if (k < 0.84) c = uPal[2];
        else               c = uPal[1];
        // 불은 속이 뚫린다. 바깥으로 갈수록 성기게
        float hl = noise(vec2(u * 40.0 + sd * 9.0, v * 22.0));
        if (hl < 0.08 + 0.36 * k) discard;
        gl_FragColor = vec4(c, uFade * (1.0 - 0.30 * u));
        return;
      }
      if (vTone < 0.5) {          // 밝은 가닥
        if      (t < 0.14) c = C_MID;
        else if (t < 0.34) c = C_DEEP;
        else if (t < 0.52) c = C_CY1;
        else if (t < 0.62) c = C_WHT;
        else if (t < 0.80) c = C_CY1;
        else               c = C_WHT;   // 마루 = 흰 포말
      } else {                    // 짙은 가닥. 색이 달라야 두 가닥으로 읽힌다
        if      (t < 0.20) c = C_DEEP;
        else if (t < 0.48) c = C_MID;
        else if (t < 0.58) c = C_WHT;
        else if (t < 0.84) c = C_CY1;
        else               c = C_WHT;
      }
      // 마루 안쪽에 포말 얼룩
      if (t > 0.78) {
        float f = noise(vec2(u * 44.0 + sd * 11.0, v * 30.0));
        if (f < 0.34) c = C_CY1;
      }
      // ── 먹 외곽선 (v94) ──
      // ★감는 리본만 외곽선이 없었다. 궤적·참격·포말은 다 먹으로 형태를 정의하는데
      //   여기만 색 띠로 끝나서, 칼을 감는 동안 화면에 **반투명 파란 천**이 붙어 있었다
      //   (심사 "등간격 평행 띠 = 천으로 읽힌다"의 진원지). 양쪽 끝 한 겹을 먹으로 끊는다.
      if (t < 0.09 || t > 0.91) c = C_DK2 * 0.5;
      gl_FragColor = vec4(c, uFade * (1.0 - 0.30 * u));
    }`
});
const wrapMesh = new THREE.Mesh(wrapGeo, wrapMat);
wrapMesh.frustumCulled = false;
wrapMesh.renderOrder = 4;
scene.add(wrapMesh);

// ---------- 흩날리는 흰 물거품 조각 ----------
// 레퍼런스에서 흰 조각들이 호에서 멀리까지 날아간다. 띠 가장자리에 붙어 있는
// 포말만으로는 그 느낌이 안 나서 별도 파티클로 뽑는다.
// 빛나는 점이 아니라 **찢어진 종이 조각**이라 알파는 계단, 색은 납작한 흰색.
const SPRAY_MAX = 260;
const spray = [];                 // {p, v, t, ttl, size, seed, spin, rot}
const sprayGeo = new THREE.BufferGeometry();
const spPos = new Float32Array(SPRAY_MAX * 4 * 3);
const spUV = new Float32Array(SPRAY_MAX * 4 * 2);
const spA = new Float32Array(SPRAY_MAX * 4);
const spSeed = new Float32Array(SPRAY_MAX * 4);
// 먹물 튐. 같은 조각 시스템을 쓰되 이 값이 1 이면 **어두운 붉은 먹물 + 흰 심**으로
// 칠한다. 처치 순간에만 켠다(칼 궤적의 감청 팔레트를 오염시키지 않으려면 색을
// 파티클 단위로 갈라야 한다. 팔레트를 통째로 바꾸면 리본까지 붉어진다).
const spInk = new Float32Array(SPRAY_MAX * 4);
const spIdx = [];
for (let i = 0; i < SPRAY_MAX; i++) {
  const o = i * 4;
  spIdx.push(o, o + 1, o + 2, o, o + 2, o + 3);
  spUV[(o) * 2] = 0; spUV[(o) * 2 + 1] = 0;
  spUV[(o + 1) * 2] = 1; spUV[(o + 1) * 2 + 1] = 0;
  spUV[(o + 2) * 2] = 1; spUV[(o + 2) * 2 + 1] = 1;
  spUV[(o + 3) * 2] = 0; spUV[(o + 3) * 2 + 1] = 1;
}
sprayGeo.setAttribute('position', new THREE.BufferAttribute(spPos, 3));
sprayGeo.setAttribute('aUV', new THREE.BufferAttribute(spUV, 2));
sprayGeo.setAttribute('aAlpha', new THREE.BufferAttribute(spA, 1));
sprayGeo.setAttribute('aSeed', new THREE.BufferAttribute(spSeed, 1));
sprayGeo.setAttribute('aInk', new THREE.BufferAttribute(spInk, 1));
sprayGeo.setIndex(spIdx);

const sprayMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, side: THREE.DoubleSide,
  blending: THREE.NormalBlending,
  uniforms: { uPal: { value: null }, uRise: { value: 0 },
              // ★v97. 몸통을 한 단 올리고(5c1220 -> 7e1622) 심의 순백을 뺐다
              //   (f4e8ea -> dc8a92). 위 프래그먼트 '눈알' 주석 참조.
              // ★★v99(11-FX-B). 7e1622 -> BE5460. **한 단 더 올린 게 아니라 자를 바꿨다.**
              //   #7e1622 는 hex 로 보면 진홍인데 ACES 톤매핑을 지나면 화면에서
              //   #5C000B (휘도 **20**) 다 - 눈에는 그냥 검은 조각이다. 붉은색은 ACES 가
              //   특히 세게 누른다(휘도의 79% 를 G·B 가 지는데 진홍엔 그 둘이 없다).
              //   화면에서 역산해 #A83A48(휘도 82 · 채도 0.66)에 앉게 잡았다.
              //   처치 문법은 그대로 진홍이다 - 진홍을 **진홍으로 보이게** 한 것뿐이고,
              //   같은 이유로 enemy.js 가 쓰는 tex/ink_drop.png 도 같은 자리에 맞췄다.
              uInkDark: { value: new THREE.Color(0xBE5460) },
              uInkCore: { value: new THREE.Color(0xdc8a92) } },
  vertexShader: `
    attribute vec2 aUV; attribute float aAlpha; attribute float aSeed; attribute float aInk;
    varying vec2 vUV; varying float vA; varying float vSeed; varying float vInk;
    void main(){ vUV = aUV; vA = aAlpha; vSeed = aSeed; vInk = aInk;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `
    varying vec2 vUV; varying float vA; varying float vSeed; varying float vInk;
    uniform vec3 uPal[7];
    uniform float uRise;
    uniform vec3 uInkDark;
    uniform vec3 uInkCore;
    float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
    float noise(vec2 p){
      vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
      return mix(mix(hash(i), hash(i+vec2(1,0)), f.x),
                 mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
    }
    void main(){
      if (vA <= 0.02) discard;
      // ── v96. 초승달(속 빈 고리) -> **꼬리 달린 쉼표·물방울** ──
      // 오너 지시 7항. 옛 식은 원 두 개의 차집합이라 **속이 뚫린 타원 고리**였고,
      // 화면에서 6~14px 밖에 안 되는 조각이 그 모양이면 눈에는 '검은 눈알'로 보였다
      // (실측 시트에서 처치 순간 지면에 눈알이 수십 개 깔린다).
      // 지금은 둥근 머리 + 가늘어지며 휘는 꼬리 한 덩어리다. 속이 차 있고,
      // 형태를 정의하는 것은 바깥 한 겹의 먹뿐이다.
      // ★+x 가 진행 방향이다(JS 가 화면 속도로 눕힌다). 머리가 앞, 꼬리가 뒤.
      vec2 q = vUV - vec2(0.32, 0.5);
      float wob = (noise(vUV * 5.0 + vSeed * 7.0) - 0.5) * 0.05;
      float head = length(vec2(q.x, q.y * 1.18)) / (0.22 + wob);
      // 꼬리: 뒤로 갈수록 가늘어지고 살짝 휜다
      float s = clamp(q.x / 0.60, 0.0, 1.0);
      float hw = 0.22 * (1.0 - s) * (1.0 - s) + 0.006;
      float tail = abs(q.y + 0.13 * s * s) / hw;
      float d = q.x > 0.0 ? min(head, tail) : head;
      if (d > 1.0) discard;
      // ★v97. 0.74 -> 0.84. 물보라를 9차의 6할로 되돌리자 조각이 다시 커졌는데,
      //   먹이 반지름의 26% 면 **넓이의 45%** 라 12px 조각이 통째로 '검은 눈알'이 된다
      //   (v96 이 '속 빈 고리'를 쉼표로 고치며 닫은 지적이 크기만으로 되살아났다).
      //   0.84 면 먹은 넓이의 29% - 형태를 정의하는 테두리로 남고 덩어리는 물이 된다.
      bool edge = d > 0.84;                              // 바깥 한 겹만 먹
      vec3 c;
      if (vInk > 0.5) {
        // 먹물: 어두운 붉은 덩어리에 밝은 심. 물보라와 같은 실루엣이라 튀지 않는다.
        // ★v97. 심을 0.42 -> 0.26 으로 좁히고 **순백을 뺐다**(uInkCore 를 연분홍으로).
        //   어두운 테두리 + 한가운데 흰 점 = 화면에서 10~14px 이면 눈알이다.
        //   실측 크롭에서 처치 순간 지면에 검은 눈알이 스무 개씩 깔렸다(9차의 그 지적이
        //   물보라만 고쳐졌고 먹물에는 남아 있었다). 지금은 붉은 핏방울로 읽힌다.
        c = edge ? uInkDark * 0.62 : (d < 0.26 ? uInkCore : uInkDark);
        gl_FragColor = vec4(c, vA > 0.35 ? 1.0 : 0.7);
        return;
      }
      if (uRise > 0.5) {
        // 불티: 심이 있는 불덩이. 윤곽은 검붉게, 식으면 재.
        c = edge ? uPal[0]
          : d < 0.34 ? uPal[6] : d < 0.52 ? uPal[5] : uPal[4];
        c = mix(c, uPal[0], (1.0 - vA) * 0.75);
      } else {
        // ★속은 흰 심이 주인이어야 한다(밝기 계약). 먹은 바깥 한 겹뿐.
        c = edge ? uPal[0] * 0.7 : (d < 0.46 ? uPal[6] : uPal[5]);
      }
      gl_FragColor = vec4(c, vA > 0.4 ? 1.0 : 0.62);
    }`
});
const sprayMesh = new THREE.Mesh(sprayGeo, sprayMat);
sprayMesh.frustumCulled = false;
sprayMesh.renderOrder = 5;
scene.add(sprayMesh);

// ---------- 참격(타격 지점) ----------
// ★v92. 여기 있던 **가산합성 초승달 + 별빛 텍스처**(arcMat/spawnArc/updateArcs,
//   약 150줄)를 통째로 지웠다. 명중 지점의 한 획은 이제 feel.js 가 플립북 시트
//   (tex/slash_flip.png)를 월드에 눕혀 1/24 로 재생한다 - feel.impactSlash().
//   화면에 남는 역할("여기서 갈라졌다")은 그대로고, 문법만 60fps 가산합성에서
//   24fps 작화 프레임으로 갈렸다. 부르는 쪽(main.js)은 좌표·각도·크기·종류만 넘긴다.
// ★왜 여기서 안 그리나: 시트를 읽는 쪽이 feel.js 하나여야 밝기 계약(먹 0.12 /
//   0.45 / 0.70 / 심 0.95)과 팔레트 분기(처치 진홍 / 물 감청)가 한 군데서만 산다.

// ---------- 타격 물보라 ----------
// 처음엔 충격파 '링'을 그렸는데, 카메라 빌보드 원판은 크기·각도 어느 조합에서도
// '납작한 파스텔 블롭'으로 보였다(실측 3회). 원작의 임팩트는 링이 아니라
// **물보라 파편이 왕창 터지는 것**이고, 그건 초승달 물방울 시스템이 이미 한다.
// 그래서 타격 순간에 물방울을 크게·많이 터뜨리는 것으로 정리했다.
const _tipDir = new THREE.Vector3();
const _advAxis = new THREE.Vector3(0, 1, 0);
// ★v96. 34개 x 배수 2.8 -> 13개 x 1.5. 오너 지시 "칼 근처에서만".
//   실측(v95): 터지는 프레임에 조각이 화면 여기저기 흩어져 획보다 넓은 자리를 먹었다.
//   물보라는 "칼이 지나간 자리에 물이 튄다"는 표시지 화면을 채우는 장치가 아니다.
// ★v97. 13개 x 1.5 -> 21개 x 1.75 (9차의 6할). 오너: "너무 줄였다."
//   모양(속이 찬 쉼표꼴)은 v96 이 고친 그대로 둔다 - 9차의 '속 빈 고리'로는 안 돌아간다.
//   조각이 작아지면 고리는 검은 눈알로 보이고, 쉼표는 그냥 작은 물방울로 보인다.
function spawnBurst(a, b, delta) {
  _tipDir.copy(delta);
  if (_tipDir.lengthSq() < 1e-6) _tipDir.set(0, 1, 0);
  _tipDir.normalize();
  spawnSpray(a, b, _tipDir, 21, 1.75);
}
function updateBursts(dt) {}

const _sq = new THREE.Vector3(), _camR = new THREE.Vector3(), _camU = new THREE.Vector3();
const _c1 = new THREE.Vector3(), _c2 = new THREE.Vector3();
let sprayAcc = 0;
function spawnSpray(aPt, bPt, moveDir, count, scale, ink) {
  // ── 몸 비우기 (v98) ──
  // ★가독 계약("머리·상체 상시 판독")을 깨고 있던 것은 **궤적이 아니라 물보라**였다.
  //   실측: 머리 덮임 최악 70.2% 인데 그중 궤적 몫은 **0.0%** - 전부 물보라 조각이었다
  //   (계측은 궤적 메시만 껐다 켠 마스크와 전체 마스크를 따로 재서 갈랐다).
  //   궤적은 BODY_R 로 이미 가슴을 피하는데 물보라에는 그 자가 없었다.
  //   가슴 반지름 안에서 태어나면 밖으로 밀고, 속도에도 바깥 성분을 준다
  //   (물이 몸에서 터져 나가는 그림이라 연출로도 이쪽이 맞다).
  const cx = root.position.x, cz = root.position.z;
  const cy = root.position.y + charH * 0.42;
  const SPRAY_CLEAR = 0.95;
  // ★12-FX-D. 물보라 양도 벌의 일부다(D 는 미니멀이라 0.40, C 는 v95 라 1.15).
  //   먹물 튐(ink)은 **처치 문법**이라 네 벌 공통 무수정이다 - 배수를 안 건다.
  if (!ink) count = Math.max(1, Math.round(count * FX.sprayK));
  for (let i = 0; i < count && spray.length < SPRAY_MAX; i++) {
    const f = 0.35 + Math.random() * 0.85;                 // 칼날 바깥쪽에서 주로
    const p = aPt.clone().lerp(bPt, f);
    let ox = p.x - cx, oz = p.z - cz;
    let orr = Math.hypot(ox, oz);
    if (orr < 1e-4) { ox = 1; oz = 0; orr = 1; }
    if (orr < SPRAY_CLEAR && p.y > cy) {
      const push = (SPRAY_CLEAR - orr) / orr;
      p.x += ox * push; p.z += oz * push;
      orr = SPRAY_CLEAR;
    }
    // 진행 방향으로 튀고 + 바깥으로 흩어진다
    const v = moveDir.clone().multiplyScalar(0.35 + Math.random() * 1.1);
    v.x += (Math.random() - 0.5) * 3.2 + (ox / orr) * 1.2;
    v.y += Math.random() * 2.6 - 0.5;
    v.z += (Math.random() - 0.5) * 3.2 + (oz / orr) * 1.2;
    spray.push({
      p, v, t: 0,
      ttl: 0.30 + Math.random() * 0.55,
      size: charH * (0.012 + Math.random() * Math.random() * 0.055) * scale,
      seed: Math.random() * 10,
      rot: Math.random() * 6.28, spin: (Math.random() - 0.5) * 9,
      ink: ink ? 1 : 0,
    });
  }
}

// 먹물 튐. 처치한 자리에서 사방으로. 칼날 선분이 아니라 **맞은 지점**이 원점이다.
const _ia = new THREE.Vector3(), _ib = new THREE.Vector3(), _idir = new THREE.Vector3();
function spawnInk(x, y, z, dx, dy, dz, count, scale) {
  _idir.set(dx, dy, dz);
  if (_idir.lengthSq() < 1e-6) _idir.set(0, 1, 0);
  _idir.normalize();
  _ia.set(x, y, z).addScaledVector(_idir, -0.22);
  _ib.set(x, y, z).addScaledVector(_idir, 0.22);
  spawnSpray(_ia, _ib, _idir, count, scale, true);
}
// ── 24fps 양자화 (v94. 격차 6) ──
// v92 에서 참격·임팩트·속도선·궤적 리본은 다 1/24 로 끊었는데 **물보라와 감는 리본만
// 60fps 로 매끈하게** 흐르고 있었다(v92 스스로 신고한 잔여). 같은 화면에서 어떤 것은
// 끊어 그리고 어떤 것은 미끄러지면 눈은 미끄러지는 쪽을 CG 로 읽는다.
// 방법은 리본과 같다: **같은 1/24 칸 안에서는 아예 다시 안 그린다.** 그동안 쌓인 dt 를
// 칸이 바뀌는 프레임에 한꺼번에 먹인다(= 물리는 맞고 그림만 계단이 된다).
// ★게임시계(gameT)를 쓰므로 히트스톱 중에는 칸이 안 바뀌고 한 장을 붙들고 있는다.
// ★force = DEV 굽기 창구 전용(클립을 손으로 미는 경로는 gameT 가 안 흘러 갇힌다).
let sprayQ = -1, sprayDtAcc = 0;
function updateSpray(dt, force) {
  sprayDtAcc += dt;
  const fq = Math.floor(gameT * FX_FPS);
  if (!force && fq === sprayQ) return;
  sprayQ = fq;
  dt = sprayDtAcc; sprayDtAcc = 0;
  _camR.setFromMatrixColumn(camera.matrixWorld, 0);
  _camU.setFromMatrixColumn(camera.matrixWorld, 1);
  for (let i = spray.length - 1; i >= 0; i--) {
    const s2 = spray[i];
    s2.t += dt;
    if (s2.t >= s2.ttl) { spray.splice(i, 1); continue; }
    s2.v.multiplyScalar(Math.pow(curEl.rise ? 0.05 : 0.12, dt));   // 공기저항으로 금방 멈춘다
    // 물방울은 떨어지고 불티는 떠오른다. 이걸 안 뒤집으면 팔레트만 주황인
    // '주황색 물방울'이 된다.
    s2.v.y += curEl.rise ? 2.4 * dt : -5.5 * dt;
    s2.p.addScaledVector(s2.v, dt);
    s2.rot += s2.spin * dt;
  }
  for (let i = 0; i < SPRAY_MAX; i++) {
    const o = i * 4;
    if (i >= spray.length) {
      for (let k = 0; k < 4; k++) { spA[o + k] = 0; spInk[o + k] = 0; }
      continue;
    }
    const s2 = spray[i];
    // ★알파도 1/24 계단으로 끊는다. 위치만 계단이고 알파가 미끄러지면 조각이
    //   '스르르 녹는' 그림이 되어 다시 파티클 CG 로 읽힌다.
    const life = Math.ceil((1 - s2.t / s2.ttl) * 6) / 6;
    // ★속도를 화면에 투영해 그 방향으로 눕히고, 빠를수록 길게(물방울 꼬리).
    // 카메라 정면 정사각형으로 돌리기만 하면 '색종이'로 보인다.
    const vx = s2.v.dot(_camR), vyv = s2.v.dot(_camU);
    const sp2 = Math.hypot(vx, vyv);
    const angv = sp2 > 0.4 ? Math.atan2(vyv, vx) : s2.rot;
    const cs = Math.cos(angv), sn = Math.sin(angv);
    const stretch = 1.0 + Math.min(1.5, sp2 * 0.14);
    _c1.copy(_camR).multiplyScalar(cs).addScaledVector(_camU, sn).multiplyScalar(s2.size * stretch);
    _c2.copy(_camR).multiplyScalar(-sn).addScaledVector(_camU, cs).multiplyScalar(s2.size * 0.74);
    const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
    for (let k = 0; k < 4; k++) {
      _sq.copy(s2.p).addScaledVector(_c1, corners[k][0]).addScaledVector(_c2, corners[k][1]);
      spPos[(o + k) * 3] = _sq.x; spPos[(o + k) * 3 + 1] = _sq.y; spPos[(o + k) * 3 + 2] = _sq.z;
      spA[o + k] = life;
      spSeed[o + k] = s2.seed;
      spInk[o + k] = s2.ink || 0;
    }
  }
  sprayGeo.attributes.position.needsUpdate = true;
  sprayGeo.attributes.aAlpha.needsUpdate = true;
  sprayGeo.attributes.aSeed.needsUpdate = true;
  sprayGeo.attributes.aInk.needsUpdate = true;
}

setElement('water');            // 셰이더가 uniform 없이 컴파일되면 검게 나온다
// ★v96. 0.155 -> 0.098. 오너 지시 "칼 근처에서만" + 캐릭터 가독.
//   실측(수면참 모으는 구간, 1280x720): 이 감김 리본이 **주인공 머리 상자의 46%** 를
//   덮고 있었다(흰 덩어리 하나로 뭉쳐 보인다). 감는 리본은 "기를 모은다"는 표시라
//   칼에 붙어 있기만 하면 되고, 몸까지 감쌀 이유가 없다.
const spec_R0 = (L, c) => L * 0.098 * (1 + (1 - c) * 0.9);
let coil = 1.0, wrapPhase = 0, lastTip = null, tipSpeed = 0;
let swordFast = 0;   // 0=칼이 느리다(감김) 1=베는 중(풀림)
let released = false; // 이번 공격에서 이미 터졌는가. 터진 뒤 다시 감기면
                      // '기를 모은다'는 뜻이 흐려진다.
// 칼끝이 이만큼 빨라야 '벤다'로 친다. 실측(Heavy 클립): 들어올릴 때 ~12,
// 실제 타격 순간 ~98. 둘이 확실히 갈리도록 45 로 둔다.
// 낮게 잡으면 들어올리는 동안 리본이 풀려버려 "감았다 푸는" 그림이 안 나온다.
const FAST_REF = 45.0;
const _n1 = new THREE.Vector3(), _n2 = new THREE.Vector3(), _sp = new THREE.Vector3();
const _tan = new THREE.Vector3(), _wd = new THREE.Vector3(), _prev = new THREE.Vector3();
const _spd = new THREE.Vector3(), _cam = new THREE.Vector3();
// ★v94. 물보라와 같은 1/24 게이트(위 updateSpray 주석 참조).
let wrapQ = -1, wrapDtAcc = 0;
function updateWrap(dt, aPt, bPt, active, force) {
  wrapDtAcc += dt;
  const fq = Math.floor(gameT * FX_FPS);
  if (!force && fq === wrapQ) return;
  wrapQ = fq;
  dt = wrapDtAcc; wrapDtAcc = 0;
  // 감겨 있을 때만 보인다. 베는 순간 coil 이 떨어지면서 그대로 사라진다.
  // ★12-FX-D. 감는 리본 세기도 벌에서 온다(D 는 0.50 = 미니멀).
  const want = (active && !released && curEl.wrap) ? Math.max(0, coil * 1.25 - 0.25) * FX.wrapK : 0;
  wrapMat.uniforms.uFade.value += (want - wrapMat.uniforms.uFade.value) * Math.min(1, dt * 14);
  // ★알파도 계단이다. 여섯 단이면 24fps 한 장마다 눈에 보이게 한 칸씩 떨어진다.
  wrapMat.uniforms.uFade.value = Math.round(wrapMat.uniforms.uFade.value * 6) / 6;
  if (wrapMat.uniforms.uFade.value < 0.02) return;
  _d.copy(bPt).sub(aPt);
  const L = _d.length() || 1;
  _d.multiplyScalar(1 / L);
  // 칼끝 속도로 감김/풀림을 정한다. 모을 땐 감기고 벨 땐 풀린다.
  const coilT = 1 - swordFast;
  coil += (coilT - coil) * Math.min(1, dt * (coilT < coil ? 22 : 2.6));
  wrapPhase += dt * 5.5;

  const NP = bladePath.length;
  // 휜 칼을 따라가려면 매 마디마다 접선/법선을 다시 잡아야 한다.
  // 직선 축 하나로 감으면 칼이 휜 만큼 리본이 날에서 떠버린다.
  const _bp = new THREE.Vector3(), _bp2 = new THREE.Vector3(), _tg = new THREE.Vector3();
  const R0 = spec_R0(L, coil);
  _cam.copy(camera.position);
  for (let sIdx = 0; sIdx < WRAP_STRANDS; sIdx++) {
    const cf = WRAP_CFG[sIdx];
    const base = sIdx * WRAP_N * 2;
    for (let j = 0; j < WRAP_N; j++) {
      const t = j / (WRAP_N - 1);
      // 중심선 위의 점과 그 지점의 접선
      if (NP >= 2) {
        const f = Math.min(NP - 1.001, t * 1.26 * (NP - 1));
        const i0 = Math.floor(f), fr = f - i0;
        _bp.copy(bladePath[i0]).lerp(bladePath[Math.min(NP - 1, i0 + 1)], fr);
        _bp2.copy(bladePath[Math.min(NP - 1, i0 + 1)]).sub(bladePath[i0]);
        _bp.applyMatrix4(handBone.matrixWorld);
        _tg.copy(_bp2).transformDirection(handBone.matrixWorld).normalize();
      } else {
        _bp.copy(aPt).addScaledVector(_d, L * (0.02 + 1.26 * t));
        _tg.copy(_d);
      }
      _n1.set(0, 1, 0).cross(_tg);
      if (_n1.lengthSq() < 1e-6) _n1.set(1, 0, 0).cross(_tg);
      _n1.normalize();
      _n2.copy(_tg).cross(_n1).normalize();
      const th = t * cf.turns * Math.PI * 2 + wrapPhase + cf.phase;
      const pulse = 1 + 0.34 * Math.sin(t * 8.0 + wrapPhase * 1.7 + cf.phase * 1.5)
                      + 0.16 * Math.sin(t * 19.0 - wrapPhase * 1.1);
      const rad = R0 * cf.rad * Math.sin(Math.PI * Math.min(1, t * 1.12)) * pulse;
      _sp.copy(_bp).addScaledVector(_n1, Math.cos(th) * rad)
                   .addScaledVector(_n2, Math.sin(th) * rad);
      if (j === 0) _tan.copy(_tg);
      else _tan.copy(_sp).sub(_prev).normalize();
      const swell = (0.62 + 0.55 * Math.sin(t * 6.5 + wrapPhase * 1.3 + cf.phase * 2.0))
                  * (0.55 + 0.45 * Math.sin(Math.PI * Math.min(1, t * 1.1)));
      _wd.copy(_tan).cross(_cam.clone().sub(_sp)).normalize();
      const sm = Math.max(0, Math.min(1, (t - 0.30) / 0.34));
      _wd.applyAxisAngle(_tan, Math.PI * (sm * sm * (3 - 2 * sm)) + cf.phase * 0.3);
      _wd.multiplyScalar(L * 0.135 * cf.w * Math.max(0.18, swell));
      const o = base + j * 2;
      wPos[o * 3] = _sp.x + _wd.x; wPos[o * 3 + 1] = _sp.y + _wd.y; wPos[o * 3 + 2] = _sp.z + _wd.z;
      wPos[(o + 1) * 3] = _sp.x - _wd.x; wPos[(o + 1) * 3 + 1] = _sp.y - _wd.y;
      wPos[(o + 1) * 3 + 2] = _sp.z - _wd.z;
      wUV[o * 2] = t; wUV[o * 2 + 1] = 1;
      wUV[(o + 1) * 2] = t; wUV[(o + 1) * 2 + 1] = 0;
      wTone[o] = cf.tone; wTone[o + 1] = cf.tone;
      _prev.copy(_sp);
    }
  }
  wrapGeo.attributes.position.needsUpdate = true;
  wrapGeo.attributes.aUV.needsUpdate = true;
  wrapGeo.attributes.aTone.needsUpdate = true;
}

const clampi = (v, a, b) => (v < a ? a : (v > b ? b : v));
// Catmull-Rom: 저장된 샘플 사이를 부드럽게 잇는다(각진 호 제거)
function cr(p0, p1, p2, p3, t, out) {
  const t2 = t * t, t3 = t2 * t;
  out.x = 0.5 * (2 * p1.x + (-p0.x + p2.x) * t + (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2
                 + (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3);
  out.y = 0.5 * (2 * p1.y + (-p0.y + p2.y) * t + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2
                 + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3);
  out.z = 0.5 * (2 * p1.z + (-p0.z + p2.z) * t + (2 * p0.z - 5 * p1.z + 4 * p2.z - p3.z) * t2
                 + (-p0.z + 3 * p1.z - 3 * p2.z + p3.z) * t3);
  return out;
}
let trailGain = 1.0;       // 일격기에서 1.0 -> 1.9 로 부푼다
let lastSwingFxT = -9;     // 마지막 화면공간 본 획을 그은 게임시각(v94)
// ── 본 획 색 = 지금 든 칼의 색 (v94) ──
// ★물·기본칼은 feel.js 의 귀멸 실측 팔레트(PAL_WATER)를 그대로 쓴다. 원소 램프에서
//   기계로 뽑은 값보다 그쪽이 정확하다(감청 -> 밝은 시안 -> 흰 심 단계가 손으로 맞춰져 있다).
// ★그 밖의 칼은 램프에서 네 단만 골라 쓴다. 먹은 제일 어두운 단을 한 번 더 눌러서
//   만든다 - 램프의 0번은 '짙은 색'이지 먹이 아니라서, 그대로 쓰면 경계가 배경에 녹는다
//   (1번 칼이 안 보이던 것과 똑같은 기전).
let swingPalEl = null;
const _hex3 = (v, k) => {
  const r = Math.round(Math.min(255, ((v >> 16) & 255) * k));
  const g = Math.round(Math.min(255, ((v >> 8) & 255) * k));
  const b = Math.round(Math.min(255, (v & 255) * k));
  return (r << 16) | (g << 8) | b;
};
function applySwingPalette() {
  if (!feel.setSwingPalette) return;
  if (curEl === swingPalEl) return;              // 칼이 안 바뀌었으면 건너뛴다
  swingPalEl = curEl;
  const p = curEl.p;
  const hx = h => parseInt(h, 16);
  // ★v99. 먹 튀김(f1) 방울의 원소색. 팔레트 1번(감청 자리)을 **선형 그대로** 넘긴다.
  //   feel.js 는 이 색으로 방울 다섯을 칠하고 순먹은 둘만 남긴다. 안 넘기면 불칼에서도
  //   파란 물방울이 튄다. (setHex 가 아니라 setRGB 인 이유는 feel.js 쪽 주석 참조.)
  if (feel.setPopTint) { const c = HEX(p[1]); feel.setPopTint(c[0], c[1], c[2]); }
  if (curEl.style === 1 || curEl === ELEMENTS.water) {
    feel.setSwingPalette({ ink: 0x081228, edge: 0x0c3c9c, mid: 0x24ccfc, core: 0xcce4fc,
                           thr: [0.30, 0.55, 0.82] });
    return;
  }
  feel.setSwingPalette({ ink: _hex3(hx(p[0]), 0.45), edge: hx(p[1]),
                         mid: hx(p[4]), core: hx(p[6]), thr: [0.30, 0.55, 0.82] });
}
const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _d = new THREE.Vector3();
const _pa = new THREE.Vector3(), _pb = new THREE.Vector3(), _perp = new THREE.Vector3();
// v94. 화면공간 리본 전용 임시값(물보라의 _camR/_camU 와 **따로** 둔다. 같은 프레임에
// 둘 다 도는데 하나를 나눠 쓰면 언젠가 한쪽이 다른 쪽 값을 밟는다).
const _tR = new THREE.Vector3(), _tU = new THREE.Vector3(), _c = new THREE.Vector3();
const _pc = new THREE.Vector3(), _tv = new THREE.Vector3();

// ── 크기 계약 (9차 확정 판정. renders/history/v94_wave9/handoff_combat.md) ──
// 정면 리치 3.2m · 정면 부채꼴 ±75°. 이 밖으로 **획을 뻗지 않는다.**
// 손맛 심사관의 "이펙트가 판정의 3~5배 과장" FAIL 이 여기서 닫힌다.
const REACH_R = 3.2;
const REACH_COS = Math.cos(75 * Math.PI / 180);
// 폭이 화면 수직으로 부풀 때 XZ 로 삐져나가는 몫만 조인다(높이는 자유 - 공중은
// 아무 거짓말도 안 한다. 오히려 "세로 스윕"이 화면 존재감의 주된 출처다).
const REACH_EDGE = 3.6;
function clampReach(p, px, pz) {
  const dx = p.x - px, dz = p.z - pz;
  const r = Math.hypot(dx, dz);
  if (r <= REACH_EDGE || r < 1e-5) return;
  const k = REACH_EDGE / r;
  p.x = px + dx * k; p.z = pz + dz * k;
}
// ── 지속 계약 (v94) ──
// 캐릭터 심사관 FAIL: "이펙트가 몸의 3~4배를 0.3~0.9초 덮어 타격 애니가 안 보인다."
// 예전에는 샘플 세기가 0.92^(프레임) 로 삭았다 = 0.13 에 닿기까지 24.5프레임(0.41초).
// 이제 **1/24 칸 나이**로 센다. 앞 넉 장이 본 획(4/24 = 0.167초)이고, 뒤 두 장은
// 폭을 3분의 1 이하로 좁힌 **가는 먹 자취**다. 여섯 칸(0.25초) 뒤에는 아무것도 없다.
// ★v96. 여섯 칸 -> **넉 칸**(4/24 = 0.167초). 오너 지시 "2~4프레임".
//   여섯 칸이면 앞 넉 장이 본 획이고 뒤 두 장이 가는 자취인데, 실측에서 그 두 장도
//   알파 0.78 로 또렷하게 남아 획이 0.25초를 버텼다(= 다음 스윙과 겹쳐 두 겹이 된다).
// ★v97. 넉 칸 -> **다섯 칸**(5/24 = 0.208초). 오너가 "너무 줄였다"고 했다.
//   9차의 0.25~0.39초 잔류(다음 스윙과 겹쳐 두 겹이 되던 그 값)로는 안 돌아간다.
//   다섯째 칸은 폭 0.26 의 **가는 먹 자취**라 면적이 아니라 '지나간 자리'만 남긴다.
// ★v98(11차). 다섯 칸 -> **열한 칸**(11/24 = 0.458초). 오너 직접 지시:
//   "칼 이펙트가 별똥별처럼 칼 지나간 자리 쏵... 긴 고리 달리듯이."
//   근거는 실측이다(renders/history/v97_wave11/fx_research.md 2.3). 원작 한 획을
//   1/24 로 끊어 추적하니 **13프레임(0.54초)** 살았고, 그 사이 길이는 16%만 줄고
//   L/Wmax 는 4.9 -> 4.7 로 거의 안 변했다 = **끝부터 갉는 게 아니라 통째로 얇아진다.**
//   그래서 세기(알파)는 늦게까지 붙들고 **폭 사다리만** 뒤로 갈수록 급히 내린다.
// ★그래도 '몸을 오래 덮는다'는 옛 FAIL 로 안 돌아가는 이유: 열한째 칸의 폭 배수가
//   0.16 이고 거기에 혜성 테이퍼(꼬리 0.08)가 곱해져 **면적이 아니라 선**만 남는다.
// ★12-FX-D. 계단표도 벌마다 다르다(A/B 열한 칸 0.458초 · C 여섯 칸 0.25초 ·
//   D 여섯 칸이되 폭이 급히 빠진다). 값은 전부 위 FX_TABLE 에 있다.
const TRAIL_LADDER   = FX.ladder;
const TRAIL_LADDER_W = FX.ladderW;
// ── 가닥 배치 (v96. 한 가닥) ──
// 가닥은 "칼날 위 어디에 중심선을 두고(at), 그 자리에서 화면 바깥으로 얼마나 밀려서(off),
// 얼마나 굵은가(half)"로 적는다. off·half 단위는 **미터**다.
// ★at 0.62~0.80 -> **0.90**. 심사관 둘이 같은 말을 했다: "이펙트가 검신이 아니라
//   몸 옆·앞 허공에 뜬 판때기." 중심선이 칼 중간(0.62)이면 획의 안쪽 절반이 손·팔에
//   걸치고 바깥 절반이 허공으로 나간다. 0.90 은 **칼끝 바로 앞**이라 획이 칼끝 궤적을
//   그대로 따라간다(measureBlade 가 실측한 bladeA 0.18 ~ bladeB 0.98 위의 자리다).
// ★off 1.16 -> 0.05. 옛 배치는 바깥 끝(off+half)이 1.36m 였고 gain 1.55 를 곱하면
//   칼에서 2.1m 밖까지 부풀었다 = 화면 세로의 41%. 그게 오너가 본 "화면 1/3".
//   지금은 획이 칼끝을 **가운데 두고** ±half 로만 자란다.
// ★half 0.36~0.42 -> 0.150. 획 전체 두께 = 2 x 0.150 x gain x taper(최대 1.36).
//   실측(1280x720 · 이펙트 메시를 껐다 켠 차이로 잰 마스크):
//     획 길이 77~152px · 굵기 7~24px · L/W 4.6~18.1 · 화면 점유 0.07~0.28%
//   ★L/W 는 **둘레/면적**으로 잰다. 주성분(PCA)으로 재면 굽은 호에서 x·y 퍼짐이
//     비슷해져 1.2 로 나온다(v96 에서 한 번 속았다). 얇은 띠는 둘레~2L·면적~L*W 이므로
//     L/W = 둘레^2/(4*면적) 이고 이 식은 곡률과 무관하다.
//   길이(살아 있는 넉 칸 동안 칼끝이 지나간 거리)는 2.2~3.2m 이므로 L/W 는 4~5 다
//   (오너 지시 2항: "L/W 4+ 의 띠 하나"). ★가늘면 길어도 화면을 안 덮는다.
//
// ── v97 (10-FX-B). 크기는 9차와 10차의 **중간점** ──
// 오너: "너무 줄였다... 모양이 좀 이상하고 큰 게 문제였지."
//   9차: 화면 점유 4.0~11.8% (다섯 가닥 + 화면좌표 붓자국 넉 장. 머리 80~94% 가림)
//   10차: 화면 점유 0.10~0.56% (한 가닥 · 폭 6~13px. "사실상 안 보인다")
// 목표는 그 사이 - 정점 프레임 3~7%. **크기 손잡이는 아래 TRAIL_HALF 한 숫자다.**
// 나머지 둘은 그 배수로 적어 두었으므로 이 숫자만 움직이면 세 가닥이 같이 간다.
// ★off 를 이렇게 벌린 이유: 세 가닥을 같은 자리에 겹치면 새 면적이 안 생긴다(9차에서
//   실측된 것과 같은 함정 - 획을 1.3배 키웠는데 점유는 15% 밖에 안 올랐다).
//   면적은 **간격**에서 나온다. 그래서 본 획 바깥으로 나란히 눕힌다.
// ★그래도 셋 다 발원은 칼끝 궤적(_c)이다. off 는 '화면에서 캐릭터 바깥쪽'이므로
//   가닥이 늘어도 몸 쪽으로는 안 자란다 = 머리 가독이 구조적으로 지켜진다.
//
// ── v98 (11차 FX). 오너 지시: "별똥별처럼, 그리고 긴 고리 달리듯이" ──
// 앞 판(v97)은 **길이 방향 단면이 대칭 렌즈**였다(sin 반주기). 그러면 제일 굵은 자리가
// 획 한가운데라 칼끝에는 가는 끝만 붙고, 화면에서는 "부채꼴 호 한 장"으로 읽힌다.
// 실측(fx_research.md 2.1)은 그 반대였다 — **앞에서 14% 지점이 최대 폭**이고 그 뒤로
// 단조 감소하는 꼬리다. 손잡이는 아래 COMET_* 넷이다.
// ★반폭 0.72 -> 0.74. 수명이 두 배가 되면 같은 폭으로도 면적이 그만큼 늘어난다.
//   존재감은 폭이 아니라 **길이**에서 가져온다(원작 넓은 장 실측: 점유 1.4~6.3% 인데
//   길이는 화면 대각선의 17~40%. 순수 리본 컷은 가닥 하나가 화면폭의 1.1% 뿐이다).
// ★★12-FX-D. 아래 다섯 줄이 곧 **네 벌의 기하**다. 값은 FX_TABLE 에 있고
//   여기서는 이름만 빌린다(옛 상수 이름을 그대로 둬야 아래 200줄 주석이 안 거짓말이 된다).
//   · TRAIL_HALF  A 0.888 · B 0.980 · C 0.820 · D 0.400
//   · 프로파일    A/B/D 혜성(COMET_*) · C 는 v95 의 (1 - 0.78 un^2)
//   · STRAND_CFG  A 3가닥 · B 2가닥 · C 5가닥 · D 1가닥. **전부 칼끝 궤적 발원**이다.
const TRAIL_HALF = FX.half;
// 혜성 프로파일 (un: 0 = 칼끝(머리) … 1 = 꼬리 끝)
const COMET = FX.comet || { head: 0.14, nose: 0.42, tailp: 1.30, tail: 0.08 };
const COMET_HEAD = COMET.head;    // 최대 폭이 앉는 자리. 실측 0.10~0.35 중 칼끝에 붙는 쪽
const COMET_NOSE = COMET.nose;    // 코끝 폭(머리 대비). 0 으로 하면 칼끝에서 획이 떨어져 보인다
const COMET_TAILP = COMET.tailp;  // 꼬리 테이퍼 지수. 실측 0.5 지점 0.44 · 0.75 지점 0.20 에 맞춘 값
const COMET_TAIL = COMET.tail;    // 꼬리 끝 폭(머리 대비). 실측 중앙 0.13
const FX_V95_TAPER = FX.profile === 'v95';   // C 만 v95 의 (1 - 0.78 un^2)
const FX_OFF_BASE = FX.offK[0], FX_OFF_SPAN = FX.offK[1];
const FX_HEAD_SPAN = FX.headSpan;            // headOnly 가닥이 사는 머리 구간
const FX_ALPHA = FX.alpha;                   // 'binary' | 'v95'(3단) | 'soft'(D)
// ★★칼끝 반경 정박 배수(2026-08-11 오너 지시 "칼은 짧은데 효과가 긴 것 같다").
//   획의 **바깥 가장자리**가 이 마디 칼끝 반경의 몇 배까지 허용되는가. 1.03 = 3% 여유.
//   네 벌 공통 제약이고, 이 자가 물리는 자리는 updateTrail 의 outCap 이다.
const FX_TIP_K = FX.tipK;
// ★off/half 의 단위는 미터다. 옛 판이 겪은 함정을 그대로 적어 둔다 —
//   **틈을 off 로 벌리면 안 된다.** 아래 OUT_R(획 바깥 가장자리 상한 3.50m)이
//   먼저 물린다(실측에서 본 획 중심선까지가 이미 2.69m 라 남는 방이 0.81m 뿐이다).
//   v98 이 off 를 1.09m 로 밀었다가 겹 획·갈퀴가 **통째로 폭 0 으로 깎여 사라졌다**
//   (점유 3.2% -> 0.9%, wrote 140 -> 24). 그래서 네 벌 다 off 를 1.3m 아래로 뒀고,
//   가닥 사이 틈은 화소 고정 먹 외곽선이 가닥마다 제 경계를 그어 주는 것으로 낸다.
// ★kind 는 셰이더의 채색 분기다(0 = 본 획 · 1 = 겹 획 · 2 = 마루/갈퀴).
//   headOnly 가닥은 머리 구간에만 산다(호쿠사이 갈퀴는 꼬리가 아니라 진행 방향 마루에 있다).
const STRAND_CFG = FX.cfg;
// ★lifeK = 가닥별 수명 배수. 셋이 **같은 칸에 동시에 죽으면** 안 된다 -
//   물 작화의 소멸 규칙("생길 때나 무너질 때 전부 동시면 리얼리티가 안 난다",
//   いちあっぷ 물 작화 교재). 갈퀴가 먼저 죽고 겹 획, 본 획 순으로 남는다.
// force = 1/24 홀드를 건너뛰고 무조건 다시 그린다(DEV 굽기 창구 전용.
//         클립을 손으로 밀며 부르는 경로는 gameT 가 안 흘러서 홀드에 갇힌다).
// ★★22차 멀티. 인자 R = 궤적 한 벌(rig). 예전 전역들이 전부 여기로 들어왔다.
//   로컬은 updateTrail() 이 LOCAL_RIG 에 지금 값을 담아 부르고, 원격은 mpFx 가
//   그 사람의 rig 를 담아 부른다. **계산은 이 함수 한 벌뿐이다.**
function buildRibbon(R, force) {
  // ★리본의 시계. 게임시간을 1/24 로 끊어 칸 번호를 만든다.
  const fq = Math.floor(R.clock * FX_FPS);
  if (!force && fq === R.q) {
    // 붙들고 지나간 렌더 프레임 수. 60fps 면 2~3 이 정상(3-2-3-2 홀드),
    // 히트스톱 중에는 멈춘 만큼 계속 올라간다.
    R.hold++;
    if (R.dbg && window.__trailDbg) window.__trailDbg.hold = R.hold;
    return;
  }
  R.q = fq;
  R.hold = 0;
  const n = R.buf.length;
  let w = 0;
  // ── 카메라 평면 기저 (v94 화면공간 전환의 핵심) ──
  // 리본의 **폭 방향을 카메라 평면 안에서** 잡는다. 이 두 벡터가 그 평면이다.
  _tR.setFromMatrixColumn(camera.matrixWorld, 0);
  _tU.setFromMatrixColumn(camera.matrixWorld, 1);
  // ── 1m 가 화면에서 몇 화소인가 (v97) ──
  // 셰이더의 먹 외곽선 폭을 **화소로** 잡으려고 넘긴다(위 halfArr 주석).
  // 플레이어 깊이 하나로 계산한다 - 획은 플레이어 반경 3.2m 안에만 살아서
  // 마디마다 깊이가 크게 안 다르고, 원근까지 정확히 맞출 이유는 없다(먹 두께다).
  {
    const dCam = camera.position.distanceTo(R.pos3) || 12;
    const h = renderer.domElement.height || 720;   // ★gl.canvas 말고 domElement(LOG 함정)
    R.mat.uniforms.uPxPerM.value =
      (h * 0.5) / (Math.tan(camera.fov * Math.PI / 360) * dCam);
  }
  // ★★18차 기술 변주 (mode 4 전용). **손잡이 세 줄이 여기 다 있다.**
  //   Z 3연타(Attack) = 기본. 가는 일섬이 셋 연달아 선다.
  //   X 내려찍기(Heavy) = 1.34배 굵히고 **낙뢰 지그재그**를 켠다(셰이더 uBolt).
  //   C 횡일섬(Wide)    = 0.86배로 더 가늘게. 대신 흰 심을 한 단 밝게 든다(uSharp).
  // ★기하는 넷이 똑같은 길을 지난다 - 여기서 배수 하나와 스위치 둘만 갈린다.
  //   다른 벌(A~D)에서는 이 블록이 통째로 안 돈다(uBolt/uSharp 는 셰이더에서도 안 읽힌다).
  let techW = 1.0;
  if (FX.mode === 4) {
    const bolt = (R.clip === 'Heavy') ? 1 : 0;
    const wide = (R.clip === 'Wide') ? 1 : 0;
    techW = bolt ? 1.34 : (wide ? 0.86 : 1.0);
    R.mat.uniforms.uBolt.value = bolt;
    R.mat.uniforms.uSharp.value = wide ? 1.22 : 1.0;
  }
  // 판정 계약(handoff_combat.md): 정면 리치 3.2m · 정면 부채꼴 ±75°.
  const px = R.pos3.x, pz = R.pos3.z;
  const fwx = Math.sin(R.yaw), fwz = Math.cos(R.yaw);
  // 폭이 바깥으로 자라는 기준점 = 플레이어 가슴께
  _pc.set(px, R.pos3.y + R.charH * 0.55, pz);
  const g = R.gain * (R.el.tGain || 1);
  let clipped = 0;
  let maxAge = -1;                 // 이번 프레임에 그려진 가장 오래된 마디의 나이(1/24 칸)
  // ★12-FX-D 진단 창구. "왜 획이 이만큼밖에 안 나오나"를 추측하지 말고 숫자로 본다
  //   (칼끝 정박을 넣고 나서 폭을 올려도 점유가 안 움직였다 = 폭이 범인이 아니었다).
  let dgRoom = 0, dgHalf = 0, dgCap = 0, dgTl = 0, dgTip = 0;
  // ── 살아 있는 창을 먼저 잰다 (v94) ──
  // ★수명이 여섯 칸으로 짧아지면서 생긴 함정이다. 마디 인덱스(age)는 여전히 버퍼
  //   **전체**에 걸쳐 0..1 인데 실제로 살아 있는 건 맨 앞 10% 뿐이다. 그러면
  //     · 길이 방향 테이퍼가 age 0..0.1 구간만 지나 **끝이 안 뾰족해지고**(뭉툭한 판때기)
  //     · 손그림 텍스처도 u 0..0.1 만 보여서 **등간격 평행 띠**만 남는다
  //       (심사 인용: "띠가 천으로 읽힌다" - 정작 텍스처에는 갈라지는 붓결이 그려져 있다).
  //   그래서 age 를 살아 있는 창으로 다시 정규화해서 쓴다(un).
  // ★★v96 에서 밟은 함정. 예전 식은 **첫 번째 죽은 샘플에서 멈췄다**(break).
  //   그런데 스윙이 끝난 직후에는 **제일 새 샘플이 먼저 죽는다**(칼이 느려져 t=0 으로
  //   태어난다). 그러면 aliveN 이 0 이 되고 uScale 이 폭발해서 남아 있는 획 전체가
  //   un=1 로 눌린다. v95 까지는 테이퍼 하한이 0.22 라 "좀 얇다" 정도로 지나갔는데,
  //   v96 에서 테이퍼를 sin 반주기로 바꾸자 un=1 이 곧 **폭 0** 이라 획이 통째로
  //   사라졌다(실측: 알파가 살아 있는 마디 20개의 폭이 전부 0.000m).
  //   그래서 멈추지 않고 **끝까지 훑어 제일 오래된 살아 있는 샘플**을 찾는다.
  let aliveN = 1;
  for (let j = n - 1; j >= 0; j--) {
    const ee = R.buf[j];
    const aa = (ee.f === undefined ? 0 : fq - ee.f);
    if (aa >= TRAIL_LADDER.length) break;      // 계단표 밖 = 확실히 죽었다(더 옛것도 마찬가지)
    if (ee.t * TRAIL_LADDER[aa > 0 ? aa : 0] > 0.13) aliveN = n - j;
  }
  const uScale = (n - 1) / Math.max(1, aliveN - 1);
  for (let s = 0; s < STRANDS; s++) {
    const C = STRAND_CFG[s];
    const KIND = C.kind;
    // ── 한 획은 **머리에서 이어진 한 덩어리**여야 한다 (v98) ──
    // ★수명을 열한 칸으로 늘리면서 새로 생긴 결함이다. 궤적이 길어지니 중간 어느
    //   구간이 판정 부채꼴(±75°) 밖으로 나갔다 되돌아오고, 그 구간만 알파 0 이 되어
    //   **획이 두 토막**으로 끊긴다. 화면에서는 칼과 무관한 자리에 떠 있는 파란 덩어리 +
    //   자로 자른 듯 평평한 절단면으로 보인다(= 오너가 싫어한 '판때기'가 그대로 재현).
    //   그래서 머리 쪽에서 훑다가 한 번 끊기면 **그보다 오래된 마디는 전부 안 그린다.**
    let broke = false, sawAlive = false, outRun = 0;
    for (let i = 0; i < RIBS; i++) {
      const base = (s * RIBS + i) * 2;
      if (n < 2) { R.alp[base] = 0; R.alp[base + 1] = 0; continue; }
      // 최신(n-1)에서 과거로, 실수 인덱스로 훑으며 Catmull-Rom 보간
      const fi = (i / (RIBS - 1)) * (n - 1);
      const k = n - 1 - fi;
      const i1 = Math.floor(k), fr = k - i1;
      const e = R.buf[clampi(i1, 0, n - 1)];
      const e0 = R.buf[clampi(i1 - 1, 0, n - 1)];
      const e2 = R.buf[clampi(i1 + 1, 0, n - 1)];
      const e3 = R.buf[clampi(i1 + 2, 0, n - 1)];
      cr(e0.a, e.a, e2.a, e3.a, fr, _a);
      cr(e0.b, e.b, e2.b, e3.b, fr, _b);
      _d.copy(_b).sub(_a);
      const L = _d.length() || 1;
      _d.multiplyScalar(1 / L);
      const age = i / (RIBS - 1);
      // 살아 있는 창 기준 진행도(0 = 방금 지나간 자리, 1 = 꼬리 끝). 위 uScale 주석 참조.
      const un = Math.min(1, age * uScale);
      // ── 중심선: 칼날 위 한 점 ──
      // 예전에는 리본의 **폭 방향이 칼날 축**이었다. 즉 리본 면 = (칼날) x (시간) 이라
      // 가로베기에서는 그 면이 통째로 수평이 되고, 고정 쿼터뷰에서 그게 **지면에 깔린
      // 깔개**로 보였다(심사: "귀멸은 화면에 그은 획, 게임은 지형 원근에 눕는 깔개").
      // 이제 칼날 축은 **중심선의 자리**를 정할 뿐이고, 폭은 아래에서 화면 평면으로 편다.
      _c.copy(_a).addScaledVector(_d, L * C.at);
      // ── 리치 계약: 중심선이 판정 밖이면 안 그린다 ──
      // ★"등 뒤로 뻗는 획은 그리지 마라"(판정이 ±75° 에서 잘린다). 여기서 알파를 0 으로
      //   두는 쪽을 골랐다. 경계로 접어 넣으면 부채꼴 가장자리에 그림이 뭉친다.
      const rx = _c.x - px, rz = _c.z - pz;
      const rr = Math.hypot(rx, rz);
      const fdot = rr > 1e-4 ? (rx * fwx + rz * fwz) / rr : 1;
      const inReach = rr <= REACH_R && fdot >= REACH_COS;
      // ★v98. 경계 바로 앞에서 폭을 미리 0 으로 줄인다. 수명을 열한 칸으로 늘리면서
      //   꼬리가 부채꼴·리치 경계에 닿는 일이 잦아졌는데, 알파만 0 으로 끊으면 꼬리가
      //   **자로 자른 듯 뭉툭하게** 잘린다(오너가 싫어한 '판때기'와 같은 인상).
      //   경계 앞 좁은 띠에서만 걸리므로 잘 보이는 몸통은 안 건드린다.
      const edgeK = Math.min(1, Math.max(0, (fdot - REACH_COS) / 0.10)) *
                    Math.min(1, Math.max(0, (REACH_R - rr) / 0.25));
      // ── 폭 방향: **화면에서 캐릭터로부터 바깥으로** ──
      // ★처음엔 "접선의 화면 수직"으로 폈다가 두 가지가 깨져서 바꿨다(실측 스크린샷).
      //   ① 획이 캐릭터를 **한가운데 놓고 위아래로** 부풀어 몸이 통째로 사라졌다
      //      (캐릭터 심사 FAIL 을 그대로 재현했다).
      //   ② 접선이 시선과 나란해지는 마디에서 수직 방향의 **부호가 뒤집혀** 리본이
      //      나비넥타이처럼 접혔다(큰 직선 사각형이 화면에 떴다).
      //   호의 접선에 수직인 방향은 곧 **반지름 방향**이므로, 처음부터 반지름으로
      //   잡으면 두 문제가 같이 없어진다. 부호가 구조적으로 안 뒤집히고,
      //   폭이 캐릭터에서 **바깥으로만** 자란다(= 리치 계약 방향과도 같다).
      _perp.copy(_c).sub(_pc);                 // 플레이어(가슴) -> 중심선
      let tx = _perp.dot(_tR), ty = _perp.dot(_tU);
      let tl = Math.hypot(tx, ty);
      if (tl < 1e-5) { tx = 0; ty = 1; tl = 1; }   // 화면에서 겹쳐 있으면 위로
      tx /= tl; ty /= tl;
      _perp.copy(_tR).multiplyScalar(tx).addScaledVector(_tU, ty);
      // ── 굵기 ──
      // ★수명은 이제 **1/24 칸 나이**로 센다(지수 감쇠가 아니다). 본 획은 넉 장만
      //   살고 그 뒤 두 장은 가는 먹 자취다. 계약: 본 획 2~4프레임(0.08~0.17초).
      // ★DEV 굽기 창구(__bakeTrail/__bakeWrap)는 e.f 를 안 넣고 샘플을 만든다.
      //   그때 af 가 NaN 이 되면 폭이 NaN -> **정점 좌표가 NaN** 이 되어 화면이
      //   한두 프레임 새까매진다(v88 '검은 번쩍'과 같은 기전). 없으면 '방금 태어남'으로 본다.
      const af = (e.f === undefined ? 0 : fq - e.f);
      // ★v98. 가닥마다 나이가 다르게 흐른다(lifeK). 갈퀴(0.72)는 본 획(1.00)보다
      //   먼저 죽는다 - 셋이 같은 칸에 사라지면 "판때기 하나가 꺼졌다"로 읽힌다.
      const afS = Math.round(af / (C.lifeK || 1));
      const li = afS > 0 ? (afS >= TRAIL_LADDER.length ? -1 : afS) : 0;
      const lad = li < 0 ? 0 : TRAIL_LADDER[li];
      const ladW = li < 0 ? 0 : TRAIL_LADDER_W[li];
      const inten = e.t * lad;
      const wob = 1.0 + 0.24 * Math.sin(k * 0.55 + s * 2.3) + 0.12 * Math.sin(k * 1.31 + s);
      // 길이 방향 테이퍼: **양끝이 다 뾰족하다.**
      // ★un(살아 있는 창 기준)으로 재야 실제로 뾰족해진다. age 로 재면 창 밖에서만
      //   좁아져서 화면에는 뭉툭한 판때기만 남는다.
      // ★v96. 옛 식 (1 - 0.78 un²) 은 **머리 쪽이 늘 최대 폭**이라 획이 칼끝에서
      //   뭉툭하게 시작하는 닫힌 다각형 덩어리였다(오너 지시 2항 "L/W 1.5~3.0 덩어리").
      //   sin 반주기로 바꾸면 붓 한 획의 단면이 된다 - 머리 39% -> 한가운데 100% ->
      //   꼬리 0%. 0.06 을 더해 머리를 완전한 점으로 만들지 않는다(칼끝에 붙어야 한다).
      // ★v97. 지수 0.55 -> 0.42. 양끝 뾰족함은 그대로 두고 **한가운데가 오래 굵게**
      //   간다(9차의 '물의 풍성함'이 여기서 나온다). 0.55 는 렌즈꼴이 너무 빨리
      //   가늘어져서 굵기를 올려도 가운데 한 점만 굵은 바늘이 됐다.
      // ★v97. 머리 여유 0.10 -> 0.06. 굵어진 획에서 0.10 은 머리 61% 폭이라 시작이
      //   뭉툭한 널빤지로 읽혔다(실측 크롭). 0.06 이면 47% - 칼끝에 붙어 있으면서 뾰족하다.
      // ★★v98 (11차). sin 반주기(대칭 렌즈) -> **혜성**. 오너 지시의 핵심이 여기다.
      //   대칭 렌즈는 제일 굵은 자리가 획 한가운데라, 칼끝에는 늘 가는 끝만 붙고
      //   그림 전체가 "허공에 뜬 부채꼴 호 한 장"이 된다. 실측한 원작 한 획은
      //   앞끝 가는 코 -> **앞에서 14% 지점 최대 폭** -> 뒤로 단조 감소였다.
      //     un < 0.14 : 코 0.42 에서 1.0 까지 올라온다(칼끝에 붙어 있어야 하므로 0 이 아니다)
      //     un > 0.14 : pow(1-s, 1.30) 으로 내려가 꼬리 끝 0.08
      //   실측 대조 - 0.5 지점 0.49(실측 0.44) · 0.75 지점 0.20(실측 0.20).
      // ★12-FX-D. C(v95 정박판)만 원본의 단면을 그대로 쓴다: (1 - 0.78 un^2).
      //   머리가 제일 굵고 단조 감소한다 - 혜성과 달리 코가 없어서 칼끝에서 이미
      //   최대 폭이다. v95 의 '풍성함'은 이 한 줄에서도 나온다.
      let cf;
      if (FX_V95_TAPER) {
        cf = 1.0 - 0.78 * un * un;
      } else if (un < COMET_HEAD) {
        cf = COMET_NOSE + (1 - COMET_NOSE) * Math.pow(un / COMET_HEAD, 0.62);
      } else {
        const cs2 = (un - COMET_HEAD) / (1 - COMET_HEAD);
        cf = COMET_TAIL + (1 - COMET_TAIL) * Math.pow(1 - cs2, COMET_TAILP);
      }
      const taper = cf * wob * ladW;
      // 머리 장식(캐릭터 쪽 물보라)은 갓 지나간 구간에만 산다
      const headK = C.headOnly ? Math.max(0, 1.0 - un / FX_HEAD_SPAN) : 1.0;
      // ── 몸을 침범하는 만큼 깎는다 (가독 계약. v97) ──
      // ★★아래 v97/v98 설명 세 문단은 **이제 계보 기록이다**(12-FX-D 가 대체했다).
      //   그때는 반폭이 미터 상수였고 획이 칼끝 궤적을 가운데 두고 자랐다. 지금은
      //   반폭이 '칼이 쓸고 간 방의 비율'이고 바깥 가장자리가 칼끝에 정박한다.
      //   BODY_R 은 그대로 살아 있다 - 몸 반경 안에는 여전히 한 화소도 안 그린다.
      // ★폭을 되돌리면서 새로 생긴 위험이다. 스윙 시작·끝(특히 칼을 머리 위로 세울 때)
      //   에는 중심선이 몸 코앞에 온다. 거기서 반폭 0.6m 를 그대로 펴면 그 한 마디가
      //   **주인공을 덮는 덩어리**가 된다(9차의 "머리 80~94% 가림"이 이 기전).
      // ★"몸에서 얼마나 먼가"로 폭을 배수 조절하는 방식은 실측에서 안 먹었다(1차 시도.
      //   머리 덮임이 여전히 0.98 이었다). 배수는 **안쪽 가장자리가 어디에 닿는지**를
      //   모르기 때문이다. 그래서 지금은 안쪽 가장자리를 직접 잰다:
      //     안쪽 가장자리 거리 = tl + off - half  (tl = 가슴 -> 중심선, 화면 평면)
      //   이 값이 BODY_R 보다 작으면 **그만큼만 깎는다.** 상한이 증명되는 방식이다 —
      //   가슴 반지름 BODY_R 안에는 어떤 마디도 한 화소도 안 그린다.
      // ★BODY_R 0.80m = 가슴(charH 0.55)에서 머리 꼭대기(charH 1.02)까지의 거리다.
      // ★바깥도 같은 방식으로 닫는다. 안 그러면 아래 clampReach 가 정점을 리치 원에
      //   **몰아붙여** 가장자리가 자로 자른 듯 평평해진다 = 오너가 싫어한 '판때기'
      //   (실측 크롭 x_sumen. 획이 붓이 아니라 널빤지로 보였다). 여기서 반폭을 줄이면
      //   실루엣이 리치 원을 따라 **매끈하게** 닫히고 clampReach 는 거의 안 걸린다.
      // ★v98. 0.80 -> 0.95. 수명이 두 배가 되면서 획이 몸 위에 머무는 칸 수도 두 배가
      //   됐다 - 같은 반지름으로는 머리 덮임 최악이 70% 까지 올라갔다(상한 60).
      // ★12-FX-D. 네 벌이 **똑같이** 지키는 두 자다(공통 원칙: 과대 금지·몸 가림 금지).
      // ★★2026-08-11. 0.95 -> **0.82**. 실측으로 되돌린 값이다 —
      //   칼끝 반경(가슴 기준·카메라 평면)이 스윙 내내 **1.27~1.42m 뿐**이다
      //   (probe_room.js. 손은 0.54~0.80m). 안쪽 벽이 0.95 면 칼이 지나간 방이
      //   0.49m 밖에 안 남아 획이 통째로 0 으로 깎였다(실측 점유 0.16%).
      //   0.82 는 이 값의 원래 근거(가슴 charH 0.55 -> 머리 꼭대기 charH 1.02 = 0.82m)
      //   그대로다 - 머리 가림 계약은 유지하면서 칼이 쓸고 간 방을 되돌려 준다.
      const BODY_R = FX.bodyR;                   // 0.82
      const OUT_R = FX.outR;                     // 안전 상한(clampReach 3.6 안쪽). 아래 칼끝 자가 먼저 문다
      // ══════════════════════════════════════════════════════════════════
      // ★★칼끝 반경 정박 (2026-08-11. 오너 실시간 지시)
      //   **"칼은 짧은데 효과가 긴 것 같다."**
      // 원인은 폭이 아니라 **어디를 가운데 두느냐**였다. 지금까지 획은 칼끝 궤적을
      // **가운데** 두고 ±half 로 자랐다 = 바깥 절반(최대 0.9m)이 늘 **칼끝 바깥 허공**이다.
      // 칼(카타나) 자체가 1m 남짓인데 그 밖으로 한 자루 길이가 더 뻗으니
      // "칼보다 효과가 길다"로 읽히는 것이 당연하다.
      // → 이 마디의 **칼끝이 실제로 있는 반경**을 재서, 획의 바깥 가장자리를 거기에
      //   정박시킨다(넘으면 통째로 안쪽으로 민다. 깎지 않고 밀어야 면적이 산다).
      //   폭은 그대로 두고 **칼이 지나간 안쪽**으로 자란다 = 칼이 쓸고 간 자리다.
      // ★tipK 1.03 = 3% 여유. 0 으로 두면 안티에일리어싱 한 겹이 칼끝에서 잘려
      //   획이 칼끝에 안 닿아 보인다(포말·물방울은 물보라가 따로 뿌리므로 예외 허용).
      _tv.copy(_b).sub(_pc);
      const tipR = Math.hypot(_tv.dot(_tR), _tv.dot(_tU));
      const outCap = Math.min(OUT_R, Math.max(BODY_R + 0.10, tipR * FX_TIP_K));
      // ★v98. 0.72 + 0.28*taper -> **0.30 + 0.70*taper**. 옛 값은 꼬리에서도 가닥이
      //   72% 벌어진 채로 남아 '나란한 바늘 셋'이 됐다. 별똥별은 꼬리가 **한 점으로
      //   수렴**해야 한다 - 꼬리로 갈수록 가닥이 중심선으로 모이게 한다.
      // ★12-FX-D. 꼬리에서 가닥이 얼마나 모이는가. A/B/D 는 0.30+0.70(한 점으로 수렴),
      //   C 는 v95 원본의 0.72+0.28(꼬리에서도 부채가 남는다 = 그 판의 풍성함).
      // ══════════════════════════════════════════════════════════════════
      // ★★폭을 **칼이 쓸고 간 방(room)의 비율**로 잡는다 (2026-08-11 오너 지시 1항)
      // 1차 시도에서 반폭을 옛날처럼 미터로 두고 바깥만 칼끝에 정박했더니 획이
      // **통째로 사라졌다**(실측 점유 3.3% -> 0.36%). 이유는 산수다 —
      //   쓸 수 있는 방 = 칼끝 반경 x 1.03 - 몸 반경(BODY_R)
      //   칼끝 반경이 2.0m 면 방이 1.24m 인데 옛 반폭 0.888m 는 폭이 1.78m 다.
      //   들어갈 자리가 없으니 몸 침범분으로 다 깎여 0 이 된다.
      // → 그래서 반폭·안쪽밀기를 **방의 비율**로 적는다. 칼이 멀리 뻗은 마디에서는
      //   저절로 굵어지고 몸 앞으로 접힌 마디에서는 저절로 가늘어진다.
      //   이 한 줄이 "이펙트는 칼이 지나간 자리"를 기하로 증명한다.
      // ★gK: 일격기가 좀 더 굵어야 하지만(연출) 방을 넘을 수는 없으므로 배수를 조인다.
      const room = Math.max(0, outCap - BODY_R);
      const gK = Math.min(1.15, Math.max(0.72, g / 1.55));
      let half = C.w * room * taper * headK * edgeK * gK * techW;   // ★techW = 18차 기술 변주
      if (half > room * 0.48) half = room * 0.48;
      // C.inset = 이 가닥의 바깥 가장자리가 **칼끝에서 안쪽으로** 얼마나 물러나는가(방 비율).
      // 0 = 칼끝에 붙은 마루(포말·갈퀴), 클수록 몸 쪽에 눕는 겹 획.
      let inset = C.inset * room * (FX_OFF_BASE + FX_OFF_SPAN * taper);
      const insetMax = Math.max(0, room - 2 * half);
      if (inset > insetMax) inset = insetMax;
      // 바깥 가장자리 = 칼끝 반경 - 물러난 양. off 는 그 자리를 만들기 위한 값이다.
      const off = outCap - inset - half - tl;
      if (room > dgRoom) dgRoom = room;
      if (half > dgHalf) dgHalf = half;
      if (outCap > dgCap) dgCap = outCap;
      if (tl > dgTl) dgTl = tl;
      if (tipR > dgTip) dgTip = tipR;
      _pa.copy(_c).addScaledVector(_perp, off + half);
      _pb.copy(_c).addScaledVector(_perp, off - half);
      // ★폭이 화면에서 바깥으로 자라므로 가로베기에서는 대개 공중으로 뻗지만,
      //   내려베기(칼이 화면 위아래로 움직일 때)에서는 화면 가로로 뻗는다. 그때 획이
      //   리치 밖으로 삐져나가지 않게 XZ 반지름만 한 번 조인다(높이는 자유 —
      //   공중은 아무 거짓말도 안 하고, 오히려 '세로 스윕'이 화면 존재감의 주된 출처다).
      clampReach(_pa, px, pz); clampReach(_pb, px, pz);
      R.pos[base * 3] = _pa.x; R.pos[base * 3 + 1] = _pa.y; R.pos[base * 3 + 2] = _pa.z;
      R.pos[(base + 1) * 3] = _pb.x; R.pos[(base + 1) * 3 + 1] = _pb.y; R.pos[(base + 1) * 3 + 2] = _pb.z;
      // ★u 도 un 이다. 손그림 텍스처(갈라지는 붓결·찢긴 끝)가 **보이는 획 전체**에
      //   걸쳐 펴져야 한다. age 를 넘기면 텍스처 앞 10% 만 늘어나 등간격 띠가 된다.
      R.uv[base * 2] = un; R.uv[base * 2 + 1] = 1.0;         // 바깥 = 포말 쪽
      R.uv[(base + 1) * 2] = un; R.uv[(base + 1) * 2 + 1] = 0.0;
      R.seed[base] = KIND; R.seed[base + 1] = KIND;
      // 이 마디의 반폭(m). 셰이더가 먹 외곽선을 화소로 잡는 데 쓴다
      R.half[base] = half; R.half[base + 1] = half;
      // 알파는 계단으로. 매끈하게 흐리면 칠 그림이 아니라 다시 빛처럼 보인다.
      // ★알파는 **형태의 유/무**만 가른다(오너 지시). 반투명 구간이 곧 '유리 부채'였다.
      // ★v98. 계단 1.0/0.92/0.78 -> **1.0 아니면 0**. 오너 지시 그대로 "알파는 형태의
      //   유/무만 가른다"인데 0.78~0.92 구간이 남아 있었고, 이 게임 배경이 밝은 모래라
      //   그 반투명 구간에서 획이 바닥색과 섞여 **채도가 통째로 깎였다**(실측: 획 화소
      //   채도 중앙 0.20~0.24. 오너가 그림체를 칭찬한 v95 는 0.31~0.48, 원작은 0.56).
      //   불투명하게 칠하면 팔레트 색이 그대로 화면에 오른다.
      // ★12-FX-D. 벌마다 계단이 다르다.
      //   'binary'(A/B) 1.0 아니면 0 · 'v95'(C) 원본 3단 · 'soft'(D) 잔광이라 넉 단.
      //   D 만 반투명을 허용하는 이유는 그 벌의 정의가 '잔광'이기 때문이다(대조군).
      let q;
      if (FX_ALPHA === 'v95') q = inten > 0.46 ? 1.0 : (inten > 0.26 ? 0.92 : (inten > 0.13 ? 0.78 : 0));
      // ★18차 'flash'. 가산이라 알파가 곧 **세기**다. 세 단으로 뚝뚝 꺼진다 —
      //   두 칸은 온전히 서 있고 뒤 세 칸에서 0.72 -> 0.38 -> 0 으로 떨어진다.
      //   binary(1 아니면 0)로 두면 5칸이 통째로 최대 밝기로 살다가 한 프레임에
      //   사라져서 '섬광'이 아니라 '깜빡이는 판'이 된다.
      else if (FX_ALPHA === 'flash') q = inten > 0.55 ? 1.0 : (inten > 0.30 ? 0.72 : (inten > 0.13 ? 0.38 : 0));
      else if (FX_ALPHA === 'soft') q = inten > 0.60 ? 1.0 : (inten > 0.40 ? 0.78 : (inten > 0.22 ? 0.52 : (inten > 0.10 ? 0.30 : 0)));
      else q = inten > 0.13 ? 1.0 : 0;
      if (!inReach) { q = 0; if (i === 0) clipped++; }
      // ★연결성 규칙(위 broke 주석). **판정 부채꼴을 벗어난 구간이 세 마디 이상 이어지면**
      //   그보다 오래된 마디는 전부 안 그린다.
      // ★끊는 조건을 alpha 가 아니라 **inReach** 로 잡는 것이 중요하다. 1차 시도에서
      //   "알파 0 이 한 번이라도 나오면 끊는다"로 뒀더니 스윙 중에 칼이 잠깐 느려져
      //   태생 세기가 0.13 아래로 내려간 마디 하나 때문에 **꼬리가 통째로 사라졌다**
      //   (실측: 점유가 3.2% -> 0.9% 로, wrote 가 140 -> 24 로 주저앉았다).
      //   세기 구멍은 원래 있던 것이고(v97 도 그랬다) 그림에서는 붓결로 읽힌다.
      if (inReach) { outRun = 0; if (q > 0) sawAlive = true; }
      else if (sawAlive && ++outRun >= 3) broke = true;
      if (broke) q = 0;
      // 칼별 알파 배수. 계단은 그대로 두고 전체만 낮춘다(계단을 재계산하면 띠가 진다).
      q *= (R.el.tAlpha === undefined ? 1 : R.el.tAlpha);
      R.alp[base] = q; R.alp[base + 1] = q;
      if (q > 0) { w++; if (af > maxAge) maxAge = af; }
    }
  }
  // ★q 는 지금 그린 1/24 칸 번호다. 연속 캡처에서 이 값이 몇 프레임마다 오르는지가
  //   곧 "리본이 계단으로 자라는가"의 숫자 증거다(60fps 면 3-2-3-2 여야 한다).
  // clipped = 리치·부채꼴 밖이라 안 그린 가닥 수(크기 계약이 실제로 물렸는지 숫자로 본다)
  // ★v96 계약 창구. oldest = **지금 그려지는 가장 오래된 마디의 나이**(1/24 칸).
  //   "본 획은 2~4프레임만 산다"는 계약이 실제로 물렸는지는 이 값으로만 잰다
  //   (화면에서 '이펙트가 보이는 시간'을 재면 스윙 시간까지 더해져 계약과 다른 것을 재게 된다).
  //   TRAIL_LADDER.length - 1 이 상한이므로 이 값이 3 을 넘으면 계약이 깨진 것이다.
  // ★22차. 이번 칸에 실제로 알파가 살아 있는 마디가 몇 개였나. 로컬은 아래 진단
  //   창구가 같은 값을 쓰고, 원격은 이 수로 "이펙트가 떴다"를 세고 메시를 껐다 켠다.
  R.wrote = w;
  if (R.dbg) window.__trailDbg = { n, wrote: w, q: R.q, hold: 0, clipped, aliveN,
                        room: +dgRoom.toFixed(2), half: +dgHalf.toFixed(2),
                        cap: +dgCap.toFixed(2), tl: +dgTl.toFixed(2), tip: +dgTip.toFixed(2),
                        oldest: maxAge, ladder: TRAIL_LADDER.length,
                        lastT: R.buf.length ? R.buf[R.buf.length-1].t : -1 };
  R.geo.attributes.position.needsUpdate = true;
  R.geo.attributes.aUV.needsUpdate = true;
  R.geo.attributes.aAlpha.needsUpdate = true;
  R.geo.attributes.aSeed.needsUpdate = true;
  R.geo.attributes.aHalf.needsUpdate = true;
}

// ── 로컬 플레이어 통로 ──
// ★전역(root·charH·trailGain·curEl·atkClip·gameT)을 rig 필드에 옮겨 담고 부른다.
//   이 자리가 곧 "옛 updateTrail() 이 읽던 값들"의 목록이다.
function updateTrail(force) {
  LOCAL_RIG.clock = gameT;
  LOCAL_RIG.pos3 = root.position;          // Group 의 Vector3 는 갈리지 않으므로 참조로 둔다
  LOCAL_RIG.yaw = root.rotation.y;
  LOCAL_RIG.charH = charH;
  LOCAL_RIG.gain = trailGain;
  LOCAL_RIG.el = curEl;
  LOCAL_RIG.clip = atkClip;
  buildRibbon(LOCAL_RIG, force);
}

// ---------- 캐릭터 ----------
const root = new THREE.Group();
scene.add(root);
// ── 시작 위치 ──
// 맵의 spawns[] 중 하나에서 시작한다(?spawn=2 로 바꿀 수 있다). 어디를 보고 서는지도
// 맵이 정해 준다(yaw). 죽어서 되살아날 때도, R(제자리)도 전부 이 함수를 지나게 해서
// "시작 자리"가 한 군데서만 정해지게 한다.
const SPAWN_I = +(new URLSearchParams(location.search).get('spawn') || 0);
function toSpawn() {
  const s = level.spawnPoint(SPAWN_I);
  root.position.set(s.x, s.y, s.z);
  root.rotation.y = s.yaw;
}
toSpawn();
// ── 캐릭터별 설정 ──
// 발 미끄러짐 0 의 조건: 이동속도 = (클립의 접지 발 속도) x (재생속도)
// 접지 발 속도는 blender/probe_stride.py 실측(게임 키 기준, 재생속도 1.0):
//   검사  걷기 0.98 / 달리기 1.74      탱커  걷기 1.31 / 달리기 1.48
// ★예전엔 검사 달리기를 2.42 로 잘못 알고 4.8 을 줘서 **49% 미끄러지고** 있었다.
//   그 2.42 는 blend 원본을 잰 값인데 게임이 쓰는 glb 는 키 기준이 달랐다.
//   이제 게임이 실제 로드하는 glb 를, 게임과 같은 방식(무기 제외)으로 잰다.
const CHAR_CFG = {
  // jump 는 클립 안에서 구간이 어디인지를 초 단위로 적는다.
  // start=도약 시작(웅크림은 건너뛴다) / rise=상승 중 버틸 지점 / fall=하강 중 버틸 지점
  // land=착지 흡수 시작 / end=회복 끝
  // ★예전엔 이 값이 검사 클립 기준으로 하드코딩(0.20/0.40/0.50/0.73)돼 있었다.
  //   궁수 점프는 1.92초짜리라 0.73 이면 **정점(0.83)에 닿기도 전에** 잘려서,
  //   팔을 위로 뻗던 도중에 Idle 로 튀며 양팔이 휙 돌아갔다.
  // 검사(kensa)는 Meshy 로 받은 삿갓 쓴 한국 검사 몸이다.
  // Idle/Attack/Heavy/Wide/Jump 는 slayer 무브셋을 이식한 것이고
  // (blender/s26_swordsman.py -> s24_moveset.py), 점프 구간(초)은 그래서 slayer 와 같다.
  // ★걷기/달리기만 2026-08-10 에 **Meshy 네이티브 원본**으로 갈아 끼웠다
  //   (blender/s27_kensa_native.py). 같은 리그라 리타게팅 왜곡이 0 이고, 그 대신
  //   보폭과 사이클이 통째로 달라져서 발 속도를 다시 쟀다:
  //     걷기   1.033초 / 발 속도 1.570 -> 이동 1.71 을 내려고 재생속도 1.09
  //     달리기 0.633초 / 발 속도 5.325 -> 이동 3.20 을 내려고 재생속도 0.60
  //   ★이 값은 **모델 공간**에서 잰 것이다. probe_stride.py 는 발을 골반 기준으로
  //     재는데, 게임은 모델 원점을 고정한 채 root 만 미므로 골반이 앞뒤로 출렁이면
  //     그만큼 값이 어긋난다(이번 걷기에서 1.570 vs 1.474 로 6% 차이가 났다).
  // ★달리기 재생속도가 1 밑으로 내려간 이유와, 남은 선택지
  //   네이티브 달리기는 **접지 5프레임 / 체공 5프레임짜리 전력질주**다. 원본 속도로
  //   틀면 5.3m/s 로 달리는 그림이다. 이동속도를 3.20 으로 묶어 두면 발이 안
  //   미끄러지는 대신 사이클이 1.05초(분당 114걸음)로 늘어나고 **체공이 0.26초**가 된다.
  //   사람 전력질주 체공은 0.10~0.15초라, 이대로면 살짝 둥둥 뜬 것처럼 보일 수 있다.
  //   더 힘차게 만들려면 이동속도를 올려야 한다(미끄러짐은 그래도 0이다):
  //     run: { spd: 4.42, ts: 0.83 }  -> 사이클 0.76초(분당 158걸음), 체공 0.19초
  //   다만 이동속도를 38% 올리면 요괴 추격·칼 사거리·전진 스텝이 전부 다시 잡혀야 해서
  //   여기서 임의로 안 바꿨다. 바꾸려면 enemy.js/feel.js 와 같이 봐야 한다.
  kensa:  { h: 1.75, walk: { spd: 1.71, ts: 1.09 }, run: { spd: 3.20, ts: 0.60 },
            jump: { start: 0.00, rise: 0.20, fall: 0.40, land: 0.50, end: 0.73 } },
  // 검사 걷기는 2026-08-05 에 발 궤적 + IK 로 다시 만들었다(옛 4포즈 클립은 접지 구간이
  // 없어 두 발이 서로 반대로 왕복했다). 재작성 후 실측 발 속도 0.928, 재생속도 1.84 -> 1.71.
  slayer: { h: 1.75, walk: { spd: 1.71, ts: 1.84 }, run: { spd: 3.20, ts: 1.84 },
            jump: { start: 0.00, rise: 0.20, fall: 0.40, land: 0.50, end: 0.73 } },
  tank:   { h: 2.00, walk: { spd: 1.70, ts: 1.30 }, run: { spd: 2.20, ts: 1.49 } },
  // 궁수 걷기: 원본에 뿌리 뼈 스케일 1.1765 가 박혀 있어 걸을 때 17.65% 부풀었다.
  // 제거 후 보폭이 정확히 15% 줄어 발 속도 1.63 -> 1.39. 이동 1.63 을 유지하려고 재생속도를 올린다.
  // 궁수 점프는 클립이 두 개다(glb 에 Jump / JumpB 둘 다 들어 있다).
  //   Jump  = 2.50초. 몸 회전 11도, 발이 뜨는 높이 0.30. **이걸 쓴다**
  //   JumpB = 1.92초. 몸이 82도 돌아가고 발이 0.94 뜬다. 게임이 이미 루트를 0.95 올리므로
  //           겹쳐서 겉보기 1.9 가 되고, 끝날 때 40도 돌아간 채라 Idle 로 홱 돌아온다.
  // ★Jump 는 첫 키가 0.042초다. time=0 이면 그 프레임에 멈춰 있는 셈이 되니 start 를 꼭 준다.
  archer: { h: 1.70, walk: { spd: 1.63, ts: 1.17 }, run: { spd: 3.20, ts: 0.64 },
            jump: { start: 0.417, rise: 0.625, fall: 0.875, land: 1.000, end: 1.417 } },
  // 병사는 걷기가 합성 클립이라 발 속도 측정이 1.35 와 0.88 로 갈렸다.
  // 중간값 1.1 로 잡고 눈으로 맞춘다. 달리기 2.35 는 두 방식이 일치해 신뢰도 높다.
  soldier:{ h: 1.75, walk: { spd: 1.80, ts: 1.64 }, run: { spd: 3.20, ts: 1.36 } },
  // 기본 모델은 클립이 걷기/달리기뿐이라 Idle 을 만들어 넣었다. 공격/점프 없음(방어 코드 있음).
  // 실측 발 속도 걷기 1.42 / 달리기 4.85. 달리기는 보폭 1.41m 짜리 전력질주라 재생속도를 낮춘다.
  basic:  { h: 1.75, walk: { spd: 1.71, ts: 1.20 }, run: { spd: 3.20, ts: 0.66 } },
  // 기본2(basic2) = 시작 캐릭터. Meshy 알몸 베이스에 우리 칼 7자루를 꿰고
  // slayer 무브셋 5종(Idle/Attack/Heavy/Wide/Jump)을 이식했다.
  //   blender/s31_basic2_body.py -> s24_moveset.py -> s27_kensa_native.py
  // ★2026-08-14: Walk/Run 의 **하체만** Unity ToonSoldier 로 교체했다.
  //   s42_basic2_soldier_legs.py 가 Soldier 골반 이동 + 양쪽 Thigh/Calf/Foot/Toe0
  //   회전을 레스트 델타로 굽고, 현재 basic2 의 골반 회전·상체·팔·검 자세는
  //   정규화 위상으로 유지한다. 전투/대기/점프 5종도 그대로다.
  //   Run 은 원본 infantry_combat_run 의 26키다.
  // ★★2026-08-25 26차: Walk 하체를 s42 GAIT_V26 **절차 보행**으로 재작(오너 "질질
  //   끌며 걷는 느낌" 수리). 병의 규명: Soldier 원팩에 Walk 가 없어 s12 가 Run 을
  //   완화 합성한 클립이었고(달리기 골격), 접지 듀티 12~18%(정상 60%)·양발 동시접지
  //   0%·접지 중 발이 골반 대비 2.23m/s 로 긁혀 **ts 1.18 에서 지면 대비 초당 0.92m
  //   역방향 스케이트(-54%)**였다. 게다가 회전 리타게팅이라 다리가 긴 basic2 에서
  //   발끝 들림이 0.33~0.38m(하이니 행진)로 증폭됐다. ts 로는 못 고치는 병이라
  //   (접지 동기 ts 0.766 을 주면 보폭x케이던스가 모자라 몸이 +49% 앞으로 미끄러진다)
  //   클립을 보행의 산수로 다시 구웠다: 듀티 0.55·양발 동시접지 15%·발끝 들림
  //   0.125~0.133m·무릎 130~173도·직립.
  // 실측(gait26.py, 26차 최종 glb): 접지 발속도 1.190 m/s(클립초)
  //   -> 이동 1.71 에 ts **1.42** = 미끄러짐 +0.2% (26차 최종 glb 실측 접지 발속도
  //   1.202, 필요 ts 1.422. 분당 ~150걸음. 구 1.18 은 새 클립에서 -19% 스케이트가
  //   된다 — 클립과 ts 는 한 몸이다)
  //   Run 1.09320m · 0.8667초 -> 3.20m/s 에 ts 1.27 (약 176걸음/분. 26차 불변 —
  //   접지가 3장 미만짜리 전력질주 클립이라 s27 식 접지 발속도 측정은 불가)
  // 점프는 slayer 이식본이라 구간(초)이 kensa 와 같다.
  basic2: { h: 1.75, walk: { spd: 1.71, ts: 1.42 }, run: { spd: 3.20, ts: 1.27 },
            jump: { start: 0.00, rise: 0.20, fall: 0.40, land: 0.50, end: 0.73 } },
};
const DEF_CFG = { h: 1.75, walk: { spd: 1.8, ts: 1.0 }, run: { spd: 3.2, ts: 1.0 },
                  jump: { start: 0.00, rise: 0.20, fall: 0.40, land: 0.50, end: 0.73 } };
let curCfg = DEF_CFG;
let mixer = null, current = null, model = null;
const actions = {};
let handBone = null, charH = 2.4;
// ★21차. **왼손** 본. 오른손잡이 궁수는 왼손이 활을 쥔다(blender/s11_archer.py 의 SHOT 표).
//   화살이 떠나는 자리를 여기서 읽는다 - 몸통에서 어림잡으면 만작 자세에서 팔이
//   앞으로 뻗어 있는 만큼(약 0.4m) 화살이 가슴에서 튀어나오는 그림이 된다.
//   없는 캐릭터면 null 이고, 그때는 arrow 발사 자리가 몸 기준 어림값으로 흐른다.
let lhandBone = null;
const footBones = [];
const _fp = new THREE.Vector3();
// 바인드 포즈 박스로 높이를 맞추면 포즈에 따라 발이 뜨거나 파묻힌다.
// (일격기·횡일섬은 루트를 내려서 주저앉으므로 특히 심하다)
// 매 프레임 **가장 낮은 발 본**을 바닥에 붙인다. 웅크리면 엉덩이가 내려가고
// 발은 그대로 - 물리적으로도 이게 맞다.
const _lowHist = [];
function groundFeet() {
  if (!model || !footBones.length) return;
  let low = Infinity;
  for (const b of footBones) {
    b.updateWorldMatrix(true, false);
    _fp.setFromMatrixPosition(b.matrixWorld);
    if (_fp.y < low) low = _fp.y;
  }
  if (low === Infinity) return;
  // ★달리기에는 **두 발이 다 뜨는 체공 구간**이 있다. 매 프레임 '지금 가장 낮은
  // 발'을 바닥에 붙이면 그 순간에도 발을 바닥까지 끌어내려 몸이 주저앉고,
  // 애니메이터가 넣은 골반 상하(0.236)가 통째로 사라진다.
  // 그래서 달릴 때만 최근 한 사이클의 **최저값**(= 실제로 디딘 발)을 바닥으로 삼는다.
  // 주저앉기(수면참)까지 이렇게 하면 일어설 때 캐릭터가 떠 있으므로 달리기 한정.
  // 창은 프레임 수가 아니라 **시간**으로: 120Hz 에서 창이 반으로 줄면 안 된다.
  // 달리기 한 사이클 = 0.83 / 1.85 = 0.45 초.
  const rel = low - model.position.y;            // 모델 원점 기준 발 높이(포즈만의 함수)
  let base = rel;
  if (current && current === actions.Run) {
    const now = gameT;               // ★게임시간. 히트스톱 중에 창이 흘러가면 안 된다
    _lowHist.push(now, rel);
    while (_lowHist.length > 2 && _lowHist[0] < now - 0.5) _lowHist.splice(0, 2);
    for (let i = 1; i < _lowHist.length; i += 2) if (_lowHist[i] < base) base = _lowHist[i];
  } else if (_lowHist.length) {
    _lowHist.length = 0;
  }
  model.position.y = (root.position.y + charH * 0.045) - base;   // 발바닥 두께만큼 띄움
}
// ★★공격 타이밍은 **게임시간(gameT)** 을 쓴다. 절대 performance.now() 를 쓰면 안 된다.
//   히트스톱이 세계를 45~120ms 멈추는데 콤보 창만 벽시계로 흐르면, 멈춘 동안 창이
//   그대로 지나가 **히트스톱 중에 3연타가 씹힌다.** dt 를 멈추는 것과 시계를 멈추는 것을
//   같이 해야 한다(2026-08-10 히트스톱 도입 때 이것 하나 때문에 설계가 갈렸다).
let gameT = 0;
// ---------------------------------------------------------------------------
// ★히트스톱 한 겹 더 (17차 타격감 팩)
// ---------------------------------------------------------------------------
// feel.js 에 이미 히트스톱이 있다(명중 55ms · 처치 105ms, 배율 0.05). 그건 그대로
// 두고 여기서 **덮는 층**을 하나 더 깐다. 이유 둘:
//   1) 오너 요구가 "명중 순간 60~80ms" 인데 feel.js 는 이번 판 소유가 아니라 못 고친다.
//   2) 다타(3연타)는 타마다 짧게 · 처치타는 조금 길게 — 이 배분을 main.js 가 쥐어야
//      스윙 번호(enemy.swing)를 보고 예산을 나눌 수 있다.
// ★두 겹은 **안 더해진다.** 아래 tick 에서 min(feel 배율, 이 배율) 로 더 멈춘 쪽만 쓴다.
//   그래서 최종 정지 길이는 max(feel, 여기) 가 되고 겹쳐도 늘어지지 않는다.
// ★게임시계(gameT)도 같이 멎으므로 콤보 창·커밋·버퍼가 전부 함께 선다(위 주석의 그 계약).
const HS_SCALE = 0.04;        // 멈춘 동안의 시간 배율. 0 이 아닌 이유는 feel.js STOP_SCALE 주석과 같다
const HS_HIT = 0.070;         // 안 죽인 명중. 60~80ms 대역의 한가운데
const HS_KILL = 0.112;        // 처치. 명중보다 한 박자 길다
const HS_BUDGET = 0.150;      // 한 스윙에 여러 마리를 베어도 합쳐서 이 이상은 안 멈춘다
let hsLeft = 0, hsBudget = 0, hsSwing = -1;
function addHitStop(sec, swing) {
  if (swing !== undefined && swing !== hsSwing) { hsSwing = swing; hsBudget = 0; }
  const use = Math.min(sec, Math.max(0, HS_BUDGET - hsBudget));
  if (use <= 0) return 0;
  hsBudget += use;
  if (use > hsLeft) hsLeft = use;     // 겹치면 긴 쪽으로(더하면 3연타가 늘어진다)
  return use;
}
function stepHitStop(rawDt) {
  if (hsLeft <= 0) return 1;
  hsLeft -= rawDt;
  if (hsLeft < 0) hsLeft = 0;
  return HS_SCALE;
}
let attacking = false, attackEnd = 0, comboStep = 0, comboWindow = 0;
// ── 입력 버퍼 (2026-08-10 9차. 건틀릿 손맛 1위 격차) ──
// 심사 실측: "200ms 간격으로 Z 를 세 번 눌렀는데 두 번만 나갔다." 원인이 둘이었다.
//   1) 버퍼가 **Z 전용**이고, 예약분을 푸는 자리가 클립이 통째로 끝나는 프레임뿐이었다
//      (= 캔슬로 풀린 경우엔 예약이 그냥 버려졌다)
//   2) 창이 0.25초라도 커밋(0.28초)보다 짧아서, 커밋 안에 누른 입력은 늘 만료됐다
// 이제 버퍼는 **어떤 액션이든** 담고(BUF.kind), 캔슬 가능해지는 그 프레임에 바로 푼다.
// 창은 0.15초. 짧아 보이지만 푸는 자리가 앞당겨져서 실효는 예전보다 훨씬 길다.
// ★0.15 가 아니라 0.20 인 이유: 아래 ATK_MIN_GAP(0.24) 때문에 예약이 최대 0.24초를
//   기다릴 수 있다. 창이 그보다 훨씬 짧으면 "기다리다 만료"가 나서 버퍼가 무의미해진다.
const BUFFER_WINDOW = 0.20;
// ── 연타 최소 간격 ──
// ★enemy.js 의 SWING_GAP 0.22 와 맞물린 값이다. 그 파일은 "0.22초 안에 다시 켜진 hot"
//   을 **같은 스윙**으로 보고 번호를 안 올린다(= 같은 요괴를 다시 못 벤다). 그래서
//   0.22 보다 빠르게 다음 타를 내보내면 **보이고 들리는데 안 들어가는 스윙**이 생긴다.
//   그건 이번 파도가 고치려는 '판정 정직성' 자체를 깨는 일이라, 여기서 바닥을 깐다.
//   예약(버퍼)이 그 사이를 메우므로 입력은 안 버려지고 0.24초에 정확히 나간다.
//   ★enemy.js 가 SWING_GAP 을 내리면 이 값도 같이 내릴 것(handoff_combat.md 에 요청해 뒀다).
const ATK_MIN_GAP = 0.24;
let lastAtkStartT = -99;
const BUF = { kind: null, t: -99 };
function bufferInput(kind) { BUF.kind = kind; BUF.t = gameT; }
function bufferAlive(now) { return BUF.kind && (now - BUF.t) < BUFFER_WINDOW; }
function clearBuffer() { BUF.kind = null; BUF.t = -99; }
let heavy = false;                 // 일격기 중이면 궤적이 커진다

// ---------------------------------------------------------------- 이동 캔슬 (2차 QA S1)
// ★2차 QA 1순위. "Z 한 번에 최장 1.36초 정지. 포위당하면 이게 사망 원인 1위다."
//   실측(headed 60fps, 이동키를 누른 채 Z 한 번):
//     Z 실효 정지 1213ms / X 1808ms / C 1528ms.
//   원인은 단순하다. `moving = (mx||mz) && !attacking` 이라 **클립이 끝날 때까지**
//   이동이 통째로 막혔다. 그런데 클립의 뒤쪽 절반은 이미 다 벤 뒤의 회복 동작이다.
//
// 규칙:
//   커밋 구간 = 입력 ~ **첫 스윙의 타격 판정이 끝나는 순간**. 여기는 못 끊는다
//               (끊을 수 있게 하면 휘두르다 마는 그림이 나온다).
//   그 뒤     = 이동 입력이 남은 회복을 캔슬한다. 콤보 창은 살려 둬서 Z 를 이으면 다음 타.
//
// ★커밋 경계는 추측이 아니라 실측이다. enemy.js 의 타격 게이트(hot: 칼끝 속도
//   HOT_ON 0.42 에서 켜지고 HOT_OFF 0.16 에서 꺼진다)를 60fps 로 찍어 클립별로 쟀다.
//   입력 후 경과 ms 기준으로 hot 구간은 이랬다:
//     Attack : [68.8~137] [190.3~264.3] [366.9~434.3] [726.3~825.3]   (스윙 3개, 클립 1.185초)
//              ★앞 둘은 enemy.js 가 같은 스윙(SWING_GAP 0.22)으로 묶는다 = 1타는 264ms 에 끝난다.
//                그 사이 52ms 의 골(137~190)에서 끊으면 1타를 휘두르다 마는 게 되므로
//                커밋을 264ms 뒤인 0.28 에 둔다.
//     Heavy  : [842.3~954.6]                                          (한 방, 클립 1.797초)
//     Wide   : [559.8~679.0]                                          (한 방, 클립 1.500초)
//   X·C 가 긴 건 모아서 늦게 베는 기술이라 그렇다. "타격 구간 끝 기준"은 셋 다 같다.
//
// ── 2026-08-12 13-모션이식: 베기 3종을 Meshy 프리셋으로 갈았다 ──
// 오너 "베는모션을 meshy ai로 해와 차라리". 클립이 통째로 바뀌었으므로 위 수치는
// **옛 클립의 기록**이다. 새 클립을 같은 방법으로 다시 쟀다(평시 URL·요괴 없는 자리·
// 8판, renders/history/v99_wave13/meshy_moves/). 입력 후 경과 초, hot 상승~하강:
//     Attack : [0.133~0.517] [0.583~0.785] [1.017~1.32]   (스윙 3개, 클립 1.800초)
//              ★맨 앞 [0.017~0.083] 은 Idle->Attack 크로스페이드(0.06초)의 자세 점프다.
//                1타와 0.116초 차라 SWING_GAP(0.22) 안에서 같은 번호로 묶인다(옛 판과 같다).
//     Heavy  : [0.775~클립끝 0.98]                        (한 방, 클립 1.100초)
//     Wide   : [0.300~클립끝 0.80]                        (한 방, 클립 0.933초)
//   ★커밋은 **HOT_ON(15.8m/s 환산)을 넘는 구간의 끝**으로 잡는다. hot 하강 엣지가
//     아니다 - 하강은 히스테리시스(HOT_OFF 0.16) 꼬리라 칼이 다 느려질 때까지 안 꺼진다.
//     그 꼬리까지 커밋에 넣으면 Z 1타가 0.51초를 묶는다(옛 판 0.28). 꼬리를 빼는
//     것이 애초에 TAIL_SLACK 을 만든 이유이기도 하다.
//
// ── 2026-08-12 14-베기수정: X=세로 · C=가로 · 투구 폼 제거 ──
// 오너 "x는 세로로베는거고 c는 가로로베는건데 너무길게 만들지말고, 휘두르는모션은
// 야구에서 체인지업하듯이 자세가 이상해". 대본을 다시 짰다(s24 헤더 참고):
//   X = sword_slash 의 **머리 위 내려베기만**(도끼 프리셋 폐기 - 아래 ★)
//   C = sword_slash 의 **앞을 낮게 쓸어 도는 구간만**
//   Z = left_slash 한 테이크 안의 스윙 셋(내려베기 / 횡쓸기 / 되받아 베기)
// 그래서 클립이 짧아졌고 타이밍을 전부 다시 쟀다.
//   측정법은 위와 같다(평시 URL·요괴 없는 자리·6판, mf_commit.mjs).
//   ★단 이번엔 **히스테리시스를 빼고 HOT_ON(fast>0.42) 을 넘는 구간만** 찍었다.
//     커밋의 정의가 그것이라 하강 엣지로는 애초에 잴 수가 없다.
//   증거 = renders/history/v99_wave14/moves_fix/commit_after.json
//     Attack : [0.017~0.117] [0.134~0.283] [0.434~0.567] [0.882~1.051]  (클립 1.133초)
//              ★맨 앞은 Idle->Attack 크로스페이드의 자세 점프다(옛 판과 같은 성질).
//                1타와 0.016초 차라 SWING_GAP(0.22) 안에서 같은 번호로 묶인다.
//     Heavy  : [0.017~0.134] [0.251~0.533]                             (클립 0.633초)
//     Wide   : [0.016~0.166] [0.266~0.467]                             (클립 0.582초)
//              ★X·C 의 맨 앞 구간은 CAST_SETTLE(0.20) 이 판정에서 통째로 가린다.
//                실제 스윙은 0.251 / 0.266 이라 여유가 0.05초 이상 남는다.
//   (옛 판 = Attack [0.135~0.435][0.585~0.752][1.018~1.319] 클립 1.332 ·
//            Heavy [0.800~클립끝] 0.984 · Wide [0.300~클립끝] 0.801)
//
// ★★X 의 타격 구간이 0.567 까지 긴 데는 이유가 있다. **프리셋의 내려베기는
//   칼끝이 몸 뒤를 지난다**(레스트 정면 기준 tipF -0.3~-1.4). makeHitSeg 의 정면
//   부채꼴 게이트가 뒤에 있는 칼을 통째로 버리므로, 내려찍는 구간만 넣으면
//   **스윙 번호는 발급되는데 피해가 0** 이다(실측: 14판 전부 hits 0).
//   칼이 앞으로 넘어오는 구간(소스 f18~f21)까지 타격 구간에 넣어야 벤다.
//   지금 값은 그 구간을 배속 0.55 로 늘려 확보한 것이다(13판 전부 hits 2 · worst 1).
//   ★단 앞으로 너무 많이 끌면 이번엔 **가로로 읽힌다**(칼끝이 좌우로 2.2 이동).
//     소스 f20.2 에서 끊는 게 둘을 다 만족하는 자리다(세로성 1.14 -> 1.78).
//
// ── 2026-08-13 15-모션수제: 베기 3종을 **손으로 짠 키프레임**으로 다시 만들었다 ──
// 오너 "칼 베는거 안고쳐짐 그냥 너가 직접 베는 모션 만들어. 위에서아래로. 옆으로."
// 프리셋 트림을 두 번 기각당해 소스 자체를 버렸다(대본은 blender/s24 의 HAND_SPEC).
// 같은 자(mf_commit.mjs 6판, 평시 URL·요괴 없는 자리)로 다시 쟀다.
//   증거 = renders/history/v99_wave15/handmoves/commit_after.json
//     Attack : [0.167~0.283] [0.583~0.700] [1.000~1.100]   (클립 1.133초. 유령 없음)
//     Heavy  : [0.083~0.099] [0.200~0.316]                  (클립 0.633초)
//     Wide   : [0.233~0.383]                                (클립 0.600초. 유령 없음)
//   ★★**캐스트 첫 프레임 유령이 거의 사라졌다.** 수제 클립은 f0 을 Idle 첫 프레임과
//     **같은 자세**로 박아 두어 크로스페이드가 건너뛸 거리가 구조적으로 0 이다.
//     그래서 14차가 유령을 누르려고 늘렸던 크로스페이드(0.10/0.12/0.16)를 다시
//     짧게(0.06/0.08/0.08 = 13차 이전 값) 되돌릴 수 있었고, **짧게 한 쪽이 더 좋았다**:
//         캐스트 0.12초 안 칼끝 최고속(m/s)   14차 Z 52.6 · X 33.8 · C 46.2
//           15차 긴 페이드(0.10/0.12/0.16)    Z 19.7 · X 20.4 · C 13.6
//           15차 짧은 페이드(0.06/0.08/0.08)  Z 13.0 · X 17.8 · C 15.2
//         그때 swordFast(버스트 문턱 0.55)    Z 0.309 · X 0.502 · C 0.398  = 셋 다 문턱 아래
//         hot 상승 엣지 수(mf_edges 8판)      Z 4 -> **3** (유령 엣지 자체가 없어졌다)
//
// ── 2026-08-13 16-베기근본 (오너 "베는건 여전히 이상해. 간단하잖아 세로로베고 가로로베고") ──
// 15차까지 세 판이 **정지 실루엣·월드 궤적**으로만 판정되어 전부 통과했는데 전부 기각됐다.
// 16차에 처음으로 **게임 카메라 화면**과 **시간축**을 쟀고, 그 자로 대본을 다시 짰다.
// (진단·증거는 renders/history/v99_wave16/blade_audit/ · LOG.md 16-베기근본 절)
// 클립 길이는 셋 다 그대로다(Attack 46장 · Heavy 22장 · Wide 22장). 타격 구간만 옮겨졌다:
//     Attack : 클립 0.267~0.400 / 0.700~0.833 / 1.200~1.300  -> 게임 0.198~0.296 / 0.519~0.617 / 0.889~0.963
//     Heavy  : 클립 0.267~0.400                              -> 게임 0.232~0.348
//     Wide   : 클립 0.267~0.433                              -> 게임 0.222~0.361
//
// ── 2026-08-13 18-X검도 (오너 "칼 베는모션도 검도나 사무라이처럼 위에서 아래로 딱 써는") ──
// X(수면참)만 대본을 다시 짰다(Z·C 는 16차 클립 그대로 = 이 표의 Attack·Wide 도 그대로).
// 검도 문법이라 **한 박자 정지**(게임 0.058초)가 들어가 타격 구간이 통째로 뒤로 밀렸다.
// 같은 자(mf_commit.mjs 4판)로 다시 잰 값 — 증거 renders/history/v99_wave18/moves/
//     Heavy : 게임 0.232~0.348  ->  **0.289~0.401**   (클립 0.700초·게임 0.609초는 그대로)
//   커밋 = "그 스윙의 타격이 끝나는 순간" 이라 0.35 -> **0.40**.
//   ★캐스트 유령이 사라졌다: X 의 hot 창이 두 개(0.083~0.100 + 본 스윙)에서 **하나**가 됐고
//     캐스트 0.12초 안 칼끝 19.6 -> 14.1 m/s · swordFast 0.573 -> **0.352**(버스트 문턱 0.55 아래).
//     같은 파도에서 Idle 칼을 세운 것(18-Idle칼)이 크로스페이드 시작 자세를 바꾼 덕이다.
// ── 2026-08-24 23차 모션재작: 베기 3종 대본을 다시 짰다(blender/s24 MOVES_V23) ──
// 회수·연결이 리본 문턱(칼끝 14.8m/s)을 넘던 유령 hot(Z 회수 [984~1084ms]·C 회수
// [523~589ms])을 대본에서 없앴고, 임팩트 뒤 홀드가 생겨 타격 구간이 조금 움직였다.
// 같은 자(mo_live.mjs 단발, 평시 60fps, 요괴 없는 자리)로 다시 잰 값 —
//   증거 renders/history/v99_wave23/motion/live_after/
//     Attack : hot [6~89(캐스트 몸보정, SWING_GAP 이 1타와 묶는다)] [172~273] [505~606] [857~939]
//     Heavy  : hot [254~354]   (18차 0.289~0.401 → 회수 유령이 빠져 끝이 당겨졌다)
//     Wide   : hot [249~382]
//   커밋 = "그 스윙의 타격이 끝나는 순간" → Heavy 0.40 -> 0.35, Wide 0.37 -> 0.38.
// ── 2026-08-25 26차 X 재작(HEAVY_V26)·Z 봉인(SKILL_Z_ON): X 의 hot 창이 옮겨졌다 ──
// 챔버가 +84 로 높아지고 낙하가 중력 가속(한 장 늦은 hot 진입)이라 창이 뒤로 밀렸다.
// 같은 자(mo_live26.mjs 단발, 평시 URL 로컬 미러, 요괴 없는 자리)로 다시 잰 값 —
//   증거 renders/history/v99_wave26/motion/live_after26b/
//     Heavy : hot [게임 ~300~401ms] (베이크 표 f9~13 = 클립 0.300~0.433 과 궤합.
//             마지막 hot 표본 clipT 0.461 = 게임 0.401초)
//     Wide  : hot [264~392]   (23차 [249~382] 와 표본 간격 안 일치 = 불변 대조군 ✓)
//     Attack: 창 없음(SKILL_Z_ON=false 봉인 실증. 표는 산 채로 둔다)
//   커밋 = "그 스윙의 타격이 끝나는 순간" → Heavy 0.35 -> 0.40 (18차 검도판과 같은 값
//   으로 회귀 — 깊어진 낙하만큼 창이 늦게 닫힌다).
const ATK_COMMIT = { Attack: 0.30, Heavy: 0.40, Wide: 0.38 };
let atkClip = null;                // 지금 도는 공격 클립 이름. 없으면 공격 중이 아니다
let atkStartT = 0;                 // 공격이 시작된 **게임시간**(히트스톱 중에는 안 흐른다)
let atkStruck = false;             // 이번 공격에서 타격 구간(hot)을 한 번이라도 지났나
let atkHitT = -99;                 // 이번 공격에서 **실제로 벤** 마지막 게임시간(-99 = 헛스윙)
let atkStarts = 0;                 // 공격 클립이 **새로 시작된** 횟수(검증용. 입력이 몇 번 나갔나)

// ── 후딜 캔슬 (2026-08-10 9차 재작업. 건틀릿 손맛 1위 격차) ──
// 심사 실측: Z 310~400ms · C 856ms · X 1254ms 발묶임, 그동안 취소 불가.
// 옛 규칙은 조건이 하나였다 — "커밋 경과 + `!enemies.hot`". 그런데 hot 은
// 히스테리시스(켜짐 0.42 / 꺼짐 0.16)라 **베고 난 뒤에도 칼이 느려질 때까지 안 꺼진다.**
// 실측하면 X 는 타격이 954ms 에 끝나는데 hot 꼬리가 300ms 를 더 물고 있었다.
// 그래서 규칙을 셋으로 나눈다(하나라도 참이면 끊을 수 있다):
//   1) 명중 확정 캔슬 — 실제로 벤 뒤 HIT_CANCEL(0.12초). 이게 근접 전투의 리듬이다.
//      "때렸으면 바로 다음 행동"이 되는 순간 연타·치고빠지기가 성립한다.
//   2) 커밋 경과 + 칼이 지금 타격 구간이 아님 — 옛 규칙 그대로(헛스윙 경로).
//   3) 꼬리 상한 — 커밋 + TAIL_SLACK 이 지나면 hot 이 안 꺼져도 끊는다.
//      hot 히스테리시스가 회복 동작까지 물고 늘어지는 것을 막는 안전판이다.
// ★1·3 을 더해도 "휘두르다 마는 그림"은 안 나온다. 셋 다 atkStruck(= 타격 구간을
//   한 번이라도 지났다)을 전제로 하므로, 칼이 나가기 전에는 어떤 경로로도 안 끊긴다.
const HIT_CANCEL = 0.12;
// ★0.06 인 이유: 커밋은 이미 '타격 구간이 끝나는 순간'이라, 그 뒤로 hot 이 아직
//   안 꺼진 건 히스테리시스 꼬리(칼이 느려지는 중)뿐이다. 실측하면 그 꼬리가 X 에서
//   300ms 를 물고 있었다. 0.06 은 "한 프레임 지나침"을 흡수할 만큼만 남긴 값이다.
const TAIL_SLACK = 0.06;
// ★검증 전용 스위치. 'old' 로 두면 9차 이전 규칙(커밋 + !hot 하나)으로 되돌아간다.
//   같은 빌드·같은 측정 방법으로 개선 전/후를 재려고 둔 것이다(게임은 늘 'new').
let cancelMode = 'new';
const ATK_COMMIT_OLD = { Attack: 0.28, Heavy: 0.97, Wide: 0.70 };
// 지금 스윙의 커밋 길이. 3연타는 **단수마다 다르다**(2·3타는 진입점이 스윙 코앞이라 짧다).
function commitNow() {
  if (cancelMode === 'old') return ATK_COMMIT_OLD[atkClip] || 0.28;
  // ★21차. 표가 캐릭터별로 갈린다(궁수 = 쏘기 한 번짜리 표). 검사는 옛 표 그대로다.
  if (atkClip === 'Attack') { const T = atkStepCommit(); return T[comboStep] || T[0]; }
  return ATK_COMMIT[atkClip] || 0.28;
}
// ── 한 방짜리 기술의 캐스트 앞구간 (2026-08-12 13차. 오너 "X 쓸 때 2타가 나가네") ──
// 수면참은 크게 한 번인데 피해가 두 번 들어갔다. 범인은 스윙 모션이 아니라 **몸 보정**이다.
// 실측(평시 URL, 요괴를 세워 놓고 X 20회. renders/history/v99_wave13/xsingle/):
//   캐스트가 시작되는 첫 프레임에 방향 스냅(최대 SNAP_BACK_DEG 110도를 0.09초에)과
//   전진 스텝(STEP_DUR 0.14초)이 **몸을** 옮긴다. 칼은 아직 머리 위에 그대로인데 몸이
//   도니까 칼끝이 월드에서 확 움직이고, 타격 게이트가 보는 값은 |Δ칼끝|/dt 라
//   이게 **64~336 m/s** 로 읽혔다(진짜 내려찍기의 최고 속도가 45~70 이다).
//   그래서 칼을 휘두르기도 전에 타격 구간이 열려 **스윙 번호가 하나 더 발급됐다**:
//     hot 상승 엣지 [0.017] [0.833]  ← 간격 0.82초. enemy.js 의 SWING_GAP(0.22)으로는
//     절대 못 묶는다. 두 번호가 같은 요괴를 각각 한 번씩 때린다 = 데미지 숫자 두 개.
// 그래서 **몸 보정이 끝나기 전에는 판정을 안 연다.** 창의 길이는 추측이 아니라 그 두
// 보정의 길이에서 나온다: max(스냅 0.09, 스텝 0.14) + 한 프레임 여유.
// ★3연타(Z)에는 안 건다. Z 는 1타 타격이 0.069초라 이 창 **안**에 있다(가리면 1타가 사라진다).
//   Z 는 이 떨림이 진짜 1타와 SWING_GAP 안쪽으로 붙어서 어차피 같은 번호로 묶인다.
// ★수면참의 진짜 타격은 0.83초, 횡일섬은 0.56초다. 양쪽 다 여유가 0.13초 넘게 남는다.
const CAST_SETTLE = 0.20;
// 한 방짜리 기술(수면참·횡일섬)인가. 3연타와 규칙이 갈리는 자리는 전부 이걸 본다.
function isOneShotClip() { return atkClip === 'Heavy' || atkClip === 'Wide'; }
// 지금 몸 보정 구간인가(= 칼끝 속도가 스윙이 아니라 몸의 이동을 재고 있는 구간)
function castSettling(now) {
  return attacking && isOneShotClip() && (now - atkStartT) < CAST_SETTLE;
}
function canCancelAttack(now) {
  if (!atkClip) return false;
  if (!atkStruck) return false;              // 아직 한 번도 안 휘둘렀으면 커밋 유지
  const cm = commitNow();
  const since = now - atkStartT;
  if (cancelMode === 'old') return since >= cm && !enemies.hot;
  if (atkHitT > -90 && now - atkHitT >= HIT_CANCEL) return true;          // 1
  if (since >= cm && !enemies.hot) return true;                          // 2
  if (since >= cm + TAIL_SLACK) return true;                             // 3
  return false;
}

// ── 대시(퀵스텝) — 2026-08-10 9차 신설 ──
// 건틀릿 심사 결론: "회피기 부재 + 후딜 루트는 근접 전투의 리듬이 성립할 수 없는
// 구조적 결함". 보스 장판(내려찍기 반경 4m, 예고 1.2초)을 **물리적으로** 벗어날
// 수단이 걷기(1.8m/s)·달리기(3.2m/s)뿐이라 11트라이 0킬이 나왔다.
//
// 배치: **이동키를 누른 채 Space**. 아무것도 안 누르고 Space 면 예전대로 점프다.
//   ★새 키를 안 만든 이유: 방향키+Shift(달리기)+Z/X/C 로 왼손이 이미 꽉 차 있다.
//     점프는 이 게임에서 이동 수단이 아니라 몸짓이라(높이 0.95m) 자리를 내줄 수 있다.
// 수치의 근거 — 전부 이 레포의 실측값에서 역산했다:
//   거리 3.5m : 내려찍기 반경 4.0m. 보스 앞 교전 거리 2.8m 에서 한 번이면 6.3m 로
//               벗어난다(예고 1.2초 안에 여유 2.3m). 후려치기(부채꼴 3.4m)도 한 번이면 빠진다.
//   시간 0.18s: 달리기 3.2m/s 의 6배 속도. 예고 1.2초 안에 두 번도 넣을 수 있다(쿨 1.2s 라
//               연속은 못 하지만, 예고를 보고 반응할 시간이 1초 남는다).
//   무적 0.20s: 대시 구간(0.18)보다 0.02 길다. 나가는 순간부터 착지까지 다 덮는다.
//               ★잡몹 타격은 enemy.js 가 자기 안에서 damagePlayer 를 직접 부르므로
//                 창구(setIframe)가 있어야 먹는다. 없는 빌드에서는 조용히 건너뛰고
//                 **자리 이동으로만** 피한다(보스 장판은 명중 순간 좌표를 다시 재므로
//                 창구 없이도 100% 피해진다 — 그게 이번 파도의 증명 대상이다).
//   쿨 1.2s   : 후려치기 경직 1.30초보다 짧다. "한 대 피하고 붙어서 한 대"가 성립한다.
// ── ★회피 스위치 (17차. 오너: 「회피 스킬 일단 없애줘 스페이스바는 그냥 점프여」) ──
// **로직은 한 줄도 안 지운다.** 이 한 줄이 꺼짐이고, 되살리는 것도 이 한 줄이다(true).
//   꺼지면 같이 죽는 것: 대시 이동 · 무적 0.20s · 후딜 캔슬로 나가는 회피 · 쿨 1.2s ·
//   계기판 회피 칸(아래 mountSpaceChip 이 그 자리에 점프 칸을 세운다).
// ★무적을 전제로 쓰인 자리 둘은 **죽어도 안 깨진다** - 둘 다 "무적이 아니다"로 흐른다:
//   (가) 보스 피해 통로의 `gameT < dashIfUntil` (dashIfUntil 이 -99 로 남는다)
//   (나) enemies.setIframe (호출 자체가 안 일어난다. enemy.js 는 손대지 않는다)
// ★★밸런스: 보스 판정(boss.js tryLand)은 **x·z 만 본다.** 점프로는 어떤 패턴도 안 피해진다.
//   회피가 메우던 구멍 둘이 다시 열린다 - ①칼을 휘두르는 중(최대 1.19초 묶인다)
//   ②내려찍기 원(반경 3.6m) 한복판에 서 있었을 때. 나머지 셋은 boss.js 가 "제일 느린
//   걸음으로도 예고 안에 빠져나올 수 있게" 잡아 둔 값이라 회피 없이도 성립한다.
const DASH_ON = false;
// ★26차: Z(기본 3연타) 봉인 스위치 SKILL_Z_ON 은 파일 앞(조작 안내 접는 자리 위)에
//   있다 — 그 자리가 top-level 에서 먼저 실행돼 여기 두면 TDZ 다. 문법은 DASH_ON 과 같다.
const DASH_DIST = 3.5, DASH_DUR = 0.18, DASH_IFRAME = 0.20, DASH_CD = 1.2;
let dashLeft = 0, dashDX = 0, dashDZ = 0, dashGone = 0;
let dashReadyT = -99;              // 이 게임시간이 지나면 다시 쓸 수 있다
let dashIfUntil = -99;             // 무적 종료 게임시간(보스 경로는 여기서 직접 막는다)
const dashEase = t => 1 - (1 - t) * (1 - t) * (1 - t);   // ease-out cubic. 튀어나갔다 멎는다
function dashReady(now) { return dashLeft <= 0 && now >= dashReadyT; }

// ---------------------------------------------------------------- 전진 스텝 (2차 QA S3)
// "스냅 반경 2.6인데 2.8에서 적중이 급락한다."
// 실측하면 원인이 둘로 갈린다:
//   1) 스냅이 2.6 밖을 아예 안 잡는다  -> 반경을 3.0 으로 올린다(아래 SNAP_R)
//   2) 잡아 돌려도 **칼이 안 닿는다**. 칼날 선분과 요괴 캡슐로 잰 실제 사거리는
//      중심간 1.88m 다(2.0m 에서 이미 0.12m 모자란다).
// 그래서 각도만 고쳐선 안 되고 거리도 조금 좁혀야 한다. 공격 시작에 짧은 전진을 섞는다.
// ★거리에 비례해 준다. 이미 붙어 있는 놈에게 또 밀면 그게 "빨려 들어간다"로 읽힌다.
//   STEP_KEEP 1.75m 는 실측 사거리(1.88m) 바로 안쪽이라, 이미 닿는 거리면 스텝이 0 이다.
// ★9차: 스냅 반경 = **판정 리치**(3.2m)로 맞춘다. 둘이 어긋나면 "몸은 돌았는데 안 닿는"
//   (반경 > 리치) 또는 "닿는데 안 돌아보는"(반경 < 리치) 구멍이 생긴다. 한 값에서 나온다.
const SNAP_R = 3.2;
// ── 등 뒤로는 안 돌아본다 (9차) ──
// 심사의 "밀착하면 등 뒤도 베인다"의 **진짜 기전**이 여기였다(실측으로 잡았다):
//   스냅이 몸을 0.09초에 걸쳐 돌리는데 3연타 1타의 타격은 0.069초에 들어간다.
//   즉 **몸이 아직 등을 보인 상태에서 판정이 도는 프레임**이 있고, 정확히 180도
//   뒤의 요괴가 8회 중 7회 베였다(backhit.json).
// 정면 부채꼴 게이트(makeHitSeg)가 그 프레임을 잘라내지만, enemy.js 가 직전 프레임
// 선분과 이번 프레임 선분 사이를 보간하기 때문에 급회전 중에는 한 프레임분(최대 33도)이
// 새어 나온다. 그래서 **애초에 그런 회전을 안 만든다** — 이 각도보다 뒤에 있는 표적에는
// 스냅도 전진 스텝도 걸지 않는다(그 자리에서 헛스윙이 나는 게 정직하다).
const SNAP_BACK_DEG = 110;
// ★STEP_KEEP 도 리치를 따라 올린다(1.75 -> 2.9). 옛 값이면 3.2m 표적마다 0.40m 를
//   전부 밀어붙여서, 이미 닿는 거리인데도 매번 한 발 들어가 "빨려 들어간다"가 된다.
//   2.9 는 리치(3.2) 바로 안쪽이라 정말 아슬아슬한 거리에서만 최대 0.30m 붙는다.
const STEP_MAX = 0.40, STEP_KEEP = 2.90, STEP_DUR = 0.14;
let stepLeft = 0, stepDist = 0;
// ── 감속 코스트 (17차) ──
// 키를 뗀 뒤 남은 속도를 흘려보내는 시간. 0.16초면 반 걸음(약 0.29m) 미끄러지고 선다.
// 더 길면 조작이 미끄럽다고 읽히고, 0.10 아래면 여전히 스냅으로 보인다.
const COAST_T = 0.16;
let coastVX = 0, coastVZ = 0, coastLeft = 0, coastRun = false;
const stepEase = t => 1 - (1 - t) * (1 - t);   // ease-out. 앞이 빠르고 끝에서 멎는다 = 한 발 내딛는 그림
function stepDistFor(d) {
  return Math.max(0, Math.min(STEP_MAX, d - STEP_KEEP));
}
// 공격 입력 순간의 방향 스냅. 등 뒤(SNAP_BACK_DEG 밖) 표적은 아예 건너뛴다.
// ★세 공격 함수가 **같은 함수**를 지난다. 한 군데만 고치면 규칙이 갈라진다.
function snapTarget() {
  const t = enemies.nearestTo(root.position.x, root.position.z, SNAP_R);
  if (!t) return null;
  let d = t.yaw - root.rotation.y;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  if (Math.abs(d) > SNAP_BACK_DEG * Math.PI / 180) return null;
  return enemies.snapFacing(root, SNAP_R);
}
// ── ★활 조준 스냅 (21차) ──
// snapTarget 과 **같은 규칙**이고 반경만 다르다(SNAP_R 3.2 -> BOW_AIM_R 13).
// ★함수를 따로 판 이유: snapTarget 의 반경을 인자로 열면 칼 세 자리(Z·X·C)가 전부
//   그 인자를 지나가게 되고, 언젠가 한 곳만 다른 값을 넣는다. 갈래를 붙이는 게 아니라
//   **부르는 쪽을 가르는** 편이 안전하다.
// ★등 뒤 게이트(SNAP_BACK_DEG)는 그대로 쓴다. 활이라고 뒤를 돌아 쏘면 그건 조준이
//   아니라 자동 조준이 몸을 조종하는 것이다.
function snapTargetBow() {
  const t = enemies.nearestTo(root.position.x, root.position.z, BOW_AIM_R);
  if (!t) return null;
  let d = t.yaw - root.rotation.y;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  if (Math.abs(d) > SNAP_BACK_DEG * Math.PI / 180) return null;
  return enemies.snapFacing(root, BOW_AIM_R);
}
// t 는 enemies.snapFacing 이 돌려준 표적(없으면 null). 클립이 실제로 시작되는 자리에서만 부른다.
function startStep(t) {
  stepLeft = 0; stepDist = 0;
  if (!t) return;
  const s = stepDistFor(t.d);
  if (s < 0.02) return;
  stepDist = s; stepLeft = STEP_DUR;
}
// 점프. 수직 이동은 여기서 만들고 클립은 다리 모양만 담당한다.
// 높이 h 와 중력 g 로 초속을 정하면 체공시간이 2*v0/g 로 딱 떨어진다.
const JUMP_H = 0.95, GRAV = 18.0;
const JUMP_V0 = Math.sqrt(2 * GRAV * JUMP_H);
let vy = 0, grounded = true, jumping = false;

// ── 지금 눌린 이동키를 카메라 기준 방향으로 ──
// ★루프와 대시가 **같은 함수**를 지난다. 두 벌이 되면 "화면에서 위로 갔는데
//   대시는 옆으로 나가는" 어긋남이 반드시 생긴다.
const _mvDir = new THREE.Vector3();
function moveDirFromKeys() {
  let mx = 0, mz = 0;
  if (keys.KeyW || keys.ArrowUp) mz -= 1;
  if (keys.KeyS || keys.ArrowDown) mz += 1;
  if (keys.KeyA || keys.ArrowLeft) mx -= 1;
  if (keys.KeyD || keys.ArrowRight) mx += 1;
  if (!mx && !mz) return null;
  // yaw 는 고정이지만 상수로 박지 않는다(카메라 규칙이 한 군데서만 정해져야 한다)
  _mvDir.set(Math.sin(yaw) * mz + Math.cos(yaw) * mx, 0,
             Math.cos(yaw) * mz - Math.sin(yaw) * mx).normalize();
  return _mvDir;
}

// Space = 이동키를 누르고 있으면 대시, 아니면 점프. ★지금은 스위치가 꺼져 있어(DASH_ON)
// 첫 줄에서 바로 false 를 돌려준다 = 부르는 쪽은 전부 "회피가 안 나갔다"로 흐른다.
function tryDash() {
  if (!DASH_ON) return false;                  // ★17차 오너 지시. 갈림은 이 한 줄뿐이다
  if (isCleared() || preview.on) return false;
  if (enemies.dead) return false;
  if (!grounded) return false;                 // 공중 대시는 없다(점프와 구분이 안 된다)
  const now = gameT;
  if (attacking && !canCancelAttack(now)) { bufferInput('dash'); return false; }
  if (!dashReady(now)) { deny('dash'); return false; }
  const d = moveDirFromKeys();
  if (!d) return false;                        // 방향이 없으면 대시가 아니다(점프로 간다)
  // 공격 중이었으면 회복 동작을 끊고 나간다(위 canCancelAttack 을 이미 통과했다)
  if (attacking) { attacking = false; heavy = false; atkClip = null; }
  dashDX = d.x; dashDZ = d.z;
  dashLeft = DASH_DUR; dashGone = 0;
  dashReadyT = now + DASH_CD;
  dashIfUntil = now + DASH_IFRAME;
  // 잡몹 타격은 enemy.js 안에서 직접 들어간다. 창구가 있으면 거기에 무적을 심는다.
  // ★없는 빌드에서도 게임은 그대로 돈다(자리 이동만으로 피한다).
  if (typeof enemies.setIframe === 'function') enemies.setIframe(DASH_IFRAME);
  root.rotation.y = Math.atan2(d.x, d.z);      // 나가는 쪽을 본다(옆으로 미끄러지면 안 읽힌다)
  clearBuffer();
  sfx.dash();
  // 달리기 클립을 빠르게 돌려 "한 발 크게 내딛는" 그림을 만든다.
  // ★회피 전용 클립은 없다(모션은 다른 파일의 몫이다). 여기서는 있는 것으로 읽히게만 한다.
  // ★★timeScale 을 덮어쓰기 전에 **원래 값을 적어 둔다.** 걷기/달리기 재생속도는
  //   캐릭터마다 CHAR_CFG 에서 한 번 박아 넣는 값이라(activateChar), 1 로 되돌리면
  //   그 뒤 달리기가 통째로 느려진다(캐릭터를 바꿔도 안 돌아온다).
  const a = actions.Run || actions.Walk;
  if (a) {
    if (dashTsSaved === null) { dashTsAct = a; dashTsSaved = a.timeScale; }
    _lowHist.length = 0;
    a.reset(); a.timeScale = dashTsSaved * 1.9; a.play();
    if (current && current !== a) current.crossFadeTo(a, 0.04, false);
    current = a;
  }
  return true;
}
let dashTsAct = null, dashTsSaved = null;   // 대시가 잠시 덮어쓴 재생속도의 원본
function restoreDashTs() {
  if (dashTsAct && dashTsSaved !== null) dashTsAct.timeScale = dashTsSaved;
  dashTsAct = null; dashTsSaved = null;
}

function tryJump() {
  if (!grounded || attacking) return;
  if (isCleared()) return;         // 층 돌파 뒤에는 안 받는다
  vy = JUMP_V0;
  grounded = false;
  jumping = true;
  const a = actions.Jump;
  if (a) {
    _lowHist.length = 0;
    a.reset(); a.setEffectiveTimeScale(1); a.play();
    // 웅크림 구간은 건너뛴다. 게임은 누르는 즉시 떠오르므로 그 사이 공중에서 웅크리게 된다.
    a.time = (curCfg.jump || DEF_CFG.jump).start;
    if (current && current !== a) current.crossFadeTo(a, 0.05, false);
    current = a;
  }
}

const clock = new THREE.Clock();
const loader = new GLTFLoader();
// 칼날이 손 본 로컬에서 어느 쪽으로 뻗는지 "실측"한다.
// 예전에는 손 본의 +Y 를 칼날이라 가정했는데 실제 그립은 거의 반대쪽(-Y 계열)
// 이라 궤적이 칼과 148 도 어긋난 허공에 그려지고 있었다. 칼 정점(손 본에
// 100% 웨이트)들을 바인드 로컬로 되돌려 직접 재면 그립을 바꿔도 따라온다.
const bladeA = new THREE.Vector3(), bladeB = new THREE.Vector3();
const bladePath = [];      // 휜 칼날 중심선(손 본 로컬). 리본이 이걸 따라 감는다
let bladeOK = false;
// ★glTF 는 머티리얼마다 메시를 쪼갠다(SW_baekah_1,_2,...). 한 자루가 여러 메시라
// 배열로 받아 전부 훑어야 칼끝을 놓치지 않는다.
// ★★22차 멀티. 알맹이를 **순수 함수**로 뺐다 - 남의 아바타(원격)도 같은 자로 재야
//   하는데, 옛 판은 전역 bladeA/bladeB/bladePath 에 바로 써 넣어서 로컬 하나만
//   잴 수 있었다. 여기서 재는 값은 **손 본 로컬 좌표**라 같은 glb 면 사람마다 같다
//   (월드로 옮기는 건 그 사람 손 본의 matrixWorld 다 = 스케일·위치가 저절로 물린다).
//   실패하면 null 을 돌려준다.
function measureBladeOf(meshes) {
  const v = new THREE.Vector3();
  const pts = [];
  for (const mesh of meshes) {
    if (!mesh.skeleton) continue;
    const hi = mesh.skeleton.bones.findIndex(b => /r[_ ]hand/i.test(b.name));
    if (hi < 0) continue;
    const ibm = mesh.skeleton.boneInverses[hi];
    const pos = mesh.geometry.attributes.position;
    const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
    for (let i = 0; i < pos.count; i++) {
      let w = 0;
      for (let k = 0; k < 4; k++) if (si.getComponent(i, k) === hi) w += sw.getComponent(i, k);
      if (w > 0.99) pts.push(v.fromBufferAttribute(pos, i).applyMatrix4(ibm).clone());
    }
  }
  if (pts.length < 20) { if (DEV) console.warn('칼 정점 못 찾음'); return null; }
  let far = pts[0];
  for (const p of pts) if (p.lengthSq() > far.lengthSq()) far = p;
  const dir = far.clone().normalize();
  let pmax = 0;
  for (const p of pts) pmax = Math.max(pmax, p.dot(dir));
  const outA = dir.clone().multiplyScalar(pmax * 0.18);   // 코등이 조금 앞
  const outB = dir.clone().multiplyScalar(pmax * 0.98);   // 칼끝
  // ★칼이 초승달로 휘어서 직선 축만으로는 리본이 날에서 떠버린다.
  // 정점을 날 방향으로 구간별로 묶어 평균을 내면 **휜 중심선**이 나온다.
  const NSEG = 16;
  const bins = [];
  for (let i = 0; i < NSEG; i++) bins.push({ s: new THREE.Vector3(), n: 0 });
  for (const p of pts) {
    const d0 = p.dot(dir);
    const t = (d0 - pmax * 0.16) / (pmax * 0.84);
    if (t < 0 || t > 1) continue;
    const i = Math.min(NSEG - 1, Math.max(0, Math.floor(t * NSEG)));
    bins[i].s.add(p); bins[i].n++;
  }
  const path = [];
  for (const b of bins) if (b.n > 2) path.push(b.s.divideScalar(b.n));
  // ★평시 콘솔은 비어 있어야 한다(건틀릿 연출UI S10 "개발 흔적"). ?dev 에서만 남긴다.
  if (DEV) console.log('[blade]', meshes[0].name, dir.toArray().map(n => n.toFixed(3)).join(','), 'len', pmax.toFixed(2));
  return { a: outA, b: outB, path, len: pmax };
}

// 로컬 플레이어 통로(옛 이름 그대로). 전역 셋을 여기서만 쓴다.
function measureBlade(meshes) {
  bladeOK = false;
  const m = measureBladeOf(meshes);
  if (!m) return;
  bladeA.copy(m.a); bladeB.copy(m.b);
  bladePath.length = 0;
  for (const q of m.path) bladePath.push(q);
  bladeOK = true;
}

// ---------- 칼 교체 ----------
// 7자루를 전부 glb 에 넣고 visible 만 토글한다(자루당 수백 삼각형).
// 칼마다 길이/실루엣이 달라서 바꿀 때마다 칼날 축을 다시 재야 궤적이 맞는다.
const SWORDS = [
  { key: 'nokseun', name: '녹슨 칼', el: 'plain' },     // 봉인칼 = 평범한 검기만
  { key: 'baekah', name: '백아', el: 'water' },
  { key: 'hongyeom', name: '홍염', el: 'fire' },
  { key: 'seorikkot', name: '서리꽃', el: 'ice' },
  { key: 'imugi', name: '이무기 비늘', el: 'poison' },
  { key: 'bawigyeol', name: '바위결', el: 'earth' },
  { key: 'eoduk', name: '어둑', el: 'dark' },
];
const swordMesh = {};
// ★시작 칼 = 1번 슬롯(오너 제공 new_sword 흑요석 대검, 2026-08-12 오너 지시)
let swordIdx = 0;

// ---------------------------------------------------------------- 자체발광 칼날
// 레퍼런스 Red_Tessaiga 를 픽셀로 실측한 결과(칼폭 120px 가로 단면):
//   · 색상이 355~359 도에 **고정**돼 있다. 어디에도 주황으로 안 간다.
//   · 명도는 0.63~0.82 로 거의 안 변하고, 음영이 전부 **채도**로 진다.
//     밝은 심 S 0.44 <-> 어두운 결 S 0.76. 금속 칼(하이라이트=밝기)과 정반대다.
//   · 실루엣 바로 안쪽이 가장 진하고(S 0.72, V 0.63) 그게 테두리선 역할을 한다.
//   · 바깥 후광은 칼폭의 10~15% 로 **아주 좁다**. 28px 떨어지면 이미 원래 하늘색이라
//     화면 전체 블룸이 아니라 실루엣에 붙은 얇은 띠다. 칼끝만 조금 더(25px) 번진다.
// 그래서 구현은 (1) 채도 계단 자체발광 + (2) 뒤집힌 껍질 2겹 가산 후광 이다.
const _sc = new THREE.Color();
const LIN = h => { _sc.setStyle('#' + h, THREE.SRGBColorSpace); return [_sc.r, _sc.g, _sc.b]; };
const GLOW = {
  fire: {
    tones: ['D17677', 'CF666C', 'C7575D', 'BA343D', 'A12D3B'],   // 밝은 심 -> 어두운 결
    vein: 'A12D3B', core: 'D17677',
    halo: ['5E100C', '2E0808'],       // 하늘색을 빼고 남은 순수 가산분(실측)
    out: [0.06, 0.14],                // 칼폭 대비 껍질 두께
  },
};

function bladeGlowMat(g, ax) {
  const m = new THREE.MeshBasicMaterial({ color: 0xffffff });
  m.userData.u = { uT: { value: 0 } };
  m.onBeforeCompile = sh => {
    sh.uniforms.uT = m.userData.u.uT;
    sh.uniforms.uCen = { value: ax.cen };
    sh.uniforms.uLen = { value: ax.len };     // 길이 방향 단위벡터 / 반길이
    sh.uniforms.uWid = { value: ax.wid };     // 폭 방향 단위벡터 / 반폭
    g.tones.forEach((h, i) => { sh.uniforms['uC' + i] = { value: new THREE.Vector3(...LIN(h)) }; });
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>',
        '#include <common>\nvarying vec3 vLoc; varying vec3 vN; varying vec3 vV;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n  vLoc = position;')
      .replace('#include <project_vertex>',
        '#include <project_vertex>\n  vN = normalize(normalMatrix * objectNormal);'
        + '\n  vV = normalize(-mvPosition.xyz);');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>',
        '#include <common>\nuniform float uT; uniform vec3 uC0,uC1,uC2,uC3,uC4;'
        + '\nuniform vec3 uCen; uniform vec4 uLen; uniform vec4 uWid;'
        + '\nvarying vec3 vLoc; varying vec3 vN; varying vec3 vV;')
      .replace('#include <opaque_fragment>', [
        // ★칼은 캐릭터 메시에 병합돼 있어서 position 이 칼 기준이 아니다.
        // 칼 정점으로 주축을 뽑아 넘겨받은 축으로 (길이, 폭) 좌표를 만든다.
        // 이걸 안 하면 결이 칼을 **가로질러** 그어진다(실제로 그랬다).
        'vec3 d = vLoc - uCen;',
        'float al = dot(d, uLen.xyz) / uLen.w;',        // -1(자루) ~ +1(칼끝)
        'float u  = dot(d, uWid.xyz) / uWid.w;',        // -1(날) ~ +1(등)
        // 레퍼런스 구조: 가운데보다 살짝 날 쪽에 밝은 심, 그 옆으로 어두운 결,
        // 양 끝(실루엣)이 가장 진하다. 명도는 그대로 두고 채도만 오르내린다.
        // 밝은 심은 **좁은 줄기 하나**다. 가운데를 넓게 밝히면 연분홍 수박이 된다
        // (실측: 그렇게 했더니 채도 중앙값 0.45, 레퍼런스는 0.59).
        'float t = smoothstep(0.06, 0.86, abs(u + 0.10));',
        'float vein = sin(al * 9.0 + u * 2.4) * 0.5 + 0.5;',
        'vein *= sin(al * 3.1 + 0.7) * 0.5 + 0.5;',
        't += vein * 0.24 - 0.03;',
        't += sin(uT * 0.5 + al * 2.0) * 0.035;',       // 아주 느린 흐름. 번쩍이면 안 된다
        // 실루엣 바로 안쪽이 제일 진한 테두리(실측 S 0.72 / V 0.63)
        'float fr = 1.0 - abs(dot(normalize(vN), normalize(vV)));',
        't = mix(t, 1.05, smoothstep(0.52, 0.94, fr));',
        't = clamp(t, 0.0, 1.0);',
        // 5 단 계단(셀). 명도가 아니라 **채도**가 오르는 색들이다.
        'vec3 c = t < 0.10 ? uC0 : t < 0.26 ? uC1 : t < 0.52 ? uC2 : t < 0.80 ? uC3 : uC4;',
        'gl_FragColor = vec4(c, 1.0);',
      ].join('\n'));
  };
  return m;
}

function bladeAxes(geom) {
  // 칼 정점의 주축(PCA). 가장 긴 축 = 칼 길이, 그 다음 = 칼 폭.
  const p = geom.attributes.position, n = p.count;
  const cen = new THREE.Vector3();
  for (let i = 0; i < n; i++) cen.x += p.getX(i), cen.y += p.getY(i), cen.z += p.getZ(i);
  cen.divideScalar(n);
  const cov = [0, 0, 0, 0, 0, 0, 0, 0, 0];
  const d = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    d.set(p.getX(i) - cen.x, p.getY(i) - cen.y, p.getZ(i) - cen.z);
    const a = [d.x, d.y, d.z];
    for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) cov[r * 3 + c] += a[r] * a[c];
  }
  const mul = (M, v) => new THREE.Vector3(
    M[0] * v.x + M[1] * v.y + M[2] * v.z,
    M[3] * v.x + M[4] * v.y + M[5] * v.z,
    M[6] * v.x + M[7] * v.y + M[8] * v.z);
  const power = M => {
    let v = new THREE.Vector3(0.53, 0.31, 0.79).normalize();
    for (let k = 0; k < 60; k++) { v = mul(M, v); if (v.length() < 1e-12) break; v.normalize(); }
    return v;
  };
  const e0 = power(cov);
  const lam = mul(cov, e0).dot(e0);
  const cov2 = cov.slice();
  const a0 = [e0.x, e0.y, e0.z];
  for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) cov2[r * 3 + c] -= lam * a0[r] * a0[c];
  const e1 = power(cov2);
  // 반길이/반폭: 각 축으로 투영한 최대 절댓값
  let hl = 0, hw = 0;
  for (let i = 0; i < n; i++) {
    d.set(p.getX(i) - cen.x, p.getY(i) - cen.y, p.getZ(i) - cen.z);
    hl = Math.max(hl, Math.abs(d.dot(e0)));
    hw = Math.max(hw, Math.abs(d.dot(e1)));
  }
  return {
    cen,
    len: new THREE.Vector4(e0.x, e0.y, e0.z, hl || 1),
    wid: new THREE.Vector4(e1.x, e1.y, e1.z, hw || 1),
    width: hw * 2,
  };
}

function flatGlowMat(hex) {
  // 결/등줄기처럼 이미 형상으로 갈라져 있는 부분은 같은 팔레트의 한 단으로 칠한다
  const m = new THREE.MeshBasicMaterial();
  m.color.setStyle('#' + hex, THREE.SRGBColorSpace);
  return m;
}

function shellMat(hex, outset) {
  // 뒤집힌 껍질: 앞면을 버리고 뒷면만 그리면 실루엣 밖으로 삐져나온 부분만 남는다.
  // = 화면 전체 블룸이 아니라 칼에 붙은 얇은 후광. 실측한 좁은 띠와 맞다.
  const m = new THREE.MeshBasicMaterial({
    color: new THREE.Color().setStyle('#' + hex, THREE.SRGBColorSpace),
    side: THREE.BackSide, blending: THREE.AdditiveBlending,
    depthWrite: false, transparent: true,
  });
  m.onBeforeCompile = sh => {
    sh.uniforms.uOut = { value: outset };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uOut;\nattribute vec3 aSmooth;')
      // ★법선이 갈라진(하드 에지) 메시라 그냥 normal 로 밀면 모서리가 벌어진다.
      // 같은 위치의 법선을 평균낸 aSmooth 로 밀어야 껍질이 안 찢어진다.
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n  transformed += aSmooth * uOut;');
  };
  return m;
}

function smoothNormals(geom) {
  if (geom.getAttribute('aSmooth')) return;
  const p = geom.attributes.position, n = geom.attributes.normal;
  const map = new Map();
  const key = i => (Math.round(p.getX(i) * 8192) + ',' + Math.round(p.getY(i) * 8192)
    + ',' + Math.round(p.getZ(i) * 8192));
  for (let i = 0; i < p.count; i++) {
    const k = key(i); let e = map.get(k);
    if (!e) { e = [0, 0, 0]; map.set(k, e); }
    e[0] += n.getX(i); e[1] += n.getY(i); e[2] += n.getZ(i);
  }
  const out = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) {
    const e = map.get(key(i));
    const l = Math.hypot(e[0], e[1], e[2]) || 1;
    out[i * 3] = e[0] / l; out[i * 3 + 1] = e[1] / l; out[i * 3 + 2] = e[2] / l;
  }
  geom.setAttribute('aSmooth', new THREE.BufferAttribute(out, 3));
}

const glowMats = [];
const glowDone = new Set();
function setupGlow(key, g) {
  if (glowDone.has(key)) return;      // 캐릭터를 오갈 때 껍질이 겹겹이 쌓인다
  glowDone.add(key);
  const parts = swordMesh[key] || [];
  const blade = parts.find(o => o.userData.mn.startsWith('bd_'));
  if (!blade) return;
  const ax = bladeAxes(blade.geometry);
  const w = ax.width;
  for (const o of parts) {
    const mn = o.userData.mn;
    if (mn.startsWith('bd_') || mn.startsWith('bv_')) {
      const m = bladeGlowMat(g, ax); o.material = m; glowMats.push(m);
    } else if (mn.startsWith('ht_')) {
      o.material = flatGlowMat(g.vein);        // 빗금 = 어두운 결
    } else if (mn.startsWith('sp_')) {
      o.material = flatGlowMat(g.core);        // 등줄기 잉걸 = 밝은 심
    }
  }
  smoothNormals(blade.geometry);
  g.out.forEach((f, i) => {
    const sh = new THREE.SkinnedMesh(blade.geometry, shellMat(g.halo[i], w * f));
    sh.name = 'GLOWSHELL_' + key + i;
    sh.bind(blade.skeleton, blade.bindMatrix);
    sh.frustumCulled = false;
    sh.renderOrder = 2 + i;
    blade.add(sh);
  });
}
const swordEl = document.getElementById('sword');
function equipSword(i) {
  if (!SWORDS[i] || !swordMesh[SWORDS[i].key]) return;
  swordIdx = i;
  setElement(SWORDS[i].el);
  for (const k in swordMesh) for (const m of swordMesh[k]) m.visible = (k === SWORDS[i].key);
  measureBlade(swordMesh[SWORDS[i].key]);
  trailBuf.length = 0; spray.length = 0;      // 이전 칼의 궤적/조각이 남으면 어색하다
  if (swordEl) {
    // ★번호 접두사('2. 백아')를 뺐다(건틀릿 연출UI S4). 그 숫자는 **내부 목록 순서**라
    //   플레이어에게 아무 뜻이 없다. ui.js 가 화면에서 떼어내던 것을 원본에서 없앤다.
    // ★불투명도 0.45 로 흐려지는 연출도 뺐다. 이름이 안 읽혔다는 판정이 나와서
    //   ui.js 가 opacity:1 로 눌러 두고 있었다(= 연출은 이미 안 먹고 있었다).
    //   "방금 바꿨다"는 신호가 필요하면 opacity 말고 다른 채널로 다시 붙일 것.
    swordEl.textContent = SWORDS[i].name;
  }
}

// ?char=archer 로 캐릭터를 갈아끼운다. Meshy 로 받은 모델을 붙일 때 씀.
// ---------------------------------------------------------------- 캐릭터 로드/교체
// 여러 캐릭터를 **동시에 올려두고** 활성 하나만 보여준다.
// 전역(model/mixer/actions/handBone/...)은 '지금 활성인 캐릭터'를 가리키는
// 포인터로 쓰고, 교체할 때 통째로 갈아끼운다.
// footBones/swordMesh 는 const 라 재대입이 안 되므로 내용만 비우고 다시 채운다.
const CHARS = {};
// 캐릭터 명단. 여기에 이름만 추가하면 F 키 순환에 들어간다(web/<이름>.glb).
// 맨 앞이 시작 캐릭터다.
// ★basic 은 목록에서 뺐다(2026-08-10 QA). Attack/Jump 클립이 없어 Z·Space 를 눌러도
//   아무 일이 안 일어나 게임이 멈춘 것처럼 보인다. glb 와 CHAR_CFG 항목은 그대로 두었으니
//   개발용으로 되살릴 때는 여기에 이름만 다시 넣으면 된다:  'basic'
// ★2026-08-10 2차 QA(S4). **평시에는 한 명만 쓴다.**
//   병사는 2차대전 철모, 탱커는 로마식 망토라 한국 요괴 세계관을 정면으로 깬다.
//   지우지는 않는다(모션 이식·리깅 검증에 계속 쓴다). ?dev 로 열면 로스터가 다 뜨고
//   F 순환도 그때만 돈다. 평시에 F 는 아무 일도 안 한다(안내에도 안 나온다).
//   부수효과: 평시 로딩이 glb 여러 개 -> 1개다(첫 화면이 그만큼 빨리 뜬다).
// ★2026-08-11 오너 지시로 **시작 캐릭터를 basic2 로 바꿨다**(알몸 베이스. 옷은 나중).
//   basic2 는 이제 kensa 와 같은 구성이다 - 칼 7자루(SW_*) + 클립 7종.
//   kensa 는 지우지 않고 ?dev 로스터에 남긴다(모션 원본이자 비교 기준이다).
// ★2026-08-19 홈화면(home.js)이 생겼다. 평시에도 **?char= 로 고른 하나**는 목록에 넣는다.
//   목록 길이는 여전히 1 이라 "평시 로딩 glb 한 개" 라는 성질은 안 깨진다.
//   아는 이름만 받는다(오타·경로 주입이면 조용히 시작 캐릭터로 돌아간다).
//   ?dev 는 예전대로 로스터 전체이고 F 순환도 그때만 돈다.
const CHAR_ALL = ['basic2', 'kensa', 'slayer', 'tank', 'archer', 'soldier'];
const CHAR_WANT = (new URLSearchParams(location.search).get('char') || '').toLowerCase();
const CHAR_LIST = DEV ? CHAR_ALL : [CHAR_ALL.includes(CHAR_WANT) ? CHAR_WANT : CHAR_ALL[0]];
// ★라벨에 '(구)' 같은 개발 표기를 넣지 않는다(S5). 평시 화면에 새면 그대로 개발 흔적이 된다.
//   개발용 구분은 라벨이 아니라 **키 이름**으로 한다(?dev 에서만 ' (slayer)' 처럼 붙는다).
const CHAR_LABEL = { basic2: '검사', kensa: '검사', slayer: '검사', tank: '탱커', archer: '궁수', soldier: '병사', basic: '기본' };
let charIdx = 0;
// 지금 활성인 캐릭터 이름. charIdx 는 최초 로드 때 ?char= 보다 늦게 맞춰져서 믿을 수 없다.
let curChar = null;

function loadChar(name, onDone) {
  // ★쿼리는 glbUrl 이 정한다(맨 위 「glb 캐시 버전표」). 예전에는 여기서 페이지
  //   쿼리를 그대로 붙였는데, 그게 배포본에서 「?dev 로만 새 모델이 보이는」 착시를
  //   만들었다. 이제 배포는 ?v=<해시>, 개발은 페이지 쿼리다(섞이지 않는다).
  loader.load(glbUrl('./' + name + '.glb'), gltf => {
    const m = gltf.scene;
    m.updateMatrixWorld(true);
    // ★키 기준은 **몸통 메시만**. 칼 7자루가 박스에 들어가면 바인드 포즈에서
    // 위아래로 삐져나와 키가 부풀고, 캐릭터가 작아져 바닥에 파묻힌다.
    // 방패(SH_)도 같은 이유로 뺀다. 탱커 방패는 레스트(T포즈) 기준으로 구워져 있어
    // 손 옆 허공에 세로로 서 있다. 지금 치수로는 마침 몸통 높이 안에 들어가 있지만,
    // 방패를 조금만 키우거나 내리면 바로 박스를 밀어 키 정규화가 통째로 틀어진다.
    // (칼은 SW_, 방패는 SH_. 아래 swords 수집/발광 셸은 칼 전용이라 SH_ 를 넣지 말 것)
    // ★setFromObject 를 메시마다 부르기 전에 월드행렬을 갱신할 것(스케일이 튄다).
    const box = new THREE.Box3();
    const _tb = new THREE.Box3();
    m.traverse(o => {
      if (o.isMesh && !o.name.startsWith('SW_') && !o.name.startsWith('SH_')) {
        box.union(_tb.setFromObject(o));
      }
    });
    if (box.isEmpty()) box.setFromObject(m);
    const cfg = CHAR_CFG[name] || DEF_CFG;
    let h = box.max.y - box.min.y;
    const s = cfg.h / h;                   // 캐릭터별 목표 키로 정규화
    m.scale.setScalar(s);
    m.position.y = -box.min.y * s;
    root.add(m);
    h *= s;

    const feet = [];
    const swords = {};
    let hand = null;
    let lhand = null;
    m.traverse(o => {
      if (o.isMesh) {
        o.frustumCulled = false;
        o.castShadow = true;
        o.receiveShadow = true;
        const old = o.material;
        o.userData.mn = (old && old.name) || '';   // 재질 이름은 여기서만 알 수 있다
        o.material = new THREE.MeshToonMaterial({
          map: old && old.map ? old.map : null,
          color: old && old.map ? 0xffffff : (old ? old.color : 0x888888)
        });
      }
      if (o.isBone && /r[_ ]hand/i.test(o.name)) hand = o;
      if (o.isBone && /l[_ ]hand/i.test(o.name)) lhand = o;   // ★21차. 활 쥔 손
      if (o.isBone && /(foot|toe)/i.test(o.name)) feet.push(o);
      if (o.isSkinnedMesh && o.name.startsWith('SW_')) {
        const k = o.name.slice(3).replace(/_\d+$/, '');
        (swords[k] = swords[k] || []).push(o);
      }
    });

    const mx = new THREE.AnimationMixer(m);
    const acts = {};
    gltf.animations.forEach(c => {
      const a = mx.clipAction(c);
      acts[c.name] = a;
      if (c.name === 'Run') a.timeScale = cfg.run.ts;
      if (c.name === 'Walk') a.timeScale = cfg.walk.ts;
      if (c.name === 'Attack' || c.name === 'Heavy' || c.name === 'Wide') {
        a.setLoop(THREE.LoopOnce); a.clampWhenFinished = true;
      }
    });

    CHARS[name] = { model: m, mixer: mx, actions: acts, handBone: hand, lhandBone: lhand,
                    feet, swords, charH: h, clips: gltf.animations.map(c => c.name) };
    m.visible = false;
    if (onDone) onDone(name);
  }, (ev) => {
    // ★진행률. index.html 인라인이 window.__loadProgress(0~1) 를 첫 바이트부터 깔아 둔다
    //   (handoff_ui A-1). 호출이 하나도 없으면 그쪽이 가짜 크리프로 기어가므로,
    //   실제 바이트 진도를 흘려 주는 게 언제나 낫다. 캐릭터 구간은 0.35~0.90 을 쓴다.
    if (ev && ev.lengthComputable && ev.total > 0) {
      loadProgress(0.35 + 0.55 * (ev.loaded / ev.total));
    }
  }, err => {
    if (DEV) console.warn('로드 실패', name, err);
    if (onDone) onDone(null);
  });
}

function activateChar(name) {
  const c = CHARS[name];
  if (!c) return false;
  // ★미리보기는 옛 캐릭터의 액션을 붙들고 있다(LoopOnce -> LoopRepeat 로 바꿔둔 상태).
  //   전역 포인터를 갈아끼우기 **전에** 정리해야 옛 캐릭터의 공격 클립이 복구된다.
  //   resume=false: 아래에서 어차피 current 를 비우고 Idle 을 다시 튼다.
  exitPreview(false);
  for (const k in CHARS) CHARS[k].model.visible = (k === name);
  // 전역 포인터 교체
  curCfg = CHAR_CFG[name] || DEF_CFG;
  model = c.model;
  mixer = c.mixer;
  handBone = c.handBone;
  lhandBone = c.lhandBone || null;
  charH = c.charH;
  current = null;
  bladeOK = false;
  for (const k in actions) delete actions[k];
  for (const k in c.actions) actions[k] = c.actions[k];
  footBones.length = 0;
  for (const b of c.feet) footBones.push(b);
  for (const k in swordMesh) delete swordMesh[k];
  for (const k in c.swords) swordMesh[k] = c.swords[k];
  // 상태 초기화(전 캐릭터의 공격/점프가 남으면 새 캐릭터가 굳는다)
  attacking = false; jumping = false; heavy = false;
  atkClip = null; stepLeft = 0; coastLeft = 0;
  trailBuf.length = 0; spray.length = 0; _lowHist.length = 0;
  if (Object.keys(c.swords).length) {
    for (const k in GLOW) {
      const sw = SWORDS.find(v => v.el === k);
      if (sw && c.swords[sw.key]) setupGlow(sw.key, GLOW[k]);
    }
    equipSword(swordIdx);
    if (swordEl) swordEl.style.display = '';
  } else if (swordEl) {
    // ★칼이 없는 캐릭터(궁수 등)로 바꿔도 우하단에 앞 캐릭터의 칼 이름이 그대로
    //   남아 있었다(v72 QA #16 "2. 백아"). 들고 있지도 않은 칼 이름은 거짓말이라 감춘다.
    //   판단은 목록이 아니라 **실제 SW_ 메시 유무**로 한다(캐릭터가 늘어도 안 깨진다).
    swordEl.style.display = 'none';
  }
  play('Idle');
  curChar = name;
  // 우상단 상태줄. ★2026-08-10 2차 QA(S5): "검사 (kensa) · 클립 7개" 는 **개발 정보**다.
  //   내부 이름과 클립 수는 플레이어에게 아무 뜻이 없고, 게임이 아직 만들다 만 것처럼 읽힌다.
  //   ?dev 에서만 쓴다. 평시에는 비워서 화면에서 아예 없앤다(공간도 안 먹게 display 를 끈다).
  const el = document.getElementById('stat');
  if (el) {
    el.textContent = DEV ? (CHAR_LABEL[name] || name) + ' (' + name + ') · 클립 ' + c.clips.length + '개' : '';
    el.style.display = DEV ? '' : 'none';
  }
  refreshPanel();
  window.__dbg = { mixer, actions, model, root, CHARS,
                   get cur(){return current;}, get atk(){return attacking;} };
  return true;
}

function cycleChar() {
  for (let i = 1; i <= CHAR_LIST.length; i++) {
    const n = CHAR_LIST[(charIdx + i) % CHAR_LIST.length];
    if (CHARS[n]) { charIdx = CHAR_LIST.indexOf(n); activateChar(n); return; }
  }
}

// ---------------------------------------------------------------- 클립 미리보기 패널(개발용)
// 캐릭터마다 클립 구성이 다르다(검사 7개 / 병사 4개, 병사는 Jump 자체가 없다).
// 이름만 봐선 뭐가 뭔지 모르니 눌러서 돌려보게 만든다.
// ★HUD(.hud) 는 pointer-events:none 이라 그 안에 버튼을 넣으면 클릭이 안 먹는다.
//   그래서 패널은 별도 div 로 body 에 직접 붙이고, CSS 도 파일 추가 없이 여기서 주입한다.
const STD_CLIPS = ['Idle', 'Walk', 'Run', 'Attack', 'Jump'];   // 표준 5종. 없는 걸 알려주려고 둔다
const PREVIEW_FPS = 30;                                        // 프레임 표시·스텝 기준
const preview = {
  on: false,          // 켜져 있으면 렌더 루프의 상태 기계를 통째로 건너뛴다
  name: null,         // 재생 중인 클립 이름
  act: null,          // 그 클립의 AnimationAction
  last: 'Idle',       // P 로 다시 켤 때 마지막으로 보던 클립
  rate: 1,            // 재생속도 배수(0.25 / 0.5 / 1)
  paused: false,
  // ★Attack/Heavy/Wide 는 게임에선 LoopOnce + clampWhenFinished 다. 미리보기에선
  //   반복 재생해야 보이므로 잠깐 바꾸고, 나갈 때 반드시 원래대로 되돌린다.
  //   안 되돌리면 정상 모드에서 공격 모션이 영원히 반복된다.
  saved: new Map(),
};
// 매 프레임 DOM 을 다시 쓰지 않으려고 마지막 값을 들고 비교한다(선언이 먼저 와야 TDZ 가 없다).
let cpLastCur, cpLastTxt = '';

const cp = (() => {
  const st = document.createElement('style');
  st.textContent =
  '#cp{position:fixed;right:14px;top:42px;width:244px;z-index:8;max-height:calc(100vh - 128px);' +
  'overflow-y:auto;padding:10px 11px 11px;border:1px solid #24455f;border-radius:9px;' +
  'background:rgba(5,10,17,0.84);color:#a9c4d8;font-size:12px;line-height:1.45;letter-spacing:.2px;' +
  'font-family:"Paperlogy",-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif;user-select:none}' +
  '#cp::-webkit-scrollbar{width:6px}#cp::-webkit-scrollbar-thumb{background:#24455f;border-radius:3px}' +
  '#cp .t{color:#7fd8ff;font-weight:700;font-size:12.5px;letter-spacing:.6px}' +
  '#cp .miss{margin-top:3px;font-size:11px;color:#6f8496}#cp .miss b{color:#ff9a7a;font-weight:600}' +
  '#cp .sec{margin-top:8px;padding-top:8px;border-top:1px solid #18324a}' +
  '#cp .cb{display:flex;align-items:center;width:100%;gap:7px;margin-top:4px;padding:5px 8px;' +
  'border:1px solid #23405a;border-radius:6px;background:#0b1622;color:#bcd6ea;font:inherit;' +
  'font-size:12px;cursor:pointer;text-align:left}' +
  '#cp .cb:hover{background:#12283c;border-color:#356e94}' +
  '#cp .cb .n{flex:0 0 12px;color:#5f7d94;font-size:10.5px}' +
  '#cp .cb .nm{flex:1 1 auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
  '#cp .cb .d{flex:0 0 auto;color:#6f8496;font-size:10.5px}' +
  '#cp .cb.on{background:#12405e;border-color:#7fd8ff;color:#eaf8ff}' +
  '#cp .cb.on .n,#cp .cb.on .d{color:#9fe0ff}' +
  '#cp .cb.cur{border-color:#3f7ca3;color:#dff1ff}' +
  '#cp .cb.no{opacity:.38;cursor:default}' +
  '#cp .r{display:flex;gap:4px;margin-top:5px;align-items:center}' +
  '#cp .r .lb{flex:0 0 36px;color:#6f8496;font-size:10.5px}' +
  '#cp .sb{flex:1 1 0;padding:4px 0;border:1px solid #23405a;border-radius:5px;background:#0b1622;' +
  'color:#bcd6ea;font:inherit;font-size:11px;cursor:pointer}' +
  '#cp .sb:hover{background:#12283c}#cp .sb.on{background:#12405e;border-color:#7fd8ff;color:#eaf8ff}' +
  '#cp .tm{margin-top:7px;font-size:11px;color:#8fb4cc;font-variant-numeric:tabular-nums}' +
  '#cp .bar{height:3px;margin-top:4px;border-radius:2px;background:#16293a;overflow:hidden}' +
  '#cp .bar i{display:block;height:100%;width:0;background:#7fd8ff}' +
  '#cp .ex{width:100%;margin-top:7px;padding:5px 0;border:1px solid #3a5b74;border-radius:6px;' +
  'background:#122232;color:#9fd8ff;font:inherit;font-size:11.5px;cursor:pointer}' +
  '#cp .ex:hover{background:#1a3247}' +
  '#cp .hint{margin-top:8px;font-size:10.5px;color:#5d7386;line-height:1.65}' +
  '#cp .hint b{color:#8fb4cc;font-weight:600}' +
  '#cp.off .ctl{opacity:.42}';       // 미리보기가 아니면 제어부는 흐리게(눌리기는 한다)
  document.head.appendChild(st);

  const el = document.createElement('div');
  el.id = 'cp';
  el.className = 'off';
  // ★v96 회귀 수정. 이 판은 모듈이 뜨는 순간 body 에 붙는데, display 를 정하는 코드는
  //   refreshPanel(캐릭터 로드 뒤)에 있다. 그래서 **로딩 화면이 떠 있는 동안** 파란
  //   개발자 패널이 오른쪽 위에 그대로 보였다(심사 지적 "로딩 중 dev DOM"). 처음부터
  //   감춰 두고 refreshPanel 이 ?dev 일 때만 켠다.
  el.style.display = 'none';
  // 정적 뼈대만 innerHTML 로. 클립 이름(glb 에서 온 값)은 아래에서 textContent 로 넣는다.
  el.innerHTML =
    '<div class="t" id="cpT">클립</div>' +
    '<div class="miss" id="cpM"></div>' +
    '<div class="sec" id="cpL"></div>' +
    '<div class="sec ctl">' +
      '<div class="r"><span class="lb">속도</span>' +
        '<button class="sb" data-rate="0.25">0.25x</button>' +
        '<button class="sb" data-rate="0.5">0.5x</button>' +
        '<button class="sb" data-rate="1">1x</button></div>' +
      '<div class="r"><span class="lb">프레임</span>' +
        '<button class="sb" id="cpPause">일시정지</button>' +
        '<button class="sb" id="cpPrev">◀ ,</button>' +
        '<button class="sb" id="cpNext">. ▶</button></div>' +
      '<div class="tm" id="cpTm">정상 모드</div>' +
      '<div class="bar"><i id="cpBar"></i></div>' +
      '<button class="ex" id="cpExit">정상 모드로 (ESC)</button>' +
    '</div>' +
    '<div class="hint">클립을 눌러 미리보기 · 미리보기 중 <b>1~9</b> 로 선택<br>' +
      '<b>P</b> 켜고끄기 · <b>,</b> <b>.</b> 한 프레임 · <b>ESC</b> 나가기</div>';
  document.body.appendChild(el);

  const q = id => el.querySelector('#' + id);
  const o = { root: el, title: q('cpT'), miss: q('cpM'), list: q('cpL'), tm: q('cpTm'),
              bar: q('cpBar'), pause: q('cpPause'), btns: [],
              rates: Array.prototype.slice.call(el.querySelectorAll('[data-rate]')) };
  // ★버튼에 포커스가 남으면 그 뒤에 누른 Space(점프)가 그 버튼을 다시 클릭한다.
  //   mousedown 을 막아 아예 포커스를 안 준다. 나중에 만드는 클립 버튼도 같은 처리를 한다.
  el.addEventListener('mousedown', e => { if (e.target.closest('button')) e.preventDefault(); });
  o.rates.forEach(b => b.addEventListener('click', () => { preview.rate = +b.dataset.rate; syncCtl(); }));
  o.pause.addEventListener('click', () => { preview.paused = !preview.paused; syncCtl(); });
  q('cpPrev').addEventListener('click', () => stepFrame(-1));
  q('cpNext').addEventListener('click', () => stepFrame(1));
  q('cpExit').addEventListener('click', () => exitPreview());
  return o;
})();

// 클립 하나를 골라 미리보기로 들어간다(이미 미리보기면 클립만 갈아탄다).
function previewClip(name) {
  const a = actions[name];
  // ★없는 클립 방어. 병사에는 Jump 가 없다. 예전에 actions.Jump 가 undefined 인데
  //   a.time 을 건드려 TypeError 로 렌더 루프가 통째로 멈춘 사고가 있었다. 여기서 끊는다.
  if (!a) { refreshPanel(); return false; }
  if (window.__freeze) window.__freeze = false;   // DEV 굽기 함수가 세워둔 상태면 안 움직인다
  if (!preview.on) {
    preview.on = true;
    // 공격·점프 중에 눌렀을 수 있다. 남은 상태를 털어야 클립만 깨끗이 보인다.
    attacking = false; heavy = false; jumping = false;
    trailBuf.length = 0; spray.length = 0;
  }
  _lowHist.length = 0;                            // 클립이 바뀌면 접지 기준을 새로 잡는다
  for (const k in actions) if (actions[k] !== a) actions[k].stop();
  if (!preview.saved.has(a)) {
    preview.saved.set(a, { loop: a.loop, reps: a.repetitions, clamp: a.clampWhenFinished });
  }
  a.setLoop(THREE.LoopRepeat, Infinity);
  a.clampWhenFinished = false;
  a.reset();                    // reset 은 timeScale 을 안 건드린다(걷기/달리기 ts 가 살아 있다)
  a.setEffectiveWeight(1);
  a.play();
  current = a;
  preview.name = name; preview.act = a; preview.last = name; preview.paused = false;
  if (mixer) mixer.update(0);
  refreshPanel();
  return true;
}

// 패널 버튼 순서 = 숫자키 순서. 없는 번호를 눌러도 조용히 무시한다.
function previewClipAt(i) {
  const it = cp.btns[i];
  if (!it || !it.act) return;
  previewClip(it.name);
}

function togglePreview() {
  if (preview.on) { exitPreview(); return; }
  const c = curChar ? CHARS[curChar] : null;
  if (!c || !c.clips.length) return;            // 아직 로딩 중이면 아무 일도 안 한다
  previewClip(c.actions[preview.last] ? preview.last : c.clips[0]);
}

// resume=false 는 캐릭터 교체용. activateChar 가 어차피 current 를 비우고 Idle 을 다시 트니
// 여기서 옛 캐릭터의 액션을 또 건드리지 않는다.
function exitPreview(resume = true) {
  if (!preview.on) { return; }
  const a = preview.act;
  preview.on = false; preview.name = null; preview.act = null; preview.paused = false;
  // 바꿔놨던 루프 설정을 되돌린다. Map 이 액션 참조를 직접 들고 있어서
  // 이미 다른 캐릭터로 넘어간 뒤에 불려도 옛 액션이 제대로 복구된다.
  preview.saved.forEach((s, act) => { act.setLoop(s.loop, s.reps); act.clampWhenFinished = s.clamp; });
  preview.saved.clear();
  if (a) a.stop();
  _lowHist.length = 0;
  if (resume) {
    current = null;              // 비워야 play('Idle') 가 크로스페이드 없이 바로 먹는다
    play('Idle');
    if (mixer) mixer.update(0);
  }
  refreshPanel();
}

// 정지 상태에서 한 프레임씩. 어느 프레임에서 자세가 깨지는지 짚으려고 만든 것이다.
function stepFrame(dir) {
  const a = preview.act;
  if (!preview.on || !a) return;                 // 미리보기 밖에서는 a.time 을 절대 안 건드린다
  preview.paused = true;
  const dur = a.getClip().duration;
  let t = a.time + dir / PREVIEW_FPS;
  if (dur > 0) { while (t < 0) t += dur; while (t >= dur) t -= dur; } else t = 0;
  a.time = t;
  if (mixer) mixer.update(0);                    // 세워둔 상태라 여기서 직접 포즈를 갱신한다
  syncCtl();
  updateCpLive();
}

// 캐릭터가 바뀌거나 미리보기 상태가 바뀔 때만 부른다(매 프레임 아님).
function refreshPanel() {
  const c = curChar ? CHARS[curChar] : null;
  cp.root.className = preview.on ? '' : 'off';
  // ★평소에는 숨긴다. 개발 패널이 화면 오른쪽 15% 를 늘 먹고 있으면 게임 화면을
  //   판단할 수가 없다(시점·이펙트 스크린샷마다 이게 절반을 가렸다).
  //   ★v96. P 키가 DEV 뒤로 들어갔으므로(위 keydown) 이 판은 **?dev 에서만** 뜬다.
  //   preview.on 을 or 로 두면 프로덕션에서 다른 경로로 미리보기가 켜지는 날 다시 샌다.
  cp.root.style.display = DEV ? '' : 'none';
  cp.btns.length = 0;
  cp.list.textContent = '';
  if (!c) { cp.title.textContent = '클립 (불러오는 중)'; return; }
  const names = [];
  for (const n of c.clips) if (names.indexOf(n) < 0) names.push(n);   // 이름이 겹치면 액션도 하나다
  // ★내부 이름(kensa/slayer)은 ?dev 에서만 붙인다. 미리보기(P)는 평시에도 열리는 화면이라
  //   여기에 개발 표기를 그대로 두면 S5 게이트에 구멍이 난다.
  cp.title.textContent = (CHAR_LABEL[curChar] || curChar)
                       + (DEV ? ' (' + curChar + ')' : '')
                       + ' · 클립 ' + names.length + '개'
                       + (preview.on ? '  [미리보기]' : '');
  const missing = STD_CLIPS.filter(n => !c.actions[n]);
  if (missing.length) cp.miss.innerHTML = '없는 표준 클립: <b>' + missing.join(' / ') + '</b>';
  else cp.miss.textContent = '표준 5종(Idle Walk Run Attack Jump) 모두 있음';
  names.forEach((n, i) => {
    const a = c.actions[n];
    const b = document.createElement('button');
    b.className = 'cb' + (a ? '' : ' no');
    const num = document.createElement('span');
    num.className = 'n';
    num.textContent = i < 9 ? String(i + 1) : '';
    const nm = document.createElement('span');
    nm.className = 'nm';
    nm.textContent = n;
    const du = document.createElement('span');
    du.className = 'd';
    // 길이는 THREE.AnimationClip.duration. 액션이 없으면 눌리지도 않게 막는다.
    du.textContent = a ? a.getClip().duration.toFixed(2) + 's' : '액션 없음';
    b.appendChild(num); b.appendChild(nm); b.appendChild(du);
    if (a) b.addEventListener('click', () => previewClip(n));
    cp.list.appendChild(b);
    cp.btns.push({ name: n, el: b, act: a });
  });
  syncCtl();
}

function syncCtl() {
  cp.rates.forEach(b => b.classList.toggle('on', +b.dataset.rate === preview.rate));
  cp.pause.classList.toggle('on', preview.paused);
  cp.pause.textContent = preview.paused ? '재생' : '일시정지';
  // current 와 절대 같을 수 없는 값을 넣어 다음 프레임에 강조를 한 번 다시 칠하게 한다.
  cpLastCur = undefined;
}

// 매 프레임: 재생 시각 표시 + '지금 재생 중' 강조. DOM 쓰기는 값이 바뀔 때만 한다.
function updateCpLive() {
  if (current !== cpLastCur) {
    cpLastCur = current;
    for (const it of cp.btns) {
      it.el.classList.toggle('on', preview.on && preview.name === it.name);
      it.el.classList.toggle('cur', !preview.on && !!it.act && it.act === current);
    }
  }
  const a = preview.act;
  let txt = '정상 모드';
  let pct = 0;
  if (preview.on && a) {
    const dur = a.getClip().duration;
    const t = a.time;
    pct = dur > 0 ? (t / dur) * 100 : 0;
    // 예: 0.83 / 1.92s · f25/58 · x0.5 · ts1.84(클립에 박힌 재생속도) · 정지
    txt = t.toFixed(2) + ' / ' + dur.toFixed(2) + 's · f' + (Math.floor(t * PREVIEW_FPS) + 1) +
          '/' + Math.max(1, Math.round(dur * PREVIEW_FPS)) + ' · x' + preview.rate +
          (a.timeScale !== 1 ? ' · ts' + a.timeScale : '') + (preview.paused ? ' · 정지' : '');
  }
  if (txt !== cpLastTxt) {
    cpLastTxt = txt;
    cp.tm.textContent = txt;
    cp.bar.style.width = pct.toFixed(1) + '%';
  }
}

{
  // 기본 시작 캐릭터는 CHAR_LIST 맨 앞이다(예전엔 'slayer' 가 박혀 있어 목록 순서를
  // 바꿔도 시작 캐릭터가 안 바뀌었다). ?char= 로 덮어쓸 수 있다.
  // ★2026-08-19 부터 ?char= 는 평시에도 먹는다(위 CHAR_LIST 정의. 홈화면이 이 값을 넘긴다).
  //   못 찾으면 아래 폴백이 조용히 검사로 돌아간다(에러 없음).
  const want = (new URLSearchParams(location.search).get('char') || CHAR_LIST[0]);
  let left = CHAR_LIST.length;
  const total = CHAR_LIST.length;
  loadProgress(0.35);              // 맵(level1.glb)은 여기 오기 전에 이미 끝났다
  CHAR_LIST.forEach(n => loadChar(n, () => {
    loadProgress(0.35 + 0.55 * (total - left + 1) / total);
    if (--left === 0) {
      if (!activateChar(want)) activateChar(CHAR_LIST.find(k => CHARS[k]));
      charIdx = Math.max(0, CHAR_LIST.indexOf(want));
      // ★#load 를 여기서 바로 감추지 않는다(9차. 연출UI S1 "타이틀 카드 미발화").
      //   에셋 파싱이 메인 스레드를 1~8초 물고 있는 동안 카드를 띄우면, CSS 애니는
      //   **문서 타임라인(벽시계)** 을 타므로 화면에 한 프레임도 안 그려진 채로 다 지나간다.
      //   그래서 "프레임이 실제로 흐르기 시작한 뒤"에 감춘다(아래 bootGate).
      bootAssetsDone = true;
    }
  }));
}
// ── 부팅 게이트 ──
// #load 를 감추는 그 순간이 곧 ui.js 의 입장 카드 신호다(waitSpawn 이 display 를 본다).
// 그래서 **연속 3프레임이 매끄럽게 흐른 뒤**에 감춘다. 기준 0.10초는 "10fps 보다
// 빠르다"는 뜻이고, 셋을 연달아 요구하므로 파싱 히치 한 방으로는 안 열린다.
let bootAssetsDone = false, bootShown = false, bootSmooth = 0, bootDoneAt = 0;
function loadProgress(p) {
  // ui.js 가 로딩 진행 셸을 정의하면 그쪽이 받는다. 없으면 아무 일도 안 한다.
  try { if (typeof window.__loadProgress === 'function') window.__loadProgress(Math.max(0, Math.min(1, p))); }
  catch (e) { /* 진행 표시가 게임을 멈출 이유는 없다 */ }
}
function bootGate(rawDt) {
  if (bootShown || !bootAssetsDone) return;
  if (!bootDoneAt) bootDoneAt = performance.now();
  // ★0.06초 = 16fps 보다 빠른 프레임. 카드의 CSS 애니는 **문서 타임라인(벽시계)** 을
  //   타므로, 이보다 느린 상태에서 띄우면 애니 앞부분이 화면에 한 장도 안 그려진 채
  //   지나간다(그게 심사의 "40초간 불투명도 0" 이었다). 셋을 연달아 요구한다.
  if (rawDt > 0 && rawDt < 0.06) bootSmooth++; else bootSmooth = 0;
  // ★백스톱. 느린 기계(또는 다른 프로그램이 물고 있는 기계)에서는 매 프레임이
  //   0.12초를 넘어 게이트가 **영영 안 열릴 수 있다.** 그러면 로딩 화면에 갇힌다.
  //   에셋이 다 온 뒤 3초가 지나면 매끄럽든 말든 연다. 카드가 좀 끊겨 보이는 것보다
  //   게임이 안 시작되는 게 훨씬 나쁘다.
  if (bootSmooth < 3 && performance.now() - bootDoneAt < 3000) return;
  bootShown = true;
  loadProgress(1);
  const el = document.getElementById('load');
  if (el) el.style.display = 'none';
}

// ── 멀티플레이 창구 ──
// ★선언이 play() 보다 **앞**에 있어야 한다. 로딩 중 activateChar 가 play('Idle') 를
//   부르는데, let 은 선언 전에 읽으면 ReferenceError 다(TDZ). 값은 파일 끝에서 채운다.
let multi = null;
// ★요괴 동기화(2단계 1차)도 같은 이유로 여기서 선언한다. 아래 enemies 의 onHit 이
//   이 이름을 읽는데, 값을 채우는 자리는 파일 끝(멀티 기동부)이다. const 로 뒤에
//   두면 그 사이에 칼이 한 번만 닿아도 TDZ 로 게임이 죽는다(ARROW_ON 에서 밟은 함정).
let mpEnemy = null;
// ★지금 도는 클립 이름. **play() 에 적어 두는 방식은 틀렸다** - 공격 셋(tryAttack·
//   tryHeavy·tryWide)은 play() 를 거치지 않고 액션을 직접 조작한다(3연타를 내려면
//   클립 시간을 단수 진입점으로 점프시켜야 해서다). 그래서 그 방식으로는 공격이
//   통째로 누락돼 남의 화면에 'Idle' 로 전해졌다(2026-08-19 「팀원 공격이 안 보인다」).
//   actions 는 일곱 개뿐이라 역산이 훨씬 싸고, 무엇보다 **어떤 경로로 바뀌든 맞는다.**
function clipNameOf(act) {
  if (!act) return 'Idle';
  for (const k in actions) if (actions[k] === act) return k;
  return 'Idle';
}

function play(name, fade = 0.18) {
  const a = actions[name];
  if (!a || current === a) return;
  _lowHist.length = 0;               // 클립이 바뀌면 접지 기준을 새로 잡는다
  a.reset().play();
  if (current) current.crossFadeTo(a, fade, false);
  else a.fadeIn(fade);
  current = a;
}

// 3연타 클립의 단수별 진입점(초)과 그 단수의 커밋 길이(초).
// ★근거는 enemy.js 의 타격 게이트(hot)를 60fps 로 찍은 실측이다(위 ATK_COMMIT 주석).
//   입력 후 경과 ms 기준 hot 구간 [68.8~137][190.3~264.3] / [366.9~434.3] / [726.3~825.3]
//   을 클립초(=ms/1000*1.35)로 환산하면 스윙 셋이 클립 0.093~0.357 / 0.495~0.586 /
//   0.980~1.114 에 있다. 진입점은 각 스윙의 예비동작 0.09초 앞이고,
//   커밋은 "그 스윙의 타격이 끝나는 순간"까지다(= (hot끝 - 진입)/1.35).
// ★2026-08-12 14-베기수정으로 클립이 또 바뀌어 다시 쟀다(위 ATK_COMMIT 주석의 새 표).
//   새 클립(1.500초 = 게임 1.133초)의 스윙 셋: HOT_ON 구간이 입력 후 경과로
//     1타 0.134~0.300 · 2타 0.433~0.565 · 3타 0.883~1.050 초.
//   클립초 = 경과 x 1.35 이므로 스윙 시작이 클립 0.181 / 0.585 / 1.192.
//   진입점 = 거기서 예비동작 0.09초를 뺀 값(1타는 클립 머리라 0).
//   커밋   = (그 스윙의 HOT_ON 구간 끝 클립초 - 진입점) / 1.35.
//     1타 (0.405-0)/1.35 = 0.30   2타 (0.763-0.495)/1.35 = 0.20   3타 (1.418-1.10)/1.35 = 0.24
//   ★1타 커밋이 0.40 -> 0.30 으로 돌아온 것이 이번 작업의 목표 중 하나였다
//     (오너 "휘두르는 모션이 이상하다" = 예비동작이 길다. 예비동작을 자르니 커밋도 짧아졌다).
//   옛 값 [0, 0.70, 1.28] / [0.40, 0.17, 0.29].
// ★2026-08-13 15-모션수제로 클립을 손으로 다시 짜서 또 옮겨졌다(commit_after.json):
//   스윙 셋의 HOT_ON 구간이 입력 후 경과로 0.167~0.283 / 0.583~0.700 / 1.000~1.099 초.
//   클립초 = 경과 x 1.35 이므로 스윙 시작이 클립 0.225 / 0.787 / 1.350.
//   진입점 = 거기서 예비동작 0.09초(=클립 0.12)를 뺀 값. 1타는 클립 머리라 0 이다.
//   커밋   = (그 스윙의 HOT_ON 구간 끝 클립초 - 진입점) / 1.35.
//     1타 (0.382-0)/1.35 = 0.28   2타 (0.945-0.667)/1.35 = 0.21   3타 (1.484-1.230)/1.35 = 0.19
//   옛 값 [0, 0.50, 1.10] / [0.30, 0.20, 0.24].
// ★2026-08-13 16-베기근본으로 또 옮겨졌다(위 ATK_COMMIT 주석의 새 표).
//   스윙 셋의 클립 시작이 0.267 / 0.733 / 1.200 초. 진입점 = 거기서 예비 0.09초
//   (=클립 0.12초)를 뺀 값. 1타는 클립 머리라 0.
//   커밋 = (그 스윙의 hot 끝 클립초 - 진입점) / 1.35.
//     1타 (0.400-0)/1.35 = 0.30   2타 (0.833-0.580)/1.35 = 0.19   3타 (1.300-1.080)/1.35 = 0.16
//   옛 값 [0, 0.67, 1.23] / [0.28, 0.21, 0.19].
// ── 2026-08-24 23차 모션재작으로 또 옮겨졌다(위 ATK_COMMIT 주석의 새 표) ──
// 새 대본은 임팩트 뒤 **홀드(칼이 서는 3장)** 가 생겨서, 진입점을 "스윙 시작 −0.09초"
// 격자가 아니라 **자세가 이어지는 자리**(홀드 끝 = 재장전 시작)에 앉힌다:
//   · 연타 캔슬은 대개 명중+0.12초 = 클립 0.43~0.56(1타 뒤 홀드 구간)에서 일어난다.
//     옛 진입(0.58)은 재장전 한복판이라 클립 점프가 자세 팝(칼끝 페이크 70~98m/s,
//     손 화면 17px 점프. live_before mash250 실측)을 만들었다. 홀드→재장전 초입(0.55)
//     으로 옮기면 같은 실측이 12px·30m/s 로 준다(live_after).
//   · 2타 hot 은 클립 0.733(f22)부터라 진입 0.55 = 예비 0.136초. 3타 hot 은 1.200(f36),
//     진입 1.00(f30, 3타 장전 초입) = 예비 0.148초.
//   커밋 = (그 스윙의 hot 끝 클립초 − 진입) / 1.35. 단발 실측(live_after):
//     1타 (0.369−0)/1.35 = 0.27→0.28   2타 (0.818−0.55)/1.35 = 0.20   3타 (1.268−1.00)/1.35 = 0.20
//   옛 값 [0, 0.58, 1.08] / [0.30, 0.19, 0.16].
// ── 2026-08-24 24차 대검 물리 재작(blender/s24 MOVES_V24)에서 **재실측 = 표 불변** ──
// 타격 슬롯을 일부러 23차 자리에 고정하고 감기·회수만 다시 썼기 때문이다. 단발 실측
// (v99_wave24/motion/live_after): Z hot [5~94(캐스트)][162~277][510~610][862~942] ·
// X [256~356] · C [237~385] — 23차와 프레임 반올림 안에서 같다. 커밋·DPS 영향 0.
const ATK_STEP_T = [0, 0.55, 1.00];
const ATK_STEP_COMMIT = [0.28, 0.20, 0.20];

// ── ★★궁수 (21차. 오너 지시 「궁수 활 쏘는거 없으면 만들어줘」) ─────────────
// **위 두 표는 검사 클립 기준인데 여태 캐릭터 구분 없이 쓰였다.** 궁수에 판정이
// 붙기 전까지는 캔슬이 아예 안 걸려서 안 드러났을 뿐이다. Z 를 연타하면 궁수 클립의
// 만작(0.58)·복귀 꼬리(1.08) 자리로 재진입해서 **활을 반쯤 당긴 자세부터 다시 쏘는**
// 그림이 나온다. 그래서 표를 캐릭터별로 가른다.
//
// 궁수 Attack 클립의 실측(archer.glb, blender/s11_archer.py 의 SHOT 표가 정본):
//   길이 1.1667초 = 28프레임 @24fps.  f1 차렷 · f5 메김 · f11 만작 · f16 조준정지 ·
//   f19 「손이 귀 뒤로」 · f28 복귀.  프레임 f 의 클립 시각은 **f/24** 다.
//
// ★★**발사 프레임은 f19 가 아니라 f16 이다.** 표만 읽고 f19(0.792)로 잡았다가
//   실측으로 뒤집었다. 시위 손(오른손)의 속도를 클립초에 대해 찍으면(__slow 0.08 로
//   12.5배 늦춰 165표본) 이렇게 나온다:
//       클립 0.46~0.66  속도 0.01~0.13   ← **조준 정지**(손이 얼어 있다)
//       클립 0.679      3.36             ← 여기서 손이 튄다 = 시위를 놓은 순간
//       클립 0.716~0.733 11.0~11.6       ← 봉우리(손이 귀 뒤로 날아가는 중)
//       클립 0.795      2.02             ← 이미 다 날아가서 잦아드는 중
//   즉 f19(0.792)는 **손이 다 날아간 뒤의 자세**고, 시위가 풀리는 순간은 조준 정지가
//   끝나는 f16(0.667)이다. f19 에 맞춰 쏘면 손이 follow-through 를 마친 뒤에야
//   화살이 나타난다(게임시간 0.06초 늦다 = 4프레임).
const ARCHER_TS = 2.00;              // 궁수 Attack 재생속도(검사는 1.35 그대로)
const ARCHER_ENTER = 0.10;           // 클립 진입점(초). 차렷 자세를 건너뛴다
const ARCHER_SHOT_CLIP = 16 / 24;    // 시위를 놓는 클립 시각(초) = 0.667. 위 실측이 근거다
//
// ★재생속도를 1.35 -> 2.00 으로 올렸다. 근거:
//   1.35 로 두면 키 입력에서 발사까지 0.667/1.35 = **0.494초**다. 같은 게임에서
//   검사 Z 1타는 입력 후 **0.167초**에 판정이 열린다(위 ATK_STEP_T 주석의 실측).
//   3배 굼뜬 평타는 "조준이 느린 활"이 아니라 **입력이 씹힌 것**으로 읽힌다.
//   그렇다고 검사와 같은 0.167 로 맞추면 만작~조준 구간이 뭉개져서 활을 당기는
//   그림 자체가 사라진다(활의 드라마가 만작인데 그걸 버리는 셈이다).
//   2.00 + 진입 0.10 이면 발사가 **0.283초**, 클립 전체가 0.533초다. 만작(클립 0.458)이
//   입력 후 0.18초에 서고, 검사의 1.7배라 "활이라 한 박자 느리다"로 읽힌다.
// ★진입점 0.10 은 f1(차렷, 클립 0.042)과 f5(메김, 클립 0.208) 사이다. 차렷 자세는
//   Idle 에서 크로스페이드(0.06)로 건너오므로 굳이 다시 밟을 이유가 없다.
// 키 입력에서 화살이 떠나기까지(초). **이 값이 이번 작업의 핵심 수치다.**
const ARCHER_RELEASE_T = (ARCHER_SHOT_CLIP - ARCHER_ENTER) / ARCHER_TS;   // = 0.283
// 커밋(= 이 시간 전에는 다른 입력으로 못 끊는다). 발사 직후에 열린다.
// ★0.02초(약 한 프레임) 여유를 준 이유: 발사와 커밋 해제가 같은 프레임에 겹치면
//   화살이 떠나는 프레임에 이미 클립이 끊길 수 있어서 "쏘는 손"이 화면에서 사라진다.
const ARCHER_COMMIT = ARCHER_RELEASE_T + 0.02;                            // = 0.303
// 궁수용 3연타 표. **세 칸이 같은 값이다** - 궁수 Attack 은 클립 하나에 쏘기 한 번이라
// 단수라는 게 없다(Z 를 연타하면 늘 처음부터 다시 당긴다).
const ATK_STEP_T_BOW = [ARCHER_ENTER, ARCHER_ENTER, ARCHER_ENTER];
const ATK_STEP_COMMIT_BOW = [ARCHER_COMMIT, ARCHER_COMMIT, ARCHER_COMMIT];
// ★활을 쏘는 캐릭터. **이름으로 가른다.** 칼 유무(bladeOK)로 가르면 칼을 안 든
//   캐릭터가 늘어날 때마다 같이 활을 쏘게 된다. 지금 활 클립을 가진 건 archer 하나다.
const BOW_CHARS = { archer: true };
// ★★롤백은 **이 한 줄이다.** false 로 두면:
//     · arrow.js 는 import 만 되고 시스템이 아예 안 만들어진다(메시도 안 생긴다)
//     · isArcher() 가 늘 false 라 궁수 Attack 이 검사 표·검사 재생속도(1.35)로 돌아간다
//     · 조준 반경도, 시위음도, 발사도 통째로 죽는다
//   **정의는 여기 한 곳뿐이다.** arrow.js 안에는 이 이름이 없다 - 두 벌이면 반드시
//   어긋난다는 게 이 레포가 반복해서 배운 것이다(HANDOFF §3 롤백).
const ARROW_ON = true;
// ★ARROW_ON 이 꺼져 있으면 **여기서부터 전부 거짓**이 된다 = 아래 표·타이밍·조준이
//   한꺼번에 옛 길로 돌아간다(검사 표를 쓰고, 화살을 안 쏘고, 클립은 1.35 로 돈다).
function isArcher() { return ARROW_ON && !!BOW_CHARS[curChar]; }
function atkStepT() { return isArcher() ? ATK_STEP_T_BOW : ATK_STEP_T; }
function atkStepCommit() { return isArcher() ? ATK_STEP_COMMIT_BOW : ATK_STEP_COMMIT; }
function atkTimeScale() { return isArcher() ? ARCHER_TS : 1.35; }
// ── 자동 조준 반경 ──
// ★SNAP_R(3.2m)은 **칼 사거리**에서 나온 값이라 활에 그대로 쓰면 안 된다
//   (3.2m 밖은 조준이 안 걸려서 활이 근접무기가 된다).
//   13m 의 근거: 이 카메라가 세로로 담는 세계가 약 14m 다. **화면에 보이는 놈까지만**
//   자동으로 겨눈다 - 화면 밖의 놈을 겨누면 캐릭터가 이유 없이 홱 도는 그림이 된다.
// ★반경 안에 아무도 없으면 바라보는 방향으로 그냥 쏜다(헛방의 자유를 남긴다).
const BOW_AIM_R = 13.0;
// 이번 캐스트에서 화살이 이미 떠났나. tryAttack 이 false 로 되돌린다.
let arrowShot = false;

function tryAttack() {
  // ★26차 오너 지시. 갈림은 이 한 줄뿐이다(DASH_ON 전례). 궁수(개발용)의 화살은 남긴다.
  if (!SKILL_Z_ON && !isArcher()) return;
  if (!actions.Attack) return;
  if (isCleared()) return;         // 층 돌파 뒤에는 안 받는다(입력 버퍼로 새는 경로까지 막는다)
  if (dashLeft > 0) { bufferInput('atk'); return; }   // 대시 중에 누른 Z 는 착지에 이어진다
  // ★공격 방향 스냅. 반경 SNAP_R(3.0m) 안에 적이 있으면 그쪽으로 몸을 돌리고 벤다.
  //   v72 QA: 요괴 넷이 몸에 겹쳐 있어도 각이 어긋나면 Z 12번에 1킬이었다.
  //   판정을 넓히는 게 아니라 **입력한 방향을 고쳐 주는** 것이라 헛스윙의 자유는 남는다
  //   (반경 안에 아무도 없으면 아무것도 안 한다). 규칙과 보간은 enemy.js 가 갖는다.
  //   ★반경은 main.js 가 넘긴다. enemy.js 기본값(2.6)은 그 파일의 소유라 안 건드린다.
  const now = gameT;
  // ── 9차: 누른 만큼 나간다 ──
  // 옛 규칙은 "이미 휘두르는 중이면 단수만 올리고 return" 이었다. 3연타가 클립 하나에
  // 스윙 셋으로 들어 있어서, **입력 세 번이 스윙 하나로 뭉개졌다**(심사의 "3연타 중
  // 2회만 발동"). 이제 캔슬 가능한 시점이면 다음 타를 **그 자리에서 다시 시작**한다.
  //   · 커밋 안(칼이 나가는 중)  -> 버퍼에 적어 두고 캔슬 프레임에 자동으로 이어진다
  //   · 캔슬 가능                -> 클립을 다음 단수 지점부터 다시 튼다
  if (attacking && !canCancelAttack(now)) { bufferInput('atk'); return; }
  if (now - lastAtkStartT < ATK_MIN_GAP) { bufferInput('atk'); return; }   // 연타 바닥(위 주석)
  // ★콤보 창이 살아 있으면 다음 단수로 잇는다. 창 밖이면 새 연격이라 단수를 끊는다.
  //   이 분기가 "치고 빠졌다가 다시 붙어도 2타·3타로 이어진다"를 만든다.
  //   ★수면참·횡일섬에서 이어 나온 Z 는 **새 연격**이다(기술 이름이 남으면 안 된다).
  const fromSkill = attacking && atkClip && atkClip !== 'Attack';
  if (!fromSkill && (attacking || now < comboWindow)) comboStep = Math.min(2, comboStep + 1);
  else { comboStep = 0; resetCombo(null); }
  // ★21차. 궁수 Attack 은 클립 하나에 쏘기 한 번이라 **단수라는 게 없다.**
  //   표(ATK_STEP_T_BOW)가 세 칸 다 같은 값이라 그림은 어차피 같지만, 내부 카운터가
  //   「3타」를 세고 있으면 언젠가 그 수를 읽는 자리가 생겨서 거짓말이 된다.
  const bow = isArcher();
  if (bow) comboStep = 0;
  // 조준. 칼은 사거리(3.2m) 안, 활은 화면 안(13m)을 본다. 규칙은 같다.
  const tgt = bow ? snapTargetBow() : snapTarget();
  attacking = true;
  heavy = false;
  clearBuffer();
  released = false; coil = 1;
  const a = actions.Attack;
  _lowHist.length = 0;
  // ★21차. 재생속도가 캐릭터별로 갈린다(궁수 2.00. 근거는 ARCHER_TS 주석).
  const _ts = atkTimeScale();
  a.reset(); a.setEffectiveTimeScale(_ts); a.play();
  // ★클립 진입점을 단수에 맞춘다. 그냥 0 부터 다시 틀면 세 번 눌러도 **같은 1타**만
  //   세 번 나간다. 진입점은 enemy.js 의 타격 게이트(hot)를 60fps 로 찍어 잰
  //   스윙 시작 시각(경과 ms -> 클립초 = ms/1000*1.35)에서 예비동작 0.09초를 뺀 값이다:
  //   ★2026-08-12 14-베기수정으로 다시 잰 값(위 ATK_STEP_T 주석에 근거를 적었다):
  //     1타 hot 0.134s -> 클립 0.181s -> 진입 0     (클립 머리라 0)
  //     2타 hot 0.433s -> 클립 0.585s -> 진입 0.50
  //     3타 hot 0.883s -> 클립 1.192s -> 진입 1.10
  a.time = atkStepT()[comboStep] || 0;
  // ── 크로스페이드 0.10 -> 0.06 되돌림 (2026-08-13 15-모션수제) ──
  // 수제 클립은 f0 이 Idle 첫 프레임과 같은 자세라 건너뛸 거리가 없다. 그래서
  // 14차가 유령을 누르려고 늘렸던 값을 되돌렸고, **되돌린 쪽이 더 조용했다**
  // (근거·수치는 위 ATK_COMMIT 주석). 아래는 그 14차 기록이다:
  // ── (옛) 크로스페이드 0.06 -> 0.10 (2026-08-12 14-베기수정) ──
  // ★예비동작을 자른 대가로 클립 첫 자세가 **더 감긴 자세**가 됐다. 그래서 Idle 에서
  //   건너뛰는 거리가 늘고, 캐스트 첫 0.12초의 칼끝 속도(= 유령 물보라)가
  //   59.5 -> 81.6 m/s 로 나빠졌다. 크로스페이드를 늘리면 같은 거리를 더 긴 시간에
  //   건너므로 속도가 준다. 실측(mf_commit.mjs 6판, commit_after.json):
  //     Attack 0.06 81.6 -> 0.10 **52.6** m/s (옛 판 59.5 보다도 낮다)
  //     Heavy  0.08 46.9 -> 0.12 33.8 / 0.16 29.1   Wide 0.08 89.8 -> 0.16 **46.2**
  //   ★Heavy 를 0.16 이 아니라 0.12 로 둔 이유: 유령 hot 구간의 끝이 0.135 -> 0.184 로
  //     밀려 CAST_SETTLE(0.20)에 너무 붙는다. 여유 0.065초를 사는 쪽을 골랐다.
  //   ★판정에는 영향이 없다(유령 구간은 X·C 는 CAST_SETTLE 이, Z 는 SWING_GAP 이 흡수).
  if (current && current !== a) current.crossFadeTo(a, 0.06, false);
  current = a;
  const dur = (a.getClip().duration - a.time) / _ts;
  attackEnd = now + dur;
  comboWindow = now + dur * 0.75 + 0.25;   // 다음 단수를 이을 수 있는 창(캔슬 뒤 여유 포함)
  atkClip = 'Attack'; atkStartT = now; atkStruck = false; atkHitT = -99; atkStarts++; lastAtkStartT = now;   // 커밋 구간 시작(S1)
  arrowShot = false;                       // ★21차. 이번 캐스트의 화살은 아직 안 떠났다
  // ★궁수는 전진 스텝을 안 한다. 그건 "칼이 0.4m 모자라서 한 발 붙는" 보정인데
  //   13m 를 쏘는 활에는 뜻이 없고, 활을 당기면서 앞으로 미끄러지는 그림이 된다.
  if (!bow) startStep(tgt);                                // 붙는 전진 스텝(S3)
  // ★여기서 표시를 안 한다. 이 자리가 곧 "허공을 베어도 1 HIT" 의 원인이었다.
}

// 일격기: 3연타와 달리 느리게 모아서 한 번에 크게 벤다. 콤보로 이어지지 않는다.
function tryHeavy() {
  if (!actions.Heavy) return;
  if (isCleared()) return;
  if (dashLeft > 0) { bufferInput('heavy'); return; }
  // ★9차: "휘두르는 중이면 무시"가 곧 심사의 "씹힘인지 버그인지 모르겠다"였다.
  //   커밋 안이면 **버퍼에 담고**(캔슬 프레임에 자동으로 나간다), 회복 구간이면
  //   그 자리에서 끊고 나간다. 어느 쪽도 아니면 그때만 거부 피드백을 낸다.
  if (attacking) {
    if (!canCancelAttack(gameT)) { bufferInput('heavy'); return; }
    attacking = false; atkClip = null;
  }
  const tgt = snapTarget();   // 공격 방향 스냅(tryAttack 주석 참고)
  const now = gameT;
  clearBuffer();
  sfx.heavySwing();
  attacking = true; heavy = true; comboStep = 0;
  resetCombo('수면참');      // 이번 연격의 이름. 명중하면 옆에 누적 수가 붙는다
  released = false; coil = 1;
  const a = actions.Heavy;
  _lowHist.length = 0;
  a.reset(); a.setEffectiveTimeScale(1.15); a.play();
  // 크로스페이드 0.12 -> 0.08 되돌림 (2026-08-13. 근거는 tryAttack 의 같은 자리 주석)
  if (current && current !== a) current.crossFadeTo(a, 0.08, false);
  current = a;
  const dur = a.getClip().duration / 1.15;
  attackEnd = now + dur;
  comboWindow = 0;                       // 콤보 입력 안 받음
  atkClip = 'Heavy'; atkStartT = now; atkStruck = false; atkHitT = -99; atkStarts++; lastAtkStartT = now;   // 커밋 구간 시작(S1)
  startStep(tgt);                                         // 붙는 전진 스텝(S3)
  showSkill(comboLabel);                 // 기술 이름은 지금 뜬다. 명중하면 옆에 수가 붙는다
}

// 횡일섬: 45도로 눕힌 칼을 가로로 크게 쓸어 벤다. 골반까지 돌아서 사거리가 넓다.
function tryWide() {
  if (!actions.Wide) return;
  if (isCleared()) return;
  if (dashLeft > 0) { bufferInput('wide'); return; }
  if (attacking) {                            // 규칙은 tryHeavy 와 같다
    if (!canCancelAttack(gameT)) { bufferInput('wide'); return; }
    attacking = false; atkClip = null;
  }
  const tgt = snapTarget();   // 공격 방향 스냅(tryAttack 주석 참고)
  const now = gameT;
  clearBuffer();
  sfx.heavySwing();
  attacking = true; heavy = true; comboStep = 0;   // heavy 플래그 = 궤적 확대
  resetCombo('횡일섬');      // 이번 연격의 이름. 명중하면 옆에 누적 수가 붙는다
  released = false; coil = 1;
  const a = actions.Wide;
  _lowHist.length = 0;
  a.reset(); a.setEffectiveTimeScale(1.2); a.play();
  // 크로스페이드 0.16 -> 0.08 되돌림 (2026-08-13. 근거는 tryAttack 의 같은 자리 주석)
  if (current && current !== a) current.crossFadeTo(a, 0.08, false);
  current = a;
  const dur = a.getClip().duration / 1.2;
  attackEnd = now + dur;
  comboWindow = 0;
  atkClip = 'Wide'; atkStartT = now; atkStruck = false; atkHitT = -99; atkStarts++; lastAtkStartT = now;   // 커밋 구간 시작(S1)
  startStep(tgt);                                        // 붙는 전진 스텝(S3)
  showSkill(comboLabel);                 // 기술 이름은 지금 뜬다. 명중하면 옆에 수가 붙는다
}

// ---------- 콤보 · 명중 표시 ----------
// ★v72 QA #10 이 두 가지를 한꺼번에 잡아냈다.
//   (1) 허공을 베어도 "1 HIT" 이 떴다. 스윙을 **시작할 때** 띄우고 있었기 때문이다.
//       HIT 은 "맞았다"는 주장이므로 **칼이 닿은 프레임**에만 떠야 한다.
//   (2) 3연타의 2·3타에서 표시가 안 바뀌었다. tryAttack 의 콤보 진행 분기가
//       showCombo 앞에서 return 했다. 이제 표시는 명중 쪽이 하므로 그 분기와 무관하다.
//
// 표시 규칙
//   큰 글자 = 콤보 단수(1·2·3 HIT) 또는 기술 이름(수면참·횡일섬).
//   작은 글자 = 이번 연격에서 실제로 벤 **누적 명중 수**. 단수보다 많을 때만 붙는다
//               (광역타로 한 번에 여럿 베면 "2 HIT 명중 5" 처럼 읽힌다).
//
// ── ★타수 표시 스위치 (18차, 오너 지시 「때릴때 1타 2타 이런거 안뜨게해」) ──
// 위 표시 규칙 중 **명중 쪽(showHit)만** 끈다. 이 한 줄이 손잡이다 - true 로 되돌리면
// 18차 이전이 한 글자도 안 다르게 복원된다.
//   끄는 것: 화면 한가운데 위쪽에 뜨던 「1타」·「2타」·「3타」 와 그 옆 작은 「명중 6」.
//   안 끄는 것(전부 그대로 산다):
//     · 내부 누적 comboHits · 연격 단수 comboStep · 데미지 숫자 · 처치 수 · 체력바.
//     · atkHitT(명중 확정 캔슬의 기준점) - 이건 게임 규칙이라 표시와 무관하게 찍는다.
const COMBO_UI_ON = false;
// ── ★기술 이름 콜아웃 스위치 (18차 후속, 오너 지시 「스킬 쓸때 화면 가운데 스킬명뜨고그런거 안나오게..」) ──
// 위 스위치가 남겨 뒀던 **나머지 절반**이다. 두 지시가 합쳐져 #combo 판은 이제
// **아무것도 안 쓴다** - 판(div)과 수명 코드는 롤백을 위해 그대로 둔다(아래 ★참고).
//   끄는 것: X 수면참 · C 횡일섬 을 **입력한 순간** 화면 가운데 위쪽에 뜨던
//            「스킬 / 수면참 / 물의 一」 카드(ui.js 의 dressCombo 가 씌우던 그 판).
//   안 끄는 것: 기술 자체(모션·이펙트·피해·쿨다운)·하단 스킬 칩(X·C)·거부 흔들림.
//              comboLabel 도 그대로 세운다 - resetCombo 는 표시가 아니라 **연격 상태**다.
// ★두 스위치를 하나로 합치지 않는다. 오너 지시가 두 건이라 되돌릴 때도 따로 되돌려야 한다.
const SKILL_CALLOUT_ON = false;
const comboEl = document.getElementById('combo');
let comboT = 0;
let comboHits = 0;                 // 이번 연격에서 누적된 명중 수
let comboLabel = null;             // 기술 이름. 평타 연격은 null
// 새 연격이 시작될 때 누적을 끊는다. 이걸 안 하면 숫자가 판 내내 불어난다.
function resetCombo(label) {
  comboHits = 0;
  comboLabel = label || null;
}
// 기술 이름은 **입력한 순간** 뜬다. "이 기술이 나갔다"는 알림이라 허공에 그어도 거짓이 아니다.
function showSkill(label) {
  if (!SKILL_CALLOUT_ON) return;   // 오너 지시. 부르는 자리(tryHeavy·tryWide)는 안 건드린다
  comboEl.textContent = label;
  comboT = 0.9;
}
// 칼이 닿은 그 프레임에 부른다(잡몹 onHit · 보스 hit 둘 다).
function showHit() {
  comboHits++;
  atkHitT = gameT;                 // 명중 확정 캔슬의 기준점(canCancelAttack 1번 규칙)
  if (!COMBO_UI_ON) {
    // ★기술 콜아웃의 **수명만** 원래대로 이어 준다. 옛 코드는 여기서 comboT 를 0.9 로
    //   다시 채웠고, 그래서 기술 판이 입력 0.9초 + 명중 0.9초로 살았다. 그 길이를
    //   건드리면 이번 작업(타수 지우기)이 남의 연출까지 짧게 만드는 회귀가 된다.
    // ★단, **이미 꺼진 판은 안 되살린다.** 조건 없이 채우면 평타를 때릴 때 직전에
    //   썼던 기술 이름이 유령처럼 다시 뜬다(#combo 는 글자를 지우지 않고 투명해질 뿐이다).
    // ★후속 지시로 SKILL_CALLOUT_ON 까지 꺼진 지금은 comboT 가 영영 0 이라 이 줄이
    //   아무 일도 안 한다. 그래도 남긴다 - 콜아웃만 되살리는 롤백에서 다시 필요하다.
    if (comboLabel && comboT > 0) comboT = 0.9;
    return;
  }
  const step = comboStep + 1;
  // ★v96 회귀 수정. 큰 글자가 「1 HIT」(영문)인데 그 옆 작은 글자는 「명중 3」(국문)이라
  //   한 줄 안에서 언어가 갈렸다(심사 지적). 국문으로 통일한다 - 「3타 · 명중 5」.
  const head = comboLabel || (step + '타');
  const base = comboLabel ? 1 : step;
  comboEl.innerHTML = head + (comboHits > base ? '<i>명중 ' + comboHits + '</i>' : '');
  comboT = 0.9;
}

// ---------------------------------------------------------------- 화면 되먹임 (9차 신설)
// 심사 격차 두 개를 한 덩어리로 처리한다.
//   7위 "어디서 맞았는지 모른다"  -> 맞은 **방향**으로 붉은 비네트가 쏠린다
//   8위 "씹힘인지 버그인지 모른다" -> 못 쓰는 입력에 칩 흔들림 + 낮은 거부음
// ★DOM 은 여기서 만든다(ui.js 는 다른 파일 소유다). 스타일도 여기 한 장에 담는다.
//   ui.js 가 만든 스킬 칩(#uiSkills .sk)에는 **클래스만 얹는다**(구조를 안 건드린다).
const fxStyle = document.createElement('style');
fxStyle.id = 'mainFxStyle';
fxStyle.textContent = [
  // 방향 비네트: 화면 전체를 덮는 판 하나를 돌려 쓴다(맞을 때마다 각도만 바꾼다).
  '#hurtDir{position:fixed;inset:0;z-index:8;pointer-events:none;opacity:0;',
  '  transition:opacity .26s ease-out;mix-blend-mode:normal}',
  '#hurtDir.on{opacity:1;transition:opacity .06s linear}',
  // ── 피격 비네트 상한 (v96 회귀 수정) ──
  // 심사: "체력 20 에서 붉은 비네트가 너무 진해 둘러싼 적이 안 보인다."
  // 진원지는 enemy.js 의 #eHurt 인데 그 파일은 못 건드린다(소유가 다르다). 그래서
  // **여기서 덮는다** - 이 style 이 나중에 붙고 선택자도 한 단 세다(body #eHurt).
  //   옛 값 inset 0 0 130px 30px rgba(200,20,40,.85) 은 번짐 130 + 퍼짐 30 이라
  //   붉은 물이 화면 위아래 끝에서 각각 160px(720 중 22%씩, 합쳐 44%)까지 들어왔고,
  //   체력이 낮으면 계속 맞으므로 그 상태가 **상시**가 된다.
  //   퍼짐을 0 으로 두고 번짐만 남기면 가장자리 8% 만 물들고 중앙은 통째로 맑다.
  //   ★알파(0.85 -> 0.52)도 같이 내린다. 인라인 opacity(피격 세기)는 enemy.js 가
  //     쥐고 있어서 못 만지므로, 만질 수 있는 것은 그림자의 색·크기뿐이다.
  'body #eHurt{box-shadow:inset 0 0 62px 0 rgba(196,26,44,.52)}',
  // 거부 흔들림. 칩을 좌우로 두 번 튕긴다(0.22초). 색은 안 건드린다 - 흔들림만으로 읽힌다.
  '@keyframes mainDeny{0%{transform:translateX(0)}18%{transform:translateX(-4px)}',
  '  42%{transform:translateX(4px)}66%{transform:translateX(-2px)}100%{transform:translateX(0)}}',
  '#uiSkills .sk.deny{animation:mainDeny .22s ease-out}',
].join('\n');
document.head.appendChild(fxStyle);

const hurtDirEl = document.createElement('div');
hurtDirEl.id = 'hurtDir';
document.body.appendChild(hurtDirEl);
let hurtDirT = 0;
// 맞은 방향(월드 x,z)을 화면 각도로 바꿔 그쪽 가장자리를 붉게 물들인다.
// ★화면 각도로 바꾸는 이유: 쿼터뷰라 월드 방향과 화면 방향이 다르다. 월드 그대로 쓰면
//   "왼쪽에서 맞았는데 화면은 위가 붉어지는" 어긋남이 난다. screenAngle 은 아래
//   요괴 블록에서 이미 쓰는 함수와 같은 것을 쓴다(두 벌이 되면 반드시 갈라진다).
function hurtFrom(sx, sz) {
  const p = root.position;
  const sa = screenAngle(p.x, p.y + charH * 0.5, p.z, sx - p.x, 0, sz - p.z);
  // ── ★맞았을 때의 화면 반응 (17차) ──
  // 신규유저 지적: "맞을 때도 붉은 비네트뿐이라 위협감이 없다." 비네트는 **어디서**
  // 맞았는지만 말하고 **맞았다**는 말을 안 한다. 그래서 카메라를 때린 놈 반대쪽으로
  // 한 번 민다 — 몸이 밀리는 넉백(enemy.js PLAYER_KB)과 같은 방향이라 한 사건으로 읽힌다.
  // ★sa.ang 은 '나 -> 때린 놈' 방향이므로 π 를 더해 반대로. 5.5px 은 처치(4.6)보다
  //   살짝 크다. 내가 맞는 건 더 큰 사건이어야 한다.
  camPunchScreen(5.5, sa.ang + Math.PI, 0.26);
  // CSS linear-gradient 의 0deg 는 "아래에서 위로"다. 화면 각(오른쪽 0, 위 +90)에서
  // 90 을 빼면 그대로 맞는다.
  const deg = 90 - sa.ang * 180 / Math.PI;
  // ── 붉은 워시 총량 (v94. 9A-1 지형 요청) ──
  // 지형 에이전트 실측: 피격 중 화면 워시가 **지면의 R-G 를 +20/255** 밀어서 색 측정이
  // 통째로 오염됐다(측정용 컷을 한 장 버렸다). 그건 곧 플레이어 눈에도 맵 색이
  // 순간 다른 맵처럼 보였다는 뜻이다.
  // 고치는 방향: 세기가 아니라 **면적**을 줄인다. 방향을 알리는 일은 가장자리 띠가
  // 다 하고, 화면 절반까지 걸쳐 있던 꼬리는 아무 정보도 안 준다.
  //   최대 알파 0.68 -> 0.44 · 꼬리 도달 50% -> 30% · 지속 0.42 -> 0.34초
  hurtDirEl.style.background =
    'linear-gradient(' + deg.toFixed(1) + 'deg, rgba(150,16,16,0.44) 0%, ' +
    'rgba(150,16,16,0.20) 12%, rgba(150,16,16,0) 30%)';
  hurtDirEl.classList.add('on');
  hurtDirT = 0.34;
}
// 방향을 모르는 피격(출처가 사라진 경우)은 사방으로 옅게. 없던 일로 하지 않는다.
function hurtNoDir() {
  hurtDirEl.style.background =
    'radial-gradient(ellipse at 50% 50%, rgba(150,16,16,0) 58%, rgba(150,16,16,0.38) 100%)';
  hurtDirEl.classList.add('on');
  hurtDirT = 0.34;
}

// ── 거부 피드백 ──
// kind: 'heavy' | 'wide' | 'dash'
let lastDenyT = -99;
function deny(kind) {
  const now = performance.now();
  if (now - lastDenyT < 140) return;      // 연타로 누르면 소리가 뭉친다
  lastDenyT = now;
  sfx.deny();
  const sel = kind === 'heavy' ? '[data-k="Heavy"]' : kind === 'wide' ? '[data-k="Wide"]' : '[data-k="Dash"]';
  const el = document.querySelector('#uiSkills ' + sel);
  if (!el) return;
  el.classList.remove('deny');
  void el.offsetWidth;                    // 같은 프레임에 뺐다 붙이면 애니가 다시 안 돈다
  el.classList.add('deny');
}

// ── Space 칸 ──
// ★ui.js 가 만든 #uiSkills 안에 한 장을 더 붙인다(구조·CSS 를 그쪽 것과 공유한다).
//   ui.js 의 updateSkills 는 Basic/Heavy/Wide 세 노드만 만지므로 서로 안 밟는다.
//   ui.js 가 아직 칩을 안 만들었을 수 있어 잠깐 기다렸다 붙인다(없으면 조용히 포기).
// ★17차: 회피가 잠겼으므로(DASH_ON) 같은 자리에 **점프 칸**을 세운다. 이름표만 바꾸는 게
//   아니라 data-k 를 Jump 로 준다 - 그래야 ui.js 의 회피 전용 처리(쿨 덮개·남은 초)가
//   이 칸을 아예 안 건드린다(그쪽은 [data-k="Dash"] 만 찾는다). 점프는 쿨이 없으니
//   덮개도 숫자도 안 얹고 늘 밝다(ui.js 의 베기 칸과 같은 규칙).
// ★구조는 ui.js 의 slotHtml 과 1:1 로 맞춘다(첫 자식 <i class="cd">, 그 다음 <b class="cds">).
let dashChip = null;
(function mountSpaceChip(tries = 0) {
  const host = document.getElementById('uiSkills');
  if (!host) { if (tries < 40) setTimeout(() => mountSpaceChip(tries + 1), 150); return; }
  // ★26차: Z 봉인이면 계기판의 Z(베기) 칸을 접는다. X·C 는 flex 라 그대로 왼쪽 정렬.
  //   ui.js 의 updateSkills 가 이 노드를 계속 만져도 display:none 이라 안 보인다.
  if (!SKILL_Z_ON) {
    const zSlot = host.querySelector('[data-k="Basic"]');
    if (zSlot) zSlot.style.display = 'none';
  }
  const d = document.createElement('div');
  d.className = 'sk rdy';
  d.dataset.k = DASH_ON ? 'Dash' : 'Jump';
  d.innerHTML = '<i class="cd"></i><b class="cds"></b><span class="key">Space</span>'
    + '<span class="nm">' + (DASH_ON ? '회피' : '점프') + '</span>';
  host.appendChild(d);
  if (DASH_ON) dashChip = d;      // 매 프레임 쿨을 칠할 대상. 점프 칸에는 칠할 것이 없다
})();

// ---------- 루프 ----------
const fwd = new THREE.Vector3(), rightv = new THREE.Vector3(), move = new THREE.Vector3();
const swordA = new THREE.Vector3(), swordB = new THREE.Vector3();
const camTarget = new THREE.Vector3();

// ---------------------------------------------------------------------------
// ★이동 신뢰성 (17차. 신규유저 비평 1순위 "게임을 못 하게 만드는 유일한 요인")
// ---------------------------------------------------------------------------
// 진단부터 적는다. 비평의 세 그림은 **셋 다 같은 한 가지**였다.
//   ① 같은 자리에서 40초 넘게 못 움직임(걷기 애니만 반복) 3회
//   ② 캐릭터가 벽 위에 올라타 맵 지붕을 걸음(07_standing_on_walls_zoomout.png)
//   ③ 벽 틈에 껴 화면이 통째로 벽·캐릭터로 덮임(12·13)
//
// ★맵 벽은 칸 한 줄마다 상자로 굽는다. 앞벽(1.45m)과 뒷벽(3.60m)이 **따로** 상자가
//   되고 상자는 칸 경계에서 0.22m 씩 안으로 물러나 있다(level2.json colliderNote).
//   그래서 **보이는 벽 속에 0.22~0.44m 짜리 빈 금**이 생긴다. 실측: 이 맵에 71 군데,
//   총 길이 420.8m. 사람 지름은 0.70m 라 절대 못 들어가는 폭인데, 금은 콜라이더가
//   아니라 콜라이더 **사이**라서 충돌기는 "여기는 밖"이라고 답한다.
//
// ★level.slide 는 목적지로 **먼저 옮기고 나서** 밀어내는 방식이고(level.js 소유),
//   밀어낼 때 "파고든 깊이가 얕은 축"으로 뺀다. 한 프레임 이동이 상자 안쪽으로 깊이
//   들어가면 그 규칙이 **뒤집힌다** — 되돌아 나오는 대신 옆(=금 쪽)으로 밀린다.
//   금 안에 들어가면 양쪽 상자가 서로 반대로 밀어서 밀어내기 3회가 끝나도 못 나온다.
//   실측(16방향 x 설 수 있는 자리 21071):
//       걷기 1.71m/s (한 프레임 0.029m)   -> 벽 속 착지 0.00%
//       달리기 3.20   (0.053m)            -> 0.26%
//       달리기 + 프레임 드롭(dt 상한 0.05) -> 0.81%
//       ★대시 3.5m/0.18s (한 프레임 0.885m) -> 18.13%
//   전진 스텝(0.09m)·넉백(0.087m)은 0%. 즉 **대시 한 번이 여덟 자리 중 하나에서**
//   사람을 벽 속에 박는다. 박힌 자리에서 8방향 1.5초씩 눌러 본 실측 이동은 0.00m다
//   (= ①의 40초 정지). 그리고 앞벽이 1.45m 라 **끼인 사람의 상반신만 벽 위로 나온다**
//   = ②의 "지붕 보행". 실측 y 는 0.02(바닥)였다 — 한 번도 올라간 적이 없다.
//   ③도 같은 자리다: 금 격자점의 30.9% 가 카메라 광선이 벽에 막히는 자리다
//   (제대로 선 자리에서는 0.8%).
//
// ★고치는 자리는 main.js 뿐이다(level.js·level2.json 은 소유 밖). 두 겹으로 막는다.
//   ① moveBy  = 한 프레임 이동을 0.09m 씩 잘라 민다. 상자 안쪽으로 깊이 들어갈 일이
//                없어지니 밀려나는 축이 안 뒤집힌다. 그래도 조각의 결과가 벽 속이면
//                그 조각을 버리고 x축/z축으로 갈라 미끄러뜨린다(진짜 슬라이드).
//   ② unwedge = 그래도 어떤 경로로든 벽 속에 있으면 제일 가까운 설 수 있는 자리로
//                빼낸다. level.pushOut 은 같은 3회 밀어내기라 금 안에서는 진동만 한다.
const PR = level.PLAYER_RADIUS;
// '벽 속인가'를 볼 때 쓰는 반경. 벽에 붙어 선 정상 상태는 면에서 정확히 PR 만큼
// 떨어져 있으므로, 그걸 벽 속으로 오판하지 않게 6% 줄여 잡는다.
const WEDGE_R = PR * 0.94;
const MOVE_SUB = 0.09;          // m. 조각 하나의 최대 길이(제일 좁은 금 0.22m 의 절반 이하)
const MOVE_SUB_MAX = 24;        // 한 프레임 조각 수 상한(대시 최대 0.885m -> 10조각)
const _mv = { x: 0, z: 0, hit: false };
let moveVeto = 0, moveWedge = 0, moveMaxY = 0, moveMaxGY = 0;   // 진단 계수기

// 한 프레임의 이동을 실제로 놓는 **유일한 문**. 걷기·코스트·대시·전진스텝이 전부 여기로 온다.
// 규칙이 갈라지면 "대시로만 벽에 박히는" 이번 같은 일이 또 난다.
function moveBy(dx, dz) {
  const d = Math.hypot(dx, dz);
  if (!(d > 1e-9)) return 0;
  const x0 = root.position.x, z0 = root.position.z;
  const n = Math.min(MOVE_SUB_MAX, Math.max(1, Math.ceil(d / MOVE_SUB)));
  const sx = dx / n, sz = dz / n;
  for (let i = 0; i < n; i++) {
    const px = root.position.x, pz = root.position.z;
    let st = level.slide(px, pz, sx, sz, PR, _mv);
    let nx = st.x, nz = st.z;
    if (level.blocked(nx, nz, WEDGE_R)) {
      // 이 조각이 사람을 벽 속으로 넣었다. 버리고 축을 갈라 미끄러진다.
      moveVeto++;
      let ok = false;
      if (sx !== 0) {
        st = level.slide(px, pz, sx, 0, PR, _mv);
        if (!level.blocked(st.x, st.z, WEDGE_R)) { nx = st.x; nz = st.z; ok = true; }
      }
      if (!ok && sz !== 0) {
        st = level.slide(px, pz, 0, sz, PR, _mv);
        if (!level.blocked(st.x, st.z, WEDGE_R)) { nx = st.x; nz = st.z; ok = true; }
      }
      if (!ok) break;            // 두 축 다 벽 속이다. 이 프레임은 여기까지.
    }
    root.position.x = nx; root.position.z = nz;
  }
  return Math.hypot(root.position.x - x0, root.position.z - z0);
}

// ── 벽 속에서 빼내기 ──
// ★level.pushOut 을 안 쓴다. 그것도 같은 '밀어내기 3회'라 0.44m 금 안에서는 양쪽
//   상자가 서로 반대로 밀어 제자리 진동만 한다(실측 8방향 1.5초 이동 0.00m).
//   그래서 밀지 않고 **가장 가까운 설 수 있는 자리를 찾아 그리로 걸어 나간다.**
// ★출구를 고를 때 **가는 길**까지 본다. 안 보면 1.56m 짜리 돌벽을 뚫고 반대편으로
//   순간이동하는 그림이 나온다(금을 따라 나가는 길과 거리가 비슷하다).
const UNWEDGE_SPD = 7.0;        // m/s. 한 박자(0.2~0.5초)에 빠져나온다
const UNWEDGE_MAX = 4.0;        // m. 이보다 먼 출구는 안 찾는다
const UNWEDGE_PATH_R = 0.12;    // m. 길 검사 반경(금 반폭 0.22 보다 작다)
const _uw = { x: 0, z: 0, on: false };
function unwedgePathOk(x0, z0, x1, z1) {
  const d = Math.hypot(x1 - x0, z1 - z0);
  const n = Math.max(2, Math.ceil(d / 0.08));
  for (let i = 1; i < n; i++) {
    const t = i / n;
    if (level.blocked(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, UNWEDGE_PATH_R)) return false;
  }
  return true;
}
function unwedgeTarget(x, z) {
  // 고리를 가까운 쪽부터 훑는다. 처음 찾은 자리가 곧 최단 출구다.
  let fallback = null;
  for (let d = 0.15; d <= UNWEDGE_MAX; d += 0.10) {
    const steps = Math.max(16, Math.round(d * 20));
    for (let i = 0; i < steps; i++) {
      const a = (i / steps) * Math.PI * 2;
      const nx = x + Math.sin(a) * d, nz = z + Math.cos(a) * d;
      if (level.blocked(nx, nz, PR * 1.02)) continue;
      if (unwedgePathOk(x, z, nx, nz)) return { x: nx, z: nz };
      if (!fallback) fallback = { x: nx, z: nz };
    }
  }
  return fallback;               // 길이 막혀도 벽 속에 두는 것보다는 낫다
}
function unwedge(dt) {
  if (!level.blocked(root.position.x, root.position.z, WEDGE_R)) { _uw.on = false; return false; }
  moveWedge++;
  if (_uw.on && level.blocked(_uw.x, _uw.z, PR * 1.02)) _uw.on = false;   // 목표가 상했다
  if (!_uw.on) {
    const t = unwedgeTarget(root.position.x, root.position.z);
    if (!t) return false;        // 나갈 자리가 없다. 그냥 둔다(움직임은 막지 않는다)
    _uw.x = t.x; _uw.z = t.z; _uw.on = true;
  }
  const dx = _uw.x - root.position.x, dz = _uw.z - root.position.z;
  const d = Math.hypot(dx, dz);
  if (d < 1e-4) { _uw.on = false; return true; }
  const k = Math.min(d, UNWEDGE_SPD * Math.max(dt, 1 / 240));
  // ★여기서는 level.slide 를 안 지난다. 지금 자리가 이미 벽 속이라 밀어내기가 또
  //   금 쪽으로 되민다. 목표는 이미 '설 수 있는 자리'로 검증돼 있다.
  root.position.x += dx / d * k;
  root.position.z += dz / d * k;
  return true;
}

// ── 카메라 가림 완화 (camBase 층만) ──
// ★손맛 층(camPunch·흔들림)은 한 줄도 안 건드린다. 17차 타격감 팩이 갈라 둔 그 경계다.
// 카메라는 yaw 고정이라 시야를 막는 것은 **플레이어 남쪽의 높은 것**뿐이다.
// 실측: 제대로 선 자리 21071 중 168(0.8%)이 가슴이 가린다 — 전부 중앙 회랑 기둥
// (x=±3.2, h=3.57) 바로 북쪽이다. 벽 속(금)에서는 30.9% 라 그쪽은 위 두 겹이 없앤다.
// 대응은 **각을 조금 세우는 것** 하나뿐이다(당겨도 3m 앞의 기둥은 안 비킨다).
//   +0.28rad(49.3° -> 65.3°) 면 168 중 96 자리가 열린다. 그 이상은 부감이 돼서 안 쓴다.
const CAM_LIFT_MAX = 0.28;      // rad. 가릴 때 더 세우는 최대 각
const CAM_LIFT_HOLD = 0.20;     // s. 이만큼 계속 가려야 든다(기둥을 스칠 때는 안 든다)
const CAM_LIFT_UP = 3.0;        // 1/s. 드는 속도
const CAM_LIFT_DN = 2.0;        // 1/s. 내리는 속도
const CAM_MIN_GAP = 6.0;        // m. camBase 가 플레이어에 이보다 가까워지지 않는다
let camLift = 0, camOccT = 0;
let camTallCache = null;
// ★문턱을 charH 로 잡으면 안 된다. charH 는 캐릭터 glb 가 도착해야 1.75 가 되는데
//   이 목록은 한 번 굽고 캐시하므로 **모델보다 먼저 불리면 기준이 2.4 로 굳는다.**
//   가슴(1.085)보다 낮은 것은 어차피 못 가리므로 고정 상수로 거른다.
const CAM_OCC_MIN_H = 1.20;
function camTall() {
  if (camTallCache) return camTallCache;
  const lv = level.data();
  camTallCache = ((lv && lv.colliders) || []).filter(c => (c.h || 0) > CAM_OCC_MIN_H);
  return camTallCache;
}
function camOccluded(px, pz, pit) {
  const list = camTall();
  if (!list.length) return false;
  // ★placeCamera 가 보는 지점과 **같은 높이**를 쓴다(그쪽은 지면과 무관한 절대 y 다).
  //   여기서만 지면을 더하면 단 위에서 판정이 어긋난다.
  const chest = charH * 0.62;
  const tx = px - Math.sin(yaw) * lead, tz = pz - Math.cos(yaw) * lead;
  const dx = tx + Math.sin(yaw) * Math.cos(pit) * dist - px;
  const dz = tz + Math.cos(yaw) * Math.cos(pit) * dist - pz;
  const dy = Math.sin(pit) * dist;
  const horiz = Math.hypot(dx, dz) || 1;
  const far = Math.min(1, 7.0 / horiz);   // 7m 넘으면 광선이 제일 높은 벽보다 위다
  for (let i = 1; i <= 18; i++) {
    const t = far * i / 18;
    const sx = px + dx * t, sz = pz + dz * t, sy = chest + dy * t;
    for (let j = 0; j < list.length; j++) {
      const c = list[j];
      if (sy >= c.h) continue;
      if (c.type === 'circle') {
        const ex = sx - c.x, ez = sz - c.z;
        if (ex * ex + ez * ez < c.r * c.r) return true;
      } else if (Math.abs(sx - c.x) < c.hx && Math.abs(sz - c.z) < c.hz) return true;
    }
  }
  return false;
}
function updateCamLift(rawDt) {
  // ★판단은 **기본 각**으로 한다. 든 각으로 재면 드는 순간 조건이 풀려서 오르내림이
  //   반복된다(카메라가 숨을 쉰다). 기본 각이 막혀 있는 동안만 들고 있는다.
  const occ = camOccluded(root.position.x, root.position.z, pitch);
  if (occ) camOccT += rawDt; else camOccT = 0;
  const want = (camOccT >= CAM_LIFT_HOLD) ? CAM_LIFT_MAX : 0;
  const k = Math.min(1, rawDt * (want > camLift ? CAM_LIFT_UP : CAM_LIFT_DN));
  camLift += (want - camLift) * k;
  if (camLift < 1e-4) camLift = 0;
}

// ---------------------------------------------------------------------------
// ★카메라 오프셋 레이어 (17차 타격감 팩)
// ---------------------------------------------------------------------------
// 카메라의 자리를 **두 층으로 갈랐다.**
//   camBase        = 이동·추적이 정하는 자리. 여기만 보간한다.
//   camPunch/흔들림 = 손맛이 그 위에 얹는 오프셋. camBase 를 절대 안 건드린다.
//
// ★왜 갈랐나 — 실측으로 잡은 버그다(renders/history/v99_wave17/hitfeel/).
//   예전 코드는 `camera.position.lerp(want, k)` 로 보간하고 **그 결과에 흔들림을
//   더했다.** 다음 프레임의 lerp 출발점이 곧 '흔들린 자리'라서, 흔들림이 보간 루프
//   안으로 새어 들어가 1차 IIR 저역통과(극 0.8)를 탄다. 그 필터가 뭉갠 것이
//   히트스톱이었다: 세계는 멈췄는데(게임 dt 17ms -> 0.85ms) 카메라만 계속 흘러서
//   **멈춘 프레임의 화소 차분이 안 멈춘 프레임의 295%** 로 나왔다(배경 띠 0.86 -> 7.9).
//   비평가의 "히트스톱 0 · 카메라 반응 0.00" 두 지적이 같은 뿌리에서 나온 것이다.
//
// ★이 층은 이동 카메라 로직과 **절연**이다. 이동·추적을 고치는 사람은 camBase 만
//   보면 되고(_camWant 를 어떻게 만들든 자유), 손맛은 camPunch 만 만진다. 둘은
//   placeCamera 마지막 두 줄에서 합쳐진다.
const _camWant = new THREE.Vector3();
const camBase = new THREE.Vector3();      // 오프셋이 안 얹힌 '이동 카메라'의 자리
let camBaseInit = false;
// 지금 화면에 걸린 펀치 오프셋(월드 m)과 그 방향·크기·수명.
const camPunch = new THREE.Vector3();
const _punchDir = new THREE.Vector3();
const _pRt = new THREE.Vector3(), _pUp = new THREE.Vector3();
let punchAmp = 0, punchLeft = 0, punchDur = 0.001;
// 화면 px 를 카메라 거리 평면의 m 로. fov·dist·캔버스 높이가 다 반영된다.
function pxToMeters(px) {
  const h = (cv && (cv.clientHeight || cv.height)) || 640;
  return px * (2 * Math.tan(camera.fov * Math.PI / 360) * dist) / h;
}
// ── 카메라 펀치 ──
// px = 화면 픽셀 / ang = 화면 각도(screenAngle 이 주는 그 각. 오른쪽 0, 위 +) /
// dur = 되돌아오는 시간(초).
// ★귀에 걸리는 흔들림이 아니라 **한 번 밀렸다 앉는 변위**다. 15Hz 로 떠는 흔들림은
//   차분에서는 크게 잡히지만 눈에는 "잡음"으로 읽히고, 방향이 없어서 "어디를 베었나"를
//   말해 주지 못한다. 베기 방향으로 한 번 미는 쪽이 같은 진폭에서 훨씬 세게 읽힌다.
function camPunchScreen(px, ang, dur) {
  const m = pxToMeters(px);
  if (!(m > 0)) return;
  // 진행 중인 펀치보다 약하면 무시(약한 게 강한 걸 덮으면 김이 샌다. feel.shake 와 같은 규칙)
  const cur = punchLeft > 0 ? punchAmp * (punchLeft / punchDur) : 0;
  if (m < cur) return;
  _pRt.setFromMatrixColumn(camera.matrixWorld, 0);
  _pUp.setFromMatrixColumn(camera.matrixWorld, 1);
  // screenAngle 은 x 를 aspect 로 늘려서 각을 낸다. 되돌릴 때 그만큼 나눠야 방향이 맞는다.
  const asp = camera.aspect || 1;
  _punchDir.copy(_pRt).multiplyScalar(Math.cos(ang) / asp)
           .addScaledVector(_pUp, Math.sin(ang));
  if (_punchDir.lengthSq() < 1e-12) return;
  _punchDir.normalize();
  punchAmp = m; punchDur = Math.max(0.02, dur); punchLeft = punchDur;
}
// ── 흔들림 붙들기 ──
// ★feel.updateShake(0) 으로는 흔들림이 안 선다. feel.js 의 오프셋 식이 누적 시간이
//   아니라 **performance.now() 를 직접 읽기** 때문이다(`const t = performance.now()*0.001`).
//   dt 를 0 으로 줘도 벽시계는 흐르므로 sin 값이 매 프레임 바뀐다 — 실측에서 히트스톱
//   동안 카메라가 17~23px 씩 계속 떨었다. feel.js 는 이번 판 소유가 아니라 못 고친다.
//   그래서 **멈추기 직전 프레임의 오프셋을 붙들어** 쓴다. 0 으로 죽이지 않는 이유는
//   그러면 정지가 시작되는 프레임에 카메라가 흔들림 폭만큼 튀기 때문이다.
// ── ★흔들림 보정 게인 ──
// 위 절연(보간 되먹임 제거)에는 부작용이 하나 딸려 온다. 예전에는 흔들림이 보간
// 루프 안으로 새면서 1차 IIR(극 0.87)을 타서 **화면에 나가는 진폭이 0.62배로 눌려**
// 있었다. 되먹임을 끊으면 같은 feel.shake(amp) 가 그대로 1.0 배로 나간다 = 오너가
// 한 번도 승인한 적 없는 세기다(실측: 프레임간 카메라 이동 최대 7px -> 18px).
// 그래서 옛 화면 세기를 그대로 복원하는 게인을 곱한다. 이 판에서 새로 늘어나는 것은
// **방향성 펀치 하나뿐**이고, 흔들림은 예전 그림 그대로다("과대 금지", 오너).
// ★feel.js 의 shake(amp,dur) 값을 바꾸는 게 아니다. 화면에 얹는 자리에서만 곱한다
//   (feel.js 는 이번 판 소유가 아니다).
const SHAKE_GAIN = 0.65;
const _shakeHold = new THREE.Vector3();
const _shakeOut = new THREE.Vector3();
let shakeHeld = false;
function shakeOffsetFrozen(frozen) {
  if (frozen) {
    if (!shakeHeld) { _shakeHold.copy(feel.shakeOffset()).multiplyScalar(SHAKE_GAIN); shakeHeld = true; }
    return _shakeHold;
  }
  shakeHeld = false;
  return _shakeOut.copy(feel.shakeOffset()).multiplyScalar(SHAKE_GAIN);
}
// frozen = 히트스톱 중. 멈춘 동안에는 펀치도 **그 자리에 붙들려 있어야** 한다.
// (여기서 계속 되돌아오면 '멈춘 프레임'이 다시 움직이는 프레임이 된다)
function updateCamPunch(rawDt, frozen) {
  if (punchLeft <= 0) { camPunch.set(0, 0, 0); return; }
  if (!frozen) punchLeft -= rawDt;
  if (punchLeft <= 0) { punchLeft = 0; camPunch.set(0, 0, 0); return; }
  const k = punchLeft / punchDur;                 // 1 -> 0
  // smoothstep. k=1 근처가 평평해서 **정점에서 한 박자 머물렀다가** 부드럽게 앉는다.
  camPunch.copy(_punchDir).multiplyScalar(punchAmp * k * k * (3 - 2 * k));
}

// ── 카메라 놓기 ──
// ★한 군데서만 놓는다. 루프도, 검증 프로브도 이 함수를 지난다. 두 벌이 되면
//   "프로브가 재는 카메라"와 "화면에 보이는 카메라"가 갈라진다.
// lerpK <= 0 이면 보간 없이 그 자리에 딱 놓는다(프로브·스크린샷용).
// hold = true 면 camBase 도 흔들림도 **한 픽셀도 안 옮긴다**(히트스톱. 배경이 진짜로 선다).
function placeCamera(lerpK, hold) {
  // 바라보는 지점을 캐릭터보다 lead 만큼 **앞으로** 민다. 카메라가 보는 방향의
  // 수평 성분이 (-sin yaw, 0, -cos yaw) 라 그 쪽으로 밀면 캐릭터가 화면 아래로 내려간다.
  camTarget.set(root.position.x - Math.sin(yaw) * lead,
                charH * 0.62,
                root.position.z - Math.cos(yaw) * lead);
  // ★17-이동신뢰성: 가림 완화로 얻은 각을 여기서 한 번만 더한다(camBase 층).
  //   camLift 는 평시 0 이라 안 가려 있을 때의 그림은 옛것과 한 픽셀도 안 다르다.
  const pit = pitch + camLift;
  _camWant.set(camTarget.x + Math.sin(yaw) * Math.cos(pit) * dist,
               camTarget.y + Math.sin(pit) * dist,
               camTarget.z + Math.cos(yaw) * Math.cos(pit) * dist);
  if (!camBaseInit) { camBase.copy(_camWant); camBaseInit = true; }
  else if (hold) { /* 히트스톱: 이동 보간을 통째로 세운다 */ }
  else if (lerpK > 0 && lerpK < 1) camBase.lerp(_camWant, lerpK);
  else camBase.copy(_camWant);
  // ★최소 거리. 지금 식으로는 dist(18~32) 가 곧 거리라 절대 안 걸리지만, 카메라를
  //   만지는 다음 사람이 camBase 를 당겼을 때 **등에 처박히는 그림**은 여기서 막는다.
  //   (비평 ③ "카메라가 등에 처박혀 화면 전체가 캐릭터")
  const gx = camBase.x - camTarget.x, gy = camBase.y - camTarget.y, gz = camBase.z - camTarget.z;
  const gap = Math.sqrt(gx * gx + gy * gy + gz * gz);
  if (gap > 1e-4 && gap < CAM_MIN_GAP) {
    const s = CAM_MIN_GAP / gap;
    camBase.set(camTarget.x + gx * s, camTarget.y + gy * s, camTarget.z + gz * s);
  }
  camera.position.copy(camBase);
  camera.lookAt(camTarget);
  // 오프셋은 lookAt **뒤에** 얹는다. 앞에 얹으면 미는 만큼 시선이 되돌아와 상쇄된다.
  // ★그리고 camBase 에는 안 더한다 — 다음 프레임 보간이 이 오프셋을 먹으면
  //   손맛이 이동 카메라 안으로 새어 들어간다(위 절연 주석).
  camera.position.add(camPunch).add(shakeOffsetFrozen(hold));
  camera.updateMatrixWorld();
  // ★project/unproject 가 쓰는 역행렬까지 여기서 맞춰 둔다. 렌더러가 render() 안에서
  //   갱신하기 때문에, 이걸 안 하면 프로브가 **한 프레임 전 카메라**를 재고
  //   붓질 슬래시 각도도 한 프레임 어긋난다.
  camera.matrixWorldInverse.copy(camera.matrixWorld).invert();
}

// ── 시점 검증 프로브 ──
// "전방 몇 m / 폭 몇 m / 캐릭터가 화면의 몇 % / 원근왜곡비" 를 **화면에서 직접** 잰다.
// 손으로 푼 식이 아니라 실제 투영행렬로 재기 때문에 fov·해상도·종횡비가 다 반영된다.
// ?dev 없이도 열어 둔다(읽기 전용이고, 60fps 로 실제로 도는 판에서 재야 의미가 있다).
const _pv = new THREE.Vector3();
function probeCam() {
  placeCamera(0);
  const gy = level.groundY(root.position.x, root.position.z);
  // 화면의 한 점(NDC)이 지면과 만나는 자리
  const hitGround = (nx, ny) => {
    _pv.set(nx, ny, 0.5).unproject(camera).sub(camera.position);
    if (Math.abs(_pv.y) < 1e-6) return null;
    const t = (gy - camera.position.y) / _pv.y;
    if (t <= 0) return null;                       // 하늘을 보는 픽셀
    return { x: camera.position.x + _pv.x * t, z: camera.position.z + _pv.z * t, t };
  };
  // 전방축(-sin yaw, -cos yaw) 위의 좌표
  const fx = -Math.sin(yaw), fz = -Math.cos(yaw);
  const rx = Math.cos(yaw), rz = -Math.sin(yaw);
  const along = p => (p.x - root.position.x) * fx + (p.z - root.position.z) * fz;
  const side = p => (p.x - root.position.x) * rx + (p.z - root.position.z) * rz;
  const top = hitGround(0, 1), bot = hitGround(0, -1);
  // 캐릭터가 화면 세로의 몇 %
  const foot = _pv.copy(root.position).setY(gy).project(camera).clone();
  const head = _pv.copy(root.position).setY(gy + charH).project(camera).clone();
  const charPct = Math.abs(head.y - foot.y) / 2 * 100;
  // 폭: 플레이어가 선 줄(화면 세로 위치)에서 좌우 끝까지
  const lw = hitGround(-1, foot.y), rw = hitGround(1, foot.y);
  // ── 원근 왜곡비 ──
  // 화면 위끝과 아래끝에 **같은 크기의 것**을 놓았을 때 픽셀 크기가 몇 배 차이 나는가.
  // ★세로 막대로 재면 안 된다. 쿼터뷰에서 세로 막대는 화면 위쪽일수록 카메라 쪽으로
  //   눕는 각이 커져서 오히려 늘어난다(실측 0.89 가 나왔다. 눈에 보이는 왜곡과 반대다).
  //   바닥에 놓인 1m 자(가로)로 재야 벽·바닥이 기우는 정도와 일치하고,
  //   이 값이 레포에 기록된 옛 시점 1.33 과도 맞는다.
  const stick = p => {
    if (!p) return null;
    const a = _pv.set(p.x - rx * 0.5, gy, p.z - rz * 0.5).project(camera).x;
    const b = _pv.set(p.x + rx * 0.5, gy, p.z + rz * 0.5).project(camera).x;
    return Math.abs(b - a);
  };
  const sTop = stick(top), sBot = stick(bot);
  return {
    yaw: +yaw.toFixed(3), pitch: +pitch.toFixed(3), deg: +(pitch * 180 / Math.PI).toFixed(1),
    // ★가림 완화로 지금 더 세워 둔 각. 평시 0 이라 위 두 값이 곧 화면의 각이다.
    lift: +camLift.toFixed(4),
    dist: +dist.toFixed(2), fov: camera.fov, lead: +lead.toFixed(2),
    fwd: top ? +along(top).toFixed(2) : null,
    back: bot ? +(-along(bot)).toFixed(2) : null,
    width: (lw && rw) ? +Math.abs(side(rw) - side(lw)).toFixed(2) : null,
    charPct: +charPct.toFixed(2),
    footPct: +((foot.y + 1) / 2 * 100).toFixed(1),
    bodyPct: +((foot.y + 1) / 2 * 100 + charPct / 2).toFixed(1),
    warp: (sTop && sBot) ? +(sBot / sTop).toFixed(3) : null,
    camY: +camera.position.y.toFixed(2),
    aspect: +camera.aspect.toFixed(3),
  };
}
window.__probe = probeCam;
// 검증용 창구. ?dev 없이도 열어 둔다. 헤디드 브라우저에서 실제 60fps 로 도는 판에
// 플레이어를 원하는 자리에 세워 놓고 찍어야 시점·이펙트를 눈으로 판단할 수 있다.
window.__root = root;
window.__put = (x, z, yaw) => {
  root.position.set(x, level.groundY(x, z), z);
  if (yaw !== undefined) root.rotation.y = yaw;
};
// ── 월드 한 점이 화면 어디에 있나 ──
// ui.js 의 목표 방향 나침반이 쓴다. 손으로 푼 삼각함수가 아니라 **이번 프레임의 실제
// 카메라 행렬**로 재기 때문에 fov·해상도·줌이 바뀌어도 화살표가 안 어긋난다.
// x/y 는 NDC(-1..1, y 는 위가 +), behind 는 카메라 뒤쪽인가. 읽기 전용이다.
const _scrV = new THREE.Vector3();
window.__screen = (x, z, y) => {
  _scrV.set(x, y === undefined ? level.groundY(x, z) + 1.0 : y, z);
  _scrV.applyMatrix4(camera.matrixWorldInverse);
  // 카메라 공간에서 z 가 0 보다 크면 등 뒤다. 이때 투영하면 w 가 음수라 좌우가
  // 뒤집혀 나오므로 부르는 쪽이 뒤집어 써야 한다(그래서 이 값을 같이 준다).
  const behind = _scrV.z > -0.02;
  _scrV.applyMatrix4(camera.projectionMatrix);
  return { x: _scrV.x, y: _scrV.y, behind };
};
window.__feel = feel;
window.__sfx = sfx;
// 프레임 기록. 열 = [벽시계ms, rawDt ms, 게임dt ms, 공격중, 콤보단계,
//                    Attack 클립시각, 스윙번호, 처치수, 콤보창까지 남은시간(음수=열려있음)]
let __rec = null;
window.__recStart = () => { __rec = []; return true; };
window.__recDump = () => { const r = __rec; __rec = null; return r; };
window.__camSet = (o) => {
  if (o.yaw !== undefined) yaw = o.yaw;
  if (o.pitch !== undefined) pitch = o.pitch;
  if (o.dist !== undefined) { dist = o.dist; applyDist(); }   // 안개·그림자 상자도 같이 간다
  if (o.lead !== undefined) lead = o.lead;
  if (o.fov !== undefined) { camera.fov = o.fov; camera.updateProjectionMatrix(); }
  return probeCam();
};

let __frames = 0;
let lastFrameWall = performance.now();   // 부팅 게이트가 보는 벽시계(프레임 간격)
// DEV 는 파일 맨 위에서 한 번만 정한다(위 '개발 모드 스위치' 절).
const nextFrame = DEV ? (fn => setTimeout(fn, 16)) : (fn => requestAnimationFrame(fn));
if (DEV) {
  // 검증용. 캔버스는 preserveDrawingBuffer 없이 만들어져서 그냥 toDataURL 하면
  // 빈 이미지가 나온다. 읽기 직전에 한 번 더 그려서 같은 태스크 안에서 뽑는다.
  window.__cap = () => { composer.render(); return cv.toDataURL('image/jpeg', 0.86); };
  window.__view = (y, p, d) => { yaw = y; pitch = p; dist = d; applyDist(); };
  // 시점 검증용. 카메라와 현재 값을 그대로 노출한다(고정 쿼터뷰 튜닝에 쓴다).
  window.__cam = camera;
  // 맵·충돌 검증용. 플레이어를 원하는 자리에 세워놓고 벽을 밀어볼 수 있어야 한다.
  window.__root = root;
  window.__put = (x, z) => { root.position.set(x, level.groundY(x, z), z); };
  window.__camState = () => ({ yaw, pitch, dist, fov: camera.fov,
    deg: +(pitch * 180 / Math.PI).toFixed(1) });
  // 셰이더가 실제로 갱신됐는지 브라우저에서 확인하기 위한 창구.
  window.__fx = { scene, renderer, composer, camera, trailMat, wrapMat, sprayMat, ELEMENTS,
                  el: () => curEl, trailN: () => trailBuf.length, buf: trailBuf,
                  update: () => updateTrail(true), burst: spawnBurst,
                  // ── 계측 창구 (v96) ──
                  // ★화면 점유·휘도 델타는 **이펙트를 껐다 켠 두 장의 차이**로만 정확히
                  //   잰다(색으로 추리면 하늘·물이 같이 걸린다). 그 목록이 이것이다.
                  //   월드 이펙트(궤적·감김·물보라) + feel.js 의 화면 겹 전부.
                  meshes: [trailMesh, wrapMesh, sprayMesh].concat(feel.fxMeshes || []),
                  // ★12-FX-D. 촬영 하네스가 **첫 줄에 "지금 어느 벌을 보고 있는가"**를
                  //   찍을 수 있어야 한다(LOG 12-FX 함정: A/B 가 서로 다른 파일을 읽고
                  //   있었는데 아무도 몰랐다). 그래서 벌 이름·기하를 그대로 노출한다.
                  style: { key: FX.key, name: FX.name, mode: FX.mode, half: FX.half,
                           strands: STRANDS, life: FX.ladder.length, trailMax: TRAIL_MAX,
                           profile: FX.profile, alpha: FX.alpha, tipK: FX_TIP_K,
                           sprayK: FX.sprayK, wrapK: FX.wrapK,
                           // ★18차. 스위치 상태와 합성 방식까지 한 줄에 적는다
                           //   (A/B 판정지 첫 줄에 "어느 판을 보고 있는가"가 있어야 한다).
                           // ★실제 재질에서 읽는다. 상수식으로 적었다가 가산->평칠로
                           //   되돌린 뒤에도 'additive' 라고 적혀 판정지가 거짓말을 했다.
                           v18: FX_V18,
                           blend: trailMat.blending === THREE.AdditiveBlending ? 'additive' : 'normal',
                           lifeSec: +(FX.ladder.length / FX_FPS).toFixed(3) },
                  charH: () => charH, root: () => root };
  window.__atkTime = () => (actions.Attack ? actions.Attack.time : -1);
  // 칼날 판정 선분(월드). 요괴 캡슐 판정을 숫자로 검증할 때 쓴다.
  // ★루프가 enemy.js 에 넘기는 것과 **똑같은 식**으로 계산한다(bladeA/B 를 손 본
  //   월드행렬로 옮긴다). __freeze 중에는 swordA/B 가 안 갱신되므로 여기서 직접 뽑는다.
  window.__blade = () => {
    if (!handBone || !bladeOK) return null;
    handBone.updateWorldMatrix(true, false);
    return { a: bladeA.clone().applyMatrix4(handBone.matrixWorld).toArray(),
             b: bladeB.clone().applyMatrix4(handBone.matrixWorld).toArray() };
  };
  // 실시간 캡처는 toDataURL 이 느려서 애니메이션이 굶는다. 프레임을 찍어 세우고 뽑는다.
  window.__size = (w, h) => {
    renderer.setPixelRatio(1);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  // 백그라운드 탭은 setTimeout 이 초당 2회로 throttle 돼서 실시간 재생 검증이 안 된다.
  // 클립을 직접 훑어 궤적 버퍼를 채운 뒤 한 장 뽑는다(프로덕션 코드 경로 그대로).
  window.__bakeTrail = (t0, t1, n = TRAIL_MAX, clip = 'Attack', gain = 1.0) => {
    const a = actions[clip];
    trailGain = gain;
    if (!a || !handBone || !bladeOK) return 'no blade';
    window.__freeze = true;
    for (const k in actions) if (actions[k] !== a) actions[k].stop();
    if (!a.isRunning()) { a.reset(); a.play(); }
    a.setEffectiveWeight(1); a.paused = true; a.setEffectiveTimeScale(1);
    trailBuf.length = 0;
    for (let i = 0; i < n; i++) {
      a.time = t0 + (t1 - t0) * (i / (n - 1));
      mixer.update(0);
      groundFeet();
      handBone.updateWorldMatrix(true, false);
      trailBuf.push({
        a: bladeA.clone().applyMatrix4(handBone.matrixWorld),
        b: bladeB.clone().applyMatrix4(handBone.matrixWorld),
        t: 1,
        f: Math.floor(gameT * FX_FPS)   // v94 수명 계단이 읽는 태생 칸(없으면 NaN 폭)
      });
    }
    // ★force. 이 창구는 게임시간을 안 흘리고 클립만 손으로 미는 경로라
    //   1/24 홀드에 걸리면 첫 호출 말고는 아무것도 안 그린다.
    updateTrail(true);
    return trailBuf.length;
  };
  // 감기는 리본은 매 프레임 누적이라 프레임을 세우면 안 보인다.
  // 클립을 t0~t1 로 밀면서 실제 updateTrail/updateWrap 을 그대로 돌린다.
  window.__bakeWrap = (clip, t0, t1, steps = 40, dtStep = 1 / 60) => {
    const a = actions[clip];
    if (!a || !handBone || !bladeOK) return 'no blade';
    window.__freeze = true;
    for (const k in actions) if (actions[k] !== a) actions[k].stop();
    if (!a.isRunning()) { a.reset(); a.play(); }
    a.setEffectiveWeight(1); a.paused = true; a.setEffectiveTimeScale(1);
    trailBuf.length = 0; lastTip = null; released = false; coil = 1;
    spray.length = 0;
    trailGain = (clip === 'Heavy') ? 1.9 : 1.0;
    for (let i = 0; i < steps; i++) {
      a.time = t0 + (t1 - t0) * (i / (steps - 1));
      mixer.update(0);
      groundFeet();
      handBone.updateWorldMatrix(true, false);
      const pa = bladeA.clone().applyMatrix4(handBone.matrixWorld);
      const pb = bladeB.clone().applyMatrix4(handBone.matrixWorld);
      if (lastTip) tipSpeed = _spd.copy(pb).sub(lastTip).length() / Math.max(dtStep, 1e-3);
      lastTip = (lastTip || new THREE.Vector3()).copy(pb);
      swordFast = Math.min(1, Math.max(0, (tipSpeed / FAST_REF - 0.12) / 0.55));
      if (swordFast > 0.55) released = true;
      const dec = Math.pow(0.86, dtStep * 60);
      for (const e of trailBuf) e.t *= dec;
      trailBuf.push({ a: pa, b: pb, t: Math.max(0, (swordFast - 0.38) / 0.62),
                      f: Math.floor(gameT * FX_FPS) });
      while (trailBuf.length > TRAIL_MAX) trailBuf.shift();
      updateTrail(true);            // ★force. 위 __bakeTrail 과 같은 이유
      updateWrap(dtStep, pa, pb, true, true);   // ★force: gameT 가 안 흐르는 경로
      const wk = Math.max(0, (swordFast - 0.38) / 0.62);
      if (wk > 0.15 && curEl.spray > 0) spawnSpray(pa, pb, _spd.clone().normalize(),
                                Math.round(2 + wk * 7), clip === 'Heavy' ? 1.5 : 1.0);
      updateSpray(dtStep, true);                // ★force: 같은 이유
    }
    return { coil: +coil.toFixed(2), tipSpeed: +tipSpeed.toFixed(2), n: trailBuf.length };
  };
  // ── 판정 리치·각도 프로브 (9차) ──
  // 비평가의 "거리 실측 35회" 를 사람 손 없이 재현한다. 클립을 프레임마다 세워
  // **실제 판정 선분**(makeHitSeg 를 지난 값)을 만들고, 가상의 요괴 캡슐에 대고
  // enemy.js 의 capsuleDist 로 물어본다. 즉 게임과 완전히 같은 계산이다.
  //   clip  : 'Attack' | 'Heavy' | 'Wide'
  //   dists : 잴 거리 목록(플레이어 중심 ~ 요괴 중심, m)
  //   angs  : 잴 각도 목록(도. 0 = 정면, 180 = 등 뒤)
  //   ext / cone : 규칙을 덮어써 **개선 전/후를 한 빌드에서** 잰다(-1 = 지금 값)
  // 반환: [{ang, hits:[{d, hit}]}] 와 각도별 최대 명중 거리
  window.__reach = (o = {}) => {
    const clip = o.clip || 'Attack';
    const a = actions[clip];
    if (!a || !handBone || !bladeOK) return 'no blade';
    const dists = o.dists || [1.0, 1.4, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.1, 3.2, 3.3, 3.4, 3.6, 4.0];
    const angs = o.angs || [0, 30, 60, 75, 90, 120, 180];
    const steps = o.steps || 90;
    const extSave = _hitOverride.ext, coneSave = _hitOverride.cone;
    if (o.ext !== undefined) _hitOverride.ext = o.ext;
    if (o.cone !== undefined) _hitOverride.cone = o.cone;
    // 플레이어를 정면(yaw 0)으로 세우고 클립을 훑는다
    const yaw0 = root.rotation.y;
    root.rotation.y = 0;
    window.__freeze = true;
    for (const k in actions) if (actions[k] !== a) actions[k].stop();
    if (!a.isRunning()) { a.reset(); a.play(); }
    a.setEffectiveWeight(1); a.paused = true; a.setEffectiveTimeScale(1);
    const dur = a.getClip().duration;
    const out = angs.map(ang => ({ ang, max: null, hits: [] }));
    const px = root.position.x, pz = root.position.z, py = root.position.y;
    const _pa = new THREE.Vector3(), _pb = new THREE.Vector3();
    let prevTip = null;
    const frames = [];
    for (let i = 0; i < steps; i++) {
      a.time = dur * (i / (steps - 1));
      mixer.update(0);
      groundFeet();
      handBone.updateWorldMatrix(true, false);
      _pa.copy(bladeA).applyMatrix4(handBone.matrixWorld);
      _pb.copy(bladeB).applyMatrix4(handBone.matrixWorld);
      // 타격 게이트(hot). enemy.js 와 **같은 식**이다: 칼끝 속도 -> swordFast,
      // 히스테리시스 HOT_ON 0.42 / HOT_OFF 0.16. (그 상수는 enemy.js 소유라 여기 복사본이다.
      //  값이 바뀌면 이 프로브도 같이 고쳐야 한다 - handoff_combat.md 에 적어 두었다.)
      const dtF = dur / (steps - 1);
      let fast = 0;
      if (prevTip) fast = Math.min(1, Math.max(0, (_pb.distanceTo(prevTip) / dtF / FAST_REF - 0.12) / 0.55));
      prevTip = _pb.clone();
      frames.push({ a: _pa.clone(), b: _pb.clone(), fast });
    }
    let hotState = false;
    for (const f of frames) {
      hotState = hotState ? f.fast > 0.16 : f.fast > 0.42;
      f.hot = hotState;
    }
    for (const rec of out) {
      const th = rec.ang * Math.PI / 180;
      for (const d of dists) {
        // 정면(yaw 0)이 +z 다. 각도는 +z 에서 시계 반대로 돈다.
        const ex = px + Math.sin(th) * d, ez = pz + Math.cos(th) * d;
        let hit = false;
        for (const f of frames) {
          if (!f.hot) continue;
          makeHitSeg(f.a, f.b);
          if (enemies.capsuleDist(hitA, hitB, ex, ez, py, 1).hit) { hit = true; break; }
        }
        rec.hits.push({ d, hit });
        if (hit) rec.max = d;
      }
    }
    _hitOverride.ext = extSave; _hitOverride.cone = coneSave;
    root.rotation.y = yaw0;
    a.paused = false;
    window.__freeze = false;
    return { clip, ext: o.ext !== undefined ? o.ext : HIT_EXT,
             cone: o.cone !== undefined ? o.cone : HIT_CONE_DEG, out };
  };
  window.__setAttackFrame = (f, fps = 30) => {
    const a = actions.Attack;
    if (!a) return -1;
    window.__freeze = true;
    for (const k in actions) if (actions[k] !== a) actions[k].stop();
    if (!a.isRunning()) { a.reset(); a.play(); }
    a.setEffectiveWeight(1);
    a.paused = true;
    a.time = Math.max(0, (f - 1) / fps);
    current = a;
    mixer.update(0);
    groundFeet();
    return a.time;
  };
}
// ---------- 요괴 ----------
// 판정용 히트박스를 새로 만들지 않는다. measureBlade() 가 실측한 칼날 선분
// (swordA=코등이 / swordB=칼끝, 둘 다 월드 좌표)을 그대로 넘겨준다.
// ── 벤 방향을 화면 각도로 ──
// 붓질 슬래시도 초승달도 **화면에서** 벤 방향으로 누워야 한다. 월드 방향을 그대로
// 쓰면 쿼터뷰에서 각이 죽어 전부 가로줄처럼 보인다. 투영해서 각을 낸다.
const swingDir = new THREE.Vector3(0, 1, 0);
let lastSwingHeard = -1;
const _s1 = new THREE.Vector3(), _s2 = new THREE.Vector3();
function screenAngle(x, y, z, dx, dy, dz) {
  _s1.set(x, y, z).project(camera);
  _s2.set(x + dx, y + dy, z + dz).project(camera);
  const ax = (_s2.x - _s1.x) * camera.aspect, ay = _s2.y - _s1.y;
  if (ax * ax + ay * ay < 1e-9) return { ang: 0, x: _s1.x * camera.aspect, y: _s1.y };
  return { ang: Math.atan2(ay, ax), x: _s1.x * camera.aspect, y: _s1.y };
}

// ---------------------------------------------------------------- 판정 = 보이는 것 (9차)
// 건틀릿 손맛 1위 격차: "이펙트는 화면에서 200~300px 인데 실제 판정은 2~3유닛.
//   3~5배 괴리." + "밀착하면 yaw 0 · π · -π/2 어느 쪽을 봐도 맞는다 = 등 뒤도 베인다."
//
// 판정을 새로 만들지 않는다. enemy.js 에 넘기는 **칼날 선분**을 두 번 손보고 넘긴다.
// (판정 코드는 enemy.js 소유라 안 건드린다. 넘기는 값만 바꾸면 잡몹·보스가 같이 따라온다.)
//
//   1) 리치 — 칼끝을 칼날 방향으로 HIT_EXT 만큼 늘린다. "긴 칼"과 같은 모양이라
//      스윙 궤적을 그대로 따라간다(원 모양 판정을 덧대면 궤적과 어긋난다).
//      값은 아래 __reach 프로브로 정면 명중 상한이 3.2m 가 되게 맞춘 것이다.
//   2) 각도 게이트 — 플레이어 중심에서 **정면 ±HIT_CONE_DEG** 부채꼴 밖은 잘라낸다.
//      2D 에서 반각 90도 미만인 원뿔은 **반평면 두 장의 교집합**과 정확히 같으므로,
//      선분을 두 번 자르면 끝난다(결과는 언제나 부분선분 하나).
//      다 잘려 나가면 플레이어 몸 안(정면 0.05m)의 점으로 접는다. 요괴는 몸 충돌
//      때문에 0.81m 보다 가까이 못 오고 캡슐 반경은 0.54m 라, 그 점은 누구에게도 안 닿는다.
//      ★null 을 넘기면 안 된다. enemy.js 가 직전 선분(hasPrevBlade)을 버려서
//        스윕 판정이 한 프레임 끊긴다.
// 보스가 마지막으로 친 벽시계 시각. 피격 방향을 되짚을 때 "범인이 보스인가"를 가른다.
let lastBossFireAt = -99999;
const HIT_EXT = 1.45;              // 칼끝 연장(m). 정면 상한 3.2m 가 나오는 값(프로브 실측)
const HIT_CONE_DEG = 75;           // 정면 부채꼴 반각(도)
// ★검증 프로브(__reach)가 **개선 전/후를 한 빌드에서** 재려고 잠시 덮어쓰는 자리다.
//   -1 이면 위 상수를 쓴다. 게임 경로는 늘 -1 이라 실제 판정에는 영향이 없다.
const _hitOverride = { ext: -1, cone: -1 };
const hitA = new THREE.Vector3(), hitB = new THREE.Vector3();
const _hx = new THREE.Vector3();
// 반평면 하나로 선분 [P0,P1] 을 자른다. n 은 안쪽을 가리키는 법선(원점 = 플레이어).
// 반환: 잘린 뒤에도 남아 있으면 true
function clipHalf(p0, p1, nx, nz, ox, oz) {
  const d0 = (p0.x - ox) * nx + (p0.z - oz) * nz;
  const d1 = (p1.x - ox) * nx + (p1.z - oz) * nz;
  if (d0 >= 0 && d1 >= 0) return true;
  if (d0 < 0 && d1 < 0) return false;
  const t = d0 / (d0 - d1);
  if (d0 < 0) p0.lerp(p1, t); else p1.lerp(p0, t);
  return true;
}
// ── 각도 게이트 검증 창구 ──
// 실제로 벤 **타격 지점**이 몸에서 몇 도였는지 쌓는다. "등 뒤가 베였나"는 요괴 위치를
// 추측할 게 아니라 이 값으로 답해야 한다(요괴는 계속 움직이므로 추측은 늘 흔들린다).
// ?dev 에서만 쌓는다(평시에는 함수 한 번 호출하고 바로 나간다).
function logHitAngle(x, z) {
  if (!DEV) return;
  const p = root.position;
  let d = Math.atan2(x - p.x, z - p.z) - root.rotation.y;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  const arr = (window.__hitAng = window.__hitAng || []);
  arr.push([+(d * 180 / Math.PI).toFixed(1), +Math.hypot(x - p.x, z - p.z).toFixed(2)]);
  if (arr.length > 400) arr.shift();
}

// a,b = 실제 칼날(월드). 결과는 hitA/hitB 에 담아 그대로 반환한다.
function makeHitSeg(a, b) {
  const ext = _hitOverride.ext >= 0 ? _hitOverride.ext : HIT_EXT;
  const coneDeg = _hitOverride.cone >= 0 ? _hitOverride.cone : HIT_CONE_DEG;
  hitA.copy(a); hitB.copy(b);
  // 1) 연장
  _hx.copy(b).sub(a);
  const L = _hx.length();
  if (L > 1e-4 && ext > 0) hitB.addScaledVector(_hx.multiplyScalar(1 / L), ext);
  if (coneDeg >= 180) return hitA;      // 게이트 없음(개선 전 비교용)
  // 2) 정면 부채꼴로 자르기
  const ox = root.position.x, oz = root.position.z;
  const fx = Math.sin(root.rotation.y), fz = Math.cos(root.rotation.y);
  // 부채꼴 경계 두 줄의 **안쪽 법선**. 경계는 정면을 ±(90-각)만큼 돌린 방향이다.
  const rad = coneDeg * Math.PI / 180;
  const s = Math.sin(rad), c = Math.cos(rad);
  //   n1 = 정면을 -(90-각) 회전, n2 = +(90-각) 회전.  (원뿔 반각 < 90 이라 둘 다 안쪽을 본다)
  const n1x = fx * s - fz * c, n1z = fx * c + fz * s;
  const n2x = fx * s + fz * c, n2z = -fx * c + fz * s;
  let ok = clipHalf(hitA, hitB, n1x, n1z, ox, oz);
  if (ok) ok = clipHalf(hitA, hitB, n2x, n2z, ox, oz);
  if (!ok) {                       // 칼이 통째로 뒤에 있다 = 이번 프레임은 아무도 안 벤다
    hitA.set(ox + fx * 0.05, root.position.y + 0.9, oz + fz * 0.05);
    hitB.copy(hitA);
  }
  return hitA;
}

// ── 아이템 드랍 (20차) ────────────────────────────────────────────────────
// ★롤백 = 이 한 줄을 false 로. 그러면 아래 items 가 null 이 되고 스폰·업데이트·
//   주머니·아이템창(ui.js 가 window.__items 를 보고 켠다)이 통째로 안 돈다.
const ITEMS_ON = true;
const { createItemSystem } = await import('./items.js' + location.search);
const items = ITEMS_ON ? createItemSystem({
  scene, camera, level,
  getPlayer: () => root.position,
  // 물약 사용의 실물. enemy.js 가 플레이어 체력을 쥐고 있으므로 그쪽 창구를 부른다.
  //   ★enemies 는 아래에서 만들어지지만, 이 화살표는 **부를 때** 평가되므로
  //     선언 순서를 뒤집을 필요가 없다(TDZ 는 호출 시점에 이미 풀려 있다).
  heal: (n) => (window.__enemy && window.__enemy.heal) ? window.__enemy.heal(n) : 0,
  // 주운 그 순간. 화면 좌하단 픽업 줄은 ui.js 가 진다.
  onPickup: (def, have) => {
    if (window.__ui && window.__ui.itemPicked) window.__ui.itemPicked(def, have);
    // 소리는 **희귀한 것에만** 낸다. 엽전마다 종을 치면 그게 잡음이 된다.
    if (def.tier === 'rare') sfx.token();
  },
}) : null;
window.__items = items;

// ── 화살 (21차. 오너 지시 「궁수 활 쏘는거 없으면 만들어줘」) ────────────────
// ★롤백 스위치 ARROW_ON 의 **정의는 위(isArcher 바로 앞)** 에 있다. 여기 두면
//   로딩 중 Z 를 누른 판에서 선언 전 접근(TDZ)이 난다 - 캐릭터 glb 로드 콜백은
//   이 줄보다 앞에 있는 await 사이에 끼어들 수 있고, 그러면 actions.Attack 가드가
//   이미 열린 채로 tryAttack -> isArcher() 가 ARROW_ON 을 읽는다.
const { createArrowSystem } = await import('./arrow.js' + location.search);
const arrows = ARROW_ON ? createArrowSystem({
  scene, camera, level,
  // ★판정 창구 둘. **화살표로 감싸는 이유는 items.js 의 heal 과 같다** - enemies/boss 는
  //   아래에서 const 로 선언되므로 지금 참조를 잡으면 TDZ 에 걸린다(부를 때는 이미 풀려 있다).
  //   창구가 없는 낡은 빌드와 짝을 지어도 게임은 그대로 돈다(0 / false 로 흐른다).
  hitEnemies: (a, b, o) => (enemies && enemies.hitSegment) ? enemies.hitSegment(a, b, o) : 0,
  hitBoss: (a, b, o) => (window.__boss && window.__boss.hitSegment)
                          ? window.__boss.hitSegment(a, b, o) : false,
  // 시위를 떠나는 그 순간.
  // ★22차 멀티. 시위를 떠나는 그 자리에서 **한 번만** 적는다.
  //   여기가 유일한 길목인 이유: arrow.js 의 push() 가 모든 발사를 지나므로
  //   나중에 발사 호출을 하나 더 만들어도 여기를 빠뜨릴 수가 없다
  //   (「바뀔 때 한 번 적어 두는」 방식이 조용히 틀리는 함정을 이 구조로 피한다).
  onFire: (a) => { sfx.bow(); mpNoteShot(a); },
  // ★명중 연출의 방향을 화살 진행 방향으로 세운다. 안 세우면 onHit 이 **직전 칼질의**
  //   방향(swingDir)으로 참격·먹물을 눕힌다 - 활을 쏘는데 칼자국이 옆으로 눕는다.
  beforeHit: (a, dir) => { swingDir.copy(dir); },
}) : null;
window.__arrows = arrows;

// ═══════════════════════════════════════════════════════════════════════════
// 남의 공격 이펙트 (22차 멀티. 2026-08-20)
//
// 오너 신고: **"팀원의 공격 이런 건 안 보이네."** 남의 모션은 맞는데 칼에서 아무
// 빛도 안 나서 허공을 젓는 것처럼 보였다.
//
// ── 무엇을 골랐나: (나) 원격 아바타의 **뼈에서 로컬 계산** ────────────────────
// 이벤트로 "지금 베었다"를 보내고 받는 쪽이 통조림 이펙트를 트는 길((가))도 있었지만
// 안 골랐다. 이 게임의 궤적은 그림 한 장이 아니라 **칼끝이 지나간 자리의 연속**이라,
// 이벤트로는 원리적으로 재현이 안 된다(어느 자리를 어떤 속도로 지났는지가 없다).
// 반면 원격 아바타에는 같은 glb 의 **뼈와 칼 메시가 그대로** 있고, 클립도 이미 같은
// 시각·같은 배속으로 돌고 있다(mp.js 가 msg.c/msg.p/msg.ts 로 맞춘다).
// 그러니 로컬 플레이어에게 하던 것과 **글자 하나 다르지 않은 계산**을 그 사람 손 본에
// 대고 한 번 더 돌리면 된다. 실제 이득이 셋이다 —
//   ① 네트워크에 **한 바이트도 안 늘었다**(칼 이펙트에 한해서. 화살은 아래 참조)
//   ② 지연이 곧 아바타 지연이다. 이펙트만 따로 늦거나 어긋날 수가 없다
//   ③ 그림 문법이 내 것과 자동으로 같다. 크기·색·수명 상수를 두 번 적을 자리가 없다
//
// ── 그래서 무엇을 바꿨나 ──
// 옛 판은 궤적 버퍼·지오메트리·칸 번호가 전부 **모듈 전역 한 벌**이었다. 그릇만
// makeTrailRig() 로 빼고(위쪽), 계산은 buildRibbon(R) **한 함수**로 남겼다.
// 로컬은 updateTrail() 이 전역을 담아 부르고, 원격은 여기가 그 사람 rig 를 담아 부른다.
//
// ── 안 한 것(일부러) ──
// · 화면 겹 붓자국(feel.swing): SCREEN_STROKE = 0 이라 **지금 아무것도 안 그린다.**
//   부르면 그리는 대신 lastStroke(전멸 링·임팩트 컷이 되짚는 자리)만 더럽힌다.
// · 칼 감김(updateWrap)·물보라: 시작 칼 nokseun 의 원소가 plain 이고 그 표에
//   wrap:0 · spray:0.0 이다 = **로컬 플레이어도 이 칼로는 안 나온다.** 남에게만
//   더 얹으면 "내 이펙트와 같은 문법" 계약이 깨진다.
// · 명중 연출(feel.hit/kill/burst/pop): 요괴가 아직 각자 로컬이라(mp.js 머리말)
//   남의 칼에 맞는 내 요괴가 없다. 2단계(호스트 권위) 몫이다.
//
// ★★롤백 스위치는 아래 MP_FX_ON **한 줄이고 정의는 여기 한 곳뿐이다.**
//   mp.js 는 ctx.fx 가 null 인지만 본다(스위치를 두 벌 두면 반드시 어긋난다).
// ═══════════════════════════════════════════════════════════════════════════
const MP_FX_ON = true;     // false = 남의 이펙트가 통째로 안 생긴다(rig·화살 시스템도 안 만든다)

// ═══════════════════════════════════════════════════════════════════════════
// ── 멀티 2단계 1차: 요괴를 방장 기준으로 하나로 ──
// 방장 한 명만 enemy.js 를 굴리고(스폰·AI·이동·공격·피해), 참가자는 받은 상태를
// **그림으로만** 그린다. 인디 스팀 멀티의 사실상 표준(방장 권위)이고, 스팀으로 가면
// 이 구조 그대로 Steam Networking 을 탄다.
//   · 방장 화면  = 혼자 하던 판과 한 글자도 안 다르다(+ 10Hz 송신 하나)
//   · 참가자 화면 = 같은 요괴가 같은 자리에서 같이 죽는다. 아직 **때리지는 못한다**
//     (참가자의 피해 판정은 2차 몫이다. 지금은 칼도 화살도 요괴를 못 건드린다)
// ★★롤백 스위치는 아래 MP_ENEMY_ON **한 줄이고 정의는 여기 한 곳뿐이다.**
//   false 면 mpenemy.js 를 아예 안 읽고 enemies.setNetMode 도 안 부른다 =
//   요괴가 예전처럼 **각자 로컬**로 돌아간다(1단계 그대로).
// ═══════════════════════════════════════════════════════════════════════════
const MP_ENEMY_ON = true;

// ═══════════════════════════════════════════════════════════════════════════
// ── 멀티 2단계 2차: 같이 잡고, 같이 맞는다 ──
// 1차는 "같은 요괴가 같은 자리에 있고 같이 죽는다"까지였다. 남은 셋이 2차다.
//   · 참가자의 칼·화살이 요괴에 닿는다 — 참가자가 자기 화면에서 판정하고(예측)
//     **주장**만 보내면 방장이 싼 상식 검사 뒤 확정한다(enemy.js resolveHit 머리 주석).
//   · 요괴가 **제일 가까운 사람**을 쫓고 때린다 — 1차까지 요괴가 아는 사람은
//     방장 하나뿐이라 참가자 체력이 100 에서 안 내려갔다.
//   · 참가자 화면에도 드랍이 뜬다 — 아이템은 각자 주머니라 소식이 0바이트다.
// ★★롤백 스위치는 아래 MP_HIT_ON **한 줄이고 정의는 여기 한 곳뿐이다.**
//   1차(MP_ENEMY_ON)와 **따로** 둔 이유: 2차가 말썽일 때 요괴 공유까지 같이 잃지
//   않고 1차 상태로만 돌아가려는 것이다. false 면 참가자는 다시 못 때리고
//   요괴는 방장만 쫓는다(= f4f2e04 판의 동작).
//   enemy.js 는 ctx 로 받은 값만 보고, mp.js·mpenemy.js 에는 스위치가 없다
//   (주장이 안 생기면 보낼 것도 없고, 피해 통보도 날 일이 없다).
// ═══════════════════════════════════════════════════════════════════════════
const MP_HIT_ON = true;

// 원격 궤적 벌 수 상한. 지금 상정 인원이 2~4명이고, 한 벌이 약 27KB + 1 드로우콜이다.
// 넘치면 **먼저 붙은 사람** 것을 지킨다(나중 사람은 아바타만 뜨고 이펙트가 없다).
const MP_FX_MAX = 4;

// 최근 발사 한 건. arrow.js 의 push() 한 자리에서만 적힌다(위 onFire 주석).
// ★TDZ 주의: 아래 let 이 초기화되기 전에 mpNoteShot 이 불릴 일은 없다 -
//   화살이 날려면 게임 루프가 돌아야 하고, 그건 모듈 평가가 끝난 뒤다.
let mpShotSeq = 0, mpShotAt = -9e9;
const mpShot = { n: 0, x: 0, y: 0, z: 0, dx: 0, dy: 0, dz: 1 };
function mpNoteShot(a) {
  const sp = Math.hypot(a.vx, a.vy, a.vz) || 1;
  mpShot.n = ++mpShotSeq;
  mpShot.x = a.x; mpShot.y = a.y; mpShot.z = a.z;
  mpShot.dx = a.vx / sp; mpShot.dy = a.vy / sp; mpShot.dz = a.vz / sp;   // 단위 방향만 보낸다
  mpShotAt = performance.now();
}
// 상태 소식에 실어 보낼 값. **막 쏜 뒤 0.6초 동안만** 싣는다.
// ★왜 창을 두나: 채널이 unreliable 이라 한 장이 유실될 수 있다. 15Hz 로 0.6초면
//   같은 발사가 최대 9번 실려 나가고, 받는 쪽은 번호(n)로 중복을 버린다.
//   ★평시(칼잡이)에는 null 이라 소식 크기가 예전 그대로다.
const MP_SHOT_WINDOW = 600;
function mpShotWire() {
  if (!mpShot.n || performance.now() - mpShotAt > MP_SHOT_WINDOW) return null;
  return [mpShot.n, +mpShot.x.toFixed(2), +mpShot.y.toFixed(2), +mpShot.z.toFixed(2),
          +mpShot.dx.toFixed(3), +mpShot.dy.toFixed(3), +mpShot.dz.toFixed(3)];
}

function createMpFx() {
  const rigs = new Map();           // id -> rig(+ 손 본·칼 축)
  const _a2 = new THREE.Vector3(), _b2 = new THREE.Vector3(), _sp2 = new THREE.Vector3();
  const _ax = new THREE.Vector3(0, 1, 0);
  let fxFrames = 0, attachN = 0, failN = 0;

  // ── 남의 화살 (여기만 (가) 이벤트다) ────────────────────────────────────
  // ★칼과 달리 화살은 **결정적**이다 - 시작점과 단위 방향만 같으면 속도·중력이 코드
  //   상수라 궤적이 그대로 재현된다(arrow.js SPEED 30 · G 4.0). 그래서 뼈를 훑을
  //   이유가 없고, 오히려 뼈로 하면 "언제 시위를 놓았나"를 다시 추측해야 한다.
  // ★판정은 안 준다(hitEnemies/hitBoss 가 0·false). 1단계 멀티에서 요괴는 각자
  //   로컬이라 남의 화살이 내 요괴를 죽이면 "유령 킬"이 된다(mp.js 머리말과 같은 규칙).
  //   그래서 **그림만 나는 화살**이다. 벽·땅·수명에는 그대로 걸린다.
  let ghost = null;
  function ghostSys() {
    if (ghost || !ARROW_ON) return ghost;
    ghost = createArrowSystem({
      scene, camera, level,
      hitEnemies: () => 0, hitBoss: () => false,
      onFire: () => sfx.bow(),        // 남이 쏘는 소리는 들려야 한다
      beforeHit: () => {},
    });
    return ghost;
  }

  // ── 원격 한 사람 붙이기 ────────────────────────────────────────────────
  // model = mp.js 가 올린 그 사람 glb 의 루트. 이미 스케일·재질이 끝난 상태로 온다.
  // charH = 그 캐릭터의 목표 키(CHAR_CFG[name].h). ★로컬의 charH 와 **정확히 같은 수**다
  //   (로컬도 box 높이를 cfg.h 로 정규화하므로 charH === cfg.h 로 떨어진다).
  //   여기서 박스를 다시 재면 그때 도는 클립 자세가 섞여 몇 cm 씩 어긋난다.
  function attach(id, model, charH) {
    if (!model || rigs.has(id)) return;
    if (rigs.size >= MP_FX_MAX) { failN++; return; }
    // 손 본
    let hand = null;
    // ★어느 칼인지는 **묻지 않고 본다.** mp.js 가 시작 칼 하나만 visible 로 두므로
    //   보이는 SW_ 메시를 모으면 그게 곧 그 사람이 든 칼이다. 이름을 여기 또 적으면
    //   mp.js 의 START_SWORD 와 두 벌이 되어 언젠가 어긋난다.
    const byKey = {};
    model.traverse(o => {
      if (o.isBone && /r[_ ]hand/i.test(o.name)) hand = o;
      if (o.isSkinnedMesh && o.visible && o.name.startsWith('SW_')) {
        const k = o.name.slice(3).replace(/_\d+$/, '');
        (byKey[k] = byKey[k] || []).push(o);
      }
    });
    const keys = Object.keys(byKey);
    if (!hand || keys.length !== 1) { failN++; return; }   // 칼이 없는 캐릭터(궁수 등)
    const key = keys[0];
    const m = measureBladeOf(byKey[key]);
    if (!m) { failN++; return; }

    // 이 칼의 원소 = 그림(팔레트·굵기·알파)의 출처. 로컬 setElement() 와 같은 표를 본다.
    const sw = SWORDS.find(x => x.key === key);
    const elName = (sw && sw.el) || 'plain';
    const el = ELEMENTS[elName] || ELEMENTS.plain;
    const pal = PAL[elName] || PAL.plain;

    const r = makeTrailRig([]);
    r.mat = trailMat.clone();          // ★셰이더 소스가 같아 프로그램은 공유된다(컴파일 0회)
    r.mat.uniforms.uPal.value = pal;
    r.mat.uniforms.uStyle.value = el.style;
    const wt = WAVETEX[elName];
    r.mat.uniforms.uTex.value = wt || WAVETEX.water;
    r.mat.uniforms.uUseTex.value = wt ? 1 : 0;
    r.mesh = new THREE.Mesh(r.geo, r.mat);
    r.mesh.frustumCulled = false;
    r.mesh.renderOrder = 3;            // 로컬 궤적과 같은 층
    r.mesh.visible = false;
    scene.add(r.mesh);
    r.el = el;
    r.hand = hand;
    r.bA = m.a; r.bB = m.b;
    r.lastTip = null;
    r.charH = charH || 2.4;
    r.model = model;
    r.wrote = 0;
    r.swings = 0; r.wasHot = false;
    rigs.set(id, r);
    attachN++;
  }

  function detach(id) {
    const r = rigs.get(id);
    if (!r) return;
    scene.remove(r.mesh);
    r.geo.dispose(); r.mat.dispose();
    rigs.delete(id);
  }

  // ── 프레임 한 장 ───────────────────────────────────────────────────────
  // mp.js 가 그 사람 mixer 를 굴린 **직후에** 부른다(뼈가 이번 프레임 값이어야 한다).
  // clip = 지금 도는 클립 이름, act = 그 AnimationAction(진행도용).
  // ★dtRaw 로 받는다. 남의 아바타는 mp.js 에서 이미 rawDt 로 도는데 여기만 게임시계를
  //   쓰면 내 히트스톱 동안 궤적만 얼어붙어 칼에서 떨어져 나간다.
  function frame(id, dtRaw, clip, act) {
    const r = rigs.get(id);
    if (!r || !r.hand) return;
    // 이 벌의 시계는 **벽시계**다(rawDt 를 누적하지 않는다 - 그 값은 main.js 에서
    // Math.min(0.05, delta) 로 잘려 있어 프레임이 낮을수록 실제보다 느리게 쌓인다.
    // 이 레포가 송신 주기와 경로 조회에서 두 번 밟은 함정이다).
    r.clock = performance.now() * 0.001;
    // ★셰이더의 재시딩 시계. 로컬은 tick 이 trailMat.uniforms.uT 에 gameT 를 넣는데,
    //   원격 재질은 그 자리를 안 지나므로 여기서 직접 넣는다. 안 넣으면 uT 가 0 에
    //   묶여 붓결 노이즈가 한 장에 굳는다(계단으로 다시 그리는 맛이 통째로 죽는다).
    r.mat.uniforms.uT.value = r.clock;

    r.hand.updateWorldMatrix(true, false);
    _a2.copy(r.bA).applyMatrix4(r.hand.matrixWorld);
    _b2.copy(r.bB).applyMatrix4(r.hand.matrixWorld);

    // ★순간이동 방어. 첫 소식이 오면 mp.js 가 아바타를 **한 프레임에** 제자리로
    //   옮긴다(수십 m). 그 한 칸을 그대로 궤적으로 그리면 맵을 가로지르는 띠가 한 장
    //   생긴다. 로컬에도 같은 규칙이 있다 - 되살아나기·칼 교체에서 trailBuf 를 비운다.
    //   문턱 2m/프레임 = 60fps 에서 120m/s 다(달리기 최대의 열 배가 넘는다).
    if (r.lastTip && _b2.distanceToSquared(r.lastTip) > 4) {
      r.buf.length = 0; r.lastTip.copy(_b2);
    }

    // 칼끝 속도 -> 궤적 세기. 로컬과 **같은 자**다(FAST_REF 45, 게이트 0.12/0.55).
    let fast = 0;
    if (r.lastTip) {
      const sp = _sp2.copy(_b2).sub(r.lastTip).length() / Math.max(dtRaw, 1e-3);
      fast = Math.min(1, Math.max(0, (sp / FAST_REF - 0.12) / 0.55));
    } else {
      _sp2.set(0, 0, 0);
      r.lastTip = new THREE.Vector3();
    }
    r.lastTip.copy(_b2);

    // 공격 중인가 = 공격 클립이 아직 끝까지 안 갔는가.
    // ★클립 이름만 보면 안 된다 - LoopOnce + clampWhenFinished 라 다 끝난 뒤에도
    //   이름은 'Attack' 인 채로 남는다. 그러면 서 있기만 해도 궤적이 계속 그어진다.
    let atk = false, prog = 0;
    if (clip === 'Attack' || clip === 'Heavy' || clip === 'Wide') {
      const dur = act && act.getClip() ? act.getClip().duration : 0;
      if (dur > 0) { prog = act.time / dur; atk = act.time < dur - 0.02; }
    }
    // 궤적 크기. 로컬 tick() 의 gainTarget 표를 그대로 옮겼다
    // (Z 3연타는 1타 1.35 -> 2타 1.55 -> 3타 1.80 으로 커지고, 일격기는 1.85).
    let gt = 1.15;
    if (clip === 'Heavy' || clip === 'Wide') gt = atk ? 1.85 : 1.15;
    else if (clip === 'Attack' && atk) gt = prog > 0.76 ? 1.80 : (prog > 0.39 ? 1.55 : 1.35);
    r.gain += (gt - r.gain) * Math.min(1, dtRaw * 9);
    r.clip = atk ? clip : null;

    // 몸 기준점(리치 부채꼴·몸 비우기의 원점). 그 사람 그룹의 월드 자리다.
    // ★로컬은 root(그룹)의 자리를 쓰고 원격은 **model 의 월드 자리**를 쓴다.
    //   x·z 는 완전히 같고, y 만 접지 보정(model.position.y)만큼 다르다 - 그 값은
    //   발뼈 최저점을 바닥에 붙이는 몇 cm 짜리 보정이라 가슴 높이(charH x 0.55 = 1.32m)
    //   기준점에 주는 오차가 무시할 수준이다. 좌표를 더 보내는 대신 이쪽을 골랐다
    //   (mp.js 머리 주석의 좌표 규약: 원격에는 model 월드 좌표만 온다).
    r.model.getWorldPosition(r.pos3);
    r.yaw = r.model.parent ? r.model.parent.rotation.y : 0;

    // 샘플 하나 밀어 넣기. 로컬(tick 의 trailBuf.push)과 같은 식이다.
    const wake = Math.max(0, (fast - 0.28) / 0.72);
    for (const e of r.buf) {                // 물결이 칼을 떠나 날아가는 몫
      if (e.vb) {
        e.a.addScaledVector(e.va, dtRaw);
        e.b.addScaledVector(e.vb, dtRaw);
        e.vb.applyAxisAngle(_ax, 1.3 * dtRaw);
        e.va.multiplyScalar(Math.pow(0.40, dtRaw));
        e.vb.multiplyScalar(Math.pow(0.40, dtRaw));
      }
    }
    const invDt = 1 / Math.max(dtRaw, 1e-3);
    r.buf.push({ a: _a2.clone(), b: _b2.clone(), t: atk ? wake : 0,
                 f: Math.floor(r.clock * FX_FPS),
                 va: _sp2.clone().multiplyScalar((atk ? 0.06 : 0) * invDt),
                 vb: _sp2.clone().multiplyScalar((atk ? 0.16 : 0) * invDt) });
    while (r.buf.length > TRAIL_MAX) r.buf.shift();

    buildRibbon(r);
    // 살아 있는 마디가 하나도 없으면 아예 안 그린다(드로우콜 회수).
    r.mesh.visible = r.wrote > 0;
    if (r.wrote > 0) fxFrames++;
    // 스윙 세기(검증용). 칼끝이 문턱을 넘는 순간을 한 번으로 친다.
    const hot = atk && fast > 0.52;
    if (hot && !r.wasHot) { r.swings++; r.hotAt = performance.now(); }
    r.wasHot = hot;
  }

  // 남이 쏜 화살 한 발. wire = [n, x, y, z, dx, dy, dz]
  function arrow(wire) {
    const g = ghostSys();
    if (!g || !wire || wire.length < 7) return;
    g.fireDir(wire[1], wire[2], wire[3], wire[4], wire[5], wire[6]);
  }

  // 화살은 **게임시계**로 난다(로컬 화살과 같은 규칙. arrow.js 머리말).
  function updateArrows(dt, paused) { if (ghost) ghost.update(dt, paused); }

  function dispose() {
    for (const id of [...rigs.keys()]) detach(id);
    if (ghost) ghost.reset();
  }

  // 판을 다시 시작할 때(R). 남의 화살과 남의 궤적을 같이 지운다 - 이 게임의
  // 리셋 문화 그대로다(로컬도 trailBuf/spray/arrows 를 여기서 비운다).
  // ★rig 자체는 안 없앤다. 사람이 나간 게 아니라 내 판이 다시 시작한 것뿐이다.
  function reset() {
    if (ghost) ghost.reset();
    for (const [, r] of rigs) { r.buf.length = 0; r.lastTip = null; r.mesh.visible = false; r.wrote = 0; }
  }

  const api = {
    attach, detach, frame, arrow, updateArrows, dispose, reset,
    get rigs() { return rigs.size; },
    // ★검증 창구(상수가 아니라 window 노출. HANDOFF 의 관례). 남의 궤적만 껐다 켠다.
    //   같은 프레임에 켠 그림과 끈 그림을 나란히 렌더해야 "이펙트가 정확히 몇 화소인가"를
    //   추측 없이 잴 수 있다(눈으로는 옅은 시안 한 줄을 셀 수가 없다).
    show(v) { for (const [, r] of rigs) r.mesh.visible = !!v && r.wrote > 0; return rigs.size; },
    // 검증 창구. "보이는 것 같다"가 아니라 수로 본다.
    //   fxFrames = 궤적이 실제로 화소를 쓴 프레임 수(전체 합)
    //   swings   = 원격이 칼을 휘두른 횟수(칼끝이 문턱을 넘은 수)
    get state() {
      return {
        on: MP_FX_ON, rigs: rigs.size, attached: attachN, failed: failN,
        fxFrames, arrows: ghost ? ghost.state.live : 0,
        fired: ghost ? ghost.state.fired : 0,
        list: [...rigs.entries()].map(([id, r]) => ({
          id: id.slice(-6), clip: r.clip, wrote: r.wrote, swings: r.swings,
          vis: r.mesh.visible, gain: +r.gain.toFixed(2),
          tip: r.lastTip ? r.lastTip.toArray().map(v => +v.toFixed(2)) : null,
          hotAgoMs: r.hotAt ? Math.round(performance.now() - r.hotAt) : -1,
        })),
      };
    },
  };
  return api;
}
const mpFx = MP_FX_ON ? createMpFx() : null;
window.__mpfx = mpFx;

// ── ★화살을 놓는다 (21차) ──────────────────────────────────────────────────
// 부르는 자리는 아래 루프 한 곳뿐이다(클립 발사 프레임).
// 정하는 것 둘:
//   ① **어디서 떠나는가** = 활을 쥔 왼손. 몸 기준 어림값으로 하면 만작에서 팔이
//      앞으로 뻗은 만큼(약 0.4m) 화살이 가슴에서 튀어나온다.
//   ② **어디를 겨누는가** = 발사 순간에 **다시** 잰다. 입력 순간에 겨눈 놈은 0.35초
//      동안 움직였고, 그 사이 더 가까운 놈이 들어왔을 수도 있다.
//      아무도 없으면 바라보는 방향으로 그냥 쏜다(헛방의 자유).
const _bowP = new THREE.Vector3();
function fireArrow() {
  if (!arrows) return null;
  if (lhandBone) lhandBone.getWorldPosition(_bowP);
  else {
    // 왼손 본이 없는 캐릭터를 위한 어림값(가슴 높이 · 반 걸음 앞).
    const gy = level.groundY(root.position.x, root.position.z);
    _bowP.set(root.position.x + Math.sin(root.rotation.y) * 0.30,
              gy + charH * 0.66,
              root.position.z + Math.cos(root.rotation.y) * 0.30);
  }
  const t = enemies.nearestTo(root.position.x, root.position.z, BOW_AIM_R);
  if (t) {
    let d = t.yaw - root.rotation.y;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    // ★등 뒤는 안 겨눈다(snapTargetBow 와 **같은 게이트**). 몸은 앞을 보는데 화살만
    //   뒤로 날아가는 그림을 막는 자리다.
    if (Math.abs(d) <= SNAP_BACK_DEG * Math.PI / 180) {
      // 표적 높이. 요괴 캡슐(enemy.js CAP_LO 0.20 ~ CAP_HI 0.74 x 키 1.30)의 한가운데가
      // 발밑 +0.61m 다. 보스는 몸통 중심이 +1.55m(boss.js CENTER_Y 1.65 에 맞춘 값).
      const ty = level.groundY(t.x, t.z) + (t.boss ? 1.55 : 0.61);
      return arrows.fireAt(_bowP.x, _bowP.y, _bowP.z, t.x, ty, t.z);
    }
  }
  // 자유 사격. 활을 쥔 손 높이에서 정면으로, 아주 살짝 위로(중력에 바로 먹히지 않게).
  return arrows.fireDir(_bowP.x, _bowP.y, _bowP.z,
                        Math.sin(root.rotation.y), 0.045, Math.cos(root.rotation.y));
}

const enemies = createEnemySystem({
  scene, camera,
  // 무리 자리는 맵이 정한다(level1.json 의 mobs[]). 마릿수·반경은 enemy.js 가 정한다.
  mobs: level.mobs(),
  getPlayerPos: () => root.position,
  // ★2차 스위치를 그대로 넘긴다(정의는 위 MP_HIT_ON 한 곳).
  netHit: MP_HIT_ON,
  // ── 요괴가 **남**을 때렸다 (2차) ──
  // 내 체력이 아니라 남의 체력 이야기다. 소식으로 내보내면 그 사람이 자기 무적·
  // 새는 통·넉백으로 자기 체력을 깎는다. 혼자 하는 판에서는 한 번도 안 불린다.
  onNetHurt: (tag, dmg, x, z) => { if (mpEnemy) mpEnemy.onNetHurt(tag, dmg, x, z); },
  // ── 참가자인 내가 요괴를 쳤다는 주장 (2차) ──
  // enemy.js 의 예측이 스윙마다 한 번 넘긴다. 방장에게 실어 보내는 일만 한다.
  onClaim: (c) => { if (mpEnemy) mpEnemy.onClaim(c); },
  onRespawn: () => {
    toSpawn();
    vy = 0; grounded = true; jumping = false;
    attacking = false; heavy = false;
    atkClip = null; stepLeft = 0;   // 커밋·전진 스텝도 끊는다(죽은 자리의 관성이 남으면 안 된다)
    coastLeft = 0; punchLeft = 0; hsLeft = 0;   // ★감속 관성·카메라 펀치·히트스톱도 같이
    dashLeft = 0; dashReadyT = -99; dashIfUntil = -99;   // 대시도 같이(쿨은 풀어 준다)
    clearBuffer();               // 죽는 순간 눌러 둔 입력이 부활 프레임에 튀어나오면 안 된다
    resetCombo(null);            // 죽고 되살아나면 누적 명중 수도 끊는다
    // ★타격 지점 참격(feel.impactSlash)은 여기서 안 지운다. 한 장이 0.17~0.25초라
    //   되살아나기(초 단위)까지 어차피 다 지나가 있다.
    trailBuf.length = 0; spray.length = 0;
    // ★죽으면 주머니도 바닥의 물건도 비운다(오너 지시. R 재시작과 같은 규칙).
    if (items) items.reset();
    // ★날아가던 화살도 같이 지운다. 안 지우면 되살아난 자리 옆으로 지난 판의 화살이 지나간다.
    if (arrows) { arrows.reset(); arrowShot = false; }
  },
  // ── 칼이 닿는 그 프레임 ──
  // 여기 한 줄 한 줄이 "처치하는 맛"이다. 순서에 뜻이 있다:
  //   멈춘다(히트스톱) -> 소리 -> 화면(참격 한 장·붓질·먹물). 소리가 늦으면 다 어긋난다.
  onHit: (h) => {
    // ★멀티(방장)일 때만 값이 있다. **제일 먼저** 적는다 - 아래 연출 줄 중 하나가
    //   던져도 "요괴가 맞았다"는 사실은 남에게 가야 한다. 혼자 하는 판에서는
    //   mpEnemy 가 null 이라 비교 한 번으로 끝난다.
    if (mpEnemy) mpEnemy.onHit(h);
    // ★★2차. **남이 때린 한 대**는 여기서 끝난다(by 가 비어 있지 않다). 시체·데미지
    //   숫자는 enemy.js 가 이미 세웠고, 아래 줄들은 전부 **때린 사람의 손맛**이다 -
    //   히트스톱·카메라 펀치·베는 소리를 남의 칼질에 내면 내 화면이 남의 손에 흔들린다.
    //   (참가자 화면에서 남의 타격을 그리는 netEvent 도 같은 이유로 손맛을 안 낸다.)
    if (h.by) return;
    // ★예측(h.predicted)은 여기를 그대로 지난다 - 히트스톱·펀치·소리·참격이 목적이다.
    //   아이템·처치 수는 아래 h.kill 갈래에만 있고 예측은 **절대 kill 이 아니라서**
    //   구조적으로 안 굴러간다(확정본이 오면 netEvent 가 같은 콜백으로 다시 부른다).
    const sa = screenAngle(h.x, h.y, h.z, swingDir.x, swingDir.y, swingDir.z);
    // ★"N HIT" 은 여기서만 뜬다. 칼이 실제로 닿은 프레임이다.
    showHit();
    logHitAngle(h.x, h.z);           // 각도 게이트 검증(?dev 에서만 쌓인다)
    // ── ★손맛 세 박자 (17차) ──
    // 순서에 뜻이 있다: **민다(펀치) -> 선다(히트스톱) -> 소리 -> 그림.**
    //   · 펀치는 이 프레임에 바로 화면에 나간다(placeCamera 가 이 tick 끝에 돈다)
    //   · 히트스톱은 다음 프레임부터 먹는다(feel.step 은 프레임 머리에서 이미 지났다)
    //   그래서 사람 눈에는 "한 프레임 밀리고 -> 그 자리에 멈춘다" 로 이어진다.
    // ★px 는 오너 기준 "절제". 명중 3px · 처치 4.6px(24m·fov24·640px 기준 0.048/0.073m).
    //   이보다 키우면 34m 쿼터뷰에서 맵이 통째로 흔들리는 그림이 된다.
    if (h.kill) {
      camPunchScreen(4.6, sa.ang, 0.24);
      addHitStop(HS_KILL, h.swing);
      feel.kill(h.swing);
      sfx.kill();
      // ★5번째 인자 kind. 안 넘기면 feel.js 가 window.__dbg 를 훔쳐보며 기술을 **추측**한다.
      //   heavy 는 수면참·횡일섬일 때만 켜지는 플래그라 그게 곧 감청(water)이다.
      feel.slash(sa.ang, sa.x, sa.y, h.wiped, heavy ? 'water' : 'kill');
      // ★★18차. 접점 연출이 스위치로 갈린다(FX_V18).
      //   1 = 파열 한 겹(방사 스파크 + 링 + 중심 섬광. 시안)
      //   0 = 옛 두 장(진홍/감청 초승달 + 먹 튀김 팝) — 아래 두 줄이 그대로 산다.
      //   ★파열의 f0(최대 프레임)이 히트스톱(처치 105ms)에 붙들린다. 그 합이 목적이다.
      if (FX_V18) feel.burst(h.x, h.y, h.z, sa.ang, 1.0, true);
      else {
        // ★맞은 자리에 참격 한 장(v92. 옛 spawnImpact = 가산합성 초승달 자리).
        //   붓자국이 화면에 앉는 큰 획이라면 이건 요괴 가슴께에 서는 작은 획이다.
        //   종류는 붓자국과 같은 규칙 - 수면참·횡일섬은 감청, 그 밖의 처치는 진홍.
        feel.impactSlash(h.x, h.y, h.z, sa.ang, 0.95, heavy ? 'water' : 'kill');
        // ★v94. 접점의 1~2프레임 팝(흰 번쩍 -> 먹 튀김). 처치도 명중이라 같이 찍는다.
        feel.pop(h.x, h.y, h.z, 1.15);
      }
      spawnInk(h.x, h.y, h.z, swingDir.x, swingDir.y, swingDir.z, 26, 1.35);
      // ★아이템 드랍. **처치 프레임의 그 자리**에서 튄다. 시체가 눕는 자리도,
      //   플레이어 발밑도 아니다 - 벤 점에서 나와야 "이 한 대가 떨어뜨렸다"로 읽힌다.
      //   h.leader 는 enemy.js 가 같은 콜백에 실어 준다(두목은 드랍률·희귀도가 높다).
      if (items) items.spawnFromKill(h.x, h.y, h.z, h.leader);
      // ★무리 전멸의 먹링은 **마지막으로 벤 자리**에 편다. 좌표를 안 넘기면 feel.js 가
      //   직전 붓자국의 화면 좌표를 월드로 되짚는다(한 프레임만 지나도 못 찾고 버린다).
      if (h.wiped) { feel.wipe(h.x, h.y, h.z); sfx.wipe(); }
    } else {
      // ★2~5번째 인자(v91). 안 죽인 한 대에도 **작은 참격 한 획**이 그어진다.
      //   각도·자리는 처치와 같은 sa 를 쓴다. 크기·알파는 feel.js 가 줄인다
      //   (임팩트 프레임과 찢김선은 안 붙는다 - 그건 처치의 몫이다).
      camPunchScreen(3.0, sa.ang, 0.17);
      addHitStop(HS_HIT, h.swing);
      feel.hit(h.swing, sa.ang, sa.x, sa.y, heavy ? 'water' : 'kill');
      sfx.hit(1);
      // ★18차. 처치와 같은 규칙으로 갈린다(파열은 처치보다 한 단 작다 - burst 안에서).
      if (FX_V18) feel.burst(h.x, h.y, h.z, sa.ang, 0.85, false);
      else {
        // ★안 죽인 명중은 감청 고정이다. 붉은색은 처치·피격 전용(오너 지시).
        feel.impactSlash(h.x, h.y, h.z, sa.ang, 0.72, 'water');
        // ★v94. 심사 격차 4: "안 죽는 적은 리본이 그냥 통과한다."
        //   맞은 그 자리에 흰 번쩍 한 장 + 먹 튀김 한 장(24fps 기준 2프레임).
        //   A3 가 넣은 적 플래시·경직(enemy.js)과 겹으로 논다.
        feel.pop(h.x, h.y, h.z, 0.9);
      }
    }
  },
  // ── 맞은 방향 (9차. 손맛 7위 "어디서 맞았는지 모른다") ──
  // ★enemy.js 는 출처 좌표를 콜백으로 안 넘긴다(넘기는 건 피해량뿐이다). 그래서
  //   "지금 나를 때릴 수 있는 자리에 있는 놈"을 여기서 되짚는다. 보스가 방금 쳤으면
  //   보스가 범인이고(0.35초 안), 아니면 제일 가까운 잡몹이다. 둘 다 없으면 무방향.
  onPlayerHurt: () => {
    feel.hurt(); sfx.hurt();
    const p = root.position;
    const B = window.__boss;
    if (B && B.pos && performance.now() - lastBossFireAt < 350) hurtFrom(B.pos.x, B.pos.z);
    else {
      const t = enemies.nearestTo(p.x, p.z, 0);
      if (t) hurtFrom(t.x, t.z); else hurtNoDir();
    }
  },
});
window.__enemy = enemies;
// 은신 모듈에 플레이어 몸을 넘긴다. 숨으면 몸이 반투명해지고 그림자가 꺼진다.
// ★root 는 캐릭터를 바꿔도 그대로 남는 그룹이다(F 로 바꾸면 자식만 갈린다).
//   stealth 쪽이 자식 수 변화를 보고 재질 목록을 다시 훑는다.
stealth.attachPlayer(root);
window.__stealth = stealth;
// 검증용 창구. ?dev 없이도 켜 둔다(읽기 전용이라 게임 동작에 영향이 없고, 실제
// 60fps 로 도는 판에서 플레이어가 어디 있는지 봐야 한 판을 끝까지 몰아볼 수 있다).
window.__pos = () => ({ x: +root.position.x.toFixed(2), y: +root.position.y.toFixed(2),
                        z: +root.position.z.toFixed(2), yaw: +root.rotation.y.toFixed(3),
                        hp: enemies.hp, kills: enemies.kills });
// ── 이동 캔슬·전진 스텝 검증 창구 (S1·S3) ──
// 읽기 전용이다. "지금 커밋 구간인가 / 언제부터 끊을 수 있나"를 숫자로 봐야
// 정지 시간을 실측할 수 있다. ?dev 없이도 열어 두는 이유는 __pos 와 같다
// (실제 60fps 로 도는 판에서 재야 의미가 있다).
// ── 타격감 창구 (17차) ──
// 읽기 전용. "지금 몇 ms 멈춰 있나 / 펀치가 몇 px 걸려 있나"를 눈이 아니라 숫자로 본다.
// ?dev 없이도 열어 둔다(__pos·__atk 과 같은 이유 — 실제 60fps 판에서 재야 의미가 있다).
window.__hitfeel = () => {
  const h = (cv && (cv.clientHeight || cv.height)) || 640;
  const mPerPx = (2 * Math.tan(camera.fov * Math.PI / 360) * dist) / h;
  return {
    stop: +hsLeft.toFixed(4), stopBudget: +hsBudget.toFixed(4), stopSwing: hsSwing,
    punchLeft: +punchLeft.toFixed(4), punchDur: +punchDur.toFixed(3),
    punchPx: +(camPunch.length() / mPerPx).toFixed(2),
    punchAmpPx: +(punchAmp / mPerPx).toFixed(2),
    shakePx: +(feel.shakeOffset().length() * SHAKE_GAIN / mPerPx).toFixed(2),
    camBase: [+camBase.x.toFixed(4), +camBase.y.toFixed(4), +camBase.z.toFixed(4)],
    coast: +coastLeft.toFixed(3),
    px: { hit: 3.0, kill: 4.6, hurt: 5.5 },
    ms: { hit: HS_HIT * 1000, kill: HS_KILL * 1000, budget: HS_BUDGET * 1000 },
  };
};
window.__atk = () => ({
  clip: atkClip, attacking,
  since: atkClip ? +(gameT - atkStartT).toFixed(3) : -1,
  commit: atkClip ? commitNow() : 0,
  step2: comboStep,
  struck: atkStruck, hot: enemies.hot,
  // ★칼끝 속도 원값도 같이 준다(읽기 전용). hot 은 0.42/0.16 을 넘었나만 알려줘서
  //   "왜 켜졌나"를 못 본다 - 클립이 바뀌는 프레임의 **포즈 점프**가 속도로 읽히는지
  //   아닌지는 이 숫자로만 가려진다(13-X 단타 조사).
  fast: +swordFast.toFixed(3), tip: +tipSpeed.toFixed(1),
  clipT: current ? +current.time.toFixed(3) : -1,
  sinceHit: atkHitT > -90 ? +(gameT - atkHitT).toFixed(3) : -1,
  cancelable: canCancelAttack(gameT),
  step: +stepDist.toFixed(3), stepLeft: +stepLeft.toFixed(3),
  snapR: SNAP_R,
  buf: BUF.kind, bufAge: BUF.kind ? +(gameT - BUF.t).toFixed(3) : -1,
  starts: atkStarts,               // 클립이 새로 시작된 누적 횟수(= 입력이 실제로 나간 수)
});
// ── 대시 검증 창구 (9차) ──
// 쿨·무적·남은 시간을 숫자로 본다. ?dev 없이도 연다(__atk 와 같은 이유).
window.__dash = () => ({
  left: +dashLeft.toFixed(3), ready: dashReady(gameT),
  cdLeft: +Math.max(0, dashReadyT - gameT).toFixed(3),
  ifLeft: +Math.max(0, dashIfUntil - gameT).toFixed(3),
  dist: DASH_DIST, dur: DASH_DUR, cd: DASH_CD, iframe: DASH_IFRAME,
  gone: +dashGone.toFixed(3),
});
// ── 판정 리치 창구 (9차) ──
// 지금 프레임에 enemy.js 로 넘어간 **판정 선분**과 그 규칙 값.
window.__reachCfg = () => ({ ext: HIT_EXT, coneDeg: HIT_CONE_DEG,
  segA: hitA.toArray().map(v => +v.toFixed(3)),
  segB: hitB.toArray().map(v => +v.toFixed(3)) });
// ── 규칙 A/B 창구 (9차) ──
// ★?dev 밖에 두는 이유는 __atk 와 같다. **실제 60fps 로 도는 판**에서 재야 의미가 있는데
//   ?dev 는 루프가 setTimeout(16) 이라 게임시계가 벽시계보다 느리게 흐른다(측정이 왜곡된다).
//   부르지 않으면 아무 일도 안 하는 읽기/설정 창구라 평시 동작에 영향이 없다.
// 후딜 캔슬 규칙: 'old'(9차 이전) | 'new'(지금)
window.__cancelMode = (m) => { if (m) cancelMode = m; return cancelMode; };
// 판정 규칙: ext(칼끝 연장 m) · cone(정면 부채꼴 반각. 180 = 게이트 없음). -1 = 기본값
window.__hitRule = (o = {}) => {
  if (o.ext !== undefined) _hitOverride.ext = o.ext;
  if (o.cone !== undefined) _hitOverride.cone = o.cone;
  return { ext: _hitOverride.ext, cone: _hitOverride.cone, defExt: HIT_EXT, defCone: HIT_CONE_DEG };
};
// 표적 거리 d 에서 전진 스텝이 몇 m 인지(사거리 검증 스크립트가 쓴다)
window.__atkStep = d => +stepDistFor(d).toFixed(3);

// ── 이동 신뢰성 계측 창구 (17차) ──
// veto  = 조각 하나가 벽 속으로 들어가서 버린 횟수(축 분리 슬라이드로 갈아탄 횟수)
// wedge = 몸이 벽 속에 있어서 빼내기가 돈 프레임 수. **평시에는 0 이어야 한다**
// maxY  = 이 판에서 플레이어가 올라간 최고 높이. 맵의 제일 높은 단(계단 1.02)을
//         넘으면 "벽 위에 올라탔다"는 뜻이다(비평 ②의 검증자).
// lift  = 지금 걸린 카메라 가림 완화 각(rad). 안 가려 있으면 0.
window.__move = () => ({
  veto: moveVeto, wedge: moveWedge, maxY: +moveMaxY.toFixed(3),
  maxGroundY: +moveMaxGY.toFixed(3),
  wedgedNow: level.blocked(root.position.x, root.position.z, WEDGE_R),
  lift: +camLift.toFixed(4), occT: +camOccT.toFixed(2),
  sub: MOVE_SUB, wedgeR: +WEDGE_R.toFixed(3), minGap: CAM_MIN_GAP,
});
window.__moveReset = () => { moveVeto = 0; moveWedge = 0; moveMaxY = 0; moveMaxGY = 0; return true; };

// ---------- 보스 · 증표 · 탈출 ----------
// 층을 "깨는" 부분이다. 자리(보스 마당·아레나·탈출구)는 전부 맵이 정한다.
// ★플레이어 체력은 enemy.js 가 한 군데서 관리한다. 보스는 그 문(damagePlayer)만 쓴다.
//   여기서 체력을 따로 들면 체력바가 두 개가 되고 무적 시간이 갈라진다.
const boss = createBossSystem({
  scene,
  getPlayerPos: () => root.position,
  // ★대시 무적은 여기서 막는다. 보스 피해는 **반드시** 이 콜백을 지나므로,
  //   enemy.js 에 무적 창구가 없어도 보스 쪽은 이 한 줄로 온전히 막힌다.
  //   (잡몹은 enemy.js 안에서 자기 damagePlayer 를 직접 불러서 여기를 안 지난다.
  //    그쪽은 setIframe 창구가 붙으면 같이 먹는다 - handoff_combat.md 참고.)
  damagePlayer: (n) => (gameT < dashIfUntil ? 0 : enemies.damagePlayer(n)),
  isPlayerDead: () => enemies.dead,
  getKills: () => enemies.kills,
  // 보스는 "무슨 일이 났는지"만 알린다. 소리·연출은 여기서 붙인다.
  // ★예고음은 예고 시작 그 프레임에, 예고 시간(dur)을 그대로 받아 올라간다.
  //   소리 쪽에서 시간을 다시 재면 언젠가 반드시 어긋난다.
  onEvent: (name, d) => {
    if (name === 'tell') sfx.bossTell(d.dur, d.atk);
    else if (name === 'tellEnd') sfx.stopTell();
    else if (name === 'fire') {
      sfx.bossHit(); feel.shake(0.10, 0.24); lastBossFireAt = performance.now();
      // 판정이 나가는 **그 프레임**의 보스-플레이어 거리. "예고 안에 장판을 벗어났는가"는
      // 이 값으로만 답할 수 있다(몇 프레임 뒤에 재면 보스가 이미 움직인 뒤다). ?dev 전용.
      if (DEV) {
        const bp = window.__boss ? window.__boss.pos : null;
        const arr = (window.__fireLog = window.__fireLog || []);
        arr.push({ atk: d.atk, t: +performance.now().toFixed(0),
                   dist: bp ? +Math.hypot(root.position.x - bp.x, root.position.z - bp.z).toFixed(2) : -1 });
        if (arr.length > 200) arr.shift();
      }
    }
    else if (name === 'hit') {
      showHit();                 // 보스도 맞으면 콤보 단수가 뜬다(잡몹과 같은 규칙)
      logHitAngle(d.x, d.z);     // 각도 게이트 검증(잡몹과 같은 창구)
      feel.hit(d.swing);
      sfx.hit(d.heavy ? 1.25 : 1);
      const sa = screenAngle(d.x, d.y, d.z, swingDir.x, swingDir.y, swingDir.z);
      // 보스 타격도 같은 한 장을 쓴다(크기만 크다). 감청 - 처치가 아니다.
      // ★18차. 잡몹과 같은 규칙으로 갈린다(보스만 다른 문법이면 화면이 두 벌이 된다).
      if (FX_V18) feel.burst(d.x, d.y, d.z, sa.ang, d.heavy ? 1.25 : 0.95, false);
      else feel.impactSlash(d.x, d.y, d.z, sa.ang, d.heavy ? 1.35 : 0.9, 'water');
    } else if (name === 'die') {
      // 보스가 쓰러진 자리에 먹링을 편다. 좌표를 안 넘기면 붓자국이 없어서
      // feel.js 가 되짚기에 실패하고 링이 아예 안 뜬다(그 경로를 안 쓰게 만든다).
      const bp = window.__boss ? window.__boss.pos : null;
      if (bp) feel.wipe(bp.x, 0, bp.z); else feel.wipe();
      sfx.wipe();
    }
    else if (name === 'token') sfx.token();
    else if (name === 'clear') sfx.clear();
  },
});
window.__boss = boss;

// ---------- 연출 껍데기 ----------
// 입장 타이틀 카드·보스 조우 배너·사망/클리어 화면·조작 안내·HUD 톤. 전부 DOM 이라
// 게임 로직과 안 섞인다. 상태는 window.__boss / window.__enemy 를 읽기만 한다.
// 쿼리(?v=..)를 물려주는 이유는 위 모듈들과 같다.
const ui = await import('./ui.js' + location.search);
ui.initUI();

// ---------- 멀티플레이 (1단계: 아바타 공유) ----------
// `?room=A7K2` 면 참가, `?host=1` 이 붙으면 방장이다(홈화면이 이 주소를 세운다).
// ★쿼리가 없으면 mp.js·net.js·peerjs 를 **한 바이트도 안 읽는다.** 혼자 하는 판의
//   로딩과 요청 수가 예전 그대로여야 한다.
// ★남에게 보내는 좌표는 root 가 아니라 **model 의 월드 위치**다. root 는 x·z 만 갖고
//   높이는 model 이 매 프레임 접지 보정으로 따로 정하기 때문이다(mp.js 머리 주석).
{
  const _q = new URLSearchParams(location.search);
  const _room = (_q.get('room') || '').trim();
  if (_room) {
    const _wp = new THREE.Vector3();
    const _isHost = _q.get('host') === '1';
    // ── 요괴를 방장 기준으로 하나로 (2단계 1차) ──
    // ★모드를 **붙기 전에** 정한다. 공용 시그널링이라 방에 들어가는 데 십여 초가 걸리는데,
    //   그 사이 참가자가 로컬 AI 로 요괴를 잡아 두면 붙는 순간 그게 전부 되살아난다
    //   ("내가 잡은 게 살아났다" 로 보인다). 방장인지 참가자인지는 주소가 이미 안다.
    if (MP_ENEMY_ON) {
      const mpeMod = await import('./mpenemy.js' + location.search);
      // ★층 이름은 getSelf 가 아바타 소식에 싣는 값과 **같은 식**이어야 한다.
      //   두 곳이 어긋나면 "아바타는 경고가 뜨는데 요괴는 조용히 틀린" 판이 된다.
      mpEnemy = mpeMod.createEnemySync({
        enemies,
        getMap: () => (IS_DUNGEON ? 'level2' : 'level1'),
        // ★방장인지 참가자인지는 **주소가 이미 안다**(net 이 붙기 전에도 확실하다).
        //   보내는 쪽·받는 쪽 갈래가 이 한 값으로 갈린다(사건은 방장만, 주장은 참가자만).
        isHost: _isHost,
      });
      enemies.setNetMode(_isHost ? 'host' : 'remote');
    }
    const mpMod = await import('./mp.js' + location.search);
    multi = mpMod.createMultiplayer({
      THREE, scene, loader, glbUrl, CHAR_CFG, DEF_CFG,
      // ★요괴 동기화. **스위치(MP_ENEMY_ON)의 정의는 위 한 곳**이고 mp.js 는
      //   이 값이 null 인지만 본다(스위치를 두 벌 두면 반드시 어긋난다).
      enemy: mpEnemy,
      // ★남의 공격 이펙트. **스위치(MP_FX_ON)의 정의는 main.js 한 곳**이고 mp.js 는
      //   이 값이 null 인지만 본다(스위치를 두 벌 두면 반드시 어긋난다).
      fx: mpFx,
      getSelf() {
        if (!model) return null;
        model.getWorldPosition(_wp);
        return {
          x: +_wp.x.toFixed(3), y: +_wp.y.toFixed(3), z: +_wp.z.toFixed(3),
          yaw: +root.rotation.y.toFixed(3),
          clip: clipNameOf(current),
          // 클립 안 재생 시각. 3연타는 play() 를 다시 부르지 않고 **클립 시간을
          // 점프**해서 낸다(ATK_ENTRY). 이 값이 없으면 남의 화면에서 1타만 나온다.
          pt: current ? +current.time.toFixed(3) : 0,
          // ★재생속도도 보낸다. 공격은 캐릭터별로 갈리고(검사 1.35 / 궁수 2.00)
          //   받는 쪽이 1.0 으로 틀면 같은 모션이 다른 속도로 돌아 어긋난다.
          ts: current ? +current.timeScale.toFixed(3) : 1,
          // ★공격이 **다시 시작**된 횟수. 3연타는 클립 이름도 안 바뀌고 play() 도
          //   안 거치므로, 이 수가 없으면 남의 화면에서 1타만 보이고 만다.
          atk: atkStarts,
          char: curChar || 'basic2',
          // ★남이 쏜 화살. 막 쏜 뒤 0.6초 동안만 실린다(그 밖에는 null 이라 평시
          //   소식 크기가 예전 그대로다). 받는 쪽은 번호로 중복을 버린다.
          sh: mpShotWire(),
          // ★죽어 있나(2차). 죽은 사람은 요괴의 표적에서 빠진다 - 안 빼면 무리가
          //   시체 곁에 모여 서서 허공에 칼질을 한다. **죽었을 때만** 실리므로
          //   평시 소식 크기는 예전 그대로다(sh 와 같은 규칙).
          d: enemies.hp <= 0 ? 1 : undefined,
          // 어느 층에 있는지. 서로 다른 층에 들어가면 아무도 안 보이는데, 그게
          // "연결이 안 됐다"와 화면상 구분이 안 된다. 받는 쪽이 경고를 띄우게 알린다.
          map: IS_DUNGEON ? 'level2' : 'level1',
        };
      },
    });
    multi.start(_isHost ? 'host' : 'join', _room)
      .catch(e => {
        console.warn('[mp] 연결 실패:', e && e.message);
        // ★못 붙었으면 요괴를 내가 굴린다. 안 그러면 빈 들판에서 혼자 걷게 된다
        //   (참가자 모드는 소식이 와야 요괴가 서는데, 올 데가 없다).
        if (mpEnemy) enemies.setNetMode('local');
      });
  }
}

function tick() {
  nextFrame(tick);
  __frames++;
  window.__tickN = __frames;
  window.__hasHand = !!handBone;
  // ── 시간 ──
  // ★여기서 dt 를 **한 번만** 스케일한다. 아래로 흐르는 dt 는 전부 게임시간이라
  //   mixer·요괴·보스·궤적이 같은 값으로 멈춘다. 카메라 이동과 흔들림만 rawDt 를 쓴다.
  // ★__slow 는 **검증 전용** 배속이다(기본 1). 0.15 로 두면 게임·연출·흔들림이
  //   통째로 6배 느려져서 60~200ms 짜리 타격 연출을 스크린샷으로 잡을 수 있다.
  //   게임 로직은 그대로 도므로 "느리게 재생한 실제 판"이지 별도 데모가 아니다.
  const rawDt = Math.min(0.05, clock.getDelta()) * (window.__slow || 1);
  // ★부팅 게이트는 **클램프 전 값**을 봐야 한다. rawDt 는 0.05 로 잘려 있어서
  //   1.3초짜리 파싱 히치도 0.05 로 보인다. clock.getDelta 는 이미 소비됐으므로
  //   프레임 사이 벽시계 간격을 따로 잰다.
  const _wall = performance.now();
  bootGate((_wall - lastFrameWall) / 1000);
  lastFrameWall = _wall;
  // ★시간 배율은 두 층이다(feel.js 히트스톱·슬로모 / 여기 히트스톱). **더 멈춘 쪽**만
  //   쓴다 — 곱하면 두 겹이 서로 배가돼서 명중 한 번에 세상이 400배 느려진다.
  // ★사망 슬로모가 걸리면 내 히트스톱은 즉시 버린다. feel.js 의 death() 도 같은 이유로
  //   자기 stopT 를 0 으로 민다 — "마지막 한 마리를 베면서 같이 죽는" 프레임에서
  //   히트스톱이 남아 있으면 사망 슬로모가 최대 112ms 뒤로 밀린다(죽은 줄 늦게 안다).
  // ★feel.state 는 매번 객체를 새로 짓는 진단 창구다. 히트스톱이 걸려 있는 프레임에서만
  //   본다(평시에는 이 줄이 비교 한 번으로 끝난다).
  if (hsLeft > 0 && feel.state.death > 0) { hsLeft = 0; hsBudget = 0; }
  const _tScale = Math.min(feel.step(rawDt), stepHitStop(rawDt));
  // 이 프레임이 '히트스톱으로 멈춘 프레임'인가. 사망 슬로모(0.30)·전멸 슬로모(0.35)는
  // 아니다 — 그 둘은 카메라가 계속 흘러야 늘어지는 맛이 산다.
  const hitFrozen = _tScale <= 0.12;
  const dt = rawDt * _tScale;
  gameT += dt;
  const now = gameT;                 // 게임 안의 모든 "지금"은 이 시계를 본다
  for (const m of glowMats) m.userData.u.uT.value = now;
  trailMat.uniforms.uT.value = now;

  // 이동
  let mx = 0, mz = 0;
  if (keys.KeyW || keys.ArrowUp) mz -= 1;
  if (keys.KeyS || keys.ArrowDown) mz += 1;
  if (keys.KeyA || keys.ArrowLeft) mx -= 1;
  if (keys.KeyD || keys.ArrowRight) mx += 1;
  const running = !!(keys.ShiftLeft || keys.ShiftRight);
  // 미리보기 중에는 이동 입력을 무시한다. 걸어가 버리면 모션을 볼 수가 없다.
  // (카메라·조명은 그대로 두므로 마우스 시점·휠 줌은 계속 된다)
  // ★층 돌파 뒤에도 같다. 키가 이미 눌린 채로 판이 끝나면 keydown 게이트를 안 지나므로
  //   여기서 한 번 더 끊어야 "패널 뜬 채로 걸어다니는" 그림이 안 나온다.
  const cleared = !!boss.cleared;
  if (preview.on || cleared) { mx = 0; mz = 0; }
  if (dashLeft > 0) { mx = 0; mz = 0; }      // 대시 중에는 방향키가 궤도를 못 휜다
  // ── 선입력 풀기 (9차) ──
  // ★이동 캔슬보다 **먼저** 본다. 예약해 둔 공격이 있으면 그게 이번 프레임의 답이다.
  //   (뒤에 두면 방향키를 누른 채 연타할 때 이동 캔슬이 먼저 먹어서 예약이 버려진다.)
  if (bufferAlive(now) && dashLeft <= 0 && !cleared && !preview.on &&
      (!attacking || canCancelAttack(now))) {
    const k = BUF.kind;
    clearBuffer();
    if (k === 'atk') tryAttack();
    else if (k === 'heavy') tryHeavy();
    else if (k === 'wide') tryWide();
    else if (k === 'dash') tryDash();
  } else if (BUF.kind && !bufferAlive(now)) {
    // ★예약이 만료됐다 = 그 입력은 끝내 안 나갔다. **그때만** 거부 피드백을 낸다
    //   (손맛 8위 "씹힘인지 버그인지 구분 불가"). Z 는 뺀다 - 연타로 누르는 키라
    //   흘린 입력마다 소리를 내면 그게 잡음이 된다.
    if (BUF.kind === 'heavy' || BUF.kind === 'wide' || BUF.kind === 'dash') deny(BUF.kind);
    clearBuffer();
  }
  // ── 이동 캔슬 (S1) ──
  // ★위 두 줄 **뒤에** 있어야 한다. 미리보기·층 돌파에서는 mx/mz 가 이미 0 이라
  //   여기서 저절로 안 걸린다(게이트를 또 적을 필요가 없다).
  // 타격이 끝난 회복 동작만 끊는다. 판단 근거는 canCancelAttack(= enemy.js 의 hot).
  if (attacking && (mx || mz) && canCancelAttack(now)) {
    attacking = false; heavy = false; atkClip = null;
    clearBuffer();                   // 이동을 택한 프레임이다. 예약해 둔 Z 를 자동으로 잇지 않는다
    // 캔슬한 그 프레임에 바로 걸음으로 넘긴다. 아래 상태 기계가 다음 프레임에 해도
    // 되지만, 한 프레임이라도 Attack 포즈로 미끄러지면 "밀린다"로 읽힌다.
    // 크로스페이드를 기본(0.18)보다 짧게 주는 이유도 같다.
    // ★comboWindow 는 **일부러 안 건드린다.** 캔슬 뒤에 Z 를 이으면 다음 타로 이어져야 한다.
    play(running ? 'Run' : 'Walk', 0.12);
  }
  // ── ★벽 속에서 빼내기 (17-이동신뢰성) ──
  // 어떤 경로로든 몸이 벽 속(콜라이더 사이 0.22~0.44m 짜리 금)에 들어가 있으면,
  // 이 프레임의 입력을 접고 제일 가까운 설 수 있는 자리로 빼낸다. 아래 moveBy 는
  // 벽 속에서는 두 축이 다 막혀서 한 조각도 못 나가므로(= 40초 정지), 여기가 먼저다.
  const wedged = unwedge(rawDt);
  if (root.position.y > moveMaxY) moveMaxY = root.position.y;
  // ★"벽 위에 올라탔나"의 진짜 자는 이쪽이다. maxY 는 점프가 섞여서 못 쓴다
  //   (대시 키를 방향 없이 누르면 점프가 나간다). 발이 딛고 선 면의 높이는
  //   맵의 제일 높은 단(계단 꼭대기 1.02)을 절대 넘을 수 없다.
  {
    const _gy = level.groundY(root.position.x, root.position.z);
    if (_gy > moveMaxGY) moveMaxGY = _gy;
  }
  const moving = !wedged && (mx || mz) && !attacking && dashLeft <= 0;
  if (moving) {
    fwd.set(Math.sin(yaw), 0, Math.cos(yaw));
    rightv.set(Math.cos(yaw), 0, -Math.sin(yaw));
    move.set(0, 0, 0).addScaledVector(fwd, mz).addScaledVector(rightv, mx).normalize();
    const spd = running ? curCfg.run.spd : curCfg.walk.spd;
    // ★코스트(관성)를 매 프레임 새로 채운다. 키를 떼는 순간의 속도·방향이 그대로 남는다.
    coastVX = move.x * spd; coastVZ = move.z * spd;
    coastLeft = COAST_T; coastRun = running;
    // ★벽에 부딪히면 멈추는 게 아니라 미끄러진다(level.js slide). 이동을 통째로
    //   취소하면 벽을 스치며 걸을 때마다 딱딱 멈춰서 조작이 답답해진다.
    //   몸이 향하는 방향(targetYaw)은 밀려난 결과가 아니라 **입력**으로 정한다.
    //   밀려난 방향으로 돌리면 벽에 붙어 걸을 때 몸이 벽을 향해 홱 돈다.
    // ★17차부터 이동은 전부 moveBy 한 문으로만 나간다(조각내기 + 벽 속 거부 + 축 분리).
    moveBy(move.x * spd * dt, move.z * spd * dt);
    const targetYaw = Math.atan2(move.x, move.z);
    let d = targetYaw - root.rotation.y;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    root.rotation.y += d * Math.min(1, dt * 14);
  } else if (coastLeft > 0) {
    // ── ★감속 코스트 (17차. 모션 비평가 "달리기 종료가 1프레임 스냅") ──
    // 키를 떼면 속도가 **한 프레임에 5.5m/s -> 0** 이었다. 클립은 0.18초에 걸쳐
    // 크로스페이드되는데 몸은 그 자리에 못이 박혀서, 발만 움직이고 세상은 딱 서는
    // 그림이 됐다. 남은 속도를 k^2 로 0.16초 동안 흘려보낸다.
    //   총 이동거리 = v x COAST_T / 3 = 달리기 기준 약 0.29m (반 걸음)
    // ★공격·대시·점프가 시작되면 즉시 버린다(그쪽 이동과 겹치면 두 배로 미끄러진다).
    // ★벽 통과는 이동·대시·전진스텝과 **같은 level.slide** 를 지난다.
    // ★17-이동신뢰성 담당자에게: 이 블록은 '입력이 없을 때'만 돈다. 이동 로직을
    //   새로 짜면 coastVX/VZ 를 채워 주는 한 줄(위 moving 블록)만 옮기면 된다.
    if (attacking || dashLeft > 0 || jumping) { coastLeft = 0; }
    else {
      coastLeft = Math.max(0, coastLeft - dt);
      const ck = coastLeft / COAST_T;                  // 1 -> 0
      const cs = ck * ck;
      moveBy(coastVX * cs * dt, coastVZ * cs * dt);
    }
  }

  // ── 대시 (9차) ──
  // ★게임시간(dt)으로 민다. 히트스톱이 걸려 있으면 대시도 같이 멈춰야 화면과 안 어긋난다.
  // ★벽 통과는 이동·전진스텝과 **같은 level.slide** 를 지난다(규칙이 갈라지면 안 된다).
  //   그래서 벽에 막히면 그만큼 덜 간다 = "벽으로는 못 피한다"가 저절로 성립한다.
  if (dashLeft > 0) {
    const p0 = dashGone;
    dashLeft = Math.max(0, dashLeft - dt);
    dashGone = dashEase(1 - dashLeft / DASH_DUR) * DASH_DIST;
    const k = dashGone - p0;
    // ★한 프레임에 최대 0.885m 를 가는 이 줄이 "벽 속 끼임" 의 진범이었다(18.13%).
    //   moveBy 가 0.09m 씩 잘라서 민다 — 그래서 벽 앞에서 정확히 멈춘다.
    moveBy(dashDX * k, dashDZ * k);
    if (dashLeft <= 0) { dashGone = 0; restoreDashTs(); }
  }

  // ── 전진 스텝 (S3) ──
  // 공격 시작에 섞이는 0.14초짜리 짧은 미끄러짐. 몸이 향한 쪽으로만 간다.
  // ★몸 방향은 스냅(enemy.js stepSnap, 0.09초)이 매 프레임 돌리고 있으므로,
  //   여기서 그때그때 root.rotation.y 를 읽으면 스텝이 스냅을 따라 휜다
  //   = "돌면서 한 발 들어간다". 시작 순간의 방향으로 고정하면 옆으로 새 보인다.
  // ★벽 통과는 level.slide 가 막는다(이동과 같은 함수라 규칙이 갈라지지 않는다).
  if (stepLeft > 0) {
    const p0 = 1 - stepLeft / STEP_DUR;
    stepLeft = Math.max(0, stepLeft - dt);
    const k = (stepEase(1 - stepLeft / STEP_DUR) - stepEase(p0)) * stepDist;
    const yy = root.rotation.y;
    moveBy(Math.sin(yy) * k, Math.cos(yy) * k);
  }

  // 중력·착지·지면 높이
  // ★바닥은 더 이상 y=0 평면이 아니다. 맵 평지가 0.02 이고 대웅전 단 위는 0.22 다.
  //   groundFeet() 가 root.position.y 를 기준으로 발을 붙이므로 여기만 맞추면 된다.
  const gy = level.groundY(root.position.x, root.position.z);
  if (!grounded || vy !== 0) {
    vy -= GRAV * dt;
    root.position.y += vy * dt;
    if (root.position.y <= gy) { root.position.y = gy; vy = 0; grounded = true; }
  } else if (root.position.y !== gy) {
    // 단을 오르내릴 때. 20cm 를 한 프레임에 순간이동하면 눈에 띄니 0.1초쯤 걸려 따라간다.
    // (완전한 지형 추종은 아니다. 맵에 올라설 수 있는 건 20~26cm 단 셋뿐이라 이걸로 족하다)
    root.position.y += (gy - root.position.y) * Math.min(1, dt * 18);
    if (Math.abs(gy - root.position.y) < 0.002) root.position.y = gy;
  }

  if (attacking && now > attackEnd) {
    attacking = false; heavy = false; atkClip = null;
    // ★예약(선입력)을 푸는 자리는 이제 루프 위쪽 한 군데다(캔슬 프레임 포함).
    //   여기서 또 풀면 같은 입력이 두 번 나간다.
  }
  // 그림자 카메라가 캐릭터를 따라가야 범위를 좁게 유지할 수 있다(= 선명한 그림자).
  key.target.position.copy(root.position);
  key.position.set(root.position.x + 5, 9, root.position.z + 4);

  if (mixer && !window.__freeze && preview.on) {
    // ── 미리보기 모드 ──
    // ★아래 상태 기계 블록을 통째로 건너뛴다. 저 블록은 매 프레임 play('Idle') /
    //   play('Walk') 를 부르기 때문에, 안 건너뛰면 고른 클립이 다음 프레임에 바로 덮인다.
    //   점프 보정(actions.Jump.time 조작)도 여기선 안 돈다. 점프 클립이 없는 캐릭터에서
    //   undefined.time 으로 루프가 죽던 그 코드 경로를 아예 안 밟는다는 뜻이다.
    //   재생속도는 액션의 timeScale 을 안 건드리고 mixer 에 먹이는 dt 로만 조절한다.
    //   (걷기/달리기는 timeScale 이 캐릭터마다 다르게 박혀 있어서 손대면 게임이 틀어진다)
    mixer.update(preview.paused ? 0 : dt * preview.rate);
    if (grounded) groundFeet();
  } else if (mixer && !window.__freeze) {
    if (attacking) { /* Attack 유지 */ }
    else if (dashLeft > 0) { /* 대시 클립 유지. 안 막으면 아래 play('Idle') 이 매 프레임 덮는다 */ }
    else if (jumping) { /* Jump 유지 */ }
    else if (moving) play(running ? 'Run' : 'Walk');
    // ★코스트 앞 절반은 걷기/달리기 클립을 붙들고 있는다. 몸이 아직 0.2m 쯤
    //   미끄러지는 중인데 클립만 Idle 로 넘기면 그게 발 미끄러짐이다.
    //   뒤 절반에서 Idle 로 넘기면 남은 크로스페이드(0.18초)와 남은 코스트가 겹쳐
    //   "속도가 줄면서 자세가 선다" 한 문장이 된다.
    else if (coastLeft > COAST_T * 0.5) play(coastRun ? 'Run' : 'Walk');
    else play('Idle');
    mixer.update(dt);
    if (jumping && !actions.Jump) {
      // ★점프 클립이 없는 캐릭터(Meshy 임포트 등)에서 여기서 a.time 을 건드려
      // TypeError 가 나면 렌더 루프가 통째로 멈춘다(스페이스 누르면 정지).
      if (grounded) jumping = false;
    } else if (jumping) {
      const a = actions.Jump;
      const J = curCfg.jump || DEF_CFG.jump;
      const RISE = J.rise, FALL = J.fall, LAND = J.land, END = J.end;
      if (!grounded) {
        // 체공시간이 상황마다 다르므로 구간마다 버틴다.
        // 올라갈 땐 무릎을 당긴 채, 내려올 땐 발을 내린 채.
        // 상한만 걸어 시간이 자연히 흐르게 한다. 특정 프레임에 강제 대입하면
        // 정점에서 7 -> 13 으로 건너뛰어 다리가 툭 펴지는 스냅이 생긴다.
        a.time = Math.min(a.time, vy > 0 ? RISE : FALL);
      } else {
        if (a.time < LAND) a.time = LAND;          // 착지 구간부터 이어붙인다
        if (a.time >= END - 1e-3) jumping = false;
      }
      mixer.update(0);
    }
    if (grounded) groundFeet();      // 공중에선 접지를 끄지 않으면 다리 접기가 상쇄된다
  }

  // 칼 궤적 기록 (칼날 축은 measureBlade 가 실측한 값)
  // __freeze 중에는 건드리지 않는다 - __bakeTrail 이 구워둔 궤적이 덮어써진다.
  // ── 궤적 크기 ──
  // ★오너: "일반 Z 3연타에도 물의 호흡 궤적을 크고 또렷하게. 3타는 특히 크게."
  //   귀멸에서 잡졸을 벨 때도 물결이 화면을 쓸고 지나간다. 예전 값(일반 1.15)은
  //   일격기(2.4)와 격차가 너무 커서 3연타가 "그냥 칼질"로 보였다.
  //   한 클립 안에서 1타 1.55 -> 2타 1.80 -> 3타 2.20 으로 **점점 커지게** 한다.
  //   마무리가 제일 커야 3연타가 하나의 문장으로 읽힌다.
  // ★v94. 값을 한 단씩 내렸다(2.4 -> 1.85, 1.50/1.75/2.05 -> 1.35/1.55/1.80).
  //   폭의 뜻이 바뀌었기 때문이다. 예전 gain 은 **칼날 축 위 구간**을 부풀렸지만
  //   지금은 **캐릭터에서 바깥으로 뻗는 거리**를 부풀린다. 옛 값을 그대로 쓰면
  //   바깥 끝이 판정 리치 3.2m 를 넘어가 clampReach 에 눌려 납작해진다.
  let gainTarget = 1.15;
  if (heavy) gainTarget = 1.85;
  else if (attacking) {
    gainTarget = 1.45;
    if (current && current === actions.Attack) {
      const cdur = current.getClip().duration;
      const u = cdur > 0 ? current.time / cdur : 0;
      // ★2026-08-12 14-베기수정. 클립이 1.500초로 줄어 자리가 또 옮겨졌다.
      //   스윙 셋이 있는 자리 u = 0.12~0.27 / 0.39~0.51 / 0.79~0.95 (옛 0.09~0.30 /
      //   0.43~0.52 / 0.76~0.93). 문턱 0.33·0.65 가 그 사이 골에 정확히 들어간다.
      // ★2026-08-13 15-모션수제. 클립 길이는 1.500초 그대로인데 스윙 자리가 옮겨졌다:
      //   u = 0.15~0.26 / 0.53~0.63 / 0.90~0.99. 문턱을 그 사이 골로 옮긴다(0.39·0.76).
      gainTarget = u > 0.76 ? 1.80 : (u > 0.39 ? 1.55 : 1.35);
    }
  }
  trailGain += (gainTarget - trailGain) * Math.min(1, dt * 9);
  if (handBone && bladeOK && !window.__freeze) {
    handBone.updateWorldMatrix(true, false);
    const a = swordA.copy(bladeA).applyMatrix4(handBone.matrixWorld).clone();
    const b = swordB.copy(bladeB).applyMatrix4(handBone.matrixWorld).clone();
    // 칼끝 속도 하나로 둘을 함께 몬다:
    //   느리다(들어올릴 때) -> 리본이 칼을 감고, 궤적은 거의 안 생긴다
    //   빠르다(벨 때)       -> 리본이 풀려 꼬리가 되고, 궤적(파도)이 터진다
    if (lastTip) tipSpeed = _spd.copy(b).sub(lastTip).length() / Math.max(dt, 1e-3);
    lastTip = (lastTip || new THREE.Vector3()).copy(b);
    // ★이번 프레임 칼끝 진행 방향. onHit 이 붓질·초승달을 이 방향으로 눕힌다.
    //   _spd 는 아래에서 여러 번 재사용되므로 여기서 따로 떠 둔다.
    if (_spd.lengthSq() > 1e-9) swingDir.copy(_spd).normalize();
    swordFast = Math.min(1, Math.max(0, (tipSpeed / FAST_REF - 0.12) / 0.55));
    // ★3연타는 **마지막 3타**에서 터져야 한다.
    // 이펙트는 "칼끝이 제일 빨라지는 순간" 한 번 터지는데, 2026-08-08 에 베기 모션을
    // 되돌리면서 1타가 3타보다 빨라졌다(1타 43.8 / 3타 39.6 m/s). 그래서 첫 방에
    // 다 터지고 나머지 두 방이 밋밋해졌다. 속도만 보면 안 되고 **클립 진행도**를 같이 본다.
    // 수면참·횡일섬은 한 방짜리라 게이트를 안 건다.
    let burstOK = true;
    if (current && current === actions.Attack) {
      const cd = current.getClip().duration;
      // 3타 구간 (13-모션이식으로 0.58->0.65. 14-베기수정에서도 0.65 가 맞는다 -
      // 새 클립 1.500초에서 3타 진입점이 u 0.733, 타격이 u 0.79~0.95 라 문턱 위다)
      burstOK = cd > 0 && current.time > cd * 0.65;
    }
    if (attacking && swordFast > 0.55 && burstOK) {
      if (!released) spawnBurst(a, b, _spd);   // 타격 순간 한 번: 충격 링 + 물보라
      released = true;
    }
    // ── 화면공간 본 획 (v94) ──
    // ★심사 1순위: "귀멸은 화면에 그은 획, 게임은 지형 원근에 눕는 깔개."
    //   지금까지 화면에 큰 획이 그어지는 건 **처치한 프레임뿐**이었다. 그래서 안 죽는
    //   적을 상대로는 화면에 아무 그림도 안 남고 월드 리본만 보였다.
    //   귀멸은 반대다 - **휘두를 때마다** 화면에 획이 한 장 그어진다.
    // ★스윙 번호(enemies.swing)를 안 쓴다. 그건 전투 구역 소유고, 무엇보다 요괴가
    //   없으면 안 올라간다("허공에 휘둘러도 획은 그어져야 한다").
    //   대신 칼끝이 빨라지는 순간을 직접 본다. 0.11초 게이트는 9차에서 스윙 간격이
    //   0.14~0.17초까지 좁혀졌으므로(handoff_combat) 두 스윙이 하나로 안 뭉친다.
    // ★몸 보정 구간(CAST_SETTLE)에는 안 긋는다. 그 구간의 칼끝 속도는 휘두른 게 아니라
    //   스냅·전진 스텝이 **몸을** 옮긴 것이라, 여기까지 열어 두면 수면참 한 번에 획이
    //   두 장 그어진다(0.02초에 한 장, 0.83초 슬램에 한 장). 눈에는 그게 곧 "2타"다.
    if (attacking && swordFast > 0.52 && gameT - lastSwingFxT > 0.11 && !castSettling(gameT)) {
      lastSwingFxT = gameT;
      const sa = screenAngle(b.x, b.y, b.z, swingDir.x, swingDir.y, swingDir.z);
      // ★획의 자리를 **캐릭터 바깥으로** 한 뼘 민다. 칼끝 화면 좌표 그대로 두면 획이
      //   캐릭터를 한가운데 놓고 그어져서 타격 애니가 안 보인다(캐릭터 심사 FAIL 의
      //   직접 원인). 벤 방향은 그대로고 자리만 바깥으로 나간다.
      const sp = screenAngle(root.position.x, root.position.y + charH * 0.55,
                             root.position.z, 0, 1, 0);
      let ox = sa.x - sp.x, oy = sa.y - sp.y;
      const ol = Math.hypot(ox, oy) || 1;
      ox /= ol; oy /= ol;
      // ★획의 색 = 지금 든 칼의 원소 색. 안 물리면 일곱 자루가 화면에서 다 같아진다
      //   (본 획이 모든 스윙에 그어지므로 이게 곧 칼의 정체가 된다).
      //   붉은 계열은 처치·피격 전용이라 홍염(주홍)도 진홍 처치획과는 안 겹친다.
      applySwingPalette();
      // ★0.26 -> 0.34. 실측에서 **처치 프레임의 몸 가림이 0.15 -> 0.23~0.32초로 나빠졌다**
      //   (획을 키운 값). 획을 줄이는 대신 자리를 몸에서 더 밀어내면 화면 존재감은
      //   지키면서 몸만 비켜 간다.
      feel.swing(sa.ang, sa.x + ox * 0.34, sa.y + oy * 0.34, heavy, 'el');
    }
    // 모으는 동안(느릴 때)엔 물자국을 아예 안 남긴다. 조금이라도 남기면
    // 어두운 판때기가 칼 뒤에 붙어 '기를 모으는' 그림을 망친다.
    const wake = Math.max(0, (swordFast - 0.28) / 0.72);
    // ★별똥별 꼬리: 기록된 순간부터 계속 삭는다. 예전엔 저장된 26개를 전부
    // 살려둬서, 칼이 호를 다 그리고 나면 지나간 자국이 통째로 남아 "그려놓은 호"가 됐다.
    // 실제 꼬리는 머리 쪽만 진하고 뒤는 이미 흩어져 있다.
    // ★"자유로운 물결": 물은 칼 궤적에 붙박이가 아니라 **칼을 떠나 날아간다.**
    // 각 샘플에 기록 순간의 칼끝 속도를 심어두고 매 프레임 그 방향으로 흘려보낸다.
    // 곡률(회전)을 살짝 줘서 뻗어나가며 말리게 한다. 이게 없으면 스윙 폭 그대로의
    // 짧은 호로 끝난다(오너: "칼도 시원하게, 지금 너무 짧아").
    // ★v94. 지수 감쇠(0.92^프레임, 0.41초)를 없앴다. 그게 "이펙트가 0.3~0.9초 동안
    //   몸을 덮는다"의 절반이었다. 이제 수명은 샘플이 태어난 **1/24 칸 번호**(e.f)로
    //   세고 계단표(TRAIL_LADDER)가 정한다 - 본 획 넉 장(0.167초) + 먹 자취 두 장.
    //   e.t 는 이제 '태어날 때의 세기'로 고정이고 시간에 따라 안 변한다.
    for (const e of trailBuf) {
      if (e.vb) {
        e.a.addScaledVector(e.va, dt);
        e.b.addScaledVector(e.vb, dt);
        e.vb.applyAxisAngle(_advAxis, 1.3 * dt);
        e.va.multiplyScalar(Math.pow(0.40, dt));
        e.vb.multiplyScalar(Math.pow(0.40, dt));
      }
    }
    const invDt = 1 / Math.max(dt, 1e-3);
    // ★날아가는 몫을 0.10/0.32 -> 0.06/0.16 으로 줄였다. 예전 값이면 샘플이 0.15초에
    //   1.9m 를 더 날아가서 궤적이 판정 리치 밖으로 통째로 밀려났다(크기 계약 위반).
    //   지금은 리치 밖을 안 그리므로 많이 날려 봐야 잘려 사라질 뿐이다.
    trailBuf.push({ a, b, t: attacking ? wake : 0, f: Math.floor(gameT * FX_FPS),
      va: _spd.clone().multiplyScalar((attacking ? 0.06 : 0) * invDt),
      vb: _spd.clone().multiplyScalar((attacking ? 0.16 : 0) * invDt) });
    while (trailBuf.length > TRAIL_MAX) trailBuf.shift();
    updateTrail();
    feel.trailFoamSample(a, b, attacking ? wake : 0, root.position, charH);  // ★16-FX 포말 마루 통로(한 줄)
    updateWrap(dt, a, b, attacking);
    // 베는 동안에만 조각이 튄다. 세게 벨수록 많이.
    if (attacking && wake > 0.15) {
      // ★v96. (2 + wake*9) -> (0.8 + wake*3.2). 옛 값은 초당 660개라 조각이 늘 260개
      //   상한(SPRAY_MAX)에 붙어 있었다 = 칼 주변이 아니라 **구름**이었다.
      // ★v97. (1.4 + wake*5.6) = 9차의 6할. 상한에 안 붙는 선에서 물의 양을 되돌린다.
      sprayAcc += dt * 60 * (1.4 + wake * 5.6) * (heavy ? 1.7 : 1.0) * curEl.spray;
      const nSp = Math.floor(sprayAcc);
      sprayAcc -= nSp;
      if (nSp > 0) spawnSpray(a, b, _spd.clone().normalize(), nSp, heavy ? 1.5 : 1.0);
    }
    updateSpray(dt);
    updateBursts(dt);
  }
  // ★타격 지점 참격은 이제 feel.js 안에서 돈다(updateOverlay). 게임시계로 늙는
  //   성질은 그대로 옮겼다 - 히트스톱 중에는 한 장을 붙들고 있다가 풀리면서 이어진다.
  //   실제 dt 로 돌리면 멈춘 사이에 여섯 장이 혼자 다 지나가 버린다.

  // ── 요괴 ──
  // 타격 구간은 칼끝 속도(swordFast)로 정한다. 궤적(trail)이 진해지는 구간과
  // 같은 신호를 쓰므로 "눈에 보이는 칼 궤적 = 판정"이 구조적으로 보장된다.
  // 칼이 없는 캐릭터(기본·기본2)는 bladeOK 가 false 라 a/b 가 null 로 나가고,
  // 그러면 판정 자체가 안 돈다(에러 없음).
  {
    // ★은신 판정은 요괴보다 **먼저** 돌아야 한다. 요괴가 이번 프레임의 canSee 를
    //   읽기 때문이다. 순서가 뒤집히면 한 프레임 늦은 상태로 어그로가 걸린다.
    //   moving/running 은 위 이동 블록이 이번 프레임에 계산한 값 그대로다
    //   (걷기는 조용하고 달리기는 소리가 샌다 = 수풀에서 달리면 들킨다).
    stealth.update(dt, { x: root.position.x, z: root.position.z,
                         moving: !!moving, running: running && !!moving, attacking });
    const bladeLive = !!(handBone && bladeOK && !window.__freeze);
    // ★판정에 넘기는 선분은 **보이는 칼 그대로가 아니다**(위 makeHitSeg 주석).
    //   리치를 조금 늘리고 정면 부채꼴 밖을 잘라 낸 선분이다. 잡몹·보스가 같은 값을 본다.
    if (bladeLive) makeHitSeg(swordA, swordB);
    // ★한 방짜리 기술의 몸 보정 구간에는 칼끝 속도를 **판정으로 안 넘긴다**(위 CAST_SETTLE).
    //   보이는 칼·궤적·리본은 그대로 swordFast 를 쓴다 - 가리는 건 판정 입력 하나뿐이다.
    const settling = castSettling(now);
    enemies.update(dt, {
      a: bladeLive ? hitA : null,
      b: bladeLive ? hitB : null,
      attacking,
      fast: (bladeLive && !settling) ? swordFast : 0,
      // ★이번 캐스트의 신원. 공격 클립이 새로 시작될 때만 올라가는 수라(atkStarts)
      //   enemy.js 가 "같은 캐스트인가"를 이걸로 가린다.
      cast: atkStarts,
      // 한 방짜리 기술(수면참·횡일섬)인가. enemy.js 가 이 캐스트에는 스윙 번호를 하나만 준다.
      single: attacking && isOneShotClip(),
      // ★어떤 기술로 때리는가(Attack=Z · Heavy=X · Wide=C). enemy.js 의 기술 배율이
      //   이 한 줄을 읽는다. 넘기지 않으면 그 파일이 속도·single 로 **추측**하게 되는데,
      //   17차에 feel.slash 에서 같은 추측을 걷어낸 이유가 그것이다(추측은 틀린다).
      kind: atkClip,
      // ★층 돌파 뒤에는 요괴도 멈춘다. 입력만 잠그면 "층 돌파" 패널이 뜬 채로 요괴가
      //   계속 때리고, 그 넉백(enemy.js damagePlayer)이 플레이어를 조금씩 밀어낸다.
      //   판이 끝난 화면에서 움직이는 건 아무것도 없어야 한다.
      paused: preview.on || cleared,
      // ★함께 있는 사람들(2차). 요괴가 **제일 가까운 사람**을 쫓는 근거다.
      //   혼자 하는 판에서는 multi 가 null 이라 이 칸이 null 이고, enemy.js 는
      //   예전처럼 나 하나만 본다(코드 경로가 한 글자도 안 갈린다).
      //   ★게터를 **여기서** 읽는다 - mp.js 의 update 는 이 뒤에 돌기 때문에
      //     미리 만들어 두면 한 프레임 낡은 자리를 쫓게 된다.
      players: multi ? multi.players : null,
    });
    // ★이동 캔슬(S1)의 근거를 여기서 적는다. 이번 프레임의 타격 구간(hot)은 방금
    //   enemies.update 가 정했다. 위쪽 이동 블록은 **한 프레임 전 값**을 보게 되는데,
    //   그 방향의 오차는 "한 프레임 늦게 끊긴다" 뿐이라 안전한 쪽이다
    //   (반대로 미리 끊으면 칼이 나가는 중에 걸음으로 넘어간다).
    if (attacking && enemies.hot) atkStruck = true;
    // ★보스는 enemies 다음에 돈다. 이유가 두 개다.
    //   1) 스윙 번호(hot/swing)를 enemy.js 가 이번 프레임에 갱신한 뒤 받아야 한다.
    //      보스가 임계값을 다시 정의하면 잡몹과 판정 구간이 갈라진다.
    //   2) 플레이어가 죽는 프레임을 보스가 봐야 증표를 **그 자리에** 떨어뜨린다.
    boss.update(dt, {
      a: bladeLive ? hitA : null,
      b: bladeLive ? hitB : null,
      hot: enemies.hot,
      swing: enemies.swing,
      heavy,
      paused: preview.on,
    });
    // ── 아이템 드랍 (20차) ──
    // ★요괴·보스 **뒤에** 돈다. 이번 프레임에 벤 놈이 떨어뜨린 물건이 같은 프레임에
    //   첫 위치를 잡아야 한 프레임 늦게 나타나지 않는다.
    // ★dt 는 게임시간이다(히트스톱·슬로모가 이미 곱해져 있다). 세상이 멎는 그 105ms
    //   동안 물건만 혼자 튀어오르면 처치의 정지가 통째로 무너진다.
    // ── 화살 (21차) ──
    // ★요괴·보스 **뒤**, 아이템 **앞**이다. 뒤인 이유는 이번 프레임에 움직인 요괴
    //   자리로 판정해야 하기 때문이고, 앞인 이유는 화살이 벤 놈이 떨어뜨린 물건이
    //   같은 프레임에 첫 위치를 잡아야 하기 때문이다(items.js 머리말과 같은 규칙).
    // ★dt 는 게임시간이다. 세상이 멎는 70~112ms 동안 화살만 혼자 날아가면 안 된다.
    if (arrows) {
      // 발사 프레임. 클립 시각이 아니라 **경과 시간**으로 잰다 - 클립 시각은
      // 크로스페이드·캔슬로 튀는데 경과는 안 튄다(ARCHER_RELEASE_T 주석이 정본).
      if (!arrowShot && attacking && atkClip === 'Attack' && isArcher() &&
          !preview.on && !cleared && (now - atkStartT) >= ARCHER_RELEASE_T) {
        arrowShot = true;
        fireArrow();
        // ★★여기가 0.864초 완전 경직을 푸는 자리다.
        //   atkStruck 은 여태 「attacking && enemies.hot」 한 곳에서만 켜졌는데(아래),
        //   그 hot 은 **칼끝 속도** 게이트라 활에는 영영 안 켜진다. 그래서 궁수는
        //   canCancelAttack 의 첫 관문(!atkStruck)을 못 지나 이동·점프·연타가 전부
        //   클립이 끝날 때까지 잠겼다. 활에서 「한 번 휘둘렀다」에 해당하는 사건은
        //   **화살이 시위를 떠난 것**이고, 그 자리가 정확히 여기다.
        atkStruck = true;
      }
      arrows.update(dt, preview.on || cleared);
    }
    // ★남의 화살도 **게임시계**로 난다(로컬과 같은 규칙). arrows 가 꺼져 있어도
    //   이 줄은 돌아야 한다 - 남의 화살 시스템은 따로 서 있기 때문이다.
    if (mpFx) mpFx.updateArrows(dt, preview.on || cleared);
    if (items) items.update(dt, preview.on || cleared);

    // ── 휘두름 소리 ──
    // ★스윙 번호가 올라가는 그 프레임에 낸다. 키를 누른 순간이 아니다.
    //   3연타 클립 하나에 스윙이 셋이라 키 입력에 맞추면 소리가 한 번만 나고,
    //   무엇보다 **칼이 실제로 빨라지는 순간**과 어긋나서 따로 논다.
    //   공격 클립이 없는 캐릭터(기본·기본2)는 attacking 자체가 안 켜져서 여기 안 온다.
    if (enemies.swing !== lastSwingHeard) {
      lastSwingHeard = enemies.swing;
      if (!heavy) sfx.swing(0.9 + Math.random() * 0.25);
    }
  }

  // 카메라
  // ★★17차에 여기서 방향이 뒤집혔다. 옛 설계는 "세계는 멈춰도 카메라는 안 멈춘다"
  //   였다(feel.js 머리말). 그런데 실측해 보니 그 흔들림이 **히트스톱을 통째로 지우고
  //   있었다**: 멈춘 프레임의 화소 차분이 안 멈춘 프레임의 295%, 배경 띠 0.86 -> 7.9.
  //   세계가 멎어도 그림이 매 프레임 3~6px 씩 밀리면 사람은 멈춤을 못 본다.
  //   그래서 히트스톱 동안에는 **카메라도 같이 선다**(보간·흔들림 둘 다).
  //   대신 멈추기 직전 프레임에 베기 방향으로 한 번 민 펀치가 그 자리에 붙들려 있어서,
  //   "쳤다(1프레임 변위) -> 섰다(60~110ms 정지) -> 앉는다" 세 박자가 된다.
  //   ★사망·전멸 슬로모는 hitFrozen 이 아니므로 예전 그대로 흔들리며 흐른다.
  //   ★흔들림 타이머(shakeT)는 계속 실제 dt 로 늙힌다. 멈춘 동안 안 늙히면 정지가
  //     끝난 뒤 흔들림만 뒤늦게 남아서 "다 끝나고 카메라가 떤다"가 된다.
  //     화면에 나가는 오프셋만 placeCamera 안에서 붙들어 둔다(shakeOffsetFrozen).
  feel.updateShake(rawDt);
  updateCamPunch(rawDt, hitFrozen);
  // ★가림 완화는 히트스톱 중에는 안 돈다(멈춘 프레임에서 각이 움직이면 정지가 깨진다).
  if (!hitFrozen) updateCamLift(rawDt);
  placeCamera(rawDt * 12, hitFrozen);
  // 화면 겹(붓질 슬래시·속도선)도 실제 dt. 카메라와 같은 시계를 쓴다.
  feel.updateOverlay(rawDt);

  // #combo 판의 수명·등장 팝. ★18차에 두 스위치(COMBO_UI_ON·SKILL_CALLOUT_ON)가 모두
  //   꺼지면서 comboT 를 0 위로 올리는 자리가 하나도 안 남았다 - 그래서 지금은 매 프레임
  //   else 가지로만 흐르고(불투명도 0 고정) 판은 영영 안 보인다. **그래도 안 지운다**:
  //   ①스위치 둘 중 아무거나 되돌리면 이 줄이 그대로 다시 필요하다 ②comboEl 은 index.html
  //   의 실제 div 라 null 이 아니고, 하는 일은 프레임당 style 쓰기 한 번뿐이다(비용 0에 가깝다).
  if (comboT > 0) {
    comboT -= dt;
    comboEl.style.opacity = Math.max(0, Math.min(1, comboT * 1.6));
    comboEl.style.transform = 'translateX(-50%) scale(' + (1 + (0.9 - comboT) * 0.12) + ')';
  } else comboEl.style.opacity = 0;

  // ── 방향 비네트 · 대시 칩 (9차) ──
  // ★비네트는 **실제 dt(rawDt)** 로 늙는다. 히트스톱으로 세계가 멈춘 동안에도
  //   화면은 계속 흘러야 "멈춘 것"이 아니라 "맞은 것"으로 읽힌다(feel.updateShake 와 같은 규칙).
  if (hurtDirT > 0) {
    hurtDirT -= rawDt;
    if (hurtDirT <= 0) hurtDirEl.classList.remove('on');
  }
  // ★회피가 잠긴 동안에는 dashChip 이 null 이다(점프 칸에는 칠할 쿨이 없다).
  if (DASH_ON && dashChip) {
    const ready = dashReady(now);
    // 대시 중에도 "불가"로 보여야 한다(쿨이 이미 돌기 시작했다)
    dashChip.classList.toggle('rdy', ready);
    dashChip.classList.toggle('off', !ready);
    const g = dashChip.firstElementChild;
    if (g) {
      // ★ui.js 스킬 칩과 **같은 표기**(12시부터 시계방향으로 걷히는 라디얼).
      //   준비되면 문자열을 지운다(칩이 밝아지면 어차피 안 보이므로 매 프레임 안 쓴다).
      if (ready) { if (g.style.background) g.style.background = ''; }
      else {
        const turn = Math.max(0, Math.min(1, (dashReadyT - now) / DASH_CD)).toFixed(3);
        g.style.background = 'conic-gradient(from 0deg,rgba(4,4,3,.80) 0turn ' + turn
          + 'turn,rgba(4,4,3,0) ' + turn + 'turn)';
      }
    }
  }

  updateCpLive();     // 클립 패널: 재생 시각·강조 갱신(값이 바뀔 때만 DOM 을 쓴다)

  // ── 검증 기록 ──
  // 히트스톱이 실제로 몇 ms 걸렸는지, 그 사이 콤보 창이 살아 있었는지를 **숫자로**
  // 남긴다. 눈으로 "멈춘 것 같다"는 증거가 아니다. __rec() 로 켜고 __recDump() 로 뽑는다.
  if (__rec) {
    __rec.push([+(performance.now()).toFixed(1), +(rawDt * 1000).toFixed(2),
                +(dt * 1000).toFixed(2), attacking ? 1 : 0, comboStep,
                (current && current === actions.Attack) ? +current.time.toFixed(3) : -1,
                enemies.swing, enemies.kills,
                +(now - comboWindow).toFixed(3)]);
    if (__rec.length > 1800) __rec.shift();
  }

  // 남의 아바타 보간·재생 + 내 상태 송신(15Hz). rawDt 인 이유는 위 주석과 같다.
  if (multi) multi.update(rawDt);

  composer.render();
}
tick();
