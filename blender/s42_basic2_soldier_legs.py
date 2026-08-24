# -*- coding: utf-8 -*-
"""basic2 의 Walk/Run 하체만 ToonSoldier 모션으로 교체한다.

사용 예:

  OUT_GLB=/tmp/basic2_soldier_legs.glb \
    blender -b -P blender/s42_basic2_soldier_legs.py

입력/출력 환경변수:
  DST_GLB       대상. 기본 web/basic2.glb
  SRC_GLB       하체 모션 원본. 기본 web/soldier.glb
  OUT_GLB       결과. 기본 /tmp/basic2_soldier_legs.glb (원본을 자동 덮지 않는다)
  CLIPS         교체할 클립. 기본 Walk,Run
  GAME_H        게임 안 목표 키. 기본 1.75
  PELVIS_ROT    1이면 Soldier 골반 회전도 이식. 기본 0(현재 상체 기울기 보존)
  EXPORT        0이면 검사만 하고 파일을 쓰지 않는다. 기본 1
  TEX_FORMAT    glTF 이미지 형식. 기본 AUTO
  TEX_QUALITY   이미지 품질. 기본 90

설계 계약:
  * Soldier 의 골반 이동과 양쪽 Thigh/Calf/Foot/Toe0 회전만 이식한다.
  * 골반 회전, Spine/Chest/팔/손/머리는 기존 basic2 클립을 정규화 위상으로
    다시 샘플한다. 따라서 클립 길이가 달라져도 상체와 칼 자세는 유지된다.
  * Attack/Heavy/Idle/Jump/Wide 액션과 메시/스킨/칼/재질은 손대지 않는다.
  * 리그가 다르므로 fcurve 를 직접 복사하지 않고 월드 레스트 델타로 리타게팅한다.
"""

import bpy
import math
import os
import re
from mathutils import Matrix, Quaternion, Vector


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
DST_GLB = os.environ.get("DST_GLB") or os.path.join(WEB, "basic2.glb")
SRC_GLB = os.environ.get("SRC_GLB") or os.path.join(WEB, "soldier.glb")
OUT_GLB = os.environ.get("OUT_GLB") or "/tmp/basic2_soldier_legs.glb"
CLIPS = [x.strip() for x in os.environ.get("CLIPS", "Walk,Run").split(",") if x.strip()]
GAME_H = float(os.environ.get("GAME_H", "1.75"))
PELVIS_ROT = os.environ.get("PELVIS_ROT", "0") == "1"
EXPORT = os.environ.get("EXPORT", "1") != "0"
TEX_FORMAT = os.environ.get("TEX_FORMAT", "AUTO").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

PELVIS = "Bip001 Pelvis"
LEGS = tuple("Bip001 %s %s" % (side, part)
             for side in ("L", "R")
             for part in ("Thigh", "Calf", "Foot", "Toe0"))
LOWER = (PELVIS,) + LEGS
FINAL_ACTIONS = {"Attack", "Heavy", "Idle", "Jump", "Run", "Walk", "Wide"}


def fail(msg):
    raise SystemExit("★ " + msg)


print("=" * 78)
print("[Soldier 하체 이식]")
print("  대상 %s" % DST_GLB)
print("  소스 %s" % SRC_GLB)
print("  결과 %s" % OUT_GLB)
print("  클립 %s / 골반 회전 %s" % (",".join(CLIPS), "이식" if PELVIS_ROT else "기존 유지"))

for p in (DST_GLB, SRC_GLB):
    if not os.path.isfile(p):
        fail("입력 파일이 없다: %s" % p)

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0


def imp(path):
    before_o = set(o.name for o in sc.objects)
    before_a = set(a.name for a in bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in sc.objects if o.name not in before_o]
    acts = [a for a in bpy.data.actions if a.name not in before_a]
    # Blender glTF 임포터가 만드는 뼈 표시용 구는 원본 glb 에 없는 검사 잔재다.
    for o in list(objs):
        if o.type == "MESH" and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o, do_unlink=True)
            objs.remove(o)
    return objs, acts


def use(obj, act):
    if obj.animation_data is None:
        obj.animation_data_create()
    obj.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            obj.animation_data.action_slot = slots[0]
    except Exception:
        pass


def set_frame(f):
    base = math.floor(f)
    sc.frame_set(int(base), subframe=float(f - base))
    bpy.context.view_layer.update()


