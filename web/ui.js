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
// ═══ 12차 파도: 시스템창 → 로블록스+메이플+롤 (오너 지시 「전체 UI 컨셉을
//     로블록스+메이플+롤 느낌으로 바꿔줘」. 이 파일의 3차 리테마다) ═══════════════
// 컨셉 정본 두 장(오너 승인) - incoming/codex_ui/hud_concept.png · popup_concept.png
// 화면의 모든 판을 그 두 장의 문법 한 벌로 갈아입힌다.
//
//   판   : 둥근 남색(칩 12px · 슬롯 14px · 카드 20px · 알약 999px). 불투명
//   테   : 또렷한 크림 2~3px + 그 **바깥에 어두운 링** 한 겹(밝은 초원 위 가독의 핵심)
//   모서리: 전부 둥글다. 각진 판은 이 벌에 하나도 없다(11차와 정반대)
//   발광 : **안 쓴다.** 존재감은 테의 또렷함과 글자 밑 딱딱한 그림자 한 겹으로 낸다
//   카드 : 위 가운데 민트 탭 노치 + 왼쪽 변에 걸친 동그란 아이콘 뱃지(이 벌의 서명)
//   글자 : 볼드 산세리프(Pretendard 계열 시스템 스택, 700~800). 숫자는 tabular
//   포인트: 민트(라벨·탭) · 노랑(목표·강조) · 빨강(경고·체력) 셋뿐
//   경고 : 같은 판에 붉은 변주(보스 조우 · 사망). 판 색은 안 바꾼다
//
// ★저작권: 스타일 문법(색·모서리·배치)만 차용한다. 로고·원문 문구·전용 서체는
//   한 점도 안 쓴다. 화면에 나가는 말은 전부 이 게임이 원래 쓰던 우리 문구다.
//
// ★이번 작업은 **스킨 교체**다. 정보 설계·문구·발화 타이밍·수명·키 배정·반응형 단계·
//   safeBox·awake 원샷·물림 규칙은 한 칸도 안 건드렸다.
//
// ★붓 서체(RFBrush)는 11차에 UI 에서 은퇴했다. web/fonts/ 의 woff2 두 벌은
//   **지우지 않았다**(다른 곳에서 참조할 수 있다). 여기서는 @font-face 도 preload 도 안 건다.

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
  // ★17차: 보스 경고창도 '경고'였다. 같은 말이 두 창의 머리에 걸리면 머리말이
  //   창을 구별하는 일을 못 한다(비평 7). 사망 쪽을 상태 낱말로 내린다 -
  //   '경고'는 앞으로 다가올 일이고, 이건 이미 일어난 일이다.
  head: '쓰러짐',                   // 창 머리(붉은 변주)
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
/* ══ 16차 리테마: 롤 + 소드아트온라인 + 메이플 블렌드 ══════════════════════════
   오너 지시 두 줄이 이 벌의 전부다.
     ① "롤 + 소드아트온라인 + 메이플스토리 합친모드로해. 가장중요한건 사람들이
        게임하고싶게끔느껴지는 ui여야해. 캡쳐하고싶고."
     ② "아래 그 스킬이랑 체력바있고 이런거 가로로길게해서 좀 롤이나 메이플처럼해봐.
        지금은 가운데 떠있어서 화면너무가림"

   컨셉 정본 세 장(codex 생성) - incoming/codex_ui3/hud_bar.png · cards.png · parts.png
   레퍼런스 실물 - renders/history/v99_wave16/ui_blend/ref/ (+ v99_wave13/uimaple2/ref/)
   분석 정본 - docs/references/ui-blend-analysis.md  ★색·형태를 바꾸기 전에 그 문서를 읽을 것

   ── 블렌드 규칙 한 줄 ────────────────────────────────────────────────────────
   **롤에서 뼈대를, 소드아트온라인에서 살갗을, 메이플에서 심장 박동을 가져온다.**
     롤   : 화면 아래 테두리에 붙은 **가로 띠**. 좌=나 / 중=누를 것 / 우=가진 것.
            정사각 슬롯, 쿨다운은 시계 쓸기 + 안쪽 큰 숫자. 화면 가운데는 비운다
     SAO  : 유리판 + **1px 헤어라인** + **컷코너(모서리를 45도로 자른다)** + 삼각 노치 +
            마름모 글리프 + 자간 벌린 라벨. 두꺼운 테·입체 그림자·종이 결은 **전부 없다**
     ★★실측 정정(16차 레퍼런스 17장 픽셀 샘플링). 흔히 말하는 "SAO = 시안"은 **틀렸다.**
       아인크라드기 SAO 의 판은 **흰 프로스트 유리**(흰색 40~60% + 배경 탈색)이고
       주액센트는 시안이 아니라 **주황·앰버 #E8A31E**(선택된 행)다. 시안은 보조다.
       그런데 우리는 흰 판을 못 쓴다 - 13차 기각본이 바로 그 밝은 아이보리 판이었다.
       그래서 **판은 SAO 앨리시제이션기의 다크 홀로 패널**(ref sao_14: ㄱ자 브라켓 ·
       회로 배선 · 도트 스캔 · 십자 마커) 쪽을 취하고, **앰버는 뜻으로 되살렸다** -
       목표·보상·성장(레벨 뱃지 · EXP 띠 · 결과 수치)이 전부 앰버다. 시안은 시스템·기술.
       SAO 에서 가져온 나머지: 게이지 끝을 **45도로 자른다(둥근 캡 금지)** · 채움 위아래
       **흰 1px 선** · 삼각 노치 · 마름모 글리프 · 장식은 특수 상태에만.
     메이플: 채도 높은 게이지 채움 + 광택 한 줄, 수치는 **바 안**, 맨 아래 EXP 띠, 레벨 뱃지

   ── 13차(기각본)와의 실측 차이 ──────────────────────────────────────────────
     계기판 높이  161px(화면의 17.9%)  ->  76px(8.4%)     ★"화면 너무 가림"의 정체
     계기판 폭    화면의 37%           ->  100%(전폭)      ★가로로 짧고 세로로 두꺼웠다
     층수         3층 세로 쌓기        ->  **한 줄**
     판 색        아이보리 종이+갈색 테 ->  어두운 유리+시안 헤어라인

   ★컷코너는 clip-path 로 만든다(폭이 바뀌어도 따라온다. 회전 사각형·border-image 는 어긋난다).
     ★★clip-path 는 **바깥 그림자·발광을 통째로 자른다.** 발광이 필요한 판은
       box-shadow 가 아니라 filter:drop-shadow 를 쓴다 - 그건 잘린 실루엣을 따라간다.
       늘 떠 있는 조각(계기판)에는 filter 를 안 건다(매 상태변화마다 다시 그린다).
   ★색을 바꿀 때는 index.html 의 로딩 화면 CSS 도 **같이** 바꿀 것(정본이 두 벌이다).
   ★이번 작업은 표면과 배치 교체다. 정보 항목 · 문구 · 키 배정 · 발화 타이밍 · 수명 ·
     safeBox · awake 원샷 · 연출 물림 규칙(이 파일 맨 끝 블록)은 한 칸도 안 건드렸다. */
:root{
  --ui-font:${SANS};
  /* 판 - 어두운 유리 */
  --ui-glass:rgba(13,20,36,.90);
  --ui-glass-2:rgba(7,12,23,.94);
  --ui-deep:#05080f;
  /* 선 */
  --ui-edge:rgba(196,230,255,.34);      /* 기본 헤어라인 */
  --ui-edge-on:rgba(120,224,255,.78);   /* 살아 있는 판 */
  --ui-hair:rgba(255,255,255,.09);      /* 면 위 미세 분할선 */
  /* 글자 */
  --ui-txt:#eaf4ff;
  --ui-dim:#9fb4cc;
  --ui-mute:#63788e;
  /* 액센트 셋 */
  --ui-cy:#56d8ff;
  --ui-cy-dim:#2f86a6;
  --ui-gold:#ffbb3d;
  --ui-red:#ff5a4a;
  /* 뜻이 걸린 색. 스킨이 바뀌어도 이 뜻은 안 바뀐다 */
  --ui-green:#3ddc84;
  --rb-token:#ffbb3d;   /* 증표 */
  --rb-ok:#3ddc84;      /* 은신 */
  /* 그림자 한 겹. 입체 오프셋(0 4px 0 …)은 이 벌에 하나도 없다 */
  --ui-drop:0 8px 22px rgba(0,0,0,.55);
}
/* 가짜 굵기·가짜 기울임 금지. ★800 을 부르면 Pretendard(있으면) 나 Apple SD Gothic Neo
   의 **진짜 굵은 자소**로 떨어진다. 없는 굵기를 만들어 내면 획이 뭉개진다. */
body{font-synthesis:none;-webkit-font-synthesis:none}

/* ── 컷코너 한 벌 ────────────────────────────────────────────────────────────
   같은 다각형을 쓰는 판을 여기 한 번에 모은다. 크기(--c)만 각자 다르다.
   ★남의 DOM(#bClear)에도 클래스를 못 붙이므로 선택자 목록으로 관리한다. */
#uiTitle .win,#uiBanner .win,#uiDeath .win,#bClear,
#uiSkills .sk,#uiSkills .skLock,#eBar,#bBox,#bGoal,#help,#stat,#uiHelpChip,
#combo .uiCall,#uiDock .dkSword,#uiSkills .sk .key,#uiDock .dkLv,
#uiHpFloat .track,#uiHpFloat .lv,#uiNav .plate,#uiPip,#stHud,#uiNav .cap,#uiPip .cap,#uiNav .dst{
  clip-path:polygon(var(--c) 0,calc(100% - var(--c)) 0,100% var(--c),
                    100% calc(100% - var(--c)),calc(100% - var(--c)) 100%,
                    var(--c) 100%,0 calc(100% - var(--c)),0 var(--c))}

/* ── 카드 등장 ──────────────────────────────────────────────────────────────
   ★시간은 13차 값 그대로다(.46 / .40 / .30s). 곡선도 그대로.
   --sp 로 전체 속도를 조절한다. 1 = 첫 입장, 0.38 = R 재시작(짧게). */
@keyframes sysWin{
  from{opacity:0;transform:scale(.94)}
  62% {opacity:1;transform:scale(1.012)}
  to  {opacity:1;transform:none}
}
@keyframes sysUp{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}
@keyframes sysRule{from{opacity:0;transform:scaleX(0)}to{opacity:1;transform:scaleX(1)}}

/* ══ 창 한 벌 (어두운 유리 + 헤어라인 + 컷코너) ═══════════════════════════════
   ★★position 을 이 표에 **절대 넣지 말 것.** #bClear 는 boss.js·level2.js 가
     position:fixed + transform 으로 화면 가운데를 잡고 있어서, 여기서 relative 로
     덮으면 패널이 문서 흐름으로 돌아가 **화면 밖 아래**로 사라진다. 실제로 한 번
     그렇게 만들었고 클리어 촬영에서 판이 통째로 안 나와서 잡았다(11차 기록).
     자기 DOM 인 .win 세 개만 아래 줄에서 따로 relative 를 받는다.
   ★backdrop-filter(진짜 유리 흐림)는 안 쓴다. 캔버스 위에서 매 프레임 도는 비용이라
     게임 프레임을 먹는다. 반투명 + 어두운 바탕이면 흐림 없이도 글자가 뜬다. */
#uiTitle .win,#uiBanner .win,#uiDeath .win{position:relative}
#uiTitle .win,#uiBanner .win,#uiDeath .win,#bClear{
  --c:14px;
  background:
    repeating-linear-gradient(0deg,rgba(120,190,255,.030) 0 1px,rgba(0,0,0,0) 1px 4px),
    linear-gradient(180deg,var(--ui-glass) 0%,var(--ui-glass-2) 100%);
  box-shadow:inset 0 0 0 1.5px var(--ui-edge-on),
             inset 0 0 40px rgba(60,150,220,.10);
  filter:drop-shadow(0 0 14px rgba(86,216,255,.26)) drop-shadow(0 10px 26px rgba(0,0,0,.62));
  color:var(--ui-txt);
  font-family:var(--ui-font);font-variant-numeric:tabular-nums}
/* 붉은 변주(보스 경고 · 사망). ★판 색은 안 바꾼다 - 선·라벨·글자만 붉다.
   판까지 붉히면 다른 물건이 된다(13차 규칙 그대로). */
#uiBanner .win,#uiDeath .win{
  box-shadow:inset 0 0 0 1.5px rgba(255,110,88,.80),
             inset 0 0 40px rgba(190,60,40,.14);
  filter:drop-shadow(0 0 14px rgba(255,90,74,.28)) drop-shadow(0 10px 26px rgba(0,0,0,.62))}

/* ── 창 위아래의 시안 표식 ────────────────────────────────────────────────────
   컨셉(cards.png)의 서명이다. 위 가운데에 짧은 밝은 막대 하나 + 그 아래 얇은 실선.
   ★13차의 「탭 노치」·「네이비 띠」가 있던 자리를 그대로 물려받는다 - DOM(.fr)은
     그대로 두고 뜻만 갈아 끼웠다. */
#uiTitle .fr,#uiBanner .fr,#uiDeath .fr{
  content:'';position:absolute;left:0;right:0;top:0;height:34px;margin:0;
  border:0;border-radius:0;pointer-events:none;
  background:
    linear-gradient(90deg,rgba(86,216,255,0),var(--ui-cy) 22%,var(--ui-cy) 78%,rgba(86,216,255,0))
      no-repeat 50% 0 / 132px 3px,
    linear-gradient(90deg,rgba(86,216,255,0),rgba(120,205,255,.42) 30%,
      rgba(120,205,255,.42) 70%,rgba(86,216,255,0)) no-repeat 50% 33px / 100% 1px}
#uiBanner .fr,#uiDeath .fr{
  background:
    linear-gradient(90deg,rgba(255,90,74,0),var(--ui-red) 22%,var(--ui-red) 78%,rgba(255,90,74,0))
      no-repeat 50% 0 / 132px 3px,
    linear-gradient(90deg,rgba(255,90,74,0),rgba(255,140,120,.44) 30%,
      rgba(255,140,120,.44) 70%,rgba(255,90,74,0)) no-repeat 50% 33px / 100% 1px}

/* 아래 변의 짝. 컨셉(cards.png)의 창은 위아래가 대칭이다 - 위가 「열림」이면
   아래가 「닫힘」이라 판이 한 덩어리로 닫힌다. */
#uiTitle .win::before,#uiBanner .win::before,#uiDeath .win::before{
  content:'';position:absolute;left:0;right:0;bottom:0;height:14px;pointer-events:none;
  background:
    linear-gradient(90deg,rgba(86,216,255,0),var(--ui-cy) 22%,var(--ui-cy) 78%,rgba(86,216,255,0))
      no-repeat 50% 100% / 96px 2px}
#uiBanner .win::before,#uiDeath .win::before{
  background:
    linear-gradient(90deg,rgba(255,90,74,0),var(--ui-red) 22%,var(--ui-red) 78%,rgba(255,90,74,0))
      no-repeat 50% 100% / 96px 2px}

/* 삼각 노치. SAO 의 시그니처 둘 중 하나다(다른 하나가 컷코너).
   ★#bClear 는 가상요소 둘이 이미 차 있어서(::before=위 표식, ::after=창 이름) 노치가 없다.
     남의 DOM 을 안 건드린다는 규칙이 장식보다 위다. */
