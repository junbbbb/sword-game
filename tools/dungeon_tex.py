# -*- coding: utf-8 -*-
"""컨셉 아트 `incoming/codex_dungeon/tiles_dungeon.png` 를 던전용 게임 텍스처로 만든다.

    python3 tools/dungeon_tex.py

원자재는 2048x2048 넉 장 붙은 시트다(오너 대리 합격판).

    좌상 = 이끼 낀 큰 판석 바닥      -> web/tex/dg_floor.png     (이어붙임)
    우상 = 석벽 블록                 -> web/tex/dg_wall.png      (이어붙임)
    좌하 = 금 간 바닥(변주)          -> web/tex/dg_floor_b.png   (이어붙임)
    우하 = 제단 메달리온(룬)         -> web/tex/dg_medallion.png (데칼. 알파 비네트)

같이 굽는 절차 텍스처(원자재에 없다. 조명 드라마용):

    web/tex/dg_pool.png       횃불 웜 풀 데칼(주황. 가장자리가 잡음으로 흔들린다)
    web/tex/dg_pool_cold.png  달빛 바닥 웅덩이(푸른. 타원)
    web/tex/dg_shaft.png      달빛 샤프트 콘의 옆면(위가 진하고 아래로 사라진다)
    web/tex/dg_flame.png      횃불 불꽃 스프라이트(물방울 모양. 심지가 희다)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
왜 원본을 그냥 못 쓰는가 — 세 가지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① **이음매.** 컨셉 그림은 되풀이를 전제로 안 그렸다. 그대로 깔면 2m 마다 격자
   줄이 보인다. tileize.py 의 Moisan periodic 분해를 그대로 빌려 쓴다
   (그림을 한 톨도 안 지우고 양끝만 맞춘다).

② **큰 명암 얼룩.** 원본은 한 장짜리 그림이라 가운데가 밝고 구석이 어둡다.
   되풀이하면 그 얼룩이 바둑판으로 깔린다. 아주 큰 커널로 저주파를 나눠서
   평평하게 만든다(돌결·이끼 같은 중고주파는 그대로 산다).

③ **어둡다.** 게임 재질 계약이 `화면색 = baseColorFactor x 타일 x 정점색` 이고
   baseColorFactor 는 1 을 못 넘는다(glTF 규격). 타일이 목표색보다 **밝아야**
   어두운 던전 팔레트를 만들 여유가 생긴다. 그래서 한 스칼라로 밝기만 올린다
   (채널별로 올리면 원본의 색기가 날아간다 - 색 보정은 재질 곱수가 한다).

★평균은 여기서 재서 `web/tex/dungeon_tex.json` 에 적어 둔다. 블렌더 파이썬에는
  PIL 이 없어서 s40 이 png 평균을 스스로 못 잰다(LOG.md 의 옛 함정).
"""
import os
import sys
import json
import math
import importlib.util

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "incoming", "codex_dungeon", "tiles_dungeon.png")
OUT_DIR = os.path.join(ROOT, "web", "tex")
META = os.path.join(OUT_DIR, "dungeon_tex.json")

# tileize.py 의 이음매 도구를 그대로 빌린다(같은 자로 재야 숫자가 비교된다)
_spec = importlib.util.spec_from_file_location(
    "tileize", os.path.join(ROOT, "tools", "tileize.py"))
_tz = importlib.util.module_from_spec(_spec)
sys.modules["tileize"] = _tz
_spec.loader.exec_module(_tz)

RES = 1024                 # 굽는 크기. 2m 타일 기준 512px/m 라 발밑에서도 안 뭉갠다
# 목표 sRGB 평균. 재질 곱수가 1 을 안 넘게 하는 하한(0.30 쯤)보다 넉넉히 위다.
# 너무 올리면 JPEG 로 구울 때 밝은 쪽이 뭉치므로 0.58 에서 멈춘다.
TARGET_MEAN = 0.58


