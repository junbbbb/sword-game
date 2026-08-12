# -*- coding: utf-8 -*-
"""탑 1층 **던전**을 만들어 web/level2.glb + web/level2.json 으로 내보낸다.

실행: blender -b -P blender/s40_dungeon1.py
설계 정본: docs/dungeon1-design.md   (방 그래프 · 몹 의도 · 팔레트 · 검증 목록)

모티브는 「게임속 바바리안으로 살아남기」 1층이다. 갇힌 자들이 살아 나가려고
싸우는 석조 던전. 고블린만 나오고 보스는 없다. 증표(符)는 제단 위에 처음부터
놓여 있고, 그걸 들고 남동쪽 잠긴 계단(門)까지 되짚어 나가면 층 돌파다.

★초원 맵(blender/s20_level1.py -> web/level1.*)은 **한 글자도 안 건드린다.**
  이 파일은 그 문법(Buf / mat_tex 곱수 계약 / 콜라이더 emit / 자기 검증)을 물려받되
  전제를 뒤집는다.

    초원: 열린 벌판에 막는 덩어리를 띄엄띄엄 얹는다. 어디나 밝다
    던전: 통째로 막힌 돌덩이에서 방과 통로를 파낸다. 횃불 자리만 밝다

────────────────────────────────────────────────────────────────
★이 파일에서 조정할 값
  CELL(2.0)  : 바꾸면 맵 전체가 그 비율로 커진다. 레이아웃(칸 좌표)은 안 고쳐도 된다
  TORCH_R    : 횃불 웅덩이 반경. 어둠과 밝음의 리듬 폭이다
  AMB        : 아무 빛도 없는 자리의 밝기. 0 으로 내리면 캐릭터가 검은 판에 뜬다
  PAL        : 목표색 표. 화면 평균색이 정확히 이 값이 되도록 곱수를 푼다

★좌표계 함정 (초원 맵과 같다)
  블렌더는 Z 가 위다. glTF 는 export_yup=True 로 나가므로 three.js 에서는 Y 가 위다.
    three.x = blender.x / three.y = blender.z / three.z = -blender.y
  그래서 이 스크립트는 **게임 좌표(gx, gz, y)** 로만 배치를 적고,
  블렌더에 넣을 때만 (bx, by, bz) = (gx, -gz, y) 로 바꾼다.
  level2.json 에 적히는 숫자는 전부 three.js 좌표다.

★어둠은 실광원이 아니라 **정점색(glTF COLOR_0)** 으로 굽는다
  씬 조명은 main.js 것 그대로 두고 여기서 명암을 구워 넣는다. 툰 파이프라인 관례고,
  광원을 스무 개 켜는 것보다 압도적으로 싸다. 초원 맵이 절벽 단 차이 음영을 내던
  그 장치(Buf.c)를 색까지 실어 쓴다 - 횃불 자리는 따뜻하고 구석은 차다.

★곱수 계약 (초원 맵과 같다. 어기면 팔레트가 조용히 밀린다)
    화면색 = baseColorFactor x 타일 x 정점색
    baseColorFactor = 목표색(선형) / 타일 평균(선형) / 정점색 평균
  ★정점색 평균을 **손으로 어림하지 않는다.** 버퍼를 다 채운 뒤 면적 가중으로 재서
    그 값으로 재질을 만든다(두 번 훑기). s20 은 이 값을 상수로 적어 두고 어긋날
    때마다 고쳤는데, 그게 v86·v89·v94 에서 세 번 회귀를 냈다.

★메시 이름 규칙 (web/level.js 계약)
    COL_*   = 막는다 (colliders[] 와 1:1)
    DECO_*  = 안 막는다
    ★FLOOR 로 시작하는 이름을 **쓰면 안 된다.** level.js 가 그 재질의 셰이더를
      기워 초원용 스플랫(풀·흙 타일)을 얹는다. 던전 바닥은 DGFLOOR 다.
"""

import bpy
import os
import json
import math
import random
import numpy as np

# ★기본 시작 파일에는 Cube/Camera/Light 가 들어 있다. 안 지우면 glb 안에
#   정체불명의 Cube 가 같이 나간다.
bpy.ops.wm.read_homefile(use_empty=True)

ROOT = "/Users/lbj/Documents/gameproject"
OUT_GLB = os.path.join(ROOT, "web", "level2.glb")
OUT_JSON = os.path.join(ROOT, "web", "level2.json")
# ★굽는 도중에 게임이 web/level2.glb 를 읽으면 반쪽짜리 파일을 받는다.
#   옆에 _tmp 로 다 쓴 뒤 os.replace 로 갈아끼운다(같은 파일시스템 rename 은 원자적이다).
TMP_GLB = os.path.join(ROOT, "web", "level2_tmp.glb")
TMP_JSON = os.path.join(ROOT, "web", "level2_tmp.json")
TMP = os.environ.get("TMPDIR_LEVEL") or "/tmp"

# ★난수는 **한 스트림**만 쓴다. 여러 개를 섞으면 어느 한 곳을 고칠 때 나머지 배치가
#   통째로 흔들려서 "무엇을 바꿨는지"를 렌더로 비교할 수 없게 된다.
RND = random.Random(40_1)


# ═════════════════════════════════════════════════════════════
# 1) 치수
# ═════════════════════════════════════════════════════════════
CHAR_H = 1.75         # 캐릭터 키. 모든 치수를 이걸로 잰다

CELL = 2.0            # 칸 한 변(m)
GRID = 28             # 28 x 2.0 = 56m 정사각 (오너 지시: 내부 공간 ~56x56)
SIZE = CELL * GRID    # 56.0
HALF = SIZE / 2.0     # 28.0

FLOOR_Y = 0.02        # 바닥 높이. 캐릭터 발이 2cm 잠긴다

# ── 벽 높이 (docs/dungeon1-design.md 5절의 계산) ──
# 카메라가 고정 쿼터뷰 yaw 0 이라 **벽은 플레이어보다 남쪽에 있을 때만** 가린다.
# 시선 기울기 tan(0.86rad) = 1.16 이므로, 남쪽 d 미터 벽은 1.16*d 를 넘으면 발치를 가린다.
WALL_FRONT_H = 1.45   # 북쪽 이웃이 걸을 수 있는 벽 = 그 방의 **앞벽**. 1.25m 안까지 붙어야 가려진다
# ★13차B. 3.10 -> 3.60. 뒷벽은 **정의상 플레이어보다 북쪽**이라 아무리 높여도 안 가린다
#   (가리는 벽은 남쪽 벽뿐이고 그건 앞벽 1.45 다). 컨셉의 아치가 3.2m 높이로 서려면
#   벽이 그보다 커야 하고, 높이 감쇠(HFALL)가 윗동을 어둠으로 지운다.
WALL_BACK_H = 3.60    # 남쪽 이웃이 걸을 수 있거나 속 채움 = **뒷벽**. 방을 닫는다
# ★★맵 바깥 테두리. 북·동·서는 **하늘을 막는 배경**이라 훨씬 높다.
#   첫 판은 4.2m 였는데 인게임 컷에서 화면 위 구석에 하늘색이 새어 들어왔다
#   (증거 shot_04_어둠_통로 · shot_06_탈출계단). 화면 맨 위 광선은 카메라에서
#   37.3도로 내려오므로 플레이어 2m 앞의 벽은 4.7m, 5m 앞은 2.4m 를 넘겨야 화면 끝을
#   메운다. 테두리는 그보다 멀리 있으니 넉넉히 7.5m 를 준다.
WALL_EDGE_H = 7.50
# ★남쪽 테두리만 낮다. 카메라가 언제나 플레이어의 남쪽에 있으므로 여기를 높이면
#   낙하방 남단에 선 플레이어를 통째로 가린다(z=27 벽 기준 5.8m 를 넘으면 가린다).
WALL_EDGE_S_H = 4.20

# ★★콜라이더를 칸 경계에서 얼마나 **안으로** 넣는가. 이 값이 통로의 실제 폭이다.
#   web/nav.js 는 1.6m 격자의 칸 중심에 **반경 0.55** 로 서 볼 수 있는지 물어서
#   "요괴가 지나갈 수 있는 칸"을 만든다. 폭 4.0m 통로의 통과 띠는
#       4.0 - 2*0.55 + 2*INSET
#   이고, 1.6m 격자에서 **두 줄**이 항상 살아남으려면 이 띠가 3.2m 를 넘어야 한다
#   (격자가 통로와 정렬돼 있다는 보장이 없다. 실제로 INSET 0.06 으로 구웠더니
#    K2·K4·K12 세 통로가 한 줄로 떨어졌다 - 요괴가 문에 끼는 자리다).
#       INSET 0.22 -> 띠 3.34m > 3.2  ✓
#   대신 몸이 벽에 0.22m 파묻힌다. 플레이어 반경 0.35 라 **중심은 벽 밖에 남고**
#   어깨만 살짝 겹친다(초원 맵도 같은 이유로 0.34 를 쓴다).
WALL_INSET = 0.22

# ── 조명 ──
# ★★14차(브롤스타즈·포트나이트 화풍). 오너 직접 지시:
#   **"브롤스타즈, 포트나이트 풍의 그림체 맵을 원했는데 지금과 많이 다르다. 다시."**
#   13차까지의 목표(디아블로급 남색 어둠 + 국소 웜)는 **폐기**다. 컨셉이 뒤집혔다.
#
#     컨셉 실측         13차 목표(폐기)        14차 목표(incoming/codex_dungeon2)
#     화면 Y평균         0.021                 **0.177**   (여덟 배)
#     Y 하위 25%         0.0043                **0.039**
#     진짜 어둠(<2%)     73%                   **13%**
#     띠별 R/B          0.23 / 0.85 / 1.19     0.50 / 1.28 / **7.64 / 9.94**
#     띠별 채도 S        0.75 / 0.40 / 0.52    0.61 / 0.50 / **0.62 / 0.65**
#
#   즉 (가) 여섯 배 밝고 (나) 어둠이 **검정이 아니라 채도 있는 보라·코발트**이고
#   (다) 밝은 자리는 훨씬 더 뜨거운 호박색이다. "잘 안 보이는 어둠"은 이번 판에서
#   미덕이 아니라 **결함**이다(오너: "화면 전체가 잘 읽히는 밝은 카툰").
#
#   색은 여전히 세 층으로 만든다. 층의 역할은 그대로고 값만 뒤집혔다.
#       ① 씬 조명(main.js 던전 분기)  = **밝은 웜광**.  E = (0.993, 0.830, 0.895)
#          (13차는 0.391,0.565,0.864 = 차고 어두운 달빛이었다. 휘도 1.55배 · R/B 두 배)
#       ② 정점색(COLOR_0, 이 파일)     = 보라 어둠 <-> 호박 웜의 기울기
#       ③ 이미시브 데칼(이 파일)       = 횃불 둘레의 밝기 폭(COLOR_0 이 1 에서 잘려
#          못 내는 구간을 이 층이 낸다)
#
# AMB : 아무 빛도 없는 자리. ★13차의 (0.034,0.076,0.196) 에서 **열세 배** 올렸다.
#       그 값은 "빛이 안 닿으면 안 보인다"는 계약이었고 이번 컨셉은 정반대다.
#       색은 컨셉의 그늘 실측(#382f4c H258 S38 · #1a1636 H248 S59)을 따라 **자주빛
#       보라**로 둔다 — R 이 G 보다 높아야 남색이 아니라 보라로 읽힌다.
# ★★AMB 를 올리면 횃불이 얹힐 자리가 그만큼 줄어든다(COLOR_0 은 1 에서 잘린다).
#   0.46 이면 남는 폭이 2.2배뿐이라 TORCH_P 를 13차의 1.06 에서 0.62 로 같이 내렸다.
#   빛의 드라마는 이제 정점색이 아니라 **이미시브 웜 풀**이 낸다(③층).
AMB = np.array((0.46, 0.39, 0.58), np.float32)
# ★AMB_MIN 은 높이 감쇠·접지 어둠이 곱해진 뒤의 바닥이다. 13차는 0.028(사실상 검정)
#   이었다. 이번엔 컨셉의 제일 깊은 구석(#1a1636, Y 0.011)이 바닥이라 0.30 이다.
AMB_MIN = 0.30        # 어떤 채널도 이보다 어두워지지 않는다
# 컨셉 횃불 둘레 실측 #cf8c3e(H32 S70) · 코어 #f6b556. 13차보다 조금 덜 붉다 —
# 바닥 알베도가 이미 크림(R/B 4.0)이라 빛까지 새빨가면 주홍으로 넘어간다.
TORCH_RGB = np.array((1.00, 0.48, 0.13), np.float32)   # 횃불 빛의 색
# ★14차. 계단의 찬 빛을 파랑에서 **청록**으로 옮겼다. 이 팔레트에서 파랑은
#   어둠의 색이라(AMB 가 보라·코발트) 파란 빛은 "빛"으로 안 읽힌다.
COLD_RGB = np.array((0.30, 0.86, 0.92), np.float32)    # 계단·천장 틈의 찬 빛
MOSS_RGB = np.array((0.06, 0.16, 0.04), np.float32)    # 벽 밑동 이끼(정점색에 더한다)
TORCH_R = 4.2         # 횃불 반경(m). 이 거리에서 세기의 1/2 x 창 이 남는다
# ★★13차는 1.06 이었다. AMB 가 0.034 -> 0.46 으로 올라가 **남은 폭이 0.54 뿐**이라
#   같은 세기를 주면 횃불 둘레가 통째로 1.0 에서 잘린 평평한 판이 된다(계조 소실).
TORCH_P = 0.62        # 횃불 세기
# ★★꼬리를 자르는 창(window). 1/(1+(d/R)^2) 만 쓰면 꼬리가 길어서 광원 마흔 개가
#   서로를 더해 맵 전체가 1.0 으로 포화된다. 사거리 밖은 0 이 되게 잘라야 웅덩이가 생긴다.
# ★14차. 2.5 -> 2.9. 컨셉의 홀은 **바닥 전체가** 호박색이다(횃불에서 4m 떨어진
#   한복판도 R/B 7 대다). 13차의 "웅덩이 여럿"이 아니라 "방 하나가 통째로 따뜻"이
#   이 화풍이다. 창 지수(w^2.7)는 그대로라 가까운 쪽 대비는 안 잃는다.
TORCH_RANGE = 2.9     # 사거리 = R 의 몇 배까지 빛이 닿는가
# ★★TOP_BONUS 를 0.22 -> 0.10 으로 내렸다. 벽 **윗면은 윗면 조도(E 0.87)** 를 받아
#   바닥과 같은 밝기로 뜬다. 쿼터뷰라 그 면적이 크고, 색이 라일락(찬 색)이라
#   화면 밝은 띠를 냉기로 채워 R/B 를 끌어내렸다(판정 3.7 vs 컨셉 7.6~9.9).
#   컨셉의 밝은 띠는 거의 전부 **횃불 받은 바닥**이다.
TOP_BONUS = 0.14      # 벽 마루(윗면)에 얹는 밝기. 두께가 읽히게 한다

# ★★높이 감쇠 — 쿼터뷰에서 벽 상단을 어둠에 녹이는 장치.
# ★14차. HFALL_MIN 0.42 -> 0.78. 컨셉의 벽 꼭대기는 **어둠에 안 녹는다** — 갓돌이
#   화면에서 제일 밝은 라일락(#8868a9)이다. 13차의 0.42 는 "천장 없는 어둠"을
#   흉내내려던 값인데 이 화풍에는 그 어둠 자체가 없다. 완전히 없애지는 않는다:
#   테두리 벽(7.5m)이 바닥과 같은 밝기면 방의 위아래 구분이 사라진다.
HFALL_Y0 = 2.60       # 여기까지는 안 건드린다
HFALL_SPAN = 3.60     # 이만큼 올라가는 동안
HFALL_MIN = 0.78      # 여기까지 어두워진다(테두리 벽 7.5m 꼭대기가 이 값)

# 횃불 불꽃이 걸리는 높이. 앞벽(1.45)보다 확실히 높아야 벽 위로 떠 보이지 않는다
# = 횃불은 **뒷벽에만** 단다(아래 자기 검증이 확인한다).
TORCH_Y = 2.05


# ═════════════════════════════════════════════════════════════
# 2) 좌표 변환
# ═════════════════════════════════════════════════════════════
def gx_of(c):
    """칸 인덱스 c(0..GRID-1) 의 중심 게임 X"""
    return -HALF + (c + 0.5) * CELL


def gz_of(r):
    return -HALF + (r + 0.5) * CELL


def gxf(cf):
    """칸 **경계** 단위의 실수 좌표 -> 게임 X. 칸 c 의 중심은 cf = c + 0.5"""
    return -HALF + cf * CELL


def gzf(rf):
    return -HALF + rf * CELL


def cell_of(gx, gz):
    c = int((gx + HALF) / CELL)
    r = int((gz + HALF) / CELL)
    return (min(GRID - 1, max(0, c)), min(GRID - 1, max(0, r)))


def bpos(gx, gz, y):
    """게임 좌표 -> 블렌더 좌표"""
    return (gx, -gz, y)


def yaw_to(gx, gz, tx, tz):
    """three.js 회전 Y. main.js 는 targetYaw = atan2(move.x, move.z) 라 yaw 0 이 +Z 를 본다."""
    return math.atan2(tx - gx, tz - gz)


# ═════════════════════════════════════════════════════════════
# 3) 레이아웃 — 통째로 막힌 돌덩이에서 방과 통로를 파낸다
# ═════════════════════════════════════════════════════════════
# 칸 좌표는 (c0, r0, c1, r1) 닫힌 구간. r 이 작을수록 북쪽(-Z), c 가 작을수록 서쪽(-X).
# 값의 근거는 docs/dungeon1-design.md 1절 표에 그대로 있다.
ROOMS = [
    # id,          c0, r0, c1, r1,  뜻
    ("R_ALTAR",     9,  2, 18,  7),   # 제단 방. 증표가 여기 있다
    ("R_NW",        2,  2,  6,  7),   # 북서 우물방
    ("R_NE",       21,  2, 25,  7),   # 북동 취사장
    ("R_WEST",      2, 13,  6, 18),   # 서쪽 창고
    ("R_EAST",     21, 13, 25, 18),   # 동쪽 감옥
    ("R_HALL",     11, 10, 16, 18),   # 중앙 회랑(지름길)
    ("R_ENTRY",    10, 21, 16, 25),   # 낙하방. 여기서 시작한다
    ("R_STAIR",    20, 21, 25, 25),   # 계단방. 잠긴 탈출 계단
]

# 통로는 전부 폭 2칸(4.0m). 왜 4.0 인가는 설계 문서 "문폭" 절에 계산이 있다
# (nav.js 가 1.6m 격자 x 반경 0.55 로 판정하므로 W-1.1 이 실제 통과 폭이다).
CORRIDORS = [
    ("K1",  12, 19, 13, 20),   # 낙하방 <-> 중앙 회랑 (가운데 갈래)
    ("K2",   3, 22,  9, 23),   # 낙하방 <-> 서쪽 통로
    ("K3",   3, 19,  4, 23),   # 서쪽 통로 <-> 서쪽 창고
    ("K4",  17, 22, 19, 23),   # 낙하방 <-> 계단방 (동쪽 갈래. 잠긴 계단을 일찍 본다)
    ("K5",  23, 19, 24, 20),   # 계단방 <-> 동쪽 감옥
    ("K6",   7, 15, 10, 16),   # 서쪽 창고 <-> 중앙 회랑
    ("K7",  17, 15, 20, 16),   # 동쪽 감옥 <-> 중앙 회랑
    ("K8",   3,  8,  4, 12),   # 서쪽 창고 <-> 북서 우물방
    ("K9",  23,  8, 24, 12),   # 동쪽 감옥 <-> 북동 취사장
    ("K10",  7,  4,  8,  5),   # 북서 우물방 <-> 제단 방
    ("K11", 19,  4, 20,  5),   # 북동 취사장 <-> 제단 방
    ("K12", 13,  8, 14,  9),   # 중앙 회랑 <-> 제단 방 (지름길의 끝)
]

# walk[r][c] = True 면 걸을 수 있다. 처음엔 통째로 막혀 있다
walk = [[False] * GRID for _ in range(GRID)]
ROOM_OF = {}        # (c, r) -> 방 id


def carve(c0, r0, c1, r1, tag=None):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            walk[r][c] = True
            if tag and (c, r) not in ROOM_OF:
                ROOM_OF[(c, r)] = tag


for (rid, c0, r0, c1, r1) in ROOMS:
    carve(c0, r0, c1, r1, rid)
for (kid, c0, r0, c1, r1) in CORRIDORS:
    carve(c0, r0, c1, r1, kid)

ROOM_BOX = {rid: (c0, r0, c1, r1) for (rid, c0, r0, c1, r1) in ROOMS}
CORR_BOX = {kid: (c0, r0, c1, r1) for (kid, c0, r0, c1, r1) in CORRIDORS}

# ── 스폰 정면 통로 ★"첫 15초"가 여기서 결정된다 ──
# 초원(15m x 4.4m)보다 짧다. 낙하방이 10m 깊이라 그만큼이 없다. 첫 화면에 들어오는
# 구간만 확실히 비우면 목적은 같다. ★소품 배치와 자기 검증이 **같은 상수**를 본다
# (첫 판에서 배제 창은 5.5m 인데 검사는 6.5m 까지 훑어서 잔해 하나가 새어 들어왔다).
SPAWN_LANE_LEN = 5.0
SPAWN_LANE_HALF = 1.5

# 스폰 자리. 낙하방 남쪽에 셋. 소품 배치가 여기를 침범하면 안 되므로 먼저 정한다
ENT_C0, ENT_R0, ENT_C1, ENT_R1 = ROOM_BOX["R_ENTRY"]
SPAWN_PTS = [
    (gx_of(ENT_C0 + 1), gz_of(ENT_R1 - 1)),
    (gx_of(13), gz_of(ENT_R1 - 1)),
    (gx_of(ENT_C1 - 1), gz_of(ENT_R1 - 1)),
]


def blocked(c, r):
    if c < 0 or r < 0 or c >= GRID or r >= GRID:
        return True
    return not walk[r][c]


# ── 벽 높이 등급 ──
# FRONT : 북쪽 이웃이 걸을 수 있다 = 그 칸에 선 플레이어에게 이 벽은 남쪽(= 카메라 쪽)이다
# BACK  : 남쪽 이웃이 걸을 수 있거나 속 채움. 화면 위쪽 배경이라 높아야 방이 닫힌다
# EDGE  : 맵 바깥 테두리
H_FRONT, H_BACK, H_EDGE = 0, 1, 2


