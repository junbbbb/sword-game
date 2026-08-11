# -*- coding: utf-8 -*-
"""개울 전용 질감 한 장을 굽는다 -> web/tex/water_bed.png (512, 이어붙는다)

왜 별도 텍스처인가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
심사 판정: "물이 물로 안 보인다 1/10 — 단색 시안 리본. 깊이·포말·흐름이 전무하고
강바닥이 없다." 그리고 못 박아 둔 조건이 하나 더 있었다:
**지면 텍스처에 파란 틴트를 씌워 재사용하지 말 것.** 강바닥은 강바닥이어야 한다.

한 장에 세 가지를 채널로 나눠 담는다. 개울은 화면에서 작아서 조회 두 번이면 충분하다.

    R = 강바닥 자갈      물이 얕은 자리에서 비쳐 보이는 둥근 돌. 평균 0.5 (곱수)
    G = 포말 덩어리      물가 흰 거품의 실루엣을 뜯는 노이즈. 뭉치가 커야 거품이 된다
    B = 물살 결          흐름 방향(x)으로 길게 늘어난 줄. 시간에 따라 흘려 물살을 만든다

★셋 다 sRGB 가 아니라 **데이터**다. 읽는 쪽(web/level.js)에서 NoColorSpace 로 받는다.
★R 은 평균이 정확히 0.5 여야 한다. 셰이더가 (R-0.5) 로 쓰기 때문에 평균이 밀리면
  강바닥이 통째로 밝아지거나 어두워진다.
★이어붙어야 한다(RepeatWrapping). 전부 wrap 연산으로만 만든다.

실행: python3 tools/bake_water_tex.py
"""
import os
import struct
import zlib

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "tex", "water_bed.png")
S = 512
# 한 판이 덮는 크기(m). web/level.js 의 uWBFreq 와 짝이다.
# 3.2m 짜리 한 판이면 512/3.2 = 160 텍셀/m. 화면이 150 디바이스px/m 이라 거의 1:1 =
# 텍셀 하나가 픽셀 하나로 온다(밉이 안 뭉갠다). 지면 타일에서 배운 그 규칙이다.
PERIOD_M = 3.2


def wrap_box(a, r):
    """이어지는 박스 블러(가장자리를 감아 돈다)."""
    if r < 1:
        return a
    k = 2 * r + 1
    p = np.concatenate([a[-r:, :], a, a[:r, :]], axis=0)
    p = np.concatenate([p[:, -r:], p, p[:, :r]], axis=1)
    cs = np.concatenate([np.zeros((1, p.shape[1]), np.float32),
                         np.cumsum(p, axis=0, dtype=np.float32)], axis=0)
    a2 = (cs[k:, :] - cs[:-k, :]) / k
    cs2 = np.concatenate([np.zeros((a2.shape[0], 1), np.float32),
                          np.cumsum(a2, axis=1, dtype=np.float32)], axis=1)
    return (cs2[:, k:] - cs2[:, :-k]) / k


