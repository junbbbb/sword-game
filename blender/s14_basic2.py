# -*- coding: utf-8 -*-
"""Meshy 8k 게임캐릭터(basic2, glb 2개)를 게임용 단일 glb 로 굽는다 -> web/basic2.glb

s13_basic.py 의 후속. 함정 처리는 s13 과 같고, **Idle 을 ToonSoldier 원본
애니에서 리타게팅**하는 단계가 새로 붙었다.

받은 것
  Meshy_AI_game_character_8k_biped_Animation_Walking_withSkin.glb  (16.2MB)
  Meshy_AI_game_character_8k_biped_Animation_Running_withSkin.glb  (16.2MB)
  두 파일이 **각각 메시를 통째로** 들고 있다. 뼈(24본)·메시(6058정점 8370삼각형)·
  재질(4096x4096 PNG 1장)이 완전히 같아 메시는 하나만 두고 액션만 모은다.
  glb 직접 파싱 결과 파일당 애니메이션 **정확히 1개**(숨은 clip0 없음),
  뿌리 스케일 오염도 없음(scale 1.0000~1.0000).

만드는 액션: Idle / Walk / Run  (Attack 은 **안 넣는다**. 근거는 아래)
  Walk <- Meshy Walking
  Run  <- Meshy Running   (오너는 "걷기만 있다"고 알고 있었지만 달리기도 왔다)
  Idle <- ToonSoldier infantry_guard_idle 리타게팅 (몸통·다리·머리)
          + 팔만 걷기 중립 프레임으로 교체

★Idle 팔을 왜 갈아끼웠나 (렌더 비교 근거: renders/history/v53_basic2/cmpA_*, cmpB_*)
  guard_idle 은 **소총을 가슴에 걸친** 자세다. basic2 는 빈손이라 그대로 씌우면
  양 팔뚝을 배 앞에 수평으로 든 채 보이지 않는 총을 받쳐 든 그림이 된다
  (측면 렌더에서 특히 명확했다). 그래서 **팔 8뼈의 로컬 회전만** 걷기 사이클에서
  팔이 가장 중립인 프레임(f31, 레스트 대비 편차 0.106)의 값으로 덮었다.
  로컬 회전이라 몸통이 흔들리면 팔도 따라 움직인다(굳지 않는다).
  실측: 이렇게 해도 10.7초 동안 손이 키의 8.2~8.6% 만큼 움직인다.
  다리·골반·척추·목·머리는 guard_idle 그대로라 체중 이동과 호흡이 살아 있다.

★Attack 을 왜 안 넣었나 (렌더: renders/history/v53_basic2/rejected_Attack_*)
  infantry_combat_shoot 을 실제로 구워서 봤다. 세 가지 이유로 뺐다.
  1) 빈손이라 정면에서 '허공에 소총을 겨눈' 자세로 그대로 읽힌다.
  2) 동작이 거의 없다. 손 이동 범위가 키의 11.6~13.0% 뿐이다
     (같은 방식으로 잰 Walk 팔은 42.5~51.1%). 휘두름·찌름·예비동작이 없다.
  3) 첫 프레임과 마지막 프레임 차이가 키의 0.12% 다 = **반복 사격용 루프**이지
     시작과 끝이 있는 단발 동작이 아니다. 게임이 한 번 재생하면 아무 일도
     안 일어난 것처럼 보인다.
  게다가 웅크린 자세라 이 클립만 캐릭터가 8cm 낮아진다(최고z 1.3584 vs Idle 1.3947).
  게임에 없는 클립 방어 코드가 이미 있으므로 억지로 넣지 않는다.
  다시 보고 싶으면 WITH_ATTACK=1 로 구우면 된다.

★★리타게팅 방식: '레스트 델타'다. 절대 행렬 복사가 아니다
  s12_soldier.py 는 소스(애니 FBX)와 대상(모델 FBX)이 **같은 ToonSoldier 리그**라
  아마추어 공간 절대 행렬을 통째로 복사해도 됐다. 여기는 대상이 Meshy 리그다.
  glTF 는 뼈 축·roll·길이를 저장하지 않아 임포터가 임의로 정하므로
  **뼈 로컬 축이 소스와 완전히 다르다**(실측: 레스트 축각차 84~178도).
  절대 행렬을 넣으면 딱 그만큼 뒤틀린다.

  그래서
      D = R_world(애니FBX 뼈, 프레임 f) @ R_world(ToonSoldier **모델** 레스트 뼈)^-1
      목표 = D @ R_world(Meshy 레스트 뼈)
  로 '레스트에서 얼마나 돌아갔나'만 옮긴다. 축 규약과 무관하고, 두 레스트가
  같은 T 포즈이기만 하면 성립한다.

  ★기준 레스트는 **모델 FBX** 여야 한다. 애니 FBX 는 저마다 자기 레스트를 들고
    오는데 그게 T 포즈가 아니다(실측: 모델 레스트와 위팔 48.6도 차이).
    애니 FBX 자기 레스트로 델타를 뽑으면 팔이 48도 어긋난다.

  ★두 리그가 같은 월드 프레임인지 먼저 쟀다(scratch probe):
    - 레스트 관절 방향 각도차 허벅지 5.4 / 종아리 5.3 / 위팔 5.3 / 팔뚝 7.3 /
      쇄골 6.8 / 목 20.7 도. 목만 조금 크다(Meshy 목은 곧고 병사는 15도 숙임).
      이 차이는 '각자 자기 레스트를 유지한 채 움직임만 받는다'는 뜻이라 문제 없다.
    - 정면: Meshy (0.11,-0.99), Soldier (0.00,-1.00), 애니FBX (0.04,-1.00). 전부 -Y.
    - 왼쪽축: 둘 다 +X.
    => 월드 회전 보정 불필요.

  ★스케일 폭주 방지: pb.matrix 에 직접 쓰지 않는다(과거 손이 39배).
    부모부터 순서대로 **matrix_basis** 를 해석적으로 계산해 넣는다.
      pose(b) = pose(parent) @ rest(parent)^-1 @ rest(b) @ basis(b)
    basis 는 **순수 회전**(이동 0, 스케일 1)이라 스케일이 섞일 여지 자체가 없다.
    골반만 이동을 준다. 자식은 FK 로 따라온다.
    ★부수 효과로 뼈마다 view_layer.update() 를 부를 필요가 없어져 빠르다
      (322프레임 x 24뼈 = 15,456 회 -> 프레임당 1회).
    ★해석식이 맞는지 프레임마다 Blender 평가값과 대조해 최대 오차를 찍는다.

★척추 뼈 수가 다르다
  Meshy: Pelvis -> Chest2 -> Chest -> Spine -> {Clavicle, Neck}  (척추 3마디)
         ※ Meshy 원본 이름이 Spine02 가 제일 아래다. 헷갈리기 쉽다.
  Soldier: Pelvis -> Spine -> Neck                               (척추 1마디)
  병사의 Spine 델타를 Meshy 척추 **세 개 모두**에 준다. 절대 회전을 지정하는
  방식이라 세 배로 굽지 않고 상체가 병사처럼 한 덩어리로 돈다.

★아마추어 오브젝트 월드 높이가 FBX 마다 다르다
  guard_idle 1.1802 / combat_shoot 1.0432 / 모델 1.2235.
  우리는 델타만 쓰므로 회전은 영향이 없지만 골반 **이동**은 영향을 받는다.
  그래서 골반 이동도 클립 평균을 빼 상대값으로 쓰고, 마지막에 s12 방식으로
  클립별 접지 보정(메시 최저점 10분위를 바인드에 맞춤)을 한 번 더 건다.

★함정 (s13 과 동일. 하나라도 밟으면 조용히 망가진다)
  1) fix_paths: 다른 파일에서 가져온 액션은 옛 뼈 이름을 계속 가리켜 T 포즈가 된다
  2) 뿌리 뼈 스케일 오염 (Meshy 가 골반에 스케일을 박는 경우가 있다)
  3) 액션 슬롯(Blender 4.4+): 슬롯 없으면 액션이 조용히 아무 일도 안 한다
  4) use_fake_user: 안 켜면 export 에서 조용히 빠진다
  5) 소스 액션 이름 충돌 -> 들어오자마자 SRC_ 접두사
  6) 한 파일에 클립이 여러 개일 수 있다 -> 파일별 액션 수를 찍는다
  7) 뼈 length 를 믿지 마라 -> 머리 좌표 사이 거리로 잰다
  8) Icosphere: glTF **임포터**가 뼈 표시용으로 만드는 반지름 1 구. glb 엔 없다.
     안 지우면 게임이 전 메시로 박스를 재므로 키가 망가진다.
  9) ★fps: FBX 임포터는 씬 fps 를 자기 값으로 덮어쓴다. glb 를 24fps 로 읽고
     30fps 로 내보내면 걷기가 25% 빨라진다. 그래서 **아무것도 임포트하기 전에**
     fps 를 30 으로 고정한다(Meshy 원본 키 간격 0.0333초 = 정확히 30fps,
     ToonSoldier FBX 도 30fps).

실행: blender -b -P blender/s14_basic2.py
손잡이(환경변수)
  TEX_SIZE / TEX_FORMAT / TEX_QUALITY : 텍스처 축소·포맷
  OUT_GLB   : 결과 경로(비교 굽기용)
  IDLE_SRC  : retarget(기본) | breath   ... 리타게팅 실패 시 합성 숨쉬기로 폴백
  IDLE_ARMS : walk(기본) | retarget | both
              both 면 비교용으로 IdleB(걷기팔) 액션을 하나 더 굽는다(A/B 렌더용).
  IDLE_LEN  : 0(기본, 322프레임 전부) 또는 자를 프레임 수
              ★전부 쓰는 근거: f322 == f1 이라 이음새가 정확히 0 이다.
                앞부분만 자르면 어디서 끊어도 이음새가 키의 1.3~6.0% 생겨
                루프마다 눈에 띄게 튄다(60/90/120/150/180/240 전부 확인).
                활동량도 앞쪽에 몰려 있지 않다. 머리 움직임은 오히려
                f121~241 구간이 제일 크다(체중 이동 + 두리번).
                용량 비용도 거의 없다. 322프레임 클립 하나가 약 50KB 다
                (익스포터가 값이 안 변하는 채널을 접는다).
  WITH_ATTACK : 0(기본, 안 넣는다) | 1
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import asset_anim as AA  # noqa: E402

SRC = os.path.join(ROOT, "incoming/meshy4/Meshy_AI_game_character_8k_biped")
WEB = os.path.join(ROOT, "web")
BASE = "Meshy_AI_game_character_8k_biped_Animation_%s_withSkin.glb"
MODEL_FBX = os.path.join(AA.PACK, "model/ToonSoldier_WW2_demo.FBX")

# ---- 텍스처 굽기 손잡이 ----
# ★basic(s13)에서 얻은 결론: 4096 PNG 는 glb 25.2MB, 2048 JPEG q90 은 0.89MB.
#   게임 거리·최대 줌에서 화질 차이가 안 보였다. basic2 도 같은 설정으로 간다.
# ★알파 확인(필수): 이 텍스처는 PNG colortype **6 = RGBA** 라 알파 채널이 있다.
#   basic(colortype 2)과 다르다. 그래서 실제로 쓰이는지 직접 뜯어 봤다.
#     - 재질 alphaMode = OPAQUE  (glTF 규격상 알파를 **무시**한다)
#     - 알파 < 255 인 픽셀이 1677만 중 34개, 최소값도 164(완전 투명 0 이 없다)
#     - 게임(main.js)은 재질을 MeshToonMaterial({map}) 로 갈아끼워 불투명 처리
#   => 잃을 정보가 없으므로 JPEG 안전.
TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_FORMAT = os.environ.get("TEX_FORMAT", "JPEG").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "basic2.glb")
IDLE_SRC = os.environ.get("IDLE_SRC", "retarget")
IDLE_ARMS = os.environ.get("IDLE_ARMS", "walk")
IDLE_LEN = int(os.environ.get("IDLE_LEN", "0"))
WITH_ATTACK = os.environ.get("WITH_ATTACK", "0") == "1"

# Meshy 이름 -> 우리 규칙. 순서 중요(긴 것부터 매칭)
# ★포즈 시스템과 게임 코드가 "r hand", "l thigh" 같은 **부분 문자열**로 뼈를 찾는다.
#   Meshy 이름(RightHand, LeftUpLeg)은 안 잡힌다.
# ★척추 주의: Spine/Spine01/Spine02 중 위 두 개를 Chest/Chest2 로 부른다.
#   셋 다 'spine' 을 넣으면 pb("spine") 이 엉뚱한 걸 잡는다.
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

# 우리(Meshy) 뼈 -> ToonSoldier 뼈. 이름이 같은 건 그대로, 없는 건 대응을 지정한다.
# 척추 3마디는 전부 병사 Spine 의 델타를 받는다(위 문서주석 참고).
# HeadNub/HeadFront 는 머리에 붙은 표식이라 Head 델타를 그대로 받는다.
RETARGET_MAP = {
    "Bip001 Pelvis": "Bip001 Pelvis",
    "Bip001 Chest2": "Bip001 Spine",
    "Bip001 Chest": "Bip001 Spine",
    "Bip001 Spine": "Bip001 Spine",
    "Bip001 Neck": "Bip001 Neck",
    "Bip001 Head": "Bip001 Head",
    "Bip001 HeadNub": "Bip001 Head",
    "Bip001 HeadFront": "Bip001 Head",
}
for s in ("L", "R"):
    for p in ("Clavicle", "UpperArm", "Forearm", "Hand",
              "Thigh", "Calf", "Foot", "Toe0"):
        n = "Bip001 %s %s" % (s, p)
        RETARGET_MAP[n] = n

ARM_BONES = tuple("Bip001 %s %s" % (s, p) for s in ("L", "R")
                  for p in ("Clavicle", "UpperArm", "Forearm", "Hand"))
PELVIS = "Bip001 Pelvis"

# ---------------------------------------------------------------- 씬 준비
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
print("빈 씬 기본 fps =", sc.render.fps)
# ★함정 9: 임포트 전에 30 으로 고정한다.
sc.render.fps = 30
sc.render.fps_base = 1.0
print("fps 를 30 으로 고정(Meshy 키 간격 0.0333초 = 30fps)")


def imp(tag):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, BASE % tag))
    return [o for o in sc.objects if o.name not in before]


# ---- 1) Walking 을 기준으로 삼는다(메시 제공 + Walk) ----
objs = imp("Walking")
arm = next(o for o in objs if o.type == "ARMATURE")
for o in list(objs):
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        print("Icosphere 제거(키 계산 오염원. glb 엔 없고 임포터가 만든 것)")
        bpy.data.objects.remove(o, do_unlink=True)
        objs.remove(o)
mesh = next(o for o in objs if o.type == "MESH")
print("기준 리그:", arm.name, "본", len(arm.data.bones), "/ 메시", mesh.name,
      len(mesh.data.polygons), "면")
print("glTF 임포트 후 fps =", sc.render.fps)

acts = {}
if arm.animation_data and arm.animation_data.action:
    acts["Walk"] = arm.animation_data.action
    print("  [Walking] 아마추어에 붙은 액션 = %s (%.1f~%.1f 프레임)"
          % (acts["Walk"].name, acts["Walk"].frame_range[0],
             acts["Walk"].frame_range[1]))

# ---- 2) Running 은 액션만 가져오고 오브젝트는 버린다 ----
# ★함정 5: 소스 액션이 "Run" 을 먼저 차지하면 우리 액션이 조용히 Run.001 이 되고
#   이름 기반 정리 루프가 그걸 지운다. 들어오자마자 SRC_ 로 민다.
# ★함정 6: 한 파일에 클립이 여러 개일 수 있다(궁수는 한 파일에 2개였다).
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


# ★★함정 1: Blender 는 뼈 이름을 바꿀 때 **그 아마추어에 현재 붙어 있는 액션**의
#   데이터 경로만 고친다. Run 은 다른 아마추어에서 가져온 뒤 그 아마추어를 지웠으므로
#   fcurve 가 아직 pose.bones["RightHand"] 를 가리킨다. 그대로 내보내면 그 클립을
#   재생할 때 아무 뼈도 안 잡혀 **T 포즈**가 된다.
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


print("\n[fix_paths] 기준 액션(Walk)만 0 개가 정상. Run 이 0 이면 T 포즈 함정이다")
for nm in list(acts):
    acts[nm].name = nm
    acts[nm].use_fake_user = True
    print("  액션 %-8s fcurve 경로 %4d개 수정" % (nm, fix_paths(acts[nm])))
if fix_paths(acts["Run"]) != 0:
    raise SystemExit("fix_paths 재실행에서 또 고쳐졌다 = 1차가 실패")


# ---- 4) 진단 도구 ----
def use(act):
    """액션을 붙인다. ★함정 3: Blender 4.4+ 는 슬롯이 있어야 채널이 먹는다."""
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def mesh_low():
    """**변형된 메시**의 최저 z(월드). 접지 판정은 이걸로 해야 한다.
    발끝 뼈로 재면 뒤꿈치 착지·발등 폄에서 부츠 끝을 놓친다(s12 주석 참고)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    m = mesh.matrix_world
    a, b, c, d = m[2][0], m[2][1], m[2][2], m[2][3]
    nv = len(me.vertices)
    buf = [0.0] * (nv * 3)
    me.vertices.foreach_get("co", buf)
    z = min(a * buf[i] + b * buf[i + 1] + c * buf[i + 2] + d
            for i in range(0, nv * 3, 3))
    ev.to_mesh_clear()
    return z