#uiTitle .win::after,#uiBanner .win::after,#uiDeath .win::after{
  content:'';position:absolute;left:50%;top:34px;margin-left:-7px;
  width:0;height:0;pointer-events:none;
  border-left:7px solid transparent;border-right:7px solid transparent;
  border-top:7px solid var(--ui-cy);opacity:.9}
#uiBanner .win::after,#uiDeath .win::after{border-top-color:var(--ui-red)}

/* ── 창 이름 (「알림」·「경고」) ───────────────────────────────────────────────
   ★13차는 네이비 띠 안에 눕혔다. 이 벌은 띠가 없고 **위 실선 바로 밑**에 앉는다.
     자리를 absolute 로 못박아야 카드마다 다른 padding 을 안 탄다. */
#uiTitle .hd,#uiBanner .hd,#uiDeath .hd{display:block;text-align:center}
/* 13차의 원 뱃지(.ic)는 이 벌에 없다 - 유리창에는 스티커가 안 붙는다.
   대신 그 <i> 를 **모서리 해시 마크**로 다시 쓴다(컨셉 cards.png 의 서명. 왼쪽 위와
   오른쪽 아래에 길이가 다른 짧은 선 셋). 한 요소의 배경 여섯 겹이라 DOM 은 안 는다.
   ★글자 '!' 가 들어 있으므로 font-size:0 으로 지운다(요소를 지우면 서명도 없어진다).
   ★.hd 는 position 이 없어서 inset 은 **.win** 기준으로 잡힌다(.win 이 relative). */
#uiTitle .hd .ic,#uiBanner .hd .ic,#uiDeath .hd .ic{
  display:block;position:absolute;inset:13px;font-size:0;pointer-events:none;opacity:.55;
  background:
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 0 0 / 15px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 0 4px / 10px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 0 8px / 5px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 100% 100% / 15px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 100% calc(100% - 4px) / 10px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 100% calc(100% - 8px) / 5px 1px}
#uiBanner .hd .ic,#uiDeath .hd .ic{
  background:
    linear-gradient(90deg,var(--ui-red),var(--ui-red)) no-repeat 0 0 / 15px 1px,
    linear-gradient(90deg,var(--ui-red),var(--ui-red)) no-repeat 0 4px / 10px 1px,
    linear-gradient(90deg,var(--ui-red),var(--ui-red)) no-repeat 0 8px / 5px 1px,
    linear-gradient(90deg,var(--ui-red),var(--ui-red)) no-repeat 100% 100% / 15px 1px,
    linear-gradient(90deg,var(--ui-red),var(--ui-red)) no-repeat 100% calc(100% - 4px) / 10px 1px,
    linear-gradient(90deg,var(--ui-red),var(--ui-red)) no-repeat 100% calc(100% - 8px) / 5px 1px}
#uiTitle .hd b,#uiBanner .hd b,#uiDeath .hd b,#bClear::after{
  position:absolute;left:0;right:0;top:44px;z-index:2;
  text-align:center;line-height:1;
  font-size:12px;font-weight:800;letter-spacing:.22em;padding-left:.22em;
  color:var(--ui-cy);text-shadow:0 0 10px rgba(86,216,255,.55)}
#uiBanner .hd b,#uiDeath .hd b{color:var(--ui-red);text-shadow:0 0 10px rgba(255,90,74,.55)}

/* ── 1) 입장 알림창 ──────────────────────────────────────────────────────────
   ★v95 판정 S3: 「층 타이틀 카드가 캐릭터와 정중앙에서 겹친다.」 시점이 고정 쿼터뷰라
     캐릭터는 **항상 화면 정중앙**에 선다. 그래서 창을 화면 위쪽 1/3 에 앉힌다.
   ★사망 창(#uiDeath)은 정중앙 그대로 둔다(자리만으로 안 헷갈린다. 위=입장, 가운데=사망). */
#uiTitle{position:fixed;inset:0;z-index:12;pointer-events:none;user-select:none;
  display:flex;flex-direction:column;align-items:center;justify-content:flex-start;
  padding-top:clamp(46px,8vh,110px);
  opacity:0;transition:opacity .55s ease;--sp:1}
#uiTitle.on{opacity:1}
#uiTitle.out{opacity:0}
/* 비네트. 화면을 눌러 카드만 남긴다.
   ★1층은 **밝은 봄 초원**이다. 어두운 던전 기준으로 옅게 깔면 카드가 흙바닥에 묻힌다.
   ★초점을 24% 에 둔다. 밝은 눈은 **카드가 있는 자리**여야 한다. */
#uiTitleBg{position:fixed;inset:0;z-index:11;pointer-events:none;opacity:0;
  transition:opacity .6s ease;
  background:radial-gradient(ellipse at 50% 24%,rgba(10,26,48,.52) 0%,rgba(2,4,10,.94) 78%)}
#uiTitleBg.on{opacity:1}
#help,#bHud,#stat{transition:opacity .5s ease}
/* ★★계기판을 물리는 규칙들은 **이 파일 CSS 의 맨 끝**에 모아 뒀다(「연출이 화면을
     소유한다」 블록). 여기 두면 아래쪽의 같은-특이도 규칙에게 진다. */

#uiTitle .win{width:min(520px,80vw);padding:70px 44px 30px;text-align:center;
  transform-origin:50% 0}
#uiTitle.run .win{animation:sysWin calc(.46s*var(--sp)) cubic-bezier(.2,1.02,.3,1) both}
#uiTitle .bd{padding-top:0}
/* .big = 「탑 1층」(크게), .sub = 「풀에 덮인 절터」(그 밑) */
#uiTitle .big{font-size:clamp(30px,4.2vh,46px);font-weight:800;letter-spacing:.02em;
  color:var(--ui-txt);line-height:1.14;text-shadow:0 0 22px rgba(120,200,255,.45)}
#uiTitle .sub{font-size:clamp(14px,1.9vh,18px);font-weight:700;letter-spacing:.1em;
  color:var(--ui-cy);margin-top:8px;text-shadow:0 0 12px rgba(86,216,255,.4)}
/* 얇은 실선 + 가운데 마름모(컨셉의 그 표식) */
#uiTitle .rule,#uiDeath .rule{position:relative;width:190px;height:1px;margin:18px auto 15px;opacity:0;
  background:linear-gradient(90deg,rgba(120,205,255,0),rgba(120,205,255,.55),rgba(120,205,255,0))}
#uiTitle .rule::after,#uiDeath .rule::after{content:'';position:absolute;left:50%;top:50%;
  width:6px;height:6px;margin:-3px 0 0 -3px;transform:rotate(45deg);
  background:var(--ui-cy);box-shadow:0 0 8px rgba(86,216,255,.7)}
#uiTitle .lore{font-size:clamp(11px,1.45vh,13.5px);font-weight:600;letter-spacing:.05em;
  color:var(--ui-dim);opacity:0}
/* 실제 재생은 .run 이 붙을 때만. 클래스를 뺐다 붙이면 같은 카드를 다시 틀 수 있다 */
#uiTitle.run .big {animation:sysUp  calc(.42s*var(--sp)) ease-out calc(.20s*var(--sp)) both}
#uiTitle.run .sub {animation:sysUp  calc(.42s*var(--sp)) ease-out calc(.34s*var(--sp)) both}
#uiTitle.run .rule{animation:sysRule calc(.40s*var(--sp)) ease-out calc(.48s*var(--sp)) both}
#uiTitle.run .lore{animation:sysUp  calc(.42s*var(--sp)) ease-out calc(.58s*var(--sp)) both}

/* ── 2) 보스 조우 경고창 ─────────────────────────────────────────────────────
   보스 HUD(#bHud)와 **같은 자리**를 쓴다. 배너가 빠지면서 체력바가 그 자리에 든다.
   ★가로 가운데잡기를 transform 으로 안 한다(이 파일이 예전에 밟은 함정이다).
     등장 애니가 transform 을 쓰기 때문에, 카드를 transform 으로 가운데에 놓으면
     애니가 붙는 순간 가운데잡기가 통째로 날아간다. */
#uiBanner{position:fixed;left:0;right:0;top:0;z-index:10;
  pointer-events:none;user-select:none;display:flex;justify-content:center;
  padding-top:26px;opacity:0;transition:opacity .45s ease}
#uiBanner.on{opacity:1}
#uiBanner .win{width:min(560px,88vw);padding:64px 44px 22px;text-align:center;
  transform-origin:50% 0}
#uiBanner.on .win{animation:sysWin .40s cubic-bezier(.2,1.02,.3,1) both}
#uiBanner .bd{padding-top:0}
#uiBanner .tag{font-size:12.5px;font-weight:700;letter-spacing:.12em;
  color:#ffab97;text-shadow:none}
/* 이름 좌우의 붉은 표식. 컨셉 경고 카드의 마름모 두 개다(글자가 아니라 장식).
   ★자리를 absolute 로 잡지 않고 **flex 줄에 태운다.** 우리 보스 이름은 두 글자라
     표식을 카드 양 끝에 붙이면 이름과 따로 노는 물건이 된다(실측 컷에서 잡았다). */
#uiBanner .name{display:flex;align-items:center;justify-content:center;gap:.5em;
  font-size:clamp(30px,4.2vh,46px);font-weight:800;letter-spacing:.02em;
  color:#ff7a63;margin-top:8px;line-height:1.14;
  text-shadow:0 0 24px rgba(255,90,74,.55)}
#uiBanner .name::before,#uiBanner .name::after{
  content:'';width:9px;height:9px;flex:0 0 9px;transform:rotate(45deg);
  background:var(--ui-red);box-shadow:0 0 10px rgba(255,90,74,.8)}
#uiBanner.on .tag {animation:sysUp .40s ease-out .18s both}
#uiBanner.on .name{animation:sysUp .44s ease-out .28s both}
/* 배너가 떠 있는 동안 보스 HUD 를 눌러 둔다. 배너가 **다 빠진 뒤에** 이 클래스가
   풀리고, 그때 boss.js 의 .25s 전환이 이어받아 체력바가 뜬다(boss.js 는 안 건드린다). */
body.uiBossIn #bHud{opacity:0;transition:opacity .3s ease}
#bHud{transition:opacity .4s ease}

/* ── 상단 목표 태그 · 보스 체력바 ────────────────────────────────────────── */
#bHud{top:16px;width:min(640px,84vw)}
/* ★★#bBox 를 inline-block 으로 두지 말 것. #bGoal 도 inline 계열이라 **둘이 한 줄에
     올라타고**, 그러면 목표 태그가 보스 상자(투명해도 자리는 차지한다)에 밀려
     화면 가운데에서 43px 왼쪽으로 어긋난다(실측으로 잡았다). */
#bBox{--c:7px;margin-top:12px;padding:7px 14px 9px;
  background:linear-gradient(180deg,rgba(28,12,14,.86),rgba(12,6,8,.92));
  box-shadow:inset 0 0 0 1px rgba(255,110,88,.55),inset 0 0 18px rgba(190,50,36,.22)}
#bName{margin-bottom:6px;line-height:1.2;
  font-size:11.5px;font-weight:800;letter-spacing:.16em;
  color:#ff9d88;text-shadow:0 0 8px rgba(255,90,74,.4)}
#bBar{height:11px;border:0;border-radius:0;background:rgba(3,5,10,.9);
  box-shadow:inset 0 0 0 1px rgba(255,110,88,.34)}
#bFill{filter:saturate(1.1) brightness(1.05)}
/* 목표 태그. 「목표 · …」. ★본문 글자는 boss.js 가 쓴 그대로 나간다.
   라벨과 마름모는 가상요소라 boss.js 가 innerHTML 을 다시 써도 안 지워진다.

   ★★17차 비평 4 「증표 를 집어라」의 진범 = **이 판이 flex 였던 것**이다.
     16차는 inline-flex + gap:9px 이었다. flex 통에 들어간 글자는 「연속한 글자 덩어리
     하나 = 익명 플렉스 아이템 하나」로 쪼개진다 - 즉 boss.js 가 쓴
     「제단의 <i>증표</i>를 집어라」 가 [제단의][증표][를 집어라] 세 칸이 되고,
     그 사이마다 gap 9px 이 끼어들어 **조사가 낱말에서 떨어져 나갔다**(실측 9.0px).
     같은 이유로 「· 고블린들이…」 앞에도 없는 공백이 생겼다.
     ★익명 아이템은 앞뒤 공백까지 지워지므로 gap 만 0 으로 줄이면 이번엔
       「제단의증표를」로 붙는다. flex 를 **쓰지 않는 것**만이 답이다.
   ★그래서 판을 inline-block 으로 되돌리고, 마름모·「목표」 라벨은 absolute 로
     왼쪽에 못박는다(자리는 padding-left 가 비워 준다). 본문은 한 줄의 보통 글이라
     조사가 붙는다 - 한글 조판에서 강조는 **자리를 넓히지 말고 배경만 넓혀야** 한다.
     이 판에 margin·gap 을 다시 넣지 말 것. */
#bGoal{--c:9px;display:inline-block;position:relative;
  padding:8px 20px 9px 74px;border:0;line-height:1.32;
  background:linear-gradient(180deg,rgba(30,22,8,.86),rgba(14,10,4,.92));
  box-shadow:inset 0 0 0 1px rgba(255,187,61,.62),inset 0 0 20px rgba(190,130,20,.18);
  color:var(--ui-txt);font-size:13.5px;font-weight:700;letter-spacing:.01em;
  text-shadow:none;opacity:1}
/* 금색 마름모 + 「목표」 라벨. 둘 다 왼쪽 여백 안에 절대 좌표로 선다.
   ★마름모는 transform 이 rotate 로 차 있으므로 세로 가운데잡기를 margin 으로 한다. */
#bGoal::before{content:'';position:absolute;left:19px;top:50%;
  width:11px;height:11px;margin:-5.5px 0 0;
  transform:rotate(45deg);background:var(--ui-gold);
  box-shadow:0 0 10px rgba(255,187,61,.75),inset 0 0 0 2px rgba(20,14,2,.55)}
#bGoal::after{content:'목표';position:absolute;left:39px;top:50%;
  transform:translateY(-50%);line-height:1;color:var(--ui-gold);
  font-size:11px;font-weight:800;letter-spacing:.2em}
/* 강조 낱말. ★색과 굵기까지만 한다. padding 을 주고 싶으면 반드시
   「margin:0 -N」 을 짝으로 붙여 **배경만 넓힐 것**(자리를 넓히면 조사가 떨어진다). */
#bGoal i{color:var(--ui-gold);font-style:normal;font-weight:800}
/* 빈 목표줄은 태그도 안 그린다(첫 프레임에 빈 판이 깜빡이는 것을 막는다) */
#bGoal:empty{display:none}

/* ── 3) 사망 경고창 ──────────────────────────────────────────────────────────
   enemy.js 의 「쓰러졌다」(#eDead)는 여기 카드가 대신한다. 리스폰 로직은 그대로 돈다.
   ★「落」은 남긴다. 붓 장식이 아니라 **도장**이다(한 글자가 「쓰러졌다」를 말한다). */
#eDead{opacity:0!important}
#uiDeath{position:fixed;inset:0;z-index:11;pointer-events:none;user-select:none;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  opacity:0;transition:opacity .4s ease;
  background:
    radial-gradient(ellipse 44% 36% at 50% 48%,rgba(150,26,18,.34) 0%,rgba(150,26,18,0) 100%),
    radial-gradient(ellipse at 50% 48%,rgba(4,7,14,.90) 0%,rgba(1,2,6,.985) 68%)}
