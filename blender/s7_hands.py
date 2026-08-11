# -*- coding: utf-8 -*-
"""주먹을 제대로 만들어 붙인다. slayer.blend 를 직접 고친다.

왜
  지금 손은 **한쪽 10 정점짜리 네모 덩어리**다. 손가락도 너클도 엄지도 없다.
  파지가 수치상 완벽해도(자루축 이탈 0.00) "쥐었다"로 안 읽히는 근본 원인이 이것이다.
  T 포즈 렌더에서도 손이 뭉툭한 벽돌로 보인다.

설계
  이 캐릭터는 손을 **절대 펴지 않는다**(항상 칼을 쥐고 있다).
  그래서 손가락 뼈를 넣을 필요가 없다. **자루를 감싼 주먹**을 통째로 만들어
  손 본에 웨이트 1.0 으로 묶으면 끝이다.
  자루는 손바닥 중심(palm_local)을 BLADE_LOCAL 방향으로 지난다. 그 축을
  중심으로 손가락 마디 4 개를 고리처럼 두르고, 손등과 엄지를 얹는다.

★주의: 새 주먹의 중심을 예전 palm_local 과 같은 자리에 둔다. 여기가 바뀌면
  지금까지 맞춰둔 파지·칼 부착이 전부 어긋난다.
실행: blender --background --python s7_hands.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
importlib.reload(CP)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
H = max(zs) - min(zs)
print("body:", body.name, "면", len(body.data.polygons), "H=%.3f" % H)

# 포즈를 레스트로 (지오메트리를 레스트 기준으로 만들어야 스키닝이 맞는다)
for b in arm.pose.bones:
    b.rotation_mode = "QUATERNION"
    b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()

ps = CP.Poser(arm, H)
# ★상수로 못 박는다. 이 스크립트를 다시 돌리면 '지금 있는 주먹'에서 다시 재게 되어
# 값이 조금씩 흘러간다. 원본 손(10정점 블록)에서 잰 값이 정본이다.
PALM = {"r": Vector((6.7737, 0.3771, 0.9296)),
        "l": Vector((6.7737, 0.3770, -0.9297))}
# 0.1661 은 블록의 **모서리까지** 거리라 실제 손 굵기보다 크다. 그대로 반지름으로
# 쓰면 주먹이 장화만 해진다(실측 렌더에서 확인). 실제 손 굵기는 그 0.58 배.
# 0.58 로 줄였더니 이번엔 손이 팔보다 가늘어 소매 끝에 달린 마개처럼 보였다.
# 실측: 팔뚝 반경 중앙값 0.1138 / 그때 주먹 중앙값 0.0799.
# 주먹은 팔뚝과 비슷하거나 살짝 굵어야 한다 -> 0.83 배.
FIST_R = {"r": 0.1661 * 0.83, "l": 0.1661 * 0.83}
print("palm_local r=%s  주먹반경 %.4f" % (tuple(round(v, 3) for v in PALM["r"]), FIST_R["r"]))

# ---------------------------------------------------------------- 옛 주먹 정점 제거
vgn = {g.index: g.name for g in body.vertex_groups}
old = {"r": [], "l": []}
for v in body.data.vertices:
    best, bw = None, -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, vgn.get(g.group, "")
    if not best:
        continue
    nm = best.lower()
    if "r hand" in nm:
        old["r"].append(v.index)
    elif "l hand" in nm:
        old["l"].append(v.index)
print("옛 주먹 정점: 오른 %d, 왼 %d" % (len(old["r"]), len(old["l"])))

bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.object.mode_set(mode="OBJECT")
for s in ("r", "l"):
    for i in old[s]:
        body.data.vertices[i].select = True
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.delete(type="VERT")
bpy.ops.object.mode_set(mode="OBJECT")
print("삭제 후 면", len(body.data.polygons))


# ---------------------------------------------------------------- 새 주먹
def ring(seg, r_out, r_in, half_len, squash):
    """자루축을 감싸는 마디 하나. 축은 로컬 +X. 단면은 타원(손가락은 납작하다)."""
    vs, fs = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        cy, cz = math.cos(a), math.sin(a) * squash
        for sx in (-half_len, half_len):
            vs.append((sx, cy * r_out, cz * r_out))
    n = seg
    for k in range(n):
        a0 = k * 2
        a1 = ((k + 1) % n) * 2
        fs.append((a0, a1, a1 + 1, a0 + 1))
    return vs, fs


def add_mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


# ★몸통 머티리얼을 그대로 쓰면 안 된다. 새 지오메트리엔 UV 가 없어서 텍스처의
# (0,0) 구석을 물어 **검은 갈색 장화**로 나온다(실측). 피부색 단색 머티리얼을 만든다.
# 색은 T 포즈 렌더의 얼굴에서 뽑았다: #F8D8A8
SKIN = bpy.data.materials.new("skin_hand")
SKIN.use_nodes = True
_bsdf = SKIN.node_tree.nodes.get("Principled BSDF")
if _bsdf:
    _bsdf.inputs["Base Color"].default_value = (0.973, 0.847, 0.659, 1.0)
    _bsdf.inputs["Roughness"].default_value = 0.85

BL = CP.BLADE_LOCAL.normalized()        # 손 로컬에서 자루가 지나는 방향
parts = []
for side in ("r", "l"):
    bone = ps.pb("%s hand" % side)
    rest = arm.matrix_world @ arm.data.bones[bone.name].matrix_local
    sc_v = rest.to_scale()
    S = abs(sc_v.x)                      # 본 로컬 -> 월드 스케일
    Rfist = FIST_R[side] / S             # 로컬 단위 주먹 반경
    P = Vector(PALM[side])

    # 자루축 로컬 프레임: X=자루방향, Y=손등쪽, Z=옆
    ax = BL.copy()
    up = Vector((0, 0, 1))
    if abs(ax.dot(up)) > 0.9:
        up = Vector((0, 1, 0))
    zz = ax.cross(up).normalized()
    yy = zz.cross(ax).normalized()
    M = Matrix((ax, yy, zz)).transposed().to_4x4()
    M.translation = P

    flip = 1.0 if side == "r" else -1.0

    # 손가락 마디 4 개. 자루축을 따라 늘어서고, 검지 쪽이 굵다.
    for i in range(4):
        t = i / 3.0
        off = (-0.52 + 1.04 * t) * Rfist        # 자루축 방향 위치
        rr = Rfist * (0.94 - 0.14 * t)          # 새끼손가락 쪽이 가늘다
        vs, fs = ring(12, rr, rr * 0.55, Rfist * 0.21, 0.86)
        ob = add_mesh("fist_%s_f%d" % (side, i), vs, fs, SKIN)
        ob.matrix_world = rest @ M @ Matrix.Translation((off, 0, 0))
        parts.append((ob, side))

    # 손등 + 손목 쪽 덩어리
    vs, fs = ring(12, Rfist * 0.98, 0, Rfist * 0.62, 0.80)
    ob = add_mesh("fist_%s_palm" % side, vs, fs, SKIN)
    ob.matrix_world = rest @ M @ Matrix.Translation((0, -Rfist * 0.30, 0))
    parts.append((ob, side))

    # 엄지: 자루를 비스듬히 가로지른다. 방향이 읽히는 결정적 단서.
    vs, fs = ring(8, Rfist * 0.34, 0, Rfist * 0.62, 1.0)
    ob = add_mesh("fist_%s_thumb" % side, vs, fs, SKIN)
    TM = (Matrix.Translation((Rfist * 0.30, Rfist * 0.62, -Rfist * 0.30 * flip))
          @ Matrix.Rotation(math.radians(58 * flip), 4, "Y")
          @ Matrix.Rotation(math.radians(28), 4, "Z"))
    ob.matrix_world = rest @ M @ TM
    parts.append((ob, side))

# 부드럽게 + 두께감
for ob, side in parts:
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    b = ob.modifiers.new("Bev", "BEVEL")
    b.width = 0.02
    b.segments = 2
    bpy.ops.object.modifier_apply(modifier=b.name)
    bpy.ops.object.shade_smooth()

# 손 본에 웨이트 1.0 으로 묶고 몸에 병합
for ob, side in parts:
    bone = ps.pb("%s hand" % side).name
    vg = ob.vertex_groups.new(name=bone)
    vg.add(range(len(ob.data.vertices)), 1.0, "REPLACE")

bpy.ops.object.select_all(action="DESELECT")
for ob, _ in parts:
    ob.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print("병합 후 면", len(body.data.polygons), "정점", len(body.data.vertices))

arm.data.pose_position = "POSE"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
print("SAVED slayer.blend")
