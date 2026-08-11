# -*- coding: utf-8 -*-
"""ToonSoldier(WW2 미군) 원본 에셋을 게임용 단일 glb 로 굽는다 -> web/soldier.glb

받은 것
  모델 FBX 1개(T 포즈, 소총이 손에 스킨된 단일 메시) + 애니메이션 FBX 4개.
  게임이 찾는 이름은 Idle / Walk / Run / Attack 이다.

매핑과 근거
  Idle   <- infantry_guard_idle
           combat_idle 은 다리를 크게 벌리고 웅크린 '사격 직전' 자세라
           대기 상태에서 Walk/Run 으로 넘어갈 때 다리가 튄다.
           guard_idle 은 발이 골반 아래에 모인 중립 기립 + 총을 가슴에 걸친
           자세라 이동 클립과 이어진다. 두 클립 다 f_last == f_first(루프 완벽),
           발 이동 0.000 이지만 guard 쪽이 더 안 움직인다(완전 접지).
           길이는 guard 322프레임 vs combat 61프레임. 322프레임은 데이터가 크지만
           메시가 1006 삼각형뿐이라 총량이 작다. 자연스러움을 택했다.
  CombatIdle <- infantry_combat_idle
           **기본 Idle 로는 안 쓰지만 클립 자체는 버리지 않는다.** 원본 팩의
           모션을 하나도 빠뜨리지 않고 넣어 오너가 게임에서 직접 눌러 보고
           고를 수 있게 한다(전투 대기/경계 자세로 쓸 수 있다).
           61프레임, 루프 완벽(마지막-첫 프레임 차 0.0001), 양발 완전 접지.
           ★원본 FBX 4개는 임포트 시 각각 액션을 **정확히 1개**만 만든다
             (전부 "Bip001|Take 001|BaseLayer" 단일 스택). 숨은 테이크는 없다.
             확인 스크립트: blender/probe_takes.py
  Run    <- infantry_combat_run   (26프레임, 제자리, f26 == f1)
  Attack <- infantry_combat_shoot (31프레임)
  Walk   <- **원본에 걷기가 없다.** infantry_combat_run 을 줄이고 늘려 합성한다.
           Run 을 우리 리그로 옮긴 뒤 각 뼈의 **로컬 회전**을 Idle 1프레임(중립
           기립)과 72% 로 슬러프해 보폭·무릎높이·상하진폭을 한꺼번에 줄이고,
           25프레임 주기를 34프레임으로 늘려 케이던스를 2.4보/초 -> 1.8보/초로
           낮췄다. 같은 뼈대라 리타게팅 오차가 0 이다.

    ★다른 glb 에서 빌려오려던 시도와 왜 접었는지 (다시 하지 않도록 전부 기록)

    1) slayer.glb 의 Walk - 리그는 완벽히 같다.
       뼈 23개 이름 전부 일치, 레스트 head 최대 오차 0.000077,
       head->tail 방향 각도차 **최대 0.0000도**. 리타게팅도 그대로 됐다.
       그런데 옮겨놓고 발 궤적을 재보니 **걷기가 아니었다.**
       s6_export_game.py 의
         WALK = [(1, walk_pose(0)), (9, walk_pose(1)), (17, walk_pose(2)),
                 (25, walk_pose(3)), (33, walk_pose(0))]
       에서 walk_pose 의 phase 1 과 3 이 **같은 else 가지**로 떨어진다.
       pose(3) == pose(1) 이라 클립이 회문이다. 실측하면 f18..f33 이 f16..f1 을
       정확히 되짚는다. 발이 뒤로 갔다가 **디딘 채로 다시 앞으로 온다**
       (오른발 접지 구간 속도 -2.79, 음수). 스윙 구간도 발목·발가락 굴림도
       골반 상하도 없는 4포즈짜리다.

    2) archer.glb 의 Walk - 클립 자체는 진짜 보행 사이클이다
       (스윙 8프레임 / 접지 18프레임 톱니, 접지 중 발끝 z 0.007~0.04).
       회전 델타 리타게팅(축계 변환 C 포함)까지 만들어 붙였고 수평 궤적은
       archer 와 정확히 일치했다. 그런데 세로가 안 맞아서 접었다:
       - 허벅지:종아리 비율이 다르다. 우리 0.610:0.428(59:41),
         archer 0.355:0.415(46:54). 허벅지가 **72% 더 길다.**
         각도만 옮기면 발목이 ±15cm 어긋난다.
       - 그래서 2본 IK(코사인 법칙)를 짰다. 무릎·발목 목표는 정확히 찍혔는데
         결과가 더 나빴다. archer 의 Walk 는 glTF **이동 채널**이 들어 있어
         프레임마다 다리가 최대 17% 늘어난다(f10: 엉덩이->발목 89.6 vs
         레스트 76.9). 우리 다리는 안 늘어나니 IK 가 매 프레임 최대 뻗음에서
         클램프에 걸려 무릎이 아예 안 굽는다. 골반 높이도 같은 이유로 20cm 뜬다.
       - 회전만 옮기고 상수 접지 보정만 하면 몸이 7% 위아래로 뛴다. 게다가
         골반 상하가 archer 의 늘어난 다리에서 나온 값이라 다리와 위상이 어긋나,
         **디딘 발이 뒤가 아니라 앞으로 움직인다**(미끄러짐).
       - 프레임마다 최저점을 바닥에 맞추는 보정도 해봤다. 진폭은 1.7% 로
         줄었지만 우리 쪽에서 더 낮은 발이 archer 의 디딘 발과 달라서
         **디딘 발이 앞으로 0.30 미끄러졌다.**

    3) 합성으로 돌아온 뒤에도 한 번 틀렸다. 섞는 비율 W=0.5 로 했더니
       **접지 위상이 뒤집혔다.** 접은 다리와 편 다리를 똑같이 절반씩 중립으로
       당기면 두 발 높이가 교차한다. 실측하면 양발이 접지 중 앞으로 갔다
       (발 속도 -0.39). W=0.72 로 올려 Run 의 구조를 살리니 디딘 발이 제대로
       뒤로 쓸린다. **W 를 내릴 때는 반드시 접지 구간 투영을 다시 재라.**

       팔·목·머리는 섞지 않고 Idle(guard_idle) 의 소총 파지 자세를 **로컬
       회전**으로 덮는다. 로컬이라 척추가 흔들리면 총도 같이 흔들리고,
       Idle/Run/Attack 과 팔 모양이 이어져 전환할 때 안 튄다.
  Jump   <- 원본에 없다. 만들지 않았다(게임은 있으면 쓰고 없으면 폴백).

★함정 기록 (이 프로젝트에서 실제로 데인 것들)
  1) 액션 슬롯: Blender 4.4+ 는 act.slots.new(id_type="OBJECT") 로 슬롯을 만들고
     animation_data.action_slot 을 지정하지 않으면 액션이 조용히 아무 일도 안 한다.
  2) fcurve 데이터 경로: 다른 아마추어에서 가져온 액션은 옛 뼈 이름을 계속 가리켜
     재생하면 T 포즈가 된다. 여기서는 액션 4개를 **전부 우리 아마추어 위에서 직접
     구워서** 만들기 때문에 구조적으로 발생하지 않는다. 그래도 아래 audit_paths()
     로 모든 fcurve 가 실제 존재하는 뼈를 가리키는지 세어 출력한다.
  3) pb.matrix 직접 대입 -> 아마추어 스케일 폭주(과거 손이 39배). 그래서
     copy_pose_safe() 는 소스 행렬에서 **스케일을 벗겨내고** 넣고, 넣은 뒤
     b.scale 을 1로 고정한다. 부모부터 순서대로 + 매번 view_layer.update().
  4) use_fake_user: 안 켜면 export 에서 조용히 빠진다.
  5) 텍스처: 이 FBX 의 머티리얼은 **존재하지 않는 .psd 경로**를 가리킨다
     (임포트 직후 이미지 크기가 0x0). 옆에 있는 US_soldier_simple.tga 를
     직접 로드해 Principled 의 Base Color 에 물려야 한다. 노드 셰이더는
     glTF 로 안 나가므로 Principled 한 장이어야 한다.

실행: blender -b -P blender/s12_soldier.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import asset_anim as AA  # noqa: E402

PACK = AA.PACK
WEB = os.path.join(ROOT, "web")
OUT = os.path.join(WEB, "soldier.glb")
TGA = os.path.join(PACK, "model/Materials/US_soldier_simple.tga")

# 부위 묶음. copy_pose 는 endswith 로 매칭하므로 "Bip001 " 접두어를 뺀 이름을 쓴다.
# 주의: "Bip001 L Toe0Nub".endswith("L Toe0") 는 False 라 Nub 이 섞이지 않는다.
LEGS = ("Pelvis", "Spine",
        "L Thigh", "L Calf", "L Foot", "L Toe0", "L Toe0Nub",
        "R Thigh", "R Calf", "R Foot", "R Toe0", "R Toe0Nub")
UPPER = ("Neck", "Head", "HeadNub",
         "L Clavicle", "L UpperArm", "L Forearm", "L Hand",
         "R Clavicle", "R UpperArm", "R Forearm", "R Hand")
ALL = LEGS + UPPER

# ---------------------------------------------------------------- 씬 준비
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
print("빈 씬 fps =", sc.render.fps)

bpy.ops.import_scene.fbx(filepath=os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX"))
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH")
print("모델 임포트: 아마추어 %s (본 %d) / 메시 %s (%d 폴리곤)"
      % (arm.name, len(arm.data.bones), mesh.name, len(mesh.data.polygons)))
print("모델 FBX 임포트 후 fps =", sc.render.fps)

# 3ds Max Biped 가 남기는 "Bip001 Footsteps" 같은 빈 오브젝트를 없앤다.
# 남기면 glb 에 쓸모없는 노드로 실린다. 부모로 물려 있으면 월드 행렬을 지키며 떼어낸다.
for o in list(sc.objects):
    if o.type not in ("ARMATURE", "MESH"):
        for ch in list(o.children):
            mw = ch.matrix_world.copy()
            ch.parent = None
            ch.matrix_world = mw
        print("  빈 오브젝트 제거:", o.name, o.type)
        bpy.data.objects.remove(o, do_unlink=True)

# 모델 FBX 가 딸려온 bind take 를 지운다(나중에 우리 액션과 섞이면 곤란).
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
arm.animation_data_clear()

# 회전 모드를 쿼터니언으로 통일한다. 레스트(항등) 상태에서 바꿔야 포즈가 안 바뀐다.
for b in arm.pose.bones:
    b.rotation_mode = "QUATERNION"

# ---------------------------------------------------------------- 텍스처
# ★FBX 머티리얼이 가리키는 .psd 는 이 저장소에 없다(크기 0x0 으로 로드 실패).
img = bpy.data.images.load(TGA)
print("텍스처 %s -> %dx%d" % (os.path.basename(TGA), img.size[0], img.size[1]))
assert img.size[0] > 0, "TGA 로드 실패"
for mat in list(bpy.data.materials):
    nt = mat.node_tree
    nt.nodes.clear()
    out_n = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs[0], out_n.inputs[0])
    try:
        mat.blend_method = "OPAQUE"
    except Exception:
        pass
    print("  머티리얼 %s -> Principled + %s" % (mat.name, img.name))
# glb 에 확실히 실리도록 blend 안에 pack 한다(원본 파일 경로 의존 제거)
img.pack()


# ---------------------------------------------------------------- 도구
def rest():
    """포즈를 레스트로 되돌린다. 소스에 없는 뼈(Nub 등)에 이전 프레임이 남는 걸 막는다."""
    for b in arm.pose.bones:
        b.location = (0, 0, 0)
        b.rotation_quaternion = (1, 0, 0, 0)
        b.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def copy_pose_safe(src, parts, off=None):
    """asset_anim.copy_pose 와 같은 원리(아마추어 공간 최종 행렬, 부모부터 순서대로).
    다른 점 둘:
      1) 소스 행렬에서 **스케일을 벗겨** 넣고 b.scale 을 1로 고정한다.
         과거에 pb.matrix 직접 대입으로 손이 39배가 된 사고가 있었다.
      2) off(아마추어 로컬 벡터)를 모든 뼈에 똑같이 더한다 = 몸 전체 평행이동.
         접지 보정용. 골반만 밀면 자식이 자기 절대 행렬로 덮어써서 도로 돌아온다.
    반환 (옮긴 뼈 수, 소스에서 발견한 최대 |scale-1|)."""
    smap = {b.name: b for b in src.pose.bones}
    todo = []
    for b in arm.pose.bones:
        if b.name not in smap:
            continue
        if not any(b.name.endswith(p) for p in parts):
            continue
        d, x = 0, b
        while x.parent:
            d += 1
            x = x.parent
        todo.append((d, b))
    todo.sort(key=lambda t: t[0])
    dev = 0.0
    for _, b in todo:
        m = smap[b.name].matrix
        loc, rot, scl = m.decompose()
        dev = max(dev, max(abs(s - 1.0) for s in scl))
        if off is not None:
            loc = loc + off
        b.matrix = Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
        b.scale = (1, 1, 1)
        bpy.context.view_layer.update()
    return len(todo), dev


def new_action(name):
    arm.animation_data_clear()
    arm.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True          # ★안 켜면 export 에서 조용히 빠진다
    arm.animation_data.action = act
    # ★Blender 4.4+ 슬롯: 지정 안 하면 액션이 아무 일도 안 한다
    try:
        slot = act.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = slot
    except Exception as e:
        print("  slot 생성 실패(구버전?):", e)
    return act


def key(frame):
    bpy.context.view_layer.update()
    for b in arm.pose.bones:
        b.keyframe_insert("location", frame=frame)
        b.keyframe_insert("rotation_quaternion", frame=frame)
        b.keyframe_insert("scale", frame=frame)


# 아마추어 로컬에서의 '위' 방향. 월드로 1 올리려면 이 벡터에 그 값을 곱해 더한다
# (아마추어 스케일 0.0254 가 들어 있어 길이가 39.37 이다).
LOCAL_UP = (arm.matrix_world.to_3x3().inverted() @ Vector((0, 0, 1)))
def mesh_low():
    """**변형된 메시**의 최저 z(월드). 접지 판정은 이걸로 해야 한다.
    ★발끝 뼈로 재면 두 군데서 틀린다:
      1) 뒤꿈치 착지 순간에는 발끝이 들려 있어 '떴다'고 오판한다.
      2) 발을 쭉 편 도약 순간에는 부츠 끝이 발끝 뼈보다 더 아래로 나간다.
    실제로 발끝 뼈 기준으로 맞췄더니 걷기에서 부츠가 12cm 바닥에 박혔다."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    z = min((mesh.matrix_world @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    return z


