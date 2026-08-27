# -*- coding: utf-8 -*-
"""poc2: Mixamo 대검 내려베기 리타게팅(poc1 검증 코어 그대로) + 최소 보정.
    Blender -b --factory-startup --python fix_export.py

산출:
  poc2/basic2_heavy_mixamo.glb  보정 전(중간 스트립·기준)
  poc2/basic2_heavy_fixed.glb   보정 후 ★납품물
  poc2/fix_report.json          프레임별 "원본을 얼마나 옮겼는가" 전체 기록

보정(최소 일탈 원칙 - 원본 유지, 계약 깨는 프레임만, 최소량만):
  [1] 칼끝 관통(z < -0.025): R Clavicle/UpperArm/Forearm 에 월드 사전회전을
      가중 최소제곱(lever 비례, 쇄골 1/4 가중)으로 배분하는 Newton 으로
      칼끝 z=+0.02 달성. 관통 스팬 앞뒤 3프레임 코사인 램프로 감쇠.
      골반·다리·왼팔은 여기서 절대 건드리지 않는다.
  [2] 왼손 자루 이탈(>0.10m): 왼 UpperArm/Forearm 2본 IK. 시드=리타게팅 원본
      포즈에서 최소회전(rotation_difference)만 누적 -> 가장 가까운 해.
      원본 팔꿈치 평면 유지, 손목 목표 = 보정된 자루축에서 0.10m(원본 접근
      방향 유지, 축상 위치는 원본 정상그립 구간 [s_lo,s_hi]로 클램프).
      이탈<=0.10 프레임은 불개입. 왼팔뚝 프레임간 45° 초과 시 그 프레임 IK 해제.
★승격 노트(2026-08-27) — 원본은 세션 스크래치패드에 있었고 그건 사라진다. HANDOFF §7
  22-a(IdleAlt 바닥 관통 -0.23m, 오너 보류)의 처방이 [1]번 보정이라 **참조 구현으로**
  레포에 들여왔다. 그대로는 안 돈다: 아래 POC·FBX 경로가 사라진 스크래치 경로이고,
  대상도 27차 이전의 Heavy 클립이다. 27차 리타게팅 정본은 blender/s43_mixamo_retarget.py
  이고, 이 파일에서 가져다 쓸 것은 관통 프레임에 쇄골·위팔·팔뚝으로 최소 회전을 배분하는
  뉴턴 + 코사인 램프의 산수다(apply_fix1 부근). ★그때는 관통이 -0.76m 라 오른팔을 58도
  까지 옮겼다 - 22-a 는 -0.23m 이니 개입각이 훨씬 작아야 정상이다. 반드시 재서 보고할 것.
  계측은 같이 올라온 poc2_measure_metrics.py(GLB·OUTJSON 환경변수).
"""
import bpy, json, math, os, struct
from mathutils import Vector, Matrix, Quaternion

POC = "/private/tmp/claude-501/-Users-lbj/daecc644-d7fb-4b67-bf22-e40f318e0f80/scratchpad/poc2"
GLB = "/Users/lbj/Documents/gameproject/web/basic2.glb"
FBX = "/private/tmp/claude-501/-Users-lbj/daecc644-d7fb-4b67-bf22-e40f318e0f80/scratchpad/gsp/great sword slash.fbx"
OUT_MIX = os.path.join(POC, "basic2_heavy_mixamo.glb")
OUT_FIX = os.path.join(POC, "basic2_heavy_fixed.glb")
K_TRANS = 0.6809
F0, F1 = 1, 39
PELVIS = "Bip001 Pelvis"
FEET = ["Bip001 L Foot", "Bip001 R Foot", "Bip001 L Toe0", "Bip001 R Toe0"]
RC, RU, RF, RH = "Bip001 R Clavicle", "Bip001 R UpperArm", "Bip001 R Forearm", "Bip001 R Hand"
LC, LU, LF, LH = "Bip001 L Clavicle", "Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand"
SWORD = "SW_nokseun"
PEN_MAX = 0.025          # 계약: 이보다 깊이 박히면 위반
Z_TGT = 0.02             # 관통 프레임 목표 칼끝 z
RAMP_W = [0.853553, 0.5, 0.146447]   # 코사인 램프 0.5*(1+cos(pi*k/4)), k=1..3
D_ON = 0.10              # 왼손 개입 문턱 = 목표 거리
STEP_LIMIT = 45.0        # 왼팔뚝 프레임간 한계(도)

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
report = {}


