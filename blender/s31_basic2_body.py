# -*- coding: utf-8 -*-
"""알몸 기본2(basic2)의 오른 주먹에 우리 칼 7자루를 꿰어 web/basic2_body.glb 를 만든다.

    blender -b -P blender/s31_basic2_body.py
    -> web/basic2_body.glb   (액션 없음. 모션은 이어서 s24_moveset.py 가 이식한다)

★★2026-08-24 23차부터 공정은 **일곱 줄**이다 — 아래 여섯 줄 뒤에 s42(Soldier 하체)가
  붙는다(2026-08-14 커밋 6a8dbf8 부터. 이 헤더가 그동안 여섯 줄로 남아 있었다):
    # 7) Walk/Run 하체만 Soldier 로 교체 (자세한 건 s42 헤더)
    DST_GLB=web/basic2.glb OUT_GLB=<임시>.glb blender -b -P blender/s42_basic2_soldier_legs.py
    cp <임시>.glb web/basic2.glb
★★md5 계보: 18차 여섯 줄 = fa19aa9d → +s42 = 5013a2f4(구 커밋본)
  → 23차 모션재작(MOVES_V23=1, s24 베기 3종 재작) 여섯 줄 = 106f43ae → +s42 = 9c5d4f7e
  → 24차 대검 물리(MOVES_V24=1·JUMP_V24=1 + s27 달리기 캐리 4손잡이) 여섯 줄 =
    155c7409 → +s42 = 525d9e99
  → 25차 파지·캐리(GRIP_V25=1: 손등 계약+베기 날 정렬 wrl / CARRY_V25=1: Walk·Run
    어깨 거치. s27 에 CARRY_TIP_E=30 CARRY_U=-0.05 CARRY_O=0.04 CARRY_TIP_B=8 명시
    = 코드 기본값) 여섯 줄 = b7bf59a1 → +s42 = **32bc2c79**
  ★25차 롤백: GRIP_V25=0 CARRY_V25=0 (+아래 24차 환경 그대로) = 525d9e99 재현
    (2026-08-24 실측. renders/history/v99_wave25/motion/scripts/run8_rollback_check.sh)
  ★2번 줄 재현 주의: 커밋본은 **IDLE_E=70 IDLE_AZ=35 를 명시**해서 구웠다(run6.sh 기본값.
    s24 코드 기본은 78/22 라 안 넘기면 md5 가 어긋난다. 23차 재현으로 실측 확인.
    24차도 같은 값을 명시해 idle 을 그대로 뒀다 — 하단세는 장대 게이트와 충돌해
    IDLE_V24=1 데모 프리셋으로만 남겼다. s24 의 24차 절 주석 참조).
  ★24차 3번 줄은 s27 에 네 손잡이가 붙는다(안 주면 23차 판):
    LIFT_TABLE=Walk:-10,Run:8 TIP_TABLE=Walk:-24,Run:-24 DAMP_TABLE=Run:0.15 NCAND=60
    WRIST_WIDE=Walk,Run   (걷기 값은 23차와 동일 — 달리기만 캐리로 바뀐다)
  일곱 줄 전체 = renders/history/v99_wave25/motion/scripts/run8_v25.sh (25차 정본.
    24차 판 = v99_wave24/motion/scripts/run7_v24.sh)
  (23차 재현 검증용 = v99_wave23/.../run7_repro.sh — 24차 착수 전에 9c5d4f7e 를
   run7_repro24.sh 로 재현 확인했다. 로그 = v99_wave24/motion/logs/repro_*.log)

전체 공정 **여섯 줄**(이 순서대로 다시 돌리면 언제든 재현된다. 2026-08-11 실행 기록.
1~4 는 2026-08-11 재실행에서 **바이트 단위로 같은 파일**이 다시 나왔다.
2026-08-12 에는 여섯 줄 전부가 committed basic2.glb 와 md5 까지 같았다.
같은 날 13-걷기팔에서도 **손대기 전 md5 7ae7066d… 재현 확인 후** 고쳤다.
2026-08-12 14-베기수정에서도 손대기 전에 committed md5 d7bb257c… 를 여섯 줄로
재현해 확인했다 — 그 다음에야 2번 줄의 ANIM_SPEC 을 고쳤다. 새 md5 cc7a26dd…
2026-08-13 15-모션수제에서도 손대기 전에 committed md5 cc7a26dd… 를 여섯 줄로
재현해 확인했다 — 그 다음에야 2번 줄을 HAND 로 갈았다.
2026-08-13 18차(걷기 팔꿈치·검도 X·Idle 칼 세우기)에서도 손대기 전에
committed md5 fc74fee3 을 여섯 줄로 재현해 확인했다. 새 md5 **fa19aa9d**.
★그 판을 다시 뽑는 스위치는 세 개다:
    KENDO_X=0 ELB_R=0 LIFT_TABLE= TIP_TABLE= WRIST_WIDE=0 SWING_R_REF=hand IDLE_GUARD=0)
★★6번(s34)을 빼먹으면 1번 칼이 옛 카타나로 남아 md5 가 안 맞는다. 여기 다섯 줄만
  적혀 있어서 실제로 한 번 헛돌았다. 6번은 blender/s34_sword1_swap.py 헤더에 있다.

    # 1) 알몸 basic2 + 칼 7자루
    #    ★2026-08-12 오너 지시 3차로 **오른 주먹을 팔축 둘레 93.9도 돌린다**
    #      (아래 [5b] 절. FIST_ROLL=0 이면 옛 판 그대로. 칼은 한 톨도 안 건드린다)
    blender -b -P blender/s31_basic2_body.py
    # 2) slayer 무브셋 7종 이식 (레스트 관절 각도차 5.9~10.4도. kensa 보다 작다)
    #    ★점프는 기본값 RELEASE=Jump 로 **한 손 파지**가 되고(2026-08-12 오너 지시),
    #      기본값 SWORD_DOWN=Jump 로 **검 든 오른팔이 몸 옆·아래로 내려간다**
    #      (같은 날 오너 지시 2차. 빼면 검을 앞으로 겨눈 채 뛴다)
    #    ★기본값 HAND_GRIP=1 로 **왼손목 방향을 자루에서 역산**한다(오너 지시 3차.
    #      빼면 왼손목이 Attack 169도·Heavy 161도까지 꺾인다. WRIST_LIM=60 이 상한)
    #    ★★2026-08-13 15-모션수제(오너 "칼 베는거 안고쳐짐 그냥 너가 직접 베는
    #      모션 만들어. 위에서아래로. 옆으로."): **베기 3종은 이제 Meshy 프리셋이
    #      아니라 손으로 짠 키프레임이다.** 손잡이 하나 `HAND=Attack,Heavy,Wide`.
    #      대본(각 기술의 키프레임 표)은 s24_moveset.py 의 HAND_SPEC 에 있다.
    #      ★점프도 같은 지시로 팔 위상표(SWD_KEYS·BAL_KEYS)를 다시 잡았다 —
    #        칼끝이 뒤가 아니라 **몸 옆**으로 나가고 양팔은 20~30도만 벌어진다.
    #    ★★2026-08-13 17차(16차 건틀릿 비평 "막대에 꿰인 사람"): 그 "몸 옆"이
    #      **화면에서는 발밑 수직 장대**였다(카메라가 월드 고정이라 몸 오른쪽이
    #      카메라 쪽이 되는 yaw 가 있다). 칼끝을 들고(E +14/+18) 방위를 45도
    #      격자에서 비끼고(Wd 122/128) **팔꿈치 굽힘(EB +40)** 을 새로 넣어
    #      여덟 방향 전부에서 실루엣이 서게 고쳤다. 위팔 외전은 15~26도로 유지.
    #      옛 판은 `JUMP_V15=1` 로 되살아난다(그 판의 basic2.glb md5 9640ffd6).
    #    ── 폐기된 길(코드는 남아 있다. 되살리려면 HAND 를 빼고 아래 두 줄을 넣는다) ──
    #      13-모션이식·14-베기수정의 Meshy 프리셋 트림 방식. ANIM_DIR/ANIM_SPEC 경로는
    #      s24 에 그대로 있어서 14차 판(md5 cc7a26dd…)이 언제든 재현된다:
    #        ANIM_DIR=incoming/meshy_anim ANIM_BLEND=8 \
    #        ANIM_SPEC="Attack=left_slash:14-16@0.5+left_slash:16-22@1.0+left_slash:22-23@0.16+left_slash:23-30@1.30+left_slash:30-37@0.55+left_slash:37-46@1.25+left_slash:46-47@0.25;Heavy=sword_slash:6-11@0.75+sword_slash:11-17.5@1.35+sword_slash:17.5-20.2@0.55+sword_slash:20.2-20.35@0.04;Wide=sword_slash:14.5-16@0.20+sword_slash:16-21@0.75+sword_slash:21-21.4@0.08"
    #      오너가 두 번 다 "안 고쳐짐" 으로 기각했다. 소스가 한 손 과장 연기라
    #      **자르는 일로는 끝이 없다**는 것이 두 번의 결론이다.
    #    ★★2026-08-13 18차 두 건이 **기본값으로** 켜져 있다(둘 다 스위치 한 줄로 되돌린다):
    #      KENDO_X=1    X(Heavy) 를 **검도 정면베기**로 새로 짰다(오너 "위에서 아래로 딱
    #                   써는 모션 새로. 기존꺼 그냥 잊고"). 대본은 s24 의 HAND_SPEC_KENDO.
    #                   KENDO_X=0 이면 16차 Heavy 대본이 그대로 굽힌다
    #      IDLE_GUARD=1 서 있을 때 **칼을 세운다**(오너 "칼각도 너무 눞혀져있다").
    #                   IDLE_E=70 IDLE_AZ=35 가 기본. 손목에만 회전을 먹이므로 팔은
    #                   한 도도 안 움직인다. IDLE_GUARD=0 이면 옛 Idle 그대로
    SRC_GLB=web/slayer.glb DST_GLB=web/basic2_body.glb OUT_GLB=web/basic2_moves.glb \
      DST_SWORD=SW_baekah.001 SWORD_FIT=0 GRIP_K=1.0 KEEP_ORIG=1 \
      HAND=Attack,Heavy,Wide \
      OUTDIR=renders/history/v99_wave15/handmoves/moveset blender -b -P blender/s24_moveset.py
    # 3) 걷기·달리기만 basic2 네이티브로 교체(+오른팔 감쇠·팔 들기·스윙 자연화·손목 보정)
    #    ★SW_NAME/TIP_K/ARM_LIFT/TIP_ELEV 는 2026-08-12 에 붙었다. 빼면 칼끝이
    #      지면 아래로 내려간다(6번이 1번 칼을 1.78배로 키우는데 3번은 그걸 못 본다).
    #      TIP_K 는 6번 로그의 pmax 비(131.531/73.868)를 그대로 적은 값이다.
    #    ★LIFT_MODE=abd / SWING_* / TIP_FLAT 은 같은 날 오너 지시 4차
    #      **"걸을 때 팔을 너무 뒤로 뺀다"** 로 붙었다. 셋을 다 빼면(=LIFT_MODE=lean
    #      ARM_LIFT=16, SWING_R/SWING_L 빈 값, TIP_FLAT=0) 옛 판 md5 가 그대로 나온다.
    #        LIFT_MODE=abd  드는 축을 '몸 옆으로 벌리기'로 바꾼다. 옛 lean 축은 팔이
    #                       기운 쪽으로 더 밀어 올리는 방식이라 팔을 더 뒤로 뺐다
    #        ARM_LIFT=28    벌림각(옛 16도는 lean 축 기준이라 숫자를 그대로 못 옮긴다)
    #        SWING_R=2      오른팔 중립 스윙을 수직 아래 +2도(앞)로. 상수 회전 하나라
    #                       칼 방향호는 한 도도 안 변한다
    #        SWING_L=-2 + GF/GB  왼팔은 앞 이득 0.80 / 뒤 이득 0.58 (걷기만)
    #        TIP_FLAT=0.02  손목 보정 후보를 고를 때 칼끝 고도 **진폭**도 본다
    #    ★★2026-08-13 18차 오너 지시 **"걸을때 칼든손 왜이렇게 벌리고 걸음?"** 으로
    #      아래 다섯 손잡이가 붙었다(전부 걷기만. 달리기는 한 도도 안 변한다).
    #      13-걷기팔이 "ARM_LIFT 를 줄이는 대신 팔꿈치를 굽히는 손잡이"라고 처방까지
    #      적어 두고 못 만든 그 채널이다. 다섯을 다 빼면 15차 판이 그대로 나온다.
    #        ELB_R=70 ELB_DIR=-20   팔꿈치를 70도 더 굽힌다(방향 0=앞 / 음수=앞바깥.
    #                       안쪽으로 굽히면 칼이 허벅지를 파고든다 — 실측 관통 0.055)
    #        LIFT_TABLE=Walk:-10    걷기만 벌림을 28 -> -10 도로(위팔 외전 56 -> 19도)
    #        TIP_TABLE=Walk:-24     달리기 목표(-24)와 같은 값을 걷기에도 명시
    #        WRIST_WIDE=Walk        손목 보정 후보를 **구면 균등**으로 넓힌다
    #                       (팔꿈치가 칼 방향 다발을 기울여서 옛 3축 격자에는 답이 없다)
    #        SWING_R_REF=elbow SWING_R_REF_CLIPS=Walk
    #                       오른팔 스윙을 **위팔**로 잰다(손목으로 재면 팔꿈치를 굽힌
    #                       만큼 위팔이 뒤로 밀려 노 젓는 자세가 된다 — 실측 -53도)
    DST_GLB=web/basic2_moves.glb OUT_GLB=web/basic2.glb CLIPS=Walk,Run \
      SW_NAME=SW_nokseun TIP_K=1.7806 TIP_ELEV=-24 TIP_FLAT=0.02 \
      LIFT_MODE=abd ARM_LIFT=28 \
      ELB_R=70 ELB_DIR=-20 ELB_CLIPS=Walk LIFT_TABLE=Walk:-10 TIP_TABLE=Walk:-24 \
      WRIST_WIDE=Walk SWING_R_REF=elbow SWING_R_REF_CLIPS=Walk \
      SWING_R=2 SWING_L=-2 SWING_GF=0.80 SWING_GB=0.58 SWING_L_CLIPS=Walk \
      NAT_DIR=incoming/meshy4/Meshy_AI_game_character_8k_biped \
      NAT_STEM=Meshy_AI_game_character_8k_biped \
      OUTDIR=renders/history/v97_wave11/char_basic2/native blender -b -P blender/s27_kensa_native.py
    # 4) 이름의 .001 떼기 (안 하면 1~7 칼 교체가 죽는다)
    python3 tools/glb_rename.py web/basic2.glb
    # 5) 오너가 준 옷(벨트+모피 치마+어깨끈) 입히기. ★4번까지는 web/basic2.glb 가
    #    **알몸**이다. 이 줄이 같은 파일을 옷 입은 것으로 제자리 교체한다
    #    (임시파일에 쓰고 os.replace. 이미 옷이 있으면 멈춘다)
    BODY_GLB=web/basic2.glb OUT_GLB=web/basic2.glb \
      OUTDIR=renders/history/v98_wave12/cloth blender -b -P blender/s33_basic2_cloth.py
    # 6) 1번 칼을 오너가 준 new_sword 로 교체 + 1.5배 + 자루 파지 (자세한 건 s34 헤더)
    #    ★이 줄까지 돌려야 committed basic2.glb 와 md5 가 같아진다
    OUTDIR=renders/history/v98_wave12/sword1 blender -b -P blender/s34_sword1_swap.py

  ★2번에서 GRIP_K 를 1.0 으로 둔 근거: s24 가 찍는 손 크기가 소스 0.0853 /
    타깃 0.0823 로 3.4% 차이뿐이다(kensa 는 36% 차이라 0.64 를 줬다).
  ★3번을 하는 이유는 **보폭**이다. slayer 걷기를 이식하면 발 속도가 1.09 라
    이동 1.71 을 내려고 재생속도 1.57 이 필요하고, 한 걸음이 0.30초짜리
    종종걸음이 된다. 네이티브는 발 속도 1.412 → 재생속도 1.21 로 한 걸음 0.44초다.

왜 새로 만드나 (s26 을 다시 못 쓰는 이유)
  s26_swordsman.py 는 kensa 전용이다. Meshy 가 어깨 뒤로 물려 놓은 **막대 무기를
  잘라내고 주먹 구멍을 메우는** 수술이 몸통의 절반이고, 그 좌표가 kensa 메시에
  묶여 있다. basic2 는 애초에 빈손(꽉 쥔 주먹)이라 수술할 것이 없다.
  여기서 필요한 것은 "이미 정합이 끝난 칼 7자루를 다른 Meshy 손으로 옮기는 일"뿐이다.

★칼은 새로 꽂지 않는다. **kensa 의 칼을 좌표계째 옮긴다**
  kensa 의 7자루는 s26 이 이미 slayer 레스트 월드 칼 방향에 맞춰 꽂아 둔 것이다
  (그 정합이 s24 의 SWORD_FIT 이 하는 일과 같다). 그러니 각도를 다시 고를 이유가 없다.
  옮길 때 지켜야 하는 것은 **레스트에서의 월드 방향**이다:

      v_b(손뼈로컬) = FC_b + R @ ((v_k(손뼈로컬) - FC_k) * S)
      R = Rot(HM_b)^-1 @ Rot(HM_k)        HM = 손뼈 레스트 월드행렬

  이러면 HM_b @ v_b 의 방향이 HM_k @ v_k 와 정확히 같아진다. 즉 두 캐릭터가
  레스트에서 칼을 **같은 월드 각도로** 든다. 이 성질이 있어야 이어지는 s24 의
  레스트 델타 리타게팅이 칼끝 궤적을 그대로 옮긴다(s24 가 SWORD_FIT=0 으로도
  "레스트 자루축 각도차 0.0도" 를 찍어 검산해 준다).
  ★손뼈 로컬 축은 두 리그가 서로 46~74도 어긋나 있다(실측). 그래서 손뼈 로컬
    좌표를 그냥 복사하면 칼이 딱 그만큼 돌아간 채 박힌다. R 이 그걸 되돌린다.

★크기 S = (basic2 몸 키) / (kensa 몸 키)
  게임은 캐릭터를 CHAR_CFG.h(1.75)로 정규화한다. 원본 키가 kensa 1.700 / basic2 1.500
  이라 칼을 원본 크기로 옮기면 게임 화면에서 13% 더 긴 칼이 된다. 사거리 판정이
  칼 메시 실측(measureBlade)이라 그대로 두면 basic2 만 리치가 길어진다. 그래서
  **게임 화면에서 같은 길이가 되도록** 원본 단계에서 미리 줄인다.

★자리는 주먹 중심(손뼈에 웨이트 0.5 초과인 몸 정점의 무게중심)에 맞춘다
  basic2 손은 구멍 없는 꽉 쥔 주먹이라 자루가 살을 지난다. hero(s15)·kensa(s26)에서
  이미 쓰던 관례 그대로다 — 주먹이 닫힌 덩어리면 관통해도 '쥔 것'으로 보인다.

★함정 (표준 파이프라인. 하나라도 밟으면 조용히 망가진다)
  1) fps: 임포트 **전에** 30 고정
  2) 임포트 순서: **타깃(basic2)을 먼저**. 나중에 읽으면 char1 이 char1.001 이 되어
     그대로 내보내진다
  3) 스키닝은 REST 에서 굽는다. 포즈 상태로 재면 애니에서 어긋난다
  4) Icosphere: glTF 임포터가 뼈 표시용으로 만드는 반지름 1 구. glb 엔 없다.
     안 지우면 게임이 전 메시로 박스를 재므로 키가 망가진다
  5) 게임은 SW_ 로 시작하는 메시를 키 계산에서 뺀다. 칼 이름은 반드시 SW_<키>
  6) 게임은 재질 이름 앞자리(bd_/bv_/ht_/sp_)로 발광 부위를 가른다. 재질 이름을
     건드리지 말 것(kensa 것을 그대로 데려온다)
  7) 부모를 지우기 전에 정점을 월드로 굳혀 둘 것. 지운 뒤에는 matrix_world 가 변한다

손잡이(환경변수)
  DST_GLB   몸(타깃)          기본 web/basic2_native.glb
            ★basic2.glb 는 파이프라인의 **결과물**이다(칼 7자루 + 전투 7클립).
              그걸 다시 넣으면 칼 위에 칼을 꽂는다. 그래서 s14 가 구운 알몸 원본을
              web/basic2_native.glb 로 남겨 두고 그쪽을 기본값으로 쓴다.
              (백업 확장자 .bak_* 로 두면 glTF 임포터가 못 읽는다)
              SW_ 메시가 이미 있는 파일을 주면 멈춘다.
  SRC_GLB   칼을 가져올 원본   기본 web/kensa.glb
  OUT_GLB   결과              기본 web/basic2_body.glb
  KEEP_ANIM 1(기본) 타깃 원본 액션(Idle/Walk/Run)을 남긴다 / 0 지운다
            ★네이티브 걷기·달리기가 여기 들어 있다. s31_basic2_native.py 가 쓴다
  GRIP_ALIGN 1(기본) 손목 기준 칼날 축을 원본에 맞춰 조인다 / 0 자루 중심만 맞춤
  SW_SCALE  칼 배율에 곱하는 여유  기본 1.0
  RENDER    1(기본) 검산 렌더 / 0 생략
  OUTDIR    렌더 폴더  기본 renders/history/v97_wave11/char_basic2
  TEX_FORMAT/TEX_QUALITY  기본 AUTO(원본 포맷 유지) / 90
"""
import bpy
import os
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")

