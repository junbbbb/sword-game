# -*- coding: utf-8 -*-
# 게임용 glTF 내보내기: 캐릭터 + 칼(본에 웨이트로 병합) + 액션 4종(Idle/Walk/Run/Attack)
# 실행: blender --background --python s6_export_game.py
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
WEB = os.path.join(ROOT, "web")
os.makedirs(WEB, exist_ok=True)
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
import asset_anim as AA
importlib.reload(CP)
importlib.reload(AA)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("Floor", "Plane")))
zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
CHAR_H = max(zs) - min(zs)          # 칼 병합 전에 재야 정확하다
FLOOR0 = min(zs)
print("body:", body.name, "H=%.3f" % CHAR_H)

# ---------- 칼/머리카락을 본에 웨이트 주고 캐릭터에 병합 ----------
# 중요: 스키닝은 "레스트 포즈" 기준이다. 포즈 상태에서 월드 좌표를 구우면
# 칼이 손에서 어긋난 자리에 붙는다. 먼저 레스트로 되돌린다.
for _b in arm.pose.bones:
    _b.rotation_mode = "QUATERNION"
    _b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
HAND_BONE = next(b.name for b in arm.pose.bones if "r hand" in b.name.lower())
HEAD_BONE = next(b.name for b in arm.pose.bones if b.name.lower().endswith("head"))

def bind_and_merge(objs, bone_name):
    merged = []
    for ob in objs:
        if ob.type != "MESH":
            continue
        # 제약 제거하고 월드 트랜스폼을 메시에 굽는다
        mw = ob.matrix_world.copy()
        ob.constraints.clear()
        ob.parent = None
        ob.matrix_world = mw
        bpy.context.view_layer.update()
        ob.data.transform(mw)
        ob.matrix_world = Matrix()
        # join 하면 소스 오브젝트의 모디파이어가 사라진다(칼날 Solidify 소실 -> 날이 안 보임).
        # 미리 적용해서 지오메트리에 구운다.
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        for md in list(ob.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=md.name)
            except Exception as e:
                print("modifier_apply fail", ob.name, md.name, e)
        vg = ob.vertex_groups.new(name=bone_name)
        vg.add(range(len(ob.data.vertices)), 1.0, "REPLACE")
        m = ob.modifiers.new("Armature", "ARMATURE")
        m.object = arm
        merged.append(ob)
    return merged


# ---------- 칼: 7종을 전부 넣고 게임에서 바꿔 낀다 ----------
# 한 자루만 구워 넣으면 교체할 때마다 glb 를 다시 받아야 한다. 자루당 수백 삼각형뿐이라
# 전부 넣고 런타임에 visible 만 토글하는 게 훨씬 낫다.
# 머리카락만 몸에 병합하고, 칼은 **자루당 별도 스킨드 메시**(SW_<key>)로 남긴다.
import swords as SW
importlib.reload(SW)

old_sword = [o for o in sc.objects if o.type == "MESH" and
             o.name.startswith(("bladeK_", "tsubaK_", "gripK_", "ringK", "pomK"))]
kat_root = bpy.data.objects.get("katana_slayer")
GRIP_M = kat_root.matrix_world.copy() if kat_root else Matrix()   # 손에 맞춰둔 그립 자세
for o in old_sword:
    bpy.data.objects.remove(o, do_unlink=True)
if kat_root:
    bpy.data.objects.remove(kat_root, do_unlink=True)
bpy.context.view_layer.update()

hair_parts = [o for o in sc.objects if o.type == "MESH" and
              (o.name.startswith(("hair_cap", "hl")) and o is not body)]
merged = bind_and_merge(hair_parts, HEAD_BONE)

# 자루마다 크기가 다르지만(정체성) 손에 붙는 기준은 같다.
SW_SCALE = CHAR_H * 0.235
sword_objs = {}
for v in SW.VARIANTS:
    r = SW.build_sword(v, scale=SW_SCALE)
    r.matrix_world = GRIP_M @ r.matrix_world
    bpy.context.view_layer.update()
    parts = [c for c in r.children if c.type == "MESH"]
    bound = bind_and_merge(parts, HAND_BONE)
    if not bound:
        continue
    bpy.ops.object.select_all(action="DESELECT")
    for o in bound:
        o.select_set(True)
    bpy.context.view_layer.objects.active = bound[0]
    if len(bound) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = "SW_" + v["key"]
    ob.data.name = "SW_" + v["key"]
    sword_objs[v["key"]] = ob
    bpy.data.objects.remove(r, do_unlink=True)