#uiDeath.on{opacity:1}
/* 카드가 떠 있는 동안 HUD 를 물린다(입장 카드와 같은 규칙) */
body.uiDeathOn #help,body.uiDeathOn #uiDock,body.uiDeathOn #bHud,
body.uiDeathOn #stat,body.uiDeathOn #stHud,body.uiDeathOn #uiHpFloat{opacity:.05}
body.uiDeathOn #uiNav,body.uiDeathOn #uiPip,
body.uiDeathOn #stVig{opacity:.05!important}
#uiDeath .win{width:min(400px,76vw);padding:66px 34px 30px;text-align:center;
  transform-origin:50% 50%}
#uiDeath.on .win{animation:sysWin .30s cubic-bezier(.2,1.02,.3,1) both}
#uiDeath .bd{padding-top:0}
#uiDeath .glyph{font-size:clamp(84px,13vh,124px);font-weight:800;line-height:1.14;
  color:#fff1ee;text-shadow:0 0 30px rgba(255,90,74,.85),0 0 70px rgba(255,60,40,.4)}
#uiDeath .rule{width:150px;margin:14px auto 13px;
  background:linear-gradient(90deg,rgba(255,120,100,0),rgba(255,120,100,.6),rgba(255,120,100,0))}
#uiDeath .rule::after{background:var(--ui-red);box-shadow:0 0 8px rgba(255,90,74,.8)}
/* ★판정 S8: 「0.0초 뒤 다시」 - 소수점이 떨려 눈이 붙잡히고 문장이 안 끝난다.
     한 줄로 합치고 정수로 센다 - 「3초 뒤 다시 일어선다」. */
#uiDeath .cnt{font-size:clamp(13px,1.7vh,16px);font-weight:700;letter-spacing:.04em;
  color:#ffb0a0;font-variant-numeric:tabular-nums;text-shadow:none}
#uiDeath.on .glyph{animation:sysUp  .28s ease-out .06s both}
#uiDeath.on .rule {animation:sysRule .34s ease-out .16s both}
#uiDeath.on .cnt  {animation:sysUp  .28s ease-out .22s both}

/* ── 4) 조작 안내 ────────────────────────────────────────────────────────────
   판정 S8·S13 로 다듬은 정보 설계(키 열 오른쪽 정렬·비-키는 맨 아래 주석)는 그대로.
   ★13차 판은 아이보리 큰 판이라 화면 왼쪽 1/4 를 먹었다. 유리로 내리고 글자를 줄인다. */
/* ★★17차 비평 9 「도움말 판이 고정 픽셀이라 1100 폭에서 화면의 24% x 47.9% 를 먹는다」.
     16차 값은 전부 px 못박기였다(13px · 106px 열 · 12/15/13 여백). 창이 작아져도
     판만 그대로라 좁은 창일수록 화면을 더 많이 가린다 - 정확히 거꾸로다.
   ★고침: **판의 모든 치수를 글자 크기 하나(--hf)에 매단다.** 그 하나만 창 크기를
     따라가면 판 전체가 같이 줄어든다(em 은 부모 글자 크기를 따르므로 열 폭·여백·
     키캡까지 한 번에 따라온다).
   ★--hf 는 가로·세로 **둘 다** 본다. 세로가 짧은 창에서 판이 계기판을 파고드는
     사고가 13차·14차에 두 번 있었다(min() 의 두 번째 항이 그 보험이다). */
#help{--c:10px;--hf:clamp(10.4px,min(.68vw + 4.2px,1.45vh + 1.2px),13px);
  position:fixed;font-family:var(--ui-font);color:var(--ui-dim);
  left:clamp(10px,1.06vw,16px);top:clamp(10px,1.47vh,14px);
  font-size:var(--hf);line-height:1.5;
  padding:.9em 1.1em .95em;border:0;
  background:
    repeating-linear-gradient(0deg,rgba(120,190,255,.026) 0 1px,rgba(0,0,0,0) 1px 4px),
    linear-gradient(180deg,rgba(10,16,29,.86),rgba(6,10,20,.90));
  box-shadow:inset 0 0 0 1px var(--ui-edge),inset 0 0 26px rgba(50,130,200,.08);
  text-shadow:none;
  transition:opacity .42s ease,transform .42s ease}
#help b{color:var(--ui-txt);font-weight:800}
#help .hRow{gap:.62em;padding:0}
/* ★키 열은 **가장 긴 줄(「이동+ Space」)이 들어가는 최소값**이다. 더 줄이면 그 줄만
   판 밖 왼쪽으로 흘러나간다(flex-basis 고정이라 줄지도 늘지도 않는다). */
#help .ks{flex:0 0 6.9em;gap:.3em}
/* 키캡. 어두운 유리 + 헤어라인 + 컷코너(작은 판이라 4px) */
#help .k{--c:4px;border:0;border-radius:0;background:rgba(20,30,50,.92);
  box-shadow:inset 0 0 0 1px rgba(160,210,255,.42);
  clip-path:polygon(4px 0,calc(100% - 4px) 0,100% 4px,100% calc(100% - 4px),
                    calc(100% - 4px) 100%,4px 100%,0 calc(100% - 4px),0 4px);
  color:var(--ui-txt);font-weight:700;text-shadow:none;
  font-size:.92em;min-width:1.9em;padding:1px .5em 2px}
#help .kx{color:var(--ui-mute);font-weight:600;font-size:.92em}
#help .t{color:var(--ui-dim);font-weight:600}
#help .t b{color:var(--ui-txt)}
#help .hSep{height:1px;border-radius:0;margin:.5em .3em .55em 0;
  background:linear-gradient(90deg,rgba(120,205,255,.34),rgba(120,205,255,0))}
#help .hNote{color:var(--ui-mute);font-weight:600;font-size:.92em;line-height:1.45}
body.uiHelpOff #help{opacity:0;transform:translateX(-10px)}
/* 「?」 칩. 같은 유리 문법(판만, 문구는 그대로 「?」) */
#uiHelpChip{--c:8px;position:fixed;left:16px;top:14px;z-index:7;width:34px;height:34px;
  border:0;background:linear-gradient(180deg,rgba(14,22,38,.92),rgba(7,12,23,.94));
  box-shadow:inset 0 0 0 1px var(--ui-edge-on),inset 0 0 16px rgba(60,160,230,.16);
  color:var(--ui-cy);font-family:var(--ui-font);font-size:16px;font-weight:800;
  line-height:34px;text-align:center;user-select:none;cursor:pointer;
  text-shadow:0 0 8px rgba(86,216,255,.5);
  opacity:0;pointer-events:none;
  transition:opacity .42s ease,color .2s,transform .12s}
body.uiHelpOff #uiHelpChip{opacity:1;pointer-events:auto}
#uiHelpChip:hover{color:#fff;transform:translateY(-1px)}

/* ── 5) HUD 톤 통일 ────────────────────────────────────────────────────────── */
#eHud,#bHud,#stHud,#stat,#sword,#bGoal,#bName,#bClear,#combo{font-family:var(--ui-font)}
/* 우상단 수치판(개발용). 평시에는 비어 있으므로 빈 칩이 안 뜨게 접는다 */
#stat{--c:7px;display:inline-block;padding:6px 12px;border:0;
  background:rgba(8,13,24,.86);box-shadow:inset 0 0 0 1px var(--ui-edge);
  color:var(--ui-mute);font-weight:600;letter-spacing:.02em;text-shadow:none}
#stat span{color:var(--ui-dim)}
#stat:empty{display:none}

/* ══ 아래 계기판 = **화면 하단 전폭 가로 띠** ═════════════════════════════════
   ★★오너 지시의 핵심이 여기다. 13차는 폭 37% · 높이 18% 의 **덩어리**라
     화면 한복판 아래에 카드가 하나 떠 있는 그림이었다. 이 벌은 롤·메이플처럼
     **화면 아래 테두리에 붙은 가로 띠** 한 줄이다(높이 8~9%).

     [Lv 3] [♥] [체력 게이지 84/100] [처치 12]   [X][C][Space][잠금][잠금]   [칼 · 녹슨 칼]
     ─────────────────────────── EXP 띠(맨 아래 변) ───────────────────────────

   ★셋으로 나눈 이유는 롤의 정보 위계 그대로다 - 왼쪽이 「나」, 가운데가 「내가 누를 것」,
     오른쪽이 「내가 가진 것」. grid 1fr auto 1fr 이라 슬롯 열은 창 폭과 무관하게
     **화면 정중앙**에 선다(캐릭터가 늘 정중앙에 서므로 눈이 안 흔들린다).
   ★판은 아래로 갈수록 짙어지는 그러데이션이다. 위 가장자리가 흐리게 끝나야
     「띠가 얹혀 있다」가 아니라 「화면이 여기서 끝난다」로 읽힌다.
   ★clip-path 를 안 건다(전폭이라 자를 모서리가 없다). filter 도 안 건다 - 늘 떠 있는
     조각이라 상태가 바뀔 때마다 다시 그리는 비용을 지불할 이유가 없다. */
/* ★★17차 비평 1: 「입장·사망 카드는 8점인데 상시 계기판은 4점(웹 대시보드
     프로그레스바)이다. 언어가 두 개다.」 처방은 **새 컨셉을 만들지 말고 카드의 언어를
     계기판 규범으로 승격**하는 것. 카드가 가진 문법은 넷이고, 그 넷을 여기로 옮긴다.
       ① 스캔라인(1px/4px 푸른 결)   ② 모서리 해시 마크(길이가 다른 짧은 선 셋)
       ③ 마름모 구분자              ④ 어두운 유리판 + 컷코너 캡슐
     ★색은 안 늘린다. 시안=시스템 · 앰버=성장 · 초록/노랑/빨강=체력 그대로다. */
#uiDock{position:fixed;left:0;right:0;bottom:0;z-index:6;
  display:grid;grid-template-columns:1fr auto 1fr;align-items:center;
  gap:clamp(10px,2vw,30px);
  padding:9px clamp(12px,2.4vw,32px) 12px;
  pointer-events:none;user-select:none;
  font-family:var(--ui-font);font-variant-numeric:tabular-nums;
  background:
    repeating-linear-gradient(0deg,rgba(120,190,255,.030) 0 1px,rgba(0,0,0,0) 1px 4px),
    linear-gradient(180deg,rgba(4,8,16,0) 0%,rgba(5,9,18,.62) 22%,
             rgba(4,7,15,.90) 62%,rgba(3,5,12,.96) 100%);
  transition:opacity .5s ease}
/* 위 가장자리 실선. 가운데가 밝고 양끝이 사라진다(롤 HUD 의 금색 장식선 자리) */
#uiDock::before{content:'';position:absolute;left:0;right:0;top:0;height:1px;
  pointer-events:none;
  background:linear-gradient(90deg,rgba(86,216,255,0) 0%,rgba(86,216,255,.42) 26%,
             rgba(140,232,255,.72) 50%,rgba(86,216,255,.42) 74%,rgba(86,216,255,0) 100%)}
/* 모서리 해시 마크. 카드(.hd .ic)가 쓰는 그 서명을 계기판 양 끝에도 새긴다.
   ★좌우 **여백 안**에 선다(내용은 padding 뒤에서 시작하므로 글자와 안 겹친다).
     여백이 좁아지는 1000px 밑에서는 이 겹을 끈다(겹치느니 없는 게 낫다). */
#uiDock::after{content:'';position:absolute;left:7px;right:7px;top:7px;height:9px;
  pointer-events:none;opacity:.5;
  background:
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 0 0 / 14px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 0 4px / 9px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 0 8px / 4px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 100% 0 / 14px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 100% 4px / 9px 1px,
    linear-gradient(90deg,var(--ui-cy),var(--ui-cy)) no-repeat 100% 8px / 4px 1px}
#uiDock .dkRow{display:flex;align-items:center;white-space:nowrap;min-width:0}
#uiDock .dkRow *{white-space:nowrap}
/* 왼쪽 = 나 */
#uiDock .dkLeft{gap:10px}
/* 가운데 = 누를 것 */
#uiDock .dkMid{justify-content:center}
/* 오른쪽 = 가진 것 */
#uiDock .dkRight{justify-content:flex-end}

/* 레벨 뱃지. 메이플의 「LV.」 자리이자 롤의 초상 옆 레벨 원이다.
   ★머리 위 뱃지와 **같은 수**다. 새 정보가 아니라 같은 값을 두 자리에서 읽는 것뿐. */
/* ★색이 앰버인 이유: 이 벌의 색 규칙은 **시안=시스템·기술 / 앰버=목표·보상·성장 /
     빨강=위험 / 초록=체력** 넷이다. 레벨과 EXP 는 「성장」이라 앰버 쪽에 속한다
     (SAO 의 선택 행 앰버 #E8A31E · 메이플 EXP 노랑 · 롤 골드가 전부 같은 자리다).
     덤으로 가운데 슬롯 열(시안)과 색이 갈려서 「나」와 「누를 것」이 한눈에 나뉜다. */
#uiDock .dkLv{--c:7px;flex:0 0 auto;width:30px;height:30px;
  display:flex;align-items:center;justify-content:center;
  background:linear-gradient(180deg,rgba(38,28,10,.94),rgba(18,13,4,.96));
  box-shadow:inset 0 0 0 1px var(--ui-gold),inset 0 0 14px rgba(230,160,40,.26);
  color:var(--ui-gold);font-size:14px;font-weight:800;line-height:1;
  text-shadow:0 0 10px rgba(255,187,61,.6)}
/* 「체력」 라벨. ★17차 비평 1: 13차가 낱말 대신 넣은 하트 ♥ 는 **글자 글리프**라
   기계마다 이모지로 떨어진다(카드의 활자 문법에 유일하게 안 맞는 조각이었다).
   오른쪽 「칼」 태그의 라벨과 **같은 문법**으로 되돌린다 - 작은 대문자급 시안 라벨.
   그래야 계기판 좌우가 [라벨 + 값] 한 쌍씩으로 읽힌다. */
#uiDock .dkLb{font-size:10px;font-weight:800;letter-spacing:.16em;line-height:1;
  color:var(--ui-cy);text-shadow:none}
/* #eHud 를 통째로 옮겨 담았다(자리는 줄이 잡으므로 여백은 0) */
#eHud{position:static;display:flex;align-items:center;gap:10px;left:auto;bottom:auto;
  flex:1 1 auto;min-width:0}

/* 체력 게이지 ──────────────────────────────────────────────────────────────
   ★★17차 비평 1 「형광 민트 프로그레스바」. 16차는 enemy.js 가 인라인으로 쓴
     「linear-gradient(90deg,#2ee08a,#7ff0c0)」 위에 saturate(1.14) brightness(1.06) 을
     **더 얹고** 있었다. 가로 방향 밝음→더밝음 그러데이션은 웹 대시보드의 문법이고,
     그 채도는 카드(어두운 유리 + 시안 헤어라인) 옆에서 혼자 딴 화면이 된다.
   ★고치는 방법: 색이 **뜻**이라는 규칙(초록>50% · 노랑>25% · 빨강)은 그대로 두고,
     그 세 뜻을 카드 팔레트의 값으로 다시 칠한다.
       · 트랙 = 카드와 같은 딥 네이비 유리 + 시안 헤어라인
       · 채움 = **세로** 그러데이션(밝은 위 → 짙은 아래. 관이지 막대가 아니다)
       · 채움 끝에 흰 발광 한 줄(SAO 의 「게이지 끝」 문법)
   ★enemy.js 의 인라인 배경을 이겨야 하므로 !important 를 쓴다. 대신 **뜻은 우리가
     같은 문턱(50/25%)으로 다시 계산해서** 클래스로 얹는다(updateHp).
     한쪽만 고치면 두 파일이 다른 색을 번갈아 칠하므로, 여기 문턱을 바꾸면
     enemy.js 의 문턱도 같이 볼 것. */
