# -*- coding: utf-8 -*-
"""Meshy 고블린(glb 3개)을 게임용 단일 glb 로 합친다. -> web/goblin.glb

s13_basic.py 의 고블린판. 함정 처리는 s13 / s11 과 같고 여기에
'삼각형 감축(동시 10~20마리)' 과 '베이스컬러 외 맵 제거' 를 더했다.

받은 것
  incoming/meshy5/Meshy_AI_biped/ 의 Walking / Running / Attack (각 29.6MB)
  세 파일이 **각각 메시를 통째로** 들고 있다. 뼈(24본)·메시(3976정점 5466삼각형)·
  재질(4096x4096 PNG 29.3MB 1장)이 같으므로 메시는 하나만 두고 액션만 모은다.

glb 직접 파싱(probe_glbscale.py) 결과
  파일당 애니메이션 정확히 1개. 숨은 clip0 없음.
  scale 채널 1.0000~1.0000 = **뿌리 스케일 오염 없음**.

만드는 액션: Idle / Walk / Run / Attack  (게임이 쓰는 이름 그대로)
  Idle 만 Meshy 가 안 줬다. 걷기에서 다리가 모인 프레임을 골라 숨쉬기 루프를 만든다.
  ★레스트(T포즈)를 Idle 로 쓰면 안 된다. 레스트는 최저z 가 정확히 0인데 걷기·
    달리기는 음수에서 논다. 레스트를 쓰면 걷기 시작 순간 캐릭터가 툭 떨어진다.

실행: blender -b -P blender/s16_goblin.py
"""
import bpy
import os
import math
from mathutils import Matrix

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming/meshy5/Meshy_AI_biped")
WEB = os.path.join(ROOT, "web")
BASE = "Meshy_AI_biped_Animation_%s_withSkin.glb"

# ---- 손잡이 ----
# TEX_SIZE  : 텍스처 한 변 픽셀(0 이면 원본 유지). ★익스포터에 해상도 옵션이
#             없어서 image.scale() 로 데이터블록을 직접 줄인다.
# TEX_FORMAT: AUTO(PNG 유지) / JPEG / WEBP.
#             이 텍스처는 PNG **colortype 2**(알파 채널 자체가 없음)이고 재질도
#             alphaMode 를 안 쓴다. JPEG 로 바꿔도 잃는 정보가 없다.
# TRI_TARGET: 목표 삼각형 수. 게임에 동시 10~20마리가 나오므로 낮게 잡는다.
# IDLE_BASE_F: Idle 바탕으로 쓸 Walk 프레임. 0 이면 아래 규칙으로 자동 선정.
TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_FORMAT = os.environ.get("TEX_FORMAT", "JPEG").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))
TRI_TARGET = int(os.environ.get("TRI_TARGET", "2000"))
IDLE_BASE_F = int(os.environ.get("IDLE_BASE_F", "0"))
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "goblin.glb")

# 게임 기준값(보고용 계산에만 쓴다)
GAME_TARGET_H = float(os.environ.get("GAME_TARGET_H", "1.2"))
PLAYER_H = 1.75          # main.js CHAR_CFG.slayer.h
SWORD_LO, SWORD_HI = 1.20, 2.48   # enemy.js 주석의 칼끝 월드 Y 실측 구간

