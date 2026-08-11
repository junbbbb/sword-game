# -*- coding: utf-8 -*-
"""★출고되는 자루로 파지를 잰다.

지금까지 프로브가 전부 `katana_slayer` 를 쟀는데, s6 는 그 오브젝트를 **지우고**
swords.py 의 SW_* 를 굽는다. 출고 자루는 길이·굵기가 딴판이라(구 0.567 vs 출고 0.36)
"이탈 0.002" 같은 합격 판정이 전부 무의미했다. 여기서는 s6 와 똑같이 자루를 만들어
붙이고, 주먹이 자루의 **어디를** 쥐는지 본다.

실행: SWORD=hongyeom SKILL=guard blender -b -P probe_ship.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
import swords as SW
importlib.reload(CP)
importlib.reload(SW)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
CHAR_H = max(zs) - min(zs)
kat = bpy.data.objects.get("katana_slayer")
GRIP_M = kat.matrix_world.copy()
ps = CP.Poser(arm, CHAR_H)
FIST = ps.fist_r.get("l", 0.166)

# s6 와 동일하게 자루를 만들어 손 본에 묶는다
SW_SCALE = CHAR_H * 0.235
KEY = os.environ.get("SWORD", "hongyeom")
v = next(x for x in SW.VARIANTS if x["key"] == KEY)
root = SW.build_sword(v, scale=SW_SCALE)
root.matrix_world = GRIP_M @ root.matrix_world
hand_bone = next(b.name for b in arm.pose.bones if "r hand" in b.name.lower())
con = root.constraints.new("CHILD_OF")
con.target = arm
con.subtarget = hand_bone
con.inverse_matrix = (arm.matrix_world @ arm.pose.bones[hand_bone].matrix).inverted()
bpy.context.view_layer.update()
grip_ob = next(c for c in root.children if c.name.startswith("gr_"))
pom_ob = next(c for c in root.children if c.name.startswith("pm_"))


def hilt():
    dg = bpy.context.evaluated_depsgraph_get()
    ax = (root.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
    ev = grip_ob.evaluated_get(dg)
    me = ev.to_mesh()
    pts = [ev.matrix_world @ p.co for p in me.vertices]
    o = sum(pts, Vector((0, 0, 0))) / len(pts)     # 축 위의 점 = 무게중심
    ts = [(p - o).dot(ax) for p in pts]
    rad = max(((p - o) - ax * ((p - o).dot(ax))).length for p in pts)
    ev.to_mesh_clear()
    return o + ax * min(ts), o + ax * max(ts), ax, rad


SK = os.environ.get("SKILL", "guard")
if SK == "guard":
    SEQ = [("GUARD", CP.GUARD)]
else:
    src = {"combo": CP.SEQ, "heavy": CP.HEAVY_SEQ, "wide": CP.WIDE_SEQ,
           "jump": CP.JUMP_SEQ}[SK]
    SEQ = [(str(f), p) for f, p in src]

print("\n=== 출고 자루 파지 [%s] (H %.3f, 주먹반경 %.3f) ===" % (KEY, CHAR_H, FIST))
for nm, pose in SEQ:
    ps.apply(pose)
    bpy.context.view_layer.update()
    a, b, ax, grad = hilt()
    L = (b - a).length
    dg = bpy.context.evaluated_depsgraph_get()
    line = ["%-6s 자루 %.3f 반지름 %.4f (주먹의 %.0f%%)"
            % (nm, L, grad, grad / FIST * 100)]
    for s in ("r", "l"):
        if pose.get("1h") and s == "l":
            line.append("    %s: (한손)" % s)
            continue
        c = ps.palm_world(s)
        t = (c - a).dot(ax)
        perp = ((c - a) - ax * t).length
        u = t / L
        # 주먹 정점이 자루 축 구간 안에 얼마나 들어가는가
        hb = ps.pb("%s hand" % s)
        M = ps.A2W @ hb.matrix
        ok = "OK " if (perp < FIST * 0.4 and 0.02 <= u <= 0.98) else "NG "
        line.append("    %s%s 축이탈 %.4f (%.2f 주먹) | 자루위치 %+.2f (0물미 1츠바)"
                    % (ok, s, perp, perp / FIST, u))
    # 물미가 왼 주먹 밖으로 나오는가
    pw = [pom_ob.matrix_world @ p.co for p in pom_ob.data.vertices]
    pc = sum(pw, Vector((0, 0, 0))) / len(pw)
    lp = ps.palm_world("l")
    line.append("    물미 중심이 왼 주먹 중심보다 %.4f 바깥 (양수라야 자루 끝이 보인다)"
                % ((lp - pc).dot(ax)))
    print("\n".join(line))
