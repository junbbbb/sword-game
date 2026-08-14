// BLACK LEDGER UI — clean-slate 20
//
// 이 파일은 과거 스킨의 DOM/CSS를 재활용하지 않고 화면의 정보 위계부터
// 다시 조립한다. 게임 로직은 만지지 않고 window.__boss / __enemy / __dbg를
// 읽어 표시만 한다. 다른 파일이 소유한 ID는 동작 계약으로 유지하되,
// 배치와 의미 클래스는 이 파일이 새로 정의한다.

const FLOOR = {
  eyebrow: 'DUNGEON ENTRY',
  number: '01',
  floor: '탑 1층',
  name: '풀에 덮인 절터',
  lore: '새로운 층의 문이 열렸습니다.',
};

const BOSS = {
  eyebrow: 'DANGER APPROACHING',
  tag: '탑 1층 · 수문장',
  name: '각귀',
};

const DEATH = {
  eyebrow: 'SURVIVAL FAILED',
  glyph: '패',
  title: '생존 실패',
  line: '초 뒤 다시 일어서기',
  soon: '곧 다시 일어서기',
};

const ENTER_HOLD = 2200;
const REPLAY_HOLD = 850;
const BANNER_HOLD = 2500;
const CINE_HOLD = 1600;
const HELP_BOOT = 6200;
const HELP_IDLE = 4200;
const RESPAWN_SEC = 2.6;
const RESPAWN_LEAD = 0.55;

let started = false;

if (typeof window.__loadProgress !== 'function') {
  window.__loadProgress = function () {};
}

function make(tag, id, className) {
  const node = document.createElement(tag);
  if (id) node.id = id;
  if (className) node.className = className;
  return node;
}

function move(parent, id) {
  const node = document.getElementById(id);
  if (node) parent.appendChild(node);
  return node;
}

function clamp(value, lo, hi) {
  return Math.max(lo, Math.min(hi, value));
}

