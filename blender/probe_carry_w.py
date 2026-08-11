# -*- coding: utf-8 -*-
"""가중치 후보를 **굽지 않고** 수치로 먼저 비교한다(굽기 4번 + 렌더 16장을 아낀다).

메모리 안에서 왼팔에 캐리 자세를 w 만큼 먹인 뒤, 프레임마다
방패 최고점 z 와 어깨 z 를 비교한다. 파일은 아무것도 안 건드린다.

실행: blender -b -P probe_carry_w.py
"""
import bpy
import os
import sys
import math

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import carry_pose as CP           # noqa: E402

SRC = os.environ.get("SRC", os.path.join(ROOT, "web", "tank.glb"))
WEIGHTS = [0.0, 0.6, 0.75, 0.9, 1.0]

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=SRC)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
shield = next(o for o in sc.objects if o.name.startswith("SH_"))
arm.data.pose_position = "POSE"
if arm.animation_data is None:
    arm.animation_data_create()

top = CP.shield_sampler(arm, shield)
ref = CP.read_reference(arm, "Idle", 17)

# 목표선: Idle 에서 방패가 어깨보다 얼마나 아래인가. 여기에 가까울수록 성공.
CP.use_action(arm, "Idle")
sc.frame_set(17)
bpy.context.view_layer.update()
idle_gap = top() - CP.shoulder_z(arm)
print("[목표] Idle f17 방패 최고점은 어깨보다 %+.1fcm (이 값이 캐리 자세의 정답)"
      % (idle_gap * 100))

def swing(qs):
    """프레임들 사이의 최대 방향 차이(도). 팔이 얼마나 살아 있는지의 지표.
    w=1.0 이면 0도(완전히 굳음), w=0 이면 원본 스윙 그대로."""
    best = 0.0
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            d = abs(qs[i].dot(qs[j]))
            best = max(best, 2 * math.degrees(math.acos(min(1.0, d))))
    return best


for clip in ("Walk", "Run"):
    act = bpy.data.actions[clip]
    f0, f1, src = CP.capture(arm, act)
    print("=== %s (f%d~%d) 방패 최고점 - 어깨 z, 단위 cm ===" % (clip, f0, f1))
    head = "  w    " + " ".join("f%02d" % f for f in range(f0, f1 + 1)) + "   최악"
    print(head)
    for w in WEIGHTS:
        vals = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            CP.apply_frame(arm, src[f], ref, w)
            vals.append((top() - CP.shoulder_z(arm)) * 100)
        # 남은 스윙은 굽는 것과 똑같은 blend 로 계산한다(렌더 없이 각도로 본다)
        sw = {nm: swing([CP.blend(src[f][nm], ref[nm], w)
                         for f in range(f0, f1 + 1)]) for nm in CP.L_CHAIN}
        print("  %.2f " % w + " ".join("%+3.0f" % v for v in vals)
              + "   %+.1f (f%d)  남은스윙 위팔 %4.1f도 팔뚝 %4.1f도 손 %4.1f도"
              % (max(vals), f0 + vals.index(max(vals)),
                 sw[CP.L_CHAIN[0]], sw[CP.L_CHAIN[1]], sw[CP.L_CHAIN[2]]))
print("SWEEP DONE")
