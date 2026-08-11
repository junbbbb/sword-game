# -*- coding: utf-8 -*-
"""Meshy 기본 남성(basic_man1, glb 2개)을 게임용 단일 glb 로 합친다.
s11_archer.py 의 기본체판. 함정 처리는 s11 과 동일하다.

받은 것
  Meshy_AI_biped_Animation_Walking_withSkin.glb  (26.4MB)
  Meshy_AI_biped_Animation_Running_withSkin.glb  (26.4MB)
  두 파일 **각각 메시를 통째로** 들고 있다. 뼈대(24본)·메시(5386정점 8535삼각형)·
  재질(4096x4096 PNG 1장)이 완전히 같으므로 메시는 하나만 두고 액션만 모은다.
  glb 를 직접 파싱해 확인한 결과 파일당 애니메이션이 **정확히 1개씩**이다
  (궁수 때처럼 숨은 clip0 이 없다). 뿌리 스케일 오염도 없다(scale 1.0000~1.0000).

만드는 액션: Idle / Walk / Run 셋뿐.
  Attack, Jump 는 원본에 없다. 게임에 없는 클립 방어 코드가 이미 있으므로
  억지로 만들지 않는다.

★Idle 바탕 = Walk **f1** (근거는 아래 6단계 주석)

★뼈 이름을 Bip001 규칙으로 바꾼다
  포즈 시스템(combo_poses.Poser.pb)과 게임 코드(main.js)가 전부
  "r hand", "l thigh" 같은 **부분 문자열**로 뼈를 찾는다.
  Meshy 이름(RightHand, LeftUpLeg)은 안 잡힌다.

★척추 주의: Spine/Spine01/Spine02 중 위 두 개는 Chest/Chest2 로 부른다.
  셋 다 'spine' 을 넣으면 pb("spine") 이 엉뚱한 걸 잡는다.

★Icosphere 를 지운다
  Blender 의 gltf **임포터**가 뼈를 그리려고 반지름 1 짜리 구를 만든다
  (glb 안에는 없다). main.js 는 전 메시로 박스를 재므로 이게 그대로 키에
  들어가 몸이 쪼그라들고 발이 뜬다.

실행: blender --background --python s13_basic.py
"""
import bpy
import os
import math
from mathutils import Matrix

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming/meshy3/Meshy_AI_biped")
WEB = os.path.join(ROOT, "web")
BASE = "Meshy_AI_biped_Animation_%s_withSkin.glb"

# ---- 텍스처 굽기 손잡이 (여기만 고치면 된다) ----
# 원본 텍스처는 4096x4096 PNG 26MB 라 glb 가 25MB 다(다른 캐릭터의 3배).
# TEX_SIZE  : 텍스처 한 변 픽셀. 0 이면 원본 그대로 둔다.
#             ★Blender glTF 익스포터에는 해상도 옵션이 아예 없다(포맷/품질뿐).
#               그래서 축소는 이미지 데이터블록을 image.scale() 로 직접 줄인다.
# TEX_FORMAT: AUTO(PNG 유지) / JPEG / WEBP. 이 캐릭터 텍스처는 PNG colortype 2
#             (알파 채널 자체가 없음) 이고 재질도 alphaMode 를 안 쓴다.
#             따라서 JPEG 로 바꿔도 잃는 정보가 없다.
# TEX_QUALITY: JPEG/WEBP 품질(0~100).
# OUT_GLB   : 결과 경로. 비교 굽기용으로 임시 경로에 뽑을 때 쓴다.
TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_FORMAT = os.environ.get("TEX_FORMAT", "JPEG").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "basic.glb")

# Meshy 이름 -> 우리 규칙. 순서 중요(긴 것부터 매칭)
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

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene


def imp(tag):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, BASE % tag))
    return [o for o in sc.objects if o.name not in before]


# ---- 1) Walking 을 기준으로 삼는다(메시 제공 + Walk) ----
objs = imp("Walking")
arm = next(o for o in objs if o.type == "ARMATURE")
for o in list(objs):
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        print("Icosphere 제거(키 계산 오염원)")
        bpy.data.objects.remove(o, do_unlink=True)
        objs.remove(o)
mesh = next(o for o in objs if o.type == "MESH")
print("기준 리그:", arm.name, "본", len(arm.data.bones), "/ 메시", mesh.name,
      len(mesh.data.polygons), "면")

acts = {}
if arm.animation_data and arm.animation_data.action:
    acts["Walk"] = arm.animation_data.action
    print("  [Walking] 아마추어에 붙은 액션 = %s (%.1f~%.1f 프레임)"
          % (acts["Walk"].name, acts["Walk"].frame_range[0],
             acts["Walk"].frame_range[1]))

