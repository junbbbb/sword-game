# -*- coding: utf-8 -*-
"""s43 — Mixamo Great Sword 팩을 basic2 리그에 리타게팅한다(27차 정본).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python blender/s43_mixamo_retarget.py
  -> renders/mixamo/build/basic2_mixamo60c.glb   (md5 9b56f79a, 2026-08-27 배포본)
  이걸 web/basic2.glb 로 복사하고 tools/build_deploy.py -> dist -> vercel.

★27차에 **수제 키프레임 파이프라인(s24 bake_hand)을 폐기**하고 이리로 왔다. 이유는
  docs/HANDOFF.md §7 모션 참고 — 여섯 파도 연속 기각의 원인이 파라미터가 아니라 방법
  이었다(계약은 필요조건일 뿐 동작이 아니다). s24 는 Attack(Z, 봉인) 때문에 살아 있다.

입력 (전부 레포 안. renders/·incoming/ 은 gitignore 지만 이 기계에 남는다)
  기준본  incoming/mixamo_greatsword/base_basic2_w26.glb  = 26차 배포본 a3e730ea
          ★web/basic2.glb 를 읽으면 자기 출력이 다음 입력이 되어 재현이 깨진다.
  소스    incoming/mixamo_greatsword/pack/   Mixamo 팩 51종(30fps)
          incoming/mixamo_greatsword/new60/  오너가 60fps 로 다시 받은 3종
  ★Mixamo 다운로드 설정: FBX Binary · **Without Skin** · 30 또는 60fps ·
    **Keyframe Reduction = none**(축소하면 속도 정점이 뭉개져 hot 창이 달라진다).

핵심 두 가지 — 이걸 모르면 결과가 통째로 틀어진다
  ① ALIGN_TO_AXE : Mixamo 대검 모션은 Brute.fbx 의 BattleAxe_GEO 를 전제로 만들어졌다.
     그 도끼도 우리 칼과 똑같이 mixamorig:RightHand 하나에만 스킨돼 있고, 레스트 축이
     우리 칼과 **66도** 어긋나 있었다(칼끝으로 0.75m). 안 맞추면 Brute 가 도끼를 세워
     드는 자리에서 우리는 칼을 땅으로 늘어뜨린다. `mixamorig:Weapon` 뼈는 실제 도끼와
     86.8도 어긋난 **미사용 뼈**다 — 기준 삼았다가 렌더에서 기각했다.
  ② BLADE_ROLL : ①의 rotation_difference 는 축만 맞추는 최소 회전이라 칼축 둘레 롤이
     임의로 남는다. 그대로면 "넓적면으로 내리치는" 그림이 된다(실측 48~52도). 295도.

전 클립 60fps. 30fps 소스는 반프레임 subframe 보간으로 60 격자에 다시 담고, 기준본도
60fps 로 임포트한다(안 그러면 봉인된 Attack 길이가 두 배로 뒤틀린다).

원본 대비 허용된 일탈(전부 골반 '이동' 채널, 관절 회전은 원본 그대로)
  Jump      골반 이동 z 를 f0 값으로 고정(게임 코드가 root 를 띄우므로 이중 점프 방지).
  Walk/Run  골반 이동 xy 의 '선형 추세'(루트 전진 net)만 제거. 루프 클립인데 소스가
            전진형이라 그대로 두면 매 사이클 순간이동 스냅백이 난다(전진은 main.js 소관).
  Idle      LOOP_SEAL — 끝 N프레임을 첫 프레임 포즈로 수렴시켜 루프 이음새를 없앤다.
관절 보정은 **없다**. 6클립 전부 관통 계약을 그냥 통과한 것들만 골랐다.

★함정: macOS 파일시스템은 대소문자를 구분 안 한다. `Great Sword Idle.fbx` 가 팩의
  `great sword idle.fbx` 에 매칭돼 엉뚱한 파일을 집은 사고가 있었다 — 소스 탐색은
  디렉토리 listdir 로 **정확한 대소문자 일치**를 확인한다(new60 을 먼저 본다).

남은 일은 docs/HANDOFF.md §7 모션 22-a~f (IdleAlt 바닥 관통 −0.23m 등).
"""
import bpy, json, math, os, struct
from mathutils import Vector, Matrix, Quaternion

