// ── 전송 계층 ──────────────────────────────────────────────────────────────
// 게임 코드(mp.js)는 **이 파일의 인터페이스만** 본다. 그래야 통로를 갈아끼울 때
// 게임을 안 건드린다. 지금 구현은 WebRTC P2P(PeerJS 공용 시그널링)이고,
// 스팀 출시 때는 이 자리에 Steam Networking 어댑터가 들어온다.
//
//   const net = await createNet({ onMessage, onJoin, onLeave, onStatus })
//   await net.host('A7K2')   // 방장으로 연다
//   await net.join('A7K2')   // 참가한다
//   net.send({ t:'st', ... })
//
// ★모양은 **별(star)** 이다. 방장이 가운데에 있고 참가자는 방장하고만 붙는다.
//   참가자끼리 직접 안 붙는 이유: ①연결 수가 n² 가 아니라 n 이다 ②2단계(호스트 권위)
//   에서 어차피 방장이 판정을 쥐므로 지금 모양을 그대로 쓴다.
//   대신 방장이 **중계**한다 - 참가자 A 의 메시지를 B·C 에게 그대로 넘긴다.
// ★모든 메시지에 `from`(보낸 사람 id)을 전송 계층이 붙인다. 게임 코드는 그걸로
//   누구의 아바타인지 안다. 중계될 때도 원본 from 이 유지된다(방장 id 로 덮으면
//   참가자가 서로를 방장으로 본다).
// ★peerjs 는 **필요할 때만** 읽는다(87KB). 혼자 하는 판에서는 요청이 한 건도 안 나간다.

const LIB = './lib/peerjs.min.js';
// 공용 시그널링에는 남의 게임도 산다. 접두사로 방코드 공간을 갈라 둔다.
const PREFIX = 'sworddemo-';
// 방코드 글자. 0/O·1/I 처럼 헷갈리는 짝은 뺐다(친구에게 불러 줘야 하는 값이다).
const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
// ★참가 대기 시간. 처음엔 8초였는데 **배포본 실측에서 방 여는 데만 10~14초**가
//   걸렸다(무료 공용 시그널링 서버라 붐빈다). 8초면 멀쩡한 방도 "없다"고 튕긴다.
//   기다리는 쪽이 낫다 - 안 되는 경우는 어차피 코드가 틀렸거나 방장이 안 켠 것이다.
const JOIN_TIMEOUT = 25000;

// ── ICE 서버 ─────────────────────────────────────────────────────────────
// ★2026-08-19. **같은 공유기 안의 두 기기가 서로 못 붙는 사고**로 넣었다.
//   크롬은 사생활 보호로 로컬 IP 를 mDNS(`xxxx.local`)로 감춘다. 상대가 그걸
//   해석하지 못하면 같은 LAN 인데도 로컬 경로(host 후보)를 못 쓰고, 공인 IP 로
//   나갔다 돌아오는 길(헤어핀 NAT)을 시도하는데 공유기 상당수가 그걸 지원하지
//   않는다. 그래서 **밖에 있는 친구와는 붙는데 같은 집 안에서는 안 붙는다.**
// ★STUN 은 "내 공인 주소가 뭔지" 만 알려 준다. 길이 아예 없을 때 대신 짐을
//   날라 주는 것은 **TURN** 이고, 지금까지 하나도 설정돼 있지 않았다
//   (PeerJS 기본은 구글 STUN 뿐이다).
// ★TURN 은 남의 무료 서버다. 죽어 있을 수 있고 그래도 게임은 돈다 - 직접 연결이
//   되는 판에서는 애초에 쓰이지 않는다(ICE 가 더 싼 길을 먼저 고른다).
//   스팀으로 가면 이 자리는 밸브의 SDR 릴레이가 대신한다(무료·무제한).
const ICE = {
  iceServers: [
    { urls: ['stun:stun.l.google.com:19302', 'stun:stun1.l.google.com:19302'] },
    // Open Relay (metered.ca) 공개 자격증명. 계정이 필요 없는 공용 TURN 이다.
    { urls: ['turn:openrelay.metered.ca:80', 'turn:openrelay.metered.ca:443',
             'turn:openrelay.metered.ca:443?transport=tcp'],
      username: 'openrelayproject', credential: 'openrelayproject' },
  ],
  // 후보를 다 모으고 고르지 말고, 오는 대로 시도한다(붙는 시간이 짧아진다).
  iceCandidatePoolSize: 4,
};