print("swords:", list(sword_objs))

arm.data.pose_position = "POSE"
bpy.context.view_layer.update()

bpy.ops.object.select_all(action="DESELECT")
for ob in merged:
    ob.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = body
if merged:
    bpy.ops.object.join()
print("joined -> verts", len(body.data.vertices))

# ---------- 포즈 유틸 (정의는 combo_poses.py 가 정본) ----------
X, Y, Z = CP.X, CP.Y, CP.Z
ps = CP.Poser(arm, CHAR_H)
GUARD = CP.GUARD["b"]


def apply(spec):
    # 리스트면 상체 포즈만, dict 면 루트 이동(스텝/주저앉기)까지 포함
    ps.apply(spec if isinstance(spec, dict) else {"b": spec})


def key_pose(f, root=False):
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("location", frame=f)
    if root:
        arm.keyframe_insert("location", frame=f)


def guard_plus(extra):
    return GUARD + extra


# ---------- 액션 생성 ----------
def make_action(name, frames, accel=(), decel=(), root=False, linear=()):
    """accel = 이 키 이후 구간을 가속(윈드업->타격), decel = 급감속(타격->여파).
    전부 EASE_IN_OUT 이면 칼이 물속에서 움직이듯 밋밋해진다.
    linear = 매 프레임 키를 박아 둔 구간(combo_poses.stroke). 여기는 포즈 자체가
    이미 속도 곡선이라 이징을 또 걸면 이중으로 먹고 키 사이에 오버슛이 생긴다."""
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
        apply(spec)
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
    # ★키 사이에서 왼 주먹이 자루를 놓치는 걸 막는다(combo_poses 주석 참고).
    nre = CP.relock_grip(ps, frames)
    print("action", name, "frames", frames[-1][0], "| 파지 재고정 %d 프레임" % nre)
    return act


# ---------- 모캡 하체 + 검도 팔 ----------
import mocap_asf as MA
importlib.reload(MA)

# 하체·척추·머리만 모캡에서. 팔은 검도 기준으로 덮으므로 제외한다.
# 목·머리는 제외(모캡이 51도나 흔든다). 검도 팔 쪽에서 따로 준다.
MC_ARMS = set(["l clavicle", "l upperarm", "l forearm", "l hand",
               "r clavicle", "r upperarm", "r forearm", "r hand"])
MC_LOWER = set(["pelvis", "spine",
                "l thigh", "l calf", "l foot", "l toe0",
                "r thigh", "r calf", "r foot", "r toe0"])


def make_mocap_action(name, clip, mf0, mf1, step, keys=None, lean_fix=0,
                      root_lift=True, full_arms=False):
    """모캡 구간을 우리 클립으로 굽는다.
    keys = [(출력프레임, 검도자세이름, 파지간격), ...] 사이는 선형 보간."""
    sk = MA.Skel(os.path.join(ROOT, "mocap", "02.asf"))
    frames = MA.read_amc(os.path.join(ROOT, "mocap", clip + ".amc"), limit=mf1 + 2)
    if arm.animation_data:
        arm.animation_data_clear()
    arm.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    try:
        act.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    out_n = 0
    for i, mf in enumerate(range(mf0, mf1, step)):
        of = i + 1
        ps.reset()
        arm.location = ps.home
        MA.apply_frame(ps, sk, frames[mf], parts=MC_LOWER)
        if lean_fix:
            # 모캡 피험자가 등을 많이 굽힌다. 우리 톤에 맞게 편다.
            ps.apply({"b": [("spine", X, -lean_fix)]}, reset=False)
        if full_arms:
            # ★모캡 팔을 그대로 쓴다. 칼날 방향은 **양 손목을 잇는 선**에서 뽑는다
            # (모캡에 칼은 없지만 두 손목은 있다. 양손 파지면 그 선이 자루 축이다).
            MA.apply_frame(ps, sk, frames[mf], parts=MC_ARMS)
            bd = MA.blade_dir(sk, frames[mf])
            ops = [("neck", CP.AIM, (0.0, 1.0, 0.22)),
                   ("head", CP.AIM, (0.0, 1.0, -0.04)),
                   ("head", CP.FACE, (0.0, 0.0, 1.0))]
            if bd is not None:
                ops.append(("r hand", CP.BLADE,
                            (bd.dot(CP.RIGHT), bd.dot(CP.UP), bd.dot(CP.FWD), 55.0)))
            ops.append(("l", CP.GRIP, CP.GB))    # 왼손을 우리 자루에 스냅
            ps.apply({"b": ops}, reset=False)
        else:
            # 검도 팔: keys 사이를 보간
            a, b, t, gb = keys[0][1], keys[0][1], 0.0, keys[0][2]
            for k in range(len(keys) - 1):
                f0k, n0k, g0k = keys[k]
                f1k, n1k, g1k = keys[k + 1]
                if f0k <= of <= f1k:
                    t = (of - f0k) / float(max(1, f1k - f0k))
                    a, b = n0k, n1k
                    gb = g0k + (g1k - g0k) * t
                    break
            else:
                a = b = keys[-1][1]
                gb = keys[-1][2]
                t = 0.0
            ps.apply({"b": CP.kendo_arms(a, b, t, gb)}, reset=False)
        bpy.context.view_layer.update()
        if root_lift:
            # 모캡은 루트 높이를 안 준다. 가장 낮은 정점을 바닥에 맞춘다.
            dg = bpy.context.evaluated_depsgraph_get()
            ev = body.evaluated_get(dg)
            me = ev.to_mesh()
            lo = min((ev.matrix_world @ v.co).z for v in me.vertices)
            ev.to_mesh_clear()
            arm.location = ps.home + Vector((0, 0, FLOOR0 - lo))
        key_pose(of, root=True)
        out_n = of
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"
    except Exception:
        pass
    print("action %s <- 모캡 %s f%d~%d -> 1~%d" % (name, clip, mf0, mf1, out_n))
    return act


