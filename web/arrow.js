// 화살 (21차. 오너 지시 "궁수 활 쏘는거 없으면 만들어줘")
//
// 이 파일이 지는 일은 넷이다.
//   ① **난다**    시위를 떠난 자리에서 포물선으로 날아간다
//   ② **맞춘다**  요괴·보스에게 닿으면 그 한 발이 사라진다
//   ③ **박힌다**  벽에 걸리거나 땅에 닿거나 수명이 다하면 사라진다
//   ④ **그린다**  화살 한 벌(InstancedMesh) + 지나간 자국 한 벌. 드로우콜 둘이 전부다
//
// ★왜 별 파일인가: items.js 헤더와 같은 이유다. main.js 는 이미 5,600줄이고, 여기 값들
//   (속도·중력·자국 길이)은 0.05초 단위의 감각이라 **혼자 놓고 만져야** 맞는 값이 나온다.
//
// ★★items.js 와 갈리는 자리 하나: **바운스가 없다.**
//   떨어진 물건은 톡 튀어야 "떨어졌다"가 읽히지만, 화살은 맞거나 박히거나 사라지거나
//   셋뿐이다. 튀는 화살은 화살이 아니라 공이다.
//
// ★★판정 알고리즘을 여기서 새로 짜지 않았다. enemy.js 의 doHits 가 이미
//   **선분 대 캡슐 스윕**이라(직전 선분 → 이번 선분 사이를 쪼개 훑는다), 화살의
//   (직전 위치 → 현재 위치)를 그대로 넘기면 그게 곧 화살의 판정이다. 그 창구가
//   enemy.js hitSegment / boss.js hitSegment 이고, 정본 주석은 그 두 자리에 있다.
//
// 롤백은 한 줄이다: **main.js 의 ARROW_ON = false**.
//   그러면 이 파일은 import 만 되고 시스템이 아예 안 만들어진다(메시도 안 생긴다).
//   ★스위치를 여기 두지 않은 이유: main.js 가 발사 타이밍·조준 반경·캐릭터 표까지
//     쥐고 있어서, 두 곳에 두면 반드시 어긋난다(이 레포가 반복해서 배운 것이다).
import * as THREE from './lib/three.module.js';

// ---------------------------------------------------------------------------
// 날아가는 값 (전부 초·미터)
// ---------------------------------------------------------------------------
// ★SPEED 30 의 근거는 "빨라 보이게"가 아니라 **화면에서 읽히는가**다.
//   이 게임 카메라는 24m 거리·640px 기준으로 월드 1m ≈ 43px 이다. 60fps 에서
//   30m/s 면 한 프레임에 0.50m = **약 21px** 이 건너뛴다. 40 이상으로 올리면
//   프레임마다 28px 이 순간이동해서 화살이 아니라 점멸하는 점으로 보인다
//   (그래서 아래 자국(TRAIL)이 옵션이 아니라 필수다 - 프레임 사이를 그 판이 잇는다).
//   20 밑으로 내리면 5m 거리에서도 0.25초가 걸려 "쏘고 기다리는" 그림이 된다.
const SPEED = 30.0;
// 중력. 지형 중력(18.0)보다 훨씬 약하다. 진짜 중력을 먹이면 12m 표적까지 0.4초 동안
// 1.44m 가 떨어져서 조준이 곡예가 된다. 4.0 이면 같은 거리에서 0.32m 만 처지는데,
// 그게 "화살이 살짝 처진다"가 눈에 보이면서 판정을 안 흔드는 대역이다.
// ★자동 조준으로 쏠 때는 이 처짐을 **미리 계산해서 위로 올려 쏜다**(아래 fireAt 참고).
const G = 4.0;
const LIFE = 2.4;             // 수명(초). 30m/s x 2.4 = 72m. 맵 끝까지는 못 간다(맵이 더 넓다)
const RANGE = 26.0;           // 이 거리를 넘으면 사라진다. 수명보다 이쪽이 먼저 걸린다
const MAX_ARROWS = 16;        // 동시에 날 수 있는 수. 넘으면 제일 오래된 것부터 지운다
// ★★관통 상한. 0 = 첫 명중에 소멸(기본). 1 이면 두 마리를 뚫고 세 마리째에 멎는다.
//   기본을 0 으로 둔 이유: 지금 잡몹이 한 종이고 무리가 3~5마리라, 관통을 열면
//   한 발이 무리를 통째로 지우는 판이 나온다. 그건 활이 아니라 레일건이다.
const PIERCE = 0;
const LEN = 0.66;             // 화살 전체 길이(m). 판정 선분의 길이이기도 하다
const R_WALL = 0.06;          // 벽 판정 반경. 화살대 굵기(0.010)보다 넉넉히 준다
const ARM_T = 0.02;           // 이 시간 안에는 판정을 안 연다(쏜 자리에 겹친 놈을 즉사시키지 않게)