def pct(xs, p):
    """정렬 후 p 분위. 한 프레임짜리 튀는 값에 안 끌려가려고 쓴다."""
    s = sorted(xs)
    return s[min(len(s) - 1, max(0, int(len(s) * p)))]


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


# ---- 4.5) ★★함정 2: 뿌리 뼈에 박힌 스케일 ----
# 궁수 Walking_Woman 은 Bip001 Pelvis 에 스케일 1.1765 가 전 프레임 상수로 박혀
# 걷기만 하면 17.65% 부풀었다. 이 리그도 뼈 24개가 전부 골반 하위다.
# basic2 는 glb 직접 파싱(probe_glbscale.py)에서 두 파일 다 1.0000~1.0000 이지만
# 굽는 쪽에서도 한 번 더 거른다.
# ★보정은 '스케일 1.0 + 골반 translation 을 같은 배율로 축소' 여야 한다.
#   스케일만 내리면 다리가 짧아진 만큼 발이 뜬다.
def deflate_root_scale(act):
    sfc = [fc for fc in fcs_of(act)
           if fc.data_path == 'pose.bones["%s"].scale' % PELVIS]
    vals = [k.co.y for fc in sfc for k in fc.keyframe_points]
    if not vals:
        print("  골반 스케일 채널 없음 = 손댈 것 없음")
        return 1.0
    k = sum(vals) / len(vals)
    if max(vals) - min(vals) > 1e-4:
        raise SystemExit("골반 스케일이 상수가 아니다(%.4f~%.4f)" % (min(vals), max(vals)))
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


