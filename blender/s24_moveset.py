# -*- coding: utf-8 -*-
"""검사(slayer) 리그의 전투 모션 7종을 **Meshy 리그 캐릭터**에 통째로 이식한다.

    blender -b -P blender/s24_moveset.py
    -> web/hero2.glb  (hero 몸 + slayer 액션 Idle/Walk/Run/Attack/Heavy/Wide/Jump)

★★2026-08-13 이후 이 파일은 **모션을 만드는 곳**이기도 하다 (15-모션수제)
  베기 3종(Attack/Heavy/Wide)은 더 이상 남의 모션을 옮겨오지 않는다.
  손잡이 `HAND=Attack,Heavy,Wide` 를 주면 아래 [7c 수제 키프레임] 절의
  HAND_SPEC 표(= 손으로 짠 키프레임)로 굽는다. 오너가 프리셋 트림을 두 번
  기각했기 때문이다("칼 베는거 안고쳐짐 그냥 너가 직접 베는 모션 만들어").
  세 갈래 중 어느 길로 굽는지는 파일 맨 아래 한 곳에서 갈린다:
      HAND 에 있으면  -> bake_hand()   수제 키프레임          (지금 공정)
      ANIM 에 있으면  -> bake_alt()    Meshy 프리셋 트림      (13·14차. 폐기)
      둘 다 아니면    -> bake()        slayer 리타게팅        (Idle/Walk/Run/Jump)
  ★Jump 는 여전히 리타게팅이다. 다만 팔만 위상표로 덮어쓴다([오른팔 내리기]·
    [한 손 파지] 절). 다리·몸통의 도약·착지가 좋아서 남겨 둔 것이다.

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

★★검 놓은 왼손 주먹 방향 (HAND_FREE. 기본 켬) — 2026-08-13 오너 지시
  "점프했을때 검안쥔손 주먹이 왜 하늘을향하고있냐"
  위 [왼손 손목] 교정은 **자루를 쥔 손**만 잡는다(가중치가 파지 게이트다).
  손을 놓는 순간 그 가중치가 0 이 되는데, **놓은 뒤의 손 방향을 정하는 코드가
  없었다.** 그래서 체공 내내 소스(양손검)의 손 회전이 남아 주먹 앞면이 고도
  +82~+90도, 곧 **거의 정확히 하늘**을 보고 있었다. 손 방향을 팔뚝에서 다시
  정한다. 자세한 표와 근거는 아래 [놓은 손 주먹 방향] 절에 있다.

★★검 든 오른팔 내리기 (SWORD_DOWN. 기본 Jump) — 2026-08-12 오너 지시 2차
  "점프할 때 한 손으로 검을 앞으로 들고 있는데 넌 그게 말이 된다 생각하냐?"
  1차는 왼손만 풀었고 오른팔은 소스 그대로 **검을 앞으로 겨눈** 자세였다.
  SWORD_DOWN 에 적은 클립은 오른팔 3본을 어깨에서 통째로 돌려 검을 몸 옆·아래로
  내린다. 자세한 표와 근거는 아래 [오른팔 내리기] 절에 있다.
  ★★2026-08-13 17차: 그 "몸 옆"이 **화면에서는 발밑 수직 장대**였다(16차 건틀릿
    SHEET_J3). 칼끝을 들고(E +14/+18) 방위를 45도 격자에서 비껴 놓고(Wd 122/128)
    팔꿈치를 굽혀(EB +40) 여덟 방향 전부에서 실루엣이 서게 고쳤다. 굽는 자리에서
    여덟 방향 화면을 재는 자가 같이 들어왔다 — [17차 신설: 8방향 화면 실루엣] 절.

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
  HAND      수제 키프레임으로 구울 클립(쉼표). 지금 공정은 Attack,Heavy,Wide.
            빈 값이면 옛 길(ANIM 프리셋 / slayer 리타게팅)로 돌아간다
  DBG_REACH 1 이면 프레임마다 왼팔이 자루까지 몇 배 뻗는지 좌표까지 찍는다(디버그)
  GRIP_K    왼손목-자루 오프셋 환산 보정(기본 1.0. 손 크기가 키 대비 많이 다를 때만)
  GRIP_ON/GRIP_OFF  파지 게이트 문턱(키 정규화. 기본 0.10 / 0.18)
  RELEASE   한 손으로 쥘 클립(쉼표)   기본 Jump  (빈 값이면 전부 양손)
  SWORD_DOWN 검 든 오른팔을 내릴 클립  기본 Jump  (빈 값이면 소스 그대로)
  SWD_WRIST  오른손목이 먹어 줄 각의 상한(도)   기본 22
  JUMP_V15   1 이면 점프 칼 위상표를 **15차 판**으로 되돌린다(17차 before 재현용)
  SWD_TABLE  점프 칼 위상표 직접 주입 "t,E,Wd,A,F,EB;..." (튜닝용. 비면 파일 값)
  HAND_GRIP 1(기본) 왼손목 방향을 자루에서 역산 / 0 옛 판(리타게팅 그대로) 재현
  WRIST_LIM 왼손목 기하각 상한(도)     기본 60  (레스트 중립이 16.8도인 잣대다)
  HAND_FREE 1(기본) 검 놓은 손(균형 팔) 주먹 방향을 팔뚝에서 다시 쓴다
            / 0 이면 옛 판(주먹이 하늘) 재현. md5 aa60d350 이 그대로 나온다
  FST_TABLE 놓은 손 위상표 직접 주입 "t,ROLL,BEND;..." (튜닝용. 비면 파일 값)
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
#
# ── 대본을 다시 짤 때 반드시 아는 세 가지 (14-베기수정, 2026-08-12) ──
# 오너 "x는 세로로베는거고 c는 가로로베는건데 너무길게 만들지말고, 휘두르는모션
#       지금해놓은건 무슨 야구에서 체인지업하듯이 자세가 이상해."
# 실측 근거는 blender/probe_meshy_plane.py(소스 훑기) · probe_moves_read.py(결과 판정)
# · probe_moves_strip.py(실루엣 시트). 증거=renders/history/v99_wave14/moves_fix/
#
# 1) **화면에서 읽히는 방향은 tipL / tipU 두 값이 정한다.**
#    게임 카메라는 캐릭터 뒤에 있다 = 몸의 좌우가 화면 가로, 위아래가 화면 세로,
#    앞뒤(F)는 화면 깊이라 거의 안 보인다. 그래서 "세로로 벤다"는 곧
#    타격 구간의 |ΔtipU| / |ΔtipL| 이 크다는 뜻이다(probe_moves_read 가 이걸 찍는다).
#
# 2) ★★**프리셋의 내려베기는 칼끝이 몸 뒤를 지난다**(tipF -0.3~-1.4).
#    main.js makeHitSeg 의 정면 부채꼴 게이트가 뒤에 있는 칼을 통째로 버리므로,
#    내려찍는 구간만 넣으면 **스윙 번호는 발급되는데 피해가 0** 이다
#    (실측: X 14판 전부 hits 0). 칼이 앞으로 넘어오는 구간(sword_slash f18~f21)까지
#    타격 구간에 넣어야 벤다. 단 앞으로 너무 끌면 이번엔 좌우 이동이 커져
#    **가로로 읽힌다** — sword_slash 는 f20.2 에서 끊는 게 둘을 다 만족한다.
#
# 3) ★axe_chop 은 **쓸 데가 없다.** 앞 3.2초가 정지+도끼 들어올리기(그 22장이
#    오너가 말한 투구 폼 그 자체다). 진짜 내려찍기 f133~135 는 우리 칼 계약으로
#    환산하면 칼끝이 좌우로만 0.8 움직이고 위아래로는 0.4뿐이라, 배속을 아무리
#    올려도 **세로로 안 읽힌다**(속도 문제가 아니라 방향 문제다). 그래서 뺐다.
#
# 최종 대본(s31 헤더 2번 줄에 그대로 있다):
#   Attack = left_slash 한 테이크의 스윙 셋. 예비동작(f2~f13, 팔을 어깨 위 뒤로 감는
#            구간)을 통째로 잘라 f14 에서 시작한다. 스윙 사이에는 칼끝을 HOT_OFF
#            아래로 떨어뜨리는 가드 구간을 끼운다(안 그러면 2·3타가 안 박힌다).
#   Heavy  = sword_slash 의 머리 위 올림(f6~f11) + 빠른 내려베기(f11~f17.5) +
#            앞으로 넘어오는 구간(f17.5~f20.2 @0.55 = 판정이 실제로 닿는 자리) + 정지.
#   Wide   = sword_slash 의 낮게 당기기(f14.5~f16) + 앞을 쓸어 도는 구간(f16~f21).
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

# ══════════════════════════════════════════════════════════════════════════
# ★★25차 GRIP_V25 — **손등 계약** (2026-08-24, 오너 "지금은 손등이 하늘로오게
#   이상하게 들고있잖아")
#   계약: 지속 자세(Idle 전 프레임 등)에서 오른손 손등 노멀의 월드 고도가
#   [-25, +35]도 안이고 캐릭터 바깥쪽(오른쪽) 반구를 향할 것. 물리 근거:
#   31kg 급 슬래브의 토크는 중립 손목(악수 자세, 엄지 위)으로만 전완 뼈에 실린다.
#   손등이 하늘 = 완전 회내 = 손목이 토크를 못 받는 자세다.
#   ★칼축 둘레 회전은 칼끝 궤적을 안 바꾸는 공짜 자유도다(칼이 오른손에 강체
#     스킨 + 손뼈 머리가 자루축 위). 손등 교정은 전부 이 자유도로 한다.
#   GRIP_V25=0 이면 이 파일의 25차 갈래(Idle 손등 롤 + 베기 날 정렬)가 전부 꺼져
#   24차 판이 바이트까지 그대로 나온다(2026-08-24 롤백 실측).
GRIP_V25 = os.environ.get("GRIP_V25", "1") == "1"
# 오른 주먹 손등 노멀(손뼈 로컬). ★부호 함정 둘(25차 실측으로 확정):
#   1) 주먹을 돌린 판이라 엄지축은 THUMB_REF 가 아니라 **칼끝 쪽**이다(probe_wrist
#      와 같은 재잡기). 2) 오른손은 로컬 외적 부호가 해부학과 반대다(LOG:3400,
#      왼손 t x arm = 손등 / 오른손은 그 반대). 결과값은 probe_wrist 의 최종
#      bak (-0.965,+0.161,+0.209) 와 일치해야 한다(아래 로그로 매 굽기 확인).
BACK_L = None
FF_R = fist_frame(arm, DST_BODY, HAND_R) if (GRIP_V25 and TIP_DIR is not None) else None
if FF_R:
    _t_r = FF_R[2].copy()
    if _t_r.dot(TIP_DIR) < 0:              # 엄지축을 칼끝 쪽으로(주먹 돌린 판)
        _t_r = -_t_r
    BACK_L = (-(_t_r.cross(FF_R[1]))).normalized()   # ★오른손 외적 반전
    print("   오른 주먹 손등 노멀(손뼈 로컬) (%+.3f,%+.3f,%+.3f)"
          "  ★probe_wrist 최종 bak 과 일치해야 한다" % (BACK_L.x, BACK_L.y, BACK_L.z))

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
# ★2026-08-13 오너 지시 3차로 벌림을 절반 가까이 줄였다. "그냥 양팔이 살짝
#   벌려지는 정도 아님?" — 옛 값 40~54도는 만세에 가까웠다. 새 값은 오른팔(SWD_KEYS
#   의 A 20~28도)과 **좌우 대칭**이 되게 20~30도로 맞췄다. 그게 곧 "양팔이 살짝".
# ★★★2026-08-13 17차 4번째 — **팔꿈치가 몸통에 붙어 있었다** (이번 수정)
#   오너 직접 지시: **"점프할때 칼안든손 팔꿈치가 몸통에왜이렇게 붙어있음.
#                     칼든손처럼 좀 자연스러운자세가 되어야지."**
#   실측(committed ca0e350a, blender/probe_jump_larm.py. 게임이 멈춰 세우는 두 장):
#       f7   왼 **위팔 외전 +7.6도** / 팔꿈치 굽힘 56.7 / 팔꿈치 바깥 +0.040m / 척추 0.308m
#            오른 위팔 외전 +14.9도 / 굽힘 100.0 / 바깥 +0.077m / 척추 0.388m
#       f13  왼 **위팔 외전 +8.6도** / 굽힘 51.7 / 바깥 +0.045m / 척추 0.316m
#            오른 위팔 외전 +25.5도 / 굽힘  93.6 / 바깥 +0.129m / 척추 0.427m
#   왼 위팔 외전이 오너 기준("살짝 벌림 15~30도")의 **절반**이었다. 팔꿈치가 어깨
#   바로 밑 4cm 에 매달려 갈비뼈를 스치고 있었다.
#
# ★왜 A 를 26·30 으로 줘 놓고 7.6·8.6 도가 나왔나 — 17차 함정 4번의 재판
#   A(BAL_KEYS 의 벌림)는 **손목** 기준 각이다. 실측도 손목 기준으로는 +26.0·+30.0 도로
#   목표대로 나왔다. 그런데 **팔꿈치**는 그 선 위에 없다 — IK 는 팔꿈치를 스위블
#   평면(pole)이 정한 자리에 놓고, 그 자리가 어깨->손목 축에서 l1·sin(어깨각) = **15cm**
#   떨어져 있다. 그 15cm 를 어디로 쓰느냐가 곧 "팔꿈치가 몸에 붙나 뜨나"이고,
#   옛 BAL_POLE(-0.10,-1.00,-0.45)은 그걸 **안쪽으로 34.6도** 썼다. 그래서
#   손목은 26도 벌어졌는데 위팔은 7.6도였다.
#
# ★고친 방법 — 팔꿈치 방향을 **어깨->손목 축에 수직인 평면 안에서 각으로** 준다 (EO 신설)
#   폴을 절대 방향(가슴 좌표 상수)으로 주면 안 된다. 팔이 벌어질수록 그 폴이
#   어깨->손목 축과 나란해져 수직 성분이 짧아지고(f13 에서 |perp| 0.39), 팔꿈치가
#   프레임마다 홱 돈다. 대신 그 축에 수직인 평면을 만들어 **바깥·뒤 두 축**을 세우고
#   (바깥축은 팔이 아래로 늘어져 있는 한 늘 안정적이다) 각 EO 하나로 정한다:
#       EO   0도 = 팔꿈치가 **곧게 뒤** · +면 바깥 · -면 안쪽(옛 값이 -34.6도였다)
#   오른팔 EB(팔꿈치 굽힘)와 같은 자리의 채널이다 — 오른팔은 칼을 든 강체라 굽힘으로,
#   왼팔은 IK 라 **스위블**로 팔꿈치를 몸에서 띄운다.
# ★뻗음 k 도 같이 내렸다(0.88/0.90 -> 0.85/0.86). 팔꿈치를 더 굽히면(56.7 -> 63.6도)
#   팔꿈치가 축에서 더 멀어져(15.7 -> 16.2cm) 같은 EO 로도 더 뜨고, 무엇보다
#   **소프트하게 굽은 팔**이 균형 잡는 사람의 팔이다(편 팔은 차렷에 가깝다).
# ★좌우를 거울로 맞추지 않았다. 칼(1.66m)을 든 오른팔은 무게 때문에 f7 에 덜 벌어졌다가
#   f13 에 더 벌어진다(14.9 -> 25.5도). 왼팔은 그 사이에서 **거의 일정**하게 둔다
#   (23~26도) — 한쪽은 칼에 끌려가고 한쪽은 균형을 잡는, 그게 자연스러운 비대칭이다.
#   ★A(벌림)·F(앞으로)는 **한 칸도 안 건드렸다**. 바뀐 것은 EO(신설)와 두 정지 장의
#     k 뿐이다. 그래서 실측 '손목 벌림' 칸이 전 프레임 before 와 **같은 값**으로 나온다
#     = 손목 목표가 그대로고 **팔꿈치만** 돌았다는 증명이다.
#     t 0.09 줄은 전환 완충용으로 새로 끼웠고 A·F·k 는 위아래 두 키의 중점을 넣었다.
BAL_KEYS = [                    # (위상 t, 벌림 A도, 앞으로 F도, 뻗음 k=팔길이 비,
                                #  ★팔꿈치 방향 EO도(0=곧게 뒤 / +바깥 / -안쪽))
    (0.00, 12, -8, 0.84, -35),  # f1  웅크림. 아직 자루를 쥐고 있다(가중치 0)
    (0.09, 16, 1, 0.85, -30),   # f3  ★전환 완충용으로 끼운 줄(A·F·k 는 위아래 중점).
                                #     여기서 EO 를 미리 풀면 놓은 손이 f4 한 장 동안
                                #     앞을 지르는 그림이 나온다(실측 주먹면 -80 -> -18도)
    (0.18, 20, 10, 0.86, -16),  # f5  도약. 손을 놓으며 팔꿈치가 몸에서 떨어지기 시작
    (0.27, 26, 14, 0.85, +4),   # f7  ★상승 내내 이 자세로 멈춘다
    (0.55, 30, 2, 0.86, +3),    # f13 ★하강 내내 이 자세로 멈춘다
    (0.70, 22, 8, 0.86, -8),    # f16 착지 흡수. 팔을 내린다
    (1.00, 14, 2, 0.82, -35),   # f23 회복. Idle 로 0.18초 크로스페이드되며 다시 쥔다
]
# ★옛 판(오너 기각: 팔꿈치가 몸통에 붙는다). `LARM_OUT=0` 하나로 이 표와 옛 폴이
#   같이 돌아오고 **6줄 md5 까지 ca0e350a 로 일치**한다 = 이번 코드가 옛 경로를
#   한 톨도 안 건드렸다는 증명이자, before/after 를 같은 기계에서 다시 굽는 창구다.
#   (EO 칸은 옛 폴의 실측 각 -34.6도를 적어 둔 것이다. 이 표를 쓸 때는 안 읽힌다.)
BAL_KEYS_PRE = [
    (0.00, 12, -8, 0.84, -35),
    (0.18, 20, 10, 0.86, -35),
    (0.27, 26, 14, 0.88, -35),
    (0.55, 30, 2, 0.90, -35),
    (0.70, 22, 8, 0.86, -35),
    (1.00, 14, 2, 0.82, -35),
]
BAL_ON, BAL_FULL = 0.02, 0.18   # 파지->균형 전환 구간(위상). 도약 순간에 놓는다
# ★옛 판(LARM_OUT=0)의 팔꿈치 방향. 가슴 좌표계 X=왼쪽/Y=위/Z=앞 — 아래·약간 뒤·
#   **약간 안쪽**. 이 '약간 안쪽'이 팔꿈치를 갈비뼈에 붙여 놓은 범인이었다.
BAL_POLE = (-0.10, -1.00, -0.45)
# 0 이면 옛 경로 그대로(md5 재현 창구). 1 이면 위 EO 채널을 쓴다.
LARM_OUT = os.environ.get("LARM_OUT", "1") == "1"
if not LARM_OUT:
    BAL_KEYS = BAL_KEYS_PRE
# 튜닝 창구(굽는 값을 파일 안 고치고 바꾼다). "t,A,F,k,EO;t,..." 형식.
_bal_tab = os.environ.get("BAL_TABLE", "").strip()
if _bal_tab:
    BAL_KEYS = [tuple(float(x) for x in row.split(","))
                for row in _bal_tab.split(";") if row.strip()]


def bal_key(t):
    """위상 t 의 (A,F,k,EO). 구간 안은 smoothstep(속도가 튀면 팔이 홱 꺾인다)."""
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
    A, F, k = bal_key(t)[:3]
    A, F = math.radians(A), math.radians(F)
    u = Vector((math.sin(A), -math.cos(A) * math.cos(F), math.cos(A) * math.sin(F)))
    return wpos(pose, L_ARM[0]) + (torso_frame(pose) @ u) * (ARM_L * k)


def bal_pole(pose, t, S, T):
    """이번 프레임의 왼 팔꿈치가 향할 방향(월드 단위벡터). S 어깨 / T **이번 프레임의
    실제 손목 목표**(파지<->균형이 섞인 뒤의 값).

    ★어깨->손목 축에 **수직인 평면 안에서** 각(EO)으로 준다. 절대 방향 상수로 주면
      팔이 벌어질수록 그 상수가 축과 나란해져 수직 성분이 짧아지고, 팔꿈치가
      프레임마다 홱 돈다(옛 BAL_POLE 이 f13 에서 |perp| 0.39 까지 떨어졌다).
      바깥축은 팔이 아래로 늘어져 있는 한 축과 60도 이상 벌어져 늘 안정적이다.
      EO 0 = 곧게 뒤 · + = 바깥 · - = 안쪽.
    ★기준 축을 **섞인 뒤의 T** 로 잡는 것이 중요하다. 순수 균형 목표로 잡으면
      전환 두 장(f3·f4)에서 실제 팔 축과 어긋난 평면에 각을 재게 돼 팔꿈치가
      엉뚱한 데로 간다(실측: f2 외전이 -21.9 -> -39.0 도로 오히려 안으로 말렸다).
    """
    if not LARM_OUT:
        return (torso_frame(pose) @ Vector(BAL_POLE)).normalized()
    n = (T - S)
    if n.length < 1e-5:
        return (torso_frame(pose) @ Vector(BAL_POLE)).normalized()
    n.normalize()
    C = torso_frame(pose)
    o = C @ Vector((1, 0, 0))                        # 가슴 X = 왼쪽 = 왼팔의 바깥
    o = (o - n * o.dot(n))
    if o.length < 1e-4:                              # 팔을 옆으로 완전히 뻗은 경우
        return (torso_frame(pose) @ Vector(BAL_POLE)).normalized()
    o.normalize()
    b = -n.cross(o)                                  # 같은 평면의 '뒤' 축(외적 부호는
    if b.dot(C @ Vector((0, 0, -1))) < 0:            # 리그를 안 믿고 가슴 뒤로 검산한다)
        b = -b
    e = math.radians(bal_key(t)[3])
    return (b * math.cos(e) + o * math.sin(e)).normalized()


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
# ★★2026-08-13 오너 지시 3차로 **Wd(칼끝 벌림)를 통째로 다시 잡았다.**
#   "점프할때 왜 칼 뒤로감? 뭐 보통 한손으로 칼들고 점프하면 그냥 양팔이
#    살짜가벌려지는정도아님?"
#   진단: Wd 는 **'뒤'에서 재는 각**이다(위 swd_dirs 의 b 식. Wd=0 이면 정확히 뒤).
#   옛 값 22~40도는 곧 "칼끝을 거의 정확히 뒤로" 라는 뜻이었고, 실측도 그랬다
#   (칼끝 골반기준 뒤 -1.44~-1.50m). 팔을 내리려고 칼끝 고도만 신경 쓰다가
#   방위를 안 본 것이다. 90도 부근이 '몸 옆(오른쪽)', 그보다 크면 옆·앞이다.
#   그래서 15차는 Wd 를 88~106 으로 옮겼다 = **칼이 몸 옆으로 나간다.**
#
# ★★★2026-08-13 17차 — 그 "몸 옆"이 **화면에서 발밑 수직 장대**였다 (이번 수정)
#   16차 건틀릿 블라인드 비평이 SHEET_J3 #001~#003 을 집었다: 체공 중 칼이 캐릭터
#   발밑으로 곧게 뻗어 "막대에 꿰인 사람"으로 보인다. 원인은 15차가 고른 방향이
#   아니라 **재는 자**였다. 15차는 월드(몸 기준 오른쪽 +1.9m)로 통과시켰는데,
#   게임 카메라는 월드 yaw 고정이고 캐릭터만 돈다 —
#       캐릭터가 **화면 오른쪽을 보고 뛰면 몸 기준 오른쪽이 카메라 쪽**이 되고,
#       카메라 쪽 1m 는 화면에서 49.5px **아래**다(위로 1m 는 41.5px 위).
#   그래서 옆으로 내민 1.9m 이 통째로 화면 아래로 꽂혔다(실측 화면 칼 109px 중
#   수직편차 2~11도 · 칼끝이 발밑보다 95~99px 아래 · 몸 겹침 0.20~0.24).
#   자세한 기하와 8방향 표는 아래 [17차 신설: 8방향 화면 실루엣] 절에 있다.
#
#   무엇을 바꿨나 — 셋을 같이 눌렀다(하나만 고치면 다른 방향이 무너진다)
#     1) **칼끝을 든다**(E -27 -> +14/+18). 아래로 꽂히는 성분이 그만큼 준다.
#        칼끝 지면 여유도 +0.12m -> +1.3m 로 넉넉해진다(15차는 바닥에 붙어 있었다).
#     2) **방위를 45도 격자에서 비껴 놓는다**(Wd 90 -> 122/128). 8방향은 45도
#        간격이라 Wd 를 90 에 두면 어느 방향에서 **정확히 수직**이 된다.
#        32~38도 비껴 두면 최악 방향에서도 수직편차 36~47도가 남는다.
#     3) **팔꿈치를 굽힌다**(EB 신설 +40도). 1·2 만으로는 팔이 같이 들려
#        어깨 외전이 46도까지 벌어졌다(만세). 팔꿈치를 굽히면 팔-칼 사잇각이
#        32 -> 43도로 벌어져 **칼은 들고 위팔은 15~26도에 붙들 수 있다.**
#   ★A(팔 벌림)는 손목 기준 각이라 팔꿈치를 굽히면 위팔보다 커 보인다. 오너가 말한
#     "양팔이 살짝"은 **위팔 외전**이고, 실측 15~26도로 15~30도 구간 안이다.
#   ★E 와 A 를 아무렇게나 못 고르는 기하 근거: 이 함수는 팔을 통째로 돌리므로
#     팔-칼 사잇각이 소스가 준 상수(체공 32도, 팔꿈치 굽힌 뒤 43도)로 굳는다.
#     칼끝 고도는 언제나 정확히 나오고, 못 맞춘 몫은 **팔이 밀려서** 갚는다
#     (손목이 먹어 주는 몫이 SWD_WRIST 22도까지). 그래서 표를 고칠 때는 목표가
#     아니라 로그의 "실제로 나온" 칼·위팔 각을 보라.
SWD_KEYS = [       # (위상 t, 칼끝 고도 E도(음수=아래), 칼끝 벌림 Wd도(뒤에서 오른쪽),
                   #          팔 벌림 A도, 팔 앞으로 F도(음수=뒤), 팔꿈치 더 굽힘 EB도)
    (0.00, -14, 62, 14, 10, 0),    # f1  웅크림. 가중치 0이라 소스 그대로다
    (0.20,  +8, 114, 30, 16, 32),  # f5  도약. 칼끝이 들리며 앞옆으로 나온다
    (0.27, +14, 122, 34, 18, 40),  # f7  ★상승 내내 이 자세로 멈춘다
    (0.55, +18, 128, 36, 12, 40),  # f13 ★하강 내내 이 자세로 멈춘다
    (0.70,  +6, 114, 28, 10, 22),  # f16 착지 흡수. 칼끝이 내려오기 시작
    (1.00,  -6,  98, 16,  4, 0),   # f23 회복(가중치 0. 소스 착지 스윙으로 돌아간다)
]
# ★15차 판(오너 기각: 화면에서 발밑 수직 장대). `JUMP_V15=1` 로 언제든 재현된다 —
#   17차 before/after 표를 이 스위치 하나로 같은 기계에서 다시 뽑을 수 있다.
SWD_KEYS_V15 = [
    (0.00, -14, 62, 14, 10, 0),
    (0.20, -22, 84, 20, 6, 0),
    (0.27, -27, 90, 26, 4, 0),
    (0.55, -29, 94, 30, -2, 0),
    (0.70, -20, 86, 22, 4, 0),
    (1.00, -14, 76, 16, 2, 0),
]
if os.environ.get("JUMP_V15"):
    SWD_KEYS = SWD_KEYS_V15
# ══════════════════════════════════════════════════════════════════════════
# ★★24차 점프 — **대검을 몸통에 붙여 든다** (2026-08-24, 오너 "검을 들고 행하는
#   모든 건 논리적으로, 물리적으로도")
#   17차 판은 팔 벌림 목표 34/36(실측 위팔 외전 +16/+26)으로 칼을 몸 옆에 **내밀고**
#   뛰었다. 1.6m 슬래브를 한 손으로 몸에서 떨어뜨려 들면 관성 모멘트가 커져
#   비논리다(한 손 파지 자체는 12차 오너 지시 "한 손에 쥐고 뛰어야지" — 유지한다).
#   무거운 물건을 든 팔은 **팔꿈치를 더 굽혀 몸통에 붙인다**:
#     A 34/36→22/24 (팔 벌림 목표를 몸 쪽으로)  EB 40→54 (팔꿈치. 팔-칼 사잇각이
#     43→~48도로 벌어져 팔을 내려도 칼끝이 선다 — 17차와 같은 기하)
#     E +14/+18→+20/+24 (칼끝을 더 세워 화면 장대 성분·발밑 침투를 같이 줄인다)
#     Wd 122/128 은 17차 값 유지(45도 격자 비껴두기 — 8방향 수직편차의 근거)
#   ★8방향 화면 실루엣(jump_screen_audit)이 매 굽기마다 0/8 을 강제한다.
#   롤백: JUMP_V24=0 이면 17차 표. JUMP_V15=1 이면 그쪽이 이긴다(15차 재현 우선).
SWD_KEYS_V24 = [
    (0.00, -14, 62, 14, 10, 0),     # f1  웅크림. 가중치 0이라 소스 그대로
    (0.20, +12, 112, 24, 14, 46),   # f5  도약. 칼이 들리며 팔꿈치가 접힌다
    (0.27, +20, 122, 22, 15, 54),   # f7  ★상승 정지 — 칼을 몸에 붙여 세워 든다
    (0.55, +24, 128, 24, 10, 54),   # f13 ★하강 정지
    (0.70, +8, 112, 20, 8, 30),     # f16 착지 흡수. 무게가 내려오기 시작
    (1.00, -6, 98, 16, 4, 0),       # f23 회복(가중치 0. 소스 착지 스윙으로)
]
if os.environ.get("JUMP_V24", "1") == "1" and not os.environ.get("JUMP_V15"):
    SWD_KEYS = SWD_KEYS_V24
# 튜닝 창구(굽는 값을 파일 안 고치고 바꾼다). "t,E,Wd,A,F,EB;t,..." 형식.
_swd_tab = os.environ.get("SWD_TABLE", "").strip()
if _swd_tab:
    SWD_KEYS = [tuple(float(x) for x in row.split(","))
                for row in _swd_tab.split(";") if row.strip()]
# 가중치(위상, w). 도약 0.2초 안에 다 내리고, 착지 뒤에 소스로 돌려준다.
SWD_W = [(0.00, 0.0), (0.03, 0.0), (0.20, 1.0), (0.70, 1.0), (0.88, 0.55), (1.00, 0.0)]
# 손목이 먹어 줄 상한(도). 0 이면 팔이 칼 사잇각만큼 덜 내려간다.
SWD_WRIST = float(os.environ.get("SWD_WRIST", "22"))

# ══════════════════════════════════════════════════════════════════════════
# ★★18차 C — 서 있을 때(Idle) **칼을 세운다** (2026-08-13, 오너 지시)
#   오너: "칼쥐고 가만히잇을때 칼각도나 너무 눞혀져있다 조금세워야할듯?"
#   ★★진단은 '각도'가 아니라 **화면**이었다(16차 카메라 기하의 Idle 판).
#     커밋본 Idle 의 칼끝 월드 고도는 **+38.2도**다. 그런데 이 카메라의 시선축이
#     (위 -0.758, 앞 +0.653) 이라, 캐릭터가 **카메라를 보고 설 때** 칼 방향이
#     그 축과 거의 나란해진다 = 화면에서 칼이 접혀 사라진다(맨손으로 보인다).
#     실측 산수(연속 yaw 전체):
#         화면 칼 길이 비 = |cos(E + 40.7도)|      (E = 칼끝 월드 고도)
#         E +38.2 -> 최악 yaw 에서 **0.19** (19%)  <- 오너가 본 그림
#         E +45~50 -> 0.07~0.17 (더 나빠진다!)     <- "조금만" 세우면 역효과다
#     40% 이상을 만족하는 구간은 **E <= 26도** 또는 **E >= 73도** 둘뿐이다.
#     오너 지시("세워라")와 같은 방향인 것은 뒤쪽이라 **E +78도**(거의 수직)로 세운다.
#   ★팔은 안 올린다(만세 금지). 회전을 **손목에** 먹이므로 어깨·팔꿈치는 한 도도
#     안 움직인다. IDLE_ARM 에 비율을 주면 그만큼만 팔로 넘긴다.
#   ★방위(IDLE_AZ)를 45도 격자에서 22.5도 비껴 두는 이유는 17-점프기하와 같다.
#   손잡이:  IDLE_GUARD=0 이면 옛 Idle 이 그대로 나온다(되돌림 한 줄)
IDLE_GUARD = os.environ.get("IDLE_GUARD", "1") == "1"
IDLE_CLIPS = [c.strip() for c in os.environ.get("IDLE_CLIPS", "Idle").split(",")
              if c.strip()]
# ══════════════════════════════════════════════════════════════════════════
# ★★24차 Idle — **대검 하단세** (2026-08-24, 오너 "검이 지금 크잖아. 검을 들고
#   행하는 모든 건 논리적으로, 물리적으로도")
#   칼 실측(probe_sword_dims, 게임 1.75m 환산): 전장 1.83m(캐릭터 키보다 길다) ·
#   손목→칼끝 1.60m · 날 폭 최대 0.42m. 실물 츠바이헨더(1.7m)가 2~3.5kg 인데 이
#   비주얼은 강판 슬래브라 15~30kg 급으로 읽힌다 — 그 물건을 수직으로 계속 들고
#   서 있는 것(18차 E+78/70)은 비논리다. 칼끝을 낮춘 **하단세**로 바꾼다.
#   ★화면 계약(16차 산수)은 그대로 지켜진다: 화면 칼 길이 비 = |cos(E+40.7°)| 라
#     40% 이상 구간이 E≤26 또는 E≥73 둘뿐인데, 하단세 E-12 는 |cos(28.7)|=0.88 로
#     세운 판(E70 실측 최악 48%)보다 오히려 **더 잘 보인다.**
#   ★방위 +18 은 45도 격자에서 비껴 두는 17차 규칙 그대로(어느 yaw 도 순수 수직 금지).
#   ★IDLE_ARM 0.35: 회전의 35%를 팔이 먹는다(어깨에서 팔 전체가 내려온다) —
#     손목에만 51도를 다 먹이면 손목만 꺾인 그림이 된다. 손이 같이 내려와야
#     "무게에 팔이 끌려 내려간" 하단세다. 왼손 IK 는 옮겨진 자루를 따라온다.
#   ★★그런데 24차 실측에서 **하단세는 장대 게이트와 정면 충돌**로 판명났다:
#     8방향 화면 실루엣에서 「아래(정면)」 yaw 장대 점수 1.02(상한 0.55) —
#     칼끝이 발보다 72px 아래 + 수직편차 9도. 낮게 앞으로 겨눈 1.6m 칼은
#     8방향 중 어느 하나에서 반드시 카메라 쪽을 향해 "발밑 장대"가 된다
#     (기하 증명: 8방향 최악 상대방위 ≤22.5도 → 수직편차 상한 ~24도 → 통과 불가.
#      칼끝을 위로 올리는 것 말고는 출구가 없고 그건 하단세가 아니다).
#     E+35(구판, "눕혀져있다" 기각)~E+26 사이도 접힘 40% 계약이 막는다.
#     즉 이 카메라에서 정적 자세의 칼은 **수직 띠(E 73~82)** 말고 갈 곳이 없다.
#   그래서 **기본값은 세운 판(커밋본 70/35) 유지** = 게임 계약이 이긴다(과제 규칙).
#   하단세 데모(-12/+18/0.35)는 IDLE_V24=1 로 구워 오너 판정에 쓴다.
IDLE_V24 = os.environ.get("IDLE_V24", "0") == "1"
_IDLE_DEF = ("-12", "18", "0.35") if IDLE_V24 else ("78", "22", "0")
IDLE_E = float(os.environ.get("IDLE_E", _IDLE_DEF[0]))    # 칼끝 목표 고도(가슴 좌표계)
IDLE_AZ = float(os.environ.get("IDLE_AZ", _IDLE_DEF[1]))  # 칼끝 목표 방위(+=왼쪽)
IDLE_ARM = float(os.environ.get("IDLE_ARM", _IDLE_DEF[2]))  # 회전 중 팔이 먹을 비율


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
    E, Wd, A, F = _key_at(SWD_KEYS, t)[:4]
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
        return 0.0, 0.0, 0.0, 0.0, 0.0
    S = wpos(pose, R_ARM[0])
    EL = wpos(pose, R_ARM[1])
    W = wpos(pose, HAND_R)
    Hr = (A2W @ pose[HAND_R]).to_3x3()
    Hr.normalize()
    d = (Hr @ TIP_DIR).normalized()                 # 지금 칼끝 방향
    # ── ★★17차 신설: 팔꿈치 굽힘(EB) ──
    # 왜 필요한가. 이 함수는 팔 3본을 **통째로** 돌리므로 팔-칼 사잇각이 소스가
    # 준 상수(체공 구간 실측 32도)로 굳는다. 그래서 "칼끝을 들면 팔이 같이 들리고,
    # 팔을 내리면 칼끝이 같이 내려간다" — 15차가 칼끝을 내리다 못해 지면 18cm 까지
    # 간 것도, 17차 1차 시도에서 칼끝을 들자 팔이 46도까지 벌어진 것도 같은 뿌리다.
    # 사잇각을 벌리는 정공법은 **팔꿈치**다(사람도 큰 칼은 팔꿈치를 굽혀 든다).
    # 팔꿈치에서 팔뚝·손·칼을 함께 굽히면 파지는 한 톨도 안 변한다(칼은 손의 자식).
    eb = _key_at(SWD_KEYS, t)[4]
    if abs(eb) > 1e-4:
        nx = (EL - S).cross(W - EL)                 # 지금 굽어 있는 평면의 법선
        if nx.length < 1e-5:                        # 완전히 편 팔이면 가슴 왼쪽축으로
            nx = torso_frame(pose) @ Vector((1, 0, 0))
        qe = Quaternion(nx.normalized(), math.radians(eb) * w)
        Rw[R_ARM[1]] = qe.to_matrix() @ Rw[R_ARM[1]]
        Rw[R_ARM[2]] = qe.to_matrix() @ Rw[R_ARM[2]]
        W = EL + qe @ (W - EL)                      # 손목이 팔꿈치 둘레로 돈다
        d = (qe @ d).normalized()                   # 칼도 같이 돈다
    a = (W - S).normalized()                        # 지금 팔 방향
    # ★17차: **팔-칼 사잇각**(파지가 정한 상수. 팔꿈치를 굽힌 뒤 값이다).
    #   이 각 + 손목 상한이 곧 "칼끝을 얼마나 올리면서 팔을 얼마나 내릴 수 있나"의
    #   한계다. 칼끝 고도 E 는 항상 정확히 나오고(회전으로 맞추니까), 못 맞추면
    #   **팔**이 밀린다 — 그래서 팔 각도는 목표가 아니라 실측을 봐야 한다.
    nat = math.degrees(d.angle(a))
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
    return (math.degrees(q.angle), math.degrees(wr * w), w, nat,
            math.degrees(max(0.0, rest - math.radians(SWD_WRIST))) * w)


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
            # 팔꿈치가 향할 방향도 같은 비율로 넘긴다(EO 채널). 툭 끊기지 않게
            # 원래 팔꿈치 방향에서 섞는다.
            pole = (E - S).normalized().lerp(bal_pole(pose, ph, S, T), wb)
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


# ------------------------------------------------------- 놓은 손 주먹 방향 (17차)
# ★오너 지시(2026-08-13): **"점프했을때 검안쥔손 주먹이 왜 하늘을향하고있냐"**
#
# 무엇이 하늘을 보고 있었나 (실측 blender/probe_jump_lhand.py · committed aa60d350)
#   주먹 메시에는 손가락·엄지·너클이 없다(13-손목에서 광선 스캔으로 확인). 방향은
#   셋으로 잰다 — **팔축**(손목원점->주먹중심. 주먹의 앞면, 손가락 마디 골이 보이는
#   쪽이다) · 구멍축(마디가 늘어선 방향) · 손등축. 체공 구간의 팔축 월드 고도:
#       f5 +72 · f7 **+87** · f9 **+90** · f13 **+82** · f15 +77   (+90 = 똑바로 하늘)
#   주먹 앞면이 거의 정확히 수직으로 하늘을 봤다. **손등은 밖(+0.97)이라 맞았다** —
#   틀린 것은 손목이다. 왼손목 기하각(팔꿈치->손목 vs 손목->주먹중심)이 체공 내내
#   **128~132도**였다(레스트 중립 16.8도, 사람 굴곡·신전 한계 60~70도).
#   팔뚝은 -38~-43도로 내려가 있는데 손만 팔뚝 위로 접혔으니 주먹은 자동으로 하늘이다.
#   ★13차의 "손등 하늘"과는 **다른 병**이다. 그때는 주먹 구멍축이 90도 어긋난
#     것(칼이 손바닥에서 손등으로 꿰뚫음)이었고, 이번은 축은 맞는데 손목이 접혔다.
#     그래서 이번 처방은 메시 회전이 아니라 **손뼈 방향**이다.
#
# 왜 아무도 안 잡고 있었나 — 13-손목의 교정이 체공에서 **꺼진다**
#   apply_hand_grip 의 가중치는 wh = 파지게이트 x (1 - 균형가중치)^2 다. 체공은
#   균형가중치가 1 이라 wh = 0 이다. 그건 맞다(놓은 손이 허공의 자루를 쥐면 안 된다).
#   문제는 **놓은 뒤의 손 방향을 정하는 코드가 없었다**는 것이다. 그래서 소스
#   (양손검 점프)의 리타게팅 손 회전이 그대로 남고, 그 손은 '자루를 쥔 손' 모양이라
#   팔이 벌어지면 주먹이 하늘로 돌아간다. 17-점프기하는 오른팔·칼만 다뤘고 여기는
#   못 봤다(그 판의 무회귀 표에도 왼손 항목이 없다).
#
# 어떻게 고치나 — 손 방향을 **팔뚝에서** 정한다 (팔·칼·오른손은 한 톨도 안 건드린다)
#   자연스러운 점프에서 벌린 팔의 손은 팔뚝을 거의 그대로 잇고(손목 15~20도),
#   손등이 바깥·위를 본다. 그 둘을 그대로 목표로 준다:
#     · 팔축   -> 팔뚝 방향에서 **손바닥 쪽으로 BEND 도** 기운 방향
#                 = 주먹 앞면이 아래·안쪽. ★손목 기하각이 정확히 BEND 로 나온다
#                   (상한을 따로 둘 필요가 없다. 각을 직접 주는 구조다)
#     · 손등축 -> 팔뚝에 수직인 '바깥쪽'을 팔뚝 둘레로 ROLL 도 돌린 방향
#                 (ROLL 0=바깥 · +90=앞 · -90=뒤. 이게 곧 아래팔 회내/회외다)
#   두 목표가 서로 수직이라 회전 하나로 정확히 만족한다([왼손 손목]과 같은 구조).
#   ★기준을 '월드 위'가 아니라 **'가슴 바깥'** 으로 잡은 근거: 체공에서 팔뚝이
#     -38~-43도로 거의 아래를 보므로 '위'를 기준으로 잡으면 투영이 무너진다.
#     균형 팔은 벌림 12~30도 안에 있어 팔뚝이 늘 아래를 향하니, 가슴 바깥축은
#     팔뚝과 60도 이상 벌어진 채로 유지된다(안정적이다).
#   ★가중치는 균형 팔과 **같은 bal_weight** 다. 손을 놓는 그 비율만큼만 손도 돈다.
#     apply_hand_grip(파지 손) 뒤에 이어 붙이므로 전환 구간에서 두 목표가 섞인다.
FST_KEYS = [                 # (위상 t, 손등 롤 ROLL도(0=바깥/+90=앞), 손목 굽힘 BEND도)
    (0.00,  0, 16),          # f1  웅크림. 가중치 0이라 안 쓰인다(연속성용)
    (0.18,  8, 18),          # f5  도약. 손을 놓으며 주먹이 팔뚝을 따라 내려온다
    (0.27, 12, 16),          # f7  ★상승 내내 이 자세로 멈춘다
    (0.55, 12, 16),          # f13 ★하강 내내 이 자세로 멈춘다
    (0.70,  6, 20),          # f16 착지 흡수
    (1.00,  0, 22),          # f23 회복. Idle 로 크로스페이드되며 다시 쥔다
]
HAND_FREE = os.environ.get("HAND_FREE", "1") == "1"      # 0 이면 옛 판 재현
_fst_tab = os.environ.get("FST_TABLE", "").strip()
if _fst_tab:
    FST_KEYS = [tuple(float(x) for x in row.split(","))
                for row in _fst_tab.split(";") if row.strip()]


def apply_hand_free(pose, Rw, t):
    """검을 놓은 왼손의 주먹 방향을 팔뚝에서 다시 쓴다.

    반환 (전 주먹면 고도, 후 주먹면 고도, 후 손목 기하각, 가중치). 안 건드리면 None.
    """
    if FF_L is None or not HAND_FREE or t is None:
        return None
    w = bal_weight(t)
    if w <= 1e-4:
        return None
    _, ax_l, _, bak_l = FF_L                    # 팔축 · 손등축(둘은 서로 수직이다)
    W = wpos(pose, HAND_L)
    E = wpos(pose, L_ARM[1])
    f = (W - E).normalized()                    # 팔뚝 방향(팔꿈치 -> 손목)
    a0 = (Rw[HAND_L] @ ax_l).normalized()
    e0 = math.degrees(math.asin(max(-1.0, min(1.0, a0.z))))
    ROLL, BEND = _key_at(FST_KEYS, t)
    out = torso_frame(pose) @ Vector((1, 0, 0))  # 가슴 X = 왼쪽 = **왼손의 바깥쪽**
    o0 = out - f * out.dot(f)
    if o0.length < 1e-4:                        # 팔을 옆으로 완전히 뻗은 경우(안 온다)
        return None
    o0.normalize()
    rl, bd = math.radians(ROLL), math.radians(BEND)
    b0 = (o0 * math.cos(rl) + f.cross(o0) * math.sin(rl)).normalized()   # 손등 목표
    n = (f * math.cos(bd) - b0 * math.sin(bd)).normalized()              # 팔축 목표
    b = (b0 - n * b0.dot(n)).normalized()       # 손등 목표를 팔축에 수직으로 다시 세운다
    # 손 로컬 (팔축, 손등축, 그 외적) -> 월드 (n, b, 그 외적). 둘 다 정규직교라
    # 행렬 하나가 곧 회전이다(det=+1 이 보장된다). [왼손 손목]과 같은 수법.
    Ml = Matrix((ax_l, bak_l, ax_l.cross(bak_l))).transposed()
    Mt = Matrix((n, b, n.cross(b))).transposed()
    q = Rw[HAND_L].to_quaternion().slerp((Mt @ Ml.inverted()).to_quaternion(), w)
    Rw[HAND_L] = q.to_matrix()
    a1 = (Rw[HAND_L] @ ax_l).normalized()
    return (e0, math.degrees(math.asin(max(-1.0, min(1.0, a1.z)))),
            math.degrees(f.angle(a1)), w)


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


# ---- ★25차 GRIP_V25: 손등 계약 롤 도구 (Idle 이 쓴다) ----
def _back_roll_solve(pose):
    """f0 자세에서 손등 계약([-25,+35]도 + 바깥 반구)을 만드는 최소 칼축 롤.
    반환 (롤 rad, 칼축 월드, 전 고도, 전 바깥, 후 고도, 후 바깥)."""
    Hr = (A2W @ pose[HAND_R]).to_3x3()
    Hr.normalize()
    u = (Hr @ TIP_DIR).normalized()
    bak = (Hr @ BACK_L).normalized()
    Ci = torso_frame(pose).inverted()

    def stat(v):
        return (math.degrees(math.asin(max(-1.0, min(1.0, v.z)))), -(Ci @ v).x)

    e0, o0 = stat(bak)
    best = None
    for pd in range(-90, 91):
        b2 = (Quaternion(u, math.radians(pd)) @ bak).normalized()
        e, o = stat(b2)
        ok = (-25.0 <= e <= 35.0) and o > 0.0
        pen = 0.0 if ok else (max(0.0, e - 35.0) + max(0.0, -25.0 - e)
                              + max(0.0, -o) * 100.0)
        key = (0 if ok else 1, pen, abs(pd))
        if best is None or key < best[0]:
            best = (key, pd, e, o)
    return math.radians(best[1]), u, e0, o0, best[2], best[3]


def _apply_axis_roll(Rw, ang, axis):
    """칼축 둘레 롤을 손목(상한 45도) + 잔여는 팔 체인 강체 롤로 나눠 먹인다.
    축이 칼축이라 칼끝·칼 선분은 불변이다(판정·FX 무영향)."""
    cap = math.radians(45.0)
    wr = max(-cap, min(cap, ang))
    rest = ang - wr
    if abs(rest) > 1e-6:
        m = Quaternion(axis, rest).to_matrix()
        for bn in R_ARM:
            Rw[bn] = m @ Rw[bn]
    if abs(wr) > 1e-6:
        Rw[HAND_R] = Quaternion(axis, wr).to_matrix() @ Rw[HAND_R]


# ================================================================ 7) 굽기
def bake(name):
    f0, f1 = use_src(name)
    nf = f1 - f0 + 1
    rel = name in RELEASE and DO_GRIP
    swd = name in SWDOWN
    idl = IDLE_GUARD and name in IDLE_CLIPS and TIP_DIR is not None
    IDL_M = [None]          # f0 에서 한 번 정하고 **전 프레임에 같은 회전**을 먹인다
                            # (프레임마다 다시 잡으면 숨쉬기 흔들림이 죽는다)
    IDL_ROLL = [None]       # ★25차: 손등 계약 롤도 f0 에서 한 번(전 프레임 동일)
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
        print("   균형 팔 위상표(t / 벌림 / 앞으로 / 뻗음 / ★팔꿈치 EO(0=뒤,+바깥) /"
              " 파지->균형 가중치):")
        for t, A, F, k, EO in BAL_KEYS:
            print("      t %.2f (f%-2d)  A %+3d도  F %+3d도  k %.2f  팔꿈치 EO %+4d도"
                  "   w %.2f"
                  % (t, f0 + int(round(t * (nf - 1))), A, F, k, EO, bal_weight(t)))
        if not LARM_OUT:
            print("      ★LARM_OUT=0 — EO 를 안 쓰고 옛 폴(%s)로 굽는다" % (BAL_POLE,))
    if swd:
        print("   오른팔(검) 위상표(t / 칼끝 고도·벌림 / 팔 벌림·앞으로(음수=뒤) /"
              " 팔꿈치 / 가중치):")
        for t, E, Wd, A, F, EB in SWD_KEYS:
            print("      t %.2f (f%-2d)  칼끝 E %+3d도 Wd %+3d도   팔 A %+3d도 F %+3d도"
                  "   팔꿈치 %+3d도   w %.2f"
                  % (t, f0 + int(round(t * (nf - 1))), E, Wd, A, F, EB,
                     _key_at(SWD_W, t)[0]))

    if rel and HAND_FREE:
        print("   놓은 손 위상표(t / 손등 롤(0=바깥,+90=앞) / 손목 굽힘 / 가중치):")
        for t, RL, BD in FST_KEYS:
            print("      t %.2f (f%-2d)  롤 %+3d도  굽힘 %+3d도   w %.2f"
                  % (t, f0 + int(round(t * (nf - 1))), RL, BD, bal_weight(t)))

    lows, maxerr, befs, afts, swds, wrs, frs = [], 0.0, [], [], [], [], []
    jtips, jhnds, jhips, jchs, larms = [], [], [], [], []
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
        if idl:
            # ★18차 C: 칼만 세운다. 파지보다 **먼저**(왼손이 따라와야 한다).
            if IDL_M[0] is None:
                Hr0 = (A2W @ pose[HAND_R]).to_3x3()
                Hr0.normalize()
                d0 = (Hr0 @ TIP_DIR).normalized()
                C0i = torso_frame(pose)
                bt0 = (C0i @ _sph(IDLE_E, IDLE_AZ)).normalized()
                IDL_M[0] = d0.rotation_difference(bt0)
                print("   ★Idle 칼 세우기: 칼끝 %+.1f/%+.1f -> 목표 %+.1f/%+.1f"
                      " (회전 %.1f도, 팔 몫 %.0f%%)"
                      % (*_unsph(C0i.inverted() @ d0), IDLE_E, IDLE_AZ,
                         math.degrees(IDL_M[0].angle), IDLE_ARM * 100))
            q = IDL_M[0]
            if IDLE_ARM > 1e-6:
                qa = Quaternion().slerp(q, IDLE_ARM)
                ma = qa.to_matrix()
                for bn in R_ARM:
                    Rw[bn] = ma @ Rw[bn]
                qh = q @ qa.inverted()          # 남은 몫은 손목이 먹는다
                Rw[HAND_R] = qh.to_matrix() @ Rw[HAND_R]
            else:
                Rw[HAND_R] = q.to_matrix() @ Rw[HAND_R]
            pose, basis = build(Rw, pw)
            # ★25차 GRIP_V25: 손등 계약 롤(칼축 둘레 = 칼끝 E/AZ·칼 선분 불변)
            if GRIP_V25 and BACK_L is not None:
                if IDL_ROLL[0] is None:
                    ang, u1, e0, o0, e1, o1 = _back_roll_solve(pose)
                    IDL_ROLL[0] = (ang, u1)
                    print("   ★손등 계약(GRIP_V25): 고도 %+.1f 바깥 %+.2f -> 롤 %+.1f도"
                          " -> 고도 %+.1f 바깥 %+.2f  (계약 [-25,+35] + 바깥 반구)"
                          % (e0, o0, math.degrees(ang), e1, o1))
                if abs(IDL_ROLL[0][0]) > 1e-6:
                    _apply_axis_roll(Rw, IDL_ROLL[0][0], IDL_ROLL[0][1])
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
            # ★17차 신설: 손을 **놓은 뒤**의 주먹 방향(파지 교정 다음에 온다.
            #   가중치가 서로 여집합이라 전환 구간에서 두 목표가 섞인다)
            rf = apply_hand_free(pose, Rw, phase(i))
            if rf:
                frs.append(rf)
                pose, basis = build(Rw, pw)
        if rel:
            # ★왼팔도 **실제로 나온 각**을 잰다(오른팔 jchs 와 같은 규칙).
            #   A(BAL_KEYS) 는 손목 기준 목표라 위팔이 얼마나 벌어졌는지를 못 말한다 —
            #   그 착각이 팔꿈치를 갈비뼈에 붙여 놓고도 "A 26도면 살짝 벌림"이라고
            #   통과시킨 원인이다(17차 함정 4의 왼팔판).
            Cl = torso_frame(pose).transposed()     # 월드 -> 가슴(X=왼쪽=왼팔 바깥)
            Sl, El, Wl = (wpos(pose, L_ARM[0]), wpos(pose, L_ARM[1]),
                          wpos(pose, HAND_L))
            vu = Cl @ (El - Sl).normalized()
            vw = Cl @ (Wl - Sl).normalized()
            Pv, Nv = wpos(pose, PELVIS), wpos(pose, NECK)
            sv = Nv - Pv
            ss = 0.0 if sv.length_squared < 1e-9 else max(
                0.0, min(1.0, (El - Pv).dot(sv) / sv.length_squared))
            larms.append((
                math.degrees(math.asin(max(-1.0, min(1.0, vu.x)))),   # 위팔 외전
                math.degrees(math.asin(max(-1.0, min(1.0, vw.x)))),   # 손목 기준 벌림
                math.degrees((El - Sl).angle(Wl - El)),               # 팔꿈치 굽힘
                (Cl @ (El - Sl)).x,                                   # 팔꿈치 바깥
                (El - (Pv + sv * ss)).length,                         # 팔꿈치-척추축
                (Cl @ (El - Sl)).z))                                  # 팔꿈치 앞뒤
        for bn in ORDER:
            arm.pose.bones[bn].matrix_basis = basis[bn]
        bpy.context.view_layer.update()
        if i % 20 == 0:                             # 해석식 자기검증(★함정 8)
            for bn in ORDER:
                a = (A2W @ arm.pose.bones[bn].matrix).translation
                b = (A2W @ pose[bn]).translation
                maxerr = max(maxerr, (a - b).length)
        lows.append(low_of(DST_BODY))
        if TIP_DIR is not None and D_SW:
            HMj = A2W @ pose[HAND_R]
            jtips.append(HMj @ (TIP_DIR * D_SW[2] * ANIM_TIP_K
                                / HMj.to_3x3().to_scale()[0]))
            jhnds.append(wpos(pose, HAND_R))
            jhips.append(wpos(pose, PELVIS))
            # ★17차: **목표가 아니라 실제로 나온 각**을 잰다. 목표(SWD_KEYS)는
            #   손목 상한(SWD_WRIST)에 걸리면 그대로 안 나온다 — 표만 보고
            #   "몸 옆이다"라고 판정하면 15차와 같은 실수를 반복한다.
            Cj = torso_frame(pose)                       # 가슴축(열=X왼쪽/Y위/Z앞)
            Ct = Cj.transposed()
            vb = Ct @ (jtips[-1] - jhnds[-1]).normalized()
            va = Ct @ (jhnds[-1] - wpos(pose, R_ARM[0])).normalized()
            # ★어깨 외전은 '어깨->손목'이 아니라 **'어깨->팔꿈치'(위팔)** 로 재야
            #   오너가 말한 "양팔이 살짝 벌어지는 정도"와 같은 뜻이 된다.
            #   팔꿈치를 굽히면 손목은 더 벌어져도 위팔은 몸에 붙어 있을 수 있다.
            vu = Ct @ (wpos(pose, R_ARM[1]) - wpos(pose, R_ARM[0])).normalized()
            jchs.append((
                math.degrees(math.asin(max(-1.0, min(1.0, vb.y)))),      # 칼끝 고도 E
                math.degrees(math.atan2(-vb.x, -vb.z)),                  # 칼끝 방위 Wd
                math.degrees(math.atan2(-va.x, math.hypot(va.y, va.z))),  # 팔 벌림 A
                math.degrees(math.atan2(va.z, -va.y)),                   # 팔 앞뒤 F
                math.degrees((Cj @ Vector((0, 1, 0))).angle(W_UP)),      # 몸 기울기
                math.degrees(math.atan2(-vu.x, math.hypot(vu.y, vu.z))),  # 위팔 외전
                math.degrees((wpos(pose, R_ARM[0]) - wpos(pose, R_ARM[1])).angle(
                    jhnds[-1] - wpos(pose, R_ARM[1])))))                 # 팔꿈치 굽힘
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
    if larms:
        gkl = 1.75 / DH
        print("   ★왼팔(균형) **실제로 나온** 값 — 위팔 외전이 오너 기준"
              "('살짝 벌림' 15~30도)의 과녁이다")
        print("     %3s %8s %8s %8s %9s %9s"
              % ("f", "위팔외전", "손목벌림", "팔꿈치굽힘", "팔꿈치바깥", "척추거리"))
        for i, r in enumerate(larms):
            print("     f%-2d %+7.1f도 %+7.1f도 %7.1f도 %+8.3fm %8.3fm"
                  % (i, r[0], r[1], r[2], r[3] * gkl, r[4] * gkl))
        air = [larms[i] for i in range(len(larms)) if JUMP_AIR[0] <= i <= JUMP_AIR[1]]
        if air:
            print("     체공 f%d~f%d: 위팔 외전 %+.1f~%+.1f도 · 굽힘 %.1f~%.1f도"
                  " · 팔꿈치 바깥 %+.3f~%+.3fm · 척추거리 %.3f~%.3fm"
                  % (JUMP_AIR[0], JUMP_AIR[1],
                     min(r[0] for r in air), max(r[0] for r in air),
                     min(r[2] for r in air), max(r[2] for r in air),
                     min(r[3] for r in air) * gkl, max(r[3] for r in air) * gkl,
                     min(r[4] for r in air) * gkl, max(r[4] for r in air) * gkl))
        for h in JUMP_HOLDS:
            if h < len(larms):
                r = larms[h]
                print("     ★f%-2d(게임 정지) 위팔 외전 %+.1f도 · 팔꿈치 굽힘 %.1f도"
                      " · 팔꿈치 바깥 %+.3fm · 척추거리 %.3fm"
                      % (h, r[0], r[2], r[3] * gkl, r[4] * gkl))
    if frs:
        on = [r for r in frs if r[3] > 0.5]
        if on:
            e0 = sorted(r[0] for r in on)
            e1 = sorted(r[1] for r in on)
            g1 = sorted(r[2] for r in on)
            print("   ★놓은 손 주먹면 고도(+90 = 똑바로 하늘): 전 %+.0f~%+.0f"
                  " -> 후 %+.0f~%+.0f / 손목 기하각 후 %.0f~%.0f도 (%d/%d 프레임)"
                  % (e0[0], e0[-1], e1[0], e1[-1], g1[0], g1[-1], len(on), nf))
    if swd and swds:
        act_f = [(i, d, wr, nt, er) for i, (d, wr, w, nt, er) in enumerate(swds)
                 if w > 1e-4]
        print("   오른팔 회전량: %d/%d 프레임 적용 (팔 최대 %.1f도 f%d / 평균 %.1f도,"
              " 손목 되돌림 최대 %.1f도)"
              % (len(act_f), nf, max(r[1] for r in act_f),
                 f0 + max(act_f, key=lambda r: r[1])[0],
                 sum(r[1] for r in act_f) / len(act_f),
                 max(r[2] for r in act_f)))
        print("   ★팔-칼 사잇각(파지 상수) %.0f~%.0f도 + 손목 상한 %.0f도"
              " = 팔을 내릴 수 있는 한계. 목표 못 채운 팔 오차 최대 %.1f도"
              % (min(r[3] for r in act_f), max(r[3] for r in act_f), SWD_WRIST,
                 max(r[4] for r in act_f)))

    if swd and jtips:
        gkj = 1.75 / DH
        ORG = DREST[ROOT_BONE][1]                 # 게임 루트(발밑)의 수평 기준점
        print("   ★칼끝(게임 1.75m 환산): 프레임 / 바닥여유 / 골반기준 오른쪽·위·앞 /"
              " 오른손 높이 / **실제로 나온** 칼끝 고도·방위 · 손목 벌림·앞뒤 ·"
              " 위팔 외전 · 팔꿈치 굽힘 · 몸기울기 · 팔칼 사잇각")
        for i, t in enumerate(jtips):
            d = t - jhips[i]
            E_a, W_a, A_a, F_a, tl, UA, EBa = jchs[i]
            print("     f%-3d  바닥 %+.3f   오른 %+.2f 위 %+.2f 앞 %+.2f   손 %.2f"
                  "   칼 E%+4.0f Wd%+4.0f  손목 A%+4.0f F%+4.0f  위팔%+4.0f"
                  "  팔꿈치%4.0f  몸%3.0f  사잇각%4.0f"
                  % (i, (t.z + shift - BIND_LOW) * gkj,
                     -d.dot(W_LFT) * gkj, d.dot(W_UP) * gkj, d.dot(W_FWD) * gkj,
                     (jhnds[i].z + shift - BIND_LOW) * gkj,
                     E_a, W_a, A_a, F_a, UA, EBa, tl,
                     swds[i][3] if i < len(swds) else 0.0))

        # ── ★★17차: 여덟 방향 화면 실루엣 (이 파도의 진짜 자) ──
        def _loc(P):
            dd = P - ORG
            return (-dd.dot(W_LFT) * gkj, (P.z + shift - BIND_LOW) * gkj,
                    dd.dot(W_FWD) * gkj)

        jump_screen_audit([(_loc(h), _loc(t)) for h, t in zip(jhnds, jtips)])

    # ── ★18차 C: Idle 도 여덟 방향 화면으로 잰다 ──
    # 서 있는 자세는 게임에서 제일 오래 보는 그림이고, 오너가 본 "칼이 눕혀졌다"는
    # 실은 **화면에서 접힌 것**이었다. 점프와 같은 자를 그대로 댄다(멈춤 장 = f0·중간).
    if idl and jtips:
        gkj = 1.75 / DH
        ORG = DREST[ROOT_BONE][1]

        def _loci(P):
            dd = P - ORG
            return (-dd.dot(W_LFT) * gkj, (P.z + shift - BIND_LOW) * gkj,
                    dd.dot(W_FWD) * gkj)

        te = [jchs[i][0] for i in range(len(jchs))]
        tw = [jchs[i][1] for i in range(len(jchs))]
        print("   ★Idle 칼끝 고도 %+.1f~%+.1f도 · 방위 %+.1f~%+.1f도 ·"
              " 바닥여유 %+.3f~%+.3f m · 오른손 높이 %.2f~%.2f m"
              % (min(te), max(te), min(tw), max(tw),
                 min((t.z + shift - BIND_LOW) * gkj for t in jtips),
                 max((t.z + shift - BIND_LOW) * gkj for t in jtips),
                 min((h.z + shift - BIND_LOW) * gkj for h in jhnds),
                 max((h.z + shift - BIND_LOW) * gkj for h in jhnds)))
        jump_screen_audit([(_loci(h), _loci(t)) for h, t in zip(jhnds, jtips)],
                          holds=(0, nf // 2), air=(0, nf - 1),
                          title="Idle 8방향 화면 실루엣")

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
        if idl and IDL_M[0] is not None:            # ★18차 C. 1차와 같은 자리·같은 회전
            q = IDL_M[0]
            if IDLE_ARM > 1e-6:
                qa = Quaternion().slerp(q, IDLE_ARM)
                ma = qa.to_matrix()
                for bn in R_ARM:
                    Rw[bn] = ma @ Rw[bn]
                Rw[HAND_R] = (q @ qa.inverted()).to_matrix() @ Rw[HAND_R]
            else:
                Rw[HAND_R] = q.to_matrix() @ Rw[HAND_R]
            pose, basis = build(Rw, pw)
            # ★25차 GRIP_V25: 1차와 같은 자리·같은 롤
            if GRIP_V25 and IDL_ROLL[0] is not None and abs(IDL_ROLL[0][0]) > 1e-6:
                _apply_axis_roll(Rw, IDL_ROLL[0][0], IDL_ROLL[0][1])
                pose, basis = build(Rw, pw)
        if DO_GRIP:
            _, _, _, _, Ch, wh = apply_grip(pose, Rw, gts[i], phase(i))
            pose, basis = build(Rw, pw)
            if apply_hand_grip(pose, Rw, Ch, wh):       # ★1차와 같은 순서로
                pose, basis = build(Rw, pw)
            if apply_hand_free(pose, Rw, phase(i)):
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


# =============================================== 7c) 수제 키프레임 (15-모션수제)
# ★오너 지시(2026-08-12 밤): "칼 베는거 안고쳐짐 그냥 너가 직접 베는 모션 만들어.
#   위에서아래로. 옆으로."
#   Meshy 프리셋 트림(13-모션이식 -> 14-베기수정)으로 두 번 고쳤는데 두 번 다
#   기각됐다. 소스가 **한 손 과장 연기**라 어디를 잘라도 몸짓이 남는다 —
#   자르는 일로는 끝이 없다는 뜻이라, Z/X/C 를 손으로 짠 키프레임으로 다시 만든다.
#   (ANIM_DIR/ANIM_SPEC 프리셋 경로는 코드로 남겨 두었다. HAND 를 안 주면 그 길이
#    그대로 살아 있어서 14차 판이 언제든 재현된다.)
#
# ── 무엇을 손으로 적나 (뼈 각도를 직접 적지 않는다) ──
# 뼈 로컬 각도를 적으면 리그마다 축이 달라 읽을 수도 고칠 수도 없다(이 레포에서
# 두 리그의 손뼈 로컬축이 46~74도 어긋나 있다). 그래서 **화면에서 보이는 것**을 적는다:
#     bel/baz   칼끝이 어디를 겨누나   가슴 좌표계 고도(+위)/방위(0=앞, +=왼쪽)
#     arl       팔을 **칼 축 둘레 어디에** 둘 것인가(roll 도. 0=칼 아래쪽)
#               ★팔이 칼과 이루는 각은 파지가 정한 상수(약 80도)라 팔에
#                 줄 수 있는 자유는 이 하나뿐이다. 자세한 근거는 아래 겨누기 절.
#     bend      팔꿈치를 얼마나 더 굽히나(바탕 자세 대비 증분. +=더 굽힘)
#     ty/tp/tr  가슴 돌림(+왼쪽)/숙임(+앞)/기울임(+오른쪽)
#     hy        골반 돌림(+왼쪽. 발은 제자리라 허리가 꼬인다)
#     cr        웅크림(도). 엉덩이-무릎-발목 3분절이 같이 접혀 골반이 내려간다
#     lg        스탠스(도). + 는 **왼발이 앞·오른발이 뒤**(오른손잡이 칼 발놀림).
#               허벅지만 앞뒤로 갈라 돌린다 = 발이 앞뒤로 벌어지고 골반이 내려앉는다.
#               ★이게 없으면 아무리 칼을 잘 휘둘러도 "제자리에 뻣뻣하게 서서 팔만
#                 흔드는" 그림이 된다(1차 실루엣 시트에서 그대로 보였다).
#     wf/ws     ★16차 신설. **골반(무게중심) 자체를 옮긴다.** 게임 cm 단위.
#               wf + 는 앞, ws + 는 왼쪽. 발은 제자리에 두려고 허벅지를 반대로
#               돌린다(안 그러면 발이 골반을 따라 통째로 미끄러진다).
#               ★15차까지 골반 수평 이동이 **세 클립 전부 0.000m** 이었다. lg/cr 은
#                 다리를 접고 벌릴 뿐 무게를 옮기지 못한다 — 그래서 "팔만 흔든다"가
#                 수치로 증명됐다(임팩트 때 손 속도/칼끝 속도 0.19~0.26).
#     gw        왼손이 자루를 쥔 정도(1=두 손. 0 이면 왼팔이 바탕 자세로 남는다)
# 이 값들은 **회전 하나**로 오른팔에 먹인다(= [오른팔 내리기] 절이 점프에서 쓰던
# 검증된 방식 그대로):
#     1) 칼끝을 목표 방향으로 보내는 최소회전
#     2) **칼축 둘레**로 더 돌려(칼끝은 안 움직인다) 팔을 arl 자리에 놓는다
#   ★팔 목표를 '절대 방향'으로 주면 안 되는 이유는 아래 겨누기 절에 실측으로 적었다.
#     (그래서 HAND_WRIST 손목 잔각은 지금 늘 0 이다 — 진단용으로만 남겨 둔다)
#
# ── ★바탕 자세 = Idle 첫 프레임 ──
# f0 을 Idle 과 **같은 자세**로 두면 크로스페이드가 건너뛸 거리가 0 이라
# "캐스트 첫 프레임 물보라"(14차의 남은 것 3번)가 구조적으로 사라진다.
# 프리셋을 트림하는 방식으로는 절대 못 하던 것이다 — 소스의 첫 자세는 남의 자세니까.
# 그래서 f0 키는 **자동으로** 바탕값이 박히고(아래 base), 마지막 키에 "base" 라고
# 적으면 그 채널이 다시 바탕값으로 돌아온다.
#
# ── ★채널마다 따로 키를 찍는다 ──
# 한 프레임에 모든 채널을 적을 필요가 없다. 적은 채널만 그 프레임에 키가 생기고
# 나머지는 자기 이웃 키끼리 이어진다(진짜 키프레임 작업과 같다). 보간은
# Catmull-Rom 이라 키를 촘촘히 두면 그 구간이 빨라지고, 살짝 넘어갔다 돌아오는
# **오버슛**도 공짜로 생긴다(팔로스루의 문법).
#
# ── ★애니메이션 문법(오너가 두 번 기각한 것을 피하는 규칙) ──
#   · 예비(안티시페이션)는 **짧게**. 2~4장. 길면 "야구 투구 폼"으로 읽힌다.
#   · 예비에서 손을 **가슴 뒤로 감지 않는다**. 투구 판정자(probe_moves_read)는
#     "손이 어깨 위 +0.05H **그리고** 가슴 뒤 +0.20H" 인 장을 센다. 위로는 들되
#     뒤로는 안 간다 = 세로 베기의 본질만 남긴다.
#   · 임팩트는 **한 구간에 몰아서**. 칼끝이 그 구간에서만 HOT_ON 을 넘어야
#     스윙 번호가 하나로 뜬다.
#   · 스윙 사이에는 칼끝을 HOT_OFF 아래로 **두 장 이상** 떨어뜨린다(정지 타격감도
#     같이 번다). 안 그러면 히스테리시스 때문에 세 타가 한 번호로 묶인다.
#   · 몸통이 팔을 리드하고(ty/hy 가 먼저 돌고) 손목이 마지막에 스냅한다.
HAND = [c.strip() for c in os.environ.get("HAND", "").split(",") if c.strip()]
HAND_WRIST = float(os.environ.get("HAND_WRIST", "26"))   # 지금은 안 쓴다(잔각 0)
# 웅크림 회전 부호. 무릎이 앞으로 나가는 쪽이 +1 이다(1차 실행에서 무릎 전방
# 변위를 찍어 확정했다. 반대로 두면 무릎이 뒤로 꺾인다).
CR_SGN = -1.0
DBG_REACH = os.environ.get("DBG_REACH", "0") == "1"

W_UP = Vector((0, 0, 1))
W_FWD = facing(DREST).to_3d()
W_FWD.z = 0
W_FWD.normalize()
W_LFT = W_UP.cross(W_FWD).normalized()
# 가슴 회전이 실릴 뼈(골반·다리는 뺀다). 팔은 몸통을 따라 통째로 돈다.
UPPER = [b for b in ORDER if b not in (
    PELVIS, "Bip001 L Thigh", "Bip001 R Thigh", "Bip001 L Calf", "Bip001 R Calf",
    "Bip001 L Foot", "Bip001 R Foot", "Bip001 L Toe0", "Bip001 R Toe0",
    "Bip001 L Toe0Nub", "Bip001 R Toe0Nub")]
THIGHS = [b for b in ("Bip001 L Thigh", "Bip001 R Thigh") if b in PARENT]
CALFS = [b for b in ("Bip001 L Calf", "Bip001 R Calf") if b in PARENT]
THIGH_LEN = (DREST["Bip001 L Calf"][1] - DREST["Bip001 L Thigh"][1]).length
LEG_LEN = (THIGH_LEN
           + (DREST["Bip001 L Foot"][1] - DREST["Bip001 L Calf"][1]).length)

# ── 수제 키프레임 대본 ──
# (프레임, {채널: 값}).  f0 은 자동으로 바탕값이라 여기 안 적는다.
# "base" = 그 채널의 바탕값(Idle 첫 프레임)으로 돌아간다.
# 지켜야 하는 산수와 16차 재작의 이유는 아래 표 머리에 다 적었다.
HAND_SPEC = {
    # ══════════════════════════════════════════════════════════════════════
    # ★★★16차 전면 재작 (2026-08-13. 오너 "베는건 여전히 이상해. 간단하잖아
    #   세로로베고 가로로베고 각자 하나씩")
    #   15차 대본은 **정지 실루엣과 월드 궤적으로만** 짜여 있었고 그 자로는 전부
    #   통과했는데 오너는 또 기각했다. 16차에 처음으로 **화면(게임 카메라)**과
    #   **시간축**을 재서 세 가지가 나왔다:
    #     ① X 는 임팩트~팔로스루 여덟 장(f10~f17) 동안 **칼이 화면에서 접혀 있었다**
    #        (화면 칼 길이 83px -> 5px). 칼 방향이 카메라 시선축과 나란해지는 자리다.
    #     ② 예비가 **등속 드리프트**라 그 자체가 느린 스윙 하나로 읽혔다
    #        (Z f02~f07 · C f02~f08 이 화면속도 일정).
    #     ③ **골반 수평 이동이 세 클립 전부 0.000m** — 손 속도/칼끝 속도 0.19~0.26,
    #        즉 칼끝 속도의 3/4 이 손목·팔뚝 회전이었다("팔만 흔드는 마네킹").
    #   그래서 대본을 아래 다섯 규칙으로 다시 짰다.
    #
    #   [R1] ★★카메라 금지구역 — 칼이 "앞아래 45~60도"를 겨누면 화면에서 접힌다.
    #        게임 카메라는 pitch 49.3도라 시선축이 (위 -0.758, 앞 +0.653) 이다.
    #        칼 방향이 그 근처면 83px -> 5px. **그 자리엔 머물지 말고 한 장에 지나가라.**
    #        더 근본적으로: 이 카메라에서 월드 1m 위 = 화면 43px 위 · 1m 앞 = 화면 47px
    #        **위**다. 즉 "아래로 + 앞으로"는 화면에서 서로 상쇄된다 —
    #        **순수 시상면 내려베기는 이 카메라에서 원리적으로 안 읽힌다.**
    #        그래서 X 는 옆으로 45도쯤 눕힌 **가파른 내려찍기**로 짰다(업계의 카메라 치트).
    #        C 와는 화면 기울기로 확실히 갈린다(X 는 세로 우세, C 는 가로 전용).
    #   [R2] 예비는 3장 안에 감고 **정점에서 한 장 멈춘 뒤 한 장 되눌린다**(압축).
    #        등속으로 흐르면 그게 곧 또 하나의 스윙이다.
    #   [R3] 임팩트는 **한 장에 최대 간격**. 그 앞뒤로 가속·감속이 있어야 한다.
    #   [R4] 팔로스루는 오버슛 한 장 + 정착 한 장. 죽은 장은 두 장을 넘기지 않는다.
    #   [R5] 회수는 칼각 12도/장 아래로(HOT_ON 15.8 을 안 넘긴다). 대신 **손과 무게**가
    #        움직여 실루엣이 계속 바뀐다 — 그래야 "멈춰 섰다"로 안 보인다.
    #   [R6] ★신설 채널 wf/ws 로 **골반을 실제로 옮긴다**(게임 cm). 임팩트에서
    #        앞으로 12~18cm. 이게 없으면 아무리 잘 짜도 팔만 흔드는 그림이다.
    # ══════════════════════════════════════════════════════════════════════
    #
    # ── 아래 산수는 15차에서 그대로 물린 것들이다. 지킬 것 ──
    #   1) **칼끝 속도는 게임이 HOT_ON 15.8 로 자른다.** 한 프레임에 칼끝이
    #      15.8/(30*재생속도) m 넘게 움직이면 그 장은 hot 이다 = 예비·회수에서도
    #      스윙 번호가 발급되고 피해가 들어간다.
    #        Attack ts1.35 -> 0.390 m/장   Heavy ts1.15 -> 0.458   Wide ts1.20 -> 0.439
    #      칼 1.66m 기준 각도로는 약 13도/장(ts1.15~1.35)이 문턱이다.
    #   2) 스윙 사이는 **HOT_OFF(게임 9.36) 아래로 두 장 이상**. 그리고 스윙 사이
    #      간격이 게임 0.22초(enemy.js SWING_GAP)보다 커야 다른 타로 센다
    #      = 클립 프레임으로 Attack 9장, Heavy/Wide 8장 이상.
    #   3) **손을 올리지 말고 칼을 세워라.** 칼끝 높이 = 손 높이 + 1.66*sin(bel).
    #      팔을 어깨 위로 올리면 왼손이 자루에서 떨어진다(reach > 1.0).
    #   4) 바닥 여유 = 손 높이 - 1.66*sin(|bel|). 손이 1.5m 라도 |bel| 60도가 한계다.
    #      ★이 한계와 [R1] 금지구역(45~60도)이 겹친다 — 그래서 세로베기의 마무리는
    #        방위(baz)를 줘서 빠져나와야 한다. 순수 세로로는 갈 곳이 없다.
    #   5) 몸통 회전(ty·hy)도 칼끝을 옮긴다. 칼끝은 가슴축에서 1.7m 라 ty 1도가 3cm.
    #      baz + ty + hy 를 **합쳐서** 1)의 산수에 넣어라.

    # ── Z 기본 3연타 (46장 = 1.500초 클립 = 게임 1.111초 @ts1.35) ──
    # 대각 내려베기 -> 되받아 횡베기 -> 가파른 세로 마무리.
    # ★타격 셋을 f9~f12 · f22~f25 · f36~f39 에 두었다(사이 10·11장 = 게임
    #   0.247·0.272초 > SWING_GAP 0.22). 15차의 죽은 장(f13~15·f18~20·f30~31)이
    #   있던 자리는 **되받아 감기**로 채웠다 — 1타의 오버슛이 그대로 2타의 예비가 되고,
    #   2타의 오버슛이 3타의 예비가 된다(그 사이 칼끝은 5~9 m/s = HOT_OFF 아래).
    "Attack": (46, [
        (1, dict(bel=+39, baz=-4,  bend=+4,  ty=-2,  tp=-1, hy=-1, cr=2, lg=-3,  wf=-2, ws=-1)),
        (2, dict(bel=+44, baz=-8,  bend=+9,  ty=-4,  tp=-3, hy=-2, cr=4, lg=-6,  wf=-4, ws=-2)),
        (3, dict(bel=+50, baz=-13, bend=+14, ty=-7,  tp=-5, hy=-3, cr=6, lg=-9,  wf=-6, ws=-3)),
        (4, dict(bel=+55, baz=-17, bend=+18, ty=-9,  tp=-6, hy=-4, cr=7, lg=-11, wf=-7, ws=-4)),
        (5, dict(bel=+59, baz=-19, bend=+21, ty=-10, tp=-7, hy=-5, cr=8, lg=-12, wf=-8, ws=-4)),
        (6, dict(bel=+60, baz=-19, bend=+22, ty=-10, tp=-7, hy=-5, cr=8, lg=-12, wf=-8, ws=-4)),
        (7, dict(bel=+59, baz=-18, bend=+21, ty=-9,  tp=-6, hy=-4, cr=9, lg=-11, wf=-7, ws=-3)),
        (8, dict(bel=+51, baz=-13, bend=+18, ty=-4,  tp=-1, hy=-2, cr=11, lg=-3, wf=-3, ws=-1)),
        (9, dict(bel=+32, baz=-2,  arl=+26, bend=+15, ty=+3, tp=+5, hy=+2, cr=13, lg=+8, wf=+4, ws=+2)),
        (10, dict(bel=+4,  baz=+14, arl=+56, bend=+11, ty=+9, tp=+10, hy=+4, cr=16, lg=+19, wf=+9, ws=+4)),
        (11, dict(bel=-22, baz=+32, arl=+86, bend=+7, ty=+14, tp=+15, hy=+7, cr=18, lg=+28, wf=+13, ws=+6)),
        (12, dict(bel=-38, baz=+46, arl=+108, bend=+5, ty=+18, tp=+18, hy=+9, cr=20, lg=+33, wf=+16, ws=+8)),
        (13, dict(bel=-35, baz=+43, arl=+104, bend=+7, ty=+17, tp=+17, hy=+8, cr=19, lg=+31, wf=+15, ws=+8)),
        (15, dict(bel=-14, baz=+52, arl=+82, bend=+12, ty=+21, tp=+11, hy=+10, cr=16, lg=+25, wf=+12, ws=+9)),
        (17, dict(bel=+14, baz=+54, arl=+54, bend=+26, ty=+23, tp=+4, hy=+11, cr=13, lg=+19, wf=+9, ws=+9)),
        (19, dict(bel=+38, baz=+52, arl=+26, bend=+32, ty=+22, tp=-2, hy=+10, cr=11, lg=+15, wf=+7, ws=+8)),
        (20, dict(bel=+46, baz=+50, arl=+20, bend=+34, ty=+21, tp=-4, hy=+10, cr=10, lg=+13, wf=+6, ws=+7)),
        (21, dict(bel=+42, baz=+45, arl=+22, bend=+32, ty=+16, tp=-1, hy=+7, cr=11, lg=+8, wf=+7, ws=+5)),
        (22, dict(bel=+26, baz=+26, arl=+22, bend=+26, ty=+7, tp=+3, hy=+3, cr=12, lg=0, wf=+7, ws=+3)),
        (23, dict(bel=+12, baz=-8,  arl=+14, bend=+12, ty=-7, tp=+5, hy=-3, cr=12, lg=-8, wf=+7, ws=-1)),
        (24, dict(bel=+7,  baz=-32, arl=+6, bend=+11, ty=-18, tp=+4, hy=-9, cr=11, lg=-15, wf=+6, ws=-5)),
        (25, dict(bel=+5,  baz=-48, arl=+2, bend=+11, ty=-24, tp=+4, hy=-12, cr=10, lg=-20, wf=+5, ws=-8)),
        (26, dict(bel=+5,  baz=-44, arl=+2, bend=+12, ty=-23, tp=+3, hy=-11, cr=9, lg=-20, wf=+4, ws=-7)),
        (27, dict(bel=+6,  baz=-41, arl=+4, bend=+13, ty=-21, tp=+3, hy=-10, cr=8, lg=-18, wf=+3, ws=-6)),
        (29, dict(bel=+20, baz=-30, bend=+24, ty=-17, tp=+1, hy=-8, cr=8, lg=-15, wf=+1, ws=-5)),
        (31, dict(bel=+36, baz=-26, bend=+30, ty=-14, tp=-3, hy=-6, cr=8, lg=-13, wf=-1, ws=-4)),
        (33, dict(bel=+50, baz=-20, bend=+34, ty=-10, tp=-6, hy=-4, cr=8, lg=-11, wf=-4, ws=-3)),
        (34, dict(bel=+58, baz=-16, bend=+36, ty=-8, tp=-8, hy=-3, cr=9, lg=-10, wf=-5, ws=-3)),
        (35, dict(bel=+54, baz=-14, bend=+34, ty=-6, tp=-6, hy=-2, cr=10, lg=-8, wf=-4, ws=-2)),
        (36, dict(bel=+48, baz=-12, arl=+20, bend=+32, ty=-3, tp=-2, hy=-1, cr=12, lg=-2, wf=-1, ws=-2)),
        (37, dict(bel=+20, baz=-2,  arl=+48, bend=+15, ty=+3, tp=+7, hy=+2, cr=15, lg=+12, wf=+6, ws=+1)),
        (38, dict(bel=-13, baz=+23, arl=+86, bend=+9, ty=+11, tp=+14, hy=+6, cr=18, lg=+26, wf=+13, ws=+5)),
        (39, dict(bel=-42, baz=+42, arl=+114, bend=+5, ty=+16, tp=+20, hy=+8, cr=22, lg=+34, wf=+17, ws=+7)),
        (40, dict(bel=-39, baz=+40, arl=+110, bend=+7, ty=+15, tp=+19, hy=+8, cr=21, lg=+32, wf=+16, ws=+7)),
        (41, dict(bel=-23, baz=+35, arl=+88, bend=+11, ty=+12, tp=+14, hy=+6, cr=16, lg=+25, wf=+12, ws=+6)),
        (42, dict(bel=-11, baz=+29, arl=+68, bend=+13, ty=+9, tp=+10, hy=+5, cr=12, lg=+19, wf=+9, ws=+5)),
        (43, dict(bel=-1,  baz=+24, arl=+50, bend=+12, ty=+7, tp=+7, hy=+4, cr=9, lg=+14, wf=+7, ws=+4)),
        (44, dict(bel=+6,  baz=+19, arl=+34, bend=+10, ty=+5, tp=+5, hy=+2, cr=6, lg=+10, wf=+5, ws=+3)),
        (45, dict(bel=+12, baz=+15, arl=+22, bend=+8, ty=+3, tp=+4, hy=+1, cr=4, lg=+7, wf=+4, ws=+2)),
    ]),

    # ── X 수면참 = 가파른 내려찍기 (22장 = 0.700초 클립 = 게임 0.609초 @ts1.15) ──
    # ★15차는 방위(baz)를 -8~+4 에 묶어 "월드 세로성 7.55"를 냈는데, 바로 그것 때문에
    #   칼이 카메라 시선축에 갇혀 여덟 장 동안 화면에서 사라졌다([R1]).
    #   16차는 위(bel +76)에서 **앞아래·왼쪽(baz +38)** 으로 떨어뜨린다. 화면에서는
    #   가파른 대각 = "위에서 아래로"로 읽히고, 칼은 한 장도 접히지 않는다.
    # ★C 와의 구분: X 는 bel 이 +76 -> -42 로 118도 내려오고 baz 는 55도만 돈다.
    #   C 는 bel 을 +9~+32 에 묶고 baz 가 126도 돈다. 화면 기울기가 완전히 갈린다.
    "Heavy": (22, [
        (1, dict(bel=+41, baz=-2,  bend=+4,  ty=-2, tp=-2,  hy=-1, cr=2,  lg=-3,  wf=-2, ws=-1)),
        (2, dict(bel=+48, baz=-5,  bend=+9,  ty=-3, tp=-4,  hy=-2, cr=4,  lg=-6,  wf=-4, ws=-2)),
        (3, dict(bel=+56, baz=-9,  bend=+15, ty=-5, tp=-7,  hy=-3, cr=6,  lg=-9,  wf=-6, ws=-3)),
        (4, dict(bel=+58, baz=-11, bend=+25, ty=-6, tp=-8,  hy=-4, cr=8,  lg=-11, wf=-7, ws=-3)),
        (5, dict(bel=+66, baz=-14, bend=+29, ty=-8, tp=-10, hy=-5, cr=9,  lg=-14, wf=-9, ws=-4)),
        (6, dict(bel=+67, baz=-14, bend=+29, ty=-8, tp=-10, hy=-5, cr=9,  lg=-14, wf=-9, ws=-4)),
        (7, dict(bel=+61, baz=-11, bend=+26, ty=-5, tp=-7,  hy=-3, cr=11, lg=-10, wf=-6, ws=-2)),
        (8, dict(bel=+54, baz=-8,  bend=+25, ty=-2, tp=-2,  hy=-1, cr=12, lg=-2,  wf=-2, ws=-1)),
        (9, dict(bel=+28, baz=-1,  arl=+30, bend=+16, ty=+2, tp=+6,  hy=+1, cr=14, lg=+10, wf=+5, ws=+2)),
        (10, dict(bel=-8,  baz=+15, arl=+66, bend=+10, ty=+8, tp=+13, hy=+4, cr=17, lg=+21, wf=+11, ws=+5)),
        (11, dict(bel=-30, baz=+30, arl=+90, bend=+6, ty=+11, tp=+17, hy=+6, cr=19, lg=+29, wf=+14, ws=+7)),
        (12, dict(bel=-41, baz=+40, arl=+104, bend=+4, ty=+14, tp=+20, hy=+7, cr=22, lg=+34, wf=+17, ws=+8)),
        (13, dict(bel=-38, baz=+38, arl=+100, bend=+6, ty=+13, tp=+19, hy=+7, cr=21, lg=+33, wf=+16, ws=+8)),
        (14, dict(bel=-24, baz=+34, arl=+84, bend=+10, ty=+11, tp=+15, hy=+6, cr=16, lg=+25, wf=+12, ws=+7)),
        (15, dict(bel=-12, baz=+29, arl=+66, bend=+12, ty=+9, tp=+11, hy=+5, cr=12, lg=+19, wf=+9, ws=+6)),
        (16, dict(bel=-3,  baz=+25, arl=+50, bend=+12, ty=+7, tp=+8, hy=+4, cr=9, lg=+15, wf=+7, ws=+5)),
        (17, dict(bel=+3,  baz=+21, arl=+37, bend=+11, ty=+6, tp=+6, hy=+3, cr=7, lg=+12, wf=+6, ws=+4)),
        (18, dict(bel=+7,  baz=+18, arl=+27, bend=+9, ty=+5, tp=+5, hy=+2, cr=5, lg=+9, wf=+5, ws=+3)),
        (19, dict(bel=+10, baz=+15, arl=+19, bend=+7, ty=+4, tp=+4, hy=+2, cr=4, lg=+7, wf=+4, ws=+2)),
        (20, dict(bel=+12, baz=+13, arl=+13, bend=+5, ty=+3, tp=+3, hy=+1, cr=3, lg=+5, wf=+3, ws=+1)),
        (21, dict(bel=+14, baz=+11, arl=+9,  bend=+4, ty=+2, tp=+2, hy=+1, cr=2, lg=+3, wf=+2, ws=+1)),
    ]),

    # ── C 횡일섬 = 가로 베기 (22장 = 0.700초 클립 = 게임 0.583초 @ts1.20) ──
    # ★15차의 두 가지를 고쳤다: ①예비 일곱 장이 등속이라 그 자체가 스윙으로 읽혔다
    #   -> 다섯 장에 가속하며 감고 한 장 멈춘 뒤 한 장 되누른다. ②쓸고 나서 여섯 장
    #   붙박이 -> 오버슛 한 장 + 정착 한 장 + 감속하는 회수(손·무게가 계속 움직인다).
    # ★bel 을 +9~+32 에 묶어 칼이 바닥과 나란히 눕지 않게 하고(15차 계약 유지),
    #   대신 baz 를 -56 -> +70 으로 126도 돌린다 = 화면 가로 이동 최대.
    "Wide": (22, [
        (1, dict(bel=+32, baz=-5,  bend=+3,  ty=-2,  hy=-1,  cr=1,  lg=-2,  ws=-1,  wf=-1)),
        (2, dict(bel=+27, baz=-13, arl=+8, bend=+7,  ty=-7,  hy=-4, cr=4,  lg=-6,  ws=-3,  wf=-2)),
        (3, dict(bel=+23, baz=-22, arl=+16, bend=+15, ty=-12, hy=-7, cr=6,  lg=-11, ws=-5,  wf=-3)),
        (4, dict(bel=+20, baz=-30, arl=+21, bend=+17, ty=-16, hy=-9, cr=8, lg=-15, ws=-7,  wf=-4)),
        (5, dict(bel=+18, baz=-36, arl=+24, bend=+19, ty=-19, hy=-11, cr=9, lg=-17, ws=-8, wf=-5)),
        (6, dict(bel=+17, baz=-38, arl=+25, bend=+20, ty=-20, hy=-11, cr=10, lg=-18, ws=-9, wf=-5)),
        (7, dict(bel=+18, baz=-36, arl=+24, bend=+19, ty=-18, hy=-10, cr=11, lg=-16, ws=-8, wf=-4)),
        (8, dict(bel=+17, baz=-28, arl=+23, bend=+18, ty=-11, hy=-6,  cr=12, lg=-9,  ws=-5, wf=-1)),
        (9, dict(bel=+14, baz=-12, arl=+26, bend=+12, ty=0,   hy=+1,  cr=13, lg=+3,  ws=0,  wf=+3)),
        (10, dict(bel=+11, baz=+16, arl=+30, bend=+10, ty=+14, hy=+8,  cr=14, lg=+15, ws=+5, wf=+8)),
        (11, dict(bel=+10, baz=+38, arl=+32, bend=+9,  ty=+23, hy=+13, cr=13, lg=+23, ws=+9, wf=+11)),
        (12, dict(bel=+9,  baz=+62, arl=+31, bend=+10, ty=+31, hy=+18, cr=12, lg=+29, ws=+11, wf=+12)),
        (13, dict(bel=+10, baz=+78, arl=+30, bend=+12, ty=+36, hy=+21, cr=11, lg=+32, ws=+12, wf=+12)),
        (14, dict(bel=+11, baz=+75, arl=+29, bend=+13, ty=+34, hy=+20, cr=10, lg=+30, ws=+11, wf=+11)),
        (15, dict(bel=+13, baz=+70, arl=+27, bend=+13, ty=+31, hy=+18, cr=9,  lg=+28, ws=+10, wf=+10)),
        (16, dict(bel=+15, baz=+63, arl=+24, bend=+13, ty=+28, hy=+16, cr=8,  lg=+25, ws=+9, wf=+9)),
        (17, dict(bel=+18, baz=+55, arl=+21, bend=+12, ty=+24, hy=+14, cr=6,  lg=+22, ws=+8, wf=+8)),
        (18, dict(bel=+20, baz=+47, arl=+18, bend=+11, ty=+20, hy=+12, cr=5,  lg=+18, ws=+6, wf=+6)),
        (19, dict(bel=+23, baz=+39, arl=+15, bend=+10, ty=+16, hy=+9,  cr=4,  lg=+15, ws=+5, wf=+5)),
        (20, dict(bel=+25, baz=+32, arl=+12, bend=+8,  ty=+13, hy=+7,  cr=3,  lg=+12, ws=+4, wf=+4)),
        (21, dict(bel=+27, baz=+26, arl=+9,  bend=+6,  ty=+10, hy=+6,  cr=2,  lg=+9,  ws=+3, wf=+3)),
    ]),
}

HAND_CH = ("bel", "baz", "arl", "bend", "ty", "tp", "tr", "hy", "cr", "lg",
           "wf", "ws", "gw", "wrl")
# ★25차 신설 채널 wrl: 오른손목의 **칼축 둘레** 롤(도). 칼끝·칼 선분이 불변이라
#   궤적·판정·FX 에 한 톨도 안 가고 **날면 방향만** 돈다(날 정렬 계약용).
#   GRIP_V25=0 이면 키 자체가 안 들어가 24차 판 그대로다.

# ══════════════════════════════════════════════════════════════════════════
# ★★18차 X 신작 — **검도 정면베기(마키리오로시)** (2026-08-13, 오너 지시)
#   오너: "칼 베는모션도 검도나 사무라이처럼 위에서 아래로 딱 써는 모션 새로 해줘봐
#          기존꺼 그냥 잊고. 맘에 안들면 다시 돌릴거임"
#   `KENDO_X=0` 이면 위 16차 Heavy 대본이 그대로 굽힌다(md5 fc74fee3 재현 창구).
#
# ── 이 카메라에서 "위에서 아래로"를 어떻게 만드나 (16차가 잰 기하 위에서 짠다) ──
#   [G1] 화면 세로 감도: 월드 1m **위** = 41.5px 위 · 1m **앞(카메라 반대)** = 49.5px
#        **위**. 즉 칼끝이 앞으로 나가면 화면에서는 **올라간다.** 15차가 "순수 세로"로
#        짜고도 화면에서 안 읽힌 이유가 이것이다(내려베기의 아래와 앞이 서로 상쇄).
#        -> 그러니 **칼끝의 앞 이동을 아끼는 것**이 곧 화면 낙차다. 팔을 앞으로 뻗어
#           마무리하지 말고 **몸이 가라앉으며 손을 몸 가까이 내리는** 검도 마무리로 짠다.
#   [G2] 화면 가로는 **좌우 성분만** 만든다(1m = 64.8px). 그래서 시상면(좌우 0)에서
#        휘두르면 화면 궤적은 **정확히 수직**이다. 15차의 진짜 문제는 세로성이 아니라
#        ①칼이 접혀 안 보인 것 ②낙차가 작았던 것이었다.
#        -> 16차는 방위를 55도 돌려 둘을 다 샀지만 그만큼 대각이 됐다(실측 화면
#           Δx -113 / Δy +147 = 세로/가로 1.30). **이번 계약은 그 비를 올리는 것이다.**
#   [G3] ★접힘 금지구역: 칼 **월드** 방향이 시선축 (위 -0.758, 앞 +0.653) 근처면
#        화면 길이가 83px -> 5px 로 접힌다. 그 자리는 "앞아래 25~75도" 다.
#        빠져나오는 유일한 출구가 **좌우 성분**이라, 칼이 깊이 내려가는 마지막
#        두세 장에서만 방위를 준다(그때는 이미 임팩트가 끝나 화면 낙차를 다 벌었다).
#        ★월드 방위 = baz + ty(가슴 돌림)다. **둘을 합쳐서** 계산해야 한다.
#   [G4] 바닥: 칼끝 높이 = 손 높이 - 1.66 x sin(|월드 고도|). 손 1.3m 면 |고도| 45도가
#        한계다. 그리고 월드 고도 = bel - tp(가슴 숙임) 이므로 tp 도 예산에 넣는다.
#
# ── 검도 문법(오너 지시문 그대로) ──
#   ①정중선으로 크게 들어 올림(f1~f6) ②한 박자 정지(f7~f8 = 게임 0.058초)
#   ③일직선 낙하(f9~f12. 손목 스냅 + 골반 가라앉음) ④하단 잔심(f13~f15)
#   ⑤회수(f16~f21. 감속형이라 리본이 두 번째 참격으로 안 읽힌다)
#   임팩트(칼이 수평선을 지나는 순간) = f10~f11 사이 = 입력 후 **0.29~0.32초**
#   (지시 0.25~0.35 안. 클립 22장 = 0.700초 = 게임 **0.609초** @ts1.15, 지시 0.6~0.7 안)
#
# ── 지켜야 하는 산수(15·16차에서 물린 것) ──
#   · 칼끝 15.8 m/s(HOT_ON) = ts1.15 에서 **0.458 m/장** = 칼 1.66m 로 약 **16도/장**.
#     예비는 그 아래(최대 11도/장), 낙하는 위(23~46도/장), 회수는 아래(≤12도/장).
#   · 칼끝 앞뒤 F > 0 이어야 벤다(main.js 정면 부채꼴 게이트).
#   · Catmull-Rom 은 키가 등차수열이면 직선이 된다 = 기계적 와이퍼. 값에 스페이싱을 넣는다.
HAND_SPEC_KENDO = (22, [
    # ── ①들어 올림. Δbel 9.5·11·10·7·4·1 = 앞은 빠르고 정점에서 눌러 앉힌다 ──
    #    baz 를 0 근처에 두는 것이 "정중선"이다. 몸은 뒤에 실었다가(wf-) 앞으로 넘긴다.
    #    ★정점 bel 을 +78 로 둔 이유(카메라): 칼을 **정확히 수직**으로 세우면 화면
    #      길이가 65% 로 줄고 칼끝도 낮아진다(시선축이 위-앞 대각이라 그렇다).
    #      14도 앞으로 눕히면 82% 로 서고 칼끝이 화면에서 18px 더 높다 = 낙차가 커진다.
    (1,  dict(bel=+45, baz=+1,  bend=+9,  ty=-1, tp=-2,  hy=-1, cr=3,  lg=-4,  wf=-3,  ws=-1)),
    (2,  dict(bel=+56, baz=0,   bend=+16, ty=-2, tp=-4,  hy=-2, cr=6,  lg=-8,  wf=-6,  ws=-2)),
    (3,  dict(bel=+66, baz=-1,  bend=+23, ty=-3, tp=-6,  hy=-3, cr=9,  lg=-12, wf=-9,  ws=-3)),
    (4,  dict(bel=+73, baz=-2,  bend=+29, ty=-4, tp=-8,  hy=-4, cr=11, lg=-15, wf=-11, ws=-4)),
    (5,  dict(bel=+77, baz=-3,  bend=+33, ty=-5, tp=-9,  hy=-5, cr=12, lg=-17, wf=-13, ws=-4)),
    (6,  dict(bel=+78, baz=-4,  bend=+35, ty=-6, tp=-10, hy=-5, cr=13, lg=-18, wf=-14, ws=-5)),
    # ── ②한 박자 정지(f7) + 한 장 되누름(f8. 칼끝이 2도 더 눕고 몸이 먼저 출발한다) ──
    (7,  dict(bel=+78, baz=-4,  bend=+35, ty=-6, tp=-10, hy=-5, cr=13, lg=-18, wf=-14, ws=-5)),
    (8,  dict(bel=+80, baz=-4,  bend=+34, ty=-5, tp=-9,  hy=-4, cr=14, lg=-15, wf=-11, ws=-4)),
    # ── ③낙하. 28 -> 44 -> 28 -> 13 도/장. 임팩트(수평선 통과)는 f10~f11 사이다 ──
    #    ★baz 는 f10 까지 0 근처(=화면에서 곧게 내리꽂힌다). 방위는 칼이 깊이 내려가는
    #      **마지막 두 장에서만** 준다 — 그 자리가 [G3] 접힘 금지구역이기 때문이다.
    (9,  dict(bel=+52, baz=-4,  arl=+32, bend=+26, ty=-2, tp=-1, hy=-1, cr=16, lg=-6, wf=-3, ws=-2)),
    (10, dict(bel=+8,  baz=+1,  arl=+40, bend=+16, ty=+2, tp=+4, hy=+1, cr=20, lg=+10, wf=+7, ws=+1)),
    (11, dict(bel=-20, baz=+20, arl=+48, bend=+9,  ty=+4, tp=+7, hy=+3, cr=24, lg=+22, wf=+15, ws=+3)),
    (12, dict(bel=-30, baz=+34, arl=+56, bend=+9,  ty=+6, tp=+9, hy=+5, cr=25, lg=+29, wf=+19, ws=+5)),
    # ── ④잔심(하단 멈춤). 세 장 동안 칼은 멈추고 **몸만** 가라앉았다 펴진다 ──
    (13, dict(bel=-29, baz=+38, arl=+54, bend=+10, ty=+6, tp=+9, hy=+5, cr=24, lg=+28, wf=+18, ws=+5)),
    (14, dict(bel=-28, baz=+39, arl=+52, bend=+11, ty=+6, tp=+8, hy=+5, cr=22, lg=+26, wf=+16, ws=+5)),
    (15, dict(bel=-26, baz=+38, arl=+50, bend=+11, ty=+6, tp=+8, hy=+5, cr=20, lg=+23, wf=+14, ws=+5)),
    # ── ⑤회수. 13·11·9·7·5·3 도/장 = **감속형**(등속이면 그게 또 하나의 스윙이다) ──
    (16, dict(bel=-15, baz=+35, arl=+46, bend=+10, ty=+6, tp=+7, hy=+4, cr=17, lg=+20, wf=+12, ws=+4)),
    (17, dict(bel=-4,  baz=+34, arl=+48, bend=+11, ty=+6, tp=+6, hy=+4, cr=12, lg=+16, wf=+10, ws=+4)),
    (18, dict(bel=+5,  baz=+28, arl=+40, bend=+11, ty=+5, tp=+5, hy=+3, cr=9,  lg=+13, wf=+8, ws=+3)),
    (19, dict(bel=+12, baz=+22, arl=+34, bend=+10, ty=+4, tp=+4, hy=+3, cr=7,  lg=+10, wf=+6, ws=+3)),
    (20, dict(bel=+17, baz=+16, arl=+30, bend=+8,  ty=+3, tp=+3, hy=+2, cr=5,  lg=+7,  wf=+5, ws=+2)),
    (21, dict(bel=+20, baz=+10, arl=+28, bend=+6,  ty=+2, tp=+2, hy=+1, cr=3,  lg=+5,  wf=+3, ws=+1)),
])
KENDO_X = os.environ.get("KENDO_X", "1") == "1"
if KENDO_X:
    HAND_SPEC["Heavy"] = HAND_SPEC_KENDO      # ★16차 대본은 위에 그대로 남아 있다

# ══════════════════════════════════════════════════════════════════════════
# ★★23차 베기 3종 재작 (2026-08-24, 오너 "베는 모션 너무 어색해. 다 점검해서 다시")
#   `MOVES_V23=0` 이면 위 18차 판(검도 X + 16차 Z·C)이 그대로 굽힌다(md5 fa19aa9d 경로).
#
# ── 진단(18차 커밋본 실측. after_2_s24.log 프레임표 + 브라우저 실측이 근거) ──
#   ①【회수가 두 번째 획으로 읽힌다】 리본(FX)은 칼끝 14.8 m/s(FAST_REF 45,
#     swordFast 0.38)부터 그려지는데, C 회수 f17~19 가 16.3~17.7 m/s(=hot 재점화,
#     스윙3), C 장전 f1~3 도 16.7~22.7(스윙1), Z 회수 f41~44 도 16.9~19.3(스윙4)이었다.
#     한 입력에 획이 2~3개 = "와이퍼". §7-19 의 "C 회수 리본 잔류"의 정체가 이것.
#   ②【임팩트 뒤 서는 자세(홀드)가 없다】 Z 연결부 f13~20·f26~35 가 화면 9~27px/장으로
#     8~10장 연속 이동(등속 구간 f30~34·f41~45), X 회수 f16~21 이 19~25px/장 6장.
#     임팩트(75~111px/장) 대비 겨우 4~5배라 정지-폭발 대비가 죽는다.
#   ③【Z 1타와 3타가 같은 호를 되긋는다】 화면에서 1타 우→좌 대각(f8 x+52→f12 x-87),
#     3타도 우→좌 대각(f36 x+51→f39 x-81), 2타만 좌→우 = 와이퍼 왕복 그 자체.
#   ④【왼손 파지 이탈】 Z f23~35 에서 왼손이 자루에서 최대 1.13주먹 뜬 채 13장
#     (~320ms, 뻗음 1.18), C f2 0.96주먹. 두손검 파지가 화면에서 깨진다.
#   ⑤【X 임팩트가 Z 보다 약하다】 X 낙하 화면속도 최고 71px/장 < Z 평타 111px/장.
#     일격기의 화면 낙차가 평타만 못했다.
#
# ── 23차 규칙(16차 R1~R6 위에 셋을 더한다) ──
#   [R7] 회수·재장전은 칼끝 12 m/s 아래(리본 문턱 14.8 의 8할). 회수는 짧은 경로로,
#        몸(ty)과 칼(baz)을 **한 방향으로 같이 돌리지 않는다**(속도가 더해진다).
#        끝자세가 바탕에서 20~30도 남아도 된다 — Idle 크로스페이드가 느리게 메운다.
#   [R8] 임팩트 오버슛 뒤 **정착 1장 + 홀드 2~3장**(칼끝 화면 ≤8px/장, 몸만 미세하게
#        는다). 이 홀드가 곧 읽히는 실루엣이다.
#   [R9] 3연타는 세 획의 문법이 달라야 한다: 1타 대각 내려베기(우→좌) → 2타 가슴
#        높이 수평 되베기(좌→우) → 3타 정중선 오버헤드 내려찍기(수직 우세, 오른쪽
#        탈출). 같은 호 왕복 금지.
#   산수는 위 표 머리의 것: hot 문턱 = Attack 13.5도/장 · Heavy 15.9 · Wide 15.2,
#   리본 문턱 = 12.6 / 14.9 / 14.3 도/장. ty 1도 = 3cm 도 같이 센다.
HAND_SPEC_V23 = {
    # ── Z 3연타 (46장 유지. 타격 슬롯도 16차와 같은 자리 = f9~12 / f22~25 / f36~39,
    #    스윙 사이 10·11장 = 게임 0.247·0.272초 > SWING_GAP 0.22 유지) ──
    "Attack": (46, [
        # 장전(우상단으로 감음. 16차 검증치 재사용) + 정점 유지 f6 + 되누름 f7
        (1, dict(bel=+40, baz=-4,  bend=+5,  ty=-2,  tp=-1, hy=-1, cr=2,  lg=-3,  wf=-2, ws=-1)),
        (2, dict(bel=+46, baz=-9,  bend=+10, ty=-4,  tp=-3, hy=-2, cr=4,  lg=-6,  wf=-4, ws=-2)),
        (3, dict(bel=+52, baz=-14, bend=+15, ty=-7,  tp=-5, hy=-3, cr=6,  lg=-9,  wf=-6, ws=-3)),
        (4, dict(bel=+58, baz=-18, bend=+19, ty=-9,  tp=-6, hy=-4, cr=7,  lg=-11, wf=-7, ws=-4)),
        (5, dict(bel=+62, baz=-21, bend=+22, ty=-11, tp=-7, hy=-5, cr=8,  lg=-12, wf=-8, ws=-4)),
        (6, dict(bel=+63, baz=-21, bend=+23, ty=-11, tp=-7, hy=-5, cr=8,  lg=-12, wf=-8, ws=-4)),
        (7, dict(bel=+64, baz=-22, bend=+22, ty=-10, tp=-6, hy=-4, cr=9,  lg=-11, wf=-7, ws=-3)),
        (8, dict(bel=+50, baz=-15, arl=+30, bend=+18, ty=-5, tp=-2, hy=-2, cr=11, lg=-4, wf=-3, ws=-1)),
        # 1타 hot f9~12: 대각 내려베기(화면 우→좌)
        (9,  dict(bel=+28, baz=-2,  arl=+40, bend=+14, ty=+2,  tp=+5,  hy=+2, cr=13, lg=+8,  wf=+5,  ws=+2)),
        (10, dict(bel=-2,  baz=+16, arl=+62, bend=+10, ty=+9,  tp=+11, hy=+5, cr=16, lg=+20, wf=+10, ws=+4)),
        (11, dict(bel=-26, baz=+34, arl=+88, bend=+6,  ty=+15, tp=+16, hy=+7, cr=19, lg=+29, wf=+14, ws=+6)),
        (12, dict(bel=-38, baz=+44, arl=+104, bend=+5, ty=+18, tp=+18, hy=+9, cr=20, lg=+33, wf=+17, ws=+8)),
        # 오버슛 f13 + 정착 f14 + ★홀드 f15 (칼은 서고 몸만 가라앉는다. [R8])
        # (v23a 실측: 홀드 4장 + 느린 재장전 시작 = 죽은 장 6장 — 홀드를 3장으로 줄이고
        #  재장전을 5장 균등 ~10도/장으로 당겼다)
        (13, dict(bel=-35, baz=+46, arl=+100, bend=+7, ty=+18, tp=+17, hy=+9, cr=19, lg=+31, wf=+16, ws=+8)),
        (14, dict(bel=-32, baz=+45, arl=+96, bend=+8,  ty=+17, tp=+16, hy=+8, cr=17, lg=+28, wf=+14, ws=+7)),
        (15, dict(bel=-31, baz=+45, arl=+94, bend=+8,  ty=+16, tp=+14, hy=+8, cr=15, lg=+26, wf=+12, ws=+7)),
        # 재장전 f16~20 (왼어깨로. ~10도/장 = 리본 아래 [R7]) + 되누름 f21
        (16, dict(bel=-24, baz=+46, arl=+86, bend=+10, ty=+17, tp=+11, hy=+8,  cr=14, lg=+24, wf=+11, ws=+7)),
        (17, dict(bel=-14, baz=+49, arl=+74, bend=+13, ty=+18, tp=+8,  hy=+9,  cr=14, lg=+22, wf=+10, ws=+7)),
        (18, dict(bel=-4,  baz=+52, arl=+62, bend=+16, ty=+20, tp=+4,  hy=+9,  cr=13, lg=+21, wf=+9,  ws=+7)),
        (19, dict(bel=+6,  baz=+55, arl=+52, bend=+18, ty=+21, tp=+2,  hy=+10, cr=13, lg=+19, wf=+8,  ws=+8)),
        (20, dict(bel=+13, baz=+57, arl=+46, bend=+20, ty=+22, tp=0,   hy=+10, cr=12, lg=+18, wf=+8,  ws=+8)),
        (21, dict(bel=+16, baz=+59, arl=+43, bend=+21, ty=+23, tp=-1,  hy=+11, cr=12, lg=+17, wf=+7,  ws=+8)),
        # 2타 hot f22~25: 가슴 높이 수평 되베기(화면 좌→우. bel 을 +9~15 에 묶는다)
        (22, dict(bel=+15, baz=+38, arl=+40, bend=+18, ty=+14, tp=+2, hy=+7,  cr=13, lg=+10, wf=+9,  ws=+5)),
        (23, dict(bel=+11, baz=+4,  arl=+36, bend=+13, ty=0,   tp=+4, hy=0,   cr=14, lg=0,   wf=+12, ws=0)),
        (24, dict(bel=+9,  baz=-28, arl=+30, bend=+11, ty=-13, tp=+4, hy=-7,  cr=13, lg=-10, wf=+15, ws=-5)),
        (25, dict(bel=+10, baz=-42, arl=+28, bend=+11, ty=-19, tp=+3, hy=-10, cr=12, lg=-15, wf=+16, ws=-8)),
        # 오버슛 f26 + ★홀드 f27 ([R8]. ④왼손: bel 을 세우고 arl 을 올려 뻗음 완화)
        (26, dict(bel=+11, baz=-44, arl=+28, bend=+12, ty=-20, tp=+2, hy=-10, cr=11, lg=-16, wf=+15, ws=-8)),
        (27, dict(bel=+12, baz=-43, arl=+30, bend=+13, ty=-19, tp=+1, hy=-10, cr=9,  lg=-15, wf=+13, ws=-7)),
        # 3타 장전 f28~34: 정중선으로 들어 올림
        # (v23a 실측: 6장 12도/장 + 몸 = hot 재점화(유령 스윙3, 게임 0.741~0.815초에
        #  발급돼 스윙2와 0.124초 간격 = SWING_GAP 안 = 진짜 3타가 같은 번호로 묶여
        #  피해가 안 들어간다). 7장 ~8도/장으로 늦추고 정점을 +67 로 낮췄다)
        # (v23b 실측: f31 한 장이 아직 hot 을 스쳐 유령 스윙3이 남았다 — 스윙2 끝과
        #  0.148초·진짜 3타와 0.124초 간격이라 SWING_GAP 이 셋을 한 번호로 묶어
        #  **3타 피해가 사라진다**. 장전을 다시 15% 늦추고 정점을 +62 로 낮췄다)
        # (v23c 실측: 유령은 사라졌는데 f29~34 가 등속 6장으로 찍혔다 — 예비 등속은
        #  16차가 기각당한 문법이라, 느리게 출발해 중간이 빠르고 정점에서 눌러 앉는
        #  5·6·7·8·8·6·4·3 스페이싱으로 다듬었다. 리본 문턱(12.6도/장) 아래는 유지)
        (28, dict(bel=+17, baz=-41, arl=+30, bend=+15, ty=-18, tp=0,  hy=-9, cr=9,  lg=-14, wf=+11, ws=-7)),
        (29, dict(bel=+22, baz=-39, arl=+31, bend=+17, ty=-17, tp=-1, hy=-8, cr=10, lg=-13, wf=+9,  ws=-6)),
        (30, dict(bel=+28, baz=-36, arl=+31, bend=+19, ty=-15, tp=-3, hy=-7, cr=10, lg=-12, wf=+7,  ws=-5)),
        (31, dict(bel=+35, baz=-32, arl=+32, bend=+22, ty=-13, tp=-4, hy=-6, cr=11, lg=-11, wf=+4,  ws=-4)),
        (32, dict(bel=+43, baz=-28, arl=+32, bend=+25, ty=-11, tp=-6, hy=-5, cr=11, lg=-9,  wf=+1,  ws=-3)),
        (33, dict(bel=+51, baz=-23, arl=+33, bend=+27, ty=-9,  tp=-7, hy=-4, cr=12, lg=-8,  wf=-2,  ws=-2)),
        (34, dict(bel=+57, baz=-18, arl=+33, bend=+28, ty=-7,  tp=-8, hy=-3, cr=12, lg=-7,  wf=-4,  ws=-1)),
        (35, dict(bel=+62, baz=-13, arl=+34, bend=+29, ty=-5,  tp=-7, hy=-2, cr=13, lg=-5,  wf=-4,  ws=-1)),
        # 3타 hot f36~39: 정중선 오버헤드 내려찍기([R9]. 마지막 두 장 오른쪽 탈출을
        # v23a 의 -28도에서 -38도로 키웠다 — 접힘 2장(f39~40, 44px)이 그 자리였다)
        (36, dict(bel=+38, baz=-11, arl=+40, bend=+24, ty=-3, tp=-3,  hy=-1, cr=16, lg=0,   wf=+2,  ws=0)),
        (37, dict(bel=+4,  baz=-14, arl=+48, bend=+14, ty=0,  tp=+4,  hy=+1, cr=20, lg=+10, wf=+10, ws=+1)),
        (38, dict(bel=-20, baz=-26, arl=+56, bend=+9,  ty=+2, tp=+8,  hy=+3, cr=24, lg=+18, wf=+16, ws=+2)),
        (39, dict(bel=-28, baz=-38, arl=+60, bend=+8,  ty=+3, tp=+10, hy=+4, cr=25, lg=+22, wf=+19, ws=+3)),
        # 정착 f40 + 감속 회수 f41~45 (11→10→9→8→6도/장 단조 감속 = 등속·리본·hot 없음.
        # 18차 스윙4 유령(회수 f41~44 hot)의 제거가 이 구간의 계약이다 [R7])
        (40, dict(bel=-27, baz=-39, arl=+58, bend=+9,  ty=+3, tp=+9,  hy=+4, cr=23, lg=+20, wf=+17, ws=+3)),
        (41, dict(bel=-17, baz=-36, arl=+53, bend=+10, ty=+3, tp=+7,  hy=+3, cr=19, lg=+17, wf=+14, ws=+3)),
        (42, dict(bel=-8,  baz=-32, arl=+48, bend=+10, ty=+2, tp=+5,  hy=+3, cr=15, lg=+14, wf=+11, ws=+2)),
        (43, dict(bel=0,   baz=-27, arl=+43, bend=+10, ty=+2, tp=+4,  hy=+2, cr=11, lg=+10, wf=+8,  ws=+2)),
        (44, dict(bel=+7,  baz=-22, arl=+38, bend=+9,  ty=+1, tp=+3,  hy=+1, cr=8,  lg=+7,  wf=+5,  ws=+1)),
        (45, dict(bel=+12, baz=-18, arl=+34, bend=+8,  ty=+1, tp=+2,  hy=+1, cr=5,  lg=+4,  wf=+3,  ws=+1)),
    ]),

    # ── X 수면참 (검도 문법 유지 = 오너 18차 지시 존중. 고친 것 = ⑤낙하 낙차 확대
    #    (f9~12 간격 28→50도/장, 전진 wf +21)와 [R7] 회수 단축·감속, 잔심 4장) ──
    "Heavy": (22, [
        (1,  dict(bel=+45, baz=+1,  bend=+9,  ty=-1, tp=-2,  hy=-1, cr=3,  lg=-4,  wf=-3,  ws=-1)),
        (2,  dict(bel=+56, baz=0,   bend=+16, ty=-2, tp=-4,  hy=-2, cr=6,  lg=-8,  wf=-6,  ws=-2)),
        (3,  dict(bel=+66, baz=-1,  bend=+23, ty=-3, tp=-6,  hy=-3, cr=9,  lg=-12, wf=-9,  ws=-3)),
        (4,  dict(bel=+73, baz=-2,  bend=+29, ty=-4, tp=-8,  hy=-4, cr=11, lg=-15, wf=-11, ws=-4)),
        (5,  dict(bel=+77, baz=-3,  bend=+33, ty=-5, tp=-9,  hy=-5, cr=12, lg=-17, wf=-13, ws=-4)),
        (6,  dict(bel=+78, baz=-4,  bend=+35, ty=-6, tp=-10, hy=-5, cr=13, lg=-18, wf=-14, ws=-5)),
        (7,  dict(bel=+78, baz=-4,  bend=+35, ty=-6, tp=-10, hy=-5, cr=13, lg=-18, wf=-14, ws=-5)),
        (8,  dict(bel=+80, baz=-4,  bend=+34, ty=-5, tp=-9,  hy=-4, cr=14, lg=-15, wf=-11, ws=-4)),
        # 낙하 f9~12: 방위 탈출을 16차보다 세게(f11 +26 / f12 +37) — v23a 의 +22/+34 는
        # bel 이 더 깊어진 만큼 접힘(38px, 36%)을 만들었다. bel 도 -24/-35 로 완화([G3])
        # (v23b 실측: 화면속도 최고 65px 로 오히려 줄었다(목표 = Z 임팩트 105px 급).
        #  f10 을 더 깊이 떨어뜨리고(bel -8) 방위를 한 장 일찍 줘 접힘 구간을 빠르게
        #  통과시킨다. 왼손은 v23a(arl 52~56)가 v23b(48~52)보다 좋았다 — 잔심 arl 복원)
        # (v23c 실측: f11 이 45% 문턱에 딱 걸렸다(48px) — 방위를 한 장 일찍·더 크게 줘
        #  접힘 구간을 벗어나게 한다)
        (9,  dict(bel=+50, baz=-2,  arl=+34, bend=+26, ty=-2, tp=0,   hy=-1, cr=16, lg=-6,  wf=-2,  ws=-2)),
        (10, dict(bel=-10, baz=+12, arl=+42, bend=+14, ty=+2, tp=+5,  hy=+1, cr=22, lg=+14, wf=+10, ws=+1)),
        (11, dict(bel=-26, baz=+33, arl=+50, bend=+10, ty=+4, tp=+8,  hy=+3, cr=26, lg=+26, wf=+18, ws=+3)),
        (12, dict(bel=-35, baz=+38, arl=+54, bend=+9,  ty=+6, tp=+10, hy=+5, cr=26, lg=+30, wf=+21, ws=+5)),
        # 잔심 f13~16 (4장. 칼은 서고 몸만 가라앉았다 편다 [R8])
        (13, dict(bel=-34, baz=+38, arl=+54, bend=+10, ty=+6, tp=+9, hy=+5, cr=24, lg=+28, wf=+19, ws=+5)),
        (14, dict(bel=-34, baz=+38, arl=+53, bend=+11, ty=+6, tp=+9, hy=+5, cr=22, lg=+26, wf=+17, ws=+5)),
        (15, dict(bel=-33, baz=+38, arl=+52, bend=+11, ty=+6, tp=+8, hy=+5, cr=20, lg=+24, wf=+15, ws=+5)),
        (16, dict(bel=-33, baz=+38, arl=+52, bend=+11, ty=+6, tp=+8, hy=+4, cr=18, lg=+22, wf=+13, ws=+4)),
        # 회수 f17~21: 11·10·9·8·6도/장 단조 감속(v23a 는 첫 두 장이 hot 을 스쳤다),
        # 몸 가까이 짧은 경로. 끝자세 잔여각은 Idle 크로스페이드가 메운다([R7])
        (17, dict(bel=-22, baz=+36, arl=+48, bend=+11, ty=+5, tp=+7, hy=+4, cr=15, lg=+18, wf=+11, ws=+4)),
        (18, dict(bel=-12, baz=+32, arl=+44, bend=+11, ty=+5, tp=+5, hy=+3, cr=12, lg=+14, wf=+9,  ws=+3)),
        (19, dict(bel=-3,  baz=+27, arl=+40, bend=+10, ty=+4, tp=+4, hy=+2, cr=9,  lg=+11, wf=+7,  ws=+2)),
        (20, dict(bel=+5,  baz=+23, arl=+35, bend=+8,  ty=+3, tp=+3, hy=+2, cr=6,  lg=+8,  wf=+5,  ws=+2)),
        (21, dict(bel=+11, baz=+19, arl=+31, bend=+6,  ty=+2, tp=+2, hy=+1, cr=4,  lg=+5,  wf=+3,  ws=+1)),
    ]),

    # ── C 횡일섬 (타격 f9~13 은 16차 검증치 유지. 고친 것 = ①장전 감속(f1~3 이 hot
    #    이던 것을 ≤10도/장으로), [R8] 홀드 f14~16 신설, [R7] 회수 감속·몸은 나중에) ──
    "Wide": (22, [
        # 장전 f1~7: v23a 실측 f3~5 가 아직 hot(스윙1 유령)이었다 — 되감기 총량을 줄이고
        # (baz -38 → -30, ty -20 → -15) 한 장당 칼 6~7도·몸 3도 아래로 눌렀다([R7])
        (1, dict(bel=+34, baz=0,   arl=+8,  bend=+2,  ty=-1,  hy=-1,  cr=1,  lg=-2,  ws=-1, wf=-1)),
        (2, dict(bel=+32, baz=-6,  arl=+12, bend=+5,  ty=-3,  hy=-2,  cr=3,  lg=-5,  ws=-2, wf=-2)),
        (3, dict(bel=+29, baz=-12, arl=+15, bend=+9,  ty=-6,  hy=-4,  cr=5,  lg=-8,  ws=-3, wf=-3)),
        (4, dict(bel=+26, baz=-18, arl=+18, bend=+13, ty=-9,  hy=-6,  cr=7,  lg=-11, ws=-5, wf=-4)),
        (5, dict(bel=+23, baz=-24, arl=+21, bend=+16, ty=-12, hy=-8,  cr=8,  lg=-14, ws=-7, wf=-4)),
        (6, dict(bel=+21, baz=-28, arl=+23, bend=+18, ty=-14, hy=-9,  cr=9,  lg=-16, ws=-8, wf=-5)),
        (7, dict(bel=+20, baz=-30, arl=+24, bend=+19, ty=-15, hy=-10, cr=10, lg=-17, ws=-8, wf=-5)),
        (8, dict(bel=+18, baz=-24, arl=+24, bend=+18, ty=-10, hy=-6,  cr=12, lg=-10, ws=-5, wf=-1)),
        # 타격 f9~13 (16차 실측 화면 100px/장 = 유지. 끝 방위만 +79→+74 로 눌러 왼손 뻗음 완화)
        (9,  dict(bel=+15, baz=-10, arl=+26, bend=+12, ty=+1,  hy=+1,  cr=13, lg=+3,  ws=0,   wf=+3)),
        (10, dict(bel=+12, baz=+18, arl=+30, bend=+10, ty=+14, hy=+8,  cr=14, lg=+15, ws=+5,  wf=+8)),
        (11, dict(bel=+10, baz=+42, arl=+32, bend=+9,  ty=+24, hy=+13, cr=13, lg=+23, ws=+9,  wf=+11)),
        (12, dict(bel=+9,  baz=+62, arl=+36, bend=+10, ty=+30, hy=+17, cr=12, lg=+28, ws=+11, wf=+12)),
        (13, dict(bel=+10, baz=+74, arl=+36, bend=+12, ty=+34, hy=+20, cr=11, lg=+31, ws=+12, wf=+12)),
        # 정착 f14 + ★홀드 f15~16 ([R8]. arl +36 은 왼손 뻗음 완화 실험 — 실측으로 판정)
        (14, dict(bel=+11, baz=+73, arl=+34, bend=+13, ty=+34, hy=+20, cr=10, lg=+30, ws=+11, wf=+11)),
        (15, dict(bel=+12, baz=+72, arl=+30, bend=+13, ty=+33, hy=+20, cr=9,  lg=+29, ws=+11, wf=+10)),
        (16, dict(bel=+13, baz=+71, arl=+29, bend=+13, ty=+32, hy=+19, cr=8,  lg=+28, ws=+10, wf=+10)),
        # 회수 f17~21: 칼 먼저(baz 6~7도/장) 몸 나중(ty 는 3~4도/장). 리본 문턱 아래([R7].
        # v23a 는 f20 에 hot 한 장이 남았었다 — 꼬리를 더 눌렀다)
        (17, dict(bel=+15, baz=+65, arl=+27, bend=+13, ty=+31, hy=+18, cr=7, lg=+26, ws=+9,  wf=+9)),
        (18, dict(bel=+17, baz=+58, arl=+25, bend=+12, ty=+29, hy=+17, cr=6, lg=+24, ws=+9,  wf=+8)),
        (19, dict(bel=+20, baz=+51, arl=+22, bend=+11, ty=+26, hy=+15, cr=5, lg=+21, ws=+8,  wf=+7)),
        (20, dict(bel=+23, baz=+44, arl=+19, bend=+9,  ty=+22, hy=+13, cr=4, lg=+17, ws=+6,  wf=+5)),
        (21, dict(bel=+26, baz=+38, arl=+16, bend=+7,  ty=+18, hy=+11, cr=3, lg=+14, ws=+5,  wf=+4)),
    ]),
}
# ★롤백 스위치는 이 한 줄이다. 0 이면 위 표가 그대로 이겨서 18차 판이 나온다.
MOVES_V23 = os.environ.get("MOVES_V23", "1") == "1"
if MOVES_V23:
    for _k in ("Attack", "Heavy", "Wide"):
        HAND_SPEC[_k] = HAND_SPEC_V23[_k]

# ══════════════════════════════════════════════════════════════════════════
# ★★24차 베기 3종 — **대검 물리 언어로 재작** (2026-08-24, 오너 "베는 모션 여전히
#   이상해. 검이 지금 크잖아. 검을 들고 행하는 모든 건 논리적으로, 물리적으로도")
#   `MOVES_V24=0` 이면 23차 판이 그대로 굽힌다(MOVES_V23 기본 1 이므로).
#
# ── 칼 제원(probe_sword_dims 실측, 게임 1.75m 환산)이 이번 재작의 출발점이다 ──
#   전장 1.827m(캐릭터 키 1.75 보다 길다) · 손목→칼끝 1.602m · 날 폭 최대 0.42m.
#   실물 츠바이헨더(1.6~1.8m)가 2~3.5kg — 이 비주얼은 폭 42cm 슬래브라 강판 근사
#   (1.6m x 평균폭 0.25m x 실두께 1cm, 강철 7850)로 **~31kg 급**으로 읽힌다.
#   번역 기준: "사람이 어떻게든 두 손으로 다루는 최대치의 슬래브".
#
# ── 23차 커밋본(md5 9c5d4f7e)의 잔여 결함 — repro_2_s24.log 프레임표가 근거 ──
#   ①【장전·회수가 리본 문턱을 파닥거린다】 리본은 칼끝 14.8 m/s 부터 그려지는데
#     Z 장전 f2~3 = 14.8~15.3 / X 장전 f2 = 15.6 / C 회수 f20 = 15.1 m/s.
#     감아올리는 팔이 임팩트급 속도로 움직인다 = 무게의 부재이자 유령 획의 씨앗.
#   ②【임팩트 뒤 관성이 없다】 Z 1타 v: 56.6 → 43.3 → 19.5 → **3.7**(f13).
#     20kg 슬래브가 최고속에서 두 장 만에 멎는 건 물리 거짓말이다. 오버슛이
#     사실상 0이라 "휘두른다"가 아니라 "가져다 댄다"로 읽힌다.
#   ③【몸이 팔과 동시에 돈다】 hy(골반)와 ty(가슴)가 같은 프레임에 같은 비율로
#     움직인다(hy ≈ ty/2 고정). 골반이 어깨를 끌지 않으면 대검이 못 나간다.
#   ④【3타 장전 등속】 f30~33 화면 등속 4장(16차가 기각당한 문법의 잔재).
#
# ── 24차 규칙(23차 R7~R9 위에 셋을 더한다) ──
#   [R10] ★가속 서사 — 장전·회수는 "느린 출발(2~5도/장) → 중간(7~11) → 정점에서
#         눌러앉음(2~4)". 어느 프레임도 리본 문턱(12.6/14.9/14.3 도/장)을 안 넘는다.
#         무거운 것은 **출발이 느리다.** 이 곡선이 [R7]의 리본 파닥임도 뿌리째 없앤다.
#   [R11] ★관성 팔로스루 — 임팩트 최고속 뒤 2~3장을 5~10도/장으로 **감쇠**시키며
#         원호를 계속 긋는다(23차는 1장 만에 3도로 죽었다). 그 다음에 정착·홀드.
#         칼끝 화면속도 곡선이 "완만한 상승 → 뾰족한 피크 → 긴 감쇠"를 그린다.
#   [R12] ★골반 선행 — 감기에서 hy 가 ty 보다 1~2장 먼저 정점에 닿고, 스윙 전환에서
#         hy 가 먼저 반대로 돈다. 임팩트의 몸통 회전 총량(hy+ty)은 23차와 같게
#         유지하되 **골반 몫을 키운다**(23차 hy≈ty/2 → 24차 hy≈0.7ty). 무게는
#         골반이 끌고 어깨가 따라가는 순서로만 옮겨진다.
#   지키는 것: 타격 슬롯(Z f8~12/f22~25/f36~39 · X f9~12 · C f8~13)과 스윙 사이
#   간격(SWING_GAP 0.22 초과), 히트스톱 궤합, 커밋 시간(재생속도·클립 길이 불변),
#   [G3] 접힘 금지구역, 바닥여유 ≥ 0, 캡슐 상한(임팩트 구간이 1.5m 아래를 지난다).
HAND_SPEC_V24 = {
    # ── Z 3연타 (46장 유지. 타격 슬롯·스윙 간격 23차와 동일) ──
    "Attack": (46, [
        # 장전 f1~7: [R10] Δbel 2.5,4,4,6,6,4,2 (23차 4.5,6,6,6,4,1,1 = f1~3 이
        # 리본 문턱 위. v24a 실측: 중간을 6으로 눌러야 Catmull 접선 과속(f3 15.5)이
        # 12 아래로 내려온다). [R12] hy 가 f4 에 -8 로 먼저 앉고 ty 는 f6 에 -10.
        (1, dict(bel=+38, baz=-2,  bend=+5,  ty=-1,  tp=-1, hy=-3, cr=2,  lg=-3,  wf=-3,  ws=-1)),
        (2, dict(bel=+42, baz=-6,  bend=+10, ty=-3,  tp=-2, hy=-5, cr=4,  lg=-6,  wf=-5,  ws=-2)),
        (3, dict(bel=+46, baz=-11, bend=+15, ty=-5,  tp=-4, hy=-7, cr=6,  lg=-9,  wf=-7,  ws=-3)),
        (4, dict(bel=+52, baz=-16, bend=+19, ty=-7,  tp=-5, hy=-8, cr=7,  lg=-11, wf=-9,  ws=-4)),
        (5, dict(bel=+58, baz=-20, bend=+22, ty=-9,  tp=-6, hy=-8, cr=8,  lg=-12, wf=-10, ws=-4)),
        (6, dict(bel=+62, baz=-22, bend=+23, ty=-10, tp=-7, hy=-8, cr=8,  lg=-12, wf=-10, ws=-4)),
        (7, dict(bel=+64, baz=-22, bend=+22, ty=-10, tp=-6, hy=-7, cr=9,  lg=-11, wf=-9,  ws=-3)),
        # 릴리즈 f8: [R12] 골반이 먼저 풀린다(hy -1, ty 는 아직 -5)
        (8, dict(bel=+51, baz=-15, arl=+30, bend=+18, ty=-5, tp=-2, hy=-1, cr=11, lg=-4, wf=-3, ws=-1)),
        # 1타 hot f8~12: 대각 내려베기(23차 검증 궤적 유지. hy 몫만 키움 —
        # 임팩트 몸통 총량 hy+ty 는 23차 27도 = 24차 28도로 같다)
        (9,  dict(bel=+28, baz=-2,  arl=+40, bend=+14, ty=+1,  tp=+5,  hy=+4,  cr=13, lg=+8,  wf=+5,  ws=+2)),
        (10, dict(bel=-2,  baz=+16, arl=+62, bend=+10, ty=+7,  tp=+11, hy=+7,  cr=16, lg=+20, wf=+10, ws=+4)),
        (11, dict(bel=-26, baz=+34, arl=+88, bend=+6,  ty=+13, tp=+16, hy=+10, cr=19, lg=+29, wf=+14, ws=+6)),
        (12, dict(bel=-38, baz=+44, arl=+104, bend=+5, ty=+16, tp=+18, hy=+12, cr=20, lg=+33, wf=+17, ws=+8)),
        # [R11] 관성 팔로스루 f13(Δ~5도/장) → 감쇠 f14(Δ3) → 정착 f15(Δ3).
        # 23차는 f13 에서 v 3.7 로 즉사했다. 무게는 목표를 지나쳐 관성으로 더 간다.
        (13, dict(bel=-42, baz=+47, arl=+102, bend=+6, ty=+17, tp=+18, hy=+12, cr=21, lg=+32, wf=+17, ws=+8)),
        (14, dict(bel=-40, baz=+47, arl=+99,  bend=+7, ty=+17, tp=+16, hy=+12, cr=20, lg=+30, wf=+16, ws=+8)),
        (15, dict(bel=-37, baz=+46, arl=+96,  bend=+8, ty=+16, tp=+15, hy=+11, cr=18, lg=+28, wf=+14, ws=+7)),
        # 재장전 f16~21: [R10] Δbel 8,9,5,9,9,9 — 끌어올리다 **왼어깨 위에서 한 번
        # 걸치고(f18 되걸침 비트) 되누르는** 두 박자. 균등 램프는 등속 플래그에,
        # Δ11 이상은 hot(15.8) 코앞이라 유령 스윙(1·2타 사이를 SWING_GAP 이 한
        # 번호로 묶는 v23b 결함)에 걸린다 — 상한 Δ9(v ≈11.5). 진입점 ATK_STEP_T
        # 0.55(f16.5)의 자세 연속성이 여기 걸려 있다.
        # [R12] f21 에서 골반이 먼저 되돈다(hy +9, ty 는 +23)
        (16, dict(bel=-30, baz=+47, arl=+88, bend=+10, ty=+17, tp=+12, hy=+10, cr=16, lg=+25, wf=+12, ws=+7)),
        (17, dict(bel=-21, baz=+50, arl=+76, bend=+13, ty=+18, tp=+9,  hy=+10, cr=15, lg=+23, wf=+11, ws=+7)),
        (18, dict(bel=-16, baz=+52, arl=+70, bend=+15, ty=+19, tp=+7,  hy=+10, cr=14, lg=+21, wf=+10, ws=+7)),
        (19, dict(bel=-7,  baz=+55, arl=+58, bend=+17, ty=+21, tp=+3,  hy=+11, cr=13, lg=+19, wf=+9,  ws=+8)),
        (20, dict(bel=+2,  baz=+57, arl=+49, bend=+19, ty=+22, tp=+1,  hy=+11, cr=12, lg=+18, wf=+8,  ws=+8)),
        (21, dict(bel=+11, baz=+59, arl=+43, bend=+21, ty=+23, tp=-1,  hy=+9,  cr=12, lg=+17, wf=+8,  ws=+8)),
        # 2타 hot f22~25: 수평 되베기(23차 궤적 유지. [R12] 골반 선행 — hy 가 ty 보다
        # 한 장 먼저 반대로 넘어간다: f22 에서 이미 +4, f23 에 -3)
        (22, dict(bel=+15, baz=+38, arl=+40, bend=+18, ty=+15, tp=+2, hy=+4,  cr=13, lg=+10, wf=+9,  ws=+5)),
        (23, dict(bel=+11, baz=+4,  arl=+36, bend=+13, ty=+1,  tp=+4, hy=-3,  cr=14, lg=0,   wf=+12, ws=0)),
        (24, dict(bel=+9,  baz=-28, arl=+30, bend=+11, ty=-12, tp=+4, hy=-9,  cr=13, lg=-10, wf=+15, ws=-5)),
        (25, dict(bel=+10, baz=-42, arl=+28, bend=+11, ty=-18, tp=+3, hy=-11, cr=12, lg=-15, wf=+16, ws=-8)),
        # [R11] 팔로스루 f26(Δ~4) + 정착·홀드 f27
        (26, dict(bel=+11, baz=-46, arl=+28, bend=+12, ty=-19, tp=+2, hy=-11, cr=11, lg=-16, wf=+15, ws=-8)),
        (27, dict(bel=+12, baz=-45, arl=+30, bend=+13, ty=-19, tp=+1, hy=-11, cr=9,  lg=-15, wf=+13, ws=-7)),
        # 3타 장전 f28~35: **두 번에 나눠 끌어올린다**(재걸침 f31·f34). 20kg 급을
        # 한 호흡에 못 올리는 사람의 문법이자, 균등 램프의 화면 등속 플래그와
        # 리본 문턱을 동시에 피하는 유일한 스페이싱이다:
        #   v24a 실측: 정점 62 는 8장 안에 리본 아래로 못 올린다(f31 16.1 m/s hot
        #   = 유령 스윙3 — 2타·진짜 3타와 0.148·0.124초 간격 = SWING_GAP 이 셋을
        #   묶어 3타 피해 소멸, v23b 재발). v24b: 정점 55 + Δ8 도 f31 15.1(리본 위).
        #   → 정점 +52 로 낮추고 Δbel 3,5,7,3,7,7,3,5 (최대 v ~13.5 < 리본 14.8).
        # [R12] hy 는 ty 보다 두 장 먼저 0 에 닿는다
        (28, dict(bel=+15, baz=-43, arl=+30, bend=+15, ty=-18, tp=0,  hy=-10, cr=9,  lg=-14, wf=+11, ws=-7)),
        (29, dict(bel=+20, baz=-41, arl=+31, bend=+17, ty=-17, tp=-1, hy=-8,  cr=10, lg=-13, wf=+9,  ws=-6)),
        (30, dict(bel=+27, baz=-38, arl=+31, bend=+19, ty=-15, tp=-3, hy=-7,  cr=10, lg=-12, wf=+7,  ws=-5)),
        (31, dict(bel=+30, baz=-36, arl=+32, bend=+20, ty=-14, tp=-4, hy=-5,  cr=11, lg=-11, wf=+5,  ws=-4)),
        (32, dict(bel=+37, baz=-32, arl=+32, bend=+23, ty=-12, tp=-5, hy=-4,  cr=11, lg=-10, wf=+2,  ws=-3)),
        (33, dict(bel=+44, baz=-27, arl=+33, bend=+25, ty=-10, tp=-6, hy=-3,  cr=12, lg=-8,  wf=-1,  ws=-2)),
        (34, dict(bel=+47, baz=-23, arl=+33, bend=+26, ty=-8,  tp=-7, hy=-2,  cr=12, lg=-7,  wf=-3,  ws=-1)),
        (35, dict(bel=+52, baz=-17, arl=+34, bend=+28, ty=-5,  tp=-7, hy=-1,  cr=13, lg=-5,  wf=-4,  ws=-1)),
        # 3타 hot f36~39: 정중선 오버헤드(23차 궤적 유지)
        (36, dict(bel=+38, baz=-11, arl=+40, bend=+24, ty=-3, tp=-3,  hy=0,   cr=16, lg=0,   wf=+2,  ws=0)),
        (37, dict(bel=+4,  baz=-14, arl=+48, bend=+14, ty=0,  tp=+4,  hy=+2,  cr=20, lg=+10, wf=+10, ws=+1)),
        (38, dict(bel=-20, baz=-26, arl=+56, bend=+9,  ty=+2, tp=+8,  hy=+4,  cr=24, lg=+18, wf=+16, ws=+2)),
        (39, dict(bel=-28, baz=-38, arl=+60, bend=+8,  ty=+3, tp=+10, hy=+5,  cr=25, lg=+22, wf=+19, ws=+3)),
        # [R11] 팔로스루 f40(Δ~4. 바닥여유 f39 +0.111 이라 bel 은 -30 까지만) →
        # 회수 f41~45: [R10] Δbel 4,8,10,9,5 — 무겁게 출발해 중간에 끌어올리고
        # 잦아드는 꼬리(v24a 의 9,9,9,9 균등은 화면 등속 플래그 f42~45).
        (40, dict(bel=-30, baz=-41, arl=+59, bend=+9,  ty=+3, tp=+9,  hy=+5, cr=24, lg=+21, wf=+18, ws=+3)),
        (41, dict(bel=-26, baz=-40, arl=+56, bend=+10, ty=+3, tp=+8,  hy=+4, cr=21, lg=+18, wf=+15, ws=+3)),
        (42, dict(bel=-18, baz=-37, arl=+51, bend=+10, ty=+2, tp=+6,  hy=+3, cr=17, lg=+15, wf=+12, ws=+2)),
        (43, dict(bel=-8,  baz=-32, arl=+45, bend=+10, ty=+2, tp=+4,  hy=+2, cr=12, lg=+11, wf=+9,  ws=+2)),
        (44, dict(bel=+1,  baz=-26, arl=+39, bend=+9,  ty=+1, tp=+3,  hy=+1, cr=8,  lg=+7,  wf=+6,  ws=+1)),
        (45, dict(bel=+6,  baz=-21, arl=+35, bend=+8,  ty=+1, tp=+2,  hy=+1, cr=5,  lg=+4,  wf=+4,  ws=+1)),
    ]),

    # ── X 수면참 (검도 문법·낙하 궤적은 23차 유지 = 18차 오너 지시 존중.
    #    고친 것 = [R10] 들어올림 가속 서사(f2 가 리본 15.6 을 넘던 것),
    #    [R12] 골반 선발, 잔심의 무게 받기(tp 되눌림) ──
    "Heavy": (22, [
        # 들어올림 f1~6: Δbel 4.5,7,9,9,8,5 (23차 9.5,11,10,7,4,1 — 첫 두 장이
        # 임팩트급). 20kg 을 머리 위로 — **출발이 제일 느리다.**
        (1,  dict(bel=+40, baz=+1,  bend=+6,  ty=-1, tp=-2,  hy=-2, cr=3,  lg=-4,  wf=-4,  ws=-1)),
        (2,  dict(bel=+47, baz=0,   bend=+12, ty=-2, tp=-4,  hy=-3, cr=6,  lg=-8,  wf=-7,  ws=-2)),
        (3,  dict(bel=+56, baz=-1,  bend=+19, ty=-3, tp=-6,  hy=-4, cr=9,  lg=-12, wf=-10, ws=-3)),
        (4,  dict(bel=+65, baz=-2,  bend=+26, ty=-4, tp=-8,  hy=-5, cr=11, lg=-15, wf=-12, ws=-4)),
        (5,  dict(bel=+73, baz=-3,  bend=+32, ty=-5, tp=-9,  hy=-5, cr=12, lg=-17, wf=-13, ws=-4)),
        (6,  dict(bel=+78, baz=-4,  bend=+35, ty=-6, tp=-10, hy=-5, cr=13, lg=-18, wf=-14, ws=-5)),
        # 한 박자 정지 f7 + 되누름 f8 ([R12] 골반이 먼저 출발한다: hy -3, ty 는 -5)
        (7,  dict(bel=+78, baz=-4,  bend=+35, ty=-6, tp=-10, hy=-5, cr=13, lg=-18, wf=-14, ws=-5)),
        (8,  dict(bel=+80, baz=-4,  bend=+34, ty=-5, tp=-9,  hy=-3, cr=14, lg=-15, wf=-11, ws=-4)),
        # 낙하 f9~12: 23차 궤적 그대로(방위 탈출·접힘 해결이 세 판에 걸친 실측 산물).
        # [R12] hy 만 한 장 앞: 23차 -1,+1,+3,+5 → +1,+3,+5,+6 (ty 는 -2,+2,+4,+5)
        (9,  dict(bel=+50, baz=-2,  arl=+34, bend=+26, ty=-2, tp=0,   hy=+1, cr=16, lg=-6,  wf=-2,  ws=-2)),
        (10, dict(bel=-10, baz=+12, arl=+42, bend=+14, ty=+2, tp=+5,  hy=+3, cr=22, lg=+14, wf=+10, ws=+1)),
        (11, dict(bel=-26, baz=+33, arl=+50, bend=+10, ty=+4, tp=+8,  hy=+5, cr=26, lg=+26, wf=+18, ws=+3)),
        (12, dict(bel=-35, baz=+38, arl=+54, bend=+9,  ty=+5, tp=+10, hy=+6, cr=26, lg=+30, wf=+21, ws=+5)),
        # 잔심 f13~16: 칼은 서고(바닥여유 f12 -0.018 이라 더 못 내린다 — 오버슛은
        # 땅이 받았다) 몸이 무게를 **받아낸다**: cr 25→19 로 천천히 일어나고
        # tp 가 10→8 로 되눌린다(23차보다 회복이 느리다 = 무게)
        (13, dict(bel=-34, baz=+38, arl=+54, bend=+10, ty=+5, tp=+10, hy=+6, cr=25, lg=+28, wf=+20, ws=+5)),
        (14, dict(bel=-34, baz=+38, arl=+53, bend=+11, ty=+6, tp=+9,  hy=+5, cr=23, lg=+26, wf=+18, ws=+5)),
        (15, dict(bel=-33, baz=+38, arl=+52, bend=+11, ty=+6, tp=+8,  hy=+5, cr=21, lg=+24, wf=+16, ws=+5)),
        (16, dict(bel=-33, baz=+38, arl=+52, bend=+11, ty=+6, tp=+8,  hy=+4, cr=19, lg=+22, wf=+14, ws=+4)),
        # 회수 f17~21: [R10] Δ 10,9,9,8,6 (23차 11,10,9,8,6 이 12.6~13.4 m/s —
        # 리본 14.9 아래로 여유 있게). 무게를 끌어올리는 감속 꼬리.
        (17, dict(bel=-23, baz=+36, arl=+48, bend=+11, ty=+5, tp=+7, hy=+4, cr=16, lg=+18, wf=+11, ws=+4)),
        (18, dict(bel=-14, baz=+33, arl=+44, bend=+11, ty=+5, tp=+5, hy=+3, cr=12, lg=+14, wf=+9,  ws=+3)),
        (19, dict(bel=-5,  baz=+28, arl=+40, bend=+10, ty=+4, tp=+4, hy=+2, cr=9,  lg=+11, wf=+7,  ws=+2)),
        (20, dict(bel=+3,  baz=+24, arl=+36, bend=+8,  ty=+3, tp=+3, hy=+2, cr=6,  lg=+8,  wf=+5,  ws=+2)),
        (21, dict(bel=+9,  baz=+20, arl=+32, bend=+6,  ty=+2, tp=+2, hy=+1, cr=4,  lg=+5,  wf=+3,  ws=+1)),
    ]),

    # ── C 횡일섬 (타격 f8~13 은 23차 검증 궤적 유지. 고친 것 = [R10] 감기 가속
    #    서사, [R12] 골반이 감고 골반이 푼다, [R11] 오버슛 한 장, 회수 감속 강화
    #    (23차 f20 이 리본 14.3 을 15.1 로 넘던 것) ──
    "Wide": (22, [
        # 감기 f1~7: Δbaz 3.5,4,6,7,6,4,3 — 골반(hy)이 f2 부터 끌고 가슴(ty)이
        # 따라온다. 몸통이 먼저 비틀리고 칼이 끌려 감기는 순서.
        (1, dict(bel=+34, baz=-1,  arl=+8,  bend=+2,  ty=-1,  hy=-2,  cr=1,  lg=-2,  ws=-1, wf=-1)),
        (2, dict(bel=+32, baz=-5,  arl=+12, bend=+5,  ty=-2,  hy=-4,  cr=3,  lg=-5,  ws=-2, wf=-2)),
        (3, dict(bel=+30, baz=-11, arl=+14, bend=+9,  ty=-5,  hy=-6,  cr=5,  lg=-8,  ws=-3, wf=-3)),
        (4, dict(bel=+27, baz=-18, arl=+18, bend=+13, ty=-8,  hy=-8,  cr=7,  lg=-11, ws=-5, wf=-4)),
        (5, dict(bel=+24, baz=-24, arl=+21, bend=+16, ty=-11, hy=-9,  cr=8,  lg=-14, ws=-7, wf=-4)),
        (6, dict(bel=+22, baz=-28, arl=+23, bend=+18, ty=-13, hy=-10, cr=9,  lg=-16, ws=-8, wf=-5)),
        (7, dict(bel=+20, baz=-31, arl=+24, bend=+19, ty=-15, hy=-10, cr=10, lg=-17, ws=-8, wf=-5)),
        # 되누름·릴리즈 f8: [R12] 골반이 먼저 풀린다(hy -10→-6, ty 는 -15→-11)
        (8, dict(bel=+18, baz=-25, arl=+24, bend=+18, ty=-11, hy=-6,  cr=12, lg=-10, ws=-5, wf=-1)),
        # 타격 f8~13: 23차 검증 궤적(화면 100px/장급). [R12] 골반 몫 +1
        (9,  dict(bel=+15, baz=-10, arl=+26, bend=+12, ty=0,   hy=+2,  cr=13, lg=+3,  ws=0,   wf=+3)),
        (10, dict(bel=+12, baz=+18, arl=+30, bend=+10, ty=+13, hy=+9,  cr=14, lg=+15, ws=+5,  wf=+8)),
        (11, dict(bel=+10, baz=+42, arl=+32, bend=+9,  ty=+23, hy=+14, cr=13, lg=+23, ws=+9,  wf=+11)),
        (12, dict(bel=+9,  baz=+62, arl=+36, bend=+10, ty=+29, hy=+18, cr=12, lg=+28, ws=+11, wf=+12)),
        (13, dict(bel=+10, baz=+74, arl=+36, bend=+12, ty=+33, hy=+21, cr=11, lg=+31, ws=+12, wf=+12)),
        # [R11] 관성 오버슛 f14(+76. 23차는 f13 에서 곧장 되돌았다) → 정착·홀드 f15~16
        (14, dict(bel=+11, baz=+76, arl=+34, bend=+13, ty=+34, hy=+21, cr=10, lg=+30, ws=+11, wf=+11)),
        (15, dict(bel=+12, baz=+74, arl=+31, bend=+13, ty=+33, hy=+20, cr=9,  lg=+29, ws=+11, wf=+10)),
        (16, dict(bel=+13, baz=+72, arl=+29, bend=+13, ty=+32, hy=+19, cr=8,  lg=+28, ws=+10, wf=+10)),
        # 회수 f17~21: [R10] Δbaz 4,6,7,7,5 — 무겁게 출발하는 꼬리(23차 7,7,7,7,6 은
        # f20 이 15.1 m/s 로 리본 위 + v24a 의 6,6,6,6,5 는 화면 등속 플래그).
        # 끝 방위 +43 잔여는 Idle 크로스페이드가 메운다([R7])
        (17, dict(bel=+15, baz=+68, arl=+27, bend=+13, ty=+31, hy=+18, cr=7, lg=+26, ws=+9,  wf=+9)),
        (18, dict(bel=+17, baz=+62, arl=+25, bend=+12, ty=+29, hy=+17, cr=6, lg=+24, ws=+9,  wf=+8)),
        (19, dict(bel=+20, baz=+55, arl=+22, bend=+11, ty=+27, hy=+16, cr=5, lg=+21, ws=+8,  wf=+7)),
        (20, dict(bel=+23, baz=+48, arl=+19, bend=+9,  ty=+24, hy=+14, cr=4, lg=+18, ws=+6,  wf=+5)),
        (21, dict(bel=+26, baz=+43, arl=+16, bend=+7,  ty=+21, hy=+12, cr=3, lg=+15, ws=+5,  wf=+4)),
    ]),
}
# ★24차 롤백 스위치. 0 이면 23차 판(MOVES_V23 기본 1)이 그대로 이긴다.
MOVES_V24 = os.environ.get("MOVES_V24", "1") == "1"
if MOVES_V24:
    for _k in ("Attack", "Heavy", "Wide"):
        HAND_SPEC[_k] = HAND_SPEC_V24[_k]

# ══════════════════════════════════════════════════════════════════════════
# ★★25차 GRIP_V25 — **날 정렬 계약**: hot 프레임에서 칼은 날로 벤다(칼끝 속도
#   벡터와 날 평면의 사잇각 <=30도). 슬래브가 넓적면으로 때리면 베기가 아니라
#   뺨때리기다. 커밋본 실측(probe_blade25, v99_wave25/motion/probe/blade_before2):
#     Z 1타 f8~11 정렬 8~25도(통과. f12 30.2 = 경계라 불변) / 2타 f22~25 **54~70도
#     위반**(need +60~+76) / 3타 f36~37 통과·f38 47.8 위반(need -49)
#     X f9~11 5.8~17.0 전부 통과(**한 글자도 안 건드린다**)
#     C f8~13 **전부 67~71도 위반**(need +70~+72)
#   처방 = 칼축 둘레 롤(궤적·타격 슬롯 불변): arl 증분(팔+칼이 같이 롤) 우선
#   + 잔여는 손목 롤 wrl(해부 상한 45도 캡). 진입은 장전 구간 램프, 복귀는
#   프레임당 8도 이하(비-hot 손목 중립 계약).
#   ★값은 (arl 증분, wrl 절대값(None=키 없음)) 표다. hot 슬롯·bel/baz 는 불변.
#   ★1차 굽기 실측(griptest vs repro25, s24 진단 표 대조)이 설계 가설 하나를
#     뒤집었다: wrl(손목 칼축 롤)은 궤적을 **한 톨도 안 바꾸지만**(1·3타 v 표
#     바이트 일치), arl 증분은 손목을 어깨 중심 원뿔로 **평행이동**시켜 칼끝
#     속도를 살짝 바꾼다(2타 f22 43.7->38.6). hot 창 프레임은 그래도 불변이었다.
#     그래서 arl 몫을 최소화한다: Wide 는 wrl 45 단독(need 70~72 -> 잔여 25~27,
#     계약 상한 30 안), Attack 2타만 arl +12(합 57. 잔여 2~19도).
V25_BLADE = {
    "Attack": {
        # 2타(수평 되베기) hot f22~25: need +60~+76 = arl +12 + wrl +45 (합 57)
        16: (0, 0.0),                    # wrl 램프 시작(재장전 초입. 중립 고정점)
        22: (+12, +45.0), 23: (+12, +45.0), 24: (+12, +45.0), 25: (+12, +45.0),
        26: (+6, None), 27: (+3, None),   # 팔로스루 arl 감쇠 램프(팝 방지)
        31: (0, 0.0),                    # wrl 복귀 종점(6장 = 7.5도/장)
        # 1타 꼬리 f12(need -30): 국소 -10 롤(f8~11 정렬 8~25 는 격리 유지)
        8: (0, 0.0), 11: (0, 0.0), 12: (0, -10.0), 14: (0, 0.0),
        # 3타 꼬리 f37~38(need -24/-49): f36 중립 -> 램프 -> f42 복귀(8도/장)
        36: (0, 0.0), 37: (0, -18.0), 38: (0, -32.0), 42: (0, 0.0),
    },
    "Wide": {
        # 횡일섬 hot f8~13: need +70~+72 = wrl +45 단독(arl 0 = 궤적 완전 불변)
        8: (0, +45.0), 9: (0, +45.0), 10: (0, +45.0), 11: (0, +45.0),
        12: (0, +45.0), 13: (0, +45.0),
        19: (0, 0.0),                    # wrl 복귀 종점(6장 = 7.5도/장)
    },
}
if MOVES_V24 and GRIP_V25:
    for _k, _tab in V25_BLADE.items():
        _nf, _keys = HAND_SPEC[_k]
        _seen = set()
        for _f, _kv in _keys:
            if _f in _tab:
                _da, _wl = _tab[_f]
                if _da:
                    _kv["arl"] = _kv.get("arl", 0) + _da
                if _wl is not None:
                    _kv["wrl"] = _wl
                _seen.add(_f)
        for _f, (_da, _wl) in sorted(_tab.items()):
            if _f in _seen:
                continue
            _kv = {}
            if _da:
                _kv["arl"] = _da          # (지금 표에는 이 갈래가 없다. 안전망)
            if _wl is not None:
                _kv["wrl"] = _wl
            if _kv:
                _keys.append((_f, _kv))
        _keys.sort(key=lambda t: t[0])

# ================================ 16차 신설: 게임 카메라 화면 좌표 ================================
# ★★15차까지 세 판을 전부 **월드 좌표**(칼끝의 위/옆/앞)로 판정했고 세 판 다 통과했는데
#   오너는 세 판 다 기각했다. 16차에 처음으로 화면으로 재 보니 이유가 나왔다:
#     · 게임 카메라는 pitch 49.3도로 내려본다. 월드에서 1m 올라가면 화면 세로 43px,
#       1m **앞으로** 가도 화면 세로 47px 다 — 즉 내려베기의 "아래로"와 "앞으로"가
#       화면에서 서로 상쇄된다.
#     · 더 나쁜 것: **칼이 시선축과 나란해지면 화면에서 접힌다.** 칼 방향이
#       (위 -0.758, 앞 +0.653) 근처면 화면 길이가 83px -> 5px 로 준다.
#       15차 X(수면참)는 그 자리에 여덟 장(f10~f17) 머물렀다 = 임팩트와 팔로스루
#       내내 **칼이 화면에서 사라져 있었다.**
#   그래서 이제 굽는 자리에서 화면을 같이 잰다. 카메라 값은 main.js CAM 과 같다.
CAM_PITCH = 0.86          # rad. main.js CAM.pitch
CAM_DIST = 24.0           # main.js CAM.dist
CAM_FOV = 24.0            # main.js CAM.fov (세로 fov, 도)
CAM_LEAD = 1.25           # main.js CAM.lead (바라보는 점을 캐릭터 앞으로 민다)
SCR_W, SCR_H = 960, 640   # 판정 해상도
CHAR_H_GAME = 1.75        # 게임 캐릭터 키


def _cam_axes():
    """(l,u,f) 기저에서 카메라 눈·축. l=캐릭터 왼쪽 u=위 f=앞(캐릭터가 보는 쪽).
    ★main.js placeCamera 를 그대로 옮긴 것이다. 카메라는 캐릭터 **뒤 위**에 있고
      바라보는 점은 캐릭터보다 lead 만큼 앞이다."""
    sp, cp = math.sin(CAM_PITCH), math.cos(CAM_PITCH)
    tgt = Vector((0.0, CHAR_H_GAME * 0.62, CAM_LEAD))     # camTarget
    eye = tgt + Vector((0.0, sp * CAM_DIST, -cp * CAM_DIST))
    zc = (eye - tgt).normalized()                         # three.js lookAt 의 z(뒤쪽)
    up = Vector((0.0, 1.0, 0.0))
    xc = Vector((up.y * zc.z - up.z * zc.y,               # up x zc  (l,u,f 우수계)
                 up.z * zc.x - up.x * zc.z,
                 up.x * zc.y - up.y * zc.x)).normalized()
    yc = Vector((zc.y * xc.z - zc.z * xc.y,
                 zc.z * xc.x - zc.x * xc.z,
                 zc.x * xc.y - zc.y * xc.x)).normalized()
    return eye, xc, yc, zc


CAM_EYE, CAM_X, CAM_Y, CAM_Z = _cam_axes()
CAM_TAN = math.tan(math.radians(CAM_FOV) * 0.5)
CAM_ASPECT = SCR_W / float(SCR_H)


def screen_px(p):
    """게임 미터 (l,u,f) -> 화면 픽셀 (x 오른쪽+, y 아래+). 원점은 캐릭터 발밑."""
    d = Vector(p) - CAM_EYE
    zz = -d.dot(CAM_Z)                       # 카메라 앞쪽 거리
    if zz < 0.01:
        zz = 0.01
    nx = d.dot(CAM_X) / (zz * CAM_TAN * CAM_ASPECT)
    ny = d.dot(CAM_Y) / (zz * CAM_TAN)
    return (nx * SCR_W * 0.5, -ny * SCR_H * 0.5)


# ================================ 17차 신설: 8방향 화면 실루엣 ================================
# ★★16차의 화면 자(screen_px)는 **캐릭터가 카메라를 등지고 선 한 방향**만 잰다.
#   베기는 그래도 됐다 — 오너가 보는 컷이 대개 뒤통수 방향이고, 무엇보다 베기는
#   0.5초 안에 끝난다. 점프는 다르다: 게임이 상승 내내 f6, 하강 내내 f12 에서
#   **자세를 멈춰 세우고**, 플레이어는 여덟 방향 중 아무 데나 보고 뛴다.
#   그래서 자세 한 장이 여덟 개의 화면 그림이 된다.
#
# ★16차가 확립한 함정의 점프판 (2026-08-13, 17차)
#   카메라는 월드 yaw 고정이고 **캐릭터만 돈다.** 그러니 몸 기준 방향은 yaw 마다
#   다른 화면 방향이 된다. 실측 감도(아래 screen_px 로 잰 값):
#       월드 1m 위      -> 화면 41.5px 위
#       월드 1m 카메라 반대쪽(멀리) -> 화면 49.5px **위**
#       월드 1m 화면 오른쪽 -> 화면 64.8px 오른쪽
#   즉 "카메라 쪽으로 1m" 는 화면에서 49.5px **아래**다. 칼끝을 몸 오른쪽으로
#   1.9m 내밀어 놓으면, **오른쪽이 카메라 쪽이 되는 yaw**(= 캐릭터가 화면
#   오른쪽을 보고 뛸 때)에서 그 1.9m 이 통째로 화면 아래로 꽂힌다.
#   15차가 "칼끝 뒤 -1.44m -> 오른쪽 +1.9m" 로 고친 그 조치가, 화면에서는
#   **발밑으로 뻗은 수직 장대**를 만들었다(16차 건틀릿 SHEET_J3 #001~#003).
#   ★결론: 월드로 "몸 옆" 이라고 통과시키지 마라. 여덟 방향 전부 화면으로 재라.
#
# ★기하가 정한 한계(이 표를 읽는 사람이 반드시 알아야 한다)
#   칼이 몸에 고정된 방향인 한, 어느 yaw 에서는 칼의 수평 성분이 카메라 축과
#   나란해진다(8방향이면 최소 22.5도 안). 그때 화면 각은 거의 수직이 된다.
#   화면에서 "아래로 꽂히지 않게" 하려면 41.5*sin(E) > 49.5*cos(E),
#   즉 **칼끝 고도 E > 47.5도**여야 하는데 그건 팔을 만세로 들어야 나온다.
#   그래서 17차의 처방은 "수직을 없애기"가 아니라 **셋을 동시에 누르기**다:
#     1) 칼끝 고도 E 를 올려 아래로 꽂히는 성분을 줄인다(장대 길이 = 발밑 침투)
#     2) 칼 방위 Wd 를 45도 격자에서 **22~25도 비껴** 어느 yaw 도 정확한 수직에
#        떨어지지 않게 한다(수직편차 20도 이상 확보)
#     3) 칼이 몸 실루엣을 가로지르는 몫(겹침)을 방위로 밀어낸다
JUMP_YAW_NAMES = ["화면위(등)", "위-오른", "오른", "아래-오른",
                  "아래(정면)", "아래-왼", "왼", "위-왼"]


def _yaw_luf(rt, up, fw, yaw):
    """캐릭터 로컬 (오른쪽,위,앞) 게임 m -> **고정 월드** (l,u,f) 게임 m.
    yaw=0 이 카메라를 등진 자세(화면 위로 달릴 때)다. yaw 는 라디안, 화면
    시계방향(위->오른쪽->아래->왼쪽)으로 돈다.
    ★screen_px 의 (l,u,f) 는 캐릭터 축이 아니라 **카메라가 고정된 월드 축**이다
      (l=화면 왼쪽 u=위 f=카메라 반대쪽). 캐릭터가 돌면 몸 축만 그 안에서 돈다."""
    c, s = math.cos(yaw), math.sin(yaw)
    return (-rt * c - fw * s, up, fw * c - rt * s)


def _seg_dist(p, a, b):
    """점 p 에서 선분 ab 까지 거리(px)."""
    ax, ay = b[0] - a[0], b[1] - a[1]
    L2 = ax * ax + ay * ay
    t = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, ((p[0] - a[0]) * ax
                                                 + (p[1] - a[1]) * ay) / L2))
    return math.hypot(p[0] - a[0] - ax * t, p[1] - a[1] - ay * t)


JUMP_BODY_R = 0.22        # 몸통 반폭(게임 m). 화면 겹침을 재는 통로 폭
JUMP_HOLDS = (6, 12)      # 게임이 체공 중 멈춰 세우는 두 장(main.js jump.rise/fall)
JUMP_AIR = (4, 14)        # 발이 떨어져 있는 구간. f15 는 착지 접촉장(a.time=LAND)


def jump_screen_audit(rows, holds=JUMP_HOLDS, air=JUMP_AIR,
                      title="점프 8방향 화면 실루엣"):
    """rows = [((오른,위,앞) 손, (오른,위,앞) 칼끝)...] (게임 m, 발밑 원점).
    여덟 방향 각각에서 화면 칼 실루엣을 재고 표로 찍는다. 반환 = 방향별 최악값.

    ★판정을 셋으로 나눈 이유: 게임은 체공 중 **f6·f12 두 장에서 멈춰 선다**
      (main.js 가 a.time 을 rise/fall 에 물린다). 오너가 본 장대도 그 두 장이다.
      나머지 체공 장(f4~f14)은 1/30초씩 지나가고, 지상 장(도약 전·착지 후)은
      칼이 바닥 가까이 있는 게 정상이라 같은 잣대로 재면 안 된다.
    """
    print("   ★%s (960x640 · 캐릭터 키 화면 %.0fpx)"
          % (title, screen_px((0, 0, 0))[1] - screen_px((0, CHAR_H_GAME, 0))[1]))
    print("     %-10s %s | %s"
          % ("", "  ".join("%23s" % ("★체공정지 f%d" % f) for f in holds),
             "체공 최악(f%d~%d)  지상 최악" % air))
    print("     %-10s %s | %s"
          % ("yaw(화면)",
             "  ".join("%23s" % "길이  각도 편차 겹침 발밑" for _ in holds),
             " 길이 편차 겹침 발밑        판정"))
    out = []
    for k, nm in enumerate(JUMP_YAW_NAMES):
        yaw = math.radians(45.0 * k)
        cells, w_air, w_grd = [], None, None
        for i, (hd, tp) in enumerate(rows):
            H = screen_px(_yaw_luf(*hd, yaw=yaw))
            T = screen_px(_yaw_luf(*tp, yaw=yaw))
            F = screen_px(_yaw_luf(0.0, 0.0, 0.0, yaw))
            D = screen_px(_yaw_luf(0.0, CHAR_H_GAME, 0.0, yaw))
            dx, dy = T[0] - H[0], T[1] - H[1]
            ln = math.hypot(dx, dy)
            ang = math.degrees(math.atan2(-dy, dx))        # +90 = 화면 위
            vdev = abs(abs(ang) - 90.0)                    # 0 = 완전 수직
            n = 24
            ovl = sum(1 for j in range(n + 1)
                      if _seg_dist((H[0] + dx * j / n, H[1] + dy * j / n), F, D)
                      < JUMP_BODY_R * 64.76) / float(n + 1)
            bel = T[1] - F[1]                              # + = 화면에서 발밑 아래
            # 장대 점수: 길고(len) 수직에 가깝고(vdev) 몸을 가로지르거나(ovl)
            # 발밑을 뚫고 내려간(bel) 만큼 나쁘다. 0.55 넘으면 "꿰인 사람"이다.
            pole = ((max(0.0, 30.0 - vdev) / 30.0) * (ln / 100.0)
                    * (0.4 + 0.6 * min(1.0, max(0.0, bel) / 60.0) + ovl))
            if i in holds:
                cells.append((ln, ang, vdev, ovl, bel))
            tgt = "air" if air[0] <= i <= air[1] else "grd"
            if tgt == "air" and (w_air is None or pole > w_air[0]):
                w_air = (pole, ln, vdev, ovl, bel, i)
            if tgt == "grd" and (w_grd is None or pole > w_grd[0]):
                w_grd = (pole, ln, vdev, ovl, bel, i)
        hold_bad = max(_pole_of(c) for c in cells)
        # ★18차: Idle 처럼 '지상 구간'이 아예 없는 클립도 이 자를 쓴다(air 가 전 프레임).
        if w_grd is None:
            w_grd = (0.0, 0.0, 0.0, 0.0, 0.0, -1)
        vd = ("★장대" if max(hold_bad, w_air[0]) > 0.55
              else ("접힘" if min(c[0] for c in cells) < 35
                    else ("통과(지상만△)" if w_grd[0] > 0.55 else "통과")))
        print("     %-10s %s | %4.0f %4.0f %5.2f %+5.0f  f%-2d %.2f / f%-2d %.2f  %s"
              % (nm,
                 "  ".join("%4.0f %+5.0f %4.0f %5.2f %+5.0f" % c for c in cells),
                 w_air[1], w_air[2], w_air[3], w_air[4],
                 w_air[5], w_air[0], w_grd[5], w_grd[0], vd))
        out.append((nm, cells, w_air, w_grd))
    bad = [o for o in out if max(max(_pole_of(c) for c in o[1]), o[2][0]) > 0.55]
    print("     -> ★체공 장대 판정 %d/8 방향%s"
          % (len(bad), ("  " + " ".join(o[0] for o in bad)) if bad else ""))
    return out


def _pole_of(c):
    """표 셀(길이,각도,편차,겹침,발밑) -> 장대 점수. 위 식과 같은 것."""
    ln, _, vdev, ovl, bel = c
    return ((max(0.0, 30.0 - vdev) / 30.0) * (ln / 100.0)
            * (0.4 + 0.6 * min(1.0, max(0.0, bel) / 60.0) + ovl))


def _sph(el, az):
    """가슴 좌표계 단위벡터. X=왼쪽 Y=위 Z=앞. az 0=앞 +=왼쪽, el +=위."""
    el, az = math.radians(el), math.radians(az)
    return Vector((math.sin(az) * math.cos(el), math.sin(el),
                   math.cos(az) * math.cos(el)))


def _unsph(v):
    """단위벡터 -> (고도, 방위) 도. _sph 의 역."""
    v = v.normalized()
    return (math.degrees(math.asin(max(-1.0, min(1.0, v.y)))),
            math.degrees(math.atan2(v.x, v.z)))


def _bframe(bt, C):
    """칼 축 bt 에 수직인 기준 두 축. e1 = '칼 아래쪽', e2 = bt x e1.
    팔 roll(arl) 은 e1 에서 e2 쪽으로 재는 각이다(0도 = 팔이 칼 아래쪽)."""
    dn = -(C @ Vector((0, 1, 0)))                # 가슴 기준 아래
    e1 = dn - bt * dn.dot(bt)
    if e1.length < 1e-5:                         # 칼이 수직이면 뒤쪽을 기준으로
        bk = -(C @ Vector((0, 0, 1)))
        e1 = bk - bt * bk.dot(bt)
    e1.normalize()
    return e1, bt.cross(e1).normalized()


def _crv(pts, x):
    """Catmull-Rom. pts = [(f, v)...] (f 오름차순). 키 사이는 부드럽고 살짝 넘어간다."""
    if len(pts) == 1:
        return pts[0][1]
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    i = 0
    while i < len(pts) - 2 and x > pts[i + 1][0]:
        i += 1
    x0, y0 = pts[i]
    x1, y1 = pts[i + 1]
    xm, ym = pts[i - 1] if i > 0 else (x0, y0)
    xp, yp = pts[i + 2] if i + 2 < len(pts) else (x1, y1)
    h = x1 - x0
    m0 = (y1 - ym) / max(1e-6, x1 - xm) * h
    m1 = (yp - y0) / max(1e-6, xp - x0) * h
    t = (x - x0) / max(1e-6, h)
    t2, t3 = t * t, t * t * t
    return ((2 * t3 - 3 * t2 + 1) * y0 + (t3 - 2 * t2 + t) * m0
            + (-2 * t3 + 3 * t2) * y1 + (t3 - t2) * m1)


def bake_hand(name):
    nf, keys = HAND_SPEC[name]

    # --- 바탕 자세: Idle 첫 프레임(리타게팅 결과 그대로) ---
    f0, f1 = use_src("Idle")
    praw = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        praw.append((S2W @ src.pose.bones[PELVIS].matrix).translation.copy())
    n_i = len(praw)
    pmean = Vector((sum(p.x for p in praw) / n_i, sum(p.y for p in praw) / n_i,
                    sum(p.z for p in praw) / n_i))
    sc.frame_set(f0)
    bpy.context.view_layer.update()
    GT0 = grip_target() if DO_GRIP else None
    BASE_R = {bn: m.copy() for bn, m in delta_rots().items()}
    BASE_P = DREST[ROOT_BONE][1] + (praw[0] - pmean) * K_TRANS
    pose0, _ = build(BASE_R, BASE_P)
    C0 = torso_frame(pose0)
    HM0 = A2W @ pose0[HAND_R]
    Hr0 = HM0.to_3x3()
    Hr0.normalize()
    d0w = (Hr0 @ TIP_DIR).normalized()
    a0w = (wpos(pose0, HAND_R) - wpos(pose0, R_ARM[0])).normalized()
    BASE = dict(zip(("bel", "baz"), _unsph(C0.inverted() @ d0w)))
    _e1, _e2 = _bframe(d0w, C0)
    BASE["arl"] = math.degrees(math.atan2(a0w.dot(_e2), a0w.dot(_e1)))
    for c in ("bend", "ty", "tp", "tr", "hy", "cr", "lg", "wf", "ws", "wrl"):
        BASE[c] = 0.0
    BASE["gw"] = 1.0
    print("\n[%s] ★수제 키프레임 %d장 (%.3f초 @30fps) / 키 %d개"
          % (name, nf, (nf - 1) / 30.0, len(keys)))
    print("   바탕(Idle f0): 칼끝 고도 %+.1f 방위 %+.1f / 팔 roll %+.1f (팔-칼 사잇각 %.1f도)"
          % (BASE["bel"], BASE["baz"], BASE["arl"], math.degrees(a0w.angle(d0w))))

    # --- 채널별 커브 ---
    CH = {}
    for c in HAND_CH:
        pts = [(0.0, BASE[c])]
        for fk, kv in keys:
            if c in kv:
                v = kv[c]
                pts.append((float(fk), BASE[c] if v == "base" else float(v)))
        pts.sort(key=lambda p: p[0])
        CH[c] = pts

    def val(c, i):
        return _crv(CH[c], float(i))

    def frame_pose(i):
        """i 번째 프레임의 (pose, basis, Rw, pw, 진단)."""
        Rw = {bn: BASE_R[bn].copy() for bn in ORDER}
        pw = BASE_P.copy()
        cr = math.radians(val("cr", i))
        if abs(cr) > 1e-6:                       # 웅크림: 엉덩이-무릎-발목 3분절
            mh = Quaternion(W_LFT, CR_SGN * cr).to_matrix()
            mk = Quaternion(W_LFT, -CR_SGN * cr).to_matrix()
            for bn in THIGHS:
                Rw[bn] = mh @ Rw[bn]
            for bn in CALFS:
                Rw[bn] = mk @ Rw[bn]
            pw = pw - W_UP * (LEG_LEN * (1.0 - math.cos(cr)))
        lg = math.radians(val("lg", i))
        if abs(lg) > 1e-6:                       # 스탠스: 허벅지만 앞뒤로 갈라 돌린다
            mf = Quaternion(W_LFT, CR_SGN * lg).to_matrix()
            mb = Quaternion(W_LFT, -CR_SGN * lg).to_matrix()
            Rw["Bip001 L Thigh"] = mf @ Rw["Bip001 L Thigh"]
            Rw["Bip001 R Thigh"] = mb @ Rw["Bip001 R Thigh"]
            # 정강이·발은 안 건드린다(월드 회전 유지) = 발바닥이 계속 바닥과 나란하고
            # 무릎만 앞뒤로 벌어진다. 그만큼 골반이 내려앉는다.
            pw = pw - W_UP * (THIGH_LEN * (1.0 - math.cos(lg)))
        # ── 무게중심 옮기기 (16차 신설) ──
        # ★골반을 실제로 옮긴다. 발이 같이 끌려가면 미끄러지므로 허벅지를 **반대로**
        #   돌려 발을 제자리에 붙들어 둔다(다리가 뒤로 끌리는 = 앞으로 체중을 실은 그림).
        kcm = DH / CHAR_H_GAME / 100.0            # 게임 cm -> 블렌더 단위
        wf = val("wf", i) * kcm
        ws = val("ws", i) * kcm
        if abs(wf) > 1e-9 or abs(ws) > 1e-9:
            pw = pw + W_FWD * wf + W_LFT * ws
            if abs(wf) > 1e-9:
                th = math.asin(max(-0.7, min(0.7, wf / LEG_LEN)))
                mq = Quaternion(W_LFT, -CR_SGN * th).to_matrix()
                for bn in THIGHS:
                    Rw[bn] = mq @ Rw[bn]
                pw = pw - W_UP * (LEG_LEN * (1.0 - math.cos(th)))
            if abs(ws) > 1e-9:
                th = math.asin(max(-0.7, min(0.7, ws / LEG_LEN)))
                mq = Quaternion(W_FWD, -th).to_matrix()
                for bn in THIGHS:
                    Rw[bn] = mq @ Rw[bn]
                pw = pw - W_UP * (LEG_LEN * (1.0 - math.cos(th)))
        hy = math.radians(val("hy", i))
        if abs(hy) > 1e-6:                       # 골반 돌림(발은 제자리)
            mp = Quaternion(W_UP, hy).to_matrix()
            Rw[PELVIS] = mp @ Rw[PELVIS]
            for bn in UPPER:
                Rw[bn] = mp @ Rw[bn]
        qt = (Quaternion(W_UP, math.radians(val("ty", i)))
              @ Quaternion(W_LFT, math.radians(val("tp", i)))
              @ Quaternion(W_FWD, math.radians(val("tr", i))))
        if qt.angle > 1e-6:
            mt = qt.to_matrix()
            for bn in UPPER:
                Rw[bn] = mt @ Rw[bn]
        pose, basis = build(Rw, pw)
        # 팔꿈치 굽힘(팔뚝·손만 돈다)
        bd = math.radians(val("bend", i))
        if abs(bd) > 1e-6:
            S = wpos(pose, R_ARM[0])
            E = wpos(pose, R_ARM[1])
            W = wpos(pose, HAND_R)
            n = (E - S).cross(W - E)
            if n.length < 1e-6:
                n = (C0 @ Vector((-1, 0, 0)))
            mb = Quaternion(n.normalized(), bd).to_matrix()
            Rw[R_ARM[1]] = mb @ Rw[R_ARM[1]]
            Rw[HAND_R] = mb @ Rw[HAND_R]
            pose, basis = build(Rw, pw)
        # ── 칼끝 겨누기 + 팔 굴리기 ──
        # ★★팔이 칼과 이루는 각 α 는 **파지가 정한 상수**다(레스트에서 약 80도).
        #   그래서 팔 방향을 절대 각도로 적으면 안 된다 — 1차 실행에서 팔 목표를
        #   절대값으로 줬더니 잔각이 상한 26도에 늘 붙어 팔이 목표에서 47도까지
        #   어긋났고, 그 바람에 오른손이 몸 바깥으로 나가 **왼손이 자루를 놓쳤다**
        #   (뻗음 1.30 = 팔 길이의 130%). 팔에 줄 수 있는 자유는 하나뿐이다:
        #   **칼 축 둘레로 어디에 놓을 것인가(roll)**. 그것만 준다.
        C = torso_frame(pose)
        bt = (C @ _sph(val("bel", i), val("baz", i))).normalized()
        S = wpos(pose, R_ARM[0])
        W = wpos(pose, HAND_R)
        Hr = (A2W @ pose[HAND_R]).to_3x3()
        Hr.normalize()
        d = (Hr @ TIP_DIR).normalized()
        a = (W - S).normalized()
        q = d.rotation_difference(bt)
        al = a.angle(d)                          # 팔-칼 사잇각(이 회전으로 안 변한다)
        e1, e2 = _bframe(bt, C)
        ph = math.radians(val("arl", i))
        at = (bt * math.cos(al)
              + (e1 * math.cos(ph) + e2 * math.sin(ph)) * math.sin(al))
        p = q @ a
        p = p - bt * p.dot(bt)
        r = at - bt * at.dot(bt)
        if p.length > 1e-5 and r.length > 1e-5:
            p.normalize()
            r.normalize()
            q = Quaternion(bt, math.atan2(p.cross(r).dot(bt), p.dot(r))) @ q
        wr = 0.0                                 # 잔각이 0 이라 손목을 안 쓴다
        mq = q.to_matrix()
        for bn in R_ARM:
            Rw[bn] = mq @ Rw[bn]
        # ★25차 GRIP_V25: 날 정렬 손목 롤(wrl). 축이 칼축(bt)이라 칼끝 궤적·타격
        #   슬롯이 불변이고 날면 방향만 돈다. GRIP_V25=0 이면 키가 없어 늘 0 이다.
        if GRIP_V25:
            _wl = math.radians(val("wrl", i))
            if abs(_wl) > 1e-6:
                Rw[HAND_R] = Quaternion(bt, _wl).to_matrix() @ Rw[HAND_R]
        pose, basis = build(Rw, pw)
        # 왼손 파지(두 손). gw=0 이면 왼팔은 바탕 자세 그대로 남는다
        dev, reach = 0.0, 0.0
        if DO_GRIP and GT0 is not None:
            gw = max(0.0, min(1.0, val("gw", i)))
            gt = (GT0[0], GT0[1], GT0[2], gw)
            T, bef, _, w, Ch, wh = apply_grip(pose, Rw, gt, None)
            reach = (T - wpos(pose, L_ARM[0])).length / ARM_L
            if DBG_REACH:
                CC = torso_frame(pose)
                LS = wpos(pose, L_ARM[0])
                rr = CC.inverted() @ (T - LS)
                hh = CC.inverted() @ (wpos(pose, HAND_R) - LS)
                print("      [reach f%d] 자루목표 왼어깨기준 (좌%+.3f 위%+.3f 앞%+.3f)H"
                      " %.2f / 오른손 (좌%+.3f 위%+.3f 앞%+.3f)H %.2f / 오른팔뻗음 %.2f"
                      % (i, rr.x / DH, rr.y / DH, rr.z / DH, rr.length / ARM_L,
                         hh.x / DH, hh.y / DH, hh.z / DH, hh.length / ARM_L,
                         (wpos(pose, HAND_R) - wpos(pose, R_ARM[0])).length / ARM_L))
            pose, basis = build(Rw, pw)
            dev = (wpos(pose, HAND_L) - T).length / DH
            if apply_hand_grip(pose, Rw, Ch, wh):
                pose, basis = build(Rw, pw)
        return pose, basis, Rw, pw, math.degrees(wr), dev, reach

    # --- 1차: 접지 보정량·칼끝 진단 ---
    gk = 1.75 / DH
    ts = {"Attack": 1.35, "Heavy": 1.15, "Wide": 1.20}.get(name, 1.0)
    lows, tips, hips, hnds, knees, maxerr, wrs, devs, rchs, pit = (
        [], [], [], [], [], 0.0, [], [], [], 0)
    for i in range(nf):
        pose, basis, Rw, pw, wr, dev, reach = frame_pose(i)
        for bn in ORDER:
            arm.pose.bones[bn].matrix_basis = basis[bn]
        bpy.context.view_layer.update()
        if i % 8 == 0:                           # 해석식 자기검증(★함정 8)
            for bn in ORDER:
                aa = (A2W @ arm.pose.bones[bn].matrix).translation
                bb = (A2W @ pose[bn]).translation
                maxerr = max(maxerr, (aa - bb).length)
        lows.append(low_of(DST_BODY))
        HM = A2W @ pose[HAND_R]
        tips.append(HM @ (TIP_DIR * D_SW[2] * ANIM_TIP_K / HM.to_3x3().to_scale()[0]))
        hips.append(wpos(pose, PELVIS))
        hnds.append(wpos(pose, HAND_R))
        knees.append((wpos(pose, "Bip001 L Calf") - wpos(pose, "Bip001 L Thigh"))
                     .dot(W_FWD) / DH)
        wrs.append(wr)
        devs.append(dev)
        rchs.append(reach)
        rh = wpos(pose, HAND_R)
        # 투구 판정: 손이 어깨 위 +0.05H 이고 가슴 뒤 +0.20H (probe_moves_read 와 같은 자)
        if ((rh - wpos(pose, CLAV_R)).dot(W_UP) / DH > 0.05
                and -(rh - wpos(pose, "Bip001 Chest2")).dot(W_FWD) / DH > 0.20):
            pit += 1
    shift = BIND_LOW - pct(lows, 0.10)
    print("   해석식 자기검증: Blender 평가와 뼈 위치 최대 오차 %.7f (키의 %.5f%%)"
          % (maxerr, maxerr / DH * 100))
    if maxerr > DH * 1e-4:
        raise SystemExit("해석식 FK 가 Blender 평가와 다르다. 신뢰 불가")
    print("   접지 보정: 메시 최저 %.4f~%.4f (10분위 %.4f) -> 바인드 %.4f (%+.4f)"
          % (min(lows), max(lows), pct(lows, 0.10), BIND_LOW, shift))
    print("   왼손 이탈(자루까지, 키 정규화) %.4f~%.4f (최대 %.2f주먹 @f%d)"
          " / 손목 잔각 최대 %.1f도 (상한 %.0f)"
          % (min(devs), max(devs), max(devs) / FIST, devs.index(max(devs)),
             max(wrs), HAND_WRIST))
    print("   왼팔 뻗음(자루 목표까지 / 팔 길이) %.2f~%.2f  ★1.00 넘으면 그만큼 못 잡는다"
          % (min(rchs), max(rchs)))
    print("   무릎 전방 변위(키 정규화) %.4f~%.4f  ★웅크림이 클수록 커져야 한다"
          % (min(knees), max(knees)))
    print("   ★투구 프레임(손 어깨위+가슴뒤): %d장 / %d" % (pit, nf))
    vs = [0.0] + [(tips[i] - tips[i - 1]).length * 30.0 * gk * ts
                  for i in range(1, nf)]
    cl = [(t.z + shift - BIND_LOW) * gk for t in tips]
    # ★진단 좌표계는 probe_moves_read.py 와 **같은 고정 월드 축**이다(가슴 좌표계가
    #   아니다). 게임 카메라가 캐릭터 뒤에 있으니 화면 가로=L · 화면 세로=U ·
    #   화면 깊이=F 이고, 판정 부채꼴이 보는 것도 F 다. 몸이 돌면 가슴 축도 도는데
    #   그걸로 재면 "돌았으니 안 움직였다"는 거짓 판정이 나온다.
    rel = [Vector(((t - h).dot(W_LFT), (t - h).dot(W_UP), (t - h).dot(W_FWD)))
           for t, h in zip(tips, hips)]
    hot = [i for i, v in enumerate(vs) if v > 15.8]
    runs, cur = [], []
    for i in hot:
        if cur and i != cur[-1] + 1:
            runs.append(cur)
            cur = []
        cur.append(i)
    if cur:
        runs.append(cur)
    print("   칼끝(게임 1.75m 환산, **재생속도 %.2f 곱한 값** = 게임이 보는 속도):"
          " 최고 %.1f m/s / 바닥여유 %+.3f~%+.3f m" % (ts, max(vs), min(cl), max(cl)))
    for k, run in enumerate(runs):
        i0 = max(0, run[0] - 1)
        pa, pb = rel[i0], rel[run[-1]]
        dL, dU, dF = pb.x - pa.x, pb.y - pa.y, pb.z - pa.z
        print("     스윙%d f%d~%d (클립 %.3f~%.3f / 게임 %.3f~%.3f초)  "
              "ΔL %+.2f ΔU %+.2f ΔF %+.2f  세로성 %.2f 가로성 %.2f"
              % (k + 1, run[0], run[-1], run[0] / 30.0, run[-1] / 30.0,
                 run[0] / 30.0 / ts, run[-1] / 30.0 / ts, dL * gk, dU * gk, dF * gk,
                 abs(dU) / max(abs(dL), 1e-6), abs(dL) / max(abs(dU), 1e-6)))
    if not runs:
        print("     ★타격 구간 없음! 이 클립은 안 벤다")
    hz = [(h.z + shift - BIND_LOW) * gk for h in hnds]
    print("   프레임별  v=칼끝속도 z=칼끝 바닥여유 h=오른손 높이"
          " F=칼끝 앞뒤(>0 이어야 벤다) 손=왼손이탈(주먹):")
    for i in range(nf):
        pf = rel[i].z * gk
        print("     f%-3d %5.3fs  v%6.1f  z%+6.3f  h%5.2f  F%+6.2f  손%4.1f  %s%s"
              % (i, i / 30.0, vs[i], cl[i], hz[i], pf, devs[i] / FIST,
                 "#" * int(vs[i] / max(1e-9, max(vs)) * 28),
                 "  <-hot" if vs[i] > 15.8 else ""))

    # ── ★★16차: 게임 카메라 화면 판정 ──
    # 오너는 월드가 아니라 **화면**을 본다. 여기서 재는 셋이 15차까지 한 번도
    # 안 잰 차원이다: 화면 칼 길이(접힘) · 화면 칼끝 이동(px) · 등속 구간.
    def _luf(P):
        d = P - BASE_P
        return (d.dot(W_LFT) * gk, (P.z + shift - BIND_LOW) * gk, d.dot(W_FWD) * gk)

    sc_tip = [screen_px(_luf(t)) for t in tips]
    sc_hnd = [screen_px(_luf(h)) for h in hnds]
    sblade = [math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(sc_tip, sc_hnd)]
    sv = [0.0] + [math.hypot(sc_tip[i][0] - sc_tip[i - 1][0],
                             sc_tip[i][1] - sc_tip[i - 1][1]) for i in range(1, nf)]
    smax = max(sblade)
    pk = max(sv)
    # 등속 구간: 이웃 세 장의 화면속도가 서로 15% 안이고 그게 4장 이상 이어지면 기계적이다
    flat, cur = [], 0
    for i in range(2, nf):
        a, bq = sv[i - 1], sv[i]
        if a > pk * 0.12 and abs(bq - a) <= max(1.0, a * 0.15):
            cur += 1
        else:
            if cur >= 3:
                flat.append((i - cur - 1, cur + 1))
            cur = 0
    if cur >= 3:
        flat.append((nf - cur - 1, cur + 1))
    dead, cur = [], 0
    for i in range(1, nf):
        if sv[i] < pk * 0.10:
            cur += 1
        else:
            if cur >= 2:
                dead.append((i - cur, cur))
            cur = 0
    if cur >= 2:
        dead.append((nf - cur, cur))
    thin = [i for i in range(nf) if sblade[i] < smax * 0.45]
    print("   ★게임 카메라 화면(960x640): 칼 길이 최대 %.0f px · 최소 %.0f px(%.0f%%)"
          % (smax, min(sblade), min(sblade) / smax * 100))
    print("     45%% 미만(칼이 시선축과 나란해 접힌 장) %d장%s"
          % (len(thin), ("  f" + ",f".join(str(x) for x in thin)) if thin else ""))
    print("     화면 칼끝 최고 %.0f px/장 · 중앙 %.0f px/장" % (pk, sorted(sv)[nf // 2]))
    print("     등속 구간(4장 이상) %s / 죽은 장(<10%%, 2장 이상) %s"
          % (" ".join("f%d~%d" % (s, s + c - 1) for s, c in flat) or "없음",
             " ".join("f%d~%d" % (s, s + c - 1) for s, c in dead) or "없음"))
    print("     f    화면칼끝(x,y)px   화면칼길이  화면속도px/장")
    for i in range(nf):
        print("     f%-3d (%+7.1f,%+7.1f) %8.0f %10.1f  %s"
              % (i, sc_tip[i][0], sc_tip[i][1], sblade[i], sv[i],
                 "#" * int(sv[i] / max(1e-9, pk) * 34)))

    # --- 2차: 키 찍기 ---
    act = new_action(name)
    for i in range(nf):
        pose, basis, Rw, pw, _, _, _ = frame_pose(i)
        pw = pw + Vector((0, 0, shift))
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
    if c in HAND and c in HAND_SPEC:
        BAKED[c] = bake_hand(c)
    elif c in ANIM:
        BAKED[c] = bake_alt(c, ANIM[c])
    else:
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