def action_base(name):
    return re.sub(r"\.\d{3}$", "", name)


def normalized(m):
    r = m.to_3x3()
    r.normalize()
    return r


def angle_deg(a, b):
    q = a.inverted() @ b
    return math.degrees(q.to_quaternion().angle)


def percentile(xs, q):
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, int(len(ys) * q)))]


def evaluated_low(meshes):
    dg = bpy.context.evaluated_depsgraph_get()
    low = float("inf")
    for obj in meshes:
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        try:
            for v in me.vertices:
                low = min(low, (mw @ v.co).z)
        finally:
            ev.to_mesh_clear()
    return low


def new_action(name):
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = None
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    try:
        slot = act.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = slot
    except Exception as e:
        print("  액션 슬롯 생성 건너뜀: %s" % e)
    return act


# ---------------------------------------------------------------- 대상
dst_objs, dst_actions = imp(DST_GLB)
arm = next((o for o in dst_objs if o.type == "ARMATURE"), None)
if arm is None:
    fail("대상 glb 에 아마추어가 없다")
body = [o for o in dst_objs if o.type == "MESH"
        and not o.name.startswith(("SW_", "SH_"))]
swords = [o for o in dst_objs if o.type == "MESH" and o.name.startswith(("SW_", "SH_"))]
old_all = {action_base(a.name): a for a in dst_actions}
missing = sorted(FINAL_ACTIONS - set(old_all))
if missing:
    fail("대상 액션이 부족하다: %s" % missing)
for name in CLIPS:
    if name not in old_all:
        fail("대상에 %s 클립이 없다" % name)
    old_all[name].name = "OLD__" + name
    old_all[name].use_fake_user = True

for bn in LOWER:
    if arm.data.bones.get(bn) is None:
        fail("대상 하체 뼈가 없다: %s" % bn)

print("\n[대상] 아마추어 %s / 뼈 %d / 몸 메시 %d / 무기 메시 %d" %
      (arm.name, len(arm.data.bones), len(body), len(swords)))
print("       액션 %s" % sorted(old_all))

# ---------------------------------------------------------------- Soldier 소스
src_objs, src_actions_fresh = imp(SRC_GLB)
src = next((o for o in src_objs if o.type == "ARMATURE"), None)
if src is None:
    fail("Soldier glb 에 아마추어가 없다")
src_actions = {}
for act in src_actions_fresh:
    base = action_base(act.name)
    act.name = "SRC__" + base
    act.use_fake_user = True
    src_actions[base] = act
for name in CLIPS:
    if name not in src_actions:
        fail("Soldier에 %s 클립이 없다" % name)
for bn in LOWER:
    if src.data.bones.get(bn) is None:
        fail("Soldier 하체 뼈가 없다: %s" % bn)

print("[소스] 아마추어 %s / 뼈 %d / 액션 %s" %
      (src.name, len(src.data.bones), sorted(src_actions)))

# ---------------------------------------------------------------- 레스트/비율
A2W = arm.matrix_world.copy()
A2W_INV = A2W.inverted()
A2W_R_INV = normalized(A2W).inverted()
S2W = src.matrix_world.copy()
DREST = {b.name: b.matrix_local.copy() for b in arm.data.bones}
SREST_W = {b.name: normalized(S2W @ b.matrix_local) for b in src.data.bones}
DREST_W = {b.name: normalized(A2W @ b.matrix_local) for b in arm.data.bones}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}

DREST_PELVIS_W = A2W @ arm.data.bones[PELVIS].head_local
SREST_PELVIS_W = S2W @ src.data.bones[PELVIS].head_local
DREST_FOOT_W = A2W @ arm.data.bones["Bip001 L Foot"].head_local
SREST_FOOT_W = S2W @ src.data.bones["Bip001 L Foot"].head_local
DLEG = (DREST_PELVIS_W - DREST_FOOT_W).length
SLEG = (SREST_PELVIS_W - SREST_FOOT_W).length
K_TRANS = DLEG / SLEG

arm.data.pose_position = "REST"
bpy.context.view_layer.update()
BIND_LOW = evaluated_low(body)
bind_z = []
for o in body:
    bind_z.extend((o.matrix_world @ v.co).z for v in o.data.vertices)
