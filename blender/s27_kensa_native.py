# -*- coding: utf-8 -*-
"""검사(kensa)의 걷기·달리기를 **Meshy 네이티브 클립**으로 갈아 끼운다.

    blender -b -P blender/s27_kensa_native.py
    -> web/kensa.glb  (Walk/Run = 네이티브, Idle/Attack/Heavy/Wide/Jump = 그대로)
    그다음  python3 tools/glb_rename.py web/kensa.glb   (이름에 .001 이 붙었나 확인)

왜 만들었나
  지금 kensa 의 Idle/Walk/Run 은 토이솔저 리그(slayer.glb)에서 리타게팅해 온 것이다
  (s24_moveset.py). 리타게팅은 아무리 잘해도 두 리그의 비례 차이만큼 왜곡이 남는다.
  s24 로그가 남긴 왼팔 정합 경고(33도)가 그 증거다.
  그런데 **kensa 자기 리그로 만들어진 네이티브 클립이 이미 있다**:
      incoming/meshy_slayer/..._Animation_Idle_14_withSkin.glb   7.53초
      incoming/meshy_slayer/..._Animation_Walking_withSkin.glb   1.07초
      incoming/meshy_slayer/..._Animation_Running_withSkin.glb   0.67초
  같은 리그라 리타게팅 자체가 필요 없다. 왜곡이 0 이다.

★셋 중 걷기·달리기만 쓴다 (2026-08-10 v90 판단, 근거 렌더는 renders/history/v90_motion)
  Idle_14 는 이름만 Idle 이고 실제로는 **7.5초짜리 품새**다. 칼을 머리 위로 들었다
  내리고, 몸을 돌리고, f113 에서 하이킥을 찬다. 골반이 앞뒤로 0.52m 움직인다.
  가만히 서 있는 동안 캐릭터가 혼자 발차기하는 화면이 되므로 기각했다.
  지금 Idle(양손 겨눔)은 게임 톤에 맞고 파지도 안정적이라(왼손-자루축 0.086 고정) 유지한다.

★네이티브는 빈손 클립이라 **칼이 풍차처럼 돈다**. 그래서 세 가지를 얹는다
  1) 오른팔 감쇠(ARM_DAMP): 오른팔 4본만 자기 사이클 평균 자세 쪽으로 당긴다.
     한 손에 뭘 들고 걸으면 그 팔은 원래 덜 흔든다. 왼팔·다리·척추는 안 건드린다.
     실측 칼 방향호: 걷기 89.5도 -> 36.1도 / 달리기 72.3도 -> 39.1도
  2) 오른팔 들기(ARM_LIFT): 감쇠한 팔을 프레임마다 **월드에서 정확히 그 각도만큼**
     들어 올린다(어깨 회전. 손·칼은 강체로 따라온다). 2026-08-12 추가 — 아래 참조.
  3) 손목 로컬 회전(WRIST_FIX): 감쇠하면 칼이 '사이클 평균 방향'에 굳는데 그 평균이
     걷기는 정면 수평(-23도), 달리기는 어깨 위(+17도)라 둘 다 실루엣을 망친다
     (달리기는 칼이 머리를 가로지른다). 칼끝 평균 고도를 TIP_ELEV 로 맞춘다.

★★하류에서 칼이 커지면 이 스크립트의 측정이 거짓말이 된다 (SW_NAME·TIP_K)
  2026-08-12 오너 지시로 s34 가 **1번 칼을 1.5배**로 키워 자루째 다시 앉혔다.
  손목-칼끝 거리가 73.87 -> 131.53 (**x1.7806**) 이 됐고, 그 칼이 게임 **시작 칼**이다
  (main.js swordIdx=0). 그런데 이 스크립트는 s34 **앞**에 도므로 그 크기를 못 본다.
  기본값(SW_baekah, TIP_K=1) 그대로 두면 바닥여유가 +0.20 이라고 찍고 넘어가는데
  실제 게임 화면에서는 칼끝이 **지면 아래 0.47m** 까지 내려간다(실측).
      SW_NAME  측정 기준 칼을 고른다(게임 시작 칼 = SW_nokseun)
      TIP_K    하류에서 손목-칼끝 거리가 몇 배가 되는지. 그 배율로 **가상 칼끝**을
               만들어 바닥여유에 함께 넣는다. s34 가 칼끝을 같은 반직선 위에
               다시 놓으므로(로그의 dir 오차 0.017도) 이 모형이 정확하다.
  ★관통(몸)은 실제 메시로만 잰다. s34 는 자루를 주먹에 다시 앉히므로 칼몸 전체가
    단순히 커지는 게 아니라서, 가상 칼끝으로 관통을 흉내 내면 오히려 거짓말이 된다.

★"같은 리그"는 가정이 아니라 실측이다
  이 스크립트는 시작하자마자 두 아마추어의 **레스트를 뼈 24개 전부 대조**한다.
  실측: 최대 위치차 0.000022(아마추어 단위, 월드로는 2e-7 m) / 최대 축 각도차 0.026도.
  즉 완전히 같은 레스트다. 그래서 리타게팅(레스트 델타 계산)을 안 하고
  **fcurve 를 그대로 옮긴다**. 키 값을 한 번도 다시 굽지 않으므로 원본 그대로다.
  대조에서 어긋나면(ε 초과) 즉시 멈춘다. 조용히 뒤틀린 결과를 내보내느니 낫다.

★전투 모션은 안 건드린다 (재검은 했다)
  Attack/Heavy/Wide 는 우리가 손으로 만든 것(combo_poses.py)이고 Jump 는 이식본이다.
  네이티브 원본에 대응물이 없으므로 그대로 둔다.
  대신 **왼손이 자루를 놓쳤는지**를 프레임마다 잰다([전투 파지 점검]). s24 이식의
  알려진 왜곡이 그거였기 때문이다. 실측 결과 왼손-자루축 거리는
      Idle 0.086 고정 / Attack 0.071~0.086 / Heavy 0.070~0.086 / Jump 0.086 고정
  로 손 두께(≈0.08m) 범위 안이다. Wide 만 54프레임 중 4프레임이 0.12 를 넘는데
  그건 s24 의 파지 게이트가 **일부러** 놓게 한 구간이다(횡일섬 중반 한손 놓기).
  즉 고칠 만한 왜곡이 없어서 이 스크립트는 전투를 손대지 않는다.

★칼 간섭이 이 교체의 유일한 위험이다
  네이티브 클립은 **빈손 기준**으로 만들어졌다. 그런데 kensa 의 칼 7자루는
  오른손 뼈에 100% 웨이트로 붙은 강체다(s26). 팔을 내리면 칼이 같이 내려온다.
  그래서 클립마다 프레임별로 두 가지를 실측한다:
      바닥 여유 = 칼 최저점이 **게임에서** 바닥 위 몇 m 인가
                  (게임은 매 프레임 가장 낮은 발 본을 바닥+charH*0.045 에 놓는다.
                   main.js groundFeet 와 같은 식으로 환산한다)
      몸 관통  = 칼 정점이 몸 표면 안쪽으로 몇 m 들어갔나 (BVH 최근접 + 법선 부호)
  기준을 넘으면 **그 클립에만** 오른손목 로컬 회전 보정 키를 얹는다.
  보정은 각도 격자 탐색으로 "기준을 통과하는 가장 작은 회전"을 고른다.
  다른 클립(전투)에는 절대 안 닿는다.

★표준 파이프라인 함정 (s13/s14/s24 에서 하나씩 밟아 본 것들)
  1) fps: 임포트 **전에** 30 고정. glb 는 초 단위다
  2) 이름 충돌: 소스 액션은 들어오자마자 SRC_ 접두. 안 그러면 우리 Idle 이 Idle.001 이
     되고 정리 루프가 그걸 지운다
  3) fcurve 데이터 경로: 소스는 Meshy 원명(Hips/LeftArm)을 가리킨다. 아마추어를 지운 뒤
     이름을 바꿔도 경로는 안 따라온다. **직접 고쳐야** T 포즈가 안 나온다
  4) 액션 슬롯(4.4+): 슬롯을 안 물리면 액션이 조용히 아무 일도 안 한다
  5) use_fake_user: 안 켜면 export 에서 조용히 빠진다
  6) 임포트 순서: **타깃(kensa)을 먼저** 읽는다. 나중에 읽으면 char1 이 char1.001 이
     되어 그대로 내보내진다(게임이 이름으로 칼을 찾는다)
  7) Icosphere: glTF 임포터가 뼈 표시용으로 만드는 반지름 1 구. 키 측정을 망친다

손잡이(환경변수)
  CLIPS      네이티브로 갈아끼울 클립  기본 Walk,Run  (Idle 은 위 이유로 뺐다)
  DST_GLB    타깃 = 결과            기본 web/kensa.glb (제자리 갱신)
  OUT_GLB    결과 경로 따로 줄 때   기본 DST_GLB 와 같다
  NAT_DIR    네이티브 클립 폴더     기본 incoming/meshy_slayer
  NAT_STEM   네이티브 파일 앞머리(= Meshy 모델 이름)
             기본 Meshy_AI_young_Korean_swordsma_biped
             ★다른 Meshy 캐릭터에 쓸 때 바꾸는 유일한 값이다(basic2 는
               NAT_DIR=incoming/meshy4/Meshy_AI_game_character_8k_biped
               NAT_STEM=Meshy_AI_game_character_8k_biped)
  NAT_IDLE   Idle 파일의 번호 부분  기본 Idle_14
  ARM_DAMP   오른팔 감쇠            기본 0.25 (1=원본 그대로, 0=평균에 고정)
  ARM_LIFT   오른팔 들기(도)        기본 0 (양수면 손이 올라간다. 칼끝을 지면 위로)
  LIFT_MODE  드는 축                기본 lean(옛 판) / **abd**(순수 벌림)
  LIFT_CLIPS 들기를 걸 클립         기본 = CLIPS (달리기는 빼는 게 낫다. 아래 참조)
             ★lean 은 팔이 기운 쪽으로 더 밀어 손을 올린다 = 뒤로 기운 클립에서는
               팔을 더 뒤로 뺀다. abd 는 몸 옆으로만 벌려 앞뒤 스윙과 독립이다.
  SWING_R    오른팔 목표 중립 스윙각(도)  빈 값(기본)=안 건드림. 0=수직 아래, +=앞
  SWING_L    왼팔 목표 중립 스윙각(도)    빈 값(기본)=안 건드림
  SWING_GF   왼팔 앞 스윙 이득       기본 1.0 (1=원본 진폭)
  SWING_GB   왼팔 뒤 스윙 이득       기본 1.0 (뒤로 덜 빼려면 0.6 처럼)
  SWING_H    두 이득이 갈리는 폭(도) 기본 12
  SWING_R_CLIPS / SWING_L_CLIPS  스윙 보정을 걸 클립  기본 = CLIPS
  WRIST_FIX  1(기본) 칼 간섭 보정 / 0 측정만 하고 안 고침
  TIP_ELEV   칼끝 평균 목표 고도(도) 기본 -35 (수평 아래로 내린다)
  TIP_FLAT   칼끝 고도 **진폭** 벌점(도당) 기본 0 (옛 판 = 평균만 본다)
             ★같은 평균이라도 후보에 따라 칼끝이 사이클 안에서 출렁이는 폭이 두 배씩
               다르다. 출렁이면 제일 낮은 프레임이 바닥여유를 다 먹는다.
  SW_NAME    측정 기준 칼           기본 SW_baekah (게임 기본 장착 칼)
  TIP_K      하류 칼끝 배율         기본 1.0 (s34 에서 커질 칼을 미리 넣는다)
  NCAND      비싼 검사를 돌릴 후보 수 기본 26
  CLEAR_MIN  바닥 여유 하한(m)      기본 0.02
  PEN_MAX    몸 관통 허용(m)        기본 0.025 (= 지금 출시본 Idle/Walk 수준)
  FIST_R     주먹 반경(m)           기본 0.15 (이 안쪽 관통은 '쥔 것'이라 안 센다)
  EXPORT     1(기본) 내보내기 / 0 측정만
  RENDER     1 이면 전후 비교 렌더   기본 0
  RENDER_ONLY loco / combat (쉼표)  기본 둘 다
  OUTDIR     렌더 폴더              기본 renders/history/v90_motion
  COMBAT_PEN 1 이면 전투 클립 칼 간섭도 잰다(진단만)  기본 0
  TEX_FORMAT/TEX_QUALITY           기본 AUTO / 90

★관통은 '주먹 안'과 '몸'을 갈라서 본다
  s26 이 칼을 주먹 터널에 비스듬히 꿰었으므로 자루가 주먹 살을 지나는 건 **정상**이다.
  문제는 자루/칼날이 **허리·허벅지**를 파고드는 것이다. 그래서 손목에서 FIST_R 밖의
  정점만 관통으로 센다. 실측 기준선(v90 이전 출시본): Walk 0.026 / Run 0.041.
  결과: Walk 0.033 / Run 0.015 (감쇠+손목 보정 후).

★'몸 안쪽인가'는 **광선 홀짝**으로 판정한다. 최근접면 법선 부호로 재면 오목한 자리
  (가랑이 사이·삿갓 챙 아래·겨드랑이)에서 거짓양성이 난다. 첫 시도에서 "칼이 몸속
  70cm" 같은 값이 나왔다(몸 두께가 30cm 인데). 홀짝으로 바꾸니 전부 5cm 대로 내려왔다.
  s26 이 주먹 구멍까지 덮어 닫힌 다양체로 만들어 놨기 때문에 홀짝이 성립한다.

★발 속도는 **모델 공간**에서 재라 (probe_stride.py 의 함정)
  probe_stride 는 발을 골반 기준으로 잰다. 그런데 게임은 모델 원점을 고정한 채
  root 만 미므로, 골반이 앞뒤로 출렁이는 클립에서는 그 출렁임이 값에 섞인다.
  이번 걷기에서 골반 기준 1.474 vs 모델 공간 1.570 으로 6% 벌어졌다. CHAR_CFG 에는
  모델 공간 값을 넣는다. 이 스크립트의 [접지 발 속도] 절은 둘 다 검산으로 찍는다.
  ★보폭x2/사이클 로 하는 검산은 **걷기에만** 유효하다. 달리기는 체공 구간이 있어
    (이 클립은 20프레임 중 10프레임이 체공) 그 식이 통째로 과소평가된다.
"""
import bpy
import os
import sys
import math
import json
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")
NAT_DIR = os.environ.get("NAT_DIR") or os.path.join(ROOT, "incoming", "meshy_slayer")
DST_GLB = os.environ.get("DST_GLB") or os.path.join(WEB, "kensa.glb")
OUT_GLB = os.environ.get("OUT_GLB") or DST_GLB
WRIST_FIX = os.environ.get("WRIST_FIX", "1") == "1"
CLEAR_MIN = float(os.environ.get("CLEAR_MIN", "0.02"))
PEN_MAX = float(os.environ.get("PEN_MAX", "0.025"))
SW_NAME = os.environ.get("SW_NAME", "SW_baekah")   # 측정 기준 칼
TIP_K = float(os.environ.get("TIP_K", "1.0"))      # 하류(s34)에서 칼끝이 몇 배가 되나
FIST_R = float(os.environ.get("FIST_R", "0.15"))
EXPORT = os.environ.get("EXPORT", "1") == "1"
RENDER = os.environ.get("RENDER", "0") == "1"
OUTDIR = os.environ.get("OUTDIR") or os.path.join(
    ROOT, "renders", "history", "v90_motion")
