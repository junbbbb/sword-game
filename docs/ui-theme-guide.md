# 클린 슬레이트 UI 가이드

현재 UI는 기존 테마 위에 색만 덮는 스킨이 아니다. `web/ui.js`가 정보 위계와 DOM을
새로 조립하고, `web/ui-rebuild.css`가 **Black Ledger** 화면 체계를 전담한다.
`web/index.html`은 아래 한 파일만 불러오며 `data-ui-system`으로 활성 상태를 표시한다.

```html
<link id="uiCss" rel="stylesheet" href="./ui-rebuild.css">
<body data-ui-system="black-ledger">
```

## 바꿀 때의 순서

작은 시안 변경은 `web/ui-rebuild.css` 맨 위 `:root` 토큰부터 고친다. 같은 색이나
간격을 컴포넌트 선택자마다 다시 쓰지 않는다.

| 토큰 묶음 | 역할 |
|---|---|
| `--bl-ink-*` | 배경과 표면의 깊이 |
| `--bl-bone*`, `--bl-muted` | 본문, 수치, 보조 정보 |
| `--bl-brass*`, `--bl-gold` | 프레임, 선택, 성장과 보상 |
| `--bl-rust*`, `--bl-moss*` | 위험/피격, 생존 상태 |
| `--bl-skill`, `--bl-line*`, `--bl-shadow` | 액션, 경계, 깊이 |
| `--bl-font`, `--bl-safe-*` | 공통 서체와 기기 안전 여백 |
| `--fx-damage-*` | `enemy.js`가 읽는 월드 데미지 숫자 색 |

`--fx-damage-*`는 Three.js 재질 초기화 때 CSS에서 한 번 읽으므로 바꾼 뒤 페이지를
새로고침한다. 값은 `#RGB` 또는 `#RRGGBB`가 가장 안전하다. 정보 구조까지 바꾸는
요청이면 토큰을 억지로 늘리지 말고 `ui.js`의 해당 컴포넌트와 CSS 절을 함께 고친다.

## 컴포넌트 지도

`web/ui-rebuild.css`는 다음 순서로 나뉜다.

1. 레이어와 로딩 장부
2. 하단 HUD의 생존자 카드·액션 덱·장비 카드
3. 목표와 보스 HUD
4. 조작 안내 서랍
5. 플레이어 머리 위 HP와 화면 가장자리 목표 표시
6. 입장·보스 경고·사망·클리어 연출
7. 보조 HUD, 화면 소유 상태, 반응형 규칙

DOM 생성과 상태 연결은 같은 순서의 주석이 있는 `web/ui.js`에서 찾는다. CSS는 외형과
배치를, JS는 노드 생성·상태 읽기·인라인 수치 갱신을 맡는다.

## 동작 계약

다음 ID와 구조는 다른 시스템이 직접 읽거나 갱신하므로 시각 작업 중 임의로 바꾸지 않는다.

| 소유 파일 | 유지할 계약 |
|---|---|
| `index.html` | `#uiCss`, `#load`, `#help`, `#stat`, `#sword`, `#combo` |
| `enemy.js` | `#eHud > #eBar > #eFill`, `#eTxt`, 피격·사망 상태 |
| `boss.js` / `level2.js` | `#bHud`, `#bBox`, `#bGoal`, `#bName`, `#bFill`, `#bClear` |
| `stealth.js` | `#stHud`, `#stVig`와 은신 상태 클래스 |
| `ui.js` | `#uiRoot`의 네 레이어, `#uiDock`, `#uiSkills`, `#uiHpFloat`, `#uiNav`, `#uiPip` 및 연출 노드 |

`#eHud`는 이름과 달리 **플레이어 체력/처치 HUD**다. 몬스터 머리 위 체력바와 혼동하지
않는다. 스킬 슬롯의 첫 자식 `i.cd`, 그 다음 `b.cds`, 그리고 `data-k` 값은
`main.js`와 `ui.js`가 공유하는 구조 계약이다. 로직이 쓰는 `width`, `transform`,
`opacity`, `display` 인라인 값과 `uiCine`, `uiCleared`, `uiDeathOn` 같은 상태 클래스도
고정값으로 덮지 않는다.

