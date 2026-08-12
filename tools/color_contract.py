# -*- coding: utf-8 -*-
"""색계약 — "바닥에 칠한 색"과 "화면에 나온 색"을 잇는 자(尺).

왜 필요한가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOG.md 의 색계약 함정은 "목표색은 화면 실측으로만 증명된다" 다. 이 맵은 그 함정이
특히 깊다. 조명이 반구광 1.55 + 해 2.35 + 림 0.55 이고 톤매핑이 ACES 라
**칠한 색이 화면에 그대로 안 나온다.** 2026-08-11 실측:

    칠한 #aabc6b (S 43.1% V 73.7%)  ->  화면 #c1c792 (S 26.5% V 78.1%)

밝기는 오르고 **채도는 반 토막**이 난다. 이게 9차 지형이 "밝은 파스텔"로 보인
기계적 원인이다 — 팔레트를 봄 낮으로 올리는 순간 ACES 의 하이라이트 구간에
들어가서 색이 씻긴다.

실측 표(8x8 색표를 바닥에 통째로 굽고 부감으로 촬영, renders/history/v96_wave10/
terrain/calib/) 가 말해 주는 것:

    칠한 V   화면 V    칠한 S 36.4 -> 화면 S    칠한 S 60.7 -> 화면 S
      25.5    23.5            42.4                    63.9
      37.0    38.5            44.2                    66.4      <- 채도 최대
      48.5    54.4            40.6                    63.5
      60.0    66.3            35.0                    57.5
      83.0    82.7            20.2                    45.3      <- 무너진다

  ★**화면 채도가 제일 잘 사는 자리는 칠한 V 37% 근처다.** 거기서는 오히려
    채도가 올라간다(36.4 -> 44.2). 밝게 칠할수록 손해다.

이 모듈은 그 관계를 식으로 세우고 **거꾸로 푼다**: 원하는 화면색을 넣으면
그렇게 나오게 하는 칠할 색을 돌려준다.

    python3 tools/color_contract.py fit          # 실측표로 조도 맞추고 오차 보고
    python3 tools/color_contract.py table        # 지형 팔레트 목표 -> 칠할 색
    python3 tools/color_contract.py to 0x515b36  # 화면 목표색 하나 -> 칠할 색

식
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    화면 = sRGB( ACES( 조도 x linear(칠한색) ) )

  · 조도(IRRADIANCE)는 채널마다 다르다(하늘은 푸르고 해는 따뜻하다). 실측표로 맞춘다.
  · ACES 는 three.js r1xx 의 ACESFilmicToneMapping 을 그대로 옮긴 것이다.
    ★근사가 아니라 **같은 식**이어야 뜻이 있다. 입력·출력 행렬과 RRTAndODTFit
    까지 그대로 옮겼다.
  · 램버트 확산광은 시점과 무관하므로 이 표는 카메라 각도가 달라져도 성립한다.
    성립하지 않는 것은 그림자·안개뿐이다(그래서 실측은 안개를 끄고 찍는다).
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(ROOT, "renders", "history", "v96_wave10", "terrain",
                   "calib", "calib_dense.npy")

# ── three.js ACESFilmicToneMapping (r150+) 그대로 ──
_IN = np.array([[0.59719, 0.35458, 0.04823],
                [0.07600, 0.90834, 0.01566],
                [0.02840, 0.13383, 0.83777]], np.float64)
_OUT = np.array([[1.60475, -0.53108, -0.07367],
                 [-0.10208, 1.10813, -0.00605],
                 [-0.00327, -0.07276, 1.07602]], np.float64)
EXPOSURE = 1.05          # web/main.js renderer.toneMappingExposure

# 실측으로 맞춘 조도(선형). fit 명령이 이 값을 다시 뽑는다.
# ★web/main.js 의 조명을 건드리면 이 값이 거짓이 된다 — fit 을 다시 돌려라.
# ★2026-08-11 실측: [0.99, 0.99, 1.00]. 평균오차 2.9/255 · 최대 8.6/255 (24칸).
#   즉 **평평한 바닥에 닿는 빛의 합은 거의 정확히 1.0** 이고, 화면이 파스텔로
#   씻긴 것은 조명 세기 탓이 아니라 **ACES 톤매핑 하나** 때문이다.
#   (반구광 1.55 + 해 2.35 + 림 0.55 는 램버트 1/PI 와 감쇠를 거쳐 1.0 으로 앉는다.)
IRRADIANCE = np.array([0.99, 0.99, 1.00], np.float64)

# ★13차D 신설. 던전(level2)은 조명이 다르다 — 같은 자로 환산한 값이 이것이다.
#   반구 0x6f9ad2 1.70 · 키 0xc4d8f0 1.70 · 림 0x3f6ea6 0.45  (web/main.js 던전 분기)
#   휘도 0.55 = 초원의 55% · 파랑/빨강 2.21배. **차고 어둡다.**
#   blender/s40_dungeon1.py 의 PAL 은 이 조도로 역산한 값이라, main.js 조명을
#   건드리면 이 숫자와 던전 팔레트가 같이 거짓이 된다.
IRR_DUNGEON = np.array([0.391, 0.565, 0.864], np.float64)


def srgb_to_lin(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(np.asarray(c, np.float64), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def aces(lin):
    """three.js 와 같은 ACES 필믹. 입력·출력 모두 선형 RGB."""
    c = np.asarray(lin, np.float64) * (EXPOSURE / 0.6)
    c = c @ _IN.T
    a = c * (c + 0.0245786) - 0.000090537
    b = c * (0.983729 * c + 0.4329510) + 0.238081
    c = a / b
    c = c @ _OUT.T
    return np.clip(c, 0.0, 1.0)


def paint_to_screen(paint_srgb, irr=None):
    """칠한 sRGB(0~1) -> 화면 sRGB(0~1)."""
    irr = IRRADIANCE if irr is None else irr
    return lin_to_srgb(aces(srgb_to_lin(paint_srgb) * irr))


def screen_to_paint(target_srgb, irr=None, iters=40):
    """화면 목표 sRGB(0~1) -> 그렇게 나오게 하는 칠할 sRGB(0~1).

    ACES 는 채널이 섞이는 3x3 을 두 번 지나므로 채널별로 따로 못 푼다.
    벡터 뉴턴 대신 **감쇠 고정점 반복**을 쓴다(단조라 잘 수렴하고 코드가 짧다).
    ★도달 못 하는 목표가 있다(ACES 가 못 내는 채도). 그때는 제일 가까운 값을
      돌려주고 err 로 알려 준다 — 조용히 어긋나면 안 된다.
    """
    irr = IRRADIANCE if irr is None else irr
    t = np.asarray(target_srgb, np.float64)
    p = np.clip(t.copy(), 0.0, 1.0)
    for _ in range(iters):
        got = paint_to_screen(p, irr)
        # 선형 공간에서 비율로 밀면 밝기는 한 번에 잡히고 색은 서서히 따라온다
        gl = np.maximum(srgb_to_lin(got), 1e-5)
        tl = np.maximum(srgb_to_lin(t), 1e-5)
        p = np.clip(srgb_to_lin(p) * (tl / gl) ** 0.75, 0.0, 1.0)
        p = lin_to_srgb(p)
    return p, float(np.abs(paint_to_screen(p, irr) - t).max())


def hexs(c):
    v = np.clip(np.asarray(c, np.float64), 0, 1) * 255.0 + 0.5
    return "#%02x%02x%02x" % (int(v[0]), int(v[1]), int(v[2]))


def hsv(c):
    import colorsys
    return colorsys.rgb_to_hsv(*np.clip(c, 0, 1))


# ─────────────────────────────────────────────────────────────────────────────
def cmd_fit():
    """실측표로 조도 세 개를 맞춘다. 오차가 크면 표가 오염된 것이다."""
    if not os.path.exists(CAL):
        print("실측표가 없다:", CAL)
        return
    a = np.load(CAL)                      # [row, col, base_rgb(0~255) x3, screen x3]
    base = a[:, 2:5] / 255.0
    scr = a[:, 5:8] / 255.0
    # ★오염 표본 걸러내기: 소품 그림자·물·절벽에 걸린 칸은 색상이 통째로 틀어진다.
    #   칠한 색의 색상 순서(R<G, B 최소)가 화면에서도 지켜지는 칸만 쓴다.
    ok = (base[:, 1] > base[:, 0]) & (scr[:, 1] > scr[:, 0]) & (base[:, 2] < base[:, 1])
    ok &= (base.max(1) > 0.12) & (base.max(1) < 0.90)
    base, scr = base[ok], scr[ok]

    def search(bs, sc):
        best, berr = None, 1e9
        for r in np.arange(0.70, 1.80, 0.01):
            for g in np.arange(0.70, 1.80, 0.01):
                for b in np.arange(0.50, 1.80, 0.01):
                    irr = np.array([r, g, b])
                    got = lin_to_srgb(aces(srgb_to_lin(bs) * irr))
                    e = float(np.abs(got - sc).mean())
                    if e < berr:
                        berr, best = e, irr
        return best, berr

    # ★2단 로버스트: 한 번 맞춘 뒤 잔차 상위 30% 를 버리고 다시 맞춘다.
    #   색표 64칸 중 몇 칸은 소품·절벽·물 위에 얹혀서 바닥이 아니다. 중앙값으로도
    #   안 걸러지는 칸이 있으므로(칸 전체가 절벽이면 중앙값도 절벽이다) 잔차로 뺀다.
    b0, _ = search(base, scr)
    res = np.abs(lin_to_srgb(aces(srgb_to_lin(base) * b0)) - scr).max(1)
    keep = res <= np.percentile(res, 70)
    best, berr = search(base[keep], scr[keep])
    got = lin_to_srgb(aces(srgb_to_lin(base[keep]) * best))
    print("맞춘 조도 = [%.3f, %.3f, %.3f]" % tuple(best))
    print("  평균오차 %.1f/255  최대오차 %.1f/255  표본 %d개(오염 %d칸 제외)"
          % (np.abs(got - scr[keep]).mean() * 255, np.abs(got - scr[keep]).max() * 255,
             int(keep.sum()), int((~keep).sum())))
    print("\n★ 이 값을 위 IRRADIANCE 에 적어라.")


TARGETS = [
    # (이름, 화면 목표 sRGB hex) — 오너 레퍼런스 실측 + 밝은 판타지 보정
    ("풀 볕",       0x86a04e),
    ("풀 중간",     0x64803c),
    ("풀 그늘",     0x3a4d2a),
    ("풀 짙은그늘", 0x27351f),
    ("흙길",        0xa8854e),
    ("판석",        0x8d9280),
    ("바위",        0x555f5e),
    ("물 얕은",     0x4f8f96),
    ("물 깊은",     0x255663),
]


def cmd_table():
    print("화면 목표색 -> 칠할 색  (조도 %s)" % np.round(IRRADIANCE, 3))
    print("%-12s %-9s %-9s %-24s %s" % ("이름", "화면목표", "칠할색", "칠할 HSV", "오차"))
    for name, h in TARGETS:
        t = np.array([(h >> 16) & 255, (h >> 8) & 255, h & 255], np.float64) / 255.0
        p, err = screen_to_paint(t)
        hh, ss, vv = hsv(p)
        print("%-12s %-9s %-9s H%4.0f S%5.1f V%5.1f      %.1f/255"
              % (name, hexs(t), hexs(p), hh * 360, ss * 100, vv * 100, err * 255))


def cmd_to(argv):
    for h in argv:
        v = int(h, 16)
        t = np.array([(v >> 16) & 255, (v >> 8) & 255, v & 255], np.float64) / 255.0
        p, err = screen_to_paint(t)
        hh, ss, vv = hsv(p)
        print("화면 %s -> 칠할 %s   H%4.0f S%5.1f V%5.1f   오차 %.1f/255"
              % (hexs(t), hexs(p), hh * 360, ss * 100, vv * 100, err * 255))


def cmd_fwd(argv):
    for h in argv:
        v = int(h, 16)
        p = np.array([(v >> 16) & 255, (v >> 8) & 255, v & 255], np.float64) / 255.0
        s = paint_to_screen(p)
        hp, sp, vp = hsv(p)
        hs2, ss2, vs2 = hsv(s)
        print("칠한 %s (H%4.0f S%5.1f V%5.1f) -> 화면 %s (H%4.0f S%5.1f V%5.1f)"
              % (hexs(p), hp * 360, sp * 100, vp * 100,
                 hexs(s), hs2 * 360, ss2 * 100, vs2 * 100))


if __name__ == "__main__":
    a = sys.argv[1:]
    # ★13차D. `--dungeon` 을 앞에 붙이면 던전 조도로 푼다(초원과 팔레트가 다르다).
    if a and a[0] == "--dungeon":
        IRRADIANCE = IRR_DUNGEON
        a = a[1:]
    if not a or a[0] == "fit":
        cmd_fit()
    elif a[0] == "table":
        cmd_table()
    elif a[0] == "to":
        cmd_to(a[1:])
    elif a[0] == "fwd":
        cmd_fwd(a[1:])
    else:
        print(__doc__)
