# -*- coding: utf-8 -*-
"""codex 포말 마루 원화 16종을 게임용 회색조 시트로 굽는다.

입력(각 1536x1024, 4x2 contact sheet):
  incoming/codex_foam/foam_crest_claw_master.png
  incoming/codex_foam/foam_crest_round_master.png

출력:
  web/tex/foam_crest_sheet.png                 2048x1024, 4x4, cell 512x256
  renders/history/v99_wave16/foam_fx/art/foam_crest_sheet_preview.png
  renders/history/v99_wave16/foam_fx/art/foam_crest_bake.json

원화는 image_gen 이 실측 스틸을 형태 레퍼런스로 받아 만든 평칠 contact sheet 다.
이 스크립트는 그림을 새로 만들지 않고 다음 계약만 기계적으로 강제한다.

  * 각 입력을 4x2 고정 격자로 자르고 셀 안 내용 bbox 를 자동 검출한다.
  * 긴 아래 먹선의 기울기를 재서 수평으로 눕힌다. 런타임 quad 의 x축이 궤적 접선이다.
  * 둥근 원화도 화면에서 깃발이 되지 않도록 실루엣 비를 최소 2.6:1 로 압축한다.
  * 생성 원화의 미세 그라데이션을 회색조 네 단으로 양자화한다.
        먹 0.12 / 감청 0.46 / 시안 0.70 / 흰심 0.95
    색은 feel.js 가 다시 칠한다. 이 텍스처에는 colorSpace 를 걸면 안 된다.
  * 알파는 0/255 이진이다. 투명 RGB 는 가장자리 색으로 bleed 한다.
  * 실루엣 바깥 4px 는 반드시 먹으로 닫아 축소 후에도 윤곽이 남게 한다.
  * R2 합성 계약: 런타임 v=0.20 아래의 밝은 하부 물결은 버리고, 그 바로 아래
    v=0.04~0.20 에 있던 먹만 남긴다. 먹 한 줄은 흰 리본 경계에 걸치고 흰 포말은
    리본 밖 어두운 배경에서 시작하게 만드는 절단선이다.

실행:
  python3 tools/bake_foam_crest.py
  python3 tools/bake_foam_crest.py --tex-only
"""
from __future__ import annotations

import argparse
from collections import deque
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bake_fx_tex import bleed_rgb, save_rgba  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "incoming", "codex_foam")
TEX_DIR = os.path.join(ROOT, "web", "tex")
ART_DIR = os.path.join(ROOT, "renders", "history", "v99_wave16", "foam_fx", "art")

SOURCES = (
    ("foam_crest_claw_master.png", "claw"),
    ("foam_crest_round_master.png", "round"),
)

SRC_COLS, SRC_ROWS = 4, 2
CELL_W, CELL_H = 512, 256
ATLAS_COLS, ATLAS_ROWS = 4, 4
ATLAS_W, ATLAS_H = CELL_W * ATLAS_COLS, CELL_H * ATLAS_ROWS
MARGIN_X, MARGIN_Y = 12, 10

# R2: 리본과 포말의 합성 경계. 런타임 UV 기준(0=quad 안쪽, 1=바깥).
# 밝은 화소는 SEAM_V 이상에서만 살고, 먹선만 INK_OVERLAP_V 만큼 안쪽에 남는다.
SEAM_V = 0.20
INK_OVERLAP_V = 0.16

# feel.js 가 읽는 회색조 밝기 계약. 텍스처는 sRGB decode 없이 읽는다.
L_INK = 0.12
L_EDGE = 0.46
L_CYAN = 0.70
L_CORE = 0.95
LUM = np.array([L_INK, L_EDGE, L_CYAN, L_CORE], np.float32)

# image_gen 프롬프트에 준 네 색. 결과에 생긴 미세 음영은 가장 가까운 색으로 붙인다.
SOURCE_PALETTE = np.array(
    [
        [0x07, 0x15, 0x2B],
        [0x17, 0x4A, 0x78],
        [0x32, 0xBE, 0xEA],
        [0xF6, 0xFC, 0xFF],
    ],
    np.float32,
)