def pct(xs, p):
    """정렬 후 p 분위. 한 프레임짜리 튀는 값에 안 끌려가려고 쓴다."""
    s = sorted(xs)
    return s[min(len(s) - 1, max(0, int(len(s) * p)))]


bpy.context.view_layer.update()
BIND_LOW = mesh_low()                 # 바인드 포즈(발이 바닥) 최저 z. 접지 기준선
print("바인드 포즈 메시 최저 z = %.4f" % BIND_LOW)


def purge_actions(keep):
    """keep 에 든 액션만 남기고 나머지를 지운다. 비교는 이름이 아니라 데이터블록으로."""
    keep = list(keep)
    for a in list(bpy.data.actions):
        if not any(a == k for k in keep):
            bpy.data.actions.remove(a)


def fcurves_of(act):
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


def audit_paths(act):
    """★T 포즈 함정 감사. 모든 fcurve 가 실제 존재하는 뼈를 가리키는지 센다.
    반환 (총 fcurve, 이름 안 맞아 고친 수, 그래도 못 찾은 수)."""
    names = set(b.name for b in arm.pose.bones)
    total = fixed = bad = 0
    for fc in fcurves_of(act):
        dp = fc.data_path
        if '"' not in dp:
            continue
        total += 1
        bn = dp.split('"')[1]
        if bn in names:
            continue
        # 이름이 다르면 여기서 고쳐야 한다(s9_meshy.fix_paths 와 같은 자리).
        # 이 스크립트는 전부 우리 리그 위에서 구우므로 여기 걸리면 버그다.
        bad += 1
    return total, fixed, bad