def srgb_to_lin(a):
    a = np.asarray(a, np.float64)
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(a):
    a = np.clip(np.asarray(a, np.float64), 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def load_quads():
    im = Image.open(SRC).convert("RGB")
    w, h = im.size
    hw, hh = w // 2, h // 2
    box = {
        "floor":  (0, 0, hw, hh),
        "wall":   (hw, 0, w, hh),
        "floor_b": (0, hh, hw, h),
        "medallion": (hw, hh, w, h),
    }
    out = {}
    for k, b in box.items():
        q = im.crop(b).resize((RES, RES), Image.LANCZOS)
        out[k] = np.asarray(q, np.float32) / 255.0
    return out


def flatten_lowfreq(rgb, k, amount=0.80):
    """되풀이했을 때 바둑판으로 깔리는 **큰 명암 얼룩**만 나눠 없앤다.

    k 는 아주 크게 잡는다(그림 폭의 3/8). 작게 잡으면 판석 하나하나의 명암까지
    평평해져서 부조가 사라진다. amount 로 부분만 적용해 손그림 기운을 남긴다.
    ★wrap_blur 는 감아 도는 흐림이라 여기서 새 이음매가 안 생긴다.
    """
    base = _tz.wrap_blur(rgb, k, passes=2)
    g = base.mean(axis=2, keepdims=True)
    m = float(g.mean())
    corr = m / np.maximum(g, 1e-4)
    corr = 1.0 + (corr - 1.0) * amount
    return np.clip(rgb * corr, 0.0, 1.0)


def calm_fine(rgb, keep=0.72):
    """게임 거리에서 결이 아니라 **지글거림**으로 보이는 최고주파만 조금 누른다.

    3px 이하의 대역만 건드린다. 붓맛(중주파)은 그대로다.
    """
    lo = _tz.wrap_blur(rgb, 3, passes=2)
    return np.clip(lo + (rgb - lo) * keep, 0.0, 1.0)


# ═════════════════════════════════════════════════════════════
# 탈타일화 (13차C. 오너 "던전 타일도 너무 타일스럽고")
# ═════════════════════════════════════════════════════════════
# ★진단부터. "타일스럽다"의 기계적 정체는 밝기가 아니라 **색**이었다.
#     dg_floor 줄눈 L 0.585 vs 판석 L 0.610  = 밝기 차 -0.024 (거의 없다)
#     dg_floor 줄눈 초록초과 0.117 vs 전체 0.028 = **채도 차가 네 배**
#   즉 격자를 그리는 것은 그림자가 아니라 **산성 초록 그물**이다. 화면에서 눈은
#   그 그물을 먼저 잡고, 그게 4.5m 마다 되풀이되니 바둑판으로 읽힌다.
#   그래서 줄눈은 **색으로 지우고 밝기로 아주 조금만 남긴다** — 진짜 줄눈은
#   패인 자리라 어두운 게 맞고, 초록은 벽 밑동에만 있어야 컨셉과 같다.
def soften_grout(rgb, cut=0.030, keep=0.30, dark=0.105):
    """줄눈의 초록을 걷어내고 아주 옅은 그늘만 남긴다.

    cut  : 이 값 아래의 초록초과는 판석 자체의 색기라 안 건드린다
    keep : cut 위쪽 초록을 얼마나 남기는가(0.30 = 70% 걷어냄)
    dark : 걷어낸 자리를 얼마나 어둡게 눌러 '패인 줄'로 만드는가
           ★0.05 는 너무 옅어서 줄눈이 **떠 보였다**(색만 빠지고 깊이가 안 생겼다).
             0.105 면 판석이 위로 솟고 줄눈이 패인다 = 오너가 말한 '3D'가 여기서 난다.
    """
    R, G, B = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    ge = G - np.maximum(R, B)                       # 초록 초과(줄눈 이끼의 지문)
    over = np.maximum(0.0, ge - cut)
    out = rgb.copy()
    out[:, :, 1] = G - over * (1.0 - keep)          # 초록만 끌어내린다
    # 걷어낸 만큼만 밝기를 눌러 **얇은 그늘**로 바꾼다(전체 대비는 오히려 내려간다)
    sh = 1.0 - np.clip(over / max(1e-6, float(over.max())), 0, 1) * dark
    return np.clip(out * sh[:, :, None], 0.0, 1.0)


def pull_chroma(rgb, amount):
    """알베도의 채도를 끌어내린다 — **색은 빛이 칠한다**는 문법.

    ★컨셉(concept_hall.png)의 바닥은 그 자체로는 회갈색이고, 화면의 파랑·주황은
      전부 조명이 얹은 것이다. 우리 타일은 알베도가 이미 청록으로 물들어 있어서
      횃불 주황이 얹혀도 잘 안 데워졌다(채도 높은 파랑이 주황을 밀어낸다).
      휘도는 그대로 두고 색기만 뺀다.
    """
    g = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1]
         + 0.0722 * rgb[:, :, 2])[:, :, None]
    return np.clip(g + (rgb - g) * (1.0 - amount), 0.0, 1.0)


def normalize_mean(rgb, target=TARGET_MEAN):
    """한 **스칼라**로 밝기만 올린다(채널별로 하면 원본 색기가 지워진다).

    선형에서 곱하고 sRGB 평균이 target 이 되는 배수를 이분법으로 푼다.
    """
    lin = srgb_to_lin(rgb)
    lo, hi = 0.05, 40.0
    for _ in range(60):
        mid = (lo + hi) * 0.5
        got = float(lin_to_srgb(lin * mid).mean())
        if got < target:
            lo = mid
        else:
            hi = mid
    k = (lo + hi) * 0.5
    return np.clip(lin_to_srgb(lin * k), 0.0, 1.0), k


def save_rgb(name, rgb):
    """알파가 없는 타일은 **jpg 로도** 굽는다.

    ★블렌더 glTF 익스포터를 `export_image_format="AUTO"` 로 돌려야 알파 텍스처
      (웜 풀·달빛·불꽃·메달리온)가 PNG 로 살아남는다. 그런데 AUTO 는 불투명 텍스처도
      원본 형식을 그대로 물고 가므로, 큰 석재 타일을 png 로 두면 glb 가 통째로 부푼다.
      그래서 **불투명은 jpg 로 저장해 두고 블렌더가 그걸 읽게** 한다(png 는 눈 검사용).
    """
    p = os.path.join(OUT_DIR, name + ".png")
    im8 = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(im8).save(p)
    Image.fromarray(im8).save(os.path.join(OUT_DIR, name + ".jpg"),
                              quality=92, subsampling=0)
    lin = srgb_to_lin(rgb).reshape(-1, 3).mean(axis=0)
    srgb = rgb.reshape(-1, 3).mean(axis=0)
    print("   [저장] %-14s sRGB평균 #%02x%02x%02x · 선형 %.4f %.4f %.4f"
          % (name, int(srgb[0] * 255), int(srgb[1] * 255), int(srgb[2] * 255),
             lin[0], lin[1], lin[2]))
    return [float(x) for x in lin]


