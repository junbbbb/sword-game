# -*- coding: utf-8 -*-
"""콤보 스윙 검증기 (검도 자세 / 양손 파지 기준).

판정 기준 3가지:
  1. 앞에서 벤다 — 칼끝이 **머리 높이 아래(u<0.45)** 에 있는 동안은 항상 몸 앞(f>0.12).
     머리 위로 젖히는 상단세만 예외. 이전 판정식은 어깨 높이 옆구리 통과를 놓쳤다.
  2. 양손 파지 — 왼손이 자루에서 떨어지지 않는다.
  3. IK 도달 — 팔이 늘어나지 않는다(못 닿으면 팔이 뻗어 어색해진다).
실행: blender --background --python tune_swing.py   (NORENDER=1 이면 수치만)
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
OUT = os.path.join(ROOT, "renders", "swing")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
importlib.reload(CP)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"

arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh_ob = next(o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("Floor", "Plane")))
katana = bpy.data.objects.get("katana_slayer")
if arm.animation_data:
    arm.animation_data_clear()

zs = [(mesh_ob.matrix_world @ v.co).z for v in mesh_ob.data.vertices]
xs = [(mesh_ob.matrix_world @ v.co).x for v in mesh_ob.data.vertices]
H = max(zs) - min(zs)
FOOT = min(zs)
CTRX = (min(xs) + max(xs)) / 2
SWS = H * float(os.environ.get("KATANA_SCALE", "0.56"))

ps = CP.Poser(arm, H)
TIP_L = Vector((0.86 * SWS, 0, 0))       # 칼 로컬 +X = 칼끝
# 왼손 판정은 **자루 축까지의 수직 거리**로 한다. 특정 지점(물미)을 기대하면
# 양손 간격(GB)을 바꿀 때마다 기준이 어긋난다. 축 방향 위치는 GRIP 이 보장한다.
R, U, F = CP.RIGHT, CP.UP, CP.FWD
HEAD_U = 0.45        # 정수리 높이. 이 위에서만 칼이 뒤로 넘어가도 된다
FRONT_MIN = 0.12     # 그 아래에서는 항상 이만큼 앞에 있어야 한다


def to_ruf(p, org):
    d = Vector(p) - org
    return (d.dot(R) / H, d.dot(U) / H, d.dot(F) / H)


SKILL = os.environ.get("SKILL", "combo")
if SKILL == "wide":
    KEYS = [("GUARD", CP.GUARD), ("XG1", CP.XG1), ("XG1B", CP.XG1B),
            ("XG2", CP.XG2), ("XM1", CP.XM1), ("XM2", CP.XM2), ("XS0", CP.XS0),
            ("XS", CP.XS), ("XE1", CP.XE1), ("XE1B", CP.XE1B),
            ("XE2", CP.XE2), ("XR", CP.XR)]
    SEQ, LAST = CP.WIDE_SEQ, CP.WIDE_LAST
    WF, SF, TR, IMP = (CP.WIDE_WINDUP_F, CP.WIDE_STRIKE_F,
                       CP.WIDE_TRAILS, CP.WIDE_IMPACTS)
    OUT = os.path.join(ROOT, "renders", "wide")
    os.makedirs(OUT, exist_ok=True)
elif SKILL == "heavy":
    KEYS = [("GUARD", CP.GUARD), ("HG1", CP.HG1), ("HG2", CP.HG2), ("HG3", CP.HG3),
            ("HM1", CP.HM1), ("HM2", CP.HM2), ("HM3", CP.HM3),
            ("HS", CP.HS), ("HE1", CP.HE1), ("HE1B", CP.HE1B),
            ("HE2", CP.HE2), ("HR", CP.HR)]
    SEQ, LAST = CP.HEAVY_SEQ, CP.HEAVY_LAST
    WF, SF, TR, IMP = (CP.HEAVY_WINDUP_F, CP.HEAVY_STRIKE_F,
                       CP.HEAVY_TRAILS, CP.HEAVY_IMPACTS)
    OUT = os.path.join(ROOT, "renders", "heavy")
    os.makedirs(OUT, exist_ok=True)
else:
    KEYS = [("GUARD", CP.GUARD),
            ("W1", CP.W1), ("A1A", CP.A1A), ("A1B", CP.A1B),
            ("S1", CP.S1), ("E1", CP.E1), ("E1B", CP.E1B),
            ("A2A", CP.A2A), ("A2B", CP.A2B),
            ("S2", CP.S2), ("A2C", CP.A2C), ("E2", CP.E2), ("E2B", CP.E2B),
            ("W3", CP.W3), ("A3A", CP.A3A), ("A3B", CP.A3B), ("A3C", CP.A3C),
            ("S3", CP.S3), ("E3", CP.E3), ("E3B", CP.E3B), ("REC", CP.REC)]
    SEQ, LAST = CP.SEQ, CP.LAST
    WF, SF, TR, IMP = CP.WINDUP_F, CP.STRIKE_F, CP.TRAILS, CP.IMPACTS
print("SKILL =", SKILL)

print("=== 키포즈 (몸통 기준, 키 H 정규화) ===")
# ★어깨 위치와 팔 길이도 같이 찍는다. 손을 어디까지 놓을 수 있는지는 상수가 아니다 —
# 척추를 숙이고 비틀면 어깨가 통째로 움직여서 같은 (r,u,f) 가 닿기도 하고 안 닿기도 한다.
# 이걸 모르고 "낮고 왼쪽" 손 자리를 적었다가 IK 가 1.6 배까지 늘어난 적이 있다(v74).
print("%-6s | %-18s | %-18s | %-5s %-5s | %-18s %-5s | %s" % (
    "pose", "오른손 (r,u,f)", "칼끝 (r,u,f)", "왼손", "IK",
    "오른어깨 (r,u,f)", "팔길이", "판정"))
bad = []
for nm, p in KEYS:
    ps.reach_log = []
    ps.apply(p)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    org = ps.origin()
    KM = katana.evaluated_get(dg).matrix_world
    rh = ps.wpos("r hand")
    lh = ps.wpos("l hand")
    tip = KM @ TIP_L
    ax = (KM.to_3x3() @ Vector((1, 0, 0))).normalized()
    ga = KM.translation
    hr, tr = to_ruf(rh, org), to_ruf(tip, org)
    # ★파지 판정은 반드시 **주먹 중심**으로. 예전엔 손목과 자루축 거리를 재고
    # "주먹은 0.072 H 더 나가 있으니 그 값이면 쥔 것"이라고 봤는데, 손목→주먹
    # 오프셋은 방향이 팔 자세마다 달라서 그 논리가 성립하지 않는다.
    # 실제로는 왼 주먹이 자루에서 주먹 1.1~2.4 개 떨어져 있는데도 계속 OK 가 떴다.
    lp = ps.palm_world("l")
    _v = (lp if lp is not None else lh) - ga
    grip_err = (_v - ax * _v.dot(ax)).length / H
    flag = []
    if tr[1] < HEAD_U and tr[2] < FRONT_MIN and not p.get("wind"):
        flag.append("칼끝이 앞이 아님(f%+.2f)" % tr[2])
    # 주먹 반지름 0.069 H. 그 1/3 을 넘게 벗어나면 쥔 것으로 안 보인다.
    if grip_err > 0.023 and not p.get("1h"):
        flag.append("왼 주먹 자루 이탈 %.3f" % grip_err)
    if p.get("1h"):
        flag.append("[한손 신전]")
    if ps.reach_log:
        flag.append("IK 못닿음 %s" % ps.reach_log)
    if [f for f in flag if not f.startswith('[')]:
        bad.append(nm)
    sh = ps.wpos("r upperarm")
    el = ps.wpos("r forearm")
    reach = ((el - sh).length + (rh - el).length) / H
    sr = to_ruf(sh, org)
    print("%-6s | %5.2f %5.2f %5.2f | %5.2f %5.2f %5.2f | %5.2f %5s | "
          "%5.2f %5.2f %5.2f %6.3f | %s" % (
              nm, hr[0], hr[1], hr[2], tr[0], tr[1], tr[2], grip_err,
              "OK" if not ps.reach_log else "NG", sr[0], sr[1], sr[2], reach,
              "OK" if not flag else " / ".join(flag)))

# ---------------- 실제 애니메이션 궤적 ----------------
arm.animation_data_create()
act = bpy.data.actions.new("combo")
arm.animation_data.action = act
try:
    act.slots.new(id_type="OBJECT", name="S")
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
for f, p in SEQ:
    ps.apply(p)
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("location", frame=f)
    arm.keyframe_insert("location", frame=f)
try:
    for lay in act.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        fr = int(round(kp.co[0]))
                        kp.interpolation = "QUAD" if fr in (WF | SF) else "BEZIER"
                        kp.easing = ("EASE_IN" if fr in WF
                                     else "EASE_OUT" if fr in SF else "EASE_IN_OUT")
except Exception:
    pass
# 게임 익스포트(s6)와 같은 파지 재고정을 걸어야 검증이 실제와 같아진다.
print("파지 재고정: %d 프레임" % CP.relock_grip(ps, SEQ))

print()
print("=== 실제 궤적(1/4 프레임 샘플링) ===")
SUB = 4
dg = bpy.context.evaluated_depsgraph_get()
verdicts = []
for ti, (r0, r1) in enumerate(TR):
    pts, grips = [], []
    for si in range((r1 - r0) * SUB + 1):
        f = r0 + si / SUB
        sc.frame_set(int(f), subframe=f - int(f))
        org = ps.origin()
        KM = katana.evaluated_get(dg).matrix_world
        pts.append(to_ruf(KM @ TIP_L, org))
        _ax = (KM.to_3x3() @ Vector((1, 0, 0))).normalized()
        # 키프레임이 다 맞아도 **사이 프레임**에서 손이 자루를 놓칠 수 있다.
        # 본은 쿼터니언으로 보간되는데 주먹 위치는 그 보간을 따라가지 않는다.
        _lp = ps.palm_world("l")
        _vv = (_lp if _lp is not None else ps.wpos("l hand")) - KM.translation
        grips.append((_vv - _ax * _vv.dot(_ax)).length / H)
    dr = max(p[0] for p in pts) - min(p[0] for p in pts)
    du = max(p[1] for p in pts) - min(p[1] for p in pts)
    # 되감기 구간(타격 직전까지)은 몸 뒤로 재껴도 된다 - 그게 사거리를 만든다.
    # ★기준을 WINDUP_F 에서 IMPACTS 로 옮겼다. 통과점 방식으로 바뀌면서 타이밍이
    #   이징 세트가 아니라 통과점 u 표에 들어갔고, WINDUP_F 는 빈 집합이 됐다.
    wf = IMP[ti] - 2 if ti < len(IMP) else (max(WF) if WF else 0)
    behind = [p for j, p in enumerate(pts)
              if p[1] < HEAD_U and p[2] < FRONT_MIN
              and (r0 + j / SUB) > wf + 0.5]
    ok = not behind
    verdicts.append(ok)
    print("  구간%d  칼끝 이동 좌우 %.2f 상하 %.2f | 머리 아래인데 앞이 아닌 프레임 %d | 왼손 최대이탈 %.2f -> %s"
          % (ti + 1, dr, du, len(behind), max(grips), "OK" if ok else "NG"))
    print("        r: " + " ".join("%+.2f" % p[0] for p in pts[::SUB]))
    print("        u: " + " ".join("%+.2f" % p[1] for p in pts[::SUB]))
    print("        f: " + " ".join("%+.2f" % p[2] for p in pts[::SUB]))

worst = None
for si in range((LAST - 1) * SUB + 1):
    f = 1 + si / SUB
    sc.frame_set(int(f), subframe=f - int(f))
    p = to_ruf(katana.evaluated_get(dg).matrix_world @ TIP_L, ps.origin())
    # 되감기 구간(각 타격의 통과 시작 ~ 임팩트 2프레임 전)은 몸 뒤로 넘어가도 된다
    windup = any(t0 - 4 <= f <= im - 2 for (t0, _), im in zip(TR, IMP))
    if p[1] < HEAD_U and p[2] < FRONT_MIN and not windup and f < LAST - 8:
        if worst is None or p[2] < worst[1][2]:
            worst = (f, p)
print()
print("=== 전체 구간(1~%d) ===" % LAST)
if worst is None:
    print("  칼끝이 머리 아래에 있을 땐 항상 몸 앞 - OK")
else:
    print("  프레임 %.2f 칼끝 (r %+.2f u %+.2f f %+.2f) 이 몸 뒤/옆 - NG"
          % (worst[0], worst[1][0], worst[1][1], worst[1][2]))
    verdicts.append(False)

# ---------------- 렌더 ----------------
if os.environ.get("NORENDER") != "1":
    li = bpy.data.lights.new("S", "SUN")
    li.energy = 4.5
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = (math.radians(58), 0, math.radians(-30))
    sc.collection.objects.link(so)
    cam = sc.camera
    if cam is None:
        cd = bpy.data.cameras.new("C")
        cam = bpy.data.objects.new("C", cd)
        sc.collection.objects.link(cam)
        sc.camera = cam
    cam.data.lens = 45
    CTR = Vector((CTRX, 0, FOOT + H * 0.58))
    VIEWS = {
        "front": CTR + Vector((0, -H * 2.4, H * 0.16)),
        "side": CTR + Vector((-H * 2.4, 0, H * 0.16)),
        "top": CTR + Vector((0, -0.001, H * 2.5)),
    }
    sc.render.resolution_x = 440
    sc.render.resolution_y = 540
    arm.animation_data_clear()
    for nm, p in KEYS:
        ps.apply(p)
        for vn, pos in VIEWS.items():
            cam.location = pos
            d = CTR - pos
            cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (nm, vn))
            bpy.ops.render.render(write_still=True)
    print("rendered ->", OUT)

print("KEY BAD:", bad if bad else "none")
print("SWING:", "ALL OK" if all(verdicts) else "NG %s" % [i + 1 for i, v in enumerate(verdicts) if not v])
print("DONE")
