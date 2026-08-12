# -*- coding: utf-8 -*-
"""던전 1층 텍스처를 **롤·나혼렙 풍**으로 굽는다 (15차 파도. 전면 재작).

    python3 tools/dungeon_tex.py            전부
    python3 tools/dungeon_tex.py flame      불꽃 플립북만(glb 밖. 런타임 로드)
    python3 tools/dungeon_tex.py light      빛 데칼만(곱수 계약 밖. s40 은 다시 돌릴 것)
    python3 tools/dungeon_tex.py floor      바닥만 미리보기(메타는 안 건드린다)

오너 지시(2026-08-13): **"맵 갈아엎고 다시. 롤·나혼렙 풍의 깔끔+미감. 지금 점점
저퀄. 오버워치·발로란트 질감 조사해봐. 돌 바닥 느낌 있잖아. 지금은 타일 덩어리
직육면체들 같아."**  14차(브롤스타즈)는 폐기다.

정본 둘
  처방전  docs/references/aaa-environment-craft.md   5절 A~F · 6절 체크리스트
  컨셉    incoming/codex_dungeon3/{lol_hall,lol_corridor,lol_tiles}.png

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
★이 판에서 뒤집힌 것 — 컨셉 실측(scripts/lol_metrics.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    lol_tiles  흙(따뜻) 41%  #5f4c33 H34 S0.46 Y 0.0795
               판석(찬) 59%  #2a2924 H48 S0.13 Y 0.0223      ← ★판석이 **덜 밝고 덜 화려하다**
               띠별 채도  0.19(암) -> 0.39(명)               ← 어두운 데는 거의 무채색
    lol_hall   최암 15% #080b0f (H216 S0.42)  최명 3% #90713c (H38 S0.58)
               띠별 R/B 0.56 / 0.98 / 1.92 / 3.69 / 5.31     ← ★어두우면 차고 밝으면 뜨겁다

  14차는 정확히 반대였다: **크림색 판석 + 보라 줄눈**. 즉 채도 예산을 걷는 바닥에
  다 쓰고 어두운 자리마저 물들여 놨다. 이번 판의 규칙은 처방전 2-3 절 그대로다.

      "빛은 명도와 색상으로 그린다. 채도로는 안 그린다."

  그래서 알베도는 **흙만 따뜻하고 판석은 찬 회녹색**이고, 뜨거운 호박색은
  전부 **횃불(정점색·이미시브)** 이 만든다. 알베도로 주황을 칠하지 않는다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇을 어떻게 굽는가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    dg_floor / dg_floor_b   ★★**절차 판석 포장**. 흙 바닥이 기본이고 판석은
                            덮임률 0.70 / 0.42 로 흩뿌린다(처방전 B-0).
                            ★두 장은 **같은 판석 배치**에서 나온다 — 성긴 쪽은
                            촘촘한 쪽의 **부분집합**이라 두 메시가 만나는 자리에서
                            판석이 어긋나지 않는다(밀도만 바뀐다)
    dg_wall                 절차 석벽. running bond · 단마다 장수·높이가 다르다 ·
                            하이라이트는 60% 에만 · 몸통은 조용하게
    dg_block                같은 생성기, 다듬은 돌(기둥·아치·제단·트림). 더 작고 고르다
    dg_crack                ★신설. 판석 경계를 무시하고 지나가는 **분기 균열** 데칼
    dg_wear                 바닥 얼룩 넉 장(마모 · 자갈 · 이끼 · 흙)
    dg_medallion            제단 팔각 문양(청록 -> 이 판은 차분한 청록·황동)
    dg_pool / dg_wglow      횃불 빛(가산)
    dg_flame / dg_flame_fb  불꽃
    dg_pool_cold / dg_shaft 출구의 찬 청록 빛

★평균은 여기서 재서 `web/tex/dungeon_tex.json` 에 적어 둔다. 블렌더 파이썬에는
  PIL 이 없어서 s40 이 png 평균을 스스로 못 잰다(LOG.md 의 옛 함정).
★dungeon_tex.py 를 돌렸으면 **s40 을 반드시 다시 돌려라**(평균·게인이 갈린다).
"""
import os
import sys
import json
import math
import importlib.util

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "web", "tex")
META = os.path.join(OUT_DIR, "dungeon_tex.json")

# tileize.py 의 이음매 도구를 그대로 빌린다(같은 자로 재야 숫자가 비교된다)
_spec = importlib.util.spec_from_file_location(
    "tileize", os.path.join(ROOT, "tools", "tileize.py"))
_tz = importlib.util.module_from_spec(_spec)
sys.modules["tileize"] = _tz
_spec.loader.exec_module(_tz)

RES = 1024

# ═════════════════════════════════════════════════════════════
# 치수 — 처방전 B 의 표를 그대로 상수로 박는다
# ═════════════════════════════════════════════════════════════
FLOOR_M = 5.0                 # 바닥 타일 한 변(m). s40 의 FLOOR_UV_SCALE 과 한 짝
WALL_M = 4.6                  # 벽 타일 한 변(m). s40 의 WALL_UV_SCALE 과 한 짝
PPM = RES / FLOOR_M           # 204.8 px/m
MOD = 0.25                    # ★기준 모듈. 모든 판석 크기가 이것의 정수배다
MODPX = MOD * PPM             # 51.2 px
NMOD = int(round(FLOOR_M / MOD))          # 20 x 20 모듈

# 판석 배합 (Vetter Stone 3-Height Random Ashlar 15 / 50 / 35 을 우리 모듈로)
#   0.25m 15% · 0.50m 50% · 0.75m 35%  ->  5m 타일 한 장에 약 75장
# ★★2차 조정. 처방전 B-1 의 표(0.25/0.50/0.75)를 **한 모듈 위로** 올렸다.
#   같은 자로 컨셉을 재 보면(lol_hall 은 우리와 같은 64 px/m 다) 판석이 50~90px =
#   **0.8~1.4m** 다. 처방전 표대로 구운 1차는 화면에서 판석이 아니라 **자갈밭**으로
#   읽혔다. 배합비 15/50/35 와 "가운데 크기가 절반"은 그대로 지킨다.
#   장수는 5m 타일에 약 35장(덮임 0.70 기준) — 폴리카운트 하한 16 위다.
STONE_MIX = [(4, 4, 8), (4, 3, 5), (3, 4, 5),         # 1.00 계열 (35%)
             (3, 3, 17), (3, 2, 5), (2, 3, 5),        # 0.75 계열 (50%)
             (2, 2, 11)]                              # 0.50 계열 (15%)
MAX_JOINT_RUN = 12            # 줄눈이 직선으로 이어질 수 있는 최대 모듈 수(3.0m)
JOINT_PX = 3.0                # 줄눈 폭(px). 0.5m 판 기준 1.5%  (실물 규격 10~12mm)
COVER_DENSE = 0.72            # 방·제단 둘레 덮임률
COVER_SPARSE = 0.42           # 통로·방 한복판 덮임률

