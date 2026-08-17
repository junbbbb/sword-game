// 아이템 드랍 (20차. 오너 지시 "메이플스토리처럼 아이템 드랍되게해줘 아이템창도 만들고")
//
// 이 파일이 지는 일은 셋이다.
//   ① **떨어뜨린다**  요괴를 벤 자리에서 물건이 포물선으로 톡 튀어 바닥에 앉는다
//   ② **줍는다**      가까이 가면 빨려 들어오고 닿으면 자동으로 주머니에 들어간다
//   ③ **센다**        무엇을 몇 개 가졌나(주머니). 화면에 그리는 건 ui.js 몫이다
//
// ★왜 별 파일인가: main.js 는 이미 5천 줄이고, 여기 값들(튀는 높이·바운스 감쇠·
//   자석 반경)은 0.05초 단위의 감각이라 **혼자 놓고 만져야** 맞는 값이 나온다.
//
// ★★그리는 방법은 두 벌이고 스위치 하나로 갈린다(DROP_3D).
//   · 3D(지금) = **품목별 InstancedMesh 한 벌**. 같은 품목이 스무 개 굴러도 드로우콜 하나다
//   · 2D(옛것)  = 화면을 향해 서는 빌보드 판 한 벌(시트·UV·알파가 그대로 살아 있다)
//   여기에 바닥 그림자 판 하나 + 반짝/획득팝 가산 판 하나가 늘 따라붙는다.
//   개체마다 Mesh 를 만들면 40 드로우콜이 되고, 그건 이 게임의 예산이 아니다.
//
// ★FLOOR_* 규칙: 이 파일의 메시는 **scene 에 직접** 붙는다(레벨 ROOT 밑이 아니다).
//   level.js 의 콜라이더 수집은 레벨 glb 의 자식만 훑으므로, 여기 판들은 어떤
//   경우에도 콜라이더가 되지 않는다. **바닥 그림자 판을 레벨 ROOT 밑으로 옮기지 말 것.**
//
// 롤백 둘:
//   · main.js 의 ITEMS_ON = false  -> 이 파일은 import 만 되고 스폰·업데이트·주머니가
//     통째로 안 돈다(메시도 안 만든다)
//   · 아래 DROP_3D = false          -> 3D 메시 대신 옛 2D 빌보드 판이 돌아온다
import * as THREE from './lib/three.module.js';

// ---------------------------------------------------------------------------
// 품목표
// ---------------------------------------------------------------------------
// ★cell = 아이콘 시트(tex/item_atlas.png)의 칸 번호. 한 줄에 다섯 칸(1280x256,
//   칸 하나 256px). ui.js 가 **같은 상수**를 읽어 CSS background-position 을 계산하므로,
//   칸 번호를 바꾸면 두 곳이 같이 움직인다.
// ★★시트는 이제 **아이템창 안에서만** 쓴다(3D 로 바뀐 뒤에도 창 안은 2D 아이콘이 표준이다).
//   DROP_3D=false 로 되돌리면 바닥 드랍도 이 시트를 도로 쓴다.
// ★반짝이 별은 시트에 없다. 가산합성 셰이더가 직접 그린다(칸을 낭비할 이유가 없다).
// ★tier 는 색이 아니라 뜻이다. 반짝 색·주머니 테 색·획득 줄 색이 전부 여기서 나온다.
export const ATLAS_URL = './tex/item_atlas.png';
export const ATLAS_COLS = 5;
export const ATLAS_ROWS = 1;

// ★★화폐는 **동전이 아니다**(오너 지시 2026-08-18). 이 게임이 선 자리는 오디세우스의
//   시대 = 미케네고, 그때는 주조 동전이 아직 없었다. 값을 세던 물건 둘을 그대로 쓴다.
//     · 청동 잉곳 = oxhide ingot. 네 귀가 뻗은 소가죽 꼴 청동판. 실루엣이 독특해서
//       바닥에 떨어져 있어도 한눈에 읽힌다(흔한 드랍)
//     · 황금 탈란톤 = 호메로스가 상금으로 세던 「황금 탈란톤」. 두툼한 금 덩이(고급 드랍)
export const ITEMS = [
  // id        이름            등급        칸  바닥빛 색
  { id: 'ingot', name: '청동 잉곳', tier: 'common', cell: 0, glow: [1.00, 0.70, 0.32] },
  { id: 'talanton', name: '황금 탈란톤', tier: 'fine', cell: 1, glow: [1.00, 0.84, 0.40] },
  { id: 'potion', name: '붉은 물약', tier: 'fine', cell: 2, glow: [1.00, 0.46, 0.36] },
  { id: 'tooth', name: '요괴의 이빨', tier: 'fine', cell: 3, glow: [0.94, 0.88, 0.72] },
  { id: 'shard', name: '달빛 파편', tier: 'rare', cell: 4, glow: [0.62, 0.90, 1.00] },
];
export const ITEM_BY_ID = {};
for (const it of ITEMS) ITEM_BY_ID[it.id] = it;

// 등급 이름. 주머니 툴팁이 그대로 읽는다.
export const TIER_NAME = { common: '흔함', fine: '보통', rare: '희귀' };

// 쓰는 물건. 지금은 물약 하나뿐이다(표시만 하는 나머지와 갈리는 유일한 줄).
export const USE_HEAL = 30;

// ── 드랍표 ──────────────────────────────────────────────────────────────────
// ★확률은 **독립 시행이 아니라 한 번의 굴림**이다. 0~1 난수 하나를 굴려 아래 표를
//   위에서부터 누적으로 훑는다. 그래서 한 마리가 두 개를 떨어뜨리는 일이 없고,
//   합계(일반 0.70 / 두목 0.96)가 곧 "무언가 떨어질 확률"이다.
// ★두목은 **드랍률과 희귀도를 같이** 올린다(오너 지시). 달빛 파편이 2% -> 10% 로
//   다섯 배가 되는 게 "두목을 먼저 베는 이유"다.
const DROP = [
  { id: 'ingot', p: 0.30, lead: 0.34 },
  { id: 'talanton', p: 0.16, lead: 0.20 },
  { id: 'potion', p: 0.14, lead: 0.18 },
  { id: 'tooth', p: 0.08, lead: 0.14 },
  { id: 'shard', p: 0.02, lead: 0.10 },
];

