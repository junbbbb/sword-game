# -*- coding: utf-8 -*-
"""두 glb 의 **액션 채널을 프레임 단위로 대조**한다 (13-모션이식, 2026-08-12).

    A=/경로/before.glb B=web/basic2.glb blender -b -P blender/probe_clip_diff.py

왜: 베기 3종만 갈아끼웠다는 주장을 증명하려면 Idle·Walk·Run·Jump 가 **한 자리도**
안 변했음을 보여야 한다. 뼈 이름·프레임 수·본 회전·본 위치를 그대로 비교한다.
쿼터니언은 부호가 뒤집혀도 같은 회전이라, 회전은 **행렬 각도차**로 잰다.
"""
import bpy
import os
import math
from mathutils import Matrix

A = os.environ["A"]
B = os.environ["B"]
ROOT = "/Users/lbj/Documents/gameproject"
for _v in ("A", "B"):
    pass
if not os.path.isabs(A):
    A = os.path.join(ROOT, A)
if not os.path.isabs(B):
    B = os.path.join(ROOT, B)


def load(path):
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.render.fps_base = 1.0
    bpy.ops.import_scene.gltf(filepath=path)
    if sc.render.fps != 30:
        sc.render.fps = 30
    arm = next(o for o in sc.objects if o.type == "ARMATURE")
    out = {}
    for act in bpy.data.actions:
        arm.animation_data_create()
        arm.animation_data.action = act
        sl = list(getattr(act, "slots", []))
        if sl:
            arm.animation_data.action_slot = sl[0]
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        rows = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            rows.append({b.name: (arm.matrix_world @ b.matrix).copy()
                         for b in arm.pose.bones})
        out[act.name] = (f0, f1, rows)
    return out


DA = load(A)
DB = load(B)
print("=" * 78)
print("[대조] A %s" % A)
print("       B %s" % B)
print("  A 액션 %s" % sorted(DA))
print("  B 액션 %s" % sorted(DB))
print("%-8s %6s %6s | %14s %14s   판정" % ("클립", "A장", "B장", "위치 최대차(m)",
                                           "회전 최대차(도)"))
for name in sorted(set(DA) | set(DB)):
    if name not in DA or name not in DB:
        print("%-8s %6s %6s | %14s %14s   ★한쪽에만 있다"
              % (name, len(DA[name][2]) if name in DA else "-",
                 len(DB[name][2]) if name in DB else "-", "-", "-"))
        continue
    ra, rb = DA[name][2], DB[name][2]
    if len(ra) != len(rb):
        print("%-8s %6d %6d | %14s %14s   ★프레임 수가 다르다"
              % (name, len(ra), len(rb), "-", "-"))
        continue
    dp, dr = 0.0, 0.0
    for a, b in zip(ra, rb):
        for bn, ma in a.items():
            mb = b.get(bn)
            if mb is None:
                continue
            dp = max(dp, (ma.translation - mb.translation).length)
            X = ma.to_3x3().normalized().inverted() @ mb.to_3x3().normalized()
            dr = max(dr, math.degrees(X.to_quaternion().angle))
    print("%-8s %6d %6d | %14.8f %14.8f   %s"
          % (name, len(ra), len(rb), dp, dr,
             "차이 0" if (dp < 1e-7 and dr < 1e-5) else "★변경됨"))
