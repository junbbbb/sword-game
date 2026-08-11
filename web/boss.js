// ---------------------------------------------------------------------------
// web/boss.js — 층의 이름 있는 요괴 / 증표 / 탈출
//
// 이 파일이 붙기 전까지 게임에는 **끝이 없었다.** 잡몹만 무한히 잡을 수 있었다.
// 여기서 한 층을 "깨는" 루프를 닫는다.
//
//   보스 마당 진입 → 보스전 → 증표 낙하 → 줍기 → 탈출구까지 반출 → 클리어
//
// ★핵심 설계(docs/game-design.md): **죽이는 것만으로는 기록이 안 된다.**
//   막타만으로 확정하면 20분 작업을 한 대에 뺏겨서 재미가 아니라 화가 난다.
//   증표를 든 사람은 위치가 노출되고, 탈출구까지 들고 나가야 확정이다.
//   솔로에서도 "잡고 끝"이 아니라 **"들고 살아 나가기"**라는 마지막 긴장이 남는다.
//
// 구조 원칙
//  1. main.js 는 2,086줄, enemy.js 는 1,161줄이다. 보스 로직은 전부 여기 둔다.
//     main.js 가 하는 일은 createBossSystem() 한 번과 update() 한 줄이 전부다.
//  2. **새 히트박스를 만들지 않는다.** main.js 의 measureBlade() 가 실측한 칼날
//     선분(swordA=코등이 / swordB=칼끝)을 그대로 받는다. 스윙 번호(중복 타격 방지)도
//     enemy.js 가 이미 히스테리시스로 뽑고 있으므로 그 결과를 넘겨받아 쓴다.
//     여기서 임계값을 다시 정의하면 "잡몹은 맞는데 보스는 안 맞는" 날이 반드시 온다.
//  3. 외형은 **boss.glb**(Meshy 각귀, 15,040 삼각형 / 뼈 24 / 2048 텍스처)다.
//     예전에는 요괴 덩어리(enemy.js buildYokaiGeometry)를 2.6배로 키워 빨갛게 칠한
//     임시 덩어리였다. 지금은 그걸 **로드 실패 시 폴백**으로만 남긴다.
//     ★갈아끼운 것은 겉뿐이다. 판정 구(중심 y 1.65 / 반경 1.43)·패턴 3종·예고 시간·
//       데미지·리쉬·증표는 한 글자도 안 건드렸다. 아래 '판정 상수' 절을 볼 것.
//  4. 모듈 로딩은 main.js·enemy.js 와 **같은 쿼리**로. URL 이 한 글자라도 다르면
//     브라우저가 별개 모듈로 올려서 서로 다른 맵 인스턴스를 보게 된다.
// ---------------------------------------------------------------------------
import * as THREE from './lib/three.module.js';
import { GLTFLoader } from './lib/GLTFLoader.js';
const LV = await import('./level.js' + location.search);
// ★폴백(boss.glb 로드 실패) 전용. 모델이 정상이면 여기서 아무것도 안 쓴다.
//   보스가 통째로 안 보이는 것보다는 옛 덩어리라도 서 있는 편이 낫다.
const EN = await import('./enemy.js' + location.search);
// 이 파일이 내는 **정보성** 로그는 전부 이 게이트를 지난다(에러·경고는 항상 낸다).
const DEV = typeof location !== 'undefined' && location.search.includes('dev');

// ---------------------------------------------------------------------------
// 수치 (전부 근거를 적는다. 근거 없는 숫자는 다음 사람이 못 고친다)
// ---------------------------------------------------------------------------

// ── 판정 상수 (★외형을 갈아끼워도 절대 안 바뀌는 값) ──
// 아래 네 줄은 임시 덩어리 시절의 수식 그대로다. 값을 유지하려고 식까지 남겼다.
// 여기를 손대면 "잡몹은 맞는데 보스는 안 맞는" 날이 온다.
//
// ★잡몹은 HOVER_Y 0.62 로 띄워져 있다. 검사 칼끝이 높이 1.20~2.48 을 지나가서
//   바닥에 두면 한 대도 안 맞았기 때문이다(enemy.js 주석의 실측).
//   보스는 몸이 2.6배라 같은 0.62 를 쓰면 아랫자락이 허공에 62cm 떠서 우스워진다.
//   0.35 로 낮춰도 **몸통 중심이 0.35 + 0.50*2.6 = 1.65m** 라 칼끝 구간(1.20~2.48)
//   한복판이다. 판정 구(반경 1.43)는 y 0.22~3.08 을 덮는다. 칼이 확실히 닿는다.
// ★진짜 모델은 발이 땅에 붙으므로 HOVER 는 **폴백 덩어리 전용**으로만 남았다.
//   판정 중심 1.65 는 그대로 쓴다. 키 3.0m 짜리 몸의 55% 지점이라 배꼽 언저리고,
//   반경 1.43 구가 y 0.22~3.08 = 발끝부터 뿔 끝까지를 그대로 덮는다.
const SCALE = 2.6;                  // 폴백 덩어리 배율 + 아래 두 식의 계수
const HOVER = 0.35;                 // 폴백 덩어리 부양(모델에는 안 쓴다)
const BODY_CY = 0.50;               // enemy.js 와 같은 로컬 몸통 중심
const CENTER_Y = HOVER + BODY_CY * SCALE;   // = 1.65
// 판정 구 반경. 잡몹은 0.60*scale 로 뿔·자락까지 넉넉히 덮는데, 보스는 그대로 쓰면
// 1.56m 라 허공을 베도 맞는다. 0.55 로 살짝 조인다(= 1.43m, 몸통 실루엣과 거의 같다).
const HIT_R = 0.55 * SCALE;                 // = 1.43

// ── 외형(모델) ──
// 키 3.0m 로 정규화한다. 기준은 **바인드 박스**(three.js Box3 가 스키닝 안 먹은
// 상태로 재는 값 = 1.700). 배율 3.0/1.700 = 1.7647.
// ★클립 포즈로 재면 안 된다. 각귀는 웅크린 도깨비라 클립마다 키가 다르다
//   (Idle 1.56 / Walk 1.75 / Attack 2.25 모델단위). 클립 기준으로 정규화하면
//   걸을 때마다 몸이 커졌다 작아진다.
// ★그래서 **실제 화면에 서 있는 높이는 2.6~2.8m** 다(브라우저에서 스키닝을 먹여 실측:
//   Idle 2.61~2.76 / 예고 2.84). 웅크린 자세라 3.0 을 다 안 쓴다.
//   플레이어 1.75 의 약 1.6배, 잡몹 고블린 1.30 의 약 2.1배로 보인다.
// 판정 구가 y 0.22~3.08 을 덮으므로 이 키가 구 안에 통째로 들어앉는다.
// 더 키우면 고정 쿼터뷰 화면(가로 21m)에서 보스 하나가 화면을 먹어 예고 범위를 못 읽고,
// 정수리가 판정 구 위(3.08)를 뚫어 "머리를 베도 안 맞는" 자리가 생긴다.
const VIS_H = 3.0;
// 발밑 그림자 반경. 임시 덩어리 때(SCALE*0.6 = 1.56)와 같은 크기로 맞췄다.
const SHADOW_R = VIS_H * 0.52;
// ── 접지 발 속도(재생속도 계산용) ──
// enemy.js 가 고블린에서 실측한 값(키 1.30 기준 Walk 0.80 / Run 2.35)을 키로 환산했다.
// 보스 클립은 고블린과 **같은 Meshy 원본**이라(walk 32프레임 / run 20프레임 일치)
// 프레임 구성이 같고, 발 속도는 키에 비례한다.
// ★재생속도 = 이동속도 / 이 값. 이래야 발이 안 미끄러진다(스케이트 방지).
const WALK_FOOT = 0.80 * (VIS_H / 1.30);    // = 1.846 m/s
const RUN_FOOT = 2.35 * (VIS_H / 1.30);     // = 5.423 m/s
// ── 공격 클립 창 ──
// Attack 클립은 85프레임(2.80초)인데 앞 7프레임은 준비 자세, 35프레임 뒤로는
// 회복 꼬리다. enemy.js 가 같은 클립에서 손 속도를 프레임마다 재서 **33프레임이
// 타격 순간**임을 확인했다. 예고가 끝나는 그 프레임에 피해가 들어가므로(fire),
// 타격 8프레임 전부터 틀어 칼과 판정이 눈으로 맞물리게 한다.
// 남은 꼬리는 경직(rec 1.30~1.80초) 동안 그대로 흐른다 = 회복 동작이 공짜로 붙는다.
const ATK_START_T = 25 / 30;        // 26번째 프레임(0-based 25)
const ATK_TS = 1.45;

// ── 체력 ──
// 잡몹 졸개 1, 정예 2, 두목 3 이 **스윙 수**다(한 스윙 = 1 감소).
// 보스는 두목의 20배로 잡는다. 3연타 한 사이클(약 1.6초)에 3~5 가 들어가므로
// 실제로는 12~20 스윙, 회피 시간을 끼면 **40~70초짜리 싸움**이 된다.
// 100초를 넘기면 프로토타입에서 지루하고, 20초 밑이면 패턴 3개를 다 못 본다.
const MAX_HP = 60;
const HIT_DMG = 3;                  // Z 3연타 한 대
const HEAVY_DMG = 5;                // 수면참(X)·횡일섬(C). 모으는 만큼 값어치가 있어야 한다

// ── 이동 ──
// ★플레이어보다 느려야 한다. 안 그러면 "도망친다"가 선택지에서 사라지고 리쉬가
//   장식이 된다. 6종 중 제일 느린 탱커 달리기가 2.20 이라 그보다 낮은 2.10 을 쓴다.
//   느린 보스가 심심하지 않은 이유는 돌진(9m 를 0.75초에)이 그 간격을 지우기 때문이다.
const SPEED = 2.10;
// 벽 충돌 반경. level.js 가 어차피 AGENT_MAX_R(0.75)로 자른다. 보스 몸이 1.4m 라
// 기둥에 살짝 겹쳐 보이지만, 크게 잡으면 마당 기둥 사이에 통째로 낀다.
const BODY_R = 0.75;

// ── 아레나 / 리쉬 ──
// 아레나는 맵이 정한다(level1.json boss.arena, x±19.2 z -35.2..-12.8 = 38x22m).
// 여유 3.0m 를 벗어나면 리쉬. 문턱에서 반 발짝 왔다갔다 할 때 전투가 켜졌다 꺼졌다
// 하지 않을 만큼은 두껍고, 도망 한 번이 확실히 리쉬가 될 만큼은 얇다.
const LEASH_MARGIN = 3.0;
// 귀환 중 회복. 60hp 를 6초에 채운다. **도망은 리셋**이라는 게 분명해야 한다.
// 이보다 느리면 "조금 나갔다 들어와서 회복 끊기"가 정석 공략이 된다.
const HEAL_RATE = 10.0;

