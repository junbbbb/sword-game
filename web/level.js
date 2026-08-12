// ---------------------------------------------------------------------------
// web/level.js — 맵(level1.glb) 을 씬에 올리고, 2D 충돌과 지면 높이를 담당한다.
//
// main.js 는 이미 2천 줄이라 맵 관련은 전부 여기로 뺐다. main.js 가 하는 일은
// loadLevel() 한 번과 slide()/groundY() 호출 몇 줄이 전부다.
//
// 설계 원칙
//  1. 충돌은 **메시를 파싱하지 않는다.** level1.json 의 colliders[] 에 축정렬 박스와
//     원 102개가 이미 들어 있다(블렌더 s20_level1.py 가 렌더 메시와 같은 부피로 뽑아준다).
//     레이캐스트·BVH 는 이 규모에서 전부 과잉이다.
//  2. 판정은 **평면 2D(XZ)** 다. 높이를 안 본다. 맵에서 넘어다닐 수 있는 건 20cm 짜리
//     대웅전 단 하나뿐이라 3D 로 만들 이유가 없다(높이는 groundY 가 따로 본다).
//  3. ★벽에 닿으면 멈추는 게 아니라 **미끄러진다.** 원하는 자리로 일단 옮긴 뒤
//     파고든 만큼만 되밀어낸다(depenetration). 되밀리는 방향이 벽의 법선이라
//     벽 방향 성분만 사라지고 접선 성분은 그대로 남는다 = 벽을 타고 흐른다.
//     "벽에 부딪히면 이동 취소"로 만들면 대각선으로 걸을 때마다 딱딱 멈춰서
//     조작이 답답해진다.
//  4. 플레이어와 요괴가 **같은 함수**를 쓴다. 따로 만들면 서로 다른 벽을 보게 된다.
//
// 좌표계: level1.json 은 이미 three.js 좌표다(X=동, Y=위, Z=남). 변환하지 않는다.
// ---------------------------------------------------------------------------
import * as THREE from './lib/three.module.js';
import { GLTFLoader } from './lib/GLTFLoader.js';

// ── 반경 기준값 ──
// 몸통 반경이다. 칼을 휘두르는 폭이 아니다. 캐릭터 어깨폭이 0.5m 정도라 0.35 면
// 어깨가 벽에 살짝 닿는 자리에서 멈춘다. 통로가 3.2m(=1칸)라 0.35 로도 둘이 스쳐
// 지나갈 수 있고, 문 기둥 사이 3.33m 도 넉넉히 통과한다.
export const PLAYER_RADIUS = 0.35;
// 요괴 반경은 enemy.js 가 자기 몸집(scale)에 물려서 따로 정한다(ENEMY_R).

// 격자에 넣을 때 넉넉히 부풀리는 값. 이보다 큰 반경으로 질의하면 옆 칸 벽을 놓친다.
const AGENT_MAX_R = 0.75;
const GCELL = 4.0;               // 충돌 격자 한 칸(m). 96m 맵이 24x24 = 576칸이 된다

// ── 지면 결 ──
// 문제(실측): level1.glb 의 바닥 텍스처는 2048px 한 장으로 96m 를 덮는다. 1m 가
// 21px 이라 카메라가 가까이 붙으면 흙바닥이 그냥 뿌옇게 뭉갠 얼룩으로 보인다.
//
// 고치는 법은 두 겹이다. 텍스처를 키우는 건 답이 아니다(96m 를 200px/m 로 덮으려면
// 19200px 이다). **작은 이어붙는 그림을 여러 장 곱한다.**
//
//   ① 타일 스플랫 — 손그림 지면 네 장(풀·흙·돌·마른풀)을 1.6~2.4m 주기로 깔고
//      스플랫맵(512, blender/s20_level1.py 가 굽는다)으로 자리마다 섞는다.
//      "여기는 풀, 여기는 밟힌 흙, 여울목은 젖은 박석"이 결로 드러난다.
//   ② 잔결 노이즈 — 그 위에 밝기만 ±10% 흔드는 한 장을 더 곱한다. 타일 계단이
//      너무 매끈하게 반복되는 걸 흐트러뜨린다.
//
// ★★두 겹 다 **곱수의 평균이 1** 이다. 타일은 자기 평균색으로 나눠서 쓰고
//   (아래 uTR), 잔결은 텍스처 자체의 평균이 0.5 다. 그래서
//     - 멀어져서 밉맵이 다 뭉개지면 곱수가 정확히 1.0 로 수렴한다
//       = 게임 거리의 화면 톤은 하나도 안 바뀐다
//     - 어느 구역이든 평균 밝기가 보존된다
//       = "밝고 따뜻하면 걸을 수 있다" 색 규칙이 결 때문에 깨질 수가 없다
//   이게 이 파일에서 제일 중요한 계약이다. 곱수를 더할 일이 생기면 같은 규칙을 지켜라.
//
// ★★패치는 **하나**다. onBeforeCompile 을 두 번 걸지 마라. three 는 재질 파라미터로
//   프로그램을 캐시하는데 그 키에 onBeforeCompile 이 안 들어가서, 나중 것이 앞엣것을
//   통째로 덮거나 include 순서가 어긋난다. 아래 patchFloorMaterial 한 곳에서만 짠다.
const DETAIL_TEX = './tex/ground_detail.png';
const DETAIL_FINE = 1 / 1.7;     // 잔결 주기의 역수(1/m)
const DETAIL_WIDE = 1 / 4.3;     // 넓은 얼룩 주기의 역수(1/m)
const DETAIL_WIDE_W = 0.72;      // 넓은 얼룩을 섞는 비율
// 곱수 폭. 아래 자르는 값과 짝이다. 0.26 · 0.55 · 1.0 을 실제 화면에서 재봤다:
// 0.26 은 있는 듯 없는 듯하고 1.0 은 흙이 지저분해 보인다. 0.55 에서 결이 또렷하면서
// 아직 흙으로 읽힌다(renders/history/v71_polish/00_gain_ladder.png).
// ★타일이 들어오면서 결의 주역이 바뀌었다. 잔결은 거들기만 하면 되므로 낮춘다.
const DETAIL_GAIN = 0.38;
const DETAIL_MIN = 0.90, DETAIL_MAX = 1.10;
const DETAIL_FADE0 = 30.0;       // 이 거리부터 서서히 빼고
const DETAIL_FADE1 = 55.0;       // 여기서 완전히 끈다(먼 바닥이 반짝이는 걸 막는다)

// ── 지면 타일 4장 ──
// 순서가 스플랫맵 채널 순서다: R=풀 G=흙 B=돌 A=마른풀. 바꾸면 s20 도 같이 바꿔라.
// period  타일 한 판이 몇 m 인가. ★넷 다 다른 값이고 서로 나누어떨어지지 않는다.
//         한 주기로 통일하면 그 간격마다 같은 무늬가 도는 게 바로 보인다. 값이 다르면
//         두 타일이 섞이는 자리에서 무늬가 다시 맞물리기까지 아주 멀다
//         (스플랫이 초원에 마른 풀을 얼룩으로 섞으므로 초원은 항상 2.1m 와 2.4m 의
//          겹침이다 = 두 주기 혼합).
// deg     읽는 좌표를 돌리는 각. 격자 방향까지 갈라 놔야 네 판이 안 나란해진다
// ref     타일의 평균색. **로딩 때 png 에서 직접 잰다.** 여기 적힌 값은 캔버스를
//         못 읽었을 때의 대비책일 뿐이다(tools/bake_fx_tex.py 가 찍어 준 값).
const TILES = [
  { file: './tex/tile_grass.png', period: 2.10, deg: 27, ref: [0.4197, 0.5502, 0.3399] },
  // ★★v97(11차). period 1.32 -> 2.55. 이 채널의 **역할이 바뀌었다** — 캠프 얼룩에서
  //   **길**로. v90 이 주 동선을 판석(B)으로 깔았는데, 2.75m 판돌이 6.4m 폭 직선
  //   복도를 따라 줄줄이 반복되면서 화면에서 황토색 다각형 격자가 됐고 그게
  //   오너가 본 "화장실 타일" 의 절반이었다(before/b2_road_ns.jpg).
  //   스플랫에서 주 동선 판석 가중치의 72% 를 이 채널로 옮겼다
  //   (tools/ground_splat_remix.py). 내용물도 갈았다 — codex path_organic 은
  //   흙이 지배하고 판석 **조각**이 불규칙하게 박혀 "열 맞춘 판석"이 안 생긴다.
  //   ★tools/bake_fx_tex.py TILE_PERIOD 와 반드시 같은 값이어야 한다.
  //   ★네 주기가 서로 안 나누어떨어져야 한다는 규칙은 그대로: 2.10 / 2.55 / 2.75 / 2.40.
  { file: './tex/tile_dirt.png', period: 2.55, deg: 41, ref: [0.5795, 0.5111, 0.4200] },
  // ★★v96-B. period 1.28 -> 2.75. B 채널의 **내용물이 갈렸다** — 손바닥 파빙에서
  //   판돌(incoming/tiles_v2/slab.jpg)로. 조각 하나가 그림의 1/3 이라 1.28m 에서는
  //   화면에서 43cm 짜리 자갈이 되고, 그게 10차가 남긴 "잔균열 유약" 인상이었다.
  //   2.75m 면 조각 하나가 90cm = 레퍼런스(롤) 길의 판돌 크기다.
  //   ★tools/bake_fx_tex.py TILE_PERIOD 와 반드시 같은 값이어야 한다(자가 어긋난다).
  //   ★주기 넷이 서로 안 나누어떨어져야 한다는 위 규칙은 그대로다:
  //     2.10 / 1.32 / 2.75 / 2.40.
  { file: './tex/tile_stone.png', period: 2.75, deg: 111, ref: [0.5996, 0.6097, 0.5804] },
  { file: './tex/tile_dry.png', period: 2.40, deg: 154, ref: [0.6605, 0.5798, 0.3602] },
];
const SPLAT_TEX = './tex/ground_splat.png';   // level1.json 의 splatmap 이 이기고, 없으면 이것

// ── ★★v97(11차). 메달리온 데칼 — "화장실 타일" 신고의 진짜 처방 ────────────
// 오너: **"지금 너무 패턴 느낌이라 별로야, 화장실 타일 같잖아. 일러스트 느낌이어야지."**
//
// ★자기상관으로는 이 신고를 못 잡는다. 실측했다 — 신고 당시 초원 자기상관은
//   이미 0.118 로 규격(0.35) 한참 안이었다. 사람 눈이 잡아낸 것은 **표식의 되풀이**다.
//   v96-B 잔디는 에너지의 66% 가 10~25cm 한 대역에 몰려 있어서 크기가 하나뿐인
//   밝은 C 자 붓자국이 2.1m 마다 돌아왔다. 상관값이 낮아도 그건 눈에 보인다.
//
// ★그래서 **텍스처를 갈아서는 안 풀리고 배치 문법이 바뀌어야 한다.**
//   오너 레퍼런스(refpack/lol_ground_owner_ref2.png)의 문법이 셋이다.
//     ① 조용한 잔디 바탕(표식 없음)   ② 큰 **비반복** 문양 덩어리가 명소에 하나씩
//     ③ 유기적 경계(풀이 석판을 삼킨다)
//   ①은 타일(tools/tileize.py)이, ②③이 이 겹이다. 되풀이를 지우는 것이 아니라
//   **되풀이가 아닌 것을 하나 놓아** 눈이 거기 앉게 만드는 쪽이다.
//
// 구현을 왜 이렇게 했나 — 셋 중에 골랐다
//   (가) 쿼드 메시 데칼: 드로우콜 6개 + 깊이 싸움(폴리곤 오프셋) + 기복 있는 지면에서
//        평면이 파고든다. 조명도 따로 논다
//   (나) s20 재굽기로 바닥 베이스컬러에 구워 넣기: 2048 이 96m = 21 px/m 이라
//        7m 짜리 문양이 텍스처에서 147px 다. 화면(150 px/m)의 **1/7** 이라 뭉갠다.
//        게다가 재굽기는 배치·콜라이더를 건드릴 위험이 있다
//   (다) **바닥 셰이더에 겹 하나 추가** ← 이걸 골랐다. 드로우콜 0, 조명 자동 일치,
//        기복을 그대로 탄다. 값은 조회 1회 + 자리마다 ALU 열 몇 개.
//        전용 아틀라스라 1024px 이 7m = 146 px/m 로 화면과 같다.
//
// ★자리는 손으로 안 찍었다. renders/history/v97_wave11/ground/w11g_place.py 가
//   콜라이더(AABB 거리)·소품·수풀·단을 다 피한 빈터를 훑어서 고른 값이다.
//   ★★상자 콜라이더를 hypot(hx,hz) 원으로 바꾸면 안 된다 — 외곽 벽처럼 길고 얇은
//     상자가 반경 24m 원이 되어 맵 절반이 후보에서 사라진다(첫 판에서 밟았다).
const MED_TEX = './tex/ground_medallion.png';   // tools/bake_medallion.py 가 굽는다
// size = **칸 한 변의 m**. 그림이 칸의 68% 를 차지하므로 실제 문양 지름은 그 0.68 배다
//        (size 10.5 -> 지름 7.1m). ★빈터반경 >= size*0.34 여야 소품에 안 가린다
// cell = 아틀라스 칸. 0 = 온전한 메달리온 · 1 = 부서진 조각 고리(가운데가 비었다)
// ★서로 **안 겹쳐야** 한다. 아래 셰이더가 "겹치지 않는다"를 전제로 uv 를 더해서
//   조회를 한 번으로 묶는다. 겹치면 두 uv 가 합쳐져 엉뚱한 자리를 문다.
//   (검증: level.medallions() 가 쌍마다 거리를 재서 알려 준다)
const MEDALLIONS = [
  { x: -33.0, z: 36.0, size: 10.5, deg: 18, cell: 0 },   // 스폰 전방. 첫 화면에 들어온다
  { x: 0.0, z: 34.2, size: 12.0, deg: 104, cell: 0 },    // 남 중앙 초원(출구 어귀)
  { x: 25.8, z: 29.4, size: 10.0, deg: 231, cell: 1 },   // 동쪽 초원 수풀 사이 공터
  { x: -23.4, z: 1.2, size: 9.0, deg: 66, cell: 0 },     // 서쪽 초원(개울 쪽)
  // ★칸을 섞는 규칙: 한 화면에 둘이 걸릴 만큼 가까운 쌍은 **다른 칸**을 준다.
  //   ⑤와 ⑥은 13.9m 라 같이 보일 수 있어서 온전판 / 조각고리로 갈랐다.
  { x: -13.2, z: -18.6, size: 11.0, deg: 341, cell: 0 }, // 보스 어귀
  { x: 0.0, z: -22.8, size: 11.5, deg: 143, cell: 1 },   // ★보스마당(판석 광장) 반복 희석
];
const MED_AMT = 1.0;             // 0 이면 데칼이 통째로 빠진다(전후 비교 손잡이)
// ★칠한 색을 화면색으로 되돌리는 기준 밝기(선형 휘도). 초원 베이스컬러 #8ea855 의
//   선형 휘도가 0.344 다. 데칼은 **곱수가 아니라 색**이라 그냥 덮으면 그 자리의
//   매크로 볕·그늘(2048 베이스컬러에 구워 둔 것)이 통째로 지워져 스티커가 된다.
//   그래서 "이 자리가 기준보다 얼마나 밝은가" 를 곱해 볕·그늘만 따라가게 한다.
const MED_REF_L = 0.344;
const MED_SHADE_MIN = 0.72, MED_SHADE_MAX = 1.35;

