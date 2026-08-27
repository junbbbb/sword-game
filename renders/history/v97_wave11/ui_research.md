# 나 혼자만 레벨업 시스템창 시각 문법 조사

조사일: 2026-08-11 / 목적: 게임 UI를 이 문법으로 갈아입히기 위한 CSS 이식용 레퍼런스

## 저작권 주의

이 문서는 **스타일 문법(색·레이아웃·발광 패턴·정렬 규칙)만** 참고 대상으로 삼는다.
로고, 「NOTIFICATION」·「QUEST INFO」 같은 원문 문구, 원작 전용 서체, 모서리 필리그리 아트워크 자체는 **복제하지 않는다.**
아래에 적힌 hex 값은 공개된 스크린샷·스캔본에서 픽셀을 샘플링해 얻은 **추정치**이며, 제작사 공식 디자인 스펙이 아니다. 게임에 옮길 때는 색·비율만 참고하고 형태와 문구는 자체 디자인으로 재해석한다.

---

## 0. 먼저 알아야 할 것: 정본이 하나가 아니다

**결론.** "나혼렙 시스템창"은 단일 디자인이 아니라 최소 3계열이 존재하며, 서로 문법이 꽤 다르다. 어느 쪽을 베낄지 먼저 정해야 한다.

| 계열 | 출처 | 판 | 테두리 | 헤더 |
|---|---|---|---|---|
| **A. 애니 (A-1 Pictures, 2024)** | TV 애니 본편 | 짙은 네이비틸 반투명, 거의 평면 | 얇은 헤어라인 + **별도 레이어의 굵은 네온 브래킷 프레임** | **좌측 정렬**, 박스 2개 나란히 |
| **B. 웹툰/만화 (D&C 미디어)** | 원작 만화 패널 | 짙은 남색 세로 그라디언트, 반투명 | 발광선 없음, **모서리 아르누보 필리그리** | **상단 중앙 밴드** |
| **C. 골드 변주** | 만화 후반부 상태창 | 짙은 차콜 | 금색 세선 | 좌측 상단 타이틀 |

**게임 UI 이식 관점 권장: A(애니) 계열.** 이유는 필리그리 아트워크 없이 순수 CSS로 100% 재현 가능하고, 저작권상 안전한 기하 도형만 쓰기 때문이다. 아래 항목별 조사에서는 A를 기본으로 하되 B·C를 함께 적는다.

**근거/출처**
- 애니 A계열: https://static.wikia.nocookie.net/solo-leveling/images/b/b4/Anime_Episode_10_notification_for_job_change_quest.png (10화 job-change 알림창, 1366x768)
- 애니 A계열: https://static.wikia.nocookie.net/solo-leveling/images/b/b3/Anime_Episode_3_Jinwoo_receives_a_quest_from_the_System.png (3화, 창을 뒤에서 본 컷)
- 애니 A계열: https://static.wikia.nocookie.net/solo-leveling/images/b/bd/Anime_Episode_12_Jinwoo_uses_shop_in_system.png (12화 SHOP 창)
- 웹툰 B계열: https://static.wikia.nocookie.net/solo-leveling/images/c/c7/DailyQuest1.jpg (QUEST INFO 일일퀘스트)
- 웹툰 B계열: https://static.wikia.nocookie.net/solo-leveling/images/c/cc/PenaltyQuest1.jpg (반투명 상태의 같은 창)
- 골드 C계열: https://static.wikia.nocookie.net/solo-leveling/images/a/ad/Status_Page_2.png
- 골드 C계열: https://static.wikia.nocookie.net/solo-leveling/images/9/95/System1.jpg (여러 창이 공중에 떠 있는 일러스트)
- 위키 서술: "게임 같은 인터페이스로, 언제 어디서나 나타나는 **푸른 홀로그램 화면**" (Solo Leveling Wiki, System 항목) https://solo-leveling.fandom.com/wiki/System

---

## 1. 판(패널) 색

**결론 (A. 애니).**
- 배경은 **청록기 도는 짙은 남색**이다. 청록(teal)이 살짝 섞인 네이비이며, 순수한 남색보다 약간 초록 쪽으로 기울어 있다.
- 실측 median: 상단 `#102D3F`, 중앙 `#122D3D`, 하단 `#0F2534`, 우측 `#0F2837`.
- 대표값으로 **`#102B3C`** 하나로 잡아도 무방하다.
- **그라디언트는 거의 없다.** 위아래 차이가 L 기준 3 정도로 미미해서 사실상 평면 채움으로 봐도 된다. 대신 판 안쪽에 **아주 옅은 대각선 회로/스크래치 텍스처**와 작은 시안색 입자(파티클)가 흩뿌려져 있다. 이게 "평면 단색"으로 안 보이게 만드는 핵심이다.
- **불투명도는 대략 0.85~0.92.** 판 바깥 배경이 `#1B3146`인데 판 안이 `#102D3F`로 배경보다 더 어둡다. 즉 완전 투명 유리가 아니라 **어둡게 깔아주는 반투명 필름**에 가깝다. 뒤가 흐릿하게 비치는 정도.

