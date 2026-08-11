# -*- coding: utf-8 -*-
"""리타게팅한 달리기의 (1) 발 미끄러짐 없는 속도 (2) 파지 유지를 잰다.

발 미끄러짐: 애니는 제자리 루프라 접지한 발이 몸 기준 뒤로 밀린다.
그 '뒤로 밀리는 속도'와 게임 이동 속도가 같아야 미끄러지지 않는다.
실행: blender -b -P probe_run.py
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
import asset_anim as AA
importlib.reload(CP)
importlib.reload(AA)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
katana = bpy.data.objects.get("katana_slayer")
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
FLOOR = min(zs)
ps = CP.Poser(arm, H)
FIST = ps.fist_r.get("l", 0.166)
FPS = 30.0
GAME_H = 1.75            # web/main.js 가 캐릭터를 이 키로 정규화한다

src, f0, f1, tmp = AA.load("infantry_combat_run")
N = f1 - f0 + 1
rows = []
for i in range(N):
    sc.frame_set(f0 + i)
    ps.reset()
    AA.copy_pose(src, arm)
    ps.apply({"b": CP.GUARD_ARMS}, reset=False)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    # 발끝 최저점 (본 head 는 발목이라 접지 판정에 못 쓴다)
    lo = min((ev.matrix_world @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    # 파지
    KM = katana.evaluated_get(dg).matrix_world
    ax = (KM.to_3x3() @ Vector((1, 0, 0))).normalized()
    g = bpy.data.objects.get("gripK_slayer")
    ge = g.evaluated_get(dg)
    gm = ge.to_mesh()
    pts = [ge.matrix_world @ v.co for v in gm.vertices]
    o = sum(pts, Vector((0, 0, 0))) / len(pts)
    ge.to_mesh_clear()
    v = ps.palm_world("l") - o
    dev = (v - ax * v.dot(ax)).length / FIST
    # 발 앞뒤 위치 (FWD = -Y). 접지한 발은 몸 기준 뒤로 밀린다
    lf = ps.wpos("l foot")
    rf = ps.wpos("r foot")
    rows.append((i + 1, lo - FLOOR, lf.dot(CP.FWD), rf.dot(CP.FWD), dev))

print("\n=== 달리기 리타게팅 검사 (H=%.3f, 게임키 %.2f) ===" % (H, GAME_H))
print(" f  | 최저발-바닥 | 왼발앞뒤  오른발앞뒤 | 왼주먹 이탈(주먹)")
for r in rows:
    print(" %2d | %8.3f | %8.3f %8.3f | %.2f" % r)

dev = [r[4] for r in rows]
print("\n파지: 최대 이탈 %.2f 주먹 (기준 0.30 이하면 자루가 주먹 안)" % max(dev))

# 접지 구간 = 발끝이 바닥에서 가장 낮은 쪽 40%
lows = sorted(r[1] for r in rows)
thr = lows[int(len(lows) * 0.4)]
for side, ix in (("왼", 2), ("오른", 3)):
    ct = [r for r in rows if r[1] <= thr]
    # 그 발이 접지인 프레임: 그 발의 앞뒤값이 감소(뒤로 밀림)하는 연속 구간
    ys = [r[ix] for r in rows]
    best, cur = [], []
    for i in range(1, len(ys)):
        if ys[i] < ys[i - 1] - 1e-4:
            if not cur:
                cur = [i - 1]
            cur.append(i)
        else:
            if len(cur) > len(best):
                best = cur
            cur = []
    if len(cur) > len(best):
        best = cur
    if len(best) >= 2:
        d = ys[best[0]] - ys[best[-1]]
        dt = (best[-1] - best[0]) / FPS
        v = d / dt
        print("%s발: 뒤로 %.3f 이동 / %.3f 초 = %.2f 단위/초  (게임 스케일 %.2f/초)"
              % (side, d, dt, v, v / H * GAME_H))
print("\n사이클 %d 프레임 = %.3f 초" % (N - 1, (N - 1) / FPS))
AA.drop(tmp)