DST_GLB = os.environ.get("DST_GLB") or os.path.join(WEB, "basic2_native.glb")
SRC_GLB = os.environ.get("SRC_GLB") or os.path.join(WEB, "kensa.glb")
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "basic2_body.glb")
KEEP_ANIM = os.environ.get("KEEP_ANIM", "1") == "1"
GRIP_ALIGN = os.environ.get("GRIP_ALIGN", "1") == "1"
SW_SCALE = float(os.environ.get("SW_SCALE", "1.0"))
RENDER = os.environ.get("RENDER", "1") == "1"
OUTDIR = os.environ.get("OUTDIR") or os.path.join(
    ROOT, "renders", "history", "v97_wave11", "char_basic2")
TEX_FORMAT = os.environ.get("TEX_FORMAT", "AUTO").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

HAND_R = "Bip001 R Hand"

print("=" * 78)
print("[설정] 몸  %s" % DST_GLB)
print("       칼  %s" % SRC_GLB)
print("       결과 %s" % OUT_GLB)


def drop_junk():
    """glTF 임포터가 뼈를 그리려고 만드는 Icosphere(★함정 4)."""
    for o in list(bpy.data.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)


def rest(arm):
    """레스트로 고정하고 포즈 basis 를 지운다(★함정 3)."""
    for b in arm.pose.bones:
        b.rotation_mode = "QUATERNION"
        b.matrix_basis = Matrix()
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()