**결론 (B. 웹툰).**
- **세로 그라디언트가 뚜렷하다.** 위가 어둡고 아래로 갈수록 밝고 푸르러진다.
- 실측(패널 내부 x 25~75% 구간 median): y16% `#1B2B39` → y25% `#1A2531` → y45% `#1D3149` → y55% `#223C58` → y65% `#223F5E` → y85% `#254665` → y92% `#233E59`
- 즉 **`#1A2531` (상단) → `#254665` (하단)** 의 linear-gradient. 여기에 가장자리 비네팅이 얹혀 좌우 끝이 다시 어두워진다(좌 `#192B3E`, 우 `#18293D`).
- 반투명이 확실하다. PenaltyQuest1.jpg에서는 같은 창이 거의 투명해져 뒤 인물이 그대로 보인다. 즉 **장면에 따라 불투명도가 변하는 연출**이다.

**결론 (C. 골드).** 판 `#292824`, 최암부 `#030303`, 잉크 `#F6C41F`. 짙은 차콜 + 금색.

**근거/출처**
- 위 이미지들을 PIL/numpy로 영역별 median 샘플링(자체 측정)
- 팬 재현 CSS의 수렴값도 같은 방향: `--sl-window-bg: rgba(13, 20, 43, 0.9)`, `--sl-dark-blue: #0d142b` https://github.com/No0bToPro/SoloLevelingSystem (styles.css)
- `--panel-bg-color: rgba(15, 25, 45, 0.92)` https://github.com/HorusRento/soul-leveling (css/themes.css)
- `linear-gradient(135deg, #1a2239 0%, #24243e 100%)` https://github.com/digishivam/sololevelingsystemui (index.html)

---

## 2. 테두리

**결론 (A. 애니). 2층 구조다. 이게 이 디자인의 정체성이다.**

**2-1. 안쪽 콘텐츠 판의 테두리**
- **1px 창백한 청백색 헤어라인.** 밝은 지점 실측 `#8FD3F1`, 평상시엔 더 어둡게 깔림(`#1D3A51`).
- **단선이다.** 이중선 아님.
- **모서리는 각진 직각(border-radius: 0).** 노치도 잘린 모서리도 없다. 그냥 사각형.
- 발광이 매우 약하다. 이 선은 "경계 표시"일 뿐 주인공이 아니다.

**2-2. 바깥 네온 브래킷 프레임 (별도 레이어)**
- 판에서 **떨어져 있는** 굵은 전기청색 프레임. 상단 바 + 하단 바 + 좌우 세로 레일로 구성.
- **3~4겹 평행선**으로 그려진다. 굵은 바 1개가 아니라 두께가 다른 선이 겹쳐 있다.
- **코너는 45도로 꺾여 내려가는 계단형/모따기(chamfer)**다. 둥글지 않고, 직각도 아니고, 대각선으로 꺾인다. 전형적인 SF HUD 브래킷.
- 색: 중간톤 `#36B4F2`, 밝은 코어 `#BEF4FE`, 중간 밝기대 `#41D3FB`. 상단 바 median `#189CF0`, 하단 바 median `#1463A0`(하단이 더 어둡다).
- 좌우 세로 레일은 어두운 파랑(`#1F477C`, `#1E4E9A`)의 **그리블(greeble) 구조물**로, 회로/메카 패널처럼 계단형 요철이 잔뜩 들어간다.

**결론 (B. 웹툰). 발광 테두리가 아예 없다.**
- 좌우 에지 실측이 `#192B3E`, `#18293D`로 판 내부보다 오히려 어둡다. **네온 아웃라인이 없다.**
- 대신 **네 모서리에 아르누보/켈트 매듭 스타일 필리그리 장식**이 들어간다. 밝은 시안(`#4BADC5`, `#50B1D0`, `#4DB0CB`, `#4AB1C9`)의 가는 곡선 매듭이 두 변을 따라 뻗는다.
- 상단 중앙에는 **왕관형 아라베스크 장식**이 헤더 밴드 위에 걸쳐진다.
- 즉 B계열의 "테두리감"은 선이 아니라 **모서리 장식 + 비네팅 + 바깥 드롭섀도**로 만들어진다.