// ── ★v96. 산포 디테일 (꽃잎·자갈·낙엽·잔풀) ──────────────────
// 오너 레퍼런스(롤 실물)에는 파란 꽃잎이 수십 장 흩뿌려져 있다. 블라인드 심사가
// 우리 판에서 이걸 **0개**로 셌다. 여기서 그 겹을 얹는다.
//
// ★왜 베이스컬러(2048)가 아니라 전용 타일인가. 2048 이 96m 를 덮으므로 21 px/m 인데
//   화면은 150 디바이스 px/m 이다. 15cm 짜리 꽃잎이 텍스처에서 3px 이라 화면에서는
//   21px 짜리 **뭉갠 얼룩**이 된다(9차의 꽃 얼룩이 정확히 그 실패였다).
//   전용 타일은 2048 이 8.5m 라 241 px/m — 화면보다 1.6배 촘촘하다.
// ★되풀이는 **성김**으로 막는다. 덮개 6% 짜리 층을 다시 저주파 마스크로 잘라
//   면적의 40% 에만 올린다. 성긴 것이 오히려 주기를 안 들키게 한다.
// ★이 겹만은 곱수가 아니라 **덮어쓰기**다(꽃잎은 밝기 변조가 아니라 물건이다).
//   그래서 구역 평균색이 덮개만큼 밀린다 — 덮개를 낮게 잡는 이유가 이것이기도 하다.
//   tools/bake_scatter_tex.py 가 굽는다.
const SCATTER_TEX = './tex/ground_scatter.png';
const SCATTER_PERIOD = 8.5;      // ★tools/bake_scatter_tex.py PERIOD_M 과 같아야 한다
const SCATTER_DEG = 23;          // 타일 격자·스플랫과 안 나란하게 튼다
const SCATTER_AMT = 1.0;         // 0 이면 통째로 뺀 그림이 나온다(전후 비교 손잡이)
// 곱수의 세기. mix(1, 비율, amt) 라 평균 1 은 그대로 두고 **폭만** 늘린다.
// ★0 / 1.0 / 1.6 / 2.2 / 2.8 을 같은 프레임에서 재봤다
// (renders/history/v82_splat/07_amt_ladder.png).
//   1.0 = 있는 듯 없는 듯. 곱하는 자리가 선형 공간이라 비율 1.18 이 화면에서는 8% 밖에 안 된다
//   2.8 = 지저분하다. 초원이 얼룩덜룩해서 구역이 아니라 노이즈로 읽힌다
//   1.9 = 손그림 밀도가 살면서 초원이 한 덩이로 읽힌다. 그리고 여기까지가
//         **아무 픽셀도 클램프에 안 닿는** 한계다(타일 비율 0.635~1.492 -> 0.31~1.94).
//         클램프에 닿는 순간 그 자리만 평균 1.0 계약이 깨진다.
// ★v94. 1.9 -> 2.05. 대역 재배치(tools/tileize.py)로 타일 자체의 비율 폭이
//   0.633~1.489 로 정리되면서, 늘려도 클램프에 안 닿는 여유가 생겼다.
//   amt 2.05 + 클램프 0.24 에서 **네 장 전부 클램프 밖 0.0000%** 를 실측 확인했다
//   (계약이 깨지는 건 자르는 순간이지 늘리는 순간이 아니다).
const TILE_AMT = 2.05;           // 0 이면 타일이 통째로 빠진다(전후 비교용 손잡이)
// 곱수를 자르는 폭. 타일 자체의 비율이 0.64~1.49 이고 TILE_AMT 로 그 폭을 늘리므로
// 여기는 **사고 방지용 안전망**이다(스플랫이 두 타일의 어두운 쪽끼리 겹쳤을 때).
// ★평소에 여기 닿으면 안 된다. 자르는 순간 평균 1.0 이 깨져서 그 자리만 어두워진다.
const TILE_MIN = 0.24, TILE_MAX = 2.10;   // ★v94. amt 2.05 에 맞춰 안전망을 같이 넓혔다
// 타일 좌표를 저주파로 미는 폭(m). 격자가 자로 잰 듯 반듯하면 눈이 바로 잡아낸다.
// ★★밀 때 쓰는 값은 **아주 매끄러워야 한다.** 처음에는 잔결 노이즈에서 뽑아 둔 두 값
//   (1.7m·4.3m 주기)을 그대로 썼다. 조회는 안 늘었는데 **프레임 시간이 6.5ms 늘었다.**
//   원인: UV 에 고주파를 더하면 화면 미분(dFdx/dFdy)이 요동쳐서 하드웨어가 밉 단계와
//   이방성 비율을 매 픽셀 크게 잡는다. 조회 수가 아니라 **필터링 비용**이 폭발한다.
//   그래서 텍스처 대신 sin 두 번으로 15~19m 짜리 완만한 물결을 만든다. ALU 두 번이라
//   공짜에 가깝고, 미분 기여가 진폭 x 주파수 = 0.5 x 0.41 = 0.21 로 묶여 있다.
//   (1.6~2.4m 짜리 국소 격자는 이미 주기 네 개 x 회전 네 개 + 스플랫 섞임이 깬다.
//    이 물결은 맵 전체에서 격자가 한 줄로 쭉 이어지지 않게 하는 몫만 맡는다.)
const TILE_WARP = 0.5;
// 타일의 이방성 필터. 이 게임은 카메라가 pitch 0.86(지면에서 49도)으로 **고정**이라
// 필요한 비율이 1/sin(49도) = 1.32 다. 4 면 14도까지 덮으므로 넉넉한 보험이다.
// ★8 로 잡았다가 프레임 시간이 5.6ms -> 16.0ms 가 된 적이 있다(+183%). 범인은 이방성
//   자체가 아니라 **위의 텍스처 워프**였다. 이방성은 UV 미분이 요동칠 때 그 요동을
//   그대로 배로 곱한다. 워프를 매끄럽게 고친 뒤로는 2·4·8 이 전부 측정 잡음 안이다.
//   그래도 값을 낮게 두는 이유: 약한 기기에서는 이 배수가 그대로 값이 된다.
const TILE_ANISO = 4;
let DETAIL_N = 0;                // 실제로 결이 붙은 재질 수(검증용)
let SPLAT_PIX = null;            // {w, h, data} 검증용. 브라우저에서 가중치를 되짚는다

// ── 개울 수면 ──────────────────────────────────────────────
// 건틀릿 1회차 지형 판정에서 제일 낮은 점수가 물이었다(1/10).
//   "단색 시안 리본 + 자로 그은 직선 경계. 깊이·포말·젖음·흐름이 전무."
// 맞는 지적이다. v93 의 수면은 재질 하나(#4f97b0)에 가장자리만 정점색으로 죽인
// 평면이었다. 여기서 다섯 가지를 얹는다. 전부 **셰이더 한 벌**로 끝낸다
// (메시를 겹치면 반투명 정렬 문제가 생기고 드로우콜도 는다).
//
//   ① 깊이   물가는 얕고 밝다 -> 중심은 어둡고 짙다. 3~4단 계단(툰)이라
//            그라데이션이 아니라 **칠한 물**로 읽힌다
//   ② 강바닥 얕은 자리에 자갈이 비친다. ★지면 텍스처에 파란 틴트를 씌워 재사용하지
//            않는다(그건 흙에 물감 칠한 것으로 보인다). tex/water_bed.png 전용 한 장
//   ③ 포말   물가 선을 따라 흰 거품. 노이즈로 뜯고 시간에 따라 찰랑인다
//   ④ 흐름   길이 방향으로 흐르는 밝은 띠. 물이 **움직인다**는 유일한 신호다
//   ⑤ 젖은 림 물가 바로 안쪽에 짙은 띠. 뭍과 물 사이의 경계를 부드럽게 만든다
//
// ★UV 계약: s20_level1.py 의 add_stream_ribbon 이 굽는다.
//     u = 흐름 방향 월드 x(m)   v = 기슭까지의 정규화 거리(0 기슭 · 1 중심)
//   정점색이 아니라 UV 를 쓰는 이유는 저쪽 주석에 적었다(패치 실패 시 색이 안 상한다).
// ★시간은 mesh.onBeforeRender 에서 넣는다. level.js 에는 프레임 훅이 없고,
//   rAF 를 따로 돌리면 탭이 숨어도 계속 돈다. onBeforeRender 는 **그려질 때만** 불린다.
const WATER_TEX = './tex/water_bed.png';
const WATER_PERIOD = 3.2;        // water_bed 한 판이 덮는 m (bake_water_tex.py 와 같은 값)
// 물빛 세 단. ★귀멸 톤에 맞춰 채도를 낮췄다. v93 의 #4f97b0 는 채도 55% 라
//   맵에서 수풀 다음으로 쨍했다(심사: 채도 스프레드 58pt). 여기 셋의 평균 채도는 41% 다.
//   물가(밝고 탁함) -> 중간 -> 심(어둡고 푸름) 순으로 명도가 떨어진다.
// ★v94 2차. 첫 판은 물가색을 (0.62,0.74,0.72) 로 아주 밝게 잡았는데, 화면에서
//   **개울 한가운데로 흰 길이 난 것**처럼 보였다. 원인은 색이 아니라 자리다 —
//   수면 리본은 물칸 3.2m 중 가운데 1.6m 만 덮으므로 그 가장자리가 물가가 아니다.
//   그래서 포말은 바닥칠로 옮기고(s20_level1.py 15절), 메시는 **칠한 얕은 물보다
//   확실히 깊은 물**로만 그린다. 기준은 바닥에 칠한 개울색 #539db6 =
//   (0.325, 0.616, 0.714) 이고, 여기 셋은 전부 그보다 어둡다.
// ★★v96. 오너 판정 "9차에 물 셰이더가 있는데 화면에서 안 읽힌다". 실측으로
//   원인을 특정했다 — **셰이더는 멀쩡히 돌고 있었다. 색이 틀렸다.**
//   이 세 값은 diffuseColor 에 그대로 들어가므로 **선형(linear)** 이다. 그런데
//   위 v94 값은 sRGB 처럼 골라 놨다. 선형 0.26 은 sRGB 로 0.55 다 — 즉
//   "물가는 밝다" 가 아니라 **하늘색 페인트**였다. 화면 실측(tools/color_contract.py):
//
//       W_SHALLOW  화면 #a6c3cb  S 18.5%  V 79.7%
//       W_MID      화면 #89b1c0  S 28.8%  V 75.3%
//       W_DEEP     화면 #5a8daa  S 46.8%  V 66.5%
//
//   셋의 명도 폭이 13pt 뿐이라 4단 계단이 **한 색으로 뭉친다.** 게다가 셋 다
//   ACES 하이라이트 구간(V 66~80%)이라 채도가 씻겨서 "단색 시안 리본"이 된다.
//   심사가 1/10 을 준 그 그림이 여기서 나왔다.
//   롤 실물 강물을 같은 자로 재면 V 15~43% · S 38~65% 다(g_scuttle · riot_jungle).
// ★그래서 화면 목표를 먼저 정하고 거꾸로 풀었다. 명도 폭 34 -> 56 (22pt) 이고
//   깊을수록 **어둡고 더 파랗다**(롤의 구조). 밝기는 오너의 "밝은 판타지" 쪽으로
//   롤보다 한 단 올려 뒀다.
const W_SHALLOW = [0.094, 0.217, 0.194];   // 화면 #5c8f88  물가·얕은 여울
const W_MID = [0.055, 0.131, 0.153];       // 화면 #3a6a75
const W_DEEP = [0.029, 0.072, 0.100];      // 화면 #1f4557  한복판
// 포말. 선형 0.90 은 화면 V 88.5% 짜리 **흰 페인트**였다. 0.46 이면 V 80% 로
// 물빛과 대비는 살고 종이처럼 튀지는 않는다(실측 사다리로 골랐다).
const W_FOAM = [0.46, 0.56, 0.54];
const W_STEPS = 4.0;             // 깊이 계단 수. 3 은 띠가 굵고 6 이면 그라데이션이 된다
const W_FLOW = 0.085;            // 물살이 흐르는 속도(m/s 아니라 UV/s)
let WATER_N = 0;