print("\n[스케일 점검] 굽기 전")
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

# ---- 5) 레스트 기준값 캡처 ----
for b in arm.pose.bones:
    b.rotation_mode = "QUATERNION"          # 쿼터니언 커브에 키를 찍으려면 필수
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
BIND_LOW = mesh_low()
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
TRI = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print("\n[레스트(바인드 T포즈)] 메시 z %.4f ~ %.4f / 키 %.4f / 삼각형 %d"
      % (min(zs), max(zs), H, TRI))
arm.data.pose_position = "POSE"

A2W = arm.matrix_world.copy()
A2W_R = A2W.to_3x3()
A2W_R.normalize()                            # 순수 회전(우리 리그는 사실상 항등)
A2W_R_INV = A2W_R.inverted()
# 레스트: 아마추어 공간 / 월드 회전
REST_ARM = {b.name: b.matrix_local.copy() for b in arm.data.bones}
REST_W_ROT = {}
for b in arm.data.bones:
    m = (A2W @ b.matrix_local).to_3x3()
    m.normalize()
    REST_W_ROT[b.name] = m
# 부모 우선 순서(깊이순)
ORDER = []
for b in arm.pose.bones:
    d, x = 0, b
    while x.parent:
        d += 1
        x = x.parent
    ORDER.append((d, b.name))
