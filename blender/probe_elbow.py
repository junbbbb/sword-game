# -*- coding: utf-8 -*-
"""특정 구간에서 왼팔 관절이 프레임 사이에 얼마나 튀는지 본다.
사이 프레임 이탈의 원인이 '동작이 빨라서'인지 '팔꿈치가 뒤집혀서'인지 가른다.
실행: SKILL=heavy F0=25 F1=30 blender -b -P probe_elbow.py
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
SEQ = {"combo": CP.SEQ, "heavy": CP.HEAVY_SEQ, "wide": CP.WIDE_SEQ}[SK]
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
CP.relock_grip(ps, SEQ)
try:
    for lay in act.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "LINEAR"
except Exception:
    pass

F0 = int(os.environ.get("F0", "25"))
F1 = int(os.environ.get("F1", "30"))
SUB = int(os.environ.get("SUB", "4"))
dg = bpy.context.evaluated_depsgraph_get()
print("\n=== %s f%d~%d 왼팔 추적 (모두 H 단위, 몸통 기준) ===" % (SK, F0, F1))
print(" 프레임 | 팔꿈치(r,u,f)      | 손목(r,u,f)        | 칼끝(r,u,f)        | 이탈(주먹)")
prev = None
for si in range((F1 - F0) * SUB + 1):
    f = F0 + si / float(SUB)
    sc.frame_set(int(f), subframe=f - int(f))
    org = ps.origin()

    def ruf(p):
        d = p - org
        return (d.dot(CP.RIGHT) / H, d.dot(CP.UP) / H, d.dot(CP.FWD) / H)

    el = ps.wpos("l forearm")
    wr = ps.wpos("l hand")
    KM = katana.evaluated_get(dg).matrix_world
    ax = (KM.to_3x3() @ Vector((1, 0, 0))).normalized()
    tip = KM @ Vector((0.86 * H * 0.56, 0, 0))
    g = bpy.data.objects.get("gripK_slayer")
    ge = g.evaluated_get(dg)
    gm = ge.to_mesh()
    pts = [ge.matrix_world @ v.co for v in gm.vertices]
    o = sum(pts, Vector((0, 0, 0))) / len(pts)
    ge.to_mesh_clear()
    lp = ps.palm_world("l")
    v = lp - o
    dev = (v - ax * v.dot(ax)).length / FIST
    e, w, t = ruf(el), ruf(wr), ruf(tip)
    jump = ""
    if prev is not None:
        jump = " 팔꿈치이동 %.3f" % ((el - prev).length / H)
    prev = el.copy()
    print(" %6.2f | %5.2f %5.2f %5.2f | %5.2f %5.2f %5.2f | %5.2f %5.2f %5.2f | %.2f%s"
          % (f, e[0], e[1], e[2], w[0], w[1], w[2], t[0], t[1], t[2], dev, jump))
