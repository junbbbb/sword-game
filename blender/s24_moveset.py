# -*- coding: utf-8 -*-
"""검사(slayer) 리그의 전투 모션 7종을 **Meshy 리그 캐릭터**에 통째로 이식한다.

    blender -b -P blender/s24_moveset.py
    -> web/hero2.glb  (hero 몸 + slayer 액션 Idle/Walk/Run/Attack/Heavy/Wide/Jump)

이 스크립트의 존재 이유
  Meshy 로 뽑는 고품질 캐릭터는 모션이 걷기/달리기 정도밖에 없다. 반대로 우리가
  손으로 만든 전투 모션(combo_poses.py)은 토이솔저 리그에만 있다. 둘을 붙이는
  통로가 이 파일이다. **모션이 좋아지거나(slayer.glb 재굽기) 새 모델이 와도
  다시 돌리기만 하면 된다.** 그래서 어떤 값도 하드코딩하지 않는다.
      새 모델: DST_GLB=web/새모델.glb OUT_GLB=web/새모델2.glb blender -b -P ...
      모션만 갱신: 그냥 다시 실행

★★리타게팅 방식은 '레스트 델타'다. 절대 행렬 복사가 아니다 (s14_basic2.py 와 동일)
      D = R_world(소스 애니 뼈, f) @ R_world(소스 **모델** 레스트 뼈)^-1
      목표 = D @ R_world(타깃 레스트 뼈)
  glTF 는 뼈 축·roll·길이를 저장하지 않아 임포터가 임의로 정한다. 실측으로
  두 리그의 레스트 뼈 축은 84~178도 어긋나 있다(아래 [정합] 표가 매번 찍는다).
  절대 회전을 넣으면 딱 그만큼 뒤틀린다. '레스트에서 얼마나 돌아갔나'만 옮긴다.

  ★기준 레스트 함정은 여기선 자동으로 피해 간다. s14 는 애니 FBX 와 모델 FBX 가
    따로였고 애니 FBX 의 레스트가 T 포즈가 아니라 위팔이 48.6도 어긋났다.
    이번 소스는 액션과 메시가 **같은 glb(slayer.glb)** 안에 있으므로 소스 레스트가
    곧 모델 레스트다. 그래도 같은 사고를 두 번 겪지 않도록, 소스 레스트가 T 포즈인지
    (양 손목이 어깨보다 바깥, 좌우 대칭) 매 실행 검사한다.

  ★스케일 폭주 방지: pb.matrix 에 직접 쓰지 않는다(과거 손이 39배).
    부모부터 순서대로 **matrix_basis** 를 해석적으로 계산해 넣는다.
        pose(b) = pose(부모) @ rest(부모)^-1 @ rest(b) @ basis(b)
    basis 는 **순수 회전**(이동 0, 스케일 1)이라 스케일이 섞일 여지가 없다.
    골반만 이동을 준다. 자식은 FK 로 따라온다.
    부수 효과로 소스에 스케일 오염이 있어도 결과에 옮겨붙지 않는다(회전만 읽는다).
    해석식이 맞는지 프레임마다 Blender 평가값과 대조해 최대 오차를 찍는다.

★★파지(양손검) 문제가 이 이식의 핵심이다
  slayer 모션은 전부 양손검 전제다. 그런데 두 리그의 비례가 다르다(실측):
      팔 길이 / 키   slayer 0.302   hero 0.353   (hero 팔이 17% 길다)
      어깨폭  / 키   slayer 0.303   hero 0.288
  관절 각도만 옮기면 두 손이 각자 더 멀리 뻗어 **자루에서 벌어진다**.
  게다가 검이 손에 꽂힌 각도 자체가 다르다:
      레스트 월드 자루축   slayer (-0.501,-0.459, 0.734)
                           hero   ( 0.437,-0.857, 0.273)   => **68.0도 차이**
  그래서 손 사이 오프셋을 그대로 옮기는 것(단순 이식)으로는 절대 안 맞는다.
  ★★그래서 먼저 **검을 다시 꽂는다**(SWORD_FIT, 기본 켬).
    68도는 대부분 '팔뚝축 둘레 roll' 이다. 이걸 그대로 두면 왼손 위치를 아무리
    잘 맞춰도 (1) 왼손이 자루를 가로질러 쥐고 (2) **칼끝 궤적이 통째로 68도
    돌아간다**. 칼끝이 모션의 정체성인데 그게 어긋나면 이식이 의미가 없다.
    SW_hero 는 오른손 뼈에 100% 웨이트로 붙은 강체라, 손 레스트 좌표계에서
    정점을 회전시키면 그만이다. 검의 주축(칼날 방향)과 부축(칼날 평면 법선,
    칼날 구간 공분산의 최소 고유벡터)으로 좌표계를 만들어 소스 검의 좌표계에
    포갠다. 위치는 안 건드린다(손이 쥐는 지점은 각자 자기 검 기준 그대로).
    ★s15 가 고른 SW_TILT/SW_LIFT 는 'Meshy 걷기에서 팔을 내렸을 때' 기준이라
      양손검 무브셋에서는 어차피 무의미하다. 원본 hero.glb 는 안 건드린다.
  **그 다음 타깃 자신의 검(SW_*) 자루축에 왼손을 다시 건다.**
      1) 소스에서 프레임마다 왼손목이 자기 자루축의 어디에 있는지 잰다
         (축상 t / 축까지 수직거리 p). 실측 Idle: t=-0.117H, p=0.077H 로 일정.
      2) p 는 손목이 자루에서 떨어진 양이 아니라 **손목-손바닥 거리**다.
         그래서 '자루 위 기준점 -> 왼손목' 벡터를 왼손 델타로 되돌려
         (= 레스트 자세에서 본 벡터) 해부학적 상수로 만든 뒤 타깃에 다시 씌운다.
      3) 타깃 자루축 위의 기준점 C 를 t*키비율로 잡되 **자기 자루 길이로 자른다**
         (hero 자루는 손 아래 0.089H 뿐인데 slayer 는 0.135H 다. 안 자르면
          왼손이 손잡이 끝을 지나 허공을 쥔다).
      4) 왼팔 2본 IK(위팔+팔뚝)로 손목을 그 목표에 보낸다. 팔꿈치 스위블은
         리타게팅 결과를 그대로 유지해 어깨가 어색하게 돌지 않게 한다.
  ★언제 풀 것인가: 소스 왼손이 자기 자루에서 떨어져 있는 프레임(달리기 팔치기,
    횡일섬 중반의 한손 놓기)까지 붙이면 원본 모션이 망가진다. 소스의 수직거리 p 로
    게이트를 만들어(0.10H 이하 100% ~ 0.18H 이상 0%) 가중치를 스무딩해 섞는다.
    실측 게이트: Idle/Walk/Jump/Attack 전 프레임 파지, Heavy 전 프레임 파지,
    Wide 54 중 38 프레임, Run 0 프레임(달리기는 원래 손을 놓는다).

★발 접지
  비례가 다르면(허벅지 0.247H vs 0.203H, 종아리 0.173H vs 0.240H) 각도만 옮겼을 때
  발 높이가 달라진다. 클립마다 메시 최저점 10분위를 바인드 최저점에 맞추는
  **한 클립 한 상수** 보정을 건다(s12/s14 와 동일). 프레임마다 다른 값을 주면
  골반 상하 운동이 사라져 걸음이 죽는다.
  게임(main.js groundFeet)은 매 프레임 발 본으로 다시 접지하므로 절대 높이보다
  '발이 뒤로 밀리는 속도'가 중요하다. 그래서 마지막에 probe_stride 와 같은 방식으로
  걷기/달리기 접지 발 속도를 재서 CHAR_CFG 에 넣을 값을 찍어 준다.

★함정 (하나라도 밟으면 조용히 망가진다)
  1) fps: 임포트 전에 30 고정. glb 는 초 단위라 fps 가 다르면 프레임이 안 맞는다
  2) 액션 이름 충돌: 소스는 들어오자마자 SRC_, 타깃 원본은 ORIG_ 접두사
  3) 액션 슬롯(4.4+): 슬롯 없으면 액션이 조용히 아무 일도 안 한다
  4) use_fake_user: 안 켜면 export 에서 조용히 빠진다
  5) Icosphere: glTF **임포터**가 뼈 표시용으로 만드는 반지름 1 구. glb 엔 없다.
     안 지우면 키 측정이 망가진다(발 속도가 0.63배로 과소평가된 전과가 있다)
  6) 소스 오브젝트를 안 지우고 내보내면 검사 몸이 통째로 딸려 나간다
  7) 뼈 이름: Meshy 원본(Hips/LeftArm/Spine02)이면 RENAME 을 먹인다. 이때
     **정점 그룹 이름도 같이** 바꿔야 스킨이 안 끊긴다
  8) 오차는 월드 단위로 재라. 아마추어 스케일이 0.01 이라 아마추어 공간 수치는
     100배 커 보인다

손잡이(환경변수)
  SRC_GLB   소스(모션) glb           기본 web/slayer.glb
  DST_GLB   타깃(몸) glb             기본 web/hero.glb
  OUT_GLB   결과                     기본 web/hero2.glb
  CLIPS     이식할 액션 목록(쉼표)   기본 Idle,Walk,Run,Attack,Heavy,Wide,Jump
  SRC_SWORD 소스 자루 기준 메시      기본 SW_baekah (게임 기본 swordIdx=1)
  DST_SWORD 타깃 자루 메시           기본 자동탐색(SW_ 로 시작하는 첫 메시)
  SWORD_FIT 1(기본) 타깃 검을 소스와 같은 각도로 주먹에 다시 꽂는다 / 0 원본 유지
  GRIP_IK   1(기본) 왼팔 IK 사용 / 0 순수 리타게팅만(비교용)
  GRIP_K    왼손목-자루 오프셋 환산 보정(기본 1.0. 손 크기가 키 대비 많이 다를 때만)
  GRIP_ON/GRIP_OFF  파지 게이트 문턱(키 정규화. 기본 0.10 / 0.18)
  KEEP_ORIG 1 이면 타깃 원본 액션을 Orig* 이름으로 같이 내보낸다(기본 0)
  VERIFY    1(기본) 결과 glb 재임포트해 파지·접지 실측
  RENDER    1(기본) 렌더 / 0 생략
  OUTDIR    렌더 폴더               기본 renders/history/v75_moveset
  TEX_FORMAT/TEX_QUALITY  텍스처 재인코딩(기본 AUTO = 원본 포맷 유지)
"""
import bpy
import os
import sys
import math
import json
from mathutils import Vector, Matrix, Quaternion

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")

