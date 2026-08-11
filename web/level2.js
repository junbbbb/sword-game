// ---------------------------------------------------------------------------
// web/level2.js - 던전 1층의 "층 진행" (보스 없는 판)
//
// boss.js 와 **같은 자리에 꽂히는** 모듈이다. main.js 가
//   const { createBossSystem } = await import('./level2.js' + location.search)
// 로 boss.js 대신 이 파일을 읽는다. 그래서 export 이름·api 게터·DOM id 가 boss.js 와
// 한 글자라도 다르면 안 된다(ui.js 가 그 이름으로 폴링하고, 그 선택자 위에 CSS 를 덮는다).
//
// boss.js 와 다른 점
//  1. 보스가 없다. 각귀도 예고도 패턴도 체력바도 없다. 이 파일은 플레이어에게 피해를
//     한 번도 주지 않는다(damagePlayer·isPlayerDead 는 규약상 받기만 하고 안 쓴다).
//  2. 증표가 **제단 위에 처음부터 놓여 있다.** 보스를 죽여야 떨어지던 것을, 방을 지키는
//     정예 고블린 무리 한복판에서 집어 오는 일로 바꿨다. 무리는 enemy.js 가 맵의
//     mobs[] 로 세운다. **이 파일은 적을 한 마리도 만들지 않는다.**
//  3. 단계가 셋뿐이다: 제단의 증표 줍기 → 탈출(계단) → 층 돌파.
//     ★'보스전'·'사망' 이라는 문자열을 **절대 내보내지 않는다.** ui.js 가 그 두 글자를
//       보면 보스 경고 배너와 처치 연출(startCine)을 건다. 이 층에는 둘 다 없다.
//  4. 던전은 어둡다. 증표는 조명을 안 타는 재질로 두고 느리게 부유·회전시켜 어둠 속
//     등대로 쓴다. 유도(guide)의 kind 는 'token'·'exit' 둘뿐이다(ui.js NAV_KIND 의 符·門).
//
// 맵에서 읽는 것: level2.json 의 altar(제단 + 그 방)와 exits(탈출 계단). 둘 다 level.js 를
// 지난다. altar 가 없는 옛 맵에서는 경고만 남기고 증표 없이 조용히 돈다.
// ---------------------------------------------------------------------------
import * as THREE from './lib/three.module.js';
// ★main.js·enemy.js·boss.js 와 **같은 쿼리**로 부른다. URL 이 한 글자라도 다르면
//   브라우저가 별개 모듈로 올려서 서로 다른 맵 인스턴스를 보게 된다.
const LV = await import('./level.js' + location.search);

// ---------------------------------------------------------------------------
// 수치 (근거를 적는다. 근거 없는 숫자는 다음 사람이 못 고친다)
// ---------------------------------------------------------------------------
// 줍기 반경. boss.js 와 **같은 값**을 쓴다. 달려 지나가다 자연히 걸리는 거리라
// "밟았는데 안 주워지는" 순간이 안 생긴다. 여기만 다르게 두면 층마다 손맛이 갈린다.
const TOKEN_PICK_R = 1.7;
// 탈출구 반경(맵 radius, 보통 2.6)에 붙이는 여유. boss.js 와 같다.
const EXIT_PAD = 0.4;

// ── 증표의 몸짓 ──
// 제단 상판(groundY 가 이미 단 높이를 물고 있다) 위 0.9m. 플레이어 눈높이보다 조금
// 아래라 방에 들어서는 순간 시야 한복판에 걸린다. 더 띄우면 어깨 위로 지나가서
// 어두운 회랑에서는 오히려 놓친다.
const TOKEN_Y = 0.9;
// 부유 진폭 0.12m / 주기 2.6초. **아주 느려야** 한다. 어둠 속 유일한 광원이 빠르게
// 흔들리면 위치가 아니라 깜빡임으로 읽혀서 거리 가늠이 안 된다.
const BOB_AMP = 0.12;
const BOB_W = Math.PI * 2 / 2.6;    // = 2.417 rad/s
// 회전 0.6rad/s = 한 바퀴에 10.5초. 팔면체 모서리가 천천히 빛을 바꿔서 "살아 있다"만
// 알린다. 1rad/s 를 넘기면 팽이가 되고 제단이 장식품처럼 보인다.
const SPIN = 0.6;