// ---------------------------------------------------------------------------
// 던전 횃불 불꽃 (13차-불꽃. 오너 "불꽃이 그림처럼 멈춰 있네")
// ---------------------------------------------------------------------------
// 던전에 불이 49자루 서 있는데 전부 정지 스프라이트였다. 방이 통째로 박제로 읽힌다.
// 고치는 것은 셋이고, 셋 다 **한 재질 안**에서 한다(드로우콜 증가 0).
//   ① 플립북    tex/dg_flame_fb.png 넉 칸을 UV 로 갈아 끼운다 = 실루엣이 다시 그려진다
//   ② 미세 흔들림 빌보드 윗변만 좌우로 눕고(바람) 키가 숨 쉰다. 밑동은 안 움직인다
//   ③ 밝기 맥동  이미시브를 ±13%. 웜 풀은 **같은 위상**으로 ±5%(그래야 한 불로 읽힌다)
//
// ★24fps 칸으로 양자화한다. 이 게임의 이펙트 문법이 그것이다(참격 시트·먹 파열 전부
//   1/24 홀드다). 60fps 로 매끈하게 보간하면 3D 젤리가 되고, 칸으로 끊으면 작화가 된다.
// ★작화는 2칸 打ち(=12fps). 애니 관례이면서, 4칸 플립북이 한 바퀴 0.333초 =
//   관솔 흔들림의 실제 주기와 맞는다.
// ★위상은 **자리에서 뽑는다**(Math.random 금지). 새로고침마다 달라지면 재현이 안 되고,
//   같은 위상이면 마흔아홉 자루가 군무를 춘다 - 그게 오히려 더 가짜다.
const FLAME_TEX = './tex/dg_flame_fb.png';
const FLAME_N = 4.0;             // 플립북 칸 수(dungeon_tex.py FLIP_N 과 같아야 한다)
const FLAME_HOLD = 2.0;          // 24fps 칸 몇 개를 한 작화로 붙드는가. 2 = 12fps
const FLAME_SWAY = 0.055;        // 꼭대기 좌우 진폭(m). 불꽃 폭이 0.40~0.86m 라 이 정도면
                                 //   "바람에 눕는다"로 읽히고 그 위는 자리가 흔들려 보인다
const FLAME_RISE = 0.030;        // 키 숨쉬기(m). 좌우만 흔들면 깃발이 된다
const FLAME_PULSE = 0.13;        // 불꽃 밝기 맥동 ±13%
const POOL_PULSE = 0.05;         // 바닥 웜 풀 맥동 ±5%. ★더 주면 바닥이 깜빡여서 촌스럽다
let FLAME_N_PATCHED = 0;

let LV = null;                   // level1.json 원본
let ROOT = null;                 // 씬에 붙은 맵 그룹
let PROPS = null;                // web/props.js 모듈(소품 인스턴싱). 없으면 null
let FLOOR_Y = 0;                 // 맵 바닥 높이(0.02). 맵이 없으면 0

const BOXES = [];                // {x, z, hx, hz}
const CIRCLES = [];              // {x, z, r}
const PLATFORMS = [];            // 올라설 수 있는 낮은 단 {box|circle, top}
let CELLS = null;                // 격자 버킷: 각 칸이 [{...collider}, ...]
let GW = 0, GH = 0, GX0 = 0, GZ0 = 0;

// ---------------------------------------------------------------------------
// 로드
// ---------------------------------------------------------------------------
// search 는 index.html 이 쓰는 캐시버스팅 쿼리(?v=..)를 그대로 물려주기 위한 것이다.
// json·glb 도 같이 물려줘야 맵만 옛것이 남는 사고가 안 난다.
export function mapName(search) {
  // ★13차. 맵이 둘이 됐다. 기본은 **던전(level2)** 이고 `?map=field` 로 초원(level1)이다.
  //   초원 파일(level1.glb·json·s20_level1.py)은 한 글자도 안 바뀌었다 - 폴백이 그걸
  //   그대로 부른다. 값은 파일 이름이 되므로 아는 이름만 받는다(경로 주입 방지).
  const q = search === undefined ? location.search : search;
  const m = (new URLSearchParams(q).get('map') || '').toLowerCase();
  if (m === 'field' || m === 'level1') return 'level1';
  return 'level2';
}

export async function loadLevel(scene, search) {
  const q = search === undefined ? location.search : search;
  const base = mapName(q);
  const res = await fetch('./' + base + '.json' + q);
  if (!res.ok) throw new Error(base + '.json 을 못 읽었다: ' + res.status);
  LV = await res.json();
  FLOOR_Y = LV.floorY || 0;

  buildColliders();
  buildPlatforms();
  buildGrid();

  const glb = await new Promise((ok, bad) => {
    new GLTFLoader().load('./' + base + '.glb' + q, ok, undefined, bad);
  });
  ROOT = glb.scene;
  ROOT.traverse(o => {
    if (!o.isMesh) return;
    // 바닥은 그림자를 받기만 한다. 던지게 두면 자기 자신에게 얼룩이 생긴다.
    const isFloor = o.name.startsWith('FLOOR');
    o.receiveShadow = true;
    o.castShadow = !isFloor;
  });
  // 바닥에만 결을 얹는다. 실패해도 맵은 그대로 뜬다.
  // ★13차. 던전(level2)은 `floorLook: false` 다. 아래 결·타일·스플랫은 전부 **초원용**
  //   (풀·흙·마른 풀)이라 던전 바닥에 얹으면 돌바닥에 잔디가 낀다. 던전은 컨셉 아트에서
  //   잘라 온 판석 타일과 정점색(횃불)으로 이미 완성돼 있다.
  // ★13차B. 던전 바닥 메시 이름은 `FLOOR_DG` 다 - 즉 위 314행의 `startsWith('FLOOR')`에
  //   걸려 **그림자를 안 던진다**(1차는 DGFLOOR 라 바닥이 자기 자신에게 그림자를 던졌다).
  //   빛 데칼·달빛 샤프트·불꽃도 같은 이유로 FLOOR_ 로 짓는다. 이 줄이 먼저 걸러 주므로
  //   초원용 스플랫이 얹힐 걱정은 없다.
  DETAIL_N = (LV.floorLook === false) ? 0 : await applyFloorLook(ROOT, q);
  // 수면(WATER_STREAM)은 따로 짠다. 실패해도 v93 그림 그대로 뜬다(아래 주석).
  WATER_N = await applyWaterLook(ROOT, q);
  // 던전 횃불(FLOOR_FLAME · FLOOR_POOL)에 애니메이션을 건다. 초원에는 그 메시가
  // 아예 없으므로 한 줄도 안 돌고 0 을 돌려준다(초원 회귀 위험 0).
  FLAME_N_PATCHED = await applyFlameLook(ROOT, q);
  scene.add(ROOT);

  // ★소품 5종(바위·절벽바위·덤불·나무·수풀)은 이 glb 에 없다.
  //   web/props/<종류>.glb 를 한 벌씩 읽어 props.js 가 InstancedMesh 로 심는다.
  //   수풀만 구역별 메시(BUSH_01..16)로 심는데, 은신 연출이 그 이름을 찾기 때문이다.
  //   ★ROOT 밑에 붙인다(stealth.js 가 LV.root() 를 훑어 수풀을 찾는다).
  //   ★같은 쿼리로 부른다. 다른 URL 로 부르면 모듈 인스턴스가 갈린다.
  // ★13차. 던전(level2)은 props[] 가 비어 있다 - 모든 지오메트리가 glb 안에 있다.
  //   빈 채로 props.js 를 부르면 "props[] 가 없다"고 경고만 찍고 돌아온다. 평상 콘솔이
  //   비어 있어야 진짜 경고가 눈에 들어오므로, 심을 게 없으면 아예 안 부른다.
  if ((LV.props || []).length) {
    try {
      PROPS = await import('./props.js' + q);
      await PROPS.build(ROOT, LV, q, groundY);
    } catch (e) {
      // 소품이 없어도 맵과 충돌은 그대로 돈다. 게임이 안 뜨는 것보다는 낫다.
      console.error('[level] 소품을 못 심었다', e);
      PROPS = null;
    }
  }
  return LV;
}

// ---------------------------------------------------------------------------
// 지면 결 얹기
// ---------------------------------------------------------------------------
// ★바닥 메시만 골라야 한다. level1.glb 의 메시 이름은 FLOOR / COL_CLIFF / COL_ROCK /
//   DECO_MOSS / WATER_STREAM 식이다. 재질을 통으로 훑어 얹으면 절벽·바위·이끼까지
//   얼룩덜룩해진다. 이름으로 정확히 FLOOR 만 집는다(재질 이름은 MAT_FLOOR 하나뿐).
async function applyFloorLook(root, q) {
  const floors = [];
  root.traverse(o => { if (o.isMesh && o.name.startsWith('FLOOR')) floors.push(o); });
  if (!floors.length) { console.warn('[level] 바닥 메시(FLOOR)를 못 찾았다'); return 0; }

  // 실패해도 게임은 그대로 돈다(결만 없다). 그래서 reject 없이 null 로 받는다.
  const load = (url) => new Promise(ok => {
    new THREE.TextureLoader().load(url + q, t => ok(t), undefined, () => ok(null));
  });

  const tex = await load(DETAIL_TEX);
  if (!tex) { console.warn('[level] 지면 디테일 텍스처를 못 읽었다. 결 없이 간다'); return 0; }
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  // ★colorSpace 를 건드리지 않는다. 이건 색이 아니라 곱수다. sRGB 로 읽으면
  //   0.5 가 0.21 로 내려앉아 바닥이 통째로 새까매진다.
  tex.colorSpace = THREE.NoColorSpace;
  tex.anisotropy = 8;            // 기기 상한은 three 가 알아서 자른다
  tex.needsUpdate = true;

  // 타일 4장 + 스플랫맵. 하나라도 없으면 타일은 통째로 끄고 잔결만 얹는다
  // (게임이 안 뜨는 것보다 결이 덜한 게 낫다).
  const splatUrl = (LV && LV.splatmap) || SPLAT_TEX;
  const [splat, scatter, medal, ...tiles] = await Promise.all(
    [load(splatUrl), load(SCATTER_TEX), load(MED_TEX)].concat(TILES.map(t => load(t.file))));

  // ★메달리온은 **색**이다(곱수가 아니다). sRGB 로 읽어야 칠한 색이 화면에 나온다.
  //   알파에는 감마가 안 걸리므로 덮개는 그대로 산다(산포 겹과 같은 계약).
  // ★ClampToEdge 다. 아틀라스라 Repeat 이면 칸이 서로 샌다.
  if (medal) {
    medal.wrapS = medal.wrapT = THREE.ClampToEdgeWrapping;
    medal.colorSpace = THREE.SRGBColorSpace;
    medal.anisotropy = TILE_ANISO;
    medal.needsUpdate = true;
  } else {
    console.warn('[level] 메달리온 데칼을 못 읽었다. 그 겹 없이 간다');
  }

  // ★산포는 **색**이다(위의 넷과 달리 곱수가 아니다). sRGB 로 읽어야 화면에서
  //   칠한 색이 나온다. 알파에는 감마가 안 걸리므로 덮개는 그대로 산다.
  if (scatter) {
    scatter.wrapS = scatter.wrapT = THREE.RepeatWrapping;
    scatter.colorSpace = THREE.SRGBColorSpace;
    scatter.anisotropy = TILE_ANISO;
    scatter.needsUpdate = true;
  } else {
    console.warn('[level] 산포 디테일 텍스처를 못 읽었다. 그 겹 없이 간다');
  }

  let tile = null;
  if (splat && tiles.every(t => t)) {
    // ★스플랫맵은 색이 아니라 네 개의 가중치다. sRGB 로 읽으면 0.5 가 0.21 로
    //   내려앉아 섞이는 비율이 통째로 틀어진다(바닥이 뿌옇거나 어두워진다).
    splat.colorSpace = THREE.NoColorSpace;
    // ★flipY 를 끈다. s20 이 png 첫 줄에 z=+48(남쪽)을 넣었고, 아래 셰이더가
    //   v = (48 - z) / 96 으로 찍는다. 뒤집으면 남북이 통째로 바뀐다
    //   (여울목에 풀이 깔리고 초원에 박석이 깔린다).
    splat.flipY = false;
    splat.wrapS = splat.wrapT = THREE.ClampToEdgeWrapping;
    splat.anisotropy = 4;
    splat.needsUpdate = true;
    SPLAT_PIX = readPixels(splat.image);
    tile = TILES.map((cfg, i) => {
      const t = tiles[i];
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      // ★sRGB 로 읽지 않는다. 이 넷도 색이 아니라 **비율**이다(위 계약 참조).
      //   sRGB 로 읽으면 밉맵이 바이트를 평균낸 값과 셰이더가 감마를 푼 값이 서로
      //   달라져서, 멀어질수록 바닥이 7% 쯤 어두워진다. 날것으로 읽어야 평균이 정확히 맞다.
      t.colorSpace = THREE.NoColorSpace;
      t.anisotropy = TILE_ANISO;
      t.needsUpdate = true;
      // 평균색을 png 에서 직접 잰다. 밉맵 맨 끝(1x1)이 수렴하는 값과 정확히 같은 값이다
      const px = readPixels(t.image);
      const ref = px ? px.mean : cfg.ref;
      const a = cfg.deg * Math.PI / 180, k = 1 / cfg.period;
      return {
        tex: t,
        // 회전 x 축소를 한 덩이로 접은 2x2. 셰이더에서 gdRot(m, p) 로 쓴다
        m: new THREE.Vector4(Math.cos(a) * k, Math.sin(a) * k,
                             -Math.sin(a) * k, Math.cos(a) * k),
        inv: new THREE.Vector3(1 / Math.max(ref[0], 1e-3),
                               1 / Math.max(ref[1], 1e-3),
                               1 / Math.max(ref[2], 1e-3)),
        ref,
        measured: !!px,
      };
    });
  } else {
    console.warn('[level] 지면 타일/스플랫맵을 못 읽었다. 잔결만 얹는다');
  }

  let n = 0;
  for (const m of floors) {
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    for (const mat of mats) if (patchFloorMaterial(mat, tex, splat, tile, scatter, medal)) n++;
  }
  return n;
}

