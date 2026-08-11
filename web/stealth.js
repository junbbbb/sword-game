// ---------------------------------------------------------------------------
// web/stealth.js — 수풀 은신 (리그 오브 레전드 규칙 + 소리 + 연출)
//
// docs/game-design.md "시야와 은신(부쉬)" 을 그대로 옮긴 것이다.
//   · 수풀 안에 있으면 밖에서 안 보인다
//   · 수풀 안에서는 밖이 보인다
//   · 같은 수풀 안에 들어오면 서로 보인다
//   · 공격하면 잠깐 드러난다
// 여기에 소리를 얹는다. 달리기·전투는 시끄러워 위치가 새고 걷기는 조용하다.
// = **수풀에 숨어도 달리면 들킨다.**
//
// 왜 별도 모듈인가
//   main.js 2,600줄 / enemy.js 2,100줄이다. 은신은 "플레이어 상태"도 아니고
//   "요괴 상태"도 아니라 **둘 사이의 규칙**이라 어느 쪽에 넣어도 남의 파일이 된다.
//   여기 한 군데에 규칙과 눈에 보이는 신호를 같이 둔다.
//
// ===========================================================================
// ★2026-08-10 연출 대개편 — v72 QA 가 지적한 여섯 가지
// ===========================================================================
// QA 실증(renders/history/v72_qa/cmp_3_inside_lowangle, st_C0_hidden)에서
// "숨었다" HUD 가 떠 있는데도 화면은 **상추 더미 위에 서 있는 그림**이었다.
// 원인을 하나씩 갈라 보면 이랬고, 대응은 그 옆에 적었다.
//
//  1) 잎이 캐릭터 **앞에** 한 장도 안 그려진다
//     수풀 포기가 1.10~1.61m 라 키 1.75 의 무릎만 잠겼고, 쿼터뷰에서 카메라와
//     캐릭터 사이에 잎이 없었다. 수풀 안에 서 있는 게 아니라 위에 올라선 그림.
//     -> (가) props.js KIND_Y.bush 1.0 -> 1.35 (평균 1.84m. 콜라이더·판정 불변)
//        (나) **앞잎 카드**: 숨은 구역의 포기 자리마다 카메라를 보는 잎 판을 세운다.
//             불투명 패스에서 discard 만 하는 알파컷이라 깊이를 쓰고, 그래서
//             몸도 궤적 이펙트도 정상적으로 가린다(아래 ★렌더 순서).
//
//  2) 반투명 0.34 가 밝은 배경에서 오히려 더 눈에 띈다
//     ★실은 그 반투명이 **한 번도 적용된 적이 없다.** three 는 material.transparent 를
//       바꿀 때 needsUpdate 를 안 올리면 프로그램을 다시 안 만든다. 옛 프로그램에는
//       #define OPAQUE 가 살아 있고 그 안에서 diffuseColor.a = 1.0 으로 덮어쓴다.
//       = opacity 를 아무리 내려도 알파가 1 로 되돌아간다(수풀 0.32 도 같은 이유로
//         무효였다. QA 스샷의 수풀이 통째로 불투명한 게 그 증거다).
//     대응은 "고쳐서 반투명하게" 가 아니다. 반투명 자체를 버린다.
//     -> **먹 실루엣**: 채도를 죽이고 어둡게 물들이고 실루엣에 옅은 청록 림을 얹는다.
//        밝은 배경에서 반투명은 배경색과 섞여 더 튀지만, 어두운 실루엣은 어두워진
//        수풀 속(아래 3)에 녹는다. 알파를 안 건드리니 정렬 문제도 없다.
//     -> ★칼(SW_)·방패(SH_)·칼날 발광까지 같은 처리에 넣는다. 예전 코드는 이 셋을
//        빼놨고 그래서 "칼날만 하얗게 수풀 위로 삐져나왔다".
//
//  3) 수풀 속이 텅 비고 균일한 형광 연두 -> props.js 가 정점색으로 안쪽 그늘을 굽는다
//     (밑동이 어둡고 구역 안쪽이 어둡다. 이 파일이 아니라 props.js 쪽 주석 참고)
//     여기서는 **들어간 구역만** 한 단 더 어둡게 물들이고 살짝 비쳐 보이게 한다.
//
//  4) 바닥에 경계 표시가 없어 어디부터 은신인지 모른다 -> **경계 링**
//     level1.json 의 bushes[].rects 그대로, 구역 안쪽 바닥을 옅게 어둡게 깔고
//     경계 바로 바깥에 옅은 밝은 선을 한 줄 두른다. 항상 보이고(여기부터 부쉬다)
//     들어가면 조금 진해진다. 왜 '띠' 가 아니라 '판' 인지는 아래 ★경계 링 참고.
//
//  5) 나올 때 알파가 튀고 페이드 -> **연속 전환 곡선** 들어갈 때 0.25초 / 나올 때 0.35초.
//     지수 보간(FADE_SPEED)을 버리고 시간 기반 진행도 + smoothstep 으로 바꿨다.
//     지수 보간은 프레임 간격이 흔들리면 그만큼 튄다(그게 0.34 -> 0.60 점프의 정체다).
//
//  6) 소리가 없다 -> 출입 순간 **잎 스침**(sfx.rustle). 연출용이라 소리 반경과 무관하다.
//
// ★렌더 순서 함정 (여기 손대면 궤적 이펙트가 깨진다)
//   앞잎은 transparent:false + discard 로 **불투명 패스**에서 깊이를 쓴다. 그래서
//   그 뒤에 그려지는 반투명 궤적(main.js trail renderOrder 3, depthTest 켬)이
//   잎에 정상적으로 가려진다. 앞잎을 transparent:true 로 바꾸면 renderOrder 가 낮아
//   궤적이 잎 위로 올라온다. 초승달(renderOrder 12, depthTest 끔)만은 원래대로
//   전부 위에 그려진다 - 그건 화면에 찍는 임팩트 프레임이라 맞는 동작이다.
//
// ★판정은 이 개편에서 한 줄도 안 건드렸다. canSee(ex, ez, alerted) 의 시그니처와
//   내용은 전투 수정 에이전트가 고쳐 놓은 그대로다(alerted 분기 포함).
// ---------------------------------------------------------------------------
import * as THREE from './lib/three.module.js';
// ★main.js·enemy.js 와 같은 URL 로 부른다(캐시 버스팅 쿼리). 다르면 맵 인스턴스가 갈린다.
const LV = await import('./level.js' + location.search);
// 이 파일이 내는 **정보성** 로그는 전부 이 게이트를 지난다(경고·에러는 항상 낸다).
// 평시 콘솔이 비어 있어야 "콘솔 에러 0" 스모크가 뜻을 갖는다(건틀릿 연출UI S10).
const DEV = typeof location !== 'undefined' && location.search.includes('dev');

// ── 소리 반경 ──
// 수풀 한 칸이 3.2m 다. 이 숫자들은 전부 "한 칸" 을 기준으로 잡았다.
const NOISE_IDLE = 0.0;    // 가만히 있으면 아무 소리도 안 난다. 완전 은신
// 걷기 2.2m: 한 칸(3.2m)보다 짧다. 같은 수풀 가장자리에 붙어 선 요괴만 듣는다.
// = 걸어서 이동하는 동안에도 은신이 유지된다(이게 성립해야 잠입이 선택지가 된다).
const NOISE_WALK = 2.2;
// 달리기 9.0m: 무리 어그로(enemy.js AGGRO_RADIUS 7.0)보다 넓다. 즉 **어그로 범위 안에
// 있는 요괴는 예외 없이 듣는다.** "수풀에 숨어도 달리면 들킨다"를 숫자로 보장하는 값이다.
const NOISE_RUN = 9.0;
// 공격하면 아예 드러난다(LoL 규칙). 잔여 시간 동안은 수풀이 없는 것처럼 취급한다.
// 1.1초: 검사 Attack 클립이 1.6초, 실제 베는 구간이 0.9초쯤이다. 한 번 베고
// 빠지면 곧 다시 숨을 수 있고, 계속 베면 계속 드러난다.
const REVEAL_ATTACK = 1.1;

