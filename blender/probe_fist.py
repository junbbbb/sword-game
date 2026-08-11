# -*- coding: utf-8 -*-
"""주먹 메시의 로컬 기하를 잰다.

파지를 제대로 만들려면 두 가지 상수가 필요하다.
  1) palm_local  : 손 본 로컬에서 주먹 중심이 어디인가 (칼은 손목이 아니라 여기 붙는다)
  2) fist_axis   : 주먹의 '구멍' 방향. 자루가 이 축으로 통과해야 쥔 것처럼 보인다
둘 다 리그 고정값이므로 한 번 재서 combo_poses 에 상수로 넣는다.
실행: blender -b slayer.blend -P probe_fist.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import combo_poses as CP

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh_ob = next(o for o in sc.objects if o.type == "MESH"
               and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                          "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
katana = bpy.data.objects.get("katana_slayer")
A2W = arm.matrix_world
zs = [(mesh_ob.matrix_world @ v.co).z for v in mesh_ob.data.vertices]
H = max(zs) - min(zs)

# 손 본이 지배하는 정점
vgn = {g.index: g.name for g in mesh_ob.vertex_groups}
HAND = {"r": [], "l": []}
for v in mesh_ob.data.vertices:
    best, bw = None, -1
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, vgn.get(g.group, "")
    if not best:
        continue
    b = best.lower()
    if "r hand" in b:
        HAND["r"].append(v.index)
    elif "l hand" in b:
        HAND["l"].append(v.index)

# 포즈 리셋 상태(레스트에 가까움)에서 잰다
P = CP.Poser(arm, H)
P.reset()
bpy.context.view_layer.update()

dg = bpy.context.evaluated_depsgraph_get()
ev = mesh_ob.evaluated_get(dg)
me = ev.to_mesh()

print("\n=== 주먹 로컬 기하 (H=%.4f) ===" % H)
res = {}
for s in ("r", "l"):
    hb = P.pb("%s hand" % s)
    M = (A2W @ hb.matrix)
    Minv = M.inverted()
    pts = [Minv @ (ev.matrix_world @ me.vertices[i].co) for i in HAND[s]]
    c = sum(pts, Vector((0, 0, 0))) / len(pts)
    # 공분산 → 주축
    cov = [[0.0] * 3 for _ in range(3)]
    for p in pts:
        d = p - c
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]
    Mc = Matrix(cov)
    # 파워법으로 최대 고유벡터
    v = Vector((1, 0.3, 0.2)).normalized()
    for _ in range(80):
        v = (Mc @ v)
        if v.length < 1e-12:
            break
        v.normalize()
    lam = (Mc @ v).length / max(1e-12, len(pts))
    # 최소 고유벡터(= 손바닥 두께 방향) : 디플레이션
    Md = Mc - Matrix([[v[i] * v[j] * (Mc @ v).dot(v) for j in range(3)] for i in range(3)])
    w = Vector((0.2, 1, 0.3)).normalized()
    for _ in range(80):
        w = (Md @ w)
        if w.length < 1e-12:
            break
        w.normalize()
    ext = [max(abs((p - c)[k]) for p in pts) for k in range(3)]
    print("%s hand: 정점 %d" % (s, len(pts)))
    print("   palm_local  = (%.4f, %.4f, %.4f)   |len| %.4f = %.4f H"
          % (c.x, c.y, c.z, c.length, c.length / H))
    print("   주축1(긴쪽) = (%.3f, %.3f, %.3f)" % (v.x, v.y, v.z))
    print("   주축2       = (%.3f, %.3f, %.3f)" % (w.x, w.y, w.z))
    print("   로컬 반경   = (%.3f, %.3f, %.3f)" % tuple(ext))
    res[s] = (c, v, w)

ev.to_mesh_clear()

# 칼날 로컬 방향과 오른 주먹 주축의 관계
bd = CP.BLADE_LOCAL
for s in ("r", "l"):
    c, v, w = res[s]
    a1 = math.degrees(math.acos(max(-1, min(1, abs(v.dot(bd))))))
    a2 = math.degrees(math.acos(max(-1, min(1, abs(w.dot(bd))))))
    print("%s: 칼날축 vs 주축1 %.1f도, vs 주축2 %.1f도" % (s, a1, a2))

# 실제 자루가 오른 주먹 로컬 어디를 지나는가
bpy.context.view_layer.update()
hb = P.pb("r hand")
M = (A2W @ hb.matrix)
Minv = M.inverted()
ax = Minv.to_3x3() @ (katana.matrix_world.to_3x3() @ Vector((1, 0, 0)))
org = Minv @ katana.matrix_world.translation
print("\n칼 원점(손 로컬) = (%.4f, %.4f, %.4f)  축 = (%.3f, %.3f, %.3f)"
      % (org.x, org.y, org.z, ax.normalized().x, ax.normalized().y, ax.normalized().z))
c = res["r"][0]
t = (c - org).dot(ax.normalized())
print("오른 주먹 중심의 자루축 이탈 = %.4f" % ((c - org) - ax.normalized() * t).length)
