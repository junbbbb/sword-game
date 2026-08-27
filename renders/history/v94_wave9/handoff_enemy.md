# handoff — 9A-3 (적 반응·은신·보스) → 다른 파일 소유자에게

작성 2026-08-10. 소유 파일은 `web/enemy.js` · `web/stealth.js` · `web/boss.js` 뿐이라
아래 것들은 **내가 못 고친다.** 근거(실측)까지 같이 적는다.
증거 정본: `renders/history/v94_wave9/enemy/`

---

## ① [해결됨 · 9A-1 지형] level.js 가 한동안 **브라우저에서 통째로 안 떴다** (기록용)

2026-08-10 21:1x 에 `web/level.js` 528 줄 앞 쉼표가 빠져 있었다(21:2x 에 스스로 고침).
같은 함정을 또 밟을 수 있으니 진단법만 남긴다.

```
527:      '  foam = max( foam, ( 1.0 - smoothstep( 0.0, 0.055, wd ) ) * 0.75 );'     <- 여기 끝에 , 없음
528:      '  // 거품 바깥 한 줄은 더 희게(마루). 안쪽은 성기게 부서진다',
```

증상: `SyntaxError: Unexpected string` → level.js 를 import 하는 **모든 모듈**
(nav · stealth · enemy · boss · main)이 같이 죽고 로딩이 87% 에서 멈춘다.
★`node --check level.js` 는 **통과한다**(CommonJS 로 읽어서). 브라우저 모듈 파서만 잡는다.
모듈로 검사하려면 `.mjs` 로 복사해서 `node --check` 할 것.
확인 방법(모듈별 격리):

```js
// index.html 을 띄운 페이지에서
for (const m of ['level.js','nav.js','stealth.js','props.js','enemy.js','boss.js','feel.js','ui.js','main.js'])
  try { await import('./'+m+'?t='+Date.now()); console.log(m,'OK'); }
  catch(e){ console.log(m, e.name+': '+e.message); }
```

---

## ② [9B-2 이펙트 / feel.js] 은신·가림 실루엣 색을 바꿔 달라 — 건틀릿 캐릭터 1순위 격차

건틀릿 심사관: "수풀 뒤에서 3~4초 클립을 돌려도 플레이어를 못 찾겠다"
(`v93_gauntlet/character/FINAL_07_xray.jpg` — "형광 잎 위 흰 와이어프레임").

**그 흰 와이어프레임은 stealth.js 가 아니라 feel.js 다.**
`feel.js` 1005~1022 의 두 벌:

| | 색 | 알파 | 림 |
|---|---|---|---|
| 은신용 SIL | `0x0b0910` | 0.80 | `0xd9cdb4` |
| 상시(가림) OCC | `0x171320` | **0.52** | `0xf0e6d2` (밝은 종이색) |

xray 시트에 찍힌 것은 **OCC 쪽**이다(수풀에 숨은 게 아니라 소품 뒤를 지나갈 때).
알파 0.52 + 밝은 종이색 림 0.85 조합이라, 형광 초록 잎 위에서는 **안쪽 먹이 안 보이고
림만 남아** 정확히 "흰 와이어프레임"이 된다.

### 내가 잰 숫자 (같은 방식으로 A/B 하면 된다)
- 방법: `window.__cap()` 이 `composer.render()` 를 **동기로** 부른다는 점을 이용해
  **한 태스크 안에서** (렌더→읽기→플레이어 메시 전부 끄기→렌더→읽기).
  그 사이 게임 루프가 안 돌아 세계가 완전히 멈추므로, 두 장의 차이 = 정확히 플레이어 픽셀.
  (시간을 두면 잎·풀이 움직여서 화면 전체가 마스크로 잡힌다. 3번 헛고생했다.)
- 스크립트: 아래 ⑤ 참고.

BUSH_16 한가운데, 플레이어 마스크 3,65x px 기준:

| 조합 | 몸 평균 L | 배경 L | ΔL | 웨버 |
|---|---|---|---|---|
| 9차 이전 | 72.7 | 66.9 | **+5.9 (잎보다 밝다)** | 0.081 |
| 9차 stealth.js 수정 후 | 51.7 | 70.3 | **-18.5** | 0.264 |

BUSH_13 은 **거의 안 움직였다**(옛 64.1 → 새 62.0). 그 자리에서는 앞잎 카드가 몸을
가려서 화면에 나오는 게 stealth.js 의 먹이 아니라 **feel.js 의 가림 껍데기**이기 때문이다.
`debug.tune({inkLo, inkHi})` 을 0 과 1 극단으로 흔들어도 1.5/255 밖에 안 움직인 것이 증거다
(`enemy/ink_sweep.json`).

### 요청
1. **OCC 조합 재조정**: 알파 0.52 → 0.68 안팎으로 올리고 림 비중(0.85)을 0.55~0.6 으로 낮춰
   "안쪽이 먹, 테두리는 거들기" 쪽으로. 지금은 반대라 밝은 배경에서 윤곽만 뜬다.