def qn(M):
    m = M.to_3x3()
    m.normalize()
    return m.to_quaternion()


def canon(q):
    """부호 정규화(w>=0). q 와 -q 는 같은 회전이지만 angle/slerp 해석이 갈린다."""
    q = q.normalized()
    if q.w < 0:
        q.negate()
    return q


def qdeg(q):
    a = q.angle
    return math.degrees(a if a <= math.pi else 2 * math.pi - a)


def sdeg(q1, q2):
    return qdeg(q1.rotation_difference(q2))


# ======================================================================
# 0. poc1 과 동일한 리타게팅 (검증 완료 코어. 로직 변경 없음)
# ======================================================================
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
sc = bpy.context.scene
sc.render.fps = 30
sc.frame_start, sc.frame_end = F0, F1

bpy.ops.import_scene.gltf(filepath=GLB)
tgt_objs = set(bpy.data.objects)
tgt = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bpy.ops.import_scene.fbx(filepath=FBX)
src = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o not in tgt_objs)
fbx_objs = [o for o in bpy.data.objects if o not in tgt_objs]
mix_actions = [a for a in bpy.data.actions if 'mixamo' in a.name.lower()]
print("[임포트] 타깃 %s / 소스 %s" % (tgt.name, src.name))

ad_t = tgt.animation_data
mute_saved = [(t, t.mute) for t in ad_t.nla_tracks]
for t, _ in mute_saved:
    t.mute = True

sc.frame_set(F0)
bpy.context.view_layer.update()
Mw_s = src.matrix_world.copy()
Mw_t = tgt.matrix_world.copy()
Qm_t = qn(Mw_t)
Qm_t_inv = Qm_t.inverted()
Mw_t_inv = Mw_t.inverted()

q_rest_w_s = {sb: qn(Mw_s @ src.data.bones[sb].matrix_local) for _, sb in MAP}
q_rest_w_t = {tb: qn(Mw_t @ tgt.data.bones[tb].matrix_local) for tb, _ in MAP}
q_rest_arm_t = {b.name: qn(b.matrix_local) for b in tgt.data.bones}
rest_local_pel = tgt.data.bones[PELVIS].matrix_local.copy()
p_rest_pel_t = (Mw_t @ tgt.data.bones[PELVIS].matrix_local).to_translation()
p_rest_hips_s = (Mw_s @ src.data.bones['mixamorig:Hips'].matrix_local).to_translation()

src_q, src_hip = {}, {}
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    Mf = src.matrix_world
    for _, sb in MAP:
        src_q[(f, sb)] = qn(Mf @ src.pose.bones[sb].matrix)
    src_hip[f] = (Mf @ src.pose.bones['mixamorig:Hips'].matrix).translation.copy()

old_heavy = bpy.data.actions['Heavy']
old_heavy.name = 'Heavy_old'
act = bpy.data.actions.new('Heavy')
act.use_fake_user = True
ad_t.action = act
try:
    slot = act.slots.new(id_type='OBJECT', name=tgt.name)
    ad_t.action_slot = slot
except Exception as e:
    print("[액션] 슬롯:", e)


def bake_frame(f, z_off):
    q_pose = {}
    for tb, sb in MAP:
        D = src_q[(f, sb)] @ q_rest_w_s[sb].inverted()
        q_pose[tb] = Qm_t_inv @ (D @ q_rest_w_t[tb])
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
    bake_frame(f, 0.0)


def feet_min_z():
    Mf = tgt.matrix_world
    return min((Mf @ tgt.pose.bones[b].matrix).translation.z for b in FEET)


lows0 = []
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    lows0.append(feet_min_z())
zmin = min(lows0)
rest_base = min((tgt.matrix_world @ tgt.data.bones[b].head_local).z for b in FEET)
z_off = rest_base - zmin
print("[접지] 골반 z 오프셋 %+.4f" % z_off)
prev_q = {}
for f in range(F0, F1 + 1):
    bake_frame(f, z_off)

