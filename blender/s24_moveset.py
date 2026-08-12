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

★★한 손 파지 (RELEASE. 기본 Jump) — 2026-08-12 오너 지시
  "점프 자세 좀 바꿔줘. 칼을 양손으로 쥐고 뛰는 게 물리적으로 말이 안 되잖아.
   한 손에 쥐고 뛰어야지."
  RELEASE 에 적은 클립은 왼손을 자루에서 떼고 **균형 잡는 팔**로 바꾼다.
  자세한 표와 근거는 아래 [한 손 파지] 절에 있다.

★★왼손 손목 (HAND_GRIP. 기본 켬) — 2026-08-12 오너 지시 3차
  "왼쪽(손)은 엄청 꺾여 있음. 그리고 (X 쓸 때) 왼쪽 손도 이상하게 꺾여버리고."
  IK 는 손목 **위치**만 맞추고 손 방향은 리타게팅에 맡겨 왔다. 그래서 왼손목이
  Attack 169도 · Heavy 161도까지 꺾였다(사람 한계 60~70도). 자루에서 역산해
  손뼈 회전만 다시 쓴다. 자세한 표와 근거는 아래 [왼손 손목] 절에 있다.

★★검 든 오른팔 내리기 (SWORD_DOWN. 기본 Jump) — 2026-08-12 오너 지시 2차
  "점프할 때 한 손으로 검을 앞으로 들고 있는데 넌 그게 말이 된다 생각하냐?"
  1차는 왼손만 풀었고 오른팔은 소스 그대로 **검을 앞으로 겨눈** 자세였다.
  SWORD_DOWN 에 적은 클립은 오른팔 3본을 어깨에서 통째로 돌려 검을 몸 옆·아래로
  내린다. 자세한 표와 근거는 아래 [오른팔 내리기] 절에 있다.

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
  RELEASE   한 손으로 쥘 클립(쉼표)   기본 Jump  (빈 값이면 전부 양손)
  SWORD_DOWN 검 든 오른팔을 내릴 클립  기본 Jump  (빈 값이면 소스 그대로)
  HAND_GRIP 1(기본) 왼손목 방향을 자루에서 역산 / 0 옛 판(리타게팅 그대로) 재현
  WRIST_LIM 왼손목 기하각 상한(도)     기본 60  (레스트 중립이 16.8도인 잣대다)
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
# 한 손 파지 클립(오너 지시. 아래 [한 손 파지] 절 참조)
RELEASE = [c.strip() for c in os.environ.get("RELEASE", "Jump").split(",") if c.strip()]
# 검 든 오른팔을 내릴 클립(오너 지시 2차. 아래 [오른팔 내리기] 절 참조)
SWDOWN = [c.strip() for c in os.environ.get("SWORD_DOWN", "Jump").split(",") if c.strip()]
# 왼손목-자루 오프셋 환산 배율에 곱하는 보정. 두 리그의 손 크기가 키 대비 많이
# 다를 때만 건드린다(아래 [자루] 절에서 손 크기 차이를 찍는다).
GRIP_K = float(os.environ.get("GRIP_K", "1.0"))
# 주먹 하나를 키의 몇 %로 볼 것인가. 175cm 성인 주먹 폭 ~9.6cm.
FIST = 0.055

# ── Meshy 프리셋 모션을 **다른 소스**에서 끌어오기 (13-모션이식, 2026-08-12) ──
# 오너 "베는모션을 meshy ai로 해와 차라리". 베기 3종(Z/X/C)만 slayer 가 아니라
# Meshy 애니메이트 프리셋에서 가져온다. 나머지(Idle/Walk/Run/Jump)는 그대로 slayer 다.
#   ANIM_DIR   프리셋 glb 폴더            예 incoming/meshy_anim
#   ANIM_SPEC  클립별 이어붙이기 대본     ";" 로 클립, "+" 로 구간을 나눈다
#              "Attack=sword_slash:9-24@1.15+left_slash:13-28@1.15; Heavy=axe_chop:118-140@1.7"
#              구간 = 파일이름:소스첫프레임-끝프레임@배속   (배속 1.5 = 1.5배 빠르게)
#              소스 프레임은 **소수도 된다**(subframe 으로 샘플한다).
#   ANIM_BLEND 구간 이음매 크로스페이드 프레임 수(기본 4). 0 이면 뚝 끊긴다
#   ANIM_TIP_K 칼끝 진단용 배율. 하류 s34 가 1번 칼을 키우는 몫(s27 TIP_K 와 같은 값)
# ★이 소스에는 검이 없다(맨손 프리셋이다). 그래서 왼손 파지 IK·손목 교정은
#   이 클립들에 **안 건다** — 두 손 거리 실측 0.48~0.87H(=69~125cm)라 애초에
#   한 손 파지 모션이다. 억지로 왼손을 자루로 끌면 원본 모션이 망가진다.
ANIM_DIR = os.environ.get("ANIM_DIR", "")
ANIM_SPEC = os.environ.get("ANIM_SPEC", "")
ANIM_BLEND = int(os.environ.get("ANIM_BLEND", "4"))
ANIM_TIP_K = float(os.environ.get("ANIM_TIP_K", "1.7806"))


def parse_anim_spec(s):
    """'Attack=a:1-20@1.2+b:5-14~6' -> {클립: [(파일, f0, f1, 배속, 앞이음매길이)]}

    ~N 은 **이 구간으로 넘어오는 이음매**를 몇 장에 걸쳐 섞을지다.
    안 적으면 ANIM_BLEND. 단 앞 구간과 **같은 파일이고 프레임이 이어지면 0**이다
    (같은 소스가 이어지는 자리는 자세가 이미 연속이라 섞을 게 없다.
     이 문법이 곧 '배속 램프' 다 — 구간을 잘라 배속만 바꿔 이어 붙이면 된다).
    """
    out = {}
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        clip, rest = part.split("=", 1)
        segs = []
        for sg in rest.split("+"):
            sg = sg.strip()
            bl = None
            if "~" in sg:
                sg, bb = sg.split("~")
                bl = int(bb)
            spd = 1.0
            if "@" in sg:
                sg, sp = sg.split("@")
                spd = float(sp)
            stem, rng = sg.split(":")
            fa, fb = rng.split("-")
            stem = stem.strip()
            fa, fb = float(fa), float(fb)
            if bl is None:
                # ★1 이다(0 이 아니다). 앞 구간의 마지막 소스 프레임과 이 구간의 첫
                #   프레임이 같은 자리라, 0 으로 두면 **같은 자세가 두 장 연달아** 나가
                #   그 한 장에서 칼끝 속도가 0 으로 꺼진다(= 타격 구간이 갈라진다).
                bl = (1 if (segs and segs[-1][0] == stem
                            and abs(segs[-1][2] - fa) < 1e-6) else ANIM_BLEND)
            segs.append((stem, fa, fb, spd, bl))
        out[clip.strip()] = segs
    return out


ANIM = parse_anim_spec(ANIM_SPEC) if (ANIM_DIR and ANIM_SPEC) else {}

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
# 검 든 팔. 어깨에서 통째로 돌릴 3본(손·검은 FK 자식이라 강체로 따라온다)
R_ARM = ("Bip001 R UpperArm", "Bip001 R Forearm", "Bip001 R Hand")
HAND_R = "Bip001 R Hand"
HAND_L = "Bip001 L Hand"
# ★쇄골이 매달린 척추 마디. 이름이 헷갈리게 붙어 있다(실측 계층:
#   Pelvis -> Chest2 -> Chest -> Spine -> Clavicle). 즉 **Spine 이 제일 윗마디**다.
TORSO = "Bip001 Spine"
NECK = "Bip001 Neck"
CLAV_L, CLAV_R = "Bip001 L Clavicle", "Bip001 R Clavicle"