// ── 지나간 자국 ──
// ★"이펙트"가 아니라 **화살의 일부**다. 한 프레임에 21px 을 건너뛰는 물건은 자국이
//   없으면 사람 눈에 연속으로 안 보인다(위 SPEED 주석). 그래서 길이를 취향이 아니라
//   프레임 이동거리에서 정한다: 0.50m 를 확실히 덮는 0.9m.
// ★조준선·사거리 표시 같은 **화면 표시물이 아니다.** 이 게임은 그런 것을 차례로
//   제거해 왔다(공격 쐐기 → 백색 번쩍 → 타수 → 기술명 → 느낌표). 자국은 날아가는
//   물건에 붙어 있고 0.9m 뒤에서 끝난다.
const TRAIL_ON = true;        // 롤백용. false 면 자국 판이 통째로 안 그려진다
const TRAIL_LEN = 0.90;
const TRAIL_W = 0.055;        // 반폭(m). 24m 카메라에서 약 4.7px
const TRAIL_RGB = [0.62, 0.74, 0.90];   // 차가운 흰빛. 칼 이펙트(시안)와 안 겹치는 자리

// ---------------------------------------------------------------------------
export function createArrowSystem(opts) {
  const scene = opts.scene;
  const camera = opts.camera;
  const level = opts.level || null;
  // ★판정 창구는 **화살표로 받는다.** main.js 에서 enemies/boss 는 이 아래에서
  //   const 로 선언되므로(TDZ), 참조를 직접 받으면 로드 순서에 묶인다.
  //   items.js 의 heal 창구가 같은 규약이다.
  const hitEnemies = opts.hitEnemies || (() => 0);
  const hitBoss = opts.hitBoss || (() => false);
  // 발사·명중 순간에 main.js 가 끼워 넣을 것(소리·이펙트 방향). 없으면 조용히 넘어간다.
  const onFire = opts.onFire || (() => { });
  const beforeHit = opts.beforeHit || (() => { });

  function groundAt(x, z) {
    if (level && level.ready && level.ready()) return level.groundY(x, z);
    return 0.02;
  }
  function wallAt(x, z) {
    if (level && level.ready && level.ready() && level.blocked) return level.blocked(x, z, R_WALL);
    return false;
  }

  // -------------------------------------------------------------------------
  // 풀
  // -------------------------------------------------------------------------
  // ★매 프레임 도는 배열이라 객체를 새로 만들지 않는다(items.js 와 같은 규칙).
  //   id 는 **음수로 내려간다** - enemy.js/boss.js 의 중복 명중 방지 번호가 칼의
  //   스윙 번호(0 부터 증가)와 같은 통을 쓰기 때문이다. 음수면 절대 안 겹친다.
  const pool = [];
  for (let i = 0; i < MAX_ARROWS; i++) {
    pool.push({ id: -1, x: 0, y: 0, z: 0, px: 0, py: 0, pz: 0,
                vx: 0, vy: 0, vz: 0, t: 0, gone: 0, sx: 0, sy: 0, sz: 0 });
  }
  let live = 0;
  // ★★-1 부터 시작하면 **첫 화살이 아무도 못 맞춘다.** enemy.js 의 요괴는
  //   `lastSwing: -1` 로 태어나고(= "아직 아무 스윙에도 안 맞았다"의 뜻), boss.js 도
  //   `let lastSwing = -1` 이다. 그 초깃값과 번호가 같으면 doHits 의
  //   `e.lastSwing === swingId` 가 참이 되어 **전원이 건너뛰어진다.**
  //   실측으로 밟았다: 첫 발이 요괴 몸 한가운데(중심에서 0.15m)를 지나갔는데 체력이
  //   한 톨도 안 깎이고 땅에 박혔다. **-2 부터 시작한다.**
  let nextId = -2;                 // 다음 화살의 신원(음수로 내려간다)
  // 검증 창구 카운터. "맞는 것 같다"가 아니라 수로 본다.
  const stat = { fired: 0, hitEnemy: 0, hitBoss: 0, wall: 0, ground: 0, expired: 0,
                 lastFlightMs: -1, lastDist: -1 };

  function removeAt(i) {
    const tmp = pool[i]; pool[i] = pool[live - 1]; pool[live - 1] = tmp;
    live--;
  }

  // -------------------------------------------------------------------------
  // 그림 ① — 화살 한 자루
  // -------------------------------------------------------------------------
  // ★저폴리 절차 생성이다(삼각형 **26개**. state.tris 로 실측한 값). 오너 화풍은 저폴리 + 핸드페인티드라
  //   매끈한 PBR 금속을 넣으면 그 하나만 다른 게임에서 온다.
  // ★★기준 축은 **+Z** 다. 인스턴스 회전을 setFromUnitVectors(+Z, 날아가는 방향)
  //   한 줄로 끝내려고 그렇게 뒀다(오일러로 풀면 위아래가 뒤집히는 각이 반드시 나온다).
  function mergeParts(parts) {
    let total = 0;
    const gs = parts.map(p => {
      const g = p.geo.index ? p.geo.toNonIndexed() : p.geo;
      total += g.attributes.position.count;
      return g;
    });
    const pos = new Float32Array(total * 3);
    const nrm = new Float32Array(total * 3);
    const col = new Float32Array(total * 3);
    let o = 0;
    for (let i = 0; i < gs.length; i++) {
      const g = gs[i], n = g.attributes.position.count;
      pos.set(g.attributes.position.array, o * 3);
      nrm.set(g.attributes.normal.array, o * 3);
      const c = new THREE.Color(parts[i].color);
      for (let k = 0; k < n; k++) {
        col[(o + k) * 3] = c.r; col[(o + k) * 3 + 1] = c.g; col[(o + k) * 3 + 2] = c.b;
      }
      o += n;
    }
    const out = new THREE.BufferGeometry();
    out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    out.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
    out.setAttribute('color', new THREE.BufferAttribute(col, 3));
    return out;
  }

  // ★items.js 의 bakeShade 와 같은 처방이다(그 파일의 긴 주석이 정본).
  //   던전은 정점색 조명이라 빛이 안 닿는 구석이 진짜로 캄캄하다 - 면 방향을 정점색에
  //   미리 구워 두면 빛이 어떻든 화살대와 촉이 갈린다. 여기서는 화살이 늘 도니까
  //   높이 항(items.js 의 접지 그늘)은 뺐다 - 돌면 그 그림자가 같이 돌아서 깜빡인다.
  const _bakeL = new THREE.Vector3(0.42, 0.86, 0.30).normalize();
  function bakeShade(geo) {
    const nrm = geo.attributes.normal, col = geo.attributes.color;
    for (let i = 0; i < nrm.count; i++) {
      const d = nrm.getX(i) * _bakeL.x + nrm.getY(i) * _bakeL.y + nrm.getZ(i) * _bakeL.z;
      const k = 0.52 + 0.44 * Math.max(0, d);
      col.setXYZ(i, Math.min(1, col.getX(i) * k), Math.min(1, col.getY(i) * k),
                 Math.min(1, col.getZ(i) * k));
    }
    col.needsUpdate = true;
    return geo;
  }

  function arrowGeo() {
    // 화살대. 5모 기둥이면 실루엣은 원기둥인데 삼각형이 10개다.
    const shaft = new THREE.CylinderGeometry(0.010, 0.010, LEN * 0.80, 5, 1, true);
    shaft.rotateX(Math.PI / 2);                       // +Y -> +Z
    shaft.translate(0, 0, LEN * 0.08);
    // 촉. 네모뿔이라 각이 서고, 그 각이 저폴리 핸드페인티드의 결이다.
    const head = new THREE.ConeGeometry(0.028, 0.11, 4, 1);
    head.rotateX(Math.PI / 2);                        // 꼭짓점이 +Z 를 본다
    head.rotateZ(Math.PI / 4);                        // 마름모가 아니라 반듯한 네모로 서게
    head.translate(0, 0, LEN * 0.48 - 0.055 + 0.11 / 2);
    // 깃 둘. 얇은 판이라 **양면 재질이 필수**다(items.js 20차 함정: 뒷면 컬링).
    const finA = new THREE.PlaneGeometry(0.15, 0.075);
    finA.rotateY(Math.PI / 2);                        // 긴 축을 Z 로, 판이 ZY 평면에
    finA.translate(0, 0, -LEN * 0.34);
    const finB = new THREE.PlaneGeometry(0.15, 0.075);
    finB.rotateY(Math.PI / 2);
    finB.rotateZ(Math.PI / 2);                        // 두 번째 깃은 90도 돌려 십자로
    finB.translate(0, 0, -LEN * 0.34);
    return bakeShade(mergeParts([
      { geo: shaft, color: 0x9a6f45 },   // 나무
      { geo: head, color: 0xc4cad3 },    // 무쇠 촉
      { geo: finA, color: 0xe6dcc6 },    // 깃
      { geo: finB, color: 0xd2c4a6 },
    ]));
  }

  const arrowMesh = new THREE.InstancedMesh(
    arrowGeo(),
    new THREE.MeshToonMaterial({
      color: 0xffffff,          // 색은 재질이 아니라 정점이 진다(위 bakeShade)
      emissive: new THREE.Color(0x2b2b30),
      emissiveIntensity: 0.38,  // 어두운 던전에서 안 사라질 만큼만. 넘기면 형광 막대가 된다
      flatShading: true,
      vertexColors: true,
      side: THREE.DoubleSide,   // ★깃(판 둘) 때문에 반드시 필요하다
    }),
    MAX_ARROWS);
  arrowMesh.frustumCulled = false;   // 자리를 인스턴스 행렬이 만든다(경계구가 못 따라온다)
  arrowMesh.castShadow = false;
  arrowMesh.receiveShadow = false;
  arrowMesh.count = 0;
  arrowMesh.visible = false;
  scene.add(arrowMesh);

  // -------------------------------------------------------------------------
  // 그림 ② — 지나간 자국
  // -------------------------------------------------------------------------
  // 화살마다 판 한 장. 화살 뒤 TRAIL_LEN 만큼 늘어나고 뒤로 갈수록 옅어진다.
  // ★가산 합성이다. 알파합성으로 하면 밝은 초원에서 회색 막대가 된다.
  // ★items.js quadMesh 와 같은 규칙: 자리를 정점 버퍼가 만드니 frustumCulled 를 끈다.
  const trA = new Float32Array(MAX_ARROWS * 4);
  const trGeo = new THREE.BufferGeometry();
  {
    const pos = new Float32Array(MAX_ARROWS * 4 * 3);
    const uv = new Float32Array(MAX_ARROWS * 4 * 2);
    const idx = [];
    for (let i = 0; i < MAX_ARROWS; i++) {
      const o = i * 4;
      idx.push(o, o + 1, o + 2, o, o + 2, o + 3);
      // u 0 = 꼬리(사라지는 쪽) · 1 = 화살 쪽
      uv[o * 2 + 0] = 0; uv[o * 2 + 1] = 0;
      uv[o * 2 + 2] = 1; uv[o * 2 + 3] = 0;
      uv[o * 2 + 4] = 1; uv[o * 2 + 5] = 1;
      uv[o * 2 + 6] = 0; uv[o * 2 + 7] = 1;
    }
    trGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3).setUsage(THREE.DynamicDrawUsage));
    trGeo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    trGeo.setAttribute('aA', new THREE.BufferAttribute(trA, 1).setUsage(THREE.DynamicDrawUsage));
    trGeo.setIndex(idx);
  }
  const trMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: true, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    uniforms: { uCol: { value: new THREE.Vector3(TRAIL_RGB[0], TRAIL_RGB[1], TRAIL_RGB[2]) } },
    vertexShader: `
      attribute float aA;
      varying vec2 vU; varying float vA;
      void main(){
        vU = uv; vA = aA;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: `
      uniform vec3 uCol;
      varying vec2 vU; varying float vA;
      void main(){
        // 세로(v)로는 가운데가 밝고, 가로(u)로는 화살 쪽이 밝다.
        float a = (1.0 - smoothstep(0.0, 1.0, abs(vU.y * 2.0 - 1.0)));
        a *= vU.x * vU.x;
        a *= vA;
        if (a < 0.01) discard;
        gl_FragColor = vec4(uCol * a, a);
      }`,
  });
  const trMesh = new THREE.Mesh(trGeo, trMat);
  trMesh.frustumCulled = false;
  trMesh.renderOrder = 5;
  trMesh.visible = false;
  scene.add(trMesh);

  // -------------------------------------------------------------------------
  // 쏜다
  // -------------------------------------------------------------------------
  const _dir = new THREE.Vector3();
  const _hitA = new THREE.Vector3(), _hitB = new THREE.Vector3();
  const _prevA = new THREE.Vector3(), _prevB = new THREE.Vector3();
  const _q = new THREE.Quaternion();
  const _mZ = new THREE.Vector3(0, 0, 1);
  const _vP = new THREE.Vector3(), _vS = new THREE.Vector3(1, 1, 1);
  const _m4 = new THREE.Matrix4();
  const _camN = new THREE.Vector3(), _segD = new THREE.Vector3(), _side = new THREE.Vector3();

  // 방향을 그대로 받아 쏜다(자동 조준에 아무도 안 걸렸을 때).
  function fireDir(fx, fy, fz, dx, dy, dz) {
    _dir.set(dx, dy, dz);
    if (_dir.lengthSq() < 1e-9) return null;
    _dir.normalize();
    return push(fx, fy, fz, _dir.x, _dir.y, _dir.z);
  }

  // 표적 한 점을 겨눠 쏜다. **중력 처짐을 미리 되돌려서** 쏜다.
  // ★이게 자동 조준의 실체다: 방향을 표적 쪽으로 돌리는 것만으로는 안 맞는다
  //   (날아가는 동안 G x t^2 / 2 만큼 처지니까). 비행시간을 거리/속도로 어림잡고
  //   그만큼 위를 겨눈다. 어림이라 아주 먼 표적에서는 조금 어긋나지만, 그건
  //   **헛방의 자유**로 남겨 두는 게 맞다(맞히는 것은 근거리 자동, 멀면 실력).
  function fireAt(fx, fy, fz, tx, ty, tz) {
    const dx = tx - fx, dz = tz - fz;
    const flat = Math.hypot(dx, dz);
    const tof = Math.max(0.02, flat / SPEED);
    const dy = (ty + 0.5 * G * tof * tof) - fy;
    return fireDir(fx, fy, fz, dx, dy, dz);
  }

  function push(fx, fy, fz, dx, dy, dz) {
    if (live >= MAX_ARROWS) removeAt(0);     // 제일 오래된 것부터 버린다
    const a = pool[live++];
    a.id = nextId--;
    a.x = a.px = fx; a.y = a.py = fy; a.z = a.pz = fz;
    a.sx = fx; a.sy = fy; a.sz = fz;
    a.vx = dx * SPEED; a.vy = dy * SPEED; a.vz = dz * SPEED;
    a.t = 0; a.gone = 0;
    stat.fired++;
    onFire(a);
    return a;
  }

  // -------------------------------------------------------------------------
  // 매 프레임
  // -------------------------------------------------------------------------
  // ★dt 는 **게임시간**이다(히트스톱·슬로모가 이미 곱해져 있다). 세상이 멎는 그
  //   70~112ms 동안 화살만 혼자 날아가면 명중의 정지가 통째로 무너진다.
  function update(dt, paused) {
    const tPos = trGeo.attributes.position.array;
    let tn = 0;
    let an = 0;

    for (let i = live - 1; i >= 0; i--) {
      const a = pool[i];
      if (!paused) {
        a.px = a.x; a.py = a.y; a.pz = a.z;
        a.vy -= G * dt;
        a.x += a.vx * dt; a.y += a.vy * dt; a.z += a.vz * dt;
        a.t += dt;
        a.gone = Math.hypot(a.x - a.sx, a.y - a.sy, a.z - a.sz);

        // ── 판정 ──
        // 선분 둘을 만든다: 이번 프레임의 (오늬 → 촉)과 직전 프레임의 같은 것.
        // enemy.js 가 그 둘 사이를 쪼개 훑으므로, 한 프레임에 0.5m 를 건너뛰어도
        // 요괴를 뚫고 지나가지 않는다(30m/s 에서 프레임 이동거리 0.50m < 화살 0.66m).
        _dir.set(a.vx, a.vy, a.vz);
        const sp = _dir.length() || 1;
        _dir.multiplyScalar(1 / sp);
        _hitB.set(a.x, a.y, a.z);
        _hitA.copy(_hitB).addScaledVector(_dir, -LEN);
        _prevB.set(a.px, a.py, a.pz);
        _prevA.copy(_prevB).addScaledVector(_dir, -LEN);

        let done = false;
        if (a.t > ARM_T) {
          // main.js 가 이 한 줄로 명중 연출의 방향(swingDir)을 화살 진행 방향에 맞춘다.
          beforeHit(a, _dir);
          // 잡몹 먼저, 그다음 보스. 둘 다 **같은 화살 id** 를 스윙 번호로 받으므로
          // 한 발이 같은 놈을 두 번 때리는 일이 없다.
          const n = hitEnemies(_hitA, _hitB, { prevA: _prevA, prevB: _prevB,
                                               swing: a.id, kind: 'Arrow', cap: PIERCE + 1 });
          if (n > 0) { stat.hitEnemy += n; done = true; }
          if (!done && hitBoss(_hitA, _hitB, { prevA: _prevA, prevB: _prevB, swing: a.id })) {
            stat.hitBoss++; done = true;
          }
          if (done) {
            stat.lastFlightMs = +(a.t * 1000).toFixed(1);
            stat.lastDist = +a.gone.toFixed(2);
          }
        }
        // ── 사라지는 세 갈래 ──
        if (!done && a.y <= groundAt(a.x, a.z) + 0.02) { stat.ground++; done = true; }
        if (!done && wallAt(a.x, a.z)) { stat.wall++; done = true; }
        if (!done && (a.t >= LIFE || a.gone >= RANGE)) { stat.expired++; done = true; }
        if (done) { removeAt(i); continue; }
      }

      // ── 그린다 ──
      _dir.set(a.vx, a.vy, a.vz);
      if (_dir.lengthSq() > 1e-9) _dir.normalize(); else _dir.set(0, 0, 1);
      _q.setFromUnitVectors(_mZ, _dir);
      _vP.set(a.x, a.y, a.z).addScaledVector(_dir, -LEN * 0.5);   // 원점이 화살 가운데다
      _m4.compose(_vP, _q, _vS);
      arrowMesh.setMatrixAt(an++, _m4);

      if (TRAIL_ON) {
        // 자국 판 한 장. 카메라를 향하도록 옆 방향을 그때그때 만든다.
        // (빌보드가 아니라 **선분에 붙은 리본**이라 화살 방향은 그대로 유지된다)
        _segD.copy(_dir);
        _camN.set(a.x - camera.position.x, a.y - camera.position.y, a.z - camera.position.z);
        _side.crossVectors(_segD, _camN);
        if (_side.lengthSq() < 1e-8) _side.set(1, 0, 0); else _side.normalize();
        _side.multiplyScalar(TRAIL_W);
        // 꼬리(u=0)는 화살 뒤 TRAIL_LEN, 머리(u=1)는 화살 자리
        const hx = a.x - _dir.x * LEN * 0.55, hy = a.y - _dir.y * LEN * 0.55,
              hz = a.z - _dir.z * LEN * 0.55;
        const tx = hx - _dir.x * TRAIL_LEN, ty = hy - _dir.y * TRAIL_LEN,
              tz = hz - _dir.z * TRAIL_LEN;
        const o = tn * 12;
        tPos[o + 0] = tx - _side.x; tPos[o + 1] = ty - _side.y; tPos[o + 2] = tz - _side.z;
        tPos[o + 3] = hx - _side.x; tPos[o + 4] = hy - _side.y; tPos[o + 5] = hz - _side.z;
        tPos[o + 6] = hx + _side.x; tPos[o + 7] = hy + _side.y; tPos[o + 8] = hz + _side.z;
        tPos[o + 9] = tx + _side.x; tPos[o + 10] = ty + _side.y; tPos[o + 11] = tz + _side.z;
        // 갓 떠난 화살은 자국이 짧아야 한다(0.06초에 걸쳐 자란다)
        const k = Math.min(1, a.t / 0.06) * 0.85;
        trA[tn * 4] = trA[tn * 4 + 1] = trA[tn * 4 + 2] = trA[tn * 4 + 3] = k;
        tn++;
      }
    }

    arrowMesh.count = an;
    arrowMesh.visible = an > 0;
    if (an > 0) arrowMesh.instanceMatrix.needsUpdate = true;
    trMesh.visible = tn > 0;
    trGeo.setDrawRange(0, tn * 6);
    if (tn > 0) {
      trGeo.attributes.position.needsUpdate = true;
      trGeo.attributes.aA.needsUpdate = true;
    }
  }

  function reset() {
    live = 0;
    arrowMesh.count = 0; arrowMesh.visible = false;
    trMesh.visible = false; trGeo.setDrawRange(0, 0);
  }

  // -------------------------------------------------------------------------
  return {
    update, fireDir, fireAt, reset,
    speed: SPEED, grav: G, len: LEN, pierce: PIERCE,
    get live() { return live; },
    // 검증 창구(읽기 전용). "맞는 것 같다"가 아니라 수로 본다.
    get state() {
      return {
        live, fired: stat.fired, hitEnemy: stat.hitEnemy, hitBoss: stat.hitBoss,
        wall: stat.wall, ground: stat.ground, expired: stat.expired,
        lastFlightMs: stat.lastFlightMs, lastDist: stat.lastDist,
        speed: SPEED, grav: G, pierce: PIERCE,
        draws: (arrowMesh.visible ? 1 : 0) + (trMesh.visible ? 1 : 0),
        tris: arrowMesh.geometry.attributes.position.count / 3,
        arrows: pool.slice(0, live).map(a => ({
          id: a.id, t: +a.t.toFixed(3), gone: +a.gone.toFixed(2),
          x: +a.x.toFixed(2), y: +a.y.toFixed(2), z: +a.z.toFixed(2),
          v: +Math.hypot(a.vx, a.vy, a.vz).toFixed(1),
        })),
      };
    },
  };
}