# Meshy 이름 -> 우리 규칙. 순서 중요(긴 것부터 매칭)
# ★게임 코드(main.js)와 포즈 시스템이 "r hand", "l thigh" 같은 **부분 문자열**로
#   뼈를 찾는다. Meshy 이름(RightHand, LeftUpLeg)은 안 잡힌다.
# ★척추: Spine/Spine01/Spine02 중 위 두 개는 Chest/Chest2 로. 셋 다 'spine' 을
#   넣으면 pb("spine") 이 엉뚱한 걸 잡는다.
RENAME = [
    ("LeftToeBase", "Bip001 L Toe0"), ("RightToeBase", "Bip001 R Toe0"),
    ("LeftUpLeg", "Bip001 L Thigh"), ("RightUpLeg", "Bip001 R Thigh"),
    ("LeftForeArm", "Bip001 L Forearm"), ("RightForeArm", "Bip001 R Forearm"),
    ("LeftShoulder", "Bip001 L Clavicle"), ("RightShoulder", "Bip001 R Clavicle"),
    ("LeftHand", "Bip001 L Hand"), ("RightHand", "Bip001 R Hand"),
    ("LeftFoot", "Bip001 L Foot"), ("RightFoot", "Bip001 R Foot"),
    ("LeftLeg", "Bip001 L Calf"), ("RightLeg", "Bip001 R Calf"),
    ("LeftArm", "Bip001 L UpperArm"), ("RightArm", "Bip001 R UpperArm"),
    ("Spine02", "Bip001 Chest2"), ("Spine01", "Bip001 Chest"),
    ("Spine", "Bip001 Spine"),
    ("Hips", "Bip001 Pelvis"),
    ("head_end", "Bip001 HeadNub"), ("headfront", "Bip001 HeadFront"),
    ("Head", "Bip001 Head"), ("neck", "Bip001 Neck"),
]
NAMEMAP = dict(RENAME)
PELVIS = "Bip001 Pelvis"

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene

# ---- 0) fps 고정 ----
# ★FBX 임포터는 씬 fps 를 자기 값으로 덮어쓴다. 여기선 glb 만 다루지만
#   24fps 로 읽고 30fps 로 내보내면 걷기가 25% 빨라지므로 먼저 못박고 확인한다.
print("빈 씬 기본 fps =", sc.render.fps)
sc.render.fps = 30
sc.render.fps_base = 1.0
print("fps 를 30 으로 고정(Meshy 키 간격 0.0333초 = 정확히 30fps)")


def imp(tag):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, BASE % tag))
    got = [o for o in sc.objects if o.name not in before]
    # ★임포터가 뼈를 그리려고 만드는 반지름 1 짜리 Icosphere.
    #   glb 안에는 없는 물건이고 'glTF_not_exported' 컬렉션에 들어간다.
    #   main.js 는 전 메시로 박스를 재므로 이게 그대로 키에 들어가 몸이
    #   쪼그라들고 발이 뜬다. 즉시 지운다.
    for o in list(got):
        if any(c.name == "glTF_not_exported" for c in o.users_collection) \
                or o.name.startswith("Icosphere"):
            print("  임포터 부산물 제거(키 계산 오염원):", o.name)
            bpy.data.objects.remove(o, do_unlink=True)
            got.remove(o)
    return got


# ---- 1) Walking 을 기준으로 삼는다(메시 제공 + Walk) ----
print("=" * 72)
print("[1] 기준 파일 임포트")
objs = imp("Walking")
print("  glTF 임포트 후 fps =", sc.render.fps)
arm = next(o for o in objs if o.type == "ARMATURE")
mesh = next(o for o in objs if o.type == "MESH")
print("기준 리그:", arm.name, "본", len(arm.data.bones),
      "/ 메시", mesh.name, len(mesh.data.polygons), "면",
      len(mesh.data.vertices), "정점")

acts = {}
pre0 = [a for a in bpy.data.actions]
print("  [Walking] 파일이 들고 온 액션 %d개 %s"
      % (len(pre0), [a.name for a in pre0]))
if arm.animation_data and arm.animation_data.action:
    acts["Walk"] = arm.animation_data.action
    print("    아마추어에 붙은 것 = %s (%.1f~%.1f 프레임)"
          % (acts["Walk"].name, acts["Walk"].frame_range[0],
             acts["Walk"].frame_range[1]))