ORDER.sort()
ORDER = [n for _, n in ORDER]
PARENT = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
REST_PELVIS_W = (A2W @ arm.data.bones[PELVIS].head_local).copy()
REST_ANKLE_W = (A2W @ arm.data.bones["Bip001 L Foot"].head_local).copy()
LEG_DST = REST_PELVIS_W.z - REST_ANKLE_W.z
print("  골반 높이 %.4f / 발목 높이 %.4f / 다리 길이 %.4f"
      % (REST_PELVIS_W.z, REST_ANKLE_W.z, LEG_DST))

# ---- 6) ToonSoldier 모델 FBX 의 레스트(리타게팅 기준) ----
# ★애니 FBX 의 레스트가 아니라 **모델 FBX** 의 레스트(T 포즈)를 기준으로 써야 한다.
#   애니 FBX 는 저마다 자기 레스트를 들고 오는데 T 포즈가 아니다(위팔 48.6도 차이).
before = set(o.name for o in sc.objects)
bpy.ops.import_scene.fbx(filepath=MODEL_FBX)
solobjs = [o for o in sc.objects if o.name not in before]
sol = next(o for o in solobjs if o.type == "ARMATURE")
SOL_W_ROT = {}
for b in sol.data.bones:
    m = (sol.matrix_world @ b.matrix_local).to_3x3()
    m.normalize()
    SOL_W_ROT[b.name] = m
