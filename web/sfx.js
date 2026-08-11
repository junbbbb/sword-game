// 소리. 전부 WebAudio 로 그 자리에서 합성한다. 외부 파일 0개.
//
// 왜 합성인가: 파일을 쓰면 로딩·경로·라이선스가 붙고, 무엇보다 **매번 똑같은 소리**가
// 난다. 한 판에 고블린을 서른 마리 베는 게임에서 같은 명중음이 서른 번 나면 그때부터
// 소리가 아니라 잡음이다. 합성이면 재생마다 피치·필터를 흔들 수 있다.
//
// 오너 지시: 명중음은 "칼로 뭔가 써는 ASMR" 결로.
//   그래서 명중음을 한 덩어리로 안 만든다. **세 겹을 10~20ms 씩 어긋나게** 깐다.
//     1) 공기 가르는 소리 (40ms, 고역)
//     2) 살 가르는 소리   (60ms, 1.2~2.4kHz) ← 여기가 ASMR 의 정체다
//     3) 저역 퍽          (100ms, 90~120Hz)
//   한 번에 겹쳐 치면 "퍽" 하나로 뭉쳐서 밋밋해진다.
//
// ★★자동재생 정책: 사용자 입력 전에는 AudioContext 가 suspended 라 아무 소리도 안 난다.
//   "구현했는데 소리가 안 나는" 상태의 100% 원인이 이것이다. 그래서 컨텍스트를
//   **첫 입력에서 만들고**(keydown/pointerdown/touchstart), 이미 있으면 resume 한다.
//   unlock() 이 한 번도 안 불린 상태에서 play 를 부르면 그냥 조용히 무시한다.

const MASTER = 0.55;
// 동시 발성 상한. 넘으면 제일 오래된 것부터 끊는다.
// ★6 -> 9 (2026-08-10). 처치음이 6겹을 통째로 쓰고 있어서, 여기에 잔향 꼬리와
//   요괴 비명을 얹자마자 **처치음의 첫 두 겹(공기·살)이 20ms 페이드로 잘려 나갔다.**
//   ASMR 결의 정체가 그 두 겹이라 상한을 올리는 게 맞다. 9겹이라도 전부 0.05~0.9초
//   짜리 짧은 소리고 컴프레서를 지나므로 뭉치지 않는다.
const MAX_VOICES = 9;
const STREAK_WINDOW = 2.0;   // 이 시간 안에 또 잡으면 처치음이 반음 올라간다
const STREAK_MAX = 8;
const DEMON_CRY_GAP = 0.09;  // 이 간격 안의 두 번째 비명은 안 낸다(전멸이 합창이 된다)

// ── 들판 앰비언스 ──
// 바람 + 풀벌레 + 이따금 새. 여기도 파일 0개다.
// ★배선: 앰비언스 -> duck -> master. comp(컴프레서)는 **안 지난다.**
//   계속 깔리는 소리를 컴프레서에 넣으면 한 마리 벨 때마다 배경이 같이 눌렸다
//   풀려서 세상이 숨을 쉰다. duck 은 지나게 둔다 - 맞았을 때 배경까지 먹먹해지는 건
//   맞는 그림이다. master 를 지나므로 M 음소거는 그대로 먹는다.
const AMB = 0.10;            // 앰비언스 전체 볼륨. 아주 낮게(0.08~0.12 대역)
const AMB_RISE = 1.4;        // 켜질 때 드는 시간(초). 툭 켜지면 놀란다
const BIRD_MIN = 3.0;        // 새 간격(초)
const BIRD_MAX = 9.0;
const BIRD_FIGHT = 2.6;      // 추격 2마리 이상이면 간격을 이 배수로 늘린다
const BIRD_FIGHT_N = 2;

