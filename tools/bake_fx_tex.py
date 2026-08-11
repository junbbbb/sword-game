# -*- coding: utf-8 -*-
"""귀멸 애니 풍 이펙트 텍스처 4장을 절차적으로 굽는다 (Pillow + numpy).

  web/tex/brush_slash.png  2048x512  수묵 붓자국 한 획 (가산합성용)
  web/tex/hit_spark.png     512x512  타격 섬광 (가산합성용)
  web/tex/ink_drop.png      256x256  먹물 방울 (일반합성용, 처치 파편)
  web/tex/ring_shock.png    512x512  충격 고리 (가산합성용)

── 왜 이렇게 그리는가 ──
기존 web/tex/wave_water.png · wave_fire.png 를 픽셀로 재보고 그 결을 그대로 따랐다.
그 두 장의 정체는 이랬다.
  * 색이 딱 10~13종. 전부 **평칠**이고 경계가 그라데이션 없이 끊긴다
  * 띠 경계가 자로 그은 직선이 아니라 손으로 그은 것처럼 흔들린다
  * 띠 사이를 가르는 **가는 밝은 선(갓선)** 이 한 줄 지나간다
  * 실루엣 위아래가 찢긴 종이처럼 너덜너덜하다
  * 아주 작은 **흰 사각 점**이 흩뿌려져 있다 (동그란 글로우가 아니라 픽셀 사각형)
  * 알파가 사실상 이진(255 94% / 0 5%)이고 그 사이는 얇은 옅은 테두리뿐
그래서 여기서도 그라데이션을 쓰지 않는다. 팔레트도 web/main.js 의 ELEMENTS
(fire · plain) 값을 그대로 가져와 같은 집안 색으로 맞췄다.

── 알파 규칙 (여기서 데이면 게임 화면에서 검은 테두리로 나온다) ──
  1) **스트레이트 알파**로 굽는다. RGB 에 알파를 미리 곱하지 않는다
  2) 알파 0 인 픽셀에도 이웃 색을 번지게(bleed) 채운다. 새까맣게 두면 확대 필터링
     에서 검은 링이 생긴다
  3) 알파는 계단으로 떨어뜨린다. 부드러운 페이드는 이 그림체가 아니다
     (blender/fx_water.py 의 "알파 페이드 없음. 밝기는 계단식" 규칙과 같은 결)

실행:
    python3 tools/bake_fx_tex.py            # 텍스처 4장 + 검증 이미지
    python3 tools/bake_fx_tex.py --tex-only # 텍스처만
"""
import os
import sys
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(ROOT, "web", "tex")
OUT_DIR = os.path.join(ROOT, "renders", "history", "v66_fx_tex")

# ─────────────────────────────────────────────────────────────
# 팔레트 — web/main.js ELEMENTS 와 같은 값. 한쪽만 고치지 말 것
# ─────────────────────────────────────────────────────────────
# fire: 안쪽이 제일 뜨겁고 바깥으로 갈수록 식어 검붉게 스러진다
C_WHITE = "FFFFFF"
F_CREAM = "FFF0C8"   # 크림 (wave_fire 최다색 중 하나)
F_GOLD2 = "FFD678"
F_GOLD = "FFC63E"
F_ORANGE = "F58C22"
F_EMBER = "E85E1C"
F_RED = "C4321A"
F_BLOOD = "8C1A0C"
F_MAROON = "6E160A"
F_DARK = "4A0E08"
F_INK = "280804"
# plain: 기본칼 검기. 흰 심에서 옅은 청백으로 식는다
P_ICE = "D8F4FF"
P_SKY = "A8E4FA"
P_CYAN = "7FD4F5"
P_BLUE = "62A8CE"
P_DEEP = "3E86AE"


def hexf(h):
    """'RRGGBB' -> float RGB 0..1"""
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], np.float32) / 255.0


# ─────────────────────────────────────────────────────────────
# 노이즈 (손그림 흔들림의 재료)
# ─────────────────────────────────────────────────────────────
def _grid_noise(h, w, gh, gw, rng):
    """저해상도 난수 격자를 부드럽게 키운 값 노이즈 0..1"""
    gh = max(2, int(gh))
    gw = max(2, int(gw))
    g = rng.random((gh, gw)).astype(np.float32)
    im = Image.fromarray(np.uint8(np.clip(g, 0, 1) * 255), "L")
    return np.asarray(im.resize((w, h), Image.BICUBIC), np.float32) / 255.0


def fbm2(h, w, gh, gw, rng, octaves=3, gain=0.5):
    """옥타브를 겹친 2D 값 노이즈. gh/gw 비율이 결의 방향을 정한다
    (gh 크고 gw 작으면 가로줄무늬 = 붓털)"""
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += amp * _grid_noise(h, w, gh * (2 ** o), gw * (2 ** o), rng)
        tot += amp
        amp *= gain
    return acc / tot


def noise1d(n, cells, rng, loop=False):
    """1D 값 노이즈 0..1. loop=True 면 양끝이 이어진다(원환용)"""
    cells = max(2, int(cells))
    g = rng.random(cells + 1).astype(np.float32)
    if loop:
        g[-1] = g[0]
    xs = np.linspace(0, cells, n, endpoint=False).astype(np.float32)
    i = xs.astype(int)
    t = xs - i
    t = t * t * (3 - 2 * t)
    return g[i] * (1 - t) + g[i + 1] * t