SRC_GLB = os.environ.get("SRC_GLB") or os.path.join(WEB, "slayer.glb")
DST_GLB = os.environ.get("DST_GLB") or os.path.join(WEB, "hero.glb")
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "hero2.glb")
CLIPS = [c.strip() for c in os.environ.get(
    "CLIPS", "Idle,Walk,Run,Attack,Heavy,Wide,Jump").split(",") if c.strip()]
SRC_SWORD = os.environ.get("SRC_SWORD", "SW_baekah")
DST_SWORD = os.environ.get("DST_SWORD", "")
SWORD_FIT = os.environ.get("SWORD_FIT", "1") == "1"
GRIP_IK = os.environ.get("GRIP_IK", "1") == "1"
KEEP_ORIG = os.environ.get("KEEP_ORIG", "0") == "1"
VERIFY = os.environ.get("VERIFY", "1") == "1"
RENDER = os.environ.get("RENDER", "1") == "1"
OUTDIR = os.environ.get("OUTDIR") or os.path.join(
    ROOT, "renders", "history", "v75_moveset")
TEX_FORMAT = os.environ.get("TEX_FORMAT", "AUTO").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

# 파지 게이트: 소스 왼손목-자루축 수직거리(키 정규화). 이 아래면 쥔 것으로 본다.
GRIP_ON = float(os.environ.get("GRIP_ON", "0.10"))
GRIP_OFF = float(os.environ.get("GRIP_OFF", "0.18"))
# 왼손목-자루 오프셋 환산 배율에 곱하는 보정. 두 리그의 손 크기가 키 대비 많이
# 다를 때만 건드린다(아래 [자루] 절에서 손 크기 차이를 찍는다).
GRIP_K = float(os.environ.get("GRIP_K", "1.0"))
# 주먹 하나를 키의 몇 %로 볼 것인가. 175cm 성인 주먹 폭 ~9.6cm.
FIST = 0.055

# Meshy 원본 이름 -> 우리 규칙(s13/s14 와 같은 표). 순서 중요(긴 것부터).
# ★"r hand", "l thigh" 같은 부분 문자열로 뼈를 찾는 코드가 게임·포즈 양쪽에 있다.
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
    ("Spine", "Bip001 Spine"), ("Hips", "Bip001 Pelvis"),
    ("head_end", "Bip001 HeadNub"), ("headfront", "Bip001 HeadFront"),
    ("Head", "Bip001 Head"), ("neck", "Bip001 Neck"),
]

# 타깃에만 있는 뼈를 소스 어느 뼈에 붙일지. 이름이 같으면 자동이라 여기 안 적는다.
# ★척추 마디 수가 다르다. Meshy 는 Pelvis->Chest2->Chest->Spine 3마디,
#   slayer 는 Pelvis->Spine 1마디. 셋 다 slayer Spine 델타를 받는다.
#   **절대 회전을 지정하는 방식**이라 세 배로 굽지 않고 상체가 한 덩어리로 돈다.
FALLBACK = {
    "Bip001 Chest2": "Bip001 Spine",
    "Bip001 Chest": "Bip001 Spine",
    "Bip001 Spine": "Bip001 Spine",
    "Bip001 HeadNub": "Bip001 Head",     # 머리에 붙은 표식. 머리 델타 그대로
    "Bip001 HeadFront": "Bip001 Head",   # 코 방향 표식. 게임이 정면 판정에 쓴다
    "Bip001 L Toe0Nub": "Bip001 L Toe0",
    "Bip001 R Toe0Nub": "Bip001 R Toe0",
}
PELVIS = "Bip001 Pelvis"
L_ARM = ("Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand")
HAND_R = "Bip001 R Hand"
HAND_L = "Bip001 L Hand"

print("=" * 78)
print("[설정] 소스 %s" % SRC_GLB)
print("       타깃 %s" % DST_GLB)
print("       결과 %s" % OUT_GLB)
print("       클립 %s / 왼팔IK %s" % (",".join(CLIPS), "ON" if GRIP_IK else "OFF"))

# ================================================================ 1) 씬 준비
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
# ★함정 1: 아무것도 임포트하기 전에 30 으로 고정한다.
sc.render.fps = 30
sc.render.fps_base = 1.0


def imp(path):
    """glb 하나를 읽고 (새 오브젝트, 새 액션) 을 돌려준다."""
    b_o = set(o.name for o in sc.objects)
    b_a = set(a.name for a in bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in sc.objects if o.name not in b_o]
    acts = [a for a in bpy.data.actions if a.name not in b_a]
    if sc.render.fps != 30:                       # ★함정 1
        print("  ★fps 가 %d 로 바뀌었다. 30 으로 되돌린다" % sc.render.fps)
        sc.render.fps = 30
    return objs, acts


def junk(o):
    """glTF 임포터가 만든 뼈 표시용 Icosphere 인가(★함정 5)."""
    return any(c.name == "glTF_not_exported" for c in o.users_collection)


# ================================================================ 2) 소스
src_objs, src_acts = imp(SRC_GLB)
for a in src_acts:                                 # ★함정 2
    a.name = "SRC_" + a.name