def fist(arm, body, tag):
    """손뼈 레스트 월드행렬 HM 과 주먹 중심 FC(손뼈 로컬)를 잰다."""
    A2W = arm.matrix_world.copy()
    HM = A2W @ arm.data.bones[HAND_R].matrix_local
    HMi = HM.inverted()
    vg = body.vertex_groups.get(HAND_R)
    assert vg is not None, "%s 에 %s 정점그룹이 없다" % (tag, HAND_R)
    P = []
    for v in body.data.vertices:
        for g in v.groups:
            if g.group == vg.index and g.weight > 0.5:
                P.append(HMi @ (body.matrix_world @ v.co))
                break
    assert len(P) > 20, "%s 손 정점이 %d 개뿐이다" % (tag, len(P))
    n = len(P)
    FC = Vector((sum(p.x for p in P) / n, sum(p.y for p in P) / n,
                 sum(p.z for p in P) / n))
    W = [body.matrix_world @ v.co for v in body.data.vertices]
    H = max(p.z for p in W) - min(p.z for p in W)
    FLOOR = min(p.z for p in W)
    print("\n[%s] 몸 정점 %d / 키 %.4f (바닥 %.4f)" % (tag, len(W), H, FLOOR))
    print("       주먹 정점 %d  중심(뼈로컬) (%+.3f, %+.3f, %+.3f)"
          % (n, FC.x, FC.y, FC.z))
    print("       주먹 bbox x %+.3f~%+.3f y %+.3f~%+.3f z %+.3f~%+.3f"
          % (min(p.x for p in P), max(p.x for p in P),
             min(p.y for p in P), max(p.y for p in P),
             min(p.z for p in P), max(p.z for p in P)))
    rr = max((p - FC).length for p in P)
    print("       주먹 반경(중심->최원점) %.3f (뼈로컬) = %.4f m"
          % (rr, rr * A2W.to_scale().x))
    return HM, FC, H, FLOOR, P


