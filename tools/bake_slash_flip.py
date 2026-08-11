# -*- coding: utf-8 -*-
"""참격 플립북 시트를 굽는다 (web/tex/slash_flip.png).

  2048 x 1920 = 가로 2칸(가로베기 · 대각베기) x 세로 6칸(한 획의 6프레임)
  칸 하나 1024 x 320

── 왜 시트인가 ──
지금까지 참격은 셰이더가 시간을 **연속 보간**해 그렸다(머리가 미끄러져 나가고
꼬리가 서서히 사라진다). 그건 3D 리본의 문법이고, 귀멸 애니의 문법이 아니다.
애니의 참격은 **작화가가 그린 낱장 6~8장이 24fps 로 뚝뚝 넘어가는 것**이다.
그래서 낱장을 여기서 굽고, feel.js 는 1/24초마다 다음 칸으로 **점프**만 한다.

── 이 파일이 bake_fx_tex.py 와 갈라진 이유 ──
문법(평칠 계단 · 스트레이트 알파 · 먹 번짐 · 갈필)은 bake_fx_tex.py 것을 그대로
쓴다. 실제로 fbm2 · stepped_alpha · bleed_rgb · save_rgba 를 **거기서 import** 한다.
파일만 가른 것은 그 파일을 다른 작업(지면 타일)이 같은 시각에 고치고 있었기
때문이다. 한 파일을 둘이 쓰면 한쪽 저장이 다른 쪽을 지운다.

── ★밝기 계약 (여기를 어기면 게임에서 색이 통째로 틀어진다) ──
이 시트는 **회색조**다. 색은 feel.js 가 팔레트로 다시 칠한다(처치=진홍 / 물=감청).
feel.js 는 픽셀 밝기를 문턱 uThr 과 비교해 네 단으로 나눈다. 그래서 굽는 쪽은
문턱 사이 한가운데에 값을 놓아야 한다.
      먹(ink)  0.12   <- 처치 0.38 · 물 0.30 문턱보다 아래
      가장자리 0.45   <- 두 팔레트 다 'edge'
      중간     0.70   <- 물에서만 갈린다(처치는 edge 로 합쳐진다. 의도)
      흰 심    0.95   <- 두 팔레트 다 'core'
★그리고 feel.js 는 이 텍스처를 **sRGB 로 안 읽는다**(colorSpace 를 안 건다).
  sRGB 로 읽으면 하드웨어가 선형으로 풀어서 0.45 가 0.17 로 내려앉고 계단이 무너진다.

── 프레임 진행 (한 획이 자라며 갈필로 찢어진다) ──
  f0 起筆   짧고 두껍게 눌러 넣은 머리
  f1 送筆   절반쯤 뻗음. 몸통이 제일 굵다
  f2 全長   끝까지 뻗음. 갈필이 시작된다
  f3 裂     머리는 그대로, 꼬리가 찢겨 나가기 시작
  f4 散     가닥으로 갈라지고 조각이 튄다
  f5 殘     성긴 조각만 남는다(다음 프레임에 사라진다)

실행:
    python3 tools/bake_slash_flip.py            # 시트 + 검증 + 미리보기
    python3 tools/bake_slash_flip.py --tex-only
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bake_fx_tex import (fbm1, fbm2, stepped_alpha, save_rgba, bleed_rgb, hexf)  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(ROOT, "web", "tex")
OUT_DIR = os.path.join(ROOT, "renders", "history", "v91_fx2")

CW, CH = 1024, 320          # 칸 하나
NCOL, NROW = 2, 6           # 가로 2종 x 6프레임
SHEET_W, SHEET_H = CW * NCOL, CH * NROW

# 밝기 계단(위 '밝기 계약' 참조)
L_INK = 0.12
L_EDGE = 0.45
L_MID = 0.70
L_CORE = 0.95

# 먹 외곽선 두께(칸 픽셀). 화면에서는 세로로 약 0.43배, 가로로 0.27배 축소돼 얹히므로
# 12px 는 화면 5px 남짓이 된다. 애니 먹선(720p 기준 3~5px)과 같은 굵기다.
RIM = 10
RIM_OUT = 4                 # 바깥(아래) 선은 이만큼 더 굵다. 한쪽이 굵어야 붓으로 읽힌다
MARGIN = 14                 # 칸 가장자리 여백(px). 이웃 칸이 필터링으로 새어 들지 않게

# 프레임표: (꼬리 u0, 머리 u1, 굵기배수, 갈필세기, 조각수)
FRAMES = {
    "h": [(0.00, 0.34, 0.72, 0.02, 0),
          (0.00, 0.68, 0.98, 0.15, 2),
          (0.01, 1.00, 1.00, 0.34, 5),
          (0.16, 1.00, 0.88, 0.55, 8),
          (0.40, 1.00, 0.66, 0.76, 10),
          (0.65, 1.00, 0.44, 0.90, 11)],
    "d": [(0.00, 0.30, 0.78, 0.02, 0),
          (0.00, 0.72, 1.00, 0.18, 3),
          (0.02, 1.00, 0.96, 0.38, 6),
          (0.22, 1.00, 0.82, 0.58, 9),
          (0.46, 1.00, 0.60, 0.78, 11),
          (0.70, 1.00, 0.40, 0.92, 12)],
}


def _erode(m, n):
    """4이웃 침식 n 번. L1 거리 n 만큼 안으로 파고든 마스크를 준다.
    (scipy 없이 쓰려고 이렇게 한다. 1024x320 x 12번이라 순식간이다)"""
    out = m.copy()
    for _ in range(n):
        p = np.pad(out, 1, mode="constant", constant_values=False)
        out = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    return out


def _cell(style, fi, rng):
    """칸 하나. (cov 0..1, lum 0..1) 을 준다"""
    W, H = CW, CH
    # ★u 는 칸 안 좌표가 아니라 **획 좌표**다. 칸 좌우에 MARGIN 만큼 여백을 남기려고
    #   0..1 을 칸의 [MARGIN, W-MARGIN] 구간에 편다. 여백이 없으면 옆 칸(다른 획 종류)이
    #   선형 필터링으로 새어 들어와 획 끝에 유령이 붙는다.
    u = (np.arange(W, dtype=np.float32) - MARGIN) / (W - 1.0 - 2 * MARGIN)
    y = np.arange(H, dtype=np.float32)[:, None]
    u0, u1, tk, dry, nfrag = FRAMES[style][fi]
    s = 2.0 * u - 1.0

    if style == "h":
        # 가로베기: 얕게 아래로 부른 호. 몸통이 가운데
        cy = H * (0.400 + 0.150 * (1.0 - s * s))
        prof = np.interp(u, [0.00, 0.05, 0.14, 0.32, 0.52, 0.72, 0.88, 1.00],
                            [0.03, 0.52, 0.90, 1.00, 0.92, 0.70, 0.38, 0.04])
        maxhw = H * 0.210
    else:
        # 대각베기: 깊게 휘고 끝에서 한 번 더 채인다(S). 몸통이 앞쪽
        cy = H * (0.330 + 0.235 * (1.0 - s * s) + 0.045 * np.sin(np.pi * u * 1.7))
        prof = np.interp(u, [0.00, 0.05, 0.12, 0.26, 0.44, 0.64, 0.82, 1.00],
                            [0.03, 0.62, 1.00, 0.97, 0.78, 0.52, 0.26, 0.03])
        maxhw = H * 0.185
    cy = cy.astype(np.float32)
    hw = np.maximum(maxhw * tk * prof, 1.5).astype(np.float32)

    # 손그림 노이즈 세 벌(위 가장자리 · 아래 가장자리 · 잔결)
    coarse_t = fbm2(H, W, 2, 7, rng, octaves=3)
    coarse_b = fbm2(H, W, 2, 6, rng, octaves=3)
    fine = fbm2(H, W, 3, 30, rng, octaves=2)

    tt = (y - cy[None, :]) / hw[None, :]        # 음수=위 / 양수=아래
    at = np.abs(tt)
    # ★찢김은 마를수록 커진다. 앞 프레임은 젖은 붓이라 가장자리가 매끈하고,
    #   뒤 프레임은 종이를 긁는 붓이라 이가 크게 빠진다
    e_top = 1.00 + (0.17 + 0.20 * dry) * (coarse_t - 0.5) * 2 + 0.08 * (fine - 0.5) * 2
    e_bot = 1.00 + (0.23 + 0.26 * dry) * (coarse_b - 0.5) * 2 + 0.11 * (fine - 0.5) * 2
    edge = np.where(tt < 0, e_top, e_bot).astype(np.float32)

    # 머리: 비스듬히 뾰족하게 끊는다(수직으로 자르면 붓이 아니라 잘린 띠다)
    ttc = np.clip(tt, -1.6, 1.6)
    if u1 >= 0.999:
        head = np.ones((H, W), np.float32)      # 프로파일이 이미 뾰족하다
    else:
        uh = u1 - 0.040 * ttc - 0.020 * ttc * ttc + 0.022 * (fine - 0.5) * 2
        head = np.clip((uh - u[None, :]) / 0.050, 0, 1)
    # 꼬리: 起筆(볼록하게 눌러 넣은 자국) -> 뒤 프레임에서는 찢겨 나간 자리
    ut = (u0 + 0.045 * ttc + 0.028 * ttc * ttc
          + (0.018 + 0.055 * dry) * (coarse_t - 0.5) * 2)
    tail = np.clip((u[None, :] - ut) / (0.030 + 0.060 * dry), 0, 1)
    live = (head * tail).astype(np.float32)

    # 칸 여백 밖은 아예 안 그린다(u 를 잘라 쓰면 여백에 실오라기가 눕는다)
    xp = np.arange(W)[None, :]
    inbox = ((xp >= MARGIN) & (xp <= W - 1 - MARGIN)).astype(np.float32)

    # 실루엣(갈필 이전). 먹 외곽선은 **이걸로** 뜬다. 갈필 구멍까지 테두리를 두르면
    # 획 전체가 먹 덩어리가 된다
    solid = np.clip((edge - at) * hw[None, :] / 2.2, 0, 1) * live * inbox
    sbin = solid > 0.5
    rim = sbin & ~_erode(sbin, RIM)
    rim |= sbin & (tt > 0) & ~_erode(sbin, RIM + RIM_OUT)

    # ── 갈필(dry brush) ── 굵은 가로 결. 뒤로 갈수록·바깥 털부터 끊긴다
    fiber = (0.58 * fbm2(H, W, 52, 7, rng, octaves=2)
             + 0.42 * fbm2(H, W, 112, 4, rng, octaves=2))
    span = max(u1 - u0, 0.20)
    ramp = np.clip((u - (u0 + 0.04)) / span, 0, 1) ** 1.05
    thr = 0.03 + (0.34 + 0.62 * dry) * ramp[None, :] * (0.30 + 0.72 * np.clip(at, 0, 1.2))
    cov = solid * np.clip((fiber - thr) / 0.045, 0, 1)

    # 비백(飛白): 젖은 몸통에도 붓털 사이로 종이가 비친 가는 틈. 얇게.
    vein = fbm2(H, W, 54, 11, rng, octaves=2)
    cov *= 1.0 - np.clip((vein - (0.888 - 0.090 * dry)) / 0.014, 0, 1)
    # ★먹 테두리는 갈필로 다 갉히면 안 된다. 절반만 갉히게 되돌린다
    cov = np.where(rim, np.maximum(cov, solid * 0.72), cov)

    # ── 밝기 계단 ──
    shift = (-0.20 + 0.10 * np.sin(u * 4.3 + 1.1)).astype(np.float32)
    a2 = np.clip(np.abs(tt - shift[None, :]) / np.maximum(edge, 1e-3), 0, 1)
    core_w = 0.35 * (1.0 - 0.40 * fi / 5.0)      # 마를수록 심이 좁아진다
    lum = np.where(a2 < core_w, L_CORE, np.where(a2 < 0.60, L_MID, L_EDGE)).astype(np.float32)
    # 갓선: 띠를 가르는 가는 밝은 선 한 줄(wave 텍스처부터 이어 온 서명)
    lum[(np.abs(a2 - 0.60) < 0.013) & (cov > 0.35)] = L_CORE
    lum[rim] = L_INK

    # ── 튄 조각 ── 머리 앞쪽과 바깥으로 몇 점. 전부 **통짜 먹**이다.
    # ★가운데를 밝게 비우면 동그란 고리(비눗방울)로 보인다. 애니의 튄 먹은 꽉 찬 점이다.
    for _ in range(nfrag):
        uu = float(rng.uniform(max(0.0, u0 - 0.02), min(1.04, u1 + 0.08)))
        cxp = MARGIN + uu * (W - 1.0 - 2 * MARGIN)
        base = float(np.interp(np.clip(uu, 0, 1), u, cy))
        cyp = base + float(rng.normal(0.0, maxhw * 0.85)) * (1.0 if rng.random() < 0.7 else -1.0)
        rr = float(rng.uniform(2.5, 8.0))
        ar = float(rng.uniform(1.8, 3.6))
        # 칸 여백 안에 들어오는 조각만 쓴다(가장자리를 물면 이웃 칸으로 샌다)
        if not (MARGIN + rr * ar < cxp < W - MARGIN - rr * ar):
            continue
        if not (MARGIN + rr < cyp < H - MARGIN - rr):
            continue
        y0, y1 = int(cyp - rr - 2), int(cyp + rr + 3)
        x0, x1 = int(cxp - rr * ar - 2), int(cxp + rr * ar + 3)
        dy = (np.arange(y0, y1)[:, None] - cyp) / rr
        dx = (np.arange(x0, x1)[None, :] - cxp) / (rr * ar)
        blob = (dx * dx + dy * dy < 1.0)
        cov[y0:y1, x0:x1] = np.maximum(cov[y0:y1, x0:x1], blob.astype(np.float32))
        sub = lum[y0:y1, x0:x1]
        sub[blob] = L_INK
        lum[y0:y1, x0:x1] = sub

    return np.clip(cov, 0, 1), lum


def bake_slash_flip(path):
    rng = np.random.default_rng(20260810 + 91)
    sheet_rgb = np.zeros((SHEET_H, SHEET_W, 3), np.float32)
    sheet_a = np.zeros((SHEET_H, SHEET_W), np.uint8)
    stats = []
    for ci, style in enumerate(("h", "d")):
        for fi in range(NROW):
            cov, lum = _cell(style, fi, rng)
            alpha = stepped_alpha(cov)
            # 먹선은 반투명하면 안 된다. 테두리가 흐리면 그림이 아니라 번짐이 된다
            alpha[(lum <= L_INK + 1e-3) & (cov > 0.35)] = 255
            rgb = np.repeat(lum[..., None], 3, axis=2)
            # 알파 0 자리도 이웃 색으로 채운다(확대 필터가 검은 링을 만들지 않게)
            rgb = bleed_rgb(rgb, alpha, iters=26, fill_hex="1F1F1F")
            y0, x0 = fi * CH, ci * CW
            sheet_rgb[y0:y0 + CH, x0:x0 + CW] = rgb
            sheet_a[y0:y0 + CH, x0:x0 + CW] = alpha
            ys, xs = np.nonzero(alpha > 0)
            stats.append({
                "cell": "%s%d" % (style, fi),
                "cov": float((alpha > 0).mean()),
                "top": int(ys.min()) if len(ys) else -1,
                "bot": int(ys.max()) if len(ys) else -1,
                "left": int(xs.min()) if len(xs) else -1,
                "right": int(xs.max()) if len(xs) else -1,
                "ink": float(((np.abs(rgb[..., 0] - L_INK) < 0.02) & (alpha > 128)).mean()),
                "core": float(((np.abs(rgb[..., 0] - L_CORE) < 0.02) & (alpha > 128)).mean()),
            })
    save_rgba(path, sheet_rgb, sheet_a)
    return path, stats


def verify(path, stats):
    print("[검증] %s" % path)
    a = np.asarray(Image.open(path).convert("RGBA"))
    print("  크기 %dx%d · %.0f KB" % (a.shape[1], a.shape[0], os.path.getsize(path) / 1024.0))
    bad = 0
    for s in stats:
        # 칸 여백: 위·아래 6px 이상 비어 있어야 이웃 칸이 필터링으로 새어 들지 않는다
        m_top, m_bot = s["top"], CH - 1 - s["bot"]
        mark = ""
        if m_top < 6 or m_bot < 6 or s["left"] < 2 or (CW - 1 - s["right"]) < 2:
            mark = "  ← 여백 부족!"
            bad += 1
        print("  %-4s 덮음 %5.1f%%  먹 %4.1f%%  심 %4.1f%%  여백 위%3d 아래%3d  x %4d..%4d%s"
              % (s["cell"], s["cov"] * 100, s["ink"] * 100, s["core"] * 100,
                 m_top, m_bot, s["left"], s["right"], mark))
    # 알파 분포(스트레이트 알파 · 계단인지)
    al = a[..., 3]
    print("  알파: 0 %.0f%% · 255 %.0f%% · 그 사이 %.1f%%"
          % ((al == 0).mean() * 100, (al == 255).mean() * 100,
             ((al > 0) & (al < 255)).mean() * 100))
    lv, cnt = np.unique(a[..., 0][al > 128], return_counts=True)
    top = sorted(zip(cnt, lv), reverse=True)[:6]
    print("  밝기 상위: %s" % ", ".join("%d(%.0f%%)" % (v, c / max(1, (al > 128).sum()) * 100)
                                        for c, v in top))
    print("  여백 미달 칸 %d개" % bad)
    return bad == 0


# 게임이 이 시트로 무엇을 그리는지 눈으로 확인하는 장. feel.js 의 밝기 계단 로직을
# 그대로 파이썬으로 옮겨 두 팔레트로 다시 칠한다(코드와 그림이 어긋나면 여기서 걸린다).
PAL = {
    "kill": {"ink": "2A0710", "edge": "D21B32", "mid": "D21B32", "core": "FFF2F2",
             "thr": (0.38, 0.82, 0.82)},
    "water": {"ink": "1428C8", "edge": "288CD2", "mid": "3CBEF0", "core": "F0F0F0",
              "thr": (0.30, 0.55, 0.82)},
}


def preview(path, out):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0
    lum = a[..., 0]
    H, W = lum.shape
    tiles = []
    for name, p in PAL.items():
        t0, t1, t2 = p["thr"]
        col = np.zeros((H, W, 3), np.float32)
        col[:] = hexf(p["ink"])
        col[lum > t0] = hexf(p["edge"])
        col[lum > t1] = hexf(p["mid"])
        col[lum > t2] = hexf(p["core"])
        # 종이색 배경 위에 일반합성(게임과 같은 NormalBlending)
        bg = np.zeros((H, W, 3), np.float32)
        bg[:] = hexf("C8BFA8")
        al = a[..., 3:4]
        tiles.append((name, np.clip(col * al + bg * (1 - al), 0, 1)))
    sheet = Image.new("RGB", (W, H * len(tiles) + 8 * (len(tiles) - 1)), (30, 30, 34))
    for i, (_n, t) in enumerate(tiles):
        sheet.paste(Image.fromarray(np.uint8(t * 255 + 0.5)), (0, i * (H + 8)))
    sheet = sheet.resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS)
    sheet.save(out)
    print("미리보기: %s %s" % (out, sheet.size))
    return out


def main():
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(TEX_DIR, "slash_flip.png")
    p, stats = bake_slash_flip(p)
    print("구움: %s (%d bytes)" % (p, os.path.getsize(p)))
    ok = verify(p, stats)
    if "--tex-only" not in sys.argv:
        preview(p, os.path.join(OUT_DIR, "SHEET_slash_flip.png"))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
