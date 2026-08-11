#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UV 아일랜드를 부위별 색으로 텍스처 위에 겹쳐 그린다(어느 픽셀이 어느 부위인지 눈으로 확인)."""
import json
import os
import sys
from PIL import Image, ImageDraw

SCRATCH = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad"
UVJSON = os.path.join(SCRATCH, "uvmap.json")
TEX = os.path.join(SCRATCH, "soldier_tex.png")
OUT_OVERLAY = os.path.join(SCRATCH, "uv_overlay.png")
OUT_MASK = os.path.join(SCRATCH, "uv_mask.png")

REGION_COLOR = {
    "face":     (255, 80, 80),
    "helmet":   (255, 190, 60),
    "torso":    (70, 200, 120),
    "upperarm": (70, 170, 255),
    "forearm":  (150, 120, 255),
    "hand":     (255, 90, 220),
    "thigh":    (255, 140, 40),
    "calf":     (120, 255, 230),
    "foot":     (200, 200, 200),
    "other":    (100, 100, 100),
}

S = 512
data = json.load(open(UVJSON))
faces = data["faces"]

base = Image.open(TEX).convert("RGB").resize((S, S), Image.NEAREST)
mask = Image.new("RGB", (S, S), (0, 0, 0))
fill = Image.new("RGB", (S, S), (0, 0, 0))
dm = ImageDraw.Draw(mask)
df = ImageDraw.Draw(fill)


def pts(uv):
    # Blender UV 원점=좌하단, PIL=좌상단
    return [(u * S, (1.0 - v) * S) for u, v in uv]


for f in faces:
    c = REGION_COLOR.get(f["region"], (100, 100, 100))
    p = pts(f["uv"])
    dm.polygon(p, fill=c)
    df.polygon(p, fill=c)

# 1) 텍스처 위에 반투명 오버레이 + 경계선
ov = Image.blend(base, fill, 0.45)
do = ImageDraw.Draw(ov)
for f in faces:
    c = REGION_COLOR.get(f["region"], (100, 100, 100))
    p = pts(f["uv"])
    do.line(p + [p[0]], fill=c, width=1)
ov = ov.resize((1024, 1024), Image.NEAREST)

# 범례
lg = ImageDraw.Draw(ov)
y = 8
for r, c in REGION_COLOR.items():
    if any(f["region"] == r for f in faces):
        lg.rectangle([8, y, 26, y + 14], fill=c, outline=(0, 0, 0))
        lg.text((32, y + 1), r, fill=(255, 255, 255))
        lg.text((31, y), r, fill=(0, 0, 0))
        y += 18
ov.save(OUT_OVERLAY)
mask.save(OUT_MASK)
print("wrote", OUT_OVERLAY)
print("wrote", OUT_MASK)

# 부위별 커버 픽셀 수
from collections import Counter
px = mask.load()
cnt = Counter()
inv = {v: k for k, v in REGION_COLOR.items()}
for yy in range(S):
    for xx in range(S):
        c = px[xx, yy]
        if c != (0, 0, 0):
            cnt[inv.get(c, "?")] += 1
tot = sum(cnt.values())
print("\n%-10s %8s %7s" % ("REGION", "PIXELS", "SHARE"))
for r, n in cnt.most_common():
    print("%-10s %8d %6.1f%%" % (r, n, n / tot * 100))
print("%-10s %8d  (%.1f%% of 512x512 used)" % ("TOTAL", tot, tot / (S * S) * 100))