# ================================================================ 1) 임포트
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30                                    # ★함정 1
sc.render.fps_base = 1.0

# ★함정 2: 타깃을 먼저 읽는다
bpy.ops.import_scene.gltf(filepath=DST_GLB)
drop_junk()
arm_b = next(o for o in sc.objects if o.type == "ARMATURE")
body_b = max((o for o in sc.objects if o.type == "MESH"),
             key=lambda o: len(o.data.vertices))
rest(arm_b)
# ★결과물을 다시 넣으면 칼 위에 칼을 꽂는다. 알몸 원본만 받는다.
dup = [o.name for o in sc.objects if o.name.startswith("SW_")]
assert not dup, ("타깃에 이미 칼이 있다(%s). DST_GLB 는 알몸 원본"
                 " web/basic2_native.glb 여야 한다" % dup)
keep_objs = {o.name for o in sc.objects}
keep_acts = [a.name for a in bpy.data.actions]
print("\n[몸] 아마추어 %s (스케일 %.4f) / 뼈 %d / 메시 %s %d정점 / 액션 %s"
      % (arm_b.name, arm_b.matrix_world.to_scale().x, len(arm_b.data.bones),
         body_b.name, len(body_b.data.vertices), keep_acts))

bpy.ops.import_scene.gltf(filepath=SRC_GLB)
drop_junk()
arm_k = next(o for o in sc.objects
             if o.type == "ARMATURE" and o is not arm_b)
