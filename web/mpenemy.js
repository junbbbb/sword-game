// ── 멀티: 요괴 동기화의 전송 정책 (2단계 1차) ─────────────────────────────────
//
// 이 파일이 정하는 것은 **언제·누구에게·얼마나 보낼까** 하나뿐이다.
// 무엇을 어떻게 접느냐(양자화·신원·적용)는 enemy.js 가 안다(그 파일 NET_* 머리 주석).
// 통로는 net.js 가 안다. 셋이 서로의 안을 안 들여다본다.
//
//   방장  : 매 프레임 tickHost() -> 때가 되면 send({t:'en', ...}) 한 건
//   참가자: 받은 소식을 recv() 로 흘린다 -> enemies.netEvent / netApply
//
// ★스위치(MP_ENEMY_ON)의 정의는 **main.js 한 곳**이다. 이 파일에는 스위치가 없다 —
//   꺼져 있으면 main.js 가 이 모듈을 아예 안 읽는다.
//
// ── 대역폭을 어떻게 줄였나 (실측 근거) ──
// 필드 맵에 요괴가 39마리다. 전부 15Hz 로 보내면 개체당 8바이트 x 39 x 15 = 4.7KB/s 라
// 아바타 스트림(0.6KB/s)의 여덟 배다. 세 손잡이 중 둘을 썼다:
//   ① 관심 영역(AOI) — 사람이 서 있는 자리 26m 안의 놈만 보낸다. 화면에 실제로 보이는
//      범위가 12~15m(쿼터뷰 dist 34·fov 20)이고 머리 위 판도 28m 에서 끊기므로,
//      26m 밖은 **어차피 아무도 안 본다.** 필드에서 39 -> 3~9마리로 줄었다(실측).
//   ② 주기 — 10Hz. 요괴 최고 속도 2.78m/s 라 한 주기에 28cm 이고, 받는 쪽이 속도를
//      재서 앞을 보므로(enemy.js NET_EXTRAP) 화면에서는 그 처짐이 안 남는다.
//   ③ **변화분만 보내기는 안 썼다.** "바뀔 때만 적기"는 자리를 하나 빠뜨리면 조용히
//      틀리는 방식이고(22차 사고), 관심 영역이 이미 열 배를 줄여 줘서 값이 안 나온다.
//      대신 1초에 한 번 **전수**를 실어 목록을 맞춘다(f=1). 그게 유실의 자가 치유다.
//
// ★주기는 벽시계(performance.now)로 잰다. 게임 dt(rawDt)는 main.js 에서
//   Math.min(0.05, delta) 로 잘려 있어 프레임이 낮을수록 실제보다 느리게 쌓인다.
//   같은 함정을 이 레포에서 이미 두 번 밟았다(송신 주기·경로 조회).

const SEND_HZ = 10;        // 근거리 상태 송신(초당). 위 ② 참조
const FULL_MS = 1000;      // 전수 송신 주기(ms). 목록 맞추기 + 유실 자가 치유
const AOI_R = 26;          // 관심 영역 반경(m). 위 ① 참조
const EV_KEEP_MS = 500;    // 사건(타격·처치)을 몇 ms 동안 되풀이해 실을까
const EV_MAX = 16;         // 그 창에 담는 사건 수 상한(3연타 x 여러 마리를 덮는다)
// ★처치는 **주기를 안 기다리고** 다음 프레임에 바로 나간다.
//   실측(2026-08-20, 두 창 22fps): 주기를 기다리게 두면 죽는 시각 차이가 7~212ms
//   (중앙 80)였다. 100ms 주기 + 양쪽 프레임 간격 45ms 가 그대로 쌓인 값이다.
//   "같이 죽는다"가 이 판의 목적이라 여기만 앞당긴다. 30ms 바닥을 두는 이유는
//   3연타처럼 사건이 몰릴 때 소식이 프레임마다 나가지 않게 하려는 것이다.
const URGENT_MIN_MS = 30;
// ★소식이 이만큼 끊기면 참가자는 자기 AI 로 되돌아간다.
//   방장 창이 갑자기 사라지면(브라우저 강제 종료·전원 차단) WebRTC 의 close 는
//   바로 안 온다 - ICE 가 죽었다고 판정할 때까지 수십 초가 걸린다. 그동안 들판이
//   통째로 얼어붙는다(실측: 방장 창을 닫아도 참가자는 remote 인 채로 남았다).
//   퇴장 인사(bye)와 연결 끊김 둘 다 놓쳤을 때의 마지막 그물이다.
// ★★그물은 **되돌아올 수 있어야 한다.** 5초로 두고 한 방향으로만 만들었더니
//   측정 중 방장 창이 잠깐 멎은 것만으로 참가자가 로컬로 떨어졌고, 소식이 다시
//   와도 영영 안 돌아왔다(그 판의 요괴가 통째로 갈라졌다 — 2026-08-20 실측).
//   그래서 ①8초로 늘리고 ②소식이 다시 오면 그림 모드로 복귀한다.
//   복귀 뒤 1초 안에 전수 소식이 목록을 통째로 맞추므로 갈라진 상태가 안 남는다.
const DEAD_MS = 8000;

