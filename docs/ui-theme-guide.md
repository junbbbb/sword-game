# UI 테마 가이드

UI는 기존 구조와 게임 로직을 유지한 채 색, 표면, 테두리, 장식, 타이포그래피만
덮어쓰는 독립 스킨이다. 현재 활성 시안은 참고 이미지의 먹색·청동 알림창과 따뜻한
판타지 게임 가독성을 섞은 **Bronze Story**다. 이전 **Abyss Hunter** 시안도 그대로
보관하므로 한 줄로 왕복할 수 있다.

## 활성화

`web/index.html`에서 테마 CSS를 불러오고 `body`의 값으로 활성 테마를 고른다.

```html
<link rel="stylesheet" href="./ui-theme-abyss.css">
<link rel="stylesheet" href="./ui-theme-bronze.css">
<link rel="stylesheet" href="./ui-theme-vine.css">
<body data-ui-theme="bronze-story" data-ui-frame="vine">
```

- 현재 시안: `data-ui-theme="bronze-story"` + 마감 겹 `data-ui-frame="vine"`
- 이전 시안: `data-ui-theme="abyss-hunter"`
- 끄기: `data-ui-theme` 속성을 제거한다.
- 다른 테마로 전환: 속성값만 새 테마 이름으로 바꾼다.

## Bronze Vine 마감 겹 (19차, 2026-08-18)

`ui-theme-vine.css`는 **독립 테마가 아니라 Bronze Story 위에 얹는 덧겹**이다.
독립 테마로 만들면 `body[data-ui-theme="..."]` 스코프가 갈려서 44KB를 통째로
복사해야 하므로, `data-ui-theme`는 그대로 두고 `data-ui-frame` 하나를 더 받는다.

```
되돌리기 = body 에서 data-ui-frame="vine" 한 토막을 지운다
          -> Bronze Story(+Paperlogy)가 화소까지 그대로 돌아온다(19차에 검증)
```

레퍼런스(웹툰 시스템창)를 화소로 재서 **어긋난 셋만** 갈아 끼웠다.

| 부분 | Bronze Story | Bronze Vine (레퍼런스 실측) |
|---|---|---|
| 판 바탕 | 세로 그라데이션 + 주사선, 따뜻함 | `#272727` **평면 무채색** |
| 테 | 굵기 같은 **겹줄** (방향 없음) | **홑겹 베벨**, 위 변 마루 `#E6B78E` · 옆 변 마루 `#AA764E` (**빛이 위에서**) |
| 모서리 | 각진 잎·방패, **네 귀 전부** | 둥근 봉 당초문, **좌상+우하 대각 한 쌍** |

- 색·두께·장식 크기는 `ui-theme-vine.css` 상단 `--vn-*` 토큰에서 먼저 고친다.
- 레일 마루는 바깥 끝이 아니라 **레일의 40~44% 지점**에 둔다. 바깥 끝에 두면
  판 둘레가 형광펜으로 그은 것처럼 뜬다.
- 장식은 가상요소가 아니라 **배경 겹**이다. `.win::before/::after`와
  `#bClear::before/::after`가 이미 다 차 있어서(그중 하나는 창 이름 **글자**를
  `content`로 들고 있다) 가상요소를 쓸 수 없다.
- 이 판들은 **진짜 `border`를 두르지 않는다**(ui.js 254~258줄 규칙). 레일은
  배경 겹으로 그린다.
- **서체는 이 겹이 건드리지 않는다.** 레퍼런스 글자는 픽셀 서체지만 오너가
  `86b5a2f`에서 Paperlogy로 정했다. 픽셀 서체가 지던 「시스템의 목소리」 역할은
  **낫표 「」**(`#uiTitle .lore`, `#uiDeath .cnt`)가 대신 진다.
- **상시 HUD(계기판·목표 배너·나침반·머리 위 바)에는 덩굴을 안 얹었다.**
  레퍼런스는 '시스템 창' 한 종류의 문법이고, 전투 중 상시로 떠 있는 띠에
  당초문을 두르면 눈이 장식에 붙는다. 확장은 오너 결정 사항이다.

### 당초문 에셋 다시 굽기

`web/tex/ui_vine_{tl,tr,bl,br}.webp`는 codex ImageGen 산출물을 두 단계로 가공한다.

```bash
# ① 초록 크로마키 -> 투명 (알파를 연속값으로 뽑고 디스필한다)
python3 tools/ui_chroma.py <초록배경.png> <keyed.png> --size 640

# ② 광도로 실측 팔레트를 강제 + 잉크 상자로 자르기 + 네 모서리 뒤집기
python3 tools/bake_ui_vine.py <keyed.png> web/tex --size 256 --dim 0.86
```

- 생성물은 **채도가 매번 튄다.** 색을 프롬프트로 맞추려 하지 말고 ②의 램프에 맡긴다.
- `--dim`은 장식을 레일보다 어둡게 눌러 같은 금속으로 읽히게 하는 값이다.
- ②는 **잉크 상자로 자른다.** 안 자르면 장식이 판 안쪽에 얌전히 앉아서
  레퍼런스처럼 레일에 걸터앉지 않는다.