def run_swing(ps):
    """오른 다리가 앞뒤 어디쯤인가. -1(뒤) ~ +1(앞). 팔 흔들기를 여기에 맞춘다."""
    d = ps.bone_dir("r thigh")
    return 0.0 if d is None else max(-1.0, min(1.0, d.dot(CP.FWD) / 0.55))


def make_asset_action(name, anim, arm_pose=None, step=1, hold_arms=True, parts=None):
    """원본 에셋 애니메이션에서 **하체·척추**를 가져오고 팔은 우리 중단세로 덮는다.
    손으로 만든 4 포즈 다리 사이클로는 발목·발가락·골반 상하가 없어서
    달리는 게 이상했다(오너 지적). 자세한 이유는 asset_anim.py 주석 참고."""
    src, f0, f1, tmp = AA.load(anim)
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
    arms = arm_pose if arm_pose is not None else CP.GUARD_ARMS
    out = 0
    src_frames = list(range(f0, f1 + 1, step))
    for i, sf in enumerate(src_frames):
        sc.frame_set(sf)                     # 소스 리그를 그 프레임으로
        ps.reset()
        arm.location = ps.home               # 루트 이동 없음(제자리 루프)
        AA.copy_pose(src, arm, parts or AA.LOWER_NOHEAD)   # 하체·척추
        if hold_arms:
            a = arms(run_swing(ps)) if callable(arms) else arms
            ps.apply({"b": a}, reset=False)
        out = i + 1
        key_pose(out)
    AA.drop(tmp)
    # 여기는 relock_grip 이 필요 없다. 매 프레임을 직접 풀어서 키를 박았으므로
    # 이미 프레임마다 정확한 파지다(relock 은 '키 사이'를 메우는 도구다).
    nre = 0
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"
    except Exception:
        pass
    print("action %s <- %s  소스 f%d~%d -> 출력 1~%d | 파지 재고정 %d"
          % (name, anim, f0, f1, out, nre))
    return act


# Idle: 호흡 루프 (1-40, 마지막이 첫 프레임과 동일해야 루프가 매끄러움)
IDLE = [
    (1, GUARD),
    (14, guard_plus([("spine", X, 3)])),
    (26, guard_plus([("spine", X, -2)])),
    (40, GUARD),
]