// ── 전환 시간(초) ──
// 비대칭이다. 잠기는 건 빠르고 풀리는 건 느리다. 빨리 잠겨야 "숨었다"가 조작에
// 붙어 오고, 천천히 풀려야 나오는 그림이 잘리지 않는다.
const FADE_IN = 0.25;
const FADE_OUT = 0.35;

// ── 들어간 수풀 ──
// 0.32 까지 내리면 수풀이 사라져서 오히려 캐릭터가 도드라진다(그리고 그 값은
// 위 ★2 의 이유로 애초에 안 먹고 있었다).
// ★0.72 로 재 봤더니 이번엔 반대로 **밝아졌다.** 밝은 흙바닥이 잎 사이로 비쳐
//   섞이기 때문이다. 잎 덩어리는 어두워야 그 안에 든 실루엣이 녹는다.
//   그래서 거의 불투명하게 두고 어둡게 물들이는 쪽으로 간다.
const BUSH_IN_ALPHA = 0.90;
const BUSH_IN_TINT = 0.40;   // 0=그대로, 1=새까맣게

// ── 먹 실루엣 ──
// 최종 밝기 = INK_COL x (INK_LO + INK_HI x 원래밝기^0.55). 전부 선형 공간이다.
//
// ★★9차 전면 재조정 (건틀릿 1회차 캐릭터 부문 **1순위 격차**)
//   심사관: "수풀 뒤에서 3~4초짜리 클립을 돌려도 플레이어를 못 찾겠다."
//   고치기 전에 숫자부터 냈다(headed, BUSH_13 한가운데, 200x240 크롭,
//   플레이어 메시를 껐다 켠 두 장의 차이로 **정확한 마스크**를 떠서 잰 값):
//       플레이어 픽셀 평균 명도 74.2  /  바로 뒤 배경(잎) 77.2   -> 차이 **3.0 / 255**
//   즉 몸이 잎과 **같은 밝기**였다. 이건 은신이 아니라 삭제다.
//
//   옛 주석은 "잎 덩어리는 어두워야 그 안에 든 실루엣이 녹는다"고 적혀 있었다.
//   그때의 목표(녹아든다)가 지금은 격차의 원인이다. 목표를 뒤집는다.
//   **은신 중에도 내가 어디 있는지는 항상 읽혀야 한다.** 숨는 건 요괴의 판정이
//   해 주지(canSee), 플레이어 화면까지 나를 지울 이유가 없다.
//
//   그래서 feel.js 가 이미 실측으로 찾아 둔 조합을 그대로 가져온다.
//     · 안쪽은 **짙은 먹**(값 대비로 형태를 만든다)
//     · 테두리는 **종이색**(잎빛 테두리는 초록에 그대로 녹는다는 게 v88 실측이다)
//   INK_LO/HI 를 3분의 1로 눌러 몸을 어둡게 깔고, 림 색을 청록 -> 종이색으로 바꾼다.
//   ★값은 눈이 아니라 스윕으로 골랐다(BUSH_16, 한 페이지 안에서 tune() 으로 5조합.
//     배경이 고정돼 있어야 비교가 정직하다. renders/history/v94_wave9/enemy/ink_sweep.json)
//       옛값(.075/.45)      몸 72.7 vs 잎 66.9   ΔL  +5.9   웨버 0.081  <- 잎보다 밝다
//       .022/.150           몸 54.5 vs 잎 67.3   ΔL -12.8   웨버 0.190
//       .014/.085           몸 51.6 vs 잎 67.0   ΔL -15.4   웨버 0.230
//       .010/.055           몸 50.7 vs 잎 66.7   ΔL -16.0   웨버 0.240  <- 골랐다
//       .006/.032           몸 53.1 vs 잎 67.0   ΔL -14.0   웨버 0.208  <- 더 내리면 되레 나빠진다
//     마지막 줄이 중요하다. 몸을 더 눌러도 안 좋아지는 이유는 그 지점부터는
//     **feel.js 의 가림 실루엣 껍데기**(SIL_COLOR 0x0b0910 · 알파 0.80 · 종이색 림)가
//     화면을 차지하기 때문이다. 그 위는 이 파일의 손이 안 닿는다 -> handoff_enemy.md.
const INK_COL = 0x4e6f66;    // 물들이는 색(먹빛 청올리브. 값이 낮아 색조는 거들기만 한다)
const INK_LO = 0.010;        // 제일 어두운 데 (0.075 에서 내림)
const INK_HI = 0.055;        // 밝은 데까지의 폭 (0.45 에서 내림). 칼날 흰색도 여기 눌린다
// ★림 색을 청록(0x7fe0cf) -> **종이색**으로 바꿨다. v88 이 상시 실루엣에서 이미
//   같은 결론을 냈다: "테두리를 잎빛으로 두면 잎에 그대로 녹는다. 종이색이라야
//   초록 위에서 윤곽이 잡힌다. 이 한 줄이 보인다/안 보인다를 갈랐다."
const RIM_COL = 0xd9cdb4;    // 실루엣 가장자리 종이색
const RIM_K = 0.38;          // ★블룸 임계값 1.02 보다 한참 아래여야 한다(안 번지게)
// ★림 지수. 낮추면(2.2) 곡면 전체가 떠서 조각상이 된다. 실루엣 가장자리에만
//   남으려면 3 이상이어야 한다(실측 1회). 몸이 어두워진 만큼 3.4 -> 3.0 으로만 넓힌다.
const RIM_POW = 3.0;

// ── 앞잎 카드 ──
const FOL_MAX = 40;          // 한 프레임에 세우는 카드 상한(포기 16 x 2줄 + 여유)
const FOL_R = 2.7;           // 이 반경(m) 안의 포기에만 세운다
const FOL_Y = 1.30;          // 카드 중심 높이(m). 키 1.75 의 가슴~머리 띠를 덮는다
// ★잎 크기는 카드 크기가 정한다(텍스처 한 장에 잎 46 장이 들어 있다).
//   0.86/0.80 으로 재 봤더니 잎 하나가 0.35m 라 수풀 본체의 잔잎보다 커서
//   **다른 식물**로 읽혔다. 0.68/0.62 면 잎 하나가 0.27m 로 앞뒤가 맞는다.
const FOL_HW = 0.62;         // 반폭(m). 포기 scale 을 곱한다
const FOL_HH = 0.56;         // 반높이(m)
// ── 빈틈 메우기 ──
// ★포기 자리만 앵커로 쓰면 **플레이어가 선 자리**가 비는 수가 있다. 수풀 포기는
//   덩어리로 심겨 있고 사람은 그 사이 빈 곳에 서기 때문이다(v72 QA 스샷이 정확히
//   그 상황이다). 그래서 구역 전체에 흔들린 격자를 깔아 놓고 플레이어 주변의
//   격자점에도 카드를 세운다. **월드 고정 좌표**라 걸어도 카드가 안 따라온다
//   (플레이어에 붙이면 카메라에 붙은 스티커로 보인다).
const FILL_STEP = 0.95;      // 격자 간격(m)
const FILL_R = 1.65;         // 이 반경 안의 격자점만
const FILL_MIN = 0.42;       // 몸에 너무 붙은 점은 뺀다(통째로 가려지면 내가 안 보인다)
// 한 포기에 카드를 두 장 겹친다(아래·위). 카드를 작게 줄인 만큼 덮는 넓이를
// 되찾는다. 두 장의 높이·좌우 흔들림이 달라 한 장짜리보다 훨씬 덜 규칙적이다.
const FOL_ROWS = [
  { dy: -0.30, dx: -0.16, cut: 0.02, sc: 1.00 },
  { dy: 0.32, dx: 0.18, cut: 0.06, sc: 0.88 },
];
// ★카드를 앵커보다 이만큼(m) 카메라 쪽으로 당긴다. 이 값이 0 이면 카드가
//   **자기 포기 속에 파묻혀** 한 장도 안 보인다(첫 시도의 증상이 정확히 이거였다).
//   포기 반지름이 1m 쯤이라 그보다 조금 더 당겨야 껍질 밖으로 나온다.
//   ★균일하게 당기므로 앞뒤 순서는 그대로 보존된다. 플레이어보다 1.15m 넘게
//     뒤에 있던 포기는 여전히 뒤에 남는다(= 등 뒤 잎이 얼굴을 가리지 않는다).
const FOL_AHEAD = 1.15;
const CUT_OPEN = 0.50;       // 알파컷 하한 = 잎이 다 나온 상태 (텍스처 순번 하한과 같다)
const CUT_SHUT = 1.04;       // 알파컷 상한 = 한 장도 안 나온 상태
// ★반경 끝에서 컷이 1.0 을 넘어야 한다. 안 넘으면 잎이 다 자란 채로 목록에서
//   빠져서 걸어 나올 때 **한 프레임에 툭 사라진다**. 0.55 면 q=1 에서 1.05 가 된다.
//   q 를 제곱해서 쓰므로 가까운 카드는 거의 안 깎인다.
const FOL_FAR_BIAS = 0.55;
// ★몸을 덮는 잎은 반대로 **갈라 놓는다.** 안 그러면 캐릭터가 통째로 사라져서
//   내가 어디 있는지 모른다(실측: 측면 앵글에서 완전 실종).
//   ★월드 거리로 골라내면 안 된다. 몸을 덮는 카드는 "가까운 카드"가 아니라
//     "카메라와 몸 사이에 있고 화면에서 몸과 겹치는 카드"다. 옆에서 보면 2.5m
//     떨어진 포기가 몸을 덮는다(월드 반경 1.3m 로는 하나도 안 걸렸다).
//     그래서 판정을 **정점 셰이더의 화면 좌표**로 옮겼다(uHole/uPly).
// ★0.42 -> 0.55 (9차. 건틀릿 캐릭터 1순위 "수풀에서 플레이어를 못 찾는다").
//   먹을 아무리 진하게 해도 **잎이 몸을 덮고 있으면** 소용이 없다. 컷 하한이
//   CUT_OPEN 0.50 이고 상한이 CUT_SHUT 1.04 라, 0.55 면 몸 한복판(구멍 중심)에서
//   1.05 = 잎이 한 장도 안 나온다. 즉 가슴께에 잎이 확실히 갈라진다.
//   0.62 이상은 안 쓴다 - 갈라진 자리가 "수풀에 뚫린 구멍"으로 읽히기 시작한다.
const HOLE_K = 0.55;         // 몸과 겹치는 자리에서 더해지는 컷
const HOLE_R0 = 0.035;       // 구멍 안쪽 반지름(NDC)
const HOLE_R1 = 0.205;       // 구멍이 스러지는 반지름(NDC). 캐릭터 키가 0.14 쯤이다
const HOLE_Y = 1.00;         // 기준점 높이(m). 가슴께
const FOL_TINT = 0x8fa07f;   // 카드 색조(어둡고 차분하게. 흰색이면 텍스처 그대로)
const FOL_TEX = './tex/bush_leaf.png';

