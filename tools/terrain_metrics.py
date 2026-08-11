# -*- coding: utf-8 -*-
"""지형 화면 품질을 숫자로 재는 자(尺). 건틀릿 심사관의 지적을 재현·반증하는 데 쓴다.

왜 필요한가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2026-08-10 건틀릿 1회차에서 지형이 12/50 으로 떨어졌고 근거가 두 숫자였다.
  · 잔디 1:1 국소대비 p99 = 5.0 (롤 52)
  · 채도 스프레드 = 58pt (벽 13.6% ↔ 수풀 71.9%. 롤은 8pt)
말로 "좋아졌다"고 하면 다음 심사에서 또 진다. **같은 자로 재서 before/after 를
남긴다.** 그리고 그 자를 롤 실물 스크린샷에도 똑같이 대서, 자 자체가 정직한지
증명한다(우리 그림에만 유리한 자를 만들면 아무 의미가 없다).

재는 법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
국소대비는 **디바이스 픽셀 1:1** 에서만 뜻이 있다. 리사이즈하면 고주파가
평균으로 뭉개져서 어느 쪽이든 값이 내려간다. 그래서 크롭만 하고 절대 안 줄인다.

  p99_range5  각 화소에서 5x5 창의 (최대 - 최소) 휘도. 그 분포의 99 분위수.
              "이 그림에서 제일 또렷한 붓자국이 몇 단계짜리인가" 를 뜻한다.
              창을 작게 잡는 이유: 큰 창을 쓰면 구역 경계(길↔풀)의 색 차이가
              들어와서 질감이 아니라 구도를 재게 된다.
  p99_hp      |L - box_blur(L, 2px)| 의 99 분위수. 같은 것을 고역통과로 본 값.
              두 값이 같이 움직여야 진짜 질감이 생긴 것이다(한쪽만 오르면
              측정 방식에 걸린 것일 수 있다).
  sat_mean    HSV 의 S 평균(%). 채도.
  lum_mean    휘도 평균(0~255).

★휘도는 sRGB 바이트 그대로 쓴다(감마 풀지 않는다). 심사관이 보는 것은 화면에
  나온 바이트이고, "몇 단계 차이로 보이는가" 도 그 공간에서 세는 게 맞다.

쓰는 법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    python3 tools/terrain_metrics.py card                 # 기준선(롤 vs v93) 한 장
    python3 tools/terrain_metrics.py shot <png> x y w h [이름]
    python3 tools/terrain_metrics.py spec <spec.json>     # 여러 크롭 한꺼번에
    python3 tools/terrain_metrics.py crops <png> x y w h <out.png>   # 크롭 눈 확인용

spec.json 은 [{"file":..., "rect":[x,y,w,h], "name":..., "group":...}, ...] 이다.
"""
import os
import sys
import json

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 휘도 가중치(Rec.709). sRGB 바이트에 그대로 건다 — 위 주석의 이유.
LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)


def _box(a, rad):
    """누적합 박스 블러. ★cumsum 앞에 0 줄을 붙여야 길이가 맞는다."""
    if rad < 1:
        return a
    k = 2 * rad + 1
    p = np.pad(a.astype(np.float32), rad, mode="edge")
    cs = np.concatenate([np.zeros((1, p.shape[1]), np.float32),
                         np.cumsum(p, axis=0, dtype=np.float32)], axis=0)
    a2 = (cs[k:, :] - cs[:-k, :]) / k
    cs2 = np.concatenate([np.zeros((a2.shape[0], 1), np.float32),
                          np.cumsum(a2, axis=1, dtype=np.float32)], axis=1)
    return (cs2[:, k:] - cs2[:, :-k]) / k


def _minmax(a, k=5):
    """k x k 창의 최대·최소. 슬라이딩 윈도 뷰로 한 번에 뽑는다(파이썬 루프 금지)."""
    r = k // 2
    p = np.pad(a, r, mode="edge")
    win = np.lib.stride_tricks.sliding_window_view(p, (k, k))
    return win.max(axis=(-1, -2)), win.min(axis=(-1, -2))


