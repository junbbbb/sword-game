# -*- coding: utf-8 -*-
"""던전 Meshy 구조물 9종을 **자리마다 조명을 구워** web/props/dg_*.glb 로 낸다.

실행:  blender -b -P blender/s41_dgprops.py
       DGP_ONLY=pillar_intact,altar blender -b -P blender/s41_dgprops.py   # 몇 종만
배치표: blender/dgprops_build.json  (blender/s40_dungeon1.py 가 굽는다)
원자재: incoming/meshy_dgprops/<이름>_3k.glb  +  같은 폴더 prep/dgp_<이름>.jpg
        (텍스처는 tools/dgprops_tex.py 가 먼저 굽는다)

왜 이 파일이 따로 있는가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① **level2.glb 에 못 합친다.** 예산이 5.00MiB 이고 지금 4.53 이다. 소품 9종은
   그 자체로 6MB 대라 합치면 두 배가 된다. web/props/ 는 따로 받는 자리다
   (초원 소품 11.37MB 이 이미 거기 있다. tools/build_deploy.py 가 props/ 하위
   glb 를 캐릭터 필터에서 빼 주므로 새 파일도 자동으로 배포에 실린다).
② **level2.json 을 한 바이트도 안 건드린다.** 콜라이더·nav 계약이다.

★★★ 이 파일의 존재 이유 — 던전은 조명을 정점색(COLOR_0)에 굽는다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
씬 조명은 캐릭터용 방향광 하나 + 반구광뿐이다. 던전의 횃불 38자루·특수광원 13개는
**실광원이 아니라 s40 이 정점에 구워 놓은 색**이다. Meshy 에셋에는 그게 없다.
그대로 넣으면 어둠 속 소품이 혼자 밝게 떠서 "스티커"가 된다
(16-저폴리진단이 지적한 최대 리스크).

그래서 여기서 **자리마다** 굽는다. 굽는 식은 s40 과 한 글자도 다르면 안 된다:

    정점색 = clip(lum(위치, 법선), AMB_MIN, 1) x TOP_MUL x 자체가림 x 접지어둠 x 개체변주

  · `lum()` 은 s40 4절의 그 함수다 — 아래 `lum()` 은 **복사본**이고,
    배치표에 실린 표본 160개로 **한 톨이라도 어긋나면 이 스크립트가 멈춘다**.
    (복사본 두 벌이 조용히 갈라지는 것을 막는 유일한 방법이다.)
  · `TOP_MUL` : 벽 계열(cut/trim/rubble) 팔레트는 **수직면 조도**로 풀렸다.
    같은 재질의 수평면은 윗면 조도(2.4배)를 받아 혼자 밝은 판이 된다. s40 의
    add_quad 가 하는 그 보정을 여기서도 한다.
  · `자체가림` : 소품 제 몸이 만드는 그늘(BVH 레이캐스트 24방향). **평균을 1 로
    되돌려서** 대비만 남긴다 — 안 그러면 소품이 통째로 어두워져 색계약이 깨진다
    (tools/paint_prop_ao.py 의 ③ 과 같은 이유).
  · `접지어둠` : s40 의 contact_ao. 벽 밑에 붙은 소품이 바닥과 같은 밝기면 뜬다.

★색 — 텍스처는 한 화소도 안 만진다 (오너 원칙: 원본 충실 · 재칠 금지)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s40 의 mat_tex 와 **완전히 같은 계약**으로 baseColorFactor 하나만 푼다.
    화면색 = baseColorFactor x 텍스처 x 정점색
    곱수 = 목표색(PAL) / 텍스처평균 / 정점색평균     (hue_keep 0.88 만큼 스칼라 쪽)
`hue_keep` 이 0.88 이라 사실상 **밝기만** 맞추고 Meshy 원본의 색기(이끼 초록,
따뜻한 회록)는 그대로 산다. 실측 채널 편차는 아래 [곱수] 줄이 매번 찍는다.
★텍스처 평균은 **UV 면적 가중**으로 잰다. 이미지 전체 평균으로 재면 아틀라스의
  빈 검은 자리가 섞여 실제보다 40% 어둡게 나오고, 그만큼 곱수가 부풀어 소품이
  혼자 밝아진다(실측: 기둥 전체평균 0.040 vs 면적가중 0.048).

★삼각형 — 히어로는 원본 그대로, 반복 부재만 줄인다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
16-저폴리진단이 잰 기준 밀도는 **Meshy 소품 115 tris/m²** (던전 절차 기둥은 19).
1m 짜리 잔해의 겉넓이가 2.5m² 이므로 그 기준으로는 290 삼각형이면 된다. 3,012 을
그대로 42벌 깔면 그것만으로 12만 삼각형이라, 화면에서 60px 인 부재는 줄인다.
줄인 뒤에도 기준 밀도의 두 배 위다(아래 [메시] 줄이 tris/m² 를 찍는다).

★배치를 왜 여기서 안 적는가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
자리는 s40 이 안다(방·통로·횃불·콜라이더가 전부 거기 있다). 여기서 다시 적으면
두 파일이 갈라진다. 이 파일은 **원자재를 다루는 법**만 안다.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.read_homefile(use_empty=True)

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming", "meshy_dgprops")
PREP = os.path.join(SRC, "prep")
OUT = os.path.join(ROOT, "web", "props")
BUILD = os.path.join(ROOT, "blender", "dgprops_build.json")

with open(BUILD) as f:
    B = json.load(f)

# ═════════════════════════════════════════════════════════════
# 1) 조명 모델 — s40_dungeon1.py 4절의 **복사본**. 아래 자기검증이 지킨다
# ═════════════════════════════════════════════════════════════
AMB = np.array(B["amb"], np.float64)
AMB_MIN = B["ambMin"]
TORCH_RANGE = B["torchRange"]
NL_FLOOR = B["nlFloor"]
NEAR_R, NEAR_P = B["near"]["r"], B["near"]["p"]
NEAR_RANGE, NEAR_NL = B["near"]["range"], B["near"]["nl"]
HFALL_Y0, HFALL_SPAN, HFALL_MIN = B["hfall"]["y0"], B["hfall"]["span"], B["hfall"]["min"]
CONTACT_AO, CONTACT_R = B["contact"]["ao"], B["contact"]["r"]
CONTACT_AO2, CONTACT_R2 = B["contact"]["ao2"], B["contact"]["r2"]
CELL, GRID, HALF = B["cell"], B["grid"], B["half"]
FLOOR_Y = B["floorY"]
HUE_KEEP = B["hueKeep"]
# ★TOP_MUL 은 배치표에 없다(s40 의 Buf.wallfam 쪽 상수다). 값이 갈리면 곧바로
#   윗면이 밝아져 눈에 띄므로 여기 적고 아래 [곱수] 줄이 결과를 찍는다.
TOP_MUL = 0.46
WALLFAM = {"cut", "trim", "rubble"}      # 수직면 조도로 푼 재질 = 윗면을 눌러야 한다

LIGHTS = [(l[0], l[1], l[2], l[3], l[4], np.array(l[5:8], np.float64), l[8])
          for l in B["lights"]]
BLOCKED = [row for row in B["blocked"]]


def height_fall(y):
    if y <= HFALL_Y0:
        return 1.0
    t = min(1.0, (y - HFALL_Y0) / HFALL_SPAN)
    t = t * t * (3.0 - 2.0 * t)
    return 1.0 - (1.0 - HFALL_MIN) * t


def lum(gx, gz, y, moss=0.0, nrm=None):
    """★s40_dungeon1.py 의 lum() 과 **같아야 한다**(자기검증이 확인한다)."""
    acc = AMB.copy()
    for (lx, lz, ly, rad, power, rgb, near) in LIGHTS:
        dx = gx - lx
        dz = gz - lz
        dy = y - ly
        d2 = dx * dx + dz * dz + dy * dy * 0.55
        ndl = None
        if nrm is not None:
            dd = math.sqrt(dx * dx + dz * dz + (y - ly) ** 2) + 1e-4
            ndl = (nrm[0] * (-dx) + nrm[1] * (ly - y) + nrm[2] * (-dz)) / dd
        rng = rad * TORCH_RANGE
        if d2 < rng * rng:
            w = 1.0 - math.sqrt(d2) / rng
            f = power * (w ** 2.7) / (1.0 + d2 / (rad * rad))
            if ndl is not None:
                f *= NL_FLOOR + (1.0 - NL_FLOOR) * max(0.0, ndl)
            acc = acc + rgb * f
        if near > 0.0:
            nrng = NEAR_R * NEAR_RANGE
            dn2 = dx * dx + dz * dz + dy * dy
            if dn2 < nrng * nrng:
                wn = 1.0 - math.sqrt(dn2) / nrng
                fn = near * NEAR_P * (wn ** 3.0) / (1.0 + dn2 / (NEAR_R * NEAR_R))
                if ndl is not None:
                    fn *= NEAR_NL + (1.0 - NEAR_NL) * max(0.0, ndl)
                acc = acc + rgb * fn
    acc = acc * height_fall(y)
    if moss > 0.0:
        acc = acc + np.array((0.06, 0.16, 0.04)) * moss
    return np.clip(acc, AMB_MIN, 1.0)


def cell_of(gx, gz):
    c = int((gx + HALF) / CELL)
    r = int((gz + HALF) / CELL)
    return (min(GRID - 1, max(0, c)), min(GRID - 1, max(0, r)))


def blocked(c, r):
    if c < 0 or r < 0 or c >= GRID or r >= GRID:
        return True
    return BLOCKED[r][c] == "#"


def wall_dist(gx, gz):
    c, r = cell_of(gx, gz)
    best = 9.0
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if not blocked(c + dc, r + dr):
                continue
            cx = -HALF + (c + dc + 0.5) * CELL
            cz = -HALF + (r + dr + 0.5) * CELL
            dx = max(0.0, abs(gx - cx) - CELL * 0.5)
            dz = max(0.0, abs(gz - cz) - CELL * 0.5)
            best = min(best, math.hypot(dx, dz))
    return best


def contact_ao(gx, gz):
    d = wall_dist(gx, gz)
    t = max(0.0, 1.0 - d / CONTACT_R)
    t = t * t * (3.0 - 2.0 * t)
    t2 = max(0.0, 1.0 - d / CONTACT_R2)
    t2 = t2 * t2 * (3.0 - 2.0 * t2)
    return (1.0 - CONTACT_AO * t) * (1.0 - CONTACT_AO2 * t2)


# ── ★자기검증. s40 이 같은 함수로 구운 표본과 대조한다 ──
_bad = 0
_worst = 0.0
for s in B["lumCheck"]:
    got = lum(s["p"][0], s["p"][1], s["p"][2], nrm=s["n"])
    d = float(np.abs(got - np.array(s["c"])).max())
    _worst = max(_worst, d)
    if d > 1e-6:
        _bad += 1
if _bad:
    raise SystemExit(
        "[치명] lum() 복사본이 s40 과 갈렸다 — 표본 %d/%d 불일치(최대 %.3g).\n"
        "  s40_dungeon1.py 4절을 그대로 다시 옮겨라. 안 그러면 소품만 조명이 다르다."
        % (_bad, len(B["lumCheck"]), _worst))
print("[자기검증] lum() 표본 %d개 일치 (최대 오차 %.2g)" % (len(B["lumCheck"]), _worst))


# ═════════════════════════════════════════════════════════════
# 2) 종류별 손잡이
# ═════════════════════════════════════════════════════════════
# tris  : 줄일 목표 삼각형(None 이면 원본 그대로). 화면 크기로 가른다
# ao    : (세기, 감마, 하한) — tools/paint_prop_ao.py 의 SPEC 과 같은 뜻
# cast  : 그림자를 던지는가
#   ★던전에서 그림자는 **위험한 손잡이**다. 해가 없어 방향광이 거의 누워 있고,
#     키 큰 물건이 던지면 바닥에 대각선 슬래브가 눕는다(15차: 아치 그림자가
#     캐릭터 휘도를 15분의 1로 만들었다 - 그래서 벽·트림은 castShadow=false 다).
#     발치에 있는 것(기둥 밑동·잔해·화로·제단)만 던진다 — 짧아서 접지로 읽힌다.
#     벽에 붙거나(아치·모서리돌) 벽 위에 얹힌 것(갓돌)은 안 던진다.
KIND = {
    "pillar_intact": dict(tris=None, ao=(0.80, 1.15, 0.34), cast=True),
    "pillar_broken": dict(tris=None, ao=(0.80, 1.15, 0.34), cast=True),
    "arch_gate":     dict(tris=None, ao=(0.75, 1.20, 0.36), cast=False),
    "altar":         dict(tris=None, ao=(0.78, 1.15, 0.36), cast=True),
    "brazier":       dict(tris=900,  ao=(0.80, 1.15, 0.32), cast=True),
    "rubble_large":  dict(tris=1100, ao=(0.85, 1.10, 0.30), cast=True),
    "rubble_small":  dict(tris=420,  ao=(0.85, 1.10, 0.30), cast=True),
    "coping_chunk":  dict(tris=380,  ao=(0.75, 1.20, 0.36), cast=False),
    "quoin_corner":  dict(tris=900,  ao=(0.75, 1.20, 0.36), cast=False),
}
AO_RAYS = 24            # 반구 표본 수. 24 면 3천 정점에 7만 광선이라 1초 안이다
AO_DIST = 0.42          # 가림을 보는 거리(원자재 단위. 긴 축이 1.90 이다)
GROUND_AO = 0.42        # 바닥에 닿는 자리의 어둠(제 몸 밑은 바닥이 가린다)
GROUND_H = 0.34         # 그 어둠이 사라지는 높이(원자재 단위)
VARY_V = 0.10           # 개체마다 밝기 ±5%
VARY_W = 0.06           # 개체마다 색온도 ±3%

ONLY = [s for s in os.environ.get("DGP_ONLY", "").split(",") if s]


# ═════════════════════════════════════════════════════════════
# 3) 색 계약 (s40 의 mat_tex 와 같은 식)
# ═════════════════════════════════════════════════════════════
def srgb_to_linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    c = int(h, 16)
    return np.array([srgb_to_linear(((c >> 16) & 255) / 255.0),
                     srgb_to_linear(((c >> 8) & 255) / 255.0),
                     srgb_to_linear((c & 255) / 255.0)], np.float64)


def lum3(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def solve_factor(target_hex, tile_lin, shade):
    """s40 mat_tex 와 같은 곱수. hue_keep 만큼 스칼라 쪽으로 간다.

    ★★여기서 s40 과 갈리는 것이 하나 있다 — **곱수가 1 을 넘는다**(2.7~8.5).
      s40 의 타일(dg_block)은 선형평균 0.71 짜리 **거의 흰** 손그림이라 작은 곱수로
      목표에 닿는다. Meshy 텍스처는 그림자까지 구워진 **어두운** 원자재라(0.026~0.053)
      같은 목표에 닿으려면 곱수가 1 을 넘어야 한다.
      glTF `baseColorFactor` 는 [0,1] 이라 그 위를 못 싣는다. 그래서
        glb  = clamp(곱수, 0, 1)
        나머지 = dg_manifest.json 의 `gain` -> web/level.js 가 material.color 에 곱한다
      (three.js 의 diffuse 는 1 을 넘어도 된다. 텍스처 화소를 밝히는 대신 이렇게 하는
       이유는 오너 원칙 "소품 색은 원본 충실 · 재칠 금지" 다 — 원자재 jpg 는 크기만
       바뀌고 화소는 한 톨도 안 바뀐다. 8비트로 굽어 놓으면 되돌릴 수도 없다.)
    ★1 을 넘긴 몫이 텍스처의 상위 1% 화소를 알베도 1 위로 올린다(실측 p99 0.37~1.43).
      그 화소는 Meshy 가 구워 둔 하이라이트 줄기라, 어두운 던전에서 **횃불을 받은
      돌의 반짝임**으로 읽힌다. 평균은 정확히 계약값에 앉는다."""
    tgt = hex_lin(target_hex)
    den = [max(1e-6, float(tile_lin[i]) * float(shade[i])) for i in range(3)]
    per = [tgt[i] / den[i] for i in range(3)]
    sca = lum3(tgt) / max(1e-6, lum3(den))
    raw = [per[i] * (1.0 - HUE_KEEP) + sca * HUE_KEEP for i in range(3)]
    fac = [min(1.0, x) for x in raw]
    gain = [raw[i] / max(fac[i], 1e-6) for i in range(3)]
    return fac, gain, max(raw)


# ═════════════════════════════════════════════════════════════
# 4) 원자재 다루기
# ═════════════════════════════════════════════════════════════
def import_kind(kind):
    """Meshy glb 한 벌을 들여와 **바닥 y=0 · xz 중심 0** 으로 앉힌다.

    ★크기는 안 건드린다. 배치표의 `scale` 이 원자재 치수(긴 축 1.90)에 그대로
      곱해지는 값이라, 여기서 정규화하면 s40 의 계산이 통째로 어긋난다.
    ★glTF 임포터가 Y-up -> Z-up 으로 돌려 놓는다. 그래서 들어온 메시의 **높이축은
      블렌더 Z** 이고, 그건 s40 의 bpos(gx,gz,y)=(gx,-gz,y) 규약과 이미 같다."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, kind + "_3k.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    assert len(meshes) == 1, "%s: 메시가 %d개다" % (kind, len(meshes))
    ob = meshes[0]
    # 부모(빈 오브젝트)의 회전까지 정점에 굽는다
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    ob.matrix_world = ob.matrix_world      # noqa: 명시 - 아래 transform_apply 가 읽는다
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in new:
        if o is not ob:
            bpy.data.objects.remove(o, do_unlink=True)
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    off = np.array([(co[:, 0].min() + co[:, 0].max()) * 0.5,
                    (co[:, 1].min() + co[:, 1].max()) * 0.5,
                    co[:, 2].min()])
    co -= off
    me.vertices.foreach_set("co", co.ravel())
    me.update()
    return ob


