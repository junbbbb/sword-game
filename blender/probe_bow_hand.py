# -*- coding: utf-8 -*-
"""손에 들 활을 어디에 어떻게 놓을지 **실측**한다. (web/archer.glb 를 읽기 전용으로 본다)

★archer.glb 는 s11 의 **결과물**이다. 여기서는 재기만 하고, 굽는 쪽(s11)의 입력으로는
  절대 넣지 않는다(LOG 함정 15: basic2 에서 결과물을 원본으로 다시 먹인 사고가 있다).

무엇을 재나
  1) Attack 클립의 프레임별 두 손 위치 - **어느 손이 앞으로 뻗는지**(활 쥔 손)를 정한다.
     지시서는 왼손이라고 했지만 반드시 직접 확인하라고 했다.
  2) 만작 프레임(f11, 클립 0.458초)에서 왼손 뼈 행렬 M_pose.
  3) 화살이 날아가는 방향(캐릭터 정면)과 시위 손(오른손)의 위치.
     활은 화살과 같은 평면에 있어야 하고, 시위가 그 손 쪽을 향해야 어긋나 보이지 않는다.
  4) REST 에서의 같은 뼈 행렬 M_rest - s10_shield.py 와 같은 L = M_pose⁻¹ @ target 을 풀려면 필요하다.

실행: blender --background --python blender/probe_bow_hand.py
"""
import bpy
import os
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.path.join(ROOT, "web/archer.glb")
BONE = "Bip001 L Hand"

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH")
A2W = arm.matrix_world
print("[씬] 오브젝트", [(o.name, o.type) for o in sc.objects])
print("[액션]", sorted(a.name for a in bpy.data.actions))
print("[뼈 %d개]" % len(arm.data.bones))

FPS = sc.render.fps / sc.render.fps_base
print("[fps] %.3f" % FPS)


def use(act):
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def wp(name):
    return (A2W @ arm.pose.bones[name].matrix).translation.copy()


# ------------------------------------------------------------ REST 실측
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
M_rest = A2W @ arm.pose.bones[BONE].matrix
print("\n[REST] 키 %.4f" % H)
for b in ("Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand",
          "Bip001 R UpperArm", "Bip001 R Forearm", "Bip001 R Hand",
          "Bip001 Head", "Bip001 Pelvis"):
    p = wp(b)
    print("  %-20s (%7.3f, %7.3f, %7.3f)" % (b, p.x, p.y, p.z))
print("[REST] 왼손 뼈 행렬")
for r in range(4):
    print("   ", "  ".join("%8.4f" % M_rest[r][c] for c in range(4)))

# ------------------------------------------------------------ Attack 프레임별
atk = bpy.data.actions["Attack"]
arm.data.pose_position = "POSE"
use(atk)
f0 = int(round(atk.frame_range[0]))
f1 = int(round(atk.frame_range[1]))
print("\n[Attack] f%d~f%d (%d프레임, %.4f초)" % (f0, f1, f1 - f0 + 1, (f1 - f0) / FPS))
print("  %4s %7s | %-24s | %-24s | %7s %7s"
      % ("f", "t(초)", "왼손(x,y,z)", "오른손(x,y,z)", "왼손앞", "오른손앞"))
best = None
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    L = wp("Bip001 L Hand")
    R = wp("Bip001 R Hand")
    # 정면 = -Y 이므로 "앞으로" 는 -y 가 큰 쪽
    print("  %4d %7.4f | %7.3f %7.3f %7.3f | %7.3f %7.3f %7.3f | %7.3f %7.3f"
          % (f, (f - f0) / FPS, L.x, L.y, L.z, R.x, R.y, R.z, -L.y, -R.y))
    if best is None or (-L.y) > best[1]:
        best = (f, -L.y)
print("[판정] 왼손이 가장 앞으로 나오는 프레임 f%d (앞 %.3fm)" % best)

# ------------------------------------------------------------ 만작 프레임 상세
DRAW_F = int(os.environ.get("DRAW_F", "11"))
sc.frame_set(DRAW_F)
bpy.context.view_layer.update()
M_pose = A2W @ arm.pose.bones[BONE].matrix
Lh = wp("Bip001 L Hand")
Lf = wp("Bip001 L Forearm")
Lu = wp("Bip001 L UpperArm")
Rh = wp("Bip001 R Hand")
Hd = wp("Bip001 Head")
print("\n[만작 f%d = 클립 %.4f초]" % (DRAW_F, (DRAW_F - f0) / FPS))
print("  왼손  (%7.3f,%7.3f,%7.3f)" % (Lh.x, Lh.y, Lh.z))
print("  왼팔뚝(%7.3f,%7.3f,%7.3f)  왼위팔(%7.3f,%7.3f,%7.3f)"
      % (Lf.x, Lf.y, Lf.z, Lu.x, Lu.y, Lu.z))
print("  오른손(%7.3f,%7.3f,%7.3f)  머리 (%7.3f,%7.3f,%7.3f)"
      % (Rh.x, Rh.y, Rh.z, Hd.x, Hd.y, Hd.z))
d = Lh - Rh
print("  왼손-오른손 벡터 (%7.3f,%7.3f,%7.3f)  거리 %.3f (= 당긴 길이)"
      % (d.x, d.y, d.z, d.length))
fa = (Lh - Lf)
print("  왼팔뚝->손 방향 (%.3f,%.3f,%.3f) 길이 %.3f" % (fa.x, fa.y, fa.z, fa.length))
print("[만작] 왼손 뼈 행렬 M_pose")
for r in range(4):
    print("   ", "  ".join("%8.4f" % M_pose[r][c] for c in range(4)))
Mp3 = M_pose.to_3x3()
print("[만작] 왼손 뼈 로컬축의 월드 방향")
for k, nm in enumerate(("X", "Y", "Z")):
    v = Vector((Mp3[0][k], Mp3[1][k], Mp3[2][k])).normalized()
    print("   뼈 %s -> (%6.3f,%6.3f,%6.3f)" % (nm, v.x, v.y, v.z))
Mr3 = M_rest.to_3x3()
print("[REST] 왼손 뼈 로컬축의 월드 방향")
for k, nm in enumerate(("X", "Y", "Z")):
    v = Vector((Mr3[0][k], Mr3[1][k], Mr3[2][k])).normalized()
    print("   뼈 %s -> (%6.3f,%6.3f,%6.3f)" % (nm, v.x, v.y, v.z))

# 참고: Idle/Walk/Run/Jump 에서의 왼손 위치(활이 몸을 뚫는지 나중에 볼 기준선)
print("\n[다른 클립의 왼손]")
for nm in ("Idle", "Walk", "Run", "Jump"):
    a = bpy.data.actions.get(nm)
    if not a:
        continue
    use(a)
    g0 = int(round(a.frame_range[0]))
    g1 = int(round(a.frame_range[1]))
    ps = []
    for f in range(g0, g1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        ps.append(wp("Bip001 L Hand"))
    print("  %-5s f%d~%d  x %.3f~%.3f  y %.3f~%.3f  z %.3f~%.3f"
          % (nm, g0, g1, min(p.x for p in ps), max(p.x for p in ps),
             min(p.y for p in ps), max(p.y for p in ps),
             min(p.z for p in ps), max(p.z for p in ps)))