#eBar{--c:5px;position:relative;flex:1 1 auto;width:auto;min-width:92px;max-width:300px;
  height:20px;border:0;border-radius:0;
  background:linear-gradient(180deg,rgba(9,15,29,.96),rgba(3,6,14,.96));
  box-shadow:inset 0 0 0 1px rgba(150,205,245,.34)}
#eFill{position:relative;filter:none;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.22),inset 0 -1px 0 rgba(0,0,0,.30)}
#eBar.hpHi  #eFill{background:linear-gradient(180deg,#4bd193,#1fa96c 44%,#0d7248)!important}
#eBar.hpMid #eFill{background:linear-gradient(180deg,#eccb55,#c9991f 44%,#7f5a0c)!important}
#eBar.hpLo  #eFill{background:linear-gradient(180deg,#f97f66,#dc4330 44%,#84190f)!important}
/* 채움의 앞머리. 「여기까지 차 있다」를 발광 한 줄이 말한다(둥근 캡 금지 규칙과 짝) */
#eFill::after{content:'';position:absolute;top:0;bottom:0;right:0;width:5px;
  pointer-events:none;
  background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.42))}
/* 임계 눈금 25·50·75% + 위쪽 광택 한 줄.
   ★17차: 25% 만 붉고 나머지는 검었다(한 바 안에 눈금이 두 색). **한 색으로 통일**하고
     세기만 다르게 둔다 - 위험은 채움 색과 숫자 캡슐이 이미 두 번 말한다. */
#eBar::after{content:'';position:absolute;inset:0;pointer-events:none;
  background:
    /* ★카드의 스캔라인을 게이지 위에도 덮는다. 이 한 겹이 「웹 프로그레스바」와
       「홀로 계기」를 가른다 - 채움과 트랙이 같은 결을 쓰게 되기 때문이다. */
    repeating-linear-gradient(0deg,rgba(2,6,14,.16) 0 1px,rgba(0,0,0,0) 1px 3px),
    linear-gradient(180deg,rgba(255,255,255,.26) 0 1px,rgba(255,255,255,0) 1px),
    linear-gradient(0deg,rgba(255,255,255,.20) 0 1px,rgba(255,255,255,0) 1px),
    linear-gradient(180deg,rgba(255,255,255,.20) 2px,rgba(255,255,255,0) 34%),
    linear-gradient(90deg,rgba(0,0,0,0) 0 calc(25% - 1px),rgba(4,9,18,.62) calc(25% - 1px) 25%,rgba(0,0,0,0) 25%),
    linear-gradient(90deg,rgba(0,0,0,0) 0 calc(50% - 1px),rgba(4,9,18,.40) calc(50% - 1px) 50%,rgba(0,0,0,0) 50%),
    linear-gradient(90deg,rgba(0,0,0,0) 0 calc(75% - 1px),rgba(4,9,18,.40) calc(75% - 1px) 75%,rgba(0,0,0,0) 75%)}
/* 수치 캡슐. ★★17차 비평 1: 16차는 이 숫자를 **트랙 안 가운데**에 얹었다.
   만체력(형광 초록)에서 흰 글자가 그 위에 올라타 대비가 무너졌다 -
   흰 글자는 밝은 채움 위에서 읽히지 않는다. 카드가 쓰는 어두운 유리 캡슐로
   **바 밖에** 내보낸다. 컷코너까지 카드와 같은 문법이다. */
#uiHpNum{--c:4px;position:static;flex:0 0 auto;
  clip-path:polygon(4px 0,calc(100% - 4px) 0,100% 4px,100% calc(100% - 4px),
                    calc(100% - 4px) 100%,4px 100%,0 calc(100% - 4px),0 4px);
  padding:4px 9px 5px;line-height:1;
  background:linear-gradient(180deg,rgba(11,18,33,.94),rgba(5,9,18,.96));
  box-shadow:inset 0 0 0 1px rgba(150,205,245,.30);
  font-size:12.5px;font-weight:800;letter-spacing:.01em;color:#eaf6ff;
  font-variant-numeric:tabular-nums;text-shadow:none}
#uiHpNum s,#uiHpNum u{text-decoration:none;color:var(--ui-mute);font-weight:700;font-size:11px}
#uiHpNum s{margin:0 1px}
/* 25% 밑으로 떨어지면 캡슐째로 붉힌다. 채움 색과 같은 뜻을 두 번 말해 준다 */
#uiHpNum.low{color:#ffd9d1;
  background:linear-gradient(180deg,rgba(38,12,10,.94),rgba(20,6,5,.96));
  box-shadow:inset 0 0 0 1px rgba(255,110,88,.62),inset 0 0 14px rgba(190,50,36,.28)}
/* 처치 수. 게이지 오른쪽에 **마름모 구분자** 하나 두고 붙인다(카드의 그 표식) */
#eTxt{position:relative;flex:0 0 auto;margin:0;padding-left:18px;
  color:var(--ui-dim);font-size:12px;font-weight:700;letter-spacing:.02em;white-space:nowrap}
#eTxt::before{content:'';position:absolute;left:3px;top:50%;width:5px;height:5px;
  margin:-2.5px 0 0;transform:rotate(45deg);background:var(--ui-cy-dim);
  box-shadow:0 0 6px rgba(86,216,255,.35)}
#eTxt b{color:var(--ui-txt)}

/* ── 성장 띠 (메이플 EXP 자리) ───────────────────────────────────────────────
   처치 5 마다 레벨 뱃지가 한 단 오르는데, 그 사이가 화면 어디에도 없어서 뱃지가
   갑자기 바뀌는 것처럼 보였다. 그 진행도를 계기판 **맨 아래 변**에 편 것뿐이다.
   ★글자는 안 붙인다(새 정보가 아니다). ★전폭이라 메이플의 그 자리와 같아진다.

   ★★17차 비평 5 「최하단 앰버 바가 잘려 보인다(렌더 버그로 읽힌다)」. 원인 둘.
     (가) 화면 **밑변에 딱 붙어** 있었다(bottom:0). 3px 짜리 띠가 창 끝에 걸리면
          그 자체가 잘린 조각으로 보인다.
     (나) 빈 트랙이 알파 .10 이라 사실상 안 보였다. 그래서 60% 찬 띠가
          「화면 한복판에서 끊긴 막대」로 읽혔다 - 끝이 있는 게이지가 아니라 버그다.
     고침: 판 안쪽으로 5px 들이고(밑변에서 떨어뜨리고), 좌우도 계기판 여백에 맞춰
     들이고, **빈 트랙을 보이게** 깐다. 그러면 「여기까지 찼다」가 처음으로 읽힌다. */
#uiDock .dkExp{position:absolute;left:clamp(12px,2.4vw,32px);right:clamp(12px,2.4vw,32px);
  bottom:5px;height:4px;display:block;border:0;border-radius:0;overflow:hidden;
  background:rgba(11,17,31,.94);
  box-shadow:inset 0 0 0 1px rgba(255,200,110,.28)}
#uiDock .dkExp i{position:absolute;left:0;top:0;bottom:0;right:0;display:block;
  transform:scaleX(0);transform-origin:0 50%;border-radius:0;
  background:linear-gradient(90deg,#a06a12,var(--ui-gold));
  box-shadow:0 0 10px rgba(255,187,61,.6);
  transition:transform .3s cubic-bezier(.22,.8,.3,1)}

/* 칼 태그. 슬롯 열 오른쪽 끝(롤이 스킬 옆에 장비를 두는 자리).
   ★display 는 안 건드린다. 칼이 없는 몸(궁수)에서 main.js 가 none 을 넣고,
     그때는 JS 가 태그째로 접는다. */
#uiDock .dkSword{--c:7px;display:inline-flex;align-items:center;gap:8px;
  padding:6px 14px 7px;border:0;
  background:linear-gradient(180deg,rgba(12,20,35,.90),rgba(7,12,23,.94));
  box-shadow:inset 0 0 0 1px var(--ui-edge)}
#uiDock .dkSword .lb{font-size:10px;font-weight:800;letter-spacing:.16em;color:var(--ui-cy)}
#sword{position:static;right:auto;bottom:auto;opacity:1!important;
  font-size:13px;font-weight:800;letter-spacing:.01em;color:var(--ui-txt);text-shadow:none}

/* 은신 알림은 계기판 위로 물러난다.
   ★★계기판 높이가 바뀌면 이 값도 같이 바꿔야 한다(13차·14차가 두 번 밟은 함정).
     지금 계기판은 76px 이고 여유 12px 이라 88px 이다. */
#stHud{--c:8px;bottom:88px;border:0;border-radius:0;
  letter-spacing:.08em;font-weight:800;font-size:12.5px;padding:7px 17px 8px;text-shadow:none}
/* 은신 줄. 초록/주황이 무슨 뜻인지는 그대로 두고 판만 이 벌의 유리로 내린다. */
#stHud.hide{color:#c8ffe4;background:linear-gradient(180deg,rgba(8,32,24,.92),rgba(4,18,14,.94));
  box-shadow:inset 0 0 0 1px var(--rb-ok),inset 0 0 18px rgba(40,200,130,.20)}
#stHud.loud{color:#ffe2bb;background:linear-gradient(180deg,rgba(40,24,8,.92),rgba(22,13,4,.94));
  box-shadow:inset 0 0 0 1px var(--ui-gold),inset 0 0 18px rgba(230,160,40,.20)}
/* 은신 비네트. stealth.js 것을 여기서 덮는다(이 style 이 나중에 붙어 이긴다). */
#stVig{box-shadow:inset 0 0 190px 62px rgba(2,8,7,.72),
                  inset 0 0 70px 8px rgba(24,120,70,.30)}
#stVig.loud{box-shadow:inset 0 0 190px 62px rgba(10,5,0,.74),
                       inset 0 0 70px 8px rgba(150,96,16,.34)}
/* 콤보 숫자(평타 「1타」). ★transform 은 main.js 가 inline 으로 쓴다(여기서 절대 잡지 말 것) */
#combo{font-weight:800;color:#eaf6ff;letter-spacing:.02em;
  font-variant-numeric:tabular-nums;
  text-shadow:0 0 18px rgba(86,216,255,.55),0 2px 6px rgba(0,0,0,.7)}
/* 누적 명중 수. 한 번에 여럿을 벤 그 사실만 조용히 알리는 자리라 크기를 확 낮춘다 */
#combo i{font-style:normal;font-weight:700;
  font-size:.32em;letter-spacing:.04em;color:var(--ui-dim);margin-left:.55em;
  vertical-align:middle;text-shadow:none}

/* ── 6) 결과창 (층 돌파) ─────────────────────────────────────────────────────
   boss.js·level2.js 가 만든 DOM(#bClear h1/table/.hint)은 그대로 두고 CSS 만 덮는다.
   ★transform 을 덮을 때 translate(-50%,-50%) 를 **반드시 같이 적는다.** 남의 파일이
     그걸로 화면 가운데를 잡고 있어서, scale 만 쓰면 패널이 오른쪽 아래로 밀려난다.
   ★그래서 이 판만 등장 애니에 sysWin 을 못 쓴다. 대신 opacity + 미세 scale 로 같은
     인상을 낸다(가운데잡기가 transform 에 묶여 있는 판의 숙명이다).
   ★가상요소 둘 중 ::after 는 창 이름(「결과」)이고 ::before 는 위쪽 시안 표식이다
     (13차의 원 뱃지는 이 벌에 없다 - 유리창에는 스티커가 안 붙는다). */
/* ★결과창만 **앰버**다. 이 벌의 색 규칙에서 앰버는 「목표·보상」이고, 층 돌파는
     이 게임에서 유일한 보상의 순간이다. 나머지 창(입장·경고·사망)과 색으로 갈라 두면
     화면을 처음 보는 사람도 「이건 좋은 소식」이라는 것을 글자보다 먼저 안다. */
#bClear{padding:0;min-width:min(500px,88vw);
  box-shadow:inset 0 0 0 1.5px rgba(255,187,61,.72),inset 0 0 46px rgba(190,130,20,.14);
  filter:drop-shadow(0 0 16px rgba(255,187,61,.26)) drop-shadow(0 10px 26px rgba(0,0,0,.62));
  transition:opacity .45s ease,transform .45s cubic-bezier(.2,.9,.25,1);
  transform:translate(-50%,-50%) scale(.972)}
#bClear.uiIn{transform:translate(-50%,-50%) scale(1)}
#bClear::before{content:'';position:absolute;left:0;right:0;top:0;height:34px;
  pointer-events:none;
  background:
    linear-gradient(90deg,rgba(255,187,61,0),var(--ui-gold) 22%,var(--ui-gold) 78%,rgba(255,187,61,0))
      no-repeat 50% 0 / 152px 3px,
    linear-gradient(90deg,rgba(255,187,61,0),rgba(255,205,120,.44) 30%,
      rgba(255,205,120,.44) 70%,rgba(255,187,61,0)) no-repeat 50% 33px / 100% 1px}
#bClear::after{content:'${CLEAR_HEAD}';color:var(--ui-gold);
  text-shadow:0 0 10px rgba(255,187,61,.55)}
#bClear h1{font-size:38px;font-weight:800;letter-spacing:.04em;
  color:#fff6e2;margin:0;padding:74px 34px 0;line-height:1.14;
  text-shadow:0 0 26px rgba(255,187,61,.5)}
/* 표. 칸 여백을 없애고 줄마다 얇은 실선을 깐다 - 라벨은 왼쪽, 값은 오른쪽 끝.
   값은 금색이다(컨셉 cards.png 그대로. 보상은 금색이라는 규칙과 같다). */
#bClear table{width:auto;min-width:min(330px,76vw);margin:24px 34px 0;
  font-size:12.5px;color:var(--ui-mute);border-spacing:0}
#bClear td{padding:10px 0;border-bottom:1px solid rgba(255,205,120,.14);
  font-weight:700;letter-spacing:.04em;text-align:left;white-space:nowrap}
#bClear tr:last-child td{border-bottom:none}
#bClear td.v{color:var(--ui-gold);font-weight:800;font-size:15px;
  text-align:right;padding-left:34px;font-variant-numeric:tabular-nums;
  text-shadow:0 0 12px rgba(255,187,61,.35)}
#bClear .hint{margin:18px 34px 24px;font-size:11.5px;font-weight:700;
  letter-spacing:.04em;color:var(--ui-dim)}
#bClear.uiIn h1{animation:sysUp .5s ease-out .06s both}
/* 결과창이 뜨면 상단 목표 태그를 접는다.
   ★판정 S9: 태그도 「층 돌파」, 창 제목도 「층 돌파」. 답을 말한 쪽만 남긴다. */
body.uiCleared #bHud{opacity:0;transition:opacity .45s ease}

/* ── 클리어 암막 ─────────────────────────────────────────────────────────────
   v72 QA #15: 패널이 뜬 채로 계속 걸어다닐 수 있었다. 입력은 main.js 가 잠그고,
   여기서는 「판이 끝났다」를 눈으로 못박는다. 패널(z 8)보다 아래, HUD(z 6)보다 위. */
#uiClearDim{position:fixed;inset:0;z-index:7;pointer-events:none;opacity:0;
  transition:opacity .7s ease;
  background:radial-gradient(ellipse at 50% 50%,rgba(4,10,20,.34) 0%,rgba(0,2,6,.72) 84%)}
