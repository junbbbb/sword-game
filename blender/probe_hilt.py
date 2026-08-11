# -*- coding: utf-8 -*-
"""두 손이 실제로 '자루'를 쥐고 있는지 실측한다.

지금까지 파지 검증은 전부 **본 좌표(손목 관절)** 로만 했다. 그런데 칼은
손목이 아니라 **손바닥 중심**에 붙어 있고(convert_to_slayer 의 palm_local),
그래서 손목이 자루 축 위에 있어도 주먹은 자루에서 떨어져 있을 수 있다.
여기서는 메시(주먹 정점)와 자루 실린더를 직접 재서
  - 주먹 중심이 자루 축에서 얼마나 벗어났는지(수직거리)
  - 자루 어느 지점을 쥐고 있는지(물미 0 ~ 츠바 1)
를 뽑는다.

실행: SKILL=guard|combo|heavy|wide blender -b slayer.blend -P probe_hilt.py
"""
import bpy
import os
import sys
import math
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
P = CP.Poser(arm, H)

# ---- 손 정점 인덱스 (본 지배도 최대 기준) ----
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


def palms():
    """평가된(스킨 변형 적용) 메시에서 좌우 주먹 중심·반지름."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh_ob.evaluated_get(dg)
    me = ev.to_mesh()
    out = {}
    for s, idx in HAND.items():
        pts = [ev.matrix_world @ me.vertices[i].co for i in idx]
        c = sum(pts, Vector((0, 0, 0))) / len(pts)
        rad = max((p - c).length for p in pts)
        out[s] = (c, rad, len(pts))
    ev.to_mesh_clear()
    return out


def hilt():
    """자루 축(월드). 반환: (물미점, 츠바쪽 끝점, 단위방향, 자루반지름)"""
    bpy.context.view_layer.update()
    ax = (katana.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
    g = bpy.data.objects.get("gripK_slayer")
    dg = bpy.context.evaluated_depsgraph_get()
    ev = g.evaluated_get(dg)
    me = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in me.vertices]
    # ★축 위의 점은 반드시 **무게중심**으로. 아무 정점이나 쓰면 실린더 '표면'을
    # 따라가는 선이 되어 반지름만큼 통째로 어긋난 축을 재게 된다.
    o = sum(pts, Vector((0, 0, 0))) / len(pts)
    ts = [(p - o).dot(ax) for p in pts]
    lo, hi = min(ts), max(ts)
    rad = max((p - (o + ax * ((p - o).dot(ax)))).length for p in pts)
    ev.to_mesh_clear()
    return o + ax * lo, o + ax * hi, ax, rad


def report(name, pose):
    P.apply(pose["b"] if isinstance(pose, dict) else pose)  # placeholder
    return


def check(name, pose):
    P.apply(pose)
    bpy.context.view_layer.update()
    a, b, ax, grad = hilt()
    L = (b - a).length
    pm = palms()
    line = ["%-6s 자루 길이 %.3f (H %.3f = %.3f H) 반지름 %.3f" % (name, L, H, L / H, grad)]
    for s in ("r", "l"):
        if pose.get("1h") and s == "l":
            line.append("    %s: (한손 포즈, 생략)" % s)
            continue
        c, rad, n = pm[s]
        t = (c - a).dot(ax)
        perp = (c - a) - ax * t
        u = t / L
        # 주먹이 자루를 감싸려면 중심이 축에서 주먹반경 안, 즉 대략 0 에 가까워야 한다.
        verdict = "OK " if (perp.length < rad * 0.55 and -0.05 <= u <= 1.05) else "NG "
        line.append("    %s%s 주먹 r=%.3f | 축이탈 %.4f (=%.2f 주먹) | 자루위치 %.2f (0물미 1츠바)"
                    % (verdict, s, rad, perp.length, perp.length / rad, u))
    # 손목 본과 주먹 중심의 차이 (파지 계산이 손목을 쓰면 이만큼 틀어진다)
    for s in ("r", "l"):
        w = P.wpos("%s hand" % s)
        c = pm[s][0]
        d = c - w
        line.append("    %s 손목→주먹중심 %.4f (%.3f H)  축직교성분 %.4f"
                    % (s, d.length, d.length / H, (d - ax * d.dot(ax)).length))
    print("\n".join(line))


SK = os.environ.get("SKILL", "guard")
if SK == "guard":
    SEQ = [("GUARD", CP.GUARD)]
else:
    src = {"combo": CP.SEQ, "heavy": CP.HEAVY_SEQ,
           "wide": CP.WIDE_SEQ, "jump": CP.JUMP_SEQ}[SK]
    SEQ = [(str(f), p) for f, p in src]

print("\n=== 자루 파지 실측 (H=%.3f) ===" % H)
for nm, ps in SEQ:
    check(nm, ps)