// 이미지의 픽셀을 캔버스로 뽑아 평균색까지 재 둔다.
// ★게임 로직이 아니라 **계약 검사**다. 타일의 평균색을 여기서 재기 때문에
//   타일을 다시 구워도 코드에 적힌 숫자를 고칠 일이 없다(어긋날 수가 없다).
function readPixels(img) {
  if (!img || !img.width) return null;
  try {
    const w = img.width | 0, h = img.height | 0;
    const cv = document.createElement('canvas');
    cv.width = w; cv.height = h;
    const cx = cv.getContext('2d', { willReadFrequently: true });
    cx.drawImage(img, 0, 0);
    const data = cx.getImageData(0, 0, w, h).data;
    let r = 0, g = 0, b = 0;
    for (let i = 0; i < data.length; i += 4) { r += data[i]; g += data[i + 1]; b += data[i + 2]; }
    const n = data.length / 4;
    return { w, h, data, mean: [r / n / 255, g / n / 255, b / n / 255] };
  } catch (e) {
    // 다른 출처에서 온 이미지면 캔버스가 오염돼서 읽을 수 없다. 대비책 값으로 간다
    console.warn('[level] 텍스처 픽셀을 못 읽었다. 적어 둔 평균색으로 간다', e);
    return null;
  }
}

function patchFloorMaterial(mat, tex, splat, tile, scatter, medal) {
  if (!mat || mat.userData.groundDetail) return false;
  mat.userData.groundDetail = true;
  const b = (LV && LV.bounds) || { minX: -48, maxX: 48, minZ: -48, maxZ: 48 };
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uGD = { value: tex };
    shader.uniforms.uGDFreq = { value: new THREE.Vector2(DETAIL_FINE, DETAIL_WIDE) };
    shader.uniforms.uGDGain = { value: DETAIL_GAIN };
    shader.uniforms.uGDWide = { value: DETAIL_WIDE_W };
    shader.uniforms.uGDClamp = { value: new THREE.Vector2(DETAIL_MIN, DETAIL_MAX) };
    shader.uniforms.uGDFade = { value: new THREE.Vector2(DETAIL_FADE0, DETAIL_FADE1) };
    // 전후 비교용 손잡이. gain·amt 를 0 으로 내리면 그 겹이 붙기 전 그림이 그대로
    // 나온다(재컴파일이 없으니 같은 프레임·같은 카메라로 두 장을 찍을 수 있다)
    mat.userData.gdShader = shader;

    // ★UV 를 안 쓴다. 바닥 UV 는 96m 한 장에 0..1 로 깔려 있어서 거기 곱하면
    //   주기가 미터가 아니라 맵 크기에 묶인다. **월드 좌표**로 재야 1.7m 가 1.7m 다.
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vGDW;')
      // project_vertex 다음이어야 한다. transformed(최종 정점 위치)가 그 앞에서 정해진다
      .replace('#include <project_vertex>',
               '#include <project_vertex>\n\tvGDW = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;');

    const head = [
      '#include <common>',
      'varying vec3 vGDW;',
      'uniform sampler2D uGD;',
      'uniform vec2 uGDFreq;',
      'uniform float uGDGain;',
      'uniform float uGDWide;',
      'uniform vec2 uGDClamp;',
      'uniform vec2 uGDFade;'];
    // ★map_fragment **다음**이어야 한다. 그 앞에서는 diffuseColor 가 아직 바닥
    //   텍스처를 안 먹은 흰색이라 곱해봐야 결이 안 생긴다.
    const body = [
      '#include <map_fragment>',
      '{',
      '  vec2 gdP = vGDW.xz;',
      '  vec2 gdQ = vec2( gdP.x * 0.80 - gdP.y * 0.60, gdP.x * 0.60 + gdP.y * 0.80 );',
      '  float gdF = texture2D( uGD, gdP * uGDFreq.x ).g - 0.5;',
      '  float gdW = texture2D( uGD, gdQ * uGDFreq.y + vec2( 0.37, 0.61 ) ).r - 0.5;'];

    if (tile) {
      shader.uniforms.uSplat = { value: splat };
      // (minX, maxZ, 1/폭, 1/깊이). u 는 동쪽으로, v 는 **북쪽으로** 증가한다
      shader.uniforms.uSplatBox = {
        value: new THREE.Vector4(b.minX, b.maxZ,
                                 1 / (b.maxX - b.minX), 1 / (b.maxZ - b.minZ)),
      };
      shader.uniforms.uTileAmt = { value: TILE_AMT };
      shader.uniforms.uTileClamp = { value: new THREE.Vector2(TILE_MIN, TILE_MAX) };
      shader.uniforms.uTileWarp = { value: TILE_WARP };
      for (let i = 0; i < 4; i++) {
        shader.uniforms['uT' + i] = { value: tile[i].tex };
        shader.uniforms['uTM' + i] = { value: tile[i].m };
        shader.uniforms['uTR' + i] = { value: tile[i].inv };
      }
      head.push(
        'uniform sampler2D uSplat;',
        'uniform vec4 uSplatBox;',
        'uniform sampler2D uT0;', 'uniform sampler2D uT1;',
        'uniform sampler2D uT2;', 'uniform sampler2D uT3;',
        'uniform vec4 uTM0;', 'uniform vec4 uTM1;', 'uniform vec4 uTM2;', 'uniform vec4 uTM3;',
        'uniform vec3 uTR0;', 'uniform vec3 uTR1;', 'uniform vec3 uTR2;', 'uniform vec3 uTR3;',
        'uniform float uTileAmt;',
        'uniform vec2 uTileClamp;',
        'uniform float uTileWarp;',
        // 회전과 축소를 한 덩이로 접어 둔 2x2 곱셈
        'vec2 gdRot( vec4 m, vec2 p ) { return vec2( m.x * p.x + m.y * p.y, m.z * p.x + m.w * p.y ); }');
      body.push(
        '  // ① 타일 스플랫. 가중치 넷으로 지면 네 장을 섞어 곱한다',
        '  vec2 gdS = vec2( ( gdP.x - uSplatBox.x ) * uSplatBox.z,',
        '                   ( uSplatBox.y - gdP.y ) * uSplatBox.w );',
        '  vec4 gdw = texture2D( uSplat, gdS );',
        '  // ★v96. 정규화 **전** 합이 "이 자리에 결을 얼마나 깔 것인가" 다.',
        '  //   s20 이 물칸에서 네 채널을 통째로 0.06 배로 줄여 놓는다. 그러면 개울',
        '  //   바닥에 박석 무늬가 안 깔린다(9차의 "강바닥 = 지면 텍스처 + 파란 필터").',
        '  //   합이 1 인 자리(맵의 대부분)는 clamp 가 1 로 붙잡으므로 전과 똑같다.',
        '  float gdStr = clamp( ( gdw.r + gdw.g + gdw.b + gdw.a ) * 1.35, 0.0, 1.0 );',
        '  gdw /= max( gdw.r + gdw.g + gdw.b + gdw.a, 1e-3 );',
        '  // 격자를 아주 완만하게 흔든다(15~19m 물결). ★텍스처로 밀면 안 된다.',
        '  //   UV 미분이 요동쳐서 밉·이방성 비용이 폭발한다(위 TILE_WARP 주석).',
        '  vec2 gdT = gdP + vec2( sin( gdP.y * 0.41 + 1.7 ), sin( gdP.x * 0.33 ) ) * uTileWarp;',
        '  vec3 gdTM = texture2D( uT0, gdRot( uTM0, gdT ) ).rgb * uTR0 * gdw.r',
        '            + texture2D( uT1, gdRot( uTM1, gdT ) ).rgb * uTR1 * gdw.g',
        '            + texture2D( uT2, gdRot( uTM2, gdT ) ).rgb * uTR2 * gdw.b',
        '            + texture2D( uT3, gdRot( uTM3, gdT ) ).rgb * uTR3 * gdw.a;',
        '  diffuseColor.rgb *= clamp( mix( vec3( 1.0 ), gdTM, uTileAmt * gdStr ),',
        '                             uTileClamp.x, uTileClamp.y );');

      // ── ★v97 ④ 메달리온 데칼 (위 MEDALLIONS 주석이 왜를 적었다) ──
      if (medal && MEDALLIONS.length) {
        shader.uniforms.uMed = { value: medal };
        // (cx, cz, cos/size, sin/size). 회전과 축소를 한 덩이로 접어 둔다
        shader.uniforms.uMedA = {
          value: MEDALLIONS.map(m => {
            const a = m.deg * Math.PI / 180, k = 1 / m.size;
            return new THREE.Vector4(m.x, m.z, Math.cos(a) * k, Math.sin(a) * k);
          }),
        };
        // (아틀라스 칸 번호, 세기)
        shader.uniforms.uMedB = {
          value: MEDALLIONS.map(m => new THREE.Vector2(m.cell, 1.0)),
        };
        shader.uniforms.uMedAmt = { value: MED_AMT };
        shader.uniforms.uMedRef = {
          value: new THREE.Vector3(1 / MED_REF_L, MED_SHADE_MIN, MED_SHADE_MAX),
        };
        head.push(
          '#define MED_N ' + MEDALLIONS.length,
          'uniform sampler2D uMed;',
          'uniform vec4 uMedA[ MED_N ];',
          'uniform vec2 uMedB[ MED_N ];',
          'uniform float uMedAmt;',
          'uniform vec3 uMedRef;');
        body.push(
          '  // ④ 메달리온 데칼. **월드 고정 · 비반복**. 명소마다 한 장씩 박혀 있다',
          '  //   ★조회를 한 번으로 묶는다: 자리들이 서로 안 겹치므로 uv 를 그냥 더하면',
          '  //     걸린 자리의 uv 하나만 남는다. 자리마다 texture2D 를 부르면 조회가',
          '  //     6배가 되는데, 그 비용은 바닥 **전 화소**가 낸다(데칼은 맵의 3% 인데도).',
          '  vec2 medUV = vec2( 0.0 );',
          '  float medW = 0.0;',
          '  for ( int mi = 0; mi < MED_N; mi++ ) {',
          '    vec4 mt = uMedA[ mi ];',
          '    // ★gdT(물결 먹인 좌표)가 아니라 gdP(순수 월드)를 쓴다. 물결을 먹이면',
          '    //   문양이 0.5m 씩 휘어서 동심원이 찌그러진다',
          '    vec2 md = gdP - mt.xy;',
          '    vec2 mq = vec2( mt.z * md.x + mt.w * md.y,',
          '                   -mt.w * md.x + mt.z * md.y ) + 0.5;',
          '    // ★가장자리를 **부드러운 창**으로 끈다. 칸 경계에서 uv 가 툭 끊기면',
          '    //   그 화소 사분면의 UV 미분이 폭발해 GPU 가 제일 거친 밉(=알파 평균 0.31)',
          '    //   을 물어서 경계선을 따라 희미한 점선이 생긴다. 창이 0 이면 안 보인다.',
          '    //   ★창은 **원**이어야 한다(사각이 아니라). 굽는 쪽(bake_medallion.py)의',
          '    //     RIM0/RIM1 이 원형 페이드라 사각 창을 쓰면 네 귀퉁이에 "알파는 0 인데',
          '    //     창은 열린" 띠가 남는다. 그 띠가 옆 데칼과 겹치면 uv 두 개가 더해져',
          '    //     아틀라스 한복판을 물어 엉뚱한 조각이 뜬다. 원이면 덮개가 정확히',
          '    //     반지름 0.498*size 짜리 원이라, 두 자리가 그 합보다 멀면 절대 안 겹친다',
          '    //     (level.medallions().overlap 이 그 규칙으로 검사한다).',
          '    float mm = length( mq - 0.5 );',
          '    float mw = 1.0 - smoothstep( 0.455, 0.498, mm );',
          '    medUV += mw * vec2( ( clamp( mq.x, 0.0, 1.0 ) + uMedB[ mi ].x ) * 0.5,',
          '                        clamp( mq.y, 0.0, 1.0 ) );',
          '    medW += mw;',
          '  }',
          '  medW = clamp( medW, 0.0, 1.0 );',
          '  vec4 medT = texture2D( uMed, medUV );',
          '  // ★매크로 볕·그늘을 지우지 않는다. 데칼은 곱수가 아니라 색이라 그냥 덮으면',
          '  //   2048 베이스컬러에 구워 둔 볕·그늘이 그 자리만 통째로 사라진다(= 스티커).',
          '  //   "여기가 기준보다 얼마나 밝은가" 만 뽑아서 곱한다.',
          '  float medL = dot( diffuseColor.rgb, vec3( 0.2126, 0.7152, 0.0722 ) );',
          '  float medS = clamp( medL * uMedRef.x, uMedRef.y, uMedRef.z );',
          '  diffuseColor.rgb = mix( diffuseColor.rgb, medT.rgb * medS,',
          '                          clamp( medT.a * medW * uMedAmt, 0.0, 1.0 ) );');
      }

      if (scatter) {
        shader.uniforms.uSC = { value: scatter };
        const sa = SCATTER_DEG * Math.PI / 180, sk = 1 / SCATTER_PERIOD;
        shader.uniforms.uSCM = {
          value: new THREE.Vector4(Math.cos(sa) * sk, Math.sin(sa) * sk,
                                   -Math.sin(sa) * sk, Math.cos(sa) * sk),
        };
        shader.uniforms.uSCAmt = { value: SCATTER_AMT };
        head.push('uniform sampler2D uSC;', 'uniform vec4 uSCM;', 'uniform float uSCAmt;');
        body.push(
          '  // ③ 산포 디테일. 꽃잎·자갈·낙엽·잔풀을 **덮어쓴다**(곱수가 아니다)',
          '  vec4 gdSC = texture2D( uSC, gdRot( uSCM, gdT ) );',
          '  // 저주파 덮개. ★텍스처를 또 읽지 않는다 — UV 미분이 요동쳐서 밉·이방성',
          '  //   비용이 폭발한다(위 TILE_WARP 주석과 같은 함정). sin 두 번이면 된다.',
          '  //   주기는 56m 와 69m 라 한 화면에 걸쳐 서서히 있다가 없다가 한다',
          '  float gdSL = 0.5 + 0.5 * sin( gdP.x * 0.113 + gdP.y * 0.077 + 1.3 )',
          '                         * sin( gdP.y * 0.091 - gdP.x * 0.061 + 2.7 );',
          '  // 풀·마른풀 자리에 제일 많고 흙·판석에도 조금(자갈·낙엽은 길에도 있다)',
          '  float gdSM = smoothstep( 0.36, 0.68, gdSL ) * gdStr',
          '             * ( 0.34 + 0.66 * clamp( gdw.r + gdw.a, 0.0, 1.0 ) );',
          '  diffuseColor.rgb = mix( diffuseColor.rgb, gdSC.rgb,',
          '                          clamp( gdSC.a * gdSM * uSCAmt, 0.0, 1.0 ) );');
      }
    }
    body.push(
      '  // ② 잔결. 멀면 뺀다(먼 바닥이 반짝이는 걸 막는다).',
      '  //    타일은 밉맵이 알아서 평균으로 수렴하므로 따로 안 뺀다',
      // cameraPosition 은 three 가 모든 재질에 기본으로 넣어주는 유니폼이다
      '  float gdFade = 1.0 - smoothstep( uGDFade.x, uGDFade.y, length( vGDW - cameraPosition ) );',
      '  float gdM = 1.0 + ( gdF + gdW * uGDWide ) * uGDGain * gdFade;',
      '  diffuseColor.rgb *= clamp( gdM, uGDClamp.x, uGDClamp.y );',
      '}');

    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', head.join('\n'))
      .replace('#include <map_fragment>', body.join('\n'));
  };
  // ★onBeforeCompile 만으로는 안 먹는다. three 는 재질 **파라미터**로 프로그램을
  //   캐시하는데, 그 키에 onBeforeCompile 이 안 들어간다. 같은 파라미터의 다른
  //   MeshStandardMaterial 이 먼저 컴파일해 둔 프로그램을 그대로 받아 쓰면 이 코드가
  //   통째로 무시된다(three 의 오래된 함정). 키를 손으로 갈라준다.
  // ★셰이더를 고치면 이 문자열도 같이 올려라. 안 올리면 옛 프로그램이 그대로 재활용된다.
  // ★셰이더를 고치면 이 문자열도 같이 올려라. 산포 겹이 붙고 안 붙고가 프로그램을
  //   가르므로 키에 같이 넣는다(안 그러면 산포 없는 프로그램이 재활용될 수 있다).
  // ★v97. 메달리온 겹이 붙고 안 붙고가 프로그램을 가르므로 키에 같이 넣는다.
  //   그리고 셰이더 문구를 고쳤으므로 버전을 올렸다(안 올리면 옛 프로그램이 재활용된다).
  mat.customProgramCacheKey = () => (tile
    ? 'floorSplat4' + (scatter ? 'sc' : '') + (medal && MEDALLIONS.length ? 'md' : '')
    : 'groundDetail1');
  mat.needsUpdate = true;
  return true;
}