def _foreground(rgb: np.ndarray) -> np.ndarray:
    """검은 배경·거터를 제외한다. 가장 어두운 먹선(#07152b)은 살린다."""
    mx = rgb.max(axis=2)
    # 회색 거터는 14 이하, 먹선은 blue 30~45 대역이다.
    return mx > 18


def _erode(mask: np.ndarray, n: int) -> np.ndarray:
    out = mask.copy()
    for _ in range(n):
        p = np.pad(out, 1, mode="constant", constant_values=False)
        out = (
            p[1:-1, 1:-1]
            & p[:-2, 1:-1]
            & p[2:, 1:-1]
            & p[1:-1, :-2]
            & p[1:-1, 2:]
        )
    return out


def _largest_component(mask: np.ndarray) -> np.ndarray:
    """셀 경계를 넘은 이웃 칸의 바늘 끝/미세 조각을 버리고 본체 한 덩어리만 남긴다."""
    h, w = mask.shape
    seen = np.zeros_like(mask)
    best: list[tuple[int, int]] = []
    for y0, x0 in zip(*np.nonzero(mask & ~seen)):
        if seen[y0, x0]:
            continue
        q = deque([(int(y0), int(x0))])
        seen[y0, x0] = True
        comp: list[tuple[int, int]] = []
        while q:
            y, x = q.popleft()
            comp.append((y, x))
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    q.append((yy, xx))
        if len(comp) > len(best):
            best = comp
    out = np.zeros_like(mask)
    if best:
        yy, xx = zip(*best)
        out[np.asarray(yy), np.asarray(xx)] = True
    return out


def _content_box(mask: np.ndarray, pad: int = 3) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError("빈 원화 셀")
    x0 = max(0, int(xs.min()) - pad)
    y0 = max(0, int(ys.min()) - pad)
    x1 = min(mask.shape[1], int(xs.max()) + pad + 1)
    y1 = min(mask.shape[0], int(ys.max()) + pad + 1)
    return x0, y0, x1, y1


def _baseline_angle(mask: np.ndarray) -> float:
    """각 x열의 가장 아래 live pixel에 직선을 맞춰 아래 먹선의 기울기를 잰다."""
    xs, bottoms = [], []
    for x in range(mask.shape[1]):
        yy = np.nonzero(mask[:, x])[0]
        if len(yy):
            xs.append(x)
            bottoms.append(int(yy.max()))
    if len(xs) < 24:
        return 0.0
    xs = np.asarray(xs, np.float32)
    bottoms = np.asarray(bottoms, np.float32)
    # 끝의 갈고리/바늘 하나가 회귀를 끌고 가지 않도록 중앙 90%만 쓴다.
    lo, hi = np.percentile(xs, [5, 95])
    use = (xs >= lo) & (xs <= hi)
    slope = float(np.polyfit(xs[use], bottoms[use], 1)[0])
    deg = math.degrees(math.atan(slope))
    return max(-22.0, min(22.0, deg))


def _deskew(cell: np.ndarray) -> tuple[np.ndarray, float]:
    live = _largest_component(_foreground(cell))
    cell = np.where(live[..., None], cell, 0).astype(np.uint8)
    x0, y0, x1, y1 = _content_box(live, 6)
    crop = cell[y0:y1, x0:x1]
    angle = _baseline_angle(_foreground(crop))
    if abs(angle) > 0.35:
        # PIL 양의 각은 영상 좌표계의 기울기를 같은 부호로 상쇄한다.
        crop = np.asarray(
            Image.fromarray(crop).rotate(
                angle,
                resample=Image.Resampling.BICUBIC,
                expand=True,
                fillcolor=(0, 0, 0),
            )
        )
    live = _foreground(crop)
    x0, y0, x1, y1 = _content_box(live, 4)
    return crop[y0:y1, x0:x1], angle