def _grout_stat(rgb):
    """줄눈이 얼마나 튀는가. 탈타일화의 before/after 를 재는 자다."""
    R, G, B = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    ge = G - np.maximum(R, B)
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    m = ge > np.percentile(ge, 80)
    return {"ge": round(float(ge[m].mean()), 4),
            "geStd": round(float(ge.std()), 4),
            "chroma": round(float((rgb.max(axis=2) - rgb.min(axis=2)).mean()), 4),
            "lumDelta": round(float(L[m].mean() - L[~m].mean()), 4),
            "lumStd": round(float(L.std()), 4)}


def save_rgba(name, rgb, alpha):
    p = os.path.join(OUT_DIR, name + ".png")
    a = np.clip(alpha, 0, 1)
    px = np.dstack([np.clip(rgb, 0, 1), a])
    Image.fromarray((px * 255 + 0.5).astype(np.uint8)).save(p)
    print("   [저장] %-14s RGBA %dx%d · 알파평균 %.3f"
          % (name, rgb.shape[1], rgb.shape[0], float(a.mean())))


# ═════════════════════════════════════════════════════════════
# 절차 텍스처 (원자재에 없는 것들)
# ═════════════════════════════════════════════════════════════
def _vnoise(res, cells, seed):
    rs = np.random.RandomState(seed)
    g = rs.rand(cells + 1, cells + 1).astype(np.float32)
    g[-1, :] = g[0, :]
    g[:, -1] = g[:, 0]
    xs = np.linspace(0, cells, res, endpoint=False, dtype=np.float32)
    i0 = np.floor(xs).astype(np.int32)
    t = xs - i0
    t = t * t * (3 - 2 * t)
    a = g[i0][:, i0]
    b = g[i0 + 1][:, i0]
    c = g[i0][:, i0 + 1]
    d = g[i0 + 1][:, i0 + 1]
    tx, ty = t[None, :], t[:, None]
    return (a * (1 - ty) * (1 - tx) + b * ty * (1 - tx)
            + c * (1 - ty) * tx + d * ty * tx)


def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def bake_pool(res, stops, seed, squash=1.0, wob=0.20, core=0.22, amax=0.62,
              tail=0.62, rough=0.42):
    """바닥에 까는 **빛 웅덩이** 데칼.

    ★13차C 전면 재작. 오너 "불꽃 있으면 주변 밝아지는 효과는 왜 이리 이상하냐."
      옛 판이 스티커로 읽힌 기계적 원인은 실측으로 셋이었다.

        core90 0.375   알파가 최대의 90% 를 넘는 자리가 반경의 **37.5%**
                       = 가운데가 통째로 평평한 **원반**이다. 빛은 중심에서
                         바로 떨어지지 한동안 평평할 수가 없다
        edgeMaxSlope 1.157  그 평평한 판이 한 자리에서 뚝 떨어진다 = **테두리**
        NormalBlending + 알파 0.52  칠하는 순간 바닥돌의 52%가 **지워진다**
                       (빛이 아니라 물감이다. 이 한 줄이 제일 컸다 -
                        고치는 쪽은 web/level.js 의 가산 합성이다)

      그래서 프로파일을 **점광원의 2차 감쇠**로 다시 깐다. 평평한 코어가 없다.

          f = 1 / (1 + (r/core)^2)      점광원 그 자체(중심에서 바로 떨어진다)
          w = 카드 끝에서 0 이 되는 창   (안 자르면 사각 모서리에 계단이 보인다)

    ★가장자리는 **두 옥타브**로 흐트러뜨린다. 한 옥타브(옛 판)는 큰 물결이라
      매끈한 타원이 그대로 남았다. 잔 옥타브를 겹쳐야 윤곽선이 사라진다.
    ★꼬리만 갉는다. 중심까지 갉으면 심이 지저분해져서 '불'이 아니라 '얼룩'이 된다.

    stops : (심 · 중간 · 끝) 세 색. **반경**으로 섞는다(알파로 섞으면 amax 를
            건드리는 순간 전부 끝색이 된다 - 옛 판이 밟은 함정이다).
    """
    yy, xx = np.mgrid[0:res, 0:res].astype(np.float32) / (res - 1) * 2 - 1
    n1 = _vnoise(res, 5, seed)
    n2 = _vnoise(res, 13, seed + 37)
    r = np.sqrt(xx * xx + (yy * squash) ** 2)
    r = r * (1.0 + wob * (n1 - 0.5) * 2.0 + wob * 0.55 * (n2 - 0.5) * 2.0)
    r = np.maximum(r, 0.0)

    f = 1.0 / (1.0 + (r / max(1e-3, core)) ** 2) ** 1.10      # 2차 감쇠
    w = _smooth((1.0 - r) / max(1e-3, tail))                  # 카드 끝을 0 으로
    a0 = np.clip(f * w, 0.0, 1.0)
    # 꼬리(밝기 하위)만 잡음으로 갉아 **소멸선을 없앤다**
    tm = _smooth((0.42 - a0) / 0.42) ** 1.4
    a0 = a0 * (1.0 - tm * rough * (1.0 - _vnoise(res, 9, seed + 71)))
    a = np.clip(a0, 0, 1) * amax

    hot = np.array(stops[0], np.float32)      # 심 - 황백
    mid = np.array(stops[1], np.float32)      # 중간 - 주황
    tip = np.array(stops[2], np.float32)      # 끝 - 붉게 죽는다
    # ★색 램프는 **알파가 아직 보이는 구간 안에서** 다 돌아야 한다. 처음엔 램프를
    #   core*2.4 에 걸었는데 거기는 이미 알파가 0.12 라, 눈에 보이는 웅덩이가 통째로
    #   황백 한 색이 됐다(측정값 lumAtHalf 0.745 = 반밝기 자리가 아직 흰색).
    #   반밝기 자리(r = core)에서 이미 주황이어야 "황백 -> 주황 -> 소멸"이 읽힌다.
    t1 = _smooth(r / max(1e-3, core * 1.15))[:, :, None]
    t2 = _smooth((r - core * 1.15) / 0.42)[:, :, None]
    rgb = hot[None, None, :] * (1 - t1) + mid[None, None, :] * t1
    rgb = rgb * (1 - t2) + tip[None, None, :] * t2
    # 아주 옅은 결(빛이 돌바닥을 훑는 얼룩)
    rgb = np.clip(rgb * (0.92 + 0.16 * _vnoise(res, 9, seed + 71)[:, :, None]), 0, 1)
    return rgb, a