# ---- 2) 나머지는 액션만 가져오고 오브젝트는 버린다 ----
# ★액션 이름 충돌 함정: 임포트한 소스 액션이 "Run" 같은 우리 이름을 먼저 차지하면
#   우리 액션이 조용히 Run.001 이 되고, 8단계 정리 루프가 그걸 지운다.
#   들어오자마자 SRC_ 접두사로 밀어 원천 차단한다.
# ★한 파일에 애니메이션이 여러 개일 수 있다(궁수는 rigify_clip 75프레임 +
#   clip0 2프레임 정지가 같이 있었다). 그래서 파일당 새 액션 수를 찍는다.
for tag, name in (("Running", "Run"),):
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
        # 숨은 클립이 있으면 프레임 수가 많은 쪽이 진짜 동작이다.
        longest = max(fresh, key=lambda a: a.frame_range[1] - a.frame_range[0])
        print("    ★숨은 클립 발견. 최장 클립 = %s" % longest.name)
    act.use_fake_user = True
    acts[name] = act
    for o in got:
        bpy.data.objects.remove(o, do_unlink=True)
print("모은 액션:", list(acts))

# ---- 3) 뼈 이름 변경 ----
n = 0
for old, new in RENAME:
    b = arm.data.bones.get(old)
    if b:
        b.name = new
        n += 1
print("뼈 이름 변경 %d개 / 전체 %d개" % (n, len(arm.data.bones)))
print("  ->", [b.name for b in arm.data.bones])

# ★★가장 중요한 함정
# Blender 는 뼈 이름을 바꿀 때 **그 아마추어에 현재 붙어 있는 액션**의 데이터 경로만
# 따라 고친다. Run 은 **다른 아마추어**에서 가져온 뒤 그 아마추어를 지웠으므로
# fcurve 경로가 아직 pose.bones["RightHand"] 를 가리킨다. 그대로 내보내면 그 클립을
# 재생할 때 아무 뼈도 안 잡혀 **T 포즈**가 된다.
# (증상: 걷기는 되는데 Shift 달리기 누르면 T 포즈. 탱커에서 실제로 겪었다)
NAMEMAP = dict(RENAME)


def fix_paths(act):
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
    n = 0
    for fc in fcs:
        dp = fc.data_path
        if '"' not in dp:
            continue
        old_b = dp.split('"')[1]
        new_b = NAMEMAP.get(old_b)
        if new_b and new_b != old_b:
            fc.data_path = dp.replace('"%s"' % old_b, '"%s"' % new_b, 1)
            n += 1
    return n


for nm, act in acts.items():
    act.name = nm
    act.use_fake_user = True
    print("  액션 %-8s fcurve 경로 %d개 수정" % (nm, fix_paths(act)))
# 기준 액션(Walk)만 0 개가 정상. Run 이 0 이면 T 포즈 함정에 빠진 것이다.
if fix_paths(acts["Run"]) != 0:
    raise SystemExit("fix_paths 재실행에서 또 고쳐졌다 = 1차가 실패")


# ---- 4) 진단 도구 ----
def use(act):
    """액션을 붙인다. Blender 4.4+ 는 슬롯이 있어야 채널이 먹는다."""
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


# ---- 4.5) ★★Meshy 리타깃 잔재 감시: 뿌리 뼈에 박힌 스케일 ----
# 궁수 Walking_Woman 은 Bip001 Pelvis 에 스케일 1.1765 가 전 프레임 상수로 박혀
# 있어서 걷기만 하면 캐릭터가 17.65% 부풀었다. 이 리그는 뼈 24개가 전부 골반
# 하위라 골반 스케일이 스켈레톤 전체에 곱해진다.
# basic_man1 은 glb 직접 파싱(probe_glbscale.py)에서 두 파일 다 1.0000~1.0000 로
# 깨끗했지만, 굽는 쪽에서도 한 번 더 걸러 둔다.
# ★보정은 '스케일 1.0 + 골반 translation 을 같은 배율로 축소' 여야 한다.
#   스케일만 내리면 다리가 짧아진 만큼 발이 뜬다(s11 4.5단계 유도식 참고).
PELVIS = "Bip001 Pelvis"


def deflate_root_scale(act):
    sfc = [fc for fc in fcs_of(act)
           if fc.data_path == 'pose.bones["%s"].scale' % PELVIS]
    vals = [k.co.y for fc in sfc for k in fc.keyframe_points]
    if not vals:
        print("  골반 스케일 채널 없음 = 손댈 것 없음")
        return 1.0
    k = sum(vals) / len(vals)
    if max(vals) - min(vals) > 1e-4:
        raise SystemExit("골반 스케일이 상수가 아니다(%.4f~%.4f). 보정식 재검토 필요"
                         % (min(vals), max(vals)))
    if abs(k - 1.0) < 1e-4:
        print("  골반 스케일 이미 1.0 = 손댈 것 없음")
        return 1.0
    s = 1.0 / k
    # 포즈 본 location 은 월드가 아니라 레스트 기준 로컬 오프셋이다.
    #   p = rest + R @ loc,  원하는 것 p' = s*p  =>  loc' = s*loc + (s-1)*R⁻¹@rest
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


