// ---------------------------------------------------------------------------
// web/enemy.js — 맵에 자리잡은 요괴(고블린) 무리 / 칼날 선분 피격 / 두 동강
//
// main.js 는 이미 2천 줄이라 전투 로직을 통째로 여기로 뺐다.
// main.js 가 하는 일은 createEnemySystem() 한 번과 update() 한 줄이 전부다.
//
// 설계 원칙 (목표 플랫폼 = PC / 스팀)
//  1. 요괴는 **고블린 glb(뼈 24, 2000 삼각형)** 다. 예전엔 코드로 만든 464 삼각형
//     덩어리를 InstancedMesh 로 그렸는데, 그건 최종 아트가 나오기 전의 임시였다.
//     glb 는 **한 번만 로드**하고 SkeletonUtils.clone 으로 복제한다(지오메트리·텍스처
//     공유, 뼈만 새로). 그림자는 여전히 가짜 원판이다 - 스킨드 메시 수십을 섀도맵에
//     넣으면 스킨 패스가 통째로 한 번 더 돈다.
//  2. 피격은 main.js 의 measureBlade() 가 실측한 칼날 선분을 **그대로** 쓴다.
//     새 히트박스를 만들면 예전처럼 눈에 보이는 칼과 판정이 어긋난다(148도 사고).
//     판정 몸통은 구가 아니라 **세로 캡슐**이다(아래 CAP_* 주석에 근거).
//  3. 무한 스폰이 아니라 **자리를 잡고 있는 필드 몬스터**다. 어디로 갈지, 어디까지
//     당길지 고르는 게 이 게임의 긴장이다. 그래서 어그로 범위·무리 어그로·귀환이
//     전부 필요하다. 귀환이 없으면 맵 하나를 통째로 끌고 다니게 된다.
//  4. 매 프레임 객체를 만들지 않는다. 요괴도 시체도 전부 풀에서 꺼내 쓴다.
// ---------------------------------------------------------------------------
import * as THREE from './lib/three.module.js';
import { GLTFLoader } from './lib/GLTFLoader.js';
// 맵(벽 충돌·지면 높이)은 level.js 가 갖고 있다. ★main.js 와 **같은 쿼리**로 불러야
// 한다. URL 이 한 글자라도 다르면 브라우저가 별개 모듈로 올려서, main.js 가 로드해 둔
// 맵을 여기서는 못 보고 요괴만 벽을 뚫고 다니게 된다.
const LV = await import('./level.js' + location.search);
// 길찾기(흐름장)와 은신(수풀) 규칙. 둘 다 **같은 쿼리**로 부를 것(위와 같은 이유).
const NAV = await import('./nav.js' + location.search);
const ST = await import('./stealth.js' + location.search);
// ★이 파일이 내는 콘솔 로그는 전부 이 게이트를 지난다. 평시 콘솔은 0줄이어야
//   "콘솔 에러 0" 스모크가 뜻을 갖는다.
const DEV = typeof location !== 'undefined' && location.search.includes('dev');

// ---------------------------------------------------------------------------
// 고블린 모델
// ---------------------------------------------------------------------------
// ★clone 은 three.js examples/jsm/utils/SkeletonUtils.js 의 함수다. 이 레포 lib 에는
//   그 파일이 없고 필요한 건 clone 하나뿐이라 여기 옮겨 적었다(r160 원본과 같은 로직).
//   핵심은 두 가지다.
//    - Object3D.clone() 은 뼈 계층은 복제하지만 SkinnedMesh 의 skeleton 은 **원본을
//      그대로 가리킨다.** 그대로 두면 40마리가 뼈 한 벌을 공유해 전부 같은 포즈로 논다.
//    - 그래서 skeleton 을 복제하고 bones 배열을 **복제본 쪽 뼈**로 다시 매핑한다.
//   지오메트리·텍스처는 공유된다(복제 비용이 뼈 24개짜리 계층 하나뿐인 이유).
function cloneSkinned(source) {
  const srcOf = new Map(), cloneOf = new Map();
  const out = source.clone();
  (function walk(a, b) {
    srcOf.set(b, a); cloneOf.set(a, b);
    for (let i = 0; i < a.children.length; i++) walk(a.children[i], b.children[i]);
  })(source, out);
  out.traverse(node => {
    if (!node.isSkinnedMesh) return;
    const src = srcOf.get(node);
    node.skeleton = src.skeleton.clone();
    node.bindMatrix.copy(src.bindMatrix);
    node.skeleton.bones = src.skeleton.bones.map(b => cloneOf.get(b));
    node.bind(node.skeleton, node.bindMatrix);
  });
  return out;
}

// ★모듈 최상단에서 await 한다. main.js 가 `await import('./enemy.js')` 로 부르므로
//   여기서 기다리면 createEnemySystem() 이 불릴 때는 모델이 반드시 준비돼 있다.
//   실패해도 게임이 통째로 죽으면 안 되니(맵·보스는 멀쩡하다) null 로 떨어뜨린다.
const GOBLIN = await (async () => {
  try {
    const g = await new Promise((ok, bad) => {
      new GLTFLoader().load('./goblin.glb' + location.search, ok, undefined, bad);
    });
    g.scene.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(g.scene);
    let skin = null;
    g.scene.traverse(o => { if (o.isSkinnedMesh && !skin) skin = o; });
    if (!skin) throw new Error('SkinnedMesh 가 없다');
    return { scene: g.scene, clips: g.animations, skin,
             bindH: box.max.y - box.min.y, footY: box.min.y };
  } catch (e) {
    console.error('[enemy] goblin.glb 로드 실패. 요괴 없이 돈다.', e);
    return null;
  }
})();

// ---------------------------------------------------------------------------
// 배치
// ---------------------------------------------------------------------------
// ★무리 자리는 **맵이 정한다**. main.js 가 level1.json 의 mobs[] 를 그대로 넘겨준다.
// 예전에는 여기 하드코딩한 좌표 7개를 썼는데 그건 맵이 빈 평면이던 시절 얘기다.
// 맵의 무리 자리는 이미 통로·마당 한가운데로 잡혀 있고 서로 17m 이상 떨어져 있다
// (어그로 7m 두 개가 안 겹쳐야 "한 무리만 떼어낸다"가 성립한다).
//
// 마릿수만 여기서 정한다. 이건 맵 사정이 아니라 전투 사정이라 맵에 안 적는다.
//   3~5마리를 돌려 쓴다. 5마리에 정면으로 혼자 붙으면 지고, 3마리는 붙어볼 만하다.
//   무리마다 달라야 "저 무리는 건드리지 말자"는 판단이 생긴다.
function groupsFromMobs(mobs) {
  return (mobs || []).map((m, i) => ({
    pos: [m.x, m.z],
    count: 3 + (i % 3),
    radius: m.radius || 2.4,
  }));
}

// ── 필드 규칙 ──
// AGGRO_RADIUS 7.0
//   ★근거가 되는 카메라가 바뀌었다(옛 주석은 "거리 7 · fov 46" 기준이었다).
//   지금은 고정 쿼터뷰 pitch 0.90 / dist 34 / fov 20 이라 **플레이어 앞이 10.1m 까지**
//   보인다. 어그로 7.0 이면 무리가 화면에 들어온 뒤 3m 를 더 걸어야 달려든다.
//   즉 **보고 나서 판단할 시간**이 있다. 더 넓히면 화면에 들어오기도 전에 달려들고,
//   더 좁히면 무리 한가운데까지 걸어 들어가야 반응해서 회피 선택이 사라진다.
const AGGRO_RADIUS = 7.0;
// LEASH_DIST 24.0 (자기 자리에서 이만큼 멀어지면 포기하고 귀환)
// ★16.0 이었다. 건틀릿 1회차 손맛 8번 지적: "추격이 달리기만으로 끊겨 수풀이 무용".
//   실측하면 이유가 분명하다. 플레이어 달리기 3.20 · 옛 요괴 1.72~2.13 이라
//   **직선으로 8초만 달리면** 요괴 자리에서 16m 가 넘어 무리가 통째로 포기했다.
//   수풀에 들어갈 이유가 없다 = 맵의 절반(수풀)이 장식이 된다.
//   그래서 두 손잡이를 같이 돌린다.
//     · 속도(아래 e.speed)를 걷기<요괴<달리기 대역 한가운데로 올린다
//     · 리쉬를 24 로 늘려 "거리로 떼어내기"를 느리고 비싸게 만든다
//   대신 **수풀은 그대로 즉효**다(LOSE_SIGHT 1.5초로 확실히 끊긴다).
//   위험: 무리 간격이 17m 이상이라 24 면 A무리를 B무리 자리까지 끌고 갈 수 있다.
//   그래도 B는 **플레이어가 자기 7m 안에 들어와야** 붙으므로 자동 연쇄는 아니다.
const LEASH_DIST = 24.0;
// GROUP_RESPAWN 25초
//   한 무리를 정리하고 다음 무리로 넘어가기엔 충분히 길고,
//   되돌아왔을 때 맵이 텅 비어 있지 않을 만큼은 짧다.
const GROUP_RESPAWN = 25.0;
const RETURN_HEAL = 1.2;        // 귀환 중 초당 체력 회복
// LOSE_SIGHT 1.5초 (쫓던 중에 플레이어를 놓치면 이만큼 버티다 포기한다)
//   ★수풀 은신이 실제로 도망 수단이 되려면 이 값이 필요하다. 0 이면 수풀에 들어간
//   순간 무리가 멈춰서 우스꽝스럽고, 길면 숨어도 계속 몰려와 은신이 무용지물이 된다.
//   1.5초면 요괴 속도 1.85m/s 기준 약 2.8m 를 더 밀고 들어온다 = "마지막 본 자리까지
//   와 보고 없으면 돌아간다"로 읽힌다.
const LOSE_SIGHT = 1.5;
// ── 수색(두리번) ──
// 시야를 잃은 뒤 마지막 목격 지점에서 서성이는 시간. 개체마다 이 사이에서 뽑는다.
//   1.5초는 "잠깐 두리번"이 눈에 남는 최소치고, 2.5초를 넘기면 숨은 쪽이 지루해진다.
//   개체마다 다르게 잡아야 넷이 동시에 홱 돌아서지 않는다(그건 다시 스위치로 읽힌다).
const SEARCH_MIN = 1.5, SEARCH_MAX = 2.5;
// 두리번거리는 각(±라디안)과 왕복 속도. 0.9rad = ±52도. 목을 돌려 좌우를 훑는 폭이다.
const SEARCH_SWEEP = 0.9;
const SEARCH_RATE = 2.4;
// 마지막 목격 지점까지 이만큼 안으로 들어가면 멈춰서 두리번거린다.
const SEARCH_ARRIVE = 1.2;
// ★수색 이동속도는 **절대값**으로 못박는다(e.speed 의 비율이 아니다).
//   클립 갈래가 want 1.05 에서 갈리는데, 추격 속도를 올리면 비율식(0.45배)이
//   1.1 을 넘어 **Run 클립**이 돌아서 "놓친 놈"이 "쫓는 놈"으로 보인다.
//   실제로 옛 주석이 그 사고를 기록해 뒀고, 이번 속도 상향으로 그 조건이 되살아났다.
const SEARCH_SPD = 0.92;

// ── 규모 ──
// 맵의 무리 자리가 10군데(level1.json mobs[])라 배치 합계는 39다.
// 무리 간격이 17m 이상이고 어그로가 7m 라, 동시에 쫓아오는 건 많아야 두 무리(9마리)다.
// 풀은 성능 실측(stress)에서 40마리를 한 번에 세울 수 있게 넉넉히 잡는다.
const MAX_ENEMIES = 64;
// 동시에 남는 시체. 한 구가 **두 동강**이라 메시가 두 벌 필요하다(아래 CORPSE 절).
// 3연타 한 스윙에 최대 3~4마리가 같이 죽는 걸 봤다. 6이면 그게 두 번 겹쳐도 안 밀린다.
const MAX_CORPSES = 6;
// ── 시체 먹 소멸 타이밍 (v84 QA S9) ──
// ttl 1.55 안에서: 0~0.42 쓰러짐 · 0.80~1.55 먹으로 흩어짐 · 마지막 0.20 알파 꼬리.
// 쓰러지는 그림(두 조각 벌어짐)이 끝나고 한 박자 두고 시작해야 두 연출이 안 겹친다.
const DIS_START = 0.80;
const DIS_TAIL = 0.20;
// 흩어짐이 훑고 지나갈 높이(m, size 1 기준). 다 쓰러진 몸은 누워 있어서 세로로
// 1.3m 가 아니라 40cm 남짓이다. 서 있는 키로 잡으면 문턱이 몸 위를 안 지나간다.
const DIS_H = 0.55;
// ── 처치 순간 먹 파열 (v84 QA S9) ──
// 한 마리에 8조각. 상한 40이면 3연타로 네 마리를 같이 베어도(32) 안 밀린다.
const INK_MAX = 40;
// ★8 -> 13 (17차 처치 팝). 여덟 점은 34m 쿼터뷰에서 한 뭉치로 뭉쳐 "터졌다"가 아니라
//   "얼룩이 하나 생겼다"로 읽혔다. 상한(INK_MAX 40)이 세 번의 처치를 담으므로 13이면
//   연속 처치에서도 앞선 것이 안 밀린다. 색·수명·크기는 그대로다(생존 중 먹 튀김과 같은 집안).
const INK_PER_KILL = 13;
const INK_TTL = 0.46;
// 고블린 오브젝트(뼈+믹서) 상한. 살아 있는 놈 + 시체가 각각 하나씩 들고 있다.
const MAX_VIS = MAX_ENEMIES + MAX_CORPSES;

// ---------------------------------------------------------------------------
// ★머리 위 판 두 장 — 체력 바 · 인지 표식
// ---------------------------------------------------------------------------
// 둘 다 **월드 빌보드**다. DOM 으로 하면 40마리분 좌표를 매 프레임 투영해서
// style 을 써야 하고(레이아웃 40회/프레임), 3D 로 하면 정점 버퍼 한 벌에 다 들어가
// **드로우콜 1**로 끝난다. 먹 파편(inkMesh)이 쓰는 것과 같은 수법이다.
//
// 크기 근거(실측 산수). 고정 쿼터뷰 fov 20 · dist 34 라 화면 높이 760px 이
// 대상 평면에서 2*34*tan(10도) = 11.99m 다. 즉 **1m = 63px**.
//   · 고블린 키 1.30m = 82px
//   · 체력 1 = 0.22m = 14px, 3체력 바 = 0.66m = 42px  (몸 높이의 절반)
//   · 표식 0.62m = 39px  (느낌표 한 글자가 이 정도는 돼야 34m 에서 읽힌다)
// ★2026-08-13 오너 지시로 칸 그림을 걷어냈다("세 칸이 합쳐진 느낌 말고 그냥 하나의 바").
//   PIP_W 는 이제 **체력 1 이 차지하는 길이**다 - 값도 뜻도 그대로고, 그 길이 안을
//   칸으로 쪼개 그리던 셰이더 구역만 없앴다.
//
// ── ★★폭을 고정한다 (오너 지시 2026-08-13 밤. 「길이 = 튼튼함」 설계 기각) ──
// 오너 원문: "어떤 고블린은 체력바가 왜이리 작아? 체력바길이는 동일하게하고 가운데
//            구분선을 넣어서 체력이 가늠되게하던가 뭐 그래야할거같은데
//            체력별로 체력바길이 다르게 하려했어?"
// 그렇다. 그러려던 것이었고 **기각됐다.** 「폭 = maxHp x PIP_W」는 화면에서 이렇게 나왔다
// (실측, 960x640 뷰포트 = 1m 62.7px):
//     리더 3핍 41.5px  ·  일반 2핍 27.9px  ·  일반 1핍 **13.9px**
// 1핍 잡몹이 전체의 60% 인데 그 놈의 바는 **리더의 3분의 1**이고, 몸통보다 짧아서
// 「바」가 아니라 「점」으로 읽혔다. 설계가 답하려던 질문("몇 대 더 때려야 하나")은
// 옳았는데, 그 답을 **바의 존재감**과 맞바꾼 것이 잘못이었다 - 바는 먼저 바로 보여야 한다.
//
// 새 계약(롤 미니언 바 문법): **폭은 한 값 · 채움은 hp/maxHp 비율 · 눈금이 타수를 센다.**
//   · BAR_W 는 옛 2핍 폭(0.22 x 2)과 **같은 값**이다. 즉 2핍 잡몹의 바는 이번 변경으로
//     화소 하나 안 움직인다(A/B 에서 그 한 줄이 자 노릇을 한다).
//   · 오너 화면(1512x950, 1m = 93px)에서 41px. 고블린 키 1.30m = 121px 의 1/3 이다.
//   · 촬영 뷰포트(640px)에서는 27.9px 라 리더 6칸이 칸당 4.7px 로 빠듯하다 -
//     **눈금 판정은 실측 해상도를 같이 적어야 한다**(아래 hpbar_fixed 하네스).
const BAR_W = 0.44;             // ★바 폭(m). 몹 종류와 무관하게 한 값이다 (= 옛 PIP_W 0.22 x 2)
// ── ★눈금(구분선) — 한 대가 한 칸이다 ──
// 폭을 고정하면 「몇 대 더 때려야 하나」를 길이가 못 말한다. 그 말을 눈금이 대신한다.
// 칸 수는 **maxHp / 칼 한 대**라서 18차 데미지 반감(SWORD_DMG 0.5)이 그대로 반영된다:
//     1핍 2칸 · 2핍 4칸 · 리더 3핍 6칸   (경계선은 칸 수보다 하나 적다)
// DMG_SCALE 을 1 로 되돌리면 칸 수도 저절로 1/2/3 으로 돌아간다(상수 하나도 안 고친다).
// ★17차가 걷어낸 「칸 그림」으로 되돌아가면 안 된다. 그때 기각된 것은 **채움을 칸으로
//   쪼개고 칸 사이에 트랙색 홈을 판** 그림이었다("딱 세 칸이 합쳐진 느낌"). 여기 눈금은
//   홈이 아니라 **채움 위에 겹치는 가는 값**이다 - 채움 자체는 끊기지 않고 이어진다.
const BAR_TICK_HW = 0.050;      // 눈금 반폭(판 높이 = 1 단위. 11px 바에서 약 1.1px)
const BAR_TICK_AA = 0.030;      // 그 경계를 눕히는 폭(상수. fwidth 는 GLSL1 확장이라 안 쓴다)
// ★눈금의 **세기**. 첫 판은 잉크(선형 0.005)를 박았더니 실측 열 밝기가 207 -> 6 으로
//   떨어져 채움에 검은 슬릿을 판 그림이 됐다 = 17차가 기각한 「칸이 합쳐진 느낌」의 재발.
//   그래서 절대색이 아니라 **자기 색의 배수**로 바꿨다 - 눈금은 잉크가 아니라 그림자다.
//   채움 위(그림자)와 빈 트랙 위(한 단계 밝은 값) 둘 다 바탕에서 파생하므로 색이 안 는다.
const BAR_TICK_MUL = 0.34;      // 채움 위 눈금 = 그 자리 색 x 이 값
const BAR_TICK_LIFT = 2.6;      // 빈 트랙 위 눈금 = 트랙색 x 이 값(어두운 데선 밝혀야 보인다)
// ★0.105 -> 0.145. 첫 실사 스크린샷에서 칸 높이가 7px 이라 속(찬 칸/빈 칸)을 나누는
//   띠가 3px 밖에 안 나왔다 = 찼는지 비었는지 구별이 안 됐다. 9px 이면 속이 5px 다.
// ★0.145 -> 0.175 (17차 UI 통일). 카드 문법은 **1px 헤어라인**이 형태를 정의하는데,
//   9px 짜리 바에서 위아래 헤어라인 2px 을 빼면 속이 7px 이라 그러데이션이 안 선다.
//   11px 이면 속이 9px 이라 채움이 띠로 읽힌다.
const PIP_H = 0.175;            // 바 높이(m)
// 피격 뒤 이만큼만 떠 있는다. 상시로 두면 40개 바가 화면을 덮어 롤 HUD 가 아니라
// MMO 가 된다. "때린 놈만 잠깐"이 이 게임의 밀도에 맞는다.
const PIP_SHOW = 1.2;
const PIP_FADE = 0.25;          // 마지막 0.25초에 걷힌다
// 표식 판 크기(m). 정사각형이다.
const MARK_SZ = 0.62;
// 표식 종류(텍스처 아틀라스 칸 번호). 0=! 1=? 2=공격 쐐기
const MARK_NONE = -1, MARK_EX = 0, MARK_Q = 1, MARK_ATK = 2;
// ── ★공격 쐐기(머리 위 삼각형) 스위치 (오너 지시 2026-08-13) ──
// "고블린 머리위에 삼각형 표시뜨는거 없애줘."
// 9차 A-3 이 넣은 예고 삼종(자세·번득임·머리 쐐기) 중 **머리 쐐기 한 갈래만** 끈다.
//   · 끄는 것은 시각물 하나뿐이다. 예고 시계(ATK_WIND 0.30 + 타격 0.575 = 0.875초)·
//     예비 자세·호박 번득임·경직·넉백은 한 줄도 안 건드렸다 = 밸런스 무변경.
//   · e.wndT 자체도 그대로다. 자세·번득임·공격 취소가 전부 이 시계를 읽는다.
//   · 인지 표식(! / ?)은 남는다. 은신이 성립하려면 "쟤가 나를 놓쳤다"가 보여야 한다.
// 되살리려면 이 한 줄을 true 로. 아틀라스 칸 수(MARK_N)·markOf 분기·UV 가 같이 돌아온다.
const MARK_ATK_ON = false;
// 아틀라스 칸 수. 쐐기를 끄면 칸을 굽지도 않는다(빈 칸을 남기면 그게 부스러기다).
const MARK_N = MARK_ATK_ON ? 3 : 2;
// 상태별 표시 시간
const MARK_FOUND = 1.4;         // 발견(!) 이 떠 있는 시간
const MARK_LOST_FADE = 0.9;     // 포기(? 페이드)

// ---------------------------------------------------------------------------
// ★큰 데미지 숫자 (오너 지시 2026-08-12)
//   "칼 휘두를 때 상대 흰색으로 번쩍이게 하지 말고 데미지를 보여줘.
//    메이플스토리나 로블록스처럼 큰 글자로."
// ---------------------------------------------------------------------------
// 위 두 판(핍·표식)과 **같은 틀**이다 - 캔버스에 구운 아틀라스 + 월드 빌보드 판.
// DOM 으로 하면 한 프레임에 여러 뭉치의 좌표를 투영해서 style 을 써야 하고,
// 스프라이트로 하면 드로우콜이 자릿수만큼 늘어난다. 여기서는 자리 한 칸이 판 한 장,
// 전부 정점 버퍼 한 벌 = **드로우콜 1**이다.
//
// 크기 근거(실측 산수. 현행 카메라는 fov 24 · dist 24 다 - 위 핍 주석의 fov 20/dist 34
// 는 옛 값이라 그대로 믿으면 안 된다):
//   대상 평면의 화면 높이 = 2 * 24 * tan(12도) = 10.20m → 720px 화면에서 **1m = 70.6px**
//   칸 높이 0.62m = 44px, 그 안의 글자 획이 대략 0.49m = **35px**
//   → 지시서의 "게임 거리에서 28~40px" 대역 한가운데다. 처치타는 1.35배(=47px).
// ── ★크기 재조정 (17차. 이펙트 비평가) ──
// 지적 그대로: "데미지 숫자 100 이 참격보다 크다 — 고블린 머리의 3배, 그게 동시에 넷."
// 자를 대고 확인했다. 고블린 전체 키 GOB_H = 1.30m 이고 머리는 그중 대략 0.30m 다.
//   옛 값 0.62m = 머리의 2.07배, 처치타는 x1.35 = 0.84m = **머리의 2.8배**.
//   세 자리("100")가 가로로 늘어서면 몸통보다 넓은 판이 되어 참격 획을 덮는다.
// 새 계약: **명중 = 머리 1.13배 · 처치 = 머리 1.47배**(오너 지시 "1~1.5배 수준").
//   0.34m = 머리의 1.13배. 720px 화면(1m = 70.6px)에서 칸 24px · 글자 획 약 19px.
//   지시서의 옛 대역(28~40px)보다 작지만 그 대역은 "숫자가 주인공"이던 시절 값이고,
//   지금 계약은 **참격이 주인공**이다.
// ★수치 체계(전부 100)는 오너 판정 대기 중이라 한 글자도 안 건드렸다. 크기만이다.
const DMG_H = 0.34;             // 숫자 한 칸의 세로 크기(m). 이 한 숫자가 크기 손잡이다
const DMG_KILL_SC = 1.30;       // 처치타는 더 크다(메이플 크리티컬 문법). 0.442m = 머리 1.47배
// ★0.30 -> 0.46 (17차). 이펙트·UI 비평이 같이 지적한 "숫자가 참격 리본을 덮는다".
//   숫자는 벤 자리에 떠야 한다는 계약(아래 spawnDmgPop 주석)은 그대로 두고, 칼날이
//   지나간 평면에서 16cm(화면 10px)만 위로 뺀다. 자리의 뜻은 안 바뀌고 리본만 비운다.
const DMG_ANCHOR_Y = 0.46;      // 명중 지점보다 이만큼 위에서 시작한다
// ── ★뜨는 시각을 한 박자 늦춘다 (17차) ──
// 같은 지적의 나머지 절반은 **타이밍**이다. 여태 숫자는 칼이 닿은 그 프레임에 떠서
// 참격 획(feel.js SW_N = 4/24 = 0.167초)의 첫 프레임부터 위에 얹혔다.
// ★이 시계는 게임시간이다. 즉 히트스톱(70~112ms) 동안에는 **거의 안 흐른다.**
//   그래서 이 한 줄이 "멈춘 임팩트 프레임에는 숫자가 없다"를 만든다 —
//   정지 화면에는 벤 자세와 획만 남고, 시간이 풀리면서 숫자가 튀어오른다.
//   벽시계로는 타격 후 약 140~180ms 다(정지 + 이 지연).
const DMG_DELAY = 0.07;
// 모션 세 마디. 톡 튀어오르고(0.10) · 잠깐 서고(0.30) · 흐려지며 오른다(0.30).
const DMG_RISE = 0.10, DMG_HOLD = 0.30, DMG_FADE = 0.30;
const DMG_TTL = DMG_RISE + DMG_HOLD + DMG_FADE;
const DMG_UP1 = 0.42;           // 튀어오르는 높이(m)
const DMG_UP2 = 0.55;           // 흐려지며 더 오르는 높이(m)
const DMG_MAX_POP = 20;         // 동시에 떠 있는 숫자 뭉치 상한
const DMG_MAX_DIGITS = 5;       // 한 뭉치 최대 자릿수(99999)
// 이 반경 안에 이미 떠 있는 뭉치 수만큼 옆·위로 비킨다(다중 명중 겹침 방지)
// ★1.6 -> 2.2 (17차). 광역타로 넷을 한 번에 베면 네 뭉치가 서로 1.6~2.1m 떨어진 자리에
//   떠서 **서로를 이웃으로 안 세고** 넷 다 ox=0 에 겹쳐 섰다(비평가 "동시 4개").
//   무리 하나가 서는 폭이 대략 2m 라 반경을 그 위로 올려야 같은 사건으로 묶인다.
const DMG_NEAR = 2.2;
// ── ★화면에 띄우는 수는 무엇인가 ──
// 이 게임의 잡몹 체력 단위는 **핍**이다(maxHp 1~3). 화면에 "1"을 띄우면
// 큰 글자의 값어치가 없으므로 100 배 해서 띄운다. 이건 각색이 아니라 **단위 환산**이다
// (m → cm 와 같다). 그래서 화면의 수와 실제로 깎인 체력은 언제나 SWORD_DMG·DMG_SHOW
// 한 곱셈으로 이어져 있다 - 나중에 무기별 피해나 소수 피해가 생기면 여기 손 안 대고
// 숫자가 저절로 따라간다.
//
// ── ★칼 데미지 반감 (오너 지시 2026-08-13 "칼 데미지 반으로 줄이고") ──
// **손잡이는 이 한 줄뿐이다.** DMG_SCALE 을 1 로 되돌리면 18차 이전 밸런스가
// 한 글자도 안 다르게 그대로 돌아온다(아래 파생 세 곳이 전부 이 값에서 나온다).
//
// 왜 「몹 체력을 2배로」가 아니라 「칼 데미지를 0.5로」인가:
//   ① 체력 분포(leader 3 / 일반 2·1)는 스폰·리더 개념과 묶인 밸런스 축이라 안 건드린다.
//   ② 머리 위 바의 길이 계약(당시: 핍 1 = PIP_W = 0.22m)이 그대로 산다. maxHp 가
//      안 변하니 **바의 물리적 크기가 화소 하나 안 바뀐다.** 체력을 2배로 올렸다면
//      리더 바가 0.66m -> 1.32m 로 두 배가 돼서 PIP_W 까지 같이 손봐야 했다(회귀 두 배).
//      ★그 길이 계약은 같은 날 밤 오너가 기각했다(BAR_W 주석). 지금 이 항의 값어치는
//        「바 크기」가 아니라 **눈금 칸 수**로 옮겨 갔다 - DMG_SCALE 이 곧 칸 수의
//        분모라, 1 로 되돌리면 칸도 2/4/6 에서 1/2/3 으로 저절로 돌아간다.
//   ③ 귀환 회복(RETURN_HEAL, 초당 핍)도 핍 단위라 **완치까지 걸리는 벽시계 시간이
//      그대로다.** 체력을 2배로 올렸다면 회복도 같이 2배로 올려야 했다.
//   ④ 0.5 는 IEEE754 에서 정확히 표현되므로 3 - 0.5×6 = 0 이 **오차 없이** 성립한다.
//      (e.hp <= 0 처치 판정에 엡실론이 필요 없다. 0.3 같은 값이면 필요했다.)
// 대신 「핍 1 = 한 대」가 깨지므로 그 가정에 기대던 자리 두 곳을 SWORD_DMG 로 다시
// 적었다: 바를 띄우는 조건(아래 updatePlates)과 붉어지는 문턱(pip 셰이더).
//
// ★보스는 안 건드렸다. boss.js 가 자기 체력·피해를 따로 갖는 별도 체계다
//   (MAX_HP 60 / Z 3 / X·C 5 = 20타·12타). 이 파일의 핍과 공유하는 상수가 없어서
//   여기를 바꿔도 보스는 한 톨도 안 움직인다. 보스도 반감할지는 오너 판정 영역.
const DMG_SCALE = 0.5;          // ★칼 데미지 배율. 롤백 손잡이(1 = 18차 이전)
const SWORD_DMG = 1 * DMG_SCALE; // 칼 한 대가 깎는 체력(핍). e.hp 는 이 단위로 산다
const DMG_SHOW = 100;           // 화면 환산 배수. 핍 1 = 100 (한 대 = 50 이 뜬다)

// ── 전투 수치 ──
const PLAYER_MAX_HP = 100;
// ★8 -> 6 (건틀릿 1회차 손맛). 목표 체감은 "3마리 캠프를 풀피로 붙어서 이기고
//   30 안팎을 쓴다". 8 이면 3~4대만 맞아도 체력 3분의 1이 날아가서, 캠프 하나를
//   정리하는 게 판돈이 너무 큰 도박이 됐다. 아래 DMG_LEAK 이 이 값에서 파생되므로
//   초당 상한(= 겹쳐 맞을 때의 천장)도 10 -> 7.5 로 같이 내려간다.
//   ★공격 예고(ATK_WIND)가 새로 붙어 한 대당 주기가 0.30초 길어진 것도 같이 먹는다.
const ENEMY_DMG = 6;
// 피격 후 무적.
// ★0.65 였다. 그 값이 v72 QA 가 지적한 "메트로놈"의 진짜 원인이다. 네 마리가 때려도
//   첫 대 말고는 전부 0.65초 안에 삼켜져서 화면에 한 번밖에 안 나타났다. 그래서
//   마릿수가 체감에서 통째로 사라지고, HP 는 일정한 박자로만 깎였다.
//   지금은 총량을 아래 새는 통(DMG_LEAK)이 따로 묶으므로, 무적은 **연출이 겹치지
//   않을 만큼만** 있으면 된다.
// 0.30 인 이유: 요괴 공격 주기가 1.2초다. 넷이 고르게 흩어지면 타격 간격이 0.30초라
//   0.30 이면 **넷이 다 통과한다**(0.4 면 한 놈이 통째로 지워져 셋으로 읽힌다).
const PLAYER_IFRAME = 0.30;
// 피격 넉백(m). 0.15 는 발이 반 걸음 밀리는 정도라 조작을 못 뺏으면서 몸으로 읽힌다.
const PLAYER_KB = 0.15;
const ENEMY_ATK_CD = 1.2;
// 공격 쿨 흔들림. 매번 정확히 1.2초면 한 번 박자가 맞은 무리는 **영원히** 맞은 채로
// 때린다(= 넷이 한 놈처럼 들린다). ±18% 를 흔들어 저절로 어긋나게 둔다.
// 평균은 그대로 1.2초라 마리당 DPS 는 안 변한다.
const ATK_CD_JITTER = 0.18;
// ★적이 멈춰서는 거리. 칼끝이 캐릭터 앞 약 1.4m 까지 닿는데(실측) 예전엔 이 값이
// 1.15 + 몸집보정 0.35 라 딱 1.43m 에서 멈췄다. 즉 **칼끝 끄트머리에 겨우 걸리는**
// 자리에 서서, 정면으로 안 서면 헛스윙이 났다. 확실히 안쪽으로 들어오게 줄인다.
const ENEMY_ATK_RANGE = 0.95;
const ENEMY_ATK_SIZE = 0.25;
// 죽고 되살아나기까지(게임시간 초).
// ★1.6 -> 2.6 (v84 QA S2). 1.6초는 「落」카드가 아직 화면에 떠 있는 동안에
//   **리스폰 텔레포트가 일어나는** 길이였다. 실측(headed, 2026-08-10):
//     t=1.82s 죽어 있음 + 카드 떠 있음, 자리 (-22.72, 29.66)
//     t=2.27s 되살아남 + **카드 아직 떠 있음**, 자리 (-31.68, 36.80)  <- 여기가 사고다
//     t=2.67s 카드 내려감
//   플레이어 눈에는 "죽었다"가 아니라 "화면이 어두워지더니 다른 데로 튕겨났다"로
//   읽힌다. 그래서 순서를 갈랐다: 카드가 **다 걷힌 뒤에** 몸이 움직인다.
//   ui.js 는 이 값을 window.__enemy.deadIn 으로 읽어 카드를 먼저 내린다.
// ★게임시간이다. 죽는 순간 feel.death() 가 1초 동안 0.30배로 늘어뜨리므로
//   벽시계로는 약 2.6 + 0.7 = 3.3초가 된다(의도한 늘어짐이다).
const RESPAWN_DELAY = 2.6;
// ── 카드를 걷기 시작하는 시점 (deadUntil 까지 남은 게임시간 초) ──
// ★0.70 -> 0.12 (v88 QA S3). v84 에서 "카드가 다 걷힌 뒤에 몸이 움직인다"로 뒤집었는데,
//   그러자 이번엔 **걷힌 자리에 시체가 서 있는 1초**가 새로 생겼다(v88 QA 실측).
//     0.70 에 걷기 시작 -> 0.4초 페이드 -> 0.3초 동안 죽은 자리에 그대로 서 있음
//     -> 그제서야 스폰으로 순간이동. "일어났다가 튕겨났다"로 읽힌다.
//   고칠 곳은 순서가 아니라 **겹침의 방향**이다. 카드가 아직 짙을 때 몸이 옮겨져야
//   "어둠 속에서 깨어나니 스폰"이 된다. 0.12 면 페이드(0.4초)의 앞 30% 안에서
//   텔레포트가 끝나므로 그 순간 카드 투명도는 아직 0.6 이상이다(CSS ease).
//   ★ui.js 폴링이 50ms 라 실제 발화는 0.07~0.12 사이다. 그래도 전부 페이드 앞머리다.
//   ★0 으로 두면 안 된다. 텔레포트와 동시에 걷히기 시작해서 이동이 그대로 보인다.
const RESPAWN_CARD_LEAD = 0.12;