def bake_wall_glow(w, h, seed=8801):
    """횃불이 **벽을 타고 오르는** 자국. 13차C 신설.

    ★왜 정점색으로 못 하는가: 벽 상자는 seg 1.1m 로 잘려 있어서 정점 간격이 1m 다.
      횃불의 뜨거운 심(반경 0.45m)이 그 격자에 안 잡힌다. 벽을 0.6m 로 다시 자르면
      삼각형이 세 배가 되어 glb 예산(5MB)을 넘긴다. 그래서 **해상도를 텍스처가**
      들고, 정점색은 넓은 스필만 맡는다(둘이 역할을 나눈다).
    ★위로 길다. 불은 위로 올라가고 벽에 붙은 그을음·열도 위로 번진다. 좌우 대칭이지만
      세로로는 비대칭(아래 짧게 · 위로 길게)이어야 '빛'으로 읽힌다.
    """
    yy = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]     # -1 아래 / +1 위
    xx = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    n = _vnoise(max(w, h), 7, seed)[:h, :w]
    # 불꽃 자리는 카드의 아래쪽 1/3. 위로 갈수록 넓게 퍼지며 죽는다(연기 기둥 문법)
    # ★★첫 판은 위로 너무 길었다(1/0.92). 화면에서 벽에 **손전등을 비춘 띠**로
    #   읽혔다 - 컨셉의 벽 자국은 관솔을 감싸는 둥근 얼룩이고 위로 아주 조금만
    #   끌린다. 세로 배율을 0.92 -> 0.56 으로 줄이고 감쇠를 세워 심을 붙였다.
    y0 = -0.30
    up = np.clip((yy - y0) / 1.30, -1, 1)
    spread = 0.46 + 0.34 * np.clip(up, 0, 1) ** 0.80             # 위로 조금 벌어진다
    d = np.sqrt((xx / spread) ** 2 + (np.maximum(0.0, y0 - yy) / 0.34) ** 2
                + (np.maximum(0.0, yy - y0) / 0.56) ** 2)
    d = d * (1.0 + 0.24 * (n - 0.5) * 2.0)
    a = 1.0 / (1.0 + (d / 0.26) ** 2) ** 1.30
    a = a * _smooth((1.0 - np.abs(xx)) / 0.34) * _smooth((1.0 - np.abs(yy)) / 0.30)
    hot = np.array((1.00, 0.93, 0.76), np.float32)
    mid = np.array((1.00, 0.60, 0.24), np.float32)
    tip = np.array((0.86, 0.32, 0.10), np.float32)
    t1 = _smooth(d / 0.34)[:, :, None]
    t2 = _smooth((d - 0.34) / 0.55)[:, :, None]
    rgb = hot[None, None, :] * (1 - t1) + mid[None, None, :] * t1
    rgb = rgb * (1 - t2) + tip[None, None, :] * t2
    return np.clip(rgb, 0, 1), np.clip(a, 0, 1)