export function createSfx() {
  let ctx = null;
  let master = null, comp = null, duck = null;
  let muted = false;
  let ready = false;
  const voices = [];         // {node, end, gain}
  let noiseBuf = null;
  let streak = 0, lastKill = -99;
  let tell = null;           // 진행 중인 보스 예고음
  let played = 0;            // 검증용 누적 재생 수
  let ana = null;            // 검증용 레벨 미터(master 뒤)
  let amb = null;            // 앰비언스 노드 묶음. 안 켜졌으면 null
  let birdTimer = 0, birds = 0;
  let lastCry = -99;         // 마지막 요괴 비명 시각(합창 방지)
  let deaths = 0, cries = 0; // 검증용 누적
  // 마지막 스윙이 무엇이었나. **feel.js 가 붓자국 색을 고르는 데 쓴다**
  // (3연타=진홍 / 수면참·횡일섬=감청). 소리와 그림이 같은 신호를 봐야 안 어긋난다.
  let lastSwing = null;

  // ── 시동 ──
  function unlock() {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return false;
      ctx = new AC();
      comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -14; comp.knee.value = 24;
      comp.ratio.value = 5; comp.attack.value = 0.003; comp.release.value = 0.16;
      // 덕킹용 로우패스. 평소엔 열려 있고 피격 때만 150ms 닫는다.
      duck = ctx.createBiquadFilter();
      duck.type = 'lowpass';
      duck.frequency.value = 20000;
      master = ctx.createGain();
      master.gain.value = muted ? 0 : MASTER;
      comp.connect(duck); duck.connect(master); master.connect(ctx.destination);
      // 2초짜리 화이트노이즈 한 장을 돌려 쓴다. 재생마다 시작 지점과 속도를 흔든다.
      const n = Math.floor(ctx.sampleRate * 2);
      noiseBuf = ctx.createBuffer(1, n, ctx.sampleRate);
      const d = noiseBuf.getChannelData(0);
      for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
      // 검증용 레벨 미터. master 뒤라 M 음소거가 진짜 0 을 만드는지 숫자로 보인다.
      ana = ctx.createAnalyser();
      ana.fftSize = 2048;
      master.connect(ana);
      ready = true;
    }
    if (ctx.state === 'suspended') ctx.resume();
    // ★여기서 켠다. unlock 은 첫 입력에서만 불리므로 자동재생 정책에 안 걸린다.
    startAmbience();
    return true;
  }

  function now() { return ctx ? ctx.currentTime : 0; }
  const rnd = (a, b) => a + Math.random() * (b - a);
  const vary = () => 1 + (Math.random() - 0.5) * 0.16;    // 피치 +-8%

  // 보이스 관리. 상한을 넘으면 제일 오래된 것을 20ms 페이드로 끊는다.
  function keep(g, end) {
    voices.push({ g, end });
    for (let i = voices.length - 1; i >= 0; i--) if (voices[i].end < now()) voices.splice(i, 1);
    while (voices.length > MAX_VOICES) {
      const v = voices.shift();
      try {
        v.g.gain.cancelScheduledValues(now());
        v.g.gain.setValueAtTime(v.g.gain.value, now());
        v.g.gain.linearRampToValueAtTime(0.0001, now() + 0.02);
      } catch (e) { /* 이미 끝난 노드 */ }
    }
    played++;
  }

  // ── 벽돌 1: 노이즈 한 덩이 ──
  // t0 부터 dur 동안, type/freq/Q 의 필터를 지나, peak 로 붙었다 사라진다.
  function noise(t0, dur, type, f0, f1, Q, peak, rate) {
    if (!ready) return;
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf;
    src.loop = true;
    src.playbackRate.value = (rate || 1) * vary();
    const bq = ctx.createBiquadFilter();
    bq.type = type; bq.Q.value = Q;
    bq.frequency.setValueAtTime(f0, t0);
    if (f1 && f1 !== f0) bq.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t0 + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), t0 + dur * 0.14);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(bq); bq.connect(g); g.connect(comp);
    src.start(t0, Math.random() * 1.5);
    src.stop(t0 + dur + 0.02);
    keep(g, t0 + dur);
  }

  // ── 벽돌 2: 음정 있는 한 방 ──
  function tone(t0, dur, type, f0, f1, peak) {
    if (!ready) return;
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(f0, t0);
    if (f1 && f1 !== f0) o.frequency.exponentialRampToValueAtTime(Math.max(18, f1), t0 + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), t0 + Math.min(0.012, dur * 0.2));
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g); g.connect(comp);
    o.start(t0); o.stop(t0 + dur + 0.02);
    keep(g, t0 + dur);
  }

  // ── 벽돌 3: 물결 반짝임(콤 필터) ──
  // 노이즈를 짧은 지연 + 되먹임에 통과시키면 금속성 울림이 생긴다. 수면참·횡일섬용.
  function shimmer(t0, dur, delay, peak) {
    if (!ready) return;
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf; src.loop = true;
    src.playbackRate.value = vary();
    const dl = ctx.createDelay(0.05);
    dl.delayTime.value = delay;
    const fb = ctx.createGain(); fb.gain.value = 0.72;
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass'; bp.frequency.value = rnd(1600, 2600); bp.Q.value = 1.2;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(peak, t0 + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(dl); dl.connect(fb); fb.connect(dl);
    dl.connect(bp); bp.connect(g); g.connect(comp);
    src.start(t0, Math.random()); src.stop(t0 + dur + 0.02);
    keep(g, t0 + dur);
  }

  // ── 벽돌 4: 낮은 잔향 꼬리 ──
  // shimmer 와 같은 콤 필터인데 **아래쪽**이다. 지연을 길게(20~40ms) 잡고 저역만
  // 남기면 금속 반짝임이 아니라 "동굴에서 되돌아오는 울림"이 된다.
  // 마지막 일격이 방 안에 남는 소리. 짧은 타격음과 겹쳐야 한 방이 무거워진다.
  function lowTail(t0, dur, delay, peak, fb) {
    if (!ready) return;
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf; src.loop = true;
    src.playbackRate.value = 0.55 * vary();
    const dl = ctx.createDelay(0.2);
    dl.delayTime.value = delay;
    const g2 = ctx.createGain(); g2.gain.value = fb === undefined ? 0.80 : fb;
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass'; lp.frequency.value = rnd(300, 460); lp.Q.value = 0.8;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), t0 + 0.05);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(dl); dl.connect(g2); g2.connect(dl);
    dl.connect(lp); lp.connect(g); g.connect(comp);
    src.start(t0, Math.random()); src.stop(t0 + dur + 0.03);
    keep(g, t0 + dur);
  }

  // -------------------------------------------------------------------------
  // 들판 앰비언스
  // -------------------------------------------------------------------------
  // ★keep() 에 안 넣는다. 앰비언스는 계속 도는 소리라 보이스 상한(6)에 들어가면
  //   요괴를 몇 마리만 베어도 바람이 먼저 끊긴다.
  function startAmbience() {
    if (amb || !ready) return;
    const t = now();
    let nodes = 0;
    const bus = ctx.createGain(); nodes++;
    bus.gain.setValueAtTime(0.0001, t);
    bus.gain.setTargetAtTime(AMB, t, AMB_RISE / 3);
    bus.connect(duck);

    // 바람: 저역만 통과시킨 노이즈. 세기와 밝기를 **주기가 다른 LFO 둘**이 따로 흔든다.
    // 하나만 쓰면 그 주기가 귀에 들려서 바람이 아니라 기계가 된다.
    const wsrc = ctx.createBufferSource(); nodes++;
    wsrc.buffer = noiseBuf; wsrc.loop = true; wsrc.playbackRate.value = 0.62;
    const wlp = ctx.createBiquadFilter(); nodes++;
    wlp.type = 'lowpass'; wlp.frequency.value = 340; wlp.Q.value = 0.5;
    const whp = ctx.createBiquadFilter(); nodes++;
    whp.type = 'highpass'; whp.frequency.value = 70; whp.Q.value = 0.4;   // 우르릉 저역 제거
    const wg = ctx.createGain(); nodes++;
    wg.gain.value = 0.52;
    wsrc.connect(wlp); wlp.connect(whp); whp.connect(wg); wg.connect(bus);
    const lfoA = ctx.createOscillator(); nodes++;
    lfoA.type = 'sine'; lfoA.frequency.value = 0.057;                     // 17.5초 주기
    const lfoAg = ctx.createGain(); nodes++;
    lfoAg.gain.value = 0.30;
    lfoA.connect(lfoAg); lfoAg.connect(wg.gain);
    const lfoB = ctx.createOscillator(); nodes++;
    lfoB.type = 'sine'; lfoB.frequency.value = 0.031;                     // 32초 주기
    const lfoBg = ctx.createGain(); nodes++;
    lfoBg.gain.value = 190;
    lfoB.connect(lfoBg); lfoBg.connect(wlp.frequency);
    wsrc.start(t, Math.random()); lfoA.start(t); lfoB.start(t);

    // 풀벌레: 아주 좁은 고역 대역 + 빠른 떨림. 두 마리(주파수·떨림이 다르다)를 겹친다.
    // ★Q 를 크게 잡으면 통과 에너지가 확 줄어든다. 그래서 게인 숫자가 바람보다 크다.
    //   숫자만 보고 "벌레가 더 크네" 하면 안 된다.
    const bugs = [];
    for (const spec of [[4700, 13.5, 0.26], [6250, 17.3, 0.17]]) {
      const s = ctx.createBufferSource(); nodes++;
      s.buffer = noiseBuf; s.loop = true; s.playbackRate.value = 1 + Math.random() * 0.4;
      const bp = ctx.createBiquadFilter(); nodes++;
      bp.type = 'bandpass'; bp.frequency.value = spec[0]; bp.Q.value = 16;
      const g = ctx.createGain(); nodes++;
      g.gain.value = spec[2];
      const lfo = ctx.createOscillator(); nodes++;
      lfo.type = 'sine'; lfo.frequency.value = spec[1];
      const lg = ctx.createGain(); nodes++;
      lg.gain.value = spec[2] * 0.85;              // 거의 0 까지 떨어뜨린다 = 또르르
      lfo.connect(lg); lg.connect(g.gain);
      s.connect(bp); bp.connect(g); g.connect(bus);
      s.start(t, Math.random()); lfo.start(t);
      bugs.push(g);
    }

    amb = { bus, wind: wg, bugs, nodes };
    scheduleBird(1.5 + Math.random() * 2.5);
  }

  // 지금 쫓아오는 요괴 수. enemy.js 의 검증 창구를 읽는다(3~9초에 한 번만 부른다).
  function chaseCount() {
    try {
      const e = window.__enemy;
      const p = e && e.pathing;
      return p ? (p.chase | 0) : 0;
    } catch (err) { return 0; }
  }

  // 새 지저귐 예약. 전투 중이면 간격을 늘린다(칼 부딪히는데 새가 울면 우습다).
  function scheduleBird(sec) {
    if (birdTimer) clearTimeout(birdTimer);
    birdTimer = setTimeout(() => {
      birdTimer = 0;
      if (!amb) return;
      chirp();
      const k = chaseCount() >= BIRD_FIGHT_N ? BIRD_FIGHT : 1;
      scheduleBird((BIRD_MIN + Math.random() * (BIRD_MAX - BIRD_MIN)) * k);
    }, Math.max(120, sec * 1000));
  }

  // 짧은 지저귐 두세 마디. 마디마다 피치가 오르거나 내린다.
  function chirp() {
    if (!ready || !amb) return;
    const t0 = now();
    const base = rnd(1900, 3900);
    const n = 2 + Math.floor(Math.random() * 3);
    const up = Math.random() < 0.55;
    let t = t0;
    for (let i = 0; i < n; i++) {
      const d = rnd(0.030, 0.070);
      const f0 = base * (1 + i * 0.05) * rnd(0.94, 1.06);
      const f1 = f0 * (up ? rnd(1.25, 1.90) : rnd(0.55, 0.80));
      const o = ctx.createOscillator();
      o.type = (i % 2) ? 'triangle' : 'sine';
      o.frequency.setValueAtTime(f0, t);
      o.frequency.exponentialRampToValueAtTime(f1, t + d);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.55, t + d * 0.22);
      g.gain.exponentialRampToValueAtTime(0.0001, t + d);
      o.connect(g); g.connect(amb.bus);
      o.start(t); o.stop(t + d + 0.02);
      t += d + rnd(0.020, 0.055);
    }
    birds++;
  }

  // -------------------------------------------------------------------------
  // 실제 소리들
  // -------------------------------------------------------------------------

  // 휘두름. 필터 스윕 휘익. 스윙마다 피치가 다르다.
  function swing(power) {
    // ★ready 검사보다 앞이다. 소리가 아직 안 열렸어도 **그림은 색을 골라야 한다**
    lastSwing = { kind: 'light', at: performance.now() };
    if (!ready) return;
    const t = now(), k = power === undefined ? 1 : power;
    const f = rnd(520, 780) * k;
    noise(t, 0.17 / k, 'bandpass', f * 0.55, f * 3.4, 1.5, 0.16 * k, 1);
    noise(t + 0.02, 0.12 / k, 'highpass', 2200, 5200, 0.7, 0.055 * k, 1);
  }

  // 큰 기술(수면참·횡일섬). 더 크고 길게 + 물결 반짝임.
  function heavySwing() {
    // ★여기가 "물의 호흡"의 유일한 표식이다. feel.js 가 이걸 읽어 붓자국을 감청으로
    //   칠한다(1순위는 애니 클립이고 이건 그게 없어졌을 때의 보험).
    lastSwing = { kind: 'heavy', at: performance.now() };
    if (!ready) return;
    const t = now();
    noise(t, 0.34, 'bandpass', 260, 2600, 1.1, 0.24, 0.85);
    noise(t + 0.05, 0.26, 'highpass', 1400, 4800, 0.8, 0.10, 1);
    shimmer(t + 0.06, 0.42, rnd(0.004, 0.009), 0.075);
    tone(t + 0.02, 0.30, 'sine', 120, 58, 0.10);
  }

  // 명중. 세 겹을 어긋나게 깐다(위 주석 참고).
  function hit(power) {
    if (!ready) return;
    const t = now(), k = power === undefined ? 1 : power;
    noise(t, 0.040, 'highpass', 3400, 6200, 0.6, 0.11 * k, 1);              // 공기
    noise(t + 0.014, 0.062, 'bandpass', rnd(2400, 1900), rnd(1300, 1150),   // 살
          2.6, 0.20 * k, 1);
    noise(t + 0.030, 0.10, 'lowpass', rnd(120, 90), 60, 0.9, 0.26 * k, 1);  // 퍽
    tone(t + 0.030, 0.09, 'sine', rnd(118, 92), 52, 0.16 * k);
  }

  // 처치. 명중보다 굵고 젖은 소리 + 낮은 쿵. 연속으로 잡으면 반음씩 올라간다.
  function kill() {
    if (!ready) return;
    const t = now();
    const T = t;
    if (T - lastKill < STREAK_WINDOW) streak = Math.min(STREAK_MAX, streak + 1);
    else streak = 0;
    lastKill = T;
    const semi = Math.pow(2, streak / 12);
    noise(t, 0.050, 'highpass', 2600, 4800, 0.6, 0.10, 1);
    // 젖은 소리 = 대역이 넓고 아래로 미끄러진다
    noise(t + 0.016, 0.15, 'bandpass', 1500 * semi, 520 * semi, 1.4, 0.30, 1);
    noise(t + 0.020, 0.10, 'bandpass', 780 * semi, 300 * semi, 3.2, 0.16, 0.8);
    noise(t + 0.042, 0.20, 'lowpass', 150, 48, 0.8, 0.30, 1);
    tone(t + 0.042, 0.24, 'sine', 92 * semi, 40, 0.24);
    tone(t + 0.030, 0.13, 'triangle', 300 * semi, 150 * semi, 0.09);
    // ★잔향 꼬리(v84 QA S9). 마지막 일격이 "툭" 끊기지 않고 방에 남는다.
    //   0.72초. 처치 간격(연속처치 2초)보다 짧아서 다음 처치와 겹쳐 뭉치지 않는다.
    lowTail(t + 0.05, 0.72, 0.032, 0.085, 0.82);
  }

  // 요괴가 쓰러지는 소리. 처치음(칼이 살을 가른 소리) 위에 얹히는 **그놈의 소리**다.
  // ★오너 지시: 짧게, 톤은 낮게, 잔인하지 않게. 그래서
  //     · 사람 비명 대역(1~3kHz)을 피하고 340 -> 120Hz 로 미끄러지는 낮은 소리
  //     · 0.20초. 길면 고통을 묘사하게 된다
  //     · 대역 좁은 노이즈 한 겹으로 숨 새는 결만 얹는다(피·젖은 소리는 kill 이 낸다)
  //   전멸처럼 한 프레임에 여럿이 죽으면 첫 놈만 운다(DEMON_CRY_GAP).
  function demonDie() {
    if (!ready) return;
    const t = now();
    if (t - lastCry < DEMON_CRY_GAP) return;
    lastCry = t;
    cries++;
    const f = rnd(300, 380);
    tone(t, 0.20, 'triangle', f, f * 0.36, 0.11);
    tone(t + 0.012, 0.16, 'sawtooth', f * 0.5, f * 0.22, 0.045);
    noise(t, 0.13, 'bandpass', rnd(900, 1200), 380, 3.0, 0.075, 1);
  }

  // 무리 전멸. 처치음 위에 낮은 종 하나.
  function wipe() {
    if (!ready) return;
    const t = now();
    tone(t + 0.03, 0.9, 'sine', 196, 190, 0.18);
    tone(t + 0.03, 0.7, 'sine', 294, 292, 0.10);
    noise(t, 0.5, 'lowpass', 200, 60, 0.7, 0.16, 0.7);
  }

  // 플레이어 피격. 둔탁한 쿵 + 전체를 150ms 로우패스로 덕킹.
  function hurt() {
    if (!ready) return;
    const t = now();
    tone(t, 0.22, 'sine', 130, 45, 0.34);
    noise(t, 0.16, 'lowpass', 420, 120, 0.7, 0.24, 1);
    noise(t, 0.05, 'bandpass', 900, 500, 1.4, 0.12, 1);
    try {
      duck.frequency.cancelScheduledValues(t);
      duck.frequency.setValueAtTime(20000, t);
      duck.frequency.exponentialRampToValueAtTime(520, t + 0.02);
      duck.frequency.setValueAtTime(520, t + 0.15);
      duck.frequency.exponentialRampToValueAtTime(20000, t + 0.34);
    } catch (e) { /* 무시 */ }
  }

  // ── 거부음 (2026-08-10 9차. 건틀릿 손맛 8위) ──
  // 심사: "쿨다운 중에 X 를 눌렀는데 아무 일도 안 일어난다. **씹힌 건지 버그인지
  //   구분이 안 된다.**" 못 쓰는 입력에는 반드시 대답이 있어야 한다.
  // 규칙: 이 게임에서 제일 **낮고 짧고 마른** 소리다. 명중음(1.2~2.4kHz 살 가르는 결)과
  //   대역이 겹치면 전투 중에 "뭔가 맞았나?"로 오독된다. 그래서 200Hz 아래 + 0.09초로
  //   끊고, 잔향을 안 붙인다(잔향이 붙으면 '연출'로 읽혀서 거부가 아니게 된다).
  //   두 음을 살짝 어긋나게 깔아 반음 내려앉는 결을 만든다 = "안 된다"의 억양.
  function deny() {
    if (!ready) return;
    const t = now();
    tone(t, 0.075, 'square', 186, 150, 0.055);        // 마른 몸통
    tone(t + 0.012, 0.090, 'sine', 128, 96, 0.085);   // 내려앉는 저음
    noise(t, 0.035, 'lowpass', 300, 140, 0.9, 0.055, 1);
  }

  // ── 대시(회피) ──
  // 짧은 바람 스치는 소리 하나. 휘두름(swing)과 대역을 벌려야(더 높고 더 짧게)
  // "벤 것"과 "피한 것"이 안 헷갈린다. 몸이 지나간 자국이라 저역은 거의 안 준다.
  function dash() {
    if (!ready) return;
    const t = now();
    noise(t, 0.10, 'bandpass', 900, 2600, 1.1, 0.085, 1);
    noise(t + 0.02, 0.075, 'highpass', 2600, 5200, 0.7, 0.045, 1);
    tone(t, 0.06, 'sine', 240, 150, 0.035);
  }

  // ── 플레이어 사망 (v84 QA S2) ──
  // "여섯 번 죽고 한 번도 죽은 줄 몰랐다"의 소리 쪽 답이다.
  // 이 게임에서 **제일 낮고 제일 긴 소리**여야 한다. 그래야 피격(hurt)과 안 헷갈린다.
  //   피격 : 130 -> 45Hz, 0.22초, 덕킹 0.15초
  //   사망 : 72 -> 24Hz, 1.7초, 덕킹 0.9초 + 1.9초에 걸쳐 열림
  // 덕킹을 길게 잡는 게 요점이다. 바람·풀벌레가 통째로 먹먹해지면서 세상이 물러난다
  // (feel.death() 의 0.30배 슬로모와 같은 순간에 걸려서 시간과 소리가 같이 늘어진다).
  function death() {
    if (!ready) return;
    stopTell();
    const t = now();
    deaths++;
    tone(t, 1.70, 'sine', 72, 24, 0.42);            // 바닥으로 꺼지는 저음
    tone(t + 0.02, 1.10, 'triangle', 147, 72, 0.10); // 낮은 종 하나(장송)
    noise(t, 1.20, 'lowpass', 320, 46, 0.7, 0.26, 0.7);
    lowTail(t + 0.06, 1.60, 0.045, 0.13, 0.86);
    try {
      duck.frequency.cancelScheduledValues(t);
      duck.frequency.setValueAtTime(20000, t);
      duck.frequency.exponentialRampToValueAtTime(300, t + 0.06);
      duck.frequency.setValueAtTime(300, t + 0.90);
      duck.frequency.exponentialRampToValueAtTime(20000, t + 2.80);
    } catch (e) { /* 무시 */ }
  }

  // 보스 예고. 예고 시작부터 타격까지 **올라가는 톤**. 소리만으로 피할 수 있어야 한다.
  function bossTell(dur, kind) {
    if (!ready) return;
    stopTell();
    const t = now();
    const base = kind === 'slam' ? 130 : kind === 'charge' ? 190 : 240;
    const o = ctx.createOscillator();
    o.type = 'sawtooth';
    o.frequency.setValueAtTime(base, t);
    o.frequency.exponentialRampToValueAtTime(base * 3.1, t + dur);
    const bq = ctx.createBiquadFilter();
    bq.type = 'lowpass'; bq.Q.value = 6;
    bq.frequency.setValueAtTime(base * 2.4, t);
    bq.frequency.exponentialRampToValueAtTime(base * 7.0, t + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.05, t + dur * 0.3);
    g.gain.exponentialRampToValueAtTime(0.16, t + dur);
    o.connect(bq); bq.connect(g); g.connect(comp);
    o.start(t); o.stop(t + dur + 0.06);
    tell = { o, g };
    keep(g, t + dur);
  }
  function stopTell() {
    if (!tell) return;
    try {
      tell.g.gain.cancelScheduledValues(now());
      tell.g.gain.setValueAtTime(tell.g.gain.value, now());
      tell.g.gain.linearRampToValueAtTime(0.0001, now() + 0.05);
      tell.o.stop(now() + 0.07);
    } catch (e) { /* 이미 끝남 */ }
    tell = null;
  }
  // 예고가 터지는 순간. 낮게 깔리는 충격.
  function bossHit() {
    if (!ready) return;
    stopTell();
    const t = now();
    tone(t, 0.42, 'sine', 78, 32, 0.40);
    noise(t, 0.30, 'lowpass', 700, 90, 0.8, 0.30, 0.8);
    noise(t, 0.08, 'highpass', 2000, 4000, 0.6, 0.10, 1);
  }

  // ── 잎 스침 (수풀 출입) ──
  // 연출용이다. **소리 반경(stealth.js NOISE_*)과 아무 관계가 없다.**
  // 수풀에 들어가고 나오는 순간을 귀로도 못박는 것뿐이고, 요괴는 이 소리를 못 듣는다.
  //
  // ★한 보이스로 만든다. 노이즈 덩이를 서너 개 따로 치면 그때마다 keep() 이
  //   보이스를 하나씩 먹어서 상한(6)이 차고, 수풀에 들어갔다 나올 때마다
  //   **전투음이 먼저 끊긴다.** 그래서 소스는 하나로 두고 게인 봉투에 서너 번
  //   턱을 만든다(잎은 한 번에 안 스치고 몇 번 부딪히며 잦아든다).
  function rustle(power) {
    if (!ready) return;
    const t = now(), k = power === undefined ? 1 : power;
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf; src.loop = true;
    src.playbackRate.value = rnd(0.9, 1.5);
    // 밝은 대역에서 시작해 내려온다 = 잎이 스치고 잦아드는 결
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass'; bp.Q.value = 0.85;
    bp.frequency.setValueAtTime(rnd(2600, 3900), t);
    bp.frequency.exponentialRampToValueAtTime(rnd(900, 1500), t + 0.24);
    // 저역을 빼야 '바스락'이 된다. 안 빼면 바람 소리와 섞여 뭉갠다
    const hp = ctx.createBiquadFilter();
    hp.type = 'highpass'; hp.frequency.value = 800; hp.Q.value = 0.5;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    let tt = t;
    const n = 3 + Math.floor(Math.random() * 2);
    for (let i = 0; i < n; i++) {
      const peak = 0.075 * k * (1 - i / (n + 0.6)) * rnd(0.72, 1.24);
      g.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), tt + 0.012);
      tt += rnd(0.030, 0.070);
      g.gain.exponentialRampToValueAtTime(0.0002, tt);
    }
    const dur = tt - t + 0.05;
    src.connect(bp); bp.connect(hp); hp.connect(g); g.connect(comp);
    src.start(t, Math.random() * 1.5);
    src.stop(t + dur + 0.03);
    keep(g, t + dur);
  }

  // 증표 획득 / 층 돌파. 짧은 종 + 지축 울림.
  function bell(high) {
    if (!ready) return;
    const t = now();
    const f = high ? 880 : 587;
    tone(t, 0.9, 'sine', f, f * 0.995, 0.16);
    tone(t + 0.005, 0.6, 'sine', f * 1.5, f * 1.49, 0.07);
    tone(t + 0.01, 0.35, 'sine', f * 2.02, f * 2.0, 0.04);
    noise(t, 0.55, 'lowpass', 160, 55, 0.7, 0.18, 0.7);
  }

  return {
    unlock,
    swing, heavySwing, hit, kill, wipe, hurt, rustle,
    // 9차: 못 쓰는 입력(거부) · 대시
    deny, dash,
    // enemy.js 가 window.__sfx 로 부른다(main.js 를 안 거친다)
    death, demonDie,
    bossTell, stopTell, bossHit,
    token() { bell(false); },
    clear() { bell(true); tone(now() + 0.18, 1.4, 'sine', 392, 390, 0.13); },
    toggleMute() {
      muted = !muted;
      if (master) master.gain.setTargetAtTime(muted ? 0 : MASTER, now(), 0.02);
      return muted;
    },
    get muted() { return muted; },
    get streak() { return streak; },
    // feel.js 가 붓자국 색을 고르는 신호. {kind:'light'|'heavy', at: performance.now()}
    get lastSwing() { return lastSwing; },
    // 검증 창구
    get state() {
      return { ctx: ctx ? ctx.state : 'none', ready, muted,
               voices: voices.filter(v => v.end > now()).length,
               played, streak, deaths, cries,
               amb: amb ? { on: true, nodes: amb.nodes,
                            bus: +amb.bus.gain.value.toFixed(4),
                            wind: +amb.wind.gain.value.toFixed(4),
                            bugs: amb.bugs.map(g => +g.gain.value.toFixed(4)),
                            birds, next: !!birdTimer }
                        : { on: false },
               lastSwing };
    },
    // master 뒤에서 실제로 나가는 소리를 잰다. 음소거 검증도 이 숫자로 본다.
    // bands 는 대역별 최대치(dB). 귀 없이 "바람·벌레·새가 실제로 울리는지" 보는 창구다.
    level() {
      if (!ana) return null;
      const buf = new Float32Array(ana.fftSize);
      ana.getFloatTimeDomainData(buf);
      let s = 0, p = 0;
      for (let i = 0; i < buf.length; i++) {
        const v = buf[i];
        s += v * v;
        if (v > p) p = v; else if (-v > p) p = -v;
      }
      const f = new Float32Array(ana.frequencyBinCount);
      ana.getFloatFrequencyData(f);
      const hz = ctx.sampleRate / 2 / f.length;
      const band = (a, b) => {
        let m = -200;
        for (let i = Math.floor(a / hz); i <= Math.ceil(b / hz) && i < f.length; i++) if (f[i] > m) m = f[i];
        return +m.toFixed(1);
      };
      return { rms: +Math.sqrt(s / buf.length).toFixed(6), peak: +p.toFixed(6),
               bands: { wind: band(60, 400), bird: band(1800, 4200), bug: band(4400, 6600) } };
    },
  };
}