# Walk: 좌우 대칭 4포즈 사이클 (다리는 world X 로 앞뒤 스윙, 무릎은 뒤로 굽힘)
# 팔 스윙도 X 축이다. Y 축은 팔을 위아래로 벌리는 축이라 걸을 때 팔이
# 앞뒤가 아니라 옆으로 들렸다(측정: r upperarm Y+ -> 팔꿈치가 위로).
#
# ★2026-08-05: **Walk 는 더 이상 이 함수를 쓰지 않는다.**
#   발 궤적 기반 IK(make_walk_action, 아래)로 전면 교체했다. 이 함수와 WALK
#   리스트는 아래 RUN(비교용, 역시 미사용) 이 참조하므로 시그니처만 남긴다.
#   왜 버렸는지는 make_walk_action 주석에 적어 뒀다.
def walk_pose(phase, amp=26, knee=34, lean=0):
    """phase 0=왼발 앞, 1=중간, 2=오른발 앞, 3=중간. X- 가 앞.
    팔은 흔들지 않는다. 양손으로 자루를 잡고 있으므로 팔을 따로 돌리면
    왼손이 자루에서 떨어져 나간다. 걸을 땐 중단세를 유지하고 다리만 움직인다."""
    if phase == 0:
        legs = [("l thigh", X, -amp), ("r thigh", X, amp),
                ("l calf", X, 8), ("r calf", X, knee)]
        sp = [("spine", Z, -4 + 4), ("spine", X, 6 + lean)]
    elif phase == 2:
        legs = [("l thigh", X, amp), ("r thigh", X, -amp),
                ("l calf", X, knee), ("r calf", X, 8)]
        sp = [("spine", Z, -4 - 4), ("spine", X, 6 + lean)]
    else:
        legs = [("l thigh", X, 0), ("r thigh", X, 0),
                ("l calf", X, 20), ("r calf", X, 20)]
        sp = []
    # spine 은 팔 IK 보다 먼저 와야 한다(나중에 오면 어깨가 돌면서 손 위치가 어긋남).
    base = [t for t in GUARD if not (t[0].endswith("thigh") and t[1] == X)]
    if sp:
        base = [t for t in base if t[0] != "spine"]
    return sp + base + legs


WALK = [(1, walk_pose(0)), (9, walk_pose(1)), (17, walk_pose(2)),
        (25, walk_pose(3)), (33, walk_pose(0))]
RUN = [(1, walk_pose(0, 42, 55, 8)), (6, walk_pose(1, 42, 55, 8)),
       (11, walk_pose(2, 42, 55, 8)), (16, walk_pose(3, 42, 55, 8)),
       (21, walk_pose(0, 42, 55, 8))]


# ==================== 걷기: 발 궤적 -> 2본 IK (2026-08-05 재작성) ====================
# 왜 다시 만들었나 (probe_walk.py 로 실측한 고장 증상)
#   1) walk_pose 의 phase 1 과 3 이 같은 else 가지로 떨어져 **중간 자세 두 개가
#      완전히 동일**했다. 클립이 회문이라 f18~f33 이 f16~f1 을 되짚는다.
#   2) 더 근본적으로 허벅지·종아리 **각도**만 주고 발의 세계 위치를 안 봤다.
#      그래서 디딘 발이 뒤로 밀리지 않고 호를 그리며 들렸다 놨다 했다.
#      실측: 접지 구간 발 속도가 왼발 +2.77 / 오른발 -2.65 로 **부호가 반대**
#      (= 두 발이 대칭으로 앞뒤 왕복만 하고 접지 구간이 아예 없다는 뜻).
#
# 어떻게 바꿨나: 각도를 손으로 찍지 않는다. 발이 있어야 할 자리를 먼저 정하고
# 코사인 법칙 2본 IK 로 허벅지·종아리 각도를 역산한다.
#   · 접지 60% : 발목을 레스트 높이(= 발바닥이 바닥)에 고정하고 **일정한 속도로**
#                뒤로 민다. 이게 미끄러짐을 없애는 핵심이다.
#   · 스윙 40% : 3차 에르미트로 앞으로 보낸다. 양 끝 기울기를 접지 속도와 같게
#                맞춰서(C1 연속) 착지·이지 순간에 발이 톡 튀지 않는다.
#                덤으로 이지 직후 조금 더 뒤로, 착지 직전 조금 되당기는
#                실제 보행의 꼬리 모양이 저절로 나온다.
#   · 골반 높이: **컴퍼스 보행**. 디딘 다리 길이가 일정하도록
#                h = sqrt(Lc^2 - (발 앞뒤거리)^2). 한발 지지 때 높고 양발 지지
#                때 낮아 사이클당 2번 오르내린다(진폭 ±1.4% 키).
#                코사인 곡선으로 대충 흔들면 양발 지지 순간에 다리가 안 닿아
#                IK 가 클램프되고 그 자리에서 발이 미끄러진다. 그래서 기하로 푼다.
#   · 골반 좌우: 디딘 다리 쪽으로 실린다(1 사이클 1회). 양발 지지 순간엔 0 이라
#                뻗음 한계 계산을 건드리지 않는다.
#   · 골반 비틀림: 스윙하는 쪽 골반이 앞으로. 척추로 같은 양을 되돌려 어깨는
#                정면을 유지한다(실제 보행의 골반-흉곽 반대 회전).
#   · ★팔은 안 흔든다. 양손으로 자루를 잡고 있어 팔을 따로 돌리면 왼손이
#     자루에서 떨어진다. 걸을 땐 중단세를 유지하고 다리만 움직인다(원래 설계).
#
# 축 확인(probe_legaxis.py 실측): 발끝이 발목보다 **-Y** 쪽에 있다.
#   즉 FWD = (0,-1,0) 이 맞다. walk_pose 독스트링의 "X- 가 앞"은 **회전축** 이야기
#   (월드 X 축으로 음의 각도를 주면 다리가 앞으로 나간다)이지 전방축이 아니다.
#   왼다리가 +X, 오른다리가 -X 이고 RIGHT = (-1,0,0) 이다.
WALK_N = 28            # 사이클 프레임 수. 30fps 기준 0.93초 = 분당 128보
WALK_STANCE = 0.60     # 접지 비율. 실제 보행이 60%(양발 지지가 앞뒤 10%씩)
WALK_A = 0.152         # 발 앞뒤 진폭(키 배). 보폭 = 2A = 키의 30%
WALK_LIFT = 0.50       # 스윙 최고 높이(발목 높이 배)
WALK_REACH = 0.99      # 접지 다리 길이(최대 뻗음 배). 1.0 이면 무릎이 잠긴다
WALK_SWAY = 0.011      # 골반 좌우(키 배)
WALK_YAW = 3.5         # 골반 비틀림(도)
WALK_LEAN = 3.0        # 걷기 상체 앞기울기(도). GUARD 의 spine X 2 에 더한다
WALK_TOEOUT = 6.0      # 발끝 벌림(도). 사람은 6~8도 벌리고 걷는다
WALK_PLANTAR = 10.0    # 이지 직후 발끝 아래로(도)
WALK_DORSI = 7.0       # 스윙 중반 발끝 위로(도). 발끝이 바닥을 긁지 않게