# ── 알베도 팔레트 (sRGB 0~255) ──
# ★★"칠할 색"이 아니라 **타일의 색기**다. 최종 색은 s40 의 PAL x 이 타일이고,
#   hue_keep 0.88 이라 화면 색상은 사실상 여기서 정해진다.
# ★채도는 컨셉 실측(흙 S0.46 · 판석 S0.13)보다 낮게 잡는다 — 컨셉 그림의 채도는
#   이미 **횃불빛이 실린 값**이고 우리는 그 빛을 정점색으로 따로 얹기 때문이다.
# ★★1차 굽기에서 **주황 흙 + 파란 판석**이 나왔다(보색 대비). 컨셉을 다시 재 보면
#   판석은 파랑이 아니라 **따뜻한 무채**(#2a2924 = H48 S0.13)고 흙과 색상이 15도밖에
#   안 벌어져 있다. 갈라놓는 것은 **채도**(0.46 vs 0.13)지 색상이 아니다.
#   14차의 "보라 줄눈 vs 크림 판석"과 같은 실수를 색만 바꿔 되풀이할 뻔했다.
ALB_DIRT = (0x96, 0x83, 0x69)        # 흙 (H32 S0.30 V0.59)  따뜻하다
ALB_DIRT2 = (0x86, 0x75, 0x5e)       # 흙 어두운 쪽
ALB_STONE = (0x83, 0x7f, 0x77)       # 판석 (H41 S0.08 V0.545) ★따뜻한 무채
ALB_STONE_C = (0x7b, 0x7e, 0x7a)     # 판석 찬 변주(청록이 아니라 **회녹**)
ALB_STONE_W = (0x8c, 0x84, 0x76)     # 판석 따뜻 변주
ALB_JOINT = (0x63, 0x59, 0x49)       # 줄눈(흙의 어두운 값. ★보색이 아니다)
ALB_PEBBLE = (0x7d, 0x77, 0x6c)      # 흙에 박힌 자갈
ALB_MOSS = (0x5c, 0x6b, 0x3e)        # 이끼 (줄눈·구석에만)
ALB_WALL = (0x8b, 0x86, 0x7d)        # 벽 몸통 막돌 (H45 S0.09) ★따뜻한 무채
ALB_WALL_C = (0x7e, 0x82, 0x86)      # 벽 찬 변주(회청. 아주 옅게)
ALB_WALL_W = (0x92, 0x8b, 0x7e)      # 벽 따뜻 변주
ALB_WGROUT = (0x72, 0x6e, 0x67)      # 벽 줄눈 ★같은 색의 어두운 값(휘도 0.62배)
ALB_CUT = (0x9d, 0x9b, 0x95)         # 다듬은 돌(기둥·아치·트림)
ALB_GOLD = (0xc8, 0xa2, 0x58)        # 황동(횃불 받침·금테)
ALB_TEAL_HI = (0x5f, 0xb0, 0xb4)     # 메달리온 청록