- `codex exec`에 **`-i` 입력 이미지를 둘 이상 넣지 말 것.** 10분을 넘겨도
  파일이 안 나온다. codex 자체 크로마키 제거도 쓰지 말 것(알파가 봉 몸통을 파먹는다).

각 테마 규칙은 자기 `body[data-ui-theme="..."]` 아래로 제한한다. 테마 CSS는
`ui.js`의 동적 기본 스타일보다 먼저 로드되지만, `body[...]`를 더한 높은 선택자
우선순위로 외형을 유지한다. 상태 제어용 인라인 `width`, `transform`, `opacity`,
`display`는 테마가 덮지 않는다.

## Bronze Story 팔레트와 표면

색과 공통 표면은 `web/ui-theme-bronze.css` 상단의 `--bs-*` 토큰 블록에서 먼저
고친다. 개별 HUD 선택자에 같은 색을 반복해서 직접 쓰지 않는다.

| 의미 | Bronze Story 토큰 | 용도 |
|---|---|---|
| 서체 | `--bs-font-ui`, `--bs-font-display` | Paperlogy 수치, 제목, 알림 |
| 바탕 단계 | `--bs-night-*`, `--bs-charcoal*` | 먹색 배경과 판 깊이 |
| 판 표면 | `--bs-panel*`, `--bs-panel-fill*` | 카드, 도크, 보조판 |
| 글자 | `--bs-cream*`, `--bs-parchment`, `--bs-muted` | 주 정보, 설명, 비활성 정보 |
| 테두리/장식 | `--bs-bronze*`, `--bs-frame-image` | 이중선과 주요 카드 모서리 |
| 성장/보상 | `--bs-gold*` | 레벨, EXP, 목표, 획득물 |
| 생존/위험 | `--bs-green*`, `--bs-red*` | 플레이어 HP, 보스, 피격, 사망 |

`--ui-*`와 `--rb-*`는 위 토큰을 가리키는 호환 alias다. 기본 UI 구조는 유지하고
Bronze Story 토큰을 바꾸면 로딩 화면과 동적 HUD가 함께 따라오게 한다. 하단/머리 위
하단 체력처럼 JS와 공유해야 하는 완성 그라데이션은 `--ui-hp-*-fill`, 성장 바는
`--ui-exp-fill`, 데미지 숫자는 `--fx-damage-*`에서 바꾼다. 플레이어 머리 위
머리 위 바는 저체력 상태에 따라 색을 바꾸지 않는다.

`--fx-damage-*` 다섯 값은 Three.js 재질로도 전달되므로 `#RGB` 또는 `#RRGGBB`
형식으로 지정한다. `oklch()`나 `color-mix()` 같은 문법은 안전한 기본색에 폴백한다.

## 서체: Paperlogy

게임의 로딩 화면, HUD, 팝업, 보스/결과창, 은신 안내와 캔버스에 구운 피해 숫자까지
`Paperlogy`를 사용한다. 폰트는 외부 CDN에 의존하지 않도록
`web/ui-assets/fonts/`에 번들되어 있다.

- `4Regular` = 400, `5Medium` = 500, `6SemiBold` = 600
- `7Bold` = 700, `8ExtraBold` = 800, `9Black` = 900
- `web/ui-theme-bronze.css` 상단의 `@font-face`와 `--bs-font-*`가 정본이다.
- 로딩 직전 기본 글꼴은 `web/index.html`, 동적으로 주입되는 보조 HUD는
  `web/{ui,enemy,boss,level2,stealth,main}.js`의 `Paperlogy` 선언을 따른다.

무게를 바꾸려면 기존 `font-weight`만 조절한다. 폰트 파일명이나 `font-family` 이름을
바꾸면 캔버스 숫자/표식도 함께 수정해야 한다. 라이선스·출처는
`web/ui-assets/fonts/Paperlogy-NOTICE.md`에 기록한다.

색은 의미를 유지한다. 팔레트를 바꿔도 체력=생존, 적색=보스/피격,
금색=성장/보상, 청동색=선택/행동이라는 역할은 섞지 않는다. 투명도, 그라데이션,
프레임과 표면 질감은 같은 파일에서 조정하되 작은 변경은 먼저 토큰으로 해결한다.

## 머리 위 체력 바 빠른 조정

플레이어와 일반 몬스터는 서로 다른 렌더 경로를 쓴다. 플레이어 바는 `web/ui.js`의
`#uiHpFloat` DOM/CSS이고, 몬스터 바는 `web/enemy.js`의 `pipMat` 월드 셰이더다.

- 플레이어 높이: `#uiHpFloat`의 `height`와 같은 미디어 분기의 높이
- 플레이어 구분선 간격/색: `#uiHpFloat .fl`의 `repeating-linear-gradient`
- 플레이어 고정색: `#uiHpFloat .fl`의 초록 그라데이션
- 몬스터 폭/높이: `BAR_W`, `PIP_H`
- 몬스터 테두리: `BAR_BORDER`
- 몬스터 고정색: `pipBarFrag`의 `hpSeg`

