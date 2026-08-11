# -*- coding: utf-8 -*-
"""Meshy 캐릭터(glb 3개)를 게임용 단일 glb 로 합친다.

받은 것
  Walking / Running / Attack 세 파일. **각각 메시를 통째로 들고 있다**(7.9MB x 3).
  뼈대는 셋 다 동일하므로 메시는 하나만 두고 액션만 모은다.

★뼈 이름을 Bip001 규칙으로 바꾼다
  우리 포즈 시스템(combo_poses.Poser.pb)과 게임 코드(main.js)가 전부
  "r hand", "l thigh" 같은 **부분 문자열**로 뼈를 찾는다.
  Meshy 이름(RightHand, LeftUpLeg)은 안 잡힌다.
  이름만 바꿔주면 지금까지 만든 포즈·스킬·리타게터가 **코드 수정 없이** 그대로 돈다.

★척추 주의: Meshy 는 Spine/Spine01/Spine02 세 개다. 우리 pb("spine") 은 첫 일치를
  반환하므로 셋 다 'spine' 을 넣으면 엉뚱한 걸 잡는다. 위 두 개는 Chest 로 부른다.
실행: blender --background --python s9_meshy.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming/meshy1/Meshy_AI_Crimson_Centurion_biped")
WEB = os.path.join(ROOT, "web")
BASE = "Meshy_AI_Crimson_Centurion_biped_Animation_%s_withSkin.glb"

# Meshy 이름 -> 우리 규칙. 순서 중요(긴 것부터 매칭)
RENAME = [
    ("LeftToeBase", "Bip001 L Toe0"), ("RightToeBase", "Bip001 R Toe0"),
    ("LeftUpLeg", "Bip001 L Thigh"), ("RightUpLeg", "Bip001 R Thigh"),
    ("LeftForeArm", "Bip001 L Forearm"), ("RightForeArm", "Bip001 R Forearm"),
    ("LeftShoulder", "Bip001 L Clavicle"), ("RightShoulder", "Bip001 R Clavicle"),
    ("LeftHand", "Bip001 L Hand"), ("RightHand", "Bip001 R Hand"),
    ("LeftFoot", "Bip001 L Foot"), ("RightFoot", "Bip001 R Foot"),
    ("LeftLeg", "Bip001 L Calf"), ("RightLeg", "Bip001 R Calf"),
    ("LeftArm", "Bip001 L UpperArm"), ("RightArm", "Bip001 R UpperArm"),
    ("Spine02", "Bip001 Chest2"), ("Spine01", "Bip001 Chest"),
    ("Spine", "Bip001 Spine"),
    ("Hips", "Bip001 Pelvis"),
    ("head_end", "Bip001 HeadNub"), ("headfront", "Bip001 HeadFront"),
    ("Head", "Bip001 Head"), ("neck", "Bip001 Neck"),
]

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene


def imp(tag):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, BASE % tag))
    return [o for o in sc.objects if o.name not in before]


# ---- 1) 걷기를 기준으로 삼는다 ----
objs = imp("Walking")
arm = next(o for o in objs if o.type == "ARMATURE")
mesh = next(o for o in objs if o.type == "MESH")
print("기준 리그:", arm.name, "본", len(arm.data.bones), "/ 메시", mesh.name,
      len(mesh.data.polygons), "면")

acts = {}
if arm.animation_data and arm.animation_data.action:
    acts["Walk"] = arm.animation_data.action

# ---- 2) 나머지는 액션만 가져오고 오브젝트는 버린다 ----
for tag, name in (("Running", "Run"), ("Attack", "Attack")):
    got = imp(tag)
    a2 = next(o for o in got if o.type == "ARMATURE")
    if a2.animation_data and a2.animation_data.action:
        act = a2.animation_data.action
        act.use_fake_user = True
        acts[name] = act
    for o in got:
        bpy.data.objects.remove(o, do_unlink=True)
print("모은 액션:", list(acts))

# ---- 3) 뼈 이름 변경 ----
n = 0
for old, new in RENAME:
    b = arm.data.bones.get(old)
    if b:
        b.name = new
        n += 1
print("뼈 이름 변경 %d개" % n)
print("  ->", [b.name for b in arm.data.bones])

# ★★가장 중요한 함정
# Blender 는 뼈 이름을 바꿀 때 **그 아마추어에 현재 붙어 있는 액션**의 데이터 경로만
# 따라 고친다. Running/Attack 은 **다른 아마추어**에서 가져온 뒤 그 아마추어를
# 지웠으므로, fcurve 경로가 아직 pose.bones["RightHand"] 를 가리킨다.
# 그대로 내보내면 그 클립을 재생할 때 **아무 뼈도 안 잡혀 T 포즈**가 된다.
# (증상: 걷기는 되는데 Shift 달리기 누르면 T 포즈)
NAMEMAP = dict(RENAME)


def fix_paths(act):
    fcs = []
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    fcs.extend(cb.fcurves)
    except Exception:
        pass
    if not fcs:
        fcs = list(act.fcurves)
    n = 0
    for fc in fcs:
        dp = fc.data_path
        if '"' not in dp:
            continue
        old_b = dp.split('"')[1]
        new_b = NAMEMAP.get(old_b)
        if new_b and new_b != old_b:
            fc.data_path = dp.replace('"%s"' % old_b, '"%s"' % new_b, 1)
            n += 1
    return n


for nm, act in acts.items():
    act.name = nm
    act.use_fake_user = True
    print("  액션 %-8s fcurve 경로 %d개 수정" % (nm, fix_paths(act)))

# ---- 4) Idle 만들기 ----
# Meshy 가 Idle 을 안 줬다. 걷기 첫 프레임을 기준으로 숨쉬기 루프를 만든다.
arm.animation_data.action = acts["Walk"]
try:
    slots = list(getattr(acts["Walk"], "slots", []))
    if slots:
        arm.animation_data.action_slot = slots[0]
except Exception:
    pass
sc.frame_set(int(acts["Walk"].frame_range[0]))
bpy.context.view_layer.update()
base_pose = {b.name: (b.location.copy(), b.rotation_quaternion.copy())
             for b in arm.pose.bones}

arm.animation_data_clear()
arm.animation_data_create()
idle = bpy.data.actions.new("Idle")
idle.use_fake_user = True
arm.animation_data.action = idle
try:
    slot = idle.slots.new(id_type="OBJECT", name="S")
    arm.animation_data.action_slot = slot
except Exception:
    pass
SPINE = arm.pose.bones.get("Bip001 Spine")
for f, amp in ((1, 0.0), (25, 1.0), (50, 0.0)):
    for b in arm.pose.bones:
        loc, rot = base_pose[b.name]
        b.location = loc
        b.rotation_mode = "QUATERNION"
        b.rotation_quaternion = rot
    if SPINE:
        # 아주 작은 숨쉬기(가슴 2도). 크면 흔들거린다.
        SPINE.rotation_quaternion = (
            SPINE.rotation_quaternion @ Matrix.Rotation(
                math.radians(2.0 * amp), 4, "X").to_quaternion())
    bpy.context.view_layer.update()
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("location", frame=f)
acts["Idle"] = idle
print("Idle 생성 (50프레임 숨쉬기)")

# ---- 5) 모든 액션이 익스포트되게 남긴다 ----
for a in bpy.data.actions:
    a.use_fake_user = True
KEEP = set(acts)
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
print("최종 액션:", [a.name for a in bpy.data.actions])

# ---- 6) 크기 진단 ----
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
tri = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print("키 %.3f  삼각형 %d" % (H, tri))

OUT = os.path.join(WEB, "tank.glb")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT, export_format="GLB", use_selection=False,
    export_animations=True, export_animation_mode="ACTIONS",
    export_nla_strips=False, export_bake_animation=True,
    export_frame_range=False, export_yup=True)
print("EXPORTED", OUT, os.path.getsize(OUT))
