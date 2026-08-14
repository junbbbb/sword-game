// 손맛: 히트스톱 · 화면 흔들림 · 처치 연출(붓질 슬래시 · 방사형 속도선)
//
// 왜 별 파일인가: main.js 가 이미 2천 줄이고, 여기 값들은 **혼자 놓고 만지는 게 맞다**.
// 히트스톱은 0.05초 단위의 감각이라 다른 코드와 섞여 있으면 튜닝을 못 한다.
//
// ★설계의 핵심 한 줄: **세계는 멈춰도 카메라는 안 멈춘다.**
//   멈춘 45~120ms 동안 화면이 같이 얼어붙으면 "끊겼다"로 읽히고, 그동안 화면이
//   미세하게 떨리면 "때렸다"로 읽힌다. 그래서 시간 배율(스케일된 dt)과
//   흔들림(실제 dt)을 이 파일에서 **두 시계로 갈라서** 관리한다.
import * as THREE from './lib/three.module.js';

// ── 시간 값 (전부 초) ──
const STOP_HIT = 0.055;      // 명중 (45~70ms 대역의 한가운데)
const STOP_KILL = 0.105;     // 처치 (90~120ms)
const STOP_HURT = 0.060;     // 플레이어 피격
const STOP_SCALE = 0.05;     // 0 이 아니라 0.05. 완전 0 은 렌더가 멈춘 것처럼 보인다
const STOP_BUDGET = 0.140;   // 한 스윙에 여러 마리를 베어도 합쳐서 이 이상은 안 멈춘다
const SLOW_T = 0.25;         // 무리 전멸 슬로모
const SLOW_SCALE = 0.35;
const BLOOM_PULSE = 0.15;    // 전멸 순간 블룸 가산량
const BLOOM_PULSE_T = 0.30;

// ── 레벨 상승 (캐릭터 부착 월드 연출) ──
// 화면을 가리는 알림창 대신 발밑의 얇은 고리와 몸을 타고 오르는 빛만 남긴다.
// 실제 시간으로 1초 안에 끝나므로 히트스톱 중에도 성장 신호가 또렷하게 읽힌다.
const LEVEL_UP_T = 0.96;
const LEVEL_UP_SPARKS = 14;
// ── 사망 슬로모 (v84 QA S2) ──
// 실측 근거: 죽는 순간 화면에서 유일하게 바뀌는 게 「落」카드뿐이라, 여섯 번 죽는
// 동안 한 번도 "죽었다"로 안 읽혔다(2026-08-10 QA). 카드를 키우는 것만으로는
// 안 된다. **시간이 늘어져야** 몸이 먼저 안다. 0.30배로 1초.
// ★이 값은 main.js 의 `dt = rawDt * feel.step(rawDt)` 를 통해 게임 전체에 걸린다.
//   즉 요괴·리스폰 타이머까지 같이 늘어진다(의도다 - 죽은 뒤 세상이 느려진다).
const DEATH_SLOW_T = 1.00;
const DEATH_SLOW_SCALE = 0.30;

// ── 붓자국 팔레트 (기술별) ──
// 왜 갈라야 하나: 붓자국 하나로 진홍만 쓰면 **물의 호흡이 피 색으로 나온다.**
// 귀멸에서 기술의 정체는 색이다. 수면참·횡일섬은 감청(紺碧)에 흰 심이어야 물이 된다.
// 밴드는 밝은 쪽부터 core - mid - edge - ink 네 단이고, thr 은 그 경계다.
// ★처치(진홍)는 현행 그대로다. mid 를 edge 와 같은 색으로 두고 경계를 붙여 놨으므로
//   기존 두 단(진홍 - 먹) 그림이 한 픽셀도 안 바뀐다. 여기 숫자를 바꾸면 그게 깨진다.
const PAL_KILL = {
  ink: 0x2a0710,     // 잉크 테두리(먹빛 검붉음)
  edge: 0xd21b32,    // 진홍
  mid: 0xd21b32,
  core: 0xfff2f2,    // 흰 심
  thr: [0.38, 0.82, 0.82],
};
// ── 물 계열 (v94. 여기가 "먹선 11~14%" FAIL 의 진범이었다) ──
// 옛 값은 ink 가 #1428C8 이었다. **그건 먹이 아니라 밝은 파랑이다**(상대휘도 0.20,
// 채도 100%). 그래서 획의 경계 1픽셀 링을 재면 어두운 화소가 11~14% 밖에 안 나왔다
// (같은 시트로 그린 처치 초승달은 ink 가 #2A0710 이라 51% 로 합격). 색 하나가
// "먹선이 형태를 정의한다"를 통째로 깨고 있었다.
// ★귀멸 프레임 팔레트 실측(v93 sheets/08_palette.png)에 맞춘다:
//   한 획 안에 감청 #0C2484~#0C3C9C -> 밝은 시안 #24CCFC -> 흰 심 #CCE4FC.
//   게임 쪽은 중간 명도 파랑(#245484·#0C6C9C)에만 몰려 있어 계단이 없었다.
const PAL_WATER = {
  ink: 0x081228,     // 먹(감청 먹). 형태를 정의하는 선. 휘도 0.045
  edge: 0x0c3c9c,    // 감청
  mid: 0x24ccfc,     // 밝은 시안
  core: 0xcce4fc,    // 흰 심
  thr: [0.30, 0.55, 0.82],
};

// ── 원소 팔레트 (v94) ──
// 화면공간 본 획이 **모든 스윙**에 그어지면서 생긴 문제: 획이 늘 감청이면 홍염(불)을
// 들고 휘둘러도 파란 획이 그어져 칼 일곱 자루의 정체가 화면에서 사라진다.
// 그래서 main.js 가 지금 든 칼의 색 계단을 여기 밀어 넣는다(setSwingPalette).
// ★붉은 계열은 여전히 처치·피격 전용이다 - 홍염은 주홍이라 진홍(PAL_KILL)과 안 겹친다.
// ★물·기본칼은 이 자리를 안 쓰고 아래 PAL_WATER 를 그대로 쓴다(귀멸 실측 팔레트라
//   원소 램프에서 기계로 뽑은 것보다 정확하다).
const PAL_EL = { ink: 0x081228, edge: 0x0c3c9c, mid: 0x24ccfc, core: 0xcce4fc,
                 thr: [0.30, 0.55, 0.82] };
// ── 무리 전멸 링 ──
const RING_T = 0.40;         // 퍼지는 시간(실제 시간). 슬로모 중에도 이 속도로 돈다
const RING_S0 = 1.6;         // 판 한 변(m). 그림의 고리는 이 안쪽 0.77 쯤을 쓴다
// ★v94. 7.4 -> 5.2. 이번 파도의 문법 계약이 "지면 전개는 폐기, 바닥에는 먹 자취 소량만"
//   이다(참격은 화면에 그은 획이고 지면에 까는 그림이 아니다). 전멸의 방점이라 없애지는
//   않았지만, 화면 절반을 덮던 지름을 무리 하나 크기로 줄였다.
// ★v96. 5.2 -> 3.4. 오너 지시 "칼 근처에서만". 무리 하나 크기여도 지면 데칼은
//   쿼터뷰에서 화면 아래쪽을 넓게 먹는다. 마지막으로 벤 자리 한 뼘이면 방점은 선다.
const RING_S1 = 3.4;
const RING_LIFT = 0.035;     // 바닥에서 띄우는 높이. 0 이면 바닥과 z-파이팅한다
// ★색: 구운 ring_shock.png 는 흰·금색이고 원래 가산합성용이다. 그런데 이 맵은
//   아침 산야라 바닥이 밝다. 흰 고리를 밝은 흙 위에 얹으면 그냥 사라진다
//   (붓자국이 같은 이유로 가산합성을 버렸다). 그래서 감청 먹으로 물들여 **어두운
//   고리**로 칠한다. 밝은 흙에서도 풀밭에서도 읽히고, 물의 호흡 색과도 한 집안이다.
//   네 가지(흰 일반 / 감청 먹 / 흙 먹 / 흰 가산)를 실제 화면에서 재보고 골랐다.
// ── 붓자국 크기 (v84 QA S3) ──
// 붓자국은 "여기까지 베었다"고 말하는 그림이다. 그런데 화면을 가로질러 버리면
// 실제 판정보다 훨씬 넓게 벤 것처럼 거짓말을 한다(QA: "화면 절반을 가로지른다").
// ★자를 대고 쟀다(headed, 1280x720, aspect 1.778, 2026-08-10):
//     스냅 사거리 3.0m 를 아래 화면단위(가로 -aspect..aspect / 세로 -1..1)로 옮기면
//       가로축 0.607 · 세로축(지면) 0.521.
//   한 획의 전체 길이는 2 x uLen 이다. 예전 값 uLen 1.15(x 난수 1.14)는
//   전체 2.62 = **3.0m 의 4.3배**이자 화면 가로폭의 74% 였다.
//   상한을 "실사거리의 1.3배" = 0.607 x 1.3 = 0.789 로 잡으면 uLen <= 0.394.
// 그래서 난수 상한(x1.14)을 물려도 안 넘게 아래처럼 둔다.
//   큰 획   0.34 x 1.14 = 0.388  (전체 0.776 = 3.0m 의 1.28배)
//   보통 획 0.25 x 1.14 = 0.285  (전체 0.570 = 3.0m 의 0.94배)
// 굵기는 같은 비율로 줄이면 실오라기가 된다. 짧은 붓은 상대적으로 굵어야 붓으로
// 읽혀서 길이/굵기 비를 4.8 -> 3.2 로 낮춰 잡았다.
// ★궤적 리본(main.js, 칼끝 실측)과 타격 지점 참격(아래 impactSlash, 획 길이 약 1.9m)은
//   원래부터 실사거리 안이라 안 건드린다. 화면을 가로지르던 건 여기 붓자국뿐이다.
// ★v91. 굵기 상수의 뜻이 바뀌었다. 예전 값은 **획 몸통의 반두께**였는데, 지금은
//   시트 칸 세로 절반이다(칸 320px 중 획 몸통은 120~140px = 칸의 0.375 배).
//   그래서 같은 그림 두께를 내려면 0.078 / 0.375 = 0.208 이 필요하다. 여기에 12%만
//   더 얹어 조금 굵게 잡았다(먹 외곽선이 생기면서 속살이 얇아 보이는 것을 보정).
//   길이는 사거리 계약을 그대로 지킨다(큰 획 최대 0.34x1.14x2 = 0.775 <= 0.789).
// ── v94. 크기 계약을 **두 축으로 갈랐다** ──
// 서로 충돌하던 두 심사 판정을 동시에 푸는 유일한 방법이다.
//   · 손맛 심사관: "이펙트가 판정의 3~5배 과장"  -> 벤 **끝선**은 판정에 맞춰야 한다
//   · 이펙트 심사관: "화면 점유 0.5~1.4% vs 귀멸 15~57%" -> 화면에서 커야 한다
// 답: **길이(=리치 방향)는 판정에 못 박고, 굵기(=획에 수직)로 존재감을 낸다.**
//   길이 방향으로 뻗으면 "저기까지 벤 것처럼" 거짓말이 되지만, 획에 수직으로 부푸는 건
//   아무 거짓말도 안 한다(귀멸의 획이 실제로 그렇게 생겼다 - 짧고 굵다).
// 길이 상한(9차 확정 판정 리치 3.2m 기준. handoff_combat.md):
//   3.0m 가 화면 가로축 0.607 이었으므로 3.2m = 0.647.
//   한 획 전체 길이 = 2 x uLen x (난수 1.14) <= 0.647 x 1.28 = 0.828  ->  uLen <= 0.363
const SL_LEN_BIG = 0.362;    // 전체 0.825 = 3.2m 의 1.28배 (상한)
const SL_LEN = 0.345;        // 전체 0.787 = 3.2m 의 1.22배
// ── 굵기는 "화면에서 보고 싶은 몸통 반높이"로 적는다 ──
// ★uThk 는 시트 **칸 세로 절반**이지 획 몸통이 아니다. 칸 안에서 획이 차지하는 비율
//   (SHEET_BODY)을 나눠 줘야 "화면에서 이만큼 굵다"를 상수로 적을 수 있다.
//   시트를 다시 구우면 SHEET_BODY 만 갈면 그림 두께가 그대로 유지된다.
const SHEET_BODY = 0.63;     // 시트 칸 높이 중 획 몸통 비율(실측)
// ★한 획을 뚱뚱하게 만드는 것으로는 존재감이 안 나온다 — 실측 스크린샷에서 그 그림은
//   붓이 아니라 **돛(sail)**으로 읽혔다. 길이가 리치 계약에 묶여 있으므로 굵기만 키우면
//   가로세로 비가 1:1 로 가고, 1:1 은 붓의 비율이 아니다.
//   귀멸의 큰 기술 컷도 한 획이 뚱뚱한 게 아니라 **2~3획이 겹쳐** 화면을 채운다.
//   그래서 한 획은 붓 비율(약 2.2:1)로 두고, 획을 여러 장 어긋나게 깐다(아래 swing).
// ★v94 2차. 0.155/0.200 -> 0.205/0.280. 1차 실측에서 화면 점유가 3.5~7.8% 로 목표
//   12~30% 의 3분의 1 이었다(v93 의 0.5~1.4% 에서 4배 오른 것이긴 하다).
//   붓 비율(약 2.2:1)은 지키면서 획 자체를 한 단 키우고, 아래에서 획 수를 셋 -> 넷으로 늘린다.
// ★v94 3차. 실측으로 갈랐다. 획을 통째로 키웠더니 화면 점유가 4.3~7.0% 로 겨우 15% 올랐다
//   — 획 넷이 서로 **겹쳐서** 새 면적이 거의 안 늘었기 때문이다. 그리고 같은 변경으로
//   처치 프레임의 몸 가림이 0.15 -> 0.32초로 **나빠졌다.**
//   그래서 평타는 도로 낮추고 **일격기(수면참·횡일섬)만** 키운다. 그 둘은 실측에서
//   몸·요괴 가림이 0프레임이라 키울 여유가 있고, 귀멸의 15~57% 컷도 평타가 아니라
//   기술 컷이다. 겹치는 대신 **벌려서** 면적을 낸다(아래 push 배수).
const SW_HALF = 0.175;       // 평타 본 획 몸통 반높이(화면 세로 반높이 1 기준)
const SW_HALF_BIG = 0.360;   // 일격기(수면참·횡일섬)
const SL_THK_BIG = SW_HALF_BIG / SHEET_BODY;
const SL_THK = SW_HALF / SHEET_BODY;
// 안 죽인 명중의 획 배수. 처치와 같은 크기로 그으면 "다 벤 것 같은데 안 죽네"가 된다.
// 작고 옅게 스쳐야 **처치의 한 획**이 값을 지킨다.
const SL_HIT_K = 0.62;
const SL_HIT_A = 0.78;       // 알파도 옅게
// ── 지속 계약 (v94) ──
// 캐릭터 심사관 FAIL: "이펙트가 몸의 3~4배를 0.3~0.9s 덮어 타격 애니가 안 보인다."
// 그래서 **본 획은 24fps 기준 2~4프레임만 살고 사라진다.** 잔상은 가는 먹 자취(궤적
// 리본 꼬리)만 남는다. 여기 숫자가 그 계약이다 - 늘리면 계약이 깨진다.
const SW_N = 4;              // 휘두름 본 획 4/24 = 0.167s
const SW_N_LIGHT = 3;        // 안 죽인 명중 3/24 = 0.125s
const SW_N_KILL = 4;         // 처치 획 4/24 = 0.167s
// ── 화면 겹 붓자국을 껐다 (v96. 오너 직접 지시) ──
// 오너가 배포본을 보고 한 말이 이 상수의 전부다:
//   "이펙트 효과가 칼 근처에서만 나타나야 하는데 뭔 화면의 1/3 덮는 수준이여."
// 실측(1280x720 · v95 빌드 · renders/history/v96_wave10/fx/sheet_before_*.jpg):
//   한 번 휘두를 때 이 화면 겹이 **본 획 1 + 동반 획 3 = 넉 장**을 캐릭터 옆 허공에
//   띄운다. 프레임 검사에서 주인공 머리가 80~94% 덮였고, 그림은 붓이 아니라
//   파란 **돛/연**으로 읽혔다(심사 인용 "몸 옆·앞 허공에 뜬 판때기"와 같은 그림).
// 문법을 갈랐다: **획은 이제 칼 궤적에 붙은 가는 호 하나뿐**이고 그건 월드에서
//   칼끝 실측 궤적으로 그린다(main.js updateTrail). 화면 좌표에 앉는 큰 붓자국은
//   원리상 "칼 근처"일 수가 없으므로(자리를 화면에서 정한다) 통째로 끈다.
// ★기계는 남겨 둔다. 지우면 같이 죽는 것이 셋이다 —
//     · 임팩트 프레임(백색 패널)의 먹 실루엣이 lastStroke.len/thk 를 읽는다(합격작)
//     · 찢김선이 lastStroke.ang/x/y 를 읽는다
//     · 전멸 링이 lastSlashNDC 로 월드 자리를 되짚는다
//   그래서 stroke() 는 **자리·각도만 기록하고 슬롯은 안 잡는다**(아래 SCREEN_STROKE).
const SCREEN_STROKE = 0;     // 1 로 되돌리면 v95 의 화면 겹 붓자국이 그대로 살아난다
const SW_COMP = [];          // 동반 획 폐기(9B-2 가 만든 세 장)

// ── 애니 프레임 ──
// ★이 파일의 v91 전체가 이 한 줄에서 나온다: **연출은 24fps 로 뚝뚝 끊긴다.**
//   60fps 로 부드럽게 보간하면 3D 리본이고, 1/24 초씩 붙들면 작화 프레임이다.
//   시트(web/tex/slash_flip.png)는 가로 2칸(가로베기·대각베기) x 세로 6칸(6프레임).
// ── 타격 지점 참격이 읽는 시트 (v97 11-FX시트) ──
// ★A/B 손잡이 한 줄. codex(gpt-5.6-sol)가 귀멸 실프레임 기준으로 그린 낱장 6장을
//   tools/bake_slash_flip3.py 로 이 규격(2x6 · 칸 1024x320 · 회색조 밝기 계단)에 구웠다.
//   롤백 = 이 문자열을 './tex/slash_flip.png' 로 되돌리는 것뿐이다(옛 시트는 그대로 있다).
const IMPACT_SHEET = './tex/slash_flip3.png';
const FRAME_T = 1 / 24;      // 한 장을 붙드는 시간(초)
// ── v99 16-FX 포말 마루 A/B ──
// 1 = 칼끝 궤적에 붙는 구운 포말 마루 + 타격 팝 f1 물방울 제거.
// 0 = 새 층을 완전히 끄고 기존 팝 두 장 경로로 돌아간다(롤백은 이 한 줄).
const FOAM_CREST_V2 = 1;
// ═════════════════════════════════════════════════════════════════════════════
// ★★18차 「이아이도 일섬」 스위치 (2026-08-13. 오너 지시)
//
//   "칼 이펙트 한번 기존껏 그냥 무시하고 한번너가 새로 만들어봐 귀멸의칼날처럼말고
//    너가 그냥 이펙트 를. 기존꺼 다시 돌릴수있게해놓고."
//
// 그래서 이 상수 **하나**가 새 판과 옛 판을 가른다. main.js 가 이 값을 그대로
// 수입해 쓰므로(import { createFeel, FX_V18 }) 스위치는 이 파일 이 줄뿐이다.
//   1 = 18차 일섬  · 얇은 섬광 호(main.js uMode 4) + 접점 에너지 파열(아래 burst)
//   0 = 17차까지의 귀멸 판  · B 두툼한 물 리본 + 포말 마루 + 초승달 + 먹 튀김 팝
//
// ★0 으로 내리면 **옛 경로가 바이트 그대로** 다시 돈다. 지운 코드가 한 줄도 없고
//   새 코드는 전부 이 상수 뒤에 숨어 있다(gate 만 걸었다. 아래 세 자리가 전부다):
//     · trailFoamSample  포말 마루 표본 수집을 여기서 끊는다(포말은 리본의 것이다)
//     · main.js onHit    초승달(impactSlash)+먹 튀김(pop) 대신 burst() 를 부른다
//     · main.js FX_STYLE 기본 벌이 B 리본 대신 V 일섬이 된다(?fx=b 로 옛 판 열람)
// ★?fx=a|c|d 대조군 셋은 이 스위치와 **무관하다**(그 셋은 손도 안 댔다).
// ═════════════════════════════════════════════════════════════════════════════
export const FX_V18 = 1;
const FLIP_N = 6;            // 시트 세로 칸 수 = 한 획의 프레임 수
const FLIP_C = 2;            // 시트 가로 칸 수 = 획 종류
const FLIP_A = [1.0, 1.0, 1.0, 1.0, 0.90, 0.70];   // 프레임별 알파도 계단이다
// 획 종류 고르기: 화면 각도가 수평에서 이만큼 안쪽이면 가로베기 칸을 쓴다
const FLIP_H_SIN = 0.42;     // sin 0.42 = 약 25도
// 찢김선 길이(장 수). 처치는 짧게 스치고, 무리 전멸은 길게 끈다
// ★v94. 4·8 -> 3·5 로 줄였다. 심사 인용 "속선이 3D 말뚝". 속도선이 본 획보다 오래
//   남으면 획이 사라진 화면에 검은 막대만 남고, 그 순간 배경에 꽂힌 물체로 읽힌다.
//   본 획(4장)보다 짧게 살아야 "획에 딸린 결"로 읽힌다.
const SPD_N = 3;             // 3/24 = 0.125초
const SPD_N_LONG = 5;        // 5/24 = 0.208초 (전멸)
// ── 임팩트 프레임(전면 백색 패널) 스위치 ── ★오너 지시로 껐다(2026-08-13, 17차)
//   "몬스터 다잡아갈때 무슨 이펙트에 화면 번쩍이는거 넣어놨냐? 그거빼"
// 정체: 처치·전멸 순간 화면 전체를 종이색(0xf4eee0)으로 뒤집고 먹 실루엣만 남기는
//   한 장짜리 만화 컷이다(아래 '임팩트 프레임' 절 참조). 실측한 그 한 장은
//   **화면 평균 휘도 50 -> 203 · 200 이상 화소 90.8%** 였고, 다음 프레임이면 사라진다.
//   의도는 "애니가 칼 닿는 순간에 끼워 넣는 극단 대비 컷"이었지만, 60fps 에서 한 장은
//   그림으로 안 읽히고 **흰 점멸**로만 남는다(16차 블라인드 이펙트 비평도 같은 지적:
//   "이 컷이 칼이 닿는 순간을 오히려 가린다"). 사람 눈에는 연출이 아니라 모니터 결함이다.
// ★1 로 되돌리면 v91~17차의 그 컷이 그대로 살아난다. 코드는 통째로 남겨 뒀다
//   (셰이더·실루엣·병합 창까지 전부 그대로. 켜는 문은 이 상수 하나뿐이다).
const IMPACT_CUT = 0;
// 임팩트 프레임 장 수. 처치 1장, 전멸·보스 2장(오너 지시 그대로)
const IMP_N_KILL = 1;
const IMP_N_WIPE = 2;

const RING_TINT = 0x24406e;
const RING_ALPHA = 1.0;      // 시작 투명도
const RING_FRESH = 0.20;     // 이 시간 안에 붓자국이 있었을 때만 그린다(자리를 아는 경우)
const RING_HIT_H = 0.60;     // 요괴가 칼 맞는 높이(enemy.js GOB_H 1.30 x 캡슐 중간)
const FLOOR_FALLBACK = 0.02;

// 바닥 높이는 level.js 가 안다(링을 지면에 눕히려면 필요하다).
// ★같은 URL 로 부른다. 쿼리까지 같아야 main.js·enemy.js 가 쓰는 그 한 벌이 온다.
//   못 읽어도 링은 평지 높이로 그린다(맵에서 올라설 수 있는 단은 셋뿐이다).
let LVL = null;
import('./level.js' + location.search).then(m => { LVL = m; }).catch(() => { LVL = null; });
function groundLevel(x, z) {
  return (LVL && LVL.ready()) ? LVL.groundY(x, z) : FLOOR_FALLBACK;
}

// ── 이 붓자국이 무슨 기술인가 ──
// main.js 가 기술을 안 넘긴다. 그래서 **밖에 이미 나와 있는 신호**를 읽는다.
//   1순위 window.__dbg.cur   지금 도는 애니 클립. Heavy=수면참 / Wide=횡일섬.
//                            시간 창이 없어서 정확하다(맞은 그 프레임의 클립을 본다)
//   2순위 window.__sfx.lastSwing  sfx.js 가 남기는 스윙 종류. 1순위가 없어졌을 때의 보험
// 둘 다 못 읽으면 처치(진홍)로 본다. 진홍이 기본이고 그게 훨씬 자주 나온다.
// ★slash() 에 kind 를 직접 넘기면 이 추측을 건너뛴다. main.js 를 고칠 수 있게 되면
//   'water' / 'kill' 을 넘기고 이 함수는 지워도 된다.
const WATER_WINDOW = 1.1;    // 초. 2순위 신호의 유효 시간
function detectKind(explicit) {
  if (explicit === 'water') return 1;
  if (explicit === 'kill') return 0;
  const d = window.__dbg;
  if (d && d.actions && d.cur) {
    return (d.cur === d.actions.Heavy || d.cur === d.actions.Wide) ? 1 : 0;
  }
  const w = window.__sfx && window.__sfx.lastSwing;
  if (w && w.kind === 'heavy' && performance.now() - w.at < WATER_WINDOW * 1000) return 1;
  return 0;
}

