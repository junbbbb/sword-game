# -*- coding: utf-8 -*-
"""알몸 basic2 에 오너가 준 옷(incoming/basic_cloth.glb)을 입혀 web/basic2.glb 를 만든다.

    blender -b -P blender/s33_basic2_cloth.py
    -> web/basic2.glb   (칼 7자루 + 클립 7종은 그대로, 메시 cloth1 이 하나 늘어난다)

전체 공정 다섯 줄(이 순서대로 다시 돌리면 언제든 재현된다. 2026-08-11 실행 기록)
  1~4 는 s31_basic2_body.py 헤더에 있는 그대로다. 이 스크립트가 5번이다.

    # 4) 까지 돌면 web/basic2.glb 는 **알몸**이다. 옷은 여기서 입힌다.
    # 5) 옷
    BODY_GLB=web/basic2.glb OUT_GLB=web/basic2.glb \
      OUTDIR=renders/history/v98_wave12/cloth blender -b -P blender/s33_basic2_cloth.py

★왜 s15_hero.py 를 그냥 못 쓰나
  s15 는 **옷과 검을 한꺼번에** 입혀 hero.glb 를 만든다. 그 검은 basic_sword.glb
  한 자루이고 재질 이름이 게임의 발광 규칙(bd_/bv_/ht_/sp_)을 안 따른다. 지금
  basic2 는 s31 이 kensa 에서 옮겨 온 칼 **7자루**를 물고 있고(원소 전환·칼날
  발광·궤적이 전부 거기 걸려 있다), s15 를 돌리면 그게 통째로 날아간다.
  그래서 s15 에서 **옷 공정만** 떼어 왔다. 검 관련 절(s15 [3])은 통째로 뺐다.
  옷 자체의 실측·수치는 s15 것을 그대로 물려받는다(아래 [옷 치수] 주석).

★[옷 치수] 이 옷은 이미 이 몸에 맞게 재어 둔 것이다(s15 판정 기록)
  받은 물건은 '옷 한 벌'이 아니라 **허리 벨트 + 모피 로인클로스 + 어깨 가죽끈**이다.
  basic / basic2 둘 다에 얹어 재 본 결과 basic2 쪽이 맞다고 판정됐다:
      벨트 둘레가 요구하는 배율 S_b 0.3872 / 어깨끈이 요구하는 최소배율 S_s 0.3988
      -> 두 치수의 어긋남이 3.0% (basic 은 12.0%)
  그래서 배치 손잡이(HIP_F·CLOTH_S)는 s15 가 쓰던 값을 기본값으로 그대로 둔다.
  몸(char1)의 레스트 지오메트리는 s31/s24/s27 을 거쳐도 안 변한다(그 셋은 칼과
  애니메이션만 건드린다). 즉 s15 때 잰 치수가 지금도 유효하다.

★공정 (s15 [2] 절의 순서를 그대로 따른다)
  1) 옷 정점 용접  glTF 는 UV 이음매에서 정점을 쪼갠다. 섬 판정·웨이트 전이 전에 붙인다
  2) 벨트 섬을 찾아 허리 높이(HIP_F)에 앉히고 벨트 둘레에 맞춰 통째로 배율
  3) conform  몸을 뚫는 옷 정점을 몸 표면 **바깥**으로 민다
     ("가려지는 몸 면을 지운다" 는 못 쓴다. 이 옷은 몸을 덮지 않아 지우면 구멍이 난다)
  4) 웨이트 전이  옷엔 뼈가 없다. 몸 정점그룹을 옷으로 옮기고 스무딩·가랑이 보정·4개 자르기
  5) 재질  MeshToonMaterial 계약(베이스컬러만)에 맞춰 normal/mr/emissive 링크를 끊는다

★함정 (하나라도 밟으면 조용히 망가진다)
  1) fps: 임포트 **전에** 30 고정
  2) 임포트 순서: **몸을 먼저**. 나중에 읽으면 이름이 .001 로 밀려 그대로 나간다
  3) 스키닝은 REST 에서 굽는다. 포즈 상태로 재면 애니에서 어긋난다
  4) Icosphere: glTF 임포터가 뼈 표시용으로 만드는 반지름 1 구. 안 지우면 게임이
     전 메시로 박스를 재므로 키가 망가진다
  5) 옷 이름은 **cloth1**. SW_/SH_ 로 시작하면 게임이 무기·방패로 본다
  6) 재질 이름 앞자리(bd_/bv_/ht_/sp_)는 게임의 칼날 발광 규칙이다. 옷 재질 이름을
     그 접두어로 바꾸지 말 것
  7) 액션에 use_fake_user 를 안 켜면 export 에서 조용히 빠진다
  8) 게임 키 계산은 SW_/SH_ 를 뺀 **모든** 메시를 합친 박스다. 옷이 몸 박스를 넘으면
     키 정규화가 흔들린다. 아래 [키] 절에서 몸만/몸+옷 박스를 찍어 검산한다

손잡이(환경변수)
  BODY_GLB   알몸 몸        기본 web/basic2.glb  (이미 옷이 있으면 멈춘다)
  CLOTH_GLB  옷            기본 incoming/basic_cloth.glb
  OUT_GLB    결과           기본 web/basic2.glb  (임시파일에 쓰고 os.replace 로 교체)
  HIP_F      벨트 높이 z/키  기본 0.560
  CLOTH_S    벨트 최소배율에 곱할 여유  기본 1.035
  CONFORM_M / CONFORM_HEM   벨트선 / 치마밑단 여유 간격(m)  기본 0.004 / 0.028
  LEG_MAX    치마 밑단이 다리를 따라가는 강도  기본 0.85
  SMOOTH_N   웨이트 라플라시안 스무딩 횟수     기본 14
  PRUNE      웨이트 가지치기 문턱             기본 0.02
  VERIFY     1(기본) 전 클립 찢어짐·뚫림 검사 / 0 생략
  RENDER     1(기본) 검산 렌더 / 0 생략
  OUTDIR     렌더 폴더  기본 renders/history/v98_wave12/cloth
  TEX_SIZE / TEX_FORMAT / TEX_QUALITY   기본 2048 / AUTO(원본 포맷 유지) / 90
"""
import bpy
import bmesh
import os
import math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")
INC = os.path.join(ROOT, "incoming")


