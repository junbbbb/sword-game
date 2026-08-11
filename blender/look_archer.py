# -*- coding: utf-8 -*-
"""web/archer.glb 를 임포트해 클립별 대표 프레임을 정면·측면으로 렌더한다.
게임 빌드 말고 여기서 먼저 본다. ★T 포즈로 나오는 클립이 있으면
s11_archer.py 의 fix_paths 가 실패한 것이다(다른 파일에서 가져온 액션의
fcurve 경로가 옛 뼈 이름을 가리키면 아무 뼈도 안 잡혀 바인드 포즈가 나온다).

실행: CLIPS="Walk:7,Run:5" blender -b -P look_archer.py
"""
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
# OUTDIR 로 저장 폴더를 바꾼다(작업 회차별로 나눠 담으려고). 안 주면 예전 자리.
OUT = os.environ.get("OUTDIR") or os.path.join(ROOT, "renders", "history", "v43_archer")
CLIPS = os.environ.get("CLIPS", "Idle:25")
# VIEWS 로 시점을 고른다(front / side / front,side). 한 번에 찍는 장수를 줄이는 용도.
WANT = [v for v in os.environ.get("VIEWS", "front,side").split(",") if v]

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
# GLB 로 다른 파일을 볼 수 있다(수정 전 백업과 나란히 비교할 때).
# 카메라는 아래에서 **바인드 포즈** 메시로 잡으므로 파일이 달라도 같은 자리다.
bpy.ops.import_scene.gltf(
    filepath=os.path.join(ROOT, "web", os.environ.get("GLB", "archer.glb")))

# ★임포터가 뼈를 화면에 그리려고 만드는 Icosphere. glb 안에는 없는 물건이고
# 'glTF_not_exported' 컬렉션에 들어간다. 안 지우면 렌더에 반지름 1 짜리 구가
# 통째로 찍혀 캐릭터를 가린다(키 계산도 오염시킨다. probe_stride 주석 참고).
for o in list(sc.objects):
    if any(c.name == "glTF_not_exported" for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)

arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH")

# ★NOEMIT=1: 재질의 이미시브를 끈다.
# Meshy 재질은 emissiveFactor (1,1,1) + emissiveTexture 에 알베도를 그대로 물려
# 놓는다. 여기에 태양광까지 더해지면 밝은 살결이 통째로 하얗게 날아가
# **피부 톤 그라데이션을 눈으로 못 본다**. 게임(main.js)은 어차피 재질을
# MeshToonMaterial({map}) 로 갈아끼워 이미시브를 버리므로, 끄는 쪽이 실제와 가깝다.
if os.environ.get("NOEMIT") == "1":
    n = 0
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            for key in ("Emission Strength", "Emission Color"):
                s = nd.inputs.get(key) if hasattr(nd, "inputs") else None
                if s is None:
                    continue
                if key == "Emission Strength":
                    s.default_value = 0.0
                else:
                    s.default_value = (0, 0, 0, 1)
                for l in list(m.node_tree.links):
                    if l.to_socket == s:
                        m.node_tree.links.remove(l)
                n += 1
    print("이미시브 차단 소켓 %d개" % n)
ws = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
H = max(p.z for p in ws) - min(p.z for p in ws)
FOOT = min(p.z for p in ws)
CX = (min(p.x for p in ws) + max(p.x for p in ws)) / 2
print("키 %.3f  액션 %s" % (H, [a.name for a in bpy.data.actions]))

w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.06, 0.08, 1)
for nm, en, rot in (("S", 4.0, (58, 0, -30)), ("F", 1.6, (-30, 0, 130))):
    li = bpy.data.lights.new(nm, "SUN")
    li.energy = en
    so = bpy.data.objects.new(nm, li)
    so.rotation_euler = tuple(math.radians(a) for a in rot)
    sc.collection.objects.link(so)
# 바닥판. 발이 뜨는지 파묻히는지 그림자로 본다.
bpy.ops.mesh.primitive_plane_add(size=H * 6, location=(0, 0, 0))

cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.lens = 50
TGT = Vector((CX, 0, FOOT + H * 0.52))
D = H * 2.3
# 캐릭터는 -Y 를 본다. front = 얼굴 쪽에서, side = 왼쪽(-X)에서.
#
# 시점 정의 = (카메라 오프셋, 바라보는 점, 렌즈mm, 가로px, 세로px)
# 렌즈를 None 으로 주면 위에서 정한 50mm 를 쓴다.
#
# ★face  : 얼굴 확대. 텍스처 해상도를 낮추면 얼굴이 제일 먼저 뭉개진다.
#          머리 중심(키의 93%)을 키의 0.22 거리에서 본다. 화면 세로에
#          머리가 거의 꽉 찬다.
# ★game  : 실제 게임 시점. main.js 값을 그대로 옮겼다.
#          PerspectiveCamera(fov 46 세로) / dist 7.0 / pitch 0.28rad /
#          바라보는 점 charH*0.62. 게임은 캐릭터를 키 1.75 로 정규화하므로
#          (CHAR_CFG.basic.h) 거리도 같은 비율로 줄여 화면 크기를 맞춘다.
#          세로 900px 은 실제 브라우저 전체화면 세로와 비슷하다.
GAME_FOV = math.radians(46.0)
GAME_D = 7.0 * (H / 1.75)
GAME_Z = 2.4 * (H / 1.75)   # 휠 줌 하한
GAME_P = 0.28
ALL = {
    "front": (Vector((0, -D, H * 0.10)), TGT, None, 520, 700),
    "side": (Vector((-D, 0, H * 0.10)), TGT, None, 520, 700),
    # ★거리를 더 못 줄인다. 0.22 로 붙였더니 코가 카메라에 훨씬 가까워
    #   원근이 튀면서 이마만 화면에 꽉 찼다(턱이 잘렸다).
    "face": (Vector((0, -H * 0.35, 0)), Vector((CX, 0, FOOT + H * 0.90)),
             None, 520, 700),
    "game": (Vector((math.sin(0.55) * math.cos(GAME_P) * GAME_D,
                     math.cos(0.55) * math.cos(GAME_P) * GAME_D,
                     math.sin(GAME_P) * GAME_D)),
             Vector((CX, 0, FOOT + H * 0.62)), "GAME", 640, 900),
    # ★gamezoom = 게임에서 **가장 가까이** 갈 수 있는 자리.
    #   main.js 휠 줌 하한이 dist 2.4 다(기본 7.0). 플레이어가 캐릭터를 볼 수 있는
    #   최대 크기가 여기고, 텍스처 판단은 이 그림으로 해야 한다.
    #   얼굴만 화면에 꽉 차는 face 시점은 게임에 존재하지 않는 거리다.
    "gamezoom": (Vector((math.sin(0.55) * math.cos(GAME_P) * GAME_Z,
                         math.cos(0.55) * math.cos(GAME_P) * GAME_Z,
                         math.sin(GAME_P) * GAME_Z)),
                 Vector((CX, 0, FOOT + H * 0.62)), "GAME", 640, 900),
}
VIEWS = {k: v for k, v in ALL.items() if k in WANT}
os.makedirs(OUT, exist_ok=True)

for item in CLIPS.split(","):
    name, f = item.split(":")
    act = bpy.data.actions[name]
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass
    sc.frame_set(int(f))
    bpy.context.view_layer.update()
    for vn, (off, tgt, lens, rx, ry) in VIEWS.items():
        if lens == "GAME":
            # 게임과 같은 세로 화각을 쓴다. AUTO 로 두면 가로가 긴 화면에서
            # 화각이 가로에 물려 캐릭터 크기가 달라진다.
            cd.sensor_fit = "VERTICAL"
            cd.angle_y = GAME_FOV
        else:
            cd.sensor_fit = "AUTO"
            cd.lens = lens or 50
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        cam.location = tgt + off
        dd = tgt - cam.location
        cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, "%s_f%02d_%s.png" % (name, int(f), vn))
        bpy.ops.render.render(write_still=True)
print("DONE", OUT)