# 다리 치수는 **레스트에서** 잰다(포즈가 섞이면 뼈 길이가 아니라 그 포즈 값이 나온다).
ps.reset()
LEG = {}
for _s in ("l", "r"):
    _hip, _knee = ps.wpos("%s thigh" % _s), ps.wpos("%s calf" % _s)
    _ank, _toe = ps.wpos("%s foot" % _s), ps.wpos("%s toe" % _s)
    LEG[_s] = dict(hip=_hip, ank=_ank,
                   L1=(_knee - _hip).length, L2=(_ank - _knee).length,
                   fdir=(_toe - _ank).normalized())
LEG_R = min(LEG[s]["L1"] + LEG[s]["L2"] for s in ("l", "r"))
ANK_Z = LEG["l"]["ank"].z                 # 접지 중 발목 높이 = 레스트 그대로
print("다리: 허벅지 %.4f 종아리 %.4f 합 %.4f / 발목높이 %.4f(바닥 위 %.4f)"
      % (LEG["l"]["L1"], LEG["l"]["L2"], LEG_R, ANK_Z, ANK_Z - FLOOR0))


def foot_at(p, A, lift):
    """사이클 위상 p(0~1)에서 그 발의 (앞뒤 오프셋, 들린 높이, 발등 각도).
    앞뒤 오프셋은 + 가 앞(FWD). 각도는 + 가 발끝을 아래로(저측굴곡)."""
    p = p % 1.0
    st = WALK_STANCE
    if p < st:
        # 접지: 일정한 속도로 뒤로. 직선이어야 미끄러지지 않는다.
        return A - 2.0 * A * (p / st), 0.0, 0.0
    u = (p - st) / (1.0 - st)
    # 3차 에르미트. 양 끝 기울기 m 을 접지 속도와 같게 이어 붙인다.
    m = -2.0 * A * (1.0 - st) / st
    fo = ((2 * u ** 3 - 3 * u ** 2 + 1) * (-A) + (u ** 3 - 2 * u ** 2 + u) * m
          + (-2 * u ** 3 + 3 * u ** 2) * A + (u ** 3 - u ** 2) * m)
    z = lift * math.sin(math.pi * u)
    pitch = (WALK_PLANTAR if u < 0.5 else WALK_DORSI) * math.sin(2 * math.pi * u)
    return fo, z, pitch


