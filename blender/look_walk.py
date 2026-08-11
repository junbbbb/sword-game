# -*- coding: utf-8 -*-
"""걷기 사이클을 **게임이 실제로 로드하는 glb 에서** 뽑아 본다.

왜 glb 인가
  포즈 스크립트를 다시 돌려 보면 "블렌더에서 만든 것"만 확인된다. 액션 슬롯,
  fake_user, 베이크 같은 내보내기 단계에서 조용히 어긋나는 사고가 많았으므로
  최종 산출물을 그대로 임포트해서 본다.

바닥판을 깔아 발이 뚫는지/뜨는지 눈으로 판정할 수 있게 했다.
칼은 7자루가 겹쳐 보이므로 한 자루만 남긴다.

실행: FRAMES=1,5,9 VIEW=side blender -b -P blender/look_walk.py
"""
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.environ.get("GLB", "slayer.glb")
ACT = os.environ.get("ACT", "Walk")
VIEW = os.environ.get("VIEW", "side")
TAG = os.environ.get("TAG", "new")
OUTDIR = os.environ.get("OUTDIR", os.path.join(ROOT, "renders", "history", "v47_walk"))
KEEP_SWORD = os.environ.get("SWORD", "SW_nokseun")

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30            # ★glb 는 초 단위다. 원본과 같은 30fps 로 읽어야 프레임이 1:1
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "web", GLB))
arm = next(o for o in sc.objects if o.type == "ARMATURE")


def _skip(o):
    if o.name.startswith(("SW_", "SH_")):
        return True
    return any(c.name == "glTF_not_exported" for c in o.users_collection)


bodies = [o for o in sc.objects if o.type == "MESH" and not _skip(o)]
zs, xs = [], []
for m in bodies:
    zs += [(m.matrix_world @ v.co).z for v in m.data.vertices]
    xs += [(m.matrix_world @ v.co).x for v in m.data.vertices]
H = max(zs) - min(zs)
FOOT = min(zs)
CX = (min(xs) + max(xs)) / 2
print("키 %.4f 바닥 %.4f" % (H, FOOT))

# 칼 한 자루만 남긴다(7자루가 다 보이면 뭐가 뭔지 모른다)
for o in list(sc.objects):
    if o.name.startswith("SW_") and not o.name.startswith(KEEP_SWORD):
        o.hide_render = True

# 바닥판: 발이 뚫는지/뜨는지 판정할 기준면
bpy.ops.mesh.primitive_plane_add(size=H * 6, location=(CX, 0, FOOT))
floor = bpy.context.object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.34, 0.36, 0.40, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
floor.data.materials.append(fm)

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

cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 55
# 다리를 보는 게 목적이라 시선을 허리 아래로 내린다(보통 0.50 H 인데 0.40 H)
TGT = Vector((CX, 0, FOOT + H * 0.40))
D = H * 1.95
VIEWS = {
    "side": Vector((-D, 0, H * 0.05)),        # 캐릭터 오른쪽(RIGHT = -X)
    "side2": Vector((D, 0, H * 0.05)),        # 왼쪽
    "front": Vector((0, -D, H * 0.08)),       # 정면(FWD = -Y)
    "q": Vector((-D * 0.7, -D * 0.7, H * 0.12)),
}
os.makedirs(OUTDIR, exist_ok=True)
sc.render.resolution_x, sc.render.resolution_y = 520, 760
sc.render.film_transparent = False

act = bpy.data.actions[ACT]
arm.animation_data_create()
arm.animation_data.action = act
try:
    slots = list(getattr(act, "slots", []))
    if slots:
        arm.animation_data.action_slot = slots[0]
except Exception:
    pass
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
print("[%s] f%d~%d" % (ACT, f0, f1))

frames = [int(x) for x in os.environ.get("FRAMES", "1,8,15").split(",")]
off = VIEWS[VIEW]
cam.location = TGT + off
dd = TGT - cam.location
cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
for f in frames:
    sc.frame_set(f)
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(OUTDIR, "%s_%s_f%02d.png" % (TAG, VIEW, f))
    bpy.ops.render.render(write_still=True)
    print("  rendered", sc.render.filepath)
print("DONE", OUTDIR)