def _p(v):
    """상대경로로 줘도 프로젝트 루트 기준으로 읽히게 한다(blender 의 cwd 를 안 믿는다)."""
    if not v:
        return None
    return v if os.path.isabs(v) else os.path.join(ROOT, v)


BODY_GLB = _p(os.environ.get("BODY_GLB")) or os.path.join(WEB, "basic2.glb")
CLOTH_GLB = _p(os.environ.get("CLOTH_GLB")) or os.path.join(INC, "basic_cloth.glb")
OUT_GLB = _p(os.environ.get("OUT_GLB")) or os.path.join(WEB, "basic2.glb")

HIP_F = float(os.environ.get("HIP_F", "0.560"))       # 벨트를 앉힐 높이 z/키
CLOTH_S = float(os.environ.get("CLOTH_S", "1.035"))   # 벨트 최소배율에 곱할 여유
CONFORM_M = float(os.environ.get("CONFORM_M", "0.004"))
CONFORM_HEM = float(os.environ.get("CONFORM_HEM", "0.028"))
LEG_MAX = float(os.environ.get("LEG_MAX", "0.85"))
SMOOTH_N = int(os.environ.get("SMOOTH_N", "14"))
PRUNE = float(os.environ.get("PRUNE", "0.02"))
VERIFY = os.environ.get("VERIFY", "1") == "1"
RENDER = os.environ.get("RENDER", "1") == "1"
OUTDIR = _p(os.environ.get("OUTDIR")) or os.path.join(
    ROOT, "renders", "history", "v98_wave12", "cloth")
TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_FORMAT = os.environ.get("TEX_FORMAT", "AUTO").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

NANG = 36
CLOTH_NAME = "cloth1"
# 옷이 물어도 되는 뼈. 팔(UpperArm/Forearm/Hand)·다리·목·머리는 뺀다.
#  - 팔을 물면 겨드랑이에서 어깨끈이 몸통에 끌려 늘어난다
#  - 다리를 물면 치마가 두 허벅지 사이에서 찢어진다
#  - 목/머리를 물면 어깨끈이 고개를 따라 움직인다
ALLOW = ("Bip001 Pelvis", "Bip001 Spine", "Bip001 Chest", "Bip001 Chest2",
         "Bip001 L Clavicle", "Bip001 R Clavicle")
# 치마(벨트 아래)는 다리를 물려야 한다. 골반에만 묶으면 무릎을 들 때 허벅지가
# 치마를 그대로 뚫고 나온다(s15 1차 굽기 실측: Run 프레임당 평균 71정점, 최대 8.0cm).
ALLOW_LEG = ("Bip001 Pelvis", "Bip001 Spine", "Bip001 L Thigh", "Bip001 R Thigh")

print("=" * 78)
print("[설정] 몸  %s" % BODY_GLB)
print("       옷  %s" % CLOTH_GLB)
print("       결과 %s" % OUT_GLB)

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30                                    # ★함정 1
sc.render.fps_base = 1.0


def drop_junk():
    """glTF 임포터가 뼈를 그리려고 만드는 Icosphere(★함정 4)."""
    for o in list(bpy.data.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)


def imp(path):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    drop_junk()
    return [o for o in sc.objects if o.name not in before]


def weld(ob, dist=1e-5):
    """glTF 는 UV/노멀 이음매에서 정점을 쪼갠다. 섬 판정과 웨이트 전이 전에 붙인다."""
    n0 = len(ob.data.vertices)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return n0, len(ob.data.vertices)


