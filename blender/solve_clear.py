# -*- coding: utf-8 -*-
"""베기 포즈에서 **왼 주먹이 몸통(코트) 안에 파묻히는** 걸 푸는 최소 변경을 찾는다.

원인은 중단세와 같다. 왼손은 오른 주먹에서 칼날 반대 방향으로 GB 만큼 떨어진 자리이므로,
칼날의 앞 성분이 클수록 왼손이 뒤(= 몸 쪽)로 끌려간다.
쓸 수 있는 손잡이는 둘뿐이다.
  1) 오른손을 앞으로 더 낸다 (팔 길이 한계에 걸린다)
  2) 칼을 세운다 = 칼날의 앞 성분을 줄인다 (스윙의 성격이 바뀌므로 최소로)
두 축을 훑어 **닿으면서 손이 나오는** 조합 중 원본에서 가장 덜 바뀐 것을 고른다.

실행: blender -b -P solve_clear.py
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
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh = next(o for o in bpy.data.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
ps = CP.Poser(arm, H)
FIST = ps.fist_r["l"]

vgn = {g.index: g.name for g in mesh.vertex_groups}
TOR = []
for v in mesh.data.vertices:
    best, bw = None, -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, vgn.get(g.group, "")
    if best and any(x in best.lower() for x in ("spine", "pelvis", "neck")):
        TOR.append(v.index)


def clearance(pose):
    """왼 주먹 중심이 그 높이의 몸통 앞면에서 얼마나 나왔는가(주먹 배수). 음수면 파묻힘."""
    ps.reach_log = []
    ps.apply(pose)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    P = [ev.matrix_world @ v.co for v in me.vertices]
    org = ps.origin()
    lp = ps.palm_world("l")
    band = [P[j] for j in TOR if abs(P[j].z - lp.z) < H * 0.045]
    ev.to_mesh_clear()
    if not band:
        return 9.0, False
    # 몸통 단면에서 **왼 주먹 방향**의 표면까지. 앞뒤(FWD)만 보면 옆으로 벗어난
    # 포즈에서 틀린 답이 나온다.
    d = lp - org
    d.z = 0
    if d.length < 1e-6:
        return -9.0, bool(ps.reach_log)
    n = d.normalized()
    surf = max((p - org).dot(n) for p in band)
    return (d.length - surf) / FIST, bool(ps.reach_log)


def variants(pose):
    """(오른손 u 올림, f 앞으로, 칼 세우기, 상체 숙임 완화).
    ★검도 교본: 벤 마무리에 오른 주먹은 **어깨 바로 아래**(우리 기준 u +0.19).
    지금 베기는 u +0.03(배꼽 높이)이라 손이 배에 파묻힌다.
    비용은 '최종 u 가 0.19 에서 얼마나 벗어나는가' 로 잡는다. 단순히 u 를 크게
    올리는 걸 싸게 두면 어깨 위로 손이 올라가 찌르는 자세가 된다(실제로 그랬다)."""
    cur_u = 0.0
    for key, op, val in pose["b"]:
        if op == CP.IK and key == "r":
            cur_u = val[1]
            break
    out = []
    for du in (0.0, 0.03, 0.06, 0.09, 0.12, 0.15, 0.18, 0.21, 0.24, 0.27):
        for df in (0.0, 0.03, 0.06, 0.09, 0.12, 0.15, 0.18, 0.22):
            for k in (0.0, 0.12, 0.25, 0.40):
                for dsp in (0, 6, 12):
                    cost = abs((cur_u + du) - 0.19) * 12.0 + df * 8.0 \
                        + k * 8.0 + dsp * 0.35
                    out.append((du, df, k, dsp, cost))
    out.sort(key=lambda t: t[4])
    return out


UP = CP.UP


def rebuild(pose, du, df, k, dsp):
    bl = []
    for key, op, val in pose["b"]:
        if op == CP.IK and key == "r":
            bl.append((key, op, (val[0], val[1] + du, val[2] + df)))
        elif op == CP.BLADE:
            d = (CP.ruf(*val) + UP * k).normalized()
            bl.append((key, op, (d.dot(CP.RIGHT), d.dot(CP.UP), d.dot(CP.FWD))))
        elif key == "spine" and op == CP.X and val > 0:
            bl.append((key, op, max(0, val - dsp)))     # 숙임만 완화(젖히진 않는다)
        else:
            bl.append((key, op, val))
    return dict(pose, b=bl)


NAMES = {}
for nm, seq in (("SEQ", CP.SEQ), ("HEAVY_SEQ", CP.HEAVY_SEQ),
                ("WIDE_SEQ", CP.WIDE_SEQ), ("JUMP_SEQ", CP.JUMP_SEQ)):
    print("\n===== %s =====" % nm)
    for f, pose in seq:
        if pose.get("1h") or CP.grip_of(pose) is None:
            continue
        c0, r0 = clearance(pose)
        if c0 > 0.10:
            print("  f%-3d 여유 %+.2f 주먹  OK" % (f, c0))
            continue
        best = None
        for du, df, k, dsp, cost in variants(pose):
            if du == 0.0 and df == 0.0 and k == 0.0 and dsp == 0:
                continue
            c, bad = clearance(rebuild(pose, du, df, k, dsp))
            if c > 0.15 and not bad:
                best = (du, df, k, dsp, c)
                break
        if best:
            du, df, k, dsp, c = best
            nb = rebuild(pose, du, df, k, dsp)
            ik = bl2 = None
            for key, op, val in nb["b"]:
                if op == CP.IK and key == "r":
                    ik = val
                elif op == CP.BLADE:
                    bl2 = val
            print("  f%-3d %+.2f -> %+.2f | IK (%.2f, %.2f, %.2f) BLADE (%.2f, %.2f, %.2f)%s"
                  % (f, c0, c, ik[0], ik[1], ik[2], bl2[0], bl2[1], bl2[2],
                     ("  spineX -%d" % dsp) if dsp else ""))
        else:
            print("  f%-3d %+.2f -> 해 없음" % (f, c0))