def wall_class(c, r):
    if c <= 0 or r <= 0 or c >= GRID - 1 or r >= GRID - 1:
        return H_EDGE
    if not blocked(c, r - 1):
        return H_FRONT          # 북쪽이 트였다 -> 낮춘다(가림 방지)
    return H_BACK


WALL_H_OF = {H_FRONT: WALL_FRONT_H, H_BACK: WALL_BACK_H, H_EDGE: WALL_EDGE_H}


# ═════════════════════════════════════════════════════════════
# 4) 빛 — 횃불 목록과 정점 밝기 함수
# ═════════════════════════════════════════════════════════════
# LIGHTS: (gx, gz, y, 반경, 세기, 색)
LIGHTS = []
TORCH_PROPS = []      # 실제로 벽에 다는 횃불(불꽃 지오메트리). (gx, gz, y, face)


def add_light(gx, gz, y, rad, power, rgb, near=0.0):
    """near = 근접 웜 세기 배수(13차C). 횃불만 1.0 이고 달빛·계단은 0 이다 —
    찬 빛은 넓게 번지는 게 맞고, 뜨거운 불만 옆면을 국소로 태운다."""
    LIGHTS.append((gx, gz, y, rad, power, np.asarray(rgb, np.float32), near))


def face_of_wall(c, r):
    """벽 칸이 어느 쪽으로 트여 있는가. 횃불은 트인 쪽으로 불꽃을 내민다."""
    if not blocked(c, r + 1):
        return "S"          # 남쪽이 방 = 이 벽은 방의 북벽
    if not blocked(c, r - 1):
        return "N"
    if not blocked(c + 1, r):
        return "E"
    if not blocked(c - 1, r):
        return "W"
    return None


FACE_DIR = {"N": (0.0, -1.0), "S": (0.0, 1.0), "E": (1.0, 0.0), "W": (-1.0, 0.0)}


def can_mount(c, r):
    """이 벽 칸에 횃불을 달 수 있는가.

    ★뒷벽(3.10m)에만 단다. 앞벽(1.45m)에 달면 불꽃(2.05m)이 벽 위로 떠서
      허공에 뜬 불덩이가 된다. 그리고 앞벽은 화면 맨 아래라 어차피 안 보인다."""
    if not blocked(c, r):
        return False
    if wall_class(c, r) == H_FRONT:
        return False
    return face_of_wall(c, r) is not None


# ★13차B. 횃불이 두 종류다(컨셉에 둘 다 나온다).
#   PED  받침대형 — 벽 앞 0.62m 에 선 기둥 + 사발. 컨셉 홀의 주역이다
#   WALL 벽걸이형 — 쇠 팔에 꽂힌 관솔. 통로와 좁은 자리
#   ★어느 쪽인지를 **여기서** 정해야 한다. 불꽃 높이가 다르면 광원 높이도 달라야 하고,
#     광원은 지오메트리보다 먼저(정점색을 굽기 전에) 등록돼야 하기 때문이다.
PED_Y = 1.34          # 받침대형 불꽃 높이
PED_OUT = 0.62        # 벽면에서 나온 거리


def mount_torch(c, r):
    """벽 칸 (c, r) 의 트인 면에 횃불을 단다."""
    if not can_mount(c, r):
        return False
    dx, dz = FACE_DIR[face_of_wall(c, r)]
    gx = gx_of(c) + dx * (CELL * 0.5 - 0.12)
    gz = gz_of(r) + dz * (CELL * 0.5 - 0.12)
    # 받침대는 **방 안**에만 세운다(통로에 세우면 폭 4.0m 계약이 깨진다)
    fx, fz = gx + dx * PED_OUT, gz + dz * PED_OUT
    fc, fr = cell_of(fx, fz)
    in_room = (not blocked(fc, fr)) and not ROOM_OF.get((fc, fr), "").startswith("K")
    # ★스폰 정면 통로에는 받침대를 못 세운다(콜라이더가 첫 15초를 막는다).
    #   배제 창은 자기 검증 4)가 훑는 범위와 **같은 상수**를 본다.
    for (_sx, _sz) in SPAWN_PTS:
        if (abs(fx - _sx) < SPAWN_LANE_HALF + 0.5
                and -(SPAWN_LANE_LEN + SPAWN_LANE_HALF) - 0.5 < fz - _sz
                < SPAWN_LANE_HALF + 0.5):
            in_room = False
    ped = in_room and (len(TORCH_PROPS) % 2 == 0)
    y = PED_Y if ped else TORCH_Y
    TORCH_PROPS.append((gx, gz, y, dx, dz, ped))
    add_light(gx + dx * (PED_OUT if ped else 0.30), gz + dz * (PED_OUT if ped else 0.30),
              y, TORCH_R, TORCH_P, TORCH_RGB, near=1.0)
    return True


def pick_spread(cands, n):
    """후보 칸 중에서 서로 제일 멀리 떨어진 n 개를 고른다(탐욕적 최원점).

    ★손으로 좌표를 스무 개 적으면 레이아웃을 한 칸만 옮겨도 절반이 벽에서 떨어진다
      (첫 판에서 스무 자루가 앞벽에 걸려 통째로 버려졌다). 후보를 **찾아서** 고른다."""
    if not cands or n <= 0:
        return []
    out = [cands[0]]
    while len(out) < n and len(out) < len(cands):
        best, bd = None, -1
        for cd in cands:
            if cd in out:
                continue
            d = min((cd[0] - o[0]) ** 2 + (cd[1] - o[1]) ** 2 for o in out)
            if d > bd:
                bd, best = d, cd
        if best is None:
            break
        out.append(best)
    return out


# ── 방마다 횃불 자리 ──
# 방 하나에 둘~셋. 방 한가운데가 0.55~0.75, 구석이 0.30 근처가 된다.
# ★수를 늘리면 그만큼 리듬이 죽는다. 어둠이 있어야 밝음이 정보가 된다.
_torch_bad = []
for (rid, c0, r0, c1, r1) in ROOMS:
    ring = []
    for c in range(c0 - 1, c1 + 2):
        ring += [(c, r0 - 1), (c, r1 + 1)]
    for r in range(r0, r1 + 1):
        ring += [(c0 - 1, r), (c1 + 1, r)]
    cands = [x for x in ring if can_mount(*x)]
    area = (c1 - c0 + 1) * (r1 - r0 + 1)
    want = 3 if area >= 36 else 2
    if rid == "R_HALL":
        want = 5              # 컨셉 홀은 횃불이 여덟 자루다. 웅덩이가 좁아 리듬은 산다
    if rid == "R_ALTAR":
        want = 5              # 제단 방은 목표라서 유일하게 환하다
    if rid == "R_ENTRY":
        want = 2              # 낙하방은 천장 구멍의 찬 빛이 주역이다
    for cd in pick_spread(cands, want):
        if not mount_torch(*cd):
            _torch_bad.append(cd)

# ── 통로 횃불 ──
# **한쪽 끝에만** 한 자루. 통로 한가운데가 가장 어둡다
# = 방(밝다) -> 어둠 -> 방(밝다) 리듬이 화면에서 읽힌다.
for (kid, c0, r0, c1, r1) in CORRIDORS:
    ring = []
    for c in range(c0 - 1, c1 + 2):
        ring += [(c, r0 - 1), (c, r1 + 1)]
    for r in range(r0 - 1, r1 + 2):
        ring += [(c0 - 1, r), (c1 + 1, r)]
    cands = [x for x in ring if can_mount(*x)]
    long_side = max(c1 - c0, r1 - r0) + 1
    for cd in pick_spread(cands, 2 if long_side >= 5 else 1):
        if not mount_torch(*cd):
            _torch_bad.append(cd)

# ── 특수 광원 (지오메트리가 따로 있는 것들) ──
ALTAR_C, ALTAR_R = 13, 3          # 제단 칸(방 R_ALTAR 안. 북쪽에 붙인다)
ALTAR_X, ALTAR_Z = gxf(ALTAR_C + 1.0), gz_of(ALTAR_R)   # 제단 중심(칸 경계에 걸친다)
ALTAR_TOP = 0.30                  # 제단 단 높이(platforms[] 로 나간다)
# 제단 화로 둘. 던전에서 가장 밝은 자리가 목표다
add_light(ALTAR_X - 2.4, ALTAR_Z + 0.2, 1.15, 7.0, 0.95, TORCH_RGB, near=1.0)
add_light(ALTAR_X + 2.4, ALTAR_Z + 0.2, 1.15, 7.0, 0.95, TORCH_RGB, near=1.0)

CAMP_X, CAMP_Z = gx_of(23), gz_of(5)      # 북동 취사장 모닥불
add_light(CAMP_X, CAMP_Z, 0.55, 6.2, 0.85, TORCH_RGB, near=1.0)

SHAFT_X, SHAFT_Z = gx_of(13), gz_of(23)   # 낙하방 천장 구멍에서 내려오는 찬 빛
# ★13차D. 반경 6.0 -> 3.4. 오너 "달빛 샤프트는 국소 연출로만."
#   찬 빛의 반경이 횃불(3.8)보다 넓으면 달빛이 방을 통째로 물들여서 던전이
#   **지붕 없는 마당**이 된다(옛 판 화면의 파란 안개 절반이 이 둘이었다).
#   컨셉의 샤프트는 바닥에 지름 4m 짜리 웅덩이 하나를 만들고 그걸로 끝난다.
add_light(SHAFT_X, SHAFT_Z, 2.6, 3.4, 0.72, COLD_RGB)

# ── 세워 두는 화로 (13차B 신설) ──
# ★★컨셉 홀의 주역은 벽걸이 관솔이 아니라 **바닥에 선 받침대 화로**다. 기둥 옆에
#   서서 기둥 밑동을 아래에서 비추고, 그래서 기둥이 어둠에서 형체로 떠오른다.
#   1차 홀이 텅 비어 보인 이유의 절반이 이거였다 - 기둥이 있었지만 안 보였다.
# ★광원은 지오메트리보다 **먼저** 등록해야 한다(정점색을 굽기 전에 목록이 완성돼야
#   한다). 그래서 자리를 여기서 손으로 적고, 아래 11절이 같은 좌표에 물건을 세운다.
FREE_BRAZIERS = [
    (-5.0, -5.0), (5.0, -5.0), (-5.0, 3.0), (5.0, 3.0),     # 중앙 회랑 기둥 옆
    # ★낙하방은 **스폰 정면 통로**(x -6.5~-3.5 / -2.5~0.5 / 1.5~4.5, z 16~22.5)를
    #   피해야 한다. 첫 배치가 거기 걸려 자기 검증이 두 건 실패로 잡았다.
    (-7.6, 16.4), (5.2, 16.4),                              # 낙하방 양 끝
    (-7.2, -17.2), (7.2, -17.2),                            # 제단 방 입구
]
for (_bx, _bz) in FREE_BRAZIERS:
    add_light(_bx, _bz, 1.34, TORCH_R * 1.05, TORCH_P * 1.05, TORCH_RGB, near=1.0)

STAIR_C0, STAIR_R0 = 22, 21               # 계단 바닥 칸(북으로 오른다)
STAIR_X = gxf(STAIR_C0 + 1.0)
STAIR_Z = gz_of(STAIR_R0 + 1)
# 계단 위 찬 빛. 유일한 출구가 유일하게 차다
# ★13차D. 6.4 -> 3.6 (위 샤프트와 같은 이유. 국소여야 '출구'로 읽힌다)
add_light(STAIR_X, gz_of(STAIR_R0) - 0.6, 1.9, 3.6, 0.92, COLD_RGB)

WELL_X, WELL_Z = gx_of(4), gz_of(5)       # 북서 우물


def height_fall(y):
    """높이 감쇠. 벽 상단이 어둠으로 사라진다(쿼터뷰 던전의 천장 노릇)."""
    if y <= HFALL_Y0:
        return 1.0
    t = min(1.0, (y - HFALL_Y0) / HFALL_SPAN)
    t = t * t * (3.0 - 2.0 * t)                   # smoothstep. 급하면 띠가 보인다
    return 1.0 - (1.0 - HFALL_MIN) * t


# ★★면이 광원을 보고 있는가(N·L). 13차B 에서 제일 크게 그림을 바꾼 한 줄이다.
#   1차는 정점색이 **거리만** 봤다. 그래서 기둥·아치·벽이 사방 똑같은 밝기가 되어
#   쿼터뷰에서 통째로 납작한 판으로 읽혔다("회색 상자"의 나머지 절반).
#   컨셉에서 기둥이 둥글게 보이는 것은 횃불 쪽 면이 밝고 반대쪽이 죽기 때문이다.
#   NL_FLOOR 는 완전히 등진 면에도 남기는 몫이다(0 이면 뒷면이 시커먼 구멍이 된다).
NL_FLOOR = 0.60

# ═════════════════════════════════════════════════════════════
# 4b) 13차C — 근접 웜(횃불이 옆면을 데운다) · 바닥 매크로 변주 · 벽 밑 접지 어둠
# ═════════════════════════════════════════════════════════════
# 오너 지시: "불꽃 있으면 주변 밝아지는 효과는 왜 이리 이상하냐. 그리고 던전 타일도
#            너무 타일스럽고. 그림인 듯한 느낌이지만 3D인, 그런 느낌으로 가야지."
#
# ★진단(실측). 옛 판의 횃불 빛은 **너무 넓게 퍼진 한 겹**이었다.
#     벽 정점색 R/B  0.6m 1.66 / 1.8m 1.41 / 3.6m 1.19 / 5.4m 0.64
#   = 5m 넘게 완만하게 데워진다. 컨셉(concept_hall.png)의 횃불은 반대다 — 1m 안쪽이
#   황백으로 타고 2m 밖은 이미 남색이다. "가까이 세다"가 아니라 "**빨리 죽는다**"가
#   횃불의 문법이고, 그 대비가 없으니 빛이 정보가 아니라 안개로 보였다.
#
# 그래서 층을 하나 더 얹는다(넓은 스필은 그대로 두고 그 위에).
#   NEAR_*  = 반경 1.2m 짜리 **근접 웜**. N·L 이 거의 전부라 빛을 본 면만 데워지고
#             뒷면은 차갑게 남는다 = 기둥이 둥글게 서고 벽이 판때기를 벗는다.
NEAR_R = 1.20         # 근접 웜 반경(m). 이 거리에서 세기의 1/2
NEAR_P = 0.42         # 근접 웜 세기 (★14차. AMB 가 0.46 이라 남은 폭이 좁다)
NEAR_RANGE = 2.30     # 사거리 = R 의 몇 배. 넘으면 0(꼬리를 안 남긴다)
NEAR_NL = 0.20        # 등진 면에 남기는 몫. 0.05 = 사실상 안 남긴다(뒷면은 차다)

# ── 바닥 매크로 변주 (탈타일화 ①) ──
# ★격자로 읽히는 원인의 절반은 텍스처가 아니라 **바닥이 통째로 같은 밝기**라는 것이다.
#   4.5m 마다 같은 무늬가 오는데 밝기까지 같으면 눈이 주기를 센다. 격자 주기와 아무
#   상관 없는 3~9m 얼룩을 정점색에 실으면 그 셈이 끊긴다(초원에서 쓴 그 처방이다).
MACRO_A = 0.120       # 큰 얼룩 진폭(곱수). ★14차. 밝은 바닥에서 0.175 는 얼룩 카펫이다
MACRO_S1 = 7.30       # 저주파 파장(m). 격자 4.5m 와 **약분이 안 되는** 수여야 한다
MACRO_S2 = 3.10       # 중주파 파장(m)
# ★13차D 신설. 판 하나 크기(1.05~1.25m)의 옥타브. 13차C 가 남긴 격차
#   "컨셉은 안 밝은 자리에도 **판마다** 명암이 있다"가 이 주파수다.
#   0.5m 격자에서 1.75m 는 한 주기에 표본 3.5개 = 표현 가능한 제일 잔 결이다
#   (1.2m 로 내리면 표본 2.4개라 격자 모양으로 접힌다 - 실제로 한 번 접혔다).
#   진폭은 작게: 여기가 크면 바닥이 얼룩덜룩한 카펫이 된다.
MACRO_S3 = 1.75       # 판 크기 옥타브(m)
MACRO_W3 = 0.20       # 그 옥타브의 몫(나머지 0.80 을 S1·S2 가 나눈다)
# ── 벽 밑 접지 어둠 (탈타일화 ④) ──
# 벽 발치가 바닥과 같은 밝기면 벽이 바닥 위에 **붕 떠 보인다**. 부드러운 띠를 깐다.
CONTACT_AO = 0.22     # 벽에 딱 붙은 자리에서 몇 % 어두워지는가
CONTACT_R = 0.95      # 그 띠의 폭(m)


def _hash2(ix, iy, seed):
    """격자점 하나에서 0..1. ★random 모듈을 안 쓴다 - 자리로만 정해져야 다시 구울 때
    같은 그림이 나오고, 한 군데를 고쳐도 나머지가 안 흔들린다."""
    h = math.sin(ix * 127.1 + iy * 311.7 + seed * 74.7) * 43758.5453
    return h - math.floor(h)


def _vnoise2(gx, gz, scale, seed):
    """파장 scale(m) 짜리 값잡음. smoothstep 보간이라 띠가 안 보인다."""
    fx, fz = gx / scale, gz / scale
    ix, iz = math.floor(fx), math.floor(fz)
    tx, tz = fx - ix, fz - iz
    tx = tx * tx * (3.0 - 2.0 * tx)
    tz = tz * tz * (3.0 - 2.0 * tz)
    a = _hash2(ix, iz, seed)
    b = _hash2(ix + 1, iz, seed)
    c = _hash2(ix, iz + 1, seed)
    d = _hash2(ix + 1, iz + 1, seed)
    return (a * (1 - tx) * (1 - tz) + b * tx * (1 - tz)
            + c * (1 - tx) * tz + d * tx * tz)


def macro_at(gx, gz):
    """바닥 매크로 명암 곱수. 1 을 중심으로 위아래로 흔든다(평균 1 = 곱수 계약 유지)."""
    n = (_vnoise2(gx, gz, MACRO_S1, 11.0) * 0.68
         + _vnoise2(gx, gz, MACRO_S2, 29.0) * 0.32) * (1.0 - MACRO_W3)
    n += _vnoise2(gx, gz, MACRO_S3, 53.0) * MACRO_W3
    return 1.0 + (n - 0.5) * 2.0 * MACRO_A


def wall_dist(gx, gz):
    """제일 가까운 벽 칸의 면까지 거리(m). 이끼·접지 어둠·마모 데칼이 같이 쓴다."""
    c, r = cell_of(gx, gz)
    best = 9.0
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if not blocked(c + dc, r + dr):
                continue
            cx, cz = gx_of(c + dc), gz_of(r + dr)
            dx = max(0.0, abs(gx - cx) - CELL * 0.5)
            dz = max(0.0, abs(gz - cz) - CELL * 0.5)
            best = min(best, math.hypot(dx, dz))
    return best


def lum(gx, gz, y, moss=0.0, nrm=None):
    """정점 밝기 곱수(RGB). 이 값이 glTF COLOR_0 으로 나간다.

    ★falloff = w^2 / (1 + (d/R)^2),  w = max(0, 1 - d/(R * TORCH_RANGE))
      뒤의 분수만 쓰면 꼬리가 길어 광원끼리 더해져 맵이 통째로 1.0 으로 포화된다.
      앞의 창(w)이 사거리 밖을 0 으로 잘라 **웅덩이**를 만든다.
    ★1 을 넘기면 안 된다. COLOR_0 은 정규화 ushort 라 잘린다.
    ★13차B 에서 셋이 늘었다.
       (가) 높이 감쇠 - 벽 윗동을 어둠에 녹인다
       (나) 이끼 - 벽 밑동·구석의 초록. 컨셉 바닥의 이끼 가장자리가 이 색이다
       (다) 웜 풀의 **감마** - 중심을 더 밝게, 가장자리를 더 빨리 죽인다.
            선형 감쇠는 웅덩이가 아니라 넓은 얼룩으로 읽힌다(1차의 인상).
    """
    acc = AMB.copy()
    for (lx, lz, ly, rad, power, rgb, near) in LIGHTS:
        dx = gx - lx
        dz = gz - lz
        dy = y - ly
        d2 = dx * dx + dz * dz + dy * dy * 0.55   # 세로 거리는 덜 센다(벽면이 통째로 죽는다)
        # ★N·L 은 두 층이 같이 쓴다. 한 번만 구한다
        ndl = None
        if nrm is not None:
            dd = math.sqrt(dx * dx + dz * dz + (y - ly) ** 2) + 1e-4
            ndl = (nrm[0] * (-dx) + nrm[1] * (ly - y) + nrm[2] * (-dz)) / dd
        rng = rad * TORCH_RANGE
        if d2 < rng * rng:
            w = 1.0 - math.sqrt(d2) / rng
            f = power * (w ** 2.7) / (1.0 + d2 / (rad * rad))
            if ndl is not None:
                f *= NL_FLOOR + (1.0 - NL_FLOOR) * max(0.0, ndl)
            acc = acc + rgb * f
        # ── 근접 웜(13차C) ──
        # ★★거리는 **세로를 안 깎는다.** 넓은 스필은 벽면이 통째로 죽는 걸 막으려고
        #   dy 를 0.55 로 눌렀는데, 근접 웜에서 같은 짓을 하면 횃불 위 3m 벽까지
        #   데워져서 다시 안개가 된다. 여기서는 실제 거리를 그대로 쓴다.
        if near > 0.0:
            nrng = NEAR_R * NEAR_RANGE
            dn2 = dx * dx + dz * dz + dy * dy
            if dn2 < nrng * nrng:
                wn = 1.0 - math.sqrt(dn2) / nrng
                fn = near * NEAR_P * (wn ** 3.0) / (1.0 + dn2 / (NEAR_R * NEAR_R))
                if ndl is not None:
                    fn *= NEAR_NL + (1.0 - NEAR_NL) * max(0.0, ndl)
                acc = acc + rgb * fn
    acc = acc * height_fall(y)
    if moss > 0.0:
        acc = acc + MOSS_RGB * moss
    return np.clip(acc, AMB_MIN, 1.0)