# 소스 제거 + NLA 배선 (poc1 과 동일)
for o in fbx_objs:
    bpy.data.objects.remove(o, do_unlink=True)
for a in mix_actions:
    bpy.data.actions.remove(a, do_unlink=True)
heavy_track = None
for t, m in mute_saved:
    t.mute = m
    for s in t.strips:
        if s.action and s.action.name == 'Heavy_old':
            heavy_track = t
if heavy_track is not None:
    name = heavy_track.name
    ad_t.nla_tracks.remove(heavy_track)
else:
    name = 'Heavy'
tr = ad_t.nla_tracks.new()
tr.name = name
strip = tr.strips.new('Heavy', F0, act)
try:
    strip.action_slot = act.slots[0]
except Exception as e:
    print("[NLA]", e)
bpy.data.actions.remove(old_heavy, do_unlink=True)
ad_t.action = None
for _ in range(3):
    bpy.data.orphans_purge(do_recursive=True)
export_mutes = [(t, t.mute) for t in ad_t.nla_tracks]


def export_glb(path):
    ad_t.action = None
    for t, m in export_mutes:
        t.mute = m
    try:
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB',
                                  export_animation_mode='ACTIONS', export_animations=True)
    except TypeError as e:
        print("[익스포트] 폴백:", e)
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB')


def check_glb(path):
    with open(path, 'rb') as fh:
        blob = fh.read()
    clen, _ = struct.unpack('<II', blob[12:20])
    gj = json.loads(blob[20:20 + clen])
    anims = gj.get('animations', [])
    lines = []
    for an in anims:
        ins = {s['input'] for s in an['samplers']}
        dur = max(gj['accessors'][i]['max'][0] for i in ins)
        lines.append(dict(name=an['name'], channels=len(an['channels']), dur=round(dur, 4)))
    print("[GLB]", os.path.basename(path), "애니 %d개" % len(anims),
          [(l['name'], l['dur']) for l in lines])
    if len(anims) != 7 or 'Heavy' not in [l['name'] for l in lines]:
        raise SystemExit("★GLB 애니 7개/Heavy 조건 실패: " + path)
    return lines


export_glb(OUT_MIX)
report['glb_mix'] = check_glb(OUT_MIX)

# ======================================================================
# 준비: 칼 기하(바인드) + 편의 함수
# ======================================================================
def edit_mode_on():
    for t in ad_t.nla_tracks:
        t.mute = True
    ad_t.action = act
    try:
        ad_t.action_slot = act.slots[0]
    except Exception:
        pass


edit_mode_on()
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
print("[칼] 자루끝~칼끝 %.3fm" % (tip_bind - pommel_bind).length)