acts = {}
FPS = None

# ------------------------------------------- Idle / CombatIdle / Run / Attack
# 원본 애니메이션 FBX 를 우리 리그로 전신 리타게팅한다.
# 원본 팩의 애니메이션 4개를 **하나도 빠뜨리지 않고** 전부 굽는다.
for aname, clip in (("Idle", "infantry_guard_idle"),
                    ("CombatIdle", "infantry_combat_idle"),
                    ("Run", "infantry_combat_run"),
                    ("Attack", "infantry_combat_shoot")):
    src, f0, f1, tmp = AA.load(clip)
    # ★소스 액션을 즉시 리네임한다. 소스가 우리 액션 이름을 먼저 차지하면
    #   Blender 가 우리 쪽에 .001 을 붙이고, 이름 기반 정리에 지워진다
    #   (아래 purge_actions 는 데이터블록으로 비교하므로 이미 안전하지만,
    #    로그에서 어느 게 소스인지 바로 보이도록 이름도 갈라둔다).
    try:
        src.animation_data.action.name = "SRC_%s" % clip
    except Exception as e:
        print("  소스 액션 리네임 실패:", e)
    if FPS is None:
        FPS = sc.render.fps
        print("애니메이션 FBX 가 정한 fps =", FPS)
    # ---- 1차: 접지 보정량을 잰다 ----
    # ★애니메이션 FBX 4개는 저마다 **아마추어 오브젝트의 월드 높이가 다르다**
    #   (guard_idle 1.1802 / combat_idle 1.0432 / run 1.3418 / shoot 1.0419,
    #    모델은 1.2235). copy_pose 는 아마추어 **로컬** 공간에서 옮기므로 이
    #   오브젝트 높이 차이를 그대로 무시한다. 그 결과 shoot 은 발이 0.18 뜨고
    #   run 은 반대로 잠긴다. 소스 자체는 멀쩡하다(소스 발끝 최저 z 0.0009~0.0178).
    #   클립마다 '사이클 중 낮은 쪽 10분위'를 바인드 최저점에 맞추는 상수만큼
    #   몸 전체를 올리고 내린다. 클립 안의 움직임은 하나도 안 건드린다.
    #   최저값(0분위)이 아니라 10분위를 쓰는 이유: 달리기는 도약 순간 부츠 끝이
    #   한두 프레임 확 내려가는데 거기에 맞추면 정작 디딜 때 6~10cm 뜬다.
    lows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        rest()
        copy_pose_safe(src, ALL)
        lows.append(mesh_low())
    shift = BIND_LOW - pct(lows, 0.10)
    off = LOCAL_UP * shift

    # ---- 2차: 보정을 넣고 굽는다 ----
    act = new_action(aname)
    n_bone = 0
    dev = 0.0
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        rest()
        n_bone, d = copy_pose_safe(src, ALL, off)
        dev = max(dev, d)
        key(f - f0 + 1)               # 1부터 시작하도록 옮긴다
    acts[aname] = act
    print("[%s] <- %s  %d프레임, 뼈 %d개 리타게팅, 소스 최대 |scale-1| = %.6f"
          % (aname, clip, f1 - f0 + 1, n_bone, dev))
    print("     접지 보정: 메시 최저 %.4f~%.4f(10분위 %.4f) -> 바인드 %.4f "
          "(몸 전체 %+.4f 이동)"
          % (min(lows), max(lows), pct(lows, 0.10), BIND_LOW, shift))
    AA.drop(tmp)
    # 소스 FBX 가 들고 온 액션도 지운다.
    # ★이름이 아니라 **데이터블록 자체**로 비교한다. 이름으로 비교하면
    #   이름이 충돌해 Blender 가 .001 을 붙였을 때 우리 액션을 지워버린다
    #   (실제로 한 번 당했다: 검사 glb 의 "Walk" 가 먼저 자리를 차지하는 바람에
    #    우리가 구운 액션이 "Walk.001" 이 됐고 정리 루프가 그걸 지웠다).
    purge_actions(acts.values())

