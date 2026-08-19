// ── 멀티: 요괴 동기화의 전송 정책 (2단계 1차 + 2차) ──────────────────────────
//
// 이 파일이 정하는 것은 **언제·누구에게·얼마나 보낼까** 하나뿐이다.
// 무엇을 어떻게 접느냐(양자화·신원·적용)는 enemy.js 가 안다(그 파일 NET_* 머리 주석).
// 통로는 net.js 가 안다. 셋이 서로의 안을 안 들여다본다.
//
//   방장  : 매 프레임 tickHost() -> 때가 되면 send({t:'en', ...}) 한 건
//   참가자: 받은 소식을 recv() 로 흘린다 -> enemies.netEvent / netApply
//
// ── 2차에 늘어난 것 (소식 **종류는 하나만** 늘었다) ──
//   ① 참가자 -> 방장  {t:'eh', n, c:[...]}  「몇 번 요괴를 어디서 쳤다」는 **주장**
//   ② 방장 -> 전원    기존 'en' 에 두 칸
//        eb : 사건의 **주인**(누가 때렸나). 방장 것이면 아예 안 싣는다
//        h  : **사람이 맞았다**는 통보(그 사람만 자기 체력에 적용한다)
//   새 메시지 종류를 하나로 묶은 이유: 소식이 늘 때마다 순서·유실·중복 규칙을 한 벌씩
//   더 만들게 되고, 이 레포는 그런 규칙이 두 벌이 되면 반드시 어긋난다는 걸 배웠다.
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
// ── 2차: 주장(참가자 -> 방장) ──
// ★주기를 아바타 소식(15Hz)에 맞춘다. 주장은 **때린 그 프레임에 바로** 나가야 하고
//   (아래 CLAIM_MIN_MS), 그 뒤 창이 닫힐 때까지 되풀이해 실어 유실을 메운다.
const CLAIM_HZ = 15;
const CLAIM_MIN_MS = 30;    // 새 주장이 생겼을 때의 최소 간격(3연타가 프레임마다 나가지 않게)
const CLAIM_KEEP_MS = 400;  // 이만큼 되풀이해 싣는다. enemy.js CLAIM_MAX_MS 와 같은 값이다
const CLAIM_MAX = 12;       // 그 창에 담는 주장 수 상한(3연타 x 여러 마리를 덮는다)
const CLAIM_STRIDE = 13;    // [id, sid, kind, lvl, age, x,y,z, nx,ny,nz, kx,kz]
// 기술 이름을 숫자로 접는다. **표를 두 벌로 만들지 않으려고** 한 배열에서 양방향을 뽑는다.
const KINDS = ['Attack', 'Heavy', 'Wide', 'Arrow'];
// ── 2차: 피해 통보(방장 -> 그 사람) ──
// 요괴가 남을 때린 사건. 사건(타격)과 같은 수법으로 되풀이해 싣고 번호로 중복을 버린다.
// ★한 건이 드물다(요괴 한 마리가 1.2초에 한 번). 그래서 정수로 촘촘히 접지 않고
//   읽히는 모양 그대로 둔다 - 여기서 아끼는 바이트보다 나중에 읽는 사람의 시간이 비싸다.
const HURT_KEEP_MS = 500;
const HURT_MAX = 8;
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

// peerjs id 의 뒤 여섯 자. 사건의 주인·피해 통보의 수신자를 가리키는 이름이다.
// ★한 곳에서만 만든다. 두 곳에서 자르면 한쪽이 다섯 자가 되는 날 아무도 못 찾는다.
function shortTag(id) { return id ? String(id).slice(-6) : ''; }