def islands(ob):
    adj = {i: set() for i in range(len(ob.data.vertices))}
    for p in ob.data.polygons:
        vs = list(p.vertices)
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            adj[a].add(b)
            adj[b].add(a)
    seen, out = set(), []
    for i in range(len(ob.data.vertices)):
        if i in seen:
            continue
        st, comp = [i], []
        seen.add(i)
        while st:
            a = st.pop()
            comp.append(a)
            for nb in adj[a]:
                if nb not in seen:
                    seen.add(nb)
                    st.append(nb)
        out.append(comp)
    out.sort(key=len, reverse=True)
    return out


def bake_world(ob):
    """정점을 월드 좌표로 굳히고 오브젝트 행렬을 단위행렬로."""
    ob.data.transform(ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)
    ob.data.update()


def ring(pts, cx, cy, mode):
    """각도 구간별 반경. 고리의 안쪽면(min) / 바깥면(max)."""
    r = [None] * NANG
    for p in pts:
        d = math.hypot(p.x - cx, p.y - cy)
        k = int((math.atan2(p.y - cy, p.x - cx) + math.pi) / (2 * math.pi) * NANG) % NANG
        if r[k] is None:
            r[k] = d
        elif mode == "min":
            r[k] = min(r[k], d)
        else:
            r[k] = max(r[k], d)
    return r