export function initUI() {
  if (started) return window.__ui;
  started = true;

  document.body.dataset.uiSystem = 'black-ledger';
  document.body.removeAttribute('data-ui-theme');

  // enemy.js / boss.js / main.js 가 주입한 기본 스타일보다 새 CSS가 뒤에
  // 오도록 링크 노드만 헤드 마지막으로 옮긴다. 재다운로드는 없다.
  const cssLink = document.getElementById('uiCss');
  if (cssLink) document.head.appendChild(cssLink);

  const root = make('div', 'uiRoot');
  const persistent = make('div', 'uiPersistent');
  const world = make('div', 'uiWorld');
  const feedback = make('div', 'uiFeedback');
  const overlay = make('div', 'uiOverlay');
  root.append(persistent, world, feedback, overlay);
  document.body.appendChild(root);

  // ── 다른 시스템이 만든 노드를 역할 레이어로 옮긴다. ──
  const help = move(persistent, 'help');
  move(persistent, 'stat');
  const bossHud = move(persistent, 'bHud');
  move(persistent, 'stHud');
  move(feedback, 'eHurt');
  move(feedback, 'hurtDir');
  move(feedback, 'stVig');
  const clearEl = move(overlay, 'bClear');
  move(overlay, 'combo');

  // ── 입장: 중앙 모달이 아닌 왼쪽 위치 공개 타이틀 ──
  const titleBg = make('div', 'uiTitleBg');
  const title = make('div', 'uiTitle');
  title.innerHTML =
    '<div class="entry-card">'
    + '<div class="entry-card__mark"></div>'
    + '<div class="entry-card__copy">'
    + '<span class="entry-card__eyebrow"></span>'
    + '<div class="big"></div><div class="sub"></div>'
    + '<div class="entry-card__rule"></div><div class="lore"></div>'
    + '</div></div>';
  title.querySelector('.entry-card__mark').textContent = FLOOR.number;
  title.querySelector('.entry-card__eyebrow').textContent = FLOOR.eyebrow;
  title.querySelector('.big').textContent = FLOOR.floor;
  title.querySelector('.sub').textContent = FLOOR.name;
  title.querySelector('.lore').textContent = FLOOR.lore;

  // ── 보스 경고: 화면 위를 짧게 가르는 한 줄 ──
  const banner = make('div', 'uiBanner');
  banner.innerHTML =
    '<div class="boss-alert"><span class="boss-alert__eyebrow"></span>'
    + '<div class="tag"></div><div class="name"></div></div>';
  banner.querySelector('.boss-alert__eyebrow').textContent = BOSS.eyebrow;
  banner.querySelector('.tag').textContent = BOSS.tag;
  banner.querySelector('.name').textContent = BOSS.name;

  // ── 사망: 카드보다 짧은 도장 + 상태 문장 ──
  const death = make('div', 'uiDeath');
  death.innerHTML =
    '<div class="death-mark"></div><div class="death-copy">'
    + '<span class="death-copy__eyebrow"></span><strong></strong><div class="cnt"></div>'
    + '</div>';
  death.querySelector('.death-mark').textContent = DEATH.glyph;
  death.querySelector('.death-copy__eyebrow').textContent = DEATH.eyebrow;
  death.querySelector('strong').textContent = DEATH.title;
  const deathCount = death.querySelector('.cnt');

  const clearDim = make('div', 'uiClearDim');
  overlay.append(titleBg, title, banner, death, clearDim);

  // ── 조작 서랍 버튼 ──
  const helpChip = make('button', 'uiHelpChip');
  helpChip.type = 'button';
  helpChip.textContent = '?';
  helpChip.title = 'H 키로 조작 안내';
  helpChip.setAttribute('aria-label', '조작 안내 열기');
  persistent.appendChild(helpChip);

  // ── 액션 덱. 첫 자식 i.cd / 둘째 b.cds 순서는 main.js 계약이다. ──
  const skills = make('div', 'uiSkills');
  const slot = (kind, key, name) =>
    '<div class="sk" data-k="' + kind + '"><i class="cd"></i><b class="cds"></b>'
    + '<span class="key">' + key + '</span><span class="nm">' + name + '</span></div>';
  skills.innerHTML = slot('Basic', 'Z', '베기')
    + slot('Heavy', 'X', '수면참')
    + slot('Wide', 'C', '횡일섬')
    + '<div class="skLock"><i class="lk"></i></div>'
    + '<div class="skLock"><i class="lk"></i></div>';
  const skBasic = skills.querySelector('[data-k="Basic"]');
  const skHeavy = skills.querySelector('[data-k="Heavy"]');
  const skWide = skills.querySelector('[data-k="Wide"]');

  // ── 세 HUD 섬 ──
  const dock = make('div', 'uiDock');

  const survivor = make('section', null, 'survivor-card');
  survivor.innerHTML =
    '<header class="survivor-card__identity">'
    + '<span class="survivor-card__name">TOWER SURVIVOR</span>'
    + '<span class="player-level"><small>LV</small><b class="dkLv">1</b></span>'
    + '</header><div class="survivor-card__vital-head"><span>VITAL</span></div>';
  const playerLevel = survivor.querySelector('.player-level');
  const levelValue = survivor.querySelector('.dkLv');
  const vitalHead = survivor.querySelector('.survivor-card__vital-head');
  const hpNumber = make('b', 'uiHpNum');
  vitalHead.appendChild(hpNumber);

  const playerHud = document.getElementById('eHud');
  const playerBar = document.getElementById('eBar');
  if (playerHud) survivor.appendChild(playerHud);
  const expTrack = make('i', null, 'dkExp');
  const expFill = document.createElement('i');
  expTrack.appendChild(expFill);
  survivor.appendChild(expTrack);

  const actionDeck = make('section', null, 'action-deck');
  actionDeck.appendChild(skills);

  const equipment = make('aside', null, 'equipment-card');
  equipment.innerHTML = '<span class="equipment-card__label">EQUIPPED WEAPON</span>'
    + '<div class="equipment-card__line"><i class="equipment-card__mark"></i></div>';
  const sword = document.getElementById('sword');
  if (sword) equipment.querySelector('.equipment-card__line').appendChild(sword);
  else equipment.style.display = 'none';

  dock.append(survivor, actionDeck, equipment);
  persistent.appendChild(dock);

  // ── 플레이어 머리 위 생존 게이지 ──
  const hpFloat = make('div', 'uiHpFloat');
  hpFloat.innerHTML = '<b class="lv">1</b><span class="track"><i class="gh"></i><i class="fl"></i></span>';
  const hpFloatLevel = hpFloat.querySelector('.lv');
  const hpGhost = hpFloat.querySelector('.gh');
  const hpFill = hpFloat.querySelector('.fl');
  world.appendChild(hpFloat);

  // ── 목표 방향 / 근처 무리 ──
  const nav = make('div', 'uiNav');
  nav.innerHTML = '<div class="dial"><i class="tip"></i></div><div class="plate"></div>'
    + '<div class="cap"></div><div class="dst"></div>';
  const navDial = nav.querySelector('.dial');
  const navPlate = nav.querySelector('.plate');
  const navCap = nav.querySelector('.cap');
  const navDistance = nav.querySelector('.dst');
  const pip = make('div', 'uiPip');
  pip.innerHTML = '<div class="cap">요괴 무리</div>';
  const pipCap = pip.querySelector('.cap');
  world.append(nav, pip);

  // ── 조작 안내 ──
  let helpOff = matchMedia('(pointer:coarse)').matches;
  let helpTouched = false;
  let helpTimer = 0;
  let helpBootTimer = 0;

  function setHelp(off) {
    helpOff = !!off;
    document.body.classList.toggle('uiHelpOff', helpOff);
    helpChip.setAttribute('aria-expanded', helpOff ? 'false' : 'true');
    helpChip.setAttribute('aria-label', helpOff ? '조작 안내 열기' : '조작 안내 닫기');
  }

  function toggleHelp() {
    helpTouched = true;
    clearTimeout(helpTimer);
    clearTimeout(helpBootTimer);
    setHelp(!helpOff);
  }

  function armHelpClose() {
    if (helpTouched || helpOff || helpTimer) return;
    helpTimer = setTimeout(() => setHelp(true), HELP_IDLE);
  }

  setHelp(helpOff);
  helpChip.addEventListener('click', toggleHelp);
  helpBootTimer = setTimeout(() => { if (!helpTouched) setHelp(true); }, HELP_BOOT);

  // ── 입장 / 재시작 ──
  let awake = false;
  let titleTimer = 0;
  function showTitle(short) {
    clearTimeout(titleTimer);
    title.classList.remove('on', 'out');
    void title.offsetWidth;
    title.classList.add('on');
    titleBg.classList.add('on');
    document.body.classList.add('uiTitleOn');
    titleTimer = setTimeout(() => {
      title.classList.add('out');
      titleBg.classList.remove('on');
      awake = true;
      titleTimer = setTimeout(() => {
        title.classList.remove('on', 'out');
        document.body.classList.remove('uiTitleOn');
      }, 470);
    }, short ? REPLAY_HOLD : ENTER_HOLD);
  }

  let firstTitleShown = false;
  const load = document.getElementById('load');
  function waitForSpawn() {
    if (firstTitleShown) return;
    if (!load || getComputedStyle(load).display === 'none') {
      firstTitleShown = true;
      showTitle(false);
      return;
    }
    setTimeout(waitForSpawn, 100);
  }
  waitForSpawn();

  // ── 보스 경고 / 처치 연출 ──
  let bannerShown = false;
  let bannerTimer = 0;
  function showBanner() {
    bannerShown = true;
    clearTimeout(bannerTimer);
    banner.classList.remove('on');
    void banner.offsetWidth;
    banner.classList.add('on');
    document.body.classList.add('uiBossIn');
    bannerTimer = setTimeout(() => {
      banner.classList.remove('on');
      document.body.classList.remove('uiBossIn');
    }, BANNER_HOLD);
  }

  let cineTimer = 0;
  let bossDeadSeen = false;
  function startCine() {
    clearTimeout(cineTimer);
    document.body.classList.add('uiCine');
    cineTimer = setTimeout(() => document.body.classList.remove('uiCine'), CINE_HOLD);
  }
  function endCine() {
    clearTimeout(cineTimer);
    document.body.classList.remove('uiCine');
  }

  // ── 사망 ──
  let deadSeen = false;
  let diedStamp = 0;
  let deathStartedAt = 0;
  let deathHoldUntil = 0;
  function showDeath() {
    deathStartedAt = performance.now();
    deathHoldUntil = deathStartedAt + 1750;
    death.classList.add('on');
    document.body.classList.add('uiDeathOn');
  }
  function hideDeath() {
    death.classList.remove('on');
    document.body.classList.remove('uiDeathOn');
  }

  // ── 한 판 리셋 ──
  let lastRestartAt = -9999;
  function newRun() {
    const now = performance.now();
    if (now - lastRestartAt < 550) return;
    lastRestartAt = now;
    bannerShown = false;
    clearTimeout(bannerTimer);
    banner.classList.remove('on');
    document.body.classList.remove('uiBossIn', 'uiCleared');
    endCine();
    bossDeadSeen = false;
    if (clearEl) clearEl.classList.remove('uiIn');
    hideDeath();
    showTitle(true);
  }

  // ── 스킬 상태 ──
  let lastSkill = '';
  let busyStartedAt = 0;
  let busyEstimate = 0.62;
  let wasBusy = false;

  function busyLeft(debug) {
    const now = performance.now();
    if (!wasBusy) {
      wasBusy = true;
      busyStartedAt = now;
    }
    const current = debug && debug.cur;
    if (current && typeof current.time === 'number' && typeof current.getClip === 'function') {
      const clip = current.getClip();
      if (clip && clip.duration > 0) {
        const ratio = clamp(1 - current.time / clip.duration, 0, 1);
        return { ratio, seconds: ratio * busyEstimate };
      }
    }
    const ratio = clamp(1 - (now - busyStartedAt) / 1000 / busyEstimate, 0, 1);
    return { ratio, seconds: ratio * busyEstimate };
  }

  function noteBusyEnd() {
    if (!wasBusy) return;
    wasBusy = false;
    const elapsed = (performance.now() - busyStartedAt) / 1000;
    if (elapsed > 0.15 && elapsed < 2) busyEstimate = busyEstimate * 0.65 + elapsed * 0.35;
  }

  function setSeconds(node, seconds) {
    if (!node) return;
    const value = seconds >= 1 ? String(Math.ceil(seconds))
      : (seconds >= 0.35 ? seconds.toFixed(1) : '');
    if (node.textContent !== value) node.textContent = value;
  }

  function paintCooldown(node, ratio, seconds) {
    if (!node) return;
    const cover = node.firstElementChild;
    const label = node.querySelector('.cds');
    if (!cover) return;
    if (!(ratio > 0)) {
      if (cover.style.background) cover.style.background = '';
      setSeconds(label, 0);
      return;
    }
    const turn = clamp(ratio, 0, 1).toFixed(3);
    cover.style.background = 'conic-gradient(from 0deg,rgba(3,3,3,.84) 0turn '
      + turn + 'turn,rgba(3,3,3,0) ' + turn + 'turn)';
    setSeconds(label, seconds);
  }

  function setSkill(node, exists, busy, left, mine) {
    if (!node) return;
    node.classList.toggle('gone', !exists);
    node.classList.toggle('off', busy);
    node.classList.toggle('rdy', exists && !busy);
    paintCooldown(node, busy && left ? left.ratio : 0,
      busy && left && mine ? left.seconds : 0);
  }

  let dashCache = null;
  function dashNode() {
    if (dashCache && dashCache.isConnected) return dashCache;
    dashCache = skills.querySelector('[data-k="Dash"]');
    if (dashCache && !dashCache.querySelector('.cds') && dashCache.firstElementChild) {
      const seconds = make('b', null, 'cds');
      dashCache.insertBefore(seconds, dashCache.firstElementChild.nextSibling);
    }
    return dashCache;
  }

  function updateDash() {
    const node = dashNode();
    if (!node) return;
    const label = node.querySelector('.cds');
    if (typeof window.__dash !== 'function') {
      setSeconds(label, 0);
      return;
    }
    try {
      const value = window.__dash();
      setSeconds(label, value ? Math.max(0, value.cdLeft || 0) : 0);
    } catch (_) { /* 진단 창구가 사라지면 글자만 비운다. */ }
  }

  function updateSkills() {
    const debug = window.__dbg;
    const actions = debug && debug.actions;
    const busy = !!(debug && debug.atk);
    if (!busy) noteBusyEnd();
    const left = busy ? busyLeft(debug) : null;
    setSkill(skHeavy, !!(actions && actions.Heavy), busy, left, lastSkill === 'Heavy');
    setSkill(skWide, !!(actions && actions.Wide), busy, left, lastSkill === 'Wide');
    if (skBasic) {
      const exists = !!(actions && actions.Attack);
      skBasic.classList.toggle('gone', !exists);
      skBasic.classList.toggle('rdy', exists);
      skBasic.classList.remove('off');
    }
    updateDash();
  }

  // ── 레벨 / 체력. 레벨업은 화면 팝업 대신 월드 빛 연출을 부른다. ──
  let hpMax = 100;
  let hpSeen = -1;
  let killsSeen = -1;
  let levelSeen = 0;
  let expSeen = -1;
  let levelPulseTimer = 0;
  let levelFxAt = -9999;
  let levelFxValue = 1;

  function playerHeight() {
    const debug = window.__dbg;
    if (!debug || !debug.model || !debug.CHARS) return 0;
    for (const key in debug.CHARS) {
      const item = debug.CHARS[key];
      if (item.model === debug.model) return item.charH || 0;
    }
    return 0;
  }

  function showLevelUp(level) {
    levelFxAt = performance.now();
    levelFxValue = level;
    const feel = window.__feel;
    const target = window.__root;
    if (feel && typeof feel.levelUp === 'function' && target) {
      feel.levelUp(target, playerHeight() || 1.8);
    }
    clearTimeout(levelPulseTimer);
    playerLevel.classList.remove('pulse');
    void playerLevel.offsetWidth;
    playerLevel.classList.add('pulse');
    levelPulseTimer = setTimeout(() => playerLevel.classList.remove('pulse'), 760);
  }

  function updatePlayerHud() {
    const enemy = window.__enemy;
    if (!enemy || typeof enemy.hp !== 'number') return;
    const kills = Math.max(0, Number(enemy.kills) || 0);
    const level = 1 + Math.floor(kills / 5);
    if (level !== levelSeen) {
      const previous = levelSeen;
      levelSeen = level;
      levelValue.textContent = String(level);
      hpFloatLevel.textContent = String(level);
      if (previous > 0 && level > previous) showLevelUp(level);
    }
    const progress = (kills % 5) / 5;
    if (progress !== expSeen) {
      expSeen = progress;
      expFill.style.transform = 'scaleX(' + progress.toFixed(3) + ')';
    }
    if (enemy.hp > hpMax) hpMax = Math.ceil(enemy.hp);
    const hp = Math.max(0, Math.round(enemy.hp));
    if (hp !== hpSeen) {
      hpSeen = hp;
      hpNumber.innerHTML = hp + '<s>/</s><u>' + hpMax + '</u>';
      hpNumber.classList.toggle('low', hp <= hpMax * 0.25);
      if (playerBar) {
        const band = hp <= hpMax * 0.25 ? 'hpLo' : (hp <= hpMax * 0.5 ? 'hpMid' : 'hpHi');
        playerBar.classList.remove('hpHi', 'hpMid', 'hpLo');
        playerBar.classList.add(band);
      }
    }
    killsSeen = kills;
  }

  let swordSeen = '';
  function updateSword() {
    if (!sword) return;
    const hidden = sword.style.display === 'none';
    equipment.style.display = hidden ? 'none' : '';
    if (hidden) return;
    const text = sword.textContent;
    if (text === swordSeen) return;
    const prefix = /^\s*\d+\.\s*/.exec(text);
    if (prefix) sword.textContent = text.slice(prefix[0].length);
    swordSeen = sword.textContent;
  }

  // ── 플레이어 머리 위 HP. 투영은 실제 카메라 행렬을 쓴다. ──
  const HP_UP = 0.34;
  const GHOST_HOLD = 0.14;
  const GHOST_SPEED = 1.15;
  let floatRatio = -1;
  let ghostRatio = 0;
  let ghostHold = 0;
  let floatTime = 0;
  let floatVisible = false;
  let floatHitTimer = 0;

  function showFloat(on) {
    if (on === floatVisible) return;
    floatVisible = on;
    hpFloat.classList.toggle('on', on);
  }

  function updatePlayerFloat(now) {
    const screen = window.__screen;
    const player = window.__root;
    const enemy = window.__enemy;
    const height = playerHeight();
    const dt = floatTime ? Math.min(0.1, (now - floatTime) / 1000) : 0;
    floatTime = now;
    if (!screen || !player || !enemy || !height || enemy.dead
      || document.body.classList.contains('uiCleared')) {
      showFloat(false);
      return;
    }
    const pos = player.position;
    const point = screen(pos.x, pos.z, pos.y + height + HP_UP);
    if (point.behind) {
      showFloat(false);
      return;
    }
    const x = Math.round((point.x + 1) * 0.5 * innerWidth - 44);
    const y = Math.round((1 - point.y) * 0.5 * innerHeight - 8);
    hpFloat.style.transform = 'translate3d(' + x + 'px,' + y + 'px,0)';
    showFloat(true);

    if (enemy.hp > hpMax) hpMax = Math.ceil(enemy.hp);
    const ratio = clamp(enemy.hp / hpMax, 0, 1);
    if (ratio !== floatRatio) {
      if (floatRatio >= 0 && ratio < floatRatio) {
        ghostRatio = Math.max(ghostRatio, floatRatio);
        ghostHold = GHOST_HOLD;
        hpFloat.classList.add('hit');
        clearTimeout(floatHitTimer);
        floatHitTimer = setTimeout(() => hpFloat.classList.remove('hit'), 170);
      } else if (ratio > floatRatio) {
        ghostRatio = ratio;
      }
      floatRatio = ratio;
      hpFill.style.width = (ratio * 100).toFixed(2) + '%';
      hpFloat.classList.toggle('mid', ratio <= 0.5 && ratio > 0.25);
      hpFloat.classList.toggle('low', ratio <= 0.25);
    }
    if (ghostRatio < ratio) ghostRatio = ratio;
    if (ghostRatio > ratio) {
      if (ghostHold > 0) ghostHold -= dt;
      else ghostRatio = Math.max(ratio, ghostRatio - dt * GHOST_SPEED);
      hpGhost.style.width = (ghostRatio * 100).toFixed(2) + '%';
    } else if (hpGhost.style.width !== '0%') {
      hpGhost.style.width = '0%';
    }
  }

  function floatFrame(now) {
    requestAnimationFrame(floatFrame);
    updatePlayerFloat(now);
  }
  setTimeout(() => requestAnimationFrame(floatFrame), 0);

  // ── 화면 가장자 목표 ──
  const NAV = {
    boss: { glyph: '적', ink: '#ef725b', caption: '각귀' },
    token: { glyph: '표', ink: '#f2b84b', caption: '증표' },
    exit: { glyph: '문', ink: '#85c59d', caption: '탈출구' },
  };
  const navCaptionSeen = {};
  let navCaptionTimer = 0;
  let pipCaptionShown = false;
  let navPoint = null;

  function objective(boss) {
    if (!boss) return null;
    if (boss.guide !== undefined) return boss.guide;
    if (boss.phase === '증표줍기' && boss.token && boss.token.state === '바닥') {
      return { x: boss.token.x, z: boss.token.z, kind: 'token' };
    }
    if (boss.phase === '보스탐색' || boss.phase === '보스전') {
      return boss.pos ? { x: boss.pos.x, z: boss.pos.z, kind: 'boss' } : null;
    }
    return null;
  }

  function edgePoint(screen, x, z, edge) {
    const projected = screen(x, z);
    const nx = projected.behind ? -projected.x : projected.x;
    const ny = projected.behind ? -projected.y : projected.y;
    if (!projected.behind && Math.abs(nx) <= 0.86 && Math.abs(ny) <= 0.86) return null;
    const scale = Math.max(Math.abs(nx), Math.abs(ny)) || 1;
    const ex = nx / scale * edge;
    const ey = ny / scale * edge;
    return {
      x: (ex + 1) * 0.5 * innerWidth,
      y: (1 - ey) * 0.5 * innerHeight,
      angle: Math.atan2(-ey * innerHeight, ex * innerWidth) * 180 / Math.PI,
    };
  }

  function safeEdge(point, half, bottomSpace) {
    return {
      x: clamp(point.x, half + 12, innerWidth - half - 12),
      y: clamp(point.y, Math.max(82, half + 12), innerHeight - bottomSpace),
    };
  }

  function showNavCaption(kind) {
    if (!awake || navCaptionSeen[kind]) return;
    navCaptionSeen[kind] = true;
    navCap.textContent = NAV[kind].caption;
    navCap.classList.add('on');
    clearTimeout(navCaptionTimer);
    navCaptionTimer = setTimeout(() => navCap.classList.remove('on'), 2200);
  }

  function updateNav(boss, cleared) {
    const screen = window.__screen;
    const target = !cleared && !deadSeen && screen ? objective(boss) : null;
    if (!target) {
      nav.style.opacity = '0';
      navPoint = null;
      return;
    }
    const point = edgePoint(screen, target.x, target.z, 0.84);
    if (!point) {
      nav.style.opacity = '0';
      navPoint = null;
      return;
    }
    const kind = NAV[target.kind] || NAV.boss;
    nav.style.setProperty('--nav-ink', kind.ink);
    navPlate.dataset.glyph = kind.glyph;
    showNavCaption(target.kind in NAV ? target.kind : 'boss');
    const bottomSpace = innerWidth <= 600 ? 190 : 132;
    const at = safeEdge(point, 34, bottomSpace);
    nav.style.left = at.x.toFixed(0) + 'px';
    nav.style.top = at.y.toFixed(0) + 'px';
    navDial.style.transform = 'rotate(' + point.angle.toFixed(1) + 'deg)';
    const player = typeof window.__pos === 'function' ? window.__pos() : null;
    if (player && !navCap.classList.contains('on')) {
      navDistance.textContent = Math.round(Math.hypot(target.x - player.x, target.z - player.z)) + 'm';
      navDistance.classList.add('on');
    } else navDistance.classList.remove('on');
    nav.style.opacity = '1';
    navPoint = at;
  }

  function updatePip(cleared) {
    const screen = window.__screen;
    const enemy = window.__enemy;
    const player = typeof window.__pos === 'function' ? window.__pos() : null;
    if (cleared || deadSeen || !screen || !enemy || !player) {
      pip.style.opacity = '0';
      return;
    }
    let best = null;
    let bestDistance = 15 * 15;
    const groups = enemy.field || [];
    for (const group of groups) {
      if (!group.alive || !group.at) continue;
      const dx = group.at[0] - player.x;
      const dz = group.at[1] - player.z;
      const distance = dx * dx + dz * dz;
      if (distance < bestDistance) {
        bestDistance = distance;
        best = group;
      }
    }
    if (!best) {
      pip.style.opacity = '0';
      return;
    }
    const point = edgePoint(screen, best.at[0], best.at[1], 0.67);
    if (!point) {
      pip.style.opacity = '0';
      return;
    }
    const bottomSpace = innerWidth <= 600 ? 181 : 124;
    const at = safeEdge(point, 12, bottomSpace);
    if (navPoint && Math.hypot(navPoint.x - at.x, navPoint.y - at.y) < 64) {
      pip.style.opacity = '0';
      return;
    }
    pip.style.left = at.x.toFixed(0) + 'px';
    pip.style.top = at.y.toFixed(0) + 'px';
    pip.style.opacity = '1';
    if (awake && !pipCaptionShown) {
      pipCaptionShown = true;
      pipCap.classList.add('on');
      setTimeout(() => pipCap.classList.remove('on'), 2200);
    }
  }

  // ── 클리어 결과의 처치 수를 상시 HUD와 맞춘다. ──
  function fixClearKills(node) {
    const enemy = window.__enemy;
    if (!node || !enemy) return;
    const cells = node.querySelectorAll('td');
    for (const cell of cells) {
      if (cell.textContent !== '처치') continue;
      const value = cell.nextElementSibling;
      if (value) value.textContent = String(enemy.kills);
      break;
    }
    // level2.js는 이미 생활어로 쓰지만 boss.js의 옛 결과 문구는 아직
    // 「남쪽 문으로 반출」이다. 게임 로직 소유 파일을 건드리지 않고 표시만 맞춘다.
    for (const value of node.querySelectorAll('td.v')) {
      if (value.textContent.endsWith('으로 반출')) {
        value.textContent = value.textContent.replace(/으로 반출$/, '으로 가지고 나감');
      }
    }
  }

  // main.js는 소리 줄을 현재 상태(켜짐/꺼짐)로 쓴다. 나머지 조작 안내와
  // 같은 동작형 문장으로만 다듬고, 실제 음소거 상태나 입력은 건드리지 않는다.
  const mute = document.getElementById('mute');
  function fixMuteCopy() {
    if (!mute) return;
    const text = mute.textContent;
    const off = text.includes('꺼짐');
    if (!off && !text.includes('켜짐')) return;
    mute.innerHTML = '<span class="ks"><span class="k">M</span></span>'
      + '<span class="t">소리 ' + (off ? '켜기' : '끄기') + '</span>';
  }

  // ── 입력. 게임 이벤트를 막지 않고 표시용 기억만 남긴다. ──
  addEventListener('keydown', event => {
    if (event.repeat) return;
    armHelpClose();
    if (event.code === 'KeyX') lastSkill = 'Heavy';
    else if (event.code === 'KeyC') lastSkill = 'Wide';
    else if (event.code === 'KeyZ' || event.code === 'Space') lastSkill = '';
    if (event.code === 'KeyH') toggleHelp();
    else if (event.code === 'KeyR') newRun();
  });
  addEventListener('pointerdown', armHelpClose, { passive: true });
  addEventListener('wheel', armHelpClose, { passive: true });

  // ── 20Hz DOM 폴링 ──
  let previousRunTime = 0;
  let clearHelpDone = false;
  setInterval(() => {
    const boss = window.__boss;
    const enemy = window.__enemy;
    if (boss) {
      const runTime = Number(boss.time) || 0;
      if (runTime < previousRunTime - 0.4) newRun();
      previousRunTime = runTime;

      if (!bannerShown && boss.phase === '보스전') showBanner();
      const bossDead = boss.state === '사망';
      if (bossDead && !bossDeadSeen) startCine();
      bossDeadSeen = bossDead;

      const cleared = !!boss.cleared;
      document.body.classList.toggle('uiCleared', cleared);
      if (clearEl) {
        clearEl.classList.toggle('uiIn', cleared);
        if (cleared) fixClearKills(clearEl);
      }
      if (cleared && !clearHelpDone) {
        clearHelpDone = true;
        setHelp(true);
      }
      if (!cleared) clearHelpDone = false;
      updateNav(boss, cleared);
      updatePip(cleared);
    }

    updateSkills();
    updatePlayerHud();
    updateSword();
    fixMuteCopy();

    if (enemy) {
      const stamp = Number(window.__playerDied) || 0;
      const dead = !!enemy.dead;
      if (stamp > diedStamp) {
        diedStamp = stamp;
        showDeath();
      } else if (dead && !deadSeen) {
        showDeath();
      }
      const open = death.classList.contains('on');
      const left = typeof enemy.deadIn === 'number' ? enemy.deadIn : null;
      const lead = typeof enemy.respawnCardLead === 'number'
        ? enemy.respawnCardLead : RESPAWN_LEAD;
      if (open && performance.now() >= deathHoldUntil
        && (!dead || (left !== null && left <= lead))) hideDeath();
      deadSeen = dead;
      if (dead || open) {
        const total = typeof enemy.respawnDelay === 'number' ? enemy.respawnDelay : RESPAWN_SEC;
        const seconds = left !== null ? left
          : Math.max(0, total - (performance.now() - deathStartedAt) / 1000);
        const count = Math.ceil(seconds - 0.001);
        deathCount.textContent = count >= 1 ? count + DEATH.line : DEATH.soon;
      }
    }
  }, 50);

  // ── 진단 / 데모 API. 기존 호출 이름은 유지하되 레벨업은 팝업이 아니다. ──
  const api = {
    showTitle,
    showBanner,
    showLevelUp,
    toggleHelp,
    setHelp,
    get state() {
      const dockRect = dock.getBoundingClientRect();
      const floatRect = hpFloat.getBoundingClientRect();
      let feelLevel = null;
      try {
        const feelState = window.__feel && window.__feel.state;
        feelLevel = feelState && feelState.levelUp ? feelState.levelUp : null;
      } catch (_) { /* 연출 진단은 선택적이다. */ }
      return {
        system: 'black-ledger',
        helpOff,
        bannerDone: bannerShown,
        dead: deadSeen,
        cleared: document.body.classList.contains('uiCleared'),
        titleOn: title.classList.contains('on'),
        banner: banner.classList.contains('on'),
        deathCard: death.classList.contains('on'),
        levelUp: {
          on: performance.now() - levelFxAt < 1100,
          value: levelFxValue,
          world: feelLevel,
        },
        dock: {
          rect: [Math.round(dockRect.left), Math.round(dockRect.top),
            Math.round(dockRect.width), Math.round(dockRect.height)],
          islands: 3,
          hp: hpNumber.textContent,
          sword: sword ? sword.textContent : null,
        },
        hpFloat: {
          on: hpFloat.classList.contains('on'),
          rect: [Math.round(floatRect.left), Math.round(floatRect.top),
            Math.round(floatRect.width), Math.round(floatRect.height)],
          fill: hpFill.style.width,
          ghost: hpGhost.style.width,
        },
        nav: {
          on: nav.style.opacity === '1',
          glyph: navPlate.dataset.glyph || '',
          left: nav.style.left,
          top: nav.style.top,
        },
        kills: killsSeen,
      };
    },
  };
  window.__ui = api;
  return api;
}
