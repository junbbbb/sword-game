// ── 멀티플레이 (1단계: 아바타 공유) ────────────────────────────────────────
// 남의 캐릭터를 내 세계에 세우고 위치·방향·동작을 맞춘다.
//
// ★1단계가 **하지 않는 것**을 먼저 적는다. 요괴는 아직 각자 로컬이다 - 내가 잡은
//   고블린이 네 화면에서는 살아 있다. 같은 맵에서 각자 다른 던전을 도는 셈이고,
//   "같이 뛰어다니는 그림"까지가 이 판의 범위다. 몹을 맞추려면 방장 한 명이
//   enemy.js 를 굴리고 나머지는 그림만 그리는 2단계가 필요하다(작업의 본체는
//   enemy.js 4,004줄에서 판정과 렌더를 갈라내는 일이다).
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

  let net = null;
  // ★송신 주기는 **벽시계**로 잰다. 게임 dt(rawDt)로 재면 안 된다 - 그 값은
  //   main.js 에서 `Math.min(0.05, delta)` 로 잘려 있어서, 프레임이 낮을수록
  //   실제 흐른 시간보다 적게 쌓인다. 실측(2026-08-19 렉 신고): **13.5fps 인 기계가
  //   15Hz 를 시켰는데 6.75Hz 만 보냈다**(delta 0.074 가 0.05 로 잘려 두 프레임에
  //   한 번씩만 문턱을 넘었다). 느린 기계일수록 더 안 보내게 되는 셈이라
  //   상대 화면에서 그 사람만 유독 끊겨 보인다 - 방향이 정확히 반대였다.
  let lastSendMs = 0;
  let mySeq = 0;                 // 동작이 바뀔 때마다 오른다(같은 클립 재발동을 알린다)
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
    if (n > 1) {
      const hz = (rxTimes.length / 2).toFixed(0);      // 최근 2초 평균
      line += '  ·  수신 ' + hz + '/s';
      if (rxGapMax > 400) line += '\n최대 끊김 ' + Math.round(rxGapMax) + 'ms';
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
    }, null, err => {
      console.warn('[mp] 남의 캐릭터를 못 읽었다:', name, err);
    });
  }

  function despawn(id) {
    const p = peers.get(id);
    if (!p) return;
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
      if (!p.seen) {                       // 첫 소식이면 순간이동으로 자리를 잡는다
        p.cur.x = msg.x; p.cur.y = msg.y; p.cur.z = msg.z; p.cur.yaw = msg.r;
        p.seen = true;
      }
      if (msg.c !== p.clip || msg.s !== p.seq) {
        p.clip = msg.c; p.seq = msg.s;
        playOn(p, msg.c);
        if (p.current && typeof msg.p === 'number') p.current.time = msg.p;
      } else if (p.current && typeof msg.p === 'number') {
        // ★3연타는 play() 를 다시 부르지 않고 **클립 시간을 점프**해서 낸다. 이름만
        //   보면 1타 뒤로는 아무 일도 안 일어난 것처럼 보인다. 그래서 재생 시각도 맞춘다.
        //   임계값(0.12초)을 두는 이유는 매 소식마다 되감으면 재생이 뚝뚝 끊기기 때문이다.
        if (Math.abs(p.current.time - msg.p) > 0.12) p.current.time = msg.p;
      }
    } else if (msg.t === 'bye') {
      despawn(from); roster();
    }
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
        onLeave: id => { despawn(id); roster(); },
        onJoin: () => roster(),
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
      roster();
      // 나갈 때 남의 화면에서 내 아바타를 지운다(브라우저를 닫아도 불린다)
      window.addEventListener('pagehide', () => { try { net && net.send({ t: 'bye' }); } catch (_) {} });
      return net.room;
    },

    // 내 동작이 바뀌었다고 알린다(main.js 의 play() 가 부른다)
    bumpSeq() { mySeq++; },

    // 프레임마다. rawDt 를 받는다 - 남의 아바타는 내 히트스톱에 멈추면 안 된다.
    update(rawDt) {
      if (dead) return;
      // 남의 아바타: 목표로 따라붙고 클립을 돌린다
      const k = 1 - Math.exp(-LERP_K * rawDt);
      for (const [, p] of peers) {
        p.cur.x += (p.tgt.x - p.cur.x) * k;
        p.cur.y += (p.tgt.y - p.cur.y) * k;
        p.cur.z += (p.tgt.z - p.cur.z) * k;
        p.cur.yaw = angLerp(p.cur.yaw, p.tgt.yaw, k);
        p.group.position.set(p.cur.x, p.cur.y, p.cur.z);
        p.group.rotation.y = p.cur.yaw;
        if (p.mixer) p.mixer.update(rawDt);
      }
      // 진단 표시는 0.5초마다만 다시 쓴다(매 프레임 DOM 을 쓸 이유가 없다)
      if (net && net.count > 1) {
        hudAcc += rawDt;
        if (hudAcc > 0.5) { hudAcc = 0; roster(); }
      }
      // 내 상태 송신
      if (!net) return;
      const txNow = performance.now();
      if (txNow - lastSendMs < 1000 / SEND_HZ) return;
      lastSendMs = txNow;
      const s = getSelf();
      if (!s) return;
      myMap = s.map;
      txCount++;
      net.send({ t: 'st', n: ++txSeq, x: s.x, y: s.y, z: s.z, r: s.yaw,
                 c: s.clip, p: s.pt, s: mySeq, k: s.char, m: s.map });
    },

    dispose() {
      dead = true;
      for (const id of [...peers.keys()]) despawn(id);
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
        rxHz: +(rxTimes.length / 2).toFixed(1), rx: rxCount, tx: txCount,
        gapMaxMs: Math.round(rxGapMax), stale: rxStale,
        peers: net ? net.count : 1, host: net ? net.isHost : null,
      };
    },
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