export function createFeel(opts) {
  const scene = opts.scene;
  const camera = opts.camera;
  const bloom = opts.bloom || null;

  let stopT = 0;             // 남은 히트스톱
  let slowT = 0;             // 남은 슬로모
  let deathT = 0;            // 남은 사망 슬로모(전멸 슬로모보다 세고 길다)
  let budget = 0;            // 이번 스윙에 이미 쓴 히트스톱
  let budgetSwing = -1;      // 예산을 쓰고 있는 스윙 번호
  let shakeT = 0, shakeDur = 0.001, shakeAmp = 0;
  let bloomT = 0, bloomBase = bloom ? bloom.strength : 0;
  const shakeOff = new THREE.Vector3();

  // ── 시간 ──
  // 매 프레임 **맨 앞에서 한 번** 부른다. 실제 dt 를 먹고 이번 프레임에 쓸 배율을 낸다.
  // ★이번 프레임 배율을 남겨 둔다. 타격 지점 참격(월드 플립북)이 **게임시계**로
  //   늙어야 하기 때문이다 - 히트스톱 동안 한 장을 붙들고 있어야 한다.
  //   main.js 가 이 함수를 프레임 맨 앞에서, updateOverlay 를 렌더 직전에 부르므로
  //   그 사이에 값이 낡을 일이 없다.
  let timeScale = 1;
  function step(rawDt) {
    if (stopT > 0) { stopT -= rawDt; if (stopT < 0) stopT = 0; timeScale = STOP_SCALE; return STOP_SCALE; }
    // ★사망이 전멸보다 위다. 마지막 한 마리를 베면서 같이 죽는 경우가 있는데,
    //   그때 0.35배(전멸)로 덮이면 사망이 "조금 느려졌다"로 묽어진다.
    if (deathT > 0) { deathT -= rawDt; if (deathT < 0) deathT = 0; timeScale = DEATH_SLOW_SCALE; return DEATH_SLOW_SCALE; }
    if (slowT > 0) { slowT -= rawDt; if (slowT < 0) slowT = 0; timeScale = SLOW_SCALE; return SLOW_SCALE; }
    timeScale = 1;
    return 1;
  }

  // 스윙 하나 안에서 합산 상한을 지키며 멈춘다.
  function addStop(sec, swing) {
    if (swing !== undefined && swing !== budgetSwing) { budgetSwing = swing; budget = 0; }
    const room = Math.max(0, STOP_BUDGET - budget);
    const use = Math.min(sec, room);
    if (use <= 0) return 0;
    budget += use;
    if (use > stopT) stopT = use;      // 겹치면 긴 쪽으로(더하면 3연타에서 늘어진다)
    return use;
  }

  function shake(amp, dur) {
    // 진행 중인 흔들림보다 약하면 무시한다(약한 게 강한 걸 덮어쓰면 김이 샌다)
    const cur = shakeT > 0 ? shakeAmp * (shakeT / shakeDur) : 0;
    if (amp < cur) return;
    shakeAmp = amp; shakeDur = dur; shakeT = dur;
  }

  // ★실제 dt 로 돈다. 멈춘 시간에도 화면은 떨려야 한다.
  function updateShake(rawDt) {
    if (shakeT <= 0) { shakeOff.set(0, 0, 0); return; }
    shakeT -= rawDt;
    if (shakeT <= 0) { shakeT = 0; shakeOff.set(0, 0, 0); return; }
    const k = shakeT / shakeDur;
    const a = shakeAmp * k * k;                       // 뒤로 갈수록 빨리 잦아든다
    const t = performance.now() * 0.001;
    shakeOff.set(Math.sin(t * 97.3) * a, Math.sin(t * 71.7 + 1.3) * a * 0.8,
                 Math.sin(t * 113.1 + 2.7) * a * 0.5);
  }
  function shakeOffset() { return shakeOff; }

  // -------------------------------------------------------------------------
  // 화면 겹 (붓질 슬래시 · 속도선)
  // ★카메라의 자식으로 붙이지 않는다. 카메라를 씬에 넣어야 그려지는데, 그러면
  //   lookAt 이 한 프레임 낡은 matrixWorld 를 보는 함정이 생긴다. 그냥 매 프레임
  //   카메라 앞에 손으로 놓는다(계산이 4줄이고 함정이 없다).
  const OVER_Z = 0.6;                     // 카메라 앞 거리(near 0.1 보다 크면 된다)
  const _fwd = new THREE.Vector3();

  const NOISE = `
    float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
    float noise(vec2 p){
      vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
      return mix(mix(hash(i), hash(i+vec2(1,0)), f.x),
                 mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
    }`;

  // ★2026-08-10 실측으로 바꾼 것: 붓자국은 **가산합성이 아니라 칠하기**다.
  //   원래 스펙은 가산합성이었는데, 맵이 아침 산야(밝은 흙바닥)로 바뀌자 흰 심이
  //   그대로 날아가 "칼 빔"이 됐다. 가산합성은 원리상 **어두운 잉크 테두리를 못 그린다.**
  //   귀멸의 임팩트 프레임이 그림으로 읽히는 이유가 바로 그 잉크 테두리다.
  //   그래서 NormalBlending 으로 칠한다: 잉크 테두리 - 진홍 - 흰 심, 세 단.
  // ★v94. 3 -> 7. 한 번 휘두를 때 본 획 1 + 동반 획 3 = 네 장이 동시에 뜨고,
  //   3연타에서 앞 스윙의 획이 아직 살아 있는 동안 다음 스윙이 겹친다.
  //   슬롯이 모자라면 방금 그은 획이 밀려 사라져서 겹침이 안 쌓인다.
  //   ★배열 유니폼은 전부 mkNum(SLOTS,...)/mkVec2(SLOTS) 로 만든다(아래 함정 주석).
  // ★7 -> 6. 이 셰이더는 **화면 전체를 덮는 판**에서 픽셀마다 SLOTS 번 도는 루프라
  //   슬롯 수가 곧 필레이트다(실측: 이펙트 전체가 4.44fps 를 먹는다). 6이면 한 스윙
  //   네 장 + 앞 스윙 잔여 두 장이 겹칠 수 있어 연타의 겹침은 그대로 산다.
  const SLOTS = 6;
  const mkCols = (n, hex) => { const a = []; for (let i = 0; i < n; i++) a.push(new THREE.Color(hex)); return a; };
  const mkThr = (n, t) => { const a = []; for (let i = 0; i < n; i++) a.push(new THREE.Vector3(t[0], t[1], t[2])); return a; };
  const mkNum = (n, v) => { const a = []; for (let i = 0; i < n; i++) a.push(v); return a; };
  const mkVec2 = (n) => { const a = []; for (let i = 0; i < n; i++) a.push(new THREE.Vector2()); return a; };
  const slashMat = new THREE.ShaderMaterial({
    transparent: true, depthTest: false, depthWrite: false, fog: false,
    blending: THREE.NormalBlending, side: THREE.DoubleSide,
    uniforms: {
      uAspect: { value: 1.78 },
      // ★배열 길이는 반드시 SLOTS 다. 예전에는 [1,1,1] 처럼 **손으로 세 개**를 적어
      //   뒀는데, SLOTS 를 5 로 올린 순간 uOff.value[3] 이 undefined 가 되어
      //   stroke() 의 `.set()` 에서 통째로 터졌다(게임 루프가 죽는다). 한 번 밟았다.
      uP: { value: mkNum(SLOTS, 1) },      // 진행도 0..1 (절차 폴백 전용. 1 = 다 끝남)
      uFrm: { value: mkNum(SLOTS, -1) },   // 시트 칸 번호 0..5 (음수 = 꺼짐)
      uCol: { value: mkNum(SLOTS, 0) },    // 시트 세로줄 0=가로베기 1=대각베기
      uFa: { value: mkNum(SLOTS, 1) },     // 프레임별 알파(계단)
      uAng: { value: mkNum(SLOTS, 0) },
      uOff: { value: mkVec2(SLOTS) },
      uLen: { value: mkNum(SLOTS, 1) },
      uThk: { value: mkNum(SLOTS, 0.1) },
      uSeed: { value: mkNum(SLOTS, 0) },
      uTex: { value: null },
      uUseTex: { value: 0 },               // 0 = 절차 폴백 / 1 = 플립북 시트
      // ★색은 **획마다 따로** 든다. 3연타로 벤 직후에 수면참으로 마무리하면 화면에
      //   진홍 획과 감청 획이 같이 떠 있어야 한다. 재질에 색 하나만 두면 나중에
      //   그은 획이 앞의 획 색까지 갈아치운다.
      //   배열 인덱스가 루프 변수라 GLSL ES 1.0 에서도 안전하다(동적 인덱싱 아님).
      uInk:  { value: mkCols(SLOTS, PAL_KILL.ink) },
      uEdge: { value: mkCols(SLOTS, PAL_KILL.edge) },
      uMid:  { value: mkCols(SLOTS, PAL_KILL.mid) },
      uCore: { value: mkCols(SLOTS, PAL_KILL.core) },
      uThr:  { value: mkThr(SLOTS, PAL_KILL.thr) },
    },
    vertexShader: `
      varying vec2 vUV;
      void main(){ vUV = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      varying vec2 vUV;
      uniform float uAspect;
      uniform float uP[${SLOTS}];
      uniform float uFrm[${SLOTS}];
      uniform float uCol[${SLOTS}];
      uniform float uFa[${SLOTS}];
      uniform float uAng[${SLOTS}];
      uniform vec2  uOff[${SLOTS}];
      uniform float uLen[${SLOTS}];
      uniform float uThk[${SLOTS}];
      uniform float uSeed[${SLOTS}];
      uniform sampler2D uTex;
      uniform float uUseTex;
      uniform vec3 uInk[${SLOTS}];
      uniform vec3 uEdge[${SLOTS}];
      uniform vec3 uMid[${SLOTS}];
      uniform vec3 uCore[${SLOTS}];
      uniform vec3 uThr[${SLOTS}];
      ${NOISE}
      void main(){
        // 화면 좌표: 가로가 긴 쪽으로 정규화(-aspect..aspect, -1..1)
        vec2 p = (vUV - 0.5) * 2.0;
        p.x *= uAspect;
        vec3 acc = vec3(0.0);
        float wsum = 0.0;
        float aA = 0.0;
        for (int i = 0; i < ${SLOTS}; i++) {
          float prog = uP[i];
          if (prog >= 1.0) continue;
          float c = cos(-uAng[i]), s = sin(-uAng[i]);
          vec2 d = p - uOff[i];
          vec2 q = vec2(d.x * c - d.y * s, d.x * s + d.y * c);
          q.x /= uLen[i];
          q.y /= uThk[i];
          if (abs(q.x) > 1.0) continue;
          float sd = uSeed[i];
          // ── 플립북 시트 ──
          // ★그림의 형태를 셰이더가 안 만든다. **구운 낱장을 그대로 얹는다.**
          //   그래서 여기서는 칸 좌표로 옮겨 뜨기만 하고 곧장 끝낸다.
          if (uUseTex > 0.5) {
            if (abs(q.y) > 1.0) continue;
            vec2 cuv = clamp(q * 0.5 + 0.5, 0.0015, 0.9985);
            // ★three 는 텍스처를 flipY 로 올린다. 시트는 위에서 아래로 f0..f5 라
            //   v 축에서 거꾸로(마지막 칸부터) 읽어야 f0 이 f0 으로 나온다.
            vec2 cell = vec2(uCol[i], ${(FLIP_N - 1).toFixed(1)} - uFrm[i]);
            vec2 uv = (cell + cuv) * vec2(${(1 / FLIP_C).toFixed(6)}, ${(1 / FLIP_N).toFixed(6)});
            vec4 tx = texture2D(uTex, uv);
            // 구운 시트는 **회색조**다. 밝기 네 단을 팔레트로 다시 칠한다.
            // (tools/bake_slash_flip.py 의 '밝기 계약' 참조. 먹 0.12 / 0.45 / 0.70 / 심 0.95)
            float lum = dot(tx.rgb, vec3(0.30, 0.59, 0.11));
            vec3 th2 = uThr[i];
            vec3 c2 = lum > th2.z ? uCore[i] : (lum > th2.y ? uMid[i] : (lum > th2.x ? uEdge[i] : uInk[i]));
            float a2 = tx.a * uFa[i];
            acc += c2 * a2; wsum += a2;
            aA = max(aA, min(1.0, a2));
            continue;
          }
          // 살짝 휜 붓. 중심선이 x^2 로 처진다(직선이면 자로 그은 티가 난다)
          float yc = 0.34 * q.x * q.x - 0.14;
          // 양끝이 뾰족하고 가장자리가 찢긴 두께
          float w = pow(max(0.0, 1.0 - q.x * q.x), 0.40);
          w *= 0.80 + 0.34 * noise(vec2(q.x * 5.2 + sd * 17.0, sd));
          float dd = abs(q.y - yc) / max(w, 1e-3);
          if (dd > 1.0) continue;
          // 스치고 지나간다: 머리가 앞서 나가고 꼬리가 따라 사라진다
          float head = mix(-1.25, 1.55, prog);
          float mask = smoothstep(head - 1.75, head - 1.05, q.x)
                     * (1.0 - smoothstep(head - 0.10, head + 0.02, q.x));
          if (mask <= 0.002) continue;
          float life = 1.0 - prog;
          vec3 cIn = uInk[i], cEd = uEdge[i], cMi = uMid[i], cCo = uCore[i];
          vec3 th = uThr[i];
          // ── 절차 폴백 ──
          // 시트를 못 읽었을 때만 여기까지 온다(파일이 빠진 배포본 대비).
          // 그때도 prog 는 1/24 로 끊어 넣으므로 계단감은 남는다.
          vec3 col;
          float a;
          float body = 1.0 - smoothstep(0.86, 1.0, dd);
          col = dd < 0.42 ? cCo : (dd < 0.86 ? cMi : cIn);
          a = body * mask * pow(life, 0.40) * 0.92;
          // ★색은 알파 가중 평균으로 모으고 알파는 제일 진한 획을 따른다.
          //   acc 에 col*a 를 그냥 더하면(가산합성 시절 코드) 칠하기에서는
          //   알파가 두 번 곱해져 획이 배경에 녹는다.
          acc += col * a; wsum += a;
          aA = max(aA, min(1.0, a));
        }
        // ★aA <= 0.004 이 아니라 !(aA > 0.004) 이다. NaN 은 모든 비교가 거짓이라
        //   앞의 형태로 쓰면 **NaN 이 discard 를 통과한다.** 통과한 NaN 은 HalfFloat
        //   HDR 버퍼에 찍히고, 블룸의 분리 블러가 그 한 픽셀을 사각형으로 번지게 해서
        //   화면 대부분을 한두 프레임 새까맣게 만든다(v88 QA '검은 번쩍'과 같은 기전.
        //   진범은 enemy.js 먹 파편이었고 여기는 같은 함정을 미리 막아 두는 것이다).
        if (!(aA > 0.004)) discard;
        gl_FragColor = vec4(acc / max(wsum, 1e-4), aA);
      }`,
  });
  const slashMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), slashMat);
  slashMesh.frustumCulled = false;
  slashMesh.renderOrder = 40;
  slashMesh.visible = false;
  scene.add(slashMesh);

  // ── 속도선(찢김선) ──
  // ★v91. 방사형 바퀴살에서 **벤 방향으로 찢어지는 선**으로 바꿨다.
  //   방사형은 "무언가 터졌다"고만 말하고 어디를 어떻게 벴는지는 말하지 않는다.
  //   귀멸의 타격 컷은 벤 축을 따라 종이가 찢긴 것처럼 선이 뻗는다. 그래서
  //   타격점을 원점으로 두고 **벤 각도로 회전한 좌표**에서 가로로만 뻗게 그린다.
  // ★색: 가산합성 흰 선이 아니라 **먹선**이다. 이 맵은 아침 산야(밝은 흙)라
  //   흰 선은 배경에 녹아 사라진다(붓자국·전멸 링이 같은 이유로 칠하기로 갔다).
  const lineMat = new THREE.ShaderMaterial({
    transparent: true, depthTest: false, depthWrite: false, fog: false,
    blending: THREE.NormalBlending, side: THREE.DoubleSide,
    uniforms: { uAspect: { value: 1.78 }, uP: { value: 1 }, uSeed: { value: 0 },
                uAng: { value: 0 }, uAt: { value: new THREE.Vector2() },
                uLong: { value: 0 },
                uCol: { value: new THREE.Color(0x141a2e) } },
    vertexShader: `
      varying vec2 vUV;
      void main(){ vUV = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      varying vec2 vUV;
      uniform float uAspect; uniform float uP; uniform float uSeed; uniform vec3 uCol;
      uniform float uAng; uniform vec2 uAt; uniform float uLong;
      ${NOISE}
      void main(){
        if (uP >= 1.0) discard;
        vec2 p = (vUV - 0.5) * 2.0;
        p.x *= uAspect;
        // 타격점을 원점으로, 벤 방향을 x 축으로
        vec2 d = p - uAt;
        float c = cos(-uAng), s = sin(-uAng);
        vec2 q = vec2(d.x * c - d.y * s, d.x * s + d.y * c);
        // 줄 번호(벤 축과 나란한 줄이 촘촘히 깔린다). 고르면 빗금이 되니 난수로 흩는다
        // ★v94. 17 -> 27. 성긴 검은 막대 몇 개는 배경에 꽂힌 **말뚝**으로 읽힌다(심사 인용).
        //   같은 자리에 촘촘히 여러 줄이 있어야 '결'로 읽힌다.
        // ★v96. 27 -> 34. 뻗는 길이를 절반으로 줄이면서(아래 outer) 줄 간격까지 그대로
        //   두면 짧은 막대 몇 개가 되어 다시 말뚝이 된다. 짧아진 만큼 촘촘해야 한다.
        // ★v97. 34 -> 42. 오너 "너무 줄였다". 수렴형(v96 이 얻은 모양)은 그대로 두고
        //   **개수와 굵기만** 되돌린다 - 결은 촘촘할수록 '찢김'으로 읽힌다.
        float k = q.y * (42.0 + 18.0 * uLong) + uSeed;
        float cell = floor(k);
        float f = fract(k) - 0.5;
        float rnd = hash(vec2(cell, uSeed));
        // 타격점 언저리는 비우고 바깥으로 찢겨 나간다
        float ax = abs(q.x);
        float inner = 0.09 + rnd * 0.15;
        // ★v94. 길이를 0.62배로 줄였다(심사 "속선이 3D 말뚝"). 화면을 가로지르는
        //   길이의 검은 막대는 배경에 꽂힌 물체로 읽힌다. 획에 딸린 결이려면
        //   **본 획 길이 언저리**에서 끝나야 한다.
        // ★v96. 다시 0.55배(총 0.34배). 오너 지시 "칼 근처에서만". 본 획이 이제 칼에
        //   붙은 가는 호 하나뿐이라, 속도선이 전화면으로 뻗으면 그게 곧 화면을 덮는 것이다.
        // ★v97. 마지막 배수 0.34 -> 0.46. 본 획이 다시 굵어졌으므로(main.js STRAND_CFG)
        //   결도 그 획 언저리까지는 뻗어야 '획에 딸린 결'이 된다. 화면을 가로지르진 않는다.
        float outer = (0.50 + rnd * 0.60) * (0.62 + 0.95 * uLong) * (0.58 + uP * 0.62) * 0.46;
        // ★선 끝을 알파로 흐리면 '모션블러 얼룩'이 된다(실측 1회). 애니의 속도선은
        //   **굵기가 뾰족해지며** 끝난다. 그래서 알파는 계단으로 끊고 두께를 좁힌다.
        // ★v96. 균일 두께 평행 막대(양끝만 뾰족)에서 **타격점으로 수렴하는** 결로 바꿨다.
        //   안쪽 끝(타격점 쪽)이 실오라기이고 바깥으로 갈수록 굵어졌다가 끝에서 뜯긴다.
        //   그래야 눈이 선을 따라 타격점으로 끌려 들어간다(오너 지시 6항).
        float sN = clamp((ax - inner) / max(outer - inner, 1e-4), 0.0, 1.0);
        float tap = pow(sN, 0.75) * (1.0 - smoothstep(0.70, 1.0, sN));
        // ★v97. (0.05 + rnd*0.11) -> (0.07 + rnd*0.15). 수렴 모양은 그대로, 굵기만 보강.
        float thick = (0.07 + rnd * 0.15) * (0.06 + 0.94 * tap);
        float line = 1.0 - smoothstep(thick * 0.72, thick, abs(f));
        float span = step(inner, ax) * (1.0 - step(outer, ax));
        // 벤 축에서 멀어질수록 줄이 **성겨진다**(흐려지는 게 아니라 개수가 준다).
        // 줄마다 제 난수를 문턱과 견줘 있거나 없거나 둘 중 하나로 만든다.
        // ★v94. 퍼짐 폭을 절반으로 조였다(1.05 -> 0.58). 벤 축에서 멀리 떨어져 홀로 뜬
        //   검은 선은 어디에도 안 붙어 보여서 지면에 꽂힌 물체가 된다.
        // ★v96. 0.58 -> 0.34. 길이를 줄인 만큼 폭도 같이 줄여야 '한 다발'로 읽힌다.
        // ★v97. 0.34 -> 0.44. 다발이 굵어진 본 획을 감싸야 한다(길이와 같이 움직인다).
        float band = 1.0 - smoothstep(0.15 + 0.22 * uLong, 0.44 + 0.34 * uLong, abs(q.y));
        float exist = step(hash(vec2(cell + 3.7, uSeed + 1.3)) * 0.92, band);
        float life = 1.0 - uP * 0.25;
        float a = line * span * exist * life * (0.60 + 0.18 * uLong);
        if (!(a > 0.004)) discard;      // ★NaN 도 걸러내는 형태(위 붓자국과 같은 이유)
        gl_FragColor = vec4(uCol, a);
      }`,
  });
  const lineMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), lineMat);
  lineMesh.frustumCulled = false;
  // ★v94. 41 -> 39. 속도선은 본 획 **아래**에 깔린다. 위에 얹으면 획을 가로지르는
  //   검은 막대가 되어 획의 형태를 부순다(심사 "3D 말뚝"의 절반이 이 순서 문제였다).
  lineMesh.renderOrder = 39;
  lineMesh.visible = false;
  scene.add(lineMesh);

  // ═══════════════════════════════════════════════════════════════════════
  // 임팩트 프레임 (v91) — ★지금은 꺼져 있다(IMPACT_CUT = 0, 17차 오너 지시).
  // 아래 규칙과 셰이더는 되살릴 때를 위해 그대로 둔다. 켜는 문은 그 상수 하나다.
  //
  // 무엇인가: 애니에서 칼이 닿는 그 순간에 딱 **한 장** 끼워 넣는 극단 대비 컷이다.
  //   화면이 종이색으로 뒤집히고 그 위에 먹 실루엣만 남는다. 다음 프레임에 사라진다.
  // ★규칙 3 이 "페이드가 있으면 플래시가 된다"고 적어 뒀는데, 실측해 보니 페이드가
  //   없어도 플래시였다. 60fps 한 장은 그림으로 안 읽히고 밝기 계단으로만 남는다.
  //
  // ★규칙 세 가지. 하나라도 어기면 이건 연출이 아니라 **버그로 보인다.**
  //   1) 정확히 1프레임(전멸·보스는 2). 시간(ms)이 아니라 **렌더 프레임 수**로 센다.
  //      updateOverlay 가 composer.render() 직전에 프레임당 한 번 불리는 것을 이용한다.
  //   2) **흰색 기조.** 풀스크린 검정은 금지다. v88 의 'NaN 검은 번쩍' 사고와
  //      한 화면에서 구별이 안 되면 오너는 이걸 버그로 읽는다. 종이색 바탕이라야
  //      "일부러 넣은 컷"으로 읽힌다.
  //   3) 반투명 금지. 계단(step)으로만 칠한다. 페이드가 있으면 플래시가 된다.
  const IMP_PAPER = 0xf4eee0;   // 종이색(누런 흰빛). 순백은 눈이 아프고 톤도 안 맞는다
  const IMP_INK = 0x0b0a10;     // 먹
  const impMat = new THREE.ShaderMaterial({
    transparent: true, depthTest: false, depthWrite: false, fog: false,
    blending: THREE.NormalBlending, side: THREE.DoubleSide,
    uniforms: {
      uAspect: { value: 1.78 }, uSeed: { value: 0 },
      uAt: { value: new THREE.Vector2() }, uAng: { value: 0 },
      uLen: { value: 0.3 }, uThk: { value: 0.2 }, uCol: { value: 0 }, uFrm: { value: 2 },
      uTex: { value: null }, uHasTex: { value: 0 }, uBig: { value: 0 },
      uPaper: { value: new THREE.Color(IMP_PAPER) },
      uInk: { value: new THREE.Color(IMP_INK) },
    },
    vertexShader: `
      varying vec2 vUV;
      void main(){ vUV = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      varying vec2 vUV;
      uniform float uAspect; uniform float uSeed;
      uniform vec2 uAt; uniform float uAng; uniform float uLen; uniform float uThk;
      uniform float uCol; uniform float uFrm; uniform float uBig;
      uniform sampler2D uTex; uniform float uHasTex;
      uniform vec3 uPaper; uniform vec3 uInk;
      ${NOISE}
      void main(){
        vec2 p = (vUV - 0.5) * 2.0;
        p.x *= uAspect;
        vec2 d = p - uAt;
        float c = cos(-uAng), s = sin(-uAng);
        vec2 q = vec2(d.x * c - d.y * s, d.x * s + d.y * c);
        float ink = 0.0;
        // 1) 방금 그은 참격을 **통짜 먹**으로 한 번 더 찍는다(색이 아니라 실루엣이다)
        if (uHasTex > 0.5) {
          vec2 t2 = vec2(q.x / (uLen * 1.35), q.y / (uThk * 1.35));
          if (abs(t2.x) < 1.0 && abs(t2.y) < 1.0) {
            vec2 cuv = clamp(t2 * 0.5 + 0.5, 0.0015, 0.9985);
            vec2 cell = vec2(uCol, ${(FLIP_N - 1).toFixed(1)} - uFrm);
            vec4 tx = texture2D(uTex, (cell + cuv) * vec2(${(1 / FLIP_C).toFixed(6)}, ${(1 / FLIP_N).toFixed(6)}));
            ink = max(ink, step(0.35, tx.a));
          }
        }
        // 2) 벤 방향으로 찢긴 굵은 선 몇 가닥
        // ★굵기는 **줄 간격에 대한 비율**이다. 0.16+0.26 으로 뒀더니 한 줄이 간격의
        //   84% 를 먹어 화면이 바코드가 됐다(실측 1회). 12~26% 가 '찢긴 선'이다.
        float k = q.y * 11.0 + uSeed;
        float rnd = hash(vec2(floor(k), uSeed));
        float f = fract(k) - 0.5;
        float lw = 0.06 + rnd * 0.14;
        float line = 1.0 - step(lw, abs(f));
        float ax = abs(q.x);
        float outer = (0.45 + rnd * 0.70) * (0.80 + 0.50 * uBig);
        float span = step(0.09 + rnd * 0.13, ax) * (1.0 - step(outer, ax));
        ink = max(ink, line * span * (1.0 - step(0.85 + 0.45 * uBig, abs(q.y))));
        // 3) 화면 **모서리**만 먹. 거친 종이를 찢어 붙인 것처럼 들쭉날쭉해야 한다.
        //    ★문턱이 낮으면 테두리가 화면 5분의 1을 먹고 '검은 화면'이 된다(금지 사항).
        //    16:9 에서 r 은 가운데 0 · 좌우 끝 1.10 · 모서리 1.49 다.
        float r = length(p * vec2(0.62, 1.0));
        float ragged = r + 0.11 * noise(p * 3.1 + uSeed) + 0.10 * noise(p * 9.5 - uSeed);
        ink = max(ink, step(1.40 - 0.05 * uBig, ragged));
        // ★계단으로만 칠한다. mix 로 섞으면 회색이 생기고 그 순간 '흐릿한 플래시'가 된다
        vec3 col = mix(uPaper, uInk, step(0.5, ink));
        gl_FragColor = vec4(col, 1.0);
      }`,
  });
  const impMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), impMat);
  impMesh.frustumCulled = false;
  impMesh.renderOrder = 60;         // 다른 화면 겹(40·41)보다 위. 이 프레임은 이게 전부다
  impMesh.visible = false;
  scene.add(impMesh);

  // 임팩트 프레임에 **사람 형태**를 남기는 재질. 은신 실루엣의 껍데기를 그대로 빌려
  // 깊이 비교 없이 통짜 먹으로 한 번 그린다(= 종이 위에 검은 사람이 선다).
  const impInkMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(IMP_INK), fog: false,
    transparent: true, depthTest: false, depthWrite: false, side: THREE.FrontSide,
  });

  // ═══════════════════════════════════════════════════════════════════════
  // 타격 지점 참격 (v92) — 옛 가산합성 초승달의 자리
  //
  // main.js 는 명중한 그 지점에 **초승달**(AdditiveBlending)을 하나 띄우고 있었다.
  // 그 문법이 이 화면에 남은 마지막 60fps CG 조각이었다: 매끈하게 벌어지고,
  // 겹치면 흰색으로 타고, 잉크 테두리를 원리상 못 그린다.
  // 여기서는 **같은 시트(slash_flip.png)를 월드에 눕혀** 재생한다.
  //   · 화면 겹 붓자국 = "이만큼 베었다"   (크다. 화면 좌표에 앉는다)
  //   · 이 한 장       = "여기서 갈라졌다" (작다. 요괴 가슴께 월드 좌표에 선다)
  // ★가산합성을 안 쓴다. 아침 산야(밝은 흙) 위에서 흰 심이 그대로 날아가 '칼 빔'이
  //   되기 때문이다(붓자국·전멸 링이 같은 이유로 칠하기로 갔다). 시트의 밝기 네 단을
  //   팔레트로 다시 칠한다 - 먹 / 색 / 밝은 색 / 흰 심. 흰 심은 남으므로 임팩트의
  //   **흰 기조**는 그대로다. 달라진 건 그 흰빛에 먹 테두리가 붙는다는 것뿐이다.
  // ★프레임은 1/24 로 끊어 넘어간다. 그리고 **게임시계로 늙는다** - 히트스톱 동안
  //   한 장을 붙들고 있다가 풀리면서 이어진다(옛 초승달이 게임 dt 로 늙던 성질 그대로.
  //   실제 시간으로 돌리면 멈춰 있는 사이에 혼자 다 지나가 버린다).
  // ★메시를 늘 켜 둔다(visible=true). 알파 0 이면 프래그먼트가 전부 discard 라
  //   화면에는 아무것도 안 나오지만 **셰이더 프로그램은 첫 프레임에 구워진다.**
  //   = 첫 타격의 컴파일 히치가 구조적으로 안 생긴다(옛 arcMesh 가 갖고 있던 성질).
  const IMPF_MAX = 8;          // 동시에 떠 있을 수 있는 장 수(옛 ARC_MAX 와 같다)
  // ★v96. 0.95 -> 0.64 / 0.52 -> 0.35. **비를 그대로 두고 크기만 줄였다** — 그림은
  //   한 픽셀도 안 바뀌고(합격작 보존) 요괴를 통째로 덮던 것만 없어진다.
  //   실측(v95): 획 전체 길이 1.9m x size 0.95 = 1.80m 인데 요괴 키가 1.30m 라
  //   "무엇을 벴는지" 자체가 안 보였다(오너 지시 8항). 지금은 1.22m 로 요괴 안에 든다.
  // ★v97. 0.64 -> 0.80 / 0.35 -> 0.44. 여기도 **비는 그대로**다(합격작 무수정 계약).
  //   오너 "너무 줄였다"에 맞춘 중간점 - 9차 0.95 와 10차 0.64 사이. 획 전체 길이는
  //   1.52m 라 요괴(키 1.30m)를 아직 안 덮는다(10차가 닫은 지적을 다시 열지 않는다).
  const IMPF_LEN = 0.80;       // size 1 일 때 획 반길이(m)
  const IMPF_THK = 0.44;       // size 1 일 때 칸 반높이(m). 그림의 획은 이 안쪽 0.375
  const IMPF_N_KILL = 6;       // 처치는 시트 여섯 장 전부(0.25초)
  const IMPF_N_HIT = 4;        // 안 죽인 명중은 네 장(0.167초)에서 끊는다
  // 장별 알파도 계단이다. 처치는 진하게 시작해 끊고, 명중은 처음부터 옅다
  // (스친 한 대가 처치와 같은 무게로 보이면 처치의 한 획이 값을 잃는다).
  const IMPF_A_KILL = [1.0, 1.0, 1.0, 0.90, 0.72, 0.46];
  const IMPF_A_HIT = [0.78, 0.78, 0.58, 0.36];
  const impfGeo = new THREE.BufferGeometry();
  const ifPos = new Float32Array(IMPF_MAX * 4 * 3);
  const ifUV = new Float32Array(IMPF_MAX * 4 * 2);
  const ifA = new Float32Array(IMPF_MAX * 4);
  const ifFrm = new Float32Array(IMPF_MAX * 4);
  const ifCol = new Float32Array(IMPF_MAX * 4);
  const ifKill = new Float32Array(IMPF_MAX * 4);
  const ifIdx = [];
  for (let i = 0; i < IMPF_MAX; i++) {
    const o = i * 4;
    ifIdx.push(o, o + 1, o + 2, o, o + 2, o + 3);
    // 칸 안 좌표. 아래왼쪽부터 시계반대(획의 길이축이 x)
    ifUV[o * 2] = 0; ifUV[o * 2 + 1] = 0;
    ifUV[(o + 1) * 2] = 1; ifUV[(o + 1) * 2 + 1] = 0;
    ifUV[(o + 2) * 2] = 1; ifUV[(o + 2) * 2 + 1] = 1;
    ifUV[(o + 3) * 2] = 0; ifUV[(o + 3) * 2 + 1] = 1;
  }
  impfGeo.setAttribute('position', new THREE.BufferAttribute(ifPos, 3));
  impfGeo.setAttribute('aUV', new THREE.BufferAttribute(ifUV, 2));
  impfGeo.setAttribute('aAlpha', new THREE.BufferAttribute(ifA, 1));
  impfGeo.setAttribute('aFrm', new THREE.BufferAttribute(ifFrm, 1));
  impfGeo.setAttribute('aCol', new THREE.BufferAttribute(ifCol, 1));
  impfGeo.setAttribute('aKill', new THREE.BufferAttribute(ifKill, 1));
  impfGeo.setIndex(ifIdx);
  const impfMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: false, fog: false,
    blending: THREE.NormalBlending, side: THREE.DoubleSide,
    uniforms: {
      uTex: { value: null }, uHasTex: { value: 0 },
      // 색은 두 벌만 든다(처치 진홍 / 물 감청). 획마다 aKill 로 고른다.
      uInkK: { value: new THREE.Color(PAL_KILL.ink) },
      uEdgeK: { value: new THREE.Color(PAL_KILL.edge) },
      uMidK: { value: new THREE.Color(PAL_KILL.mid) },
      uCoreK: { value: new THREE.Color(PAL_KILL.core) },
      uThrK: { value: new THREE.Vector3(PAL_KILL.thr[0], PAL_KILL.thr[1], PAL_KILL.thr[2]) },
      uInkW: { value: new THREE.Color(PAL_WATER.ink) },
      uEdgeW: { value: new THREE.Color(PAL_WATER.edge) },
      uMidW: { value: new THREE.Color(PAL_WATER.mid) },
      uCoreW: { value: new THREE.Color(PAL_WATER.core) },
      uThrW: { value: new THREE.Vector3(PAL_WATER.thr[0], PAL_WATER.thr[1], PAL_WATER.thr[2]) },
    },
    vertexShader: `
      attribute vec2 aUV; attribute float aAlpha; attribute float aFrm;
      attribute float aCol; attribute float aKill;
      varying vec2 vUV; varying float vA; varying float vFrm; varying float vCol; varying float vK;
      void main(){ vUV = aUV; vA = aAlpha; vFrm = aFrm; vCol = aCol; vK = aKill;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      varying vec2 vUV; varying float vA; varying float vFrm; varying float vCol; varying float vK;
      uniform sampler2D uTex; uniform float uHasTex;
      uniform vec3 uInkK; uniform vec3 uEdgeK; uniform vec3 uMidK; uniform vec3 uCoreK; uniform vec3 uThrK;
      uniform vec3 uInkW; uniform vec3 uEdgeW; uniform vec3 uMidW; uniform vec3 uCoreW; uniform vec3 uThrW;
      void main(){
        // ★!(vA > x) 꼴이다. NaN 은 모든 비교가 거짓이라 (vA <= x) 로 쓰면
        //   NaN 이 discard 를 통과해 HDR 버퍼에 찍히고 블룸이 그 한 점을
        //   사각형으로 번지게 한다(v88 '검은 번쩍'과 같은 기전).
        if (!(vA > 0.004)) discard;
        float k = step(0.5, vK);
        vec3 cInk = mix(uInkW, uInkK, k);
        vec3 cEdge = mix(uEdgeW, uEdgeK, k);
        vec3 cMid = mix(uMidW, uMidK, k);
        vec3 cCore = mix(uCoreW, uCoreK, k);
        vec3 th = mix(uThrW, uThrK, k);
        if (uHasTex < 0.5) {
          // ── 절차 폴백 ── 시트를 못 읽었을 때만 온다(획 하나를 손으로 그린다).
          vec2 q = vUV * 2.0 - 1.0;
          float w = pow(max(0.0, 1.0 - q.x * q.x), 0.40) * 0.72;
          float d = abs(q.y - (0.34 * q.x * q.x - 0.14)) / max(w, 1e-3);
          if (d > 1.0) discard;
          vec3 cf = d < 0.42 ? cCore : (d < 0.86 ? cMid : cInk);
          gl_FragColor = vec4(cf, vA);
          return;
        }
        // ★three 는 텍스처를 flipY 로 올린다. 시트는 위에서 아래로 f0..f5 라
        //   v 축에서 거꾸로(마지막 칸부터) 읽어야 f0 이 f0 으로 나온다.
        vec2 cuv = clamp(vUV, 0.0015, 0.9985);
        vec2 cell = vec2(vCol, ${(FLIP_N - 1).toFixed(1)} - vFrm);
        vec4 tx = texture2D(uTex, (cell + cuv) * vec2(${(1 / FLIP_C).toFixed(6)}, ${(1 / FLIP_N).toFixed(6)}));
        float a = tx.a * vA;
        if (!(a > 0.004)) discard;
        // 구운 시트는 회색조다. 밝기 네 단을 팔레트로 다시 칠한다
        // (tools/bake_slash_flip.py 의 '밝기 계약'. 먹 0.12 / 0.45 / 0.70 / 심 0.95)
        float lum = dot(tx.rgb, vec3(0.30, 0.59, 0.11));
        vec3 c = lum > th.z ? cCore : (lum > th.y ? cMid : (lum > th.x ? cEdge : cInk));
        gl_FragColor = vec4(c, a);
      }`,
  });
  const impfMesh = new THREE.Mesh(impfGeo, impfMat);
  impfMesh.frustumCulled = false;
  impfMesh.renderOrder = 12;        // 궤적(3)·물보라(5) 위, 화면 겹(40+) 아래
  scene.add(impfMesh);
  const impfs = [];                 // {p, ang, t, n, size, col, kill}
  const _ifR = new THREE.Vector3(), _ifU = new THREE.Vector3();
  const _ifL = new THREE.Vector3(), _ifT = new THREE.Vector3(), _ifQ = new THREE.Vector3();
  const IMPF_CORNER = [[-1, -1], [1, -1], [1, 1], [-1, 1]];

  // 맞은 자리에 참격 한 장. ang = 화면 각도(라디안) / size = 크기(m) / kind = 'kill'|'water'
  function impactSlash(x, y, z, ang, size, kind) {
    if (impfs.length >= IMPF_MAX) impfs.shift();
    const kill = kind === 'kill' ? 1 : 0;
    impfs.push({
      p: new THREE.Vector3(x, y, z), ang, t: 0,
      n: kill ? IMPF_N_KILL : IMPF_N_HIT,
      // ★v97. 커진 것은 **처치의 진홍 초승달뿐**이다(오너 지시 "0.64 -> 0.80 안팎").
      //   안 죽인 명중까지 같이 키우면 일격기 한 대가 1.5m 짜리 판때기가 되어
      //   "무엇을 벴는지 안 보인다"는 지적이 다시 열린다(실측 크롭 x_sumen).
      //   0.82 를 곱하면 처치 아닌 장은 v96 크기 그대로다.
      size: (size || 1) * (kill ? 1.0 : 0.82),
      // 획 종류: 화면에서 수평에 가까우면 가로베기 칸, 아니면 대각베기 칸
      // (붓자국 stroke() 와 같은 규칙이라 두 그림의 휨이 서로 안 어긋난다)
      col: Math.abs(Math.sin(ang)) < FLIP_H_SIN ? 0 : 1,
      kill,
    });
  }

  // 게임시간(히트스톱이 걸리면 같이 멈추는 시계)으로 늙힌다.
  function updateImpactSlashes(dtGame) {
    for (let i = impfs.length - 1; i >= 0; i--) {
      impfs[i].t += dtGame;
      if (Math.floor(impfs[i].t / FRAME_T) >= impfs[i].n) impfs.splice(i, 1);
    }
    _ifR.setFromMatrixColumn(camera.matrixWorld, 0);
    _ifU.setFromMatrixColumn(camera.matrixWorld, 1);
    for (let i = 0; i < IMPF_MAX; i++) {
      const o = i * 4;
      if (i >= impfs.length) { for (let k = 0; k < 4; k++) ifA[o + k] = 0; continue; }
      const s = impfs[i];
      const fr = Math.floor(s.t / FRAME_T);
      const lad = s.kill ? IMPF_A_KILL : IMPF_A_HIT;
      const a = lad[Math.min(fr, lad.length - 1)];
      const cs = Math.cos(s.ang), sn = Math.sin(s.ang);
      // 획의 길이축 · 두께축(카메라 평면 안에서 벤 각도로 돌린다)
      _ifL.copy(_ifR).multiplyScalar(cs).addScaledVector(_ifU, sn)
          .multiplyScalar(s.size * IMPF_LEN);
      _ifT.copy(_ifR).multiplyScalar(-sn).addScaledVector(_ifU, cs)
          .multiplyScalar(s.size * IMPF_THK);
      for (let k = 0; k < 4; k++) {
        _ifQ.copy(s.p).addScaledVector(_ifL, IMPF_CORNER[k][0])
            .addScaledVector(_ifT, IMPF_CORNER[k][1]);
        ifPos[(o + k) * 3] = _ifQ.x; ifPos[(o + k) * 3 + 1] = _ifQ.y; ifPos[(o + k) * 3 + 2] = _ifQ.z;
        ifA[o + k] = a;
        ifFrm[o + k] = fr;
        ifCol[o + k] = s.col;
        ifKill[o + k] = s.kill;
      }
    }
    impfGeo.attributes.position.needsUpdate = true;
    impfGeo.attributes.aAlpha.needsUpdate = true;
    impfGeo.attributes.aFrm.needsUpdate = true;
    impfGeo.attributes.aCol.needsUpdate = true;
    impfGeo.attributes.aKill.needsUpdate = true;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 타격 팝 (v94 신설) — "안 죽는 적은 리본이 그냥 통과한다" 대응
  //
  // 심사 격차 4: 처치에는 백색 패널·진홍 초승달·찢김선이 다 붙는데, **안 죽는 한 대**에는
  // 리본이 몸을 지나갈 뿐이라 맞았다는 그림이 없다. 귀멸은 안 죽는 한 대에도
  // 접점에서 흰 것이 한 번 번쩍하고 먹이 튄다. 그 두 장을 여기서 그린다.
  //   f0 : 흰 번쩍 — 불규칙한 흰 덩어리 + 굵은 먹 테두리 (형태를 정의하는 건 테두리다)
  //   f1 : 먹 튀김 — 접점에서 방사로 튄 먹 방울 몇 개 (흰 심을 한 점씩 남긴다)
  // ★1~2프레임(24fps 기준 0.042~0.083초)만 산다. 지속 계약의 정신 그대로,
  //   "명중을 알리는 것"이지 "화면을 덮는 것"이 아니다.
  // ★게임시계로 늙는다(히트스톱 중에는 한 장을 붙들고 있다). 실제 시간으로 돌리면
  //   멈춘 45~105ms 사이에 두 장이 혼자 다 지나가 아무도 못 본다.
  // ★텍스처가 없다. 절차로 그린다 - 시트를 한 장 더 굽는 것보다 확실하고, 이 그림은
  //   형태가 단순해서(덩어리 + 테두리 + 방울) 절차로도 손그림처럼 나온다.
  const POP_MAX = 12;
  // 오너가 기각한 것은 '사방으로 튀는 낱알'이라는 그림 자체다. 새 포말 마루가 켜진
  // 판에서는 f0 접점 붓획만 남기고 f1 방울은 재생하지 않는다. 롤백 상수를 0 으로
  // 내리면 기존 두 장 경로가 그대로 살아난다(아래 f1 셰이더도 지우지 않았다).
  const POP_N = FOAM_CREST_V2 ? 1 : 2;
  // ★v96. 0.62 -> 0.44. 아래 먹 테두리를 좁히면서 크기도 같이 줄인다(오너 지시 7항).
  const POP_SIZE = 0.44;           // size 1 일 때 반지름(m)
  const popGeo = new THREE.BufferGeometry();
  const pPos = new Float32Array(POP_MAX * 4 * 3);
  const pUV = new Float32Array(POP_MAX * 4 * 2);
  const pA = new Float32Array(POP_MAX * 4);
  const pFrm = new Float32Array(POP_MAX * 4);
  const pSeed = new Float32Array(POP_MAX * 4);
  const pIdx = [];
  for (let i = 0; i < POP_MAX; i++) {
    const o = i * 4;
    pIdx.push(o, o + 1, o + 2, o, o + 2, o + 3);
    pUV[o * 2] = 0; pUV[o * 2 + 1] = 0;
    pUV[(o + 1) * 2] = 1; pUV[(o + 1) * 2 + 1] = 0;
    pUV[(o + 2) * 2] = 1; pUV[(o + 2) * 2 + 1] = 1;
    pUV[(o + 3) * 2] = 0; pUV[(o + 3) * 2 + 1] = 1;
  }
  popGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  popGeo.setAttribute('aUV', new THREE.BufferAttribute(pUV, 2));
  popGeo.setAttribute('aAlpha', new THREE.BufferAttribute(pA, 1));
  popGeo.setAttribute('aFrm', new THREE.BufferAttribute(pFrm, 1));
  popGeo.setAttribute('aSeed', new THREE.BufferAttribute(pSeed, 1));
  popGeo.setIndex(pIdx);
  const popMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: false, fog: false,
    blending: THREE.NormalBlending, side: THREE.DoubleSide,
    uniforms: {
      uWht: { value: new THREE.Color(0xf6f2e8) },     // 종이 흰빛(순백은 눈이 아프다)
      uInk: { value: new THREE.Color(0x0b0a10) },     // 먹
      // ★v99(11-FX-B). 감청(물빛). 먹 튀김 방울의 다수를 이 색으로 돌린다.
      //   ★값이 #186095 가 아니라 #56A5C9 인 데 이유가 있다. main.js 의 물 팔레트는
      //     hex 를 255 로 나눠 **선형 그대로** 셰이더에 넣는데, THREE.Color(hex) 는
      //     sRGB 로 읽어 선형으로 변환한다(r160 ColorManagement 기본 on).
      //     그래서 같은 화면색을 내려면 여기 값은 팔레트 hex 를 sRGB 인코딩한 것이어야
      //     한다(#186095 를 선형으로 보고 sRGB 로 되감으면 #56A5C9). 같은 hex 를
      //     그대로 적으면 화면에서 거의 검정이 된다.
      uWat: { value: new THREE.Color(0x56A5C9) },
    },
    vertexShader: `
      attribute vec2 aUV; attribute float aAlpha; attribute float aFrm; attribute float aSeed;
      varying vec2 vUV; varying float vA; varying float vFrm; varying float vSd;
      void main(){ vUV = aUV; vA = aAlpha; vFrm = aFrm; vSd = aSeed;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      varying vec2 vUV; varying float vA; varying float vFrm; varying float vSd;
      uniform vec3 uWht; uniform vec3 uInk; uniform vec3 uWat;
      float h1(float x){ return fract(sin(x * 127.1) * 43758.5453); }
      void main(){
        // ★!(vA > x) 꼴. NaN 은 모든 비교가 거짓이라 (vA <= x) 로 쓰면 NaN 이
        //   discard 를 통과해 HDR 버퍼에 찍히고 블룸이 사각형으로 번지게 한다.
        if (!(vA > 0.004)) discard;
        vec2 q = vUV * 2.0 - 1.0;
        float r = length(q);
        if (vFrm < 0.5) {
          if (${FOAM_CREST_V2 ? 'true' : 'false'}) {
            // ── R2 f0. 접점 붓획 ── f1 제거 뒤 홀로 남은 흰 원판을 3:1의 짧고
            // 찢긴 붓자국으로 바꾼다. 팝마다 기울기·가장자리 결을 달리해 UI 대시도 피한다.
            float ta = (h1(vSd * 2.9 + 0.7) - 0.5) * 2.4;
            vec2 e = vec2(q.x * cos(ta) + q.y * sin(ta),
                          -q.x * sin(ta) + q.y * cos(ta));
            float ax = abs(e.x);
            if (ax > 0.92) discard;
            float taper = pow(max(0.0, 1.0 - ax / 0.92), 0.56);
            float grain = (h1(floor((e.x + 1.0) * 11.0) + vSd * 5.3) - 0.5) * 0.055;
            float bend = 0.045 * sin(e.x * 5.7 + vSd);
            float outer = 0.055 + 0.245 * taper + grain;
            float ey = abs(e.y - bend);
            if (ey > outer) discard;
            float rim = 0.050 + 0.018 * h1(floor(e.x * 13.0) + vSd * 7.1);
            bool ink = ey > max(0.0, outer - rim) || ax > 0.82;
            gl_FragColor = vec4(ink ? uInk : uWht, 1.0);
          } else {
            // 롤백 경로: R1 이전의 불규칙 흰 덩어리를 그대로 보존한다.
            float th = atan(q.y, q.x);
            float a1 = h1(floor(th * 2.5465 + vSd) + vSd * 3.1);
            float a2 = h1(floor(th * 1.2732 + vSd * 2.0) + vSd * 7.7);
            float R = 0.50 + 0.34 * a2 + 0.16 * a1;
            if (r > R) discard;
            gl_FragColor = vec4(r > R * 0.88 ? uInk : uWht, 1.0);
          }
          return;
        }
        // ── f1. 먹 튀김 ── 접점에서 방사로 튄 방울.
        // ★★v99(11-FX-B). LOG 의 "어두운 테두리 + 한가운데 흰 점 = 눈알" 함정이
        //   **접점 자국에 그대로 남아 있었다**: r<0.17 먹 원판 안에 r<0.075 흰 점.
        //   판정 시트 v98 열 Z1 칸 임팩트 한가운데의 그 눈알이 이것이다.
        //   v96 은 f0 번쩍에서, v97 은 방울 속에서 같은 지적을 닫았는데 접점만 남았다.
        //   → 흰 점을 빼고, 접점 자국을 **원판이 아니라 짧은 획**으로 바꾼다.
        //     원판은 크기를 아무리 줄여도 눈이 된다(모양이 문제지 크기가 아니다).
        // ★같이: 방울 일곱 중 순먹은 둘쯤만 남기고 나머지를 **감청 몸 + 흰 꼬리 쉼표**로
        //   돌린다. 순먹 방울이 밝은 모래 위에 흩어지면 그 무리 자체가 검은 타원 떼로
        //   읽힌다(오너 판정지 지적). 물의 호흡이 튀긴 것이니 물색이 다수인 쪽이 맞다.
        float ink = 0.0, wat = 0.0, tip = 0.0;
        for (int k = 0; k < 7; k++) {
          float fk = float(k);
          float ang = (fk + h1(fk * 3.3 + vSd)) * 0.8976;             // 2pi/7 언저리에 흩음
          float dist = 0.40 + 0.52 * h1(fk * 5.1 + vSd * 2.3);
          // ★v97. 0.10+0.11 -> 0.062+0.072. 심을 빼서 속을 채우자 방울 하나가
          //   화면 15~20px 짜리 **검은 잎사귀**로 읽혔다(실측 크롭). 튀김은 작아야 튀김이다.
          float rad = 0.062 + 0.072 * h1(fk * 7.9 + vSd * 4.1);
          vec2 c = vec2(cos(ang), sin(ang)) * dist;
          // 방울 좌표계: +x 가 날아간 방향(바깥). 꼬리는 접점 쪽(-x)으로 끌린다.
          vec2 d = q - c;
          vec2 e = vec2(d.x * cos(ang) + d.y * sin(ang), -d.x * sin(ang) + d.y * cos(ang));
          bool pure = h1(fk * 11.3 + vSd * 5.9) < 0.28;               // 일곱 중 둘쯤만 순먹
          // ★순먹은 **작고 꼬리가 없다.** 1차 시도에서 먹에도 꼬리를 달았더니 화면에
          //   검은 바늘이 방사로 뻗어 '별표(*)'가 됐다(실측 크롭). 검은 것은 점이어야 한다.
          float rd = rad * (pure ? 0.62 : 0.95);
          float head = length(vec2(e.x * 0.62, e.y * 1.30));
          // 꼬리가 있어야 '방울'이 아니라 '쉼표'다. 없으면 그냥 점 일곱 개다.
          // ★길이는 날아간 거리의 38% 까지만. 접점까지 끌면 획이 아니라 긁힌 자국이 된다.
          float s = clamp(-e.x / max(dist * 0.38, 1e-3), 0.0, 1.0);
          float hw = rd * (1.0 - s) * 0.80 + 0.016;
          bool onTail = (!pure) && (e.x < 0.0) && (s < 1.0) && (abs(e.y) < hw);
          if (head < rd || onTail) {
            if (pure) ink = 1.0;
            else { wat = 1.0; if (onTail && s > 0.55) tip = 1.0; }    // 꼬리 안쪽 끝만 흰빛
          }
        }
        // 접점 자국. 원판 + 흰 점이 아니라 **짧은 먹 획** 하나. 각도는 팝마다 다르게
        // (가로로 못 박으면 화면 UI 의 대시로 읽힌다).
        float ta = h1(vSd * 2.9 + 0.7) * 3.14159;
        vec2 tq = vec2(q.x * cos(ta) + q.y * sin(ta), -q.x * sin(ta) + q.y * cos(ta));
        if (r < 0.16 && abs(tq.y) < 0.028 + 0.070 * abs(tq.x)) ink = 1.0;
        if (ink < 0.5 && wat < 0.5) discard;
        gl_FragColor = vec4(ink > 0.5 ? uInk : (tip > 0.5 ? uWht : uWat), 1.0);
      }`,
  });
  // ★메시를 늘 켜 둔다(알파 0 이면 전부 discard). 첫 타격에서 셰이더를 굽느라
  //   화면이 멎는 일이 구조적으로 안 생긴다(impfMesh 가 쓰는 것과 같은 성질).
  const popMesh = new THREE.Mesh(popGeo, popMat);
  popMesh.frustumCulled = false;
  popMesh.renderOrder = 13;         // 타격 지점 참격(12) 바로 위, 화면 겹(39+) 아래
  scene.add(popMesh);
  const pops = [];                  // {p, t, size, seed}
  const _pR = new THREE.Vector3(), _pU = new THREE.Vector3(), _pQ = new THREE.Vector3();
  const POP_CORNER = [[-1, -1], [1, -1], [1, 1], [-1, 1]];

  // 명중 접점에 팝 하나. x,y,z = 월드 좌표 / size = 크기 배수
  function pop(x, y, z, size) {
    if (pops.length >= POP_MAX) pops.shift();
    pops.push({ p: new THREE.Vector3(x, y, z), t: 0, size: size || 1,
                seed: Math.random() * 20 });
  }
  // 게임시간으로 늙힌다(히트스톱이 걸리면 같이 멈춘다)
  function updatePops(dtGame) {
    for (let i = pops.length - 1; i >= 0; i--) {
      pops[i].t += dtGame;
      if (Math.floor(pops[i].t / FRAME_T) >= POP_N) pops.splice(i, 1);
    }
    _pR.setFromMatrixColumn(camera.matrixWorld, 0);
    _pU.setFromMatrixColumn(camera.matrixWorld, 1);
    for (let i = 0; i < POP_MAX; i++) {
      const o = i * 4;
      if (i >= pops.length) { for (let k = 0; k < 4; k++) pA[o + k] = 0; continue; }
      const s = pops[i];
      const fr = Math.floor(s.t / FRAME_T);
      // 먹 튀김 장은 조금 더 크게 퍼진다(튀는 그림이라 넓어야 읽힌다)
      const rad = s.size * POP_SIZE * (fr < 1 ? 1.0 : 1.55);
      for (let k = 0; k < 4; k++) {
        _pQ.copy(s.p).addScaledVector(_pR, POP_CORNER[k][0] * rad)
           .addScaledVector(_pU, POP_CORNER[k][1] * rad);
        pPos[(o + k) * 3] = _pQ.x; pPos[(o + k) * 3 + 1] = _pQ.y; pPos[(o + k) * 3 + 2] = _pQ.z;
        pA[o + k] = 1;
        pFrm[o + k] = fr;
        pSeed[o + k] = s.seed;
      }
    }
    popGeo.attributes.position.needsUpdate = true;
    popGeo.attributes.aAlpha.needsUpdate = true;
    popGeo.attributes.aFrm.needsUpdate = true;
    popGeo.attributes.aSeed.needsUpdate = true;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 접점 에너지 파열 (18차 일섬) — 초승달·먹 튀김을 대신하는 한 겹
  //
  // 옛 판의 접점 연출은 둘이었다: 진홍/감청 **초승달**(월드 플립북 impactSlash)과
  // **먹 튀김 팝**(popMesh). 둘 다 먹으로 형태를 정의하는 귀멸 문법이라 일섬 판의
  // 언어(흰 코어 -> 시안 -> 딥블루 감쇠, 먹선 없음)와 한 화면에 못 선다.
  // 여기서 그리는 것은 **작은 에너지 파열** 한 겹이다:
  //   · 방사 스파크 일곱 가닥 (칼이 지나간 각도를 축으로 앞뒤로 길다)
  //   · 링 한 겹 (프레임마다 넓어지고 얇아진다)
  //   · 중심 섬광 (f0 에만. 여기만 선형 2를 넘겨 블룸이 문다)
  //
  // ★★타이밍이 히트스톱에 물려 있다 (17차 타격감 팩과의 합).
  //   이 층은 **게임시계**로 늙는다(pop·초승달과 같은 규칙). 히트스톱(명중 70ms ·
  //   처치 105ms)이 걸리면 게임시계가 0.05배로 눌리므로, 파열은 **f0 한 장을
  //   붙들고 있는다.** 그래서 f0 을 최대 프레임으로 그린다 — 중심 섬광이 제일 밝고
  //   스파크가 제일 길다. "멈춘 그 화면에 제일 센 그림이 서 있다"가 되게.
  //   (반대로 f0 을 작게 그리고 뒤에서 키우면, 커지는 장면이 전부 히트스톱 뒤로
  //    밀려 사람 눈에는 '멈췄다가 뒤늦게 터진다'로 보인다.)
  // ★크기 계약은 옛 판 그대로다. 반지름 0.62m x size 라 처치(1.15)에도 0.71m —
  //   요괴 키 1.30m 안에 든다("무엇을 벴는지 안 보인다"를 다시 열지 않는다).
  // ═══════════════════════════════════════════════════════════════════════
  const BURST_MAX = 8;
  const BURST_R = 0.62;            // size 1 일 때 반지름(m)
  const BURST_N_HIT = 4;           // 4/24 = 0.167초
  const BURST_N_KILL = 5;          // 5/24 = 0.208초 (처치가 한 장 길고 한 단 크다)
  // 프레임별 알파. 파열은 **커지면서 옅어진다**(f0 이 제일 세다).
  // ★★판의 크기는 **고정**이다(BURST_R). 1차 시도에서 판까지 프레임마다 키웠더니
  //   셰이더 안의 링 반지름 증가와 곱해져서 파열이 0.97m 짜리 별이 됐다(실측 T10.
  //   "과대 금지" 계약 위반). 커지는 것은 셰이더의 링·스파크뿐이고, 판은 그 자다.
  const BURST_A = [1.0, 0.72, 0.42, 0.20, 0.08];
  const burstGeo = new THREE.BufferGeometry();
  const bPos = new Float32Array(BURST_MAX * 4 * 3);
  const bUV = new Float32Array(BURST_MAX * 4 * 2);
  const bA = new Float32Array(BURST_MAX * 4);
  const bFrm = new Float32Array(BURST_MAX * 4);
  const bSeed = new Float32Array(BURST_MAX * 4);
  const bAng = new Float32Array(BURST_MAX * 4);
  const bBig = new Float32Array(BURST_MAX * 4);
  const bIdx = [];
  for (let i = 0; i < BURST_MAX; i++) {
    const o = i * 4;
    bIdx.push(o, o + 1, o + 2, o, o + 2, o + 3);
    bUV[o * 2] = 0; bUV[o * 2 + 1] = 0;
    bUV[(o + 1) * 2] = 1; bUV[(o + 1) * 2 + 1] = 0;
    bUV[(o + 2) * 2] = 1; bUV[(o + 2) * 2 + 1] = 1;
    bUV[(o + 3) * 2] = 0; bUV[(o + 3) * 2 + 1] = 1;
  }
  burstGeo.setAttribute('position', new THREE.BufferAttribute(bPos, 3));
  burstGeo.setAttribute('aUV', new THREE.BufferAttribute(bUV, 2));
  burstGeo.setAttribute('aAlpha', new THREE.BufferAttribute(bA, 1));
  burstGeo.setAttribute('aFrm', new THREE.BufferAttribute(bFrm, 1));
  burstGeo.setAttribute('aSeed', new THREE.BufferAttribute(bSeed, 1));
  burstGeo.setAttribute('aAng', new THREE.BufferAttribute(bAng, 1));
  burstGeo.setAttribute('aBig', new THREE.BufferAttribute(bBig, 1));
  burstGeo.setIndex(bIdx);
  // ★색은 **선형 vec3 로 직접** 넣는다(THREE.Color 금지 - 그 자는 hex 를 sRGB 로
  //   읽어 선형으로 바꾼다. 위 uWat 주석의 함정이 그것이다). main.js 의 uPal 과
  //   같은 자를 써야 궤적의 코어와 파열의 코어가 화면에서 같은 색에 앉는다.
  // ★기본값은 물칼 팔레트에서 뽑은 값이다. main.js 가 칼을 바꿀 때마다
  //   setBurstPalette() 로 그 칼의 네 단을 넘긴다(안 부르면 이 물빛 그대로).
  const burstMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: false, fog: false,
    blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    uniforms: {
      // 흰 코어. 선형 1.85 = 블룸 문턱(1.02)을 확실히 넘긴다 = 이 한 점만 번진다
      uCore: { value: new THREE.Vector3(1.68, 1.78, 1.86) },
      uHot: { value: new THREE.Vector3(0.31, 1.08, 1.32) },     // 시안(밝은 단)
      uMid: { value: new THREE.Vector3(0.13, 0.58, 0.76) },     // 시안(중간 단)
      uDeep: { value: new THREE.Vector3(0.05, 0.21, 0.36) },    // 딥블루(감쇠 끝)
    },
    vertexShader: `
      attribute vec2 aUV; attribute float aAlpha; attribute float aFrm;
      attribute float aSeed; attribute float aAng; attribute float aBig;
      varying vec2 vUV; varying float vA; varying float vFrm;
      varying float vSd; varying float vAn; varying float vBg;
      void main(){ vUV = aUV; vA = aAlpha; vFrm = aFrm; vSd = aSeed; vAn = aAng; vBg = aBig;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      varying vec2 vUV; varying float vA; varying float vFrm;
      varying float vSd; varying float vAn; varying float vBg;
      uniform vec3 uCore; uniform vec3 uHot; uniform vec3 uMid; uniform vec3 uDeep;
      float h1(float x){ return fract(sin(x * 127.1) * 43758.5453); }
      void main(){
        // ★!(vA > x) 꼴. NaN 은 모든 비교가 거짓이라 (vA <= x) 로 쓰면 NaN 이
        //   discard 를 통과해 HDR 버퍼에 찍히고 블룸이 사각형으로 번진다(v88 함정).
        if (!(vA > 0.004)) discard;
        vec2 q = vUV * 2.0 - 1.0;
        float r = length(q);
        if (r > 1.0) discard;
        float fr = floor(vFrm + 0.5);
        // 벤 각도를 x 축으로 돌린 좌표. 스파크가 **칼이 지나간 축**으로 길어야
        // "칼이 지나가며 터졌다"로 읽힌다(무작위 방사는 폭죽이 된다).
        float ca = cos(-vAn), sa = sin(-vAn);
        vec2 p = vec2(q.x * ca - q.y * sa, q.x * sa + q.y * ca);
        float ang = atan(p.y, p.x);

        // ── 링 한 겹 ── 프레임마다 넓어지고 얇아진다(판은 안 커진다. 위 주석)
        float rr = 0.26 + 0.17 * fr;
        float tw = max(0.028, 0.10 - 0.018 * fr);
        float ring = 1.0 - smoothstep(0.0, tw, abs(r - rr));
        // 링은 완전한 원이 아니다. 벤 축 방향이 더 세고, 각도 열두 칸으로 **끊긴다**.
        // ★안 끊으면 UI 아이콘(완전한 동심원)으로 읽힌다 - 이 게임 화면에는 이미
        //   요괴 예고 링이 그 문법으로 돌고 있어서 둘이 헷갈린다(실측 크롭에서 그랬다).
        ring *= 0.45 + 0.55 * abs(cos(ang));
        ring *= 0.55 + 0.60 * h1(floor((ang + 3.14159265) / 0.52) * 1.7 + vSd);

        // ── 방사 스파크 다섯 가닥 ──
        // 각 가닥은 제 각도·길이를 씨앗에서 받는다. 벤 축(ang 0/pi) 근처가 길다.
        // ★일곱 가닥 + 작은 흔들림(0.72)은 화면에서 **바퀴살**로 보였다(실측 T11).
        //   다섯으로 줄이고 흔들림을 칸의 95% 까지 열면 '몇 가닥 튀었다'가 된다.
        const float SPK = 5.0;
        float step0 = 6.2831853 / SPK;
        float si = floor((ang + 3.14159265) / step0);
        float sp = 0.0;
        for (int k = -1; k <= 1; k++) {
          float idx = si + float(k);
          float sd = vSd + idx * 3.77;
          float ac = (idx + 0.5) * step0 - 3.14159265 + (h1(sd) - 0.5) * step0 * 0.95;
          float da = ang - ac;
          // 각도 차를 -pi..pi 로 접는다
          da = da - 6.2831853 * floor(da / 6.2831853 + 0.5);
          // 길이: 벤 축에 가까울수록 길다(0.55 ~ 1.0). 프레임이 갈수록 길어진다
          float axial = abs(cos(ac));
          // ★길이 상한이 곧 계약이다. 1차 시도는 최대 1.30 이라 판 밖으로 뻗어
          //   **직선 별**이 됐다(실측 T10). 지금 상한 0.68 - 링 안쪽에 머문다.
          float len = (0.30 + 0.30 * axial) * (0.85 + 0.10 * fr) * (0.45 + 0.70 * h1(sd + 1.3));
          if (r < len) {
            // 바늘: 뿌리에서 굵고 끝에서 0 으로. 폭은 **각도** 폭이라 r 이 커질수록
            // 실제 화소 폭은 그대로다(각도 0.10rad x r 0.5 = 화면에서 2~3px).
            // ★1차 시도의 0.052 는 1px 라 흰 공 옆에서 아예 안 보였다(실측 T9).
            float tt = 1.0 - r / max(len, 1e-3);
            float hw = (0.105 + 0.055 * h1(sd + 2.1)) * (0.35 + 0.65 * tt);
            float d = 1.0 - smoothstep(hw * 0.35, hw, abs(da));
            sp = max(sp, d * (0.35 + 0.65 * tt));
          }
        }

        // ── 중심 섬광 ── f0 에만. 히트스톱이 붙드는 그 한 장이다.
        // ★★작아야 한다. 1차 시도에서 반지름 0.32(=0.23m)로 뒀더니 파열이 통째로
        //   **흰 공** 하나가 됐다(실측 T9. 스파크도 링도 그 안에 먹혔다). 접점의
        //   '점'이지 폭발이 아니다 - 여기서 화면을 채우면 17차의 백색 패널로 되돌아간다.
        float cr = (0.11 + 0.04 * vBg) * (fr < 0.5 ? 1.0 : (fr < 1.5 ? 0.62 : 0.0));
        float core = cr > 0.0 ? (1.0 - smoothstep(cr * 0.40, cr, r)) : 0.0;

        // ── 합성 ── 겹마다 색을 따로 얹는다(가산이라 그냥 더하면 된다).
        //   링   = 시안 몸 + 딥블루 번짐
        //   스파크 = 시안 바늘 + 뿌리의 흰 심(세제곱이라 끝으로 갈수록 색만 남는다)
        //   중심  = 흰 섬광
        if (sp < 0.05 && ring < 0.05 && core < 0.02) discard;
        vec3 c = uHot * (ring * 0.85) + uDeep * (ring * 0.60);
        c += uHot * (sp * 1.10) + uMid * (sp * 0.45);
        c += uCore * (pow(sp, 3.0) * 0.85);
        c += uCore * core;
        float e = clamp(max(max(ring, sp), core), 0.0, 1.0);
        gl_FragColor = vec4(c, vA * e);
      }`,
  });
  const burstMesh = new THREE.Mesh(burstGeo, burstMat);
  burstMesh.frustumCulled = false;
  burstMesh.renderOrder = 14;       // 팝(13) 바로 위, 화면 겹(39+) 아래
  burstMesh.visible = true;         // 늘 켜 둔다(알파 0 이면 전부 discard. 예열 겸용)
  scene.add(burstMesh);
  const bursts = [];                // {p, t, ang, size, seed, n, big}
  let burstSpawnN = 0;              // 지금까지 띄운 파열 수(게이트 검증 창구)
  const _bR = new THREE.Vector3(), _bU = new THREE.Vector3(), _bQ = new THREE.Vector3();

  // 접점에 파열 하나. x,y,z = 월드 좌표 / ang = 화면 각도(벤 방향) /
  // size = 크기 배수 / kill = 처치면 한 단 크고 한 장 길다
  function burst(x, y, z, ang, size, kill) {
    burstSpawnN++;
    if (bursts.length >= BURST_MAX) bursts.shift();
    bursts.push({ p: new THREE.Vector3(x, y, z), t: 0, ang: ang || 0,
                  size: (size || 1) * (kill ? 1.15 : 0.90),
                  n: kill ? BURST_N_KILL : BURST_N_HIT,
                  big: kill ? 1 : 0, seed: Math.random() * 20 });
  }
  // 게임시간으로 늙힌다(히트스톱이 걸리면 f0 을 붙들고 있는다. 위 타이밍 주석)
  function updateBursts(dtGame) {
    for (let i = bursts.length - 1; i >= 0; i--) {
      bursts[i].t += dtGame;
      if (Math.floor(bursts[i].t / FRAME_T) >= bursts[i].n) bursts.splice(i, 1);
    }
    _bR.setFromMatrixColumn(camera.matrixWorld, 0);
    _bU.setFromMatrixColumn(camera.matrixWorld, 1);
    for (let i = 0; i < BURST_MAX; i++) {
      const o = i * 4;
      if (i >= bursts.length) { for (let k = 0; k < 4; k++) bA[o + k] = 0; continue; }
      const s = bursts[i];
      const fr = Math.min(Math.floor(s.t / FRAME_T), BURST_A.length - 1);
      const rad = s.size * BURST_R;         // ★고정. 위 BURST_A 주석 참조
      const a = BURST_A[fr];
      for (let k = 0; k < 4; k++) {
        _bQ.copy(s.p).addScaledVector(_bR, POP_CORNER[k][0] * rad)
           .addScaledVector(_bU, POP_CORNER[k][1] * rad);
        bPos[(o + k) * 3] = _bQ.x; bPos[(o + k) * 3 + 1] = _bQ.y; bPos[(o + k) * 3 + 2] = _bQ.z;
        bA[o + k] = a;
        bFrm[o + k] = fr;
        bSeed[o + k] = s.seed;
        bAng[o + k] = s.ang;
        bBig[o + k] = s.big;
      }
    }
    burstGeo.attributes.position.needsUpdate = true;
    burstGeo.attributes.aAlpha.needsUpdate = true;
    burstGeo.attributes.aFrm.needsUpdate = true;
    burstGeo.attributes.aSeed.needsUpdate = true;
    burstGeo.attributes.aAng.needsUpdate = true;
    burstGeo.attributes.aBig.needsUpdate = true;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 칼끝 포말 마루 (v99 16-FX) — 물방울 대신 리본 바깥면에 붙는 흰 거품
  //
  // main.js 의 파란 B 리본은 다른 에이전트 소유라 여기서 갈지 않는다. 이 층은 매 프레임
  // 넘어오는 칼날 선분 a→b 중 **칼끝 b의 지나간 자리**에 구운 포말 덩어리를 겹쳐 놓는다.
  // 원화 한 덩어리의 아래 긴 먹선이 기존 리본 바깥 가장자리와 포개져 두 메시가 한 몸으로
  // 읽히고, 흰 갈고리/와권은 그 먹선 바깥쪽으로만 솟는다.
  //
  // 시간 계약:
  //   · trailFoamSample() 은 재사용되는 a,b와 선택적인 플레이어 기준점을 즉시 복사한다.
  //   · 실제 생성·자리·알파 변화는 updateFoamCrests() 의 1/24초 칸에서만 일어난다.
  //   · 흰 머리는 3칸, 그 뒤는 시안/먹 잔흔. 수명은 4/5/6칸으로 어긋난다.
  //   · wake<=0.18 이 되는 순간 생성을 끊고 최대 6칸(0.25초) 안에 전부 죽는다.
  //     본 리본 11칸보다 반드시 먼저 회수되어 C의 늦은 회수 동작을 추가타로 만들지 않는다.
  const FOAM_MAX = 28;
  const FOAM_COLS = 4, FOAM_ROWS = 4;
  const FOAM_WAKE_MIN = 0.18;
  const FOAM_SPACING = 0.22;       // R2: 빠른 칼에서도 마루가 끊기지 않는 칼끝 이동거리(m)
  const FOAM_SEAM_V = 0.20;        // 이 UV부터 밝은 포말. 굽기 스크립트와 같은 계약
  const FOAM_OUT_GAP = 0.080;      // 밝은 포말 시작선을 리본/블룸 외곽 밖에 두는 간격(m)
  const FOAM_RIBBON_TIP_K = 1.03;  // main.js B 리본의 칼끝 반경 정박 배수와 동일
  const FOAM_ALPHA = [1.00, 1.00, 0.96, 0.82, 0.55, 0.32];
  const FOAM_SCALE = [1.00, 1.00, 0.92, 0.75, 0.54, 0.34];
  const foamGeo = new THREE.BufferGeometry();
  const fcPos = new Float32Array(FOAM_MAX * 4 * 3);
  const fcUV = new Float32Array(FOAM_MAX * 4 * 2);
  const fcA = new Float32Array(FOAM_MAX * 4);
  const fcCell = new Float32Array(FOAM_MAX * 4);
  const fcAge = new Float32Array(FOAM_MAX * 4);
  const fcIdx = [];
  for (let i = 0; i < FOAM_MAX; i++) {
    const o = i * 4;
    fcIdx.push(o, o + 1, o + 2, o, o + 2, o + 3);
    fcUV[o * 2] = 0; fcUV[o * 2 + 1] = 0;
    fcUV[(o + 1) * 2] = 1; fcUV[(o + 1) * 2 + 1] = 0;
    fcUV[(o + 2) * 2] = 1; fcUV[(o + 2) * 2 + 1] = 1;
    fcUV[(o + 3) * 2] = 0; fcUV[(o + 3) * 2 + 1] = 1;
  }
  foamGeo.setAttribute('position', new THREE.BufferAttribute(fcPos, 3));
  foamGeo.setAttribute('aUV', new THREE.BufferAttribute(fcUV, 2));
  foamGeo.setAttribute('aAlpha', new THREE.BufferAttribute(fcA, 1));
  foamGeo.setAttribute('aCell', new THREE.BufferAttribute(fcCell, 1));
  foamGeo.setAttribute('aAge', new THREE.BufferAttribute(fcAge, 1));
  foamGeo.setIndex(fcIdx);

  const foamMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: false, fog: false,
    blending: THREE.NormalBlending, side: THREE.DoubleSide,
    uniforms: {
      uTex: { value: null }, uHasTex: { value: 0 },
      // THREE.Color(hex)는 sRGB→선형 변환을 한다. 아래 sRGB 값은 변환 뒤 먹≈0.02~0.10,
      // 감청≈0.04~0.35, 시안≈0.18~0.82, 포말≤1.0 에 앉도록 고른 값이다.
      // 어느 단도 블룸 문턱 1.02를 넘지 않는다 — 흰색은 먹 옆의 대비로 만든다.
      uInk: { value: new THREE.Color(0x263d57) },
      uEdge: { value: new THREE.Color(0x3b6eaa) },
      uCyan: { value: new THREE.Color(0x76c8ea) },
      uFoam: { value: new THREE.Color(0xf4fbff) },
    },
    vertexShader: `
      attribute vec2 aUV; attribute float aAlpha; attribute float aCell; attribute float aAge;
      varying vec2 vUV; varying float vA; varying float vCell; varying float vAge;
      void main(){ vUV = aUV; vA = aAlpha; vCell = aCell; vAge = aAge;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      varying vec2 vUV; varying float vA; varying float vCell; varying float vAge;
      uniform sampler2D uTex; uniform float uHasTex;
      uniform vec3 uInk; uniform vec3 uEdge; uniform vec3 uCyan; uniform vec3 uFoam;
      void main(){
        // 부정형 알파 검사: NaN이 HDR 버퍼로 빠지는 v88 계열 사고를 막는다.
        if (!(vA > 0.004)) discard;
        float lum;
        float ta;
        if (uHasTex > 0.5) {
          vec2 cuv = clamp(vUV, 0.003, 0.997);
          float ci = floor(vCell + 0.5);
          float cx = mod(ci, ${FOAM_COLS.toFixed(1)});
          // three TextureLoader의 flipY를 상쇄: 원화 0번은 시트의 맨 윗줄이다.
          float cy = ${(FOAM_ROWS - 1).toFixed(1)} - floor(ci / ${FOAM_COLS.toFixed(1)});
          vec4 tx = texture2D(uTex, (vec2(cx, cy) + cuv)
                                    * vec2(${(1 / FOAM_COLS).toFixed(6)}, ${(1 / FOAM_ROWS).toFixed(6)}));
          lum = dot(tx.rgb, vec3(0.30, 0.59, 0.11));
          ta = tx.a;
        } else {
          // 시트가 빠진 배포본의 조용한 절차 폴백. 원판/낱알이 아니라 아래 먹선에
          // 붙은 세 덩어리 하나만 그린다. 전부 step이라 반투명 CG 페이드가 없다.
          vec2 q = vUV;
          float base = step(0.12, q.x) * step(q.x, 0.96)
                     * step(abs(q.y - (0.23 + 0.035 * sin(q.x * 17.0))), 0.075);
          float p0 = step(length((q - vec2(0.28,0.38)) / vec2(0.18,0.25)), 1.0);
          float p1 = step(length((q - vec2(0.52,0.34)) / vec2(0.16,0.19)), 1.0);
          float p2 = step(length((q - vec2(0.73,0.30)) / vec2(0.13,0.14)), 1.0);
          float live = max(base, max(p0, max(p1, p2)));
          if (!(live > 0.5)) discard;
          // 바닥은 먹, 마루는 흰색. 작은 폴백에서도 '눈알'이 될 내부 점은 없다.
          lum = q.y < 0.28 ? 0.12 : (q.y < 0.34 ? 0.70 : 0.95);
          ta = 1.0;
        }
        float a = ta * vA;
        if (!(a > 0.004)) discard;
        vec3 c = lum > 0.82 ? uFoam : (lum > 0.62 ? uCyan : (lum > 0.30 ? uEdge : uInk));
        // 머리 3칸 뒤에는 흰 면을 없애고 한 단씩 어둡게 내려 꼬리를 포말이 아닌
        // 기존 감청 리본의 결로 돌려준다. 알파·색 모두 칸 단위라 스르르 녹지 않는다.
        if (vAge > 2.5)
          c = lum > 0.82 ? uCyan : (lum > 0.62 ? uEdge : uInk);
        gl_FragColor = vec4(c, a);
      }`,
  });
  const foamMesh = new THREE.Mesh(foamGeo, foamMat);
  foamMesh.frustumCulled = false;
  foamMesh.renderOrder = 6;          // 궤적3·감김4·물보라5 위, 실루엣7·링8 아래
  foamMesh.visible = true;           // 알파 0으로 숨겨 첫 스윙 셰이더 컴파일 히치를 막는다
  scene.add(foamMesh);

  let foamSheetLoaded = 0;
  new THREE.TextureLoader().load('./tex/foam_crest_sheet.png' + location.search, (t) => {
    // 회색조 밝기 0.12/0.46/0.70/0.95를 선형 그대로 읽어야 한다. colorSpace 금지.
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    t.generateMipmaps = false;
    t.minFilter = THREE.LinearFilter;
    t.magFilter = THREE.LinearFilter;
    foamMat.uniforms.uTex.value = t;
    foamMat.uniforms.uHasTex.value = 1;
    foamSheetLoaded = 1;
  }, undefined, () => { /* 시트가 없으면 위 절차 포말로 조용히 돈다 */ });

  const foams = [];                 // {p, dir, blade, out, drift, birth, life, variant, wake}
  const foamPending = {
    a: new THREE.Vector3(), b: new THREE.Vector3(), chest: new THREE.Vector3(),
    wake: 0, valid: false, anchored: false, seq: 0,
  };
  const foamPrevTip = new THREE.Vector3();
  const foamLastSpawn = new THREE.Vector3();
  let foamPrevValid = false, foamLastSpawnValid = false, foamActive = false;
  let foamClock = 0, foamQFrame = -1, foamHold = 0, foamProcessedSeq = 0;
  let foamSerial = 0, foamSpawnN = 0, foamDropped = 0, foamLastWake = 0;
  const _fcDir = new THREE.Vector3(), _fcBlade = new THREE.Vector3();
  const _fcOut = new THREE.Vector3(), _fcDrift = new THREE.Vector3();
  const _fcFrom = new THREE.Vector3(), _fcP = new THREE.Vector3();
  const _fcR = new THREE.Vector3(), _fcU = new THREE.Vector3();
  const _fcL = new THREE.Vector3(), _fcN = new THREE.Vector3(), _fcC = new THREE.Vector3();
  const _fcQ = new THREE.Vector3();
  const FOAM_CORNER = [[-1, -1], [1, -1], [1, 1], [-1, 1]];

  function finiteV3(v) {
    return !!v && Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.z);
  }

  // main.js 한 줄 통로. a,b/rootPos는 매 프레임 재사용되는 객체이므로 즉시 복사한다.
  function trailFoamSample(a, b, wake, rootPos, charH) {
    foamPending.seq++;
    // ★18차. 포말 마루는 **B 리본의 바깥면에 붙는 층**이다(정박 계약이 리본 기하에
    //   물려 있다). 일섬 판에는 붙을 리본이 없으므로 표본 수집 자체를 여기서 끊는다.
    //   FX_V18=0 이면 이 한 줄이 없는 것과 같다(아래 옛 경로가 그대로 돈다).
    if (FX_V18) { foamPending.valid = false; return false; }
    if (!FOAM_CREST_V2 || !finiteV3(a) || !finiteV3(b) || !Number.isFinite(wake)) {
      foamPending.valid = false;
      return false;
    }
    foamPending.a.copy(a);
    foamPending.b.copy(b);
    foamPending.wake = Math.max(0, Math.min(1, wake));
    // R2 합성용 선택 인자. main.js B 리본과 같은 가슴 기준 바깥 방향을 재현한다.
    // 옛 3인자 호출도 안전하게 돌며 그때는 칼날 방향을 보수적 폴백으로 쓴다.
    foamPending.anchored = finiteV3(rootPos) && Number.isFinite(charH) && charH > 0;
    if (foamPending.anchored) {
      foamPending.chest.copy(rootPos);
      foamPending.chest.y += charH * 0.55;
    }
    foamPending.valid = true;
    return true;
  }

  function spawnFoamCrest(p, dir, blade, out, drift, wake, anchored) {
    if (foams.length >= FOAM_MAX) { foams.shift(); foamDropped++; }
    const n = foamSerial++;
    foams.push({
      p: p.clone(), dir: dir.clone(), blade: blade.clone(), out: out.clone(),
      drift: drift.clone(), anchored: !!anchored, birth: foamQFrame,
      // 4/5/6칸. 같은 칸 동시 소멸을 피하고 최대치는 0.25초로 못 박는다.
      life: 4 + (n % 3),
      // 빠른 머리는 날카로운 claw 0..7, 낮은 wake는 둥근 crest 8..15.
      variant: wake > 0.58 ? (n % 8) : (8 + (n % 8)),
      wake,
    });
    foamSpawnN++;
  }

  function consumeFoamSample() {
    if (!foamPending.valid) {
      foamActive = false; foamPrevValid = false; foamLastSpawnValid = false;
      return;
    }
    _fcP.copy(foamPending.b);
    _fcBlade.copy(foamPending.b).sub(foamPending.a);
    if (_fcBlade.lengthSq() < 1e-8) _fcBlade.set(0, 1, 0);
    else _fcBlade.normalize();
    if (foamPrevValid) _fcDir.copy(_fcP).sub(foamPrevTip);
    else _fcDir.copy(_fcBlade);
    // main.js 의 vb = 칼끝 속도*0.16 과 같은 바깥 흐름. 정지 도장은 리본만
    // 바깥으로 날아가며 갈고리 방향이 어긋났으므로, R2부터 포말도 같이 운반한다.
    if (foamPrevValid) _fcDrift.copy(_fcP).sub(foamPrevTip).multiplyScalar(0.16 / FRAME_T);
    else _fcDrift.set(0, 0, 0);
    if (_fcDir.lengthSq() < 1e-8) _fcDir.copy(_fcBlade);
    else _fcDir.normalize();
    const wake = foamPending.wake;
    foamLastWake = wake;
    if (wake > FOAM_WAKE_MIN) {
      if (!foamActive || !foamLastSpawnValid) {
        if (foamPending.anchored) _fcOut.copy(_fcP).sub(foamPending.chest);
        else _fcOut.copy(_fcBlade);
        spawnFoamCrest(_fcP, _fcDir, _fcBlade, _fcOut, _fcDrift, wake,
                       foamPending.anchored);
        foamLastSpawn.copy(_fcP);
        foamLastSpawnValid = true;
      } else {
        _fcFrom.copy(foamLastSpawn);
        const dist = _fcFrom.distanceTo(_fcP);
        // 한 작화 칸에 너무 많은 도장이 찍히지 않게 상한 3. 빠른 칼은 간격이 넓어져도
        // 각 원화 길이가 0.5~0.7m라 서로 겹쳐 한 마루로 남는다.
        const count = Math.min(3, Math.floor(dist / FOAM_SPACING));
        for (let j = 1; j <= count; j++) {
          // 마지막 점으로 균등분할하면 0.31m 이동/count 1에서 간격이 두 배로 뛴다.
          // 실제 자 FOAM_SPACING 만큼씩만 전진해 다음 칸에 남은 거리를 넘긴다.
          _fcQ.copy(_fcFrom).lerp(_fcP, Math.min(1, j * FOAM_SPACING / Math.max(dist, 1e-4)));
          if (foamPending.anchored) _fcOut.copy(_fcQ).sub(foamPending.chest);
          else _fcOut.copy(_fcBlade);
          spawnFoamCrest(_fcQ, _fcDir, _fcBlade, _fcOut, _fcDrift, wake,
                         foamPending.anchored);
          foamLastSpawn.copy(_fcQ);
        }
      }
      foamActive = true;
    } else {
      // 캐스트 시각 종료. 기존 포말은 제 수명표대로 죽되 새 덩어리는 즉시 끊는다.
      foamActive = false;
      foamLastSpawnValid = false;
    }
    foamPrevTip.copy(_fcP);
    foamPrevValid = true;
  }

  function rebuildFoamGeometry() {
    _fcR.setFromMatrixColumn(camera.matrixWorld, 0);
    _fcU.setFromMatrixColumn(camera.matrixWorld, 1);
    for (let i = 0; i < FOAM_MAX; i++) {
      const o = i * 4;
      if (i >= foams.length) {
        for (let k = 0; k < 4; k++) fcA[o + k] = 0;
        continue;
      }
      const s = foams[i];
      const age = Math.max(0, foamQFrame - s.birth);
      const ai = Math.min(age, FOAM_ALPHA.length - 1);
      const alpha = FOAM_ALPHA[ai];
      const scale = FOAM_SCALE[ai];
      // 진행 방향을 카메라 평면에 내린다. 아래에서 리본의 방사 방향과 직교시켜
      // 원화의 왼쪽 큰 갈고리가 진행 방향을 보게 한다(왼쪽 머리→오른쪽 바늘 꼬리).
      let dx = s.dir.dot(_fcR), dy = s.dir.dot(_fcU);
      let dl = Math.hypot(dx, dy);
      if (dl < 1e-5) { dx = 1; dy = 0; dl = 1; }
      dx /= dl; dy /= dl;
      // main.js B 리본과 똑같이 '플레이어 가슴 -> 칼끝'의 화면 방사 방향을 쓴다.
      // 선택 anchor가 없는 옛 호출에서는 저장한 칼날 방향으로 조용히 폴백한다.
      if (s.anchored && foamPending.anchored) _fcOut.copy(s.p).sub(foamPending.chest);
      else _fcOut.copy(s.out);
      let nx = _fcOut.dot(_fcR), ny = _fcOut.dot(_fcU);
      let nl = Math.hypot(nx, ny);
      if (nl < 1e-5) {
        nx = s.blade.dot(_fcR); ny = s.blade.dot(_fcU); nl = Math.hypot(nx, ny);
      }
      if (nl < 1e-5) { nx = -dy; ny = dx; nl = 1; }
      nx /= nl; ny /= nl;
      _fcN.copy(_fcR).multiplyScalar(nx).addScaledVector(_fcU, ny);
      // 길이축은 리본 바깥축과 정확히 직교시킨다. 그래야 아래 L 오프셋이 포말을
      // 다시 리본 안으로 밀지 않고, 갈고리도 리본의 진행 접선을 따라 눕는다.
      let lx = -ny, ly = nx;
      if (lx * -dx + ly * -dy < 0) { lx = -lx; ly = -ly; }
      _fcL.copy(_fcR).multiplyScalar(lx).addScaledVector(_fcU, ly);
      // 최신/강한 마루만 크다. 원화 한 덩어리는 최대 1.30x0.56m지만 R2 절단 뒤
      // 셀의 live 면은 8~36%이고 먹선·구멍으로 갈라져 통짜 흰 판이 되지 않는다. 길이는
      // 칼끝 반경+반길이 약 2.1m라 3.2m 판정 리치 안에 남는다.
      const hl = (0.40 + 0.25 * s.wake) * scale;
      const hh = (0.18 + 0.10 * s.wake) * scale;
      // B 리본 바깥 가장자리는 tipR*1.03 에 정박한다. 시트의 v=FOAM_SEAM_V를
      // 그 가장자리보다 FOAM_OUT_GAP 바깥에 놓아 밝은 몸통이 흰 리본과 겹치지 않게
      // 기하로 보장한다. 그 아래에는 굽기에서 남긴 얇은 먹 경계만 있다.
      const tipPad = s.anchored ? nl * (FOAM_RIBBON_TIP_K - 1.0) : 0.045;
      const seamCenter = tipPad + FOAM_OUT_GAP + hh * (1.0 - 2.0 * FOAM_SEAM_V);
      _fcC.copy(s.p)
          .addScaledVector(_fcL, hl * 0.55)   // 머리(로컬 -x)가 b 근처에 앉는다
          .addScaledVector(_fcN, seamCenter); // 먹 경계만 리본에 걸치고 흰 몸통은 바깥으로
      for (let k = 0; k < 4; k++) {
        _fcQ.copy(_fcC).addScaledVector(_fcL, FOAM_CORNER[k][0] * hl)
            .addScaledVector(_fcN, FOAM_CORNER[k][1] * hh);
        fcPos[(o + k) * 3] = _fcQ.x;
        fcPos[(o + k) * 3 + 1] = _fcQ.y;
        fcPos[(o + k) * 3 + 2] = _fcQ.z;
        fcA[o + k] = alpha;
        fcCell[o + k] = s.variant;
        fcAge[o + k] = age;
      }
    }
    foamGeo.attributes.position.needsUpdate = true;
    foamGeo.attributes.aAlpha.needsUpdate = true;
    foamGeo.attributes.aCell.needsUpdate = true;
    foamGeo.attributes.aAge.needsUpdate = true;
  }

  function updateFoamCrests(dtGame) {
    if (!FOAM_CREST_V2) {
      if (foams.length) foams.length = 0;
      for (let i = 0; i < fcA.length; i++) fcA[i] = 0;
      foamGeo.attributes.aAlpha.needsUpdate = true;
      return;
    }
    foamClock += Math.max(0, Number.isFinite(dtGame) ? dtGame : 0);
    const qf = Math.floor(foamClock / FRAME_T);
    if (qf === foamQFrame) { foamHold++; return; }
    foamQFrame = qf;
    foamHold = 0;
    // 이미 태어난 포말을 main.js 리본 샘플과 같은 계수로 바깥에 운반한다.
    // 새로 태어날 포말은 아직 한 칸도 흐르지 않아야 하므로 consume보다 먼저 돈다.
    const driftDecay = Math.pow(0.40, FRAME_T);
    for (const s of foams) {
      s.p.addScaledVector(s.drift, FRAME_T);
      s.drift.multiplyScalar(driftDecay);
    }
    if (foamPending.seq !== foamProcessedSeq) {
      consumeFoamSample();
      foamProcessedSeq = foamPending.seq;
    } else {
      // 샘플 통로가 끊긴 판에서도 옛 마지막 점에서 새 포말을 만들지 않는다.
      foamActive = false; foamPrevValid = false; foamLastSpawnValid = false;
    }
    for (let i = foams.length - 1; i >= 0; i--) {
      if (foamQFrame - foams[i].birth >= foams[i].life) foams.splice(i, 1);
    }
    rebuildFoamGeometry();
  }

  // ── 무리 전멸 링 (tex/ring_shock.png) ──
  // ★지면에 눕는 데칼이다. 화면 겹이 아니다. 마지막 요괴가 쓰러진 자리에서 한 번
  //   퍼지고 끝난다. 아무 처치에서나 띄우면 0.4초짜리 고리가 계속 깔려서 값이 없어진다.
  const ringMat = new THREE.MeshBasicMaterial({
    map: null, transparent: true, depthWrite: false, fog: false,
    side: THREE.DoubleSide, blending: THREE.NormalBlending, opacity: 0,
    color: new THREE.Color(RING_TINT),
  });
  const ringMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), ringMat);
  ringMesh.rotation.x = -Math.PI / 2;      // 눕힌다(로컬 xy 가 월드 xz 가 된다)
  ringMesh.renderOrder = 8;
  ringMesh.frustumCulled = false;
  ringMesh.visible = false;
  scene.add(ringMesh);
  // 못 읽으면 링만 안 나온다. 게임은 그대로 돈다.
  new THREE.TextureLoader().load('./tex/ring_shock.png' + location.search, (t) => {
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    ringMat.map = t;
    ringMat.needsUpdate = true;
  }, undefined, () => { /* 없으면 링 없이 간다 */ });

  // ── 레벨 상승 빛 ──
  // DOM 알림과 무관한 월드 연출이다. 기하는 시작할 때 한 번만 만들고, 레벨이 오를 때는
  // 위치·알파·버텍스만 갱신한다. 매번 Mesh/Material 을 새로 만들지 않으므로 GC가 없다.
  const levelRoot = new THREE.Group();
  levelRoot.name = 'level-up-light';
  levelRoot.visible = false;
  scene.add(levelRoot);

  const levelGroundMat = new THREE.MeshBasicMaterial({
    color: 0xf1a83a, transparent: true, opacity: 0, depthWrite: false, fog: false,
    side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
  });
  const levelRiseMat = new THREE.MeshBasicMaterial({
    color: 0xffedbd, transparent: true, opacity: 0, depthWrite: false, fog: false,
    side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
  });
  // 반지름은 캐릭터 키의 비율이다. 2.4m 캐릭터 기준 최대 지름 약 1.55m로 몸 주변만 쓴다.
  const levelGroundRing = new THREE.Mesh(new THREE.RingGeometry(0.285, 0.315, 48), levelGroundMat);
  levelGroundRing.rotation.x = -Math.PI / 2;
  levelGroundRing.position.y = 0.025;
  levelGroundRing.renderOrder = 12;
  levelGroundRing.frustumCulled = false;
  levelRoot.add(levelGroundRing);

  const levelRiseRing = new THREE.Mesh(new THREE.RingGeometry(0.205, 0.222, 40), levelRiseMat);
  levelRiseRing.rotation.x = -Math.PI / 2;
  levelRiseRing.position.y = 0.08;
  levelRiseRing.renderOrder = 13;
  levelRiseRing.frustumCulled = false;
  levelRoot.add(levelRiseRing);

  // 카메라 쪽만 보는 세로 베일. 텍스처 없이 셰이더에서 중심 심·상승 띠를 만든다.
  // 화면 전체 플래시가 아니라 캐릭터 키 안에 머물도록 로컬 크기를 0..1 로 고정한다.
  const levelGlowMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, depthTest: true, fog: false,
    blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    uniforms: {
      uProgress: { value: 0 },
      uAlpha: { value: 0 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main(){
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: `
      varying vec2 vUv;
      uniform float uProgress;
      uniform float uAlpha;
      void main(){
        float x = abs(vUv.x - 0.5) * 2.0;
        float body = pow(max(0.0, 1.0 - x), 3.4);
        float yFade = smoothstep(0.02, 0.18, vUv.y)
                    * (1.0 - smoothstep(0.70, 1.0, vUv.y));
        float liftY = 0.10 + uProgress * 0.72;
        float lift = exp(-pow((vUv.y - liftY) * 8.0, 2.0))
                   * pow(max(0.0, 1.0 - x), 2.0);
        float energy = body * yFade * 0.34 + lift * 0.62;
        if (energy * uAlpha < 0.004) discard;
        vec3 gold = vec3(1.12, 0.58, 0.16);
        vec3 ivory = vec3(1.42, 1.18, 0.70);
        vec3 col = mix(gold, ivory, clamp(body * 0.72 + lift, 0.0, 1.0));
        gl_FragColor = vec4(col, energy * uAlpha);
      }`,
  });
  const levelGlow = new THREE.Mesh(new THREE.PlaneGeometry(0.58, 1.16), levelGlowMat);
  levelGlow.position.y = 0.56;
  levelGlow.renderOrder = 11;
  levelGlow.frustumCulled = false;
  levelRoot.add(levelGlow);

  // 상승 스파크는 점 스프라이트가 아니라 짧은 세로 선이다. 텍스처 없는 네모 점보다
  // 쿼터뷰에서 가볍고, 14가닥 x 2버텍스라 활성 중 갱신 비용도 사실상 없다.
  const levelSparkPos = new Float32Array(LEVEL_UP_SPARKS * 2 * 3);
  const levelSparkGeo = new THREE.BufferGeometry();
  levelSparkGeo.setAttribute('position', new THREE.BufferAttribute(levelSparkPos, 3));
  const levelSparkMat = new THREE.LineBasicMaterial({
    color: 0xffe8a5, transparent: true, opacity: 0, depthWrite: false, fog: false,
    blending: THREE.AdditiveBlending,
  });
  const levelSparks = new THREE.LineSegments(levelSparkGeo, levelSparkMat);
  levelSparks.renderOrder = 14;
  levelSparks.frustumCulled = false;
  levelRoot.add(levelSparks);

  // 같은 패턴이 매번 정북에서 시작하지 않도록 발화할 때 회전값만 바꾼다.
  // 씨앗 자체는 고정해 레벨업마다 배열을 다시 만들지 않는다.
  const levelSparkSeed = [];
  const levelFract = n => n - Math.floor(n);
  for (let i = 0; i < LEVEL_UP_SPARKS; i++) {
    const a = levelFract(Math.sin((i + 1) * 91.73) * 43758.5453);
    const b = levelFract(Math.sin((i + 1) * 47.11) * 24634.6345);
    const c = levelFract(Math.sin((i + 1) * 13.57) * 15731.7431);
    levelSparkSeed.push({
      ang: a * Math.PI * 2,
      radius: 0.105 + b * 0.155,
      delay: c * 0.34,
      lift: 0.72 + b * 0.28,
      len: 0.025 + a * 0.035,
    });
  }

  let levelTarget = null;
  let levelAge = LEVEL_UP_T;
  let levelHeight = 2.4;
  let levelCount = 0;
  let levelSpin = 0;
  const levelAnchor = new THREE.Vector3();
  const levelStaticAnchor = new THREE.Vector3();

  // ★플립북 시트를 여기서 직접 읽는다(main.js 를 안 건드리려고).
  //   못 읽으면 절차 폴백으로 그린다 - 게임은 그대로 돈다.
  // ★밉맵을 끈다. 칸이 서로 붙어 있어서 밉 레벨이 올라가면 **옆 칸 그림이 섞인다**
  //   (다음 프레임이 유령처럼 겹쳐 보인다). 화면에서 2~4배 축소라 밉맵 없이도 된다.
  // ★colorSpace 를 안 건다. sRGB 로 읽으면 하드웨어가 선형으로 풀어서 0.45 가
  //   0.17 로 내려앉고 밝기 계단이 통째로 무너진다(bake_slash_flip.py '밝기 계약').
  // ── 시트 두 벌 (v94) ──
  // ★건틀릿에서 **유일하게 합격한 산출물**이 처치의 백색 패널 + 진홍 초승달이다
  //   (경계 먹선 51%. 나머지 파랑 획은 11~14%로 전부 탈락).
  //   합격작은 손대지 않는다 - 그래서 그 둘이 읽는 시트는 **옛 시트 그대로** 둔다.
  //   새로 구운 굵은 획 시트(slash_flip2, 칸 1024x448·획 몸통 0.632)는 이번에
  //   신설한 **화면공간 본 획**만 읽는다.
  //     slashMat  (화면 겹 붓자국)      -> slash_flip2  (★SCREEN_STROKE=0 이라 지금은 안 그린다)
  //     impfMat   (타격 지점 진홍 초승달) -> IMPACT_SHEET (v97 11-FX시트에서 codex 작화로 갈았다)
  //     impMat    (백색 패널의 획 실루엣) -> slash_flip   (합격작. 무수정)
  // ★새 시트가 없으면 slashMat 도 옛 시트로 내려간다(그림만 가늘어지고 안 깨진다).
  function mkSheet(t) {
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    t.generateMipmaps = false;
    t.minFilter = THREE.LinearFilter;
    t.magFilter = THREE.LinearFilter;
    return t;
  }
  let sheetName = '';
  new THREE.TextureLoader().load('./tex/slash_flip.png' + location.search, (t) => {
    mkSheet(t);
    impMat.uniforms.uTex.value = t;
    impMat.uniforms.uHasTex.value = 1;
    // ★타격 지점 참격은 아래 IMPACT_SHEET 가 주인이다. 여기서는 **비어 있을 때만** 꽂는다
    //   (두 로더가 같은 uniform 을 쓰므로 순서를 안 재우면 늦게 끝난 쪽이 이긴다.
    //    실제로 처음에 이 줄이 무조건 덮어써서 새 시트가 안 붙었다)
    if (!impfMat.uniforms.uTex.value) {
      impfMat.uniforms.uTex.value = t;
      impfMat.uniforms.uHasTex.value = 1;
    }
    // 새 시트가 아직/영영 안 오면 본 획도 여기에 붙는다
    if (!slashMat.uniforms.uTex.value) {
      slashMat.uniforms.uTex.value = t;
      slashMat.uniforms.uUseTex.value = 1;
      sheetName = './tex/slash_flip.png';
    }
  }, undefined, () => { /* 없으면 절차 폴백 */ });
  // ── 타격 지점 참격 시트 (v97 11-FX시트. codex 작화 장착) ──
  // ★여기 한 줄이 A/B 의 전부다. 되돌리려면 './tex/slash_flip.png' 로 바꾸면 끝난다
  //   (옛 시트 파일은 지우지 않았다). 재생 타이밍·팔레트 재칠은 한 글자도 안 건드렸다.
  //   못 읽으면 위 로더가 이미 옛 시트를 꽂아 놨으므로 조용히 옛 그림으로 돈다.
  new THREE.TextureLoader().load(IMPACT_SHEET + location.search, (t) => {
    impfMat.uniforms.uTex.value = mkSheet(t);
    impfMat.uniforms.uHasTex.value = 1;
  }, undefined, () => { /* 없으면 옛 시트 그대로 */ });
  new THREE.TextureLoader().load('./tex/slash_flip2.png' + location.search, (t) => {
    slashMat.uniforms.uTex.value = mkSheet(t);
    slashMat.uniforms.uUseTex.value = 1;
    sheetName = './tex/slash_flip2.png';
  }, undefined, () => { /* 없으면 위 폴백이 이미 걸려 있다 */ });

  const SLASH_DUR = FLIP_N * FRAME_T;      // 시트 전체 길이(참고용). 실제 수명은 slot.n
  // ★v94. 슬롯마다 **몇 장까지 재생할지(n)** 를 따로 든다. 시트는 여섯 장이지만
  //   지속 계약(본 획 2~4프레임) 때문에 화면 겹은 넉 장에서 끊는다. 남은 두 장
  //   (f4 散 · f5 殘)은 안 쓴다 - 그 두 장이 곧 "0.3~0.9초 덮음"의 절반이었다.
  const slashes = [];
  for (let i = 0; i < SLOTS; i++) slashes.push({ t: 9, col: 0, light: 0, n: SW_N, aK: 1 });
  let ring = 0;
  let lineT = 9, lineN = 4, lineSeed = 0;
  let ringT = 1, ringN = 0, wipeN = 0;
  // 임팩트 프레임: 남은 **렌더 프레임 수**(시간이 아니다)
  let impLeft = 0, impN = 0, impOn = 0, impBig = 0;
  let warm = 3;                // 남은 예열 프레임 수(아래 updateOverlay 끝 참조)
  // 마지막 붓자국이 앉은 화면 자리. 링의 월드 좌표를 여기서 되짚는다
  let lastSlashT = -99;
  const lastSlashNDC = new THREE.Vector2();
  // 임팩트 프레임과 찢김선이 쓰는 '방금 그은 획'
  const lastStroke = { ang: 0, x: 0, y: 0, len: SL_LEN, thk: SL_THK, col: 0, big: 0 };

  // 붓자국 하나. ang = 화면 각도(라디안, +x 오른쪽 / +y 위), off = 화면 중심 기준 위치
  // kind 는 'water' / 'kill'. 안 주면 지금 도는 기술을 보고 알아서 고른다(detectKind).
  // ★main.js 는 이 함수를 **처치한 프레임에만** 부른다. 그래서 여기가 곧
  //   "한 놈을 베었다"는 신호이고, 찢김선도 여기서 같이 튼다.
  function slash(ang, offX, offY, big, kind) {
    stroke(ang, offX, offY, big, kind, false);
    // 처치마다 짧게 한 번(전멸은 wipe 가 길게 다시 튼다)
    speedLines(SPD_N, ang, lastStroke.x, lastStroke.y, false);
  }

  // 획 한 장을 슬롯에 앉힌다. light = 안 죽인 명중(작고 옅게. 찢김선·임팩트는 없다)
  // opt = { n: 재생할 장 수, lenK/thkK: 길이·굵기 배수, aK: 알파 배수 } (v94. 동반 획용)
  function stroke(ang, offX, offY, big, kind, light, opt) {
    opt = opt || {};
    // ── v96. 화면 겹은 안 그린다(위 SCREEN_STROKE 주석) ──
    // ★그래도 **자리·각도·크기는 반드시 기록한다.** 임팩트 프레임의 먹 실루엣,
    //   찢김선, 전멸 링이 전부 이 값을 되짚어 쓴다. 여기서 일찍 나가면 그 셋이
    //   조용히 옛 자리에 그려진다(눈으로는 "링이 엉뚱한 데서 터진다"로 보인다).
    if (!SCREEN_STROKE) {
      if (opt.comp) return;                    // 동반 획은 기록도 안 한다
      const lenQ = (big ? SL_LEN_BIG : SL_LEN) * (light ? SL_HIT_K : 1.0);
      const thkQ = (big ? SL_THK_BIG : SL_THK) * (light ? 0.80 : 1.0);
      if (!light) {
        lastSlashT = performance.now() * 0.001;
        lastSlashNDC.set((offX || 0) / (camera.aspect || 1), offY || 0);
        lastStroke.ang = ang;
        lastStroke.x = offX || 0; lastStroke.y = offY || 0;
        lastStroke.len = lenQ; lastStroke.thk = thkQ;
        lastStroke.col = Math.abs(Math.sin(ang)) < FLIP_H_SIN ? 0 : 1;
        lastStroke.big = big ? 1 : 0;
      }
      return;
    }
    const s = slashes[ring];
    const i = ring;
    ring = (ring + 1) % SLOTS;
    s.t = 0;
    s.n = Math.max(1, Math.min(FLIP_N, opt.n || (light ? SW_N_LIGHT : SW_N_KILL)));
    s.aK = opt.aK === undefined ? 1 : opt.aK;
    // 획 종류: 화면에서 수평에 가까우면 가로베기 칸, 아니면 대각베기 칸.
    // 벤 각도와 그림의 휨이 어긋나면 "붙여 놓은 스티커"로 보인다.
    s.col = Math.abs(Math.sin(ang)) < FLIP_H_SIN ? 0 : 1;
    // kind 'el' = 지금 든 칼의 원소 색(setSwingPalette 로 들어온다). 그 밖은 종전대로.
    const pal = kind === 'el' ? PAL_EL : (detectKind(kind) ? PAL_WATER : PAL_KILL);
    // ★palK = 획마다 색 계단을 통째로 밝게/어둡게 민다. 같은 팔레트로 세 획을 겹치면
    //   프레임 안 색이 네 가지뿐이라 "2톤 그림"이 된다. 획끼리 한 단씩 어긋나야
    //   귀멸처럼 색이 고르게 퍼진다(먹은 안 민다 - 먹선은 늘 먹이어야 한다).
    const pk = opt.palK || 1;
    slashMat.uniforms.uInk.value[i].setHex(pal.ink);
    slashMat.uniforms.uEdge.value[i].setHex(pal.edge).multiplyScalar(pk);
    slashMat.uniforms.uMid.value[i].setHex(pal.mid).multiplyScalar(pk);
    slashMat.uniforms.uCore.value[i].setHex(pal.core).multiplyScalar(pk > 1 ? 1 : pk);
    slashMat.uniforms.uThr.value[i].set(pal.thr[0], pal.thr[1], pal.thr[2]);
    // 링이 쓸 자리. offX 는 main.js 가 aspect 를 곱해 넘긴 값이라 되나눠 NDC 로 돌린다
    // ★안 죽인 명중(light)은 여기 안 남긴다. 전멸 링이 "마지막으로 **벤** 자리"를
    //   되짚을 때 스친 자국에 끌려가면 링이 엉뚱한 데서 터진다.
    if (!light) {
      lastSlashT = performance.now() * 0.001;
      lastSlashNDC.set((offX || 0) / (camera.aspect || 1), offY || 0);
    }
    const k = light ? SL_HIT_K : 1.0;
    const len = (big ? SL_LEN_BIG : SL_LEN) * k * (opt.lenK || 1) * (0.86 + Math.random() * 0.28);
    const thk = (big ? SL_THK_BIG : SL_THK) * (light ? 0.80 : 1.0) * (opt.thkK || 1)
              * (0.85 + Math.random() * 0.30);
    slashMat.uniforms.uAng.value[i] = ang;
    slashMat.uniforms.uOff.value[i].set(offX || 0, offY || 0);
    // ★v94. 동반 획은 절반 확률로 시트를 **좌우로 뒤집어** 읽는다(uLen 부호).
    //   안 그러면 세 장이 똑같은 창날 모양으로 겹쳐서 "복사한 스티커 셋"으로 보인다.
    //   셰이더는 q.x /= uLen 뒤 abs(q.x) 로만 자르므로 음수를 그대로 먹는다.
    const mir = opt.comp && Math.random() < 0.5 ? -1 : 1;
    // ★길이는 화면 가로 반폭(=aspect, 16:9 에서 1.78)이 기준이다. 1.85 로 뒀더니
    //   한 획이 화면을 대각으로 다 가로질러서 붓자국이 아니라 렌즈 플레어로 보였다.
    slashMat.uniforms.uLen.value[i] = len * mir;
    slashMat.uniforms.uThk.value[i] = thk;
    slashMat.uniforms.uCol.value[i] = s.col;
    slashMat.uniforms.uSeed.value[i] = Math.random() * 10;
    slashMat.uniforms.uFrm.value[i] = 0;
    slashMat.uniforms.uFa.value[i] = FLIP_A[0];
    slashMat.uniforms.uP.value[i] = 0;
    s.light = light ? 1 : 0;
    slashMesh.visible = true;
    // ★동반 획(opt.comp)은 lastStroke 를 안 건드린다. 임팩트 컷·찢김선이 되짚는
    //   "방금 그은 획"은 언제나 **본 획**이어야 한다(동반 획은 작고 어긋나 있다).
    if (!light && !opt.comp) {
      lastStroke.ang = ang;
      lastStroke.x = offX || 0; lastStroke.y = offY || 0;
      lastStroke.len = len; lastStroke.thk = thk;
      lastStroke.col = s.col; lastStroke.big = big ? 1 : 0;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 휘두름 본 획 (v94 신설) — 화면공간 문법의 주인공
  //
  // 왜 새로 만드나: 지금까지 화면에 큰 획이 그어지는 건 **처치한 프레임뿐**이었다.
  // 그래서 안 죽는 적을 상대로 계속 칼을 휘두르면 화면에 남는 큰 그림이 없고,
  // 월드에 눕는 궤적 리본만 보인다 = 심사관이 본 "지형 원근에 눕는 깔개".
  // 귀멸은 반대다. **벨 때마다 화면에 획이 한 장 그어진다.** 뭔가 맞았는지는 그
  // 다음 문제다. 그래서 스윙이 시작되는 그 프레임에 이걸 부른다(main.js 궤적 구역).
  //
  // 구성: 본 획 한 장 + 어긋난 동반 획 한 장. 한 획만 그으면 "칼빔 한 줄"이고,
  //       두 획이 겹쳐야 붓으로 읽힌다(귀멸 프레임은 거의 항상 2~3획이 겹쳐 있다).
  // ★길이는 판정 리치에 못 박혀 있고(SL_LEN 주석), 화면 존재감은 **굵기**로 낸다.
  function swing(ang, offX, offY, big, kind) {
    stroke(ang, offX, offY, big, kind, false, { n: SW_N });
    // 동반 획 셋. 각도를 살짝 틀고 획에 **수직으로** 밀어 어긋나게 깐다.
    // ★일격기는 더 크게 벌린다. 겹쳐 쌓으면 새 면적이 안 생긴다(실측: 획을 통째로
    //   1.3배 키웠는데 점유는 15% 밖에 안 올랐다). 면적은 **간격**에서 나온다.
    const spread = big ? 1.75 : 1.0;
    const sn = Math.sin(ang), cs = Math.cos(ang);
    for (const c of SW_COMP) {
      const push = c.push * spread * (0.78 + Math.random() * 0.44);
      stroke(ang + c.dAng * (0.6 + Math.random() * 0.8),
             (offX || 0) - sn * push,
             (offY || 0) + cs * push,
             big, kind, false,
             { n: c.n, lenK: c.lenK, thkK: c.thkK, aK: c.aK, palK: c.palK, comp: 1 });
    }
  }

  // 찢김선. n = 몇 **장**(24fps 기준) 갈지. ang = 벤 방향. at = 타격점(화면 좌표)
  function speedLines(n, ang, atX, atY, long) {
    lineT = 0;
    lineN = Math.max(1, n | 0);
    lineSeed = Math.random() * 20;
    lineMat.uniforms.uAng.value = ang || 0;
    lineMat.uniforms.uAt.value.set(atX || 0, atY || 0);
    lineMat.uniforms.uLong.value = long ? 1 : 0;
    lineMat.uniforms.uP.value = 0;
    lineMesh.visible = true;
  }

  // 임팩트 프레임을 n 장 예약한다. **렌더 프레임 수**다(1 = 딱 한 장).
  // ★IMPACT_CUT 이 0 이면 여기서 끝난다(오너 지시. 위 스위치 주석 참조).
  //   예약 자체를 안 하므로 impLeft·impN·impOn 이 전부 0 으로 남는다 = 계측 창구가
  //   "컷이 한 번도 안 떴다"를 그대로 증언한다. lastPanelT 도 안 건드리니
  //   panelWanted() 는 늘 참이고 panelMerged 도 0 에 머문다(가짜 병합 기록 방지).
  function impact(n) {
    if (!IMPACT_CUT) return;
    n = n | 0;
    if (n >= 2) impBig = 1;                 // 두 장짜리(전멸·보스)는 컷도 크게 찢는다
    impLeft = Math.max(impLeft, n);
    impN++;
    lastPanelT = performance.now() * 0.001;
  }
  // ── 더블 패널 병합 (v94. 심사 격차 5) ──
  // 다중 처치에서 전면 백색 패널이 0.75초 간격으로 두 번 뜨면 **연출이 아니라 점멸**로
  // 읽힌다("모니터가 깜빡인 줄 알았다"). 한 번 뜬 뒤 이 창 안의 추가 처치는 패널을
  // 다시 안 띄운다 - 초승달(impactSlash)·먹 튀김(pop)·히트스톱은 그대로 다 간다.
  // ★전멸(wipe)은 예외다. 그건 "마지막 한 마리"라는 별도의 방점이고 두 장짜리다.
  const PANEL_MERGE = 0.80;
  let lastPanelT = -99;
  let panelMerged = 0;             // 병합해서 안 띄운 횟수(검증 창구)
  function panelWanted() {
    return performance.now() * 0.001 - lastPanelT > PANEL_MERGE;
  }

  // 그 자리에 링을 한 번 편다.
  function ringAt(x, z) {
    if (!ringMat.map) return false;
    ringMesh.position.set(x, groundLevel(x, z) + RING_LIFT, z);
    // 매번 같은 각도로 찍히면 도장으로 보인다
    ringMesh.rotation.set(-Math.PI / 2, 0, Math.random() * Math.PI * 2);
    ringMesh.scale.set(RING_S0, RING_S0, 1);
    ringMat.opacity = RING_ALPHA;
    ringMesh.visible = true;
    ringT = 0;
    ringN++;
    return true;
  }

  // 자리를 안 받았을 때: 마지막 붓자국의 화면 좌표를 월드로 되짚는다.
  // ★바닥 평면과 만나게 하면 안 된다. 붓자국이 앉은 자리는 요괴가 **맞은 자리**(가슴께)라
  //   광선을 바닥까지 늘리면 카메라 반대쪽으로 1m 넘게 밀린다. 가슴 높이 평면과 만난다.
  const _rayA = new THREE.Vector3(), _rayD = new THREE.Vector3();
  function ringFromLastSlash() {
    if (!ringMat.map) return false;
    // 같은 프레임에 그은 붓자국만 믿는다. 보스 사망도 wipe() 를 부르는데 그쪽은
    // 붓자국이 없어서 옛날 자리에 링이 찍히면 엉뚱한 데서 터진다.
    if (performance.now() * 0.001 - lastSlashT > RING_FRESH) return false;
    _rayA.set(lastSlashNDC.x, lastSlashNDC.y, -1).unproject(camera);
    _rayD.set(lastSlashNDC.x, lastSlashNDC.y, 1).unproject(camera).sub(_rayA);
    if (Math.abs(_rayD.y) < 1e-4) return false;
    const t = (FLOOR_FALLBACK + RING_HIT_H - _rayA.y) / _rayD.y;
    if (t < 0) return false;
    return ringAt(_rayA.x + _rayD.x * t, _rayA.z + _rayD.z * t);
  }

  // 플레이어 루트(Object3D), 루트의 position(Vector3), 또는 {x,y,z} 모두 받는다.
  // Vector3를 넘긴 경우도 매 프레임 다시 읽으므로 이동하는 캐릭터에 그대로 붙어 간다.
  function levelAnchorFrom(target) {
    let t = typeof target === 'function' ? target() : target;
    if (!t) return false;
    if (t.isObject3D && typeof t.getWorldPosition === 'function') {
      t.getWorldPosition(levelAnchor);
      return true;
    }
    if (t.position && Number.isFinite(t.position.x) && Number.isFinite(t.position.z)) t = t.position;
    if (!Number.isFinite(t.x) || !Number.isFinite(t.z)) return false;
    levelAnchor.set(t.x, Number.isFinite(t.y) ? t.y : groundLevel(t.x, t.z), t.z);
    return true;
  }

  // UI가 레벨 변화를 감지한 순간 부르는 단 하나의 문.
  // target을 생략하면 평시에도 열려 있는 __root를 우선 사용하고,
  // 개발 진단 객체의 __dbg.root를 마지막 보험으로 쓴다.
  function levelUp(target, height) {
    const fallback = window.__root || (window.__dbg && window.__dbg.root);
    levelTarget = target || fallback || null;
    if (!levelAnchorFrom(levelTarget)) return false;
    levelStaticAnchor.copy(levelAnchor);
    let h = typeof height === 'function' ? height() : height;
    h = Number(h);
    levelHeight = Number.isFinite(h) && h > 0 ? Math.max(1.0, Math.min(3.2, h)) : 2.4;
    levelAge = 0;
    levelCount++;
    levelSpin = (levelCount * 2.3999632297) % (Math.PI * 2); // 황금각: 반복 도장 느낌 방지
    levelRoot.visible = true;
    updateLevelUp(0);
    return true;
  }

  // 실제 시간으로 늙힌다. 히트스톱 때문에 레벨업 빛이 2~3초 남아 화면을 가리지 않는다.
  function updateLevelUp(rawDt) {
    if (levelAge >= LEVEL_UP_T) return;
    if (!levelAnchorFrom(levelTarget)) levelAnchor.copy(levelStaticAnchor);
    levelRoot.position.copy(levelAnchor);
    levelRoot.scale.setScalar(levelHeight);

    const p = Math.max(0, Math.min(1, levelAge / LEVEL_UP_T));
    const enter = Math.min(1, p / 0.10);
    const fadeP = Math.max(0, (p - 0.60) / 0.40);
    const fade = 1 - fadeP * fadeP;
    const bell = Math.pow(Math.max(0, Math.sin(p * Math.PI)), 0.72);
    const easeOut = 1 - (1 - p) * (1 - p);

    // 발밑 고리는 빠르게 넓어지고, 두 번째 고리는 몸을 훑으며 올라간다.
    levelGroundRing.scale.setScalar(0.72 + easeOut * 0.40);
    levelGroundMat.opacity = 0.42 * enter * fade;
    levelRiseRing.position.y = 0.08 + easeOut * 0.83;
    levelRiseRing.scale.setScalar(0.82 + p * 0.28);
    levelRiseMat.opacity = 0.58 * bell * fade;

    // 베일은 월드의 y축을 지키면서 카메라를 향한다(완전 빌보드처럼 눕지 않는다).
    const dx = camera.position.x - levelRoot.position.x;
    const dz = camera.position.z - levelRoot.position.z;
    levelGlow.rotation.set(0, Math.atan2(dx, dz), 0);
    levelGlowMat.uniforms.uProgress.value = p;
    levelGlowMat.uniforms.uAlpha.value = 0.58 * bell * fade;

    for (let i = 0; i < LEVEL_UP_SPARKS; i++) {
      const s = levelSparkSeed[i];
      const o = i * 6;
      const q = (p - s.delay) / Math.max(0.001, 1 - s.delay);
      if (q <= 0 || q >= 1) {
        levelSparkPos[o] = levelSparkPos[o + 1] = levelSparkPos[o + 2] = 0;
        levelSparkPos[o + 3] = levelSparkPos[o + 4] = levelSparkPos[o + 5] = 0;
        continue;
      }
      const a = s.ang + levelSpin + q * 0.34;
      const radius = s.radius * (0.88 + q * 0.42);
      const x = Math.cos(a) * radius;
      const z = Math.sin(a) * radius;
      const y = 0.055 + q * s.lift;
      const len = s.len * (0.75 + (1 - q) * 0.45);
      levelSparkPos[o] = x;
      levelSparkPos[o + 1] = y;
      levelSparkPos[o + 2] = z;
      levelSparkPos[o + 3] = x * 1.025;
      levelSparkPos[o + 4] = y + len;
      levelSparkPos[o + 5] = z * 1.025;
    }
    levelSparkGeo.attributes.position.needsUpdate = true;
    levelSparkMat.opacity = 0.68 * bell * fade;

    levelAge += Math.max(0, Number.isFinite(rawDt) ? rawDt : 0);
    if (levelAge >= LEVEL_UP_T) {
      levelAge = LEVEL_UP_T;
      levelRoot.visible = false;
      levelGroundMat.opacity = 0;
      levelRiseMat.opacity = 0;
      levelSparkMat.opacity = 0;
      levelGlowMat.uniforms.uAlpha.value = 0;
      levelTarget = null;
    }
  }

  // ── 검증용 프레임 번호 ──
  // ★"임팩트 프레임이 정확히 1프레임인가"는 **렌더된 프레임 수**로만 잴 수 있다.
  //   시간(ms)으로 재면 프레임 길이가 흔들릴 때 1프레임인지 2프레임인지 못 가린다.
  //   updateOverlay 는 composer.render() 직전에 프레임당 딱 한 번 불린다(main.js).
  let fxFrame = 0;

  // 매 프레임 **실제 dt** 로. 연출은 멈춘 시간에도 흘러야 한다.
  function updateOverlay(rawDt) {
    fxFrame++;
    // ── 임팩트 프레임 ──
    // ★여기서 켜고 **다음 호출에서 끈다.** main.js 가 이 함수 바로 뒤에 render 를
    //   부르므로, 화면에 남는 시간이 정확히 예약한 렌더 프레임 수가 된다.
    if (impLeft > 0) {
      impLeft--;
      impOn = 1;
      impMesh.visible = true;
      impMat.uniforms.uAt.value.set(lastStroke.x, lastStroke.y);
      impMat.uniforms.uAng.value = lastStroke.ang;
      impMat.uniforms.uLen.value = lastStroke.len;
      impMat.uniforms.uThk.value = lastStroke.thk;
      impMat.uniforms.uCol.value = lastStroke.col;
      impMat.uniforms.uFrm.value = 2;          // 획이 제일 굵은 장을 실루엣으로 쓴다
      impMat.uniforms.uBig.value = impBig ? 1 : lastStroke.big;
      if (impLeft <= 0) impBig = 0;
      impMat.uniforms.uSeed.value = Math.random() * 9;
      impMat.uniforms.uAspect.value = camera.aspect;
    } else if (impOn) {
      impOn = 0;
      impMesh.visible = false;
    }
    // ★은신 실루엣은 화면 겹과 아무 상관이 없지만 여기 얹는다. main.js 가 매 프레임
    //   부르는 함수가 이것뿐이고, main.js 는 못 건드리기 때문이다(v84 QA S13).
    silhouette(impOn === 1);
    // ── 참격 플립북 ──
    // ★보간이 없다. 1/24 초마다 **다음 칸으로 점프**할 뿐이다. 그래서 60fps 화면에서
    //   같은 그림이 2~3프레임씩 붙들려 있고, 그게 작화 프레임의 계단감이다.
    let any = false;
    for (let i = 0; i < SLOTS; i++) {
      const s = slashes[i];
      const fr = Math.floor(s.t / FRAME_T);
      // ★v94. FLIP_N(6) 이 아니라 **슬롯이 든 s.n** 에서 끊는다(지속 계약).
      if (fr >= s.n) {
        slashMat.uniforms.uFrm.value[i] = -1;
        slashMat.uniforms.uP.value[i] = 1;
        continue;
      }
      slashMat.uniforms.uFrm.value[i] = fr;
      slashMat.uniforms.uFa.value[i] = FLIP_A[fr] * (s.light ? SL_HIT_A : 1.0) * s.aK;
      // 절차 폴백도 계단으로 돈다(시트를 못 읽었을 때만 쓰인다)
      slashMat.uniforms.uP.value[i] = (fr + 0.5) / s.n;
      s.t += rawDt;
      any = true;
    }
    slashMesh.visible = any;
    // ── 찢김선 ── 이것도 장 단위다. 장마다 씨앗을 갈아 매번 다시 그린 것처럼 만든다
    {
      const fr = Math.floor(lineT / FRAME_T);
      if (fr >= lineN) {
        lineMat.uniforms.uP.value = 1;
        lineMesh.visible = false;
      } else {
        lineMat.uniforms.uP.value = fr / lineN;
        lineMat.uniforms.uSeed.value = lineSeed + fr * 7.13;
        lineMesh.visible = true;
        lineT += rawDt;
      }
    }

    if (bloom) {
      if (bloomT > 0) {
        bloomT -= rawDt;
        const k = Math.max(0, bloomT / BLOOM_PULSE_T);
        bloom.strength = bloomBase + BLOOM_PULSE * Math.sin(k * Math.PI);
      } else if (bloom.strength !== bloomBase) bloom.strength = bloomBase;
    }

    // 타격 지점 참격(월드 플립북). ★게임시계로 늙는다(히트스톱 중에는 한 장 홀드).
    // ★아래 early return 보다 먼저 와야 한다. 화면 겹이 다 꺼진 뒤에도 이건 살아 있다.
    updateImpactSlashes(rawDt * timeScale);
    // 타격 팝(흰 번쩍 + 먹 튀김). 같은 이유로 게임시계, 같은 이유로 early return 앞.
    updatePops(rawDt * timeScale);
    // ★18차. 접점 에너지 파열. 같은 게임시계·같은 1/24 칸이고, 부르는 쪽이 없으면
    //   빈 층이다(FX_V18=0 이면 main.js 가 아예 안 부른다 = 슬롯이 늘 0개).
    updateBursts(rawDt * timeScale);
    // 칼끝 포말 마루. 같은 게임시계·같은 1/24 칸이며, 데이터가 안 오면 조용히 비어 있다.
    updateFoamCrests(rawDt * timeScale);
    // 레벨 상승 빛. UI 창을 대체하는 캐릭터 부착 신호라 실제 시간으로 짧게 끝낸다.
    updateLevelUp(rawDt);

    // 링. 지면 데칼이라 자리는 한 번 정하면 그대로고 크기·투명도만 간다.
    // ★아래 early return 보다 먼저 와야 한다. 붓자국이 다 사라진 뒤에도 링은 남는다.
    if (ringT < 1) {
      ringT += rawDt / RING_T;
      if (ringT >= 1) { ringT = 1; ringMesh.visible = false; ringMat.opacity = 0; }
      else {
        const e = 1 - (1 - ringT) * (1 - ringT);      // 처음에 확 퍼지고 끝에서 멎는다
        const s = RING_S0 + (RING_S1 - RING_S0) * e;
        ringMesh.scale.set(s, s, 1);
        ringMat.opacity = RING_ALPHA * Math.pow(1 - ringT, 1.4);
      }
    }

    // ── 셰이더 예열 (v91) ──
    // ★첫 참격에서 화면이 1~2초 멎는다. 실측(2026-08-10, 부하 있는 기계):
    //   평시 30fps -> 겹을 **처음 그리는** 그 프레임에 4.5fps. 원인은 연출이 아니라
    //   **셰이더 프로그램을 그때 컴파일**하는 것이다(three 는 처음 그릴 때 굽는다).
    //   그래서 시작하자마자 넓이 0 짜리로 한 번 그려 미리 구워 둔다. 픽셀은 하나도
    //   안 나오지만 프로그램은 만들어진다. 첫 처치의 멎음이 사라진다.
    if (warm > 0) {
      warm--;
      camera.getWorldDirection(_fwd);
      // ★v94. 신규 재질(타격 팝)도 같은 패스에 편입한다. 팝은 월드 좌표 풀이라
      //   평소에는 메시 변환이 항등이어야 한다 - 예열이 끝나는 프레임에 되돌린다.
      for (const m of [slashMesh, lineMesh, impMesh, popMesh]) {
        m.visible = true;
        m.position.copy(camera.position).addScaledVector(_fwd, OVER_Z);
        m.quaternion.copy(camera.quaternion);
        m.scale.set(1e-5, 1e-5, 1);
      }
      // 레벨업 때 처음 셰이더를 굽느라 끊기지 않게 세로 베일도 같은 3프레임에 예열한다.
      // 알파 0 · 미소 크기라 부팅 화면에는 한 픽셀도 남지 않는다.
      if (levelAge >= LEVEL_UP_T) {
        levelRoot.visible = true;
        levelRoot.position.copy(camera.position).addScaledVector(_fwd, OVER_Z);
        levelRoot.scale.setScalar(1e-5);
        levelGlowMat.uniforms.uAlpha.value = 0;
      }
      if (warm === 0) {
        for (const m of [slashMesh, lineMesh, impMesh]) m.visible = false;
        popMesh.position.set(0, 0, 0);
        popMesh.quaternion.identity();
        popMesh.scale.set(1, 1, 1);
        popMesh.visible = true;          // 팝은 늘 켜 둔다(알파 0 이면 전부 discard)
        if (levelAge >= LEVEL_UP_T) {
          levelRoot.visible = false;
          levelRoot.position.copy(levelStaticAnchor);
          levelRoot.scale.setScalar(levelHeight);
        }
      }
      return;
    }
    // 화면 겹을 카메라 앞에 놓는다(위치·회전·크기 전부 이번 프레임 카메라 기준)
    if (!slashMesh.visible && !lineMesh.visible && !impMesh.visible) return;
    camera.getWorldDirection(_fwd);
    const h = 2 * OVER_Z * Math.tan(camera.fov * Math.PI / 360);
    const w = h * camera.aspect;
    slashMat.uniforms.uAspect.value = camera.aspect;
    lineMat.uniforms.uAspect.value = camera.aspect;
    for (const m of [slashMesh, lineMesh, impMesh]) {
      if (!m.visible) continue;
      m.position.copy(camera.position).addScaledVector(_fwd, OVER_Z);
      m.quaternion.copy(camera.quaternion);
      m.scale.set(w, h, 1);
    }
  }

  // -------------------------------------------------------------------------
  // 가려짐 실루엣 (v84 QA S13 은신 → v88 QA S2 상시)
  //
  // 문제: 앞잎 카드가 몸을 100% 가려서 **내가 어디 있는지 화면에서 사라진다.**
  //   stealth.js 는 이미 몸 앞의 잎을 갈라 놓는 장치(uHole)를 갖고 있지만, 잎이
  //   빽빽한 자리에서는 그것만으로 안 뚫린다. 그리고 stealth.js 는 못 건드린다.
  //   ★v88 QA: 같은 일이 수풀 밖에서도 난다. 석탑 뒤 · 보스 밀착 · 절벽 뒤에서
  //     플레이어가 통째로 사라진다. 고정 쿼터뷰라 카메라를 돌려 피할 수도 없다.
  //     그래서 이 장치를 **평상시에도 켠다.** 다만 톤을 갈라야 한다(아래 두 재질).
  //
  // 수: **가려진 조각만 그리는 두 번째 패스.** 스텐실을 안 쓰고 깊이 비교만 뒤집는다.
  //   플레이어 메시와 지오메트리·뼈를 공유하는 껍데기를 한 벌 더 만들고
  //   depthFunc = GreaterDepth 로 그린다. 즉 "내 앞에 뭔가 있는 픽셀"에서만 통과한다.
  //     · 안 가려진 곳: 깊이가 딱 같으므로(같은 지오메트리) 부등호가 거짓 -> 안 그린다
  //     · 잎에 가린 곳: 잎이 더 앞이라 부등호가 참 -> 먹빛 실루엣이 잎 위에 얹힌다
  //   그래서 "잎 사이로 먹 그림자가 비친다"가 되고, 몸을 다시 그리는 게 아니라
  //   가려진 부분만 그리므로 **은신이 풀린 것처럼 보이지도 않는다.**
  // ★은신 판정에는 한 줄도 안 닿는다. 그림자·소리 반경·발각 계산은 stealth.js 것이다.
  // ★뼈 계산은 원본이 이미 한 것을 그대로 쓴다(skeleton 공유). 늘어나는 건 숨어 있는
  //   동안의 드로우콜 열 개 남짓뿐이다(아래 SIL_MIN_TRI 로 걸러서 그 수를 잡아 뒀다).
  //   실측 60fps 유지(2026-08-10, 수풀 안 · 요괴 39마리 상태에서 58~60).
  // ★색은 실측으로 골랐다(2026-08-10, BUSH_16 확대 크롭 비교).
  //   · 먼저 붉은색 알파 1 로 찍어 **실루엣이 실제로 그려지는지** 눈으로 확인했고
  //   · 먹(#120e14) 알파 0.62 는 잎 그늘과 구별이 안 됐다(어두운 데 어두운 걸 얹은 꼴)
  //   · 테두리를 잎빛(#6f8a63)으로 두면 잎에 그대로 녹아든다. **종이색**이라야
  //     초록 위에서 윤곽이 잡힌다. 이 한 줄이 "보인다/안 보인다"를 갈랐다.
  // ★v94. A3 실측(handoff_enemy.md ②)으로 값을 다시 잡았다.
  //   BUSH_13 에서는 stealth.js 의 먹을 3배 어둡게 해도 화면이 1.5/255 밖에 안 움직였다.
  //   앞잎 카드가 몸을 덮는 자리에서 화면에 나오는 것은 stealth.js 의 먹이 아니라
  //   **이 껍데기**이기 때문이다(`debug.tune({inkLo,inkHi})` 을 0↔1 로 흔든 실측이 증거).
  //   알파 0.80 은 초록 잎이 20% 비쳐서 "형광 잎 위 흰 와이어프레임"이 됐다.
  //   → 알파를 올리고 림 비중을 낮춘다. "안쪽이 먹, 테두리는 거들기"가 맞는 순서다.
  const SIL_COLOR = 0x080609;   // 먹. 안쪽은 거의 검다(한 단 더 짙게)
  const SIL_ALPHA = 0.92;       // 0.80 -> 0.92. 잎이 비치는 몫을 20% -> 8% 로
  const SIL_RIM = 0xa89878;     // 종이색 윤곽. 밝기를 한 단 낮춰 '와이어프레임' 인상을 없앤다
  // ── 상시(가려짐) 실루엣 색 (v88 QA S2) ──
  // ★은신 실루엣과 **반대로 짠다.** 은신은 "잎 속에 숨은 먹 그림자"라 안쪽이 짙고
  //   윤곽은 거들기만 한다. 상시는 "저 뒤에 내가 있다"는 표시라 **윤곽이 주인공**이고
  //   안쪽 먹은 옅게 깐다. 그래야 둘이 한눈에 구별되고, 평상시 화면을 안 잡아먹는다.
  //   · 밝은 회색 석탑 뒤 : 옅은 먹만으로도 충분히 어두워져 형체가 잡힌다
  //   · 어두운 보스 몸 뒤 : 먹은 배경에 묻힌다. **밝은 종이색 림**이 유일한 단서라
  //     림 비중(0.85)과 지수(2.0)를 은신(0.50 / 2.6)보다 크게 잡았다
  // ★네 후보를 세 배경(밝은 석탑 / 붉고 어두운 보스 / 회색 절벽)에서 나란히 찍어 골랐다
  //   (renders/history/v88_fix/tone/SHEET_tone.png, 2026-08-10).
  //     a 0.42 · 림 0.85 : 밝은 석탑 위에서 너무 옅어 형체가 안 잡힌다
  //     a 0.60 · 림 0.55 : 제일 선명하지만 은신 실루엣(0.80 · 0.50)과 구별이 흐려진다
  //     a 0.52 · 림 0.68 : 세 배경 다 읽히면서 은신보다 확실히 옅다  <- 이걸 골랐다
  // ★v94. 위 은신 실루엣과 같은 진단. 건틀릿 캐릭터 심사 1순위 "수풀 뒤에서 3~4초
  //   클립을 돌려도 플레이어를 못 찾겠다"의 xray 시트에 찍힌 것이 **이 조합**이었다
  //   (수풀이 아니라 소품 뒤를 지날 때). 알파 0.52 + 밝은 종이색 림 비중 0.68 이라
  //   밝은 배경 위에서는 안쪽 먹이 안 보이고 림만 남아 정확히 흰 와이어프레임이 된다.
  //   대형 소품이 플레이어를 완전히 가리는 문제(격차 7-①)의 답도 이것이다 -
  //   소품을 디더로 지우는 대신 **가려진 몸을 확실히 보이게** 한다(소품은 props.js 소유).
  const OCC_COLOR = 0x0f0c16;   // 먹. 은신보다 한 단만 옅다(옛 0x171320 보다 짙게)
  const OCC_ALPHA = 0.72;       // 0.52 -> 0.72. 안쪽 먹이 배경을 실제로 눌러야 형체가 잡힌다
  const OCC_RIM = 0xc8b998;     // 종이색이되 한 단 낮춘 밝기(흰 윤곽선 인상 제거)
  // ★깊이 편향(클립공간 z). 이게 없으면 **안 가려진 몸에도 실루엣이 낀다.**
  //   원인은 부동소수 오차가 아니라 **자기 자신에 의한 가림**이다. 칼·팔·하카마가
  //   몸통보다 앞에 있으니 몸통 껍데기 입장에서는 "내 앞에 뭔가 있다"가 참이 되어,
  //   마당 한복판에서 자기 칼 위에 자기 윤곽이 겹쳐 그려진다.
  //   그래서 껍데기를 카메라 쪽으로 당겨서 **몸에 붙어 있는 것은 가림으로 안 세게** 한다.
  //   실측(2026-08-10, 1300x772 · 8자리 스윕. 숫자는 260x290 크롭에서 바뀐 픽셀 수):
  //     bias        0      4e-5    1.5e-4   4e-4    1e-3
  //     마당 A   1620     1072      246       0       0     <- 자기 가림(없애야 하는 것)
  //     마당 B   1576     1052      248       0       0
  //     석탑 뒤  4797     4797     4797    4797    4797     <- 지켜야 하는 것
  //     절벽 뒤  4026     4021     3994    3940    1776     <- 1e-3 부터 깨진다
  //     보스 밀착2188     1785     1348    1304       0     <- 1e-3 부터 깨진다
  //   4e-4 가 유일하게 "자기 가림 0 · 셋 다 살아 있음"인 값이다.
  //   이 시점(24m · near 0.1 · far 200)에서 4e-4 NDC = 약 1.15m. 즉 몸에서 1.15m 안쪽에
  //   붙은 것만 가림으로 안 친다(= 내 칼과 내 옷). 은신 재질은 0 으로 둔다
  //   (v84 그림을 한 픽셀도 안 바꾼다. 은신은 몸 전체를 그리는 것이라 자기 가림이 안 보인다).
  const OCC_BIAS = 4e-4;
  function mkSilMaterial(col, rim, alpha, rimMix, rimPow, bias) {
    return new THREE.ShaderMaterial({
      transparent: true, depthTest: true, depthWrite: false,
      depthFunc: THREE.GreaterDepth,          // ★이 한 줄이 이 장치의 전부다
      side: THREE.FrontSide, fog: false,
      uniforms: { uCol: { value: new THREE.Color(col) },
                  uRim: { value: new THREE.Color(rim) },
                  uA: { value: alpha },
                  uRimMix: { value: rimMix },
                  uRimP: { value: rimPow },
                  uBias: { value: bias } },
      vertexShader: `
        #include <common>
        #include <skinning_pars_vertex>
        uniform float uBias;
        varying vec3 vN; varying vec3 vV;
        void main(){
          #include <beginnormal_vertex>
          #include <skinbase_vertex>
          #include <skinnormal_vertex>
          #include <begin_vertex>
          #include <skinning_vertex>
          vec4 mv = modelViewMatrix * vec4(transformed, 1.0);
          vN = normalize(normalMatrix * objectNormal);
          vV = normalize(-mv.xyz);
          gl_Position = projectionMatrix * mv;
          // 카메라 쪽으로 아주 조금 당긴다(w 를 곱해야 원근에 상관없이 같은 NDC 만큼)
          gl_Position.z -= uBias * gl_Position.w;
        }`,
      fragmentShader: `
        uniform vec3 uCol; uniform vec3 uRim; uniform float uA;
        uniform float uRimMix; uniform float uRimP;
        varying vec3 vN; varying vec3 vV;
        void main(){
          // 테두리(림)만 밝다. 안쪽은 먹. 납작한 검은 판이 아니라 '몸'으로 읽힌다.
          // ★2.0 -> 2.6. 34m 쿼터뷰에서 캐릭터가 90px 밖에 안 돼서, 지수가 낮으면
          //   림이 몸 전체를 덮어 회색 유령이 된다. 가장자리만 남겨야 먹 실루엣이다.
          //   (상시 실루엣은 반대로 림을 넓게 쓴다. uRimP 로 갈라 놨다)
          float rim = pow(1.0 - clamp(dot(normalize(vN), normalize(vV)), 0.0, 1.0), uRimP);
          vec3 c = mix(uCol, uRim, rim * uRimMix);
          gl_FragColor = vec4(c, uA * (0.80 + rim * 0.20));
        }`,
    });
  }
  // 은신용(v84 그대로) / 상시 가려짐용. **둘은 절대 같이 안 그린다**(아래 silhouette).
  // ★v94. 림 비중을 둘 다 낮췄다(은신 0.50 -> 0.40, 상시 0.68 -> 0.46).
  //   "안쪽이 먹, 테두리는 거들기"로 순서를 바로잡는다. 지수(rimP)는 올려서 림이
  //   가장자리에만 남게 한다 - 지수가 낮으면 림이 몸 전체를 덮어 회색 유령이 된다.
  const silMat = mkSilMaterial(SIL_COLOR, SIL_RIM, SIL_ALPHA, 0.40, 2.8, 0.0);
  const occMat = mkSilMaterial(OCC_COLOR, OCC_RIM, OCC_ALPHA, 0.46, 2.6, OCC_BIAS);
  // ★몇 벌을 뜰 것인가. 실측(2026-08-10): 플레이어 root 밑에 스킨드 메시가 **48개**
  //   있다(몸 char1 8,260삼각형 + 칼 7자루가 조각조각 = 나머지 47개, 합 36,092).
  //   전부 뜨면 숨어 있는 동안 드로우콜이 48개 늘어난다. 실루엣은 **모양**이 읽히면
  //   되는 것이라 그 값을 낼 이유가 없다. 그래서 두 가지로 거른다.
  //     · 지금 보이는 것만 (칼 일곱 자루 중 든 것 하나만 visible 이다)
  //     · 삼각형 120개 이상 (경첩·장식 같은 부스러기는 실루엣에 안 보인다)
  //   ★여기 원래 "실제로 남는 건 두셋"이라고 적혀 있었는데 **거짓말이었다.**
  //     실측(2026-08-10, kensa + 백아): 61벌이 남았다(몸 8,260 + 7,888 + 7,402 + 옷·칼
  //     조각 다수). 즉 은신 중에는 드로우콜이 61개 늘고 있었다.
  //   ★v91 에서 고쳤다. **삼각형 많은 순으로 상한을 건다**(아래 SIL_MAX_MESHES).
  //     실루엣은 겉모양만 읽히면 되는 그림이라, 큰 조각 몇 벌이면 윤곽이 같다.
  //     실측 삼각형 분포(kensa + 백아, 큰 순): 8260 · 7888 · 7402 · 3432 · 1292 x n · ...
  //     여섯 벌이면 몸 + 하카마 + 하오리 + 칼 + 큰 조각 둘이라 겉선이 다 나온다.
  //     (가림 셸이 OCC_MAX_MESHES 로 이미 쓰던 방식과 같은 문법이다)
  const SIL_MIN_TRI = 120;
  // ★상한은 안전판이지 본 수단이 아니다(진짜 원인은 아래 silLive 였다). 지금 이 캐릭터
  //   구성에서 실제로 보이는 껍데기는 7벌이고, 상한 8은 "캐릭터가 바뀌어도 예산이
  //   새지 않게" 못을 박아 두는 값이다. 고를 때는 삼각형 수가 아니라 **덩치**로 고른다
  //   (칼날은 길지만 폴리곤이 적다. 삼각형 순으로 자르면 칼이 실루엣에서 사라진다 - 실측).
  let SIL_MAX_MESHES = 8;      // setSilMax 로 갈아 끼울 수 있다(A/B 검증 전용)
  // ★상시 실루엣은 **드로우콜 예산이 다르다.** 은신은 수풀에 있는 동안만이라
  //   서넛까지 눈감아 줬지만, 상시는 한 판 내내 도는 값이다. 그래서 삼각형이
  //   많은 순으로 **딱 두 벌만** 켠다(= 몸 + 든 칼의 제일 큰 조각). 개수로 못을
  //   박아 두면 캐릭터·칼이 바뀌어도 예산이 안 새어 나간다. 실측 +1~2 드로우콜.
  // ★v94. 2 -> 3. 두 벌(몸 + 든 칼의 큰 조각)만 켜면 대형 소품 뒤에서 **하카마·하오리가
  //   빠진 반쪽 실루엣**이 뜬다(격차 7-① "석탑이 플레이어를 완전히 가림"의 잔여).
  //   큰 순으로 한 벌만 더 켜면 겉선이 닫힌다. 실측 +1 드로우콜.
  const OCC_MAX_MESHES = 3;
  function silTri(g) {
    return (g.index ? g.index.count : g.attributes.position.count) / 3;
  }
  // ★"61벌 문제"의 진범. o.visible 은 **자기 플래그**일 뿐이라, 부모 그룹이 꺼져 있어도
  //   참이다. 캐릭터는 CHARS[k].model.visible 로 그룹째 껐다 켜므로(main.js), 안 쓰는
  //   캐릭터 여섯의 몸·옷 메시가 전부 "보인다"로 세어졌다. 실측(2026-08-10):
  //     조상까지 따지기 전 61벌 -> 따진 뒤 **7벌**(kensa 몸 1 + 든 칼 백아 6조각).
  //   즉 54벌은 애초에 화면에 안 그려지는 것들이었다. 그림은 한 픽셀도 안 바뀐다.
  function silLive(o, root) {
    let p = o;
    while (p) {
      if (!p.visible) return false;
      if (p === root) return true;
      p = p.parent;
    }
    return true;                    // root 밑이 아니면 자기 플래그만 믿는다
  }
  function silSize(o) {
    const g = o.geometry;
    if (!g.boundingSphere) g.computeBoundingSphere();
    return g.boundingSphere ? g.boundingSphere.radius : 0;
  }
  function silWants(o, root) {
    return !!(o.isSkinnedMesh && o.geometry && o.skeleton && o.visible
              && silTri(o.geometry) >= SIL_MIN_TRI && silLive(o, root));
  }
  // 플레이어 메시가 갈릴 수 있다(F 키 캐릭터 교체 · 1~7 칼 교체). 그래서 매 프레임
  // 서명을 보고 달라졌을 때만 껍데기를 새로 만든다(서명에 uuid 를 이어 붙인다).
  const silMeshes = [];
  let silSig = '';
  let silOn = false;          // 지금 껍데기를 하나라도 그리는 중인가
  let silMode = '';           // '' | 'stealth' | 'occ'
  let silCheckAt = -9999;
  let silWarm = 0;            // 임팩트 컷 재질 예열용(껍데기를 처음 뜬 뒤 한 프레임)
  let occOn = true;           // 상시 실루엣 스위치(A/B 검증용. 은신 쪽은 안 탄다)
  let silSeen = 0;                  // 상한을 걸기 전에 몇 벌이 후보였나(검증용)
  function silRebuild(root) {
    for (const s of silMeshes) { if (s.mesh.parent) s.mesh.parent.remove(s.mesh); }
    silMeshes.length = 0;
    // ★먼저 **후보를 모으고 큰 순으로 줄을 세운 다음** 상한만큼만 껍데기를 뜬다.
    //   예전에는 만들고 나서 걸렀기 때문에 은신 중 드로우콜이 61개 늘었다.
    const cand = [];
    root.traverse(o => { if (silWants(o, root)) cand.push(o); });
    silSeen = cand.length;
    cand.sort((a, b) => silSize(b) - silSize(a));
    for (const o of cand.slice(0, SIL_MAX_MESHES)) {
      const g = new THREE.SkinnedMesh(o.geometry, silMat);
      g.frustumCulled = false;
      g.castShadow = false; g.receiveShadow = false;
      g.renderOrder = 7;            // 잎(1)·궤적(3~5)보다 뒤, 전멸 링(8)보다 앞
      g.bind(o.skeleton, o.bindMatrix);
      g.visible = false;
      scene.add(g);
      silMeshes.push({ mesh: g, src: o, tri: silTri(o.geometry), big: false });
    }
    // 큰 순으로 상시용 표를 준다(정렬은 껍데기를 새로 뜰 때만 한 번 돈다)
    silMeshes.slice().sort((a, b) => b.tri - a.tri)
      .slice(0, OCC_MAX_MESHES).forEach(s => { s.big = true; });
    silMode = '';                   // 재질을 다시 물려야 한다
    if (silMeshes.length) silWarm = 1;   // 임팩트 컷 재질을 미리 굽는다(아래 참조)
  }
  // imp = 임팩트 프레임인가. 그 한 장 동안에는 껍데기를 **통짜 먹**으로 그려서
  // 종이색 판 위에 사람 실루엣을 남긴다(귀멸의 그 컷이 이 그림이다).
  function silhouette(imp) {
    const root = window.__dbg && window.__dbg.root;
    if (!root) {
      if (silOn) { for (const s of silMeshes) s.mesh.visible = false; silOn = false; silMode = ''; }
      return;
    }
    // 상태는 stealth.js 를 **읽기만** 한다. 없으면 상시 모드로만 돈다.
    let hiding = false;
    try {
      const s = window.__stealth && window.__stealth.state();
      // 숨었을 때 + 수풀 안에서 들킨 동안까지. 수풀에 서 있는 내내 내가 보여야 한다.
      hiding = !!(s && (s.hidden || s.bush >= 0));
    } catch (e) { hiding = false; }
    // ★두 셸을 겹쳐 그리지 않는다. **같은 껍데기의 재질만 갈아 끼운다.**
    //   따로 한 벌을 더 만들면 은신 중에 먹이 두 번 얹혀 새까맣게 뭉치고
    //   드로우콜도 두 배가 된다.
    const mode = imp ? 'imp' : (hiding ? 'stealth' : 'occ');

    // 서명 확인은 0.25초에 한 번이면 된다(칼·캐릭터 교체는 사람 손으로 하는 일이다).
    // 매 프레임 48개 노드를 훑어 문자열을 잇는 건 내내 도는 공짜가 아니다.
    const nowS = performance.now();
    if (nowS - silCheckAt > 250) {
      silCheckAt = nowS;
      let sig = '';
      root.traverse(o => { if (silWants(o, root)) sig += o.uuid; });
      if (sig !== silSig) { silSig = sig; silRebuild(root); }
    }
    // ★임팩트 컷 재질(스킨드 통짜 먹)도 미리 굽는다. 안 그러면 첫 처치의 그 한 장에서
    //   화면이 멎는다(위 '셰이더 예열' 과 같은 이유). 투명도 0 으로 한 프레임만 그린다.
    if (silWarm > 0) {
      silWarm--;
      impInkMat.opacity = 0;
      for (const s of silMeshes) { s.mesh.material = impInkMat; s.mesh.visible = s.src.visible; }
      silMode = 'warm';
      return;
    }
    if (impInkMat.opacity !== 1) impInkMat.opacity = 1;   // 예열 다음 프레임에 되돌린다
    if (mode !== silMode) {
      const m = imp ? impInkMat : (hiding ? silMat : occMat);
      for (const s of silMeshes) {
        s.mesh.material = m;
        // 임팩트 프레임에서는 종이판(60) 위에 얹어야 한다. 평소 자리는 7이다.
        s.mesh.renderOrder = imp ? 62 : 7;
      }
      silMode = mode;
    }
    // ★자리를 맞출 일이 없다. bindMode 가 'attached' 라 껍데기의 변환이 스스로
    //   상쇄돼서 씬 루트에 그냥 붙여도 원본과 정확히 같은 자리에 선다
    //   (enemy.js 의 시체 twin 이 쓰는 것과 같은 성질이다).
    for (const s of silMeshes) {
      s.mesh.visible = s.src.visible && (imp || hiding ? true : (occOn && s.big));
    }
    silOn = hiding || occOn;
  }

  // -------------------------------------------------------------------------
  // 바깥에서 부르는 문
  return {
    // ── 계측 창구 (v96) ──
    // ★"이펙트가 화면의 몇 %인가"는 **이펙트를 껐다 켠 두 장의 차이**로만 정확히 잰다.
    //   색으로 마스크를 추리면 배경의 하늘·물까지 걸려서 숫자가 거짓말을 한다.
    //   그림에는 아무 영향이 없다(배열 하나를 내줄 뿐이다).
    fxMeshes: [slashMesh, lineMesh, impMesh, impfMesh, popMesh, foamMesh, ringMesh, burstMesh,
               levelRoot],
    step, updateShake, shakeOffset, updateOverlay, slash, speedLines, shake,
    // 화면 중앙 팝업 없이 캐릭터에 붙는 0.96초 성장 빛. target은 Object3D/Vector3 모두 가능.
    levelUp,
    // ★v99 16-FX main.js 한 줄 통로.
    // a,b = 칼날 선분, wake = 0..1, rootPos/charH = B 리본과 같은 바깥축을 만드는 기준.
    // 벡터는 main.js가 재사용하므로 함수 안에서 즉시 복사한다. 호출이 없어도 빈 층이다.
    trailFoamSample,
    // ★v94. 화면공간 본 획. main.js 궤적 구역이 **스윙이 터지는 프레임마다** 부른다
    //   (처치 여부와 무관). 이게 "화면에 그은 획" 문법의 주인공이다.
    swing,
    // ★v94. 명중 접점의 1~2프레임 팝(흰 번쩍 + 먹 튀김). 안 죽은 한 대에도 부른다.
    pop,
    // ★v94. 지금 든 칼의 색 계단을 본 획에 물린다(kind='el'). 안 부르면 감청 그대로.
    //   네 값은 **밝기 순서**여야 한다: ink(먹) < edge < mid < core(흰 심).
    setSwingPalette(o) {
      if (!o) return PAL_EL;
      if (o.ink !== undefined) PAL_EL.ink = o.ink;
      if (o.edge !== undefined) PAL_EL.edge = o.edge;
      if (o.mid !== undefined) PAL_EL.mid = o.mid;
      if (o.core !== undefined) PAL_EL.core = o.core;
      if (o.thr) PAL_EL.thr = o.thr;
      return PAL_EL;
    },
    // ★v99. 먹 튀김(f1) 방울 다수가 쓰는 **원소색**. main.js 가 칼을 바꿀 때마다
    //   지금 든 칼의 팔레트에서 감청 자리를 넘긴다. 안 부르면 물빛 기본값 그대로다
    //   (그러면 불칼에서도 파란 방울이 튄다 - 그래서 부르는 쪽이 있어야 한다).
    // ★인자는 **선형 rgb 0..1** 이다. main.js 의 uPal 이 hex/255 를 선형으로 그냥
    //   쓰므로 같은 자로 넘겨야 화면에서 궤적의 감청 밴드와 같은 색에 앉는다.
    //   (setHex 로 받으면 sRGB->선형 변환이 한 번 더 걸려 훨씬 어두워진다.)
    setPopTint(r, g, b) { popMat.uniforms.uWat.value.setRGB(r, g, b); },
    // ★18차 일섬. 접점 파열 한 겹(위 burst 절). main.js onHit 이 초승달+팝 자리에
    //   이것 하나를 부른다(FX_V18=1 일 때만. 0 이면 옛 두 줄이 그대로 돈다).
    burst,
    // ★18차. 파열의 색 계단을 **지금 든 칼**의 팔레트에 물린다. 인자는 전부
    //   **선형 rgb 0..1**(main.js uPal 과 같은 자)이고 밝기 순서로 넘긴다:
    //     wht(흰 심) > lt1(시안) > mid(중간) > dk1(감청)
    //   코어는 wht 를 1.85배로 든다 - 블룸 문턱(선형 1.02)을 넘겨야 그 한 점이 번진다.
    //   안 부르면 물빛 기본값 그대로다(불칼에서도 시안 파열이 터진다 = 부르는 쪽이 있어야 한다).
    // ★채도 밀기는 궤적 셰이더(main.js fsat)와 **같은 자(2.10)**를 쓴다. 두 층이
    //   같은 색에 앉아야 "한 이펙트"로 읽힌다(흰 심은 안 민다 - 밀 색이 없다).
    setBurstPalette(wht, lt1, mid, dk1) {
      const S = 2.10;
      const put = (u, c, k) => {
        const l = c.x * 0.2126 + c.y * 0.7152 + c.z * 0.0722;
        u.set(Math.max(0, (l + (c.x - l) * S) * k),
              Math.max(0, (l + (c.y - l) * S) * k),
              Math.max(0, (l + (c.z - l) * S) * k));
      };
      const U = burstMat.uniforms;
      if (wht) U.uCore.value.set(wht.x * 1.85, wht.y * 1.85, wht.z * 1.85);
      if (lt1) put(U.uHot.value, lt1, 1.25);
      if (mid) put(U.uMid.value, mid, 0.95);
      if (dk1) put(U.uDeep.value, dk1, 0.85);
    },
    // 맞은 그 자리에 참격 한 장(월드 플립북). main.js 의 옛 spawnImpact(가산합성
    // 초승달 + 별빛)를 그대로 대신한다. 부르는 쪽은 **좌표·각도·크기·종류**만 넘긴다.
    //   x,y,z = 월드 좌표(요괴 가슴께) / ang = 화면 각도(라디안) / size = 크기(m)
    //   kind  = 'kill' 진홍 / 'water' 감청. 붉은색은 처치 전용이다(오너 지시).
    impactSlash,
    // 비치명 명중. ★v91: 각도·자리를 받으면 **작은 획**을 한 장 긋는다.
    //   귀멸에서는 안 죽는 한 대에도 작화 한 획이 그어진다. 다만 임팩트 프레임과
    //   찢김선은 안 붙인다 - 그건 처치의 몫이라 여기서 쓰면 값이 없어진다.
    //   (보스 타격 경로는 각도를 안 넘겨서 예전 그대로 멈춤+흔들림만 간다)
    hit(swing, ang, offX, offY, kind) {
      addStop(STOP_HIT, swing);
      shake(0.045, 0.10);
      if (ang !== undefined && ang !== null) stroke(ang, offX, offY, false, kind, true);
    },
    // 처치. ★임팩트 프레임 한 장이 여기서 예약된다(main.js 는 이걸 부른 직후에
    //   slash() 를 불러 획 정보를 넘긴다. 둘 다 같은 프레임이라 순서는 상관없다).
    // ★v94. 백색 패널은 병합 창(0.80초) 안에서 한 번만 뜬다. 창 안의 추가 처치는
    //   초승달·먹 튀김·히트스톱만 간다(위 panelWanted 주석).
    kill(swing) {
      addStop(STOP_KILL, swing); shake(0.085, 0.16);
      if (panelWanted()) impact(IMP_N_KILL); else panelMerged++;
    },
    // 무리 마지막 한 마리. 여기가 "무리 전멸"의 방점이다.
    // x,z 를 주면 그 자리에, 안 주면 마지막 붓자국을 되짚어 링을 편다.
    wipe(x, y, z) {
      slowT = SLOW_T;
      bloomT = BLOOM_PULSE_T;
      shake(0.11, 0.22);
      // 전멸은 찢김선이 길고, 임팩트 프레임도 두 장이다
      speedLines(SPD_N_LONG, lastStroke.ang, lastStroke.x, lastStroke.y, true);
      impact(IMP_N_WIPE);
      wipeN++;
      if (x !== undefined && z !== undefined) ringAt(x, z);
      else ringFromLastSlash();
    },
    hurt() { addStop(STOP_HURT); shake(0.16, 0.26); },
    // ── 플레이어 사망 (v84 QA S2) ──
    // enemy.js 가 hp 0 이 된 그 프레임에 부른다(window.__feel 을 통해).
    // 여기가 하는 일은 **시간을 늘어뜨리는 것 하나**다. 먹판·「落」·소리는 각자
    // 자기 파일(ui.js·sfx.js)에서 같은 순간에 같이 걸린다.
    death() {
      deathT = DEATH_SLOW_T;
      stopT = 0;                  // 히트스톱이 걸려 있으면 슬로모가 뒤로 밀린다
      slowT = 0;
      shake(0.20, 0.45);          // 피격(0.16)보다 세게. "이번엔 다르다"
    },
    setBloomBase(v) { bloomBase = v; },
    // 실루엣 튜닝 손잡이(브라우저에서 바로 돌려 보고 값을 고르는 용도).
    // stealth.js 의 debug.tune 과 같은 성격이다 - 게임 로직에는 아무 영향이 없다.
    // which: 'sil'(은신, 기본) / 'occ'(상시 가려짐)
    silTune(o, which) {
      o = o || {};
      const m = which === 'occ' ? occMat : silMat;
      if (o.col !== undefined) m.uniforms.uCol.value.setHex(o.col);
      if (o.rim !== undefined) m.uniforms.uRim.value.setHex(o.rim);
      if (o.a !== undefined) m.uniforms.uA.value = o.a;
      if (o.rimMix !== undefined) m.uniforms.uRimMix.value = o.rimMix;
      if (o.rimP !== undefined) m.uniforms.uRimP.value = o.rimP;
      if (o.bias !== undefined) m.uniforms.uBias.value = o.bias;
      return { col: '#' + m.uniforms.uCol.value.getHexString(),
               rim: '#' + m.uniforms.uRim.value.getHexString(),
               a: m.uniforms.uA.value, rimMix: m.uniforms.uRimMix.value,
               rimP: m.uniforms.uRimP.value, bias: m.uniforms.uBias.value };
    },
    // 상시 실루엣만 껐다 켜는 스위치(A/B 검증용. 은신 실루엣은 그대로 돈다).
    setOcclusionSilhouette(on) { occOn = !!on; return occOn; },
    // 껍데기 상한 A/B 검증용. "61벌을 6벌로 줄여도 실루엣이 같은가"를 눈으로 재려면
    // 같은 화면에서 상한만 바꿔 두 장을 떠야 한다. 게임 로직에는 안 닿는다.
    setSilMax(n) {
      SIL_MAX_MESHES = Math.max(1, n | 0);
      silSig = '';                 // 다음 점검에서 껍데기를 다시 뜬다
      silCheckAt = -9999;
      return SIL_MAX_MESHES;
    },
    // ★setBrushTexture 는 v92 에서 지웠다. v91 때는 main.js 가 옛 붓자국 한 장
    //   (tex/brush_slash.png)을 계속 넘겨 주는데 main.js 를 못 고쳐서 빈 창구만
    //   남겨 뒀던 것인데, 이제 main.js 가 그 줄을 안 부른다(부르는 곳 0).
    // 연출 손잡이(브라우저에서 바로 돌려 보는 용도). 게임 로직에는 안 닿는다.
    fxTune(o) {
      o = o || {};
      if (o.paper !== undefined) impMat.uniforms.uPaper.value.setHex(o.paper);
      if (o.ink !== undefined) impMat.uniforms.uInk.value.setHex(o.ink);
      if (o.line !== undefined) lineMat.uniforms.uCol.value.setHex(o.line);
      // 지금 그 자리에서 컷을 한 장 껴 본다. ★IMPACT_CUT 이 0 이면 아무 일도 안 난다
      //   (스위치가 이겨야 한다. 디버그 창구로 오너가 끈 연출이 되살아나면 안 된다).
      if (o.imp !== undefined) impact(o.imp);
      return { paper: '#' + impMat.uniforms.uPaper.value.getHexString(),
               ink: '#' + impMat.uniforms.uInk.value.getHexString(),
               line: '#' + lineMat.uniforms.uCol.value.getHexString() };
    },
    // 검증 창구
    get state() {
      return { stop: +stopT.toFixed(4), slow: +slowT.toFixed(4),
               death: +deathT.toFixed(4),
               // 프레임 단위 검증 창구(임팩트 프레임 길이·프레임 스냅 확인용)
               //   frame = 렌더 프레임 번호 / impOn = 이번 프레임에 임팩트 컷이 떠 있나
               //   impN  = 지금까지 예약된 임팩트 컷 수 / frm = 슬롯별 지금 시트 칸
               fx: { frame: fxFrame, impN: impN, impOn: impOn, impLeft: impLeft,
                     wipeN: wipeN,
                     // v94 검증 창구
                     //   panelMerged = 병합 창(0.80초) 때문에 안 띄운 백색 패널 수
                     //   pops        = 지금 떠 있는 타격 팝의 장 번호(0=흰 번쩍 1=먹 튀김)
                     //   slotN       = 슬롯별 재생 장 수(지속 계약. 본 획 4장)
                     //   sheet2      = 굵은 획 시트를 읽었나(못 읽으면 옛 시트 폴백)
                     panelMerged: panelMerged,
                     pops: pops.map(s => Math.floor(s.t / FRAME_T)),
                     slotN: slashes.map(s => s.n),
                     sheet2: /flip2/.test(sheetName),
                     sheetName: sheetName,
                     // 타격 지점 참격(월드 플립북): 지금 몇 장이 떠 있고 각각 몇 번째 칸인가
                     impf: impfs.map(s => Math.floor(s.t / FRAME_T)),
                     impfSheet: !!impfMat.uniforms.uTex.value,
                     // ★18차 접점 파열. FX_V18 게이트가 실제로 물렸는지 이 두 숫자로 본다
                     //   (V18=1 이면 spawned 가 오르고 foam.spawned 는 0 에 머문다. 0 이면 반대).
                     burst: { v18: FX_V18, n: bursts.length, spawned: burstSpawnN,
                              ages: bursts.map(s => Math.floor(s.t / FRAME_T)) },
                     // 포말 마루: 새 메시도 fxMeshes 계측에 들어가며 수명/24fps 홀드를 여기서 본다.
                     foam: { enabled: !!FOAM_CREST_V2, tex: !!foamSheetLoaded,
                             n: foams.length, frame: foamQFrame, hold: foamHold,
                             wake: +foamLastWake.toFixed(3), spawned: foamSpawnN,
                             dropped: foamDropped,
                             anchored: !!foamPending.anchored,
                             spacing: FOAM_SPACING, seam: FOAM_SEAM_V,
                             ages: foams.map(s => foamQFrame - s.birth),
                             lives: foams.map(s => s.life),
                             cells: foams.map(s => s.variant) },
                     frm: slashMat.uniforms.uFrm.value.slice(),
                     col: slashMat.uniforms.uCol.value.slice(),
                     line: +lineMat.uniforms.uP.value.toFixed(3),
                     sheet: !!slashMat.uniforms.uTex.value },
               // 붓자국 상한(3.0m 자 기준으로 몇 배인가). S3 회귀를 숫자로 잡는다
               slashLen: { big: SL_LEN_BIG, small: SL_LEN, maxTotal: +(SL_LEN_BIG * 1.14 * 2).toFixed(3) },
               // 실루엣: mode 가 지금 어느 쪽인지, n 은 뜬 껍데기 수,
               //         draw 는 이번 프레임에 실제로 그리는 수(= 늘어난 드로우콜)
               //         seen 은 상한을 걸기 전 후보 수(61 -> 6 감축을 숫자로 남긴다)
               sil: { on: silOn, mode: silMode, n: silMeshes.length, seen: silSeen,
                      occ: occOn, occMax: OCC_MAX_MESHES, max: SIL_MAX_MESHES,
                      draw: silMeshes.reduce((n, s) => n + (s.mesh.visible ? 1 : 0), 0),
                      tri: silMeshes.map(s => s.tri) },
               budget: +budget.toFixed(4), shake: +shakeT.toFixed(3),
               brush: slashMat.uniforms.uUseTex.value ? 'flip' : 'proc',
               ring: { tex: !!ringMat.map, on: ringMesh.visible, n: ringN,
                       t: +ringT.toFixed(3), op: +ringMat.opacity.toFixed(3),
                       at: [+ringMesh.position.x.toFixed(2), +ringMesh.position.y.toFixed(3),
                            +ringMesh.position.z.toFixed(2)] },
               // visible은 부팅 3프레임 셰이더 예열 때도 true가 된다.
               // 실제 레벨업 상태는 불투명도가 아니라 수명 시계로 판정해야
               // 부팅/이펙트 A-B 캡처가 가짜 레벨업으로 계측되지 않는다.
               levelUp: { on: levelAge < LEVEL_UP_T, draw: levelRoot.visible, n: levelCount,
                          t: +Math.min(levelAge, LEVEL_UP_T).toFixed(3),
                          duration: LEVEL_UP_T, height: +levelHeight.toFixed(2),
                          at: [+levelRoot.position.x.toFixed(2), +levelRoot.position.y.toFixed(3),
                               +levelRoot.position.z.toFixed(2)] },
               // 각 슬롯이 지금 무슨 색인가(감청 분기가 먹었는지 눈 없이 확인)
               tint: slashMat.uniforms.uEdge.value.map(c => '#' + c.getHexString()),
               kind: detectKind() ? 'water' : 'kill' };
    },
    get frozen() { return stopT > 0; },
  };
}