def hip_h(p, A, Lc, lift):
    """골반 높이(발목 높이 기준). 컴퍼스 보행: 다리 길이가 Lc 를 넘지 않는
    최대 높이를 **양쪽 다리 모두**에 대해 구하고 낮은 쪽을 쓴다.
    ★디딘 다리만 보면 안 된다. 이지 직후(스윙 초반)에는 발이 아직 뒤로 한참
    나가 있는데 거의 안 들려서, 그때 다리가 제일 많이 필요하다. 접지만 보고
    골반을 올렸더니 그 프레임에서 IK 가 클램프됐다(뻗음 비율 1.001)."""
    hs = []
    for q in (p % 1.0, (p + 0.5) % 1.0):
        fo, lz, _ = foot_at(q, A, lift)
        fo = min(abs(fo), Lc * 0.999)
        hs.append(lz + math.sqrt(max(1e-6, Lc * Lc - fo * fo)))
    return min(hs)


def hip_h_s(p, A, Lc, lift):
    """양발 지지 구간에서 높이가 살짝 솟았다 꺼지는 요철을 없앤다.
    앞뒤 ±2 프레임 중 **가장 낮은** 값을 쓰므로 뻗음 한계를 절대 안 넘는다."""
    return min(hip_h(p + k / float(WALK_N), A, Lc, lift) for k in (-2, -1, 0, 1, 2))


def move_pelvis(dw):
    """골반을 월드 기준 dw 만큼 평행이동.
    ★pb.matrix 에 행렬을 통째로 대입하면 아마추어 스케일(0.0254)이 날아간다
    (과거 손이 39배로 부푼 사고). **평행이동 행렬만 앞에 곱해서** 회전·스케일은
    손도 대지 않는다. dw 는 월드 단위라 아마추어 공간으로 바꿔 넣는다."""
    b = ps.pb("pelvis")
    if b is None:
        return
    d = ps.W2A.to_3x3() @ Vector(dw)
    b.matrix = Matrix.Translation(d) @ b.matrix
    ps._update()


def leg_ik(side, target, pole_w):
    """엉덩이-무릎-발목 2본 IK(코사인 법칙). 무릎은 pole 방향으로 민다.
    반환 = 목표까지 거리 / 다리 최대 길이 (1.0 을 넘으면 못 닿아 클램프된 것)."""
    th, ca = ps.pb("%s thigh" % side), ps.pb("%s calf" % side)
    if not (th and ca):
        return 0.0
    A = (ps.A2W @ th.matrix).translation.copy()
    B = (ps.A2W @ ca.matrix).translation.copy()
    C = (ps.A2W @ ps.pb("%s foot" % side).matrix).translation.copy()
    L1, L2 = (B - A).length, (C - B).length
    v = Vector(target) - A
    d = v.length
    if d < 1e-6:
        return 0.0
    n = v / d
    reach = L1 + L2
    ratio = d / reach
    d = min(d, reach * 0.999)      # 완전히 펴면 무릎 방향이 정의되지 않는다
    cs = max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))
    ang = math.acos(cs)
    pole = Vector(pole_w)
    perp = pole - n * pole.dot(n)
    if perp.length < 1e-5:
        perp = n.cross(CP.UP)
    perp.normalize()
    knee = A + n * (L1 * math.cos(ang)) + perp * (L1 * math.sin(ang))
    ps.aim("%s thigh" % side, knee - A)
    B2 = (ps.A2W @ ca.matrix).translation
    ps.aim("%s calf" % side, (A + n * d) - B2)
    return ratio