def measure(rgb):
    """RGB uint8 (H,W,3) -> 지표 딕셔너리. 크기 조정 없음."""
    f = rgb.astype(np.float32)
    lum = f @ LUMW
    mx, mn = _minmax(lum, 5)
    rng = mx - mn
    hp = np.abs(lum - _box(lum, 2))
    mxc = f.max(axis=2)
    mnc = f.min(axis=2)
    sat = np.where(mxc > 1e-3, (mxc - mnc) / np.maximum(mxc, 1e-3), 0.0)
    return {
        "px": int(lum.size),
        "lum_mean": float(lum.mean()),
        # ★v96 신설. 오너 레퍼런스 정합의 1번 격차가 "명암 폭"이다.
        #   0~1 정규화 명도의 표준편차. 롤 실물 = 0.093, 9차 우리 판 = 0.043.
        #   p99_range5(국소대비)와 다른 것을 잰다: 저쪽은 **붓자국 한 개의 세기**,
        #   이쪽은 **화면 전체에 그늘과 볕이 얼마나 벌어져 있는가**다.
        #   9차에서 통일하면서 이 값만 죽었다(국소대비는 살아 있었다).
        "lum_sd": float((lum / 255.0).std()),
        "p99_range5": float(np.percentile(rng, 99)),
        "p95_range5": float(np.percentile(rng, 95)),
        "p50_range5": float(np.percentile(rng, 50)),
        "p99_hp": float(np.percentile(hp, 99)),
        "sat_mean": float(sat.mean() * 100.0),
        "sat_p50": float(np.percentile(sat, 50) * 100.0),
        "sat_p90": float(np.percentile(sat, 90) * 100.0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ★v96 신설 — 되풀이(자기상관)와 산포 디테일 개수
# ─────────────────────────────────────────────────────────────────────────────
def autocorr(rgb, lag_min=10, lag_max=140):
    """되풀이 무늬의 세기. 0에 가까울수록 "같은 무늬가 안 돈다".

    왜 이렇게 재는가
      타일을 주기 p 로 깔면 밝기 신호가 p 마다 자기 자신과 닮는다. 그 닮음을
      **정규화 자기상관**으로 재면 한 숫자가 된다. 0 lag 주변(=그냥 이웃 화소끼리
      닮은 것)은 되풀이가 아니므로 lag_min 안쪽을 도려낸다.

    ★고역통과를 먼저 건다. 안 그러면 화면의 큰 명암 구배(그늘/볕)가 상관을
      통째로 끌어올려서 "타일 되풀이"가 아니라 "구도"를 재게 된다.
    반환: (r, dy, dx) — r 이 최대 상관, (dy,dx) 가 그 자리(주기 px)
    """
    f = rgb.astype(np.float32) @ LUMW
    f = f - _box(f, 24)                     # 고역통과: 24px 보다 큰 구배를 뺀다
    f = f - f.mean()
    h, w = f.shape
    win = (np.hanning(h)[:, None] * np.hanning(w)[None, :]).astype(np.float32)
    f = f * win
    F = np.fft.rfft2(f)
    ac = np.fft.irfft2(F * np.conj(F), s=f.shape)
    ac = np.fft.fftshift(ac)
    ac /= max(ac.max(), 1e-9)
    cy, cx = h // 2, w // 2
    yy = np.arange(h)[:, None] - cy
    xx = np.arange(w)[None, :] - cx
    d = np.sqrt(yy * yy + xx * xx)
    m = (d >= lag_min) & (d <= lag_max)
    if not m.any():
        return 0.0, 0, 0
    i = np.argmax(np.where(m, ac, -1e9))
    return float(ac.flat[i]), int(i // w - cy), int(i % w - cx)


def scatter_count(rgb, amin=8, amax=1400, thr=16.0):
    """산포 디테일(꽃잎·자갈·낙엽 같은 **작고 또렷한 물건**) 개수.

    ★밝기만 보면 안 된다. 풀 텍스처의 붓결이 밝기 고역에 잔뜩 걸려서, 첫 판은
      레퍼런스 284 개 대비 우리 화면을 1900 개로 셌다(= 자를 잘못 든 것이다).
      레퍼런스에서 눈에 띄는 것은 **색이 다른 것**(초록 위의 파란 꽃잎, 회색 자갈)
      이므로 **색상 거리**로 센다: 국소 중앙색과 색차(R-G, G-B 평면 거리)가
      문턱을 넘는 화소만 후보다. 붓결은 밝기만 흔들고 색은 안 흔들어서 빠진다.

    넓이 amin~amax 인 덩어리만 남긴다(넓은 그늘·구역 경계와 미세 노이즈 제외).
    ★겹친 꽃무리는 한 개로 세므로 이 값은 **하한**이다.
    """
    f = rgb.astype(np.float32)
    # 색차 두 축. 밝기와 직교하도록 잡는다
    o1 = f[:, :, 0] - f[:, :, 1]
    o2 = f[:, :, 1] - f[:, :, 2]
    d1 = o1 - _box(o1, 9)
    d2 = o2 - _box(o2, 9)
    m = np.sqrt(d1 * d1 + d2 * d2) > thr
    h, w = m.shape
    lab = np.zeros((h, w), np.int32)
    cur = 0
    sizes = []
    ys, xs = np.nonzero(m)
    seen = np.zeros((h, w), bool)
    stack = []
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        cur += 1
        n = 0
        stack.append((y0, x0))
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            lab[y, x] = cur
            n += 1
            if n > amax:                     # 너무 크면 더 안 센다(그늘·구역)
                pass
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        sizes.append(n)
    sizes = np.array(sizes) if sizes else np.zeros(0)
    keep = ((sizes >= amin) & (sizes <= amax)).sum() if sizes.size else 0
    return int(keep), int(sizes.size)


def crop(path, rect):
    im = Image.open(path).convert("RGB")
    x, y, w, h = [int(v) for v in rect]
    x = max(0, min(im.width - 1, x))
    y = max(0, min(im.height - 1, y))
    w = max(1, min(im.width - x, w))
    h = max(1, min(im.height - y, h))
    return np.asarray(im.crop((x, y, x + w, y + h)), dtype=np.uint8)


def row(name, m):
    return ("%-26s %7d  lum %6.1f  p99range5 %6.2f  p99hp %6.2f  "
            "sat %5.1f%%  (p50range5 %5.2f)"
            % (name, m["px"], m["lum_mean"], m["p99_range5"], m["p99_hp"],
               m["sat_mean"], m["p50_range5"]))


# ─────────────────────────────────────────────────────────────────────────────
# 기준선 — 롤 실물과 v93(건틀릿에서 진 판)을 같은 자로 잰다
# ─────────────────────────────────────────────────────────────────────────────
G = os.path.join(ROOT, "renders", "history", "v93_gauntlet", "terrain")

# 크롭 자리는 눈으로 골랐다. `crops` 명령으로 잘라 낸 그림을 확인할 수 있다.
# ★롤 쪽은 원본이 우리보다 작다(1:1 이 아니라 게임 안에서 더 축소된 상태다).
#   즉 이 비교는 **우리에게 유리한 쪽으로 기울어 있다** — 그런데도 졌다는 게
#   심사관의 지적이었다.
BASELINE = [
    # 롤 실물
    (os.path.join(G, "ref", "riot_mid_lane.jpg"), (70, 120, 240, 200), "롤 잔디(mid)", "lol"),
    (os.path.join(G, "ref", "riot_mid_lane.jpg"), (600, 470, 200, 170), "롤 잔디2(mid)", "lol"),
    (os.path.join(G, "ref", "sr_bluespawn.png"), (250, 380, 260, 200), "롤 잔디(spawn)", "lol"),
    (os.path.join(G, "ref", "sr_bluespawn.png"), (700, 120, 240, 180), "롤 포석(spawn)", "lol"),
    (os.path.join(G, "ref", "riot_jungle.jpg"), (330, 300, 220, 180), "롤 강물(jungle)", "lol"),
    (os.path.join(G, "ref", "riot_baron_pit.jpg"), (200, 200, 400, 340), "롤 절벽(baron)", "lol"),
    # v93 = 건틀릿에서 진 판
    (os.path.join(G, "01_grass_still.png"), (2320, 240, 620, 420), "v93 잔디", "v93"),
    (os.path.join(G, "02_road_still.png"), (1200, 700, 620, 420), "v93 포석/길", "v93"),
    (os.path.join(G, "03_river_still.png"), (1150, 640, 900, 260), "v93 물", "v93"),
    (os.path.join(G, "04_cliff_still.png"), (300, 500, 620, 500), "v93 절벽", "v93"),
]


def cmd_card():
    print("=" * 108)
    print("지형 국소대비·채도 기준선 (전부 1:1 크롭, 리사이즈 없음)")
    print("=" * 108)
    last = None
    for path, rect, name, grp in BASELINE:
        if not os.path.exists(path):
            print("  (없음) " + path)
            continue
        if grp != last:
            print("── %s ──" % grp)
            last = grp
        print("  " + row(name, measure(crop(path, rect))))
    print()
    print("읽는 법: p99range5 가 국소대비다. 롤 잔디와 우리 잔디를 같은 줄에서 비교해라.")


def cmd_spec(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    out = []
    groups = {}
    for it in spec:
        p = it["file"]
        if not os.path.isabs(p):
            p = os.path.join(ROOT, p)
        if not os.path.exists(p):
            print("  (없음) " + p)
            continue
        m = measure(crop(p, it["rect"]))
        m["name"] = it.get("name", os.path.basename(p))
        m["group"] = it.get("group", "-")
        out.append(m)
        groups.setdefault(m["group"], []).append(m)
        print("  " + row("[%s] %s" % (m["group"], m["name"]), m))
    # 채도 스프레드 = 그룹 안에서 채도 최대 - 최소
    for g, ms in groups.items():
        if len(ms) < 2:
            continue
        ss = sorted(ms, key=lambda m: m["sat_mean"])
        print("[채도 스프레드] %-10s %.1fpt  (최저 %s %.1f%% ↔ 최고 %s %.1f%%)"
              % (g, ss[-1]["sat_mean"] - ss[0]["sat_mean"], ss[0]["name"],
                 ss[0]["sat_mean"], ss[-1]["name"], ss[-1]["sat_mean"]))
    print(json.dumps(out, ensure_ascii=False))
    return out


def cmd_shot(argv):
    path = argv[0]
    rect = [int(v) for v in argv[1:5]]
    name = argv[5] if len(argv) > 5 else os.path.basename(path)
    print("  " + row(name, measure(crop(path, rect))))


def cmd_crops(argv):
    """크롭을 그대로 png 로 뽑는다. 자리를 눈으로 확인할 때 쓴다."""
    path = argv[0]
    rect = [int(v) for v in argv[1:5]]
    Image.fromarray(crop(path, rect)).save(argv[5])
    print("saved", argv[5])


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "card":
        cmd_card()
    elif a[0] == "spec":
        cmd_spec(a[1])
    elif a[0] == "shot":
        cmd_shot(a[1:])
    elif a[0] == "crops":
        cmd_crops(a[1:])
    else:
        print(__doc__)
