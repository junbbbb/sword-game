# -*- coding: utf-8 -*-
"""방패 캐리 자세를 고치기 전에 실측한다. 아무것도 안 만들고 안 내보낸다.

재는 것
  1) 아마추어 matrix_world 의 스케일(★pb.matrix 에 월드 행렬을 그대로 쓰면 손이
     39배가 되는 사고가 있었다. A2W 에 스케일이 있는지부터 확인한다)
  2) 왼팔 체인의 부모/connect 여부/레스트 길이
  3) Idle f17 왼팔 3뼈의 **아마추어 공간** 행렬(기준 자세가 될 값)
  4) Walk/Run 전 프레임의 방패 최고점 z vs 어깨 z (고치기 전 기준선)
  5) Run 에서 가슴이 얼마나 앞으로 기우는지(절대 고정 vs 부모상대 고정 판단용)

★방패 최고점은 depsgraph 로 메시를 굽지 않고 계산한다.
  방패는 손 뼈에 웨이트 1.0 강체이므로 world = M_pose(hand) @ M_rest(hand)^-1 @ v_rest
  가 정확히 성립한다. 프레임마다 7MB 몸통 메시를 평가하지 않아 훨씬 빠르다.

실행: blender -b -P probe_carry.py
"""
import bpy
import os
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")
SRC = os.environ.get("SRC", os.path.join(WEB, "tank.glb"))

L_UP, L_FORE, L_HAND = ("Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand")
IDLE_F = 17

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=SRC)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH" and o.name.startswith("char"))
shield = next((o for o in sc.objects if o.name.startswith("SH_")), None)
print("소스:", SRC)
print("액션:", [a.name for a in bpy.data.actions])
print("방패:", shield.name if shield else "없음")

A2W = arm.matrix_world
loc, rot, scl = A2W.decompose()
print("[A2W] 위치 %s 회전(w,x,y,z) %s 스케일 %s"
      % (tuple(round(v, 4) for v in loc),
         tuple(round(v, 4) for v in rot),
         tuple(round(v, 5) for v in scl)))

print("=== 왼팔 체인 ===")
for nm in (L_UP, L_FORE, L_HAND):
    b = arm.data.bones[nm]
    print("  %-20s parent=%-20s connect=%s len=%.4f"
          % (nm, b.parent.name if b.parent else "-", b.use_connect, b.length))

if arm.animation_data is None:
    arm.animation_data_create()
arm.data.pose_position = "POSE"


def use(act_name):
    act = bpy.data.actions[act_name]
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception as ex:
        print("action_slot 실패:", ex)
    return act


def show(tag, m):
    e = m.to_euler()
    s = tuple(round(m.col[i].to_3d().length, 4) for i in range(3))
    print("   %-20s pos(%.4f,%.4f,%.4f) euler(%.1f,%.1f,%.1f)도 스케일%s"
          % (tag, m.translation.x, m.translation.y, m.translation.z,
             math.degrees(e.x), math.degrees(e.y), math.degrees(e.z), s))


# ---- 기준 자세(Idle f17) ----
use("Idle")
sc.frame_set(IDLE_F)
bpy.context.view_layer.update()
print("=== Idle f%d 왼팔 (아마추어 공간) ===" % IDLE_F)
for nm in (L_UP, L_FORE, L_HAND):
    show(nm, arm.pose.bones[nm].matrix)
REF_HAND = arm.pose.bones[L_HAND].matrix.copy()

# ---- 방패 레스트 정점(있으면) ----
SH_V = None
if shield:
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    HAND_REST_INV = (A2W @ arm.pose.bones[L_HAND].matrix).inverted()
    SH_V = [shield.matrix_world @ v.co for v in shield.data.vertices]
    SH_LOCAL = [HAND_REST_INV @ p for p in SH_V]      # 손 뼈 기준 로컬
    arm.data.pose_position = "POSE"
    bpy.context.view_layer.update()
    print("방패 정점 %d개, 레스트 z %.3f~%.3f"
          % (len(SH_V), min(p.z for p in SH_V), max(p.z for p in SH_V)))


def shield_top(hand_world):
    """현재 손 뼈 월드 행렬에서 방패 최고점 z."""
    return max((hand_world @ p).z for p in SH_LOCAL)


print("=== 클립별 방패 최고점 z vs 어깨 z (고치기 전) ===")
for clip in ("Walk", "Run"):
    act = use(clip)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    print("[%s] 프레임 %d~%d" % (clip, f0, f1))
    worst = None
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        hw = A2W @ arm.pose.bones[L_HAND].matrix
        sl = (A2W @ arm.pose.bones[L_UP].matrix).translation
        sr = (A2W @ arm.pose.bones["Bip001 R UpperArm"].matrix).translation
        sho = (sl.z + sr.z) / 2
        hd = (A2W @ arm.pose.bones["Bip001 Head"].matrix).translation
        top = shield_top(hw) if SH_V else float("nan")
        rows.append((f, top, sho, hd.z, top - sho))
        if worst is None or (top - sho) > worst[4]:
            worst = rows[-1]
    for r in rows:
        mark = " <<<" if r is worst else ""
        print("   f%02d 방패최고 %.3f  어깨 %.3f  머리 %.3f  차이 %+6.1fcm%s"
              % (r[0], r[1], r[2], r[3], r[4] * 100, mark))
    print("   [%s] 최악 f%02d, 어깨보다 %+.1fcm" % (clip, worst[0], worst[4] * 100))

# ---- Run 에서 몸통이 얼마나 기우는지 ----
print("=== Run 몸통 기울기(절대고정 vs 부모상대 판단용) ===")
use("Run")
act = bpy.data.actions["Run"]
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
for f in range(f0, f1 + 1, max(1, (f1 - f0) // 6)):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    ch = arm.pose.bones.get("Bip001 Chest2") or arm.pose.bones["Bip001 Chest"]
    cl = arm.pose.bones.get("Bip001 L Clavicle")
    e = ch.matrix.to_euler()
    ce = cl.matrix.to_euler() if cl else None
    print("   f%02d 가슴 euler(%.1f,%.1f,%.1f)  쇄골 euler%s"
          % (f, math.degrees(e.x), math.degrees(e.y), math.degrees(e.z),
             ("(%.1f,%.1f,%.1f)" % (math.degrees(ce.x), math.degrees(ce.y),
                                    math.degrees(ce.z))) if ce else "-"))

# ---- 액션 fcurve 구조(슬롯형인지, 키가 촘촘한지) ----
print("=== 액션 fcurve 구조 ===")
for a in bpy.data.actions:
    fcs = []
    try:
        for lay in a.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    fcs.extend(cb.fcurves)
    except Exception:
        pass
    src = "slotted" if fcs else "legacy"
    if not fcs:
        fcs = list(a.fcurves)
    sample = [fc for fc in fcs if L_UP in fc.data_path]
    print("  %-8s %s fcurve %d개, 슬롯 %d, L UpperArm 채널 %d, 키수 %s"
          % (a.name, src, len(fcs), len(list(getattr(a, "slots", []))),
             len(sample), [len(fc.keyframe_points) for fc in sample[:4]]))
print("PROBE DONE")