SOL_PELVIS_W = (sol.matrix_world @ sol.data.bones[PELVIS].head_local).copy()
SOL_ANKLE_W = (sol.matrix_world @ sol.data.bones["Bip001 L Foot"].head_local).copy()
LEG_SRC = SOL_PELVIS_W.z - SOL_ANKLE_W.z
K_TRANS = LEG_DST / LEG_SRC                  # 골반 이동 진폭 환산 배율
print("\n[ToonSoldier 모델 레스트] 본 %d / 골반 %.4f / 발목 %.4f / 다리 %.4f"
      % (len(sol.data.bones), SOL_PELVIS_W.z, SOL_ANKLE_W.z, LEG_SRC))
print("  골반 이동 환산 배율 K = 다리길이비 %.4f" % K_TRANS)
miss = [k for k, v in RETARGET_MAP.items() if v not in SOL_W_ROT]
if miss:
    raise SystemExit("매핑 대상이 병사 리그에 없다: %s" % miss)
# 모델 FBX 는 레스트 수치만 필요하다. 오브젝트는 바로 버린다(glb 에 딸려나가면 안 된다).
for o in solobjs:
    bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    if a.name not in ("Walk", "Run"):
        print("  모델 FBX 가 딸고 온 액션 제거:", a.name)
        bpy.data.actions.remove(a)
print("FBX 임포트 후 fps =", sc.render.fps)
if sc.render.fps != 30:
    print("  ★fps 가 바뀌었다. 30 으로 되돌린다")
    sc.render.fps = 30


# ---- 7) 리타게팅 엔진 ----
def rest_pose():
    for b in arm.pose.bones:
        b.location = (0, 0, 0)
        b.rotation_quaternion = (1, 0, 0, 0)
        b.scale = (1, 1, 1)


def retarget_frame(src, pelvis_world, chk=False):
    """소스 리그의 **현재 프레임** 포즈를 우리 리그로 옮긴다.

    - 회전: 레스트 델타(D = 소스포즈 @ 소스레스트^-1)를 우리 레스트에 곱한다.
    - 이동: 골반만 준다. 자식은 FK 로 따라온다.
    - basis 를 해석적으로 계산해 넣으므로 뼈마다 depsgraph 갱신이 필요 없다.
        pose(b) = pose(parent) @ rest(parent)^-1 @ rest(b) @ basis(b)
    chk=True 면 Blender 평가값과 대조해 최대 오차를 돌려준다(해석식 자기검증).
    """
    smap = {b.name: b for b in src.pose.bones}
    S2W = src.matrix_world
    pose = {}
    for bn in ORDER:
        sn = RETARGET_MAP.get(bn)
        sb = smap.get(sn) if sn else None
        if sb is None:
            # 대응이 없으면 부모의 델타를 그대로 물려받는다(몸이 끊기지 않게).
            Rw = REST_W_ROT[bn].copy()
        else:
            m = (S2W @ sb.matrix).to_3x3()
            m.normalize()
            Rw = m @ SOL_W_ROT[sn].inverted() @ REST_W_ROT[bn]
        Ra = A2W_R_INV @ Rw                  # 아마추어 공간 회전
        p = PARENT[bn]
        if p is None:
            t = A2W.inverted() @ pelvis_world
            M = Matrix.Translation(t) @ Ra.to_4x4()
            basis = REST_ARM[bn].inverted() @ M
        else:
            P = pose[p] @ REST_ARM[p].inverted() @ REST_ARM[bn]
            Pr = P.to_3x3()
            Pr.normalize()
            basis = (Pr.inverted() @ Ra).to_4x4()   # 순수 회전. 이동 0, 스케일 1
            M = P @ basis
        pose[bn] = M
        pb = arm.pose.bones[bn]
        pb.matrix_basis = basis
    err = 0.0
    if chk:
        # ★오차는 반드시 **월드 단위**로 재라. pb.matrix 는 아마추어 공간이고
        #   이 리그는 아마추어 스케일이 0.01 이라(캐릭터가 143.7 단위) 같은 수치가
        #   100배 커 보인다. 처음에 이걸 잊고 임계값을 잡았다가 8마이크로미터짜리
        #   부동소수 오차에 스크립트가 멈췄다.
        bpy.context.view_layer.update()
        for bn in ORDER:
            a = (A2W @ arm.pose.bones[bn].matrix).translation
            b = (A2W @ pose[bn]).translation
            err = max(err, (a - b).length)
    return err