## 몬스터 머리 위 체력바

실제 몬스터 체력바는 DOM/CSS가 아니라 `web/enemy.js`의 Three.js 월드 렌더링이다.

- `BAR_W`, `PIP_H`: 명패의 월드 크기
- `★머리 위 판 (체력 바 · 인지 표식)` 절: 판 시스템과 한 드로우콜 구조
- `체력 바 (머리 위)` 절의 `pipMat`: 명패·프레임·트랙·연속 채움·빈사 끝점·등급 리벳 셰이더
- `pipMesh`: 동적 버퍼를 실제 메시로 묶는 곳
- `updatePlates()`: 타격 후 노출 시간, 알파, 위치, `hp/maxHp`를 버퍼와 uniform에 전달하는 곳

색·모양은 `pipMat`의 프래그먼트 셰이더에서, 전체 크기는 `BAR_W`/`PIP_H`에서 조정한다.
노출 판정(`e.pipT`), 최대 개수, 버퍼 attribute 이름은 성능과 전투 로직 계약이므로 외형
수정만 할 때는 유지한다.

## 레벨 상승 연출

레벨 상승은 화면 중앙 창을 띄우지 않는다. `web/ui.js`의 `레벨 / 체력` 절이 레벨 변화를
감지하면 `showLevelUp()`에서 `window.__feel.levelUp(window.__root, height)`를 호출하고,
하단 레벨 숫자에는 짧은 `pulse`만 준다.

캐릭터 주변 빛은 `web/feel.js`의 `레벨 상승 빛` 절에 있다. `levelRoot` 아래 발밑 고리,
상승 고리, 세로 베일 셰이더, 스파크를 두며 `levelUp()`이 시작하고
`updateLevelUp()`이 실제 시간으로 약 1초 동안 갱신한다. 지속 시간과 스파크 수는 파일
상단의 `LEVEL_UP_T`, `LEVEL_UP_SPARKS`에서 바꾼다. 화면 전체 플래시나 DOM 모달을 다시
추가하지 않는다.

## QA와 배포 빌드

```bash
# 로컬 확인
python3 -m http.server 8777 --directory web
# http://127.0.0.1:8777/

# 문법과 배포본 생성
node --check web/ui.js
node --check web/enemy.js
node --check web/feel.js
python3 tools/build_deploy.py

# 프로덕션 배포가 필요할 때
cd dist
vercel deploy --prod --yes --archive=tgz
```

최소 확인 항목은 16:9·좁은 화면 겹침, 플레이어/몬스터/보스 HP 갱신, 스킬 쿨다운,
입장·사망·클리어 상태, 레벨업 때 중앙 모달이 없는지, 콘솔 오류와 CSS 404가 없는지다.

## 이전 시안과 롤백

`web/ui-theme-abyss.css`와 `web/ui-theme-bronze.css`는 파일과 Git 이력에 남아 있지만
현재 `index.html`에서는 불러오지 않는다. 새 DOM에 옛 CSS 한 장만 다시 연결하면 구조가
섞이므로, 옛 시안 전체가 필요할 때는 해당 브랜치/커밋으로 되돌린다.

```bash
# 현재 변경과 UI 이력 확인
git diff -- web/index.html web/ui.js web/ui-rebuild.css web/enemy.js web/feel.js
git log --oneline --decorate -- web/index.html web/ui.js web/enemy.js web/feel.js

# 옛 시안은 전환하지 않고 내용만 확인
git show 2ffa67c:web/ui-theme-bronze.css
git show c57a5ab:web/ui-theme-abyss.css

# 옛 시안 브랜치에서 전체 화면 확인
git switch codex/ui-bronze-story-20260814
git switch codex/ui-awakened-demo-20260814

# 이미 공유한 새 UI 커밋을 안전하게 취소
git switch codex/ui-clean-slate-20260814
git revert <commit-sha>
git push origin codex/ui-clean-slate-20260814
```

브랜치 전환 전에는 작업 중인 변경을 커밋하거나 임시 보관한다. 공유한 이력에는
`reset --hard`나 강제 푸시 대신 `git revert`를 사용한다.