print("\n[스케일 점검] 굽기 전")
print("아마추어 원점", tuple(round(x, 5) for x in arm.matrix_world.translation))
for nm in sorted(acts):
    r = scale_ranges(acts[nm])
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-8s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))
    if bad:
        if set(bad) == {PELVIS}:
            deflate_root_scale(acts[nm])
        else:
            raise SystemExit("골반이 아닌 뼈에 스케일이 박혔다: %s" % list(bad))

# ---- 5) 걷기 프레임별 발·팔 표 (Idle 바탕 프레임 선정 근거) ----
# 캐릭터는 -Y 를 본다(headfront 가 코 쪽이고 -Y 에 있다). 그래서 발.y 가 작을수록 앞.
# 팔 흔들림은 '레스트에서 손이 골반보다 얼마나 뒤(+y)에 있는가' 를 기준선으로 잰다.
use(acts["Walk"])
WF0 = int(acts["Walk"].frame_range[0])
WF1 = int(acts["Walk"].frame_range[1]) + 1


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
arm.data.pose_position = "POSE"
print("\n[레스트(바인드 T포즈)] 최저z %+.4f / 손-골반 기준선 dy 왼 %+.4f 오른 %+.4f"
      % (REST_LOW, BASE_LDY, BASE_RDY))
print("[걷기 프레임별]  발 전후간격 = |왼발.y - 오른발.y| (작을수록 다리 모임)")
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
    cand.append((f, gap, swing, max(lt.z, rt.z), lz))
    print("  %4d %10.4f %8.4f %8.4f %10.4f %9.4f"
          % (f, gap, lt.z, rt.z, swing, lz))

# ---- 6) Idle 바탕 프레임 ----
# ★왜 Walk f1 인가 (위 표가 근거)
#   - 발 전후간격이 0.006m 로 사이클 최소다(접촉 자세는 0.60~0.68m 벌어진다).
#     '다리를 벌린 중간자세' 를 피하라는 요구를 정확히 만족한다.
#   - 팔 스윙이 거의 중립이다(레스트 기준 편차 0.058m, 사이클 2위. 1위 f0 과
#     0.004m 차이라 사실상 같다). 걷기 사이클에서 양팔은 180도 반대 위상이라
#     '양팔이 동시에 완전 중립' 인 프레임은 존재하지 않는다.
#   - 발끝 높이가 0.049 / 0.015 (레스트 0.034) 라 두 발 다 사실상 땅에 있다.
#     f13(반대쪽 패싱)은 들린 발끝이 0.090 까지 떠서 외발서기로 보인다.
#   - 메시 최저z 가 -0.028 로 Walk/Run 클립과 같은 대역이다. 레스트 T포즈는
#     최저z 가 정확히 0 이라, 그걸 Idle 로 쓰면 걷기 시작할 때 캐릭터가
#     3cm 아래로 툭 떨어진다(클립 간 접지 높이 불일치). 걷기 프레임을 바탕으로
#     삼으면 Idle <-> Walk 전환에 수직 튐이 없다.
IDLE_BASE_F = 1
sc.frame_set(IDLE_BASE_F)
bpy.context.view_layer.update()
print("\nIdle 바탕 = Walk f%d / 메시 최저z %+.4f" % (IDLE_BASE_F, low_z()))
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
    a.use_fake_user = True
    arm.animation_data.action = a
    try:
        # ★Blender 4.4+ 는 슬롯이 없으면 액션이 조용히 아무 일도 안 한다.
        slot = a.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = slot
    except Exception:
        pass
    return a


# ---- 7) Idle: 숨쉬기 루프 50프레임 ----
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
print("Idle 생성 (50프레임 숨쉬기, 가슴 2도)")

# ---- 8) 안 쓰는 클립은 지운다. 남기면 파일만 커진다 ----
for a in bpy.data.actions:
    a.use_fake_user = True
KEEP = {"Idle", "Walk", "Run"}
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        print("액션 제거:", a.name)
        bpy.data.actions.remove(a)
print("최종 액션:", sorted(a.name for a in bpy.data.actions))


# ---- 9) 크기 진단 ----
# ★클립별 스킨 메시의 최저z / 최고z. 골반 스케일 사고의 재발 감시용이다.
# 세 클립의 키(최고z-최저z 가 아니라 최고z 자체)가 같아야 한다.
def clip_z(act):
    """액션 전 프레임을 돌며 스킨 적용된 메시의 최저z / 최고z 를 잰다.
    프레임마다 Vector 를 3만개씩 만들면 느려서 z 행만 직접 곱한다."""
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