TEX_FORMAT = os.environ.get("TEX_FORMAT", "AUTO").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

# 게임이 정규화하는 키와 발바닥 두께(main.js CHAR_CFG.kensa.h / groundFeet)
GAME_H = 1.75
SOLE = 0.045                      # charH * 0.045 만큼 띄운다

# ★파일 이름은 Meshy 모델 이름을 앞머리로 쓴다. 기본값은 kensa 것이라
#   **다른 Meshy 캐릭터에 쓰려면 NAT_STEM 만 바꾸면 된다**(2026-08-11, basic2).
#     kensa   Meshy_AI_young_Korean_swordsma_biped
#     basic2  Meshy_AI_game_character_8k_biped     (NAT_DIR=incoming/meshy4/...)
NAT_STEM = os.environ.get("NAT_STEM", "Meshy_AI_young_Korean_swordsma_biped")
NAT_IDLE = os.environ.get("NAT_IDLE", "Idle_14")   # 모델마다 Idle 번호가 다르다
ALL_NATIVE = {                    # 우리 클립 이름 -> 원본 파일
    "Idle": "%s_Animation_%s_withSkin.glb" % (NAT_STEM, NAT_IDLE),
    "Walk": "%s_Animation_Walking_withSkin.glb" % NAT_STEM,
    "Run":  "%s_Animation_Running_withSkin.glb" % NAT_STEM,
}
# ★Idle 은 기본에서 뺐다. Meshy 의 "Idle_14" 는 이름만 Idle 이고 실제로는 **7.5초짜리
#   품새**다(칼을 머리 위로 들었다 내리고, 몸을 돌리고, f113 에서 하이킥까지 찬다.
#   골반이 앞뒤로 0.52m 움직인다 = 제자리 대기가 아니다). 서 있기만 해도 캐릭터가
#   혼자 발차기를 하는 화면이 된다. 렌더로 확인하고 뺐다(renders/history/v90_motion).
#   지금 Idle(양손 겨눔)은 게임에 맞으므로 그대로 둔다.
CLIPS = [c.strip() for c in os.environ.get("CLIPS", "Walk,Run").split(",") if c.strip()]
NATIVE = {k: v for k, v in ALL_NATIVE.items() if k in CLIPS}
KEEP = [c for c in ("Idle", "Attack", "Heavy", "Wide", "Jump") if c not in NATIVE]

# ★네이티브는 **빈손** 클립이라 오른팔이 100% 자유롭게 흔들린다. 그런데 우리 칼은
#   오른손 뼈에 붙은 1m 짜리 강체다. 그대로 두면 한 사이클마다 칼이 200도씩 도는
#   **풍차**가 된다(v90 1차 렌더에서 확인. 달리기 f008 에서 칼날이 정면으로 수평,
#   f013 에서 어깨 위로 곧추선다). 그래서 오른팔 4본만 자기 사이클 평균 자세 쪽으로
#   당긴다. 한 손에 뭘 들고 뛰면 그 팔은 원래 덜 흔든다 - 해부학적으로도 맞는 처리다.
#   왼팔·다리·척추는 **하나도 안 건드린다**(달리기의 생동감은 거기서 나온다).
ARM_DAMP = float(os.environ.get("ARM_DAMP", "0.30"))
# ★24차(2026-08-24): 클립별 감쇠 덮어쓰기 "Run:0.15". 빈 값(기본)이면 전 클립
#   ARM_DAMP 그대로 = 옛 판 재현. 대검 캐리는 달리기의 오른팔 잔여 스윙(±14도)을
#   더 눌러야 해서 만들었다 — 무거운 것을 든 팔은 흔들리지 않는다. 걷기는 18차
#   오너 지시로 튜닝된 판이라 한 도도 안 건드린다.
DAMP_TABLE = {}
for _row in os.environ.get("DAMP_TABLE", "").split(","):
    _row = _row.strip()
    if _row:
        _k, _v = _row.split(":")
        DAMP_TABLE[_k.strip()] = float(_v)
# 감쇠한 팔을 어깨에서 들어 올리는 각도(도). 0 이면 안 건드린다. 아래 [오른팔 들기] 참조.
ARM_LIFT = float(os.environ.get("ARM_LIFT", "0"))
# ★2026-08-12 오너 지시("걸을 때 팔을 너무 뒤로 뺀다") — 드는 **축**을 고른다.
#   lean 은 옛 판이다: 축 = (사이클 평균 팔방향) x 위. 팔이 이미 기울어 있는 쪽으로
#   더 밀어야 손이 올라가므로, 팔이 뒤로 기운 클립에서는 **팔을 더 뒤로 뺀다**
#   (실측: 걷기 오른팔 중립 스윙 -10.4도 -> -23.1도). 그게 오너가 본 그림이다.
#   abd 는 축 = 가슴 앞축이다. **순수 벌림**(몸 옆으로 벌리기)이라 앞뒤 스윙을
#   한 도도 안 건드리면서 손을 올린다. 그래서 아래 [팔 스윙] 과 서로 독립이다.
LIFT_MODE = os.environ.get("LIFT_MODE", "lean").strip().lower()
# 들기를 걸 클립(기본 = CLIPS 전부). 달리기는 팔이 이미 굽어 손목이 높아서 안 들어도
# 칼끝이 뜬다. 거기까지 들면 칼이 위를 보고 그만큼 손목 보정이 커져 손목만 꺾인다.
LIFT_CLIPS = [c.strip() for c in os.environ.get(
    "LIFT_CLIPS", ",".join(CLIPS)).split(",") if c.strip()]
DAMP_BONES = ["Bip001 R Clavicle", "Bip001 R UpperArm",
              "Bip001 R Forearm", "Bip001 R Hand"]

# ★2026-08-13 18차 오너 지시: **"걸을때 칼든손 왜이렇게 벌리고 걸음?"**
#   13-걷기팔이 남긴 그대로다 — 그 판은 팔을 뒤로 안 빼는 대신 **옆으로** 벌어야
#   손목 높이를 벌 수 있었다(ARM_LIFT=28 이 순수 벌림이다). 그때 적어 둔 처방이
#   "ARM_LIFT 를 줄이는 대신 팔꿈치를 굽히는 손잡이(지금 없다)" 였고, 이번에 만든다.
#   ARM_LIFT 만 줄이면 칼끝이 그만큼 내려간다(28->20 에서 여유 +0.150 -> +0.035).
#     ELB_R      오른 팔꿈치를 몇 도 더 굽히나(0 = 옛 판 재현). 팔뚝·손·칼이 함께 돈다
#     ELB_DIR    굽는 방향(도). 0 = 손이 **앞으로**(시상면 굴곡) · +90 = 손이 **안쪽으로**
#                ★★이 각이 이 작업의 전부다. 칼은 손의 강체 자식이라 팔꿈치를 굽히면
#                  **칼도 같은 회전을 먹는다.** 그런데 걷기의 칼은 거의 정면(앞)을
#                  겨누고 있어서, 굽히는 축이 '가슴 앞축'에 가까울수록(ELB_DIR=90)
#                  칼은 자기 축 둘레로 돌 뿐 **방향이 거의 안 변한다.**
#                  ELB_DIR=0(앞으로 굽힘)으로 크게 굽히면 칼끝 고도가 굽힌 만큼 올라가
#                  손목 보정이 그 각을 통째로 되갚아야 한다(손목이 꺾인다).
#     ELB_CLIPS  굽힘을 걸 클립(기본 = CLIPS). 달리기는 이미 75~88도 굽어 있다
ELB_R = float(os.environ.get("ELB_R", "0"))
ELB_DIR = float(os.environ.get("ELB_DIR", "60"))
ELB_CLIPS = [c.strip() for c in os.environ.get(
    "ELB_CLIPS", ",".join(CLIPS)).split(",") if c.strip()]
# 클립별 ARM_LIFT 덮어쓰기 "Walk:6,Run:28". 빈 값이면 전 클립 ARM_LIFT.
#   ★달리기는 한 도도 안 건드려야 해서(오너 지시 범위는 걷기) 표로 갈랐다.
LIFT_TABLE = {}
for _row in os.environ.get("LIFT_TABLE", "").split(","):
    _row = _row.strip()
    if _row:
        _k, _v = _row.split(":")
        LIFT_TABLE[_k.strip()] = float(_v)