# ---- 2) 나머지는 액션만 가져오고 오브젝트는 버린다 ----
# ★액션 이름 충돌 함정: 임포트한 소스 액션이 "Run" 같은 우리 이름을 먼저 차지하면
#   우리 액션이 조용히 Run.001 이 되고 정리 루프가 그걸 지운다.
#   들어오자마자 SRC_ 접두사로 밀어 원천 차단한다.
# ★한 파일에 애니메이션이 여러 개일 수 있다(궁수 파일에 rigify_clip 75프레임 +
#   clip0 2프레임 정지가 같이 있었다). 그래서 파일당 새 액션 수를 찍는다.
print("=" * 72)
print("[2] 나머지 파일에서 액션만 수확")
for tag, name in (("Running", "Run"), ("Attack", "Attack")):
    pre = set(a.name for a in bpy.data.actions)
    got = imp(tag)
    fresh = [a for a in bpy.data.actions if a.name not in pre]
    for a in fresh:
        a.name = "SRC_" + a.name
    a2 = next(o for o in got if o.type == "ARMATURE")
    act = a2.animation_data.action if a2.animation_data else None
    print("  [%s] 새 액션 %d개 %s / 아마추어에 붙은 것 = %s (%.1f~%.1f 프레임)"
          % (tag, len(fresh), [a.name for a in fresh],
             act.name if act else None,
             act.frame_range[0] if act else -1,
             act.frame_range[1] if act else -1))
    if len(fresh) > 1:
        longest = max(fresh, key=lambda a: a.frame_range[1] - a.frame_range[0])
        print("    ★숨은 클립 발견. 최장 클립 = %s" % longest.name)
        act = longest
    act.use_fake_user = True
    acts[name] = act
    for o in got:
        bpy.data.objects.remove(o, do_unlink=True)
print("모은 액션:", list(acts))

# ---- 3) 뼈 이름 변경 ----
print("=" * 72)
print("[3] 뼈 이름 Bip001 규칙으로")
n = 0
for old, new in RENAME:
    b = arm.data.bones.get(old)
    if b:
        b.name = new
        n += 1
print("뼈 이름 변경 %d개 / 전체 %d개" % (n, len(arm.data.bones)))
print("  ->", [b.name for b in arm.data.bones])
if n != len(RENAME):
    raise SystemExit("★뼈 이름을 다 못 바꿨다. RENAME 표를 리그와 대조해라")


# ★★가장 중요한 함정
# Blender 는 뼈 이름을 바꿀 때 **그 아마추어에 현재 붙어 있는 액션**의 데이터
# 경로만 따라 고친다. Run/Attack 은 **다른 아마추어**에서 가져온 뒤 그 아마추어를
# 지웠으므로 fcurve 경로가 아직 pose.bones["RightHand"] 를 가리킨다. 그대로
# 내보내면 그 클립을 재생할 때 아무 뼈도 안 잡혀 **T 포즈**가 된다.
# (증상: 걷기는 되는데 Shift 달리기 누르면 T 포즈. 탱커에서 실제로 겪었다)
def fcs_of(act):
    """Blender 4.4+ 는 액션이 레이어/스트립/채널백 구조라 act.fcurves 가 비어 있다."""
    fcs = []
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    fcs.extend(cb.fcurves)
    except Exception:
        pass
    if not fcs:
        fcs = list(act.fcurves)
    return fcs


def fix_paths(act):
    n = 0
    for fc in fcs_of(act):
        dp = fc.data_path
        if '"' not in dp:
            continue
        old_b = dp.split('"')[1]
        new_b = NAMEMAP.get(old_b)
        if new_b and new_b != old_b:
            fc.data_path = dp.replace('"%s"' % old_b, '"%s"' % new_b, 1)
            n += 1
    return n


print("=" * 72)
print("[4] fcurve 경로 수리(T포즈 함정)")
for nm in ("Walk", "Run", "Attack"):
    act = acts[nm]
    act.name = nm
    act.use_fake_user = True
    print("  액션 %-8s fcurve %3d개 중 경로 %3d개 수정"
          % (nm, len(fcs_of(act)), fix_paths(act)))