def val_noise(cells, seed, blur=None):
    """격자 난수 -> 확대 -> 블러. cells 로 나눠떨어지므로 이어붙는다."""
    g = np.random.default_rng(seed)
    small = g.random((cells, cells)).astype(np.float32)
    rep = S // cells
    big = np.repeat(np.repeat(small, rep, 0), rep, 1)
    return wrap_box(big, rep // 2 if blur is None else blur)


def fbm(seed, octaves=4, base=8, gain=0.55):
    out = np.zeros((S, S), np.float32)
    amp, tot, c = 1.0, 0.0, base
    for i in range(octaves):
        if S % c:
            break
        out += val_noise(c, seed + i * 17) * amp
        tot += amp
        amp *= gain
        c *= 2
    return out / max(tot, 1e-6)


def pebbles(seed, n=520):
    """강바닥 자갈. 둥근 돌 하나하나에 **위쪽 하이라이트 + 아래 그림자**를 준다.
    ★평평한 원반을 흩으면 물방울 무늬가 된다. 물때가 낀 돌로 읽히려면 명암이 있어야 한다.
    ★가장자리에서 감아 돌게(모듈로) 그려야 이어붙는다."""
    g = np.random.default_rng(seed)
    h = np.zeros((S, S), np.float32)
    yy = np.arange(S)[:, None]
    xx = np.arange(S)[None, :]
    for _ in range(n):
        cx, cy = g.integers(0, S), g.integers(0, S)
        # 지름 6~34px = 3.8~21cm. 게임 화면에서 6~32px 로 온다(거의 1:1)
        rr = float(g.uniform(3.0, 17.0))
        ax = rr * float(g.uniform(0.72, 1.35))
        ang = float(g.uniform(0, np.pi))
        dx = ((xx - cx + S // 2) % S) - S // 2
        dy = ((yy - cy + S // 2) % S) - S // 2
        ca, sa = np.cos(ang), np.sin(ang)
        u = (dx * ca + dy * sa) / ax
        v = (-dx * sa + dy * ca) / rr
        d2 = u * u + v * v
        m = np.clip(1.0 - d2, 0.0, 1.0)
        if m.max() <= 0:
            continue
        dome = np.sqrt(m)                       # 반구
        # 빛은 위(-y)에서 온다. 돔의 위쪽이 밝고 아래쪽이 어둡다
        h += dome * (0.55 + 0.85 * (-v)) * float(g.uniform(0.55, 1.0))
    return h


def main():
    # ── R: 강바닥 ──
    peb = pebbles(20260811)
    peb = (peb - peb.mean()) / max(peb.std(), 1e-6)
    silt = (fbm(771, octaves=4, base=8) - 0.5) * 1.4      # 모래 얼룩(저주파)
    bed = np.clip(0.5 + peb * 0.115 + silt * 0.10, 0.0, 1.0)
    bed = bed - bed.mean() + 0.5                          # ★평균 정확히 0.5

    # ── G: 포말 덩어리 ──
    # 잘게 갈라진 노이즈가 아니라 **뭉치**여야 한다. 저주파 두 겹을 곱해
    # 덩어리 사이가 성기게 비도록 만든다(찢어진 종이 같은 거품).
    f1 = fbm(9137, octaves=3, base=16, gain=0.5)
    f2 = fbm(2255, octaves=2, base=32, gain=0.5)
    foam = np.clip(f1 * 0.72 + f2 * 0.38, 0.0, 1.0)
    foam = (foam - foam.min()) / max(foam.max() - foam.min(), 1e-6)

    # ── B: 물살 결 ──
    # 흐름 방향(가로)으로 길게 늘인다. 세로로 8배 눌러 줄무늬를 만든다.
    st = fbm(4413, octaves=3, base=32, gain=0.55)
    st = wrap_box(st, 22)                                  # 가로로 뭉갠다
    st2 = fbm(8821, octaves=2, base=64, gain=0.5)
    streak = np.clip(st * 0.75 + st2 * 0.35, 0.0, 1.0)
    streak = (streak - streak.min()) / max(streak.max() - streak.min(), 1e-6)

    rgb = np.stack([bed, foam, streak], axis=2)
    arr = np.uint8(np.clip(rgb, 0, 1) * 255 + 0.5)
    rgba = np.concatenate([arr, np.full((S, S, 1), 255, np.uint8)], axis=2)

    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(S))

    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xffffffff))

    blob = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", S, S, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    tmp = OUT + ".tmp"
    with open(tmp, "wb") as f:
        f.write(blob)
    os.replace(tmp, OUT)                                   # ★원자적 교체
    print("[물결] %s  %dx%d  %.0f KB  한 판 %.1fm = %.0f 텍셀/m"
          % (OUT, S, S, os.path.getsize(OUT) / 1024.0, PERIOD_M, S / PERIOD_M))
    print("      R 강바닥 평균 %.4f (0.5 여야 한다) std %.4f"
          % (bed.mean(), bed.std()))
    print("      G 포말   평균 %.4f  범위 %.2f~%.2f" % (foam.mean(), foam.min(), foam.max()))
    print("      B 물살   평균 %.4f  범위 %.2f~%.2f"
          % (streak.mean(), streak.min(), streak.max()))
    # 이어붙임 검사: 좌우·상하 이음매의 이웃 대비가 안쪽 평균과 비슷해야 한다
    for nm, a, b, inner in (("가로", rgb[:, -1], rgb[:, 0], np.abs(np.diff(rgb, axis=1)).mean()),
                            ("세로", rgb[-1, :], rgb[0, :], np.abs(np.diff(rgb, axis=0)).mean())):
        seam = float(np.abs(a - b).mean())
        print("      이음매 %s %.5f vs 안쪽 평균 %.5f  (%+.0f%%)"
              % (nm, seam, inner, (seam / max(inner, 1e-9) - 1) * 100))


if __name__ == "__main__":
    main()