// ── 패턴 ──
// ★예고(telegraph)가 없으면 게임이 아니라 주사위다. 예고 시간은 눈대중이 아니라
//   **제일 느린 캐릭터가 실제로 빠져나올 수 있는 시간**에서 역산했다.
//   재료: 단순 시각 반응 0.25초 + (빠져나갈 거리 / 이동속도).
//   이동속도는 6종 중 최저인 탱커 달리기 2.20 을 기준으로 잡는다.
//
// ★★브라우저에서 실측하고 나서 전부 다시 계산한 값이다.
//   **베는 동안에는 못 움직인다.** main.js 의 moving 조건이 `&& !attacking` 이고,
//   검사 Attack 클립이 1.60초 / 재생속도 1.35 라 **한 번 베면 1.19초 묶인다**
//   (실측 1194ms). 처음엔 0.74초쯤으로 어림잡고 예고를 짰는데, 그 상태로 봇을
//   붙였더니 52초 동안 98 피해를 다 맞았다. 예고를 못 본 게 아니라 **묶여 있었다.**
//
//   그래서 규칙을 이렇게 정한다.
//     · 예고 시간은 "칼을 안 휘두르고 있던 사람"이 반응해서 피할 수 있게 잡는다.
//     · "휘두르는 중이면 못 피한다"는 벌로 남긴다. 그게 공격을 거는 값이다.
//     · 대신 **경직(rec)을 칼 묶임 1.19초보다 길게** 둔다. 경직이 시작되자마자
//       한 대 넣으면 다음 예고가 뜨기 전에 반드시 풀리도록.
//       경직이 1.19 보다 짧으면 "한 대도 못 넣거나, 넣으면 무조건 맞거나" 둘뿐이다.
//
// 1) 후려치기 — 앞쪽 부채꼴. 싸고 잦다. 얼굴 앞에서 딜만 넣는 걸 벌준다.
//    플레이어는 보스 중심에서 약 2.8m(판정구 1.43 + 칼 사거리 1.4)에 서서 때린다.
//    반경 3.4 밖으로 나가려면 **뒤로 0.6m**. 탱커 달리기 0.27초 + 반응 0.25 = 0.52.
//    ★옆으로는 못 피한다(부채꼴이 ±45도라 옆걸음은 안에 남는다). "뒤로 빠져라"가
//      이 패턴의 정답이고, 그래서 제일 자주 나오고 제일 안 아프다.
//    경직 1.30 = 칼 묶임 1.19 + 다시 붙는 0.19(0.6m / 3.2). 경직 시작에 한 대 넣으면
//    다음 예고가 뜨기 전에 정확히 풀린다.
//
// ★★9차 재조정 (건틀릿 1회차 손맛 7번: 11트라이 0킬)
//   고치기 전에 실측부터 했다(headed, 아레나에 서서 가만히 있기, 게임시계 기준).
//     100 -> 80  charge 20     (t=1.3)
//      80 -> 52  slam   28     (t=4.6)   <- **첫 두 대 합이 48.** 심사관이 적은 그 숫자다
//      52 -> 38  swipe  14
//      ... 100 -> 0 이 19.4초
//   예고 시간 자체는 설계값 그대로였다(charge 1.10 / slam 1.20 / swipe 0.80 게임초,
//   실측 오차 0.00). "예고가 7초씩 걸린다"는 관측은 **벽시계 착시**였다 - 로드 직후
//   구간은 게임시계가 벽시계의 0.15~0.6배로 흘러서 1.10초가 7.35초로 보인다.
//   (LOG.md 함정: 게임시계와 벽시계를 반드시 구분할 것)
//
//   그래서 손댈 곳은 두 군데다.
//     · 피해량: 첫 두 대 48 -> 31. 한 대 최대 28 -> 18.
//     · 예고: "제일 느린 걸음(1.71m/s)으로도 반응 0.25초 뒤에 빠져나올 수 있는가"를
//       패턴마다 다시 풀었다. 셋 다 이제 **걷기로 탈출 가능**하다.
//       (칼을 휘두르는 중이면 1.19초 묶이므로 여전히 못 피한다 - 그건 벌로 남긴다.
//        main.js 가 넣는 대시가 그 구멍을 메운다)
//
// 1) 후려치기 — 앞쪽 부채꼴.
//    2.8m 에 서 있다가 반경 3.4 밖으로 = 뒤로 0.6m. 걷기 0.35초 + 반응 0.25 = 0.60초.
//    예고 0.95 면 0.35초가 남는다(0.80 이면 여유가 0.20 뿐이라 프레임 운이 섞였다).
const SWIPE = { tell: 0.95, act: 0.18, rec: 1.30, r: 3.4, half: Math.PI * 0.25, dmg: 10 };
// 2) 돌진 — 직선. 멀어지면 이걸로 간격을 지운다. 느린 보스의 유일한 접근 수단.
//    통로 반폭 1.5 + 플레이어 반경 0.35 = **옆으로 1.85m**.
//    ★1.10 이었다. 그 값은 "탱커도 이 거리에서는 달리고 있다"를 가정한 값인데,
//      실제로는 예고를 본 순간 멈춰서 방향을 트는 사람이 대부분이라 걷기로 잡아야 한다.
//      걷기 1.71m/s 로 1.85m = 1.08초 + 반응 0.25 = **1.33초**. 예고 1.45 면 통과한다.
const CHARGE = { tell: 1.45, dash: 0.75, rec: 1.40, speed: 12.0,
                 half: 1.5, len: 9.0, hitR: 1.7, dmg: 13 };
// 3) 내려찍기 — 보스 중심 원. 제일 아프고 제일 크게 예고한다.
//    ★원의 중심을 **플레이어가 아니라 보스**에 둔 이유: 플레이어 발밑에 두면
//      반경을 중심에서부터 벗어나야 해서 2.1초짜리 예고가 필요하다. 그건 예고가
//      아니라 산책이다. 보스 중심이면 이미 2.8m 에 서 있으므로 조금만 더 나가면 된다.
//    ★반경 4.0 -> 3.6 · 예고 1.20 -> 1.45. 2.8m 에 선 사람은 0.8m 만 더 = 걷기 0.47초
//      + 반응 0.25 = 0.72초로 여유 있게 빠진다. **원 한복판**(0m)에 서 있었다면
//      3.6m 를 2.1초에 걸어야 하니 여전히 못 빠진다 - 거기는 대시 전제로 남긴다.
const SLAM = { tell: 1.45, act: 0.22, rec: 1.80, r: 3.6, dmg: 18 };
// 패턴 재사용 대기. 후려치기는 대기 없음(빈칸을 메우는 역할).
// 돌진 7초 / 내려찍기 9초. 셋이 균등하게 돌면 외우기만 하면 되는 순서 문제가 된다.
const CD_CHARGE = 7.0;
const CD_SLAM = 9.0;
// 거리 조건. 돌진은 멀 때만, 내려찍기는 가까울 때만.
const CHARGE_MIN = 7.5;             // 이보다 가까우면 돌진이 그냥 즉사기가 된다
// ★처음에 20 으로 뒀다가 브라우저에서 잡았다. 돌진 사거리는 9m(CHARGE.len)인데
//   19.5m 에서 돌진을 골라 **9m 를 달리고 헛돈 뒤 1.15초 경직**에 들어갔다.
//   예고 통로가 9m 로 그려지는 이상 닿지도 않을 거리에서 고르면 안 된다.
//   12 = 9m 돌진 + 그동안 플레이어가 다가오는 몫(2~3m).
const CHARGE_MAX = 12.0;
const SLAM_MAX = 6.5;
const SWIPE_MAX = 4.2;

// 플레이어 피해는 enemy.js 가 관리한다(체력·무적 0.65초·사망 전부 거기 있다).
// ★여기서 따로 체력을 들면 체력바가 두 개가 된다. 반드시 한 군데서만.

// ── 증표 ──
const TOKEN_PICK_R = 1.7;           // 줍기 반경. 달려 지나가다 자연히 걸리는 거리
const EXIT_PAD = 0.4;               // 탈출구 반경(맵 2.6)에 붙이는 여유

// 색
const COL_BOSS = new THREE.Vector3(1.65, 0.52, 0.42);   // 폴백 덩어리 색조(곱해지는 값)
// 예고 중 색. ★흰 번쩍임으로 예고를 알리면 안 된다.
//   흰색을 조금만 섞어도 블룸까지 겹쳐 **보스가 회색 덩어리**가 된다(v58_boss/02·04).
//   같은 붉은 계열로 더 뜨겁게만 올리면 실루엣·뿔·눈이 그대로 남고 "달아오른다"로 읽힌다.
//   흰 번쩍임은 **칼에 맞았을 때 전용**으로 남긴다(그래야 둘이 안 헷갈린다).
const COL_TELL_HOT = new THREE.Vector3(3.4, 0.80, 0.30);  // 폴백 덩어리용
// ★모델용. MeshToonMaterial 의 emissive 에 얹는다(텍스처 위에 더해지는 자체발광).
//   재질을 곱하기(color)로 물들이면 붉은 살결·검은 천이 통째로 뭉개진다. 각귀는
//   이미 붉은 몸이라 **더 뜨거워지기만** 하면 되므로 더하기가 맞다.
//   블룸 임계값이 1.02 라 이 값만으로는 안 번지고, 예고 끝(hot=1)에서만 살짝 걸린다.
// ★세기를 0.78 로 뒀다가 낮췄다. 아침 산야 팔레트에서는 그 값이면 갑옷·검은 천·
//   뿔이 전부 한 덩어리 주황으로 뭉개져서, 잡몹 시절 "회색 덩어리" 사고의 붉은 판이
//   된다(v76_boss/02_tell_swipe 첫 컷). 0.42 면 달아오른 게 읽히면서 갑옷이 남는다.
const HOT_E = new THREE.Vector3(0.42, 0.06, 0.03);
const COL_TELL = 0xff3a2a;          // 예고 바닥 표시(붉은색 = 위험 구역)
const COL_TOKEN = 0xffc23a;         // 증표(호박색). 붉은 요괴들과 안 섞인다