# ★팔 스윙 자연화 (2026-08-12 오너 지시). 아래 [팔 스윙] 절 참조.
#   빈 값이면 그 팔을 안 건드린다(옛 판 재현 스위치).
SWING_R = os.environ.get("SWING_R", "").strip()      # 오른팔 목표 중립 스윙각(도)
SWING_L = os.environ.get("SWING_L", "").strip()      # 왼팔 목표 중립 스윙각(도)
SWING_GF = float(os.environ.get("SWING_GF", "1.0"))  # 왼팔 앞 스윙 이득
SWING_GB = float(os.environ.get("SWING_GB", "1.0"))  # 왼팔 뒤 스윙 이득
SWING_H = float(os.environ.get("SWING_H", "12"))     # 두 이득이 갈리는 폭(도)
SWING_R_CLIPS = [c.strip() for c in os.environ.get(
    "SWING_R_CLIPS", ",".join(CLIPS)).split(",") if c.strip()]
# ★18차: 오른팔 스윙을 **무엇으로 재나**. 기본 hand(옛 판) / elbow(위팔로 잰다).
#   ★17-점프왼팔 함정 1 의 걷기판이다. 팔꿈치를 굽히면 손목은 어깨->팔꿈치 선에서
#     벗어나므로, 손목을 목표에 맞추면 **위팔이 그만큼 뒤로 밀린다**(실측: 팔꿈치를
#     82도 굽히고 손목 중립을 +2 로 맞췄더니 위팔이 뒤로 30~53도 = 노 젓는 자세).
#     팔이 앞뒤로 어디 있나는 사람 눈에 **위팔**로 보인다. 그래서 기준을 고를 수 있게 했다.
SWING_R_REF = os.environ.get("SWING_R_REF", "hand").strip().lower()
SWING_R_REF_CLIPS = [c.strip() for c in os.environ.get(
    "SWING_R_REF_CLIPS", ",".join(CLIPS)).split(",") if c.strip()]
SWING_L_CLIPS = [c.strip() for c in os.environ.get(
    "SWING_L_CLIPS", ",".join(CLIPS)).split(",") if c.strip()]

# Meshy 원명 -> 우리 규칙(s13/s24 와 **같은 표**. 순서 중요, 긴 것부터)
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
NAMEMAP = dict(RENAME)
PELVIS = "Bip001 Pelvis"
HAND_R = "Bip001 R Hand"

print("=" * 78)
print("[설정] 타깃 %s" % DST_GLB)
print("       결과 %s" % OUT_GLB)
print("       네이티브 %s" % NAT_DIR)
print("       칼 보정 %s / 바닥여유>=%.3f / 관통<=%.3f / 내보내기 %s"
      % ("ON" if WRIST_FIX else "OFF", CLEAR_MIN, PEN_MAX, EXPORT))

# ================================================================ 1) 씬 준비
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30                # ★함정 1: 아무것도 읽기 전에
sc.render.fps_base = 1.0


def imp(path):
    b_o = set(o.name for o in sc.objects)
    b_a = set(a.name for a in bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in sc.objects if o.name not in b_o]
    acts = [a for a in bpy.data.actions if a.name not in b_a]
    # ★함정 7: 임포터가 만드는 뼈 표시용 구. glb 안에는 없다.
    for o in list(objs):
        if o.type == "MESH" and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o, do_unlink=True)
            objs.remove(o)
    return objs, acts


def fcs_of(act):
    """4.4+ 는 액션이 레이어/스트립/채널백 구조라 act.fcurves 가 비어 있다."""
    fcs = []
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    fcs.extend(cb.fcurves)
    except Exception:
        pass
    return fcs or list(act.fcurves)


def use(obj, act):
    """액션을 붙인다. ★함정 4: 슬롯이 없으면 조용히 아무 일도 안 한다."""
    if obj.animation_data is None:
        obj.animation_data_create()
    obj.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            obj.animation_data.action_slot = slots[0]
    except Exception:
        pass


# ================================================================ 2) 타깃 먼저
# ★함정 6: 타깃을 **먼저** 읽어야 char1 / SW_* 이름이 안 밀린다.
objsK, actsK = imp(DST_GLB)
armK = next(o for o in objsK if o.type == "ARMATURE")
body = next(o for o in objsK if o.type == "MESH" and not o.name.startswith("SW_"))
swords = [o for o in objsK if o.type == "MESH" and o.name.startswith("SW_")]
print("\n[타깃] %s 뼈 %d개 / 몸 %s / 칼 %d자루 %s"
      % (armK.name, len(armK.data.bones), body.name, len(swords),
         [o.name for o in swords]))
have = {a.name: a for a in actsK}
print("       액션 %s" % sorted(have))
for nm in list(NATIVE) + KEEP:
    if nm not in have:
        raise SystemExit("타깃에 %s 클립이 없다. 파이프라인 전제가 깨졌다." % nm)

# 옛 로코모션은 **비교 측정용으로 잠깐 살려 둔다**(내보내기 직전에 지운다).
for nm in NATIVE:
    have[nm].name = "OLD_" + nm
    have[nm].use_fake_user = True
old = {nm: bpy.data.actions["OLD_" + nm] for nm in NATIVE}

# ================================================================ 3) 네이티브 임포트
new = {}
for nm, fn in NATIVE.items():
    path = os.path.join(NAT_DIR, fn)
    if not os.path.exists(path):
        raise SystemExit("네이티브 원본이 없다: %s" % path)
    objs, fresh = imp(path)
    # ★함정 2: 들어오자마자 SRC_ 로 민다.
    for a in fresh:
        a.name = "SRC_" + a.name
    src_arm = next(o for o in objs if o.type == "ARMATURE")
    bound = src_arm.animation_data.action if src_arm.animation_data else None
    print("\n[%s] 새 액션 %d개 %s" % (nm, len(fresh), [a.name for a in fresh]))
    if len(fresh) > 1:
        # 숨은 clip0 함정(궁수에서 겪었다). 최장 클립이 진짜다.
        bound = max(fresh, key=lambda a: a.frame_range[1] - a.frame_range[0])
        print("    ★숨은 클립이 있다. 최장 클립을 쓴다: %s" % bound.name)
    if bound is None:
        raise SystemExit("%s: 아마추어에 붙은 액션이 없다" % nm)
    print("    아마추어에 붙은 것 = %s (프레임 %.1f~%.1f = %.3f초)"
          % (bound.name, bound.frame_range[0], bound.frame_range[1],
             (bound.frame_range[1] - bound.frame_range[0]) / 30.0))
    # 소스 아마추어의 레스트가 타깃과 같은지 **여기서 실측한다**
    worst_p = worst_a = 0.0
    for bn in src_arm.data.bones:
        tgt = NAMEMAP.get(bn.name, bn.name)
        bk = armK.data.bones.get(tgt)
        if bk is None:
            raise SystemExit("타깃에 뼈 %s(<-%s) 가 없다" % (tgt, bn.name))
        wN = src_arm.matrix_world @ bn.matrix_local
        wK = armK.matrix_world @ bk.matrix_local
        worst_p = max(worst_p, (wN.translation - wK.translation).length)
        for i in range(3):
            u = wN.col[i].to_3d().normalized()
            v = wK.col[i].to_3d().normalized()
            worst_a = max(worst_a, math.degrees(math.acos(max(-1, min(1, u.dot(v))))))
    print("    [레스트 대조] 최대 위치차 %.6f(아마추어단위) / 최대 축각차 %.3f도"
          % (worst_p, worst_a))
    if worst_p > 1e-3 or worst_a > 0.5:
        raise SystemExit("레스트가 다르다. fcurve 직접 이식이 성립하지 않는다.")
    new[nm] = bound
    bound.use_fake_user = True
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)

# ================================================================ 4) 경로 고치기
# ★함정 3. 이 단계가 빠지면 그 클립은 게임에서 **T 포즈**로 나온다.
def fix_paths(act):
    n = 0
    for fc in fcs_of(act):
        dp = fc.data_path
        if '"' not in dp:
            continue
        ob = dp.split('"')[1]
        nb = NAMEMAP.get(ob)
        if nb and nb != ob:
            fc.data_path = dp.replace('"%s"' % ob, '"%s"' % nb, 1)
            n += 1
    return n


print("\n[fcurve 경로]")
FIXED = {}
for nm in NATIVE:
    FIXED[nm] = fix_paths(new[nm])
    again = fix_paths(new[nm])
    print("  %-5s %3d개 수정 (재실행 %d개 = 0 이어야 정상)" % (nm, FIXED[nm], again))
    if again != 0:
        raise SystemExit("fix_paths 재실행에서 또 고쳐졌다 = 1차가 실패")
    if FIXED[nm] == 0:
        raise SystemExit("%s 의 경로가 하나도 안 고쳐졌다 = T 포즈 함정" % nm)
    new[nm].name = nm             # 이제 이름 충돌이 없다(옛것은 OLD_)
    new[nm].use_fake_user = True  # ★함정 5

# ================================================================ 5) 스케일 오염
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


print("\n[스케일 오염 점검] (궁수 골반 1.1765 사고의 재발 감시)")
for nm in sorted(list(NATIVE) + KEEP):
    act = new.get(nm) or bpy.data.actions[nm]
    r = scale_ranges(act)
    bad = {b: "%.4f~%.4f" % v for b, v in r.items() if v[0] < 0.999 or v[1] > 1.001}
    print("  %-7s 스케일 뼈 %2d개 / 비정상 %s" % (nm, len(r), bad or "없음"))
    if bad:
        raise SystemExit("스케일이 박힌 뼈가 있다: %s" % list(bad))

# ================================================================ 6) 측정 도구
# 게임이 쓰는 배율: 몸통 메시(SW_ 제외)의 바인드 박스 높이를 1.75 로 정규화
zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
BIND_H = max(zs) - min(zs)
SCALE = GAME_H / BIND_H
print("\n[배율] 바인드 키 %.4f -> 게임 키 %.2f (배율 %.4f)" % (BIND_H, GAME_H, SCALE))

FOOT_BONES = [b for b in armK.pose.bones
              if "foot" in b.name.lower() or "toe" in b.name.lower()]
print("       접지 판정 뼈 %d개 %s" % (len(FOOT_BONES), [b.name for b in FOOT_BONES]))

# 측정 칼. 기본은 게임 기본 장착(SWORDS[1] = baekah)이지만, 지금 시작 칼은
# 1번(nokseun)이고 그것만 s34 에서 1.5배가 된다 -> SW_NAME/TIP_K 로 지정한다.
SW = next((o for o in swords if o.name.startswith(SW_NAME)), swords[0])
if not SW.name.startswith(SW_NAME):
    print("       ★칼 %s 를 못 찾아 %s 로 잰다" % (SW_NAME, SW.name))
print("       측정 칼 %s (정점 %d) / 하류 칼끝 배율 TIP_K %.4f"
      % (SW.name, len(SW.data.vertices), TIP_K))


def ev_verts(obj):
    """평가된(스킨 적용) 정점을 월드로."""
    dg = bpy.context.evaluated_depsgraph_get()
    e = obj.evaluated_get(dg)
    me = e.to_mesh()
    mw = e.matrix_world
    out = [mw @ v.co for v in me.vertices]
    e.to_mesh_clear()
    return out


def ev_bvh(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    e = obj.evaluated_get(dg)
    me = e.to_mesh()
    mw = e.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    ps = [list(p.vertices) for p in me.polygons]
    e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps, all_triangles=False)


def low_foot():
    return min((armK.matrix_world @ b.matrix).translation.z for b in FOOT_BONES)


