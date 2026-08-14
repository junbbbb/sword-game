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
from mathutils import Matrix, Vector


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


made = {}
summary = {}
for name in CLIPS:
    old, source, rows = clip_samples(name)
    print("\n[%s] 기존 %.1f~%.1f / Soldier %.1f~%.1f / 출력 %d장" %
          (name, old.frame_range[0], old.frame_range[1],
           source.frame_range[0], source.frame_range[1], len(rows)))

    lows = []
    for _, basis, rots, pw in rows:
        build_pose(basis, rots, pw, 0.0)
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
        pose = build_pose(basis, rots, pw, shift)
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