src = next(o for o in src_objs if o.type == "ARMATURE")
SRC_ACT = {a.name[4:]: a for a in src_acts}
print("\n[소스] 아마추어 %s / 뼈 %d / 액션 %s"
      % (src.name, len(src.data.bones), sorted(SRC_ACT)))
missing = [c for c in CLIPS if c not in SRC_ACT]
if missing:
    raise SystemExit("소스에 없는 클립: %s (있는 것: %s)" % (missing, sorted(SRC_ACT)))

# ================================================================ 3) 타깃
dst_objs, dst_acts = imp(DST_GLB)
for a in dst_acts:                                 # ★함정 2
    a.name = "ORIG_" + a.name
arm = next(o for o in dst_objs if o.type == "ARMATURE")
DST_MESH = [o for o in dst_objs if o.type == "MESH" and not junk(o)]
print("[타깃] 아마추어 %s / 뼈 %d / 메시 %s / 원본 액션 %s"
      % (arm.name, len(arm.data.bones), [m.name for m in DST_MESH],
         [a.name for a in dst_acts]))

# ---- 뼈 이름 정규화 (★함정 7) ----
have = set(b.name for b in arm.data.bones)
todo = [(o, n) for o, n in RENAME if o in have and n not in have]
if todo:
    print("  Meshy 원본 이름을 발견했다. %d개 뼈를 우리 규칙으로 바꾼다" % len(todo))
    for old, new in todo:
        arm.data.bones[old].name = new
    nm = dict(todo)
    for m in DST_MESH:                              # 정점 그룹도 같이(스킨 유지)
        for g in m.vertex_groups:
            if g.name in nm:
                g.name = nm[g.name]
else:
    print("  뼈 이름은 이미 우리 규칙이다(변경 없음)")

# ---- 뼈 매핑 표 ----
SRC_BONES = set(b.name for b in src.data.bones)
DST_BONES = [b.name for b in arm.data.bones]
MAP = {}
for bn in DST_BONES:
    if bn in SRC_BONES:
        MAP[bn] = bn
    elif bn in FALLBACK and FALLBACK[bn] in SRC_BONES:
        MAP[bn] = FALLBACK[bn]
    else:
        MAP[bn] = None                              # 부모 델타를 물려받는다
print("\n[뼈 매핑] 타깃 %d본 <- 소스 %d본" % (len(DST_BONES), len(SRC_BONES)))
for bn in DST_BONES:
    s = MAP[bn]
    tag = "" if s == bn else ("  <- %s" % s if s else "  (대응 없음: 레스트 유지)")
    print("   %-22s %s" % (bn, tag))
unused = sorted(SRC_BONES - set(v for v in MAP.values() if v))
print("   소스에서 안 쓰는 뼈 %d개: %s" % (len(unused), unused))

# ================================================================ 4) 레스트
for a in (src, arm):
    for b in a.pose.bones:
        b.rotation_mode = "QUATERNION"              # 쿼터니언 커브에 키를 찍으려면 필수
        b.matrix_basis = Matrix()


def rest_world(a):
    """뼈 이름 -> (월드 회전 3x3 정규화, 월드 head 위치)."""
    a.data.pose_position = "REST"
    bpy.context.view_layer.update()
    A2W = a.matrix_world.copy()
    out = {}
    for b in a.data.bones:
        m = (A2W @ b.matrix_local).to_3x3()
        m.normalize()
        out[b.name] = (m, A2W @ b.head_local)
    a.data.pose_position = "POSE"
    return A2W, out


def body_meshes(a):
    """키 판정용 메시(무기·Icosphere 제외)."""
    return [o for o in bpy.data.objects
            if o.type == "MESH" and o.parent == a
            and not o.name.startswith(("SW_", "SH_")) and not junk(o)]


def low_of(meshes, dg=None):
    dg = dg or bpy.context.evaluated_depsgraph_get()
    lo = 1e9
    for o in meshes:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        for v in me.vertices:
            z = (mw @ v.co).z
            if z < lo:
                lo = z
        ev.to_mesh_clear()
    return lo


SRC_BODY = body_meshes(src)
DST_BODY = body_meshes(arm)
S2W, SREST = rest_world(src)
A2W, DREST = rest_world(arm)
A2W_R = A2W.to_3x3()
A2W_R.normalize()
A2W_R_INV = A2W_R.inverted()
A2W_INV = A2W.inverted()

src.data.pose_position = "REST"
arm.data.pose_position = "REST"
bpy.context.view_layer.update()


def height(meshes):
    zs = []
    for o in meshes:
        zs += [(o.matrix_world @ v.co).z for v in o.data.vertices]
    return max(zs) - min(zs), min(zs)


SH, SLOW = height(SRC_BODY)
DH, BIND_LOW = height(DST_BODY)
K_H = DH / SH                                       # 키 비율(길이 환산 배율)
src.data.pose_position = "POSE"
arm.data.pose_position = "POSE"

REST_ARM = {b.name: b.matrix_local.copy() for b in arm.data.bones}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
ORDER = []
for b in arm.pose.bones:
    d, x = 0, b
    while x.parent:
        d += 1
        x = x.parent
    ORDER.append((d, b.name))
ORDER.sort()
ORDER = [n for _, n in ORDER]
ROOTS = [n for n in ORDER if PARENT[n] is None]
if len(ROOTS) != 1 or ROOTS[0] != PELVIS:
    print("  ★뿌리 뼈가 %s 다(골반이 아니다). 그래도 진행한다" % ROOTS)
ROOT_BONE = ROOTS[0]

LEG_S = SREST[PELVIS][1].z - SREST["Bip001 L Foot"][1].z
LEG_D = DREST[PELVIS][1].z - DREST["Bip001 L Foot"][1].z
K_TRANS = LEG_D / LEG_S                             # 골반 이동 진폭 환산 배율
print("\n[레스트] 소스 키 %.4f / 타깃 키 %.4f  (키비율 K_H=%.4f)" % (SH, DH, K_H))
print("         다리(골반-발목) 소스 %.4f / 타깃 %.4f  (골반이동 배율 %.4f)"
      % (LEG_S, LEG_D, K_TRANS))
print("         타깃 바인드 최저 z %.4f" % BIND_LOW)


def norm(seg, W, H):
    return (W[seg[1]][1] - W[seg[0]][1]).length / H


print("\n[비례] 키로 나눈 마디 길이")
for tag, a, b in (("허벅지", "Bip001 L Thigh", "Bip001 L Calf"),
                  ("종아리", "Bip001 L Calf", "Bip001 L Foot"),
                  ("위팔", "Bip001 L UpperArm", "Bip001 L Forearm"),
                  ("팔뚝", "Bip001 L Forearm", "Bip001 L Hand"),
                  ("어깨폭", "Bip001 L UpperArm", "Bip001 R UpperArm")):
    if a in SREST and b in SREST and a in DREST and b in DREST:
        print("   %-6s 소스 %.3f / 타깃 %.3f  (%+.1f%%)"
              % (tag, norm((a, b), SREST, SH), norm((a, b), DREST, DH),
                 (norm((a, b), DREST, DH) / norm((a, b), SREST, SH) - 1) * 100))

# ---- [정합] 두 리그가 같은 월드 프레임/같은 T 포즈인가 ----
print("\n[정합] 레스트 관절 방향 각도차(월드). 이 값이 크면 리타게팅이 그만큼 틀어진다")
worst = 0.0
for tag, a, b in (("허벅지", "Bip001 L Thigh", "Bip001 L Calf"),
                  ("종아리", "Bip001 L Calf", "Bip001 L Foot"),
                  ("위팔", "Bip001 L UpperArm", "Bip001 L Forearm"),
                  ("팔뚝", "Bip001 L Forearm", "Bip001 L Hand"),
                  ("쇄골", "Bip001 L Clavicle", "Bip001 L UpperArm")):
    if not (a in SREST and b in SREST and a in DREST and b in DREST):
        continue
    ds = (SREST[b][1] - SREST[a][1]).normalized()
    dd = (DREST[b][1] - DREST[a][1]).normalized()
    ang = math.degrees(ds.angle(dd))
    worst = max(worst, ang)
    print("   %-6s %.1f 도" % (tag, ang))