def fbm1(n, cells, rng, octaves=3, gain=0.5, loop=False):
    acc = np.zeros(n, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += amp * noise1d(n, cells * (2 ** o), rng, loop)
        tot += amp
        amp *= gain
    return acc / tot


# ─────────────────────────────────────────────────────────────
# 이어붙는(tileable) 2D 노이즈
# ★위의 fbm2 는 PIL resize 로 키운다. 가장자리가 서로 안 맞아서 **타일링하면
#   주기마다 격자선이 보인다.** 화면에 한 번 얹고 마는 이펙트에는 상관없지만
#   바닥처럼 수십 번 반복하는 텍스처에는 절대 쓰면 안 된다. 그래서 격자 인덱스를
#   나머지연산으로 감아 직접 보간한다(양끝이 같은 난수를 본다 = 이어진다).
# ─────────────────────────────────────────────────────────────
def _tile_grid(n, cy, cx, rng):
    """cy x cx 난수 격자를 n x n 으로 부드럽게 키운다. 상하좌우가 이어진다"""
    cy = max(2, int(cy))
    cx = max(2, int(cx))
    g = rng.random((cy, cx)).astype(np.float32)
    ty = np.linspace(0, cy, n, endpoint=False).astype(np.float32)
    tx = np.linspace(0, cx, n, endpoint=False).astype(np.float32)
    iy = ty.astype(int) % cy
    jy = (iy + 1) % cy
    ix = tx.astype(int) % cx
    jx = (ix + 1) % cx
    fy = ty - np.floor(ty)
    fy = fy * fy * (3 - 2 * fy)
    fx = tx - np.floor(tx)
    fx = fx * fx * (3 - 2 * fx)
    a = g[iy, :] * (1 - fy)[:, None] + g[jy, :] * fy[:, None]      # 세로 보간 (n, cx)
    return a[:, ix] * (1 - fx)[None, :] + a[:, jx] * fx[None, :]   # 가로 보간 (n, n)


def _tile_fbm(n, cy, cx, rng, octaves=4, gain=0.5):
    """옥타브를 겹친 이어붙는 값 노이즈. cy/cx 비율이 결의 방향을 정한다"""
    acc = np.zeros((n, n), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += amp * _tile_grid(n, cy * (2 ** o), cx * (2 ** o), rng)
        tot += amp
        amp *= gain
    return acc / tot


def _tile_layers(n, cells, rng, gain=0.62):
    """소수(prime) 격자를 겹친 이어붙는 노이즈.

    ★2 배씩 키우는 보통의 fbm 을 바닥에 쓰면 안 된다. 옥타브가 전부 같은 격자에
      맞물려서 격자무늬(체크 짜임)가 눈에 보인다(실측 실패 1회). 서로 나누어
      떨어지지 않는 칸수를 쓰고 층마다 무작위로 밀면 그 결이 사라진다.
    """
    acc = np.zeros((n, n), np.float32)
    amp, tot = 1.0, 0.0
    for c in cells:
        g = _tile_grid(n, c, c, rng)
        g = np.roll(g, (int(rng.integers(0, n)), int(rng.integers(0, n))), axis=(0, 1))
        acc += amp * g
        tot += amp
        amp *= gain
    return acc / tot


def _tile_warp(base, dx, dy):
    """base 를 (dx, dy) 픽셀만큼 밀어서 다시 읽는다. 감아 읽으므로 이어붙음이 유지된다.

    dx/dy 를 저주파 노이즈로 주면 결이 휘감긴다(도메인 워핑). 풀이 한 방향으로
    빗질된 것처럼 보이지 않게 하는 유일하게 값싼 방법이다.
    """
    n = base.shape[0]
    yy, xx = np.meshgrid(np.arange(n, dtype=np.float32),
                         np.arange(n, dtype=np.float32), indexing="ij")
    sx = (xx + dx) % n
    sy = (yy + dy) % n
    x0 = np.floor(sx).astype(int) % n
    y0 = np.floor(sy).astype(int) % n
    x1 = (x0 + 1) % n
    y1 = (y0 + 1) % n
    fx = (sx - np.floor(sx))[..., ]
    fy = (sy - np.floor(sy))[..., ]
    a = base[y0, x0] * (1 - fx) + base[y0, x1] * fx
    b = base[y1, x0] * (1 - fx) + base[y1, x1] * fx
    return a * (1 - fy) + b * fy


def _tile_flow(base, ang, length=8.0, steps=9):
    """흐름 방향으로 문질러 **획**을 만든다 (line integral convolution 의 싼 버전).

    ★풀잎을 만들 때 "세로로 긴 노이즈 + 가로로 긴 노이즈"를 겹치면 안 된다. 두 격자가
      직교해서 그대로 **돗자리 짜임**으로 보인다(실측 실패 1회. 잔디가 아니라 삼베가
      나왔다). 잎은 한 자리에서 한 방향으로만 뻗어야 한다.
      그래서 저주파 각도장 ang 을 만들고 잔 노이즈를 그 방향으로만 밀어서 평균낸다.
      결과는 소용돌이치는 붓결이 되고 격자 방향이 통째로 사라진다.
    ang     라디안 각도장 (n x n)
    length  획의 반길이(px)
    """
    ca, sa = np.cos(ang), np.sin(ang)
    acc = np.zeros_like(base)
    tot = 0.0
    for i in range(steps):
        t = ((i + 0.5) / steps - 0.5) * 2.0 * length
        w = 1.0 - abs(t) / (length + 1e-6) * 0.55        # 끝으로 갈수록 옅어진다(획 끝)
        acc += w * _tile_warp(base, ca * t, sa * t)
        tot += w
    return acc / tot


def _tile_ridge(n, cells, rng, gain=0.55):
    """능선 노이즈. 0.5 를 접어 올려 **가는 선**만 1 에 가깝게 남긴다.
    흙바닥 갈라짐처럼 '선으로 읽히는 것'은 이걸로 만든다(평범한 노이즈를 임계값으로
    자르면 선이 아니라 얼룩덜룩한 반점이 된다)."""
    v = _tile_layers(n, cells, rng, gain=gain)
    return 1.0 - np.abs(v * 2.0 - 1.0)


def _tile_cells(n, k, rng, jitter=0.42):
    """이어붙는 셀룰러(보로노이). k x k 칸마다 점을 하나씩 흩는다.

    돌려주는 값
      f1  가장 가까운 점까지의 거리(px)    -> 판석 가운데가 볼록해 보이게
      f2  두 번째 점까지의 거리(px)        -> f2 - f1 이 작은 곳이 **이음매**다
      cid 가장 가까운 점의 칸 번호         -> 판마다 다른 밝기를 주는 열쇠

    ★이웃 3x3 칸을 나머지연산으로 감아 본다. 감아 본 칸의 점 좌표는 한 판 크기만큼
      되밀어 줘야 거리가 맞는다(안 그러면 가장자리에서 이음매가 어긋난다).
    """
    cellw = n / float(k)
    py = (np.arange(k, dtype=np.float32)[:, None] + 0.5
          + (rng.random((k, k)).astype(np.float32) - 0.5) * 2.0 * jitter) * cellw
    px = (np.arange(k, dtype=np.float32)[None, :] + 0.5
          + (rng.random((k, k)).astype(np.float32) - 0.5) * 2.0 * jitter) * cellw
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    ri = (yy / cellw).astype(np.int32)
    ci = (xx / cellw).astype(np.int32)
    f1 = np.full((n, n), 1e9, np.float32)
    f2 = np.full((n, n), 1e9, np.float32)
    cid = np.zeros((n, n), np.int32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ry, rx = ri + dy, ci + dx
            r2, c2 = ry % k, rx % k
            sy = py[r2, c2] + (ry - r2) * cellw      # 감아 본 만큼 되민다
            sx = px[r2, c2] + (rx - c2) * cellw
            d = np.sqrt((yy - sy) ** 2 + (xx - sx) ** 2)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))   # ★f1 을 덮기 전에
            cid = np.where(closer, r2 * k + c2, cid)
            f1 = np.where(closer, d, f1)
    return f1, f2, cid


def _tile_cells2(n, k, rng, jitter=0.42):
    """_tile_cells 와 같은데 **두 번째로 가까운 점의 칸 번호(cid2)** 까지 돌려준다.

    ★판석 파빙에 필요하다. 판 크기를 불규칙하게 만드는 유일하게 깨끗한 방법은
      보로노이 격자를 두 벌 겹치는 게 아니라(이음매가 서로 충돌해서 지저분해진다)
      **이웃 칸끼리 합치는** 것이다. 합치려면 "이 이음매가 어느 두 판 사이인가"를
      알아야 한다 = cid 와 cid2. 둘이 같은 무리면 그 이음매를 지운다.
    """
    cellw = n / float(k)
    py = (np.arange(k, dtype=np.float32)[:, None] + 0.5
          + (rng.random((k, k)).astype(np.float32) - 0.5) * 2.0 * jitter) * cellw
    px = (np.arange(k, dtype=np.float32)[None, :] + 0.5
          + (rng.random((k, k)).astype(np.float32) - 0.5) * 2.0 * jitter) * cellw
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    ri = (yy / cellw).astype(np.int32)
    ci = (xx / cellw).astype(np.int32)
    f1 = np.full((n, n), 1e9, np.float32)
    f2 = np.full((n, n), 1e9, np.float32)
    cid = np.zeros((n, n), np.int32)
    cid2 = np.zeros((n, n), np.int32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ry, rx = ri + dy, ci + dx
            r2, c2 = ry % k, rx % k
            sy = py[r2, c2] + (ry - r2) * cellw
            sx = px[r2, c2] + (rx - c2) * cellw
            d = np.sqrt((yy - sy) ** 2 + (xx - sx) ** 2)
            nid = r2 * k + c2
            closer = d < f1
            mid = (~closer) & (d < f2)
            # ★f1/cid 를 덮기 **전에** f2/cid2 를 정한다. 순서가 바뀌면 둘이 같아진다
            f2 = np.where(closer, f1, np.where(mid, d, f2))
            cid2 = np.where(closer, cid, np.where(mid, nid, cid2))
            cid = np.where(closer, nid, cid)
            f1 = np.where(closer, d, f1)
    return f1, f2, cid, cid2


def _merge_groups(k, rng, p=0.34, rounds=2):
    """k x k 보로노이 칸을 확률 p 로 이웃과 합쳐 무리 번호를 만든다.
    ★가로로 감아 이어야 한다(% k). 안 그러면 타일 이음매에서 판이 갈린다."""
    par = list(range(k * k))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for _ in range(rounds):
        for (dr, dc) in ((0, 1), (1, 0)):
            for r in range(k):
                for c in range(k):
                    if rng.random() >= p:
                        continue
                    a = find(r * k + c)
                    b = find(((r + dr) % k) * k + ((c + dc) % k))
                    if a != b:
                        par[a] = b
    return np.array([find(i) for i in range(k * k)], np.int32)


def _smooth(x, a, b):
    """smoothstep. 계단을 만들 때 경계를 한 픽셀만 부드럽게 하는 용도.
    a·b 에 배열을 줘도 된다(자갈처럼 자리마다 크기가 다른 것에 쓴다)"""
    t = np.clip((x - a) / np.maximum(np.asarray(b, np.float32) - a, 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _norm01(v, lo=2.0, hi=98.0):
    """백분위로 0..1 로 편다. band_color 의 계단 폭을 실제 분포에 맞추기 위한 것"""
    a, b = np.percentile(v, lo), np.percentile(v, hi)
    return np.clip((v - a) / max(b - a, 1e-6), 0.0, 1.0)


# ─────────────────────────────────────────────────────────────
# 칠하기 — 색 계단은 딱 끊는다. 보간하면 그라데이션이 되어 결이 깨진다
# ─────────────────────────────────────────────────────────────
def band_color(b, stops):
    """b(0..1) 를 팔레트 계단으로 바꾼다. stops=[(상한, 'RRGGBB'), ...] 오름차순"""
    out = np.zeros(b.shape + (3,), np.float32)
    prev = -1e9
    for hi, hx in stops:
        m = (b > prev) & (b <= hi)
        out[m] = hexf(hx)
        prev = hi
    out[b > stops[-1][0]] = hexf(stops[-1][1])
    return out


# 알파 계단. 안은 꽉 차고 가장자리만 몇 단으로 떨어진다(옅은 halo 포함)
ALPHA_STEPS = ((0.94, 255), (0.72, 214), (0.46, 154), (0.22, 84), (0.06, 38))


def stepped_alpha(cov):
    a = np.zeros(cov.shape, np.uint8)
    for th, v in sorted(ALPHA_STEPS, key=lambda s: s[0]):
        a[cov >= th] = v
    return a


def speckle(rgb, alpha, mask, rng, count, color, size=2, jitter=0):
    """아주 작은 사각 점. wave 텍스처의 흰 알갱이와 같은 문법"""
    h, w = alpha.shape
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return
    pick = rng.integers(0, len(ys), size=count)
    c = hexf(color)
    for p in pick:
        y = int(ys[p]) + (int(rng.integers(-jitter, jitter + 1)) if jitter else 0)
        x = int(xs[p]) + (int(rng.integers(-jitter, jitter + 1)) if jitter else 0)
        s = int(size + rng.integers(0, 2))
        y0, y1 = max(0, y), min(h, y + s)
        x0, x1 = max(0, x), min(w, x + s)
        if y0 >= y1 or x0 >= x1:
            continue
        rgb[y0:y1, x0:x1] = c
        alpha[y0:y1, x0:x1] = 255


# ─────────────────────────────────────────────────────────────
# 알파 0 영역 색 번지기 (검은 링 방지)
# ─────────────────────────────────────────────────────────────
def bleed_rgb(rgb, alpha, iters=40, fill_hex=None):
    """알파가 있는 픽셀의 색을 투명 영역으로 퍼뜨린다.
    확대·밉맵 필터링이 투명 픽셀의 RGB 까지 섞기 때문에, 거기가 검으면
    윤곽에 검은 링이 낀다. 스트레이트 알파를 쓰는 한 이 작업은 필수다."""
    h, w = alpha.shape
    known = alpha > 0
    out = rgb.copy()
    out[~known] = 0.0
    kn = known.copy()
    for _ in range(iters):
        if kn.all():
            break
        pv = np.pad(out, ((1, 1), (1, 1), (0, 0)), mode="edge")
        pk = np.pad(kn.astype(np.float32), ((1, 1), (1, 1)), mode="edge")
        acc = np.zeros_like(out)
        cnt = np.zeros((h, w), np.float32)
        for dy, dx in ((0, 1), (2, 1), (1, 0), (1, 2)):
            k = pk[dy:dy + h, dx:dx + w]
            acc += pv[dy:dy + h, dx:dx + w] * k[..., None]
            cnt += k
        m = (~kn) & (cnt > 0)
        out[m] = acc[m] / cnt[m][:, None]
        kn |= m
    if not kn.all() and fill_hex is not None:
        out[~kn] = hexf(fill_hex)
    return out


def save_rgba(path, rgb, alpha):
    arr = np.empty(alpha.shape + (4,), np.uint8)
    arr[..., :3] = np.uint8(np.clip(rgb, 0, 1) * 255 + 0.5)
    arr[..., 3] = alpha
    Image.fromarray(arr, "RGBA").save(path, optimize=True)
    return path


def save_rgb(path, rgb):
    """알파가 없는 장. 지면 타일은 덮는 그림이 아니라 바닥 전체를 채우는 재질이라
    알파 채널이 통째로 낭비다(파일 크기 25% 절약)."""
    arr = np.uint8(np.clip(rgb, 0, 1) * 255 + 0.5)
    Image.fromarray(arr).save(path, optimize=True)
    return path


# ═════════════════════════════════════════════════════════════
# 1) brush_slash 2048x512 — 수묵 횡획
# ═════════════════════════════════════════════════════════════
def bake_brush_slash(path):
    W, H = 2048, 512
    rng = np.random.default_rng(20260810)
    x = np.arange(W, dtype=np.float32)
    y = np.arange(H, dtype=np.float32)[:, None]
    u = x / (W - 1.0)

    # 붓길. 아래로 배가 부른 횡획 + 끝에서 살짝 튀어 오르는 마무리 + 손떨림
    arc = np.maximum(np.sin(np.pi * np.clip(u * 0.94, 0, 1)), 0.0)
    cy = (H * 0.40
          + 78.0 * arc ** 1.25
          - 46.0 * np.clip((u - 0.80) / 0.20, 0, 1) ** 1.6      # 收筆에서 튀어 오른다
          + 24.0 * (fbm1(W, 5, rng, octaves=2) - 0.5))

    # 굵기: 起筆(눌러 넣기) -> 몸통 -> 갈필로 급히 가늘어지는 꼬리.
    # 예전 값은 너무 뚱뚱해서 붓이 아니라 불기둥으로 읽혔다
    ku = [0.00, 0.02, 0.05, 0.13, 0.26, 0.40, 0.54, 0.66, 0.78, 0.88, 0.95, 1.00]
    kw = [30.0, 128.0, 152.0, 150.0, 132.0, 110.0, 86.0, 64.0, 44.0, 27.0, 15.0, 7.0]
    hw = np.interp(u, ku, kw).astype(np.float32)
    hw *= (0.88 + 0.24 * fbm1(W, 11, rng, octaves=2))

    tt = (y - cy[None, :]) / hw[None, :]          # 음수=위 / 양수=아래
    at = np.abs(tt)

    # 실루엣 가장자리를 찢는다. 잘게 부스스한 게 아니라 **큼직하게 뜯긴** 이가 나야
    # 손으로 그은 먹선이 된다. 위아래를 다른 노이즈로 흔들어 비대칭을 만든다
    coarse_t = fbm2(H, W, 2, 9, rng, octaves=3)
    coarse_b = fbm2(H, W, 2, 8, rng, octaves=3)
    fine = fbm2(H, W, 4, 46, rng, octaves=2)
    e_top = 1.00 + 0.19 * (coarse_t - 0.5) * 2 + 0.09 * (fine - 0.5) * 2
    e_bot = 1.00 + 0.26 * (coarse_b - 0.5) * 2 + 0.13 * (fine - 0.5) * 2
    edge = np.where(tt < 0, e_top, e_bot).astype(np.float32)

    # 起筆: 왼쪽 끝을 비스듬히·볼록하게 잘라 붓을 눌러 넣은 자국을 만든다.
    # 수직으로 뚝 자르면 붓이 아니라 잘린 띠가 된다
    # ★상수 0.032 는 포물선 꼭짓점(-0.052^2/(4*0.030) = -0.0225)을 밀어 올린 값이다.
    #   이게 없으면 획이 x=0 에 딱 붙어 ClampToEdge 로 왼쪽 끝이 번진다
    ttc = np.clip(tt, -1.5, 1.5)
    start = 0.032 + 0.052 * ttc + 0.030 * ttc * ttc + 0.006 * (fine - 0.5) * 2
    live = (u[None, :] > start)

    # ── 갈필(dry brush) ──
    # 붓털을 **굵은** 가로줄무늬 노이즈로 만든다. 잘게 갈리면 붓털이 아니라 스캔선이 된다.
    # 뒤로 갈수록 문턱을 올려 가닥이 갈라지고, 바깥 털부터 먼저 끊긴다
    fiber = (0.58 * fbm2(H, W, 42, 8, rng, octaves=2)
             + 0.42 * fbm2(H, W, 104, 5, rng, octaves=2))
    dry = np.clip((u - 0.28) / 0.66, 0, 1) ** 1.05
    thr = 0.04 + 0.90 * dry[None, :] * (0.38 + 0.62 * np.clip(at, 0, 1.2))
    fiber_soft = np.clip((fiber - thr) / 0.04, 0, 1)

    inside = np.clip((edge - at) * hw[None, :] / 3.2, 0, 1) * live
    cov = inside * fiber_soft

    # 비백(飛白): 젖은 몸통에도 붓털 사이로 종이가 비쳐 나온 가는 흰 틈이 있어야 한다.
    # 이게 없으면 아무리 색을 잘 깔아도 "칠한 띠"지 "그은 붓"이 아니다
    # ★얇게. 문턱을 조금만 낮춰도 획이 두 동강 난다(한 번 데였다)
    # gw 를 너무 낮추면 틈이 자로 그은 수평선이 되어 스캔선처럼 보인다
    vein = fbm2(H, W, 58, 13, rng, octaves=2)
    vdry = np.clip((u - 0.05) / 0.90, 0, 1)
    cov *= 1.0 - np.clip((vein - (0.885 - 0.085 * vdry[None, :])) / 0.014, 0, 1)

    # 꼬리 뒤로 떨어져 나간 조각 몇 점
    for _ in range(46):
        uu = float(rng.uniform(0.62, 1.02))
        cxp = uu * (W - 1)
        cyp = float(np.interp(cxp, x, cy)) + float(rng.normal(0, np.interp(uu, ku, kw) * 0.85))
        rr = float(rng.uniform(1.5, 6.5))
        if not (0 <= cxp < W and 0 <= cyp < H):
            continue
        yy = np.arange(max(0, int(cyp - rr - 2)), min(H, int(cyp + rr + 3)))
        xx = np.arange(max(0, int(cxp - rr * 2.6)), min(W, int(cxp + rr * 2.6)))
        if len(yy) == 0 or len(xx) == 0:
            continue
        dy = (yy[:, None] - cyp) / rr
        dx = (xx[None, :] - cxp) / (rr * 2.4)
        cov[yy[0]:yy[-1] + 1, xx[0]:xx[-1] + 1] = np.maximum(
            cov[yy[0]:yy[-1] + 1, xx[0]:xx[-1] + 1],
            (dx * dx + dy * dy < 1.0).astype(np.float32))

    alpha = stepped_alpha(cov)

    # ── 색 계단 ──
    # ★"흰 심 + 가장자리로 갈수록 붉은 기운"이다. 붉은 띠가 넓으면 붓이 아니라
    #   불기둥이 된다. 그래서 흰색이 단면의 절반 가까이를 먹고, 붉은 계단은
    #   바깥 20% 안에서 몰아친다
    heat = np.interp(u, [0.0, 0.30, 0.52, 0.70, 0.86, 1.0],
                     [1.00, 0.96, 0.80, 0.62, 0.46, 0.36]).astype(np.float32)
    # 심을 살짝 위로 밀어 좌우 대칭을 깬다(붓은 한쪽이 더 마른다)
    shift = 0.13 * np.sin(u * 5.1 + 0.8) + 0.10 * (fbm1(W, 6, rng, octaves=2) - 0.5) * 2
    bt = np.clip(np.abs(tt - shift[None, :]) / np.maximum(edge, 1e-3), 0, 1)
    b = 1.0 - (1.0 - bt) * heat[None, :]
    b += 0.028 * (fbm2(H, W, 3, 40, rng, octaves=2) - 0.5) * 2      # 띠 경계도 손그림
    b = np.clip(b, 0, 1)

    rgb = band_color(b, [
        (0.44, C_WHITE), (0.57, F_CREAM), (0.67, F_GOLD2), (0.76, F_GOLD),
        (0.84, F_ORANGE), (0.90, F_EMBER), (0.96, F_RED), (1.00, F_BLOOD)])

    # 갓선: 띠를 가르는 가는 밝은 선 한 줄 (wave 텍스처의 서명 같은 요소)
    line = (np.abs(b - 0.615) < 0.010) & (cov > 0.3)
    rgb[line] = hexf(F_CREAM)

    # 알갱이
    body = (alpha > 200)
    speckle(rgb, alpha, body & (u[None, :] < 0.72), rng, 150, C_WHITE, size=2)
    speckle(rgb, alpha, body & (u[None, :] > 0.45), rng, 70, F_GOLD, size=2)
    speckle(rgb, alpha, body & (u[None, :] > 0.55), rng, 45, C_WHITE, size=1, jitter=22)

    rgb = bleed_rgb(rgb, alpha, iters=40, fill_hex=F_DARK)
    return save_rgba(path, rgb, alpha)


# ═════════════════════════════════════════════════════════════
# 2) hit_spark 512x512 — 타격 섬광
# ═════════════════════════════════════════════════════════════
def bake_hit_spark(path):
    S = 512
    rng = np.random.default_rng(4177)
    cx = cy = S / 2.0
    yy = np.arange(S, dtype=np.float32)[:, None] - cy
    xx = np.arange(S, dtype=np.float32)[None, :] - cx

    cov = np.zeros((S, S), np.float32)
    band = np.ones((S, S), np.float32)

    # 5가닥 + 짧은 곁가지 3가닥. 길이를 일부러 들쭉날쭉하게 둔다
    main = [(-1.45, 232, 30), (-0.35, 176, 24), (0.62, 244, 27),
            (1.78, 150, 21), (2.72, 208, 26)]
    sub = [(0.05, 96, 12), (2.15, 78, 10), (-2.55, 110, 13)]
    for ang, L, wmax in main + sub:
        ang += float(rng.uniform(-0.07, 0.07))
        dxs, dys = math.cos(ang), math.sin(ang)
        s = xx * dxs + yy * dys                    # 가닥 방향
        q = np.abs(-xx * dys + yy * dxs)           # 가닥 폭 방향
        sn = np.clip(s / L, -0.14, 1.0)
        # 뾰족한 바늘 모양. 끝으로 갈수록 급히 좁아진다
        half = wmax * np.clip(1.0 - np.clip(sn, 0, 1), 0, 1) ** 1.55
        half *= 0.55 + 0.45 * (1.0 + np.clip(-sn, 0, 1) * 2.2)
        # 가닥마다 손그림 흔들림
        wob = 1.0 + 0.30 * (fbm2(S, S, 26, 26, rng, octaves=2) - 0.5) * 2
        half = half * wob
        m = (s > -0.14 * L) & (s < L) & (q < half)
        c = np.clip((half - q) / 2.4, 0, 1) * m
        cov = np.maximum(cov, c)
        bb = np.clip(0.52 * (q / np.maximum(half, 1e-3)) + 0.80 * np.clip(sn, 0, 1) ** 1.25, 0, 1)
        band = np.where(c > cov * 0.999 - 1e-6, np.minimum(band, np.where(m, bb, 1.0)), band)

    # 가운데 불덩이: 완벽한 원이 아니라 찌그러진 별
    r = np.sqrt(xx * xx + yy * yy)
    th = np.arctan2(yy, xx)
    n = fbm1(720, 6, rng, octaves=3, loop=True)
    idx = ((th + math.pi) / (2 * math.pi) * 719).astype(int)
    core_r = 30.0 * (0.72 + 0.55 * n[idx]) + 9.0 * np.abs(np.cos(th * 2.5))
    cc = np.clip((core_r - r) / 2.4, 0, 1)
    cov = np.maximum(cov, cc)
    band = np.where(cc > 0.5, np.minimum(band, np.clip(r / np.maximum(core_r, 1e-3), 0, 1) * 0.5), band)

    # 튀어나간 잔불
    for _ in range(30):
        a = float(rng.uniform(0, 2 * math.pi))
        d = float(rng.uniform(96, 244))
        px, py = cx + math.cos(a) * d, cy + math.sin(a) * d
        rr = float(rng.uniform(1.4, 4.6))
        m = ((np.arange(S)[None, :] - px) ** 2 + (np.arange(S)[:, None] - py) ** 2) < rr * rr
        cov = np.maximum(cov, m.astype(np.float32))
        band = np.where(m, min(0.62, 0.20 + d / 420.0), band)

    alpha = stepped_alpha(cov)
    b = np.clip(band + 0.035 * (fbm2(S, S, 14, 14, rng, octaves=2) - 0.5) * 2, 0, 1)
    rgb = band_color(b, [
        (0.19, C_WHITE), (0.36, P_ICE), (0.54, P_SKY),
        (0.72, P_CYAN), (0.88, P_BLUE), (1.00, P_DEEP)])

    body = alpha > 200
    speckle(rgb, alpha, body, rng, 70, C_WHITE, size=1)
    speckle(rgb, alpha, body & (r > 70), rng, 40, P_ICE, size=1, jitter=8)

    rgb = bleed_rgb(rgb, alpha, iters=48, fill_hex=P_DEEP)
    return save_rgba(path, rgb, alpha)


# ═════════════════════════════════════════════════════════════
# 3) ink_drop 256x256 — 먹물 방울
# ═════════════════════════════════════════════════════════════
def bake_ink_drop(path):
    # ★★v99 (11-FX-B). 이 한 장이 "임팩트 주변 검은 타원 덩어리"의 정체였다.
    #   증거: 오너 판정지(v97_wave11/fx/SHEET_3COL_owner.jpg) v98 열 Z1·X 칸의
    #   30~45px 짜리 검은 타원 여덟 개. 정점 투영으로 못 박았다 —
    #   enemy.js spawnInkBurst 가 INK_PER_KILL=8 개를 이 텍스처로 그린다.
    #   옛 그림이 그렇게 읽힌 이유가 둘이었다:
    #     ① **속이 제일 어두웠다.** 색 계단이 안쪽 70% 를 F_INK(#280804, 거의 검정)로
    #        칠하고 밝은 붉은 기운을 테두리에만 뒀다 = 검은 덩이에 붉은 테.
    #        LOG 의 계약은 정반대다 - **속은 밝은 것이 주인, 먹은 바깥 한 겹**.
    #     ② 게다가 enemy.js 가 t.rgb * 0.62 로 한 번 더 눌러 화면 휘도가 10~25 였다.
    #   그래서 계단을 뒤집고(진홍 속 + 짙은 한 겹 테두리) 실루엣을 rad 54 -> 38 로
    #   줄였다. 처치 진홍 문법은 그대로다 - 오히려 main.js 의 처치 잔방울
    #   (uInkDark #7e1622)과 **같은 진홍**에 앉게 값을 역산했다(0.62 를 미리 나눴다).
    S = 256
    rng = np.random.default_rng(919)
    cx, cy = S / 2.0, S * 0.42          # 위쪽에 무게 중심. 아래로 튄다
    yy = np.arange(S, dtype=np.float32)[:, None] - cy
    xx = np.arange(S, dtype=np.float32)[None, :] - cx
    r = np.sqrt(xx * xx + yy * yy)
    th = np.arctan2(yy, xx)

    NA = 1024
    n1 = fbm1(NA, 5, rng, octaves=3, loop=True)
    n2 = fbm1(NA, 11, rng, octaves=2, loop=True)
    idx = ((th + math.pi) / (2 * math.pi) * (NA - 1)).astype(int)
    down = np.clip(np.sin(th), 0, 1)                     # 아래쪽(+y)일수록 1
    # 위는 둥글고 아래는 혀처럼 길게 튄다. 이 비대칭이 없으면 그냥 동그라미다
    tongue = np.clip(np.sin(th * 3.4 + 1.1), 0, 1) ** 1.8
    rad = 38.0 * (0.90 + 0.16 * n1[idx])
    rad *= 1.0 + 0.90 * down ** 1.2 * (0.28 * n2[idx] + 0.72 * tongue)
    rad *= 1.0 - 0.16 * np.clip(-np.sin(th), 0, 1)       # 위쪽은 눌러 둥글게
    cov = np.clip((rad - r) / 1.9, 0, 1)

    # 아래로 튄 방울들
    for _ in range(10):
        a = float(rng.uniform(0.18, math.pi - 0.18))
        d = float(rng.uniform(40, 84))
        px, py = cx + math.cos(a) * d * 0.92, cy + math.sin(a) * d
        rr = float(rng.uniform(2.6, 11.0)) * (1.0 - d / 190.0)
        if rr < 1.2:
            continue
        gy = np.arange(S)[:, None] - py
        gx = np.arange(S)[None, :] - px
        rr2 = rr * (0.85 + 0.30 * fbm1(NA, 4, rng, octaves=2, loop=True)[
            ((np.arctan2(gy, gx) + math.pi) / (2 * math.pi) * (NA - 1)).astype(int)])
        cov = np.maximum(cov, np.clip((rr2 - np.sqrt(gx * gx + gy * gy)) / 1.6, 0, 1))
    # 튄 자국으로 이어지는 굵은 실 (가늘면 긁힌 자국처럼 보인다)
    for _ in range(3):
        a = float(rng.uniform(0.45, math.pi - 0.45))
        L = float(rng.uniform(42, 76))
        dxs, dys = math.cos(a), math.sin(a)
        s = xx * dxs + yy * dys
        q = np.abs(-xx * dys + yy * dxs)
        half = np.clip(1.0 - s / L, 0, 1) ** 1.1 * float(rng.uniform(4.2, 7.0))
        cov = np.maximum(cov, ((s > 24) & (s < L) & (q < half)).astype(np.float32))

    alpha = stepped_alpha(cov)

    b = np.clip(r / np.maximum(rad, 1e-3), 0, 1)
    b += 0.05 * (fbm2(S, S, 9, 9, rng, octaves=2) - 0.5) * 2
    b = np.clip(np.where(cov > 0, b, 1.0), 0, 1)
    # ★v99. 계단을 **뒤집었다**. 속이 진홍이고 먹은 바깥 한 겹뿐이다.
    #   값은 enemy.js 의 t.rgb * 0.62 를 미리 나눠 둔 것이라, 화면에서는
    #   main.js 처치 잔방울(uInkDark #7e1622 / uInkCore #dc8a92)과 같은 집안에 앉는다.
    #   ★값은 **화면에서 역산**했다. 텍스처는 sRGB 로 읽히고 -> enemy.js 가 x0.62 ->
    #     ACES 톤매핑을 지난다. 붉은색은 ACES 를 지나며 특히 어두워져서, 순수한 진홍
    #     hex 를 그대로 적으면 화면 휘도가 20 안팎(= 검정)이 된다. 아래 괄호가 화면값이다.
    K_BODY = "EB6A78"    # 몸통 진홍 (화면 #A83A48 휘도 82 · 채도 0.66)
    K_DEEP = "B5505B"    # 한 단 짙게 (화면 #77202C 휘도 51)
    K_RIM = "7A323E"     # 바깥 한 겹 (화면 #3E0A14 휘도 22). 순검정을 쓰면 다시 검은 눈알이다
    K_SHEEN = "FFC4CE"   # 젖은 자리 갓선 (화면 #B68E95 휘도 151)
    rgb = band_color(b, [
        (0.62, K_BODY), (0.86, K_DEEP), (1.00, K_RIM)])
    # 젖은 자리가 빛을 받는 곳. 왼쪽 위에만 가는 밝은 선(갓선 문법 그대로)
    sheen = (np.abs(b - 0.50) < 0.045) & (np.cos(th + 2.3) > 0.45) & (alpha > 150)
    rgb[sheen] = hexf(K_SHEEN)

    body = alpha > 200
    speckle(rgb, alpha, body & (b > 0.62), rng, 18, K_DEEP, size=1)
    speckle(rgb, alpha, body, rng, 8, K_SHEEN, size=1, jitter=3)

    rgb = bleed_rgb(rgb, alpha, iters=48, fill_hex=K_DEEP)
    return save_rgba(path, rgb, alpha)


# ═════════════════════════════════════════════════════════════
# 4) ring_shock 512x512 — 충격 고리
# ═════════════════════════════════════════════════════════════
def bake_ring_shock(path):
    S = 512
    rng = np.random.default_rng(3355)
    cx = cy = S / 2.0
    # 완벽한 원이면 컴퍼스 티가 난다. 살짝 찌그러뜨리고 기울인다
    rot = 0.16
    ys = np.arange(S, dtype=np.float32)[:, None] - cy
    xs = np.arange(S, dtype=np.float32)[None, :] - cx
    ex = (xs * math.cos(rot) + ys * math.sin(rot)) / 1.00
    ey = (-xs * math.sin(rot) + ys * math.cos(rot)) / 0.90
    r = np.sqrt(ex * ex + ey * ey)
    th = np.arctan2(ey, ex)

    NA = 1440
    idx = ((th + math.pi) / (2 * math.pi) * (NA - 1)).astype(int)
    nr = fbm1(NA, 6, rng, octaves=3, loop=True)
    nw = fbm1(NA, 10, rng, octaves=3, loop=True)
    ng = fbm1(NA, 6, rng, octaves=2, loop=True)

    # 반지름이 각도마다 흔들린다. 매끈한 원이면 컴퍼스로 그린 티가 난다
    R = 196.0 * (0.93 + 0.13 * nr[idx])
    # 두께 4px ~ 20px. 이 편차가 있어야 "붓으로 한 번에 돌린 원"이 된다.
    # 편차를 너무 키우면 고리가 아니라 흩어진 조각으로 읽힌다
    Wd = 3.6 + 16.0 * (nw[idx] ** 1.5)
    d = np.abs(r - R)

    gap = (ng[idx] > 0.695)                             # 군데군데 끊김
    hard = (th > 1.74) & (th < 2.14)                    # 크게 한 군데 잘라낸다
    cov = np.clip((Wd - d) / 1.8, 0, 1)
    cov[gap | hard] = 0.0

    # 끊긴 자리 바깥으로 튄 파편 호
    for _ in range(7):
        a0 = float(rng.uniform(-math.pi, math.pi))
        span = float(rng.uniform(0.05, 0.20))
        rr = 196.0 * float(rng.uniform(1.06, 1.26))
        ww = float(rng.uniform(1.6, 4.6))
        da = np.abs(np.angle(np.exp(1j * (th - a0))))
        m = (da < span) & (np.abs(r - rr) < ww)
        cov = np.maximum(cov, m.astype(np.float32))
    # 튀는 알갱이
    for _ in range(26):
        a = float(rng.uniform(-math.pi, math.pi))
        dd = float(rng.uniform(210, 250))
        px, py = cx + math.cos(a) * dd, cy + math.sin(a) * dd * 0.92
        rr = float(rng.uniform(1.2, 3.6))
        m = ((np.arange(S)[None, :] - px) ** 2 + (np.arange(S)[:, None] - py) ** 2) < rr * rr
        cov = np.maximum(cov, m.astype(np.float32))

    alpha = stepped_alpha(cov)
    b = np.clip(d / np.maximum(Wd, 1e-3), 0, 1)
    b += 0.04 * (fbm2(S, S, 11, 11, rng, octaves=2) - 0.5) * 2
    b = np.clip(np.where(cov > 0, b, 1.0), 0, 1)
    rgb = band_color(b, [
        (0.46, C_WHITE), (0.63, F_CREAM), (0.78, F_GOLD2),
        (0.90, F_GOLD), (1.00, F_ORANGE)])

    body = alpha > 200
    speckle(rgb, alpha, body, rng, 44, C_WHITE, size=1)
    rgb = bleed_rgb(rgb, alpha, iters=56, fill_hex=F_DARK)
    return save_rgba(path, rgb, alpha)


# ═════════════════════════════════════════════════════════════
# 5) ground_detail 512x512 — 지면 디테일 (곱연산용 · 타일링)
# ═════════════════════════════════════════════════════════════
# 왜 필요한가: level1.glb 의 바닥은 2048px 한 장으로 96m 를 덮는다. 1m 가 21px 이라
# 카메라가 가까이 붙으면 흙바닥이 그냥 뿌옇게 뭉갠 얼룩으로 보인다. 이 한 장을
# 1.7m / 4.3m 두 주기로 겹쳐 **곱해서** 그 빈 자리를 메운다(web/level.js).
#
# ★위 네 장과 규칙이 다르다. 여기서 헷갈리면 바닥이 통째로 어두워지거나 줄이 간다.
#   1) 알파를 안 쓴다. 전부 255 다. 얹는 그림이 아니라 **재질의 결**이다
#   2) 평균이 정확히 0.5 여야 한다. 곱수가 1 + (v-0.5)*g 라 평균이 0.5 를 벗어나면
#      바닥 전체 밝기가 밀린다. 멀어져서 밉맵이 다 뭉개졌을 때 곱수가 정확히 1.0 로
#      수렴해야 "멀리는 원래 색 그대로"가 된다
#   3) 반드시 이어붙어야 한다(_tile_layers). fbm2 로 구우면 주기마다 격자선이 보인다
#   4) 색이 아니라 밝기다. three 쪽에서 colorSpace 를 건드리면 안 된다
#      (sRGB 로 읽으면 0.5 가 0.21 이 되어 바닥이 새까매진다)
#
# ★채널을 나눠 담는다(한 장을 두 벌처럼 쓰는 요령).
#   같은 그림을 1.7m 와 4.3m 로 두 번 읽어 겹치는데, 두 번 다 저주파가 세면
#   1.7m 짜리 큰 얼룩이 눈에 띄게 반복된다. 그래서
#     R = 저주파 위주 (넓은 흙 얼룩)  -> 넓은 주기(4.3m)로 읽는다
#     G = 고주파 위주 (잔결·알갱이)   -> 좁은 주기(1.7m)로 읽는다
#     B = 둘의 평균                   -> 채널을 안 고른 코드용 폴백
#   두 채널 다 평균이 0.5 여야 하는 건 똑같다.
def _fix_mean_std(x, std=0.165):
    """평균 0.5 · 표준편차 고정. 이 표준편차가 곱수의 폭을 정한다
    (level.js 가 uGDGain 을 곱하고 0.90~1.10 으로 자른다)"""
    x = (x - float(x.mean())) / max(float(x.std()), 1e-6) * std + 0.5
    x = np.clip(x, 0.02, 0.98)
    return x - (float(x.mean()) - 0.5)          # 자르면서 밀린 평균을 되돌린다


# ★★v90. 잔결의 진폭은 여기서 정한다. **level.js 의 DETAIL_GAIN 이 아니다.**
#   이유: web/*.js 는 이번 작업의 소유가 아니다(다른 에이전트가 붙어 있다).
#   셰이더가 하는 계산은  곱수 = 1 + (tex - 0.5) * uGDGain  이라 진폭이
#   **(텍스처의 0.5 대비 편차) x gain** 의 곱이다. 둘 중 아무거나 줄이면 결과가 같고,
#   평균 0.5 는 그대로라 "멀면 곱수 1.0 수렴" 계약도 한 톨도 안 깨진다.
#   그래서 게임에서 gain 사다리로 고른 값을 이 std 에 접어 넣는다.
#     실측: level.debug.detailGain() 사다리 0 / 0.06 / 0.12 / 0.20 / 0.38 (v90_ground)
#     결론: 게임 거리에서 0.12 가 상한. 그 위는 바닥이 자글거린다
#     접기:  std = 0.165 x (0.12 / 0.38) = 0.052
DETAIL_STD = 0.052
DETAIL_GAIN_SHIPPED = 0.38     # web/level.js 의 값. 바뀌면 위 계산을 다시 해라
DETAIL_GAIN_TARGET = 0.12      # 사다리로 고른 **실효** gain


def bake_ground_detail(path):
    """지면 잔결. ★v90 에서 **고주파를 통째로 들어냈다.**

    오너 판정: "바닥도 자글자글하니 이상하고."
    범인이 여기였다. 이 장은 1.7m 와 4.3m 두 주기로 읽히는데, 예전에는 그 안에
    109칸(1.3cm)·127칸(1.1cm) 짜리 층과 하드 엣지 자갈이 들어 있었다. 게임 거리
    (약 75px/m)에서 그건 1px 도 안 되는 잡음이라, 카메라가 움직일 때마다 밉 단계와
    이방성 표본이 픽셀마다 다르게 잡혀 **바닥이 끓는다.**

    규칙 A(최소 특징 25cm)를 이 장에도 그대로 건다. 512px 짜리 한 장을 두 주기로
    읽으므로 채널마다 상한이 다르다.
      R = 4.3m 로 읽는다 -> 1px = 8.4mm. 25cm = 30px -> 칸수 상한 17
      G = 1.7m 로 읽는다 -> 1px = 3.3mm. 25cm = 75px -> 칸수 상한 6
    ★상한이 빡빡한 쪽(G)이 기준이다. 여기 담긴 그림은 이제 "잔결"이 아니라
      **아주 완만한 밝기 물결**이다. 하는 일도 하나로 줄었다: 타일 격자가 1.6~2.4m
      주기로 나란히 서는 걸 다른 주기로 흐트러뜨리는 것.
    """
    S = 512
    rng = np.random.default_rng(20260905)

    # R 채널(4.3m 로 읽음). 3/7/15칸 = 143 / 61 / 29cm. 상한 17 안이다
    lo = _tile_layers(S, (3, 7, 15), rng, gain=0.60)
    # G 채널(1.7m 로 읽음). 2/4/6칸 = 85 / 43 / 28cm. 상한 6 을 안 넘는다
    hi = _tile_layers(S, (2, 4, 6), rng, gain=0.62)
    # 두 채널이 같은 자리에서 같이 어두워지면 얼룩이 배가 된다. 한쪽을 밀어 어긋내 둔다
    hi = _tile_warp(hi, S * 0.31, S * 0.17)

    lo = _fix_mean_std(lo, DETAIL_STD)
    hi = _fix_mean_std(hi, DETAIL_STD)
    mid = _fix_mean_std((lo + hi) * 0.5, DETAIL_STD)

    ch = []
    for x in (lo, hi, mid):
        q = np.uint8(np.clip(x, 0, 1) * 255 + 0.5)
        # 8bit 로 굳히면서 반올림이 평균을 밀 수 있다. 재서 한 번 되민다
        bias = 127.5 - float(q.mean())
        if abs(bias) > 0.02:
            q = np.uint8(np.clip(x + bias / 255.0, 0, 1) * 255 + 0.5)
        ch.append(q)
    rgb = np.stack(ch, axis=2).astype(np.float32) / 255.0
    alpha = np.full((S, S), 255, np.uint8)
    return save_rgba(path, rgb, alpha)


# ═════════════════════════════════════════════════════════════
# 검증 — 저장한 파일을 다시 열어 알파 구조를 실제로 재본다
# ═════════════════════════════════════════════════════════════
def verify(path):
    im = Image.open(path)
    a = np.asarray(im.convert("RGBA")).astype(int)
    al = a[..., 3]
    rgbmax = a[..., :3].max(axis=2)
    h, w = al.shape
    corners = [tuple(a[0, 0]), tuple(a[0, w - 1]), tuple(a[h - 1, 0]), tuple(a[h - 1, w - 1])]
    low = al < 64
    print("── %s  %s %s" % (os.path.basename(path), im.size, im.mode))
    print("   알파 min/max/mean            %d / %d / %.1f" % (al.min(), al.max(), al.mean()))
    print("   알파 히스토그램(8구간)       %s" % np.histogram(al, bins=8, range=(0, 256))[0].tolist())
    print("   a==0 비율 %.4f   a==255 비율 %.4f" % ((al == 0).mean(), (al == 255).mean()))
    print("   모서리 픽셀(RGBA)            %s" % (corners,))
    if (al == 0).any():
        z = a[..., :3][al == 0]
        print("   a==0 픽셀 RGB 평균/최소/최대 %s / %s / %s"
              % (z.mean(axis=0).round(1).tolist(), z.min(axis=0).tolist(), z.max(axis=0).tolist()))
        print("   a==0 인데 RGB 가 새까만 픽셀 %d개  <- 0 이어야 검은 링이 안 낀다"
              % int((z.max(axis=1) == 0).sum()))
    if low.any():
        print("   a<64 구간 RGB 최대 %s  <- 알파보다 크면 스트레이트 알파가 맞다"
              % a[..., :3][low].max(axis=0).tolist())
    print("   RGB>알파 픽셀 비율 %.4f  (premultiplied 면 0 이 나온다)"
          % (rgbmax > al).mean())
    return im


def verify_tile(path):
    """지면 디테일 전용 검증. 알파가 아니라 **평균·분산·이음매**를 잰다.

    이음매 판정: 왼끝 열과 오른끝 열은 타일링하면 **서로 붙는다.** 그 두 열의 차이를
    안쪽 이웃 열 511쌍의 차이 **분포 안에서** 본다. 한 쌍만 골라 비교하면 하필 그
    자리가 매끈해서 이음매가 나쁜 것처럼 보인다(실제로 한 번 속았다).
    상위 백분위로 튀면 그 자리에 선이 보인다는 뜻이다. 50% 아래면 안 보인다.
    """
    im = Image.open(path)
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    al = a[..., 3]
    print("── %s  %s %s" % (os.path.basename(path), im.size, im.mode))
    print("   알파 min/max                 %d / %d  <- 둘 다 255 여야 한다"
          % (al.min(), al.max()))
    for ci, cname in enumerate(("R 저주파(4.3m)", "G 고주파(1.7m)", "B 평균")):
        v = a[..., ci] / 255.0
        dcol = np.abs(np.diff(v, axis=1)).mean(axis=0)
        drow = np.abs(np.diff(v, axis=0)).mean(axis=1)
        seam_x = float(np.abs(v[:, 0] - v[:, -1]).mean())
        seam_y = float(np.abs(v[0, :] - v[-1, :]).mean())
        pct_x = float((dcol < seam_x).mean()) * 100.0
        pct_y = float((drow < seam_y).mean()) * 100.0
        print("   [%s] min/max/mean/std %.3f / %.3f / %.5f / %.4f   평균오차 %+.5f"
              % (cname, v.min(), v.max(), v.mean(), v.std(), v.mean() - 0.5))
        print("        이음매 가로 %.5f (백분위 %.1f%%) · 세로 %.5f (백분위 %.1f%%)"
              "   안쪽 이웃 평균 %.5f  <- 50%% 아래면 안 보인다"
              % (seam_x, pct_x, seam_y, pct_y, dcol.mean()))
    # 두 채널을 겹쳐 곱했을 때의 실제 밝기 폭
    lo = a[..., 0] / 255.0 - 0.5
    hi = a[..., 1] / 255.0 - 0.5
    m = np.clip(1.0 + (hi * 1.0 + lo * 0.72) * 0.55, 0.90, 1.10)
    print("   겹쳐 곱한 실제 곱수  min %.4f  max %.4f  mean %.5f  std %.4f"
          % (m.min(), m.max(), m.mean(), m.std()))
    return im


# ═════════════════════════════════════════════════════════════
# 미리보기 — 어두운 게임 화면 위에 가산합성으로 얹어 본다
# ═════════════════════════════════════════════════════════════
def _load_font(size):
    # ★한글이 들어가는 라벨이 있다. Arial 을 먼저 잡으면 전부 두부(네모)로 나온다
    for p in ("/System/Library/Fonts/AppleSDGothicNeo.ttc",
              "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def add_over(bg, tex, box, gain=1.0, mode="add"):
    """bg(RGB float 0..1) 위에 tex(RGBA PIL) 를 box=(x,y,w,h) 로 얹는다"""
    x, y, w, h = box
    t = tex.resize((max(1, w), max(1, h)), Image.LANCZOS)
    ta = np.asarray(t).astype(np.float32) / 255.0
    fg, al = ta[..., :3], ta[..., 3:4]
    H, W = bg.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return bg
    fg = fg[y0 - y:y1 - y, x0 - x:x1 - x]
    al = al[y0 - y:y1 - y, x0 - x:x1 - x]
    dst = bg[y0:y1, x0:x1]
    if mode == "add":
        bg[y0:y1, x0:x1] = np.clip(dst + fg * al * gain, 0, 1)
    else:
        bg[y0:y1, x0:x1] = dst * (1 - al) + fg * al
    return bg


def make_previews(paths):
    os.makedirs(OUT_DIR, exist_ok=True)
    tex = {k: Image.open(v).convert("RGBA") for k, v in paths.items()}

    # 게임 스크린샷 후보
    cands = [
        os.path.join(ROOT, "renders/history/v61_goblin_ingame/01_field_start.jpeg"),
        os.path.join(ROOT, "renders/history/v61_goblin_ingame/12_clear.jpeg"),
        os.path.join(ROOT, "renders/history/v64_final/PLAY_crowd.png"),
        os.path.join(ROOT, "renders/history/v64_final/PLAY_clear.png"),
    ]
    shots = [p for p in cands if os.path.exists(p)]
    out = []
    font = _load_font(26)
    small = _load_font(19)

    # (a) 낱장 합성: 스크린샷 위에 하나씩
    for i, (name, im) in enumerate(tex.items()):
        shot = Image.open(shots[i % len(shots)]).convert("RGB")
        shot = shot.crop((0, 0, min(1280, shot.width), min(800, shot.height)))
        bg = np.asarray(shot, np.float32) / 255.0
        W, H = shot.size
        if name == "brush_slash":
            add_over(bg, im, (int(W * 0.03), int(H * 0.28), int(W * 0.94), int(W * 0.94 * 0.25)), 1.0)
        elif name == "hit_spark":
            add_over(bg, im, (int(W * 0.34), int(H * 0.26), 340, 340), 1.0)
            add_over(bg, im, (int(W * 0.58), int(H * 0.46), 190, 190), 0.8)
        elif name == "ring_shock":
            add_over(bg, im, (int(W * 0.28), int(H * 0.30), 460, 460), 1.0)
        else:
            for k in range(7):
                s = 46 + k * 16
                add_over(bg, im, (int(W * (0.30 + 0.07 * k)), int(H * (0.36 + 0.045 * (k % 4))), s, s),
                         1.0, mode="over")
        img = Image.fromarray(np.uint8(bg * 255))
        d = ImageDraw.Draw(img)
        lbl = "%s  (%s)" % (name, "normal blend" if name == "ink_drop" else "additive")
        d.rectangle([10, 10, 12 + int(d.textlength(lbl, font=font)), 46], fill=(0, 0, 0))
        d.text((14, 14), lbl, font=font, fill=(255, 255, 255))
        p = os.path.join(OUT_DIR, "comp_%d_%s.png" % (i + 1, name))
        img.save(p)
        out.append(p)

    # (b) 처치 연출 합본: 한 장면에 다 얹어 본다
    shot = Image.open(shots[0]).convert("RGB").crop((0, 0, 1280, 800))
    bg = np.asarray(shot, np.float32) / 255.0
    add_over(bg, tex["ring_shock"], (330, 250, 420, 420), 0.85)
    add_over(bg, tex["brush_slash"], (60, 300, 1160, 290), 1.0)
    add_over(bg, tex["hit_spark"], (470, 300, 300, 300), 1.0)
    add_over(bg, tex["hit_spark"], (700, 420, 150, 150), 0.7)
    for k in range(10):
        s = 34 + (k * 13) % 60
        add_over(bg, tex["ink_drop"], (380 + k * 58, 400 + (k % 5) * 42, s, s), 1.0, mode="over")
    img = Image.fromarray(np.uint8(bg * 255))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 470, 46], fill=(0, 0, 0))
    d.text((14, 14), "kill fx mock  (slash + ring + spark + ink)", font=font, fill=(255, 255, 255))
    p = os.path.join(OUT_DIR, "comp_5_kill_mock.png")
    img.save(p)
    out.append(p)

    # (c) 4장 시트: 왼쪽=체크무늬 위 원본(알파 모양) / 오른쪽=어두운 맵 색 위 가산합성
    names = ["brush_slash", "hit_spark", "ink_drop", "ring_shock"]
    CELL_W, CELL_H, PAD, HDR = 600, 330, 34, 40
    boxes, hs = [], []
    for n in names:
        tw, th = tex[n].size
        s = min(CELL_W / tw, CELL_H / th)
        boxes.append((max(1, int(tw * s)), max(1, int(th * s))))
        hs.append(boxes[-1][1] + HDR + 26)
    CW = PAD * 3 + CELL_W * 2
    CH = PAD + sum(h + PAD for h in hs)
    ck = (np.indices((CH, CW)).sum(axis=0) // 16) % 2
    sheet = Image.fromarray(np.uint8(np.where(ck[..., None], 62, 46) * np.ones((1, 1, 3), np.uint8)))
    d = ImageDraw.Draw(sheet)
    yv = PAD
    for n, (bw, bh) in zip(names, boxes):
        im = tex[n]
        tw, th = im.size
        d.text((PAD, yv), "%s   %dx%d" % (n, tw, th), font=font, fill=(255, 255, 255))
        top = yv + HDR
        sc = im.resize((bw, bh), Image.LANCZOS)
        sheet.paste(sc, (PAD, top), sc)
        d.text((PAD, top + bh + 4), "straight alpha over checker", font=small, fill=(205, 205, 205))
        # 어두운 야생 맵 바닥색 위 합성. ink_drop 만 일반합성(먹은 발광하지 않는다)
        dark = np.tile(np.array([[[0.11, 0.13, 0.09]]], np.float32), (bh, bw, 1))
        add_over(dark, im, (0, 0, bw, bh), 1.0, mode="over" if n == "ink_drop" else "add")
        sheet.paste(Image.fromarray(np.uint8(dark * 255)), (PAD * 2 + CELL_W, top))
        d.text((PAD * 2 + CELL_W, top + bh + 4),
               "%s on dark map color" % ("normal" if n == "ink_drop" else "additive"),
               font=small, fill=(205, 205, 205))
        yv += HDR + bh + 26 + PAD
    p = os.path.join(OUT_DIR, "sheet_fx_tex.png")
    sheet.save(p)
    out.append(p)

    # (d) brush_slash 는 붓 결을 봐야 하니 어두운 바닥 위에 원본 해상도로 한 장 더
    im = tex["brush_slash"]
    tw, th = im.size
    dark = np.tile(np.array([[[0.09, 0.11, 0.08]]], np.float32), (th, tw, 1))
    add_over(dark, im, (0, 0, tw, tw * th // tw), 1.0)
    Image.fromarray(np.uint8(dark * 255)).save(
        os.path.join(OUT_DIR, "brush_slash_1to1_dark.png"))
    out.append(os.path.join(OUT_DIR, "brush_slash_1to1_dark.png"))
    # 꼬리 갈필 확대 (2배)
    crop = Image.fromarray(np.uint8(dark * 255)).crop((980, 90, 1620, 410))
    crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save(
        os.path.join(OUT_DIR, "brush_slash_tail_zoom.png"))
    out.append(os.path.join(OUT_DIR, "brush_slash_tail_zoom.png"))

    # (e) 확대 필터링 시험 — 알파 0 픽셀의 RGB 가 검으면 여기서 검은 링이 나온다.
    #     가장자리를 8배 쌍선형으로 늘려 중간 회색 위에 얹어 본다
    tiles, labels = [], []
    for n, box, mode in (("brush_slash", (0, 150, 90, 300), "add"),
                         ("hit_spark", (150, 150, 250, 250), "add"),
                         ("ink_drop", (70, 60, 150, 140), "over"),
                         ("ring_shock", (40, 150, 140, 250), "add")):
        c = tex[n].crop(box)
        big = c.resize((c.width * 8, c.height * 8), Image.BILINEAR)
        for gray in (0.34, 0.62):
            bgz = np.tile(np.array([[[gray, gray, gray]]], np.float32), (big.height, big.width, 1))
            add_over(bgz, big, (0, 0, big.width, big.height), 1.0, mode=mode)
            tiles.append(Image.fromarray(np.uint8(bgz * 255)))
            labels.append("%s  x8 bilinear  %s  bg %.2f" % (n, mode, gray))
    cw = max(t.width for t in tiles) + 20
    chh = max(t.height for t in tiles) + 50
    board = Image.new("RGB", (cw * 2, chh * 4), (18, 18, 20))
    dd = ImageDraw.Draw(board)
    for i, (t, lb) in enumerate(zip(tiles, labels)):
        cxp, cyp = (i % 2) * cw + 10, (i // 2) * chh + 34
        board.paste(t, (cxp, cyp))
        dd.text((cxp, cyp - 26), lb, font=small, fill=(240, 240, 240))
    p = os.path.join(OUT_DIR, "alpha_edge_filter_test.png")
    board.save(p)
    out.append(p)

    # (f) 결 맞춤 확인 — 기존 wave 텍스처와 나란히 놓고 같은 집안인지 본다
    olds = [os.path.join(TEX_DIR, "wave_water.png"), os.path.join(TEX_DIR, "wave_fire.png")]
    olds = [o for o in olds if os.path.exists(o)]
    if olds:
        rows2 = [(os.path.basename(o), Image.open(o).convert("RGBA")) for o in olds]
        rows2 += [(n + ".png", tex[n]) for n in ("brush_slash", "ring_shock", "hit_spark")]
        BW = 900
        items = []
        for n, im in rows2:
            bh = max(1, int(BW * im.height / im.width))
            items.append((n, im, bh))
        Hb = 40 + sum(h + 52 for _, _, h in items)
        board2 = Image.new("RGB", (BW + 60, Hb), (26, 30, 24))
        d2 = ImageDraw.Draw(board2)
        yv2 = 34
        for n, im, bh in items:
            dk = np.tile(np.array([[[0.11, 0.13, 0.09]]], np.float32), (bh, BW, 1))
            add_over(dk, im, (0, 0, BW, bh), 1.0, mode="over" if n.startswith("wave") else "add")
            board2.paste(Image.fromarray(np.uint8(dk * 255)), (30, yv2))
            d2.text((30, yv2 - 26), n, font=small, fill=(235, 235, 235))
            yv2 += bh + 52
        p = os.path.join(OUT_DIR, "style_match_vs_wave.png")
        board2.save(p)
        out.append(p)
    return out


# ═════════════════════════════════════════════════════════════
# 6) bush_leaf 512x512 — 수풀 앞잎 카드 (web/stealth.js)
#
# 무엇에 쓰는가
#   은신 중에 **캐릭터와 카메라 사이**에 세우는 잎 카드 한 장이다. 이게 없으면
#   쿼터뷰에서 캐릭터가 수풀 위에 올라선 그림이 된다(v72 QA 실증).
#
# ★알파가 곧 '잎의 순번'이다 — 이 장의 유일한 특이 규칙
#   카드가 통째로 나타났다 사라지면 스티커를 껐다 켜는 것으로 보인다. 잎이
#   **한 장씩** 돋고 한 장씩 지워져야 "잎이 갈라진다"로 읽힌다.
#   그래서 잎마다 임의의 순번을 정해 그 값을 알파(128~255)에 굽는다.
#   게임 셰이더는 `if (a < uCut) discard;` 한 줄로 컷을 훑어 올리면 되고,
#   uCut 을 0.50 -> 1.02 로 밀면 잎이 순번대로 사라진다.
#   = 알파는 투명도가 아니라 **순번**이다. 반투명 합성을 안 쓴다(불투명 패스에서
#     깊이를 쓰고 discard 만 한다. 그래야 궤적 이펙트를 잎이 정상적으로 덮는다).
#
# 잎 배치: 아래 가운데에서 위·바깥으로 뻗는다. 카드가 세로 빌보드라 이래야
#   "덤불 윗동아리"로 보인다. 가장자리는 성기게 둬서 컷이 올라갈 때 밖에서부터 지워진다.
# ═════════════════════════════════════════════════════════════
# 잎 색. props 수풀(#6fd143)보다 한 단 어둡고 진하다. 앞잎은 역광에 가까워
# 어두워야 뒤의 수풀 덩어리와 앞뒤가 갈린다(다 밝으면 한 덩어리로 뭉친다).
L_TIP = "8FD455"     # 잎끝 (제일 밝다)
L_MID = "5FA83A"     # 잎 몸통
L_BASE = "336B2A"    # 잎 밑동
L_VEIN = "A8DE72"    # 잎맥
L_DEEP = "1F4420"    # 카드 아래쪽 그늘


def bake_bush_leaf(path):
    S = 512
    rng = np.random.default_rng(20260812)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)

    rgb = np.zeros((S, S, 3), np.float32)
    alpha = np.zeros((S, S), np.float32)      # 0..1 (마지막에 순번 바이트로)

    # 잎 46장. 가운데(0.50, 0.56)에서 사방으로 퍼진다.
    # ★안쪽 잎이 순번이 높다(= 제일 먼저 돋고 제일 늦게 지워진다).
    #   그래야 컷을 올릴 때 **바깥에서부터** 성글어지고 심이 남는다.
    N = 46
    ox, oy = S * 0.50, S * 0.56
    for i in range(N):
        t = (i + 0.5) / N
        ring = t ** 0.60                           # 0(중심) ~ 1(바깥)
        rank = 1.00 - 0.48 * ring - 0.02 * rng.random()     # 1.00(중심) ~ 0.50(바깥)
        # 위쪽으로 조금 더 많이 뻗는다(덤불 윗동아리). 아래도 비우지는 않는다
        ang = rng.random() * 2 * np.pi
        ang = ang - 0.42 * np.sin(ang + np.pi / 2)          # 위·옆으로 쏠리게
        rad = S * (0.04 + 0.27 * ring) * (0.80 + 0.40 * rng.random())
        cx = ox + np.cos(ang) * rad * 1.20
        cy = oy + np.sin(ang) * rad * 1.00
        ln = S * (0.105 + 0.075 * rng.random()) * (1.10 - 0.26 * ring)   # 반길이
        wd = ln * (0.34 + 0.16 * rng.random())                            # 반폭
        # 잎이 뻗는 방향: 중심에서 바깥으로 + 흔들림
        la = ang + (rng.random() - 0.5) * 0.9
        ca, sa = float(np.cos(la)), float(np.sin(la))

        # 잎 로컬 좌표. u=길이(-1..1), v=폭
        dx, dy = xx - cx, yy - cy
        u = (dx * ca + dy * sa) / ln
        v = (-dx * sa + dy * ca) / wd
        # 살짝 휜다. 곧은 타원이면 플라스틱 잎이 된다
        v = v - 0.42 * u * u + 0.14
        # 양끝이 뾰족한 눈 모양. 폭 프로파일
        w = np.clip(1.0 - u * u, 0.0, 1.0) ** 0.62
        d = np.abs(v) / np.maximum(w, 1e-3)
        cov = np.clip((1.0 - d) / 0.16, 0.0, 1.0)
        cov[np.abs(u) > 1.0] = 0.0
        if cov.max() <= 0:
            continue

        # 알파 = 순번 x 가장자리 계단. 가장자리가 먼저 지워져 잎이 야위어 간다
        step = np.where(cov >= 0.86, 1.0, np.where(cov >= 0.50, 0.90,
                        np.where(cov >= 0.18, 0.78, 0.0)))
        a_i = rank * step
        m = a_i > alpha
        alpha[m] = a_i[m]

        # 색: 밑동 어둡고 끝이 밝다 + 잎맥 한 줄 + 잎마다 밝기 흔들림
        b = np.clip(u * 0.5 + 0.5, 0, 1)                       # 0 밑동 ~ 1 끝
        col = (hexf(L_BASE)[None, None, :] * (1 - b)[..., None]
               + hexf(L_MID)[None, None, :] * b[..., None])
        tip = np.clip((b - 0.62) / 0.38, 0, 1)
        col = col * (1 - tip)[..., None] + hexf(L_TIP)[None, None, :] * tip[..., None]
        vein = np.clip(1.0 - np.abs(v) / np.maximum(w * 0.20, 1e-3), 0, 1)
        col = col * (1 - vein * 0.55)[..., None] + hexf(L_VEIN)[None, None, :] * (vein * 0.55)[..., None]
        # ★세로 그늘은 **잎 단위**로 준다. 카드 전체에 세로 그라데이션을 곱하면
        #   뒤에서 평칠로 끊을 때 계단이 잎 결이 아니라 **화면 가로줄**로 생겨
        #   깨진 픽셀처럼 보인다(실측 1회).
        vs = 1.0 if cy < S * 0.50 else (0.84 if cy < S * 0.74 else 0.68)
        col *= (0.86 + 0.28 * rng.random()) * vs
        rgb[m] = col[m]

    # ★평칠로 끊는다. 이 맵은 통째로 MeshToonMaterial(셀 셰이딩)이라 부드러운
    #   그라데이션 잎을 얹으면 그 카드만 **다른 렌더러로 그린 것**처럼 뜬다.
    #   파일 앞머리의 "그라데이션을 쓰지 않는다. 밝기는 계단식" 규칙과 같은 결이다.
    _lum = np.array([0.2126, 0.7152, 0.0722], np.float32)
    lum = (rgb * _lum[None, None, :]).sum(axis=2)
    m = alpha > 0.02
    if m.any():
        lo, hi = float(np.percentile(lum[m], 4)), float(np.percentile(lum[m], 96))
        t = np.clip((lum - lo) / max(hi - lo, 1e-4), 0, 1)
        stops = [hexf(L_DEEP), hexf(L_BASE), hexf(L_MID), hexf(L_TIP), hexf(L_VEIN)]
        band = np.digitize(t, [0.16, 0.40, 0.68, 0.92])
        out = np.zeros_like(rgb)
        for i, c in enumerate(stops):
            out[band == i] = c
        rgb = np.where(m[..., None], out, rgb)


    # 아주 작은 밝은 알갱이(다른 이펙트 텍스처와 같은 문법). 잎 사이 반짝임
    a8 = np.uint8(np.clip(alpha, 0, 1) * 255 + 0.5)
    speckle(rgb, a8, alpha > 0.6, rng, 26, L_VEIN, size=1)
    alpha = a8.astype(np.float32) / 255.0

    # ★순번 알파는 128 밑으로 안 내려간다. 게임 컷이 0.50 에서 시작하므로
    #   128 미만 값이 있으면 그 픽셀은 영영 안 그려진다(=구멍).
    a = np.where(alpha > 0.02, np.clip(alpha, 0.502, 1.0), 0.0)
    alpha8 = np.uint8(a * 255 + 0.5)
    rgb = bleed_rgb(rgb, alpha8, iters=48, fill_hex=L_MID)
    return save_rgba(path, rgb, alpha8)


# ═════════════════════════════════════════════════════════════
# 7) 지면 타일 4장 512x512 — 스플랫 합성용 (곱연산 · 타일링)
# ═════════════════════════════════════════════════════════════
# 무엇인가: 바닥을 96m 한 장(2048px = 21px/m)으로만 덮으면 가까이서 결이 없다.
# 그래서 1.6~2.4m 마다 되풀이되는 작은 그림 네 장을 스플랫맵으로 골라 섞어 덮는다.
#   tile_grass  풀   (초원 연두)   web/level.js 에서 스플랫 R
#   tile_dirt   흙길 (따뜻한 황토)                    G
#   tile_stone  돌   (여울·폐허 창백 석재)            B
#   tile_dry    마른 풀 (금빛)                        A
#
# ★★이 넷은 "색"이 아니라 "비율"로 쓴다. 게임 셰이더가 하는 계산은
#      곱수 = mix( 1, 타일색 / 타일평균색, TILE_AMT )
#      최종색 = 베이스컬러(2048 구역색) x 곱수
#   이라 **평균이 정확히 맞아야** 다음 둘이 동시에 성립한다(mix 는 평균 1 을 안 건드리고
#   폭만 늘린다).
#     1) 멀어져서 밉맵이 다 뭉개지면 타일색 -> 타일평균색 이므로 곱수가 1.0 로 수렴
#        = 게임 거리에서는 지금 화면 톤이 한 톨도 안 바뀐다
#     2) 어떤 구역이든 곱수의 평균이 1 이라 "밝고 따뜻하면 걸을 수 있다" 색 규칙이
#        스플랫 때문에 깨질 수가 없다(구역 밝기의 평균이 보존된다)
#   ★그래서 게임은 이 png 의 평균색을 **로딩 때 직접 재서** 쓴다(web/level.js).
#     여기서 숫자를 적어 넘기지 않는다. 적어 넘기면 다시 구울 때마다 어긋난다.
#
# ★두 번째 규칙: **눈에 띄는 것을 타일에 넣지 마라.**
#   꽃 한 송이, 큰 돌 하나처럼 "저거 아까 봤는데" 소리가 나오는 물건은 2m 마다
#   되풀이되면 그 즉시 격자로 읽힌다. 눈에 띄는 것은 되풀이가 없는 2048 베이스컬러
#   (blender/s20_level1.py 의 꽃무리·이끼 얼룩)가 맡는다. 타일은 잔결만 맡는다.
#
# ★세 번째 규칙: 색은 계단이다(이 레포 텍스처 문법). v 라는 **스칼라 한 장**을 먼저
#   만들고 band_color 로 6단 평칠한다. 계단 뒤에 연속값을 곱하면 색이 수천 개로
#   불어나 png 도 커지고 그림체도 깨진다. 특징(갈라짐·자갈·이음매)은 전부 계단
#   **앞에서** v 를 밀거나 당겨서 넣는다.
#
# ═════ v90. "롤 같은 바닥" 재작업 ═══════════════════════════
# 오너 판정 두 줄이 이 절을 통째로 다시 쓰게 했다.
#   ① "바닥이 롤 같은 느낌이 나야지. 무조건 흙바닥이 아니라 좀 깔끔하게."
#   ② "바닥도 자글자글하니 이상하고."
#
# ★진단(전 렌더 renders/history/v90_ground/BEFORE_*.png)
#   - 풀 타일이 소용돌이 각도장(_tile_flow)을 따라 문질러져서 **이끼 카펫**으로 읽혔다
#   - 흙길이 주 동선 전부를 덮어 맵 전체가 흙탕이었다
#   - 잎·알갱이·자갈이 3~13cm 짜리라 게임 거리(약 75px/m)에서 1~2px 이 된다.
#     밉맵이 뭉개기 직전 크기라 카메라가 움직일 때마다 **자글거린다**
#
# ★그래서 규칙 두 개를 새로 못 박는다.
#
#   [규칙 A] 최소 특징 크기 25cm. 이보다 잔 것은 **그리지 않는다.**
#     게임 거리에서 25cm 는 19px 이다. 그 아래는 화면에서 결이 아니라 지글거림이 된다.
#     _tile_layers 의 칸수 상한이 여기서 자동으로 나온다:  칸수 <= 주기(m) / 0.25
#     주기 2.1m -> 8칸, 1.7m -> 6칸, 1.6m -> 6칸, 2.4m -> 9칸.
#     아래 바커들은 이 상한을 절대 안 넘고, 검증이 넘었는지 다시 잰다.
#     ★예외는 판석 이음매 하나뿐이다. 그건 잡음이 아니라 **격자 위의 규칙적인 선**이라
#       밉맵이 평균내면 균일한 옅은 어두움으로 수렴한다(위상이 안 흔들려서 안 긴다).
#
#   [규칙 B] 큰 면적은 평칠. 잔결이 아니라 **큰 붓 두세 값**으로 면을 만든다.
#     비율의 표준편차(_fit_ratio 의 std)를 확 낮췄다. 게임이 이 폭을 TILE_AMT 1.9 로
#     늘려 쓰기 때문에 여기서 0.18 이면 화면에서는 ±34% 다 = 얼룩덜룩.
#
# 크기: 1024 로 올렸다. 주기 1.6~2.4m 이므로 화면에 430~640px/m 로 깔린다.
# ★해상도를 올린 이유가 "더 잘게 그리려고"가 아니다. 정반대다. 특징을 25cm 이상으로
#   키우면서 그 특징의 **가장자리**가 계단지지 않게 하려는 것이다.
TILE_S = 1024
MIN_FEAT_M = 0.25          # 최소 특징 크기(m). 규칙 A


def _cells_max(period_m):
    """이 주기의 타일에서 규칙 A 를 지키는 _tile_layers 칸수 상한"""
    return int(period_m / MIN_FEAT_M)


# 풀 — 봄 초원. 바닥 팔레트 K_OPEN(0xaabc6b) 과 같은 집안.
# ★v90. 계단을 좁히고 채도를 눌렀다. 계단이 넓으면 그게 그대로 얼룩이 된다.
GR_SHADE = "44622E"  # 포기 밑 그늘 (드물게만)
GR_DARK = "578038"
GR_MID = "689342"    # ← 면적의 주역
GR_LEAF = "78A54D"
GR_LIT = "8BB85E"

# 흙 — 다져진 흙. ★v90 에서 주 동선 자리를 판석에 넘기고 **캠프·샛길 보조**로 강등.
#   채도를 확 낮췄다(황토 -> 회갈색). 길이 아니라 "밟혀 풀이 죽은 자리"의 색이다.
DR_SHADE = "5D4E3C"
DR_DARK = "77664F"
DR_MID = "8E7C62"    # ← 면적의 주역
DR_WARM = "A18E73"
DR_LIT = "B4A287"

# 마른 풀 — 금빛. 초원에 **다른 주기**로 섞여 되풀이를 깨는 게 유일한 일이다.
# ★v90. 풀과 값이 너무 벌어지면 초원이 두 색 얼룩으로 읽힌다. 톤을 풀 쪽으로 당겼다.
DY_SHADE = "6E6238"
DY_DARK = "8A7C45"
DY_MID = "A08F52"    # ← 면적의 주역
DY_STRAW = "B5A262"
DY_LIT = "C7B676"

# 판석 파빙 — ★v90 신규. 주 동선(스폰-중앙-보스 어귀)과 여울목이 이걸 깐다.
# ★슬롯 사정: 스플랫 채널은 넷뿐이고 그 배정은 web/level.js(다른 에이전트 소유)에
#   R=grass G=dirt B=stone A=dry 로 박혀 있다. 그래서 **B 채널(tile_stone.png)의
#   내용물**을 젖은 자갈에서 판석 파빙으로 갈아끼웠다. 파일 이름은 계약이라 그대로 둔다.
#   여울목·폐허·바위 발치가 전부 이 채널이라 세계관도 맞는다(무너진 산사 터의 박석).
PV_JOINT = "5F6459"  # 줄눈 (가늘게)
PV_DARK = "868B7E"
PV_MID = "9DA294"    # ← 면적의 주역
PV_LIT = "B0B5A7"
PV_PALE = "C2C7B9"
PV_WEAR = "D2D6C9"   # 모서리 마모. 밟혀 닳아 볕을 받는 면
PV_MOSS = "6E7B60"   # 줄눈 이끼 (아주 드물게)


def _fit_ratio(rgb, ref, std=0.175, hue_keep=0.60, floor=None):
    """타일을 '곱수'로 쓰기 좋게 다듬는다.

    ref  이 타일의 평균색이 될 값. 게임은 이걸 png 에서 직접 재므로 여기서는
         "너무 어두운 채널을 안 만든다"가 목적이다. 평균이 0.2 인 채널이 있으면
         그 채널만 곱수가 5배로 흔들려서 바닥이 색 튄다.
    std  비율의 표준편차. 곱수의 세기다. 0.175 면 곱수가 대체로 0.65~1.35 다.
    hue_keep  칠한 **색 계단**을 밝기 대비 얼마나 남길지. 1.0 이면 칠한 그대로,
         0.0 이면 순수 명암만 남는다. 0.6 이면 색이 살아 있으면서도
         베이스컬러의 구역 색을 안 밀어낸다.
    floor ★v90 신규. 비율의 **하한**(예: 0.70 = 평균의 70% 아래로는 안 내려간다).

         왜 필요한가: 게임은 이 비율을 그대로 안 쓰고 mix(1, 비율, TILE_AMT=1.9) 로
         **폭을 1.9배 늘려** 쓴다. 그래서 화소 몇 %만 극단으로 어두워도 늘린 곱수가
         게임의 안전망(TILE_MIN 0.28)에 닿는다. 닿는 순간 그 자리만 "평균 1" 계약이
         깨져서 줄눈이 시커먼 구멍이 된다(판석 파빙에서 실제로 2.17% 가 닿았다).
         하한은 **하드 클립**이다. 부드럽게 눌러 봐야 줄눈이 흐리멍덩해질 뿐이고,
         줄눈 속은 원래 한 값으로 평칠된 자리라 잘려도 그림이 안 상한다.
    """
    ref = np.asarray(ref, np.float32)
    m = rgb.reshape(-1, 3).mean(0)
    r = rgb / np.maximum(m, 1e-4)              # 채널 평균이 1 인 비율
    d = r - 1.0
    db = d.mean(axis=2, keepdims=True)         # 밝기 성분
    d = db + (d - db) * hue_keep               # 색 성분만 줄인다
    d *= std / max(float(d.std()), 1e-6)
    if floor is not None:
        d = np.maximum(d, floor - 1.0)
    out = ref[None, None, :] * (1.0 + d)
    # 0..1 로 자르면서 평균이 밀린다. 몇 번 되민다(게임이 실측하므로 완벽할 필요는 없다)
    for _ in range(4):
        out = np.clip(out, 0.0, 1.0)
        cur = out.reshape(-1, 3).mean(0)
        out = out * (ref / np.maximum(cur, 1e-4))[None, None, :]
    return np.clip(out, 0.0, 1.0)


def bake_tile_grass(path):
    """깨끗한 초원. **큰 붓 세 값 평칠 + 드문 포기 그림자.**

    ★v90 에서 소용돌이(_tile_flow 각도장)를 통째로 뺐다. 각도장을 한 바퀴 반 돌리면
      잎이 예뻐 보일 것 같지만, 그 결과는 게임 거리에서 잎이 아니라 **이끼 카펫**이다.
      롤 지면의 풀은 붓결이 아니라 큰 면이고, 결은 면과 면 사이에만 있다.
    주기 2.10m / 1024px -> 1px = 2.05mm.  규칙 A 상한 = 2.10/0.25 = 8칸.
    """
    S = TILE_S
    rng = np.random.default_rng(20260901)
    cmax = _cells_max(2.10)                       # = 8

    # 큰 붓. 70cm(3칸) 와 42cm(5칸) 두 겹이 면의 골격이다
    field = _tile_layers(S, (3, 5), rng, gain=0.66)
    # 26cm(8칸) 한 겹만 얹어 면 안에 결을 준다. 이보다 잘면 규칙 A 위반
    patch = _tile_layers(S, (cmax,), rng, gain=1.0)
    v = 0.72 * field + 0.28 * patch

    # 포기 그림자. 42cm 격자에 절반만, 반지름 14cm 짜리 부드러운 원.
    # ★고르게 뿌리면 물방울무늬가 된다. 저주파로 자리를 골라 뭉치게 둔다
    f1, _f2, cid = _tile_cells(S, 5, rng, jitter=0.62)
    pick = rng.random(25).astype(np.float32)[cid]
    where = _tile_layers(S, (3,), rng, gain=1.0)
    rad = (S / 5.0) * 0.46
    clump = (1.0 - _smooth(f1, rad * 0.18, rad)) * (pick > 0.52) * (where > 0.42)
    v -= 0.20 * clump
    v = _norm01(v)

    # 세 값이 주역(DARK / MID / LEAF), 그늘과 볕은 가장자리에서만 나온다.
    # ★MID 를 제일 넓게(30%) 잡아 "한 덩이로 읽히는 면"을 만든다
    rgb = band_color(v, [(0.11, GR_SHADE), (0.36, GR_DARK), (0.70, GR_MID),
                         (0.91, GR_LEAF), (1.00, GR_LIT)])
    # std 0.180 -> 0.105. 게임이 TILE_AMT 1.9 로 늘려 쓰므로 화면에서는 ±20% 다
    rgb = _fit_ratio(rgb, (0.44, 0.55, 0.36), std=0.105, hue_keep=0.45)
    return save_rgb(path, rgb)


def bake_tile_dirt(path):
    """다져진 흙. ★v90 에서 **주 동선 자리를 판석에 넘기고 보조로 강등**했다.

    이제 이 결이 깔리는 곳은 캠프 반경(요괴 무리가 밟아 놓은 자리)·보스 마당·둔덕과
    포장 가장자리의 닳은 띠뿐이다. 그래서 "길"처럼 보일 필요가 없다 = 방향(밀린 결)도,
    자갈도, 갈라짐도 다 뺐다. **밟혀 풀이 죽은 균일한 면**이면 된다.
    채도도 확 낮췄다(황토 -> 회갈). 채도가 높으면 좁은 자리에서도 눈을 끈다.
    주기 1.70m / 1024px -> 1px = 1.66mm.  규칙 A 상한 = 1.70/0.25 = 6칸.
    """
    S = TILE_S
    rng = np.random.default_rng(20260902)
    cmax = _cells_max(1.70)                       # = 6

    blot = _tile_layers(S, (3, 5), rng, gain=0.66)     # 57cm / 34cm
    tread = _tile_layers(S, (cmax,), rng, gain=1.0)    # 28cm
    v = _norm01(0.74 * blot + 0.26 * tread)

    rgb = band_color(v, [(0.12, DR_SHADE), (0.36, DR_DARK), (0.68, DR_MID),
                         (0.90, DR_WARM), (1.00, DR_LIT)])
    rgb = _fit_ratio(rgb, (0.58, 0.51, 0.42), std=0.098, hue_keep=0.40)
    return save_rgb(path, rgb)


def bake_tile_dry(path):
    """마른 풀. 하는 일이 하나다: **초원의 되풀이를 다른 주기로 깨는 것.**

    ★v90. 그래서 그림 자체는 풀과 거의 같은 문법이어야 한다. 예전에는 누운 줄기를
      길게 문질러 놔서 초원에 섞이면 두 재질이 싸웠다(금빛 소용돌이 + 초록 소용돌이).
      톤을 풀 쪽으로 당기고 획을 없앴다. 주기만 다르면 제 몫은 다 한다.
    주기 2.40m / 1024px -> 1px = 2.34mm.  규칙 A 상한 = 2.40/0.25 = 9칸.
    """
    S = TILE_S
    rng = np.random.default_rng(20260903)
    cmax = _cells_max(2.40)                       # = 9

    sward = _tile_layers(S, (3, 5), rng, gain=0.66)    # 80cm / 48cm
    tuft = _tile_layers(S, (cmax,), rng, gain=1.0)     # 27cm
    v = 0.74 * sward + 0.26 * tuft

    # 성긴 자리(풀이 눕고 바닥이 비치는 곳). 풀 타일의 포기 그림자와 같은 문법.
    # ★원을 또렷하게 남기면 물방울무늬가 된다. 저주파로 세기를 흔들어 얼룩에 묻는다
    f1, _f2, cid = _tile_cells(S, 4, rng, jitter=0.60)
    pick = rng.random(16).astype(np.float32)[cid]
    rad = (S / 4.0) * 0.46
    thin = (1.0 - _smooth(f1, rad * 0.18, rad)) * (pick > 0.62)
    v -= 0.15 * thin * (0.4 + 1.2 * _tile_layers(S, (3,), rng, gain=1.0))
    v = _norm01(v)

    rgb = band_color(v, [(0.13, DY_SHADE), (0.38, DY_DARK), (0.68, DY_MID),
                         (0.90, DY_STRAW), (1.00, DY_LIT)])
    rgb = _fit_ratio(rgb, (0.60, 0.55, 0.38), std=0.100, hue_keep=0.42)
    return save_rgb(path, rgb)


def bake_tile_paved(path):
    """판석 파빙. ★v90 신규. **주 동선과 여울목이 이 결을 깐다.**

    파일 이름이 tile_stone.png 인 이유는 web/level.js 의 스플랫 채널 배정
    (R=grass G=dirt B=stone A=dry)이 계약이라서다. 내용물만 젖은 자갈에서
    판석 파빙으로 갈아끼웠다(그 파일을 고칠 권한이 이 작업에 없다).

    ── 판을 불규칙하게 만드는 법 ─────────────────────────────
    보로노이 격자를 두 벌 겹치면 이음매가 서로 충돌해 지저분해진다. 대신 한 벌을
    깔고 **이웃 칸끼리 확률로 합친다**(_merge_groups). 합쳐진 두 판 사이의 이음매는
    지운다 = 한 판이 두세 칸을 먹어 큰 판이 되고, 안 합쳐진 자리는 작은 판으로 남는다.
    이음매 격자는 여전히 한 벌이라 선이 깨끗하게 이어진다.

    ── 규칙 A 의 유일한 예외 ─────────────────────────────────
    줄눈은 4.7cm 라 25cm 보다 잘다. 그래도 안 자글거린다. 잡음이 아니라 **32cm 격자
    위의 규칙적인 선**이라 밉맵이 평균내면 위상이 안 흔들리고 균일한 옅은 어두움으로
    수렴하기 때문이다. 대신 어깨를 0.9cm 까지 부드럽게 깔아 하드 엣지를 안 만든다.
    주기 1.60m / 1024px -> 1px = 1.56mm.  판 = 4칸(40cm) 격자.
    """
    S = TILE_S
    rng = np.random.default_rng(20260904)
    K = 5                                          # 1.60/5 = 32cm 짜리 기본 판(규칙 A 안)
    # ★흩는 폭(jitter)이 크면 보로노이 칸이 별처럼 **오목해진다.** 실제 판석에는 오목한
    #   모서리가 없다(돌은 볼록하게 깨진다). 0.44 로 구웠더니 게임 화면에서 판석이
    #   아니라 "깨진 유약"으로 읽혔다(renders/history/v90_ground/ZOOM_ground_before_after.png).
    #   0.24 로 낮추면 사각·육각에 가까운 **놓은 돌**이 된다.
    f1, f2, cid, cid2 = _tile_cells2(S, K, rng, jitter=0.24)
    # ★합치는 확률을 낮게 잡아야 한다. K x K 가 25칸뿐이라 p 를 크게 주면 몇 번 만에
    #   **전부 한 무리**가 되어 줄눈이 통째로 사라진다(첫 굽기에서 실제로 그랬다.
    #   줄눈 화소가 2.7% 밖에 안 나왔다). 시도 2*25*0.20 = 10회 -> 무리 15개쯤 남는다
    grp = _merge_groups(K, rng, p=0.20, rounds=1)

    # 손으로 그은 것처럼 이음매를 흔든다. ★흔드는 노이즈도 규칙 A 를 지킨다(5칸=32cm).
    #   예전에는 53칸(3cm)으로 흔들어서 줄눈이 톱니처럼 지글거렸다
    wob = (_tile_layers(S, (3, 5), rng, gain=0.6) - 0.5) * (0.030 * S)
    raw = 1.0 - _smooth((f2 - f1) + wob, 0.006 * S, 0.030 * S)   # 폭 4.7cm, 어깨 0.9cm
    # 같은 무리로 합쳐진 두 판 사이의 이음매는 지운다 = 큰 판
    same = (grp[cid] == grp[cid2]).astype(np.float32)
    joint = raw * (1.0 - same)

    # 판마다 다른 밝기. ★무리 번호로 뽑아야 합쳐진 판이 한 값으로 칠해진다
    hv = rng.random(K * K).astype(np.float32)[grp[cid]]
    # ★결에 3칸(53cm) 층을 넣으면 안 된다. 타일 주기가 1.6m 라 그 큰 명암이 1.6m 마다
    #   되풀이돼서 긴 길에 **줄무늬 그림자**가 깔린다(첫 굽기에서 대각선 띠가 보였다).
    #   판 크기(32cm)와 같은 5칸 한 겹만 아주 옅게 얹는다
    grain = _tile_layers(S, (5,), rng, gain=1.0)                  # 32cm

    # 판마다 다른 밝기를 조금 더 벌린다. 판이 개별로 안 읽히면 그냥 금 간 회색 판이다
    v = 0.50 + (hv - 0.5) * 0.52 + (grain - 0.5) * 0.10 - joint * 0.60
    # 모서리 마모. 줄눈 **바로 바깥**만 밝힌다. 밟혀 닳아 볕을 받는 면이다.
    #   (줄눈 안쪽은 어둡고 그 테두리가 밝다 = 판이 도톰해 보인다)
    # ★모든 모서리를 똑같이 밝히면 판마다 흰 테두리가 둘려서 만화 외곽선처럼 보인다.
    #   저주파로 세기를 흔들어 **닳은 자리와 안 닳은 자리**를 만든다(53cm 얼룩).
    wear = _smooth(joint, 0.06, 0.34) * (1.0 - _smooth(joint, 0.34, 0.66))
    wear *= 0.35 + 1.30 * _tile_layers(S, (3,), rng, gain=1.0)
    v += 0.17 * wear
    v = np.clip(v, 0.0, 1.0)
    v = _norm01(v)

    rgb = band_color(v, [(0.12, PV_JOINT), (0.34, PV_DARK), (0.62, PV_MID),
                         (0.82, PV_LIT), (0.94, PV_PALE), (1.00, PV_WEAR)])
    # 줄눈 이끼. 물가·폐허라는 신호를 색으로 한 단만. ★넓게 깔면 초록 바닥이 되고
    #   여울목이 "건널 수 있는 밝은 띠"로 안 읽힌다. 저주파로 자리를 골라 뭉치게 둔다
    moss = (joint > 0.62) & (_tile_layers(S, (3, 6), rng, gain=0.5) > 0.700)
    rgb[moss] = hexf(PV_MOSS)
    print("   [판석] 무리 %d개 (칸 %d개에서 합침) · 줄눈 화소 %.1f%%"
          % (len(np.unique(grp)), K * K, float((joint > 0.55).mean()) * 100.0))
    # std 는 넷 중 유일하게 높게 둔다. 줄눈이 안 읽히면 포장이 아니라 회색 판이다.
    # ★floor 0.70 이 없으면 줄눈이 TILE_AMT 1.9 에 늘어나 게임 클램프를 뚫는다(위 주석)
    rgb = _fit_ratio(rgb, (0.60, 0.61, 0.58), std=0.125, hue_keep=0.42, floor=0.70)
    return save_rgb(path, rgb)


# 타일 주기(m). web/level.js 의 TILES[].period 와 같은 값이어야 한다.
# ★검증이 "게임 거리에서 몇 px 로 깔리는가"를 재려면 이 값이 필요하다.
# ★v96. web/level.js TILES 와 **같은 값이어야 한다**. 흙·판석 주기를 줄인 이유:
# 심사 "흙 텍스처 셀이 캐릭터 몸통만 하다". 주기를 줄이면 셀이 같은 비율로 작아진다.
# ★★v96-B. tile_stone 1.28 -> 2.75. 내용물이 **손바닥 파빙에서 판돌로** 갈렸다
#   (incoming/tiles_v2/slab.jpg). 조각 하나가 그림의 1/3 이므로 1.28m 에서는
#   화면에서 43cm 짜리 자갈이고, 그게 10차가 남긴 "잔균열 유약" 인상의 정체다.
#   2.75m 면 조각 하나가 **90cm** = 레퍼런스(롤) 길의 판돌과 같은 크기다.
#   ★web/level.js TILES[2].period 와 반드시 같이 옮겨야 한다(둘이 어긋나면 자가
#     "게임 거리 몇 px" 를 틀리게 잰다. 화면은 level.js 값만 따른다).
# ★v97. tile_dirt 1.32 -> 2.55 (흙이 "캠프 얼룩"에서 "길"로 역할이 바뀌었다).
#   ★web/level.js TILES[].period 와 반드시 같은 값이어야 한다. 하나만 고치면
#     화면은 level.js 를, 자는 이 표를 따르므로 자가 조용히 거짓말을 한다.
TILE_PERIOD = {"tile_grass": 2.10, "tile_dirt": 2.55, "tile_stone": 2.75, "tile_dry": 2.40}
GAME_PX_PER_M = 75.0        # 고정 쿼터뷰(pitch 0.86 / dist 24 / fov 24)의 실측 배율


def _wrap_box(a, k):
    """감아 도는 박스 블러(타일이므로 양끝이 이어진다). k 는 한 변의 픽셀 수"""
    if k <= 1:
        return a.astype(np.float32)
    n = a.shape[0]
    k = min(k, n)
    out = a.astype(np.float32)
    for ax in (0, 1):
        c = np.cumsum(np.concatenate([out, out, out], axis=ax), axis=ax, dtype=np.float32)
        sl = [slice(None), slice(None)]
        sl2 = [slice(None), slice(None)]
        sl[ax] = slice(n + k // 2, 2 * n + k // 2)
        sl2[ax] = slice(n + k // 2 - k, 2 * n + k // 2 - k)
        out = (c[tuple(sl)] - c[tuple(sl2)]) / k
    return out


def measure_tile_grain(path, name):
    """★v90 신규. "게임 거리에서 자글거리는가"를 숫자로 잰다.

    오너 판정("바닥도 자글자글하니 이상하고")을 눈이 아니라 값으로 재기 위한 것이다.
    두 가지를 잰다.

      잔결비   25cm 보다 **잔** 성분이 전체 분산에서 차지하는 비율.
               규칙 A 를 지켰으면 낮게 나온다. 이게 그대로 자글거림의 재료다.
      끓음     게임 거리(75px/m)까지 축소한 뒤 남는 이웃 픽셀 대비.
               밉맵이 뭉갠 뒤에도 남는 고주파라, 카메라가 움직일 때 픽셀이 들끓는
               정도와 같이 간다. 화면 밝기 기준 % 로 읽는다.
    """
    period = TILE_PERIOD.get(name, 2.0)
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0
    lum = a.mean(axis=2)
    S = lum.shape[0]

    feat_px = max(1, int(round(S / period * MIN_FEAT_M)))
    hf = lum - _wrap_box(lum, feat_px)
    hf_ratio = float(hf.std()) / max(float(lum.std()), 1e-6)

    # 게임 거리로 축소(박스 평균 = 밉맵이 하는 일). 그 뒤 이웃 차이가 '끓음'이다
    gpx = max(4, int(round(period * GAME_PX_PER_M)))
    step = max(1, S // gpx)
    small = _wrap_box(lum, step)[::step, ::step]
    boil = float(np.abs(np.diff(small, axis=1)).mean() + np.abs(np.diff(small, axis=0)).mean()) / 2.0
    print("   [자글] 25cm 미만 잔결비 %.3f  ·  게임거리 %dpx 축소 후 끓음 %.4f "
          "(화면 %.2f%%)  <- 낮을수록 깨끗" % (hf_ratio, gpx, boil, boil * 100.0))
    return {"hf_ratio": round(hf_ratio, 4), "boil": round(boil, 5), "game_px": gpx}


def verify_tile_rgb(path):
    """지면 타일 전용 검증. 게임이 이걸 '비율'로 쓰므로 재야 하는 것은 셋이다.
      1) 채널 평균 — 게임이 실측해 나누는 값. 너무 어두운 채널이 있으면 색이 튄다
      2) 비율의 폭 — 곱수가 실제로 얼마나 흔들리는가(클램프에 자주 닿으면 안 된다)
      3) 이음매 — 좌우/상하 끝 줄의 차이가 안쪽 이웃 1023쌍 분포에서 몇 %인가
    ★v90 에서 넷째가 붙었다: 자글거림(measure_tile_grain).
    """
    im = Image.open(path)
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255.0
    mean = a.reshape(-1, 3).mean(0)
    ratio = a / mean[None, None, :]
    ncol = len(np.unique(np.asarray(im.convert("RGB")).reshape(-1, 3), axis=0))
    print("── %s  %s %s  (%.0f KB)"
          % (os.path.basename(path), im.size, im.mode, os.path.getsize(path) / 1024.0))
    print("   평균색 R%.4f G%.4f B%.4f  (=%02X%02X%02X)  · 평칠 색 수 %d"
          % (mean[0], mean[1], mean[2],
             int(mean[0] * 255), int(mean[1] * 255), int(mean[2] * 255), ncol))
    print("   곱수(타일/평균)  min %.3f  max %.3f  mean %.4f  std %.4f"
          % (ratio.min(), ratio.max(), ratio.mean(), ratio.std()))
    # ★게임은 이 비율을 그대로 안 쓴다. mix(1, 비율, TILE_AMT) 로 **폭을 늘려** 쓴다
    #   (web/level.js 의 TILE_AMT. 선형 공간에서 곱하기 때문에 비율 1.18 이 화면에서는
    #   8% 밖에 안 되기 때문이다). 늘린 뒤에도 클램프에 안 닿아야 평균 1.0 계약이 산다.
    amt, lo, hi = 1.9, 0.28, 2.05   # web/level.js 의 TILE_AMT / TILE_MIN / TILE_MAX
    wide = 1.0 + (ratio - 1.0) * amt
    print("   TILE_AMT %.1f 로 늘린 곱수  min %.3f  max %.3f   클램프 %.2f~%.2f 밖 %.4f%%"
          "  <- 0 이어야 한다"
          % (amt, wide.min(), wide.max(), lo, hi,
             ((wide < lo) | (wide > hi)).mean() * 100.0))
    for ci, cn in enumerate("RGB"):
        v = a[..., ci]
        dcol = np.abs(np.diff(v, axis=1)).mean(axis=0)
        drow = np.abs(np.diff(v, axis=0)).mean(axis=1)
        sx = float(np.abs(v[:, 0] - v[:, -1]).mean())
        sy = float(np.abs(v[0, :] - v[-1, :]).mean())
        # ★평칠(색 계단) 텍스처는 안쪽 이웃 차이가 대부분 0 이라 백분위가 쉽게 90%%
        #   대로 튄다. 그래서 **안쪽 평균·최대와 나란히** 읽어야 한다.
        #   진짜 이음매는 안쪽 최대보다 크게 튄다. 최대 안쪽이면 그냥 평범한 한 쌍이다.
        print("   [%s] 이음매 가로 %.5f (백분위 %.1f%%) · 세로 %.5f (백분위 %.1f%%)"
              "   안쪽 이웃 평균 %.5f 최대 %.5f"
              % (cn, sx, float((dcol < sx).mean()) * 100.0,
                 sy, float((drow < sy).mean()) * 100.0,
                 float(dcol.mean()), float(max(dcol.max(), drow.max()))))
    return im


def make_tile_sheet(paths):
    """네 장을 3x3 으로 이어 붙여 한 장에 담는다. 이음매가 보이는지 눈으로 재는 그림"""
    os.makedirs(OUT_DIR, exist_ok=True)
    names = [n for n in ("tile_grass", "tile_dirt", "tile_stone", "tile_dry") if n in paths]
    if not names:
        return []
    cellpx = 384
    sheet = Image.new("RGB", (cellpx * len(names), cellpx + 26), (18, 18, 20))
    dr = ImageDraw.Draw(sheet)
    fnt = _load_font(15)
    for i, n in enumerate(names):
        t = Image.open(paths[n]).convert("RGB")
        # 3x3 으로 깔고 가운데를 잘라낸다. 이음매가 그림 안쪽으로 들어와야 눈에 띈다
        big = Image.new("RGB", (t.width * 3, t.height * 3))
        for yy in range(3):
            for xx in range(3):
                big.paste(t, (xx * t.width, yy * t.height))
        crop = big.crop((int(t.width * 0.5), int(t.height * 0.5),
                         int(t.width * 2.5), int(t.height * 2.5)))
        sheet.paste(crop.resize((cellpx, cellpx), Image.LANCZOS), (i * cellpx, 26))
        dr.text((i * cellpx + 8, 6), "%s  (2x2 타일링)" % n, font=fnt, fill=(220, 220, 210))
    out = os.path.join(OUT_DIR, "tile_sheet.png")
    sheet.save(out)
    return [out]


# 화면에 얹는 이펙트 네 장. 미리보기 합성은 이 넷만 한다
# (ground_detail 은 얹는 그림이 아니라 바닥 재질의 결이라 합성 대상이 아니다)
FX_SET = ("brush_slash", "hit_spark", "ink_drop", "ring_shock")
# 지면 타일 네 장. 검증이 다르다(알파가 아니라 평균·비율·이음매를 잰다)
TILE_SET = ("tile_grass", "tile_dirt", "tile_stone", "tile_dry")

BAKERS = (("brush_slash", bake_brush_slash),
          ("hit_spark", bake_hit_spark),
          ("ink_drop", bake_ink_drop),
          ("ring_shock", bake_ring_shock),
          ("ground_detail", bake_ground_detail),
          ("bush_leaf", bake_bush_leaf),
          ("tile_grass", bake_tile_grass),
          ("tile_dirt", bake_tile_dirt),
          # ★tile_stone.png 에 **판석 파빙**을 굽는다. 이름이 계약이라 못 바꾼다
          #   (web/level.js 의 채널 배정 R=grass G=dirt B=stone A=dry).
          ("tile_stone", bake_tile_paved),
          ("tile_dry", bake_tile_dry))


def main():
    os.makedirs(TEX_DIR, exist_ok=True)
    # --only=이름[,이름] 이면 그 장만 다시 굽는다. 멀쩡한 파일을 건드리지 않으려고 둔다
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = set(a[7:].split(","))
    paths = {}
    for name, fn in BAKERS:
        if only and name not in only:
            continue
        p = os.path.join(TEX_DIR, name + ".png")
        fn(p)
        paths[name] = p
        print("구움: %s (%d bytes)" % (p, os.path.getsize(p)))
    print()
    for name, p in paths.items():
        # 알파를 쓰는 장은 알파 구조를 재고(verify), 타일링 재질은 이음매를 잰다
        if name in FX_SET or name == "bush_leaf":
            verify(p)
        elif name in TILE_SET:
            verify_tile_rgb(p)
            measure_tile_grain(p, name)     # ★v90. 자글거림을 숫자로
        else:
            verify_tile(p)
        print()
    tiles = {k: v for k, v in paths.items() if k in TILE_SET}
    if tiles:
        tot = sum(os.path.getsize(v) for v in tiles.values())
        print("[예산] 지면 타일 %d장 합계 %.0f KB (상한 3072 KB)" % (len(tiles), tot / 1024.0))
    if "--tex-only" not in sys.argv:
        fx = {k: v for k, v in paths.items() if k in FX_SET}
        if len(fx) == len(FX_SET):
            for p in make_previews(fx):
                print("검증 이미지: %s" % p)
        for p in make_tile_sheet(tiles):
            print("검증 이미지: %s" % p)


if __name__ == "__main__":
    main()
