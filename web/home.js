// ── 홈화면 ────────────────────────────────────────────────────────────────
// 층과 캐릭터를 고르고 게임으로 들어간다. index.html 이 **쿼리가 비어 있을 때만**
// 이 모듈을 부른다(`?map=field` 같은 기존 링크·`?dev` 관례는 예전처럼 곧장 게임).
//
// ★게임으로 들어갈 때 페이지를 다시 읽지 않는다. history.pushState 로 주소만 바꾸고
//   main.js 를 동적 import 한다. 이유가 둘이다.
//   ① main.js 는 부팅 때 location.search 를 읽는다(맵·캐릭터·?dev). 주소를 먼저
//      바꿔 두면 main.js 는 한 줄도 고칠 필요가 없다.
//   ② 설치본(Electron)은 `will-navigate` 로 주소 이동을 검사한다. 게임 주소 안이라
//      리로드도 통과하긴 하지만, 아예 이동을 안 하는 쪽이 안전하고 빠르다.
// ★pushState 라서 **브라우저 뒤로가기 = 홈 복귀**다(popstate 에서 리로드한다).
//   게임 안에 홈 버튼을 새로 얹지 않으려고 이 길을 골랐다 - 화면 가리는 표시물은
//   이 게임에서 연쇄적으로 제거돼 온 이력이 있다.
// ★#load(로딩 창)를 여기서 감추지 않는다. z-index 로 덮기만 한다. index.html 의
//   진행 막대는 감춰지는 순간을 "로딩 끝"으로 읽어서, 홈에서 display:none 을 주면
//   게임이 시작하기도 전에 100% 가 박힌다.

import { makeRoomCode } from './net.js';

const MAPS = [
  {
    key: 'level2', name: '던전 1층',
    desc: '색색의 석조 회랑. 제단의 증표를 계단으로 반출한다.',
    tag: '보스 없음',
  },
  {
    key: 'field', name: '초원',
    desc: '아침 산야. 개방감 있게 짠 첫 층이다.',
    tag: '보스 있음',
  },
];

// 클립 구성은 glb 를 직접 읽어 확인한 값이다(2026-08-19).
//   basic2·kensa·slayer  Attack Heavy Idle Jump Run Walk Wide   (전부)
//   archer               Attack Idle Jump JumpB Run Walk        (Heavy·Wide 없음)
//   tank                 Attack Idle Run Walk                   (Heavy·Wide·Jump 없음)
//   soldier              Attack CombatIdle Idle Run Walk        (Heavy·Wide·Jump 없음)
// ★없는 클립은 눌러도 아무 일이 안 일어난다(play() 가 조용히 빠진다). 그래서
//   "무엇이 되는 캐릭터인지"를 고르기 전에 여기서 말해 준다.
const CHARS = [
  { key: 'basic2',  name: '검사', desc: '흑요석 대검',  moves: '베기 3종 · 점프' },
  { key: 'kensa',   name: '검사', desc: '삿갓 쓴 한국 검사',        moves: '베기 3종 · 점프' },
  { key: 'slayer',  name: '검사', desc: '무브셋 원본',              moves: '베기 3종 · 점프' },
  { key: 'archer',  name: '궁수', desc: '점프 클립 두 벌',        moves: 'Z 베기 · 점프', thin: true },
  { key: 'tank',    name: '탱커', desc: '로마식 망토',              moves: 'Z 베기만',      thin: true },
  { key: 'soldier', name: '병사', desc: '2차대전 철모',             moves: 'Z 베기만',      thin: true },
];

const STORE = 'swordHome';           // 마지막 선택을 기억한다(테스트 왕복이 잦다)
const sel = { map: 'level2', char: 'basic2', dev: false };

try {
  const saved = JSON.parse(localStorage.getItem(STORE) || '{}');
  if (MAPS.some(m => m.key === saved.map)) sel.map = saved.map;
  if (CHARS.some(c => c.key === saved.char)) sel.char = saved.char;
  sel.dev = !!saved.dev;
} catch (e) { /* 저장값이 깨졌으면 기본값으로 간다 */ }

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function card(kind, it) {
  const on = sel[kind] === it.key;
  const key = kind === 'char' ? '<span class="hmKey">' + esc(it.key) + '</span>' : '';
  const line = kind === 'char'
    ? '<span class="hmMoves' + (it.thin ? ' hmThin' : '') + '">' + esc(it.moves) + '</span>'
    : '<span class="hmMoves' + (it.tag === '보스 있음' ? '' : ' hmThin') + '">' + esc(it.tag) + '</span>';
  return '<button class="hmCard" type="button" data-kind="' + kind + '" data-key="' + esc(it.key) + '"' +
         ' aria-pressed="' + (on ? 'true' : 'false') + '">' +
           '<b>' + esc(it.name) + '</b>' + key +
           '<span class="hmDesc">' + esc(it.desc) + '</span>' + line +
         '</button>';
}