print("=" * 78)
print("[설정] 소스 %s" % SRC_GLB)
print("       타깃 %s" % DST_GLB)
print("       결과 %s" % OUT_GLB)
print("       클립 %s / 왼팔IK %s" % (",".join(CLIPS), "ON" if GRIP_IK else "OFF"))
print("       한 손 파지(왼손을 떼는 클립) %s" % (",".join(RELEASE) or "없음"))
print("       오른팔 내리기(검 든 팔) %s" % (",".join(SWDOWN) or "없음"))

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
missing = [c for c in CLIPS if c not in SRC_ACT and c not in ANIM]
if missing:
    raise SystemExit("소스에 없는 클립: %s (있는 것: %s)" % (missing, sorted(SRC_ACT)))
if ANIM:
    print("       ★Meshy 프리셋에서 가져올 클립: %s" % sorted(ANIM))

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
# 왼팔 길이(어깨->팔꿈치->손목). 균형 팔 목표를 이 길이의 비로 준다.
ARM_L = ((DREST[L_ARM[1]][1] - DREST[L_ARM[0]][1]).length
         + (DREST[L_ARM[2]][1] - DREST[L_ARM[1]][1]).length)
print("\n[레스트] 소스 키 %.4f / 타깃 키 %.4f  (키비율 K_H=%.4f)" % (SH, DH, K_H))
print("         다리(골반-발목) 소스 %.4f / 타깃 %.4f  (골반이동 배율 %.4f)"
      % (LEG_S, LEG_D, K_TRANS))
print("         타깃 바인드 최저 z %.4f" % BIND_LOW)

# ================================================ 4b) Meshy 프리셋 소스 (2026-08-12)
# 프리셋 glb 하나하나가 자기 아마추어·메시를 들고 온다. 뼈 이름은 Meshy 원본
# (Hips/LeftArm/Spine02)이라 위 RENAME 표를 그대로 먹인다. 그러면 계층·이름이
# 타깃과 **한 글자도 안 틀리게** 같아진다(실측: 24본 전부 일치, 부모도 전부 일치).
# 레스트만 다르다 — 손 5.2도 / 팔뚝 10.4도 / 위팔 11.4도, 골반 head 최대 6.5cm.
# 그래서 절대 회전 복사가 아니라 **레스트 델타**로 옮긴다(이 파일의 기본 방식 그대로).
ALT_CTX = {}          # 파일이름 -> (아마추어, S2W, SREST, SH, SLOW, MAP, 액션)


def load_alt(stem):
    """프리셋 glb 하나를 소스로 읽어 리타게팅에 필요한 것만 재 둔다."""
    path = os.path.join(ROOT, ANIM_DIR, stem + ".glb")
    objs, acts = imp(path)
    a = next(o for o in objs if o.type == "ARMATURE")
    a.name = "ALT_" + stem
    src_objs.extend(objs)                          # ★함정 6: 정리 목록에 같이 넣는다
    have = set(b.name for b in a.data.bones)
    todo = [(o_, n_) for o_, n_ in RENAME if o_ in have and n_ not in have]
    nm = dict(todo)
    for old, new in todo:
        a.data.bones[old].name = new
    meshes = [o for o in objs if o.type == "MESH"]
    for m in meshes:                               # ★함정 7: 정점 그룹도 같이
        for g in m.vertex_groups:
            if g.name in nm:
                g.name = nm[g.name]
    for b in a.pose.bones:
        b.rotation_mode = "QUATERNION"
        b.matrix_basis = Matrix()
    W, R = rest_world(a)
    body = [o for o in meshes if not junk(o)]
    a.data.pose_position = "REST"
    bpy.context.view_layer.update()
    H, LOW = height(body)
    a.data.pose_position = "POSE"
    bones = set(b.name for b in a.data.bones)
    M = {}
    for bn in DST_BONES:
        M[bn] = bn if bn in bones else (
            FALLBACK[bn] if bn in FALLBACK and FALLBACK[bn] in bones else None)
    act = acts[0]
    act.name = "ALT_" + stem
    if a.animation_data is None:
        a.animation_data_create()
    a.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            a.animation_data.action_slot = slots[0]
    except Exception:
        pass
    unmapped = [bn for bn in DST_BONES if M[bn] is None]
    print("   %-14s 뼈 %d(이름바꿈 %d) / 키 %.4f / 액션 %s f%.0f~%.0f"
          " / 대응없는 타깃뼈 %s"
          % (stem, len(bones), len(todo), H, act.name,
             act.frame_range[0], act.frame_range[1], unmapped or "없음"))
    return dict(arm=a, S2W=W, SREST=R, SH=H, SLOW=LOW, MAP=M, act=act,
                f0=int(act.frame_range[0]), f1=int(act.frame_range[1]))


if ANIM:
    print("\n[프리셋 소스] %s" % os.path.join(ROOT, ANIM_DIR))
    for _stems in ANIM.values():
        for _st in [g[0] for g in _stems]:
            if _st not in ALT_CTX:
                ALT_CTX[_st] = load_alt(_st)
    # 레스트 어긋남을 도 단위로 한 번 찍어 둔다(리타게팅이 필요한 근거)
    for _st, _cx in ALT_CTX.items():
        worst, wbn = 0.0, ""
        for bn in DST_BONES:
            sn = _cx["MAP"].get(bn)
            if not sn:
                continue
            X = _cx["SREST"][sn][0].inverted() @ DREST[bn][0]
            d = math.degrees(X.to_quaternion().angle)
            if d > worst:
                worst, wbn = d, bn
        print("   %-14s 레스트 최대 어긋남 %.2f도 (%s) / 키비율 %.4f"
              % (_st, worst, wbn, DH / _cx["SH"]))


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


