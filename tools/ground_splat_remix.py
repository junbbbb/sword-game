# -*- coding: utf-8 -*-
"""주 동선의 판석 가중치를 흙(길) 채널로 옮긴다 — s20 산출물의 **후처리**.

왜 이게 있나 (11차 파도, 2026-08-11)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너: **"너무 패턴 느낌이라 별로야, 화장실 타일 같잖아."**
그 인상의 절반은 잔디였고 **나머지 절반이 길**이었다.

  v90 이 롤 문법("주 동선은 정돈된 돌 포장")을 따라 K_PATH 를 판석 85% 로 깔았다.
  그런데 이 맵의 주 동선은 **폭 6.4m 짜리 직선 복도가 맵을 가로지르는 십자 + 외곽 고리**다.
  거기에 2.75m 주기 판돌을 깔면 같은 다각형이 길을 따라 끝없이 줄지어 선다.
  게다가 K_PATH 의 베이스컬러가 황토(#97774a)라 회색 돌이 아니라
  **황토색 다각형 격자** 로 보인다 = 화장실 타일.
  (증거: renders/history/v97_wave11/ground/before/b2_road_ns.jpg)

고치는 법은 타일 내용물만 갈아서는 안 된다. 길이 무슨 채널을 물고 있는지를 바꿔야 한다.

    주 동선 칸에서   판석(B) 의 MOVE 배를 흙(G) 으로 옮긴다
    흙 채널의 내용물 = codex path_organic (흙 지배 + 불규칙 판석 조각, 주기 2.55m)

★왜 전부 안 옮기고 72% 만 옮기나. 다 옮기면 "정돈된 동선"이라는 v90 의 설계가
  통째로 사라져서 길이 그냥 진흙탕이 된다. 28% 를 남기면 줄눈이 희미하게 비쳐
  **"한때 포장이었던 길"** 로 읽힌다. 그리고 path_organic 자체가 판석 조각을 품고 있다.

★여울목·폐허·바위 발치는 건드리지 않는다. 거기는 판석이 세계관(무너진 산사 터)이고
  좁아서 되풀이가 안 읽힌다. 주 동선 칸('-')만 골라 낸다.

★★이 파일은 **s20 의 출력을 덮어쓴다.** blender/s20_level1.py 를 다시 돌리면
  이 변경이 사라진다. 원래대로 하려면 s20 의 SPLAT_MIX[K_PATH] 를
      (0.03, 0.09, 0.85, 0.03)  ->  (0.03, 0.70, 0.24, 0.03)
  으로 바꾸고 이 후처리를 지우는 것이 맞다. 이번 판이 s20 을 안 건드린 이유는
  재굽기가 level1.glb/json(콜라이더 111·소품 878)까지 새로 뽑기 때문이다 —
  바닥 결 하나 고치자고 배치를 흔들 수는 없다.
  ★s20 원본은 web/tex/ground_splat.png.bak_v97 에 남겼다.

쓰는 법
    python3 tools/ground_splat_remix.py            # 굽는다(멱등: 몇 번 돌려도 같다)
    python3 tools/ground_splat_remix.py --from-bak # 원본(.bak_v97)에서 다시
"""
import os
import sys
import json

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLAT = os.path.join(ROOT, "web", "tex", "ground_splat.png")
BAK = SPLAT + ".bak_v97"
LV = json.load(open(os.path.join(ROOT, "web", "level1.json"), encoding="utf-8"))
SHEET = os.path.join(ROOT, "renders", "history", "v97_wave11", "ground", "bake",
                     "splat_remix.jpg")

MOVE = 0.72                 # 판석 -> 흙 이동 비율
FEATHER_M = 1.6             # 칸 마스크를 무르게 하는 폭(m). 길 가장자리가 톱니가 안 되게
FORD_KEEP_R = 7.0           # 여울목 반경(m). 여기는 판석을 그대로 둔다