def _quantize(crop: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """원화 하나를 512x256 회색조/이진알파 셀에 앉힌다."""
    h0, w0 = crop.shape[:2]
    avail_w = CELL_W - 2 * MARGIN_X
    avail_h = CELL_H - 2 * MARGIN_Y
    scale = min(avail_w / max(1, w0), avail_h / max(1, h0))
    w = max(8, int(round(w0 * scale)))
    h = max(8, int(round(h0 * scale)))
    # 둥근 마루도 화면에서 높은 파도 아이콘이 되지 않게 2.6:1 이상으로 눌러 둔다.
    h = min(h, max(8, int(round(w / 2.6))))
    resized = np.asarray(
        Image.fromarray(crop).resize((w, h), Image.Resampling.LANCZOS)
    )
    live = _foreground(resized)

    flat = resized.astype(np.float32).reshape(-1, 1, 3)
    dist = ((flat - SOURCE_PALETTE[None, :, :]) ** 2).sum(axis=2)
    cls = np.argmin(dist, axis=1).reshape(h, w)
    lum = LUM[cls]

    # 생성 원화의 외곽 먹이 리사이즈로 갉혀도 최소 4 texel은 남는다.
    rim = live & ~_erode(live, 4)
    lum[rim] = L_INK

    cell_lum = np.zeros((CELL_H, CELL_W), np.float32)
    cell_a = np.zeros((CELL_H, CELL_W), np.uint8)
    x = (CELL_W - w) // 2
    y = CELL_H - MARGIN_Y - h  # 아래 먹선이 모든 셀에서 같은 높이에 앉는다.
    cell_lum[y : y + h, x : x + w] = np.where(live, lum, 0.0)
    cell_a[y : y + h, x : x + w] = np.where(live, 255, 0).astype(np.uint8)

    # R1 실측: 아래 회색 물결과 일부 흰 화소가 거의 흰 B 리본 위에 얹혀 흰 몸통은
    # 사라지고 먹선만 검푸른 가시처럼 남았다. 밝은 층의 시작선을 고정하고, 그 안쪽은
    # 얇은 먹 경계만 남긴다. 수평 직선으로 새 실루엣을 만들지 않도록 기존 먹 화소만
    # 보존하며 나머지는 알파부터 제거한다.
    v_runtime = 1.0 - (np.arange(CELL_H, dtype=np.float32) + 0.5) / CELL_H
    v_runtime = v_runtime[:, None]
    was_live = cell_a > 0
    is_ink = np.isclose(cell_lum, L_INK, atol=1e-6)
    cut_deep = was_live & (v_runtime < SEAM_V - INK_OVERLAP_V)
    cut_bright_overlap = was_live & (v_runtime < SEAM_V) & ~is_ink
    cut = cut_deep | cut_bright_overlap
    cell_a[cut] = 0
    cell_lum[cut] = 0.0

    raw_coverage = float(np.mean(was_live))
    stat = {
        "source_size": [int(w0), int(h0)],
        "baked_size": [int(w), int(h)],
        "raw_coverage": raw_coverage,
        "coverage": float(np.mean(cell_a > 0)),
        "seam_v": SEAM_V,
        "ink_overlap_v": INK_OVERLAP_V,
    }
    return cell_lum, cell_a, stat


def _load_cels(path: str) -> list[tuple[np.ndarray, float]]:
    src = np.asarray(Image.open(path).convert("RGB"))
    h, w = src.shape[:2]
    cels = []
    for row in range(SRC_ROWS):
        for col in range(SRC_COLS):
            x0, x1 = col * w // SRC_COLS, (col + 1) * w // SRC_COLS
            y0, y1 = row * h // SRC_ROWS, (row + 1) * h // SRC_ROWS
            # 거터의 회색 선을 셀 안에서 한 번 더 잘라 낸다.
            gx = max(3, (x1 - x0) // 80)
            gy = max(3, (y1 - y0) // 100)
            cell = src[y0 + gy : y1 - gy, x0 + gx : x1 - gx]
            cels.append(_deskew(cell))
    return cels


def bake(out_path: str) -> list[dict]:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    atlas_lum = np.zeros((ATLAS_H, ATLAS_W), np.float32)
    atlas_a = np.zeros((ATLAS_H, ATLAS_W), np.uint8)
    stats = []
    cell_i = 0
    for filename, family in SOURCES:
        path = os.path.join(SRC_DIR, filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        for source_i, (crop, angle) in enumerate(_load_cels(path)):
            lum, alpha, stat = _quantize(crop)
            row, col = divmod(cell_i, ATLAS_COLS)
            y, x = row * CELL_H, col * CELL_W
            atlas_lum[y : y + CELL_H, x : x + CELL_W] = lum
            atlas_a[y : y + CELL_H, x : x + CELL_W] = alpha
            stat.update(
                {
                    "cell": cell_i,
                    "family": family,
                    "source_cell": source_i,
                    "deskew_deg": round(float(angle), 3),
                }
            )
            stats.append(stat)
            cell_i += 1

    rgb = np.repeat(atlas_lum[..., None], 3, axis=2)
    rgb = bleed_rgb(rgb, atlas_a, iters=16, fill_hex="07152B")
    save_rgba(out_path, rgb, atlas_a)
    return stats


def verify(path: str, stats: list[dict]) -> tuple[bool, dict]:
    arr = np.asarray(Image.open(path).convert("RGBA"))
    alpha_values = sorted(int(v) for v in np.unique(arr[..., 3]))
    live = arr[..., 3] > 0
    gray = arr[..., 0]
    levels = sorted(int(v) for v in np.unique(gray[live])) if live.any() else []
    expected = sorted(int(v * 255 + 0.5) for v in LUM)
    coverages = [s["coverage"] for s in stats]
    bright_floor = []
    ink_floor = []
    for i, stat in enumerate(stats):
        row, col = divmod(i, ATLAS_COLS)
        cell = arr[row * CELL_H : (row + 1) * CELL_H,
                   col * CELL_W : (col + 1) * CELL_W]
        cell_live = cell[..., 3] > 0
        cell_bright = cell_live & (cell[..., 0] > expected[0])
        cell_ink = cell_live & (cell[..., 0] == expected[0])

        def min_sample_v(mask: np.ndarray) -> float:
            yy = np.nonzero(mask)[0]
            return float(1.0 - (int(yy.max()) + 1) / CELL_H) if len(yy) else 1.0

        bright_v = min_sample_v(cell_bright)
        ink_v = min_sample_v(cell_ink)
        bright_floor.append(bright_v)
        ink_floor.append(ink_v)
        stat["bright_min_v"] = round(bright_v, 6)
        stat["ink_min_v"] = round(ink_v, 6)
    ok = (
        arr.shape == (ATLAS_H, ATLAS_W, 4)
        and alpha_values == [0, 255]
        and levels == expected
        and len(stats) == 16
        and all(0.025 < c < 0.48 for c in coverages)
        and all(v >= SEAM_V - 1.0 / CELL_H for v in bright_floor)
        and all(v >= SEAM_V - INK_OVERLAP_V - 1.0 / CELL_H for v in ink_floor)
    )
    report = {
        "ok": ok,
        "size": [int(arr.shape[1]), int(arr.shape[0])],
        "grid": [ATLAS_COLS, ATLAS_ROWS],
        "cell": [CELL_W, CELL_H],
        "alpha_values": alpha_values,
        "luminance_values": levels,
        "expected_luminance_values": expected,
        "seam_v": SEAM_V,
        "ink_overlap_v": INK_OVERLAP_V,
        "bright_min_v": round(min(bright_floor), 6),
        "ink_min_v": round(min(ink_floor), 6),
        "cells": stats,
    }
    return ok, report


def save_preview(tex_path: str, preview_path: str) -> None:
    rgba = np.asarray(Image.open(tex_path).convert("RGBA"))
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    rgb = rgba[..., :3].astype(np.float32)
    bg = np.zeros_like(rgb) + np.array([13.0, 21.0, 34.0], np.float32)
    comp = np.uint8(np.clip(rgb * a + bg * (1.0 - a), 0, 255))
    Image.fromarray(comp).save(preview_path, quality=95)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex-only", action="store_true", help="미리보기 생략")
    args = ap.parse_args()
    os.makedirs(ART_DIR, exist_ok=True)
    tex_path = os.path.join(TEX_DIR, "foam_crest_sheet.png")
    stats = bake(tex_path)
    ok, report = verify(tex_path, stats)
    report_path = os.path.join(ART_DIR, "foam_crest_bake.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    if not args.tex_only:
        save_preview(tex_path, os.path.join(ART_DIR, "foam_crest_sheet_preview.png"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