# 칼끝 정점 인덱스(손목에서 가장 먼 정점. main.js measureBlade 와 같은 기준)
armK.data.pose_position = "REST"
bpy.context.view_layer.update()
wrist = (armK.matrix_world @ armK.pose.bones[HAND_R].matrix).translation.copy()
_rv = [SW.matrix_world @ v.co for v in SW.data.vertices]
TIP_I = max(range(len(_rv)), key=lambda i: (_rv[i] - wrist).length_squared)
BLADE_L = (_rv[TIP_I] - wrist).length
# 손 뼈 로컬 칼끝(길이 포함). TIP_K 를 곱하면 하류에서 커질 칼의 **가상 칼끝**이다.
TIP_HL = (armK.matrix_world @ armK.pose.bones[HAND_R].matrix).inverted() @ _rv[TIP_I]
armK.data.pose_position = "POSE"
print("       칼끝 정점 #%d / 손목-칼끝 %.4f (게임 %.3f m)%s"
      % (TIP_I, BLADE_L, BLADE_L * SCALE,
         "  -> 하류 %.3f m" % (BLADE_L * TIP_K * SCALE) if TIP_K != 1.0 else ""))


# ★'몸 안쪽인가' 판정은 **광선 교차 횟수 홀짝**으로 한다. 최근접면 법선 부호로
#   재면 오목한 자리(가랑이 사이, 삿갓 챙 아래, 겨드랑이)에서 대놓고 거짓양성이
#   난다. 실제로 첫 시도에서 "칼이 몸속 70cm" 같은 값이 나왔다(몸 두께가 30cm 인데).
#   s26 이 주먹 구멍까지 덮어 **닫힌 다양체**로 만들어 놨으므로 홀짝 판정이 성립한다.
RAYS = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0.577, 0.577, 0.577))]


def _inside(bvh, p):
    votes = 0
    for d in RAYS:
        n, o = 0, p.copy()
        for _ in range(24):
            hit = bvh.ray_cast(o, d)
            if hit[0] is None:
                break
            n += 1
            o = hit[0] + d * 1e-5
        votes += n % 2
    return votes >= 2                    # 3방향 다수결(스치는 교차 방어)