BIND_H = max(bind_z) - min(bind_z)
SCALE = GAME_H / BIND_H
arm.data.pose_position = "POSE"
src.data.pose_position = "POSE"

print("\n[레스트] 대상 다리 %.5f / Soldier 다리 %.5f / 골반 이동 배율 %.5f" %
      (DLEG, SLEG, K_TRANS))
print("         대상 키 %.5f -> 게임 키 %.2f (배율 %.5f) / 바인드 최저 %.5f" %
      (BIND_H, GAME_H, SCALE, BIND_LOW))


def sample_basis(obj, action, f):
    use(obj, action)
    set_frame(f)
    return {b.name: b.matrix_basis.copy() for b in obj.pose.bones}


def source_state(action, f):
    use(src, action)
    set_frame(f)
    rots = {}
    for bn in LOWER:
        rots[bn] = normalized(S2W @ src.pose.bones[bn].matrix)
    pelvis = (S2W @ src.pose.bones[PELVIS].matrix).translation.copy()
    return rots, pelvis


def detach_target():
    if arm.animation_data is not None:
        arm.animation_data.action = None


def build_pose(old_basis, src_rots, pelvis_world, shift):
    """기존 local pose 위에 Soldier 하체만 덮고 대상 pose 행렬 dict 을 돌려준다."""
    detach_target()
    for b in arm.pose.bones:
        b.matrix_basis = old_basis[b.name]
    bpy.context.view_layer.update()

    pose = {b.name: b.matrix.copy() for b in arm.pose.bones}

    # 골반은 위치만 Soldier에서 가져오고 회전은 기존 기본2 것을 유지한다.
    pw = pelvis_world + Vector((0.0, 0.0, shift))
    if PELVIS_ROT:
        rw = src_rots[PELVIS] @ SREST_W[PELVIS].inverted() @ DREST_W[PELVIS]
        ra = A2W_R_INV @ rw
    else:
        ra = normalized(pose[PELVIS])
    ma = Matrix.Translation(A2W_INV @ pw) @ ra.to_4x4()
    pelvis_basis = DREST[PELVIS].inverted() @ ma
    arm.pose.bones[PELVIS].matrix_basis = pelvis_basis
    pose[PELVIS] = ma

    # 하체 자식 회전은 Soldier의 월드 레스트 델타를 대상 레스트에 적용한다.
    for bn in LEGS:
        rw = src_rots[bn] @ SREST_W[bn].inverted() @ DREST_W[bn]
        ra = A2W_R_INV @ rw
        parent = PARENT[bn]
        pmat = pose[parent] @ DREST[parent].inverted() @ DREST[bn]
        pr = normalized(pmat)
        basis = (pr.inverted() @ ra).to_4x4()
        arm.pose.bones[bn].matrix_basis = basis
        pose[bn] = pmat @ basis

    bpy.context.view_layer.update()
    return pose


def clip_samples(name):
    old = old_all[name]
    source = src_actions[name]
    of0, of1 = old.frame_range
    sf0, sf1 = source.frame_range
    # Soldier가 만든 고유 보행 주기와 중복 루프 끝점을 그대로 쓴다.
    n = int(round(sf1 - sf0)) + 1
    rows = []
    for i in range(n):
        phase = i / max(1, n - 1)
        tf = of0 + (of1 - of0) * phase
        sf = sf0 + (sf1 - sf0) * phase
        basis = sample_basis(arm, old, tf)
        rots, pelvis = source_state(source, sf)
        rows.append((phase, basis, rots, pelvis))
    pmean = Vector((
        sum(r[3].x for r in rows) / n,
        sum(r[3].y for r in rows) / n,
        sum(r[3].z for r in rows) / n,
    ))
    # 제자리 애니메이션: Soldier의 절대 위치/평균 root motion을 버리고 진폭만 환산.
    cooked = []
    for phase, basis, rots, pelvis in rows:
        pw = DREST_PELVIS_W + (pelvis - pmean) * K_TRANS
        cooked.append((phase, basis, rots, pw))
    return old, source, cooked