// ---------------------------------------------------------------------------
// 개울 수면
// ---------------------------------------------------------------------------
async function applyWaterLook(root, q) {
  const water = [];
  root.traverse(o => { if (o.isMesh && o.name.startsWith('WATER')) water.push(o); });
  if (!water.length) return 0;

  const tex = await new Promise(ok => {
    new THREE.TextureLoader().load(WATER_TEX + q, t => ok(t), undefined, () => ok(null));
  });
  if (!tex) { console.warn('[level] 강바닥 텍스처를 못 읽었다. 수면은 그대로 간다'); return 0; }
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  // ★색이 아니라 데이터다(자갈 곱수 · 포말 마스크 · 물살 마스크).
  //   sRGB 로 읽으면 평균 0.5 가 0.21 로 내려앉아 강바닥이 통째로 어두워진다.
  tex.colorSpace = THREE.NoColorSpace;
  tex.anisotropy = 4;
  tex.needsUpdate = true;

  let n = 0;
  for (const m of water) {
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    for (const mat of mats) if (patchWaterMaterial(m, mat, tex)) n++;
  }
  return n;
}

function patchWaterMaterial(mesh, mat, tex) {
  if (!mat || mat.userData.waterLook) return false;
  mat.userData.waterLook = true;
  const uT = { value: 0 };
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uWB = { value: tex };
    shader.uniforms.uWT = uT;
    shader.uniforms.uWK = { value: 1 / WATER_PERIOD };
    shader.uniforms.uWShallow = { value: new THREE.Vector3().fromArray(W_SHALLOW) };
    shader.uniforms.uWMid = { value: new THREE.Vector3().fromArray(W_MID) };
    shader.uniforms.uWDeep = { value: new THREE.Vector3().fromArray(W_DEEP) };
    shader.uniforms.uWFoam = { value: new THREE.Vector3().fromArray(W_FOAM) };
    shader.uniforms.uWSteps = { value: W_STEPS };
    shader.uniforms.uWFlow = { value: W_FLOW };
    mat.userData.wShader = shader;

    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWW;\nvarying vec2 vWUV;')
      .replace('#include <project_vertex>',
               '#include <project_vertex>\n\tvWW = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;\n\tvWUV = uv;');

    const head = [
      '#include <common>',
      'varying vec3 vWW;',
      'varying vec2 vWUV;',
      'uniform sampler2D uWB;',
      'uniform float uWT;',
      'uniform float uWK;',
      'uniform vec3 uWShallow;',
      'uniform vec3 uWMid;',
      'uniform vec3 uWDeep;',
      'uniform vec3 uWFoam;',
      'uniform float uWSteps;',
      'uniform float uWFlow;'].join('\n');

    // ★color_fragment **다음**에 넣는다. 그 앞이면 three 가 vColor 를 곱하면서
    //   우리가 정한 색을 덮어쓴다. 여기서는 diffuseColor 를 통째로 다시 쓴다.
    // ★주석에 역따옴표(`)를 쓰지 마라 — 이 파일이 템플릿 리터럴로 조립되던 시절의
    //   함정이 LOG.md 에 기록돼 있다. 배열 join 으로 짜는 이유이기도 하다.
    const body = [
      '#include <color_fragment>',
      '{',
      '  vec2 wp = vWW.xz * uWK;',
      '  float wd = clamp( vWUV.y, 0.0, 1.0 );          // 0 기슭 -> 1 중심',
      '  vec3 wtex = texture2D( uWB, wp ).rgb;',
      '  // 흐름. 강은 동서로 흐르므로 x 로만 민다. 두 겹을 다른 속도로 흘려',
      '  // 되풀이가 눈에 안 잡히게 한다',
      '  float f1 = texture2D( uWB, wp * vec2( 0.55, 1.30 ) + vec2( -uWT * uWFlow, 0.0 ) ).b;',
      '  float f2 = texture2D( uWB, wp * vec2( 0.31, 0.90 ) + vec2( -uWT * uWFlow * 0.55, 0.13 ) ).b;',
      '  float flow = f1 * 0.62 + f2 * 0.38;',
      '  // ① 깊이 계단. 흐름으로 경계를 흔들어 자로 그은 띠가 안 되게 한다',
      '  float dep = clamp( wd * 1.06 + ( flow - 0.5 ) * 0.20, 0.0, 1.0 );',
      '  dep = floor( dep * uWSteps ) / ( uWSteps - 1.0 );',
      '  dep = clamp( dep, 0.0, 1.0 );',
      '  vec3 col = dep < 0.5 ? mix( uWShallow, uWMid, dep * 2.0 )',
      '                       : mix( uWMid, uWDeep, ( dep - 0.5 ) * 2.0 );',
      '  // ② 강바닥. 얕을수록 세게 비친다(깊으면 안 보인다)',
      '  //    ★v96. 물빛을 어둡게 내리면서 같은 곱수가 화면에서 더 작게 보이게 됐다',
      '  //    (감마 때문에 어두운 쪽에서 sRGB 단계가 촘촘하다). 세기를 올려 되돌린다',
      '  float bedAmt = ( 1.0 - smoothstep( 0.10, 0.72, wd ) ) * 0.92;',
      '  col *= 1.0 + ( wtex.r - 0.5 ) * 3.1 * bedAmt;',
      '  // ④ 물살 결. 깊은 쪽에만 얹는다(물가는 포말이 주역이다)',
      '  //    ★더하는 색이 얕은물빛인데 그게 어두워졌으므로 세기를 같이 올린다.',
      '  //    이 띠가 "물이 움직인다" 는 유일한 신호다 — 안 보이면 웅덩이가 된다',
      '  float band = smoothstep( 0.58, 0.78, flow ) * smoothstep( 0.18, 0.55, wd );',
      '  col += uWShallow * band * 0.55;',
      '  // ⑤ 젖은 림. 물가 바로 안쪽을 짙게 눌러 뭍과의 경계를 만든다',
      '  col *= 1.0 - ( 1.0 - smoothstep( 0.0, 0.20, wd ) ) * 0.26;',
      '  // ③ 포말. 물가 선을 따라 흰 거품. 노이즈로 뜯고 천천히 찰랑인다',
      '  float lap = 0.5 + 0.5 * sin( vWW.x * 1.7 + uWT * 1.15 );',
      '  // 띠 폭. 넓으면 흰 리본이 되고 좁으면 물가 선이 된다. 0.16 은 넓었다',
      '  float edge = 1.0 - smoothstep( 0.015, 0.085 + lap * 0.055, wd );',
      '  // 노이즈 주기를 3.2/4.6 = 0.70m 로 잡는다. 화면에서 덩어리 하나가 약 20px 이라',
      '  //   폭 15px 짜리 포말 띠가 그 안에서 끊겼다 이어졌다 한다(1.9 로 두면 덩어리가',
      '  //   40~60px 이라 띠가 통짜 흰 리본으로 읽혔다 — 첫 판이 그랬다).',
      '  float fnz = texture2D( uWB, wp * 4.6 + vec2( -uWT * 0.055, uWT * 0.020 ) ).g;',
      '  // 문턱을 높게 잡아야 거품이 통짜 띠가 아니라 **덩어리**로 끊긴다.',
      '  //   0.42 로 두면 물가 화소의 58%가 흰색이라 자로 그은 흰 줄이 된다(첫 판이 그랬다).',
      '  float foam = edge * step( 0.56 + ( 1.0 - edge ) * 0.40, fnz );',
      '  // 물가 맨 바깥 한 줄만은 끊기지 않게 얇게 이어 준다(파도가 닿는 선).',
      '  // ★자리가 물가가 아니라 물 한복판이라 **선을 긋지 않는다.** 끊어진 잔물결만 남긴다',
      '  foam *= 0.55;',
      '  // 거품 바깥 한 줄은 더 희게(마루). 안쪽은 성기게 부서진다',
      '  col = mix( col, uWFoam, clamp( foam, 0.0, 1.0 ) * 0.86 );',
      '  diffuseColor.rgb = col;',
      '}'].join('\n');

    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', head)
      .replace('#include <color_fragment>', body);
  };
  // ★three 는 재질 파라미터로 프로그램을 캐시하는데 그 키에 onBeforeCompile 이
  //   안 들어간다. 손으로 갈라 준다. ★셰이더를 고치면 이 문자열도 같이 올려라.
  mat.customProgramCacheKey = () => 'waterLook7';   // 셰이더를 고쳤으면 이 숫자를 올린다
  mat.needsUpdate = true;
  // ★시간. 그려지기 직전에만 갱신된다 = 탭이 숨으면 안 돈다.
  mesh.onBeforeRender = () => { uT.value = performance.now() * 0.001; };
  return true;
}