def bake_wear(res=256, seed=5501):
    """바닥 **마모·이끼 데칼** 넉 장(2x2 아틀라스). 13차C 신설.

    ★격자 리듬을 끊는 것은 명암 변주만으로는 모자란다. 되풀이 주기와 아무 상관 없는
      자리에 **비반복 얼룩**이 놓여야 눈이 주기를 못 센다(초원에서 메달리온이 한 그
      노릇이다). 넉 장인 이유: 한 장이면 그것 자체가 새 되풀이가 된다.

        0 통행 마모(반들반들. 밝고 누렇다)   1 습윤(어둡고 푸르다)
        2 이끼 침식(어둡고 초록)             3 마모 변주(작고 옅다)

    색은 알베도다(조명·정점색을 그대로 탄다). 알파가 모양이다.
    """
    half = res // 2
    yy, xx = np.mgrid[0:half, 0:half].astype(np.float32) / (half - 1) * 2 - 1
    tiles = []
    # (색, 알파상한, 덩어리 크기, 찌그러짐, 잡음 세기)
    spec = [((0.86, 0.80, 0.66), 0.62, 0.78, 1.25, 0.42),
            ((0.36, 0.40, 0.48), 0.55, 0.70, 0.85, 0.50),
            ((0.30, 0.44, 0.24), 0.60, 0.66, 1.00, 0.58),
            ((0.80, 0.76, 0.68), 0.42, 0.58, 0.80, 0.46)]
    for i, (col, amax, size, sq, nz) in enumerate(spec):
        n1 = _vnoise(half, 3, seed + i * 91)
        n2 = _vnoise(half, 7, seed + i * 91 + 13)
        n3 = _vnoise(half, 15, seed + i * 91 + 29)
        r = np.sqrt(xx * xx + (yy * sq) ** 2)
        # ★윤곽을 통째로 잡음으로 민다. 원형이 남으면 그게 또 스티커다
        r = r * (1.0 + nz * (n1 - 0.5) * 2.0 + nz * 0.5 * (n2 - 0.5) * 2.0)
        a = _smooth((size - r) / 0.62)
        a = a * (0.55 + 0.45 * n3)                       # 속이 얼룩덜룩해야 '자국'이다
        a = a * _smooth((1.0 - np.maximum(np.abs(xx), np.abs(yy))) / 0.22)
        rgb = np.zeros((half, half, 3), np.float32)
        for c in range(3):
            rgb[:, :, c] = col[c] * (0.86 + 0.28 * n2)
        tiles.append((np.clip(rgb, 0, 1), np.clip(a, 0, 1) * amax))
    top = np.concatenate([tiles[0][0], tiles[1][0]], axis=1)
    bot = np.concatenate([tiles[2][0], tiles[3][0]], axis=1)
    at = np.concatenate([tiles[0][1], tiles[1][1]], axis=1)
    ab = np.concatenate([tiles[2][1], tiles[3][1]], axis=1)
    return np.concatenate([top, bot], axis=0), np.concatenate([at, ab], axis=0)


def bake_shaft(w, h):
    """달빛 샤프트 콘의 옆면. 위(천장 틈)가 진하고 아래로 사라진다."""
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]      # 0 = 위
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    # ★★세로 프로파일이 이 텍스처의 전부다.
    #   처음엔 "위가 제일 진하고 아래로 사라진다"로 구웠다(천장 틈이 광원이니까).
    #   그런데 이 게임에는 **천장이 없다.** 위쪽 끝이 그대로 잘려서 화면에
    #   가장자리가 곧은 반투명 다각형이 떴다(통로 컷에서 벽을 가로지르는 그 판).
    #   그래서 위아래 **양쪽으로** 사라지게 바꿨다: 60% 높이에서 제일 진하고
    #   꼭대기에서 0, 밑동에서 0.18(바닥 웅덩이가 이어받는다).
    top_fade = np.clip((1.0 - yy) / 0.40, 0, 1) ** 1.20        # 위 40% 에서 사라진다
    body = 0.18 + 0.82 * np.clip(yy / 0.75, 0, 1) ** 0.65
    v = np.clip(top_fade * body, 0, 1)
    # 가로: 가장자리가 부드럽게 사라져야 콘이 판때기로 안 보인다
    e = np.clip(1.0 - np.abs(xx), 0, 1) ** 1.15
    streak = 0.80 + 0.20 * _vnoise(max(w, h), 5, 913)[:h, :w]
    a = np.clip(v * e * streak * 0.62, 0, 1)
    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = 0.52
    rgb[:, :, 1] = 0.72
    rgb[:, :, 2] = 1.00
    return rgb, a


