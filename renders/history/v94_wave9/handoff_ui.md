# v94 UI 작업이 남긴 요청 (9A-2 → main.js · boss.js 소유자)

작업 범위는 `web/ui.js` · `web/index.html` · `web/fonts/` 뿐이다.
아래는 **그 밖의 파일이라 손대지 않은 것들**이다. 급한 순서로 적는다.

증거: `renders/history/v94_wave9/ui/` (sheet_01~07 = before/after, after_* = 원본 컷)

---

## A. main.js

### A-1. 로딩 진행률을 실제로 흘려 달라 (계약 완료, 호출만 남음)
`window.__loadProgress(v)` 를 **index.html 인라인 스크립트가 첫 바이트부터 깔아 둔다.**
0~1 사이 값을 아무 때나, 몇 번이든 부르면 된다(뒤로 가는 값은 무시한다).

```js
window.__loadProgress(loaded / total);   // GLB 로더 onProgress 등 어디서든
```

- ui.js 는 main.js **맨 끝**에서 불려서 로딩이 끝난 뒤에야 붙는다. 그래서 실제 구현은
  index.html 쪽에 있고, ui.js 에는 "없으면 채우는" 안전망만 뒀다. 어느 쪽이든 호출은 안전하다.
- 지금은 호출이 하나도 없어서 **가짜 크리프**(0.3초 뒤부터 90% 를 점근선으로 기어감)가 돌고 있다.
  진짜 값이 한 번이라도 들어오면 크리프는 즉시 은퇴한다.
- `#load` 를 `display:none` 하는 시점은 지금 그대로 두면 된다(MutationObserver 가 보고 있다).
  다만 감추기 **직전에** `__loadProgress(1)` 을 한 번 불러 주면 막대가 끝까지 차는 게 보인다.
- `#load` 의 id 와 "display:none 으로 감춘다"는 계약은 유지해 달라. ui.js 의 타이틀 카드
  발화 게이트(`waitSpawn`)가 그걸 본다.

### A-2. console.* 3곳 ?dev 게이트 (판정 S10)
`main.js` 에 `console.*` 가 3개 남아 있다. ui.js·index.html 쪽은 0개로 정리했다.
평시 콘솔은 비어 있어야 한다(판정에서 "개발 흔적"으로 잡혔다).

### A-3. 칼 이름 두 가지 (지금은 ui.js 가 화면에서 되돌리고 있다)
`equipSword()` 근처:
```js
swordEl.textContent = (i + 1) + '. ' + SWORDS[i].name;   // '2. 백아'
setTimeout(() => { swordEl.style.opacity = 0.45; }, 1400);
```
- **번호 접두사**: `2.` 는 내부 목록 순서다. 플레이어에게 뜻이 없다(판정 S4).
  ui.js 가 20Hz 폴링에서 `/^\s*\d+\.\s*/` 를 떼고 있다. 원본에서 빼면 그 코드도 지운다.
- **불투명도 0.45**: 이름이 안 읽혔다. ui.js 가 `#sword{opacity:1!important}` 로 눌렀다.
  즉 **장착 순간 밝아졌다 흐려지는 연출이 지금은 안 먹는다.** 그 연출을 살리고 싶으면
  opacity 말고 다른 채널(테두리 번쩍임 등)로 옮겨 달라. 옮기면 ui.js 의 `!important` 를 뺀다.
- `swordEl.style.display = 'none'`(칼 없는 몸) 은 그대로 두면 된다. ui.js 가 그걸 보고
  계기판의 「칼」 셀째로 접는다.

### A-4. 소리 줄 문구 (지금은 ui.js 가 화면에서 되돌리고 있다)
```js
muteEl.innerHTML = '<span class="k">M</span>소리 ' + (on ? '꺼짐' : '켜짐');
```
조작 안내의 다른 줄은 전부 **동작형**("이 안내 접기 / 펼치기", "베기", "점프")인데 이 줄만
**상태형**이라 말투가 혼자 다르다(판정 S8). ui.js 가 `소리 끄기` / `소리 켜기` 로 다시 쓰고,
index.html 의 새 구조(`<span class="ks"><span class="k">M</span></span><span class="t">…</span>`)로
복원한다. 원본을 아래처럼 바꾸면 ui.js 의 `fixMute()` 를 지울 수 있다.
```js
muteEl.innerHTML = '<span class="ks"><span class="k">M</span></span>'
  + '<span class="t">소리 ' + (on ? '켜기' : '끄기') + '</span>';
```

### A-5. 회피 칩에 쿨다운 라디얼 붙이기 (선택)
main.js 가 `#uiSkills` 에 붙이는 `Space 회피` 칩은 ui.js 의 `.sk` CSS 를 같이 쓰고 있어서
생김새는 이미 한 벌이다. 다만 **쿨다운 표시가 없다.** 칩의 **첫 자식**으로
`<i class="cd"></i>` 를 넣고, 잠긴 동안 아래처럼 배경만 갈아 주면 시계 방향 쓸기가 공짜로 붙는다.
```js
cd.style.background = 'conic-gradient(from 0deg,rgba(4,4,3,.80) 0turn ' + left
  + 'turn,rgba(4,4,3,0) ' + left + 'turn)';   // left = 남은 비율 0~1
```
`.sk.off` 클래스가 붙어 있을 때만 보인다(투명도는 CSS 가 맡는다).

---

## B. boss.js

### B-1. 문구 2개 (지금은 ui.js 가 화면에서 갈아 끼우고 있다)
ui.js `TEXT_PATCH` 표에서 표시 단계에 치환 중이다. 원본을 고치면 표에서 지운다.

