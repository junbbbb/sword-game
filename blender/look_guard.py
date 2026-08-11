# -*- coding: utf-8 -*-
"""중단세를 크게 여러 각도로. 포즈 문제는 Blender 에서 바로 보는 게 맞다."""
import bpy, os, sys, math
from mathutils import Vector
ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import importlib, combo_poses as CP
importlib.reload(CP)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "blender", "slayer.blend"))
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("Floor","Plane")))
if arm.animation_data: arm.animation_data_clear()
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
xs = [(mesh.matrix_world @ v.co).x for v in mesh.data.vertices]
H = max(zs) - min(zs); FOOT = min(zs); CX = (min(xs)+max(xs))/2
ps = CP.Poser(arm, H)

POSE = os.environ.get("POSE", "GUARD")
ps.apply(getattr(CP, POSE))
bpy.context.view_layer.update()

li = bpy.data.lights.new("S","SUN"); li.energy = 4.2
so = bpy.data.objects.new("S", li); so.rotation_euler = (math.radians(58),0,math.radians(-30))
sc.collection.objects.link(so)
li2 = bpy.data.lights.new("F","SUN"); li2.energy = 1.6; li2.color=(0.7,0.82,1.0)
so2 = bpy.data.objects.new("F", li2); so2.rotation_euler = (math.radians(-30),0,math.radians(130))
sc.collection.objects.link(so2)
cam = sc.camera
if cam is None:
    cd = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 62
# 손 부분을 크게: 척추 높이를 겨눈다
TGT = Vector((CX, 0, FOOT + H * 0.56))
D = H * 1.15
VIEWS = {
    "front": Vector((0, -D, H*0.10)),          # 정면(캐릭터 정면 = -Y)
    "front_hi": Vector((0, -D*0.9, H*0.42)),   # 위에서 내려다본 정면
    "side":  Vector((-D, 0, H*0.10)),
    "q":     Vector((-D*0.72, -D*0.72, H*0.16)),
}
OUT = os.path.join(ROOT, "renders", "guard_look")
os.makedirs(OUT, exist_ok=True)
sc.render.resolution_x, sc.render.resolution_y = 900, 900
for nm, off in VIEWS.items():
    cam.location = TGT + off
    dd = TGT - cam.location
    cam.rotation_euler = dd.to_track_quat("-Z","Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (POSE, nm))
    bpy.ops.render.render(write_still=True)
print("DONE", OUT)