new_objs = [o for o in sc.objects if o.name not in keep_objs]
body_k = max((o for o in new_objs
              if o.type == "MESH" and not o.name.startswith("SW_")),
             key=lambda o: len(o.data.vertices))
sword_objs = [o for o in new_objs if o.type == "MESH" and o.name.startswith("SW_")]
rest(arm_k)
print("[칼] 아마추어 %s (스케일 %.4f) / 몸 %s / 칼 %d자루: %s"
      % (arm_k.name, arm_k.matrix_world.to_scale().x, body_k.name,
         len(sword_objs), sorted(o.name for o in sword_objs)))
assert sword_objs, "%s 에 SW_ 메시가 없다" % SRC_GLB

# ================================================================ 2) 실측
HM_b, FC_b, H_b, FLOOR_b, HP_b = fist(arm_b, body_b, "몸 basic2")
HM_k, FC_k, H_k, FLOOR_k, HP_k = fist(arm_k, body_k, "칼 kensa")

# 손뼈 축 어긋남(정보). R 이 이걸 되돌린다.
Rb = HM_b.to_quaternion().to_matrix()
Rk = HM_k.to_quaternion().to_matrix()
R = Rb.inverted() @ Rk
print("\n[정합] 손뼈 레스트 축 각도차(월드)")
for k, nm in enumerate("XYZ"):
    a = Vector((HM_b[0][k], HM_b[1][k], HM_b[2][k])).normalized()
    c = Vector((HM_k[0][k], HM_k[1][k], HM_k[2][k])).normalized()
    print("       %s축  %6.2f 도" % (nm, math.degrees(math.acos(
        max(-1.0, min(1.0, a.dot(c)))))))
print("       보정 R 회전각 %.2f 도" % math.degrees(R.to_quaternion().angle))

ARM_K_UNIT = arm_k.matrix_world.to_scale().x   # 뼈로컬 1 단위 = 몇 m (검산 출력용.
# ★아래에서 kensa 아마추어를 지우므로 지금 값을 빼 둔다. 지운 뒤 만지면 ReferenceError)
S = (H_b / H_k) * SW_SCALE
print("\n[크기] 칼 배율 S = %.4f / %.4f = %.4f (여유 %.3f 포함)"
      % (H_b, H_k, S, SW_SCALE))
print("       게임 정규화 뒤 칼 길이는 kensa 와 같아진다"
      " (원본 배율 1.0 이면 %.1f%% 길어진다)" % ((H_k / H_b - 1) * 100))

# ================================================================ 3) 칼 옮기기
# ★함정 7: 부모(kensa 아마추어)를 지우기 전에 월드로 굳힌다.
#
# ★★칼날 축은 **손목 원점 기준**으로 맞춘다. 자루 중심 기준이 아니다.
#   main.js measureBlade 와 s24 [자루] 절이 둘 다 "손 본 로컬에서 원점에서 가장 먼
#   정점"으로 칼날 방향을 정한다(= 손목 원점 기준). 그런데 두 리그의 주먹 중심이
#   손목에서 서로 다른 자리에 있어(실측 2.5cm 차) 자루 중심만 맞춰 옮기면 그 방향이
#   5.2도 어긋난다. 5도면 90cm 칼끝이 8cm 옆에 있는 것이라 궤적·사거리가 그만큼 밀린다.
#   그래서 옮긴 뒤 **자루 중심을 축으로** 미세 회전해 손목 기준 방향을 다시 맞춘다.
#   회전축(자루 중심)과 측정 기준점(손목)이 달라 한 번에 안 맞으므로 반복해서 조인다
#   (s26 이 kensa 에 쓴 것과 같은 방식. kensa 는 이 값이 slayer 대비 0.01도다).
GRIP_W = HM_b @ FC_b
tip_before = {}      # 칼 이름 -> (칼끝 정점 번호, 손목기준 목표 월드방향, 길이)
for o in sword_objs:
    MW = o.matrix_world.copy()
    KL = [HM_k.inverted() @ (MW @ v.co) for v in o.data.vertices]   # kensa 손뼈 로컬
    ti = max(range(len(KL)), key=lambda i: KL[i].length_squared)    # 손목 기준 최원점
    tgt = (HM_k.to_3x3() @ KL[ti]).normalized()
    tip_before[o.name] = (ti, tgt, KL[ti].length)
    loc = [HM_b @ (FC_b + R @ ((vk - FC_k) * S)) for vk in KL]      # 월드
    o.parent = None
    o.matrix_world = Matrix()
    for v, p in zip(o.data.vertices, loc):
        v.co = p
    o.data.update()

