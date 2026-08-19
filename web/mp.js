// ── 멀티플레이 (게임 계층) ─────────────────────────────────────────────────
// 남의 캐릭터를 내 세계에 세우고 위치·방향·동작을 맞춘다.
//
// ★지금까지 온 길과 **아직 못 하는 것**을 먼저 적는다.
//   1단계(아바타 공유) : 남의 몸·모션·공격 이펙트가 내 화면에 선다.
//   2단계 1차(요괴 동기화) : 요괴를 **방장 한 명만** 굴린다. 참가자는 받은 상태를
//     그림으로만 그린다 = 같은 요괴가 같은 자리에 있고 같이 죽는다.
//     그 규약은 enemy.js 의 NET_* 머리 주석, 전송 정책은 mpenemy.js 가 정본이다.
//   2단계 2차(같이 잡고 같이 맞는다) : 참가자의 칼·화살이 요괴에 닿는다(주장 + 방장
//     확정), 요괴가 **제일 가까운 사람**을 쫓고 때린다, 참가자 화면에도 드랍이 뜬다.
//     이 파일이 그 둘에 대는 것은 **사람 목록**(요괴의 표적·관심 영역의 중심)과
//     주장을 방장에게 실어 나르는 자리뿐이다. 규약은 mpenemy.js·enemy.js 가 안다.
//   아직 못 하는 것 : 보스는 여전히 각자 로컬이다(따로 안 맞춘다).
// ★전송은 net.js 뒤에 숨어 있다. 스팀으로 가면 그 파일만 갈아끼운다.
//
// ── 좌표를 어떻게 넘기는가 (여기가 이 파일에서 제일 조심스러운 대목) ──
// main.js 는 root(Group)가 x·z 를 갖고, 그 자식 model 이 **매 프레임 접지 보정**으로
// 로컬 y 를 바꾼다(발뼈 최저점을 바닥에 붙이는 계산. 달리기는 한 사이클 최저값).
// 그 계산을 원격에서 다시 돌리면 어긋날 수밖에 없다(클립 시각이 미세하게 다르다).
// 그래서 **model 의 월드 좌표를 그대로 보낸다.** 받는 쪽은 model 에 오프셋을 주지 않고
// (position 0) 그룹에 받은 월드 좌표를 꽂는다. 같은 glb·같은 스케일이라 메시 배치가
// 동일하므로 이러면 두 화면의 그림이 정확히 겹친다. **model.position.y 를 여기서
// 건드리면 그 순간 어긋난다.**

import { createNet, makeRoomCode } from './net.js';

const SEND_HZ = 15;              // 초당 상태 송신. 40바이트 x 15 = 600B/s 정도다
const LERP_K = 16;               // 남의 위치를 따라붙는 속도(지수 감쇠)
const START_SWORD = 'nokseun';   // 1번 슬롯. 안 고르면 칼 일곱 자루가 다 보인다

export { makeRoomCode };