// ── 공격 방향 스냅 ──
// ★이 게임에서 제일 크게 잘못돼 있던 것. 요괴 넷이 몸에 겹쳐 있어도 바라보는 각이
//   어긋나면 Z 를 12번 눌러 1킬이 나왔다(v72 QA 실측). 칼날 선분 판정은 정직해서
//   "안 닿으면 안 맞는다"가 맞는데, **입력한 사람은 겹친 적을 벤다고 믿는다.**
//   그 간극을 여기서 메운다. 공격 입력 순간 반경 안의 가장 가까운 적으로 몸을 돌린다.
// SNAP_R 2.6: 칼끝이 캐릭터 앞 1.4m 까지 닿고 요괴 캡슐 반경이 0.4다. 2.6이면
//   "몸을 돌리면 벨 수 있는 놈"까지만 잡고, 저만치 있는 놈에게 끌려가지 않는다.
const SNAP_R = 2.6;
// SNAP_DUR 0.09초. 즉시(0)와 나란히 놓고 실측해 골랐다. 0 은 한 프레임에 180도가
//   돌아가 목이 꺾인 것처럼 보이고, 0.15 이상이면 1타의 칼이 이미 나간 뒤에 몸이
//   따라와 헛스윙이 남는다. 0.09 는 Attack 크로스페이드(0.06)와 거의 겹쳐서
//   "휘두르면서 돈다"로 읽힌다.
const SNAP_DUR = 0.09;

// ── 피격 판정 ──
// swordFast(칼끝 속도 정규화값)가 이 값을 넘는 동안만 '베는 중'이다.
// main.js 의 궤적(trail)은 swordFast 0.28 부터 보이고 물보라는 0.39 부터 튄다.
// 판정을 0.40 으로 두면 **눈에 보이는 궤적이 진해지는 구간**과 거의 정확히 겹친다.
// 히스테리시스(끄는 값을 낮게)를 두는 이유: 한 번 휘두르는 중에 값이 임계선에서
// 떨면 스윙 번호가 새로 발급돼 같은 적을 두 번 때리게 된다.
const HOT_ON = 0.42;
const HOT_OFF = 0.16;
const BLADE_PAD = 0.14;         // 칼날 굵기 보정
// ★스윙 번호 최소 간격.
// 히스테리시스만으로는 모자랐다. 실측(400fps 로 돌려본 최악 조건)에서 검사 Attack
// 클립 한 번에 스윙 번호가 **5개** 발급됐다. 칼끝 속도는 |Δ위치|/dt 라 프레임이
// 짧을수록 노이즈가 커지고, 임계선 근처에서 켜졌다 꺼졌다 한다.
// 그러면 한 번 휘두른 걸로 같은 적을 5번 때린다(3체력 적이 한 방에 죽는다).
// 사람이 낼 수 있는 연타 간격보다 짧은 재발급은 전부 같은 스윙으로 친다.
//
// ── 2026-08-10 9차: 0.22 -> 0.12 요청을 **기각**했다 (handoff_combat A-2) ──
// 요청 취지: main.js 의 연타 바닥(ATK_MIN_GAP 0.24)을 같이 내려 연타를 빠르게.
// 실측(headed, Z/X/C 각 5회 x 두 조건. 원자료 renders/history/v94_wave9/soban_enemy/):
//   · 3연타 클립 한 번의 **진짜 획 간격** = 0.289 ~ 0.390초
//   · 같은 클립에서 나온 **떨림(노이즈 재점화) 간격** = 0.039 ~ 0.128초
//   → 안전대는 0.128 < SWING_GAP < 0.289 다. 0.22 는 이 안에 있다.
//   → 0.12 는 떨림 상한(0.128) **아래**다. 실제로 60fps Z 5회 중 1회가
//     획 3개짜리 클립에 스윙 번호를 **4개** 발급했다(= 같은 요괴를 한 번 더 벤다).
//     이건 이 값이 막으라고 있는 사고 그 자체다.
//   ★프레임률을 올린 조건(__slow 0.25 = dt 1/4 = 240fps 상당)에서 떨림이 더 촘촘해진다.
//     즉 이 상한은 기계마다 달라진다 - 0.12 는 어느 기계에서 깨질지 모르는 값이다.
// 지금 구멍은 없다: main.js 바닥이 0.24 > 0.22 라 "보이는데 안 들어가는 스윙"은 안 난다.
//
// ── 0.14~0.17 연타를 정말 원하면 숫자가 아니라 **규칙**을 바꿔야 한다 ──
// 같은 실측에서 "hot 이 꺼져 있던 길이"로 재면 둘이 깨끗하게 갈린다:
//   떨림 0.004 ~ 0.064초 (12건)  /  진짜 획 0.078 ~ 0.304초 (22건)  <- 사이가 비어 있다
// 즉 **꺼짐이 0.07초 이상 이어진 뒤에 켜진 것만 새 스윙으로 인정**하면, 연타 속도에
// 상한을 걸지 않고도 떨림만 걸러진다(모양으로 거르므로 프레임률에 안 흔들린다).
// 그 규칙으로 바꾸면 SWING_GAP 은 0.07 근처까지 내려갈 수 있고 ATK_MIN_GAP 도 따라온다.
// ★단, 판정 정직성 계약(handoff_combat 0장)을 다시 재야 하는 변경이라 main.js 소유자와
//   **같이** 해야 한다. 갈아 끼우며 재는 창구는 api.setSwingGap(v) 로 열어 뒀다.
let SWING_GAP = 0.22;

// ---------------------------------------------------------------------------
// 덩어리 메시 — ★지금은 **보스 폴백 전용**이다.
// 잡몹은 고블린 glb 로, 보스는 boss.glb(각귀 실모델)로 갈아탔다. 이 지오메트리는
// boss.js 가 boss.glb **로드에 실패했을 때만** 2.6배로 키워 쓰는 비상용으로 남는다.
// 평상시에는 화면에 한 조각도 안 나온다.
// 여기 손대면 그 폴백 판정(중심 y 1.65 / 반경 1.43)이 같이 틀어진다. 건드리지 말 것.
// ---------------------------------------------------------------------------
const BODY_CY = 0.50;        // 로컬 몸통 중심 y. boss.js 가 같은 값을 들고 있다
// ★임시다. 최종 아트가 아니라 실루엣·연출 확인용 플레이스홀더다.
// 한국 도깨비 느낌으로 뿔·부라린 눈·송곳니를 넣었다. 몸은 어둡게 깔아
// 눈이 블룸에 걸려 먼저 읽히게 한다(어두운 배경에서 요괴가 다가오는 그림).
//
// 삼각형 예산: 몸 320 + 아랫자락 16 + 뿔 12x2 + 눈두덩 8x2 + 눈 32x2 +
//              입 8 + 송곳니 4x4 = 464. (상한 600)
// ★형태 조건: **볼록한 덩어리**를 유지해야 한다. 죽을 때 임의 각도 평면으로
//   자르는데, 오목하거나 팔다리가 뻗은 형태면 잘린 단면이 엉망으로 읽힌다.
//   그래서 특징(뿔·눈·이빨)은 전부 덩어리 표면에 얕게 붙이는 방식으로만 넣었다.
// 뼈 없음. 통통 튀기와 기울기는 전부 코드가 만든다.
const COL_BODY = new THREE.Color(0x1b2438);
// 뿔은 원래 뼈색(밝은 베이지)이었는데, 몸이 어두워서 뿔만 형광처럼 튀고
// 눈이 안 보였다. 눈이 초점이어야 하므로 뿔은 몸에서 한 단만 밝게 둔다.
const COL_HORN = new THREE.Color(0x6d6152);
const COL_BROW = new THREE.Color(0x3d3a36);
const COL_EYE = new THREE.Color(0xff5a24);
const COL_SKIRT = new THREE.Color(0x0d1220);
const COL_MOUTH = new THREE.Color(0x1a0408);
const COL_FANG = new THREE.Color(0xc9bfa6);

// ---------------------------------------------------------------------------
// ★몸집과 피격 판정 — 이 파일에서 제일 중요한 수치다
// ---------------------------------------------------------------------------
// 검사가 칼을 휘두르면 칼끝이 높이 **1.20 ~ 2.48** 을 지난다(브라우저 실측).
// 임시 요괴(덩어리)는 바닥에 두면 칼이 통째로 머리 위를 지나가 한 대도 안 맞아서
// HOVER_Y 0.62 로 **띄워** 놨었다. 고블린은 제대로 된 캐릭터라 띄우면 공중부양이
// 그대로 보인다. 그래서 **판정을 구에서 세로 캡슐로 바꿨다.**
//
//   구  : 중심 하나 + 반경 하나. 세로로 덮으려면 반경을 키워야 하고, 키우면
//         옆으로도 같이 커져서 허공을 베도 맞는다.
//   캡슐: 발~머리를 잇는 **선분** + 반경. 세로는 선분이, 옆은 반경이 따로 맡는다.
//         칼날도 선분이므로 판정은 **선분 대 선분 최단거리** 한 번이면 끝난다.
//         칼이 정수리 살짝 위를 지나도 위쪽 반구 안이라 맞는다.
//
// 게임 키 1.30 (플레이어 1.75 의 74%). 바인드 박스 1.7075 를 이 값으로 정규화한다.
// ★키를 1.2 로 두면 정수리가 1.151 이라 칼끝 최저점(1.20)보다 4.9cm 아래다.
//   1.30 이면 정수리가 1.23~1.29(Idle 실측)로 칼끝 최저점을 넘어선다.
const GOB_BIND_H = 1.7075;   // goblin.glb 바인드 박스 높이(실측)
const GOB_H = 1.30;          // 게임 키(기본값. 개체마다 e.size 를 곱한다)
// 캡슐 선분 = 키의 20% ~ 74% 지점(발목 위 ~ 목 아래). 반경까지 더하면
// y 는 -0.14 ~ 1.36 을 덮는다(키 1.30 기준). 정수리 1.23 보다 13cm 위까지다.
const CAP_LO = 0.20, CAP_HI = 0.74;
// 캡슐 반경 0.40 의 근거(고블린 정점을 스키닝해서 직접 잰 값, 키 1.30 환산)
//   · 몸통(y 0.55~1.45) 표면 반경 중앙값 0.30~0.41 → 0.40 은 몸통을 전부 덮는다
//   · 전체 정점의 75% 가 반경 0.365~0.47 안 → 팔까지 대부분 들어온다
//   · 벽 충돌 반경 ENEMY_R 0.34 보다 크다 → **몸이 부딪히는 놈은 반드시 벨 수 있다**
//   · 임시 요괴의 판정 구는 0.60*scale + 0.14 = 0.61~0.86 이었다. 세로를 선분이
//     맡으니 반경은 오히려 **줄었다**(허공을 베고 맞는 일이 준다)
const CAP_R = 0.40;
// ── 접지 발 속도(키 1.30 기준, 재생속도 1.0) ──
// 발끝 뼈가 지면에 붙어 있는 구간만 골라 수평 속도의 중앙값을 냈다.
//   Walk 0.836 / 0.859   Run 2.607 / 2.692   (좌/우 발)
// 다른 에이전트가 보고한 값(키 1.2 기준 0.66 / 1.97 = 키 1.3 환산 0.715 / 2.134)
// 보다 높다. 클립 자체가 접지 구간에서 속도가 ±20% 흔들려서 재는 방법에 따라 갈린다.
// 두 값 사이에서 **낮은 쪽에 가깝게** 잡는다. 발이 뒤로 미끄러지는 건 덜 보이지만
// 앞으로 미끄러지면(스케이트) 바로 눈에 띈다.
const WALK_FOOT = 0.80;
const RUN_FOOT = 2.35;
// 공격 클립(85프레임 = 2.833초)에서 실제로 쓰는 구간.
// 손 속도를 프레임마다 재보니 **33프레임(1.10초)에서 20.2** 로 최고였다. 그게 타격
// 순간이다. 0~7 은 서 있는 준비 자세고, 35 뒤로는 50프레임짜리 회복 꼬리다.
// 8~46 만 쓰면 "들었다가 내리친다"만 남는다.
const ATK_FROM = 8 / 30, ATK_TO = 46 / 30;
const ATK_TS = 1.45;                       // 재생속도. 창 = (46-8)/30/1.45 = 0.874초
const ATK_HIT_T = (33 - 8) / 30 / ATK_TS;  // 타격까지 0.575초 (= 예고 시간)

// ---------------------------------------------------------------------------
// ★공격 예고 (건틀릿 1회차 손맛 6번 · 포위 3/10: "누가 때리는지 모른다")
// ---------------------------------------------------------------------------
// 옛 구조에는 예고가 **판정상으로만** 있었다. 사거리에 들어오면 곧장 Attack 클립을
// 틀고 0.575초 뒤에 맞았다. 문제는 그 0.575초가 **화면에서 안 읽힌다**는 것이다.
//   · 34m 쿼터뷰에서 1.3m 짜리가 칼을 드는 동작은 몇 픽셀이다
//   · 넷이 몸에 겹쳐 있으면 그 중 누가 클립을 틀었는지 구별이 안 된다
// 그래서 클립보다 **앞에** 정지된 예비 구간을 하나 끼운다. 이 구간에는 셋이 동시에 붙는다.
//   1) 자세: 발을 멈추고 몸을 뒤로 젖히며 살짝 커진다(실루엣이 변한다)
//   2) 번득임: 구간 끝 45% 에서 호박빛 자체발광이 올라온다(피격 흰빛과 색을 갈랐다)
//   3) 머리 표식: 붉은 쐐기(아래 MARK_ATK). 겹쳐 있어도 **누구인지**가 읽힌다
//      ★★이 셋째 갈래는 오너 지시로 꺼졌다(2026-08-13, MARK_ATK_ON = false).
//        예고 시계는 그대로라 1)·2)가 그 일을 계속 한다 = 시간·판정은 무변경이다.
// 0.30초인 이유: 단순 시각 반응 0.25초가 하한이고, 0.35 를 넘기면 예고만 보고
// 걸어서 빠져나갈 수 있어 근접이 무해해진다. 총 예고 = 0.30 + 0.575 = 0.875초.
const ATK_WIND = 0.30;

// ---------------------------------------------------------------------------
// ★피격 리액션 (건틀릿 1회차 손맛 5번: "적이 맞아도 아무 반응이 없다")
// ---------------------------------------------------------------------------
// 경직. 맞은 놈은 이 시간 동안 **발이 멈추고 클립이 거의 얼어붙는다.**
//   · 휘두르던 칼은 취소된다(atkT/hitT/wndT 를 통째로 끊는다) = 때리면 끊긴다
//   · 클립 재생속도를 STUN_TS 로 눌러 "맞은 자세로 멎었다"를 만든다
// 0.13초인 이유: 3연타 사이 간격이 0.28초라 그보다 짧아야 다음 타가 새 반응을
// 만들 수 있고, 0.10 아래면 60fps 에서 8프레임도 안 돼서 눈에 안 남는다.
// ★0.13 -> 0.18 (17차). 실측으로 왜 "반응이 안 보인다"고 읽혔는지 갈랐다:
//   ① 잡몹 60% 가 1체력이라(maxHp = leader?3:(hash<0.4?2:1)) **이 경로 자체를 안 탄다.**
//      한 대에 죽으면 경직도 넉백도 없고 곧장 시체다 = 신규유저의 "벤다가 아니라 지운다".
//      체력 분포는 밸런스라 안 건드린다(오너 판정 영역). 대신 **탈 때 확실히 보이게** 한다.
//      ★18차에 그 오너 판정이 왔다("칼 데미지 반으로 줄이고"). DMG_SCALE 0.5 로
//        **모든 잡몹이 최소 두 대를 버틴다** = 17차가 공들여 키운 이 경직·넉백·스쿼시가
//        이제 한 판에 100% 발화한다. 17차 처방(경직 0.18 · 넉백 0.59m)은 그때
//        "탈 일이 드무니 탈 때만이라도 크게"로 정한 값이라, 매 타격에 도는 지금도
//        과한지 다음 손맛 파도가 실전투로 재판할 것(숫자는 이번에 안 건드렸다).
//   ② FLASH_R/G/B = 0(오너 지시)이라 색 신호가 통째로 없다. 그러니 남은 신호는
//      경직·넉백·스쿼시 셋뿐인데 그게 다 60~130ms 라 히트스톱(55ms)에 거의 다 먹혔다.
//   0.18 은 3연타 간격(0.28초)보다 여전히 짧아서 다음 타가 새 반응을 만든다.
const HIT_STUN = 0.18;
const STUN_TS = 0.08;           // 경직 중 클립 재생속도(0 이면 완전 정지라 뻣뻣하다)
// 피격 번쩍임 색. ★흰색 전체 가산 금지 - 실루엣이 통째로 지워져 "형태 파괴"가 된다
//   (건틀릿 캐릭터 심사관이 보스의 전신 플랫 주황을 같은 이유로 지적했다).
//   따뜻한 주홍을 **조금만** 더한다. 초록 고블린 위에서 색상 대비로 튀면서
//   G·B 채널의 명암(= 셰이딩)은 그대로 남는다.
// ── ★상한을 왜 이 값으로 내렸나 (2026-08-11 소반. 밀착 순백 사고) ──
// 이 값은 **선형 HDR**이다. 씬은 composer 의 렌더타겟에 그려지므로 톤매핑(ACES)과
// sRGB 는 맨 끝 OutputPass 에서 붙고, 그 사이에 블룸이 낀다(임계 1.02, main.js).
// 고블린 몸의 선형색은 채널 최대 0.3 언저리다. 옛 값(R 0.72)은 그 두 배를 통째로
// 얹어서 두 가지가 동시에 일어났다:
//   ① 몸이 ACES 무릎 위로 올라가 기울기가 반 토막 난다 = **명암 차이가 뭉개진다**
//   ② 몸 전체가 블룸 임계를 넘어 실루엣 **밖까지 번진다** = 흰 덩어리
//   실측(v96 soban_flash, 밀착 1.13m): 꼭대기에서 몸이 초록을 잃고(G-max(R,B)
//   +19.9 -> -18.5) 채도 0.44 -> 0.34, 창백한 살구색 판이 됐다.
// 그래서 색은 그대로 두고 세기만 0.36 배로 내린다. 몸의 밝은 데가 0.6 근처에
// 머물러 무릎을 안 넘고, 초록 위에 주홍이 얹혀 "맞았다"는 그대로 읽힌다.
// ★올릴 일이 생기면 반드시 밀착 프레임을 다시 찍어라(멀리서는 티가 안 난다).
//
// ── ★★0 으로 내렸다 (오너 지시 2026-08-12) ──
// "칼 휘두를 때 상대 흰색으로 번쩍이게 하지 말고 데미지를 보여줘."
// 9A-3 이 넣고 11차가 톤다운한 이 주홍 틴트가 오너가 말한 그 "번쩍"이다. 세기를 더
// 깎는 게 아니라 **끈다** - 이제 "맞았다"를 말하는 건 머리 위의 큰 숫자다.
//   · 끄는 것은 몸 색 가산 한 갈래뿐이다. 경직(HIT_STUN)·넉백·스쿼시·핍·먹 튀김·
//     참격 획·히트스톱·소리는 한 줄도 안 건드렸다.
//   · 시체 절단 셰이더(uFlash)도 이 상수를 문자열로 박아 쓰므로 **여기 한 곳**으로
//     같이 꺼진다. 되살리려면 이 줄만 옛 값(0.26/0.095/0.05)으로 되돌리면 된다.
//   · e.flash 자체는 남긴다. "방금 맞았다"의 시계라 진단 창구(debug.reaction)가 읽고,
//     되살릴 때 배선을 다시 깔 일이 없다.
const FLASH_R = 0.0, FLASH_G = 0.0, FLASH_B = 0.0;
const FLASH_DECAY = 6.0;        // 1 -> 0 까지 0.167초
// 공격 예고 번득임 색(호박). 피격(주홍)과 **다른 색**이어야 둘이 안 헷갈린다.
const WIND_R = 0.40, WIND_G = 0.19, WIND_B = 0.02;
// 잘린 속살. 절단면이 몸 색과 같으면 "잘렸다"가 안 읽힌다.
const COL_FLESH = new THREE.Color(0x5c1220);
const COL_CUT_EDGE = new THREE.Color(0xff9a6a);

// 개체별 색조. 전부 같은 색이면 무리가 한 덩어리로 보인다.
// ★고블린은 텍스처가 있다. 여기 색은 그 위에 **곱해지는** 값이라 세게 주면
//   텍스처가 통째로 물든다. 살짝만 흔들어 개체 구분만 만든다(0.82~1.0 대역).
const TINTS = [
  new THREE.Color(0xffffff), new THREE.Color(0xd6ddf0),
  new THREE.Color(0xf0dcc8), new THREE.Color(0xd2e8d8),
  new THREE.Color(0xe8d2d2),
];

function paint(geo, color, glow) {
  const n = geo.attributes.position.count;
  const col = new Float32Array(n * 3);
  const gl = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    col[i * 3] = color.r; col[i * 3 + 1] = color.g; col[i * 3 + 2] = color.b;
    gl[i] = glow;
  }
  geo.setAttribute('aCol', new THREE.BufferAttribute(col, 3));
  geo.setAttribute('aGlow', new THREE.BufferAttribute(gl, 1));
  return geo;
}

// BufferGeometryUtils 가 lib 에 없다. 조각 수가 7개뿐이라 직접 이어붙인다.
// 전부 non-indexed 로 펴서 position/normal/aCol/aGlow 네 배열만 concat 하면 끝.
function mergeParts(parts) {
  let total = 0;
  const flat = parts.map(p => {
    const g = p.index ? p.toNonIndexed() : p;
    total += g.attributes.position.count;
    return g;
  });
  const pos = new Float32Array(total * 3);
  const nrm = new Float32Array(total * 3);
  const col = new Float32Array(total * 3);
  const glo = new Float32Array(total);
  let o = 0;
  for (const g of flat) {
    const c = g.attributes.position.count;
    pos.set(g.attributes.position.array.subarray(0, c * 3), o * 3);
    nrm.set(g.attributes.normal.array.subarray(0, c * 3), o * 3);
    col.set(g.attributes.aCol.array.subarray(0, c * 3), o * 3);
    glo.set(g.attributes.aGlow.array.subarray(0, c), o);
    o += c;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
  out.setAttribute('aCol', new THREE.BufferAttribute(col, 3));
  out.setAttribute('aGlow', new THREE.BufferAttribute(glo, 1));
  return out;
}

// 정점을 방향에 따라 울퉁불퉁하게 민다. 매끈한 구는 '덩어리'로 안 읽힌다.
// ★non-indexed 지오메트리라 같은 자리에 정점이 여러 벌 있다. 변형량을
//   **위치만 보고** 계산해야 중복 정점이 같은 값을 받아 메시가 안 찢어진다.
function lumpy(geo, amp, freq) {
  const p = geo.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const l = v.length() || 1;
    const nx = v.x / l, ny = v.y / l, nz = v.z / l;
    const d = 1 + amp * (Math.sin(nx * freq * 1.7 + 1.3) * Math.cos(ny * freq * 1.1 + 2.7)
                       + Math.sin(nz * freq * 2.3 + 0.4) * 0.6);
    p.setXYZ(i, v.x * d, v.y * d, v.z * d);
  }
  geo.computeVertexNormals();
  return geo;
}

function buildYokaiGeometry() {
  const parts = [];

  // 몸통 320면(detail 3 = 20 x 16). 매끈해지지 않게 울퉁불퉁 변형을 한 번 먹인다.
  // 살짝 세로로 길게 눌러야 '넙데데한 바위'가 아니라 '웅크린 것'으로 읽힌다.
  const body = new THREE.IcosahedronGeometry(0.42, 3);
  lumpy(body, 0.09, 2.4);
  body.scale(0.95, 1.08, 0.95);
  body.translate(0, BODY_CY, 0);
  parts.push(paint(body, COL_BODY, 0));

  // 아랫자락. 바닥까지 좁아지는 원뿔. 발이 없어도 '떠 있는 원귀'로 읽힌다.
  const skirt = new THREE.ConeGeometry(0.37, 0.52, 8, 1, true);
  skirt.rotateX(Math.PI);           // 뾰족한 끝이 아래로
  skirt.translate(0, 0.13, 0);
  parts.push(paint(skirt, COL_SKIRT, 0));

  // 뿔 2개. 좌우 길이를 다르게 해 한쪽이 부러진 인상을 준다.
  const hornH = [0.30, 0.21];
  for (let s = 0; s < 2; s++) {
    const sx = s === 0 ? -1 : 1;
    const h = new THREE.ConeGeometry(0.075, hornH[s], 6, 1, true);
    h.rotateZ(sx * 0.38);
    h.rotateX(-0.18);
    h.translate(sx * 0.20, 0.84 + hornH[s] * 0.34, -0.03);
    parts.push(paint(h, COL_HORN, 0));
  }

  // 눈두덩. 찌푸린 인상은 이 두 조각이 거의 다 만든다.
  for (const sx of [-1, 1]) {
    const brow = new THREE.OctahedronGeometry(0.11, 0);
    brow.scale(1.45, 0.30, 0.34);
    brow.rotateZ(sx * -0.40);
    brow.translate(sx * 0.165, 0.685, 0.315);
    parts.push(paint(brow, COL_BROW, 0));
  }

  // 눈 2개. glow=1 이라 블룸에 걸려 멀리서도 이게 제일 먼저 보인다.
  // ★z 를 조금만 더 밀면 몸 밖에 붕 뜬다. 몸통 타원면 위에 딱 얹는 값이다.
  for (const sx of [-1, 1]) {
    const e = new THREE.OctahedronGeometry(0.095, 1);
    e.scale(1.0, 0.80, 0.62);
    e.translate(sx * 0.155, 0.575, 0.36);
    parts.push(paint(e, COL_EYE, 1));
  }

  // 입. 몸 표면을 뚫고 나오게 앞으로 빼야 보인다(안쪽에 두면 몸에 먹힌다).
  const mouth = new THREE.OctahedronGeometry(0.15, 0);
  mouth.scale(1.30, 0.44, 0.62);
  mouth.translate(0, 0.335, 0.36);
  parts.push(paint(mouth, COL_MOUTH, 0));

  // 송곳니 4개. 사면체 4삼각형짜리.
  for (let k = 0; k < 4; k++) {
    const f = new THREE.TetrahedronGeometry(0.05, 0);
    f.rotateX(k % 2 ? 2.55 : 0.55);
    f.translate(-0.10 + k * 0.067, 0.345 + (k % 2 ? 0.033 : -0.033), 0.395);
    parts.push(paint(f, COL_FANG, 0));
  }

  const g = mergeParts(parts);
  g.computeBoundingSphere();
  return g;
}

// ---------------------------------------------------------------------------
// 셰이더
// ---------------------------------------------------------------------------
// 조명은 씬 등에 붙지 않고 직접 계산한다. MeshLambert + onBeforeCompile 로 하면
// 인스턴스 속성(플래시·절단면)을 끼워 넣는 자리가 지저분해진다.
// 대신 그림자를 못 받으므로 아래에 가짜 그림자 원판을 따로 깐다.
const LIGHT_COMMON = `
  vec3 lightOf(vec3 N, vec3 base){
    vec3 L1 = normalize(vec3(0.45, 0.78, 0.36));    // main.js 의 key (5,9,4)
    vec3 L2 = normalize(vec3(-0.62, 0.42, -0.52));  // main.js 의 rim (-6,4,-5)
    float d1 = max(dot(N, L1), 0.0);
    float d2 = max(dot(N, L2), 0.0);
    vec3 hemi = mix(vec3(0.04, 0.06, 0.09), vec3(0.62, 0.77, 0.91), N.y * 0.5 + 0.5);
    return base * (hemi * 0.95 + vec3(1.0) * d1 * 0.85 + vec3(0.36, 0.62, 1.0) * d2 * 0.5);
  }
`;

const VERT_COMMON = `
  attribute vec3 aCol;
  attribute float aGlow;
  attribute vec3 aTint;
  attribute float aFlash;
  varying vec3 vN;
  varying vec3 vCol;
  varying float vGlow;
  varying float vFlash;
  varying float vDepth;
`;

const FRAG_COMMON = `
  uniform vec3 uFogColor;
  uniform float uFogNear;
  uniform float uFogFar;
  varying vec3 vN;
  varying vec3 vCol;
  varying float vGlow;
  varying float vFlash;
  varying float vDepth;
`;

