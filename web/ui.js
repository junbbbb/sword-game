// 연출 껍데기 - 입장 알림창 · 보스 경고창 · 사망/결과창 · 조작 안내 · HUD 톤
//
// 이 파일은 **DOM 만 만진다.** 게임 로직(이동·전투·리스폰·보스 상태)에는 한 줄도 안 붙는다.
// 상태는 전부 window.__boss / window.__enemy 를 **읽기만** 해서 알아낸다(폴링).
// 그래서 enemy.js·boss.js 가 어떻게 바뀌든 이 파일은 안 깨지고, 반대로 이 파일이
// 죽어도 게임은 그대로 돈다.
//
// ★모든 겹은 pointer-events:none 이다. 알림창이 떠 있는 동안에도 조작은 살아 있다.
//   유일한 예외가 왼쪽 위 「?」 칩(클릭으로 조작 안내를 편다)이고, 30px 짜리 칩 하나다.
//
// ═══ 11차 파도: 먹·붓 → 시스템창 (오너 지시 「UI 나혼렙 시스템창으로 해봐」) ═══
// 외관 컨셉이 SAO + 나 혼자만 레벨업 + 게임 속 바바리안으로 확정됐고, 셋의 공통
// 시그니처가 **게임 시스템 창**이다. 그래서 화면의 모든 판을 한 문법으로 갈아입힌다.
//
//   판   : 짙은 남색 유리(위가 밝고 아래가 짙은 세로 경사) + 반투명
//   테   : 가는 청백 발광선 1px. 안쪽에 한 겹 더 옅은 선(이중선)
//   모서리: 네 귀에 짧은 청백 브래킷. 둥근 모서리는 안 쓴다(각진 것이 이 문법이다)
//   발광 : 바깥으로 은은하게 한 겹만. ★과하면 촌스러워진다(오너 톤: 담백)
//   머리 : 상단 중앙에 「알림」 · 「경고」 · 「스킬」 같은 한 낱말 + 밑줄
//   글자 : 깨끗한 산세리프(Pretendard 계열 시스템 스택). 숫자는 tabular
//   경고 : 같은 문법의 붉은 변주(보스 조우 · 사망)
//
// ★저작권: 스타일 문법(색·배치·발광 패턴)만 차용한다. 로고·원문 문구·전용 서체는
//   한 점도 안 쓴다. 화면에 나가는 말은 전부 이 게임이 원래 쓰던 우리 문구다.
//
// ★붓 서체(RFBrush)는 UI 에서 은퇴했다. web/fonts/ 의 woff2 두 벌은 **지우지 않았다**
//   (다른 곳에서 참조할 수 있다). 여기서는 @font-face 도 preload 도 안 건다.

// ---------------------------------------------------------------------------
// 문구. ★오너가 바꿀 곳은 여기 하나다. 아래 코드에는 문구가 안 박혀 있다.
// ---------------------------------------------------------------------------
// ── 층 표기 규칙 (11차 개정. 이 규칙이 정본이다) ────────────────────────────
// 예전 규칙(판정 S9)은 「카드류 = 한자 + 첫 등장 루비(一層/일층), HUD = 아라비아」
// 였다. 한자 병기와 루비(방주)는 **세로 붓 조판의 장치**다. 시스템창은 활자 문법이라
// 그 장치가 설 자리가 없다 - 가로 한 줄에 루비를 달면 주석이 아니라 얼룩이 된다.
// 그래서 규칙을 하나로 줄인다.
//
//   화면 어디서나 **아라비아 숫자** 「1층」. 한자도 루비도 안 쓴다.
//
// 지금 화면에 나가는 표기와 그 소유 파일(2026-08-11 감사. 위반 0):
//   ui.js    FLOOR.no        '탑 1층'          입장 알림창  ✓
//   ui.js    BOSS_CARD.tag   '탑 1층 · 수문장' 보스 경고창  ✓
//   boss.js  #bName          '1층 · 각귀'      HUD          ✓
//   boss.js  #bGoal · h1     '층 돌파'(수 없음)본문         ✓
//   index    조작 안내       '층 재시작'(수 없음) 본문      ✓
// ★새 층·새 문구를 넣을 때 이 표에 한 줄을 같이 적을 것.
//
// ★예외가 딱 하나 있다: **나침반 글리프(鬼·符·門)**. 그건 표기가 아니라 아이콘이다
//   (한 글자가 목표 종류를 말한다). 정보로서 잘 작동해 온 자산이라 그대로 둔다.
const FLOOR = {
  head: '알림',                     // 창 머리
  no: '탑 1층',                     // 큰 글자
  name: '풀에 덮인 절터',           // 층 이름
  lore: '해를 삼킨 탑, 그 첫걸음.', // 아래 한 줄
};

const BOSS_CARD = {
  head: '경고',                     // 창 머리(붉은 변주)
  tag: '탑 1층 · 수문장',           // 윗줄(작게)
  name: '각귀',                     // 큰 글자
};

const DEATH = {
  head: '경고',                     // 창 머리(붉은 변주)
  glyph: '落',                      // 한 글자. ★도장 노릇이라 남긴다(정보 설계 유지)
  line: '다시 일어선다',            // 카운트 뒤에 붙는 말 ("3초 뒤 다시 일어선다")
  soon: '곧 다시 일어선다',         // 남은 시간이 1초 밑일 때
};

// 결과창(클리어). ★패널 DOM 은 boss.js 것이라 못 바꾼다. 머리 낱말만 여기서 얹는다.
const CLEAR_HEAD = '결과';

// 기술 콜아웃 창 머리.
const SKILL_HEAD = '스킬';

// 한자 나침반 판이 처음 뜰 때 딱 한 번 밑에 붙는 작은 말.
// ★두 번째부터는 안 붙는다. 한 번 배우면 글자만으로 읽힌다.
const NAV_HINT = { boss: '각귀', token: '증표', exit: '탈출구' };

// 무리 마커가 처음 뜰 때 딱 한 번 붙는 라벨.
const PIP_HINT = '요괴 무리';

// ---------------------------------------------------------------------------
// boss.js 문구 덮어쓰기. ★boss.js 는 이 작업의 소유 밖이라 한 줄도 안 건드린다.
//   대신 화면에 나온 글자만 표시 단계에서 갈아 끼운다(fixClearKills 와 같은 수법).
//   원본을 고칠 수 있게 되면 이 표는 통째로 지우면 된다.
// ---------------------------------------------------------------------------
const TEXT_PATCH = [
  // '위치 노출' = 증표를 들면 요괴가 내 자리를 안다는 뜻. 명사 두 개로는 안 읽힌다.
  ['· 위치 노출', '· 요괴들이 증표를 쫓는다'],
  // 'R 을 눌러 다시' = 조사가 붙었는데 서술이 안 끝난다.
  ['R 을 눌러 다시', 'R 키를 눌러 다시 도전'],
  // ★판정 S13: 결과창의 「남쪽 문으로 반출」. '반출'은 물류·행정 용어라
  //   내가 방금 한 일(증표를 들고 문 밖으로 걸어 나갔다)이 안 그려진다.
  ['으로 반출', '으로 가지고 나감'],
];

// ── 기술 이름 콜아웃 ─────────────────────────────────────────────────────────
// main.js 가 #combo 에 기술 이름을 쓰면(showSkill) 여기서 그 글자를 **시스템 팝**으로
// 갈아 끼운다. 원본 파일은 한 줄도 안 건드린다(TEXT_PATCH 와 같은 수법).
// ★型 번호는 이 게임의 두 기술이 같은 호흡이라는 사실에서 온다 - main.js 는
//   수면참·횡일섬 둘 다 감청(water) 팔레트로 그린다. 그래서 둘 다 「물의 X」다.
// ★오너가 바꿀 곳은 이 표다. 표에 없는 글자는 창이 안 씌워진다(평타 「1타」).
const SKILL_TYPE = {
  '수면참': '물의 一',
  '횡일섬': '물의 二',
};

// 시간(ms). 첫 입장은 길게, R 재시작은 짧게.
// ★11차에서 **한 값도 안 바꿨다.** 이번 작업은 스킨 교체라 타이밍은 그대로 간다.
const ENTER_HOLD = 2800;            // 첫 입장 창이 화면에 머무는 시간
const REPLAY_HOLD = 1000;           // R 재시작 창
// ★v72 QA #11: 배너가 보스 체력바와 겹치고 보스 몸통까지 가렸다. 1.8초는 조우한
//   그 순간에 화면 위쪽을 너무 오래 먹는다. 그래서 배너가 **다 빠진 뒤에**
//   체력바를 들인다(아래 BANNER_FADE). 겹치는 구간 자체를 없애는 게 요점이다.
// ★v93 판정 S7: 1.2초는 **읽기도 전에 사라진다.** 2.5초로 늘렸다 - 등장이 끝난 뒤에도
//   1.6초가 남으므로 「탑 1층 · 수문장 / 각귀」를 두 줄 다 읽을 수 있다.
const BANNER_HOLD = 2500;           // 보스 경고창이 화면에 머무는 시간
const BANNER_FADE = 460;            // 배너 사라짐(.45s)이 끝나고 체력바가 들어오기까지
// ★판정 S4: R 재시작 900ms 구간에서 **창도 반투명, 계기판도 반투명**이었다.
//   둘이 같은 순간에 서로를 지나가면 어느 쪽도 화면의 주인이 아니다.
//   창 사라짐(.55s)이 거의 끝난 뒤에야 계기판을 들인다.
const TITLE_OUT = 470;              // .out 을 붙이고 계기판을 되돌리기까지
const TITLE_CLEAN = 640;            // 애니 클래스를 거두기까지(전환 .55s 보다 뒤)
// ★판정 S6: 보스가 쓰러지는 컷 동안에도 도움말·목표 알약·계기판이 그대로 서 있었다.
const CINE_KILL = 1800;
// ── 조작 안내 접기 (v84 QA S10) ──
//     · 아무 입력(키·클릭·휠)이든 한 번 들어오면 그로부터 6초 뒤 접는다
//     · 아무것도 안 눌러도 뜬 지 8초가 지나면 접는다(읽을 시간은 준다)
//   H 는 그대로 수동 토글이고, 한 번이라도 직접 만지면 자동으로는 안 건드린다.
const HELP_IDLE = 6000;
const HELP_BOOT = 8000;

// ★리스폰까지 걸리는 시간(초). enemy.js 가 respawnDelay 로 내주면 그걸 쓰고,
//   없는 낡은 빌드에서만 이 숫자를 쓴다(카운트만 어긋나고 게임은 정상).
const RESPAWN_SEC = 2.6;
// 창을 내리고 나서 몸이 움직이기까지의 여유(초). enemy.js 와 같은 뜻이다.
const RESPAWN_LEAD = 0.55;

// ---------------------------------------------------------------------------
// 서체
// ---------------------------------------------------------------------------
// ★시스템창은 활자다. 붓 서체(RFBrush)를 UI 에서 은퇴시키고 깨끗한 산세리프로 간다.
//   Pretendard 를 먼저 부르되 **번들하지 않는다** - 로컬에 깔린 사람은 그걸 쓰고,
//   없으면 곧바로 OS 기본 고딕으로 떨어진다(맥=Apple SD Gothic Neo). 두 벌 다
//   시스템창 문법에 맞는 균일한 획이라 그림이 안 흔들린다.
// ★웹폰트를 안 받으므로 「맨몸으로 떴다가 바뀌는」 깜빡임 자체가 없어졌다
//   (붓 시절에는 그것 때문에 preload 두 줄이 필요했다. index.html 에서 걷어냈다).
const SANS = "'Pretendard Variable',Pretendard,-apple-system,BlinkMacSystemFont,"
  + "'Apple SD Gothic Neo','Segoe UI','Malgun Gothic','Noto Sans KR',sans-serif";

