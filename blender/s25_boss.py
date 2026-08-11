# -*- coding: utf-8 -*-
"""Meshy 보스(각귀, glb 5개)를 게임용 단일 glb 로 합친다. -> web/boss.glb

s16_goblin.py 의 보스판이다. **뼈대가 고블린과 비트 단위로 같다**(같은 24본,
같은 이름·순서 - probe 로 대조 완료). 그래서 파이프라인이 그대로 돈다.
바뀌는 것은 세 가지뿐이다.

  1. Idle 을 **만들 필요가 없다.** 고블린은 Meshy 가 Idle 을 안 줘서 걷기 프레임을
     골라 숨쉬기 루프를 지어냈는데, 보스는 Combat_Stance(1.70초)를 받았다.
     ★그래도 레스트(T포즈)를 Idle 로 쓰면 안 된다는 원칙은 그대로다. 레스트는
       최저z 가 정확히 0이고 다른 클립은 음수에서 놀아서, 레스트를 쓰면 움직이기
       시작하는 순간 캐릭터가 툭 떨어진다.
  2. **삼각형 감축을 안 한다.** 고블린은 동시 10~20마리라 2,000까지 깎았지만
     보스는 층에 한 마리다. 15,040 을 그대로 쓴다(스팀 설치형이라 예산 여유 있음).
  3. 파일이 5개다(레스트 1 + 애니 4). 레스트(Character_output)는 clip0 2프레임짜리
     정지 클립뿐이라 **안 쓴다.** 애니 4개만 읽는다.

받은 것
  incoming/meshy_boss/ 의 Walking / Running / Attack / Combat_Stance (각 8.7MB)
  네 파일이 **각각 메시를 통째로** 들고 있다(합 43MB). 뼈(24본)·메시(15,040삼각형)·
  재질(2048x2048 PNG 1장)이 같으므로 메시는 하나만 두고 액션만 모은다.

glb 직접 파싱(probe_glbscale.py) 결과
  파일당 애니메이션 정확히 1개. 숨은 clip0 없음.
  scale 채널 1.0000~1.0000 = **뿌리 스케일 오염 없음**(궁수 Walk 17.65% 사고 없음).

만드는 액션: Idle / Walk / Run / Attack  (게임이 쓰는 이름 그대로)
  Idle = Combat_Stance(1.70초) / Walk = walking_man(1.07초)
  Run  = running(0.67초)       / Attack = Attack(2.83초)

실행: blender -b -P blender/s25_boss.py
"""
import bpy
import os

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming/meshy_boss")
WEB = os.path.join(ROOT, "web")
BASE = "Meshy_AI_Korean_dokkaebi_ogre__biped_Animation_%s_withSkin.glb"

# ---- 손잡이 ----
# TEX_SIZE  : 텍스처 한 변 픽셀(0 이면 원본 유지). ★익스포터에 해상도 옵션이
#             없어서 image.scale() 로 데이터블록을 직접 줄인다. 원본이 이미
#             2048 이라 이 값에서는 축소가 안 일어난다(포맷 변환만 먹는다).
# TEX_FORMAT: AUTO(PNG 유지) / JPEG / WEBP.
#             이 텍스처도 고블린과 같은 PNG **colortype 2**(알파 채널 자체가 없음)이고
#             재질도 alphaMode 를 안 쓴다. JPEG 로 바꿔도 잃는 정보가 없다.
# TRI_TARGET: 목표 삼각형 수. **0 = 감축 안 함**(보스는 층에 한 마리다).
TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_FORMAT = os.environ.get("TEX_FORMAT", "JPEG").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))
TRI_TARGET = int(os.environ.get("TRI_TARGET", "0"))
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "boss.glb")

# 게임 기준값(보고용 계산에만 쓴다)
# ★보스 시각 키 목표 = 2.9~3.1m. 플레이어 1.75m 의 1.7배로 "한눈에 다르게" 보인다.
GAME_TARGET_H = float(os.environ.get("GAME_TARGET_H", "3.0"))
PLAYER_H = 1.75          # main.js CHAR_CFG.slayer.h
GOBLIN_H = 1.30          # enemy.js GOB_H(잡몹 게임 키)
SWORD_LO, SWORD_HI = 1.20, 2.48   # enemy.js 주석의 칼끝 월드 Y 실측 구간

