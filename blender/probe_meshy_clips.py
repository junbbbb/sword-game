# -*- coding: utf-8 -*-
"""Meshy 프리셋 3종의 **내용**을 프레임 단위로 실측한다(13-모션이식, 2026-08-12).

    blender -b -P blender/probe_meshy_clips.py

찍는 것 (전부 소스 리그 자체 좌표. 키로 정규화해 타깃과 비교 가능하게)
  · 손 궤적    : 오른손·왼손 월드 위치, 두 손 거리(양손 파지인지 판단)
  · 가상 칼끝  : 오른손 원점에서 손 로컬 칼축으로 blade 길이만큼 뻗은 점
                 (칼축은 basic2 계약값 dir=(-0.161963,0.278876,-0.946571),
                  길이는 pmax=131.55776 손뼈 로컬 단위 -> 실측으로 환산)
  · 칼끝 속도  : 프레임간 |Δ| / dt. 게임의 타격 게이트가 보는 바로 그 값
  · 루트 모션  : 골반 수평 이동(게임 이동과 이중이 되는지)
  · 발 높이    : 접지 판단
"""
import bpy
import os
import math
import json
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
ANIM = os.path.join(ROOT, "incoming", "meshy_anim")
OUT = ("/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b"
       "/scratchpad/meshy_clips.json")

# basic2 칼 계약(2026-08-12 커밋 75cf433). 손뼈 로컬 좌표계 기준.
BLADE_DIR = Vector((-0.161963, 0.278876, -0.946571))
BLADE_PMAX = 131.55776          # 손뼈 로컬 단위(아마추어 스케일 0.01 이 안 곱해진 값)

CLIPS = [("sword_slash", "Z"), ("axe_chop", "X"), ("left_slash", "C")]

sc = None


def fresh():
    global sc
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.render.fps_base = 1.0


def imp(path):
    b_o = set(o.name for o in sc.objects)
    b_a = set(a.name for a in bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    if sc.render.fps != 30:
        sc.render.fps = 30
    objs = [o for o in sc.objects if o.name not in b_o]
    acts = [a for a in bpy.data.actions if a.name not in b_a]
    arm = next(o for o in objs if o.type == 'ARMATURE')
    return objs, acts, arm


report = {}
for stem, slot in CLIPS:
    fresh()
    objs, acts, arm = imp(os.path.join(ANIM, stem + ".glb"))
    act = acts[0]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    slots = list(getattr(act, "slots", []))
    if slots:
        arm.animation_data.action_slot = slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])

    A2W = arm.matrix_world.copy()
    # 키(발바닥~머리끝) — 메시 바운딩으로
    mesh = next(o for o in objs if o.type == 'MESH' and o.name != 'Icosphere')
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    zs = [(mesh.matrix_world @ v.co).z for v in ev.data.vertices]
    H = max(zs) - min(zs)
    ZLOW = min(zs)
    arm.data.pose_position = "POSE"

    # 칼끝 로컬 벡터: 손뼈 pose 행렬(아마추어 스케일 포함) 안에서 재현되도록
    # BLADE_PMAX 는 basic2 손뼈 로컬 단위다. 두 리그의 손뼈 스케일이 같은
    # 아마추어 스케일(0.01)을 쓰므로 그대로 쓴다.
    tip_local = BLADE_DIR.normalized() * BLADE_PMAX

    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        RH = arm.pose.bones["RightHand"]
        LH = arm.pose.bones["LeftHand"]
        HP = arm.pose.bones["Hips"]
        LF = arm.pose.bones["LeftFoot"]
        RF = arm.pose.bones["RightFoot"]
        Rm = A2W @ RH.matrix
        tip = Rm @ tip_local
        rows.append({
            "f": f,
            "rh": list((A2W @ RH.matrix).translation),
            "lh": list((A2W @ LH.matrix).translation),
            "hip": list((A2W @ HP.matrix).translation),
            "tip": list(tip),
            "lf": (A2W @ LF.matrix).translation.z - ZLOW,
            "rf": (A2W @ RF.matrix).translation.z - ZLOW,
        })
    # 속도(월드 m/s, 30fps)
    for i, r in enumerate(rows):
        if i == 0:
            r["v"] = 0.0
            continue
        p = Vector(rows[i - 1]["tip"])
        c = Vector(r["tip"])
        r["v"] = (c - p).length * 30.0
    for r in rows:
        r["hands"] = (Vector(r["rh"]) - Vector(r["lh"])).length / H
        r["tipz"] = r["tip"][2] - ZLOW

    vmax = max(r["v"] for r in rows)
    imp_f = max(rows, key=lambda r: r["v"])["f"]
    hip0 = Vector(rows[0]["hip"])
    drift = max(math.hypot(r["hip"][0] - hip0.x, r["hip"][1] - hip0.y) for r in rows)
    report[stem] = {"slot": slot, "f0": f0, "f1": f1, "H": H,
                    "sec": (f1 - f0) / 30.0, "rows": rows,
                    "vmax": vmax, "impact_f": imp_f, "root_drift": drift}
    print("=" * 78)
    print("── %s (%s슬롯)  f%d~%d = %.3f초 / 키 %.4f m" % (stem, slot, f0, f1,
                                                          (f1 - f0) / 30.0, H))
    print("   칼끝 최고속 %.1f m/s @ f%d (%.3f초)  / 루트 수평이동 최대 %.4f m"
          % (vmax, imp_f, (imp_f - f0) / 30.0, drift))
    print("   두 손 거리(키 정규화) %.3f ~ %.3f" % (min(r["hands"] for r in rows),
                                                   max(r["hands"] for r in rows)))
    print("   칼끝 지면 여유 %.3f ~ %.3f m" % (min(r["tipz"] for r in rows),
                                              max(r["tipz"] for r in rows)))
    print("   프레임별 (f, 초, 칼끝속도, 두손거리, 칼끝고도, 발높이L/R):")
    for r in rows:
        bar = "#" * int(r["v"] / max(1e-9, vmax) * 40)
        print("     f%-3d %5.3fs  v%7.1f  h%.3f  z%+6.3f  ft %.3f/%.3f  %s"
              % (r["f"], (r["f"] - f0) / 30.0, r["v"], r["hands"], r["tipz"],
                 r["lf"], r["rf"], bar))

with open(OUT, "w") as f:
    json.dump(report, f)
print("[저장] %s" % OUT)
