# -*- coding: utf-8 -*-
"""양손 파지 점검: 팔이 교차하는가 / 칼이 손을 관통하는가."""
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
kat = bpy.data.objects.get("katana_slayer")
if arm.animation_data: arm.animation_data_clear()
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
ps = CP.Poser(arm, H)
R, U, F = CP.RIGHT, CP.UP, CP.FWD
SWS = H * 0.56
GRIP_A = Vector((-0.20 * SWS, 0, 0))   # 자루 물미
GRIP_B = Vector(( 0.04 * SWS, 0, 0))   # 츠바 바로 앞

def ruf(p, org):
    d = Vector(p) - org
    return (d.dot(R)/H, d.dot(U)/H, d.dot(F)/H)

# --- 칼 로컬에서 손이 자루의 어디를 잡는지 ---
ps.apply(CP.GUARD)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
KM = kat.evaluated_get(dg).matrix_world
KI = KM.inverted()
rh, lh = ps.wpos("r hand"), ps.wpos("l hand")
print("칼 로컬 좌표 (단위: s=%.3f, +X=칼끝)" % SWS)
print("  자루  x %.3f ~ %.3f   (그립 실린더)" % (-0.285*SWS, 0.035*SWS))
print("  츠바  x %.3f" % (0.038*SWS))
print("  칼날  x %.3f 부터" % (0.045*SWS))
print("  오른 손목  x %+.3f   왼 손목  x %+.3f" % ((KI@rh).x, (KI@lh).x))
# 주먹 반지름: 손 정점의 손목에서 최대 거리
VG = {g.index: g.name.lower() for g in mesh.vertex_groups}
ev = mesh.evaluated_get(dg); me = ev.to_mesh()
rad = 0
for v in mesh.data.vertices:
    bw, bn = -1, ""
    for g in v.groups:
        if g.weight > bw: bw, bn = g.weight, VG.get(g.group, "")
    if "r hand" in bn:
        rad = max(rad, ((ev.matrix_world @ me.vertices[v.index].co) - rh).length)
ev.to_mesh_clear()
print("  오른 주먹 반지름 %.3f  ->  츠바가 손목에서 %.3f 앞" % (rad, (0.038*SWS) - (KI@rh).x))
print("  ★칼날 시작(%.3f)이 주먹 반지름(%.3f) 안이면 손을 뚫는다" % (
    (0.045*SWS) - (KI@rh).x, rad))
print()

POSES = [("GUARD", CP.GUARD), ("HG1", CP.HG1), ("HS", CP.HS), ("HR", CP.HR),
         ("XG1", CP.XG1), ("XG2", CP.XG2), ("XE2", CP.XE2), ("XR", CP.XR),
         ("W1", CP.W1), ("S1", CP.S1), ("S2", CP.S2), ("S3", CP.S3)]
print("%-6s | %-7s %-7s | %-7s | %-7s | %s" % (
    "pose", "왼손r", "오른손r", "팔교차", "손-자루축", "판정"))
for nm, p in POSES:
    if p.get("1h"):
        continue
    ps.apply(p)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    org = ps.origin()
    rh, lh = ps.wpos("r hand"), ps.wpos("l hand")
    re_, le = ps.wpos("r forearm"), ps.wpos("l forearm")
    hr, hl = ruf(rh, org), ruf(lh, org)
    er, el = ruf(re_, org), ruf(le, org)
    KM = kat.evaluated_get(dg).matrix_world
    ga, gb = KM @ GRIP_A, KM @ GRIP_B
    ax = (gb - ga).normalized()
    # 손이 자루 축에서 얼마나 벗어났나(수직 거리)
    def off(hp):
        v = hp - ga
        return (v - ax * v.dot(ax)).length / H
    # 팔 교차: 팔꿈치의 좌우가 뒤집혔는가 (오른 팔꿈치가 왼쪽에 있으면 교차)
    cross = "교차!" if er[0] < el[0] else "정상"
    flag = []
    if er[0] < el[0]:
        flag.append("팔 교차")
    if off(lh) > 0.045:
        flag.append("왼손이 자루 밖 %.3f" % off(lh))
    if off(rh) > 0.045:
        flag.append("오른손이 자루 밖 %.3f" % off(rh))
    print("%-6s | %+.3f  %+.3f | %-7s | L%.3f R%.3f | %s" % (
        nm, hl[0], hr[0], cross, off(lh), off(rh),
        "OK" if not flag else " / ".join(flag)))