const home = document.createElement('div');
home.id = 'home';
home.innerHTML =
  '<div class="hmWin">' +
    '<i class="hmFr"></i>' +
    '<div class="hmTitle">「 탑의 생존자 」</div>' +
    '<div class="hmSub">TOWER CHRONICLE · DEMO BUILD</div>' +

    '<div class="hmSec">' +
      '<div class="hmSecHd">층</div>' +
      '<div class="hmGrid hmMaps">' + MAPS.map(m => card('map', m)).join('') + '</div>' +
    '</div>' +

    '<div class="hmSec">' +
      '<div class="hmSecHd">캐릭터<span class="hmHint">기술 구성이 캐릭터마다 다르다</span></div>' +
      '<div class="hmGrid hmChars">' + CHARS.map(c => card('char', c)).join('') + '</div>' +
    '</div>' +

    '<button class="hmGo" type="button">입장</button>' +

    '<div class="hmSec">' +
      '<div class="hmSecHd">멀티플레이<span class="hmHint">친구와 같은 층을 골라야 만난다</span></div>' +
      '<div class="hmMultiRow">' +
        '<button class="hmMultiBtn hmMake" type="button">방 만들기</button>' +
        '<button class="hmMultiBtn hmJoin" type="button">방 참가</button>' +
      '</div>' +
      '<div class="hmJoinRow" hidden>' +
        '<input class="hmCode" type="text" maxlength="4" placeholder="방코드 4자리" ' +
               'autocomplete="off" autocapitalize="characters" spellcheck="false">' +
        '<button class="hmCodeGo" type="button">들어가기</button>' +
      '</div>' +
      '<div class="hmMultiNote">요괴는 아직 각자 화면에서 따로 논다. 서로의 캐릭터만 보인다.</div>' +
    '</div>' +

    '<div class="hmFoot">' +
      '이동 <b>방향키</b> · 달리기 <b>Shift</b> · 점프 <b>Space</b> · 베기 <b>Z X C</b> · 안내 <b>H</b><br>' +
      '게임 중 <b>브라우저 뒤로가기</b>를 누르면 이 화면으로 돌아온다.' +
      '<label class="hmDev"><input type="checkbox" class="hmDevBox"' + (sel.dev ? ' checked' : '') + '> 개발 모드</label>' +
    '</div>' +
  '</div>';

document.body.appendChild(home);

// ── 고르기 ──
home.addEventListener('click', e => {
  const btn = e.target.closest('.hmCard');
  if (!btn) return;
  const kind = btn.dataset.kind;
  sel[kind] = btn.dataset.key;
  // 같은 종류의 카드만 끈다(층을 골랐다고 캐릭터가 풀리면 안 된다)
  home.querySelectorAll('.hmCard[data-kind="' + kind + '"]')
      .forEach(el => el.setAttribute('aria-pressed', el === btn ? 'true' : 'false'));
});

const devBox = home.querySelector('.hmDevBox');
if (devBox) devBox.addEventListener('change', () => { sel.dev = devBox.checked; });

// ── 들어가기 ──
let entered = false;
function enter(extra) {
  if (entered) return;                     // Enter 연타로 main.js 가 두 번 돌면 안 된다
  entered = true;
  try { localStorage.setItem(STORE, JSON.stringify(sel)); } catch (e) { /* 사파리 프라이빗 등 */ }

  const p = new URLSearchParams();
  p.set('map', sel.map);
  p.set('char', sel.char);
  if (sel.dev) p.set('dev', '1');
  // 멀티는 쿼리로만 켠다. room 이 없으면 main.js 가 mp.js·net.js·peerjs 를 아예 안 읽는다.
  if (extra) for (const k in extra) p.set(k, extra[k]);
  const q = '?' + p.toString();

  // 주소를 먼저 바꾼다. main.js 는 import 되는 순간 location.search 를 읽는다.
  history.pushState({ game: 1 }, '', q);
  // 뒤로가기 = 홈. 이미 main.js 가 세계를 다 세운 뒤라 되돌릴 방법이 리로드뿐이다.
  window.addEventListener('popstate', () => location.reload());

  home.remove();
  if (typeof window.__loadBegin === 'function') window.__loadBegin();
  import('./main.js' + q);
}

home.querySelector('.hmGo').addEventListener('click', () => enter());

// ── 멀티 ──
// 방 만들기: 코드를 여기서 뽑아 주소에 실어 보낸다. 그 코드가 이미 살아 있으면
// net.js 가 다른 코드로 바꿔서 연다(그때는 게임 안 표시가 진짜 코드다).
const joinRow = home.querySelector('.hmJoinRow');
const codeInput = home.querySelector('.hmCode');

home.querySelector('.hmMake').addEventListener('click', () => {
  enter({ room: makeRoomCode(), host: '1' });
});
home.querySelector('.hmJoin').addEventListener('click', () => {
  joinRow.hidden = !joinRow.hidden;
  if (!joinRow.hidden) codeInput.focus();
});
// 방코드는 대문자다. 소문자로 쳐도 대문자로 보이게 해서 "왜 안 되지" 를 없앤다.
codeInput.addEventListener('input', () => {
  const v = codeInput.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (v !== codeInput.value) codeInput.value = v;
});
function joinRoom() {
  const code = codeInput.value.trim().toUpperCase();
  if (code.length < 4) { codeInput.focus(); codeInput.classList.add('hmBad'); return; }
  enter({ room: code });
}
home.querySelector('.hmCodeGo').addEventListener('click', joinRoom);
codeInput.addEventListener('keydown', e => {
  codeInput.classList.remove('hmBad');
  if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); joinRoom(); }
});
window.addEventListener('keydown', e => {
  if (entered) return;
  if (e.key === 'Enter' || e.key === ' ') {
    const ae = document.activeElement;
    // 카드에 포커스가 있으면 그 카드를 고르는 게 먼저다(브라우저 기본 동작)
    if (ae && ae.classList.contains('hmCard')) return;
    // 방코드를 치는 중이면 그쪽 Enter 다(여기서 먹으면 혼자 입장해 버린다)
    if (ae && (ae.classList.contains('hmCode') || ae.tagName === 'INPUT')) return;
    e.preventDefault();
    enter();
  }
});