function makeEnemyMaterial(fog, piece) {
  return new THREE.ShaderMaterial({
    transparent: !!piece,
    depthWrite: true,
    side: piece ? THREE.DoubleSide : THREE.FrontSide,
    uniforms: {
      uFogColor: { value: fog ? fog.color : new THREE.Color(0x05070d) },
      uFogNear: { value: fog ? fog.near : 20 },
      uFogFar: { value: fog ? fog.far : 60 },
    },
    vertexShader: VERT_COMMON + (piece ? `
      attribute vec3 aCutN;
      attribute float aCutD;
      attribute float aCutS;
      attribute float aFade;
      varying float vCut;
      varying float vFade;
    ` : '') + `
      void main(){
        vCol = aCol * aTint;
        vGlow = aGlow;
        vFlash = aFlash;
        vec3 p = position;
        vec3 n = normal;
        ${piece ? `
        // ★절단은 로컬 좌표에서 한다. 조각이 굴러가도 자른 면이 같이 따라간다.
        vCut = (dot(position, aCutN) - aCutD) * aCutS;
        vFade = aFade;
        ` : ''}
        #ifdef USE_INSTANCING
          n = mat3(instanceMatrix) * n;
          vec4 wp = modelMatrix * instanceMatrix * vec4(p, 1.0);
        #else
          vec4 wp = modelMatrix * vec4(p, 1.0);
        #endif
        vN = normalize(mat3(modelMatrix) * n);
        vec4 mv = viewMatrix * wp;
        vDepth = -mv.z;
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: FRAG_COMMON + (piece ? `
      varying float vCut;
      varying float vFade;
    ` : '') + LIGHT_COMMON + `
      void main(){
        vec3 N = normalize(vN);
        vec3 base = vCol;
        ${piece ? `
        if (vCut < 0.0) discard;                 // 칼이 지나간 평면 바깥쪽은 없는 셈
        if (!gl_FrontFacing) {                   // 껍데기 안쪽 = 잘린 속살
          base = vec3(${COL_FLESH.r.toFixed(4)}, ${COL_FLESH.g.toFixed(4)}, ${COL_FLESH.b.toFixed(4)});
          N = -N;
        }
        // 절단면 테두리를 밝게. 이 선 하나가 '잘렸다'를 제일 강하게 읽히게 한다.
        float edge = 1.0 - smoothstep(0.0, 0.045, vCut);
        base = mix(base, vec3(${COL_CUT_EDGE.r.toFixed(4)}, ${COL_CUT_EDGE.g.toFixed(4)}, ${COL_CUT_EDGE.b.toFixed(4)}), edge * 0.9);
        ` : ''}
        vec3 c = mix(lightOf(N, base), base * 1.9, vGlow);
        // 맞은 순간 따뜻한 주홍을 **가산**한다. ★흰색으로 갈아끼우면(mix to 1.6)
        //   셰이딩·속살·절단선이 한꺼번에 지워져 몸이 흰 판이 된다(2026-08-11 소반).
        //   가산은 명암 차이를 그대로 남긴다.
        c += vec3(${FLASH_R.toFixed(4)}, ${FLASH_G.toFixed(4)}, ${FLASH_B.toFixed(4)}) * vFlash;
        float f = smoothstep(uFogNear, uFogFar, vDepth);
        c = mix(c, uFogColor, f);
        ${piece ? 'gl_FragColor = vec4(c, vFade);' : 'gl_FragColor = vec4(c, 1.0);'}
      }`,
  });
}

// 가짜 그림자. 실제 섀도맵에 수십 마리를 넣으면 그림자 패스가 통째로 한 번 더 돈다.
// 평평한 바닥뿐이라 원판 하나로 충분하다(드로우콜 1).
function makeShadowMesh(count) {
  const g = new THREE.CircleGeometry(1, 12);
  g.rotateX(-Math.PI / 2);
  const inst = new THREE.InstancedMesh(g, new THREE.ShaderMaterial({
    transparent: true, depthWrite: false,
    uniforms: {},
    vertexShader: `
      attribute float aSA;
      varying float vR; varying float vA;
      void main(){
        vR = length(position.xz);
        vA = aSA;
        #ifdef USE_INSTANCING
          gl_Position = projectionMatrix * viewMatrix * modelMatrix * instanceMatrix * vec4(position, 1.0);
        #else
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        #endif
      }`,
    fragmentShader: `
      varying float vR; varying float vA;
      void main(){
        float a = (1.0 - smoothstep(0.25, 1.0, vR)) * vA;
        if (a < 0.01) discard;
        gl_FragColor = vec4(0.0, 0.005, 0.02, a * 0.55);
      }`,
  }), count);
  inst.geometry.setAttribute('aSA',
    new THREE.InstancedBufferAttribute(new Float32Array(count), 1));
  inst.frustumCulled = false;      // 인스턴스 위치는 바운딩에 안 들어간다. 끄지 않으면 통째로 컬링된다
  inst.renderOrder = -1;
  return inst;
}

// ---------------------------------------------------------------------------
// 고블린 재질
// ---------------------------------------------------------------------------
// 캐릭터(main.js loadChar)와 같은 규칙: 원본 PBR 을 버리고 MeshToonMaterial 로
// 갈아끼운다. 같은 조명·톤매핑 아래서 플레이어와 요괴가 같은 그림체로 보여야 한다.
// 개체마다 clone 한다(색조·피격 번쩍임이 개체별 값이라). 프로그램은 한 벌만 컴파일된다.
function makeGoblinMaterial() {
  const src = GOBLIN && GOBLIN.skin.material;      // 로드 실패 시에도 안 터지게
  return new THREE.MeshToonMaterial({
    map: src && src.map ? src.map : null,
    color: 0xffffff,
    // 맞은 순간 하얗게 번쩍이는 건 emissive 로 낸다. 셰이더를 안 건드리는 게 핵심이다
    // (건드리면 프로그램이 갈라져서 40마리가 각자 컴파일된다).
    emissive: 0x000000,
  });
}

// ── 두 동강 재질 ──
// 시체 전용. 살아 있는 놈은 위 재질을 쓴다.
// ★스킨드 메시는 임의 각도로 **자를 수가 없다**(정점이 매 프레임 뼈로 움직인다).
//   그래서 덩어리 시절과 같은 수를 쓴다: **같은 메시를 두 벌 그리고 셰이더에서
//   평면 반대쪽을 discard**. 다른 점은 두 벌이 인스턴스가 아니라 **뼈를 공유하는
//   SkinnedMesh 두 개**라는 것뿐이다(뼈 계산은 한 번만 돈다).
//    · 절단 각도가 진짜 임의다(미리 두 조각을 구워두면 각도가 고정된다)
//    · 지오메트리 생성이 0
//    · 껍데기가 비어 보이므로 안쪽 면(gl_FrontFacing==false)을 속살 색으로 칠하고
//      절단면 테두리를 밝게 뺀다. 이 선 하나가 '잘렸다'를 제일 강하게 읽히게 한다
// uCutN/uCutD 는 **메시 로컬 좌표**의 평면이다(스키닝이 끝난 transformed 와 같은 공간).
// 시체가 쓰러지며 회전해도 CPU 가 매 프레임 로컬로 다시 옮겨 준다.
function makeCutMaterial(side) {
  const m = makeGoblinMaterial();
  m.side = THREE.DoubleSide;
  m.transparent = true;
  const u = {
    uCutN: { value: new THREE.Vector3(0, 1, 0) },
    uCutD: { value: 0 },
    uSide: { value: side },
    uSep: { value: 0 },        // 두 조각이 서로 반대로 벌어지는 거리
    uFade: { value: 1 },
    uFlash: { value: 0 },
    // ── 먹 소멸 (v84 QA S9) ──
    // 예전엔 마지막 0.55초에 알파를 통째로 내렸다. 반투명해지다 없어지는 건
    // "사라졌다"이지 "쓰러졌다"가 아니다. 유령처럼 비치기만 하고 끝난다.
    // 그래서 알파 대신 **문턱 discard** 로 바꾼다. 아래에서 위로 훑고 지나가는
    // 문턱보다 낮은 조각이 먼저 없어지고, 없어지는 앞머리는 먹빛으로 타들어 간다.
    // 결과: 시체가 바닥부터 **먹 덩이로 흩어지며** 없어진다.
    uDis: { value: 0 },        // 0 = 멀쩡 · 1 = 다 흩어짐
    uDisY0: { value: 0 },      // 시체가 누운 바닥 높이(월드 y)
    uDisH: { value: 0.6 },     // 흩어짐이 훑고 지나갈 높이(m)
  };
  m.userData.u = u;
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>
        uniform vec3 uCutN; uniform float uCutD; uniform float uSide; uniform float uSep;
        varying float vCut; varying vec3 vWP;`)
      .replace('#include <skinning_vertex>', `#include <skinning_vertex>
        vCut = (dot(transformed, uCutN) - uCutD) * uSide;
        transformed += uCutN * (uSide * uSep);
        // ★월드 좌표로 넘긴다. 원본 메시는 키 정규화가 걸린 그룹 안에 있고 twin 은
        //   씬 루트라, **두 메시의 로컬 좌표계가 서로 다르다.** 로컬로 재면 두 조각이
        //   서로 다른 속도로 흩어진다(절단 평면을 매 프레임 로컬로 옮기는 것과 같은 이유).
        vWP = (modelMatrix * vec4(transformed, 1.0)).xyz;`);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
        uniform float uFade; uniform float uFlash;
        uniform float uDis; uniform float uDisY0; uniform float uDisH;
        varying float vCut; varying vec3 vWP;`)
      .replace('#include <dithering_fragment>', `#include <dithering_fragment>
        if (vCut < 0.0) discard;                       // 칼이 지나간 평면 바깥쪽은 없는 셈
        // ── 먹 소멸 ──
        // ★격자를 끊어(floor) 해시한다. 부드러운 노이즈로 하면 안개처럼 뿌옇게
        //   빠져서 '먹'이 아니라 '연기'가 된다. 3.8cm 덩이로 뚝뚝 떨어져 나가야 먹이다.
        float dh = clamp((vWP.y - uDisY0) / max(uDisH, 1e-3), 0.0, 1.0);
        vec3 cell = floor(vWP * 26.0);
        float dn = fract(sin(dot(cell, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
        float df = dh * 0.70 + dn * 0.44;              // 아래가 먼저, 결은 얼룩덜룩
        float dthr = uDis * 1.22 - 0.06;
        if (df < dthr) discard;
        if (!gl_FrontFacing) gl_FragColor.rgb = vec3(${COL_FLESH.r.toFixed(4)}, ${COL_FLESH.g.toFixed(4)}, ${COL_FLESH.b.toFixed(4)});
        float edge = 1.0 - smoothstep(0.0, 0.035, vCut);
        gl_FragColor.rgb = mix(gl_FragColor.rgb,
          vec3(${COL_CUT_EDGE.r.toFixed(4)}, ${COL_CUT_EDGE.g.toFixed(4)}, ${COL_CUT_EDGE.b.toFixed(4)}), edge * 0.9);
        // 흩어지는 앞머리는 먹으로 탄다. 이 띠가 "먹이 되어 사라진다"의 전부다
        float dedge = 1.0 - smoothstep(0.0, 0.19, df - dthr);
        gl_FragColor.rgb = mix(gl_FragColor.rgb, vec3(0.055, 0.038, 0.050), dedge * 0.95);
        // ── 절단 번쩍임 ──
        // ★옛 코드는 여기서 몸을 통째로 흰색(1.6)으로 **갈아끼웠다**. 그러면 0.125초
        //   동안 시체가 판때기 순백이 되고, composer 의 블룸 임계(1.02)를 넘겨 실루엣
        //   **밖까지** 번진다. 밀착해서 벤 프레임에서는 그 덩어리가 주인공을 덮었다
        //   (증거 v96_wave10/fx/readability_worst.jpg · 2026-08-11 소반).
        //   살아있는 놈의 피격 번쩍임과 **같은 주홍을 같은 세기로 가산**한다.
        //   가산이라 속살·절단선·명암이 다 살아남고, "베였다"는 그대로 튄다.
        gl_FragColor.rgb += vec3(${FLASH_R.toFixed(4)}, ${FLASH_G.toFixed(4)}, ${FLASH_B.toFixed(4)}) * uFlash;
        gl_FragColor.a *= uFade;`);
  };
  return m;
}

// ---------------------------------------------------------------------------
// 재사용 임시값 (매 프레임 new 금지)
// ---------------------------------------------------------------------------
const _v1 = new THREE.Vector3(), _v2 = new THREE.Vector3(), _v3 = new THREE.Vector3();
const _v4 = new THREE.Vector3(), _v5 = new THREE.Vector3(), _v6 = new THREE.Vector3();
const _segA = new THREE.Vector3(), _segB = new THREE.Vector3();
const _capA = new THREE.Vector3(), _capB = new THREE.Vector3();
const _prevA = new THREE.Vector3(), _prevB = new THREE.Vector3();
// ★_cutW(월드 절단 법선)와 _cut(로컬로 옮긴 것)을 반드시 나눠 쓸 것.
// 하나로 돌려썼더니 한 스윙에 두 마리째부터 절단 평면이 엉뚱한 방향으로 잡혔다.
const _cutW = new THREE.Vector3(), _cut = new THREE.Vector3();
const _hitP = new THREE.Vector3();
// 처치 기록용(화면 안에서 죽었는지 NDC 로 재는 데만 쓴다). project() 가 값을
// 덮어쓰므로 다른 임시값과 절대 나눠 쓰지 않는다.
const _kv = new THREE.Vector3();
const _q1 = new THREE.Quaternion(), _q2 = new THREE.Quaternion();
const _e1 = new THREE.Euler();
const _mat = new THREE.Matrix4();
const _sc = new THREE.Vector3();
// 벽 충돌 결과를 받는 그릇. level.js 도 자기 것을 재사용하지만, 여기서 우리 것을
// 넘겨야 한 프레임 안에서 여러 번 불러도 값이 서로 안 덮인다.
const _mv = { x: 0, z: 0, hit: false };
// 경직 반동 시간. ★60 -> 100ms (17차). 60ms 는 60fps 에서 3.6프레임인데, 그 3.6프레임이
// 통째로 히트스톱(55~112ms) 안에 들어가 **멈춘 화면에 눌린 자세 한 장**으로만 남았다.
// 정지가 풀린 뒤에도 반동이 남아 있어야 "눌렸다가 돌아온다"가 움직임으로 읽힌다.
// 0.10 위로는 "고무"라는 옛 판정이 맞다(스쿼시가 클립보다 오래 살면 몸이 젤리가 된다).
const SQUASH_T = 0.10;
// ── ★처치 팝 (17차) ──
// 신규유저 지적: "적이 한 방에 사라져 저항감 0 — 벤다가 아니라 지운다."
// 실측으로 보면 정확한 지적이었다. 안 죽은 놈은 밀리고(0.43m) 눌리는데, **죽은 놈은
// 그 자리에 서서 쓰러지기만** 했다(updateCorpses 가 c.pos 를 한 번도 안 옮겼다).
// 처치가 피격보다 반응이 약하니 "지웠다"로 읽힐 수밖에 없다. 세 가지를 붙인다.
const CORPSE_KB = 5.7;          // 시체가 밀려나는 속도(m/s). k^2 로 흘러 총 0.42m
const CORPSE_KB_T = 0.22;       // 밀리는 시간(초)
const CORPSE_POP = 0.14;        // 처치 순간 부푸는 비율(+14%)
const CORPSE_POP_T = 0.12;      // 부풀었다 앉는 시간(초). 히트스톱 112ms 와 겹친다
const _lean = new THREE.Vector3(1, 0, 0);
// 요괴 몸통 반경(scale 1 기준). 몸이 0.42 라 0.34 면 벽에 살짝 겹치는 자리에서 멈춘다.
// 34m 카메라에서 몇 센티 겹치는 건 안 읽히고, 크게 잡으면 무리가 문에 낀다.
const ENEMY_R = 0.34;

// ---------------------------------------------------------------------------
// ★몸 충돌 (플레이어 대 요괴)
// ---------------------------------------------------------------------------
// 이게 없으면 무리 한가운데로 걸어 들어갔을 때 요괴가 **등 뒤 0.1m 에 달라붙는다.**
// 그 자리는 칼이 절대 안 닿는다(아래 실측). 검증 봇이 초반에 한 대도 못 때린 원인이다.
//
// 간격을 얼마로 둘지는 눈이 아니라 **실측**으로 정했다.
// 브라우저에서 검사 Attack / Wide 클립을 프레임마다 훑으면서, 요괴 캡슐(반경 0.4·size
// + 칼날 굵기 0.14)이 실제로 맞는 프레임 비율을 거리·방향별로 잰 값이다.
//
//   거리(m)   Attack 정면   Wide 정면   옆(90도)   뒤(180도)
//   0.10        12%          32%          8~25%       0%
//   0.30        43%          57%          14%         0%
//   0.70        42%          85%           4%         0%
//   0.80        41%          85%           4%         0%
//   0.85        35%          81%           4%         0%
//   0.90        19%          72%           4%         0%
//   1.20        16%          35%           3%         0%
//   1.76        여기서 완전히 끊긴다(칼이 닿는 최대 거리)
//
// 읽히는 것 두 가지.
//   · **뒤는 어느 거리에서도 0% 다.** 등 뒤에 붙으면 칼이 원리적으로 안 닿는다.
//     그리고 공격 중에는 몸이 안 돌아가므로(main.js: attacking 이면 moving=false)
//     한 번 등에 붙으면 그 스윙은 통째로 헛손질이 된다.
//   · 정면 명중률이 **0.30~0.85m 에서 평평하고 0.90 에서 절벽처럼 꺾인다.**
//     0.85 아래로만 붙여 놓으면 두 클립 다 잘 맞는다.
// 그래서 목표 간격을 **0.78~0.85m** 대역으로 잡는다.
//
//   SEP = 플레이어 반경 0.35 + 요괴 반경 0.34*size + BODY_GAP 0.12
//     졸개(size 0.92) 0.78 · 보통(1.00) 0.81 · 두목(1.12) 0.85
//
// 위쪽 한계도 확인했다. 요괴가 멈춰서는 거리는 ENEMY_ATK_RANGE(0.95) + size*0.25
// = 1.18~1.23 이고 공격을 시작하는 거리는 거기에 +0.35 = 1.53~1.58 이다.
// SEP 0.85 는 그보다 한참 안쪽이라 **요괴는 여전히 자기 사거리 안에 들어와 공격한다.**
// (SEP 을 1.23 위로 잡으면 AI 가 다가오려는 힘과 밀어내는 힘이 매 프레임 싸워서 떤다.)
const BODY_GAP = 0.12;
// 밀려나는 속도 상한(m/s). 플레이어 달리기가 3.20m/s 라 6.0 이면 뛰어 들어가도
// 요괴가 밀려나는 속도가 앞선다 = 몸이 겹치지 않는다.
// ★상한이 없으면 파고든 깊이를 한 프레임에 갚느라 요괴가 순간이동하듯 튕겨 나간다.
const BODY_PUSH_MAX = 6.0;
// 한 프레임에 갚는 비율(60fps 기준). 1.0 이면 딱딱하게 튕기고, 낮으면 물컹거린다.
// 0.45 면 서너 프레임(0.05초)에 걸쳐 밀려나서 "밀린다"로 읽힌다.
const BODY_PUSH_K = 0.45;
// ★밀어내기는 **요괴 쪽에만** 먹인다. 플레이어를 같이 밀면 무리에 둘러싸였을 때
//   사방에서 밀려 조작이 안 먹는다(= 갇힌다). 요괴가 비켜서는 쪽이라
//   플레이어는 무리를 헤치고 지나갈 수 있고, 대신 지나가는 동안 계속 얻어맞는다.
//   "밀고 지나갈 수는 있지만 공짜는 아니다"가 이 게임에 맞는 답이다.

// 무리 자리 하나를 **실제로 설 수 있는 자리**로 바꾼다.
// ★맵이 정해 준 무리 중심은 통로 한가운데지만 거기서 반경 2.4m 로 흩뿌리면
//   몇 마리는 건물·석등 안에 박힌다(정적 검사에서 39자리 중 2자리가 그랬다).
//   벽 밖으로 밀어내고 y 는 그 자리 지면 높이로 잡는다(고블린은 이 y 에 발을 딛는다).
function homeAt(x, z) {
  const p = LV.pushOut(x, z, ENEMY_R, { x: 0, z: 0, hit: false });
  return new THREE.Vector3(p.x, LV.groundY(p.x, p.z), p.z);
}

// 선분 위에서 점 p 에 가장 가까운 지점을 out 에 담고 거리의 제곱을 돌려준다.
function closestOnSeg(a, b, p, out) {
  _v6.copy(b).sub(a);
  const len2 = _v6.lengthSq();
  let t = len2 > 1e-9 ? _v6.dot(_v5.copy(p).sub(a)) / len2 : 0;
  t = t < 0 ? 0 : (t > 1 ? 1 : t);
  out.copy(a).addScaledVector(_v6, t);
  return out.distanceToSquared(p);
}

// ── 선분 대 선분 최단거리 ──
// 칼날(p1~q1) 대 몸통 캡슐 축(p2~q2). 거리의 제곱을 돌려주고, 캡슐 축 위의
// 가장 가까운 점을 outB 에 담는다(그 높이가 곧 '칼이 지나간 자리' = 절단면 높이다).
// Ericson, Real-Time Collision Detection 5.1.9 의 표준 풀이. 두 선분이 나란할 때
// (denom≈0) 나눗셈이 폭발하므로 그 경우만 따로 처리한다.
const _d1 = new THREE.Vector3(), _d2 = new THREE.Vector3(), _r = new THREE.Vector3();
const _c1 = new THREE.Vector3();
function segSegDist2(p1, q1, p2, q2, outB) {
  _d1.copy(q1).sub(p1);
  _d2.copy(q2).sub(p2);
  _r.copy(p1).sub(p2);
  const a = _d1.lengthSq(), e = _d2.lengthSq(), f = _d2.dot(_r);
  let s, t;
  if (a <= 1e-9 && e <= 1e-9) { outB.copy(p2); return _r.lengthSq(); }
  if (a <= 1e-9) { s = 0; t = Math.min(1, Math.max(0, f / e)); }
  else {
    const c = _d1.dot(_r);
    if (e <= 1e-9) { t = 0; s = Math.min(1, Math.max(0, -c / a)); }
    else {
      const b = _d1.dot(_d2);
      const denom = a * e - b * b;
      s = denom > 1e-9 ? Math.min(1, Math.max(0, (b * f - c * e) / denom)) : 0;
      t = (b * s + f) / e;
      if (t < 0) { t = 0; s = Math.min(1, Math.max(0, -c / a)); }
      else if (t > 1) { t = 1; s = Math.min(1, Math.max(0, (b - c) / a)); }
    }
  }
  _c1.copy(p1).addScaledVector(_d1, s);
  outB.copy(p2).addScaledVector(_d2, t);
  return _c1.distanceToSquared(outB);
}

// ---------------------------------------------------------------------------
// ★길찾기 (nav.js 흐름장 + 옆걸음)
// ---------------------------------------------------------------------------
// 문제: 추격이 직진뿐이라 바위에 막히면 벽을 타고 미끄러지다 리쉬에 걸려 귀환했다.
//      = 벽 뒤에 서 있으면 아무도 안 온다.
//
// 완전한 길찾기는 과하다. 두 겹으로 끝낸다.
//   1) **시야가 트였으면 직진.** 트인 마당이 대부분이라 이 경우가 제일 흔하고,
//      경유점을 밟게 하면 오히려 지그재그로 걸어서 부자연스럽다.
//   2) **막혔으면 흐름장.** nav.js 가 플레이어에서 BFS 를 한 번 돌려 "이 칸에서
//      다음에 갈 칸"을 통째로 적어두므로, 요괴는 배열을 한 번 읽는 것으로 경로를 얻는다.
//      개체마다 A* 를 돌리는 것과 비용이 자릿수로 다르다.
//   3) 그래도 못 빠져나오면(문틀에 어깨가 걸리는 등) **옆걸음**으로 흔든다.
//
// REPATH 0.28초: 요괴 속도 1.85m/s x 0.28 = 0.52m. 격자 한 칸(1.6m)의 3분의 1이라
// 경로가 뒤늦게 바뀌는 게 눈에 안 띈다. 20마리면 초당 71번 = 시야검사 71회/초다.
const REPATH = 0.28;
// 경유점에 이만큼 다가가면 즉시 다음 경유점을 뽑는다. 0.45 는 요괴 반경(0.34)보다
// 살짝 크다 - 정확히 밟게 하면 도착 판정이 안 나서 그 자리에서 맴돈다.
const WAYPOINT_HIT = 0.45;
// 막힘 감지 창. 0.5초 동안 "가려던 거리" 대비 "실제 간 거리"를 본다.
// ★slide() 의 hit 플래그로는 못 잡는다. 벽을 타고 잘 미끄러지는 중에도 hit 가 뜨기
//   때문이다. 실제로 안 나간 것만 막힘으로 본다.
const STUCK_WIN = 0.5;
const STUCK_RATIO = 0.45;       // 절반도 못 갔으면 막힌 것으로 본다
const SIDESTEP_T = 0.55;        // 옆걸음을 유지하는 시간

// 배치를 매번 똑같이 만들려고 Math.random 대신 쓴다.
// 필드는 "어디에 뭐가 있다"를 외우는 곳이라 새로고침마다 달라지면 안 된다.
function hash1(n) {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

// ---------------------------------------------------------------------------
export function createEnemySystem(opts) {
  const scene = opts.scene;
  // 먹 파편을 카메라 쪽으로 눕히는 데만 쓴다(빌보드). 없으면 파편만 안 뜬다.
  const camera = opts.camera || null;
  const getPlayerPos = opts.getPlayerPos;
  const onRespawn = opts.onRespawn || function () {};
  // 칼이 닿는 **그 프레임**을 바깥(main.js)에 알린다. 히트스톱·소리·붓질 슬래시가
  // 전부 이 한 통로로 걸린다. 여기서 직접 이펙트를 만들면 요괴 모듈이 화면 연출까지
  // 들고 있게 되어 나중에 손댈 수가 없다.
  const onHit = opts.onHit || function () {};
  const onPlayerHurt = opts.onPlayerHurt || function () {};

  const TRIS = GOBLIN
    ? (GOBLIN.skin.geometry.index ? GOBLIN.skin.geometry.index.count
                                  : GOBLIN.skin.geometry.attributes.position.count) / 3
    : 0;
  // 바인드 박스 키를 게임 키로 정규화하는 배수. main.js 의 loadChar 와 같은 규칙이다.
  const K_H = GOBLIN ? GOB_H / GOBLIN.bindH : 1;

  const shadowMesh = makeShadowMesh(MAX_ENEMIES);
  scene.add(shadowMesh);

  // ── 고블린 오브젝트 풀 ──
  // ★glb 는 한 번만 로드하고 여기서 복제한다. 필요할 때 만들고(lazy) 죽으면
  //   돌려받는다. 미리 70마리를 만들면 첫 프레임에 뼈 1,680개를 세우느라 멈칫한다.
  //   놀고 있는 오브젝트는 씬에서 아예 뺀다(visible=false 로 두면 컬링 목록에는 남는다).
  const visFree = [];
  let visMade = 0;
  function takeVis() {
    if (visFree.length) return visFree.pop();
    if (!GOBLIN || visMade >= MAX_VIS) return null;
    const grp = cloneSkinned(GOBLIN.scene);
    let mesh = null;
    grp.traverse(o => {
      if (!o.isSkinnedMesh) return;
      mesh = o;
      o.material = makeGoblinMaterial();
      // ★그림자는 가짜 원판이다. castShadow 를 켜면 섀도맵 패스에서 스킨드 메시를
      //   한 번 더 그려야 해서 드로우콜과 뼈 계산이 통째로 두 배가 된다.
      o.castShadow = false;
      o.receiveShadow = false;
    });
    const mixer = new THREE.AnimationMixer(grp);
    const act = {};
    // ★없는 클립을 참조하면 그 자리에서 렌더 루프가 통째로 죽는다(예전 사고).
    //   이름을 정확히 못 찾을 수도 있으니(다른 glb 와 이름이 겹쳐 Idle.001 이 되는 등)
    //   대소문자·접미사를 무시하고 찾고, 없으면 그냥 null 로 둔다.
    for (const want of ['Idle', 'Walk', 'Run', 'Attack']) {
      const clip = GOBLIN.clips.find(c => c.name === want)
        || GOBLIN.clips.find(c => c.name.toLowerCase().startsWith(want.toLowerCase()));
      act[want] = clip ? mixer.clipAction(clip) : null;
    }
    if (act.Attack) { act.Attack.setLoop(THREE.LoopOnce, 1); act.Attack.clampWhenFinished = true; }
    visMade++;
    return { grp, mesh, mixer, act, cur: null, mat: mesh ? mesh.material : null };
  }
  function giveVis(v) {
    if (!v) return;
    for (const k in v.act) if (v.act[k]) { v.act[k].stop(); v.act[k].paused = false; }
    v.cur = null;
    if (v.mesh && v.mat) v.mesh.material = v.mat;    // 시체가 바꿔 끼운 재질을 되돌린다
    if (v.grp.parent) v.grp.parent.remove(v.grp);
    visFree.push(v);
  }
  // 클립 재생. 없는 클립을 부르면 아무 일도 안 한다(방어).
  function playClip(v, name, ts, fade) {
    const a = v.act[name];
    if (!a) return;
    a.setEffectiveTimeScale(ts);
    if (v.cur === a) return;
    a.reset().play();
    if (v.cur) v.cur.crossFadeTo(a, fade === undefined ? 0.16 : fade, false);
    else a.fadeIn(0.1);
    v.cur = a;
  }

  // ── 풀 ──
  // 죽어도 배열에서 빼지 않는다. live[] 는 앞쪽이 전부 살아 있는 dense 배열이고
  // 죽으면 마지막 원소와 자리를 바꿔 뺀다(swap-remove).
  const pool = [];
  for (let i = 0; i < MAX_ENEMIES; i++) {
    pool.push({
      pos: new THREE.Vector3(), kb: new THREE.Vector3(),
      home: null, spot: null, grp: null, vis: null,
      mode: 0,                     // 0=제자리 1=추격 2=귀환 3=수색(두리번)
      hp: 1, maxHp: 1, speed: 1.6, phase: 0, yaw: 0,
      // 수색: 남은 시간 / 마지막 목격 지점 / 기준으로 삼는 시선
      searchT: 0, searchX: 0, searchZ: 0, searchYaw: 0,
      flash: 0, kbT: 0, sqT: 0, atkCd: 0, lastSwing: -1,
      atkT: 0, hitT: -1,           // 공격 클립 남은 시간 / 타격까지 남은 시간
      // ── 리액션·예고 (9차) ──
      wndT: 0,                     // 예비 자세 남은 시간(>0 이면 곧 휘두른다)
      stunT: 0,                    // 피격 경직 남은 시간(>0 이면 발도 클립도 멎는다)
      pipT: 0,                     // 머리 위 체력 바가 떠 있는 남은 시간
      tint: 0, size: 1, h: GOB_H, spawnT: 0,
      // ── 길찾기 ──
      pathT: 0,                    // 다음 경로 재계산까지 남은 시간
      direct: true,                // 시야가 트여 직진 중인가
      tx: 0, tz: 0,                // 직진이 아닐 때 향하는 경유점
      sideT: 0, sideS: 1,          // 옆걸음 잔여 시간 / 도는 방향(+1 우, -1 좌)
      wantD: 0, gotD: 0, chkT: 0,  // 막힘 감지: 내려던 거리 / 실제 간 거리 / 창 타이머
    });
  }
  const live = [];
  let freeTop = MAX_ENEMIES;      // pool[0..freeTop-1] 이 미사용

  // ── 시체 ──
  // 죽은 놈의 고블린 오브젝트를 **그대로 넘겨받는다**(포즈가 베인 순간에서 멈춘다).
  // 여기에 뼈를 공유하는 두 번째 SkinnedMesh(twin)를 하나 더 붙여서 두 벌을 그리고,
  // 두 재질이 절단 평면의 서로 반대쪽을 discard 한다 = 두 동강.
  // ★twin 은 bindMode 가 'attached' 라 자기 transform 이 스스로 상쇄된다. 즉 씬 어디에
  //   붙여도 원본과 정확히 같은 자리에 그려진다. 벌어지는 건 셰이더의 uSep 이 한다.
  const corpses = [];
  for (let i = 0; i < MAX_CORPSES; i++) {
    corpses.push({
      on: false, vis: null, twin: null,
      matA: makeCutMaterial(1), matB: makeCutMaterial(-1),
      cutW: new THREE.Vector3(0, 1, 0), cutP: new THREE.Vector3(),
      fallAxis: new THREE.Vector3(1, 0, 0),
      pos: new THREE.Vector3(), yaw: 0, size: 1,
      life: 0, ttl: 1.55,
      // ★처치 팝 (17차). kick = 밀려나는 방향(단위). 시체가 그쪽으로 미끄러진다.
      kick: new THREE.Vector3(),
    });
  }
  let corpseRing = 0;
  // ── 플래시 고정 창구 (검증용) ──
  // 피격 번쩍임은 0.167초, 절단 번쩍임은 0.125초면 사라진다. 화면을 찍어 "얼마나
  // 하얀가"를 재려면 그 꼭대기를 손으로 세워 둘 수 있어야 한다(눈으로 프레임을
  // 고르면 매번 다른 값을 재게 된다). -1 = 평소대로 · 0~1 = 그 값으로 고정.
  let flashHold = -1;
  // 월드 절단 평면을 메시 로컬로 옮길 때 쓰는 임시값
  const _inv = new THREE.Matrix4();
  const _pn = new THREE.Vector3(), _pp = new THREE.Vector3();

  // -------------------------------------------------------------------------
  // ── ★첫 처치 셰이더 히치 예열 ──
  // 증상: 판을 시작하고 **처음 한 마리를 벨 때** 화면이 한 번 멎는다.
  // 원인: 두 동강 재질(makeCutMaterial)이 이 파일 안에서만 만들어지고, 그 프로그램은
  //       **첫 시체가 그려지는 프레임**에 처음 컴파일된다. 스킨드 + onBeforeCompile
  //       패치라 컴파일이 무겁고, 하필 히트스톱과 같은 프레임에 걸려 더 크게 보인다.
  //       (v88 에서 참격 셰이더가 같은 증상이었고 예열로 4.5 -> 33.9fps 였다)
  // 수법: 로드 직후 몇 프레임 동안 **진짜 시체와 똑같은 조합**(뼈를 공유하는
  //       SkinnedMesh 두 벌 x matA/matB)을 1000분의 1 크기로 세워 둔다.
  //       화면 안이라 반드시 그려지고 = 프로그램이 그때 만들어지고, 크기가
  //       1픽셀 미만이라 아무도 못 본다. 몇 프레임 뒤 풀에 돌려준다.
  // ★비스킨드 판때기로 예열하면 **아무 소용이 없다.** three 의 프로그램 캐시 키에
  //   USE_SKINNING 이 들어가서 서로 다른 프로그램이 된다. 반드시 SkinnedMesh 로.
  // ★matA/matB 12벌은 onBeforeCompile.toString() 이 전부 같아 프로그램 한 벌을
  //   나눠 쓴다. 그래서 한 쌍만 데워도 전부 데워진다.
  // ★이 블록은 **연출 최적화**지 기능이 아니다. 그래서 두 겹으로 가둔다.
  //   ① 여기서 던지면 createEnemySystem 이 통째로 실패해 **게임이 아예 안 뜬다.**
  //      모델(glb)이 조금만 달라져도(스켈레톤 이름·bindMatrix) 던질 수 있는 코드다.
  //      예열 실패의 정당한 대가는 "첫 처치에 한 번 멎는다"이지 부팅 실패가 아니다.
  //   ② 거두는 쪽(아래 update 안 인라인 블록)은 렌더 루프 안이라 더 위험하다.
  let warmObj = null, warmLeft = 0;
  (function warmCutMaterials() {
    let borrowed = null;
    try {
      if (!GOBLIN) return;
      const v = takeVis();
      if (!v || !v.mesh) return;
      borrowed = v;
      const c = corpses[0];
      const twin = new THREE.SkinnedMesh(v.mesh.geometry, c.matB);
      twin.frustumCulled = false;
      twin.castShadow = false; twin.receiveShadow = false;
      twin.bind(v.mesh.skeleton, v.mesh.bindMatrix);
      v.mesh.material = c.matA;
      v.mesh.frustumCulled = false;
      const p = getPlayerPos();
      v.grp.scale.setScalar(1e-3);
      v.grp.position.set(p.x, p.y + 0.5, p.z);
      scene.add(v.grp);
      scene.add(twin);
      warmObj = { v, twin };
      warmLeft = 6;
    } catch (e) {
      // 빌려 온 고블린 오브젝트는 반드시 풀에 돌려준다(안 돌려주면 한 마리가 샌다).
      warmObj = null; warmLeft = 0;
      if (borrowed) { try { borrowed.mesh.frustumCulled = true; giveVis(borrowed); } catch (e2) { /* 여기서 더 할 게 없다 */ } }
      console.warn('[enemy] 두 동강 재질 예열 실패 - 첫 처치에 한 번 멎을 수 있다(게임은 그대로 돈다)', e);
    }
  })();

  // -------------------------------------------------------------------------
  // ── 처치 순간 먹 파열 (v84 QA S9) ──
  // 벤 자리에서 먹 덩이가 사방으로 터진다. tex/ink_drop.png 는 원래 이걸 하라고
  // 구워 둔 텍스처인데(tools/bake_fx_tex.py "처치 파편") 아무도 안 쓰고 있었다.
  //
  // ★main.js 의 물보라(spawnInk)와 역할이 다르다. 저건 **잔 물방울 26개**가
  //   흩뿌려지는 결이고, 이건 **큰 먹 덩이 8개**가 무겁게 튀어 굴러떨어지는 결이다.
  //   잔 물방울만으로는 "픽 쓰러진다"의 무게가 안 나온다.
  // ★일반합성이다. 먹은 발광하지 않는다(가산합성으로 깔면 밝은 흙바닥에서 사라진다).
  // 판 하나 = 사각형 하나. 40장을 한 메시로 그려서 드로우콜은 1이다.
  const inkParts = [];
  let inkRing = 0, inkN = 0;
  let inkTexOk = false;
  const inkPos = new Float32Array(INK_MAX * 4 * 3);
  const inkUVa = new Float32Array(INK_MAX * 4 * 2);
  const inkAl = new Float32Array(INK_MAX * 4);
  const inkIdx = [];
  for (let i = 0; i < INK_MAX; i++) {
    const o = i * 4;
    inkIdx.push(o, o + 1, o + 2, o, o + 2, o + 3);
    inkUVa[o * 2] = 0; inkUVa[o * 2 + 1] = 0;
    inkUVa[(o + 1) * 2] = 1; inkUVa[(o + 1) * 2 + 1] = 0;
    inkUVa[(o + 2) * 2] = 1; inkUVa[(o + 2) * 2 + 1] = 1;
    inkUVa[(o + 3) * 2] = 0; inkUVa[(o + 3) * 2 + 1] = 1;
    inkParts.push({ t: 9, ttl: INK_TTL, size: 0.2, rot: 0,
                    p: new THREE.Vector3(), v: new THREE.Vector3() });
  }
  const inkGeo = new THREE.BufferGeometry();
  inkGeo.setAttribute('position', new THREE.BufferAttribute(inkPos, 3).setUsage(THREE.DynamicDrawUsage));
  inkGeo.setAttribute('uv', new THREE.BufferAttribute(inkUVa, 2));
  inkGeo.setAttribute('aA', new THREE.BufferAttribute(inkAl, 1).setUsage(THREE.DynamicDrawUsage));
  inkGeo.setIndex(inkIdx);
  const inkMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: true, fog: false,
    side: THREE.DoubleSide, blending: THREE.NormalBlending,
    uniforms: { uTex: { value: null } },
    vertexShader: `
      attribute float aA;
      varying vec2 vU; varying float vA;
      void main(){ vU = uv; vA = aA;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `
      uniform sampler2D uTex;
      varying vec2 vU; varying float vA;
      void main(){
        // ★부등호 방향에 이유가 있다. vA <= 0.01 로 쓰면 **NaN 이 통과한다**
        //   (NaN 은 모든 비교가 거짓이라 discard 가 안 걸린다). 통과한 NaN 은 HDR
        //   버퍼에 들어가고 블룸 블러를 타고 번져서 화면을 검게 만든다.
        //   !(vA > 0.01) 은 NaN 도 반드시 걸러낸다. 아래 a 도 같은 이유다.
        //   ★셰이더 주석에 역따옴표를 쓰면 안 된다. 이 문자열이 JS 템플릿 리터럴이라
        //     거기서 문자열이 끊겨 모듈이 통째로 죽는다(node --check 는 통과한다).
        if (!(vA > 0.01)) discard;
        vec4 t = texture2D(uTex, vU);
        float a = t.a * vA;
        if (!(a > 0.02)) discard;
        // 구운 텍스처는 검붉은 먹이다. 아침 산야가 밝아서 한 단 더 눌러야 덩이로 읽힌다
        gl_FragColor = vec4(t.rgb * 0.62, a);
      }`,
  });
  const inkMesh = new THREE.Mesh(inkGeo, inkMat);
  inkMesh.frustumCulled = false;      // 자리를 정점 버퍼가 만든다(경계구가 못 따라간다)
  inkMesh.renderOrder = 6;
  inkMesh.visible = false;
  scene.add(inkMesh);
  // 못 읽으면 파편만 안 뜬다. 게임은 그대로 돈다.
  new THREE.TextureLoader().load('./tex/ink_drop.png' + (typeof location !== 'undefined' ? location.search : ''),
    (t) => {
      t.colorSpace = THREE.SRGBColorSpace;
      t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
      inkMat.uniforms.uTex.value = t;
      inkMat.needsUpdate = true;
      inkTexOk = true;
    }, undefined, () => { /* 파편 없이 간다 */ });

  // 벤 자리에서 8조각. kx,kz 는 칼이 지나간 수평 방향이라 그쪽이 더 멀리 날아간다.
  function spawnInkBurst(x, y, z, kx, kz, size) {
    if (!inkTexOk || !camera) return;
    for (let k = 0; k < INK_PER_KILL; k++) {
      const p = inkParts[inkRing];
      inkRing = (inkRing + 1) % INK_MAX;
      p.t = 0;
      p.ttl = INK_TTL * (0.72 + Math.random() * 0.56);
      p.size = (0.11 + Math.random() * 0.15) * size;
      p.rot = Math.random() * Math.PI * 2;
      p.p.set(x, y, z);
      const a = Math.random() * Math.PI * 2;
      const s = 0.9 + Math.random() * 1.5;
      p.v.set((Math.cos(a) * 0.6 + kx * 1.2) * s,
              (0.9 + Math.random() * 1.6),
              (Math.sin(a) * 0.6 + kz * 1.2) * s);
      inkN++;
    }
  }

  const _ikR = new THREE.Vector3(), _ikU = new THREE.Vector3();
  const _ikA = new THREE.Vector3(), _ikB = new THREE.Vector3(), _ikQ = new THREE.Vector3();
  const INK_CORNER = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
  function updateInk(dt) {
    if (!camera) return;
    _ikR.setFromMatrixColumn(camera.matrixWorld, 0);
    _ikU.setFromMatrixColumn(camera.matrixWorld, 1);
    let any = false;
    for (let i = 0; i < INK_MAX; i++) {
      const p = inkParts[i];
      const o = i * 4;
      if (p.t >= p.ttl) {
        if (inkAl[o] !== 0) { inkAl[o] = inkAl[o + 1] = inkAl[o + 2] = inkAl[o + 3] = 0; any = true; }
        continue;
      }
      p.t += dt;
      // ★★수명을 **절대로 넘겨서 적분하면 안 된다** (v88 QA 1순위 '검은 번쩍'의 진범).
      //   위 문턱은 프레임 시작에 재므로 여기서 p.t 가 p.ttl 을 살짝 넘어설 수 있다.
      //   그러면 아래 life 가 음수가 되고 `Math.pow(음수, 0.55)` 는 **NaN** 이다.
      //   NaN 이 정점 알파로 들어가면 셰이더의 `vA <= 0.01` 문턱을 **통과해 버린다**
      //   (NaN 은 어떤 비교도 거짓이라 discard 가 안 걸린다). 그 결과 반투명 합성으로
      //   HDR 버퍼(HalfFloat)에 NaN 이 몇 픽셀 찍히고, UnrealBloom 의 5단 분리 블러가
      //   그 NaN 을 사방으로 번지게 해서 **화면 86% 가 한두 프레임 새까맣게** 죽는다.
      //   실측(2026-08-10): Float 렌더타겟 재현 → NaN 픽셀 23개(6x6 덩이) → 이 메시만
      //   끄면 0개. aA 속성에 NaN 12개(= 죽는 파편 3개 x 정점 4개).
      if (p.t > p.ttl) p.t = p.ttl;
      // 공기저항 + 중력. 먹 덩이는 물방울보다 무거워서 금방 떨어진다
      const drag = Math.pow(0.18, dt);
      p.v.x *= drag; p.v.z *= drag;
      p.v.y -= 7.4 * dt;
      p.p.addScaledVector(p.v, dt);
      // ★위에서 p.t 를 물렸으니 0 밑으로는 안 간다. 그래도 한 겹 더 막는다.
      //   여기 한 줄이 뚫리면 화면이 통째로 검게 죽는다(위 주석).
      const life = Math.max(0, 1 - p.t / p.ttl);
      // 처음 20% 는 커지면서 나온다(터진다) - 그 뒤로는 그대로 떨어진다
      const grow = Math.min(1, p.t / (p.ttl * 0.20));
      const sz = p.size * (0.45 + grow * 0.55);
      const c = Math.cos(p.rot), s = Math.sin(p.rot);
      _ikA.copy(_ikR).multiplyScalar(c).addScaledVector(_ikU, s).multiplyScalar(sz);
      _ikB.copy(_ikR).multiplyScalar(-s).addScaledVector(_ikU, c).multiplyScalar(sz);
      for (let k = 0; k < 4; k++) {
        _ikQ.copy(p.p).addScaledVector(_ikA, INK_CORNER[k][0]).addScaledVector(_ikB, INK_CORNER[k][1]);
        inkPos[(o + k) * 3] = _ikQ.x; inkPos[(o + k) * 3 + 1] = _ikQ.y; inkPos[(o + k) * 3 + 2] = _ikQ.z;
        inkAl[o + k] = Math.pow(life, 0.55);
      }
      any = true;
    }
    inkMesh.visible = inkTexOk;
    if (any) {
      inkGeo.attributes.position.needsUpdate = true;
      inkGeo.attributes.aA.needsUpdate = true;
    }
  }

  // -------------------------------------------------------------------------
  // ── ★머리 위 판 (체력 바 · 인지 표식) ──
  //
  // 건틀릿 1회차가 짚은 두 구멍을 한 시스템으로 메운다.
  //   손맛 5위 "적 HP 바가 없다"          -> 맞은 놈 머리 위 체력 바 1.2초
  //   손맛 8번 "은신 인지 표식 0 (3/10)"  -> ! / ? / 공격 쐐기
  //
  // 구현 원칙은 먹 파편(inkMesh)과 같다. **판 40장을 정점 버퍼 한 벌에 담아
  // 드로우콜 1로 그린다.** DOM 으로 하면 40마리분 좌표 투영 + style 쓰기가
  // 매 프레임 돌고, 스프라이트로 하면 드로우콜이 40개가 된다.
  //
  // ★깊이검사를 끈다(depthTest:false). 잎·바위 뒤에 있는 놈의 표식도 보여야
  //   "쟤가 나를 놓쳤다"가 성립한다. 대신 **대기 중인 무리는 표식이 아예 없어서**
  //   맵의 정보가 새지 않는다(표식은 이미 나를 아는 놈에게만 붙는다).
  // -------------------------------------------------------------------------
  // 표식 글자는 파일로 안 만든다. 캔버스에 구우면 404·CSP·경로 문제가 통째로 없다.
  // 아틀라스 = 128px 칸 MARK_N 개: [0] ! · [1] ? · [2] 공격 쐐기(MARK_ATK_ON 일 때만)
  function makeMarkTexture() {
    const S = 128;
    const cv = document.createElement('canvas');
    cv.width = S * MARK_N; cv.height = S;
    const g = cv.getContext('2d');
    g.clearRect(0, 0, S * MARK_N, S);
    g.textAlign = 'center'; g.textBaseline = 'middle';
    // ★획이 굵어야 34m 에서 남는다. 먹 테두리(18px)를 두르고 속을 종이색으로 채운다.
    //   테두리가 없으면 밝은 흙바닥 위에서 글자가 통째로 사라진다.
    g.font = '700 104px "Nanum Myeongjo", AppleMyungjo, Georgia, "Times New Roman", serif';
    g.lineJoin = 'round';
    const glyph = (ch, i) => {
      const cx = S * i + S / 2, cy = S / 2 + 4;
      g.strokeStyle = 'rgba(8,7,10,0.96)'; g.lineWidth = 20;
      g.strokeText(ch, cx, cy);
      g.fillStyle = '#f6f0e2';
      g.fillText(ch, cx, cy);
    };
    glyph('!', 0);
    glyph('?', 1);
    // 공격 쐐기. 아래(= 그 놈 머리)를 가리키는 삼각형이라 "이놈이 친다"가 읽힌다.
    // ★오너 지시로 꺼져 있다(MARK_ATK_ON). 칸 자체를 안 굽는다.
    if (MARK_ATK_ON) {
      const cx = S * 2 + S / 2;
      g.beginPath();
      g.moveTo(cx - 40, 30); g.lineTo(cx + 40, 30); g.lineTo(cx, 104); g.closePath();
      g.strokeStyle = 'rgba(8,7,10,0.96)'; g.lineWidth = 20; g.stroke();
      g.fillStyle = '#f6f0e2'; g.fill();
    }
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    t.minFilter = THREE.LinearFilter;
    t.generateMipmaps = false;
    return t;
  }

  // -------------------------------------------------------------------------
  // ── ★데미지 숫자 아틀라스 (0~9 열 칸) ──
  //
  // 표식과 같은 이유로 파일을 안 만든다(404·CSP·경로 문제가 통째로 없다).
  // ★다른 점이 하나 있다. 이건 **색이 아니라 마스크**다. 세 겹을 세 칸에 나눠 담는다.
  //   G = 바깥 진한 외곽선 · B = 그 안쪽 크림색 테 · R = 글자 속 · A = 덮인 정도
  //   굽는 법: 초록(0,255,0)으로 굵게 긋고 → 파랑(0,0,255)으로 가늘게 덧긋고 →
  //   빨강(255,0,0)으로 속을 채운다. source-over 라 겹친 자리는 뒤에 그린 것이 이기고
  //   경계 한 겹만 둘이 섞인다 = 셰이더에서 그대로 부드러운 전환이 된다.
  // 겹이 세 개인 이유는 codex 시트(incoming/codex_ui/damage_numbers.png) 때문이다.
  //   크리티컬 숫자의 성격은 주황-빨강 색계단이 아니라 **그 둘레의 크림색 테**다
  //   (테가 없으면 어두운 배경에서 빨강이 그냥 묻힌다).
  // 왜 마스크로 굽나: **색을 프래그먼트에서 정하려고.** 그래야 일반타(흰-노랑)와
  //   처치타(주황-빨강)가 아틀라스 한 벌을 같이 쓰고, 위-아래 색계단도 공짜다.
  //   구운 그림에 색을 박으면 색을 바꿀 때마다 텍스처가 한 벌씩 늘어난다.
  // ★colorSpace 는 **안 건다**(NoColorSpace). 이건 색이 아니라 곱수라 sRGB 로 읽으면
  //   하드웨어가 선형으로 풀어서 0.5 가 0.21 이 된다(level.js 스플랫맵과 같은 함정).
  // ── ★칸 크기를 화면 크기 가까이 굽는 이유 (첫 판이 밟은 함정) ──
  // 처음엔 128x160 으로 구웠다. 화면에서는 칸이 44px 이라 **3.6배 축소**인데
  // 밉맵이 없으면 이중선형은 2x2 만 읽으므로 얇은 진한 테가 표본 사이로 새서
  // 회색 후광처럼 보이고 숫자가 움직일 때마다 지글거린다.
  // 고친 것 둘: ① 칸을 112x140 으로 줄여 축소비를 2.5배 안으로 ② 밉맵을 켠다.
  // 밉맵은 아틀라스라 이웃 칸이 샐 위험이 있는데, 글자 폭이 칸의 절반이라
  // 좌우 여백이 27px 씩(밉 2단에서도 7텍셀) 있어 실제로는 안 닿는다.
  const DIG_CW = 112, DIG_CH = 140;      // 아틀라스 한 칸(px)
  // ── ★줄이 둘인 이유 (2026-08-12 13차. 오너 "빨간 글자에 흰 테두리") ──
  // 0줄 = 일반타 · 1줄 = 처치타. **처치타는 흰 테를 더 굵게 굽는다.**
  // 처치타는 이미 1.35배로 커지지만 그건 전체가 같이 커지는 거라 테의 **몫**은 그대로다.
  // 오너가 말한 "처치타는 테가 더 굵다"는 몫의 이야기라, 굵기를 아예 따로 구워야 한다.
  const DIG_ROWS = 2;
  // 겹 굵기(px). ★보이는 두께는 절반씩이다 - 속을 나중에 채우므로 안쪽 절반이 덮인다:
  //   흰 테 = rim/2 · 바깥 어두운 키라인 = (ol - rim)/2
  // 개선 전에는 ol 36 / rim 13 이라 **어두운 겹 11.5px · 크림 6.5px** 이었다(실측 300:242).
  // 즉 굵은 쪽이 어두운 겹이었고, 밝은 바닥에서는 글자가 갈색 테로 읽혔다. 그래서 뒤집는다.
  // ★13/16px 로 한 번 밟았다. 흰 테가 획 굵기를 넘어서서 글자가 **흰 덩어리**로 읽혔고
  //   0 의 속이 메워졌다(캡처로 확인). 테는 색을 이기면 안 된다 - codex 시트에서도
  //   흰 테는 획 굵기의 절반쯤이다. 9/12px 로 내려서 색이 주인이고 테가 두르는 그림으로.
  const DIG_W = [{ ol: 26, rim: 18 },    // 일반타 : 흰 9px · 키라인 4px
                 { ol: 32, rim: 24 }];   // 처치타 : 흰 12px · 키라인 4px
  let digAdv = 0.75;                     // 자리 간격 / 칸 폭. 굽는 자리에서 실측해 덮는다
  let digInk = 0;                        // 잉크가 실제로 닿은 글자 폭(px). 자간 계약의 분모다
  let digCanvas = null;                  // 실측 창구(api.dmgScan)가 읽는 굽힌 캔버스
  // ── ★자간 계약 (오너 "글자도 조금씩 겹쳐져 있다") ──
  // 전진 = 잉크 폭 × 이 값. 1 이면 딱 붙고, 낮출수록 겹친다. 개선 전은 0.906 이라
  // 사실상 안 겹쳤다. 0.76 이면 제일 넓은 글자끼리 잉크 폭의 24% 가 겹친다.
  const DIG_ADV_RATIO = 0.76;
  // ── ★자리별 세로 지터 (오너 "높낮이가 조금씩 다 다르고") ──
  // 자리마다 칸 높이의 6~12% 만큼 위나 아래로 어긋난다. ★크기까지 해시로 뽑는다 -
  // 부호만 뽑으면 모든 자리가 같은 폭으로 튀어서 "지그재그"라는 다른 모양이 된다.
  // 결정론적 해시라 Math.random 이 안 들어간다 = 같은 뭉치는 사는 동안 같은 높낮이를
  // 유지한다(프레임마다 다시 뽑으면 그건 지터가 아니라 떨림이다. 실측으로 확인했다).
  const DMG_JIT_MIN = 0.06, DMG_JIT_MAX = 0.12;
  // 가운데 자리가 살짝 올라가는 미세 아치. 지터와 달리 **모양**이라 결정론이 아니라 규칙이다.
  const DMG_ARCH = 0.045;
  // 칸마다 잉크(알파)가 닿은 좌우 폭을 재서 제일 넓은 값을 돌려준다.
  function measureInk(cv, row = 0) {
    const g = cv.getContext('2d');
    let best = 0;
    for (let d = 0; d <= 9; d++) {
      const im = g.getImageData(DIG_CW * d, DIG_CH * row, DIG_CW, DIG_CH).data;
      let x0 = -1, x1 = -1;
      for (let x = 0; x < DIG_CW; x++) {
        let hit = false;
        for (let y = 0; y < DIG_CH; y++) { if (im[(y * DIG_CW + x) * 4 + 3] >= 26) { hit = true; break; } }
        if (!hit) continue;
        if (x0 < 0) x0 = x; x1 = x;
      }
      if (x1 > x0) best = Math.max(best, x1 - x0 + 1);
    }
    return best;
  }
  function makeDigitTexture() {
    const cv = document.createElement('canvas');
    cv.width = DIG_CW * 10; cv.height = DIG_CH * DIG_ROWS;
    const g = cv.getContext('2d');
    g.clearRect(0, 0, cv.width, cv.height);
    g.textAlign = 'center'; g.textBaseline = 'middle';
    // 볼드 라운드체. 메이플·로블록스 숫자의 정체는 **두꺼운 라운드 + 굵은 외곽선**이다.
    // macOS 는 Arial Rounded MT Bold 가 기본 탑재라 첫 칸에서 잡히고, 없는 기기에서도
    // 뒤로 갈수록 두꺼운 산세리프로 떨어져서 "굵다"는 성질은 안 잃는다.
    g.font = '900 96px "Arial Rounded MT Bold", "Avenir Next", ' +
             '"Helvetica Neue", "Apple SD Gothic Neo", Arial, sans-serif';
    g.lineJoin = 'round'; g.lineCap = 'round'; g.miterLimit = 2;
    // ★굵기 내력(칸 112 기준. 앞의 둘은 128칸 시절이다)
    //   36/17: 진한 테가 화면 2.6px 이라 회색 후광 - 진범은 굵기가 아니라 밉맵 없는 축소였다.
    //   50/20: 너무 굵어 0 의 속이 메워지고 세 자리가 한 덩어리가 됐다.
    //   36/13: 어두운 겹 11.5px · 크림 6.5px. **굵은 쪽이 어두운 겹이라 뒤집혀 있었다.**
    //   34/26 · 40/32(지금): 흰 테 13·16px · 어두운 키라인 4px. 오너 지시의 "흰 굵은 테".
    // ★어두운 키라인을 0 으로 못 없앤다. 밝은 흙바닥에서 흰 테가 배경에 먹히면
    //   글자 모양이 통째로 사라진다 - codex 시트도 흰 테 바깥에 갈색 한 줄을 두르고 있다.
    for (let row = 0; row < DIG_ROWS; row++) {
      const LW_OL = DIG_W[row].ol, LW_RIM = DIG_W[row].rim;
      for (let d = 0; d <= 9; d++) {
        const ch = String(d);
        const cx = DIG_CW * d + DIG_CW / 2, cy = DIG_CH * row + DIG_CH / 2;
        // 겹치는 순서가 곧 겹의 순서다: 바깥(G) -> 흰 테(B) -> 속(R).
        // 속을 마지막에 채우므로 두 스트로크의 **안쪽 절반은 덮인다** = 테가 밖으로만 남는다.
        g.strokeStyle = '#00ff00'; g.lineWidth = LW_OL;
        g.strokeText(ch, cx, cy);
        g.strokeStyle = '#0000ff'; g.lineWidth = LW_RIM;
        g.strokeText(ch, cx, cy);
        g.fillStyle = '#ff0000';
        g.fillText(ch, cx, cy);
      }
    }
    digCanvas = cv;
    // ★잉크 폭 실측. 자간 계약("숫자 폭의 70~80% 만 전진한다")의 분모는 글자 폭이 아니라
    //   **테까지 포함해 실제로 칠해진 폭**이다. 사람 눈에는 테까지가 글자다.
    //   글리프마다 다르니 제일 넓은 칸(0·8 계열)으로 잡는다 - 그게 겹침의 최악이다.
    //   ★일반타 줄(0)로 잰다. 처치타는 뭉치째 1.35배라 같은 비율이 그대로 따라온다.
    digInk = measureInk(cv, 0);
    // ★자리 간격은 **실측**에서 나온다. 폰트가 뒤 칸으로 떨어지면 글자 폭이 달라지는데
    //   간격을 상수로 박아 두면 숫자가 붙거나 벌어진다.
    if (digInk > 4) digAdv = Math.min(0.95, (digInk * DIG_ADV_RATIO) / DIG_CW);
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.NoColorSpace;
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    // ★핍·표식과 달리 **밉맵을 켠다**. 숫자는 튀어오르며 크기가 계속 변해서
    //   축소비가 프레임마다 달라지는데, 밉맵이 없으면 그때마다 테가 지글거린다.
    t.minFilter = THREE.LinearMipmapLinearFilter;
    t.magFilter = THREE.LinearFilter;
    t.generateMipmaps = true;
    t.anisotropy = 4;
    return t;
  }

  // 판 N 장짜리 빌보드 메시 하나를 만든다(핍·표식이 같은 틀을 쓴다).
  function plateMesh(count, mat, extra) {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(count * 4 * 3);
    const uv = new Float32Array(count * 4 * 2);
    const idx = [];
    for (let i = 0; i < count; i++) { const o = i * 4; idx.push(o, o + 1, o + 2, o, o + 2, o + 3); }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3).setUsage(THREE.DynamicDrawUsage));
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2).setUsage(THREE.DynamicDrawUsage));
    for (const k in extra) {
      geo.setAttribute(k, new THREE.BufferAttribute(extra[k].arr, extra[k].n)
        .setUsage(THREE.DynamicDrawUsage));
    }
    geo.setIndex(idx);
    const m = new THREE.Mesh(geo, mat);
    m.frustumCulled = false;      // 자리를 정점 버퍼가 만든다(경계구가 못 따라간다)
    m.renderOrder = 7;
    m.visible = false;
    scene.add(m);
    return m;
  }

  // ── 체력 바 (머리 위) ──
  // ★이름만 pip 로 남아 있다(칸 시절의 유산). 2026-08-13 부터 그림은 **칸이 없는
  //   연속 바 하나**고, 같은 날 밤부터 그 바의 **폭이 고정**이다(BAR_W 주석 참조).
  const pipN = new Float32Array(MAX_ENEMIES * 4);   // 최대 체력. 눈금 칸 수·채움 비율의 분모
  const pipHp = new Float32Array(MAX_ENEMIES * 4);  // 남은 체력(연속. 소수 그대로)
  const pipA = new Float32Array(MAX_ENEMIES * 4);   // 알파
  const pipMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: false, fog: false,
    side: THREE.DoubleSide, blending: THREE.NormalBlending,
    uniforms: {},
    vertexShader: `
      attribute float aN; attribute float aHp; attribute float aA;
      varying vec2 vU; varying float vN; varying float vHp; varying float vA;
      void main(){ vU = uv; vN = aN; vHp = aHp; vA = aA;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    // ── ★카드 문법으로 갈아 끼움 (17차. 17-UI마감 제안) ──
    // 여태 이 바 하나만 게임에서 **다른 언어**였다: 먹 테두리 + 종이색 칸.
    // 그 사이 계기판·스킬칩·플레이어 머리 위 바(#uiHpFloat)가 전부 한 벌로 통일됐다
    //   딥 네이비 트랙 + 1px 창백한 헤어라인 + 컷코너 + 세로 그러데이션 채움.
    // 블라인드 비평도 같은 자리를 짚었다: "회색 돌바닥 위에서 회색 사각이라 안 보인다."
    // 그 값을 그대로 옮긴다(ui.js #uiHpFloat .track / HP_INK).
    //   · 트랙   rgba(2,5,11,.92)              -> 딥 네이비
    //   · 헤어라인 inset 0 0 0 1px rgba(214,240,255,.72)
    //   · 컷코너  --c: 3px (판 높이의 약 0.30)
    //   · 채움   HP_INK 초록 #2ee08a~#7ff0c0. 가로가 아니라 **세로** 그러데이션
    //            (가로 그러데이션은 채움 끝이 어디인지를 흐린다)
    //   · 처치 직전(남은 체력 1 이하) 채움은 붉게 — HP_INK 의 25% 이하 색 #e04a2e
    // ★색은 전부 **선형 HDR**이다(FLASH_R 선언부의 파이프라인 주석 참조. ACES 무릎 +
    //   블룸 임계 1.02). 그래서 sRGB 표기를 그대로 못 넣는다 - ACES 를 되짚어 넣은 값이다.
    //   0.95 가 상한선이다. 그 위로 올리면 바가 블룸으로 번져 실루엣 밖까지 샌다.
    fragmentShader: `
      varying vec2 vU; varying float vN; varying float vHp; varying float vA;
      void main(){
        // ★!(a > x) 꼴. a <= x 로 쓰면 NaN 이 통과해서 블룸이 화면을 검게 만든다
        //   (LOG.md 의 '검은 번쩍' 함정. 알파 문턱은 전부 이 꼴로 쓴다).
        if (!(vA > 0.01)) discard;
        // 판을 **세로 높이 1** 로 정규화한 좌표로 옮긴다. 헤어라인 두께·컷코너·눈금을
        // 가로세로 같은 크기로 그리려면 이 환산이 있어야 한다.
        // ★2026-08-13 밤부터 이 값은 **상수**다(폭 고정). 여태는 vN(최대 체력)이 들어와
        //   개체마다 판이 늘어났다 - 그게 오너가 본 "왜 이리 작아"의 정체다.
        float ar = ${(BAR_W / PIP_H).toFixed(6)};
        float U = vU.x * ar, V = vU.y;
        // 가장자리까지의 거리(높이 단위). 네 모서리는 45도로 잘린다 = 컷코너.
        float CUT = 0.25;                           // --c: 3px / 12px 와 같은 비율
        float d = min(min(U, ar - U), min(V, 1.0 - V));
        d = min(d, (U + V - CUT) * 0.70710678);
        d = min(d, (ar - U + V - CUT) * 0.70710678);
        d = min(d, (U + 1.0 - V - CUT) * 0.70710678);
        d = min(d, (ar - U + 1.0 - V - CUT) * 0.70710678);
        if (d < 0.0) discard;                       // 잘려 나간 모서리
        float HAIR = 0.115;                         // 1px (판 높이 11px 기준)
        vec3 hair  = vec3(0.55, 0.72, 0.92);        // 창백한 청백. 형태를 정의하는 선
        vec3 track = vec3(0.022, 0.032, 0.058);     // 딥 네이비
        if (d < HAIR) { gl_FragColor = vec4(hair, vA); return; }
        // ── 속: 칸 없는 **연속 채움** (오너 지시 2026-08-13 낮) ──
        // "몬스터 체력바 칸으로 하지 말고 그냥 체력바로. 지금 볼 땐 딱 세 칸이 합쳐진
        //  느낌인데 그냥 하나의 바로."
        // 옛 그림은 트랙 하나 안을 칸으로 쪼개고 칸 사이에 트랙색 홈을 팠다(floor/fract
        // 양자화 + gap). 그 두 줄이 「세 칸이 합쳐진」의 정체다. 통째로 걷어냈고,
        // **이 계약은 이번에도 그대로다** - 채움은 여전히 한 덩어리로 이어진다.
        // 남는 것은 비율 하나다: 채움 끝 = (남은 체력 / 최대 체력) × 판 폭.
        float fillX = clamp(vHp / max(vN, 0.001), 0.0, 1.0) * ar;
        // 경계는 1px 남짓만 눕힌다(판 높이 11px 기준 ±0.06 = 0.7px).
        // ★fwidth 를 안 쓴다: GLSL1 파생함수는 확장에 걸려 있어 컴파일이 기기를 탄다.
        //   이 판은 월드 크기가 고정이라 상수 폭으로 충분하다.
        float f = 1.0 - smoothstep(fillX - 0.06, fillX + 0.06, U);
        // 세로 그러데이션. 위가 밝고 아래가 어둡다(유리에 담긴 액체의 문법).
        // ★붉어지는 뜻은 하나다: **다음 한 대에 죽는다**(남은 체력 <= 칼 한 대).
        //   칸이 없어졌으니 "마지막 한 칸만"은 성립하지 않고, 채움 전체가 붉어진다.
        // ★18차: 문턱이 상수 1.5 였다. 그건 「핍 1 = 한 대」일 때만 맞는 수라서
        //   칼 데미지를 반으로 줄이자마자 **두 대 남았는데 붉은** 거짓말이 된다.
        //   SWORD_DMG 에서 굽는다(×1.5 는 정수 사이 중점 = 부동소수 안전 여유).
        //   DMG_SCALE=1 로 되돌리면 이 값도 정확히 1.5 로 돌아온다.
        float g = clamp((V - 0.16) / 0.68, 0.0, 1.0);
        float LOW = ${(SWORD_DMG * 1.5).toFixed(4)};
        vec3 lo = (vHp < LOW) ? vec3(0.34, 0.05, 0.03) : vec3(0.03, 0.30, 0.14);
        vec3 hi = (vHp < LOW) ? vec3(0.95, 0.22, 0.13) : vec3(0.16, 0.90, 0.46);
        vec3 col = mix(track, mix(lo, hi, g), f);
        // ── ★눈금(구분선): 한 대 = 한 칸 (오너 지시 2026-08-13 밤) ──
        // 폭이 고정이라 길이는 이제 "몇 %"만 말한다. **"몇 대"는 눈금이 말한다.**
        //   칸 수 = 최대 체력 / 칼 한 대 → 1핍 2칸 · 2핍 4칸 · 리더 6칸
        //   경계선은 칸 사이에만 선다(양 끝 0·segN 은 헤어라인이 이미 그린 자리다).
        // ★홈이 아니라 **겹치는 값**이다. 채움을 잘라 내면 17차에 기각된 「세 칸이
        //   합쳐진 느낌」이 그대로 돌아온다 - 채움 마스크 f 는 위에서 이미 끝났고
        //   여기서는 색만 어둡게 눌러 얹는다.
        float segN = max(1.0, floor(vN / ${SWORD_DMG.toFixed(4)} + 0.5));
        float s = vU.x * segN;                       // 0 .. segN (칸 단위 자리)
        float bi = floor(s + 0.5);                   // 가장 가까운 칸 경계 번호
        float inner = step(0.5, bi) * step(bi, segN - 0.5);   // 양 끝 경계는 뺀다
        float dT = abs(s - bi) * ar / segN;          // 그 경계까지 거리(높이 단위)
        float tick = inner * (1.0 - smoothstep(
          ${(BAR_TICK_HW - BAR_TICK_AA).toFixed(4)},
          ${(BAR_TICK_HW + BAR_TICK_AA).toFixed(4)}, dT));
        // ★눈금 색은 **바탕을 따라 뒤집힌다.** 채움 위에서는 제 색의 그림자(어두운 값)로,
        //   빈 트랙 위에서는 어두운 색 위 어두운 색이라 안 보이므로 한 단계 **밝은** 값으로.
        //   둘 다 바탕에서 파생한 배수라 이 바에 색이 하나도 안 늘어난다.
        //   (빈 구역에도 눈금이 서야 "이 놈이 원래 몇 대짜리인가"가 반피에서도 읽힌다.)
        vec3 tickCol = mix(track * ${BAR_TICK_LIFT.toFixed(2)},
                           col   * ${BAR_TICK_MUL.toFixed(2)}, f);
        col = mix(col, tickCol, tick);
        gl_FragColor = vec4(col, vA);
      }`,
  });
  const pipMesh = plateMesh(MAX_ENEMIES, pipMat,
    { aN: { arr: pipN, n: 1 }, aHp: { arr: pipHp, n: 1 }, aA: { arr: pipA, n: 1 } });

  // ── 인지 표식 ──
  const mkA = new Float32Array(MAX_ENEMIES * 4);
  const mkTint = new Float32Array(MAX_ENEMIES * 4 * 3);
  const markMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: false, fog: false,
    side: THREE.DoubleSide, blending: THREE.NormalBlending,
    uniforms: { uTex: { value: null } },
    vertexShader: `
      attribute float aA; attribute vec3 aTint;
      varying vec2 vU; varying float vA; varying vec3 vT;
      void main(){ vU = uv; vA = aA; vT = aTint;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `
      uniform sampler2D uTex;
      varying vec2 vU; varying float vA; varying vec3 vT;
      void main(){
        if (!(vA > 0.01)) discard;
        vec4 t = texture2D(uTex, vU);
        float a = t.a * vA;
        if (!(a > 0.02)) discard;
        // 색조는 **곱하기**다. 먹 테두리는 거의 0 이라 물들어도 검은 채로 남고
        // 종이색 속만 물든다(글자 형태가 안 무너진다).
        gl_FragColor = vec4(t.rgb * vT, a);
      }`,
  });
  const markMesh = plateMesh(MAX_ENEMIES, markMat,
    { aA: { arr: mkA, n: 1 }, aTint: { arr: mkTint, n: 3 } });
  try { markMat.uniforms.uTex.value = makeMarkTexture(); } catch (err) {
    if (DEV) console.warn('[enemy] 표식 텍스처를 못 구웠다. 표식 없이 돈다.', err);
  }

  // ── ★데미지 숫자 판 ──
  // 자리 한 칸 = 판 한 장. 뭉치 20개 × 다섯 자리 = 판 100장이 정점 버퍼 한 벌에 산다.
  const dgA = new Float32Array(DMG_MAX_POP * DMG_MAX_DIGITS * 4);        // 알파
  const dgTint = new Float32Array(DMG_MAX_POP * DMG_MAX_DIGITS * 4 * 3); // 글자 속 색(선형)
  const dmgMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: false, fog: false,
    side: THREE.DoubleSide, blending: THREE.NormalBlending,
    // 키라인·흰 테 색. ★선형 HDR 이다(위 FLASH_R 주석의 파이프라인 설명 참조).
    //   uOl = 제일 바깥 한 줄. 진한 밤색이고 **얇다**(4px). 밝은 흙바닥에서 흰 테가
    //         배경에 먹히는 것만 막는 역할이라, 이게 굵으면 글자가 갈색 테로 읽힌다.
    //   uRim = 그 안쪽 **흰 테**. 오너가 말한 "흰색 테두리"가 이 겹이다.
    // ★1.0 이 아니라 0.86 인 이유는 아래 DMG_TINT 주석과 같다 - ACES 가 입력을 1.75배로
    //   받으므로 1.0 은 그냥 날아가고 블룸(임계 1.02)에 걸려 글자가 번진다. 0.86 이면
    //   화면에서 흰색으로 읽히면서 안 번진다.
    uniforms: { uTex: { value: null },
                uOl: { value: new THREE.Vector3(0.016, 0.008, 0.007) },
                uRim: { value: new THREE.Vector3(0.86, 0.86, 0.87) } },
    vertexShader: `
      attribute float aA; attribute vec3 aTint;
      varying vec2 vU; varying float vA; varying vec3 vT;
      void main(){ vU = uv; vA = aA; vT = aTint;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `
      uniform sampler2D uTex; uniform vec3 uOl; uniform vec3 uRim;
      varying vec2 vU; varying float vA; varying vec3 vT;
      void main(){
        // ★!(a > x) 꼴. a <= x 로 쓰면 NaN 이 통과해 블룸이 화면을 검게 만든다(LOG 함정).
        if (!(vA > 0.004)) discard;
        vec4 t = texture2D(uTex, vU);
        float a = t.a * vA;
        if (!(a > 0.02)) discard;
        // R = 글자 속 · G = 외곽선 · B = 크림 테. 셋은 경계 한 겹에서만 섞이므로
        // 그냥 더하면 그게 곧 부드러운 전환이다(합은 언제나 1 언저리다).
        // 속은 **위가 밝고 아래가 짙다**(메이플 숫자의 세로 색계단). vU.y 는 칸 안의
        // 세로 자리라 그대로 계단이 된다(1 = 위).
        vec3 fill = mix(vT * vec3(1.0, 0.55, 0.14), vT, vU.y);
        gl_FragColor = vec4(uOl * t.g + uRim * t.b + fill * t.r, a);
      }`,
  });
  const dmgMesh = plateMesh(DMG_MAX_POP * DMG_MAX_DIGITS, dmgMat,
    { aA: { arr: dgA, n: 1 }, aTint: { arr: dgTint, n: 3 } });
  dmgMesh.renderOrder = 8;            // 핍·표식(7)보다 위. 숫자는 아무것에도 안 가린다
  try { dmgMat.uniforms.uTex.value = makeDigitTexture(); } catch (err) {
    if (DEV) console.warn('[enemy] 숫자 텍스처를 못 구웠다. 숫자 없이 돈다.', err);
  }
  // 글자 속 색(선형 HDR). 아래로 갈수록 셰이더가 주황 쪽으로 눕힌다.
  //   일반타 = 크림-금색 / 처치타 = 주황-빨강.
  // ── ★왜 1.0 이 아니라 0.6 대인가 (두 번 밟은 함정) ──
  // 이 값은 톤매핑 **전**이다. three 의 ACES 는 안에서 `color *= exposure / 0.6` 을 하고
  // (main.js exposure 1.05) 곧 **입력이 1.75배로 들어간다.** 그래서 1.0 으로 칠하면
  // 화면에서는 그냥 흰 글자가 나온다 - 실제로 첫 두 판이 그랬다.
  // 크림·금색을 남기려면 0.6 대에서 칠하고 채널 비율로만 색을 만들어야 한다.
  // ★블룸(임계 1.02)도 이 값으로 판정하므로 여기서 안 번지는 것이 덤으로 보장된다
  //   - 글자가 번지면 오히려 못 읽는다.
  // ★13차에 채움을 더 물들였다. 흰 테를 굵게 세우고 나니 속이 크림색이면 테와 안 갈려
  //   글자가 통째로 흰 덩어리로 읽힌다. 오너 지시대로 일반타는 노랑~주황, 처치타는 빨강.
  //   셰이더가 vU.y 로 아래를 더 주황 쪽에 눕히므로, 여기 값은 **위쪽 색**이다.
  const DMG_TINT_HIT = [0.82, 0.60, 0.12];    // 위 노랑 -> 아래 주황
  const DMG_TINT_KILL = [0.70, 0.20, 0.04];   // 위 주황 -> 아래 빨강
  // 뭉치 풀. 자릿수는 별도 배열에 담는다(뭉치당 DMG_MAX_DIGITS 칸, **1의 자리부터**).
  const dmgPops = [];
  for (let i = 0; i < DMG_MAX_POP; i++) {
    // seed = 자리별 세로 지터의 씨앗. 띄운 순번에서 받는다(결정론적. Math.random 금지)
    dmgPops.push({ on: false, x: 0, y: 0, z: 0, t: 0, n: 0, ox: 0, oy: 0, sc: 1, kill: false, seed: 0 });
  }
  const dmgDig = new Int8Array(DMG_MAX_POP * DMG_MAX_DIGITS);
  let dmgSpawned = 0, dmgBad = 0, dmgShown = 0;
  // 마지막으로 그린 뭉치의 칸 높이 / 화면 높이. 판독성 판정의 자다(아래 dmg 창구).
  let dmgFrac = 0, dmgFracKind = 0;
  // 칸 높이 중 **눈에 보이는 글자**(속 + 외곽선)가 차지하는 몫. 굽는 값에서 나온다:
  //   폰트 96px 의 숫자 높이는 대략 0.72*96 = 69px, 거기에 테 굵기가 붙고, 칸은 DIG_CH.
  //   판독성 판정은 속만이 아니라 이 값으로 본다(사람 눈에는 테까지가 글자다).
  const GLYPH_OF_CELL = (69 + DIG_W[0].ol) / DIG_CH;

  // 표식 색조. 발견은 주홍(경보), 수색·놓침은 종이색(중립), 공격은 진홍(임박).
  // ★2번(공격 쐐기)은 MARK_ATK_ON = false 라 지금은 아무도 안 읽는다. 되살릴 때 쓰라고 남긴다.
  const MK_TINT = [
    [1.00, 0.44, 0.32],     // 0 = !
    [0.96, 0.93, 0.85],     // 1 = ?
    [1.00, 0.30, 0.22],     // 2 = 공격 쐐기(꺼짐)
  ];

  // 이 놈에게 지금 무슨 표식을 붙일까. 우선순위가 곧 "제일 급한 정보"의 순서다.
  //   ① 공격 예고(쐐기 — ★MARK_ATK_ON 으로 꺼짐)  ② 수색(?)  ③ 쫓는 중인데 못 봄(? 깜빡)
  //   ④ 방금 발견(! 팝)  ⑤ 포기(? 페이드)
  // ★쐐기가 꺼져 있으면 이 분기 자체를 안 탄다 = 예고 중인 놈은 판을 한 장도 안 쓴다
  //   (알파 0 으로 그리는 게 아니라 아예 안 담는다).
  const _mk = { slot: 0, a: 0, sc: 1 };
  function markOf(e) {
    if (MARK_ATK_ON && e.wndT > 0) {
      _mk.slot = MARK_ATK; _mk.a = 1;
      _mk.sc = 1.0 + 0.30 * (1 - e.wndT / ATK_WIND);
      return _mk;
    }
    const g = e.grp;
    if (!g) return null;
    if (e.mode === 3) { _mk.slot = MARK_Q; _mk.a = 1; _mk.sc = 1; return _mk; }
    if (g.aggro && g.lostT > 0.12) {
      // ★이게 은신의 심장이다. "쫓고는 있는데 지금 나를 못 본다"는 상태를
      //   깜빡이는 물음표로 알려 준다. 이 신호가 없으면 수풀에 들어간 사람은
      //   자기 판단이 통했는지를 영영 알 수 없다(건틀릿 3/10 의 이유).
      _mk.slot = MARK_Q; _mk.a = 0.70 + 0.30 * Math.sin(T * 9 + e.phase); _mk.sc = 1;
      return _mk;
    }
    const sa = T - g.aggroAt;
    if (g.aggro && sa < MARK_FOUND) {
      _mk.slot = MARK_EX;
      _mk.a = sa > MARK_FOUND - 0.3 ? (MARK_FOUND - sa) / 0.3 : 1;
      _mk.sc = 1 + Math.max(0, 1 - sa * 7) * 0.55;      // 튀어나왔다 가라앉는다
      return _mk;
    }
    const sg = T - g.giveUpAt;
    if (sg >= 0 && sg < MARK_LOST_FADE) {
      _mk.slot = MARK_Q; _mk.a = 1 - sg / MARK_LOST_FADE; _mk.sc = 1;
      return _mk;
    }
    return null;
  }

  const _plR = new THREE.Vector3(), _plU = new THREE.Vector3();
  const _plQ = new THREE.Vector3();
  const PL_CORNER = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
  // 판 한 장을 정점 버퍼에 쓴다. hw/hh 는 반폭·반높이(m).
  // ★v0/v1 은 아틀라스가 여러 줄일 때만 준다(숫자만 두 줄이다). 안 주면 예전처럼 0~1 이라
  //   핍·표식 호출은 한 글자도 안 바뀐다.
  function putPlate(posArr, uvArr, o, cx, cy, cz, hw, hh, u0, u1, v0, v1) {
    const a0 = v0 === undefined ? 0 : v0, a1 = v1 === undefined ? 1 : v1;
    for (let k = 0; k < 4; k++) {
      const sx = PL_CORNER[k][0], sy = PL_CORNER[k][1];
      _plQ.set(cx, cy, cz).addScaledVector(_plR, sx * hw).addScaledVector(_plU, sy * hh);
      posArr[(o + k) * 3] = _plQ.x;
      posArr[(o + k) * 3 + 1] = _plQ.y;
      posArr[(o + k) * 3 + 2] = _plQ.z;
      uvArr[(o + k) * 2] = sx < 0 ? u0 : u1;
      uvArr[(o + k) * 2 + 1] = sy < 0 ? a0 : a1;
    }
  }

  // ★쐐기 제거의 증거 창구(진단 전용, 매 프레임 경로 아님).
  //   winding = 지금 예비 자세를 잡고 있는 놈 수 · slots = 지금 붙어 있는 표식 칸 번호들
  //   "winding 이 0 을 넘는데 slots 에 2 가 한 번도 안 뜬다" = 예고는 도는데 삼각형은 없다.
  function markCensus() {
    let winding = 0; const slots = [];
    for (let i = 0; i < live.length; i++) {
      const e = live[i];
      if (e.wndT > 0) winding++;
      const m = markOf(e);
      if (m && m.a > 0.01) slots.push(m.slot);
    }
    return { winding, slots };
  }

  // 이 거리 밖의 놈은 판을 안 그린다. 34m 카메라에서 화면 대각이 대략 이만큼이다.
  const PLATE_MAX_D = 28;
  let plateCount = { pip: 0, mark: 0 };
  function updatePlates() {
    if (!camera) return;
    _plR.setFromMatrixColumn(camera.matrixWorld, 0);
    _plU.setFromMatrixColumn(camera.matrixWorld, 1);
    const pPos = pipMesh.geometry.attributes.position.array;
    const pUv = pipMesh.geometry.attributes.uv.array;
    const mPos = markMesh.geometry.attributes.position.array;
    const mUv = markMesh.geometry.attributes.uv.array;
    let pn = 0, mn = 0;
    const cx0 = camera.position.x, cz0 = camera.position.z;
    for (let i = 0; i < live.length; i++) {
      const e = live[i];
      const dd = (e.pos.x - cx0) * (e.pos.x - cx0) + (e.pos.z - cz0) * (e.pos.z - cz0);
      if (dd > PLATE_MAX_D * PLATE_MAX_D) continue;
      const headY = e.pos.y + e.h * 1.02;
      // ── 체력 바 ──
      // ★★폭은 **한 값**이다(BAR_W). 개체마다 안 변한다.
      //   여태는 「폭 = maxHp x PIP_W」였다 - "화면에서 같은 길이가 늘 같은 타수"라는
      //   계약이었고 그건 그 자체로는 옳았지만, 오너가 화면에서 본 것은 그게 아니라
      //   **1핍 잡몹의 13.9px 짜리 점**이었다(리더는 41.5px. 실측). 그래서 기각됐다.
      //   → 「몇 대 더 때려야 하나」는 이제 셰이더의 **눈금**이 답한다(칸 = 칼 한 대).
      //     길이가 하던 말을 눈금이 이어받았고, 바는 어느 몹 머리에서도 같은 바다.
      // ★한 대에 죽는 놈은 안 그린다. 그 놈은 맞는 순간 시체가 되므로 바가 화면에 뜰
      //   일 자체가 없다(= 뜨면 그게 거짓말이다. 늘 가득 찬 바만 보여 준다).
      // ★18차: 그 조건을 `maxHp >= 2` 라고 적어 놨었다. 「핍 1 = 한 대」였을 때만 맞는
      //   말이라, 칼 데미지를 반으로 줄이면 **두 대 버티는 1핍 잡몹의 바가 통째로
      //   사라진다**(60% 가 그 놈이다). 뜻 그대로 다시 적는다 - "한 대 맞고도 사나".
      //   DMG_SCALE=1 이면 maxHp > 1 = 정수 maxHp 에서 `>= 2` 와 완전히 같은 집합이다.
      if (e.pipT > 0 && e.maxHp > SWORD_DMG + 1e-6 && pn < MAX_ENEMIES) {
        const o = pn * 4;
        const a = Math.min(1, e.pipT / PIP_FADE);
        const nMax = e.maxHp;
        putPlate(pPos, pUv, o, e.pos.x, headY + PIP_H * 1.9, e.pos.z,
          BAR_W * 0.5, PIP_H * 0.5, 0, 1);
        // ★올림(ceil)을 걷어냈다. 칸 그림일 때는 0.3 체력도 "한 칸"으로 올려야 했지만
        //   연속 바는 남은 체력을 **있는 그대로** 그린다(귀환 회복 RETURN_HEAL 로
        //   소수 체력이 실제로 생긴다 - 그때 바가 차오르는 게 보인다).
        const hpLeft = Math.max(0, Math.min(nMax, e.hp));
        for (let k = 0; k < 4; k++) {
          pipN[o + k] = nMax; pipHp[o + k] = hpLeft; pipA[o + k] = a;
        }
        pn++;
      }
      // ── 표식 ──
      const mk = markOf(e);
      if (mk && mk.a > 0.01 && mn < MAX_ENEMIES) {
        const o = mn * 4;
        const hw = MARK_SZ * 0.5 * mk.sc;
        // ★머리에 더 붙인다. 처음엔 발밑에서 1.99m 였는데 실사에서 "누구 것인지"가
        //   한 박자 늦게 읽혔다(고블린 키가 1.30m 라 머리 위 0.69m 는 몸 하나 반이다).
        putPlate(mPos, mUv, o, e.pos.x, headY + MARK_SZ * 0.50 + PIP_H * 1.5, e.pos.z,
          hw, hw, mk.slot / MARK_N, (mk.slot + 1) / MARK_N);
        const c = MK_TINT[mk.slot];
        for (let k = 0; k < 4; k++) {
          mkA[o + k] = mk.a;
          mkTint[(o + k) * 3] = c[0]; mkTint[(o + k) * 3 + 1] = c[1]; mkTint[(o + k) * 3 + 2] = c[2];
        }
        mn++;
      }
    }
    // 안 쓴 자리는 알파 0 으로 덮는다(= 인덱스 범위를 줄이는 것과 같은 효과).
    pipMesh.geometry.setDrawRange(0, pn * 6);
    markMesh.geometry.setDrawRange(0, mn * 6);
    pipMesh.visible = pn > 0;
    markMesh.visible = mn > 0 && !!markMat.uniforms.uTex.value;
    if (pn) {
      pipMesh.geometry.attributes.position.needsUpdate = true;
      pipMesh.geometry.attributes.uv.needsUpdate = true;
      pipMesh.geometry.attributes.aN.needsUpdate = true;
      pipMesh.geometry.attributes.aHp.needsUpdate = true;
      pipMesh.geometry.attributes.aA.needsUpdate = true;
    }
    if (mn) {
      markMesh.geometry.attributes.position.needsUpdate = true;
      markMesh.geometry.attributes.uv.needsUpdate = true;
      markMesh.geometry.attributes.aA.needsUpdate = true;
      markMesh.geometry.attributes.aTint.needsUpdate = true;
    }
    plateCount.pip = pn; plateCount.mark = mn;
  }

  // -------------------------------------------------------------------------
  // ── ★큰 데미지 숫자 (오너 지시 2026-08-12) ──
  //
  // 명중한 그 지점 위에 숫자 뭉치가 톡 튀어오른다. 옛 주홍 틴트 플래시가 하던 일
  // ("맞았다")을 이제 이 숫자가 한다 - 그런데 플래시가 못 하던 말을 하나 더 한다:
  // **얼마나** 아팠는가. 그래서 값은 늘 실제로 가한 피해에서 나온다(SWORD_DMG·DMG_SHOW).
  //
  // 늙는 시계는 **게임시계**(update 가 받는 dt)다. 히트스톱이 dt 를 0 으로 눌러 두면
  // 숫자도 같이 붙들린다 = 멈춘 화면에서 숫자만 혼자 흘러가는 그림이 안 나온다.
  // -------------------------------------------------------------------------
  const _dcen = new THREE.Vector3();

  // 숫자 뭉치 하나 띄우기. amount = 화면에 띄울 값(이미 환산된 수), kill = 처치타인가
  function spawnDmgPop(x, y, z, amount, kill) {
    // ★!(a > x) 꼴로 거른다. NaN 이 들어오면 자리 좌표가 통째로 NaN 이 되어 판 하나가
    //   화면을 가로지르는 삼각형이 된다(그리고 아무도 원인을 못 찾는다).
    if (!(amount > 0)) { dmgBad++; return; }
    if (!(isFinite(x) && isFinite(y) && isFinite(z))) { dmgBad++; return; }
    let v = Math.round(amount);
    if (!(v > 0)) v = 1;
    if (v > 99999) v = 99999;              // 다섯 자리 상한(판 개수 계약)
    // 빈자리 찾기. 다 찼으면 **제일 오래된 것**을 밀어낸다(최신 타격이 늘 보여야 한다).
    let slot = 0, oldT = -1, found = false;
    for (let i = 0; i < DMG_MAX_POP; i++) {
      if (!dmgPops[i].on) { slot = i; found = true; break; }
      if (dmgPops[i].t > oldT) { oldT = dmgPops[i].t; slot = i; }
    }
    // ── 겹침 흩뿌림 ──
    // 광역타로 한 번에 여럿을 베면 숫자가 한 자리에 포개져 한 덩어리로 읽힌다.
    // 지금 이 근처에 떠 있는 뭉치 수를 세서 좌·우로 번갈아 비키고 조금씩 올린다.
    let near = 0;
    const R2 = DMG_NEAR * DMG_NEAR;
    for (let i = 0; i < DMG_MAX_POP; i++) {
      const q = dmgPops[i];
      if (!q.on || (found && i === slot)) continue;
      const dx = q.x - x, dy = q.y - y, dz = q.z - z;
      if (dx * dx + dy * dy + dz * dz < R2) near++;
    }
    const p = dmgPops[slot];
    // ★t 가 음수로 시작한다 = 아직 안 뜬 상태(위 DMG_DELAY). 0 을 넘는 순간 튀어오른다.
    p.on = true; p.t = -DMG_DELAY;
    p.x = x; p.y = y; p.z = z;
    p.kill = !!kill;
    p.sc = kill ? DMG_KILL_SC : 1;
    // ★비키는 폭 (17차). 글자가 0.62 -> 0.34m 로 작아졌으니 옆으로 비키는 거리도 같이
    //   줄여야 "흩어진 네 뭉치"가 아니라 "한 사건의 네 숫자"로 읽힌다. 다만 세로는
    //   반대로 **키운다** — 가로로만 벌리면 세 자리씩 넷이 화면을 가로지른다.
    //   가로 0.30/0.24 -> 0.24/0.19 · 세로 0.13 -> 0.20.
    p.ox = near === 0 ? 0 : ((near & 1) ? 1 : -1) * (0.24 + 0.19 * ((near - 1) >> 1));
    p.oy = 0.20 * near;
    // ★자리별 세로 지터의 씨앗. 띄운 순번 + 값이라 뭉치마다 다르고, 같은 뭉치는
    //   사는 동안 안 바뀐다. Math.random 을 쓰면 프레임마다 다시 뽑혀 글자가 떤다.
    p.seed = (dmgSpawned * 7 + v) % 9973;
    // 자릿수 쪼개기. 1의 자리부터 담는다(그리는 쪽이 거꾸로 읽는다).
    const base = slot * DMG_MAX_DIGITS;
    let n = 0, r = v;
    while (n < DMG_MAX_DIGITS) {
      dmgDig[base + n] = r % 10; r = (r / 10) | 0; n++;
      if (r <= 0) break;
    }
    p.n = n;
    dmgSpawned++;
  }

  // 늙히고(게임시계) 정점 버퍼에 쓴다. updatePlates 와 같은 틀이라 드로우콜은 1이다.
  function updateDmgPops(dt) {
    let alive = 0;
    for (let i = 0; i < DMG_MAX_POP; i++) {
      const p = dmgPops[i];
      if (!p.on) continue;
      p.t += dt;
      // ★!(t < TTL) 꼴. NaN 이 끼면 여기서 즉시 거둬진다(영원히 떠 있는 판이 없다).
      //   ★음수 t(지연 대기)는 NaN 이 아니므로 이 문턱을 통과한다 - 의도한 대로다.
      if (!(p.t < DMG_TTL)) { p.on = false; continue; }
      if (p.t < 0) continue;                       // 아직 뜰 시각이 아니다(안 센다)
      alive++;
    }
    if (!camera || !dmgMat.uniforms.uTex.value || alive === 0) {
      dmgMesh.visible = false; dmgShown = 0; return;
    }
    _plR.setFromMatrixColumn(camera.matrixWorld, 0);
    _plU.setFromMatrixColumn(camera.matrixWorld, 1);
    const dPos = dmgMesh.geometry.attributes.position.array;
    const dUv = dmgMesh.geometry.attributes.uv.array;
    const cx0 = camera.position.x, cz0 = camera.position.z;
    let dn = 0;
    for (let i = 0; i < DMG_MAX_POP; i++) {
      const p = dmgPops[i];
      if (!p.on || p.t < 0) continue;              // 지연 대기 중인 뭉치는 안 그린다
      const ddx = p.x - cx0, ddz = p.z - cz0;
      if (ddx * ddx + ddz * ddz > PLATE_MAX_D * PLATE_MAX_D) continue;
      // ── 모션 세 마디 ──
      const t = p.t;
      let a = 1, sc, up;
      if (t < DMG_RISE) {
        // ① 톡 튀어오른다. 끝이 빨리 잦아드는 easeOut 이라 "튀었다"가 남는다.
        const u = t / DMG_RISE;
        const e = 1 - (1 - u) * (1 - u);
        up = DMG_UP1 * e;
        sc = 0.42 + 0.86 * e;              // 0.42 -> 1.28 (한 번 크게 부풀었다가)
      } else if (t < DMG_RISE + DMG_HOLD) {
        // ② 잠깐 선다. 부푼 것만 0.09초에 제 크기로 가라앉는다.
        const u = (t - DMG_RISE) / DMG_HOLD;
        up = DMG_UP1 + 0.05 * u;
        sc = 1.28 - 0.28 * Math.min(1, u * 3.4);
      } else {
        // ③ 흐려지며 오른다.
        const u = (t - DMG_RISE - DMG_HOLD) / DMG_FADE;
        up = DMG_UP1 + 0.05 + DMG_UP2 * u;
        sc = 1;
        a = 1 - u * u;
      }
      const cellH = DMG_H * p.sc * sc;
      const cellW = cellH * (DIG_CW / DIG_CH);
      const adv = cellW * digAdv;
      const x0 = p.ox - adv * (p.n - 1) * 0.5;
      const cy = p.y + up + p.oy;
      // ── ★"게임 거리에서 읽히나"를 눈이 아니라 수로 남긴다 ──
      // 칸 높이가 화면 높이의 몇 분의 몇인가. 카메라까지의 실제 거리로 재므로
      // fov·거리·줌이 바뀌면 이 값이 같이 움직인다(상수로 박은 산수가 아니다).
      // 글자 획은 칸의 GLYPH_OF_CELL 배다(칸에는 외곽선 여백이 들어 있다).
      {
        const dcz = camera.position.y - cy;
        const dcam = Math.sqrt(ddx * ddx + ddz * ddz + dcz * dcz);
        if (dcam > 0.5) {
          dmgFrac = cellH / (2 * Math.tan(camera.fov * Math.PI / 360) * dcam);
          dmgFracKind = p.kill ? 1 : 0;
        }
      }
      const c = p.kill ? DMG_TINT_KILL : DMG_TINT_HIT;
      // 처치타는 아틀라스 아랫줄(흰 테가 더 굵게 구워진 줄)을 본다.
      const vRow = p.kill ? 1 : 0;
      const v0 = vRow / DIG_ROWS, v1 = (vRow + 1) / DIG_ROWS;
      const base = i * DMG_MAX_DIGITS;
      // ── ★오른쪽 자리부터 쓴다 (오너 "글자도 조금씩 겹쳐져 있다") ──
      // 같은 드로우콜 안에서는 **나중에 쓴 판이 위**다(깊이검사가 꺼져 있다).
      // 그래서 거꾸로 돌아야 왼쪽 글자가 오른쪽 글자를 덮는다. 메이플이 그렇게 겹친다 -
      // 글을 읽는 방향과 겹치는 방향이 같아야 숫자가 한 덩어리로 읽힌다.
      for (let k = p.n - 1; k >= 0; k--) {
        if (dn >= DMG_MAX_POP * DMG_MAX_DIGITS) break;
        const d = dmgDig[base + p.n - 1 - k];      // 1의 자리부터 담았으니 거꾸로 읽는다
        const o = dn * 4;
        // ── ★자리마다 높이가 다르다 (오너 "높낮이가 조금씩 다 다르고") ──
        //   지터 = 뭉치 씨앗과 자리로 만든 결정론적 해시. Math.random 을 안 쓴다 -
        //          매 프레임 다시 뽑으면 숫자가 사는 내내 덜덜 떤다.
        //   아치 = 가운데 자리가 살짝 올라간다. 지터가 흩는 것을 한 덩어리로 묶는 뼈대다.
        const hSign = hash1(p.seed * 131.7 + k * 37.3);
        const hAmp = hash1(p.seed * 57.13 + k * 91.7 + 11.0);
        const amp = (DMG_JIT_MIN + (DMG_JIT_MAX - DMG_JIT_MIN) * hAmp) * cellH;
        const jy = hSign < 0.5 ? -amp : amp;
        const u = p.n > 1 ? (2 * k) / (p.n - 1) - 1 : 0;
        const arch = DMG_ARCH * cellH * (1 - u * u);
        // 자리 이동은 **카메라 오른쪽**으로 준다. 월드 x 로 주면 시점이 돌 때 숫자가
        // 앞뒤로 늘어져 보인다(판은 이미 빌보드라 가로축이 곧 화면 가로축이다).
        _dcen.set(p.x, cy + jy + arch, p.z).addScaledVector(_plR, x0 + adv * k);
        putPlate(dPos, dUv, o, _dcen.x, _dcen.y, _dcen.z,
          cellW * 0.5, cellH * 0.5, d / 10, (d + 1) / 10, v0, v1);
        for (let q = 0; q < 4; q++) {
          dgA[o + q] = a;
          dgTint[(o + q) * 3] = c[0];
          dgTint[(o + q) * 3 + 1] = c[1];
          dgTint[(o + q) * 3 + 2] = c[2];
        }
        dn++;
      }
    }
    dmgMesh.geometry.setDrawRange(0, dn * 6);
    dmgMesh.visible = dn > 0;
    if (dn) {
      dmgMesh.geometry.attributes.position.needsUpdate = true;
      dmgMesh.geometry.attributes.uv.needsUpdate = true;
      dmgMesh.geometry.attributes.aA.needsUpdate = true;
      dmgMesh.geometry.attributes.aTint.needsUpdate = true;
    }
    dmgShown = dn;
  }

  function clearDmgPops() {
    for (let i = 0; i < DMG_MAX_POP; i++) dmgPops[i].on = false;
    dmgMesh.geometry.setDrawRange(0, 0);
    dmgMesh.visible = false;
    dmgShown = 0;
  }

  // ── 상태 ──
  let T = 0;                       // 시스템 내부 시간(정지 중엔 안 흐른다)
  let hp = PLAYER_MAX_HP;
  let kills = 0;
  let dead = false;
  let deadUntil = 0;
  let iframe = 0;
  let hurtFlash = 0;
  let swingId = 0;
  let lastSwingT = -10;
  let hotState = false;
  let hasPrevBlade = false;
  // ── 한 방짜리 기술의 캐스트 (2026-08-12 13차) ──
  // 수면참·횡일섬은 "크게 한 번"이다. 그런데 스윙 번호는 hot 이 켜질 때마다 발급되므로,
  // 한 캐스트 안에서 hot 이 두 번 켜지면 같은 요괴가 두 번 맞는다. SWING_GAP 은
  // **떨림**(0.004~0.064초 꺼짐)만 묶으라고 있는 값이라 0.2초 넘게 벌어진 재점화는 못 막는다.
  // 실측에서 회복 동작의 꼬리가 슬램에서 0.223초 뒤에 다시 켜진 판이 나왔다(경계 바로 위).
  // 그래서 **한 방짜리 캐스트는 번호를 하나만 쓴다**. 시간 상수가 아니라 캐스트 신원으로
  // 막으므로 클립 길이·재생속도가 바뀌어도 안 흔들린다.
  let castId = -1;                 // main.js 가 준 이번 캐스트 번호(공격이 새로 시작될 때만 바뀐다)
  let castSwing = -1;              // 그 캐스트가 이미 쓴 스윙 번호. -1 = 아직 안 썼다
  let dbgLine = null;
  // 몸 충돌 켜기/끄기. 껐을 때 어떻게 되는지(요괴가 등 뒤 0.1m 에 달라붙는지)를
  // 숫자로 다시 확인할 수 있어야 이 값이 왜 필요한지 나중에도 증명된다.
  let bodyPush = true;
  // 길찾기 켜기/끄기. 끄면 예전처럼 플레이어 쪽으로 직진만 한다(A/B 비교용).
  let usePath = true;
  // 공격 방향 스냅 진행 상태. main.js 의 루프를 안 건드리려고 여기서 굴린다
  // (게임 시계 dt 를 쓰므로 히트스톱·정지와 같은 시간을 산다).
  let snap = null;                 // { obj, from, delta, t, dur }
  let snapOn = true;               // 검증용 스위치(끄면 예전처럼 안 돈다)
  // 검증용. 최근 스윙별 명중 수(한 번에 여러 마리가 맞는지, 같은 적이 두 번
  // 맞지는 않는지 콘솔에서 바로 본다). 8개짜리 링이라 안 자란다.
  const hitLog = [];
  // ★처치 기록. kills 를 올리는 자리가 이 파일에 한 군데뿐이라 이게 곧 전수 기록이다.
  //   "유령 증가" 신고가 들어오면 여기부터 본다(onScreen=false 면 화면 밖 처치다).
  const killLog = [];

  // -------------------------------------------------------------------------
  // 무리 배치
  // -------------------------------------------------------------------------
  // ★맵이 로드된 뒤에 부른다(main.js 가 loadLevel 을 먼저 await 한다).
  //   격자를 콜라이더에서 뽑기 때문에 순서가 뒤집히면 통째로 빈 격자가 나온다.
  NAV.build();
  ST.build();

  const GROUPS = groupsFromMobs(opts.mobs);
  if (!GROUPS.length) console.warn('[enemy] 무리 좌표를 못 받았다. 필드가 빈 채로 돈다.');

  const groups = [];
  for (let gi = 0; gi < GROUPS.length; gi++) {
    const cfg = GROUPS[gi];
    const g = {
      idx: gi, cx: cfg.pos[0], cz: cfg.pos[1],
      spots: [], aggro: false, returning: false, respawnAt: -1, tmp: false,
      lostT: 0,                    // 플레이어를 놓친 채로 흐른 시간(은신 이탈 판정)
      searching: false,            // 놓치고 마지막 자리를 뒤지는 중인가
      seenX: undefined, seenZ: undefined,   // 마지막으로 플레이어를 본 자리
      // ── 인지 표식용 시각 (9차) ──
      // ★표식은 "지금 상태"가 아니라 "**언제** 바뀌었나"를 알아야 한다. 발견은
      //   1.4초만 팝하고, 포기는 페이드로 스러져야 "놓쳤다"가 그림으로 읽힌다.
      aggroAt: -99,                // 마지막으로 나를 발견한 시각
      giveUpAt: -99,               // 수색을 접고 돌아선 시각
    };
    for (let k = 0; k < cfg.count; k++) {
      const ang = (k / cfg.count) * Math.PI * 2 + gi * 0.7;
      const rr = cfg.radius * (0.45 + 0.55 * hash1(gi * 31 + k));
      g.spots.push({
        home: homeAt(g.cx + Math.cos(ang) * rr, g.cz + Math.sin(ang) * rr),
        // 무리마다 한 마리는 두목이다. 크고 단단해서 어느 놈을 먼저 벨지 고르게 된다.
        leader: k === 0,
        seed: gi * 101 + k * 17,
        enemy: null,
      });
    }
    groups.push(g);
  }

  function spawnAt(spot, g) {
    if (freeTop <= 0) return null;
    const e = pool[--freeTop];
    e.pos.copy(spot.home);
    e.home = spot.home;
    e.spot = spot;
    e.grp = g;
    e.mode = 0;
    e.maxHp = spot.leader ? 3 : (hash1(spot.seed) < 0.4 ? 2 : 1);
    e.hp = e.maxHp;
    // ── 추격 속도 (9차 상향) ──
    // ★규칙: **플레이어 걷기(1.71) < 요괴 < 플레이어 달리기(3.20).**
    //   옛값(1.72~2.13)은 걷기와 거의 같아서, 달리기 한 번이면 자동으로 떨어졌다.
    //   그래서 수풀에 들어갈 이유가 없었다(건틀릿 손맛 8번).
    //   지금은 달리기와의 차가 0.42~0.90m/s 다. 10m 를 벌려면 11~24초를 계속
    //   달려야 하고 그 사이 리쉬(24m)에 안 걸리게 각도를 잡아야 한다 = 비싸다.
    //   수풀은 반대로 1.5초면 확실히 끊긴다 = **수풀에 일이 생겼다.**
    // ★두목은 여전히 한 단 느리다(둔중한 놈이 하나 섞여야 무리가 한 덩어리로 안 읽힌다).
    // ★Run 클립 재생속도 = 이동속도 / 2.35 라 0.98~1.18 대역이다(옛 0.73~0.91).
    //   1.0 근처가 클립이 원래 의도한 보폭이라 발 미끄러짐도 같이 줄었다.
    e.speed = spot.leader ? 2.30 : 2.48 + hash1(spot.seed + 5) * 0.30;
    e.phase = hash1(spot.seed + 9) * 6.283;
    e.yaw = hash1(spot.seed + 13) * 6.283;
    e.flash = 0; e.kbT = 0; e.sqT = 0; e.kb.set(0, 0, 0);
    e.atkCd = 0.3 + hash1(spot.seed + 21) * 0.6;
    e.lastSwing = -1;
    e.atkT = 0; e.hitT = -1;
    e.wndT = 0; e.stunT = 0; e.pipT = 0;
    // 경로 재계산 시각을 개체마다 어긋나게 둔다(한 프레임에 40마리가 몰리면 튄다)
    e.pathT = hash1(spot.seed + 31) * REPATH;
    e.direct = true; e.tx = e.pos.x; e.tz = e.pos.z;
    e.sideT = 0;
    // 막혔을 때 도는 방향은 개체마다 고정이다. 무리가 좌우로 갈라져 양쪽으로 돌아 나온다.
    e.sideS = hash1(spot.seed + 41) < 0.5 ? -1 : 1;
    e.wantD = 0; e.gotD = 0; e.chkT = 0;
    e.searchT = 0; e.searchX = e.pos.x; e.searchZ = e.pos.z; e.searchYaw = e.yaw;
    e.tint = (hash1(spot.seed + 3) * TINTS.length) | 0;
    // 몸집. 기본 키 1.30 에 곱한다. 두목은 한 뼘 더 크고(1.45m) 졸개는 1.20~1.30m.
    // 플레이어 1.75 대비 69~83% 라 "확실히 작지만 얕보이지는 않는" 대역이다.
    e.size = (spot.leader ? 1.06 : 0.92) + hash1(spot.seed + 7) * 0.06;
    e.h = GOB_H * e.size;
    e.spawnT = T;
    // 보이는 몸을 붙인다. 풀이 비면(상한 초과) 눈에 안 보이는 채로 돈다.
    // ★null 을 그대로 두고 아래 코드가 전부 e.vis 를 검사한다. 여기서 던지면
    //   무리 하나가 못 서는 정도가 아니라 게임이 통째로 멈춘다.
    e.vis = takeVis();
    if (e.vis) {
      e.vis.grp.scale.setScalar(K_H * e.size);
      e.vis.grp.position.set(e.pos.x, e.pos.y, e.pos.z);
      e.vis.grp.rotation.set(0, e.yaw, 0);
      e.vis.mat.color.copy(TINTS[e.tint]);
      e.vis.mat.emissive.setScalar(0);
      scene.add(e.vis.grp);
      playClip(e.vis, 'Idle', 1, 0);
    }
    spot.enemy = e;
    live.push(e);
    return e;
  }

  function despawn(i) {
    const e = live[i];
    if (e.spot) e.spot.enemy = null;
    e.spot = null; e.grp = null; e.home = null;
    giveVis(e.vis); e.vis = null;
    const last = live.pop();
    if (last !== e) live[i] = last;
    pool[freeTop++] = e;
  }

  function aggroGroup(g) {
    if (g.aggro) return;
    g.aggro = true;
    g.returning = false;
    g.searching = false;
    g.lostT = 0;
    // ★발견 시각을 찍는다. 머리 위 「!」가 이 값으로 1.4초만 뜬다.
    g.aggroAt = T;
    g.giveUpAt = -99;
    let k = 0;
    for (const s of g.spots) {
      if (!s.enemy) continue;
      s.enemy.mode = 1;
      // ★옛 코드는 여기서 flash 0.45 를 줬다(알아챈 순간 흰 번쩍).
      //   지금 flash 는 **피격 전용**이다. 같은 신호가 "맞았다"와 "발견했다"를
      //   둘 다 뜻하면 둘 다 안 읽힌다. 발견은 머리 위 「!」가 맡는다.
      // ★공격 쿨을 개체마다 흩어 놓는다. 이게 없으면 넷이 나란히 달려와 같은
      //   프레임에 사거리에 들어오고, 그때부터 **한 놈처럼** 같은 박자로 때린다.
      //   한 주기(1.2초)를 마릿수로 나눠 배정하고 hash 로 한 번 더 흔든다.
      const n = g.spots.length || 1;
      s.enemy.atkCd = ENEMY_ATK_CD * ((k + hash1(s.seed + 63)) / n);
      k++;
    }
  }

  // 리쉬. 자리에서 너무 멀어지면 무리 전체가 포기하고 돌아간다.
  // ★이게 없으면 맵 전체를 끌고 다닐 수 있어서 "어디까지 당길까"가 사라진다.
  function leashGroup(g) {
    g.aggro = false;
    g.searching = false;
    g.returning = true;            // 집에 닿기 전까지는 거리로 다시 안 붙는다
    g.lostT = 0;
    g.giveUpAt = T;                // 「?」가 페이드로 스러진다 = "포기했다"
    for (const s of g.spots) if (s.enemy) {
      s.enemy.mode = 2; s.enemy.sideT = 0;
      s.enemy.wndT = 0; s.enemy.atkT = 0; s.enemy.hitT = -1;   // 들던 칼도 거둔다
    }
  }

  // ── 놓쳤다 ──
  // ★곧장 돌아서면 "스위치가 꺼졌다"로 읽힌다. v72 QA 가 "수색 동작이 없다"고
  //   적은 게 그것이다. 마지막 목격 지점까지 가 보고 잠깐 두리번거린 다음에 돌아간다.
  //   그 몇 초가 **숨은 사람에게는 긴장이고, 본 사람에게는 납득**이다.
  function searchGroup(g) {
    g.aggro = false;
    g.searching = true;
    g.lostT = 0;
    for (const s of g.spots) {
      const e = s.enemy;
      if (!e) continue;
      e.mode = 3;
      e.sideT = 0;
      e.atkT = 0; e.hitT = -1; e.wndT = 0;     // 휘두르던 칼은 거둔다
      e.searchT = SEARCH_MIN + hash1(s.seed + 51) * (SEARCH_MAX - SEARCH_MIN);
      // 마지막으로 본 자리. 아직 한 번도 못 봤으면(있을 수 없지만) 제자리를 본다.
      e.searchX = g.seenX === undefined ? e.pos.x : g.seenX;
      e.searchZ = g.seenZ === undefined ? e.pos.z : g.seenZ;
      e.searchYaw = Math.atan2(e.searchX - e.pos.x, e.searchZ - e.pos.z);
      if (!isFinite(e.searchYaw)) e.searchYaw = e.yaw;
    }
  }

  function resetField() {
    while (live.length) despawn(live.length - 1);
    for (let i = groups.length - 1; i >= 0; i--) {
      if (groups[i].tmp) { groups.splice(i, 1); continue; }
      const g = groups[i];
      g.aggro = false; g.returning = false; g.searching = false; g.respawnAt = -1;
      g.lostT = 0; g.seenX = undefined; g.seenZ = undefined;
      g.aggroAt = -99; g.giveUpAt = -99;
      for (const s of g.spots) spawnAt(s, g);
    }
    for (const c of corpses) if (c.on) endCorpse(c);
    // 판을 새로 깔면 떠 있던 숫자도 같이 거둔다(없으면 이전 판의 숫자가 허공에 남는다).
    clearDmgPops();
  }

  // ── HUD (CSS 는 파일 안 만들고 여기서 주입) ──
  const st = document.createElement('style');
  st.textContent =
    '#eHud{position:fixed;left:16px;bottom:16px;z-index:6;user-select:none;pointer-events:none;' +
    'font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif}' +
    '#eBar{width:230px;height:13px;border:1px solid #2c4a63;border-radius:7px;background:#0b1320;overflow:hidden}' +
    '#eFill{height:100%;width:100%;background:linear-gradient(90deg,#2ee08a,#7ff0c0);' +
    'transition:width .12s linear}' +
    '#eTxt{margin-top:6px;font-size:12px;color:#7b93a8;letter-spacing:.5px}' +
    // 처치 숫자는 **튀어야** 한다. 조용히 1 올라가면 아무도 안 본다.
    '#eTxt b{color:#bfe6ff;font-weight:700;font-size:15px;display:inline-block;' +
    'transform-origin:center bottom;transition:transform .12s cubic-bezier(.2,1.6,.4,1),color .18s}' +
    '#eTxt b.pop{transform:scale(1.3)}' +
    '#eTxt b.s1{color:#ffd479}#eTxt b.s2{color:#ff9a5a}#eTxt b.s3{color:#ff6a6a}' +
    '#eHurt{position:fixed;inset:0;z-index:5;pointer-events:none;opacity:0;' +
    'box-shadow:inset 0 0 130px 30px rgba(200,20,40,.85)}' +
    '#eDead{position:fixed;left:50%;top:44%;transform:translate(-50%,-50%);z-index:7;' +
    'pointer-events:none;font-size:34px;font-weight:800;letter-spacing:3px;color:#ff7b7b;' +
    'text-shadow:0 0 20px #6a0d18,0 3px 6px #000;opacity:0;' +
    'font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif}';
  document.head.appendChild(st);
  const hud = document.createElement('div');
  hud.id = 'eHud';
  hud.innerHTML = '<div id="eBar"><div id="eFill"></div></div><div id="eTxt">처치 <b>0</b></div>';
  document.body.appendChild(hud);
  const hurtEl = document.createElement('div'); hurtEl.id = 'eHurt';
  document.body.appendChild(hurtEl);
  const deadEl = document.createElement('div'); deadEl.id = 'eDead';
  deadEl.textContent = '쓰러졌다';
  document.body.appendChild(deadEl);
  const fillEl = document.getElementById('eFill');
  const txtEl = document.getElementById('eTxt');
  let hudHp = -1, hudKills = -1;

  function syncHud() {
    if (hudHp !== hp) {
      hudHp = hp;
      const r = Math.max(0, hp) / PLAYER_MAX_HP;
      fillEl.style.width = (r * 100).toFixed(1) + '%';
      fillEl.style.background = r > 0.5 ? 'linear-gradient(90deg,#2ee08a,#7ff0c0)'
        : r > 0.25 ? 'linear-gradient(90deg,#e0c22e,#f0e07f)'
          : 'linear-gradient(90deg,#e04a2e,#f08f7f)';
    }
    if (hudKills !== kills) {
      const up = hudKills >= 0 && kills > hudKills;    // 첫 그리기(-1)는 안 튄다
      hudKills = kills;
      txtEl.innerHTML = '처치 <b>' + kills + '</b>';
      if (up) {
        // 1.3배로 튀었다가 돌아온다. 연속 처치 중이면 색도 같이 올라간다.
        const b = txtEl.querySelector('b');
        const s = killStreak;
        b.className = (s >= 5 ? 's3' : s >= 3 ? 's2' : s >= 1 ? 's1' : '') + ' pop';
        // 다음 프레임에 클래스를 빼야 transition 이 돈다(같은 프레임에 빼면 안 돈다)
        requestAnimationFrame(() => requestAnimationFrame(() => {
          b.className = b.className.replace(' pop', '');
        }));
      }
    }
  }
  // 처치 스트릭. 2초 안에 또 잡으면 올라간다(소리 피치와 같은 규칙).
  let killStreak = 0, lastKillT = -99;
  function bumpStreak() {
    killStreak = (T - lastKillT < 2.0) ? killStreak + 1 : 0;
    lastKillT = T;
    return killStreak;
  }
  syncHud();

  // -------------------------------------------------------------------------
  // 두 동강 (스킨드 메시 판)
  //
  // 덩어리 시절엔 InstancedMesh 를 두 벌 그리고 셰이더에서 평면 반대쪽을 discard 했다.
  // 그 수법은 **스킨드 메시에도 그대로 통한다.** 실제로 확인한 것과 못 하는 것:
  //   되는 것  : 절단 평면 discard, 속살 색(뒷면), 절단면 테두리 → 그대로 된다.
  //   안 되는 것: 두 조각이 **따로 굴러가는 것.** 뼈가 한 벌이라 조각마다 다른 자세를
  //              가질 수가 없다. 억지로 하려면 시체마다 뼈를 한 벌 더 세워야 하는데
  //              (마리당 24개 x 6구), 34m 쿼터뷰에서 1.3m 짜리가 굴러가는 궤적 차이는
  //              화면에서 몇 픽셀이다. 값이 안 나온다.
  // 그래서 **벌어지되 같이 무너진다**로 정했다.
  //   1) 죽은 순간 포즈로 정지(믹서를 안 돌린다)
  //   2) 두 조각이 절단면 법선 방향으로 서로 반대로 벌어진다(셰이더 uSep, 최대 22cm)
  //   3) 몸 전체가 칼이 지나간 쪽으로 꺾이며 쓰러지고 가라앉는다
  //   4) 마지막 0.55초에 페이드아웃
  // "베였다"의 신호는 **밝은 절단면 테두리 + 벌어진 틈 + 그 틈으로 보이는 속살**이다.
  // 셋 다 남아 있다.
  function spawnCorpse(vis, e, nx, ny, nz, hitP, kickX, kickZ) {
    if (!vis) return;
    const c = corpses[corpseRing];
    corpseRing = (corpseRing + 1) % MAX_CORPSES;
    if (c.on) endCorpse(c);                       // 자리가 모자라면 제일 오래된 걸 치운다
    c.on = true;
    c.vis = vis;
    c.life = 0;
    c.pos.copy(e.pos);
    c.yaw = e.yaw;
    c.size = e.size;
    c.cutW.set(nx, ny, nz).normalize();
    c.cutP.copy(hitP);
    // 쓰러지는 축 = 밀려나는 방향에 수직인 수평축. 칼이 지나간 쪽으로 넘어간다.
    if (Math.abs(kickX) + Math.abs(kickZ) < 1e-4) c.fallAxis.set(1, 0, 0);
    else c.fallAxis.set(-kickZ, 0, kickX).normalize();
    // ★밀려나는 방향도 따로 남긴다(17차). 여태 시체는 **그 자리에 서서** 쓰러지기만
    //   했다 — 살아 있는 놈은 0.59m 밀리는데 죽은 놈은 안 밀리니, 처치가 피격보다
    //   반응이 약한 이상한 그림이었다(신규유저: "한 방에 사라져 저항감 0").
    c.kick.set(kickX, 0, kickZ);
    if (c.kick.lengthSq() > 1e-8) c.kick.normalize(); else c.kick.set(0, 0, 0);
    // 뼈를 공유하는 두 번째 메시를 붙인다. 지오메트리·스켈레톤 공유라 새로 세우는 건
    // Mesh 껍데기 하나뿐이다(뼈 계산은 원본 것 한 번만 돈다).
    if (!c.twin) {
      c.twin = new THREE.SkinnedMesh(vis.mesh.geometry, c.matB);
      c.twin.frustumCulled = false;
      c.twin.castShadow = false; c.twin.receiveShadow = false;
    }
    c.twin.material = c.matB;
    c.twin.bind(vis.mesh.skeleton, vis.mesh.bindMatrix);
    vis.mesh.material = c.matA;
    // 믹서를 멈춘다 = 베인 순간 포즈로 굳는다.
    for (const k in vis.act) if (vis.act[k]) vis.act[k].paused = true;
    c.matA.userData.u.uFlash.value = 1;
    c.matB.userData.u.uFlash.value = 1;
    c.matA.userData.u.uDis.value = 0;
    c.matB.userData.u.uDis.value = 0;
    scene.add(c.twin);
    // ── 처치 마무리 (v84 QA S9) ──
    // 벤 자리에서 먹이 터지고, 그놈이 한 번 운다. 둘 다 **여기 한 프레임**이다.
    spawnInkBurst(hitP.x, hitP.y, hitP.z, kickX, kickZ, e.size);
    try {
      if (typeof window !== 'undefined' && window.__sfx && window.__sfx.demonDie) {
        window.__sfx.demonDie();
      }
    } catch (err) { /* 소리는 게임을 멈출 이유가 없다 */ }
  }

  function endCorpse(c) {
    c.on = false;
    if (c.twin && c.twin.parent) c.twin.parent.remove(c.twin);
    if (c.vis) {
      for (const k in c.vis.act) if (c.vis.act[k]) c.vis.act[k].paused = false;
      giveVis(c.vis);
      c.vis = null;
    }
  }

  // 시체 갱신. 매 프레임 월드 절단 평면을 두 메시의 **로컬 좌표**로 옮겨 준다
  // (몸이 쓰러지며 회전하므로 로컬 평면이 계속 바뀐다).
  function updateCorpses(dt) {
    for (let i = 0; i < MAX_CORPSES; i++) {
      const c = corpses[i];
      if (!c.on) continue;
      c.life += dt;
      if (c.life >= c.ttl) { endCorpse(c); continue; }
      const u = Math.min(1, c.life / 0.42);          // 쓰러지는 진행도
      const grp = c.vis.grp;
      // 자세: 서 있던 yaw 위에 쓰러지는 회전을 얹는다(월드 축이라 premultiply).
      _q1.setFromEuler(_e1.set(0, c.yaw, 0, 'YXZ'));
      _q2.setFromAxisAngle(c.fallAxis, u * u * 1.45);
      grp.quaternion.copy(_q2).multiply(_q1);
      // ── ★처치 팝 한 박자 (17차) ──
      // 세 가지가 같은 0.2초 안에 겹친다: **밀린다 · 부푼다 · 먹이 튄다**(먹은 spawnCorpse).
      //   밀림 : kick 방향으로 CORPSE_KB(m/s)를 k^2 로 흘린다. 총 CORPSE_KB x 0.22/3 = 0.42m.
      //          살아 있는 놈의 넉백(0.59m)보다 조금 작다 — 죽은 몸이 더 멀리 날면 가볍다.
      //          ★벽 통과는 LV.slide 를 지난다(살아 있는 놈의 넉백과 같은 규칙).
      //   부풂 : 첫 0.12초 동안 +14% 로 부풀었다 앉는다. 히트스톱(112ms)에 걸쳐 있어서
      //          **멈춘 화면에 부푼 실루엣 한 장**이 서고, 풀리면서 원래대로 돌아온다.
      const kb = Math.max(0, 1 - c.life / CORPSE_KB_T);
      if (kb > 0 && c.kick.lengthSq() > 1e-8) {
        const kk = kb * kb * CORPSE_KB * dt;
        const st = LV.slide(c.pos.x, c.pos.z, c.kick.x * kk, c.kick.z * kk, ENEMY_R * c.size);
        c.pos.x = st.x; c.pos.z = st.z;
      }
      grp.position.set(c.pos.x, c.pos.y - u * 0.12 * c.size, c.pos.z);
      const popK = Math.max(0, 1 - c.life / CORPSE_POP_T);
      const popS = 1 + CORPSE_POP * Math.sin(popK * Math.PI * 0.85);
      grp.scale.setScalar(K_H * c.size * popS);
      grp.updateMatrixWorld(true);
      const sep = Math.min(1, c.life / 0.30) * 0.22 * c.size;
      // ★알파 페이드는 **꼬리 0.20초만** 남긴다. 소멸의 주역은 아래 uDis(먹 흩어짐)다.
      //   둘을 같이 길게 걸면 흩어지는 덩이가 반투명해져서 다시 유령이 된다.
      const fade = 1 - Math.max(0, (c.life - (c.ttl - DIS_TAIL)) / DIS_TAIL);
      // 먹 흩어짐. 쓰러지고 나서(0.42초) 한 박자 두고 시작해 ttl 에 딱 맞춰 끝난다
      const dis = Math.max(0, Math.min(1, (c.life - DIS_START) / (c.ttl - DIS_START)));
      const flash = Math.max(0, 1 - c.life * 8);
      for (let s = 0; s < 2; s++) {
        const mesh = s === 0 ? c.vis.mesh : c.twin;
        const mat = s === 0 ? c.matA : c.matB;
        // 월드 평면 -> 이 메시의 로컬 평면. 스키닝이 끝난 transformed 가 사는 공간이다.
        _inv.copy(mesh.matrixWorld).invert();
        _pp.copy(c.cutP).applyMatrix4(_inv);
        _pn.copy(c.cutW).transformDirection(_inv).normalize();
        const uu = mat.userData.u;
        uu.uCutN.value.copy(_pn);
        uu.uCutD.value = _pn.dot(_pp);
        // ★uSep 은 **그 메시의 로컬 길이**다. 원본은 그룹 스케일(키 정규화)이 걸려
        //   있고 twin 은 씬 루트라 스케일이 1이다. 각자 자기 월드 스케일로 나눠야
        //   두 조각이 같은 폭으로 벌어진다(안 하면 한쪽만 31% 더 밀려난다).
        _v4.setFromMatrixScale(mesh.matrixWorld);
        uu.uSep.value = sep / (_v4.x || 1);
        uu.uFade.value = fade;
        uu.uFlash.value = flashHold >= 0 ? flashHold : flash;   // 검증용 고정
        // ★uDis 계열은 **월드 좌표** 기준이라 메시별로 나눌 필요가 없다(위 셰이더 주석).
        uu.uDis.value = dis;
        uu.uDisY0.value = c.pos.y - 0.05;
        // 다 쓰러진 몸은 눕는다. 서 있는 키(1.3m)가 아니라 누운 두께가 기준이다.
        uu.uDisH.value = DIS_H * c.size;
      }
    }
  }

  // -------------------------------------------------------------------------
  // 피격. main.js 가 실측한 칼날 선분(a=코등이, b=칼끝)을 그대로 받는다.
  // ★칼은 프레임 사이를 건너뛴다. 60fps 에서 칼끝 속도가 90 이면 한 프레임에
  //   1.5m 를 지나간다. 이전 프레임 선분과 이번 프레임 선분 사이를 잘게 쪼개
  //   전부 검사해야 빠른 스윙에서 적을 뚫고 지나가지 않는다.
  function doHits(a, b) {
    // 이번 프레임에 칼이 이동한 거리로 쪼갤 횟수를 정한다(느릴 땐 2번이면 충분)
    const travel = Math.max(a.distanceTo(_prevA), b.distanceTo(_prevB));
    const steps = Math.max(2, Math.min(6, Math.ceil(travel / 0.3) + 1));
    // 스윙 평면의 법선 = 칼날 방향 x 칼끝 진행 방향. 자를 평면이 이거다.
    _v1.copy(b).sub(a);                       // 칼날 방향
    _v2.copy(b).sub(_prevB);                  // 칼끝 진행 방향
    _cutW.copy(_v1).cross(_v2);
    if (_cutW.lengthSq() < 1e-8) _cutW.set(0, 1, 0); else _cutW.normalize();
    // 밀려나는 방향은 칼끝 진행 방향의 수평 성분
    let kx = _v2.x, kz = _v2.z;
    const kl = Math.hypot(kx, kz);
    if (kl > 1e-5) { kx /= kl; kz /= kl; } else { kx = 0; kz = 0; }

    let hits = 0;
    for (let s = 0; s < steps; s++) {
      const t = s / (steps - 1);
      _segA.copy(_prevA).lerp(a, t);
      _segB.copy(_prevB).lerp(b, t);
      // ★첫 명중에서 멈추면 안 된다. 한 번에 여러 마리가 갈라져야 한다.
      for (let i = live.length - 1; i >= 0; i--) {
        const e = live[i];
        if (e.lastSwing === swingId) continue;      // 한 스윙에 한 번만
        // ★칼날 선분 대 몸통 캡슐. 렌더가 세우는 자리(e.pos = 발밑)와 **같은 값**으로
        //   캡슐을 세운다. 여기만 다르면 "허공을 베는데 맞는다"가 된다.
        const rad = CAP_R * e.size + BLADE_PAD;
        _capA.set(e.pos.x, e.pos.y + e.h * CAP_LO, e.pos.z);
        _capB.set(e.pos.x, e.pos.y + e.h * CAP_HI, e.pos.z);
        if (segSegDist2(_segA, _segB, _capA, _capB, _hitP) > rad * rad) continue;
        e.lastSwing = swingId;
        const hpBefore = e.hp;
        e.hp -= SWORD_DMG;
        // ★e.flash 는 "방금 맞았다"의 시계로만 남는다. 몸에 얹히는 색은 0 이다
        //   (FLASH_R 선언부 - 오너가 끄라고 한 그 번쩍이다).
        e.flash = 1;
        // 머리 위 체력 바를 띄운다. 맞은 놈만 1.2초. (죽으면 아래에서 despawn 되니 안 뜬다)
        e.pipT = PIP_SHOW;
        hits++;
        const grp = e.grp;
        if (grp) aggroGroup(grp);                   // 맞으면 그 무리가 같이 온다
        const killed = e.hp <= 0;
        const hx = _hitP.x, hy = _hitP.y, hz = _hitP.z;
        // ★큰 데미지 숫자. **칼날이 실제로 닿은 그 점** 위에 띄운다(머리 위가 아니다 -
        //   벤 자리에 떠야 "이 한 대"와 숫자가 한 사건으로 읽힌다).
        spawnDmgPop(hx, hy + DMG_ANCHOR_Y, hz, SWORD_DMG * DMG_SHOW, killed);
        if (killed) {
          kills++;
          // ── ★유령 킬 추적 창구 ──
          // "처치 수가 혼자 올라간다"는 보고를 눈이 아니라 **기록**으로 가린다.
          // kills 를 올리는 자리는 이 한 줄뿐이므로, 여기 남는 기록이 곧 전수다.
          // 남기는 것: 언제 · 어느 스윙에 · 어디 있던 놈을 · 플레이어와 몇 m 에서.
          const pp = getPlayerPos();
          // 화면 안에서 죽었나(NDC). 밖에서 죽으면 사람 눈에는 '유령 증가'로 보인다.
          let ndx = 9, ndy = 9;
          if (camera) {
            _kv.set(e.pos.x, e.pos.y + e.h * 0.5, e.pos.z).project(camera);
            ndx = +_kv.x.toFixed(2); ndy = +_kv.y.toFixed(2);
          }
          killLog.push({
            t: +T.toFixed(2), swing: swingId, kills,
            ex: +e.pos.x.toFixed(2), ez: +e.pos.z.toFixed(2),
            d: +Math.hypot(e.pos.x - pp.x, e.pos.z - pp.z).toFixed(2),
            hp0: +hpBefore.toFixed(2), maxHp: e.maxHp,
            ndc: [ndx, ndy],
            onScreen: Math.abs(ndx) <= 1 && Math.abs(ndy) <= 1,
          });
          if (killLog.length > 24) killLog.shift();
          bumpStreak();
          // ★시체가 고블린 오브젝트를 넘겨받는다. despawn 이 먼저 돌면 풀로 반납돼서
          //   다음 스폰이 그 자리에서 그 몸을 다시 써 버린다(시체가 벌떡 일어난다).
          const vis = e.vis;
          e.vis = null;
          spawnCorpse(vis, e, _cutW.x, _cutW.y, _cutW.z, _hitP, kx, kz);
          despawn(i);
        } else {
          // 안 죽었으면 살짝 뒤로 밀린다. 이게 없으면 때린 느낌이 안 난다.
          // ── ★밀림 실측 (17차) ──
          // 옛 값 4.2 · 0.13초. 감쇠가 pow(0.02, dt) 라 시간상수가 0.256초이므로
          //   실제 이동거리 = 4.2 x (1 - e^(-3.912 x 0.13)) / 3.912 = **0.43m**.
          //   24m 카메라에서 27px. 있긴 있는데 0.13초 안에 끝나고 그 0.13초가
          //   히트스톱과 겹쳐서 "밀렸다"가 화면에 남는 구간이 사실상 없었다.
          // 새 값 5.2 · 0.15초 -> 5.2 x (1 - e^(-0.5868)) / 3.912 = **0.59m (37px)**.
          //   히트스톱이 풀린 뒤에도 반 이상 남아 있어서 밀리는 장면이 실제로 보인다.
          //   그 이상(0.7m+)은 작은 고블린이 날아가는 그림이 돼서 무게가 사라진다.
          e.kb.set(kx, 0, kz).multiplyScalar(5.2);
          e.kbT = 0.15;
          // 경직 반동. 100ms 동안 납작해졌다가 돌아온다(y 0.85 / x 1.12).
          // ★클립이 아니라 **루트 오브젝트 스케일**로 한다. glb 안의 스케일을 안
          //   건드리므로 "glb 스케일 오염" 함정과 무관하고, 클립 없는 개체에도 먹는다.
          e.sqT = SQUASH_T;
          // ── ★경직 (9차) ──
          // 발이 멎고 클립이 얼어붙는다. **휘두르던 칼은 통째로 취소된다.**
          //   · 예비 자세(wndT)도 취소한다 = 예고를 보고 먼저 때리면 공격이 끊긴다.
          //     이 한 줄이 "포위가 억울하지 않다"의 실체다(선타의 값어치).
          //   · atkT 를 끊으면 이미 걸린 Attack 클립은 아래 클립 고르기가
          //     Idle/Walk 로 갈아치운다(경직 중엔 재생속도를 STUN_TS 로 눌러 둔다).
          e.stunT = HIT_STUN;
          e.wndT = 0;
          e.atkT = 0; e.hitT = -1;
        }
        // 무리 전멸 판정. 마지막 한 마리를 벤 그 프레임에만 true 다.
        let wiped = false;
        if (killed && grp) {
          wiped = true;
          for (const s of grp.spots) if (s.enemy) { wiped = false; break; }
        }
        onHit({ kill: killed, wiped, swing: swingId,
                x: hx, y: hy, z: hz,
                nx: _cutW.x, ny: _cutW.y, nz: _cutW.z, kx, kz });
      }
    }
    if (hits) {
      const last = hitLog[hitLog.length - 1];
      if (last && last.swing === swingId) last.hits += hits;
      else {
        hitLog.push({ swing: swingId, hits });
        if (hitLog.length > 8) hitLog.shift();
      }
    }
    return hits;
  }

  // -------------------------------------------------------------------------
  // ── 가장 가까운 적 ──
  // ★공격 방향 스냅의 근거다. 살아 있는 잡몹 + 보스를 같이 본다. 보스를 빼면
  //   보스 앞에서만 스냅이 안 걸려서 "이 게임은 가끔 안 돈다"가 된다.
  //   보스는 boss.js 가 window.__boss 로 자기 위치(pos)와 상태(state)를 내놓는다.
  //   그 창구가 없는 빌드에서는 조용히 잡몹만 본다(던지지 않는다).
  function nearestTo(x, z, r) {
    const rr = r === undefined ? SNAP_R : r;
    let bd2 = rr > 0 ? rr * rr : Infinity;
    let bx = 0, bz = 0, boss = false, found = false;
    for (let i = 0; i < live.length; i++) {
      const e = live[i];
      const dx = e.pos.x - x, dz = e.pos.z - z;
      const d2 = dx * dx + dz * dz;
      if (d2 < bd2) { bd2 = d2; bx = e.pos.x; bz = e.pos.z; boss = false; found = true; }
    }
    const B = (typeof window !== 'undefined') ? window.__boss : null;
    if (B && B.pos && B.state !== '사망') {
      const dx = B.pos.x - x, dz = B.pos.z - z;
      const d2 = dx * dx + dz * dz;
      if (d2 < bd2) { bd2 = d2; bx = B.pos.x; bz = B.pos.z; boss = true; found = true; }
    }
    if (!found) return null;
    // yaw 규약은 이 파일의 요괴와 같다: 바라보는 방향 = (sin yaw, 0, cos yaw).
    return { x: bx, z: bz, boss, d: +Math.sqrt(bd2).toFixed(3),
             yaw: Math.atan2(bx - x, bz - z) };
  }

  // 공격 입력 순간 캐릭터를 가장 가까운 적 쪽으로 돌린다. obj 는 main.js 의 root.
  // ★회전 보간을 여기서 도는 이유: main.js 루프를 건드리지 않고도 급회전을 주려면
  //   매 프레임 도는 자리가 필요한데, 이 시스템의 update() 가 이미 매 프레임 돈다.
  function snapFacing(obj, r, dur) {
    if (!snapOn || !obj) return null;
    const t = nearestTo(obj.position.x, obj.position.z, r);
    if (!t) return null;
    let d = t.yaw - obj.rotation.y;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    // 이미 그쪽을 보고 있으면(3도 이내) 아무것도 안 한다. 미세하게 떨면 더 이상하다.
    if (Math.abs(d) < 0.05) { snap = null; return t; }
    const D = dur === undefined ? SNAP_DUR : dur;
    if (D <= 0) { obj.rotation.y = t.yaw; snap = null; return t; }
    snap = { obj, from: obj.rotation.y, delta: d, t: 0, dur: D };
    return t;
  }

  function stepSnap(dt) {
    if (!snap) return;
    snap.t += dt;
    const k = Math.min(1, snap.t / snap.dur);
    // ease-out. 시작이 제일 빠르고 끝에서 멎는다 = 몸을 홱 틀어 겨눈 그림.
    const e = 1 - (1 - k) * (1 - k);
    snap.obj.rotation.y = snap.from + snap.delta * e;
    if (k >= 1) snap = null;
  }

  // -------------------------------------------------------------------------
  // ── 플레이어 피격 ──
  // ★여기 규칙이 "맞는 맛"의 전부다. v72 QA: "HP 가 0.8초마다 정확히 -8. 네 마리가
  //   붙어도 똑같다. 메트로놈 도트처럼 읽힌다." 원인은 무적 0.65초였다. 넷이 때려도
  //   첫 대만 들어가고 나머지 셋은 통째로 사라져서, **마릿수가 화면에서 지워졌다.**
  //
  // 그래서 무적을 짧게(0.30초) 줄여 네 번을 다 보여주되, **총량은 새는 통(leaky
  // bucket)으로 묶는다.**
  //   · 맞은 만큼 통에 담기고, 통은 초당 DMG_LEAK 만큼 샌다.
  //   · 새 타격은 "통에 남은 만큼"을 먼저 흡수당한다(amount - bucket).
  //   → 혼자 때리면(1.2초 간격) 통이 다 새서 예전과 똑같이 8이 온전히 들어간다.
  //   → 넷이 겹치면 8 · 2 · 2 · 2 처럼 들어가 **초당 총량은 DMG_LEAK 을 못 넘는다.**
  //   → 보스의 큰 한 방(14/20/28)은 통이 비어 있으면 온전히 다 들어간다.
  // DMG_LEAK 10 = 8 / 0.8초. v72 QA 가 실측한 "0.8초마다 -8" 을 그대로 상한으로 삼았다.
  // ★실측(브라우저, headed):
  //     고침 전 · 4마리 : 정확히 1.20초마다 -8 = 6.7 DPS (넷이 한 박자로 묶여 있었다)
  //     고침 전 · 8마리 : 100 -> 0 이 9.7초 = 10.3 DPS
  //     고침 후 · 4마리 : 0.32~0.85초 간격으로 -3.2~-8, 100 -> 0 이 10.5초 = 9.5 DPS
  //   즉 **최악 DPS 는 그대로 두고, 운 좋게 박자가 겹쳐 있던 경우만 상한까지 올라왔다.**
  //   마릿수와 무관하게 이 값이 천장이라는 게 예전에 없던 보장이다.
  //   너무 아프면(또는 물러 터지면) 손댈 곳은 여기 한 줄이다.
  const DMG_LEAK = ENEMY_DMG / 0.8;
  let dmgBucket = 0;
  let lastHurtT = -99;
  // ── 대시 무적 창구 (2026-08-10 9차) ──
  // ★잡몹 타격은 **이 파일 안에서** damagePlayer 를 직접 부른다(아래 update 의 hitT 갈래).
  //   main.js 가 넘긴 콜백을 안 지나므로 바깥에서 막을 방법이 없었다. 보스 피해는
  //   main.js 콜백을 지나 이미 막히고 있었고(대시 중 보스 피해 0), 잡몹만 뚫려 있었다.
  //   그 구멍이 여기다. main.js 는 대시 시작 프레임에 setIframe(0.20) 을 이미 부르고 있다.
  // ★무적은 피격 무적(iframe)과 **같은 통**을 쓴다. 통을 둘로 나누면 "잡몹은 안 아픈데
  //   보스는 아픈" 상태가 생기고, 체력·무적이 이 파일 한 군데라는 원칙이 깨진다.
  //   같은 통을 쓰므로 **짧은 값으로 깎지 않는다**(Math.max). 피격 무적 0.30 중에
  //   대시(0.20)를 넣었다고 보호가 0.10 줄어들면 안 된다.
  // ★대시분만 따로도 센다. 검증에서 "이건 대시로 흘린 타격"을 구분해야 하기 때문이다.
  //   연출은 일부러 아무것도 안 붙인다 — 피해도 넉백도 화면 붉음도 없는 것이
  //   "완전히 흘렸다"의 가장 정직한 그림이다(요괴 헛스윙 모션은 그대로 보인다).
  // ★실측(headed. 고블린 한 마리의 스윙에 대시를 물려 6회씩.
  //   원자료 renders/history/v94_wave9/soban_enemy/iframe.json):
  //     대시 없음         5/5 피격(매번 6)
  //     창구 무력화(= 전)  5/6 피격(합계 30) · dodged 0
  //     창구 살림(= 지금)  0/6 피격(합계  0) · dodged 6
  //   dodged 6 이 핵심이다. "요괴가 안 때렸다"가 아니라 **때린 걸 여기서 흘렸다**는 뜻이다.
  //   ★잡몹은 휘두르기 시작하면 사거리를 다시 안 본다(아래 update 주석). 그래서
  //     대시로 3.5m 를 빠져도 그 스윙은 그대로 들어간다 = 자리 이동으로는 못 피한다.
  let iframeDash = 0;              // 대시 무적 남은 시간(iframe 의 부분집합)
  let dodgeN = 0;                  // 대시 무적으로 흘려보낸 타격 수(검증 창구)
  function setIframe(sec) {
    const s = +sec;
    if (s > 0) {
      if (s > iframe) iframe = s;
      if (s > iframeDash) iframeDash = s;
    }
    return +Math.max(0, iframe).toFixed(3);
  }
  function damagePlayer(amount, srcX, srcZ) {
    if (dead) return 0;
    // 무적이면 피해도 넉백도 연출도 없다. 대시로 흘린 것만 따로 세어 둔다.
    if (iframe > 0) { if (iframeDash > 0) dodgeN++; return 0; }
    // ★음수·NaN 클램프. 예전엔 damagePlayer(-200) 한 줄로 체력이 300까지 올랐다.
    let amt = +amount;
    if (!(amt > 0)) return 0;
    // 통이 흡수하는 건 **잡몹의 겹치기**뿐이다. 잡몹 한 대보다 큰 타격(보스의
    // 14/20/28)은 예고를 보고도 맞은 대가라 깎지 않는다. 대신 통에는 그대로 담겨서
    // 그 뒤 몇 초 동안 잡몹 쪽을 눌러 준다(큰 걸 맞으면 숨 돌릴 틈이 생긴다).
    if (amt <= ENEMY_DMG) amt = Math.max(0, amt - dmgBucket);
    // 거의 다 흡수된 타격은 연출까지 내면 화면만 시끄럽다. 아예 없던 일로 한다.
    if (amt < 1) return 0;
    dmgBucket += amt;
    hp -= amt;
    iframe = PLAYER_IFRAME;
    lastHurtT = T;
    hurtFlash = 1;
    // ── 넉백 ──
    // 때린 놈 반대쪽으로 0.15m. 없으면 네 마리에 둘러싸여도 발이 땅에 붙어 있어서
    // "맞았다"가 몸으로 안 읽힌다. 벽을 뚫으면 안 되므로 반드시 slide 를 지난다.
    const p = getPlayerPos();
    let kx = 0, kz = 0;
    if (srcX !== undefined) { kx = p.x - srcX; kz = p.z - srcZ; }
    else {
      // 출처를 안 넘긴 호출(보스)은 제일 가까운 적을 때린 놈으로 본다.
      const t = nearestTo(p.x, p.z, 0);
      if (t) { kx = p.x - t.x; kz = p.z - t.z; }
    }
    const kd = Math.hypot(kx, kz);
    if (kd > 1e-4) {
      const st = LV.slide(p.x, p.z, (kx / kd) * PLAYER_KB, (kz / kd) * PLAYER_KB,
                          LV.PLAYER_RADIUS);
      p.x = st.x; p.z = st.z;
    }
    onPlayerHurt(amt);
    if (hp <= 0) {
      hp = 0;
      dead = true;
      deadUntil = T + RESPAWN_DELAY;
      deadEl.style.opacity = '1';
      // ★사망 **순간**을 벽시계로 못박는다. ui.js 는 20Hz 폴링이라 1.6초짜리
      //   dead 창을 놓칠 수 있다(창이 뒤로 가면 setInterval 이 1초로 늘어난다).
      //   레벨(지금 죽어 있나)이 아니라 엣지(언제 죽었나)를 내주면 안 놓친다.
      if (typeof window !== 'undefined') window.__playerDied = performance.now();
      // ── 사망 연출 (v84 QA S2) ──
      // 같은 프레임에 셋이 동시에 걸려야 "죽었다"가 한 덩어리로 읽힌다.
      //   시간(feel) : 0.30배 슬로모 1초 + 큰 흔들림
      //   소리(sfx)  : 제일 낮고 제일 긴 저음 + 세상이 먹먹해지는 덕킹
      //   화면(ui)   : 먹판 + 대형 「落」  <- ui.js 가 __playerDied 를 보고 자기가 띄운다
      // ★main.js 를 안 거치고 window 창구로 부른다. 이 파일은 onHit·onPlayerHurt 말고는
      //   바깥으로 나가는 통로가 없고, main.js 는 지금 못 건드린다.
      //   창구가 없는 빌드에서는 조용히 건너뛴다(게임은 그대로 돈다).
      try {
        if (typeof window !== 'undefined') {
          if (window.__feel && window.__feel.death) window.__feel.death();
          if (window.__sfx && window.__sfx.death) window.__sfx.death();
        }
      } catch (e) { /* 연출은 게임을 멈출 이유가 없다 */ }
    }
    return amt;
  }

  function respawnPlayer() {
    resetField();
    hp = PLAYER_MAX_HP;
    dead = false;
    iframe = 1.2;                  // 되살아난 직후 보호. 위 PLAYER_IFRAME 과 별개다
    iframeDash = 0;                // ★리스폰 무적을 대시 회피로 세지 않게 지운다
    dmgBucket = 0;
    snap = null;
    deadEl.style.opacity = '0';
    if (typeof window !== 'undefined') window.__playerRespawned = performance.now();
    onRespawn();
  }

  // -------------------------------------------------------------------------
  // -------------------------------------------------------------------------
  // 경로 재계산 (개체 하나)
  // ★여기가 길찾기의 전부다. 순서가 곧 우선순위다.
  //   1) 옆걸음 중이면 아무것도 안 바꾼다(흔들다 말면 도로 낀다)
  //   2) 시야가 트였으면 직진 (트인 마당이 대부분이라 이 경우가 제일 흔하다)
  //   3) 막혔으면 흐름장에서 "내가 볼 수 있는 가장 먼 칸"을 받아 그리로 간다
  //   4) 흐름장이 못 닿는 자리(격자 밖·벽 속)면 어쩔 수 없이 직진 = 예전 동작
  function repath(e, player) {
    if (e.sideT > 0) return;
    if (!usePath) { e.direct = true; return; }             // 검증용 스위치(끄면 옛 직진)
    if (NAV.los(e.pos.x, e.pos.z, player.x, player.z)) { e.direct = true; return; }
    const t = NAV.target(e.pos.x, e.pos.z, 6);
    if (t.ok) { e.direct = false; e.tx = t.x; e.tz = t.z; }
    else e.direct = true;
  }

  const shAttr = shadowMesh.geometry.attributes.aSA;
  const LEASH2 = LEASH_DIST * LEASH_DIST;
  const AGGRO2 = AGGRO_RADIUS * AGGRO_RADIUS;

  function update(dt, ctx) {
    const player = getPlayerPos();
    const a = ctx.a, b = ctx.b;

    // 정지(클립 미리보기·__freeze) 중에도 칼 위치는 따라간다. 안 그러면 재개하는
    // 순간 이전 프레임 선분이 몇 미터 떨어져 있어 허공을 훑으며 다 죽인다.
    if (ctx.paused) {
      if (a && b) { _prevA.copy(a); _prevB.copy(b); hasPrevBlade = true; }
      return;
    }

    T += dt;
    // 공격 방향 스냅 보간. 판정보다 **먼저** 돌아야 이번 프레임의 칼이 돌아간
    // 몸을 따라간다(나중에 돌리면 한 프레임 늦게 겨눈다).
    stepSnap(dt);

    // ── 피격 판정 ──
    // 히스테리시스로 '베는 중'을 판정한다. 켜지는 순간이 새 스윙이다.
    const fast = ctx.fast || 0;
    const wantHot = !!ctx.attacking && (hotState ? fast > HOT_OFF : fast > HOT_ON);
    // 캐스트가 바뀌면 "이 캐스트가 쓴 번호"를 비운다. main.js 가 공격 클립을 새로
    // 시작할 때만 ctx.cast 가 올라가므로, 캔슬로 이어 낸 다음 타도 새 캐스트로 잡힌다.
    if (ctx.cast !== castId) { castId = ctx.cast; castSwing = -1; }
    // ★스윙마다 번호가 바뀌어야 중복 타격이 막힌다. 단 SWING_GAP 안쪽에서
    //   다시 켜진 건 같은 스윙의 떨림으로 보고 번호를 안 올린다(= 재타격 없음).
    if (wantHot && !hotState && T - lastSwingT > SWING_GAP) {
      // ★한 방짜리 기술(ctx.single = 수면참·횡일섬)은 캐스트당 번호 하나다.
      //   이미 이 캐스트에서 하나 썼으면 새로 안 준다 = 같은 요괴는 두 번 안 맞는다
      //   (doHits 의 e.lastSwing 검사가 번호가 같은 동안 재타격을 막는다).
      //   3연타(Attack)는 클립 하나에 진짜 스윙이 셋이라 여기 안 걸린다.
      if (!(ctx.single && castSwing >= 0)) {
        swingId++;
        lastSwingT = T;
        if (ctx.single) castSwing = swingId;
      }
    }
    hotState = wantHot;
    if (a && b) {
      if (hotState && hasPrevBlade) doHits(a, b);
      _prevA.copy(a); _prevB.copy(b);
      hasPrevBlade = true;
    } else {
      hasPrevBlade = false;
    }
    if (dbgLine) {
      const pa = dbgLine.geometry.attributes.position;
      if (a && b) {
        pa.setXYZ(0, a.x, a.y, a.z); pa.setXYZ(1, b.x, b.y, b.z);
        pa.needsUpdate = true;
      }
      dbgLine.material.color.setHex(hotState ? 0xff3040 : 0x3060ff);
    }

    // ── 무리 단위 판단 (무리 수가 한 자리라 매 프레임 다 돌아도 공짜다) ──
    for (let gi = 0; gi < groups.length; gi++) {
      const g = groups[gi];
      let aliveN = 0, homeN = 0;
      for (const s of g.spots) {
        if (!s.enemy) continue;
        aliveN++;
        if (s.enemy.mode !== 2) homeN++;
      }
      // 전멸하면 타이머를 걸고, 시간이 되면 원래 자리에 다시 생긴다.
      if (aliveN === 0) {
        if (g.tmp) continue;                          // 성능 실측용 임시 무리는 안 되살린다
        if (g.respawnAt < 0) g.respawnAt = T + GROUP_RESPAWN;
        else if (T >= g.respawnAt) {
          for (const s of g.spots) spawnAt(s, g);
          g.respawnAt = -1; g.aggro = false; g.returning = false; g.searching = false;
        }
        continue;
      }
      g.respawnAt = -1;
      if (g.returning && homeN === aliveN) g.returning = false;   // 전원 복귀 완료
      if (dead) { if (g.aggro || g.searching) leashGroup(g); continue; }
      // ★갈래 순서가 뜻을 갖는다. 수색(searching) 중인 무리를 "안 쫓는 무리"로 묶어
      //   아래 어그로 검사에 넣으면, 같은 수풀 안에 서 있다는 이유로 그 프레임에
      //   바로 다시 붙는다(= 수색이 없던 일이 된다).
      if (g.aggro) {
        // ── 시야를 잃으면 포기한다 (수풀로 도망가는 길) ──
        // 한 마리라도 보고 있으면 무리 전체가 계속 안다. 아무도 못 보면 LOSE_SIGHT
        // 동안 마지막 자리로 밀고 들어가 보다가 수색으로 넘어간다.
        // ★alerted=true 로 묻는다. 이미 쫓는 놈에게는 "같은 수풀이면 보인다"를
        //   안 준다(stealth.js canSee 주석 참고). 이게 v72 QA #2 의 수정 지점이다.
        let sees = false;
        for (const s of g.spots) {
          if (s.enemy && ST.canSee(s.enemy.pos.x, s.enemy.pos.z, true)) { sees = true; break; }
        }
        if (sees) {
          g.lostT = 0;
          g.seenX = player.x; g.seenZ = player.z;   // 마지막으로 본 자리
        } else {
          g.lostT += dt;
          if (g.lostT >= LOSE_SIGHT) { searchGroup(g); continue; }
        }
        // 자기 자리에서 멀어지면 무리 전체가 포기한다
        for (const s of g.spots) {
          const e = s.enemy;
          if (!e || !e.home) continue;
          const dx = e.pos.x - e.home.x, dz = e.pos.z - e.home.z;
          if (dx * dx + dz * dz > LEASH2) { leashGroup(g); break; }
        }
      } else if (g.searching) {
        // ── 수색: 마지막 목격 지점에서 두리번거린다 ──
        // 다시 보이면(수풀에서 나왔거나, 달렸거나, 베었거나) 그 자리에서 재추격.
        for (const s of g.spots) {
          const e = s.enemy;
          if (!e) continue;
          const dx = e.pos.x - player.x, dz = e.pos.z - player.z;
          if (dx * dx + dz * dz < AGGRO2 && ST.canSee(e.pos.x, e.pos.z, true)) {
            g.searching = false; aggroGroup(g); break;
          }
        }
        if (g.searching) {
          let still = false;
          for (const s of g.spots) if (s.enemy && s.enemy.mode === 3) { still = true; break; }
          // 전원이 두리번거리기를 마쳤다. 이제 자기 자리로 돌아간다.
          // ★포기한 시각을 찍는다. 머리 위 「?」가 0.9초에 걸쳐 스러진다 = "놓쳤다".
          if (!still) { g.searching = false; g.returning = true; g.giveUpAt = T; }
        }
      } else if (!g.returning) {
        // ★어그로는 무리 단위다. 한 마리라도 범위에 들면 그 무리가 통째로 온다.
        //   옆 무리는 자기 범위 안에 안 들어왔으니 안 온다.
        // ★수풀 은신: 범위 안이어도 **볼 수 없으면** 어그로가 안 걸린다.
        //   ST.canSee 가 "수풀 밖인가 / 같은 수풀인가 / 공격했나 / 소리가 들리나"를
        //   전부 판정한다. 걸어 들어가면 조용하고, 달리면 소리가 새서 걸린다.
        for (const s of g.spots) {
          const e = s.enemy;
          if (!e) continue;
          const dx = e.pos.x - player.x, dz = e.pos.z - player.z;
          if (dx * dx + dz * dz < AGGRO2 && ST.canSee(e.pos.x, e.pos.z)) { aggroGroup(g); break; }
        }
      }
    }

    // ── 흐름장 갱신 ──
    // ★매 프레임이 아니라 **플레이어가 격자 칸(1.6m)을 넘을 때만** 다시 깐다.
    //   달리기 3.2m/s 기준 초당 두 번이다. 그 사이에는 40마리가 같은 배열을 읽는다.
    //   쫓는 놈이 하나도 없으면 아예 안 깐다(제자리 무리만 있는 평상시가 그렇다).
    let chasing = false;
    for (let gi = 0; gi < groups.length; gi++) if (groups[gi].aggro) { chasing = true; break; }
    if (chasing && NAV.needRebuild(player.x, player.z)) NAV.rebuild(player.x, player.z);

    // ── 개체 행동 ──
    const n = live.length;
    for (let i = 0; i < n; i++) {
      const e = live[i];
      e.flash -= dt * FLASH_DECAY; if (e.flash < 0) e.flash = 0;
      if (flashHold >= 0) e.flash = flashHold;      // 검증용 고정(평소엔 -1 이라 안 탄다)
      if (e.pipT > 0) e.pipT -= dt;
      if (e.stunT > 0) e.stunT -= dt;
      e.atkCd -= dt;
      // ★옆걸음 타이머는 여기서 **한 군데서만** 줄인다. 추격·귀환 갈래 안에서 줄이면
      //   대기 모드로 돌아간 개체의 타이머가 영원히 안 줄어서, 다시 어그로가 걸릴 때
      //   첫 프레임부터 엉뚱한 방향으로 걷는다.
      if (e.sideT > 0) e.sideT -= dt;
      // ★이동은 여기서 바로 좌표에 더하지 않는다. 한 프레임 이동량을 mvx/mvz 에
      //   모았다가 아래에서 **한 번에** 벽 충돌을 태운다(넉백 포함). 갈래마다 따로
      //   더하면 넉백으로만 벽을 뚫는 구멍이 남는다.
      let mvx = 0, mvz = 0;
      let want = 0;              // 이번 프레임에 내려는 이동 속도(애니 재생속도의 근거)
      if (e.kbT > 0) {
        e.kbT -= dt;
        mvx += e.kb.x * dt;
        mvz += e.kb.z * dt;
        e.kb.multiplyScalar(Math.pow(0.02, dt));
      }
      // ── 공격 클립 진행 ──
      // ★타격은 클립 중간(ATK_HIT_T)에 들어간다. 예전엔 사거리에 들어오는 즉시
      //   피가 깎여서 "맞은 다음에 휘두르는" 그림이었다. 이제 들었다가 내리치고,
      //   내리치는 프레임에 맞는다. 사거리 재검사는 **안 한다** - 한 번 휘두르기로
      //   한 놈은 끝까지 휘두른다(뒤로 빼면 안 맞는 판정은 다음 단계 과제다).
      if (e.atkT > 0) {
        e.atkT -= dt;
        if (e.hitT >= 0) {
          e.hitT -= dt;
          if (e.hitT <= 0) {
            e.hitT = -1;
            // 때린 놈의 자리를 같이 넘긴다(넉백 방향). 안 넘기면 제일 가까운 놈
            // 기준으로 밀리는데, 넷이 겹쳐 있으면 엉뚱한 쪽으로 밀린다.
            if (!dead) damagePlayer(ENEMY_DMG, e.pos.x, e.pos.z);
          }
        }
      }
      // ── ★예비 자세 진행 ──
      // 이 구간이 끝나는 프레임에 비로소 Attack 클립이 걸린다. 여기서 맞으면
      // (위 doHits 가 wndT 를 0 으로 끊으므로) 공격은 없던 일이 된다.
      if (e.wndT > 0) {
        e.wndT -= dt;
        if (e.wndT <= 0) {
          e.wndT = 0;
          e.atkT = (ATK_TO - ATK_FROM) / ATK_TS;
          e.hitT = ATK_HIT_T;
          if (e.vis && e.vis.act.Attack) {
            const av = e.vis.act.Attack;
            av.reset();
            av.time = ATK_FROM;
            av.setEffectiveTimeScale(ATK_TS);
            av.play();
            if (e.vis.cur && e.vis.cur !== av) e.vis.cur.crossFadeTo(av, 0.08, false);
            e.vis.cur = av;
          }
        }
      }

      if (e.stunT > 0) {
        // ── ★경직 ──
        // 어느 모드든 발이 멎는다. 넉백(위 kb 블록)만 통과시켜서 **맞고 밀린다**가
        // 그림으로 남는다. 수색 타이머·귀환 회복도 같이 멈춘다("맞으면 시간이 선다").
        want = 0;
      } else if (e.mode === 1) {
        // ── 추격 ──
        // ★두 갈래다. 시야가 트였으면 플레이어에게 직진하고, 막혔으면 흐름장이
        //   내준 경유점으로 간다. **공격 판단은 언제나 플레이어와의 실제 거리**로
        //   한다(경유점 거리로 하면 벽 뒤에서 허공에 칼질을 한다).
        const d = Math.hypot(player.x - e.pos.x, player.z - e.pos.z) || 1e-4;
        e.pathT -= dt;
        if (e.pathT <= 0) { e.pathT = REPATH; repath(e, player); }
        let tgx, tgz;
        if (e.direct) { tgx = player.x; tgz = player.z; }
        else {
          // 경유점에 닿았으면 기다리지 말고 그 자리에서 다음 걸 뽑는다
          if (Math.hypot(e.tx - e.pos.x, e.tz - e.pos.z) < WAYPOINT_HIT) {
            e.pathT = REPATH; repath(e, player);
          }
          tgx = e.direct ? player.x : e.tx;
          tgz = e.direct ? player.z : e.tz;
        }
        let dx = tgx - e.pos.x, dz = tgz - e.pos.z;
        const dLen = Math.sqrt(dx * dx + dz * dz) || 1;
        dx /= dLen; dz /= dLen;
        // 막힌 채로 옆걸음 중이면 가려던 방향을 90도 튼다(문틀에 어깨가 걸릴 때)
        if (e.sideT > 0) {
          const sx = -dz * e.sideS, sz = dx * e.sideS;
          dx = dx * 0.35 + sx * 0.94;
          dz = dz * 0.35 + sz * 0.94;
          const dl = Math.hypot(dx, dz) || 1; dx /= dl; dz /= dl;
        }
        const stop = ENEMY_ATK_RANGE + e.size * ENEMY_ATK_SIZE;
        // ★사거리 안이면 경유점이 아니라 **플레이어**를 본다. 경유점을 보게 두면
        //   코앞에서 옆을 보고 칼질하는 그림이 나온다.
        if (d <= stop + 0.35) e.yaw = Math.atan2((player.x - e.pos.x) / d, (player.z - e.pos.z) / d);
        else e.yaw = Math.atan2(dx, dz);
        // 휘두르는 중(예비 자세 포함)에는 발이 안 나간다. 경직 중에도 안 나간다.
        // ★예비 자세를 **정지**로 두는 게 이 예고의 핵심이다. 달려오면서 드는 그림은
        //   34m 에서 안 읽힌다. 한 박자 멈춰 서야 "온다"가 보인다.
        const busy = e.atkT > 0 || e.wndT > 0 || e.stunT > 0;
        if (d > stop && !busy) {
          if (e.kbT <= 0) {
            want = e.speed;
            mvx += dx * e.speed * dt;
            mvz += dz * e.speed * dt;
          }
        } else if (!dead && e.atkCd <= 0 && !busy && d <= stop + 0.35) {
          // 쿨을 매번 ±18% 흔든다. 어쩌다 박자가 맞아도 저절로 다시 흩어진다.
          e.atkCd = ENEMY_ATK_CD * (1 + (hash1(e.spot ? e.spot.seed + (T * 3 | 0) : T * 3 | 0) - 0.5) * 2 * ATK_CD_JITTER);
          // ★여기서는 **예비 자세만** 건다. 클립·판정은 wndT 가 0 이 되는 프레임에
          //   위쪽 진행 블록이 건다(그 사이에 맞으면 통째로 취소된다).
          e.wndT = ATK_WIND;
        }
      } else if (e.mode === 3) {
        // ── 수색: 마지막 목격 지점까지 가 보고 두리번거린다 ──
        // ★여기서는 플레이어 좌표를 안 쓴다. 놓친 놈은 **놓친 자리**만 안다.
        //   (플레이어를 보게 두면 수풀 안을 정확히 노려보는 그림이 나온다)
        e.searchT -= dt;
        let dx = e.searchX - e.pos.x, dz = e.searchZ - e.pos.z;
        const d = Math.sqrt(dx * dx + dz * dz);
        if (d > SEARCH_ARRIVE) {
          dx /= d; dz /= d;
          e.yaw = Math.atan2(dx, dz);
          // ★상수(0.92)를 쓴다. 옛 코드는 e.speed 의 0.45 배였는데, 이번에 추격
          //   속도를 2.30~2.78 로 올리자 그 식이 1.04~1.25 가 되어 클립 갈래(1.05)를
          //   넘어 **Run 으로 뛰어오게** 됐다(= 놓친 놈이 쫓는 놈으로 보인다).
          //   비율식은 속도 튜닝을 할 때마다 이 함정을 다시 밟는다. 절대값으로 못박는다.
          want = SEARCH_SPD;                      // 뛰지 않는다. 살피며 다가간다
          mvx += dx * want * dt;
          mvz += dz * want * dt;
        } else {
          // 느린 yaw 왕복. 개체마다 phase 가 달라서 넷이 따로 논다.
          e.yaw = e.searchYaw + Math.sin(e.searchT * SEARCH_RATE + e.phase) * SEARCH_SWEEP;
        }
        if (e.searchT <= 0) { e.mode = 2; e.sideT = 0; }
      } else if (e.mode === 2) {
        // ── 귀환: 자리로 돌아가며 회복. 돌아가는 중엔 플레이어를 안 본다 ──
        // ★흐름장은 플레이어 기준이라 여기선 못 쓴다. 대신 막히면 옆걸음으로 흔든다.
        //   집은 자기가 걸어 나온 자리라 옆으로 한 번만 돌면 대개 풀린다.
        let dx = e.home.x - e.pos.x, dz = e.home.z - e.pos.z;
        const d = Math.sqrt(dx * dx + dz * dz);
        e.hp = Math.min(e.maxHp, e.hp + RETURN_HEAL * dt);
        if (d < 0.25) { e.mode = 0; e.hp = e.maxHp; e.sideT = 0; }
        else {
          dx /= d; dz /= d;
          if (e.sideT > 0) {
            const sx = -dz * e.sideS, sz = dx * e.sideS;
            dx = dx * 0.35 + sx * 0.94;
            dz = dz * 0.35 + sz * 0.94;
            const dl = Math.hypot(dx, dz) || 1; dx /= dl; dz /= dl;
          }
          e.yaw = Math.atan2(dx, dz);
          // ★1.35 배였다. 추격 속도를 2.30~2.78 로 올리면서 3.1~3.75 = 플레이어
          //   달리기보다 빠른 귀환이 돼 버렸다(돌아가는 놈이 제일 빠른 그림).
          //   1.12 면 2.6~3.1 로 추격보다 한 뼘만 빠르다.
          want = e.speed * 1.12;                  // 돌아갈 땐 조금 빠르게
          mvx += dx * want * dt;
          mvz += dz * want * dt;
        }
      } else {
        // ── 대기: 제자리에서 아주 좁게 서성인다 ──
        const ox = Math.sin(T * 0.5 + e.phase) * 0.45;
        const oz = Math.cos(T * 0.37 + e.phase * 1.7) * 0.45;
        const tx = e.home.x + ox - e.pos.x, tz = e.home.z + oz - e.pos.z;
        const d = Math.sqrt(tx * tx + tz * tz);
        if (d > 0.05) {
          // ★배회는 Walk 클립으로. 걸어다니는 방향을 실제로 보고 서야 발이 안 미끄러진다.
          want = 0.45;
          mvx += (tx / d) * want * dt;
          mvz += (tz / d) * want * dt;
          e.yaw = Math.atan2(tx / d, tz / d);
        } else {
          e.yaw += dt * 0.4 * (e.phase > 3.14 ? 1 : -1);
        }
      }
      e.want = want;

      // ── 벽 충돌 ──
      // 플레이어와 **같은 함수**를 쓴다. 따로 만들면 둘이 서로 다른 벽을 보게 된다.
      // 벽을 만나면 미끄러진다(모서리를 타고 도는 건 여기서 저절로 된다).
      if (mvx || mvz) {
        const ox = e.pos.x, oz = e.pos.z;
        const s = LV.slide(e.pos.x, e.pos.z, mvx, mvz, ENEMY_R * e.size, _mv);
        e.pos.x = s.x;
        e.pos.z = s.z;
        // ── 막힘 감지 ──
        // ★slide 의 hit 플래그로는 못 잡는다. 벽을 타고 **잘 미끄러지는 중에도** hit 가
        //   뜨기 때문이다. "가려던 거리 대비 실제로 간 거리"를 0.5초 창으로 본다.
        //   절반도 못 갔으면 진짜로 낀 것이다.
        e.wantD += Math.hypot(mvx, mvz);
        e.gotD += Math.hypot(e.pos.x - ox, e.pos.z - oz);
      }
      e.chkT += dt;
      if (e.chkT >= STUCK_WIN) {
        if (e.wantD > 0.05 && e.gotD < e.wantD * STUCK_RATIO && e.sideT <= 0) {
          e.sideT = SIDESTEP_T;
          // 이번에 못 빠져나오면 다음엔 반대쪽으로 돈다. 한쪽으로만 고집하면
          // 막다른 구석에서 영원히 같은 벽을 문지른다.
          e.sideS = -e.sideS;
          e.pathT = 0;             // 경로도 즉시 다시 뽑는다(흐름장으로 갈아타게)
        }
        e.chkT = 0; e.wantD = 0; e.gotD = 0;
      }
      // ── 지면 따라가기 ──
      // ★야생 맵은 평지 0.02 위에 너럭바위 단(0.16~0.26)이 여기저기 있다. 예전 요괴는
      //   떠 있어서 안 보였지만 고블린은 발이 있다. 안 맞추면 단 위에서 발목이 묻힌다.
      //   한 프레임에 순간이동하면 눈에 띄니 플레이어와 같은 방식으로 따라가게 한다.
      const gy = LV.groundY(e.pos.x, e.pos.z);
      if (e.pos.y !== gy) {
        e.pos.y += (gy - e.pos.y) * Math.min(1, dt * 16);
        if (Math.abs(gy - e.pos.y) < 0.002) e.pos.y = gy;
      }
    }

    // ── 약한 밀어내기 ──
    // 안 넣으면 무리가 한 점에 겹쳐서 한 마리처럼 보인다. 40마리여도 780쌍이라
    // 그리드 없이 그냥 돌려도 프레임에 안 잡힌다.
    for (let i = 0; i < n; i++) {
      const ei = live[i];
      for (let j = i + 1; j < n; j++) {
        const ej = live[j];
        const dx = ei.pos.x - ej.pos.x, dz = ei.pos.z - ej.pos.z;
        const dd = dx * dx + dz * dz;
        const rr = (ei.size + ej.size) * 0.52;
        if (dd > rr * rr || dd < 1e-6) continue;
        const dist = Math.sqrt(dd);
        const push = (rr - dist) * 0.5 * 0.55;
        const ux = dx / dist, uz = dz / dist;
        ei.pos.x += ux * push; ei.pos.z += uz * push;
        ej.pos.x -= ux * push; ej.pos.z -= uz * push;
      }
    }
    // ── ★몸 충돌: 플레이어를 밀고 들어오지 못하게 ──
    // 요괴끼리 쓰는 것과 **같은 계열**이다(겹친 만큼 반대로 민다). 다른 점은 둘.
    //   1) 밀리는 건 요괴뿐이다. 플레이어는 안 밀린다 = 둘러싸여도 안 갇힌다.
    //   2) 한 프레임에 밀리는 양에 상한(BODY_PUSH_MAX)을 둔다 = 안 튕겨 나간다.
    // 간격 SEP 의 근거는 위 BODY_GAP 주석의 실측표에 있다(0.78~0.85m).
    for (let i = 0; bodyPush && i < n; i++) {
      const e = live[i];
      const dx = e.pos.x - player.x, dz = e.pos.z - player.z;
      const dd = dx * dx + dz * dz;
      const sep = LV.PLAYER_RADIUS + ENEMY_R * e.size + BODY_GAP;
      if (dd >= sep * sep) continue;
      const dist = Math.sqrt(dd);
      let ux, uz;
      if (dist < 1e-3) {
        // 정확히 겹쳤을 때는 방향이 없다. 요괴가 보는 쪽 뒤로 물린다.
        ux = -Math.sin(e.yaw); uz = -Math.cos(e.yaw);
      } else { ux = dx / dist; uz = dz / dist; }
      let step = (sep - dist) * BODY_PUSH_K;
      const cap = BODY_PUSH_MAX * dt;
      if (step > cap) step = cap;
      e.pos.x += ux * step; e.pos.z += uz * step;
    }
    // 서로 밀어낸 결과가 벽 안쪽일 수 있다(좁은 문에 무리가 몰릴 때). 한 번 빼준다.
    // ★순서 주의: 몸 충돌보다 **나중**이어야 한다. 벽이 최종 판정이라, 벽과 플레이어
    //   사이에 낀 요괴는 간격을 못 지킨 채 벽 쪽에 남는다(요괴를 벽에 밀어 넣는 것보다
    //   낫다). 그 상태로 플레이어가 한 발 물러나면 바로 간격이 회복된다.
    for (let i = 0; i < n; i++) {
      const e = live[i];
      const s = LV.pushOut(e.pos.x, e.pos.z, ENEMY_R * e.size, _mv);
      e.pos.x = s.x; e.pos.z = s.z;
    }

    // ── 몸 세우기 · 클립 고르기 ──
    for (let i = 0; i < n; i++) {
      const e = live[i];
      const v = e.vis;
      if (!v) continue;                                   // 풀이 모자라 몸이 없는 개체(방어)
      // 튀어나오듯 커진다. 뼈가 있는 지금도 이건 남긴다(리스폰 순간이 눈에 보여야 한다).
      const pop = Math.min(1, (T - e.spawnT) * 3.5);
      v.grp.position.set(e.pos.x, e.pos.y, e.pos.z);
      v.grp.rotation.set(0, e.yaw, 0);
      // ── 경직 반동 ──
      // 비치명 명중 60ms 동안 세로로 눌리고 가로로 퍼진다 + 밀리는 쪽으로 살짝 젖혀진다.
      // "맞았다"를 몸으로 알리는 신호다. 흰 번쩍임만으론 재질 하나만 바뀌어서 약하다.
      const base = K_H * e.size * pop;
      // ── ★예비 자세 (공격 예고) ──
      // 몸을 뒤로 젖히며 세로로 늘어난다. 34m 에서 읽히는 건 색이 아니라 **실루엣**이다.
      // u 는 0(막 시작) -> 1(터지기 직전).
      const wu = e.wndT > 0 ? 1 - e.wndT / ATK_WIND : 0;
      if (e.sqT > 0) {
        e.sqT -= dt;
        const q = Math.max(0, e.sqT / SQUASH_T);          // 1 -> 0
        const k = Math.sin(q * Math.PI * 0.85);           // 붙었다 풀린다
        // ★반동 깊이 (17차). 0.12/0.15 -> 0.17/0.21. 34m 쿼터뷰에서 고블린 실루엣 세로가
        //   80px 남짓이라 15% 는 12px 이고, 그게 100ms 안에 들어갔다 나온다 = 거의 안 보인다.
        //   21% 면 17px 이라 눌린 프레임이 실루엣으로 읽힌다. 몸집(base)에 곱해지므로
        //   큰 놈일수록 크게 눌린다(무게 차이가 저절로 난다).
        v.grp.scale.set(base * (1 + 0.17 * k), base * (1 - 0.21 * k), base * (1 + 0.17 * k));
        // 젖힘: 밀려나는 방향(kb)으로 상체가 넘어간다. ★0.22 -> 0.32rad(약 18도).
        //   실루엣이 기우는 건 스케일보다 훨씬 멀리서도 읽힌다.
        const kl = Math.hypot(e.kb.x, e.kb.z);
        if (kl > 1e-4) {
          v.grp.rotation.set(0, e.yaw, 0);
          v.grp.rotateOnWorldAxis(_lean.set(-e.kb.z / kl, 0, e.kb.x / kl), 0.32 * k);
        }
      } else if (wu > 0) {
        // 세로 +11% / 가로 -5% 로 "치켜든다". 그리고 뒤로 0.16rad 젖힌다.
        v.grp.scale.set(base * (1 - 0.05 * wu), base * (1 + 0.11 * wu), base * (1 - 0.05 * wu));
        v.grp.rotation.set(0, e.yaw, 0);
        // 젖히는 축 = 보는 방향의 오른쪽(= 뒤로 눕는다)
        v.grp.rotateOnWorldAxis(_lean.set(Math.cos(e.yaw), 0, -Math.sin(e.yaw)), -0.16 * wu);
      } else {
        v.grp.scale.setScalar(base);
      }
      // ── 자체발광 두 갈래 ──
      // ★흰색 setScalar 를 버렸다. 전신이 흰 덩어리가 되면 형태가 지워진다
      //   (건틀릿 캐릭터 심사관이 보스에게 같은 지적을 했다: "전신 플랫 주황").
      //   피격 = 주홍 · 공격 예고 = 호박. 색이 갈려야 둘이 각각 읽힌다.
      //   가산이라 G·B 의 명암(= 셰이딩)은 그대로 남는다.
      // ★단, 가산도 **몸 색보다 크면** 명암이 뭉갠다. 세기 상한은 FLASH_R/G/B
      //   선언부 주석 참조(선형 HDR · ACES 무릎 · 블룸 임계 1.02).
      const wg = wu > 0 ? Math.pow(Math.max(0, (wu - 0.5) / 0.5), 1.6) : 0;   // 끝 절반에서만 번득인다
      v.mat.emissive.setRGB(
        e.flash * FLASH_R + wg * WIND_R,
        e.flash * FLASH_G + wg * WIND_G,
        e.flash * FLASH_B + wg * WIND_B);
      // ── 클립 ──
      // ★재생속도 = 이동속도 / 그 클립의 접지 발 속도. 이래야 발이 안 미끄러진다.
      //   발 속도는 키에 비례하므로 개체 몸집(e.h)으로 환산한다.
      if (e.atkT > 0) {
        // 공격 중. 위에서 이미 클립을 걸었다.
      } else if (e.want > 1.05) {
        playClip(v, 'Run', e.want / (RUN_FOOT * e.h / GOB_H));
      } else if (e.want > 0.05) {
        playClip(v, 'Walk', e.want / (WALK_FOOT * e.h / GOB_H));
      } else {
        playClip(v, 'Idle', 1);
      }
      // ★경직 중에는 클립을 거의 세운다. 맞은 자세로 멎고 몸만 밀려나는 그림이
      //   "때렸다"를 제일 강하게 만든다(0 으로 완전히 세우면 뻣뻣해서 STUN_TS 만큼만).
      v.mixer.update(e.stunT > 0 ? dt * STUN_TS : dt);
      // 가짜 그림자
      // ★맵 바닥이 0.02 다. 그림자를 0.02 에 두면 바닥과 완전히 같은 높이라
      //   z-fighting 으로 지글거린다. 2.5cm 띄운다.
      _v2.set(e.pos.x, e.pos.y + 0.025, e.pos.z);
      const sh = e.size * pop * 0.42;
      _sc.set(sh, 1, sh);
      _mat.compose(_v2, _q2.identity(), _sc);
      shadowMesh.setMatrixAt(i, _mat);
      shAttr.setX(i, pop);
    }
    shadowMesh.count = n;
    shadowMesh.instanceMatrix.needsUpdate = true;
    shAttr.needsUpdate = true;

    updateCorpses(dt);
    updateInk(dt);
    // ★게임시계로 늙는다. 위 update 는 ctx.paused 면 통째로 일찍 빠져나가고, 히트스톱은
    //   main.js 가 dt 를 0 쪽으로 눌러서 넣으므로 둘 다 여기서 저절로 붙들린다.
    updateDmgPops(dt);
    updatePlates();

    // ── 예열 판 거두기 (6프레임이면 확실히 한 번은 그려졌다) ──
    // ★예전엔 stepWarm() 이라는 **별도 함수 호출**이었다. 2026-08-10 지형 정찰에서
    //   `stepWarm is not defined` 가 프레임마다 터져 렌더 루프가 통째로 죽은 배치가
    //   한 번 나왔다(1207회 연속, 캔버스 사망 / handoff_terrain.md 1장).
    //   코드는 호이스팅되는 함수 선언이라 정적으로는 성립하고, 리로드 10회 재현에서도
    //   0건이었다. 원인은 **여러 에이전트가 같은 파일을 동시에 고치는 동안 브라우저가
    //   중간 상태를 받은 것**이다 - 호출은 들어갔는데 정의는 아직 안 들어간 저장본은
    //   문법이 멀쩡해서 그대로 로드된다(모듈 URL 캐시 때문에 나중까지 되살아난다).
    //   그래서 매 프레임 도는 자리에서는 바깥 이름을 아예 안 부른다. 한 덩어리라
    //   "반쪽만 반영된 상태" 자체가 생길 수 없다.
    // ★거두기가 실패해도 렌더 루프는 못 멈춘다. 최악이 1e-3 크기(1픽셀 미만)
    //   메시 한 벌이 남는 것이라, 화면 전체와 바꿀 값이 아니다.
    if (warmObj && --warmLeft <= 0) {
      const w = warmObj;
      warmObj = null;
      try {
        if (w.twin.parent) w.twin.parent.remove(w.twin);
        w.v.mesh.frustumCulled = true;     // 빌려 쓴 값은 원래대로 돌려놓는다
        giveVis(w.v);                      // 재질도 여기서 원본으로 되돌아간다
        if (DEV) console.log('[enemy] 두 동강 재질 예열 완료');
      } catch (e) {
        console.warn('[enemy] 예열 판 거두기 실패(연출만 손해다)', e);
      }
    }

    // ── 플레이어 상태 ──
    if (iframe > 0) iframe -= dt;
    if (iframeDash > 0) iframeDash -= dt;
    // 새는 통. 최근에 받은 피해가 이 속도로 빠져나가고, 남아 있는 만큼이 다음
    // 타격을 흡수한다(= 겹쳐 맞아도 초당 총량이 DMG_LEAK 을 못 넘는다).
    if (dmgBucket > 0) { dmgBucket -= DMG_LEAK * dt; if (dmgBucket < 0) dmgBucket = 0; }
    if (hurtFlash > 0) {
      hurtFlash -= dt * 3.2;
      hurtEl.style.opacity = Math.max(0, hurtFlash * 0.75).toFixed(3);
    }
    if (dead && T >= deadUntil) respawnPlayer();
    syncHud();
  }

  // 첫 배치
  resetField();

  // -------------------------------------------------------------------------
  const api = {
    update,
    reset: respawnPlayer,
    get kills() { return kills; },
    // ★처치 수는 "판(R~클리어)" 기준이다. R 재시작에서 main.js 가 부른다.
    //   죽음(리스폰)은 판이 이어지는 것이므로 여기서 지우면 안 된다.
    resetKills() { kills = 0; },
    // ★소수점이 생긴다. 겹쳐 맞을 때 흡수분만큼 깎여 8·2·2 처럼 들어가기 때문이다
    //   (아래 damagePlayer 의 새는 통). 화면에는 체력바 폭이라 눈에 안 띈다.
    get hp() { return +hp.toFixed(1); },
    get count() { return live.length; },
    get chasing() { let c = 0; for (const e of live) if (e.mode === 1) c++; return c; },
    // 두리번거리는 중인 놈 수. "숨었더니 정말 놓쳤나"를 숫자로 본다.
    get searching() { let c = 0; for (const e of live) if (e.mode === 3) c++; return c; },
    // ── 공격 방향 스냅 ──
    // main.js 의 tryAttack/tryHeavy/tryWide 가 입력 순간 이 둘만 쓴다.
    nearestTo,
    snapFacing,
    get snap() {
      return { on: snapOn, r: SNAP_R, dur: SNAP_DUR,
               running: !!snap, left: snap ? +(snap.dur - snap.t).toFixed(3) : 0 };
    },
    setSnap(on) { snapOn = !!on; if (!snapOn) snap = null; return snapOn; },
    // 받은 피해 상한(새는 통) 상태. DPS 가 정말 묶여 있는지 확인하는 창구다.
    get guard() { return { bucket: +dmgBucket.toFixed(2), leak: DMG_LEAK,
                           iframe: +Math.max(0, iframe).toFixed(3),
                           dash: +Math.max(0, iframeDash).toFixed(3), dodged: dodgeN,
                           sinceHurt: +(T - lastHurtT).toFixed(2) }; },
    tris: TRIS,
    aggroRadius: AGGRO_RADIUS,
    leashDist: LEASH_DIST,
    groupRespawn: GROUP_RESPAWN,
    // 검증용. 최근 스윙별 명중 수
    get log() { return hitLog.slice(); },
    // ★처치 전수 기록(유령 킬 조사 창구). kills 를 올리는 자리가 이 파일에 한 곳뿐이라
    //   이 배열이 곧 "왜 숫자가 올라갔나"의 전부다. onScreen=false 면 화면 밖 처치다.
    get killLog() { return killLog.slice(); },
    // 머리 위 판이 실제로 몇 장 서 있나(눈 없이 회귀를 잡는 창구)
    // ★atkMark/cells/winding/slots 은 쐐기 제거의 증거다. winding > 0 인데 slots 에 2 가
    //   한 번도 안 들어오면 "예고는 도는데 삼각형은 없다"가 코드로 증명된다.
    get plates() { return { pip: plateCount.pip, mark: plateCount.mark,
                            tex: !!markMat.uniforms.uTex.value,
                            atkMark: MARK_ATK_ON, cells: MARK_N,
                            ...markCensus() }; },
    // ── ★체력 바 계약 창구 (읽기 전용) ──
    // 「폭이 몹 종류와 무관하게 같은가 · 눈금이 한 대 단위인가」를 눈이 아니라 수로
    // 확인하는 자리다. seg 는 **계약을 그대로 계산해 보여 준다** - 상수를 다시 적지 않고
    // 셰이더와 같은 식(maxHp / SWORD_DMG)을 쓰므로 둘이 어긋날 수 없다.
    get bar() {
      const seg = {};
      for (const mx of [1, 2, 3]) seg[mx] = Math.round(mx / SWORD_DMG);
      return { w: BAR_W, h: PIP_H, fixedW: true, seg,
               tickHalf: BAR_TICK_HW, tickAA: BAR_TICK_AA,
               tickMul: BAR_TICK_MUL, tickLift: BAR_TICK_LIFT,
               show: PIP_SHOW, fade: PIP_FADE,
               lowHp: +(SWORD_DMG * 1.5).toFixed(4), pip: SWORD_DMG };
    },
    // ── ★머리 위 체력 바 검증 창구 (쓰는 창구) ──
    // 만피 / 부분 / 저체력을 **같은 자리·같은 카메라**에서 나란히 찍으려면 체력을
    // 때려서 만들면 안 된다 - 한 대 칠 때마다 넉백으로 놈이 밀려서 화소가 안 겹친다.
    // 그래서 상태를 세워 두는 창구를 판다(dmgTest·setFlashHold 와 같은 갈래다).
    //   i     = positions 순서(살아 있는 목록 인덱스)
    //   hp    = 남길 체력. 바 채움은 hp / maxHp 그대로다
    //   maxHp = 그 놈의 최대 체력. **바 폭은 안 변하고 눈금 칸 수가 변한다**
    //           (칸 = maxHp / 칼 한 대 → 1핍 2칸 · 2핍 4칸 · 리더 6칸). 안 주면 안 건드린다
    //   show  = 바가 떠 있을 시간(초). 크게 주면 촬영 내내 안 걷힌다
    pipTest(i, hp, maxHp, show) {
      const e = live[i | 0];
      if (!e) return null;
      if (maxHp !== undefined && maxHp !== null) e.maxHp = Math.max(1, maxHp | 0);
      // ★0 은 안 넣는다. 0 이하는 "죽었다"의 뜻이라 다음 타격 판정이 시체를 만든다.
      if (hp !== undefined && hp !== null) e.hp = Math.max(0.01, Math.min(e.maxHp, +hp));
      e.pipT = (show === undefined || show === null) ? PIP_SHOW : +show;
      return { i: i | 0, hp: +e.hp.toFixed(2), maxHp: e.maxHp, pipT: +e.pipT.toFixed(2),
               x: +e.pos.x.toFixed(2), z: +e.pos.z.toFixed(2), y: +e.pos.y.toFixed(2),
               h: +e.h.toFixed(2) };
    },
    // ── ★숫자 아틀라스 실측 창구 (읽기 전용) ──
    // 겹의 두께를 눈이 아니라 픽셀로 잰다. d 칸의 세로 v 자리 가로줄을 훑어
    // 마스크 채널이 이어지는 길이를 돌려준다:
    //   ol  = 바깥 겹(G) 이 좌우로 몇 px · rim = 그 안쪽 겹(B) · fill = 속(R) · ink = 잉크 전체 폭
    // "흰 테가 굵은가 / 바깥 겹이 얇은 키라인인가"는 이 세 수로만 판정한다.
    // ★지금 서 있는 숫자 판의 자리(읽기 전용, 그린 순서 그대로).
    //   "자리마다 높이가 다른가 / 얼마나 겹치는가 / 왼쪽이 위 레이어인가"는 코드를 다시
    //   계산할 게 아니라 **정점 버퍼**에서 읽어야 한다(다시 계산하면 자기 채점이다).
    //   그린 순서가 곧 레이어다 - 깊이검사가 꺼져 있어 나중 것이 위다.
    get dmgPlates() {
      const out = [];
      const pos = dmgMesh.geometry.attributes.position.array;
      for (let i = 0; i < dmgShown; i++) {
        const o = i * 4 * 3;
        let x = 0, y = 0, z = 0, hy = 0;
        for (let k = 0; k < 4; k++) { x += pos[o + k * 3]; y += pos[o + k * 3 + 1]; z += pos[o + k * 3 + 2]; }
        for (let k = 0; k < 4; k++) hy = Math.max(hy, Math.abs(pos[o + k * 3 + 1] - y / 4));
        out.push({ i, x: +(x / 4).toFixed(4), y: +(y / 4).toFixed(4), z: +(z / 4).toFixed(4),
                   half: +hy.toFixed(4) });
      }
      return out;
    },
    // ★검증용 숫자 띄우개. 게임은 한 대에 100 만 띄우므로 다섯 자리 판독을 볼 방법이 없다.
    //   읽기만 하는 창구가 아니라 상태를 만드는 창구라 이름에 test 를 남긴다.
    dmgTest(amount, kill, dx = 0, dz = 0) {
      const p = getPlayerPos();
      spawnDmgPop(p.x + dx, p.y + 1.2, p.z + dz, amount, !!kill);
      return dmgSpawned;
    },
    dmgScan(d = 0, v = 0.5, row = 0) {
      if (!digCanvas) return null;
      const g = digCanvas.getContext('2d');
      const r0 = Math.max(0, Math.min(DIG_ROWS - 1, row | 0));
      const y = DIG_CH * r0 + Math.max(0, Math.min(DIG_CH - 1, Math.round(v * DIG_CH)));
      const im = g.getImageData(DIG_CW * (d | 0), y, DIG_CW, 1).data;
      let ol = 0, rim = 0, fill = 0, ink = 0, x0 = -1, x1 = -1;
      for (let x = 0; x < DIG_CW; x++) {
        const r = im[x * 4], gg = im[x * 4 + 1], bb = im[x * 4 + 2], aa = im[x * 4 + 3];
        if (aa < 26) continue;                       // 거의 안 덮인 자리는 잉크로 안 친다
        ink++; if (x0 < 0) x0 = x; x1 = x;
        if (gg >= r && gg >= bb) ol++;
        else if (bb >= r) rim++;
        else fill++;
      }
      return { d: d | 0, v, row: r0, ol, rim, fill, ink, span: x1 - x0 + 1,
               // 굽힌 굵기(px)와 그 중 **보이는** 두께. 보이는 건 절반씩이다(속이 안쪽을 덮는다)
               bakeOl: DIG_W[r0].ol, bakeRim: DIG_W[r0].rim,
               seenRim: DIG_W[r0].rim / 2, seenKey: (DIG_W[r0].ol - DIG_W[r0].rim) / 2,
               cw: DIG_CW, ch: DIG_CH, adv: +digAdv.toFixed(4),
               advPx: +(digAdv * DIG_CW).toFixed(1),
               // 자간 계약: 전진 / 잉크 폭. 0.70~0.80 이면 "살짝 겹친다"
               advOverInk: digInk > 0 ? +((digAdv * DIG_CW) / digInk).toFixed(3) : null,
               inkW: digInk };
    },
    // ── 데미지 숫자 창구 ──
    // 950프레임 안정성 판정이 이걸 본다. bad 는 NaN·음수라 **버린** 요청 수다(0 이어야 한다).
    // nan 은 지금 떠 있는 뭉치 중 좌표·나이가 깨진 것(정의상 늘 0 이어야 한다).
    // ★17차: 나이 하한이 0 이 아니라 -DMG_DELAY 다. 숫자가 참격 획을 덮지 않게 한 박자
    //   늦춰 띄우면서 **뜨기 전 구간의 t 가 음수**가 됐기 때문이다(위 DMG_DELAY 주석).
    //   여기를 안 고치면 950 안정성 판정이 정상 대기 중인 뭉치를 nan 으로 센다
    //   (실제로 nan 2 가 나왔다 — 코드가 아니라 자가 틀린 경우였다).
    //   waiting 을 따로 내줘서 "그래서 몇 개가 대기 중인가"를 눈으로 볼 수 있게 둔다.
    get dmg() {
      let alive = 0, nan = 0, digits = 0, maxT = 0, waiting = 0;
      for (const p of dmgPops) {
        if (!p.on) continue;
        alive++; digits += p.n;
        if (p.t < 0) waiting++;
        if (!(isFinite(p.x) && isFinite(p.y) && isFinite(p.z)
              && p.t >= -DMG_DELAY - 1e-3)) nan++;
        if (p.t > maxT) maxT = p.t;
      }
      return { alive, digits, plates: dmgShown, nan, waiting, delay: DMG_DELAY,
               spawned: dmgSpawned, bad: dmgBad,
               maxT: +maxT.toFixed(3), ttl: DMG_TTL,
               h: DMG_H, killSc: DMG_KILL_SC, adv: +digAdv.toFixed(3),
               // ★18차: scale = 칼 데미지 배율(롤백 손잡이) · per = 한 대에 뜨는 수 ·
               //   lowHp = 바가 붉어지는 문턱(= 다음 한 대에 죽는 체력). 셋이 전부
               //   DMG_SCALE 에서 나오므로 여기 세 수만 보면 밸런스 회귀가 잡힌다.
               scale: DMG_SCALE, per: SWORD_DMG * DMG_SHOW, pip: SWORD_DMG,
               lowHp: +(SWORD_DMG * 1.5).toFixed(4), show: DMG_SHOW,
               tex: !!dmgMat.uniforms.uTex.value,
               // 마지막으로 그린 뭉치의 화면 크기. cellPx = 칸 · glyphPx = 글자 획
               // (screenH 를 720 으로 잡은 값. 해상도가 달라지면 비례해 커진다)
               cellPx: +(dmgFrac * 720).toFixed(1),
               glyphPx: +(dmgFrac * GLYPH_OF_CELL * 720).toFixed(1),
               fracKind: dmgFracKind,
               // 옛 피격 플래시 세기(0 이어야 한다. 오너 지시로 껐다)
               flash: [FLASH_R, FLASH_G, FLASH_B] };
    },
    // 지금 살아 있는 놈들의 리액션 상태. 경직·예비 자세가 실제로 도는지 숫자로 본다.
    get react() {
      let stun = 0, wind = 0, pip = 0, flash = 0;
      for (const e of live) {
        if (e.stunT > 0) stun++;
        if (e.wndT > 0) wind++;
        if (e.pipT > 0) pip++;
        if (e.flash > 0) flash++;
      }
      return { stun, wind, pip, flash, hitStun: HIT_STUN, atkWind: ATK_WIND,
               dmg: ENEMY_DMG, leak: DMG_LEAK };
    },
    // ★두 동강 재질 예열 창구(main.js 가 renderer 를 갖고 있을 때 쓸 수 있게).
    //   기본은 자동이다(로드 직후 6프레임짜리 1픽셀 예열). 이건 보조 경로다.
    warmCut(renderer, cam) {
      const mats = [];
      for (const c of corpses) { mats.push(c.matA, c.matB); }
      if (renderer && cam && renderer.compile) {
        // 씬에 안 붙은 재질은 compile 이 못 잡는다. 자동 예열이 실패했을 때의
        // 최후 수단으로 남겨 둔다(재질 목록을 그대로 돌려준다).
        try { renderer.compile(scene, cam); } catch (e) { /* 무시 */ }
      }
      return mats;
    },
    // 검증용. 무리 상태 한눈에
    get field() {
      return groups.map(g => ({
        i: g.idx, at: [g.cx, g.cz],
        alive: g.spots.reduce((s, x) => s + (x.enemy ? 1 : 0), 0),
        aggro: g.aggro, ret: g.returning, srch: !!g.searching,
        lostT: +g.lostT.toFixed(2),
        respawnIn: g.respawnAt < 0 ? null : +(g.respawnAt - T).toFixed(1),
      }));
    },
    // 성능 실측용. 플레이어 주변에 임시 무리를 세워 전부 달려들게 한다.
    // tmp 무리라 전멸해도 안 되살아난다.
    stress(nWant) {
      const p = getPlayerPos();
      const room = Math.min(nWant | 0, MAX_ENEMIES - live.length);
      const g = { idx: groups.length, cx: p.x, cz: p.z, spots: [],
                  aggro: false, returning: false, searching: false, lostT: 0,
                  seenX: undefined, seenZ: undefined, respawnAt: -1, tmp: true };
      for (let k = 0; k < room; k++) {
        const ang = (k / room) * Math.PI * 2;
        const rr = 5 + (k % 3) * 1.6;
        g.spots.push({
          home: homeAt(p.x + Math.cos(ang) * rr, p.z + Math.sin(ang) * rr),
          leader: false, seed: 900 + k * 13, enemy: null,
        });
      }
      groups.push(g);
      for (const s of g.spots) spawnAt(s, g);
      aggroGroup(g);
      return live.length;
    },
    resetField,
    // ── 플래시 고정 창구 ──
    // 번쩍임의 꼭대기를 세워 두고 화면을 찍는다(순백 회귀를 눈이 아니라 픽셀로 잡는다).
    // 인자 없이 부르면 해제. 0~1 을 주면 살아있는 개체·시체 모두 그 값으로 고정된다.
    // ★2026-08-12 이후로는 **화면이 안 변한다**(FLASH_R/G/B = 0, 오너 지시). 창구는
    //   그대로 살려 둔다 - 플래시를 되살리는 날 이게 A/B 를 재는 유일한 자다.
    //   실제로 이번 제거를 증명한 것도 이 창구다(12쌍 켬/끔 평균: 옛 판 R +18.2 ->
    //   새 판 -1.1, 잡음 안. renders/history/v98_wave12/dmgnum/flash/).
    setFlashHold(v) {
      flashHold = (v === undefined || v === null || v < 0) ? -1 : Math.min(1, +v);
      return flashHold;
    },
    // 판정이 눈에 보이는 칼과 맞는지 확인하려고 실제 판정 선분을 그린다.
    showBlade(on) {
      if (on && !dbgLine) {
        const g = new THREE.BufferGeometry();
        g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(6), 3));
        dbgLine = new THREE.Line(g, new THREE.LineBasicMaterial({
          color: 0x3060ff, depthTest: false, transparent: true,
        }));
        dbgLine.frustumCulled = false;
        dbgLine.renderOrder = 99;
        scene.add(dbgLine);
      }
      if (dbgLine) dbgLine.visible = !!on;
    },
    // ── 캡슐 판정 검증 창구 ──
    // "칼끝이 1.20 을 지나는데 정말 닿느냐"를 숫자로 확인한다.
    // a,b = 칼날 선분(월드). x,z,y = 요괴가 선 자리(y 는 발밑). size = 몸집 배수.
    capsule: { r: CAP_R, lo: CAP_LO, hi: CAP_HI, h: GOB_H, pad: BLADE_PAD },
    capsuleDist(a, b, x, z, y, size) {
      const sz = size || 1, h = GOB_H * sz;
      _capA.set(x, (y || 0) + h * CAP_LO, z);
      _capB.set(x, (y || 0) + h * CAP_HI, z);
      const need = CAP_R * sz + BLADE_PAD;
      const d = Math.sqrt(segSegDist2(a, b, _capA, _capB, _hitP));
      return { dist: +d.toFixed(4), need: +need.toFixed(4), hit: d <= need,
               atY: +_hitP.y.toFixed(4),
               seg: [+_capA.y.toFixed(3), +_capB.y.toFixed(3)] };
    },
    // 성능·풀 상태
    get vis() { return { made: visMade, free: visFree.length, cap: MAX_VIS,
                         corpses: corpses.reduce((s, c) => s + (c.on ? 1 : 0), 0),
                         // 먹 소멸·먹 파열 상태(눈 없이 회귀를 잡는 창구)
                         dis: corpses.filter(c => c.on)
                           .map(c => +c.matA.userData.u.uDis.value.toFixed(2)),
                         ink: { tex: inkTexOk, spawned: inkN,
                                live: inkParts.reduce((s, p) => s + (p.t < p.ttl ? 1 : 0), 0) } }; },
    // ★맵을 다시 구울 때마다 확인해야 하는 값. 무리 자리 39곳이 실제로 설 수 있는
    //   자리인지(벽 속에 박히지 않았는지) 한 번에 본다.
    get placement() {
      const out = [];
      for (const g of groups) {
        for (const s of g.spots) {
          out.push({ g: g.idx, x: +s.home.x.toFixed(2), z: +s.home.z.toFixed(2),
                     y: +s.home.y.toFixed(2), blocked: LV.blocked(s.home.x, s.home.z, ENEMY_R) });
        }
      }
      return out;
    },
    // 지금 살아 있는 개체의 실제 좌표(무리가 벽에 끼었는지 눈으로 안 보고 확인)
    // ★hp·maxHp·lastSwing 도 같이 준다(읽기 전용). "한 스윙에 한 번"이 정말 지켜지는지는
    //   개체별 체력을 따라가야 답이 나온다 - 스윙별 명중 수(log)만으로는 "두 놈을 한 번씩"과
    //   "한 놈을 두 번"이 구분되지 않는다(13-X 단타 조사에서 이것 때문에 한나절 헤맸다).
    get positions() {
      return live.map(e => ({ g: e.grp ? e.grp.idx : -1, mode: e.mode,
        hp: e.hp, maxHp: e.maxHp, lastSwing: e.lastSwing,
        x: +e.pos.x.toFixed(2), z: +e.pos.z.toFixed(2), y: +e.pos.y.toFixed(2),
        offHome: e.home ? +Math.hypot(e.pos.x - e.home.x, e.pos.z - e.home.z).toFixed(2) : null,
        stuck: LV.blocked(e.pos.x, e.pos.z, ENEMY_R * e.size * 0.85) }));
    },
    get hot() { return hotState; },
    get swing() { return swingId; },
    // ── 스윙 번호 최소 간격 A/B 창구 ──
    // 이 값 아래로 다시 켜진 hot 은 **같은 스윙**으로 묶인다(= 같은 요괴 재타격 없음).
    // 내리면 main.js 의 연타 바닥(ATK_MIN_GAP)도 같이 내릴 수 있고, 너무 내리면
    // 한 번 휘두른 게 두 스윙으로 갈려 같은 적을 두 번 벤다. 그 경계는 눈으로 못 본다.
    // 0 을 넣으면 억제가 통째로 꺼진다(= 노이즈 재점화를 날것으로 재는 모드).
    setSwingGap(v) { const s = +v; if (s >= 0) SWING_GAP = s; return SWING_GAP; },
    get swingGap() { return SWING_GAP; },
    // ── 검증 창구 (몸 충돌 · 길찾기 · 은신) ──
    // 지금 살아 있는 놈들이 플레이어와 얼마나 떨어져 있는지. 무리 한가운데에서
    // "제일 가까운 놈이 몇 m 인가"가 몸 충돌의 성공 판정이다.
    get near() {
      const p = getPlayerPos();
      const arr = live.map(e => ({
        d: +Math.hypot(e.pos.x - p.x, e.pos.z - p.z).toFixed(3),
        sep: +(LV.PLAYER_RADIUS + ENEMY_R * e.size + BODY_GAP).toFixed(3),
        mode: e.mode, direct: e.direct, side: +e.sideT.toFixed(2),
      })).sort((a, b) => a.d - b.d);
      return { min: arr.length ? arr[0].d : null, list: arr.slice(0, 8) };
    },
    // 길찾기가 실제로 도는지. flow = 흐름장을 따라가는 중인 놈, side = 옆걸음 중인 놈
    get pathing() {
      let flow = 0, side = 0, chase = 0;
      for (const e of live) { if (e.mode === 1) chase++; if (e.mode === 1 && !e.direct) flow++; if (e.sideT > 0) side++; }
      return { chase, flow, side, nav: NAV.debug.stats() };
    },
    get stealth() { return ST.state(); },
    nav: NAV.debug,
    bodyGap: BODY_GAP,
    loseSight: LOSE_SIGHT,
    setBodyPush(on) { bodyPush = !!on; return bodyPush; },
    setPathing(on) { usePath = !!on; return usePath; },
    // ── boss.js 접점 ──
    // ★플레이어 체력·무적(0.65초)·사망은 **여기 한 군데서만** 관리한다.
    //   보스가 자기 체력을 따로 들면 체력바가 두 개가 되고, 무적이 갈라져서
    //   잡몹과 보스에게 같은 프레임에 두 번 맞는다.
    damagePlayer,
    // ── 대시 무적 창구 ──
    // main.js 가 대시 나가는 프레임에 setIframe(0.20) 으로 부른다(typeof 검사를 하고
    // 있어서 이 함수가 없는 빌드에서도 게임은 그대로 돈다). 이름·인자를 바꾸면
    // main.js 쪽 호출도 같이 봐야 한다.
    setIframe,
    get dead() { return dead; },
    // ── 되살아나기까지 남은 게임시간(초). 안 죽었으면 null ──
    // ★ui.js 가 이걸 보고 「落」카드를 **텔레포트보다 먼저** 내린다(v84 QA S2).
    //   벽시계로 세면 슬로모·프레임 스로틀에서 어긋난다. 여기 시계를 그대로 준다.
    get deadIn() { return dead ? +Math.max(0, deadUntil - T).toFixed(2) : null; },
    respawnDelay: RESPAWN_DELAY,
    respawnCardLead: RESPAWN_CARD_LEAD,
  };
  return api;
}

// ---------------------------------------------------------------------------
// boss.js 의 **폴백 경로 전용** export 다. 보스 외형은 이제 boss.glb(각귀 실모델)라
// 평상시에는 아무도 이 둘을 안 부른다. boss.glb 로드가 실패했을 때만 boss.js 가
// 요괴 덩어리를 2.6배로 키워 임시 보스로 세운다.
// ★그때 쓸 지오메트리를 보스용으로 따로 구우면 조명·안개·플래시 계산이 두 벌이 되어
//   잡몹과 보스가 서로 다른 세계에 있는 것처럼 보인다. 폴백이라도 같은 걸 내준다.
// ---------------------------------------------------------------------------
export { buildYokaiGeometry, makeEnemyMaterial };