body.uiCleared #uiClearDim{opacity:1}

/* ══ 7) 스킬 슬롯 (X 수면참 · C 횡일섬 · Space 회피 + 잠긴 칸 둘) ══════════════
   롤 문법 그대로다 - **정사각에 가까운 칸**, 칸 하나가 기술 하나.
   컨셉(parts.png)의 슬롯 구조를 그대로 옮겼다. 위에서 아래로 세 층이다.
     [키캡]      슬롯 **안** 위 가운데. ★13차는 슬롯 밖 아래에 걸려 있어서
                 계기판 높이를 15px 더 먹었다. 안으로 들이면 띠가 그만큼 낮아진다
     [획]        기술을 말하는 획(세로 호 · 가로 호 · 속도선). 시안
     [이름]      슬롯 안 아래
   ★자리 순서는 **CSS order** 가 정한다. 회피 슬롯은 main.js(mountDashChip)가 나중에
     붙기 때문에 DOM 순서로는 잠긴 칸 뒤에 선다. order 로 잡아 두면 누가 언제 붙어도
     열이 안 흐트러진다.
   ★★clip-path 를 걸었으므로 슬롯 **밖으로 나가는 조각을 두면 잘린다.** 키캡을 안으로
     들인 것이 그 때문이기도 하다. 새 조각을 붙일 때 이 규칙을 먼저 볼 것. */
#uiDock .dkSlots{align-items:center;justify-content:center;gap:14px}
#uiSkills{position:static;left:auto;bottom:auto;transform:none;
  display:flex;gap:7px;align-items:center;pointer-events:none;user-select:none;
  font-family:var(--ui-font);transition:opacity .5s ease}
/* ★★17차 비평 2 「신규 유저가 **공격 키를 몰라 두 번 죽었다**」. 16차 계기판에는
     X·C·Space 만 있었다 - 정작 이 게임의 기본기인 **Z 베기**가 화면 어디에도 없었다
     (도움말 판에만 있고 그 판은 8초 뒤 접힌다). 같은 타일 문법으로 맨 왼쪽에 세운다.
     ★자리 순서는 배우는 순서다 - 베기 → 수면참 → 횡일섬 → 회피 → 잠긴 칸. */
#uiSkills .sk[data-k="Basic"]{order:0}
#uiSkills .sk[data-k="Heavy"]{order:1}
#uiSkills .sk[data-k="Wide"]{order:2}
#uiSkills .sk[data-k="Dash"]{order:3}
#uiSkills .skLock{order:4}
/* 칸 한 벌 */
#uiSkills .sk,#uiSkills .skLock{
  --c:8px;--sk-accent:var(--ui-cy);
  position:relative;width:66px;height:58px;padding:0;border:0;border-radius:0;
  background:linear-gradient(180deg,rgba(14,23,40,.88),rgba(7,12,23,.93));
  box-shadow:inset 0 0 0 1px var(--ui-edge);
  overflow:visible;display:block;
  transition:background .16s ease,box-shadow .16s ease,filter .16s ease}
/* ★17차 비평 6: 회피 칸만 84px 이라 열의 박자가 어긋났다. 넓었던 이유는 「이동+」
   라는 조건 글자를 캡 옆에 세웠기 때문인데, 그 조건은 도움말 판이 이미 한 줄로
   말한다(「이동+ Space · 회피」). **칸 폭을 통일하고 조건 글자는 뺀다.** */
#uiSkills .skLock{width:34px}

/* 키캡. 슬롯 **안** 위 가운데. 컷코너 작은 판 */
/* ★★z-index 5. 쿨다운 덮개(.cd)가 z 4 라 그 밑에 두면 **쿨이 도는 동안 키가 통째로
     사라진다**(첫 촬영에서 X·C 가 안 보였다). 롤도 덮개 위에 키를 남긴다 - 무엇을
     누를 칸인지는 쿨과 무관한 사실이기 때문이다. */
#uiSkills .sk .key{position:absolute;left:50%;top:4px;transform:translateX(-50%);z-index:5;
  --c:3px;min-width:22px;height:15px;line-height:13px;padding:0 6px;
  border:0;border-radius:0;background:rgba(20,32,54,.95);
  box-shadow:inset 0 0 0 1px rgba(160,210,255,.46);
  color:var(--ui-txt);font-size:10.5px;font-weight:800;text-align:center;
  transition:color .16s ease,box-shadow .16s ease,background .16s ease}
/* 기술 획. 키캡 밑, 이름 위.
   ★★획은 기술마다 **따로** 만든다. 하나의 원을 돌려 쓰려다 한 판을 날렸다 -
     원에 큰 회전을 걸면 색칠된 호가 상자 밖으로 나간다. 회전을 20도 밑으로 묶고,
     형태는 border-radius 로 만든다.
   ★★17차 비평 6 「글리프-라벨 겹침(횡일섬·회피)」. 실측하면 수면참·횡일섬 획이
     이름 상자를 **4.2px 물고** 있었고 회피는 1px 차로 스쳤다(발광까지 세면 닿는다).
     칸 높이는 그대로 두고 **띠를 셋으로 나눈다** - 키캡 4~19 · 획 20~36 · 이름 40~53.
     아래 값은 전부 그 표에서 나왔다. 획을 키우려면 이름 위끝(40)을 먼저 볼 것. */
#uiSkills .sk::after{content:'';position:absolute;left:50%;z-index:1;
  border:0;border-radius:0;background:none;
  filter:drop-shadow(0 0 4px rgba(86,216,255,.55));
  transition:opacity .16s ease}
/* 베기 = 짧은 호 **둘**. 「연속으로 3연타」라는 사실을 형태가 먼저 말한다.
   ★두 겹이라 ::before 까지 쓴다(회피 칸의 「이동+」가 빠지면서 비었다). */
#uiSkills .sk[data-k="Basic"]::before{content:'';position:absolute;left:50%;z-index:1;
  top:23px;width:10px;height:11px;margin-left:-13px;
  border-right:3px solid var(--sk-accent);
  border-radius:0 100% 100% 0/0 50% 50% 0;
  transform:rotate(-14deg);opacity:.5;
  filter:drop-shadow(0 0 3px rgba(86,216,255,.45));
  transition:opacity .16s ease}
#uiSkills .sk[data-k="Basic"]::after{
  top:20px;width:13px;height:16px;margin-left:-3px;
  border-right:4px solid var(--sk-accent);
  border-radius:0 100% 100% 0/0 50% 50% 0;
  transform:rotate(-14deg)}
/* 수면참 = 세로로 크게 한 번. 오른쪽으로 부푼 긴 호 */
#uiSkills .sk[data-k="Heavy"]::after{
  top:20px;width:15px;height:16px;margin-left:-8px;
  border-right:4px solid var(--sk-accent);
  border-radius:0 100% 100% 0/0 50% 50% 0;
  transform:rotate(-15deg)}
/* 횡일섬 = 가로로 넓게. 납작한 사발 */
#uiSkills .sk[data-k="Wide"]::after{
  top:22px;width:30px;height:10px;margin-left:-15px;
  border-bottom:4px solid var(--sk-accent);
  border-radius:0 0 100% 100%/0 0 100% 100%;
  transform:rotate(-4deg)}
/* 회피 = 획이 아니라 **속도선** 셋. 베는 기술이 아니라는 것을 형태가 먼저 말한다 */
#uiSkills .sk[data-k="Dash"]::after{
  top:27px;width:26px;height:0;margin-left:-13px;
  border-top:3px solid var(--sk-accent);
  box-shadow:0 6px 0 0 var(--sk-accent),0 -6px 0 0 var(--sk-accent);
  transform:skewX(-20deg) scaleX(.86)}
/* 이름. 슬롯 안 아래.
   ★★line-height 를 못박는다. normal 로 두면 글자 상자 높이가 서체마다 달라져서
     「획과 안 겹친다」를 분기마다 계산할 수가 없다(13차 QA 가 5px 물림으로 두 번 걸렸다).
     지금 규칙: 획의 아래끝 < 이름의 위끝. 네 분기 다 이 부등식으로 값을 잡았다. */
#uiSkills .sk .nm{position:absolute;left:2px;right:2px;bottom:5px;z-index:5;margin:0;
  text-align:center;font-size:11px;line-height:1.15;font-weight:800;letter-spacing:-.01em;
  color:var(--ui-txt);text-shadow:0 1px 3px rgba(0,0,0,.7)}
/* 준비 - 시안 테 + 은은한 발광. ★drop-shadow 는 clip-path 실루엣을 따라간다 */
#uiSkills .sk.rdy{
  background:linear-gradient(180deg,rgba(20,38,64,.90),rgba(9,17,32,.94));
  box-shadow:inset 0 0 0 1px var(--ui-edge-on),inset 0 0 20px rgba(60,170,235,.22);
  filter:drop-shadow(0 0 6px rgba(86,216,255,.34))}
#uiSkills .sk.rdy .nm{color:#eefaff}
/* 불가(쿨 · 휘두르는 중). 면을 내리고 획·이름·키캡을 같이 물린다 */
#uiSkills .sk.off{
  background:linear-gradient(180deg,rgba(9,14,25,.92),rgba(5,9,17,.94));
  box-shadow:inset 0 0 0 1px rgba(150,190,225,.16);filter:none}
/* ★덮개 위에 남지만 **한 단 어둡게**. 완전히 죽이면 쿨 도는 칸이 빈 상자가 된다
   (첫 촬영에서 이름이 안 읽혔다. .34 -> .62). */
#uiSkills .sk.off .nm{color:rgba(200,222,244,.62);text-shadow:0 1px 3px rgba(0,0,0,.8)}
#uiSkills .sk.off::after{opacity:.26;filter:none}
#uiSkills .sk.off .key{color:rgba(210,232,252,.38);background:rgba(10,16,28,.9);
  box-shadow:inset 0 0 0 1px rgba(150,190,225,.24)}
#uiSkills .sk.off[data-k="Basic"]::before{opacity:.14;filter:none}
/* 쿨다운 덮개. JS 가 conic-gradient 를 20Hz 로 다시 쓴다(페인트만 도는 일이다).
   ★슬롯이 clip-path 로 잘리므로 여기서는 모서리를 안 잡아도 된다. */
#uiSkills .sk .cd{position:absolute;inset:0;border-radius:0;z-index:4;
  opacity:0;pointer-events:none;transition:opacity .1s ease}
#uiSkills .sk.off .cd{opacity:1}
/* 남은 초. 롤 문법 - 덮개 한가운데 큰 숫자 하나 */
#uiSkills .sk .cds{position:absolute;left:0;right:0;top:50%;z-index:6;
  margin-top:-12px;height:24px;line-height:24px;text-align:center;pointer-events:none;
  font-family:var(--ui-font);font-size:20px;font-weight:800;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums;color:#dff6ff;
  text-shadow:0 0 10px rgba(86,216,255,.7),0 2px 4px rgba(0,0,0,.85)}
#uiSkills .sk .cds:empty{display:none}
#uiSkills .sk.gone{display:none}
/* 잠긴 칸. 「여기 더 붙는다」만 말하고 그 이상은 안 말한다(문구도 안 붙인다).
   ★★17차 비평 3: 「잠긴 칸 둘이 **화면 정중앙 최고의 자리**에서 자물쇠만 주장한다.」
     맞다 - 없는 기술이 있는 기술과 같은 크기·같은 대비로 서 있었다(52px · 자물쇠 .34).
     칸은 남기되 **실루엣**으로 내린다: 폭 34px · 면은 거의 안 보이게 · 자물쇠는
     형태만 남는 세기(.14). 「자리가 있다」는 말은 그 정도면 충분하다. */
#uiSkills .skLock{background:rgba(6,10,19,.34);
  box-shadow:inset 0 0 0 1px rgba(150,190,225,.07)}
#uiSkills .skLock .lk{position:absolute;left:50%;top:50%;width:11px;height:9px;
  margin:-1px 0 0 -5.5px;border-radius:2px;background:rgba(140,175,210,.14)}
#uiSkills .skLock .lk::before{content:'';position:absolute;left:50%;bottom:100%;
  width:8px;height:6px;margin-left:-4px;
  border:2px solid rgba(140,175,210,.14);border-bottom:0;border-radius:5px 5px 0 0}

/* ── 8) 목표 방향 나침반 ─────────────────────────────────────────────────────
   3차 QA: **블라인드 18분간 보스를 육안으로 한 번도 못 봤다.** 그래서 셋을 바꿨다.
     (가) 판 + 한 글자(鬼 · 符 · 門). 무엇을 가리키는지 화살표 자신이 말한다
     (나) 크기 2배(화살 28x20 + 46px 판)
     (다) 은은한 명멸. 정지한 그림은 밝은 배경에서 지형으로 읽힌다
   ★글리프와 크기는 한 점도 안 바꿨다(정보로서 잘 작동해 온 자산이다).
     판만 이 벌의 유리로 갈아입힌다. 단계 색도 뜻을 그대로 지킨다. */
#uiNav{position:fixed;left:50%;top:50%;z-index:6;pointer-events:none;user-select:none;
  transform:translate(-50%,-50%);opacity:0;width:0;height:0;
  transition:opacity .35s ease,left .12s linear,top .12s linear;
  --nav-ink:#8fe6ff;--nav-glow:rgba(86,216,255,.55)}
/* 화살은 판 **둘레를 돈다.** .dial 만 돌리고 글자는 안 돌린다(뒤집힌 鬼 는 못 읽는다) */
#uiNav .dial{position:absolute;left:0;top:0;width:0;height:0;
  transition:transform .1s linear}
/* ★길쭉해야 한다. 28x20 이라야 비스듬히 돌아가도 뾰족한 끝이 읽힌다.
   ★밑변까지의 거리 38px 은 판 반지름 23 + 테에서 나왔다. */
#uiNav .tip{position:absolute;left:0;top:0;width:0;height:0;
  transform:translate(38px,-10px);
  border-left:28px solid var(--nav-ink);
  border-top:10px solid transparent;border-bottom:10px solid transparent;
  filter:drop-shadow(0 0 6px var(--nav-glow)) drop-shadow(0 2px 3px rgba(0,0,0,.6))}
/* 판 + 한 글자 */
#uiNav .plate{--c:12px;position:absolute;left:50%;top:50%;
  width:46px;height:46px;margin:-23px 0 0 -23px;border:0;border-radius:0;
  background:linear-gradient(180deg,rgba(12,22,40,.92),rgba(6,11,22,.95));
  box-shadow:inset 0 0 0 1px var(--nav-ink),inset 0 0 16px rgba(60,170,235,.20);
  display:flex;align-items:center;justify-content:center;
  font-family:var(--ui-font);font-weight:800;font-size:23px;line-height:1;
  color:var(--nav-ink);text-shadow:0 0 12px var(--nav-glow)}
/* 한자 첫 등장 라벨. ★단계마다 딱 한 번, 2.6초만 붙었다 사라진다(판정 S8) */
#uiNav .cap,#uiPip .cap{--c:5px;position:absolute;left:50%;
  transform:translate(-50%,0);padding:3px 10px 4px;white-space:nowrap;
  border:0;border-radius:0;background:rgba(6,11,22,.94);
  box-shadow:inset 0 0 0 1px var(--ui-edge);
  font-family:var(--ui-font);font-size:11px;font-weight:700;letter-spacing:.04em;
  color:var(--ui-txt);text-shadow:none;
  opacity:0;transition:opacity .35s ease}