# ============================================================ 26차 GAIT_V26
# ★걷기 하체를 Soldier 리타게팅이 아니라 **절차 보행**으로 굽는다 (2026-08-25,
#   오너 "걸음걸이 왜 이렇게 이상해짐? 질질 끌며 걷는 느낌인데.. 정상적으로 걸어야지").
#
# ── 병의 규명(gait26.py 실측, 25차 커밋본 32bc2c79) ──
#   Soldier 원팩에 Walk 가 없어 s12 가 **Run 을 72% 완화해 합성**한 클립이 소스다.
#   달리기의 골격이 그대로 남아: ①양발 동시접지 0/34장(보행은 원래 ~20% 겹친다.
#   0% = 총총 뜀) ②접지 듀티 12~18%(정상 60%) ③접지 중 발이 골반 대비 2.23m/s 로
#   긁힘 -> ts 1.18 곱하면 화면 발속도 2.63 vs 전진 1.71 = **지면 대비 초당 0.92m
#   역방향 스케이트(-54%)** ④발끝 들림 0.33~0.38m(정상 보행의 5~10배 하이니).
#   게다가 리타게팅이 병을 키웠다: 회전 복사라 궤적이 다리 길이에 비례하는데
#   basic2 다리(게임 0.87m)가 Soldier 비율보다 길어 들림·발속도가 ~1.6배 증폭.
#   ts 로는 못 고친다: 접지 동기화에 필요한 ts 0.766 을 주면 보폭x케이던스가
#   1.15m/s 뿐이라 몸이 +49% 앞으로 미끄러진다. 병은 클립의 **모양**이다.
#
# ── 처방: 보행의 산수를 직접 굽는다 (같은 리그 위 IK, 리타게팅 0) ──
#   무미끄러짐 계약: 접지 중 발의 후방 속도(클립초) x ts = spd.
#     v_c = GAIT_SPD/GAIT_TS = 1.71/1.18 = 1.449 m/s (게임 환산 클립초)
#   듀티 D=0.60(양발 겹침 20%), 스윙 클리어런스 0.11m(카메라 24m 에서 4~5px =
#   또렷하되 행진 아님), 발굴림(뒤꿈치 착지 +12도 -> 플랫 -> 뒤꿈치 들림 -26도),
#   골반 밥 ±0.020m(중간입각 최고·양발지지 최저)·좌우 스웨이 ±0.018m.
#   골반 회전·상체·팔·검은 지금까지처럼 기존 basic2 클립을 위상 재샘플로 유지하고,
#   왼팔 스윙(s27 SWING_L)과 다리가 어긋나지 않게 **기존 클립의 왼발 위상**에
#   보행 위상을 정렬한다(ph0 실측).
#   GAIT_V26=0 이면 이 절이 통째로 꺼지고 Soldier 리타게팅(25차 판)이 그대로 돈다.
GAIT_V26 = os.environ.get("GAIT_V26", "1") == "1"
GAIT_CLIPS = [x.strip() for x in os.environ.get("GAIT_CLIPS", "Walk").split(",")
              if x.strip()]
GAIT_SPD = float(os.environ.get("GAIT_SPD", "1.71"))    # main.js walk.spd
GAIT_TS = float(os.environ.get("GAIT_TS", "1.18"))      # (참고 출력용. 최종 ts 는 실측으로)
GAIT_DUTY = float(os.environ.get("GAIT_DUTY", "0.55"))  # 한 발 접지 비율
# ★발목 글라이드 진폭(게임 m). 2차 굽기 실측 교훈: 이 다리(게임 0.78m)로 v_c 1.449
#   에 필요한 ±0.48 글라이드는 **기하학적으로 불가능**하다(뒤꿈치 착지 사거리가 다리
#   +12%). 실행 가능한 최대 = 앞 +0.34(착지 사거리 딱 맞춤) / 뒤 -0.39(발끝 굴림
#   레버가 발목을 들어 사거리를 벌어준다). 접지 속도 v_c 는 여기서 **유도**되고,
#   무미끄러짐은 main.js walk.ts 를 실측값(spd/v_c)으로 맞춰 완성한다.
GAIT_XF = float(os.environ.get("GAIT_XF", "0.34"))      # 착지(앞) 진폭
GAIT_XB = float(os.environ.get("GAIT_XB", "0.39"))      # 이륙(뒤) 진폭
GAIT_CLEAR = float(os.environ.get("GAIT_CLEAR", "0.11"))  # 스윙 발목 들림(게임 m)
# ★골반 상하 진폭. 1차 굽기 실측 교훈: 0.020 으로는 뒤꿈치 착지 사거리가 안 나온다.
#   보폭 ±0.40(게임) 를 다리 0.87 로 디디려면 양발지지에서 골반이 내려와야 한다
#   (강체 다리면 -0.10, 사람은 발굴림·무릎 유연으로 ±0.045 로 줄인다 — 그 값).
GAIT_BOB = float(os.environ.get("GAIT_BOB", "0.045"))   # 골반 상하(게임 m)
GAIT_SWAY = float(os.environ.get("GAIT_SWAY", "0.018"))  # 골반 좌우(게임 m)
GAIT_N = int(os.environ.get("GAIT_N", "34"))            # 출력 장수(클립 길이 유지)