def use(act):
    """액션을 물린다. ★블렌더 4.4+ 는 액션에 슬롯이 있어 안 물리면 포즈가 안 움직인다."""
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def eval_verts(ob, dg):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    out = [ob.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return out


# ================================================================ 1) 몸
print("=" * 78)
print("[1] 몸")
# ★함정 2: 몸을 먼저 읽는다
objs = imp(BODY_GLB)
arm = next(o for o in objs if o.type == "ARMATURE")
meshes = [o for o in objs if o.type == "MESH"]
swords = [o for o in meshes if o.name.startswith("SW_")]
body = max((o for o in meshes if not o.name.startswith("SW_")
            and not o.name.startswith("SH_")),
           key=lambda o: len(o.data.vertices))
# ★결과물을 다시 넣으면 옷 위에 옷을 얹는다. 알몸만 받는다.
dup = [o.name for o in meshes if o.name.startswith(CLOTH_NAME)]
assert not dup, ("몸에 이미 옷이 있다(%s). BODY_GLB 는 s31~s27 이 구운 **알몸**"
                 " basic2 여야 한다" % dup)
for a in bpy.data.actions:
    a.use_fake_user = True                            # ★함정 7
ACT_NAMES = sorted(a.name for a in bpy.data.actions)
print("  아마추어 %s 뼈 %d / 몸 %s 정점 %d / 칼 %d자루 %s"
      % (arm.name, len(arm.data.bones), body.name, len(body.data.vertices),
         len(swords), sorted(o.name for o in swords)))
print("  액션 %d개 %s (씬 fps %d)" % (len(ACT_NAMES), ACT_NAMES, sc.render.fps))
assert len(swords) == 7, "칼이 7자루가 아니다(%d). s31 파이프라인 산출물이 맞나" % len(swords)

arm.data.pose_position = "REST"                       # ★함정 3
bpy.context.view_layer.update()
A2W = arm.matrix_world
BW = [body.matrix_world @ v.co for v in body.data.vertices]
H = max(p.z for p in BW) - min(p.z for p in BW)
FOOT = min(p.z for p in BW)
print("  키 %.4f  발바닥z %.4f  아마추어 스케일 %.4f (뼈 로컬 1 = %.1fcm)"
      % (H, FOOT, A2W.to_scale().x, A2W.to_scale().x * 100))

# ================================================================ 2) 옷 얹기
print("=" * 78)
print("[2] 옷")
cobjs = imp(CLOTH_GLB)
cloth = next(o for o in cobjs if o.type == "MESH")
n0, n1 = weld(cloth)
bake_world(cloth)
print("  정점 %d -> 용접 후 %d / 삼각형 %d"
      % (n0, n1, sum(len(p.vertices) - 2 for p in cloth.data.polygons)))
CV = [v.co.copy() for v in cloth.data.vertices]
isl = islands(cloth)
print("  섬 %d개" % len(isl))
# 벨트 고리 = 가로로 넓고 세로로 얇은 섬
belt = next(s for s in isl
            if (max(CV[i].x for i in s) - min(CV[i].x for i in s)) > 0.9
            and (max(CV[i].z for i in s) - min(CV[i].z for i in s)) < 0.3)
bp = [CV[i] for i in belt]
BCX = (max(p.x for p in bp) + min(p.x for p in bp)) / 2
BCY = (max(p.y for p in bp) + min(p.y for p in bp)) / 2
BZ0, BZ1 = min(p.z for p in bp), max(p.z for p in bp)
BMID = (BZ0 + BZ1) / 2
strap = max(isl, key=lambda s: max(CV[i].z for i in s) - min(CV[i].z for i in s))
print("  벨트 = 정점 %d  z %.3f~%.3f  중심(%.3f,%.3f)"
      % (len(belt), BZ0, BZ1, BCX, BCY))
print("  어깨끈 = 정점 %d  z %.3f~%.3f"
      % (len(strap), min(CV[i].z for i in strap), max(CV[i].z for i in strap)))

RIN = ring(bp, BCX, BCY, "min")
# 허리 프로파일(팔 제외). 벨트 띠 높이만큼의 밴드에서 잰다.
ARMG = [g.index for g in body.vertex_groups
        if any(t in g.name for t in ("UpperArm", "Forearm", "Hand"))]
armv = set()
for v in body.data.vertices:
    for g in v.groups:
        if g.group in ARMG and g.weight > 0.25:
            armv.add(v.index)
            break
ZC = FOOT + H * HIP_F
band = [p for i, p in enumerate(BW)
        if i not in armv and abs(p.z - ZC) <= (BZ1 - BZ0) * 0.5]
WCX = (max(p.x for p in band) + min(p.x for p in band)) / 2
WCY = (max(p.y for p in band) + min(p.y for p in band)) / 2
RB = ring(band, WCX, WCY, "max")
S_MIN = max(RB[i] / RIN[i] for i in range(NANG) if RIN[i] and RB[i])
S = S_MIN * CLOTH_S
print("  허리 밴드 정점 %d 중심(%.4f,%.4f) z %.4f" % (len(band), WCX, WCY, ZC))
print("  벨트 최소배율 %.4f x 여유 %.3f = %.4f (키 대비 %.4f)"
      % (S_MIN, CLOTH_S, S, S / H))

for v in cloth.data.vertices:
    p = v.co
    v.co = Vector((WCX + (p.x - BCX) * S, WCY + (p.y - BCY) * S,
                   ZC + (p.z - BMID) * S))
cloth.data.update()
BELT_TOP = ZC + (BZ1 - BMID) * S
CV = [v.co.copy() for v in cloth.data.vertices]
knee_z = (A2W @ arm.data.bones["Bip001 R Calf"].head_local).z
print("  배치 후 옷 z %.4f~%.4f  (벨트 윗선 %.4f, 무릎 %.4f)"
      % (min(p.z for p in CV), max(p.z for p in CV), BELT_TOP, knee_z))
print("  치마 밑단 z/키 %.3f  무릎 z/키 %.3f  -> %s"
      % ((min(p.z for p in CV) - FOOT) / H, (knee_z - FOOT) / H,
         "무릎 위" if min(p.z for p in CV) > knee_z else "★무릎 아래(다리가 뚫을 수 있다)"))

# ---- 2-1) 몸이 옷을 뚫는 문제: 옷 정점을 몸 표면 밖으로 밀어낸다 ----
# ★"옷에 가려지는 몸 정점을 지운다" 는 쓸 수 없다. 이 옷은 몸을 덮는 옷이 아니라
#   벨트 + 허리에서 늘어진 로인클로스 + 어깨끈이다. 가려지는 몸 면적이 거의 없고,
#   치마 틈새로 맨살이 그대로 보이므로 지우면 구멍이 뚫린다.
# ★"몸을 안쪽으로 줄인다" 도 안 쓴다. 실루엣(근육)이 캐릭터 정체성인데 옷 몇 개
#   정점 때문에 몸 전체를 깎는 건 비용이 반대다.
# ★여유 간격은 높이에 따라 다르게 준다. 벨트 선은 몸에 붙어야 벨트답고(4mm),
#   치마 밑단은 넉넉히 떨어져 있어야 달릴 때 허벅지가 앞으로 나와도 안 뚫는다(28mm).
Minv = body.matrix_world.inverted()
M3 = body.matrix_world.to_3x3()
SK_BOT0 = min(p.z for p in CV)
SK_D0 = max(1e-6, BELT_TOP - SK_BOT0)
moved, worst = 0, 0.0
for v in cloth.data.vertices:
    p = v.co
    tt = min(1.0, max(0.0, (BELT_TOP - p.z) / SK_D0))
    marg = CONFORM_M + (CONFORM_HEM - CONFORM_M) * (tt * tt * (3 - 2 * tt))
    hit, loc, nrm, _ = body.closest_point_on_mesh(Minv @ p)
    if not hit:
        continue
    lw = body.matrix_world @ loc
    nw = (M3 @ nrm).normalized()
    d = (p - lw).dot(nw)
    if d < marg:
        v.co = lw + nw * marg
        moved += 1
        worst = max(worst, marg - d)
cloth.data.update()
CV = [v.co.copy() for v in cloth.data.vertices]
print("  [conform] 몸에 너무 붙은 정점 %d개를 표면 밖(벨트 %.0fmm ~ 밑단 %.0fmm)으로 밀어냄"
      " (최대 이동 %.1fmm)"
      % (moved, CONFORM_M * 1000, CONFORM_HEM * 1000, worst * 1000))

# ---- 2-2) 웨이트 전이 ----
# 옷에 뼈가 없다. 몸의 정점 그룹을 옷으로 옮긴다.
# ★벨트 아래(치마)는 **벨트 높이에서 샘플**한다. 그대로 재면 허벅지 웨이트를 물어
#   다리를 벌릴 때 치마가 두 갈래로 찢어진다. 벨트 높이에서 뜨면 골반에 고정돼
#   치마가 통째로 엉덩이를 따라 흔들린다(실제 로인클로스가 그렇다).
GNAME = {g.index: g.name for g in body.vertex_groups}


def sample(p, allow):
    """몸 표면에서 가장 가까운 면을 찾아 그 면 정점들의 웨이트를 거리 역수로 섞는다."""
    hit, loc, nrm, fi = body.closest_point_on_mesh(Minv @ p)
    acc = {}
    if not hit:
        return acc
    lw = body.matrix_world @ loc
    for vi in body.data.polygons[fi].vertices:
        bv = body.matrix_world @ body.data.vertices[vi].co
        w = 1.0 / ((bv - lw).length + 1e-4)
        for g in body.data.vertices[vi].groups:
            nm = GNAME[g.group]
            if nm not in allow:
                continue
            acc[nm] = acc.get(nm, 0.0) + w * g.weight
    tot = sum(acc.values())
    return {k: v / tot for k, v in acc.items()} if tot > 1e-6 else {}


SK_BOT = min(p.z for p in CV)
SK_DEPTH = max(1e-6, BELT_TOP - SK_BOT)
WT = []
fallback = 0
for v in cloth.data.vertices:
    p = v.co
    if p.z >= BELT_TOP:
        w = sample(p, ALLOW)
    else:
        # ★깊이에 비례해 천천히 넘기면 정작 가장 많이 뚫리는 치마 **윗부분**
        #   (엉덩이·허벅지 뿌리)이 골반에 묶여 그대로 뚫린다. 달릴 때 허벅지는
        #   고관절 바로 아래부터 앞으로 나온다. 그래서 위에서부터 빨리 넘기고
        #   깊이 55% 지점에서 이미 다리를 100% 따라가게 한다.
        k = min(1.0, max(0.0, (BELT_TOP - p.z) / SK_DEPTH) / 0.55)
        k = k * k * (3 - 2 * k) * LEG_MAX          # 부드럽게 다리로 넘긴다
        w_top = sample(Vector((p.x, p.y, BELT_TOP)), ALLOW)
        w_leg = sample(p, ALLOW_LEG)
        w = {}
        for nm, val in w_top.items():
            w[nm] = w.get(nm, 0.0) + (1 - k) * val
        for nm, val in w_leg.items():
            w[nm] = w.get(nm, 0.0) + k * val
    if sum(w.values()) < 1e-6:
        w = {"Bip001 Pelvis": 1.0}
        fallback += 1
    WT.append(w)
print("  [웨이트] 폴백(주변에 허용 뼈가 없어 골반 1.0) %d개" % fallback)

# ★라플라시안 스무딩: 이웃 정점과 웨이트를 섞어 이음매를 없앤다.
#   웨이트가 정점마다 툭툭 바뀌면 그 경계에서 옷이 찢어져 보인다.
#   (s15 실측: 6회 = 최대 늘음 7.75배 / 14회 = 4.72배. 14회를 쓴다)
nb = {i: set() for i in range(len(cloth.data.vertices))}
for e in cloth.data.edges:
    a, b = e.vertices
    nb[a].add(b)
    nb[b].add(a)
for _ in range(SMOOTH_N):
    NW = []
    for i, w in enumerate(WT):
        acc = dict(w)
        for j in nb[i]:
            for nm, val in WT[j].items():
                acc[nm] = acc.get(nm, 0.0) + val
        tot = sum(acc.values())
        NW.append({k: v / tot for k, v in acc.items()})
    WT = NW

# ★가랑이 함정: 앞판이 **두 허벅지를 동시에** 물면 다리를 벌릴 때 양쪽으로 찢어진다.
#   ★이 보정은 반드시 **스무딩 뒤**에 해야 한다. 앞에서 하면 스무딩이 이웃한테서
#     허벅지 웨이트를 다시 끌어와 그대로 원복된다.
LT, RT = "Bip001 L Thigh", "Bip001 R Thigh"
merged = 0
for i, w in enumerate(WT):
    wl, wr = w.get(LT, 0.0), w.get(RT, 0.0)
    if wl + wr < 1e-6:
        continue
    c = 2.0 * min(wl, wr) / (wl + wr)     # 1 = 양다리를 똑같이 뭄 = 가랑이
    if c < 1e-3:
        continue
    give = c * (wl + wr)
    w[LT] = wl * (1 - c)
    w[RT] = wr * (1 - c)
    w["Bip001 Pelvis"] = w.get("Bip001 Pelvis", 0.0) + give
    merged += 1
print("  [웨이트] 양다리를 같이 문 정점 %d개의 다리 웨이트를 골반으로 이관" % merged)

# ★glTF 는 정점당 뼈 4개까지다. 여기서 안 자르면 익스포터가 조용히 잘라 정규화해
#   내가 검증한 것과 다른 게 나간다.
# ★단순 상위 4개 자르기는 이웃끼리 **다른 뼈**가 살아남아 그 자체로 틈을 만든다.
#   먼저 작은 웨이트를 잘라내 이웃끼리 같은 뼈만 남게 만든 뒤 4개로 줄인다.
over = 0
for i, w in enumerate(WT):
    items = [(k, v) for k, v in w.items() if v >= PRUNE]
    if not items:
        items = [max(w.items(), key=lambda x: x[1])]
    items.sort(key=lambda x: -x[1])
    if len(items) > 4:
        over += 1
        items = items[:4]
    tot = sum(v for _, v in items)
    WT[i] = {k: v / tot for k, v in items}
print("  [웨이트] %.2f 미만 가지치기 후에도 4개 초과라 자른 정점 %d개" % (PRUNE, over))
print("  [웨이트] 정점당 뼈 수 분포 %s"
      % sorted({n: sum(1 for w in WT if len(w) == n) for n in (1, 2, 3, 4)}.items()))

used = {}
for bn in set(ALLOW) | set(ALLOW_LEG):
    if bn not in cloth.vertex_groups:
        cloth.vertex_groups.new(name=bn)
for i, w in enumerate(WT):
    for nm, val in w.items():
        cloth.vertex_groups[nm].add([i], val, "REPLACE")
        used[nm] = used.get(nm, 0) + 1
sums = [sum(w.values()) for w in WT]
print("  [웨이트] 뼈별 영향 정점 수 %s" % sorted(used.items(), key=lambda x: -x[1]))
print("  [웨이트] ★합 최소 %.6f 최대 %.6f / 1과 다른 정점 %d개 (0 이어야 원점으로 안 빨린다)"
      % (min(sums), max(sums), sum(1 for s in sums if abs(s - 1.0) > 1e-5)))
md = cloth.modifiers.new("Armature", "ARMATURE")
md.object = arm
cloth.parent = arm          # ★익스포터 경고 "Armature must be the parent" 방지
cloth.matrix_parent_inverse = arm.matrix_world.inverted()
cloth.name = cloth.data.name = CLOTH_NAME   # ★함정 5

# ---- 2-3) 게임 키 계산 검산(★함정 8) ----
CW0 = [v.co.copy() for v in cloth.data.vertices]
h_body = H
h_all = max(max(p.z for p in BW), max(p.z for p in CW0)) - \
    min(min(p.z for p in BW), min(p.z for p in CW0))
print("  [키] 몸만 %.4f / 몸+옷 %.4f  (차이 %.5f = %.3f%%)"
      % (h_body, h_all, h_all - h_body, (h_all / h_body - 1) * 100))
if abs(h_all - h_body) > 1e-4:
    print("  ★옷이 몸 박스를 넘었다. 게임 키 정규화가 그만큼 흔들린다")

# ================================================================ 3) 검증
if VERIFY:
    print("=" * 78)
    print("[3] 애니메이션 검증 (찢어짐 = 옷 모서리 늘어남 / 뚫림 = 옷 정점이 몸 안)")
    arm.data.pose_position = "POSE"
    if arm.animation_data is None:
        arm.animation_data_create()
    # ★모서리 늘어남 = 찢어짐. 다만 모피 끝의 1mm 짜리 모서리는 배율이 크게 나와도
    #   실제로는 안 보인다. 키의 0.4%(약 6mm) 이상인 모서리만 본다.
    edges = [(e.vertices[0], e.vertices[1]) for e in cloth.data.edges]
    REST_L = [(cloth.data.vertices[a].co - cloth.data.vertices[b].co).length
              for a, b in edges]
    ELIM = H * 0.004
    EIDX = [k for k in range(len(edges)) if REST_L[k] >= ELIM]
    print("  모서리 %d개 중 %.1fmm 이상 %d개만 판정 대상"
          % (len(edges), ELIM * 1000, len(EIDX)))
    ISL_OF = {}
    for k, s in enumerate(isl):
        for i in s:
            ISL_OF[i] = k
    NAMES = {}
    for k, s in enumerate(isl):
        zs = [CV[i].z for i in s]
        NAMES[k] = "섬%d(정점%d z%.2f~%.2f)" % (k, len(s), min(zs), max(zs))
    print("  %-7s %9s %9s %10s %12s %9s"
          % ("클립", "프레임", "최대늘음", "1.2배초과", "프레임당뚫림", "최대깊이"))
    for nm in ACT_NAMES:
        act = bpy.data.actions.get(nm)
        if not act:
            continue
        use(act)
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        st_max, bad = 1.0, 0
        st_worst = None
        pk_n, pk_d, nfr = 0, 0.0, 0
        pk_isl = {}
        for f in range(f0, f1 + 1, max(1, (f1 - f0) // 12)):
            nfr += 1
            sc.frame_set(f)
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            cw = eval_verts(cloth, dg)
            for k in EIDX:
                a, b = edges[k]
                r = (cw[a] - cw[b]).length / REST_L[k]
                if r > st_max:
                    st_max = r
                    st_worst = (f, k, a, REST_L[k], (cw[a] - cw[b]).length)
                if r > 1.2:
                    bad += 1
            bt = BVHTree.FromObject(body, dg)
            for vi, p in enumerate(cw):
                loc, nrm, idx, dist = bt.find_nearest(body.matrix_world.inverted() @ p)
                if loc is None:
                    continue
                lw = body.matrix_world @ loc
                nw = (body.matrix_world.to_3x3() @ nrm).normalized()
                d = (p - lw).dot(nw)
                if d < 0:
                    pk_n += 1
                    pk_d = max(pk_d, -d)
                    k = ISL_OF.get(vi, -1)
                    a0, a1 = pk_isl.get(k, (0, 0.0))
                    pk_isl[k] = (a0 + 1, max(a1, -d))
        print("  %-7s %4d~%-4d %9.3f %9d %12.1f %9.4f"
              % (nm, f0, f1, st_max, bad, pk_n / nfr, pk_d))
        for k, (c, d) in sorted(pk_isl.items(), key=lambda x: -x[1][0])[:2]:
            print("        뚫림 상위 %s  프레임당 %.1f개 최대 %.1fmm"
                  % (NAMES.get(k, "?"), c / nfr, d * 1000))
        if st_worst and st_max > 1.2:
            f, k, a, r0, r1 = st_worst
            print("        최악 늘음 f%d %s  %.1fmm -> %.1fmm"
                  % (f, NAMES.get(ISL_OF.get(a, -1), "?"), r0 * 1000, r1 * 1000))

# ================================================================ 4) 재질
print("=" * 78)
print("[4] 재질 (게임 계약: MeshToonMaterial({map}) - 베이스컬러 말고는 안 쓴다)")
# ★옷의 normal / metallic_roughness / emissive 는 전부 낭비다(합쳐 9.5MB).
#   링크를 끊으면 익스포터가 안 내보낸다(export_unused_images 기본 False).
# ★칼 재질(bd_/bv_/ht_/sp_/fur_/gr_/ft_)은 **손대지 않는다**. 게임이 그 이름으로
#   칼날 발광 부위를 가른다. 몸 재질도 그대로 둔다. 여기서 미는 것은 옷 하나뿐이다.


def strip_material(m):
    """Principled 의 Base Color 만 남기고 나머지 입력 링크를 끊는다.

    ★Blender RNA 오브젝트는 접근할 때마다 새 래퍼가 나와서 `is` 비교가 안 먹는다.
      노드 비교는 반드시 **이름**으로."""
    if not m or not m.node_tree:
        return
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    bn = bsdf.name
    kept = None
    for l in list(nt.links):
        if l.to_node.name != bn:
            continue
        if l.to_socket.name == "Base Color":
            kept = l.from_node.name
            continue
        print("    %-18s 링크 끊음: %-16s (from %s)"
              % (m.name, l.to_socket.name, l.from_node.name))
        nt.links.remove(l)
    for key, val in (("Emission Strength", 0.0), ("Metallic", 0.0),
                     ("Roughness", 0.75), ("Specular IOR Level", 0.35)):
        s = bsdf.inputs.get(key)
        if s is not None:
            s.default_value = val
    s = bsdf.inputs.get("Emission Color")
    if s is not None:
        s.default_value = (0, 0, 0, 1)
    # 베이스컬러로 이어지는 노드만 남기고 나머지 텍스처 노드는 지운다
    keepset, stack = set(), ([kept] if kept else [])
    while stack:
        nm = stack.pop()
        if nm is None or nm in keepset:
            continue
        keepset.add(nm)
        nd = nt.nodes.get(nm)
        if nd is None:
            continue
        for i in nd.inputs:
            for l in i.links:
                stack.append(l.from_node.name)
    for nd in list(nt.nodes):
        if nd.type == "TEX_IMAGE" and nd.name not in keepset:
            print("    %-18s 텍스처 노드 제거: %s"
                  % (m.name, getattr(nd.image, "name", "?")))
            nt.nodes.remove(nd)
    print("    %-18s 남긴 베이스컬러 노드: %s" % (m.name, kept))


for m in cloth.data.materials:
    strip_material(m)
    # ★함정 6: 게임은 재질 이름 앞자리로 칼날 발광 부위를 가른다. 옷이 그 접두어를
    #   물면 칼 셰이더가 옷을 물고 들어간다. 임포트 이름을 그대로 쓰되 검사만 한다.
    assert not m.name.startswith(("bd_", "bv_", "ht_", "sp_")), \
        "옷 재질 이름 %s 가 칼 발광 접두어를 물었다" % m.name
print("  옷 재질: %s" % [m.name for m in cloth.data.materials])

used_imgs = []
for ob in [body, cloth] + swords:
    for m in ob.data.materials:
        if not m or not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            img = getattr(nd, "image", None)
            if img is not None and img not in used_imgs:
                used_imgs.append(img)
print("  남은 이미지 %d장" % len(used_imgs))
for img in used_imgs:
    w, h = img.size
    print("    %-22s %dx%d 채널%d %s" % (img.name, w, h, img.channels, img.file_format))
    if TEX_SIZE and (w > TEX_SIZE or h > TEX_SIZE):
        k = TEX_SIZE / float(max(w, h))
        img.scale(max(1, int(round(w * k))), max(1, int(round(h * k))))
        print("      -> %dx%d 로 축소" % img.size[:])

# ================================================================ 5) 내보내기
print("=" * 78)
print("[5] 내보내기")
IDLE = bpy.data.actions.get("Idle")
if IDLE:
    use(IDLE)
    sc.frame_set(int(IDLE.frame_range[0]))
arm.data.pose_position = "POSE"
bpy.context.view_layer.update()
for a in bpy.data.actions:
    a.use_fake_user = True                            # ★함정 7
print("  액션:", [a.name for a in bpy.data.actions])
print("  오브젝트:", [(o.name, o.type) for o in sc.objects])
tri = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons)
       for o in sc.objects if o.type == "MESH"}
print("  삼각형:", tri, "합계", sum(tri.values()))
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
# ★원자적 교체: 게임이 읽는 파일을 반쯤 쓴 상태로 두지 않는다
TMP = OUT_GLB + ".tmp.glb"
kw = dict(filepath=TMP, export_format="GLB", use_selection=False,
          export_apply=True, export_yup=True,
          export_animations=True, export_animation_mode="ACTIONS",
          export_nla_strips=False, export_bake_animation=True,
          export_frame_range=False)
if TEX_FORMAT not in ("AUTO", ""):
    kw.update(export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
              export_jpeg_quality=TEX_QUALITY)
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.export_scene.gltf(**kw)
os.replace(TMP, OUT_GLB)
sz = os.path.getsize(OUT_GLB)
print("EXPORTED %s  %d bytes (%.2f MB)  옷 %d정점 / 칼 %d자루 / 액션 %d개"
      % (OUT_GLB, sz, sz / 1e6, len(cloth.data.vertices), len(swords),
         len(bpy.data.actions)))

# ================================================================ 6) 렌더
if not RENDER:
    print("DONE (렌더 생략)")
    raise SystemExit(0)

os.makedirs(OUTDIR, exist_ok=True)
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                    else "BLENDER_EEVEE")
sc.view_settings.view_transform = "Standard"
wd = bpy.data.worlds.new("W")
sc.world = wd
wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs[0].default_value = (0.06, 0.065, 0.08, 1)
for eul, en, col in (((58, 0, -30), 4.0, (1, 1, 1)),
                     ((-40, 0, 130), 1.8, (0.7, 0.82, 1.0))):
    li = bpy.data.lights.new("S", "SUN")
    li.energy = en
    li.color = col
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = tuple(math.radians(a) for a in eul)
    sc.collection.objects.link(so)