// ---------------------------------------------------------------------------
// 물리·연출 값 (전부 초·미터)
// ---------------------------------------------------------------------------
const MAX_DROPS = 48;         // 동시에 굴러다닐 수 있는 수. 넘으면 제일 오래된 것부터 지운다
const G = 13.0;               // 중력. 9.8 은 이 스케일에서 너무 느긋해서 "톡" 이 안 산다
const TOSS_VY = 3.5;          // 튀어오르는 처음 속도(약 0.47m 까지 오른다)
const TOSS_VY_JIT = 0.9;
const TOSS_VXZ = 1.5;         // 옆으로 흩어지는 속도. 여러 개가 한 자리에 겹치지 않게
const BOUNCE = 0.38;          // 바닥에 닿을 때 남는 세로 속도 비율
const BOUNCE_FRICT = 0.45;    // 튈 때마다 옆속도가 이만큼 남는다
const SETTLE_VY = 1.0;        // 이보다 느리게 닿으면 그 자리에 눕는다(무한 통통 방지)
const REST_Y = 0.30;          // 2D 판일 때 안착 높이(중심). 3D 는 품목마다 반높이로 정한다
const BOB_AMP = 0.055;        // 둥실. 진폭이 이보다 크면 물건이 떠다니는 유령이 된다
const BOB_HZ = 0.62;
const ICON_S = 0.62;          // 아이콘 판 한 변(m). 24m 카메라에서 약 34px
const SPIN_HZ = 0.11;         // 바닥에 앉은 물건이 도는 속도(회/초). 느려야 '진열'로 읽힌다
const TUMBLE = 3.4;           // 날아가는 동안 구르는 속도(rad/s). 착지하면 바로 멎는다
const LIFE = 60.0;            // 방치 수명
const BLINK_AT = 8.0;         // 남은 수명이 이보다 적으면 점멸한다
const MAGNET_R = 1.0;         // 이 안에 들어오면 빨려온다(오너 지시 1m)
const MAGNET_A = 26.0;        // 빨려오는 가속
const PICK_R = 0.42;          // 이 안이면 주머니로
const ARM_T = 0.30;           // 튀어나오자마자 줍히면 "떨어진 걸 봤다"가 사라진다. 그 유예
const SPARK_HZ = 0.9;         // 안착한 물건이 반짝이는 주기
const POP_SPARKS = 5;         // 주울 때 터지는 별 수
const POP_T = 0.42;
const MAX_PER_KIND = 20;      // 품목 하나가 동시에 설 수 있는 수(인스턴스 상한)

// ★★2D 판 -> 3D 메시 (20차 오너 지시 "3d로 해야할듯 ... 2d 는 안어울린다").
//   false 로 두면 처음에 만든 빌보드 판 경로가 그대로 돌아온다(시트·UV·알파 전부 살아 있다).
//   품목표·물리·자석·주머니는 두 경로가 **같은 코드**를 쓴다 - 갈리는 건 그리는 방법뿐이다.
const DROP_3D = true;