# ═════════════════════════════════════════════════════════════
# 5) 타일 — **컨셉 아트에서 잘라 온다** (절차 생성 폐기)
# ═════════════════════════════════════════════════════════════
# ★★13차B 의 방향 전환. 1차는 여기서 값잡음으로 석재를 그렸고, 그 결과가
#   "회색 상자"의 절반이었다. 이번엔 오너 대리 합격판 컨셉 시트를 그대로 쓴다.
#
#       incoming/codex_dungeon/tiles_dungeon.png (2048, 4분할)
#         좌상 이끼 낀 판석 -> web/tex/dg_floor.jpg
#         우상 석벽 블록    -> web/tex/dg_wall.jpg
#         좌하 금 간 바닥   -> web/tex/dg_floor_b.jpg
#         우하 제단 메달리온-> web/tex/dg_medallion.png (알파 데칼)
#
#   후처리는 `tools/dungeon_tex.py` 가 한다(이어붙임화 = tileize.py 의 Moisan
#   periodic 분해 · 큰 명암 얼룩 제거 · 선형 밝기 정규화). 평균색은 그 도구가
#   재서 `web/tex/dungeon_tex.json` 에 적어 둔다 —
#   ★블렌더 파이썬에는 PIL 이 없어서 여기서 png 평균을 직접 못 잰다(LOG.md 옛 함정).
#
# ★UV 스케일은 **컨셉의 판 크기**에서 나온다. 타일 한 장에 판이 대여섯 장 들어 있으니
#   4.5m 를 덮게 하면 판 하나가 0.75~0.9m 다(컨셉에서 고블린 어깨 폭의 두 배쯤).
#   1차의 2.0m 는 판을 0.35m 로 만들어 바닥이 자갈밭처럼 촘촘했다.
TEX_DIR = os.path.join(ROOT, "web", "tex")
WALL_UV_SCALE = 4.6        # 벽. ★14차. 절차 블록 5단 x 3장이라 한 장이 1.53 x 0.92m
#   = 컨셉의 "블록 하나가 사람 몸통급". 3.6 판은 게임 화면에서 여전히 벽돌이었다
#   (컨셉은 벽 높이 3.6m 에 네 단이 들어간다). tools/dungeon_tex.py 의
#   WALL_COURSES · WALL_PER_COURSE 와 **한 짝**이라 같이 움직여야 한다
# ★13차C. 4.5 -> 6.2. 두 가지를 같이 산다.
#   (가) 판 하나가 0.75~0.9m 에서 **1.05~1.25m** 가 된다 - 컨셉의 큰 판석 크기다
#       (컨셉에서 고블린 어깨 폭보다 판이 확실히 크다. 옛 값은 자갈에 가까웠다)
#   (나) 되풀이 주기가 4.5m -> 6.2m. 화면에 들어오는 바닥이 20m 남짓이라
#       되풀이 횟수가 4.4번에서 3.2번으로 준다 = 눈이 주기를 덜 센다
#   해상도는 1024/6.2 = 165 texel/m 로 게임 화면(49 px/m)의 세 배라 여유가 있다
FLOOR_UV_SCALE = 5.0
# ★★바닥 UV 를 살짝 **돌린다**. 되풀이 자체는 못 없애지만, 격자축이 방·벽·통로의
#   직각과 나란하면 눈이 "타일이 벽에 맞춰 깔렸다"고 읽는다 - 그게 격자감의 절반이다.
#   17도는 어느 벽과도 안 맞으면서 판석의 손그림 방향이 부자연스럽지 않은 각이다.
FLOOR_UV_ROT = math.radians(17.0)

with open(os.path.join(TEX_DIR, "dungeon_tex.json")) as _f:
    TEXMETA = json.load(_f)


def load_tex(name, ext="jpg"):
    """web/tex 의 텍스처를 블렌더 이미지로 올리고 **선형 평균**을 같이 돌려준다.

    ★평균은 dungeon_tex.json 에서 읽는다(블렌더에 PIL 이 없다).
    ★colorspace 는 sRGB 그대로 둔다 - 이건 곱수가 아니라 **색**이다."""
    path = os.path.join(TEX_DIR, name + "." + ext)
    if not os.path.exists(path):
        raise SystemExit("[치명] %s 가 없다. `python3 tools/dungeon_tex.py` 를 먼저 돌려라" % path)
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    # 이미시브 스프라이트(웜 풀·달빛·불꽃)는 곱수 계약 밖이라 평균이 필요 없다
    lin = TEXMETA["lin"].get(name, [1.0, 1.0, 1.0])
    print("[타일] %-14s 선형평균 %.3f %.3f %.3f  (%s)"
          % (name, lin[0], lin[1], lin[2], os.path.basename(path)))
    return img, lin


IMG_FLOOR, FLOOR_LIN = load_tex("dg_floor")
IMG_FLOOR_B, FLOOR_B_LIN = load_tex("dg_floor_b")
IMG_WALL, WALL_LIN = load_tex("dg_wall")
IMG_MEDAL, MEDAL_LIN = load_tex("dg_medallion", "png")
IMG_POOL, _ = load_tex("dg_pool", "png")
IMG_POOLC, _ = load_tex("dg_pool_cold", "png")
IMG_SHAFT, _ = load_tex("dg_shaft", "png")
IMG_FLAME, _ = load_tex("dg_flame", "png")
# ★13차C 신설 둘
#   dg_wglow = 횃불이 벽을 타고 오르는 자국(세로로 긴 이미시브 카드)
#   dg_wear  = 바닥 마모·이끼 데칼 2x2 아틀라스(알베도. 조명·정점색을 탄다)
# ★14차 신설. 다듬은 돌(기둥·아치·제단·계단) 전용 타일. 벽 타일과 갈라 놓은 이유는
#   위 dungeon_tex.py 주석에 있다 — 수직면 조도가 낮아 곱수 천장에 부딪혔다.
IMG_BLOCK, BLOCK_LIN = load_tex("dg_block")
IMG_WGLOW, _ = load_tex("dg_wglow", "png")
IMG_WEAR, WEAR_LIN = load_tex("dg_wear", "png")


# ═════════════════════════════════════════════════════════════
# 6) 팔레트 · 재질
# ═════════════════════════════════════════════════════════════
# ★★팔레트를 **감으로 안 적었다.** 컨셉 그림의 구역별 화면색을 재고, 던전 조명의
#   조도로 ACES 를 역산해 알베도로 되돌린 값이다.
#
#     화면색 = sRGB( ACES( E x 알베도 ) )
#     알베도 = screen_to_paint(화면목표, E)
#       tools/color_contract.py · renders/history/v99_wave14/dungeon_bs/scripts/bs_plan.py
#
#   ★14차에서 E 가 두 개다. 13차는 윗면 조도 하나로 전부 풀었는데, 이 판은 바닥이
#     밝고 벽이 어두운 것이 그림의 뼈대라 **면 방향을 나눠 풀어야** 값이 맞는다.
#       윗면(바닥·제단 윗단)  E = (0.993, 0.830, 0.895)   휘도 0.869  R/B 1.11
#       수직면(벽·기둥·아치)  E = (0.469, 0.374, 0.540)   휘도 0.406  R/B 0.87
#     반구광이 수직면에서 sky/ground 반반이 되고 키라이트가 거의 안 닿아서 그렇다.
#     컨셉도 정확히 그 비율이다(바닥 Y 0.27~0.39 : 벽 Y 0.027~0.080).
#
#   컨셉 실측(incoming/codex_dungeon2) -> 이 맵의 화면 목표
#     크림 판석 #e3b983  보라 블록 #472f5d  자주 #4f2944  코발트 #232b52
#     청록 #33555d  라일락 #706692  호박 웜 #cf8c3e  깊은 어둠 #1a1636
#
#   ★13차와의 차이가 여기 다 있다: 13차 바닥 목표는 #1c1e20(화면 V 12%)이었고
#     이번은 #9a7551(V 60%)이다. **다섯 배 밝다.**
PAL = {
    # (알베도hex, 화면목표hex) - 화면목표는 근거를 남기려고 같이 적는다
    # ★1차 판정에서 바닥이 컨셉보다 어둡고 덜 크림이었다(밝은 띠 Y 0.32 vs 0.39).
    "floor":  "977d50",     # 화면 #a9804f  크림 판석 바닥 (윗면 E)
    "dirt":   "776546",     # 화면 #82603e  잔해 둘레 부스러기
    "rubble": "666f7e",     # 화면 #3f3a5e  부서진 석재(벽보다 밝다 = 얹힌 물건)
    # ★통로 컷이 컨셉보다 어두웠다(Y평균 0.138 vs 0.177). 통로는 화면의 절반이 벽이다.
    "wall":   "5f6573",     # 화면 #33304f  벽 블록 (수직면 E)
    # ★1차 굽기에서 곱수가 1.022 로 잘렸다(계약 파기). 목표 휘도를 2.5% 내려
    #   곱수에 자리를 만든다 — 13차D 가 세 번 잡고서야 앉힌 그 손잡이다.
    "cut":    "677f82",     # 화면 #3e3a5f  기둥·아치·문설주. 사람이 다듬은 돌
    "altar":  "798493",     # 화면 #565074  제단. 밝은 라일락 다듬돌
    "stair":  "5e7b7b",     # 화면 #37475c  계단. 유일하게 안 따뜻한 돌(출구는 차다)
    # ★14차. iron 이 검은 쇠에서 **황동**이 됐다. 컨셉의 횃불 받침·화로·금테는
    #   전부 금색이고, 이 파일에서 buf_iron 이 그리는 것이 바로 그 물건들이다.
    "iron":   "937d39",     # 화면 #6b4a1e  황동 받침·화로·난간
    "banner": "745a74",     # 화면 #4a2a52  벽걸이 깃발(자주)
    # ★메달리온은 **제 텍스처 색상 그대로** 두어야 한다. mat_decal 은 hue_keep 이
    #   없어 채널별로 목표에 끌어당기는데, cut(보라 회색)을 주면 청록이 지워진다
    #   (1차 굽기 곱수 0.842/0.475/0.634 = 초록을 절반 깎았다). 텍스처 선형평균
    #   (0.223,0.375,0.407)에 0.70 을 곱한 값이라 곱수가 거의 스칼라로 앉는다.
    "medal":  "678c97",     # 화면 #7391a1  제단 청록 팔각
    "flame":  "ffd27a",     # 이미시브. 조명도 정점색도 안 탄다
}

# ★타일의 **색기를 얼마나 살릴 것인가**(0 = 목표색으로 완전히 끌어당김 / 1 = 타일 그대로).
# ★★14차에서 이 손잡이의 뜻이 뒤집혔다. 13차는 타일이 찬 청록이라 살릴수록 팔레트
#   의도와 싸웠고(0.22~0.40 까지 내렸다), 이번 타일은 **컨셉 그 자체**다 — 크림 판석과
#   보라 줄눈, 보라·코발트·청록 블록이 텍스처 안에 이미 칠해져 있다. 여기서 hue_keep 을
#   내리면 그 색을 도로 지우게 된다. 그래서 0.55 -> 0.88 로 크게 올렸다.
#   목표색(PAL)이 하는 일은 이제 색상이 아니라 **밝기 배분**이다.
HUE_KEEP = 0.88


def srgb_to_linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    return (srgb_to_linear(int(h[0:2], 16) / 255.0),
            srgb_to_linear(int(h[2:4], 16) / 255.0),
            srgb_to_linear(int(h[4:6], 16) / 255.0), 1.0)


