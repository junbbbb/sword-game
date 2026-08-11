# -*- coding: utf-8 -*-
"""T 포즈 참고 시트. AI 3D 생성기(Meshy 등)에 넣을 입력 이미지용.
정면/측면/후면을 배경 없이 균일 조명으로 뽑는다.
실행: blender -b -P look_tpose.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import combo_poses as CP

BLENDF = os.environ.get("BLENDF", "slayer.blend")
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "blender", BLENDF))
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK", "bow_")))
if arm.animation_data:
    arm.animation_data_clear()

# 칼·바닥은 뺀다(참고 이미지에 무기가 있으면 생성기가 같이 만들어버린다)
for o in list(sc.objects):
    if o.name.startswith(("bladeK", "gripK", "tsubaK", "pomK", "ringK", "katana",
                          "bow_", "Plane", "Floor")) or o.type in ("LIGHT", "CAMERA"):
        bpy.data.objects.remove(o, do_unlink=True)

ps = CP.Poser(arm, 1.0)
ps.reset()                     # 레스트 = T 포즈
bpy.context.view_layer.update()

zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
xs = [(mesh.matrix_world @ v.co).x for v in mesh.data.vertices]
H = max(zs) - min(zs)
CX = (min(xs) + max(xs)) / 2
CZ = (min(zs) + max(zs)) / 2

# 균일 조명(그림자가 지면 생성기가 그걸 형태로 오해한다)
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.15
for i, rot in enumerate(((60, 0, -40), (60, 0, 140), (-40, 0, 40))):
    li = bpy.data.lights.new("S%d" % i, "SUN")
    li.energy = 1.2
    so = bpy.data.objects.new("S%d" % i, li)
    so.rotation_euler = tuple(math.radians(a) for a in rot)
    sc.collection.objects.link(so)

cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.type = "ORTHO"

# ★정직 카메라의 ortho_scale 은 렌더의 **긴 변**에 적용된다.
# 900x1200 세로 프레임에 H*1.15 를 주면 가로 커버리지가 H*0.86 뿐이라
# T 포즈의 팔(폭 = 키 만큼)이 잘린다. 뷰마다 실제 폭·높이를 재서 맞춘다.
ys = [(mesh.matrix_world @ v.co).y for v in mesh.data.vertices]
BW = max(xs) - min(xs)          # 좌우 폭 (팔 벌린 길이)
BD = max(ys) - min(ys)          # 앞뒤 두께
CY = (min(ys) + max(ys)) / 2
print("치수: 폭 %.3f  두께 %.3f  키 %.3f" % (BW, BD, H))
sc.render.film_transparent = True          # 배경 투명

OUT = os.path.join(ROOT, "renders", os.environ.get("OUTDIR", "tpose"))
os.makedirs(OUT, exist_ok=True)
TGT = Vector((CX, CY, CZ))
D = H * 4
# 뷰: (카메라 오프셋, 화면 가로로 보이는 실제 폭)
VIEWS = {"front": (Vector((0, -D, 0)), BW),
         "side": (Vector((-D, 0, 0)), BD),
         "back": (Vector((0, D, 0)), BW)}
MARGIN = 1.12
for nm, (off, wide) in VIEWS.items():
    w_need = wide * MARGIN
    h_need = H * MARGIN
    # 세로 1200 고정, 가로는 실제 비율대로. 잘림 없이 꽉 차게.
    ry = 1200
    rx = max(400, int(round(ry * w_need / h_need)))
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    cd.ortho_scale = max(w_need, h_need)     # 긴 변 기준이므로 큰 쪽을 준다
    cam.location = TGT + off
    dd = TGT - cam.location
    cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "tpose_%s.png" % nm)
    bpy.ops.render.render(write_still=True)
    print("  %-6s %dx%d  ortho %.3f (필요 폭 %.3f)" % (nm, rx, ry, cd.ortho_scale, w_need))
print("DONE", OUT, "H=%.3f" % H)