# ---- 칼끝 방향 (아래 [오른팔 내리기] 가 겨누는 축) ----
# ★게임이 처음 장착하는 칼로 잰다(swordIdx=0 = nokseun). 하류 s34 가 그 칼을
#   1.78배로 다시 앉히지만 **같은 반직선 위**라 방향은 안 변한다(s34 로그 0.017도).
#   기준은 measureBlade 와 같다: 손 레스트 로컬에서 원점에서 가장 먼 정점.
def tip_dir_local(a, name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return None
    HMi = hand_rest_matrix(a).inverted()
    loc = [HMi @ (ob.matrix_world @ v.co) for v in ob.data.vertices]
    return max(loc, key=lambda p: p.length).normalized()


GAME_SW = next((o.name for o in bpy.data.objects
                if o.type == "MESH" and o.parent == arm
                and o.name.startswith("SW_nokseun")), dname)
TIP_DIR = tip_dir_local(arm, GAME_SW) if GAME_SW else None
if TIP_DIR is not None:
    _r = DREST[HAND_R][0] @ TIP_DIR
    _o = tip_dir_local(arm, dname)
    print("   칼끝 축: %s 기준 손로컬 (%.3f,%.3f,%.3f) / 레스트 월드 (%.3f,%.3f,%.3f)"
          "  (파지 기준 칼 %s 와 %.2f도 차)"
          % (GAME_SW, TIP_DIR.x, TIP_DIR.y, TIP_DIR.z, _r.x, _r.y, _r.z,
             dname, math.degrees(TIP_DIR.angle(_o)) if _o else -1))


# ---- 왼 주먹 좌표계 (아래 [왼손 손목] 이 쓴다) ----
# ★뼈 로컬축을 안 믿는다. 손 본에 웨이트 0.5 초과인 몸 정점으로 직접 만든다.
#   팔축   = 손목 원점 -> 주먹 중심 (기하로 확정)
#   구멍축 = 팔축 수직 평면에서 2차원 주성분의 넓은 쪽(손가락 마디가 늘어선 축).
#            막대를 쥐면 이 축으로 지나간다. 부호는 **엄지 쪽**으로 고정한다.
#   ★3차원 주성분을 그냥 쓰면 손이 팔축으로 길쭉해서 축이 대각으로 섞인다(s31 함정과 같다).
# ★엄지 부호는 기하로 못 가른다(주먹에 구멍이 안 뚫려 있다). 2026-08-12 에 오른 주먹
#   접사(renders/history/v99_wave13/wrist/fisttex/)를 눈으로 보고 오른손 엄지축의 레스트
#   월드 방향을 정했고, 왼손은 그것을 좌우 대칭(X 부호 반전)한 값이다. 캐릭터 좌우축이
#   월드 X 인 것은 레스트 팔축 실측으로 확인했다(오른팔 -X / 왼팔 +X).
THUMB_REF_W = {HAND_R: Vector((0.285, -0.953, -0.100)),
               HAND_L: Vector((-0.285, -0.953, -0.100))}


def fist_frame(a, meshes, bone):
    """(주먹중심, 팔축, 엄지쪽 구멍축, 손등축). 전부 손뼈 로컬. 레스트에서 잰다."""
    import numpy as np
    a.data.pose_position = "REST"
    bpy.context.view_layer.update()
    HM = (a.matrix_world @ a.pose.bones[bone].matrix).copy()
    a.data.pose_position = "POSE"
    HMi = HM.inverted()
    P = []
    for o in meshes:
        g = o.vertex_groups.get(bone)
        if g is None:
            continue
        for v in o.data.vertices:
            w = next((x.weight for x in v.groups if x.group == g.index), 0.0)
            if w > 0.5:
                P.append(HMi @ (o.matrix_world @ v.co))
    if len(P) < 12:
        return None
    C = Vector((sum(p.x for p in P) / len(P), sum(p.y for p in P) / len(P),
                sum(p.z for p in P) / len(P)))
    ax = C.normalized()
    e1 = Vector((1, 0, 0)) if abs(ax.x) < 0.9 else Vector((0, 1, 0))
    e1 = (e1 - ax * e1.dot(ax)).normalized()
    e2 = ax.cross(e1)
    Q = []
    for p in P:
        q = p - C
        q = q - ax * q.dot(ax)
        Q.append([q.dot(e1), q.dot(e2)])
    w2, V2 = np.linalg.eigh(np.array(Q, dtype=float).T @ np.array(Q, dtype=float))
    t = (e1 * V2[0, 1] + e2 * V2[1, 1]).normalized()
    R3 = HM.to_3x3()
    R3.normalize()
    if (R3 @ t).dot(THUMB_REF_W[bone]) < 0:
        t = -t
    d = (R3 @ t).dot(THUMB_REF_W[bone])
    if abs(d) < 0.85:
        print("   ★엄지축 기준벡터와 %.2f 밖에 안 맞는다(%s). 리그가 바뀌었으면 접사를"
              " 다시 찍고 THUMB_REF_W 를 갱신해라" % (d, bone))
    return C, ax, t, t.cross(ax).normalized()


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

FF_L = fist_frame(arm, DST_BODY, HAND_L)
if FF_L:
    print("   왼 주먹(손뼈 로컬): 중심 (%+.2f,%+.2f,%+.2f) / 팔축 (%+.3f,%+.3f,%+.3f)"
          " / 엄지쪽 구멍축 (%+.3f,%+.3f,%+.3f)"
          % (FF_L[0].x, FF_L[0].y, FF_L[0].z, FF_L[1].x, FF_L[1].y, FF_L[1].z,
             FF_L[2].x, FF_L[2].y, FF_L[2].z))

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


# ── 소스 갈아끼우기 (13-모션이식) ──
# 리타게팅 식은 소스가 누구든 똑같다. 바뀌는 것은 '어느 아마추어를 읽나(src/S2W)',
# '그 소스의 레스트가 뭐냐(SREST)', '뼈를 어떻게 대느냐(MAP)', '키가 얼마냐(SH)' 뿐이다.
# 그래서 전역 넷만 갈아끼우면 위 함수들이 그대로 프리셋 소스를 읽는다.
# ★ANIM 을 안 쓰면 이 함수는 한 번도 안 불린다 = 옛 경로는 한 글자도 안 변한다.
_SRC_MAIN = None


def switch_src(cx):
    global src, S2W, SREST, MAP, SH
    if cx is None:
        src, S2W, SREST, MAP, SH = _SRC_MAIN
    else:
        src, S2W, SREST, MAP, SH = (cx["arm"], cx["S2W"], cx["SREST"],
                                    cx["MAP"], cx["SH"])


_SRC_MAIN = (src, S2W, SREST, MAP, SH)


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


def two_bone_ik(S, E, W, T, pole=None):
    """어깨 S / 팔꿈치 E / 손목 W 를 목표 T 로 보내는 회전 두 개(월드 쿼터니언).

    반환 (R1, R2, 실제도달점). R1 은 위팔에, R2@R1 은 팔뚝·손에 곱한다.
    팔꿈치 스위블(굽는 평면)은 현재 자세를 그대로 유지한다. 그래야 어깨가
    엉뚱하게 돌지 않고 리타게팅이 만든 몸짓이 살아남는다.
    ★pole 을 주면 스위블을 그쪽으로 강제한다(팔꿈치가 향할 방향). 목표를 원래
      자세에서 멀리 옮길 때는 스위블을 물려받으면 안 된다 — 자루를 쥐던 팔꿈치
      평면을 그대로 들고 옆으로 가면 **알통 자랑 자세**가 나온다(실측으로 봤다).
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
    ev = pole if pole is not None else (E - S)
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


# ---------------------------------------------------------------- 한 손 파지
# ★오너 지시(2026-08-12): "점프 자세 좀 바꿔줘. 칼을 양손으로 쥐고 뛰는 게
#   물리적으로 말이 안 되잖아. 한 손에 쥐고 뛰어야지."
#   소스(slayer)의 점프는 양손검 전제라 왼손이 자루에 붙어 있다. 게다가 s34 가
#   1번 칼을 1.5배로 다시 앉힌 뒤로는 그 왼손 자리가 **칼 아래끝보다 더 아래**다
#   (최종 glb 실측: 왼손 자루축 -0.234m / 칼 아래끝 -0.225m). 허공을 쥔 손이었다.
#
# 어떻게 바꾸나 — 각도를 굳히지 않고 **가슴 좌표계에 매단다**
#   고정 포즈를 넣으면 뻣뻣하다. 어깨(위팔 머리)에서 '가슴 기준 방향'으로 목표를
#   주면 몸이 뛰고 기울 때 팔이 통째로 따라가므로 원본 점프의 생동감이 남는다.
#   그 위에 위상별 (벌림 A / 앞으로 F / 뻗음 k) 를 얹어 도약->체공->착지를 만든다.
#
# ★위상표를 이렇게 잡은 근거: 게임은 이 클립을 통째로 재생하지 않는다
#   (main.js CHAR_CFG.jump = start 0.00 / rise 0.20 / fall 0.40 / land 0.50 / end 0.73).
#   올라가는 동안 **f7 에서 멈춰 있고** 내려오는 동안 **f13 에서 멈춘다.** 착지하면
#   f16~f23 만 재생한다. 그래서 화면에서 제일 오래 보이는 것이 f7·f13 자세다.
#   표의 t=0.27(f7) t=0.55(f13) 이 그 두 장이다.
BAL_KEYS = [                    # (위상 t, 벌림 A도, 앞으로 F도, 뻗음 k=팔길이 비)
    (0.00, 14, -12, 0.82),      # f1  웅크림. 아직 자루를 쥐고 있다(가중치 0)
    (0.18, 40, 18, 0.88),       # f5  도약. 손을 놓으며 팔이 벌어진다
    (0.27, 46, 24, 0.90),       # f7  ★상승 내내 이 자세로 멈춘다
    (0.55, 54, 4, 0.92),        # f13 ★하강 내내 이 자세로 멈춘다(팔을 뒤로 벌려 준비)
    (0.70, 34, 10, 0.86),       # f16 착지 흡수. 팔을 내린다
    (1.00, 18, 2, 0.82),        # f23 회복. Idle 로 0.18초 크로스페이드되며 다시 쥔다
]
BAL_ON, BAL_FULL = 0.02, 0.18   # 파지->균형 전환 구간(위상). 도약 순간에 놓는다
# 팔꿈치가 향할 방향(가슴 좌표계 X=왼쪽/Y=위/Z=앞). 아래·약간 뒤·약간 안쪽.
BAL_POLE = (-0.10, -1.00, -0.45)


def bal_key(t):
    """위상 t 의 (A,F,k). 구간 안은 smoothstep(속도가 튀면 팔이 홱 꺾인다)."""
    ks = BAL_KEYS
    if t <= ks[0][0]:
        return ks[0][1:]
    for i in range(len(ks) - 1):
        t0, t1 = ks[i][0], ks[i + 1][0]
        if t <= t1:
            s = (t - t0) / max(1e-6, t1 - t0)
            s = s * s * (3 - 2 * s)
            return tuple(a + (b - a) * s for a, b in zip(ks[i][1:], ks[i + 1][1:]))
    return ks[-1][1:]


def bal_weight(t):
    if t <= BAL_ON:
        return 0.0
    if t >= BAL_FULL:
        return 1.0
    s = (t - BAL_ON) / (BAL_FULL - BAL_ON)
    return s * s * (3 - 2 * s)


def torso_frame(pose):
    """가슴 좌표계 (열이 축) X=왼쪽 / Y=위(척추) / Z=앞.
    ★뼈 로컬축을 믿지 않는다. 척추 방향과 쇄골 두 개로 직접 만든다
      (Meshy 리그는 마디 이름이 뒤집혀 있어서 로컬축을 가정하면 틀린다)."""
    up = (wpos(pose, NECK) - wpos(pose, TORSO)).normalized()
    lat = wpos(pose, CLAV_L) - wpos(pose, CLAV_R)
    lat = (lat - up * lat.dot(up)).normalized()
    return Matrix((lat, up, lat.cross(up))).transposed()


def balance_target(pose, t):
    """이번 프레임의 왼손목 목표(균형 팔). 어깨에서 가슴 기준 방향으로 뻗는다."""
    A, F, k = bal_key(t)
    A, F = math.radians(A), math.radians(F)
    u = Vector((math.sin(A), -math.cos(A) * math.cos(F), math.cos(A) * math.sin(F)))
    return wpos(pose, L_ARM[0]) + (torso_frame(pose) @ u) * (ARM_L * k)


# ------------------------------------------------------------ 오른팔 내리기
# ★오너 지시 2차(2026-08-12): "점프할 때 한 손으로 검을 앞으로 들고 있는데
#   넌 그게 말이 된다 생각하냐?"
#   1차(위 [한 손 파지])는 왼손만 풀었고 검 든 오른팔은 소스 그대로였다. 그 소스가
#   양손검 전제라 **검을 어깨 높이로 앞에 겨눈 채** 뛴다(committed glb 실측.
#   가슴 좌표계 · 오른어깨 원점 · 게임 m):
#       f7  손 (안쪽 +0.209, 위 +0.014, 앞 +0.493)   칼끝 (위 +0.807, 앞 +1.872)
#       f13 손 (안쪽 +0.210, 위 -0.105, 앞 +0.499)   칼끝 (위 +0.347, 앞 +2.025)
#   1.6m 짜리 대검을 두 팔 다 놓은 채 앞으로 겨누고 뛰는 그림이다. 실제로는 무거운
#   검을 든 팔은 **몸 옆~살짝 뒤·아래로 내려** 균형을 잡는다.
#
# 어떻게 바꾸나 — 어깨에서 **팔 전체를 한 번 돌린다**(IK 아님)
#   손목 위치를 IK 로 잡으면 팔꿈치 각이 바뀌어 손목-검 관계가 틀어진다. 검은 손뼈에
#   물린 강체라 **팔꿈치 굽힘·손목 각을 그대로 둔 채 어깨에서 통째로 돌리는** 것이
#   맞다(s27 의 ARM_LIFT 와 같은 원리, 방향만 반대). 그러면 파지가 한 톨도 안 변한다.
#   목표는 각도를 굳히지 않고 **가슴 좌표계 방향**으로 준다. 몸이 뜨고 기울면 팔이
#   통째로 따라가 원본 점프의 생동감이 남는다(왼팔 균형 자세와 같은 방식).
#
# ★겨누는 것은 팔이 아니라 **칼끝**이다 (1차 시도가 여기서 틀렸다)
#   팔 방향만 목표로 주고 한 번 돌려 봤더니(팔 고도 -65도) 칼끝이 이렇게 나왔다:
#       f7 칼끝 고도 -53도 · 발밑 -0.43m   f16 -56도 · 발밑 -0.52m
#   즉 칼이 바닥을 뚫는다. 이 리그는 손목-칼끝이 1.6m 로 키(1.75m)에 육박해서
#   **팔을 내리면 칼끝이 반드시 지면 밑으로 간다.** 눈에 보이는 것도, 바닥·몸에
#   닿는 것도 칼끝이므로 칼끝 방향을 1순위로 맞추고 팔은 그 다음에 맞춘다.
#   회전 하나(3자유도)로 두 방향(4자유도)을 다 만족시킬 수는 없다 — 팔-칼 사잇각이
#   소스에 고정(실측 31도)돼 있기 때문이다. 그래서 두 단계로 나눈다:
#     1) 칼끝을 목표 방향으로 보내는 최소회전
#     2) **칼 축 둘레**로 더 돌려(칼끝은 그대로) 팔을 목표 쪽에 최대한 붙인다
#   그래도 남는 각은 손목이 먹는다: 팔을 그만큼 더 내리고 손목을 같은 각만큼
#   되돌리면 칼 방향은 유지된 채 팔만 더 내려간다(SWD_WRIST 가 상한. 22도면
#   ★f7·f13 에서 칼끝 목표와 팔 목표를 **둘 다** 소수점 셋째 자리까지 맞춘다).
#   최종 실측(basic2.glb, 가슴 좌표계 · 게임 m):
#       f7  손 (밖 -0.201, 아래 -0.486, 뒤 -0.103)  칼끝 (아래 -1.086, 뒤 -1.438)
#           칼끝 고도 -22.0도 · 팔 고도 -65.1도 · 발밑 여유 +0.510
#       f13 손 (밖 -0.189, 아래 -0.493, 뒤 -0.160)  칼끝 (아래 -1.195, 뒤 -1.495)
#           칼끝 고도 -26.0도 · 팔 고도 -63.3도 · 발밑 여유 +0.259
#       클립 전체 몸 관통 최대 0.0166 = **고치기 전과 같은 값**(f1 파지분)
#
# ★위상표의 근거는 왼팔과 같다: 게임은 상승 내내 f7, 하강 내내 f13 에서 멈춘다.
#   화면에 제일 오래 보이는 두 장이라 거기를 먼저 정하고 나머지를 이었다.
# ★착지(f16~) 는 소스가 이미 팔을 내린다(팔 고도 +2 -> -38도). 그래서 가중치를
#   0 으로 되돌려 **소스의 착지 팔스윙을 살린다**. 힘으로 붙들면 착지가 뻣뻣해진다.
SWD_KEYS = [       # (위상 t, 칼끝 고도 E도(음수=아래), 칼끝 벌림 Wd도(뒤에서 오른쪽),
                   #          팔 벌림 A도, 팔 앞으로 F도(음수=뒤))
    (0.00, -10, 40, 16, 24),    # f1  웅크림. 가중치 0이라 소스 그대로다
    (0.20, -16, 30, 20, -4),    # f5  도약. 검이 내려가며 뒤로 끌린다
    (0.27, -22, 26, 22, -12),   # f7  ★상승 내내 이 자세로 멈춘다
    (0.55, -26, 22, 20, -18),   # f13 ★하강 내내 이 자세로 멈춘다(더 뒤·아래로)
    (0.70, -20, 26, 20, -8),    # f16 착지. 칼끝을 들며 팔이 앞으로 돌아오기 시작
    (1.00, -12, 34, 18, 0),     # f23 회복(가중치 0. 소스 착지 스윙으로 돌아간다)
]
# 가중치(위상, w). 도약 0.2초 안에 다 내리고, 착지 뒤에 소스로 돌려준다.
SWD_W = [(0.00, 0.0), (0.03, 0.0), (0.20, 1.0), (0.70, 1.0), (0.88, 0.55), (1.00, 0.0)]
# 손목이 먹어 줄 상한(도). 0 이면 팔이 칼 사잇각만큼 덜 내려간다.
SWD_WRIST = float(os.environ.get("SWD_WRIST", "22"))


def _key_at(keys, t):
    """구간 안은 smoothstep 으로 잇는다(속도가 튀면 팔이 홱 꺾인다)."""
    if t <= keys[0][0]:
        return keys[0][1:]
    for i in range(len(keys) - 1):
        t0, t1 = keys[i][0], keys[i + 1][0]
        if t <= t1:
            s = (t - t0) / max(1e-6, t1 - t0)
            s = s * s * (3 - 2 * s)
            return tuple(a + (b - a) * s for a, b in zip(keys[i][1:], keys[i + 1][1:]))
    return keys[-1][1:]


def swd_dirs(pose, t):
    """이번 프레임의 (칼끝 목표방향, 팔 목표방향) 월드 단위벡터.
    ★가슴 좌표계는 X=왼쪽이라, 오른쪽으로 벌어지는 쪽이 -X 다."""
    E, Wd, A, F = _key_at(SWD_KEYS, t)
    E, Wd, A, F = (math.radians(x) for x in (E, Wd, A, F))
    b = Vector((-math.sin(Wd) * math.cos(E), math.sin(E),
                -math.cos(Wd) * math.cos(E)))       # 뒤·아래 대각
    u = Vector((-math.sin(A), -math.cos(A) * math.cos(F), math.cos(A) * math.sin(F)))
    C = torso_frame(pose)
    return (C @ b).normalized(), (C @ u).normalized()


def apply_sword_down(pose, Rw, t):
    """오른팔 3본을 어깨에서 통째로 돌려 검을 내린다. (팔 회전량도, 손목 되돌림도, w).

    팔 길이·팔꿈치 굽힘은 하나도 안 건드린다(회전 하나를 세 뼈에 똑같이 곱한다).
    손목만 마지막에 반대로 되돌려 칼 방향을 지킨다.
    """
    w = _key_at(SWD_W, t)[0]
    if w <= 1e-4 or TIP_DIR is None:
        return 0.0, 0.0, 0.0
    S = wpos(pose, R_ARM[0])
    W = wpos(pose, HAND_R)
    Hr = (A2W @ pose[HAND_R]).to_3x3()
    Hr.normalize()
    d = (Hr @ TIP_DIR).normalized()                 # 지금 칼끝 방향
    a = (W - S).normalized()                        # 지금 팔 방향
    bt, at = swd_dirs(pose, t)
    q = d.rotation_difference(bt)                   # 1) 칼끝을 목표로
    # 2) 칼 축 둘레 회전은 칼끝을 안 건드린다. 그걸로 팔을 목표 쪽에 붙인다
    p = q @ a
    p = p - bt * p.dot(bt)
    r = at - bt * at.dot(bt)
    if p.length > 1e-5 and r.length > 1e-5:
        p.normalize()
        r.normalize()
        q = Quaternion(bt, math.atan2(p.cross(r).dot(bt), p.dot(r))) @ q
    # 3) 남은 각은 손목이 먹는다: 팔을 더 내리고 손목을 같은 각만큼 되돌린다
    a2 = q @ a
    rest = a2.angle(at)
    wr = min(rest, math.radians(SWD_WRIST))
    if wr > 1e-4:
        ax = a2.cross(at)
        if ax.length > 1e-6:
            q = Quaternion(ax.normalized(), wr) @ q
    else:
        wr = 0.0
    q = Quaternion().slerp(q, w)                    # 축은 그대로, 각만 가중치만큼
    M = q.to_matrix()
    for bn in R_ARM:
        Rw[bn] = M @ Rw[bn]
    if wr > 1e-4:
        qb = Quaternion().slerp(Quaternion(ax.normalized(), -wr), w)
        Rw[HAND_R] = qb.to_matrix() @ Rw[HAND_R]    # 손목만 되돌린다(칼 방향 유지)
    return math.degrees(q.angle), math.degrees(wr * w), w


def apply_grip(pose, Rw, gt, ph=None):
    """왼팔 2본 IK 로 손목을 타깃 자루에 건다. (목표, IK전 이탈, None, 가중치).

    ph 가 오면(RELEASE 클립) 그 위상만큼 목표를 **균형 팔** 쪽으로 옮긴다.
    목표를 섞는 것이라 팔꿈치 스위블·어깨 회전은 그대로 이어진다(툭 끊기지 않는다).
    """
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
    S = wpos(pose, L_ARM[0])
    E = wpos(pose, L_ARM[1])
    pole = None
    if ph is not None:
        wb = bal_weight(ph)
        if wb > 1e-4:
            T = T.lerp(balance_target(pose, ph), wb)
            w = max(w, wb)                          # 균형 팔은 파지 게이트와 무관
            # 팔꿈치가 향할 방향도 같은 비율로 넘긴다(아래·약간 뒤). 툭 끊기지 않게
            # 원래 팔꿈치 방향에서 섞는다.
            pole = (E - S).normalized().lerp(
                (torso_frame(pose) @ Vector(BAL_POLE)).normalized(), wb)
    before = (Lw - T).length
    # ★손목 방향 교정([왼손 손목])에 넘길 값: 자루 기준점 C 와 **파지 전용** 가중치.
    #   균형 팔(RELEASE)로 넘어간 몫(wb)은 빼야 한다. 안 그러면 손을 놓은 팔이
    #   허공의 자루를 쥐는 방향으로 손목을 튼다.
    #   ★제곱으로 빼는 이유: 1차로 빼면 전환 중간(wb 0.8)에도 0.2 가 남아 손목이
    #     이미 멀어진 자루를 향해 조금 틀린다. 점프 f04 왼손목이 132 -> 143도로
    #     오히려 나빠졌다(실측). 제곱이면 같은 자리에서 0.03 이라 사실상 0 이다.
    _wb = bal_weight(ph) if ph is not None else 0.0
    wh = gt[3] * (1.0 - _wb) ** 2
    if w <= 1e-4:
        return T, before, before, 0.0, C, wh
    R1, R2, Tc = two_bone_ik(S, E, Lw, T, pole)
    R1 = Quaternion().slerp(R1, w)
    R2 = Quaternion().slerp(R2, w)
    M1 = R1.to_matrix()
    M2 = (R2 @ R1).to_matrix()
    Rw[L_ARM[0]] = M1 @ Rw[L_ARM[0]]
    Rw[L_ARM[1]] = M2 @ Rw[L_ARM[1]]
    Rw[L_ARM[2]] = M2 @ Rw[L_ARM[2]]
    return T, before, None, w, C, wh


# ---------------------------------------------------------------- 왼손 손목
# ★오너 지시(2026-08-12): "왼쪽(손)은 엄청 꺾여 있음. 그리고 (X 쓸 때) 왼쪽 손도
#   이상하게 꺾여버리고."
#
# 무엇이 어긋나 있었나 (실측. blender/probe_wrist.py, 커밋된 basic2.glb)
#   왼손목 기하각(= 팔꿈치->손목 과 손목->주먹중심 사이각. 레스트 중립이 16.8도):
#       Idle 73.8 · Attack 최대 169.1 · Heavy(X) 최대 161.0 · Wide 최대 169.3 · Jump 132.5
#   사람 손목은 굴곡·신전 60~70도가 한계다. 169도는 손이 팔뚝 위로 접힌 그림이다.
#   원인은 두 겹이다.
#     1) 소스(slayer) 자체가 그렇다(같은 잣대로 Attack 157 · Heavy 141 · Wide 151).
#        토이솔저 손은 벙어리장갑이라 안 보였을 뿐이다.
#     2) 리타게팅은 **회전 델타**를 옮기는 것이라 두 리그의 레스트 손 방향 차이가
#        그대로 손목 각도 오차로 얹힌다(여기서 10~15도 더 나빠진다).
#   게다가 왼 주먹 구멍축이 자루축과 67~77도라 **쥔 모양도 아니었다**.
#
# 어떻게 고치나 — 손목 방향을 **자루에서 역산**한다(팔은 안 건드린다)
#   IK 가 잡아 놓은 손목 **위치**와 팔꿈치는 그대로 두고, 손뼈 회전만 다시 쓴다.
#     · 구멍축 -> 자루축(엄지가 칼끝 쪽. 양손검은 두 엄지가 다 코등이를 본다)
#     · 팔축   -> 손목에서 자루 기준점 C 로 (주먹 중심이 자루 위에 얹힌다)
#   두 목표는 서로 수직이라 회전 하나로 **정확히** 만족한다. 남는 손목 굽힘은
#   '팔뚝이 자루와 얼마나 수직인가'로 결정되는데(실측 중앙 12~46도), 그게 상한을
#   넘는 프레임에서는 넘는 만큼 되돌린다(WRIST_LIM). 되돌린 만큼 구멍축이 자루에서
#   기울지만, 부러진 손목보다 낫다.
#   ★팔 자세·칼·오른손은 한 톨도 안 건드린다. 손뼈 회전 하나만 바뀐다.
WRIST_LIM = float(os.environ.get("WRIST_LIM", "60"))
HAND_GRIP = os.environ.get("HAND_GRIP", "1") == "1"      # 0 이면 옛 판 재현
# ★어느 칼에 맞출 것인가. 파지 **위치**(IK 목표 C)는 예전대로 DST_SWORD(baekah) 기준이지만
#   손 **방향**은 화면에 실제로 들려 있는 칼에 맞춰야 한다. 게임 시작 칼은 1번(nokseun)이고
#   7자루의 칼축은 서로 최대 17도 다르다(실측). TIP_DIR 이 이미 그 칼의 축이다
#   ([자루] 절에서 **타깃 아마추어의 자식**으로 한정해 찾았다. 소스에도 같은 이름의
#    칼이 있으므로 bpy.data.objects 를 이름으로 뒤지면 검사 칼을 집는다).
VIS_U = TIP_DIR if TIP_DIR is not None else (
    Vector(D_SW[0].col[0]) if D_SW else None)
if VIS_U is not None and D_SW:
    print("\n[왼손 손목] 방향 기준 칼 %s (파지 기준 %s 와 %.1f도) / 굽힘 상한 %.0f도%s"
          % (GAME_SW, dname,
             math.degrees(VIS_U.angle(Vector(D_SW[0].col[0]))), WRIST_LIM,
             "" if HAND_GRIP else "  ★HAND_GRIP=0 이라 안 건드린다"))


def apply_hand_grip(pose, Rw, C, w):
    """왼손뼈 회전을 자루 파지 방향으로 다시 쓴다. (전 기하각, 후 기하각, 구멍축각, w)."""
    if FF_L is None or not DO_GRIP or not HAND_GRIP or VIS_U is None:
        return None
    FC, ax_l, tu_l, _ = FF_L
    HM = A2W @ pose[HAND_R]
    Hr = HM.to_3x3()
    Hr.normalize()
    uh = (Hr @ VIS_U).normalized()                        # 월드 자루축(칼끝 쪽)
    W = wpos(pose, HAND_L)
    E = wpos(pose, L_ARM[1])
    Lr = (A2W @ pose[HAND_L]).to_3x3()
    Lr.normalize()
    f = (W - E).normalized()
    g0 = math.degrees(f.angle((Lr @ ax_l).normalized()))
    if w <= 1e-4:
        return g0, g0, math.degrees((Lr @ tu_l).normalized().angle(uh)), 0.0
    n0 = C - W
    n0 = n0 - uh * n0.dot(uh)                             # 자루축에 수직인 성분만
    if n0.length < 1e-6:
        n0 = f - uh * f.dot(uh)
    if n0.length < 1e-6:
        return g0, g0, math.degrees((Lr @ tu_l).normalized().angle(uh)), 0.0
    n0.normalize()
    # ★굽힘 상한은 **자루축 둘레에서만** 양보한다. 손을 자루축 둘레로 굴리면
    #   구멍축은 자루에 붙은 채로 팔축만 도니까 **파지를 안 깨고** 손목을 편다.
    #   (처음엔 임의 축으로 되돌렸다가 구멍축이 자루에서 94도까지 벌어졌다.
    #    "쥔 것처럼" 이 이번 지시의 본론이라 그 방식은 못 쓴다)
    #   f·n(th) = A cos th + B sin th = R cos(th - phi). 상한 cos(LIM) 을 만족하는
    #   두 해 중 n0 에 가까운 쪽을 고른다. R < cos(LIM) 이면 상한까지 못 가므로
    #   **제일 덜 꺾이는 자리**(th = phi)로 간다. 그게 팔을 안 건드리고 되는 최선이다.
    A = f.dot(n0)
    B = f.dot(uh.cross(n0))
    R = math.hypot(A, B)                                  # = cos(도달 가능한 최소 굽힘)
    cl = math.cos(math.radians(WRIST_LIM))
    n = n0
    if A < cl and R > 1e-6:
        phi = math.atan2(B, A)
        d = math.acos(max(-1.0, min(1.0, cl / R))) if R > cl else 0.0
        th = phi - math.copysign(d, phi)
        n = (Matrix.Rotation(th, 3, uh) @ n0).normalized()
    # 손 로컬 (팔축, 엄지축, 그 외적) -> 월드 (n, uh, 그 외적). 둘 다 정규직교라
    # 행렬 하나가 곧 회전이다(det=+1 이 보장된다).
    Ml = Matrix((ax_l, tu_l, ax_l.cross(tu_l))).transposed()
    Mt = Matrix((n, uh, n.cross(uh))).transposed()
    Ht = Mt @ Ml.inverted()
    q = Rw[HAND_L].to_quaternion().slerp(Ht.to_quaternion(), w)
    Rw[HAND_L] = q.to_matrix()
    g1 = math.degrees(f.angle((Rw[HAND_L] @ ax_l).normalized()))
    tg = math.degrees((Rw[HAND_L] @ tu_l).normalized().angle(uh))
    return g0, g1, tg, w


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
    rel = name in RELEASE and DO_GRIP
    swd = name in SWDOWN
    print("\n[%s] 소스 f%d~%d (%d장)%s%s"
          % (name, f0, f1, nf, "  ★한 손 파지(왼팔=균형)" if rel else "",
             "  ★오른팔 내리기(검)" if swd else ""))

    def ph_all(i):
        """이 프레임의 위상(0~1)."""
        return i / max(1, nf - 1)

    def phase(i):
        """RELEASE 클립이면 이 프레임의 위상(0~1), 아니면 None(=양손 파지)."""
        return ph_all(i) if rel else None

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
        print("   파지 게이트: %d/%d 프레임 (소스 왼손-자루축 수직거리 %.3f~%.3f H)%s"
              % (on, nf, min(g[2] for g in gts), max(g[2] for g in gts),
                 "  <- RELEASE 라 이 게이트 위에 균형 팔을 덮어쓴다" if rel else ""))
    if rel:
        print("   균형 팔 위상표(t / 벌림 / 앞으로 / 뻗음 / 파지->균형 가중치):")
        for t, A, F, k in BAL_KEYS:
            print("      t %.2f (f%-2d)  A %+3d도  F %+3d도  k %.2f   w %.2f"
                  % (t, f0 + int(round(t * (nf - 1))), A, F, k, bal_weight(t)))
    if swd:
        print("   오른팔(검) 위상표(t / 칼끝 고도·벌림 / 팔 벌림·앞으로(음수=뒤) / 가중치):")
        for t, E, Wd, A, F in SWD_KEYS:
            print("      t %.2f (f%-2d)  칼끝 E %+3d도 Wd %+3d도   팔 A %+3d도 F %+3d도"
                  "   w %.2f"
                  % (t, f0 + int(round(t * (nf - 1))), E, Wd, A, F, _key_at(SWD_W, t)[0]))

    lows, maxerr, befs, afts, swds, wrs = [], 0.0, [], [], [], []
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        pw = DREST[ROOT_BONE][1] + (praw[i] - pmean) * K_TRANS
        Rw = delta_rots()
        pose, basis = build(Rw, pw)
        if swd:
            # ★왼손 파지보다 **먼저**. 검이 먼저 움직여야 왼손이 그 검을 따라간다
            #   (apply_grip 은 지금 프레임의 오른손 위치에서 자루 기준점을 잡는다).
            swds.append(apply_sword_down(pose, Rw, ph_all(i)))
            pose, basis = build(Rw, pw)
        if DO_GRIP:
            T, bef, _, w, Ch, wh = apply_grip(pose, Rw, gts[i], phase(i))
            pose, basis = build(Rw, pw)
            befs.append((bef / DH, gts[i][3]))
            afts.append(((wpos(pose, HAND_L) - T).length / DH, gts[i][3]))
            # ★손목 방향 교정은 IK **뒤**에 온다(IK 가 옮겨 놓은 손목 위치를 쓴다)
            r = apply_hand_grip(pose, Rw, Ch, wh)
            if r:
                wrs.append(r)
                pose, basis = build(Rw, pw)
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
    if wrs:
        on = [r for r in wrs if r[3] > 0.5]
        if on:
            b0 = sorted(r[0] for r in on)
            b1 = sorted(r[1] for r in on)
            tg = sorted(r[2] for r in on)
            print("   왼손목(파지 %d/%d 프레임): 기하각 전 %.0f~%.0f(중앙 %.0f)"
                  " -> 후 %.0f~%.0f(중앙 %.0f) / 구멍축-자루축 후 %.0f~%.0f (상한 %.0f도)"
                  % (len(on), nf, b0[0], b0[-1], b0[len(b0) // 2],
                     b1[0], b1[-1], b1[len(b1) // 2], tg[0], tg[-1], WRIST_LIM))
    if swd and swds:
        act_f = [(i, d, wr) for i, (d, wr, w) in enumerate(swds) if w > 1e-4]
        print("   오른팔 회전량: %d/%d 프레임 적용 (팔 최대 %.1f도 f%d / 평균 %.1f도,"
              " 손목 되돌림 최대 %.1f도)"
              % (len(act_f), nf, max(d for _, d, _ in act_f),
                 f0 + max(act_f, key=lambda r: r[1])[0],
                 sum(d for _, d, _ in act_f) / len(act_f),
                 max(wr for _, _, wr in act_f)))

    # --- 2차: 보정을 넣고 키를 찍는다 ---
    act = new_action(name)
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        pw = (DREST[ROOT_BONE][1] + (praw[i] - pmean) * K_TRANS
              + Vector((0, 0, shift)))
        Rw = delta_rots()
        pose, basis = build(Rw, pw)
        if swd:                                     # ★1차와 같은 순서로(검 먼저)
            apply_sword_down(pose, Rw, ph_all(i))
            pose, basis = build(Rw, pw)
        if DO_GRIP:
            _, _, _, _, Ch, wh = apply_grip(pose, Rw, gts[i], phase(i))
            pose, basis = build(Rw, pw)
            if apply_hand_grip(pose, Rw, Ch, wh):       # ★1차와 같은 순서로
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


# ================================================ 7b) 프리셋 굽기 (13-모션이식)
# bake() 와 다른 점은 셋뿐이다.
#   1) 소스가 프리셋 아마추어다(switch_src 로 갈아끼운다)
#   2) 소스 프레임을 **소수로** 샘플한다 = 트림·배속이 여기서 일어난다
#   3) 구간을 여러 개 이어붙일 수 있다(3연타). 이음매는 월드 회전 쿼터니언 슬러프로
#      ANIM_BLEND 장에 걸쳐 섞는다. 안 섞으면 자세가 뚝 끊겨 "칼질이 끊긴다"로 읽힌다.
# ★골반은 **구간마다 자기 평균을 뺀다**. 프리셋마다 서 있는 자리가 다른데 그대로
#   이으면 이음매에서 몸이 순간이동한다. 평균을 빼면 구간 안의 몸짓(런지·기울임)은
#   살고 구간 사이의 자리 차이만 사라진다(= 루트 모션 제거. 게임 이동과 이중이 안 된다).
def _q(m):
    q = m.to_quaternion()
    q.normalize()
    return q


def alt_timeline(segs):
    """구간 목록 -> [ (구간번호, 파일, 소스프레임(소수), 가중치) ... ] 프레임별 목록."""
    plan = []
    for stem, fa, fb, spd, bl in segs:
        n = max(2, int(round(abs(fb - fa) / spd)) + 1)
        step = (fb - fa) / (n - 1)
        plan.append((stem, [fa + i * step for i in range(n)]))
    ns = len(plan)
    BL = [0] + [min(segs[j][4], len(plan[j - 1][1]) - 1, len(plan[j][1]) - 1)
                for j in range(1, ns)]
    starts, s = [], 0
    for j, (stem, fr) in enumerate(plan):
        starts.append(s)
        s += len(fr) - (BL[j + 1] if j < ns - 1 else 0)
    tl = [[] for _ in range(s)]
    for j, (stem, fr) in enumerate(plan):
        bin_ = BL[j]                                # 이 구간으로 들어오는 이음매
        bout = BL[j + 1] if j < ns - 1 else 0        # 이 구간에서 나가는 이음매
        for i, f in enumerate(fr):
            k = starts[j] + i
            if not (0 <= k < s):
                continue
            w = 1.0
            if j > 0 and bin_ > 0 and i < bin_:
                w = (i + 1) / float(bin_ + 1)
            if bout > 0 and i >= len(fr) - bout:
                w = min(w, (len(fr) - i) / float(bout + 1))
            tl[k].append((j, stem, f, w))
    for k in range(s):
        tot = sum(x[3] for x in tl[k]) or 1.0
        tl[k] = [(j, st, f, w / tot) for j, st, f, w in tl[k]]
    return plan, tl


def bake_alt(name, segs):
    plan, tl = alt_timeline(segs)
    nf = len(tl)
    print("\n[%s] ★Meshy 프리셋 %d구간 -> %d장 (%.3f초 @30fps)"
          % (name, len(segs), nf, (nf - 1) / 30.0))
    for j, ((stem, fa, fb, spd, bl), (_, fr)) in enumerate(zip(segs, plan)):
        print("   %-14s 소스 f%.1f~%.1f (%.3f초) x배속 %.2f -> %d장 (%.3f초)"
              "  앞이음매 %d장"
              % (stem, fa, fb, (fb - fa) / 30.0, spd, len(fr),
                 (len(fr) - 1) / 30.0, 0 if j == 0 else bl))

    def sample(stem, f):
        """프리셋 한 장을 소수 프레임으로 읽어 (타깃 월드회전 dict, 소스 골반)."""
        switch_src(ALT_CTX[stem])
        fi = int(math.floor(f))
        sc.frame_set(fi, subframe=float(f - fi))
        bpy.context.view_layer.update()
        return delta_rots(), (S2W @ src.pose.bones[PELVIS].matrix).translation.copy()

    # 구간별 골반 평균(자리 차이 제거용)
    pmean = []
    for (stem, fr) in plan:
        acc = Vector((0, 0, 0))
        for f in fr:
            acc += sample(stem, f)[1]
        pmean.append(acc / len(fr))

    def frame_pose(k):
        Rw, off, wsum = None, Vector((0, 0, 0)), 0.0
        for j, stem, f, w in tl[k]:
            R2, pel = sample(stem, f)
            off += (pel - pmean[j]) * w
            if Rw is None:
                Rw = {bn: _q(R2[bn]) for bn in ORDER}
                wsum = w
            else:
                t = w / max(1e-9, wsum + w)
                for bn in ORDER:
                    Rw[bn] = Rw[bn].slerp(_q(R2[bn]), t)
                wsum += w
        return {bn: Rw[bn].to_matrix() for bn in ORDER}, off

    # --- 1차: 접지 보정량·칼끝 진단 ---
    lows, maxerr, tips = [], 0.0, []
    for k in range(nf):
        Rw, off = frame_pose(k)
        pw = DREST[ROOT_BONE][1] + off * K_TRANS
        pose, basis = build(Rw, pw)
        for bn in ORDER:
            arm.pose.bones[bn].matrix_basis = basis[bn]
        bpy.context.view_layer.update()
        if k % 10 == 0:                             # 해석식 자기검증(★함정 8)
            for bn in ORDER:
                a_ = (A2W @ arm.pose.bones[bn].matrix).translation
                b_ = (A2W @ pose[bn]).translation
                maxerr = max(maxerr, (a_ - b_).length)
        lows.append(low_of(DST_BODY))
        if TIP_DIR is not None and D_SW:
            HM = A2W @ pose[HAND_R]
            tips.append(HM @ (TIP_DIR * D_SW[2] * ANIM_TIP_K / HM.to_3x3().to_scale()[0]))
    shift = BIND_LOW - pct(lows, 0.10)
    print("   해석식 자기검증: Blender 평가와 뼈 위치 최대 오차 %.7f (키의 %.5f%%)"
          % (maxerr, maxerr / DH * 100))
    if maxerr > DH * 1e-4:
        raise SystemExit("해석식 FK 가 Blender 평가와 다르다. 리타게팅 신뢰 불가")
    print("   접지 보정: 메시 최저 %.4f~%.4f (10분위 %.4f) -> 바인드 %.4f (%+.4f)"
          % (min(lows), max(lows), pct(lows, 0.10), BIND_LOW, shift))
    if tips:
        gk = 1.75 / DH                              # 게임이 키를 1.75 로 정규화한다
        vs = [0.0] + [(tips[i] - tips[i - 1]).length * 30.0 * gk
                      for i in range(1, len(tips))]
        cl = [(t.z + shift - BIND_LOW) * gk for t in tips]
        vmax = max(vs)
        vi = vs.index(vmax)
        hot = [i for i, v in enumerate(vs) if v > 15.8]   # enemy.js HOT_ON 환산
        print("   칼끝(게임 환산 1.75m 키, 배속 1.0 기준): 최고속 %.1f m/s"
              " @f%d(%.3f초) / 바닥여유 %+.3f~%+.3f m"
              % (vmax, vi, vi / 30.0, min(cl), max(cl)))
        print("   타격 구간(칼끝 15.8 m/s 초과 = enemy.js HOT_ON 환산): %s"
              % (", ".join("f%d~%.3fs" % (i, i / 30.0) for i in hot)
                 or "★없음! 이 클립은 안 벤다"))
        print("   프레임별 칼끝 속도/바닥여유:")
        for i in range(nf):
            print("     f%-3d %5.3fs  v%6.1f  z%+6.3f  %s"
                  % (i, i / 30.0, vs[i], cl[i],
                     "#" * int(vs[i] / max(1e-9, vmax) * 34)))

    # --- 2차: 키 찍기 ---
    act = new_action(name)
    for k in range(nf):
        Rw, off = frame_pose(k)
        pw = DREST[ROOT_BONE][1] + off * K_TRANS + Vector((0, 0, shift))
        pose, basis = build(Rw, pw)
        for bn in ORDER:
            arm.pose.bones[bn].matrix_basis = basis[bn]
        bpy.context.view_layer.update()
        for b in arm.pose.bones:
            b.keyframe_insert("location", frame=k + 1)
            b.keyframe_insert("rotation_quaternion", frame=k + 1)
            b.keyframe_insert("scale", frame=k + 1)
    switch_src(None)
    print("   -> 액션 %s  f1~%d (%.3f초 @30fps)" % (name, nf, (nf - 1) / 30.0))
    return act


BAKED = {}
for c in CLIPS:
    BAKED[c] = bake_alt(c, ANIM[c]) if c in ANIM else bake(c)

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
        print("  %-8s %7d %8.3f %8.3f %8.3f %9.2f   축상 %.3f~%.3f (자루끝 %.3f)%s"
              % (nm, len(ds), sd[0], sd[len(sd) // 2], sd[-1], sd[-1] / FIST,
                 min(ts), max(ts), POM_L * HSCALE / H,
                 "  ★한 손(왼손이 떨어져 있어야 정상)" if nm in RELEASE else ""))

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

    # 한 손 파지·오른팔 내리기 클립은 **연속으로** 찍어야 판정이 된다(한 장으로는
    # 팔이 어디로 가는지 안 보인다). 게임이 멈춰 보여 주는 프레임을 반드시 포함한다.
    for nm in sorted(set(RELEASE) | set(SWDOWN)):
        act = bpy.data.actions.get(nm)
        if not act:
            continue
        use(act)
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        fs = sorted(set([f0, f1] + [f0 + int(round(t * (f1 - f0)))
                                    for t in (0.09, 0.18, 0.27, 0.40, 0.55,
                                              0.70, 0.85)]))
        for f in fs:
            sc.frame_set(f)
            bpy.context.view_layer.update()
            for view in ("front", "side"):
                shoot(os.path.join(OUTDIR, "rel_%s_%s_f%02d.png" % (nm, view, f)),
                      view)

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