def make_walk_action(name="Walk"):
    """발 궤적을 정하고 프레임마다 IK 로 푸는 걷기. 4포즈 보간이 아니라
    **매 프레임 계산**이라 중간 프레임에서 발이 흐르지 않는다."""
    A = WALK_A * CHAR_H
    Lc = WALK_REACH * LEG_R
    lift = WALK_LIFT * (ANK_Z - FLOOR0)
    upper = [t for t in GUARD if "thigh" not in t[0] and t[0] != "spine"]
    if arm.animation_data:
        arm.animation_data_clear()
    arm.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True                 # ★안 켜면 export 에서 조용히 빠진다
    arm.animation_data.action = act
    try:                                     # ★4.4+ 슬롯. 없으면 액션이 아무 일도 안 한다
        slot = act.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = slot
    except Exception:
        pass
    rows, worst = [], 0.0
    for i in range(WALK_N + 1):              # 마지막 프레임 = 첫 프레임(루프 이음매)
        # ★프레임 0 부터 찍는다. glTF 는 시간을 **frame/fps** 로 적으므로 1부터
        # 시작하면 클립 앞에 1/30 초짜리 죽은 구간이 생기고(three.js 가 첫 키를
        # 그대로 물고 있는다) 루프마다 그 위상에서 한 프레임씩 멈춘다.
        # 걷기는 계속 도는 클립이라 그 한 프레임이 곧 발 미끄러짐이다.
        f = i
        p = (i % WALK_N) / float(WALK_N)
        yaw = WALK_YAW * math.cos(2 * math.pi * (p - 0.3))
        # 순서: 골반 -> 척추 -> 팔 IK -> 파지. 척추가 팔보다 뒤면 어깨가 돌면서
        # 손 위치가 어긋난다(combo_poses.apply 주석).
        ps.apply({"b": [("pelvis", Z, yaw), ("spine", Z, -4 - yaw),
                        ("spine", X, 2 + WALK_LEAN)] + upper})
        # 골반 상하·좌우. 다리 IK 보다 **먼저** 옮겨야 엉덩이 위치가 확정된다.
        h = hip_h_s(p, A, Lc, lift)
        hz = (ps.wpos("l thigh").z + ps.wpos("r thigh").z) * 0.5
        sway = WALK_SWAY * CHAR_H * math.cos(2 * math.pi * (p - 0.3))
        move_pelvis(Vector((sway, 0.0, (ANK_Z + h) - hz)))
        row = [f]
        for side in ("l", "r"):
            pp = p if side == "l" else (p + 0.5) % 1.0
            fo, lz, pitch = foot_at(pp, A, lift)
            tgt = Vector((LEG[side]["ank"].x,          # 좌우 폭은 레스트 그대로
                          LEG[side]["hip"].y - fo,     # FWD = -Y 라 앞이면 y 감소
                          ANK_Z + lz))
            out = -0.18 if side == "l" else 0.18       # 무릎을 앞+바깥으로
            r = leg_ik(side, tgt, CP.FWD + CP.RIGHT * out)
            worst = max(worst, r)
            # 발바닥: 접지 중엔 레스트 방향 그대로 = 바닥과 평행.
            fd = (Matrix.Rotation(math.radians(WALK_TOEOUT if side == "l"
                                               else -WALK_TOEOUT), 4, "Z")
                  @ Matrix.Rotation(math.radians(pitch), 4, "X")
                  @ LEG[side]["fdir"])
            ps.aim("%s foot" % side, fd)
            got = ps.wpos("%s foot" % side)
            row += [fo, lz, (got - tgt).length, r]
        key_pose(f)
        rows.append(row)
    try:                                     # 매 프레임 키라 베지어는 오버슈트만 만든다
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"
    except Exception:
        pass
    print("action %s: %d프레임(사이클 %d) 보폭 %.3f(키의 %.1f%%) 스윙높이 %.3f"
          % (name, WALK_N + 1, WALK_N, 2 * A, 200 * WALK_A, lift))
    print("  최대 뻗음 비율 %.3f (1.0 이면 클램프 = 미끄러짐)" % worst)
    print("  f | 왼발 앞뒤   높이   오차  뻗음 | 오른발 앞뒤   높이   오차  뻗음")
    for r in rows:
        print("  %2d | %+7.4f %6.4f %6.4f %5.3f | %+7.4f %6.4f %6.4f %5.3f"
              % tuple(r))
    return act

# Attack: combo_poses.SEQ 그대로. 루트 이동(스텝)은 웹에서 플레이어가
# 직접 움직이므로 빼고 상체 포즈만 쓴다.
ATTACK = [(f, p["b"]) for f, p in CP.SEQ]
# Heavy(일격기)는 몸을 깊게 낮추는 게 동작의 절반이라 루트 이동을 살린다.
# 다리만 굽히면 엉덩이 높이가 그대로여서 발이 뜨거나 바닥을 뚫는다.
HEAVY = [(f, p) for f, p in CP.HEAVY_SEQ]
# Wide(횡일섬)도 골반 회전 + 스텝이 동작의 일부라 루트 이동을 살린다.
WIDE = [(f, p) for f, p in CP.WIDE_SEQ]
# 점프는 다리 모양만. 수직 이동은 코드가 root 를 띄워서 만든다.
JUMP = [(f, p["b"]) for f, p in CP.JUMP_SEQ]