def build(src=SPLAT):
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im, np.float32) / 255.0
    n = a.shape[0]
    b = LV["bounds"]
    cell = LV["cell"]
    G = LV["gridCells"]

    # ★스플랫 좌표계. web/level.js 가 u=(x-minX)/폭, v=(maxZ-z)/깊이 로 읽고
    #   texture.flipY=false 로 받는다. 즉 png 의 **첫 줄이 z=+48(남쪽)** 이다.
    #   여기서 격자 마스크를 그릴 때 남북을 뒤집으면 길이 통째로 엉뚱한 데 깔린다.
    row_z = b["maxZ"] - (np.arange(n) + 0.5) / n * (b["maxZ"] - b["minZ"])
    col_x = b["minX"] + (np.arange(n) + 0.5) / n * (b["maxX"] - b["minX"])

    ci = np.clip(((col_x - b["minX"]) / cell).astype(int), 0, G - 1)
    ri = np.clip(((row_z - b["minZ"]) / cell).astype(int), 0, G - 1)
    grid = np.array([[1.0 if ch == "-" else 0.0 for ch in row] for row in LV["grid"]],
                    np.float32)
    mask = grid[ri[:, None], ci[None, :]]

    # 무르게. 박스 블러 두 번 = 사다리꼴이라 계단이 안 남는다
    k = max(1, int(FEATHER_M / (b["maxX"] - b["minX"]) * n))
    for _ in range(2):
        mask = _box(mask, k)

    # 여울목은 뺀다 — 판석이 세계관이고 좁아서 되풀이가 안 읽힌다
    # ★★발판 18개의 **평균**을 쓰면 안 된다. 여울목은 세 군데(서 x-29 · 중앙 x0 ·
    #   동 x+29)로 나뉘어 있어서 평균이 맵 한복판(0, -11)에 떨어진다. 첫 판에서
    #   밟았다 — 서쪽 여울은 흙으로 갈리고 엉뚱하게 중앙 남북길만 판석으로 남았다.
    #   발판마다 원을 파야 한다.
    for p in [q for q in LV["platforms"] if q["tag"] == "ford"]:
        d = np.hypot(col_x[None, :] - p["x"], row_z[:, None] - p["z"])
        mask = mask * np.clip((d - FORD_KEEP_R) / 2.0, 0.0, 1.0)

    t = mask * MOVE
    moved = a[..., 2] * t
    out = a.copy()
    out[..., 2] = a[..., 2] - moved            # B 판석
    out[..., 1] = a[..., 1] + moved            # G 흙(=길)

    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8),
                    "RGBA").save(SPLAT)

    # ── 계약 검사 ──
    s0 = a.sum(axis=2)
    s1 = out.sum(axis=2)
    print("★가중치 합 보존: 최대 어긋남 %.6f (0 이어야 한다. 셰이더가 합으로 정규화하고"
          " 합 자체를 물칸 판정에 쓴다)" % float(np.abs(s0 - s1).max()))
    sel = mask > 0.5
    print("주 동선 화소 %.1f%%  ·  거기서 판석 %.3f -> %.3f · 흙 %.3f -> %.3f"
          % (sel.mean() * 100,
             a[..., 2][sel].mean(), out[..., 2][sel].mean(),
             a[..., 1][sel].mean(), out[..., 1][sel].mean()))
    print("저장:", SPLAT, "(%.0f KB)" % (os.path.getsize(SPLAT) / 1024))
    _sheet(a, out)


def _box(m, k):
    if k < 1:
        return m
    c = np.cumsum(np.pad(m, ((k, k), (k, k)), mode="edge"), axis=0)
    m = (c[2 * k:] - c[:-2 * k]) / (2 * k)
    c = np.cumsum(m, axis=1)
    return (c[:, 2 * k:] - c[:, :-2 * k]) / (2 * k)


def _sheet(a, out):
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    def vis(x):
        # R=풀(초록) G=흙(황토) B=판석(회색) A=마른풀(연노랑) 을 사람이 볼 색으로
        col = (x[..., 0:1] * np.array([[[0.32, 0.55, 0.24]]])
               + x[..., 1:2] * np.array([[[0.62, 0.48, 0.28]]])
               + x[..., 2:3] * np.array([[[0.55, 0.57, 0.53]]])
               + x[..., 3:4] * np.array([[[0.68, 0.62, 0.36]]]))
        return (np.clip(col / np.maximum(x.sum(2, keepdims=True), 1e-3), 0, 1) * 255)
    sh = np.concatenate([vis(a), vis(out)], axis=1).astype(np.uint8)
    Image.fromarray(sh).resize((sh.shape[1] // 2, sh.shape[0] // 2),
                               Image.LANCZOS).save(SHEET, quality=92)
    print("검증 시트(왼=전 오른=후):", SHEET)


if __name__ == "__main__":
    build(BAK if "--from-bak" in sys.argv and os.path.exists(BAK) else SPLAT)