export function createMultiplayer(ctx) {
  const { THREE, scene, loader, glbUrl, CHAR_CFG, DEF_CFG, getSelf } = ctx;
  // ── 남의 공격 이펙트 (22차) ──
  // ★null 이면 통째로 안 돈다. **스위치(MP_FX_ON)의 정의는 main.js 한 곳**이고
  //   여기서는 그 결과만 받는다 - 스위치를 두 벌 두면 반드시 어긋난다(이 레포의 교훈).
  // ★칼 이펙트는 소식을 **한 바이트도 더 안 쓴다.** 남의 아바타에는 같은 glb 의 뼈와
  //   칼 메시가 그대로 있고 클립도 이미 같은 시각·같은 배속으로 도니까, 궤적을 그
  //   손 본에서 직접 계산한다(main.js mpFx 머리 주석이 정본).
  //   화살만 예외로 발사 이벤트(msg.sh)를 태워 보낸다 - 궤적이 결정적이라 시작점과
  //   방향만 같으면 그대로 재현되기 때문이다.
  const fx = ctx.fx || null;
  // ── 요괴 동기화 (2단계 1차) ──
  // ★같은 규칙이다. **스위치(MP_ENEMY_ON)의 정의는 main.js 한 곳**이고 여기서는
  //   이 값이 null 인지만 본다. 전송 정책(주기·관심 영역·사건 되풀이)은 mpenemy.js 가
  //   들고 있고, 이 파일은 **소식을 실어 나르는 자리**만 내준다.
  const enemy = ctx.enemy || null;
  // 관심 영역의 중심 = 사람이 서 있는 자리. [x,z, x,z, ...] 로 매 프레임 다시 채운다
  // (배열을 새로 만들지 않는다 - 10Hz 라도 GC 에 쓰레기를 쌓을 이유가 없다).
  const aoi = [];
  // ── 사람 목록 (2차) ──
  // 요괴가 **제일 가까운 사람**을 쫓게 하려면 enemy.js 가 남의 자리를 알아야 한다.
  // main.js 가 매 프레임 enemies.update(ctx.players) 로 넘긴다.
  // ★그릇을 재사용한다(매 프레임 객체를 새로 지으면 60fps x 인원수만큼 쓰레기가 쌓인다).
  // ★자리는 tgt(마지막으로 받은 값)를 쓴다. cur(화면에 그려지는 보간값)은 한 박자
  //   뒤라, 판정에 쓰면 요괴가 실제보다 뒤를 때린다.
  const players = [];
  const aoi2 = [];
  // 마지막으로 보낸 내 자리. 관심 영역의 중심으로만 쓴다(아래 송신부가 적는다).
  let selfX = 0, selfZ = 0, selfOK = false;

  let net = null;
  // ★송신 주기는 **벽시계**로 잰다. 게임 dt(rawDt)로 재면 안 된다 - 그 값은
  //   main.js 에서 `Math.min(0.05, delta)` 로 잘려 있어서, 프레임이 낮을수록
  //   실제 흐른 시간보다 적게 쌓인다. 실측(2026-08-19 렉 신고): **13.5fps 인 기계가
  //   15Hz 를 시켰는데 6.75Hz 만 보냈다**(delta 0.074 가 0.05 로 잘려 두 프레임에
  //   한 번씩만 문턱을 넘었다). 느린 기계일수록 더 안 보내게 되는 셈이라
  //   상대 화면에서 그 사람만 유독 끊겨 보인다 - 방향이 정확히 반대였다.
  let lastSendMs = 0;
  let dead = false;
  let myMap = '';
  let warnedMap = false;
  let txSeq = 0;                 // 내가 보낸 소식의 번호. 채널이 unreliable 이라 순서가 뒤바뀔 수 있다
  let txCount = 0;
  // ── 수신 계측 ──
  // ★렉 신고(2026-08-19)를 숫자로 가르려고 넣었다. 눈으로는 "네트워크가 느린 것"과
  //   "상대 컴퓨터가 느린 것"과 "상대 창이 백그라운드라 송신이 멈춘 것"이 구분되지 않는다.
  //   상대가 15Hz 로 보내므로 정상은 rx≈15/s · 최대 간격 ~70ms 다.
  //   rx 가 뚝 떨어지면 보내는 쪽 문제, rx 는 멀쩡한데 화면이 버벅이면 받는 쪽 성능이다.
  let rxCount = 0, rxLastT = 0, rxGapMax = 0, rxStale = 0;
  const rxTimes = [];
  // ── fps ──
  // ★벽시계로 잰다(게임 dt 는 히트스톱·슬로모에 멈춘다). 멀티 중에만 화면에 뜬다 -
  //   평시 화면에 상시 표시물을 얹지 않는다는 이 게임의 관례를 지키기 위해서다.
  //   이게 있어야 "네트워크가 느린 것" 과 "그 사람 화면이 느린 것" 이 갈린다.
  let fpsN = 0, fpsT0 = 0, fpsVal = 0;
  let route = '';                // 'host/host' · 'srflx/srflx' · 'relay/...' 등
  // ★주기는 **벽시계**로 잰다. rawDt 는 Math.min(0.05, delta) 로 잘려 있어서
  //   프레임이 낮으면 실제보다 느리게 쌓인다(송신 주기에서 이미 한 번 밟은 함정이다).
  let routeMs = 0;
  const peers = new Map();       // id -> { group, model, mixer, actions, cur, tgt, clip, seq, char }

  // ── 상태 표시 ──
  // 화면에 새 표시물을 얹는 걸 이 게임은 계속 줄여 왔다. 그래서 접속 중일 때만
  // 우상단에 한 줄, 그것도 조작을 가리지 않는 자리에 둔다.
  const hud = document.createElement('div');
  hud.id = 'mpHud';
  hud.style.cssText = 'position:fixed;right:14px;top:56px;z-index:6;pointer-events:none;' +
    'font:700 11px/1.5 "Paperlogy",sans-serif;letter-spacing:.06em;text-align:right;' +
    'color:#c8b9a2;text-shadow:0 1px 2px #000;display:none;white-space:pre-line;';
  document.body.appendChild(hud);

  function say(text, kind) {
    hud.style.display = text ? 'block' : 'none';
    hud.textContent = text || '';
    hud.style.color = kind === 'err' ? '#ff9b82' : (kind === 'ok' ? '#b9ee89' : '#c8b9a2');
  }
  function roster() {
    if (!net) return;
    const n = net.count;
    let line = '방 ' + net.room + (net.isHost ? ' (방장)' : '') + '\n' + n + '명 접속';
    if (fpsVal) line += '  ·  ' + fpsVal + 'fps';
    if (route) line += '\n경로 ' + route;
    if (n > 1) {
      const hz = (rxTimes.length / 2).toFixed(0);      // 최근 2초 평균
      line += '\n수신 ' + hz + '/s';
      if (rxGapMax > 400) line += '  ·  최대 끊김 ' + Math.round(rxGapMax) + 'ms';
    }
    say(line, n > 1 ? 'ok' : null);
  }
  let hudAcc = 0;

  // ── 남의 아바타 하나 세우기 ──
  // loadChar(main.js)와 같은 처리를 하되, 게임 로직에 쓰이는 것들(발뼈·칼 교체·
  // 발광 셸·미리보기)은 안 만든다. 남의 몸은 **그림**이지 판정 대상이 아니다.
  function spawn(id, charName) {
    if (peers.has(id) || dead) return;
    const name = charName || 'basic2';
    const group = new THREE.Group();
    scene.add(group);
    const p = { group, model: null, mixer: null, actions: null, current: null,
                cur: { x: 0, y: 0, z: 0, yaw: 0 }, tgt: { x: 0, y: 0, z: 0, yaw: 0 },
                clip: 'Idle', seq: -1, char: name, ready: false };
    peers.set(id, p);

    loader.load(glbUrl('./' + name + '.glb'), gltf => {
      if (dead || !peers.has(id)) return;                 // 로드 중에 나갔다
      const m = gltf.scene;
      m.updateMatrixWorld(true);
      // 키 정규화. 칼(SW_)·방패(SH_)는 박스에서 뺀다 - 넣으면 키가 부풀어 캐릭터가
      // 바닥에 파묻힌다(main.js loadChar 와 같은 이유·같은 규칙이다).
      const box = new THREE.Box3(); const _tb = new THREE.Box3();
      m.traverse(o => {
        if (o.isMesh && !o.name.startsWith('SW_') && !o.name.startsWith('SH_')) box.union(_tb.setFromObject(o));
      });
      if (box.isEmpty()) box.setFromObject(m);
      const cfg = CHAR_CFG[name] || DEF_CFG;
      const h = box.max.y - box.min.y;
      m.scale.setScalar(cfg.h / (h || 1));
      // ★position 은 0 그대로 둔다. 위 머리 주석의 좌표 규약이다.

      m.traverse(o => {
        if (o.isMesh) {
          o.frustumCulled = false;
          o.castShadow = true;
          o.receiveShadow = true;
          const old = o.material;
          o.material = new THREE.MeshToonMaterial({
            map: old && old.map ? old.map : null,
            color: old && old.map ? 0xffffff : (old ? old.color : 0x888888),
          });
          // 칼은 시작 칼 한 자루만 남긴다(안 고르면 일곱 자루가 겹쳐 보인다)
          if (o.name.startsWith('SW_')) {
            o.visible = o.name.slice(3).replace(/_\d+$/, '') === START_SWORD;
          }
        }
      });
      group.add(m);

      const mx = new THREE.AnimationMixer(m);
      const acts = {};
      gltf.animations.forEach(c => {
        const a = mx.clipAction(c);
        acts[c.name] = a;
        if (c.name === 'Run') a.timeScale = cfg.run ? cfg.run.ts : 1;
        if (c.name === 'Walk') a.timeScale = cfg.walk ? cfg.walk.ts : 1;
        if (c.name === 'Attack' || c.name === 'Heavy' || c.name === 'Wide') {
          a.setLoop(THREE.LoopOnce); a.clampWhenFinished = true;
        }
      });
      p.model = m; p.mixer = mx; p.actions = acts; p.ready = true;
      playOn(p, p.clip, 0);
      // 칼 궤적 한 벌을 이 사람에게 붙인다(칼이 없는 캐릭터면 안에서 조용히 넘어간다).
      // ★키(cfg.h)를 그대로 넘긴다 - main.js 의 charH 와 **같은 수**다.
      if (fx) fx.attach(id, m, cfg.h);
    }, null, err => {
      console.warn('[mp] 남의 캐릭터를 못 읽었다:', name, err);
    });
  }

  function despawn(id) {
    const p = peers.get(id);
    if (!p) return;
    if (fx) fx.detach(id);
    if (p.mixer) p.mixer.stopAllAction();
    scene.remove(p.group);
    p.group.traverse(o => {
      if (o.isMesh) { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); }
    });
    peers.delete(id);
  }

  // 남의 동작 하나 틀기. 같은 이름이라도 seq 가 바뀌면 처음부터 다시 튼다
  // (Z 를 연달아 치면 클립 이름은 계속 'Attack' 이라 이름만 봐서는 못 잡는다).
  function playOn(p, name, fade) {
    if (!p.ready || !p.actions) return;
    const a = p.actions[name] || p.actions.Idle;
    if (!a) return;
    a.reset().play();
    if (p.current && p.current !== a) p.current.crossFadeTo(a, fade === undefined ? 0.15 : fade, false);
    else if (!p.current) a.fadeIn(fade === undefined ? 0.15 : fade);
    p.current = a;
  }

  function onMessage(msg, from) {
    if (!from || from === (net && net.id)) return;
    // ── 요괴 소식 ──
    // ★방장은 자기 요괴를 자기가 굴리므로 남의 요괴 소식을 절대 안 받는다(별 구조라
    //   'en' 은 방장에게서만 나가지만, 방어로 한 번 더 막는다 - 여기가 뚫리면
    //   방장 화면의 요괴가 참가자 소식에 끌려다닌다).
    if (msg.t === 'en') {
      if (enemy && net && !net.isHost) enemy.recv(msg);
      return;
    }
    // ── 참가자의 주장 (2차) ──
    // ★방장만 받는다. 별 구조라 방장이 다른 참가자에게 그대로 중계하는데, 그쪽에서는
    //   isHost 가 false 라 mpenemy 가 조용히 버린다(3인 이상에서 낭비되는 건
    //   주장 한 건 크기뿐이고, 지금 상정 인원에서 값을 치를 만한 낭비가 아니다).
    // ★상식 검사의 자 = **그 사람의 마지막 좌표**. 여기가 그 값을 들고 있는 유일한
    //   자리라 여기서 꺼내 넘긴다(mpenemy 는 아바타를 모른다).
    if (msg.t === 'eh') {
      if (enemy && net && net.isHost) {
        const p = peers.get(from);
        if (p) enemy.recvClaim(msg, from, p.tgt.x, p.tgt.z);
      }
      return;
    }
    if (msg.t === 'st') {
      // ★층이 다르면 서로의 아바타가 남의 맵 좌표에 서게 된다(벽 속·허공). 그림이
      //   깨지기 전에 말해 주는 편이 낫다 - 테스트에서 제일 먼저 밟는 함정이다.
      if (msg.m && myMap && msg.m !== myMap) {
        if (!warnedMap) {
          warnedMap = true;
          say('층이 다르다. 둘 다 같은 층으로 들어와야 만난다.', 'err');
        }
        return;
      }
      // 계측(어떤 소식이든 도착한 시각을 센다)
      const nowMs = performance.now();
      if (rxLastT) {
        const gap = nowMs - rxLastT;
        if (gap > rxGapMax) rxGapMax = gap;
      }
      rxLastT = nowMs;
      rxCount++;
      rxTimes.push(nowMs);
      while (rxTimes.length && rxTimes[0] < nowMs - 2000) rxTimes.shift();

      let p = peers.get(from);
      if (!p) { spawn(from, msg.k); p = peers.get(from); roster(); }
      if (!p) return;
      // ★채널이 unreliable 이라 **순서가 뒤바뀐다.** 옛 소식을 그대로 반영하면
      //   캐릭터가 뒤로 튄다. 번호가 뒷걸음질하면 버린다.
      //   단 상대가 새로고침하면 번호가 1 부터 다시 시작하므로, 크게 작아진 경우는
      //   되감기가 아니라 **재접속**으로 보고 받아들인다(그때 되감기 오탐은 한 번뿐이다).
      if (typeof msg.n === 'number') {
        if (p.lastN !== undefined && msg.n <= p.lastN && p.lastN - msg.n < 120) { rxStale++; return; }
        p.lastN = msg.n;
      }
      // 캐릭터를 바꿔서 다시 들어온 경우(홈으로 나갔다 온다)
      if (msg.k && msg.k !== p.char) { despawn(from); spawn(from, msg.k); return; }
      p.tgt.x = msg.x; p.tgt.y = msg.y; p.tgt.z = msg.z; p.tgt.yaw = msg.r;
      // ★죽은 사람은 요괴의 표적에서 뺀다(2차). 안 빼면 무리가 시체 곁에 모여 선다.
      //   평시에는 이 칸이 아예 안 실린다(getSelf 가 죽었을 때만 붙인다).
      p.dead = msg.d === 1;
      if (!p.seen) {                       // 첫 소식이면 순간이동으로 자리를 잡는다
        p.cur.x = msg.x; p.cur.y = msg.y; p.cur.z = msg.z; p.cur.yaw = msg.r;
        p.seen = true;
      }
      // ── 남이 쏜 화살 ──
      // ★번호(sh[0])로 중복을 버린다. 같은 발사가 최대 9번 실려 오는데(0.6초 창),
      //   그건 유실 대비지 아홉 발이 아니다. 번호가 없으면 한 발이 아홉 번 날아간다.
      if (fx && msg.sh && msg.sh.length >= 7 && msg.sh[0] !== p.lastShot) {
        p.lastShot = msg.sh[0];
        fx.arrow(msg.sh);
      }
      if (msg.c !== p.clip || msg.s !== p.seq) {
        p.clip = msg.c; p.seq = msg.s;
        playOn(p, msg.c);
        // ★재생속도를 맞춘다. 공격은 캐릭터별로 갈려서(검사 1.35 / 궁수 2.00)
        //   1.0 으로 틀면 남의 화면에서만 느린 공격이 된다.
        if (p.current && typeof msg.ts === 'number' && msg.ts > 0) {
          p.current.setEffectiveTimeScale(msg.ts);
        }
        if (p.current && typeof msg.p === 'number') p.current.time = msg.p;
      } else if (p.current && typeof msg.p === 'number') {
        // ★3연타는 play() 를 다시 부르지 않고 **클립 시간을 점프**해서 낸다. 이름만
        //   보면 1타 뒤로는 아무 일도 안 일어난 것처럼 보인다. 그래서 재생 시각도 맞춘다.
        //   임계값(0.12초)을 두는 이유는 매 소식마다 되감으면 재생이 뚝뚝 끊기기 때문이다.
        if (Math.abs(p.current.time - msg.p) > 0.12) p.current.time = msg.p;
      }
    } else if (msg.t === 'bye') {
      despawn(from); roster();
      // ★방장이 인사하고 나갔다. 그 소식이 안 오는 판(강제 종료)도 있으므로
      //   mpenemy 쪽에 시간 그물(DEAD_MS)이 하나 더 있다 - 둘 중 먼저 걸리는 쪽이 이긴다.
      if (enemy && isHostPeer(from)) enemy.hostGone();
    }
  }

  // 요괴 소식을 내보내는 손잡이. 클로저 하나로 고정한다(net 은 나중에 갈릴 수 있다).
  function sendEn(o) { if (net) net.send(o); }

  // 이 소식이 **방장**에게서 온 것인가. 참가자의 연결은 방장 하나뿐이라(별 구조)
  // conns 의 첫 항목이 곧 방장이다. 남의 소식은 방장이 중계하되 원본 from 을 유지하므로
  // 여기서 갈린다.
  function isHostPeer(from) {
    if (!net || net.isHost) return false;
    const p = net.peers();
    return p.length > 0 && p[0] === from;
  }

  // 각도는 짧은 쪽으로 돈다(안 그러면 뒤돌 때 한 바퀴를 그린다)
  function angLerp(a, b, t) {
    let d = b - a;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    return a + d * t;
  }

  const api = {
    get on() { return !!net; },
    get count() { return net ? net.count : 1; },
    get room() { return net ? net.room : ''; },

    // mode: 'host' | 'join'
    async start(mode, code) {
      say('연결하는 중…');
      net = await createNet({
        onMessage,
        onLeave: id => {
          despawn(id); roster();
          // ★방장이 나가면 참가자의 요괴가 그 자리에 얼어붙는다(소식이 끊긴다).
          //   내 AI 로 되돌려 그대로 이어 산다 - 얼어붙은 화면보다 낫다.
          if (enemy && net && !net.isHost && net.count <= 1) enemy.hostGone();
        },
        onJoin: () => {
          roster();
          // 새로 들어온 사람에게는 목록부터 맞춰 줘야 한다(전수 한 장을 앞당긴다)
          if (enemy && net && net.isHost) enemy.forceFull();
        },
        // 진행 상태를 그대로 보여준다. 붙는 데 십여 초가 걸리는 판이라
        // 아무 말이 없으면 "멈췄다" 로 읽힌다(roster() 가 뒤에 덮는다).
        onStatus: (t, k) => say(t, k),
      });
      try {
        if (mode === 'host') await net.host(code);
        else await net.join(code);
      } catch (e) {
        say((e && e.message) || '연결 실패', 'err');
        net.close(); net = null;
        throw e;
      }
      // ★내 짧은 이름을 여기서 세운다(2차). 붙기 전에는 peerjs id 자체가 없다.
      //   mpenemy 가 enemy.js 에도 같은 값을 넣어 준다 - 정의는 그 한 곳뿐이다.
      if (enemy && enemy.setTag) enemy.setTag(net.id);
      roster();
      // 나갈 때 남의 화면에서 내 아바타를 지운다(브라우저를 닫아도 불린다)
      window.addEventListener('pagehide', () => { try { net && net.send({ t: 'bye' }); } catch (_) {} });
      return net.room;
    },

    // 프레임마다. rawDt 를 받는다 - 남의 아바타는 내 히트스톱에 멈추면 안 된다.
    update(rawDt) {
      if (dead) return;
      // fps 세기(멀티 중이 아니어도 세 둔다 - 방에 들어간 순간 바로 보여야 한다)
      {
        const t = performance.now();
        if (!fpsT0) fpsT0 = t;
        fpsN++;
        if (t - fpsT0 >= 1000) { fpsVal = Math.round(fpsN * 1000 / (t - fpsT0)); fpsN = 0; fpsT0 = t; }
      }
      // 남의 아바타: 목표로 따라붙고 클립을 돌린다
      const k = 1 - Math.exp(-LERP_K * rawDt);
      for (const [id, p] of peers) {
        p.cur.x += (p.tgt.x - p.cur.x) * k;
        p.cur.y += (p.tgt.y - p.cur.y) * k;
        p.cur.z += (p.tgt.z - p.cur.z) * k;
        p.cur.yaw = angLerp(p.cur.yaw, p.tgt.yaw, k);
        p.group.position.set(p.cur.x, p.cur.y, p.cur.z);
        p.group.rotation.y = p.cur.yaw;
        if (p.mixer) p.mixer.update(rawDt);
        // ★★칼 궤적은 **뼈를 굴린 바로 뒤**에 그린다. 순서가 뒤집히면 궤적이 한 프레임
        //   낡은 자리에 그어져 칼에서 떨어져 보인다(빠른 스윙에서 0.5m 가 넘는다).
        if (fx && p.ready) fx.frame(id, rawDt, p.clip, p.current);
      }
      // 붙은 길은 자주 안 바뀐다. 4초에 한 번만 묻는다(getStats 는 비동기·비싸다)
      if (net && net.count > 1) {
        const rNow = performance.now();
        if (rNow - routeMs > 4000) {
          routeMs = rNow;
          net.route().then(r => { route = r; }).catch(() => {});
        }
      }
      // 진단 표시는 0.5초마다만 다시 쓴다(매 프레임 DOM 을 쓸 이유가 없다)
      if (net) {
        hudAcc += rawDt;
        if (hudAcc > 0.5) { hudAcc = 0; roster(); }
      }
      // 내 상태 송신
      if (!net) return;
      const txNow = performance.now();
      // ── 요괴 상태 송신(방장만) ──
      // ★아바타 주기(15Hz)와 **따로** 돈다. 요괴는 10Hz 로 충분하고, 여기서 같이
      //   묶으면 둘 중 하나를 손볼 때마다 다른 하나가 끌려간다.
      // ★getSelf() 를 여기서 부르면 안 된다. 그 함수는 toFixed 로 문자열을 여남은 개
      //   만드는데, 이 자리는 **매 프레임** 돈다(15Hz 문턱은 아래에 있다). 아래 송신이
      //   적어 둔 마지막 자리를 쓴다 - 반경 26m 짜리 관심 영역에 한 프레임 낡은 좌표는
      //   아무 차이도 안 만든다.
      if (enemy) {
        if (net.isHost) {
          aoi.length = 0;
          if (selfOK) aoi.push(selfX, selfZ);
          for (const [, p] of peers) aoi.push(p.tgt.x, p.tgt.z);
          enemy.tickHost(txNow, aoi, sendEn);
        } else {
          // 소식이 끊겼는지 보고, 내가 친 주장을 방장에게 내보낸다(2차).
          enemy.tickGuest(txNow, sendEn);
        }
      }
      if (txNow - lastSendMs < 1000 / SEND_HZ) return;
      lastSendMs = txNow;
      const s = getSelf();
      if (!s) return;
      myMap = s.map;
      selfX = s.x; selfZ = s.z; selfOK = true;
      txCount++;
      // ★sh(화살 발사)는 **막 쏜 뒤 0.6초 동안만** 값이 있고 그 밖에는 null 이다.
      //   칼잡이 판에서는 늘 null 이라 소식 크기가 예전 그대로다.
      net.send({ t: 'st', n: ++txSeq, x: s.x, y: s.y, z: s.z, r: s.yaw,
                 c: s.clip, p: s.pt, ts: s.ts, s: s.atk, k: s.char, m: s.map,
                 sh: s.sh || undefined });
    },

    dispose() {
      dead = true;
      for (const id of [...peers.keys()]) despawn(id);
      if (fx) fx.dispose();
      if (net) { try { net.send({ t: 'bye' }); } catch (_) {} net.close(); net = null; }
      say('');
    },

    // 검증 창구. 남의 아바타가 안 보이는 원인은 여럿이다(연결·좌표·클립·로드 실패)
    // 이고 눈으로는 못 가른다. window.__mp.list 로 숫자를 본다.
    // ★HANDOFF 의 런타임 창구 관례를 따른다(window 노출, 상수가 아니다).
    // 네트워크 계측. 렉의 원인을 가르는 첫 숫자다.
    //   rxHz 가 15 근처   -> 네트워크는 멀쩡하다(느리면 받는 쪽 성능 또는 렌더 문제)
    //   rxHz 가 뚝 낮다   -> 보내는 쪽이 멈춘 것(창이 백그라운드면 rAF 가 초당 1회로 떨어진다)
    //   gapMax 가 크다    -> 순간 끊김. 값이 곧 멈춘 시간(ms)이다
    //   stale 이 늘어난다 -> 순서가 뒤바뀐 소식이 실제로 오고 있다(unreliable 채널의 정상 동작)
    get net() {
      return {
        fps: fpsVal, route, rxHz: +(rxTimes.length / 2).toFixed(1), rx: rxCount, tx: txCount,
        gapMaxMs: Math.round(rxGapMax), stale: rxStale,
        peers: net ? net.count : 1, host: net ? net.isHost : null,
      };
    },
    // ── 요괴가 쫓을 사람들 (2차) ──
    // ★게터다. main.js 가 enemies.update 를 부르는 **그 자리에서** 읽으므로,
    //   미리 만들어 두면 한 프레임 낡은 값이 된다(이 파일의 update 는 그보다 뒤에 돈다).
    // ★내 자리는 안 넣는다 - enemy.js 가 getPlayerPos() 로 이미 알고 있고,
    //   두 곳에서 넣으면 내가 두 번 세어진다.
    get players() {
      players.length = 0;
      if (!net || !enemy) return players;
      let i = 0;
      for (const [id, p] of peers) {
        if (!p.seen) continue;                 // 아직 소식이 한 번도 안 온 사람
        let o = aoi2[i];
        if (!o) { o = { tag: '', x: 0, z: 0, dead: false }; aoi2[i] = o; }
        o.tag = enemy.tagOf(id); o.x = p.tgt.x; o.z = p.tgt.z; o.dead = !!p.dead;
        players.push(o); i++;
      }
      return players;
    },
    // 남의 공격 이펙트 상태(자세한 창구는 window.__mpfx). 여기 둔 이유는
    // "아바타는 보이는데 이펙트가 안 보인다"를 한 화면에서 갈라 보기 위해서다.
    get fx() { return fx ? fx.state : null; },
    // 요괴 동기화 상태(자세한 창구는 window.__mpen). 같은 이유로 여기 한 줄을 둔다.
    get enemy() { return enemy ? enemy.state : null; },
    resetStats() { rxCount = 0; txCount = 0; rxGapMax = 0; rxStale = 0; rxTimes.length = 0; },
    // 내가 남에게 보내고 있는 값. 원격 목록과 나란히 봐야 "누가 안 움직이는지" 가 갈린다.
    get self() { return getSelf(); },
    // 남의 아바타가 실제로 어디에 어떤 크기로 서 있는지(그룹 월드 좌표·모델 스케일).
    get where() {
      const box = new THREE.Box3();
      return [...peers.entries()].map(([id, p]) => {
        const o = {
          id: id.slice(-6),
          group: p.group.position.toArray().map(v => +v.toFixed(2)),
          scale: p.model ? +p.model.scale.x.toFixed(3) : null,
          visible: p.model ? p.model.visible : null,
          meshes: p.model ? (() => { let n = 0; p.model.traverse(q => { if (q.isMesh && q.visible) n++; }); return n; })() : 0,
        };
        if (p.model) {
          o.parentOK = p.model.parent === p.group;
          o.groupInScene = !!p.group.parent;
          p.group.updateMatrixWorld(true);
          box.setFromObject(p.model);
          o.box = box.isEmpty() ? 'empty'
            : [box.min.toArray().map(v => +v.toFixed(2)), box.max.toArray().map(v => +v.toFixed(2))];
          o.layers = p.model.layers.mask;
        }
        return o;
      });
    },
    get list() {
      return [...peers.entries()].map(([id, p]) => ({
        id: id.slice(-6), char: p.char, clip: p.clip, ready: p.ready,
        x: +p.cur.x.toFixed(2), y: +p.cur.y.toFixed(2), z: +p.cur.z.toFixed(2),
        tx: +p.tgt.x.toFixed(2), tz: +p.tgt.z.toFixed(2),
        inScene: !!p.group.parent,
      }));
    },
  };

  window.__mp = api;
  return api;
}