REPO = "/Users/lbj/Documents/gameproject"
SCRATCH = os.environ.get("MX_SCRATCH", os.path.join(REPO, "renders", "mixamo"))
BUILD = os.path.join(SCRATCH, "build")
# ★타깃은 **고정된 기준본**이다. web/basic2.glb 를 읽으면 자기 출력이 다음 실행의
#   입력이 되어(봉인된 Attack 이 GLB 왕복으로 재샘플된다) md5 재현이 깨진다.
GLB = os.path.join(REPO, "incoming", "mixamo_greatsword", "base_basic2_w26.glb")
GSP  = os.path.join(REPO, "incoming", "mixamo_greatsword", "pack")    # Mixamo 팩 51종
GSP2 = os.path.join(REPO, "incoming", "mixamo_greatsword", "new60")   # 오너가 60fps 로 다시 받은 것
OUT = os.path.join(BUILD, "basic2_mixamo60c.glb")
K_TRANS = 0.6809
PELVIS = "Bip001 Pelvis"
FEET = ["Bip001 L Foot", "Bip001 R Foot", "Bip001 L Toe0", "Bip001 R Toe0"]
RH = "Bip001 R Hand"
SWORD = "SW_nokseun"

#          액션      소스 FBX                         xy추세제거  z고정
CLIPS6 = [
    ("Idle",    "Great Sword Idle2_new.fbx",     False, False),
    ("IdleAlt", "Great Sword Idle_new.fbx",      False, False),
    ("Walk",    "great sword walk.fbx",      True,  False),
    ("Run",     "great sword run (2).fbx",   True,  False),
    ("Jump",    "great sword jump (2).fbx",  False, True),
    ("Heavy",   "Great Sword Slash 3_new.fbx",   False, False),
    ("Wide",    "great sword slash (3).fbx", False, False),
]
LOOP_SEAL = {}   # 액션: 끝에서 몇 프레임에 걸쳐 첫 프레임 포즈로 수렴시킬지

MAP = [
    ("Bip001 Pelvis",     "mixamorig:Hips"),
    ("Bip001 Chest2",     "mixamorig:Spine"),
    ("Bip001 Chest",      "mixamorig:Spine1"),
    ("Bip001 Spine",      "mixamorig:Spine2"),
    ("Bip001 Neck",       "mixamorig:Neck"),
    ("Bip001 Head",       "mixamorig:Head"),
    ("Bip001 L Clavicle", "mixamorig:LeftShoulder"),
    ("Bip001 L UpperArm", "mixamorig:LeftArm"),
    ("Bip001 L Forearm",  "mixamorig:LeftForeArm"),
    ("Bip001 L Hand",     "mixamorig:LeftHand"),
    ("Bip001 R Clavicle", "mixamorig:RightShoulder"),
    ("Bip001 R UpperArm", "mixamorig:RightArm"),
    ("Bip001 R Forearm",  "mixamorig:RightForeArm"),
    ("Bip001 R Hand",     "mixamorig:RightHand"),
    ("Bip001 L Thigh",    "mixamorig:LeftUpLeg"),
    ("Bip001 L Calf",     "mixamorig:LeftLeg"),
    ("Bip001 L Foot",     "mixamorig:LeftFoot"),
    ("Bip001 L Toe0",     "mixamorig:LeftToeBase"),
    ("Bip001 R Thigh",    "mixamorig:RightUpLeg"),
    ("Bip001 R Calf",     "mixamorig:RightLeg"),
    ("Bip001 R Foot",     "mixamorig:RightFoot"),
    ("Bip001 R Toe0",     "mixamorig:RightToeBase"),
]
report = dict(clips={})


def qn(M):
    m = M.to_3x3()
    m.normalize()
    return m.to_quaternion()


def sdeg(q1, q2):
    a = q1.rotation_difference(q2).angle
    return math.degrees(a if a <= math.pi else 2 * math.pi - a)


# ======================================================================
# 0. 타깃 GLB 로드 + 클립 무관 상수 (fix_export.py 와 동일)
# ======================================================================
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
sc = bpy.context.scene
sc.render.fps = 60          # ★27차b: 전 구간 60fps (게임이 60+ 로 돌고, 빠른 베기는 키가 촘촘해야 궤적·판정이 산다)
sc.render.fps_base = 1.0