**근거/출처**
- 자체 측정 및 크롭 확대 관찰(Anime_Episode_10 코너 3배 확대, DailyQuest1 코너 3배 확대)
- 팬 재현 CSS: `border: 1px solid var(--sl-border)` where `--sl-border: rgba(0, 168, 255, 0.3)`, `border-radius: 0.25rem` https://github.com/No0bToPro/SoloLevelingSystem
- `--panel-border-color: rgba(173, 216, 230, 0.7)` https://github.com/HorusRento/soul-leveling

---

## 3. 글로우

**결론.**
- **바깥 글로우: 있다. 단, 판이 아니라 네온 프레임에 집중된다.** 애니에서 블룸이 강하게 걸린 곳은 바깥 브래킷 프레임과 텍스트뿐이고, 콘텐츠 판 자체는 거의 발광하지 않는다.
- **안쪽 글로우(inset): 사실상 없다.** 판 내부는 균일하게 어둡다. inset box-shadow로 테두리 안쪽을 밝히는 처리는 원작에 없다.
- **텍스트 글로우: 강하다.** 이게 가장 중요하다. 글자 획이 가늘기 때문에 부드러운 흰-청 헤일로가 붙어야 "발광 홀로그램" 느낌이 난다. 헤더 「NOTIFICATION」의 각 글자에 뚜렷한 halo가 보인다.
- 글로우 색은 판 색과 다르다. 판은 청록기 네이비인데 글로우는 **더 밝고 채도 높은 시안** `#41D3FB` ~ `#BEF4FE` 쪽이다.
- 강도 감각: 텍스트 글로우 반경은 글자 높이의 30~50% 정도로 꽤 넓게 퍼진다. 프레임 블룸은 선 두께의 3~5배.

**근거/출처**
- 자체 측정: 밝은 냉색 라인 픽셀(luma>120, B-R>40) 중 상위 3000개 median = `#BEF4FE`, 전체 median = `#36B4F2`
- 3화 컷에서 밝은 냉색 라인 상위 2000개 median = `#D3EAFF`
- 팬 재현 CSS 수렴값: `--sl-glow: rgba(0, 168, 255, 0.5)`, `box-shadow: 0 0 0.75rem var(--sl-glow)`, `0 0 15px 5px`, `0 0 20px 5px` https://github.com/No0bToPro/SoloLevelingSystem
- `--glow-blur-low: 5px / medium: 10px / high: 15px`, `--primary-glow-color: #00ccff` https://github.com/HorusRento/soul-leveling

---

## 4. 헤더

**결론 (A. 애니). 상단 중앙이 아니라 좌측 정렬이며, 밑줄형 밴드가 아니라 "박스 2개"다.**

구조가 이렇다.

```
[ (!) ] [        NOTIFICATION        ]
 정사각      가로로 긴 직사각
```

- **아이콘 박스**: 정사각형, 1px 헤어라인 테두리, 채움 없음(판 배경 그대로 비침). 안에 **원 안의 느낌표**가 들어간다. 원도 느낌표도 가는 획이고 강하게 발광한다.
- **타이틀 박스**: 가로로 긴 직사각형, 같은 1px 헤어라인, 채움 없음. 안에 「NOTIFICATION」이 **박스 기준 가운데 정렬**.
- 두 박스 사이에 작은 간격(박스 높이의 15% 정도).
- **헤더 배경 따로 없음.** 박스 테두리가 곧 구분 장치다.
- **구분선 없음.** 헤더 아래로 가로 라인이 그어지지 않는다.
- **좌우 장식선 없음.**
- 헤더 블록 전체가 판 상단에서 안쪽으로 여백을 두고 **왼쪽에 붙는다.**

**결론 (B. 웹툰). 이쪽이 "상단 중앙 헤더 + 밴드" 문법이다.**
- 판 전체 폭을 가로지르는 **가로 밴드**가 있고, 밴드 위아래에 **가는 시안 헤어라인** 2줄이 그어진다.
- 밴드 배경은 판보다 약간 밝고, **중앙이 더 밝은 좌우 대칭 그라디언트**(양 끝이 어둡게 페이드).
- 밴드 안에 `(!) 아이콘 + 「QUEST INFO」`가 **한 덩어리로 중앙 정렬**된다. 아이콘이 왼쪽, 텍스트가 오른쪽.
- 밴드 위쪽 여백에 **왕관형 아라베스크 장식**이 중앙에 얹힌다.
- **우상단에 창 컨트롤**이 있다. 가로줄 하나(최소화)와 `×`(닫기) 두 글리프를 나란히 놓아 실제 OS 창을 흉내 낸다. 이건 놓치기 쉬운데 원작 분위기에 크게 기여한다.