#uiNav .cap{top:50%;margin-top:28px}
#uiNav .cap.on,#uiPip .cap.on{opacity:1}
/* 남은 거리(m). ★17차 신규유저 비평 ④ "마커가 거리 정보 없이 가장자리에 고정이라
   전진 중인지 막힌 건지 판별이 안 된다." 방향만으로는 **가고 있는지**를 못 읽는다.
   숫자가 줄어드는 것만으로 충분하므로 판 하나 · 글자 하나로 끝낸다.
   ★첫 등장 라벨(.cap)과 **같은 자리**를 쓴다. 겹치는 2.6초 동안은 라벨이 이긴다.
   ★카드 문법 그대로다 - 남색 판 + 1px 창백 헤어라인 + 컷코너(--c 5px).
     테는 획 색이 아니라 --ui-edge 다. 획 색으로 두르면 판이 하나 더 생겨서
     "무엇이 목표인가"를 말하는 글자 판과 세기가 같아진다.
   ★숫자는 tabular-nums. 안 그러면 12 -> 11 에서 판 폭이 흔들려 깜빡이는 걸로 읽힌다. */
#uiNav .dst{--c:5px;position:absolute;left:50%;top:50%;margin-top:28px;
  transform:translate(-50%,0);padding:2px 8px 3px;white-space:nowrap;
  border:0;border-radius:0;background:rgba(6,11,22,.94);
  box-shadow:inset 0 0 0 1px var(--ui-edge);
  font-family:var(--ui-font);font-size:11px;font-weight:800;letter-spacing:.02em;
  font-variant-numeric:tabular-nums;color:var(--nav-ink);text-shadow:none;
  opacity:0;transition:opacity .3s ease}
#uiNav .dst.on{opacity:.92}
/* 명멸. 판이 2.2초에 한 번 은은하게 숨을 쉰다.
   ★★예전에는 **box-shadow 자체를 키프레임으로 흔들었다.** box-shadow 는 합성이 아니라
     페인트라, 나침반이 떠 있는 내내 매 프레임 판을 다시 그린다.
     A/B 실측(2026-08-11, 왕복 3회 교대): 이 애니 하나를 끄면 37.2 -> 41.8fps.
     고치는 법: 발광을 **따로 깔아 두고 그 겹의 opacity 만** 흔든다(진짜 합성 경로).
   ★::after 는 position:absolute 라 flex 줄에 안 낀다(.plate 는 flex 통이다).
   ★.plate 가 clip-path 로 잘리므로 이 겹도 **판 안에서** 빛난다(inset 발광). */
#uiNav .plate::after{content:'';position:absolute;inset:0;
  pointer-events:none;box-shadow:inset 0 0 18px 2px var(--nav-glow);opacity:0;
  animation:uiNavPulse 2.2s ease-in-out infinite}
@keyframes uiNavPulse{0%,100%{opacity:0}50%{opacity:1}}

/* ── 9) 가까운 요괴 무리 마커 ────────────────────────────────────────────────
   15m 안에 무리가 있으면 그 방향에 작은 판 하나. 라벨도 명멸도 없다.
   ★보스 화살보다 훨씬 약해야 한다. 둘이 비슷해지면 「어느 쪽이 진짜 목표냐」가 흐려진다. */
#uiPip{--c:5px;position:fixed;left:50%;top:50%;z-index:5;pointer-events:none;user-select:none;
  transform:translate(-50%,-50%);width:20px;height:20px;border:0;border-radius:0;opacity:0;
  display:flex;align-items:center;justify-content:center;
  background:rgba(8,14,26,.90);box-shadow:inset 0 0 0 1px var(--ui-edge);
  transition:opacity .3s ease,left .12s linear,top .12s linear}
/* 판 안의 점. 나침반의 한 글자가 앉는 자리와 같은 자리다 */
#uiPip::after{content:'';width:6px;height:6px;border-radius:50%;
  background:var(--ui-cy);box-shadow:0 0 8px rgba(86,216,255,.7)}
/* ★v93 판정 S11: 점이 무슨 뜻인지 화면 어디에도 없다. **처음 한 번만** 2.6초짜리
   작은 라벨을 달고 그 뒤로는 점으로 돌아간다. */
#uiPip .cap{top:24px}

/* ── 10) 기술 이름 콜아웃 ────────────────────────────────────────────────────
   판정 S14: 「기술이 나갈 때 뜨는 이름이 소박하다.」 그래서 **작은 시스템 판**이다.
     「스킬」 시안 라벨 한 줄 + 이름(크게) + 型 번호(작게)
   ★수명은 안 건드린다. 0.9초는 main.js 의 comboT 가 정하고 그게 맞는 값이다.
   ★크기를 **키우지 않는다**(오너 기조: 이펙트는 절제).
   ★transform 은 main.js 가 인라인으로 쓴다(translateX(-50%) scale). 여기서 절대
     잡지 말 것 - 잡으면 등장 팝이 통째로 죽는다. 자리 잡기는 부모(#combo)가 한다.
   ★크기를 em 이 아니라 px 로 못박는다. 부모 #combo 는 44px 인데 그 배수로 잡으면
     main.js 의 scale 애니와 곱해져서 카드가 출렁인다. */
/* ★17차 비평 8: 이 팝이 화면 위 20% 에 떠서 **목표 배너 · 나침반 마커와 같은 띠**를
   썼다(실측: 팝 189~276, 나침반 판 114~160 - 28px 차로 스친다). 팝은 0.9초짜리라
   비켜 주는 쪽이 팝이어야 한다 - 자리를 한 단 내려 띠를 가른다.
   ★자리(top)만 바꾼다. transform 은 main.js 가 인라인으로 쓰는 칸이라 여전히 안 건드린다. */
#combo{top:25%}
#combo .uiCall{--c:10px;display:inline-flex;flex-direction:column;align-items:center;
  vertical-align:middle;padding:24px 26px 12px;text-align:center;
  border:0;border-radius:0;position:relative;
  background:linear-gradient(180deg,rgba(12,20,36,.90),rgba(6,11,22,.94));
  box-shadow:inset 0 0 0 1px var(--ui-edge-on),inset 0 0 26px rgba(60,160,230,.16);
  filter:drop-shadow(0 0 12px rgba(86,216,255,.28));
  font-family:var(--ui-font)}
#combo .uiCall .hd{position:absolute;left:0;right:0;top:9px;
  font-size:10px;font-weight:800;letter-spacing:.24em;padding-left:.24em;
  color:var(--ui-cy);text-shadow:0 0 8px rgba(86,216,255,.5);-webkit-text-stroke:0}
#combo .uiCall .nm{display:block;font-size:23px;font-weight:800;letter-spacing:.02em;
  color:#eafaff;line-height:1.2;margin-top:0;-webkit-text-stroke:0;
  text-shadow:0 0 18px rgba(120,220,255,.5)}
/* 型 번호. 카드를 설명하는 작은 말이라 한 단 물린다 */
#combo .uiCall .ty{display:block;font-size:10.5px;font-weight:700;letter-spacing:.14em;
  padding-left:.14em;color:var(--ui-dim);margin-top:5px;text-shadow:none;-webkit-text-stroke:0}
/* 누적 명중 수는 판 **밖**에 그대로 남는다(main.js 가 붙이는 <i> 와 같은 자리) */
#combo .uiCall + i{vertical-align:middle}

/* ── 11) 머리 위 체력바 (오너 지시: 「체력바는 캐릭터 머리 위로, 롤처럼」) ──────
   롤 문법 그대로다. 캐릭터 머리 위에 **월드를 따라다니는** 작은 트랙 하나.
   ★아래 계기판의 체력 줄·숫자는 **그대로 둔다.** 롤도 머리 위 바와 하단 HUD 를
     이중으로 쓴다. 하나를 없애면 「지금 몇 남았나」와 「위험한가」 중 하나가 죽는다.
   ★폭은 **화면 px 고정**이다. 휠 줌(18~32m)으로 캐릭터가 커졌다 작아져도 바는 안 변한다.
   ★자리는 JS 가 **transform 으로만** 쓴다. left/top 을 매 프레임 쓰면 레이아웃이 돈다. */
#uiHpFloat{position:fixed;left:0;top:0;z-index:5;width:84px;height:12px;
  pointer-events:none;user-select:none;opacity:0;overflow:visible;
  border:0;border-radius:0;background:transparent;box-shadow:none;
  transition:opacity .18s ease;will-change:transform}
#uiHpFloat.on{opacity:1}
#uiHpFloat i{position:absolute;left:0;top:0;bottom:0;display:block}
#uiHpFloat .track{--c:3px;position:absolute;inset:0;overflow:hidden;border:0;border-radius:0;
  background:rgba(2,5,11,.92);
  box-shadow:inset 0 0 0 1px rgba(214,240,255,.72),0 2px 6px rgba(0,0,0,.6)}
#uiHpFloat .track i{top:0;bottom:0;left:0;border-radius:0}
/* 잔상. 방금 깎여 나간 만큼이 잠깐 남았다가 따라 줄어든다(폭은 JS 가 매 프레임 쓴다).
   ★채움보다 **뒤에** 깔린다(문서 순서). 그래야 줄어든 구간에서만 보인다. */
#uiHpFloat .gh{background:rgba(255,120,92,.60);transition:background .2s ease}
/* 채움. 색(초록/노랑/빨강)은 enemy.js 의 규칙을 그대로 쓴다 - 뜻이 걸린 색이라 안 바꾼다 */
#uiHpFloat .fl{filter:saturate(1.06);transition:filter .2s ease}
/* 레벨 뱃지. 같은 transform 노드 안에서 트랙 왼쪽에 붙는다 */
#uiHpFloat .lv{--c:5px;position:absolute;right:calc(100% - 3px);top:50%;z-index:3;
  width:24px;height:24px;transform:translateY(-50%);
  display:flex;align-items:center;justify-content:center;
  border:0;border-radius:0;background:rgba(24,17,6,.94);
  box-shadow:inset 0 0 0 1px var(--ui-gold),inset 0 0 10px rgba(230,160,40,.30);
  color:var(--ui-gold);font-family:var(--ui-font);
  font-size:11.5px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;
  text-shadow:0 0 8px rgba(255,187,61,.6)}
/* 맞은 순간. ★번쩍이는 것은 **방금 깎여 나간 칸**(잔상)이다. 남은 체력을 하얗게
   태우면 그 순간 색(초록/노랑/빨강)이 사라져서 「얼마나 위험한가」를 못 읽는다.
   ★남은 쪽 밝기는 1.2 를 넘기지 않는다. 1.45 로 두니 옅은 쪽 끝이 흰색으로 타서
     초록 바가 통째로 청백색으로 읽혔다(f08 실측 (191,255,255)). 색이 곧 뜻이다. */
#uiHpFloat.hit .track{box-shadow:inset 0 0 0 1.5px #fff,0 2px 6px rgba(0,0,0,.6)}
#uiHpFloat.hit .fl{filter:saturate(1.06) brightness(1.2);transition:none}
#uiHpFloat.hit .gh{background:rgba(255,247,240,.95);transition:none}

/* ── 12) 좁은 창 (판정 S2) ───────────────────────────────────────────────────
   ★13차와 같은 두 분기를 그대로 쓴다(새 벽을 만들지 않는다). 깎는 순서도 같다 -
     여백 -> 슬롯 크기 -> 글자. 슬롯이 줄면 키캡·획·이름·초 숫자를 **같이** 줄인다
     (13차 QA 가 밟은 함정: 칩만 줄이고 장식은 안 줄여서 획이 이름을 5px 물었다).
   ★계기판이 전폭이라 「좌우가 잘린다」는 문제 자체가 사라졌다. 이 분기들이 하는 일은
     **가운데 슬롯 열과 좌우 그룹이 서로 밀지 않게** 하는 것뿐이다. */
@media (max-width:1180px){
  #uiDock{gap:14px}
  #eBar{max-width:230px}
  #uiDock .dkSlots{gap:11px}
}
@media (max-width:1000px){
  #uiDock{padding:8px 12px 11px;gap:11px}
  /* 여백이 12px 이라 해시 마크(14px)가 내용과 겹친다. 겹치느니 없는 게 낫다 */
  #uiDock::after{display:none}
  #uiDock .dkExp{left:12px;right:12px}
  #uiDock .dkLeft{gap:8px}
  #uiDock .dkLv{width:27px;height:27px;font-size:13px}
  #uiDock .dkLb{font-size:9.5px;letter-spacing:.12em}
  #eBar{height:18px;min-width:84px;max-width:190px}
  #uiHpNum{font-size:11.5px;padding:3px 7px 4px}
  #eTxt{padding-left:15px;font-size:11.5px}
  #uiSkills{gap:6px}
  #uiSkills .sk,#uiSkills .skLock{width:58px;height:52px}
  #uiSkills .skLock{width:30px}
  /* 띠 표: 키캡 4~19 · 획 20~33 · 이름 34.9~ */
  #uiSkills .sk .key{top:4px;min-width:20px;height:15px;line-height:13px;font-size:10px;padding:0 5px}
  #uiSkills .sk[data-k="Basic"]::before{top:22px;width:9px;height:9px;margin-left:-11px;border-right-width:3px}
  #uiSkills .sk[data-k="Basic"]::after{top:20px;width:11px;height:13px;margin-left:-3px;border-right-width:4px}
  #uiSkills .sk[data-k="Heavy"]::after{top:20px;width:13px;height:13px;margin-left:-7px;border-right-width:4px}
  #uiSkills .sk[data-k="Wide"]::after{top:22px;width:26px;height:8px;margin-left:-13px;border-bottom-width:3px}
  #uiSkills .sk[data-k="Dash"]::after{top:25px;width:22px;margin-left:-11px;
    border-top-width:3px;box-shadow:0 5px 0 0 var(--sk-accent),0 -5px 0 0 var(--sk-accent)}
  #uiSkills .sk .nm{font-size:10.5px;bottom:5px}
  #uiSkills .sk .cds{font-size:17px;margin-top:-10px;height:20px;line-height:20px}
  #uiSkills .skLock .lk{width:10px;height:8px;margin-left:-5px}
  #uiDock .dkSword{padding:5px 11px 6px;gap:6px}
  #sword{font-size:12px}
  #uiDock .dkSword .lb{font-size:9.5px}
  #stHud{bottom:82px}          /* 70 + 12 */
}
@media (max-width:860px){
  #uiDock{padding:7px 10px 10px;gap:9px}
  #uiDock .dkExp{left:10px;right:10px}
  #uiDock .dkLv{width:24px;height:24px;font-size:12px}
  #uiDock .dkLb{font-size:9px}
  #eBar{height:17px;min-width:70px;max-width:150px}
  #uiHpNum{font-size:11px;padding:3px 6px 4px}
  #uiHpNum s,#uiHpNum u{font-size:10px}
  #eTxt{padding-left:13px;font-size:11px}
  #uiSkills{gap:5px}
  #uiDock .dkSlots{gap:8px}
  #uiSkills .sk,#uiSkills .skLock{width:50px;height:48px;--c:6px}
  #uiSkills .skLock{width:26px}
  /* 띠 표: 키캡 3~17 · 획 18~31 · 이름 33.1~ */
  #uiSkills .sk .key{top:3px;min-width:18px;height:14px;line-height:12px;font-size:9.5px;padding:0 4px}
  #uiSkills .sk[data-k="Basic"]::before{top:21px;width:8px;height:8px;margin-left:-10px;border-right-width:2px}
  #uiSkills .sk[data-k="Basic"]::after{top:19px;width:10px;height:12px;margin-left:-3px;border-right-width:3px}
  #uiSkills .sk[data-k="Heavy"]::after{top:19px;width:12px;height:12px;margin-left:-7px;border-right-width:3px}
  #uiSkills .sk[data-k="Wide"]::after{top:21px;width:22px;height:7px;margin-left:-11px;border-bottom-width:3px}
  #uiSkills .sk[data-k="Dash"]::after{top:23px;width:18px;margin-left:-9px;
    border-top-width:3px;box-shadow:0 5px 0 0 var(--sk-accent),0 -5px 0 0 var(--sk-accent)}
  #uiSkills .sk .nm{font-size:9.5px;bottom:4px}
  #uiSkills .sk .cds{font-size:15px;margin-top:-9px;height:18px;line-height:18px}
  #uiSkills .skLock .lk{width:9px;height:7px;margin-left:-4.5px}
  #uiSkills .skLock .lk::before{width:7px;height:5px;margin-left:-3.5px}
  #uiDock .dkSword{padding:4px 9px 5px;gap:5px}
  #sword{font-size:11.5px}
  #help .k{min-width:1.7em;padding:1px .38em 2px}
  #stHud{bottom:74px}          /* 62 + 12 */
  #bGoal{padding:7px 15px 8px 66px;font-size:12.5px}
  #bGoal::before{left:16px}
  #bGoal::after{left:34px;font-size:10.5px}
  #uiTitle .win{padding:62px 28px 24px}
  #uiBanner .win{padding:60px 30px 22px}
  #uiDeath .win{padding:60px 26px 24px}
}
/* 세로가 짧은 창(노트북 전체화면 아님 등). 계기판은 이 벌에서 이미 절반 이하로
   낮아졌지만, 560px 창에서는 그마저도 화면의 13% 라 한 단 더 깎는다.
   ★칸 높이가 줄면 **띠 표 전체**가 같이 줄어야 한다(획만 남기면 이름을 문다). */
