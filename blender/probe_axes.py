# -*- coding: utf-8 -*-
# 스윙 평면을 설계하려면 이 캐릭터의 실제 축(오른쪽/정면/위)과
# spine Z 회전 부호가 어느 쪽으로 도는지를 먼저 재야 한다.
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
mesh_ob = next(o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("Floor", "Plane")))
A2W = arm.matrix_world
W2A = A2W.inverted()

for b in arm.pose.bones:
    b.rotation_mode = "QUATERNION"
    b.matrix_basis = Matrix()
bpy.context.view_layer.update()


def pb(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


def wp(key):
    b = pb(key)
    return (A2W @ b.matrix).translation if b else None


print("=== bone names ===")
for b in arm.pose.bones:
    print("  ", b.name)

zs = [(mesh_ob.matrix_world @ v.co).z for v in mesh_ob.data.vertices]
ys = [(mesh_ob.matrix_world @ v.co).y for v in mesh_ob.data.vertices]
H = max(zs) - min(zs)
print("H=%.3f  y range %.3f..%.3f" % (H, min(ys), max(ys)))

ru = wp("r upperarm")
lu = wp("l upperarm")
rf = wp("r forearm")
rh = wp("r hand")
hd = wp("head")
sp = wp("spine")
print("=== rest world positions ===")
for nm, v in (("r upperarm", ru), ("l upperarm", lu), ("r forearm", rf),
              ("r hand", rh), ("head", hd), ("spine", sp)):
    print("  %-12s %s" % (nm, tuple(round(x, 3) for x in v)))

RIGHT = (ru - lu).normalized()
print("RIGHT(= r-l upperarm) =", tuple(round(x, 3) for x in RIGHT))
print("upperarm dir(rest) =", tuple(round(x, 3) for x in (rf - ru).normalized()))
print("forearm  dir(rest) =", tuple(round(x, 3) for x in (rh - rf).normalized()))

# 코 방향(정면) 추정: 머리 정점들의 y 무게중심이 몸 중심보다 어느 쪽인지
print("assumed FWD = (0,-1,0)  UP=(0,0,1)")


def swing(key, axis, deg):
    b = pb(key)
    if b is None:
        return
    ax = (W2A.to_3x3() @ Vector(axis)).normalized()
    head = b.matrix.translation.copy()
    b.matrix = (Matrix.Translation(head) @ Matrix.Rotation(math.radians(deg), 4, ax)
                @ Matrix.Translation(-head) @ b.matrix)
    bpy.context.view_layer.update()


def reset():
    for b in arm.pose.bones:
        b.matrix_basis = Matrix()
    bpy.context.view_layer.update()


print("=== spine Z twist direction ===")
for d in (-30, 30):
    reset()
    swing("spine", (0, 0, 1), d)
    n_ru = wp("r upperarm")
    dy = n_ru.y - ru.y
    print("  spine Z %+d -> r shoulder dy=%+.3f (%s)" % (
        d, dy, "오른어깨가 앞으로" if dy < 0 else "오른어깨가 뒤로"))

print("=== r upperarm Y rotation direction ===")
for d in (-60, 60):
    reset()
    swing("r upperarm", (0, 1, 0), d)
    n = wp("r forearm")
    print("  Y %+d -> elbow z=%+.3f (rest %.3f) dz=%+.3f" % (d, n.z, rf.z, n.z - rf.z))

print("=== r upperarm Z rotation direction ===")
for d in (-60, 60):
    reset()
    swing("r upperarm", (0, 0, 1), d)
    n = wp("r forearm")
    print("  Z %+d -> elbow y=%+.3f (rest %.3f) dy=%+.3f  x=%+.3f" % (
        d, n.y, rf.y, n.y - rf.y, n.x))
print("DONE")
