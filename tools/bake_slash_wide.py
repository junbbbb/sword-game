# -*- coding: utf-8 -*-
"""참격 플립북 **굵은 판** 시트를 굽는다 (web/tex/slash_flip2.png).

  2048 x 2688 = 가로 2칸(가로베기 h · 대각베기 d) x 세로 6칸(f0~f5)
  칸 하나 1024 x 448

── 왜 새로 굽나 ──
블라인드 심사관이 기존 slash_flip.png 을 두 가지 이유로 떨어뜨렸다.

  (1) 화면 점유 0.5~1.4% (귀멸 15~57%)
      획이 가늘고 길다. 칸 1024x320 에 몸통이 칸 높이의 0.375배뿐이었다.
      귀멸의 획은 **짧고 굵다**. 게임은 판정 리치(3.2m) 계약 때문에 길이를
      못 늘린다 → **획에 수직인 방향, 즉 굵기로 존재감을 낸다.**
      그래서 칸을 320 -> 448 로 키우고 몸통을 칸 높이의 0.60~0.66배로 굽는다.

  (2) 경계 먹선 비율 11~14% (귀멸 40~63%)
      기존 코드는 먹 테두리를 **갈필 이전의 solid 실루엣**에서 떴다. 그래서
      갈필로 찢긴 구멍·조각의 경계에는 먹선이 없었고, 실제 알파 경계의
      대부분이 파랑(edge)으로 드러났다.
      이번에는 **최종 알파 실루엣**에서 테두리를 뜬다. 찢겨 나간 조각도
      각자 제 먹 테두리를 갖는다. 이게 애니 먹선의 정의다.

── 문법은 bake_slash_flip.py 를 그대로 물려받는다 ──
평칠 계단 · 스트레이트 알파 · 먹 번짐(bleed) · 갈필. fbm1 · fbm2 ·
stepped_alpha · bleed_rgb · save_rgba · hexf 를 bake_fx_tex.py 에서 import 한다.
파일을 가른 것은 기존 두 파일(bake_fx_tex.py · bake_slash_flip.py)을 다른
작업이 같은 시각에 쓰고 있어서다. 기존 시트는 폴백으로 남긴다.

── ★밝기 계약 (여기를 어기면 게임에서 색이 통째로 틀어진다) ──
이 시트는 **회색조**다. 색은 셰이더가 팔레트로 다시 칠한다(물=감청 / 처치=진홍).
      먹(ink)  0.12
      가장자리 0.45
      중간     0.70
      흰 심    0.95
셰이더는 lum > thr.z ? core : lum > thr.y ? mid : lum > thr.x ? edge : ink 로 칠한다.
★텍스처를 sRGB 로 읽으면 안 된다(0.45 가 0.17 로 내려앉아 계단이 무너진다).
그래서 여기서도 감마 보정을 하지 않는다. 값을 그대로 uint8 로 박는다.

── 이번 판에서 달라진 그림 문법 ──
  · 먹 외곽선을 **최종 실루엣**에서 뜬다(위 (2)). 두께 14px 안팎,
    붓이 눌린 아래쪽은 한 단 더 굵다.
  · 흰 심이 획 한가운데가 아니라 **위쪽으로 치우쳐** 있다(-0.26). 붓으로 읽히려면
    단면이 비대칭이어야 한다. 귀멸 실프레임에서 확인한 배치다.
  · **등간격 평행 띠 금지.** 획 안의 결은 (a) 알파를 뚫는 갈라짐(gap)과
    (b) 통짜 먹 자국(ink line) 두 가지인데, 둘 다 시작점·기울기·굵기가 전부
    다르고 양끝이 뾰족하게 사라진다. 심사관이 "천으로 읽힌다"고 한 등간격
    줄무늬를 없애려는 것이다.
  · 알파는 **완전 이진**이다. 반투명 가장자리를 남기면 경계 링에 먹이 아닌
    화소가 끼어 (2) 가 다시 무너진다. 화면에서의 부드러움은 밉맵이 낸다.
  · 획의 구조(갈라짐 위치 · 심 경로 · 먹 자국)는 **프레임이 아니라 붓 종류마다**
    고정한다. 프레임마다 새로 뽑으면 가닥이 순간이동해서 눈 오는 화면이 된다.
    프레임마다 다시 뽑는 건 가장자리 노이즈뿐이다(작화의 boil).

── 프레임 진행 (본 획은 짧게 산다) ──
  f0 起筆   짧고 제일 두껍게 눌러 넣은 머리
  f1 送筆   절반쯤 뻗음. 몸통 최대 굵기
  f2 全長   끝까지 뻗음. 갈필 시작
  f3 裂     꼬리가 찢겨 나가기 시작 (여기까지가 '본 획')
  f4 散     가닥으로 갈라지고 조각이 튄다 (가는 먹 자취 수준)
  f5 殘     성긴 먹 조각 몇 개만
★f4·f5 는 **덮는 넓이**가 확 준다. 다만 조각이 획이 있던 자리 전체에 흩어지므로
  세로 범위(칸 높이 대비 0.60~0.70)는 그대로다. 이건 의도다.

실행:
    python3 tools/bake_slash_wide.py              # 시트 + 검증 + 미리보기
    python3 tools/bake_slash_wide.py --tex-only   # 시트 + 검증만
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bake_fx_tex import (fbm1, fbm2, stepped_alpha, save_rgba, bleed_rgb, hexf)  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(ROOT, "web", "tex")
OUT_DIR = os.path.join(ROOT, "renders", "history", "v94_wave9", "fx", "tex")
ANIME_DIR = os.path.join(ROOT, "renders", "history", "v93_gauntlet", "fx", "frames", "anime")

CW, CH = 1024, 448          # 칸 하나 (기존 1024x320 에서 세로 1.4배)
NCOL, NROW = 2, 6
SHEET_W, SHEET_H = CW * NCOL, CH * NROW

# ── 밝기 계단 (위 '밝기 계약') ──
L_INK = 0.12
L_EDGE = 0.45
L_MID = 0.70
L_CORE = 0.95

# ── 먹 외곽선 ──
# 칸이 세로로 1.4배 커졌으니 기존 RIM=10 도 비례로 키운다. 몸통 270px 기준
# 14px 은 단면의 5% 남짓 — 귀멸 실프레임에서 잰 먹선 두께와 같은 비율이다.
# ★다만 두께를 상수로 박으면 안 된다. 획 끝의 가는 꼬리나 찢겨 나간 가는 가닥은
#   14px 테두리 두 줄에 통째로 잡아먹혀 새까만 창날이 된다(1차 시도의 실패).
#   그래서 **국소 두께에 비례**시킨다. 붓펜으로 그린 윤곽선과 같은 원리다.
RIM_MAX = 14                # 두꺼운 몸통에서의 먹선 두께 상한(px)
RIM_MIN = 2                 # 아무리 가늘어도 이만큼은 먹선을 두른다
RIM_K = 0.31                # 국소 반두께 대비 먹선 비율
RIM_OUT = 1.55              # 붓이 눌린 아래쪽은 이 배수만큼 더 굵다
DMAX = 42                   # 거리변환 상한(px). 이보다 두꺼우면 다 같은 '두꺼움'
MARGIN_X = 16               # 칸 좌우 여백(px)
MARGIN_Y = 14               # 칸 위아래 여백(px). 이웃 칸이 필터링으로 새어 들지 않게

# ── 획 뼈대 ──
# maxhw = 칸 높이 대비 반두께. 몸통 = 2 * maxhw ≒ 0.60. 가장자리 흔들림이
# 여기에 ±0.03 을 더해 최종 세로범위가 0.60~0.70 에 들어온다.
CY0_H, BOW_H, MAXHW_H = 0.335, 0.105, 0.300
CY0_D, BOW_D, MAXHW_D = 0.315, 0.108, 0.296

# ── 단면 계단 (tt = -1(위) .. +1(아래) 정규화 좌표) ──
# 귀멸 water_wheel_arc 를 재 보면 흰 심이 **앞쪽(안쪽) 가장자리에 바싹 붙어** 있고
# 반대쪽에 짙은 파랑이 넓게 깔린다. 가운데 심은 CG 광선으로 읽힌다.
CORE_OFF = -0.38            # ★흰 심 중심. 0 이 아니다. 위로 치우쳐야 붓으로 읽힌다
CORE_HW = 0.192             # 흰 심 반폭(tt 단위) 기준값. 칸마다 아래 목표로 다시 푼다
CORE_TARGET = 0.145         # 불투명 화소 중 흰 심이 차지할 비율(검증 기준 8~20% 한가운데)
MID_HW = 0.46               # 중간 톤 반폭. 아래쪽에 가장자리(0.45)가 넓게 남는다

ALPHA_CUT = 154             # stepped_alpha 의 이 단 이상을 불투명으로 눌러 붙인다

STRUCT_SEED = 940911        # 붓 구조(갈라짐·심 경로·먹 자국) 씨앗. 프레임 불변
NOISE_SEED = 940912         # 가장자리 노이즈 씨앗. 프레임마다 다시 뽑는다(boil)

# 프레임표
#   u0,u1  = 꼬리·머리 위치 / tk = 굵기배수 / dry = 갈필세기 / frag = 튄 조각 수
#   gapw   = 갈라짐 최대 반폭(tt) / gfl = 획 전체가 벌어지는 정도(0=끝만)
#   dash   = 길이방향으로 잘려 나가는 넓이 비율(0..1)
# ★꼬리(u0)를 많이 밀지 않는다. 밀면 제일 두꺼운 구간이 통째로 사라져서
#   세로범위(존재감)가 무너진다. 뒤 프레임의 소멸은 '넓이'로 내지 '길이'로 내지 않는다.
FRAMES = {
    "h": [
        dict(u0=0.00, u1=0.32, tk=1.10, dry=0.03, frag=0, gapw=0.000, gfl=0.00, dash=0.00),
        dict(u0=0.00, u1=0.68, tk=1.00, dry=0.13, frag=1, gapw=0.028, gfl=0.00, dash=0.00),
        dict(u0=0.02, u1=1.00, tk=0.99, dry=0.30, frag=3, gapw=0.052, gfl=0.12, dash=0.00),
        dict(u0=0.09, u1=1.00, tk=0.99, dry=0.52, frag=6, gapw=0.088, gfl=0.46, dash=0.13),
        dict(u0=0.15, u1=1.00, tk=1.00, dry=0.80, frag=8, gapw=0.132, gfl=0.88, dash=0.71),
        dict(u0=0.21, u1=1.00, tk=1.01, dry=0.94, frag=7, gapw=0.172, gfl=1.00, dash=0.90),
    ],
    "d": [
        dict(u0=0.00, u1=0.30, tk=1.11, dry=0.03, frag=0, gapw=0.000, gfl=0.00, dash=0.00),
        dict(u0=0.00, u1=0.70, tk=1.02, dry=0.15, frag=2, gapw=0.030, gfl=0.00, dash=0.00),
        dict(u0=0.02, u1=1.00, tk=1.00, dry=0.34, frag=4, gapw=0.056, gfl=0.14, dash=0.00),
        dict(u0=0.10, u1=1.00, tk=1.00, dry=0.56, frag=7, gapw=0.094, gfl=0.50, dash=0.15),
        dict(u0=0.16, u1=1.00, tk=1.01, dry=0.82, frag=9, gapw=0.138, gfl=0.90, dash=0.66),
        dict(u0=0.22, u1=1.00, tk=1.02, dry=0.95, frag=8, gapw=0.178, gfl=1.00, dash=0.85),
    ],
}


# ─────────────────────────────────────────────────────────────
# 작은 도구
# ─────────────────────────────────────────────────────────────
def _erode(m, n):
    """4이웃 침식 n 번. L1 거리 n 만큼 안으로 파고든 마스크.
    (scipy 없이 쓰려고 이렇게 한다. 448x1024 라 순식간이다)"""
    out = m.copy()
    for _ in range(n):
        p = np.pad(out, 1, mode="constant", constant_values=False)
        out = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    return out


def _l1dist(m, dmax):
    """배경까지의 L1 거리(상한 dmax). 경계 바로 안쪽 화소가 0 이다.
    침식을 dmax 번 쌓아 만든다(scipy 없이)."""
    d = np.zeros(m.shape, np.int16)
    cur = m
    for _ in range(dmax):
        p = np.pad(cur, 1, mode="constant", constant_values=False)
        cur = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        d += cur
    return d


def _dmax_spread(d, n):
    """반지름 n 안의 최대 거리값을 퍼뜨린다 = '이 화소가 속한 덩어리가 얼마나 두꺼운가'.
    먹선 두께를 국소 두께에 비례시키려면 이 값이 필요하다."""
    out = d
    for _ in range(n):
        p = np.pad(out, 1, mode="edge")
        out = np.maximum.reduce([p[1:-1, 1:-1], p[:-2, 1:-1], p[2:, 1:-1],
                                 p[1:-1, :-2], p[1:-1, 2:]])
    return out


def _rank01(a):
    """값을 0..1 순위로 바꾼다. fbm 은 0.5 근처에 몰려 있어서 문턱을 비율로
    잡으려면 이렇게 펴야 한다(문턱 0.4 = 정확히 아래쪽 40%)."""
    flat = a.ravel()
    order = np.argsort(flat, kind="stable")
    r = np.empty(order.shape, np.float32)
    r[order] = np.linspace(0.0, 1.0, flat.size, dtype=np.float32)
    return r.reshape(a.shape)


def _wob(w, cells, rng, amp):
    """획을 따라 천천히 흔들리는 값 (-amp..+amp). 손이 떨린 자국"""
    return ((fbm1(w, cells, rng, octaves=2) - 0.5) * 2.0 * amp).astype(np.float32)


def _spike(u, a, b, ra, rb, p=0.85):
    """[a,b] 구간에서만 1 이고 양끝이 뾰족하게 0 으로 죽는 램프.
    ra·rb 가 양끝의 뾰족함(길이). 이게 '끝이 갈라지는 붓획'의 뼈대다"""
    return (np.clip((u - a) / max(ra, 1e-3), 0, 1) ** p
            * np.clip((b - u) / max(rb, 1e-3), 0, 1) ** p).astype(np.float32)


# ─────────────────────────────────────────────────────────────
# 붓 구조 (프레임이 바뀌어도 고정)
# ─────────────────────────────────────────────────────────────
def _brush_struct(style):
    """한 붓의 성격을 정한다. 갈라짐 5줄 · 통짜 먹 자국 3줄 · 흰 심 경로.
    ★굵기 · 간격 · 시작점이 전부 달라야 한다. 등간격이면 천으로 읽힌다."""
    r = np.random.default_rng(STRUCT_SEED + (0 if style == "h" else 7))

    # 갈라짐(alpha 를 뚫는다). 세 줄이면 충분하다. 다섯 줄이면 획이 '겹쳐 놓은 리본'이
    # 되고, 그게 심사관이 천이라고 한 그림이다.
    gaps = []
    for c, gfw, ue in ((-0.44, 1.30, 1.06), (0.02, 0.50, 0.62), (0.53, 0.95, 0.86)):
        gaps.append(dict(
            c0=float(c + r.uniform(-0.10, 0.10)),
            # ★기울기를 크게 준다. 갈라짐이 획과 나란히 흐르면 그게 바로 심사관이
            #   "천으로 읽힌다"고 한 등간격 줄무늬다. 가로지르며 벌어져야 붓털이다
            slope=float(r.uniform(0.28, 0.55)) * (1.0 if r.random() < 0.5 else -1.0),
            wcell=int(r.integers(4, 9)),
            wamp=float(r.uniform(0.03, 0.08)),
            scale=float(r.uniform(0.60, 1.45)),       # 줄마다 굵기가 다르다
            gfw=float(gfw),                           # 줄마다 벌어지는 속도가 다르다
            uend=float(ue),                           # 여기서 다시 아문다(끝까지 안 간다)
            us=float(r.uniform(0.24, 0.60)),          # 머리 쪽에서 열리기 시작하는 곳
            ur=float(r.uniform(0.20, 0.46)),          # 열리는 속도
            ut=float(r.uniform(0.05, 0.26)),          # 꼬리 쪽에서 열리는 곳
        ))
    # 통짜 먹 자국(알파를 안 뚫는다. 획 안을 가르는 가는 먹선). 귀멸 실프레임에서
    # 세어 보면 획 하나에 두세 줄뿐이고 전부 머리카락처럼 가늘다.
    lines = []
    for c in (-0.46, 0.22, 0.68):
        lines.append(dict(
            c0=float(c + r.uniform(-0.11, 0.11)),
            slope=float(r.uniform(0.24, 0.48)) * (1.0 if r.random() < 0.5 else -1.0),
            wcell=int(r.integers(3, 6)),              # 잔물결이 심하면 마디진 벌레가 된다
            wamp=float(r.uniform(0.010, 0.026)),
            hw=float(r.uniform(0.007, 0.017)),        # 2~5px. 굵으면 검은 화살촉이 된다
            a=float(r.uniform(0.05, 0.36)),
            b=float(r.uniform(0.60, 1.02)),
            ra=float(r.uniform(0.16, 0.34)),          # 길게 뾰족해야 붓끝으로 읽힌다
            rb=float(r.uniform(0.18, 0.40)),
        ))
    core = dict(
        slope=float(r.uniform(-0.09, 0.09)),
        wcell=int(r.integers(5, 8)),
        wamp=float(r.uniform(0.05, 0.09)),
        seg=int(r.integers(7, 11)),                   # 심 굵기가 출렁이는 마디 수
    )
    return dict(gaps=gaps, lines=lines, core=core, seed=int(r.integers(0, 10 ** 6)))


# ─────────────────────────────────────────────────────────────
# 칸 하나
# ─────────────────────────────────────────────────────────────
def _cell(style, fi, st):
    """(cov 0..1, lum 0..1) 을 준다"""
    W, H = CW, CH
    rng = np.random.default_rng(NOISE_SEED + fi * 31 + (0 if style == "h" else 977))
    srng = np.random.default_rng(st["seed"])          # 구조용(프레임 불변)

    F = FRAMES[style][fi]
    u0, u1, tk, dry = F["u0"], F["u1"], F["tk"], F["dry"]

    # u 는 칸 좌표가 아니라 **획 좌표**다. 0..1 을 [MARGIN_X, W-MARGIN_X] 에 편다
    u = (np.arange(W, dtype=np.float32) - MARGIN_X) / (W - 1.0 - 2 * MARGIN_X)
    y = np.arange(H, dtype=np.float32)[:, None]
    s = 2.0 * u - 1.0

    if style == "h":
        # 가로베기: 얕게 아래로 부른 호. 몸통이 앞쪽 1/3
        cy = H * (CY0_H + BOW_H * (1.0 - s * s))
        prof = np.interp(u, [0.00, 0.04, 0.12, 0.26, 0.44, 0.62, 0.80, 0.92, 1.00],
                            [0.05, 0.62, 0.95, 1.00, 0.95, 0.82, 0.58, 0.28, 0.03])
        maxhw = H * MAXHW_H
    else:
        # 대각베기: 더 깊게 휘고 끝에서 한 번 더 채인다(S)
        cy = H * (CY0_D + BOW_D * (1.0 - s * s) + 0.030 * np.sin(np.pi * u * 1.7))
        prof = np.interp(u, [0.00, 0.04, 0.10, 0.22, 0.40, 0.60, 0.78, 0.90, 1.00],
                            [0.05, 0.70, 1.00, 0.98, 0.86, 0.66, 0.42, 0.20, 0.03])
        maxhw = H * MAXHW_D
    cy = cy.astype(np.float32)
    hw = np.maximum(maxhw * tk * prof, 2.0).astype(np.float32)

    # 손그림 흔들림 세 벌(위 가장자리 · 아래 가장자리 · 잔결). 프레임마다 다시 뽑는다
    coarse_t = fbm2(H, W, 2, 8, rng, octaves=3)
    coarse_b = fbm2(H, W, 2, 7, rng, octaves=3)
    fine = fbm2(H, W, 3, 34, rng, octaves=2)

    tt = ((y - cy[None, :]) / hw[None, :]).astype(np.float32)
    at = np.abs(tt)
    # 찢김은 마를수록 커진다. 앞 프레임은 젖은 붓이라 매끈하고 뒤는 이가 빠진다
    e_top = 1.00 + (0.10 + 0.17 * dry) * (coarse_t - 0.5) * 2 + 0.045 * (fine - 0.5) * 2
    e_bot = 1.00 + (0.13 + 0.21 * dry) * (coarse_b - 0.5) * 2 + 0.060 * (fine - 0.5) * 2
    edge = np.where(tt < 0, e_top, e_bot).astype(np.float32)

    # 머리: 비스듬히 뾰족하게 끊는다(수직으로 자르면 붓이 아니라 잘린 띠다).
    # ★짧은 프레임(f0·f1)일수록 더 크게 눕혀 자른다. 안 그러면 起筆이 둥근 돌멩이가 된다
    ttc = np.clip(tt, -1.6, 1.6)
    if u1 >= 0.999:
        head = np.ones((H, W), np.float32)            # 프로파일이 이미 뾰족하다
    else:
        hs = 0.042 + 0.048 * (1.0 - u1)
        uh = u1 - hs * ttc - 0.40 * hs * ttc * ttc + 0.020 * (fine - 0.5) * 2
        head = np.clip((uh - u[None, :]) / 0.045, 0, 1)
    # 꼬리: 起筆(눌러 넣은 자국) -> 뒤 프레임에서는 찢겨 나간 자리
    ut = (u0 + 0.048 * ttc + 0.030 * ttc * ttc
          + (0.016 + 0.060 * dry) * (coarse_t - 0.5) * 2)
    tail = np.clip((u[None, :] - ut) / (0.028 + 0.058 * dry), 0, 1)
    live = (head * tail).astype(np.float32)

    inbox = (((np.arange(W)[None, :] >= MARGIN_X) & (np.arange(W)[None, :] <= W - 1 - MARGIN_X))
             & ((y >= MARGIN_Y) & (y <= H - 1 - MARGIN_Y))).astype(np.float32)

    # 실루엣(픽셀 2.6px 안에서 딱 끊는다. 그라데이션이 아니다)
    soft = np.maximum(2.6 / hw[None, :], 1e-4)
    cov = np.clip((edge - at) / soft, 0, 1) * live * inbox

    # ★이미 가는 데는 더 안 갈라진다. 붓이 그렇다. 이걸 안 걸면 획 끝의 가는 꼬리가
    #   갈라짐·먹자국에 난도질당해 새까만 창날이 된다.
    fat = np.clip((hw - 28.0) / 48.0, 0, 1).astype(np.float32)

    # 흰 심이 흐르는 경로(단면에서 어디가 젖어 있는가). 갈필이 이 줄기를 피해 가야
    # 하므로 여기서 미리 잡는다
    C = st["core"]
    cc0 = (CORE_OFF + C["slope"] * (u - 0.5) * 2.0
           + _wob(W, C["wcell"], srng, C["wamp"])).astype(np.float32)

    # ── 갈라짐(갈필) ── 굵기·기울기·시작점이 전부 다른 붓털 틈.
    #   앞 프레임에는 양끝에서만 살짝 벌어지고(gfl=0), 뒤 프레임에는 획 전체가 벌어진다.
    if F["gapw"] > 1e-4:
        for g in st["gaps"]:
            gc = (g["c0"] + g["slope"] * (u - 0.5) * 2.0
                  + _wob(W, g["wcell"], srng, g["wamp"]))
            open_h = np.clip((u - g["us"]) / g["ur"], 0, 1) ** 0.9
            open_t = np.clip((g["ut"] + u0 - u) / 0.24, 0, 1) ** 0.9
            openf = np.clip(np.maximum(np.maximum(open_h, open_t), F["gfl"] * g["gfw"]), 0, 1)
            # 줄마다 다른 데서 아문다. 셋이 나란히 끝까지 가면 리본 세 장이 된다
            openf = openf * np.clip((g["uend"] - u) / 0.14, 0, 1)
            # ★젖어 있는 심 줄기는 갈라지지 않는다. 붓에서 먹을 머금은 가운데 털이
            #   제일 늦게까지 붙어 있기 때문이다. 이걸 안 걸면 어떤 붓은 심이 통째로
            #   잘려 흰 심이 사라지고(h4) 어떤 붓은 멀쩡해(d4) 프레임마다 널을 뛴다.
            wetguard = np.clip(np.abs(gc - cc0) / 0.34, 0.20, 1.0)
            gw = (F["gapw"] * g["scale"] * openf * fat * wetguard).astype(np.float32)
            d = np.abs(tt - gc[None, :])
            cov = cov * (1.0 - np.clip((gw[None, :] - d) / soft, 0, 1))

    # ── 길이방향 끊김 ── 뒤 프레임에서 가닥이 조각으로 잘린다.
    #   ★꼬리 쪽을 더 세게 판다. 꼬리가 찢겨 나가는 게 f3~f5 의 이야기다.
    #   ★그러면서도 '길이를 자르지'는 않는다. 획이 있던 자리 전체에 조각이 흩어져야
    #     세로 존재감(칸 대비 0.6배)이 유지된다.
    if F["dash"] > 1e-4:
        # ★결이 획 방향으로 길어야 한다(가로 셀 5개 = 200px 길이). 정사각 얼룩으로
        #   자르면 색종이 조각(confetti)이 되지 먹 자취가 안 된다.
        #   세로 셀도 성기게(10) 잡아야 남는 가닥이 20~45px 로 두툼해서 흰 심을 품는다.
        #   ★가로 셀을 2 까지 늘린 이유: 4 였을 때 노이즈 최저점이 동그란 얼룩이
        #     되어 획에 **구멍이 뚫린 것처럼** 보였다. 길쭉해야 찢긴 자국이 된다.
        dsh = _rank01(fbm2(H, W, 10, 2, rng, octaves=2))
        grad = np.clip((u - u0) / 0.62, 0, 1).astype(np.float32)     # 꼬리 0 → 머리 1
        # ★심에서 먼 바깥 털부터 마른다. 젖어 있는 심 줄기가 제일 늦게까지 남는다.
        #   덕분에 f4·f5 에도 흰 심이 한 줄기 남아 '어디를 벴는지'가 읽힌다.
        wet = np.clip(np.abs(tt - cc0[None, :]) / 0.85, 0, 1.35).astype(np.float32)
        cutp = (F["dash"] * (1.0 - 0.42 * grad))[None, :] * (0.64 + 0.62 * wet)
        cov = cov * (dsh >= cutp).astype(np.float32)

    # ── 튄 조각 ── 획이 있던 자리 안쪽으로 몇 점. 작은 것은 통째로 먹이 된다
    #   ★가운데를 밝게 비우면 동그란 고리(비눗방울)로 보인다. 애니의 튄 먹은 꽉 찬 점이다.
    #   ★조각이 획 바깥으로 튀면 세로범위가 멋대로 늘어난다. 획의 세로 봉투 안에 가둔다.
    env_t = float(np.min(cy - hw))
    env_b = float(np.max(cy + hw))
    frng = np.random.default_rng(NOISE_SEED + 5000 + fi * 13 + (0 if style == "h" else 611))
    for k in range(F["frag"]):
        uu = float(frng.uniform(max(0.0, u0 - 0.02), min(1.02, u1 + 0.06)))
        cxp = MARGIN_X + uu * (W - 1.0 - 2 * MARGIN_X)
        rr = float(frng.uniform(5.0, 20.0)) * (1.0 - 0.42 * F["gfl"])
        ar = float(frng.uniform(1.6, 3.4))
        if F["gfl"] > 0.5 and k < 2:
            # 뒤 프레임에서는 위·아래 끝에 조각을 하나씩 박아 둔다. 본 획이 다 흩어져도
            # '거기 획이 있었다'는 세로 존재감이 남는다
            cyp = (env_t + rr + 2.0) if k == 0 else (env_b - rr - 2.0)
        else:
            base = float(np.interp(np.clip(uu, 0, 1), u, cy))
            cyp = base + float(frng.normal(0.0, maxhw * 0.62)) * (1.0 if frng.random() < 0.62 else -1.0)
        cyp = float(np.clip(cyp, env_t + rr, env_b - rr))
        if not (MARGIN_X + rr * ar < cxp < W - MARGIN_X - rr * ar):
            continue
        if not (MARGIN_Y + rr < cyp < H - MARGIN_Y - rr):
            continue
        # ★몸통 한가운데에 조각을 얹으면 조각이 아니라 멍(먹 테두리를 두른 얼룩)이 된다.
        #   이미 꽉 찬 자리는 건너뛴다. 조각은 떨어져 나온 것이어야 조각으로 읽힌다
        if cov[int(cyp), int(cxp)] > 0.5:
            continue
        y0, y1 = int(cyp - rr - 2), int(cyp + rr + 3)
        x0, x1 = int(cxp - rr * ar - 2), int(cxp + rr * ar + 3)
        dy = (np.arange(y0, y1)[:, None] - cyp) / rr
        dx = (np.arange(x0, x1)[None, :] - cxp) / (rr * ar)
        # 마름모에 가까운 조각. 완전한 타원은 물방울로 보인다
        blob = (np.abs(dx) ** 1.35 + np.abs(dy) ** 1.35 < 1.0)
        cov[y0:y1, x0:x1] = np.maximum(cov[y0:y1, x0:x1], blob.astype(np.float32))

    cov = np.clip(cov, 0, 1)

    # ── 알파: 완전 이진 ──
    # stepped_alpha 의 계단을 받아 ALPHA_CUT 위를 통째로 눌러 붙인다.
    # 반투명 가장자리를 남기면 경계 링에 먹이 아닌 화소가 끼어 먹선 비율이 무너진다.
    a8 = stepped_alpha(cov)
    alpha = np.where(a8 >= ALPHA_CUT, 255, 0).astype(np.uint8)
    mout = alpha > 0

    # ── 먹 외곽선 ──
    # ★기존 판과 갈라지는 지점 (1). 갈필 이전 실루엣이 아니라 **최종 알파**에서 뜬다.
    #   찢겨 나간 조각도 각자 제 먹 테두리를 갖는다 → 경계 먹선 비율이 40%를 넘는다.
    # ★기존 판과 갈라지는 지점 (2). 두께가 국소 두께에 비례한다. 몸통에서는 14px,
    #   가는 가닥에서는 3~6px. 상수로 박으면 가는 가닥이 통째로 먹이 된다.
    dist = _l1dist(mout, DMAX)
    thick = _dmax_spread(dist, DMAX).astype(np.float32)
    rim_eff = np.clip(thick * RIM_K, RIM_MIN, RIM_MAX)
    rim = mout & (dist < rim_eff)
    rim |= mout & (tt > 0.06) & (dist < np.minimum(rim_eff * RIM_OUT, RIM_MAX * RIM_OUT))

    # ── 단면 계단 (안쪽부터 흰 심 -> 중간 -> 가장자리 -> 먹) ──
    # 그라데이션 없음. 흰 심은 한쪽으로 치우쳐 있다
    cc = cc0
    # 심은 양끝이 뾰족한 한 줄기로 길게 흐른다. 토막나면 CG 하이라이트로 읽힌다
    cramp = _spike(u, u0 + 0.02, u1 - 0.02, 0.055, 0.12, p=0.55)
    cnz = fbm1(W, C["seg"], srng, octaves=2)
    cw = (CORE_HW * cramp * np.clip(0.70 + 0.62 * cnz, 0, 1.25)).astype(np.float32)
    mw = (MID_HW + _wob(W, 5, srng, 0.05)).astype(np.float32)

    # ── 획 안의 가는 먹 자국 ── 양끝이 뾰족한 쐐기. 등간격 평행 띠가 아니다
    inkline = np.zeros((H, W), bool)
    for ln in st["lines"]:
        lc = (ln["c0"] + ln["slope"] * (u - 0.5) * 2.0
              + _wob(W, ln["wcell"], srng, ln["wamp"]))
        lh = ln["hw"] * fat * _spike(u, max(ln["a"], u0), min(ln["b"], u1 + 0.02),
                                     ln["ra"], ln["rb"])
        inkline |= (np.abs(tt - lc[None, :]) < lh[None, :])
    # 비백(飛白): 붓털 사이로 종이가 비친 자국. 알파를 뚫지 않고 먹으로만 남긴다.
    # ★세로 셀을 아주 잘게(120) 가로를 성기게(4) 잡아야 **머리카락 같은 긴 선**이 된다.
    #   세로를 성기게 잡으면 통통한 애벌레가 생긴다(2차 시도의 실패).
    # 심 쪽에는 안 넣는다(흰 심에 검은 점이 박히면 때가 탄 것처럼 보인다)
    vein = fbm2(H, W, 120, 4, rng, octaves=2)
    inkline |= (vein > (0.905 - 0.045 * dry)) & (tt > cc[None, :] + 0.14)

    def _paint(k):
        lum = np.full((H, W), L_EDGE, np.float32)
        lum[np.abs(tt - cc[None, :]) < mw[None, :]] = L_MID
        lum[np.abs(tt - cc[None, :]) < (cw * k)[None, :]] = L_CORE
        lum[inkline] = L_INK
        lum[rim] = L_INK
        return lum

    # ★흰 심 폭은 손으로 못 맞춘다.
    #   앞 프레임에서는 몸통이 통짜라 심 비율이 기하학대로 나오지만, 뒤 프레임은
    #   무엇이 찢겨 나갔느냐에 따라 남은 가닥 안에서의 심 비율이 6%에서 25%까지
    #   널을 뛴다(붓 종류마다 갈라짐 위치가 달라서). 프레임표를 아무리 만져도
    #   h4 를 올리면 d4 가 넘치고 d4 를 낮추면 h4 가 모자란다.
    #   그래서 칸마다 **폭을 이분법으로 풀어** 목표 비율에 맞춘다. 그림 문법은
    #   그대로고(심은 여전히 한쪽으로 치우친 한 줄기) 폭만 칸마다 달라진다.
    lo, hi = 0.20, 3.0
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        if float((_paint(mid)[mout] > 0.85).mean()) < CORE_TARGET:
            lo = mid
        else:
            hi = mid
    lum = _paint(0.5 * (lo + hi))

    return cov, lum, alpha


# ─────────────────────────────────────────────────────────────
# 시트
# ─────────────────────────────────────────────────────────────
def bake(path):
    sheet_rgb = np.zeros((SHEET_H, SHEET_W, 3), np.float32)
    sheet_a = np.zeros((SHEET_H, SHEET_W), np.uint8)
    for ci, style in enumerate(("h", "d")):
        st = _brush_struct(style)
        for fi in range(NROW):
            cov, lum, alpha = _cell(style, fi, st)
            rgb = np.repeat(lum[..., None], 3, axis=2)
            # 알파 0 자리도 이웃 색으로 채운다(확대 필터가 검은 링을 만들지 않게)
            rgb = bleed_rgb(rgb, alpha, iters=26, fill_hex="1F1F1F")
            y0, x0 = fi * CH, ci * CW
            sheet_rgb[y0:y0 + CH, x0:x0 + CW] = rgb
            sheet_a[y0:y0 + CH, x0:x0 + CW] = alpha
    tmp = path + ".tmp.png"          # PIL 은 확장자로 포맷을 정한다
    save_rgba(tmp, sheet_rgb, sheet_a)
    os.replace(tmp, path)                              # ★원자적 저장
    return path


# ─────────────────────────────────────────────────────────────
# 검증
# ─────────────────────────────────────────────────────────────
PEAKS = (L_INK, L_EDGE, L_MID, L_CORE)


def verify(path):
    a = np.asarray(Image.open(path).convert("RGBA"))
    print("[검증] %s  %dx%d · %.0f KB"
          % (os.path.basename(path), a.shape[1], a.shape[0],
             os.path.getsize(path) / 1024.0))
    rows = []
    for ci, style in enumerate(("h", "d")):
        for fi in range(NROW):
            c = a[fi * CH:(fi + 1) * CH, ci * CW:(ci + 1) * CW]
            lum = c[..., 0].astype(np.float32) / 255.0
            al = c[..., 3].astype(np.float32) / 255.0
            m = al > 0.5
            n = int(m.sum())
            if n == 0:
                continue
            # 1) 먹선 비율: 경계 1픽셀 링에서 휘도 < 0.30
            ring = m & ~_erode(m, 1)
            ink_ring = float((lum[ring] < 0.30).mean()) if ring.any() else 0.0
            # 2) 밝기 계약: 네 봉우리 ±0.06 안에 든 비율
            lv = lum[m]
            peak = float(sum(float((np.abs(lv - p) <= 0.06).mean()) for p in PEAKS))
            # 3) 몸통 굵기: 세로 범위 / 칸 높이
            ys = np.nonzero(m.any(axis=1))[0]
            span = (ys.max() - ys.min() + 1) / float(CH)
            # 4) 흰 심 비율
            core = float((lv > 0.85).mean())
            # 5) 알파 이진성
            nb = float(((al > 0.05) & (al < 0.95)).sum()) / max(1, float((al > 0.05).sum()))
            rows.append(dict(cell="%s%d" % (style, fi), n=n, cov=n / float(CH * CW),
                             ink=ink_ring, peak=peak, span=span, core=core, nbin=nb,
                             mtop=int(ys.min()), mbot=int(CH - 1 - ys.max()),
                             inkarea=float((lv < 0.30).mean())))
    print("  칸   덮음%    먹선링%   밝기봉%   세로범위   흰심%   먹넓이%  비이진%  여백 위/아래")
    ok = True
    for r in rows:
        f1 = "" if r["ink"] >= 0.40 else " ←먹선!"
        f2 = "" if r["peak"] >= 0.90 else " ←밝기!"
        f3 = "" if 0.60 <= r["span"] <= 0.70 else " ←굵기!"
        f4 = "" if 0.08 <= r["core"] <= 0.20 else " ←심!"
        f5 = "" if r["nbin"] < 0.06 else " ←알파!"
        f6 = "" if (r["mtop"] >= MARGIN_Y and r["mbot"] >= MARGIN_Y) else " ←여백!"
        bad = f1 + f2 + f3 + f4 + f5 + f6
        ok = ok and not bad
        print("  %-4s %6.2f   %6.1f    %6.1f    %6.4f    %5.1f   %5.1f    %5.2f   %3d/%3d%s"
              % (r["cell"], r["cov"] * 100, r["ink"] * 100, r["peak"] * 100,
                 r["span"], r["core"] * 100, r["inkarea"] * 100, r["nbin"] * 100,
                 r["mtop"], r["mbot"], bad))
    al = a[..., 3]
    print("  시트 알파: 0 %.1f%% · 255 %.1f%% · 사이 %.3f%%"
          % ((al == 0).mean() * 100, (al == 255).mean() * 100,
             ((al > 0) & (al < 255)).mean() * 100))
    lv, cnt = np.unique(a[..., 0][al > 128], return_counts=True)
    top = sorted(zip(cnt, lv), reverse=True)[:6]
    tot = max(1, int((al > 128).sum()))
    print("  밝기 상위: %s"
          % ", ".join("%.3f(%.1f%%)" % (v / 255.0, c / tot * 100) for c, v in top))
    print("  → 판정: %s" % ("통과" if ok else "미달"))
    return ok, rows


# ─────────────────────────────────────────────────────────────
# 미리보기 (게임 셰이더의 팔레트 칠을 그대로 재현한다)
#   lum > thr.z ? core : lum > thr.y ? mid : lum > thr.x ? edge : ink
# ─────────────────────────────────────────────────────────────
PAL = {
    "water": {"ink": "0a1430", "edge": "0c3c9c", "mid": "24ccfc", "core": "cce4fc",
              "thr": (0.30, 0.55, 0.82)},
    "kill": {"ink": "2a0710", "edge": "d21b32", "mid": "d21b32", "core": "fff2f2",
             "thr": (0.38, 0.82, 0.82)},
}
BG_DARK = "20242a"          # 귀멸 야간 배경과 비슷한 어두운 회청


def _paint(rgba, pal, bg_hex):
    lum = rgba[..., 0].astype(np.float32) / 255.0
    al = rgba[..., 3:4].astype(np.float32) / 255.0
    t0, t1, t2 = pal["thr"]
    h, w = lum.shape
    col = np.zeros((h, w, 3), np.float32)
    col[:] = hexf(pal["ink"])
    col[lum > t0] = hexf(pal["edge"])
    col[lum > t1] = hexf(pal["mid"])
    col[lum > t2] = hexf(pal["core"])
    bg = np.zeros((h, w, 3), np.float32)
    bg[:] = hexf(bg_hex)
    return np.clip(col * al + bg * (1 - al), 0, 1)


def _font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _label(img, text, xy, size=22):
    d = ImageDraw.Draw(img)
    f = _font(size)
    d.rectangle([xy[0] - 4, xy[1] - 3, xy[0] + int(size * 0.62 * len(text)) + 8,
                 xy[1] + size + 6], fill=(16, 16, 18))
    d.text(xy, text, font=f, fill=(240, 235, 200))


def preview_sheet(path, out):
    """시트 전체를 두 팔레트로 칠해 본다. 행=프레임, 열=h/d x 물/처치"""
    a = np.asarray(Image.open(path).convert("RGBA"))
    gap = 10
    tw, th = CW // 2, CH // 2
    cols = 4
    W = cols * tw + (cols + 1) * gap
    H = NROW * th + (NROW + 1) * gap + 34
    sheet = Image.new("RGB", (W, H), (26, 26, 30))
    order = [("h", "water"), ("d", "water"), ("h", "kill"), ("d", "kill")]
    for fi in range(NROW):
        for k, (style, pname) in enumerate(order):
            ci = 0 if style == "h" else 1
            c = a[fi * CH:(fi + 1) * CH, ci * CW:(ci + 1) * CW]
            img = Image.fromarray(np.uint8(_paint(c, PAL[pname], BG_DARK) * 255 + 0.5))
            img = img.resize((tw, th), Image.LANCZOS)
            sheet.paste(img, (gap + k * (tw + gap), 34 + gap + fi * (th + gap)))
    for k, (style, pname) in enumerate(order):
        _label(sheet, "%s / %s" % (style, pname), (gap + k * (tw + gap), 6), 20)
    tmp = out + ".tmp.png"
    sheet.save(tmp)
    os.replace(tmp, out)
    print("미리보기: %s %s" % (out, sheet.size))
    return out


ANIME_CROPS = [("water_wheel_arc.png", (0, 620, 1080, 1092)),
               ("striking_tide.png", (0, 240, 1080, 712))]


def preview_vs_anime(path, out, frames=(1, 2)):
    """귀멸 실프레임 옆에 게임 획을 나란히. 먹선 굵기 · 평칠 · 흰 심 위치를 눈으로 잰다"""
    a = np.asarray(Image.open(path).convert("RGBA"))
    tw, th = CW, CH
    gap = 12
    W = 2 * tw + 3 * gap
    H = 2 * th + 3 * gap + 34
    sheet = Image.new("RGB", (W, H), (26, 26, 30))
    for i, (fn, box) in enumerate(ANIME_CROPS):
        p = os.path.join(ANIME_DIR, fn)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB").crop(box).resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (gap, 34 + gap + i * (th + gap)))
        _label(sheet, "ANIME  " + fn.replace(".png", ""), (gap, 34 + gap + i * (th + gap) + 4), 20)
    for i, fi in enumerate(frames):
        c = a[fi * CH:(fi + 1) * CH, 0:CW]                # 가로베기
        img = Image.fromarray(np.uint8(_paint(c, PAL["water"], BG_DARK) * 255 + 0.5))
        sheet.paste(img, (gap * 2 + tw, 34 + gap + i * (th + gap)))
        _label(sheet, "GAME  h f%d  (water)" % fi,
               (gap * 2 + tw, 34 + gap + i * (th + gap) + 4), 20)
    _label(sheet, "ink line / flat fill / offset white core", (gap, 6), 22)
    tmp = out + ".tmp.png"
    sheet.save(tmp)
    os.replace(tmp, out)
    print("비교:     %s %s" % (out, sheet.size))
    return out


def main():
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(TEX_DIR, "slash_flip2.png")
    bake(p)
    print("구움: %s (%d bytes)" % (p, os.path.getsize(p)))
    ok, rows = verify(p)
    if "--tex-only" not in sys.argv:
        preview_sheet(p, os.path.join(OUT_DIR, "PREVIEW_slash_flip2.png"))
        preview_vs_anime(p, os.path.join(OUT_DIR, "PREVIEW_vs_anime.png"))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