if worst > 25:
    print("   ★★25도를 넘는다. 두 레스트가 같은 자세가 아닐 수 있다")


def facing(W):
    d = W["Bip001 L Toe0"][1] - W["Bip001 L Foot"][1]
    d.z = 0
    return d.normalized()


fs, fd = facing(SREST), facing(DREST)
print("   전방(발목->발끝) 소스 (%.2f,%.2f) / 타깃 (%.2f,%.2f) -> %.1f 도 차이"
      % (fs.x, fs.y, fd.x, fd.y, math.degrees(fs.angle(fd))))
if math.degrees(fs.angle(fd)) > 30:
    raise SystemExit("두 리그의 정면이 다르다. 월드 회전 보정이 필요하다")
# 소스 레스트가 T 포즈인가(★s14 의 48.6도 사고 재발 방지)
for W, tag, H in ((SREST, "소스", SH), (DREST, "타깃", DH)):
    lh, rh = W[HAND_L][1], W[HAND_R][1]
    sh = W["Bip001 L UpperArm"][1]
    ok = abs(lh.x) > abs(sh.x) and abs(lh.z - rh.z) < H * 0.03
    print("   %s 레스트 T포즈 판정: 손목 |x| %.3f > 어깨 %.3f / 좌우 z 차 %.4f -> %s"
          % (tag, abs(lh.x), abs(sh.x), abs(lh.z - rh.z), "OK" if ok else "★의심"))

# ================================================================ 5) 자루 기하
def hand_rest_matrix(a):
    a.data.pose_position = "REST"
    bpy.context.view_layer.update()
    M = (a.matrix_world @ a.pose.bones[HAND_R].matrix).copy()
    a.data.pose_position = "POSE"
    return M


def sword_frame(a, name, H):
    """검 메시로 '오른손 레스트 로컬' 좌표계를 만든다.

    주축(칼날 방향)은 probe_swing.py(= main.js measureBlade)와 같은 절차로
    잡는다: 원점(손목)에서 가장 먼 정점의 방향. 부축은 **칼날 구간** 정점의
    축수직 성분 공분산에서 고유값이 가장 작은 방향(= 칼날 평면의 법선)이다.
    검을 다시 꽂을 때 roll 까지 맞추려면 부축이 필요하다.
    반환 (3x3 좌표계[u,n,b], 손아래 월드길이, 칼끝 월드길이, 정점수).
    """
    ob = bpy.data.objects.get(name)
    if ob is None:
        return None
    import numpy as np
    HM = hand_rest_matrix(a)
    HMi = HM.inverted()
    loc = [HMi @ (ob.matrix_world @ v.co) for v in ob.data.vertices]
    u = max(loc, key=lambda p: p.length).normalized()
    pr = [p.dot(u) for p in loc]
    hi = max(pr)
    blade = [p - u * p.dot(u) for p in loc if p.dot(u) > hi * 0.35]
    if len(blade) < 8:
        blade = [p - u * p.dot(u) for p in loc]
    M = np.array([[v.x, v.y, v.z] for v in blade], dtype=float)
    M -= M.mean(axis=0)
    w, V = np.linalg.eigh(M.T @ M)
    n = Vector(V[:, 0]).normalized()               # 최소 고유벡터 = 칼날 평면 법선
    n = (n - u * n.dot(u)).normalized()
    F = Matrix((u, n, u.cross(n))).transposed()    # 열이 축인 3x3
    Rw = HM.to_3x3()
    Rw.normalize()
    uw = (Rw @ u).normalized()
    o = HM.translation
    prw = [(ob.matrix_world @ v.co - o).dot(uw) for v in ob.data.vertices]
    print("   %-10s 정점 %5d / 레스트 월드 자루축 (%.3f,%.3f,%.3f) 칼날법선 "
          "(%.3f,%.3f,%.3f)" % (name, len(loc), uw.x, uw.y, uw.z,
                                *(Rw @ n).normalized()))
    print("              손아래 %.4f (키의 %.4f) / 칼끝 %.4f (키의 %.4f)"
          % (-min(prw), -min(prw) / H, max(prw), max(prw) / H))
    return F, -min(prw), max(prw)


print("\n[자루] 손목 원점 기준 자루 좌표계")
S_SW = sword_frame(src, SRC_SWORD, SH)
if DST_SWORD:
    dname = DST_SWORD
else:
    cand = [m.name for m in bpy.data.objects
            if m.type == "MESH" and m.parent == arm and m.name.startswith("SW_")]
    dname = cand[0] if cand else ""
    if cand:
        print("   타깃 검 자동탐색 -> %s" % dname)
D_SW = sword_frame(arm, dname, DH) if dname else None

# ---- 검을 소스와 같은 각도로 다시 꽂는다 ----
if S_SW and D_SW:
    def axang(A, B):
        return math.degrees((SREST[HAND_R][0] @ Vector(A.col[0]))
                            .angle(DREST[HAND_R][0] @ Vector(B.col[0])))
    print("   레스트 자루축 각도차 %.1f 도" % axang(S_SW[0], D_SW[0]))
    if SWORD_FIT:
        # 타깃 손 로컬에서 소스와 같은 월드 방향을 내는 좌표계
        want = DREST[HAND_R][0].inverted() @ SREST[HAND_R][0] @ S_SW[0]
        X = want @ D_SW[0].inverted()               # 순수 회전(직교 x 직교)
        ang = math.degrees(X.to_quaternion().angle)
        ob = bpy.data.objects[dname]
        HM = hand_rest_matrix(arm)
        T = ob.matrix_world.inverted() @ HM @ X.to_4x4() @ HM.inverted() @ ob.matrix_world
        for v in ob.data.vertices:
            v.co = T @ v.co
        ob.data.update()
        print("   ★%s 를 주먹 안에서 %.1f 도 돌려 다시 꽂았다(위치는 그대로)"
              % (dname, ang))
        D_SW = sword_frame(arm, dname, DH)
        print("   다시 꽂은 뒤 자루축 각도차 %.2f 도" % axang(S_SW[0], D_SW[0]))
    else:
        print("   SWORD_FIT=0 이라 검을 원본 각도 그대로 둔다"
              " (칼끝 궤적이 그만큼 어긋난다)")
DO_GRIP = GRIP_IK and S_SW is not None and D_SW is not None
if GRIP_IK and not DO_GRIP:
    print("   ★검을 못 찾아 왼팔 IK 를 끈다(소스 %s / 타깃 %s)" % (SRC_SWORD, dname))


# ---- 손 크기 대조: 파지 오프셋을 '키 비율'로 환산해도 되는지의 근거 ----
# 왼손목이 자루축에서 떨어진 거리(0.077H)는 사실 **손목-손바닥 거리**다.
# 그래서 키가 아니라 손 크기로 환산해야 맞다. 두 리그의 손이 키 대비 같은 크기면
# 키 비율이 곧 손 비율이라 그냥 K_H 를 쓰면 된다. 다르면 여기 경고가 뜬다.
def hand_size(a, meshes, H):
    nm = HAND_L
    head = a.matrix_world @ a.data.bones[nm].head_local
    ds = []
    for o in meshes:
        g = o.vertex_groups.get(nm)
        if g is None:
            continue
        for v in o.data.vertices:
            w = next((x.weight for x in v.groups if x.group == g.index), 0.0)
            if w > 0.7:
                ds.append(((o.matrix_world @ v.co) - head).length)
    return (sum(ds) / len(ds) / H) if ds else 0.0


for a in (src, arm):
    a.data.pose_position = "REST"
bpy.context.view_layer.update()
hs = hand_size(src, SRC_BODY, SH)
hd_ = hand_size(arm, DST_BODY, DH)
for a in (src, arm):
    a.data.pose_position = "POSE"
