# -*- coding: utf-8 -*-
"""다리 축 부호를 **실제로 재서** 확인한다. (walk_pose 를 다시 만들기 전 필수 단계)

왜 재나
  s6_export_game.walk_pose 독스트링은 "X- 가 앞"이라 적혀 있는데,
  combo_poses 의 축 규약은 RIGHT=(-1,0,0) / FWD=(0,-1,0) 이다. 둘이 안 맞는다.
  여기서 말이 갈리면 걷기 방향이 통째로 뒤집히므로 뼈 좌표를 직접 찍는다.

재는 것
  1) 발끝(toe) 이 발목(foot) 보다 어느 월드 방향에 있는가 = 캐릭터 정면
  2) ("l thigh", X, +deg) 를 걸면 발이 어느 방향으로 가는가
  3) ("l calf", X, +deg) 로 무릎이 접히는 방향
  4) 다리 뼈 길이(허벅지/종아리)와 골반 높이 = IK 재작성에 필요한 치수

실행: blender -b -P blender/probe_legaxis.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane")))
A2W = arm.matrix_world
W2A = A2W.inverted()
print("아마추어 스케일 =", tuple(round(x, 5) for x in A2W.to_scale()))

for b in arm.pose.bones:
    b.rotation_mode = "QUATERNION"
    b.matrix_basis = Matrix()
bpy.context.view_layer.update()

zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
FLOOR = min(zs)
print("H=%.4f  바닥 z=%.4f" % (H, FLOOR))


def pb(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


def wp(key):
    b = pb(key)
    return (A2W @ b.matrix).translation.copy() if b else None


print("=== 본 이름 ===")
print("  ", [b.name for b in arm.pose.bones])

print("=== 레스트 월드 좌표(다리) ===")
for nm in ("pelvis", "l thigh", "l calf", "l foot", "l toe",
           "r thigh", "r calf", "r foot", "r toe"):
    v = wp(nm)
    if v is not None:
        print("  %-9s (%+.4f, %+.4f, %+.4f)  z-바닥=%+.4f"
              % (nm, v.x, v.y, v.z, v.z - FLOOR))

lt, lc, lf, lto = wp("l thigh"), wp("l calf"), wp("l foot"), wp("l toe")
print("허벅지 길이 %.4f (%.3f H) / 종아리 %.4f (%.3f H) / 발목->발끝 %.4f"
      % ((lc - lt).length, (lc - lt).length / H,
         (lf - lc).length, (lf - lc).length / H, (lto - lf).length))
d = lto - lf
d.z = 0
print("발끝-발목 수평 방향 = (%+.3f, %+.3f, 0) -> 정면은 %s"
      % (d.normalized().x, d.normalized().y,
         "X-" if abs(d.x) > abs(d.y) and d.x < 0 else
         "X+" if abs(d.x) > abs(d.y) else ("Y-" if d.y < 0 else "Y+")))

# 머리 코 방향 대신 몸통 두께로도 확인: 몸통 정점의 y 분포 대칭성은 의미 없으니
# 어깨 좌우로 RIGHT 를 확인한다.
ru, lu = wp("r upperarm"), wp("l upperarm")
print("RIGHT(= r-l upperarm) = (%+.3f, %+.3f, %+.3f)"
      % tuple((ru - lu).normalized()))


def swing(key, axis, deg):
    b = pb(key)
    ax = (W2A.to_3x3() @ Vector(axis)).normalized()
    head = b.matrix.translation.copy()
    b.matrix = (Matrix.Translation(head) @ Matrix.Rotation(math.radians(deg), 4, ax)
                @ Matrix.Translation(-head) @ b.matrix)
    bpy.context.view_layer.update()


def reset():
    for b in arm.pose.bones:
        b.matrix_basis = Matrix()
    bpy.context.view_layer.update()


print("=== ('l thigh', X, deg) 를 걸면 발목이 어디로 가나 ===")
for deg in (-26, 26):
    reset()
    swing("l thigh", (1, 0, 0), deg)
    n = wp("l foot")
    print("  X %+3d -> 발목 dx=%+.4f dy=%+.4f dz=%+.4f"
          % (deg, n.x - lf.x, n.y - lf.y, n.z - lf.z))

print("=== ('r thigh', X, deg) ===")
rf0 = wp("r foot")
for deg in (-26, 26):
    reset()
    swing("r thigh", (1, 0, 0), deg)
    n = wp("r foot")
    print("  X %+3d -> 발목 dx=%+.4f dy=%+.4f dz=%+.4f"
          % (deg, n.x - rf0.x, n.y - rf0.y, n.z - rf0.z))

print("=== ('l calf', X, deg) 무릎 접힘 ===")
for deg in (-34, 34):
    reset()
    swing("l calf", (1, 0, 0), deg)
    n = wp("l foot")
    print("  X %+3d -> 발목 dx=%+.4f dy=%+.4f dz=%+.4f (무릎 뒤로 접히면 dy>0 또는 dx>0)"
          % (deg, n.x - lf.x, n.y - lf.y, n.z - lf.z))

print("=== 현재 Walk 액션(있으면) 첫 프레임 발 위치 ===")
print("액션:", [a.name for a in bpy.data.actions])
print("DONE")
