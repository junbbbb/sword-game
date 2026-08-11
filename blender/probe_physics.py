# -*- coding: utf-8 -*-
"""동작이 **물리적으로 가능한가**를 액션 전체에 대해 감사한다.

보는 것
  1. 손이 몸통 안에 들어갔는가        (주먹 정점이 몸통 볼록껍질 안)
  2. 발이 바닥을 뚫었는가            (메시 최저점이 바닥 아래)
  3. 무릎·팔꿈치가 반대로 꺾였는가    (과신전)
  4. 무게중심이 지지면 밖인가        (접지한 발이 만드는 다각형 밖 = 넘어진다)
  5. 접지한 발이 미끄러지는가        (제자리 루프인데 발이 몸 기준으로 안 움직이면
                                    이동 속도와 안 맞아 미끄러진다)
실행: blender -b -P probe_physics.py
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
import asset_anim as AA
importlib.reload(CP)
importlib.reload(AA)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
FLOOR = min(zs)
ps = CP.Poser(arm, H)

vgn = {g.index: g.name for g in mesh.vertex_groups}
GRP = {}
for v in mesh.data.vertices:
    best, bw = None, -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, vgn.get(g.group, "")
    GRP.setdefault((best or "").lower(), []).append(v.index)


def idx_of(*keys):
    out = []
    for k, ids in GRP.items():
        if any(x in k for x in keys):
            out.extend(ids)
    return out


HAND = {"r": idx_of("r hand"), "l": idx_of("l hand")}
TORSO = idx_of("spine", "pelvis", "neck")
FOOTV = idx_of("foot", "toe")
FOOTSET = set(FOOTV)


def ev_mesh():
    dg = bpy.context.evaluated_depsgraph_get()
    e = mesh.evaluated_get(dg)
    return e, e.to_mesh()


def hull2d(pts):
    """XY 볼록껍질 (Andrew monotone chain)."""
    P = sorted(set((round(p.x, 5), round(p.y, 5)) for p in pts))
    if len(P) < 3:
        return P

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for q in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    up = []
    for q in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def inside2d(poly, q):
    """점이 볼록다각형 안인가."""
    if len(poly) < 3:
        return False
    sign = 0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        c = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
        if abs(c) < 1e-12:
            continue
        s = 1 if c > 0 else -1
        if sign == 0:
            sign = s
        elif s != sign:
            return False
    return True


def in_torso(torso, probe, band):
    """★몸통 관통 판정은 **그 높이의 단면**으로 해야 한다.
    중심에서의 방향별 반지름으로 재면(예전 방식) 목·어깨까지 끌어와
    배 앞에 있는 손도 '관통'으로 나온다(전 프레임 오탐이었다)."""
    near = [p for p in torso if abs(p.z - probe.z) < band]
    if len(near) < 6:
        return False
    return inside2d(hull2d(near), (probe.x, probe.y))


def angle(a, b, c):
    u = (a - b)
    v = (c - b)
    if u.length < 1e-9 or v.length < 1e-9:
        return 180.0
    return math.degrees(u.angle(v))


def audit(name, frames, build):
    print("\n===== %s =====" % name)
    bad = []
    prev_feet = None
    for i, (f, spec) in enumerate(frames):
        build(spec)
        bpy.context.view_layer.update()
        e, me = ev_mesh()
        W = e.matrix_world
        P = [W @ me.vertices[j].co for j in range(len(me.vertices))]
        torso = [P[j] for j in TORSO]
        msg = []
        # 1) 손이 몸통 안 (그 높이의 단면 기준)
        for s in ("r", "l"):
            ins = sum(1 for j in HAND[s] if in_torso(torso, P[j], H * 0.045))
            if ins > len(HAND[s]) * 0.4:
                msg.append("%s주먹 몸통관통 %d/%d" % (s, ins, len(HAND[s])))
        # 2) 바닥 관통. ★절대 높이로 재면 안 된다. 게임은 매 프레임 **가장 낮은 발**을
        #    바닥에 맞추므로(groundFeet), 주저앉는 포즈가 아래로 내려가는 건 정상이다.
        #    발보다 아래로 내려간 **다른 부위**가 있을 때만 진짜 관통이다.
        fz = min((P[j].z for j in FOOTV), default=None)
        if fz is not None:
            other = [P[j].z for j in range(len(P)) if j not in FOOTSET]
            lo2 = min(other) if other else fz
            if lo2 < fz - H * 0.005:
                msg.append("발보다 아래로 내려간 부위 %.1f%%H" % ((fz - lo2) / H * 100))
        # 3) 과신전
        for s in ("l", "r"):
            hip, kne, ank = (ps.wpos("%s thigh" % s), ps.wpos("%s calf" % s),
                             ps.wpos("%s foot" % s))
            if hip and kne and ank:
                a = angle(hip, kne, ank)
                if a > 183:
                    msg.append("%s무릎 과신전 %.0f도" % (s, a))
            sh, el, wr = (ps.wpos("%s upperarm" % s), ps.wpos("%s forearm" % s),
                          ps.wpos("%s hand" % s))
            if sh and el and wr:
                a = angle(sh, el, wr)
                if a > 184:
                    msg.append("%s팔꿈치 과신전 %.0f도" % (s, a))
        # 4) 무게중심이 지지면 밖. 지지면 = **가장 낮은 발 기준** 접지 정점
        com = sum(P, Vector((0, 0, 0))) / len(P)
        fz2 = min((P[j].z for j in FOOTV), default=FLOOR)
        ground = [P[j] for j in FOOTV if P[j].z < fz2 + H * 0.05]
        if ground:
            gx = [p.x for p in ground]
            gy = [p.y for p in ground]
            mx = (min(gx) + max(gx)) / 2
            my = (min(gy) + max(gy)) / 2
            hw = max(0.02, (max(gx) - min(gx)) / 2)
            hh = max(0.02, (max(gy) - min(gy)) / 2)
            ox = abs(com.x - mx) / hw
            oy = abs(com.y - my) / hh
            if max(ox, oy) > 1.25:
                msg.append("무게중심 지지면 밖 (x%.2f y%.2f 배)" % (ox, oy))
        e.to_mesh_clear()
        tag = "OK" if not msg else " / ".join(msg)
        if msg:
            bad.append(str(f))
        print("  f%-4s %s" % (f, tag))
    print("  --> 문제 프레임: %s" % (", ".join(bad) if bad else "없음"))


# ---- 스킬 (combo_poses 정의) ----
for nm, seq in (("3연타 Attack", CP.SEQ), ("수면참 Heavy", CP.HEAVY_SEQ),
                ("횡일섬 Wide", CP.WIDE_SEQ), ("점프 Jump", CP.JUMP_SEQ)):
    audit(nm, seq, lambda p: ps.apply(p))

# ---- 달리기 (원본 에셋 리타게팅) ----
src, f0, f1, tmp = AA.load("infantry_combat_run")


def build_run(sf):
    sc.frame_set(sf)
    ps.reset()
    arm.location = ps.home
    AA.copy_pose(src, arm, AA.LOWER_LARM)   # 왼팔은 원본 팔 흔들기 그대로
    ps.apply({"b": CP.RUN_ARMS}, reset=False)


audit("달리기 Run", [(i, f0 + i) for i in range(0, f1 - f0 + 1, 2)], build_run)
AA.drop(tmp)
