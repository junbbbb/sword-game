# -*- coding: utf-8 -*-
"""방패가 제대로 붙었는지 눈으로 본다. web/tank.glb 를 그대로 읽어 클립별로 렌더.
게임 빌드 말고 여기서 먼저 확인한다(look_run.py 와 같은 취지).

실행: CLIP=Idle FRAMES=17 VIEWS=front,left blender -b -P look_shield.py
저장: renders/history/v42_shield/ (OUTDIR 로 바꿀 수 있다)
검사 대상 glb 도 GLB 로 바꿀 수 있다(가중치 후보를 tank.glb 덮어쓰지 않고 비교하려고).
★한 번에 3장 이하로 끊어서 돌린다(프로세스가 오래 물리면 원인을 못 찾는다).
"""
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")
OUT = os.environ.get("OUTDIR", os.path.join(ROOT, "renders", "history", "v42_shield"))
GLB = os.environ.get("GLB", os.path.join(WEB, "tank.glb"))
os.makedirs(OUT, exist_ok=True)

CLIP = os.environ.get("CLIP", "Idle")
FRAMES = [int(x) for x in os.environ.get("FRAMES", "17").split(",") if x != ""]
VIEWS = [v for v in os.environ.get("VIEWS", "front,left").split(",") if v]
TAG = os.environ.get("TAG", "")

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
print("검사 대상:", GLB)
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH" and o.name.startswith("char"))
shield = next((o for o in sc.objects if o.name.startswith("SH_")), None)
print("방패 오브젝트:", shield.name if shield else "없음")

ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                    else "BLENDER_EEVEE")
sc.view_settings.view_transform = "Standard"

# 배경/바닥 - 실루엣과 발 높이를 판단하려면 있어야 한다
w = bpy.data.worlds.new("W")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.18, 0.21, 1)
sc.world = w
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
fl = bpy.context.active_object
fl.name = "Floor"
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.28, 0.3, 0.33, 1)
fl.data.materials.append(fm)

li = bpy.data.lights.new("S", "SUN")
li.energy = 4.0
so = bpy.data.objects.new("S", li)
so.rotation_euler = (math.radians(58), 0, math.radians(-30))
sc.collection.objects.link(so)
li2 = bpy.data.lights.new("F", "SUN")
li2.energy = 1.6
li2.color = (0.7, 0.82, 1.0)
so2 = bpy.data.objects.new("F", li2)
so2.rotation_euler = (math.radians(-30), 0, math.radians(130))
sc.collection.objects.link(so2)

zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
H = max(zs) - min(zs)
cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 50
TGT = Vector((0.15, 0, H * 0.52))
D = H * 2.1
OFF = {
    "front": Vector((0, -D, H * 0.08)),
    "back": Vector((0, D, H * 0.08)),
    "left": Vector((D, 0, H * 0.06)),          # 캐릭터의 왼쪽(+X) = 방패 쪽
    "right": Vector((-D, 0, H * 0.06)),
    "q": Vector((D * 0.62, -D * 0.72, H * 0.20)),   # 왼쪽 앞 대각
}
sc.render.resolution_x, sc.render.resolution_y = 620, 800
sc.render.film_transparent = False

if arm.animation_data is None:
    arm.animation_data_create()
arm.data.pose_position = "POSE"
act = bpy.data.actions.get(CLIP)
if act is None:
    print("클립 없음:", CLIP, [a.name for a in bpy.data.actions])
else:
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception as ex:
        print("action_slot 실패:", ex)

n = 0
for f in FRAMES:
    sc.frame_set(f)
    bpy.context.view_layer.update()
    for nm in VIEWS:
        cam.location = TGT + OFF[nm]
        d = TGT - cam.location
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(OUT, "%s%s_f%02d_%s.png" % (TAG, CLIP, f, nm))
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        n += 1
        print("RENDERED", path)
print("DONE %d장" % n)
