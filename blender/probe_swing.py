# -*- coding: utf-8 -*-
"""★검사 베기의 **칼끝 높이**를 프레임별로 잰다.

왜 필요한가: 눈에 보이는 궤적과 실제로 벨 수 있는 높이가 따로 놀았다.
칼끝이 어깨 위로만 지나가서 키 1.30 짜리 고블린 머리 위를 스쳤다.

재는 방법은 web/main.js 의 measureBlade() 를 그대로 옮긴 것이다.
  · 손 본에 100% 웨이트로 붙은 정점(= 칼)을 모은다
  · 그 정점을 **손 본 레스트 로컬**로 되돌린다(= glTF 의 inverse bind matrix)
  · 원점에서 가장 먼 점의 방향을 칼날 축 dir 로 잡고, 축 위 최대 투영 pmax 를 잰다
  · 코등이 A = dir*pmax*0.18, 칼끝 B = dir*pmax*0.98
  · 매 프레임 (A2W @ pb.matrix) 를 곱해 월드로 옮긴다

s6_export_game.py 가 굽는 것과 **같은 절차**로 자루를 만들고 액션을 만든다.
액션 생성 코드는 s6 의 make_action 을 그대로 옮겼다(export 만 뺐다).

실행: blender -b -P probe_swing.py -- [--sword baekah] [--dist 1.0]
"""
import bpy
import os
import sys
import math
import json
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
import swords as SW
importlib.reload(CP)
importlib.reload(SW)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(name, dflt):
    return argv[argv.index(name) + 1] if name in argv else dflt

SWORD_KEY = opt("--sword", "baekah")     # 게임 기본값 swordIdx=1 = 백아
OUT_JSON = opt("--out", "")
TAG = opt("--tag", "now")
WRIST = opt("--wrist", "")               # 손목 제한 실험용. none = 제한 해제
if WRIST:
    CP.Poser.WRIST_MAX = None if WRIST == "none" else float(WRIST)
    print("### WRIST_MAX =", CP.Poser.WRIST_MAX)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
CHAR_H = max(zs) - min(zs)
FLOOR0 = min(zs)

# ---------- s6 와 동일하게 레스트로 되돌리고 자루 자세를 뽑는다 ----------
for _b in arm.pose.bones:
    _b.rotation_mode = "QUATERNION"
    _b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
HAND = next(b.name for b in arm.pose.bones if "r hand" in b.name.lower())
kat = bpy.data.objects.get("katana_slayer")
GRIP_M = kat.matrix_world.copy() if kat else Matrix()

SW_SCALE = CHAR_H * 0.235
v = next(x for x in SW.VARIANTS if x["key"] == SWORD_KEY)
root_ob = SW.build_sword(v, scale=SW_SCALE)
root_ob.matrix_world = GRIP_M @ root_ob.matrix_world
bpy.context.view_layer.update()

# 칼 정점을 월드(레스트)에서 모은다
pts_w = []
for c in root_ob.children_recursive:
    if c.type != "MESH":
        continue
    dg = bpy.context.evaluated_depsgraph_get()
    ev = c.evaluated_get(dg)
    me = ev.to_mesh()
    mw = c.matrix_world
    for p in me.vertices:
        pts_w.append(mw @ p.co)
    ev.to_mesh_clear()

RESTW = arm.matrix_world @ arm.data.bones[HAND].matrix_local
INV = RESTW.inverted()
pts = [INV @ p for p in pts_w]
far = max(pts, key=lambda p: p.length_squared)
DIR = far.normalized()
PMAX = max(p.dot(DIR) for p in pts)
BLADE_A = DIR * (PMAX * 0.18)     # 코등이 조금 앞
BLADE_B = DIR * (PMAX * 0.98)     # 칼끝

arm.data.pose_position = "POSE"
bpy.context.view_layer.update()
# 자루는 재고 나면 방해만 된다(액션 굽는 데 필요 없음)
for c in list(root_ob.children_recursive):
    bpy.data.objects.remove(c, do_unlink=True)
bpy.data.objects.remove(root_ob, do_unlink=True)

