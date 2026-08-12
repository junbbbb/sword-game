# -*- coding: utf-8 -*-
"""베기 클립이 **세로로 읽히나 · 가로로 읽히나 · 투구 폼이 남았나**를 수치로 잰다.

    A=옛.glb B=web/basic2.glb blender -b -P blender/probe_moves_read.py

실루엣 시트(probe_moves_strip.py)의 눈 판정을 숫자로 뒷받침하는 자다.
게임 카메라는 캐릭터 뒤에서 본다 = 화면 가로 = 몸의 좌우(L) · 화면 세로 = 위아래(U).
그래서 **읽히는 방향은 tipL / tipU 두 값이 정한다**(앞뒤 F 는 화면 깊이라 거의 안 보인다).

  세로성  = |ΔU| / |ΔL|   (X 는 이게 커야 "위->아래"로 읽힌다)
  가로성  = |ΔL| / |ΔU|   (C 는 이게 커야 "옆->옆"으로 읽힌다)
  구간    = 칼끝이 게임 HOT_ON(15.8 m/s) 을 넘는 프레임 = 실제로 보이는 스윙
  투구 프레임 = 오른손이 어깨보다 위(+0.05H) 이고 가슴보다 뒤(+0.20H) 인 프레임.
             오너가 지적한 "야구 체인지업 자세"가 바로 이 둘의 동시 만족이다.
"""
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
PATHS = [("옛", os.environ["A"]), ("새", os.environ["B"])]
CLIPS = [c for c in os.environ.get("CLIPS", "Attack,Heavy,Wide").split(",") if c]
BLADE_DIR = Vector((-0.161963, 0.278876, -0.946571))
BLADE_PMAX = 131.55776
TS = {"Attack": 1.35, "Heavy": 1.15, "Wide": 1.20}
HOT_ON = 15.8

for tag, path in PATHS:
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.render.fps_base = 1.0
    bpy.ops.import_scene.gltf(filepath=path)
    arm = next(o for o in sc.objects if o.type == "ARMATURE")
    for o in list(sc.objects):
        if o.type == "MESH" and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o, do_unlink=True)
    acts = {a.name: a for a in bpy.data.actions}
    if arm.animation_data is None:
        arm.animation_data_create()
    A2W = arm.matrix_world.copy()
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    R = {b.name: (A2W @ b.matrix) for b in arm.pose.bones}
    fw = R["Bip001 L Toe0"].translation - R["Bip001 L Foot"].translation
    fw.z = 0
    FWD = fw.normalized()
    UP = Vector((0, 0, 1))
    LFT = UP.cross(FWD).normalized()
    body = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith("SW_")]
    dg = bpy.context.evaluated_depsgraph_get()
    zs = []
    for m in body:
        ev = m.evaluated_get(dg)
        zs += [(m.matrix_world @ v.co).z for v in ev.data.vertices]
    H = max(zs) - min(zs)
    arm.data.pose_position = "POSE"
    GK = 1.75 / H
    tip_local = BLADE_DIR.normalized() * BLADE_PMAX

    print("=" * 96)
    print("[%s] %s   키 %.4f" % (tag, os.path.basename(path), H))
    for clip in CLIPS:
        act = acts.get(clip)
        if act is None:
            continue
        arm.animation_data.action = act
        try:
            slots = list(getattr(act, "slots", []))
            if slots:
                arm.animation_data.action_slot = slots[0]
        except Exception:
            pass
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        rows = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            P = {b.name: (A2W @ b.matrix) for b in arm.pose.bones}
            hip = P["Bip001 Pelvis"].translation
            hm = P["Bip001 R Hand"]
            # ★아마추어 스케일을 나누지 말 것. hm 이 이미 그 스케일을 갖고 있어
            #   나누면 100배가 된다(아마추어 스케일 0.01). probe_meshy_clips 와 같은 식.
            tip = hm @ tip_local
            rh = hm.translation
            cl = P["Bip001 R Clavicle"].translation
            ch = P["Bip001 Chest2"].translation
            d = tip - hip
            rows.append(dict(
                f=f, tip=tip.copy(),
                L=d.dot(LFT), U=d.dot(UP), F=d.dot(FWD),
                handU=(rh - cl).dot(UP) / H,
                handB=-(rh - ch).dot(FWD) / H))
        ts = TS.get(clip, 1.0)
        for i, r in enumerate(rows):
            r["v"] = 0.0 if i == 0 else (
                (rows[i]["tip"] - rows[i - 1]["tip"]).length * 30.0 * GK * ts)
        hot = [i for i, r in enumerate(rows) if r["v"] > HOT_ON]
        # 유령(캐스트 앞머리)을 뺀 **진짜 스윙 구간**들
        runs, cur = [], []
        for i in hot:
            if cur and i != cur[-1] + 1:
                runs.append(cur)
                cur = []
            cur.append(i)
        if cur:
            runs.append(cur)
        pit = [r for r in rows if r["handU"] > 0.05 and r["handB"] > 0.20]
        print("  %-7s %2d장 %.3f초(게임 %.3f) / 투구 프레임 %d장 (%.3f초, 클립의 %.0f%%)"
              % (clip, len(rows), (len(rows) - 1) / 30.0,
                 (len(rows) - 1) / 30.0 / ts, len(pit), len(pit) / 30.0 / ts,
                 len(pit) * 100.0 / len(rows)))
        for k, run in enumerate(runs):
            a, b = rows[run[0] - 1 if run[0] else 0], rows[run[-1]]
            dL, dU, dF = b["L"] - a["L"], b["U"] - a["U"], b["F"] - a["F"]
            vr = abs(dU) / max(abs(dL), 1e-6)
            print("     스윙%d f%d~%d (클립 %.3f~%.3f / 게임 %.3f~%.3f초)"
                  "  화면 좌우 %+.2f · 상하 %+.2f · 깊이 %+.2f"
                  "  -> 세로성 %.2f / 가로성 %.2f  %s"
                  % (k + 1, a["f"], b["f"], (a["f"] - 1) / 30.0, (b["f"] - 1) / 30.0,
                     (a["f"] - 1) / 30.0 / ts, (b["f"] - 1) / 30.0 / ts,
                     dL, dU, dF, vr, 1 / max(vr, 1e-6),
                     "세로" if vr > 1.6 else ("가로" if vr < 0.62 else "대각")))