# 기준 액션(Walk)만 0 개가 정상. Run/Attack 이 0 이면 T 포즈 함정에 빠진 것이다.
for nm in ("Run", "Attack"):
    if fix_paths(acts[nm]) != 0:
        raise SystemExit("★%s: fix_paths 재실행에서 또 고쳐졌다 = 1차 실패" % nm)


# ---- 5) 진단 도구 ----
def use(act):
    """액션을 붙인다. ★Blender 4.4+ 는 슬롯이 없으면 조용히 아무 일도 안 한다."""
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def low_z():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    mw = mesh.matrix_world
    z = min((mw @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    return z


def scale_ranges(act):
    rng = {}
    for fc in fcs_of(act):
        if not fc.data_path.endswith(".scale") or '"' not in fc.data_path:
            continue
        b = fc.data_path.split('"')[1]
        vs = [k.co.y for k in fc.keyframe_points]
        if not vs:
            continue
        lo, hi = rng.get(b, (9e9, -9e9))
        rng[b] = (min(lo, min(vs)), max(hi, max(vs)))
    return rng


# ---- 5.5) ★★Meshy 리타깃 잔재 감시: 뿌리 뼈에 박힌 스케일 ----
# 궁수 Walking_Woman 은 Bip001 Pelvis 에 스케일 1.1765 가 상수로 박혀 걷기만
# 하면 캐릭터가 17.65% 부풀었다. 이 리그도 뼈 24개가 전부 골반 하위다.
# ★보정은 '스케일 1.0 + 골반 translation 을 같은 배율로 축소' 여야 한다.
#   스케일만 내리면 다리가 짧아진 만큼 발이 뜬다(s11 4.5단계 유도식).
def deflate_root_scale(act):
    sfc = [fc for fc in fcs_of(act)
           if fc.data_path == 'pose.bones["%s"].scale' % PELVIS]
    vals = [k.co.y for fc in sfc for k in fc.keyframe_points]
    if not vals:
        print("  골반 스케일 채널 없음 = 손댈 것 없음")
        return 1.0
    k = sum(vals) / len(vals)
    if max(vals) - min(vals) > 1e-4:
        raise SystemExit("골반 스케일이 상수가 아니다(%.4f~%.4f)." % (min(vals), max(vals)))
    if abs(k - 1.0) < 1e-4:
        print("  골반 스케일 이미 1.0 = 손댈 것 없음")
        return 1.0
    s = 1.0 / k
    bone = arm.data.bones[PELVIS]
    c = (bone.matrix_local.to_3x3().inverted()
         @ bone.matrix_local.translation) * (s - 1.0)
    for fc in sfc:
        for kp in fc.keyframe_points:
            kp.co.y = kp.handle_left.y = kp.handle_right.y = 1.0
        fc.update()
    lfc = [fc for fc in fcs_of(act)
           if fc.data_path == 'pose.bones["%s"].location' % PELVIS]
    if not lfc:
        raise SystemExit("골반 location fcurve 가 없다. 보정 대상이 없어 발이 뜬다.")
    for fc in lfc:
        off = c[fc.array_index]
        for kp in fc.keyframe_points:
            kp.co.y = kp.co.y * s + off
            kp.handle_left.y = kp.handle_left.y * s + off
            kp.handle_right.y = kp.handle_right.y * s + off
        fc.update()
    print("  골반 스케일 %.4f -> 1.0 / 골반 위치 x%.4f" % (k, s))
    return k


print("=" * 72)
print("[5] 스케일 오염 점검(굽기 전)")
print("아마추어 원점", tuple(round(x, 5) for x in arm.matrix_world.translation),
      "스케일", tuple(round(x, 5) for x in arm.matrix_world.to_scale()))
for nm in sorted(acts):
    r = scale_ranges(acts[nm])
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-8s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))
    if bad:
        if set(bad) == {PELVIS}:
            deflate_root_scale(acts[nm])
        else:
            raise SystemExit("골반이 아닌 뼈에 스케일이 박혔다: %s" % list(bad))

