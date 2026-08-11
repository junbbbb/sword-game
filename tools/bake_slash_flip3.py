# -*- coding: utf-8 -*-
"""codex 작화 참격 6프레임을 플립북 시트로 굽는다 (web/tex/slash_flip3.png).

  2048 x 1920 = 가로 2칸(가로베기 · 대각베기) x 세로 6칸(한 획의 6프레임)
  ★칸 배치는 아래 CELLS 가 정한다 — 원화 6장을 1:1 로 얹지 않는다(오너 판정. 그 항 참조)
  칸 하나 1024 x 320  ← ★slash_flip.png 와 **같은 규격**이다(그 자리에 그대로 꽂힌다)

── 이 파일이 bake_slash_flip.py 와 갈라진 이유 ──
저쪽은 획을 **절차로 그린다**(프로파일 · 갈필 · 조각을 수식으로 만든다).
이쪽은 그리지 않는다 — codex(gpt-5.6-sol)가 귀멸 실프레임을 보고 **직접 그린 낱장**
`incoming/codex_fx/frame_1..6.png`(1024², 검은 배경)를 게임의 밝기 계약으로 **번역만** 한다.
그래서 이 파일에 있는 것은 전부 '옮기는 자'다: 회전 · 이방 축소 · 색→밝기 사상 · 먹 테두리 보강.
★기존 스크립트는 한 글자도 안 건드린다(오너 지시). 롤백은 시트 파일을 안 쓰는 것으로 끝난다.

── ★밝기 계약 (bake_slash_flip.py 와 **완전히 같다**. 어기면 화면 색이 통째로 틀어진다) ──
시트는 **회색조**다. 색은 feel.js 가 팔레트로 다시 칠한다(처치=진홍 / 물=감청).
feel.js 는 픽셀 밝기를 문턱 uThr 과 비교해 네 단으로 나눈다.
      먹(ink)  0.12   <- 처치 0.38 · 물 0.30 문턱보다 아래
      가장자리 0.45   <- 두 팔레트 다 'edge'
      중간     0.70   <- 물에서만 갈린다(처치는 edge 로 합쳐진다. 의도)
      흰 심    0.95   <- 두 팔레트 다 'core'
codex 원화는 정확히 **다섯 색**뿐이라 사상이 1:1 로 떨어진다:
      #000000 배경   -> 알파 0
      #04061E 먹선   -> 0.12
      #0F1F70 감청   -> 0.45
      #1FB1E6 시안   -> 0.70
      #FAFDFF 흰 심  -> 0.95
★알파는 **0 아니면 255**(이진)다. feel.js 는 `if (!(a > 0.004)) discard;` 로 읽는데,
  이 부정형은 알파가 NaN 이어도 버리는 계약이다. 반투명 계단을 넣으면 그 계약이
  "반쯤 보이는 유령 테두리"로 새어 나온다.
★feel.js 는 이 텍스처를 **sRGB 로 안 읽는다**(colorSpace 를 안 건다).
  sRGB 로 읽으면 하드웨어가 선형으로 풀어서 0.45 가 0.17 로 내려앉고 계단이 무너진다.

── ★기하 계약 (여기가 이 파일의 핵심이다) ──
칸은 셰이더가 **판 하나에 통째로 늘려 붙인다**(cuv = q*0.5+0.5). 판의 비는
`IMPF_LEN/IMPF_THK = 0.80/0.44 = 1.818 : 1` 이다. 그래서 칸 안 그림의 픽셀 비와
화면에 앉는 비가 **다르다**. 그림을 칸에 꽉 채우면 무엇을 그렸든 화면에서 1.818:1 이 된다
(= codex 가 그린 4.13:1 짜리 혜성이 2.3배 뚱뚱해진다).
→ 그래서 세로를 **일부러 덜 채운다.** 원화 비 R 을 화면에서 그대로 지키는 높이는
      art_h = art_w * (CH/CW) * (IMPF_LEN/IMPF_THK) / R
이고, R=4.13 · art_w=996 이면 art_h = 137px(칸 높이의 43%)다.
조사(fx_research.md 2.4)의 '넓은 액션 장 L/Wmax 3.5~7.4' 안이고, 현행 시트가 화면에서
앉는 3.1:1 보다 날씬하다. **원화의 날씬함을 지키는 것이 이 계약의 전부다.**

── 회전 ──
codex 원화는 정사각 캔버스에 **좌하 -> 우상 43도 대각**으로 그려져 있다. 게임의 칸 좌표는
'획 좌표'(가로 = 획 길이축)이고 화면 각도는 판이 따로 돌린다. 그래서 원화를 -43도 돌려
**축을 수평으로 눕힌 뒤** 칸에 앉힌다(실측 후 주축 179.7도 = 수평, 머리 말림은 오른쪽).
★NEAREST 로 돌린다. 원화가 평칠 5색이라 보간을 끼우면 색이 섞여 계단이 무너진다.

── 두 칸(획 종류) ──
codex 는 한 종류만 그렸다. 게임은 가로 2칸(가로베기 h · 대각베기 d)을 요구한다.
**그림을 새로 만들지 않는다** — 같은 낱장에 bake_slash_flip.py 의 두 스타일과 같은 만큼의
활(bow)만 더 먹인다(열별 세로 이동. 재표본 없음 = 색이 안 섞인다).
      h : 얕게 아래로 부른 호 (진폭 0.150 * CH 계열)
      d : 깊게 휘는 호 + 끝에서 한 번 더 채임 (0.235 계열)

── 먹 테두리 보강 ──
원화의 먹선은 1024² 에서 6~10px 인데, 세로로 7.4배 눌러 담으면 1px 로 사라진다
(그러면 "형태를 정의하는 것은 먹선"이라는 그림체가 통째로 죽는다).
그래서 **실루엣 경계에서 다시 뜬다** — 원화 먹 ∪ (실루엣 - 안쪽으로 RIM 깎은 것).
아래쪽을 더 굵게 두는 것도 저쪽과 같다(한쪽이 굵어야 붓으로 읽힌다).

실행:
    python3 tools/bake_slash_flip3.py            # 시트 + 검증 + 미리보기
    python3 tools/bake_slash_flip3.py --tex-only
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bake_fx_tex import save_rgba, bleed_rgb, hexf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(ROOT, "web", "tex")
SRC_DIR = os.path.join(ROOT, "incoming", "codex_fx")
OUT_DIR = os.path.join(ROOT, "renders", "history", "v97_wave11", "fx_sheet")

CW, CH = 1024, 320          # 칸 하나(★slash_flip.png 와 동일)
NCOL, NROW = 2, 6
SHEET_W, SHEET_H = CW * NCOL, CH * NROW

# 밝기 계단(위 '밝기 계약')
L_INK = 0.12
L_EDGE = 0.45
L_MID = 0.70
L_CORE = 0.95

# codex 원화 5색 → 계급 인덱스
SRC_COLORS = {
    1: (0x04, 0x06, 0x1E),   # 먹선
    2: (0x0F, 0x1F, 0x70),   # 감청
    3: (0x1F, 0xB1, 0xE6),   # 시안
    4: (0xFA, 0xFD, 0xFF),   # 흰 심
}
CLS_LUM = {1: L_INK, 2: L_EDGE, 3: L_MID, 4: L_CORE}

ROT_DEG = -43.0             # 원화 주축(137도)을 수평으로 눕히는 각
MARGIN_X = 14               # 칸 좌우 여백(px). 이웃 칸이 선형 필터링으로 새어 들지 않게
MARGIN_Y = 10               # 칸 상하 여백(px). 활(bow)까지 더한 뒤에도 이만큼 남아야 한다
QUAD_ASPECT = 0.80 / 0.44   # feel.js IMPF_LEN / IMPF_THK. 판이 화면에서 갖는 비

# ── 먹 테두리 자 ──
# ★두께를 상수로 두면 안 된다. 이 그림은 머리에서 137px, 꼬리 끝에서 4px 로 **한 칸 안에서
#   30배** 얇아진다. 상수 5px 를 두르면 꼬리는 통째로 검은 얼룩이 된다(1차 굽기가 그랬다:
#   h5 먹 100% · h0 86%). 그래서 **획 두께에 비례**시키고 상·하한만 건다.
RIM_K_TOP = 0.16            # 위쪽 먹선 = 그 자리 두께의 16%
RIM_K_BOT = 0.22            # 아래쪽은 더 굵다(한쪽이 굵어야 붓으로 읽힌다)
RIM_MAX_TOP = 6             # 칸 px 상한. 화면 세로 배율 0.52 -> 약 3px
RIM_MAX_BOT = 9
RIM_MIN_THICK = 6           # 이보다 얇은 마디에는 테두리를 안 두른다(원화 그대로 둔다)
RIM_X = 10                  # 획 끝(가로 방향) 먹선. 화면 가로 배율 0.29 -> 약 3px
INK_GROW = 1                # 원화 먹선을 이만큼 부풀린다(축소로 갉힌 몫 되돌리기)

# 활(bow) 진폭 — bake_slash_flip.py 의 cy 식과 같은 계열. 칸 높이 대비.
BOW = {"h": (0.150, 0.000), "d": (0.235, 0.045)}

# ── ★칸 배치 (오너 판정 2026-08-11) ──
# 1차 굽기는 원화 6장을 f0..f5 로 그냥 얹었다. 그런데 codex 의 起筆 낱장(frame_1)은
# 실오라기라 화면에서 **18화소**였다(점유 0.002%). f0 은 히트스톱이 0.10초 붙드는 칸이라
# 그 동안 초승달이 통째로 비어 보인다 — 오너 판정: **"보이는 것이 기능 요건이다"**.
# → frame_1 을 버리고 frame_2~6 을 f0..f4 로 당긴다. 마지막 칸은 frame_6 의 **잔흔**이다.
#   (알파로 못 흐린다 — 이 시트의 알파는 0/255 이진 계약이다. 대신 덮음 문턱을 올려
#    가는 실오라기를 지우고, 꼬리 쪽을 잘라 머리 근처 조각만 남긴다. 화면에서의 페이드는
#    feel.js 의 IMPF_A_KILL[5] = 0.46 이 이미 걸어 준다.)
#   (원화 파일번호, 덮음 문턱, 남길 u 하한)
# ★2차 굽기에서 한 번 더 밀었다. frame_2 를 f0 에 놓아 봤더니 **0.015%** 였다
#   (목표 0.039%). 범인은 시트가 아니라 **팝(흰 번쩍)** 이다 — f0 은 히트스톱 칸이라
#   같은 자리에 팝의 흰 덩어리가 겹쳐 서고, 날씬해진 초승달이 그 안에 통째로 들어간다.
#   그래서 f0 에는 **제일 큰 낱장(frame_3)** 을 놓고, 조사(fx_research 2.3)가 실측한
#   원작의 **2컷 홀드**로 f1 까지 같은 그림을 붙든다. 임팩트 프레임은 "자라는 그림"이
#   아니라 "닿은 순간의 그림"이므로 이 배치가 문법에도 맞다.
#   (원화 파일번호, 덮음 문턱, 남길 u 하한)
CELLS = [
    (3, 0.50, 0.00),   # f0 打  ← 히트스톱이 붙드는 칸. 제일 큰 낱장을 여기 둔다
    (3, 0.50, 0.00),   # f1 打  2컷 홀드(원작 작화 문법)
    (4, 0.50, 0.00),   # f2 裂
    (5, 0.50, 0.00),   # f3 散
    (6, 0.50, 0.00),   # f4 殘
    (6, 0.85, 0.30),   # f5 殘殘 = frame_6 의 잔흔(굵은 데만 남기고 꼬리를 자른다)
]


def _erode(m, n):
    """4이웃 침식 n 번(scipy 없이). bake_slash_flip.py 와 같은 구현이다"""
    out = m.copy()
    for _ in range(n):
        p = np.pad(out, 1, mode="constant", constant_values=False)
        out = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    return out


def _dilate(m, n):
    out = m.copy()
    for _ in range(n):
        p = np.pad(out, 1, mode="constant", constant_values=False)
        out = (p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:])
    return out


def load_index(path):
    """원화 한 장 -> 계급 인덱스 맵(0 배경 / 1 먹 / 2 감청 / 3 시안 / 4 흰심)"""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    out = np.zeros(a.shape[:2], np.uint8)
    for k, c in SRC_COLORS.items():
        out[np.abs(a - np.array(c, np.int16)).sum(2) < 10] = k
    # 원화에 없던 색(리사이즈 흔적 등)이 섞여 있으면 가장 가까운 계급으로 붙인다
    stray = (out == 0) & (a.sum(2) > 24)
    if stray.any():
        cand = np.stack([np.abs(a - np.array(c, np.int16)).sum(2) for c in SRC_COLORS.values()])
        out[stray] = (np.argmin(cand, axis=0) + 1)[stray]
    return out


def rotated_frames():
    """6장을 **같은 각으로** 돌리고, **공통 bbox** 를 준다.
    ★칸마다 따로 맞추면 안 된다 — 그러면 여섯 장이 다 같은 크기가 되어
      '자라다가 찢어진다'는 플립북의 전부가 사라진다."""
    rots = {}
    for i in sorted(set(c[0] for c in CELLS)):
        m = load_index(os.path.join(SRC_DIR, "frame_%d.png" % i))
        r = Image.fromarray(m).rotate(ROT_DEG, resample=Image.NEAREST,
                                      expand=True, fillcolor=0)
        rots[i] = np.asarray(r)
    H = max(r.shape[0] for r in rots.values())
    W = max(r.shape[1] for r in rots.values())
    pad = {}
    for i, r in rots.items():
        p = np.zeros((H, W), np.uint8)
        y0 = (H - r.shape[0]) // 2
        x0 = (W - r.shape[1]) // 2
        p[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] = r
        pad[i] = p
    # ★공통 bbox 는 **실제로 쓰는 낱장만** 으로 잡는다(안 쓰는 frame_1 이 자를 늘리면 안 된다)
    un = np.zeros((H, W), bool)
    for p in pad.values():
        un |= (p > 0)
    ys, xs = np.nonzero(un)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return pad, box


def _cov_resize(mask, w, h):
    """이진 마스크를 (w,h) 로 **면적 평균**해서 0..1 덮음률로 준다.
    ★NEAREST 로 줄이면 세로 7배 축소에서 얇은 먹선이 통째로 증발한다."""
    im = Image.fromarray(np.uint8(mask) * 255).resize((w, h), Image.BOX)
    return np.asarray(im, np.float32) / 255.0


def _runs(v):
    """1차원 bool 에서 (시작, 끝+1) 구간 목록"""
    d = np.diff(np.concatenate(([0], v.view(np.int8), [0])))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def _rim_runs(live):
    """마디마다 **그 자리 두께에 비례하는** 먹선을 두른다.
    세로(획의 위·아래)가 본선이고, 가로(획의 앞·뒤 끝)는 마감이다.
    ★상수 두께로 두르면 얇은 꼬리가 통째로 먹이 된다 — 이 함수가 있는 이유가 그것뿐이다."""
    H, W = live.shape
    rim = np.zeros_like(live)
    for x in range(W):
        col = live[:, x]
        if not col.any():
            continue
        for a, b in _runs(col):
            th = b - a
            if th < RIM_MIN_THICK:
                continue                       # 원화 그대로 둔다(먹으로 덮으면 얼룩)
            rt = int(min(RIM_MAX_TOP, max(1, round(th * RIM_K_TOP))))
            rb = int(min(RIM_MAX_BOT, max(1, round(th * RIM_K_BOT))))
            if rt + rb >= th:                  # 속이 안 남으면 위쪽만 한 줄
                rt, rb = 1, 1
            rim[a:a + rt, x] = True
            rim[b - rb:b, x] = True
    for y in range(H):
        row = live[y]
        if not row.any():
            continue
        for a, b in _runs(row):
            ln = b - a
            if ln < 24:
                continue
            r = int(min(RIM_X, max(1, round(ln * 0.05))))
            rim[y, a:a + r] = True
            rim[y, b - r:b] = True
    return rim


def _cell(frames, box, fi, style, art_w, art_h):
    """칸 하나. (lum 0..1, alpha uint8) 을 준다"""
    x0, y0, x1, y1 = box
    srci, live_th, u_min = CELLS[fi]
    src = frames[srci][y0:y1, x0:x1]

    covs = {k: _cov_resize(src == k, art_w, art_h) for k in (1, 2, 3, 4)}
    tot = np.clip(sum(covs.values()), 0, 1)
    live = tot >= live_th                      # ★이진 알파. 반투명 계단 없음
    if u_min > 0:
        # 잔흔 칸: 꼬리 쪽을 잘라 머리 근처 조각만 남긴다
        uu = np.arange(art_w, dtype=np.float32) / max(1.0, art_w - 1.0)
        live &= (uu >= u_min)[None, :]

    # 색 계급: 먹을 뺀 셋 중 덮음이 큰 쪽
    stack = np.stack([covs[2], covs[3], covs[4]])
    pick = np.argmax(stack, axis=0)            # 0 감청 / 1 시안 / 2 흰심
    lum = np.where(pick == 2, L_CORE, np.where(pick == 1, L_MID, L_EDGE)).astype(np.float32)

    # ── 먹 테두리 ── 원화 먹 ∪ 두께비례 경계선
    ink = covs[1] >= 0.35
    if INK_GROW:
        ink = _dilate(ink, INK_GROW)
    ink = (ink | _rim_runs(live)) & live
    lum[ink] = L_INK

    # ── 칸에 앉히기 ── 가로는 여백 안에 꽉, 세로는 가운데 + 활(bow)
    cell_lum = np.zeros((CH, CW), np.float32)
    cell_a = np.zeros((CH, CW), bool)
    ax0 = MARGIN_X
    amp, wob = BOW[style]
    u = (np.arange(art_w, dtype=np.float32)) / max(1.0, art_w - 1.0)
    s = 2.0 * u - 1.0
    # 획의 중심선. 위로 부른 호가 아니라 **아래로 부른 호**다(붓이 눌리는 쪽)
    bow = CH * (amp * (1.0 - s * s) + wob * np.sin(np.pi * u * 1.7))
    bow -= bow.mean()                           # 평균 0 = 칸 가운데를 지킨다
    base = (CH - art_h) * 0.5
    for cx in range(art_w):
        oy = int(round(base + bow[cx]))
        oy = max(MARGIN_Y, min(CH - MARGIN_Y - art_h, oy))
        col_live = live[:, cx]
        cell_lum[oy:oy + art_h, ax0 + cx] = np.where(col_live, lum[:, cx], 0.0)
        cell_a[oy:oy + art_h, ax0 + cx] = col_live
    return cell_lum, np.where(cell_a, 255, 0).astype(np.uint8)


def bake(path):
    frames, box = rotated_frames()
    bw, bh = box[2] - box[0], box[3] - box[1]
    R = bw / float(bh)
    art_w = CW - 2 * MARGIN_X
    # ★기하 계약(파일 머리말). 원화 비 R 을 **화면에서** 지키는 세로 크기
    art_h = int(round(art_w * (CH / float(CW)) * QUAD_ASPECT / R))
    # 활 진폭까지 더해도 상하 여백이 남아야 한다
    max_bow = int(round(CH * (max(a for a, _ in BOW.values()) + 0.05)))
    art_h = min(art_h, CH - 2 * MARGIN_Y - max_bow)
    print("원화 공통 bbox %dx%d (R=%.2f) -> 칸 안 그림 %dx%d (화면 비 %.2f:1)"
          % (bw, bh, R, art_w, art_h,
             (QUAD_ASPECT * art_w / CW) / (art_h / float(CH))))

    sheet_rgb = np.zeros((SHEET_H, SHEET_W, 3), np.float32)
    sheet_a = np.zeros((SHEET_H, SHEET_W), np.uint8)
    stats = []
    for ci, style in enumerate(("h", "d")):
        for fi in range(NROW):
            lum, alpha = _cell(frames, box, fi, style, art_w, art_h)
            rgb = np.repeat(lum[..., None], 3, axis=2)
            # 알파 0 자리도 이웃 색으로 채운다(확대 필터가 검은 링을 만들지 않게)
            rgb = bleed_rgb(rgb, alpha, iters=26, fill_hex="1F1F1F")
            yy, xx = fi * CH, ci * CW
            sheet_rgb[yy:yy + CH, xx:xx + CW] = rgb
            sheet_a[yy:yy + CH, xx:xx + CW] = alpha
            ys, xs = np.nonzero(alpha > 0)
            m = alpha > 128
            stats.append({
                "cell": "%s%d<-원화%d" % (style, fi, CELLS[fi][0]),
                "cov": float((alpha > 0).mean()),
                "top": int(ys.min()) if len(ys) else -1,
                "bot": int(ys.max()) if len(ys) else -1,
                "left": int(xs.min()) if len(xs) else -1,
                "right": int(xs.max()) if len(xs) else -1,
                "ink": float(((np.abs(rgb[..., 0] - L_INK) < 0.02) & m).sum() / max(1, m.sum())),
                "core": float(((np.abs(rgb[..., 0] - L_CORE) < 0.02) & m).sum() / max(1, m.sum())),
            })
    save_rgba(path, sheet_rgb, sheet_a)
    return path, stats


def verify(path, stats):
    print("[검증] %s" % path)
    a = np.asarray(Image.open(path).convert("RGBA"))
    print("  크기 %dx%d · %.0f KB" % (a.shape[1], a.shape[0], os.path.getsize(path) / 1024.0))
    bad = 0
    for s in stats:
        m_top, m_bot = s["top"], CH - 1 - s["bot"]
        mark = ""
        if m_top < 6 or m_bot < 6 or s["left"] < 2 or (CW - 1 - s["right"]) < 2:
            mark = "  ← 여백 부족!"
            bad += 1
        print("  %-12s 덮음 %5.2f%%  먹 %4.1f%%  심 %4.1f%%  여백 위%3d 아래%3d  x %4d..%4d%s"
              % (s["cell"], s["cov"] * 100, s["ink"] * 100, s["core"] * 100,
                 m_top, m_bot, s["left"], s["right"], mark))
    al = a[..., 3]
    mid = ((al > 0) & (al < 255)).mean() * 100
    print("  알파: 0 %.1f%% · 255 %.1f%% · 그 사이 %.3f%%  %s"
          % ((al == 0).mean() * 100, (al == 255).mean() * 100, mid,
             "" if mid == 0 else "← 이진 알파 계약 위반!"))
    if mid > 0:
        bad += 1
    lv, cnt = np.unique(a[..., 0][al > 128], return_counts=True)
    top = sorted(zip(cnt, lv), reverse=True)[:6]
    tot = max(1, (al > 128).sum())
    print("  밝기 상위: %s" % ", ".join("%d(%.0f%%)" % (v, c / tot * 100) for c, v in top))
    # ★save_rgba 와 **같은 식**으로 반올림해야 한다(int(round(178.5)) 은 178 이지만
    #   uint8(0.70*255+0.5) 은 179 다. 파이썬 round 는 짝수로 붙는다)
    want = set(int(np.uint8(v * 255 + 0.5)) for v in (L_INK, L_EDGE, L_MID, L_CORE))
    got = set(int(v) for v in lv)
    if not got <= want:
        print("  ★밝기 계약 위반: 계단 밖 값 %s" % sorted(got - want)[:8])
        bad += 1
    print("  검증 실패 항목 %d개" % bad)
    return bad == 0


# feel.js 의 밝기 계단 로직을 그대로 옮긴 미리보기(코드와 그림이 어긋나면 여기서 걸린다)
PAL = {
    "kill": {"ink": "2A0710", "edge": "D21B32", "mid": "D21B32", "core": "FFF2F2",
             "thr": (0.38, 0.82, 0.82)},
    "water": {"ink": "081228", "edge": "0C3C9C", "mid": "24CCFC", "core": "CCE4FC",
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
    p = os.path.join(TEX_DIR, "slash_flip3.png")
    # ★원자적 저장: 임시 파일에 다 굽고 마지막에 rename 한다(반쯤 쓰인 png 를
    #   게임이 읽어 텍스처가 통째로 검게 나오는 사고를 막는다)
    tmp = p + ".tmp.png"
    tmp, stats = bake(tmp)
    ok = verify(tmp, stats)
    os.replace(tmp, p)
    print("구움: %s (%d bytes)" % (p, os.path.getsize(p)))
    if "--tex-only" not in sys.argv:
        preview(p, os.path.join(OUT_DIR, "SHEET_slash_flip3.png"))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