def sword_state(nsub=120):
    """지금 프레임의 (바닥여유, 주먹밖 관통, 관통지점 손목거리, 관통 높이)."""
    lf = low_foot()
    HMw = armK.matrix_world @ armK.pose.bones[HAND_R].matrix
    w = HMw.translation
    sv = ev_verts(SW)
    lo = min(p.z for p in sv)
    if TIP_K != 1.0:                     # 하류에서 커질 칼끝(같은 반직선 위)
        lo = min(lo, (HMw @ (TIP_HL * TIP_K)).z)
    clear = (lo - lf) * SCALE + GAME_H * SOLE
    bvh = ev_bvh(body)
    pen, pw, ph = 0.0, 0.0, 0.0
    step = max(1, len(sv) // nsub)
    for p in sv[::step]:
        dw = (p - w).length * SCALE
        if dw <= FIST_R:                 # 주먹 안 = s26 이 일부러 꿰어 놓은 자리
            continue
        if not _inside(bvh, p):
            continue
        hit = bvh.find_nearest(p)
        if hit[0] is None:
            continue
        dep = (p - hit[0]).length * SCALE
        if dep > pen:
            pen, pw, ph = dep, dw, (p.z - lf) * SCALE + GAME_H * SOLE
    return clear, pen, pw, ph


def measure(act, label, sample=1):
    """한 클립을 프레임마다 돌며 칼 간섭과 접지를 잰다.

    바닥 여유 = (칼 최저z - 가장 낮은 발본 z) * 배율 + 1.75*0.045
                (게임 groundFeet 이 발 본을 바닥 위 0.079 에 놓으므로 그 기준)
    몸 관통  = 주먹 밖 칼 정점이 몸 표면 안쪽으로 들어간 깊이(게임 단위)
    """
    use(armK, act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    rows = []
    for f in range(f0, f1 + 1, sample):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        lf = low_foot()
        c, p, pw, ph = sword_state()
        mesh_lo = min(q.z for q in ev_verts(body))
        rows.append((f, c, p, pw, ph, (mesh_lo - lf) * SCALE, lf))
    cmin = min(r[1] for r in rows)
    pmax = max(r[2] for r in rows)
    rc = [r for r in rows if r[1] == cmin][0]
    rp = [r for r in rows if r[2] == pmax][0]
    # ★게임의 접지 규칙은 클립마다 다르다(main.js groundFeet). 달리기만 최근
    #   0.5초 창의 **최저 발**을 바닥으로 삼는다(체공 구간에 몸이 주저앉지 않게).
    #   그래서 달리기의 진짜 여유는 프레임 접지보다 이만큼 높다.
    base = min(r[6] for r in rows)
    ccyc = min(r[1] + (r[6] - base) * SCALE for r in rows)
    print("  %-10s %3d프레임  바닥여유 최소 %+.3f (f%d)  주먹밖관통 최대 %.3f "
          "(f%d, 손목거리 %.2f, 높이 %.2f)   [사이클접지 %+.3f]"
          % (label, len(rows), cmin, rc[0], pmax, rp[0], rp[3], rp[4], ccyc))
    return {"rows": rows, "clear": cmin, "pen": pmax, "fclear": rc[0],
            "fpen": rp[0], "penw": rp[3], "penh": rp[4], "cycle": ccyc}


def blade_arc(act, label=""):
    """칼이 한 사이클에 얼마나 휘젓는가. 세 가지를 잰다(전부 도).

    방향호 = 칼끝 방향(손목->칼끝)이 프레임끼리 벌어지는 최대 각
    롤    = 칼날 평면이 도는 각(같은 방향이라도 납작한 면이 90도 돌면 눈에 확 띈다)
    ★'이상하다'의 정체가 이 수치다. 빈손 클립의 팔은 한 사이클에 200도씩 돈다.
    """
    use(armK, act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    dirs, ups = [], []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        m = armK.matrix_world @ armK.pose.bones[HAND_R].matrix
        dirs.append((m.to_3x3() @ TIP_L).normalized())
        ups.append((m.to_3x3() @ FLAT_L).normalized())
    def spread_deg(vs):
        w = 0.0
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                w = max(w, math.degrees(math.acos(max(-1, min(1, vs[i].dot(vs[j]))))))
        return w
    a, r = spread_deg(dirs), spread_deg(ups)
    if label:
        print("  %-10s 칼 방향호 %5.1f도 / 칼날면 롤 %5.1f도" % (label, a, r))
    return a, r


# 칼끝 방향과 '칼날 납작한 면 법선'을 손 뼈 로컬로 미리 고정해 둔다(레스트에서 한 번).
# 법선은 칼날 정점 공분산의 **최소 고유벡터**다(s26 이 검을 꽂을 때 쓴 것과 같은 기준).
import numpy as np

armK.data.pose_position = "REST"
bpy.context.view_layer.update()
_hi = (armK.matrix_world @ armK.pose.bones[HAND_R].matrix).inverted()
_loc = [_hi @ p for p in _rv]
TIP_L = _loc[TIP_I].normalized()
_blade = np.array([[p.x, p.y, p.z] for p in _loc
                   if p.dot(TIP_L) > 0.35 * _loc[TIP_I].length])
_w, _v = np.linalg.eigh(np.cov((_blade - _blade.mean(0)).T))
FLAT_L = Vector(_v[:, 0]).normalized()
armK.data.pose_position = "POSE"
print("       칼 로컬축  칼끝 %s / 칼날면법선 %s"
      % (tuple(round(x, 3) for x in TIP_L), tuple(round(x, 3) for x in FLAT_L)))

# ---------------------------------------------------------------- 전투 파지 점검
# s24 이식의 알려진 왜곡은 **왼손이 자루에서 뜨는 것**이다(로그의 왼팔 정합 33도).
# 양손검 클립에서 왼손목이 자루축에서 얼마나 떨어졌는지 프레임마다 잰다.
# 자루축 = 오른손목에서 칼끝 방향으로 뻗은 직선. 제대로 쥐면 왼손목은 그 축에서
# 손 두께(~0.06m)만큼 떨어진 채, 오른손보다 **아래(t<0)** 에 있어야 한다.
def grip_check(act, label):
    use(armK, act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    ps, ts = [], []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        hm = armK.matrix_world @ armK.pose.bones[HAND_R].matrix
        ax = (hm.to_3x3() @ TIP_L).normalized()
        rw = hm.translation
        lw = (armK.matrix_world @ armK.pose.bones["Bip001 L Hand"].matrix).translation
        v = lw - rw
        t = v.dot(ax)
        ps.append((v - ax * t).length * SCALE)
        ts.append(t * SCALE)
    n = len(ps)
    bad = sum(1 for p in ps if p > 0.12)
    print("  %-8s %3d프레임  왼손-자루축 거리 %.3f~%.3f (평균 %.3f) / 축상 %.3f~%.3f"
          "  뜬 프레임 %d개%s"
          % (label, n, min(ps), max(ps), sum(ps) / n, min(ts), max(ts), bad,
             "  <<<" if bad > n * 0.25 else ""))
    return ps


print("\n[전투 파지 점검] 왼손이 자루를 쥐고 있나(0.12m 넘으면 뜬 것)")
for nm in ("Idle", "Attack", "Heavy", "Wide", "Jump"):
    if nm in bpy.data.actions:
        grip_check(bpy.data.actions[nm], nm)

# 전투 클립도 칼-몸 간섭을 같은 잣대로 재 둔다(이 스크립트는 안 고친다. 진단용).
if os.environ.get("COMBAT_PEN", "0") == "1":
    print("\n[전투 클립 칼 간섭] (진단만. 이 스크립트는 전투를 안 고친다)")
    for nm in ("Idle", "Attack", "Heavy", "Wide", "Jump"):
        if nm in bpy.data.actions:
            measure(bpy.data.actions[nm], nm, 2)

print("\n[칼 흔들림] 옛 클립 = 기준선")
for nm in NATIVE:
    blade_arc(old[nm], "OLD " + nm)
    blade_arc(new[nm], "NEW " + nm)

print("\n[칼 간섭 실측] (게임 단위 m. 바닥여유가 음수면 칼이 땅을 뚫는다)")
print("  * 옛 클립(리타게팅본) = 기준선")
M_OLD = {nm: measure(old[nm], "OLD " + nm, 2) for nm in NATIVE}
print("  * 새 클립(네이티브) 보정 전")
M_RAW = {nm: measure(new[nm], "NEW " + nm, 2) for nm in NATIVE}

# ================================================================ 7) 손목 보정
# 네이티브는 빈손 기준이라 팔을 내렸을 때 칼이 땅/다리를 파고들 수 있다.
# **그 클립에만** 오른손목 로컬 회전을 상수로 얹어 칼을 든다.
#   basis' = basis @ delta   (delta 는 뼈 로컬. 손의 자식인 칼이 손목을 축으로 돈다)
# 각도는 격자 탐색으로 "기준을 통과하는 가장 작은 회전"을 고른다.
AXES = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}


def hand_fcurves(act):
    got = {}
    for fc in fcs_of(act):
        if fc.data_path == 'pose.bones["%s"].rotation_quaternion' % HAND_R:
            got[fc.array_index] = fc
    return got


def apply_wrist(act, delta):
    """오른손목 rotation_quaternion 키 전부에 로컬 회전 delta 를 곱한다."""
    fcs = hand_fcurves(act)
    if len(fcs) != 4:
        raise SystemExit("오른손목 회전 채널이 4개가 아니다(%d)" % len(fcs))
    n = len(fcs[0].keyframe_points)
    for i in range(n):
        q = Quaternion([fcs[k].keyframe_points[i].co.y for k in range(4)])
        q = (q @ delta).normalized()
        for k in range(4):
            kp = fcs[k].keyframe_points[i]
            kp.co.y = kp.handle_left.y = kp.handle_right.y = q[k]
    for k in range(4):
        fcs[k].update()
    return n


def probe_wrist(act, delta, sample=0):
    """delta 를 **임시로** 걸고 최악값만 빠르게 잰다(키를 되돌린다).
    격자 탐색은 수십 번 돌므로 클립 길이에 맞춰 25프레임 정도로 성기게 본다."""
    fcs = hand_fcurves(act)
    saved = [[kp.co.y for kp in fcs[k].keyframe_points] for k in range(4)]
    apply_wrist(act, delta)
    use(armK, act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    if not sample:
        sample = max(1, (f1 - f0) // 25)
    cmin, pmax = 9e9, 0.0
    for f in range(f0, f1 + 1, sample):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        c, p, _, _ = sword_state(60)
        cmin = min(cmin, c)
        pmax = max(pmax, p)
    for k in range(4):
        for i, y in enumerate(saved[k]):
            kp = fcs[k].keyframe_points[i]
            kp.co.y = kp.handle_left.y = kp.handle_right.y = y
        fcs[k].update()
    return cmin, pmax


# ---------------------------------------------------------------- 오른팔 감쇠
def quat_fcurves(act, bone):
    got = {}
    for fc in fcs_of(act):
        if fc.data_path == 'pose.bones["%s"].rotation_quaternion' % bone:
            got[fc.array_index] = fc
    return got


def damp_arm(act, k):
    """오른팔 4본의 회전을 **자기 클립의 평균 자세** 쪽으로 당긴다(k=1 원본, 0 정지).
    평균은 부호를 맞춘 뒤(쿼터니언은 q 와 -q 가 같은 회전) 성분 평균 후 정규화한다."""
    out = []
    for bn in DAMP_BONES:
        fcs = quat_fcurves(act, bn)
        if len(fcs) != 4:
            print("       %s 회전 채널 %d개 = 건너뜀" % (bn, len(fcs)))
            continue
        n = len(fcs[0].keyframe_points)
        qs = []
        for i in range(n):
            q = Quaternion([fcs[c].keyframe_points[i].co.y for c in range(4)])
            if qs and q.dot(qs[0]) < 0:
                q.negate()
            qs.append(q)
        mean = Quaternion([sum(q[c] for q in qs) / n for c in range(4)]).normalized()
        swing = max(math.degrees(mean.rotation_difference(q).angle) for q in qs)
        for i in range(n):
            q = mean.slerp(qs[i], k)
            for c in range(4):
                kp = fcs[c].keyframe_points[i]
                kp.co.y = kp.handle_left.y = kp.handle_right.y = q[c]
        for c in range(4):
            fcs[c].update()
        out.append((bn, swing, swing * k))
    return out


# 회전만 당겨도 되는지 확인: 팔 뼈에 **움직이는 이동 채널**이 있으면 그건 안 잡힌다.
print("\n[오른팔 이동 채널] (상수여야 회전 감쇠만으로 충분하다)")
for nm in NATIVE:
    for bn in DAMP_BONES:
        rng = []
        for fc in fcs_of(new[nm]):
            if fc.data_path == 'pose.bones["%s"].location' % bn:
                vs = [k.co.y for k in fc.keyframe_points]
                rng.append(max(vs) - min(vs))
        if rng and max(rng) > 1e-4:
            print("  %-5s %-20s 이동 변화 %.5f  <<< 상수가 아니다" % (nm, bn, max(rng)))
print("  (출력 없음 = 전부 상수)")

if ARM_DAMP < 1.0 or DAMP_TABLE:
    print("\n[오른팔 감쇠] 계수 %.2f%s (0=평균에 고정, 1=원본 그대로)"
          % (ARM_DAMP,
             " / 클립별 %s" % DAMP_TABLE if DAMP_TABLE else ""))
    for nm in NATIVE:
        # ★24차: DAMP_TABLE 이 그 클립을 덮으면 그 값, 아니면 ARM_DAMP(옛 판 그대로)
        for bn, s0, s1 in damp_arm(new[nm], DAMP_TABLE.get(nm, ARM_DAMP)):
            print("  %-5s %-20s 평균에서 최대 %.1f도 -> %.1f도" % (nm, bn, s0, s1))
    print("\n[칼 흔들림] 감쇠 후")
    for nm in NATIVE:
        blade_arc(new[nm], "DMP " + nm)
    print("\n[칼 간섭 실측] 오른팔 감쇠 후")
    M_RAW = {nm: measure(new[nm], "DMP " + nm, 2) for nm in NATIVE}

# ---------------------------------------------------------------- 오른팔 들기
# ★2026-08-12. 1번 칼이 1.5배(손목-칼끝 x1.7806)가 되면서 **칼끝이 지면 아래**로
#   내려갔다(실측: 걷기 -0.168 / 달리기 -0.470). 원인은 칼이 아니라 이 클립들의
#   오른팔 각도다 — 빈손 달리기의 팔은 아래로 내려 붙고, 감쇠는 그 평균 자세를
#   그대로 굳히기 때문에 1.6m 짜리 칼을 들면 날이 땅에 눕는다.
#   그래서 감쇠한 팔을 **어깨에서 통째로 들어 올린다.** 손목 보정(칼만 돌리기)과
#   나눠 쓰는 이유: 칼만 들면 자루가 하늘을 보고 손목이 꺾인 그림이 되고,
#   팔만 들면 클립의 팔 흔들림이 그대로 남아 프레임마다 칼끝 높이가 출렁인다.
#   둘을 같이 쓰면 '무거운 칼을 든 채 달리는' 자세가 된다.
#
# ★축은 **한 클립에 하나**다(프레임마다 다시 잡으면 안 된다)
#   축 a = (어깨->손목의 사이클 평균) x 월드up. 이 축으로 +θ 돌리면 손이 올라간다.
#   ★★프레임마다 축을 다시 잡아 봤는데 **칼 방향호가 41 -> 48도로 늘었다.**
#     프레임마다 다른 회전을 먹이면 그 차이가 그대로 칼끝 궤적의 벌어짐이 되기
#     때문이다. 모든 프레임에 **같은 월드 회전**을 먹이면 방향호는 등거리라
#     한 도도 안 변한다(실측으로 확인). 그래서 축·각을 클립당 상수로 고정한다.
#   회전은 월드에서 정의하고 뼈 로컬 델타로 환산해 위팔 키에 곱한다:
#       basis' = P^-1 @ R_world @ P @ basis     (P = 이 프레임의 '기저 앞' 월드회전)
#   팔뚝·손·칼은 FK 자식이라 강체로 따라온다.
UPPER_R = "Bip001 R UpperArm"
UPPER_L = "Bip001 L UpperArm"
HAND_L = "Bip001 L Hand"
TORSO, NECK = "Bip001 Spine", "Bip001 Neck"       # ★Meshy 리그는 척추 이름이 뒤집혀
CLAV_L, CLAV_R = "Bip001 L Clavicle", "Bip001 R Clavicle"   #  있다. 쇄골이 달린
#   윗마디가 'Bip001 Spine' 이다(실측 계층 Pelvis->Chest2->Chest->Spine->Clavicle).
#   이름만 보고 Chest2 를 잡으면 배꼽에 좌표계를 매다는 셈이다.


def bwpos(bn):
    return (armK.matrix_world @ armK.pose.bones[bn].matrix).translation.copy()


def key_frames(act, bone):
    fcs = quat_fcurves(act, bone)
    if len(fcs) != 4:
        raise SystemExit("%s 회전 채널이 4개가 아니다(%d)" % (bone, len(fcs)))
    return fcs, [int(round(k.co.x)) for k in fcs[0].keyframe_points]


def chest_axes(act):
    """이 클립 **사이클 평균**의 가슴 좌표계 (왼쪽 / 위 / 앞). 월드 상수 셋이다.
    프레임마다 다시 잡으면 회전이 프레임마다 달라져 칼 방향호가 벌어진다."""
    use(armK, act)
    _, frames = key_frames(act, UPPER_R)
    au, al = Vector((0, 0, 0)), Vector((0, 0, 0))
    for f in frames:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        up = (bwpos(NECK) - bwpos(TORSO)).normalized()
        lat = bwpos(CLAV_L) - bwpos(CLAV_R)
        au += up
        al += (lat - up * lat.dot(up)).normalized()
    up = au.normalized()
    lat = (al - up * al.dot(up)).normalized()
    return lat, up, lat.cross(up)


def apply_world_rot(act, bone, Rs):
    """위팔 키 전부에 **월드 회전**을 먹인다(프레임 i 에 Rs[i]).
        basis' = P^-1 @ R_world @ P @ basis     (P = 이 프레임의 '기저 앞' 월드회전)
    회전축이 뼈 머리(어깨)를 지나므로 팔뚝·손·칼은 FK 자식으로 **강체**로 따라온다.
    ★Rs 가 전부 같은 회전이면 칼 방향호는 한 도도 안 변한다(등거리 사상)."""
    fcs, frames = key_frames(act, bone)
    use(armK, act)
    pb = armK.pose.bones[bone]
    n = len(frames)
    # 프레임마다 로컬 델타로 환산해서 모아 둔다(★먼저 다 읽고 나중에 쓴다)
    out = []
    for i, f in enumerate(frames):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        Mw = (armK.matrix_world @ pb.matrix).to_3x3()
        Mw.normalize()
        B = pb.matrix_basis.to_3x3()
        B.normalize()
        P = Mw @ B.inverted()                   # 기저 앞 월드 회전
        out.append((P.inverted() @ Rs[i] @ P @ B).to_quaternion().normalized())
    prev = None
    for i, q in enumerate(out):
        if prev is not None and q.dot(prev) < 0:   # 쿼터니언 부호 연속성
            q.negate()
        prev = q
        for c in range(4):
            kp = fcs[c].keyframe_points[i]
            kp.co.y = kp.handle_left.y = kp.handle_right.y = q[c]
    for c in range(4):
        fcs[c].update()
    return n


def lift_arm(act, deg):
    """오른 위팔 키 전부를 '손이 올라가는 방향'으로 deg 만큼 돌린다."""
    use(armK, act)
    pb = armK.pose.bones[UPPER_R]
    _, frames = key_frames(act, UPPER_R)
    # 1차: 사이클 평균 팔 방향으로 축을 정한다
    acc = Vector((0, 0, 0))
    for f in frames:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        S = (armK.matrix_world @ pb.matrix).translation
        W = (armK.matrix_world @ armK.pose.bones[HAND_R].matrix).translation
        acc += (W - S).normalized()
    if LIFT_MODE == "abd":
        # ★순수 벌림: 축 = 가슴 앞축. 앞뒤 스윙을 안 건드리고 몸 옆으로만 든다.
        #   부호는 '팔이 몸에서 멀어지는 쪽'을 실측으로 고른다(리그 좌우 무관).
        lat, _up, fwd = chest_axes(act)
        d = acc.normalized()
        out0 = -d.dot(lat)                      # 오른팔은 왼쪽축의 반대가 바깥
        ax = fwd.normalized()
        if -(Matrix.Rotation(math.radians(1), 3, ax) @ d).dot(lat) < out0:
            ax = -ax
    else:
        # lean(옛 판): 축 = 평균 팔방향 x 위. 팔이 기운 쪽으로 더 밀어 손을 올린다
        #   -> 뒤로 기운 클립에서는 팔을 더 뒤로 뺀다(오너 지적의 절반이 이것이다)
        ax = acc.normalized().cross(Vector((0, 0, 1)))
    if ax.length < 1e-4:
        raise SystemExit("팔이 정확히 수직이라 드는 축을 못 잡는다")
    Rw = Matrix.Rotation(math.radians(deg), 3, ax.normalized())
    n = apply_world_rot(act, UPPER_R, [Rw] * len(frames))
    return n, ax.normalized()


# ------------------------------------------------------------- 팔꿈치 굽힘(18차)
# ★2026-08-13 오너 지시 "걸을때 칼든손 왜이렇게 벌리고 걸음?"
#   실측(probe_armswing, committed fc74fee3): 걷기 오른팔은 **위팔 외전 56.3도**에
#   **팔꿈치 굽힘 10~15도** = 벌린 채 곧게 편 팔이다. 왼팔(=이 리그의 자연 보행)은
#   위팔 외전 23.3도다. 그 33도를 어디서 갚느냐가 이 절이다.
#     손목 높이 = 어깨높이 - |어깨->손목| x cos(팔각).  |어깨->손목| 0.614m 이라
#     외전을 56 -> 21 도로 내리면 손목이 **0.217m** 내려간다(칼끝도 같이 내려간다).
#   팔꿈치를 굽히면 손목이 어깨 쪽으로 당겨져 그 높이를 되번다. 벌림과 달리
#   **몸 옆으로 벌어지는 그림이 아니다** — 그래서 오너 지적이 사라진다.
FORE_R = "Bip001 R Forearm"


def arm_report(act, label):
    """굽는 자리에서 **실제로 나온** 오른팔 각을 찍는다(목표가 아니라 결과).

    ★probe_armswing.py 와 **같은 잣대**다: 가슴 좌표계, 0=수직 아래.
      위팔 벌림 = 어깨->**팔꿈치**  (17-점프왼팔 함정 1: 손목으로 재면 틀린다)
      손목 벌림 = 어깨->손목        (13-걷기팔이 40.6->50.7 로 적은 그 값)
    """
    use(armK, act)
    lat, up, fwd = chest_axes(act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    ua, wa, fx, hz, wr = [], [], [], [], []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        S, E, W = bwpos(UPPER_R), bwpos(FORE_R), bwpos(HAND_R)
        for v, out in ((E - S, ua), (W - S, wa)):
            out.append(math.degrees(math.atan2(-v.dot(lat), -v.dot(up))))
        fx.append(math.degrees((E - S).angle(W - E)))
        hz.append(W.z)
        # 손목 꺾임 **기하각**: 팔뚝 방향 vs 손뼈 방향(뼈 로컬 Y 가 뼈를 따라간다).
        # ★13-손목 함정: 손목 보정을 **비틀림 축**으로 주면 이 각이 안 늘어난다.
        hm = (armK.matrix_world @ armK.pose.bones[HAND_R].matrix).to_3x3()
        hm.normalize()
        wr.append(math.degrees((hm @ Vector((0, 1, 0))).angle(W - E)))
    ua.sort()
    wa.sort()
    print("  %-10s 위팔벌림 중앙 %+5.1f (%+.1f~%+.1f) · 손목벌림 중앙 %+5.1f"
          " · 팔꿈치 %.1f~%.1f · 손목꺾임 %.1f~%.1f도 · 손목높이 %.3f~%.3f"
          % (label, ua[len(ua) // 2], ua[0], ua[-1], wa[len(wa) // 2],
             min(fx), max(fx), min(wr), max(wr), min(hz), max(hz)))
    return ua[len(ua) // 2], wa[len(wa) // 2]


def bend_elbow(act, deg, dirdeg):
    """오른 팔꿈치를 deg 만큼 **더** 굽힌다. 팔뚝·손·칼이 강체로 따라온다.

    축은 **클립당 하나**다(프레임마다 다시 잡으면 칼 방향호가 벌어진다 —
    위 [오른팔 들기] 의 함정과 같은 이유). 축 = (사이클 평균 위팔) x (손이 갈 쪽).
    ★이 축이 곧 사람 팔꿈치의 경첩축이다(위팔에 수직 = 팔뚝만 접힌다).
    """
    use(armK, act)
    _, frames = key_frames(act, FORE_R)
    lat, _up, fwd = chest_axes(act)
    acc = Vector((0, 0, 0))
    flex0 = []
    for f in frames:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        S, E, W = bwpos(UPPER_R), bwpos(FORE_R), bwpos(HAND_R)
        acc += (E - S).normalized()
        flex0.append(math.degrees((E - S).angle(W - E)))
    u = acc.normalized()
    # 손이 가고 싶은 쪽. 0 = 가슴 **앞** · +90 = 몸 **안쪽**(오른팔의 안쪽이 +lat 다)
    t = (fwd * math.cos(math.radians(dirdeg))
         + lat * math.sin(math.radians(dirdeg)))
    t = t - u * t.dot(u)
    if t.length < 1e-5:
        raise SystemExit("팔꿈치 굽힘 목표가 위팔과 나란하다(ELB_DIR 을 바꿔라)")
    ax = u.cross(t.normalized()).normalized()      # +각 = 손이 t 쪽으로 간다
    n = apply_world_rot(act, FORE_R, [Matrix.Rotation(math.radians(deg), 3, ax)]
                        * len(frames))
    flex1 = []
    for f in frames:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        S, E, W = bwpos(UPPER_R), bwpos(FORE_R), bwpos(HAND_R)
        flex1.append(math.degrees((E - S).angle(W - E)))
    return n, ax, (min(flex0), max(flex0)), (min(flex1), max(flex1))


if ELB_R or LIFT_TABLE:
    print("\n[팔 각도 실측] 감쇠 직후 (0=수직 아래 · 양수=몸 바깥. 손목높이는 블렌더 단위)")
    for nm in NATIVE:
        arm_report(new[nm], "DMP " + nm)

if ELB_R:
    print("\n[팔꿈치 굽힘] %+.1f 도 (방향 %+.0f도: 0=앞 90=안쪽. 팔뚝·손·칼이 따라온다)"
          % (ELB_R, ELB_DIR))
    for nm in NATIVE:
        if nm not in ELB_CLIPS:
            print("  %-5s 건너뜀(ELB_CLIPS 밖)" % nm)
            continue
        n, ax, f0, f1 = bend_elbow(new[nm], ELB_R, ELB_DIR)
        print("  %-5s 팔뚝 키 %d개 / 축 (%+.3f,%+.3f,%+.3f) / 팔꿈치각 %.1f~%.1f -> "
              "**%.1f~%.1f도**" % (nm, n, ax.x, ax.y, ax.z, f0[0], f0[1], f1[0], f1[1]))
    print("\n[칼 흔들림] 팔꿈치 굽힘 후")
    for nm in NATIVE:
        blade_arc(new[nm], "ELB " + nm)
        arm_report(new[nm], "ELB " + nm)
    print("\n[칼 간섭 실측] 팔꿈치 굽힘 후")
    M_RAW = {nm: measure(new[nm], "ELB " + nm, 2) for nm in NATIVE}

if ARM_LIFT or LIFT_TABLE:
    print("\n[오른팔 들기] %+.1f 도%s (어깨에서. 손·칼은 강체로 따라온다) 축=%s"
          % (ARM_LIFT,
             (" / 클립별 " + " ".join("%s=%g" % kv for kv in LIFT_TABLE.items()))
             if LIFT_TABLE else "", LIFT_MODE))
    for nm in NATIVE:
        if nm not in LIFT_CLIPS:
            print("  %-5s 건너뜀(LIFT_CLIPS 밖)" % nm)
            continue
        deg = LIFT_TABLE.get(nm, ARM_LIFT)
        if abs(deg) < 1e-9:
            print("  %-5s 건너뜀(들기 0도)" % nm)
            continue
        n, ax = lift_arm(new[nm], deg)
        print("  %-5s %+.1f도 / 위팔 키 %d개 / 축 (%+.3f,%+.3f,%+.3f)"
              % (nm, deg, n, ax.x, ax.y, ax.z))
    print("\n[칼 흔들림] 팔 들기 후")
    for nm in NATIVE:
        blade_arc(new[nm], "LFT " + nm)
    print("\n[칼 간섭 실측] 팔 들기 후")
    M_RAW = {nm: measure(new[nm], "LFT " + nm, 2) for nm in NATIVE}

# ---------------------------------------------------------------- 팔 스윙 자연화
# ★2026-08-12 오너 지시: **"걸을 때 팔을 너무 뒤로 뺀다."** 실측으로 원인이 둘이었다
#   (가슴 좌표계 스윙각. 0=수직 아래, 양수=앞. 걷기):
#
#                          앞최대   뒤최대   중립    앞/뒤
#       네이티브 왼팔      +26.6    -45.4   -9.4    0.59   <- 원본이 원래 뒤로 크게 뺀다
#       네이티브 오른팔    +19.2    -40.0  -10.4    0.48
#       우리 오른팔(전)    -15.4    -30.8  -23.1     -     <- 한 사이클 내내 몸 뒤에 있다
#
#   사람 걷기는 앞 스윙(어깨 굴곡 20~25도)이 뒤 스윙(신전 10~20도)보다 크거나 비슷하다.
#   원본이 이미 뒤로 치우쳐 있었고, 거기에 우리 ARM_LIFT(lean 축)가 오른팔을 12.7도
#   **더 뒤로** 밀었다. 그래서 둘을 다 푼다.
#
# ★리프트와 스윙을 **다른 축으로 갈라 놓는 것**이 이 절의 핵심이다.
#   칼끝이 지면 아래로 안 내려가게 하는 것은 손목 높이인데(손목 높이 = 팔이 수직에서
#   얼마나 벗어났나), 옛 lean 축은 그 '벗어남'을 뒤쪽으로만 벌 수 있었다.
#   LIFT_MODE=abd 로 **옆으로 벌려** 높이를 벌면, 앞뒤 스윙은 공짜로 자유로워진다.
#
# ★오른팔은 **상수 회전 하나**만 쓴다(중립점 이동). 프레임마다 다른 각을 먹이면
#   그 차이가 그대로 칼 방향호가 된다(위 [오른팔 들기] 함정). 감쇠 뒤 오른팔 진폭은
#   걷기 15도라 뒤 스윙 상한을 따로 걸 필요도 없다.
# ★왼팔은 칼이 없으니 프레임별로 모양을 바꿔도 된다. 앞/뒤 이득을 갈라 준다:
#       s' = mid + a * (gm + gd*tanh(a/h)),  a = s - mid0, gm=(gf+gb)/2, gd=(gf-gb)/2
#   tanh 라 이득이 갈리는 지점에 꺾임이 없다(C-무한). 계단식으로 자르면 중립을
#   지나는 순간 팔 속도가 툭 튄다.


def swing_arm(act, bone, hand, target_mid, gf, gb, h, axes):
    """팔의 앞뒤 스윙을 다시 그린다. 반환 (전 (앞,뒤,중립), 후 (앞,뒤,중립), 상수냐)."""
    lat, up, fwd = axes
    ax = -lat                                   # 이 축으로 +각 = 팔이 **앞으로**
    use(armK, act)
    _, frames = key_frames(act, bone)
    pb = armK.pose.bones[bone]

    def swings():
        out = []
        for f in frames:
            sc.frame_set(f)
            bpy.context.view_layer.update()
            d = ((armK.matrix_world @ armK.pose.bones[hand].matrix).translation
                 - (armK.matrix_world @ pb.matrix).translation)
            out.append(math.degrees(math.atan2(d.dot(fwd), -d.dot(up))))
        return out

    s0 = swings()
    mid0 = (max(s0) + min(s0)) / 2.0
    gm, gd = (gf + gb) / 2.0, (gf - gb) / 2.0
    const = abs(gf - 1.0) < 1e-9 and abs(gb - 1.0) < 1e-9
    degs = []
    for s in s0:
        a = s - mid0
        g = gm + gd * math.tanh(a / h) if not const else 1.0
        degs.append(target_mid + a * g - s)
    apply_world_rot(act, bone, [Matrix.Rotation(math.radians(d), 3, ax)
                                for d in degs])
    s1 = swings()
    return ((max(s0), min(s0), mid0), (max(s1), min(s1),
            (max(s1) + min(s1)) / 2.0), const)


if SWING_R or SWING_L:
    print("\n[팔 스윙 자연화] 목표 중립  오른 %s / 왼 %s   왼팔 이득 앞 %.2f 뒤 %.2f "
          "(전환폭 %.0f도)" % (SWING_R or "-", SWING_L or "-", SWING_GF, SWING_GB,
                            SWING_H))
    print("  %-5s %-4s | %-24s | %-24s | %s"
          % ("클립", "팔", "전 앞/뒤/중립", "후 앞/뒤/중립", "회전"))
    for nm in NATIVE:
        axes = chest_axes(new[nm])
        r_end = (FORE_R if (SWING_R_REF == "elbow" and nm in SWING_R_REF_CLIPS)
                 else HAND_R)
        for tgt, bone, hand, clips, gf, gb in (
                (SWING_R, UPPER_R, r_end, SWING_R_CLIPS, 1.0, 1.0),
                (SWING_L, UPPER_L, HAND_L, SWING_L_CLIPS, SWING_GF, SWING_GB)):
            if not tgt or nm not in clips:
                continue
            b4, af, const = swing_arm(new[nm], bone, hand, float(tgt),
                                      gf, gb, SWING_H, axes)
            print("  %-5s %-4s | %+7.1f %+7.1f %+7.1f | %+7.1f %+7.1f %+7.1f | %s"
                  % (nm, "오른" if bone == UPPER_R else "왼",
                     b4[0], b4[1], b4[2], af[0], af[1], af[2],
                     "상수 %+.1f도" % (af[2] - b4[2]) if const else "프레임별"))
    print("\n[칼 흔들림] 스윙 자연화 후")
    for nm in NATIVE:
        blade_arc(new[nm], "SWG " + nm)
        if ELB_R or LIFT_TABLE:
            arm_report(new[nm], "SWG " + nm)
    print("\n[칼 간섭 실측] 스윙 자연화 후")
    M_RAW = {nm: measure(new[nm], "SWG " + nm, 2) for nm in NATIVE}

# ---------------------------------------------------------------- 손목 보정
# ★목표를 '기준 통과'가 아니라 **칼을 든 각도**로 준다.
#   감쇠만 하면 칼이 사이클 평균 방향에 그대로 굳는데, 실측하면 그 평균이 걷기에서
#   **정면 수평**이다(창을 든 것처럼 1m 짜리 날이 앞으로 튀어나온다. 탑다운 시점에서
#   실루엣을 크게 망치고 벽·요괴와 겹친다). 칼을 든 채 걷는 사람은 날을 내린다.
#   그래서 '칼끝 평균 고도 = TIP_ELEV(기본 -35도, 수평 아래)' 를 목표로 잡고
#   그걸 만드는 **가장 작은 손목 회전**을 고른다. 바닥여유·관통은 통과 조건으로 건다.
# ★탐색이 싼 이유: 고도는 메시를 안 봐도 된다(손 뼈 행렬만 있으면 된다).
#   프레임별 손 행렬을 한 번만 모아 두면 후보 수천 개를 즉시 평가할 수 있다.
#   비싼 검사(바닥·관통)는 고도 조건을 통과한 상위 몇 개에만 돌린다.
TIP_ELEV = float(os.environ.get("TIP_ELEV", "-35"))
# 클립별 TIP_ELEV 덮어쓰기 "Walk:-20". 빈 값이면 전 클립 TIP_ELEV(달리기 무변경용).
TIP_TABLE = {}
for _row in os.environ.get("TIP_TABLE", "").split(","):
    _row = _row.strip()
    if _row:
        _k, _v = _row.split(":")
        TIP_TABLE[_k.strip()] = float(_v)
NCAND = int(os.environ.get("NCAND", "26"))   # 비싼 검사를 돌릴 후보 수
# ★칼끝 고도 **진폭**에 주는 벌점(도당). 기본 0 = 옛 판(평균만 본다).
#   같은 평균 고도라도 후보에 따라 사이클 안에서 칼끝이 위아래로 출렁이는 폭이
#   두 배씩 다르다. 출렁이면 (1) 눈에 칼이 펄럭이고 (2) **제일 낮은 프레임**이
#   바닥여유를 결정하므로 평균을 더 내릴 여지도 사라진다. 그래서 진폭을 같이 본다.
TIP_FLAT = float(os.environ.get("TIP_FLAT", "0"))
# ★18차: 후보를 구면 균등으로 넓힌다. 0(기본) = 옛 격자 그대로 = 커밋본 재현.
#   ★**클립 이름을 적으면 그 클립만** 넓힌다("Walk"). 1 이면 전 클립.
#     달리기는 한 도도 안 바꿔야 해서(오너 지시 범위는 걷기) 이 갈래가 필요하다.
_WW = os.environ.get("WRIST_WIDE", "0").strip()
WRIST_WIDE = _WW not in ("", "0")
WIDE_CLIPS = [c.strip() for c in _WW.split(",") if c.strip() and c.strip() != "1"]
WRIST_MAX = float(os.environ.get("WRIST_MAX", "120"))   # 넓힐 때의 회전량 상한(도)


def hand_mats(act):
    use(armK, act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    ms = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        ms.append((armK.matrix_world @ armK.pose.bones[HAND_R].matrix).to_3x3())
    return ms


def mean_elev(mats, delta):
    """delta 를 걸었을 때 칼끝 방향의 **평균 고도**(도). +위 / -아래."""
    acc = Vector((0, 0, 0))
    for m in mats:
        acc += (m @ (delta.to_matrix() @ TIP_L)).normalized()
    d = acc.normalized()
    return math.degrees(math.asin(max(-1, min(1, d.z))))


def elev_span(mats, delta):
    """delta 를 걸었을 때 칼끝 고도가 사이클 안에서 벌어지는 폭(도)."""
    es = []
    for m in mats:
        d = (m @ (delta.to_matrix() @ TIP_L)).normalized()
        es.append(math.degrees(math.asin(max(-1, min(1, d.z)))))
    return max(es) - min(es)


def cand_deltas(wide=False):
    """후보: 단축 회전 + 2축 조합. 작은 각부터 훑는다."""
    out = [(0.0, "없음", Quaternion())]
    degs = list(range(5, 91, 5)) + list(range(-5, -91, -5))
    for an, ax in AXES.items():
        for d in degs:
            out.append((abs(d), "%s %+d도" % (an, d), Quaternion(ax, math.radians(d))))
    for d1 in range(-60, 61, 15):
        for d2 in range(-60, 61, 15):
            if d1 and d2:
                out.append((abs(d1) + abs(d2), "X%+d/Z%+d" % (d1, d2),
                            Quaternion(AXES["X"], math.radians(d1))
                            @ Quaternion(AXES["Z"], math.radians(d2))))
    # ── ★18차 신설: 구면 균등 후보 (WRIST_WIDE=1. 기본 0 = 옛 격자 그대로) ──
    # 왜 넓혀야 했나. 팔꿈치 굽힘은 팔뚝에 **월드 상수 회전**을 먹이는 일이라
    # 칼끝 방향 다발(사이클 41도짜리 호)을 통째로 기울인다. 커밋본이 6.1도까지
    # 눕혀 놓았던 그 호가 팔꿈치 80도만큼 세워지면 고도폭이 34도가 된다
    # (실측: 커밋본 6.1 -> 팔꿈치판 31~37). 그 기울기를 되눕히는 회전은
    # 세 축 격자(±90, 15도 조합)의 **밖**에 있다 — 그래서 후보가 아예 없었다.
    # 축을 구면에 고르게 뿌리면(피보나치) 그 회전이 후보 안에 들어온다.
    # ★회전량 상한(WRIST_MAX)을 두는 이유: 손목은 사람 관절이다. 다만 축이
    #   **손뼈 길이축(비틀림)** 에 가까우면 큰 각도 손목이 안 꺾인다(13-손목 함정).
    if wide:
        n = 96
        ga = math.pi * (3.0 - math.sqrt(5.0))
        for i in range(n):
            z = 1.0 - 2.0 * (i + 0.5) / n
            r = math.sqrt(max(0.0, 1.0 - z * z))
            ax = Vector((r * math.cos(ga * i), r * math.sin(ga * i), z)).normalized()
            for d in range(10, int(WRIST_MAX) + 1, 10):
                out.append((float(d), "구면%02d %+d도" % (i, d),
                            Quaternion(ax, math.radians(d))))
    return sorted(out, key=lambda t: t[0])


WRIST_USED = {}
if WRIST_FIX:
    print("\n[손목 보정] 목표: 칼끝 평균 고도 %+.0f도 / 바닥여유>=%.3f / 관통<=%.3f"
          % (TIP_ELEV, CLEAR_MIN, PEN_MAX))
    cands_n, cands_w = cand_deltas(False), cand_deltas(True)
    for nm in NATIVE:
        wide = WRIST_WIDE and (not WIDE_CLIPS or nm in WIDE_CLIPS)
        cands = cands_w if wide else cands_n
        mats = hand_mats(new[nm])
        e0 = mean_elev(mats, Quaternion())
        tgt = TIP_TABLE.get(nm, TIP_ELEV)          # 18차: 클립별 목표 고도
        print("  %-5s 보정 전: 칼끝 고도 %+.1f도 / 여유 %+.3f / 관통 %.3f  (목표 %+.0f도)"
              % (nm, e0, M_RAW[nm]["clear"], M_RAW[nm]["pen"], tgt))
        # 1차: 고도만 보고 후보를 좁힌다(메시를 안 봐도 되므로 공짜다)
        near = [(abs(mean_elev(mats, q) - tgt), mag, lab, q)
                for mag, lab, q in cands]
        near = [t for t in near if t[0] <= 30.0]
        if wide:
            # ★넓힌 후보는 **싼 항만 다 넣은 점수**로 줄을 세운다(고도오차·회전량·
            #   고도폭). 옛 정렬(오차 + 0.25*회전량)은 회전량이 큰 후보를 무조건
            #   뒤로 밀어서, 정작 호를 되눕히는 큰 회전이 상위 26 안에 못 든다.
            near.sort(key=lambda t: (0.02 * t[0] + 0.004 * t[1]
                                     + TIP_FLAT * elev_span(mats, t[3])))
        else:
            near.sort(key=lambda t: t[0] + 0.25 * t[1])
        # 2차: 비싼 검사(바닥·관통)는 상위 후보에만. 점수로 고른다.
        #   관통 초과가 압도적으로 무겁고, 그다음이 고도, 회전량은 동점 깨기용이다.
        best = None
        for err, mag, lab, q in near[:NCAND]:
            c, p = probe_wrist(new[nm], q)
            span = elev_span(mats, q)
            cost = (100 * max(0.0, p - PEN_MAX) + 100 * max(0.0, CLEAR_MIN - c)
                    + 0.02 * err + 0.004 * mag + TIP_FLAT * span)
            print("       후보 %-12s 고도오차 %4.1f도 회전 %2.0f도 -> 여유 %+.3f "
                  "관통 %.3f 고도폭 %4.1f도 점수 %.3f"
                  % (lab, err, mag, c, p, span, cost))
            if best is None or cost < best[0]:
                best = (cost, lab, q, c, p, mag, err)
        base_cost = (100 * max(0.0, M_RAW[nm]["pen"] - PEN_MAX)
                     + 100 * max(0.0, CLEAR_MIN - M_RAW[nm]["clear"])
                     + 0.02 * abs(e0 - tgt)
                     + TIP_FLAT * elev_span(mats, Quaternion()))
        if best is None or best[0] >= base_cost:
            print("       -> 보정 안 함(보정 전 점수 %.3f 가 더 낫다)" % base_cost)
            WRIST_USED[nm] = None
            continue
        apply_wrist(new[nm], best[2])
        WRIST_USED[nm] = (best[1], best[5], best[3], best[4])
        print("       -> 채택 %s (회전 %.0f도, 여유 %+.3f 관통 %.3f, 고도 %+.1f도"
              "(폭 %.1f도), 점수 %.3f < 보정전 %.3f)"
              % (best[1], best[5], best[3], best[4], mean_elev(mats, best[2]),
                 elev_span(mats, best[2]), best[0], base_cost))
        if ELB_R or LIFT_TABLE:                  # 18차: 보정까지 먹인 뒤의 손목 실측
            arm_report(new[nm], "FIN " + nm)

    print("\n[칼 흔들림] 손목 보정 후")
    for nm in NATIVE:
        blade_arc(new[nm], "FIX " + nm)
    print("\n[칼 간섭 실측] 손목 보정 후")
    M_FIX = {nm: measure(new[nm], "FIX " + nm, 2) for nm in NATIVE}
else:
    M_FIX = M_RAW

# ================================================================ 8) T 포즈 감시
# 경로를 고쳤어도 슬롯이 안 물리면 조용히 안 움직인다. **실제로 움직이는지** 본다.
print("\n[동작 확인] 클립마다 뼈가 실제로 움직이나(정지면 T 포즈 사고)")
for nm in sorted(list(NATIVE) + KEEP):
    act = new.get(nm) or bpy.data.actions[nm]
    use(armK, act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    ps = []
    for f in (f0, (f0 + f1) // 2, f1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        ps.append([(armK.matrix_world @ b.matrix).translation.copy()
                   for b in armK.pose.bones])
    mv = max((ps[i][j] - ps[0][j]).length for i in (1, 2)
             for j in range(len(ps[0])))
    print("  %-7s f%d~%d  최대 이동 %.4f %s"
          % (nm, f0, f1, mv, "" if mv > 1e-3 else "  <<< 안 움직인다"))
    if mv <= 1e-3:
        raise SystemExit("%s 가 정지 상태다. 슬롯/경로를 다시 봐라." % nm)

# ================================================================ 9) 접지 발 속도
# probe_stride 와 같은 절차. CHAR_CFG 에 넣을 값을 여기서 바로 찍는다.
def stride(act):
    use(armK, act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))

    def wp(key):
        for b in armK.pose.bones:
            if key.lower() in b.name.lower():
                return (armK.matrix_world @ b.matrix).translation.copy()
        return None

    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        rows.append((f, wp("pelvis"), wp("l foot"), wp("r foot"),
                     wp("l toe"), wp("r toe")))
    # 전방: 확실히 디딘 프레임의 발끝-발목
    order = sorted(range(len(rows)), key=lambda i: min(rows[i][4].z, rows[i][5].z))
    acc = Vector((0, 0, 0))
    for i in order[:max(1, len(rows) // 4)]:
        r = rows[i]
        a, t = (r[2], r[4]) if r[4].z <= r[5].z else (r[3], r[5])
        d = t - a
        d.z = 0
        if d.length > 1e-6:
            acc += d.normalized()
    fwd = acc.normalized() if acc.length > 1e-6 else Vector((0, -1, 0))
    grip = []
    for fi, ti, tag in ((2, 4, "왼발"), (3, 5, "오른발")):
        zz = [r[ti].z for r in rows]
        thr = min(zz) + 0.03 * BIND_H
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
        proj = [(rows[i][fi] - rows[i][1]).dot(fwd) for i in bi]
        dd = sorted(proj[k] - proj[k + 1] for k in range(len(proj) - 1))
        grip.append((dd[len(dd) // 2] * 30.0, len(bi), tag))
    # ★독립 검증: 두 발이 가장 벌어진 순간의 앞뒤 간격 = 한 걸음 보폭.
    #   접지 기울기(위)와 보폭(아래)이 서로 맞아야 측정을 믿을 수 있다.
    #   보폭은 **클립의 성질**이라 재생속도로 못 바꾼다. 이동속도를 정하면
    #   케이던스(분당 걸음수)가 자동으로 결정된다 - 그림의 인상은 여기서 갈린다.
    step = max(abs((r[2] - r[3]).dot(fwd)) for r in rows) * SCALE
    if not grip:
        return None, fwd, [], step
    return sum(g[0] for g in grip) / len(grip) * SCALE, fwd, grip, step


print("\n[접지 발 속도] (게임 단위 /초, 재생속도 1.0 기준)")
STRIDE = {}
for nm in [c for c in ("Walk", "Run") if c in NATIVE]:
    for tag, act in (("OLD", old[nm]), ("NEW", new[nm])):
        v, fwd, grip, step = stride(act)
        if v is None:
            print("  %s %-4s 접지 구간 못 찾음" % (tag, nm))
            continue
        dur = (act.frame_range[1] - act.frame_range[0]) / 30.0
        tgt = {"Walk": 1.71, "Run": 3.20}[nm]
        ts = tgt / v
        print("  %s %-4s 클립 %.3f초  보폭 %.2fm  발속도 %.3f  "
              "-> 이동 %.2f 이려면 재생 %.2f = 사이클 %.3f초 = 분당 %.0f걸음"
              % (tag, nm, dur, step, v, tgt, ts, dur / ts, 120.0 * ts / dur))
        print("       (검증) 발속도 x 사이클 = %.2fm/사이클 vs 보폭x2 = %.2fm"
              % (v * dur, step * 2))
        if tag == "NEW":
            STRIDE[nm] = v

# ================================================================ 10) 클립 z 대역
print("\n[클립별 메시 z] 클립 간 접지 높이가 크게 다르면 전환 때 수직으로 튄다")
for nm in sorted(list(NATIVE) + KEEP):
    act = new.get(nm) or bpy.data.actions[nm]
    use(armK, act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    lo, hi = 9e9, -9e9
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        vs = ev_verts(body)
        lo = min(lo, min(v.z for v in vs))
        hi = max(hi, max(v.z for v in vs))
    print("  %-7s 최저z %+.4f 최고z %+.4f (게임 키 %.3f)"
          % (nm, lo, hi, (hi - lo) * SCALE))

# ================================================================ 10.5) 전후 렌더
# ★같은 카메라·조명·바닥으로 OLD 와 NEW 를 **한 세션에서** 찍는다. 따로 찍으면
#   조명이 1도만 달라도 "달라 보인다"가 모션 차이인지 조명 차이인지 못 가른다.
# ★바닥판을 캐릭터 대신 **바닥을 움직여** 맞춘다(main.js groundFeet 과 같은 규칙:
#   가장 낮은 발 본이 바닥 위 charH*0.045 에 온다). 캐릭터를 움직이면 아마추어
#   자식 관계에 따라 칼이 따라오거나 안 따라오는 사고가 난다.
def render_all():
    os.makedirs(OUTDIR, exist_ok=True)
    ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                        else "BLENDER_EEVEE")
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = 420, 640
    sc.render.film_transparent = False
    for o in swords:                       # 7자루가 다 보이면 뭐가 뭔지 모른다
        o.hide_render = (o is not SW)
    xs = [(body.matrix_world @ v.co).x for v in body.data.vertices]
    ys = [(body.matrix_world @ v.co).y for v in body.data.vertices]
    CX, CY = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    FOOT0 = min(zs)
    bpy.ops.mesh.primitive_plane_add(size=BIND_H * 8, location=(CX, CY, FOOT0))
    floor = bpy.context.object
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    p = fm.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.30, 0.32, 0.36, 1)
    p.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(fm)
    for nm, e, rot in (("S", 4.2, (58, 0, -30)), ("F", 1.6, (-24, 0, 132))):
        li = bpy.data.lights.new(nm, "SUN")
        li.energy = e
        if nm == "F":
            li.color = (0.70, 0.82, 1.0)
        so = bpy.data.objects.new(nm, li)
        so.rotation_euler = tuple(math.radians(a) for a in rot)
        sc.collection.objects.link(so)
    cam = bpy.data.objects.new("C", bpy.data.cameras.new("C"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = 52
    TGT = Vector((CX, CY, FOOT0 + BIND_H * 0.52))
    D = BIND_H * 2.05
    OFF = {                       # 캐릭터는 -Y 를 본다. 오른손(칼)은 -X 쪽이다
        "side": Vector((-D, 0, BIND_H * 0.06)),
        "q": Vector((-D * 0.72, -D * 0.72, BIND_H * 0.16)),
        "front": Vector((0, -D, BIND_H * 0.08)),
    }
    made = []

    def shoot(act, frames, tag, view):
        use(armK, act)
        pos = TGT + OFF[view]
        cam.location = pos
        cam.rotation_euler = (TGT - pos).to_track_quat("-Z", "Y").to_euler()
        for i, f in enumerate(frames):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            floor.location.z = low_foot() - GAME_H * SOLE / SCALE
            fp = os.path.join(OUTDIR, "%s_%s_%02d_f%03d.png" % (tag, view, i, f))
            sc.render.filepath = fp
            bpy.ops.render.render(write_still=True)
            made.append(fp)

    def spread(act, n):
        f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
        return [f0 + round((f1 - f0) * i / float(n)) for i in range(n)]

    print("\n[렌더] -> %s" % OUTDIR)
    only = [t.strip() for t in os.environ.get("RENDER_ONLY", "loco,combat").split(",")]
    if "loco" in only:
        for nm in NATIVE:
            shoot(old[nm], spread(old[nm], 8), "old_" + nm.lower(), "side")
            shoot(new[nm], spread(new[nm], 8), "new_" + nm.lower(), "side")
            shoot(new[nm], spread(new[nm], 8), "new_" + nm.lower(), "q")
    if "combat" in only:
        # 전투 3종 재검(측면 위주 + 3/4 한 줄)
        for nm in ("Attack", "Heavy", "Wide"):
            act = bpy.data.actions[nm]
            shoot(act, spread(act, 10), "cbt_" + nm.lower(), "side")
            shoot(act, spread(act, 10), "cbt_" + nm.lower(), "q")
    print("[렌더] %d장" % len(made))
    # ★렌더용 소품은 **반드시 지운다**. 남기면 바닥판·조명·카메라가 glb 로 나간다.
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o is floor:
            bpy.data.objects.remove(o, do_unlink=True)
    for o in swords:
        o.hide_render = False


if RENDER:
    render_all()

# ================================================================ 11) 내보내기
print("\n[정리] 옛 로코모션 액션 제거")
for nm in list(NATIVE):
    a = bpy.data.actions.get("OLD_" + nm)
    if a:
        bpy.data.actions.remove(a)
FINAL = sorted(list(NATIVE) + KEEP)
for a in list(bpy.data.actions):
    if a.name not in FINAL:
        print("  액션 제거: %s" % a.name)
        bpy.data.actions.remove(a)
    else:
        a.use_fake_user = True
print("  최종 액션: %s" % sorted(a.name for a in bpy.data.actions))
if sorted(a.name for a in bpy.data.actions) != FINAL:
    raise SystemExit("최종 액션 목록이 기대와 다르다")

# 임포트 잔재 오브젝트가 남아 있으면 검사 몸이 두 벌 나간다
left = [o.name for o in sc.objects if o.type in ("MESH", "ARMATURE")]
print("  씬 오브젝트: %s" % left)
if len(left) != 1 + 1 + len(swords):
    raise SystemExit("오브젝트 수가 안 맞는다(소스 잔재?): %s" % left)

if EXPORT:
    use(armK, bpy.data.actions["Idle"])
    sc.frame_set(int(round(bpy.data.actions["Idle"].frame_range[0])))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=OUT_GLB, export_format="GLB", use_selection=False,
        export_animations=True, export_animation_mode="ACTIONS",
        export_nla_strips=False, export_bake_animation=True,
        export_frame_range=False, export_yup=True,
        export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
        export_jpeg_quality=TEX_QUALITY)
    print("\nEXPORTED %s  %d bytes" % (OUT_GLB, os.path.getsize(OUT_GLB)))
else:
    print("\n(EXPORT=0. 파일은 안 건드렸다)")

# ================================================================ 12) 요약
print("\n" + "=" * 78)
print("[요약]")
print("  fcurve 경로 수정: %s" % ", ".join("%s %d개" % (k, v) for k, v in FIXED.items()))
for nm in NATIVE:
    w = WRIST_USED.get(nm)
    print("  %-5s 바닥여유 OLD %+.3f -> NEW %+.3f -> 보정후 %+.3f / 관통 %.3f -> %.3f -> %.3f  손목 %s"
          % (nm, M_OLD[nm]["clear"], M_RAW[nm]["clear"], M_FIX[nm]["clear"],
             M_OLD[nm]["pen"], M_RAW[nm]["pen"], M_FIX[nm]["pen"],
             "%s (회전 %.0f도)" % (w[0], w[1]) if w else "없음"))
for nm in [c for c in ("Walk", "Run") if c in NATIVE]:
    if nm in STRIDE:
        cur = {"Walk": (1.71, 1.60), "Run": (3.20, 1.10)}[nm]
        print("  %-5s 발 속도 %.3f -> 이동 %.2f 유지하려면 재생속도 %.2f (지금 %.2f)"
              % (nm, STRIDE[nm], cur[0], cur[0] / STRIDE[nm], cur[1]))
print("=" * 78)