print("   손 크기(손목->손 정점 평균 / 키): 소스 %.4f / 타깃 %.4f  (차이 %+.1f%%)"
      % (hs, hd_, (hd_ / hs - 1) * 100 if hs else 0))
if hs and abs(hd_ / hs - 1) > 0.15:
    print("   ★손 크기가 15%% 넘게 다르다. 파지 오프셋을 키가 아니라 손 비율로"
          " 환산해야 할 수 있다(GRIP_K 로 손보라)")

# ================================================================ 6) 엔진
def src_world_rot(bn):
    """소스 뼈의 현재 프레임 월드 회전(정규화)."""
    m = (S2W @ src.pose.bones[bn].matrix).to_3x3()
    m.normalize()
    return m


def delta_rots():
    """이번 프레임의 타깃 뼈별 목표 월드 회전 dict 을 만든다(레스트 델타)."""
    Rw = {}
    for bn in ORDER:
        sn = MAP.get(bn)
        if sn is None:
            Rw[bn] = DREST[bn][0].copy()            # 대응 없으면 레스트 유지
        else:
            Rw[bn] = src_world_rot(sn) @ SREST[sn][0].inverted() @ DREST[bn][0]
    return Rw


def build(Rw, pelvis_world):
    """월드 회전 dict + 골반 월드 위치 -> (pose 행렬 dict, basis dict).

        pose(b) = pose(부모) @ rest(부모)^-1 @ rest(b) @ basis(b)
    basis 를 해석적으로 계산하므로 뼈마다 depsgraph 갱신이 필요 없다(프레임당 1회).
    basis 는 순수 회전이라 스케일이 섞일 여지가 없다.
    """
    pose, basis = {}, {}
    for bn in ORDER:
        Ra = A2W_R_INV @ Rw[bn]                     # 아마추어 공간 회전
        p = PARENT[bn]
        if p is None:
            t = A2W_INV @ pelvis_world
            M = Matrix.Translation(t) @ Ra.to_4x4()
            b = REST_ARM[bn].inverted() @ M
        else:
            P = pose[p] @ REST_ARM[p].inverted() @ REST_ARM[bn]
            Pr = P.to_3x3()
            Pr.normalize()
            b = (Pr.inverted() @ Ra).to_4x4()       # 이동 0, 스케일 1
            M = P @ b
        pose[bn] = M
        basis[bn] = b
    return pose, basis


def wpos(pose, bn):
    return A2W @ pose[bn].translation


def two_bone_ik(S, E, W, T):
    """어깨 S / 팔꿈치 E / 손목 W 를 목표 T 로 보내는 회전 두 개(월드 쿼터니언).

    반환 (R1, R2, 실제도달점). R1 은 위팔에, R2@R1 은 팔뚝·손에 곱한다.
    팔꿈치 스위블(굽는 평면)은 현재 자세를 그대로 유지한다. 그래야 어깨가
    엉뚱하게 돌지 않고 리타게팅이 만든 몸짓이 살아남는다.
    """
    l1 = (E - S).length
    l2 = (W - E).length
    v = T - S
    d = v.length
    if d < 1e-6:
        return Quaternion(), Quaternion(), W
    n = v / d
    dc = min(max(d, abs(l1 - l2) + 1e-5), l1 + l2 - 1e-5)
    ca = (l1 * l1 + dc * dc - l2 * l2) / (2 * l1 * dc)
    A = math.acos(min(1.0, max(-1.0, ca)))
    ev = E - S
    perp = ev - n * ev.dot(n)
    if perp.length < l1 * 1e-4:                     # 팔이 완전히 펴진 특이점
        ref = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
        perp = ref - n * ref.dot(n)
    perp.normalize()
    E2 = S + n * (l1 * math.cos(A)) + perp * (l1 * math.sin(A))
    R1 = (E - S).rotation_difference(E2 - S)
    W2 = E2 + (R1 @ (W - E))
    Tc = S + n * dc
    R2 = (W2 - E2).rotation_difference(Tc - E2)
    return R1, R2, Tc


def grip_target():
    """소스에서 이번 프레임의 파지 관계를 잰다.

    자루축 위 기준점 C(왼손목에서 가장 가까운 점)와 'C -> 왼손목' 벡터를
    왼손 델타로 되돌려(= 레스트 자세에서 본 모양) 해부학 상수로 만든다.
    반환 (축상 위치 t, 상수 벡터 q, 수직거리/키, 게이트 가중치).
    """
    sd = Vector(S_SW[0].col[0])
    RM = S2W @ src.pose.bones[HAND_R].matrix
    Rr = RM.to_3x3()
    Rr.normalize()
    P = RM.translation.copy()
    u = (Rr @ sd).normalized()
    L = (S2W @ src.pose.bones[HAND_L].matrix).translation.copy()
    v = L - P
    t = v.dot(u)
    C = P + u * t                                   # 자루축 위 기준점
    perp = (L - C).length
    w = 1.0 if perp <= GRIP_ON * SH else (
        0.0 if perp >= GRIP_OFF * SH else
        (GRIP_OFF * SH - perp) / ((GRIP_OFF - GRIP_ON) * SH))
    # 소스 왼손 델타를 벗겨 해부학 상수로 만든다
    Ds = src_world_rot(HAND_L) @ SREST[HAND_L][0].inverted()
    q = Ds.inverted() @ (C - L)                     # '기준점 - 손목' (레스트 기준)
    return (t, q, perp / SH, w)


def apply_grip(pose, Rw, gt):
    """왼팔 2본 IK 로 손목을 타깃 자루에 건다. (목표, IK전 이탈, None, 가중치)."""
    t, q, sperp, w = gt
    hd = Vector(D_SW[0].col[0])
    h_below, h_blade = D_SW[1], D_SW[2]
    HM = A2W @ pose[HAND_R]
    Hr = HM.to_3x3()
    Hr.normalize()
    uh = (Hr @ hd).normalized()
    # ★타깃 자루가 소스보다 짧으면 잘라 준다. 안 자르면 손잡이 끝 너머 허공을 쥔다.
    th = min(max(t * K_H, -h_below * 0.95), h_blade * 0.5)
    C = HM.translation + uh * th
    # ★Dl 은 소스 왼손 델타와 같은 값이라 q 의 델타가 상쇄된다(= 손목-자루 벡터를
    #   월드에서 그대로 옮기고 기준점만 타깃 자루로 바꾸는 것과 같다). 그래도
    #   식을 남겨 둔다. 나중에 손목 보정을 끼워도 뜻이 안 변한다.
    Dl = Rw[HAND_L] @ DREST[HAND_L][0].inverted()
    T = C - Dl @ (q * (K_H * GRIP_K))
    Lw = wpos(pose, HAND_L)
    before = (Lw - T).length
    if w <= 1e-4:
        return T, before, before, 0.0
    S = wpos(pose, L_ARM[0])
    E = wpos(pose, L_ARM[1])
    R1, R2, Tc = two_bone_ik(S, E, Lw, T)
    R1 = Quaternion().slerp(R1, w)
    R2 = Quaternion().slerp(R2, w)
    M1 = R1.to_matrix()
    M2 = (R2 @ R1).to_matrix()
    Rw[L_ARM[0]] = M1 @ Rw[L_ARM[0]]
    Rw[L_ARM[1]] = M2 @ Rw[L_ARM[1]]
    Rw[L_ARM[2]] = M2 @ Rw[L_ARM[2]]
    return T, before, None, w


def new_action(name):
    arm.animation_data_clear()
    arm.animation_data_create()
    a = bpy.data.actions.new(name)
    a.use_fake_user = True                          # ★함정 4
    arm.animation_data.action = a
    try:
        slot = a.slots.new(id_type="OBJECT", name="S")   # ★함정 3
        arm.animation_data.action_slot = slot
    except Exception as e:
        print("  slot 생성 실패(구버전?):", e)
    return a


