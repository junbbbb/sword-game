# -*- coding: utf-8 -*-
"""칼끝 궤적을 **목표**로 두고 손 위치를 푼다.

왜 이렇게 바꾸나
  지금까지는 (손 위치 + 칼날 방향)을 따로 적었다. 그래서 손 파묻힘을 고치려고
  손을 올렸더니 **칼이 어디로 가는지가 망가졌다**(실측: 수면참 타격이
  좌우 -82 / 상하 -26 로 세로베기가 아니라 가로베기가 됐다).
  스킬의 정체성은 손이 아니라 **칼끝이 그리는 궤적**이다. 그러니 그걸 입력으로 둔다.

풀이
  칼끝 T 가 정해지면, 손(오른 주먹)은 T 를 중심으로 반지름 L(칼 길이)인 **구 위**에
  있어야 한다. 그 구 위를 훑으며 아래를 모두 만족하는 점을 고른다.
    1. 어깨에서 팔 길이 안 (IK 도달)
    2. 왼 주먹이 몸통 밖 (파묻힘 없음)
    3. 손목·어깨·팔꿈치가 사람 가동범위 안
  칼날 방향은 자동으로 (T - 손) 이 된다. 따로 적을 필요가 없다.

실행: SKILL=heavy|wide|attack blender -b -P solve_arcs.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
importlib.reload(CP)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh = next(o for o in bpy.data.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
ps = CP.Poser(arm, H)
FIST = ps.fist_r["l"]
BLADE_L = 0.52          # 칼끝까지 = 키의 0.52 (실측)
R, U, F = CP.RIGHT, CP.UP, CP.FWD

vgn = {g.index: g.name for g in mesh.vertex_groups}
TOR = []
for v in mesh.data.vertices:
    best, bw = None, -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, vgn.get(g.group, "")
    if best and any(x in best.lower() for x in ("spine", "pelvis", "neck")):
        TOR.append(v.index)


# ---------------- 스킬별 칼끝 궤적 (몸통 기준 r, u, f. 키 대비 비율) ----------------
# 수면참: 위에서 아래로 **세로**. 상단세에서 머리 뒤로 넘겼다가 앞·아래로 내려벤다.
# 횡일섬: 왼쪽 아래에서 오른쪽 위로 **비스듬히 올라가며** 옆으로 쓴다.
# 3연타: 袈裟(우상->좌하) / 逆袈裟(좌하->우상) / 내려베기.
ARCS = {
    "heavy": [
        ("HG1", (0.05, 0.40, 0.70)),
        ("HG2", (0.14, 0.78, 0.18)),
        ("HG3", (0.10, 0.86, -0.28)),      # 상단세: 칼이 머리 뒤로
        ("HS", (0.02, -0.10, 0.58)),       # 타격: 아래로 쭉
        ("HE1", (0.00, -0.26, 0.62)),
        ("HE2", (0.02, -0.06, 0.72)),
        ("HR", (0.05, 0.30, 0.74)),
    ],
    "wide": [
        ("XG1", (-0.22, 0.14, 0.74)),
        ("XG2", (-0.58, -0.24, 0.44)),     # 왼쪽 아래로 되감기
        ("XS", (0.72, 0.42, 0.52)),        # 오른쪽 위로 (상승 30도)
        ("XE1", (0.82, 0.54, 0.30)),
        ("XE2", (0.46, 0.46, 0.64)),
        ("XR", (0.16, 0.38, 0.74)),
    ],
    "attack": [
        ("W1", (0.36, 0.80, -0.12)),       # 1타 준비: 오른 어깨 위
        ("S1", (-0.46, -0.16, 0.58)),      # 袈裟: 좌하로
        ("E1", (-0.52, -0.28, 0.50)),
        ("W2", (-0.48, -0.22, 0.48)),      # 2타 준비: 좌하
        ("S2", (0.46, 0.70, 0.44)),        # 逆袈裟: 우상으로
        ("E2", (0.50, 0.78, 0.36)),
        ("W3", (0.06, 0.86, -0.26)),       # 3타 준비: 상단
        ("S3", (0.02, -0.08, 0.60)),       # 내려베기
        ("E3", (0.00, -0.22, 0.64)),
        ("REC", (0.05, 0.32, 0.74)),
    ],
}


def sphere_dirs(n_th=25, n_ph=48):
    out = []
    for i in range(n_th):
        th = math.pi * (i + 0.5) / n_th
        for j in range(n_ph):
            ph = 2 * math.pi * j / n_ph
            out.append(Vector((math.sin(th) * math.cos(ph),
                               math.sin(th) * math.sin(ph),
                               math.cos(th))))
    return out


DIRS = sphere_dirs()
REJ = {}


def evaluate(pose_tpl, hand_ruf, tip_ruf):
    """손을 hand 에 두고 칼끝이 tip 을 향하도록 포즈를 만들고 채점."""
    org = ps.origin()
    hp = org + (R * hand_ruf[0] + U * hand_ruf[1] + F * hand_ruf[2]) * H
    tp = org + (R * tip_ruf[0] + U * tip_ruf[1] + F * tip_ruf[2]) * H
    bd = (tp - hp)
    if bd.length < 1e-6:
        return None
    bd.normalize()
    bl = []
    for key, op, val in pose_tpl["b"]:
        if op == CP.IK and key == "r":
            bl.append((key, op, tuple(hand_ruf)))
        elif op == CP.BLADE:
            bl.append((key, op, (bd.dot(R), bd.dot(U), bd.dot(F))))
        else:
            bl.append((key, op, val))
    pose = dict(pose_tpl, b=bl)
    ps.reach_log = []
    ps.apply(pose)
    bpy.context.view_layer.update()
    if ps.reach_log:
        REJ["도달못함"] = REJ.get("도달못함", 0) + 1
        return None
    # 관절 한계
    wpen = 0.0
    for s in ("l", "r"):
        sh, el, wr = (ps.wpos("%s upperarm" % s), ps.wpos("%s forearm" % s),
                      ps.wpos("%s hand" % s))
        pw = ps.palm_world(s)
        if not (sh and el and wr and pw):
            continue
        a, b = (wr - el), (pw - wr)
        if a.length > 1e-9 and b.length > 1e-9:
            w = math.degrees(a.angle(b))
            if s == "r":
                if w > 80.0:            # 오른손은 우리가 직접 제어하므로 한계로 건다
                    REJ["오른 손목꺾임"] = REJ.get("오른 손목꺾임", 0) + 1
                    return None
            else:
                # ★왼손은 자루에 끌려가므로 각도를 직접 못 정한다. 하드 제약으로 걸면
                # 모든 해가 죽는다. 벌점으로만 쓰고 결함은 따로 기록한다.
                wpen += max(0.0, w - 80.0) / 40.0
        # ★어깨는 '팔이 반대편으로 얼마나 넘어갔나'로 본다. atan2(옆, 아래)로 재면
        # 팔을 **앞으로** 든 자세에서 아래 성분이 0 이라 값이 폭발한다(잣대 오류였다).
        ua = (el - sh).normalized()
        trunk = (ps.wpos("neck") - ps.wpos("pelvis")).normalized()
        lat = (R * (1 if s == "r" else -1))
        lat = (lat - trunk * lat.dot(trunk)).normalized()
        # 사람은 팔을 반대쪽 어깨까지 가져갈 수 있다(수평 내전 ~130도).
        # -0.62(38도)로 잡았더니 **왼쪽으로 베는 자세가 전부 탈락**했다.
        if ua.dot(lat) < -0.88:            # 정중선을 62도 넘게 가로지름
            REJ["팔이 몸 가로지름"] = REJ.get("팔이 몸 가로지름", 0) + 1
            return None
    # 왼 주먹 몸통 여유
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    P = [ev.matrix_world @ v.co for v in me.vertices]
    lp = ps.palm_world("l")
    band = [P[j] for j in TOR if abs(P[j].z - lp.z) < H * 0.045]
    ev.to_mesh_clear()
    clr = 9.0
    if band:
        org2 = ps.origin()
        d = lp - org2
        d.z = 0
        if d.length > 1e-6:
            n = d.normalized()
            surf = max((p - org2).dot(n) for p in band)
            clr = (d.length - surf) / FIST
    if clr < 0.15:
        REJ["손 파묻힘"] = REJ.get("손 파묻힘", 0) + 1
        return None
    # 실제 칼끝이 목표에 얼마나 가까운가
    pwr = ps.palm_world("r")
    tip = pwr + ps.blade_dir() * (H * BLADE_L)
    dd = tip - org
    got = (dd.dot(R) / H, dd.dot(U) / H, dd.dot(F) / H)
    err = math.sqrt(sum((got[i] - tip_ruf[i]) ** 2 for i in range(3)))
    return err, clr, got, wpen


SK = os.environ.get("SKILL", "heavy")
SEQ = {"heavy": CP.HEAVY_SEQ, "wide": CP.WIDE_SEQ, "attack": CP.SEQ}[SK]
NAMES = {id(p): n for n, p in [(nm, getattr(CP, nm)) for nm, _ in ARCS[SK]]}

print("\n=== %s: 칼끝 궤적으로 손 위치 풀기 ===" % SK)
for nm, tip in ARCS[SK]:
    pose = getattr(CP, nm)
    # ★후보를 먼저 싸게 거른다. 칼끝 구(반지름 0.52)와 팔 길이 구(0.309)의 교집합은
    # **얇은 띠**라, 성긴 격자로는 대부분 도달 불가 지점만 뽑힌다(실측: 203 중 189).
    ps.reset()
    ps.apply(pose)
    bpy.context.view_layer.update()
    org = ps.origin()
    shw = ps.wpos("r upperarm")
    sh_ruf = ((shw - org).dot(R) / H, (shw - org).dot(U) / H, (shw - org).dot(F) / H)
    REACH = 0.309
    # ★어깨에서 칼끝까지의 물리 상한 = 팔 0.309 + 칼 0.52 = 0.83 H.
    # 게다가 팔을 완전히 펴면(굴곡 0도) 과신전 경계라 실용 상한은 0.76 정도다.
    # 내가 처음 적은 궤적은 0.83~0.90 이라 **닿을 수 없는 곳**이었다(횡일섬 전 키 해 없음).
    MAXR = 0.76
    dsh = math.sqrt(sum((tip[i] - sh_ruf[i]) ** 2 for i in range(3)))
    if dsh > MAXR:
        k = MAXR / dsh
        tip = tuple(sh_ruf[i] + (tip[i] - sh_ruf[i]) * k for i in range(3))
        print("     [%s] 칼끝이 어깨에서 %.2f H -> 닿는 한계 %.2f 로 당김  %s"
              % (nm, dsh, MAXR, tuple(round(v, 2) for v in tip)))
    best = None
    REJ.clear()
    tried = 0
    for d in DIRS:
        # 손 = 칼끝에서 칼 길이만큼 뒤
        hr = (tip[0] - d.x * BLADE_L, tip[1] - d.y * BLADE_L, tip[2] - d.z * BLADE_L)
        if hr[1] < -0.20 or hr[1] > 0.50:      # 손이 무릎 아래/머리 위로 가면 제외
            continue
        if hr[2] < -0.05:                       # 손이 몸 뒤로
            continue
        dsq = sum((hr[i] - sh_ruf[i]) ** 2 for i in range(3))
        if dsq > REACH * REACH * 0.99:          # 팔이 안 닿는 후보는 포즈 계산 전에 버린다
            REJ["도달못함(사전)"] = REJ.get("도달못함(사전)", 0) + 1
            continue
        tried += 1
        r = evaluate(pose, hr, tip)
        if r is None:
            continue
        err, clr, got, wpen = r
        # 칼끝 오차가 최우선, 그다음 손이 중단세 높이(0.19)에 가까울수록 좋다
        cost = err * 10.0 + abs(hr[1] - 0.19) * 1.5 \
            + max(0.0, 0.30 - clr) * 2.0 + wpen * 2.0
        if best is None or cost < best[0]:
            best = (cost, hr, err, clr, got, wpen)
    if best is None:
        print("  %-4s 해 없음 | 시도 %d, 탈락 사유 %s"
              % (nm, tried, ", ".join("%s %d" % kv for kv in sorted(REJ.items()))))
        continue
    _, hr, err, clr, got, wpen = best
    print("  %-4s IK (%.2f, %.2f, %.2f)  칼끝오차 %.3f  여유 %.2f주먹%s"
          % (nm, hr[0], hr[1], hr[2], err, clr,
             ("  ※왼손목 초과 %.0f도" % (wpen * 40)) if wpen > 0.01 else ""))