// 색. 증표는 호박색이다(boss.js 와 같은 상수). 던전의 푸른 어둠·붉은 고블린과 안 섞인다.
const COL_TOKEN = 0xffc23a;

// 층 진행 단계. ★HUD 목표 한 줄과 api.phase 가 이 값만 본다.
//   보스가 없으므로 boss.js 의 P_FIND·P_FIGHT 두 단계가 통째로 빠졌다.
const P_PICK = 0, P_ESCAPE = 1, P_CLEAR = 2;

// ---------------------------------------------------------------------------
// 바닥 표시 재질 (boss.js 의 decalMat 을 그대로 옮겼다. 증표 줍기 반경 고리에만 쓴다)
// 테두리는 처음부터 진하게(= 어디까지가 사정권인지), 안쪽은 uFill 만큼 찬다.
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

// 원판(증표 줍기 반경 고리). 위를 보게 눕힌다.
function discMesh(color) {
  const g = new THREE.CircleGeometry(1, 44).rotateX(-Math.PI / 2);
  const m = new THREE.Mesh(g, decalMat(color));
  m.visible = false; m.frustumCulled = false; m.renderOrder = 3;
  return m;
}

// ---------------------------------------------------------------------------
// 증표 빛기둥. 증표를 든 사람은 **위치가 노출된다**(설계의 핵심 장치).
// 지금은 솔로라 볼 사람이 없지만 구조는 그대로 가져온다. 넷코드가 붙으면 carrier
// 좌표가 그대로 다른 팀 화면의 기둥이 된다.
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
// ★이름을 boss.js 와 똑같이 둔다. main.js 는 이 이름 하나만 알고 부른다.
//   opts = { scene, getPlayerPos, damagePlayer, onEvent, isPlayerDead, getKills }
// ---------------------------------------------------------------------------
export function createBossSystem(opts) {
  const scene = opts.scene;
  const getPlayerPos = opts.getPlayerPos;
  // ★damagePlayer·isPlayerDead 는 **받기만 한다.** 이 층에서 플레이어를 때리는 건
  //   고블린 무리(enemy.js)뿐이고, 체력·무적·사망은 거기 한 군데서만 관리한다.
  //   여기서 손대면 체력바가 두 개가 되고 무적 시간이 갈라진다.
  // 소리·연출 통로. ★'token' 과 'clear' 두 가지만 쏜다. 'die'·'tell'·'fire'·'hit' 을
  //   쏘면 main.js 가 화면 흔들기·먹링·피격 연출을 거는데, 이 층에는 그 사건이 없다.
  const onEvent = opts.onEvent || function () {};
  const getKills = opts.getKills || function () { return 0; };

  const data = LV.data() || {};
  // ── 문구는 **맵이 들고 있다** ──
  // level2.json 의 goal{} 이 정본이고, 없으면 아래 기본표로 떨어진다. 층이 늘어날 때
  // 문구를 고치러 이 파일에 들어올 일이 없어야 한다(맵 한 벌 = 문구 한 벌).
  const GTXT = data.goal || {};
  const EXIT_WORD = GTXT.exitWord || '계단';
  const spec = data.altar;
  // ★altar 가 없으면(옛 맵) 게임이 안 뜨는 것보다는 증표 없이 도는 편이 낫다.
  if (!spec) {
    console.warn('[level2] level2.json 에 altar 가 없다. 증표 없이 돈다.');
  }
  // ★level2.json 은 이미 three.js 좌표다. 변환하지 않는다.
  //   y 는 json 값이 아니라 groundY 로 다시 잡는다. 제단 상판 높이는 level.js 의
  //   platforms[] 가 들고 있고, 그게 화면에 실제로 서 있는 높이다.
  const AL = spec
    ? { x: spec.x, z: spec.z, y: LV.groundY(spec.x, spec.z) }
    : { x: 0, z: 0, y: 0 };
  // 제단 방 사각형. 지금은 검증(api.arena)용으로만 내보낸다.
  const AR = (spec && spec.room) || { x: 0, z: 0, hx: 0, hz: 0 };
  // ★탈출구에는 **한글 지명**을 붙인다. json 의 id(EXIT_1)는 안 바꾼다.
  //   내부 이름이 클리어 패널에 그대로 새는 사고가 예전에 있었다(3차 QA #4).
  //   이름은 맵 한가운데(0,0)에서 본 방위로 짓는다. 플레이어 위치와 무관한 **고정 지명**이라
  //   같은 출구가 언제나 같은 이름으로 불린다.
  // ★던전은 지상이 아니라 탑 안이다. 나가는 곳이 '문'이 아니라 **'계단'** 이다.
  const EXITS = (LV.exits() || []).map(e => ({
    id: e.id, x: e.x, z: e.z, r: (e.radius || 2.5) + EXIT_PAD,
    name: (Math.abs(e.x) >= Math.abs(e.z) ? (e.x >= 0 ? '동' : '서')
                                          : (e.z >= 0 ? '남' : '북')) + '쪽 ' + EXIT_WORD,
  }));

  // ── 증표 ──
  // ★재질이 MeshBasicMaterial 인 게 핵심이다. 던전에는 하늘빛이 없어서 조명을 타는
  //   재질로 두면 증표가 어둠에 같이 잠겨 버린다. 조명을 무시해야 등대가 된다.
  const token = new THREE.Group();
  const tokGem = new THREE.Mesh(
    new THREE.OctahedronGeometry(0.30, 0),
    new THREE.MeshBasicMaterial({ color: COL_TOKEN }));
  tokGem.position.y = TOKEN_Y;
  token.add(tokGem);
  const tokBeam = beamMesh(COL_TOKEN, 0.22, 7.0);
  token.add(tokBeam);
  const tokRing = discMesh(COL_TOKEN);
  tokRing.material.uniforms.uA.value = 0.9;
  tokRing.material.uniforms.uFill.value = 0;
  tokRing.visible = true;
  tokRing.scale.setScalar(TOKEN_PICK_R);   // 고리 = 줍기 사정권. 눈으로 보이는 약속이다
  tokRing.position.y = 0.04;               // 바닥과 같은 높이면 지글거린다
  token.add(tokRing);
  token.visible = false;
  scene.add(token);

  // 소지자 표식. 머리 위에 서는 기둥이 곧 넷코드가 다른 팀에게 보낼 값이다.
  const carryBeam = beamMesh(COL_TOKEN, 0.30, 9.0);
  carryBeam.visible = false;
  scene.add(carryBeam);

  // -------------------------------------------------------------------------
  // HUD. ★boss.js 는 이 층에서 아예 안 불린다. 그래서 **이 파일이 안 만들면 화면에
  //   목표 문구도 클리어 패널도 없다.** 선택자와 구조를 boss.js 와 똑같이 둔다
  //   (ui.js 가 맨 마지막에 style 을 붙여 이 DOM 위에 스킨을 덮는다).
  // ★#bBox(체력바 상자)는 구조만 남기고 **영영 안 보인다.** 이 층에는 보스가 없다.
  //   지우면 ui.js 의 #bBox·#bBar·#bFill 규칙이 갈 곳을 잃으므로 남겨 둔다.
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
  nameEl.textContent = GTXT.hudName || '1층 · 어둠에 잠긴 회랑';
  // ★인라인으로 한 번 더 못 박는다. 남의 파일(ui.js)이 #bBox 규칙을 덮어쓸 때
  //   opacity 를 같이 얹으면 체력바 상자가 빈 채로 떠오른다. 인라인이 시트를 이긴다.
  boxEl.style.opacity = '0';

  // ── 입장 타이틀 카드 문구 갈아 끼우기 ──
  // ★ui.js 는 이 작업의 소유 밖이라 한 글자도 안 건드린다. 대신 **화면에 나온 글자만**
  //   표시 단계에서 바꾼다(ui.js 자신이 boss.js 문구에 쓰는 TEXT_PATCH 와 같은 수법이다).
  //   ui.js 의 FLOOR 표는 초원판('풀에 덮인 절터')이라 던전에서 거짓말이 된다.
  //   ui.js 는 이 카드를 만들 때 딱 한 번 글자를 쓰고 그 뒤로는 안 건드리므로,
  //   카드가 DOM 에 붙는 순간 한 번만 갈아 끼우면 끝난다(R 재시작에도 유지된다).
  // ★큰 글자('탑 1층')는 그대로 둔다. 이 던전도 1층이다.
  (function patchTitleCard() {
    const name = GTXT.floorName;
    const lore = GTXT.floorLore;
    if (!name && !lore) return;
    let tries = 0;
    const put = () => {
      const t = document.getElementById('uiTitle');
      if (!t) return false;
      const sub = t.querySelector('.sub');
      const lo = t.querySelector('.lore');
      if (name && sub && sub.textContent !== name) sub.textContent = name;
      if (lore && lo && lo.textContent !== lore) lo.textContent = lore;
      return !!sub;
    };
    // ui.js 는 main.js 맨 끝에서 시작한다. 이 모듈이 먼저 뜨므로 붙을 때까지 기다린다.
    // ★영원히 도는 타이머를 남기지 않는다(30초면 ui.js 가 안 뜬 것이다).
    const iv = setInterval(() => {
      if (put() || ++tries > 300) clearInterval(iv);
    }, 100);
  }());

  // ---------------------------------------------------------------------------
  // 목표 문구. ★오너가 바꿀 곳은 이 표 하나다. 아래 코드에는 문구가 안 박혀 있다.
  //
  // 치환:
  //   {방위}, → '북쪽, ' 처럼 채워진다. 목표가 코앞이면(GOAL_DIR_MIN 안) **쉼표까지
  //             통째로 지워진다.** 두 걸음 옆에 있는 것에 방위를 붙이면 거짓말이 된다.
  //   {문}   → 탈출 계단 지명('남쪽 계단'). EXITS 의 name 에서 온다.
  // 내부 이름(EXIT_1 · altar · phase 번호)은 한 글자도 안 쓴다.
  const GOAL = {
    pick:   GTXT.pick || '{방위}, 제단의 <i>증표</i>를 집어라',
    escape: GTXT.escape || '{방위}, <i>증표</i>를 들고 {문}으로',
    clear:  GTXT.clear || '층 돌파',
    // 증표를 들면 무슨 일이 일어나는지를 그대로 적는다(명사 두 개로는 안 읽힌다).
    expose: GTXT.expose || ' <i>· 고블린들이 증표를 쫓는다</i>',
    // 맵에 exits 가 하나도 없을 때 {문} 자리에 들어가는 말. ★'탈출구' 를 쓰면
    // '탈출구으로' 가 된다(받침 없는 말에는 '로'). 받침이 있는 '계단' 이라야 문장이 산다.
    door:   EXIT_WORD,
  };
  // m. 이 거리 안이면 방위를 안 쓴다(가까울수록 방위는 매 걸음 뒤집혀서 도움이 안 된다)
  const GOAL_DIR_MIN = 8;
  const DIRS = ['북', '북동', '동', '남동', '남', '남서', '서', '북서'];

  // 플레이어에서 목표로 본 8방위. 맵 좌표는 -z 가 북, +x 가 동이다(level json 계약).
  // 화면은 고정 쿼터뷰(yaw 0)라 **화면 위 = 북**이고, 방위가 그대로 조작(위쪽 키)이 된다.
  function dirIndex(dx, dz) {
    let i = Math.round(Math.atan2(dx, -dz) / (Math.PI / 4));   // 0 = 북, +1 = 북동
    if (i < 0) i += 8;
    return i % 8;
  }

  // 지금 어디로 가야 하는가. 문구와 나침반(ui.js)이 **같은 한 곳**에서 목표를 받는다.
  // 두 벌로 두면 화살은 증표를 가리키는데 글자는 계단을 말하는 날이 온다.
  // ★kind 는 'token'·'exit' 둘뿐이다. ui.js NAV_KIND 에 있는 글리프가 그 둘(符·門)이다.
  function guideTarget() {
    if (phase === P_CLEAR) return null;
    if (phase === P_PICK) {
      return tokenState === 1 ? { x: tokenPos.x, z: tokenPos.z, kind: 'token' } : null;
    }
    const e = nearestExit();
    return e ? { x: e.x, z: e.z, kind: 'exit', name: e.name } : null;
  }
  function nearestExit() {
    if (!EXITS.length) return null;
    const p = getPlayerPos();
    let best = EXITS[0], bd = Infinity;
    for (let i = 0; i < EXITS.length; i++) {
      const e = EXITS[i];
      const dx = e.x - p.x, dz = e.z - p.z;
      const d = dx * dx + dz * dz;
      if (d < bd) { bd = d; best = e; }
    }
    return best;
  }

  // 문구 한 줄을 만든다. ★DOM 은 **글자가 바뀔 때만** 건드린다(아래 syncHud 의 memo).
  function goalLine(di, door) {
    const t = phase === P_PICK ? GOAL.pick
      : phase === P_ESCAPE ? GOAL.escape : GOAL.clear;
    return t.replace('{방위}, ', di < 0 ? '' : DIRS[di] + '쪽, ')
            .replace('{문}', door || GOAL.door)
          + (phase === P_ESCAPE ? GOAL.expose : '');
  }

  // memo. 단계·방위·계단이 그대로면 문자열을 만들지도, DOM 을 쓰지도 않는다.
  let hudPhase = -1, hudDir = -99, hudDoor = '';
  function syncHud() {
    // 방위는 매 프레임 다시 잰다(값이 싸다. atan2 한 번). 바뀔 때만 글자가 바뀐다.
    // ★돌파 문구에는 {방위} 자리가 없다. 그 단계에서 방위를 재면 값만 흔들려서
    //   같은 글자를 몇 번씩 다시 쓴다(memo 가 헛돈다).
    let di = -1, door = '';
    const t = phase === P_CLEAR ? null : guideTarget();
    if (t) {
      if (t.name) door = t.name;
      const p = getPlayerPos();
      const dx = t.x - p.x, dz = t.z - p.z;
      // 코앞이면 방위를 뺀다. 계단은 지명이 이미 방위를 말하므로 겹치면 뺀다
      //   ('남쪽, 증표를 들고 남쪽 계단으로' 같은 말이 안 나오게).
      if (dx * dx + dz * dz > GOAL_DIR_MIN * GOAL_DIR_MIN) {
        di = dirIndex(dx, dz);
        if (door && door.indexOf(DIRS[di] + '쪽') === 0) di = -1;
      }
    }
    if (hudPhase !== phase || hudDir !== di || hudDoor !== door) {
      hudPhase = phase; hudDir = di; hudDoor = door;
      goalEl.innerHTML = goalLine(di, door);
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
  let T = 0;                       // 시스템 시간(정지 중엔 안 흐른다). 부유·기둥 결에 쓴다
  let runT = 0;                    // 층 소요 시간. ★R 재시작 때 0 으로 되감겨야 한다
  let phase = P_PICK;
  let tokenState = 0;              // 0=없음 1=바닥 2=소지 3=반출
  const tokenPos = new THREE.Vector3();
  let carriedSince = 0;
  let clearInfo = null;
  // ── ★이 판에서 잡은 수 ── (boss.js 에서 함정 주석까지 그대로 옮겼다)
  // enemy.js 의 kills 는 "R 을 누를 때 0 으로 돌아가는 판 누적"이고, 여기서는 판 시작
  // 시점과의 차이를 쓴다. 두 값이 일치해야 HUD·클리어 패널·재시작이 삼자일치다.
  // ★고장나는 경로가 하나 있다. main.js 는 R 에서 resetKills() -> restart() 순서로
  //   부르는데, 이 순서가 뒤집히거나 누가 kills 를 따로 되돌리면 killsAtStart 가
  //   현재 kills 보다 커진 채로 남는다. 그러면 Math.max(0, kills - killsAtStart) 가
  //   **영영 0** 이다 = "클리어 패널 처치 0 고정" 사고.
  //   그래서 매 프레임 감시해서 바깥 카운터가 줄어들면 기준선을 그 자리로 내린다.
  let killsAtStart = 0;
  function syncKillBase() {
    const k = getKills();
    if (k < killsAtStart) killsAtStart = k;      // 바깥에서 리셋됐다 = 기준선도 내린다
  }
  function runKills() { return Math.max(0, getKills() - killsAtStart); }

  // -------------------------------------------------------------------------
  // 리셋. R(제자리)과 클리어 후 재도전이 같은 문을 지나게 한다.
  // ★runT 를 0 으로 되감는 것이 ui.js 와의 유일한 신호다(t < lastRunT - 0.4 → newRun).
  // -------------------------------------------------------------------------
  function restart() {
    runT = 0;
    phase = P_PICK;
    carriedSince = 0;
    clearInfo = null;
    clearEl.style.opacity = '0';
    killsAtStart = getKills();
    // 증표를 제단 위에 도로 올린다. 맵에 제단이 없으면 아예 안 세운다.
    if (spec) dropToken(AL.x, AL.z);
    else { tokenState = 0; token.visible = false; carryBeam.visible = false; }
  }

  // 제단 위(또는 지정한 자리)에 증표를 놓는다.
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
    // exit 은 내부 id(EXIT_1)를 그대로 들고 있다. **화면에는 지명만 쓴다.**
    //   id 는 api·로그에 남겨 둔다(검증 스크립트가 그걸로 어느 계단인지 가린다).
    clearInfo = { time: +runT.toFixed(1), kills: runKills(),
                  exit: exit.id, exitName: exit.name };
    // ★구조를 지킨다. ui.js fixClearKills 가 '처치' 라는 낱말이 든 <td> 를 찾아
    //   **다음 형제 <td class="v">** 를 HUD 값으로 덮는다. 두 칸의 순서를 바꾸면
    //   결과창의 처치 수가 영영 안 맞는다.
    // ★'으로 반출' 이 아니라 처음부터 최종 문구를 쓴다(ui.js TEXT_PATCH 가 치환하던 말).
    clearEl.innerHTML =
      '<h1>층 돌파</h1><table>' +
      '<tr><td>소요 시간</td><td class="v">' + fmtTime(runT) + '</td></tr>' +
      '<tr><td>처치</td><td class="v">' + clearInfo.kills + '</td></tr>' +
      '<tr><td>증표</td><td class="v">' + (exit.name || GOAL.door) + '으로 가지고 나감</td></tr>' +
      '</table><div class="hint">R 키를 눌러 다시 도전</div>';
    clearEl.style.opacity = '1';
  }

  // -------------------------------------------------------------------------
  // 매 프레임. ★이 모듈은 칼 판정을 안 한다(고블린은 enemy.js 가 맡는다).
  //   ctx 에서 보는 것은 paused 하나뿐이다.
  // -------------------------------------------------------------------------
  function update(dt, ctx) {
    // 정지(클립 미리보기) 중에는 시간을 안 흘린다. 소요 시간이 멈춰야 기록이 정직하다.
    if (ctx && ctx.paused) return;

    T += dt;
    if (phase !== P_CLEAR) runT += dt;
    syncKillBase();                    // 바깥 처치 카운터가 리셋됐는지 매 프레임 확인

    const player = getPlayerPos();

    if (tokenState === 1) {
      // 제단 위에서 아주 느리게 떠오르고 돈다. 어둠 속에서 이 움직임이 "저기다"를 만든다.
      tokGem.rotation.y += dt * SPIN;
      tokGem.position.y = TOKEN_Y + Math.sin(T * BOB_W) * BOB_AMP;
      tokBeam.material.uniforms.uT.value = T;
      tokRing.material.uniforms.uA.value = 0.55 + Math.sin(T * 3.0) * 0.18;
      // 줍기. xz 평면 거리만 본다(제단 단 높이만큼 y 가 벌어져 있어도 주울 수 있어야 한다).
      const dx = player.x - tokenPos.x, dz = player.z - tokenPos.z;
      if (dx * dx + dz * dz < TOKEN_PICK_R * TOKEN_PICK_R) pickToken();
    } else if (tokenState === 2) {
      // ★소지자 노출. 머리 위에 기둥이 선다. 이 좌표가 곧 넷코드가 뿌릴 값이다.
      carryBeam.position.set(player.x, player.y + 1.9, player.z);
      carryBeam.material.uniforms.uT.value = T;
      // 탈출 판정. **줍는 것만으로는 안 된다.** 계단까지 들고 나가야 확정이다.
      for (let i = 0; i < EXITS.length; i++) {
        const e = EXITS[i];
        const ex = player.x - e.x, ez = player.z - e.z;
        if (ex * ex + ez * ez < e.r * e.r) { doClear(e); break; }
      }
    }

    syncHud();
  }

  // 첫 배치
  restart();
  syncHud();

  // -------------------------------------------------------------------------
  // ★api 의 이름·타입·문자열 값은 boss.js 와 같아야 한다. ui.js·main.js 가 폴링으로
  //   읽는 값이라, 여기 문자열 하나를 바꾸면 화면이 통째로 어긋난다.
  // -------------------------------------------------------------------------
  const api = {
    update,
    restart,
    // 넷코드 접점(boss.js 와 같은 자리). 증표 소지자의 위치는 층 전체에 공개되는 값이다.
    get carrier() {
      if (tokenState !== 2) return null;
      const p = getPlayerPos();
      return { x: +p.x.toFixed(2), z: +p.z.toFixed(2), since: +carriedSince.toFixed(1) };
    },
    get token() {
      return { state: ['없음', '바닥', '소지', '반출'][tokenState],
               x: +tokenPos.x.toFixed(2), z: +tokenPos.z.toFixed(2) };
    },
    // ★보스가 없다. 체력바(#bBox)는 영영 안 뜬다. 0/1 은 "0% 짜리 빈 바"라는 뜻이 아니라
    //   **읽을 값이 없다**는 뜻이고, 나누기가 터지지 않게 maxHp 를 1 로 둔다.
    get hp() { return 0; },
    get maxHp() { return 1; },
    // ★'사망' 을 절대 반환하지 않는다. ui.js 가 그 글자를 보면 보스 처치 연출(startCine)을
    //   건다. 이 층에는 처치할 보스가 없으므로 화면이 영영 안 돌아온다.
    get state() { return '대기'; },
    // ★'보스전' 을 절대 반환하지 않는다. ui.js 가 그 글자를 보면 보스 경고 배너를 띄운다.
    get phase() { return ['증표줍기', '탈출', '돌파'][phase]; },
    // 보스가 없으니 **제단 자리**를 돌려준다. main.js 가 window.__boss.pos 를 읽는 자리는
    // 'fire' 직후(lastBossFireAt 350ms) 뿐인데 이 모듈은 'fire' 를 안 쏘므로 안 쓰인다.
    get pos() { return { x: +AL.x.toFixed(2), z: +AL.z.toFixed(2) }; },
    get time() { return +runT.toFixed(1); },
    get cleared() { return clearInfo; },
    // 이 판에서 잡은 수. HUD(enemy.kills)·클리어 패널과 삼자일치를 밖에서 확인하는 창구.
    get runKills() { return runKills(); },
    // 조우 유예는 이 층에 없다(보스가 없다). boss.js API 와 모양만 맞춘다.
    get grace() { return 0; },
    // ★유도의 단일 진실. 상단 문구도 나침반(ui.js)도 이 값 하나를 본다.
    get guide() { return guideTarget(); },
    arena: AR,
    exits: EXITS,
    // 검증·디버그용. 브라우저 콘솔·Playwright 봇이 걸어가지 않고도 상태를 만들 수 있어야 한다.
    debug: {
      // 증표를 즉시 손에 넣은 상태로(P_ESCAPE). 제단까지 걸어가는 시간을 건너뛴다.
      pick() {
        if (tokenState >= 2) return '이미 소지';
        pickToken();
        return '증표 소지';
      },
      // 가장 가까운 계단으로 즉시 클리어. 안 들고 있으면 먼저 쥐여 준다.
      clear() {
        if (clearInfo) return '이미 돌파';
        const e = nearestExit();
        if (!e) return '탈출구 없음';
        if (tokenState < 2) pickToken();
        doClear(e);
        return '돌파 ' + e.name;
      },
      // 봇이 걸어갈 목표 좌표. exit 은 **부를 때의 플레이어 기준 가장 가까운 계단**이라
      // 증표를 주운 뒤 다시 부르면 그때의 답이 나온다(guide 와 같은 값).
      at() {
        const e = nearestExit();
        return { altar: { x: +AL.x.toFixed(2), z: +AL.z.toFixed(2) },
                 exit: e ? { x: +e.x.toFixed(2), z: +e.z.toFixed(2) } : null };
      },
    },
  };
  return api;
}