**근거/출처**
- 애니 헤더 확대 크롭 관찰: https://static.wikia.nocookie.net/solo-leveling/images/b/b4/Anime_Episode_10_notification_for_job_change_quest.png
- 아이콘 원본(투명 PNG, 흰색 원+느낌표): https://static.wikia.nocookie.net/solo-leveling/images/d/d6/Alert.png
- 웹툰 헤더 확대 크롭 관찰: https://static.wikia.nocookie.net/solo-leveling/images/c/c7/DailyQuest1.jpg
- 팬 재현도 상단 라인 문법을 씀: `.sl-window::before { height: 2px; background: linear-gradient(90deg, transparent, var(--sl-blue), transparent); }` https://github.com/No0bToPro/SoloLevelingSystem

---

## 5. 타이포

**결론.**
- **계열: 지오메트릭 산세리프.** Futura / Century Gothic 계통이다. O가 정원에 가깝고, 획 굵기가 균일하며, 끝단 장식이 없다. 고딕(그로테스크)이나 휴머니스트가 아니다.
- **굵기: Regular ~ Medium. 볼드가 아니다.** 이게 자주 틀리는 지점이다. 헤더 「NOTIFICATION」도 가는 획이고, 굵어 보이는 건 글로우 때문이다.
- **자간: 넓다.** 헤더는 대략 `0.12em ~ 0.18em`. 본문은 그보다 좁지만 여전히 기본보다 넓다.
- **대소문자: 헤더는 전부 대문자.** 본문은 대소문자 혼용 문장형("A job-change quest can now be ordered.")이며, **강조어만 볼드 이탤릭**으로 처리한다.
- **정렬: 중앙 정렬 위주.** 헤더는 박스 안 중앙, 본문은 판 기준 중앙. 다만 헤더 블록 자체는 판 왼쪽에 붙는다(항목 4 참조).
- **색: 흰색에 아주 살짝 청색을 섞은 값.** 실측 `#E6F3F7`. 순백 `#FFFFFF`보다 미세하게 차갑다. 웹툰 계열은 순백 `#FFFFFF`.
- 웹툰 계열은 **컨덴스드(폭이 좁은) 산세리프 대문자**로, 애니보다 굵고 좁다. 같은 작품이지만 서체 인상이 다르다.

**근거/출처**
- 자체 측정: 흰 글자 픽셀(luma>200, |B-R|<25) median = `#E6F3F7`
- 헤더 확대 크롭 육안 확인(글자 형태, 자간, 획 굵기)
- 팬 재현물은 Rajdhani(스퀘어드 컨덴스드) 또는 Orbitron을 쓴다. Rajdhani는 "각지고 좁으며 기술적/미래적으로 읽히는" 화면용 서체로 소개된다. https://fonts.google.com/specimen/Rajdhani , https://github.com/No0bToPro/SoloLevelingSystem (`--font-primary: 'Rajdhani', sans-serif`), https://github.com/HorusRento/soul-leveling (`--font-primary: 'Orbitron', ...`)
- 다만 팬 서체 선택은 원작과 다르다. 원작 애니는 Rajdhani/Orbitron 같은 스퀘어드가 아니라 **둥근 지오메트릭** 계열이다. 이식할 때는 이 차이를 의식할 것.

---

## 6. 경고 변주

**결론.**
- **원작 애니에는 "빨간 경고창"이라는 별도 컴포넌트가 사실상 없다.** 헤더 문구는 「NOTIFICATION」 하나로 통일되고, 위험은 **본문 텍스트의 색**으로 표현된다. 즉 판 전체를 빨갛게 바꾸는 게 아니라 **글자만 빨갛게** 한다.
- 웹툰 실측: 「CAUTION!」 빨강 = `#C61418` (상위 50px median) / `#AF1E24` (상위 400px median). 반투명 상태에서는 `#C14344`.
- 대비되는 긍정/목표 색은 **초록**: 「GOALS」 = `#73DC75` / `#70CA78`, 반투명 상태 `#65C562`.
- **원작에서 "빨간 알림"은 서사적 사건이다.** 초기에는 파란색과 흰색 알림만 나오다가, 원작 31~35화 구간에서 **처음으로 붉은 알림이 등장**하고 시스템이 그 색의 의미를 설명하지 않는다. 즉 빨강은 UI 상태가 아니라 "이례적 사건" 신호로 쓰인다. 게임에 이식할 때 이 희소성을 지키면 임팩트가 크다.
- 위험 상황의 색 언어는 창이 아니라 **환경**이 담당한다. 레드 게이트 실측: 코어 레드 `#E20E27` ~ `#EB3540`, 밝은 부분 `#ED1F1C` ~ `#F0333E`, 함께 치는 마젠타/보라 아크 `#BF62A4` ~ `#F55BC8`. 붉은 위험에는 **마젠타 번개**가 항상 따라붙는다.
- 헤더 문구 패턴(웹툰): `[PENALTY QUEST: SURVIVAL]` 처럼 **대괄호로 감싼 분류 라벨**, 그리고 본문 앞머리에 `CAUTION!` 를 붙인 뒤 이어쓰기. 예: "CAUTION! - IF THE DAILY QUEST REMAINS INCOMPLETE, PENALTIES WILL BE GIVEN ACCORDINGLY."