// ---------------------------------------------------------------------------
export function createItemSystem(opts) {
  const scene = opts.scene;
  const camera = opts.camera;
  const level = opts.level || null;          // groundY 를 위해. 없으면 평지로 본다
  const getPlayer = opts.getPlayer;          // () => THREE.Vector3 (발밑)
  const onPickup = opts.onPickup || (() => { });

  // 바닥 높이. level.js 가 아직 안 떴으면 0 으로 본다(feel.js 와 같은 규칙).
  function groundAt(x, z) {
    if (level && level.ready && level.ready()) return level.groundY(x, z);
    return 0.02;
  }

  // ── 주머니 ──
  // {id: 개수}. 순서는 ITEMS 순서로 고정한다(주운 순서로 두면 슬롯이 매번 춤춘다).
  const bag = Object.create(null);
  let picked = 0;                 // 이번 판에 주운 총 개수(검증 창구)
  let dropped = 0;                // 이번 판에 떨어진 총 개수

  // ── 드랍 목록 ──
  // 살아 있는 것만 앞에서부터 채운다(스왑 삭제). 매 프레임 도는 배열이라
  // 객체를 새로 만들지 않고 풀에서 꺼내 쓴다.
  const pool = [];
  for (let i = 0; i < MAX_DROPS; i++) {
    pool.push({ id: '', cell: 0, glow: [1, 1, 1], x: 0, y: 0, z: 0,
                vx: 0, vy: 0, vz: 0, gy: 0, t: 0, life: 0, rest: false,
                bounces: 0, phase: 0, sway: 0, magnet: false,
                rY: REST_Y, spin: 0, tumble: 0 });
  }
  let live = 0;

  // 주울 때 터지는 별. 드랍과 수명이 갈리므로 따로 둔다.
  const POPS = 24;
  const pops = [];
  for (let i = 0; i < POPS; i++) pops.push({ t: -1, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, c: [1, 1, 1] });
  let popHead = 0;

  // -------------------------------------------------------------------------
  // 그림 — 판 두 벌
  // -------------------------------------------------------------------------
  // ★자리를 정점 버퍼가 만든다. 경계구가 못 따라오므로 frustumCulled 를 끈다
  //   (enemy.js plateMesh 와 같은 규칙 — 안 끄면 통째로 컬링된다).
  function quadMesh(count, mat, extra, order) {
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
    m.frustumCulled = false;
    m.renderOrder = order;
    m.visible = false;
    scene.add(m);
    return m;
  }

  // ── 아이콘 시트 ──
  // ★★필터는 **Linear** 다. 1차 시트는 32px 블록 픽셀아트라 Nearest 였는데, 그 그림이
  //   오너에게 "마인크래프트 같다"로 기각됐다. 2차 시트는 곡선·그러데이션이 있는
  //   부드러운 셀셰이딩 일러스트(SVG 원본)라, Nearest 로 확대하면 매끈한 외곽선에
  //   계단이 서서 애써 만든 결이 도로 픽셀아트로 읽힌다. 확대·축소 둘 다 부드럽게.
  const tex = new THREE.TextureLoader().load(ATLAS_URL);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.magFilter = THREE.LinearFilter;
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.generateMipmaps = true;
  // ★밉맵 축소에서 옆 칸이 새어 들어오는 것을 막는다. 한 줄에 다섯 칸이라
  //   가장자리 텍셀이 이웃 칸과 맞닿아 있다(칸 사이 여백이 곧 아이콘의 투명 여백이라
  //   실제로는 여유가 있지만, 클램프를 안 걸면 맨 끝 칸에서 반대편이 비친다).
  tex.wrapS = THREE.ClampToEdgeWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.anisotropy = 4;

  const iconA = new Float32Array(MAX_DROPS * 4);        // 알파(점멸·페이드)
  // ★★side: DoubleSide 가 **꼭** 필요하다. 아래 writeBillboard/writeGround 는
  //   네 꼭짓점을 왼위 -> 오른위 -> 오른아래 -> 왼아래 순으로 적는데, 그 감김은
  //   화면에서 시계방향 = three.js 의 기본 앞면(반시계)의 **반대**다. 한 면만 그리면
  //   판이 통째로 뒷면 컬링에 걸려 **하나도 안 보인다**(첫 판에서 그렇게 나왔다.
  //   버퍼·씬 소속·시트 로드가 전부 정상인데 화면만 비어서 한참 걸렸다).
  //   꼭짓점 순서를 뒤집는 길도 있지만, 빌보드는 어차피 양면이 같은 그림이라 이쪽이 싸다.
  const iconMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: true, side: THREE.DoubleSide,
    uniforms: { uTex: { value: tex },
                uFogColor: { value: new THREE.Color(scene.fog ? scene.fog.color : 0x000000) },
                uFogNear: { value: scene.fog ? scene.fog.near : 1e9 },
                uFogFar: { value: scene.fog ? scene.fog.far : 1e9 } },
    vertexShader: `
      attribute float aA;
      varying vec2 vU; varying float vA; varying float vD;
      void main(){
        vU = uv; vA = aA;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vD = -mv.z;
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      uniform sampler2D uTex;
      uniform vec3 uFogColor; uniform float uFogNear; uniform float uFogFar;
      varying vec2 vU; varying float vA; varying float vD;
      void main(){
        vec4 t = texture2D(uTex, vU);
        float a = t.a * vA;
        if (a < 0.02) discard;
        // 안개. 몸(요괴·캐릭터)과 같은 규칙으로 멀어지면 배경색에 섞인다.
        float f = smoothstep(uFogNear, uFogFar, vD);
        gl_FragColor = vec4(mix(t.rgb, uFogColor, f), a);
      }`,
  });
  const iconMesh = quadMesh(MAX_DROPS, iconMat,
    { aA: { arr: iconA, n: 1 } }, 6);

  // ── 바닥빛 + 반짝이 ──
  // 한 벌에 두 모양을 담는다. aKind 0 = 바닥 원반 · 1 = 네 갈래 별.
  // ★가산합성이라 어두운 바닥에서 물건 자리가 멀리서도 보인다. 이게 "메이플에서
  //   저기 뭐 떨어졌다"를 읽게 하는 장치다. 알파합성으로 하면 바닥 무늬에 묻힌다.
  // ★칸 수 = 바닥빛(드랍당 1) + 반짝 한 점(드랍당 1) + 획득 팝. 셋을 다 세야 한다 -
  //   모자라면 별이 조용히 안 그려지는 게 아니라 **배열 밖에 쓴다**(무증상 버그다).
  const FX_N = MAX_DROPS * 2 + POPS;
  const fxKind = new Float32Array(FX_N * 4);
  const fxCol = new Float32Array(FX_N * 4 * 3);
  const fxA = new Float32Array(FX_N * 4);
  const fxMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: true, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    uniforms: {},
    vertexShader: `
      attribute float aKind; attribute vec3 aCol; attribute float aA;
      varying vec2 vU; varying float vK; varying vec3 vC; varying float vA;
      void main(){
        vU = uv; vK = aKind; vC = aCol; vA = aA;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: `
      varying vec2 vU; varying float vK; varying vec3 vC; varying float vA;
      void main(){
        vec2 p = vU * 2.0 - 1.0;
        float a;
        if (vK < 0.5) {
          // 바닥 원반. 가운데가 밝고 가장자리로 부드럽게 사라진다
          a = 1.0 - smoothstep(0.10, 1.0, length(p));
          a *= a;
        } else {
          // 네 갈래 별. 가로·세로로 뻗은 두 획을 곱이 아니라 합으로 겹친다
          float d = length(p);
          float core = 1.0 - smoothstep(0.0, 0.34, d);
          float ax = (1.0 - smoothstep(0.0, 0.055, abs(p.y))) * (1.0 - smoothstep(0.0, 1.0, abs(p.x)));
          float ay = (1.0 - smoothstep(0.0, 0.055, abs(p.x))) * (1.0 - smoothstep(0.0, 1.0, abs(p.y)));
          a = clamp(core + ax * 0.85 + ay * 0.85, 0.0, 1.0);
        }
        a *= vA;
        if (a < 0.01) discard;
        gl_FragColor = vec4(vC * a, a);
      }`,
  });
  const fxMesh = quadMesh(FX_N, fxMat,
    { aKind: { arr: fxKind, n: 1 }, aCol: { arr: fxCol, n: 3 }, aA: { arr: fxA, n: 1 } }, 5);

  // ── 바닥 그림자 ──
  // ★가산합성으로는 **어둡게 못 만든다**. 그림자는 알파합성 겹이라 판을 따로 둔다.
  //   물건이 땅에 붙어 있다는 감각은 이 타원 하나가 진다(가산 바닥빛은 "저기 뭐 있다"를,
  //   그림자는 "그게 땅 위에 있다"를 맡는다 - 둘은 다른 일이다).
  const shA = new Float32Array(MAX_DROPS * 4);
  const shMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: true, side: THREE.DoubleSide,
    uniforms: {},
    vertexShader: `
      attribute float aA;
      varying vec2 vU; varying float vA;
      void main(){
        vU = uv; vA = aA;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: `
      varying vec2 vU; varying float vA;
      void main(){
        float a = (1.0 - smoothstep(0.18, 1.0, length(vU * 2.0 - 1.0))) * vA;
        if (a < 0.01) discard;
        // enemy.js 의 가짜 그림자와 **같은 먹빛**이다(순검정은 바닥에서 구멍으로 읽힌다).
        gl_FragColor = vec4(0.0, 0.005, 0.02, a);
      }`,
  });
  const shMesh = quadMesh(MAX_DROPS, shMat, { aA: { arr: shA, n: 1 } }, 3);

  // -------------------------------------------------------------------------
  // 3D 드랍 (20차 오너 지시: "3d로 해야할듯 ... 2d 는 안어울린다")
  // -------------------------------------------------------------------------
  // ★★품목마다 InstancedMesh 한 벌이다. 같은 품목이 열 개 굴러도 드로우콜은 하나다.
  // ★재질은 캐릭터·요괴와 같은 **MeshToonMaterial + flatShading** 이다. 이 세계는
  //   저폴리 핸드페인티드라 매끈한 PBR 금속을 넣으면 그 하나만 다른 게임에서 온다.
  // ★★그리고 **이미시브를 반드시 섞는다.** 이 게임의 던전은 정점색 조명이라 빛이
  //   안 닿는 구석이 진짜로 캄캄하다 - 순수 반사 재질만 쓰면 거기 떨어진 물건이
  //   통째로 사라진다. 과하면 형광 스티커가 되므로 0.25~0.55 대역에서 절제한다.
  function toonMat(emissive, ei) {
    return new THREE.MeshToonMaterial({
      // ★색은 재질이 아니라 **정점**이 진다(아래 bakeShade). 재질은 흰색이다.
      color: 0xffffff,
      emissive: new THREE.Color(emissive),
      emissiveIntensity: ei,
      flatShading: true,
      vertexColors: true,
    });
  }

  // ── ★★명암을 정점에 굽는다 ──────────────────────────────────────────────
  // 이 게임의 지형·소품은 **정점색으로 그림을 그리는** 세계다(저폴리 핸드페인티드).
  // 처음엔 재질 색 하나에 툰 셰이딩만 맡겼는데, 던전의 빛이 약한 자리에서 물건이
  // **납작한 색면**으로 보였다(금덩이가 노란 동그라미, 잉곳이 갈색 네모). 씬 조명에
  // 기대는 대신 **면 방향과 높이를 정점색에 미리 구워** 두면 빛이 어떻든 형태가 남는다.
  //   · 면 방향(가짜 빛은 왼위에서)   -> 윗면이 밝고 옆면·아랫면이 어둡다
  //   · 높이                          -> 바닥에 가까울수록 한 단 더 어둡다(접지 그늘)
  // 이미 색 속성이 있는 지오메트리(물약의 유리·코르크)는 **그 색에 곱한다**.
  const _bakeL = new THREE.Vector3(0.42, 0.86, 0.30).normalize();
  function bakeShade(geo, baseHex) {
    const pos = geo.attributes.position;
    const nrm = geo.attributes.normal;
    const had = geo.attributes.color;
    const col = had ? had.array : new Float32Array(pos.count * 3);
    const base = new THREE.Color(baseHex);
    geo.computeBoundingBox();
    const y0 = geo.boundingBox.min.y;
    const dy = (geo.boundingBox.max.y - y0) || 1;
    for (let i = 0; i < pos.count; i++) {
      const d = nrm.getX(i) * _bakeL.x + nrm.getY(i) * _bakeL.y + nrm.getZ(i) * _bakeL.z;
      const t = (pos.getY(i) - y0) / dy;
      // 0.44 ~ 1.02. ★상한을 1 근처로 눌러 둔다 - 처음엔 1.16 까지 열어 뒀는데
      //   씬 조명과 이미시브가 그 위에 또 얹혀서 청동이 살구색, 금이 크림색이 됐다.
      const k = 0.44 + 0.40 * Math.max(0, d) + 0.18 * t;
      const r = had ? col[i * 3] : base.r;
      const g = had ? col[i * 3 + 1] : base.g;
      const b = had ? col[i * 3 + 2] : base.b;
      col[i * 3] = Math.min(1, r * k);
      col[i * 3 + 1] = Math.min(1, g * k);
      col[i * 3 + 2] = Math.min(1, b * k);
    }
    if (had) had.needsUpdate = true;
    else geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    return geo;
  }

  // 청동 소가죽 잉곳. 네 변이 안으로 휘고 네 귀가 뻗은 판 + 두께 + 베벨.
  // ★실루엣이 이 품목의 전부다. 곡선 분할을 3 으로 눌러 저폴리로 유지한다.
  function ingotGeo() {
    const H = 0.200, k = 0.42;
    const s = new THREE.Shape();
    s.moveTo(-H, -H);
    s.quadraticCurveTo(0, -H * k, H, -H);
    s.quadraticCurveTo(H * k, 0, H, H);
    s.quadraticCurveTo(0, H * k, -H, H);
    s.quadraticCurveTo(-H * k, 0, -H, -H);
    const g = new THREE.ExtrudeGeometry(s, {
      depth: 0.060, bevelEnabled: true, bevelThickness: 0.024,
      bevelSize: 0.024, bevelSegments: 1, curveSegments: 3,
    });
    g.rotateX(-Math.PI / 2);      // 눕힌다. 소가죽 잉곳은 서 있는 물건이 아니다
    g.center();
    return g;
  }

  // 황금 탈란톤. 두툼한 빵꼴 덩이(윗면이 볼록하고 옆이 두껍다).
  function talantonGeo() {
    const p = [
      new THREE.Vector2(0.000, -0.090),
      new THREE.Vector2(0.115, -0.100),
      new THREE.Vector2(0.190, -0.062),
      new THREE.Vector2(0.205, 0.014),
      new THREE.Vector2(0.170, 0.072),
      new THREE.Vector2(0.090, 0.102),
      new THREE.Vector2(0.000, 0.110),
    ];
    const g = new THREE.LatheGeometry(p, 10);
    g.center();
    return g;
  }

  // 붉은 물약. 한 덩이로 굽고 **정점색**으로 유리·목·코르크를 가른다
  // (InstancedMesh 는 재질이 한 벌이라, 두 색을 쓰려면 색이 지오메트리에 있어야 한다).
  function potionGeo() {
    const p = [
      new THREE.Vector2(0.000, 0.000),
      new THREE.Vector2(0.088, 0.005),
      new THREE.Vector2(0.124, 0.048),
      new THREE.Vector2(0.132, 0.116),
      new THREE.Vector2(0.099, 0.177),
      new THREE.Vector2(0.046, 0.210),
      new THREE.Vector2(0.039, 0.248),
      new THREE.Vector2(0.039, 0.268),
      new THREE.Vector2(0.056, 0.278),
      new THREE.Vector2(0.056, 0.324),
      new THREE.Vector2(0.000, 0.329),
    ];
    const g = new THREE.LatheGeometry(p, 9);
    const pos = g.attributes.position;
    const col = new Float32Array(pos.count * 3);
    const glass = new THREE.Color(0xc33a2e);
    const neck = new THREE.Color(0xa9c4cc);
    const cork = new THREE.Color(0xb1794b);
    for (let i = 0; i < pos.count; i++) {
      const y = pos.getY(i);
      const c = y > 0.214 ? cork : (y > 0.162 ? neck : glass);
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.center();
    return g;
  }

  // 요괴의 이빨. 여섯 모 뿔 하나를 살짝 눕힌다.
  function toothGeo() {
    const g = new THREE.ConeGeometry(0.098, 0.430, 6, 1);
    g.rotateZ(0.20);
    g.center();
    return g;
  }

  // 달빛 파편. 팔면체를 세로로 늘여 세운다(면이 크게 갈려야 결정으로 읽힌다).
  function shardGeo() {
    const g = new THREE.OctahedronGeometry(0.135, 0);
    g.scale(0.78, 1.55, 0.78);
    g.center();
    return g;
  }

  // 품목별 판. ★tilt 는 안착했을 때의 고정 기울기다 - 전부 반듯하게 서 있으면
  //   진열대처럼 보인다. 물약만 똑바로 세운다(누우면 쏟아진 병이다).
  // ★★이미시브는 **0.24~0.5** 다. 처음에 0.55~0.85 로 넣었더니 툰 셰이딩이 통째로
  //   씻겨서 물건이 **납작한 색면**으로 보였다(금덩이가 노란 동그라미가 됐다).
  //   어둠에서 안 사라질 만큼만 바닥을 깔고, 면을 가르는 일은 빛에 맡긴다.
  // ★★tilt 는 안착했을 때의 고정 기울기다. 납작한 물건(잉곳·탈란톤)은 이 각이 없으면
  //   윗면만 보여서 두께가 안 읽힌다 - 기울여야 베벨과 옆면이 함께 들어온다.
  const KIND_DEF = {
    ingot: { geo: () => bakeShade(ingotGeo(), 0xb4753c), mat: () => toonMat(0x3d2712, 0.26), tilt: 0.46 },
    talanton: { geo: () => bakeShade(talantonGeo(), 0xe8ab2b), mat: () => toonMat(0x4a3308, 0.30), tilt: 0.40 },
    potion: { geo: () => bakeShade(potionGeo(), 0xffffff), mat: () => toonMat(0x3a0e0a, 0.26), tilt: 0 },
    tooth: { geo: () => bakeShade(toothGeo(), 0xd6c5a2), mat: () => toonMat(0x2e2822, 0.22), tilt: 1.25 },
    shard: { geo: () => bakeShade(shardGeo(), 0x8ed9f0), mat: () => toonMat(0x2a6f96, 0.46), tilt: 0.16 },
  };
  const KINDS = Object.create(null);
  const KIND_LIST = [];
  if (DROP_3D) {
    for (const def of ITEMS) {
      const d = KIND_DEF[def.id];
      if (!d) continue;
      const geo = d.geo();
      geo.computeBoundingBox();
      const bb = geo.boundingBox;
      const mesh = new THREE.InstancedMesh(geo, d.mat(), MAX_PER_KIND);
      mesh.frustumCulled = false;   // 자리를 인스턴스 행렬이 만든다(경계구가 못 따라온다)
      mesh.castShadow = false;      // 가짜 그림자 타원을 따로 그린다(섀도맵 패스를 안 늘린다)
      mesh.receiveShadow = false;
      mesh.count = 0;
      mesh.visible = false;
      scene.add(mesh);
      const k = { id: def.id, mesh, tilt: d.tilt || 0,
                  // 바닥에 닿게 세울 높이 = 반높이 + 살짝. 품목마다 다르다
                  rest: (bb.max.y - bb.min.y) * 0.5 + 0.03,
                  n: 0 };
      KINDS[def.id] = k;
      KIND_LIST.push(k);
    }
  }
  const _m4 = new THREE.Matrix4();
  const _qYaw = new THREE.Quaternion();
  const _qTilt = new THREE.Quaternion();
  const _qOut = new THREE.Quaternion();
  const _vPos = new THREE.Vector3();
  const _vScale = new THREE.Vector3();
  const _axY = new THREE.Vector3(0, 1, 0);
  const _axTilt = new THREE.Vector3(0.88, 0, 0.47).normalize();

  // -------------------------------------------------------------------------
  // 정점 쓰기 도우미
  // -------------------------------------------------------------------------
  const _right = new THREE.Vector3();
  const _up = new THREE.Vector3();

  // 카메라를 향해 서는 판. 두 축은 카메라 행렬에서 뽑는다(매 프레임 한 번만).
  function camAxes() {
    const e = camera.matrixWorld.elements;
    _right.set(e[0], e[1], e[2]).normalize();
    _up.set(e[4], e[5], e[6]).normalize();
  }

  function writeBillboard(arr, i, x, y, z, half) {
    const o = i * 12;
    const rx = _right.x * half, ry = _right.y * half, rz = _right.z * half;
    const ux = _up.x * half, uy = _up.y * half, uz = _up.z * half;
    arr[o + 0] = x - rx + ux; arr[o + 1] = y - ry + uy; arr[o + 2] = z - rz + uz;
    arr[o + 3] = x + rx + ux; arr[o + 4] = y + ry + uy; arr[o + 5] = z + rz + uz;
    arr[o + 6] = x + rx - ux; arr[o + 7] = y + ry - uy; arr[o + 8] = z + rz - uz;
    arr[o + 9] = x - rx - ux; arr[o + 10] = y - ry - uy; arr[o + 11] = z - rz - uz;
  }

  // 바닥에 눕는 판(XZ 평면). 원반이 세로로 서면 벽처럼 보인다.
  function writeGround(arr, i, x, y, z, half) {
    const o = i * 12;
    arr[o + 0] = x - half; arr[o + 1] = y; arr[o + 2] = z - half;
    arr[o + 3] = x + half; arr[o + 4] = y; arr[o + 5] = z - half;
    arr[o + 6] = x + half; arr[o + 7] = y; arr[o + 8] = z + half;
    arr[o + 9] = x - half; arr[o + 10] = y; arr[o + 11] = z + half;
  }

  // 시트 칸 하나의 uv. 왼쪽 위가 0번이다.
  function writeCellUV(arr, i, cell) {
    const cw = 1 / ATLAS_COLS, ch = 1 / ATLAS_ROWS;
    const cx = (cell % ATLAS_COLS) * cw;
    const cy = 1 - Math.floor(cell / ATLAS_COLS) * ch;
    const o = i * 8;
    arr[o + 0] = cx; arr[o + 1] = cy;
    arr[o + 2] = cx + cw; arr[o + 3] = cy;
    arr[o + 4] = cx + cw; arr[o + 5] = cy - ch;
    arr[o + 6] = cx; arr[o + 7] = cy - ch;
  }

  function writeUnitUV(arr, i) {
    const o = i * 8;
    arr[o + 0] = 0; arr[o + 1] = 1;
    arr[o + 2] = 1; arr[o + 3] = 1;
    arr[o + 4] = 1; arr[o + 5] = 0;
    arr[o + 6] = 0; arr[o + 7] = 0;
  }

  function fill4(arr, i, v) { const o = i * 4; arr[o] = arr[o + 1] = arr[o + 2] = arr[o + 3] = v; }
  function fill4v3(arr, i, c) {
    const o = i * 12;
    for (let k = 0; k < 4; k++) { arr[o + k * 3] = c[0]; arr[o + k * 3 + 1] = c[1]; arr[o + k * 3 + 2] = c[2]; }
  }

  // -------------------------------------------------------------------------
  // 떨어뜨린다
  // -------------------------------------------------------------------------
  // 굴림 한 번. 아무것도 안 나오면 null.
  function roll(leader) {
    let r = Math.random();
    for (const d of DROP) {
      const p = leader ? d.lead : d.p;
      if (r < p) return d.id;
      r -= p;
    }
    return null;
  }

  // 요괴를 벤 자리에서 부른다(main.js onHit 의 kill 갈래).
  // x,y,z = 칼이 닿은 점. 거기서 튀어야 "이 한 대가 떨어뜨렸다"로 읽힌다.
  function spawnFromKill(x, y, z, leader) {
    const id = roll(!!leader);
    if (!id) return null;
    return spawn(id, x, y, z);
  }

  function spawn(id, x, y, z) {
    const def = ITEM_BY_ID[id];
    if (!def) return null;
    // 자리가 다 찼으면 제일 오래된 것을 밀어낸다(맨 앞이 제일 오래된 것이다).
    if (live >= MAX_DROPS) removeAt(0);
    const d = pool[live++];
    d.id = id; d.cell = def.cell; d.glow = def.glow;
    d.x = x; d.z = z;
    d.gy = groundAt(x, z);
    // ★튀어나오는 높이는 벤 자리 그대로가 아니다. 칼이 발밑을 스쳤으면 물건이
    //   바닥에서 솟는 그림이 되므로 최소 가슴께(0.55m)에서 시작한다.
    d.y = Math.max(y, d.gy + 0.55);
    const a = Math.random() * Math.PI * 2;
    const s = TOSS_VXZ * (0.55 + Math.random() * 0.75);
    d.vx = Math.cos(a) * s; d.vz = Math.sin(a) * s;
    d.vy = TOSS_VY + Math.random() * TOSS_VY_JIT;
    d.t = 0; d.life = LIFE; d.rest = false; d.bounces = 0;
    d.phase = Math.random() * 6.283;
    d.sway = 0.5 + Math.random() * 0.5;
    d.magnet = false;
    // ★안착 높이는 **품목마다 다르다**(3D 는 물건 크기가 제각각이라 한 값으로 못 쓴다).
    //   잉곳은 납작하게 눕고 물약은 서 있으니 바닥에 닿는 중심 높이가 갈린다.
    const K = KINDS[id];
    d.rY = K ? K.rest : REST_Y;
    // 날아가는 동안 구르는 축·각도. 착지하면 yaw 한 축만 남는다
    d.spin = Math.random() * 6.283;
    d.tumble = (Math.random() < 0.5 ? -1 : 1) * TUMBLE * (0.7 + Math.random() * 0.6);
    dropped++;
    return d;
  }

  function removeAt(i) {
    // ★스왑 삭제. 죽은 칸을 **버리지 않고** 맨 뒤와 자리를 바꾼다 - 풀에서 꺼내 쓰는
    //   구조라 객체를 잃으면 다음 스폰이 쓸 칸이 없어진다(splice 를 쓰면 안 되는 이유).
    //   순서에는 뜻이 없다(수명이 개체마다 따로 흐른다).
    const tmp = pool[i];
    pool[i] = pool[live - 1];
    pool[live - 1] = tmp;
    live--;
  }

  // -------------------------------------------------------------------------
  // 줍는다
  // -------------------------------------------------------------------------
  function addToBag(id, n) {
    bag[id] = (bag[id] || 0) + (n || 1);
    picked += (n || 1);
    return bag[id];
  }

  function popSparks(x, y, z, c) {
    for (let k = 0; k < POP_SPARKS; k++) {
      const p = pops[popHead];
      popHead = (popHead + 1) % POPS;
      const a = Math.random() * 6.283, u = Math.random() * 2 - 1;
      const s = 1.4 + Math.random() * 1.2;
      p.t = 0; p.x = x; p.y = y; p.z = z;
      p.vx = Math.cos(a) * s * 0.7; p.vz = Math.sin(a) * s * 0.7; p.vy = 1.2 + u * 0.8;
      p.c = c;
    }
  }

  // -------------------------------------------------------------------------
  // 매 프레임
  // -------------------------------------------------------------------------
  // dt = 게임시간(히트스톱·슬로모가 이미 곱해진 값). 떨어지는 물건도 세상과 같이 멎는다.
  function update(dt, paused) {
    const p = getPlayer();
    const iPos = iconMesh.geometry.attributes.position.array;
    const iUv = iconMesh.geometry.attributes.uv.array;
    const fPos = fxMesh.geometry.attributes.position.array;
    const fUv = fxMesh.geometry.attributes.uv.array;
    const sPos = shMesh.geometry.attributes.position.array;
    const sUv = shMesh.geometry.attributes.uv.array;
    camAxes();

    let n = 0;          // 이번 프레임에 그린 아이콘 판 수(2D 경로)
    let fn = 0;         // fx 판 수
    let sn = 0;         // 그림자 판 수
    for (const k of KIND_LIST) k.n = 0;

    for (let i = live - 1; i >= 0; i--) {
      const d = pool[i];
      if (!paused) {
        d.t += dt;
        d.life -= dt;
        if (d.life <= 0) { removeAt(i); continue; }

        if (d.magnet) {
          // ── 자석 ──
          // 플레이어 **가슴께**로 빨린다. 발밑으로 당기면 물건이 땅에 박히면서 사라진다.
          const tx = p.x, ty = groundAt(p.x, p.z) + 0.75, tz = p.z;
          const dx = tx - d.x, dy = ty - d.y, dz = tz - d.z;
          const dist = Math.hypot(dx, dy, dz) || 1e-4;
          const acc = MAGNET_A * dt;
          d.vx += (dx / dist) * acc; d.vy += (dy / dist) * acc; d.vz += (dz / dist) * acc;
          // 감쇠가 없으면 플레이어를 지나쳐 날아갔다 되돌아온다(궤도가 생긴다)
          const damp = Math.pow(0.02, dt);
          d.vx *= damp; d.vy *= damp; d.vz *= damp;
          d.x += d.vx * dt; d.y += d.vy * dt; d.z += d.vz * dt;
          if (dist < PICK_R) {
            addToBag(d.id, 1);
            popSparks(d.x, d.y, d.z, d.glow);
            onPickup(ITEM_BY_ID[d.id], bag[d.id]);
            removeAt(i);
            continue;
          }
        } else if (!d.rest) {
          // ── 포물선 + 바운스 ──
          d.vy -= G * dt;
          d.x += d.vx * dt; d.y += d.vy * dt; d.z += d.vz * dt;
          d.gy = groundAt(d.x, d.z);
          d.spin += d.tumble * dt;              // 날아가는 동안은 구른다
          const floor = d.gy + d.rY;
          if (d.y <= floor && d.vy < 0) {
            d.y = floor;
            d.bounces++;
            if (-d.vy < SETTLE_VY || d.bounces >= 2) {
              // 안착. 여기서부터 둥실 + 느린 회전이 시작이고 시계도 여기서 0 이다
              d.rest = true; d.vx = d.vy = d.vz = 0; d.t = 0;
            } else {
              d.vy = -d.vy * BOUNCE;
              d.vx *= BOUNCE_FRICT; d.vz *= BOUNCE_FRICT;
            }
          }
        } else {
          // 안착한 뒤에도 바닥 높이는 다시 본다(경사에서 뜨거나 묻히지 않게)
          d.gy = groundAt(d.x, d.z);
          // ★느리게 돈다. 금·청동은 도는 동안 광택이 면을 훑고 지나가는데
          //   그 스침 하나가 "값나가는 물건"을 만든다(디아블로가 쓰는 그 수다).
          d.spin += 6.283 * SPIN_HZ * dt;
        }

        // ── 자석 진입 판정 ──
        // ★튀는 도중에는 안 빨린다(ARM_T). 벤 자리에 서 있으면 물건이 나오자마자
        //   사라져서 "떨어졌다"를 아무도 못 본다.
        if (!d.magnet && d.rest && d.t > ARM_T) {
          const dx = p.x - d.x, dz = p.z - d.z;
          if (dx * dx + dz * dz < MAGNET_R * MAGNET_R) { d.magnet = true; d.vy = 1.0; }
        }
      }

      // ── 그린다 ──
      const bob = d.rest ? Math.sin(d.t * 6.283 * BOB_HZ + d.phase) * BOB_AMP : 0;
      const y = d.y + bob;
      // 점멸. 남은 수명이 8초 밑이면 깜빡이고 그 주기가 점점 빨라진다
      let a = 1;
      if (d.life < BLINK_AT) {
        const k = d.life / BLINK_AT;                 // 1 -> 0
        const hz = 2.2 + (1 - k) * 6.0;
        a = 0.20 + 0.80 * (0.5 + 0.5 * Math.sin(d.life * 6.283 * hz));
        a *= Math.min(1, k * 3.2 + 0.15);            // 마지막 순간에는 통째로 옅어진다
      }
      // 튀어나오는 첫 여섯 프레임은 작게 시작해 제 크기로 커진다(2D 였을 땐 페이드였다)
      const pop = (d.t < 0.10 && !d.rest) ? d.t / 0.10 : 1;
      if (!DROP_3D) a *= pop;

      if (DROP_3D) {
        // ★★불투명 메시라 **알파로 점멸을 못 한다**(반투명으로 바꾸면 정렬 문제가
        //   따라온다). 대신 깜빡이는 프레임에는 **아예 안 그린다** - 디아블로·메이플의
        //   사라지기 직전 점멸이 원래 그 하드 블링크다.
        const K = KINDS[d.id];
        if (K && K.n < MAX_PER_KIND && a > 0.55) {
          _qYaw.setFromAxisAngle(_axY, d.spin);
          if (d.rest && K.tilt) {
            _qTilt.setFromAxisAngle(_axTilt, K.tilt);
            _qOut.copy(_qYaw).multiply(_qTilt);
          } else if (!d.rest) {
            // 날아가는 동안은 비스듬한 축으로 구른다
            _qTilt.setFromAxisAngle(_axTilt, d.spin * 0.6);
            _qOut.copy(_qYaw).multiply(_qTilt);
          } else {
            _qOut.copy(_qYaw);
          }
          const s = 0.45 + 0.55 * pop;
          _vPos.set(d.x, y, d.z);
          _vScale.set(s, s, s);
          _m4.compose(_vPos, _qOut, _vScale);
          K.mesh.setMatrixAt(K.n++, _m4);
        }
      } else {
        writeBillboard(iPos, n, d.x, y, d.z, ICON_S * 0.5);
        writeCellUV(iUv, n, d.cell);
        fill4(iconA, n, a);
        n++;
      }

      // ── 바닥 그림자 ──
      // 날아가는 동안에도 깐다(그림자가 발밑에서 작아졌다 커지면 높이가 읽힌다).
      // 높이 올라갈수록 옅고 넓어진다.
      if (a > 0.55) {
        const h = Math.max(0, d.y - d.gy - d.rY);
        const k = 1 / (1 + h * 1.6);
        writeGround(sPos, sn, d.x, d.gy + 0.018, d.z, 0.26 + h * 0.11);
        writeUnitUV(sUv, sn);
        fill4(shA, sn, 0.62 * k);
        sn++;
      }

      // ★★가산 바닥빛(원반)은 3D 로 오면서 **뺐다.** 2D 판일 때는 그게 유일한 읽기
      //   장치였는데, 메시가 이미시브를 물고부터는 같은 자리에 따뜻한 원반을 겹치면
      //   **바로 밑에 깔린 그림자를 지워** 물건이 도로 공중에 뜬 것처럼 보였다.
      //   지금 그 일은 셋이 나눠 진다: 이미시브(어둠에서 안 사라짐) · 그림자(접지) ·
      //   반짝 한 점(값나가는 물건이라는 신호).
      if (d.rest && !d.magnet && a > 0.55) {
        // ★반짝 한 점(디아블로식). 물건 위에서 주기적으로 별 하나가 켜졌다 꺼진다.
        const tw = Math.sin(d.t * 2.1 + d.phase);
        if (tw > 0.72) {
          const k = (tw - 0.72) / 0.28;
          writeBillboard(fPos, fn, d.x + 0.10, y + d.rY * 1.1, d.z, 0.060 + 0.055 * k);
          writeUnitUV(fUv, fn);
          fill4(fxKind, fn, 1);
          fill4v3(fxCol, fn, d.glow);
          fill4(fxA, fn, k * 0.95);
          fn++;
        }
      }
    }

    // ── 주울 때 터지는 별 ──
    for (let k = 0; k < POPS; k++) {
      const s = pops[k];
      if (s.t < 0) continue;
      if (!paused) {
        s.t += dt;
        if (s.t > POP_T) { s.t = -1; continue; }
        s.vy -= G * 0.35 * dt;
        s.x += s.vx * dt; s.y += s.vy * dt; s.z += s.vz * dt;
      }
      const k2 = 1 - s.t / POP_T;
      writeBillboard(fPos, fn, s.x, s.y, s.z, 0.10 + 0.14 * (1 - k2));
      writeUnitUV(fUv, fn);
      fill4(fxKind, fn, 1);
      fill4v3(fxCol, fn, s.c);
      fill4(fxA, fn, k2 * k2 * 0.95);
      fn++;
    }

    // ── 버퍼 확정 ──
    // ★안 쓴 판은 그리지 않는다. drawRange 로 잘라야 정점 쓰레기가 화면에 안 뜬다.
    iconMesh.visible = n > 0;
    iconMesh.geometry.setDrawRange(0, n * 6);
    if (n > 0) {
      iconMesh.geometry.attributes.position.needsUpdate = true;
      iconMesh.geometry.attributes.uv.needsUpdate = true;
      iconMesh.geometry.attributes.aA.needsUpdate = true;
    }
    fxMesh.visible = fn > 0;
    fxMesh.geometry.setDrawRange(0, fn * 6);
    if (fn > 0) {
      fxMesh.geometry.attributes.position.needsUpdate = true;
      fxMesh.geometry.attributes.uv.needsUpdate = true;
      fxMesh.geometry.attributes.aKind.needsUpdate = true;
      fxMesh.geometry.attributes.aCol.needsUpdate = true;
      fxMesh.geometry.attributes.aA.needsUpdate = true;
    }
    shMesh.visible = sn > 0;
    shMesh.geometry.setDrawRange(0, sn * 6);
    if (sn > 0) {
      shMesh.geometry.attributes.position.needsUpdate = true;
      shMesh.geometry.attributes.uv.needsUpdate = true;
      shMesh.geometry.attributes.aA.needsUpdate = true;
    }
    // ★품목별 판. count 가 0 이면 아예 안 그린다 = 굴러다니는 게 없으면 드로우콜 0.
    for (const k of KIND_LIST) {
      k.mesh.count = k.n;
      k.mesh.visible = k.n > 0;
      if (k.n > 0) k.mesh.instanceMatrix.needsUpdate = true;
    }
  }

  // -------------------------------------------------------------------------
  // 쓴다 (물약)
  // -------------------------------------------------------------------------
  // 돌려주는 값: { ok, reason, healed }. ui.js 가 이걸 보고 안내 줄을 고른다.
  function use(id) {
    if (id !== 'potion') return { ok: false, reason: 'nouse' };
    if (!bag.potion) return { ok: false, reason: 'empty' };
    const heal = opts.heal;
    if (!heal) return { ok: false, reason: 'nohook' };
    const got = heal(USE_HEAL);
    // ★이미 만피면 **안 쓴다**(오너 지시 "이미 만피면 무시"). 개수가 줄면 손해다.
    if (!(got > 0)) return { ok: false, reason: 'full' };
    bag.potion--;
    if (bag.potion <= 0) delete bag.potion;
    return { ok: true, healed: got };
  }

  // -------------------------------------------------------------------------
  function reset() {
    live = 0;
    for (const k in bag) delete bag[k];
    for (const s of pops) s.t = -1;
    picked = 0; dropped = 0;
    iconMesh.visible = false; fxMesh.visible = false; shMesh.visible = false;
    iconMesh.geometry.setDrawRange(0, 0);
    fxMesh.geometry.setDrawRange(0, 0);
    shMesh.geometry.setDrawRange(0, 0);
    for (const k of KIND_LIST) { k.n = 0; k.mesh.count = 0; k.mesh.visible = false; }
  }

  // -------------------------------------------------------------------------
  const api = {
    update, spawn, spawnFromKill, use, reset,
    // ★그리는 판 자체를 내준다(읽기·조작 둘 다). "판은 서 있는데 화면에 없다"는
    //   버퍼 숫자만으로는 못 가른다 - 재질을 그 자리에서 갈아 보는 창구가 있어야 한다.
    meshes: { icon: iconMesh, fx: fxMesh, shadow: shMesh, kinds: KINDS, tex },
    // 주머니를 **복사해서** 준다. 바깥에서 직접 고치면 개수가 유령처럼 갈린다.
    get bag() { return Object.assign(Object.create(null), bag); },
    count(id) { return bag[id] || 0; },
    items: ITEMS,
    // 검증 창구(읽기 전용). "정말 떨어졌나 / 정말 주웠나"를 눈이 아니라 수로 본다.
    get state() {
      return { live, dropped, picked, bag: Object.assign({}, bag),
               drops: pool.slice(0, live).map(d => ({ id: d.id, rest: d.rest,
                 x: +d.x.toFixed(2), y: +d.y.toFixed(2), z: +d.z.toFixed(2),
                 life: +d.life.toFixed(1), magnet: d.magnet })),
               mode: DROP_3D ? '3d' : '2d',
               draws: (iconMesh.visible ? 1 : 0) + (fxMesh.visible ? 1 : 0)
                      + (shMesh.visible ? 1 : 0)
                      + KIND_LIST.reduce((a, k) => a + (k.mesh.visible ? 1 : 0), 0),
               // ★"판이 서 있는데 화면에 없다"를 눈이 아니라 버퍼로 가리는 창구.
               //   시트가 안 내려오면 tex.img 가 false 다(그때 2D 아이콘은 통째로 discard 된다).
               mesh: { icon: { vis: iconMesh.visible, range: iconMesh.geometry.drawRange.count },
                       fx: { vis: fxMesh.visible, range: fxMesh.geometry.drawRange.count },
                       shadow: { vis: shMesh.visible, range: shMesh.geometry.drawRange.count },
                       kinds: KIND_LIST.map(k => ({ id: k.id, n: k.n, vis: k.mesh.visible,
                                                    tris: k.mesh.geometry.index
                                                      ? k.mesh.geometry.index.count / 3
                                                      : k.mesh.geometry.attributes.position.count / 3,
                                                    rest: +k.rest.toFixed(3) })),
                       tex: { img: !!tex.image, w: tex.image ? tex.image.width : 0,
                              url: ATLAS_URL } },
               table: DROP.map(d => ({ id: d.id, p: d.p, lead: d.lead })),
               sum: +DROP.reduce((a, d) => a + d.p, 0).toFixed(2),
               sumLead: +DROP.reduce((a, d) => a + d.lead, 0).toFixed(2) };
    },
  };
  return api;
}