# Meshy 이름 -> 우리 규칙. 순서 중요(긴 것부터 매칭)
# ★게임 코드(main.js)와 포즈 시스템이 "r hand", "l thigh" 같은 **부분 문자열**로
#   뼈를 찾는다. Meshy 이름(RightHand, LeftUpLeg)은 안 잡힌다.
# ★척추: Spine/Spine01/Spine02 중 위 두 개는 Chest/Chest2 로. 셋 다 'spine' 을
#   넣으면 pb("spine") 이 엉뚱한 걸 잡는다.
# ★이 표는 s16(고블린)과 **글자 하나까지 같다.** 두 리그가 같은 24본이기 때문이다.
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
for tag, name in (("Running", "Run"), ("Attack", "Attack"),
                  ("Combat_Stance", "Idle")):
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
# 경로만 따라 고친다. Run/Attack/Idle 은 **다른 아마추어**에서 가져온 뒤 그 아마추어를
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
for nm in ("Walk", "Run", "Attack", "Idle"):
    act = acts[nm]
    act.name = nm
    act.use_fake_user = True
    print("  액션 %-8s fcurve %3d개 중 경로 %3d개 수정"
          % (nm, len(fcs_of(act)), fix_paths(act)))
# 기준 액션(Walk)만 0 개가 정상. Run/Attack/Idle 이 0 이면 T 포즈 함정에 빠진 것이다.
for nm in ("Run", "Attack", "Idle"):
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

# ---- 6) 삼각형 감축(보스는 안 한다) ----
# 고블린은 동시 10~20마리라 2,000까지 깎았다. 보스는 층에 **한 마리**뿐이고
# 목표 플랫폼이 스팀 설치형이라 15,040 을 그대로 쓴다. 깎으면 뿔·이빨 같은
# 얇은 특징부터 무너져서 "가까이서 보는 한 마리"에는 손해다.
print("=" * 72)
print("[6] 삼각형 감축")
TRI0 = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print("  삼각형 %d / 정점 %d" % (TRI0, len(mesh.data.vertices)))
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
    print("  ratio %.4f 적용 -> 삼각형 %d" % (md.ratio, TRI1))
else:
    TRI1 = TRI0
    print("  감축 안 함(TRI_TARGET=%s / 보스는 층에 한 마리)" % TRI_TARGET)


# ---- 7) 레스트 기준선 ----
# Idle 을 지어내지 않으므로 s16 의 '걷기 프레임별 표'는 필요 없다.
# 다만 레스트(바인드 T포즈)의 키·최저z 는 **게임 쪽 배율 계산의 기준**이라 찍는다.
# ★three.js 는 Box3.setFromObject 로 재면 스키닝이 안 먹은 **바인드 박스**가 나온다.
#   boss.js 가 쓸 배율은 이 값 기준이라 여기서 정확히 뽑아 보고한다.
def wp(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return (arm.matrix_world @ b.matrix).translation.copy()
    return None


print("=" * 72)
print("[7] 레스트(바인드 T포즈) 기준선")
use(acts["Idle"])
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
REST_LOW = low_z()
zs_rest = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H_REST = max(zs_rest) - min(zs_rest)
REST_TOP = max(zs_rest)
print("  레스트 키 %.4f / 최저z %+.4f / 최고z %+.4f" % (H_REST, REST_LOW, REST_TOP))
print("  ★three.js 바인드 박스 높이도 이 값(%.4f)이 나온다 = boss.js 배율의 분모" % H_REST)
arm.data.pose_position = "POSE"

# ---- 8) 안 쓰는 클립 제거 ----
print("=" * 72)
print("[8] 액션 정리")
for a in bpy.data.actions:
    a.use_fake_user = True
KEEP = {"Idle", "Walk", "Run", "Attack"}
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        print("액션 제거:", a.name)
        bpy.data.actions.remove(a)
print("최종 액션:", sorted(a.name for a in bpy.data.actions))


# ---- 9) 크기 진단 ----
# ★클립별 스킨 메시의 최저z / 최고z. 골반 스케일 사고 재발 감시용이자
#   **발 접지** 확인이다. 최저z 가 0 근처여야 게임에서 발이 땅에 붙는다.
#   클립들의 최고z(키)가 서로 같아야 한다.
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
print("[9] 클립별 메시 z 범위(발 접지 확인)")
print("  %-8s %6s %10s %10s %10s" % ("클립", "프레임", "최저z", "최고z", "키"))
ZTAB = {}
for nm in ("Idle", "Walk", "Run", "Attack"):
    lo, hi, nf = clip_z(acts[nm])
    ZTAB[nm] = (lo, hi, nf)
    print("  %-8s %6d %+10.4f %+10.4f %10.4f" % (nm, nf, lo, hi, hi - lo))
kk = [v[1] for v in ZTAB.values()]
print("  클립 간 최고z 편차 %.4f (%.2f%%)"
      % (max(kk) - min(kk), 100.0 * (max(kk) - min(kk)) / max(kk)))
zz = [v[0] for v in ZTAB.values()]
print("  클립 간 최저z %+.4f ~ %+.4f  (게임 배율 %.4f 를 곱하면 %+.3f ~ %+.3f m)"
      % (min(zz), max(zz), GAME_TARGET_H / H_REST,
         min(zz) * GAME_TARGET_H / H_REST, max(zz) * GAME_TARGET_H / H_REST))

print("\n[스케일 점검] 굽기 후")
for nm in sorted(KEEP):
    r = scale_ranges(acts[nm])
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-8s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))