// ---------------------------------------------------------------------------
// 보스 모델 (web/boss.glb)
// ---------------------------------------------------------------------------
// ★모듈 최상단에서 await 한다. main.js 가 `await import('./boss.js')` 로 부르므로
//   여기서 기다리면 createBossSystem() 이 불릴 때는 모델이 반드시 준비돼 있다.
//   실패해도 게임이 통째로 죽으면 안 되니(맵·잡몹은 멀쩡하다) null 로 떨어뜨리고
//   아래에서 옛 임시 덩어리로 폴백한다.
// ★캐시버스팅 쿼리를 붙인다(main.js·enemy.js 와 같은 규칙).
const BOSS = await (async () => {
  try {
    const g = await new Promise((ok, bad) => {
      new GLTFLoader().load('./boss.glb' + location.search, ok, undefined, bad);
    });
    g.scene.updateMatrixWorld(true);
    // ★three.js 의 Box3 는 스킨드 메시를 **바인드 포즈**로 잰다(스키닝 안 먹은 상태).
    //   그래서 여기서 나오는 값은 Blender 레스트 키 1.7000 과 같다. 클립별 키
    //   (Idle 1.52 / Attack 2.20)로 재면 판마다 배율이 달라지므로 반드시 바인드로.
    const box = new THREE.Box3().setFromObject(g.scene);
    return { scene: g.scene, clips: g.animations,
             bindH: box.max.y - box.min.y, footY: box.min.y };
  } catch (e) {
    console.error('[boss] boss.glb 로드 실패. 옛 임시 덩어리로 돈다.', e);
    return null;
  }
})();

// 상태
const S_IDLE = 0, S_CHASE = 1, S_TELL = 2, S_ACT = 3, S_REC = 4, S_RETURN = 5, S_DEAD = 6;
// 층 진행 단계(HUD 목표 한 줄이 이 값만 본다)
const P_FIND = 0, P_FIGHT = 1, P_PICK = 2, P_ESCAPE = 3, P_CLEAR = 4;

// 매 프레임 new 금지
const _v1 = new THREE.Vector3(), _v2 = new THREE.Vector3(), _v3 = new THREE.Vector3();
const _segA = new THREE.Vector3(), _segB = new THREE.Vector3();
const _prevA = new THREE.Vector3(), _prevB = new THREE.Vector3();
const _hitP = new THREE.Vector3();
const _q = new THREE.Quaternion(), _e = new THREE.Euler();
const _mat = new THREE.Matrix4(), _sc = new THREE.Vector3();
const _mv = { x: 0, z: 0, hit: false };

// 선분 위에서 점 p 에 가장 가까운 지점까지의 거리 제곱 (enemy.js 와 같은 계산)
function closestOnSeg(a, b, p, out) {
  _v3.copy(b).sub(a);
  const len2 = _v3.lengthSq();
  let t = len2 > 1e-9 ? _v3.dot(_v2.copy(p).sub(a)) / len2 : 0;
  t = t < 0 ? 0 : (t > 1 ? 1 : t);
  out.copy(a).addScaledVector(_v3, t);
  return out.distanceToSquared(p);
}

// ---------------------------------------------------------------------------
// 바닥 표시(예고). 위험 구역을 **바닥에 그대로 그린다.**
// 원리는 하나뿐이다: 테두리는 처음부터 진하게(= 어디까지 위험한지), 안쪽은
// 예고 시간에 맞춰 차오른다(= 언제 터지는지). 둘 다 없으면 못 피한다.
//  uMode 0 = 중심에서 바깥으로 차오름(원·부채꼴)
//  uMode 1 = 보스에서 앞으로 차오름(돌진 통로)
// ---------------------------------------------------------------------------
function decalMat(color) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uFill: { value: 0 }, uA: { value: 0 }, uMode: { value: 0 },
      uCol: { value: new THREE.Color(color) },
    },
    vertexShader: `
      varying vec2 vUv;
      void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      uniform float uFill; uniform float uA; uniform float uMode; uniform vec3 uCol;
      varying vec2 vUv;
      void main(){
        float t = uMode < 0.5 ? length(vUv - 0.5) * 2.0 : vUv.y;
        if (t > 1.0) discard;
        float edge = smoothstep(0.80, 0.97, t);
        float fill = t <= uFill ? 1.0 : 0.0;
        float a = (0.10 + fill * 0.34 + edge * 0.80) * uA;
        if (a < 0.008) discard;
        gl_FragColor = vec4(uCol * (0.55 + fill * 1.5 + edge * 1.7), a);
      }`,
  });
}

// 원판(내려찍기·증표 표시). 위를 보게 눕힌다.
function discMesh(color) {
  const g = new THREE.CircleGeometry(1, 44).rotateX(-Math.PI / 2);
  const m = new THREE.Mesh(g, decalMat(color));
  m.visible = false; m.frustumCulled = false; m.renderOrder = 3;
  return m;
}
// 부채꼴(후려치기). CircleGeometry 의 theta 는 XY 평면 +X 에서 시작하는데,
// 눕히면 theta=-pi/2 가 로컬 +Z(보스가 보는 방향)가 된다. 그래서 -pi/2 를 중심으로 연다.
function wedgeMesh(color, half) {
  const g = new THREE.CircleGeometry(1, 40, -Math.PI / 2 - half, half * 2).rotateX(-Math.PI / 2);
  const m = new THREE.Mesh(g, decalMat(color));
  m.visible = false; m.frustumCulled = false; m.renderOrder = 3;
  return m;
}
// 통로(돌진). 로컬 +Z 로 길이 1 만큼 뻗고 uv.y 가 0(보스) → 1(끝)이라
// uMode 1 로 두면 보스에서 앞으로 차오른다.
function laneMesh(color) {
  const g = new THREE.PlaneGeometry(1, 1).translate(0, 0.5, 0).rotateX(Math.PI / 2);
  const m = new THREE.Mesh(g, decalMat(color));
  m.material.uniforms.uMode.value = 1;
  m.visible = false; m.frustumCulled = false; m.renderOrder = 3;
  return m;
}

// ---------------------------------------------------------------------------
// 증표 빛기둥. 증표를 든 사람은 **위치가 노출된다**(설계의 핵심 장치).
// 지금은 솔로라 볼 사람이 없지만 구조는 지금 넣는다. 나중에 넷코드가
// carrier 상태를 브로드캐스트하면 다른 팀 화면에도 이 기둥이 그대로 선다.
// ---------------------------------------------------------------------------
function beamMesh(color, radius, height) {
  const g = new THREE.CylinderGeometry(radius, radius * 1.35, height, 14, 1, true)
    .translate(0, height * 0.5, 0);
  const m = new THREE.Mesh(g, new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    uniforms: { uCol: { value: new THREE.Color(color) }, uA: { value: 1 }, uT: { value: 0 } },
    vertexShader: `
      varying vec2 vUv;
      void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      uniform vec3 uCol; uniform float uA; uniform float uT;
      varying vec2 vUv;
      void main(){
        float up = 1.0 - vUv.y;
        float a = up * up * 0.55;
        a *= 0.75 + 0.25 * sin(uT * 3.0 - vUv.y * 9.0);   // 천천히 오르는 결
        gl_FragColor = vec4(uCol, a * uA);
      }`,
  }));
  m.frustumCulled = false; m.renderOrder = 4;
  return m;
}

