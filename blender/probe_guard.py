# -*- coding: utf-8 -*-
"""중단세에서 손이 배에서 얼마나 떨어져 있는지 재고, 팔이 닿는 최대 거리를 찾는다."""
import bpy, os, sys, math
from mathutils import Vector
ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import importlib, combo_poses as CP
importlib.reload(CP)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "blender", "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("Floor","Plane")))
if arm.animation_data: arm.animation_data_clear()
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
ps = CP.Poser(arm, H)
R, U, F = CP.RIGHT, CP.UP, CP.FWD

def ruf(p, org):
    d = Vector(p) - org
    return (d.dot(R)/H, d.dot(U)/H, d.dot(F)/H)

# 배(몸통 앞면) 위치: 척추 높이 ±0.06H 구간 정점 중 가장 앞
ps.apply(CP.GUARD)
bpy.context.view_layer.update()
org = ps.origin()
dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg); me = ev.to_mesh()
best = -9
for v in me.vertices:
    p = ev.matrix_world @ v.co
    r,u,f = ruf(p, org)
    if abs(u) < 0.07 and abs(r) < 0.10 and f > best:
        best = f
ev.to_mesh_clear()
print("배 앞면 f = %+.3f H" % best)

rh = ps.wpos("r hand"); lh = ps.wpos("l hand")
print("현재 GUARD  오른손 %s / 왼손 %s" % (
    tuple(round(x,3) for x in ruf(rh, org)), tuple(round(x,3) for x in ruf(lh, org))))
print("  -> 왼손이 배에서 %.3f H 앞 (사람 기준 주먹 하나 = 약 0.057 H)" % (ruf(lh,org)[2] - best))

# ★손·팔 정점이 몸통보다 앞에 있으면 그게 "배 앞면"으로 잡힌다(값이 손을 따라 움직였다).
# 지배 본이 spine/pelvis 인 정점만 몸통으로 친다.
VG = {g.index: g.name.lower() for g in mesh.vertex_groups}
TORSO = set()
for v in mesh.data.vertices:
    bw, bn = -1, ""
    for g in v.groups:
        if g.weight > bw: bw, bn = g.weight, VG.get(g.group, "")
    if "spine" in bn or "pelvis" in bn:
        TORSO.add(v.index)
print("몸통 정점 %d개" % len(TORSO))

def belly(o):
    dg2 = bpy.context.evaluated_depsgraph_get()
    e2 = mesh.evaluated_get(dg2); m2 = e2.to_mesh()
    b = -9
    for i in TORSO:
        pp = e2.matrix_world @ m2.vertices[i].co
        r_,u_,f_ = ruf(pp, o)
        if abs(u_) < 0.09 and abs(r_) < 0.12 and f_ > b:
            b = f_
    e2.to_mesh_clear()
    return b

print("\n허리각 x 손위치 조합 (목표: 왼손이 배보다 +0.03 H 앞)")
print("%5s %5s %5s | %8s %8s %9s | %s" % ("spX","u","f","배앞면","왼손f","배에서","IK"))
for sx in [6, 2, -2, -6]:
    for f in [0.17, 0.19, 0.21, 0.23]:
        u = 0.07
        b2 = [(k, o, v) for k, o, v in CP.GUARD["b"]]
        b2 = [(k, o, (0.02, u, f) if (k == "r" and o == CP.IK) else v) for k, o, v in b2]
        b2 = [(k, o, sx if (k == "spine" and o == CP.X) else v) for k, o, v in b2]
        pz = {"b": b2, "r": (0,0,0)}
        ps.reach_log = []
        ps.apply(pz)
        bpy.context.view_layer.update()
        o2 = ps.origin()
        bb = belly(o2)
        l = ruf(ps.wpos("l hand"), o2)
        print("%5d %5.2f %5.2f | %+8.3f %+8.3f %+9.3f | %s" % (
            sx, u, f, bb, l[2], l[2]-bb, ("OK" if not ps.reach_log else "NG %.2f" % ps.reach_log[0][1])))