def gait_on(name):
    return GAIT_V26 and name in GAIT_CLIPS


def _lerp_table(tab, x):
    """(x, y) 제어점 코사인 보간(주기 1). 등차 직선화를 피한다."""
    x = x % 1.0
    for i in range(len(tab) - 1):
        x0, y0 = tab[i]
        x1, y1 = tab[i + 1]
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            t = 0.5 - 0.5 * math.cos(math.pi * t)
            return y0 + (y1 - y0) * t
    return tab[-1][1]


def gait_samples(name):
    """절차 보행 rows: (phase, basis(기존 상체), rots(다리 월드 3x3 목표), 골반월드)."""
    old = old_all[name]
    of0, of1 = old.frame_range
    n = GAIT_N
    up = Vector((0, 0, 1))
    # 전방: 레스트 발끝-발목 수평 투영 (s27 stride 와 같은 잣대)
    fwd = (A2W @ arm.data.bones["Bip001 L Toe0"].head_local
           - A2W @ arm.data.bones["Bip001 L Foot"].head_local)
    fwd.z = 0.0
    fwd.normalize()
    latL = up.cross(fwd)      # 부호는 왼발 쪽으로 실측 정렬
    ankL = A2W @ arm.data.bones["Bip001 L Foot"].head_local
    ankR = A2W @ arm.data.bones["Bip001 R Foot"].head_local
    if latL.dot(ankL - ankR) < 0:
        latL = -latL
    # 다리 제원(월드 레스트)
    hipL = A2W @ arm.data.bones["Bip001 L Thigh"].head_local
    kneL = A2W @ arm.data.bones["Bip001 L Calf"].head_local
    L1 = (kneL - hipL).length
    L2 = (ankL - kneL).length
    toeL = A2W @ arm.data.bones["Bip001 L Toe0"].head_local
    foot_h = (ankL - toeL).dot(fwd) * -1.0            # 발목->발끝 수평 길이
    foot_h = abs(foot_h)
    # 게임 m -> 블렌더 단위
    g2b = 1.0 / SCALE
    T_per = (n - 1) / 30.0                            # 모션 주기(초)
    X_F = GAIT_XF * g2b                               # 착지 앞 진폭(블렌더)
    X_B = GAIT_XB * g2b                               # 이륙 뒤 진폭
    v_c = (X_F + X_B) / (GAIT_DUTY * T_per)           # 접지 활주 속도(유도값)
    # ── 기존 클립 왼발 위상 실측(왼발이 가장 앞 = 뒤꿈치 착지 근사) ──
    best_ph, best_v = 0.0, -1e9
    for k in range(100):
        ph = k / 100.0
        use(arm, old)
        set_frame(of0 + (of1 - of0) * ph)
        lf = (A2W @ arm.pose.bones["Bip001 L Foot"].matrix).translation
        pv = (A2W @ arm.pose.bones[PELVIS].matrix).translation
        v = (lf - pv).dot(fwd)
        if v > best_v:
            best_v, best_ph = v, ph
    ph0 = best_ph
    # ★듀티는 준 값 그대로 쓴다. 1차 굽기의 "사거리 사전 축소 루프"는 듀티를 0.50
    #   까지 깎아 전 프레임 IK 클램프(다리 쭉 뻗은 스플릿)를 만들었다 — 접지 끝단
    #   한두 장의 사거리 부족은 프레임별 IK 클램프(0.998)가 몇 cm 짧게 디디는 것으로
    #   흡수하는 편이(사람의 무릎 유연 착지) 보행 전체를 깎는 것보다 옳다.
    D = GAIT_DUTY
    h0 = ankL.z - BIND_LOW                            # 레스트 발목 높이
    S = X_F + X_B
    _drop = hipL.z - GAIT_BOB * g2b * 0.81 - (h0 + 0.012 * g2b)
    _reach = math.sqrt(X_F * X_F + _drop * _drop)
    print("   (착지 사거리 %.3f vs 다리 %.3f — 초과분은 IK 클램프 = 무릎 유연 착지 /"
          " ★필요 walk.ts = %.3f = spd %.2f ÷ v_c %.3f)"
          % (_reach, L1 + L2, GAIT_SPD / (v_c * SCALE), GAIT_SPD, v_c * SCALE))
    print("\n[GAIT_V26 %s] v_c %.3f(게임 %.3f m/s) 듀티 %.2f 발목 글라이드 +%.3f~-%.3f"
          "(게임 +%.2f~-%.2f) 클리어 %.2f 밥 %.3f 스웨이 %.3f / 기존 왼발 위상 ph0 %.2f"
          % (name, v_c, v_c * SCALE, D, X_F, X_B, GAIT_XF, GAIT_XB,
             GAIT_CLEAR, GAIT_BOB, GAIT_SWAY, ph0))

    # 발굴림 표(위상, 발피치 도. +=발끝 위) — 뒤꿈치 착지/플랫/뒤꿈치 들림/스윙
    th_tab = [(0.00, 14.0), (0.10, 0.0), (0.42, 0.0), (D, -26.0),
              (D + (1 - D) * 0.35, -8.0), (D + (1 - D) * 0.75, 8.0), (1.00, 14.0)]

    def foot_xzth(g):
        """가로 위치(전방 +, 골반 기준) / 발목 높이(바닥 0) / 발 피치(도)."""
        g = g % 1.0
        th = _lerp_table(th_tab, g)
        if g <= D:                                     # 접지: 등속 후방 활주
            x = X_F - v_c * (g * T_per)
            # 발끝 굴림 지렛대 = 발목->발끝 x1.5 (발가락 끝까지. 이 들림이 이륙 쪽
            # 사거리를 벌어 준다). 뒤꿈치 착지(+피치)는 짧은 지렛대(0.4).
            z_roll = 1.5 * foot_h * math.sin(math.radians(max(0.0, -th)))
            z = z_roll + 0.40 * foot_h * math.sin(math.radians(max(0.0, th)))
        else:
            u = (g - D) / (1.0 - D)
            tau = (1.0 - D) * T_per
            A = 2.0 * (S / tau + v_c)
            x = (-X_B - v_c * tau * u
                 + (A * tau * 0.5) * (u - math.sin(2 * math.pi * u)
                                      / (2 * math.pi)))
            z_sw = GAIT_CLEAR * g2b * (math.sin(math.pi * min(1.0, u)) ** 1.3)
            z_roll = 1.5 * foot_h * math.sin(math.radians(max(0.0, -th)))
            z = max(z_sw, z_roll * max(0.0, 1.0 - u / 0.3))
        return x, z, th

    lat_ax = up.cross(fwd).normalized()               # +θ = 발끝 위 (아래 검산)
    if ((Quaternion(lat_ax, math.radians(10)).to_matrix() @ fwd).z) < 0:
        lat_ax = -lat_ax

    rows = []
    for i in range(n):
        phase = i / max(1, n - 1)
        g = (phase - ph0) % 1.0                        # g=0 = 왼발 뒤꿈치 착지
        basis = sample_basis(arm, old, of0 + (of1 - of0) * phase)
        # 골반: 상하(중간입각 최고 g 0.30/0.80) + 좌우(입각 쪽) — 회전은 기존 유지
        pz = GAIT_BOB * g2b * math.cos(4 * math.pi * (g - 0.30))
        py = GAIT_SWAY * g2b * math.cos(2 * math.pi * (g - 0.30))
        pw = DREST_PELVIS_W + up * pz + latL * py
        # 다리: 발목 목표 -> two-bone IK -> 월드 회전 목표
        rots = {}
        for side, g_off in (("L", 0.0), ("R", 0.5)):
            x, z, th = foot_xzth(g + g_off)
            ank_rest = A2W @ arm.data.bones["Bip001 %s Foot" % side].head_local
            A_t = Vector((ank_rest.x, ank_rest.y, BIND_LOW + h0 + z)) \
                + fwd * (x - (ank_rest - DREST_PELVIS_W).dot(fwd))
            hip_rest = A2W @ arm.data.bones["Bip001 %s Thigh" % side].head_local
            H = hip_rest + up * pz + latL * py         # 골반과 같이 움직인다
            d = A_t - H
            dl = min(d.length, (L1 + L2) * 0.998)
            d = d.normalized()
            p = fwd - d * fwd.dot(d)
            if p.length < 1e-6:
                p = up - d * up.dot(d)
            p.normalize()
            ca = (L1 * L1 + dl * dl - L2 * L2) / (2 * L1 * dl)
            alk = math.acos(max(-1.0, min(1.0, ca)))
            K = H + d * (L1 * math.cos(alk)) + p * (L1 * math.sin(alk))
            A_p = H + d * dl
            th_b = "Bip001 %s Thigh" % side
            ca_b = "Bip001 %s Calf" % side
            ft_b = "Bip001 %s Foot" % side
            to_b = "Bip001 %s Toe0" % side
            r_th = (A2W @ arm.data.bones[ca_b].head_local
                    - A2W @ arm.data.bones[th_b].head_local).normalized()
            r_ca = (A2W @ arm.data.bones[ft_b].head_local
                    - A2W @ arm.data.bones[ca_b].head_local).normalized()
            rots[th_b] = (r_th.rotation_difference((K - H).normalized()).to_matrix()
                          @ DREST_W[th_b])
            rots[ca_b] = (r_ca.rotation_difference((A_p - K).normalized()).to_matrix()
                          @ DREST_W[ca_b])
            qf = Quaternion(lat_ax, math.radians(th))
            rots[ft_b] = qf.to_matrix() @ DREST_W[ft_b]
            qt = Quaternion(lat_ax, math.radians(max(th, 0.0)))
            rots[to_b] = qt.to_matrix() @ DREST_W[to_b]
        rows.append((phase, basis, rots, pw))
    return old, rows