@media (max-height:620px){
  #uiDock{padding:7px 12px 10px}
  #uiSkills .sk,#uiSkills .skLock{height:48px}
  /* 띠 표: 키캡 3~17 · 획 18~31 · 이름 32.5~ */
  #uiSkills .sk .key{top:3px;height:14px;line-height:12px}
  #uiSkills .sk .nm{bottom:4px;font-size:10px}
  #uiSkills .sk[data-k="Basic"]::before{top:20px;height:9px}
  #uiSkills .sk[data-k="Basic"]::after{top:18px;height:12px}
  #uiSkills .sk[data-k="Heavy"]::after{top:18px;height:12px}
  #uiSkills .sk[data-k="Wide"]::after{top:20px;height:7px}
  #uiSkills .sk[data-k="Dash"]::after{top:22px;
    box-shadow:0 5px 0 0 var(--sk-accent),0 -5px 0 0 var(--sk-accent)}
  #eBar{height:18px}
  #stHud{bottom:76px}
  #uiHpFloat{width:68px;height:10px}
  #uiHpFloat .lv{width:21px;height:21px;font-size:10.5px}
  /* ★안내판 아래끝이 계기판 윗선을 넘지 않게 줄 간격만 줄인다.
     글자 크기는 마지막에 건드린다는 순서 그대로다. */
  #help{line-height:1.45;padding:8px 12px 9px}
  #help .hSep{margin:4px 4px 5px 0}
  #help .hNote{line-height:1.4}
}
@media (max-height:560px){
  #uiTitle{padding-top:clamp(24px,4vh,48px)}
  #uiTitle .win{padding:58px 28px 20px}
  #uiDeath .glyph{font-size:clamp(60px,10vh,82px)}
  #uiDeath .win{padding:56px 26px 20px}
}

/* ══ 연출이 화면을 소유한다 (판정 S4 · S5 · S6 · S7) ═══════════════════════
   ★★이 블록은 **반드시 이 파일 CSS 의 맨 끝**에 있어야 한다. 여기 적힌 선택자는
     전부 (0,2,0) 이라 「body.uiHelpOff #uiHelpChip{opacity:1}」 같은 앞쪽 규칙과
     특이도가 같다. 앞에 두면 나중에 쓴 쪽이 이겨서 **조각 하나만 안 물러난다**
     (실측: 배너가 떠 있는 동안 왼쪽 위 「?」 칩만 혼자 켜져 있었다).
     새 상태를 넣을 때도 이 블록에 넣을 것.

   판정: 보스 배너·처치 컷·결과창이 도는 동안에도 도움말 판·목표 태그·계기판·
   나침반이 그대로 서 있어서 어느 것이 지금 화면의 주인인지 안 갈렸다. 특히 배너는
   좁은 창에서 왼쪽 도움말 판과 실제로 겹쳤다. z-index 를 올려 덮는 것은 답이 아니다 -
   덮어도 밑에 판이 비쳐 지저분하다. **도는 동안은 아예 물린다.**

   네 상태가 하는 일이 같아서 한 표로 적는다.
     uiTitleOn = 입장·재시작 알림창 (.06 으로 물린다. 완전히 끄면 판이 멎은 것처럼 보인다)
     uiBossIn  = 보스 경고창 (2.5s + 0.46s)
     uiCine    = 보스가 쓰러지는 컷 (CINE_KILL)
     uiCleared = 층 돌파 결과창 (판이 끝날 때까지)
   ★#uiDeath(사망 카드)의 표는 위쪽 3) 절에 그대로 둔다. */