# ---------------------------------------------------------------- 소총 파지 자세 캡처
# Idle 1프레임의 **로컬** 회전/이동을 받아둔다. 로컬이라 척추가 움직이면 따라 움직인다.
arm.animation_data_clear()
arm.animation_data_create()
arm.animation_data.action = acts["Idle"]
try:
    sl = list(getattr(acts["Idle"], "slots", []))
    if sl:
        arm.animation_data.action_slot = sl[0]
except Exception:
    pass
sc.frame_set(1)
bpy.context.view_layer.update()
CARRY = {}
for b in arm.pose.bones:
    if any(b.name.endswith(p) for p in UPPER):
        CARRY[b.name] = (b.location.copy(), b.rotation_quaternion.copy())
print("소총 파지 자세 캡처: 상체 뼈 %d개" % len(CARRY))

# ---------------------------------------------------------------- Walk
# 원본 Run 을 **보폭·무릎높이·상하진폭을 줄이고 느리게 늘려** 걷기로 만든다.
# (다른 glb 에서 빌려오는 길은 전부 막혔다. 위 문서주석의 기록 참고.)
#
# 방법
#   1) Run 을 우리 리그로 리타게팅한 **로컬 회전/이동**을 프레임마다 뽑는다.
#   2) 그 값을 Idle 1프레임(중립 기립)과 슬러프로 섞는다. 섞는 비율 W.
#      W=1 이면 달리기 그대로, W=0 이면 가만히 서 있기. 중간이 '조심스러운 전진'.
#      이렇게 하면 보폭·무릎 높이·골반 상하가 **한꺼번에** 같은 비율로 줄어든다.
#   3) 25프레임 주기를 34프레임으로 늘려 케이던스를 낮춘다(달리기 2.4보/초 ->
#      걷기 1.8보/초). 소수 프레임 샘플링은 frame_set(정수, subframe=소수).
#   4) 마지막에 메시 최저점으로 접지 상수 보정.
# 같은 뼈대라 리타게팅 오차가 0 이고, 원본 Run 이 이미 제대로 접지돼 있어
# 발이 바닥을 뚫거나 뜨지 않는다.
W = 0.72
NW = 34

