# -*- coding: utf-8 -*-
"""클립별 왼손 뼈가 월드에서 어떤 자세인지 뽑는다. 방패의 부착 방향을 정하려면
'가장 많이 보이는 포즈(Idle)'에서 방패가 어떻게 서야 하는지를 먼저 알아야 한다.
아무것도 만들지 않고 안 내보낸다.
실행: blender --background --python probe_hand.py
"""
import bpy
import os
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(WEB, "tank.glb"))
arm = next(o for o in sc.objects if o.type == "ARMATURE")
meshes = [o for o in sc.objects if o.type == "MESH"]

# Icosphere 가 tank.glb 안에 섞여 있다. 크기를 확인해 둔다(main.js 키 계산에 영향).
for m in meshes:
    ws = [m.matrix_world @ v.co for v in m.data.vertices]
    print("메시 %-12s 버텍스 %5d  z %.3f~%.3f  x %.3f~%.3f  y %.3f~%.3f"
          % (m.name, len(ws), min(p.z for p in ws), max(p.z for p in ws),
             min(p.x for p in ws), max(p.x for p in ws),
             min(p.y for p in ws), max(p.y for p in ws)))

A2W = arm.matrix_world
if arm.animation_data is None:
    arm.animation_data_create()
arm.data.pose_position = "POSE"


def pb(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


def dump(tag, f):
    bpy.context.view_layer.update()
    h = pb("l hand")
    e = pb("l forearm")
    s = pb("l upperarm")
    M = A2W @ h.matrix
    p = M.translation
    ax = [M.col[i].to_3d().normalized() for i in range(3)]
    ep = (A2W @ e.matrix).translation
    sp = (A2W @ s.matrix).translation
    fa = (p - ep).normalized()          # 팔뚝 방향(팔꿈치->손)
    print("  %-8s f%-4d 손(%.3f,%.3f,%.3f) 팔꿈치(%.3f,%.3f,%.3f) 어깨(%.3f,%.3f,%.3f)"
          % (tag, f, p.x, p.y, p.z, ep.x, ep.y, ep.z, sp.x, sp.y, sp.z))
    print("           팔뚝dir(%.2f,%.2f,%.2f)  뼈X(%.2f,%.2f,%.2f) 뼈Y(%.2f,%.2f,%.2f) 뼈Z(%.2f,%.2f,%.2f)"
          % (fa.x, fa.y, fa.z, ax[0].x, ax[0].y, ax[0].z,
             ax[1].x, ax[1].y, ax[1].z, ax[2].x, ax[2].y, ax[2].z))


print("=== REST ===")
arm.data.pose_position = "REST"
dump("REST", 0)
arm.data.pose_position = "POSE"

for act in bpy.data.actions:
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception as ex:
        print("slot 실패", ex)
    f0, f1 = act.frame_range
    f0, f1 = int(f0), int(f1)
    print("=== %s (%d~%d) ===" % (act.name, f0, f1))
    n = max(1, (f1 - f0) // 3)
    for f in range(f0, f1 + 1, n):
        sc.frame_set(f)
        dump(act.name, f)
print("PROBE DONE")
