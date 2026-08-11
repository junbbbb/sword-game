#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[2/3] 3D 투영 리페인트: 귀멸 대원복을 3D 좌표 기준으로 텍스처에 그린다.

기법: 각 삼각형을 UV 공간에 래스터라이즈하면서 무게중심 보간으로 픽셀별 3D 좌표를 얻는다.
그 3D 좌표로 "여긴 벨트 높이니까 흰색" 식의 도색을 한다. 군복 디테일(멜빵·타이·라펠 그림)은
원본 휘도를 아예 버리고 새로 그려 없앤다. 손·각반만 원본 붓질 휘도를 재활용.
"""
import json
import math
import os
import random
from PIL import Image, ImageFilter

SCR = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad"
ROOT = "/Users/lbj/Documents/gameproject"
DATA = json.load(open(os.path.join(SCR, "paint_data.json")))
ORIG = Image.open(os.path.join(SCR, "soldier_tex.png")).convert("RGB")
OUT = os.path.join(ROOT, "refpack/demon_slayer_tex.png")

S = 1024
orig = ORIG.resize((S, S), Image.LANCZOS)
op_ = orig.load()

# ---- 붓질 되살리기 ----
# (1) 원본의 "고주파 디테일"만 추출: 흐린 버전을 빼면 천 주름·짜임만 남고
#     멜빵·파우치 같은 큰 군용 형상은 사라진다.
gray = orig.convert("L")
blur = gray.filter(ImageFilter.GaussianBlur(radius=9))
gp_ = gray.load()
bp_ = blur.load()
# (2) 현재 지오메트리에서 구운 AO: 진짜 볼륨 음영(체형을 바꿨으므로 원본 명암은 안 맞음)
AO_PATH = os.path.join(SCR, "ao_bake.png")
ao_ = None
if os.path.exists(AO_PATH):
    ao_img = Image.open(AO_PATH).convert("L").resize((S, S), Image.LANCZOS)
    ao_ = ao_img.load()
    print("AO map loaded")
else:
    print("!! AO map missing - flat shading")

DETAIL_K = float(os.environ.get("PAINT_DETAIL", "2.1"))   # 천 디테일 강도
AO_K = float(os.environ.get("PAINT_AO", "0.85"))          # AO 강도


def fabric(px, py):
    """붓질 계수: 고주파 천 디테일 + AO 볼륨."""
    d = (gp_[px, py] - bp_[px, py]) / 255.0               # -0.4..0.4
    f = 1.0 + d * DETAIL_K
    if ao_ is not None:
        a = ao_[px, py] / 255.0
        f *= (1.0 - AO_K) + AO_K * (0.35 + 0.65 * a)
    return max(0.30, min(1.55, f))

lm = DATA["lm"]
hx0, hx1, hy0, hy1, hz0, hz1 = lm["head_box"]
head_w = hx1 - hx0
head_h = hz1 - hz0
head_cx = (hx0 + hx1) / 2
eye_z = lm["eye_z"]
belt0, belt1 = lm["belt"]
col0, col1 = lm["collar"]
btn_z0, btn_z1 = lm["buttons_z"]
lhand = lm["lhand"]
rhand = lm["rhand"]

# 팔레트
UNIFORM = (0x26, 0x2b, 0x38)
UNIFORM_D = (0x1a, 0x1e, 0x29)
TRIM = (0x3a, 0x40, 0x54)
PANTS = (0x1e, 0x22, 0x2e)
PANTS_D = (0x15, 0x18, 0x21)
BELT_C = (0xe9, 0xe4, 0xd4)
BELT_EDGE = (0xb9, 0xb2, 0x9c)
CUFF = (0xe6, 0xe1, 0xd3)
BTN = (0xd9, 0xb8, 0x78)
SKIN = (0xf0, 0xbe, 0x96)
SKIN_SH = (0xd8, 0x9c, 0x74)
HAIR = (0x33, 0x20, 0x2e)
BOOT = (0x24, 0x1b, 0x15)
WRAP = (0xe7, 0xe2, 0xd2)
EYE_LINE = (0x22, 0x10, 0x18)
IRIS = (0x7c, 0x2f, 0x3e)
IRIS_D = (0x47, 0x18, 0x25)
MOUTH = (0x8a, 0x4a, 0x3c)

rng = random.Random(7)
noise = [[rng.uniform(-0.03, 0.03) for _ in range(64)] for _ in range(64)]


def nz(u, v):
    return noise[int(v * 63) % 64][int(u * 63) % 64]


def lum_orig(px, py):
    r, g, b = op_[min(S - 1, max(0, px)), min(S - 1, max(0, py))]
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def shade(c, f):
    return (max(0, min(255, int(c[0] * f))), max(0, min(255, int(c[1] * f))),
            max(0, min(255, int(c[2] * f))))


def mix(a, b, t):
    return (int(a[0] * (1 - t) + b[0] * t), int(a[1] * (1 - t) + b[1] * t),
            int(a[2] * (1 - t) + b[2] * t))


def dist2(ax, ay, bx, by):
    return (ax - bx) ** 2 + (ay - by) ** 2


# ---- 픽셀 페인트 규칙 ----

def paint_jacket(x, y, z, u, v):
    c = UNIFORM
    f = 1.0 + nz(u, v)
    f *= 1.0 - 0.10 * max(0.0, min(1.0, (btn_z1 - z) / max(1.0, btn_z1 - belt1)))  # 아래로 갈수록 살짝 어둡게
    if y > 2.0:
        f *= 0.94                                    # 등판 미세 음영
    # 세움깃
    if col0 <= z:
        c = TRIM
        f = 1.0 + nz(u, v) * 0.5
        if z > col1 - 0.7:
            f *= 0.85                                # 깃 상단 라인
    # 앞섶 + 단추 (앞면만)
    if y < 0:
        if abs(x) < 0.55 and z < col0:
            c = shade(UNIFORM_D, 1.0)                # 플래킷 라인
        n_btn = 5
        for i in range(n_btn):
            bz = btn_z0 + (btn_z1 - btn_z0) * (i / (n_btn - 1))
            if dist2(x, z, 0, bz) < 0.92 ** 2:
                c = BTN
                f = 1.0 - 0.25 * ((z - bz) / 0.92)    # 단추 구형 음영
    # 벨트
    if belt0 <= z <= belt1:
        c = BELT_C
        f = 1.0 + nz(u, v) * 0.4
        if z > belt1 - 0.7 or z < belt0 + 0.7:
            c = BELT_EDGE
        if y < 0 and abs(x) < 1.6 and belt0 + 0.8 < z < belt1 - 0.8:
            c = (0xc9, 0xc9, 0xc9)                    # 버클
    return shade(c, f)


def paint_pants(x, y, z, u, v):
    c = PANTS
    f = 1.0 + nz(u, v)
    if z > belt0 - 4 and z > lm["pelvis_z"]:
        f *= 0.96
    if abs(x) < 0.7 and y < 0:
        c = PANTS_D                                   # 가운데 주름선
    return shade(c, f)


def paint_face(x, y, z, u, v):
    # 머리 로컬 정규화
    fx = (x - head_cx) / (head_w / 2)                 # -1..1
    fz = (z - eye_z) / head_h                         # 0=눈높이
    c = SKIN
    f = 1.0 + nz(u, v) * 0.5
    if y > 1.0:
        c = HAIR                                      # 뒤통수는 머리색
        return shade(c, 1.0 + nz(u, v) * 0.4)
    # 헤어라인 위 = 머리색
    if fz > 0.30:
        return shade(HAIR, 1.0 + nz(u, v) * 0.4)
    # 볼-턱 음영
    if fz < -0.34:
        f *= 0.93
    if abs(fx) > 0.72:
        f *= 0.94
    # 눈: 세로 타원 (양쪽 대칭, 미러 UV 안전)
    for sgn in (-1, 1):
        ex = sgn * 0.40                               # 눈 중심(정규화 x)
        dx = (fx - ex) / 0.195
        dz = fz / 0.150
        r2 = dx * dx + dz * dz
        if r2 < 1.0:
            if r2 > 0.80:
                return EYE_LINE                       # 테두리(얇게)
            if dz > 0.42:
                return EYE_LINE                       # 윗속눈썹 두껍게
            ix = (fx - ex) / 0.125
            iz = (fz + 0.02) / 0.118
            ir2 = ix * ix + iz * iz
            if ir2 < 1.0:
                if (ix + 0.35) ** 2 + (iz - 0.42) ** 2 < 0.14:
                    return (0xff, 0xff, 0xff)         # 하이라이트(위-안쪽)
                if ir2 > 0.60:
                    return IRIS_D
                if ix * ix + (iz + 0.12) ** 2 < 0.10:
                    return (0x1a, 0x0b, 0x10)         # 동공
                return IRIS
            return (0xf8, 0xf5, 0xee)                 # 흰자
        # 눈썹
        bx = (fx - ex) / 0.27
        bz = (fz - 0.245 - 0.06 * sgn * fx) / 0.05
        if bx * bx + bz * bz < 1.0:
            return HAIR
    # 입 (담백한 한 줄)
    if abs(fx) < 0.19 and -0.475 < fz < -0.428:
        return MOUTH
    # 코: 아주 옅은 음영 점
    if abs(fx) < 0.06 and -0.16 < fz < -0.05:
        f *= 0.96
    return shade(c, f)


def paint_hand(x, y, z, u, v, px, py):
    L = lum_orig(px, py)
    ref = 0.55
    f = 1.0 + (L / ref - 1.0) * 0.8
    f = max(0.55, min(1.06, f))
    return shade(SKIN, f)


def paint_sleeve(x, y, z, u, v):
    c = UNIFORM
    f = 1.0 + nz(u, v)
    # 커프스: 손목 근처
    for hj in (lhand, rhand):
        if dist2(x, z, hj[0], hj[2]) < 4.6 ** 2:
            c = CUFF
            f = 1.0 + nz(u, v) * 0.4
    return shade(c, f)


def paint_wrap(x, y, z, u, v, px, py):
    L = lum_orig(px, py)
    ref = 0.42
    f = 1.0 + (L / ref - 1.0) * 0.55
    f = max(0.6, min(1.10, f))
    return shade(WRAP, f)


def paint_foot(x, y, z, u, v):
    f = 1.0 + nz(u, v) * 0.6
    return shade(BOOT, f)


def pixel(region, x, y, z, u, v, px, py):
    if region in ("torso", "shoulder"):
        return paint_jacket(x, y, z, u, v)
    if region == "pelvis":
        if z >= belt0:
            return paint_jacket(x, y, z, u, v)
        return paint_pants(x, y, z, u, v)
    if region == "thigh":
        return paint_pants(x, y, z, u, v)
    if region in ("head", "neck"):
        return paint_face(x, y, z, u, v)
    if region == "hand":
        return paint_hand(x, y, z, u, v, px, py)
    if region in ("upperarm", "forearm"):
        return paint_sleeve(x, y, z, u, v)
    if region == "calf":
        return paint_wrap(x, y, z, u, v, px, py)
    if region == "foot":
        return paint_foot(x, y, z, u, v)
    return shade(UNIFORM, 1.0)


# ---- 삼각형 래스터라이즈 ----
img = Image.new("RGB", (S, S), (26, 28, 36))
pp = img.load()
painted = 0
for face in DATA["faces"]:
    (u0, v0), (u1, v1), (u2, v2) = face["uv"]
    p0 = (u0 * S, (1 - v0) * S)
    p1 = (u1 * S, (1 - v1) * S)
    p2 = (u2 * S, (1 - v2) * S)
    xyz = face["xyz"]
    reg = face["region"]
    minx = max(0, int(min(p0[0], p1[0], p2[0])) - 1)
    maxx = min(S - 1, int(max(p0[0], p1[0], p2[0])) + 1)
    miny = max(0, int(min(p0[1], p1[1], p2[1])) - 1)
    maxy = min(S - 1, int(max(p0[1], p1[1], p2[1])) + 1)
    den = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
    if abs(den) < 1e-9:
        continue
    for py in range(miny, maxy + 1):
        for px in range(minx, maxx + 1):
            cx, cy = px + 0.5, py + 0.5
            w0 = ((p1[1] - p2[1]) * (cx - p2[0]) + (p2[0] - p1[0]) * (cy - p2[1])) / den
            w1 = ((p2[1] - p0[1]) * (cx - p2[0]) + (p0[0] - p2[0]) * (cy - p2[1])) / den
            w2 = 1 - w0 - w1
            eps = -0.02
            if w0 < eps or w1 < eps or w2 < eps:
                continue
            x = xyz[0][0] * w0 + xyz[1][0] * w1 + xyz[2][0] * w2
            y = xyz[0][1] * w0 + xyz[1][1] * w1 + xyz[2][1] * w2
            z = xyz[0][2] * w0 + xyz[1][2] * w1 + xyz[2][2] * w2
            u = cx / S
            v = cy / S
            c = pixel(reg, x, y, z, u, v, px, py)
            if reg not in ("head", "neck"):        # 얼굴은 그림이라 붓질 변조 제외
                c = shade(c, fabric(px, py))
            pp[px, py] = c
            painted += 1

# 시접(bleed): 페인트 영역을 바깥으로 2px 확장
mask = Image.new("L", (S, S), 0)
mp = mask.load()
base = Image.new("RGB", (S, S), (26, 28, 36))
bp = base.load()
for yy in range(S):
    for xx in range(S):
        if pp[xx, yy] != (26, 28, 36):
            mp[xx, yy] = 255
grown = img.filter(ImageFilter.MaxFilter(5))
maskg = mask.filter(ImageFilter.MaxFilter(5))
out = Image.composite(img, Image.composite(grown, base, maskg), mask)
out.save(OUT)
print("painted px=%d -> %s" % (painted, OUT))
