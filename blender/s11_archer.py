# -*- coding: utf-8 -*-
"""Meshy 여성 궁수(glb 6개)를 게임용 단일 glb 로 합친다. s9_meshy.py 의 궁수판.

받은 것
  019fd1b2-... / Regular_Jump / Run_03 / Running / Walking / Walking_Woman
  여섯 파일 **전부 메시를 통째로** 들고 있다(5.5MB x 6). 뼈대는 동일하므로
  메시는 하나만 두고 액션만 모은다.

클립 선정 근거(실측·렌더로 비교, blender/renders/history/v43_archer 참고)
  Walk = Walking_Woman.  다른 후보 Walking 은 액션 이름부터 walking_man 이고,
    무릎을 굽혀 상체가 앞으로 수그러진다. Walking_Woman 은 골반이 0.19 높고
    (머리-골반 0.205H vs 0.178H) 상체가 곧게 서며 골반 상하 흔들림이 작다
    (0.0199H vs 0.0297H). 접지는 둘 다 정상(최저 z -0.038 / -0.040).
  Run  = Running.  Run_03 은 상체를 45도 가까이 앞으로 처박고(머리가 골반보다
    항상 0.12~0.14m 앞) 몸 전체가 지면에서 0.16 까지 떠올라 통통 튄다.
    Running 은 머리가 골반 위에 있고(±0.02) 부양은 0.074 로 얌전하며 팔을
    직각으로 접어 흔든다. 사이클도 16프레임(0.67초)이라 더 경쾌하다.
  Jump = ★점프가 두 개다. 게임에서 다시 굽지 않고 갈아끼워 보려고 **둘 다** 넣는다.
    Jump  = 019fd1b2(rigify_clip) 의 제자리 도약. 낮고 빠른 쪽.
    JumpB = Regular_Jump. 높고 느린 쪽(예전에 유일하게 쓰던 클립).
    둘 다 뿌리 스케일 오염 없음을 glb 직접 파싱으로 확인했다(2026-08-05).
    골반 수평 이동도 10~15cm 라 제자리 도약이 맞다(둘 다 루트 모션 아님).
  Attack = ★없다. 정체 불명 019fd1b2 파일은 활 쏘기가 아니라 **제자리 도약**
    이었다(웅크림 -> 도약, 지면 0.94 까지 뜸 -> 착지 -> 40프레임 정지).
    손이 골반보다 8cm 이상 올라간 적이 없어 활 자세일 수가 없다.
    그래서 Attack 은 여기서 직접 만든다(활 당기고 놓기).
    ★활은 몸 메시에 등짐으로 구워져 있었다(재질 1개, 아일랜드 1437개).
    2026-08-19(21차)에 **손에 드는 활을 붙이고 등짐 활은 지웠다.** 아래 두 절 참고.

★손에 드는 활 BW_bow (2026-08-19 추가. s10_shield.py 의 방패와 같은 자리)
  blender/bow_mesh.py 가 절차로 만들고 **왼손 뼈(Bip001 L Hand)** 에 웨이트 1.0 으로 묶는다.
  배치는 REST 눈대중이 아니라 L = M_pose⁻¹ @ target 을 푼다(s10 헤더가 정본).
  ★기준 포즈는 Idle 이 아니라 **Attack 만작(f11 = 클립 0.4167초)** 이다. 활은 쏠 때
    손에 있는 물건이고 그 프레임이 이 캐릭터의 캡처컷이다.
  ★왼손이 맞다는 실측: 만작에서 왼손이 앞으로 0.543m 나가고 오른손은 0.094m 다.
  ★이름은 BW_ 다. SW_ 는 main.js 가 칼 목록으로 모으고(3352) 칼날 셰이더까지 걸린다.
  ★키 정규화: main.js 는 SW_/SH_ 로 시작하지 않는 메시를 전부 모아 키를 잰다.
    BW_ 는 거기 안 걸리므로 활이 키 상자에 들어간다. 그래서 캔트를 -15도로 잡아
    **REST 자세 활 z 를 0.841~1.635 로** 몸통(0~1.700) 안에 넣었다. 아래 출력이 그걸 검산한다.
    (캔트 0도면 1.730 이라 몸통을 넘어 캐릭터가 1.7% 쪼그라든다)

★등짐 활 제거 (2026-08-19 추가)
  안 지우면 활이 두 개로 보인다(손에 하나, 등에 하나).
  재질로도(1개) 느슨한 조각으로도(3개) 못 가르고 **인덱스 연결성**으로만 갈린다.
  어느 아일랜드가 활인지는 blender/probe_bow_final.py 가 특정했다 -
  몸 둘레 여러 시점에서 광선을 쏴 맞은 면의 텍셀색을 읽어 "나무색 + 작은 조각 + 등 뒤"
  를 고른다. 결과는 blender/archer_backbow_verts.txt 에 **정점 인덱스**로 굳혀 뒀다.
  ★"등 뒤에서 가장 큰 아일랜드(158정점/0.817m)" 는 활이 아니라 **머리카락**이다.
    기하만 보면 긴 머리 가닥과 활대가 안 갈린다. 색을 봐야 갈린다(머리카락 #FDFCFC).
  Idle = ★019fd1b2 파일의 끝부분(정지해 선 자세)을 바탕으로 만든다.
    s9(탱커)는 걷기 첫 프레임을 썼는데 그건 다리를 벌린 중간자세다.
    이 파일 뒤쪽 40프레임은 팔을 내리고 가만히 선 자세라 Idle 바탕으로 낫다.

★뼈 이름을 Bip001 규칙으로 바꾼다
  우리 포즈 시스템(combo_poses.Poser.pb)과 게임 코드(main.js)가 전부
  "r hand", "l thigh" 같은 **부분 문자열**로 뼈를 찾는다.
  Meshy 이름(RightHand, LeftUpLeg)은 안 잡힌다.

★척추 주의: Meshy 는 Spine/Spine01/Spine02 세 개다. pb("spine") 은 첫 일치를
  반환하므로 셋 다 'spine' 을 넣으면 엉뚱한 걸 잡는다. 위 두 개는 Chest 로 부른다.

★Icosphere 를 지운다(s9 는 안 지웠다. 그게 탱커 키 버그의 원인이다)
  Meshy 가 반지름 1 짜리 정이십면체를 끼워 넣는다. main.js 는 SW_ 만 빼고
  전 메시로 박스를 재므로 이게 그대로 키에 들어간다. 몸(0~1.700) + 구(-1~1)
  = 2.700 이 되어, 목표 키 1.70 을 주면 실제 몸은 1.07 로 쪼그라들고
  position.y 보정 때문에 발이 공중에 뜬다. 지우면 키가 정확히 1.700 이다.

실행: blender --background --python s11_archer.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import combo_poses as CP
import bow_mesh as BM                                   # 손에 드는 활(21차)

SRC = os.path.join(ROOT, "incoming/meshy2/Meshy_AI_Moonshadow_Ranger_biped")
WEB = os.path.join(ROOT, "web")
BASE = "Meshy_AI_Moonshadow_Ranger_biped_Animation_%s_withSkin.glb"
MYSTERY = "019fd1b2-8fc3-74cc-97df-c4850ce84e10"

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


# ---- 1) Walking_Woman 을 기준으로 삼는다(메시 제공 + Walk) ----
objs = imp("Walking_Woman")
arm = next(o for o in objs if o.type == "ARMATURE")
# ★Icosphere 제거. 이유는 파일 상단 주석 참고.
for o in list(objs):
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        print("Icosphere 제거(키 계산 오염원)")
        bpy.data.objects.remove(o, do_unlink=True)
        objs.remove(o)
mesh = next(o for o in objs if o.type == "MESH")
print("기준 리그:", arm.name, "본", len(arm.data.bones), "/ 메시", mesh.name,
      len(mesh.data.polygons), "면")

# ---- 1.5) ★등에 구워진 활을 지운다 ----
# 손에 활을 들려주므로 안 지우면 활이 두 개다. 목록은 probe_bow_final.py 가 특정했고
# archer_backbow_verts.txt 에 정점 인덱스로 굳혀 뒀다(root 번호는 union-find 순서를
# 타서 못 믿는다. 정점 인덱스는 원본 파일이 같으면 항상 같다).
# bpy.ops 를 안 쓰고 bmesh 로 지운다 - 배경 실행에서 ops 는 컨텍스트를 탄다.
BOWF = os.path.join(ROOT, "blender/archer_backbow_verts.txt")
if os.path.exists(BOWF):
    import bmesh
    txt = [ln for ln in open(BOWF, encoding="utf-8") if not ln.startswith("#")]
    kill_ids = [int(x) for x in "".join(txt).strip().split(",") if x.strip()]
    nv0, np0 = len(mesh.data.vertices), len(mesh.data.polygons)
    # ★안전장치: 목록이 이 메시용인지 확인한다(다른 원본에 잘못 먹이면 몸에 구멍이 난다)
    if max(kill_ids) >= nv0:
        raise SystemExit("등짐 활 정점 목록이 이 메시와 안 맞는다(최대 %d >= 정점 %d)"
                         % (max(kill_ids), nv0))
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in kill_ids], context="VERTS")
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.update()
    print("등짐 활 제거: 정점 %d -> %d (-%d), 면 %d -> %d (-%d)"
          % (nv0, len(mesh.data.vertices), nv0 - len(mesh.data.vertices),
             np0, len(mesh.data.polygons), np0 - len(mesh.data.polygons)))
else:
    print("★등짐 활 목록 파일이 없다(%s). 등에 활이 남는다." % BOWF)

acts = {}
if arm.animation_data and arm.animation_data.action:
    acts["Walk"] = arm.animation_data.action

# ---- 2) 나머지는 액션만 가져오고 오브젝트는 버린다 ----
# MYSTERY 는 두 가지로 쓴다. (1) Idle 바탕 자세(_Rise), (2) 두 번째 점프(Jump).
# ★MYSTERY 파일에는 애니메이션이 두 개다: rigify_clip(75프레임 도약) 과
#   Armature|clip0|baselayer(2프레임 정지). 도약은 긴 쪽이다.
# ★액션 이름 충돌 함정: 임포트한 소스 액션이 "Jump" 같은 우리 이름을 먼저
#   차지하면 우리 액션이 조용히 Jump.001 이 된다. 들어오자마자 SRC_ 로 밀어둔다.
MYS_JUMP_SRC = None


def fresh_actions(pre_names):
    return [a for a in bpy.data.actions if a.name not in pre_names]


for tag, name in (("Running", "Run"), ("Regular_Jump", "JumpB"),
                  (MYSTERY, "_Rise")):
    pre = set(a.name for a in bpy.data.actions)
    got = imp(tag)
    fresh = fresh_actions(pre)
    for a in fresh:
        a.name = "SRC_" + a.name
    a2 = next(o for o in got if o.type == "ARMATURE")
    act = a2.animation_data.action if a2.animation_data else None
    print("  [%s] 새 액션 %d개 %s  / 아마추어에 붙은 것 = %s"
          % (tag, len(fresh), [a.name for a in fresh],
             act.name if act else None))
    if act:
        act.use_fake_user = True
        acts[name] = act
    if tag == MYSTERY:
        # 도약 클립 = 프레임 수가 가장 많은 것. _Rise 와 같은 데이터블록일 수
        # 있으므로(그러면 이름을 Jump 로 바꾸는 순간 _Rise 도 같이 바뀐다)
        # **복사본**을 따로 떠서 쓴다. 동일성은 데이터블록으로 비교한다.
        longest = max(fresh, key=lambda a: a.frame_range[1] - a.frame_range[0])
        same = (act is not None and longest == act)
        print("  [%s] 도약 클립 = %s (%d프레임) / _Rise 와 같은 데이터블록? %s"
              % (tag, longest.name,
                 int(round(longest.frame_range[1] - longest.frame_range[0])) + 1,
                 same))
        MYS_JUMP_SRC = longest.copy()
        MYS_JUMP_SRC.use_fake_user = True
        acts["Jump"] = MYS_JUMP_SRC
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
print("뼈 이름 변경 %d개" % n)
print("  ->", [b.name for b in arm.data.bones])

# ★★가장 중요한 함정
# Blender 는 뼈 이름을 바꿀 때 **그 아마추어에 현재 붙어 있는 액션**의 데이터 경로만
# 따라 고친다. Run/Jump/_Rise 는 **다른 아마추어**에서 가져온 뒤 그 아마추어를
# 지웠으므로, fcurve 경로가 아직 pose.bones["RightHand"] 를 가리킨다.
# 그대로 내보내면 그 클립을 재생할 때 **아무 뼈도 안 잡혀 T 포즈**가 된다.
# (증상: 걷기는 되는데 Shift 달리기 누르면 T 포즈)
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
# 기준 액션(Walk)만 0 개가 정상. 나머지가 0 이면 T 포즈 함정에 빠진 것이다.
if fix_paths(acts["Run"]) != 0:
    raise SystemExit("fix_paths 재실행에서 또 고쳐졌다 = 1차가 실패")


# ---- 4) 진단 도구: 스킨 적용된 메시의 최저 z(발이 뜨는지) ----
def low_z():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    mw = mesh.matrix_world
    z = min((mw @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    return z


def use(act):
    """액션을 붙인다. Blender 5 는 슬롯이 있어야 채널이 먹는다."""
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


# ---- 4.5) ★★Meshy 리타깃 잔재 제거: 뿌리 뼈에 박힌 스케일 ----
# 증상(2026-08-05): 게임에서 걷기 시작하면 캐릭터가 17.65% 부풀고 멈추면 줄었다.
# 원인: Walk(= Walking_Woman) 액션의 Bip001 Pelvis 에 스케일 1.1765 가 전 프레임
#   **상수로** 박혀 있었다(애니메이션이 아니라 그냥 상수). 이 리그는 뼈 24개가
#   전부 골반 하위라 골반 스케일이 스켈레톤 전체에 곱해진다.
#   Attack/Idle/Jump/Run 은 전부 1.0000~1.0000 이고 tank.glb, slayer.glb 도 정상.
#   1.1765 = 1/0.85. Walking_Woman 원본 리그와 이 리그의 크기 차이를 Meshy 가
#   뿌리 뼈 스케일 하나로 때운 흔적이다.
#
# ★스케일만 1.0 으로 내리면 안 된다(발이 뜬다)
#   glb 원본을 뜯어보니 Meshy 는 **골반의 translation 도 똑같이 1.1765 배** 해놨다.
#   Walk 골반 높이 108.8~114.2cm 는 레스트 골반 97.7cm 보다도 높아 애초에 말이 안 된다.
#   1.1765 로 나누면 92.5~97.1cm 로, Idle 96.1 / Run 87.3~95.5 / 레스트 97.7 과
#   같은 대역에 정확히 들어온다. 즉 걷기 클립 전체가 '지면 원점 기준 1.1765배 확대'였다.
#   그래서 스케일을 1 로 내리는 동시에 골반 위치도 1/1.1765 배 해야 한다.
#   그러면 회전은 하나도 안 건드리므로 **자세는 그대로**, 크기만 레스트 스켈레톤과
#   같아지고, 지면 원점 기준 균일 축소라 **발도 그대로 땅에 붙는다**.
#   (스케일만 내리면 다리가 15% 짧아진 만큼 발이 15cm 가까이 공중에 뜬다)
PELVIS = "Bip001 Pelvis"


def fcs_of(act):
    """Blender 4.4+ 는 액션이 레이어/스트립/채널백 구조라 act.fcurves 가 비어 있다.
    fix_paths 안에도 같은 코드가 있지만 그쪽은 손대지 말라는 지시라 따로 둔다."""
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
    """액션 안의 뼈 스케일 fcurve 를 뼈별 (최소, 최대) 로 모은다."""
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


def pelvis_track(act):
    """자기 검증용: 액션 전 프레임의 골반 armature 공간 위치를 뜬다."""
    use(act)
    out = []
    for f in range(int(round(act.frame_range[0])),
                   int(round(act.frame_range[1])) + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        out.append(arm.pose.bones[PELVIS].matrix.translation.copy())
    return out


def deflate_root_scale(act):
    """뿌리 뼈(골반)의 상수 스케일 k 를 1.0 으로 만들고 골반 위치를 1/k 로 줄인다."""
    sfc = [fc for fc in fcs_of(act)
           if fc.data_path == 'pose.bones["%s"].scale' % PELVIS]
    vals = [k.co.y for fc in sfc for k in fc.keyframe_points]
    if not vals:
        print("  골반 스케일 채널 없음 = 손댈 것 없음")
        return 1.0
    k = sum(vals) / len(vals)
    if max(vals) - min(vals) > 1e-4:
        # 상수가 아니라 진짜 애니메이션된 스케일이면 아래 보정식(균일 축소)이 안 맞는다.
        raise SystemExit("골반 스케일이 상수가 아니다(%.4f~%.4f). 보정식 재검토 필요"
                         % (min(vals), max(vals)))
    if abs(k - 1.0) < 1e-4:
        print("  골반 스케일 이미 1.0 = 손댈 것 없음")
        return 1.0
    s = 1.0 / k
    # ★Blender 의 포즈 본 location 은 월드 좌표가 아니라 **레스트 기준 뼈 로컬
    #   오프셋**이다. 그래서 fcurve 값에 그냥 s 를 곱하면 틀린다.
    #     armature 공간 골반 위치 p = rest + R @ loc   (뿌리 뼈라 부모가 없다)
    #     원하는 것: p' = s * p        (지면 원점 기준 균일 축소)
    #     => loc' = s*loc + (s-1) * R⁻¹ @ rest
    #   두 번째 항이 상수라 fcurve 값에 대한 1차식이고, 그래서 베지어 핸들 y 도
    #   같은 식으로 옮기면 곡선 모양이 그대로 유지된다.
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
        raise SystemExit("골반 location fcurve 가 없다. 보정할 대상이 없어 발이 뜬다.")
    for fc in lfc:
        off = c[fc.array_index]
        for kp in fc.keyframe_points:
            kp.co.y = kp.co.y * s + off
            kp.handle_left.y = kp.handle_left.y * s + off
            kp.handle_right.y = kp.handle_right.y * s + off
        fc.update()
    print("  골반 스케일 %.4f -> 1.0 / 골반 위치 x%.4f + (%.4f, %.4f, %.4f)"
          "  (scale fcurve %d, location fcurve %d)"
          % (k, s, c[0], c[1], c[2], len(sfc), len(lfc)))
    return k


print("\n[스케일 점검] 굽기 전")
for nm in sorted(acts):
    r = scale_ranges(acts[nm])
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-8s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))

# 아마추어 원점이 지면(월드 원점)에 있어야 '원점 기준 균일 축소'가 곧 접지 유지다.
print("아마추어 원점", tuple(round(x, 5) for x in arm.matrix_world.translation))
before = pelvis_track(acts["Walk"])
K = deflate_root_scale(acts["Walk"])
after = pelvis_track(acts["Walk"])
if K != 1.0:
    # 자기 검증: 전 프레임 세 성분 모두 정확히 1/K 배 위치로 줄었는가.
    # (아마추어가 회전돼 있을 수 있어 특정 축만 보지 않는다)
    rs = [a[i] / b[i] for a, b in zip(after, before)
          for i in range(3) if abs(b[i]) > 1e-5]
    print("  검증: 골반 위치 비율 %.5f ~ %.5f (기대 %.5f, 표본 %d개)"
          % (min(rs), max(rs), 1.0 / K, len(rs)))
    if max(abs(r - 1.0 / K) for r in rs) > 1e-3:
        raise SystemExit("골반 보정식이 안 맞는다. 위 비율이 1/K 가 아니다.")
    print("  골반 %s -> %s (첫 프레임)"
          % (tuple(round(x, 4) for x in before[0]),
             tuple(round(x, 4) for x in after[0])))

# 나머지 액션도 뿌리 스케일이 있으면 같은 처리를 한다(지금은 전부 1.0 이라 무동작).
# ★새로 들어온 Jump(019fd1b2) 도 여기서 같이 검사된다. glb 직접 파싱으로도
#   1.0000~1.0000 을 확인했지만 굽는 쪽에서도 한 번 더 걸러 둔다.
for nm in ("Run", "Jump", "JumpB", "_Rise"):
    r = scale_ranges(acts[nm])
    bad = {b: v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    if bad:
        print("[%s] 비정상 스케일 발견 %s" % (nm, bad))
        if set(bad) == {PELVIS}:
            deflate_root_scale(acts[nm])
        else:
            raise SystemExit("골반이 아닌 뼈에 스케일이 박혔다. 보정식이 다르다: %s"
                             % list(bad))


# ---- 5) Idle 바탕 자세를 _Rise 끝프레임(가만히 선 자세)에서 뜬다 ----
use(acts["_Rise"])
END = int(round(acts["_Rise"].frame_range[1]))
sc.frame_set(END)
bpy.context.view_layer.update()
print("Idle 바탕 = _Rise f%d, 메시 최저z %+.4f (0 근처여야 접지)" % (END, low_z()))
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
        slot = a.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = slot
    except Exception:
        pass
    return a


# ---- 6) Idle: 숨쉬기 루프 50프레임 ----
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
print("Idle 생성 (50프레임 숨쉬기)")

# ---- 7) Attack: 활 당기고 놓기. Meshy 가 안 줘서 직접 만든다 ----
# 오른손잡이 궁수 = 왼손이 활, 오른손이 시위.
# 방향은 전부 월드 (r=캐릭터 오른쪽, u=위, f=앞). combo_poses.ruf 규칙.
# 팔 각도는 AIM(본이 향할 방향)으로 준다. 뼈 로컬 축이 리그마다 달라
# 오일러 각을 직접 넣으면 재현이 안 되기 때문이다.
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H0 = max(zs) - min(zs)
ps = CP.Poser(arm, H0)

L_UA, L_FA = "l upperarm", "l forearm"
R_UA, R_FA = "r upperarm", "r forearm"
# (프레임, 척추 비틀기(도, 음수=오른어깨 뒤로), 왼위팔, 왼아래팔, 오른위팔, 오른아래팔)
# ★1차 시도의 실패와 수정(렌더로 확인):
#   - 만작에서 오른손이 눈높이까지 올라와 **얼굴을 가렸다**. 아래팔의 위 성분을
#     0.30 -> 0.10 으로 낮춰 턱 옆(신경 기준 위로 4cm)에 걸리게 했다.
#   - 발사 프레임에서 손이 얼굴 **앞으로** 지나갔다. 아래팔을 위-뒤로 돌려
#     손이 귀 뒤 위쪽으로 빠지게 했다(활 쏘고 손을 뒤로 털어내는 잔동작).
SHOT = [
    (1,   0.0, None, None, None, None),                      # 차렷(바탕 자세)
    (5,  -4.0, (0.10, -0.30, 0.95), (0.25, 0.25, 0.94),
     (0.55, -0.45, -0.35), (-0.45, 0.55, 0.70)),             # 활 들고 화살 메김
    (11, -10.0, (0.18, 0.02, 0.98), (0.30, 0.15, 0.94),
     (0.72, 0.12, -0.68), (-0.70, 0.10, 0.70)),              # 만작(가득 당김)
    (16, -11.0, (0.18, 0.02, 0.98), (0.30, 0.15, 0.94),
     (0.74, 0.14, -0.66), (-0.70, 0.10, 0.70)),              # 잠깐 멈춤(조준)
    (19,  -8.0, (0.16, 0.04, 0.99), (0.28, 0.15, 0.95),
     (0.55, 0.10, -0.83), (-0.25, 0.80, -0.55)),             # 발사(손이 귀 뒤로)
    (28,  0.0, None, None, None, None),                      # 복귀
]
atk = new_action("Attack")
for f, tw, lua, lfa, rua, rfa in SHOT:
    restore()
    ops = []
    if abs(tw) > 1e-6:
        ops.append(("spine", CP.Z, tw))
    for key, d in ((L_UA, lua), (L_FA, lfa), (R_UA, rua), (R_FA, rfa)):
        if d:
            ops.append((key, CP.AIM, d))
    if ops:
        ps.apply({"b": ops}, reset=False)
    bpy.context.view_layer.update()
    key_all(f)
    print("  Attack f%-3d 최저z %+.4f  오른손 %s" %
          (f, low_z(), tuple(round(x, 3) for x in ps.wpos("r hand"))))
acts["Attack"] = atk
print("Attack 생성 (28프레임 활쏘기)")

# ---- 7.5) ★손에 드는 활 BW_bow ----
# s10_shield.py 와 같은 방법. 다만 기준 포즈가 Idle 이 아니라 **Attack 만작**이다.
#   L = M_pose⁻¹ @ target 을 풀고 REST 에 M_rest @ L 로 굽는다. 스키닝이
#   M_pose @ M_rest⁻¹ 를 곱해 주므로 만작에서 정확히 target 이 된다.
BOW_ON = os.environ.get("BOW_ON", "1") != "0"     # ★롤백 스위치. 0 이면 빈손이다
DRAW_F = int(os.environ.get("BOW_DRAW_F", "11"))  # 만작 프레임(SHOT 표의 f11)
BOW_ROLL = math.radians(float(os.environ.get("BOW_ROLL", "-15")))
bow = None
if BOW_ON:
    A2W = arm.matrix_world
    # 몸통 바인드 포즈 상자(= main.js 가 키를 재는 상자). 활이 여기 안에 있어야 한다.
    bz = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
    BODY_Z = (min(bz), max(bz))
    HH = BODY_Z[1] - BODY_Z[0]

    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    M_rest = A2W @ arm.pose.bones["Bip001 L Hand"].matrix

    arm.data.pose_position = "POSE"
    use(atk)
    sc.frame_set(DRAW_F)
    bpy.context.view_layer.update()
    M_pose = A2W @ arm.pose.bones["Bip001 L Hand"].matrix

    def _wp(n):
        return (A2W @ arm.pose.bones[n].matrix).translation.copy()

    Lh, Rh, Lf = _wp("Bip001 L Hand"), _wp("Bip001 R Hand"), _wp("Bip001 L Forearm")
    draw_len = (Lh - Rh).length
    # ★활 쥔 손이 왼손인지 실측으로 확인한다(정면 = -Y 이므로 -y 가 큰 쪽이 앞).
    if -Lh.y <= -Rh.y:
        raise SystemExit("만작에서 왼손이 앞이 아니다(왼 %.3f / 오른 %.3f). "
                         "활 쥔 손을 다시 정해야 한다" % (-Lh.y, -Rh.y))
    print("[활] 만작 f%d 왼손앞 %.3f / 오른손앞 %.3f / 당긴거리 %.3f"
          % (DRAW_F, -Lh.y, -Rh.y, draw_len))

    # 기준 좌표계: ey = 시위를 당기는 방향(왼손 -> 오른손). 이렇게 잡아야
    #   시위 V 자의 꼭짓점이 만작에서 정확히 시위 손 자리에 온다.
    ey = (Rh - Lh).normalized()
    ez = (Vector((0, 0, 1)) - ey * Vector((0, 0, 1)).dot(ey)).normalized()
    ex = ey.cross(ez)
    # 손아귀는 손목 뼈보다 손끝 쪽으로 4.5cm(주먹이 활대를 감싼다)
    origin = Lh + (Lh - Lf).normalized() * 0.045
    # 캔트(-15도). ey 둘레 회전이라 화살·시위 관계는 안 깨진다.
    #   ★이 각이 REST 자세 활 위치를 정한다 = main.js 키 상자에 걸리느냐 마느냐.
    #     0도면 REST 활 z 가 1.730 으로 몸통(1.700)을 넘는다. -15도면 1.635 로 들어온다.
    binfo = BM.build(arm, "Bip001 L Hand", M_rest, M_pose, HH, draw_len,
                     basis=(ex, ey, ez), origin=origin,
                     extra_rot=Matrix.Rotation(BOW_ROLL, 4, "Y"))
    bow = binfo["obj"]
    bb = binfo["rest_bb"]
    print("[활] 길이 %.3f  끝물러남 %.3f  오늬 %.3f  정점 %d 삼각 %d"
          % (binfo["BL"], binfo["TIPY"], binfo["NOCK"], binfo["verts"], binfo["tris"]))
    print("[활] REST 바운딩 x %.3f~%.3f y %.3f~%.3f z %.3f~%.3f / 몸통 z %.3f~%.3f"
          % (bb + BODY_Z))
    if bb[4] < BODY_Z[0] - 1e-4 or bb[5] > BODY_Z[1] + 1e-4:
        print("★★활이 몸통 키 상자를 넘는다. main.js:3341 이 활까지 재서 캐릭터가"
              " %.1f%% 쪼그라든다. BOW_ROLL 로 눕히거나 main.js 에 BW_ 제외를 넣어야 한다."
              % ((1 - HH / (max(bb[5], BODY_Z[1]) - min(bb[4], BODY_Z[0]))) * 100))
    else:
        print("[활] 키 상자 안전 - main.js 수정 없이 그대로 렌더된다")
else:
    print("[활] BOW_ON=0 - 손에 활을 안 붙인다(빈손)")

# ---- 8) 안 쓰는 클립은 지운다. 남기면 파일만 커진다 ----
for a in bpy.data.actions:
    a.use_fake_user = True
# ★JumpB 를 빼먹으면 여기서 조용히 지워진다. 최종 액션은 6개다.
KEEP = {"Idle", "Walk", "Run", "Attack", "Jump", "JumpB"}
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        print("액션 제거:", a.name)
        bpy.data.actions.remove(a)
print("최종 액션:", sorted(a.name for a in bpy.data.actions))

# ---- 9) 크기 진단 ----
# ★클립별 스킨 메시의 최저z / 최고z. 골반 스케일 사고의 재발 감시용이다.
# Idle / Walk / Run 세 클립의 최고z(머리 높이)가 같아야 한다. 예전엔 Walk 만
# 17.65% 높았다. 최저z 는 셋 다 0 근처(접지)여야 한다.
# Jump 는 원래 뜨는 클립이라 최저z 가 양수인 게 정상이다.
def clip_z(act):
    """액션 전 프레임을 돌며 스킨 적용된 메시의 최저z / 최고z 를 잰다.
    Vector 를 프레임마다 3만개씩 만들면 느려서 z 행만 직접 곱한다."""
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
for nm in ("Idle", "Walk", "Run", "Attack", "Jump", "JumpB"):
    lo, hi, nf = clip_z(acts[nm])
    print("  %-8s %6d %+10.4f %+10.4f %10.4f" % (nm, nf, lo, hi, hi - lo))


# ---- 9.5) 점프 두 개의 구간 시각을 재기 위한 프레임별 표 ----
# 게임(main.js)은 점프 클립을 start / rise / fall / land / end 구간으로 나눠 쓴다.
# 클립마다 길이가 달라 초 단위 표가 필요하다. 골반 높이(도약 궤적)와
# 메시 최저z(발이 언제 땅에 닿는가)를 같이 뽑아야 구간이 정확히 보인다.
# 시각은 glb 기준(첫 키가 0초)이라 (f - f0) / fps 로 환산한다.
FPS = sc.render.fps / sc.render.fps_base
print("\n[점프 구간 측정용 프레임별 표]  scene fps = %.3f" % FPS)


def jump_table(nm):
    act = acts[nm]
    use(act)
    f0 = int(round(act.frame_range[0]))
    f1 = int(round(act.frame_range[1]))
    m = mesh.matrix_world
    a, b, c, d = m[2][0], m[2][1], m[2][2], m[2][3]
    print("  --- %s  f%d~f%d (%d프레임, %.3f초)"
          % (nm, f0, f1, f1 - f0 + 1, (f1 - f0) / FPS))
    print("      %6s %7s %9s %9s" % ("f", "t(초)", "골반z", "메시최저z"))
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = mesh.evaluated_get(dg)
        me = ev.to_mesh()
        nv = len(me.vertices)
        buf = [0.0] * (nv * 3)
        me.vertices.foreach_get("co", buf)
        lo = min(a * buf[i] + b * buf[i + 1] + c * buf[i + 2] + d
                 for i in range(0, nv * 3, 3))
        ev.to_mesh_clear()
        pz = (arm.matrix_world @ arm.pose.bones[PELVIS].matrix).translation.z
        print("      %6d %7.3f %9.4f %9.4f" % (f, (f - f0) / FPS, pz, lo))


for nm in ("Jump", "JumpB"):
    jump_table(nm)

print("\n[스케일 점검] 굽기 후")
# ★_Rise 는 8단계에서 bpy.data.actions 에서 지웠다. acts 딕셔너리에 남은 참조를
# 건드리면 ReferenceError 가 난다. 남긴 5개만 본다.
for nm in sorted(KEEP):
    r = scale_ranges(acts[nm])
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-8s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))

use(acts["Walk"])
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
tri = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print("바인드 포즈 키 %.3f  삼각형 %d  메시 %d개" % (H, tri,
      len([o for o in sc.objects if o.type == "MESH"])))

OUT = os.path.join(WEB, "archer.glb")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT, export_format="GLB", use_selection=False,
    export_animations=True, export_animation_mode="ACTIONS",
    export_nla_strips=False, export_bake_animation=True,
    export_frame_range=False, export_yup=True)
print("EXPORTED", OUT, os.path.getsize(OUT))