def bake_retarget(name, clip, parts_all=True, nframes=0):
    """애니 FBX 클립 하나를 우리 리그로 굽는다. 반환 (액션, 정보 dict)."""
    src, f0, f1, tmp = AA.load(clip)
    try:
        src.animation_data.action.name = "SRC_%s" % clip
    except Exception as e:
        print("  소스 액션 리네임 실패:", e)
    if nframes and nframes < (f1 - f0 + 1):
        f1 = f0 + nframes - 1
    S2W = src.matrix_world
    print("\n[%s] <- %s  프레임 %d~%d (%d장), 소스 아마추어 z %.4f"
          % (name, clip, f0, f1, f1 - f0 + 1, S2W.translation.z))

    # ---- 1차: 골반 궤적 평균과 접지 보정량을 잰다 ----
    # ★애니 FBX 마다 아마추어 월드 높이가 다르다(guard 1.18 / shoot 1.04 / 모델 1.22).
    #   절대 위치를 그대로 쓰면 그 클립만 최대 18cm 뜬다. 평균을 빼 상대값으로 쓴다.
    praw = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        praw.append((S2W @ src.pose.bones[PELVIS].matrix).translation.copy())
    pmean = Vector((sum(p.x for p in praw) / len(praw),
                    sum(p.y for p in praw) / len(praw),
                    sum(p.z for p in praw) / len(praw)))
    lows = []
    maxerr = 0.0
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        rest_pose()
        pw = REST_PELVIS_W + (praw[i] - pmean) * K_TRANS
        maxerr = max(maxerr, retarget_frame(src, pw, chk=(i % 40 == 0)))
        bpy.context.view_layer.update()
        lows.append(mesh_low())
    shift = BIND_LOW - pct(lows, 0.10)
    print("  해석식 자기검증: Blender 평가값과 뼈 위치 최대 오차 %.7f 월드단위 "
          "(= 키의 %.5f%%)" % (maxerr, maxerr / H * 100))
    print("  접지 보정: 메시 최저 %.4f~%.4f (10분위 %.4f) -> 바인드 %.4f (몸 전체 %+.4f)"
          % (min(lows), max(lows), pct(lows, 0.10), BIND_LOW, shift))
    # 키의 0.01%(1.44m 기준 0.14mm)를 넘으면 해석식이 틀린 것이다.
    if maxerr > H * 1e-4:
        raise SystemExit("해석식 FK 가 Blender 평가와 다르다. 리타게팅 신뢰 불가")

    # ---- 2차: 보정을 넣고 굽는다 ----
    act = new_action(name)
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        rest_pose()
        pw = REST_PELVIS_W + (praw[i] - pmean) * K_TRANS + Vector((0, 0, shift))
        retarget_frame(src, pw)
        bpy.context.view_layer.update()
        for b in arm.pose.bones:
            b.keyframe_insert("location", frame=i + 1)
            b.keyframe_insert("rotation_quaternion", frame=i + 1)
            b.keyframe_insert("scale", frame=i + 1)
    AA.drop(tmp)
    for a in list(bpy.data.actions):
        if a.name.startswith("SRC_infantry"):
            bpy.data.actions.remove(a)
    return act, dict(nf=f1 - f0 + 1, shift=shift, err=maxerr,
                     lo=min(lows), hi=max(lows))


def new_action(name):
    arm.animation_data_clear()
    arm.animation_data_create()
    a = bpy.data.actions.new(name)
    a.use_fake_user = True                   # ★함정 4
    arm.animation_data.action = a
    try:
        # ★함정 3: 슬롯이 없으면 액션이 조용히 아무 일도 안 한다
        slot = a.slots.new(id_type="OBJECT", name="S")
        arm.animation_data.action_slot = slot
    except Exception as e:
        print("  slot 생성 실패(구버전?):", e)
    return a


# ---- 8) 걷기 프레임 표: '팔이 가장 중립인' 프레임을 고른다 ----
# 캐릭터는 -Y 를 본다(headfront 가 코 쪽이고 -Y 에 있다). 발.y 가 작을수록 앞.
# 팔 흔들림은 '레스트에서 손이 골반보다 얼마나 뒤(+y)에 있는가' 를 기준선으로 잰다.
# ★걷기 사이클에서 양팔은 180도 반대 위상이라 '양팔이 동시에 완전 중립' 인 프레임은
#   존재하지 않는다. 편차 합이 최소인 프레임을 고른다.
use(acts["Walk"])
WF0 = int(round(acts["Walk"].frame_range[0]))
WF1 = int(round(acts["Walk"].frame_range[1]))