// ---------------------------------------------------------------------------
// 던전 횃불 불꽃 (플립북 + 흔들림 + 맥동)
// ---------------------------------------------------------------------------
// 초원 맵에는 FLOOR_FLAME 이 없다 = 아래가 통째로 안 돈다(초원 회귀 위험 0).
async function applyFlameLook(root, q) {
  let flame = null;
  let pool = null;
  let halo = null;          // 13차C. 불꽃 뒤 후광
  let wglow = null;         // 13차C. 벽을 타고 오르는 자국
  let poolc = null;         // 달빛 웅덩이(맥동 없음. 합성만 가산으로)
  root.traverse(o => {
    if (!o.isMesh) return;
    if (o.name === 'FLOOR_FLAME') flame = o;
    else if (o.name === 'FLOOR_POOL') pool = o;
    else if (o.name === 'FLOOR_HALO') halo = o;
    else if (o.name === 'FLOOR_WGLOW') wglow = o;
    else if (o.name === 'FLOOR_POOLC') poolc = o;
  });
  if (!flame) return 0;

  // ★그리는 차례를 못 박는다(13차C). 바닥 위에 겹치는 판이 다섯 겹이나 되고
  //   전부 depthWrite=false 라, 차례를 안 정하면 three 가 카메라 거리로 정렬한다 —
  //   거의 같은 높이의 큰 판들이라 그 순서가 프레임마다 뒤집혀 깜빡인다.
  //   돌(마모) -> 무늬(메달리온) -> 빛(웜 풀·후광·벽 자국) -> 불꽃. 물리 순서 그대로다.
  const ORDER = { FLOOR_WEAR: 1, FLOOR_MEDAL: 2, FLOOR_POOL: 3, FLOOR_POOLC: 3,
                  FLOOR_WGLOW: 4, FLOOR_HALO: 5, FLOOR_SHAFT: 5, FLOOR_DUST: 6,
                  FLOOR_FLAME: 7 };
  root.traverse(o => {
    if (o.isMesh && ORDER[o.name] !== undefined) o.renderOrder = ORDER[o.name];
  });

  // 플립북 스트립. 못 읽어도 게임은 그대로 돈다 - 칸 수를 1 로 떨어뜨리면 UV 는
  // 손대지 않은 것과 같아지고 흔들림·맥동만 남는다(정지 그림보다는 낫다).
  const tex = await new Promise(ok => {
    new THREE.TextureLoader().load(FLAME_TEX + q, t => ok(t), undefined, () => ok(null));
  });
  let frames = 1.0;
  if (tex) {
    // ★이건 **색**이다(곱수가 아니다). glb 안의 원본도 sRGB 로 들어와 있으므로
    //   여기만 선형으로 읽으면 불꽃이 통째로 어두워진다.
    tex.colorSpace = THREE.SRGBColorSpace;
    // ★★flipY 를 끈다. TextureLoader 는 기본이 true 인데 GLTFLoader 가 넣어 준
    //   원본은 false 다(glTF 규격은 UV 원점이 그림 좌상단). 이걸 안 맞추면 갈아
    //   끼우는 순간 불꽃이 **위아래로 뒤집혀서** 흰 심지가 하늘에 뜬다.
    tex.flipY = false;
    // ★스트립이라 반드시 ClampToEdge 다. Repeat 이면 칸이 서로 샌다.
    tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.anisotropy = 4;
    tex.needsUpdate = true;
    frames = FLAME_N;
  } else {
    console.warn('[level] 불꽃 플립북을 못 읽었다. 흔들림·맥동만 건다');
  }

  const cards = splitCards(flame.geometry);
  if (!cards) { console.warn('[level] 불꽃 메시가 인덱스 없이 들어왔다'); return 0; }

  // 카드 -> 불꽃 묶기. 한 자루는 십자로 선 카드 **두 장**이라 자리가 같다.
  // 두 장이 다른 위상을 받으면 한 자루가 서로 다른 칸을 그려서 X 자로 갈라진다.
  const seats = [];
  for (const c of cards) {
    let s = null;
    for (const t of seats) {
      const dx = t.x - c.x, dz = t.z - c.z;
      if (dx * dx + dz * dz < 0.0025) { s = t; break; }     // 5cm 안이면 같은 자루
    }
    if (!s) { s = { x: c.x, z: c.z, ph: seatPhase(c.x, c.z) }; seats.push(s); }
    c.ph = s.ph;
  }

  const uT = { value: 0 };
  let n = 0;
  for (const mat of matList(flame)) if (patchFlameMaterial(flame, mat, tex, frames, uT)) n++;
  setCardAttr(flame.geometry, cards);

  // 바닥 웜 풀 · 불꽃 후광 · 벽 자국. **불꽃과 같은 위상**이어야 한 불로 읽힌다.
  // ★자리가 정확히 같지는 않다 - 벽 횃불은 불꽃이 벽에서 0.24m, 웅덩이가 0.34m 다
  //   (s40_dungeon1.py 참조). 그래서 좌표를 맞추지 않고 **가장 가까운 자루**를 찾는다.
  for (const m of [pool, halo, wglow]) {
    if (!m) continue;
    const pc = splitCards(m.geometry);
    if (!pc) continue;
    for (const c of pc) {
      let best = 0, bd = Infinity;
      for (const s of seats) {
        const dx = s.x - c.x, dz = s.z - c.z;
        const d = dx * dx + dz * dz;
        if (d < bd) { bd = d; best = s.ph; }
      }
      c.ph = best;
    }
    for (const mat of matList(m)) if (patchPoolMaterial(m, mat, uT)) n++;
    setCardAttr(m.geometry, pc);
  }
  // 달빛 웅덩이는 **맥동을 안 건다**(달은 안 흔들린다). 합성만 가산으로 바꾼다.
  if (poolc) for (const mat of matList(poolc)) if (makeAdditive(mat)) n++;
  return n;
}

// ---------------------------------------------------------------------------
// 빛을 **더한다** (13차C. 오너 "주변 밝아지는 효과는 왜 이리 이상하냐")
// ---------------------------------------------------------------------------
// ★★이 게임에서 웜 풀이 스티커로 읽힌 진짜 원인은 모양이 아니라 **합성 방식**이었다.
//   glTF 는 alphaMode 가 OPAQUE / MASK / BLEND 셋뿐이라 데칼이 BLEND 로 들어온다.
//   BLEND 는 `결과 = 빛 x a + 바닥 x (1 - a)` 다 — 알파 0.52 짜리 웜 풀을 깔면
//   **바닥돌의 52%가 지워진다.** 실제로 옛 화면에서 웅덩이 안쪽 판석 무늬가
//   통째로 사라져 있었고, 그래서 빛이 아니라 물감 자국으로 보였다.
//   빛은 더해지는 것이지 덮는 것이 아니다:  `결과 = 바닥 + 빛 x a`.
// ★가산으로 바꾸면 알파는 '얼마나 가리는가'가 아니라 '얼마나 더하는가'가 된다.
//   그래서 굽는 쪽(tools/dungeon_tex.py)에서 알파 상한을 올려도 돌이 안 지워진다.
// ★depthWrite 는 이미 false 다(익스포터가 BLEND 에 그렇게 적는다). 가산에서는
//   반드시 false 여야 한다 - 켜 두면 뒤에 그려질 웅덩이가 서로를 잘라낸다.
// ★블룸 임계(1.02)는 s40 의 이미시브 세기가 지킨다(후광 0.63 · 벽 자국 0.26).
//   여기서 세기를 올리면 안 된다.
function makeAdditive(mat) {
  if (!mat || mat.userData.dgAdd) return false;
  mat.userData.dgAdd = true;
  mat.blending = THREE.AdditiveBlending;
  mat.transparent = true;
  mat.depthWrite = false;
  // ★가산이면 뒤에 있는 빛이 앞의 빛을 못 지운다 = 정렬이 필요 없다. 다만 바닥
  //   데칼끼리 z-fighting 이 나면 깜빡이므로 polygonOffset 으로 확실히 띄운다.
  mat.polygonOffset = true;
  mat.polygonOffsetFactor = -2;
  mat.polygonOffsetUnits = -2;
  mat.needsUpdate = true;
  return true;
}

function matList(mesh) {
  return Array.isArray(mesh.material) ? mesh.material : [mesh.material];
}

// 자리에서 뽑는 결정론 위상(0..1). ★Math.random 금지 — 새로고침마다 달라지면
// 재현이 안 되고, 무엇보다 카드 두 장이 서로 다른 값을 받아 한 자루가 갈라진다.
function seatPhase(x, z) {
  const s = Math.sin(x * 12.9898 + z * 78.233) * 43758.5453;
  return s - Math.floor(s);
}

// 메시 하나에 합쳐진 카드(사각형 한 장)를 잇기로 가른다.
// ★왜 이걸 런타임에 하는가: 불꽃 마흔아홉 자루가 드로우콜 하나로 구워져 있어서
//   자루마다 다른 값을 주려면 정점 속성이 필요한데 glb 에는 없다. glb 를 다시 굽지
//   않는 이유는 그 파일이 4.78MB 로 상한(5MB)에 붙어 있어서다. 정점이 392개뿐이라
//   로드 때 한 번 도는 비용은 재는 게 무의미하다.
function splitCards(geo) {
  const pos = geo.attributes.position;
  const idx = geo.index;
  if (!pos || !idx) return null;
  const n = pos.count;
  const par = new Int32Array(n);
  for (let i = 0; i < n; i++) par[i] = i;
  const find = (a) => { while (par[a] !== a) { par[a] = par[par[a]]; a = par[a]; } return a; };
  const uni = (a, b) => { a = find(a); b = find(b); if (a !== b) par[b] = a; };
  for (let t = 0; t + 2 < idx.count; t += 3) {
    const a = idx.getX(t);
    uni(a, idx.getX(t + 1));
    uni(a, idx.getX(t + 2));
  }
  const bag = new Map();
  for (let i = 0; i < n; i++) {
    const r = find(i);
    let g = bag.get(r);
    if (!g) { g = []; bag.set(r, g); }
    g.push(i);
  }
  const cards = [];
  bag.forEach(g => {
    let cx = 0, cz = 0, y0 = Infinity, y1 = -Infinity;
    for (const i of g) {
      cx += pos.getX(i);
      cz += pos.getZ(i);
      const y = pos.getY(i);
      if (y < y0) y0 = y;
      if (y > y1) y1 = y;
    }
    cards.push({ v: g, x: cx / g.length, z: cz / g.length, y0, y1, ph: 0 });
  });
  return cards;
}

// aFlame = (위상, 밑동0..끝1, 카드의 가로 방향 x, 같은 z)
function setCardAttr(geo, cards) {
  const pos = geo.attributes.position;
  const a = new Float32Array(pos.count * 4);
  for (const c of cards) {
    const h = Math.max(1e-4, c.y1 - c.y0);
    // 카드가 선 평면의 가로축. 중심에서 가장 멀리 나간 정점이 곧 그 방향이다.
    // ★이 방향으로만 밀어야 빌보드가 제 평면 안에서 눕는다(가로로 밀면 종잇장이 돈다).
    let tx = 0, tz = 0, best = 0;
    for (const i of c.v) {
      const dx = pos.getX(i) - c.x, dz = pos.getZ(i) - c.z;
      const d = dx * dx + dz * dz;
      if (d > best) { best = d; tx = dx; tz = dz; }
    }
    const L = Math.sqrt(best) || 1;
    tx /= L; tz /= L;
    for (const i of c.v) {
      a[i * 4] = c.ph;
      a[i * 4 + 1] = (pos.getY(i) - c.y0) / h;
      a[i * 4 + 2] = tx;
      a[i * 4 + 3] = tz;
    }
  }
  geo.setAttribute('aFlame', new THREE.BufferAttribute(a, 4));
}

// 24fps 칸 · 12fps 작화 · 위상. 불꽃과 웜 풀이 **같은 식**을 써야 한 불로 읽힌다.
const FLAME_HEAD = [
  'attribute vec4 aFlame;',      // x 위상 / y 밑동0..끝1 / zw 카드의 가로 방향
  'uniform float uFT;',
  'varying float vFPul;'];
const FLAME_PULSE_LINE = (k) => [
  '  float fq = floor( uFT * 24.0 );',            // ★24fps 칸(게임 전체 이펙트 문법)
  '  float ft = fq / 24.0;',
  '  float ph = aFlame.x * 6.2831853;',
  // 두 주기를 겹친다. 하나면 규칙적인 사인파라 "숨쉰다"가 아니라 "깜빡인다"가 된다
  '  vFPul = 1.0 + ' + k + ' * ( sin( ft * 5.1 + ph * 3.3 ) * 0.62'
      + ' + sin( ft * 8.7 + ph ) * 0.38 );'];

