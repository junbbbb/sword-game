# -*- coding: utf-8 -*-
"""뒷면이 사라지는가. 컬링 ON/OFF 를 같은 구도로 굽어 화소 단위로 비교한다.

    blender -b -P blender/probe_backface.py        (OUT 폴더에 *_both / *_cull)
    -> 이어서 두 장을 PIL 로 빼서 다른 화소 수를 센다

★왜 필요한가
  게임(main.js loadChar)은 재질을 **MeshToonMaterial({map}) 로 통째로 갈아끼운다.**
  three.js 기본이 FrontSide 라 glb 의 doubleSided 플래그는 버려진다. 옷처럼 경계가
  열린 메시를 얹으면 각도에 따라 안쪽 면이 통째로 사라질 수 있다.
  basic2 의 옷(2026-08-11)은 이 검사에서 81만 화소 중 151~525개(0.02~0.06%)만
  달라서 그대로 뒀다. 새 옷·망토·깃발을 얹는 사람은 **먼저 이걸 돌려라.**
  차이가 크면 답은 solidify(두께 주기)다 - 면을 복사해 뒤집으면 z-fighting 이 난다.
"""
import bpy, os, math
from mathutils import Vector
OUT = os.environ.get("OUT") or "/tmp/probe_backface"
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
GLB = os.environ.get("GLB") or "/Users/lbj/Documents/gameproject/web/basic2.glb"
bpy.ops.import_scene.gltf(filepath=GLB)
for o in list(bpy.data.objects):
    if any(c.name == "glTF_not_exported" for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = bpy.data.objects["char1"]
cloth = bpy.data.objects["cloth1"]
for o in sc.objects:
    if o.type == "MESH" and o.name.startswith("SW_") and o.name != "SW_baekah":
        o.hide_render = True
BW = [body.matrix_world @ v.co for v in body.data.vertices]
H = max(p.z for p in BW) - min(p.z for p in BW)
FOOT = min(p.z for p in BW)
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE")
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x = sc.render.resolution_y = 900
wd = bpy.data.worlds.new("W"); sc.world = wd; wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs[0].default_value = (0.06, 0.065, 0.08, 1)
for eul, en in (((58, 0, -30), 4.0), ((-40, 0, 130), 1.8)):
    li = bpy.data.lights.new("S", "SUN"); li.energy = en
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = tuple(math.radians(a) for a in eul)
    sc.collection.objects.link(so)
cd = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam); sc.camera = cam
CEN = Vector((0, 0, FOOT + H * 0.60))


def use(act):
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        s = list(getattr(act, "slots", []))
        if s:
            arm.animation_data.action_slot = s[0]
    except Exception:
        pass


# 롤식 쿼터뷰(고도 약 50도). 게임 카메라와 같은 계열의 각도에서 본다
D = H * 1.7
for nm, ang, clip, t in (("front", 0, "Idle", 0.0), ("back", 180, "Idle", 0.0),
                         ("run", 30, "Run", 0.4), ("attack", 20, "Attack", 0.6)):
    act = bpy.data.actions.get(clip)
    use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    sc.frame_set(int(f0 + (f1 - f0) * t))
    bpy.context.view_layer.update()
    a = math.radians(ang)
    eye = CEN + Vector((math.sin(a) * D * 0.66, -math.cos(a) * D * 0.66, D * 0.75))
    cam.location = eye
    cam.rotation_euler = (CEN - eye).to_track_quat("-Z", "Y").to_euler()
    for cull in (False, True):
        for m in bpy.data.materials:
            m.use_backface_culling = cull
        sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (nm, "cull" if cull else "both"))
        bpy.ops.render.render(write_still=True)
print("DONE")