**경고 변주를 만들 때의 권장 규칙**
1. 판 배경은 남색 그대로 두고 **테두리·글로우·강조 텍스트만** 붉게 바꾼다(원작 충실).
2. 판 전체를 붉게 바꾸는 건 팬 재현물 관행이지 원작 문법은 아니다. 다만 "레드 게이트" 같은 최상급 위험에서는 정당하다.
3. 글로우 강도는 파란 기본형보다 **더 세게** 준다. 붉은 계열은 같은 blur에서 눈에 덜 띈다.

**근거/출처**
- 자체 측정(DailyQuest1.jpg, PenaltyQuest1.jpg, RedGate1.jpg, Red_Gate_-_S2_Episode_13.png)
- "초기 챕터에서 시스템은 파란 알림과 흰 알림을 보냈고, 붉은 알림이 눈에 띄는 변화로 등장했다. 다만 시스템은 붉은색이 무엇을 뜻하는지 설명하지 않는다." (원작 31~35화 요약) https://www.youtube.com/watch?v=x6xz_6ZkM3A
- 팬 재현물의 red gate 테마 토큰: `--red-gate-primary: #ff1111`, `--red-gate-secondary: #cc0000`, `--red-gate-dark-bg: #1a0000`, `--red-gate-overlay-color: rgba(180, 0, 0, 0.3)`, `--panel-border-color: rgba(220, 0, 0, 0.8)` https://github.com/HorusRento/soul-leveling (css/themes.css)
- `--sl-red: #e74c3c` + `box-shadow: 0 0 0.75rem rgba(231, 76, 60, 0.5)` https://github.com/No0bToPro/SoloLevelingSystem
- 페널티 존 설정: https://solo-leveling.fandom.com/wiki/Penalty_Zone

---

## 7. 부가 요소

**결론. 이 UI의 지배 규칙은 "모든 것이 1px 헤어라인 박스"다.** 12화 SHOP 창이 이걸 가장 잘 보여준다. 탭도, 아이콘도, 목록 행도, 통화 표시도 전부 채움 없는 얇은 사각 박스다. 둥근 모서리, 그림자, 채워진 버튼이 하나도 없다.

**7-1. 라벨-값 정렬**
- **라벨 왼쪽, 값 오른쪽**의 양끝 정렬(space-between)이 기본이다.
- 웹툰 QUEST INFO: `-PUSH-UPS` ... `[0/100]` 처럼 **값을 대괄호로 감싼다.** 이게 시각적 서명 역할을 한다.
- 웹툰 상태창: `NAME: SUNG JIN-WOO` / `LEVEL: 2` 처럼 **`라벨: 값` 콜론 표기**를 2열 그리드로 배치한다. 좌열 `NAME/JOB/TITLE/HP`, 우열 `LEVEL/FATIGUE`.
- 스탯 블록은 `STRENGTH: 20` `VITALITY: 11` `AGILITY: 11` `INTELLIGENCE: 11` `SENSE: 11` 식으로 2열, 각 값 옆에 **증감 스피너(위아래 삼각형)** 가 붙는다.
- SHOP 창: 아이템명이 왼쪽, 가격이 오른쪽이며 **가격 글자가 명확히 더 작다.**

**7-2. 구분선**
- 가는 수평선 1줄. 웹툰 상태창에서는 흰색 실선이고, **선 오른쪽 끝에 작은 다이아몬드 `◆` 마커**가 붙는다. 이 디테일이 밋밋한 선을 "시스템 UI"로 만든다.
- 애니에서는 구분선을 거의 안 쓰고, 대신 **박스로 그룹을 나눈다.**