bpy.ops.import_scene.gltf(filepath=GLB)
tgt_objs = set(bpy.data.objects)
tgt = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
ad_t = tgt.animation_data
mute_saved = {t.name: t.mute for t in ad_t.nla_tracks}
for t in ad_t.nla_tracks:
    t.mute = True
ad_t.action = None
sc.frame_set(1)
bpy.context.view_layer.update()

Mw_t = tgt.matrix_world.copy()
Qm_t = qn(Mw_t)
Qm_t_inv = Qm_t.inverted()
Mw_t_inv = Mw_t.inverted()
q_rest_w_t = {tb: qn(Mw_t @ tgt.data.bones[tb].matrix_local) for tb, _ in MAP}
q_rest_arm_t = {b.name: qn(b.matrix_local) for b in tgt.data.bones}
rest_local_pel = tgt.data.bones[PELVIS].matrix_local.copy()
p_rest_pel_t = (Mw_t @ tgt.data.bones[PELVIS].matrix_local).to_translation()
rest_base = min((Mw_t @ tgt.data.bones[b].head_local).z for b in FEET)

# 칼 바인드 기하(검증용 측정에 쓴다)
sw = bpy.data.objects[SWORD]
Msw = sw.matrix_world.copy()
verts = [Msw @ v.co for v in sw.data.vertices]
hand_rest4 = Mw_t @ tgt.data.bones[RH].matrix_local
hand_rest_p = hand_rest4.to_translation()
tip_bind = max(verts, key=lambda v: (v - hand_rest_p).length)
mean = sum(verts, Vector()) / len(verts)
u = (tip_bind - mean).normalized()
for _ in range(30):
    acc = Vector()
    for v in verts:
        d = v - mean
        acc += d * d.dot(u)
    u = acc.normalized()
if u.dot(tip_bind - mean) < 0:
    u = -u
pommel_bind = min(verts, key=lambda v: (v - mean).dot(u))
mid_bind = (tip_bind + pommel_bind) * 0.5
hand_rest_inv = hand_rest4.inverted()

# ── 칼 정렬(ALIGN_TO_AXE) ──────────────────────────────────────────────
# Mixamo 대검 모션은 Brute 의 BattleAxe_GEO 를 전제로 만들어졌다. 그 도끼는 우리 칼과
# 똑같이 mixamorig:RightHand 하나에만 스킨돼 있고, 레스트에서 축이 아래 방향이다.
# (mixamorig:Weapon 뼈는 실제 무기 위치와 86.8도 어긋나 있어 기준이 못 된다 — 실측 기각)
# 우리 칼 레스트 축은 (-0.5247,-0.1715,+0.8338) 로 도끼와 66.0도 어긋나 있었다.
# 조건: R_rest·C·blade_local = axe_dir,  R_rest·blade_local = bl_dir
#   ⇒ W=(bl_dir→axe_dir 월드회전),  C = R_rest^-1·W·R_rest,  q_hand'(f) = q_hand(f)·C
ALIGN_TO_AXE = True
AXE_REST_DIR = Vector((-0.442246, -0.896557, 0.024569))   # Brute.fbx 실측
_bl = (tip_bind - pommel_bind).normalized()
_W = _bl.rotation_difference(AXE_REST_DIR)
_Rr = q_rest_w_t[RH]
GRIP_C = _Rr.inverted() @ _W @ _Rr if ALIGN_TO_AXE else None
# ── 날 세우기(BLADE_ROLL) ──────────────────────────────────────────────────
# rotation_difference 는 축만 맞추는 **최소 회전**이라 칼축 둘레 롤이 임의로 남는다.
# 그래서 오너 지적대로 "뾰족한 날이 아니라 넓적면으로 내리치는" 그림이 됐다.
# 25차 날 정렬 계약(hot 프레임에서 칼끝 속도벡터-날평면 사잇각 ≤30도)으로 재니
# 48.3도(Heavy)·51.7도(Wide) — 날과 넓적면의 딱 중간이었다.
# 0~360도를 훑어 속도가중 평균 어긋남을 최소화하는 각을 찾았다: 295도.
#   -> Heavy 24.8 · Wide 27.8 (둘 다 계약 안). 180도 주기라 115도도 같은 값이다.
# 롤 축이 칼 자신의 축(손 로컬 b_l)이라 **칼끝 궤적과 히트 판정은 불변**이다.
BLADE_ROLL_DEG = 295.0
if GRIP_C is not None and BLADE_ROLL_DEG:
    _bl_local = _Rr.inverted() @ _bl              # 칼축(손→칼끝)을 손 로컬로
    GRIP_C = GRIP_C @ Quaternion(_bl_local, math.radians(BLADE_ROLL_DEG))
    print("[날세우기] 칼축 둘레 %.1f도 롤 (넓적면 -> 날)" % BLADE_ROLL_DEG)