function patchFlameMaterial(mesh, mat, tex, frames, uT) {
  if (!mat || mat.userData.flameLook) return false;
  mat.userData.flameLook = true;
  // glb 안의 한 장짜리 그림을 스트립으로 갈아 끼운다(재질·드로우콜은 그대로다).
  if (tex) {
    if (mat.map) mat.map = tex;
    if (mat.emissiveMap) mat.emissiveMap = tex;
  }
  const hasMap = !!mat.map;
  const hasEm = !!mat.emissiveMap;
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uFT = uT;
    shader.uniforms.uFN = { value: frames };
    shader.uniforms.uFHold = { value: FLAME_HOLD };
    shader.uniforms.uFSway = { value: FLAME_SWAY };
    shader.uniforms.uFRise = { value: FLAME_RISE };
    shader.uniforms.uFPulse = { value: FLAME_PULSE };
    mat.userData.fShader = shader;

    const uv = [
      '#include <uv_vertex>',
      '{',
      '  // 24fps 칸으로 끊고, 그 위에서 두 칸씩 붙들어 12fps 작화로 넘긴다(2칸 打ち).',
      '  // ★자루마다 시간을 통째로 밀어 둔다(칸 단위). 그림 번호만 다르게 하면 마흔여덟',
      '  //   자루가 **같은 순간에 동시에** 다음 장으로 넘어가서 군무로 읽힌다 -',
      '  //   밀어 두면 넘어가는 순간까지 갈린다(2칸 打ち라 홀·짝이 반씩 나뉜다).',
      '  float ffq = floor( uFT * 24.0 ) + floor( aFlame.x * uFN * uFHold );',
      '  float fi = mod( floor( ffq / uFHold ), uFN );'];
    if (hasMap) uv.push('  vMapUv.x = ( vMapUv.x + fi ) / uFN;');
    if (hasEm) uv.push('  vEmissiveMapUv.x = ( vEmissiveMapUv.x + fi ) / uFN;');
    uv.push('}');

    // ★주석에 역따옴표(`)를 쓰지 마라 - LOG.md 의 함정이다(배열 join 으로 짜는 이유).
    const body = [
      '#include <begin_vertex>',
      '{'].concat(FLAME_PULSE_LINE('uFPulse')).concat([
      '  // 바람. **윗변만** 눕는다(up 을 제곱해서 밑동은 심지에 못 박아 둔다).',
      '  //   빠른 결을 겹쳐야 "펄럭"이 아니라 "일렁"으로 읽힌다',
      '  float sw = sin( ft * 2.7 + ph ) * 0.66 + sin( ft * 4.3 + ph * 2.1 ) * 0.34;',
      '  float up = aFlame.y;',
      '  transformed.xz += aFlame.zw * ( sw * uFSway * up * up );',
      '  // 키. 좌우로만 흔들면 깃발이 된다. 위로 한 번씩 솟아야 불이다',
      '  transformed.y += ( sin( ft * 3.3 + ph * 1.7 ) * 0.5 + 0.5 ) * uFRise * up;',
      '}']).join('\n');

    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', ['#include <common>'].concat(FLAME_HEAD).concat([
        'uniform float uFN;',
        'uniform float uFHold;',
        'uniform float uFSway;',
        'uniform float uFRise;',
        'uniform float uFPulse;']).join('\n'))
      .replace('#include <uv_vertex>', uv.join('\n'))
      .replace('#include <begin_vertex>', body);

    // 밝기 맥동. 이 재질은 베이스컬러가 검정이라 화면에 나오는 건 이미시브뿐이다.
    // ★세기를 3 넘게 올리면 ACES 가 흰색으로 말아 올려 주황이 씻긴다(LOG.md).
    //   원래 2.4 이므로 +13% 는 2.71 - 그 선 아래다.
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vFPul;')
      .replace('#include <emissivemap_fragment>',
               '#include <emissivemap_fragment>\n\ttotalEmissiveRadiance *= vFPul;');
  };
  // ★three 는 재질 파라미터로 프로그램을 캐시하는데 그 키에 onBeforeCompile 이
  //   안 들어간다. 손으로 갈라 준다. ★셰이더를 고치면 이 숫자를 같이 올려라.
  mat.customProgramCacheKey = () => 'dgFlame1';
  mat.needsUpdate = true;
  mesh.onBeforeRender = () => { uT.value = performance.now() * 0.001; };
  return true;
}

function patchPoolMaterial(mesh, mat, uT) {
  if (!mat || mat.userData.flameLook) return false;
  mat.userData.flameLook = true;
  // ★13차C. 맥동보다 **이게** 먼저다 - 합성이 알파 블렌딩인 한 어떤 모양을 구워도
  //   빛이 바닥을 지운다(위 makeAdditive 주석에 이유가 다 적혀 있다).
  makeAdditive(mat);
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uFT = uT;
    shader.uniforms.uFPulse = { value: POOL_PULSE };
    mat.userData.fShader = shader;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', ['#include <common>'].concat(FLAME_HEAD)
        .concat(['uniform float uFPulse;']).join('\n'))
      .replace('#include <begin_vertex>', ['#include <begin_vertex>', '{']
        .concat(FLAME_PULSE_LINE('uFPulse')).concat(['}']).join('\n'));
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vFPul;')
      .replace('#include <emissivemap_fragment>',
               '#include <emissivemap_fragment>\n\ttotalEmissiveRadiance *= vFPul;');
  };
  mat.customProgramCacheKey = () => 'dgPool1';
  mat.needsUpdate = true;
  mesh.onBeforeRender = () => { uT.value = performance.now() * 0.001; };
  return true;
}

export function data() { return LV; }
export function ready() { return !!LV; }
export function root() { return ROOT; }
export function props() { return PROPS; }
export function floorY() { return FLOOR_Y; }

// ---------------------------------------------------------------------------
// 충돌 자료 만들기
// ---------------------------------------------------------------------------
function buildColliders() {
  BOXES.length = 0;
  CIRCLES.length = 0;
  for (const c of (LV.colliders || [])) {
    if (c.type === 'circle') CIRCLES.push({ x: c.x, z: c.z, r: c.r, tag: c.tag });
    else BOXES.push({ x: c.x, z: c.z, hx: c.hx, hz: c.hz, tag: c.tag });
  }
}

// 올라설 수 있는 낮은 단.
// ★colliders[] 에는 안 들어 있다. 무릎(0.6m)보다 낮은 건 "막지 않는다"가 맵 규칙이라
//   기단·제단·탈출 계단은 충돌에서 빠졌는데, 그러면 발이 그 두께만큼 묻힌다.
//   그래서 **높이 전용 목록**을 따로 둔다. 숫자는 level1.json 의 platforms[] 에서
//   읽고(블렌더 s20_level1.py 가 같은 값을 뽑아 넣는다), 없으면 그냥 평지로 본다.
function buildPlatforms() {
  PLATFORMS.length = 0;
  for (const p of (LV.platforms || [])) {
    if (p.type === 'circle') PLATFORMS.push({ circle: true, x: p.x, z: p.z, r: p.r, top: p.top });
    else PLATFORMS.push({ circle: false, x: p.x, z: p.z, hx: p.hx, hz: p.hz, top: p.top });
  }
}

// 균일 격자. 102개면 전부 훑어도 되지만, 요괴 40마리가 매 프레임 질의하면
// 4천 번이 된다. 칸을 나누면 한 번에 보통 0~4개만 본다.
function buildGrid() {
  const b = LV.bounds;
  GX0 = b.minX; GZ0 = b.minZ;
  GW = Math.ceil((b.maxX - b.minX) / GCELL);
  GH = Math.ceil((b.maxZ - b.minZ) / GCELL);
  CELLS = new Array(GW * GH);
  const put = (c, minX, minZ, maxX, maxZ) => {
    // ★AABB 를 에이전트 최대 반경만큼 부풀려 넣는다. 이렇게 해 두면 "점이 든 칸"만
    //   봐도 그 점 반경 안에 걸리는 벽을 하나도 안 놓친다(경계 칸 누락 방지).
    const c0 = clampi(Math.floor((minX - AGENT_MAX_R - GX0) / GCELL), 0, GW - 1);
    const c1 = clampi(Math.floor((maxX + AGENT_MAX_R - GX0) / GCELL), 0, GW - 1);
    const r0 = clampi(Math.floor((minZ - AGENT_MAX_R - GZ0) / GCELL), 0, GH - 1);
    const r1 = clampi(Math.floor((maxZ + AGENT_MAX_R - GZ0) / GCELL), 0, GH - 1);
    for (let r = r0; r <= r1; r++) {
      for (let cc = c0; cc <= c1; cc++) {
        const k = r * GW + cc;
        (CELLS[k] || (CELLS[k] = [])).push(c);
      }
    }
  };
  for (const c of BOXES) put(c, c.x - c.hx, c.z - c.hz, c.x + c.hx, c.z + c.hz);
  for (const c of CIRCLES) { c.isCircle = true; put(c, c.x - c.r, c.z - c.r, c.x + c.r, c.z + c.r); }
}

const clampi = (v, a, b) => (v < a ? a : (v > b ? b : v));

function bucket(x, z) {
  if (!CELLS) return null;
  const c = Math.floor((x - GX0) / GCELL), r = Math.floor((z - GZ0) / GCELL);
  if (c < 0 || r < 0 || c >= GW || r >= GH) return null;
  return CELLS[r * GW + c] || null;
}

// ---------------------------------------------------------------------------
// 한 개짜리 밀어내기
// ---------------------------------------------------------------------------
const _hit = { x: 0, z: 0 };

// 원(p, r) 대 축정렬 박스. 모서리에서는 원 대 점으로, 면에서는 최소 축으로 민다.
// 면에서 축으로 미는 게 곧 '미끄러짐'이다: 밀려나는 방향이 벽 법선이라
// 벽과 나란한 성분은 하나도 안 깎인다.
function pushBox(c, px, pz, r) {
  const dx = px - c.x, dz = pz - c.z;
  const ax = Math.abs(dx) - c.hx;     // 면까지 남은 거리. 음수면 그 축으로는 안쪽
  const az = Math.abs(dz) - c.hz;
  if (ax >= r || az >= r) return false;
  const sx = dx < 0 ? -1 : 1, sz = dz < 0 ? -1 : 1;
  if (ax > 0 && az > 0) {
    const d = Math.sqrt(ax * ax + az * az);
    if (d >= r) return false;                     // 모서리 바깥의 둥근 여백
    const k = (r - d) / (d || 1e-6);
    _hit.x = px + sx * ax * k;
    _hit.z = pz + sz * az * k;
  } else if (r - ax < r - az) {                   // 파고든 깊이가 얕은 축으로 뺀다
    _hit.x = px + sx * (r - ax);
    _hit.z = pz;
  } else {
    _hit.x = px;
    _hit.z = pz + sz * (r - az);
  }
  return true;
}

function pushCircle(c, px, pz, r) {
  const dx = px - c.x, dz = pz - c.z;
  const rr = c.r + r;
  const d2 = dx * dx + dz * dz;
  if (d2 >= rr * rr) return false;
  const d = Math.sqrt(d2);
  if (d < 1e-6) { _hit.x = px + rr; _hit.z = pz; return true; }   // 정확히 중심일 때
  const k = rr / d;
  _hit.x = c.x + dx * k;
  _hit.z = c.z + dz * k;
  return true;
}

// ---------------------------------------------------------------------------
// 밖으로 밀어내기 / 미끄러지며 이동
// ---------------------------------------------------------------------------
const _out = { x: 0, z: 0, hit: false };

// 지금 자리가 벽 속이면 가장 가까운 밖으로 뺀다. 스폰 자리 보정에 쓴다.
export function pushOut(x, z, r, out) {
  const o = out || _out;
  o.x = x; o.z = z; o.hit = false;
  if (!LV) return o;
  resolve(o, r);
  clampBounds(o, r);
  return o;
}

// (x,z) 에서 (dx,dz) 만큼 가려다 벽을 만나면 미끄러진다.
// out 을 재사용하므로 반환값을 보관하지 말고 바로 읽을 것(매 프레임 객체 생성 금지).
export function slide(x, z, dx, dz, r, out) {
  const o = out || _out;
  o.x = x + dx; o.z = z + dz; o.hit = false;
  if (!LV) return o;
  resolve(o, r);
  clampBounds(o, r);
  return o;
}

// 벽을 하나 빠져나오면 다른 벽에 걸릴 수 있다(모서리·문 기둥 사이). 몇 번만 반복한다.
// ★무한 반복 금지. 두 벽 사이에 끼면 영원히 진동한다. 3회면 실사용에서 남는 침범이
//   밀리미터 단위고, 남아도 다음 프레임에 마저 빠져나온다.
function resolve(o, r) {
  const rr = r > AGENT_MAX_R ? AGENT_MAX_R : r;
  for (let it = 0; it < 3; it++) {
    const list = bucket(o.x, o.z);
    if (!list) return;
    let moved = false;
    for (let i = 0; i < list.length; i++) {
      const c = list[i];
      const got = c.isCircle ? pushCircle(c, o.x, o.z, rr) : pushBox(c, o.x, o.z, rr);
      if (got) { o.x = _hit.x; o.z = _hit.z; moved = true; o.hit = true; }
    }
    if (!moved) return;
  }
}

// 성벽이 맵을 둘러싸고 있어서 보통은 여기까지 안 온다. 문틈으로 새는 걸 막는 최후의 벽.
function clampBounds(o, r) {
  const b = LV.bounds;
  if (o.x < b.minX + r) o.x = b.minX + r; else if (o.x > b.maxX - r) o.x = b.maxX - r;
  if (o.z < b.minZ + r) o.z = b.minZ + r; else if (o.z > b.maxZ - r) o.z = b.maxZ - r;
}