# ---- 6) 삼각형 감축 ----
# 게임에 동시 10~20마리가 나온다. 스킨드 메시를 그만큼 돌리므로 낮을수록 좋다.
# ★Decimate 를 Armature 보다 **앞**으로 옮겨 적용한다. 뒤에 두고 적용하면
#   "Applied modifier was not first" 경고가 뜬다(결과는 같지만 깨끗하게 간다).
print("=" * 72)
print("[6] 삼각형 감축")
TRI0 = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print("  감축 전 삼각형 %d / 정점 %d" % (TRI0, len(mesh.data.vertices)))
if TRI_TARGET and TRI0 > TRI_TARGET:
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    md = mesh.modifiers.new("Dec", "DECIMATE")
    md.decimate_type = "COLLAPSE"
    md.ratio = TRI_TARGET / float(TRI0)
    md.use_collapse_triangulate = True
    try:
        bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)
    except Exception as e:
        print("  (modifier_move_to_index 실패, 그대로 적용)", e)
    bpy.ops.object.modifier_apply(modifier=md.name)
    TRI1 = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
    print("  ratio %.4f 적용 -> 삼각형 %d / 정점 %d  (%.1f%% 감축)"
          % (md.ratio, TRI1, len(mesh.data.vertices),
             100.0 * (1 - TRI1 / float(TRI0))))
    print("  모디파이어 남은 것:", [m.name for m in mesh.modifiers])
else:
    TRI1 = TRI0
    print("  감축 안 함(TRI_TARGET=%s)" % TRI_TARGET)

# ---- 7) 걷기 프레임별 발·팔 표 (Idle 바탕 프레임 선정 근거) ----
# 캐릭터는 -Y 를 본다(headfront 가 코 쪽이고 -Y 에 있다). 발.y 가 작을수록 앞.
# 팔 흔들림은 '레스트에서 손이 골반보다 얼마나 뒤(+y)에 있는가' 를 기준선으로 잰다.
print("=" * 72)
print("[7] Idle 바탕 프레임 찾기")
use(acts["Walk"])
WF0 = int(acts["Walk"].frame_range[0])
WF1 = int(acts["Walk"].frame_range[1])