print("\n[클립별 메시 z 범위]")
print("  %-8s %6s %10s %10s %10s" % ("클립", "프레임", "최저z", "최고z", "키"))
for nm in ("Idle", "Walk", "Run"):
    lo, hi, nf = clip_z(acts[nm])
    print("  %-8s %6d %+10.4f %+10.4f %10.4f" % (nm, nf, lo, hi, hi - lo))

print("\n[스케일 점검] 굽기 후")
for nm in sorted(KEEP):
    r = scale_ranges(acts[nm])
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-8s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))

# ---- 10) 손 그립 소켓 조사 (나중에 무기를 쥐여주려면 이 값이 필요하다) ----
# 손가락 뼈가 없다(손목 다음이 없다). 그래서 무기는 손목 뼈에 오프셋으로 붙인다.
# 오프셋은 **뼈 로컬 좌표**로 줘야 애니메이션을 따라간다.
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
for side in ("R", "L"):
    bn = "Bip001 %s Hand" % side
    b = arm.data.bones[bn]
    vg = mesh.vertex_groups.get(bn)
    print("\n[%s 레스트]" % bn)
    print("  head(월드) %s  길이 %.4f"
          % (tuple(round(x, 4) for x in (arm.matrix_world @ b.head_local)),
             b.length))
    if vg:
        M = (arm.matrix_world @ b.matrix_local).inverted()
        pts = []
        for v in mesh.data.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 0.5:
                    pts.append(M @ (mesh.matrix_world @ v.co))
                    break
        if pts:
            mn = [min(p[k] for p in pts) for k in range(3)]
            mx = [max(p[k] for p in pts) for k in range(3)]
            print("  가중치>0.5 정점 %d개" % len(pts))
            print("  뼈 로컬 bbox  x %+.4f~%+.4f  y %+.4f~%+.4f  z %+.4f~%+.4f"
                  % (mn[0], mx[0], mn[1], mx[1], mn[2], mx[2]))
            print("  손 크기(뼈 로컬) %s / 중심 %s"
                  % (tuple(round(mx[k] - mn[k], 4) for k in range(3)),
                     tuple(round((mx[k] + mn[k]) / 2, 4) for k in range(3))))
arm.data.pose_position = "POSE"

use(acts["Walk"])
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
tri = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print("\n바인드 포즈 키 %.3f  삼각형 %d  메시 %d개"
      % (H, tri, len([o for o in sc.objects if o.type == "MESH"])))


# ---- 11) 텍스처 축소 ----
# ★익스포터가 아니라 여기서 줄인다. glTF 익스포터 옵션에는 해상도가 없다
#   (export_image_format / export_image_quality / export_jpeg_quality 뿐).
# ★우리 메시가 실제로 쓰는 이미지만 건드린다. Running 파일을 임포트할 때
#   똑같은 텍스처가 texture_0.001 로 하나 더 딸려 들어오는데, 그건 쓰는 데가
#   없어서(export_unused_images 기본 False) 내보내지지 않는다. 괜히 건드려
#   시간만 버릴 이유가 없다.
used = []
for slot in mesh.data.materials:
    if not slot or not slot.node_tree:
        continue
    for nd in slot.node_tree.nodes:
        img = getattr(nd, "image", None)
        if img is not None and img not in used:
            used.append(img)
print("\n[텍스처] 메시가 쓰는 이미지 %d개" % len(used))
for img in used:
    w, h = img.size
    print("  %-16s %dx%d  채널 %d  (%s)"
          % (img.name, w, h, img.channels, img.file_format))
    if TEX_SIZE and (w > TEX_SIZE or h > TEX_SIZE):
        # 정사각형이 아닐 수도 있으니 긴 변 기준으로 비율을 맞춘다.
        k = TEX_SIZE / float(max(w, h))
        nw, nh = max(1, int(round(w * k))), max(1, int(round(h * k)))
        img.scale(nw, nh)
        print("    -> %dx%d 로 축소" % (nw, nh))
    else:
        print("    -> 축소 안 함(TEX_SIZE=%s)" % TEX_SIZE)

bpy.ops.object.select_all(action="SELECT")
# export_image_format AUTO = PNG 유지. JPEG/WEBP 는 알파를 못 담지만
# 이 캐릭터는 알파를 안 쓰므로 안전하다(위 주석 참고).
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB, export_format="GLB", use_selection=False,
    export_animations=True, export_animation_mode="ACTIONS",
    export_nla_strips=False, export_bake_animation=True,
    export_frame_range=False, export_yup=True,
    export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
    export_jpeg_quality=TEX_QUALITY)
print("EXPORTED %s  %d bytes  (TEX_SIZE=%s TEX_FORMAT=%s Q=%d)"
      % (OUT_GLB, os.path.getsize(OUT_GLB), TEX_SIZE, TEX_FORMAT, TEX_QUALITY))
