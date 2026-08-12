# -*- coding: utf-8 -*-
"""Meshy 프리셋 3종의 **스윙 평면**과 **와인드업**을 실측한다(14-베기수정, 2026-08-12).

    blender -b -P blender/probe_meshy_plane.py

probe_meshy_clips.py 가 "언제 빠른가"(칼끝 속도)를 쟀다면 이 파일은
**"어느 평면으로 베는가 / 팔이 어깨 위로 감기는가"** 를 잰다. 오너 지시가
"X 는 세로, C 는 가로, 투구 폼 금지"라 그 둘이 곧 합격 기준이다.

찍는 것 (전부 **레스트 정면 기준 몸 좌표**. 게임은 캐릭터 yaw 를 자기가 주므로
레스트 정면이 곧 게임에서의 '앞'이다)
  F 앞(+)/뒤(-) · L 왼(+)/오른(-) · U 위(+)/아래(-)
  · tipF/tipL/tipU  골반 기준 칼끝 위치
  · vF/vL/vU        칼끝 속도 성분(m/s)
  · vert%           |vU| / |v| — 100 이면 순수 위아래, 0 이면 순수 수평
  · lat%            |vL| / |vFL| — 수평 성분 중 좌우 비율(가로베기는 여기가 커야 한다)
  · handU           오른손 - 어깨(Clavicle) 높이. **+0.05H 넘으면 팔이 어깨 위**
  · handB           오른손이 가슴 뒤로 간 양(+ = 뒤). 투구 폼은 handU>0 & handB>0
  · 평면법선        구간별로 칼끝 궤적에 평면을 맞춰 법선을 몸 좌표로 찍는다
                    법선이 U 에 가까우면 **수평 스윙**, L 에 가까우면 **시상면(세로)**
"""
import bpy
import os
import math
import json
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
ANIM = os.path.join(ROOT, "incoming", "meshy_anim")
OUT = os.environ.get(
    "OUT", "/private/tmp/claude-501/-Users-lbj/"
    "83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad/meshy_plane.json")

BLADE_DIR = Vector((-0.161963, 0.278876, -0.946571))
BLADE_PMAX = 131.55776

CLIPS = [c for c in os.environ.get(
    "CLIPS", "sword_slash,axe_chop,left_slash").split(",") if c]
WIN = int(os.environ.get("WIN", "5"))          # 평면 맞춤 창(프레임)

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


def plane_normal(pts):
    """점무리에 평면을 맞춰 법선(최소 고유벡터)과 평면성(고유값 비)을 돌려준다."""
    n = len(pts)
    c = Vector((0, 0, 0))
    for p in pts:
        c += p
    c /= n
    M = [[0.0] * 3 for _ in range(3)]
    for p in pts:
        d = p - c
        for i in range(3):
            for j in range(3):
                M[i][j] += d[i] * d[j]
    m = Matrix(M)
    # 대칭행렬 고유분해: 파워법으로 최소축을 찾는다(3x3, 반복 60회면 충분)
    inv = None
    try:
        # 최소 고유벡터 = (M + eps I)^-1 의 최대 고유벡터
        tr = sum(M[i][i] for i in range(3)) / 3.0 or 1.0
        reg = Matrix.Identity(3) * (tr * 1e-6)
        inv = (m + reg).inverted()
    except Exception:
        return Vector((0, 0, 1)), 1.0
    v = Vector((0.31, 0.53, 0.79)).normalized()
    for _ in range(80):
        v = (inv @ v)
        if v.length < 1e-20:
            return Vector((0, 0, 1)), 1.0
        v.normalize()
    # 평면성: 법선 방향 분산 / 전체 분산
    num = (m @ v).dot(v)
    den = sum(M[i][i] for i in range(3)) or 1e-12
    return v, num / den