def _lum3(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


MATS = {}
MAT_LOG = []      # (이름, 목표hex, 곱수, 정점색평균) - 아래 [곱수] 줄이 다시 잰다


def _new_mat(name, backface=False, blend=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    m.use_backface_culling = backface
    if blend:
        # ★익스포터가 alphaMode=BLEND 를 적는 조건이다. 이걸 안 걸면 데칼이
        #   불투명 검은 판이 되어 바닥에 구멍이 뚫린 것처럼 보인다.
        try:
            m.blend_method = "BLEND"
        except Exception:
            pass
        try:
            m.surface_render_method = "BLENDED"     # 4.2+
        except Exception:
            pass
    return m, nt, bsdf


def mat_solid(name, hexcol, rough=0.92, backface=False, emit=0.0, shade=(1., 1., 1.)):
    """타일 없는 단색. 곱수 계약은 같다(정점색 평균으로 나눈다)."""
    if name in MATS:
        return MATS[name]
    tgt = hex_lin(hexcol)
    k = [min(1.0, tgt[i] / max(1e-6, float(shade[i]))) for i in range(3)]
    m, nt, bsdf = _new_mat(name, backface)
    bsdf.inputs["Base Color"].default_value = (k[0], k[1], k[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.0
    if emit > 0.0:
        # ★이미시브는 조명을 안 탄다. 던전에서 불꽃만 스스로 빛나야 하므로
        #   여기에만 쓴다. 익스포터가 KHR_materials_emissive_strength 로 내보내고
        #   three.js GLTFLoader 가 emissive + emissiveIntensity 로 받는다.
        bsdf.inputs["Emission Color"].default_value = hex_lin(hexcol)
        bsdf.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    MAT_LOG.append((name, hexcol, tuple(k), tuple(float(s) for s in shade), (1., 1., 1.)))
    return m


def mat_tex(name, hexcol, img, tile_lin, rough=1.0, backface=False, shade=(1., 1., 1.),
            hue_keep=HUE_KEEP):
    """타일 x 목표색.

    ★glTF 함정: Principled 에 이미지만 물리면 baseColorFactor 가 1 이라 색을 못 준다.
      Image Texture -> Mix(MULTIPLY) <- 상수색 -> Base Color 로 짜면 익스포터가
      baseColorTexture + baseColorFactor 로 정확히 쪼개서 내보낸다.
    ★곱수는 두 계산을 섞는다.
        채널별 = 목표색 / 타일평균 / 정점색평균   -> 평균색이 정확히 목표가 된다
        스칼라 = 목표휘도 / 타일휘도 / 정점휘도   -> **타일의 색기가 그대로 산다**
      hue_keep 만큼 스칼라 쪽으로 간다. 컨셉 타일을 쓰는 이유가 그 색기라서
      절반 넘게 살리고, 나머지 절반으로 팔레트 의도(바닥은 따뜻 / 벽은 차게)를 준다."""
    if name in MATS:
        return MATS[name]
    tgt = hex_lin(hexcol)
    den = [max(1e-6, float(tile_lin[i]) * float(shade[i])) for i in range(3)]
    per = [tgt[i] / den[i] for i in range(3)]
    sca = _lum3(tgt) / max(1e-6, _lum3(den))
    raw = [per[i] * (1.0 - hue_keep) + sca * hue_keep for i in range(3)]
    k = [min(1.0, x) for x in raw]
    if max(raw) > 1.0:
        print("[경고] %s 곱수가 1 을 넘는다(%.3f). 타일을 더 밝게 굽거나 목표색을 낮춰라"
              % (name, max(raw)))
    m, nt, bsdf = _new_mat(name, backface)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "REPEAT"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs[6])        # A = 타일
    mix.inputs[7].default_value = (k[0], k[1], k[2], 1.0)    # B = 곱수(선형)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    MATS[name] = m
    MAT_LOG.append((name, hexcol, tuple(k), tuple(float(s) for s in shade),
                    tuple(float(t) for t in tile_lin)))
    return m


def mat_glow(name, img, strength, tint=(1.0, 1.0, 1.0), backface=False):
    """**빛 그 자체**를 그리는 재질. 웜 풀 · 달빛 웅덩이 · 샤프트 · 불꽃.

    ★이게 이 판의 새 장치다. 베이스컬러를 검게 두고 이미시브만 켠다 =
      조명도 정점색도 안 탄다. 알파는 텍스처가 정한다(BLEND).
    ★세기를 3 넘게 주면 ACES 가 흰색으로 말아 올려서 **색이 사라진다**
      (LOG.md 의 그 함정. 휘도의 79%를 G·B 가 지므로 주황이 특히 잘 씻긴다).
      불꽃 심지만 그 위로 보내고 웅덩이는 1.6 아래에 둔다."""
    if name in MATS:
        return MATS[name]
    m, nt, bsdf = _new_mat(name, backface, blend=True)
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "CLIP"          # 데칼이라 되풀이하면 안 된다
    if abs(tint[0] - 1) + abs(tint[1] - 1) + abs(tint[2] - 1) > 1e-4:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(tex.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (tint[0], tint[1], tint[2], 1.0)
        nt.links.new(mix.outputs[2], bsdf.inputs["Emission Color"])
    else:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = strength
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    MATS[name] = m
    return m


def mat_decal(name, hexcol, img, tile_lin, shade=(1., 1., 1.), emit=0.0):
    """알파가 있는 **바닥 데칼**(제단 메달리온). 색은 조명을 타고 룬만 스스로 빛난다."""
    if name in MATS:
        return MATS[name]
    tgt = hex_lin(hexcol)
    den = [max(1e-6, float(tile_lin[i]) * float(shade[i])) for i in range(3)]
    k = [min(1.0, tgt[i] / den[i]) for i in range(3)]
    m, nt, bsdf = _new_mat(name, False, blend=True)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "CLIP"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (k[0], k[1], k[2], 1.0)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    if emit > 0.0:
        # ★같은 이미지를 이미시브로도 물린다. **밝은 룬만** 임계 위라 저 혼자 빛나고
        #   어두운 돌은 그대로다 - 마스크를 따로 안 굽고 파란 룬을 살리는 길이다.
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    MAT_LOG.append((name, hexcol, tuple(k), tuple(float(s) for s in shade),
                    tuple(float(t) for t in tile_lin)))
    return m


# ═════════════════════════════════════════════════════════════
# 7) 지오메트리 버퍼
# ═════════════════════════════════════════════════════════════
class Buf:
    """정점/면을 파이썬 리스트로 모아 두었다가 한 번에 메시로 만든다.

    ★c[] 는 정점당 **명암 곱수 RGB** 다(초원 맵은 회색 하나였다. 던전은 횃불 색이
      정보라서 세 채널을 다 쓴다). glTF COLOR_0 으로 나가 three.js 가 베이스컬러에
      곱한다. 이게 던전의 어둠·웜 라이트를 재질 하나로 내는 장치다."""

    def __init__(self, name, tile=None, uv_scale=None, glow=False, uv_rot=0.0):
        self.name = name
        self.mat = None
        self.tile = tile              # 참이면 UV 를 만든다
        self.uv_scale = uv_scale      # None 이면 **면마다 0..1** (데칼·스프라이트)
        self.uv_rot = uv_rot          # 바닥 격자축을 벽과 어긋나게 돌린다(13차C)
        self.glow = glow              # 이미시브라 정점색을 안 쓴다
        self.v = []
        self.f = []
        self.c = []
        self.uv = []                  # uv_scale 이 None 인 버퍼만 채운다
        self.shade = (1.0, 1.0, 1.0)

    def tri_count(self):
        return sum(len(f) - 2 for f in self.f)


def face_normal(pts):
    """게임 좌표 다각형의 **바깥 법선**(gx, y, gz 성분).

    ★블렌더 공간에서 뉴웰로 구한 뒤 게임 좌표로 되돌린다. 감김이 곧 법선이고
      이 파일의 상자·프리즘은 이미 바깥으로 감겨 있다(안 그러면 게임 조명도 뒤집힌다)."""
    nx = ny = nz = 0.0
    n = len(pts)
    for i in range(n):
        ax, ay, az = bpos(*pts[i])
        bx, by, bz = bpos(*pts[(i + 1) % n])
        nx += (ay - by) * (az + bz)
        ny += (az - bz) * (ax + bx)
        nz += (ax - bx) * (ay + by)
    L = math.sqrt(nx * nx + ny * ny + nz * nz)
    if L < 1e-9:
        return None
    # blender (x, y, z) -> game (gx, y, gz) = (x, z, -y)
    return (nx / L, nz / L, -ny / L)


def add_quad(buf, p0, p1, p2, p3, boost=0.0, moss=0.0, nrm=None):
    """게임 좌표 네 점(시계 반대)으로 사각면 하나. 정점색은 그 자리에서 굽는다."""
    b = len(buf.v)
    if nrm is None:
        nrm = face_normal((p0, p1, p2, p3))
    for (gx, gz, y) in (p0, p1, p2, p3):
        buf.v.append(bpos(gx, gz, y))
        col = lum(gx, gz, y, moss, nrm)
        if boost:
            col = np.clip(col + boost, 0.0, 1.0)
        buf.c.append((float(col[0]), float(col[1]), float(col[2])))
    buf.f.append((b, b + 1, b + 2, b + 3))


# ★★glTF UV 함정 (LOG.md 에 이미 적혀 있는 것):
#   블렌더 UV 는 **아래가 v=0** 이고 glTF/three 는 **위가 v=0** 이다. 익스포터가
#   v_gltf = 1 - v_blender 로 뒤집는다. 그래서 여기 적는 값은 전부 "뒤집히기 전"
#   = 블렌더 좌표다. 세로 스프라이트는 밑변이 (0,0)·(1,0) 이어야 불꽃이 바로 선다.
UV_CARD_V = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]   # 밑좌·밑우·윗우·윗좌
UV_CARD_G = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]   # 바닥용(아래 winding 순)


def add_card(buf, p0, p1, p2, p3, uvs=None):
    """UV 0..1 이 통째로 박히는 사각면(데칼 · 스프라이트)."""
    b = len(buf.v)
    uvs = uvs or UV_CARD_V
    for i, (gx, gz, y) in enumerate((p0, p1, p2, p3)):
        buf.v.append(bpos(gx, gz, y))
        buf.uv.append(uvs[i])
        if not buf.glow:
            col = lum(gx, gz, y, 0.0, (0.0, 1.0, 0.0))
            buf.c.append((float(col[0]), float(col[1]), float(col[2])))
    buf.f.append((b, b + 1, b + 2, b + 3))


def add_ground_card(buf, gx, gz, y, hx, hz, rot=0.0):
    """바닥에 눕히는 데칼 한 장(웜 풀 · 달빛 웅덩이 · 메달리온).

    ★winding 은 바닥 격자와 **같은 순서**여야 윗면이 위를 본다:
      (-x,-z) -> (-x,+z) -> (+x,+z) -> (+x,-z)."""
    cs, sn = math.cos(rot), math.sin(rot)

    def P(dx, dz):
        return (gx + dx * cs - dz * sn, gz + dx * sn + dz * cs, y)
    add_card(buf, P(-hx, -hz), P(-hx, hz), P(hx, hz), P(hx, -hz), UV_CARD_G)


def add_box(buf, gx, gz, y0, y1, hx, hz, rot=0.0, seg=None, top_boost=0.0,
            skip_bottom=True):
    """축정렬(또는 rot 만큼 돌린) 상자. seg 를 주면 옆면을 그만큼 잘라 정점색 그라데이션을 싣는다."""
    cs, sn = math.cos(rot), math.sin(rot)

    def P(dx, dz, y):
        return (gx + dx * cs - dz * sn, gz + dx * sn + dz * cs, y)

    corners = [(-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)]
    if seg is None:
        nx = nz = 1
        ny = 1
    else:
        nx = max(1, int(math.ceil(hx * 2 / seg)))
        nz = max(1, int(math.ceil(hz * 2 / seg)))
        ny = max(1, int(math.ceil((y1 - y0) / seg)))
    # 옆면 넷
    for i in range(4):
        (ax, az) = corners[i]
        (bx2, bz2) = corners[(i + 1) % 4]
        n = nx if abs(bx2 - ax) > abs(bz2 - az) else nz
        for s in range(n):
            t0, t1 = s / n, (s + 1) / n
            x0, z0 = ax + (bx2 - ax) * t0, az + (bz2 - az) * t0
            x1, z1 = ax + (bx2 - ax) * t1, az + (bz2 - az) * t1
            for j in range(ny):
                yy0 = y0 + (y1 - y0) * j / ny
                yy1 = y0 + (y1 - y0) * (j + 1) / ny
                add_quad(buf, P(x0, z0, yy0), P(x1, z1, yy0),
                         P(x1, z1, yy1), P(x0, z0, yy1))
    # 윗면
    for i in range(nx):
        for j in range(nz):
            x0 = -hx + 2 * hx * i / nx
            x1 = -hx + 2 * hx * (i + 1) / nx
            z0 = -hz + 2 * hz * j / nz
            z1 = -hz + 2 * hz * (j + 1) / nz
            add_quad(buf, P(x0, z0, y1), P(x0, z1, y1), P(x1, z1, y1), P(x1, z0, y1),
                     boost=top_boost)
    if not skip_bottom:
        for i in range(nx):
            for j in range(nz):
                x0 = -hx + 2 * hx * i / nx
                x1 = -hx + 2 * hx * (i + 1) / nx
                z0 = -hz + 2 * hz * j / nz
                z1 = -hz + 2 * hz * (j + 1) / nz
                add_quad(buf, P(x0, z0, y0), P(x1, z0, y0), P(x1, z1, y0), P(x0, z1, y0))


def add_prism(buf, gx, gz, y0, y1, r0, r1, n=8, phase=0.0, top_boost=0.0, cap=True):
    """n각 원뿔대. 기둥·화로·불꽃에 쓴다."""
    ring0, ring1 = [], []
    for i in range(n):
        a = phase + i * 2 * math.pi / n
        ring0.append((gx + math.cos(a) * r0, gz + math.sin(a) * r0, y0))
        ring1.append((gx + math.cos(a) * r1, gz + math.sin(a) * r1, y1))
    for i in range(n):
        j = (i + 1) % n
        add_quad(buf, ring0[i], ring0[j], ring1[j], ring1[i])
    if cap and r1 > 1e-4:
        b = len(buf.v)
        buf.v.append(bpos(gx, gz, y1))
        col = np.clip(lum(gx, gz, y1, 0.0, (0.0, 1.0, 0.0)) + top_boost, 0.0, 1.0)
        buf.c.append((float(col[0]), float(col[1]), float(col[2])))
        for (px, pz, py) in ring1:
            buf.v.append(bpos(px, pz, py))
            cc = np.clip(lum(px, pz, py, 0.0, (0.0, 1.0, 0.0)) + top_boost, 0.0, 1.0)
            buf.c.append((float(cc[0]), float(cc[1]), float(cc[2])))
        for i in range(n):
            j = (i + 1) % n
            buf.f.append((b, b + 1 + i, b + 1 + j))


# ── 버퍼 ──
# ★★메시 이름 규칙이 하나 늘었다: **FLOOR 로 시작하면 그림자를 안 던진다.**
#   web/level.js 314행이 `name.startsWith('FLOOR')` 로 castShadow 를 끈다. 1차는
#   바닥을 DGFLOOR 로 지어서(=FLOOR 아님) **바닥이 자기 자신에게 그림자를 던지고
#   있었다**. 이번엔 바닥·빛 데칼·샤프트·불꽃을 전부 FLOOR_ 로 짓는다 —
#   빛나는 판이 그림자를 던지면 그 자리만 시커멓게 죽는다.
#   ★초원용 스플랫이 얹힐 걱정은 없다: level2.json 의 `floorLook:false` 가
#     applyFloorLook 을 통째로 건너뛴다(level.js 322행).
buf_floor = Buf("FLOOR_DG", tile=True, uv_scale=FLOOR_UV_SCALE, uv_rot=FLOOR_UV_ROT)
# ★통로는 **다른 각으로** 돌린다. 방과 통로가 같은 각이면 두 메시의 격자가 이어져
#   한 판으로 읽히고, 그러면 UV 를 돌린 뜻이 절반 날아간다.
buf_floorb = Buf("FLOOR_DGB", tile=True, uv_scale=FLOOR_UV_SCALE,
                 uv_rot=-FLOOR_UV_ROT * 1.6)                        # 금 간 바닥(통로)
buf_dirt = Buf("FLOOR_DIRT", tile=True, uv_scale=FLOOR_UV_SCALE, uv_rot=FLOOR_UV_ROT)
buf_wall = Buf("COL_WALL", tile=True, uv_scale=WALL_UV_SCALE)
buf_cut = Buf("COL_CUT", tile=True, uv_scale=WALL_UV_SCALE)        # 기둥·아치·문설주
buf_altar = Buf("COL_ALTAR", tile=True, uv_scale=WALL_UV_SCALE)
buf_stair = Buf("DECO_STAIR", tile=True, uv_scale=WALL_UV_SCALE)
buf_iron = Buf("DECO_IRON")
buf_banner = Buf("DECO_BANNER")
buf_rubble = Buf("COL_RUBBLE", tile=True, uv_scale=WALL_UV_SCALE)
# ── 빛을 그리는 버퍼(이미시브 · 알파. 정점색을 안 쓴다) ──
buf_pool = Buf("FLOOR_POOL", tile=True, glow=True)        # 횃불 웜 풀
buf_poolc = Buf("FLOOR_POOLC", tile=True, glow=True)      # 달빛·계단의 찬 웅덩이
buf_shaft = Buf("FLOOR_SHAFT", tile=True, glow=True)      # 달빛 샤프트 콘
buf_flame = Buf("FLOOR_FLAME", tile=True, glow=True)      # 불꽃 스프라이트
buf_dust = Buf("FLOOR_DUST", tile=True, glow=True)        # 샤프트 속 먼지
buf_medal = Buf("FLOOR_MEDAL", tile=True, glow=False)     # 제단 메달리온(조명을 탄다)
# ── 13차C 신설 ──
buf_wglow = Buf("FLOOR_WGLOW", tile=True, glow=True)      # 횃불이 벽을 타고 오르는 자국
buf_halo = Buf("FLOOR_HALO", tile=True, glow=True)        # 불꽃 뒤 부드러운 후광
buf_wear = Buf("FLOOR_WEAR", tile=True, glow=False)       # 바닥 마모·이끼(조명을 탄다)


# ═════════════════════════════════════════════════════════════
# 8) 콜라이더 · 낮은 단
# ═════════════════════════════════════════════════════════════
COLLIDERS = []
PLATFORMS = []


def push_col_box(gx, gz, hx, hz, h, tag):
    COLLIDERS.append({"type": "box", "x": round(gx, 3), "z": round(gz, 3),
                      "hx": round(hx, 3), "hz": round(hz, 3),
                      "h": round(h, 2), "tag": tag})


def push_col_circle(gx, gz, r, h, tag):
    COLLIDERS.append({"type": "circle", "x": round(gx, 3), "z": round(gz, 3),
                      "r": round(r, 3), "h": round(h, 2), "tag": tag})


def push_plat_box(gx, gz, hx, hz, top, tag):
    PLATFORMS.append({"type": "box", "x": round(gx, 3), "z": round(gz, 3),
                      "hx": round(hx, 3), "hz": round(hz, 3),
                      "top": round(top, 3), "tag": tag})


def rect_decompose(pred):
    """조건에 맞는 칸을 최대 사각형으로 묶는다. 벽 지오메트리와 콜라이더 수를 줄인다."""
    used = [[False] * GRID for _ in range(GRID)]
    rects = []
    for r in range(GRID):
        for c in range(GRID):
            if used[r][c] or not pred(c, r):
                continue
            c1 = c
            while c1 + 1 < GRID and pred(c1 + 1, r) and not used[r][c1 + 1]:
                c1 += 1
            r1 = r
            while r1 + 1 < GRID and all(pred(cc, r1 + 1) and not used[r1 + 1][cc]
                                        for cc in range(c, c1 + 1)):
                r1 += 1
            for rr in range(r, r1 + 1):
                for cc in range(c, c1 + 1):
                    used[rr][cc] = True
            rects.append((c, r, c1, r1))
    return rects


def rect_world(c0, r0, c1, r1):
    gx = (gx_of(c0) + gx_of(c1)) * 0.5
    gz = (gz_of(r0) + gz_of(r1)) * 0.5
    hx = (c1 - c0 + 1) * CELL * 0.5
    hz = (r1 - r0 + 1) * CELL * 0.5
    return gx, gz, hx, hz


# ── 벽 세우기 ──
# 높이 등급마다 따로 묶는다. 같은 등급끼리 묶어야 마루 높이가 이어진다.
WALL_RECTS = []
for _cls in (H_FRONT, H_BACK, H_EDGE):
    for (c0, r0, c1, r1) in rect_decompose(
            lambda c, r, _k=_cls: blocked(c, r) and wall_class(c, r) == _k):
        gx, gz, hx, hz = rect_world(c0, r0, c1, r1)
        h = WALL_H_OF[_cls]
        edge = (_cls == H_EDGE)
        # 남쪽 테두리(맨 아랫줄)만 낮게. 위 상수 주석의 계산이 근거다
        if edge and r0 >= GRID - 1:
            h = WALL_EDGE_S_H
        WALL_RECTS.append((gx, gz, hx, hz, h, _cls))
        # ★옆면을 1.1m 로 자른다. 횃불 웅덩이가 벽면에서 둥글게 읽히려면
        #   정점이 그 정도로는 촘촘해야 한다(2.0m 로 자르면 계단처럼 각진다).
        add_box(buf_wall, gx, gz, FLOOR_Y, h, hx, hz, seg=1.1, top_boost=TOP_BONUS)
        # ★맨 바깥 테두리는 인셋을 **안 준다.** level.js 의 clampBounds 가 마지막에
        #   좌표를 bounds ± 반경으로 끌어당기는데, 그 자리가 벽 콜라이더와 맵 경계 사이의
        #   빈 띠면 플레이어가 벽 속에 놓인다. 테두리는 어차피 걸을 수 있는 칸과
        #   안 붙어 있어서(껍질이 두 칸이다) 통과 폭에 아무 영향이 없다.
        ins = 0.0 if edge else WALL_INSET
        push_col_box(gx, gz, max(0.30, hx - ins), max(0.30, hz - ins), h, "wall")


# ═════════════════════════════════════════════════════════════
# 9) 바닥
# ═════════════════════════════════════════════════════════════
# 걸을 수 있는 칸 + 한 겹 여유만 깐다(벽 밑동이 뜨지 않을 만큼).
# ★정점 격자를 통째로 만들고 면만 골라 붙인다. 이래야 이웃한 칸 사이에 이음매가 없다.
# ★13차B. SUB 3 -> 4 (0.50m 격자). 웜 풀의 감마를 세우면서 정점 간격이 성겨 보였다.
#   바닥 정점이 곧 조명 해상도다 - 여기가 성기면 웅덩이 가장자리가 각진 다각형이 된다.
# ★★13차D. 격자를 **자리에 따라 가른다**. 오너 "어두운 구역 바닥 정점 격자
#   0.5 -> 0.25m 부분 적용(횃불 존·주동선 우선, 예산 실측 후 범위 결정)."
#   전면 적용은 예산이 못 낸다 - 바닥 정점이 8,918 -> 35,672 로 네 배가 되고
#   glb 가 상한(5.000 MiB)을 넘는다(실측: 정점 하나가 인덱스까지 28~34바이트).
#   그래서 **횃불 웅덩이가 앉는 칸만** 곱게 쪼갠다. 웅덩이 가장자리가 정점 격자에
#   걸려 각져 보이던 것도 같이 낫는다(그게 0.25m 가 실제로 보이는 유일한 자리다).
# ★이음매 함정: 고운 칸과 성긴 칸이 만나면 T 자 이음이 생긴다. 바닥이 평면이라
#   기하학적 틈은 없지만, 성긴 쪽이 0.5m 를 직선 보간하는 동안 고운 쪽은 가운데
#   표본을 하나 더 지나므로 **색이 어긋난 실선**이 보일 수 있다. 그래서 경계를
#   빛의 기울기가 완만한 자리(횃불에서 3.2m 밖)에 둔다 - 거기서는 가운데 표본이
#   직선에서 거의 안 벗어난다(실측 최대 0.004, 1/255 아래).
SUB = 4                                   # 기본 = 칸을 4x4 (0.50m 격자)
SUB_FINE = 8                              # 웜 존 = 8x8 (0.25m 격자)
FN = GRID * SUB_FINE                      # 정점 격자는 늘 고운 쪽으로 깐다(공유되게)
# ★실측(이 파일을 FINE_R 만 바꿔 여섯 번 돌린 표). 곱게 쪼갠 칸 하나 = **2.54KB**
#   (정점 +48개 x 40B + 삼각형 +96개 x 6B).
#     FINE_R 0.55 -> 93칸(15%) 4.797MiB    0.70 -> 131칸(22%) 4.893MiB
#           0.80 -> 173칸(29%) 4.998MiB    1.35 -> 260칸(43%) 5.21MiB
#           3.20 -> 사실상 전부            5.97MiB  (= 전면 적용이 못 되는 이유)
#   상한 5.000MiB 를 자로 대면 0.80 이 최대인데 여유가 **2KB** 라 다음 사람이
#   삼각형 하나만 더해도 터진다. 0.70 에서 멈춘다(여유 110KiB).
#   ★이 예산의 절반은 메달리온 텍스처를 512 -> 384 로 줄여서 만들었다
#     (tools/dungeon_tex.py MRES. 289KB = 곱은 칸 114개).
FINE_R = 0.70                              # 이 거리 안에 웜 광원이 있으면 곱게 쪼갠다
_vidx = {}
_floor_needed = [[False] * GRID for _ in range(GRID)]
for r in range(GRID):
    for c in range(GRID):
        if walk[r][c]:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < GRID and 0 <= cc < GRID:
                        _floor_needed[rr][cc] = True


def moss_at(gx, gz):
    """벽에서 얼마나 가까운가 -> 이끼 세기.

    ★컨셉 바닥의 초록은 판 한가운데가 아니라 **벽 밑동과 판 사이 줄눈**에 낀다.
      그래서 벽까지의 거리로만 만든다. 거리 1.15m 밖은 0.
    ★13차C. 타일 텍스처에서 초록 줄눈을 69% 걷어냈다(tools/dungeon_tex.py).
      바닥 전체에 깔려 있던 그 초록이 이제 **여기에만** 남는다 = 컨셉과 같은 배치다.
      그래서 세기를 0.62 -> 0.78 로 올렸다(총량은 오히려 크게 줄었다).
    ★가장자리를 잡음으로 흔든다. 벽과 나란한 띠로 깔리면 그것 자체가 또 격자다."""
    t = max(0.0, 1.0 - wall_dist(gx, gz) / 1.15)
    t *= 0.55 + 0.90 * _vnoise2(gx, gz, 2.60, 47.0)
    return (min(1.0, t) ** 1.5) * 0.78


def contact_ao(gx, gz):
    """벽 발치 접지 어둠(13차C). 1 이 기본, 벽에 붙을수록 어두워진다.

    ★쿼터뷰에서 바닥과 벽이 같은 밝기로 만나면 벽이 바닥 위에 **붕 떠 보인다**
      (컨셉은 벽 밑에 항상 짙은 띠가 있다). 실광원 AO 없이 정점색으로 굽는다."""
    t = max(0.0, 1.0 - wall_dist(gx, gz) / CONTACT_R)
    t = t * t * (3.0 - 2.0 * t)
    return 1.0 - CONTACT_AO * t


def _fv(buf, i, j):
    """바닥 격자 정점(i = x 방향, j = z 방향)을 만들거나 재사용한다."""
    key = (id(buf), i, j)
    got = _vidx.get(key)
    if got is not None:
        return got
    gx = -HALF + i * (CELL / SUB_FINE)
    gz = -HALF + j * (CELL / SUB_FINE)
    idx = len(buf.v)
    buf.v.append(bpos(gx, gz, FLOOR_Y))
    col = lum(gx, gz, FLOOR_Y, moss_at(gx, gz), (0.0, 1.0, 0.0))
    # ★13차C 탈타일화. 격자 주기(4.5m)와 약분 안 되는 3~9m 얼룩 + 벽 밑 접지 어둠.
    #   AMB_MIN 아래로는 안 내린다(구석이 검은 구멍이 되면 캐릭터가 안 뜬다).
    col = np.clip(col * (macro_at(gx, gz) * contact_ao(gx, gz)), AMB_MIN * 0.80, 1.0)
    buf.c.append((float(col[0]), float(col[1]), float(col[2])))
    _vidx[key] = idx
    return idx


# ★통로는 **금 간 바닥**(컨셉 시트 좌하)으로 깐다. 방과 통로가 다른 돌이면
#   "지나가는 곳 / 머무는 곳"이 발밑에서 구별된다. 두 메시가 칸 경계에서 만나므로
#   정점을 공유하지 않지만, 높이가 같아 틈은 없고 무늬만 갈린다.
def _fine_cell(c, r):
    """이 칸을 0.25m 로 쪼갤 것인가 = 웜 광원이 FINE_R 안에 있는가.

    ★찬 빛(달빛·계단)은 안 센다. 그쪽 웅덩이는 이미 부드럽고 넓어서 격자에 안 걸린다
      - 각져 보이는 것은 빨리 죽는 횃불 쪽뿐이다."""
    cx, cz = gx_of(c), gz_of(r)
    for (lx, lz, _ly, _rad, _p, _rgb, near) in LIGHTS:
        if near <= 0.0:
            continue
        # 칸의 어느 구석이든 반경 안에 들면 곱게 (칸 반대각 = CELL*0.707)
        if math.hypot(cx - lx, cz - lz) < FINE_R + CELL * 0.71:
            return True
    return False


_fine_n = 0
_floor_cells = 0
for r in range(GRID):
    for c in range(GRID):
        if not _floor_needed[r][c]:
            continue
        tag = ROOM_OF.get((c, r), "")
        tgt = buf_floorb if tag.startswith("K") else buf_floor
        st = 1 if _fine_cell(c, r) else (SUB_FINE // SUB)
        if st == 1:
            _fine_n += 1
        _floor_cells = _floor_cells + 1
        for sj in range(0, SUB_FINE, st):
            for si in range(0, SUB_FINE, st):
                i0, j0 = c * SUB_FINE + si, r * SUB_FINE + sj
                a = _fv(tgt, i0, j0)
                b = _fv(tgt, i0, j0 + st)
                d = _fv(tgt, i0 + st, j0 + st)
                e = _fv(tgt, i0 + st, j0)
                tgt.f.append((a, b, d, e))
print("[바닥 격자] 0.25m 칸 %d / %d (%.1f%%) · 나머지는 0.50m  (FINE_R %.2f)"
      % (_fine_n, _floor_cells, _fine_n / max(1, _floor_cells) * 100, FINE_R))


# ═════════════════════════════════════════════════════════════
# 10) 문설주 · 인방석 (통로 어귀)
# ═════════════════════════════════════════════════════════════
# 어귀마다 양쪽에 다듬은 돌 기둥을 세우고 위에 인방석을 얹는다.
# ★통로 폭(4.0m)을 **한 톨도 안 좁힌다.** 문설주는 벽 칸 안에 들어앉고,
#   나오는 건 색과 재질뿐이다. 좁히면 nav 여유 계산이 깨진다(설계문서 "문폭").
DOORS = []


JAMB_HALF = 0.20      # 문설주가 어귀로 내미는 길이. 벽 콜라이더 면(INSET 0.22)보다
#                       살짝 안이라 플레이어 몸이 스칠 뿐 관통하지 않는다

# ── 아치 (13차B 신설) ──
# ★치수는 **머리가 안 닿는 조건**에서 나왔다. 통로 반폭 2.0m, 벽 인셋 0.22, 플레이어
#   반경 0.35 라 몸 중심이 갈 수 있는 제일 바깥이 |x| = 1.87m 다. 그 자리에서
#   아치 안쪽 높이가 키(1.75)보다 커야 한다.
#     스프링 1.95 · 크라운 2.95 로 잡으면 원호 반지름 2.50, 중심 y = 0.45
#     |x| 1.87 에서 안쪽 높이 2.11m > 1.75  ✓
#   (반원 아치(스프링 1.55·크라운 3.55)는 이 자리가 1.72m 라 머리가 돌을 뚫는다.)
ARCH_HALF = 2.00      # 어귀 반폭
ARCH_SPRING = 1.95    # 아치가 시작되는 높이
ARCH_RISE = 1.00      # 크라운까지 더 올라가는 높이
ARCH_DEPTH = 0.30     # 아치 판 두께의 절반(어귀 앞뒤로 이만큼씩)
ARCH_SEG = 12
# ★13차D. 겹아치가 안으로 물러나는 거리(m). 어귀 칸이 2.0m 이므로 1.05 면 겹이
#   칸 안에 들어앉는다 = 통로 폭(4.0m) 계약을 한 톨도 안 건드린다.
ARCH_STEP = 1.05


def add_arch(buf, gx, gz, along_x, half, spring, top, depth, broken=False,
             seg=ARCH_SEG, slim=False):
    """어귀 위의 아치 + 그 위 스팬드럴을 한 장의 판으로 세운다.

    ★평평한 인방석과 아치의 차이가 이 판의 인상을 절반쯤 만든다. 컨셉의 홀은
      아치 셋이 겹쳐 보이면서 깊이가 생기는 그림이다.
    ★broken 이면 꼭대기 두 조각을 빼고 그 자리를 들쭉날쭉하게 남긴다(낡은 아치).
    ★13차D. slim = **뒷면 판을 안 만든다**(안쪽 겹아치용). 쿼터뷰에서 어귀 뒷면은
      앞 아치에 늘 가려서 한 픽셀도 안 나오는데 정점은 3분의 1을 먹는다.
      seg 도 줄일 수 있게 뺐다 - 안쪽 아치는 작게 보이므로 9칸이면 각이 안 보인다.
    """
    rise = min(ARCH_RISE, max(0.25, top - spring - 0.35))
    R = (half * half + rise * rise) / (2.0 * rise)
    yc = spring + rise - R
    n = seg
    skip = set()
    if broken:
        skip = {n // 2 - 1, n // 2}          # 크라운 두 조각이 없다

    def arc(t):
        """t 0..1 -> (가로 오프셋, 높이)"""
        x = -half + 2.0 * half * t
        return x, yc + math.sqrt(max(0.0, R * R - x * x))

    for i in range(n):
        if i in skip:
            continue
        x0, y0 = arc(i / n)
        x1, y1 = arc((i + 1) / n)
        # 무너진 아치는 잘린 끝이 비스듬하게 내려앉는다
        t0 = top
        t1 = top
        if broken:
            if i == n // 2 - 2:
                t1 = top - 0.55
            if i == n // 2 + 1:
                t0 = top - 0.55
        if along_x:
            a0, b0 = (gx + x0, gz - depth), (gx + x1, gz - depth)
            a1, b1 = (gx + x0, gz + depth), (gx + x1, gz + depth)
        else:
            a0, b0 = (gx - depth, gz + x0), (gx - depth, gz + x1)
            a1, b1 = (gx + depth, gz + x0), (gx + depth, gz + x1)
        # 앞면 · 뒷면
        add_quad(buf, (a0[0], a0[1], y0), (b0[0], b0[1], y1),
                 (b0[0], b0[1], t1), (a0[0], a0[1], t0))
        if not slim:
            add_quad(buf, (a1[0], a1[1], t0), (b1[0], b1[1], t1),
                     (b1[0], b1[1], y1), (a1[0], a1[1], y0))
        # 아치 안쪽(소핏). 여기가 밝아야 아치가 두께 있는 돌로 읽힌다
        add_quad(buf, (a0[0], a0[1], y0), (a1[0], a1[1], y0),
                 (b1[0], b1[1], y1), (b0[0], b0[1], y1), boost=0.05)


def door_frame(kid):
    """통로의 양 끝 **벽 칸**에 문설주 둘 + 인방석 하나를 세운다.

    ★어귀는 통로의 r0/r1(또는 c0/c1) 자체다. r0-1 은 벌써 방 바닥이라
      거기에 문틀을 세우면 방 한가운데에 돌기둥이 선다(첫 판의 버그).
    ★앞벽(1.45m)에는 안 얹는다. 인방석이 벽 위로 떠 버린다."""
    c0, r0, c1, r1 = CORR_BOX[kid]
    vertical = (r1 - r0) >= (c1 - c0)
    ends = [(c0, c1, r0), (c0, c1, r1)] if vertical else [(r0, r1, c0), (r0, r1, c1)]
    for (a0, a1, b) in ends:
        if vertical:
            cells = [(a0 - 1, b), (a1 + 1, b)]
            span = ((gx_of(a0) + gx_of(a1)) * 0.5, gz_of(b))
            hx, hz = (a1 - a0 + 1) * CELL * 0.5, CELL * 0.5
        else:
            cells = [(b, a0 - 1), (b, a1 + 1)]
            span = (gx_of(b), (gz_of(a0) + gz_of(a1)) * 0.5)
            hx, hz = CELL * 0.5, (a1 - a0 + 1) * CELL * 0.5
        # 어귀가 진짜 벽을 지나는가(양옆이 실제로 막혀 있는가)
        if not all(blocked(cc, rr) for (cc, rr) in cells):
            continue
        top = min(WALL_H_OF[wall_class(*cc)] for cc in cells)
        if top < 2.2:
            continue
        # 문설주 둘. 벽 면 위에 걸터앉아 어귀로 0.20m 내민다
        for (cc, rr) in cells:
            px, pz = gx_of(cc), gz_of(rr)
            if vertical:
                px += (CELL * 0.5) * (1 if cc < a0 else -1)
            else:
                pz += (CELL * 0.5) * (1 if rr < a0 else -1)
            add_box(buf_cut, px, pz, FLOOR_Y, top, JAMB_HALF, JAMB_HALF,
                    seg=1.0, top_boost=TOP_BONUS)
        # ★13차B. 평평한 인방석 -> **아치**. 컨셉의 어귀는 전부 반원 가까운 아치다.
        #   낡아 보이게 셋에 하나는 꼭대기가 무너져 있다.
        _br = (len(DOORS) % 3 == 1)
        add_arch(buf_cut, span[0], span[1], vertical, ARCH_HALF,
                 ARCH_SPRING, top, ARCH_DEPTH, broken=_br)
        # ★★13차D. **겹아치**(archivolt). 오너 "컨셉처럼 겹치며 물러나는 깊이."
        #   컨셉 홀에서 깊이를 만드는 것은 아치가 있다는 사실이 아니라 아치가
        #   **여러 겹으로 물러난다**는 사실이다(우상단 어귀에 세 겹이 보인다).
        #   한 겹짜리 어귀는 벽에 뚫린 구멍이지 '통로'가 아니다.
        #   안쪽으로 ARCH_STEP 만큼 물린 겹을 하나 더 세운다 - 살짝 높게 시작해서
        #   앞 겹의 소핏 위로 띠가 하나 더 보인다.
        #   ★뒷면은 안 만든다(slim). 앞 아치에 완전히 가려서 한 픽셀도 안 나오는데
        #     정점은 3분의 1을 먹는다. seg 도 12 -> 9(안쪽은 작게 보인다).
        # ★어느 쪽이 '안쪽'인가: 어귀 줄(b)에서 통로 몸통을 향하는 쪽이다.
        #   vertical 이면 b 는 행이고 몸통은 r0..r1 사이에 있다.
        _sx, _sz = span
        if vertical:
            _sz += ARCH_STEP * (1.0 if b == r0 else -1.0)
        else:
            _sx += ARCH_STEP * (1.0 if b == c0 else -1.0)
        add_arch(buf_cut, _sx, _sz, vertical, ARCH_HALF - 0.05,
                 ARCH_SPRING + 0.16, top, ARCH_DEPTH * 0.62,
                 broken=(len(DOORS) % 4 == 2), seg=9, slim=True)
        DOORS.append(span)


for _kid in CORR_BOX:
    door_frame(_kid)


# ═════════════════════════════════════════════════════════════
# 11) 방 소품
# ═════════════════════════════════════════════════════════════
# ═════════════════════════════════════════════════════════════
# 11-0) 석조 어휘 (13차B 신설) — 기둥 · 쓰러진 원기둥 · 벽 붙임기둥 · 깃발
# ═════════════════════════════════════════════════════════════
# 컨셉 홀에서 실루엣을 만드는 것은 벽이 아니라 **기둥과 그 잔해**다. 1차는 팔각
# 막대 여덟 개뿐이라 화면이 텅 비었다. 여기서 그 어휘를 만든다.
def add_fluted(buf, gx, gz, y0, y1, r0, r1, n=16, phase=0.0, flute=0.88,
               vseg=6, cap=True, top_boost=0.0, jag=0.0):
    """세로 홈이 팬 원기둥. jag > 0 이면 윗동이 부서져 들쭉날쭉하다.

    ★홈(flute)은 반지름을 한 칸 걸러 줄여서 낸다. 로우폴리에서 홈을 파는 제일 싼 방법이고,
      쿼터뷰에서는 세로 줄무늬 명암으로 읽혀서 기둥이 원통으로 보인다.
    ★vseg 가 정점색 해상도다. 기둥이 3.4m 인데 한 토막으로 만들면 횃불 웅덩이가
      기둥 아래위를 똑같이 비춰서 납작해진다."""
    def ring(y, r, dy=None):
        pts = []
        for i in range(n):
            a = phase + i * 2 * math.pi / n
            rr = r * (flute if i % 2 else 1.0)
            yy = y if dy is None else y + dy[i]
            pts.append((gx + math.cos(a) * rr, gz + math.sin(a) * rr, yy))
        return pts

    dy = None
    if jag > 0.0:
        dy = [-jag * (0.25 + 0.75 * ((i * 0.6180339887 * 7 + 0.31) % 1.0))
              for i in range(n)]
    for k in range(vseg):
        t0, t1 = k / vseg, (k + 1) / vseg
        A = ring(y0 + (y1 - y0) * t0, r0 + (r1 - r0) * t0)
        B = ring(y0 + (y1 - y0) * t1, r0 + (r1 - r0) * t1,
                 dy if k == vseg - 1 else None)
        for i in range(n):
            j = (i + 1) % n
            add_quad(buf, A[i], A[j], B[j], B[i])
    if cap and jag <= 0.0:
        b = len(buf.v)
        buf.v.append(bpos(gx, gz, y1))
        col = np.clip(lum(gx, gz, y1, 0.0, (0.0, 1.0, 0.0)) + top_boost, 0.0, 1.0)
        buf.c.append((float(col[0]), float(col[1]), float(col[2])))
        for (px, pz, py) in ring(y1, r1):
            buf.v.append(bpos(px, pz, py))
            cc = np.clip(lum(px, pz, py, 0.0, (0.0, 1.0, 0.0)) + top_boost, 0.0, 1.0)
            buf.c.append((float(cc[0]), float(cc[1]), float(cc[2])))
        for i in range(n):
            j = (i + 1) % n
            buf.f.append((b, b + 1 + i, b + 1 + j))


def add_column(buf, gx, gz, h, r=0.46, broken=0.0, phase=0.0):
    """주춧돌 + 몰딩 + 홈 판 몸통 + 주두. broken 이면 그 비율에서 부러진다."""
    y = FLOOR_Y
    add_box(buf, gx, gz, y, y + 0.22, r * 1.62, r * 1.62, seg=0.9,
            top_boost=TOP_BONUS)
    add_fluted(buf, gx, gz, y + 0.22, y + 0.40, r * 1.34, r * 1.14, n=16,
               phase=phase, flute=1.0, vseg=1, cap=False)
    if broken > 0.0:
        top = y + 0.40 + (h - 0.40) * broken
        add_fluted(buf, gx, gz, y + 0.40, top, r * 1.10, r * 1.02, n=16,
                   phase=phase, vseg=max(2, int((top - y) * 2)), jag=0.30)
        return top
    top = y + h
    add_fluted(buf, gx, gz, y + 0.40, top - 0.34, r * 1.10, r * 0.94, n=16,
               phase=phase, vseg=6, cap=False)
    # 주두. 위로 벌어져야 기둥이 무엇을 받치고 있는 것처럼 보인다
    add_fluted(buf, gx, gz, top - 0.34, top - 0.14, r * 0.98, r * 1.26, n=16,
               phase=phase, flute=1.0, vseg=1, cap=False)
    add_box(buf, gx, gz, top - 0.14, top, r * 1.42, r * 1.42, seg=0.9,
            top_boost=TOP_BONUS)
    return top


def add_fallen_column(buf, gx, gz, yaw, length, r, n=14, bands=(0.24, 0.62),
                      lseg=10):
    """**가로로 쓰러진 원기둥.** 컨셉 홀 전경의 그 물건이다.

    ★쿼터뷰에서 바닥에 놓인 긴 원통은 화면을 대각으로 가르는 유일한 선이라
      공간에 방향을 준다(1차에 이게 없어서 화면이 평평했다).
    ★띠(bands)를 감으면 '깨진 기둥'이지 '통나무'가 아니게 된다."""
    dx, dz = math.cos(yaw), math.sin(yaw)
    sx, sz = -math.sin(yaw), math.cos(yaw)
    cy = FLOOR_Y + r * 0.78            # 조금 파묻힌다(바닥에 얹힌 게 아니라 박혔다)

    def ring(t, rad):
        px, pz = gx + dx * t, gz + dz * t
        pts = []
        for i in range(n):
            a = i * 2 * math.pi / n
            pts.append((px + sx * math.cos(a) * rad,
                        pz + sz * math.cos(a) * rad,
                        cy + math.sin(a) * rad))
        return pts

    def rad_at(u):
        rr = r
        for b in bands:
            if abs(u - b) < 0.045:
                rr = r * 1.16
        if u < 0.03 or u > 0.97:
            rr = r * 1.10
        return rr

    for k in range(lseg):
        u0, u1 = k / lseg, (k + 1) / lseg
        t0 = -length * 0.5 + length * u0
        t1 = -length * 0.5 + length * u1
        A, B = ring(t0, rad_at(u0)), ring(t1, rad_at(u1))
        for i in range(n):
            j = (i + 1) % n
            add_quad(buf, A[i], A[j], B[j], B[i])
    # 끝 마감 두 장(부러진 단면)
    for (t, rad) in ((-length * 0.5, rad_at(0.0)), (length * 0.5, rad_at(1.0))):
        pts = ring(t, rad)
        b = len(buf.v)
        cx, cz = gx + dx * t, gz + dz * t
        buf.v.append(bpos(cx, cz, cy))
        col = lum(cx, cz, cy)
        buf.c.append((float(col[0]), float(col[1]), float(col[2])))
        for (px, pz, py) in pts:
            buf.v.append(bpos(px, pz, py))
            cc = lum(px, pz, py)
            buf.c.append((float(cc[0]), float(cc[1]), float(cc[2])))
        for i in range(n):
            j = (i + 1) % n
            buf.f.append((b, b + 1 + i, b + 1 + j))
    push_col_box(gx, gz, max(abs(dx) * length * 0.5, r * 0.9),
                 max(abs(dz) * length * 0.5, r * 0.9), r * 1.9, "column")


def add_pilaster(buf, gx, gz, face, h):
    """벽에 붙은 반쯤 나온 기둥. 긴 벽이 한 장의 판으로 안 읽히게 한다."""
    fx, fz = FACE_DIR[face]
    px, pz = gx + fx * (CELL * 0.5 - 0.16), gz + fz * (CELL * 0.5 - 0.16)
    add_fluted(buf, px, pz, FLOOR_Y, h - 0.22, 0.34, 0.30, n=12, vseg=5,
               cap=False)
    add_box(buf, px, pz, h - 0.22, h, 0.42, 0.42, seg=0.9, top_boost=TOP_BONUS)


def add_banner(buf, gx, gz, face, top, w=0.72, drop=1.75):
    """벽걸이 깃발. 컨셉 홀 왼쪽 벽에 걸린 그것.

    ★밑단을 살짝 좁히고 끝을 뾰족하게 자른다. 직사각형은 '천'이 아니라 '판'이다."""
    fx, fz = FACE_DIR[face]
    ox, oz = gx + fx * (CELL * 0.5 + 0.03), gz + fz * (CELL * 0.5 + 0.03)
    sx, sz = -fz, fx
    y0, y1 = top - drop, top

    def P(u, y):
        return (ox + sx * u, oz + sz * u, y)
    add_quad(buf, P(-w * 0.5, y0 + 0.30), P(w * 0.5, y0 + 0.30),
             P(w * 0.5, y1), P(-w * 0.5, y1))
    # 아래 끝 삼각(제비꼬리). ★사각면에 같은 점을 두 번 적으면 validate 가 지운다
    b = len(buf.v)
    for (px, pz, py) in (P(-w * 0.5, y0 + 0.30), P(0.0, y0), P(w * 0.5, y0 + 0.30)):
        buf.v.append(bpos(px, pz, py))
        cc = lum(px, pz, py)
        buf.c.append((float(cc[0]), float(cc[1]), float(cc[2])))
    buf.f.append((b, b + 1, b + 2))
    # 걸이 봉
    add_box(buf_iron, ox, oz, y1, y1 + 0.08, 0.05 if abs(fx) > 0.5 else w * 0.62,
            w * 0.62 if abs(fx) > 0.5 else 0.05)


# ── 빛을 물건으로 그리는 것들 ──
# ★★컨셉과 1차의 결정적 차이가 여기 있다. 컨셉의 횃불은 **세 장**으로 그려져 있다:
#   불꽃 + 바닥에 번진 주황 웅덩이 + 벽에 번진 자국. 달빛도 세 장이다:
#   콘 + 바닥 타원 + 먼지. 1차는 불꽃 삼각형 하나뿐이었고 그래서 빛이 정보가 아니었다.
# ★14차. 0.40x0.62 -> 0.54x0.88. 컨셉의 불꽃은 받침보다 크고 화면에서 제일 먼저
#   보이는 물건이다. 씬이 여섯 배 밝아졌으므로 옛 크기로는 금색 점으로 읽힌다.
FLAME_W, FLAME_H = 0.54, 0.88
POOL_Y = FLOOR_Y + 0.014          # 바닥 데칼 띄우는 높이(z-fighting 방지)
POOL_Y2 = FLOOR_Y + 0.020         # 두 겹째(달빛). 같은 높이면 서로 깜빡인다
# ★13차C. 마모 데칼은 **빛보다 아래**다 - 돌의 일부이지 빛이 아니므로 웜 풀이
#   그 위에 얹혀야 한다. 메달리온(0.006)보다는 위, 웜 풀(0.014)보다는 아래.
WEAR_Y = FLOOR_Y + 0.009


def add_flame(gx, gz, y, w=FLAME_W, h=FLAME_H, seed=0.0):
    """불꽃 스프라이트. 십자로 두 장 세운다(카메라가 고정이라 이걸로 충분하다)."""
    for a in (0.0, math.pi * 0.5):
        a += seed
        sx, sz = math.cos(a) * w * 0.5, math.sin(a) * w * 0.5
        add_card(buf_flame, (gx - sx, gz - sz, y), (gx + sx, gz + sz, y),
                 (gx + sx, gz + sz, y + h), (gx - sx, gz - sz, y + h))


def add_pool(gx, gz, rad, cold=False, rot=0.0, squash=1.0, y=None):
    """바닥에 번진 빛 웅덩이 한 장."""
    buf = buf_poolc if cold else buf_pool
    yy = (POOL_Y2 if cold else POOL_Y) if y is None else y
    add_ground_card(buf, gx, gz, yy, rad, rad * squash, rot)


def add_wall_glow(gx, gz, dx, dz, y, w=1.70, h=2.05, back=0.0):
    """벽에 번진 횃불 자국. **13차C 에서 되살렸다.**

    ★한 번 폐기했던 장치다("정점색 N·L 이 이미 벽을 데우니 이중 계산"). 그 판단은
      절반만 맞았다 — 벽은 데워지고 **있었지만**(실측 R/B 0.6m 1.66) 벽 상자가
      seg 1.1m 로 잘려 있어서 그 열이 정점 격자에 뭉개졌다. 뜨거운 심(반경 0.45m)이
      1m 격자에 안 잡히면 남는 것은 **넓고 밋밋한 얼룩**뿐이고, 그게 오너가 본
      "이상한 주변광"의 벽쪽 절반이다.
      벽을 0.6m 로 다시 자르는 길은 삼각형이 세 배가 되어 glb 예산(5MB)을 넘긴다.
      그래서 **역할을 나눈다**: 넓은 스필은 정점색이, 뜨거운 심은 이 카드가 낸다.
    ★가산 합성이다(web/level.js 가 AdditiveBlending 으로 갈아 준다). 알파 블렌딩으로
      두면 벽돌을 지우는 물감이 되어 폐기했던 그 그림이 그대로 돌아온다.
    back = 불꽃이 벽에서 떨어져 있는 거리(받침대형 0.62m). 멀수록 넓고 옅다.
    """
    sx, sz = -dz, dx
    # ★★함정. 횃불 자리(gx, gz)는 칸 중심에서 0.88m 다 = **벽면(1.0m)보다 0.12m 안쪽**
    #   이다(mount_torch 가 CELL*0.5 - 0.12 로 잡는다). 그대로 카드를 놓으면 벽 속에
    #   파묻혀 화면에 한 픽셀도 안 나온다(첫 판이 정확히 그랬다 - 컷에 벽 자국이
    #   아예 없었다). 벽면 밖으로 0.12 + 0.05 를 밀어야 보인다.
    ox, oz = gx + dx * 0.17, gz + dz * 0.17
    k = 1.0 + back * 0.55                        # 멀면 넓게 번진다
    w, h = w * k, h * k
    # ★불꽃 자리는 카드의 아래쪽 1/3 이다(dg_wglow 가 그렇게 구워져 있다).
    #   카드 중심을 불꽃보다 위로 올려야 그림과 자리가 맞는다.
    cy = y + h * 0.17
    add_card(buf_wglow,
             (ox - sx * w * 0.5, oz - sz * w * 0.5, cy - h * 0.5),
             (ox + sx * w * 0.5, oz + sz * w * 0.5, cy - h * 0.5),
             (ox + sx * w * 0.5, oz + sz * w * 0.5, cy + h * 0.5),
             (ox - sx * w * 0.5, oz - sz * w * 0.5, cy + h * 0.5))


def add_halo(gx, gz, y, r=0.62):
    """불꽃 뒤에 세우는 부드러운 후광 한 장(13차C 신설).

    ★불꽃 스프라이트는 알파 가장자리가 또렷해서 어둠 위에 **오려 붙인 그림**으로
      떠 있었다. 실제 불은 언제나 제 둘레의 공기를 밝힌다 - 그 한 겹이 있어야
      불꽃이 배경에 앉는다.
    ★작고(반경 0.62m) 옅어야 한다. 세기를 올리면 블룸 임계(1.02)를 넘어서 불꽃과
      후광이 같이 번져 흰 공이 된다. 번지는 것은 **불꽃만**이 계약이다.
    ★불꽃과 같은 십자 두 장이 아니라 한 장이다. 두 장이면 겹치는 자리가 두 배로
      밝아져 심에 십자 자국이 생긴다."""
    for a in (math.pi * 0.25,):   # 한 장. 십자로 두 장이면 심에 십자 자국이 생긴다
        sx, sz = math.cos(a) * r, math.sin(a) * r
        add_card(buf_halo, (gx - sx, gz - sz, y - r * 0.62),
                 (gx + sx, gz + sz, y - r * 0.62),
                 (gx + sx, gz + sz, y + r * 1.38),
                 (gx - sx, gz - sz, y + r * 1.38))


def add_wear(gx, gz, rad, cell, rot=0.0, squash=1.0):
    """바닥 마모·이끼 데칼 한 장(13차C 신설). cell 0..3 = dg_wear 아틀라스 칸.

    ★격자 리듬을 끊는 **비반복** 얼룩이다. 되풀이 주기(6.2m)와 아무 관계 없는
      자리에 놓여야 눈이 주기를 못 센다."""
    cx, cy = (cell % 2) * 0.5, (cell // 2) * 0.5
    # ★블렌더 UV 는 아래가 v=0 이고 익스포터가 뒤집는다. 아틀라스 행을 여기서
    #   맞춰 두지 않으면 위아래 칸이 서로 바뀐다.
    cy = 0.5 - cy
    uv = [(cx, cy + 0.5), (cx, cy), (cx + 0.5, cy), (cx + 0.5, cy + 0.5)]
    cs, sn = math.cos(rot), math.sin(rot)

    def P(dx, dz):
        return (gx + dx * cs - dz * sn, gz + dx * sn + dz * cs, WEAR_Y)
    add_card(buf_wear, P(-rad, -rad * squash), P(-rad, rad * squash),
             P(rad, rad * squash), P(rad, -rad * squash), uv)


# ── 중앙 회랑 기둥 여덟 ──
# 기둥은 얇아서 시야를 다 막지 않으면서 "회랑"이라는 말을 그림으로 만든다.
# 콜라이더 반경 0.55 = 몸이 스치면 밀린다. 두 줄 사이 간격 6.4m 는 전투가 벌어질 폭이다.
# ★13차B. 여덟 중 둘은 **부러져** 있고 그 밑에 잔해가 쌓인다. 성한 것만 여덟이면
#   폐허가 아니라 신전이다.
HALL_C0, HALL_R0, HALL_C1, HALL_R1 = ROOM_BOX["R_HALL"]
PILLARS = []
_BROKEN_PILLAR = {2, 5}
for _i in range(4):
    _rr = HALL_R0 + 1 + _i * 2
    for _k, _dx in enumerate((-3.2, 3.2)):
        px = gxf(HALL_C0 + (HALL_C1 - HALL_C0 + 1) * 0.5) + _dx
        pz = gz_of(_rr)
        PILLARS.append((px, pz))
        _idx = _i * 2 + _k
        _bk = 0.42 if _idx in _BROKEN_PILLAR else 0.0
        _h = add_column(buf_cut, px, pz, 3.55, r=0.46,
                        broken=_bk, phase=math.pi / 16)
        push_col_circle(px, pz, 0.60, _h, "pillar")

# ── 세워 두는 화로 (자리는 4절 FREE_BRAZIERS 에 있다) ──
for (_bx, _bz) in FREE_BRAZIERS:
    add_box(buf_cut, _bx, _bz, FLOOR_Y, FLOOR_Y + 0.16, 0.34, 0.34, seg=0.9,
            top_boost=TOP_BONUS)
    add_fluted(buf_cut, _bx, _bz, FLOOR_Y + 0.16, 1.04, 0.23, 0.17, n=10,
               vseg=3, cap=False)
    add_prism(buf_iron, _bx, _bz, 1.04, 1.28, 0.19, 0.36, n=10)
    add_flame(_bx, _bz, 1.28, w=0.46, h=0.72, seed=RND.uniform(0, 1.0))
    add_halo(_bx, _bz, 1.34, r=0.70)
    add_pool(_bx, _bz, 3.25)
    push_col_circle(_bx, _bz, 0.38, 1.3, "brazier")

# ── 제단 ──
# 낮은 단(올라설 수 있다) + 그 위 제단석 + 화로 둘.
ALT_HX, ALT_HZ = 2.6, 1.9
add_box(buf_altar, ALTAR_X, ALTAR_Z, FLOOR_Y, FLOOR_Y + ALTAR_TOP, ALT_HX, ALT_HZ,
        seg=1.0, top_boost=TOP_BONUS + 0.06)
push_plat_box(ALTAR_X, ALTAR_Z, ALT_HX, ALT_HZ, FLOOR_Y + ALTAR_TOP, "altar")
# 제단석. 증표가 이 위에 뜬다(높이는 web/level2.js 가 groundY + 0.9 로 잡는다)
add_box(buf_altar, ALTAR_X, ALTAR_Z, FLOOR_Y + ALTAR_TOP, FLOOR_Y + ALTAR_TOP + 0.78,
        0.86, 0.60, seg=0.8, top_boost=TOP_BONUS + 0.10)
push_col_box(ALTAR_X, ALTAR_Z, 0.86, 0.60, 1.08, "altar")
# ★제단 바닥의 메달리온 데칼(컨셉 시트 우하). 룬만 스스로 파랗게 빛난다.
#   제단 단 **앞**에 깐다 - 단 위에 깔면 증표에 가려 안 보인다.
MEDAL_R = 3.05
add_ground_card(buf_medal, ALTAR_X, ALTAR_Z + 3.5, FLOOR_Y + 0.010,
                MEDAL_R, MEDAL_R)
# 화로 둘. 광원은 위에서 이미 등록했다
for _dx in (-2.4, 2.4):
    _bx, _bz = ALTAR_X + _dx, ALTAR_Z + 0.2
    add_fluted(buf_cut, _bx, _bz, FLOOR_Y, 0.86, 0.18, 0.14, n=10, vseg=3,
               cap=False)
    add_prism(buf_iron, _bx, _bz, 0.86, 1.10, 0.22, 0.44, n=10)
    add_flame(_bx, _bz, 1.10, w=0.62, h=0.94, seed=RND.uniform(0, 1.0))
    add_halo(_bx, _bz, 1.18, r=0.86)
    push_col_circle(_bx, _bz, 0.46, 1.6, "brazier")

# ── 계단 (탈출구) ──
# 북으로 오르는 다섯 단 + 그 위의 문틀(門).
# ★★기준점은 계단방 **안쪽**이어야 한다. 첫 판은 밑단을 방 북쪽 끝(z=17)에 두는 바람에
#   문틀이 z=13.2, 즉 **벽 속에 파묻혀** 화면에서 통째로 사라졌다(shot_06 증거).
#   두 칸 남으로 물려 문틀까지 방 안(z 14~24)에 들어오게 한다.
STAIR_N = 5
STAIR_HX = 2.0
STAIR_Z0 = gz_of(STAIR_R0 + 2)          # = 19.0
for _i in range(STAIR_N):
    _top = FLOOR_Y + 0.20 * (_i + 1)
    _z = STAIR_Z0 - _i * 0.72
    add_box(buf_stair, STAIR_X, _z, FLOOR_Y, _top, STAIR_HX, 0.36, seg=1.0,
            top_boost=TOP_BONUS + 0.10)
    push_plat_box(STAIR_X, _z, STAIR_HX, 0.36, _top, "stair")
# 문틀(門). 인방석이 굵어서 어디가 출구인지 멀리서도 읽힌다
_dz = STAIR_Z0 - (STAIR_N - 1) * 0.72 - 0.85
for _dx in (-STAIR_HX - 0.32, STAIR_HX + 0.32):
    add_box(buf_cut, STAIR_X + _dx, _dz, FLOOR_Y, 3.10, 0.34, 0.34, seg=1.0,
            top_boost=TOP_BONUS)
add_box(buf_cut, STAIR_X, _dz, 2.42, 3.10, STAIR_HX + 0.66, 0.34, seg=1.1,
        top_boost=TOP_BONUS)
# 문틀 너머의 어둠. 계단이 **어디론가 올라간다**는 말을 그림으로 만든다
# (실제로 뚫린 구멍이 아니라 벽에 붙인 검은 판이다. 콜라이더 없음)
add_box(buf_iron, STAIR_X, _dz - 0.9, FLOOR_Y + 1.02, 3.02, STAIR_HX + 0.10, 0.06)
EXIT_X, EXIT_Z = STAIR_X, STAIR_Z0 - 1.4

# ── 북서 우물 ──
add_prism(buf_cut, WELL_X, WELL_Z, FLOOR_Y, FLOOR_Y + 0.72, 1.28, 1.22, n=10,
          top_boost=TOP_BONUS)
add_prism(buf_iron, WELL_X, WELL_Z, FLOOR_Y + 0.02, FLOOR_Y + 0.06, 1.02, 1.02, n=10)
push_col_circle(WELL_X, WELL_Z, 1.30, 0.72, "well")

# ── 북동 취사장 모닥불 ──
add_prism(buf_rubble, CAMP_X, CAMP_Z, FLOOR_Y, FLOOR_Y + 0.26, 1.05, 0.95, n=9)
for _i in range(5):
    _a = _i * 2 * math.pi / 5 + 0.3
    add_box(buf_iron, CAMP_X + math.cos(_a) * 0.34, CAMP_Z + math.sin(_a) * 0.34,
            FLOOR_Y + 0.18, FLOOR_Y + 0.62, 0.09, 0.30, rot=_a)
add_flame(CAMP_X, CAMP_Z, FLOOR_Y + 0.26, w=0.86, h=1.05, seed=0.7)
add_halo(CAMP_X, CAMP_Z, FLOOR_Y + 0.40, r=1.05)
push_col_circle(CAMP_X, CAMP_Z, 1.05, 1.1, "campfire")

# ── 동쪽 감옥 철창 ──
EAST_C0, EAST_R0, EAST_C1, EAST_R1 = ROOM_BOX["R_EAST"]
for _i in range(9):
    _bx = gx_of(EAST_C1) + 0.55
    _bz = gz_of(EAST_R0) + 0.6 + _i * 0.55
    add_box(buf_iron, _bx, _bz, FLOOR_Y, 2.30, 0.05, 0.05)
add_box(buf_iron, gx_of(EAST_C1) + 0.55, gz_of(EAST_R0) + 2.8,
        2.24, 2.36, 0.06, 2.35)

# ── 쓰러진 원기둥 (13차B 신설) ──
# 컨셉 홀 전경을 가로지르는 그 물건. 자리는 손으로 적는다 - 무리 자리·스폰 정면·
# 통로 어귀를 다 피해야 해서 난수로 뽑으면 매번 다시 검사해야 한다.
# (x, z, yaw, 길이, 반지름)
FALLEN = [
    (2.20, 7.60, 0.28, 5.6, 0.58),      # 중앙 회랑 남쪽. 화면을 대각으로 가른다
    (-17.4, 7.20, 1.25, 4.6, 0.54),     # 서쪽 창고
    (-6.40, -17.0, -0.50, 5.0, 0.56),   # 제단 방. 정예 무리 서쪽
    (17.2, 7.40, 1.10, 4.2, 0.52),      # 동쪽 감옥
]
for (_fx, _fz, _fy, _fl, _fr) in FALLEN:
    add_fallen_column(buf_cut, _fx, _fz, _fy, _fl, _fr)

# ── 부러진 기둥 밑의 잔해 ──
for _i, (px, pz) in enumerate(PILLARS):
    if _i not in _BROKEN_PILLAR:
        continue
    for _k in range(4):
        _a = _k * 1.7 + 0.4
        _rr = RND.uniform(0.62, 1.05)
        add_prism(buf_rubble, px + math.cos(_a) * _rr, pz + math.sin(_a) * _rr,
                  FLOOR_Y, FLOOR_Y + RND.uniform(0.34, 0.72),
                  RND.uniform(0.26, 0.44), RND.uniform(0.14, 0.30),
                  n=RND.choice((5, 6)), phase=RND.uniform(0, 2),
                  top_boost=TOP_BONUS)

# ── 벽 붙임기둥 · 깃발 ──
# 긴 뒷벽이 한 장의 판으로 읽히면 그게 곧 "회색 상자"다. 붙임기둥으로 벽에 리듬을 주고,
# 몇 자리에는 낡은 깃발을 건다(컨셉 홀 왼쪽 벽의 그것).
_torch_cells = set()
for (_gx, _gz, _gy, _dx, _dz, _pd) in TORCH_PROPS:
    _torch_cells.add(cell_of(_gx, _gz))
_banner_n = 0
for (rid, c0, r0, c1, r1) in ROOMS:
    # ★네 벽을 다 돈다. 북벽만 하면 방의 나머지 세 면이 벽돌 벌판으로 남는다
    #   (부감 컷에서 그 벌판이 곧 "회색 상자"의 인상이다).
    ring = [(c, r0 - 1, "S") for c in range(c0, c1 + 1)]
    ring += [(c, r1 + 1, "N") for c in range(c0, c1 + 1)]
    ring += [(c0 - 1, r, "E") for r in range(r0, r1 + 1)]
    ring += [(c1 + 1, r, "W") for r in range(r0, r1 + 1)]
    for _i, (c, _row, _face) in enumerate(ring):
        # ★13차D. 3칸에 하나 -> **2칸에 하나**. 오너 "컨셉의 아치·기둥이 우리보다
        #   훨씬 많다." 컨셉 홀의 벽은 붙임기둥 사이 간격이 사람 키의 두 배쯤이다
        #   (여기서 3칸 = 6m 는 키의 3.4배라 벽이 다시 판때기로 읽힌다).
        if _i % 2 != 1:
            continue
        if not can_mount(c, _row) or (c, _row) in _torch_cells:
            continue
        if face_of_wall(c, _row) != _face:
            continue
        _h = WALL_H_OF[wall_class(c, _row)]
        add_pilaster(buf_cut, gx_of(c), gz_of(_row), _face, _h)
        # 깃발은 뒷벽(북쪽)에만. 남쪽 벽에 걸면 화면 아래에 눕는다
        if _face == "S" and rid in ("R_HALL", "R_ALTAR", "R_ENTRY") and _banner_n < 5:
            add_banner(buf_banner, gx_of(c), gz_of(_row), "S", _h - 0.30)
            _banner_n += 1

# ── 앞벽 위의 부서진 관석 ──
# 앞벽(1.45m)은 화면 아래 전경이라 면적이 크다. 평평한 마루가 그대로 보이면
# 벽돌 계단처럼 읽힌다. 위에 부서진 돌을 띄엄띄엄 얹어 **무너진 벽의 능선**을 만든다.
# ★콜라이더를 안 붙인다. 벽 콜라이더가 이미 그 자리를 막고 있고, 높이만 얹는 것이다.
_cope = 0
for _r in range(GRID):
    for _c in range(GRID):
        if not blocked(_c, _r) or wall_class(_c, _r) != H_FRONT:
            continue
        if (_c * 5 + _r * 3) % 4 != 1:
            continue
        # ★★공용 RND 를 **안 쓴다.** 여기서 난수를 뽑으면 그만큼 스트림이 밀려서
        #   아래 잔해 배치가 통째로 바뀐다(실제로 그래서 nav 섬이 한 칸 생겼다).
        #   칸 좌표에서 결정적으로 뽑으면 스트림이 한 톨도 안 움직이고 재현도 된다.
        #   (LOG.md 의 "공용 rnd 스트림" 함정 그대로다.)
        def _h1(k):
            return ((_c * 73856093) ^ (_r * 19349663) ^ (k * 83492791)) % 1000 / 1000.0
        _cx, _cz = gx_of(_c), gz_of(_r)
        add_box(buf_rubble, _cx + (_h1(1) - 0.5) * 0.9, _cz + (_h1(2) - 0.5) * 0.7,
                WALL_FRONT_H - 0.04,
                WALL_FRONT_H - 0.04 + 0.20 + _h1(3) * 0.32,
                0.30 + _h1(4) * 0.32, 0.28 + _h1(5) * 0.24,
                rot=(_h1(6) - 0.5) * 0.7, seg=0.9, top_boost=TOP_BONUS)
        _cope += 1

# ── 잔해 (부서진 석재 무더기) ──
# 방 구석에만 둔다. 통로와 스폰 정면은 아래 자기 검증이 다시 잰다.
# ★쓰러진 원기둥을 먼저 등록해 둔다. 안 그러면 잔해가 원기둥 속에서 솟는다.
RUBBLE = [(_fx, _fz, max(_fl * 0.5, _fr) * 0.8) for (_fx, _fz, _fy, _fl, _fr) in FALLEN]


def rubble_ok(gx, gz, rad):
    if blocked(*cell_of(gx, gz)):
        return False
    for (px, pz, pr) in RUBBLE:
        if (gx - px) ** 2 + (gz - pz) ** 2 < (rad + pr + 1.2) ** 2:
            return False
    # 통로 안에는 안 놓는다(폭 4.0m 를 좁히면 nav 두 줄 계약이 깨진다)
    c, r = cell_of(gx, gz)
    tag = ROOM_OF.get((c, r), "")
    if tag.startswith("K"):
        return False
    # 스폰 정면 통로도 비운다. ★검사가 훑는 범위(길이 + 검사 반경)를 그대로 쓴다
    for (sx, sz) in SPAWN_PTS:
        if (abs(gx - sx) < SPAWN_LANE_HALF + rad
                and -(SPAWN_LANE_LEN + SPAWN_LANE_HALF) - rad < gz - sz
                < SPAWN_LANE_HALF + rad):
            return False
    return True


for (rid, c0, r0, c1, r1) in ROOMS:
    if rid in ("R_ENTRY", "R_STAIR"):
        n = 3
    else:
        n = 6
    tries = 0
    got = 0
    while got < n and tries < 220:
        tries += 1
        gx = RND.uniform(gx_of(c0) - 0.7, gx_of(c1) + 0.7)
        gz = RND.uniform(gz_of(r0) - 0.7, gz_of(r1) + 0.7)
        big = RND.random() < 0.34
        rad = RND.uniform(0.72, 1.00) if big else RND.uniform(0.34, 0.52)
        if not rubble_ok(gx, gz, rad):
            continue
        # ★★높이가 반경보다 커야 **덩어리**로 읽힌다. 첫 판은 작은 잔해가 0.22~0.42m 라
        #   위에서 내려다보는 쿼터뷰에서 부피가 안 보이고 바닥에 뚫린 구멍처럼 읽혔다
        #   (증거 shot_05_제단_정예 · shot_01_낙하방). 큰 것은 무릎 위, 작은 것도
        #   정강이 높이는 되게 올린다.
        h = (RND.uniform(1.05, 1.45) if big else RND.uniform(0.46, 0.72))
        RUBBLE.append((gx, gz, rad))
        add_prism(buf_rubble, gx, gz, FLOOR_Y, FLOOR_Y + h,
                  rad, rad * RND.uniform(0.42, 0.68), n=RND.choice((5, 6, 7)),
                  phase=RND.uniform(0, 2), top_boost=TOP_BONUS)
        if big:
            push_col_circle(gx, gz, rad * 0.92, h, "rubble")
        got += 1

# ── 흙 얼룩 (바닥 위 한 겹) ──
# 잔해 둘레에는 부스러기가 쌓인다. 바닥 한 장짜리 화면을 깬다.
# ★반경을 잔해의 1.5배까지만 잡는다. 첫 판의 2.3배는 바닥에 깔린 **검은 구멍**으로
#   읽혔다. 색도 바닥과 한 단 차이(0.0199 대 0.0267)뿐이어야 얼룩으로 읽힌다.
for (gx, gz, rad) in RUBBLE[len(FALLEN):]:      # 앞 넷은 쓰러진 원기둥이라 건너뛴다
    add_prism(buf_dirt, gx, gz, FLOOR_Y + 0.008, FLOOR_Y + 0.010,
              rad * 1.5, rad * 1.5, n=9, phase=RND.uniform(0, 2))

# ═════════════════════════════════════════════════════════════
# 11-9) 빛을 그리는 것들 (13차B 신설) — 불꽃 · 웜 풀 · 달빛 샤프트
# ═════════════════════════════════════════════════════════════
# ★★여기가 이번 판의 심장이다. 컨셉과 1차의 결정적 차이는 **빛이 물건으로 그려져
#   있는가**였다. 컨셉의 횃불은 불꽃 + 바닥에 번진 주황 웅덩이 + 벽에 번진 자국
#   세 장으로 그려져 있고, 달빛은 콘 + 바닥 타원 + 먼지 세 장으로 그려져 있다.
#   1차는 불꽃 삼각형 하나뿐이었다.
# ── 횃불 지오메트리 ──
for _ti, (gx, gz, gy, dx, dz, ped) in enumerate(TORCH_PROPS):
    _s = RND.uniform(0, 1.0)
    if ped:
        # 받침대형: 낮은 기둥 + 사발 + 불꽃
        px, pz = gx + dx * PED_OUT, gz + dz * PED_OUT
        add_box(buf_cut, px, pz, FLOOR_Y, FLOOR_Y + 0.14, 0.30, 0.30, seg=0.9,
                top_boost=TOP_BONUS)
        add_fluted(buf_cut, px, pz, FLOOR_Y + 0.14, gy - 0.30, 0.20, 0.15,
                   n=10, vseg=3, cap=False)
        add_prism(buf_iron, px, pz, gy - 0.30, gy - 0.06, 0.17, 0.32, n=10)
        add_flame(px, pz, gy - 0.06, seed=_s)
        push_col_circle(px, pz, 0.34, 1.2, "brazier")
        # ★13차C. 웜 풀을 **불꽃 바로 밑**으로 옮겼다. 옛 판은 받침대 밑이라 웅덩이의
        #   심과 불꽃이 어긋나 있었고, 그래서 "빛이 어디서 오는지"가 안 읽혔다.
        add_pool(px, pz, 3.10)
        add_halo(px, pz, gy + 0.06)
        add_wall_glow(gx, gz, dx, dz, gy - 0.06, back=PED_OUT)
    else:
        # 벽걸이형: 쇠 팔 + 관솔
        add_box(buf_iron, gx + dx * 0.10, gz + dz * 0.10, gy - 0.62, gy - 0.10,
                0.07 if abs(dx) < 0.5 else 0.16, 0.16 if abs(dx) < 0.5 else 0.07)
        add_prism(buf_iron, gx + dx * 0.22, gz + dz * 0.22, gy - 0.20, gy + 0.02,
                  0.10, 0.20, n=6)
        add_flame(gx + dx * 0.24, gz + dz * 0.24, gy + 0.00, seed=_s)
        # ★웜 풀도 불꽃 바로 밑(0.24m)으로 당겼다. 옛 판은 1.0m 나 방 안쪽으로
        #   밀려 있어서 벽 횃불과 바닥 웅덩이가 따로 노는 두 물건이었다.
        add_pool(gx + dx * 0.34, gz + dz * 0.34, 2.90)
        add_halo(gx + dx * 0.24, gz + dz * 0.24, gy + 0.06)
        add_wall_glow(gx, gz, dx, dz, gy, back=0.0)

# ── 제단 화로 · 모닥불의 웜 풀 ──
add_pool(ALTAR_X - 2.4, ALTAR_Z + 0.2, 3.75)
add_pool(ALTAR_X + 2.4, ALTAR_Z + 0.2, 3.75)
add_pool(CAMP_X, CAMP_Z, 3.50)

# ═════════════════════════════════════════════════════════════
# 11-9b) 바닥 마모·이끼 데칼 (13차C 탈타일화 ②)
# ═════════════════════════════════════════════════════════════
# ★"타일스럽다"는 되풀이의 문제다. 텍스처를 아무리 잘 구워도 6.2m 마다 같은 그림이
#   오면 눈이 그 주기를 센다. 주기와 **아무 상관 없는 자리**에 얼룩을 흩어 놓으면
#   그 셈이 끊긴다(초원 바닥에서 메달리온이 한 노릇이 이것이다).
# ★어디에 놓는가가 종류를 정한다 — 사람이 다니는 자리는 반들반들 마모되고,
#   구석·벽 밑은 습기가 차 이끼가 낀다. 아무 데나 흩으면 그냥 때가 탄 바닥이다.
#     칸 0 통행 마모(밝고 누렇다)   1 습윤(어둡고 푸르다)
#     칸 2 이끼 침식(어둡고 초록)   3 마모 변주(작고 옅다)
WEAR_N = 74
_wear_put = []
_wear_try = 0
while len(_wear_put) < WEAR_N and _wear_try < 6000:
    _wear_try += 1
    _wx = RND.uniform(-HALF + 2.0, HALF - 2.0)
    _wz = RND.uniform(-HALF + 2.0, HALF - 2.0)
    _wc, _wr = cell_of(_wx, _wz)
    if blocked(_wc, _wr) or not walk[_wr][_wc]:
        continue
    # 잔해·기둥 밑에 깔면 안 보이고 낭비다
    if any((_wx - rx) ** 2 + (_wz - rz) ** 2 < (rr + 0.4) ** 2 for (rx, rz, rr) in RUBBLE):
        continue
    _wd = wall_dist(_wx, _wz)
    if any((_wx - px) ** 2 + (_wz - pz) ** 2 < 4.0 for (px, pz) in _wear_put):
        continue
    _wear_put.append((_wx, _wz))
    # 벽에서 1.2m 안쪽 = 구석 -> 이끼·습윤. 방 한복판 = 통행 마모
    if _wd < 1.20:
        _cell = 2 if RND.random() < 0.62 else 1
        _rad = RND.uniform(1.05, 1.85)
    else:
        _cell = 0 if RND.random() < 0.58 else 3
        _rad = RND.uniform(1.35, 2.45)
    add_wear(_wx, _wz, _rad, _cell, rot=RND.uniform(0, math.pi),
             squash=RND.uniform(0.62, 1.0))

# ── 달빛 샤프트 (컨셉의 서명) ──
# 천장 틈에서 꽂히는 푸른 빛 한 줄. 반투명 가산 콘 + 바닥 타원 + 먼지 몇 알.
# ★두 자리에만 둔다(낙하방 = 떨어진 구멍 / 중앙 회랑 = 홀의 주역). 늘리면
#   "천장이 통째로 무너진 집"이 되고 어둠이 정보를 잃는다.
SHAFTS = [
    (SHAFT_X, SHAFT_Z, 1.05, 1.55, 6.2, 0.22),   # 낙하방. 굵고 곧다
    (gx_of(13), gz_of(12), 0.82, 1.22, 5.6, -0.28),  # 중앙 회랑
]


def add_shaft(gx, gz, r_bot, r_top, h, tilt):
    """반투명 콘 한 개. 판 넉 장을 십자로 세워 만든다(진짜 원뿔은 무겁고 안 예쁘다).

    ★한 장짜리 판은 옆에서 보면 종이가 된다. 넉 장을 45도씩 돌려 세우면
      어느 각도에서 봐도 부피가 있고, 겹치는 자리가 저절로 밝아져 심이 생긴다."""
    top_x = gx + tilt * h * 0.34
    for k in range(3):
        a = k * math.pi / 3.0 + 0.31
        sx, sz = math.cos(a), math.sin(a)
        add_card(buf_shaft,
                 (gx - sx * r_bot, gz - sz * r_bot, FLOOR_Y + 0.05),
                 (gx + sx * r_bot, gz + sz * r_bot, FLOOR_Y + 0.05),
                 (top_x + sx * r_top, gz + sz * r_top, FLOOR_Y + h),
                 (top_x - sx * r_top, gz - sz * r_top, FLOOR_Y + h))


for (_sx, _sz, _rb, _rt, _sh, _tl) in SHAFTS:
    add_shaft(_sx, _sz, _rb, _rt, _sh, _tl)
    add_pool(_sx, _sz, _rb * 2.0, cold=True, squash=0.78,
             rot=RND.uniform(0, 1.0))
    # 먼지 몇 알. 빛줄기 안에서만 보이는 작은 판들
    for _d in range(9):
        _da = RND.uniform(0, 6.283)
        _dr = RND.uniform(0.1, _rb * 1.5)
        _dy = RND.uniform(0.6, _sh * 0.82)
        _ds = RND.uniform(0.035, 0.075)
        _px = _sx + math.cos(_da) * _dr + _tl * _dy * 0.34
        _pz = _sz + math.sin(_da) * _dr
        add_card(buf_dust, (_px - _ds, _pz, _dy), (_px + _ds, _pz, _dy),
                 (_px + _ds, _pz, _dy + _ds * 2), (_px - _ds, _pz, _dy + _ds * 2))

# 계단 위 찬 빛도 웅덩이로 받는다
add_pool(STAIR_X, gz_of(STAIR_R0) + 0.4, 2.30, cold=True, squash=0.72)


# ═════════════════════════════════════════════════════════════
# 12) 스폰 · 무리 · 탈출구 · 제단
# ═════════════════════════════════════════════════════════════
# ── 무리 ──
# ★enemy.js 가 마릿수를 **순번**으로 정한다: count = 3 + (i % 3).
#   그래서 이 배열의 **순서가 곧 마릿수 배분**이다(enemy.js 는 소유 밖이라 안 고친다).
#     i=0 -> 3 / i=1 -> 4 / i=2 -> 5 / i=3 -> 3 / i=4 -> 4 / i=5 -> 5
MOB_SPEC = [
    ("R_WEST",  gx_of(4), gz_of(15), 2.4),    # 3마리. 첫 전투
    ("R_EAST",  gx_of(23), gz_of(15), 2.6),   # 4마리
    ("R_ALTAR", ALTAR_X, ALTAR_Z + 4.2, 3.0),  # 5마리. 제단 정예
    ("R_NW",    gx_of(4), gz_of(3), 2.2),     # 3마리 (우물 콜라이더를 피해 북으로 한 칸)
    ("R_NE",    gx_of(23), gz_of(3), 2.6),    # 4마리
    ("R_HALL",  gx_of(13), gz_of(14), 3.0),   # 5마리. 지름길의 값
]

SPAWNS_JSON = []
for _i, (gx, gz) in enumerate(SPAWN_PTS):
    SPAWNS_JSON.append({"id": "SPAWN_%d" % (_i + 1),
                        "x": round(gx, 3), "y": 0.0, "z": round(gz, 3),
                        "yaw": round(yaw_to(gx, gz, gx, gz - 10.0), 4)})

MOBS_JSON = [{"id": "MOB_%d" % (i + 1), "x": round(m[1], 3), "y": 0.0,
              "z": round(m[2], 3), "radius": m[3]}
             for i, m in enumerate(MOB_SPEC)]

EXITS_JSON = [{"id": "EXIT_1", "x": round(EXIT_X, 3), "y": 0.0,
               "z": round(EXIT_Z, 3), "radius": 2.6}]

ALT_C0, ALT_R0, ALT_C1, ALT_R1 = ROOM_BOX["R_ALTAR"]
_arx, _arz, _arhx, _arhz = rect_world(ALT_C0, ALT_R0, ALT_C1, ALT_R1)
ALTAR_JSON = {
    "id": "ALTAR",
    "x": round(ALTAR_X, 3), "y": round(FLOOR_Y + ALTAR_TOP + 0.78, 3),
    "z": round(ALTAR_Z, 3),
    "room": {"x": round(_arx, 3), "z": round(_arz, 3),
             "hx": round(_arhx, 3), "hz": round(_arhz, 3)},
}


# ═════════════════════════════════════════════════════════════
# 13) 자기 검증 — 눈이 아니라 숫자로 남는다
# ═════════════════════════════════════════════════════════════
FAIL = []
NOTE = []


def _col_hits(gx, gz, rad):
    for co in COLLIDERS:
        if co["type"] == "circle":
            if (gx - co["x"]) ** 2 + (gz - co["z"]) ** 2 < (rad + co["r"]) ** 2:
                return True
        else:
            if (abs(gx - co["x"]) < co["hx"] + rad
                    and abs(gz - co["z"]) < co["hz"] + rad):
                return True
    return False


# 1) nav 흉내: 1.6m 격자 x 반경 0.55 로 실제 통과 가능한 칸을 뽑는다
NAV_CELL, NAV_R = 1.6, 0.55
NW_ = int(math.ceil(SIZE / NAV_CELL))
navwalk = [[False] * NW_ for _ in range(NW_)]
for _r in range(NW_):
    for _c in range(NW_):
        _x = -HALF + (_c + 0.5) * NAV_CELL
        _z = -HALF + (_r + 0.5) * NAV_CELL
        navwalk[_r][_c] = not _col_hits(_x, _z, NAV_R)


def nav_flood(sx, sz):
    sc = min(NW_ - 1, max(0, int((sx + HALF) / NAV_CELL)))
    sr = min(NW_ - 1, max(0, int((sz + HALF) / NAV_CELL)))
    if not navwalk[sr][sc]:
        return None
    seen = [[False] * NW_ for _ in range(NW_)]
    seen[sr][sc] = True
    q = [(sc, sr)]
    while q:
        c, r = q.pop()
        for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if 0 <= nc < NW_ and 0 <= nr < NW_ and navwalk[nr][nc] and not seen[nr][nc]:
                seen[nr][nc] = True
                q.append((nc, nr))
    return seen


REACH = nav_flood(*SPAWN_PTS[1])
if REACH is None:
    FAIL.append("스폰 자리가 콜라이더 안에 있다")
else:
    _n = sum(1 for row in REACH for v in row if v)
    _tot = sum(1 for row in navwalk for v in row if v)
    NOTE.append("nav 도달 %d / 통과가능 %d 칸 (%.0f%%)" % (_n, _tot, _n / max(1, _tot) * 100))
    if _n < _tot:
        FAIL.append("nav 격자에 스폰에서 못 가는 섬이 %d칸 있다" % (_tot - _n))

    def _reach(gx, gz, name, rad=0.0):
        c = min(NW_ - 1, max(0, int((gx + HALF) / NAV_CELL)))
        r = min(NW_ - 1, max(0, int((gz + HALF) / NAV_CELL)))
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                rr, cc = r + dr, c + dc
                if 0 <= rr < NW_ and 0 <= cc < NW_ and REACH[rr][cc]:
                    d = math.hypot((cc + 0.5) * NAV_CELL - HALF - gx,
                                   (rr + 0.5) * NAV_CELL - HALF - gz)
                    if d <= max(rad, NAV_CELL * 1.6):
                        return True
        FAIL.append("%s 에 못 간다 (%.1f, %.1f)" % (name, gx, gz))
        return False

    for (rid, c0, r0, c1, r1) in ROOMS:
        _reach(gx_of((c0 + c1) // 2), gz_of((r0 + r1) // 2), "방 " + rid)
    for _i, m in enumerate(MOB_SPEC):
        _reach(m[1], m[2], "무리 MOB_%d" % (_i + 1))
    _reach(ALTAR_X, ALTAR_Z + 2.0, "제단 앞", rad=2.2)
    _reach(EXIT_X, EXIT_Z, "탈출 계단", rad=2.6)

# 2) 막다른 길: 방마다 출입구가 둘 이상인가
for (rid, c0, r0, c1, r1) in ROOMS:
    doors = 0
    for (kid, kc0, kr0, kc1, kr1) in CORRIDORS:
        touch = not (kc1 + 1 < c0 or kc0 - 1 > c1 or kr1 + 1 < r0 or kr0 - 1 > r1)
        if touch:
            doors += 1
    if doors < 2:
        FAIL.append("방 %s 의 출입구가 %d개다(막다른 길)" % (rid, doors))
NOTE.append("방 %d개 · 통로 %d개 · 막다른 길 0" % (len(ROOMS), len(CORRIDORS)))

# 3) 통로 여유: 통로 단면마다 nav 칸이 **2줄 이상** 살아 있는가
# ★한 줄뿐이면 요괴가 문에 낀다. 통로 폭 4.0m 와 WALL_INSET 0.22 는 이 검사를
#   통과하려고 고른 값이다(위 상수 주석의 계산).
NAV_WIDTH = {}
for (kid, c0, r0, c1, r1) in CORRIDORS:
    vertical = (r1 - r0) >= (c1 - c0)
    # 통로의 **참 중심**과 반폭. (c0+c1)//2 로 어림하면 짝수 칸 통로에서 창이 한 칸
    # 어긋나 멀쩡한 줄을 놓친다(첫 판에서 K2·K4 가 그렇게 거짓 실패를 냈다).
    cx = gxf((c0 + c1 + 1) * 0.5)
    cz = gzf((r0 + r1 + 1) * 0.5)
    hw = (c1 - c0 + 1) * CELL * 0.5 if vertical else (r1 - r0 + 1) * CELL * 0.5
    worst = 99
    if vertical:
        for r in range(r0, r1 + 1):
            _rr = min(NW_ - 1, max(0, int((gz_of(r) + HALF) / NAV_CELL)))
            worst = min(worst, sum(
                1 for _c in range(NW_) if navwalk[_rr][_c]
                and abs(-HALF + (_c + 0.5) * NAV_CELL - cx) <= hw))
    else:
        for c in range(c0, c1 + 1):
            _cc = min(NW_ - 1, max(0, int((gx_of(c) + HALF) / NAV_CELL)))
            worst = min(worst, sum(
                1 for _r in range(NW_) if navwalk[_r][_cc]
                and abs(-HALF + (_r + 0.5) * NAV_CELL - cz) <= hw))
    NAV_WIDTH[kid] = worst
    if worst < 2:
        FAIL.append("통로 %s 의 nav 폭이 %d줄이다(2줄 필요)" % (kid, worst))
NOTE.append("통로 nav 폭 최소 %d줄 (%s)"
            % (min(NAV_WIDTH.values()),
               " ".join("%s%d" % (k, v) for k, v in NAV_WIDTH.items())))

# 4) 스폰 정면이 비었는가 (상수는 맨 위 SPAWN_LANE_* 하나를 같이 본다)
for _i, (sx, sz) in enumerate(SPAWN_PTS):
    for _t in range(1, int(SPAWN_LANE_LEN * 2) + 1):
        if _col_hits(sx, sz - _t * 0.5, SPAWN_LANE_HALF):
            FAIL.append("SPAWN_%d 정면 %.1fm 에 콜라이더가 있다" % (_i + 1, _t * 0.5))
            break

# 5) 무리 간격 17m 이상 · 무리가 벽에 안 끼는가
_mind = 1e9
for _i in range(len(MOB_SPEC)):
    for _j in range(_i + 1, len(MOB_SPEC)):
        _d = math.hypot(MOB_SPEC[_i][1] - MOB_SPEC[_j][1],
                        MOB_SPEC[_i][2] - MOB_SPEC[_j][2])
        _mind = min(_mind, _d)
if _mind < 17.0:
    FAIL.append("무리 최소 간격 %.1fm (17m 이상이어야 어그로 두 개가 안 겹친다)" % _mind)
NOTE.append("무리 최소 간격 %.1fm" % _mind)
for _i, m in enumerate(MOB_SPEC):
    if _col_hits(m[1], m[2], 0.9):
        FAIL.append("무리 MOB_%d 자리가 콜라이더에 낀다" % (_i + 1))

# 6) 증표 접근: 제단 반경 1.7m(TOKEN_PICK_R) 안에 설 수 있는 자리가 있는가
_ok = False
for _a in range(24):
    _ang = _a * math.pi / 12
    _px = ALTAR_X + math.cos(_ang) * 1.6
    _pz = ALTAR_Z + math.sin(_ang) * 1.6
    if not _col_hits(_px, _pz, 0.35):
        _ok = True
        break
if not _ok:
    FAIL.append("제단 반경 1.7m 안에 설 수 있는 자리가 없다(증표를 못 줍는다)")


# ═════════════════════════════════════════════════════════════
# 14) 재질 — 정점색 평균을 **재서** 곱수를 푼다 (두 번 훑기)
# ═════════════════════════════════════════════════════════════
def shade_mean_of(buf):
    """면적 가중 정점색 평균(RGB). 값이 없으면 1."""
    if not buf.c or not buf.f:
        return (1.0, 1.0, 1.0)
    tot_a = 0.0
    acc = np.zeros(3, np.float64)
    for f in buf.f:
        vs = [buf.v[i] for i in f]
        # 다각형 면적(뉴웰)
        nx = ny = nz = 0.0
        for i in range(len(vs)):
            a = vs[i]
            b = vs[(i + 1) % len(vs)]
            nx += (a[1] - b[1]) * (a[2] + b[2])
            ny += (a[2] - b[2]) * (a[0] + b[0])
            nz += (a[0] - b[0]) * (a[1] + b[1])
        area = 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)
        if area <= 0:
            continue
        m = np.zeros(3, np.float64)
        for i in f:
            m += np.asarray(buf.c[i], np.float64)
        m /= len(f)
        acc += m * area
        tot_a += area
    if tot_a <= 0:
        return (1.0, 1.0, 1.0)
    r = acc / tot_a
    return (float(r[0]), float(r[1]), float(r[2]))


ALL_BUFS = [buf_floor, buf_floorb, buf_dirt, buf_wall, buf_cut, buf_altar,
            buf_stair, buf_iron, buf_banner, buf_rubble,
            buf_medal, buf_pool, buf_poolc, buf_shaft, buf_flame, buf_dust,
            buf_wglow, buf_halo, buf_wear]
for _b in ALL_BUFS:
    if _b.glow:
        _b.c = []          # 이미시브는 정점색을 안 탄다. 버퍼에서 지운다
        _b.shade = (1.0, 1.0, 1.0)
    else:
        _b.shade = shade_mean_of(_b)

# ★★14차. hue_keep 이 뒤집혔다(위 HUE_KEEP 주석 참고). 텍스처가 곧 컨셉이라
#   색기를 지우면 안 된다. 다만 **다른 물건으로 읽혀야 하는 것**만 조금 내린다:
#     계단 0.45 = 유일하게 찬 돌(출구 표식). 벽과 같은 보라면 못 찾는다
#     제단 0.62 = 밝은 라일락 다듬돌. 벽 블록 색이 그대로 오면 벽의 일부로 읽힌다
buf_floor.mat = mat_tex("MAT_DG_FLOOR", PAL["floor"], IMG_FLOOR, FLOOR_LIN,
                        shade=buf_floor.shade, hue_keep=0.92)
buf_floorb.mat = mat_tex("MAT_DG_FLOORB", PAL["floor"], IMG_FLOOR_B, FLOOR_B_LIN,
                         shade=buf_floorb.shade, hue_keep=0.92)
buf_dirt.mat = mat_tex("MAT_DG_DIRT", PAL["dirt"], IMG_FLOOR_B, FLOOR_B_LIN,
                       shade=buf_dirt.shade, hue_keep=0.80)
buf_wall.mat = mat_tex("MAT_DG_WALL", PAL["wall"], IMG_WALL, WALL_LIN,
                       shade=buf_wall.shade, hue_keep=0.90)
# ★3차 시도에서 기둥이 **사탕 토템**이었다. 벽 텍스처의 블록별 색변주가 원통에
#   감기면서 가로 줄무늬가 됐다. 기둥·아치·문설주는 컨셉에서 **다듬은 한 덩이 돌**
#   이라 색이 균일해야 한다 = hue_keep 을 내려 목표색(라일락)으로 끌어당긴다.
buf_cut.mat = mat_tex("MAT_DG_CUT", PAL["cut"], IMG_BLOCK, BLOCK_LIN,
                      shade=buf_cut.shade, hue_keep=0.70)
buf_altar.mat = mat_tex("MAT_DG_ALTAR", PAL["altar"], IMG_BLOCK, BLOCK_LIN,
                        shade=buf_altar.shade, hue_keep=0.70)
buf_stair.mat = mat_tex("MAT_DG_STAIR", PAL["stair"], IMG_BLOCK, BLOCK_LIN,
                        shade=buf_stair.shade, hue_keep=0.45)
# 잔해도 다듬은 돌이다(컨셉의 바닥에 굴러다니는 것은 무너진 아치·기둥 조각이다).
buf_rubble.mat = mat_tex("MAT_DG_RUBBLE", PAL["rubble"], IMG_BLOCK, BLOCK_LIN,
                         shade=buf_rubble.shade, hue_keep=0.60)
buf_iron.mat = mat_solid("MAT_DG_IRON", PAL["iron"], rough=0.66,
                         shade=buf_iron.shade)
buf_banner.mat = mat_solid("MAT_DG_BANNER", PAL["banner"], rough=0.95,
                           shade=buf_banner.shade)
# 제단 메달리온. 돌은 조명을 타고 **파란 룬만** 스스로 빛난다(emit 0.9)
buf_medal.mat = mat_decal("MAT_DG_MEDAL", PAL["medal"], IMG_MEDAL, MEDAL_LIN,
                          shade=(1.0, 1.0, 1.0), emit=0.30)
# ── 빛 자체 ──
# ★세기는 ACES 를 견디는 선에서 고른다. 2 를 넘기면 주황이 흰색으로 말려 올라가
#   "웜 풀"이 아니라 "흰 얼룩"이 된다(LOG.md 의 그 함정). 불꽃 심지만 그 위로 보낸다.
# ★13차C. 0.26 -> 0.52. 가산으로 바뀌면서 알파가 '가리는 양'이 아니라 '더하는 양'이
#   됐다 = 옛 알파 블렌딩에서 바닥을 지우며 얻던 밝기를 이제 세기로 내야 한다.
#   0.52 x 알파 0.66 = 0.34 선형 < 블룸 임계 1.02 (안 번진다)
# ★★13차D. 0.52 -> 0.74. 여기가 "횃불 존이 주인공"을 만드는 유일한 층이다.
#   정점색으로는 못 낸다 - 화면 R/B 는 E(0.45) x 알베도 x 정점색 인데 정점색은
#   1 에서 잘리므로 아무리 밀어도 R/B 2.7 언저리가 천장이다. 컨셉의 횃불 둘레는
#   **8.8**, 코어는 18.6 이다. 이미시브는 조명 사슬 밖(화면 = 빛 + 이미시브)이라
#   그 폭을 낸다. AMB 를 내려 바닥이 어두워진 만큼 이 층의 대비가 같이 커진다.
#   ★14차: 맥동을 ±30% 로 올리면서 세기를 1.06 으로 맞췄다(web/level.js 와 한 짝).
# ★14차. 0.74 -> 1.05. 씬이 여섯 배 밝아졌으므로 같은 세기로는 웜 풀이 안 보인다.
#   블룸 계약(알파 **최대**로 잰다): 1.05 x 0.720 x 맥동 1.20 = 0.907 < 임계 1.02 ✓
buf_pool.mat = mat_glow("MAT_DG_POOL", IMG_POOL, 1.06)   # 1.06x0.720x1.30 = 0.992 < 1.02 ✓
# ★13차D. 0.62 -> 0.50. 콘을 줄이고 웅덩이만 두면 **바닥에 놓인 파란 전구**가 된다
#   (1차 시도 캡처가 그랬다). 빛줄기와 웅덩이는 세기 비가 유지돼야 위에서 내려온
#   빛으로 읽힌다 - 둘을 같이 내리고 콘 쪽을 덜 내린다.
# ★★14차 4차 판정. 제단 컷에서 이 세 겹이 **흰 고리**로 읽혔다(증거 shots_after4/altar).
#   13차의 어두운 던전에서는 "위에서 내려오는 빛"이었지만 씬이 여섯 배 밝아지자
#   같은 세기가 배경을 못 이기고 유령 링만 남는다. 셋을 같이 내린다 —
#   출구 표식이라 없애지는 않는다(계단 자리를 이 빛으로 찾는다).
buf_poolc.mat = mat_glow("MAT_DG_POOLC", IMG_POOLC, 0.40)
# ★13차D. 0.52 -> 0.34. 오너 "달빛 샤프트는 국소 연출로만." 콘은 6m 짜리 반투명
#   덩어리라 세기가 화면 넓이로 직결된다 - 바닥 웅덩이(POOLC)는 살리고 **공중
#   덩어리만** 줄여야 "빛줄기"가 남고 "파란 안개"가 걷힌다.
buf_shaft.mat = mat_glow("MAT_DG_SHAFT", IMG_SHAFT, 0.20)
buf_dust.mat = mat_glow("MAT_DG_DUST", IMG_POOLC, 0.60)
# ★불꽃만 블룸 임계를 넘긴다. three 는 **렌더타겟에 그릴 때 톤매핑을 안 건다**
#   (currentRenderTarget !== null 이면 NoToneMapping). 그래서 RenderPass 출력은
#   클램프 안 된 선형 HDR 이고, UnrealBloomPass 임계 1.02 를 이미시브가 날것으로 넘는다.
#   웜 풀(0.26)·달빛(0.78)·샤프트(0.52)는 전부 임계 아래라 안 번지고, 불꽃만 번진다 -
#   컨셉에서 횃불에만 후광이 있는 것과 같다.
# ★함정 기록: 화면 왼쪽이 붉게 물드는 것을 처음엔 이 세기 탓으로 오해해서 3.40 을
#   1.25 까지 내렸다. 진범은 **UI 였다** - `#hurtDir`(피격 방향 표시)가
#   `rgba(150,16,16,0.44)` 그라디언트를 화면 가장자리에 깐다. 캠프 한복판에 세워 놓고
#   찍었으니 매 컷이 피격 중이었다. 판정 컷은 **전투 밖에서** 찍을 것.
buf_flame.mat = mat_glow("MAT_DG_FLAME", IMG_FLAME, 2.40)
# ── 13차C ──
# ★셋 다 web/level.js 가 **가산 합성**으로 갈아 준다. 알파 블렌딩으로 두면 빛이
#   바닥돌·벽돌을 지우는 물감이 된다(옛 웜 풀이 스티커로 읽힌 진짜 원인이 그것이다).
# ★세기는 블룸 임계(1.02) 아래로 묶는다. 번지는 것은 불꽃(2.40)뿐이 계약이다.
#   후광 0.95 x 알파 0.66 = 0.63 · 벽 자국 0.70 x 0.37 = 0.26 — 둘 다 안 번진다.
# ★13차D. 0.82 -> 0.96 (웜 풀과 같은 이유).
#   계약 0.96 x 알파 0.722 x 맥동 1.20 = 0.832 < 임계 1.02
buf_halo.mat = mat_glow("MAT_DG_HALO", IMG_POOL, 1.06)   # 1.06 x 0.720 x 1.30 = 0.992 ✓
# ★1.35 는 벽에 손전등을 켠 그림이 됐다(증거 shots/afterB_hall). 빛은 벽을
#   "데우는" 것이지 "비추는" 것이 아니다 - 돌 무늬가 그 위로 계속 읽혀야 한다.
# ★★13차D. 0.78 -> 0.86. 처음엔 0.98 로 올렸다가 **블룸 계약 위반**을 잡고 내렸다.
#   ★13차C LOG 에 적힌 "벽 자국 알파 0.37" 은 **평균**이지 최대가 아니다(실측
#     dg_wglow.png 알파 최대 = 0.996). 계약은 최대로 재야 한다:
#         0.98 x 0.996 x 맥동 1.12 = 1.093 > 블룸 임계 1.02  ← 벽이 번진다
#         0.86 x 0.996 x 1.12      = 0.959 < 1.02            ← 안 번진다
#   웜 풀·후광도 같은 자로 다시 쟀다(0.641 · 0.883). 번지는 것은 불꽃(2.71)뿐이다.
buf_wglow.mat = mat_glow("MAT_DG_WGLOW", IMG_WGLOW, 0.86)
# 마모·이끼는 **돌**이다. 조명·정점색을 그대로 타야 웜 풀 밑에서 같이 데워진다.
buf_wear.mat = mat_decal("MAT_DG_WEAR", PAL["floor"], IMG_WEAR, WEAR_LIN,
                         shade=buf_wear.shade)


# ═════════════════════════════════════════════════════════════
# 15) 메시 생성
# ═════════════════════════════════════════════════════════════
sc = bpy.context.scene


def tri_uv(scale, rot=0.0):
    """면 법선의 우세 축으로 고르는 삼중평면 UV. 벽면은 (둘레, 높이) 로 찍힌다.

    ★한 축으로만 투영하면 벽 마루(윗면)에서 무늬가 길게 늘어난다.
    ★13차C. rot 은 **윗면(바닥) 투영에만** 건다. 옆면까지 돌리면 벽돌 단이
      비스듬히 기울어서 벽이 무너진 것처럼 보인다."""
    cs, sn = math.cos(rot), math.sin(rot)

    def f(co, poly):
        n = poly.normal
        ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2]) * 1.25
        if az >= ax and az >= ay:
            u, v = co[0] / scale, co[1] / scale
            return (u * cs - v * sn, u * sn + v * cs)
        if ax >= ay:
            return (co[1] / scale, co[2] / scale)
        return (co[0] / scale, co[2] / scale)
    return f


def make_obj(buf):
    if not buf.f:
        return None
    me = bpy.data.meshes.new(buf.name)
    me.from_pydata(buf.v, [], buf.f)
    me.validate(verbose=False)
    # ★삼중평면 UV 가 면 법선을 본다. update() 를 먼저 돌려야 poly.normal 이 산다
    me.update()
    if buf.tile:
        uvl = me.uv_layers.new(name="UVMap")
        arr = []
        if buf.uv:
            # 데칼·스프라이트: 면마다 0..1 이 통째로 박힌다(정점마다 적어 뒀다)
            for poly in me.polygons:
                for li in poly.loop_indices:
                    u, v = buf.uv[me.loops[li].vertex_index]
                    arr += [u, v]
        else:
            uvfn = tri_uv(buf.uv_scale, buf.uv_rot)
            for poly in me.polygons:
                for li in poly.loop_indices:
                    u, v = uvfn(me.vertices[me.loops[li].vertex_index].co, poly)
                    arr += [u, v]
        try:
            uvl.data.foreach_set("uv", arr)
        except Exception:
            uvl.uv.foreach_set("vector", arr)
    if buf.c:
        # ★FLOAT_COLOR 는 블렌더에서 **선형**이라 익스포터가 감마를 안 건다
        #   (BYTE_COLOR 로 넣으면 sRGB 로 보고 변환해서 값이 달라진다).
        col = me.color_attributes.new(name="Shade", type="FLOAT_COLOR", domain="POINT")
        vals = []
        for i in range(len(me.vertices)):
            s = buf.c[i] if i < len(buf.c) else (1.0, 1.0, 1.0)
            vals += [s[0], s[1], s[2], 1.0]
        col.data.foreach_set("color", vals)
        # ★"활성"이 두 종류다. 편집용(active)과 **렌더용(default)**. 익스포터가 보는 건
        #   렌더용이라 둘 다 못 박는다.
        for _at in ("active_color_name", "default_color_name"):
            if hasattr(me.color_attributes, _at):
                setattr(me.color_attributes, _at, col.name)
    me.materials.append(buf.mat)
    for p in me.polygons:
        p.use_smooth = False          # 로우폴리는 각진 게 맞다
    me.update()
    ob = bpy.data.objects.new(buf.name, me)
    sc.collection.objects.link(ob)
    return ob


tri_total = 0
for _b in ALL_BUFS:
    make_obj(_b)
    tri_total += _b.tri_count()
    print("[메시] %-12s 정점 %5d · 삼각형 %5d · 정점색평균 %.3f %.3f %.3f"
          % (_b.name, len(_b.v), _b.tri_count(), _b.shade[0], _b.shade[1], _b.shade[2]))
print("[삼각형] 합계 %d" % tri_total)


def add_empty(name, gx, gz, y=0.0, size=1.2):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = size
    e.location = bpos(gx, gz, y)
    sc.collection.objects.link(e)
    return e


for _i, (gx, gz) in enumerate(SPAWN_PTS):
    add_empty("SPAWN_%d" % (_i + 1), gx, gz)
for _i, m in enumerate(MOB_SPEC):
    add_empty("MOB_%d" % (_i + 1), m[1], m[2])
add_empty("EXIT_1", EXIT_X, EXIT_Z)
add_empty("ALTAR", ALTAR_X, ALTAR_Z, y=ALTAR_TOP + 0.78, size=2.0)


# ═════════════════════════════════════════════════════════════
# 16) 색 규칙 검증 (걸을 수 있는 곳 > 못 가는 곳)
# ═════════════════════════════════════════════════════════════
def rel_lum(lin):
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


print("\n[곱수] 재질별 계약 (곱수는 1 을 넘으면 안 된다)")
# ★13차B. 검사 기준이 **휘도**로 바뀌었다. hue_keep 만큼 타일의 색기를 살리므로
#   채널별 값은 일부러 목표에서 벗어난다. 그런데 휘도는 수학적으로 정확히 보존된다
#   (k_i = (1-h)per_i + h*s 를 넣고 풀면 L(k x 타일) = L(목표) 가 항등식이다).
#   그래서 휘도가 어긋나면 그건 hue_keep 이 아니라 **곱수가 1 에서 잘린 것**이다.
_pal_lum = {}
for (nm, hx, k, sh, tile) in MAT_LOG:
    got = [k[i] * float(tile[i]) * sh[i] for i in range(3)]
    want = hex_lin(hx)
    err = abs(rel_lum(got) - rel_lum(want)) / max(1e-6, rel_lum(want))
    _pal_lum[nm] = rel_lum(got)
    # ★13차D 추가. R/B = **알베도 평균의 색온도**. 화면 = E(R/B 0.45) x 이 값 x 정점색
    #   이므로 여기가 1.6 을 밑돌면 어떤 정점색을 줘도 화면이 새벽 파랑에서 못 나온다.
    print("  %-16s 목표 #%s  곱수 %.3f %.3f %.3f  정점 %.3f  화면선형 %.4f  R/B %.2f  휘도오차 %.1f%%"
          % (nm, hx, k[0], k[1], k[2], (sh[0] + sh[1] + sh[2]) / 3,
             rel_lum(got), got[0] / max(1e-6, got[2]), err * 100))
    if err > 0.06:
        FAIL.append("%s 화면휘도가 목표에서 %.0f%% 벗어났다(곱수가 1 에서 잘렸다)" % (nm, err * 100))

if _pal_lum.get("MAT_DG_FLOOR", 0) <= _pal_lum.get("MAT_DG_WALL", 1):
    FAIL.append("색 규칙 위반: 바닥이 벽보다 밝지 않다")
else:
    NOTE.append("색 규칙 바닥 %.4f > 벽 %.4f (배수 %.2f)"
                % (_pal_lum["MAT_DG_FLOOR"], _pal_lum["MAT_DG_WALL"],
                   _pal_lum["MAT_DG_FLOOR"] / max(1e-6, _pal_lum["MAT_DG_WALL"])))

if _torch_bad:
    FAIL.append("횃불 %d자루가 벽이 아니거나 앞벽(낮은 벽)에 걸렸다: %s"
                % (len(_torch_bad), _torch_bad[:6]))
NOTE.append("횃불 %d자루 · 광원 %d개" % (len(TORCH_PROPS), len(LIGHTS)))

# 바닥 정점색의 밝고 어두운 대역 (횃불 웅덩이와 어둠의 리듬이 실제로 있는가)
_fc = np.array(list(buf_floor.c) + list(buf_floorb.c), np.float32)
_fl = 0.2126 * _fc[:, 0] + 0.7152 * _fc[:, 1] + 0.0722 * _fc[:, 2]
NOTE.append("바닥 정점밝기 최소 %.2f · 중앙 %.2f · 최대 %.2f (밝은 10%% %.2f 이상)"
            % (_fl.min(), float(np.median(_fl)), _fl.max(),
               float(np.percentile(_fl, 90))))
if _fl.max() - _fl.min() < 0.30:
    FAIL.append("바닥 밝기 폭이 %.2f 뿐이다. 웜 존과 어둠 존의 리듬이 안 읽힌다"
                % (_fl.max() - _fl.min()))


# ═════════════════════════════════════════════════════════════
# 17) 내보내기
# ═════════════════════════════════════════════════════════════
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))
bpy.ops.object.select_all(action="SELECT")
# ★export_vertex_color="ACTIVE": 던전의 어둠(COLOR_0)을 내보내는 열쇠다.
#   기본값 "MATERIAL" 은 COLOR_0 과 COLOR_1 을 **둘 다** 싣는다.
# ★★13차B. export_image_format 이 "JPEG" 에서 **"AUTO"** 로 바뀌었다.
#   웜 풀·달빛·불꽃·메달리온은 **알파가 정보**인데 JPEG 에는 알파 채널이 없다.
#   JPEG 로 강제하면 그 넉 장이 불투명 사각형이 되어 바닥에 검은 판이 깔린다.
#   AUTO 는 원본 형식을 따라가므로, 불투명한 석재 타일은 tools/dungeon_tex.py 가
#   **jpg 로 구워 둔 것**을 읽어 그대로 jpg 로 나간다(png 로 두면 glb 가 3배가 된다).
bpy.ops.export_scene.gltf(
    filepath=TMP_GLB, export_format="GLB", use_selection=False,
    export_animations=False, export_yup=True,
    export_apply=True, export_vertex_color="ACTIVE",
    export_image_format="AUTO", export_image_quality=TEX_QUALITY,
    export_jpeg_quality=TEX_QUALITY)
_sz = os.path.getsize(TMP_GLB)
print("\n[내보내기] %.2f MB (임시)" % (_sz / 1024 / 1024))
if _sz > 5 * 1024 * 1024:
    print("[경고] glb 예산 5MB 초과")


# ═════════════════════════════════════════════════════════════
# 18) level2.json
# ═════════════════════════════════════════════════════════════
GRID_ASCII = []
for r in range(GRID):
    row = ""
    for c in range(GRID):
        if not walk[r][c]:
            row += "#"
        elif ROOM_OF.get((c, r), "").startswith("K"):
            row += "-"
        else:
            row += "."
    GRID_ASCII.append(row)

data = {
    "name": "level2",
    "title": "탑 1층 - 어둠에 잠긴 회랑",
    "generatedBy": "blender/s40_dungeon1.py",
    "design": "docs/dungeon1-design.md",
    "coordinateSystem": (
        "three.js. X=동, Y=위, Z=남. 블렌더 원본은 Z-up 이고 export_yup=True 로 "
        "변환됐다(three.x=blender.x, three.y=blender.z, three.z=-blender.y). "
        "아래 숫자는 전부 three.js 좌표라 변환 없이 그대로 쓰면 된다."
    ),
    "unit": "1 = 1m. 캐릭터 키 1.75.",
    "size": {"x": SIZE, "z": SIZE},
    "bounds": {"minX": -HALF, "maxX": HALF, "minZ": -HALF, "maxZ": HALF},
    "cell": CELL,
    "gridCells": GRID,
    "floorY": FLOOR_Y,
    "wallHeight": WALL_BACK_H,
    # ★level.js 가 이걸 보고 초원용 지면 스플랫(풀·흙 타일)을 **안 얹는다.**
    #   던전 바닥은 정점색과 석판 타일로 이미 완성돼 있다.
    "floorLook": False,
    "spawns": SPAWNS_JSON,
    "mobs": MOBS_JSON,
    "mobNote": (
        "★enemy.js 가 마릿수를 순번으로 정한다(count = 3 + i%3). 그래서 이 배열의 "
        "**순서가 곧 마릿수 배분**이다: 3 / 4 / 5 / 3 / 4 / 5. "
        "자리 뜻은 " + " · ".join("%s=%d마리" % (m[0], 3 + i % 3)
                                  for i, m in enumerate(MOB_SPEC)) + ". "
        "무리 최소 간격 %.1fm (어그로 7m 두 개가 안 겹쳐야 한 무리만 떼어낼 수 있다)."
        % _mind
    ),
    # ★보스 없음. boss 키를 일부러 안 넣는다 - 이 층에 각귀(boss.glb)는 안 뜬다.
    "exits": EXITS_JSON,
    "altar": ALTAR_JSON,
    "altarNote": (
        "증표(符)가 처음부터 놓여 있는 제단. web/level2.js 가 여기서 증표를 띄우고, "
        "주우면 exits[] 의 계단까지 들고 나가야 층 돌파다. 보스가 떨구지 않는다."
    ),
    "goal": {
        "pick": "{방위}, 제단의 <i>증표</i>를 집어라",
        "escape": "{방위}, <i>증표</i>를 들고 {문}으로",
        "clear": "층 돌파",
        "expose": " <i>· 고블린들이 증표를 쫓는다</i>",
        "floorName": "어둠에 잠긴 회랑",
        "floorLore": "천장이 무너진 자리로 떨어졌다. 올라갈 길은 없다.",
        "hudName": "1층 · 어둠에 잠긴 회랑",
        "exitWord": "계단",
        "note": (
            "오너가 문구를 바꿀 자리다. {방위}, 와 {문} 이 치환자다. "
            "floorName·floorLore 는 입장 타이틀 카드(ui.js) 글자를 표시 단계에서 "
            "갈아 끼우는 값이다. hudName 은 화면 위 HUD 이름."
        ),
    },
    "bushes": [],
    "bushNote": "던전에는 숨을 수풀이 없다. stealth.js 는 빈 배열로 조용히 돈다.",
    "props": [],
    "propNote": "외부 소품 glb 를 안 쓴다. 모든 지오메트리가 level2.glb 안에 있다.",
    "colliders": COLLIDERS,
    "colliderNote": (
        "박스는 축정렬(회전 없음)이라 2D AABB 로 바로 검사하면 된다. circle 은 원기둥. "
        "glb 안에서 COL_ 로 시작하는 메시가 막는 지형이고 DECO_ 는 안 막는다. "
        "tag: wall=돌벽 · pillar=회랑 기둥 · altar=제단 · brazier=화로 · "
        "well=우물 · campfire=모닥불 · rubble=큰 잔해. "
        "★벽 콜라이더는 칸 경계에서 %.2fm 안으로 들어가 있다(통로 실폭 %.2fm)."
        % (WALL_INSET, CELL * 2 + WALL_INSET * 2)
    ),
    "platforms": PLATFORMS,
    "platformNote": (
        "올라설 수 있는 낮은 단(제단 %.2fm · 계단 다섯 단). top 은 floorY 를 포함한 "
        "절대 높이다. 겹치면 제일 높은 값이 이긴다." % (FLOOR_Y + ALTAR_TOP)
    ),
    "lightNote": (
        "실광원이 아니라 **정점색(glTF COLOR_0)** 으로 구운 빛이다. 횃불 %d자루 + "
        "특수 광원 %d개. 밝기 = clamp(AMB + Σ 세기/(1+(d/R)^2)). "
        "AMB 는 차고(파란 기) 횃불은 따뜻하다 - 그 색 대비가 곧 '어둠'의 정보다."
        % (len(TORCH_PROPS), len(LIGHTS) - len(TORCH_PROPS))
    ),
    "grid": GRID_ASCII,
    "gridLegend": {"#": "돌벽(막는다)", "-": "통로(폭 4.0m)", ".": "방"},
    "wallNote": (
        "벽 높이는 카메라가 정한다. 고정 쿼터뷰 yaw 0 이라 벽은 플레이어보다 "
        "남쪽에 있을 때만 가린다. 북쪽 이웃이 걸을 수 있는 벽 칸 = 그 방의 앞벽 = "
        "%.2fm(낮다). 남쪽 이웃이 걸을 수 있거나 속 채움 = 뒷벽 = %.2fm. "
        "맵 테두리 %.2fm. 자세한 계산은 docs/dungeon1-design.md 5절."
        % (WALL_FRONT_H, WALL_BACK_H, WALL_EDGE_H)
    ),
}

with open(TMP_JSON, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

# ★원자적으로 갈아끼운다. 게임이 반쪽짜리를 읽으면 좌표와 그림이 어긋난다.
os.replace(TMP_GLB, OUT_GLB)
os.replace(TMP_JSON, OUT_JSON)

print("\n[검증]")
for n in NOTE:
    print("  · " + n)
if FAIL:
    print("\n[실패] %d건" % len(FAIL))
    for f_ in FAIL:
        print("  ✗ " + f_)
else:
    print("  ✓ 전부 통과")
print("\n[완료] %s (%.2f MB) + %s"
      % (OUT_GLB, os.path.getsize(OUT_GLB) / 1024 / 1024, OUT_JSON))