def bake_flame(w, h):
    """횃불 불꽃 스프라이트. 물방울 모양 + 흰 심지."""
    yy = np.linspace(1, 0, h, dtype=np.float32)[:, None]      # 1 = 위(끝)
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    # 폭: 아래 0.30 에서 시작해 0.35 높이에서 가장 넓고 위로 뾰족해진다
    width = 0.30 + 0.72 * np.clip(np.sin(np.clip(yy, 0, 1) ** 0.75 * np.pi), 0, 1) ** 1.25
    width = np.maximum(width * (1.0 - yy * 0.15), 0.02)
    n = _vnoise(max(w, h), 7, 4021)[:h, :w]
    d = np.abs(xx) / width
    d = d * (1.0 + 0.16 * (n - 0.5))
    a = np.clip(1.0 - d, 0, 1) ** 0.85
    a = a * np.clip((1.0 - yy) * 6.0, 0, 1)                   # 밑동은 자른다
    # 색: 심지(가운데 아래)가 희고 -> 노랑 -> 주황 -> 끝이 붉다
    core = np.clip((1.0 - d) * (1.0 - yy * 0.8), 0, 1) ** 2.2
    hot = np.array((1.00, 0.97, 0.86), np.float32)
    mid = np.array((1.00, 0.72, 0.26), np.float32)
    tip = np.array((0.92, 0.34, 0.12), np.float32)
    t = np.broadcast_to(np.clip(yy, 0, 1), (h, w))[:, :, None]
    rgb = mid[None, None, :] * (1 - t) + tip[None, None, :] * t
    rgb = rgb * (1 - core[:, :, None]) + hot[None, None, :] * core[:, :, None]
    return np.clip(np.nan_to_num(rgb), 0, 1), np.nan_to_num(a)


# ═════════════════════════════════════════════════════════════
# 불꽃 플립북 (13차-불꽃. 오너 "불꽃이 그림처럼 멈춰 있네")
# ═════════════════════════════════════════════════════════════
# ★한 장짜리 dg_flame.png 는 **정지 그림**이다. 던전에 불이 49자루나 서 있는데
#   전부 멎어 있으면 방이 통째로 박제로 읽힌다. 실루엣이 실제로 달라지는 넉 장을
#   가로로 이어 붙여 굽고, 게임이 24fps 칸으로 넘긴다(2칸 打ち = 12fps 작화).
#
# 왜 셰이더 왜곡이 아니라 플립북인가
#   불꽃은 흔들리는 게 아니라 **혀가 갈라졌다 붙는다**. UV 를 밀거나 늘리는 왜곡은
#   같은 실루엣이 미끄러질 뿐이라 "젤리"가 된다. 컨셉(concept_hall.png)의 관솔도
#   혀가 둘로 갈라진 순간이 잡혀 있다 - 그건 프레임을 갈아야 나온다.
#
# 화풍은 원본 dg_flame 을 그대로 잇는다(같은 색 계단 · 같은 부드러움).
#   컨셉 불꽃은 셀 평칠이 아니라 회화체 글로우다 - 여기서 갑자기 각지면 그 방만 뜬다.
FLIP_N = 4                 # 칸 수. 12fps 로 넘기면 한 바퀴 0.333초 = 관솔의 흔들림 주기
FLIP_MARGIN = 0.90         # 칸 안에서 그림이 차지하는 가로 폭(나머지는 투명 여백)
#   ★여백이 필요한 이유: 스트립을 선형보간으로 읽으면 칸 경계에서 옆 칸이 샌다.
#     밉맵까지 물리면 더 샌다. 양끝을 확실히 비워 두는 게 유일하게 안전한 길이다.


