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
<body data-ui-theme="bronze-story">
```

- 현재 시안: `data-ui-theme="bronze-story"`
- 이전 시안: `data-ui-theme="abyss-hunter"`
- 끄기: `data-ui-theme` 속성을 제거한다.
- 다른 테마로 전환: 속성값만 새 테마 이름으로 바꾼다.

각 테마 규칙은 자기 `body[data-ui-theme="..."]` 아래로 제한한다. 테마 CSS는
`ui.js`의 동적 기본 스타일보다 먼저 로드되지만, `body[...]`를 더한 높은 선택자
우선순위로 외형을 유지한다. 상태 제어용 인라인 `width`, `transform`, `opacity`,
`display`는 테마가 덮지 않는다.

## Bronze Story 팔레트와 표면

색과 공통 표면은 `web/ui-theme-bronze.css` 상단의 `--bs-*` 토큰 블록에서 먼저
고친다. 개별 HUD 선택자에 같은 색을 반복해서 직접 쓰지 않는다.

| 의미 | Bronze Story 토큰 | 용도 |
|---|---|---|
| 서체 | `--bs-font-ui`, `--bs-font-display` | 수치, 픽셀풍 제목/알림 |
| 바탕 단계 | `--bs-night-*`, `--bs-charcoal*` | 먹색 배경과 판 깊이 |
| 판 표면 | `--bs-panel*`, `--bs-panel-fill*` | 카드, 도크, 보조판 |
| 글자 | `--bs-cream*`, `--bs-parchment`, `--bs-muted` | 주 정보, 설명, 비활성 정보 |
| 테두리/장식 | `--bs-bronze*`, `--bs-frame-image` | 이중선과 주요 카드 모서리 |
| 성장/보상 | `--bs-gold*` | 레벨, EXP, 목표, 획득물 |
| 생존/위험 | `--bs-green*`, `--bs-red*` | 플레이어 HP, 보스, 피격, 사망 |

`--ui-*`와 `--rb-*`는 위 토큰을 가리키는 호환 alias다. 기본 UI 구조는 유지하고
Bronze Story 토큰을 바꾸면 로딩 화면과 동적 HUD가 함께 따라오게 한다. 하단/머리 위
체력처럼 JS와 공유해야 하는 완성 그라데이션은 `--ui-hp-*-fill`, 성장 바는
`--ui-exp-fill`, 데미지 숫자는 `--fx-damage-*`에서 바꾼다.

`--fx-damage-*` 다섯 값은 Three.js 재질로도 전달되므로 `#RGB` 또는 `#RRGGBB`
형식으로 지정한다. `oklch()`나 `color-mix()` 같은 문법은 안전한 기본색에 폴백한다.

색은 의미를 유지한다. 팔레트를 바꿔도 체력=생존, 적색=보스/피격,
금색=성장/보상, 청동색=선택/행동이라는 역할은 섞지 않는다. 투명도, 그라데이션,
프레임과 표면 질감은 같은 파일에서 조정하되 작은 변경은 먼저 토큰으로 해결한다.

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