2. **SIL(은신) 도 한 단 더 짙게**: `0x0b0910` 은 이미 검지만 알파 0.80 이라 초록 잎이 20% 비친다.
   0.88~0.92 로 올리면 stealth.js 쪽 먹(내가 이번에 3배 어둡게 했다)과 값이 이어진다.
3. 값을 바꾼 뒤 위 방식으로 **BUSH_13·BUSH_16 두 곳**에서 웨버 0.35 이상이 나오는지 확인.
   (내 파일만으로 도달 가능한 상한이 0.26 이었다)

`feel.js` 에 이미 `window.__feel.silTune({col,rim,a,rimMix,rimP,bias}, 'sil'|'occ')` 가 있어서
페이지를 안 고치고 브라우저에서 바로 스윕할 수 있다.

---

## ③ [9B-1 전투구조 / main.js] 알아 둘 것 — enemy.js 공개 API는 **추가만** 했다

시그니처 변경 0건. 기존 호출부(`enemies.update(dt, ctx)` · `nearestTo` · `snapFacing` ·
`damagePlayer` · `kills` · `resetKills` · `hot` · `swing` · `dead` · `deadIn` …)는 그대로다.

새로 생긴 읽기 창구(필요하면 쓰고, 안 써도 된다):

| 창구 | 뜻 |
|---|---|
| `enemies.killLog` | 처치 전수 기록 `{t, swing, kills, ex, ez, d, hp0, maxHp, ndc, onScreen}` (링 24) |
| `enemies.react` | `{stun, wind, pip, flash, hitStun, atkWind, dmg, leak}` — 지금 몇 마리가 경직/예비자세인지 |
| `enemies.plates` | `{pip, mark, tex}` — 머리 위 판이 몇 장 서 있나 |
| `enemies.warmCut(renderer, camera)` | 두 동강 재질 예열 **보조** 경로 |
| `boss.runKills` | 이 판에서 잡은 수(클리어 패널과 같은 값) |
| `boss.grace` | 조우 유예 남은 초 |

### 두 동강 셰이더 예열은 **이미 자동이다** — main.js 가 할 일 없음
`enemy.js` 가 로드 직후 6프레임 동안 "진짜 시체와 같은 조합"(뼈 공유 SkinnedMesh 2벌 x
matA/matB)을 **1000분의 1 크기**로 세워 둔다. 화면 안이라 반드시 그려지고 = 그때 프로그램이
컴파일되고, 1픽셀 미만이라 아무도 못 본다. 6프레임 뒤 풀에 반납한다.
- ★비스킨드 판때기로 예열하면 소용없다. three 프로그램 캐시 키에 `USE_SKINNING` 이 들어간다.
- ★matA/matB 12벌은 `onBeforeCompile.toString()` 이 전부 같아 프로그램 한 벌을 나눠 쓴다.
  그래서 한 쌍만 데우면 전부 데워진다.
- `?dev` 에서 `[enemy] 두 동강 재질 예열 완료` 가 한 번 찍힌다.
`renderer` 를 넘겨 다시 데우고 싶으면 `enemies.warmCut(renderer, camera)` 를 부르면 된다.

### 데미지·속도가 바뀌었다 (대시·캔슬 튜닝의 전제)
- 고블린 한 대 **8 → 6**, 초당 상한(새는 통) 10 → 7.5
- 고블린 공격에 **예비 자세 0.30초**가 새로 붙었다(총 예고 0.30 + 0.575 = 0.875초)
- 고블린 추격 속도 **1.72~2.13 → 2.30~2.78** (플레이어 걷기 1.71 < 요괴 < 달리기 3.20)
- 리쉬 **16 → 24m**
- 맞으면 **경직 0.13초 + 휘두르던 공격 취소** (선타에 값이 생겼다)
- 보스: 후려치기 14→10 · 돌진 20→13 · 내려찍기 28→18, 예고 0.80→0.95 / 1.10→1.45 / 1.20→1.45,
  내려찍기 반경 4.0→3.6, **아레나 첫 진입 1.5초 공격 유예**

---

## ③-2 [9A-2 UI] handoff_ui.md 의 boss.js 요청 5건 — 회신