def wp(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return (arm.matrix_world @ b.matrix).translation.copy()
    return None


arm.data.pose_position = "REST"
bpy.context.view_layer.update()
BASE_LDY = (wp("l hand") - wp("pelvis")).y
BASE_RDY = (wp("r hand") - wp("pelvis")).y
REST_LOW = low_z()
REST_LTOE = wp("l toe").z
REST_RTOE = wp("r toe").z
zs_rest = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H_REST = max(zs_rest) - min(zs_rest)
arm.data.pose_position = "POSE"
print("[레스트(바인드 T포즈)] 키 %.4f / 최저z %+.4f / 발끝z 왼 %+.4f 오른 %+.4f"
      % (H_REST, REST_LOW, REST_LTOE, REST_RTOE))
print("                       손-골반 기준선 dy 왼 %+.4f 오른 %+.4f"
      % (BASE_LDY, BASE_RDY))
print("[걷기 프레임별]  발전후간격 = |왼발.y - 오른발.y| (작을수록 다리 모임)")
print("  %4s %10s %8s %8s %10s %9s" %
      ("f", "발전후간격", "L발끝z", "R발끝z", "팔중립편차", "메시최저z"))
cand = []
for f in range(WF0, WF1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    p = wp("pelvis")
    lf, rf = wp("l foot"), wp("r foot")
    lt, rt = wp("l toe"), wp("r toe")
    lh, rh = wp("l hand"), wp("r hand")
    gap = abs(lf.y - rf.y)
    swing = abs((lh - p).y - BASE_LDY) + abs((rh - p).y - BASE_RDY)
    lz = low_z()
    cand.append((f, gap, swing, lt.z, rt.z, lz))
    print("  %4d %10.4f %8.4f %8.4f %10.4f %9.4f"
          % (f, gap, lt.z, rt.z, swing, lz))

# 자동 선정 규칙: 두 발끝이 다 땅 근처(레스트 발끝 + 키의 5% 이내)인 프레임 중
# '발 전후간격 + 팔 중립편차' 가 최소인 프레임. 걷기 사이클에서 양팔은 180도
# 반대 위상이라 '양팔 동시 완전 중립' 프레임은 존재하지 않으므로 합으로 잰다.
THR = max(REST_LTOE, REST_RTOE) + 0.05 * H_REST
ok = [c for c in cand if max(c[3], c[4]) <= THR] or cand
ok = sorted(ok, key=lambda c: c[1] + c[2])
print("  접지 판정 문턱 발끝z <= %.4f / 통과 %d프레임" % (THR, len(ok)))
print("  후보 상위 3: " + ", ".join(
    "f%d(간격%.4f 팔%.4f)" % (c[0], c[1], c[2]) for c in ok[:3]))
if not IDLE_BASE_F:
    IDLE_BASE_F = ok[0][0]
sc.frame_set(IDLE_BASE_F)
bpy.context.view_layer.update()
print("Idle 바탕 = Walk f%d / 메시 최저z %+.4f  (레스트 최저z %+.4f)"
      % (IDLE_BASE_F, low_z(), REST_LOW))
BASEP = {b.name: b.matrix_basis.copy() for b in arm.pose.bones}


def restore():
    for b in arm.pose.bones:
        b.rotation_mode = "QUATERNION"
        b.matrix_basis = BASEP[b.name].copy()
    bpy.context.view_layer.update()


def key_all(f):
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("location", frame=f)


def new_action(name):
    arm.animation_data_clear()
    arm.animation_data_create()
    a = bpy.data.actions.new(name)
    a.use_fake_user = True          # ★안 켜면 export 에서 조용히 빠진다
    arm.animation_data.action = a
    try:
        # ★Blender 4.4+ 는 슬롯이 없으면 액션이 조용히 아무 일도 안 한다.
        slot = a.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = slot
    except Exception:
        pass
    return a


# ---- 8) Idle: 숨쉬기 루프 50프레임 ----
print("=" * 72)
print("[8] Idle 생성")
idle = new_action("Idle")
SPINE = arm.pose.bones.get("Bip001 Spine")
for f, amp in ((1, 0.0), (25, 1.0), (50, 0.0)):
    restore()
    if SPINE:
        # 아주 작은 숨쉬기(가슴 2도). 크면 흔들거린다.
        SPINE.rotation_quaternion = (
            SPINE.rotation_quaternion @ Matrix.Rotation(
                math.radians(2.0 * amp), 4, "X").to_quaternion())
    bpy.context.view_layer.update()
    key_all(f)
acts["Idle"] = idle
print("Idle 생성 (50프레임 숨쉬기, 가슴 2도, 바탕 Walk f%d)" % IDLE_BASE_F)

# ---- 9) 안 쓰는 클립 제거 ----
for a in bpy.data.actions:
    a.use_fake_user = True
KEEP = {"Idle", "Walk", "Run", "Attack"}
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        print("액션 제거:", a.name)
        bpy.data.actions.remove(a)
print("최종 액션:", sorted(a.name for a in bpy.data.actions))


# ---- 10) 크기 진단 ----
# ★클립별 스킨 메시의 최저z / 최고z. 골반 스케일 사고 재발 감시용이다.
# 클립들의 최고z(키)가 같아야 한다.
def clip_z(act):
    use(act)
    f0 = int(round(act.frame_range[0]))
    f1 = int(round(act.frame_range[1]))
    m = mesh.matrix_world
    a, b, c, d = m[2][0], m[2][1], m[2][2], m[2][3]
    lo, hi = 9e9, -9e9
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = mesh.evaluated_get(dg)
        me = ev.to_mesh()
        nv = len(me.vertices)
        buf = [0.0] * (nv * 3)
        me.vertices.foreach_get("co", buf)
        zz = [a * buf[i] + b * buf[i + 1] + c * buf[i + 2] + d
              for i in range(0, nv * 3, 3)]
        ev.to_mesh_clear()
        lo = min(lo, min(zz))
        hi = max(hi, max(zz))
    return lo, hi, f1 - f0 + 1


print("=" * 72)
print("[10] 클립별 메시 z 범위")
print("  %-8s %6s %10s %10s %10s" % ("클립", "프레임", "최저z", "최고z", "키"))
ZTAB = {}
for nm in ("Idle", "Walk", "Run", "Attack"):
    lo, hi, nf = clip_z(acts[nm])
    ZTAB[nm] = (lo, hi, nf)
    print("  %-8s %6d %+10.4f %+10.4f %10.4f" % (nm, nf, lo, hi, hi - lo))
kk = [v[1] for v in ZTAB.values()]
print("  클립 간 최고z 편차 %.4f (%.2f%%)"
      % (max(kk) - min(kk), 100.0 * (max(kk) - min(kk)) / max(kk)))

print("\n[스케일 점검] 굽기 후")
for nm in sorted(KEEP):
    r = scale_ranges(acts[nm])
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-8s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))