export function createEnemySync(ctx) {
  const enemies = ctx.enemies;
  // 내가 어느 층에 있나. 층이 다르면 **자리 번호가 다른 맵을 가리킨다** -
  // 던전 24자리와 초원 39자리는 0번부터 겹치므로, 그대로 받으면 던전 고블린이
  // 초원 좌표에 선다(그림이 깨지는 것보다 조용히 틀리는 쪽이라 더 나쁘다).
  const getMap = ctx.getMap || (() => '');

  const EVS = enemies.netEvStride;      // 사건 한 건의 칸 수
  const EVQ = enemies.netEvQ;           // 사건 좌표 눈금

  // ── 방장 ──
  let seq = 0, lastMs = 0, lastFullMs = 0, evId = 0;
  let urgent = false;               // 처치가 생겼다 = 주기를 기다리지 말고 내보내라
  const evRing = [];                    // { id, t, a:[...] } 최근 사건
  const buf = [];                       // netScan 이 채우는 평면 배열(재사용)
  let txN = 0, txFull = 0;

  // ── 참가자 ──
  let lastN = -1, lastEv = 0, rxN = 0, stale = 0, evApplied = 0;
  let badMap = false;               // 층이 다르다 = 이 방의 요괴 소식은 통째로 버린다
  let lastRxMs = 0;                 // 마지막으로 요괴 소식이 온 시각(벽시계)
  let reverted = false;             // 시간 그물에 걸려 내 AI 로 떨어져 있나
  let revertN = 0, backN = 0;
  // 소식이 제일 오래 끊겼던 시간. mp.js 가 아바타 스트림에 같은 값을 두고 있다 -
  // "네트워크가 느린 것"과 "보내는 쪽이 멎은 것"을 이 한 수로 가른다.
  let rxGapMax = 0;
  // ★lastEv 를 0 에서 시작한다. 사건 번호는 1 부터 나가므로 첫 사건이 안 잘린다.
  //   (-1 로 시작해 첫 발이 통째로 죽은 21차 화살 사고를 다시 밟지 않으려고 적어 둔다.)

  // ── 계측 ──
  // 렉·대역폭 신고를 눈이 아니라 숫자로 가른다. 크기는 JSON 길이로 잰다 —
  // 실제 선로(BinaryPack + SCTP)는 이보다 작다. **위쪽 어림값**이라 안전한 쪽이다.
  const sizeLog = [];                   // [tMs, bytes]
  let bytesTx = 0;

  function note(bytes) {
    const t = performance.now();
    bytesTx += bytes;
    sizeLog.push(t, bytes);
    while (sizeLog.length && sizeLog[0] < t - 2000) { sizeLog.shift(); sizeLog.shift(); }
  }
  function bps() {
    let s = 0;
    for (let i = 1; i < sizeLog.length; i += 2) s += sizeLog[i];
    return Math.round(s / 2);
  }

  const api = {
    // ── 방장: 칼이 닿은 그 프레임 ──
    // main.js 의 onHit 이 그대로 넘긴다. **새 통로를 안 만든다** - 그 콜백이 이미
    // "요괴가 맞았다"의 유일한 출구다.
    onHit(h) {
      if (!h || h.sid === undefined || h.sid < 0) return;
      evId++;
      const a = [
        evId, h.sid, h.kill ? 1 : 0,
        Math.round(h.x * EVQ), Math.round(h.y * EVQ), Math.round(h.z * EVQ),
        Math.round(h.dmg || 0),
        Math.round(h.nx * 100), Math.round(h.ny * 100), Math.round(h.nz * 100),
        Math.round(h.kx * 100), Math.round(h.kz * 100),
      ];
      evRing.push({ id: evId, t: performance.now(), a });
      if (evRing.length > EV_MAX) evRing.shift();
      if (h.kill) urgent = true;
    },

    // ── 방장: 매 프레임 ──
    // aoi = [x,z, x,z, ...] 사람들이 서 있는 자리(내 자리 + 남의 자리). mp.js 가 채운다.
    tickHost(nowMs, aoi, send) {
      const gap = nowMs - lastMs;
      // 처치는 앞당겨 내보낸다(위 URGENT_MIN_MS 주석이 근거).
      if (gap < 1000 / SEND_HZ && !(urgent && gap >= URGENT_MIN_MS)) return false;
      urgent = false;
      lastMs = nowMs;
      const full = nowMs - lastFullMs >= FULL_MS;
      if (full) { lastFullMs = nowMs; txFull++; }
      // ★훑어서 만든다(enemy.js netScan). 전수일 때만 관심 영역을 끈다.
      enemies.netScan(buf, aoi, full ? -1 : AOI_R * AOI_R);
      const msg = { t: 'en', n: ++seq, f: full ? 1 : 0, d: buf.slice() };
      // 층 이름은 **전수 소식에만** 싣는다(1초에 한 번). 근거리 소식마다 실으면
      // 한 건이 10바이트씩 무거워지는데, 층은 판 중간에 안 바뀐다.
      // ★첫 소식은 언제나 전수다(lastFullMs 가 0 에서 시작한다) = 검사가 곧바로 걸린다.
      if (full) msg.m = getMap();
      // 사건은 창(0.5초) 안의 것을 **되풀이해서** 싣는다. 채널이 unreliable 이라
      // 한 장이 유실되면 처치가 통째로 사라진다(번호로 중복을 버리므로 다섯 번
      // 실려도 한 번만 난다. mp.js 의 화살과 같은 수법이다).
      let ev = null;
      for (let i = 0; i < evRing.length; i++) {
        if (nowMs - evRing[i].t > EV_KEEP_MS) continue;
        if (!ev) ev = [];
        for (let k = 0; k < EVS; k++) ev.push(evRing[i].a[k]);
      }
      while (evRing.length && nowMs - evRing[0].t > EV_KEEP_MS) evRing.shift();
      if (ev) msg.e = ev;
      send(msg);
      txN++;
      note(JSON.stringify(msg).length);
      return true;
    },

    // ── 참가자: 소식 한 건 ──
    recv(msg) {
      if (!msg || msg.t !== 'en') return;
      if (badMap) return;
      if (msg.m && getMap() && msg.m !== getMap()) {
        badMap = true;
        console.warn('[mpenemy] 층이 다르다. 요괴 동기화를 멈춘다:', msg.m, '!=', getMap());
        enemies.setNetMode('local');
        return;
      }
      rxN++;
      const nowMs = performance.now();
      if (lastRxMs && nowMs - lastRxMs > rxGapMax) rxGapMax = nowMs - lastRxMs;
      lastRxMs = nowMs;
      // 그물에 걸려 로컬로 떨어져 있었는데 소식이 다시 온다 = 방장이 살아 있었다.
      if (reverted) { reverted = false; backN++; enemies.setNetMode('remote'); }
      note(JSON.stringify(msg).length);
      // ★채널이 unreliable 이라 **순서가 뒤바뀐다.** 뒷걸음질하는 번호는 버린다.
      //   크게 작아진 건 되감기가 아니라 방장의 새로고침이다(mp.js 와 같은 규칙).
      if (typeof msg.n === 'number') {
        if (lastN >= 0 && msg.n <= lastN && lastN - msg.n < 120) { stale++; return; }
        if (msg.n < lastN) lastEv = 0;          // 재접속. 사건 번호도 1 부터 다시 온다
        lastN = msg.n;
      }
      // ★사건을 **먼저** 적용한다. 전수 소식이 먼저 들어가면 죽은 놈이 시체 없이
      //   조용히 사라진다(처치 연출이 통째로 빠진다).
      if (msg.e) {
        const e = msg.e;
        for (let o = 0; o + EVS <= e.length; o += EVS) {
          const id = e[o];
          if (id <= lastEv) continue;          // 같은 사건이 최대 다섯 번 실려 온다
          lastEv = id;
          enemies.netEvent({
            sid: e[o + 1], kill: e[o + 2] === 1,
            hx: e[o + 3] / EVQ, hy: e[o + 4] / EVQ, hz: e[o + 5] / EVQ,
            dmg: e[o + 6],
            nx: e[o + 7] / 100, ny: e[o + 8] / 100, nz: e[o + 9] / 100,
            kx: e[o + 10] / 100, kz: e[o + 11] / 100,
          });
          evApplied++;
        }
      }
      if (msg.d) enemies.netApply(msg.d, msg.f === 1);
    },

    // ── 참가자: 매 프레임 ──
    // 소식이 끊긴 지 오래면 내 AI 로 되돌린다(위 DEAD_MS 주석이 근거).
    tickGuest(nowMs) {
      if (reverted || !lastRxMs || nowMs - lastRxMs < DEAD_MS) return false;
      reverted = true; revertN++;
      enemies.setNetMode('local');
      return true;
    },

    // 새 사람이 들어왔다. 다음 송신을 전수로 만들어 목록부터 맞춘다.
    forceFull() { lastFullMs = 0; },

    // 방장이 나갔다. 그대로 두면 요괴가 얼어붙으므로 내 AI 로 되돌린다.
    // ★되돌아간 뒤의 요괴는 지금 서 있는 자리에서 이어서 산다(순간이동이 없다).
    // 방장이 인사하고 나갔다(또는 연결이 끊겼다). 그물과 달리 이건 되돌아오지 않는다 -
    // 소식이 다시 올 리가 없기 때문이다.
    hostGone() { lastRxMs = 0; reverted = false; enemies.setNetMode('local'); },

    // 검증 창구. 「안 보인다」의 원인을 가르는 첫 숫자다.
    //   tx/rx 가 0        -> 소식이 아예 안 오간다(연결 또는 스위치)
    //   rx 는 느는데 tracked 0 -> 번호를 모른다(맵이 다르거나 배치가 어긋났다)
    //   stale 이 는다     -> 순서가 뒤바뀐 소식이 실제로 오고 있다(정상)
    //   bps               -> 최근 2초 평균 초당 바이트(JSON 길이 기준 = 위쪽 어림값)
    get state() {
      return {
        hz: SEND_HZ, fullMs: FULL_MS, aoi: AOI_R,
        tx: txN, txFull, rx: rxN, stale, ev: evApplied, evId, urgent,
        bytes: bytesTx, bps: bps(),
        sinceRx: lastRxMs ? Math.round(performance.now() - lastRxMs) : null, deadMs: DEAD_MS,
        reverted, revertN, backN, gapMaxMs: Math.round(rxGapMax), badMap, map: getMap(),
        enemy: enemies.net,
      };
    },
  };

  window.__mpen = api;
  return api;
}