def use_src(name):
    act = SRC_ACT[name]
    if src.animation_data is None:
        src.animation_data_create()
    src.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            src.animation_data.action_slot = slots[0]
    except Exception:
        pass
    return int(act.frame_range[0]), int(act.frame_range[1])


def pct(xs, p):
    s = sorted(xs)
    return s[min(len(s) - 1, max(0, int(len(s) * p)))]


# ================================================================ 7) 굽기
def bake(name):
    f0, f1 = use_src(name)
    nf = f1 - f0 + 1
    print("\n[%s] 소스 f%d~%d (%d장)" % (name, f0, f1, nf))

    # --- 1차: 골반 궤적 평균 / 접지 보정량 / 파지 게이트를 잰다 ---
    praw, gts = [], []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        praw.append((S2W @ src.pose.bones[PELVIS].matrix).translation.copy())
        gts.append(grip_target() if DO_GRIP else None)
    pmean = Vector((sum(p.x for p in praw) / nf, sum(p.y for p in praw) / nf,
                    sum(p.z for p in praw) / nf))
    # 게이트 가중치 시간 스무딩(1-2-1). 튀는 프레임에서 팔이 홱 돌지 않게.
    if DO_GRIP:
        for _ in range(2):
            ws = [g[3] for g in gts]
            sm = [(ws[max(0, i - 1)] + 2 * ws[i] + ws[min(nf - 1, i + 1)]) / 4.0
                  for i in range(nf)]
            gts = [(g[0], g[1], g[2], s) for g, s in zip(gts, sm)]
        on = sum(1 for g in gts if g[3] > 0.5)
        print("   파지 게이트: %d/%d 프레임 (소스 왼손-자루축 수직거리 %.3f~%.3f H)"
              % (on, nf, min(g[2] for g in gts), max(g[2] for g in gts)))

    lows, maxerr, befs, afts = [], 0.0, [], []
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        pw = DREST[ROOT_BONE][1] + (praw[i] - pmean) * K_TRANS
        Rw = delta_rots()
        pose, basis = build(Rw, pw)
        if DO_GRIP:
            T, bef, _, w = apply_grip(pose, Rw, gts[i])
            pose, basis = build(Rw, pw)
            befs.append((bef / DH, gts[i][3]))
            afts.append(((wpos(pose, HAND_L) - T).length / DH, gts[i][3]))
        for bn in ORDER:
            arm.pose.bones[bn].matrix_basis = basis[bn]
        bpy.context.view_layer.update()
        if i % 20 == 0:                             # 해석식 자기검증(★함정 8)
            for bn in ORDER:
                a = (A2W @ arm.pose.bones[bn].matrix).translation
                b = (A2W @ pose[bn]).translation
                maxerr = max(maxerr, (a - b).length)
        lows.append(low_of(DST_BODY))
    shift = BIND_LOW - pct(lows, 0.10)
    print("   해석식 자기검증: Blender 평가와 뼈 위치 최대 오차 %.7f (키의 %.5f%%)"
          % (maxerr, maxerr / DH * 100))
    if maxerr > DH * 1e-4:
        raise SystemExit("해석식 FK 가 Blender 평가와 다르다. 리타게팅 신뢰 불가")
    print("   접지 보정: 메시 최저 %.4f~%.4f (10분위 %.4f) -> 바인드 %.4f (%+.4f)"
          % (min(lows), max(lows), pct(lows, 0.10), BIND_LOW, shift))
    if DO_GRIP:
        # ★게이트가 0 인 프레임(원래 손을 놓는 구간)은 이탈을 따질 대상이 아니다.
        g_b = [d for d, w in befs if w > 0.5] or [0.0]
        g_a = [d for d, w in afts if w > 0.5] or [0.0]
        print("   왼손 이탈(목표까지, 키 정규화): 전체 IK전 %.4f~%.4f / IK후 %.4f~%.4f"
              % (min(d for d, _ in befs), max(d for d, _ in befs),
                 min(d for d, _ in afts), max(d for d, _ in afts)))
        print("        파지 프레임만: IK전 %.4f~%.4f (최대 %.2f주먹) -> IK후 %.4f~%.4f"
              " (최대 %.2f주먹)"
              % (min(g_b), max(g_b), max(g_b) / FIST,
                 min(g_a), max(g_a), max(g_a) / FIST))

    # --- 2차: 보정을 넣고 키를 찍는다 ---
    act = new_action(name)
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        pw = (DREST[ROOT_BONE][1] + (praw[i] - pmean) * K_TRANS
              + Vector((0, 0, shift)))
        Rw = delta_rots()
        pose, basis = build(Rw, pw)
        if DO_GRIP:
            apply_grip(pose, Rw, gts[i])
            pose, basis = build(Rw, pw)
        for bn in ORDER:
            arm.pose.bones[bn].matrix_basis = basis[bn]
        bpy.context.view_layer.update()
        for b in arm.pose.bones:
            b.keyframe_insert("location", frame=i + 1)
            b.keyframe_insert("rotation_quaternion", frame=i + 1)
            b.keyframe_insert("scale", frame=i + 1)
    print("   -> 액션 %s  f1~%d (%.3f초 @30fps)" % (name, nf, (nf - 1) / 30.0))
    return act


BAKED = {}
for c in CLIPS:
    BAKED[c] = bake(c)

# ================================================================ 8) 정리
print("\n[정리]")
for o in list(src_objs):
    print("   소스 오브젝트 제거:", o.name)          # ★함정 6
    bpy.data.objects.remove(o, do_unlink=True)
for o in list(bpy.data.objects):
    if junk(o):
        print("   임포터 Icosphere 제거:", o.name)   # ★함정 5
        bpy.data.objects.remove(o, do_unlink=True)
keep = set(CLIPS)
if KEEP_ORIG:
    for a in dst_acts:
        if a.name.startswith("ORIG_"):
            a.name = "Orig" + a.name[5:]
            a.use_fake_user = True
            keep.add(a.name)
for a in list(bpy.data.actions):
    if a.name not in keep:
        bpy.data.actions.remove(a)
    else:
        a.use_fake_user = True                      # ★함정 4
print("   남긴 액션:", sorted(a.name for a in bpy.data.actions))
print("   남긴 오브젝트:", [(o.name, o.type) for o in sc.objects])

# 텍스처
if TEX_FORMAT not in ("AUTO", ""):
    print("   텍스처를 %s q%d 로 재인코딩한다" % (TEX_FORMAT, TEX_QUALITY))
imgs = []
for o in sc.objects:
    if o.type != "MESH":
        continue
    for m in o.data.materials:
        if not m or not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            im = getattr(nd, "image", None)
            if im is not None and im not in imgs:
                imgs.append(im)
for im in imgs:
    print("   이미지 %-24s %dx%d %s" % (im.name, im.size[0], im.size[1], im.file_format))

# 내보내기 직전 자세를 Idle 첫 프레임으로 둔다(뷰어 기본 자세)
first = BAKED.get(CLIPS[0])
arm.animation_data_clear()
arm.animation_data_create()
arm.animation_data.action = first
try:
    slots = list(getattr(first, "slots", []))
    if slots:
        arm.animation_data.action_slot = slots[0]
except Exception:
    pass
sc.frame_set(1)
bpy.context.view_layer.update()

os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
kw = dict(filepath=OUT_GLB, export_format="GLB", use_selection=False,
          export_apply=True, export_animations=True,
          export_animation_mode="ACTIONS", export_nla_strips=False,
          export_bake_animation=True, export_frame_range=False, export_yup=True)
if TEX_FORMAT not in ("AUTO", ""):
    kw.update(export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
              export_jpeg_quality=TEX_QUALITY)
bpy.ops.export_scene.gltf(**kw)
print("\nEXPORTED %s  %d bytes (%.2f MB)"
      % (OUT_GLB, os.path.getsize(OUT_GLB), os.path.getsize(OUT_GLB) / 1e6))