def build_pose_gait(old_basis, rots, pelvis_world, shift):
    """build_pose 와 같되 다리 회전이 **이미 대상 월드 목표**다(소스 레스트 매핑 없음).
    골반 회전은 기존 basic2 클립 것을 유지한다(PELVIS_ROT=0 경로와 동일)."""
    detach_target()
    for b in arm.pose.bones:
        b.matrix_basis = old_basis[b.name]
    bpy.context.view_layer.update()
    pose = {b.name: b.matrix.copy() for b in arm.pose.bones}
    pw = pelvis_world + Vector((0.0, 0.0, shift))
    ra = normalized(pose[PELVIS])
    ma = Matrix.Translation(A2W_INV @ pw) @ ra.to_4x4()
    arm.pose.bones[PELVIS].matrix_basis = DREST[PELVIS].inverted() @ ma
    pose[PELVIS] = ma
    for bn in LEGS:
        ra2 = A2W_R_INV @ rots[bn]
        parent = PARENT[bn]
        pmat = pose[parent] @ DREST[parent].inverted() @ DREST[bn]
        pr = normalized(pmat)
        basis = (pr.inverted() @ ra2).to_4x4()
        arm.pose.bones[bn].matrix_basis = basis
        pose[bn] = pmat @ basis
    bpy.context.view_layer.update()
    return pose


