# -*- coding: utf-8 -*-
"""달리기 사이클을 옆·대각에서 프레임별로 뽑아 붙인다.
포즈 문제는 게임 빌드 말고 Blender 에서 바로 본다.
실행: SRC=infantry_combat_run blender -b -P look_run.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import importlib
import combo_poses as CP
import asset_anim as AA
importlib.reload(CP)
importlib.reload(AA)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "blender", "slayer.blend"))
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
xs = [(mesh.matrix_world @ v.co).x for v in mesh.data.vertices]
H = max(zs) - min(zs)
FOOT = min(zs)
CX = (min(xs) + max(xs)) / 2
ps = CP.Poser(arm, H)

SRC = os.environ.get("SRC", "infantry_combat_run")
src, f0, f1, tmp = AA.load(SRC)
N = f1 - f0 + 1

li = bpy.data.lights.new("S", "SUN")
li.energy = 4.0
so = bpy.data.objects.new("S", li)
so.rotation_euler = (math.radians(58), 0, math.radians(-30))
sc.collection.objects.link(so)
li2 = bpy.data.lights.new("F", "SUN")
li2.energy = 1.5
li2.color = (0.7, 0.82, 1.0)
so2 = bpy.data.objects.new("F", li2)
so2.rotation_euler = (math.radians(-30), 0, math.radians(130))
sc.collection.objects.link(so2)
cam = sc.camera
if cam is None:
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
cam.data.lens = 50
TGT = Vector((CX, 0, FOOT + H * 0.50))
D = H * 2.05
VIEWS = {
    "side": Vector((-D, 0, H * 0.06)),
    "q": Vector((-D * 0.66, -D * 0.66, H * 0.16)),
    "front": Vector((0, -D, H * 0.10)),
    "back": Vector((0, D, H * 0.10)),
}
OUT = os.path.join(ROOT, "renders", "history", "v30_run")
os.makedirs(OUT, exist_ok=True)
sc.render.resolution_x, sc.render.resolution_y = 520, 700
sc.render.film_transparent = False

STEP = int(os.environ.get("STEP", "3"))
frames = list(range(0, N, STEP))
print("렌더 프레임", frames)
for i in frames:
    sc.frame_set(f0 + i)
    ps.reset()
    AA.copy_pose(src, arm, AA.LOWER_NOHEAD)
    d = ps.bone_dir("r thigh")
    sw = 0.0 if d is None else max(-1.0, min(1.0, d.dot(CP.FWD) / 0.55))
    ps.apply({"b": CP.run_arms(sw)}, reset=False)
    bpy.context.view_layer.update()
    for nm, off in VIEWS.items():
        cam.location = TGT + off
        dd = TGT - cam.location
        cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, "new_%s_f%02d.png" % (nm, i))
        bpy.ops.render.render(write_still=True)
print("DONE", OUT)