ps = CP.Poser(arm, CHAR_H)
A2W = arm.matrix_world
HB = ps.pb("r hand")
# 칼날 길이(월드) = 손 본 스케일까지 반영된 실제 길이
_hm = A2W @ arm.data.bones[HAND].matrix_local
_len = ((_hm @ BLADE_B) - (_hm @ BLADE_A)).length
print("H=%.4f floor=%.4f  칼[%s] 축길이(로컬)%.4f  칼날구간 월드길이 %.4f"
      % (CHAR_H, FLOOR0, SWORD_KEY, PMAX, _len))


def blade_world():
    """지금 포즈에서 (코등이, 칼끝) 월드 좌표."""
    M = A2W @ HB.matrix
    return M @ BLADE_A, M @ BLADE_B


# ---------- s6.make_action 을 그대로 옮김 (export 만 없음) ----------
def key_pose(f, root=False):
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("location", frame=f)
    if root:
        arm.keyframe_insert("location", frame=f)


def make_action(name, frames, accel=(), decel=(), root=False, linear=()):
    if arm.animation_data:
        arm.animation_data_clear()
    arm.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    try:
        slot = act.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = slot
    except Exception:
        pass
    for f, spec in frames:
        ps.apply(spec if isinstance(spec, dict) else {"b": spec})
        key_pose(f, root)
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            fr = int(round(kp.co[0]))
                            if fr in linear:
                                kp.interpolation = "LINEAR"
                            elif fr in accel:
                                kp.interpolation, kp.easing = "QUAD", "EASE_IN"
                            elif fr in decel:
                                kp.interpolation, kp.easing = "QUAD", "EASE_OUT"
                            else:
                                kp.interpolation, kp.easing = "BEZIER", "EASE_IN_OUT"
    except Exception:
        pass
    CP.relock_grip(ps, frames)
    return act


# ---------- 게임 좌표로 환산 ----------
# ★블렌더 단위 != 게임 단위. main.js 는 바인드 박스 높이를 목표 키 1.75 로 정규화한다
#   (m.scale.setScalar(cfg.h / h)). 그리고 groundFeet() 가 매 프레임 **가장 낮은
#   발 본**을 바닥(root.y + 키*0.045)에 붙인다. 그래서 게임에서의 칼끝 높이는
#   "칼끝 - 최저 발 본" 을 스케일한 값 + 발바닥 두께다. 루트를 내려 주저앉는
#   수면참·횡일섬은 이 보정을 빼면 높이가 통째로 틀린다.
GAME_H = 1.75
S = GAME_H / CHAR_H
SOLE = GAME_H * 0.045
FOOT_BONES = [b for b in arm.pose.bones
              if ("foot" in b.name.lower() or "toe" in b.name.lower())]
print("스케일 %.5f (블렌더 %.4f -> 게임 %.2f) / 발 본 %s"
      % (S, CHAR_H, GAME_H, [b.name for b in FOOT_BONES]))
_hw = A2W @ arm.data.bones[HAND].matrix_local
print("칼: 손 본에서 칼끝까지 %.4f 게임m / 칼날구간 %.4f 게임m"
      % (((_hw @ BLADE_B) - _hw.translation).length * S, _len * S))

# ---------- 고블린 캡슐 (게임 단위) ----------
GOB_H = 1.30
CAP_LO, CAP_HI, CAP_R = 0.20, 0.74, 0.40
BLADE_PAD = 0.14
FWD, RIGHT, UP = CP.FWD, CP.RIGHT, CP.UP
HOME = arm.location.copy()          # 캐릭터 기준점(루트 이동 전)
ORG = Vector((HOME.x, HOME.y, FLOOR0))


def ground_z():
    """지금 프레임의 최저 발 본 z (블렌더 월드)."""
    return min(((A2W @ b.matrix).translation.z) for b in FOOT_BONES)


def to_game(p, gz):
    """블렌더 월드 점 -> 게임 좌표 (우, 앞, 높이). 캐릭터 발밑이 원점."""
    d = p - ORG
    return Vector((d.dot(RIGHT) * S, d.dot(FWD) * S,
                   (p.z - gz) * S + SOLE))


