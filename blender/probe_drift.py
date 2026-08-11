# -*- coding: utf-8 -*-
"""애니메이션을 만든 뒤, 프레임별로 왼 주먹이 자루에서 얼마나 떠는지 찍는다.

키포즈만 맞춰도 소용없다. 게임(three.js)은 정수 프레임이 아니라 **임의 시각**으로
클립을 샘플링하므로, 키와 키 사이가 실제로 화면에 나온다.
실행: SKILL=combo|heavy|wide blender -b -P probe_drift.py
"""
import bpy
import os
import sys
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
importlib.reload(CP)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh_ob = next(o for o in sc.objects if o.type == "MESH"
               and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                          "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
katana = bpy.data.objects.get("katana_slayer")
zs = [(mesh_ob.matrix_world @ v.co).z for v in mesh_ob.data.vertices]
H = max(zs) - min(zs)
ps = CP.Poser(arm, H)
FIST = ps.fist_r.get("l", 0.166)

SK = os.environ.get("SKILL", "heavy")
SEQ = {"combo": CP.SEQ, "heavy": CP.HEAVY_SEQ, "wide": CP.WIDE_SEQ,
       "jump": CP.JUMP_SEQ}[SK]

arm.animation_data_create()
act = bpy.data.actions.new(SK)
arm.animation_data.action = act
try:
    act.slots.new(id_type="OBJECT", name="S")
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
for f, p in SEQ:
    ps.apply(p)
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("location", frame=f)
    arm.keyframe_insert("location", frame=f)

RELOCK = os.environ.get("RELOCK", "1") == "1"
if RELOCK:
    n = CP.relock_grip(ps, SEQ)
    print("파지 재고정: %d 프레임" % n)
    if ps.reach_log:
        print("!! 재고정 중 IK 못닿음:", ps.reach_log[-8:])

# ★게임과 같은 조건으로 재려면 전 채널을 LINEAR 로. glb 는 익스포터가
# 매 프레임(1/30 초) 베이크 + LINEAR 로 굽는다(정지 채널만 STEP 2 샘플).
# 블렌더의 베지어 평가로 재면 게임에 없는 오차를 보게 된다.
if os.environ.get("LINEARIZE", "1") == "1":
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"
    except Exception:
        pass

ONE = set()
for i in range(len(SEQ) - 1):
    (fa, pa), (fb, pb_) = SEQ[i], SEQ[i + 1]
    if pa.get("1h") or pb_.get("1h"):
        ONE.update(range(int(fa), int(fb) + 1))

f0, f1 = SEQ[0][0], SEQ[-1][0]
SUB = int(os.environ.get("SUB", "8"))
dg = bpy.context.evaluated_depsgraph_get()
rows = []
for si in range((f1 - f0) * SUB + 1):
    f = f0 + si / float(SUB)
    sc.frame_set(int(f), subframe=f - int(f))
    KM = katana.evaluated_get(dg).matrix_world
    ax = (KM.to_3x3() @ Vector((1, 0, 0))).normalized()
    g = bpy.data.objects.get("gripK_slayer")
    ge = g.evaluated_get(dg)
    gm = ge.to_mesh()
    pts = [ge.matrix_world @ v.co for v in gm.vertices]
    o = sum(pts, Vector((0, 0, 0))) / len(pts)   # 자루 중심축 위의 점
    ge.to_mesh_clear()
    lp = ps.palm_world("l")
    v = lp - o
    d = (v - ax * v.dot(ax)).length
    rows.append((f, d, d / FIST, f in ONE or int(f) in ONE))

print("\n=== %s 왼 주먹 자루 이탈 (주먹반지름 %.3f, %d분할) ===" % (SK, FIST, SUB))
tw = [r for r in rows if not r[3]]
tw.sort(key=lambda r: -r[1])
print("최악 12 프레임 (한손 구간 제외):")
for f, d, k, _ in tw[:12]:
    print("   f%-7.3f 이탈 %.4f = 주먹 %.2f 개" % (f, d, k))
print("정수 프레임만: 최대 %.4f (주먹 %.2f)"
      % (max((r[1] for r in rows if not r[3] and abs(r[0] - round(r[0])) < 1e-6), default=0),
         max((r[2] for r in rows if not r[3] and abs(r[0] - round(r[0])) < 1e-6), default=0)))
print("사이 프레임 포함: 최대 %.4f (주먹 %.2f)"
      % (max((r[1] for r in tw), default=0), max((r[2] for r in tw), default=0)))
