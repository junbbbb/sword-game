# -*- coding: utf-8 -*-
"""산포 디테일 한 장을 굽는다 -> web/tex/ground_scatter.png (RGBA 2048)

    python3 tools/bake_scatter_tex.py

왜 이 겹이 따로 필요한가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너 레퍼런스(롤 실물)에는 **파란 꽃잎이 수십 장 흩뿌려져** 있다. 자갈·낙엽·
잔풀도 같이 있다. 블라인드 심사가 우리 판에서 이걸 **0개**로 셌다.

이걸 어디에 그릴 것인가가 문제였다. 후보 셋을 실측으로 재 봤다.

  ① 바닥 베이스컬러(2048 이 96m) = **21 px/m**
     화면은 150 디바이스 px/m 이다. 즉 텍셀 하나가 화면 7 px 이라, 15cm 짜리
     꽃잎을 그리면 텍스처에서 **3 px** 이고 화면에서는 21px 짜리 뭉갠 얼룩이 된다.
     레퍼런스의 또렷한 꽃잎이 안 나온다. (9차의 SPECKS 가 정확히 이 실패였다 —
     그래서 "꽃"이 아니라 "색 얼룩"으로 보였다.)
  ② 지면 타일 4장에 섞어 그리기 = 488 px/m 로 해상도는 충분하지만 **주기가 2.1m**
     이라 꽃잎이 2.1m 격자로 도는 게 바로 보인다. 산포는 성길수록 되풀이가 눈에 띈다.
  ③ **전용 타일 한 장** = 2048 이 8.5m -> **241 px/m**. 화면보다 1.6배 촘촘하니
     밉이 곱게 먹고, 주기는 8.5m 라 한 화면(18x15m)에 두 판 남짓만 들어온다.
     ★그 위에 저주파 덮개 마스크를 곱해 **면적의 30~40%에만** 나오게 하면
     되풀이가 사실상 안 읽힌다(성긴 것이 오히려 유리하다).

그래서 ③ 이다. 이 파일이 그 한 장을 굽는다.

색 계약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RGB 는 **칠할 색**이다(화면색이 아니다). ACES 가 밝은 쪽 채도를 씻으므로
tools/color_contract.py 로 화면 목표색을 거꾸로 풀어 적었다.
알파는 덮개(0~1)다. ★알파에는 감마가 안 걸리므로 그대로 쓴다.

레퍼런스 실측(refpack/lol_ground_owner_ref.png):
    파란 꽃잎  화면 #3f6a72 ~ #4e7d8c  (H 190~195, S 45~55%, V 37~55%)
    꽃잎 무리 안 밀도 7~12%,  화면 전체로는 2~3%
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import color_contract as CC   # noqa: E402

RES = 2048
PERIOD_M = 8.5                     # 한 판이 덮는 m. ★web/level.js SCATTER_PERIOD 와 같아야 한다
PX_PER_M = RES / PERIOD_M          # 241
OUT = os.path.join(ROOT, "web", "tex", "ground_scatter.png")


def paint_of(screen_hex):
    """화면 목표색 -> 칠할 색(0~1 RGB). 감으로 고르지 않기 위한 통로."""
    t = np.array([(screen_hex >> 16) & 255, (screen_hex >> 8) & 255,
                  screen_hex & 255], np.float64) / 255.0
    p, _ = CC.screen_to_paint(t)
    return p


# ── 마크 종류 ──
# (이름, 화면목표색, 지름 m(최소, 최대), 무리당 개수(최소, 최대), 무리 수, 모양)
# ★모여 있어야 한다. 레퍼런스의 꽃잎은 고르게 뿌려진 게 아니라 **줄기처럼 몰려**
#   있고 그 사이는 텅 빈 풀이다. 고르게 뿌리면 색종이 조각(컨페티)으로 보인다
#   — 첫 판이 정확히 그랬다(renders/history/v96_wave10/terrain/scatter_v1.png).
# spread  무리가 흩어지는 반경(m). 작을수록 뭉친다
KINDS = [
    # (이름, 화면목표색, 지름 m, 무리당 개수, 무리 수, 모양, 흩어짐 m)
    ("파란 꽃잎", 0x4f8496, (0.085, 0.185), (8, 20), 7, "petal", (0.20, 0.50)),
    ("연보라 꽃", 0x7d7fb0, (0.065, 0.125), (4, 9), 3, "blossom", (0.16, 0.34)),
    ("흰 들꽃", 0xc8ccb4, (0.050, 0.095), (4, 9), 3, "blossom", (0.14, 0.32)),
    ("노란 들꽃", 0xc4b25a, (0.050, 0.100), (4, 10), 3, "blossom", (0.14, 0.32)),
    ("자갈 밝은", 0x8f8d80, (0.080, 0.200), (3, 7), 4, "pebble", (0.28, 0.65)),
    ("자갈 어두운", 0x555a55, (0.075, 0.170), (3, 7), 4, "pebble", (0.26, 0.62)),
    ("낙엽", 0x8a6b3d, (0.105, 0.240), (2, 6), 4, "leaf", (0.32, 0.75)),
    ("진한 잔풀", 0x3d5228, (0.190, 0.400), (2, 5), 8, "tuft", (0.28, 0.70)),
    ("마른 잔풀", 0x907c47, (0.150, 0.320), (2, 5), 5, "tuft", (0.26, 0.62)),
]


def stamp(acc_a, acc_c, cy, cx, rad_px, col, shape, rng):
    """마크 하나를 찍는다. acc_a = 덮개, acc_c = 색 누적(덮개 가중).

    ★하드 엣지로 그린다. 가장자리 1픽셀만 부드럽게 두고 그 안쪽은 꽉 찬 색이다.
      레퍼런스의 꽃잎이 또렷한 이유가 이것이고, 9차의 SPECKS 가 흐릿했던 이유가
      가장자리를 반지름 전체에 걸쳐 깎았기 때문이다(m = (1 - d/rad) ** 0.75).
    """
    r = int(rad_px) + 2
    i0, i1 = max(0, cy - r), min(RES, cy + r + 1)
    j0, j1 = max(0, cx - r), min(RES, cx + r + 1)
    if i1 <= i0 or j1 <= j0:
        return
    yy = (np.arange(i0, i1)[:, None] - cy).astype(np.float32)
    xx = (np.arange(j0, j1)[None, :] - cx).astype(np.float32)
    ang = rng.uniform(0, np.pi * 2)
    ca, sa = np.cos(ang), np.sin(ang)
    u = xx * ca + yy * sa
    v = -xx * sa + yy * ca
    if shape == "petal":
        # 갸름한 잎 하나. 한쪽 끝이 뾰족하다
        el = np.sqrt((u / (rad_px * 1.0)) ** 2 + (v / (rad_px * 0.42)) ** 2)
        d = el * (1.0 + 0.35 * np.clip(u / max(rad_px, 1e-3), 0, 1))
    elif shape == "blossom":
        # 다섯 잎 꽃. 각도로 반지름을 흔든다
        th = np.arctan2(v, u)
        rr = np.sqrt(u * u + v * v)
        d = rr / np.maximum(rad_px * (0.72 + 0.28 * np.cos(th * 5.0)), 1e-3)
    elif shape == "pebble":
        el = np.sqrt((u / (rad_px * 1.0)) ** 2 + (v / (rad_px * 0.78)) ** 2)
        d = el
    elif shape == "leaf":
        # 나뭇잎. 양끝이 뾰족한 렌즈꼴
        el = np.sqrt((u / (rad_px * 1.0)) ** 2 + (v / (rad_px * 0.50)) ** 2)
        d = el * (1.0 + 0.22 * np.abs(u) / max(rad_px, 1e-3))
    else:                       # tuft — 부챗살로 뻗은 풀 몇 가닥
        # ★별 모양이 아니라 **위로 뻗은 가닥**이어야 풀로 읽힌다. 아래쪽(v>0)을
        #   잘라내고 위쪽만 부채꼴로 남긴다.
        th = np.arctan2(v, u)
        rr = np.sqrt(u * u + v * v)
        blade = np.abs(np.cos(th * 3.5))
        d = rr / np.maximum(rad_px * (0.16 + 0.84 * blade ** 2.2), 1e-3)
        d = np.where(v > rad_px * 0.16, 9.0, d)
    # ★가장자리 1.4px 만 부드럽게. 나머지는 꽉 찬 색이다
    soft = 1.4 / max(rad_px, 1.0)
    m = np.clip((1.0 - d) / soft, 0.0, 1.0)
    if m.max() <= 0:
        return
    # 마크 안에서 색을 조금 흔든다(같은 도장이 반복되면 도장으로 보인다)
    c = np.clip(np.asarray(col, np.float32) * rng.uniform(0.86, 1.14), 0, 1)
    # ★안쪽 결. 한쪽에 밝은 면을 줘야 납작한 색종이가 아니라 **물건**으로 보인다.
    #   화면에서 마크 하나가 20~50px 이라 이 정도 계단이 눈에 들어온다.
    lit = np.clip(0.5 - (u * 0.7 + v * 0.7) / max(rad_px, 1e-3) * 0.5, 0.0, 1.0)
    shade = (0.86 + 0.30 * lit)[:, :, None]
    wa = acc_a[i0:i1, j0:j1]
    wc = acc_c[i0:i1, j0:j1]
    # 나중 것이 위에 온다(알파 합성). 겹치면 위엣것 색이 이긴다
    wc *= (1.0 - m)[:, :, None]
    wc += m[:, :, None] * np.clip(c[None, None, :] * shade, 0, 1)
    np.maximum(wa, m, out=wa)


def main():
    rng = np.random.default_rng(20260811)
    acc_a = np.zeros((RES, RES), np.float32)
    acc_c = np.zeros((RES, RES, 3), np.float32)
    total = 0
    report = []
    for name, hexc, (r0, r1), (n0, n1), clusters, shape, (s0, s1) in KINDS:
        col = paint_of(hexc)
        n_here = 0
        for _ in range(clusters):
            # 무리 중심. ★가장자리를 넘어가는 마크는 반대쪽으로 감싼다(이어붙임)
            ccy = int(rng.integers(0, RES))
            ccx = int(rng.integers(0, RES))
            spread = rng.uniform(s0, s1) * PX_PER_M
            for _k in range(int(rng.integers(n0, n1 + 1))):
                dy = int(rng.normal(0, spread))
                dx = int(rng.normal(0, spread))
                rad = rng.uniform(r0, r1) * 0.5 * PX_PER_M
                # ★상하좌우 감싸기: 같은 마크를 아홉 자리에 찍되 화면 밖은 stamp 가 자른다
                for oy in (-RES, 0, RES):
                    for ox in (-RES, 0, RES):
                        cy = ccy + dy + oy
                        cx = ccx + dx + ox
                        if -RES * 0.02 - rad <= cy <= RES * 1.02 + rad and \
                           -RES * 0.02 - rad <= cx <= RES * 1.02 + rad:
                            stamp(acc_a, acc_c, cy, cx, rad, col, shape,
                                  np.random.default_rng(int(rng.integers(0, 2 ** 31))))
                n_here += 1
        total += n_here
        report.append((name, n_here, CC.hexs(col), hexc))

    cov = float((acc_a > 0.35).mean())
    print("[산포] 마크 %d개 · 덮개 %.2f%% (문턱 0.35 기준)" % (total, cov * 100))
    for name, n, ph, sh in report:
        print("   %-10s %3d개  칠할 %s  (화면 목표 #%06x)" % (name, n, ph, sh))
    # 화면 한 판(18x15m)에 몇 개가 들어오는지 = 심사 항목 "화면당 산포 개수"
    per_screen = total / (PERIOD_M * PERIOD_M) * (18.0 * 15.0)
    print("[산포] 주기 %.1fm · 텍셀 %.0f px/m · 한 화면(18x15m) 이론 %d개"
          % (PERIOD_M, PX_PER_M, int(per_screen)))

    rgba = np.zeros((RES, RES, 4), np.float32)
    # ★덮개가 0 인 자리의 RGB 는 아무 값이나 돼도 되지만, 밉맵이 섞을 때
    #   검정이 배어 나오므로 **주변 마크 색의 평균**으로 채운다.
    mean_col = (acc_c.reshape(-1, 3).sum(0) / max(acc_a.sum(), 1e-6))
    rgba[:, :, :3] = np.where(acc_a[:, :, None] > 1e-4, acc_c,
                              mean_col[None, None, :])
    rgba[:, :, 3] = acc_a
    Image.fromarray(np.uint8(np.clip(rgba, 0, 1) * 255 + 0.5), "RGBA").save(OUT)
    print("[산포] 저장 %s  %.0f KB" % (OUT, os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()