// ── ★경계 링 ──
// "은은하게" 가 요구다. 처음엔 밝은 선을 0.26 으로 뒀는데 밝은 흙 위에서
// 흰 사각형 UI 처럼 읽혔다. 안쪽 그늘을 주인공으로 두고 밝은 선은 흔적만 남긴다.
// 두 번 갈아엎고 나온 형태다. 경계에 띠만 두르는 방식은 **안 보인다.**
//   잎이 판정 사각형 밖으로 0.3~1.65m 삐져나와 있어서(실측) 경계선이 통째로
//   잎 밑에 깔린다. 그래서 띠가 아니라 **바닥 판**으로 간다.
//     · 구역 안쪽 바닥 전체를 옅게 어둡게 깐다 -> 포기 사이 빈 곳으로 훤히 보인다
//       (= "여기 바닥은 수풀 그늘이다". 안쪽 어둠도 같이 거든다)
//     · 경계 바로 바깥에 아주 옅은 밝은 선 한 줄 -> 잎이 덜 나온 쪽에서 테두리가 선다
//   판정 사각형에 정확히 맞춰 그린다. 잎이 더 넓은 건 사실이지만, 실제로 숨는
//   자리는 이 사각형이라 **거짓말을 안 하는 쪽**이 맞다.
const RING_OUT = 0.40;       // 경계 바깥으로 번지는 폭(m)
const RING_EDGE = 0.09;      // 밝은 선이 앉는 자리(경계에서 바깥으로, m)
const RING_LIFT = 0.030;     // 바닥에서 띄우는 높이. 0 이면 z-파이팅한다
const RING_DARK = 0x1d2a1a;  // 구역 안쪽 바닥 그늘색
const RING_LITE = 0xcdd79c;  // 경계 밝은 선. 흰색에 가까우면 UI 사각형처럼 읽힌다
const RING_A_IN = 0.24;      // 안쪽 바닥 알파
const RING_A_EDGE = 0.15;    // 밝은 선 알파
const RING_HOT = 0.55;       // 들어간 구역은 이만큼 더 진해진다

// ---------------------------------------------------------------------------
// 수풀 자료
// ---------------------------------------------------------------------------
// level1.json 의 bushes[] = { id, cells[], rects[{x,z,hx,hz}] }. 이미 three.js 좌표다.
const BUSH = [];           // { id, rects, mesh, mat, origOpacity, oc, spots, t, tp }
let built = false;
let scene = null;          // 링·앞잎을 붙일 곳(맵 root 가 아니라 씬. 아래 ★좌표계)

export function build() {
  BUSH.length = 0;
  const d = LV.data();
  if (!d || !d.bushes) { console.warn('[stealth] level1.json 에 bushes[] 가 없다'); return false; }
  // 메시 이름(BUSH_01..)이 bushes[].id 와 같아서 그대로 짝지을 수 있다.
  const meshes = {};
  const root = LV.root();
  if (root) root.traverse(o => { if (o.isMesh && o.name.startsWith('BUSH')) meshes[o.name] = o; });
  // ★링·앞잎은 **씬**에 붙인다. 좌표를 level1.json 에서 그대로 읽어 쓰는데
  //   맵 root 에 변환이 걸려 있으면 그 좌표가 한 번 더 돌아간다. 씬에 붙이면
  //   json 좌표 = 월드 좌표가 보장된다(빌보드 계산도 뷰공간이라 배율에 안전하다).
  scene = (root && root.parent) || root;

  // 포기 자리(앞잎 카드의 앵커). 없어도 그냥 돈다 - 카드만 안 선다.
  const spotsById = {};
  for (const p of (d.props || [])) {
    if (p.kind !== 'bush' || !p.bush) continue;
    (spotsById[p.bush] = spotsById[p.bush] || []).push(p);
  }

  for (const b of d.bushes) {
    const m = meshes[b.id] || null;
    let mat = null;
    if (m) {
      // ★재질을 복제해서 쓴다. 16개가 한 재질을 공유하고 있으면 하나를 옅게 만드는
      //   순간 맵의 수풀이 전부 같이 옅어진다(실제로 공유다. props.js 가 종류당 하나).
      mat = m.material.clone();
      m.material = mat;
    }
    const spots = (spotsById[b.id] || []).map(p => {
      const a = Math.random() * Math.PI * 2;
      return {
        x: p.x, z: p.z,
        y: LV.groundY(p.x, p.z) + FOL_Y,
        ux: Math.cos(a), uz: Math.sin(a),                              // 줄별 좌우 밀기 방향
        hw: FOL_HW * (p.scale || 1) * (Math.random() < 0.5 ? -1 : 1),  // 부호 = 좌우 뒤집기
        hh: FOL_HH * (p.scale || 1),
        rot: (Math.random() - 0.5) * 0.44,
      };
    });
    BUSH.push({
      id: b.id, rects: b.rects || [], mesh: m, mat,
      origOpacity: mat ? mat.opacity : 1,
      oc: mat ? mat.color.clone() : null,
      spots, fill: fillGrid(b.rects || []), t: 0, tp: -1,
    });
  }
  buildRing(d);
  buildFoliage();
  const fills = BUSH.reduce((a, b) => a + b.fill.length, 0);
  built = true;
  if (DEV) {
    if (fills) console.log('[stealth] 빈틈 메우기 격자 ' + fills + '점');
    console.log('[stealth] 수풀 ' + BUSH.length + '곳, 메시 연결 '
      + BUSH.filter(b => b.mesh).length + '개, 앞잎 앵커 '
      + BUSH.reduce((a, b) => a + b.spots.length, 0) + '개');
  }
  return true;
}

