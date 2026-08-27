# 던전 구조물 9종 — codex 콘셉트 → Meshy 이미지→3D (2026-08-13)

원자재 `incoming/codex_dgprops/*.png` 9장을 Meshy 이미지→3D(울트라 모드)로 돌려
텍스처 입은 glb 9개를 `incoming/meshy_dgprops/` 에 받았다. 게임 코드·web/ 는 건드리지 않았다.

## 설정 (9건 전부 동일)
Meshy 7 · 높은 디테일 · **울트라 모드 ON**(25cr) · 멀티 뷰 OFF · 이미지 향상 ON · 자동 분할 OFF ·
라이선스 **비공식적인(private)** · 텍스처 2K + **PBR 맵 ON**(10cr)

## 결과 한 장 정리

| 소품 | 접수(생성) | 텍스처 접수 | 받은 파일 | 크기 | 삼각형 | Meshy 이름 |
|---|---|---|---|---|---|---|
| pillar_intact | 04:56:11 | 05:01:54 | pillar_intact.glb | 113.8MB | 3,104,876 | Ancient Stone Pillar |
| pillar_broken | 04:57:01 | 05:25:06 | pillar_broken.glb | 114.9MB | 3,139,512 | Broken Stone Obelisk |
| arch_gate | 04:57:29 | 05:26:50 | arch_gate.glb | 114.7MB | 3,102,372 | Ancient Stone Arch |
| altar | 04:57:39 | 05:27:06 | altar.glb | 122.6MB | 3,133,614 | Ancient Stone Pedestal |
| brazier | 04:57:49 | 05:27:20 | brazier.glb | 115.1MB | 3,127,598 | Ancient Stone Basin |
| rubble_large | 04:58:05 | 05:28:35 | rubble_large.glb | 114.1MB | 3,129,298 | Stone Cairn |
| rubble_small | 04:58:15 | 05:29:22 | rubble_small.glb | 114.9MB | 3,143,542 | Stacked Stone Blocks |
| coping_chunk | 04:58:24 | 05:30:14 | coping_chunk.glb | 114.8MB | 3,134,994 | Ruined Stone Barricade |
| quoin_corner | 04:58:34 | 05:30:53 | quoin_corner.glb | 114.1MB | 3,093,270 | Ancient Stone Corner |

- 생성은 접수 후 3~6분, 텍스처는 2~5분. 다운로드는 건당 20~35초(114MB).
- 9개 모두 머리 4바이트 `glTF`, 이미지 3장(base color · metallic-roughness · normal, jpeg 1.2~2.6MB),
  재질 1개, 메시 1개. **파일명이 `_texture.glb` 로 끝나는지가 텍스처가 들어 있다는 증거**다.
- 신원 확인: `verify_sheet.jpg`(왼쪽 콘셉트 / 오른쪽 Meshy 결과) 9쌍 전부 일치.

## 크레딧
시작 **2,104** → 텍스처 다 굽고 **1,709** → 마지막 확인 **1,759**.
- 생성 9건 × 25 = 225
- 텍스처 17건 × 10 = 170 ← 이 중 **80(8건)은 낭비**다(아래 사고).
- 리메시 9건 = **0**(공짜)
- 총 소모 **395**. 05:47 무렵 잔액이 1,709 → 1,759 로 **+50** 올랐다(Meshy 쪽 일일 지급으로 보인다.
  우리가 되돌린 게 아니다). 그래서 "시작-끝" 뺄셈(345)과 실제 소모(395)가 50 어긋난다.

## ★사고 — 같은 기둥에 텍스처를 여덟 번 구웠다 (80cr 소각)
`el.click()` 으로 자산 카드를 고른 줄 알았는데 **리액트가 그 클릭을 무시**한다.
뷰어는 계속 첫 모델(pillar_intact)을 들고 있었고, 그 상태로 '텍스처'를 여덟 번 눌렀다.
크레딧은 매번 정확히 10씩 줄어서(=접수는 성공) 영수증만 봐서는 정상으로 보였다.
그리드에 똑같은 기둥 카드가 아홉 장 쌓인 걸 보고서야 알았다.