bpy.ops.mesh.primitive_plane_add(size=H * 6, location=(0, 0, FOOT))
cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
# 게임 기본 칼(백아)만 켠다. 7자루가 다 보이면 겹쳐서 아무것도 안 보인다.
for o in swords:
    o.hide_render = (o.name != "SW_baekah")

CEN = Vector((0, 0, FOOT + H * 0.55))
HIP = Vector((0, 0, FOOT + H * HIP_F))


def look(cam, eye, tgt):
    cam.location = eye
    d = (tgt - eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


SHOTS = [
    ("front", CEN + Vector((0, -H * 1.9, H * 0.10)), CEN, (620, 800), "Idle", None),
    ("side", CEN + Vector((-H * 1.9, 0, H * 0.10)), CEN, (620, 800), "Idle", None),
    ("back", CEN + Vector((0, H * 1.9, H * 0.10)), CEN, (620, 800), "Idle", None),
    ("hip", HIP + Vector((0, -H * 0.75, H * 0.12)), HIP, (800, 620), "Idle", None),
    ("walk", CEN + Vector((-H * 1.2, -H * 1.5, H * 0.10)), CEN, (620, 800), "Walk", 0.5),
    ("run", CEN + Vector((-H * 1.2, -H * 1.5, H * 0.10)), CEN, (620, 800), "Run", 0.4),
    ("attack", CEN + Vector((-H * 1.2, -H * 1.5, H * 0.10)), CEN, (620, 800), "Attack", 0.6),
]
for nm, eye, tgt, res, clip, t in SHOTS:
    act = bpy.data.actions.get(clip)
    if act is None:
        continue
    use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    sc.frame_set(f0 if t is None else int(f0 + (f1 - f0) * t))
    bpy.context.view_layer.update()
    sc.render.resolution_x, sc.render.resolution_y = res
    look(cam, eye, tgt)
    sc.render.filepath = os.path.join(OUTDIR, "s33_%s.png" % nm)
    bpy.ops.render.render(write_still=True)
    print("   렌더 %s" % sc.render.filepath)
print("DONE")