// 구역을 흔들린 격자로 채운 앵커 목록. 자리는 로드 때 한 번 정하고 안 바뀐다.
function fillGrid(rects) {
  const out = [];
  for (const r of rects) {
    const nx = Math.max(1, Math.round(2 * r.hx / FILL_STEP));
    const nz = Math.max(1, Math.round(2 * r.hz / FILL_STEP));
    for (let i = 0; i < nx; i++) {
      for (let j = 0; j < nz; j++) {
        const gx = r.x - r.hx + (i + 0.5) * (2 * r.hx / nx)
          + (Math.random() - 0.5) * FILL_STEP * 0.6;
        const gz = r.z - r.hz + (j + 0.5) * (2 * r.hz / nz)
          + (Math.random() - 0.5) * FILL_STEP * 0.6;
        out.push({
          x: gx, z: gz, y: LV.groundY(gx, gz) + FOL_Y,
          hw: FOL_HW * (0.86 + Math.random() * 0.28) * (Math.random() < 0.5 ? -1 : 1),
          hh: FOL_HH * (0.86 + Math.random() * 0.28),
          rot: (Math.random() - 0.5) * 0.5,
        });
      }
    }
  }
  return out;
}

// 점이 어느 수풀에 들었는가. 없으면 -1.
// 16곳 x 사각형 2개 = 32번 검사라 매 프레임 돌려도 공짜다.
export function bushAt(x, z) {
  for (let i = 0; i < BUSH.length; i++) {
    const rs = BUSH[i].rects;
    for (let k = 0; k < rs.length; k++) {
      const r = rs[k];
      if (Math.abs(x - r.x) <= r.hx && Math.abs(z - r.z) <= r.hz) return i;
    }
  }
  return -1;
}
// 이 점이 **특정 수풀** 안인가. canSee 가 요괴마다 부르므로 전체를 안 돈다.
function inBush(i, x, z) {
  if (i < 0 || i >= BUSH.length) return false;
  const rs = BUSH[i].rects;
  for (let k = 0; k < rs.length; k++) {
    const r = rs[k];
    if (Math.abs(x - r.x) <= r.hx && Math.abs(z - r.z) <= r.hz) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// 상태
// ---------------------------------------------------------------------------
let px = 0, pz = 0;
let myBush = -1;           // 플레이어가 든 수풀 index
let lastBush = -1;         // 마지막으로 들었던 수풀(나오는 중에 앞잎이 남아야 한다)
let prevBush = -2;         // 소리용. -2 = 아직 한 번도 안 돌았다
let revealT = 0;           // 공격 노출 잔여 시간
let noiseR = 0;            // 지금 내는 소리가 들리는 반경
let hiddenNow = false;     // 최종 판정: 지금 숨어 있는가
let quiet = false;         // 숨어 있고 소리도 안 새는가(HUD 색이 갈린다)
let enabled = true;

export function setEnabled(v) { enabled = !!v; }        // 검증용 스위치
export function hidden() { return hiddenNow; }
export function noiseRadius() { return noiseR; }
export function playerBush() { return myBush; }

// ★요괴가 부르는 창구. "이 자리에서 플레이어가 보이는가".
//   보인다 = 어그로를 걸어도 된다. 안 보인다 = 없는 사람 취급한다.
//
// alerted = 이미 나를 쫓고 있는(또는 방금 놓치고 찾는 중인) 놈인가.
// ★v72 QA #2 의 원인이 이 구분이 없던 것이다. "같은 수풀 안이면 서로 보인다"는
//   LoL 규칙을 **쫓아 들어온 놈에게도** 그대로 줬더니, 추격 넷이 나를 따라 수풀에
//   들어오는 순간 전원이 계속 보게 됐다. 그래서 "숨었다" HUD 를 띄운 채로 11초를
//   맞고 죽었다 = 수풀이 장식이 됐다.
//   붙어서 쫓던 놈은 잎에 가려 놓치는 게 맞다(그래서 도망 수단이 성립한다). 대신
//   **소리와 공격 노출은 그대로 듣는다.** 숨어서 달리거나 베면 즉시 다시 들킨다
//   = 수풀은 무적이 아니라 "숨을 죽이는 동안만" 듣는 장치가 된다.
export function canSee(ex, ez, alerted) {
  if (!enabled || !built) return true;
  if (myBush < 0) return true;              // 수풀 밖이면 그냥 보인다
  if (revealT > 0) return true;             // 공격 직후는 드러난다
  // 같은 수풀 안이면 서로 보인다 — 단 **아직 나를 못 찾은 놈에게만** 준다.
  // (걸어 들어간 수풀에 요괴가 앉아 있었으면 그놈은 나를 본다. 이건 그대로다)
  if (!alerted && inBush(myBush, ex, ez)) return true;
  // 여기부터는 **눈으로는 못 본다.** 남은 건 소리뿐이다.
  if (noiseR <= 0) return false;
  const dx = ex - px, dz = ez - pz;
  return dx * dx + dz * dz < noiseR * noiseR;
}

// ---------------------------------------------------------------------------
// 갱신 (main.js 가 요괴보다 **먼저** 부른다)
// ---------------------------------------------------------------------------
export function update(dt, s) {
  if (!built) return;
  px = s.x; pz = s.z;
  myBush = enabled ? bushAt(px, pz) : -1;
  if (s.attacking) revealT = REVEAL_ATTACK;
  else if (revealT > 0) revealT -= dt;
  noiseR = s.running ? NOISE_RUN : (s.moving ? NOISE_WALK : NOISE_IDLE);
  hiddenNow = myBush >= 0 && revealT <= 0;
  // 숨긴 숨었는데 소리가 새면 반쪽이다. 소리 반경이 어그로(7.0)에 닿는 순간부터
  // "들킨다"로 본다 - 걷기 2.2 는 조용, 달리기 9.0 은 샌다.
  quiet = hiddenNow && noiseR < 7.0;
  if (myBush >= 0) lastBush = myBush;
  rustleOnCross();
  paint(dt);
  hud();
}

// 잎 스침. 수풀 경계를 **넘는 프레임**에만 낸다.
// ★소리 반경(NOISE_*)과 아무 관계가 없다. 요괴는 이 소리를 못 듣는다. 연출이다.
function rustleOnCross() {
  if (prevBush === -2) { prevBush = myBush; return; }   // 첫 프레임은 넘어간다
  if (myBush === prevBush) return;
  const enter = myBush >= 0;
  prevBush = myBush;
  const sfx = window.__sfx;
  if (sfx && sfx.rustle) sfx.rustle(enter ? 1.0 : 0.82);
}

// 0..1 진행도를 부드러운 곡선으로. 양 끝의 기울기가 0 이라 시작·끝이 안 튄다.
function ease(t) { return t * t * (3 - 2 * t); }

// ---------------------------------------------------------------------------
// 눈에 보이는 신호 (1) 수풀 (2) 앞잎 (3) 경계 링 (4) 플레이어 몸 (5) HUD
// ---------------------------------------------------------------------------
function paint(dt) {
  const kin = dt / FADE_IN, kout = dt / FADE_OUT;
  for (let i = 0; i < BUSH.length; i++) {
    const b = BUSH[i];
    const want = (i === myBush) ? 1 : 0;
    b.t = want ? Math.min(1, b.t + kin) : Math.max(0, b.t - kout);
    if (b.t === b.tp) continue;               // 값이 안 바뀌면 재질을 안 건드린다
    b.tp = b.t;
    const k = ease(b.t);
    if (b.mat) {
      const op = 1 - (1 - BUSH_IN_ALPHA) * k;
      const tr = op < 0.995;
      // ★transparent 를 바꿀 때는 needsUpdate 를 반드시 올린다. 안 올리면 three 가
      //   프로그램을 다시 안 만들고, 옛 프로그램의 #define OPAQUE 가 살아 있어
      //   diffuseColor.a = 1.0 으로 덮어써 버린다(= opacity 가 통째로 무효).
      //   이게 v72 QA 의 "수풀이 하나도 안 옅어진다" 의 정체다.
      if (b.mat.transparent !== tr) { b.mat.transparent = tr; b.mat.needsUpdate = true; }
      b.mat.opacity = op * b.origOpacity;
      // ★depthWrite 는 켠 채로 둔다. 잎 뭉치는 자기끼리 수백 번 겹치는데
      //   깊이를 안 쓰면 뒷잎이 앞잎 위에 얹혀 죽처럼 뭉갠다. 켜 두면 앞뒤가
      //   제대로 서고, 반투명 패스라 캐릭터 위에는 정상적으로 덮인다.
      const dk = 1 - BUSH_IN_TINT * k;
      if (b.oc) b.mat.color.setRGB(b.oc.r * dk, b.oc.g * dk, b.oc.b * dk);
    }
    ringLevel(i, 1 + RING_HOT * k);
  }
  foliage();
  inkPlayer(dt);
}

// ---------------------------------------------------------------------------
// (2) 앞잎 카드
// ---------------------------------------------------------------------------
// ★캐릭터와 카메라 사이에 잎을 세우는 게 이 개편의 알맹이다.
//   구역 메시를 복제해 렌더 순서를 뒤집는 방법도 있었지만 버렸다. 그 방법은
//   "캐릭터보다 뒤에 있는 잎"까지 앞으로 끌어올려서 몸이 통째로 사라지고,
//   깊이를 속이는 물건이라 궤적 이펙트와 순서 싸움이 난다.
//   여기서는 **실제로 카메라 쪽에 있는 포기 자리**에만 판을 세운다. 판은 뷰공간에서
//   앵커의 깊이를 그대로 쓰므로(화면 정렬 빌보드), 앞에 있는 잎만 앞을 가린다
//   = 깊이 테스트가 알아서 옳게 굴러간다. 속이는 데가 한 군데도 없다.
const FOL = { mesh: null, geo: null, mat: null, cen: null, size: null, cut: null, rot: null };

function buildFoliage() {
  if (FOL.mesh || !scene) return;
  const n = FOL_MAX;
  const pos = new Float32Array(n * 4 * 3);
  const uv = new Float32Array(n * 4 * 2);
  const idx = new Uint16Array(n * 6);
  // 네 귀퉁이의 부호. 실제 위치는 정점 셰이더가 뷰공간에서 만든다
  const C = [[-1, -1, 0, 0], [1, -1, 1, 0], [1, 1, 1, 1], [-1, 1, 0, 1]];
  for (let i = 0; i < n; i++) {
    for (let v = 0; v < 4; v++) {
      pos[(i * 4 + v) * 3] = C[v][0];
      pos[(i * 4 + v) * 3 + 1] = C[v][1];
      uv[(i * 4 + v) * 2] = C[v][2];
      uv[(i * 4 + v) * 2 + 1] = C[v][3];
    }
    const o = i * 4;
    idx.set([o, o + 1, o + 2, o, o + 2, o + 3], i * 6);
  }
  FOL.cen = new Float32Array(n * 4 * 3);
  FOL.size = new Float32Array(n * 4 * 2);
  FOL.cut = new Float32Array(n * 4);
  FOL.rot = new Float32Array(n * 4);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  g.setAttribute('aCen', new THREE.BufferAttribute(FOL.cen, 3).setUsage(THREE.DynamicDrawUsage));
  g.setAttribute('aSize', new THREE.BufferAttribute(FOL.size, 2).setUsage(THREE.DynamicDrawUsage));
  g.setAttribute('aCut', new THREE.BufferAttribute(FOL.cut, 1).setUsage(THREE.DynamicDrawUsage));
  g.setAttribute('aRot', new THREE.BufferAttribute(FOL.rot, 1).setUsage(THREE.DynamicDrawUsage));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.setDrawRange(0, 0);

  const mat = new THREE.ShaderMaterial({
    // ★불투명 패스에 남긴다. 아래 discard 로만 잎 모양을 낸다(위 ★렌더 순서 참고).
    transparent: false, depthTest: true, depthWrite: true,
    side: THREE.DoubleSide, fog: false,
    uniforms: {
      uTex: { value: null },
      uTint: { value: new THREE.Color(FOL_TINT) },
      uT: { value: 0 },
      uAhead: { value: FOL_AHEAD },
      uPly: { value: new THREE.Vector3() },
      uHole: { value: HOLE_K },
    },
    vertexShader: `
      uniform float uT; uniform float uAhead; uniform vec3 uPly; uniform float uHole;
      attribute vec3 aCen; attribute vec2 aSize; attribute float aCut; attribute float aRot;
      varying vec2 vUv; varying float vCut;
      void main(){
        vUv = uv;
        // 앵커를 뷰공간으로 옮기고 거기서 화면에 붙여 편다 = 카메라를 보는 판.
        // ★판 전체가 앵커 한 점의 깊이를 쓴다. 그래서 앞에 선 잎만 앞을 가린다.
        vec4 mv = modelViewMatrix * vec4(aCen, 1.0);
        vec4 mp = modelViewMatrix * vec4(uPly, 1.0);
        // 이 카드가 플레이어보다 앞인가(뷰공간 -z 가 앞이라 z 가 클수록 앞이다)
        float ahead = clamp((mv.z - mp.z) * 1.2 + 0.4, 0.0, 1.0);
        // ★뷰공간 -z 가 앞이다. z 를 키우면 카메라 쪽으로 나온다.
        //   이 한 줄이 없으면 카드가 자기 포기 속에 파묻혀 한 장도 안 보인다.
        mv.z += uAhead;
        // 화면에서 몸과 얼마나 겹치나. 겹칠수록 잎을 갈라 놓는다.
        // ★카드 중심 거리만 재면 안 된다. 카드 반높이가 0.13 NDC 나 돼서 중심이
        //   0.25 떨어져 있어도 몸을 덮는다. **자기 반지름을 빼고** 재야 맞다.
        vec4 cp = projectionMatrix * mv;
        vec4 pp = projectionMatrix * mp;
        float p11 = projectionMatrix[1][1];
        vec2 d = cp.xy / max(cp.w, 1e-4) - pp.xy / max(pp.w, 1e-4);
        d.x *= p11 / projectionMatrix[0][0];             // 세로 기준으로 맞춘다(화면비 보정)
        // ★변수 이름에 half 를 쓰면 안 된다. GLSL 예약어라 컴파일이 통째로 깨진다
        //   (node --check 는 통과하고 브라우저 셰이더 컴파일에서만 터진다).
        float hr = abs(aSize.y) * p11 / max(-mv.z, 1e-3);
        float rr = max(0.0, length(d) - hr * 0.80);
        vCut = aCut + uHole * ahead * (1.0 - smoothstep(${HOLE_R0.toFixed(3)}, ${HOLE_R1.toFixed(3)}, rr));
        float sw = sin(uT * 1.5 + aCen.x * 3.1 + aCen.z * 2.3);
        float a = aRot + sw * 0.035;
        float c = cos(a), s = sin(a);
        vec2 p = vec2(position.x * aSize.x, position.y * aSize.y);
        mv.xy += vec2(p.x * c - p.y * s, p.x * s + p.y * c) + vec2(sw * 0.02, 0.0);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      uniform sampler2D uTex; uniform vec3 uTint;
      varying vec2 vUv; varying float vCut;
      void main(){
        vec4 t = texture2D(uTex, vUv);
        // ★알파는 투명도가 아니라 **잎의 순번**이다(tools/bake_fx_tex.py bake_bush_leaf).
        //   컷을 올리면 순번이 낮은 바깥 잎부터 사라진다 = 잎이 한 장씩 갈라진다.
        if (t.a < vCut) discard;
        gl_FragColor = vec4(t.rgb * uTint, 1.0);
      }`,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.name = 'BUSH_FRONT_LEAVES';
  mesh.frustumCulled = false;      // 경계구가 없다(위치를 정점 셰이더가 만든다)
  mesh.castShadow = false;         // 빌보드 그림자는 깊이 패스에 discard 가 없어 판때기로 나온다
  mesh.receiveShadow = false;
  mesh.visible = false;
  mesh.renderOrder = 1;
  scene.add(mesh);
  FOL.mesh = mesh; FOL.geo = g; FOL.mat = mat;

  // 텍스처가 없으면 앞잎만 안 선다. 게임은 그대로 돈다.
  new THREE.TextureLoader().load(FOL_TEX + location.search, t => {
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    t.anisotropy = 4;
    mat.uniforms.uTex.value = t;
    mat.needsUpdate = true;
  }, undefined, () => console.warn('[stealth] ' + FOL_TEX + ' 를 못 읽었다. 앞잎 없이 간다'));
}

let folN = 0;
// 카드 한 장을 슬롯 n 에 쓴다. 다음 슬롯 번호를 돌려준다.
function card(n, cx, cy, cz, hw, hh, rot, cut) {
  for (let v = 0; v < 4; v++) {
    const o = n * 4 + v;
    FOL.cen[o * 3] = cx; FOL.cen[o * 3 + 1] = cy; FOL.cen[o * 3 + 2] = cz;
    FOL.size[o * 2] = hw; FOL.size[o * 2 + 1] = hh;
    FOL.cut[o] = cut;
    FOL.rot[o] = rot;
  }
  return n + 1;
}

function foliage() {
  if (!FOL.mesh) return;
  const zone = myBush >= 0 ? myBush : lastBush;
  const k = zone >= 0 ? ease(BUSH[zone].t) : 0;
  if (k <= 0.004 || !FOL.mat.uniforms.uTex.value) {
    if (FOL.mesh.visible) { FOL.mesh.visible = false; FOL.geo.setDrawRange(0, 0); folN = 0; }
    return;
  }
  FOL.mat.uniforms.uT.value = performance.now() * 0.001;
  // 몸을 덮는 잎을 갈라 놓는 기준점. 매 프레임 플레이어를 따라간다
  FOL.mat.uniforms.uPly.value.set(px, LV.groundY(px, pz) + HOLE_Y, pz);
  const base = CUT_OPEN + (CUT_SHUT - CUT_OPEN) * (1 - k);
  let n = 0;
  // (가) 포기 자리. 실제 수풀이 심긴 곳이라 카드가 수풀의 일부로 읽힌다
  const sp = BUSH[zone].spots;
  for (let i = 0; i < sp.length && n < FOL_MAX; i++) {
    const s = sp[i];
    const dx = s.x - px, dz = s.z - pz;
    const d2 = dx * dx + dz * dz;
    if (d2 > FOL_R * FOL_R) continue;
    const q = d2 / (FOL_R * FOL_R);
    for (let r = 0; r < FOL_ROWS.length && n < FOL_MAX; r++) {
      const w = FOL_ROWS[r];
      const cut = base + FOL_FAR_BIAS * q * q + w.cut;
      if (cut >= 1.0) continue;               // 어차피 한 장도 안 그려진다
      n = card(n, s.x + s.ux * w.dx, s.y + w.dy, s.z + s.uz * w.dx,
        s.hw * w.sc, s.hh * w.sc, s.rot + (r ? 0.30 : -0.22), cut);
    }
  }
  // (나) 빈틈 메우기. 몸 바로 앞이 비면 아무리 잎을 많이 세워도 안 가려진다
  const fl = BUSH[zone].fill;
  for (let i = 0; i < fl.length && n < FOL_MAX; i++) {
    const f = fl[i];
    const dx = f.x - px, dz = f.z - pz;
    const d2 = dx * dx + dz * dz;
    if (d2 > FILL_R * FILL_R || d2 < FILL_MIN * FILL_MIN) continue;
    const fq = d2 / (FILL_R * FILL_R);
    const cut = base + FOL_FAR_BIAS * fq * fq + 0.04;
    if (cut >= 1.0) continue;
    n = card(n, f.x, f.y, f.z, f.hw, f.hh, f.rot, cut);
  }
  folN = n;
  FOL.geo.setDrawRange(0, n * 6);
  FOL.mesh.visible = n > 0;
  if (!n) return;
  FOL.geo.attributes.aCen.needsUpdate = true;
  FOL.geo.attributes.aSize.needsUpdate = true;
  FOL.geo.attributes.aCut.needsUpdate = true;
  FOL.geo.attributes.aRot.needsUpdate = true;
}

// ---------------------------------------------------------------------------
// (3) 경계 링 — 바닥에 "여기부터 부쉬" 를 옅게 그린다
// ---------------------------------------------------------------------------
// 구역은 3.2m 격자 칸의 모임이다(level1.json cells/rects). 그래서 외곽선은
// **이웃 칸이 없는 변**만 모으면 정확히 나온다. 그 다음 한 줄로 이어지는 변을
// 합쳐서(안 합치면 칸 이음매마다 띠가 겹쳐 가운데 줄이 생긴다) 띠를 두른다.
const RING = { mesh: null, geo: null, str: null, span: [] };

function outlineOf(rects, cell) {
  const EPS = 0.03;
  const cells = new Set();
  for (const r of rects) {
    const a = (r.x - r.hx) / cell, b = (r.x + r.hx) / cell;
    const c = (r.z - r.hz) / cell, d = (r.z + r.hz) / cell;
    if (Math.abs(a - Math.round(a)) > EPS || Math.abs(b - Math.round(b)) > EPS
      || Math.abs(c - Math.round(c)) > EPS || Math.abs(d - Math.round(d)) > EPS) return null;
    for (let ix = Math.round(a); ix < Math.round(b); ix++) {
      for (let iz = Math.round(c); iz < Math.round(d); iz++) cells.add(ix + '|' + iz);
    }
  }
  // 이웃이 없는 변만. axis='x' 면 x 가 고정이고 z 로 뻗는 변이다
  const segs = [];
  for (const key of cells) {
    const p = key.split('|');
    const ix = +p[0], iz = +p[1];
    if (!cells.has((ix - 1) + '|' + iz)) segs.push({ axis: 'x', fix: ix * cell, lo: iz * cell, hi: (iz + 1) * cell, n: -1 });
    if (!cells.has((ix + 1) + '|' + iz)) segs.push({ axis: 'x', fix: (ix + 1) * cell, lo: iz * cell, hi: (iz + 1) * cell, n: 1 });
    if (!cells.has(ix + '|' + (iz - 1))) segs.push({ axis: 'z', fix: iz * cell, lo: ix * cell, hi: (ix + 1) * cell, n: -1 });
    if (!cells.has(ix + '|' + (iz + 1))) segs.push({ axis: 'z', fix: (iz + 1) * cell, lo: ix * cell, hi: (ix + 1) * cell, n: 1 });
  }
  // 한 줄로 이어지는 변 합치기
  const by = {};
  for (const s of segs) (by[s.axis + s.n + '@' + s.fix.toFixed(2)] = by[s.axis + s.n + '@' + s.fix.toFixed(2)] || []).push(s);
  const out = [];
  for (const key in by) {
    const g = by[key].sort((a, b) => a.lo - b.lo);
    let cur = { axis: g[0].axis, fix: g[0].fix, lo: g[0].lo, hi: g[0].hi, n: g[0].n };
    for (let i = 1; i < g.length; i++) {
      if (g[i].lo <= cur.hi + 1e-4) cur.hi = Math.max(cur.hi, g[i].hi);
      else { out.push(cur); cur = { axis: g[i].axis, fix: g[i].fix, lo: g[i].lo, hi: g[i].hi, n: g[i].n }; }
    }
    out.push(cur);
  }
  return out;
}

function buildRing(d) {
  if (RING.mesh || !scene) return;
  const cell = d.cell || 3.2;
  // 경계에서 바깥으로의 단면. 안쪽 바닥은 아래에서 판으로 따로 깐다
  const OFF = [0, RING_EDGE, RING_OUT];
  const dark = new THREE.Color(RING_DARK), lite = new THREE.Color(RING_LITE);
  const COL = [dark, lite, lite];
  const AL = [RING_A_IN, RING_A_EDGE, 0];
  const P = [], A = [], C = [], S = [], I = [];
  RING.span.length = 0;
  const put = (x, z, a, col) => {
    P.push(x, LV.groundY(x, z) + RING_LIFT, z);
    A.push(a); C.push(col.r, col.g, col.b); S.push(1);
    return P.length / 3 - 1;
  };
  for (let bi = 0; bi < BUSH.length; bi++) {
    const v0 = A.length;
    // (가) 구역 안쪽 바닥. 칸마다 판 하나. 이웃한 칸끼리는 변을 딱 맞춰 겹치지 않는다
    for (const r of BUSH[bi].rects) {
      const q0 = put(r.x - r.hx, r.z - r.hz, RING_A_IN, dark);
      const q1 = put(r.x + r.hx, r.z - r.hz, RING_A_IN, dark);
      const q2 = put(r.x + r.hx, r.z + r.hz, RING_A_IN, dark);
      const q3 = put(r.x - r.hx, r.z + r.hz, RING_A_IN, dark);
      I.push(q0, q1, q2, q0, q2, q3);
    }
    // (나) 경계 바깥 띠
    const segs = outlineOf(BUSH[bi].rects, cell);
    if (!segs) {
      console.warn('[stealth] ' + BUSH[bi].id + ' 이 격자에 안 맞는다. 경계 띠를 건너뛴다');
      RING.span.push([v0, A.length - v0]);
      continue;
    }
    for (const s of segs) {
      // 모서리를 메우려고 양끝을 바깥 폭만큼 늘인다. 볼록한 모서리가 이걸로 닫힌다
      const lo = s.lo - RING_OUT, hi = s.hi + RING_OUT;
      const base = P.length / 3;
      for (let e = 0; e < 2; e++) {
        const t = e ? hi : lo;
        for (let j = 0; j < OFF.length; j++) {
          const off = OFF[j] * s.n;
          const x = s.axis === 'x' ? s.fix + off : t;
          const z = s.axis === 'x' ? t : s.fix + off;
          put(x, z, AL[j], COL[j]);
        }
      }
      for (let j = 0; j < OFF.length - 1; j++) {
        const a = base + j, b = base + j + 1, c = base + OFF.length + j, e = base + OFF.length + j + 1;
        I.push(a, c, e, a, e, b);
      }
    }
    RING.span.push([v0, A.length - v0]);
  }
  if (!I.length) return;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(P), 3));
  g.setAttribute('aA', new THREE.BufferAttribute(new Float32Array(A), 1));
  g.setAttribute('aC', new THREE.BufferAttribute(new Float32Array(C), 3));
  RING.str = new Float32Array(S);
  g.setAttribute('aS', new THREE.BufferAttribute(RING.str, 1).setUsage(THREE.DynamicDrawUsage));
  g.setIndex(P.length / 3 > 65535 ? new THREE.BufferAttribute(new Uint32Array(I), 1)
    : new THREE.BufferAttribute(new Uint16Array(I), 1));
  g.computeBoundingSphere();
  const mat = new THREE.ShaderMaterial({
    transparent: true, depthTest: true, depthWrite: false, fog: false,
    side: THREE.DoubleSide, blending: THREE.NormalBlending,
    vertexShader: `
      attribute float aA; attribute vec3 aC; attribute float aS;
      varying float vA; varying vec3 vC;
      void main(){ vA = aA * aS; vC = aC;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `
      varying float vA; varying vec3 vC;
      void main(){ if (vA <= 0.004) discard; gl_FragColor = vec4(vC, vA); }`,
  });
  const mesh = new THREE.Mesh(g, mat);
  mesh.name = 'BUSH_EDGE_RING';
  mesh.renderOrder = 6;            // 바닥(불투명) 뒤, 전멸 링(8)·궤적(3~5) 과 안 싸운다
  mesh.castShadow = false;
  mesh.receiveShadow = false;
  scene.add(mesh);
  RING.mesh = mesh; RING.geo = g;
}

function ringLevel(i, s) {
  if (!RING.str || i >= RING.span.length) return;
  const sp = RING.span[i];
  if (!sp[1]) return;
  for (let v = sp[0]; v < sp[0] + sp[1]; v++) RING.str[v] = s;
  RING.geo.attributes.aS.needsUpdate = true;
}

// ---------------------------------------------------------------------------
// (4) 플레이어 몸 — 먹 실루엣
// ---------------------------------------------------------------------------
// 알파를 안 쓴다. 재질의 **출력색만** 물들인다.
//   · 채도를 죽이고(휘도만 남겨) 어둡게 눌러서 잎 그늘에 녹인다
//   · 실루엣 가장자리에 옅은 청록 림을 얹어 "어디 있는지"는 잃지 않게 한다
// ★칼(SW_)·방패(SH_)·칼날 발광·후광 껍질까지 **전부** 같은 처리에 넣는다.
//   예전 코드는 이 넷을 빼놨고 그래서 칼만 하얗게 떴다.
//   후광 껍질은 가산합성이라 색을 누르면 그대로 빛이 준다(따로 만질 필요가 없다).
const INK = {
  k: { value: 0 },
  col: { value: new THREE.Color(INK_COL) },
  lo: { value: INK_LO },
  hi: { value: INK_HI },
  rim: { value: new THREE.Color(RIM_COL) },
  rimK: { value: RIM_K },
};
const INK_HEAD = '\nuniform float uInkK; uniform vec3 uInkCol; uniform float uInkLo;'
  + '\nuniform float uInkHi; uniform vec3 uInkRim; uniform float uInkRimK;';

function inkBody(rim) {
  // ★끼우는 자리가 <dithering_fragment> 인 이유: 모든 내장 재질의 **맨 끝**이고,
  //   여기서는 gl_FragColor 가 이미 완성돼 있다. 칼날 발광처럼 <opaque_fragment> 를
  //   통째로 갈아치운 재질도 이 지점은 그대로라 같은 코드가 그대로 먹는다.
  const l = ['#include <dithering_fragment>',
    'if (uInkK > 0.002) {',
    '  vec3 _c = gl_FragColor.rgb;',
    '  float _l = dot(_c, vec3(0.2126, 0.7152, 0.0722));',
    '  vec3 _ink = uInkCol * (uInkLo + uInkHi * pow(max(_l, 0.0), 0.55));'];
  if (rim) {
    // normal(뷰공간) 과 vViewPosition 은 조명 계열 재질이면 항상 있다.
    l.push('  float _fr = 1.0 - abs(dot(normalize(normal), normalize(vViewPosition)));');
    l.push('  _ink += uInkRim * pow(_fr, ' + RIM_POW.toFixed(1) + ') * uInkRimK;');
  }
  l.push('  gl_FragColor.rgb = mix(_c, _ink, uInkK);', '}');
  return l.join('\n');
}

function patchInk(mat) {
  if (!mat || mat.userData.__ink) return;
  // 셰이더를 통째로 직접 쓴 재질에는 끼울 자리(<dithering_fragment>)가 없다.
  // 지금 캐릭터에는 없지만, 나중에 붙어도 조용히 지나가게 막아 둔다.
  if (mat.isShaderMaterial) { mat.userData.__ink = true; return; }
  mat.userData.__ink = true;
  // 림은 법선이 있는 재질만. MeshBasicMaterial(칼날 발광·후광)은 normal 이 없다
  const rim = !!(mat.isMeshToonMaterial || mat.isMeshStandardMaterial
    || mat.isMeshPhongMaterial || mat.isMeshLambertMaterial);
  const prev = mat.onBeforeCompile;
  const prevSrc = prev ? prev.toString() : '';
  const ownKey = Object.prototype.hasOwnProperty.call(mat, 'customProgramCacheKey')
    ? mat.customProgramCacheKey : null;
  mat.onBeforeCompile = function (sh, renderer) {
    if (prev) prev.call(this, sh, renderer);
    sh.uniforms.uInkK = INK.k;
    sh.uniforms.uInkCol = INK.col;
    sh.uniforms.uInkLo = INK.lo;
    sh.uniforms.uInkHi = INK.hi;
    sh.uniforms.uInkRim = INK.rim;
    sh.uniforms.uInkRimK = INK.rimK;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>' + INK_HEAD)
      .replace('#include <dithering_fragment>', inkBody(rim));
  };
  // ★캐시 키를 반드시 갈라야 한다. three 의 기본 키는 onBeforeCompile.toString() 인데
  //   위 래퍼는 어느 재질에 씌워도 **글자가 똑같다.** 그대로 두면 원래 셰이더가 다른
  //   재질(칼날 발광 vs 몸통)이 같은 프로그램을 나눠 써서 칼이 살로 그려진다.
  mat.customProgramCacheKey = function () {
    return 'ink' + (rim ? 'R' : 'B') + '|' + (ownKey ? ownKey.call(this) : prevSrc);
  };
  mat.needsUpdate = true;
}

let playerRoot = null;
let bodyMats = [];         // { mesh } — 그림자 토글용 목록
let bodyKids = -1;         // 마지막으로 훑었을 때 root 의 직계 자식 수(캐릭터 로드 감지)
let rescanT = 0;           // 주기 재훑기 타이머
let inkK = 0;              // 먹 실루엣 진행도 0..1
let shadowOff = false;

export function attachPlayer(root) { playerRoot = root; bodyKids = -1; rescanT = 0; }

function scanBody() {
  bodyMats = [];
  if (!playerRoot) return;
  playerRoot.traverse(o => {
    if (!o.isMesh || !o.material) return;
    // ★원래 castShadow 를 메시에 한 번만 새겨 둔다. 매번 지금 값을 읽으면
    //   숨어 있는 동안(그림자 꺼진 상태)에 다시 훑는 순간 "원래 꺼져 있었다"로
    //   굳어서 나와도 그림자가 영영 안 돌아온다.
    if (o.userData.__cast === undefined) o.userData.__cast = o.castShadow;
    o.castShadow = o.userData.__cast && !shadowOff;
    const ms = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of ms) patchInk(m);
    bodyMats.push({ mesh: o });
  });
  bodyKids = playerRoot.children.length;
}

function inkPlayer(dt) {
  if (!playerRoot) return;
  // ★매 프레임 traverse 로 노드를 세면 안 된다(캐릭터 6종이 전부 root 밑에 붙어 있어서
  //   프레임마다 수백 노드를 훑게 된다). 직계 자식 수는 O(1) 이고, 칼 교체처럼 더 깊은
  //   곳이 바뀌는 경우를 위해 0.5초에 한 번만 다시 훑는다.
  rescanT -= dt;
  if (playerRoot.children.length !== bodyKids || rescanT <= 0) { scanBody(); rescanT = 0.5; }
  const want = hiddenNow ? 1 : 0;
  const k = want ? dt / FADE_IN : -dt / FADE_OUT;
  const nk = Math.max(0, Math.min(1, inkK + k));
  if (nk === inkK) return;
  inkK = nk;
  INK.k.value = ease(inkK);
  // 그림자는 반쯤 잠긴 지점에서 끊는다. 반투명이 아니니 그림자만 남으면
  // "저기 누가 있다"가 바닥에 그려져서 숨은 그림이 안 된다.
  const off = INK.k.value > 0.5;
  if (off !== shadowOff) {
    shadowOff = off;
    for (const b of bodyMats) b.mesh.castShadow = b.mesh.userData.__cast && !off;
  }
}

// ---------------------------------------------------------------------------
// (5) HUD 한 줄 + 화면 가장자리 테두리.
// CSS 는 파일을 안 만들고 여기서 주입한다(enemy.js 와 같은 방식).
// ---------------------------------------------------------------------------
const st = document.createElement('style');
st.textContent =
  '#stHud{position:fixed;left:50%;bottom:62px;transform:translateX(-50%);z-index:6;' +
  'pointer-events:none;user-select:none;font-size:13px;font-weight:700;letter-spacing:1px;' +
  'padding:5px 14px;border-radius:14px;opacity:0;transition:opacity .16s;white-space:nowrap;' +
  'font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif}' +
  '#stHud.on{opacity:1}' +
  '#stHud.hide{color:#8ff0b6;background:rgba(6,26,16,.72);border:1px solid #2b7a52;' +
  'text-shadow:0 0 10px #0d6b3c}' +
  '#stHud.loud{color:#ffcf7a;background:rgba(32,20,4,.72);border:1px solid #8a6320;' +
  'text-shadow:0 0 10px #7a4d0d}' +
  '#stVig{position:fixed;inset:0;z-index:4;pointer-events:none;opacity:0;' +
  'transition:opacity .18s;box-shadow:inset 0 0 120px 24px rgba(24,120,70,.55)}' +
  '#stVig.on{opacity:1}' +
  '#stVig.loud{box-shadow:inset 0 0 120px 24px rgba(150,96,16,.55)}';
document.head.appendChild(st);
const hudEl = document.createElement('div'); hudEl.id = 'stHud';
document.body.appendChild(hudEl);
const vigEl = document.createElement('div'); vigEl.id = 'stVig';
document.body.appendChild(vigEl);
let hudKey = '';

function hud() {
  // 상태 세 가지: 숨음 / 숨었지만 소리가 샘 / 수풀 밖
  const key = !hiddenNow ? (myBush >= 0 ? 'seen' : 'out') : (quiet ? 'hide' : 'loud');
  if (key === hudKey) return;            // 값이 바뀔 때만 DOM 을 쓴다
  hudKey = key;
  if (key === 'hide') {
    hudEl.className = 'on hide'; hudEl.textContent = '숨었다';
    vigEl.className = 'on';
  } else if (key === 'loud') {
    hudEl.className = 'on loud'; hudEl.textContent = '숨었다 · 발소리가 샌다';
    vigEl.className = 'on loud';
  } else if (key === 'seen') {
    hudEl.className = 'on loud'; hudEl.textContent = '수풀 · 드러났다';
    vigEl.className = '';
  } else {
    hudEl.className = ''; vigEl.className = '';
  }
}

// ---------------------------------------------------------------------------
export const state = () => ({
  bush: myBush, bushId: myBush >= 0 ? BUSH[myBush].id : null,
  hidden: hiddenNow, quiet, noiseR: +noiseR.toFixed(1),
  revealT: +Math.max(0, revealT).toFixed(2),
  ink: +INK.k.value.toFixed(3),
  // ★alpha 는 이제 안 쓴다(먹 실루엣으로 갈아치웠다). 옛 검증 스크립트가 읽어도
  //   깨지지 않게 1 을 그대로 돌려준다 - 몸은 항상 불투명이다.
  alpha: 1,
});

export const debug = {
  state,
  count: () => BUSH.length,
  list: () => BUSH.map(b => ({ id: b.id, rects: b.rects.length, mesh: !!b.mesh,
                               spots: b.spots.length, t: +b.t.toFixed(3) })),
  // 이 자리에 선 요괴가 나를 보는가(콘솔에서 바로 확인)
  see: (x, z, alerted) => canSee(x, z, alerted),
  setEnabled,
  // 연출 검증 창구. 눈 없이 "잎이 몇 장 섰나 / 링이 살아 있나" 를 숫자로 본다
  fx: () => ({
    cards: folN,
    tex: !!(FOL.mat && FOL.mat.uniforms.uTex.value),
    ring: RING.mesh ? RING.geo.getAttribute('aA').count : 0,
    ringHot: RING.str ? +Math.max.apply(null, Array.from(RING.str)).toFixed(2) : 0,
    ink: +INK.k.value.toFixed(3),
    mats: bodyMats.length,
    bushT: BUSH.map(b => +b.t.toFixed(2)),
    inAlpha: BUSH[myBush >= 0 ? myBush : 0] && BUSH[myBush >= 0 ? myBush : 0].mat
      ? +BUSH[myBush >= 0 ? myBush : 0].mat.opacity.toFixed(2) : null,
  }),
  // 연출 값을 브라우저에서 바로 돌려 보기 위한 손잡이(튜닝용)
  tune: (o) => {
    if (o.inkLo !== undefined) INK.lo.value = o.inkLo;
    if (o.inkHi !== undefined) INK.hi.value = o.inkHi;
    if (o.inkCol !== undefined) INK.col.value.setHex(o.inkCol);
    if (o.rimK !== undefined) INK.rimK.value = o.rimK;
    if (o.rimCol !== undefined) INK.rim.value.setHex(o.rimCol);
    if (o.folTint !== undefined && FOL.mat) FOL.mat.uniforms.uTint.value.setHex(o.folTint);
    return { inkLo: INK.lo.value, inkHi: INK.hi.value, rimK: INK.rimK.value };
  },
};