def seg_seg_dist(p1, q1, p2, q2):
    """선분-선분 최단거리 (enemy.js 와 같은 식)."""
    d1, d2 = q1 - p1, q2 - p2
    r = p1 - p2
    a, e, f = d1.dot(d1), d2.dot(d2), d2.dot(r)
    if a < 1e-12 and e < 1e-12:
        return (p1 - p2).length
    if a < 1e-12:
        s, t = 0.0, max(0.0, min(1.0, f / e))
    else:
        c = d1.dot(r)
        if e < 1e-12:
            t, s = 0.0, max(0.0, min(1.0, -c / a))
        else:
            b = d1.dot(d2)
            den = a * e - b * b
            s = max(0.0, min(1.0, (b * f - c * e) / den)) if den > 1e-12 else 0.0
            t = (b * s + f) / e
            if t < 0:
                t, s = 0.0, max(0.0, min(1.0, -c / a))
            elif t > 1:
                t, s = 1.0, max(0.0, min(1.0, (b - c) / a))
    return ((p1 + d1 * s) - (p2 + d2 * t)).length


def capsule_at(d, lat=0.0):
    """캐릭터 앞 d 미터(옆으로 lat)에 선 고블린의 몸통 축 선분 (게임 좌표)."""
    c = Vector((lat, d, 0.0))
    return (c + Vector((0, 0, GOB_H * CAP_LO)), c + Vector((0, 0, GOB_H * CAP_HI)))


DISTS = (0.8, 1.0, 1.2, 1.4)
FPS = 30.0
HOT_DV = 0.527      # 이만큼(게임m/프레임) 이상 움직여야 '베는 중'(swordFast>=0.42)


def scan(name, act, dists=DISTS):
    """프레임별 칼끝 높이 + 캡슐 접촉 판정. 전부 **게임 단위**."""
    arm.animation_data.action = act
    f0 = int(min(kp.co[0] for lay in act.layers for st in lay.strips
                 for cb in st.channelbags for fc in cb.fcurves
                 for kp in fc.keyframe_points))
    f1 = int(max(kp.co[0] for lay in act.layers for st in lay.strips
                 for cb in st.channelbags for fc in cb.fcurves
                 for kp in fc.keyframe_points))
    rows = []
    prev = None
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        a, b = blade_world()
        gz = ground_z()
        ga, gb = to_game(a, gz), to_game(b, gz)
        dv = (gb - prev).length if prev is not None else 0.0
        prev = gb.copy()
        row = dict(f=f, ay=ga.z, by=gb.z, ar=ga.x, af=ga.y,
                   br=gb.x, bf=gb.y, dv=dv, d={})
        for dd in dists:
            p2, q2 = capsule_at(dd)
            row["d"]["%.1f" % dd] = seg_seg_dist(ga, gb, p2, q2)
        rows.append(row)
    return dict(name=name, f0=f0, f1=f1, rows=rows)


def report(res, dists=DISTS):
    rows = res["rows"]
    ys = [r["by"] for r in rows]
    print("\n=== %s (f%d~%d) ===  [게임 단위, 키 1.75]" % (res["name"], res["f0"], res["f1"]))
    print("칼끝 높이  최저 %.3f  최고 %.3f  (프레임 %d)"
          % (min(ys), max(ys), len(rows)))
    print("  f |  칼끝y  코등이y |  칼끝(우,앞)   | 속도 | "
          + " ".join("d%.1f " % d for d in dists))
    for r in rows:
        marks = []
        for d in dists:
            v = r["d"]["%.1f" % d]
            m = "*" if v <= CAP_R else ("+" if v <= CAP_R + BLADE_PAD else " ")
            marks.append("%5.2f%s" % (v, m))
        print("  %2d | %6.3f  %6.3f  | %+6.3f %+6.3f | %4.2f%s| %s"
              % (r["f"], r["by"], r["ay"], r["br"], r["bf"], r["dv"],
                 "!" if r["dv"] >= HOT_DV else " ", " ".join(marks)))
    print("  (* = 반경 0.40 안 / + = 0.54(칼날굵기 포함) 안 / ! = 판정이 켜지는 속도)")
    for d in dists:
        hits40 = [r for r in rows if r["d"]["%.1f" % d] <= CAP_R]
        hits54 = [r for r in rows if r["d"]["%.1f" % d] <= CAP_R + BLADE_PAD]
        hot = [r for r in hits54 if r["dv"] >= HOT_DV]
        mn = min(r["d"]["%.1f" % d] for r in rows)
        print("  거리 %.1f: 반경0.40 %2d프레임 / 0.54 %2d프레임 (그중 빠른 구간 %2d) "
              "| 최소여유 %.3f" % (d, len(hits40), len(hits54), len(hot), mn))
    return res


