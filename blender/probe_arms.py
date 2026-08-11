# -*- coding: utf-8 -*-
"""양팔 관절을 몸통 기준으로 재서 팔뚝이 배 앞을 가로지르는지 본다."""
import bpy, os, sys, math
from mathutils import Vector
ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import importlib, combo_poses as CP
importlib.reload(CP)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "blender", "slayer.blend"))
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH" and not o.name.startswith(("Floor","Plane")))
if arm.animation_data: arm.animation_data_clear()
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs)-min(zs)
ps = CP.Poser(arm, H)
R,U,F = CP.RIGHT, CP.UP, CP.FWD
ps.apply(getattr(CP, os.environ.get("POSE","GUARD")))
bpy.context.view_layer.update()
org = ps.origin()
def ruf(n):
    p = ps.wpos(n) - org
    return (p.dot(R)/H, p.dot(U)/H, p.dot(F)/H)
print("%-12s %7s %7s %7s" % ("bone","r","u","f"))
for n in ["r clavicle","r upperarm","r forearm","r hand",
          "l clavicle","l upperarm","l forearm","l hand"]:
    v = ruf(n)
    print("%-12s %+7.3f %+7.3f %+7.3f" % (n, *v))
le, lh = ruf("l forearm"), ruf("l hand")
re, rh = ruf("r forearm"), ruf("r hand")
import math as m
def horiz(a,b):
    d = (b[0]-a[0], b[1]-a[1], b[2]-a[2])
    return m.degrees(m.atan2(abs(d[1]), m.hypot(d[0], d[2])))
print()
print("왼 팔뚝 기울기 %5.1f도 (0=수평, 90=수직)  좌우이동 %+.3f" % (horiz(le,lh), lh[0]-le[0]))
print("오른팔뚝 기울기 %5.1f도                    좌우이동 %+.3f" % (horiz(re,rh), rh[0]-re[0]))

# 전 포즈 팔뚝 대칭 점검 (양손 파지 포즈만)
print()
print("%-6s %8s %8s %8s %8s" % ("pose","왼좌우","오른좌우","왼기울기","오른기울기"))
for nm in ["GUARD","HG1","HS","HR","XG1","XG2","XE2","XR","W1","S1","S2","S3","REC"]:
    p = getattr(CP, nm, None)
    if p is None or p.get("1h"): continue
    ps.apply(p); bpy.context.view_layer.update()
    o = ps.origin()
    def rf(n):
        q = ps.wpos(n) - o
        return (q.dot(R)/H, q.dot(U)/H, q.dot(F)/H)
    le_, lh_ = rf("l forearm"), rf("l hand")
    re_, rh_ = rf("r forearm"), rf("r hand")
    print("%-6s %+8.3f %+8.3f %7.1f도 %7.1f도" % (
        nm, lh_[0]-le_[0], rh_[0]-re_[0], horiz(le_,lh_), horiz(re_,rh_)))
