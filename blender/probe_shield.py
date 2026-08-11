# -*- coding: utf-8 -*-
"""방패를 만들기 전에 탱커를 실측한다. 아무것도 안 만들고 안 내보낸다.
실행: blender --background --python probe_shield.py
"""
import bpy
import os
import sys
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(WEB, "tank.glb"))

print("=== 오브젝트 ===")
for o in sc.objects:
    print("  %-28s %s" % (o.name, o.type))
meshes = [o for o in sc.objects if o.type == "MESH"]
arm = next(o for o in sc.objects if o.type == "ARMATURE")
print("메시 %d개" % len(meshes))
print("=== 액션 ===", [a.name for a in bpy.data.actions])

# 레스트 기준으로 재야 스키닝이 맞는다
if arm.animation_data:
    arm.animation_data_clear()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()

body = meshes[0]
ws = [body.matrix_world @ v.co for v in body.data.vertices]
zs = [p.z for p in ws]
xs = [p.x for p in ws]
ys = [p.y for p in ws]
H = max(zs) - min(zs)
print("=== 크기 ===")
print("키 %.4f  (z %.4f ~ %.4f)" % (H, min(zs), max(zs)))
print("x %.4f ~ %.4f   y %.4f ~ %.4f" % (min(xs), max(xs), min(ys), max(ys)))
tri = sum(len(p.vertices) - 2 for p in body.data.polygons)
print("몸통 삼각형 %d" % tri)

A2W = arm.matrix_world
print("아마추어 matrix_world:")
for r in A2W:
    print("   ", tuple(round(v, 4) for v in r))


def bone(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


print("=== 뼈 목록 ===")
print(" ", [b.name for b in arm.data.bones])

print("=== 왼팔/오른팔 레스트 좌표(월드) ===")
for key in ("l clavicle", "l upperarm", "l forearm", "l hand",
            "r hand", "pelvis", "head"):
    b = bone(key)
    if not b:
        print("  %-12s 없음" % key)
        continue
    m = A2W @ b.matrix
    head = m.translation
    tail = A2W @ b.tail
    print("  %-12s %-22s head=(%.4f, %.4f, %.4f) tail=(%.4f, %.4f, %.4f) len=%.4f"
          % (key, b.name, head.x, head.y, head.z, tail.x, tail.y, tail.z,
             (tail - head).length))

hb = bone("l hand")
HM = A2W @ hb.matrix
print("=== 왼손 뼈 로컬축(월드에서 본 방향) ===")
print("  X축", tuple(round(v, 4) for v in HM.col[0].to_3d()))
print("  Y축", tuple(round(v, 4) for v in HM.col[1].to_3d()))
print("  Z축", tuple(round(v, 4) for v in HM.col[2].to_3d()))
print("  손 스케일", tuple(round(HM.col[i].to_3d().length, 4) for i in range(3)))

hw = (A2W @ bone("l hand").matrix).translation
fw = (A2W @ bone("l forearm").matrix).translation
sw = (A2W @ bone("l upperarm").matrix).translation
print("=== 팔 치수 ===")
print("  위팔 %.4f (키의 %.1f%%)" % ((fw - sw).length, (fw - sw).length / H * 100))
print("  팔뚝 %.4f (키의 %.1f%%)" % ((hw - fw).length, (hw - fw).length / H * 100))
print("  어깨->손 %.4f" % (hw - sw).length)

# 손 주변 몸통 버텍스로 손 크기 / 팔뚝 굵기를 잰다
def cluster(center, rad):
    pts = [p for p in ws if (p - center).length < rad]
    if not pts:
        return None
    return (len(pts),
            (min(p.x for p in pts), max(p.x for p in pts)),
            (min(p.y for p in pts), max(p.y for p in pts)),
            (min(p.z for p in pts), max(p.z for p in pts)))


for nm, c, r in (("왼손", hw, H * 0.055), ("팔뚝중간", (hw + fw) / 2, H * 0.045)):
    got = cluster(c, r)
    if got:
        n, bx, by, bz = got
        print("  %s 주변 %d버텍스  x폭 %.4f  y폭 %.4f  z폭 %.4f"
              % (nm, n, bx[1] - bx[0], by[1] - by[0], bz[1] - bz[0]))

# 몸통 두께(가슴 높이에서의 y 범위) - 방패가 몸을 뚫는지 판단할 기준
chest_z = sw.z
band = [p for p in ws if abs(p.z - chest_z) < H * 0.03 and abs(p.x) < H * 0.12]
if band:
    print("  가슴 높이 몸통 y %.4f ~ %.4f (두께 %.4f), x %.4f ~ %.4f"
          % (min(p.y for p in band), max(p.y for p in band),
             max(p.y for p in band) - min(p.y for p in band),
             min(p.x for p in band), max(p.x for p in band)))
print("PROBE DONE")