def stroke_dir(res, fa, fb, label):
    """fa->fb 구간 칼끝 이동의 성분. 기술 성격이 유지되는지 본다."""
    rows = {r["f"]: r for r in res["rows"]}
    if fa not in rows or fb not in rows:
        return
    A, B = rows[fa], rows[fb]
    dr, du, df = B["br"] - A["br"], B["by"] - A["by"], B["bf"] - A["bf"]
    L = math.sqrt(dr * dr + du * du + df * df) or 1e-9
    print("  [%s] f%d->f%d  칼끝 이동 우%+.3f 상%+.3f 앞%+.3f | 길이%.3f "
          "| 수직 %.0f%% 좌우 %.0f%%"
          % (label, fa, fb, dr, du, df, L,
             100 * abs(du) / L, 100 * abs(dr) / L))


ATTACK = [(f, p["b"]) for f, p in CP.SEQ]
HEAVY = [(f, p) for f, p in CP.HEAVY_SEQ]
WIDE = [(f, p) for f, p in CP.WIDE_SEQ]

out = {}
a = make_action("Attack", ATTACK, accel=CP.WINDUP_F, decel=CP.STRIKE_F,
                linear=CP.ATTACK_LINEAR)
rA = report(scan("Attack", a))
for i, (t0, t1) in enumerate(CP.TRAILS):
    stroke_dir(rA, t0, t1, "%d타" % (i + 1))
out["Attack"] = rA

a = make_action("Heavy", HEAVY, accel=CP.HEAVY_WINDUP_F,
                decel=CP.HEAVY_STRIKE_F, root=True, linear=CP.HEAVY_LINEAR)
rH = report(scan("Heavy", a))
stroke_dir(rH, 26, 28, "수면참 타격")
stroke_dir(rH, 26, 34, "수면참 전체")
out["Heavy"] = rH

a = make_action("Wide", WIDE, accel=CP.WIDE_WINDUP_F,
                decel=CP.WIDE_STRIKE_F, root=True, linear=CP.WIDE_LINEAR)
rW = report(scan("Wide", a))
stroke_dir(rW, 18, 21, "횡일섬 타격")
stroke_dir(rW, 18, 27, "횡일섬 전체")
out["Wide"] = rW

# 파지 이탈(양손이 자루에 붙어 있는가) — 칼날 축에서 왼 주먹까지 수직거리
print("\n=== 파지 검사 (왼 주먹이 자루 축에서 얼마나 벗어나는가) ===")
FIST = ps.fist_r.get("l", 0.166)
for nm, seq, accel, decel, rt in (
        ("Attack", ATTACK, CP.WINDUP_F, CP.STRIKE_F, False),
        ("Heavy", HEAVY, CP.HEAVY_WINDUP_F, CP.HEAVY_STRIKE_F, True),
        ("Wide", WIDE, CP.WIDE_WINDUP_F, CP.WIDE_STRIKE_F, True)):
    act = make_action(nm, seq, accel=accel, decel=decel, root=rt)   # noqa: 검사용
    arm.animation_data.action = act
    # 한손 구간은 건너뛴다
    src = {"Attack": CP.SEQ, "Heavy": CP.HEAVY_SEQ, "Wide": CP.WIDE_SEQ}[nm]
    oneh = set()
    ks = sorted((f, p) for f, p in src)
    for i in range(len(ks) - 1):
        if ks[i][1].get("1h") or ks[i + 1][1].get("1h"):
            oneh.update(range(ks[i][0], ks[i + 1][0] + 1))
    f0, f1 = ks[0][0], ks[-1][0]
    worst, wf, n = 0.0, 0, 0
    for f in range(f0, f1 + 1):
        if f in oneh:
            continue
        sc.frame_set(f)
        bpy.context.view_layer.update()
        # ★자루 축 = 오른 주먹 중심을 지나는 blade_dir. 칼날 A~B 선분을 쓰면
        # 안 된다. 칼이 초승달로 휘어서(백아 curve 54도) 그 직선은 자루 축과
        # 나란하지 않고, 포즈와 무관한 0.245 짜리 상수 오차가 붙는다.
        ax = ps.blade_dir()
        rp = ps.palm_world("r")
        lp = ps.palm_world("l")
        if ax is None or rp is None or lp is None:
            continue
        t = (lp - rp).dot(ax)
        perp = ((lp - rp) - ax * t).length
        n += 1
        if perp > worst:
            worst, wf = perp, f
    print("  %-6s 최대 이탈 %.4f (주먹 %.2f 개) @f%d  / 검사 %d프레임 (한손 %d 제외)"
          % (nm, worst, worst / FIST, wf, n, len(oneh)))