def _flame_frame(w, h, p, seed):
    """불꽃 한 칸. p 는 0..2pi 의 위상(칸 번호에서 온다).

    ★칸 안에서 그림이 **위와 옆에 닿으면 안 된다.** 위에 닿으면 불꽃 끝이 잘린
      네모로 읽히고(원본 dg_flame 의 흠이다), 옆에 닿으면 스트립에서 옆 칸이 샌다."""
    yy = np.linspace(1, 0, h, dtype=np.float32)[:, None]      # 1 = 위(끝)
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    n = _vnoise(max(w, h), 7, seed)[:h, :w]

    # ① 키. 칸마다 끝이 오르내린다. 늘 1 아래라 끝이 칸 위에서 잘리지 않는다
    ytip = 0.90 + 0.06 * math.cos(p + 1.1)
    yn = np.clip(yy / ytip, 0, 1)                             # 0 밑동 .. 1 끝

    # ② 물방울 반폭. 아래 1/3 이 가장 넓고 위로 뾰족하다. 밑동은 심지라 가늘다
    hw = 0.56 * np.clip(np.sin(np.pi * yn ** 0.60), 0, 1) ** 1.12 + 0.10 * (1.0 - yn)
    # 위로 올라가는 배부름. "빨려 올라간다"는 인상이 이 한 줄에서 나온다
    hw = hw * (1.0 + 0.20 * np.sin(yn * 4.6 - p))
    hw = np.clip(hw, 0.0, 1.0) * FLIP_MARGIN

    # ③ 기울기. 끝만 눕는다(밑동은 심지에 물려 있어 안 움직인다)
    cx = 0.26 * yn ** 1.8 * math.sin(p)

    # ★알파는 폭으로 **나누지 않는다.** d = |x-cx|/hw 로 재면 hw 가 0 으로 가는 끝에서
    #   1px 짜리 바늘이 남아 불꽃이 안테나를 단 것처럼 보인다(첫 판이 그랬다).
    #   가장자리 흐림 폭을 절대값으로 두면 끝이 제 자리에서 스스로 사라진다.
    s = hw - np.abs(xx - cx) * (1.0 + 0.18 * (n - 0.5))
    a = np.clip(s / (0.55 * hw + 0.09), 0, 1) ** 0.85
    inw = np.clip(s / (hw + 0.05), 0, 1)                      # 0 가장자리 .. 1 한복판

    # ④ 갈라진 혀. 칸마다 한쪽으로 작은 불꽃이 떨어져 나갔다 붙는다.
    #    이게 있고 없고가 "불이 살아 있다"와 "주황 물방울"을 가른다.
    t0 = 0.34 + 0.10 * math.cos(p * 1.3)                      # 갈라지는 높이
    t1 = 0.84 + 0.05 * math.sin(p * 0.7)                      # 혀 끝(<1)
    tn = np.clip((yy - t0) / max(1e-3, t1 - t0), 0, 1)
    thw = 0.19 * np.clip(np.sin(np.pi * tn ** 0.55), 0, 1) ** 1.10 * FLIP_MARGIN
    tcx = 0.44 * math.sin(p + 2.2) * tn ** 1.4
    ts = thw - np.abs(xx - tcx) * (1.0 + 0.22 * (n - 0.5))
    tk = 0.34 + 0.66 * (0.5 + 0.5 * math.sin(p + 0.6))        # 칸마다 세기가 다르다
    ta = np.clip(ts / (0.55 * thw + 0.07), 0, 1) ** 0.90 * tk
    a = np.clip(np.maximum(a, ta), 0, 1)

    # ⑤ 칸 테두리. 위·옆을 확실히 비운다(스트립 이웃 칸 샘 방지)
    a = a * np.clip((1.0 - yy) / 0.05, 0, 1)
    edge = np.clip((1.0 - np.abs(xx)) / (1.0 - FLIP_MARGIN), 0, 1)
    a = a * (edge * edge * (3 - 2 * edge))

    # 색: 심지(가운데 아래)가 희고 -> 노랑 -> 주황 -> 끝이 붉다. 원본과 같은 계단이다.
    #   심지 세기만 칸마다 조금 다르다(불이 숨 쉬는 것처럼 보이는 값)
    core = np.clip(inw * (1.0 - yy * 0.8), 0, 1) ** 2.2
    core = core * (0.88 + 0.12 * math.cos(p * 2.0))
    hot = np.array((1.00, 0.97, 0.86), np.float32)
    mid = np.array((1.00, 0.72, 0.26), np.float32)
    tip = np.array((0.92, 0.34, 0.12), np.float32)
    t = np.broadcast_to(np.clip(yy, 0, 1), (h, w))[:, :, None]
    rgb = mid[None, None, :] * (1 - t) + tip[None, None, :] * t
    rgb = rgb * (1 - core[:, :, None]) + hot[None, None, :] * core[:, :, None]
    return np.clip(np.nan_to_num(rgb), 0, 1), np.nan_to_num(a)