// ---------------------------------------------------------------------------
export function createBossSystem(opts) {
  const scene = opts.scene;
  const getPlayerPos = opts.getPlayerPos;
  // 플레이어 체력·무적·사망은 enemy.js 한 군데서만 관리한다.
  const damagePlayer = opts.damagePlayer || function () {};
  // 소리·연출 통로. 보스는 소리를 직접 만들지 않고 "무슨 일이 일어났는지"만 알린다.
  // ★예고음이 예고와 어긋나면 소리로 피하는 게 불가능해진다. 그래서 예고 시작
  //   **그 자리**에서 남은 시간(dur)까지 같이 넘긴다(소리 쪽이 시간을 다시 재지 않게).
  const onEvent = opts.onEvent || function () {};
  const isPlayerDead = opts.isPlayerDead || function () { return false; };
  const getKills = opts.getKills || function () { return 0; };

  const data = LV.data() || {};
  const spec = data.boss;
  const arena = spec && spec.arena;
  if (!spec || !arena) {
    console.warn('[boss] level1.json 에 boss/arena 가 없다. 보스 없이 돈다.');
  }
  // ★level1.json 은 이미 three.js 좌표다. 변환하지 않는다.
  const HOME = spec
    ? { x: spec.x, z: spec.z, y: LV.groundY(spec.x, spec.z) }
    : { x: 0, z: 0, y: 0 };
  const AR = arena || { x: 0, z: 0, hx: 0, hz: 0 };
  // ★탈출구에는 **한글 지명**을 붙인다. json 의 id(EXIT_1)는 안 바꾼다.
  //   내부 이름이 클리어 패널에 그대로 새고 있었다(3차 QA #4 "증표 EXIT_1 로 반출").
  //   이름은 맵 한가운데(0,0)에서 본 방위로 짓는다. 플레이어 위치와 무관한 **고정 지명**이라
  //   같은 문이 언제나 같은 이름으로 불린다(맵은 x·z 둘 다 ±48 로 대칭이다).
  const EXITS = (LV.exits() || []).map(e => ({
    id: e.id, x: e.x, z: e.z, r: (e.radius || 2.5) + EXIT_PAD,
    name: (Math.abs(e.x) >= Math.abs(e.z) ? (e.x >= 0 ? '동' : '서')
                                          : (e.z >= 0 ? '남' : '북')) + '쪽 문',
  }));

  // ── 보스 몸 ──
  // boss.glb 가 있으면 스킨드 메시, 없으면 옛 임시 덩어리(요괴 지오메트리 x2.6).
  // 아래 로직은 body 아래 세 함수(place / look / show)만 부른다. 그래서 어느 쪽이
  // 서 있든 패턴·판정 코드는 한 줄도 안 갈라진다.
  let grp = null, mixer = null, curClip = null;
  const clips = {};
  const mats = [];
  let mesh = null, aTint = null, aFlash = null;   // 폴백 전용
  // 배율 = 목표 시각 키 / 바인드 박스 키. 로드 실패 시엔 안 쓴다.
  const K_H = BOSS ? VIS_H / BOSS.bindH : 1;

  if (BOSS) {
    grp = BOSS.scene;
    // ★boss.js 는 예전부터 YXZ 로 기울인다(yaw 먼저, 그다음 앞뒤·좌우 기울기).
    //   Object3D 기본은 XYZ 라 명시하지 않으면 돌아선 상태에서 기울기가 엉뚱하게 먹는다.
    grp.rotation.order = 'YXZ';
    grp.traverse(o => {
      if (!o.isMesh) return;
      o.frustumCulled = false;
      // ★그림자는 아래 가짜 원판이 맡는다. castShadow 를 켜면 섀도맵 패스에서
      //   15,040 삼각형 스킨드 메시를 한 번 더 그린다(잡몹과 같은 규칙).
      o.castShadow = false;
      o.receiveShadow = false;
      // 캐릭터(main.js loadChar)·잡몹(enemy.js)과 같은 규칙: 원본 PBR 을 버리고
      // MeshToonMaterial 로 간다. 같은 조명·톤매핑 아래서 같은 그림체로 보여야 한다.
      const old = o.material;
      o.material = new THREE.MeshToonMaterial({
        map: old && old.map ? old.map : null,
        color: 0xffffff,
        emissive: 0x000000,      // 예고(붉게)·피격(희게)이 여기 얹힌다
      });
      mats.push(o.material);
    });
    mixer = new THREE.AnimationMixer(grp);
    // ★없는 클립을 참조하면 그 자리에서 렌더 루프가 통째로 죽는다(예전 사고).
    //   이름을 정확히 못 찾을 수도 있으니 대소문자·접미사를 무시하고 찾고,
    //   없으면 그냥 null 로 둔다(playClip 이 null 을 그냥 흘린다).
    for (const want of ['Idle', 'Walk', 'Run', 'Attack']) {
      const c = BOSS.clips.find(x => x.name === want)
        || BOSS.clips.find(x => x.name.toLowerCase().startsWith(want.toLowerCase()));
      clips[want] = c ? mixer.clipAction(c) : null;
    }
    if (clips.Attack) {
      clips.Attack.setLoop(THREE.LoopOnce, 1);
      clips.Attack.clampWhenFinished = true;
    }
    grp.visible = false;
    scene.add(grp);
    // ★console.log 의 서식 지정자는 %f · %d · %s · %o 뿐이다. **%.4f 는 없다.**
    //   그래서 여태 "바인드 키 %.4f -> 시각 키 %.2f" 가 글자 그대로 찍히고
    //   숫자 세 개가 뒤에 줄줄이 붙어 나왔다(= 로그가 아무 값도 못 알려줬다).
    //   자리수는 JS 에서 미리 만들어 넣고 %s 로 받는다.
    if (DEV) {
      console.log('[boss] boss.glb 바인드 키 ' + BOSS.bindH.toFixed(4)
        + ' -> 시각 키 ' + VIS_H.toFixed(2) + ' (배율 ' + K_H.toFixed(4) + ')'
        + ' / 클립 ' + BOSS.clips.map(c => c.name).join(','));
    }
  } else {
    // 폴백. InstancedMesh(count 1)로 만드는 이유: enemy.js 셰이더가 aTint/aFlash 를
    // 인스턴스 속성으로 읽는다. 일반 Mesh 로 만들면 정점마다 속성을 깔아야 한다.
    const geo = EN.buildYokaiGeometry();
    geo.setAttribute('aTint', new THREE.InstancedBufferAttribute(new Float32Array(3), 3));
    geo.setAttribute('aFlash', new THREE.InstancedBufferAttribute(new Float32Array(1), 1));
    mesh = new THREE.InstancedMesh(geo, EN.makeEnemyMaterial(scene.fog, false), 1);
    mesh.frustumCulled = false;
    mesh.count = 0;
    scene.add(mesh);
    aTint = geo.attributes.aTint;
    aFlash = geo.attributes.aFlash;
    aTint.setXYZ(0, COL_BOSS.x, COL_BOSS.y, COL_BOSS.z);
    aTint.needsUpdate = true;
  }

  // 몸 세우기. ★판정(CENTER_Y / HIT_R)과 **완전히 분리**돼 있다.
  //   여기 숫자를 아무리 바꿔도 히트 구는 안 움직인다.
  //   sink 는 죽을 때 가라앉는 깊이, k 는 크기 배수(예고 부풀림 · 사망 수축).
  function place(lean, roll, k, sink) {
    if (grp) {
      grp.position.set(pos.x, pos.y - sink, pos.z);   // 발이 groundY 에 닿는다
      grp.rotation.set(lean, yaw, roll);
      grp.scale.setScalar(K_H * k);
    } else if (mesh) {
      _v1.set(pos.x, pos.y + HOVER - sink, pos.z);
      _q.setFromEuler(_e.set(lean, yaw, roll, 'YXZ'));
      const s = SCALE * k;
      _sc.set(s, s, s);
      _mat.compose(_v1, _q, _sc);
      mesh.setMatrixAt(0, _mat);
      mesh.instanceMatrix.needsUpdate = true;
    }
  }

  // 달아오름(예고) · 번쩍임(피격). 둘을 다른 색으로 둬야 안 헷갈린다.
  function look(hot, fl) {
    if (grp) {
      const r = HOT_E.x * hot + fl * 0.9;
      const g = HOT_E.y * hot + fl * 0.9;
      const b = HOT_E.z * hot + fl * 0.9;
      for (let i = 0; i < mats.length; i++) mats[i].emissive.setRGB(r, g, b);
    } else if (aTint) {
      aTint.setXYZ(0,
        COL_BOSS.x + (COL_TELL_HOT.x - COL_BOSS.x) * hot,
        COL_BOSS.y + (COL_TELL_HOT.y - COL_BOSS.y) * hot,
        COL_BOSS.z + (COL_TELL_HOT.z - COL_BOSS.z) * hot);
      aTint.needsUpdate = true;
      aFlash.setX(0, fl);
      aFlash.needsUpdate = true;
    }
  }

  function show(v) {
    if (grp) grp.visible = v;
    else if (mesh) mesh.count = v ? 1 : 0;
  }

  // 클립 재생. ★없는 클립을 부르면 아무 일도 안 한다(방어).
  function playClip(name, ts, fade) {
    const a = clips[name];
    if (!a) return;
    a.setEffectiveTimeScale(ts);
    if (curClip === a) return;
    a.reset().play();
    if (curClip) curClip.crossFadeTo(a, fade === undefined ? 0.18 : fade, false);
    else a.fadeIn(0.12);
    curClip = a;
  }

  // 공격 클립을 **타격 구간부터** 튼다(앞 25프레임의 준비 자세는 예고가 이미 했다).
  function playAttack() {
    const a = clips.Attack;
    if (!a) return;
    a.reset();
    a.time = ATK_START_T;
    a.setEffectiveTimeScale(ATK_TS);
    a.play();
    if (curClip && curClip !== a) curClip.crossFadeTo(a, 0.06, false);
    curClip = a;
  }

  // 발밑 그림자. 잡몹은 enemy.js 가 원판을 깔아 주는데 보스는 그 풀 밖이라 하나 만든다.
  // 이게 없으면 3m 짜리가 허공에 붕 떠 보인다.
  const shadow = new THREE.Mesh(
    new THREE.CircleGeometry(1, 24).rotateX(-Math.PI / 2),
    new THREE.ShaderMaterial({
      transparent: true, depthWrite: false,
      uniforms: {},
      vertexShader: `varying float vR;
        void main(){ vR = length(position.xz);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `varying float vR;
        void main(){ float a = 1.0 - smoothstep(0.15, 1.0, vR);
          if (a < 0.01) discard; gl_FragColor = vec4(0.0, 0.005, 0.02, a * 0.5); }`,
    }));
  shadow.renderOrder = -1;
  shadow.frustumCulled = false;
  shadow.visible = false;
  scene.add(shadow);

  // 예고 표시 3종
  const dSwipe = wedgeMesh(COL_TELL, SWIPE.half);
  const dLane = laneMesh(COL_TELL);
  const dSlam = discMesh(COL_TELL);
  scene.add(dSwipe); scene.add(dLane); scene.add(dSlam);
  // 내려찍기가 터질 때 퍼지는 충격 링(예고와 다른 색으로 "이미 터졌다"를 알린다)
  const dShock = discMesh(0xffd9a0);
  scene.add(dShock);

  // ── 증표 ──
  const token = new THREE.Group();
  const tokGem = new THREE.Mesh(
    new THREE.OctahedronGeometry(0.30, 0),
    new THREE.MeshBasicMaterial({ color: COL_TOKEN }));
  tokGem.position.y = 0.85;
  token.add(tokGem);
  const tokBeam = beamMesh(COL_TOKEN, 0.22, 7.0);
  token.add(tokBeam);
  const tokRing = discMesh(COL_TOKEN);
  tokRing.material.uniforms.uA.value = 0.9;
  tokRing.material.uniforms.uFill.value = 0;
  tokRing.visible = true;
  tokRing.scale.setScalar(TOKEN_PICK_R);
  tokRing.position.y = 0.04;      // 바닥과 같은 높이면 지글거린다
  token.add(tokRing);
  token.visible = false;
  scene.add(token);

  // 소지자 표식. ★"증표를 든 사람은 층 전체에 위치가 보인다"의 구현부다.
  // 지금은 자기 머리 위에 서는 기둥 하나지만, 이 기둥의 좌표가 곧
  // 넷코드가 다른 팀에게 보낼 값이다(carrier 게터로 밖에 내놨다).
  const carryBeam = beamMesh(COL_TOKEN, 0.30, 9.0);
  carryBeam.visible = false;
  scene.add(carryBeam);

  // -------------------------------------------------------------------------
  // HUD (CSS 는 파일 안 만들고 여기서 주입. enemy.js 가 쓰는 방식 그대로)
  // -------------------------------------------------------------------------
  const st = document.createElement('style');
  st.textContent =
    '#bHud{position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:6;' +
    'pointer-events:none;user-select:none;text-align:center;width:min(520px,74vw);' +
    'font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif}' +
    '#bGoal{font-size:14px;letter-spacing:1px;color:#cfe4f5;text-shadow:0 1px 4px #000;' +
    'opacity:.92}' +
    '#bGoal i{font-style:normal;color:#ffc23a}' +
    '#bBox{margin-top:8px;opacity:0;transition:opacity .25s}' +
    '#bName{font-size:12px;letter-spacing:2px;color:#ff9a8a;margin-bottom:4px;' +
    'text-shadow:0 1px 4px #000}' +
    '#bBar{height:11px;border:1px solid #6b2a2a;border-radius:6px;background:#160a0c;overflow:hidden}' +
    '#bFill{height:100%;width:100%;background:linear-gradient(90deg,#c0281e,#ff6a4a);' +
    'transition:width .12s linear}' +
    '#bClear{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:8;' +
    'pointer-events:none;opacity:0;transition:opacity .4s;text-align:center;' +
    'padding:26px 44px;border:1px solid #2c4a63;border-radius:12px;' +
    'background:rgba(4,8,14,.82);box-shadow:0 0 60px rgba(20,60,110,.5);' +
    'font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif}' +
    '#bClear h1{font-size:30px;font-weight:800;letter-spacing:6px;color:#8fe8ff;' +
    'text-shadow:0 0 22px #1f7fd0;margin-bottom:16px}' +
    '#bClear table{margin:0 auto;font-size:14px;color:#7b93a8;border-spacing:14px 5px}' +
    '#bClear td.v{color:#e8f4ff;font-weight:700;text-align:right;font-variant-numeric:tabular-nums}' +
    '#bClear .hint{margin-top:16px;font-size:12px;color:#5d7285;letter-spacing:1px}';
  document.head.appendChild(st);
  const hud = document.createElement('div');
  hud.id = 'bHud';
  hud.innerHTML =
    '<div id="bGoal"></div>' +
    '<div id="bBox"><div id="bName"></div><div id="bBar"><div id="bFill"></div></div></div>';
  document.body.appendChild(hud);
  const clearEl = document.createElement('div');
  clearEl.id = 'bClear';
  document.body.appendChild(clearEl);
  const goalEl = document.getElementById('bGoal');
  const boxEl = document.getElementById('bBox');
  const nameEl = document.getElementById('bName');
  const fillEl = document.getElementById('bFill');
  nameEl.textContent = '1층 · 각귀';

  // ---------------------------------------------------------------------------
  // 목표 문구. ★오너가 바꿀 곳은 이 표 하나다. 아래 코드에는 문구가 안 박혀 있다.
  //
  // 3차 QA: "게임이 나를 적에게 데려다주지 않는다"(블라인드 18분간 보스 육안 0회).
  //   예전 문구는 **무엇**만 말하고(보스를 찾아라) **어디**를 안 말했다. 화면 어디에도
  //   방향이 없으니 초원 96m 를 무작정 헤맬 수밖에 없다. 그래서 한 줄에 방위와
  //   지형 표식을 같이 넣는다. 화면은 고정 쿼터뷰(yaw 0)라 **화면 위 = 북**이고,
  //   방위가 그대로 조작(위쪽 키)이 된다.
  //
  // 치환:
  //   {방위}, → '북쪽, ' 처럼 채워진다. 목표가 코앞이면(GOAL_DIR_MIN 안) **쉼표까지
  //             통째로 지워진다.** 두 걸음 옆에 있는 것에 방위를 붙이면 거짓말이 된다.
  //   {문}   → 탈출구 지명('남쪽 문'). EXITS 의 name 에서 온다.
  // 내부 이름(EXIT_1 · 보스 · phase 번호)은 한 글자도 안 쓴다.
  const GOAL = {
    find:   '{방위}, 붉은 끈의 선돌을 지나 각귀에게',
    fight:  '각귀를 쓰러뜨려라',
    pick:   '{방위}, 떨어진 <i>증표</i>를 주워라',
    escape: '{방위}, <i>증표</i>를 들고 {문}으로',
    clear:  '층 돌파',
    // ★'· 위치 노출' 이었다. 명사 두 개로는 **무슨 일이 일어나는지**가 안 읽힌다
    //   (건틀릿 연출UI S8). 9A-2 가 ui.js 에서 화면만 갈아 끼우고 있었는데,
    //   같은 말을 두 파일이 따로 들고 있으면 언젠가 갈린다. 원본을 고쳤다.
    expose: ' <i>· 요괴들이 증표를 쫓는다</i>',      // 탈출 중에는 뒤에 붙는다
  };
  // m. 이 거리 안이면 방위를 안 쓴다(가까울수록 방위는 매 걸음 뒤집혀서 도움이 안 된다)
  const GOAL_DIR_MIN = 8;
  const DIRS = ['북', '북동', '동', '남동', '남', '남서', '서', '북서'];

  // 플레이어에서 목표로 본 8방위. 맵 좌표는 -z 가 북, +x 가 동이다(level1.json 계약).
  function dirIndex(dx, dz) {
    let i = Math.round(Math.atan2(dx, -dz) / (Math.PI / 4));   // 0 = 북, +1 = 북동
    if (i < 0) i += 8;
    return i % 8;
  }

  // 지금 어디로 가야 하는가. 문구와 나침반(ui.js)이 **같은 한 곳**에서 목표를 받는다.
  // 두 벌로 두면 화살은 증표를 가리키는데 글자는 탈출구를 말하는 날이 온다.
  function guideTarget() {
    if (phase === P_CLEAR) return null;
    if (phase === P_PICK) {
      return tokenState === 1 ? { x: tokenPos.x, z: tokenPos.z, kind: 'token' } : null;
    }
    if (phase === P_ESCAPE) {
      const e = nearestExit();
      return e ? { x: e.x, z: e.z, kind: 'exit', name: e.name } : null;
    }
    return { x: pos.x, z: pos.z, kind: 'boss' };     // 보스탐색 · 보스전
  }
  function nearestExit() {
    if (!EXITS.length) return null;
    const p = getPlayerPos();
    let best = EXITS[0], bd = Infinity;
    for (const e of EXITS) {
      const dx = e.x - p.x, dz = e.z - p.z;
      const d = dx * dx + dz * dz;
      if (d < bd) { bd = d; best = e; }
    }
    return best;
  }

  // 문구 한 줄을 만든다. ★DOM 은 **글자가 바뀔 때만** 건드린다(아래 syncHud 의 memo).
  function goalLine(di, door) {
    const t = phase === P_FIND ? GOAL.find
      : phase === P_FIGHT ? GOAL.fight
      : phase === P_PICK ? GOAL.pick
      : phase === P_ESCAPE ? GOAL.escape : GOAL.clear;
    return t.replace('{방위}, ', di < 0 ? '' : DIRS[di] + '쪽, ')
            .replace('{문}', door || '탈출구')
          + (phase === P_ESCAPE ? GOAL.expose : '');
  }

  // memo. 단계·방위·문이 그대로면 문자열을 만들지도, DOM 을 쓰지도 않는다.
  let hudPhase = -1, hudDir = -99, hudDoor = '', hudHp = -1, hudBar = -1;
  function syncHud() {
    // 방위는 매 프레임 다시 잰다(값이 싸다. atan2 한 번). 바뀔 때만 글자가 바뀐다.
    // ★보스전·돌파 문구에는 {방위} 자리가 없다. 그 단계에서 방위를 재면 값만 흔들려서
    //   같은 글자를 몇 번씩 다시 쓴다(memo 가 헛돈다).
    let di = -1, door = '';
    const t = (phase === P_FIGHT || phase === P_CLEAR) ? null : guideTarget();
    if (t) {
      if (t.name) door = t.name;
      const p = getPlayerPos();
      const dx = t.x - p.x, dz = t.z - p.z;
      // 코앞이면 방위를 뺀다. 탈출구는 지명이 이미 방위를 말하므로 겹치면 뺀다
      //   ('남쪽, 증표를 들고 남쪽 문으로' 같은 말이 안 나오게).
      if (dx * dx + dz * dz > GOAL_DIR_MIN * GOAL_DIR_MIN) {
        di = dirIndex(dx, dz);
        if (door && door.indexOf(DIRS[di] + '쪽') === 0) di = -1;
      }
    }
    if (hudPhase !== phase || hudDir !== di || hudDoor !== door) {
      hudPhase = phase; hudDir = di; hudDoor = door;
      goalEl.innerHTML = goalLine(di, door);
    }
    // 체력바는 **보스전 중에만**. 귀환·회복 중에도 보여야 "도망치면 회복한다"를 눈으로 배운다.
    const showBar = state === S_CHASE || state === S_TELL || state === S_ACT
      || state === S_REC || state === S_RETURN;
    if (hudBar !== (showBar ? 1 : 0)) {
      hudBar = showBar ? 1 : 0;
      boxEl.style.opacity = showBar ? '1' : '0';
    }
    if (hudHp !== hp) {
      hudHp = hp;
      fillEl.style.width = (Math.max(0, hp) / MAX_HP * 100).toFixed(1) + '%';
    }
  }

  function fmtTime(s) {
    const m = Math.floor(s / 60);
    const r = s - m * 60;
    return m > 0 ? m + '분 ' + r.toFixed(1) + '초' : r.toFixed(1) + '초';
  }

  // -------------------------------------------------------------------------
  // 상태
  // -------------------------------------------------------------------------
  let T = 0;                       // 시스템 시간(정지 중엔 안 흐른다)
  let runT = 0;                    // 층 소요 시간
  let phase = P_FIND;
  let state = S_IDLE;
  let hp = MAX_HP;
  let pos = new THREE.Vector3(HOME.x, HOME.y, HOME.z);
  let yaw = 0;
  let flash = 0;
  let stateT = 0;                  // 현재 상태에 머문 시간
  let atk = null;                  // 진행 중인 패턴 ('swipe'|'charge'|'slam')
  let atkHit = false;              // 이번 패턴이 이미 한 대 먹였는가(연타 방지)
  let aimX = 0, aimZ = 1;          // 예고 시작 순간에 **고정된** 조준
  let ax = 0, az = 0;              // 내려찍기 중심(고정)
  let cdCharge = 0, cdSlam = 0;
  let deathT = 0;
  let lastSwing = -1;
  let hasPrev = false;
  let shockT = -1;
  // 증표
  let tokenState = 0;              // 0=없음 1=바닥 2=소지
  const tokenPos = new THREE.Vector3();
  let carriedSince = 0;
  let clearedAt = -1;
  let clearInfo = null;
  let wasDead = false;
  // ── ★이 판에서 잡은 수 ──
  // enemy.js 의 kills 는 "R 을 누를 때 0 으로 돌아가는 판 누적"이고, 여기서는
  // 판 시작 시점과의 차이를 쓴다. 두 값이 일치해야 HUD·클리어 패널·재시작이 삼자일치다.
  // ★고장나는 경로가 하나 있다. main.js 는 R 에서 resetKills() -> boss.restart()
  //   순서로 부르는데, 이 순서가 뒤집히거나(다른 진입점) 누가 kills 를 따로 되돌리면
  //   killsAtStart 가 현재 kills 보다 커진 채로 남는다. 그러면
  //   Math.max(0, kills - killsAtStart) 가 **영영 0** 이다 = "클리어 패널 처치 0 고정".
  //   그래서 매 프레임 감시해서 바깥 카운터가 줄어들면 기준선을 그 자리로 내린다.
  let killsAtStart = 0;
  function syncKillBase() {
    const k = getKills();
    if (k < killsAtStart) killsAtStart = k;      // 바깥에서 리셋됐다 = 기준선도 내린다
  }
  function runKills() { return Math.max(0, getKills() - killsAtStart); }
  // ── ★조우 유예 ──
  // 배너("각귀")가 뜨는 1.42초 시점에 이미 첫 예고가 터지고 있었다(건틀릿 실측).
  // 카드가 화면을 덮은 채로 맞으면 그건 연출이 아니라 사고다.
  // 아레나에 처음 발을 들인 뒤 이 시간 동안은 패턴을 아예 안 고른다(추격만 한다).
  // ★1.5 -> 2.0. 9A-2 가 배너 수명을 1.2 -> 2.5초로 늘렸고 **완전 불투명 구간이
  //   1.9초**라고 실측해 넘겼다(handoff_ui.md B-3). 유예가 그보다 짧으면 글자가
  //   아직 진한 동안 예고가 시작된다. 2.0 이면 불투명 구간을 덮고,
  //   첫 피해는 2.0 + 예고(0.95~1.45) 뒤라 배너가 다 걷힌 다음이다.
  const FIGHT_GRACE = 2.0;
  let graceT = 0;
  let graceUsed = false;

  function setState(s) { state = s; stateT = 0; }

  // 각도 보간. ±pi 를 넘어가는 최단 방향으로 k(0..1) 만큼 돈다.
  // ★차이를 안 접으면 359도를 도는 그림이 나온다(한 프레임 스냅으로 보인다).
  function turnTo(cur, want, k) {
    let d = want - cur;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    return cur + d * Math.min(1, Math.max(0, k));
  }

  function inArena(x, z, pad) {
    return Math.abs(x - AR.x) <= AR.hx + pad && Math.abs(z - AR.z) <= AR.hz + pad;
  }

  // -------------------------------------------------------------------------
  // 리셋. R(제자리)과 클리어 후 재도전이 같은 문을 지나게 한다.
  // -------------------------------------------------------------------------
  function restart() {
    hp = MAX_HP;
    pos.set(HOME.x, HOME.y, HOME.z);
    yaw = 0; flash = 0;
    setState(S_IDLE);
    atk = null; atkHit = false;
    cdCharge = 0; cdSlam = 0;
    deathT = 0; shockT = -1;
    tokenState = 0;
    token.visible = false;
    carryBeam.visible = false;
    phase = P_FIND;
    runT = 0;
    killsAtStart = getKills();
    graceT = 0; graceUsed = false;
    clearedAt = -1; clearInfo = null;
    clearEl.style.opacity = '0';
    // ★재시작 때 클립을 통째로 되감는다. 안 하면 지난 판에서 죽을 때 굳었던
    //   공격 클립(clampWhenFinished)이 그대로 남아 다음 판 보스가 팔을 든 채 서 있다.
    for (const k in clips) if (clips[k]) { clips[k].stop(); clips[k].paused = false; }
    curClip = null;
    look(0, 0);
    playClip('Idle', 1);
    show(!!spec);                 // 맵에 보스 자리가 없으면 아예 안 세운다
    shadow.visible = !!spec;
    hideTells();
  }

  function hideTells() {
    onEvent('tellEnd', {});
    dSwipe.visible = false; dLane.visible = false; dSlam.visible = false;
    // ★충격 링도 같이 꺼야 한다. shockT 만 -1 로 되돌렸더니 R 로 재시작한 뒤에도
    //   지난 판의 붉은 고리가 바닥에 남아 있었다(v58_boss/03 스크린샷).
    dShock.visible = false; shockT = -1;
  }

  // -------------------------------------------------------------------------
  // 칼 맞기. enemy.js 가 뽑아 준 스윙 번호를 그대로 쓴다(중복 타격 방지 공유).
  // ★칼은 프레임 사이를 건너뛴다. 이전 프레임 선분과 이번 선분 사이를 쪼개 검사한다.
  // -------------------------------------------------------------------------
  function bladeHit(a, b, swing, heavy) {
    if (swing === lastSwing) return false;
    _v1.set(pos.x, pos.y + CENTER_Y, pos.z);
    const rad = HIT_R + 0.14;                 // 0.14 = enemy.js BLADE_PAD(칼날 굵기)
    const travel = Math.max(a.distanceTo(_prevA), b.distanceTo(_prevB));
    const steps = Math.max(2, Math.min(6, Math.ceil(travel / 0.3) + 1));
    for (let s = 0; s < steps; s++) {
      const t = s / (steps - 1);
      _segA.copy(_prevA).lerp(a, t);
      _segB.copy(_prevB).lerp(b, t);
      if (closestOnSeg(_segA, _segB, _v1, _hitP) > rad * rad) continue;
      lastSwing = swing;
      hp -= heavy ? HEAVY_DMG : HIT_DMG;
      flash = 1;
      onEvent('hit', { swing, heavy: !!heavy, dead: hp <= 0,
                       x: _hitP.x, y: _hitP.y, z: _hitP.z });
      // 맞으면 잠자던 보스도 일어나고, 돌아가던 보스도 다시 붙는다.
      // (돌아가는 중에 때려도 계속 도망가면 뒤통수만 치는 무한 딜이 된다)
      if (state === S_IDLE || state === S_RETURN) { setState(S_CHASE); phase = P_FIGHT; }
      if (hp <= 0) die();
      return true;
    }
    return false;
  }

  function die() {
    hp = 0;
    onEvent('die', {});
    setState(S_DEAD);
    deathT = 0;
    hideTells();
    phase = P_PICK;
    // 증표는 쓰러진 자리에 떨어진다. 벽에 겹치면 밖으로 밀어낸다.
    const p = LV.pushOut(pos.x, pos.z, 0.4, _mv);
    dropToken(p.x, p.z);
  }

  function dropToken(x, z) {
    tokenState = 1;
    tokenPos.set(x, LV.groundY(x, z), z);
    token.position.copy(tokenPos);
    token.visible = true;
    carryBeam.visible = false;
  }

  function pickToken() {
    onEvent('token', {});
    tokenState = 2;
    token.visible = false;
    carryBeam.visible = true;
    carriedSince = runT;
    phase = P_ESCAPE;
  }

  function doClear(exit) {
    onEvent('clear', {});
    tokenState = 3;
    carryBeam.visible = false;
    phase = P_CLEAR;
    clearedAt = runT;
    // exit 은 내부 id(EXIT_1)를 그대로 들고 있다. **화면에는 지명만 쓴다**(3차 QA #4).
    //   id 는 API·로그에 남겨 둔다(검증 스크립트가 그걸로 어느 문인지 가린다).
    clearInfo = { time: +runT.toFixed(1), kills: runKills(),
                  exit: exit.id, exitName: exit.name };
    clearEl.innerHTML =
      '<h1>층 돌파</h1><table>' +
      '<tr><td>소요 시간</td><td class="v">' + fmtTime(runT) + '</td></tr>' +
      '<tr><td>처치</td><td class="v">' + clearInfo.kills + '</td></tr>' +
      '<tr><td>보스</td><td class="v">각귀 격파</td></tr>' +
      '<tr><td>증표</td><td class="v">' + (exit.name || '탈출구') + '으로 반출</td></tr>' +
      // ★'R 을 눌러 다시' 는 조사는 붙었는데 서술이 안 끝난다(건틀릿 연출UI S8).
      //   ui.js 가 화면에서 되돌리고 있던 것을 원본으로 옮겼다.
      '</table><div class="hint">R 키를 눌러 다시 도전</div>';
    clearEl.style.opacity = '1';
  }

  // -------------------------------------------------------------------------
  // 패턴 고르기.
  // 거리로 고르되 대기시간을 둬서 셋이 기계적으로 돌지 않게 한다.
  // -------------------------------------------------------------------------
  function chooseAttack(dist) {
    if (cdCharge <= 0 && dist > CHARGE_MIN && dist < CHARGE_MAX) return 'charge';
    if (cdSlam <= 0 && dist < SLAM_MAX) return 'slam';
    if (dist < SWIPE_MAX) return 'swipe';
    return null;
  }

  function beginAttack(name, player) {
    atk = name;
    atkHit = false;
    setState(S_TELL);
    // ★예고 시작 순간에 조준을 **고정한다.** 예고 중에도 계속 따라오면
    //   바닥 표시가 플레이어를 쫓아다녀서 피할 방법이 없어진다.
    //   "예고 = 이 자리가 위험하다"는 약속이 지켜져야 회피가 실력이 된다.
    let dx = player.x - pos.x, dz = player.z - pos.z;
    const d = Math.hypot(dx, dz) || 1;
    aimX = dx / d; aimZ = dz / d;
    yaw = Math.atan2(aimX, aimZ);
    ax = pos.x; az = pos.z;
    if (name === 'charge') cdCharge = CD_CHARGE;
    if (name === 'slam') cdSlam = CD_SLAM;
    // 예고 시작. 바닥 표시가 차오르는 것과 **같은 시간**을 소리에 준다.
    const P = name === 'charge' ? CHARGE : (name === 'slam' ? SLAM : SWIPE);
    onEvent('tell', { atk: name, dur: P.tell });
  }

  // 예고 표시 갱신. u = 0..1 진행도
  // ★높이는 groundY 가 아니라 **평지 바닥 + 4cm** 로 고정한다. groundY 를 쓰면
  //   보스가 제단(0.26) 위에 섰을 때 4m 짜리 원판이 통째로 24cm 떠서 허공에 뜬 고리가
  //   된다. 평지에 붙여두면 제단·단이 앞을 가리는 정도로만 끝난다(가산 합성이라
  //   z-fighting 은 안 난다. 4cm 는 바닥과 같은 높이일 때의 지글거림만 피하는 값이다).
  const DECAL_Y = LV.floorY() + 0.04;
  function showTell(u) {
    const gy = DECAL_Y;
    if (atk === 'swipe') {
      dSwipe.visible = true;
      dSwipe.position.set(pos.x, gy, pos.z);
      dSwipe.rotation.y = yaw;
      dSwipe.scale.setScalar(SWIPE.r);
      dSwipe.material.uniforms.uFill.value = u;
      dSwipe.material.uniforms.uA.value = Math.min(1, u * 4);
    } else if (atk === 'charge') {
      dLane.visible = true;
      dLane.position.set(pos.x, gy, pos.z);
      dLane.rotation.y = yaw;
      dLane.scale.set(CHARGE.half * 2, 1, CHARGE.len);
      dLane.material.uniforms.uFill.value = u;
      dLane.material.uniforms.uA.value = Math.min(1, u * 4);
    } else if (atk === 'slam') {
      dSlam.visible = true;
      dSlam.position.set(ax, gy, az);
      dSlam.scale.setScalar(SLAM.r);
      dSlam.material.uniforms.uFill.value = u;
      dSlam.material.uniforms.uA.value = Math.min(1, u * 4);
    }
  }

  // -------------------------------------------------------------------------
  function update(dt, ctx) {
    const player = getPlayerPos();

    // 정지(클립 미리보기) 중에도 칼 위치는 따라간다. 안 그러면 재개하는 순간
    // 몇 미터 떨어진 이전 선분과 이어져 허공을 훑으며 때린다(enemy.js 와 같은 함정).
    if (ctx && ctx.paused) {
      if (ctx.a && ctx.b) { _prevA.copy(ctx.a); _prevB.copy(ctx.b); hasPrev = true; }
      return;
    }

    T += dt;
    if (phase !== P_CLEAR) runT += dt;
    if (cdCharge > 0) cdCharge -= dt;
    if (cdSlam > 0) cdSlam -= dt;
    if (graceT > 0) graceT -= dt;
    syncKillBase();                    // 바깥 처치 카운터가 리셋됐는지 매 프레임 확인
    flash -= dt * 6; if (flash < 0) flash = 0;
    stateT += dt;

    const a = ctx && ctx.a, b = ctx && ctx.b;

    // ── 칼 맞기 ──
    // ctx.hot / ctx.swing 은 enemy.js 가 뽑은 값이다. 여기서 임계값을 다시 정의하면
    // "잡몹은 맞는데 보스는 안 맞는" 날이 반드시 온다.
    if (a && b) {
      if (hasPrev && ctx.hot && state !== S_DEAD) bladeHit(a, b, ctx.swing, !!ctx.heavy);
      _prevA.copy(a); _prevB.copy(b);
      hasPrev = true;
    } else {
      hasPrev = false;
    }

    const dead = isPlayerDead();
    // 플레이어가 죽는 순간을 **한 프레임에** 잡아야 그 자리에 떨어뜨린다.
    // (죽은 뒤 1.6초 있다가 리스폰되므로 그 전에 좌표를 기록해야 한다)
    if (dead && !wasDead && tokenState === 2) {
      const p = LV.pushOut(player.x, player.z, 0.4, _mv);
      dropToken(p.x, p.z);
      phase = P_PICK;
    }
    wasDead = dead;

    // ── 보스 행동 ──
    if (state === S_DEAD) {
      // 무너지는 연출. 기울며 가라앉는다(조각 절단은 잡몹 전용 풀이라 안 쓴다).
      // ★믹서를 안 돌린다. 베인 순간의 포즈에서 굳은 채로 넘어가야 "쓰러졌다"로 읽힌다.
      deathT += dt;
      const u = Math.min(1, deathT / 1.4);
      flash = Math.max(flash, 1 - u * 1.6);
      look(0, flash);                        // 마지막 흰 번쩍임이 꺼지며 가라앉는다
      place(u * 1.25, u * 0.35, 1 - u * 0.35, u * 2.2);
      show(u < 1);
      shadow.visible = u < 1;
      if (u < 1) {
        shadow.position.set(pos.x, pos.y + 0.03, pos.z);
        const sh = SHADOW_R * (1 - u * 0.35) * (1 - u);
        shadow.scale.set(sh, 1, sh);
      }
    } else if (spec) {
      const dx = player.x - pos.x, dz = player.z - pos.z;
      const dist = Math.hypot(dx, dz);
      const playerIn = inArena(player.x, player.z, 0);
      const playerOut = !inArena(player.x, player.z, LEASH_MARGIN);
      // 이번 프레임에 실제로 발을 뗐는가(걷기/서기 클립을 고르는 유일한 근거).
      // ★move() 안에서 세면 벽에 막혀 제자리걸음을 해도 걷기가 돈다. 여기서 센다.
      let stepped = 0;

      if (state === S_IDLE) {
        // ★아레나에 발을 들이면 시작한다. 마당이 38x22m 라 문턱에서 이미 보스가 보인다.
        if (playerIn && !dead) {
          setState(S_CHASE); phase = P_FIGHT;
          // 첫 조우에만 유예를 준다. 나갔다 들어오기를 반복해 공짜 시간을 얻는 걸 막는다
          // (배너도 한 번만 뜬다 - ui.js bannerDone).
          if (!graceUsed) { graceUsed = true; graceT = FIGHT_GRACE; }
        }
        // 제자리에서 아주 느리게 돈다. 단 플레이어가 가까이 있으면 그쪽으로 몸을 튼다
        // (문턱에서 등을 보이고 도는 건 "여기 있는 줄 모른다"로 읽혀 김이 샌다).
        if (dist < 16 && dist > 0.01) yaw = turnTo(yaw, Math.atan2(dx / dist, dz / dist), dt * 1.6);
        else yaw += dt * 0.25;
      } else if (state === S_RETURN) {
        hp = Math.min(MAX_HP, hp + HEAL_RATE * dt);
        let hx = HOME.x - pos.x, hz = HOME.z - pos.z;
        const hd = Math.hypot(hx, hz);
        if (hd < 0.4 && hp >= MAX_HP) { setState(S_IDLE); phase = P_FIND; }
        else if (hd > 0.05) {
          hx /= hd; hz /= hd;
          yaw = Math.atan2(hx, hz);
          move(hx * SPEED * 1.3 * dt, hz * SPEED * 1.3 * dt);
          stepped = SPEED * 1.3;
        }
        // 돌아가는 중에 다시 들어오면 바로 붙는다(회복분은 그대로 가져간다)
        if (playerIn && !dead) { setState(S_CHASE); phase = P_FIGHT; }
      } else {
        // 전투 중. 플레이어가 마당 밖으로 도망치거나 죽으면 포기하고 돌아간다.
        if (playerOut || dead) {
          setState(S_RETURN);
          atk = null; hideTells();
          if (!dead) phase = tokenState ? phase : P_FIND;
        } else if (state === S_CHASE) {
          // ★유예 중에는 패턴을 안 고른다(배너가 화면을 덮은 채로 맞지 않게).
          //   대신 걸어서 다가온다 = 화면은 멈춰 있지 않다.
          const want = graceT > 0 ? null : chooseAttack(dist);
          if (want) beginAttack(want, player);
          else {
            // 사거리 밖이면 걸어서 붙는다. 길찾기는 없다(직진이 전부다).
            const d = dist || 1;
            yaw = Math.atan2(dx / d, dz / d);
            move((dx / d) * SPEED * dt, (dz / d) * SPEED * dt);
            stepped = SPEED;
          }
        } else if (state === S_TELL) {
          const P = atk === 'charge' ? CHARGE : (atk === 'slam' ? SLAM : SWIPE);
          showTell(Math.min(1, stateT / P.tell));
          if (stateT >= P.tell) { setState(S_ACT); hideTells(); fire(player); }
        } else if (state === S_ACT) {
          runAct(dt, player);
        } else if (state === S_REC) {
          const P = atk === 'charge' ? CHARGE : (atk === 'slam' ? SLAM : SWIPE);
          // ── ★경직 후반의 느린 추격 (건틀릿: "보스가 몇 초씩 제자리") ──
          // 옛 구조에서는 경직 1.3~1.8초 동안 보스가 **한 발도 안 뗐다.** 플레이어가
          // 뒤로 빠지면 그 자리에서 굳은 채로 다음 예고를 시작해서, 멀리 선 사람에겐
          // "저 놈은 안 온다"로 보였다.
          // 경직 후반 45% 에만, 걷기의 3분의 1 속도로 조금 따라온다.
          //   · 앞 55% 는 그대로 굳어 있어야 "지금이 딜 타임"이라는 신호가 안 흐려진다
          //   · 0.7m/s 라 플레이어가 걷기만 해도 거리는 계속 벌어진다(도망은 여전히 유효)
          // 오너 기준으로 보스는 '대충'이라, 여기까지만 한다(길찾기·회피 없음).
          if (stateT > P.rec * 0.55 && dist > 2.2) {
            const d = dist || 1;
            yaw = turnTo(yaw, Math.atan2(dx / d, dz / d), dt * 2.0);
            move((dx / d) * SPEED * 0.34 * dt, (dz / d) * SPEED * 0.34 * dt);
            stepped = SPEED * 0.34;
          }
          if (stateT >= P.rec) { atk = null; setState(S_CHASE); }
        }
      }

      // ── 클립 고르기 ──
      // 상태를 그대로 클립에 대응시킨다. 재생속도 = 이동속도 / 접지 발 속도.
      // ★공격(swipe/slam)은 fire() 가 클립을 이미 걸었고, 경직(S_REC)은 그 꼬리가
      //   그대로 흐른다. 그래서 여기서는 손대지 않는다. 건드리면 휘두르다 만다.
      if (state === S_TELL) {
        // 예고 = 제자리에서 자세를 잡는다. 위험은 바닥 표시·달아오름·부풀기가 알린다.
        playClip('Idle', 1);
      } else if (state === S_ACT && atk === 'charge') {
        // 돌진 12m/s. Walk 로는 절대 안 따라온다.
        playClip('Run', CHARGE.speed / RUN_FOOT, 0.08);
      } else if (state === S_REC && stepped > 0.05) {
        // 경직 후반에 조금 따라올 때만. ★크로스페이드를 길게(0.24) 준다 - 공격 클립의
        //   회복 꼬리에서 걷기로 넘어가는 자리라 짧게 끊으면 팔이 튄다.
        playClip('Walk', stepped / WALK_FOOT, 0.24);
      } else if (state !== S_ACT && state !== S_REC) {
        if (stepped > 0.05) playClip(stepped > RUN_FOOT * 0.7 ? 'Run' : 'Walk',
          stepped / (stepped > RUN_FOOT * 0.7 ? RUN_FOOT : WALK_FOOT));
        else playClip('Idle', 1);
      }
      if (mixer) mixer.update(dt);

      // ── 몸 세우기 ──
      // ★예고 중에는 **몸이 부푼다.** 바닥 표시를 못 본 사람도 실루엣 변화로
      //   "온다"를 읽을 수 있어야 한다(예고 신호는 둘 이상이어야 한다).
      // ★기울기(lean)는 뼈 없는 덩어리 시절에 0.16~0.75 라디안(최대 43도)까지 썼다.
      //   진짜 사람 형태에 그걸 먹이면 허리가 부러진 것처럼 보인다. 동작은 클립이
      //   맡으므로 여기는 실루엣을 살짝 흔드는 정도만 남긴다(폴백은 옛 값 그대로).
      const big = !!grp;                      // 모델인가 폴백 덩어리인가
      let sBoost = 1, lean = big ? 0.0 : 0.16, bobAmp = big ? 0 : 0.14, hot = 0;
      if (state === S_TELL) {
        const P = atk === 'charge' ? CHARGE : (atk === 'slam' ? SLAM : SWIPE);
        const u = Math.min(1, stateT / P.tell);
        sBoost = 1 + u * (big ? 0.10 : 0.20);
        lean = big ? (atk === 'slam' ? -u * 0.14 : u * 0.10)       // 찍기는 몸을 세운다
                   : (atk === 'slam' ? 0.16 - u * 0.55 : 0.16 + u * 0.30);
        bobAmp = big ? 0 : 0.05;
        hot = u;                             // 붉게 달아오른다
      } else if (state === S_ACT) {
        sBoost = big ? 0.98 : 0.92;          // 터질 때 한 번 움츠린다
        lean = big ? (atk === 'slam' ? 0.10 : 0.08) : (atk === 'slam' ? 0.75 : 0.55);
        hot = 1;
      }
      const act = state === S_IDLE ? 0.35 : 1.0;
      const bob = Math.abs(Math.sin(T * (state === S_IDLE ? 1.3 : 3.0))) * bobAmp * act;
      look(hot, flash);
      place(lean * act, Math.sin(T * 1.9) * (big ? 0.02 : 0.06) * act, sBoost, -bob);
      show(true);
      shadow.visible = true;
      shadow.position.set(pos.x, pos.y + 0.03, pos.z);
      // ★잡몹과 같은 비율로. 처음에 1.05 를 곱했더니 반경 3.3m 짜리 검은 원판이
      //   깔려서 바닥에 구멍이 뚫린 것처럼 보였다(v58_boss/01 스크린샷).
      const sh = (big ? SHADOW_R : SCALE * 0.6) * sBoost;
      shadow.scale.set(sh, 1, sh);
    }

    // ── 충격 링(내려찍기가 터진 뒤) ──
    if (shockT >= 0) {
      shockT += dt;
      const u = shockT / 0.45;
      if (u >= 1) { shockT = -1; dShock.visible = false; }
      else {
        dShock.visible = true;
        dShock.scale.setScalar(SLAM.r * (0.35 + u * 0.85));
        dShock.material.uniforms.uFill.value = 1;
        dShock.material.uniforms.uA.value = (1 - u) * 1.2;
      }
    }

    // ── 증표 ──
    if (tokenState === 1) {
      tokGem.rotation.y += dt * 1.6;
      tokGem.position.y = 0.85 + Math.sin(T * 2.2) * 0.12;
      tokBeam.material.uniforms.uT.value = T;
      tokRing.material.uniforms.uA.value = 0.55 + Math.sin(T * 3.0) * 0.18;
      const dxT = player.x - tokenPos.x, dzT = player.z - tokenPos.z;
      if (!isPlayerDead() && dxT * dxT + dzT * dzT < TOKEN_PICK_R * TOKEN_PICK_R) pickToken();
    } else if (tokenState === 2) {
      // ★소지자 노출. 머리 위에 기둥이 선다. 이 좌표가 곧 넷코드가 뿌릴 값이다.
      carryBeam.position.set(player.x, player.y + 1.9, player.z);
      carryBeam.material.uniforms.uT.value = T;
      // 탈출구 판정. **보스를 죽인 것만으로는 안 된다.** 들고 나가야 확정이다.
      for (let i = 0; i < EXITS.length; i++) {
        const e = EXITS[i];
        const ex = player.x - e.x, ez = player.z - e.z;
        if (ex * ex + ez * ez < e.r * e.r) { doClear(e); break; }
      }
    }

    syncHud();
  }

  // 예고가 끝나는 순간. 여기서 실제 판정이 나간다.
  // ★즉발 한 프레임이 아니라 짧은 활성 구간(0.18~0.22초)을 둔다. 한 프레임만 보면
  //   경계에 서 있던 사람이 프레임 운으로 맞았다 안 맞았다 한다.
  function fire(player) {
    onEvent('fire', { atk });
    // ★휘두르는 그림은 여기서 시작한다. 예고가 끝나는 **그 프레임**에 피해가 들어가므로
    //   클립도 같은 프레임에 타격 구간부터 틀어야 칼과 판정이 눈으로 맞물린다.
    //   돌진은 달리는 그림이라 클립을 안 건다(위 update 가 Run 을 튼다).
    if (atk !== 'charge') playAttack();
    if (atk === 'slam') {
      // 터진 뒤 퍼지는 링. 예고(붉은색)와 다른 색이라 "이미 터졌다"가 구분된다.
      shockT = 0;
      dShock.position.set(ax, DECAL_Y + 0.01, az);
    }
    tryLand(player);
  }

  function runAct(dt, player) {
    const P = atk === 'charge' ? CHARGE : (atk === 'slam' ? SLAM : SWIPE);
    if (atk === 'charge') {
      const before = pos.x, beforeZ = pos.z;
      move(aimX * CHARGE.speed * dt, aimZ * CHARGE.speed * dt);
      const moved = Math.hypot(pos.x - before, pos.z - beforeZ);
      tryLand(player);
      // 벽에 박으면 즉시 끝낸다. 안 그러면 벽에 얼굴을 문지르며 시간을 다 쓴다.
      if (stateT >= CHARGE.dash || moved < CHARGE.speed * dt * 0.25) setState(S_REC);
    } else {
      tryLand(player);
      if (stateT >= P.act) setState(S_REC);
    }
  }

  // 패턴별 명중 판정. 한 패턴에 한 대만 들어간다.
  function tryLand(player) {
    if (atkHit || isPlayerDead()) return;
    if (atk === 'swipe') {
      const dx = player.x - pos.x, dz = player.z - pos.z;
      const d = Math.hypot(dx, dz);
      if (d > SWIPE.r) return;
      // 부채꼴. d 가 0 에 가까우면 각도가 의미 없으니 무조건 맞는다.
      if (d > 0.2) {
        const dot = (dx / d) * aimX + (dz / d) * aimZ;
        if (dot < Math.cos(SWIPE.half)) return;
      }
      atkHit = true; damagePlayer(SWIPE.dmg);
    } else if (atk === 'slam') {
      const dx = player.x - ax, dz = player.z - az;
      if (dx * dx + dz * dz > SLAM.r * SLAM.r) return;
      atkHit = true; damagePlayer(SLAM.dmg);
    } else if (atk === 'charge') {
      const dx = player.x - pos.x, dz = player.z - pos.z;
      if (dx * dx + dz * dz > CHARGE.hitR * CHARGE.hitR) return;
      atkHit = true; damagePlayer(CHARGE.dmg);
    }
  }

  // 벽 충돌은 플레이어·잡몹과 **같은 함수**를 쓴다. 따로 만들면 서로 다른 벽을 본다.
  // 그 위에 아레나 밖으로는 못 나가게 한 겹 더 가둔다(보스가 마당을 벗어나면
  // "마당에 들어가면 시작"이라는 규칙이 무너진다).
  function move(dx, dz) {
    const s = LV.slide(pos.x, pos.z, dx, dz, BODY_R, _mv);
    pos.x = s.x; pos.z = s.z;
    const lx = AR.hx - BODY_R, lz = AR.hz - BODY_R;
    if (pos.x < AR.x - lx) pos.x = AR.x - lx; else if (pos.x > AR.x + lx) pos.x = AR.x + lx;
    if (pos.z < AR.z - lz) pos.z = AR.z - lz; else if (pos.z > AR.z + lz) pos.z = AR.z + lz;
    pos.y = LV.groundY(pos.x, pos.z);
  }

  // 첫 배치
  restart();
  syncHud();

  // -------------------------------------------------------------------------
  const api = {
    update,
    restart,
    // ★넷코드 접점. 증표 소지자의 위치는 층 전체에 공개되는 값이다.
    //   지금은 솔로라 이 값을 볼 사람이 없지만, 구조를 먼저 넣어 둔다.
    get carrier() {
      if (tokenState !== 2) return null;
      const p = getPlayerPos();
      return { x: +p.x.toFixed(2), z: +p.z.toFixed(2), since: +carriedSince.toFixed(1) };
    },
    get token() {
      return { state: ['없음', '바닥', '소지', '반출'][tokenState],
               x: +tokenPos.x.toFixed(2), z: +tokenPos.z.toFixed(2) };
    },
    get hp() { return +hp.toFixed(1); },
    get maxHp() { return MAX_HP; },
    get state() { return ['대기', '추격', '예고', '공격', '경직', '귀환', '사망'][state]; },
    get attack() { return atk; },
    get phase() { return ['보스탐색', '보스전', '증표줍기', '탈출', '돌파'][phase]; },
    get pos() { return { x: +pos.x.toFixed(2), z: +pos.z.toFixed(2) }; },
    get time() { return +runT.toFixed(1); },
    get cleared() { return clearInfo; },
    // ★이 판에서 잡은 수. HUD(enemy.kills)·클리어 패널과 삼자일치를 밖에서 확인하는 창구.
    get runKills() { return runKills(); },
    // 조우 유예가 남아 있는가(배너와 겹치는 공격을 실제로 막고 있는지 검증용)
    get grace() { return +Math.max(0, graceT).toFixed(2); },
    // ★유도의 단일 진실. 상단 문구도 나침반(ui.js)도 이 값 하나를 본다.
    //   kind 는 '나침반에 무슨 글자를 새길까'까지 정해 준다(boss=鬼 · token=符 · exit=門).
    //   갈 곳이 없으면(층 돌파) null 이다.
    get guide() { return guideTarget(); },
    arena: AR,
    exits: EXITS,
    // 검증·디버그용. 브라우저 콘솔에서 바로 상태를 만들 수 있어야 한다.
    debug: {
      // 보스 앞으로 순간이동시키는 게 아니라 **보스를 즉사**시킨다(플레이 검증용)
      kill() { if (state !== S_DEAD) { hp = 0; die(); } return 'boss dead'; },
      hurt(n) { hp = Math.max(0, hp - (n || 10)); if (hp <= 0 && state !== S_DEAD) die(); return hp; },
      // 예고 중인지, 얼마나 남았는지
      tell() {
        if (state !== S_TELL) return null;
        const P = atk === 'charge' ? CHARGE : (atk === 'slam' ? SLAM : SWIPE);
        return { atk, left: +(P.tell - stateT).toFixed(2), total: P.tell };
      },
      // 경직(플레이어의 딜 타임)이 얼마나 남았는지. 칼 묶임 1.19초와 비교하는 창구다.
      rec() {
        if (state !== S_REC) return null;
        const P = atk === 'charge' ? CHARGE : (atk === 'slam' ? SLAM : SWIPE);
        return { atk, left: +(P.rec - stateT).toFixed(2), total: P.rec };
      },
    },
  };
  return api;
}