// ---------------------------------------------------------------------------
const CSS = `
/* ★아래 색값의 출처: renders/history/v97_wave11/ui_research.md
     (애니 스크린샷을 픽셀 샘플링해 뽑은 **추정치**다. 공식 스펙이 아니다)
   조사에서 확정된 것 중 이 게임에 그대로 옮긴 규칙 넷:
     ① 판은 **평면**이다. 세로 그라디언트가 아니라 청록기 도는 짙은 남색 한 색(#102B3C)
        + 아주 옅은 대각 결. 매끈한 경사를 주면 웹툰 계열(다른 벌)이 된다
     ② 테두리는 **2층**이다. 판에 붙은 1px 헤어라인 + 판에서 **떨어진** 네온 브래킷 프레임.
        이 2층 구조가 이 문법의 정체성이다
     ③ 안쪽 발광(inset glow)은 **안 쓴다.** 원작에 없다. 발광은 프레임과 글자에만
     ④ 굵기가 아니라 **발광**으로 존재감을 만든다. 글자는 500 안팎, 자간을 넓게 */
:root{
  --sys-font:${SANS};
  /* 판. 평면 + 반투명 필름(뒤가 흐릿하게 비치는 정도) */
  --sys-bg:rgba(16,43,60,.88);
  --sys-bg-deep:rgba(11,31,45,.92);     /* 칩처럼 작은 판은 한 단 더 눌러 쓴다 */
  /* 테두리 1층: 판에 붙은 헤어라인. 경계 표시일 뿐 주인공이 아니다 */
  --sys-edge:rgba(143,211,241,.42);
  --sys-edge-in:rgba(143,211,241,.16);  /* 안쪽 칸막이·구분선 */
  /* 테두리 2층: 떨어져 있는 네온 브래킷 프레임 */
  --sys-frame:#36b4f2;
  --sys-frame-core:#bef4fe;
  --sys-glow:rgba(65,211,251,.55);
  --sys-glow-soft:rgba(54,180,242,.28);
  --sys-rule:rgba(143,211,241,.26);     /* 구분선 */
  /* 글자 */
  --sys-txt:#e6f3f7;    /* 본문·값 */
  --sys-key:#cdeeff;    /* 머리 낱말·키캡 */
  --sys-dim:rgba(230,243,247,.62);
  --sys-mute:rgba(230,243,247,.38);
  --sys-halo:0 0 4px rgba(190,244,254,.8),0 0 13px rgba(65,211,251,.42);
  /* 붉은 변주(경고). ★판 색은 안 바꾼다 - 원작에서 붉은 알림은 **판이 아니라
     테두리·글로우·글자**가 붉어진다. 판까지 붉히면 「다른 시스템의 창」이 된다. */
  --sys-warn:#f0333e;
  --sys-warn-edge:rgba(240,51,62,.50);
  --sys-warn-frame:#e20e27;
  --sys-warn-core:#ffc9cd;
  --sys-warn-glow:rgba(240,51,62,.62);
  --sys-warn-soft:rgba(226,14,39,.34);
  --sys-warn-txt:#ffe9ea;
  --sys-warn-halo:0 0 5px rgba(255,201,205,.85),0 0 15px rgba(240,51,62,.5);
  /* 뜻이 걸린 색 두 가지. 시스템창 안에서도 이 뜻은 안 바뀐다 */
  --sys-gold:#f6c41f;   /* 증표 */
  --sys-ok:#73dc75;     /* 은신 */
}
/* 가짜 굵기·가짜 기울임 금지 */
body{font-synthesis:none;-webkit-font-synthesis:none}

/* ── 시스템창 등장 ──────────────────────────────────────────────────────
   창이 세로로 펴지면서 한 번 밝아졌다 가라앉는다. 합성(transform·opacity)과
   filter 만 쓰므로 60fps 를 안 깎는다.
   --sp 로 전체 속도를 조절한다. 1 = 첫 입장, 0.38 = R 재시작(짧게). */
@keyframes sysWin{
  from{opacity:0;transform:scaleY(.55);filter:brightness(2.1)}
  55% {opacity:1;transform:scaleY(1);  filter:brightness(1.18)}
  to  {opacity:1;transform:none;       filter:none}
}
@keyframes sysUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes sysRule{from{opacity:0;transform:scaleX(0)}to{opacity:1;transform:scaleX(1)}}

/* ══ 판 한 벌 (2층 테두리) ═══════════════════════════════════════════════
   1층 = 판에 붙은 1px 헤어라인. 2층 = 판에서 떨어진 네온 브래킷 프레임(.fr).
   ★둥근 모서리를 안 쓴다. 이 화면의 판은 전부 각졌다(계기판·나침반·칩까지).
     하나만 둥글면 그게 곧 두 번째 언어다.
   ★backdrop-filter(진짜 유리 흐림)는 안 쓴다. 캔버스 위에서 매 프레임 도는
     비용이라 게임 프레임을 먹는다. 반투명 필름만으로도 홀로그램으로 읽힌다.
   ★판에 inset 발광을 안 준다(조사 ③). 대신 바깥 그림자는 남긴다 - 1층은 **밝은 봄
     초원**이라 판이 배경에서 안 떨어지면 아무리 예뻐도 안 읽힌다(이 게임의 가독 요구). */
/* ★#load(로딩 화면)는 이 표에 없다. 이 파일의 CSS 는 main.js 맨 끝에서 붙는데
     로딩 화면은 그보다 **먼저** 떠 있어야 하므로, 같은 판을 index.html 이 자기
     인라인 CSS 로 한 벌 더 갖고 있다(그 한 벌이 로딩 화면의 정본이다). */
/* ★★position 을 이 표에 **절대 넣지 말 것.** #bClear 는 boss.js 가 position:fixed +
     transform 으로 화면 가운데를 잡고 있어서, 여기서 relative 로 덮으면 패널이
     문서 흐름으로 돌아가 **화면 밖 아래(top 1097px)**로 사라진다. 실제로 한 번
     그렇게 만들었고 클리어 촬영에서 판이 통째로 안 나와서 잡았다.
     자기 DOM 인 .win 세 개만 아래 줄에서 따로 relative 를 받는다. */
#uiTitle .win,#uiBanner .win,#uiDeath .win{position:relative}
#uiTitle .win,#uiBanner .win,#uiDeath .win,#bClear{
  border:1px solid var(--sys-edge);border-radius:0;
  background-color:var(--sys-bg);
  /* 판 안의 옅은 대각 결. ★없으면 단색 채움이라 값싸 보인다(조사 4번 주의) */
  background-image:
    repeating-linear-gradient(45deg,rgba(143,211,241,.030) 0 1px,transparent 1px 8px),
    repeating-linear-gradient(-45deg,rgba(143,211,241,.016) 0 1px,transparent 1px 13px);
  box-shadow:0 10px 34px rgba(0,0,0,.55);
  font-family:var(--sys-font);font-variant-numeric:tabular-nums}

/* ── 네온 브래킷 프레임 (2층) ────────────────────────────────────────
   판에서 8px 떨어져 위·아래 가로 바 + 좌우 세로 레일이 돌고, **네 모서리는
   45도로 꺾인다**(둥글지도 직각이지도 않은 이 모따기가 SF HUD 브래킷의 표식이다).
   ★가로 바·세로 레일은 4px 띠 안에 1px 선 두 줄이다(원작은 3~4겹 평행선).
   ★모따기 대각선은 45도 그라디언트 한 겹으로 긋는다 - 바의 끝과 레일의 끝을 잇는다.
   ★발광은 여기에만 준다(판은 거의 안 빛난다. 조사 ③). */
#uiTitle .fr,#uiBanner .fr,#uiDeath .fr,#bClear::before{
  --ch:13px;                                   /* 모따기 길이 */
  content:'';position:absolute;inset:-8px;pointer-events:none;
  background-image:
    /* 위 바 · 아래 바 (1px 선 **세 줄**. 레퍼런스는 가로 바가 세로 레일보다 두껍고
       그게 프레임의 무게중심이라, 여기도 바만 한 줄 더 깐다) */
    repeating-linear-gradient(180deg,var(--sys-frame-core) 0 1px,transparent 1px 3px,var(--sys-frame) 3px 4px,transparent 4px 6px,var(--sys-frame) 6px 7px),
    repeating-linear-gradient(0deg,var(--sys-frame-core) 0 1px,transparent 1px 3px,var(--sys-frame) 3px 4px,transparent 4px 6px,var(--sys-frame) 6px 7px),
    /* 좌 레일 · 우 레일 (두 줄) */
    repeating-linear-gradient(90deg,var(--sys-frame-core) 0 1px,transparent 1px 3px,var(--sys-frame) 3px 4px),
    repeating-linear-gradient(270deg,var(--sys-frame-core) 0 1px,transparent 1px 3px,var(--sys-frame) 3px 4px),
    /* 네 귀 45도 모따기 */
    linear-gradient(135deg,transparent calc(50% - 1px),var(--sys-frame) calc(50% - 1px) calc(50% + 1px),transparent calc(50% + 1px)),
    linear-gradient(-135deg,transparent calc(50% - 1px),var(--sys-frame) calc(50% - 1px) calc(50% + 1px),transparent calc(50% + 1px)),
    linear-gradient(45deg,transparent calc(50% - 1px),var(--sys-frame) calc(50% - 1px) calc(50% + 1px),transparent calc(50% + 1px)),
    linear-gradient(-45deg,transparent calc(50% - 1px),var(--sys-frame) calc(50% - 1px) calc(50% + 1px),transparent calc(50% + 1px));
  background-size:
    calc(100% - var(--ch)*2) 7px,calc(100% - var(--ch)*2) 7px,
    4px calc(100% - var(--ch)*2),4px calc(100% - var(--ch)*2),
    var(--ch) var(--ch),var(--ch) var(--ch),var(--ch) var(--ch),var(--ch) var(--ch);
  background-position:
    50% 0,50% 100%,0 50%,100% 50%,
    0 0,100% 0,0 100%,100% 100%;
  background-repeat:no-repeat;
  filter:drop-shadow(0 0 5px var(--sys-glow)) drop-shadow(0 0 16px var(--sys-glow-soft))}
/* 붉은 변주. ★판 색은 그대로 두고 **테두리·프레임·발광·글자만** 붉힌다.
   원작에서 붉은 알림은 상태가 아니라 사건이라, 창의 정체는 그대로여야 한다. */
#uiBanner .win,#uiDeath .win{
  border-color:var(--sys-warn-edge);--sys-rule:rgba(240,51,62,.30)}
#uiBanner .fr,#uiDeath .fr{
  --sys-frame:var(--sys-warn-frame);--sys-frame-core:var(--sys-warn-core);
  --sys-glow:var(--sys-warn-glow);--sys-glow-soft:var(--sys-warn-soft)}

/* ── 창 머리 (「알림」·「경고」·「스킬」) ────────────────────────────────
   ★조사 4번: 상단 중앙 밴드가 아니라 **좌측 정렬 + 테두리 박스 두 개**다.
       [ (!) ] [  알림  ]
     아이콘 박스(정사각, 원 안의 느낌표) + 타이틀 박스(가로로 긴 직사각).
     둘 다 **채움 없음**. 채우는 순간 그냥 다이얼로그가 된다.
     밑줄도 좌우 장식선도 없다 - 박스 테두리가 곧 구분 장치다.
   ★이 한 줄이 "이건 시스템이 나에게 말을 거는 창이다"를 만든다. 없으면 그냥 상자다. */
#uiTitle .hd,#uiBanner .hd,#uiDeath .hd{
  display:flex;align-items:stretch;justify-content:flex-start;gap:5px}
#uiTitle .hd .ic,#uiBanner .hd .ic,#uiDeath .hd .ic{
  position:relative;flex:0 0 19px;height:19px;font-style:normal;
  border:1px solid var(--sys-edge);
  display:flex;align-items:center;justify-content:center;
  font-size:10px;line-height:1;color:var(--sys-key);text-shadow:var(--sys-halo)}
/* 느낌표를 감싸는 가는 원. 원도 획도 얇고 강하게 빛난다 */
#uiTitle .hd .ic::before,#uiBanner .hd .ic::before,#uiDeath .hd .ic::before{
  content:'';position:absolute;inset:3px;border:1px solid currentColor;border-radius:50%;
  opacity:.85}
#uiTitle .hd b,#uiBanner .hd b,#uiDeath .hd b{
  display:flex;align-items:center;border:1px solid var(--sys-edge);
  padding:0 9px 0 calc(9px + .3em);height:19px;
  font-weight:500;font-size:11px;letter-spacing:.3em;
  color:var(--sys-key);text-shadow:var(--sys-halo)}
#uiBanner .hd .ic,#uiDeath .hd .ic,#uiBanner .hd b,#uiDeath .hd b{
  border-color:var(--sys-warn-edge);color:var(--sys-warn-txt);
  text-shadow:var(--sys-warn-halo)}

/* ── 1) 입장 알림창 ──────────────────────────────────────────────────── */
/* ★v95 판정 S3: "층 타이틀 카드가 캐릭터와 정중앙에서 겹친다." 시점이 고정 쿼터뷰라
   캐릭터는 **항상 화면 정중앙**에 선다. 그래서 창을 화면 위쪽 1/3 에 앉힌다.
   ★시스템창은 가로로 눕는 물건이라 예전 세로 붓 조판(3자 286px)보다 훨씬 낮다.
     실측 목표(글자 덩어리 아래끝 ≤ 0.45vh)를 훨씬 여유 있게 지킨다.
   ★사망 창(#uiDeath)은 정중앙 그대로 둔다. 자리만으로도 안 헷갈린다(위=입장, 가운데=사망). */
#uiTitle{position:fixed;inset:0;z-index:12;pointer-events:none;user-select:none;
  display:flex;flex-direction:column;align-items:center;justify-content:flex-start;
  padding-top:clamp(40px,8vh,110px);
  opacity:0;transition:opacity .55s ease;--sp:1}
#uiTitle.on{opacity:1}
#uiTitle.out{opacity:0}
/* 비네트. 화면을 눌러 창만 남긴다.
   ★1층은 **밝은 봄 초원**이다. 어두운 던전 기준으로 옅게 깔면 창이 흙바닥에 묻힌다.
   ★초점을 24% 에 둔다. 밝은 눈은 **창이 있는 자리**여야 한다(46% 는 캐릭터를 비춘다).
   ★11차: 먹빛(중성 검정)에서 밤바다빛(남색 검정)으로 옮겼다. 창이 남색이라
     바탕도 같은 계열이어야 창이 화면 위에 얹힌 조각이 아니라 화면의 일부로 앉는다. */
#uiTitleBg{position:fixed;inset:0;z-index:11;pointer-events:none;opacity:0;
  transition:opacity .6s ease;
  background:
    repeating-linear-gradient(180deg,rgba(150,215,255,.014) 0 1px,transparent 1px 5px),
    radial-gradient(ellipse at 50% 24%,rgba(3,9,20,.56) 0%,rgba(0,2,6,.94) 78%)}
#uiTitleBg.on{opacity:1}
#help,#bHud,#stat{transition:opacity .5s ease}
/* ★★계기판을 물리는 규칙들은 **이 파일 CSS 의 맨 끝**에 모아 뒀다(「연출이 화면을
     소유한다」 블록). 여기 두면 아래쪽의 같은-특이도 규칙에게 진다. */

#uiTitle .win{width:min(430px,78vw);padding:14px 26px 22px;text-align:center;
  transform-origin:50% 0}
#uiTitle.run .win{animation:sysWin calc(.46s*var(--sp)) cubic-bezier(.2,.9,.25,1) both}
/* ★굵게 하지 않는다(조사 ④). 500 안팎 + 넓은 자간 + 강한 헤일로가 이 문법의
     존재감 만드는 법이다. 굵히면 게임 로고가 되고 시스템창이 아니게 된다. */
#uiTitle .bd{padding-top:20px}
#uiTitle .big{font-size:clamp(26px,3.4vh,38px);font-weight:500;letter-spacing:.2em;
  padding-left:.2em;color:#fff;line-height:1.15;
  text-shadow:var(--sys-halo),0 2px 6px rgba(0,0,0,.85)}
#uiTitle .sub{font-size:clamp(13px,1.7vh,17px);font-weight:400;letter-spacing:.2em;
  padding-left:.2em;color:var(--sys-txt);margin-top:9px;
  text-shadow:0 0 9px rgba(65,211,251,.3),0 1px 4px rgba(0,0,0,.9)}
#uiTitle .rule{width:64px;height:1px;margin:14px auto 12px;opacity:0;
  background:linear-gradient(90deg,transparent,var(--sys-edge),transparent)}
#uiTitle .lore{font-size:clamp(11px,1.4vh,13px);letter-spacing:.14em;color:var(--sys-dim);
  padding-left:.14em;opacity:0;text-shadow:0 1px 3px rgba(0,0,0,.9)}
/* 실제 재생은 .run 이 붙을 때만. 클래스를 뺐다 붙이면 같은 창을 다시 틀 수 있다 */
#uiTitle.run .big {animation:sysUp  calc(.42s*var(--sp)) ease-out calc(.20s*var(--sp)) both}
#uiTitle.run .sub {animation:sysUp  calc(.42s*var(--sp)) ease-out calc(.34s*var(--sp)) both}
#uiTitle.run .rule{animation:sysRule calc(.40s*var(--sp)) ease-out calc(.48s*var(--sp)) both}
#uiTitle.run .lore{animation:sysUp  calc(.42s*var(--sp)) ease-out calc(.58s*var(--sp)) both}

/* ── 2) 보스 조우 경고창 ─────────────────────────────────────────────── */
/* 보스 HUD(#bHud)와 **같은 자리**를 쓴다. 배너가 빠지면서 체력바가 그 자리에 든다.
   ★가로 가운데잡기를 transform 으로 안 한다(이 파일이 예전에 밟은 함정이다).
     등장 애니가 transform 을 쓰기 때문에, 창을 transform 으로 가운데에 놓으면
     애니가 붙는 순간 가운데잡기가 통째로 날아간다.
     겉껍질을 화면 폭 전체로 깔고 flex 로 가운데를 잡으면 그 길이 아예 막힌다. */
/* ★padding-top 은 **프레임이 밖으로 8px 나가는 것**까지 세어야 한다. 16px 으로 뒀더니
   네온 프레임 윗변이 화면 맨 위 8px 에 딱 붙어서 「잘린 것처럼」 보였다(실측 컷). */
#uiBanner{position:fixed;left:0;right:0;top:0;z-index:10;
  pointer-events:none;user-select:none;display:flex;justify-content:center;
  padding-top:24px;opacity:0;transition:opacity .45s ease}
#uiBanner.on{opacity:1}
#uiBanner .win{width:min(430px,86vw);padding:13px 24px 18px;text-align:center;
  transform-origin:50% 0}
#uiBanner.on .win{animation:sysWin .40s cubic-bezier(.2,.9,.25,1) both}
#uiBanner .bd{padding-top:17px}
#uiBanner .tag{font-size:12px;letter-spacing:.22em;padding-left:.22em;
  color:rgba(255,233,234,.66);text-shadow:0 1px 4px rgba(0,0,0,.9)}
#uiBanner .name{font-size:clamp(26px,3.6vh,38px);font-weight:500;letter-spacing:.22em;
  padding-left:.22em;color:#fff;margin-top:8px;line-height:1.15;
  text-shadow:var(--sys-warn-halo),0 2px 6px rgba(0,0,0,.9)}
#uiBanner.on .tag {animation:sysUp .40s ease-out .18s both}
#uiBanner.on .name{animation:sysUp .44s ease-out .28s both}
/* 배너가 떠 있는 동안 보스 HUD 를 눌러 둔다. 배너가 **다 빠진 뒤에** 이 클래스가
   풀리고, 그때 boss.js 의 .25s 전환이 이어받아 체력바가 뜬다(boss.js 는 안 건드린다). */
body.uiBossIn #bHud{opacity:0;transition:opacity .3s ease}
#bHud{transition:opacity .4s ease}

/* ── 상단 목표문구 · 보스 체력바 자리 못박기 ────────────────────────── */
#bHud{top:12px;width:min(560px,78vw)}
#bBox{margin-top:11px}
#bName{margin-bottom:6px;line-height:1.25}
#bBar{height:10px}

/* ── 3) 사망 경고창 ──────────────────────────────────────────────────── */
/* enemy.js 의 "쓰러졌다"(#eDead)는 여기 창이 대신한다. 리스폰 로직은 그대로 돈다. */
/* ★v84 QA S2: "여섯 번 죽고 한 번도 죽은 줄 몰랐다." 그래서 화면을 완전히 다른
     그림으로 만든다 - 붉은 경고창 + 큰 한 글자 + HUD 후퇴.
   ★「落」은 남긴다. 이건 붓 장식이 아니라 **도장**이다(한 글자가 "쓰러졌다"를 말한다).
     같은 이유로 나침반의 鬼·符·門 도 남겼다. 다만 획은 붓이 아니라 활자로 그린다. */
#eDead{opacity:0!important}
#uiDeath{position:fixed;inset:0;z-index:11;pointer-events:none;user-select:none;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  opacity:0;transition:opacity .4s ease;
  background:
    radial-gradient(ellipse 44% 36% at 50% 48%,rgba(84,12,8,.28) 0%,rgba(84,12,8,0) 100%),
    radial-gradient(ellipse at 50% 48%,rgba(4,6,12,.90) 0%,rgba(0,1,4,.985) 68%)}
#uiDeath.on{opacity:1}
/* 창이 떠 있는 동안 HUD 를 물린다(입장 창과 같은 규칙) */
body.uiDeathOn #help,body.uiDeathOn #uiDock,body.uiDeathOn #bHud,
body.uiDeathOn #stat,body.uiDeathOn #stHud,body.uiDeathOn #uiHpFloat{opacity:.05}
body.uiDeathOn #uiNav,body.uiDeathOn #uiPip,
body.uiDeathOn #stVig{opacity:.05!important}
#uiDeath .win{width:min(330px,72vw);padding:13px 24px 22px;text-align:center;
  transform-origin:50% 50%}
#uiDeath.on .win{animation:sysWin .30s cubic-bezier(.2,.9,.25,1) both}
#uiDeath .bd{padding-top:10px}
#uiDeath .glyph{font-size:clamp(84px,13vh,124px);font-weight:400;line-height:1.16;
  color:#fff;
  text-shadow:var(--sys-warn-halo),0 0 42px rgba(240,51,62,.45),0 3px 8px rgba(0,0,0,.95)}
#uiDeath .rule{width:96px;height:1px;margin:10px auto 13px;opacity:0;
  background:linear-gradient(90deg,transparent,var(--sys-warn),transparent)}
/* ★판정 S8: 「0.0초 뒤 다시」 - 소수점이 떨려 눈이 붙잡히고 문장이 안 끝난다.
     한 줄로 합치고 정수로 센다 - 「3초 뒤 다시 일어선다」. */
#uiDeath .cnt{font-size:clamp(13px,1.7vh,16px);letter-spacing:.16em;padding-left:.16em;
  color:var(--sys-warn-txt);font-variant-numeric:tabular-nums;
  text-shadow:0 0 9px rgba(240,51,62,.35),0 1px 4px rgba(0,0,0,.95)}
#uiDeath.on .glyph{animation:sysUp  .28s ease-out .06s both}
#uiDeath.on .rule {animation:sysRule .34s ease-out .16s both}
#uiDeath.on .cnt  {animation:sysUp  .28s ease-out .22s both}

/* ── 4) 조작 안내 ────────────────────────────────────────────────────── */
/* 판정 S8·S13 로 다듬은 정보 설계(키 열 오른쪽 정렬·비-키는 맨 아래 주석)는 그대로.
   판만 시스템창 문법으로 갈아입는다(작은 판이라 브래킷은 안 붙인다. 담백하게). */
#help{font-family:var(--sys-font);color:var(--sys-dim);
  transition:opacity .42s ease,transform .42s ease}
#help b{color:var(--sys-txt);font-weight:600}
/* 키캡도 **채우지 않는다.** 1px 헤어라인 박스 하나가 이 문법의 지배 규칙이다
   (조사: 채워진 버튼·둥근 모서리·그림자가 전무하다). */
#help .k{border:1px solid var(--sys-edge);background:rgba(11,31,45,.55);
  color:var(--sys-key);border-radius:0;text-shadow:var(--sys-halo)}
#help .kx{color:var(--sys-mute)}
#help .t{color:var(--sys-dim)}
#help .hSep{background:var(--sys-edge-in)}
#help .hNote{color:var(--sys-mute)}
body.uiHelpOff #help{opacity:0;transform:translateX(-10px)}
/* 「?」 칩. ★둥근 원을 안 쓴다(이 화면의 판은 전부 각졌다) */
#uiHelpChip{position:fixed;left:16px;top:14px;z-index:7;width:30px;height:30px;
  border-radius:0;border:1px solid rgba(143,211,241,.46);
  background:var(--sys-bg-deep);
  box-shadow:0 0 12px rgba(52,140,225,.20);
  color:var(--sys-key);font-family:var(--sys-font);font-size:15px;font-weight:600;
  line-height:28px;text-align:center;user-select:none;cursor:pointer;
  opacity:0;pointer-events:none;
  transition:opacity .42s ease,border-color .2s,color .2s}
body.uiHelpOff #uiHelpChip{opacity:.9;pointer-events:auto}
#uiHelpChip:hover{border-color:rgba(178,231,255,.95);color:#fff}

/* ── 5) HUD 톤 통일 ─────────────────────────────────────────────────── */
/* 기능은 손대지 않는다. 서체·색·테두리만 시스템창으로 맞춘다.
   ★1층 맵이 밝은 봄 초원이라 **글자에 그림자만 줘서는 안 읽힌다.** 조각마다 남색 판을
     깔고 그 위에 청백 글씨를 올린다. 이게 HUD 를 한 벌로 묶는 규칙이다.
   ★#eTxt b 의 transform·transition 은 안 건드린다(처치 팝 애니가 그걸 쓴다).
     색도 b 에만 걸어서 연속처치 클래스(.s1/.s2/.s3)가 계속 이긴다. */
#help,#bGoal,#stat{
  background:var(--sys-bg-deep);
  border:1px solid var(--sys-edge-in);border-radius:0;
  text-shadow:0 1px 3px rgba(0,0,0,.9)}
#eHud,#bHud,#stHud,#stat,#sword,#bGoal,#bName,#bClear,#combo{font-family:var(--sys-font)}
#help{padding:9px 12px 10px}
#bGoal{display:inline-block;padding:4px 14px;color:var(--sys-dim);letter-spacing:.12em;
  border-color:rgba(143,211,241,.26)}
#bGoal i{color:var(--sys-gold);font-style:normal}
/* 보스 이름줄도 같은 판 위에 올린다(밝은 흙바닥 위에서는 이름이 그냥 사라진다).
   ★opacity 는 boss.js 가 inline 으로 쓴다. 여기서는 손대지 않는다 */
#bBox{padding:6px 12px 8px;border-radius:0;
  background:var(--sys-bg-deep);
  border:1px solid rgba(255,124,100,.30);
  box-shadow:0 0 14px rgba(198,44,26,.14),inset 0 1px 0 rgba(255,196,178,.12)}
#bName{font-size:12px;font-weight:600;letter-spacing:.24em;padding-left:.24em;
  color:#ff9c86;text-shadow:0 1px 3px rgba(0,0,0,.95),0 0 12px rgba(198,44,26,.5)}
#bBar{border:1px solid rgba(255,124,100,.34);background:rgba(20,6,6,.86);border-radius:0}
#bFill{filter:saturate(.95)}
#stat{display:inline-block;padding:4px 11px;color:var(--sys-mute);letter-spacing:.06em}
#stat span{color:var(--sys-dim)}

/* ── 아래 계기판 한 벌 (v93 판정 S4) ──────────────────────────────────────
   판정: "HUD 수치가 0개, 떠 있는 섬이 5개." 그래서 하나의 판에 도킹했다.
     [체력 84/100 ▬▬▬▬  처치 3] │ [X 수면참][C 횡일섬] │ [칼 백아]
   11차에서는 **그 구조를 한 칸도 안 바꾸고** 판만 시스템창으로 갈아입힌다.
   ★계기판은 배경이 아니라 **판**이어야 한다. 반투명을 얕게 두면 밝은 풀밭 무늬가
     판을 뚫고 올라와 얼룩진다(첫 시안 확대 컷에서 잡았던 문제다). */
#uiDock{position:fixed;left:50%;bottom:14px;transform:translateX(-50%);z-index:6;
  display:flex;align-items:stretch;pointer-events:none;user-select:none;
  font-family:var(--sys-font);font-variant-numeric:tabular-nums;
  background-color:var(--sys-bg-deep);
  /* 큰 판과 같은 옅은 대각 결. 계기판도 같은 유리라는 표시다 */
  background-image:
    repeating-linear-gradient(45deg,rgba(143,211,241,.026) 0 1px,transparent 1px 8px);
  border:1px solid var(--sys-edge);border-radius:0;
  box-shadow:0 6px 22px rgba(0,0,0,.55);
  transition:opacity .5s ease}
/* 판 위쪽에 청백 실선 한 올. 이 한 줄이 「계기판의 윗변」을 만들어 준다 */
#uiDock::before{content:'';position:absolute;left:10px;right:10px;top:-1px;height:1px;
  background:linear-gradient(90deg,transparent,rgba(178,231,255,.62) 24%,
             rgba(178,231,255,.62) 76%,transparent)}
/* ★white-space:nowrap 이 여기 있는 이유: 좁은 창에서 「수면참」이 「수면/참」으로 접혀
   계기판이 두 줄로 부푸는 것을 막는다. */
#uiDock .cell{position:relative;display:flex;align-items:center;gap:10px;padding:7px 15px;
  white-space:nowrap}
#uiDock .cell *{white-space:nowrap}
#uiDock .cell + .cell::before{content:'';position:absolute;left:0;top:50%;height:22px;
  margin-top:-11px;width:1px;background:var(--sys-edge-in)}
/* 셀 이름표. 작고 낮게 - 값이 주인공이고 이름표는 길잡이다 */
#uiDock .lb{font-size:10px;letter-spacing:.22em;color:var(--sys-mute);
  white-space:nowrap;text-shadow:0 1px 2px rgba(0,0,0,.9)}

/* 체력 셀. #eHud 를 통째로 옮겨 담았다(자리는 셀이 잡으므로 여백은 0) */
#eHud{position:static;display:flex;align-items:center;gap:0;left:auto;bottom:auto}
/* ★빈 트랙이 **항상** 보여야 한다(판정 S4). 트랙을 한 단 어둡게 내리고 테를 둘러
     놓으면 채워진 부분과 빈 부분이 늘 같이 읽힌다. */
#eBar{position:relative;width:236px;height:18px;
  border:1px solid rgba(143,211,241,.32);background:rgba(4,11,22,.92);border-radius:0}
/* ★색(초록/노랑/빨강)은 enemy.js 가 inline 으로 쓴다. 그건 **정보**라 안 건드린다.
     남색 판 위에서 살짝 눌러 준다(원색 그대로면 판에서 튄다). */
#eFill{filter:saturate(.86) brightness(.96)}
/* 임계 눈금 25·50·75%. ★75% 는 그냥 눈금이고 25% 만 붉다 - 여기부터가 한 대에 죽는 구간 */
#eBar::after{content:'';position:absolute;inset:0;pointer-events:none;
  background:
    linear-gradient(90deg,transparent 0 calc(25% - 1px),rgba(255,106,85,.66) calc(25% - 1px) 25%,transparent 25%),
    linear-gradient(90deg,transparent 0 calc(50% - 1px),rgba(3,10,20,.62) calc(50% - 1px) 50%,transparent 50%),
    linear-gradient(90deg,transparent 0 calc(75% - 1px),rgba(3,10,20,.62) calc(75% - 1px) 75%,transparent 75%)}
/* 숫자. ★트랙 **위에** 얹으면 눈금 실선이 숫자를 가로질러 갈라져 읽힌다. 오른쪽에 세운다.
   폭이 안 흔들리게 tabular-nums 를 박고 자리도 못박는다(숫자가 흔들리면 판이 떤다). */
#uiHpNum{display:inline-flex;align-items:baseline;min-width:62px;justify-content:flex-end;
  font-size:13px;font-weight:700;letter-spacing:.02em;
  color:#fff;font-variant-numeric:tabular-nums;text-shadow:0 1px 3px rgba(0,0,0,.95)}
#uiHpNum s{text-decoration:none;color:var(--sys-mute);font-weight:400;font-size:11px;margin:0 1px}
#uiHpNum u{text-decoration:none;color:var(--sys-dim);font-weight:400;font-size:11px}
/* 25% 밑으로 떨어지면 숫자를 붉게 물린다. 눈금과 같은 뜻을 두 번 말해 준다 */
#uiHpNum.low{color:var(--sys-warn)}
/* 처치 수. 체력 셀 안에 실선 하나 두고 붙인다.
   ★실선 높이는 셀 사이 실선과 같아야 한다(길이가 다른 칸막이가 둘이면 실수로 보인다). */
#eTxt{position:relative;margin-left:2px;padding-left:13px;
  color:var(--sys-mute);letter-spacing:.14em;font-size:12px;white-space:nowrap}
#eTxt::before{content:'';position:absolute;left:0;top:50%;height:22px;width:1px;
  margin-top:-11px;background:var(--sys-edge-in)}
#eTxt b{color:var(--sys-txt)}

/* 칼 셀. ★main.js 가 inline 으로 0.45 를 쓰므로 !important 가 필요하다.
   ★display 는 안 건드린다. 칼이 없는 몸(궁수)에서 main.js 가 none 을 넣고,
     그때는 JS 가 셀째로 접는다. */
#sword{position:static;right:auto;bottom:auto;opacity:1!important;
  font-size:14px;font-weight:600;letter-spacing:.12em;padding-left:.12em;
  color:var(--sys-txt);text-shadow:0 1px 3px rgba(0,0,0,.95)}

/* 은신 알림은 계기판 위로 물러난다 */
#stHud{bottom:86px}
/* 은신 줄. 초록/주황이 무슨 뜻인지는 그대로 두고 판만 시스템창으로 내린다.
   ★v84 QA S13: 「숨었다」가 수풀 위에서 안 읽혔다(초록 글자를 초록 위에 얹었으니까).
     판을 거의 검게 내리고 글자를 흰 쪽으로 올린다. 테두리가 상태를 먼저 알린다. */
#stHud{border-radius:0;letter-spacing:.2em;font-weight:600;font-size:13px;
  padding:6px 16px}
#stHud.hide{color:#e6fbf1;background:linear-gradient(180deg,rgba(5,26,20,.92),rgba(2,14,11,.95));
  border:1px solid var(--sys-ok);
  box-shadow:0 0 14px rgba(24,140,96,.26),inset 0 1px 0 rgba(150,255,214,.14);
  text-shadow:0 1px 3px #000}
#stHud.loud{color:#ffe6bf;background:linear-gradient(180deg,rgba(30,16,3,.92),rgba(16,8,2,.95));
  border:1px solid #d79a3c;
  box-shadow:0 0 14px rgba(150,96,16,.26),inset 0 1px 0 rgba(255,214,150,.14);
  text-shadow:0 1px 3px #000}
/* 은신 비네트. stealth.js 것을 여기서 덮는다(이 style 이 나중에 붙어 이긴다).
   ★가장자리를 **어둡게** 눌러야 "숨었다"가 한눈에 온다(밝기 대비가 정보를 나른다). */
#stVig{box-shadow:inset 0 0 190px 62px rgba(2,8,7,.72),
                  inset 0 0 70px 8px rgba(24,120,70,.30)}
#stVig.loud{box-shadow:inset 0 0 190px 62px rgba(10,5,0,.74),
                       inset 0 0 70px 8px rgba(150,96,16,.34)}
/* 콤보 숫자(평타 「1타」). ★transform 은 main.js 가 inline 으로 쓴다(여기서 절대 잡지 말 것) */
#combo{font-weight:800;color:#eaf5ff;letter-spacing:.1em;
  font-variant-numeric:tabular-nums;
  text-shadow:0 0 20px rgba(90,180,255,.5),0 0 8px rgba(0,0,0,.85),0 3px 6px #000}
/* 누적 명중 수. 한 번에 여럿을 벤 그 사실만 조용히 알리는 자리라 크기를 확 낮춘다 */
#combo i{font-style:normal;font-weight:500;
  font-size:.32em;letter-spacing:.1em;color:var(--sys-dim);margin-left:.55em;
  vertical-align:middle;text-shadow:0 1px 3px rgba(0,0,0,.95)}

/* ── 6) 결과창 (층 돌파) ─────────────────────────────────────────────── */
/* boss.js 가 만든 DOM(#bClear h1/table/.hint)은 그대로 두고 CSS 만 덮는다.
   ★라벨-값 두 칸 정렬은 원래 이 문법의 **정석**이다(예전에는 이것만 서구식 stat box
     라고 지적받았는데, 그건 주변이 전부 붓·먹이었기 때문이다. 이제는 여기가 기준이다).
   ★transform 을 덮을 때 translate(-50%,-50%) 를 **반드시 같이 적는다.** boss.js 가
     그걸로 화면 가운데를 잡고 있어서, scale 만 쓰면 패널이 오른쪽 아래로 밀려난다.
   ★그래서 이 판만 등장 애니에 sysWin(scaleY)을 못 쓴다. 대신 opacity + 미세 scale 로
     같은 인상을 낸다(가운데잡기가 transform 에 묶여 있는 판의 숙명이다). */
#bClear{padding:0;border-radius:0;min-width:min(360px,86vw);
  transition:opacity .45s ease,transform .45s cubic-bezier(.2,.9,.25,1);
  transform:translate(-50%,-50%) scale(.965)}
#bClear.uiIn{transform:translate(-50%,-50%) scale(1)}
/* 창 머리 「결과」. ★#bClear 의 자식 구조는 boss.js 것이라 한 칸도 못 늘린다.
   그래서 가상요소 두 개를 나눠 쓴다 - ::before 는 위 프레임 규칙이 이미 가져갔고
   (네온 브래킷), ::after 가 머리 박스 하나를 그린다.
   ★다른 창은 [!] 박스 + [낱말] 박스 두 개인데 여기만 한 개다. 가상요소가 둘뿐이라
     생기는 제약이고, 남의 DOM 을 안 건드린다는 규칙이 그보다 위다. */
#bClear::after{content:'${CLEAR_HEAD}';position:absolute;left:26px;top:22px;
  display:flex;align-items:center;height:19px;padding:0 9px 0 calc(9px + .3em);
  border:1px solid var(--sys-edge);
  font-size:11px;font-weight:500;letter-spacing:.3em;
  color:var(--sys-key);text-shadow:var(--sys-halo)}
#bClear h1{font-size:30px;font-weight:500;letter-spacing:.24em;padding-left:.24em;
  color:#fff;margin:0;padding-top:64px;line-height:1.15;
  text-shadow:var(--sys-halo),0 2px 6px rgba(0,0,0,.9)}
/* 표. 칸 여백을 없애고 줄마다 실선을 깐다 - 라벨은 왼쪽, 값은 오른쪽 끝.
   ★라벨-값 정렬은 원래 이 문법의 정석이라 구조를 그대로 살렸다. */
#bClear table{width:auto;min-width:min(300px,74vw);margin:24px 30px 0;
  font-size:13px;color:var(--sys-dim);border-spacing:0}
#bClear td{padding:9px 0;border-bottom:1px solid var(--sys-edge-in);
  font-weight:400;letter-spacing:.1em;text-align:left;white-space:nowrap;
  text-shadow:0 1px 2px rgba(0,0,0,.9)}
#bClear tr:last-child td{border-bottom:none}
#bClear td.v{color:var(--sys-txt);font-weight:500;font-size:14px;
  text-align:right;padding-left:34px;letter-spacing:.04em;
  font-variant-numeric:tabular-nums;
  text-shadow:0 0 8px rgba(65,211,251,.3),0 1px 3px rgba(0,0,0,1)}
#bClear .hint{margin:18px 30px 22px;font-size:11px;
  letter-spacing:.16em;color:var(--sys-mute)}
#bClear.uiIn h1{animation:sysUp .5s ease-out .06s both}
/* 결과창이 뜨면 상단 목표 알약을 접는다.
   ★판정 S9: 알약도 「층 돌파」, 창 제목도 「층 돌파」. 답을 말한 쪽만 남긴다. */
body.uiCleared #bHud{opacity:0;transition:opacity .45s ease}

/* ── 클리어 암막 ─────────────────────────────────────────────────────── */
/* v72 QA #15: 패널이 뜬 채로 계속 걸어다닐 수 있었다. 입력은 main.js 가 잠그고,
   여기서는 "판이 끝났다"를 눈으로 못박는다. 패널(z 8)보다 아래, HUD(z 6)보다 위. */
#uiClearDim{position:fixed;inset:0;z-index:7;pointer-events:none;opacity:0;
  transition:opacity .7s ease;
  background:radial-gradient(ellipse at 50% 50%,rgba(2,6,14,.30) 0%,rgba(0,2,6,.66) 84%)}
body.uiCleared #uiClearDim{opacity:1}

/* ── 7) 스킬 칩 (X 수면참 · C 횡일섬) ──────────────────────────────── */
/* v72 QA #16: 두 기술이 언제 되는지 화면 어디에도 안 나왔다. 쿨다운이 따로 없고
   "휘두르는 중이면 못 쓴다"가 전부라, 그 한 가지를 상태로 보여준다. */
#uiSkills{position:static;left:auto;bottom:auto;transform:none;
  display:flex;gap:8px;pointer-events:none;user-select:none;
  font-family:var(--sys-font);transition:opacity .5s ease}
/* ★v84 QA #9: 준비와 불가의 차이가 **투명도뿐**이라 둘 다 "흐릿한 칩"으로 읽혔다.
   투명도는 정보가 아니다. 그래서 세 가지를 한꺼번에 바꾼다.
     준비 : 청백 테두리가 켜지고 글자가 하얘진다 (= 지금 쓸 수 있다)
     불가 : 판이 가라앉고 글자가 물리고 **시계 방향 쿨다운**이 덮인다
   투명도는 둘 다 1 로 고정한다. */
#uiSkills .sk{position:relative;overflow:hidden;
  display:flex;align-items:center;gap:7px;padding:4px 11px 5px 13px;
  background:linear-gradient(180deg,rgba(11,25,46,.80),rgba(5,13,26,.88));
  border:1px solid var(--sys-edge-in);border-radius:0;
  transition:background .16s ease,border-color .16s ease,box-shadow .16s ease}
#uiSkills .sk .key{min-width:17px;padding:0 4px;text-align:center;font-size:11px;
  line-height:16px;color:var(--sys-key);border:1px solid rgba(143,211,241,.34);
  background:rgba(8,20,38,.8);border-radius:2px;
  transition:color .16s ease,border-color .16s ease}
#uiSkills .sk .nm{font-size:13px;font-weight:600;letter-spacing:.1em;padding-left:.1em;
  color:var(--sys-txt);text-shadow:0 1px 2px rgba(0,0,0,.95);transition:color .16s ease}
/* 준비 */
#uiSkills .sk.rdy{border-color:var(--sys-edge);
  background:linear-gradient(180deg,rgba(15,35,62,.86),rgba(7,18,34,.92));
  box-shadow:0 0 10px rgba(52,140,225,.22)}
#uiSkills .sk.rdy .nm{color:#fff}
#uiSkills .sk.rdy .key{color:#fff;border-color:rgba(178,231,255,.7)}
/* 불가 */
#uiSkills .sk.off{border-color:rgba(143,211,241,.10);
  background:linear-gradient(180deg,rgba(5,12,22,.86),rgba(3,8,16,.92));box-shadow:none}
#uiSkills .sk.off .nm{color:#4d6076}
#uiSkills .sk.off .key{color:#4d6076;border-color:rgba(143,211,241,.12);background:rgba(4,10,19,.8)}
/* 쿨다운 라디얼. ★v93 판정 S4: "잔여 시간이 화면에 없다."
   롤·도타가 쓰는 **시계 방향 쓸기**다. 칩 전체를 덮고 12시부터 돌아 걷힌다.
   ★conic-gradient 문자열을 20Hz 로 다시 쓴다. 페인트만 도는 일이라 프레임을 안 깎는다. */
#uiSkills .sk .cd{position:absolute;inset:0;pointer-events:none;opacity:0;
  transition:opacity .1s ease}
#uiSkills .sk.off .cd{opacity:1}
#uiSkills .sk.gone{display:none}
/* 회피 칩만 조건이 하나 더 붙는다. Space 혼자 누르면 점프고, 이동 중이어야 회피다.
   ★칩 마크업은 main.js 가 만든다. 남의 구조를 안 건드리려고 조건 글자만 CSS 로 세운다.
     키캡 밖에 두는 것이 규칙에 맞다(「이동+」는 키가 아니라 조건이다).
   ★main.js 가 나중에 자기 마크업에 「이동+」를 직접 넣으면 이 줄을 지워야 두 번 안 붙는다. */
#uiSkills .sk[data-k="Dash"]::before{content:'이동+';margin-right:-4px;
  font-size:11px;line-height:16px;letter-spacing:0;color:var(--sys-mute);
  white-space:nowrap;text-shadow:0 1px 2px rgba(0,0,0,.95);transition:color .16s ease}
#uiSkills .sk.rdy[data-k="Dash"]::before{color:var(--sys-dim)}
#uiSkills .sk.off[data-k="Dash"]::before{color:#4d6076}

/* ── 8) 목표 방향 나침반 ─────────────────────────────────────────────── */
/* 3차 QA: **블라인드 18분간 보스를 육안으로 한 번도 못 봤다.** 그래서 셋을 바꿨다.
     (가) 판 + 한 글자(鬼 · 符 · 門). 무엇을 가리키는지 화살표 자신이 말한다
     (나) 크기 2배(화살 26x18 + 46px 판)
     (다) 은은한 명멸. 정지한 그림은 밝은 배경에서 지형으로 읽힌다
   ★11차: **글리프와 크기는 한 점도 안 바꿨다**(정보로서 잘 작동해 온 자산이다).
     판만 시스템 칩으로 갈아입힌다. 단계 색도 뜻을 그대로 지킨다(아래 NAV_KIND). */
#uiNav{position:fixed;left:50%;top:50%;z-index:6;pointer-events:none;user-select:none;
  transform:translate(-50%,-50%);opacity:0;width:0;height:0;
  transition:opacity .35s ease,left .12s linear,top .12s linear;
  --nav-ink:#e9f4ff;--nav-glow:rgba(255,90,64,.55)}
/* 화살은 판 **둘레를 돈다.** .dial 만 돌리고 글자는 안 돌린다(뒤집힌 鬼 는 못 읽는다) */
#uiNav .dial{position:absolute;left:0;top:0;width:0;height:0;
  transition:transform .1s linear}
/* ★길쭉해야 한다. 26x18(비율 1.43)이라야 비스듬히 돌아가도 뾰족한 끝이 읽힌다.
   ★밑변까지의 거리 36px 은 판 대각선 반지름(23*√2 = 32.5px)에서 나온 값이다.
     31px 로 두면 화살이 비스듬할 때만 판 모서리를 파고든다. */
#uiNav .tip{position:absolute;left:0;top:0;width:0;height:0;
  transform:translate(36px,-10px);
  border-left:28px solid var(--nav-ink);
  border-top:10px solid transparent;border-bottom:10px solid transparent;
  filter:drop-shadow(0 1px 2px rgba(0,0,0,.95)) drop-shadow(0 0 8px rgba(0,0,0,.6))}
/* 판 + 한 글자 */
#uiNav .plate{position:absolute;left:50%;top:50%;
  width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:0;
  background:var(--sys-bg-deep);
  border:1px solid rgba(143,211,241,.5);
  display:flex;align-items:center;justify-content:center;
  font-family:var(--sys-font);font-weight:600;font-size:26px;line-height:1;
  color:var(--nav-ink);text-shadow:0 1px 3px rgba(0,0,0,1),0 0 12px rgba(0,0,0,.85);
  box-shadow:0 2px 12px rgba(0,0,0,.7)}
/* 한자 첫 등장 라벨. ★단계마다 딱 한 번, 2.6초만 붙었다 사라진다(판정 S8).
   鬼·符·門 은 주석이 없으면 못 읽는 사람이 있는데, 한 번 짝을 보여 주면 그 뒤로는
   글자만으로 읽힌다. */
#uiNav .cap{position:absolute;left:50%;top:50%;transform:translate(-50%,0);
  margin-top:26px;padding:2px 7px;white-space:nowrap;border-radius:0;
  background:var(--sys-bg-deep);
  border:1px solid rgba(143,211,241,.38);
  font-family:var(--sys-font);font-size:11px;letter-spacing:.14em;color:var(--sys-key);
  text-shadow:0 1px 2px #000;opacity:0;transition:opacity .35s ease}
#uiNav .cap.on{opacity:1}
/* 명멸. 판이 2.2초에 한 번 은은하게 숨을 쉰다.
   ★크기·투명도를 흔들면 "깜빡이는 경고등"이 된다. 여기 필요한 건 숨 쉬는 정도다.
   ★★예전에는 **box-shadow 자체를 키프레임으로 흔들었다.** 주석에는 「합성만 쓰므로
     프레임을 안 깎는다」고 적혀 있었는데 **틀린 말이었다** - box-shadow 는 합성이
     아니라 페인트라, 나침반이 떠 있는 내내 매 프레임 판을 다시 그린다.
     A/B 실측(2026-08-11, 왕복 3회 교대): 이 애니 하나를 끄면 37.2 → 41.8fps.
     **4.6fps(11%)를 여기서 먹고 있었다.**
     고치는 법: 발광을 **따로 깔아 두고 그 겹의 opacity 만** 흔든다. 그림자는 한 번만
     그려지고 그 뒤로는 합성기가 알파만 곱한다(진짜 합성 전용 경로다).
   ★::after 는 position:absolute 라 flex 줄에 안 낀다(.plate 는 flex 통이다). */
#uiNav .plate::after{content:'';position:absolute;inset:-1px;pointer-events:none;
  box-shadow:0 0 14px 2px var(--nav-glow);opacity:0;
  animation:uiNavPulse 2.2s ease-in-out infinite}
@keyframes uiNavPulse{0%,100%{opacity:0}50%{opacity:1}}

/* ── 9) 가까운 요괴 무리 마커 ────────────────────────────────────────── */
/* 15m 안에 무리가 있으면 그 방향에 작은 판 하나. 라벨도 명멸도 없다.
   ★보스 화살보다 훨씬 약해야 한다. 둘이 비슷해지면 "어느 쪽이 진짜 목표냐"가 흐려진다.
   ★v95 판정 S11: "마커 언어가 두 벌이다." 그래서 나침반과 **같은 문법**으로 옮겼다 -
     같은 남색 판, 같은 테, 같은 각진 모서리. 다만 소형(18px 대 46px)이고
     판 안에는 아무 뜻 없는 점 하나만 남는다. */
#uiPip{position:fixed;left:50%;top:50%;z-index:5;pointer-events:none;user-select:none;
  transform:translate(-50%,-50%);width:18px;height:18px;border-radius:0;opacity:0;
  display:flex;align-items:center;justify-content:center;
  background:var(--sys-bg-deep);
  border:1px solid rgba(143,211,241,.42);
  box-shadow:0 1px 6px rgba(0,0,0,.85);
  transition:opacity .3s ease,left .12s linear,top .12s linear}
/* 판 안의 점. 나침반의 한 글자가 앉는 자리와 같은 자리다 */
#uiPip::after{content:'';width:5px;height:5px;border-radius:50%;
  background:rgba(191,225,255,.9);box-shadow:0 0 6px rgba(143,211,241,.7)}
/* ★v93 판정 S11: 점이 무슨 뜻인지 화면 어디에도 없다. 판을 붙이면 나침반과 격이
   같아지므로, **처음 한 번만** 2.6초짜리 작은 라벨을 달고 그 뒤로는 점으로 돌아간다. */
#uiPip .cap{position:absolute;left:50%;top:21px;transform:translateX(-50%);
  padding:2px 7px;white-space:nowrap;border-radius:0;
  background:var(--sys-bg-deep);
  border:1px solid rgba(143,211,241,.34);
  font-family:var(--sys-font);font-size:11px;letter-spacing:.14em;color:var(--sys-key);
  text-shadow:0 1px 2px #000;opacity:0;transition:opacity .35s ease}
#uiPip .cap.on{opacity:1}

/* ── 10) 기술 이름 콜아웃 ────────────────────────────────────────────────
   판정 S14: "기술이 나갈 때 뜨는 이름이 소박하다." 그래서 **작은 시스템 팝**으로 만든다.
     「스킬」 머리 한 줄 + 이름(크게) + 型 번호(작게)
   ★수명은 안 건드린다. 0.9초는 main.js 의 comboT 가 정하고 그게 맞는 값이다.
   ★크기를 **키우지 않는다**(오너 기조: 이펙트는 절제). 예전 44px 한 줄이 먹던
     화면보다 오히려 좁게 잡았다.
   ★평타 「1타」 는 이 창을 안 씌운다. 그건 수치라 맨 숫자가 맞고, 여기에 창을 씌우면
     매 타격마다 창이 떠서 창이 값싸진다.
   ★transform 은 main.js 가 인라인으로 쓴다(translateX(-50%) scale). 여기서 절대
     잡지 말 것 - 잡으면 등장 팝이 통째로 죽는다. 자리 잡기는 부모(#combo)가 한다.
   ★크기를 em 이 아니라 px 로 못박는다. 부모 #combo 는 44px 인데 그 배수로 잡으면
     main.js 의 scale 애니와 곱해져서 창이 출렁인다. */
#combo .uiCall{display:inline-flex;flex-direction:column;align-items:flex-start;
  vertical-align:middle;padding:8px 18px 10px;text-align:left;
  border:1px solid var(--sys-edge);border-radius:0;
  background-color:var(--sys-bg);
  background-image:
    repeating-linear-gradient(45deg,rgba(143,211,241,.030) 0 1px,transparent 1px 8px);
  box-shadow:0 4px 16px rgba(0,0,0,.6);
  font-family:var(--sys-font)}
/* 머리는 다른 창과 같은 **테두리 박스**다(채우지 않는다). 작은 팝이라 [!] 는 뺐다 */
#combo .uiCall .hd{display:inline-flex;align-items:center;align-self:flex-start;
  height:16px;padding:0 8px 0 calc(8px + .3em);
  border:1px solid var(--sys-edge);
  font-size:9px;font-weight:500;letter-spacing:.3em;
  color:var(--sys-key);text-shadow:var(--sys-halo)}
#combo .uiCall .nm{display:block;font-size:22px;font-weight:500;letter-spacing:.14em;
  padding-left:.14em;color:#fff;line-height:1.25;margin-top:9px;
  text-shadow:var(--sys-halo),0 2px 5px rgba(0,0,0,.9)}
/* 型 번호. 창을 설명하는 작은 말이라 한 단 물린다 */
#combo .uiCall .ty{display:block;font-size:10px;font-weight:500;letter-spacing:.24em;
  padding-left:.24em;color:var(--sys-dim);margin-top:3px;
  text-shadow:0 1px 3px rgba(0,0,0,.95)}
/* 누적 명중 수는 창 **밖**에 그대로 남는다(main.js 가 붙이는 <i> 와 같은 자리) */
#combo .uiCall + i{vertical-align:middle}

/* ── 11) 좁은 창 (판정 S2) ───────────────────────────────────────────────
   판정: "계기판이 874px 고정이라 CSS 폭 921px 미만에서 좌우가 잘린다."
   ★해결은 두 겹이다.
     (가) 절대 안전망: max-width 로 창을 절대 안 넘게 한다.
     (나) 진짜 해결: 좁아지면 **줄어든다.** 체력 트랙·칩 여백·자간을 단계로 깎는다.
          800px 에서 모든 글자가 그대로 읽혀야 한다.
   ★글자 크기는 마지막에 건드린다. 먼저 깎을 것은 **여백과 트랙 폭**이다.
   ★min-width 를 안 쓴다. 쓰면 그 값 밑에서 다시 잘리는 벽이 생길 뿐이다. */
#uiDock{max-width:calc(100vw - 16px)}
@media (max-width:1000px){
  #uiDock .cell{padding:6px 11px;gap:8px}
  #eBar{width:170px}
  #uiHpNum{min-width:56px;font-size:12px}
  #eTxt{padding-left:10px;letter-spacing:.10em}
  #uiSkills{gap:6px}
  #uiSkills .sk{padding:3px 9px 4px 10px;gap:6px}
  #uiSkills .sk .nm{font-size:12px;letter-spacing:.06em}
  #sword{font-size:13px;letter-spacing:.08em}
  #uiDock .lb{letter-spacing:.14em}
  /* 도움말 판. 키 열 폭이 가장 크게 먹는다(106px) */
  #help{font-size:12px;padding:8px 10px 9px}
  #help .ks{flex:0 0 96px}
}
@media (max-width:860px){
  #uiDock{bottom:10px}
  #uiDock .cell{padding:5px 8px;gap:6px}
  #eBar{width:118px;height:16px}
  #uiHpNum{min-width:50px;font-size:11px}
  #uiHpNum s,#uiHpNum u{font-size:10px}
  #eTxt{padding-left:8px;font-size:11px;letter-spacing:.06em}
  #eTxt::before,#uiDock .cell + .cell::before{height:18px;margin-top:-9px}
  #uiSkills{gap:5px}
  #uiSkills .sk{padding:3px 7px 4px 8px;gap:5px}
  #uiSkills .sk .nm{font-size:11.5px;letter-spacing:.04em}
  #uiSkills .sk .key{min-width:15px;padding:0 3px;font-size:10px}
  #uiSkills .sk[data-k="Dash"]::before{font-size:10px}
  #sword{font-size:12.5px;letter-spacing:.04em}
  #uiDock .lb{font-size:9px;letter-spacing:.08em}
  #help{font-size:11.5px;line-height:1.55;padding:7px 9px 8px}
  #help .ks{flex:0 0 88px;gap:3px}
  #help .k{min-width:21px;padding:1px 5px;font-size:11px}
  #help .kx,#help .hNote{font-size:11px}
}
/* 세로가 짧은 창(노트북 전체화면 아님 등). 창이 화면 밖으로 밀리는 것을 막는다 */
@media (max-height:560px){
  #uiTitle{padding-top:clamp(24px,5vh,56px)}
  #uiTitle .win{padding:12px 22px 18px}
  #uiDeath .glyph{font-size:clamp(64px,11vh,92px)}
}

/* ── 12) 머리 위 체력바 (12차. 오너 지시: 「체력바는 캐릭터 머리 위로, 롤처럼」) ──
   롤 문법 그대로다. 캐릭터 머리 위에 **월드를 따라다니는** 작은 트랙 하나.
   ★아래 계기판의 체력 셀·숫자는 **그대로 둔다.** 롤도 머리 위 바와 하단 HUD 를
     이중으로 쓴다. 하나를 없애면 「지금 몇 남았나」와 「위험한가」 중 하나가 죽는다.
   ★수치를 안 얹는다. 숫자는 계기판에 이미 있고, 머리 위 숫자는 전투 중에 읽히지도
     않으면서 캐릭터 얼굴을 가린다(롤 기본 HUD 도 머리 위에는 숫자가 없다).
   ★폭은 **화면 px 고정**이다. 휠 줌(18~32m)으로 캐릭터가 커졌다 작아져도 바는 안 변한다.
     월드 크기로 매달면 멀어질 때 2~3px 이 돼서 읽을 수가 없다.
   ★시스템창 문법을 그대로 탄다: 각진 1px 헤어라인 + 한 단 눌린 판. 발광은 **안 준다**
     (조사 ③). 대신 바깥 그림자 한 겹만 남긴다 - 1층은 밝은 봄 풀밭이라 그게 없으면
     바가 배경에 녹는다(계기판이 같은 이유로 그림자를 갖고 있다).
   ★자리는 JS 가 **transform 으로만** 쓴다. left/top 을 매 프레임 쓰면 레이아웃이 돈다. */
#uiHpFloat{position:fixed;left:0;top:0;z-index:5;width:84px;height:9px;
  pointer-events:none;user-select:none;opacity:0;
  border:1px solid rgba(143,211,241,.42);background:rgba(4,11,22,.88);
  box-shadow:0 1px 4px rgba(0,0,0,.62);
  transition:opacity .18s ease;will-change:transform}
#uiHpFloat.on{opacity:1}
#uiHpFloat i{position:absolute;left:0;top:0;bottom:0;display:block}
/* 잔상. 방금 깎여 나간 만큼이 잠깐 남았다가 따라 줄어든다(폭은 JS 가 매 프레임 쓴다).
   ★채움보다 **뒤에** 깔린다(문서 순서). 그래야 줄어든 구간에서만 보인다. */
#uiHpFloat .gh{background:rgba(255,120,92,.52);transition:background .2s ease}
/* 채움. 색(초록/노랑/빨강)은 enemy.js 의 규칙을 그대로 쓴다 - 뜻이 걸린 색이라 안 바꾼다.
   계기판은 남색 판 위라 많이 눌러 놨지만, 이건 풀밭 위라 살짝만 눌러 준다. */
#uiHpFloat .fl{filter:saturate(.92);transition:filter .2s ease}
/* 맞은 순간. ★번쩍이는 것은 **방금 깎여 나간 칸**(잔상)이다. 남은 체력을 하얗게
   태우면 그 순간 색(초록/노랑/빨강)이 사라져서 "얼마나 위험한가"를 못 읽는다.
   남은 쪽은 살짝만 들어 올리고 테두리만 같이 밝힌다. 0.2초에 걸쳐 가라앉는다. */
#uiHpFloat.hit{border-color:rgba(255,224,224,.92)}
/* ★남은 쪽 밝기는 1.2 를 넘기지 않는다. 1.45 로 두니 옅은 쪽 끝이 흰색으로 타서
     초록 바가 통째로 청백색으로 읽혔다(f08 실측 (191,255,255)). 색이 곧 뜻이다. */
#uiHpFloat.hit .fl{filter:saturate(.92) brightness(1.2);transition:none}
#uiHpFloat.hit .gh{background:rgba(255,247,240,.95);transition:none}
/* 세로가 짧은 창에서는 캐릭터도 그만큼 작게 잡힌다. 바도 같이 줄인다 */
@media (max-height:620px){ #uiHpFloat{width:68px;height:8px} }

/* ══ 연출이 화면을 소유한다 (판정 S4 · S5 · S6 · S7) ═══════════════════════
   ★★이 블록은 **반드시 이 파일 CSS 의 맨 끝**에 있어야 한다. 여기 적힌 선택자는
     전부 (0,2,0) 이라 「body.uiHelpOff #uiHelpChip{opacity:.9}」 같은 앞쪽 규칙과
     특이도가 같다. 앞에 두면 나중에 쓴 쪽이 이겨서 **조각 하나만 안 물러난다**
     (실측: 배너가 떠 있는 동안 왼쪽 위 「?」 칩만 혼자 켜져 있었다).
     새 상태를 넣을 때도 이 블록에 넣을 것.

   판정: 보스 배너·처치 컷·결과창이 도는 동안에도 도움말 판·목표 알약·계기판·
   나침반이 그대로 서 있어서 어느 것이 지금 화면의 주인인지 안 갈렸다. 특히 배너는
   좁은 창에서 왼쪽 도움말 판과 실제로 겹쳤다. z-index 를 올려 덮는 것은 답이 아니다 -
   덮어도 밑에 판이 비쳐 지저분하다. **도는 동안은 아예 물린다.**

   네 상태가 하는 일이 같아서 한 표로 적는다.
     uiTitleOn = 입장·재시작 알림창 (.06 으로 물린다. 완전히 끄면 판이 멎은 것처럼 보인다)
     uiBossIn  = 보스 경고창 (2.5s + 0.46s)
     uiCine    = 보스가 쓰러지는 컷 (CINE_KILL)
     uiCleared = 층 돌파 결과창 (판이 끝날 때까지)
   ★#uiDeath(사망 창)의 표는 위쪽 3) 절에 그대로 둔다. */
body.uiTitleOn #help,body.uiTitleOn #uiHelpChip,body.uiTitleOn #uiDock,
body.uiTitleOn #bHud,body.uiTitleOn #stat,body.uiTitleOn #stHud,
body.uiTitleOn #uiHpFloat{
  opacity:.06;
  /* ★들어올 때는 **빠르게** 물린다(판정 S4). 예전 값 .5s 는 창이 진해지는 구간과
     그대로 겹쳐서, R 재시작에 창도 0.2·계기판도 0.8 인 프레임이 24장 나왔다.
     나가는 쪽은 아래 평상 규칙의 느린 전환 + JS 의 TITLE_OUT 지연이 맡는다. */
  transition:opacity .16s ease}
body.uiBossIn #help,body.uiBossIn #uiHelpChip,
body.uiCine #help,body.uiCine #uiHelpChip,body.uiCine #uiDock,
body.uiCine #bHud,body.uiCine #stat,body.uiCine #stHud,body.uiCine #uiHpFloat,
body.uiCleared #help,body.uiCleared #uiHelpChip,body.uiCleared #uiDock,
body.uiCleared #stat,body.uiCleared #stHud,
body.uiCleared #uiHpFloat{opacity:0;transition:opacity .22s ease}
/* 인라인 opacity 를 쓰는 둘(나침반·마커)만 !important. 인라인은 클래스 규칙을 이긴다 */
body.uiTitleOn #uiNav,body.uiTitleOn #uiPip{opacity:.06!important}
body.uiBossIn #uiNav,body.uiBossIn #uiPip,
body.uiCine #uiNav,body.uiCine #uiPip,
body.uiCleared #uiNav,body.uiCleared #uiPip{opacity:0!important}
/* 도움말 판은 접힘 애니(translateX)를 같이 쓴다. 연출 중에는 자리를 안 옮기고
   투명도만 쓴다 - 옆으로 미끄러지면 연출 위에 움직이는 물건이 하나 더 생긴다 */
body.uiBossIn #help,body.uiCine #help,body.uiCleared #help{transform:none}
/* ★#stHud 의 **평상 전환**은 건드리지 않는다. stealth.js 가 .16s 로 잡아 뒀고 그건
   「방금 숨었다 / 방금 들켰다」를 알리는 값이라, 여기서 느리게 덮으면 알림이 늦는다. */
`;