made = {}
summary = {}
for name in CLIPS:
    if gait_on(name):
        old, rows = gait_samples(name)
        builder = build_pose_gait
        print("\n[%s] 기존 %.1f~%.1f / **GAIT_V26 절차 보행** / 출력 %d장" %
              (name, old.frame_range[0], old.frame_range[1], len(rows)))
    else:
        old, source, rows = clip_samples(name)
        builder = build_pose
        print("\n[%s] 기존 %.1f~%.1f / Soldier %.1f~%.1f / 출력 %d장" %
              (name, old.frame_range[0], old.frame_range[1],
               source.frame_range[0], source.frame_range[1], len(rows)))

    lows = []
    for _, basis, rots, pw in rows:
        builder(basis, rots, pw, 0.0)
        lows.append(evaluated_low(body))
    q10 = percentile(lows, 0.10)
    shift = BIND_LOW - q10
    print("  접지 1차: 메시 최저 %.5f~%.5f / 10분위 %.5f -> 보정 %+.5f" %
          (min(lows), max(lows), q10, shift))

    action = new_action("NEW__" + name)
    max_upper_local = 0.0
    loop_pos = loop_rot = 0.0
    first_pose = None
    final_lows = []
    for i, (_, basis, rots, pw) in enumerate(rows):
        pose = builder(basis, rots, pw, shift)
        final_lows.append(evaluated_low(body))
        # 계약 검사: 하체 외 local basis는 샘플한 기존 값과 같아야 한다.
        for bn in basis:
            if bn in LOWER:
                continue
            max_upper_local = max(max_upper_local,
                                  (arm.pose.bones[bn].matrix_basis.translation -
                                   basis[bn].translation).length,
                                  angle_deg(normalized(basis[bn]),
                                            normalized(arm.pose.bones[bn].matrix_basis)))
        use(arm, action)
        frame = i + 1
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION"
            pb.keyframe_insert("location", frame=frame)
            pb.keyframe_insert("rotation_quaternion", frame=frame)
            pb.keyframe_insert("scale", frame=frame)
        now = {bn: pose[bn].copy() for bn in LOWER}
        if first_pose is None:
            first_pose = now
        if i == len(rows) - 1:
            for bn in LOWER:
                loop_pos = max(loop_pos, (first_pose[bn].translation - now[bn].translation).length)
                loop_rot = max(loop_rot, angle_deg(normalized(first_pose[bn]), normalized(now[bn])))

    action.use_fake_user = True
    made[name] = action
    summary[name] = dict(n=len(rows), shift=shift, low=min(final_lows), high=max(final_lows),
                         loop_pos=loop_pos, loop_rot=loop_rot,
                         upper=max_upper_local)
    print("  접지 최종: %.5f~%.5f / 루프 하체 위치 %.7f·회전 %.5f도" %
          (min(final_lows), max(final_lows), loop_pos, loop_rot))
    print("  상체 local 보존 최대오차: %.8f (위치m 또는 각도)" % max_upper_local)