**교훈 — 영수증(크레딧)은 "접수됐다"만 말하지 "무엇에 걸렸는지"는 말하지 않는다.**
그래서 스크립트에 신원 확인을 박았다.
- 카드 선택은 **진짜 마우스 클릭**(page.mouse.click). 좌표는 스크롤이 멈춘 뒤 다시 잰다.
- 고른 뒤 **뷰어 하단 썸네일의 `uploads/<id>`** 가 그 소품의 원본 이미지 id 와 같은지 본다
  (`tools/meshy_pipe/mp_ids.json` 에 소품별 model/image id 표를 박아 뒀다).
- 도구막대가 `텍스처 +10` 이면 아직 무텍스처, `+50` 이면 이미 텍스처된 것 → 두 번 굽지 않는다.
- 패널 상태(PBR ON · 2K)와 패널에 물린 이미지 id 가 뷰어와 같은지까지 보고 나서야 누른다.

## 다른 함정들 (다음 사람이 또 밟지 말 것)
1. **뷰어의 초록 다운로드 버튼은 무텍스처(`_generate`) 파일을 준다.** 텍스처 입은 파일은
   **카드의 ⋮ 메뉴 → 다운로드**. 같은 자산인데 53MB(무텍스처) vs 114MB(텍스처)로 갈린다.
   눈으로도 갈리지 않는다 - 뷰어는 텍스처 자산을 열어도 흰 모델을 보여 준다.
2. **텍스처 패널은 "열릴 때" 대상 모델에 묶인다.** 열어 둔 채 다른 카드를 눌러도 앞 모델을 가리킨다.
   반드시 닫고(Escape) → 카드 고르고 → 다시 연다.
3. **전체화면 '텍스처 편집'은 Escape 로 안 닫힌다**(X 버튼). 떠 있으면 뒤의 모든 클릭이 먹힌다.
   반면 텍스처 생성 패널은 Escape 로 닫힌다. 둘은 다른 물건이다.
4. 스무스 스크롤: `scrollIntoView` 직후에 잰 좌표는 흔들린다. `behavior:'instant'` + 1.2초 대기 후 재측정.
5. **★playwright 의 `download.saveAs` 를 믿지 마라(이 방식에서는).** connectOverCDP 로 붙었다
   떨어지는 구조라 임시 아티팩트 폴더가 앞 연결의 것이고, 그 폴더가 사라져 `ENOENT` 로 깨진다.
   9건 중 8건이 이걸로 실패했다(같은 걸 다시 돌리면 어쩌다 되기도 해서 더 헷갈린다).
   해법: CDP `Browser.setDownloadBehavior` 로 **받을 폴더를 직접 지정**하고, 그 폴더에 새로 생긴
   파일의 크기가 3초간 멎을 때까지 지켜본다(`mp_lib.setDownloadDir` / `waitNewFile`).
6. **좌표로 요소를 찾으면 창 크기가 바뀔 때 조용히 거짓말을 한다.** 브라우저를 다시 띄웠더니
   뷰어 푸터의 y 가 통째로 움직여 "자산을 못 찾았다"가 났다. 신원 썸네일은 좌표가 아니라
   `src` 에 `/uploads/` 가 박혔는지로 찾는다.
7. 브라우저를 백그라운드 Bash 로 띄우면 하네스가 그 작업을 죽일 때 창도 같이 죽는다(리메시 2건이
   그렇게 끊겼다). `nohup … &` 로 떼어 놓고 띄울 것.
8. 내부 API(`/meshyd-api/web/v1/…`)는 토큰이 필요해 쓰지 않았다. 화면이 보여 주는 것만 읽었다.

## 폴리 — 울트라는 3백만 삼각형을 뱉는다
다운로드 대화상자에는 폴리 감축 선택지가 **없다**(크기/원점/포맷 뿐).
대신 뷰어 도구막대의 **리메시가 크레딧 0**이다: 고정/적응형 · 3K/10K/30K/100K · 사각형/삼각형.
과거 관례(소품 2~3천)에 맞춰 **3K·삼각형**으로 9종을 다시 뽑아 `_3k.glb` 로 함께 받았다.
원본 9개는 손대지 않고 그대로 둔다.