| 지금 (boss.js) | 화면에 나가는 말 | 이유 |
|---|---|---|
| `GOAL.expose = ' <i>· 위치 노출</i>'` | `· 요괴들이 증표를 쫓는다` | 명사 두 개로는 무슨 일이 일어나는지 안 읽힌다(판정 S8) |
| `<div class="hint">R 을 눌러 다시</div>` | `R 키를 눌러 다시 도전` | 조사는 붙었는데 서술이 안 끝난다(판정 S8) |

### B-2. 클리어 패널 「처치 0」 (판정 S6 후반)
`clearInfo.kills = getKills() - killsAtStart` 와 화면 왼쪽 아래 HUD 의 세션 누적이 **다른 수**다.
죽었다 살아나거나 R 을 끼면 어긋난다. ui.js 는 **눈에 보이는 숫자만** `__enemy.kills` 로 맞춰
놓았는데(fixClearKills), API·로그로 나가는 `clearInfo.kills` 는 여전히 다른 값이다.
어느 쪽이 정본인지 boss.js 가 정해 주면 ui.js 의 덮어쓰기를 뺀다.

### B-3. 배너 동안 보스 공격 유예 (판정 S7)
보스 배너 수명을 1.2초 → **2.5초**(완전 불투명 1.9초, 실측)로 늘렸다. 이제 배너가 떠 있는
동안 보스가 먼저 때리면 "글자를 읽다가 맞는" 그림이 된다. 조우 직후 1.5초 안팎의 공격 유예를
boss.js 쪽에서 넣어 주는 게 맞다. ui.js 는 게임 상태를 한 줄도 안 만진다.

### B-4. `#bClear` 구조는 CSS 로만 다시 칠했다
`h1 + table + .hint` 구조를 그대로 두고 표를 **기록패**로 보이게 덮었다(판정 S9).
행을 늘리거나 `td` 구성을 바꾸면 ui.js 의 `#bClear td` 규칙을 같이 봐 달라.

### B-5. `#bHud` 둘째 줄은 죽어 있지 않았다 (판정 S6 정정)
`#bBox` 는 보스전에 들어가면 `opacity:1` 로 정상 점등한다.
실측: `phase='보스전'`, `#bBox opacity=1`, `#bName='1층 · 각귀'`, `#bFill width=100%`
(증거 `after_boss_hpbar.png` · `crop_after_boss_hpbar.png`).
판정 당시에는 보스와 실제로 붙지 않아 계속 0 으로 보였던 것으로 보인다. 손댈 것 없음.
다만 클리어 뒤에는 상단 알약이 카드 제목과 같은 말("층 돌파")을 반복해서
ui.js 가 `body.uiCleared #bHud{opacity:0}` 으로 접는다.

---

## C. 모두에게 (밟기 쉬운 함정)

1. **`#uiSkills` · `#eHud` · `#sword` 는 이제 `#uiDock` 안에 있다.**
   ui.js 가 `initUI()` 에서 **부모만 옮겼다**(`appendChild`). 세 파일 다 `getElementById` 로
   잡고 있어서 참조는 안 끊긴다. 다만 **`position:fixed` 로 자리를 다시 잡으면 판 밖으로
   튀어나간다.** 자리는 계기판이 정한다.
2. **붓 서체는 글자가 넓다.** HUD 에 붓으로 짧은 말을 얹을 때 `white-space:nowrap` 을 안 주면
   「수면참」이 「수면/참」으로 접혀 판이 두 줄로 부푼다(실제로 한 번 부풀었다).
3. **붓 서체에 굵은 벌은 없다.** `font-weight:700` 을 주면 브라우저가 가짜 굵기를 만들어
   붓끝을 뭉갠다. ui.js 는 `font-synthesis:none` 을 body 에 박아 그 길을 막았다.
4. **index.html 의 모듈 로드 줄은 그대로다.** `<script type="module">import('./main.js' + location.search)</script>`
   한 줄은 글자 하나 안 건드렸다. 그 **위에** 로딩 진행용 일반 `<script>` 한 덩이가 새로 들어갔다.
5. **`page.waitForFunction(fn, {timeout})` 은 안 먹는다.** 두 번째 인자는 `arg` 다.
   `waitForFunction(fn, null, {timeout})` 라고 써야 한다. 안 그러면 기본 30초에 걸려
   "로딩이 안 끝난다"로 오진한다(이번에 한 번 당했다).
6. **"딱 한 번" 짜리 UI 는 로딩 중에 태워 먹기 쉽다.** ui.js 는 main.js **맨 끝**에서
   붙는데, 그때 캐릭터 GLB 는 아직 내려오는 중이라 20Hz 폴링이 로딩 화면 뒤에서 먼저 돈다.
   나침반 병기·요괴 핍 라벨을 그 틱에 띄웠더니 **아무도 못 본 채 소모**됐다
   (로딩이 길면 100% 소모, 짧으면 살아남는 경주였다). 지금은 입장 카드가 걷히는
   순간(`awake`)부터만 센다. 비슷한 1회성 연출을 붙일 때 같은 함정을 밟게 된다.
7. **수명 짧은 카드는 스크린샷 타이밍이 거짓말을 한다.** 타이틀 카드를 로딩 종료 +0.5초에
   찍었더니 등장 애니 t=150ms 였고 글자가 통째로 안 보였다("카드가 안 뜬다"로 오진).
   +1.2초 이후에 찍어야 한다. 수명·불투명도는 스크린샷 말고 **페이지 안에서** 재라
   (`ui94_banner.mjs` 방식: `setInterval` 로 `getComputedStyle().opacity` 를 훑는다).