# ---------------------------------------------------------------- 정리/내보내기
for name in CLIPS:
    bpy.data.actions.remove(old_all[name])
    made[name].name = name
    made[name].use_fake_user = True

for obj in src_objs:
    if obj.name in sc.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
for act in list(bpy.data.actions):
    if act.name.startswith("SRC__"):
        bpy.data.actions.remove(act)

for act in bpy.data.actions:
    act.use_fake_user = True
actual = set(a.name for a in bpy.data.actions)
if actual != FINAL_ACTIONS:
    fail("최종 액션 목록 불일치: 기대 %s / 실제 %s" %
         (sorted(FINAL_ACTIONS), sorted(actual)))
left = [o for o in sc.objects if o.type in ("MESH", "ARMATURE")]
if len([o for o in left if o.type == "ARMATURE"]) != 1:
    fail("소스 아마추어 잔재가 남았다: %s" % [o.name for o in left])

print("\n[최종 계약]")
print("  액션 %s" % sorted(actual))
print("  대상 본 %d / 메시 %d / 변경 하체 %s" %
      (len(arm.data.bones), len([o for o in left if o.type == "MESH"]), ", ".join(LOWER)))
for name in CLIPS:
    s = summary[name]
    print("  %-4s %2d장 / 접지 %.5f~%.5f / shift %+.5f / 루프 %.7fm·%.5f도" %
          (name, s["n"], s["low"], s["high"], s["shift"],
           s["loop_pos"], s["loop_rot"]))

if EXPORT:
    os.makedirs(os.path.dirname(os.path.abspath(OUT_GLB)), exist_ok=True)
    use(arm, bpy.data.actions["Idle"])
    sc.frame_set(int(round(bpy.data.actions["Idle"].frame_range[0])))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=OUT_GLB,
        export_format="GLB",
        use_selection=False,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_nla_strips=False,
        export_bake_animation=True,
        export_frame_range=False,
        export_yup=True,
        export_image_format=TEX_FORMAT,
        export_image_quality=TEX_QUALITY,
        export_jpeg_quality=TEX_QUALITY,
    )
    print("\nEXPORTED %s (%d bytes)" % (OUT_GLB, os.path.getsize(OUT_GLB)))
else:
    print("\nEXPORT=0 — 파일을 쓰지 않았다")
print("=" * 78)