**7-3. 게이지/스탯바**
- 웹툰 상태창의 HP/MP 바는 **라벨 아래에 놓인 굵은 흰 수평선**이며, 채워진 길이로 잔량을 표시한다. `HP: 205` 밑에 긴 흰 바, `MP: 22` 밑에 아주 짧은 바. 배경 트랙은 거의 보이지 않는다.
- 즉 **둥근 캡슐형 프로그레스바가 아니라 각진 막대**다. border-radius 0.
- 팬 재현물은 여기에 그라디언트를 얹는다: `linear-gradient(90deg, #4e9afe 0%, #76fffa 100%)`. 원작보다 화려하지만 게임 UI로는 이쪽이 읽기 좋다.

**7-4. 버튼 ([예][아니오])**
- **채움 없는 얇은 테두리 박스 + 대문자 텍스트.** SHOP 창의 `BUY` / `SELL` 탭이 정확히 이 형태다.
- 선택된 탭은 **테두리와 글자가 더 밝아지는** 방식으로 표시된다. 배경을 채우지 않는다.
- 두 버튼은 나란히, 같은 폭으로 놓인다.
- 원작 퀘스트 수락 프롬프트는 `Yes` / `NO` 2지 선택으로 알려져 있다.

**근거/출처**
- SHOP 창: https://static.wikia.nocookie.net/solo-leveling/images/b/bd/Anime_Episode_12_Jinwoo_uses_shop_in_system.png
- 웹툰 상태창(라벨:값, 구분선+◆, HP/MP 바, 스피너): https://static.wikia.nocookie.net/solo-leveling/images/b/bd/System_status.png
- 웹툰 QUEST INFO(대괄호 값 표기): https://static.wikia.nocookie.net/solo-leveling/images/c/c7/DailyQuest1.jpg
- 게이지 그라디언트 팬 구현: https://github.com/digishivam/sololevelingsystemui
- 팬 구현들의 공통 구성 요소(XP 프로그레스바, STR/AGI/STA/INT 스탯 표시, 인벤토리 섹션): https://github.com/digishivam/sololevelingsystemui , https://github.com/keanteng/solo-leveling

---

## 8. 애니메이션

**결론. 원작 제작사의 공식 모션 스펙은 공개된 자료가 없다.** 검색으로 A-1 Pictures의 UI 모션 브레이크다운이나 아트 디렉션 인터뷰를 찾지 못했다. 아래는 (a) 본편에서 관찰 가능한 것과 (b) 팬 재현물이 수렴한 관행을 구분해 적는다.

**(a) 원작에서 확인되는 것**
- 판은 **공간에 떠 있고 원근이 걸린다.** 3화 컷은 창을 **뒤에서** 보여주며 글자가 좌우 반전돼 있다. 즉 창은 2D 오버레이가 아니라 3D 평면으로 취급된다. 웹툰 패널들도 사다리꼴로 기울어 그려진다.
- 판 안에서 **작은 시안 입자가 상시 떠다닌다.** 정지 프레임에서도 스파클이 보인다.
- **글리치 연출이 존재한다.** 시즌2 6화에서 시스템이 글리치를 일으키는 장면이 나오며, 이는 연출 장치이자 서사적 복선이다.
- 여러 창이 동시에 뜰 때는 **깊이가 다른 레이어로 흩어져 배치**된다(System1.jpg 일러스트: 창들이 서로 다른 거리·각도로 공중에 떠 있고 살짝 휘어 있다).

**(b) 팬 재현물이 수렴한 관행 (원작 근거 아님, 실용적 기본값으로는 유효)**
- 등장: `fadeIn 0.5s ease-out` + `slideUp 0.5s ease-out` 동시 실행
- 상시: 좌우로 흐르는 **스캔 하이라이트**. `background-size: 200% 100%` 의 `linear-gradient(90deg, transparent 0%, rgba(0,168,255,0.1) 50%, transparent 100%)` 를 `statusScan 2s linear infinite` 로 흘림
- 상단 2px 그라디언트 라인(`transparent → blue → transparent`)을 `::before` 로 상시 표시
- 강조 순간: `box-shadow: 0 0 0 0` → `0 0 0 10px rgba(0,168,255,0)` 로 퍼지는 **펄스 링**
- 속도 토큰: very-fast 0.2s / fast 0.4s / normal 0.8s / slow 1.5s
- 레벨업: 파티클 시스템 + 밝기 애니메이션, 성취 시 **파란 글로우 펄스**

