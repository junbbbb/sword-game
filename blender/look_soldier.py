# -*- coding: utf-8 -*-
"""web/soldier.glb 를 그대로 읽어 클립별 대표 프레임을 정면/측면으로 렌더한다.
게임 빌드 말고 여기서 먼저 눈으로 본다(look_run.py / look_shield.py 와 같은 취지).

보는 것
  1) T 포즈로 나오는 클립이 있나  -> 있으면 fcurve 데이터 경로 문제다(주된 실패 모드)
  2) 텍스처가 입혀졌나            -> 회색 무지면 실패
  3) 발이 바닥에 붙었나           -> 바닥 평면을 깔아둔다

실행: CLIP=Walk FRAMES=1,8,20 VIEWS=side blender -b -P blender/look_soldier.py
저장: renders/history/v45_soldier/  (OUTDIR 로 폴더 이름만 바꿀 수 있다)
★한 번에 3장 이하로 끊어서 돌린다.
"""
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")
# 버전별로 증거를 남기려고 폴더를 갈아끼운다(기본은 예전 v45).
OUT = os.path.join(ROOT, "renders", "history",
                   os.environ.get("OUTDIR", "v45_soldier"))
os.makedirs(OUT, exist_ok=True)

CLIP = os.environ.get("CLIP", "Idle")
FRAMES = [int(x) for x in os.environ.get("FRAMES", "1").split(",") if x != ""]
VIEWS = [v for v in os.environ.get("VIEWS", "front,side").split(",") if v]
TAG = os.environ.get("TAG", "")

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
# ★glb 는 30fps 로 구웠다. 빈 씬 기본값 24 로 두면 임포터가 프레임을 리샘플해서
#   프레임 번호가 어긋난다(26프레임 클립이 20프레임이 된다).
sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=os.path.join(WEB, "soldier.glb"))
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH"
            and not any(c.name == "glTF_not_exported" for c in o.users_collection))
print("메시:", body.name, "머티리얼:",
      [(ms.material.name if ms.material else None) for ms in body.material_slots])
for m in bpy.data.materials:
    imgs = [n.image.name for n in m.node_tree.nodes
            if n.type == "TEX_IMAGE" and n.image]
    print("  머티리얼 %s 텍스처 %s" % (m.name, imgs))
print("액션:", sorted(a.name for a in bpy.data.actions))

ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                    else "BLENDER_EEVEE")
sc.view_settings.view_transform = "Standard"

w = bpy.data.worlds.new("W")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.18, 0.21, 1)
sc.world = w
# 바닥 - 발이 뜨는지 잠기는지 보려면 있어야 한다
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
fl = bpy.context.active_object
fl.name = "Floor"
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.30, 0.32, 0.35, 1)
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
TGT = Vector((0, 0, H * 0.50))
D = H * 2.15
# glTF 규약: 정면 = -Y, 위 = +Z, 캐릭터의 오른쪽 = -X
OFF = {
    "front": Vector((0, -D, H * 0.10)),
    "back": Vector((0, D, H * 0.10)),
    "side": Vector((-D, 0, H * 0.06)),           # 캐릭터의 오른쪽에서
    "left": Vector((D, 0, H * 0.06)),
    "q": Vector((-D * 0.66, -D * 0.66, H * 0.18)),
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
    # ★슬롯을 안 걸면 액션이 조용히 아무 일도 안 한다 -> 바인드(T) 포즈로 보인다.
    #   이건 glb 문제가 아니라 렌더 스크립트 문제이므로 헷갈리지 않게 로그를 남긴다
    try:
        slots = list(getattr(act, "slots", []))
        print("슬롯 %d개 -> %s" % (len(slots), slots[0].name_display if slots else "없음"))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception as ex:
        print("action_slot 실패:", ex)
    print("클립 %s 프레임범위 %s" % (CLIP, tuple(int(x) for x in act.frame_range)))

n = 0
for f in FRAMES:
    sc.frame_set(f)
    bpy.context.view_layer.update()
    # 발 높이를 숫자로도 남긴다(렌더만 보면 몇 cm 뜬 건 안 보인다)
    tz = []
    for s in ("L", "R"):
        b = arm.pose.bones.get("Bip001 %s Toe0" % s)
        if b:
            tz.append((arm.matrix_world @ b.matrix).translation.z)
    print("  f%03d 발끝 z = %s" % (f, [round(x, 4) for x in tz]))
    for nm in VIEWS:
        cam.location = TGT + OFF[nm]
        d = TGT - cam.location
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(OUT, "%s%s_f%03d_%s.png" % (TAG, CLIP, f, nm))
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        n += 1
        print("RENDERED", path)
print("DONE %d장" % n)