# ---- 10.5) 게임 크기 환산 ----
# main.js 는 전 메시 박스로 키를 재서 CHAR_CFG.h 로 정규화한다.
# 여기서는 Idle 첫 프레임(게임 진입 자세)의 박스를 기준으로 잰다.
print("=" * 72)
print("[10.5] 게임 크기 환산")
use(acts["Idle"])
sc.frame_set(1)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg)
me = ev.to_mesh()
mw = mesh.matrix_world
pts = [mw @ v.co for v in me.vertices]
ev.to_mesh_clear()
Z0, Z1 = min(p.z for p in pts), max(p.z for p in pts)
H_IDLE = Z1 - Z0
# 몸통 중심(피격 구 근사에 쓰인다) = 골반~가슴 사이 몸통 정점의 z 중앙값이 아니라
# 전체 박스 중심과 골반 높이 둘 다 찍어 준다.
PELVIS_Z = wp("pelvis").z
HEAD_Z = wp("head").z
K = GAME_TARGET_H / H_IDLE
print("  원본 키(Idle f1) %.4f / 레스트 키 %.4f" % (H_IDLE, H_REST))
print("  게임 목표 키 %.2f -> 배율 %.4f (플레이어 키 %.2f 대비 %.1f%%)"
      % (GAME_TARGET_H, K, PLAYER_H, 100.0 * GAME_TARGET_H / PLAYER_H))
print("  게임 단위: 발바닥 0.000 / 박스중심 %.3f / 골반 %.3f / 머리뼈 %.3f / 정수리 %.3f"
      % ((Z0 + Z1) / 2 * K - Z0 * K, (PELVIS_Z - Z0) * K,
         (HEAD_Z - Z0) * K, GAME_TARGET_H))
print("  칼끝 실측 구간 %.2f~%.2f 와 비교: 바닥에 세우면 몸통은 %.2f~%.2f 를 차지"
      % (SWORD_LO, SWORD_HI, 0.0, GAME_TARGET_H))
if GAME_TARGET_H < SWORD_LO:
    print("  ★칼끝 하한(%.2f)이 정수리(%.2f)보다 높다 = 바닥에 두면 한 대도 안 맞는다"
          % (SWORD_LO, GAME_TARGET_H))
else:
    print("  ★정수리 %.2f 가 칼끝 하한 %.2f 를 %.2f 만큼만 넘는다 = 스치는 수준"
          % (GAME_TARGET_H, SWORD_LO, GAME_TARGET_H - SWORD_LO))