**근거/출처**
- 3화 반전 컷(3D 평면 취급 증거): https://static.wikia.nocookie.net/solo-leveling/images/b/b3/Anime_Episode_3_Jinwoo_receives_a_quest_from_the_System.png
- 다중 창 부유 일러스트: https://static.wikia.nocookie.net/solo-leveling/images/9/95/System1.jpg
- 글리치 연출: https://comicbook.com/anime/news/solo-leveling-glitch-red-gate-jinwoo-secret/ , https://www.sportskeeda.com/anime/why-system-glitch-solo-leveling-season-2-episode-6-explored
- 팬 재현 애니메이션 CSS 전량: https://github.com/No0bToPro/SoloLevelingSystem (styles.css의 `.sl-window`, `.sl-window::before`, `.sl-window.sl-animate-active::after`, `@keyframes statusScan`)
- "상태창의 스캐닝 라인 효과와 발광 테두리, 레벨업의 파티클/밝기 애니메이션, 성취 시 파란 글로우 펄스" (같은 저장소 README)
- 팬 제작 System 사례(Python + Blender, 60~70시간): https://www.cbr.com/solo-leveling-anime-system-create/ , https://www.reddit.com/r/anime/comments/1ectakc/ive_made_the_system_from_solo_leveling/

---

## 9. 비슷한 문법을 쓰는 다른 작품

- **소드 아트 온라인 (SAO)**: **명암이 정반대다.** 원작 소설의 메뉴는 "빛나는 보라색 직사각 창"이고, 애니 메인 메뉴는 **흰 배경 레이아웃**에 좌측 요약도 / 중앙 원형 카테고리 버튼 / 우측 상세 다이얼로그 3분할이다. 즉 SAO는 밝은 판 + 어두운 글자 + **둥근 원형 버튼**이고, 나혼렙은 어두운 판 + 밝은 글자 + **각진 사각 박스**다. 참고: https://swordartonline.fandom.com/wiki/Sword_Art_Online
- **오버로드 (Overlord)**: **HUD가 지속적으로 존재하지 않는다는 점이 결정적 차이.** 유그드라실의 명령 콘솔은 게임 안에서만 쓰이는 기능적 인터페이스이고, 아인즈는 신세계로 넘어온 뒤 **콘솔을 소환할 수 없게 된다.** 그래서 나혼렙처럼 화면에 상시 떠 있는 시스템창 문법이 성립하지 않는다. 콘솔 자체의 색·형태에 대한 신뢰할 만한 시각 자료는 찾지 못했다(미검증). 참고: https://overlordmaruyama.fandom.com/wiki/YGGDRASIL
- **게임 속 바바리안으로 살아남기**: 네이버웹툰 연재, 원작 웹소설 각색 한태수, 작화 MIDNIGHT STUDIO, 2023-04-19 연재 시작. **시스템창/상태창의 시각 디자인에 대한 근거 자료를 찾지 못했다(미검증).** 이 항목은 실물 컷을 직접 확인하기 전에는 인용하지 말 것. 참고: https://namu.wiki/w/게임%20속%20바바리안으로%20살아남기(웹툰)
- **나혼렙 자체의 게임화 (Solo Leveling: ARISE)**: 3인칭 액션 RPG로 출시되어 있어 인게임 UI가 동일 문법의 실사용 사례가 된다. 다만 공식 UI 분석 문서는 찾지 못했다. 참고: https://www.pcgamingwiki.com/wiki/Solo_Leveling:_Arise

---

## CSS 토큰 제안

아래 값은 **애니(A계열)를 기준으로 한 추정치**다. 원작 스크린샷 픽셀 샘플링에서 도출했으며 공식 스펙이 아니다. 실제 게임 배경 위에 얹어보고 대비를 재조정할 것.