| 소품 | 3K판 삼각형 | 크기 |
|---|---|---|
| pillar_intact | 2,930 | 16.4MB |
| pillar_broken | 2,996 | 15.6MB |
| arch_gate | 3,082 | 18.6MB |
| altar | 2,762 | 19.4MB |
| brazier | 2,996 | 17.6MB |
| rubble_large | 3,092 | 17.8MB |
| rubble_small | 3,012 | 15.0MB |
| coping_chunk | 3,069 | 18.1MB |
| quoin_corner | 2,978 | 19.0MB |

- **텍스처는 리메시를 따라온다**(base/MR/normal 3장 그대로). 실루엣도 썸네일에서 원본과 구분이 안 된다
  (`verify_sheet_3k.jpg` 3열 비교).
- 다만 리메시본의 텍스처는 **png** 로 들어온다(장당 3~10MB). 파일이 15~20MB 로 커진 이유가 이것이고,
  장착 단계에서 jpg/webp 로 다시 굽으면 3~5MB 로 내려간다.
- 색: Meshy 결과가 콘셉트보다 **회색으로 뜬다**(콘셉트는 초록 이끼 기가 돈다). 과거 12-소품원색 판단
  (ACES 역보정 · `tools/raw_props.py`)이 여기에도 필요할 수 있다 - 장착 단계에서 볼 것.

## 장착 전에 알아야 할 것 — 크기와 원점
9종 모두 **긴 축이 약 1.9 단위로 정규화**되어 나온다(Meshy 가 맞춘다). 던전 실제 치수는 장착 쪽에서
따로 곱해야 한다. 그리고 다운로드 대화상자에서 원점을 '바닥'으로 두고 받았는데도
**실제 원점은 물체 한가운데**다(바닥 y 가 -0.39 ~ -0.95). 바닥에 세우려면 y 를 올려 줘야 한다.

| 소품 | 크기(x·y·z) | 바닥 y |
|---|---|---|
| pillar_intact | 0.72 × 1.90 × 0.70 | -0.951 |
| pillar_broken | 0.86 × 1.90 × 0.83 | -0.952 |
| arch_gate | 1.57 × 1.90 × 0.38 | -0.952 |
| altar | 1.89 × 0.77 × 1.55 | -0.387 |
| brazier | 1.90 × 1.82 × 1.88 | -0.913 |
| rubble_large | 1.88 × 1.61 × 1.84 | -0.803 |
| rubble_small | 1.90 × 1.34 × 1.37 | -0.670 |
| coping_chunk | 1.90 × 1.23 × 0.40 | -0.616 |
| quoin_corner | 1.13 × 1.90 × 1.14 | -0.951 |

## 파일
- 원본(풀디테일 3.1M): `incoming/meshy_dgprops/<이름>.glb` 9개 (113~123MB, 합 1.2GB)
- 저폴리(3K): `incoming/meshy_dgprops/<이름>_3k.glb` 9개 (15~20MB)
- 판정지: `verify_sheet.jpg`(콘셉트↔결과) · `verify_sheet_3k.jpg`(콘셉트↔원본↔3K) ·
  `thumb_<이름>.png` · `thumb3k_<이름>.png` · `view_<이름>.png`
- 도구: `tools/meshy_pipe/` (mp_lib · mp_open · mp_probe · mp_form · mp_submit · mp_batch ·
  mp_texture · mp_harvest · mp_remesh · mp_thumbs · mp_glbinfo · mp_map · mp_cards · **mp_ids.json**)
- 되돌리는 법: `node tools/meshy_pipe/mp_open.mjs`(nohup) 으로 창을 띄우고 나머지 스크립트가 붙는다.
  복제 프로필 `~/Library/Caches/ms-playwright-mcp/meshy-clone-0813` (원본 MCP 프로필은 건드리지 않음).