def srgb_to_lin(a):
    a = np.asarray(a, np.float64)
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(a):
    a = np.clip(np.asarray(a, np.float64), 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def c8(t):
    return np.array(t, np.float64) / 255.0


def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def normalize_mean(rgb, target):
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
    """알파가 없는 타일은 **jpg 로도** 굽는다(s40 이 jpg 를 읽는다)."""
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


# ═════════════════════════════════════════════════════════════
# 자기검증 — 처방전 A표를 **텍스처 단계에서** 미리 잰다
# ═════════════════════════════════════════════════════════════
def _band_sigma(rgb, ppm):
    """가우시안 3대역 분해(매크로 >1.2m · 판석대 0.25~1.2m · 미세 <0.25m).

    ★화면이 아니라 **알베도**에서 재는 값이라 A표의 목표(화면 σ)와 직접 비교하면
      안 된다. 여기서는 판석대/미세의 **비**와 상대 진폭만 본다 — 화면 실측은
      renders/history/v99_wave15/dungeon_lol/scripts/lol_metrics.py 가 한다."""
    lin = srgb_to_lin(rgb)
    L = lin[:, :, 0] * 0.2126 + lin[:, :, 1] * 0.7152 + lin[:, :, 2] * 0.0722
    lo = _tz.wrap_blur(L[:, :, None].astype(np.float32), int(1.2 * ppm / 2))[:, :, 0]
    mid = _tz.wrap_blur(L[:, :, None].astype(np.float32), int(0.25 * ppm / 2))[:, :, 0]
    m = float(L.mean())
    return (float(lo.std()) / m, float((mid - lo).std()) / m, float((L - mid).std()) / m)


def _tex_stat(rgb, tag="", ppm=PPM):
    R, G, B = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    S = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    ma, me, fi = _band_sigma(rgb, ppm)
    return {"tag": tag,
            "S_med": round(float(np.median(S)), 4),
            "lum_mean": round(float(L.mean()), 4),
            "rel_macro": round(ma, 4), "rel_meso": round(me, 4), "rel_fine": round(fi, 4),
            "macro_over_meso": round(ma / max(1e-6, me), 3)}


def seam_audit(rgb, tag):
    """처방전 B-14. offset 50% 로 밀어 **가장자리를 한가운데로** 가져와 재는 감사.

    이음매가 있으면 밀었을 때 그 선을 따라 국소 대비가 튄다. 가운데 열/행의
    기울기 크기를 나머지 화면의 중앙값과 견준다(1.0 이면 티가 안 난다)."""
    n = rgb.shape[0]
    r = np.roll(np.roll(rgb, n // 2, axis=0), n // 2, axis=1)
    g = np.abs(np.diff(r.mean(axis=2), axis=1))
    col = float(g[:, n // 2 - 1].mean())
    med = float(np.percentile(g, 85))
    gh = np.abs(np.diff(r.mean(axis=2), axis=0))
    row = float(gh[n // 2 - 1, :].mean())
    medh = float(np.percentile(gh, 85))
    return {"tag": tag, "seam_v": round(col / max(1e-6, med), 2),
            "seam_h": round(row / max(1e-6, medh), 2)}


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


def _fbm(res, cells, seed, oct_n=3, gain=0.5):
    out = np.zeros((res, res), np.float32)
    amp, tot = 1.0, 0.0
    for i in range(oct_n):
        out += _vnoise(res, cells * (2 ** i), seed + i * 17) * amp
        tot += amp
        amp *= gain
    return out / tot


def _hsv_shift(col, dh_deg=0.0, ds=0.0, dv=1.0):
    """색상 회전 · 채도 가감 · 명도 배수. col 은 0~1 RGB."""
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*np.clip(col, 0, 1))
    h = (h + dh_deg / 360.0) % 1.0
    s = float(np.clip(s + ds, 0, 1))
    v = float(np.clip(v * dv, 0, 1))
    return np.array(colorsys.hsv_to_rgb(h, s, v), np.float64)


# ═════════════════════════════════════════════════════════════
# 판석 배치 — 처방전 B-1~B-4
# ═════════════════════════════════════════════════════════════
def plan_stones(seed=1501):
    """모듈 격자에 판석을 놓는다. **큰 돌 먼저, 남는 틈을 작은 돌로.**

    지키는 규칙 (전부 처방전 B, 출처 등급 A)
      · 모든 크기가 기준 모듈 0.25m 의 정수배
      · 가로세로비 2.6:1 이하 (3x1 = 3.0 은 표에서 뺐다)
      · **네 모서리가 한 점에서 만나지 않는다**
      · **줄눈이 3.0m(12모듈) 넘게 직선으로 이어지지 않는다**
    반환: [(mx, my, mw, mh)] 모듈 좌표(감아 돈다)
    """
    rs = np.random.RandomState(seed)
    occ = np.zeros((NMOD, NMOD), np.int32)          # 칸 점유
    corner = np.zeros((NMOD, NMOD), np.int32)       # 격자점에 모인 모서리 수
    vseg = np.zeros((NMOD, NMOD), bool)             # 세로 줄눈 조각 (x 선, y 칸)
    hseg = np.zeros((NMOD, NMOD), bool)             # 가로 줄눈 조각
    stones = []

    def free(mx, my, mw, mh):
        for j in range(mh):
            for i in range(mw):
                if occ[(my + j) % NMOD, (mx + i) % NMOD]:
                    return False
        return True

    def corner_ok(mx, my, mw, mh):
        # ★네 모서리 금지: 이미 셋이 모인 격자점에 또 얹으면 넷이 된다
        for (cx, cy) in ((mx, my), (mx + mw, my), (mx, my + mh), (mx + mw, my + mh)):
            if corner[cy % NMOD, cx % NMOD] >= 3:
                return False
        return True

    def run_ok(seg, line, a, b):
        """seg[line] 에 [a,b) 를 켰을 때 최장 연속 구간이 상한 이하인가(감아 돈다)."""
        row = seg[line].copy()
        for k in range(a, b):
            row[k % NMOD] = True
        if row.all():
            return False
        best = run = 0
        for k in range(NMOD * 2):
            if row[k % NMOD]:
                run += 1
                best = max(best, run)
            else:
                run = 0
        return best <= MAX_JOINT_RUN

    def joint_ok(mx, my, mw, mh):
        for cx in (mx, mx + mw):
            if not run_ok(vseg, cx % NMOD, my, my + mh):
                return False
        for cy in (my, my + mh):
            if not run_ok(hseg, cy % NMOD, mx, mx + mw):
                return False
        return True

    def place(mx, my, mw, mh):
        for j in range(mh):
            for i in range(mw):
                occ[(my + j) % NMOD, (mx + i) % NMOD] = 1
        for (cx, cy) in ((mx, my), (mx + mw, my), (mx, my + mh), (mx + mw, my + mh)):
            corner[cy % NMOD, cx % NMOD] += 1
        for cx in (mx, mx + mw):
            for j in range(mh):
                vseg[cx % NMOD, (my + j) % NMOD] = True
        for cy in (my, my + mh):
            for i in range(mw):
                hseg[cy % NMOD, (mx + i) % NMOD] = True
        stones.append((mx % NMOD, my % NMOD, mw, mh))

    # ★큰 것부터. 같은 분포에서 뽑으면 큰 돌이 영영 안 들어간다(처방전 B-1)
    for (mw, mh, want) in STONE_MIX:
        got, tries = 0, 0
        while got < want and tries < want * 400:
            tries += 1
            mx, my = rs.randint(0, NMOD), rs.randint(0, NMOD)
            if not free(mx, my, mw, mh):
                continue
            if not corner_ok(mx, my, mw, mh) or not joint_ok(mx, my, mw, mh):
                continue
            place(mx, my, mw, mh)
            got += 1
    return stones, occ


def stone_polys(stones, seed=1502):
    """판석 사각형 -> **불규칙 다각형**(4~7각) + 손상 등급.

    ★둥근 아메바를 만들지 않는다. 모서리를 **안쪽으로** 당기고 변 가운데를
      **바깥으로** 살짝 밀어서 볼록을 유지한다(볼록이면 반평면 max 로 정확한 SDF 가 나온다).
    ★손상은 슬라이더가 아니라 등급이다(처방전 B-9):
        62% 멀쩡  ·  30% 모서리 하나만 깨짐  ·  8% 크게 깨짐(둘로 갈라짐)
    """
    rs = np.random.RandomState(seed)
    out = []
    for (mx, my, mw, mh) in stones:
        cx = (mx + mw * 0.5) * MODPX
        cy = (my + mh * 0.5) * MODPX
        hw = mw * MODPX * 0.5 - JOINT_PX * 0.5
        hh = mh * MODPX * 0.5 - JOINT_PX * 0.5
        pts = []
        base = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        for i, (px, py) in enumerate(base):
            # 모서리를 안쪽으로 (돌은 깎여 있다. 직각이 그대로 남으면 벽돌이다)
            k = 0.06 + rs.rand() * 0.16
            pts.append((px * (1 - k * 0.9), py * (1 - k * 0.9)))
            # 변 가운데 점 — 절반만 넣는다(전부 넣으면 여덟 모서리 = 다시 둥글다)
            if rs.rand() < 0.55:
                nx, ny = base[(i + 1) % 4]
                mxp, myp = (px + nx) * 0.5, (py + ny) * 0.5
                g = 1.0 + rs.rand() * 0.05
                pts.append((mxp * g, myp * g))
        grade = 0
        r = rs.rand()
        if r < 0.30:
            grade = 1        # 모서리 하나만 깨짐
        elif r < 0.35:
            grade = 2        # 크게 깨짐
        out.append({"c": (cx, cy), "pts": pts, "hw": hw, "hh": hh,
                    "grade": grade, "chip": int(rs.randint(0, 4)),
                    "chipk": 0.16 + rs.rand() * 0.20,
                    "vjit": (rs.rand() - 0.5) * 2.0,       # 판별 밑값 ±
                    "hjit": (rs.rand() - 0.5) * 2.0,       # 판별 색상 ±
                    "edge": rs.rand(),                     # 에지 하이라이트 추첨
                    "ew": 1.7 + rs.rand() * 2.2,           # 그 굵기(px)
                    "tilt": (rs.rand() - 0.5) * 2.0,       # 기울어 앉음
                    "split": rs.rand() * math.pi,
                    "wsel": rs.rand()})
    return out


def _poly_sdf(px, py, pts):
    """볼록 다각형 부호거리(반평면 max). 안이 음수."""
    n = len(pts)
    d = None
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        ln = math.hypot(ex, ey)
        if ln < 1e-6:
            continue
        # 바깥 법선 (CCW 기준 오른쪽)
        nx, ny = ey / ln, -ex / ln
        h = (px - ax) * nx + (py - ay) * ny
        d = h if d is None else np.maximum(d, h)
    return d


def bake_ground(coverage, seed=1501, keep_field=None, tag=""):
    """★★이 판의 심장 — 흙 바닥에 판석을 **덜** 깐다 (처방전 B-0).

    "연속 테셀레이션이 없으면 패턴으로 읽힐 것 자체가 없다."
    방 바닥을 판석으로 빈틈없이 덮는 것을 그만두고, 덮임률 42~72% 로 흩는다.

    층 순서 (전부 그레이스케일 값 -> 색 순. 처방전 2-3 절 라이엇 강의 목차)
      ① 흙 바닥      따뜻한 저채도. 큰 얼룩은 **정점색**이 내므로 여기선 작게
      ② 자갈         흙에 박힌 작은 돌. ★최소 형상 23px 규칙을 지킨다(0.11m)
      ③ 판석         값·색상만 흩고 채도는 평평하게. 위 밝고 아래 어둡(1.12~1.20배)
      ④ 에지         30~40% 에만. 코너에서 진하게. **흰색 금지**
      ⑤ 함몰 그림자  판 둘레 바깥을 어둡게 = 판이 바닥에 **박혀** 보인다
      ⑥ 이끼         줄눈과 판 그늘에만(그물이 아니다)
      ⑦ 균열         판석 경계를 무시하고 지나간다
    """
    res = RES
    rs = np.random.RandomState(seed + 700)
    stones, _occ = plan_stones(seed)
    polys = stone_polys(stones, seed + 1)

    # ── ① 흙 ──────────────────────────────────────────────
    # ★큰 얼룩(매크로)은 **정점색**이 낸다(s40 의 MACRO_A). 텍스처가 큰 얼룩을
    #   가지면 5m 마다 그 얼룩이 되풀이돼서 바로 "벽지"가 된다 — 여기선 작게.
    dirt = c8(ALB_DIRT)
    dirt2 = c8(ALB_DIRT2)
    n_lo = _vnoise(res, 6, seed + 11)
    n_mid = _fbm(res, 11, seed + 23, 2)
    t = np.clip(n_lo * 0.45 + n_mid * 0.55, 0, 1)[:, :, None]
    img = dirt2[None, None, :] * (1 - t) + dirt[None, None, :] * t
    img = img * (0.96 + 0.08 * _vnoise(res, 15, seed + 31))[:, :, None]

    # ── ③~⑤ 판석 ─────────────────────────────────────────
    # 덮임률: 저주파 마스크로 **뭉치고 비운다**(고르게 빼면 그냥 성긴 격자다)
    if keep_field is None:
        keep_field = _vnoise(res, 3, seed + 61)
    stone_mask = np.zeros((res, res), np.float32)
    stone_h = np.zeros((res, res), np.float32)       # 판 윗면 높이(함몰 계산용)
    kept = 0
    ys_all = np.arange(res)
    for p in polys:
        cx, cy = p["c"]
        # 이 자리의 덮임 추첨. keep_field 가 높은 자리가 먼저 살아남는다
        fx, fy = int(cx) % res, int(cy) % res
        thr = 1.0 - coverage
        score = 0.62 * keep_field[fy, fx] + 0.38 * ((p["vjit"] + 1) * 0.5)
        if score < thr:
            continue
        kept += 1
        hw, hh = p["hw"], p["hh"]
        pad = 7.0
        x0, x1 = int(math.floor(cx - hw - pad)), int(math.ceil(cx + hw + pad))
        y0, y1 = int(math.floor(cy - hh - pad)), int(math.ceil(cy + hh + pad))
        xs = np.arange(x0, x1)
        ys = np.arange(y0, y1)
        lx = (xs - cx)[None, :]
        ly = (ys - cy)[:, None]
        pts = list(p["pts"])
        # 손상 등급 — 모서리 하나를 잘라 낸다(대부분은 이것뿐이다)
        if p["grade"] >= 1:
            ci = p["chip"] % len(pts)
            ax, ay = pts[ci]
            k = p["chipk"]
            pts[ci] = (ax * (1 - k), ay * (1 - k))
        d = _poly_sdf(lx, ly, pts)
        if p["grade"] == 2:
            # 크게 깨짐: 판을 가로지르는 틈 하나
            a = p["split"]
            sd = np.abs(lx * math.cos(a) + ly * math.sin(a)) - 1.15
            d = np.maximum(d, -sd)
        inside = _smooth((-d) / 1.35)
        if inside.max() <= 0.02:
            continue
        # 판별 색: 밑값 ±6% · 색상 ±4° · **채도는 안 흔든다**(처방전 2-3)
        base = c8(ALB_STONE)
        if p["wsel"] > 0.72:
            base = c8(ALB_STONE_W)
        elif p["wsel"] < 0.28:
            base = c8(ALB_STONE_C)
        col = _hsv_shift(base, dh_deg=p["hjit"] * 5.0, dv=1.0 + p["vjit"] * 0.105)
        # 판 안의 작은 기울기: 위가 밝고 아래가 어둡다(베개 음영 금지)
        v = np.clip((ly + hh) / (2 * hh), 0, 1)
        grad = 1.09 - 0.17 * v + 0.02 * p["tilt"]
        # 잔결(아주 낮게. 롤 실측 고주파 RMS < 2.2/255)
        gsub = 0.985 + 0.030 * _vnoise(res, 46, seed + 71)[np.ix_(ys % res, xs % res)]
        sh = grad * gsub
        # ④ 에지 하이라이트 — 30~40% 에만. 위쪽 변에서, 코너 쪽이 진하다
        if p["edge"] < 0.36:
            top = _smooth((0.42 - v) / 0.30)
            band = _smooth((p["ew"] + d) / p["ew"])
            cor = 0.55 + 0.45 * _smooth((np.abs(lx) / max(hw, 1e-3) - 0.45) / 0.4)
            sh = sh + band * top * cor * (0.19 + 0.12 * p["wsel"])
        # 아래쪽 변은 반대로 눌러 준다(판이 앞으로 나온다)
        bot = _smooth((v - 0.66) / 0.30)
        sh = sh * (1.0 - 0.13 * bot * _smooth((3.0 + d) / 3.0))
        px = np.clip(col[None, None, :] * sh[:, :, None], 0, 1)
        a3 = inside[:, :, None]
        sub = img[np.ix_(ys % res, xs % res)]
        img[np.ix_(ys % res, xs % res)] = sub * (1 - a3) + px * a3
        sm = stone_mask[np.ix_(ys % res, xs % res)]
        stone_mask[np.ix_(ys % res, xs % res)] = np.maximum(sm, inside)
        hsub = stone_h[np.ix_(ys % res, xs % res)]
        stone_h[np.ix_(ys % res, xs % res)] = np.maximum(
            hsub, inside * (0.72 + 0.28 * (p["vjit"] + 1) * 0.5))

    # ── ⑤ 함몰 그림자 ────────────────────────────────────
    # ★"위에서 내리쬐는 빛에서 돌을 서로 떼어 놓는 것이 바로 이 함몰"(처방전 B-6).
    #   판 **바깥** 3~4px 을 어둡게 한다. 판 안은 안 건드린다(테두리 어둠 = 베개다).
    blur = _tz.wrap_blur(stone_mask[:, :, None].astype(np.float32), 4, passes=2)[:, :, 0]
    ao = np.clip(blur - stone_mask, 0, 1)
    img = img * (1.0 - 0.50 * ao)[:, :, None]
    wide = _tz.wrap_blur(stone_mask[:, :, None].astype(np.float32), 13, passes=2)[:, :, 0]

    # ── ②' 자갈 — ★포장 **가장자리**에 몰린다 ────────────
    # 처방전 3-1b: "가장자리를 작은 돌 띠로 마감하고 그 바깥에 낱개 조각을
    # 밀도를 줄이며 흩는다. 격자를 벗어나도 되는 유일한 돌이 이 가장자리 조각이다."
    # ★잡음 문턱으로 만들면 **벌레 모양 얼룩**이 된다(1차 굽기). 작은 다각형을
    #   실제로 놓는다. 반지름 12~18px = 지름 0.12~0.18m 로 최소 형상 23px 규칙 위.
    peb = c8(ALB_PEBBLE)
    edge_band = np.clip(wide - stone_mask, 0, 1)              # 판석 둘레 0.3m 띠
    pebm = np.zeros((res, res), np.float32)
    ng = 17
    for gj in range(ng):
        for gi in range(ng):
            px0 = (gi + rs.rand()) * res / ng
            py0 = (gj + rs.rand()) * res / ng
            ix, iy = int(px0) % res, int(py0) % res
            if stone_mask[iy, ix] > 0.25:
                continue
            if rs.rand() > 0.20 + 0.72 * edge_band[iy, ix]:
                continue
            rad = 11.0 + rs.rand() * 6.0
            k = 5 + int(rs.rand() * 2)
            ph = rs.rand() * 6.28
            pts = [(math.cos(ph + i * 2 * math.pi / k) * rad * (0.72 + 0.5 * rs.rand()),
                    math.sin(ph + i * 2 * math.pi / k) * rad * (0.72 + 0.5 * rs.rand()))
                   for i in range(k)]
            x0, x1 = int(px0 - rad - 4), int(px0 + rad + 5)
            y0p, y1p = int(py0 - rad - 4), int(py0 + rad + 5)
            xs = np.arange(x0, x1)
            ys = np.arange(y0p, y1p)
            d = _poly_sdf((xs - px0)[None, :], (ys - py0)[:, None], pts)
            m = _smooth((-d) / 1.3)
            sub = pebm[np.ix_(ys % res, xs % res)]
            pebm[np.ix_(ys % res, xs % res)] = np.maximum(sub, m)
            v = np.clip((ys - py0 + rad)[:, None] / (2 * rad), 0, 1)
            sh = (1.06 - 0.22 * v) * (0.88 + 0.30 * rs.rand())
            pc = np.clip(peb[None, None, :] * sh[:, :, None], 0, 1)
            isub = img[np.ix_(ys % res, xs % res)]
            img[np.ix_(ys % res, xs % res)] = isub * (1 - m[:, :, None]) + pc * m[:, :, None]
    pao = _tz.wrap_blur(pebm[:, :, None].astype(np.float32), 3)[:, :, 0]
    img = img * (1.0 - 0.20 * np.clip(pao - pebm, 0, 1))[:, :, None]

    # ── ⑥ 이끼 — 줄눈과 판 그늘에만 (그물 금지) ───────────
    moss = c8(ALB_MOSS)
    mfield = _smooth((_vnoise(res, 5, seed + 81) - 0.62) / 0.22)
    mfine = _smooth((_vnoise(res, 61, seed + 83) - 0.52) / 0.20)
    mm = np.clip(ao * 1.4, 0, 1) * mfield * mfine * 0.55
    img = img * (1 - mm[:, :, None]) + moss[None, None, :] * mm[:, :, None]

    # ── ⑦ 균열 — 판석 경계를 무시하고 지나간다 ────────────
    img = draw_cracks(img, rs, n=2, seed=seed + 91, mask=stone_mask)

    img = np.clip(img, 0, 1).astype(np.float32)
    return img, kept, len(polys)


def draw_cracks(img, rs, n=2, seed=0, width=2.4, dark=0.42, mask=None):
    """분기 균열. ★틈은 어둡게, **그 틈의 가장자리는 밝게** (처방전 2-3 Charré).

    ★값잡음 등고선으로 그리면 "지렁이"가 된다(14차 함정). 여기서는 **꺾은선**을
      직접 걸어 그린다 — 돌이 갈라지는 길은 부드러운 곡선이 아니다.
    """
    res = img.shape[0]
    yy, xx = np.mgrid[0:res, 0:res].astype(np.float32)
    field = np.full((res, res), 1e9, np.float32)

    def seg(x0, y0, x1, y1):
        ex, ey = x1 - x0, y1 - y0
        ln = max(1e-3, math.hypot(ex, ey))
        # 감아 도는 거리
        dx = ((xx - x0 + res * 1.5) % res) - res * 0.5
        dy = ((yy - y0 + res * 1.5) % res) - res * 0.5
        t = np.clip((dx * ex + dy * ey) / (ln * ln), 0, 1)
        px = dx - t * ex
        py = dy - t * ey
        return np.sqrt(px * px + py * py)

    # ★1차 굽기에서 균열이 **철사**로 나왔다(한 칸을 가로지르는 거의 직선 두 줄).
    #   돌이 갈라지는 길은 짧게 꺾이며 나아간다 — 마디를 짧게, 꺾임을 크게.
    for k in range(n):
        x, y = rs.rand() * res, rs.rand() * res
        ang = rs.rand() * 2 * math.pi
        branches = [(x, y, ang, 1.0)]
        while branches:
            (x, y, ang, w) = branches.pop()
            steps = int(7 + rs.rand() * 6)
            for s in range(steps):
                ln = 18 + rs.rand() * 42
                nx, ny = x + math.cos(ang) * ln, y + math.sin(ang) * ln
                field = np.minimum(field, seg(x, y, nx, ny) / max(0.35, w))
                x, y = nx, ny
                ang += (rs.rand() - 0.5) * 1.5
                if w > 0.55 and rs.rand() < 0.20:
                    branches.append((x, y, ang + (rs.rand() - 0.5) * 2.4, w * 0.60))
                w *= 0.90
    core = _smooth((width - field) / width)
    edge = _smooth((width * 2.4 - field) / (width * 1.6)) - core
    if mask is not None:
        core = core * mask
        edge = edge * mask
    out = img * (1.0 - dark * core)[:, :, None]
    out = np.clip(out * (1.0 + 0.13 * np.clip(edge, 0, 1))[:, :, None], 0, 1)
    return out


# ═════════════════════════════════════════════════════════════
# 벽 — 타일 석벽 (처방전 C)
# ═════════════════════════════════════════════════════════════
# ★트림 시트를 **텍스처로** 만들지 않았다. 우리 벽 UV 는 삼중평면이라 v 가
#   "세계 높이 / 4.6m" 이고, 벽 높이가 1.45 · 3.6 · 4.2 · 7.5m 로 넷이라
#   가로 띠를 어디에 그려도 벽마다 다른 자리에 걸린다. 그래서 **띠는 지오메트리로**
#   두르고(s40 의 주춧돌·띠돌·갓돌) 이 텍스처는 처방전대로 **몸통 타일**만 맡는다.
#   그게 처방전 C 의 분업 원칙 그대로다 — "트림은 벽을 대체하지 않는다."
WALL_JOINT = 3.0          # 줄눈 폭(px). 4.6m/1024 = 222px/m -> 13.5mm
WALL_HI_FRAC = 0.60       # ★하이라이트를 받는 블록 비율. 전부 주면 도장 자국이 된다
WALL_HI_A = 0.115         # 그 세기(가산). ±20% 로 흩는다
WALL_LO_A = 0.115         # 밑동 그늘


def bake_wall(res=RES, seed=1601, base=ALB_WALL, cool=ALB_WALL_C, warm=ALB_WALL_W,
              grout=ALB_WGROUT, courses=None, quiet=1.0, jitter=0.062, moss=True,
              m_per_tile=WALL_M):
    """막돌 쌓기. **단마다 장수와 높이가 다르고 반 칸씩 밀린다**(running bond).

    처방전 C 가 금지한 것을 하나씩 없앤 판이다.
      · stack bond (5단 x 3장 균일)      -> 단마다 장수 다름 + 어긋물림
      · 전 블록 같은 갓 하이라이트       -> 60% 에만 + 세기 ±20%
      · 가로세로비 3:1 넘는 긴 돌        -> 1.1 ~ 2.5 로 가둔다
      · 시끄러운 몸통                    -> 잔결 진폭 1/3
    """
    rs = np.random.RandomState(seed)
    img = np.zeros((res, res, 3), np.float64)
    gcol = c8(grout)
    gn = _vnoise(res, 19, seed + 5)
    img[:] = gcol[None, None, :] * (0.72 + 0.36 * gn[:, :, None])

    ppm = res / m_per_tile
    if courses is None:
        # 단 높이 0.34 ~ 0.50m. 합이 정확히 res 가 되게 마지막에 맞춘다
        # ★★2차 조정. 단 높이 0.34~0.50m -> **0.50~0.72m**. 컨셉(lol_corridor)의
        #   벽은 3.6m 높이에 단이 대여섯이고 블록 하나가 사람 어깨보다 넓다.
        #   1차 값은 4.6m 에 열한 단이 들어가 화면에서 **벽돌 격자**로 읽혔다 —
        #   오너가 기각한 그 "타일 덩어리"가 벽에도 있었던 것이다.
        hs = []
        while sum(hs) < res - 0.44 * ppm:
            hs.append((0.50 + rs.rand() * 0.22) * ppm)
        hs = [h * res / sum(hs) for h in hs]
    else:
        hs = [res / courses] * courses

    ys, xs = np.mgrid[0:res, 0:res].astype(np.float64)
    nz1 = _vnoise(res, 9, seed + 11)                  # 블록 안 얼룩
    nz2 = _vnoise(res, 31, seed + 23)                 # 잔결
    y0 = 0.0
    for ci, ch in enumerate(hs):
        # 가로세로비 1.1 ~ 2.5 가 되도록 장수를 고른다
        lo = max(2, int(math.ceil(res / (ch * 2.2))))
        hi = max(lo, int(math.floor(res / (ch * 1.15))))
        n = int(rs.randint(lo, hi + 1))
        w = 1.0 + (rs.rand(n) - 0.5) * 0.28
        w = w / w.sum() * res
        off = rs.rand() * res                          # 단마다 어긋물림
        x = off
        for k in range(n):
            bw = w[k]
            # ★★1차 굽기가 **사탕 블록**으로 나왔다(파랑·크림이 번갈아 나오는 격자).
            #   원인 둘: (가) 색표 셋을 그대로 뽑아 이웃한 두 장의 색상이 벌어졌다
            #   (나) 모서리 둥글기가 블록 높이의 16% 라 알약이 됐다(14차 함정 재발).
            #   벽 하나는 **한 가지 돌**이다. 변주는 명도 ±6% 와 색상 ±3도까지만.
            sel = rs.rand()
            col = np.array(base, np.float64) / 255.0
            if sel > 0.80:
                col = col * 0.60 + c8(warm) * 0.40
            elif sel < 0.24:
                col = col * 0.60 + c8(cool) * 0.40
            col = _hsv_shift(col, dh_deg=(rs.rand() - 0.5) * 3.0,
                             dv=1.0 + (rs.rand() - 0.5) * 2 * jitter)
            cx, cy = x + bw * 0.5, y0 + ch * 0.5
            hx = bw * 0.5 - WALL_JOINT * 0.5
            hy = ch * 0.5 - WALL_JOINT * 0.5
            dx = ((xs - cx + res * 1.5) % res) - res * 0.5
            dy = ys - cy
            # ★둥근 사각형이 아니라 **깎아 놓은 돌**이다. 네 모서리를 조금씩
            #   안쪽으로 당기고(직각 제거) 변 하나를 살짝 밀어 볼록 다각형으로 만든다.
            pts = []
            b4 = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
            for i, (bx, by) in enumerate(b4):
                kx = 1.0 - (0.015 + rs.rand() * 0.055) * min(1.0, hy / max(hx, 1e-3))
                ky = 1.0 - (0.025 + rs.rand() * 0.070)
                pts.append((bx * kx, by * ky))
                if rs.rand() < 0.42:
                    nx2, ny2 = b4[(i + 1) % 4]
                    pts.append(((bx + nx2) * 0.5 * 1.005, (by + ny2) * 0.5 * 1.005))
            d = _poly_sdf(dx, dy, pts)
            body = _smooth((-d) / 1.25)
            if body.max() <= 0.02:
                x = (x + bw) % res
                continue
            v = np.clip((dy + hy) / (2 * hy), 0, 1)     # 0 위 .. 1 아래
            # 몸통은 **조용하게**. 위->아래 아주 완만한 기울기 하나뿐
            sh = 1.04 - 0.10 * v
            # 갓 하이라이트: 60% 에만, 세기 ±20%, 굵기도 흩는다. ★흰색이 아니라
            #   제 색의 밝은 값이다(가산이 아니라 배수라 색상이 안 씻긴다)
            if rs.rand() < WALL_HI_FRAC:
                hw_px = 2.0 + rs.rand() * 3.0
                amp = WALL_HI_A * (0.8 + rs.rand() * 0.4)
                sh = sh + amp * _smooth((hw_px + d) / hw_px) * _smooth((0.30 - v) / 0.26)
            # 밑동 그늘은 전부에 (접지는 물리다)
            sh = sh * (1.0 - WALL_LO_A * _smooth((v - 0.62) / 0.38))
            # 손그림 얼룩(진폭 1/3)
            sh = sh * (0.975 + 0.05 * nz1 * quiet) * (0.99 + 0.02 * nz2 * quiet)
            px = np.clip(col[None, None, :] * sh[:, :, None], 0, 1)
            a = body[:, :, None]
            img = img * (1 - a) + px * a
            x = (x + bw) % res
        y0 += ch

    # 줄눈 함몰 그림자 — 블록 둘레 바깥만
    blk = _smooth((img.mean(axis=2) - 0.16) / 0.07)
    aoo = _tz.wrap_blur(blk[:, :, None].astype(np.float32), 5, passes=2)[:, :, 0]
    img = img * (1.0 - 0.30 * np.clip(aoo - blk, 0, 1))[:, :, None]
    # ★벽 밑동 오염(오버워치 관례: "walls usually have some dirt on top and bottom").
    #   v_blender 0 = 세계 높이 0 이라 **이미지 맨 아랫줄이 바닥면**이다.
    hgt = np.linspace(0, 1, res)[:, None]
    img = img * (1.0 - 0.16 * _smooth((0.10 - hgt) / 0.10))[:, :, None]
    if moss:
        mcol = c8(ALB_MOSS)
        m1 = _smooth((_vnoise(res, 7, seed + 41) - 0.80) / 0.12)
        m2 = _smooth((_vnoise(res, 59, seed + 61) - 0.56) / 0.20)
        mm = m1 * m2 * 0.34 * _smooth((0.34 - hgt) / 0.34)   # 밑동에만
        img = img * (1 - mm[:, :, None]) + mcol[None, None, :] * mm[:, :, None]
    return np.clip(img, 0, 1).astype(np.float32)


# ═════════════════════════════════════════════════════════════
# 제단 메달리온
# ═════════════════════════════════════════════════════════════
def bake_medallion(res=256):
    """제단 바닥의 팔각 문양. 청록 + 황동."""
    yy, xx = np.mgrid[0:res, 0:res].astype(np.float32) / (res - 1) * 2 - 1
    r = np.sqrt(xx * xx + yy * yy)
    ang = np.arctan2(yy, xx)
    oct_r = np.cos(np.pi / 8) / np.cos(((ang + np.pi / 8) % (np.pi / 4)) - np.pi / 8)
    stone = c8(ALB_CUT).astype(np.float32)
    gold = c8(ALB_GOLD).astype(np.float32)
    teal = c8(ALB_TEAL_HI).astype(np.float32)
    dark = c8(ALB_WGROUT).astype(np.float32)
    rgb = np.zeros((res, res, 3), np.float32)
    rgb[:] = stone[None, None, :] * 0.90
    R_OUT, R_GOLD, R_TEAL = 0.92, 0.80, 0.72

    def ring(lo, hi, col, soft=0.018):
        m = _smooth((r * oct_r - lo) / soft) * _smooth((hi - r * oct_r) / soft)
        return m[:, :, None] * col[None, None, :], m

    for lo, hi, col in ((R_TEAL, R_GOLD, gold), (0.0, R_TEAL, teal * 0.62)):
        px, m = ring(lo, hi, col)
        rgb = rgb * (1 - m[:, :, None]) + px
    for e in (R_OUT, R_GOLD):
        m = _smooth((0.022 - np.abs(r * oct_r - e)) / 0.014)
        rgb = rgb * (1 - m[:, :, None] * 0.85) + dark[None, None, :] * (m[:, :, None] * 0.85)
    sp = np.abs(np.sin(ang * 4.0))
    m = _smooth((0.10 - sp) / 0.07) * _smooth((R_TEAL - 0.04 - r * oct_r) / 0.03)
    rgb = rgb * (1 - m[:, :, None] * 0.72) + (teal * 0.34)[None, None, :] * (m[:, :, None] * 0.72)
    m = _smooth((0.13 - r) / 0.03)
    rgb = rgb * (1 - m[:, :, None]) + (teal * 1.10)[None, None, :] * m[:, :, None]
    grid = np.minimum(np.abs(((xx * 3.0 + 9) % 1.0) - 0.5), np.abs(((yy * 3.0 + 9) % 1.0) - 0.5))
    gm = _smooth((0.045 - grid) / 0.03) * _smooth((r * oct_r - R_OUT + 0.10) / 0.06)
    rgb = rgb * (1 - gm[:, :, None] * 0.32) + dark[None, None, :] * (gm[:, :, None] * 0.32)
    rgb = np.clip(rgb * (0.94 + 0.12 * _vnoise(res, 11, 771)[:, :, None]), 0, 1)
    a = _smooth((R_OUT + 0.02 - r * oct_r) / 0.035)
    return rgb, a


# ═════════════════════════════════════════════════════════════
# 빛 데칼 (형태는 13차 그대로 · 색만 이번 컨셉으로)
# ═════════════════════════════════════════════════════════════
# 컨셉 실측: 홀 최명 3% #90713c(H38 S0.58) · 복도 #a06b40(H27 S0.60)
POOL_HOT = (1.00, 0.82, 0.46)
POOL_MID = (1.00, 0.58, 0.19)
POOL_TIP = (0.84, 0.34, 0.10)


def bake_pool(res, stops, seed, squash=1.0, wob=0.20, core=0.22, amax=0.62,
              tail=0.62, rough=0.42):
    """바닥에 까는 **빛 웅덩이** 데칼(가산 합성. web/level.js 가 갈아 준다).

    ★프로파일은 점광원의 2차 감쇠다 — 평평한 코어가 없다(있으면 원반 스티커다).
    ★가장자리는 **두 옥타브**로 흐트러뜨린다(한 옥타브면 매끈한 타원이 남는다).
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
    """횃불이 **벽을 타고 오르는** 자국."""
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
    hot = np.array((1.00, 0.88, 0.62), np.float32)
    mid = np.array((1.00, 0.60, 0.22), np.float32)
    tip = np.array((0.84, 0.34, 0.11), np.float32)
    t1 = _smooth(d / 0.34)[:, :, None]
    t2 = _smooth((d - 0.34) / 0.55)[:, :, None]
    rgb = hot[None, None, :] * (1 - t1) + mid[None, None, :] * t1
    rgb = rgb * (1 - t2) + tip[None, None, :] * t2
    return np.clip(rgb, 0, 1), np.clip(a, 0, 1)


def bake_wear(res=256, seed=5501):
    """바닥 데칼 넉 장(2x2 아틀라스). ★처방전 E 의 네 종류다.

        0 WEAR   사람이 다닌 닳음(밝고 매끈)      1 RUBBLE 흩어진 돌조각
        2 MOSS   이끼 얼룩(그물 아님)             3 DIRT   흙 얼룩(판석을 덮는다)
    ★알파 상한 0.55 (13차 교훈: 1.0 이면 데칼이 바닥돌을 덮어 물감이 된다).
    """
    half = res // 2
    yy, xx = np.mgrid[0:half, 0:half].astype(np.float32) / (half - 1) * 2 - 1
    tiles = []
    spec = [(c8((0xb0, 0xa2, 0x86)), 0.34, 0.80, 1.30, 0.40, 0),
            (c8((0x74, 0x74, 0x6e)), 0.50, 0.66, 0.92, 0.55, 1),
            (c8(ALB_MOSS), 0.44, 0.62, 1.00, 0.58, 2),
            (c8(ALB_DIRT2), 0.52, 0.74, 0.86, 0.48, 3)]
    for (col, amax, size, sq, nz, kind) in spec:
        n1 = _vnoise(half, 3, seed + kind * 91)
        n2 = _vnoise(half, 7, seed + kind * 91 + 13)
        n3 = _vnoise(half, 15, seed + kind * 91 + 29)
        r = np.sqrt(xx * xx + (yy * sq) ** 2)
        r = r * (1.0 + nz * (n1 - 0.5) * 2.0 + nz * 0.5 * (n2 - 0.5) * 2.0)
        a = _smooth((size - r) / 0.62)
        a = a * (0.55 + 0.45 * n3)
        a = a * _smooth((1.0 - np.maximum(np.abs(xx), np.abs(yy))) / 0.22)
        rgb = np.zeros((half, half, 3), np.float32)
        for c in range(3):
            rgb[:, :, c] = col[c] * (0.86 + 0.28 * n2)
        if kind == 1:
            # 돌조각: 알갱이를 **형상**으로 박는다(잡음이 아니다)
            g = _smooth((_vnoise(half, 22, seed + 7) - 0.72) / 0.06)
            rgb = rgb * (1 - g[:, :, None] * 0.55) + 0.42 * g[:, :, None]
            a = np.clip(a * (0.45 + 0.85 * g), 0, 1)
        tiles.append((np.clip(rgb, 0, 1), np.clip(a, 0, 1) * amax))
    top = np.concatenate([tiles[0][0], tiles[1][0]], axis=1)
    bot = np.concatenate([tiles[2][0], tiles[3][0]], axis=1)
    at = np.concatenate([tiles[0][1], tiles[1][1]], axis=1)
    ab = np.concatenate([tiles[2][1], tiles[3][1]], axis=1)
    return np.concatenate([top, bot], axis=0), np.concatenate([at, ab], axis=0)


def bake_crack_decal(res=512, seed=9101):
    """★신설 — DECAL_CRACK. 길이 3~6m 짜리 **분기 균열** 한 장(알파).

    처방전 1-3 절: "금이 판석을 무시하고 지나간다. 판석보다 한 단계 큰 스케일의
    두 번째 그림이라 '칸 격자' 읽기를 부순다." 우리에게 지금 한 장도 없던 것이다.
    """
    rs = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:res, 0:res].astype(np.float32)
    field = np.full((res, res), 1e9, np.float32)

    def seg(x0, y0, x1, y1, w):
        ex, ey = x1 - x0, y1 - y0
        ln = max(1e-3, math.hypot(ex, ey))
        dx, dy = xx - x0, yy - y0
        t = np.clip((dx * ex + dy * ey) / (ln * ln), 0, 1)
        px, py = dx - t * ex, dy - t * ey
        return np.sqrt(px * px + py * py) / max(0.3, w)

    x, y = res * 0.06, res * (0.30 + rs.rand() * 0.4)
    ang = (rs.rand() - 0.5) * 0.7
    stack = [(x, y, ang, 1.0)]
    while stack:
        (x, y, ang, w) = stack.pop()
        for s in range(int(7 + rs.rand() * 5)):
            ln = res * (0.06 + rs.rand() * 0.09)
            nx, ny = x + math.cos(ang) * ln, y + math.sin(ang) * ln
            field = np.minimum(field, seg(x, y, nx, ny, w))
            x, y = nx, ny
            ang += (rs.rand() - 0.5) * 0.85
            if w > 0.5 and rs.rand() < 0.30:
                stack.append((x, y, ang + (rs.rand() - 0.5) * 2.4, w * 0.60))
            w *= 0.92
            if not (0 < x < res and 0 < y < res):
                break
    core = _smooth((3.0 - field) / 3.0)
    edge = np.clip(_smooth((7.0 - field) / 5.0) - core, 0, 1)
    rgb = np.zeros((res, res, 3), np.float32)
    dark = c8(ALB_JOINT).astype(np.float32) * 0.55
    lite = c8(ALB_STONE).astype(np.float32) * 1.15
    rgb[:] = dark[None, None, :]
    rgb = rgb * (1 - edge[:, :, None]) + lite[None, None, :] * edge[:, :, None]
    a = np.clip(core * 0.55 + edge * 0.16, 0, 0.55)
    # 카드 가장자리에서 알파를 0 으로 (사각 스티커 방지)
    fx = _smooth(np.minimum(xx, res - 1 - xx) / (res * 0.06))
    fy = _smooth(np.minimum(yy, res - 1 - yy) / (res * 0.06))
    return rgb, a * fx * fy


def bake_shaft(w, h):
    """계단 위에서 내려오는 빛기둥의 옆면(출구 표식. 청록)."""
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    top_fade = np.clip((1.0 - yy) / 0.40, 0, 1) ** 1.20
    body = 0.18 + 0.82 * np.clip(yy / 0.75, 0, 1) ** 0.65
    v = np.clip(top_fade * body, 0, 1)
    e = np.clip(1.0 - np.abs(xx), 0, 1) ** 1.15
    streak = 0.80 + 0.20 * _vnoise(max(w, h), 5, 913)[:h, :w]
    a = np.clip(v * e * streak * 0.62, 0, 1)
    rgb = np.zeros((h, w, 3), np.float32)
    rgb[:, :, 0] = 0.42
    rgb[:, :, 1] = 0.92
    rgb[:, :, 2] = 0.95
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
    t = np.broadcast_to(np.clip(yy, 0, 1), (h, w))[:, :, None]
    rgb = FLAME_MID[None, None, :] * (1 - t) + FLAME_TIP[None, None, :] * t
    rgb = rgb * (1 - core[:, :, None]) + FLAME_HOT[None, None, :] * core[:, :, None]
    return np.clip(np.nan_to_num(rgb), 0, 1), np.nan_to_num(a)


# ═════════════════════════════════════════════════════════════
# 불꽃 플립북
# ═════════════════════════════════════════════════════════════
FLIP_N = 4
FLIP_MARGIN = 0.90
FLAME_HOT = np.array((1.00, 0.95, 0.78), np.float32)
FLAME_MID = np.array((1.00, 0.72, 0.28), np.float32)
FLAME_TIP = np.array((0.94, 0.40, 0.12), np.float32)


def _flame_frame(w, h, p, seed):
    """불꽃 한 칸. p 는 0..2pi 의 위상."""
    yy = np.linspace(1, 0, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    n = _vnoise(max(w, h), 7, seed)[:h, :w]
    ytip = 0.90 + 0.06 * math.cos(p + 1.1)
    yn = np.clip(yy / ytip, 0, 1)
    hw = 0.56 * np.clip(np.sin(np.pi * yn ** 0.60), 0, 1) ** 1.12 + 0.10 * (1.0 - yn)
    hw = hw * (1.0 + 0.20 * np.sin(yn * 4.6 - p))
    hw = np.clip(hw, 0.0, 1.0) * FLIP_MARGIN
    cx = 0.26 * yn ** 1.8 * math.sin(p)
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
        r, a = _flame_frame(w, h, p, 4021 + f * 97)
        rgbs.append(r)
        alphas.append(a)
    return np.concatenate(rgbs, axis=1), np.concatenate(alphas, axis=1)


# ═════════════════════════════════════════════════════════════
# ★목표 sRGB 평균 — 곱수 계약에 자리를 만드는 값이다
# ═════════════════════════════════════════════════════════════
#   k = 목표알베도 / (타일평균 x 정점색평균) <= 1 이 계약이라, 타일이 어두우면
#   곱수가 1 에서 잘려 팔레트가 조용히 밀린다. 이 판은 화면을 네 배 어둡게
#   가져가므로 목표알베도가 작아져 여유가 크지만, 벽은 수직면 조도가 바닥의
#   21% 뿐이라 여전히 빠듯하다 -> 벽·다듬은돌을 바닥보다 밝게 굽는다.
# ★실측으로 고른 값이다. 0.85 로 올리면 밝은 쪽 **5.1%가 클리핑**해서 갓
#   하이라이트가 통째로 죽는다(14차가 밟은 그 함정). 0.78 은 0.08% 뿐이다.
TARGET_FLOOR = 0.560
TARGET_WALL = 0.780
TARGET_BLOCK = 0.830


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    meta = {"src": "절차 생성(15차 · 처방전 aaa-environment-craft.md)",
            "res": RES, "lin": {}, "gain": {}, "seam": {}, "stat": {}}

    # ★두 바닥은 **같은 배치·같은 keep_field** 에서 나온다. 성긴 쪽이 촘촘한 쪽의
    #   부분집합이라 두 메시가 만나는 자리에서 판석이 어긋나지 않는다.
    keep = _vnoise(RES, 3, 1501 + 61)
    for (cov, name) in ((COVER_DENSE, "dg_floor"), (COVER_SPARSE, "dg_floor_b")):
        print("\n[%s]  절차 판석 포장 — 덮임률 목표 %.2f" % (name, cov))
        a, kept, total = bake_ground(cov, keep_field=keep, tag=name)
        a, gain = normalize_mean(a, TARGET_FLOOR)
        meta["lin"][name] = save_rgb(name, a)
        meta["gain"][name] = round(float(gain), 4)
        meta["seam"][name] = seam_audit(a, name)
        meta["stat"][name] = _tex_stat(a, name)
        meta["stat"][name]["stones"] = kept
        meta["stat"][name]["stones_planned"] = total
        print("   [배치] 판석 %d / %d 장 (5m 타일 한 장 기준)" % (kept, total))
        print("   [화풍] %s" % meta["stat"][name])
        print("   [이음매] %s" % meta["seam"][name])

    print("\n[dg_wall]  절차 석벽 — running bond · 하이라이트 60%%")
    w = bake_wall()
    w, wgain = normalize_mean(w, TARGET_WALL)
    meta["lin"]["dg_wall"] = save_rgb("dg_wall", w)
    meta["gain"]["dg_wall"] = round(float(wgain), 4)
    meta["stat"]["dg_wall"] = _tex_stat(w, "dg_wall", RES / WALL_M)
    meta["seam"]["dg_wall"] = seam_audit(w, "dg_wall")
    print("   [화풍] %s" % meta["stat"]["dg_wall"])

    print("\n[dg_block]  절차 — 다듬은 돌(기둥·아치·제단·트림)")
    b = bake_wall(seed=2207, base=ALB_CUT, cool=(0x90, 0x98, 0xa0),
                  warm=(0xa2, 0x9e, 0x94), grout=(0x4a, 0x4c, 0x52),
                  quiet=0.55, jitter=0.038, moss=False, m_per_tile=2.6)
    b, bgain = normalize_mean(b, TARGET_BLOCK)
    meta["lin"]["dg_block"] = save_rgb("dg_block", b)
    meta["gain"]["dg_block"] = round(float(bgain), 4)
    meta["stat"]["dg_block"] = _tex_stat(b, "dg_block", RES / 2.6)
    print("   [화풍] %s" % meta["stat"]["dg_block"])

    print("\n[dg_medallion]  절차 — 팔각 문양")
    med, ma = bake_medallion(256)
    save_rgba("dg_medallion", med, ma)
    meta["lin"]["dg_medallion"] = [float(x) for x in srgb_to_lin(med).reshape(-1, 3).mean(axis=0)]
    meta["gain"]["dg_medallion"] = 1.0

    print("\n[dg_crack]  절차 — 분기 균열 데칼(신설)")
    cr, ca = bake_crack_decal(512)
    save_rgba("dg_crack", cr, ca)
    meta["lin"]["dg_crack"] = [float(x) for x in srgb_to_lin(cr).reshape(-1, 3).mean(axis=0)]

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
    """**빛 데칼만** 굽는다(웜 풀 · 찬 웅덩이 · 빛기둥 · 벽 자국)."""
    os.makedirs(OUT_DIR, exist_ok=True)
    rgb, a = bake_pool(256, (POOL_HOT, POOL_MID, POOL_TIP), 311,
                       squash=1.0, wob=0.22, core=0.28, amax=0.72,
                       tail=0.70, rough=0.44)
    save_rgba("dg_pool", rgb, a)
    rgb, a = bake_pool(256, ((0.74, 1.00, 0.98), (0.30, 0.84, 0.90), (0.13, 0.48, 0.66)),
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
    elif len(sys.argv) > 1 and sys.argv[1] == "floor":
        keep = _vnoise(RES, 3, 1501 + 61)
        for (cov, name) in ((COVER_DENSE, "dg_floor"), (COVER_SPARSE, "dg_floor_b")):
            a, kept, total = bake_ground(cov, keep_field=keep)
            a, _ = normalize_mean(a, TARGET_FLOOR)
            save_rgb(name, a)
            print("   판석 %d/%d · %s · %s"
                  % (kept, total, _tex_stat(a, name), seam_audit(a, name)))
    elif len(sys.argv) > 1 and sys.argv[1] == "wall":
        w = bake_wall()
        w, _ = normalize_mean(w, TARGET_WALL)
        save_rgb("dg_wall", w)
        print(_tex_stat(w, "dg_wall", RES / WALL_M))
    else:
        main()