def bake_flame_flip(w, h, n=FLIP_N):
    """불꽃 플립북 스트립(가로 n 칸). 칸 하나가 원본 dg_flame 과 같은 규격이다."""
    rgbs, alphas = [], []
    for f in range(n):
        p = 2.0 * math.pi * f / n
        # 잡결 시드도 칸마다 바꾼다. 같은 시드면 가장자리 결이 안 움직여서
        # 실루엣만 흐물거리는 "젤리"가 된다(손그림 불꽃은 결까지 다시 그려진다).
        r, a = _flame_frame(w, h, p, 4021 + f * 97)
        rgbs.append(r)
        alphas.append(a)
    return np.concatenate(rgbs, axis=1), np.concatenate(alphas, axis=1)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("[원자재] %s" % SRC)
    q = load_quads()
    meta = {"src": "incoming/codex_dungeon/tiles_dungeon.png", "res": RES,
            "lin": {}, "gain": {}, "seam": {}}

    # (원자재키, 이름, 줄눈 걷어내는 세기, 채도 빼는 세기)
    # ★13차C. 바닥 둘은 세게 걷는다(발밑이고 되풀이가 제일 잘 보인다).
    #   벽은 절반만 — 벽돌 단은 실루엣 정보라 다 지우면 벽이 종잇장이 된다.
    for key, name, grout, chroma in (("floor", "dg_floor", 0.30, 0.44),
                                     ("wall", "dg_wall", 0.55, 0.22),
                                     ("floor_b", "dg_floor_b", 0.30, 0.44)):
        print("\n[%s]" % name)
        a = q[key]
        a = flatten_lowfreq(a, int(RES * 0.375), amount=0.80)
        a, seam = _tz.make_tileable(a, name)
        a = calm_fine(a, keep=0.72)
        # ★★순서 함정: 줄눈 걷기는 **밝기 정규화 뒤**에 해야 한다. cut(초록초과
        #   문턱)이 절대값이라, 원본이 아직 어두운 채로 재면 문턱을 못 넘어서
        #   손을 대도 절반밖에 안 걷힌다(첫 판이 48% 에서 멎었다). 정규화로
        #   밝기를 올린 뒤에 걷고, 걷느라 밝기가 밀린 만큼 한 번 더 정규화한다.
        a, _g0 = normalize_mean(a)
        g0 = _grout_stat(a)
        a = soften_grout(a, keep=grout)
        a = pull_chroma(a, chroma)
        g1 = _grout_stat(a)
        a, _g1 = normalize_mean(a)
        gain = _g0 * _g1
        meta["lin"][name] = save_rgb(name, a)
        meta["gain"][name] = round(float(gain), 4)
        meta["seam"][name] = seam["after"]
        meta.setdefault("grout", {})[name] = {"before": g0, "after": g1}
        print("   [줄눈] 초록초과 %.4f -> %.4f (%.0f%% 감) · 채도 %.3f -> %.3f"
              % (g0["ge"], g1["ge"], (1 - g1["ge"] / max(1e-6, g0["ge"])) * 100,
                 g0["chroma"], g1["chroma"]))
        print("   [밝기] 선형 x%.2f (곱수 계약용 여유)" % gain)

    # ── 메달리온: 데칼이라 이어붙일 필요가 없다. 대신 알파 비네트로 바닥에 녹인다 ──
    print("\n[dg_medallion]")
    med = q["medallion"]
    med = flatten_lowfreq(med, int(RES * 0.45), amount=0.55)
    med, gain = normalize_mean(med, TARGET_MEAN)
    # ★512 로 줄인다. 데칼 하나가 5m 를 덮으니 102px/m 로 충분하고, 1024 png(알파라
    #   jpg 로 못 간다)는 그 자체로 2MB 라 glb 예산의 40% 를 혼자 먹는다.
    MRES = 512
    med = np.asarray(Image.fromarray((np.clip(med, 0, 1) * 255 + 0.5).astype(np.uint8))
                     .resize((MRES, MRES), Image.LANCZOS), np.float32) / 255.0
    yy, xx = np.mgrid[0:MRES, 0:MRES].astype(np.float32) / (MRES - 1) * 2 - 1
    rr = np.sqrt(xx * xx + yy * yy)
    va = np.clip((0.99 - rr) / 0.26, 0, 1)
    va = va * va * (3 - 2 * va)
    save_rgba("dg_medallion", med, va)
    meta["lin"]["dg_medallion"] = [float(x) for x in srgb_to_lin(med).reshape(-1, 3).mean(axis=0)]
    meta["gain"]["dg_medallion"] = round(float(gain), 4)

    # ── 절차 텍스처 ──
    print("\n[절차]")
    # ★13차C. 웜 풀은 **가산 합성**(web/level.js)이 전제다. 알파는 이제 '돌을 얼마나
    #   덮는가'가 아니라 '빛을 얼마나 더하는가'라서 조금 올려도 돌이 안 지워진다.
    #   심 황백 -> 주황 -> 붉게 소멸. 세 색을 **반경**으로 섞는다.
    rgb, a = bake_pool(256, ((1.00, 0.95, 0.80), (1.00, 0.62, 0.26), (0.90, 0.34, 0.11)),
                       311, squash=1.0, wob=0.22, core=0.28, amax=0.72,
                       tail=0.70, rough=0.44)
    save_rgba("dg_pool", rgb, a)
    # 달빛 웅덩이: 컨셉 실측이 #26578e (S .73 V .56) 로 **여기는 진짜 밝다**.
    # 던전에서 제일 밝은 자리라 알파를 높게 준다(같은 2차 감쇠를 쓴다).
    rgb, a = bake_pool(256, ((0.72, 0.88, 1.00), (0.30, 0.58, 1.00), (0.14, 0.32, 0.80)),
                       517, squash=0.74, wob=0.16, core=0.44, amax=0.80,
                       tail=0.66, rough=0.34)
    save_rgba("dg_pool_cold", rgb, a)
    rgb, a = bake_shaft(128, 512)
    save_rgba("dg_shaft", rgb, a * 0.36)
    rgb, a = bake_flame(128, 192)
    save_rgba("dg_flame", rgb, a)
    # 벽을 타고 오르는 횃불 자국(13차C 신설). 세로로 길다
    rgb, a = bake_wall_glow(128, 192)
    save_rgba("dg_wglow", rgb, a)
    # 바닥 마모·이끼 데칼 넉 장(13차C 신설). 격자 리듬을 끊는 비반복 얼룩
    rgb, a = bake_wear(256)
    save_rgba("dg_wear", rgb, a)
    meta["lin"]["dg_wear"] = [float(x) for x in srgb_to_lin(rgb).reshape(-1, 3).mean(axis=0)]
    bake_flip_only()

    with open(META, "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("\n[메타] %s" % META)


def bake_flip_only():
    """불꽃 플립북만 굽는다.

    ★따로 뗀 이유: main() 은 dungeon_tex.json 의 평균·게인을 다시 쓴다. 그 값은
      **이미 구워 놓은 level2.glb 의 재질 곱수와 짝**이라, 불꽃 하나 고치자고 전체를
      다시 돌리면 맵 색이 통째로 밀릴 위험이 있다. 플립북은 glb 밖(런타임 로드)이라
      혼자 구울 수 있다."""
    os.makedirs(OUT_DIR, exist_ok=True)
    print("[불꽃 플립북] %d칸" % FLIP_N)
    rgb, a = bake_flame_flip(128, 192)
    save_rgba("dg_flame_fb", rgb, a)


if __name__ == "__main__":
    # `python3 tools/dungeon_tex.py flame` = 불꽃 플립북만(원자재 · glb 무관)
    if len(sys.argv) > 1 and sys.argv[1] == "flame":
        bake_flip_only()
    else:
        main()