# ---- 11) 텍스처 ----
# ★게임은 재질을 MeshToonMaterial({map}) 로 갈아끼운다. 베이스컬러 말고는 안 쓴다.
#   이 재질은 emissiveTexture 에 알베도를 그대로 물려놨다(Meshy 기본). 링크를 끊으면
#   익스포터가 안 내보낸다(export_unused_images 기본 False).
# ★Blender RNA 오브젝트는 접근할 때마다 새 래퍼가 나와 `is` 비교가 안 먹는다.
#   노드 비교는 반드시 **이름**으로(s15 에서 이걸로 베이스컬러까지 날렸다).
print("=" * 72)
print("[11] 텍스처")


def strip_material(m):
    if not m or not m.node_tree:
        return
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    bn = bsdf.name
    kept = None
    for l in list(nt.links):
        if l.to_node.name != bn:
            continue
        if l.to_socket.name == "Base Color":
            kept = l.from_node.name
            continue
        print("    %-16s 링크 끊음: %-18s (from %s)"
              % (m.name, l.to_socket.name, l.from_node.name))
        nt.links.remove(l)
    for key, val in (("Emission Strength", 0.0), ("Metallic", 0.0),
                     ("Roughness", 0.75), ("Specular IOR Level", 0.35)):
        s = bsdf.inputs.get(key)
        if s is not None:
            s.default_value = val
    s = bsdf.inputs.get("Emission Color")
    if s is not None:
        s.default_value = (0, 0, 0, 1)
    keepset, stack = set(), ([kept] if kept else [])
    while stack:
        nm = stack.pop()
        if nm is None or nm in keepset:
            continue
        keepset.add(nm)
        nd = nt.nodes.get(nm)
        if nd is None:
            continue
        for i in nd.inputs:
            for l in i.links:
                stack.append(l.from_node.name)
    for nd in list(nt.nodes):
        if nd.type == "TEX_IMAGE" and nd.name not in keepset:
            print("    %-16s 텍스처 노드 제거: %s"
                  % (m.name, getattr(nd.image, "name", "?")))
            nt.nodes.remove(nd)
    print("    %-16s 남긴 베이스컬러 노드: %s" % (m.name, kept))


for m in mesh.data.materials:
    strip_material(m)

used = []
for slot in mesh.data.materials:
    if not slot or not slot.node_tree:
        continue
    for nd in slot.node_tree.nodes:
        img = getattr(nd, "image", None)
        if img is not None and img not in used:
            used.append(img)
print("  메시가 쓰는 이미지 %d장" % len(used))
for img in used:
    w, h = img.size
    print("    %-16s %dx%d 채널%d %s" % (img.name, w, h, img.channels, img.file_format))
    if TEX_SIZE and (w > TEX_SIZE or h > TEX_SIZE):
        k = TEX_SIZE / float(max(w, h))
        img.scale(max(1, int(round(w * k))), max(1, int(round(h * k))))
        print("      -> %dx%d 로 축소" % img.size[:])
    else:
        print("      -> 축소 안 함(TEX_SIZE=%s)" % TEX_SIZE)

# ---- 12) 내보내기 ----
print("=" * 72)
print("[12] 내보내기")
use(acts["Idle"])
sc.frame_set(1)
arm.data.pose_position = "POSE"
bpy.context.view_layer.update()
sc.render.fps = 30
print("  export fps =", sc.render.fps)
print("  오브젝트:", [(o.name, o.type) for o in sc.objects])
print("  액션:", sorted(a.name for a in bpy.data.actions))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB, export_format="GLB", use_selection=False,
    export_animations=True, export_animation_mode="ACTIONS",
    export_nla_strips=False, export_bake_animation=True,
    export_frame_range=False, export_yup=True,
    export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
    export_jpeg_quality=TEX_QUALITY)
sz = os.path.getsize(OUT_GLB)
print("EXPORTED %s  %d bytes (%.2f MB)  TEX_SIZE=%d %s q%d  삼각형 %d->%d  뼈 %d"
      % (OUT_GLB, sz, sz / 1e6, TEX_SIZE, TEX_FORMAT, TEX_QUALITY,
         TRI0, TRI1, len(arm.data.bones)))