if GRIP_ALIGN:
    WRIST = HM_b.to_translation()
    print("\n[조임] 손목 기준 칼날 축을 원본에 맞춘다 (자루 중심 둘레 미세 회전)")
    for o in sorted(sword_objs, key=lambda x: x.name):
        tgt = tip_before[o.name][1]
        first = None
        for it in range(40):
            far = max((v.co for v in o.data.vertices),
                      key=lambda p: (p - WRIST).length_squared)
            cur = (far - WRIST).normalized()
            ang = cur.angle(tgt)
            if first is None:
                first = math.degrees(ang)
            if ang < 1e-4:
                break
            ax = cur.cross(tgt)
            if ax.length < 1e-9:
                break
            q = Matrix.Rotation(ang, 3, ax.normalized())
            for v in o.data.vertices:
                v.co = GRIP_W + q @ (v.co - GRIP_W)
            o.data.update()
        print("       %-14s %5.2f도 -> %.4f도 (%d회)"
              % (o.name, first, math.degrees(ang), it + 1))

# ================================================================ 4) kensa 정리
for o in list(sc.objects):
    if o is arm_b or o is body_b or o in sword_objs:
        continue
    if o.name in keep_objs:
        continue
    bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    if a.name not in keep_acts:
        bpy.data.actions.remove(a)
if not KEEP_ANIM:
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    if arm_b.animation_data:
        arm_b.animation_data_clear()
for a in bpy.data.actions:
    a.use_fake_user = True                              # 안 켜면 export 에서 빠진다

# ================================================================ 5) 스키닝
for o in sword_objs:
    for vg in list(o.vertex_groups):
        o.vertex_groups.remove(vg)
    vg = o.vertex_groups.new(name=HAND_R)               # ★손뼈 100%
    vg.add(range(len(o.data.vertices)), 1.0, "REPLACE")
    for md in list(o.modifiers):
        o.modifiers.remove(md)
    md = o.modifiers.new("Armature", "ARMATURE")
    md.object = arm_b
    o.parent = arm_b
    o.matrix_parent_inverse = arm_b.matrix_world.inverted()

# ====================================== 5b) 오른 주먹을 '쥔 방향'으로 돌린다 (13-손목)
# ★오너 지시(2026-08-12): "손등이 왜 하늘을 향하고 있냐? 손잡이를 쥐고 있어야 하는데,
#   주먹 쥔 캐릭터니까 조절 좀 잘해봐."
#
# 무엇이 어긋나 있었나 (실측. blender/probe_wrist.py)
#   주먹을 쥐고 막대를 잡으면 막대는 **손가락 마디가 늘어선 축**(검지 관절 -> 새끼
#   관절, 아래에서 '구멍축')으로 지나간다. 손등 노멀과는 90도다. 그런데 이 모델은
#       구멍축 - 칼축   86.0 도   (0 이어야 쥔 것이다)
#       손등노멀 - 칼축  7.7 도   (90 이어야 정상)
#   즉 칼이 손가락 사이가 아니라 **손바닥에서 손등으로 꿰뚫고** 있었다. 그래서 칼이
#   앞을 가리키면 손등도 같이 앞·위를 보고, 오너 눈에 "손등이 하늘"로 보인 것이다.
#   주먹 좌표계는 뼈 로컬축을 안 믿고 메시로 만든다(Meshy 리그는 축이 제멋대로다):
#     팔축   = 손목 원점 -> 주먹 중심 (기하로 확정)
#     구멍축 = 팔축에 수직인 평면에서 2차원 주성분의 **넓은** 쪽
#     손등축 = 좁은 쪽(두께)
#   ★3차원 주성분을 그냥 쓰면 안 된다. 손이 팔축으로 길쭉해(손목->손끝 20cm) 축 셋이
#     대각으로 섞인다. 실제로 첫 판에서 구멍축이 팔축과 같은 20cm 로 나왔다.
#
# 어떻게 고치나 — **칼이 아니라 주먹 메시를 돌린다**
#   칼을 돌리면 칼끝 방향(dir)·리치(pmax)가 바뀌어 12차에서 맞춰 둔 계약이 깨진다.
#   반대로 주먹 정점을 **팔축 둘레로** 돌리면
#     · 회전축이 주먹 중심을 지나므로 주먹 중심 FC 가 **한 톨도 안 움직인다**
#       (s34 가 자루를 앉히는 기준점이 FC 다. 자루 겹침 91% 가 그대로 지켜진다)
#     · 칼 메시·뼈·액션을 아예 안 건드리므로 dir·pmax 가 **바이트 단위로 같다**
#   회전량은 각도를 굳히지 않고 **푼다**: 엄지 쪽 구멍축을 칼끝 방향에 제일 가깝게
#   보내는 각. 팔축과 칼축이 정확히 90도가 아니라(83.4도) 6.6도가 남는데, 이건
#   칼이 손가락 사이를 6.6도 비껴 지난다는 뜻이라 눈에 안 보인다.
#   회전량에 **정점의 손뼈 웨이트를 곱한다**. 주먹(웨이트 1)은 통째로 돌고 손목은
#   웨이트만큼만 돌아 스킨과 같은 감쇠가 걸린다 = 팔뚝이 꺾이지 않고 비틀린다.
#   (사람 팔도 같은 일을 한다. 손목이 아니라 아래팔이 도는 pronation 이다)
FIST_ROLL = os.environ.get("FIST_ROLL", "auto")
# ★엄지가 어느 쪽인지는 기하로 못 가른다(주먹에 구멍이 안 뚫려 있다. 광선 스캔으로
#   확인했다). 2026-08-12 에 주먹 접사를 눈으로 보고 정했다
#   (renders/history/v99_wave13/wrist/fisttex/t_armP.png 에서 손가락 마디 골 네 개와
#    엄지 위치를 확인). PCA 부호는 실행마다 뒤집히므로 **레스트 월드 기준벡터**와의
#   내적으로 부호를 고정한다. 리그가 바뀌면 여기서 큰 소리로 죽는다.
THUMB_REF_W = Vector((0.285, -0.953, -0.100))