export function createEnemySync(ctx) {
  const enemies = ctx.enemies;
  // 내가 어느 층에 있나. 층이 다르면 **자리 번호가 다른 맵을 가리킨다** -
  // 던전 24자리와 초원 39자리는 0번부터 겹치므로, 그대로 받으면 던전 고블린이
  // 초원 좌표에 선다(그림이 깨지는 것보다 조용히 틀리는 쪽이라 더 나쁘다).
  const getMap = ctx.getMap || (() => '');

  const EVS = enemies.netEvStride;      // 사건 한 건의 칸 수
  const EVQ = enemies.netEvQ;           // 사건 좌표 눈금

  // 나를 가리키는 짧은 이름. 사건의 주인(by)·피해 통보의 수신자를 이걸로 적는다.
  // ★mp.js 가 붙는 순간 세운다(그 전에는 ''). enemy.js 에도 같은 값을 넣어 준다 -
  //   그래야 확정본이 왔을 때 "내가 때린 것인가"를 그쪽에서 혼자 가릴 수 있다.
  let myTag = '';
  const isHost = !!ctx.isHost;

  // ── 방장 ──
  let seq = 0, lastMs = 0, lastFullMs = 0, evId = 0, lastUrgMs = 0;
  let urgent = false;               // 처치가 생겼다 = 주기를 기다리지 말고 내보내라
  const evRing = [];                    // { id, t, a:[...], by } 최근 사건
  const buf = [];                       // netScan 이 채우는 평면 배열(재사용)
  let txN = 0, txFull = 0;
  // 2차: 사람이 맞았다는 통보 링. { id, t, tag, dmg, x, z }
  const hurtRing = [];
  let hurtId = 0;
  // 2차: 참가자별로 이미 적용한 주장 번호. 채널이 unreliable 이라 **순서가 뒤바뀐다** -
  // "마지막 번호보다 작으면 버린다"로 두면 뒤늦게 온 4번이 5번에 밀려 영영 죽는다.
  // 그래서 32칸 창(id & 31)에 번호를 그대로 적어 둔다. 되풀이 창(400ms)보다 넉넉하다.
  const claimSeen = new Map();      // from -> Int32Array(32)
  let claimRx = 0, claimDup = 0, claimApplied = 0;

  // ── 참가자 ──
  let lastN = -1, lastEv = 0, rxN = 0, stale = 0, evApplied = 0;
  let badMap = false;               // 층이 다르다 = 이 방의 요괴 소식은 통째로 버린다
  let lastRxMs = 0;                 // 마지막으로 요괴 소식이 온 시각(벽시계)
  let reverted = false;             // 시간 그물에 걸려 내 AI 로 떨어져 있나
  let revertN = 0, backN = 0;
  // 소식이 제일 오래 끊겼던 시간. mp.js 가 아바타 스트림에 같은 값을 두고 있다 -
  // "네트워크가 느린 것"과 "보내는 쪽이 멎은 것"을 이 한 수로 가른다.
  let rxGapMax = 0;
  // 2차(참가자): 내가 친 주장. { id, t, sid, kind, lvl, x,y,z, nx,ny,nz, kx,kz }
  const claimRing = [];
  let claimSeq = 0, claimTxN = 0, lastClaimMs = 0, claimUrgent = false, claimBytes = 0;
  let hurtLast = 0, hurtApplied = 0;    // 받은 피해 통보의 마지막 번호·적용 수
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
      // ★방장만 사건을 낸다. 참가자 화면에서도 onHit 은 도는데(예측·확정 손맛),
      //   그건 소식이 아니다 - 여기서 안 막으면 참가자가 방장에게 사건을 되쏜다.
      if (!isHost) return;
      if (!h || h.sid === undefined || h.sid < 0) return;
      // 예측은 소식이 아니다(애초에 참가자에게서만 난다. 방어로 한 번 더 막는다).
      if (h.predicted) return;
      evId++;
      const a = [
        evId, h.sid, h.kill ? 1 : 0,
        Math.round(h.x * EVQ), Math.round(h.y * EVQ), Math.round(h.z * EVQ),
        Math.round(h.dmg || 0),
        Math.round(h.nx * 100), Math.round(h.ny * 100), Math.round(h.nz * 100),
        Math.round(h.kx * 100), Math.round(h.kz * 100),
      ];
      // ★by = 이 한 대의 주인. '' 이면 방장이라 **아예 안 싣는다**(아래 tickHost).
      //   참가자가 벤 것일 때만 열두 바이트 남짓이 는다.
      evRing.push({ id: evId, t: performance.now(), a, by: h.by || '' });
      if (evRing.length > EV_MAX) evRing.shift();
      // ★처치는 여태처럼 앞당긴다. **남이 때린 한 대**도 같이 앞당긴다 -
      //   그 사람에게는 이 소식이 곧 "내 칼이 먹혔다"의 확정본이라, 100ms 주기를
      //   기다리게 두면 그만큼이 통째로 조작감에 붙는다.
      //   실측(2026-08-20): 앞당기기 전 주장->확정 중앙 207ms · 90% 312ms 였다.
      if (h.kill || h.by) urgent = true;
    },

    // ── 방장: 요괴가 **남**을 때린 그 프레임 ──
    // enemy.js 가 onNetHurt 으로 넘긴다. 체력은 그 사람이 자기 규칙(무적·새는 통·
    // 넉백)으로 깎는다 - 여기서 하는 일은 "얼마짜리를 어디서 맞았다"를 전하는 것뿐이다.
    onNetHurt(tag, dmg, x, z) {
      if (!isHost || !tag) return;
      hurtId++;
      hurtRing.push({ id: hurtId, t: performance.now(), tag,
                      dmg: Math.round(dmg * 10) / 10,
                      x: Math.round(x * EVQ), z: Math.round(z * EVQ) });
      if (hurtRing.length > HURT_MAX) hurtRing.shift();
      // ★사람이 맞는 건 처치만큼 급하다. 100ms 를 기다리면 예비 자세 -> 타격의
      //   박자가 화면에서 그만큼 어긋난다(내 화면에선 이미 맞았는데 소리가 늦는다).
      urgent = true;
    },

    // ── 참가자: 내가 요괴를 쳤다는 주장 ──
    // enemy.js 의 예측(resolveHit predictOnly)이 스윙마다 한 번씩 넘긴다.
    onClaim(c) {
      if (isHost || !c) return;
      claimSeq++;
      claimRing.push({ id: claimSeq, t: performance.now(),
                       sid: c.sid, kind: c.kind, lvl: c.lvl,
                       x: c.x, y: c.y, z: c.z,
                       nx: c.nx, ny: c.ny, nz: c.nz, kx: c.kx, kz: c.kz });
      if (claimRing.length > CLAIM_MAX) claimRing.shift();
      claimUrgent = true;
    },

    // ── 방장: 매 프레임 ──
    // aoi = [x,z, x,z, ...] 사람들이 서 있는 자리(내 자리 + 남의 자리). mp.js 가 채운다.
    tickHost(nowMs, aoi, send) {
      // ── 두 박자로 나눠 돈다 (2차) ──
      // ★상태(요괴 자리·체력)는 10Hz 그대로. 사건(타격·처치·사람이 맞았다)만
      //   급할 때 앞당긴다. **앞당긴 소식에는 상태를 안 싣는다** - 그러면
      //   ①한 건이 열 배 작고 ②상태 스트림의 박자가 안 흔들린다.
      //   1차는 급한 소식에도 상태를 통째로 실어 보냈다(그때는 급한 게 처치뿐이라
      //   1초에 한두 번이었지만, 2차부터는 남의 칼질마다 걸린다).
      const due = nowMs - lastMs >= 1000 / SEND_HZ;
      const hot = urgent && (nowMs - lastUrgMs) >= URGENT_MIN_MS;
      if (!due && !hot) return false;
      if (hot) { urgent = false; lastUrgMs = nowMs; }
      const msg = { t: 'en', n: ++seq };
      if (due) {
        lastMs = nowMs;
        const full = nowMs - lastFullMs >= FULL_MS;
        if (full) { lastFullMs = nowMs; txFull++; }
        // ★훑어서 만든다(enemy.js netScan). 전수일 때만 관심 영역을 끈다.
        enemies.netScan(buf, aoi, full ? -1 : AOI_R * AOI_R);
        msg.f = full ? 1 : 0;
        msg.d = buf.slice();
        // 층 이름은 **전수 소식에만** 싣는다(1초에 한 번). 근거리 소식마다 실으면
        // 한 건이 10바이트씩 무거워지는데, 층은 판 중간에 안 바뀐다.
        // ★첫 소식은 언제나 전수다(lastFullMs 가 0 에서 시작한다) = 검사가 곧바로 걸린다.
        if (full) msg.m = getMap();
      }
      // 사건은 창(0.5초) 안의 것을 **되풀이해서** 싣는다. 채널이 unreliable 이라
      // 한 장이 유실되면 처치가 통째로 사라진다(번호로 중복을 버리므로 다섯 번
      // 실려도 한 번만 난다. mp.js 의 화살과 같은 수법이다).
      let ev = null, evBy = null;
      for (let i = 0; i < evRing.length; i++) {
        if (nowMs - evRing[i].t > EV_KEEP_MS) continue;
        if (!ev) ev = [];
        const at = ev.length / EVS;                 // 이 사건이 몇 번째로 실리나
        for (let k = 0; k < EVS; k++) ev.push(evRing[i].a[k]);
        // ★주인은 **드문드문**(sparse) 싣는다. 방장이 다 벤 판(대부분)에서는 이 칸이
        //   통째로 없다 = 1차와 바이트가 같다. 참가자가 벤 사건에만 [자리, 이름]이 붙는다.
        if (evRing[i].by) { if (!evBy) evBy = []; evBy.push(at, evRing[i].by); }
      }
      while (evRing.length && nowMs - evRing[0].t > EV_KEEP_MS) evRing.shift();
      if (ev) msg.e = ev;
      if (evBy) msg.eb = evBy;
      // 사람이 맞았다는 통보도 같은 수법이다(창 안의 것을 되풀이해 싣고 번호로 중복을 버린다).
      let hu = null;
      for (let i = 0; i < hurtRing.length; i++) {
        const h = hurtRing[i];
        if (nowMs - h.t > HURT_KEEP_MS) continue;
        if (!hu) hu = [];
        hu.push([h.id, h.tag, h.dmg, h.x, h.z]);
      }
      while (hurtRing.length && nowMs - hurtRing[0].t > HURT_KEEP_MS) hurtRing.shift();
      if (hu) msg.h = hu;
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
        // 사건의 주인 표. 드문드문 실려 오므로 자리 번호 -> 이름으로 편다.
        let byAt = null;
        if (msg.eb) { byAt = new Map(); for (let k = 0; k + 1 < msg.eb.length; k += 2) byAt.set(msg.eb[k], msg.eb[k + 1]); }
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
            // ★없으면 방장 것이다. 이 한 칸이 "내가 잡았다"의 근거다.
            by: byAt ? (byAt.get(o / EVS) || '') : '',
          });
          evApplied++;
        }
      }
      // ── 내가 맞았다 ──
      // ★번호가 뒷걸음질하면 버린다(사건과 같은 규칙). 남에게 온 통보는 그냥 지나간다 -
      //   별 구조라 방장의 소식이 전원에게 가고, 각자 자기 것만 집어 든다.
      if (msg.h) {
        for (let i = 0; i < msg.h.length; i++) {
          const h = msg.h[i];
          if (!h || h[1] !== myTag) continue;
          if (h[0] <= hurtLast) continue;
          hurtLast = h[0];
          enemies.netHurt(h[2], h[3] / EVQ, h[4] / EVQ);
          hurtApplied++;
        }
      }
      if (msg.d) enemies.netApply(msg.d, msg.f === 1);
    },

    // ── 방장: 참가자의 주장 한 건 ──
    // px·pz = mp.js 가 들고 있는 **그 사람의 마지막 좌표**. 상식 검사(거리)의 자다.
    // ★판정은 안 한다. enemy.js 가 자기 자로 재고(거리·묵은 정도) 통과한 것만
    //   자기 판정 자리로 흘린다 - 이 파일은 여전히 전송 정책만 안다.
    recvClaim(msg, from, px, pz) {
      if (!isHost || !msg || msg.t !== 'eh' || !msg.c || px === undefined) return 0;
      const c = msg.c;
      let seen = claimSeen.get(from);
      if (!seen) { seen = new Int32Array(32); claimSeen.set(from, seen); }
      let n = 0;
      for (let o = 0; o + CLAIM_STRIDE <= c.length; o += CLAIM_STRIDE) {
        const id = c[o];
        claimRx++;
        // 32칸 창. 같은 주장이 최대 여섯 번 실려 온다(400ms x 15Hz).
        if (seen[id & 31] === id) { claimDup++; continue; }
        seen[id & 31] = id;
        n += enemies.netClaim({
          sid: c[o + 1], kind: KINDS[c[o + 2]] || 'Attack', lvl: c[o + 3], age: c[o + 4],
          x: c[o + 5] / EVQ, y: c[o + 6] / EVQ, z: c[o + 7] / EVQ,
          nx: c[o + 8] / 100, ny: c[o + 9] / 100, nz: c[o + 10] / 100,
          kx: c[o + 11] / 100, kz: c[o + 12] / 100,
          px, pz, by: shortTag(from),
        });
      }
      claimApplied += n;
      return n;
    },

    // ── 참가자: 매 프레임 ──
    // 소식이 끊긴 지 오래면 내 AI 로 되돌린다(위 DEAD_MS 주석이 근거).
    tickGuest(nowMs, send) {
      // ── 주장 내보내기 (2차) ──
      // ★때린 그 프레임에 바로 나간다(claimUrgent). 15Hz 를 기다리면 평균 33ms 가
      //   그냥 붙는데, 사람이 "때렸는데 늦게 죽는다"를 느끼는 문턱이 100ms 언저리라
      //   그 3분의 1을 여기서 버릴 이유가 없다.
      if (send && claimRing.length) {
        const gap = nowMs - lastClaimMs;
        if (gap >= 1000 / CLAIM_HZ || (claimUrgent && gap >= CLAIM_MIN_MS)) {
          claimUrgent = false;
          lastClaimMs = nowMs;
          const c = [];
          for (let i = 0; i < claimRing.length; i++) {
            const q = claimRing[i];
            const age = nowMs - q.t;
            if (age > CLAIM_KEEP_MS) continue;
            c.push(q.id, q.sid, Math.max(0, KINDS.indexOf(q.kind)), q.lvl, Math.round(age),
                   Math.round(q.x * EVQ), Math.round(q.y * EVQ), Math.round(q.z * EVQ),
                   Math.round(q.nx * 100), Math.round(q.ny * 100), Math.round(q.nz * 100),
                   Math.round(q.kx * 100), Math.round(q.kz * 100));
          }
          while (claimRing.length && nowMs - claimRing[0].t > CLAIM_KEEP_MS) claimRing.shift();
          if (c.length) {
            const m = { t: 'eh', n: ++claimSeq, c };
            send(m);
            claimTxN++;
            // ★주장 바이트만 따로 센다. note() 는 받은 소식까지 합치므로 그 값으로는
            //   "2차가 얼마나 더 쓰나"를 못 낸다.
            const nb = JSON.stringify(m).length;
            claimBytes += nb;
            note(nb);
          }
        }
      }
      if (reverted || !lastRxMs || nowMs - lastRxMs < DEAD_MS) return false;
      reverted = true; revertN++;
      enemies.setNetMode('local');
      return true;
    },

    // ── 내 짧은 이름 (2차) ──
    // ★peerjs id 는 30자가 넘는다. 사건의 주인·피해 통보 수신자로 그대로 실으면
    //   한 건에 서른 바이트다. 뒤 여섯 자만 쓴다 - 무작위 id 라 2~4명 사이에서
    //   겹칠 일이 없고, mp.js 가 이미 화면 표시에 같은 여섯 자를 쓰고 있다.
    setTag(id) {
      myTag = shortTag(id);
      enemies.setNetTag(myTag);      // enemy.js 가 확정본의 by 와 견줄 값
      return myTag;
    },
    get tag() { return myTag; },
    // 남의 peerjs id 를 같은 자로 접는다. mp.js 가 사람 목록을 만들 때 쓴다 -
    // **자르는 규칙은 이 파일 한 곳**이다(두 곳이면 언젠가 한쪽이 어긋난다).
    tagOf: shortTag,

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
        // ── 2차 ──
        //   claimTx 가 0        -> 예측이 아예 안 돈다(스위치 또는 칼이 안 닿았다)
        //   claimRx 는 느는데 applied 0 -> 방장이 전부 기각했다(enemy.net.claimNo 를 봐라)
        //   hurtRx 가 0         -> 요괴가 나를 아직 안 때렸다(또는 통보가 안 온다)
        tag: myTag, host: isHost,
        claimTx: claimTxN, claimBytes, claimRing: claimRing.length,
        claimRx, claimDup, claimApplied, hurtTx: hurtId, hurtRx: hurtApplied,
        enemy: enemies.net,
      };
    },
  };

  window.__mpen = api;
  return api;
}