# Idle 1프레임의 로컬 값(전신). 위 CARRY 는 상체만이라 여기서 다시 전부 받는다.
arm.animation_data_clear()
arm.animation_data_create()
arm.animation_data.action = acts["Idle"]
try:
    sl = list(getattr(acts["Idle"], "slots", []))
    if sl:
        arm.animation_data.action_slot = sl[0]
except Exception:
    pass
sc.frame_set(1)
bpy.context.view_layer.update()
IDLE1 = {b.name: (b.location.copy(), b.rotation_quaternion.copy())
         for b in arm.pose.bones}

src, rf0, rf1 = None, 0, 0
src, rf0, rf1, tmp = AA.load("infantry_combat_run")
PER = rf1 - rf0                            # 실제 루프 주기(마지막 프레임 = 첫 프레임)
print("Walk 합성: Run %d..%d (주기 %d프레임) -> %d프레임, 섞는 비율 %.2f"
      % (rf0, rf1, PER, NW, W))


def walk_pose_at(i):
    """i 번째 출력 프레임의 포즈를 만든다(접지 보정 전)."""
    t = rf0 + i * (PER / float(NW - 1))
    sc.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
    bpy.context.view_layer.update()
    rest()
    copy_pose_safe(src, ALL)
    run_l = {b.name: (b.location.copy(), b.rotation_quaternion.copy())
             for b in arm.pose.bones}
    for b in arm.pose.bones:
        il, iq = IDLE1[b.name]
        rl, rq = run_l[b.name]
        b.location = il.lerp(rl, W)
        b.rotation_quaternion = iq.slerp(rq, W)
        b.scale = (1, 1, 1)
    # 팔·목·머리는 소총 파지로 고정한다. 달리기 팔을 반만 섞으면 총이 어정쩡하게
    # 흔들린다. Idle/Attack 과 팔 모양이 같아야 전환할 때 안 튄다.
    for bn, (loc, rot) in CARRY.items():
        pb = arm.pose.bones.get(bn)
        if pb:
            pb.location = loc
            pb.rotation_quaternion = rot
    bpy.context.view_layer.update()