# ================================================================ 9) 검증
# ★결과 glb 를 **다시 읽어서** 잰다. 액션 슬롯·fake_user·베이크 단계에서
#   조용히 어긋나는 사고가 많았으므로 최종 산출물을 그대로 본다.
if not (VERIFY or RENDER):
    print("검증·렌더 생략")
    raise SystemExit(0)

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath=OUT_GLB)
if sc.render.fps != 30:
    sc.render.fps = 30
arm = next(o for o in sc.objects if o.type == "ARMATURE")
for o in list(sc.objects):
    if o.type == "MESH" and any(c.name == "glTF_not_exported"
                                for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)
BODY = [o for o in sc.objects if o.type == "MESH"
        and not o.name.startswith(("SW_", "SH_"))]
SWORD = next((o for o in sc.objects if o.type == "MESH"
              and o.name.startswith("SW_")), None)
for b in arm.pose.bones:
    b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
zs = []
for o in BODY:
    zs += [(o.matrix_world @ v.co).z for v in o.data.vertices]
H = max(zs) - min(zs)
FLOOR = min(zs)
xs = []
for o in BODY:
    xs += [(o.matrix_world @ v.co).x for v in o.data.vertices]
CX = (min(xs) + max(xs)) / 2
# 자루축(레스트 손 로컬)
HM = arm.matrix_world @ arm.pose.bones[HAND_R].matrix
loc = [HM.inverted() @ (SWORD.matrix_world @ v.co) for v in SWORD.data.vertices] \
    if SWORD else []
UD = max(loc, key=lambda p: p.length).normalized() if loc else None
pr = [p.dot(UD) for p in loc] if loc else [0]
TIP_L, POM_L = max(pr), min(pr)
# 손 로컬 길이 -> 월드 길이(아마추어 스케일). 키로 나눠 보고할 때 필요하다.
HSCALE = HM.to_3x3().to_scale()[0]
arm.data.pose_position = "POSE"
print("\n" + "=" * 78)
print("[검증] %s 재임포트: 키 %.4f / 바닥 %.4f / 액션 %s"
      % (os.path.basename(OUT_GLB), H, FLOOR,
         sorted(a.name for a in bpy.data.actions)))
print("       뼈 %d / 메시 %s" % (len(arm.data.bones),
                                 [(o.name, len(o.data.vertices)) for o in sc.objects
                                  if o.type == "MESH"]))
print("       주먹 하나 = 키의 %.3f = %.4f 월드 = 게임 %.1fcm"
      % (FIST, FIST * H, FIST * 1.75 * 100))


def use(act):
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