def wp(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return (arm.matrix_world @ b.matrix).translation.copy()
    return None


arm.data.pose_position = "REST"
bpy.context.view_layer.update()
BASE_LDY = (wp("l hand") - wp("pelvis")).y
BASE_RDY = (wp("r hand") - wp("pelvis")).y
arm.data.pose_position = "POSE"
print("\n[걷기 프레임별]  발전후간격 = |왼발.y - 오른발.y| / 팔중립편차 = 레스트 대비")
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
    lz = mesh_low()
    cand.append((swing, gap, f))
    print("  %4d %10.4f %8.4f %8.4f %10.4f %9.4f" % (f, gap, lt.z, rt.z, swing, lz))
cand.sort()
NEUTRAL_F = cand[0][2]
print("팔이 가장 중립인 걷기 프레임 = f%d (팔편차 %.4f, 발간격 %.4f)"
      % (NEUTRAL_F, cand[0][0], cand[0][1]))
sc.frame_set(NEUTRAL_F)
bpy.context.view_layer.update()
WALK_ARMS = {bn: (arm.pose.bones[bn].location.copy(),
                  arm.pose.bones[bn].rotation_quaternion.copy())
             for bn in ARM_BONES}
WALK_BASE = {b.name: b.matrix_basis.copy() for b in arm.pose.bones}


def apply_walk_arms(act):
    """액션 전 프레임의 **팔 로컬 회전**을 걷기 중립 프레임 값으로 덮는다.
    로컬이라 척추가 움직이면 팔도 따라 움직인다(굳지 않는다)."""
    use(act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        for bn, (loc, rot) in WALK_ARMS.items():
            pb = arm.pose.bones[bn]
            pb.location = loc
            pb.rotation_quaternion = rot
            pb.scale = (1, 1, 1)
        for bn in WALK_ARMS:
            arm.pose.bones[bn].keyframe_insert("location", frame=f)
            arm.pose.bones[bn].keyframe_insert("rotation_quaternion", frame=f)
    return f1 - f0 + 1


# ---- 9) Idle ----
info = {}
if IDLE_SRC == "retarget":
    idle, info = bake_retarget("Idle", "infantry_guard_idle", nframes=IDLE_LEN)
    acts["Idle"] = idle
    if IDLE_ARMS in ("walk", "both"):
        if IDLE_ARMS == "both":
            # 비교용 사본. Blender 액션 복사는 copy() 로 충분하다.
            idb = idle.copy()
            idb.name = "IdleB"
            idb.use_fake_user = True
            acts["IdleB"] = idb
            print("  IdleB(걷기팔) 사본 생성: 프레임 %d개"
                  % apply_walk_arms(idb))
        else:
            print("  Idle 팔을 걷기 중립(f%d)으로 교체: 프레임 %d개"
                  % (NEUTRAL_F, apply_walk_arms(idle)))
else:
    # ---- 폴백: 합성 숨쉬기(s13 방식) ----
    # 걷기 중립 프레임을 바탕으로 가슴 2도짜리 숨쉬기 50프레임.
    idle = new_action("Idle")
    SPINE = arm.pose.bones.get("Bip001 Chest2")
    for f, amp in ((1, 0.0), (25, 1.0), (50, 0.0)):
        for b in arm.pose.bones:
            b.rotation_mode = "QUATERNION"
            b.matrix_basis = WALK_BASE[b.name].copy()
        if SPINE:
            SPINE.rotation_quaternion = (
                SPINE.rotation_quaternion @ Matrix.Rotation(
                    math.radians(2.0 * amp), 4, "X").to_quaternion())
        bpy.context.view_layer.update()
        for b in arm.pose.bones:
            b.keyframe_insert("rotation_quaternion", frame=f)
            b.keyframe_insert("location", frame=f)
    acts["Idle"] = idle
    print("Idle 생성 (합성 숨쉬기 50프레임, 가슴 2도) - 걷기 f%d 바탕" % NEUTRAL_F)

# ---- 10) Attack ----
if WITH_ATTACK:
    atk, ainfo = bake_retarget("Attack", "infantry_combat_shoot")
    acts["Attack"] = atk

# ---- 11) 안 쓰는 클립 정리 ----
for a in bpy.data.actions:
    a.use_fake_user = True
KEEP = set(acts)
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        print("액션 제거:", a.name)
        bpy.data.actions.remove(a)
print("\n최종 액션:", sorted(a.name for a in bpy.data.actions))

# ---- 12) fcurve 감사 (T 포즈 함정 재확인) ----
names = set(b.name for b in arm.pose.bones)
for nm in sorted(acts):
    bad = 0
    tot = 0
    for fc in fcs_of(acts[nm]):
        if '"' not in fc.data_path:
            continue
        tot += 1
        if fc.data_path.split('"')[1] not in names:
            bad += 1
    print("  액션 %-8s fcurve %4d개 / **없는 뼈를 가리킴 %d개**" % (nm, tot, bad))
    assert bad == 0, "액션 %s 가 없는 뼈를 가리킨다 -> T 포즈 난다" % nm


# ---- 13) 클립별 z 표 (스케일 오염·접지 감시) ----
def clip_z(act):
    use(act)
    f0 = int(round(act.frame_range[0]))
    f1 = int(round(act.frame_range[1]))
    lo, hi = 9e9, -9e9
    m = mesh.matrix_world
    a, b, c, d = m[2][0], m[2][1], m[2][2], m[2][3]
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


print("\n[클립별 메시 z 범위]  ★클립 간 '키'가 같아야 한다(다르면 스케일 오염)")
print("  %-8s %6s %10s %10s %10s %10s" % ("클립", "프레임", "최저z", "최고z", "키", "바닥대비"))
for nm in sorted(acts):
    lo, hi, nf = clip_z(acts[nm])
    print("  %-8s %6d %+10.4f %+10.4f %10.4f %+10.4f"
          % (nm, nf, lo, hi, hi - lo, lo - BIND_LOW))

print("\n[스케일 점검] 굽기 후")
for nm in sorted(acts):
    r = scale_ranges(acts[nm])
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-8s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))