// 이 자리에 반경 r 로 설 수 있는가(검증·배치용).
export function blocked(x, z, r) {
  if (!LV) return false;
  const list = bucket(x, z);
  if (!list) return false;
  const rr = r > AGENT_MAX_R ? AGENT_MAX_R : r;
  for (let i = 0; i < list.length; i++) {
    const c = list[i];
    if (c.isCircle ? pushCircle(c, x, z, rr) : pushBox(c, x, z, rr)) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// 지면 높이
// ---------------------------------------------------------------------------
// ★완전한 지형 추종이 아니다. 맵에서 올라설 수 있는 건 20cm 대웅전 단, 24cm 보스
//   제단, 22cm 탈출 계단 셋뿐이라 그 셋만 목록으로 본다. 그 외는 전부 평지(0.02)다.
//   비탈·2층이 생기면 그때 제대로 만든다.
export function groundY(x, z) {
  if (!LV) return 0;
  let y = FLOOR_Y;
  for (let i = 0; i < PLATFORMS.length; i++) {
    const p = PLATFORMS[i];
    if (p.top <= y) continue;
    if (p.circle) {
      const dx = x - p.x, dz = z - p.z;
      if (dx * dx + dz * dz > p.r * p.r) continue;
    } else if (Math.abs(x - p.x) > p.hx || Math.abs(z - p.z) > p.hz) continue;
    y = p.top;
  }
  return y;
}

// ---------------------------------------------------------------------------
// 지점 (스폰·무리·탈출)
// ---------------------------------------------------------------------------
export function spawns() { return (LV && LV.spawns) || []; }
export function mobs() { return (LV && LV.mobs) || []; }
export function exits() { return (LV && LV.exits) || []; }

// n 번째 스폰 지점. 없으면 원점.
export function spawnPoint(i) {
  const s = spawns();
  if (!s.length) return { x: 0, y: 0, z: 0, yaw: 0 };
  const p = s[((i | 0) % s.length + s.length) % s.length];
  return { x: p.x, y: groundY(p.x, p.z), z: p.z, yaw: p.yaw || 0 };
}

// 검증용. 콘솔에서 충돌·지면을 바로 찍어볼 수 있게 열어둔다.
export const debug = {
  counts: () => ({ box: BOXES.length, circle: CIRCLES.length, platform: PLATFORMS.length }),
  // 한 점에서 여러 방향으로 밀어 보고 어디에 막히는지 본다
  probe(x, z, dx, dz, r = PLAYER_RADIUS) {
    const o = slide(x, z, dx, dz, r, { x: 0, z: 0, hit: false });
    return { to: [+o.x.toFixed(3), +o.z.toFixed(3)], hit: o.hit,
             moved: +Math.hypot(o.x - x, o.z - z).toFixed(3) };
  },
  groundY,
  blocked,
  props: () => (PROPS ? PROPS.debug : null),
  // 지면 결이 실제로 붙었는지. 붙은 재질 수와 셰이더에 문구가 박혔는지 본다
  detail() {
    const out = { patched: DETAIL_N, meshes: [], injected: 0, tex: null,
                  tiles: 0, splat: false, refs: [] };
    if (!ROOT) return out;
    ROOT.traverse(o => {
      if (!o.isMesh) return;
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) {
        if (!m || !m.userData.groundDetail) continue;
        out.meshes.push(o.name);
        // gdShader 가 있다 = onBeforeCompile 이 실제로 돌았다(캐시 키 함정을 통과했다)
        const sh = m.userData.gdShader;
        if (!sh) continue;
        if (sh.fragmentShader.indexOf('uGDGain') >= 0 && sh.vertexShader.indexOf('vGDW') >= 0) out.injected++;
        out.gain = sh.uniforms.uGDGain.value;
        out.tex = !!sh.uniforms.uGD.value;
        out.splat = !!(sh.uniforms.uSplat && sh.uniforms.uSplat.value);
        out.amt = sh.uniforms.uTileAmt ? sh.uniforms.uTileAmt.value : 0;
        out.tiles = 0;
        out.refs = [];
        for (let i = 0; i < 4; i++) {
          const u = sh.uniforms['uT' + i], r = sh.uniforms['uTR' + i];
          if (u && u.value) out.tiles++;
          // 잰 평균색(=곱수의 기준). 1/x 로 들고 있으니 되돌려 보여준다
          if (r && r.value) out.refs.push([+(1 / r.value.x).toFixed(4),
                                           +(1 / r.value.y).toFixed(4),
                                           +(1 / r.value.z).toFixed(4)]);
        }
        // 셰이더 조회 수. 예산(기존 3 + 5)을 넘겼는지 바로 센다
        out.fetches = (sh.fragmentShader.match(/texture2D\s*\(/g) || []).length;
      }
    });
    return out;
  },
  // 전후 비교용. 인자 없이 부르면 원래 값으로 되돌린다
  detailGain(v) {
    return setFloorUniform('uGDGain', v === undefined ? DETAIL_GAIN : v);
  },
  // 타일 스플랫만 껐다 켠다. 0 이면 v81 까지의 그림(베이스컬러 x 잔결)이 그대로 나온다
  tileAmt(v) {
    return setFloorUniform('uTileAmt', v === undefined ? TILE_AMT : v);
  },
  // ★v97. 메달리온 데칼만 껐다 켠다(전후 비교·fps 교대 측정용).
  //   재컴파일이 없으니 같은 프레임·같은 카메라로 두 장을 찍을 수 있다
  medAmt(v) {
    return setFloorUniform('uMedAmt', v === undefined ? MED_AMT : v);
  },
  // 메달리온이 실제로 붙었는지 + **자리가 서로 안 겹치는지**를 여기서 증명한다.
  // 겹치면 셰이더가 uv 를 더하는 최적화가 깨져 엉뚱한 자리를 문다(위 주석 참조).
  medallions() {
    const out = { n: MEDALLIONS.length, tex: false, injected: 0, fetches: 0,
                  list: MEDALLIONS.map(m => ({ x: m.x, z: m.z, size: m.size,
                                               deg: m.deg, cell: m.cell,
                                               dia: +(m.size * 0.68).toFixed(2) })),
                  overlap: [] };
    for (let i = 0; i < MEDALLIONS.length; i++) {
      for (let j = i + 1; j < MEDALLIONS.length; j++) {
        const a = MEDALLIONS[i], b = MEDALLIONS[j];
        const d = Math.hypot(a.x - b.x, a.z - b.z);
        // 덮개는 반지름 0.498*size 짜리 **원**이다(셰이더의 원형 창 = 굽기의 RIM1).
        // 두 원이 안 닿으면 uv 합산 최적화가 안전하다
        const need = (a.size + b.size) * 0.498;
        if (d < need) out.overlap.push({ i, j, d: +d.toFixed(2), need: +need.toFixed(2) });
      }
    }
    if (!ROOT) return out;
    ROOT.traverse(o => {
      if (!o.isMesh) return;
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) {
        const sh = m && m.userData.gdShader;
        if (!sh || !sh.uniforms.uMed) continue;
        out.tex = !!sh.uniforms.uMed.value;
        out.amt = sh.uniforms.uMedAmt.value;
        if (sh.fragmentShader.indexOf('uMedA[') >= 0) out.injected++;
        out.fetches = (sh.fragmentShader.match(/texture2D\s*\(/g) || []).length;
      }
    });
    return out;
  },
  // 수면 셰이더가 실제로 붙었는지. 붙은 재질 수 · 조회 수 · 시간이 도는지 본다
  water() {
    const out = { patched: WATER_N, meshes: [], injected: 0, tex: false,
                  fetches: 0, t: 0, uvRange: null };
    if (!ROOT) return out;
    ROOT.traverse(o => {
      if (!o.isMesh || !o.name.startsWith('WATER')) return;
      out.meshes.push(o.name);
      const uv = o.geometry.getAttribute('uv');
      if (uv) {
        let v0 = 9e9, v1 = -9e9, u0 = 9e9, u1 = -9e9;
        for (let i = 0; i < uv.count; i++) {
          const u = uv.getX(i), v = uv.getY(i);
          if (u < u0) u0 = u; if (u > u1) u1 = u;
          if (v < v0) v0 = v; if (v > v1) v1 = v;
        }
        out.uvRange = { u: [+u0.toFixed(2), +u1.toFixed(2)],
                        v: [+v0.toFixed(2), +v1.toFixed(2)] };
      }
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) {
        const sh = m && m.userData.wShader;
        if (!sh) continue;
        if (sh.fragmentShader.indexOf('uWSteps') >= 0
            && sh.vertexShader.indexOf('vWUV') >= 0) out.injected++;
        out.tex = !!sh.uniforms.uWB.value;
        out.t = +sh.uniforms.uWT.value.toFixed(2);
        out.fetches = (sh.fragmentShader.match(/texture2D\s*\(/g) || []).length;
      }
    });
    return out;
  },
  // 던전 불꽃이 실제로 살아 있는지. **지금 이 순간** 자루마다 몇 번 칸을 그리는지까지
  // 돌려준다 - 연속 캡처와 대조하면 "옆 횃불과 위상이 다른가"를 눈이 아니라 수로 잰다.
  flame() {
    const out = { patched: FLAME_N_PATCHED, meshes: [], injected: 0, frames: 0,
                  t: 0, seats: 0, cards: 0, phases: [], frameNow: [], pool: 0,
                  halo: 0, wglow: 0, additive: 0 };
    if (!ROOT) return out;
    const seen = new Map();
    // 가산으로 갈아탄 재질 수(13차C). 이게 0 이면 빛이 다시 바닥을 지우고 있다는 뜻이다
    ROOT.traverse(o => {
      if (!o.isMesh) return;
      for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
        if (m && m.blending === THREE.AdditiveBlending) out.additive++;
      }
    });
    ROOT.traverse(o => {
      if (!o.isMesh) return;
      const a = o.geometry.getAttribute('aFlame');
      if (!a) return;
      out.meshes.push(o.name);
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) {
        const sh = m && m.userData.fShader;
        if (!sh) continue;
        if (sh.vertexShader.indexOf('aFlame') >= 0
            && sh.fragmentShader.indexOf('vFPul') >= 0) out.injected++;
        out.t = +sh.uniforms.uFT.value.toFixed(2);
        if (sh.uniforms.uFN) out.frames = sh.uniforms.uFN.value;
      }
      // ★위상 표는 **불꽃 자루**를 세는 것이다. 웜 풀·후광·벽 자국은 그 위상을
      //   물려받은 종속물이라 같이 세면 자루 수가 부풀어 검증이 거짓말을 한다.
      if (o.name === 'FLOOR_POOL') { out.pool = a.count; return; }
      if (o.name === 'FLOOR_HALO') { out.halo = a.count; return; }
      if (o.name === 'FLOOR_WGLOW') { out.wglow = a.count; return; }
      for (let i = 0; i < a.count; i++) {
        const p = +a.getX(i).toFixed(4);
        if (!seen.has(p)) seen.set(p, 0);
        seen.set(p, seen.get(p) + 1);
      }
    });
    out.cards = 0;
    seen.forEach(v => { out.cards += v; });
    out.seats = seen.size;
    out.phases = Array.from(seen.keys()).sort((a, b) => a - b);
    // 지금 그려지는 칸 번호. 셰이더와 **똑같은 식**이라야 대조가 성립한다
    const nf = out.frames || 1;
    out.frameNow = out.phases.map(p => Math.floor(
      (Math.floor(out.t * 24) + Math.floor(p * nf * FLAME_HOLD)) / FLAME_HOLD) % nf);
    return out;
  },
  // 이 자리에 어떤 결이 깔렸나. 셰이더와 **같은 식**으로 스플랫맵을 되짚는다.
  // 남북이 뒤집혔는지(flipY 함정)를 브라우저에서 바로 잡아내는 창구다.
  splatAt(x, z) {
    if (!SPLAT_PIX || !LV) return null;
    const b = LV.bounds;
    const u = (x - b.minX) / (b.maxX - b.minX);
    const v = (b.maxZ - z) / (b.maxZ - b.minZ);
    const j = Math.max(0, Math.min(SPLAT_PIX.w - 1, Math.floor(u * SPLAT_PIX.w)));
    const i = Math.max(0, Math.min(SPLAT_PIX.h - 1, Math.floor(v * SPLAT_PIX.h)));
    const k = (i * SPLAT_PIX.w + j) * 4;
    const d = SPLAT_PIX.data;
    const s = (d[k] + d[k + 1] + d[k + 2] + d[k + 3]) || 1;
    const w = { grass: +(d[k] / s).toFixed(3), dirt: +(d[k + 1] / s).toFixed(3),
                stone: +(d[k + 2] / s).toFixed(3), dry: +(d[k + 3] / s).toFixed(3) };
    // 같은 자리의 칸 종류도 같이 준다. 결과 칸이 어긋나면 좌표가 밀린 것이다
    const cell = LV.cell || 3.2;
    const c = Math.floor((x - b.minX) / cell), r = Math.floor((z - b.minZ) / cell);
    const row = LV.grid && LV.grid[r];
    w.cell = [c, r];
    w.grid = row ? row[c] : null;
    w.top = ['grass', 'dirt', 'stone', 'dry'].reduce((a, k2) => (w[k2] > w[a] ? k2 : a));
    return w;
  },
};

// 바닥 재질 전부의 유니폼 하나를 같은 값으로 맞춘다(전후 비교용).
// ★재컴파일이 없다. 그래서 같은 프레임·같은 카메라로 두 장을 찍을 수 있다.
function setFloorUniform(name, v) {
  if (!ROOT) return null;
  let n = 0;
  ROOT.traverse(o => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      const sh = m && m.userData.gdShader;
      if (sh && sh.uniforms[name]) { sh.uniforms[name].value = v; n++; }
    }
  });
  return n ? v : null;
}
