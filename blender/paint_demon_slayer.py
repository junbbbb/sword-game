#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ToonSoldiers WW2 텍스처를 귀멸 대원복으로 리페인트.

핵심 기법: 원본은 프로가 그린 명암(주름·재봉선·그림자)을 갖고 있다.
그 휘도(luminance)를 그대로 살리고 색상만 갈아끼우면 붓질 퀄리티를 유지한 채 옷을 바꿀 수 있다.
  new_pixel = new_base_color * (L / L_mean_of_region)
"""
import json
import os
import math
from PIL import Image, ImageDraw, ImageFilter

SCRATCH = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad"
ROOT = "/Users/lbj/Documents/gameproject"
UVJSON = os.path.join(SCRATCH, "uvmap.json")
TEX = os.path.join(SCRATCH, "soldier_tex.png")
OUT = os.path.join(ROOT, "refpack/demon_slayer_tex.png")

S = 512

# 부위 -> 새 베이스 색 (귀멸 대원복 팔레트, 오리지널 변형)
PALETTE = {
    "torso":    (0x26, 0x2b, 0x38),   # 대원복 차콜
    "upperarm": (0x26, 0x2b, 0x38),
    "forearm":  (0x26, 0x2b, 0x38),
    "thigh":    (0x1e, 0x22, 0x2e),   # 하카마(더 어둡게)
    "calf":     (0xe7, 0xe2, 0xd2),   # 흰 각반
    "foot":     (0x24, 0x1b, 0x15),   # 짚신/조리
    "helmet":   (0x3a, 0x24, 0x32),   # 머리카락(먹빛 자주)
    "face":     (0xf0, 0xbe, 0x96),   # 피부
    "hand":     (0xf0, 0xbe, 0x96),   # 피부(소총 아일랜드는 메시에서 삭제됨)
}
# 부위별 대비 강도(1.0=원본 명암 그대로, <1=평탄, >1=강조)
CONTRAST = {
    "torso": 1.05, "upperarm": 1.05, "forearm": 1.05, "thigh": 1.0,
    "calf": 0.85, "foot": 0.9, "helmet": 1.15, "face": 0.85, "hand": 0.85,
}
# 기준 밝기 백분위: 베이스 색이 "이 밝기"에 대응한다.
# 피부는 높게(밝은 부분이 살색 = 하이라이트가 흰색으로 날아가지 않음), 천은 중간.
REF_PCT = {
    "torso": 62, "upperarm": 62, "forearm": 62, "thigh": 62,
    "calf": 70, "foot": 62, "helmet": 66, "face": 88, "hand": 88,
}
RATIO_CAP = {"face": 1.06, "hand": 1.06, "calf": 1.10}   # 기본 1.35

REGION_COLOR = {   # uv_overlay.py 와 동일해야 함
    "face": (255, 80, 80), "helmet": (255, 190, 60), "torso": (70, 200, 120),
    "upperarm": (70, 170, 255), "forearm": (150, 120, 255), "hand": (255, 90, 220),
    "thigh": (255, 140, 40), "calf": (120, 255, 230), "foot": (200, 200, 200),
    "other": (100, 100, 100),
}


def build_masks():
    """부위별 마스크를 UV 폴리곤에서 직접 래스터라이즈(가장자리 여유분 포함)."""
    data = json.load(open(UVJSON))
    masks = {}
    for reg in PALETTE:
        masks[reg] = Image.new("L", (S, S), 0)
    draws = {r: ImageDraw.Draw(m) for r, m in masks.items()}
    for f in data["faces"]:
        reg = f["region"]
        if reg not in draws:
            continue
        p = [(u * S, (1.0 - v) * S) for u, v in f["uv"]]
        draws[reg].polygon(p, fill=255)
        draws[reg].line(p + [p[0]], fill=255, width=3)   # 시접(bleed) 여유
    # 각 마스크를 조금 부풀려 아일랜드 경계 밖 여백까지 덮는다
    for r in masks:
        masks[r] = masks[r].filter(ImageFilter.MaxFilter(5))
    return masks


def main():
    src = Image.open(TEX).convert("RGB").resize((S, S), Image.LANCZOS)
    sp = src.load()
    masks = build_masks()
    mp = {r: m.load() for r, m in masks.items()}

    # 부위별 평균 휘도
    lum = [[0.0] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            r, g, b = sp[x, y]
            lum[y][x] = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

    means = {}
    for reg in PALETTE:
        vals = []
        row = mp[reg]
        for y in range(S):
            for x in range(S):
                if row[x, y]:
                    vals.append(lum[y][x])
        if vals:
            vals.sort()
            idx = min(len(vals) - 1, int(len(vals) * REF_PCT[reg] / 100.0))
            means[reg] = max(vals[idx], 1e-3)
        else:
            means[reg] = 0.5
        print("%-9s ref_lum(p%d)=%.3f  px=%d" % (reg, REF_PCT[reg], means[reg], len(vals)))

    out = Image.new("RGB", (S, S), (24, 26, 32))
    op = out.load()
    # 우선순위: 작은 부위가 큰 부위를 덮도록(마스크 겹칠 때)
    order = ["torso", "thigh", "upperarm", "forearm", "calf", "foot", "hand", "helmet", "face"]
    for y in range(S):
        for x in range(S):
            for reg in order:
                if mp[reg][x, y]:
                    base = PALETTE[reg]
                    k = CONTRAST[reg]
                    cap = RATIO_CAP.get(reg, 1.35)
                    ratio = lum[y][x] / means[reg]
                    ratio = 1.0 + (ratio - 1.0) * k
                    ratio = max(0.20, min(cap, ratio))
                    op[x, y] = tuple(min(255, int(c * ratio)) for c in base)
    out.save(OUT)
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
