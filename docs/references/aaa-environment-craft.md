# AAA 환경아트 — 싼 자원으로 돌을 무겁게 읽히게 하는 기술

15차 조사(2026-08-13). 오너 지시로 착수했다.

> "맵좀갈아엎고 다시하자. 롤, 뭐 나혼자만레벨업, 이런풍의 그냥 깔끔하면서 미감있고.
> 지금점점저퀄리티 느낌으로 가고있어. 뭐오버워치나 발로란트느낌의 맵도좋네..
> 거기서 질감이나 이런거 어떻겧 표현했는지 조사도해봐. 돌 바닥이런것들도 참 느낌있잖아.
> 지금은타일덩어리 직육면체 들같아.."
>
> 보충: "발로란트, 포트나이트등 그 큰게임들에서 뭐 디테일한 색을 가져오자는게 아니라
> 그 텍스처라 그러나? 질감? 그런것들이 **가성비있게** 잘 만들어져서 그런거 언급했던거긴 해"

**그래서 이 문서는 색 모사가 아니라 경제학을 다룬다.** 오버워치·발로란트·롤·포트나이트가
적은 텍스처·적은 폴리곤·적은 드로우콜로 어떻게 돌을 무겁게 읽히게 하는가. 각 기법마다
우리 파이프라인(three.js · 로우폴리 · 핸드페인트 타일 · 버텍스 조명 · 노멀맵 없음 · ACES)에서
**그대로 되는가 / 변형이 필요한가 / 불가한가**를 판정해 뒀다.

조사 원칙: 소스를 실제로 열어 읽었다. 못 읽은 것은 못 읽었다고 적었다. 인용은 원문 그대로 두고
번역을 붙였다. 추측은 "추정"이라고 표시했다.

★**미리 밝혀 둘 것 하나.** 오너가 포트나이트를 같이 들었는데, **에픽이 포트나이트 환경 텍스처
공정을 밝힌 1차 자료는 못 찾았다**(아트북·GDC 발표 어디에도 텍스처 경제학이 없다).
그래서 이 문서의 실제 근거는 **오버워치(블리자드 공식 + 블리자드 아티스트 본인) ·
발로란트와 롤(라이엇 공식) · Dota 2(밸브 공식) · 트라인(Frozenbyte 사내 위키) ·
워프레임(디지털 익스트림스 공식)** 이다. 포트나이트는 빠져 있다.
다행히 오너가 원한 것은 특정 게임이 아니라 그 게임들이 공유하는 공정이고, 그 공정은 위 다섯에서
같은 모양으로 나온다.

---

## 1. 먼저 진단 — 지금 화면이 왜 "타일 덩어리"로 읽히는가

기법을 옮기기 전에, 오너의 "저퀄리티"가 화면에서 무엇으로 측정되는지부터 못 박는다.
비교 대상은 오너가 직접 넣어 둔 롤 스크린샷(`refpack/lol_ground_owner_ref.png`,
`lol_ground_owner_ref2.png`)과 14차 게임 화면(`renders/history/v99_wave14/dungeon_bs/prod_hall.png`)이다.

### 1-1. 실측표

| 잰 것 | 롤(오너 레퍼런스) | 우리 14차 화면 | 판정 |
|---|---|---|---|
| 채도 중앙값 (걸어 다니는 바닥) | **0.29 ~ 0.31** | **0.50 ~ 0.54** | 1.8배 과하다 |
| 채도 상위 5% 가 있는 곳 | 풀·이끼(H 81°) — **못 걷는 면** | 바닥 판석(H 21°) — **걷는 면** | 채도 예산을 바닥에 다 썼다 |
| 값 요동 σ · 매크로(>1.2m) | 0.012 | 0.016 | 비슷 |
| 값 요동 σ · 판석대(0.25~1.2m) | **0.021** | **0.060** | **2.9배 시끄럽다** |
| 값 요동 σ · 미세(<0.25m) | **0.034** | **0.111** | **3.3배 시끄럽다** |
| 매크로 / 판석대 비 | **0.58** | **0.27** | 큰 얼룩이 절반밖에 없다 |
| 캐릭터 / 바닥 휘도비 | (해당 없음) | **1.39배** | ★**우리 자기검증 기준 2배 미달** |
| 기둥 / 바닥 휘도비 | | 1.34배 | 기둥이 바닥에서 안 떨어진다 |
| 벽 / 바닥 휘도비 | | 0.71배 | |
| **줄눈 면적** (국소밝기 80% 미만) | **2.7%** | **16.0%** | **6배 넓다** |
| 깊은 줄눈 (국소밝기 72% 미만) | 0.7% | 10.4% | **15배** |
| 판석 장수 (5.0m 타일 1장 안) | | **19장** | 권고 하한 16, HOTS 급 ~100 |
| 판석 최대/최소 지름비 | 약 6배 | 12.2배 | 비율은 오히려 과하다 |

측정 방법은 재현 가능하다: sRGB→선형 변환 후 Rec.709 휘도, 값 요동은 가우시안 3대역 분해
(σ 1.2m / 0.25m 기준), 줄눈은 전역 임계가 아니라 **국소 중앙값 대비**(가우시안 σ6px)로 잡았다.
화면 픽셀·미터는 롤 55 px/m · 우리 64 px/m 로 맞췄다.

### 1-2. 숫자가 말하는 것

**① 채도를 걷는 바닥에 다 써 버렸다.** 롤에서 판석 광장은 S 0.31, 그 주변 풀이 S 0.46 이다.
그런데 값(V)은 돌 0.294 · 풀 0.282 로 **거의 같다.** 즉 롤의 지면은 값으로는 한 덩이의
고요한 판이고, 돌과 풀은 **색상과 채도로만** 갈린다. 그 위에 챔피언이 올라서면 챔피언만 튄다.
우리는 화면의 99.4% 가 S 0.50 이고 그중 제일 채도 높은 것이 바닥 판석 자체다.
**캐릭터가 설 자리(낮은 채도의 조용한 판)를 안 남겨 뒀다.**

**② 캐릭터가 바닥에서 1.39배밖에 안 떨어진다.** 13차 던전은 이 값이 4.4배였고
`docs/dungeon1-design.md` 6절의 자기검증 항목이 "2배 이상"을 요구한다. 14차에서 씬을
여섯 배 밝히면서 이 계약이 깨졌다. 오너가 "저퀄"이라고 느끼는 감각의 절반은 색이 아니라
**주인공이 배경에 잠긴 것**이다. 이건 취향이 아니라 회귀다.

**③ 시끄러움이 3배인데 정보량은 더 적다.** 판석대·미세 대역 모두 롤의 3배로 요동친다.
그런데 롤 화면은 더 "잘 그려진" 것처럼 보인다. 왜냐하면 롤의 변화는 **판석의 윤곽선**
(모양 정보)이고 우리 변화는 **판석 안의 그라디언트**(잡음)이기 때문이다.
값 진폭이 큰데 정보는 없는 것 — 이게 정확히 "싸구려 텍스처 팩" 인상이다.

**④ 큰 얼룩이 모자란다.** 매크로/판석대 비가 롤 0.58, 우리 0.27. 롤 바닥에는 광장 전체를
가로지르는 넓고 부드러운 명암 기울기가 깔려 있고 그 위에 판석이 얹힌다.
우리는 어디를 봐도 똑같은 세기로 아른거린다 = 벽지.

**⑤ 줄눈이 판석보다 눈에 띈다.** 화면 면적의 16% 가 줄눈이다(롤 2.7%). 깊은 줄눈만 봐도
10.4% 대 0.7% 로 **15배**다. 게다가 우리 줄눈은 판석의 어두운 값이 아니라 **보색(보라 vs 주황)** 이다.
줄눈이 그림의 주인공이 되면 판석은 그 사이에 낀 덩어리로 보인다 — 이게 "타일 덩어리"의 물증이다.