```css
:root {
  /* ---- 판 ---- */
  --sys-panel-bg:        rgba(16, 43, 60, 0.88);   /* #102B3C, 청록기 도는 짙은 남색 */
  --sys-panel-bg-solid:  #102B3C;
  --sys-panel-bg-top:    rgba(18, 45, 61, 0.90);   /* 그라디언트 쓸 때 상단 */
  --sys-panel-bg-bottom: rgba(15, 37, 52, 0.90);   /* 하단, 차이는 아주 미세하게 */
  --sys-panel-radius:    0px;                       /* 각진 모서리 고정 */

  /* ---- 테두리 (2층) ---- */
  --sys-edge:            #8FD3F1;                   /* 안쪽 판 1px 헤어라인 */
  --sys-edge-dim:        rgba(143, 211, 241, 0.42); /* 평상시 */
  --sys-edge-width:      1px;
  --sys-frame:           #36B4F2;                   /* 바깥 네온 브래킷 */
  --sys-frame-core:      #BEF4FE;                   /* 브래킷 밝은 코어 */
  --sys-frame-mid:       #41D3FB;
  --sys-frame-deep:      #1463A0;                   /* 하단 바처럼 어두운 쪽 */
  --sys-rail:            #1F477C;                   /* 좌우 그리블 레일 */

  /* ---- 글로우 ---- */
  --sys-glow:            rgba(65, 211, 251, 0.55);
  --sys-glow-soft:       rgba(54, 180, 242, 0.30);
  --sys-glow-frame:      0 0 6px var(--sys-glow), 0 0 18px var(--sys-glow-soft);
  --sys-glow-text:       0 0 4px rgba(190,244,254,0.85), 0 0 12px rgba(65,211,251,0.45);
  --sys-glow-panel-out:  0 0 28px rgba(54,180,242,0.22);  /* 판 바깥 은은한 글로우 */
  /* inset 글로우는 쓰지 않는다 (원작에 없음) */

  /* ---- 타이포 ---- */
  --sys-text:            #E6F3F7;                   /* 살짝 청기 도는 흰색 */
  --sys-text-dim:        rgba(230, 243, 247, 0.62);
  --sys-font:            "Century Gothic", "Futura", "Questrial", system-ui, sans-serif;
  --sys-title-spacing:   0.15em;                    /* 헤더 자간 */
  --sys-body-spacing:    0.04em;
  --sys-title-weight:    500;                       /* 볼드 아님 */

  /* ---- 상태 색 ---- */
  --sys-ok:              #73DC75;                   /* GOALS 초록 */
  --sys-gold:            #F6C41F;                   /* 골드 변주 잉크 */
  --sys-warn:            #C61418;                   /* CAUTION 빨강 */
  --sys-danger:          #E20E27;                   /* 레드 게이트 코어 */
  --sys-danger-hot:      #F0333E;
  --sys-danger-arc:      #F55BC8;                   /* 붉은 위험에 따라붙는 마젠타 */

  /* ---- 여백 ---- */
  --sys-pad:             24px;
  --sys-gap:             12px;
}

/* 경고 변주: 판은 그대로 두고 테두리·글로우·강조만 붉게 (원작 문법) */
.sys-panel--warn {
  --sys-edge:       #F0333E;
  --sys-edge-dim:   rgba(240, 51, 62, 0.50);
  --sys-frame:      #E20E27;
  --sys-frame-core: #FFC9CD;
  --sys-glow:       rgba(240, 51, 62, 0.65);   /* 파란 기본형보다 강하게 */
  --sys-glow-soft:  rgba(226, 14, 39, 0.38);
  --sys-text:       #FFE9EA;
}

/* 웹툰(B) 계열을 쓰고 싶을 때의 판 색 오버라이드 */
.sys-panel--manhwa {
  --sys-panel-bg-top:    #1A2531;
  --sys-panel-bg-bottom: #254665;
  --sys-edge:            #4CB0CC;   /* 모서리 장식용 시안 */
}
```

**적용 시 주의**

1. `--sys-panel-radius`는 0으로 고정한다. 둥근 모서리 하나로 이 문법이 무너진다.
2. 헤더는 배경을 채우지 말고 **테두리 박스**로 만든다. 채우는 순간 일반 다이얼로그처럼 보인다.
3. 글자를 굵게 하지 말고, 대신 `--sys-glow-text`를 세게 준다. 굵기가 아니라 발광으로 존재감을 만든다.
4. 판 내부에 아주 옅은 대각선 텍스처와 미세 입자를 넣는다. 순수 단색 채움이면 값싸 보인다.
5. 빨강은 아껴 쓴다. 원작에서 붉은 알림은 상태가 아니라 사건이다.
6. 원작 문구(NOTIFICATION, QUEST INFO 등)와 아르누보 필리그리 아트워크는 가져오지 않는다. 기하 도형과 색만 쓴다.

---

## 남은 불확실성

- 제작사 공식 컬러 스펙·모션 가이드는 공개 자료가 없다. 모든 hex는 압축된 스크린샷에서 역산한 값이라 실제 원본보다 채도가 낮게 나왔을 가능성이 있다. 특히 웹툰 스캔본은 JPEG 열화가 커서 시안 계열이 실제보다 어둡게 측정된다.
- 원작 서체는 특정하지 못했다. 지오메트릭 산세리프 계열이라는 것까지만 확인했다.
- 등장/퇴장 모션의 원작 타이밍은 정지 이미지로 검증 불가. 8-(b)는 팬 관행이지 원작 근거가 아니다.
- 오버로드 콘솔의 시각 디자인, 게임 속 바바리안의 상태창 디자인은 근거를 찾지 못해 미검증으로 남긴다.