현재 플레이어는 레벨 배지와 같은 16px(낮은 화면 14px)의 가는 초록 게이지에
듬성듬성한 1px 구분선만 얹은 형태이고,
몬스터는 기준 화면에서 약 5px인 붉은 단일 게이지다. 둘 다 체력 비율에 따라 색을
바꾸지 않는다. 몬스터 바 높이를 바꾸면 셰이더 종횡비가 `BAR_W / PIP_H`에서 자동으로
다시 계산되므로 다른 셰이더 수치를 함께 보정할 필요는 없다.

## 스킬 아이콘 교체

현재는 `web/ui-assets/bronze-skills.webp`, 이전 시안은
`web/ui-assets/abyss-skills.webp` 한 장을 각각 2×2로 잘라 네 슬롯에 쓴다. 같은
크기와 배치로 파일만 교체하면 CSS는 그대로 둘 수 있다.

- 왼쪽 위: `Basic`
- 오른쪽 위: `Heavy`
- 왼쪽 아래: `Wide`
- 오른쪽 아래: `Jump` / `Dash`

이미지 안에 키나 기술명을 넣지 않는다. 키캡·이름·쿨다운은 기존 DOM이 별도로
표시하므로, 이미지에는 기술의 실루엣만 둔다. 상세 생성 정보는
`web/ui-assets/README.md`에 기록한다.

## DOM 소유 경계

테마 CSS는 **외형만 소유**한다. 다음 파일이 가진 DOM과 상태 계약은 유지한다.

- `index.html`: `#load`, `#help`, `#stat`, `#sword`, `#combo` 등 정적 셸
- `ui.js`: 알림창, 스킬 슬롯, 하단 도크, 내비게이션, 보조 HP, 기본 `#uiStyle`
- `enemy.js`: `#eHud`, `#eBar`, `#eFill`, `#eTxt`, 피격·사망 상태
- `boss.js`: `#bHud`, `#bBox`, `#bGoal`, `#bName`, `#bFill`, `#bClear`
- `stealth.js`: `#stHud`, `#stVig`와 은신 상태 클래스
- `main.js`: 게임 수치, 쿨다운, 표시 여부, 인라인 갱신과 개발용 패널

테마 작업에서는 ID·클래스·DOM 순서·문구·`innerHTML`을 바꾸지 않는다. JS가 갱신하는 `width`, `transform`, `opacity`, `display`와 상태 클래스도 CSS에서 고정하지 않는다. 배치를 손댈 때는 `pointer-events`, `z-index`, safe area가 게임 입력을 막지 않는지 확인한다.

## 새 테마 추가

1. `web/ui-theme-bronze.css`를 참고해 `web/ui-theme-<name>.css`를 만든다.
2. 모든 선택자를 `body[data-ui-theme="<name>"]`로 스코프한다.
3. 의미 토큰부터 새 팔레트로 매핑하고, 필요한 부품의 표면 규칙만 추가한다.
4. JS나 기존 기본 CSS를 복사해 수정하지 않는다. 인라인 상태까지 덮는 `!important`는 가급적 쓰지 않는다.
5. `index.html`에 CSS 링크를 추가하고 `body` 속성값만 바꿔 비교한다. 여러 테마 CSS가 함께 로드되어도 스코프 값이 다르면 충돌하지 않는다.
6. 팔레트/표면, HUD, 팝업, QA처럼 작은 커밋으로 나눈다.

## 빠른 QA

- 첫 로딩 화면부터 게임 HUD까지 기본색이 번쩍이거나 테마가 끊기지 않는가
- 플레이어/보스 HP, 처치 수, EXP, 쿨다운이 실제 상태에 따라 계속 갱신되는가
- 일반·피격·위험·은신·보스·사망/클리어 상태가 색만 보고도 구분되는가
- 16:9, 좁은 창, 작은 높이에서 HUD가 겹치거나 화면 중앙을 과도하게 가리지 않는가
- 한글/숫자가 잘리지 않고 대비가 충분한가
- 조작 안내와 개발용 UI가 클릭·키보드·게임 입력을 막지 않는가
- 브라우저 콘솔에 CSS 로드 실패나 JS 오류가 없는가

## 롤백

현재 작업 브랜치는 `codex/ui-bronze-story-20260814`다. 이전 보라 시안은
`c57a5ab` 또는 `codex/ui-awakened-demo-20260814`에서 확인할 수 있다.

```bash
# UI 변경 이력 확인
git log --oneline --decorate -- web/index.html web/ui-theme-bronze.css docs/ui-theme-guide.md

# 새 UI와 기존 UI 전환
git switch codex/ui-bronze-story-20260814
git switch codex/ui-awakened-demo-20260814

# 공유된 이력을 보존하면서 특정 UI 커밋만 되돌리기
git switch codex/ui-bronze-story-20260814
git revert <commit-sha>
git push origin codex/ui-bronze-story-20260814
```

브랜치를 바꾸기 전에는 작업 중인 변경을 먼저 커밋하거나 임시 보관한다. 이미 푸시한 이력에는 `reset --hard`나 강제 푸시 대신 `git revert`를 사용한다.
