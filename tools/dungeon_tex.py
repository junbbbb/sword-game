# -*- coding: utf-8 -*-
"""던전 1층 텍스처를 **브롤스타즈·포트나이트 화풍**으로 굽는다 (14차 파도. 전면 재작).

    python3 tools/dungeon_tex.py            전부
    python3 tools/dungeon_tex.py flame      불꽃 플립북만(glb 밖. 런타임 로드)
    python3 tools/dungeon_tex.py light      빛 데칼만(곱수 계약 밖. s40 은 다시 돌릴 것)

오너 지시(2026-08-12): **"브롤스타즈, 포트나이트 풍의 그림체 맵을 원했는데 지금과
많이 다르다. 다시. 장소는 던전 1층."**  정본 = `incoming/codex_dungeon2/` 석 장
(bs_hall · bs_corridor · bs_tiles). 13차까지의 "디아블로급 남색 어둠"은 폐기다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
컨셉 실측 (renders/history/v99_wave14/dungeon_bs/scripts/bs_regions.py · bs_palette.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
화면색이다(칠할 색이 아니다 - ★ACES 역산은 bs_plan.py 가 한다).

    bs_tiles  크림 판석 75.8% #e3b983 (H34 S43 V89)  밝 #f6d79f  어 #a47550
              보라 줄눈  2.9% #70607f (H270 S25 V50) · 자주 줄눈 4.0% #917387
              라임 풀    0.2% #868c39                ← ★0.2% 다. 그물이 아니다
    bs_hall   보라 블록 #472f5d (H271 S50) 밝 #8868a9 · 자주 #4f2944 · 코발트 #232b52
              청록 블록 #33555d~#467c83 · 호박 웜 #cf8c3e 밝 #f6b556 · 깊은 어둠 #1a1636
    화면 전체  Y평균 0.177 · p05 0.009 · p50 0.129 · p95 0.489 · S중앙 0.60
              띠별 R/B  0.50 / 1.28 / 7.64 / 9.94 / 7.94   (어둠은 보라 · 밝으면 호박)

★13차판(디아블로)의 Y평균은 0.030 이었다. **여섯 배 밝히는** 판이다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇을 어떻게 굽는가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    dg_floor / dg_floor_b   incoming/codex_dungeon2/bs_tiles.png 를 이어붙임화
                            (컨셉 그림 자체가 바닥 견본이다 - 그릴 이유가 없다)
    dg_wall                 **절차 생성**. 컨셉의 큰 둥근 블록은 견본 그림이 없다
                            (벽이 원근 안에 있어 잘라 쓸 수가 없다). 블록 하나가
                            사람 몸통급이라는 것이 이 화풍의 핵심이라 크기·베벨·
                            블록별 색변주를 손잡이로 들고 있어야 한다
    dg_medallion            **절차 생성**. 컨셉 제단 = 청록 팔각 + 금테. 옛 판은
                            컨셉 시트에서 잘라 온 384px png 가 406KB 였다(glb 의 8%).
                            같은 그림을 절차로 그리면 평칠이라 30KB 다
    dg_pool / dg_wglow      횃불 빛(가산). 컨셉 호박색으로 재보정
    dg_flame / dg_flame_fb  불꽃. 형태는 13차 그대로(이미 카툰 문법) · 색만 재보정
    dg_wear                 바닥 얼룩 넉 장. 크림/보라/라임 팔레트로 재보정
    dg_pool_cold / dg_shaft 계단의 찬 빛. 컨셉에 달빛은 없지만 **출구 표식**이라
                            남긴다. 색을 청록(메달리온과 같은 계열)으로 옮겼다

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
SRC_TILES = os.path.join(ROOT, "incoming", "codex_dungeon2", "bs_tiles.png")
OUT_DIR = os.path.join(ROOT, "web", "tex")
META = os.path.join(OUT_DIR, "dungeon_tex.json")

# tileize.py 의 이음매 도구를 그대로 빌린다(같은 자로 재야 숫자가 비교된다)
_spec = importlib.util.spec_from_file_location(
    "tileize", os.path.join(ROOT, "tools", "tileize.py"))
_tz = importlib.util.module_from_spec(_spec)
sys.modules["tileize"] = _tz
_spec.loader.exec_module(_tz)

RES = 1024
# ★목표 sRGB 평균. 13차는 0.58 이었다 — 그 판은 화면 Y평균 0.03 짜리 어둠이라
#   알베도가 어두워도 곱수에 자리가 남았다. 이 판은 화면이 여섯 배 밝으므로
#   알베도도 그만큼 밝아야 한다(곱수 k = 목표/타일평균/정점색평균 <= 1 이 계약이다).
#   bs_tiles 원본 평균이 이미 0.667 이라 거의 그대로 쓴다.
TARGET_MEAN = 0.660

# ── 컨셉에서 역산한 **알베도**(칠할 색). bs_plan.py inv 의 출력이다 ──
#   화면 #472f5d (정점색 0.40) -> 알베도 #816591  … 이런 식으로 뽑았다
ALB_PURPLE = (0x81, 0x65, 0x91)      # 보라 블록
ALB_PLUM = (0x8b, 0x5e, 0x76)        # 자주 블록
ALB_COBALT = (0x56, 0x61, 0x87)      # 코발트 블록
ALB_TEAL = (0x61, 0x89, 0x87)        # 청록 블록
ALB_LILAC = (0xa1, 0x99, 0xbf)       # 밝은 라일락(다듬은 돌 · 갓돌)
ALB_GROUT = (0x3a, 0x35, 0x55)       # 줄눈(깊은 어둠 #1a1636 의 알베도보다 조금 어둡게)
ALB_MOSS = (0xa7, 0xb3, 0x4f)        # 라임 풀
ALB_GOLD = (0xd9, 0xa8, 0x4e)        # 금테(제단·횃불 받침)
ALB_TEAL_HI = (0x63, 0xc6, 0xc0)     # 메달리온 청록


def srgb_to_lin(a):
    a = np.asarray(a, np.float64)
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(a):
    a = np.clip(np.asarray(a, np.float64), 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def c8(t):
    return np.array(t, np.float32) / 255.0


def flatten_lowfreq(rgb, k, amount=0.80):
    """되풀이했을 때 바둑판으로 깔리는 **큰 명암 얼룩**만 나눠 없앤다.

    bs_tiles 는 왼쪽 위가 밝고 오른쪽 아래가 어두운 한 장짜리 그림이라
    그대로 깔면 5m 마다 그 사선 얼룩이 되풀이된다.
    ★wrap_blur 는 감아 도는 흐림이라 여기서 새 이음매가 안 생긴다.
    """
    base = _tz.wrap_blur(rgb, k, passes=2)
    g = base.mean(axis=2, keepdims=True)
    m = float(g.mean())
    corr = m / np.maximum(g, 1e-4)
    corr = 1.0 + (corr - 1.0) * amount
    return np.clip(rgb * corr, 0.0, 1.0)


def calm_fine(rgb, keep=0.78):
    """게임 거리에서 결이 아니라 **지글거림**으로 보이는 최고주파만 조금 누른다."""
    lo = _tz.wrap_blur(rgb, 3, passes=2)
    return np.clip(lo + (rgb - lo) * keep, 0.0, 1.0)


def push_chroma(rgb, amount):
    """채도를 **올린다**. 13차의 pull_chroma 와 반대 방향인 이유:

    그 판의 문법은 "색은 빛이 칠한다"(알베도는 무채색에 가깝게)였다. 이 판의
    컨셉은 정반대다 — 돌 자체가 크림·보라·청록으로 **칠해져 있고** 화면 채도
    중앙값이 0.60 이다. 알베도가 회색이면 어떤 조명을 넣어도 그 그림이 안 나온다.
    """
    g = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1]
         + 0.0722 * rgb[:, :, 2])[:, :, None]
    return np.clip(g + (rgb - g) * (1.0 + amount), 0.0, 1.0)


def normalize_mean(rgb, target=TARGET_MEAN):
    """한 **스칼라**로 밝기만 올린다(채널별로 하면 원본 색기가 지워진다)."""
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


def save_rgb(name, rgb, quality=90):
    """알파가 없는 타일은 **jpg 로도** 굽는다(s40 이 jpg 를 읽는다).

    ★블렌더 glTF 익스포터를 `export_image_format="AUTO"` 로 돌려야 알파 텍스처가
      PNG 로 살아남는다. 그런데 AUTO 는 불투명 텍스처도 원본 형식을 그대로 물고
      가므로, 큰 석재 타일을 png 로 두면 glb 가 통째로 부푼다.
    """
    p = os.path.join(OUT_DIR, name + ".png")
    im8 = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(im8).save(p)
    jp = os.path.join(OUT_DIR, name + ".jpg")
    Image.fromarray(im8).save(jp, quality=quality, subsampling=0)
    lin = srgb_to_lin(rgb).reshape(-1, 3).mean(axis=0)
    srgb = rgb.reshape(-1, 3).mean(axis=0)
    print("   [저장] %-14s sRGB평균 #%02x%02x%02x · 선형 %.4f %.4f %.4f · jpg %dKB"
          % (name, int(srgb[0] * 255), int(srgb[1] * 255), int(srgb[2] * 255),
             lin[0], lin[1], lin[2], os.path.getsize(jp) // 1024))
    return [float(x) for x in lin]


def save_rgba(name, rgb, alpha):
    p = os.path.join(OUT_DIR, name + ".png")
    a = np.clip(alpha, 0, 1)
    px = np.dstack([np.clip(rgb, 0, 1), a])
    Image.fromarray((px * 255 + 0.5).astype(np.uint8)).save(p)
    print("   [저장] %-14s RGBA %dx%d · 알파 평균 %.3f 최대 %.3f · %dKB"
          % (name, rgb.shape[1], rgb.shape[0], float(a.mean()), float(a.max()),
             os.path.getsize(p) // 1024))


def _tex_stat(rgb, tag=""):
    """화풍 자기 채점용. ★'라임이 그물로 읽히는가'를 여기서 잡는다."""
    R, G, B = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    S = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    ge = G - np.maximum(R, B)                     # 초록 초과 = 이끼의 지문
    return {"tag": tag,
            "S_mean": round(float(S.mean()), 4),
            "lum_mean": round(float(L.mean()), 4),
            "lum_std": round(float(L.std()), 4),
            "green_frac": round(float((ge > 0.045).mean()), 5),
            "green_mean": round(float(ge.mean()), 5)}


# ═════════════════════════════════════════════════════════════
# 잡음 도구
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


# ═════════════════════════════════════════════════════════════
# 벽 — **큰 둥근 블록** (14차 신설. 절차 생성)
# ═════════════════════════════════════════════════════════════
# ★왜 절차인가: 컨셉의 벽은 원근 안에 있어 잘라 쓸 수가 없다(400x300px 을 1024 로
#   늘리면 뭉갠다). 그리고 이 화풍의 핵심은 "블록 하나가 사람 몸통급"이라는 **치수**
#   라서, 그 손잡이를 코드가 들고 있어야 한다 — 잘라 온 그림은 크기를 못 바꾼다.
# ★13차B 가 "절차 석재는 회색 상자가 됐다"고 폐기했던 것은 **값잡음으로 그린 돌결**
#   이었다. 이건 다른 물건이다: 평칠 + 굵은 베벨 + 굵은 줄눈 = 그래픽이지 결이 아니다.
#   브롤스타즈의 돌은 사진이 아니라 도형이다.
WALL_COURSES = 5            # 세로 단 수. UV 4.6m 기준 한 단 = 0.92m
WALL_PER_COURSE = 3         # 가로 블록 수. 한 장 = 1.53m (캐릭터 어깨의 세 배)
# ★3차 시도(6단 x 3장 · UV 3.6m)는 게임 화면에서 **여전히 벽돌**이었다. 컨셉의
#   블록은 문설주 하나에 세 장, 벽 높이 3.6m 에 네 단이 들어간다 = 한 장이
#   1.5 x 0.9m 다. 여기 숫자와 s40 의 WALL_UV_SCALE 은 한 짝이라 같이 움직인다.
WALL_GROUT = 0.085          # 줄눈 폭(블록 높이 대비 한쪽)
# ★★1차 시도가 **알약**으로 나왔다(둥글기 0.30 · 하이라이트를 곱셈으로 1.72).
#   컨셉의 블록은 네모다. 모서리를 아주 조금만 굴리고(0.14), 윗면을 **경계가 보이는
#   띠**로 얹고, 가장자리에 어두운 잉크선을 둘러야 "그린 돌"이 된다.
#   ★밝게 만드는 일을 곱셈으로 하면 채도가 씻긴다(1.72 를 곱해 분홍·민트가 됐다).
#     아래 `_tint` 가 밝힌 만큼 채도를 되돌려 준다.
WALL_ROUND = 0.14           # 모서리 둥글기(블록 높이 대비)
WALL_BEVEL = 0.26           # 윗면(갓) 띠가 차지하는 세로 비율
WALL_HI = 1.24              # 그 띠의 밝기 배수
WALL_LO = 0.66              # 블록 밑동 그늘 배수
WALL_INK = 0.46             # 가장자리 잉크선 세기
# ★2차 시도가 **파스텔**로 나왔다(분홍·민트·연보라). 원인 둘:
#   (가) 역산 알베도가 이미 채도 30% 인데 ACES 가 밝은 쪽에서 또 씻는다
#   (나) 갓 배수 1.46 에 맨 윗줄 +0.30 이 겹쳐 위쪽 절반이 흰색으로 말려 올라갔다
#   그래서 팔레트 채도를 굽기 직전에 한 번 올리고(WALL_SAT) 갓을 낮췄다.
# ★★3차 시도가 **젤리 곰 벽**으로 나왔다(분홍·민트·형광 보라가 옆에 붙는다).
#   원인은 채도가 아니라 **폭**이었다: 색표 다섯을 그대로 뽑으니 이웃한 두 장의
#   색상이 120도씩 벌어졌다. 컨셉의 벽은 한 벽이 통째로 청보라 계열이고 변주는
#   주로 **명도**다(실측: 보라 #472f5d · 코발트 #232b52 = 색상 41도 차이).
#   그래서 뽑은 색을 벽 평균색 쪽으로 절반 끌어당긴다(WALL_PULL).
WALL_SAT = 1.10             # 블록 색표 채도 배수
WALL_PULL = 0.52            # 뽑은 색을 벽 평균 쪽으로 끌어당기는 몫
ALB_WALL_BASE = (0x6c, 0x6a, 0x8c)   # 벽 평균색(위 다섯의 가중평균)

# 블록 색표 (알베도). 가중치는 컨셉 벽의 면적비를 따랐다
#   보라 19.3% · 코발트 26.6% · 자주 14.6% · 청록 2.9%(기둥에 몰려 있다) + 라일락
WALL_MIX = [(ALB_PURPLE, 0.34), (ALB_COBALT, 0.34), (ALB_PLUM, 0.12),
            (ALB_TEAL, 0.10), (ALB_LILAC, 0.10)]


def _rr_sdf(px, py, hx, hy, r):
    """둥근 사각형 부호거리. 안이 음수."""
    qx = np.abs(px) - (hx - r)
    qy = np.abs(py) - (hy - r)
    ax = np.maximum(qx, 0.0)
    ay = np.maximum(qy, 0.0)
    return np.sqrt(ax * ax + ay * ay) + np.minimum(np.maximum(qx, qy), 0.0) - r


def _sat(c, k):
    """채도만 k 배(휘도 보존). 팔레트를 굽기 직전에 한 번 올린다."""
    c = np.asarray(c, np.float64)
    g = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return np.clip(g + (c - g) * k, 0, 1)


def _pick(rs, mix, base=None, pull=None, sat=None):
    r = rs.rand() * sum(w for _, w in mix)
    got = mix[-1][0]
    for c, w in mix:
        r -= w
        if r <= 0:
            got = c
            break
    base = np.array(ALB_WALL_BASE if base is None else base, np.float64) / 255.0
    col = np.array(got, np.float64) / 255.0
    pull = WALL_PULL if pull is None else pull
    return _sat(base * pull + col * (1.0 - pull), WALL_SAT if sat is None else sat)


def _tint(col, sh, resat=0.55):
    """색 x 명암. **밝힌 만큼 채도를 되돌린다.**

    ★단순 곱셈은 밝은 쪽에서 채도를 씻어 낸다(1.72 를 곱했더니 보라가 분홍,
      청록이 민트가 됐다 — 1차 시도의 그 파스텔이 여기서 나왔다).
      sh > 1 인 자리에서 그만큼 색기를 되살려 준다.
    """
    px = col[None, None, :] * sh[:, :, None]
    g = (0.2126 * px[:, :, 0] + 0.7152 * px[:, :, 1] + 0.0722 * px[:, :, 2])[:, :, None]
    k = 1.0 + resat * np.clip(sh - 1.0, 0, None)[:, :, None]
    return np.clip(g + (px - g) * k, 0, 1)


def bake_wall(res=RES, seed=1407, mix=None, base=None, pull=None, sat=None,
              moss=True, jitter=0.17):
    """큰 블록 벽. **가로로 감아 도는** 배치라 이어붙임이 저절로 성립한다.

    ★세로 이음: 단 높이가 res/COURSES 로 딱 떨어지고 단마다 독립이라 위아래가 맞는다.
    ★가로 이음: 한 단의 블록 폭 합을 res 로 정확히 맞추고, 마지막 블록이 오른쪽
      끝에서 왼쪽 끝으로 **감아 돌게** 그린다(칸 인덱스에 modulo 를 쓴다).

    한 블록의 층 (컨셉 bs_hall·bs_corridor 를 확대해 세어 본 그대로다)
        ① 갓 — 위 26% 가 확실히 밝다. 경계가 **보인다**(뭉개면 알약이 된다)
        ② 몸통 — 아래로 가며 완만히 어두워진다
        ③ 잉크선 — 가장자리 두 픽셀이 제 색의 어두운 판(검정이 아니다)
        ④ 접지 그늘 — 줄눈 쪽 아래가 더 어둡다(블록이 앞으로 나와 보인다)
    """
    rs = np.random.RandomState(seed)
    img = np.zeros((res, res, 3), np.float64)
    grout = np.array(ALB_GROUT, np.float64) / 255.0
    gn = _vnoise(res, 17, seed + 5)
    img[:] = grout[None, None, :] * (0.62 + 0.42 * gn[:, :, None])

    ch = res / WALL_COURSES                       # 단 높이(px)
    ys, xs = np.mgrid[0:res, 0:res].astype(np.float64)
    nz1 = _vnoise(res, 11, seed + 11)             # 블록 안 얼룩
    nz2 = _vnoise(res, 37, seed + 23)             # 잔결
    # (실금 잡음은 뺐다 — 2차 시도에서 낙서로 읽혔다)
    for c in range(WALL_COURSES):
        y0 = c * ch
        w = 1.0 + (rs.rand(WALL_PER_COURSE) - 0.5) * 0.36
        w = w / w.sum() * res
        off = rs.rand() * res                     # 단마다 어긋물림(running bond)
        x = off
        for k in range(WALL_PER_COURSE):
            bw = w[k]
            col = _pick(rs, WALL_MIX if mix is None else mix, base, pull, sat)
            # 블록마다 명도를 흔든다(컨셉은 같은 색이 두 번 안 붙는다).
            # ★밝기만 흔들고 색상은 거의 안 흔든다 — 색상까지 흔들면 팔레트가 흐려진다
            col = np.clip(col * (1.0 - jitter * 0.82 + jitter * rs.rand()), 0, 1)
            col = np.clip(col + (rs.rand(3) - 0.5) * 0.030, 0, 1)
            cx, cy = x + bw * 0.5, y0 + ch * 0.5
            hx, hy = bw * 0.5 - WALL_GROUT * ch, ch * 0.5 - WALL_GROUT * ch
            rad = WALL_ROUND * ch
            dx = ((xs - cx + res * 1.5) % res) - res * 0.5
            dy = ys - cy
            d = _rr_sdf(dx, dy, hx, min(hy, hx * 0.98), rad)
            body = _smooth((-d) / 1.3)            # 가장자리 1.3px 만 흐린다
            if body.max() <= 0:
                x = (x + bw) % res
                continue
            v = np.clip((dy + hy) / (2 * hy), 0, 1)          # 0 위 .. 1 아래
            # ① 갓. 경계가 보이는 띠다(폭 0.05 = 한 단에서 3px)
            cap = _smooth((WALL_BEVEL - v) / 0.055)
            # ② 몸통 세로 그라데이션
            grad = 1.0 - (1.0 - WALL_LO) * _smooth((v - WALL_BEVEL) / (1 - WALL_BEVEL)) ** 0.80
            sh = grad + (WALL_HI - 1.0) * cap
            # 갓 안에서도 맨 위 한 줄이 제일 밝다(빛을 물고 있는 모서리)
            sh = sh + 0.14 * _smooth((0.06 - v) / 0.04)
            # ③ 잉크선 — 가장자리 안쪽 2.4px
            ink = _smooth((d + 2.4) / 2.4)
            sh = sh * (1.0 - WALL_INK * ink)
            # ④ 좌우 말림 + 접지 그늘
            sh = sh * (1.0 - 0.16 * (np.abs(dx) / max(hx, 1e-3)) ** 3)
            sh = sh * (1.0 - 0.20 * _smooth((v - 0.86) / 0.14))
            # ⑤ 손그림 얼룩. ★실금(구불구불한 선)은 뺐다 — 2차 시도에서 낙서로 읽혔다.
            #   값잡음의 등고선은 돌의 금이 아니라 지렁이다.
            sh = sh * (0.94 + 0.12 * nz1) * (0.975 + 0.05 * nz2)
            px = _tint(col, sh)
            # ⑥ 갓에 **따뜻한 기**를 조금 얹는다(빛은 따뜻하고 돌은 찬 게 이 컨셉이다)
            px = np.clip(px + cap[:, :, None] * 0.05
                         * np.array((1.00, 0.86, 0.62))[None, None, :], 0, 1)
            a = body[:, :, None]
            img = img * (1 - a) + px * a
            x = (x + bw) % res
    # ── 줄눈 접지 그늘: 블록 둘레가 더 어두워야 블록이 앞으로 나온다 ──
    blk = _smooth((img.mean(axis=2) - 0.14) / 0.06)
    ao = _tz.wrap_blur(blk[:, :, None].astype(np.float32), 5, passes=2)[:, :, 0]
    img = img * (1.0 - 0.34 * np.clip(ao - blk, 0, 1))[:, :, None]
    # ── 라임 이끼: **아주 드물게.** 컨셉 벽의 초록은 0.4~1.4% 뿐이다 ──
    # ★전례 함정: 13차C 가 "산성 초록 줄눈 그물"로 기각당했다. 그물이 되는 조건은
    #   초록이 **줄눈을 따라 이어질 때**다. 그래서 줄눈을 따라 칠하지 않고 잡음이
    #   높은 자리에만 **작은 포기로** 얹는다(이어지지 않는다).
    # ★1차 시도는 이게 **노란 물감 자국**이었다(덩어리가 크고 알파 0.85). 잔 옥타브로
    #   자르고 알파를 0.55 로 내려 잎사귀 크기로 만든다.
    # ★2차 시도는 이게 **노란 물감 자국**이었다(덩어리가 크고 색이 누렜다).
    #   색을 초록으로 내리고, 잔 옥타브(cells 67)로 잘라 잎사귀 크기로 만든다.
    if moss:
        mcol = _sat(np.array((0.42, 0.58, 0.20)), 1.10)
        m1 = _smooth((_vnoise(res, 9, seed + 41) - 0.82) / 0.10)
        m2 = _smooth((_vnoise(res, 67, seed + 61) - 0.58) / 0.18)
        mm = m1 * m2 * 0.42
        img = img * (1 - mm[:, :, None]) + mcol[None, None, :] * mm[:, :, None]
    return np.clip(img, 0, 1).astype(np.float32)


# ── 다듬은 돌(기둥·아치·제단·계단) ──────────────────────────────
# ★★4차 판정에서 기둥이 **검은 토템**으로 나왔다. 원인은 곱수 천장이다:
#   기둥은 수직면이라 조도가 바닥의 43% 뿐인데, 벽 텍스처(휘도 0.28)를 같이 쓰면
#   목표 휘도가 0.185 에서 잘린다(컨셉의 청록 붙임기둥은 화면 Y 0.17 이다).
#   벽 텍스처를 더 밝게 구우면 갓 부분이 12% 클리핑돼 계조가 죽는다.
#   그래서 **다듬은 돌 전용 타일**을 한 장 더 굽는다(glb +105KB. 예산 610KB 여유).
#   컨셉도 실제로 그렇다 — 벽은 색색의 막돌이고 아치·붙임기둥·제단은 한 가지
#   밝은 다듬돌이다.
BLOCK_MIX = [(ALB_LILAC, 0.56), (ALB_TEAL, 0.24), (ALB_COBALT, 0.20)]
BLOCK_BASE = (0xa4, 0x9f, 0xc0)     # 다듬돌 평균색
BLOCK_PULL = 0.70                   # 색을 평균 쪽으로 크게 끌어당긴다(한 덩이 돌이다)


# ═════════════════════════════════════════════════════════════
# 제단 메달리온 — **절차 생성** (14차. 406KB -> 30KB)
# ═════════════════════════════════════════════════════════════
def bake_medallion(res=256):
    """컨셉 제단 한복판의 **청록 팔각 + 금테**. 알파 데칼.

    ★옛 판은 컨셉 시트에서 잘라 온 384px png 였고 **406KB(glb 예산의 8%)** 를
      혼자 먹었다. 쓰이는 곳은 카드 한 장(정점 4개)이다. 같은 그림을 평칠로
      그리면 png 압축이 잘 먹어 30KB 다 — 그 차액이 이 판의 벽 텍스처 값이다.
    """
    yy, xx = np.mgrid[0:res, 0:res].astype(np.float32) / (res - 1) * 2 - 1
    r = np.sqrt(xx * xx + yy * yy)
    ang = np.arctan2(yy, xx)
    # 팔각형 반지름(정팔각의 내접 반경 변주)
    oct_r = np.cos(np.pi / 8) / np.cos(((ang + np.pi / 8) % (np.pi / 4)) - np.pi / 8)
    stone = np.array(ALB_LILAC, np.float32) / 255.0
    gold = np.array(ALB_GOLD, np.float32) / 255.0
    teal = np.array(ALB_TEAL_HI, np.float32) / 255.0
    dark = np.array(ALB_GROUT, np.float32) / 255.0
    rgb = np.zeros((res, res, 3), np.float32)
    rgb[:] = stone[None, None, :] * 0.92
    R_OUT, R_GOLD, R_TEAL = 0.92, 0.80, 0.72

    def ring(lo, hi, col, soft=0.018):
        m = _smooth((r * oct_r - lo) / soft) * _smooth((hi - r * oct_r) / soft)
        return m[:, :, None] * col[None, None, :], m

    for lo, hi, col in ((R_TEAL, R_GOLD, gold), (0.0, R_TEAL, teal)):
        px, m = ring(lo, hi, col)
        rgb = rgb * (1 - m[:, :, None]) + px
    # 어두운 외곽선(카툰의 잉크). 팔각 테두리와 금테 안쪽에 한 줄씩
    for e in (R_OUT, R_GOLD):
        m = _smooth((0.022 - np.abs(r * oct_r - e)) / 0.014)
        rgb = rgb * (1 - m[:, :, None] * 0.85) + dark[None, None, :] * (m[:, :, None] * 0.85)
    # 살(spoke) 여덟 개 + 가운데 보석
    sp = np.abs(np.sin(ang * 4.0))
    m = _smooth((0.10 - sp) / 0.07) * _smooth((R_TEAL - 0.04 - r * oct_r) / 0.03)
    rgb = rgb * (1 - m[:, :, None] * 0.75) + (teal * 0.42)[None, None, :] * (m[:, :, None] * 0.75)
    m = _smooth((0.13 - r) / 0.03)
    rgb = rgb * (1 - m[:, :, None]) + (teal * 1.15)[None, None, :] * m[:, :, None]
    # 판석 이음선(제단 윗면이 판으로 나뉜 느낌) + 얼룩
    grid = np.minimum(np.abs(((xx * 3.0 + 9) % 1.0) - 0.5), np.abs(((yy * 3.0 + 9) % 1.0) - 0.5))
    gm = _smooth((0.045 - grid) / 0.03) * _smooth((r * oct_r - R_OUT + 0.10) / 0.06)
    rgb = rgb * (1 - gm[:, :, None] * 0.35) + dark[None, None, :] * (gm[:, :, None] * 0.35)
    rgb = np.clip(rgb * (0.94 + 0.12 * _vnoise(res, 11, 771)[:, :, None]), 0, 1)
    a = _smooth((R_OUT + 0.02 - r * oct_r) / 0.035)
    return rgb, a


# ═════════════════════════════════════════════════════════════
# 빛 데칼 (형태는 13차 그대로 · 색만 컨셉으로)
# ═════════════════════════════════════════════════════════════
# 컨셉 횃불 실측: 코어 #f6b556~#fcd26f · 둘레 #cf8c3e · 끝 #a5662e
# ★4차 조정. 심을 흰색에 가깝게 두면(0.90,0.62) 가산으로 더할 때 **화면을 씻는다** —
#   판정에서 밝은 띠 R/B 가 3.9(컨셉 7.6~9.9)로 나온 원인의 절반이 여기였다.
POOL_HOT = (1.00, 0.86, 0.50)
POOL_MID = (1.00, 0.62, 0.20)
POOL_TIP = (0.88, 0.40, 0.13)


def bake_pool(res, stops, seed, squash=1.0, wob=0.20, core=0.22, amax=0.62,
              tail=0.62, rough=0.42):
    """바닥에 까는 **빛 웅덩이** 데칼(가산 합성. web/level.js 가 갈아 준다).

    ★프로파일은 점광원의 2차 감쇠다 — 평평한 코어가 없다(있으면 원반 스티커다).
        f = 1 / (1 + (r/core)^2)      w = 카드 끝에서 0 이 되는 창
    ★가장자리는 **두 옥타브**로 흐트러뜨린다(한 옥타브면 매끈한 타원이 남는다).
    ★색 램프는 알파가 아직 보이는 구간 안에서 다 돌아야 한다(13차C 실측).
    """
    yy, xx = np.mgrid[0:res, 0:res].astype(np.float32) / (res - 1) * 2 - 1
    n1 = _vnoise(res, 5, seed)
    n2 = _vnoise(res, 13, seed + 37)
    r = np.sqrt(xx * xx + (yy * squash) ** 2)
    r = r * (1.0 + wob * (n1 - 0.5) * 2.0 + wob * 0.55 * (n2 - 0.5) * 2.0)
    r = np.maximum(r, 0.0)
    f = 1.0 / (1.0 + (r / max(1e-3, core)) ** 2) ** 1.10
    w = _smooth((1.0 - r) / max(1e-3, tail))
    a0 = np.clip(f * w, 0.0, 1.0)
    tm = _smooth((0.42 - a0) / 0.42) ** 1.4
    a0 = a0 * (1.0 - tm * rough * (1.0 - _vnoise(res, 9, seed + 71)))
    a = np.clip(a0, 0, 1) * amax
    hot = np.array(stops[0], np.float32)
    mid = np.array(stops[1], np.float32)
    tip = np.array(stops[2], np.float32)
    t1 = _smooth(r / max(1e-3, core * 1.15))[:, :, None]
    t2 = _smooth((r - core * 1.15) / 0.42)[:, :, None]
    rgb = hot[None, None, :] * (1 - t1) + mid[None, None, :] * t1
    rgb = rgb * (1 - t2) + tip[None, None, :] * t2
    rgb = np.clip(rgb * (0.92 + 0.16 * _vnoise(res, 9, seed + 71)[:, :, None]), 0, 1)
    return rgb, a


def bake_wall_glow(w, h, seed=8801):
    """횃불이 **벽을 타고 오르는** 자국.

    ★왜 정점색으로 못 하는가: 벽 상자가 seg 1.1m 라 정점 간격이 1m 다. 뜨거운
      심(반경 0.45m)이 그 격자에 안 잡힌다. **해상도를 텍스처가** 들고 정점색은
      넓은 스필만 맡는다.
    """
    yy = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    n = _vnoise(max(w, h), 7, seed)[:h, :w]
    y0 = -0.30
    up = np.clip((yy - y0) / 1.30, -1, 1)
    spread = 0.46 + 0.34 * np.clip(up, 0, 1) ** 0.80
    d = np.sqrt((xx / spread) ** 2 + (np.maximum(0.0, y0 - yy) / 0.34) ** 2
                + (np.maximum(0.0, yy - y0) / 0.56) ** 2)
    d = d * (1.0 + 0.24 * (n - 0.5) * 2.0)
    a = 1.0 / (1.0 + (d / 0.26) ** 2) ** 1.30
    a = a * _smooth((1.0 - np.abs(xx)) / 0.34) * _smooth((1.0 - np.abs(yy)) / 0.30)
    hot = np.array((1.00, 0.92, 0.70), np.float32)
    mid = np.array((1.00, 0.64, 0.26), np.float32)
    tip = np.array((0.88, 0.38, 0.14), np.float32)
    t1 = _smooth(d / 0.34)[:, :, None]
    t2 = _smooth((d - 0.34) / 0.55)[:, :, None]
    rgb = hot[None, None, :] * (1 - t1) + mid[None, None, :] * t1
    rgb = rgb * (1 - t2) + tip[None, None, :] * t2
    return np.clip(rgb, 0, 1), np.clip(a, 0, 1)


def bake_wear(res=256, seed=5501):
    """바닥 **마모·이끼 데칼** 넉 장(2x2 아틀라스).

    ★격자 리듬을 끊는 것은 명암 변주만으로는 모자란다. 되풀이 주기와 아무 상관
      없는 자리에 **비반복 얼룩**이 놓여야 눈이 주기를 못 센다. 넉 장인 이유:
      한 장이면 그것 자체가 새 되풀이가 된다.
    ★14차. 색을 컨셉 팔레트로 갈았다(옛 판은 흙빛·청록이라 크림 바닥에서 떴다).
        0 통행 마모(밝은 크림)   1 습윤(보라 그늘)
        2 라임 이끼              3 옅은 모래 변주
    """
    half = res // 2
    yy, xx = np.mgrid[0:half, 0:half].astype(np.float32) / (half - 1) * 2 - 1
    tiles = []
    spec = [((0.97, 0.88, 0.70), 0.50, 0.78, 1.25, 0.42),
            ((0.44, 0.38, 0.58), 0.44, 0.70, 0.85, 0.50),
            ((0.55, 0.62, 0.26), 0.42, 0.60, 1.00, 0.58),
            ((0.92, 0.83, 0.68), 0.36, 0.58, 0.80, 0.46)]
    for i, (col, amax, size, sq, nz) in enumerate(spec):
        n1 = _vnoise(half, 3, seed + i * 91)
        n2 = _vnoise(half, 7, seed + i * 91 + 13)
        n3 = _vnoise(half, 15, seed + i * 91 + 29)
        r = np.sqrt(xx * xx + (yy * sq) ** 2)
        r = r * (1.0 + nz * (n1 - 0.5) * 2.0 + nz * 0.5 * (n2 - 0.5) * 2.0)
        a = _smooth((size - r) / 0.62)
        a = a * (0.55 + 0.45 * n3)
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
    """계단 위에서 내려오는 빛기둥의 옆면.

    ★이 게임에는 천장이 없다. 위쪽 끝이 그대로 잘리면 화면에 가장자리가 곧은
      반투명 다각형이 뜬다(13차B 가 밟았다). 위아래 **양쪽으로** 사라지게 한다.
    ★14차. 색을 달빛 파랑 -> 메달리온과 같은 **청록**으로 옮겼다. 컨셉에 달빛은
      없지만 계단은 출구 표식이라 남긴다 — 파랑은 이 팔레트에서 어둠의 색이라
      빛으로 안 읽힌다.
    """
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    top_fade = np.clip((1.0 - yy) / 0.40, 0, 1) ** 1.20
    body = 0.18 + 0.82 * np.clip(yy / 0.75, 0, 1) ** 0.65
    v = np.clip(top_fade * body, 0, 1)
    e = np.clip(1.0 - np.abs(xx), 0, 1) ** 1.15
    streak = 0.80 + 0.20 * _vnoise(max(w, h), 5, 913)[:h, :w]
    a = np.clip(v * e * streak * 0.62, 0, 1)
    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = 0.52
    rgb[:, :, 1] = 0.94
    rgb[:, :, 2] = 0.96
    return rgb, a


def bake_flame(w, h):
    """횃불 불꽃 스프라이트 한 장(정지본. 런타임은 플립북을 쓴다)."""
    yy = np.linspace(1, 0, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    width = 0.30 + 0.72 * np.clip(np.sin(np.clip(yy, 0, 1) ** 0.75 * np.pi), 0, 1) ** 1.25
    width = np.maximum(width * (1.0 - yy * 0.15), 0.02)
    n = _vnoise(max(w, h), 7, 4021)[:h, :w]
    d = np.abs(xx) / width
    d = d * (1.0 + 0.16 * (n - 0.5))
    a = np.clip(1.0 - d, 0, 1) ** 0.85
    a = a * np.clip((1.0 - yy) * 6.0, 0, 1)
    core = np.clip((1.0 - d) * (1.0 - yy * 0.8), 0, 1) ** 2.2
    hot, mid, tip = FLAME_HOT, FLAME_MID, FLAME_TIP
    t = np.broadcast_to(np.clip(yy, 0, 1), (h, w))[:, :, None]
    rgb = mid[None, None, :] * (1 - t) + tip[None, None, :] * t
    rgb = rgb * (1 - core[:, :, None]) + hot[None, None, :] * core[:, :, None]
    return np.clip(np.nan_to_num(rgb), 0, 1), np.nan_to_num(a)


# ═════════════════════════════════════════════════════════════
# 불꽃 플립북 (13차-불꽃. 형태는 그대로 · 색만 컨셉으로)
# ═════════════════════════════════════════════════════════════
# 왜 셰이더 왜곡이 아니라 플립북인가: 불꽃은 흔들리는 게 아니라 **혀가 갈라졌다
# 붙는다**. UV 왜곡은 같은 실루엣이 미끄러질 뿐이라 "젤리"가 된다.
FLIP_N = 4
FLIP_MARGIN = 0.90
# 컨셉 불꽃 실측: 심 #fcd26f(거의 흰 노랑) · 몸 #f1ae52 · 끝 #d68e44
FLAME_HOT = np.array((1.00, 0.96, 0.80), np.float32)
FLAME_MID = np.array((1.00, 0.74, 0.30), np.float32)
FLAME_TIP = np.array((0.95, 0.44, 0.14), np.float32)


def _flame_frame(w, h, p, seed):
    """불꽃 한 칸. p 는 0..2pi 의 위상.

    ★칸 안에서 그림이 위와 옆에 닿으면 안 된다(위=잘린 네모 · 옆=이웃 칸 샘)."""
    yy = np.linspace(1, 0, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    n = _vnoise(max(w, h), 7, seed)[:h, :w]
    ytip = 0.90 + 0.06 * math.cos(p + 1.1)
    yn = np.clip(yy / ytip, 0, 1)
    hw = 0.56 * np.clip(np.sin(np.pi * yn ** 0.60), 0, 1) ** 1.12 + 0.10 * (1.0 - yn)
    hw = hw * (1.0 + 0.20 * np.sin(yn * 4.6 - p))
    hw = np.clip(hw, 0.0, 1.0) * FLIP_MARGIN
    cx = 0.26 * yn ** 1.8 * math.sin(p)
    # ★알파는 폭으로 나누지 않는다(끝에서 1px 바늘이 남는다). 흐림 폭을 절대값으로.
    s = hw - np.abs(xx - cx) * (1.0 + 0.18 * (n - 0.5))
    a = np.clip(s / (0.55 * hw + 0.09), 0, 1) ** 0.85
    inw = np.clip(s / (hw + 0.05), 0, 1)
    t0 = 0.34 + 0.10 * math.cos(p * 1.3)
    t1 = 0.84 + 0.05 * math.sin(p * 0.7)
    tn = np.clip((yy - t0) / max(1e-3, t1 - t0), 0, 1)
    thw = 0.19 * np.clip(np.sin(np.pi * tn ** 0.55), 0, 1) ** 1.10 * FLIP_MARGIN
    tcx = 0.44 * math.sin(p + 2.2) * tn ** 1.4
    ts = thw - np.abs(xx - tcx) * (1.0 + 0.22 * (n - 0.5))
    tk = 0.34 + 0.66 * (0.5 + 0.5 * math.sin(p + 0.6))
    ta = np.clip(ts / (0.55 * thw + 0.07), 0, 1) ** 0.90 * tk
    a = np.clip(np.maximum(a, ta), 0, 1)
    a = a * np.clip((1.0 - yy) / 0.05, 0, 1)
    edge = np.clip((1.0 - np.abs(xx)) / (1.0 - FLIP_MARGIN), 0, 1)
    a = a * (edge * edge * (3 - 2 * edge))
    core = np.clip(inw * (1.0 - yy * 0.8), 0, 1) ** 2.2
    core = core * (0.88 + 0.12 * math.cos(p * 2.0))
    t = np.broadcast_to(np.clip(yy, 0, 1), (h, w))[:, :, None]
    rgb = FLAME_MID[None, None, :] * (1 - t) + FLAME_TIP[None, None, :] * t
    rgb = rgb * (1 - core[:, :, None]) + FLAME_HOT[None, None, :] * core[:, :, None]
    return np.clip(np.nan_to_num(rgb), 0, 1), np.nan_to_num(a)


def bake_flame_flip(w, h, n=FLIP_N):
    rgbs, alphas = [], []
    for f in range(n):
        p = 2.0 * math.pi * f / n
        # 잡결 시드도 칸마다 바꾼다. 같은 시드면 실루엣만 흐물거리는 "젤리"가 된다
        r, a = _flame_frame(w, h, p, 4021 + f * 97)
        rgbs.append(r)
        alphas.append(a)
    return np.concatenate(rgbs, axis=1), np.concatenate(alphas, axis=1)


# ═════════════════════════════════════════════════════════════
# 바닥 — 컨셉 견본(bs_tiles.png)을 이어붙임화
# ═════════════════════════════════════════════════════════════
def bake_floor(variant=0):
    """bs_tiles.png -> 이어붙는 바닥 타일.

    variant 0 = 그대로 · 1 = 180도 돌리고 조금 서늘하게(같은 그림이 두 벌 깔리는
    것을 눈이 알아채지 못하게 하는 값싼 변주. 새 텍스처를 굽는 것보다 glb 가 싸다).
    """
    im = Image.open(SRC_TILES).convert("RGB")
    if variant == 1:
        im = im.rotate(180)
    a = np.asarray(im.resize((RES, RES), Image.LANCZOS), np.float32) / 255.0
    # ① 한 장짜리 그림의 사선 명암 얼룩을 나눠 없앤다(안 하면 5m 마다 그 얼룩이 온다)
    a = flatten_lowfreq(a, int(RES * 0.375), amount=0.86)
    # ② 이어붙임화(Moisan periodic 분해. 그림을 한 톨도 안 지운다)
    a, seam = _tz.make_tileable(a, "dg_floor_v%d" % variant)
    a = calm_fine(a, keep=0.78)
    # ③ 채도. 컨셉 화면 S 중앙값이 0.60 인데 ACES 가 밝은 쪽 채도를 반 토막 낸다
    #   (tools/color_contract.py 상단 실측표). 알베도에서 미리 올려 둔다.
    a = push_chroma(a, 0.24 if variant == 0 else 0.18)
    if variant == 1:
        # 변주는 조금 서늘하게(빨강 -4% · 파랑 +5%). 두 벌이 붙어도 경계가 안 선다
        a = np.clip(a * np.array((0.96, 0.99, 1.05), np.float32)[None, None, :], 0, 1)
    a, gain = normalize_mean(a)
    return a, gain, seam


# ═════════════════════════════════════════════════════════════
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    meta = {"src": "incoming/codex_dungeon2/bs_tiles.png (바닥) + 절차(벽·메달리온)",
            "res": RES, "lin": {}, "gain": {}, "seam": {}, "stat": {}}
    print("[원자재] %s" % SRC_TILES)

    for variant, name in ((0, "dg_floor"), (1, "dg_floor_b")):
        print("\n[%s]  컨셉 견본 이어붙임화" % name)
        a, gain, seam = bake_floor(variant)
        meta["lin"][name] = save_rgb(name, a)
        meta["gain"][name] = round(float(gain), 4)
        meta["seam"][name] = seam["after"]
        meta["stat"][name] = _tex_stat(a, name)
        print("   [화풍] %s" % meta["stat"][name])

    print("\n[dg_wall]  절차 — 큰 둥근 블록 %d단 x %d장 (UV 3.6m 기준 1.20x0.60m)"
          % (WALL_COURSES, WALL_PER_COURSE))
    w = bake_wall()
    # ★벽 타일을 0.44 -> 0.56 으로 밝혔다. 밝기가 올라가는 게 아니라 **곱수에 자리를
    #   만드는** 일이다: k = 목표휘도 / (타일휘도 x 정점색평균) <= 1 이 계약인데,
    #   벽 목표(#625f73, 휘도 0.119)를 정점색 0.42 로 나누면 타일 휘도가 0.28 이상
    #   있어야 한다. 0.44 판은 0.182 라 곱수가 1.56 으로 잘렸다(= 계약 파기).
    w, wgain = normalize_mean(w, 0.56)
    meta["lin"]["dg_wall"] = save_rgb("dg_wall", w)
    meta["gain"]["dg_wall"] = round(float(wgain), 4)
    meta["stat"]["dg_wall"] = _tex_stat(w, "dg_wall")
    print("   [화풍] %s" % meta["stat"]["dg_wall"])

    print("\n[dg_block]  절차 — 다듬은 돌(기둥·아치·제단·계단)")
    b = bake_wall(seed=2207, mix=BLOCK_MIX, base=BLOCK_BASE, pull=BLOCK_PULL,
                  sat=1.02, moss=False, jitter=0.10)
    b, bgain = normalize_mean(b, 0.70)
    meta["lin"]["dg_block"] = save_rgb("dg_block", b)
    meta["gain"]["dg_block"] = round(float(bgain), 4)
    meta["stat"]["dg_block"] = _tex_stat(b, "dg_block")
    print("   [화풍] %s" % meta["stat"]["dg_block"])

    print("\n[dg_medallion]  절차 — 청록 팔각 + 금테")
    med, ma = bake_medallion(256)
    save_rgba("dg_medallion", med, ma)
    meta["lin"]["dg_medallion"] = [float(x) for x in srgb_to_lin(med).reshape(-1, 3).mean(axis=0)]
    meta["gain"]["dg_medallion"] = 1.0

    print("\n[절차 · 빛과 얼룩]")
    bake_light_only()
    rgb, a = bake_flame(128, 192)
    save_rgba("dg_flame", rgb, a)
    rgb, a = bake_wear(256)
    save_rgba("dg_wear", rgb, a)
    meta["lin"]["dg_wear"] = [float(x) for x in srgb_to_lin(rgb).reshape(-1, 3).mean(axis=0)]
    bake_flip_only()

    with open(META, "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("\n[메타] %s" % META)


def bake_light_only():
    """**빛 데칼만** 굽는다(웜 풀 · 찬 웅덩이 · 빛기둥 · 벽 자국).

    ★따로 뗀 이유: main() 은 dungeon_tex.json 의 평균·게인을 다시 쓰는데 그 값이
      이미 구워 둔 level2.glb 의 재질 곱수와 짝이다. 이 넉 장은 `mat_glow` 가 쓰는
      이미시브라 **곱수 계약 밖**이라 혼자 구워도 맵 색이 안 밀린다.
    ★단 s40 은 다시 돌려야 한다 — 이미지가 glb 안에 들어 있다."""
    os.makedirs(OUT_DIR, exist_ok=True)
    rgb, a = bake_pool(256, (POOL_HOT, POOL_MID, POOL_TIP), 311,
                       squash=1.0, wob=0.22, core=0.28, amax=0.72,
                       tail=0.70, rough=0.44)
    save_rgba("dg_pool", rgb, a)
    # 계단의 찬 빛. 청록(메달리온 계열)이다 — 이 팔레트에서 파랑은 어둠의 색이다
    rgb, a = bake_pool(256, ((0.80, 1.00, 0.98), (0.34, 0.86, 0.90), (0.16, 0.52, 0.68)),
                       517, squash=0.74, wob=0.16, core=0.44, amax=0.80,
                       tail=0.66, rough=0.34)
    save_rgba("dg_pool_cold", rgb, a)
    rgb, a = bake_shaft(128, 512)
    save_rgba("dg_shaft", rgb, a * 0.36)
    rgb, a = bake_wall_glow(128, 192)
    save_rgba("dg_wglow", rgb, a)


def bake_flip_only():
    """불꽃 플립북만 굽는다(glb 밖 · 런타임 로드라 혼자 구울 수 있다)."""
    os.makedirs(OUT_DIR, exist_ok=True)
    print("[불꽃 플립북] %d칸" % FLIP_N)
    rgb, a = bake_flame_flip(128, 192)
    save_rgba("dg_flame_fb", rgb, a)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "flame":
        bake_flip_only()
    elif len(sys.argv) > 1 and sys.argv[1] == "light":
        bake_light_only()
    elif len(sys.argv) > 1 and sys.argv[1] == "wall":
        # 벽만 미리보기(굽기 반복용. 메타는 안 건드린다)
        w = bake_wall()
        w, _ = normalize_mean(w, 0.56)
        save_rgb("dg_wall", w)
        print(_tex_stat(w, "dg_wall"))
    else:
        main()