# ---- 14) 손 그립 소켓 조사 (무기를 쥐여주려면 이 값이 필요하다) ----
# ★뼈 length 를 믿지 마라(함정 7). glTF 가 길이를 저장 안 해 임포터가 임의로 정한다.
#   손목->손끝 거리는 정점 bbox 로 잰다.
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
print("\n[손 조사] 손가락 뼈 유무 = 아래 목록에 finger/thumb/index 가 있는지 보라")
print("  전체 뼈 %d개: %s" % (len(arm.data.bones), [b.name for b in arm.data.bones]))
for side in ("R", "L"):
    bn = "Bip001 %s Hand" % side
    b = arm.data.bones[bn]
    kids = [c.name for c in b.children]
    vg = mesh.vertex_groups.get(bn)
    print("\n[%s 레스트]  자식 뼈 %s" % (bn, kids or "없음(손목이 말단)"))
    print("  head(월드) %s / tail(월드) %s / 임포터가 정한 length %.4f"
          % (tuple(round(x, 4) for x in (arm.matrix_world @ b.head_local)),
             tuple(round(x, 4) for x in (arm.matrix_world @ b.tail_local)),
             b.length))
    M = (arm.matrix_world @ b.matrix_local)
    print("  뼈 로컬축(월드) X %s / Y %s / Z %s"
          % tuple(tuple(round(x, 3) for x in M.to_3x3().normalized().col[i])
                  for i in range(3)))
    if vg:
        Mi = M.inverted()
        pts = []
        for v in mesh.data.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 0.5:
                    pts.append(Mi @ (mesh.matrix_world @ v.co))
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
            print("  ★그립 소켓 후보(뼈 로컬) = 손 bbox 중심 %s"
                  % (tuple(round((mx[k] + mn[k]) / 2, 4) for k in range(3)),))
arm.data.pose_position = "POSE"

# ---- 15) 텍스처 축소 ----
# ★익스포터가 아니라 여기서 줄인다. glTF 익스포터에는 해상도 옵션이 아예 없다
#   (export_image_format / export_image_quality / export_jpeg_quality 뿐).
# ★우리 메시가 실제로 쓰는 이미지만 건드린다. Running 파일을 임포트할 때 똑같은
#   텍스처가 texture_0.001 로 하나 더 딸려 들어오지만 쓰는 데가 없어 안 나간다.
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
    print("  %-16s %dx%d  채널 %d  (%s)" % (img.name, w, h, img.channels, img.file_format))
    if TEX_SIZE and (w > TEX_SIZE or h > TEX_SIZE):
        k = TEX_SIZE / float(max(w, h))
        nw, nh = max(1, int(round(w * k))), max(1, int(round(h * k)))
        img.scale(nw, nh)
        print("    -> %dx%d 로 축소" % (nw, nh))
    else:
        print("    -> 축소 안 함(TEX_SIZE=%s)" % TEX_SIZE)

# 마지막 포즈가 남지 않게 Idle 을 걸어둔다
use(acts["Idle"])
sc.frame_set(1)
sc.render.fps = 30
print("export fps =", sc.render.fps)
print("원본 키 %.3f  삼각형 %d  메시 %d개"
      % (H, TRI, len([o for o in sc.objects if o.type == "MESH"])))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB, export_format="GLB", use_selection=False,
    export_animations=True, export_animation_mode="ACTIONS",
    export_nla_strips=False, export_bake_animation=True,
    export_frame_range=False, export_yup=True,
    export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
    export_jpeg_quality=TEX_QUALITY)
print("EXPORTED %s  %d bytes (%.2f MB)  (TEX_SIZE=%s TEX_FORMAT=%s Q=%d)"
      % (OUT_GLB, os.path.getsize(OUT_GLB), os.path.getsize(OUT_GLB) / 1e6,
         TEX_SIZE, TEX_FORMAT, TEX_QUALITY))
