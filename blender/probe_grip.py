# -*- coding: utf-8 -*-
# 손바닥 실제 중심(변형된 메시 기준)을 측정하고, 칼날 방향 후보를 렌더 비교한다.
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
SCR = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad/grip"
os.makedirs(SCR, exist_ok=True)
sys.path.insert(0, BLD)
import build_scenes as BS

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"

arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh_ob = next(o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("Floor", "Plane")))

# 기존 칼 제거
old = bpy.data.objects.get("katana_slayer")
if old:
    for ch in list(old.children):
        bpy.data.objects.remove(ch, do_unlink=True)
    bpy.data.objects.remove(old, do_unlink=True)
for o in list(sc.objects):
    if o.name.startswith(("bladeK_", "tsubaK_", "gripK_", "ringK", "pomK")):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()

hb = next(b for b in arm.pose.bones if "r hand" in b.name.lower())
M = arm.matrix_world @ hb.matrix
loc, rotq, _ = M.decompose()
M_norm = Matrix.Translation(loc) @ rotq.to_matrix().to_4x4()
R3 = rotq.to_matrix()
print("bone axes(world): X=%s Y=%s Z=%s" % (
    tuple(round(v, 2) for v in R3.col[0]),
    tuple(round(v, 2) for v in R3.col[1]),
    tuple(round(v, 2) for v in R3.col[2])))
blen = hb.length * arm.matrix_world.to_scale().x

# ---- 변형된(포즈 적용된) 메시에서 손 정점 중심 ----
dg = bpy.context.evaluated_depsgraph_get()
ev = mesh_ob.evaluated_get(dg)
me_ev = ev.to_mesh()
vg = {g.index: g.name for g in mesh_ob.vertex_groups}
hand_idx = []
for v in mesh_ob.data.vertices:          # 그룹 정보는 원본에서
    best, bw = None, -1
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, vg.get(g.group, "")
    if best and "r hand" in best.lower():
        hand_idx.append(v.index)
pts = [ev.matrix_world @ me_ev.vertices[i].co for i in hand_idx]
palm = sum(pts, Vector((0, 0, 0))) / len(pts)
ev.to_mesh_clear()
zs = [(ev.matrix_world @ v.co).z for v in me_ev.vertices] if False else None
print("hand verts=%d  palm(world)=%s  bone_head=%s  dist=%.4f" % (
    len(pts), tuple(round(v, 3) for v in palm), tuple(round(v, 3) for v in loc),
    (palm - loc).length))
# 손바닥을 본 로컬 좌표로
palm_local = M_norm.inverted() @ palm
print("palm in bone-local:", tuple(round(v, 4) for v in palm_local), " bone_len=%.4f" % blen)

zs2 = [(mesh_ob.matrix_world @ v.co).z for v in mesh_ob.data.vertices]
H = max(zs2) - min(zs2)
SWS = H * 0.56

AXES = [("pY", (0, 1, 0)), ("mY", (0, -1, 0)), ("pX", (1, 0, 0)),
        ("mX", (-1, 0, 0)), ("pZ", (0, 0, 1)), ("mZ", (0, 0, -1))]

cam_d = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam_d.lens = 42
li = bpy.data.lights.new("S", "SUN")
li.energy = 4.0
so = bpy.data.objects.new("S", li)
so.rotation_euler = (math.radians(55), 0, math.radians(-25))
sc.collection.objects.link(so)

made = []
for i, (nm, ax) in enumerate(AXES):
    k = BS.build_katana(tag="pr%d" % i, scale=SWS, width_mul=2.8)
    q = Vector((1, 0, 0)).rotation_difference(Vector(ax))
    off = Matrix.Translation(palm_local) @ q.to_matrix().to_4x4()
    k.matrix_world = M_norm @ off
    for o in [k] + list(k.children):
        o.hide_render = True
    made.append((nm, k))

ctr = Vector((0, 0, H * 0.5))
for nm, k in made:
    for o in [k] + list(k.children):
        o.hide_render = False
    cam.location = ctr + Vector((2.2, -3.4, 0.9))
    d = ctr - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = 560
    sc.render.resolution_y = 620
    sc.render.filepath = os.path.join(SCR, "b_%s.png" % nm)
    bpy.ops.render.render(write_still=True)
    for o in [k] + list(k.children):
        o.hide_render = True
    print("rendered", nm)
print("DONE")