if GRIP_C is not None:
    import math as _m
    report['align_to_axe'] = dict(sword_rest=[round(v,5) for v in _bl],
                                  axe_rest=[round(v,5) for v in AXE_REST_DIR],
                                  offset_deg=round(_m.degrees(_W.angle),2))
    print("[칼정렬] 레스트 칼축을 Brute 도끼축에 맞춤: %.2f도 회전" % _m.degrees(_W.angle))

report['const'] = dict(k_trans=K_TRANS, rest_base=round(rest_base, 4),
                       hand_tip_len=round((tip_bind - hand_rest_p).length, 4))
print("[상수] rest_base=%.4f 손~칼끝=%.4f" % (rest_base, (tip_bind - hand_rest_p).length))


def eval_frame(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()


def hp(b):
    return (tgt.matrix_world @ tgt.pose.bones[b].matrix).translation.copy()


def wq(b):
    return qn(tgt.matrix_world @ tgt.pose.bones[b].matrix)


def sword_pts():
    T = (tgt.matrix_world @ tgt.pose.bones[RH].matrix) @ hand_rest_inv
    return T @ pommel_bind, T @ mid_bind, T @ tip_bind


def feet_min_z():
    Mf = tgt.matrix_world
    return min((Mf @ tgt.pose.bones[b].matrix).translation.z for b in FEET)


# ======================================================================
# 1. 클립 루프: 소스 샘플 -> 새 액션 베이크(접지 2패스) -> 소스 제거
# ======================================================================
old_actions = {}       # 액션명 -> 옛 액션(나중에 NLA 재배선 후 제거)
new_actions = {}

for ACT, fbx_name, detrend_xy, pin_z in CLIPS6:
    # ★macOS 는 대소문자를 구분 안 한다: "Great Sword Idle_new.fbx" 가 옛 팩의
    #   "great sword idle.fbx" 에 매칭돼 엉뚱한 파일을 집은 사고가 있었다.
    #   새로 받은 것(gsp2)을 먼저 보고, 실제 파일명 대소문자까지 확인한다.
    path = None
    for d in (GSP2, GSP):
        if not os.path.isdir(d):
            continue
        if fbx_name in os.listdir(d):          # 대소문자 정확 일치
            path = os.path.join(d, fbx_name)
            break
    if path is None:
        raise SystemExit("★소스 없음: %s (gsp2/gsp 어디에도 정확한 이름이 없다)" % fbx_name)
    print("[%s] 소스 파일 %s" % (ACT, path))
    ent = dict(src=fbx_name)
    report['clips'][ACT] = ent
    pre_objs = set(bpy.data.objects)
    pre_acts = set(bpy.data.actions)
    sc.render.fps = 60
    sc.render.fps_base = 1.0
    bpy.ops.import_scene.fbx(filepath=path)
    fps_scene = sc.render.fps / sc.render.fps_base
    if fps_scene not in (30.0, 60.0):
        raise SystemExit("★%s fps %.3f (30 또는 60 이어야)" % (fbx_name, fps_scene))
    fbx_objs = [o for o in bpy.data.objects if o not in pre_objs]
    new_acts = [a for a in bpy.data.actions if a not in pre_acts]
    src = next(o for o in fbx_objs if o.type == 'ARMATURE')
    src_act = src.animation_data.action if src.animation_data else None
    if src_act is None:
        src_act = next((a for a in new_acts if 'mixamo' in a.name.lower()), new_acts[0])
        src.animation_data_create()
        src.animation_data.action = src_act
    F0 = int(round(src_act.frame_range[0]))
    F1 = int(round(src_act.frame_range[1]))
    if F0 != 1:
        raise SystemExit("★%s F0=%d (1 이어야)" % (fbx_name, F0))
    nf = F1 - F0 + 1
    sc.frame_start, sc.frame_end = F0, F1
    ent['frames'] = [F0, F1]
    ent['dur_export_s'] = round(F1 / 30.0, 4)

    # ---- 소스 rest/포즈 샘플 ----
    eval_frame(F0)
    Mw_s = src.matrix_world.copy()
    q_rest_w_s = {sb: qn(Mw_s @ src.data.bones[sb].matrix_local) for _, sb in MAP}
    p_rest_hips_s = (Mw_s @ src.data.bones['mixamorig:Hips'].matrix_local).to_translation()
    src_q, src_hip = {}, {}
    STEP = fps_scene / 60.0          # 30fps 소스면 0.5(반프레임 보간), 60fps 면 1.0
    NOUT = int(round((F1 - F0) / STEP)) + 1
    for i in range(NOUT):
        p = F0 + i * STEP
        ip = int(p // 1)
        sc.frame_set(ip, subframe=float(p - ip))
        bpy.context.view_layer.update()
        f = i + 1                    # 출력은 언제나 60fps 프레임 번호 1..NOUT
        Mf = src.matrix_world
        for _, sb in MAP:
            src_q[(f, sb)] = qn(Mf @ src.pose.bones[sb].matrix)
        src_hip[f] = (Mf @ src.pose.bones['mixamorig:Hips'].matrix).translation.copy()
    # ↓ 이 아래로는 전부 60fps 출력 프레임 번호로 센다
    F0, F1 = 1, NOUT
    nf = NOUT
    sc.render.fps = 60
    sc.render.fps_base = 1.0
    sc.frame_start, sc.frame_end = F0, F1
    ent['frames'] = [F0, F1]
    ent['src_fps'] = fps_scene
    ent['dur_export_s'] = round(F1 / 60.0, 4)
    print("[%s] 소스 %.0ffps %d장 -> 60fps %d장 (%.3fs)"
          % (ACT, fps_scene, int(round((F1 - 1) * STEP)) + 1, NOUT, NOUT / 60.0))

    # ---- 루프 봉합: 끝 N프레임을 첫 프레임 포즈로 수렴시켜 이음새 제거 ----
    _N = LOOP_SEAL.get(ACT, 0)
    if _N and (F1 - F0) > _N:
        import math as _m
        _seam_before = max(_m.degrees(
            (src_q[(F1, sb)] @ src_q[(F0, sb)].inverted()).angle) for _, sb in MAP)
        for _, sb in MAP:
            _err = src_q[(F1, sb)] @ src_q[(F0, sb)].inverted()   # 끝-시작 불일치
            for f in range(F1 - _N + 1, F1 + 1):
                t = (f - (F1 - _N)) / float(_N)
                w = 0.5 - 0.5 * _m.cos(_m.pi * t)                 # 0 -> 1 부드럽게
                src_q[(f, sb)] = _err.inverted().slerp(
                    __import__('mathutils').Quaternion(), 1.0 - w) @ src_q[(f, sb)]
        _perr = src_hip[F1] - src_hip[F0]
        for f in range(F1 - _N + 1, F1 + 1):
            t = (f - (F1 - _N)) / float(_N)
            w = 0.5 - 0.5 * _m.cos(_m.pi * t)
            src_hip[f] = src_hip[f] - _perr * w
        _seam_after = max(_m.degrees(
            (src_q[(F1, sb)] @ src_q[(F0, sb)].inverted()).angle) for _, sb in MAP)
        ent['loop_seal'] = dict(frames=_N, seam_before_deg=round(_seam_before, 2),
                                seam_after_deg=round(_seam_after, 3))
        print("[%s] 루프 봉합 %d프레임: 이음새 %.1f도 -> %.2f도"
              % (ACT, _N, _seam_before, _seam_after))

    # ---- 골반 이동 채널 처리(관절 회전 불변) ----
    if pin_z:                                   # Jump: 수직 성분 억제
        z0 = src_hip[F0].z
        dz = [src_hip[f].z - z0 for f in range(F0, F1 + 1)]
        ent['jump_z_suppressed'] = dict(
            src_max=round(max(dz), 4), src_min=round(min(dz), 4),
            tgt_max=round(max(dz) * K_TRANS, 4), tgt_min=round(min(dz) * K_TRANS, 4))
        for f in range(F0, F1 + 1):
            src_hip[f].z = z0
        print("[Jump] 골반 z 억제: 소스 %+.3f~%+.3f m (타깃환산 %+.3f~%+.3f m) -> f0 값 고정"
              % (min(dz), max(dz), min(dz) * K_TRANS, max(dz) * K_TRANS))
    if detrend_xy:                              # Walk/Run: 수평 선형 추세 제거
        net = src_hip[F1] - src_hip[F0]
        net.z = 0.0
        ent['xy_detrend'] = dict(src_net=round(net.length, 4),
                                 tgt_net=round(net.length * K_TRANS, 4))
        for f in range(F0, F1 + 1):
            w = (f - F0) / float(F1 - F0)
            src_hip[f] = src_hip[f] - net * w
        print("[%s] 골반 xy 추세 제거: 소스 net %.3f m (타깃환산 %.3f m)"
              % (ACT, net.length, net.length * K_TRANS))

    # ---- 새 액션 생성 + 베이크 ----
    old = bpy.data.actions.get(ACT)
    if old is None:
        print("[%s] 타깃에 없던 새 액션이다 — 신규로 만든다" % ACT)   # IdleAlt
    else:
        old.name = ACT + '_old'
        old_actions[ACT] = old
    act = bpy.data.actions.new(ACT)
    act.use_fake_user = True
    new_actions[ACT] = act
    ad_t.action = act
    try:
        slot = act.slots.new(id_type='OBJECT', name=tgt.name)
        ad_t.action_slot = slot
    except Exception as e:
        print("[액션] 슬롯:", e)

    def bake_frame(f, z_off, prev_q):
        q_pose = {}
        for tb, sb in MAP:
            D = src_q[(f, sb)] @ q_rest_w_s[sb].inverted()
            qw = D @ q_rest_w_t[tb]
            if GRIP_C is not None and tb == RH:
                qw = qw @ GRIP_C
            q_pose[tb] = Qm_t_inv @ qw
        p_goal = p_rest_pel_t + (src_hip[f] - p_rest_hips_s) * K_TRANS
        p_goal.z += z_off
        for tb, sb in MAP:
            pb = tgt.pose.bones[tb]
            par = tgt.data.bones[tb].parent
            if par is None:
                v_arm = Mw_t_inv @ p_goal
                pose4 = Matrix.Translation(v_arm) @ q_pose[tb].to_matrix().to_4x4()
                basis4 = rest_local_pel.inverted() @ pose4
                qb = qn(basis4)
                pb.location = basis4.to_translation()
                pb.keyframe_insert('location', frame=f)
            else:
                qb = (q_rest_arm_t[tb].inverted() @ q_rest_arm_t[par.name]
                      @ q_pose[par.name].inverted() @ q_pose[tb])
            prev = prev_q.get(tb)
            if prev is not None and qb.dot(prev) < 0.0:
                qb.negate()
            prev_q[tb] = qb.copy()
            pb.rotation_quaternion = qb
            pb.keyframe_insert('rotation_quaternion', frame=f)

    prev_q = {}
    for f in range(F0, F1 + 1):
        bake_frame(f, 0.0, prev_q)
    lows0 = []
    for f in range(F0, F1 + 1):
        eval_frame(f)
        lows0.append(feet_min_z())
    z_off = rest_base - min(lows0)
    prev_q = {}
    for f in range(F0, F1 + 1):
        bake_frame(f, z_off, prev_q)
    ent['z_off'] = round(z_off, 4)

    # ---- 즉석 자기검증(간이. 정밀 측정은 measure6.py 가 GLB 에서 다시 한다) ----
    tips, feet, pelxy = [], [], []
    q_edge = {}
    for f in (F0, F1):
        eval_frame(f)
        q_edge[f] = {tb: wq(tb) for tb, _ in MAP}
    for f in range(F0, F1 + 1):
        eval_frame(f)
        tips.append(sword_pts()[2])
        feet.append(feet_min_z())
        p = hp(PELVIS)
        pelxy.append((p.x, p.y))
    ent['ground_dev'] = round(abs(min(feet) - rest_base), 6)
    ent['tip_min'] = round(min(t.z for t in tips), 4)
    ent['stance_f0_feet'] = round(feet[0] - rest_base, 4)
    if ACT in ('Idle', 'Walk', 'Run'):
        seam = max(sdeg(q_edge[F0][tb], q_edge[F1][tb]) for tb, _ in MAP)
        dxy = math.hypot(pelxy[-1][0] - pelxy[0][0], pelxy[-1][1] - pelxy[0][1])
        ent['loop_seam_deg'] = round(seam, 2)
        ent['loop_pel_xy_gap'] = round(dxy, 4)
    print("[베이크] %-5s %d장 z_off %+0.4f tip_min %+0.4f 접지오차 %.6f"
          % (ACT, nf, z_off, ent['tip_min'], ent['ground_dev']))

    # ---- 소스 제거 ----
    ad_t.action = None
    for o in fbx_objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in new_acts:
        try:
            bpy.data.actions.remove(a, do_unlink=True)
        except Exception:
            pass

# ======================================================================
# 2. NLA 재배선: 옛 액션 스트립 -> 새 액션 (fix_export.py 와 동일 패턴)
# ======================================================================
for ACT in new_actions:
    old = old_actions.get(ACT)          # 신규 액션(IdleAlt)은 옛 짝이 없다
    victim = None
    if old is not None:
        for t in ad_t.nla_tracks:
            for s in t.strips:
                if s.action and s.action.name == old.name:
                    victim = t
    name = victim.name if victim is not None else ACT
    if victim is not None:
        ad_t.nla_tracks.remove(victim)
    tr = ad_t.nla_tracks.new()
    tr.name = name
    strip = tr.strips.new(ACT, 1, new_actions[ACT])
    try:
        strip.action_slot = new_actions[ACT].slots[0]
    except Exception as e:
        print("[NLA]", e)
    if old is not None:
        bpy.data.actions.remove(old, do_unlink=True)

ad_t.action = None
for t in ad_t.nla_tracks:
    t.mute = mute_saved.get(t.name, False)
for _ in range(3):
    bpy.data.orphans_purge(do_recursive=True)

# ======================================================================
# 3. 익스포트 + GLB JSON 청크 자체검증
# ======================================================================
try:
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB',
                              export_animation_mode='ACTIONS', export_animations=True)
except TypeError as e:
    print("[익스포트] 폴백:", e)
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB')

with open(OUT, 'rb') as fh:
    blob = fh.read()
clen, _ = struct.unpack('<II', blob[12:20])
gj = json.loads(blob[20:20 + clen])
anims = gj.get('animations', [])
lines = []
for an in anims:
    ins = {s['input'] for s in an['samplers']}
    mn = min(gj['accessors'][i]['min'][0] for i in ins)
    mx = max(gj['accessors'][i]['max'][0] for i in ins)
    lines.append(dict(name=an['name'], channels=len(an['channels']),
                      t0=round(mn, 4), dur=round(mx, 4)))
    print("[GLB] %-6s ch %d  t %.4f~%.4f" % (an['name'], len(an['channels']), mn, mx))
names = sorted(l['name'] for l in lines)
EXPECT = sorted(['Attack', 'Heavy', 'Idle', 'Jump', 'Run', 'Walk', 'Wide'] + [a for a, *_ in CLIPS6 if a == 'IdleAlt'])
if names != EXPECT:
    raise SystemExit("★GLB 애니 목록 불일치: %s (기대 %s)" % (names, EXPECT))
report['glb'] = lines
report['glb_bytes'] = len(blob)
with open(os.path.join(BUILD, 'build_report_60c.json'), 'w') as fh:
    json.dump(report, fh, indent=1, ensure_ascii=False)
print("BUILD_DONE", OUT)