# ---- 키포즈별 손목: 제한을 걸었을 때 vs 안 걸었을 때 ----
# ★제한이 실제로 무는 포즈를 찾는다. 무는 포즈는 **작가가 적은 칼날 방향이
#   그대로 안 나온** 포즈다(= 기술 성격이 조용히 바뀐 자리).
print("\n=== 키포즈별 오른손목 (제한 78 / 제한 없음) ===")
_save = CP.Poser.WRIST_MAX
for nm, src in (("Attack", CP.SEQ), ("Heavy", CP.HEAVY_SEQ), ("Wide", CP.WIDE_SEQ)):
    line = []
    for f, pose in src:
        CP.Poser.WRIST_MAX = 78.0
        ps.apply(pose)
        bpy.context.view_layer.update()
        w1 = ps.wrist_bend("r")
        CP.Poser.WRIST_MAX = None
        ps.apply(pose)
        bpy.context.view_layer.update()
        w0 = ps.wrist_bend("r")
        line.append("f%-2d %4.0f/%4.0f%s" % (f, w1, w0, "*" if w0 - w1 > 2 else " "))
    print("  %-6s %s" % (nm, " ".join(line)))
print("  (* = 제한이 물어서 칼날 방향이 바뀐 포즈)")
CP.Poser.WRIST_MAX = _save

# 손목 꺾임
print("\n=== 손목 꺾임 (WRIST_MAX %s) ===" % CP.Poser.WRIST_MAX)
for nm, seq, accel, decel, rt in (
        ("Attack", ATTACK, CP.WINDUP_F, CP.STRIKE_F, False),
        ("Heavy", HEAVY, CP.HEAVY_WINDUP_F, CP.HEAVY_STRIKE_F, True),
        ("Wide", WIDE, CP.WIDE_WINDUP_F, CP.WIDE_STRIKE_F, True)):
    act = make_action(nm, seq, accel=accel, decel=decel, root=rt)   # noqa: 검사용
    arm.animation_data.action = act
    ks = sorted((f, p) for f, p in {"Attack": CP.SEQ, "Heavy": CP.HEAVY_SEQ,
                                    "Wide": CP.WIDE_SEQ}[nm])
    worst, wf = 0.0, 0
    for f in range(ks[0][0], ks[-1][0] + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        w = ps.wrist_bend("r")
        if w > worst:
            worst, wf = w, f
    print("  %-6s 오른손목 최대 %.1f도 @f%d" % (nm, worst, wf))

# IK 클램프(팔이 안 닿아 굳은 곳)
print("\n=== IK 못 닿음 기록 (1.0 이면 팔이 완전히 뻗어 굳음) ===")
seen = {}
for lbl, ratio in ps.reach_log:
    if ratio >= 0.999:
        seen[lbl] = seen.get(lbl, 0) + 1
print("  ", seen if seen else "없음")

if OUT_JSON:
    with open(OUT_JSON, "w") as fp:
        json.dump(out, fp)
    print("saved", OUT_JSON)