REP = {}
TRAIL = {}
if VERIFY:
    print("\n[검증1] 파지: 왼손목 - 자루축 수직거리 (키 정규화. 소스 기준값 0.077)")
    print("  %-8s %7s %8s %8s %8s %9s" % ("클립", "프레임", "최소", "중앙", "최대",
                                          "주먹환산(최대)"))
    for nm in CLIPS:
        act = bpy.data.actions.get(nm)
        if not act or not SWORD:
            continue
        use(act)
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        ds, ts, tips = [], [], []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            RM = arm.matrix_world @ arm.pose.bones[HAND_R].matrix
            Rr = RM.to_3x3()
            Rr.normalize()
            u = (Rr @ UD).normalized()
            P = RM.translation.copy()
            L = (arm.matrix_world @ arm.pose.bones[HAND_L].matrix).translation
            v = L - P
            t = v.dot(u)
            ds.append((v - u * t).length / H)
            ts.append(t / H)
            tips.append(RM @ (UD * TIP_L))          # 칼끝(손 행렬로 직접)
        TRAIL[nm] = tips
        sd = sorted(ds)
        print("  %-8s %7d %8.3f %8.3f %8.3f %9.2f   축상 %.3f~%.3f (자루끝 %.3f)"
              % (nm, len(ds), sd[0], sd[len(sd) // 2], sd[-1], sd[-1] / FIST,
                 min(ts), max(ts), POM_L * HSCALE / H))

    print("\n[검증2] 접지: 발 본 최저 높이(바닥=%.4f)와 메시 뚫림" % FLOOR)
    for nm in CLIPS:
        act = bpy.data.actions.get(nm)
        if not act:
            continue
        use(act)
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        fz, mz = [], []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            fz.append(min((arm.matrix_world @ arm.pose.bones[b].matrix).translation.z
                          for b in ("Bip001 L Foot", "Bip001 R Foot")))
            mz.append(low_of(BODY))
        print("  %-8s 발본 z %.4f~%.4f (키의 %+.2f%%~%+.2f%%) / 메시최저 %.4f~%.4f "
              "(바닥대비 %+.2f%%)"
              % (nm, min(fz), max(fz), (min(fz) - FLOOR) / H * 100,
                 (max(fz) - FLOOR) / H * 100, min(mz), max(mz),
                 (min(mz) - FLOOR) / H * 100))

    # ★옷(치마·어깨끈)은 강체 스키닝이라 깊게 앉으면 찢어진다. s15 는 걷기/달리기까지만
    #   봤는데 이 무브셋은 그보다 훨씬 깊게 앉는다(일격기·착지). 모서리 늘음으로 잰다.
    cloth = next((o for o in BODY if o.name.startswith("cloth")), None)
    if cloth:
        print("\n[검증2-1] 옷 모서리 늘음(1.0 = 원래 길이. 2.0 넘으면 눈에 띈다)")
        ed = [(e.vertices[0], e.vertices[1]) for e in cloth.data.edges]
        L0 = [(cloth.data.vertices[a].co - cloth.data.vertices[b].co).length
              for a, b in ed]
        keep = [k for k in range(len(ed)) if L0[k] >= H * 0.004]
        for nm in CLIPS:
            act = bpy.data.actions.get(nm)
            if not act:
                continue
            use(act)
            f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
            mx, over = 1.0, 0
            for f in range(f0, f1 + 1):
                sc.frame_set(f)
                dg = bpy.context.evaluated_depsgraph_get()
                ev = cloth.evaluated_get(dg)
                me = ev.to_mesh()
                vs = [v.co for v in me.vertices]
                n = 0
                for k in keep:
                    a, b = ed[k]
                    r = (vs[a] - vs[b]).length / L0[k]
                    if r > mx:
                        mx = r
                    if r > 2.0:
                        n += 1
                ev.to_mesh_clear()
                over = max(over, n)
            print("  %-8s 최대 늘음 %.2f배 / 2배 초과 모서리 최대 %d개 (판정대상 %d)"
                  % (nm, mx, over, len(keep)))

    # 발 속도(probe_stride 와 같은 방식: 접지 구간의 프레임별 이동량 중앙값)
    print("\n[검증3] 발 속도(게임 키 1.75 환산). main.js CHAR_CFG 의 walk/run spd 후보")
    SCALE = 1.75 / H
    FWD = None
    for nm in ("Walk", "Run"):
        act = bpy.data.actions.get(nm)
        if not act:
            continue
        use(act)
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        rows = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            bpy.context.view_layer.update()

            def wp(k):
                return (arm.matrix_world @ arm.pose.bones[k].matrix).translation.copy()
            rows.append((wp(PELVIS), wp("Bip001 L Foot"), wp("Bip001 R Foot"),
                         wp("Bip001 L Toe0"), wp("Bip001 R Toe0")))
        if FWD is None:
            order = sorted(range(len(rows)), key=lambda i: min(rows[i][3].z, rows[i][4].z))
            acc = Vector((0, 0, 0))
            for i in order[:max(1, len(rows) // 4)]:
                r = rows[i]
                a, t = (r[1], r[3]) if r[3].z <= r[4].z else (r[2], r[4])
                d = t - a
                d.z = 0
                if d.length > 1e-6:
                    acc += d.normalized()
            FWD = acc.normalized() if acc.length > 1e-6 else Vector((0, -1, 0))
            print("  전방 FWD = (%.2f, %.2f)" % (FWD.x, FWD.y))
        # ★달리기는 접지가 짧다(체공 구간이 있다). 임계값을 넓혀 가며 찾는다.
        #   고정 3%로만 재면 '접지 구간 못 찾음' 이 나온다(실측: 달리기 26프레임).
        grip, used_thr = [], 0.0
        for kthr in (0.03, 0.05, 0.08, 0.12):
            grip = []
            for fi, ti, tag in ((1, 3, "왼발"), (2, 4, "오른발")):
                zz = [r[ti].z for r in rows]
                thr = min(zz) + kthr * H
                on = [i for i, z in enumerate(zz) if z <= thr]
                bi, cur = [], []
                for i in on:
                    if cur and i == cur[-1] + 1:
                        cur.append(i)
                    else:
                        if len(cur) > len(bi):
                            bi = cur
                        cur = [i]
                if len(cur) > len(bi):
                    bi = cur
                if len(bi) < 3:
                    continue
                proj = [(rows[i][fi] - rows[i][0]).dot(FWD) for i in bi]
                dd = sorted(proj[k] - proj[k + 1] for k in range(len(proj) - 1))
                grip.append((dd[len(dd) // 2] * 30, len(bi), tag))
            used_thr = kthr
            if grip:
                break
        if not grip:
            print("  %-6s 접지 구간 못 찾음" % nm)
            continue
        v = sum(g[0] for g in grip) / len(grip) * SCALE
        print("  %-6s %d프레임 %.3f초 / 접지판정 발끝 키의 %.0f%% 안 / %s -> 발속도 %.2f"
              % (nm, f1 - f0, (f1 - f0) / 30.0, used_thr * 100,
                 " ".join("%s %d장" % (g[2], g[1]) for g in grip), v))
        for ts in (1.0, 1.2, 1.5, 1.84):
            print("        재생속도 %.2f -> 이동속도 %.2f" % (ts, v * ts))

# 대표 프레임: 칼끝이 가장 빠른 프레임(= 타격 순간). 없으면 가운데.
for nm in CLIPS:
    act = bpy.data.actions.get(nm)
    if not act:
        continue
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    tips = TRAIL.get(nm)
    if tips and len(tips) > 2:
        sp = [(tips[i + 1] - tips[i]).length for i in range(len(tips) - 1)]
        REP[nm] = f0 + max(range(len(sp)), key=lambda i: sp[i])
    else:
        REP[nm] = (f0 + f1) // 2
print("\n[대표 프레임] " + "  ".join("%s=f%d" % (k, v) for k, v in REP.items()))

# ================================================================ 10) 렌더
if RENDER:
    os.makedirs(OUTDIR, exist_ok=True)
    ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids \
        else "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = 520, 760
    sc.render.film_transparent = False
    bpy.ops.mesh.primitive_plane_add(size=H * 6, location=(CX, 0, FLOOR))
    floor = bpy.context.object
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        0.34, 0.36, 0.40, 1)
    fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    floor.data.materials.append(fm)
    li = bpy.data.lights.new("S", "SUN")
    li.energy = 4.0
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = (math.radians(58), 0, math.radians(-30))
    sc.collection.objects.link(so)
    li2 = bpy.data.lights.new("F", "SUN")
    li2.energy = 1.5
    li2.color = (0.7, 0.82, 1.0)
    so2 = bpy.data.objects.new("F", li2)
    so2.rotation_euler = (math.radians(-30), 0, math.radians(130))
    sc.collection.objects.link(so2)
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = 55
    TGT0 = Vector((CX, 0, FLOOR + H * 0.50))
    DIR = {"front": Vector((0, -1, 0.05)), "side": Vector((-1, 0, 0.03))}

    def shoot(path, view, tgt=None, dist=None, eye=None):
        t = tgt or TGT0
        d = dist or (H * 2.05)
        off = (eye or DIR[view]).normalized() * d
        cam.location = t + off
        dd = t - cam.location
        cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print("   rendered", os.path.basename(path))

    def grip_shot(path):
        """★파지 접사는 반드시 '자루축에 수직'인 방향에서 봐야 한다.
        고정 측면에서 보면 자루를 팔이 가려 두 손이 겹쳐 보이고 판정이 안 된다."""
        RM = arm.matrix_world @ arm.pose.bones[HAND_R].matrix
        Rr = RM.to_3x3()
        Rr.normalize()
        u = (Rr @ UD).normalized() if UD else Vector((0, 0, 1))
        P = RM.translation.copy()
        L = (arm.matrix_world @ arm.pose.bones[HAND_L].matrix).translation.copy()
        e = u.cross(Vector((0, 0, 1)))
        if e.length < 1e-3:
            e = u.cross(Vector((0, 1, 0)))
        e.normalize()
        mid = (P + L) / 2
        # ★수직 방향은 두 개(±)다. 몸 반대쪽을 골라야 머리·어깨에 안 가린다.
        pel = (arm.matrix_world @ arm.pose.bones[PELVIS].matrix).translation
        away = mid - pel
        away.z *= 0.2
        if e.dot(away) < 0:
            e = -e
        shoot(path, "side", tgt=mid, dist=H * 1.05, eye=e)

    for nm in CLIPS:
        act = bpy.data.actions.get(nm)
        if not act:
            continue
        use(act)
        sc.frame_set(REP[nm])
        bpy.context.view_layer.update()
        for view in ("front", "side"):
            shoot(os.path.join(OUTDIR, "%s_%s_f%02d.png" % (nm, view, REP[nm])), view)
        # 파지 접사: 두 손이 같은 자루를 쥐고 있는지 눈으로 판정하는 컷
        grip_shot(os.path.join(OUTDIR, "grip_%s_f%02d.png" % (nm, REP[nm])))

    # 공격 3종은 스윙 흐름을 5장으로 본다(한 장으로는 궤적을 못 읽는다)
    for nm in ("Attack", "Heavy", "Wide"):
        act = bpy.data.actions.get(nm)
        if not act:
            continue
        use(act)
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        for k in range(5):
            f = f0 + int(round((f1 - f0) * (0.15 + 0.7 * k / 4.0)))
            sc.frame_set(f)
            bpy.context.view_layer.update()
            shoot(os.path.join(OUTDIR, "swing_%s_%d_f%02d.png" % (nm, k, f)),
                  "side", dist=H * 2.6)

    # 칼끝 궤적: 공격 클립은 궤적이 곧 정체성이다
    trailmat = bpy.data.materials.new("trail")
    trailmat.use_nodes = True
    nt = trailmat.node_tree
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.35, 0.12, 1)
    em.inputs["Strength"].default_value = 12.0
    nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
    for nm in ("Attack", "Heavy", "Wide"):
        pts = TRAIL.get(nm)
        act = bpy.data.actions.get(nm)
        if not pts or not act:
            continue
        cu = bpy.data.curves.new("trail_" + nm, "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p.x, p.y, p.z, 1)
        cu.bevel_depth = H * 0.008
        cu.materials.append(trailmat)
        ob = bpy.data.objects.new("trail_" + nm, cu)
        sc.collection.objects.link(ob)
        use(act)
        sc.frame_set(REP[nm])
        bpy.context.view_layer.update()
        # ★궤적은 몸보다 훨씬 크다. 궤적 + 몸을 다 담게 카메라를 물린다.
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts),
                     min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts),
                     max(p.z for p in pts)))
        lo.z = min(lo.z, FLOOR)
        hi.z = max(hi.z, FLOOR + H)
        ctr = (lo + hi) / 2
        ctr.x, ctr.y = CX, 0
        rad = max((hi - lo).length / 2, H * 0.6)
        print("   %s 칼끝 궤적 상자 x %.2f~%.2f y %.2f~%.2f z %.2f~%.2f"
              % (nm, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))
        for view in ("front", "side"):
            shoot(os.path.join(OUTDIR, "trail_%s_%s.png" % (nm, view)), view,
                  tgt=ctr, dist=rad * 3.0)
        bpy.data.objects.remove(ob, do_unlink=True)
    print("\n렌더 완료:", OUTDIR)

print("\nDONE")