def shift_root(dz):
    """골반(루트)만 월드 dz 만큼 올린다. 자식은 로컬 회전이라 FK 로 따라온다."""
    pb = arm.pose.bones["Bip001 Pelvis"]
    m = pb.matrix.copy()
    m.translation = m.translation + LOCAL_UP * dz
    pb.matrix = m
    pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


lows = []
for i in range(NW):
    walk_pose_at(i)
    lows.append(mesh_low())
z_shift = BIND_LOW - pct(lows, 0.10)
print("  보정 전 메시 최저 z %.4f ~ %.4f (진폭 %.4f = 키의 %.1f%%) -> 상수 %+.4f"
      % (min(lows), max(lows), max(lows) - min(lows),
         (max(lows) - min(lows)) / 2.605 * 100, z_shift))

act = new_action("Walk")
for i in range(NW):
    walk_pose_at(i)
    shift_root(z_shift)
    key(i + 1)
acts["Walk"] = act
AA.drop(tmp)
purge_actions(acts.values())
print("[Walk] <- infantry_combat_run 을 %.0f%% 로 줄이고 %d프레임으로 늘림"
      % (W * 100, NW))

# ---------------------------------------------------------------- 감사 + 마무리
for nm, a in acts.items():
    a.use_fake_user = True
    total, fixed, bad = audit_paths(a)
    print("  액션 %-7s fcurve %4d개 / 뼈 이름 수정 %d개 / **못 찾은 뼈 %d개**"
          % (nm, total, fixed, bad))
    assert bad == 0, "액션 %s 의 fcurve 가 없는 뼈를 가리킨다 -> T 포즈 난다" % nm