// ---------------------------------------------------------------------------
let started = false;

// ---------------------------------------------------------------------------
// 로딩 진행 창구 (인터페이스 계약)
// ---------------------------------------------------------------------------
// main.js 는 로드 중 아무 때나 window.__loadProgress(0~1) 을 부르면 된다.
// ★진짜 구현은 index.html 의 인라인 스크립트에 있다. 이 파일은 main.js **맨 끝**에서
//   불려서 로딩이 이미 끝난 뒤에야 존재하기 때문에, 여기에만 두면 로딩 중에는
//   함수 자체가 없다. 그래서 index.html 이 먼저 깔고 여기서는 **없을 때만** 채운다.
if (typeof window.__loadProgress !== 'function') {
  window.__loadProgress = function () {};
}

export function initUI() {
  if (started) return window.__ui;
  started = true;

  // ★style 을 **맨 마지막에** 붙인다. enemy.js·boss.js·stealth.js 가 이미 넣어 둔
  //   규칙과 선택자 특이도가 같으므로, 나중에 붙은 쪽이 이긴다(!important 를 안 써도 된다).
  const style = document.createElement('style');
  style.id = 'uiStyle';
  style.textContent = CSS;
  document.head.appendChild(style);

  // ── DOM ──
  // ★모든 창이 같은 뼈대다: .win > (.hd > b) + .bd. 뼈대가 같아야 CSS 한 벌로 묶인다.
  // ★뼈대: .win > i.fr(떨어진 네온 프레임) + .hd([!] 박스 + 낱말 박스) + .bd(본문).
  //   세 창이 같은 뼈대라야 CSS 한 벌로 묶인다.
  const HEAD = (w) => '<div class="hd"><i class="ic">!</i><b>' + w + '</b></div>';
  const bg = el('div', 'uiTitleBg');
  const title = el('div', 'uiTitle');
  title.innerHTML =
    '<div class="win"><i class="fr"></i>' + HEAD('') + '<div class="bd">'
    + '<div class="big"></div><div class="sub"></div>'
    + '<div class="rule"></div><div class="lore"></div></div></div>';
  title.querySelector('.hd b').textContent = FLOOR.head;
  title.querySelector('.big').textContent = FLOOR.no;
  title.querySelector('.sub').textContent = FLOOR.name;
  title.querySelector('.lore').textContent = FLOOR.lore;

  const banner = el('div', 'uiBanner');
  banner.innerHTML =
    '<div class="win"><i class="fr"></i>' + HEAD('') + '<div class="bd">'
    + '<div class="tag"></div><div class="name"></div></div></div>';
  banner.querySelector('.hd b').textContent = BOSS_CARD.head;
  banner.querySelector('.tag').textContent = BOSS_CARD.tag;
  banner.querySelector('.name').textContent = BOSS_CARD.name;

  const death = el('div', 'uiDeath');
  death.innerHTML =
    '<div class="win"><i class="fr"></i>' + HEAD('') + '<div class="bd">'
    + '<div class="glyph"></div><div class="rule"></div><div class="cnt"></div></div></div>';
  death.querySelector('.hd b').textContent = DEATH.head;
  death.querySelector('.glyph').textContent = DEATH.glyph;
  const deathCnt = death.querySelector('.cnt');

  const chip = el('div', 'uiHelpChip');
  chip.textContent = '?';
  chip.title = 'H 키로 조작 안내';
  chip.addEventListener('click', () => toggleHelp());

  // 클리어 암막
  const dim = el('div', 'uiClearDim');

  // 스킬 칩 두 장. 이름은 index.html 조작 안내와 같은 말을 쓴다.
  const skills = el('div', 'uiSkills');
  skills.innerHTML =
    '<div class="sk" data-k="Heavy"><i class="cd"></i><span class="key">X</span><span class="nm">수면참</span></div>' +
    '<div class="sk" data-k="Wide"><i class="cd"></i><span class="key">C</span><span class="nm">횡일섬</span></div>';
  const skHeavy = skills.querySelector('[data-k="Heavy"]');
  const skWide = skills.querySelector('[data-k="Wide"]');

  // 목표 방향 나침반. 판(글자)은 안 돌고 화살만 판 둘레를 돈다
  const nav = el('div', 'uiNav');
  nav.innerHTML = '<div class="dial"><i class="tip"></i></div><div class="plate"></div>'
    + '<div class="cap"></div>';
  const navDial = nav.querySelector('.dial');
  const navPlate = nav.querySelector('.plate');
  const navCap = nav.querySelector('.cap');

  // 가까운 요괴 무리 마커
  const pip = el('div', 'uiPip');
  pip.innerHTML = '<div class="cap"></div>';
  const pipCap = pip.querySelector('.cap');
  pipCap.textContent = PIP_HINT;

  document.body.append(bg, title, banner, death, chip, dim, nav, pip);

  // -------------------------------------------------------------------------
  // 계기판 도킹 (v93 판정 S4)
  // -------------------------------------------------------------------------
  // ★남의 파일이 만든 조각을 **옮겨 담기만** 한다. enemy.js·main.js 는 전부
  //   getElementById 로 잡고 있어서 부모가 바뀌어도 참조가 안 끊긴다.
  //   (없으면 그 셀만 조용히 빠지고 나머지는 그대로 선다)
  const dock = el('div', 'uiDock');
  const swordEl = document.getElementById('sword');
  const swordCell = cell('칼', swordEl);
  for (const c of [cell('체력', document.getElementById('eHud')),
                   cell('', skills), swordCell]) {
    if (c) dock.append(c);
  }
  document.body.append(dock);

  // 체력 숫자. 트랙(#eBar) 바로 오른쪽에 세운다.
  // ★enemy.js 는 #eBar·#eFill 만 만진다. 그 뒤에 형제를 하나 더 넣어도 안 부딪힌다.
  const hpNum = el('b', 'uiHpNum');
  const barEl = document.getElementById('eBar');
  if (barEl && barEl.parentNode) barEl.parentNode.insertBefore(hpNum, barEl.nextSibling);

  // 머리 위 체력바(12차). 잔상(.gh)이 채움(.fl) **뒤**에 깔린다 - 문서 순서가 곧 층이다.
  const hpFloat = el('div', 'uiHpFloat');
  hpFloat.innerHTML = '<i class="gh"></i><i class="fl"></i>';
  const hpGhost = hpFloat.querySelector('.gh');
  const hpFill = hpFloat.querySelector('.fl');
  document.body.append(hpFloat);

  function cell(label, node) {
    if (!node) return null;                        // 담을 게 없으면 셀도 없다
    const c = document.createElement('div');
    c.className = 'cell';
    if (label) {
      const l = document.createElement('span');
      l.className = 'lb';
      l.textContent = label;
      c.appendChild(l);
    }
    c.appendChild(node);
    return c;
  }

  // -------------------------------------------------------------------------
  // 1) 입장 알림창
  // -------------------------------------------------------------------------
  // ★"첫 등장 한 번" 짜리 작은 라벨(나침반 라벨·요괴 마커)은 **입장 창이 걷힌 뒤**에만
  //   센다. 이 파일은 main.js 맨 끝에서 붙는데 그 시점에 캐릭터 GLB 는 아직 내려오는
  //   중이라, 로딩 화면이 떠 있는 동안 폴링이 먼저 돌아 버린다. 그러면 딱 한 번뿐인
  //   라벨을 **아무도 못 본 채 소모한다**(실측: 로딩이 길면 100% 소모되는 경주였다).
  //   창이 걷히는 순간이 곧 플레이어가 화면을 보기 시작하는 순간이다.
  let awake = false;

  let titleTimer = 0;
  function showTitle(short) {
    clearTimeout(titleTimer);
    // 애니를 다시 틀려면 클래스를 뺐다가 **레이아웃을 한 번 강제로 계산한 뒤** 붙여야 한다.
    // 같은 프레임에 뺐다 붙이면 브라우저가 변화를 못 보고 그냥 넘어간다.
    title.classList.remove('run', 'on', 'out');
    void title.offsetWidth;
    title.style.setProperty('--sp', short ? '0.38' : '1');
    title.classList.add('run', 'on');
    bg.classList.add('on');
    document.body.classList.add('uiTitleOn');    // HUD 를 물린다
    titleTimer = setTimeout(() => {
      title.classList.add('out');
      bg.classList.remove('on');
      awake = true;                                // 이제부터가 플레이어의 시간이다
      // ── 창이 걷힌 **뒤에** 계기판을 들인다 (판정 S4) ──
      // ★예전에는 이 줄이 바로 위 .out 과 같은 줄에 있었다. 그러면 창 사라짐(.55s)과
      //   계기판 돌아옴(.5s)이 **같은 순간에 같이 시작**한다. 실측하면 그 사이 300ms
      //   가까이 창도 반투명, 계기판도 반투명이라 화면에 주인이 없었다.
      // ★TITLE_OUT(470ms)은 창 전환 .55s 의 85% 지점이다. 그때 창은 이미 불투명도
      //   0.1 밑이라 눈에 남는 겹침이 없다. 완전히 0 이 될 때까지 기다리면
      //   이번엔 화면이 한 박자 비어 버린다 - 그 사이가 이 값이다.
      titleTimer = setTimeout(() => {
        document.body.classList.remove('uiTitleOn');
        // 전환이 끝난 뒤에 애니 클래스를 빼야 마지막 프레임이 안 튄다
        titleTimer = setTimeout(() => title.classList.remove('run', 'on', 'out'),
                                TITLE_CLEAN - TITLE_OUT);
      }, TITLE_OUT);
    }, short ? REPLAY_HOLD : ENTER_HOLD);
  }

  // 첫 창은 **로딩이 끝난 뒤**에 뜬다. main.js 가 #load 를 display:none 으로 감추는
  // 그 순간이 곧 "초원에 섰다"는 순간이라, 그걸 보고 있으면 훅이 하나도 안 든다.
  let firstDone = false;
  const loadEl = document.getElementById('load');
  function waitSpawn() {
    if (firstDone) return;
    if (!loadEl || getComputedStyle(loadEl).display === 'none') {
      firstDone = true;
      showTitle(false);
      return;
    }
    setTimeout(waitSpawn, 100);
  }
  waitSpawn();

  // -------------------------------------------------------------------------
  // 2) 보스 조우 경고창
  // -------------------------------------------------------------------------
  let bannerTimer = 0;
  let bannerDone = false;
  function showBanner() {
    bannerDone = true;
    clearTimeout(bannerTimer);
    banner.classList.remove('on');
    void banner.offsetWidth;
    banner.classList.add('on');
    document.body.classList.add('uiBossIn');     // 보스 HUD 를 잠깐 눌러 둔다
    bannerTimer = setTimeout(() => {
      banner.classList.remove('on');               // .45s 에 걸쳐 사라진다
      // ★배너가 **다 빠진 뒤에** 체력바를 들인다. 같이 시작하면 둘이 반투명하게 겹친다.
      bannerTimer = setTimeout(() => {
        document.body.classList.remove('uiBossIn');
      }, BANNER_FADE);
    }, BANNER_HOLD);
  }

  // -------------------------------------------------------------------------
  // 2-b) 연출이 화면을 소유하는 창 (판정 S6)
  // -------------------------------------------------------------------------
  // 보스가 쓰러지는 그 순간부터 CINE_KILL 동안 계기판·도움말·목표 알약·나침반을
  // 물린다. 컷(집중선·슬로모·증표 낙하)이 끝나면 저절로 돌아온다.
  // ★신호는 boss.state 하나만 본다. 이 파일은 게임 상태를 한 줄도 안 만들고,
  //   컷을 그리는 쪽(feel.js·main.js)에 손을 뻗지도 않는다.
  // ★'사망'은 한 번 되면 R 을 누를 때까지 계속 '사망'이다. 그래서 **엣지**만 잡는다.
  let cineTimer = 0;
  let bossDeadSeen = false;
  function startCine(ms) {
    clearTimeout(cineTimer);
    document.body.classList.add('uiCine');
    cineTimer = setTimeout(() => document.body.classList.remove('uiCine'), ms);
  }
  function endCine() {
    clearTimeout(cineTimer);
    document.body.classList.remove('uiCine');
  }

  // -------------------------------------------------------------------------
  // 3) 사망
  // -------------------------------------------------------------------------
  let deadAt = -1;
  let wasDead = false;
  // ★v72 QA: "죽었는데 사망 화면을 못 봤다."
  //   원인은 이 창이 **레벨 신호**(지금 죽어 있나)를 20Hz 로 훔쳐보는 구조였던 것이다.
  //   enemy.dead 가 true 인 창은 게임시간 1.6초뿐인데, 그 1.6초는 히트스톱·__slow·
  //   프레임 스로틀에 따라 벽시계로는 얼마든지 짧아질 수 있다.
  //   그래서 enemy.js 가 **엣지**(죽은 시각)를 window.__playerDied 에 못박고,
  //   여기서는 그 시각이 바뀌었는지만 본다. 한 번 잡으면 최소 DEATH_MIN 은 띄운다.
  let lastDiedStamp = 0;
  let deathHold = 0;                 // 이 시각까지는 리스폰해도 창을 안 내린다
  const DEATH_MIN = 2000;
  function showDeath() {
    deadAt = performance.now();
    deathHold = deadAt + DEATH_MIN;
    death.classList.add('on');
    document.body.classList.add('uiDeathOn');
  }
  function hideDeath() {
    death.classList.remove('on');
    document.body.classList.remove('uiDeathOn');
  }

  // -------------------------------------------------------------------------
  // 4) 조작 안내 접기 / 펼치기
  // ★H 는 비어 있는 키다(main.js·enemy.js·boss.js·stealth.js 어디에도 KeyH 가 없다).
  //   preventDefault 도 안 한다. 이 리스너는 게임 입력을 하나도 안 먹는다.
  // -------------------------------------------------------------------------
  let helpOff = false;
  let helpTimer = 0;
  let helpTouched = false;           // 직접 켜고 끈 적이 있으면 자동으로 안 접는다
  function setHelp(off) {
    helpOff = off;
    document.body.classList.toggle('uiHelpOff', off);
  }
  function toggleHelp() {
    helpTouched = true;
    clearTimeout(helpTimer);
    clearTimeout(helpBootTimer);
    setHelp(!helpOff);
  }
  // 아무 입력이든 한 번 들어오면 그때부터 6초를 잰다(한 번만 건다).
  // ★"이동 입력"으로 좁히면 안 된다. Z 만 눌러 싸우는 사람에게는 타이머가 아예
  //   안 걸려서 안내판이 화면 왼쪽 위를 영원히 먹는다(v84 QA S10 실측).
  function armHelp() {
    if (helpTouched || helpTimer || helpOff) return;
    helpTimer = setTimeout(() => { if (!helpTouched) setHelp(true); }, HELP_IDLE);
  }
  // 아무것도 안 눌러도 8초면 접는다. 첫 화면의 4분의 1을 계속 덮고 있을 이유가 없다.
  let helpBootTimer = setTimeout(() => {
    if (!helpTouched) setHelp(true);
  }, HELP_BOOT);

  addEventListener('keydown', (e) => {
    if (e.repeat) return;
    armHelp();                                   // ★H·R 분기보다 먼저. 아무 키나 입력이다
    if (e.code === 'KeyH') { toggleHelp(); return; }
    // R = 층 재시작. 창을 짧게 한 번 더 틀고 한 판치 상태를 되돌린다.
    if (e.code === 'KeyR') { newRun(); return; }
  });
  // 키보드만 입력이 아니다. 휠 줌·클릭도 "이 사람은 이제 조작 중"이라는 신호다.
  addEventListener('pointerdown', armHelp, { passive: true });
  addEventListener('wheel', armHelp, { passive: true });

  // -------------------------------------------------------------------------
  // 한 판이 새로 시작될 때 되돌릴 것들
  // -------------------------------------------------------------------------
  // ★두 곳에서 부른다. R 키(즉시)와 폴링(boss.time 이 0 으로 되감긴 것을 보고).
  //   R 을 누르면 둘 다 50ms 안에 걸리므로 막지 않으면 창이 시작하자마자 다시 시작한다.
  let newRunAt = -9999;
  function newRun() {
    if (performance.now() - newRunAt < 600) return;
    newRunAt = performance.now();
    bannerDone = false;
    clearTimeout(bannerTimer);
    banner.classList.remove('on');
    document.body.classList.remove('uiBossIn');
    // 연출 창도 같이 되돌린다. 보스 처치 컷 도중에 R 을 누르면 uiCine 이 남아
    // 새 판이 계기판 없이 시작한다(타이머는 R 을 모른다).
    endCine();
    bossDeadSeen = false;
    const clearEl = document.getElementById('bClear');
    if (clearEl) clearEl.classList.remove('uiIn');
    // ★죽어 있는 동안 R 을 눌렀으면 사망 창과 입장 창이 겹친다. 층을 다시 시작하는
    //   순간의 답은 입장 창 쪽이므로 사망 창을 먼저 내린다.
    hideDeath();
    showTitle(true);
  }

  // -------------------------------------------------------------------------
  // 5) 결과창의 처치 수를 HUD 와 맞춘다
  // -------------------------------------------------------------------------
  // ★v72 QA #13: 패널은 "처치 0", HUD 는 "처치 1" 이었다. 둘이 **다른 수를 세고 있다.**
  //   boss.js 는 안 건드리는 파일이므로, 눈에 보이는 두 수를 여기서 하나로 맞춘다
  //   (기준은 플레이어가 판 내내 보고 있던 HUD 값이다).
  function fixClearKills(clearEl) {
    const enemy = window.__enemy;
    if (!enemy) return;
    const want = String(enemy.kills);
    const tds = clearEl.querySelectorAll('td');
    for (let i = 0; i < tds.length; i++) {
      if (tds[i].textContent !== '처치') continue;
      const v = tds[i].nextElementSibling;
      if (v && v.textContent !== want) v.textContent = want;   // 값이 같으면 DOM 을 안 쓴다
      return;
    }
  }

  // -------------------------------------------------------------------------
  // 6) 스킬 칩 (X 수면참 · C 횡일섬)
  // -------------------------------------------------------------------------
  // 쓸 수 있으면 밝게, 휘두르는 중이면 어둡게. 그 클립이 아예 없는 캐릭터에서는 감춘다.
  function updateSkills() {
    const d = window.__dbg;
    const acts = (d && d.actions) || null;
    const busy = !!(d && d.atk);
    if (!busy) noteBusyEnd();
    const left = busy ? busyLeft(d) : 0;
    setSkill(skHeavy, !!(acts && acts.Heavy), busy, left);
    setSkill(skWide, !!(acts && acts.Wide), busy, left);
  }
  function setSkill(node, has, busy, left) {
    node.classList.toggle('gone', !has);
    node.classList.toggle('off', busy);
    node.classList.toggle('rdy', has && !busy);
    // 쿨다운 라디얼. 12시에서 시작해 시계 방향으로 남은 만큼 덮여 있다가 걷힌다.
    // ★색은 시스템창 남색이다(예전 먹색 rgba(4,4,3,..) 은 칩 밖의 판과 안 맞는다).
    const g = node.firstElementChild;              // .cd
    if (!g) return;
    if (!busy) { if (g.style.background) g.style.background = ''; return; }
    const turn = Math.max(0, Math.min(1, left)).toFixed(3);
    g.style.background = 'conic-gradient(from 0deg,rgba(3,10,20,.82) 0turn ' + turn
      + 'turn,rgba(3,10,20,0) ' + turn + 'turn)';
  }
  // 남은 시간 비율(1 = 방금 시작, 0 = 곧 끝).
  // ★main.js 는 attackEnd(게임시계)를 밖에 안 내놓는다. 그래서 **지금 도는 클립의
  //   진행도**를 읽는다. 클립 시간은 재생속도와 무관하게 0..duration 이라 그대로 비율이다.
  //   클립을 못 읽는 몸(궁수 등)에서는 아래 EMA 로 떨어진다.
  let busyT0 = 0, busyEst = 0.62, wasBusy = false;
  function busyLeft(d) {
    const now = performance.now();
    if (!wasBusy) { wasBusy = true; busyT0 = now; }
    const a = d && d.cur;
    if (a && typeof a.time === 'number' && typeof a.getClip === 'function') {
      const clip = a.getClip();
      if (clip && clip.duration > 0) {
        return Math.max(0, Math.min(1, 1 - a.time / clip.duration));
      }
    }
    return Math.max(0, Math.min(1, 1 - (now - busyT0) / 1000 / busyEst));
  }
  // 스윙이 끝난 그 순간에 실제 길이를 배운다(다음 스윙의 어림값이 정확해진다)
  function noteBusyEnd() {
    if (!wasBusy) return;
    wasBusy = false;
    const took = (performance.now() - busyT0) / 1000;
    if (took > 0.15 && took < 2.0) busyEst = busyEst * 0.65 + took * 0.35;
  }

  // -------------------------------------------------------------------------
  // 7) 목표 방향 나침반
  // -------------------------------------------------------------------------
  // 상단 문구가 "무엇"을 말하고(보스를 찾아라 → 증표를 주워라 → 탈출구로),
  // 이 화살표는 "어느 쪽"만 말한다. 목표가 화면에 들어오면 스스로 사라진다.
  // ★화면 좌표는 main.js 의 window.__screen 이 **실제 카메라 행렬**로 내준다.
  //   여기서 각도를 손으로 풀면 줌·창 크기가 바뀔 때마다 어긋난다.
  const NAV_EDGE = 0.90;      // NDC. 광선이 화면 사각형과 만나는 자리
  const NAV_EDGE_PIP = 0.62;  // 요괴 마커는 화살보다 안쪽에
  const PIP_CLEAR = 72;       // px. 화살과 이만큼 안에서 겹치면 마커는 안 찍는다
  const NAV_IN = 0.90;        // 이 안쪽이면 "화면에 보인다"로 치고 숨긴다
  const NAV_R = 64;           // px. 나침반 중심에서 화살 끝까지
  const PLATE_R = 23;         // px. 판 반지름
  const PIP_R = 9;            // px. 무리 마커 소형판 반지름(18px 판)
  // px. 나침반 첫 등장 라벨(.cap)이 판 중심 밑으로 자라는 길이(margin-top 26 + 높이 19).
  const NAV_CAP_H = 34;

  // ★나침반이 커지면서(판 46px + 화살 끝까지 64px) HUD 를 덮기 시작했다. 여백을 상수로
  //   박으면 창 크기·글자 크기가 바뀔 때마다 어긋나므로 **HUD 조각의 실제 사각형을
  //   재서** 못 들어가는 상자를 만든다.
  //   ★HUD 를 피하는 기준은 **판**이다. 화살은 얇은 획이라 위를 스쳐도 글자를
  //     못 읽게 만들지 않는다. 판이 겹치면 그때는 정말 못 읽는다.
  // ★v95 판정 S12: "門 판이 계기판과 근접 충돌한다(우하단)." 원인 두 가지.
  //     (가) 아래 한계를 **가로 전체**에 걸었다. 계기판은 화면 가운데 아래에만 있는데
  //          오른쪽 아래를 가리킬 때도 판을 계기판 윗선까지 밀어 올렸다.
  //          → x 를 먼저 정하고, **그 x 가 계기판 가로 범위 안일 때만** 위로 민다.
  //     (나) 상자를 창 크기로만 캐시했다. 계기판 높이는 **글자가 다시 그려지면 바뀐다.**
  //          → 계기판·목표줄 크기가 바뀌면 상자를 버린다(ResizeObserver).
  let safe = null, safeW = 0, safeH = 0;
  function dropSafe() { safe = null; }
  // 크기가 바뀌는 두 조각만 본다. 자리(top)는 크기에서 따라온다(bottom 고정이라
  // 판이 높아지면 윗선이 그만큼 올라온다).
  if (typeof ResizeObserver === 'function') {
    const ro = new ResizeObserver(dropSafe);
    for (const id of ['uiDock', 'bHud']) {
      const e = document.getElementById(id);
      if (e) ro.observe(e);
    }
  }
  // 서체 도착도 잡아 둔다(ResizeObserver 가 없는 낡은 브라우저의 보험).
  // ★11차에 웹폰트를 은퇴시켰지만 이 줄은 남긴다 - Pretendard 가 로컬에 깔린
  //   기계에서는 여전히 「시스템 고딕 → Pretendard」 로 한 번 다시 그려진다.
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(dropSafe);

  function safeBox() {
    if (safe && safeW === innerWidth && safeH === innerHeight) return safe;
    const rect = (id) => {
      const e = document.getElementById(id);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return r.height > 0 ? r : null;
    };
    const hud = rect('bHud');            // 목표문구 + 보스 체력바
    // ★v93 판정 S5: 탈출 단계에서 門 판이 칼 이름 위로 올라탔다. 그때는 여기서 재는
    //   상자가 **스킬 칩만** 이었다. 이제 셋이 한 판(#uiDock)에 도킹돼 있으므로
    //   판 하나만 재면 아래쪽이 통째로 막힌다.
    const sk = rect('uiDock');
    if (!hud || !sk) return {            // 아직 안 그려졌다. 재지 말고 화면만 안 벗어나게
      navL: NAV_R, navR: innerWidth - NAV_R, navT: NAV_R,
      navB: innerHeight - NAV_R, navBDock: innerHeight - NAV_R,
      pipL: PIP_R, pipR: innerWidth - PIP_R, pipT: PIP_R,
      pipB: innerHeight - PIP_R, pipBDock: innerHeight - PIP_R,
      dockL: -1e4, dockR: -1e4,
    };
    safeW = innerWidth; safeH = innerHeight;
    safe = {
      navL: NAV_R + 4, navR: innerWidth - NAV_R - 4,
      navT: Math.max(NAV_R + 4, hud.bottom + PLATE_R + 6),
      // 계기판 가로 범위 **밖**이면 바닥까지 내려간다
      navB: innerHeight - NAV_R - 4,
      // 계기판 가로 범위 **안**이면 판 윗선 위에서 멈춘다.
      // ★여백 10px. 6px 으로 뒀더니 판과 계기판 사이가 8px 밖에 안 남아
      //   「닿지는 않았는데 붙어 있는」 그림이 됐다(판정 S12 의 근접 충돌).
      navBDock: Math.min(innerHeight - NAV_R - 4, sk.top - PLATE_R - 10),
      pipL: PIP_R + 8, pipR: innerWidth - PIP_R - 8,
      pipT: Math.max(PIP_R + 8, hud.bottom + PIP_R + 6),
      pipB: innerHeight - PIP_R - 8,
      pipBDock: Math.min(innerHeight - PIP_R - 8, sk.top - PIP_R - 8),
      // 계기판 좌우 변. 판 반지름만큼 넓혀 두면 「모서리를 스치는」 자리도 안 생긴다
      dockL: sk.left, dockR: sk.right,
    };
    return safe;
  }
  // 단계별 얼굴. 글자 하나 + 획 색 + 명멸 색.
  // ★색은 화면의 실물과 짝을 맞췄다 - 보스는 어귀 선돌의 붉은 끈, 증표는 호박색 빛기둥.
  //   "저 색을 따라가면 된다"가 설명 없이 붙는다.
  // ★11차: 뜻(붉음=보스, 호박=증표, 중성=탈출구)은 그대로 두고 획 색만 시스템창의
  //   청백 쪽으로 끌어왔다. 남색 판 위에서 크림색 획은 누렇게 뜬다(실측).
  const NAV_KIND = {
    boss:  { glyph: '鬼', ink: '#ffd9d0', glow: 'rgba(255,90,64,.60)' },
    token: { glyph: '符', ink: '#ffe3ad', glow: 'rgba(255,200,90,.55)' },
    exit:  { glyph: '門', ink: '#d9edff', glow: 'rgba(143,211,241,.55)' },
  };
  // 목표. ★boss.guide 가 정본이다(상단 문구와 **같은 값**을 본다). 낡은 boss.js 로
  //   돌아가도 화살은 살아 있어야 하므로 옛 경로를 폴백으로 남긴다.
  function navTarget(boss) {
    if (boss.guide !== undefined) return boss.guide;
    const ph = boss.phase;
    if (ph === '돌파') return null;
    if (ph === '증표줍기') {
      const t = boss.token;
      return (t && t.state === '바닥') ? { x: t.x, z: t.z, kind: 'token' } : null;
    }
    if (ph === '탈출') {
      const e = nearestExit(boss);
      return e ? { x: e.x, z: e.z, kind: 'exit' } : null;
    }
    return boss.pos ? { x: boss.pos.x, z: boss.pos.z, kind: 'boss' } : null;
  }
  function nearestExit(boss) {
    const list = boss.exits;
    if (!list || !list.length) return null;
    const p = window.__pos ? window.__pos() : null;
    if (!p) return list[0];
    let best = null, bd = Infinity;
    for (const e of list) {
      const dx = e.x - p.x, dz = e.z - p.z;
      const d = dx * dx + dz * dz;
      if (d < bd) { bd = d; best = e; }
    }
    return best;
  }

  // 월드 한 점을 화면 가장자리 자리(%)와 각도(도)로 바꾼다. 화살과 마커가 같이 쓴다.
  // 화면 안에 있으면 null 을 낸다(가리킬 이유가 없다).
  function edgeSpot(scr, x, z, edge) {
    const p = scr(x, z);
    // 등 뒤에 있으면 투영이 좌우·상하로 뒤집혀 나온다. 부호만 되돌린다.
    const nx = p.behind ? -p.x : p.x;
    const ny = p.behind ? -p.y : p.y;
    if (!p.behind && Math.abs(nx) <= NAV_IN && Math.abs(ny) <= NAV_IN) return null;
    // 중심에서 그 방향으로 쏜 광선이 화면 사각형과 만나는 자리
    const m = Math.max(Math.abs(nx), Math.abs(ny)) || 1;
    const ex = nx / m * edge, ey = ny / m * edge;
    return {
      px: (ex + 1) * 0.5 * innerWidth,
      py: (1 - ey) * 0.5 * innerHeight,
      // 회전은 **픽셀** 기준이라야 맞다. NDC 는 가로세로 축척이 달라서 각이 눕는다.
      ang: Math.atan2(-ey * innerHeight, ex * innerWidth) * 180 / Math.PI,
    };
  }
  // 자리를 안전 상자 안으로 민다.
  // ★각도는 안 건드린다. 자리만 몇십 px 물러나므로 **가리키는 방향은 그대로**다.
  // ★순서가 중요하다(판정 S12). **x 를 먼저 정하고 그 다음에 아래 한계를 고른다.**
  //   half = 판 반지름. 판의 가장자리 기준으로 겹침을 따진다.
  function place(node, spot, l, r, t, bFree, bDock, dockL, dockR, half) {
    const x = Math.min(Math.max(spot.px, l), Math.max(l, r));
    const overDock = (x + half) > dockL && (x - half) < dockR;
    const b = overDock ? bDock : bFree;
    const y = Math.min(Math.max(spot.py, t), Math.max(t, b));
    node.style.left = (x / innerWidth * 100).toFixed(2) + '%';
    node.style.top = (y / innerHeight * 100).toFixed(2) + '%';
    return { px: x, py: y };
  }

  let navGlyph = '';          // 지금 새겨 둔 글자. 안 바뀌면 DOM 을 안 건드린다
  let navPx = null;           // 화살이 지금 있는 화면 좌표(px). 마커가 겹치는지 볼 때 쓴다
  // 단계가 처음 뜰 때만 판 밑에 작은 말을 2.6초 붙인다(첫 등장 1회)
  const navCapSeen = {};
  let navCapTimer = 0;
  function showNavCap(kind) {
    const txt = NAV_HINT[kind];
    // ★!awake 일 때는 seen 을 찍지 않고 그냥 돌아간다. 그래야 창이 걷힌 뒤
    //   다음 폴링에서 다시 시도한다(한 번뿐인 라벨을 로딩 중에 태우지 않는다).
    if (!txt || navCapSeen[kind] || !awake) return;
    navCapSeen[kind] = true;
    navCap.textContent = txt;
    navCap.classList.add('on');
    clearTimeout(navCapTimer);
    navCapTimer = setTimeout(() => navCap.classList.remove('on'), 2600);
  }
  function updateNav(boss, cleared) {
    const scr = window.__screen;
    // 판이 끝났거나 쓰러져 있으면 갈 곳을 가리킬 이유가 없다.
    const off = cleared || death.classList.contains('on');
    const t = (!off && scr) ? navTarget(boss) : null;
    if (!t) { nav.style.opacity = '0'; navPx = null; return; }
    const spot = edgeSpot(scr, t.x, t.z, NAV_EDGE);
    if (!spot) { nav.style.opacity = '0'; navPx = null; return; }   // 화면 안에 있다
    const k = NAV_KIND[t.kind] || NAV_KIND.boss;
    if (navGlyph !== k.glyph) {
      navGlyph = k.glyph;
      navPlate.textContent = k.glyph;
      nav.style.setProperty('--nav-ink', k.ink);
      nav.style.setProperty('--nav-glow', k.glow);
    }
    // ★글자가 바뀌는 그 틱에만 부르면 안 된다. 그 틱이 로딩 중이었으면 영영 못 뜬다.
    //   매 틱 불러도 안쪽에서 seen 으로 한 번만 통과한다.
    showNavCap(t.kind);
    const s = safeBox();
    // ★첫 등장 라벨이 붙어 있는 동안은 판 밑으로 34px 이 더 자란다. 그 창에서만
    //   아래 한계를 더 올린다 - 평상시에도 올려 두면 「가리키는 자리」가 어긋난다.
    const capH = navCap.classList.contains('on') ? NAV_CAP_H : 0;
    navPx = place(nav, spot, s.navL, s.navR, s.navT, s.navB, s.navBDock - capH,
                  s.dockL, s.dockR, PLATE_R + 8);
    navDial.style.transform = 'rotate(' + spot.ang.toFixed(1) + 'deg)';
    nav.style.opacity = '1';
  }

  // -------------------------------------------------------------------------
  // 8) 가까운 요괴 무리 마커
  // -------------------------------------------------------------------------
  // 15m 안 최근접 무리 방향에 점 하나. "저기 뭔가 있다"만 말하고 그 이상은 안 한다.
  // ★enemy.js 의 field 는 **읽기만** 한다(무리의 집 좌표 at 와 생존 수).
  const PIP_RANGE = 15;       // m
  function updatePip(cleared) {
    const scr = window.__screen;
    const en = window.__enemy;
    const p = window.__pos ? window.__pos() : null;
    const off = cleared || death.classList.contains('on');
    if (off || !scr || !en || !p) { pip.style.opacity = '0'; return; }
    let bx = 0, bz = 0, bd = PIP_RANGE * PIP_RANGE, found = false;
    const list = en.field || [];
    for (const g of list) {
      if (!g.alive || !g.at) continue;
      const dx = g.at[0] - p.x, dz = g.at[1] - p.z;
      const d = dx * dx + dz * dz;
      if (d < bd) { bd = d; bx = g.at[0]; bz = g.at[1]; found = true; }
    }
    if (!found) { pip.style.opacity = '0'; return; }
    const spot = edgeSpot(scr, bx, bz, NAV_EDGE_PIP);
    if (!spot) { pip.style.opacity = '0'; return; }   // 눈에 보인다. 점을 찍을 이유가 없다
    const s = safeBox();
    const at = place(pip, spot, s.pipL, s.pipR, s.pipT, s.pipB, s.pipBDock,
                     s.dockL, s.dockR, PIP_R + 6);
    // ★화살 바로 옆에 붙으면 "화살에 딸린 무엇"으로 읽힌다. 겹치면 점을 접는다.
    if (navPx && Math.hypot(navPx.px - at.px, navPx.py - at.py) < PIP_CLEAR) {
      pip.style.opacity = '0'; return;
    }
    pip.style.opacity = '1';
    showPipCap();
  }
  // 점이 처음 화면에 뜬 그 한 번만 라벨을 단다(판정 S11).
  let pipCapSeen = false;
  function showPipCap() {
    if (pipCapSeen || !awake) return;             // 위 showNavCap 과 같은 이유
    pipCapSeen = true;
    pipCap.classList.add('on');
    setTimeout(() => pipCap.classList.remove('on'), 2600);
  }

  // -------------------------------------------------------------------------
  // 9) ?dev 캐릭터 라벨 중복 (개발용 화면에서만)
  // -------------------------------------------------------------------------
  // kensa 와 slayer 가 둘 다 '검사'로 떠서 F 로 돌려도 뭐가 뭔지 안 갈렸다.
  // 라벨 표는 main.js(다른 사람 파일)에 있으므로 손대지 않고, ?dev 화면의 글자만 고친다.
  const DEV = location.search.includes('dev');
  const SLAYER_HEAD = '검사 (slayer)';       // main.js 가 쓰는 원본. 이 머리만 갈아 끼운다
  const SLAYER_LABEL = '검사(토이)';         // ★오너가 바꿀 곳
  const devLabelEls = ['stat', 'cpT'];
  const devSeen = {};
  function fixDevLabel() {
    if (!DEV) return;
    for (const id of devLabelEls) {
      const e = document.getElementById(id);
      if (!e) continue;                      // 미리보기 패널은 P 를 눌러야 생긴다
      const t = e.textContent;
      if (t === devSeen[id]) continue;       // 안 바뀌었으면 아무것도 안 한다
      if (t.indexOf(SLAYER_HEAD) === 0) {
        e.textContent = SLAYER_LABEL + t.slice('검사'.length);
        devSeen[id] = e.textContent;
      } else {
        devSeen[id] = t;
      }
    }
  }

  // -------------------------------------------------------------------------
  // 10) 계기판 수치 (v93 판정 S4)
  // -------------------------------------------------------------------------
  // 체력 숫자. ★enemy.js 는 최대 체력을 안 내놓는다. 첫 폴링이 만체력이라
  //   지금까지 본 가장 큰 값을 최대로 잡으면 어떤 빌드에서도 맞는다(기본 100).
  let hpMax = 100, hpSeen = -1;
  function updateHp() {
    const en = window.__enemy;
    if (!en || typeof en.hp !== 'number') return;
    if (en.hp > hpMax) hpMax = Math.ceil(en.hp);
    const v = Math.max(0, Math.round(en.hp));
    if (v === hpSeen) return;                      // 안 바뀌었으면 DOM 을 안 쓴다
    hpSeen = v;
    hpNum.innerHTML = v + '<s>/</s><u>' + hpMax + '</u>';
    hpNum.classList.toggle('low', v <= hpMax * 0.25);
  }

  // 칼 이름. ★'2. 백아' 의 2 는 내부 목록 순서다(판정 S4). 눈에 보일 이유가 없다.
  //   main.js 가 장착할 때마다 다시 쓰므로 여기서 매번 앞머리를 떼어 준다.
  let swordSeen = '';
  function fixSword() {
    if (!swordEl) return;
    const gone = swordEl.style.display === 'none';   // 칼이 없는 몸(궁수 등)
    if (swordCell.style.display !== (gone ? 'none' : '')) {
      swordCell.style.display = gone ? 'none' : '';
    }
    if (gone) return;
    const t = swordEl.textContent;
    if (t === swordSeen) return;
    const m = /^\s*\d+\.\s*/.exec(t);
    swordEl.textContent = m ? t.slice(m[0].length) : t;
    swordSeen = swordEl.textContent;
  }

  // 소리 줄. main.js 는 상태('소리 켜짐')로 쓰는데 다른 줄은 전부 동작('접기 / 펼치기')
  // 이라 혼자 말투가 다르다(판정 S8). 지금 상태는 남기되 동작형으로 되돌린다.
  const muteEl = document.getElementById('mute');
  function fixMute() {
    if (!muteEl) return;
    const t = muteEl.textContent;
    const off = t.indexOf('꺼짐') >= 0;
    if (!off && t.indexOf('켜짐') < 0) return;     // 이미 갈아 끼운 뒤다
    muteEl.innerHTML = '<span class="ks"><span class="k">M</span></span>'
      + '<span class="t">소리 ' + (off ? '켜기' : '끄기') + '</span>';
  }

  // -------------------------------------------------------------------------
  // 10-b) 기술 이름 콜아웃을 시스템 팝으로 (판정 S14)
  // -------------------------------------------------------------------------
  // main.js 가 #combo 에 기술 이름을 쓰는 그 순간 여기서 창으로 갈아 끼운다.
  // ★폴링(20Hz)이 아니라 MutationObserver 를 쓴다. 수명이 0.9초뿐인 물건이라
  //   50ms 를 기다리면 **맨 글자로 떴다가 창으로 바뀌는** 게 눈에 보인다.
  //   관찰자 콜백은 쓰기가 끝난 직후 마이크로태스크에서 도므로 같은 프레임에 잡는다.
  // ★내 쓰기가 다시 나를 부르는 되먹임을 막아야 한다. **플래그로 끊으면 안 된다.**
  //   창을 씌우고 나면 #combo 의 textContent 가 「스킬수면참물의 一」이 되는데, 그것도
  //   표 검사(앞머리 일치)를 통과할 수 있다. 그래서 콜백이 한 번만 어긋나면
  //   같은 창을 영원히 다시 씌우는 무한 루프가 된다.
  //   **내가 마지막으로 써 넣은 innerHTML 을 그대로 기억해 두고 비교한다.** 서명이
  //   같으면 그건 내 글씨이므로 아무것도 안 한다 - 어떤 순서로 배달돼도 안 돈다.
  // ★평타 「1타」·「3타」 는 안 건드린다. 표에 있는 이름으로 시작할 때만 씌운다.
  const comboEl = document.getElementById('combo');
  let comboSig = '';
  function skillOf(t) {
    for (const k in SKILL_TYPE) if (t.indexOf(k) === 0) return k;
    return null;
  }
  function dressCombo() {
    if (!comboEl || comboEl.innerHTML === comboSig) return;
    const nm = skillOf(comboEl.textContent.trim());
    if (!nm) return;
    // main.js 가 붙인 누적 명중(<i>명중 5</i>)은 살려서 창 옆에 그대로 둔다.
    const old = comboEl.querySelector('i');
    const hits = old ? old.textContent : '';
    comboEl.innerHTML = '<span class="uiCall"><b class="hd"></b>'
      + '<b class="nm"></b><b class="ty"></b></span>' + (hits ? '<i></i>' : '');
    comboEl.querySelector('.hd').textContent = SKILL_HEAD;
    comboEl.querySelector('.nm').textContent = nm;
    comboEl.querySelector('.ty').textContent = SKILL_TYPE[nm];
    if (hits) comboEl.querySelector('.uiCall + i').textContent = hits;
    comboSig = comboEl.innerHTML;
  }
  if (comboEl) {
    new MutationObserver(dressCombo)
      .observe(comboEl, { childList: true, characterData: true, subtree: true });
  }

  // boss.js 문구 갈아 끼우기. ★원본 파일은 한 줄도 안 건드리고 **화면에 나온
  //   글자만** 바꾼다(fixClearKills 와 같은 수법). 값이 같으면 DOM 을 안 쓴다.
  function patchText(node) {
    if (!node) return;
    const h = node.innerHTML;
    let out = h;
    for (let i = 0; i < TEXT_PATCH.length; i++) {
      out = out.split(TEXT_PATCH[i][0]).join(TEXT_PATCH[i][1]);
    }
    if (out !== h) node.innerHTML = out;
  }

  // -------------------------------------------------------------------------
  // 10-c) 머리 위 체력바 (12차. 오너 지시: 「체력바는 캐릭터 머리 위로, 롤처럼」)
  // -------------------------------------------------------------------------
  // 롤 문법: 캐릭터 머리 위 0.4m 에 화면 px 고정폭 트랙 하나. 하단 계기판은 그대로 둔다.
  //
  // ★★이것만은 폴링(20Hz)에 못 얹는다. 20Hz 로 붙이면 대시 한 번에 바가 캐릭터
  //   뒤로 서너 뼘씩 끌려간다(캐릭터는 60fps 로 그려지니까). 그래서 이 한 가지만
  //   rAF 로 돈다. 하는 일은 곱셈 몇 번 + transform 한 줄이라 프레임 예산은 안 먹는다.
  //
  // ★투영은 손으로 안 푼다. main.js 의 window.__screen(x, z, y) 이 **이번 프레임의
  //   실제 카메라 행렬**(matrixWorldInverse · projectionMatrix)로 NDC 를 내준다.
  //   목표 방향 나침반이 이미 쓰는 그 창구다. 삼각함수로 어림하면 휠 줌·창 비율이
  //   바뀔 때마다 어긋난다.
  // ★★window.__fx 는 **?dev 에서만** 존재한다(main.js 3541행 `if (DEV)`). 평시 URL 에는
  //   __fx 도 __fx.charH() 도 없다. 키는 window.__dbg 에서 꺼낸다 - __dbg 는
  //   activateChar 가 캐릭터를 세울 때마다 무조건 다시 쓰므로 F 로 몸을 바꿔도 따라온다.
  const HP_UP = 0.4;             // 머리 꼭대기에서 바까지(m)
  const HP_FADE = 1.15;          // 잔상이 따라 줄어드는 속도(1초에 체력바 몇 배)
  const HP_HOLD = 0.14;          // 맞고 나서 잔상이 버티는 시간(초)
  const HP_FLASH = 180;          // 맞은 순간 밝아지는 시간(ms)
  // ★색은 enemy.js 의 규칙을 그대로 옮긴 것이다. 뜻이 걸린 색이라 여기서 안 바꾼다.
  const HP_INK = ['linear-gradient(90deg,#e04a2e,#f08f7f)',    // 25% 이하
                  'linear-gradient(90deg,#e0c22e,#f0e07f)',    // 50% 이하
                  'linear-gradient(90deg,#2ee08a,#7ff0c0)'];   // 그 위

  let fltModel = null, fltH = 0;                 // 지금 몸 · 그 키(m)
  function playerH() {
    const d = window.__dbg;
    if (!d || !d.model || !d.CHARS) return 0;    // 캐릭터 glb 가 아직 안 내려왔다
    if (d.model !== fltModel) {                  // 몸이 바뀌었을 때만 표를 훑는다
      fltModel = d.model;
      fltH = 0;
      for (const k in d.CHARS) if (d.CHARS[k].model === d.model) fltH = d.CHARS[k].charH || 0;
    }
    return fltH;
  }

  // 바 자체의 픽셀 크기. 창 크기가 바뀔 때만 다시 잰다(매 프레임 재면 레이아웃이 돈다).
  let fltW = 0, fltHt = 0;
  function measureFloat() { fltW = hpFloat.offsetWidth; fltHt = hpFloat.offsetHeight; }
  measureFloat();
  addEventListener('resize', measureFloat);

  let fltX = -9999, fltY = -9999, fltOn = false;
  let fltR = -1, fltBand = -1;        // 지금 그려 둔 채움 비율 · 색 단계
  let ghostR = 0, ghostHold = 0;      // 잔상 비율 · 버티는 시간(초)
  let fltT = 0, hitTimer = 0;

  function fltShow(on) {
    if (on === fltOn) return;
    fltOn = on;
    hpFloat.classList.toggle('on', on);
  }

  function updateHpFloat(now) {
    const scr = window.__screen, root = window.__root, en = window.__enemy;
    const dt = fltT ? Math.min(0.1, (now - fltT) / 1000) : 0;
    fltT = now;
    const h = playerH();
    if (!scr || !root || !en || !h) { fltShow(false); return; }

    // ── 자리 ──
    // root.position 을 **그대로** 읽는다. window.__pos() 는 소수 둘째 자리에서 자르는데
    // 1cm 가 화면에서 0.5px 이라 그 반올림이 그대로 바 떨림으로 보인다.
    const p = root.position;
    const s = scr(p.x, p.z, p.y + h + HP_UP);
    if (s.behind) { fltShow(false); return; }     // 카메라 뒤(고정 쿼터뷰에선 사실상 없다)
    // ★정수로 못박는다. 반 픽셀에 서면 1px 헤어라인이 두 줄 회색으로 번져서
    //   가만히 서 있어도 바가 지글거린다.
    const x = Math.round((s.x + 1) * 0.5 * innerWidth - fltW / 2);
    const y = Math.round((1 - s.y) * 0.5 * innerHeight - fltHt / 2);
    if (x !== fltX || y !== fltY) {
      fltX = x; fltY = y;
      hpFloat.style.transform = 'translate3d(' + x + 'px,' + y + 'px,0)';
    }
    fltShow(true);

    // ── 채움 ──
    // 최대 체력은 계기판과 같은 값을 쓴다(enemy.js 가 최대를 안 내놓는다. 10) 절 참조).
    if (en.hp > hpMax) hpMax = Math.ceil(en.hp);
    const r = Math.max(0, Math.min(1, en.hp / hpMax));
    if (r !== fltR) {
      if (r < fltR) {                             // 맞았다
        ghostHold = HP_HOLD;
        hpFloat.classList.add('hit');
        clearTimeout(hitTimer);
        hitTimer = setTimeout(() => hpFloat.classList.remove('hit'), HP_FLASH);
      } else {
        ghostR = r;                               // 회복은 잔상이 바로 따라간다
      }
      fltR = r;
      hpFill.style.width = (r * 100).toFixed(2) + '%';
      const band = r > 0.5 ? 2 : (r > 0.25 ? 1 : 0);
      if (band !== fltBand) { fltBand = band; hpFill.style.background = HP_INK[band]; }
    }

    // ── 잔상 ──
    // 깎인 자리를 잠깐 붙들었다가 따라 줄어든다. "방금 이만큼 맞았다"를 말하는 층이다.
    if (ghostR < r) ghostR = r;
    if (ghostR > r) {
      if (ghostHold > 0) ghostHold -= dt;
      else ghostR = Math.max(r, ghostR - dt * HP_FADE);
      hpGhost.style.width = (ghostR * 100).toFixed(2) + '%';
    } else if (hpGhost.style.width !== '0%') {
      hpGhost.style.width = '0%';                 // 붙어 있으면 굳이 안 그린다
    }
  }

  // ★★rAF 등록을 **다음 태스크로 미룬다.** main.js 는 이 파일을 부른 **뒤**(파일 맨 끝
  //   4449행)에 tick() 을 처음 돌린다. 여기서 곧바로 걸면 우리 콜백이 main 보다 **앞**에
  //   서고, 그러면 한 프레임 전 좌표·카메라로 바를 붙이게 된다(대시 한 번에 10px 넘게
  //   뒤처진다. 눈에 보인다). setTimeout(0) 한 번이면 등록 순서가 main 뒤로 간다 -
  //   rAF 콜백은 등록 순서대로 돌고, 둘 다 콜백 맨 앞에서 다시 거니까 그 순서가 유지된다.
  function fltFrame(now) {
    requestAnimationFrame(fltFrame);
    updateHpFloat(now);
  }
  setTimeout(() => requestAnimationFrame(fltFrame), 0);

  // -------------------------------------------------------------------------
  // 폴링. 20Hz 면 카운트다운이 매끄럽고, 렌더 루프에는 한 프레임도 안 얹힌다.
  // (rAF 에 붙이면 60fps 예산을 같이 쓰게 된다. UI 는 그럴 이유가 없다)
  // -------------------------------------------------------------------------
  let lastRunT = 0;
  let clearedHelpDone = false;        // 층 돌파 때 안내판을 접었는가(한 판에 한 번)
  setInterval(() => {
    const boss = window.__boss;
    const enemy = window.__enemy;

    if (boss) {
      // 판이 되감겼는가(R·클리어 후 재도전). boss.time 은 층 소요 시간이라 0 으로 돌아간다
      const t = boss.time;
      if (t < lastRunT - 0.4) newRun();
      lastRunT = t;
      // 조우 = 보스가 플레이어를 물고 늘어지기 시작한 순간(phase 가 '보스전')
      if (!bannerDone && boss.phase === '보스전') showBanner();
      // ── 보스가 쓰러진 그 순간 (판정 S6) ──
      // ★엣지만 잡는다. '사망'은 판이 끝날 때까지 유지되는 값이라 레벨로 보면
      //   계기판이 영영 안 돌아온다.
      const bossDead = boss.state === '사망';
      if (bossDead && !bossDeadSeen) startCine(CINE_KILL);
      bossDeadSeen = bossDead;
      // 결과창이 뜨면 등장 클래스를 얹는다(opacity 는 boss.js 것이라 안 건드린다)
      const clearEl = document.getElementById('bClear');
      const cleared = !!boss.cleared;
      if (clearEl) {
        clearEl.classList.toggle('uiIn', cleared);
        // ★예전에는 .hint 한 줄만 갈아 끼웠다. 그래서 표 안의 「남쪽 문으로 반출」이
        //   그대로 나갔다(판정 S13). 패널 통째로 훑는다.
        //   ★fixClearKills 를 **먼저** 부른다. 뒤에 부르면 patchText 가 방금 고친
        //     처치 수를 옛 innerHTML 로 되돌린다.
        if (cleared) { fixClearKills(clearEl); patchText(clearEl); }
      }
      patchText(document.getElementById('bGoal'));
      // 판이 끝나면 화면을 눌러 둔다(입력은 main.js 가 잠근다)
      document.body.classList.toggle('uiCleared', cleared);
      // ── 층을 돌파한 순간 조작 안내를 접는다 (판정 S7) ──
      // ★CSS 로 감추는 것만으로는 모자란다. 감추기만 하면 R 로 다음 판을 시작하는
      //   순간 안내판이 **다시 펼쳐진 채로** 튀어나온다(uiCleared 가 풀리니까).
      // ★한 번만 부른다. 매 틱 부르면 클리어 화면에서 H 를 눌러도 50ms 뒤에 도로 접힌다.
      if (cleared && !clearedHelpDone) { clearedHelpDone = true; setHelp(true); }
      if (!cleared) clearedHelpDone = false;
      updateNav(boss, cleared);
      updatePip(cleared);
    }
    updateSkills();
    fixDevLabel();
    updateHp();
    fixSword();
    fixMute();

    if (enemy) {
      const d = enemy.dead;
      // 1) 엣지. 폴링이 dead 창을 통째로 건너뛰어도 이 시각은 안 사라진다.
      const stamp = window.__playerDied || 0;
      if (stamp > lastDiedStamp) { lastDiedStamp = stamp; showDeath(); }
      // 2) 레벨. 옛 경로도 남겨 둔다(enemy.js 가 낡은 빌드여도 창은 뜬다).
      else if (d && !wasDead) showDeath();
      // ── 내리는 시점 (v84 QA S2) ──
      // ★핵심: **텔레포트보다 먼저** 내려야 한다. 창이 떠 있는 동안 몸이 옮겨지면
      //   플레이어는 "죽었다"가 아니라 "튕겨났다"로 읽는다(실측: 예전 t=2.27s).
      //   벽시계로 세면 슬로모·프레임 스로틀에서 반드시 어긋난다.
      const left = (typeof enemy.deadIn === 'number') ? enemy.deadIn : null;
      const lead = (typeof enemy.respawnCardLead === 'number') ? enemy.respawnCardLead : RESPAWN_LEAD;
      const on = death.classList.contains('on');
      if (on && performance.now() >= deathHold) {
        // 되살아난 뒤(옛 경로) 또는 곧 되살아난다(새 경로) 둘 다 내린다
        if (!d || (left !== null && left <= lead)) hideDeath();
      }
      wasDead = d;
      if (d || on) {
        // 카운트다운도 게임시계를 쓴다. 없으면 벽시계로 어림한다(낡은 빌드).
        const total = (typeof enemy.respawnDelay === 'number') ? enemy.respawnDelay : RESPAWN_SEC;
        const sec = left !== null ? left
          : Math.max(0, total - (performance.now() - deadAt) / 1000);
        // ★판정 S8: 소수점이 20Hz 로 떨리니 눈이 거기 붙잡히고 문장이 안 끝난다.
        //   정수로 올림해서 세고 말을 끝맺는다. 1초 밑에서는 숫자가 아니라 「곧」이다.
        const n = Math.ceil(sec - 0.001);
        const want = n >= 1 ? (n + '초 뒤 ' + DEATH.line) : DEATH.soon;
        if (deathCnt.textContent !== want) deathCnt.textContent = want;
      }
    }
  }, 50);

  // -------------------------------------------------------------------------
  // 검증용 창구. 보스 앞까지 걸어가지 않고도 경고창·알림창을 화면에 세울 수 있어야 한다.
  const api = {
    showTitle, showBanner, toggleHelp,
    setHelp,
    get state() {
      return { helpOff, bannerDone, dead: wasDead, floor: FLOOR.name,
               deathCard: death.classList.contains('on'), diedAt: lastDiedStamp,
               banner: banner.classList.contains('on'),
               cleared: document.body.classList.contains('uiCleared'),
               // 나침반: 보이는가 · 어디에 · 어느 쪽을 가리키나 · 무슨 글자인가
               nav: { on: nav.style.opacity === '1', left: nav.style.left,
                      top: nav.style.top, rot: navDial.style.transform,
                      glyph: navPlate.textContent,
                      ink: nav.style.getPropertyValue('--nav-ink') },
               // 요괴 마커: 보이는가 · 어디에
               pip: { on: pip.style.opacity === '1', left: pip.style.left,
                      top: pip.style.top },
               // 상단 목표 문구(boss.js 가 쓴 것을 그대로 읽는다)
               goal: (document.getElementById('bGoal') || {}).textContent || '',
               // 스킬 칩: 밝은가(off 가 아니면 지금 쓸 수 있다) · 있는가
               skills: { X: { has: !skHeavy.classList.contains('gone'),
                              on: !skHeavy.classList.contains('off'),
                              rdy: skHeavy.classList.contains('rdy'),
                              cd: skHeavy.firstElementChild.style.background },
                         C: { has: !skWide.classList.contains('gone'),
                              on: !skWide.classList.contains('off'),
                              rdy: skWide.classList.contains('rdy'),
                              cd: skWide.firstElementChild.style.background } },
               // 계기판: 한 판에 모여 있는가 · 어디까지 차지하나 · 수치가 떠 있나
               dock: (() => { const r = dock.getBoundingClientRect();
                 return { rect: [Math.round(r.left), Math.round(r.top),
                                 Math.round(r.width), Math.round(r.height)],
                          hp: hpNum.textContent,
                          sword: swordEl ? swordEl.textContent : null,
                          cells: dock.children.length }; })(),
               help: { off: helpOff, touched: helpTouched },
               // 연출이 화면을 소유하는 중인가(판정 S6·S7 검증 창구)
               cine: document.body.classList.contains('uiCine'),
               bossIn: document.body.classList.contains('uiBossIn'),
               titleOn: document.body.classList.contains('uiTitleOn'),
               // 기술 이름 콜아웃: 시스템 팝이 씌워졌는가 · 무슨 型 인가(판정 S14)
               callout: (() => {
                 const c = comboEl && comboEl.querySelector('.uiCall');
                 return { on: !!c,
                          nm: c ? c.querySelector('.nm').textContent : '',
                          ty: c ? c.querySelector('.ty').textContent : '',
                          raw: comboEl ? comboEl.textContent : '' };
               })(),
               // 머리 위 체력바: 켜졌나 · 화면 어디에(사각형) · 채움/잔상은 몇 %
               // ★캐릭터 머리가 화면 어디인지도 같이 준다. 「바가 머리 위에 붙어 있나」를
               //   촬영 없이 숫자로 대조할 수 있어야 한다(검증 ①⑤).
               hpFloat: (() => {
                 const r = hpFloat.getBoundingClientRect();
                 const root = window.__root, scr = window.__screen;
                 const h = fltH;
                 let head = null;
                 if (root && scr && h) {
                   const s = scr(root.position.x, root.position.z, root.position.y + h);
                   head = [Math.round((s.x + 1) * 0.5 * innerWidth),
                           Math.round((1 - s.y) * 0.5 * innerHeight)];
                 }
                 return { on: hpFloat.classList.contains('on'),
                          op: +getComputedStyle(hpFloat).opacity,
                          rect: [Math.round(r.left), Math.round(r.top),
                                 Math.round(r.width), Math.round(r.height)],
                          fill: hpFill.style.width, ghost: hpGhost.style.width,
                          ink: fltBand, hit: hpFloat.classList.contains('hit'),
                          charH: h, head };
               })(),
               // 좁은 창에서 계기판이 화면 안에 다 들어오는가(판정 S2)
               fits: (() => { const r = dock.getBoundingClientRect();
                 const h = document.getElementById('help');
                 const hr = h ? h.getBoundingClientRect() : null;
                 return { dock: r.left >= 0 && r.right <= innerWidth,
                          dockW: Math.round(r.width), vw: innerWidth,
                          helpW: hr ? Math.round(hr.width) : 0 }; })(),
               // 층 표기(11차 개정: 화면 어디서나 아라비아 숫자)
               // ★위의 floor 는 **층 이름**(풀에 덮인 절터)이고 여기는 **층 번호 표기**다.
               floorNote: { card: FLOOR.no, banner: BOSS_CARD.tag,
                            hud: (document.getElementById('bName') || {}).textContent || '' } };
    },
    text: { FLOOR, BOSS_CARD, DEATH, SKILL_TYPE },
  };
  window.__ui = api;
  return api;
}

function el(tag, id) {
  const e = document.createElement(tag);
  e.id = id;
  return e;
}