def eval_frame(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()


def wq(b):                       # 뼈 월드 회전
    return qn(tgt.matrix_world @ tgt.pose.bones[b].matrix)


def hp(b):                       # 뼈 head 월드 위치
    return (tgt.matrix_world @ tgt.pose.bones[b].matrix).translation.copy()


def sword_pts():                 # (pommel, mid, tip) 월드
    T = (tgt.matrix_world @ tgt.pose.bones[RH].matrix) @ hand_rest_inv
    return T @ pommel_bind, T @ mid_bind, T @ tip_bind


P0 = tgt.data.bones[RC].parent.name          # R Clavicle 의 부모(몸통, 불가침)
LP = tgt.data.bones[LU].parent.name          # L UpperArm 의 부모(L Clavicle)
print("[체인] R Clav 부모=%s / L Up 부모=%s" % (P0, LP))

# ---------- 기준선(리타게팅 원본) 기록 ----------
BASE_BONES = [P0, RC, RU, RF, RH, LC, LU, LF, LH]
ALL24 = [tb for tb, _ in MAP] + ["Bip001 HeadFront", "Bip001 HeadNub"]
base = dict(qw={b: {} for b in ALL24}, basis={b: {} for b in ALL24},
            tip={}, pom={}, mid={}, lw={}, le={}, ls={}, rh={}, feet={}, pel={})
for f in range(F0, F1 + 1):
    eval_frame(f)
    for b in ALL24:
        base['qw'][b][f] = wq(b)
        base['basis'][b][f] = tgt.pose.bones[b].rotation_quaternion.copy()
    pom, mid, tip = sword_pts()
    base['pom'][f], base['mid'][f], base['tip'][f] = pom, mid, tip
    base['lw'][f], base['le'][f], base['ls'][f] = hp(LH), hp(LF), hp(LU)
    base['rh'][f] = hp(RH)
    base['feet'][f] = feet_min_z()
    base['pel'][f] = hp(PELVIS)
tip_z0 = {f: base['tip'][f].z for f in range(F0, F1 + 1)}


def set_world_rots(f, targets, order):
    """targets: {bone: 월드 목표 회전}. order 는 부모->자식. 부모가 targets 에
    없으면 현재 씬(=원본) 값을 쓴다. basis 만 바꾸고 update."""
    qp = {}
    for b in order:
        qp[b] = Qm_t_inv @ targets[b]
        par = tgt.data.bones[b].parent.name
        qp_par = qp.get(par)
        if qp_par is None:
            qp_par = Qm_t_inv @ base['qw'][par][f]
        basis = (q_rest_arm_t[b].inverted() @ q_rest_arm_t[par]
                 @ qp_par.inverted() @ qp[b])
        tgt.pose.bones[b].rotation_quaternion = basis
    bpy.context.view_layer.update()


# ======================================================================
# 1. 칼끝 관통 보정 (R 팔 Newton, 최소 회전 배분)
# ======================================================================
pen = [f for f in range(F0, F1 + 1) if tip_z0[f] < -PEN_MAX]
spans = []
for f in pen:
    if spans and f == spans[-1][1] + 1:
        spans[-1][1] = f
    else:
        spans.append([f, f])
print("[문제1] 관통 프레임 %d개, 스팬 %s" % (len(pen), spans))
report['pen_spans'] = spans

W_J = [(RC, 4.0), (RU, 1.0), (RF, 1.0)]      # (뼈, 최소제곱 가중: 쇄골은 무겁게=적게 회전)
fix1_C = {}                                   # f -> (Cc, Cu, Cf) 월드 보정
fix1_rows = []


def apply_fix1(f, Cc, Cu, Cf):
    tg = {RC: Cc @ base['qw'][RC][f],
          RU: (Cu @ Cc) @ base['qw'][RU][f],
          RF: (Cf @ Cu @ Cc) @ base['qw'][RF][f]}
    set_world_rots(f, tg, [RC, RU, RF])


def rotvec(q):
    q = canon(q)
    a = q.angle
    if a < 1e-9:
        return Vector((0.0, 0.0, 0.0))
    return q.axis * a


def from_rotvec(v):
    a = v.length
    if a < 1e-9:
        return Quaternion()
    return Quaternion(v / a, a)


def smooth_runs(Cmap, nquat, edge_repeat_at=()):
    """Cmap: f -> 보정 쿼터니언 튜플. 연속 구간별 1-2-1 rotvec 커널 1회.
    구간 바깥은 0 패딩(미개입 프레임 쪽으로 자연 감쇠), 단 edge_repeat_at 에
    걸린 끝(타임라인 경계)은 끝값 반복 패딩."""
    runs, fs = [], sorted(Cmap)
    for f in fs:
        if runs and f == runs[-1][-1] + 1:
            runs[-1].append(f)
        else:
            runs.append([f])
    out = {}
    for run in runs:
        for j in range(nquat):
            vs = [rotvec(Cmap[f][j]) for f in run]
            n = len(vs)
            for i, f in enumerate(run):
                if i > 0:
                    vm = vs[i - 1]
                else:
                    vm = vs[0] if run[0] in edge_repeat_at else Vector((0, 0, 0))
                if i < n - 1:
                    vp = vs[i + 1]
                else:
                    vp = vs[-1] if run[-1] in edge_repeat_at else Vector((0, 0, 0))
                out.setdefault(f, []).append(from_rotvec(vm * 0.25 + vs[i] * 0.5 + vp * 0.25))
    return {f: tuple(q) for f, q in out.items()}


def solve_lift(f, warm=None):
    eval_frame(f)
    if warm is None:
        Cc, Cu, Cf = Quaternion(), Quaternion(), Quaternion()
        apply_fix1(f, Cc, Cu, Cf)
        z_id = sword_pts()[2].z
        if abs(z_id - tip_z0[f]) > 2e-4:
            raise SystemExit("f%d identity 재현 실패 %.5f vs %.5f" % (f, z_id, tip_z0[f]))
    else:
        Cc, Cu, Cf = warm[0].copy(), warm[1].copy(), warm[2].copy()
        apply_fix1(f, Cc, Cu, Cf)
    it = 0
    for it in range(1, 31):
        pom, mid, tip = sword_pts()
        dz = Z_TGT - tip.z
        if abs(dz) < 0.0015:
            break
        axs, hs = [], []
        for b, w in W_J:
            r = tip - hp(b)
            h = math.hypot(r.x, r.y)
            axs.append(Vector((r.y, -r.x, 0.0)).normalized() if h > 0.05 else None)
            hs.append(h)
        denom = sum(h * h / w for (b, w), h, a in zip(W_J, hs, axs) if a is not None)
        if denom < 1e-6:
            raise SystemExit("f%d lever 소실" % f)
        lam = dz / denom
        dths = []
        for (b, w), h, a in zip(W_J, hs, axs):
            dth = 0.0 if a is None else max(-0.15, min(0.15, lam * h / w))
            dths.append(dth)
        Cc = canon(Quaternion(axs[0], dths[0]) @ Cc) if axs[0] else Cc
        Cu = canon(Quaternion(axs[1], dths[1]) @ Cu) if axs[1] else Cu
        Cf = canon(Quaternion(axs[2], dths[2]) @ Cf) if axs[2] else Cf
        apply_fix1(f, Cc, Cu, Cf)
    return Cc, Cu, Cf, it


iters_map = {}
for f in pen:
    warm = fix1_C.get(f - 1)          # 이전 관통 프레임 해에서 워밍업(시간 일관성)
    Cc, Cu, Cf, it = solve_lift(f, warm)
    fix1_C[f] = (Cc, Cu, Cf)
    iters_map[f] = it

# ---------- 램프 (스팬 가장자리 보정을 바깥 3프레임에 코사인 감쇠) ----------
ID = Quaternion()
for fa, fb in spans:
    for k, w in enumerate(RAMP_W, start=1):
        for f, edge in ((fa - k, fa), (fb + k, fb)):
            if f < F0 or f > F1 or f in fix1_C:
                continue
            Cc, Cu, Cf = fix1_C[edge]
            fix1_C[f] = (ID.slerp(Cc, w), ID.slerp(Cu, w), ID.slerp(Cf, w))

# ---------- 보정장 시간축 평활(축 흔들림 제거) + 관통 프레임 z 재정밀화 ----------
fix1_C = smooth_runs(fix1_C, 3)
for f in pen:
    Cc, Cu, Cf, it = solve_lift(f, fix1_C[f])
    fix1_C[f] = (Cc, Cu, Cf)
    iters_map[f] = iters_map[f] + it

# ---------- 키 굽기 + 기록 ----------
pen_set = set(pen)
for f in sorted(fix1_C):
    eval_frame(f)
    apply_fix1(f, *fix1_C[f])
    for b in (RC, RU, RF):
        tgt.pose.bones[b].keyframe_insert('rotation_quaternion', frame=f)
    z1 = sword_pts()[2].z
    Cc, Cu, Cf = fix1_C[f]
    fix1_rows.append(dict(f=f, t=round((f - F0) / 30.0, 3),
                          kind="pen" if f in pen_set else "ramp",
                          iters=iters_map.get(f, 0),
                          z0=round(tip_z0[f], 4), z1=round(z1, 4),
                          deg_clav=round(qdeg(Cc), 2),
                          deg_up=round(qdeg(Cu), 2),
                          deg_fore=round(qdeg(Cf), 2),
                          rhand_cm=round((hp(RH) - base['rh'][f]).length * 100, 1)))
report['fix1'] = fix1_rows

# ======================================================================
# 2. 왼손 재파지 (2본 IK, 시드=원본, 최소회전)
# ======================================================================
# 원본 정상그립 구간에서 자루축상 왼손 위치 범위 [s_lo, s_hi]
good = [f for f in range(F0, F1 + 1)
        if ((base['lw'][f] - base['pom'][f]).cross(base['tip'][f] - base['pom'][f])).length
        / (base['tip'][f] - base['pom'][f]).length <= 0.11]
s_vals = []
for f in good:
    ax = (base['tip'][f] - base['pom'][f]).normalized()
    s_vals.append((base['lw'][f] - base['pom'][f]).dot(ax))
s_lo, s_hi = min(s_vals), max(s_vals)
print("[문제2] 원본 정상그립 %d프레임, 자루축 s=[%.3f, %.3f]" % (len(good), s_lo, s_hi))
report['fix2_s_range'] = [round(s_lo, 4), round(s_hi, 4), len(good)]

def ik_2bone(s0, e0, w0, pstar):
    """시드(e0,w0에 담긴 현재 자세)에서 최소회전 스윙+원본 팔꿈치 평면 굴신만으로
    손목을 pstar 로. 반환 (Cu, Cf, clamped) - 월드 사전회전."""
    A, B = (e0 - s0).length, (w0 - e0).length
    tlen = (pstar - s0).length
    clamped = False
    if tlen > 0.999 * (A + B):
        pstar = s0 + (pstar - s0).normalized() * 0.999 * (A + B)
        tlen = 0.999 * (A + B)
        clamped = True
    Cu, Cf = Quaternion(), Quaternion()
    e, w = e0.copy(), w0.copy()
    for _ in range(5):
        R1 = (w - s0).rotation_difference(pstar - s0)
        Cu, Cf = canon(R1 @ Cu), canon(R1 @ Cf)
        e = s0 + R1 @ (e - s0)
        w = s0 + R1 @ (w - s0)
        if (w - pstar).length < 0.001:
            break
        n = (e - s0).cross(w - e)
        if n.length < 1e-6:
            n = (e - s0).cross(Vector((0, 0, 1)))
            if n.length < 1e-6:
                n = (e - s0).cross(Vector((0, 1, 0)))
        n.normalize()
        cosb1 = max(-1.0, min(1.0, (A * A + B * B - tlen * tlen) / (2 * A * B)))
        b1 = math.acos(cosb1)
        v1, v2 = (s0 - e).normalized(), (w - e).normalized()
        b0 = math.acos(max(-1.0, min(1.0, v1.dot(v2))))
        db = b1 - b0
        cand = []
        for sgn in (1.0, -1.0):
            Qf = Quaternion(n, sgn * db)
            w_try = e + Qf @ (w - e)
            cand.append((abs((w_try - s0).length - tlen), Qf, w_try))
        cand.sort(key=lambda c: c[0])
        _, Qf, w = cand[0]
        Cf = canon(Qf @ Cf)
    return Cu, Cf, clamped


# ---------- 1차: 프레임별 원시 IK 보정 계산(적용은 아직) ----------
fix2_rows = []
fix2_meta = {}                                # f -> dict(row, pstar, clamped)
fix2_C = {}                                   # f -> (Cu, Cf)  (이후 평활·정밀화 거침)
for f in range(F0, F1 + 1):
    eval_frame(f)                             # fix1 키가 반영된 상태
    pom, mid, tip = sword_pts()
    ax = (tip - pom).normalized()
    p = hp(LH)
    s_raw = (p - pom).dot(ax)
    qproj = pom + ax * s_raw
    d_post1 = (p - qproj).length
    d0 = ((base['lw'][f] - base['pom'][f]).cross(base['tip'][f] - base['pom'][f])).length \
        / (base['tip'][f] - base['pom'][f]).length
    row = dict(f=f, t=round((f - F0) / 30.0, 3), d_orig=round(d0, 4),
               d_post1=round(d_post1, 4), ik=False)
    fix2_rows.append(row)
    if d_post1 <= D_ON:                       # 불가침(이탈 0.10 이하)
        row['d_fix'] = round(d_post1, 4)
        row['lw_cm'] = 0.0
        continue
    s_cl = max(s_lo, min(s_hi, s_raw))
    pstar = pom + ax * s_cl + (p - qproj).normalized() * D_ON
    Cu, Cf, clamped = ik_2bone(hp(LU), hp(LF), p, pstar)
    fix2_C[f] = (Cu, Cf)
    fix2_meta[f] = dict(row=row, pstar=pstar, clamped=clamped)

# ---------- 2차: 보정장 평활(1-2-1, 타임라인 양끝은 끝값 반복) ----------
fix2_C = smooth_runs(fix2_C, 2, edge_repeat_at={F0, F1})

# ---------- 3차: 적용 + 필요시 소증분 재정밀화 + 키 ----------
for f in sorted(fix2_C):
    meta = fix2_meta[f]
    row, pstar = meta['row'], meta['pstar']
    eval_frame(f)
    Cu, Cf = fix2_C[f]
    set_world_rots(f, {LU: Cu @ base['qw'][LU][f], LF: Cf @ base['qw'][LF][f]}, [LU, LF])
    wr = hp(LH)
    if (wr - pstar).length > 0.015:           # 평활로 벌어졌으면 현재 자세에서 소증분
        dCu, dCf, _ = ik_2bone(hp(LU), hp(LF), wr, pstar)
        if qdeg(dCf) <= 12.0 and qdeg(dCu) <= 12.0:
            Cu, Cf = canon(dCu @ Cu), canon(dCf @ Cf)
            fix2_C[f] = (Cu, Cf)
            set_world_rots(f, {LU: Cu @ base['qw'][LU][f], LF: Cf @ base['qw'][LF][f]}, [LU, LF])
            wr = hp(LH)
    err = (wr - pstar).length
    pom2, _, tip2 = sword_pts()
    d_fix = ((wr - pom2).cross((tip2 - pom2).normalized())).length
    for b in (LU, LF):
        tgt.pose.bones[b].keyframe_insert('rotation_quaternion', frame=f)
    row.update(ik=True, clamped=meta['clamped'], d_fix=round(d_fix, 4),
               lw_cm=round((wr - base['lw'][f]).length * 100, 1),
               cu_deg=round(qdeg(Cu), 2), cf_deg=round(qdeg(Cf), 2),
               ik_err=round(err, 4))

# ---------- 왼팔뚝 45°/프레임 가드 ----------
def lfore_steps():
    qs = {}
    for f in range(F0, F1 + 1):
        eval_frame(f)
        qs[f] = wq(LF)
    steps = {}
    for f in range(F0 + 1, F1 + 1):
        steps[f] = sdeg(qs[f - 1], qs[f])
    return steps


reverted = []
for _pass in range(12):
    steps = lfore_steps()
    bad = [f for f, s in steps.items() if s > STEP_LIMIT]
    if not bad:
        break
    fbad = bad[0]
    victim = fbad if fbad in fix2_C else (fbad - 1 if (fbad - 1) in fix2_C else None)
    if victim is None:
        print("  [가드] f%d 스텝 %.1f° 인데 IK 프레임 아님(원본 유래)" % (fbad, steps[fbad]))
        break
    del fix2_C[victim]
    for b in (LU, LF):
        tgt.pose.bones[b].rotation_quaternion = base['basis'][b][victim]
        tgt.pose.bones[b].keyframe_insert('rotation_quaternion', frame=victim)
    for row in fix2_rows:
        if row['f'] == victim:
            row.update(ik=False, reverted=True, d_fix=row['d_post1'], lw_cm=0.0)
    reverted.append(victim)
    print("  [가드] f%d IK 해제(스텝 %.1f°)" % (victim, steps[fbad]))
steps_after = lfore_steps()
report['fix2'] = fix2_rows
report['fix2_reverted'] = reverted
report['fix2_max_step_after'] = round(max(steps_after.values()), 2)
base_steps = {f: sdeg(base['qw'][LF][f - 1], base['qw'][LF][f]) for f in range(F0 + 1, F1 + 1)}
report['fix2_max_step_orig'] = round(max(base_steps.values()), 2)
report['fix2_n_ik'] = sum(1 for r in fix2_rows if r['ik'])

# ======================================================================
# 3. 최종 검증 + 서명 연속화 + 기록
# ======================================================================
EDITED = [RC, RU, RF, LU, LF]
final_rows = []
final_basis = {b: {} for b in EDITED}
final_qw = {b: {} for b in (RF, LF)}
worst = dict(tip=(9, None), step=(0, None, None))
prev_all = None
for f in range(F0, F1 + 1):
    eval_frame(f)
    pom, mid, tip = sword_pts()
    blade_min = min(pom.z, mid.z, tip.z)
    for b in EDITED:
        final_basis[b][f] = tgt.pose.bones[b].rotation_quaternion.copy()
    dev = {b: round(sdeg(base['qw'][b][f], wq(b)), 2) for b in [RC, RU, RF, RH, LU, LF, LH]}
    cur_all = {b: wq(b) for b in ALL24}
    final_qw[RF][f] = cur_all[RF]
    final_qw[LF][f] = cur_all[LF]
    if prev_all:
        for b in ALL24:
            st = sdeg(prev_all[b], cur_all[b])
            if st > worst['step'][0]:
                worst['step'] = (st, b, f)
    prev_all = cur_all
    if tip.z < worst['tip'][0]:
        worst['tip'] = (tip.z, f)
    dfeet = abs(feet_min_z() - base['feet'][f])
    dpel = (hp(PELVIS) - base['pel'][f]).length
    final_rows.append(dict(f=f, tip_z0=round(tip_z0[f], 4), tip_z=round(tip.z, 4),
                           blade_min=round(blade_min, 4), dev=dev,
                           rh_cm=round((hp(RH) - base['rh'][f]).length * 100, 1),
                           lh_cm=round((hp(LH) - base['lw'][f]).length * 100, 1),
                           feet_drift=round(dfeet, 6), pel_drift=round(dpel, 6)))

report['final'] = final_rows
report['step_profiles'] = {
    'rf_orig': [round(sdeg(base['qw'][RF][f - 1], base['qw'][RF][f]), 1) for f in range(F0 + 1, F1 + 1)],
    'rf_final': [round(sdeg(final_qw[RF][f - 1], final_qw[RF][f]), 1) for f in range(F0 + 1, F1 + 1)],
    'lf_orig': [round(sdeg(base['qw'][LF][f - 1], base['qw'][LF][f]), 1) for f in range(F0 + 1, F1 + 1)],
    'lf_final': [round(sdeg(final_qw[LF][f - 1], final_qw[LF][f]), 1) for f in range(F0 + 1, F1 + 1)],
}
report['final_tip_min'] = dict(z=round(worst['tip'][0], 4), f=worst['tip'][1])
report['final_max_step'] = dict(deg=round(worst['step'][0], 2), bone=worst['step'][1], f=worst['step'][2])
viol = [r['f'] for r in final_rows if r['tip_z'] < -PEN_MAX or r['blade_min'] < -PEN_MAX]
report['final_violations'] = viol
print("[검증] 칼끝 최저 %.4f @f%s / 위반 %s / 최대 프레임간 스텝 %.1f° (%s f%s)"
      % (worst['tip'][0], worst['tip'][1], viol, worst['step'][0], worst['step'][1], worst['step'][2]))
maxfeet = max(r['feet_drift'] for r in final_rows)
maxpel = max(r['pel_drift'] for r in final_rows)
print("[검증] 발 드리프트 최대 %.5f / 골반 드리프트 최대 %.5f (0 이어야 정상)" % (maxfeet, maxpel))
if maxfeet > 0.002 or maxpel > 0.002:
    raise SystemExit("★골반/발이 움직였다 - 보정이 하체를 오염시킴")
if viol:
    raise SystemExit("★관통 위반 잔존: %s" % viol)

# ---------- 편집 뼈 5개: 쿼터니언 부호 연속화 후 전 프레임 재기록 ----------
for b in EDITED:
    prev = None
    for f in range(F0, F1 + 1):
        q = final_basis[b][f]
        if prev is not None and q.dot(prev) < 0.0:
            q.negate()
        prev = q
        tgt.pose.bones[b].rotation_quaternion = q
        tgt.pose.bones[b].keyframe_insert('rotation_quaternion', frame=f)

export_glb(OUT_FIX)
report['glb_fix'] = check_glb(OUT_FIX)
with open(os.path.join(POC, 'fix_report.json'), 'w') as fh:
    json.dump(report, fh, indent=1, ensure_ascii=False)
print("FIX_DONE", OUT_FIX)