def decimate(ob, target):
    if target is None:
        return
    n = len(ob.data.polygons)
    if n <= target:
        return
    bpy.context.view_layer.objects.active = ob
    m = ob.modifiers.new("dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = target / float(n)
    m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=m.name)


def self_ao(ob, spec):
    """제 몸이 만드는 그늘. 반구 24방향 레이캐스트 + 바닥판.

    ★평균을 1 로 되돌린다(면적 가중). 안 되돌리면 소품 전체가 20~30% 어두워져
      아래 색계약(곱수)이 그만큼 부풀고, 결국 화면에서 원래 밝기로 되돌아온다 =
      가림은 사라지고 바이트만 쓴 꼴이 된다. paint_prop_ao.py ③ 과 같은 이유."""
    me = ob.data
    verts = [v.co.copy() for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    bvh = BVHTree.FromPolygons(verts, polys)
    # 결정적 반구 표본(피보나치). 난수를 쓰면 다시 구울 때마다 그늘이 흔들린다
    ga = math.pi * (3.0 - math.sqrt(5.0))
    dirs = []
    for i in range(AO_RAYS):
        z = 1.0 - (i + 0.5) / AO_RAYS
        r = math.sqrt(max(0.0, 1.0 - z * z))
        a = ga * i
        dirs.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
    nrm = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("normal", nrm)
    nrm = nrm.reshape(-1, 3)
    ao = np.ones(len(me.vertices), np.float64)
    for i, v in enumerate(me.vertices):
        n = Vector(nrm[i])
        if n.length < 1e-6:
            continue
        n.normalize()
        # 법선을 +Z 로 보내는 회전(반구를 법선 쪽으로 돌린다)
        rot = Vector((0, 0, 1)).rotation_difference(n).to_matrix()
        o = v.co + n * 1e-4
        hit = 0
        for d in dirs:
            wd = rot @ d
            if bvh.ray_cast(o, wd, AO_DIST)[0] is not None:
                hit += 1
        ao[i] = 1.0 - hit / float(AO_RAYS)
    amt, gam, floor = spec
    k = 1.0 - amt * (1.0 - np.clip(ao, 0, 1) ** gam)
    k = np.clip(k, floor, 1.0)
    # 바닥판(제 몸 밑을 바닥이 가린다). 원점이 바닥이라 z 로 바로 잰다
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    z = co.reshape(-1, 3)[:, 2]
    t = np.clip(1.0 - z / GROUND_H, 0.0, 1.0)
    k = k * (1.0 - GROUND_AO * (t * t * (3.0 - 2.0 * t)))
    # 면적 가중 평균을 1 로
    w = np.zeros(len(me.vertices), np.float64)
    for p in me.polygons:
        a = p.area / len(p.vertices)
        for vi in p.vertices:
            w[vi] += a
    m = float((k * w).sum() / max(w.sum(), 1e-9))
    return k / max(m, 1e-6), m


def tex_area_mean(ob, img):
    """UV 면적 가중 텍스처 평균(선형). ★이미지 전체 평균으로 재면 아틀라스의
    빈 검은 자리가 섞여 40% 어둡게 나온다 = 곱수가 그만큼 부푼다."""
    w, h = img.size
    px = np.array(img.pixels[:], np.float64).reshape(h, w, 4)[:, :, :3]
    # ★★`image.pixels` 는 **저장된 값 그대로**(8비트 jpg 면 sRGB)를 돌려준다.
    #   colorspace 설정을 푼 선형값이 아니다. 여기서 안 풀면 평균이 5.8배 밝게
    #   잡히고(실측 제단 0.192 vs 진짜 0.033) 곱수가 그만큼 작아져 소품이
    #   화면에서 통째로 어두워진다. **화소마다** 풀어야 한다(평균을 먼저 내고
    #   풀면 감마 때문에 또 다르다).
    px = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
    me = ob.data
    uvl = me.uv_layers.active.data
    tot = np.zeros(3)
    aw = 0.0
    for p in me.polygons:
        u = np.mean([uvl[li].uv[0] for li in p.loop_indices])
        v = np.mean([uvl[li].uv[1] for li in p.loop_indices])
        x = min(w - 1, max(0, int(u * w)))
        y = min(h - 1, max(0, int(v * h)))
        tot += px[y, x] * p.area
        aw += p.area
    return tot / max(aw, 1e-9)


# ═════════════════════════════════════════════════════════════
# 5) 굽기
# ═════════════════════════════════════════════════════════════
PROPS = {}
for p in B["props"]:
    PROPS.setdefault(p["kind"], []).append(p)

os.makedirs(OUT, exist_ok=True)
manifest = []
total_bytes = 0
total_tris = 0
print("\n[메시]")
for kind, places in sorted(PROPS.items()):
    if ONLY and kind not in ONLY:
        continue
    spec = KIND[kind]
    base = import_kind(kind)
    decimate(base, spec["tris"])
    ao_k, ao_mean = self_ao(base, spec["ao"])
    me = base.data
    nv = len(me.vertices)
    co0 = np.empty(nv * 3, np.float64)
    me.vertices.foreach_get("co", co0)
    co0 = co0.reshape(-1, 3)
    nrm0 = np.empty(nv * 3, np.float64)
    me.vertices.foreach_get("normal", nrm0)
    nrm0 = nrm0.reshape(-1, 3)

    # ── 텍스처 · 재질 ──
    jpg = os.path.join(PREP, "dgp_%s.jpg" % kind)
    assert os.path.exists(jpg), "텍스처가 없다. python3 tools/dgprops_tex.py 를 먼저 돌려라"
    img = bpy.data.images.load(jpg, check_existing=True)
    tile_lin = tex_area_mean(base, img)

    # ── 자리마다 복제 + 정점색 굽기 ──
    wallfam = places[0]["albedo"] in WALLFAM
    copies = []
    shade_sum = np.zeros(3)
    shade_w = 0.0
    for pi, pl in enumerate(places):
        ob = base.copy()
        ob.data = me.copy()
        bpy.context.scene.collection.objects.link(ob)
        s = pl["scale"]
        M = (Matrix.Translation(Vector((pl["x"], -pl["z"], pl["y"])))
             @ Euler((pl["pitch"], 0.0, pl["yaw"]), "XYZ").to_matrix().to_4x4()
             @ Matrix.Translation(Vector((pl["pre"][0], pl["pre"][1], pl["pre"][2])))
             @ Matrix.Diagonal(Vector((s, s, s, 1.0))))
        ob.matrix_world = M
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        m2 = ob.data
        co = np.empty(nv * 3, np.float64)
        m2.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        nn = np.empty(nv * 3, np.float64)
        m2.vertices.foreach_get("normal", nn)
        nn = nn.reshape(-1, 3)
        # 개체 변주(같은 소품이 여러 벌 서 있을 때 복제 티를 죽인다).
        # ★난수를 안 쓴다 — 다시 구울 때마다 달라지면 A/B 가 무의미하다
        hh = math.sin(pl["x"] * 12.9898 + pl["z"] * 78.233 + pi * 37.719) * 43758.5453
        hh = hh - math.floor(hh)
        fv = 1.0 + (hh - 0.5) * VARY_V
        fw = 1.0 + (((hh * 7.13) % 1.0) - 0.5) * VARY_W
        cols = np.empty((nv, 4), np.float64)
        for i in range(nv):
            bx, by, bz = co[i]
            gx, gz, gy = bx, -by, bz
            n = (nn[i][0], nn[i][2], -nn[i][1])      # 블렌더 -> 게임 좌표 법선
            c = lum(gx, gz, gy, nrm=n)
            if wallfam and abs(n[1]) > 0.70:
                c = c * TOP_MUL
            c = c * ao_k[i] * contact_ao(gx, gz) * fv
            if wallfam:
                c = c * np.array((fw, 1.0, 2.0 - fw))
            cols[i, :3] = np.clip(c, AMB_MIN * 0.80, 1.0)
            cols[i, 3] = 1.0
        # 면적 가중 정점색 평균(곱수 계약의 분모)
        for p2 in m2.polygons:
            a = p2.area / len(p2.vertices)
            for vi in p2.vertices:
                shade_sum += cols[vi, :3] * a
                shade_w += a
        col = m2.color_attributes.new(name="Shade", type="FLOAT_COLOR", domain="POINT")
        col.data.foreach_set("color", cols.ravel())
        for _at in ("active_color_name", "default_color_name"):
            if hasattr(m2.color_attributes, _at):
                setattr(m2.color_attributes, _at, col.name)
        copies.append(ob)

    shade = shade_sum / max(shade_w, 1e-9)
    matname = B["albedoMat"][places[0]["albedo"]]
    target_hex = B["materials"][matname]["hex"]
    k, gain, raw_max = solve_factor(target_hex, tile_lin, shade)
    mat = bpy.data.materials.new("MAT_DGP_" + kind.upper())
    mat.use_nodes = True
    nt = mat.node_tree
    for n_ in list(nt.nodes):
        if n_.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n_)
    outn = [n_ for n_ in nt.nodes if n_.type == "OUTPUT_MATERIAL"][0]
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "REPEAT"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (k[0], k[1], k[2], 1.0)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])

    # ── 한 덩어리로 합친다(드로우콜 1) ──
    bpy.ops.object.select_all(action="DESELECT")
    for ob in copies:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    if len(copies) > 1:
        bpy.ops.object.join()
    merged = bpy.context.view_layer.objects.active
    merged.name = ("COL_DGP_" if spec["cast"] else "DECO_DGP_") + kind.upper()
    merged.data.materials.clear()
    merged.data.materials.append(mat)
    # ★★평면 셰이딩(use_smooth=False)을 **강제하지 않는다.** s40 의 절차 메시는
    #   저폴리 상자라 각져야 맞지만, 여기 원자재는 3.1M 조각을 3K 로 리메시한
    #   것이라 법선이 이미 부드럽다. 강제로 각지게 하면
    #     (가) 정점이 3,210 -> 8,282 로 **2.6배** 튄다(면마다 정점을 쪼갠다)
    #     (나) 16-저폴리진단이 "Meshy 가 이기는 축"이라고 지목한 바로 그것
    #          (계단이 잦고 낮다)을 우리 손으로 되돌린다
    #   원자재가 갖고 온 셰이딩을 그대로 쓴다.
    bpy.data.objects.remove(base, do_unlink=True)

    # ── 내보내기 ──
    path = os.path.join(OUT, "dg_%s.glb" % kind)
    bpy.ops.object.select_all(action="DESELECT")
    merged.select_set(True)
    bpy.context.view_layer.objects.active = merged
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        export_animations=False, export_yup=True, export_apply=True,
        export_vertex_color="ACTIVE", export_image_format="AUTO",
        export_image_quality=88, export_jpeg_quality=88)
    sz = os.path.getsize(path)
    tris = len(merged.data.polygons)
    area = sum(p2.area for p2 in merged.data.polygons)
    total_bytes += sz
    total_tris += tris
    print("  %-14s %2d자리 · 삼각형 %5d (한 벌 %4d · %5.0f tris/m²) · 정점 %6d · "
          "%5.0fKB" % (kind, len(places), tris, tris // len(places),
                       tris / max(area, 1e-6), len(merged.data.vertices), sz / 1024))
    print("      곱수 %.3f %.3f %.3f x 게인 %.2f %.2f %.2f · 텍스처평균 "
          "%.4f %.4f %.4f · 정점색평균 %.3f %.3f %.3f · 목표 #%s · 자체가림평균 %.3f"
          % (k[0], k[1], k[2], gain[0], gain[1], gain[2],
             tile_lin[0], tile_lin[1], tile_lin[2],
             shade[0], shade[1], shade[2], target_hex, ao_mean))
    manifest.append({"kind": kind, "file": "dg_%s.glb" % kind, "n": len(places),
                     "cast": bool(spec["cast"]), "tris": tris,
                     "mesh": merged.name,
                     "gain": [round(g, 5) for g in gain]})
    bpy.data.objects.remove(merged, do_unlink=True)

if not ONLY:
    with open(os.path.join(OUT, "dg_manifest.json"), "w") as f:
        json.dump({
            "note": ("던전(level2) 전용 Meshy 구조물. web/level.js 가 이 목록을 읽어 "
                     "월드 좌표 그대로 씬에 얹는다. 정점색(COLOR_0)에 s40 의 횃불 "
                     "조명이 이미 구워져 있으므로 런타임 조명 계산이 없다. "
                     "cast=false 는 그림자를 안 던진다(벽·트림과 같은 이유). "
                     "gain 은 material.color 에 **곱하는** 값이다 - glTF "
                     "baseColorFactor 가 [0,1] 이라 못 실은 몫이고, 안 곱하면 "
                     "소품이 계약값보다 3~8배 어둡게 뜬다."),
            "generatedBy": "blender/s41_dgprops.py",
            "items": manifest,
        }, f, ensure_ascii=False, indent=1)

print("\n[합계] %d종 · 삼각형 %d · %.2f MB (초원 소품 11.37MB 이 비교 기준)"
      % (len(manifest), total_tris, total_bytes / 1048576))
print("->", OUT)