report = {}
for stem in CLIPS:
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

    mesh = next(o for o in objs if o.type == 'MESH' and o.name != 'Icosphere')
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    zs = [(mesh.matrix_world @ v.co).z for v in ev.data.vertices]
    H = max(zs) - min(zs)
    ZLOW = min(zs)
    # ── 레스트 정면(발목->발끝. s24 와 같은 잣대) ──
    RB = {b.name: (A2W @ b.matrix) for b in arm.pose.bones}
    fw = (RB["LeftToeBase"].translation - RB["LeftFoot"].translation)
    fw.z = 0
    FWD = fw.normalized()
    UP = Vector((0, 0, 1))
    LFT = UP.cross(FWD).normalized()          # 위 x 앞 = 왼쪽
    arm.data.pose_position = "POSE"

    def body(v):
        """월드 벡터를 몸 좌표 (앞, 왼, 위) 로."""
        return Vector((v.dot(FWD), v.dot(LFT), v.dot(UP)))

    tip_local = BLADE_DIR.normalized() * BLADE_PMAX
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        P = {b.name: (A2W @ b.matrix) for b in arm.pose.bones}
        hip = P["Hips"].translation
        tip = P["RightHand"] @ tip_local
        rh = P["RightHand"].translation
        cl = P["RightShoulder"].translation      # 쇄골 = 어깨 관절
        ch = P["Spine02"].translation            # 가슴
        bt = body(tip - hip)
        bh = body(rh - cl)
        rows.append({
            "f": f,
            "tip": list(tip), "tipb": list(bt),
            "tipz": tip.z - ZLOW,
            "handU": bh.z / H, "handB": -bh.x / H, "handL": bh.y / H,
            "rh": list(rh), "hipz": hip.z - ZLOW,
            "chestb": list(body(rh - ch)),
        })
    for i, r in enumerate(rows):
        if i == 0:
            r["v"] = 0.0
            r["vb"] = [0, 0, 0]
            continue
        d = (Vector(rows[i]["tip"]) - Vector(rows[i - 1]["tip"])) * 30.0
        r["v"] = d.length
        r["vb"] = list(body(d))

    # 구간 평면(창 WIN 프레임 슬라이딩)
    for i, r in enumerate(rows):
        a = max(0, i - WIN // 2)
        b = min(len(rows), a + WIN)
        pts = [Vector(rows[k]["tip"]) for k in range(a, b)]
        nv, flat = plane_normal(pts)
        nb = body(nv)
        if nb.z < 0:
            nb = -nb
        r["nrm"] = list(nb)
        r["flat"] = flat

    vmax = max(r["v"] for r in rows)
    report[stem] = {"f0": f0, "f1": f1, "H": H, "sec": (f1 - f0) / 30.0,
                    "rows": rows, "vmax": vmax}
    print("=" * 108)
    print("── %s  f%d~%d = %.3f초 / 키 %.4f / 칼끝최고 %.1f m/s"
          % (stem, f0, f1, (f1 - f0) / 30.0, H, vmax))
    print("   정면 (%.2f,%.2f) / 왼쪽 (%.2f,%.2f)"
          % (FWD.x, FWD.y, LFT.x, LFT.y))
    print("   f    sec     v   |  tipF   tipL   tipU |   vF     vL     vU  |"
          " vert%  lat% | handU  handB | 법선(F,L,U)      평면성")
    for r in rows:
        v = r["v"]
        vb = r["vb"]
        hor = math.hypot(vb[0], vb[1])
        vert = abs(vb[2]) / v * 100 if v > 1e-6 else 0
        lat = abs(vb[1]) / hor * 100 if hor > 1e-6 else 0
        wind = "★투구" if (r["handU"] > 0.05 and r["handB"] > 0.02) else (
            "  위 " if r["handU"] > 0.05 else "     ")
        print("   %-4d %5.3f %6.1f | %+6.2f %+6.2f %+6.2f | %+6.1f %+6.1f %+6.1f"
              " | %5.1f %5.1f | %+5.3f %+5.3f %s | %+5.2f %+5.2f %+5.2f  %.4f"
              % (r["f"], (r["f"] - f0) / 30.0, v, r["tipb"][0], r["tipb"][1],
                 r["tipb"][2], vb[0], vb[1], vb[2], vert, lat,
                 r["handU"], r["handB"], wind,
                 r["nrm"][0], r["nrm"][1], r["nrm"][2], r["flat"]))

with open(OUT, "w") as f:
    json.dump(report, f)
print("[저장] %s" % OUT)