body.uiTitleOn #help,body.uiTitleOn #uiHelpChip,body.uiTitleOn #uiDock,
body.uiTitleOn #bHud,body.uiTitleOn #stat,body.uiTitleOn #stHud,
body.uiTitleOn #uiHpFloat{
  opacity:.06;
  /* ★들어올 때는 **빠르게** 물린다(판정 S4). 예전 값 .5s 는 카드가 진해지는 구간과
     그대로 겹쳐서, R 재시작에 카드도 0.2·계기판도 0.8 인 프레임이 24장 나왔다.
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

  // 스킬 슬롯 두 칸 + 잠긴 칸 둘. 이름은 index.html 조작 안내와 같은 말을 쓴다.
  // ★첫 자식은 반드시 <i class="cd"> 다(setSkill 이 firstElementChild 로 잡는다).
  //   그 다음이 남은 초 <b class="cds">, 그 뒤가 키캡·이름이다.
  // ★회피 슬롯은 main.js(mountDashChip)가 나중에 붙인다. 그래서 잠긴 칸이 DOM 상으로는
  //   회피보다 앞에 서고, 눈에 보이는 순서는 CSS order 가 바로잡는다(14차 블록).
  const skills = el('div', 'uiSkills');
  const slotHtml = (k, key, nm) =>
    '<div class="sk" data-k="' + k + '"><i class="cd"></i><b class="cds"></b>'
    + '<span class="key">' + key + '</span><span class="nm">' + nm + '</span></div>';
  skills.innerHTML =
    // ★17차: 기본기 Z 가 계기판에 없었다(비평 2 - 신규 유저가 공격 키를 몰라 두 번 죽었다).
    //   맨 왼쪽에 X·C 와 **같은 타일 문법**으로 세운다.
    slotHtml('Basic', 'Z', '베기')
    + slotHtml('Heavy', 'X', '수면참') + slotHtml('Wide', 'C', '횡일섬')
    // 잠긴 칸. 글자를 안 붙인다 - 자물쇠 하나가 「여기 더 붙는다」를 다 말한다.
    + '<div class="skLock"><i class="lk"></i></div>'
    + '<div class="skLock"><i class="lk"></i></div>';
  const skBasic = skills.querySelector('[data-k="Basic"]');
  const skHeavy = skills.querySelector('[data-k="Heavy"]');
  const skWide = skills.querySelector('[data-k="Wide"]');

  // 목표 방향 나침반. 판(글자)은 안 돌고 화살만 판 둘레를 돈다
  const nav = el('div', 'uiNav');
  nav.innerHTML = '<div class="dial"><i class="tip"></i></div><div class="plate"></div>'
    + '<div class="cap"></div><div class="dst"></div>';
  const navDial = nav.querySelector('.dial');
  const navPlate = nav.querySelector('.plate');
  const navCap = nav.querySelector('.cap');
  const navDst = nav.querySelector('.dst');

  // 가까운 요괴 무리 마커
  const pip = el('div', 'uiPip');
  pip.innerHTML = '<div class="cap"></div>';
  const pipCap = pip.querySelector('.cap');
  pipCap.textContent = PIP_HINT;

  document.body.append(bg, title, banner, death, chip, dim, nav, pip);

  // -------------------------------------------------------------------------
  // 계기판 도킹 (16차: 세 층 쌓기 -> **화면 하단 전폭 가로 띠 한 줄**)
  // -------------------------------------------------------------------------
  // ★남의 파일이 만든 조각을 **옮겨 담기만** 한다. enemy.js·main.js 는 전부
  //   getElementById 로 잡고 있어서 부모가 바뀌어도 참조가 안 끊긴다.
  //   (없으면 그 줄만 조용히 빠지고 나머지는 그대로 선다)
  //
  // ★★16차 오너 지시: "아래 그 스킬이랑 체력바있고 이런거 가로로길게해서 좀 롤이나
  //   메이플처럼해봐. 지금은 가운데 떠있어서 화면너무가림"
  //   13~14차 계기판은 폭 37% · 높이 18% 짜리 **덩어리**였다(1440x900 실측 161px).
  //   가로로 짧고 세로로 두꺼우니 화면 한복판 아래에 카드가 하나 떠 있는 그림이 된다.
  //   롤·메이플은 둘 다 그 반대다 - **가로로 길고 세로로 얇다.**
  //
  //   [Lv 3][♥][체력 트랙 84/100][처치 n]   [X][C][Space][잠금][잠금]   [칼 · 이름]
  //   ──────────────────────────── EXP 띠(맨 아래 변) ────────────────────────────
  //
  //   세 그룹으로 나눈 근거는 롤의 정보 위계 그대로다 - 왼쪽이 「나」, 가운데가
  //   「내가 누를 것」, 오른쪽이 「내가 가진 것」. CSS 는 grid 1fr auto 1fr 이라
  //   슬롯 열이 창 폭과 무관하게 **화면 정중앙**에 선다(캐릭터가 늘 정중앙에 서므로
  //   눈이 좌우로 안 흔들린다).
  //   ★정보는 한 칸도 안 뺐다. 층만 셋에서 하나로 폈다.
  const dock = el('div', 'uiDock');
  const swordEl = document.getElementById('sword');
  const eHudEl = document.getElementById('eHud');

  // 왼쪽 = 나. [레벨 뱃지][하트][체력 트랙 + 수치][처치 n]
  // ★레벨 뱃지와 하트는 우리가 만드는 두 조각이다(남의 DOM 은 안 건드린다).
  // ★뱃지의 수는 머리 위 뱃지와 **같은 값**이다(새 정보가 아니라 같은 셈을 두 자리에서
  //   읽는 것뿐). 롤의 초상 옆 레벨 원 · 메이플의 「LV.」 가 있던 자리다.
  const lvBadge = document.createElement('b');
  lvBadge.className = 'dkLv';
  lvBadge.textContent = '1';
  const leftRow = row('dkLeft');
  leftRow.append(lvBadge);
  if (eHudEl) {
    // ★17차 비평 1: 하트 ♥ 는 **이모지 글리프**라 이 벌의 활자 문법에서 혼자 튀었다.
    //   오른쪽 「칼」 태그와 같은 작은 라벨로 되돌린다(계기판 좌우가 같은 문법이 된다).
    const lb = document.createElement('span');
    lb.className = 'dkLb';
    lb.textContent = '체력';
    leftRow.append(lb, eHudEl);
  }
  dock.append(leftRow);

  // 가운데 = 누를 것. 슬롯 열만 선다(칼은 오른쪽으로 나갔다 - 14차는 여기 붙어 있었다).
  const slotRow = row('dkSlots');
  slotRow.append(skills);
  dock.append(slotRow);

  // 오른쪽 = 가진 것. 칼 태그.
  // ★칼이 없는 몸(궁수)에서는 아래 fixSword 가 이 칸째로 접는다. 그룹이 아니라 칸이
  //   접히는 것이라 grid 세 칸은 그대로 서 있는다.
  const rightRow = row('dkRight');
  const swordCell = swordEl ? row('dkSword') : null;
  if (swordCell) {
    const lb = document.createElement('span');
    lb.className = 'lb';
    lb.textContent = '칼';
    swordCell.append(lb, swordEl);
    rightRow.append(swordCell);
  }
  dock.append(rightRow);

  // 성장 띠(메이플 EXP 자리). 값은 updateHp 가 쓴다.
  // ★position:absolute 라 grid 칸을 안 먹는다 - 판의 **아래 변 그 자체**가 된다.
  const expBar = document.createElement('i');
  expBar.className = 'dkExp';
  const expFill = document.createElement('i');
  expBar.append(expFill);
  dock.append(expBar);
  document.body.append(dock);

  // 체력 숫자. ★★17차 비평 1: 14차·16차는 이 숫자를 트랙 **안 가운데**에 얹었다.
  //   만체력에서 흰 글자가 형광 초록 위에 올라타 대비가 무너진다(캡처에서 100/100 이
  //   초록에 먹혔다). **트랙 밖 어두운 캡슐**로 내보낸다 - 카드가 쓰는 그 유리판이다.
  // ★enemy.js 는 만들 때 한 번 innerHTML 을 쓰고 그 뒤로는 #eFill 의 style 과 #eTxt 만
  //   만진다. 그래서 #eHud 에 자식을 하나 더 끼워도 안 지워진다(실측으로 확인).
  // ★자리는 [트랙][캡슐][처치 n] 이다. #eTxt 앞에 끼워야 그 순서가 나온다.
  const hpNum = el('b', 'uiHpNum');
  const barEl = document.getElementById('eBar');
  const killEl = document.getElementById('eTxt');
  if (eHudEl && killEl) eHudEl.insertBefore(hpNum, killEl);
  else if (eHudEl) eHudEl.appendChild(hpNum);
  else if (barEl) barEl.appendChild(hpNum);

  // 머리 위 체력바. 레벨 배지와 트랙은 같은 transform 노드 안에서 함께 추적된다.
  const hpFloat = el('div', 'uiHpFloat');
  hpFloat.innerHTML = '<b class="lv">1</b><span class="track"><i class="gh"></i><i class="fl"></i></span>';
  const hpLevel = hpFloat.querySelector('.lv');
  const hpGhost = hpFloat.querySelector('.gh');
  const hpFill = hpFloat.querySelector('.fl');
  document.body.append(hpFloat);

  // 계기판의 한 그룹. .dkRow 가 공통 판(가로 flex)이고 두 번째 클래스가 그 자리의 얼굴이다.
  // ★16차부터 「층」이 아니라 「그룹」이다 - 셋이 위아래로 쌓이지 않고 한 줄에 나란히 선다.
  function row(kind) {
    const c = document.createElement('div');
    c.className = 'dkRow ' + kind;
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
    // 남은 초를 찍을 칸을 기억해 둔다. ★게임 입력은 한 톨도 안 먹는다(읽기만 한다) -
    //   preventDefault 도 없고, main.js 의 리스너는 자기 것대로 그대로 돈다.
    if (e.code === 'KeyX') lastSkill = 'Heavy';
    else if (e.code === 'KeyC') lastSkill = 'Wide';
    else if (e.code === 'KeyZ' || e.code === 'Space') lastSkill = '';
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
  // ★방금 누른 기술 칸. 남은 초를 **한 칸에만** 찍기 위한 값이다(아래 updateSkills).
  //   게임 상태가 아니라 **화면 표시용 기억**이라 이 파일이 가져도 된다 -
  //   main.js 는 「지금 휘두르는 중」만 내놓고 「무엇으로 휘두르는 중」은 안 내놓는다.
  let lastSkill = '';
  function updateSkills() {
    const d = window.__dbg;
    const acts = (d && d.actions) || null;
    const busy = !!(d && d.atk);
    if (!busy) noteBusyEnd();
    const lf = busy ? busyLeft(d) : null;
    // ★★17차 비평 6 「X·C 에 같은 쿨다운 숫자가 동시에 뜬다」. 그럴 만했다 -
    //   이 게임의 잠금은 기술마다 도는 쿨이 아니라 **휘두르는 동안 전부 못 쓰는**
    //   한 개의 상태(d.atk)다. 그런데 16차는 그 하나를 두 칸에 각각 숫자로 찍었다.
    //   숫자가 둘이면 「따로 도는 쿨이 둘」이라는 거짓말이 된다.
    //   → 덮개(회색 쓸기)는 못 쓰는 칸 **전부**에 그대로 두고, **숫자는 방금 누른
    //     칸에만** 남긴다. 나머지 칸은 「지금은 못 쓴다」까지만 말한다.
    setSkill(skHeavy, !!(acts && acts.Heavy), busy, lf, lastSkill === 'Heavy');
    setSkill(skWide, !!(acts && acts.Wide), busy, lf, lastSkill === 'Wide');
    // 기본 베기(Z). ★쿨이 **없는** 기술이다 - 캔슬 지점부터 바로 다음 타로 잇는다.
    //   그래서 덮개도 숫자도 안 얹는다(얹으면 20Hz 로 깜빡이는 거짓 쿨이 생긴다).
    //   칸이 늘 밝은 것이 이 게임의 참말이다 - 언제든 누를 수 있는 한 칸.
    if (skBasic) {
      const has = !!(acts && acts.Attack);
      skBasic.classList.toggle('gone', !has);
      skBasic.classList.toggle('rdy', has);
      skBasic.classList.remove('off');
    }
    updateDash();
  }
  function setSkill(node, has, busy, lf, mine) {
    node.classList.toggle('gone', !has);
    node.classList.toggle('off', busy);
    node.classList.toggle('rdy', has && !busy);
    paintCd(node, busy && lf ? lf.r : 0, (busy && lf && mine) ? lf.sec : 0);
  }
  // ── 회피 슬롯 ──
  // ★★이 칸은 **소유가 다르다.** DOM 도 main.js(mountDashChip)가 만들고, 쿨다운 덮개와
  //   rdy/off 도 main.js 가 **매 프레임** 직접 쓴다(main.js 의 「대시 칩」 블록).
  //   그래서 여기서 같은 것을 또 쓰면 60Hz 와 20Hz 가 서로 다른 색을 번갈아 칠한다
  //   (첫 판에서 실제로 두 색이 깜빡였다 - 라디얼 색이 내 값이 아니라 main.js 값으로
  //   찍혀 나오는 것을 보고 잡았다).
  //   ★그래서 이 파일이 이 칸에 더하는 것은 **남은 초 글자 한 칸뿐**이다.
  //     덮개 색도 main.js 와 같은 값을 쓴다(아래 CD_INK) - 안 그러면 X·C 와 Space 의
  //     쿨다운이 서로 다른 색으로 보인다.
  let skDash = null;
  function dashNode() {
    if (skDash && skDash.isConnected) return skDash;
    skDash = skills.querySelector('[data-k="Dash"]');
    // main.js 가 만든 칩에는 초 칸이 없다. 구조는 안 바꾸고 자식만 하나 더한다
    // (#uiHpNum 을 #eBar 안에 넣은 것과 같은 수법).
    if (skDash && !skDash.querySelector('.cds') && skDash.firstElementChild) {
      const b = document.createElement('b');
      b.className = 'cds';
      skDash.insertBefore(b, skDash.firstElementChild.nextSibling);
    }
    return skDash;
  }
  function updateDash() {
    const node = dashNode();
    if (!node) return;
    const s = node.querySelector('.cds');
    if (!s) return;
    const f = window.__dash;
    // 낡은 빌드(창구가 없다)에서는 글자를 안 쓴다. 덮개는 main.js 가 그대로 그린다.
    if (typeof f !== 'function') { if (s.textContent) s.textContent = ''; return; }
    let d;
    try { d = f(); } catch (e) { return; }
    setSec(s, d ? Math.max(0, d.cdLeft || 0) : 0);
  }
  // 쿨다운 덮개 + 남은 초. 12시에서 시작해 시계 방향으로 남은 만큼 덮여 있다가 걷힌다.
  // ★★색은 **main.js 의 대시 칩과 같은 값**이어야 한다(위 설명). 한쪽만 바꾸면
  //   같은 열의 슬롯 셋이 서로 다른 쿨다운 색을 갖는다.
  const CD_INK = 'rgba(4,4,3,.80)';
  function paintCd(node, turn, sec) {
    const g = node.firstElementChild;              // .cd
    const s = node.querySelector('.cds');
    if (!g) return;
    if (!(turn > 0)) {
      if (g.style.background) g.style.background = '';
      setSec(s, 0);
      return;
    }
    const t = Math.max(0, Math.min(1, turn)).toFixed(3);
    g.style.background = 'conic-gradient(from 0deg,' + CD_INK + ' 0turn ' + t
      + 'turn,rgba(4,4,3,0) ' + t + 'turn)';
    setSec(s, sec);
  }
  // 남은 초 한 칸. ★1초 위는 정수(롤 문법), 밑은 소수 한 자리. 0.35초 밑에서는 아예
  //   안 쓴다 - 숫자가 사라지는 그 순간이 「이제 된다」는 신호라 마지막 한 칸은 비워 둔다.
  function setSec(s, sec) {
    if (!s) return;
    const want = sec >= 1 ? String(Math.ceil(sec))
      : (sec >= 0.35 ? sec.toFixed(1) : '');
    if (s.textContent !== want) s.textContent = want;
  }
  // 남은 시간(비율 r 과 초 sec). r 1 = 방금 시작, 0 = 곧 끝.
  // ★main.js 는 attackEnd(게임시계)를 밖에 안 내놓는다. 그래서 **지금 도는 클립의
  //   진행도**를 읽는다. 클립 시간은 재생속도와 무관하게 0..duration 이라 그대로 비율이다.
  //   클립을 못 읽는 몸(궁수 등)에서는 아래 EMA 로 떨어진다.
  // ★★초는 **클립 길이로 재면 안 된다.** 첫 판에서 0.5초짜리 휘두르기에 「2」가 떴다.
  //   클립은 2초가 넘는데 main.js 가 취소 지점(canCancelAttack)에서 attacking 을 먼저
  //   푼다 - 화면에 나가는 「남은 초」는 클립이 아니라 **실제로 못 쓰는 시간**이어야 한다.
  //   그래서 비율 x 「지난 스윙들이 실제로 걸린 시간」(busyEst) 으로 낸다.
  //   busyEst 는 아래 noteBusyEnd 가 스윙이 끝날 때마다 실측으로 배운다.
  let busyT0 = 0, busyEst = 0.62, wasBusy = false;
  function busyLeft(d) {
    const now = performance.now();
    if (!wasBusy) { wasBusy = true; busyT0 = now; }
    const a = d && d.cur;
    if (a && typeof a.time === 'number' && typeof a.getClip === 'function') {
      const clip = a.getClip();
      if (clip && clip.duration > 0) {
        const r = Math.max(0, Math.min(1, 1 - a.time / clip.duration));
        return { r, sec: r * busyEst };
      }
    }
    const r = Math.max(0, Math.min(1, 1 - (now - busyT0) / 1000 / busyEst));
    return { r, sec: r * busyEst };
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
  // ★12차: 판 크기(46px)는 그대로지만 크림 테가 3px 로 굵어져 바깥 반지름이 26px 이
  //   됐다. 화살 밑변을 36 → 38px 로 물리고 그만큼 NAV_R 도 같이 민다
  //   (안 밀면 화살이 비스듬할 때만 테를 파고든다).
  const NAV_R = 66;           // px. 나침반 중심에서 화살 끝까지(38 + 화살 28)
  const PLATE_R = 23;         // px. 판 반지름
  const PIP_R = 10;           // px. 무리 마커 소형판 반지름(20px 판)
  // px. 나침반 첫 등장 라벨(.cap)이 판 중심 밑으로 자라는 길이(margin-top 28 + 높이 22).
  const NAV_CAP_H = 36;
  // px. 남은 거리 판(.dst)이 판 중심 밑으로 자라는 길이(margin-top 28 + 높이 17).
  const NAV_DST_H = 22;

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
  // ★12차: 뜻(붉음=보스, 호박=증표, 중성=탈출구)은 그대로 두고 획 색만 이 벌의
  //   크림 쪽으로 끌어왔다. 판이 남색 + 크림 테라 획도 그 계열이어야 한 벌로 읽힌다.
  // ★16차: 글리프와 크기는 한 점도 안 바꿨다(정보로서 잘 작동해 온 자산이다).
  //   색만 이 벌의 네 색 규칙에 맞춘다 - **위험=빨강 · 보상=앰버 · 길=시안**.
  //   화면의 실물과도 여전히 짝이다(보스=어귀 선돌의 붉은 끈, 증표=호박색 빛기둥).
  const NAV_KIND = {
    boss:  { glyph: '鬼', ink: '#ff5a4a', glow: 'rgba(255,90,74,.55)' },
    token: { glyph: '符', ink: '#ffbb3d', glow: 'rgba(255,187,61,.50)' },
    exit:  { glyph: '門', ink: '#56d8ff', glow: 'rgba(86,216,255,.50)' },
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
  let navDstTxt = '';         // 지금 찍혀 있는 거리 글자. 같은 이유로 캐시한다
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
    // ── 남은 거리 ──
    // ★비평 ④ "마커에 거리 정보가 없어 전진/막힘 판별이 안 된다". 방향은 이미 화살이
    //   말하고 있었다. 없던 것은 **가고 있는가**였다. 숫자 하나면 그게 붙는다.
    // ★첫 등장 라벨이 붙어 있는 2.6초 동안만 비킨다(같은 자리를 쓴다).
    const pp = window.__pos ? window.__pos() : null;
    const capOn = navCap.classList.contains('on');
    if (pp) {
      const m = Math.max(0, Math.round(Math.hypot(t.x - pp.x, t.z - pp.z)));
      const txt = m + 'm';
      // ★글자가 안 바뀌면 DOM 을 안 건드린다. 매 프레임 textContent 를 쓰면
      //   그때마다 레이아웃이 다시 돈다(계기판에서 이미 겪은 함정이다).
      if (navDstTxt !== txt) { navDstTxt = txt; navDst.textContent = txt; }
      navDst.classList.toggle('on', !capOn);
    } else navDst.classList.remove('on');
    const s = safeBox();
    // ★첫 등장 라벨이 붙어 있는 동안은 판 밑으로 34px 이 더 자란다. 그 창에서만
    //   아래 한계를 더 올린다 - 평상시에도 올려 두면 「가리키는 자리」가 어긋난다.
    // ★거리 판(22px)도 같은 자리라 켜져 있으면 그만큼 물러난다.
    const capH = capOn ? NAV_CAP_H : (navDst.classList.contains('on') ? NAV_DST_H : 0);
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
  let hpMax = 100, hpSeen = -1, hpLevelSeen = 0, expSeen = -1;
  function updateHp() {
    const en = window.__enemy;
    if (!en || typeof en.hp !== 'number') return;
    // 표시 전용 레벨이다. 게임 시스템에는 쓰지 않으며 처치 5회마다 한 단계만 올린다.
    const kills = Math.max(0, Number(en.kills) || 0);
    const level = 1 + Math.floor(kills / 5);
    if (level !== hpLevelSeen) {
      hpLevelSeen = level;
      hpLevel.textContent = String(level);
      // 16차: 같은 수를 계기판 왼쪽 뱃지에도 쓴다(머리 위 뱃지와 **같은 값**이다).
      lvBadge.textContent = String(level);
    }
    // 성장 띠. **머리 위 뱃지와 같은 셈**을 그림으로 편 것뿐이다(새 정보가 아니다).
    // 이게 없으면 뱃지가 5마리째에 갑자기 바뀌는 것처럼 보인다.
    const g = (kills % 5) / 5;
    if (g !== expSeen) {
      expSeen = g;
      expFill.style.transform = 'scaleX(' + g.toFixed(3) + ')';
    }
    if (en.hp > hpMax) hpMax = Math.ceil(en.hp);
    const v = Math.max(0, Math.round(en.hp));
    if (v === hpSeen) return;                      // 안 바뀌었으면 DOM 을 안 쓴다
    hpSeen = v;
    hpNum.innerHTML = v + '<s>/</s><u>' + hpMax + '</u>';
    const low = v <= hpMax * 0.25;
    hpNum.classList.toggle('low', low);
    // ── 게이지 색 (17차 비평 1) ──
    // ★enemy.js 가 인라인으로 칠하는 형광 그러데이션을 카드 팔레트로 덮는다.
    //   문턱(50% · 25%)은 enemy.js 와 **같은 값**이어야 한다 - 한쪽만 바꾸면
    //   색이 뜻하는 바가 두 파일에서 갈린다. 클래스만 얹고 색은 CSS 가 갖는다.
    if (barEl) {
      const band = low ? 'hpLo' : (v <= hpMax * 0.5 ? 'hpMid' : 'hpHi');
      if (barEl.dataset.band !== band) {
        barEl.dataset.band = band;
        barEl.classList.remove('hpHi', 'hpMid', 'hpLo');
        barEl.classList.add(band);
      }
    }
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
               // 스킬 슬롯: 밝은가(off 가 아니면 지금 쓸 수 있다) · 있는가 · 남은 초
               // ★14차: sec 은 슬롯 한가운데에 실제로 쓰인 글자다(빈 문자열 = 안 뜬다).
               skills: (() => {
                 const one = (n) => n ? {
                   has: !n.classList.contains('gone'),
                   on: !n.classList.contains('off'),
                   rdy: n.classList.contains('rdy'),
                   cd: n.firstElementChild ? n.firstElementChild.style.background : '',
                   sec: (n.querySelector('.cds') || {}).textContent || '',
                   rect: (() => { const r = n.getBoundingClientRect();
                     return [Math.round(r.width), Math.round(r.height)]; })(),
                 } : null;
                 return { Z: one(skBasic), X: one(skHeavy), C: one(skWide),
                          Space: one(skills.querySelector('[data-k="Dash"]')),
                          lock: skills.querySelectorAll('.skLock').length,
                          // 남은 초가 **몇 칸에** 떠 있는가(17차: 둘이면 거짓말이다)
                          secShown: Array.from(skills.querySelectorAll('.cds'))
                            .filter(e => e.textContent).length,
                          // 화면에 보이는 왼쪽부터의 순서(CSS order 가 제대로 먹었나)
                          order: Array.from(skills.children)
                            .map(e => ({ k: e.dataset.k || 'Lock',
                                         x: Math.round(e.getBoundingClientRect().left) }))
                            .sort((a, b) => a.x - b.x).map(e => e.k) };
               })(),
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