# ---- 9.5) 게임 크기 환산 ----
# boss.js 는 three.js Box3(바인드 박스)로 키를 재서 목표 키로 정규화한다.
# 여기서 그 배율을 미리 계산해 보고한다.
print("=" * 72)
print("[9.5] 게임 크기 환산")
use(acts["Idle"])
sc.frame_set(int(round(acts["Idle"].frame_range[0])))
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg)
me = ev.to_mesh()
mw = mesh.matrix_world
pts = [mw @ v.co for v in me.vertices]
ev.to_mesh_clear()
Z0, Z1 = min(p.z for p in pts), max(p.z for p in pts)
H_IDLE = Z1 - Z0
PELVIS_Z = wp("pelvis").z
HEAD_Z = wp("head").z
K = GAME_TARGET_H / H_REST      # ★바인드 박스 기준(three.js 가 재는 값과 같다)
print("  바인드(레스트) 키 %.4f / Idle 첫 프레임 키 %.4f" % (H_REST, H_IDLE))
print("  게임 목표 키 %.2f -> 배율 %.4f" % (GAME_TARGET_H, K))
print("  플레이어 %.2f 대비 %.2f배 / 잡몹 고블린 %.2f 대비 %.2f배"
      % (PLAYER_H, GAME_TARGET_H / PLAYER_H, GOBLIN_H, GAME_TARGET_H / GOBLIN_H))
print("  게임 단위(발바닥 0 기준): 골반 %.3f / 머리뼈 %.3f / Idle 정수리 %.3f"
      % ((PELVIS_Z - Z0) * K, (HEAD_Z - Z0) * K, H_IDLE * K))
print("  기존 히트 구(중심 y 1.65 / 반경 1.43)는 y %.2f~%.2f 를 덮는다"
      % (1.65 - 1.43, 1.65 + 1.43))
print("  칼끝 실측 구간 %.2f~%.2f 가 그 구 안에 통째로 들어간다 = 판정 그대로 유지 가능"
      % (SWORD_LO, SWORD_HI))

# ---- 10) 텍스처 ----
# ★게임은 재질을 MeshToonMaterial({map}) 로 갈아끼운다. 베이스컬러 말고는 안 쓴다.
#   이 재질은 emissiveTexture 에 알베도를 그대로 물려놨다(Meshy 기본). 링크를 끊으면
#   익스포터가 안 내보낸다(export_unused_images 기본 False).
# ★Blender RNA 오브젝트는 접근할 때마다 새 래퍼가 나와 `is` 비교가 안 먹는다.
#   노드 비교는 반드시 **이름**으로(s15 에서 이걸로 베이스컬러까지 날렸다).
print("=" * 72)
print("[10] 텍스처")


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
        print("      -> 축소 안 함(이미 %d 이하)" % TEX_SIZE)

# ---- 11) 내보내기 ----
print("=" * 72)
print("[11] 내보내기")
use(acts["Idle"])
sc.frame_set(int(round(acts["Idle"].frame_range[0])))
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
print("EXPORTED %s  %d bytes (%.2f MB)  TEX_SIZE=%d %s q%d  삼각형 %d  뼈 %d"
      % (OUT_GLB, sz, sz / 1e6, TEX_SIZE, TEX_FORMAT, TEX_QUALITY,
         TRI1, len(arm.data.bones)))
print("  원본 5파일 합 43MB -> 한 벌 %.2fMB" % (sz / 1e6))
