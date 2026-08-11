# -*- coding: utf-8 -*-
"""web/level.js 의 바닥 셰이더를 파이썬에서 그대로 계산해 본다.

왜 이게 필요한가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
지면 국소대비를 게임 스크린샷으로 재려면 매번 브라우저를 띄우고, 화면에는 요괴가
돌아다니고 은신이 걸리고 그림자가 낀다(실제로 첫 측정에서 캐릭터가 수풀에 들어가
화면이 까매졌다). 손잡이 하나 돌릴 때마다 그 짓을 할 수는 없다.

바닥의 최종색은 식이 **완전히 결정적**이다.

    비율_i   = 타일_i(회전_i · p / 주기_i) / 타일평균_i
    곱수     = clamp( mix(1, Σ w_i · 비율_i, TILE_AMT), TILE_MIN, TILE_MAX )
    최종색   = 베이스컬러 × 곱수 × 잔결곱수

그래서 여기서 같은 식을 돌리고, 화면에 실제로 나온 값과 한 번만 맞춰 두면
(calibrate) 이후로는 오프라인에서 몇 초 만에 손잡이를 비교할 수 있다.

★밉맵을 흉내내는 법이 이 파일의 핵심이다.
  GPU 는 화면 1픽셀이 텍셀 N 개를 덮으면 N×N 을 평균낸 밉 단계를 읽는다. 그래서
  **타일을 화면 배율로 area 리샘플한 뒤 깔면** 그게 곧 밉 결과다. 1024px 타일이
  주기 2.1m 이고 화면이 150 디바이스px/m 이면 한 판이 315px 로 줄어든다
  = 텍셀 3.25 개가 픽셀 하나로 뭉개진다. **이 뭉갬이 v93 국소대비가 죽은 진짜 원인**
  이고, 이 파일은 그걸 숫자로 보여 준다.

쓰는 법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python3 tools/ground_sim.py table          # 주기 사다리(현재 vs 후보)
    python3 tools/ground_sim.py zones          # 구역별(초원·길·캠프) 현재 설정
    python3 tools/ground_sim.py png <out.png>  # 눈으로 볼 시트
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "web", "tex")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from terrain_metrics import measure  # noqa: E402

# ── 화면 배율 ──
# 고정 쿼터뷰(pitch 0.86 / dist 24 / fov 24) 의 실측 배율 75 CSS px/m.
# 심사관 스크린샷이 DPR 2 라 디바이스 픽셀로는 그 두 배다.
PX_PER_M = 150.0

# web/level.js 의 계약값. ★한쪽만 고치면 안 된다.
TILE_AMT = 1.9
TILE_MIN, TILE_MAX = 0.28, 2.05
DETAIL_GAIN = 0.38
DETAIL_MIN, DETAIL_MAX = 0.90, 1.10
DETAIL_FINE = 1 / 1.7
DETAIL_WIDE = 1 / 4.3
DETAIL_WIDE_W = 0.72

TILES = ["tile_grass", "tile_dirt", "tile_stone", "tile_dry"]
PERIOD_NOW = [2.10, 1.70, 1.60, 2.40]

# 구역별 스플랫 가중치. blender/s20_level1.py SPLAT_MIX 에서 그대로 옮겼다
ZONES = {
    "초원(K_OPEN)": (0.86, 0.02, 0.02, 0.10),
    "주동선(K_PATH)": (0.03, 0.09, 0.85, 0.03),
    "캠프흙": (0.30, 0.62, 0.04, 0.04),
    "보스마당(K_BOSS)": (0.04, 0.70, 0.18, 0.08),
}
# 그 구역이 화면에서 실제로 낸 평균 휘도(BEFORE 스크린샷 실측). 밝기가 다르면
# 같은 곱수라도 sRGB 단계 차가 달라지므로 여기에 맞춘 뒤 재야 공정하다.
ZONE_LUM = {"초원(K_OPEN)": 175.0, "주동선(K_PATH)": 185.0,
            "캠프흙": 170.0, "보스마당(K_BOSS)": 170.0}

_cache = {}


def load(name):
    if name not in _cache:
        _cache[name] = np.asarray(Image.open(os.path.join(TEX, name + ".png"))
                                  .convert("RGB"), np.float32) / 255.0
    return _cache[name]


def screen_tile(name, period, w, h, phase=(0, 0)):
    """타일 한 장을 화면 배율로 area 리샘플해 (h, w) 만큼 깔아 준다 = 밉 흉내."""
    src = load(name)
    rep_px = max(2, int(round(period * PX_PER_M)))          # 한 판이 화면에서 몇 px
    im = Image.fromarray(np.uint8(src * 255 + 0.5))
    im = im.resize((rep_px, rep_px), Image.BOX)             # ★area = 밉과 같은 평균
    a = np.asarray(im, np.float32) / 255.0
    ny = h // rep_px + 2
    nx = w // rep_px + 2
    big = np.tile(a, (ny, nx, 1))
    return big[phase[1]:phase[1] + h, phase[0]:phase[0] + w]


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def sim(weights, periods, amt=TILE_AMT, w=900, h=560, lum_target=175.0,
        detail_gain=DETAIL_GAIN, detail_clamp=(DETAIL_MIN, DETAIL_MAX),
        detail_fine=DETAIL_FINE, detail_wide=DETAIL_WIDE, detail_name="ground_detail"):
    """구역 하나를 화면 픽셀로 그린다. 반환 = uint8 RGB."""
    ratio = np.zeros((h, w, 3), np.float32)
    for i, (nm, per, wt) in enumerate(zip(TILES, periods, weights)):
        if wt <= 1e-4:
            continue
        t = screen_tile(nm, per, w, h, phase=(i * 37, i * 53))
        ratio += wt * (t / np.maximum(t.reshape(-1, 3).mean(0), 1e-3))
    ratio /= max(sum(weights), 1e-6)
    mult = np.clip(1.0 + (ratio - 1.0) * amt, TILE_MIN, TILE_MAX)

    # 잔결. 셰이더와 같은 두 겹(잔결 g 채널 + 넓은 얼룩 r 채널)
    d = np.asarray(Image.open(os.path.join(TEX, detail_name + ".png"))
                   .convert("RGB"), np.float32) / 255.0
    dh = d.shape[0]

    def samp(period, ch, rot):
        rep = max(2, int(round(period * PX_PER_M)))
        im = Image.fromarray(np.uint8(d[:, :, ch] * 255 + 0.5))
        im = im.resize((rep, rep), Image.BOX)
        a = np.asarray(im, np.float32) / 255.0
        big = np.tile(a, (h // rep + 2, w // rep + 2))
        return big[rot:rot + h, rot:rot + w]

    gdF = samp(1.0 / detail_fine, 1, 0) - 0.5
    gdW = samp(1.0 / detail_wide, 0, 11) - 0.5
    gdM = np.clip(1.0 + (gdF + gdW * DETAIL_WIDE_W) * detail_gain,
                  detail_clamp[0], detail_clamp[1])
    _ = dh

    base = srgb_to_lin(np.float32(lum_target / 255.0))
    out = base * mult * gdM[:, :, None]
    return np.uint8(np.clip(lin_to_srgb(out), 0, 1) * 255 + 0.5)


def cmd_table():
    print("타일 텍셀 밀도와 국소대비 (초원 = 풀 0.86 + 마른풀 0.10)")
    print("%-30s %8s %8s %8s %8s" % ("주기(풀/흙/판석/마른풀)", "텍셀/px", "p99rng5", "p99hp", "p50rng5"))
    w = ZONES["초원(K_OPEN)"]
    for label, per in (("현재 v93", PERIOD_NOW),
                       ("x1.6", [p * 1.6 for p in PERIOD_NOW]),
                       ("x2.2", [p * 2.2 for p in PERIOD_NOW]),
                       ("x3.0", [p * 3.0 for p in PERIOD_NOW]),
                       ("x4.0", [p * 4.0 for p in PERIOD_NOW])):
        img = sim(w, per)
        m = measure(img)
        dens = 1024.0 / per[0] / PX_PER_M
        print("%-30s %8.2f %8.2f %8.2f %8.2f"
              % (label + " " + "/".join("%.1f" % p for p in per), dens,
                 m["p99_range5"], m["p99_hp"], m["p50_range5"]))


def cmd_zones(periods=None):
    per = periods or PERIOD_NOW
    print("구역별 (주기 %s)" % "/".join("%.2f" % p for p in per))
    for zn, w in ZONES.items():
        m = measure(sim(w, per, lum_target=ZONE_LUM[zn]))
        print("  %-18s p99rng5 %6.2f  p99hp %6.2f  p50rng5 %6.2f  lum %5.1f"
              % (zn, m["p99_range5"], m["p99_hp"], m["p50_range5"], m["lum_mean"]))


def cmd_png(out):
    w = ZONES["초원(K_OPEN)"]
    rows = []
    for per in (PERIOD_NOW, [p * 2.2 for p in PERIOD_NOW], [p * 3.0 for p in PERIOD_NOW]):
        rows.append(sim(w, per, w=900, h=300))
    Image.fromarray(np.concatenate(rows, axis=0)).save(out)
    print("saved", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "table":
        cmd_table()
    elif a[0] == "zones":
        cmd_zones()
    elif a[0] == "png":
        cmd_png(a[1])
    else:
        print(__doc__)