def fist_axes(HM, P, ref=None, strict=True):
    """주먹 좌표계 (팔축, 엄지쪽 구멍축, 손등축). 전부 손뼈 로컬 단위벡터.

    ref 는 '엄지축이 레스트 월드에서 어느 쪽이어야 하나'. 기본은 THUMB_REF_W 이고,
    돌린 뒤 다시 잴 때는 돌아간 예상 방향을 넘긴다(strict=False 로 경고만).
    """
    import numpy as np
    C = Vector((sum(p.x for p in P) / len(P), sum(p.y for p in P) / len(P),
                sum(p.z for p in P) / len(P)))
    a = C.normalized()
    e1 = Vector((1, 0, 0)) if abs(a.x) < 0.9 else Vector((0, 1, 0))
    e1 = (e1 - a * e1.dot(a)).normalized()
    e2 = a.cross(e1)
    Q = []
    for p in P:
        q = (p - C)
        q = q - a * q.dot(a)
        Q.append([q.dot(e1), q.dot(e2)])
    Q = np.array(Q, dtype=float)
    w2, V2 = np.linalg.eigh(Q.T @ Q)
    t = (e1 * V2[0, 1] + e2 * V2[1, 1]).normalized()      # 넓은 쪽 = 구멍축
    R3 = HM.to_3x3()
    R3.normalize()
    rv = THUMB_REF_W if ref is None else ref
    if (R3 @ t).dot(rv) < 0:                              # 엄지 쪽으로 부호 고정
        t = -t
    d = (R3 @ t).dot(rv)
    if strict:
        assert abs(d) > 0.85, ("엄지축 기준벡터와 %.2f 밖에 안 맞는다. 리그가 바뀌었으면"
                               " 접사를 다시 찍고 THUMB_REF_W 를 갱신해라" % d)
    return a, t, t.cross(a).normalized()


def fist_pts(HM, ob):
    """손뼈에 웨이트 0.5 초과인 몸 정점(손뼈 로컬). 돌린 뒤 다시 재려고 쓴다."""
    HMi = HM.inverted()
    vg = ob.vertex_groups[HAND_R]
    P = []
    for v in ob.data.vertices:
        for g in v.groups:
            if g.group == vg.index and g.weight > 0.5:
                P.append(HMi @ (ob.matrix_world @ v.co))
                break
    return P


def sw_tip_local(HM, o):
    """손뼈 로컬에서 '손목원점 -> 칼끝'(measureBlade 와 같은 기준)."""
    HMi = HM.inverted()
    L = [HMi @ v.co for v in o.data.vertices]             # 칼은 이미 월드로 굳혔다
    return max(L, key=lambda p: p.length).normalized()


A_ARM, A_TUN, A_BAK = fist_axes(HM_b, HP_b)
GAME_SW = next((o for o in sword_objs if o.name.startswith("SW_nokseun")),
               sword_objs[0])
U_L = sw_tip_local(HM_b, GAME_SW)
print("\n[파지] 오른 주먹 좌표계(손뼈 로컬)와 칼축")
print("       팔축   (%+.3f,%+.3f,%+.3f)   칼축과 %.1f도"
      % (A_ARM.x, A_ARM.y, A_ARM.z, math.degrees(A_ARM.angle(U_L))))
print("       구멍축 (%+.3f,%+.3f,%+.3f)   칼축과 %.1f도  <- 0 이어야 쥔 것"
      % (A_TUN.x, A_TUN.y, A_TUN.z, math.degrees(A_TUN.angle(U_L))))
print("       손등축 (%+.3f,%+.3f,%+.3f)   칼축과 %.1f도  <- 90 이어야 정상"
      % (A_BAK.x, A_BAK.y, A_BAK.z, math.degrees(A_BAK.angle(U_L))))
# 엄지쪽 구멍축을 칼끝으로 보내는 각을 푼다(팔축 둘레라 주먹 중심은 안 움직인다)
_c = A_ARM.cross(A_TUN)
PHI = math.atan2(U_L.dot(_c), U_L.dot(A_TUN))
if FIST_ROLL not in ("auto", ""):
    PHI = math.radians(float(FIST_ROLL))
if abs(math.degrees(PHI)) > 1e-6:
    HMi_b = HM_b.inverted()
    MW = body_b.matrix_world.copy()
    MWi = MW.inverted()
    vg = body_b.vertex_groups[HAND_R]
    RMAX = max(p.length for p in HP_b) * 1.35             # 이보다 먼 곁가지 웨이트는 무시
    n_full = n_part = 0
    moved = 0.0
    for v in body_b.data.vertices:
        w = 0.0
        for g in v.groups:
            if g.group == vg.index:
                w = g.weight
                break
        if w <= 1e-4:
            continue
        p = HMi_b @ (MW @ v.co)
        if p.length > RMAX:
            continue
        # ★감쇠는 웨이트 그대로가 아니라 **0.5 에서 이미 1** 이 되게 한다.
        #   주먹 중심 FC 는 '웨이트 0.5 초과' 정점의 무게중심이고 s34 가 자루를 그 점에
        #   앉힌다. 0.5 위쪽이 전부 같은 각으로 돌면 그 무게중심은 회전축 위에 있으므로
        #   **한 톨도 안 움직인다**(pmax·자루겹침이 바이트 단위로 보존된다).
        #   웨이트를 그대로 곱하면 0.5~1.0 구간이 덜 돌아 FC 가 0.36mm 밀리고
        #   pmax 가 131.53071 -> 131.58113 으로 새어 나간다(실측).
        #   감쇠는 손목 고리(웨이트 0~0.5, 팔뚝 정점들)에서만 일어난다.
        k = min(1.0, w / 0.5)
        q = Matrix.Rotation(PHI * k, 3, A_ARM) @ p
        v.co = MWi @ (HM_b @ q)
        moved = max(moved, (q - p).length)
        if k > 0.999:
            n_full += 1
        else:
            n_part += 1
    body_b.data.update()
    # ★검산은 **실제로 바뀐 메시를 다시 재서** 한다(웨이트 감쇠 때문에 해석식과
    #   미세하게 다르다. 부호는 예상 방향으로 이어 준다)
    R3b = HM_b.to_3x3()
    R3b.normalize()
    HPa = fist_pts(HM_b, body_b)
    A_ARM2, A_TUN2, A_BAK2 = fist_axes(
        HM_b, HPa, ref=R3b @ (Matrix.Rotation(PHI, 3, A_ARM) @ A_TUN), strict=False)
    FCa = Vector((sum(p.x for p in HPa) / len(HPa), sum(p.y for p in HPa) / len(HPa),
                  sum(p.z for p in HPa) / len(HPa)))
    print("       ★주먹을 팔축 둘레로 %+.1f도 돌렸다 (정점 웨이트만큼. 통째 %d개 +"
          " 손목 감쇠 %d개, 최대 이동 %.4f 뼈로컬)"
          % (math.degrees(PHI), n_full, n_part, moved))
    print("       돌린 뒤: 구멍축-칼축 %.1f도 / 손등축-칼축 %.1f도 / 주먹중심 이동"
          " %.6f 뼈로컬 (= %.4f mm 게임)"
          % (math.degrees(A_TUN2.angle(U_L)), math.degrees(A_BAK2.angle(U_L)),
             (FCa - FC_b).length,
             (FCa - FC_b).length * arm_b.matrix_world.to_scale().x * (1.75 / H_b) * 1000))
    print("       칼 7자루 구멍축과의 각(작을수록 자루가 손가락 사이를 지난다):")
    for o in sorted(sword_objs, key=lambda x: x.name):
        u = sw_tip_local(HM_b, o)
        print("         %-14s 전 %5.1f도 -> 후 %5.1f도"
              % (o.name, math.degrees(A_TUN.angle(u)),
                 math.degrees(A_TUN2.angle(u))))