acts = []
acts.append(make_action("Idle", IDLE))
# Walk 은 4포즈 보간이 아니라 발 궤적 IK 로 매 프레임 굽는다(위 주석 참고).
acts.append(make_walk_action("Walk"))
# Run 만 원본 에셋에서 가져온다. 손으로 만든 다리 4 포즈는 발목·발가락·골반 상하가
# 없어서 뛰는 게 이상했다. RUN(위) 는 비교용으로 남겨둔다.
# ※모캡 전용 스킬 "Kata" 도 되돌렸다.
#   acts.append(make_mocap_action("Kata","02_07",110,350,4,lean_fix=12,full_arms=True))
acts.append(make_asset_action("Run", "infantry_combat_run",
                              arm_pose=CP.run_arms, parts=AA.LOWER_NOHEAD))
acts.append(make_action("Attack", ATTACK, accel=CP.WINDUP_F, decel=CP.STRIKE_F,
                        linear=CP.ATTACK_LINEAR))
# ※모캡 기반 수면참은 되돌렸다(오너 판단). 되살리려면 아래 두 줄을 쓰면 된다.
#   HEAVY_KEYS = [(1,"chudan",CP.GB), (12,"raise",CP.GB), (22,"jodan",CP.GB),
#                 (26,"strike",CP.GB), (32,"settle",CP.GB), (44,"chudan",CP.GB)]
#   acts.append(make_mocap_action("Heavy","02_07",60,240,4,HEAVY_KEYS,lean_fix=12))
acts.append(make_action("Heavy", HEAVY, accel=CP.HEAVY_WINDUP_F,
                        decel=CP.HEAVY_STRIKE_F, root=True,
                        linear=CP.HEAVY_LINEAR))
acts.append(make_action("Wide", WIDE, accel=CP.WIDE_WINDUP_F,
                        decel=CP.WIDE_STRIKE_F, root=True,
                        linear=CP.WIDE_LINEAR))
acts.append(make_action("Jump", JUMP, accel={1}, decel={16}))

# 마지막 액션만 남기면 glTF 가 하나만 뽑으므로, 전체 액션 내보내기 모드 사용
ps.reset()

# ---------- 정리: 이펙트/바닥/카메라/라이트 제거 ----------
for o in list(sc.objects):
    if o.type in ("CAMERA", "LIGHT") or o.name.startswith(("Plane", "Floor", "wave", "wt", "spray", "foam", "crest")):
        bpy.data.objects.remove(o, do_unlink=True)

# ---------- 머티리얼을 glTF 호환(Principled BSDF)으로 변환 ----------
# Blender 의 Diffuse/Emission 노드 구성은 glTF 로 안 나간다. 텍스처/색만 뽑아 Principled 로 재구성.
def to_principled(mat):
    if not mat or not mat.use_nodes:
        return
    img = None
    base = None
    mix_base = None
    emit_base = None
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            img = n.image
        elif n.type == "MIX":
            try:
                c = n.inputs[7].default_value      # cel_mat 의 밝은 쪽 = 실제 베이스 색
                mix_base = (c[0], c[1], c[2], 1.0)
            except Exception:
                pass
        elif n.type in ("EMISSION", "BSDF_DIFFUSE"):
            if not n.inputs[0].is_linked:
                try:
                    c = n.inputs[0].default_value
                    emit_base = (c[0], c[1], c[2], 1.0)
                except Exception:
                    pass
    base = mix_base or emit_base or (0.8, 0.8, 0.8, 1.0)
    nt = mat.node_tree
    nt.nodes.clear()
    out_n = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value = 0.0
    if img is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = base
    nt.links.new(bsdf.outputs[0], out_n.inputs[0])
    mat.blend_method = "OPAQUE"


for m in list(bpy.data.materials):
    to_principled(m)
print("materials converted:", len(bpy.data.materials))

# 남은 빈 오브젝트(카타나 루트 등)와 불필요 액션 제거
for o in list(sc.objects):
    if o.type == "EMPTY":
        bpy.data.objects.remove(o, do_unlink=True)
KEEP = {"Idle", "Walk", "Run", "Attack", "Heavy", "Wide", "Jump"}
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
print("actions kept:", [a.name for a in bpy.data.actions])

OUT = os.path.join(WEB, "slayer.glb")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT,
    export_format="GLB",
    use_selection=False,
    export_apply=True,
    export_animations=True,
    export_animation_mode="ACTIONS",
    export_nla_strips=False,
    export_bake_animation=True,
    export_frame_range=False,
    export_yup=True,
)
print("EXPORTED", OUT, os.path.getsize(OUT))
