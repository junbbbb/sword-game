# 참격 포말 마루 구현 보고

## A. 설계 한 문단

현행 B 리본의 파란 본체는 유지하고 그 바깥 칼끝 궤적에 `파도 마루 포말층` 한 겹만 정박시켰다: 원화는 낱알이 아니라 감청 먹선으로 이어진 큰 흰 쉼표·갈고리·와권 16종이며, 각 덩어리의 아래쪽 긴 먹 획이 기존 리본의 바깥 경계와 겹쳐 두 층을 한 몸으로 묶는다. `trailFoamSample(a, b, wake)`는 매 프레임 재사용되는 칼날 선분을 즉시 복사하고, 실제 생성·자리·알파 갱신은 게임시계를 1/24초로 양자화한 칸에서만 일어난다. 새 덩어리는 `wake > 0.18`인 칼끝을 따라 0.28m 간격으로 겹쳐 붙고 최신 머리 3칸은 순백 포말, 그 뒤는 시안·먹 잔흔으로 작아지며 4/5/6칸에 수명을 어긋나게 끝낸다; 따라서 큰 흰 면은 머리에만 있고 꼬리에는 기존 감청 리본이 남는다. `wake <= 0.18`을 시각적 캐스트 종료로 삼아 즉시 생성을 끊고 마지막 포말도 최대 6칸(0.25초) 안에 죽여 11칸 본 리본보다 먼저 회수하며, NormalBlending과 선형 1.0 이하 네 단 팔레트로 먹선 대비는 살리고 블룸 문턱은 넘지 않는다. 자유 물방울은 `FX_TABLE.b.sprayK = 0`으로 전멸시키고, `pop`의 f1 방울도 새 판에서는 재생하지 않는다.

## B. 만든 파일

- 원화 `incoming/codex_foam/foam_crest_claw_master.png` — 강한 머리용 날카로운 갈퀴 8종.
- 원화 `incoming/codex_foam/foam_crest_round_master.png` — 낮은 wake/잔흔용 와권 8종.
- 원화 설명 `incoming/codex_foam/README.md` — 규격, 레퍼런스 역할, 최종 프롬프트, 굽기 명령.
- 굽기 `tools/bake_foam_crest.py` — 4x2 원화 두 장을 4x4 회색조/이진알파 시트로 재현 가능하게 변환하고 자체 검증.
- 시트 `web/tex/foam_crest_sheet.png` — 2048x1024, 4x4, 셀 512x256. 밝기 31/117/179/242, 알파 0/255.
- 코드 `web/feel.js` — 포말 풀/셰이더/24fps 게임시계/로더 폴백/샘플 API/계측/state와 타격 팝 f1 제거.
- 설계 `renders/history/v99_wave16/foam_fx/DESIGN_codex.md` — 구현 전 확정한 설계 문단.
- 검증 `renders/history/v99_wave16/foam_fx/art/foam_crest_sheet_preview.png`, `foam_crest_bake.json` — 눈검사 시트와 기계 계약 결과.

## C. main.js 연결

정확한 시그니처:

```js
feel.trailFoamSample(a, b, wake)
// a, b: THREE.Vector3 (칼날 선분 양 끝 월드 좌표)
// wake: number 0..1
// return: boolean (유효 샘플을 복사했으면 true)
```

스윙 루프에서 `trailBuf.push(...)`와 `while (trailBuf.length > TRAIL_MAX) ...` 직후, `updateTrail()`/`updateWrap()` 근처에 아래 한 줄을 둔다. 비공격 프레임은 0을 명시하는 현재 형태가 가장 안전하다.

```js
feel.trailFoamSample(a, b, attacking ? wake : 0);
```

`FX_TABLE.b.sprayK`는 `0.0`으로 내린다. `spawnSpray`의 물방울만 죽고 `ink=1`인 처치 핏방울은 살아 있다.

현재 공유 작업트리에는 이 두 main.js 연결이 이미 외부에서 들어온 것이 확인됐다. 이 작업에서는 main.js를 편집하지 않았다.

## D. 롤백

`web/feel.js`의 아래 상수 한 줄만 바꾼다. 새 메시가 꺼지고 타격 팝도 기존 f1 방울을 포함한 2장 경로로 돌아간다.

```js
const FOAM_CREST_V2 = 0;
```

main.js의 샘플 호출은 그대로 남아도 함수가 즉시 `false`를 반환하므로 안전하다. 자유 물방울까지 완전한 옛 화면으로 되돌려야 할 때만 오너가 별도로 `FX_TABLE.b.sprayK = 1.0`을 복구한다.

## E. 오너 판정 필요

- 브라우저 런타임이 없는 환경이라 실제 Z/X/C 캡처와 ON/OFF 점유율은 못 쟀다. 목표 3~7%, 상한 9%, 머리·상체 가림 60%는 새 main 연결 판에서 오너가 판정해야 한다.
- 포말 한 덩어리 최대 판은 1.30x0.56m지만 실제 live 면은 셀의 21~30%이고 먹선/구멍이 나 있다. 정지컷에서 여전히 작으면 `hl/hh`를 키우기 전에 `FOAM_SPACING`을 0.28→0.22로 좁혀 마루 밀도를 올리는 쪽이 우선이다. 너무 많으면 반대로 0.34로 벌린다.
- C는 wake 종료 후 최대 0.25초에 새 포말이 전멸하도록 닫았지만, 다른 소유의 11칸 파란 본 리본 자체가 0.72~0.95초 회수 구간에 남는 문제는 이 작업 범위에서 바꾸지 않았다.