export function makeRoomCode(n = 4) {
  const a = new Uint8Array(n);
  crypto.getRandomValues(a);
  let s = '';
  for (let i = 0; i < n; i++) s += ALPHABET[a[i] % ALPHABET.length];
  return s;
}

let peerLibP = null;
function loadPeerLib() {
  if (window.Peer) return Promise.resolve(window.Peer);
  if (peerLibP) return peerLibP;
  peerLibP = new Promise((ok, no) => {
    const s = document.createElement('script');
    s.src = LIB;
    s.onload = () => window.Peer ? ok(window.Peer) : no(new Error('peerjs 가 window.Peer 를 안 남겼다'));
    s.onerror = () => no(new Error('peerjs 를 못 읽었다: ' + LIB));
    document.head.appendChild(s);
  });
  return peerLibP;
}

export async function createNet(hooks = {}) {
  const { onMessage, onJoin, onLeave, onStatus } = hooks;
  const say = (text, kind) => { try { onStatus && onStatus(text, kind); } catch (e) { /* 안내가 게임을 멈출 이유는 없다 */ } };

  say('시그널링 서버에 붙는 중…');
  const Peer = await loadPeerLib();

  let peer = null;
  let isHost = false;
  let myId = '';
  let room = '';
  let dead = false;
  const conns = new Map();          // id -> DataConnection

  // ── 들어온 메시지 한 건 ──
  function handle(raw, conn) {
    if (dead || !raw || typeof raw !== 'object') return;
    const from = raw.from || conn.metadata?.id || conn.peer;
    // 방장이면 다른 참가자에게 그대로 넘긴다. **원본 from 을 유지한다.**
    if (isHost) {
      for (const [id, c] of conns) {
        if (id === from || !c.open) continue;
        try { c.send(raw); } catch (e) { /* 끊기는 중인 연결 */ }
      }
    }
    try { onMessage && onMessage(raw, from); } catch (e) { console.warn('[net] onMessage:', e); }
  }

  function wire(conn, id) {
    conns.set(id, conn);
    conn.on('data', d => handle(d, conn));
    conn.on('close', () => drop(id));
    conn.on('error', e => { console.warn('[net] conn error', id, e); drop(id); });
  }

  function drop(id) {
    if (!conns.has(id)) return;
    conns.delete(id);
    try { onLeave && onLeave(id); } catch (e) { /* 무시 */ }
    if (!isHost && id === PREFIX + room) {
      say('방장이 나갔다. 연결이 끊겼다.', 'err');
    }
  }

  // peer 객체 하나를 세운다. id 를 주면 그 id 를 점유한다(방장).
  function openPeer(wantId) {
    return new Promise((ok, no) => {
      const p = wantId ? new Peer(wantId, { config: ICE }) : new Peer({ config: ICE });
      let settled = false;
      p.on('open', id => { if (!settled) { settled = true; ok({ p, id }); } });
      p.on('error', e => {
        if (!settled) { settled = true; try { p.destroy(); } catch (_) {} no(e); return; }
        // 연 뒤의 에러는 치명적이지 않은 것이 섞여 있다(상대가 사라진 경우 등)
        console.warn('[net] peer error:', e && e.type, e);
        if (e && (e.type === 'network' || e.type === 'server-error' || e.type === 'socket-error')) {
          say('시그널링 서버와 끊겼다.', 'err');
        }
      });
      p.on('disconnected', () => { if (!dead) { say('연결이 끊겼다. 다시 붙는 중.', 'warn'); try { p.reconnect(); } catch (_) {} } });
    });
  }

  const api = {
    get id() { return myId; },
    get isHost() { return isHost; },
    get room() { return room; },
    get count() { return conns.size + 1; },      // 나까지 센다
    peers() { return [...conns.keys()]; },

    // ── 방장 ──
    // 방코드를 안 주면 만들어서 돌려준다. 이미 쓰이는 코드면 다른 코드로 몇 번 더 시도한다.
    async host(code) {
      isHost = true;
      say('방을 여는 중… 공용 서버라 십여 초 걸릴 수 있다.');
      for (let attempt = 0; attempt < 5; attempt++) {
        room = (code && attempt === 0) ? String(code).toUpperCase() : makeRoomCode();
        try {
          const r = await openPeer(PREFIX + room);
          peer = r.p; myId = r.id;
          peer.on('connection', conn => {
            conn.on('open', () => {
              wire(conn, conn.peer);
              say('한 명 들어왔다.', 'ok');
              try { onJoin && onJoin(conn.peer); } catch (e) { /* 무시 */ }
            });
          });
          say('방 ' + room + ' 을 열었다. 친구에게 코드를 알려줘.', 'ok');
          return room;
        } catch (e) {
          // 그 코드가 이미 살아 있다. 다른 코드로 다시.
          if (e && e.type === 'unavailable-id') continue;
          throw e;
        }
      }
      throw new Error('빈 방코드를 못 찾았다(5번 시도)');
    },

    // ── 참가 ──
    async join(code) {
      isHost = false;
      room = String(code || '').toUpperCase().trim();
      if (!room) throw new Error('방코드가 비었다');
      say('방 ' + room + ' 을 찾는 중… 공용 서버라 십여 초 걸릴 수 있다.');
      const r = await openPeer(null);
      peer = r.p; myId = r.id;
      const target = PREFIX + room;
      return new Promise((ok, no) => {
        // ★★`reliable: true` 를 쓰면 안 된다(2026-08-19 렉 신고의 첫 용의자).
        //   reliable 채널은 TCP 처럼 **순서 보장 + 재전송**이라, 패킷 하나가 유실되면
        //   그 뒤 메시지가 전부 줄을 서서 기다린다(head-of-line blocking).
        //   위치 스트림은 "최신 값만 중요한" 데이터라 정확히 반대 성질이 필요하다 -
        //   한 장 잃으면 그냥 버리고 다음 장을 즉시 받는 쪽이 훨씬 부드럽다.
        //   대신 순서가 뒤바뀔 수 있으므로 **받는 쪽이 옛 소식을 버려야 한다**
        //   (mp.js 의 msg.n 검사. 없으면 캐릭터가 뒤로 튄다).
        //   퇴장(bye)이 유실돼도 conn.on('close') 가 잡으므로 안전하다.
        const conn = peer.connect(target, { reliable: false });
        // ★8초. PeerJS 는 상대가 없어도 connect() 가 곧바로 실패하지 않는다.
        //   기다려 주지 않으면 "방이 없다"와 "느리다"를 구분 못 한다.
        const timer = setTimeout(() => {
          if (!conns.has(target)) {
            try { conn.close(); } catch (_) {}
            no(new Error('방 ' + room + ' 에 못 붙었다. 코드가 맞는지, 방장이 켜 뒀는지 확인해줘.'));
          }
        }, JOIN_TIMEOUT);
        conn.on('open', () => {
          clearTimeout(timer);
          wire(conn, target);
          say('방 ' + room + ' 에 들어왔다.', 'ok');
          try { onJoin && onJoin(target); } catch (e) { /* 무시 */ }
          ok(room);
        });
        conn.on('error', e => { clearTimeout(timer); no(e); });
      });
    },

    // ── 보내기 ──
    // 참가자는 방장에게만 보낸다(방장이 나머지에게 뿌린다).
    send(obj) {
      if (dead || !obj) return;
      obj.from = myId;
      for (const [, c] of conns) {
        if (!c.open) continue;
        try { c.send(obj); } catch (e) { /* 끊기는 중 */ }
      }
    },

    // ── 어떤 길로 붙었나 ──
    // host  = 같은 망에서 직접 (제일 빠르다)
    // srflx = NAT 을 뚫고 직접 (보통)
    // relay = TURN 서버가 짐을 날라 준다 (지연이 늘지만 안 붙던 판이 붙는다)
    // ★같은 공유기 안의 두 기기가 relay 로 붙는 것은 정상이다 - 크롬이 로컬 IP 를
    //   mDNS 로 감춰서 host 후보를 못 쓰는 경우가 있다(이 파일 머리 ICE 주석).
    async route() {
      const c = [...conns.values()].find(x => x && x.peerConnection);
      if (!c) return '연결없음';
      try {
        const stats = await c.peerConnection.getStats();
        let sel = null; const cand = {};
        stats.forEach(r => {
          if (r.type === 'candidate-pair' && r.state === 'succeeded' &&
              (r.nominated || r.selected) && (!sel || r.priority > sel.priority)) sel = r;
          if (r.type === 'local-candidate' || r.type === 'remote-candidate') cand[r.id] = r;
        });
        if (!sel) return c.peerConnection.iceConnectionState || '탐색중';
        const t = x => (x && x.candidateType) || '?';
        return t(cand[sel.localCandidateId]) + '/' + t(cand[sel.remoteCandidateId]);
      } catch (e) { return '알수없음'; }
    },

    close() {
      dead = true;
      for (const [, c] of conns) { try { c.close(); } catch (_) {} }
      conns.clear();
      if (peer) { try { peer.destroy(); } catch (_) {} peer = null; }
    },
  };

  return api;
}