| 요청 | 처리 |
|---|---|
| **B-1** 문구 2개 | **원본을 고쳤다.** `GOAL.expose` → `· 요괴들이 증표를 쫓는다`, 클리어 힌트 → `R 키를 눌러 다시 도전`. ui.js `TEXT_PATCH` 에서 두 줄 지워도 된다(안 지워도 치환 대상이 없어 무해). |
| **B-2** 클리어 패널 처치 0 | **boss.js 가 정본이다.** `clearInfo.kills = getKills() - killsAtStart` 를 매 프레임 자기교정(바깥 카운터가 줄면 기준선도 내린다)하도록 고쳤다. 실측: 잡몹 3킬 후 돌파 → HUD 3 · `boss.runKills` 3 · `clearInfo.kills` 3 · 패널 "처치 3" **삼자일치**. `fixClearKills()` 빼도 된다. |
| **B-3** 배너 중 공격 유예 | **넣었다.** 아레나 첫 진입에 `FIGHT_GRACE = 2.0`(게임초). 배너 불투명 1.9초를 덮으려고 1.5 에서 올렸다. 실측(`enemy/banner_grace.json`): 배너 불투명(>0.5) 구간 1.17~4.43초 동안 **피해 0**, 첫 예고는 3.34초(배너가 걷히는 꼬리)에서 시작 → 첫 피해는 배너가 사라진 뒤. |
| **B-4** `#bClear` 구조 유지 | `h1 + table(4행) + .hint` 그대로다. 행 수·`td` 구성 안 건드렸다. 힌트 **문구만** 바뀌었다. |
| **B-5** `#bHud` 오진 정정 | 확인. boss.js 는 손대지 않았다. |

★ `#eHud` 도킹도 확인했다(실측): `position:static`, 부모 `.cell`, rect 264,709 로 `#uiDock`
(216,696,848,50) 안에 정확히 들어간다. enemy.js 의 `position:fixed` 는 ui.js 스타일이 덮는다 —
**enemy.js 쪽에서 자리를 다시 잡을 필요 없음.** (증거 `enemy/shot_hud_dock.png`)

---

## ④ [9A-2 UI / ui.js] 두 가지

1. **`fixClearKills()` 는 이제 안 해도 된다.** boss.js 가 판 기준으로 정확히 센다.
   실측(2026-08-10): 잡몹 3킬 후 층 돌파 → HUD 3 · `boss.runKills` 3 ·
   `clearInfo.kills` 3 · 패널 "처치 3" **삼자일치**(`enemy/boss_verify2.json`).
   덮어쓰기를 남겨 둬도 값이 같아 해는 없지만, 두 곳이 같은 수를 따로 세는 구조는 언젠가 갈린다.
2. **머리 위 판(체력 핍 · ! / ? / 공격 쐐기)은 3D 월드 빌보드**다. DOM 이 아니라서
   HUD 레이아웃과 안 부딪힌다. 드로우콜은 둘 합쳐 2다.
   다만 `depthTest:false` 라 항상 그려진다 — HUD 패널과 화면에서 겹칠 수 있다.
   겹침이 거슬리면 알려 달라(높이·크기는 enemy.js 안 상수 `PIP_*` `MARK_SZ` 하나로 조절된다).

---

## ④-2 [주인 없음 · nav.js] 평시 콘솔에 한 줄이 남는다

`?dev` 없이(= 배포 조건) 띄우면 콘솔에 **정확히 한 줄**이 남는다.

```
[nav] 격자 60x60 (1.6m), 걸을 수 있는 칸 2346/3600 = 65%
```

`web/nav.js` 는 9차 소유표에 없어서 내가 못 건드린다. 내 파일 셋(enemy·stealth·boss)은
전부 `?dev` 게이트를 걸어 0줄이다. 10차에 누가 nav.js 를 맡으면 한 줄만 감싸면 된다.

---

## ⑤ 재현용 스크립트 (누구든 다시 재려면)

`/private/tmp/.../scratchpad/a3/` 에 있고 세션이 끝나면 사라진다. 핵심만 적는다.

```js
// 실루엣 대비 — 한 태스크 안에서 두 장(세계 정지)
window.__cap();  const A = cv.toDataURL('image/png');
root.traverse(o => { if (o.isMesh) { o.__s = o.visible; o.visible = false; } });
window.__feel.silTune({a:0},'sil'); window.__feel.silTune({a:0},'occ');
window.__cap();  const B = cv.toDataURL('image/png');
// 되돌리고, 두 장이 다른 픽셀만 모아 평균 명도를 비교한다
```

★함정 (이번에 실제로 밟은 것들)
- **탭이 앞에 없으면 `?dev` 의 `setTimeout` 루프가 초당 1회로 스로틀**된다. 게임시계가
  거의 안 흘러서 "예고가 7초 걸린다" 같은 **가짜 버그**가 잡힌다. `page.bringToFront()` 필수.
- 시간으로 어림하지 말고 **값으로** 기다릴 것(`stealth.state().ink > 0.985` 등).
- `getImageData` 배열(390만 값)을 CDP 로 넘기면 몇 분 걸린다. 계산은 페이지 안에서 끝낼 것.
- 수풀 앞잎 카드 자리는 로드마다 `Math.random()` 으로 달라진다. **같은 페이지 안에서**
  값만 바꿔 가며 재야 배경이 고정돼 비교가 정직하다(`debug.tune`).