**⑥ 판석 장수가 하한이다.** 5.0m 타일 한 장에 판석 19장. 폴리카운트에서 타일링 돌바닥의 반복이
보인다는 질문에 나온 진단이 정확히 이거다: "**You only have 2² stones, while HOTS [Heroes of the Storm]
is around 10² or so** ... So I suggest that be the first thing you do"(Snader), 그리고 같은 스레드에서
최소 권고가 16장이다([polycount](https://polycount.com/discussion/132419/hand-painted-stone-texture-bad-tiling)).
우리는 하한을 겨우 넘겼다. 판석 하나가 0.89m(중앙값)라 화면에서 크게 보이는데,
그러면 되풀이 주기가 눈에 바로 잡힌다.

### 1-3. 확대해서 눈으로 본 차이

롤 판석 광장(`refpack/lol_ground_owner_ref2.png` 확대):

* 판석이 **불규칙 다각형**이다. 4~7각형이고 **똑같은 모양이 하나도 없다.**
  한 화면 안에서 제일 작은 조각과 제일 큰 판이 대략 **1 : 6** 이다.
* 줄눈은 **가늘고 어두운 선**이다. 판 폭의 1~2% 수준이고, 벌어진 자리에서만 굵어진다.
* ★**금이 판석을 무시하고 지나간다.** 갈라진 큰 균열이 여러 판을 대각으로 가로지른다.
  판석보다 **한 단계 큰 스케일의 두 번째 그림**이라 "칸 격자" 읽기를 부순다.
* 이끼·풀이 **가장자리와 줄눈으로 침범**하고, 포장의 바깥 경계가 직선으로 안 끝난다.
  돌이 풀에 녹아 사라진다.
* 판마다 **위쪽이 살짝 밝고 아래쪽이 어둡다.** 진폭은 아주 작다.
* 몇 장은 **가라앉았거나 기울어** 있다.

우리 14차 바닥(`prod_hall.png` 확대):

* 판석이 **둥근 아메바 덩어리**다. 크기가 사실상 한 종류고 전부 볼록하다. 캐러멜 같다.
* 줄눈이 **넓은 보라 수로**고 판석(주황)과 색상·값 대비가 크다. 줄눈이 판석보다 눈에 띈다.
* 판마다 **가운데가 밝고 테두리가 어두운 베개 음영**이 들어 있다(전 파도에서 이미
  "알약·젤리곰"으로 지적된 함정이 바닥에도 있다).
* 쓰러진 기둥이 **말 그대로 직육면체**다. 깨진 단면도, 모서리 치핑도, 발치 잔해도 없다.
* 벽 블록이 전부 같은 크기·같은 줄눈·같은 갓 하이라이트다.
* 이끼가 라임색 점 몇 개로 뿌려져 있어 **고명**처럼 보인다.

---

## 2. 여섯 가지 기법 — "어떻게 싸게"

### 2-1. 트림 시트 — 텍스처 한 장으로 벽·기둥·계단·문틀을 다 입힌다

**무엇인가.** 한 장의 비트맵을 가로 띠 여러 줄로 나누고, 각 띠를 건축 부재 하나에 배정한다.
"Trim sheets are like tiling textures, except that they only tile on one axis and are often used
to texture long pieces of geometry, for example crown molding, but they can be used for much more
when planned well."
([Level Design Book](https://book.leveldesignbook.com/process/env-art/texturing))

Frozenbyte(트라인 시리즈)의 사내 규칙이 제일 구체적이다
([Frozenbyte Wiki](https://wiki.frozenbyte.com/index.php/3D_Asset_Workflow:_Tile_Textures_and_Trimsheets)):

* "The current texel density for environmental Trine assets is **200px/m**" — 1k 텍스처가 5m,
  2k 가 10m 를 덮는다.
* "Plan out your trim sheet ... by dividing a plane into a uniform square grid" ·
  "Keep the segments **divisible by 10**, as it will make UV mapping easier down the line"
* "The main idea is that individual pieces **tile in at least one direction** — vertically or horizontally"
* 용도 판정: 타일 텍스처 = 크고 연속된 면(벽·바닥·지면), 트림 시트 = **반복되는 사각 부재로 된
  모듈 세트**(메모리와 드로우콜을 같이 아낀다), 유니크 텍스처 = 압출·평면으로 안 되는 복잡 형상.

발로란트는 이걸 기본 전략으로 못 박는다: "we primarily use **tiling textures and trim sheets**
on our buildings and large structures", 유니크 텍스처는 "on props when needed" 뿐이다
([The Art of VALORANT Map Environments](https://playvalorant.com/en-us/news/dev/the-art-of-valorant-map-environments/)).

**표준 레이아웃 — 인섬니악의 "Ultimate Trim"(GDC 2015, Sunset Overdrive).**
가로 띠를 **아래로 갈수록 두껍게, 위로 갈수록 얇게** 쌓고 각 띠의 높이를 **두 배씩** 늘린다.
1024px 이면 **512 / 256 / 128 / 64 / 32 / 16** 이다
([Beyond Extent — Trimsheets](https://www.beyondextent.com/deep-dives/trimsheets),
[radiator blog](https://www.blog.radiator.debacle.us/2017/07/bevels-in-video-games.html),
[cgchannel](https://www.cgchannel.com/2019/07/download-justen-lazarros-free-ultimate-trim-texturing-tools/)).
맨 아랫줄은 자투리 조각용으로 남긴다(공식 생성기가 "up to **12 full-width trim segments** and up to
**12 partial-width bottom trim segments**", [80.lv](https://80.lv/articles/ultimate-trim-generator-for-substance)).

트림 시트를 재질별로 여러 장 만들어 두면 UV 를 안 건드리고 재질만 바꿔 변주를 만든다:
"One sheet can be a generic metal trim and the other sheet can have a wood trim, and as long as
they all line up you can just **exchange one material for the other** and create variation without
touching the UVs." ([80.lv](https://80.lv/articles/tiling-textures-in-game-environments))

**왜 싼가 (숫자).**
* "12 assets would result in **36 textures**" 을 "with a trim sheet you could potentially texture all
  of those assets with **3 textures**" ([Beyond Extent](https://www.beyondextent.com/deep-dives/trimsheets))
* "one **2K texture** serving **50 different meshes** uses a fraction of the memory that 50 unique 512px
  textures would" ([propgon](https://propgon.com/en/trim-sheets-3d-optimization-game-art-guide/))
* 실제 출하 예: 트림 시트 한 장의 "**11 unique pieces**" 중 "**4 pieces of brick**" 만으로
  400×400UU 벽돌 벽 전체를 "does not look repetitive at all" 로 만들었다
  ([exp-points](https://www.exp-points.com/vuk-single-material-modular-kit-environment-ue4))

**★분업이 곧 건축 위계다.** 이게 오너 질문("트림 시트로 벽이 상자가 아니게 되는 원리")의 정답이다.

> 벽 **몸통과 바닥은 타일 텍스처**, 트림 시트는 **가로 띠(주춧돌·띠돌·갓돌)와 아치 링과 모서리**.

근거: 모듈 중세 건축을 트림 한 장으로 지은 아티스트가 "**I excluded the brick material from the
trimsheet** since it would be easier to play with tiling and add features on top of it through a shader
instead" ([exp-points](https://www.exp-points.com/wouter-gillioen-the-crossroads)) 라고 적었고,
일반 규칙으로도 "**Bigger surfaces oftentimes go better with tileable textures** ... Most obvious examples
for this are floor parts, but sometimes also parts of walls"
([Beyond Extent](https://www.beyondextent.com/articles/balancing-modularity-and-uniqueness-in-environment-art)) 이다.
즉 **트림은 벽을 대체하지 않는다. 벽에 띠를 두르는 것이다.**

계획법도 일관된다: **평면 색 목업 먼저.** "I created a reference texture using **flat colors** to plan out
the appropriate ratios and size for all the parts"
([80.lv](https://80.lv/articles/005cg-001agt-sanxia-street-1940-modular-approach-trim-sheets-decals)),
그리고 "based on a grid so you can **snap UV shells** to them easily without the need to eyeball"
([80.lv](https://80.lv/articles/arabian-afternoon-working-with-trim-sheets-efficiently)).
실물 치수와 띠 크기가 안 맞을 때 허용 오차는 "usually ... something around **25% up or down**"
([Beyond Extent — texel density](https://www.beyondextent.com/deep-dives/deepdive-texeldensity)).

**★우리 판정: 변형해서 쓴다(가치 큼).**
지금 던전은 벽·기둥·아치·문설주·계단·잔해가 **전부 같은 타일 하나(`dg_wall`)를 UV 4.6m 로**
받고 있다(`blender/s40_dungeon1.py` 의 `WALL_UV_SCALE`, `buf_cut`/`buf_altar`/`buf_stair`/`buf_rubble`
모두 같은 스케일). 이건 트림 시트가 아니라 **트림 없는 벽지**다. 부재마다 다른 띠를 받아야
건축 위계가 생긴다. 우리 빌더는 면을 직접 찍으므로 UV 를 띠에 스냅하는 건 코드 몇 줄이다.
**단, glTF 는 우리가 이미 재질 곱수 계약을 쓰고 있으므로 트림 시트를 새 텍스처로 추가하면
곱수 표에 항목이 는다.** 텍스처 장수를 안 늘리려면 지금 `dg_wall` 을 그대로 **트림 시트로
재설계**하는 편이 낫다(같은 1024², 세로를 5~6 띠로 나눈다).

### 2-2. 반복 깨기 — 타일 + 버텍스 컬러 + 데칼

타일 텍스처의 딜레마는 알려져 있다. "Because tiling textures often must be unspecific and subtle
to hide the tiling, environment artists cannot get the necessary detail into the game environment
with them alone." 그래서 **버텍스 페인팅과 데칼**을 얹는다
([80.lv](https://80.lv/articles/using-tileable-textures-in-game-environments)).

Klevestav(블리자드, 오버워치 환경/텍스처 아티스트)의 모듈 세트 튜토리얼이 셋을 나열한다
([philipk.net](https://www.philipk.net/tutorials/modular_sets/modular_sets.html)):

1. **버텍스 컬러** — "Vertex colors can be a huge help to save both texture memory and break up repetition."
2. **애드온 유닛** — 벽에 얹는 작은 별도 부재.
3. **데칼** — "Decals, such as the letters and numbers here", 특히 오염·풍화용.

그리고 대칭 모듈을 만들어 두면 "this alows me to **rotate the unit 180 degrees** to break tiling."

오버워치 스타일 재현 브레이크다운에서 확인된 실제 관행:
"Overwatch walls usually have **some dirt on top and bottom**" — 벽 재질에 오염 재질을
**버텍스 페인트로** 덧칠한다
([Games Artist, Georg Klein](https://gamesartist.co.uk/creating-an-overwatch-inspired-environment-lisbon-streets-georg-klein/)).

이건 Level Design Book 의 벽 텍스처 설계 규칙과 정확히 같은 말이다:
"Edge detail at the **top and bottom** helps emphasize where the wall meets the ceiling and the floor" ·
"keep the **middle of the wall texture fairly plain**"
([Level Design Book](https://book.leveldesignbook.com/process/env-art/texturing)).

버텍스 컬러 AO 는 **타일 텍스처를 쓰는 메시에 특히 맞는다**는 것이 폴리카운트의 정리다:
타일링 때문에 텍스처에 고유 음영을 못 넣으므로, 텍스처 기반 AO 를 쓰려면 두 번째 UV 와
별도 텍스처가 필요해져 메모리와 버텍스가 는다. 버텍스 AO 는 그 비용이 0 이다. 단점은
**해상도가 메시 밀도에 묶인다**는 것 ([polycount wiki: Ambient occlusion vertex color](http://wiki.polycount.com/wiki/Ambient_occlusion_vertex_color)).

**★가장 반직관적이고 가장 값진 발견 — 베데스다의 실측(스카이림).**

> "Players were quicker to react negatively to **repeated detail elements**, as opposed to broad
> architectural repetition." 플레이어는 "pick up on **repeated clutter first, then the repeated
> architecture**."
> ([Game Developer — Skyrim's Modular Approach to Level Design](https://www.gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design))

**똑같은 벽 모듈은 참아 준다. 그 위에 흩어 놓은 똑같은 소품이 먼저 들킨다.**
그러니 **벽을 고치기 전에 드레싱을 흩어라.** 우리 던전으로 옮기면: 횃불 38자루가 전부 같은
모양·같은 높이·같은 각도로 서 있는 것이 벽 블록이 같은 것보다 더 큰 죄다.

인접 규칙도 같은 결이다: "whenever you have a piece that's highly detailed, that piece **never works
fine visually if you place another piece next to it with the same amount of details**"
([exp-points](https://www.exp-points.com/vuk-single-material-modular-kit-environment-ue4)).

출하된 모듈 성 프로젝트가 반복 깨기를 순위로 적어 뒀다
([80.lv](https://80.lv/articles/001agt-medieval-castle-production-working-with-modular-packs)):

1. **주 모듈의 변종**을 만든다(벽이 주 모듈이면 **부서진 벽**이 변종)
2. 장식물·소품·데칼·**버텍스 페인트**·식생
3. "**Lights and shadows give weight to different parts of the image and break the monotonous look**"
4. 월드 정렬 디테일(위치별 변주)

블록아웃 하나에서 변종을 뽑는 값싼 수치도 있다: "Each blockout model can easily turn into
**3-5 others** with some crushing, stretching and bending"
([80.lv](https://80.lv/articles/technical-tips-for-environment-artists-part-1-001agt-004adk)).

**★우리 판정: 버텍스 컬러는 그대로 됨(이미 파이프라인의 심장이다). 데칼도 됨. 트림 회전도 됨.**
★three.js 한정 공짜 카드: `InstancedMesh` 는 인스턴스별 변환과 **인스턴스별 색**(`setColorAt` /
`instanceColor`)을 드로우콜 한 번에 준다([three.js docs](https://threejs.org/docs/pages/InstancedMesh.html)).
판석·잔해·횃불을 인스턴싱하면 **타일마다 색·밝기 흔들기와 무작위 yaw 가 사실상 공짜**다.
우리 COLOR_0 은 이미 어둠·N·L·높이감쇠·이끼를 곱해 굽고 있다. 여기에 **부재 접합부 AO**와
**블록별 색 변주**를 더하는 것은 순수 이득이다(텍스처 0장, 드로우콜 0, glb 증가 미미).
지금 빠져 있는 것이 정확히 그 둘이다:
* 벽 밑동·기둥 밑동·문설주 옆의 **접지 어둠**(13차에는 있었고 14차에 AMB 0.46 으로 묽어졌다)
* **블록 단위 랜덤 값 변주**(같은 텍스처를 쓰는 벽면끼리 ±5% 밝기 차)

데칼은 우리에게 이미 `FLOOR_POOL`·`FLOOR_SHAFT` 계열로 존재하지만 **전부 빛이다.**
**형태 데칼(금·깨짐·오염)이 한 장도 없다.** 이게 "타일 덩어리" 인상의 큰 원인이다
(1-3 절의 "금이 판석을 무시하고 지나간다"를 우리는 못 하고 있다).

### 2-3. 명암과 AO 를 텍스처에 굽는다 — 라이트 없이 입체를 만든다

이게 우리 파이프라인의 정곡이다. 우리는 실광원이 없고 노멀맵도 없다.
그런데 **롤·오버워치도 지형/정적 면에서는 사실상 같은 처지**다. 방식이 다를 뿐 전부
"미리 구운 값"으로 입체를 만든다.

오버워치는 라이트맵에 **색과 방향**을 같이 굽는다. 오버워치 1 에서 "we generated color and
direction for all light hitting a surface", 오버워치 2 에서 "we now generate **three lighting
directions**, allowing us to vary each of the color channels (red, green, and blue) independently."
그리고 정적 오브젝트에는 **주변 가시성(AO) 데이터**를 따로 굽는다: "data that tells the object
how much of the surrounding environment is visible ... For Overwatch 2, all maps will be generating
this data now."
([Blizzard: Environment States in Overwatch 2](https://overwatch.blizzard.com/en-gb/news/23674944/environment-states-in-overwatch-2-behind-the-scenes-with-the-engineering-team/))

발로란트도 같다. "Lighting is done in an **offline environment**" (Lightmass) 이고, 결정적으로
**"we don't have dynamic shadows in the playable space of the game**, because people playing on
lower quality settings (which usually cut shadows) would miss out on vital information."
([Riot: VALORANT Shaders and Gameplay Clarity](https://www.riotgames.com/en/news/valorant-shaders-and-gameplay-clarity))

**롤이 우리와 정확히 같은 처지고, 같은 답을 쓴다.** 라이엇 공식 기술 글:

> "**Since the main light source does not move, we prebake the shadows of the static meshes into
> their textures.** This gives the artists more control over the look of the map and also helps with
> performance (no need to render shadows from static meshes)."
> ([Riot: A Trip Down the LoL Graphics Pipeline](https://www.riotgames.com/en/news/trip-down-lol-graphics-pipeline))

우리도 광원이 안 움직이고 카메라도 고정 쿼터뷰다. **그림자를 텍스처에 구울 자격이 있다.**

★**그리고 그 구운 빛은 생각보다 훨씬 저해상도다.** 같은 블리자드 글에 실린 라이트맵 도해
(`incoming/refpack_aaa/overwatch/ow_env_9.png` — 왼쪽 최종 화면 · 가운데 라이트맵 UV 차트 ·
오른쪽 패킹된 라이트맵 아틀라스)를 보면, 체커 한 칸이 벽에서 **수십 센티미터**를 덮는다.
즉 오버워치의 구조는

```
   저주파 = 구운 빛 (라이트맵. 아주 성기다)
   고주파 = 알베도 텍스처 (여기에 디테일이 전부 있다)
```

**우리 버텍스 조명이 하는 일이 정확히 저 저주파 층이다.** 버텍스 해상도가 낮다는 것은
결함이 아니라 **같은 구조**다. 문제는 우리가 고주파 층(알베도)에 형태를 안 그려 넣은 것이다.
(이 문단은 공식 이미지를 눈으로 읽은 것이지 블리자드의 진술이 아니다.)

#### 유일하게 숫자가 공개된 레시피 — 밸브 Dota 2 공식 문서

핸드페인트 업계에서 **실제 불투명도가 적힌 유일한 스튜디오 문서**다
([Valve: Dota 2 Workshop — Color Texture Light Baking](https://help.steampowered.com/en/faqs/view/60E5-5E13-712C-5315)).
동기부터 우리와 똑같다:

> "Dota 2's in-game lighting is quite subtle and as a result we tend to lose a lot of the sculptural
> detail in the character's normal maps. **We offset this by baking - or painting - the light into
> the color texture.**"

레이어 순서와 밸브가 적어 둔 수치:

| 단계 | 무엇 | 수치 |
|---|---|---|
| 1 | 베이스 색 깔기 | |
| 2 | AO 를 베이스 위에 곱하기 | **불투명도 80%** |
| 3 | 포인트 라이트 패스(흰 점광 몇 개, **그림자 끄고**, AO 없이) | |
| 4 | 그 위에서 **위→아래 밝음→어두움 기울기**를 잡는다 | |
| 5 | 그림자를 클램프 — 베이스가 불필요하게 안 어두워지게 | **RGB 90/90/90 스크린 레이어 85%** |
| 6 | 포인트 라이트 그룹 블렌딩 | **소프트라이트 100%** ("이게 언더페인팅") |
| 7 | 컬러 그룹을 그 위에 | **오버레이 80%** |
| 8 | 명부·암부를 따로 잡기 | 컬러 그룹 복제 **lighten 30%** + 다시 복제 **darken 50%** |
| 9 | 큰 그래픽 무늬(가독성용) | **normal 80%** |
| 10 | 마지막에 값 기울기 개선 + 채도 조정 | |

★7~8 단계의 취지가 우리 ACES 사슬과 정확히 같은 문제의식이다:
"Layers with certain blend modes can **blow out the palette into unusual colors**, so it's worth
**clamping shadows and highlights to avoid excessive contrast**."

#### 빛 방향은 "위". 그런데 타일에는 예외가 있다

* "**The usual light source for hand-painted textures is a top one**" ·
  "besides an overall top-down gradient, I also added **gradients within the faces** to better define
  the light source" ([80.lv, Thais Del Rey — WoW 디오라마](https://80.lv/articles/002mrs-crafting-a-wow-diorama-textures-painting-lighting))
  → **큰 기울기 한 장 + 판마다 작은 기울기**, 두 겹이다.
* 밸브도 "top-to-bottom, light-to-dark gradient".
* 좌상단이 아니라 **정위**인 이유: 에셋이 회전하기 때문이다. 좌우가 들어가면 회전 순간 깨진다.
* ★**예외(우리에게 중요):** WoW 는 **타일 텍스처에는 방향성을 일부러 약하게** 둔다.
  "lighting is usually baked into the diffuse, although **there's no specific lighting direction in WoW
  neither does it have a very obvious baked AO**"
  ([polycount](https://polycount.com/discussion/116039/trying-to-nail-the-feel-of-hand-painted-environment)).
  타일은 회전·천장·경사면에 붙으므로 강한 정위 광이 들어가면 붙는 순간 틀린다.
  깊이는 **줄눈의 국소 AO** 가 만든다.
* ★그런데 같은 스레드가 우리 같은 경우의 면제를 준다: "If you are making ... **a fixed camera,
  ie. side scroller/topdown** where your lighting will always be seen from one direction you could get
  away with a lot more, being able to **paint your lighting all in straight on your diffuse**"(Owl).
  **우리는 yaw 0 고정 쿼터뷰다. 면제 대상이다.**

#### 스튜디오의 진짜 순서는 "값 먼저, 색 나중"

라이엇 리드 캐릭터 아티스트 Yekaterina Bourykina 의 강의 목차가 그대로 순서다
([ArtStation Learning](https://www.artstation.com/learning/courses/mj/hand-painting-textures-prop)):

```
맵 베이크 → ★그레이스케일로 값 그리기 → 그라디언트 맵으로 색 입히기 → 페인팅 → 지오 교체 → 다시 페인팅
```

즉 **플랫 컬러부터 깔고 그 위에 명암을 얹는 게 아니라, 흑백으로 명암을 완성한 뒤 색을 입힌다.**
오버워치 재현 워크플로도 같다: "working in greyscale going from **big to small shapes**".

#### 돌 텍스처를 그리는 3단계 (폴리카운트 정평 페인트오버)

([polycount: how to hand paint a rock/cave texture](https://polycount.com/discussion/89131/how-to-hand-paint-a-rock-cave-texture), Wells)

> **1단계 — 선을 스케치한다.** "get reference, see how rocks are formed, find your shapes ...
> they feel **jagged and noisy and don't flow. no rhythm.** try to avoid a lot of cracks that run
> counter to the rest of the rocks and **end abruptly**."
> **2단계 — 큰 형태를 먼저 정한다.** "**establish the rhythm of your texture** ... grab a light color,
> grab a dark color, and go nuts. **blur your eyes, do the forms read?**"
> **3단계 — 그제야 칠한다.** "define the forms you just created."

같은 스레드의 실패 진단이 우리 바닥에 그대로 해당한다:
"The lack of depth comes from the color, **the strokes aren't following the lines and contours** ...
Some of them are even 'floating' on the cracks."

**★우리 판정: 그대로 됨. 단 지금은 절반만 하고 있다.**
우리는 ③(N·L)과 위→아래 기울기 일부(높이 감쇠)를 **버텍스**에서 한다. 그런데 **틈의 AO 와
에지 하이라이트를 텍스처에 안 굽고 있다.** 절차 벽 텍스처에 갓 하이라이트(`WALL_HI 1.24`)와
밑동 그늘(`WALL_LO 0.66`)이 있긴 하지만 **블록마다 똑같이** 들어간다.

★그게 정확히 아르네 니클라스 얀손이 이름 붙인 실패다:
"**Problem: To go shadow - midtone - highlight on all shapes, regardless of location and angle of
the shape.** Solution: ... **Equally lit minor shapes flattens the painting and makes it hard to make
out the important major shapes.**"
([Arne, art tutorial](https://web.archive.org/web/20211212075542/http://androidarts.com/art_tut.htm))
모든 블록에 똑같은 3값 처리를 하면 **작은 형태들이 서로를 지워서 큰 형태가 안 읽힌다.**

### 2-4. 텍셀 밀도 위계 — 시선 가는 데만 진하게

업계 표준 목표치(문헌 종합):

| 카테고리 | 텍셀 밀도 |
|---|---|
| 모바일 / VR | 256 ~ 512 px/m |
| 3인칭 60fps | 512 ~ 1024 px/m |
| 1인칭 | 1024 ~ 2048 px/m |
| 시네마틱 | 2048 ~ 4096 px/m |

([StraySpark texture resolution guide](https://www.strayspark.studio/blog/texture-resolution-guide-games-512-1k-2k-4k))
그리고 결정 규칙은 화면 커버리지다: "Estimate how many screen pixels the object's largest face
will occupy at the closest typical camera distance", 목표는 "**at least 1:1 texel-to-pixel ratio**
at that distance." 트라인은 앞서 본 대로 **200 px/m** 한 값으로 통일해서 쓴다.

★**카메라 종류별 서열이 명시돼 있고, 탑다운이 제일 낮다.**
1인칭이 최고, 3인칭이 조금 낮고(대신 에셋 밀도로 보상), **탑다운은 "lowest density"** —
"usually the furthest away from the camera"
([Beyond Extent — Texel Density](https://www.beyondextent.com/deep-dives/deepdive-texeldensity)).
**아낀 예산은 텍스처가 아니라 실루엣과 지오메트리에 쓰라는 뜻이다.**

**★우리 판정: 우리는 이미 과하게 쓰고 있다. 해상도를 올릴 이유가 전혀 없다.**

```
바닥  1024 px / FLOOR_UV_SCALE 5.0 m = 205 px/m
벽    1024 px / WALL_UV_SCALE  4.6 m = 223 px/m
화면  1280 px 에 바닥 약 20 m         =  64 px/m
```

**텍셀 : 화면픽셀 = 3.2 : 1.** 1:1 이면 충분한데 3배를 쓰고 있다. 다시 말해
**우리 텍스처의 3px 미만 디테일은 화면에서 1px 도 못 채우고 지글거림만 남긴다.**

여기서 오버워치의 유명한 실전 지침이 정확히 우리 얘기가 된다.
텍스처 해상도를 **절반으로 줄였더니** 오버워치 화풍에 더 맞았고, 이유는
"higher resolution was **drawing too much attention and importance to the object**"
([80.lv, Overwatch HQ 브레이크다운](https://80.lv/articles/overwatch-hq-creating-a-game-level-for-portfolio)).

그리고 발로란트 쪽 원칙도 같은 방향이다: "environments should therefore be **as cheap as possible**.
A small expensive adjustment here can cause huge overall framerate costs."
([Riot](https://www.riotgames.com/en/news/valorant-shaders-and-gameplay-clarity))

**결론: 1024 를 유지하되 그 안에 그리는 형상의 최소 크기를 키운다.**
화면 64 px/m 에서 눈에 읽히려면 형상이 최소 6~8 화면픽셀 = **0.10 ~ 0.13 m** 여야 한다.
텍스처 좌표로는 1024/5.0 × 0.11 ≈ **23 px**. 그보다 작은 붓질은 전부 지글거림이다.

### 2-5. 노멀맵 없이 요철을 그린다

오버워치의 핵심 트릭 하나가 **크게 구운 베벨**이다.
"The use of **big baked-in bevels** really stood out to me" — 이 칠해 넣은 베벨이 기하 복잡도 없이
모서리를 부드럽게 만들고 "a dramatic **rim light feeling for completely free**" 를 준다.
그리고 형태 쪽 규칙이 오너의 불평과 글자 그대로 겹친다:

> "tried to avoid sharp 90 degree angles, using either a corner piece or an actual bevel
> **to prevent a level feeling like a series of boxes**."

([80.lv, Technical and Visual Analysis of Overwatch](https://80.lv/articles/overwatch-technical-overview))

실제로 오버워치 재현 작업자는 이걸 기하로도 밀어붙인다: "push curves and bevels in Maya to
**ridiculous degrees** to get them to feel right when lit in game"
([80.lv Overwatch HQ](https://80.lv/articles/overwatch-hq-creating-a-game-level-for-portfolio)).

텍스처 우선순위(오버워치)도 명시돼 있다:

> **"Color, hand-touched painted detail, normal map, metalness, then finally roughness/gloss detail."**

**컬러가 1순위, 손으로 찍은 디테일이 2순위, 노멀맵은 3순위다.**
우리에게 노멀맵이 없다는 사실은 이 위계에서 **3순위를 못 쓴다는 뜻일 뿐**이다. 1·2순위는
전부 쓸 수 있고 그게 이 화풍의 대부분을 만든다. 같은 소스: "add hand-touched variation and detail
into the texture **whenever you can** to get that hand-crafted feel."

그리고 오버워치가 면에 얹는 언어는 데칼이다: "**Sunken screws, rectangular cutout bites, vents,
seams, and metal grommets** all go on top." (우리 던전이면 나사가 아니라 쐐기 자국·정 자국·
파인 홈·물때 줄·이끼 얼룩이 그 자리다.)

Substance 계열 스타일라이즈드 작업자의 순서도 같은 결론이다: 하이트맵 먼저 → 컬러 →
그레이스케일 변환으로 러프니스 순서로 가고, 근본 방법론은 "working in greyscale going from
**big to small shapes**" 다. 바닥 판석은 "edge detection → beveling → slope blur (using **blurred
clouds** for non-noisy results) → tile generation for **size/offset variation**" 로 만든다
([80.lv 텍스처링 방법론](https://80.lv/articles/overwatch-fan-art-environment-approach-to-texturing)).
★"blurred clouds 로 슬로프 블러를 해야 노이즈가 안 낀다"는 대목은 우리가 이미 밟은 함정
("값잡음 등고선은 돌의 금이 아니라 지렁이", 14차 LOG)의 정답이다.

**★우리 판정: 전부 그대로 됨. 이게 우리가 제일 안 하고 있는 것이다.**

### 2-6. 재질별 붓 언어와 "클린한데 풍부한"의 정체

발로란트 아트 디렉터 Moby Francke 가 화풍에 붙인 이름은 "**illustrative visual design**"이고,
설명은 "**clean lines, tidy gradients, and pleasing angles**" 다
([Inverse 인터뷰](https://www.inverse.com/gaming/valorant-art-style-interview-moby-francke)).
오너가 말한 "깔끔하면서 미감있고"의 정확한 번역이 이 문장이다.

★**블리자드가 실수로 공개한 실제 수치.** 오버워치 2 기술 글에 실린 스크린샷에
`Environment States Debugger` 창이 열려 있어 노출 설정이 그대로 찍혔다
(`incoming/refpack_aaa/overwatch/ow_env_4.png`,
[출처](https://overwatch.blizzard.com/en-gb/news/23674944/environment-states-in-overwatch-2-behind-the-scenes-with-the-engineering-team/)):

```
  m_exposureValueClampUpper   1.200000     ← 자동노출 상한
  m_exposureValueClampLower   0.900000     ← 자동노출 하한   (폭이 겨우 1.33배)
  m_lumaTargetMax             0.700000     ← 화면 휘도 목표 상한
  m_lumaTargetMin             0.000000
  m_exposureCompensationMax  -1.500000
  m_exposureCompensationMin  -2.000000
  m_histogramMaxLuminance     4.000000
  m_exposureSpeed             0.050000
```

**오버워치는 자동노출을 0.9~1.2 안에 가둔다.** 밝기를 자유롭게 흔들지 않고, 화면 휘도 목표를
0.70 로 못 박아 놓는다. "clean" 은 후처리로 만들어지는 게 아니라 **값 폭을 조여서** 나온다.
우리 ACES 계약이 하는 일과 같은 종류의 일이고, 우리 14차 화면(V 폭 0.200~0.886)은 이 정신의 반대다.

라이엇이 맵 아트에서 실제로 지키는 규칙(공식):

* "we make sure that our materials are **similar in value** and there isn't too much contrast or darkness"
* "we make sure that they **aren't too dark**, especially in interior spaces"
* 색은 길찾기에 쓴다 — "colors as a way to help distinguish certain areas and structures"
* "our artist goals ... is always **subordinate to gameplay clarity**"

([The Art of VALORANT Map Environments](https://playvalorant.com/en-us/news/dev/the-art-of-valorant-map-environments/))

재질 구분의 기준은 "50m 밖에서도 나무는 나무로 보이는가"다: "A wood texture should still look
like wood from 50 meters away, and a shiny metal texture should feel different from a shiny plastic
texture." 그리고 채도 상한이 명시돼 있다: "**Avoid deeply saturated colors, give space for lighting**
... if you make a very red texture, it can't get much redder." 그라디언트는
"smooth (not noisy) but still avoid flatness (there is hierarchy)"
([Level Design Book](https://book.leveldesignbook.com/process/env-art)).

같은 책이 오버워치 Castillo 를 예로 들며 적은 값 규칙이 우리 벽·바닥 설계와 직결된다:
"Notice how the **ground is generally darker than the surrounding walls**;
**wall textures are plain with minimal noisy details.**"

색 배분에는 널리 쓰이는 70/30 규칙이 있다: "Try and have a material that covers a **70% or more**
of the environment and then a darker (or brighter) secondary color that is covers **30% or less**",
그 위에 "primary, secondary, tertiary" 로 악센트를 얹는다
([80.lv, Alex Senechal](https://80.lv/articles/tiling-textures-in-game-environments)).

노이즈 총량에 대한 블리자드 쪽 경고도 분명하다(Klevestav):
"If we add **too much visual noise and clutter** it becomes very difficult to navigate and see other
players, if there **isn't enough detail** scale will become difficult to judge" ·
"it is very easy to go overboard with detail where it is not needed ... often doesn't lead to an
overall more pleasing image" · 시각적 관심은 "**at eye level of players**" 에 몰아라
([ArchDaily 인터뷰](https://www.archdaily.com/938441/blizzard-entertainments-philip-klevestav-on-designing-built-environments-in-video-games)).

**★우리 판정: "벽은 쉬고 바닥이 일한다"는 우리 카메라에 맞게 뒤집어야 한다.**
발로란트·오버워치는 1인칭/3인칭이라 "눈높이"가 벽이다. 우리는 **고정 쿼터뷰(pitch 0.86)** 라
화면 면적의 대부분이 바닥이고, 벽은 화면 위쪽에 얇게 눕는다.
따라서 **디테일은 바닥에, 벽은 쉬게** 한다 — 이건 Castillo 규칙(바닥이 벽보다 어둡다)과
방향은 반대지만 원리(시선 가는 면에 정보, 나머지는 조용히)는 같다.
다만 값 규칙은 우리 13차 자기검증 8번(바닥 화면 평균 > 벽)이 이미 반대로 못 박아 뒀고,
14차 실측도 바닥/벽 = 1.40배다. **바닥이 밝고 벽이 어두운 우리 규칙은 유지한다**
(쿼터뷰에서 벽이 밝으면 화면 위쪽이 뜬다).

---

## 3. 형태 언어 — "직육면체 탈출"

여기부터는 텍스처가 아니라 **모양**이다. 오너의 "직육면체들 같아"는 텍스처만으로는 못 고친다.

### 3-0. 실제 석공 치수 — 여기가 숫자가 제일 많이 나온 자리다

**① 벽을 기울인다 (batter). 쿼터뷰에서 제일 값싸고 제일 크게 먹히는 한 수.**
"A **1:6 batter** means that for every 6" of height the wall gets narrower 1" on each side.
The typical range for batter is from **1:6 to 1:10**"
([Masonry Magazine — 건식 석벽 구조 원칙](https://www.masonrymagazine.com/blog/2018/11/01/dry-stone-walls-principles-of-structurally-sound-construction/)).
각도로는 수직에서 **5° ~ 9.5°** ([Wikipedia: Batter](https://en.wikipedia.org/wiki/Batter_(walls))).
성벽의 경사진 주춧돌은 굴착 방해용이자 "provide[d] a **ricochet surface** for objects dropped from
machicolations" 였다. **수직 직육면체가 아니게 되는 가장 싼 방법이다** — 버텍스 y 에 비례해 x·z 를
줄이면 삼각형이 한 장도 안 는다.

**② 갓돌·처마 띠는 생각보다 커야 한다.** 고전 비례에서 엔타블러처는 아래 기둥 높이의 **약 1/4** 이다.
즉 관 씌우는 띠 뭉치가 벽 높이의 **20~25%** 를 먹어도 정상이다. 게임 벽은 거의 항상 이걸 너무 얇게 만든다.
돌 코니스 돌출은 "about **150mm**" ([underoneroof.scot](https://underoneroof.scot/external-stone-wall-features/)).

**③ 코벨(내밀기)의 유일한 기하 규칙:** 각 단의 내밀기는 "**never be greater than 1/3 of its bearing
on the course below**" ([chestofbooks](https://chestofbooks.com/architecture/Building-Construction-3-1/Parts-Of-Walls.html)).
그래서 실제 코벨 테이블은 계단식이다. 한 번에 쑥 내밀면 가짜로 보인다.

**④ 붙임기둥 간격 — 비트루비우스가 준 숫자.** 기둥 지름 D 기준
pycnostyle 1.5D · systyle 2D · **eustyle 2.25D("가장 좋은 비례")** · diastyle 3D.
그리고 하드 리밋: "when columns are placed **three column-diameters or more apart, stone
architraves break**" ([Wikipedia: Intercolumniation](https://en.wikipedia.org/wiki/Intercolumniation)).
eustyle 은 **가운데 칸을 더 넓게** 둔다.
→ 붙임기둥 폭이 W 면 간격은 **1.5W~3W, 기본 2.25W**, 가운데 칸만 넓힌다.

**⑤ 리듬은 균등하지 말 것.** 베네치아 파사드는 A-B-A · A-A · A-A-B-A-A 로 동시에 읽히고
"a plain **A-A-A pattern**" 이 아니다 — "**All of these readings are there at the same time and it lends
a kind of tension to the facade**" ([M Gerwing Architects](https://mgerwingarch.com/m-gerwing/2011/09/08/facade-rhythm-venice)).
지금 우리 붙임기둥은 "세 칸에 하나" 로 완전 균등이다(13차B).

**⑥ 모서리에는 quoin 을 넣는다.** 모서리에만 더 크고 더 잘 다듬은 돌을 쓰고,
"long and short quoining ... places long stone blocks with their lengths oriented **vertically**,
between smaller ones that are laid **flat**". 효과는 "**imply strength, permanence, and expense**"
([Wikipedia: Quoin](https://en.wikipedia.org/wiki/Quoin)).
격자로 지은 던전에서 **모서리가 압출 티가 제일 많이 나는 자리**라 값이 크다.

**⑦ 갓돌은 세워서 얹는다.** 아래 모든 단과 **90도 다른 방향**이라 쿼터뷰에서 아주 잘 읽히고 공짜다.
덮개 돌출은 벽면에서 **1~2인치**.

**⑧ 아치는 곡선으로 파지 말고 블록으로 쌓는다.**
impost(받침돌, 벽이 여기서 끝난다) → springing line → springer → voussoirs → keystone
([Wikipedia: Arch](https://en.wikipedia.org/wiki/Arch)).
★**impost 를 살짝 내밀어라.** "지어진 것"으로 읽히게 하는 디테일이 그 돌출이다.

**⑨ 돌 놓는 방향 — 대부분의 모델러가 거꾸로 한다.**
> "**Set all the stones so their length goes into the wall, not along it.**"
> "**The front face of the stone ... should NOT be the largest face.**"
> ([Masonry Magazine](https://www.masonrymagazine.com/blog/2018/11/01/dry-stone-walls-principles-of-structurally-sound-construction/) ·
> [The Stone Trust](https://thestonetrust.org/polygonal-masonry/))

긴 돌을 면 방향으로 눕히면 **긴 가로줄**이 생기고 그게 다시 격자를 만든다.
그리고 쌓기 규칙은 "**one over two, two over one**" — 각 돌이 아래 단의 줄눈을 걸치고 양옆 두 돌에 앉는다.

**⑩ 돌 크기 비율:** 무규칙 ashlar 실측 길이 5.5"~20.5" · 높이 2.25"~8".
가로세로비 **0.7:1 ~ 2.6:1**, 최장/최단 약 **3.7배**
([dimensions.com](https://www.dimensions.com/element/stone-masonry-random-uncoursed-ashlar)).
**2.6:1 을 넘으면 돌이 아니라 벽돌로 읽힌다.**

**⑪ 큰 돌 먼저, 작은 돌로 메운다.** 큰 돌을 다 놓은 다음 남는 틈을 작은 돌이 채우는 것이지,
크기 하나의 분포에서 전부 뽑는 게 아니다. 그리고 **아래가 크고 위로 갈수록 작아진다.**

### 3-1. 근거로 확인된 규칙

* **90도 각을 없앤다.** 코너 피스나 실제 베벨로. 안 그러면 "a series of boxes"
  ([80.lv Overwatch](https://80.lv/articles/overwatch-technical-overview)).
* **벽 텍스처는 위아래에 에지 디테일, 가운데는 밋밋하게.** 이게 벽이 바닥·천장과 만나는
  자리를 강조한다 ([Level Design Book](https://book.leveldesignbook.com/process/env-art/texturing)).
* **모듈이 안 맞으면 덮어라.** "just cover the mess!" — 교차부에 물건을 얹는다
  ([Level Design Book](https://book.leveldesignbook.com/process/env-art)).
* **세트 드레싱은 프랙탈로.** "duplication, shrinking, rotating, and slightly offsetting ...
  repeated ... in an **asymmetrical fractal structure**" (같은 소스).
* **대칭 모듈은 180도 회전으로 반복을 깬다** ([philipk.net](https://www.philipk.net/tutorials/modular_sets/modular_sets.html)).
* **큰 것부터.** "START BIG, and save smaller details for later art passes. Define your basic shapes
  and massing, color palette, and main themes first" ([Level Design Book](https://book.leveldesignbook.com/process/env-art)).
* **베벨이 곧 돈이다.** "bevels, or any kind of detailed edges, are basically **what make a 3D game world
  look expensive and high poly**" · "Bevels (along with lighting design) help us **track the contours**
  of our game worlds" ([radiator blog](https://www.blog.radiator.debacle.us/2017/07/bevels-in-video-games.html)).
  ★우리는 노멀맵이 없으므로 **진짜 폴리곤 챔퍼**여야 한다.
* **디테일은 뭉치고 빈 데를 남긴다.** "There is a tendency to go overboard with **wall to wall detail** ...
  nothing becomes the focus and in turn, nothing stands out." 처방은 "**Clumping assets and creating
  negative space**" ([80.lv, Anthony Vaccaro](https://80.lv/articles/environment-art-tips-from-anthony-vaccaro)).
  같은 글: "**If the main shapes are not striking and compelling, no matter how much extra detail you
  throw on it, it will still fall flat.**"
* **3층 위계는 "1-2-3".** "Make sure that your silhouettes have **large shape, medium shape and
  small detail shapes. 1-2-3**"
  ([World of Level Design](https://www.worldofleveldesign.com/categories/game_environments_design/silhouette-design-game-environments.php)).
  조각 쪽 판본: "**the primary and secondary forms are the most important. The tertiary forms are just
  icing on the cake and cannot make a bad sculpture good.**"
* **70/30.** 큰 형태를 둘로 쪼갤 땐 50:50 이 아니라 **70:30** 이 보기 좋고, 3차 디테일은 2차의 **30%** 크기로
  ([Neil Blevins — Primary, Secondary, and Tertiary Shapes](http://www.neilblevins.com/art_lessons/composition_primary_secondary_and_tertiary_shapes/composition_primary_secondary_and_tertiary_shapes.htm)).
  같은 글의 경고가 우리 벽 그대로다: "**huge blocks of small repeating patterns** ... This does not provide
  the eye any spot to rest ... have **several areas of detail, and several areas of no detail**."
  워프레임 공식 아트 가이드도 같은 말을 "각 층에서 형태를 **2 대 1** 로 균형 잡아라 ·
  **Group your details in focal areas and leave other areas more open for the eye to rest**" 로 적는다
  ([Warframe TennoGen Art Guide](https://www.warframe.com/en/steamworkshop/basic-art-guide)).
* **★실루엣 자가진단.** "fill in an object or a building with **black and duplicate it dozens of times**",
  그리고 "Does this stand out? Does it pop from the page?" (World of Level Design).
  **우리 벽 블록 하나를 검게 칠해 30장 늘어놓고 보면 답이 즉시 나온다.**

### 3-1b. 판석 포장 — 격자로 안 읽히게 하는 실제 배합비

상업용 석재는 **크기 배합 퍼센트가 공표돼 있다**
([Vetter Stone 패턴표](https://www.vetterstone.com/products/patterns/)):

| 배합 | 분포 |
|---|---|
| 3-Height Random Ashlar (honed) | **15% / 50% / 35%** (3⅝" · 7⅝" · 11⅝"), 줄눈 3/8" |
| 4-Height Random Ashlar | 15% / 40% / 35% / 10% |
| 3-Height Random Ashlar (split) | 20% / 50% / 30% |
| 2-Height Random Ashlar | 40% / 60% |

**모양이 일정하다: 가운데 크기가 40~52% 로 지배하고, 큰 것이 30~35%, 작은 것이 15~20%.**
균등 분포가 아니다. 포장재도 3·5·6·9종 범위로 팔리고, 5종은 600×600 / 600×450 / 600×300 /
450×450 / 300×300 mm 다([pavingexpert](https://www.pavingexpert.com/random01)).
★**모든 크기가 한 기준 모듈의 정수배다**(300mm 격자에 150mm 배수). 즉 **격자를 버릴 필요가 없다.
칸마다 사각형 한 장을 찍는 짓을 그만두면 된다.**

**절대 규칙 둘**(같은 소스):
1. "**Never have four corners meeting**" — 네 모서리가 한 점에서 만나면 안 된다
2. "**Never have any joint running for more than about 3 metres**" — 줄눈이 3m 넘게 이어지면 안 된다

줄눈 폭은 "Allow **10-12mm for jointing**"(600mm 돌 기준 **1.7~2%**) 이고
"the joint width will have to **vary occasionally**".

**우리 바닥이 왜 격자로 읽히는지 이름이 있다: stack bond.** "all vertical joints aligned
**create a grid pattern in appearance**"
([Bowman](https://www.bowmancc.com/articles/construction-knowledge-masonry-series-what-is-a-running-bond-vs-a-stack-bond-pattern)).
running bond 는 반 칸, 1/3 bond 는 1/3 칸을 밀어 놓는다.

**파손은 슬라이더가 아니라 등급이다**
([80.lv 석재 바닥 머티리얼](https://80.lv/articles/creating-a-stone-floor-material-with-substance-3d-designer-scanned-atlases-assets)):
* "**Partial damage seems more realistic than all tiles breaking.**"
* "If **all sides** of the tile are destroyed, it will look too complicated and messy.
  Adding a partially destroyed representation **only to the corners** of the tile will make it seem more realistic."
* "Destroyed tiles are completely broken down into small pieces, and relatively **undamaged tiles are
  only slightly chipped at the corners**."
* "If all objects on the texture have a **similar thickness** to each other, a texture that gives an
  awkward and simple feel is more likely to be born." ← 두께도 흩어야 한다

**높이 차와 줄눈 함몰.** 새로 깐 바닥의 단차 허용은 1mm, 2~3mm 면 이미 걸림턱이다.
실제 건식 판석은 두께 1.5~2.5" 에 바닥 고르기 편차가 0.5~2" 다.
즉 **돌 폭의 0.2% 는 새 것, 5~10% 는 수백 년 내려앉은 것**으로 읽힌다.
줄눈은 돌 윗면보다 "**about 1/4″ recessed**" 여야 한다
([devineescapes](https://www.devineescapes.com/flagstone-what-to-use-sand-cement-or-gravel/)).
★**위에서 내리쬐는 빛에서 돌을 서로 떼어 놓는 것이 바로 이 함몰이다.**

**줄눈 채움은 높이로 결정한다.** 돌 윗면 평면보다 아래인 모든 곳이 흙·자갈·이끼가 된다
([80.lv](https://80.lv/articles/making-a-customizable-flagstone-material-in-substance-designer)).
대비가 손잡이다 — 같은 색 줄눈이면 "less noticeable", 어두운 줄눈이면
"**the shape of each individual slab more visible**"
([Landscaping Network](https://www.landscapingnetwork.com/flagstone/joints.html)).

**포장 가장자리를 녹이는 법.** "The primary walking surface should consist of **larger flagstones.
Smaller flagstone pieces can be used to create smoother transitions along irregular edges**"
([APC](https://apc.us.com/insights/diy-flagstone-pathways-combining-gravel-and-stone-for-a-natural-look/)).
→ 가장자리를 **작은 돌 띠**로 마감하고, 그 바깥에 격자를 벗어난 낱개 조각을 밀도를 줄이며 흩는다.
**격자를 벗어나도 되는 유일한 돌이 이 가장자리 조각이다.**

**닳음과 풍화는 절대 균일하게 넣지 않는다.** 볼록한 모서리와 코너에 몰리고,
"**Adding a Noise Texture multiplied against the curvature mask creates patches where wear is heavier
or lighter**", 먼지는 윗면(Z 노멀 0.3~1.0)과 틈에, 얼룩은 아래로 흐른다
([StraySpark](https://www.strayspark.studio/blog/procedural-weathering-blender-geometry-nodes)).
닳은 길은 저주파 마스크 하나로 **광택을 주고 · 높이차를 눌러 평평하게 하고 · 줄눈 이끼를 지운다.**
안 닳은 구석과의 대비가 곧 그림이다.

### 3-2. 모듈 세트 관례 (참고)

* **발자국(footprint)은 서로의 배수여야 한다.** "A 512x512x512 room will always tile nicely with a
  256x256x256 hallway, but a **384x384x384 room will eventually create gaps**"
  ([Game Developer — Skyrim](https://www.gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design)).
  스냅은 발자국의 **절반**. 우리 칸 2.0m 은 이미 이 조건을 만족한다.
* **원점은 발자국 바운딩박스 한가운데**에 둬야 조각이 자유롭게 회전한다
  ([ianlondon](https://ianlondon.github.io/posts/modular-level-kit-geometry/)).
* **안쪽 모서리는 별도 조각이어야 한다** — 벽 두께 때문에 전폭 벽으로는 자기 자신과 겹친다.
  **바깥 모서리는 베벨·캡이 필요**하다(같은 소스). 우리 벽이 두 칸(4.0m) 두께라 정확히 이 문제가 있다.
* **키트 만드는 순서:** 폴아웃4 GDC 는 "**Utilitarian Core → Variants → Hero Pieces**" 로 적었고,
  같은 발표에서 방 하나를 **20 오브젝트에서 123 오브젝트로 쪼갠** 사례를 든다
  ([GDC 2016, Burgess](https://archive.org/stream/GDC2016Burgess/GDC2016-Burgess_djvu.txt)).
  같은 발표의 벽 재질 변종 8종은 "**only change textures, not architecture**" 다.
* **격자를 벗어나도 되는 곳.** "**Deviate from the grid where possible**", 작은 부재는
  "ignore grid snapping completely"
  ([Beyond Extent](https://www.beyondextent.com/articles/balancing-modularity-and-uniqueness-in-environment-art)).
  스카이림의 답은 **shell-based building**: 표준 키트로 뼈대를 짓고 그 위에
  "**layer in freely placed walls, pillars and balconies to break up the play space in an organic way**".
* 아이소메트릭 특유의 함정: 격자가 "**too small then you can see very clearly where the edges of the
  grid-spaces are and it ruins the illusion of an organic level**", 그리고 "the camera having a
  **narrow FOV and being very zoomed out** is the major contributor to the vertical and flat look"
  ([80.lv](https://80.lv/articles/verticality-in-isometric-level-design)).
  ★우리 카메라(pitch 0.86 · dist 24 · yaw 0)가 정확히 그 조건이다.

---

## 4. 부록 A — 색과 무드 (오너 지시로 비중을 줄임)

색 모사가 목적이 아니라고 정정 지시가 왔으므로 요약만 남긴다.

### 나 혼자만 레벨업

**검증 주의:** A-1 미술감독·색채설계의 공개 인터뷰는 존재하지 않는다. 영어권에 도는
"art director interview: 팔레트는 노랑과 파랑" 주장은 출처 불명이라 **버렸다.**
아래는 (a) 웹툰 채색가 본인, (b) 일본 촬영(컴포지팅) 실무자의 공개 레시피, (c) 분석가 순으로 신뢰도를 매긴 것이다.

* **어둠이 무채색이 아니라 남보라다.** 던전에 들어가면 팔레트가 "the cold, oppressive purples
  and blues of the gates" 로 바뀐다는 것이 분석가 정리
  ([skeptive](https://skeptive.com/why-solo-leveling-manga-colored-versions-arent-actually-manga-1rva)).
  실무 수치로는 횃불 어둠 장면 배경 그라디언트가 **#01020E → #15274E**
  ([note.com 촬영 해설](https://note.com/taka2composite/n/n2021970f01ce)).
  캐릭터 공식 스와치의 "검정"조차 `#18171D` 로 보라 기운이다.
* **한국 웹툰 채색 관행(창작자 발언):** 그림자는 곱하기 레이어에 "채도가 낮은 보라색, 회색 등으로"
  ([CLIP STUDIO TIPS](https://tips.clip-studio.com/ko-kr/articles/10550)).
* **림라이트는 어두운 쪽일수록 세게.** 촬영 레시피가 "暗部ほど強く光の影響をいれるため"
  로 휘도 마스크를 건다. 그리고 light wrap 은 **가산 금지**, 비교(밝게)/스크린으로 합성해야
  안 뜬다(같은 소스). 색은 찬 어둠에 대한 보색인 주황 계열(#FF7519 등).
* **셀 음영의 단계는 둘.** 곱하기 한 장에 한 색으로 솔리드, 그 뒤 스크린·소프트라이트·오버레이로
  풍부하게. 단계를 늘려서 깊이를 만들지 않는다(CLIP STUDIO TIPS).
* ★**디테일은 표면 잡음이 아니라 갈라진 자리에만.** 바위는 중간톤 → 하이라이트 → 그림자로 쌓고,
  하드 브러시는 "岩の割れている部分を表現するために"(깨진 부분을 표현하려고)만 쓴다
  ([palmie](https://www.palmie.jp/lessons/82)). 그리고
  "**반사광이 여러 각도에서 들어오므로 새까만 부분에도 빛이 닿는 것을 표현해야 한다**"(같은 소스)
  — 셀 던전의 어둠이 구멍이 안 되는 규칙이다.
* **마력 발광은 돌을 물들인다.** 역제곱 감쇠 + 실루엣을 살짝 넘어 번지는 light wrap.
  ([note.com](https://note.com/taka2composite/n/n2021970f01ce))

### 롤 (오너가 직접 준 레퍼런스에서 실측)

* 걷는 판석 S ≈ 0.30, 값은 주변 풀과 거의 같다(V 0.29 vs 0.28). **채도와 색상으로만 가른다.**
* 채도 상위 5% 는 **못 걷는 면(풀)** 에 있다.
* 값 요동은 판석대 σ 0.021 · 미세 σ 0.034 로 아주 조용하다. 정보는 **윤곽선**이 나른다.

---

## 5. 처방전 — 우리 파이프라인에서 지금 당장 할 일

각 항목은 손잡이(파일·상수)까지 적었다. 수치는 1절 실측과 2절 근거에서 나왔다.

★**수치의 출처 등급을 구분해 둔다.** 이 표를 그대로 계약으로 삼을 때 어디까지가 남의 규격이고
어디부터가 우리 판단인지 알고 있어야 한다.

| 등급 | 무엇 | 예 |
|---|---|---|
| **A. 공표된 규격·스튜디오 문서** | 그대로 믿어도 된다 | 밸브 Dota 레이어 불투명도, 트라인 200 px/m, 상업 석재 배합비 15/50/35, 줄눈 10~12mm, batter 1:6~1:10, 코벨 1/3, 붙임기둥 2.25W, 4모서리·3m 줄눈 금지 |
| **B. 현업 아티스트 다수가 반복하는 관례** | 방향은 믿고 수치는 우리가 정함 | 빛은 위에서, 에지 하이라이트는 굵기·농도를 흩어라, 큰 형태 먼저, 잡음은 마지막, 70/30 |
| **C. 우리 실측에서 뽑은 우리 계약** | 근거는 1절 표, 출처는 없다 | 채도 0.28~0.34, 캐릭터/바닥 2.5배, meso σ 0.020~0.026, 최소 형상 23px, 판석 45~60장 |

★조사 중 확인된 것: **아래 항목은 어디에도 공표된 수치가 없다.** 누가 "업계 표준"이라고 말하면 의심할 것.
줄눈이 맵에서 가장 어두운 값이라는 규칙 · 핸드페인트 명도 20~80% 밴드 · 에지 하이라이트의 픽셀 폭 ·
판석 위아래 밝기차 퍼센트 · 파손 타일 비율 · 주춧돌/띠돌/갓돌의 벽 높이 대비 비율.
전부 우리가 정하는 값이고, 그래서 **재서 계약으로 박아 두는 것**이 유일한 방어다.

### A. 값과 채도 계약 (제일 먼저. 이거 없이 텍스처만 고치면 또 기각된다)

| 항목 | 지금 | 목표 | 근거 |
|---|---|---|---|
| 바닥 화면 채도 중앙값 | 0.50 ~ 0.54 | **0.28 ~ 0.34** | 롤 실측 0.29~0.31 |
| 채도 최대치가 있는 곳 | 바닥 판석 | **불·이끼·캐릭터·이펙트만** | 롤: 채도 상위 5% 는 풀 |
| 캐릭터 / 바닥 휘도비 | 1.39배 | **2.5배 이상** | 자기검증 기준 2배 + 13차 실적 4.4배 |
| 기둥 / 바닥 휘도비 | 1.34배 | **1.7배 이상 또는 0.7배 이하** | 같은 값이면 실루엣이 사라진다 |
| 바닥 / 벽 휘도비 | 1.40배 | 유지(1.3~1.6배) | 쿼터뷰에서 벽이 밝으면 위가 뜬다 |
| 판석대 값 요동 σ | 0.060 | **0.020 ~ 0.026** | 롤 0.021 |
| 미세 값 요동 σ | 0.111 | **0.032 ~ 0.040** | 롤 0.034 |
| 매크로 / 판석대 비 | 0.27 | **0.50 이상** | 롤 0.55~0.58 |

★**이 표는 빌더가 재게 만들 것.** `docs/dungeon1-design.md` 6절 자기검증에 항목으로 추가한다.
눈으로 판정하면 또 어긋난다.

### B. 바닥 판석을 다시 그린다

1. **판석 수를 늘린다: 5.0m 타일 한 장에 19장 → 45~60장.** 폴리카운트 권고가 하한 16, HOTS 급 100
   이다. 우리 카메라(64 px/m)에서 판석 하나가 화면 30~50px 이면 충분히 읽히므로
   **판석 등가 지름 0.35 ~ 0.55m** 를 중심값으로 잡는다(지금 중앙값 0.89m 는 두 배 크다).
2. **크기는 3~4종, 배합비를 상업 석재 표대로.**
   3종이면 **작은 15% / 중간 50% / 큰 35%**, 4종이면 **15 / 40 / 35 / 10**.
   ★균등 분포로 뽑지 말 것. 가운데 크기가 절반을 먹어야 한다.
   최대/최소 지름비는 **5~6배**로(지금 12.2배는 오히려 과해서 작은 조각이 잡티로 보인다).
   ★**큰 돌을 먼저 다 놓고 남는 틈을 작은 돌로 메운다.**
3. **모든 크기를 한 기준 모듈의 정수배로.** 우리 칸이 2.0m 이므로 기준을 0.25m 로 두고
   0.25 / 0.50 / 0.75 / 1.00m 배수로만 만든다. 격자는 유지하되 **칸마다 사각형 한 장을 찍지 않는다.**
4. **모양은 불규칙 다각형(4~7각), 가로세로비 2.6:1 이하.** 둥근 아메바를 버린다.
   ★14차 함정("절차 블록은 둥글기·곱셈 하이라이트가 알약·젤리곰을 만든다")이 바닥에도 그대로 있다.
5. **줄눈 두 규칙을 코드로 강제한다.**
   * 네 모서리가 한 점에서 만나면 안 된다
   * 줄눈이 **3.0m** 넘게 직선으로 이어지면 안 된다 (= 우리 칸 1.5칸)
6. **줄눈을 얇고 조용하게.** 폭은 판 폭의 **1.7~2%**(600mm 돌에 10~12mm 라는 실물 규격),
   지금 22% 인 줄눈 면적을 **화면 기준 4% 이하**로 떨어뜨린다(롤 2.7%).
   값은 판석보다 **선형 휘도 0.55~0.70배**. ★**줄눈에 보색을 넣지 않는다.**
   줄눈은 판석과 같은 색의 어두운 값이고, 그 대비 크기가 "판이 얼마나 또렷하게 보이나"의 손잡이다.
7. **줄눈은 판 윗면보다 함몰시킨다.** 실물 규격 1/4인치 ≈ 판 폭의 **1.5~2%**.
   기하로 낮출 수 없으면 텍스처의 값과 버텍스 AO 로 흉내 낸다.
   ★위에서 내리쬐는 우리 카메라에서 **판을 서로 떼어 놓는 것이 바로 이 함몰**이다.
8. **판마다 위가 밝고 아래가 어둡다.** 큰 기울기 한 장(타일 전체) + **판 하나 안의 작은 기울기**,
   두 겹으로 간다(80.lv WoW: "besides an overall top-down gradient, I also added gradients within the faces").
   판 안의 위·아래 밝기비는 **1.12 ~ 1.20배**만. "가운데 밝고 테두리 어두운 베개"를 없앤다.
9. **에지 하이라이트는 일부에만, 굵기를 흩어서.** 폴리카운트 정설:
   "**Vary opacity while drawing line, more opaque near corners and centers** ... **Vary edge width**"(moose),
   "paint all the important edges uniformly ... **and then erase like 80% of that**"(Shrike).
   → **판석의 30~40%** 에만, 코너 쪽에서 진하게, 굵기를 흩는다.
   ★흰색 금지("white is a bit too strong for those edges"), 판석 색상을 유지한 밝은 값으로.
   ★포토샵 Bevel & Emboss 류 자동 효과 금지("**Forget about drop shadows, bevel/emboss** ... paint").
10. **파손은 등급으로.** 대부분은 **모서리만 살짝 깨진 것**, 소수만 **완전히 부서진 것**,
    나머지는 멀쩡한 것. 그리고 **두께도 흩는다**(전부 같은 두께면 어색해진다).
11. **판마다 밑값을 흩는다.** 판석끼리 밝기 ±6%, 색상 ±4°.
    ★이게 "판석대 σ" 를 잡음이 아니라 **정보**로 채우는 방법이다.
12. **매크로 얼룩을 키운다.** 손잡이는 이미 있다 — `s40_dungeon1.py` 의
    `MACRO_A = 0.120` · `MACRO_S1 = 7.30` · `MACRO_S2 = 3.10`(타일 주기와 약분 안 되는 파장).
    14차에서 `MACRO_A` 를 0.175 → 0.120 으로 **내렸다**("밝은 바닥에서 0.175 는 얼룩 카펫이다").
    ★그런데 실측은 반대를 말한다: macro/meso 가 0.27 로 롤의 절반이다.
    카펫이 됐던 건 진폭이 커서가 아니라 **판석대 요동이 같이 컸기 때문**이다.
    판석대 σ 를 1/3 로 줄인 뒤 `MACRO_A` 를 **0.19~0.24** 로 올려 macro/meso ≥ 0.5 를 맞춘다.
    ★순서를 지킬 것. 판석을 먼저 조용하게 만들지 않고 매크로만 올리면 14차 카펫이 재현된다.
13. **닳은 길.** 통로 중앙과 방 사이 동선에 저주파 마스크를 깔아 **줄눈 이끼를 지우고 높이차를 눌러**
    평평하게 만든다. 안 닳은 구석과의 대비가 그림이 된다.
14. **최소 형상 23px 규칙.** 1024/5.0m 기준, **텍스처에 23px 미만 형상을 그리지 않는다**
    (화면 64px/m 에서 0.11m 미만은 지글거림). 그 아래는 전부 저주파 얼룩으로 대체.
15. **이음매 감사법.** 포토샵 offset 을 텍스처 크기의 **50%**(1024면 512)로 밀어 가장자리를
    한가운데로 가져와 본다. ★특히 "**bigger space on the edge of your texture than in the middle**"
    (가장자리 줄눈이 안쪽보다 넓은 것)이 눈이 제일 먼저 잡는 결함이다.

### C. 벽 텍스처를 트림 시트로 재설계

★**분업 원칙부터.** 벽 **몸통과 바닥은 지금처럼 타일 텍스처**로 두고,
트림 시트는 **가로 띠(주춧돌·띠돌·갓돌)와 아치 링과 모서리**만 맡는다.
트림이 벽을 대체하는 게 아니라 벽에 띠를 두른다.

같은 1024² 를 세로로 나눈다. 가로만 타일링한다. 인섬니악 Ultimate Trim 관례대로
**아래로 갈수록 두껍게, 높이를 두 배씩**:

```
  v 0.000 ~ 0.016  (16px)  가는 몰딩 / 드립 홈
  v 0.016 ~ 0.047  (32px)  띠돌 (string course)
  v 0.047 ~ 0.109  (64px)  갓돌 (coping) — ★세워 얹은 돌, 위 모서리 하이라이트 + 결손
  v 0.109 ~ 0.234 (128px)  기둥 축 / 계단 코 / 문설주
  v 0.234 ~ 0.484 (256px)  주춧돌 (plinth) — 굵은 돌 + 접지 어둠, 경사(batter) 음영
  v 0.484 ~ 1.000 (512px)  벽 몸통 — ★조용하게. 큰 블록 + 아주 낮은 대비
```

* 부재별 UV 배정: 벽 몸통 = 몸통 띠, 기둥 = 기둥 축 띠, 아치 = 띠돌 링, 문설주 = 기둥 축 띠,
  계단 = 계단 코 띠, 잔해 = 몸통 띠 회전. **UV 를 눈대중하지 말고 띠 경계에 스냅**한다.
* 몸통은 **평범하게** 둔다("keep the middle of the wall texture fairly plain", Level Design Book).
  지금 `WALL_HI 1.24` / `WALL_LO 0.66` 이 **모든 블록에 똑같이** 들어가 도장 자국이 된다.
  블록별로 하이라이트 **유무를 갈라라**(60% 만 넣기) 그리고 세기를 **±20%** 흩어라.
  ★근거: "Equally lit minor shapes flattens the painting"(Arne).
* 블록 크기도 갈라라. 지금 5단 × 3장 균일 = **stack bond** 라 격자로 읽힌다.
  단마다 블록 수를 바꾸고(2 / 4 / 3 / 5 / 3), 단마다 **반 칸 또는 1/3 칸씩 밀어라**(running bond).
  "one over two, two over one".
* 긴 돌을 가로로 눕히지 말 것. 가로세로비 **2.6:1 이하**.

### C-2. 벽·기둥 지오메트리 (★콜라이더·nav 계약은 한 톨도 안 건드린다)

던전 지오메트리 계약(앞벽 1.45m · 뒷벽 3.6m · 통로 4.0m · 콜라이더 인셋 0.22m)은
**네비게이션이 걸려 있어 못 건드린다.** 아래는 전부 그 안쪽 여유에서만 노는 장식이다.

우선순위 순:

1. **벽 경사(batter) 1:8.** 높이 1m 당 양쪽으로 0.125m 씩 좁아진다.
   ★삼각형이 하나도 안 는다(버텍스 x·z 를 y 에 비례해 줄이면 끝). 콜라이더는 인셋 안이라 무관.
   **쿼터뷰에서 수직 상자가 아니게 만드는 가장 싼 한 수.**
2. **모서리 챔퍼 0.06 ~ 0.10m.** 수직 모서리마다 면 하나. 모서리당 삼각형 2장.
   노멀맵이 없으므로 **진짜 폴리곤이어야 한다.**
3. **주춧돌 / 띠돌 / 갓돌 3단.** 벽 앞면에 얇은 판을 덧댄다(콜라이더 없음).
   갓돌 뭉치는 인색하게 굴지 말 것 — 고전 비례로는 벽 높이의 **20~25%** 까지 정상이다.
   내밀기는 한 번에 하지 말고 **단마다 밑단 지지폭의 1/3 이하**로 계단식.
4. **갓돌을 세워 얹는다.** 아래 단들과 90도 다른 방향. 공짜인데 쿼터뷰에서 아주 잘 읽힌다.
   군데군데 빠뜨려 실루엣 윗선을 들쭉날쭉하게(13차B 의 "부서진 관석"을 높이 3종으로 확장).
5. **모서리 quoin.** 방 모서리에만 더 크고 잘 다듬은 돌. 세로로 긴 것과 납작한 것을 번갈아.
   ★격자 던전에서 **모서리가 압출 티가 제일 많이 나는 자리**다.
6. **붙임기둥 간격을 흩는다.** 지금 "세 칸에 하나" 완전 균등이다.
   폭 W 기준 **1.5W ~ 3W** 사이에서 **A-A-B-A-A** 로 리듬을 넣고 **가운데 칸만 넓힌다.**
7. **아치는 블록으로 쌓는다.** impost → springer → voussoir → keystone.
   ★**impost(받침돌)를 벽면에서 살짝 내밀어라.** "지어진 것"으로 읽히는 디테일이 그거다.
8. **바닥-벽 전이.** 벽 밑동을 따라 잔해와 흙더미. 지금 벽은 **바닥 판 위에 상자가 그냥 앉아 있다.**
   이 한 줄이 "큐브가 판에 얹힌" 인상을 제일 크게 죽인다.

### D. 버텍스에서 공짜로 얻을 것 (텍스처 0장, 드로우콜 0)

1. **접합부 AO.** 벽 밑동·기둥 밑동·문설주 옆·계단 옆 0.35m 안을 **0.62~0.72배**로 곱한다.
   13차에 있던 접지 어둠을 14차 AMB 0.46 이 묽게 만들었다. 되살린다.
2. **면 단위 색 변주.** 같은 텍스처를 쓰는 벽면·기둥마다 칸 좌표 해시로 밝기 ±5%,
   색온도 ±3% 를 준다. ★공용 RND 를 쓰면 안 된다(13차B 에 스트림 밀림으로 nav 섬이 생긴 전례).
3. **모서리 밝기.** 챔퍼 면에 +8% 를 줘서 깎인 모서리가 빛을 물게 한다.
4. **위→아래 기울기.** 이미 높이 감쇠가 있다. 값을 13차(2.20m 위로 0.42까지)에 가깝게 되돌린다.

### E. 형태 데칼을 만든다 (지금 한 장도 없다)

| 데칼 | 무엇 | 배치 | 크기 |
|---|---|---|---|
| `DECAL_CRACK` | 분기 균열 한 줄 | 방마다 1~2 · 판석 경계 무시 | 길이 3~6m |
| `DECAL_RUBBLE` | 흩어진 돌조각 얼룩 | 벽 밑동 · 잔해 옆 | 1.2~2.0m |
| `DECAL_MOSS` | 이끼 얼룩(그물 아님) | 벽 밑동 · 줄눈 · 물 자리 | 0.8~1.6m |
| `DECAL_WEAR` | 사람이 다닌 닳음 | 통로 중앙선 | 폭 1.5m |

전부 `FLOOR_*` 이름 규칙(콜라이더 없음 + 그림자 안 던짐)에 얹으면 `web/level.js` 계약 안이다.
알파 상한은 **0.55 를 넘기지 않는다**(13차 교훈: 1.0 이면 데칼이 바닥돌을 덮어 물감이 된다).

### E-2. ★소품을 먼저 흩는다 (벽보다 우선순위가 높다)

베데스다 실측: 플레이어는 **반복된 소품을 반복된 건축보다 먼저 알아챈다.**
그러니 벽 블록을 다시 그리기 전에 이것부터 한다.

* **횃불 38자루** — 지금 전부 같은 모양·같은 높이·같은 각도다.
  높이 3종 × 기울기 ±8° × 불꽃 크기 3종 × 자루 길이 2종으로 흩는다.
  ★자리는 이미 칸 좌표 해시로 뽑고 있으니 같은 해시에서 변종 인덱스를 더 뽑으면 된다
  (공용 RND 를 새로 당기면 안 된다 — 13차B 에 스트림 밀림으로 nav 섬이 생긴 전례).
* **화로 8 · 모닥불 1 · 잔해** — 회전(무작위 yaw)과 크기 ±15% 를 준다.
  `InstancedMesh` + `setColorAt` 이면 드로우콜 증가 0.
* **인접 규칙** — 디테일이 센 조각 옆에 같은 밀도의 조각을 두지 않는다.
  뭉치고 비운다("Clumping assets and creating negative space").

### F. 안 할 것

* 텍스처 해상도 올리기 — 이미 3.2배 과하다. 올리면 지글거림만 는다.
* 노멀맵 도입 — 우리 툰 파이프라인 밖이고, 오버워치 위계에서도 3순위다.
* 실광원 추가 — 발로란트조차 플레이 공간에 동적 그림자를 안 쓴다.
* 판석마다 다른 색 넣기 — 채도 예산을 또 바닥에 쓰는 짓이다.
* 잡음 추가 — 우리는 이미 롤의 3.3배로 시끄럽다.

---

## 6. "타일 덩어리" 탈출 체크리스트

화면을 찍어 놓고 하나씩 본다. 하나라도 "아니오"면 아직 덩어리다.

**형태**
- [ ] 벽이 수직이 아니라 위로 갈수록 좁아지는가 (batter 1:8)
- [ ] 벽면에 주춧돌·몸통·갓돌 3단이 보이는가 (한 덩어리 벽지가 아닌가)
- [ ] 수직 모서리에 챔퍼 면이 있어 90도 각이 안 보이는가
- [ ] 벽 밑동에 잔해·흙이 쌓여 있어 "판 위에 앉은 상자"가 아닌가
- [ ] 갓돌이 세워져 얹혔고 군데군데 빠져 실루엣 윗선이 들쭉날쭉한가
- [ ] 방 모서리에 quoin(더 크고 다듬은 돌)이 있는가
- [ ] 붙임기둥 간격이 균등하지 않고 가운데 칸이 넓은가
- [ ] 아치에 impost(받침돌)가 벽면에서 내밀어져 있는가
- [ ] 한 화면에 똑같은 크기 블록이 4개 이상 나란히 있지 않은가
- [ ] ★벽 블록 하나를 검게 칠해 30장 늘어놓았을 때 형태가 튀는가

**바닥**
- [ ] 5m 타일 한 장에 판석이 45장 이상인가
- [ ] 크기가 3~4종이고 가운데 크기가 절반쯤을 먹는가 (균등 분포가 아닌가)
- [ ] 모든 판석 크기가 한 기준 모듈(0.25m)의 정수배인가
- [ ] 판석이 둥근 덩어리가 아니라 각진 다각형이고 가로세로비 2.6:1 이하인가
- [ ] 네 모서리가 한 점에서 만나는 자리가 없는가
- [ ] 3m 넘게 직선으로 이어지는 줄눈이 없는가
- [ ] 줄눈이 판석보다 눈에 덜 띄는가 (가늘고, 같은 색의 어두운 값인가)
- [ ] 줄눈이 판 윗면보다 함몰돼 보이는가
- [ ] 판석을 가로지르는 금이 있는가
- [ ] 파손이 등급으로 나뉘는가 (대부분 모서리만, 소수만 완파)
- [ ] 포장 가장자리가 작은 돌로 흩어지며 직선으로 안 끝나는가
- [ ] 통로 중앙에 닳은 길이 보이는가

**소품 (★벽보다 먼저 본다)**
- [ ] 횃불이 높이·기울기·불꽃 크기가 다 다른가
- [ ] 잔해·화로가 무작위 회전·크기를 갖는가
- [ ] 디테일이 센 자리 옆이 비어 있는가 (뭉치고 비웠는가)

**값과 색**
- [ ] 캐릭터가 바닥보다 2.5배 이상 밝은가
- [ ] 화면에서 제일 채도 높은 것이 바닥이 아닌가 (불·이끼·캐릭터·이펙트인가)
- [ ] 걷는 바닥의 채도 중앙값이 0.34 이하인가
- [ ] 넓고 부드러운 명암 얼룩이 바닥을 가로지르는가 (어디나 똑같이 아른거리지 않는가)
- [ ] 기둥이 바닥과 다른 밝기인가

**질감**
- [ ] 텍스처에 23px(=화면 0.11m) 미만 형상이 없는가
- [ ] 벽 몸통이 조용한가 (디테일이 위아래 띠에 몰려 있는가)
- [ ] 에지 하이라이트가 전 블록이 아니라 일부(30~40%)에만 있는가
- [ ] 접합부(벽 밑동·기둥 밑동)가 어두워져 있는가
- [ ] 판석 안의 명암이 "가운데 밝은 베개"가 아니라 "위 밝고 아래 어두운 기울기"인가

---

## 7. codex 이미지 생성용 스타일 키워드 묶음

컨셉 생성 프롬프트에 그대로 넣는 문단이다.

> Top-down isometric stone dungeon corridor, League of Legends Summoner's Rift terrain quality
> and Valorant "illustrative visual design": clean lines, tidy gradients, pleasing angles.
> Hand-painted diffuse with the lighting baked in, no normal maps, no dynamic shadows — one broad
> top-to-bottom light-to-dark gradient over the whole surface plus a small gradient inside each stone
> face, ambient occlusion painted into the joints and clamped off pure black, thin warm edge highlights
> of varying width on the upper edges of only about a third of the stones, heaviest near the corners.
> Irregular polygonal flagstone paving, four to seven sided stones, aspect ratio never above 2.6 to 1,
> three size grades mixed roughly fifteen / fifty / thirty-five percent so one middle size dominates,
> running bond offsets, no four corners meeting at a point, no joint running straight for more than a
> few stones, tight recessed hairline joints about two percent of the stone width (never bright, never a
> contrasting hue), a long branching crack running across the stones and ignoring their boundaries,
> most stones only chipped at the corners with a few completely broken, a few sunken and tilted slabs,
> moss and gravel filling only what sits below the stone top plane, a worn polished path down the middle,
> the paved edge dissolving into smaller loose stones and dirt rather than ending on a straight line.
> Masonry walls that batter inward as they rise, with architectural hierarchy: projecting plinth course
> at the base, quiet plain wall body, a thin string course, generous corbelled cornice, broken coping
> laid on edge with stones missing; large dressed quoins at every corner, chamfered vertical edges, no
> sharp ninety degree angles, arches built from voussoirs on projecting imposts, pilasters at uneven
> syncopated spacing with a wider centre bay, rubble and dirt piled where wall meets floor.
> Low-poly forms with big painted bevels giving a free rim-light read. Muted desaturated cool grey-green
> stone at about thirty percent saturation held in a narrow value band, all the saturation spent on
> torchlight, moss and magic emission only. Deep chromatic blue-violet darkness (#15274E toward #01020E),
> never neutral grey, never pure black — even the darkest stone catches some reflected light.
> Warm amber torch pools falling off inverse-square, cool teal light marking the exit.
> Adult stylized dark fantasy, Solo Leveling dungeon mood, painterly not noisy, large shapes over fine
> grain, several areas of detail and several areas of rest, no cel outlines on the environment,
> no candy colors, no rounded pillow-shaded blobs, no stack bond brick grid, no cube-like pillars,
> no equally lit repeated blocks.

부정 프롬프트로 뽑아 쓸 것: `pillow shading, rounded pebble blobs, stack bond, uniform brick grid,
identical block sizes, thick bright grout, contrasting grout color, rainbow saturation, plastic gloss,
cube pillars, vertical untapered walls, sprinkled confetti moss, high-frequency noise, sandy grain,
neutral grey shadows, pure black shadows, evenly lit every block`

---

## 8. 출처 목록

**오버워치 / 블리자드**
- [Blizzard: Environment States in Overwatch 2](https://overwatch.blizzard.com/en-gb/news/23674944/environment-states-in-overwatch-2-behind-the-scenes-with-the-engineering-team/) — 라이트맵에 색+방향 3방향, 정적 오브젝트 AO 굽기 (공식)
- [Blizzard: Overwatch 2 "Evolving the Art" 패널 정리](https://overwatch.blizzard.com/en-gb/news/23189038/revving-up-the-engine-overwatch-2-evolving-the-art-panel-recap/) (공식)
- [GDC Vault: The Art of 'Overwatch': Evolving a Legacy](https://www.gdcvault.com/play/1024268/The-Art-of-Overwatch-Evolving) — Bill Petras · Arnold Tsang. ★영상 본문은 멤버십 필요라 못 읽었다. 요약만 2차 출처로 확인
- [80.lv: Technical and Visual Analysis of Overwatch](https://80.lv/articles/overwatch-technical-overview) — 구운 베벨, 90도 각 회피, 재질 레이어링 (3자 분석)
- [80.lv: Overwatch HQ — Creating A Game Level for Portfolio](https://80.lv/articles/overwatch-hq-creating-a-game-level-for-portfolio) — 텍스처 위계 인용, 해상도 절반 낮추기, 데칼 그리블 언어 (3자 아티스트)
- [80.lv: Overwatch Fan Art Environment — Approach to Texturing](https://80.lv/articles/overwatch-fan-art-environment-approach-to-texturing) — big-to-small 그레이스케일, 슬로프 블러에 blurred clouds (3자)
- [Games Artist: Overwatch Lisbon Streets, Georg Klein](https://gamesartist.co.uk/creating-an-overwatch-inspired-environment-lisbon-streets-georg-klein/) — 벽 위아래 오염 버텍스 페인트, 바닥 대비 낮추기 (3자)
- [ArchDaily: Philip Klevestav 인터뷰](https://www.archdaily.com/938441/blizzard-entertainments-philip-klevestav-on-designing-built-environments-in-video-games) — 노이즈 총량, 눈높이 디테일 (블리자드 아티스트 본인)
- [philipk.net: Working with Modular Sets](https://www.philipk.net/tutorials/modular_sets/modular_sets.html) — 버텍스 컬러·애드온·데칼, 180도 회전 (블리자드 아티스트 본인)

**발로란트 / 라이엇**
- [Riot: The Art of VALORANT Map Environments](https://playvalorant.com/en-us/news/dev/the-art-of-valorant-map-environments/) — 타일+트림 시트가 기본, 값 통일, 너무 어둡게 안 함, 게임플레이 명료성 우선 (공식)
- [Riot: VALORANT Shaders and Gameplay Clarity](https://www.riotgames.com/en/news/valorant-shaders-and-gameplay-clarity) — 오프라인 라이팅, 플레이 공간에 동적 그림자 없음, 환경은 최대한 싸게 (공식)
- [Riot: Environment Art (Art Education)](https://www.riotgames.com/en/artedu/environment-art) (공식)
- [Inverse: Moby Francke 인터뷰](https://www.inverse.com/gaming/valorant-art-style-interview-moby-francke) — "illustrative visual design", clean lines / tidy gradients / pleasing angles

**핸드페인트 · 텍스처에 빛 굽기**
- [Valve: Dota 2 Workshop — Color Texture Light Baking](https://help.steampowered.com/en/faqs/view/60E5-5E13-712C-5315) — ★**불투명도가 공표된 유일한 스튜디오 문서**. AO 곱하기 80%, 그림자 클램프 90/90/90 스크린 85%, 포인트라이트 소프트라이트 100%, 컬러 오버레이 80% (공식)
- [Riot: A Trip Down the LoL Graphics Pipeline](https://www.riotgames.com/en/news/trip-down-lol-graphics-pipeline) — 광원이 안 움직이므로 정적 메시 그림자를 텍스처에 프리베이크 (공식)
- [80.lv: Crafting a WoW Diorama — Textures, Painting, Lighting](https://80.lv/articles/002mrs-crafting-a-wow-diorama-textures-painting-lighting) — 빛은 위에서, 큰 기울기 + 면 안의 작은 기울기, 웜 라이트/쿨 섀도
- [ArtStation Learning: Hand Painting Textures (Yekaterina Bourykina, Riot)](https://www.artstation.com/learning/courses/mj/hand-painting-textures-prop) — ★순서가 "베이크 → 그레이스케일 값 → 그라디언트 맵으로 색"
- [polycount: how to hand paint a rock/cave texture](https://polycount.com/discussion/89131/how-to-hand-paint-a-rock-cave-texture) — 선 스케치 → 큰 형태(눈 흐리고 읽히나) → 칠하기
- [polycount: hand painted texturing edge lighting question](https://polycount.com/discussion/137717/hand-painted-texturing-edge-lighting-question) — 에지 하이라이트는 농도·굵기를 흩고 80% 를 지운다
- [polycount: trying to nail the feel of hand-painted environment](https://polycount.com/discussion/116039/trying-to-nail-the-feel-of-hand-painted-environment) — ★타일은 방향광을 약하게(WoW), 고정 카메라면 면제, "돌은 대개 같은 명도이고 밝기는 조명이 정한다"
- [polycount: hand painted stone texture bad tiling](https://polycount.com/discussion/132419/hand-painted-stone-texture-bad-tiling) — 판석 장수(HOTS 10²), 최소 16, offset 50% 이음매 감사
- [polycount: stylized hand painting advice](https://polycount.com/discussion/128608/stylized-hand-painting-advice) — 흰 에지 금지, 통째 아웃라인 금지, 자동 bevel/emboss 금지
- [Arne Niklas Jansson: art tutorial](https://web.archive.org/web/20211212075542/http://androidarts.com/art_tut.htm) — ★모든 형태에 같은 3값 처리를 하면 그림이 납작해진다 · 채도는 중간톤에서 최고 · 벽돌벽은 질감을 부분만 암시 · 재질별 붓 언어
- [80.lv: Matt McDaid — Mastering the Stylized Art](https://80.lv/articles/matt-mcdaid-mastering-the-stylized-art) — 고주파를 저주파로 통합
- [Warframe TennoGen 공식 아트 가이드](https://www.warframe.com/en/steamworkshop/basic-art-guide) — 비금속은 중간톤 회색, 밝으면 셰이더에서 날아가고 어두우면 탁해진다 · 각 층 형태 2:1 · 디테일은 뭉치고 쉬는 데를 남긴다 (공식)
- [Riot VFX Style Guide 요약](https://www.vfxapprentice.com/blog/10-league-of-legends-vfx-design-tips) — 값·채도 극단 회피, 손으로 그린 형태, 잡음 배제
- [Miasma Caves: Stylized Texture Tutorial](https://blog.miasmacaves.com/post/159234431778/stylized-texture-tutorial) — AO 곱하기 / 커브처 오버레이, 100% 검정 금지, 잡음은 마지막에 Hue 블렌드로

**모듈 · 트림 시트 · 반복 깨기**
- [Beyond Extent: Trimsheets](https://www.beyondextent.com/deep-dives/trimsheets) — 띠 높이 512/256/128/64/32/16, 12에셋 36텍스처 → 3텍스처
- [Beyond Extent: Texel Density](https://www.beyondextent.com/deep-dives/deepdive-texeldensity) — ★탑다운이 밀도 최저, 실물 대비 25% 허용
- [Beyond Extent: Balancing Modularity and Uniqueness](https://www.beyondextent.com/articles/balancing-modularity-and-uniqueness-in-environment-art) — 큰 면은 타일 텍스처, 격자를 벗어날 곳
- [radiator: Bevels in video games](https://www.blog.radiator.debacle.us/2017/07/bevels-in-video-games.html) — Ultimate Trim 관례, 베벨이 비싸 보이게 만든다
- [cgchannel: Ultimate Trim 도구](https://www.cgchannel.com/2019/07/download-justen-lazarros-free-ultimate-trim-texturing-tools/) · [80.lv: Ultimate Trim Generator](https://80.lv/articles/ultimate-trim-generator-for-substance)
- [exp-points: 단일 머티리얼 모듈 키트](https://www.exp-points.com/vuk-single-material-modular-kit-environment-ue4) — 11조각으로 400×400UU 벽, 인접 디테일 규칙
- [exp-points: The Crossroads](https://www.exp-points.com/wouter-gillioen-the-crossroads) — ★벽돌은 트림에서 제외하고 타일링으로
- [Game Developer: Skyrim's Modular Approach to Level Design](https://www.gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design) — ★**반복된 소품이 반복된 건축보다 먼저 들킨다** · 발자국은 배수 · shell-based building
- [GDC 2016 Burgess (Fallout 4)](https://archive.org/stream/GDC2016Burgess/GDC2016-Burgess_djvu.txt) — 20 → 123 오브젝트, Utilitarian Core → Variants → Hero Pieces, 재질 변종은 건축을 안 바꾼다
- [ianlondon: modular level kit geometry](https://ianlondon.github.io/posts/modular-level-kit-geometry/) — 원점은 바운딩박스 중앙, 안쪽·바깥 모서리는 별도 조각
- [80.lv: Medieval Castle Production](https://80.lv/articles/001agt-medieval-castle-production-working-with-modular-packs) — 반복 깨기 4순위
- [80.lv: Breaking Down Repetition in Epic 3D Spaces](https://80.lv/articles/breaking-down-repetition-in-epic-3d-spaces)
- [80.lv: Verticality in Isometric Level Design](https://80.lv/articles/verticality-in-isometric-level-design) — 격자가 작으면 칸 경계가 보인다, 좁은 FOV + 줌아웃이 납작함의 주범
- [80.lv: Environment Art Tips (Anthony Vaccaro)](https://80.lv/articles/environment-art-tips-from-anthony-vaccaro) — 벽 전체 디테일 금지, 뭉치고 비우기
- [World of Level Design: Silhouette Design](https://www.worldofleveldesign.com/categories/game_environments_design/silhouette-design-game-environments.php) — 1-2-3 위계, ★검게 칠해 수십 장 복제해 보는 진단
- [Neil Blevins: Primary, Secondary, Tertiary Shapes](http://www.neilblevins.com/art_lessons/composition_primary_secondary_and_tertiary_shapes/composition_primary_secondary_and_tertiary_shapes.htm) — 70/30, 3차는 2차의 30%
- [three.js: InstancedMesh](https://threejs.org/docs/pages/InstancedMesh.html) — 인스턴스별 색·변환이 드로우콜 1

**실제 석공 규격 (형태 처방의 근거)**
- [Masonry Magazine: 건식 석벽 구조 원칙](https://www.masonrymagazine.com/blog/2018/11/01/dry-stone-walls-principles-of-structurally-sound-construction/) — batter 1:6~1:10, 돌 길이는 벽 안쪽으로, one over two
- [Wikipedia: Batter (walls)](https://en.wikipedia.org/wiki/Batter_(walls)) · [Quoin](https://en.wikipedia.org/wiki/Quoin) · [Intercolumniation](https://en.wikipedia.org/wiki/Intercolumniation) · [Arch](https://en.wikipedia.org/wiki/Arch)
- [chestofbooks: Parts of Walls](https://chestofbooks.com/architecture/Building-Construction-3-1/Parts-Of-Walls.html) — 벽 띠 어휘, 코벨 1/3 규칙
- [Vetter Stone: 패턴 배합비](https://www.vetterstone.com/products/patterns/) — ★15/50/35 등 공표 배합
- [pavingexpert: random paving](https://www.pavingexpert.com/random01) — ★네 모서리 금지, 3m 줄눈 금지, 줄눈 10~12mm
- [Bowman: running bond vs stack bond](https://www.bowmancc.com/articles/construction-knowledge-masonry-series-what-is-a-running-bond-vs-a-stack-bond-pattern) — stack bond 가 격자로 보이는 이유
- [dimensions.com: random uncoursed ashlar](https://www.dimensions.com/element/stone-masonry-random-uncoursed-ashlar) — 실측 치수·가로세로비
- [80.lv: Stone Floor Material](https://80.lv/articles/creating-a-stone-floor-material-with-substance-3d-designer-scanned-atlases-assets) — 파손 등급화, 두께도 흩어라
- [80.lv: Customizable Flagstone Material](https://80.lv/articles/making-a-customizable-flagstone-material-in-substance-designer) — 줄눈 채움은 높이로 결정
- [Landscaping Network: flagstone joints](https://www.landscapingnetwork.com/flagstone/joints.html) — 줄눈 대비가 판의 또렷함을 정한다
- [StraySpark: Procedural Weathering](https://www.strayspark.studio/blog/procedural-weathering-blender-geometry-nodes) — 닳음은 곡률 마스크 × 노이즈, 절대 균일하지 않게
- [M Gerwing Architects: Facade Rhythm, Venice](https://mgerwingarch.com/m-gerwing/2011/09/08/facade-rhythm-venice) — A-A-A 금지, 동시에 읽히는 여러 리듬

**일반 환경아트 공정**
- [The Level Design Book: Environment Art](https://book.leveldesignbook.com/process/env-art) — 채도 상한, 그라디언트 규칙, Castillo 값 관계, 프랙탈 세트 드레싱
- [The Level Design Book: Texturing](https://book.leveldesignbook.com/process/env-art/texturing) — 좋은 텍스처 조건, 벽 위아래 에지 디테일, 트림 시트 정의
- [Frozenbyte Wiki: Tile Textures and Trimsheets](https://wiki.frozenbyte.com/index.php/3D_Asset_Workflow:_Tile_Textures_and_Trimsheets) — 200 px/m, 10 배수 그리드, 한 축 타일링 (스튜디오 사내 문서)
- [80.lv: Tiling Textures in Game Environments (Alex Senechal)](https://80.lv/articles/tiling-textures-in-game-environments) — 70/30 규칙, 트림 2~3장으로 재질 전부
- [80.lv: Using Tileable Textures in Game Environments](https://80.lv/articles/using-tileable-textures-in-game-environments) — 타일링의 한계와 데칼·버텍스 페인트
- [80.lv: SanXia Street 1940](https://80.lv/articles/005cg-001agt-sanxia-street-1940-modular-approach-trim-sheets-decals) — 모듈 최소화, 데칼 3분류
- [80.lv: Hand-Painted Texture Guide](https://80.lv/articles/001agt-hand-painted-texture-guide-from-vsquad) — 칠하는 순서(베이스→AO→방향광→캐비티→에지→깊은 AO→손보정)
- [polycount wiki: Ambient occlusion vertex color](http://wiki.polycount.com/wiki/Ambient_occlusion_vertex_color) — 타일 텍스처 메시에 버텍스 AO 가 맞는 이유
- [StraySpark: Texture Resolution Guide](https://www.strayspark.studio/blog/texture-resolution-guide-games-512-1k-2k-4k) — 카테고리별 텍셀 밀도, 1:1 텍셀:픽셀 규칙

**나 혼자만 레벨업 · 웹툰 채색**
- [note.com 촬영 해설(횃불 어둠)](https://note.com/taka2composite/n/n2021970f01ce) — #01020E→#15274E, 휘도 마스크 림, light wrap 가산 금지, 역제곱
- [CLIP STUDIO TIPS 10550](https://tips.clip-studio.com/ko-kr/articles/10550) — 곱하기 한 장 셀 음영, 그림자는 저채도 보라
- [palmie: 岩や石の描き方](https://www.palmie.jp/lessons/82) — 깨진 자리에만 하드 브러시, 새까만 데도 빛이 닿아야 한다
- [animatetimes: 나혼렙 감독 인터뷰](https://www.animatetimes.com/news/details.php?id=1711946740) — 만화적 표현 배제, 실사 영상식 색미·촬영 처리
- [Elle Korea: 레드아이스 채색가 인터뷰](https://www.elle.co.kr/article/1901699) — 작업 전 영화·애니 조명 연출 참고
- ★검증 실패로 버린 것: 출처 불명의 "A-1 미술감독이 팔레트를 노랑·파랑이라고 말했다"는 영어권 페이지

**수집 이미지**
- `incoming/refpack_aaa/valorant/` — 라이엇 공식 맵 아트 이미지 21장(`SOURCES.txt` 에 원 URL)
- `refpack/lol_ground_owner_ref.png`, `lol_ground_owner_ref2.png` — 오너가 직접 준 롤 판석 레퍼런스.
  이 문서의 실측 기준이다