# 마지막 포즈가 남지 않게 Idle 을 걸어둔다
arm.animation_data_clear()
arm.animation_data_create()
arm.animation_data.action = acts["Idle"]
try:
    sl = list(getattr(acts["Idle"], "slots", []))
    if sl:
        arm.animation_data.action_slot = sl[0]
except Exception:
    pass
sc.frame_set(1)

if FPS:
    sc.render.fps = FPS
print("export fps =", sc.render.fps)

zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
tri = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print("원본 키 %.3f  삼각형 %d  버텍스 %d" % (H, tri, len(mesh.data.vertices)))


def bind_action(a):
    """액션을 아마추어에 건다. ★슬롯을 안 걸면 액션이 조용히 아무 일도 안 한다."""
    arm.animation_data_clear()
    arm.animation_data_create()
    arm.animation_data.action = a
    try:
        sl = list(getattr(a, "slots", []))
        if sl:
            arm.animation_data.action_slot = sl[0]
    except Exception:
        pass


# ---- 접지 표: 구운 액션을 실제로 재생하며 **변형 메시** 최저 z 를 잰다 ----
# 뜨거나 잠기면 여기서 잡힌다. Run 은 도약 프레임이 있어 위로 뜨는 게 정상이다.
print("접지 검사 (바인드 최저 z = %.4f, 키 %.3f)" % (BIND_LOW, H))
for nm in ("Idle", "CombatIdle", "Walk", "Run", "Attack"):
    a = acts[nm]
    bind_action(a)
    fr = (int(a.frame_range[0]), int(a.frame_range[1]))
    lo = []
    for f in range(fr[0], fr[1] + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        lo.append(mesh_low())
    print("  %-10s %3d프레임  최저 z %+.4f ~ %+.4f  "
          "바닥 대비 %+.4f ~ %+.4f (키의 %.1f%%)"
          % (nm, fr[1] - fr[0] + 1, min(lo), max(lo),
             min(lo) - BIND_LOW, max(lo) - BIND_LOW,
             (max(lo) - min(lo)) / H * 100))

bind_action(acts["Idle"])
sc.frame_set(1)
print("최종 액션:", sorted(a.name for a in bpy.data.actions))
for a in sorted(bpy.data.actions, key=lambda x: x.name):
    print("   %-7s %s  fake_user=%s" % (a.name,
                                        tuple(int(x) for x in a.frame_range),
                                        a.use_fake_user))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT, export_format="GLB", use_selection=False,
    export_animations=True, export_animation_mode="ACTIONS",
    export_nla_strips=False, export_bake_animation=True,
    export_frame_range=False, export_yup=True)
print("EXPORTED", OUT, os.path.getsize(OUT))