else:
    print("       FIST_ROLL=0 이라 주먹을 안 돌린다(옛 판 재현용)")

# ================================================================ 6) 검산
print("\n[검산] 손목 기준 칼날 축(레스트 월드). 옮기기 전후가 같아야 한다")
print("       %-14s %8s %10s %10s %10s" %
      ("칼", "각도차", "길이(kensa)", "길이(basic2)", "최저z"))
WRIST_W = HM_b.to_translation()
worst = 0.0
for o in sorted(sword_objs, key=lambda x: x.name):
    ti, d_k, len_k = tip_before[o.name]
    far = max((v.co for v in o.data.vertices),
              key=lambda p: (p - WRIST_W).length_squared)
    d_b = (far - WRIST_W).normalized()
    ang = math.degrees(math.acos(max(-1.0, min(1.0, d_b.dot(d_k)))))
    worst = max(worst, ang)
    len_b = (far - WRIST_W).length
    len_km = len_k * ARM_K_UNIT                        # ★뼈로컬 단위 -> m
    zlo = min(v.co.z for v in o.data.vertices)
    print("       %-14s %6.3f도 %10.4f %11.4f %11.4f (바닥 %+.4f)"
          % (o.name, ang, len_km, len_b, zlo, FLOOR_b))
print("       최악 %.3f 도 (0.1 미만이면 방향이 그대로 옮겨진 것이다)" % worst)
print("       게임 정규화(키 1.75) 뒤 손목->칼끝: kensa %.4f m / basic2 %.4f m"
      % (len_km * 1.75 / H_k, len_b * 1.75 / H_b))

# 자루가 주먹을 지나는가(= 쥔 것처럼 보이는가)
hw = [HM_b @ p for p in HP_b]
for o in sorted(sword_objs, key=lambda x: x.name):
    inside = 0
    for p in hw:
        d = min((p - v.co).length for v in o.data.vertices)
        if d < 0.02:
            inside += 1
    print("       %-14s 칼 표면 2cm 안의 손 정점 %d/%d" % (o.name, inside, len(hw)))

# ================================================================ 7) 내보내기
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
sc.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action="DESELECT")
kw = dict(filepath=OUT_GLB, export_format="GLB", use_selection=False,
          export_apply=True, export_yup=True,
          export_animations=KEEP_ANIM, export_animation_mode="ACTIONS",
          export_nla_strips=False, export_bake_animation=True,
          export_frame_range=False)
if TEX_FORMAT not in ("AUTO", ""):
    kw.update(export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
              export_jpeg_quality=TEX_QUALITY)
bpy.ops.export_scene.gltf(**kw)
sz = os.path.getsize(OUT_GLB)
print("\nEXPORTED %s  %d bytes (%.2f MB)  칼 %d자루  액션 %s"
      % (OUT_GLB, sz, sz / 1e6, len(sword_objs),
         [a.name for a in bpy.data.actions]))

# ================================================================ 8) 렌더
if not RENDER:
    print("DONE (렌더 생략)")
    raise SystemExit(0)

os.makedirs(OUTDIR, exist_ok=True)
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                    else "BLENDER_EEVEE")
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 620, 800
wd = bpy.data.worlds.new("W")
sc.world = wd
wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs[0].default_value = (0.06, 0.065, 0.08, 1)
for eul, en, col in (((58, 0, -30), 4.0, (1, 1, 1)),
                     ((-40, 0, 130), 1.8, (0.7, 0.82, 1.0))):
    li = bpy.data.lights.new("S", "SUN")
    li.energy = en
    li.color = col
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = tuple(math.radians(a) for a in eul)
    sc.collection.objects.link(so)
bpy.ops.mesh.primitive_plane_add(size=H_b * 6, location=(0, 0, FLOOR_b))
cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam

# 게임 기본 칼(백아)만 켠다. 7자루가 다 보이면 겹쳐서 아무 판정도 안 된다.
for o in sword_objs:
    o.hide_render = (o.name != "SW_baekah")

CEN = Vector((0, 0, FLOOR_b + H_b * 0.55))
GRIP = HM_b @ FC_b


def look(cam, eye, tgt):
    cam.location = eye
    d = (tgt - eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


for nm, eye, tgt, res in (
        ("body_front", CEN + Vector((0, -H_b * 1.9, H_b * 0.10)), CEN, (620, 800)),
        ("body_side", CEN + Vector((-H_b * 1.9, 0, H_b * 0.10)), CEN, (620, 800)),
        ("grip", GRIP + Vector((-0.18, -0.30, 0.12)), GRIP, (800, 620)),
        ("grip2", GRIP + Vector((0.10, -0.22, 0.22)), GRIP, (800, 620))):
    sc.render.resolution_x, sc.render.resolution_y = res
    look(cam, eye, tgt)
    sc.render.filepath = os.path.join(OUTDIR, "s31_%s.png" % nm)
    bpy.ops.render.render(write_still=True)
    print("   렌더 %s" % sc.render.filepath)
print("DONE")
