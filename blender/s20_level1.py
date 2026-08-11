# -*- coding: utf-8 -*-
"""탑 1층 맵을 만들어 web/level1.glb + web/level1.json 으로 내보낸다.

실행: blender -b -P blender/s20_level1.py

세계관은 "무너진 산사(山寺) 터를 삼킨 야생". 담장과 건물이 공간을 나누던 판을
**자연 지형**으로 갈아엎었다. 막는 건 바위 절벽, 빽빽한 덤불, 흙 둔덕, 개울이고
사람의 흔적은 폐허로만 남는다(이끼 낀 석탑 하나, 무너진 석등 몇, 부러진 석주,
부서진 돌계단, 입구의 선돌). 주역은 자연이다.

★v67 에서 레이아웃을 통째로 다시 짰다. 여기가 탑 100층의 **1층**이다.
  1층은 탁 트여야 하고 좁고 어두운 건 깊은 층의 몫이라, 전제를 뒤집었다.

    (전) 맵 전체가 막힌 상태에서 통로를 파냈다  -> 1칸(3.2m) 협곡이 널렸다
    (후) 맵 전체가 열린 초원이고 막는 덩어리를 **띄엄띄엄 얹는다**

  1. 통로 최소 2칸(6.4m). 주요 길은 4칸(12.8m). 1칸 통로는 하나도 없다
  2. 걷기 가능 면적 48% -> 65% (1.6m 격자 기준. web/nav.js 가 찍는 그 숫자다)
  3. **연속 벽을 해체했다.** 안쪽에는 길이 3칸 넘는 벽이 없다. 1~3칸짜리
     바위 무더기·덤불 덩어리가 3칸 이상 떨어져 흩어져 있고 그 사이로 건너편이 보인다
  4. ★막는 것과 가리는 것을 분리했다. 절반은 **너덜지대(높이 1.45m)** 라
     몸은 못 지나가지만 캐릭터 키(1.75)보다 낮아서 **건너편이 그대로 보인다.**
     개울도 같다(수면 높이 0.02, 폭 3.2m). 이게 개방감의 핵심 장치다
  5. 외곽 절벽 링은 유지하되 안으로 기운 각(lean)을 0.60 -> 0.22 로 눕혀 압박을 줄이고
     맵 밖에 옅은 안개 능선 세 겹을 세워 "너머가 아득하게" 보이게 했다
  6. 가운데 석탑을 4.2m -> 13m 로 키웠다. 선돌 문은 3.4m -> 4.6m
  7. 바닥 팔레트를 밤 톤에서 **봄 낮**으로 올렸다(연둣빛 풀·따뜻한 흙길·금빛 마른 풀).
     "밝고 따뜻하면 걸을 수 있다 / 차갑고 어두우면 못 간다" 규칙은 그대로다

────────────────────────────────────────────────────────────────
★v79. 신선한 눈 QA 가 잡은 마찰 여섯 가지를 고쳤다. 레이아웃 철학은 안 건드렸다.

  1. 개울 도하 지점이 안 읽혔다. 막힌 개울 한가운데 둥근 바위를 둘러 놨더니
     그게 통째로 "디딤돌"로 읽혔다(밟아 보고 → 못 건너고 → 짜증). 막힌 구간에서
     밟을 만한 것을 전부 뺐다(갈대로 대체). 통나무·디딤돌·선돌은 **여울목에만**
     둔다. 여울목 바닥은 젖은 돌 색을 남북으로 두 칸 더 이어 붙여 개울을 가로지르는
     창백한 띠로 만들었다. 아래 자기 검증이 "콜라이더로 뚫린 틈"과 표식 좌표를
     대조한다(어긋나면 그 자리에서 소리를 지른다)
  2. 스폰 정면에 바위 무더기가 있었다. 스폰마다 **정면 15m x 폭 4.4m** 를 비운다.
     막는 소품 배치가 전부 lane_clear() 를 통과해야 하고 검증이 다시 잰다
  3. 스폰이 경계에서 4.8m 뿐이라 화면 아래가 맵 밖(회색)이었다. 스폰을 안으로
     6.4~9.3m 물렸다. 그래도 경계로 걸어가면 보이니까 경계 바깥에 **배후 스커트**
     (바깥으로 26m 뻗어 7.6m 까지 올라가는 비탈 + 숲)를 둘렀다.
     ★예전에 폐기한 "맵 밖 60~150m 안개 능선"과 다르다. 그건 멀고 높아서 화면을
       통째로 가렸다. 이건 경계에 붙어서 화면 맨 끝 띠로만 들어온다
  4. 보스에서 EXIT_1 로 가는 직선 위에 무리가 정면으로 앉아 있었다. 3.2~3.5m 씩
     비켜 세워 "돌아갈지 뚫을지"가 선택이 되게 했다
  5. 수풀 16곳이 전부 무리에서 9.3m 밖이라 "몰래 지나가기"를 쓸 자리가 없었다.
     세 곳을 무리에서 8.0~8.6m(어그로 7m 밖) 길목으로 옮겼다
  6. 잡동사니. 통나무 이끼가 축이 아니라 X 로만 밀려서 90도로 눕힌 통나무 옆
     허공에 초록 판때기가 떠 있었다. 어귀 문설주 자리에 지형 프롭이 겹쳐 흰 석주가
     바위를 관통했다. 둘 다 원인을 막았다
────────────────────────────────────────────────────────────────
★v86. 2차 QA 의 맵 항목 3건 + 부수 1건. 레이아웃은 안 건드렸다.

  S7 서쪽 경계가 무텍스처 회색 평면(화면의 12~40%)
    (1) 절벽·스커트·스커트 바위에 **돌결 타일**(6b절, 이어붙는 512, 한 장 3.2m)을 입혔다.
        색은 타일이 아니라 재질이 정한다(baseColorFactor = 목표색/타일평균/정점색평균).
        그래서 "어둡고 차가우면 못 간다" 색 규칙이 한 톨도 안 움직인다([색규칙] 줄이 잰다)
    (2) 절벽을 **세 단으로 쪼갰다.** 단마다 안으로 0.13m 턱을 물리고 아랫도리를 눌러
        (정점색 = glTF COLOR_0) 한 벽에 밝기 여섯 단을 만들었다. 결만 입히고 면을
        그대로 두면 무슨 텍스처를 써도 판때기로 보인다
    (3) 흰 다각형 파편의 정체 = DECO_HAZE1/2/3(절벽 위 흰 봉우리 42개). 폐기했다
  S8 수풀이 도하 지점을 덮는다 -> 서·동 여울목 수풀 4곳을 차선 옆으로 비켰다.
     ★규칙 신설: 수풀 칸 사각형과 도하 차선은 겹치면 안 된다(4절 자기 검증)
  S11 물 평면 가장자리 삐져나옴 -> 인셋 0.55 -> 0.80(바닥색 휨 폭 0.64 를 넘긴다),
      수면을 3x3 격자로 깔아 **가장자리를 어둡게 죽이고**(정점색), 물칸 안쪽에도
      젖은 그늘 띠를 칠했다(15절 _rim_in)
  부수 보스 방향 어귀 세 곳(남·서·동)의 선돌에만 붉은 끈을 감았다. 나침반의 지형판
────────────────────────────────────────────────────────────────
★v89. 3차 QA 의 맵 항목 넷. 레이아웃(칸 격자·콜라이더·도하 차선)은 한 칸도 안 건드렸다.

  #5 큰 바위 재질 분열 — 한 화면에서 s20 이 굽는 바위는 무텍스처 회색 판인데
     옆의 Meshy 바위는 이끼 낀 돌결이었다. COL_ROCK 에 **절벽과 같은 돌결 타일
     트라이플래너**를 입혀 재질 언어를 하나로 합쳤다(7절 M_ROCK, 16절 ROCK_BUFS).
     곱수 실측 max 0.810 < 1 이라 화면 평균색 8a9199 는 안 움직인다.
     폐허 석재(cfd3cd)만 못 따라온다 — 곱수가 1.83 이라 baseColorFactor 상한 초과다
  #6 보스 마당 상공의 7각 슬래브 — 정체는 **DECO_ALTAR**(두 겹 8각 제단)였다.
     실제로는 안 떠 있었고(게임 안 실측: 판이 먹는 화면 높이 NDC 0.438 중 두께는
     0.030) 지면에 붙은 0.26m 짜리 낮은 단이었다. 그래도 떠 보인 이유는
     정다각형 + 접지 그늘 없음 + 맵에 없는 색 셋이다. **뺐다**(11절).
     "여기가 보스 자리"는 15절 바닥 얼룩으로만 남긴다
  S7 절벽이 아직 평평하다 — 단은 있는데 턱이 0.13m(화면 3px)라 실루엣이 못 읽었다.
     턱 0.42m(3.2배) · 단 밝기 0.50~1.00(아랫도리 0.70) · 마루를 블록 단위로
     들쭉날쭉하게(9절 RIDGE_*). 정점마다 흔들면 꼭대기에 방사 빛줄기가 생기는
     v86 함정은 "블록 안에서는 높이가 같다"로 피했다
  S8 개울이 파란 직사각 상자 — 수면을 물칸 사각형 판에서 **중심선 리본**으로 갈아
     엎었다(10절). 사행 중심선 · 안쪽으로만 파는 들쭉날쭉 기슭 · 여울목 쪽 끝단은
     4분타원 코 + 자갈톱 · 절벽 쪽 끝단은 바위 밑으로 0.5m 밀어 넣기.
     바닥의 기슭 띠·안쪽 그늘도 같은 얼룩으로 흔들었다(15절)
────────────────────────────────────────────────────────────────
★v69. rock·crag·thicket·tree·bush 5종은 **이 glb 에서 빠졌다.**
   Meshy 상세 모델로 갈아끼웠는데(blender/s22_props.py -> web/props/<종류>.glb)
   643개를 여기서 구우면 삼각형이 수십만이 된다. 배치만 level1.json 의 props[] 로
   내보내고 게임(web/props.js)이 InstancedMesh 로 심는다.
   ★콜라이더는 아래 emit_prop_colliders() 가 **그대로** 계산한다. 모양이 아니라
     배치 테이블 + 종류 규격에서 나오기 때문에 충돌은 한 칸도 안 바뀐다.
────────────────────────────────────────────────────────────────
★ 프롭은 배치(테이블)와 모양(함수)을 분리했다.
   나중에 Meshy 로 만든 상세 에셋(바위·나무·폐허)으로 갈아끼울 때
   PROP_KINDS[종류]["build"] 함수 자리에 **외부 glb 를 임포트해 배치하는 코드만**
   끼우면 된다. 배치 테이블(PROPS)과 콜라이더 규격(PROP_KINDS[...]["col"])은
   모양과 무관하게 유지되므로 충돌이 안 깨진다.
   - "어디에 무엇이 몇 개"  = PROPS  (레이아웃에서 생성)
   - "그게 어떻게 생겼나"   = build 함수 (교체 대상)
   - "무엇을 막나"          = col 규격 (모양이 아니라 종류가 정한다)
   종류는 12개로 묶었다. 종류가 적을수록 나중에 만들 에셋이 적다.
────────────────────────────────────────────────────────────────

★ 이 파일에서 조정할 값은 CELL 하나다.
   CELL 을 바꾸면 맵 전체가 그 비율로 커지거나 작아진다. GRID 를 바꾸려면 아래
   레이아웃(칸 좌표)을 같이 고쳐야 한다.

★ 좌표계 함정
  - 블렌더는 Z 가 위다. glTF 는 export_yup=True 로 내보내므로 three.js 에서는
    Y 가 위가 된다.  three.x = blender.x / three.y = blender.z / three.z = -blender.y
  - 그래서 이 스크립트는 **게임 좌표(gx, gz, y)** 로만 배치를 적고,
    블렌더로 넣을 때만 (bx, by, bz) = (gx, -gz, y) 로 바꾼다.
    level1.json 에 적히는 숫자는 전부 three.js 좌표다.

★ 텍스처 함정
  - 익스포터에는 해상도 옵션이 없다. 처음부터 2048 로 만들고 JPEG q90 으로 굽는다.
    (4096 PNG 로 나갔다가 캐릭터 glb 가 25MB 가 된 적이 있다)

★ 셰이더 함정
  - 노드로 짠 셀 셰이더는 glTF 로 안 나간다. 재질은 전부 Principled BSDF 로만.

★ 충돌 함정
  - 게임(web/level.js)은 **메시를 파싱하지 않는다.** level1.json 의 colliders[] 에
    적힌 축정렬 박스와 원만 본다. 그래서 캐노피·가지처럼 밑을 지나가야 하는 건
    COL_ 이 아닌 버퍼(DECO_/CANOPY_)에 넣는다. 이름 규칙:
      COL_*  = 막는다 (colliders[] 와 1:1)
      BUSH_* = 숨는 곳. 통과 가능, 콜라이더 없음
      DECO_/CANOPY_/WATER_/FLOOR = 안 막는다
"""

import bpy
import os
import json
import math
import random
import struct
import zlib
import numpy as np

# ★기본 시작 파일에는 Cube/Camera/Light 가 들어 있다. 안 지우면 glb 안에
#   정체불명의 Cube 가 같이 나간다(첫 실행에서 실제로 나갔다).
bpy.ops.wm.read_homefile(use_empty=True)

ROOT = "/Users/lbj/Documents/gameproject"
OUT_GLB = os.path.join(ROOT, "web", "level1.glb")
OUT_JSON = os.path.join(ROOT, "web", "level1.json")
# ★굽는 도중에 다른 사람이 web/level1.glb 를 읽으면 반쪽짜리 파일을 받는다.
#   옆에 _tmp 로 다 쓴 뒤 os.replace 로 갈아끼운다(같은 파일시스템 rename 은 원자적이다).
TMP_GLB = os.path.join(ROOT, "web", "level1_tmp.glb")
TMP_JSON = os.path.join(ROOT, "web", "level1_tmp.json")
TMP = os.environ.get("TMPDIR_LEVEL") or "/tmp"

# ─────────────────────────────────────────────────────────────
# 1) 치수 상수
# ─────────────────────────────────────────────────────────────
CHAR_H = 1.75         # 캐릭터 키 (main.js CHAR_CFG.slayer.h). 모든 치수를 이걸로 잰다

CELL = 3.2            # 칸 한 변(m). 1칸 통로 = 3.2m = 캐릭터 키의 1.83배
GRID = 30             # 칸 수. 30 x 3.2 = 96m 정사각
SIZE = CELL * GRID    # 96.0
HALF = SIZE / 2.0     # 48.0

FLOOR_Y = 0.02        # 바닥 높이. 캐릭터 발이 2cm 잠긴다

# 막는 지형의 기준 높이. 캐릭터 1.75 보다 확실히 높아야 시야가 끊긴다.
# 담장(2.0)보다 올린 이유: 자연물은 윤곽이 들쭉날쭉해서 같은 높이면 틈으로 다 보인다.
WALL_H = 2.6
CLIFF_H = 4.0         # 외곽 절벽. 맵 밖으로 못 나가게 + 실루엣으로 경계를 박는다
KNOLL_H = 3.4         # 마당 한가운데 바위 언덕(옛 요사채 자리)

# ★너덜지대. 막는 덩어리의 절반은 이 높이로 둔다.
#   무릎(0.6)보다 훨씬 높아 넘어갈 수는 없는데 캐릭터 키(1.75)보다는 낮아서
#   **건너편이 그대로 보인다.** "몸은 못 지나가는데 눈은 지나간다"가 개방감을 만든다.
LOW_H = 1.45

# 콜라이더를 칸 경계에서 얼마나 안으로 넣는가. 통로가 협곡처럼 안 보이게 하는 값이고,
# 자연물은 윤곽이 둥글어서 이 값보다 살짝 삐져나온다(스쳐도 어색하지 않은 범위).
WALL_INSET = 0.34

# 막는 칸을 채우는 프롭 밀도(칸당). 삼각형 예산의 대부분이 여기서 나간다.
# ★v67 에서 막는 칸이 244 -> 88 로 줄어서 칸당 밀도를 올릴 여유가 생겼다.
#   덩어리 하나하나가 성기면 "지형"이 아니라 "바위 세 개"로 보인다.
WALL_PROP_PER_CELL = 2.60


# ─────────────────────────────────────────────────────────────
# 2) 좌표 변환
# ─────────────────────────────────────────────────────────────
def gx_of(c):
    """칸 인덱스 c(0..GRID-1)의 중심 게임 X"""
    return -HALF + (c + 0.5) * CELL


def gz_of(r):
    """칸 인덱스 r(0..GRID-1)의 중심 게임 Z. r 이 커지면 남쪽(+Z)이다."""
    return -HALF + (r + 0.5) * CELL


def cell_of(gx, gz):
    return (int((gx + HALF) / CELL), int((gz + HALF) / CELL))


# ─────────────────────────────────────────────────────────────
# 3) 레이아웃 (칸 좌표)
# ─────────────────────────────────────────────────────────────
# ★전제가 뒤집혔다. 예전에는 꽉 막힌 판에서 통로를 파냈고(그래서 1칸 협곡이 널렸다),
#   지금은 **전부 열린 초원**에서 시작해 막는 덩어리를 띄엄띄엄 얹는다.
#   덩어리는 최대 3칸이고 덩어리끼리 최소 2칸(6.4m) 띄운다 = 모든 통로가 6.4m 이상.
W_, PATH, OPEN, BOSSF, BLD = "#", "-", ".", "X", "H"

grid = [[OPEN for _ in range(GRID)] for _ in range(GRID)]


def is_outer(c, r):
    return c <= 1 or c >= GRID - 2 or r <= 1 or r >= GRID - 2


def carve(c0, r0, c1, r1, kind):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if 0 <= r < GRID and 0 <= c < GRID:
                grid[r][c] = kind


def road(c0, r0, c1, r1):
    """흙길 색만 칠한다. 지형이 아니라 **바닥색**이라 막는 칸은 건드리지 않는다.
    넓은 초원에서 '어디로 가야 하나'를 알려주는 게 이 색의 유일한 역할이다."""
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if 0 <= r < GRID and 0 <= c < GRID and grid[r][c] == OPEN:
                grid[r][c] = PATH


# ── 외곽 절벽 링(탑의 가장자리). 2칸 = 6.4m 두께 ─────────────
for r in range(GRID):
    for c in range(GRID):
        if is_outer(c, r):
            grid[r][c] = W_

# ── 입구·탈출구. 절벽을 가르는 틈은 전부 3칸(9.6m) 이상 ──────
carve(3, 28, 5, 29, PATH)     # SPAWN_1 남서
carve(24, 28, 26, 29, PATH)   # SPAWN_2 남동
carve(0, 13, 1, 15, PATH)     # SPAWN_3 서
carve(28, 13, 29, 15, PATH)   # SPAWN_4 동
carve(13, 28, 16, 29, PATH)   # EXIT_1 남 (4칸 = 12.8m)
carve(28, 20, 29, 22, PATH)   # EXIT_2 동

# ── 보스 마당. 14x7칸 = 44.8 x 22.4m. 사방이 트인 바위 분지 ──
BOSS_ARENA = (8, 3, 21, 9)
carve(*BOSS_ARENA, BOSSF)

# ── 개울. 맵을 동서로 가르고 여울목 세 곳으로만 건넌다 ───────
# ★개울은 이 맵에서 제일 중요한 "막지만 안 가리는" 장치다. 수면이 바닥보다 1cm 위라
#   건너편이 통째로 보이는데 몸은 못 지나간다. 직선으로 그으면 담장처럼 보여서
#   사인파로 굽혀 r10~r12 사이를 흐르게 했다.
FORD_COLS = (5, 6, 14, 15, 23, 24)     # 여울목. 두 칸씩 세 곳 = 폭 6.4m


def stream_row(c):
    return 11 + int(round(1.2 * math.sin((c - 2) * 0.30)))


WATER_CELLS = set()
# ★v89. 여울목이 끊어 놓은 **구간** 목록도 같이 뽑는다. [[ (열, 행), ... ], ...]
#   10절의 수면 리본이 이 중심선을 따라 흐른다. 물칸 집합과 같은 반복문에서 나오므로
#   둘이 어긋날 수가 없다(따로 만들면 언젠가 리본이 물칸 밖으로 샌다).
STREAM_SEGS = []
_seg = []
_prev = None
for c in range(2, GRID - 2):
    if c in FORD_COLS:
        _prev = None                      # 여울목에서 개울이 끊긴다
        if _seg:
            STREAM_SEGS.append(_seg)
            _seg = []
        continue
    _rr = stream_row(c)
    # ★열이 바뀔 때 사이를 채워야 4방향으로 이어진다. 안 채우면 대각선 틈으로 샌다
    for r in ([_rr] if _prev is None else range(min(_prev, _rr), max(_prev, _rr) + 1)):
        WATER_CELLS.add((c, r))
    _seg.append((c, _rr))
    _prev = _rr
if _seg:
    STREAM_SEGS.append(_seg)
for (c, r) in WATER_CELLS:
    grid[r][c] = W_
FORD_CELLS = set((c, stream_row(c)) for c in FORD_COLS)
for (c, r) in FORD_CELLS:
    grid[r][c] = PATH

# 여울목을 열 단위로 묶는다(붙어 있는 열이 한 곳). 세 곳이 나온다.
FORD_GROUPS = []
for c in sorted(FORD_COLS):
    if FORD_GROUPS and c == FORD_GROUPS[-1][-1] + 1:
        FORD_GROUPS[-1].append(c)
    else:
        FORD_GROUPS.append([c])

# ★v79. 여울목 통로는 맵에서 개울을 건널 수 있는 **유일한** 자리다.
#   막는 소품이 한 발짝만 들어와도 6.4m 짜리 문이 4m 로 줄고, 표식과 실제 틈이
#   어긋난다(실제로 바위 무더기 두 개가 서쪽·동쪽 여울목을 반쯤 막고 있었다).
#   격자 검사(walkable)로는 절대 안 잡힌다. 여울목 칸은 걸을 수 있는 칸이라서.
FORD_LANES_X = [(-HALF + min(g) * CELL, -HALF + (max(g) + 1) * CELL)
                for g in FORD_GROUPS]
FORD_LANE_Z = (-HALF + (min(r for (_, r) in WATER_CELLS) - 1) * CELL,
               -HALF + (max(r for (_, r) in WATER_CELLS) + 2) * CELL)


def ford_lane_clear(gx, gz, rad):
    """여울목 통로를 침범하면 False."""
    if not (FORD_LANE_Z[0] - rad < gz < FORD_LANE_Z[1] + rad):
        return True
    return all(not (x0 - rad - 0.4 < gx < x1 + rad + 0.4)
               for (x0, x1) in FORD_LANES_X)

# ── 막는 덩어리. ★연속 벽이 아니다 ──────────────────────────
# (c0, r0, c1, r1, 종류). 종류가 높이를 정한다.
#   crag    바위 절벽 덩어리 2.6m   - 시야를 끊는다
#   thicket 빽빽한 덤불 3.2m        - 시야를 끊는다
#   low     너덜지대 1.45m          - ★막지만 **건너편이 보인다**
# 절반을 low 로 둔 것이 이 맵의 개방감이다. 전부 2.6m 로 두면 다시 미로가 된다.
CLUMPS = [
    (7, 2, 7, 3, "crag"), (7, 8, 7, 9, "low"),          # 보스 마당 서쪽 어귀(사이 4칸)
    (22, 2, 22, 3, "crag"), (22, 8, 22, 9, "low"),      # 보스 마당 동쪽 어귀(사이 4칸)
    (4, 5, 4, 6, "thicket"), (25, 6, 25, 7, "low"),     # 북쪽 곁터
    (4, 15, 5, 16, "crag"), (9, 15, 10, 16, "low"),     # 개울 남쪽 첫 띠
    (19, 15, 20, 16, "thicket"), (24, 15, 25, 16, "low"),
    (6, 19, 7, 20, "low"), (22, 19, 23, 20, "crag"),    # 석탑 마당 좌우
    # ★v79. 남쪽 띠 바깥 두 덩어리를 지우지 않고 **서쪽·동쪽 길 옆으로 세워 눕혔다.**
    #   옛 자리(4,23)-(5,24) / (23,23)-(24,24) 는 스폰 정면 15m 한복판이라
    #   나가자마자 10m 앞에서 막혔다(QA #7). 새 자리는 한 칸 폭 x 세 칸 길이라
    #   남북 길을 따라 흐르는 돌등성이가 되고, 스폰에서 중앙으로 가는 대각선은 비었다.
    (4, 21, 4, 23, "low"), (10, 23, 12, 24, "thicket"),  # 남쪽 띠
    (17, 23, 18, 24, "low"), (25, 21, 25, 23, "crag"),
]
KNOLLS = [(10, 19, 11, 20), (18, 19, 19, 20)]   # 바위 언덕(BLD). 석탑 마당의 문설주

CLUMP_KIND = {}
for (c0, r0, c1, r1, kind) in CLUMPS:
    carve(c0, r0, c1, r1, W_)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            CLUMP_KIND[(c, r)] = kind
for (c0, r0, c1, r1) in KNOLLS:
    carve(c0, r0, c1, r1, BLD)

# ── 여울목 칠하는 범위 ★"어디로 건너는가"를 바닥색으로 못 박는다 ──
# ★v79. 여울목 칸만 칠하면 개울 폭(3.2m)짜리 점이라 멀리서 안 읽힌다.
#   건너는 방향(남북)으로 걸을 수 있는 칸 두 개까지 젖은 돌 색을 이어 붙여
#   개울을 가로지르는 창백한 띠로 만든다.
#   ★동서로는 절대 안 편다. 개울 남안을 따라 흙길이 지나가서 강변 전체가
#     여울목 색이 되면 "여기 아무 데나 건너도 된다"가 돼 버린다(옛 주석 참고).
FORD_PAINT = set(FORD_CELLS)
for (_fc, _fr) in sorted(FORD_CELLS):
    for _step in (-1, 1):
        for _k in range(1, 3):
            _rr = _fr + _step * _k
            if not (0 <= _rr < GRID) or grid[_rr][_fc] in (W_, BLD):
                break
            FORD_PAINT.add((_fc, _rr))

# ── 흙길(바닥색). 넓은 초원에 방향을 준다 ────────────────────
road(14, 10, 15, 27)      # 중앙 대로. 여울목에서 EXIT_1 까지 (걷는 폭은 12.8m)
road(2, 13, 27, 13)       # 개울 남안 동서 길
road(2, 16, 3, 27)        # 서쪽 남북 길
road(26, 16, 27, 27)      # 동쪽 남북 길
road(6, 5, 8, 6)          # 보스 서쪽 어귀
road(21, 5, 23, 6)        # 보스 동쪽 어귀
road(4, 26, 4, 27)        # SPAWN_1 진입
road(25, 26, 25, 27)      # SPAWN_2 진입
road(2, 14, 3, 14)        # SPAWN_3 진입
road(26, 14, 27, 14)      # SPAWN_4 진입
road(26, 21, 27, 21)      # EXIT_2 진입

# ── 지점 (칸 좌표) ──────────────────────────────────────────
# ★v79. 스폰을 어귀에서 안쪽으로 물렸다(6.4~9.3m). 어귀 표식(선돌)은 절벽 틈에
#   그대로 두고 사람만 들어왔다. 이유 두 가지.
#   (1) 옛 자리는 맵 경계에서 4.8m 뿐이었다. 고정 카메라(pitch 0.86 / dist 24 /
#       lead 1.25 / fov 24)는 플레이어 **뒤 3.6m** 까지, 가로로 가까운 줄에서
#       ±8.4m·먼 줄에서 ±12.0m 를 본다. 그 범위가 맵 밖으로 나가면서 화면 아래·옆이
#       텍스처 없는 회색으로 찍혔다.
#   (2) 정면 15m 안에 바위 무더기가 있어서 첫 15초를 우회에 썼다.
#   ★소수점 자리(4.6 / 24.4 / 13.35)는 눈대중이 아니다. 아래 SPAWN_LANE 검사가
#     통과하는 지점을 골라 박은 값이다. 옮길 때는 검사부터 다시 돌려라.
SPAWN_CELLS = [(4.6, 26.0), (24.4, 26.0), (3.0, 13.35), (26.0, 13.35)]
EXIT_CELLS = [(14.5, 28.0), (28.9, 22)]
BOSS_CELL = (14.5, 6.0)          # 보스 마당 한가운데


def yaw_to_center(gx, gz):
    """three.js 기준 회전 Y. main.js 는 targetYaw = atan2(move.x, move.z) 라
    yaw 0 이 +Z 를 본다. 맵 중심을 보게 돌린다."""
    return math.atan2(-gx, -gz)


# ── 스폰 정면 통로 ★"첫 15초"가 여기서 결정된다 ─────────────
# yaw 방향으로 15m, 폭 4.4m. 이 안에는 콜라이더가 하나도 없어야 한다.
# 격자 지형은 위 레이아웃이 이미 비워 놨고, 소품은 lane_clear() 로 막는다.
# 마지막에 자기 검증이 콜라이더 전부를 넣고 다시 잰다(거기가 진짜 기준이다).
SPAWN_LANE_LEN = 15.0
SPAWN_LANE_HALF = 2.2
SPAWN_LANES = []
for (_sc, _sr) in SPAWN_CELLS:
    _sx, _sz = gx_of(_sc), gz_of(_sr)
    _sy = yaw_to_center(_sx, _sz)
    SPAWN_LANES.append((_sx, _sz, math.sin(_sy), math.cos(_sy)))


def lane_clear(gx, gz, rad):
    """스폰 정면 통로를 침범하면 False. 막는 소품은 전부 이걸 통과해야 한다."""
    for (sx_, sz_, dx_, dz_) in SPAWN_LANES:
        t = (gx - sx_) * dx_ + (gz - sz_) * dz_
        if t < -rad or t > SPAWN_LANE_LEN + rad:
            continue
        if abs(-(gx - sx_) * dz_ + (gz - sz_) * dx_) < SPAWN_LANE_HALF + rad:
            return False
    return True


# ── 어귀 표식이 설 자리 ★배치보다 먼저 안다 ─────────────────
# ★terr_07_crag: 크래그를 관통해 흰 석주가 박혀 있었다. 원인은 순서다. 막는 칸을
#   자연물로 채우는 절이 문설주보다 먼저 돌아서, 채우는 쪽이 문설주 자리를 몰랐다.
#   표(GATES)를 여기로 끌어올려 **자리를 먼저 확정**하고 채우는 쪽이 피하게 한다.
# ★d(두 짝 사이 반간격)는 어귀 폭에 맞춰 따로 준다. 하나로 고정하면 12.8m 짜리
#   대로 한가운데에 문이 옹색하게 서거나 6.4m 짜리 어귀를 문설주가 막는다.
#   "절벽에 딱 붙이는" 값으로 잡는다(어귀 폭의 절반에서 문설주 반지름을 뺀 만큼).
# ★v86. 다섯 번째 값 cord = 붉은 끈을 감을 것인가.
#   부수 과제("나침반이 안 보인다"의 맵 쪽 지원): 화면 UI 말고 **지형**이 방향을
#   말해야 한다. 보스 마당으로 들어가는 어귀 세 곳(남·서·동)의 선돌에만 붉은 끈을
#   감는다. 맵에서 붉은색은 보스 결계 원 하나뿐이라, 같은 붉은색이 어귀에 있으면
#   "저 문 너머가 그 자리"가 설명 없이 붙는다.
#   ★스폰·탈출 어귀에는 안 감는다. 여섯 어귀가 다 붉으면 단서가 아니라 장식이 된다.
GATES = [
    (gx_of(4), gz_of(28.0), False, CELL * 1.25, False),   # SPAWN_1 남서 어귀 (3칸=9.6m)
    (gx_of(25), gz_of(28.0), False, CELL * 1.25, False),  # SPAWN_2 남동 어귀 (3칸)
    (gx_of(2.0), gz_of(14), True, CELL * 1.25, False),    # SPAWN_3 서 어귀 (3칸)
    (gx_of(27.0), gz_of(14), True, CELL * 1.25, False),   # SPAWN_4 동 어귀 (3칸)
    (gx_of(14.5), gz_of(28.0), False, CELL * 1.50, False),  # EXIT_1 남 (4칸=12.8m)
    (gx_of(27.0), gz_of(21), True, CELL * 1.25, False),   # EXIT_2 동 (3칸)
    (gx_of(14.5), gz_of(9.0), False, CELL * 1.50, True),  # ★보스 남쪽 어귀(여울목 위)
    (gx_of(7), gz_of(5.5), True, CELL * 1.50, True),      # ★보스 서쪽 어귀 (4칸)
    (gx_of(22), gz_of(5.5), True, CELL * 1.50, True),     # ★보스 동쪽 어귀 (4칸)
]
GATE_POSTS = []          # (x, z). 문설주가 설 자리
for (_gx, _gz, _ax, _gd, _cd) in GATES:
    for _s in (-1, 1):
        GATE_POSTS.append((_gx + (_gd * _s if not _ax else 0),
                           _gz + (_gd * _s if _ax else 0)))


def gate_post_clear(gx, gz, rad):
    """문설주(반지름 0.62, 높이 4.6m) 자리를 프롭이 먹지 않게.

    ★여유를 2.6m 나 주는 이유가 있다. 3D 로는 안 겹쳐도(옛 최단거리 3.24m)
      pitch 0.86 탑다운에서는 4.6m 짜리 문설주의 아랫도리가 2.6~3.4m 짜리 크래그
      뒤로 숨고 윗도리만 솟아서 **바위를 뚫고 나온 석주**로 보인다
      (QA terr_07_crag 이 그 그림이다). 화면에서 안 겹치려면 발치를 벌려야 한다."""
    return all(math.hypot(gx - px_, gz - pz_) > rad + 2.60
               for (px_, pz_) in GATE_POSTS)

# 요괴 무리 자리. AGGRO 7.0 + 무리 반경 2.6 이라 중심끼리 17m 이상 떨어뜨린다.
# ★수풀에서도 8m 이상 띄운다. 수풀에 들어가자마자 무리가 붙으면 은신이 성립하지 않는다.
MOB_CELLS = [
    (2.5, 7.0),      # 북서 곁터
    (26.5, 3.0),     # 북동 곁터
    (9.5, 7.0),      # 보스 마당 서쪽 끝
    (19.5, 7.0),     # 보스 마당 동쪽 끝
    # ★v79. 아래 두 무리는 보스 -> EXIT_1 직선(x=0) **정확히 위**에 있었다.
    #   증표를 들고 뛰는 길에 정면 충돌이 강제되면 그건 긴장이 아니라 통행세다.
    #   3.2~3.5m 씩 좌우로 비켜 세웠다. 무리는 여전히 대로 사정거리 안이라
    #   "돌아갈지 뚫을지"가 선택이 된다(둘을 반대쪽으로 밀어 길이 지그재그가 된다).
    (15.6, 15.5),    # 석탑 마당 북쪽. 대로 동쪽 3.5m
    (2.5, 18.0),     # 서쪽 초원
    (26.5, 18.0),    # 동쪽 초원
    (8.0, 26.5),     # 남서 초원 (SPAWN_1 에서 11.0m. 첫 교전)
    (21.0, 26.5),    # 남동 초원
    (13.5, 26.0),    # 남쪽 대로 끝. 대로 서쪽 3.2m
]

# 수풀 구역. ★열린 맵일수록 수풀 자리가 전부다.
#   여울목 6곳 / 보스 어귀 4곳 / 덩어리 사이 길목 5곳 / 스폰 첫 은신처 1곳.
#   넓은 초원 한가운데는 하나도 없다(아무도 안 지나가서 쓸모가 없다).
# ★v86 (QA S8 "수풀이 도하 지점을 덮는다", 201_ford_west).
#   서쪽 여울목 네 칸이 도하 차선(FORD_LANES_X x FORD_LANE_Z) **한복판**이었다.
#   위에서 보면 6.4m 짜리 문이 통째로 밝은 연두 덩어리에 묻혀서, 이 맵에서
#   개울을 건널 수 있는 유일한 세 자리 중 하나가 안 보였다. 동쪽도 같은 흠이었다.
#   네 곳을 차선 **옆**으로 비켜 세웠다(옮긴 좌표는 각 줄 주석).
#   ★규칙으로 못 박았다: 수풀 칸 사각형은 도하 차선과 겹치면 안 된다.
#     바로 아래 검사가 겹침 면적을 재서 한 칸이라도 물리면 소리를 지른다.
BUSH_CELLS = [
    [(7, 11), (8, 11)],      # 서쪽 여울목 북안 ★차선 옆(옛 (5,11)(6,11) = 차선 위)
    [(7, 13), (8, 13)],      # 서쪽 여울목 남안 ★차선 옆(옛 (5,13)(6,13) = 차선 위)
    [(13, 12), (13, 13)],    # 중앙 여울목 남서 (보스로 가는 대로 옆). 차선에 안 닿는다
    [(16, 12), (16, 13)],    # 중앙 여울목 남동. 차선에 안 닿는다
    [(21, 13), (22, 13)],    # 동쪽 여울목 남안 ★차선 옆(옛 (23,13)(24,13) = 차선 위)
    [(25, 9), (26, 9)],      # 동쪽 여울목 북안 ★차선 옆(옛 (23,9)(24,9) = 차선 위)
    [(6, 3), (6, 4)],        # 보스 서쪽 어귀 앞
    [(8, 4), (8, 5)],        # 보스 서쪽 어귀 안(마당 쪽)
    [(21, 4), (21, 5)],      # 보스 동쪽 어귀 안
    [(23, 6), (23, 7)],      # 보스 동쪽 어귀 앞
    # ★v79. 아래 세 곳을 무리 코앞으로 옮겼다(8.0 ~ 8.6m). 어그로 7m 밖이면서
    #   무리가 몇인지 어느 쪽을 보는지가 읽히는 거리다. 옛 자리(첫 띠 좌우 길목,
    #   남서 스폰 앞)는 전부 무리에서 13m 넘어 "캠프 몰래 지나가기"에 쓸 데가 없었다.
    #   ★개별 요괴 자리(spot)가 수풀 사각형을 0.8m 이상 여유로 피하는지는
    #     아래 자기 검증이 spot 단위로 다시 잰다. 무리 중심만 보면 또 틀린다.
    [(5, 18), (5, 19)],      # MOB_6 서쪽 캠프 8.0m. 서쪽 길과 너덜 사이 길목
    [(24, 18), (24, 19)],    # MOB_7 동쪽 캠프 8.0m. 동쪽 길과 바위 사이 길목
    [(8, 19), (8, 20)],      # 석탑 마당 서쪽 길목
    [(21, 19), (21, 20)],    # 석탑 마당 동쪽 길목
    [(14, 22), (15, 22)],    # 중앙 대로 남쪽 길목
    [(8, 24), (9, 24)],      # MOB_8 남서 캠프 8.0m. 남쪽 띠가 뚫린 자리 한가운데
    # ★v94. 손맛 심사관 실측 "쓸만한 수풀이 캠프에서 21유닛". 정찰로 자리를 특정했다.
    #   캠프 열 곳 중 8~12m 안에 수풀이 있는 곳이 **한 곳(MOB_10, 11.2m)뿐**이었다.
    #   여섯 곳은 5.8~6.4m 로 오히려 너무 붙어 있고(들어가는 순간 이미 교전),
    #   세 곳은 12.5 / 12.5 / 19.2m 로 멀었다. 그 셋에 하나씩 신설한다.
    #   규칙 준수: ①수풀 안에 요괴 집을 두지 않는다(아래 spot 단위 검증이 다시 잰다)
    #             ②도하 표식·차선과 안 겹친다(위 겹침 검사가 잰다. 셋 다 개울에서 멀다)
    #   ★수풀은 콜라이더가 없다. 다만 BUSH_SET 이 엄폐 소품 배치에서 그 칸을 빼므로
    #     그 칸에 있던 잔돌·나무가 사라진다 = 콜라이더 diff 가 난다(0 이 아니다).
    [(20, 23), (20, 24)],    # MOB_9 남서 8.6m. 옛 19.2m -> 이 맵에서 제일 외로운 캠프였다
    [(5, 7), (5, 8)],        # MOB_1 동쪽 8.0m. 옛 12.5m
    [(24, 4), (24, 5)],      # MOB_2 서쪽 8.6m. 옛 12.5m
]

for reg in BUSH_CELLS:
    for (c, r) in reg:
        if grid[r][c] in (W_, BLD):
            print("[경고] 수풀이 막힌 칸에 있다: c%d r%d" % (c, r))

# ── ★v86 규칙: 수풀 사각형 x 도하 차선 겹침 금지 (QA S8) ──────
# 여울목은 개울을 건널 수 있는 유일한 자리다. 수풀은 안 막지만 **가린다.**
# 위에서 봤을 때 1.5m 짜리 밝은 연두 덩어리가 문을 덮으면 문이 없는 것과 같다.
# 막는 소품은 이미 ford_lane_clear() 로 걸러지는데(그건 통행 폭 문제였다),
# 수풀은 콜라이더가 없어서 그 그물을 통째로 빠져나갔다. 여기서 따로 막는다.
# ★여유 폭이 아니라 **겹침 면적**을 잰다. 차선 옆에 딱 붙는 건 허용한다
#   (중앙 여울목 좌우 수풀이 그 설계다. 옆에 붙어야 건너는 자리를 지켜볼 수 있다).
_bf_bad, _bf_gap = [], 1e9
for _bi, _reg in enumerate(BUSH_CELLS):
    for (c, r) in _reg:
        _x0, _x1 = -HALF + c * CELL, -HALF + (c + 1) * CELL
        _z0, _z1 = -HALF + r * CELL, -HALF + (r + 1) * CELL
        _ovz = min(_z1, FORD_LANE_Z[1]) - max(_z0, FORD_LANE_Z[0])
        for (_lx0, _lx1) in FORD_LANES_X:
            _ovx = min(_x1, _lx1) - max(_x0, _lx0)
            if _ovx > 1e-6 and _ovz > 1e-6:
                _bf_bad.append("BUSH_%02d 칸(%d,%d) 이 도하 차선을 %.1f x %.1f m 덮는다"
                               % (_bi + 1, c, r, _ovx, _ovz))
            elif _ovz > 1e-6:
                _bf_gap = min(_bf_gap, -_ovx)      # 차선 옆 여유(0 이면 딱 붙음)
print("[검증] 수풀 x 도하 차선 겹침 %s (차선 %d곳. 차선 z 대역에 걸친 수풀의 "
      "최소 옆여유 %.1fm)"
      % (_bf_bad if _bf_bad else "0건", len(FORD_LANES_X),
         0.0 if _bf_gap > 1e8 else max(0.0, _bf_gap)))
if _bf_bad:
    print("[경고] 도하 지점이 수풀에 묻힌다. BUSH_CELLS 를 차선 옆으로 비켜라")

BUSH_SET = set()
for reg in BUSH_CELLS:
    for cr in reg:
        BUSH_SET.add(cr)

# ★예전에 밟은 흠 두 개를 여기서 막는다.
#   (1) 요괴 자리가 수풀 칸 안에 들어가 있었다(BUSH_10)
#   (2) 요괴 자리와 수풀이 4.5m 밖에 안 떨어져 있었다(BUSH_09)
_mb = 1e9
for _bi, _reg in enumerate(BUSH_CELLS):
    for (c, r) in _reg:
        for _mi, (mc, mr) in enumerate(MOB_CELLS):
            if (int(mc), int(mr)) == (c, r):
                print("[경고] MOB_%d 가 BUSH_%02d 칸 안에 있다" % (_mi + 1, _bi + 1))
            _mb = min(_mb, math.hypot((gx_of(c) - gx_of(mc)), (gz_of(r) - gz_of(mr))))
# ★하한 6.5m. 어그로 7.0 에서 무리 반경을 감안한 값이다. 이보다 붙으면 수풀에
#   들어가는 동작 자체가 이미 교전이라 은신이 성립하지 않는다.
BUSH_MOB_MIN = 6.5
print("[수풀] %d곳 / 무리와의 최소 거리 %.1fm (하한 %.1fm) %s"
      % (len(BUSH_CELLS), _mb, BUSH_MOB_MIN,
         "" if _mb >= BUSH_MOB_MIN else "★하한 위반"))
# ★v79. 수풀 하나하나가 "제일 가까운 무리에서 몇 m 인가"를 찍는다. 전부 9m 밖이면
#   은신은 있으나 마나다(QA #3). 7.5~9m 짜리가 두세 곳 있어야 어그로(7m) 밖에서
#   무리를 보고 돌아갈지 뚫을지 정할 수 있다.
_near_cnt = 0
for _bi, _reg in enumerate(BUSH_CELLS):
    _bcx = sum(gx_of(c) for (c, r) in _reg) / len(_reg)
    _bcz = sum(gz_of(r) for (c, r) in _reg) / len(_reg)
    _bd, _bm = 1e9, ""
    for _mi, (mc, mr) in enumerate(MOB_CELLS):
        _d = math.hypot(_bcx - gx_of(mc), _bcz - gz_of(mr))
        if _d < _bd:
            _bd, _bm = _d, "MOB_%d" % (_mi + 1)
    if 7.5 <= _bd <= 9.5:
        _near_cnt += 1
    print("   BUSH_%02d (%6.1f,%6.1f) 최근접 %-6s %5.1fm%s"
          % (_bi + 1, _bcx, _bcz, _bm, _bd, "  <- 관찰 사거리" if 7.5 <= _bd <= 9.5 else ""))
print("[수풀] 무리 관찰 사거리(7.5~9.5m) 안에 있는 곳 %d 곳" % _near_cnt)


# ─────────────────────────────────────────────────────────────
# 5) 연결성 검사 (막힌 구역이 있으면 여기서 잡는다)
# ─────────────────────────────────────────────────────────────
def flood(sc, sr):
    seen = set()
    stack = [(sc, sr)]
    while stack:
        c, r = stack.pop()
        if (c, r) in seen:
            continue
        if not (0 <= c < GRID and 0 <= r < GRID):
            continue
        if grid[r][c] in (W_, BLD):
            continue
        seen.add((c, r))
        stack += [(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)]
    return seen


reach = flood(4, 27)   # 남서 터에서 출발
walk_total = sum(1 for r in range(GRID) for c in range(GRID) if grid[r][c] not in (W_, BLD))
print("[연결성] 걸을 수 있는 칸 %d / 도달 %d" % (walk_total, len(reach)))
_bad = []
for i, (c, r) in enumerate(SPAWN_CELLS):
    if (int(c), int(r)) not in reach and (int(round(c)), int(round(r))) not in reach:
        _bad.append("SPAWN_%d" % (i + 1))
for i, (c, r) in enumerate(MOB_CELLS):
    if (int(c), int(r)) not in reach:
        _bad.append("MOB_%d" % (i + 1))
for i, (c, r) in enumerate(EXIT_CELLS):
    if (int(c), int(r)) not in reach and (int(round(c)), int(round(r))) not in reach:
        _bad.append("EXIT_%d" % (i + 1))
if (int(BOSS_CELL[0]), int(BOSS_CELL[1])) not in reach:
    _bad.append("BOSS")
print("[연결성] 못 닿는 지점: %s" % (_bad if _bad else "없음"))

_mn = 1e9
for i in range(len(MOB_CELLS)):
    for j in range(i + 1, len(MOB_CELLS)):
        a, b = MOB_CELLS[i], MOB_CELLS[j]
        d = math.hypot((a[0] - b[0]) * CELL, (a[1] - b[1]) * CELL)
        _mn = min(_mn, d)
print("[무리] %d곳, 최소 간격 %.1fm (17.0 이상이어야 옆 무리가 안 딸려온다)"
      % (len(MOB_CELLS), _mn))


def walk_dist(sc_, sr_):
    """격자 위 다익스트라(대각 허용, 모서리 자르기 금지). 실제 걷는 거리."""
    import heapq
    D = [[float("inf")] * GRID for _ in range(GRID)]
    D[sr_][sc_] = 0.0
    pq = [(0.0, sc_, sr_)]
    while pq:
        d, c, r = heapq.heappop(pq)
        if d > D[r][c]:
            continue
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                nc, nr = c + dc, r + dr
                if not (0 <= nc < GRID and 0 <= nr < GRID):
                    continue
                if grid[nr][nc] in (W_, BLD):
                    continue
                if dc and dr and (grid[r][nc] in (W_, BLD) or grid[nr][c] in (W_, BLD)):
                    continue
                w = CELL * (1.41421 if dc and dr else 1.0)
                if d + w < D[nr][nc]:
                    D[nr][nc] = d + w
                    heapq.heappush(pq, (d + w, nc, nr))
    return D


RUN_SPD = 3.20   # main.js CHAR_CFG.slayer.run.spd
_bc, _br = int(BOSS_CELL[0]), int(BOSS_CELL[1])
_Dboss = walk_dist(_bc, _br)
print("[경로] 달리기 3.20 m/s 기준")
for i, (c, r) in enumerate(SPAWN_CELLS):
    c, r = min(GRID - 1, int(round(c))), min(GRID - 1, int(round(r)))
    if grid[r][c] in (W_, BLD):
        c = max(1, min(GRID - 2, c))
    d = _Dboss[r][c]
    print("   SPAWN_%d -> BOSS  %6.1f m  %4.1f초" % (i + 1, d, d / RUN_SPD))
for i, (c, r) in enumerate(EXIT_CELLS):
    c, r = min(GRID - 1, int(round(c))), min(GRID - 1, int(round(r)))
    d = _Dboss[r][c]
    print("   BOSS -> EXIT_%d   %6.1f m  %4.1f초" % (i + 1, d, d / RUN_SPD))


# ─────────────────────────────────────────────────────────────
# 6) 지오메트리 버퍼 + 원시 도형
# ─────────────────────────────────────────────────────────────
def srgb_to_linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)


class Buf:
    """정점/면을 파이썬 리스트로 모아 두었다가 한 번에 메시로 만든다.

    ★v86. c[] 는 정점당 **명암 곱수** 하나다(회색이라 값 하나면 된다).
      비어 있으면 정점색을 안 만들고, 일부만 채워져 있으면 나머지는 1.0 으로 채운다.
      glTF COLOR_0 으로 나가서 three.js 가 베이스컬러에 곱한다. 이게 절벽의
      "단 차이 음영"을 재질 하나로 내는 장치다(재질을 단마다 쪼개면 드로우콜이 는다).

    ★v94. uv[] 신설 — **정점당** UV 다(면당이 아니다). 채워 두면 make_obj 가
      uvfn 대신 이걸 쓴다. 수면이 "흐름 좌표 u / 기슭까지의 거리 v" 를 실어
      보내는 통로다. 왜 정점색이 아니라 UV 인지는 add_stream_ribbon 주석에 적었다."""

    def __init__(self, name, mat):
        self.name = name
        self.mat = mat
        self.v = []
        self.f = []
        self.c = []
        self.uv = []
        self.shade_mean = None

    def tri_count(self):
        return sum(len(f) - 2 for f in self.f)


def bpos(gx, gz, y):
    """게임 좌표 -> 블렌더 좌표"""
    return (gx, -gz, y)


def add_box(buf, gx, gz, y0, y1, hx, hz, rot=0.0):
    """축정렬(또는 rot 만큼 돌린) 상자. 12삼각형."""
    bx, by = gx, -gz
    cs, sn = math.cos(rot), math.sin(rot)
    corners = [(-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)]
    base = len(buf.v)
    for z in (y0, y1):
        for (dx, dy) in corners:
            rx = dx * cs - dy * sn
            ry = dx * sn + dy * cs
            buf.v.append((bx + rx, by + ry, z))
    b = base
    buf.f += [
        (b + 0, b + 3, b + 2, b + 1),
        (b + 4, b + 5, b + 6, b + 7),
        (b + 0, b + 1, b + 5, b + 4),
        (b + 1, b + 2, b + 6, b + 5),
        (b + 2, b + 3, b + 7, b + 6),
        (b + 3, b + 0, b + 4, b + 7),
    ]


def add_prism(buf, gx, gz, y0, y1, r0, r1, n=6, phase=0.0, cap_bottom=False):
    """n각 원뿔대. 옆면 n쿼드 + 윗뚜껑. 삼각형 3n-2."""
    bx, by = gx, -gz
    base = len(buf.v)
    for (rr, zz) in ((r0, y0), (r1, y1)):
        for i in range(n):
            a = phase + i * 2 * math.pi / n
            buf.v.append((bx + math.cos(a) * rr, by + math.sin(a) * rr, zz))
    for i in range(n):
        j = (i + 1) % n
        buf.f.append((base + i, base + j, base + n + j, base + n + i))
    buf.f.append(tuple(base + n + i for i in range(n)))
    if cap_bottom:
        buf.f.append(tuple(base + i for i in range(n - 1, -1, -1)))


def add_dome(buf, gx, gz, y0, rx, rz, h, n=7, seed=0, squash=1.0):
    """덩어리(바위·수풀·수관). 꼭대기 1 + 중간링 n + 바닥링 n. 3n 삼각형.
    정점마다 흔들어서 실루엣이 기계적으로 안 보이게 한다(탑다운은 실루엣이 전부다).
    squash 를 올리면 중간링이 위로 올라가 각지고 뭉툭해진다(바위), 낮추면 둥글다(수풀)."""
    rnd_ = random.Random(seed)
    bx, by = gx, -gz
    base = len(buf.v)
    buf.v.append((bx + rnd_.uniform(-0.1, 0.1) * rx, by + rnd_.uniform(-0.1, 0.1) * rz, y0 + h))
    for ring, (kr, kh) in enumerate(((0.80, min(0.94, 0.62 * squash)), (1.0, 0.0))):
        for i in range(n):
            a = i * 2 * math.pi / n + rnd_.uniform(-0.14, 0.14)
            jr = kr * rnd_.uniform(0.78, 1.20)
            buf.v.append((bx + math.cos(a) * rx * jr,
                          by + math.sin(a) * rz * jr,
                          y0 + h * kh * rnd_.uniform(0.85, 1.15)))
    top = base
    r1 = base + 1
    r2 = base + 1 + n
    for i in range(n):
        j = (i + 1) % n
        buf.f.append((top, r1 + i, r1 + j))
        buf.f.append((r1 + i, r2 + i, r2 + j, r1 + j))


def add_pyramid(buf, gx, gz, y0, hx, hz, h, ov=0.0):
    """사모지붕(석등 갓, 석탑 옥개석). 4삼각형 + 바닥."""
    bx, by = gx, -gz
    ex, ey = hx + ov, hz + ov
    base = len(buf.v)
    buf.v += [(bx - ex, by - ey, y0), (bx + ex, by - ey, y0),
              (bx + ex, by + ey, y0), (bx - ex, by + ey, y0),
              (bx, by, y0 + h)]
    b = base
    buf.f += [(b + 0, b + 1, b + 4), (b + 1, b + 2, b + 4),
              (b + 2, b + 3, b + 4), (b + 3, b + 0, b + 4),
              (b + 0, b + 3, b + 2, b + 1)]


def add_log(buf, gx, gz, y, half_len, rad, yaw, n=6, taper=0.82):
    """누운 통나무. 게임 XZ 평면에서 yaw(라디안, +X 에서 +Z 쪽으로) 방향으로 눕는다.
    옆면 n쿼드 + 양 뚜껑. 삼각형 4n-4."""
    bx, by = gx, -gz
    # 게임 방향 (cos yaw, sin yaw) 를 블렌더로: bx += cos, by -= sin
    axx, axy = math.cos(yaw), -math.sin(yaw)
    pxx, pxy = -axy, axx            # 축에 수직인 수평 방향
    base = len(buf.v)
    for (end, rr) in ((-1, rad * taper), (1, rad)):
        cx = bx + axx * half_len * end
        cy = by + axy * half_len * end
        for i in range(n):
            a = i * 2 * math.pi / n + 0.3
            ca, sa = math.cos(a), math.sin(a)
            buf.v.append((cx + pxx * ca * rr, cy + pxy * ca * rr, y + sa * rr))
    for i in range(n):
        j = (i + 1) % n
        buf.f.append((base + i, base + j, base + n + j, base + n + i))
    buf.f.append(tuple(base + i for i in range(n - 1, -1, -1)))
    buf.f.append(tuple(base + n + i for i in range(n)))


def add_reeds(buf, gx, gz, seed, n=5, h=1.05, spread=0.26):
    """물가 갈대 한 다발. ★v96-B: 삼각기둥 다발 -> **알파 카드 두 장(X 자)**.

    ★v79. 개울 기슭에 두던 둥근 바위를 이걸로 갈았다. 바위는 "밟고 건너라"로
      읽히는데(실제로 그렇게 읽혔다) 갈대는 아무도 밟으려 하지 않는다.
      spread 는 물칸 콜라이더(중심에서 1.26m) 안에 다 들어가게 잡은 값이다.

    ★왜 기둥을 버렸나 — 3각 기둥 다섯은 게임 거리에서 **세로 색종이 다섯 조각**이다.
      갈대의 정체는 실루엣(가늘고 휘어진 잎이 부채로 퍼진 모양)인데, 그걸
      지오메트리로 만들면 잎 한 장에 삼각형이 최소 여덟이라 예산이 안 맞는다.
      손그림 한 장 + 사각 카드 두 장이면 삼각형 4 개로 같은 실루엣이 나온다
      (원자재 incoming/tiles_v2/reed_black.jpg -> tools/tileize.py build_reed_card).
    ★두 장을 X 자로 세우는 이유: 한 장이면 옆에서 볼 때 두께가 0 이 되어 사라진다.
      쿼터뷰는 카메라가 고정이지만 캐릭터가 도는 게 아니라 **맵이 넓어서** 화면
      좌우 끝의 갈대는 꽤 비스듬히 보인다.
    ★UV 의 v=0 이 카드 **아래**다. 굽는 쪽에서 아래 26% 를 어둡게 눌러 놨으므로
      뒤집으면 밑동이 아니라 이삭이 어두워진다(= 뿌리 뽑힌 그림).
    ★n 은 이제 "잎 개수"가 아니라 뜻이 없다. 호출부 계약을 안 깨려고 인자만 남긴다.
    """
    r = random.Random(seed)
    hh = h * r.uniform(0.86, 1.24)
    hw = hh * 0.52                         # 카드 반폭. 텍스처가 정사각이라 폭 = 높이
    yaw0 = r.uniform(0, math.pi)
    for k in range(2):
        a = yaw0 + k * math.pi * 0.5
        dx, dz = math.cos(a) * hw, math.sin(a) * hw
        ox = r.uniform(-spread, spread) * 0.5
        oz = r.uniform(-spread, spread) * 0.5
        base = len(buf.v)
        for (sx, sz, yy, uu, vv) in ((-1, -1, 0.0, 0.0, 0.0), (1, 1, 0.0, 1.0, 0.0),
                                     (1, 1, hh, 1.0, 1.0), (-1, -1, hh, 0.0, 1.0)):
            buf.v.append((gx + ox + dx * sx, -(gz + oz + dz * sz), FLOOR_Y + yy))
            buf.uv.append((uu, vv))
        buf.f.append((base, base + 1, base + 2, base + 3))


# ─────────────────────────────────────────────────────────────
# 6b) 돌결 타일 ★경계가 "회색 판"이 아니라 "바위 벽"으로 읽히게
# ─────────────────────────────────────────────────────────────
# QA(v84 170_west_edge / 57_camp2)의 판정: "외곽 절벽·배후 스커트가 평평한 청회색
# 단색이라 스플랫 바닥·소품과 재질 언어가 안 맞는다. 화면의 12~40% 가 무텍스처 회색."
# 맞는 말이었다. 바닥은 타일 네 장으로 결이 깔리는데(15b절) 경계 지오메트리만
# 단색 Principled 였다. 여기서 **이어붙는 512 돌결 타일 한 장**을 구워
# 절벽 / 배후 스커트 / 스커트 바위 세 재질이 같이 쓴다.
#
# ★색 규칙은 안 깨진다. 타일은 결만 담고 **색은 재질이 정한다**
#   (baseColorFactor = 목표색 / 타일 평균색). 곱해 놓으면 평균이 정확히 목표색이라
#   "차갑고 어두우면 못 간다"가 타일 때문에 흔들릴 수 없다. 아래에서 실제로 잰다.
# ★이어붙어야 한다. 안 그러면 4m 마다 격자선이 보인다. 격자 노이즈를
#   **wrap 인덱스**로 보간해서 굽는다(양 끝이 같은 칸을 물어서 저절로 이어진다).
ROCK_TILE_RES = 512
ROCK_UV_SCALE = 3.2        # 타일 한 장이 덮는 거리(m) = 칸 한 변. 512/3.2 = 16cm/px
# 삼중평면에서 **윗면 투영 쪽으로 기울이는 가중치.** 1.0 이면 45도에서 축이 바뀌는데,
# 배후 스커트 비탈이 딱 그 언저리라 면마다 투영이 갈려 가로줄 이음매가 그어졌다
# (v86 첫 렌더 north_edge 에 실제로 그어졌다). 1.7 이면 약 60도까지 윗면으로 본다.
ROCK_UP_BIAS = 1.7


def _wrap_noise(res, cells, seed):
    """이어붙는 값 노이즈 한 옥타브."""
    g = np.random.default_rng(seed)
    a = g.random((cells, cells)).astype(np.float32)
    t = (np.arange(res, dtype=np.float32) + 0.5) * cells / res
    i0 = np.floor(t).astype(np.int32) % cells
    i1 = (i0 + 1) % cells
    f = t - np.floor(t)
    f = (f * f * (3.0 - 2.0 * f)).astype(np.float32)      # smoothstep
    fx, fy = f[None, :], f[:, None]
    A = a[np.ix_(i0, i0)]
    B = a[np.ix_(i0, i1)]
    C = a[np.ix_(i1, i0)]
    D = a[np.ix_(i1, i1)]
    return (A * (1 - fx) + B * fx) * (1 - fy) + (C * (1 - fx) + D * fx) * fy


def _wrap_fbm(res, cells, seed, octaves=4, gain=0.55):
    acc = np.zeros((res, res), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += amp * _wrap_noise(res, cells * (2 ** o), seed + o * 977)
        tot += amp
        amp *= gain
    return acc / tot


def _ridge(res, cells, seed, lo, octaves=3, gain=0.55):
    """능선 노이즈의 마루만 남긴다 = 바위 균열선."""
    v = _wrap_fbm(res, cells, seed, octaves, gain)
    v = 1.0 - np.abs(v * 2.0 - 1.0)
    return np.clip((v - lo) / max(1e-6, 1.0 - lo), 0.0, 1.0)


def bake_rock_tile():
    """돌결 512 타일. 결 + 잔결 위에 가늘고 진한 균열 세 겹을 판다.

    ★첫 판은 큰 얼룩(cells=3)을 46% 나 넣었더니 바위가 아니라 **대리석**으로 보였다.
      멀리서 보는 물건이라 큰 얼룩이 필요할 것 같지만, 큰 얼룩은 이미 정점색(단 차이)이
      만든다. 타일이 할 일은 **가까이서 보이는 결**이다."""
    S = ROCK_TILE_RES
    lump = _wrap_fbm(S, 3, 4101, 4, 0.58)        # 107cm 짜리 큰 덩어리
    grain = _wrap_fbm(S, 11, 4102, 4, 0.52)      # 29cm 결
    fine = _wrap_fbm(S, 37, 4103, 3, 0.50)       # 8.6cm 잔결
    v = 0.26 * lump + 0.40 * grain + 0.34 * fine
    v = (v - v.min()) / max(1e-6, v.max() - v.min())
    # 균열 세 겹(53 / 25 / 12cm). 문턱을 0.90 이상으로 올려 **선**으로 남긴다
    v = v - 0.46 * _ridge(S, 6, 4104, 0.90) - 0.30 * _ridge(S, 13, 4105, 0.92)
    v = v - 0.20 * _ridge(S, 27, 4106, 0.93)
    v = v - 0.14 * np.clip((grain - 0.58) * 3.4, 0.0, 1.0)    # 층리
    v = v + 0.10 * np.clip((fine - 0.70) * 3.0, 0.0, 1.0)     # 튀어나온 알갱이
    v = np.clip((v - v.mean()) * 1.30 + 0.52, 0.0, 1.0)
    # 색: 어두운 자리는 조금 더 푸르고, 밝은 자리는 조금 더 따뜻하다.
    # ★색상 폭을 좁게 잡는다. 여기서 색을 세게 주면 재질의 목표색을 덮어버린다.
    # ★밝게 굽는다. 최종색 = 곱수 x 타일이라 **타일이 밝을수록 곱수에 여유가 생긴다.**
    #   곱수는 1 을 넘길 수 없으므로(glTF baseColorFactor / COLOR_0 정규화 ushort)
    #   타일이 목표색들보다 확실히 밝아야 한다. 대비는 곱수가 상쇄해서 안 변한다.
    lo = np.array((0.40, 0.43, 0.47), np.float32)
    hi = np.array((0.80, 0.81, 0.82), np.float32)
    rgb = lo[None, None, :] + (hi - lo)[None, None, :] * v[:, :, None]
    return np.clip(rgb, 0.0, 1.0)


ROCK_TILE = bake_rock_tile()
# 타일의 **선형** 평균색. 재질의 곱수(baseColorFactor)는 여기서 나온다.
# ★sRGB 값의 평균이 아니라 선형 평균이어야 한다. 셰이더가 곱하는 건 선형이다.
_rt_l = np.where(ROCK_TILE <= 0.04045, ROCK_TILE / 12.92,
                 ((ROCK_TILE + 0.055) / 1.055) ** 2.4)
_rt_lin = _rt_l.reshape(-1, 3).mean(axis=0)
print("[돌결타일] %dx%d (한 장 %.1fm) 평균 sRGB #%02x%02x%02x / 선형 %.3f %.3f %.3f"
      % (ROCK_TILE_RES, ROCK_TILE_RES, ROCK_UV_SCALE,
         int(ROCK_TILE[:, :, 0].mean() * 255), int(ROCK_TILE[:, :, 1].mean() * 255),
         int(ROCK_TILE[:, :, 2].mean() * 255), _rt_lin[0], _rt_lin[1], _rt_lin[2]))

IMG_ROCK = bpy.data.images.new("level1_rock_tile", ROCK_TILE_RES, ROCK_TILE_RES,
                               alpha=False)
IMG_ROCK.colorspace_settings.name = "sRGB"
_rt_px = np.ones((ROCK_TILE_RES, ROCK_TILE_RES, 4), np.float32)
_rt_px[:, :, :3] = ROCK_TILE
IMG_ROCK.pixels.foreach_set(_rt_px.reshape(-1))
# ★생성 이미지는 pack() 이 안 된다. 바닥 텍스처와 같은 방식으로 파일에 한 번 굽고
#   익스포터가 그 파일을 읽게 한다(안 그러면 glb 에 빈 텍스처가 들어간다).
IMG_ROCK.filepath_raw = os.path.join(TMP, "level1_rock_tile.png")
IMG_ROCK.file_format = "PNG"
IMG_ROCK.save()


# ── ★★v96-B. 손그림 소품 타일 셋 (수피 · 이끼 · 갈대) ────────
# 돌결 타일과 **같은 계약**이다: 타일은 결만 담고 색은 재질이 정한다
# (baseColorFactor = 목표색 / 타일 평균). 다른 점은 절차가 아니라 손그림이라는 것뿐.
#
# 왜 필요했나 — 10차가 남긴 신고 셋이 전부 "무텍스처 단색 면" 이었다.
#   · 나무 줄기(COL_TRUNK)가 색만 있는 육각기둥
#   · 바위 위 이끼(DECO_MOSS)가 **초록 유리 파편**으로 읽힘 (결이 없는 납작 돔)
#   · 물가 갈대(DECO_REED)가 색종이 조각
# 원자재는 incoming/tiles_v2/, 굽는 것은 tools/tileize.py --props 다.
#
# ★평균색은 여기서 재지 않고 **tileize 가 재서 넘긴 값**을 읽는다.
#   이 스크립트에는 PIL 이 없어서 png 화소를 못 읽는다. 어림으로 적으면 곱수가
#   틀리고, 곱수가 틀리면 팔레트가 조용히 밀린다(아래 [색규칙] 줄이 잡아내긴 한다).
# ★갈대는 알파 카드라 평균이 **덮개 가중**이다. 전체 평균을 쓰면 투명한 65% 가
#   새까맣게 끼어들어 곱수가 1 을 훌쩍 넘는다.
PROP_TEX_DIR = os.path.join(ROOT, "blender", "tex")
with open(os.path.join(PROP_TEX_DIR, "prop_tiles.json")) as _f:
    PROP_TILES = json.load(_f)


def load_prop_tile(key):
    """굽힌 소품 타일 한 장을 blender 이미지로. (이미지, 선형평균) 을 돌려준다."""
    p = os.path.join(PROP_TEX_DIR, PROP_TILES[key]["file"])
    im = bpy.data.images.load(p, check_existing=True)
    im.colorspace_settings.name = "sRGB"
    lin = PROP_TILES[key]["mean_lin"]
    print("[소품타일] %-10s %s  선형평균 %.3f %.3f %.3f  덮개 %.0f%%"
          % (key, os.path.basename(p), lin[0], lin[1], lin[2],
             PROP_TILES[key]["coverage"] * 100))
    return im, lin


IMG_BARK, LIN_BARK = load_prop_tile("prop_bark")
IMG_MOSS, LIN_MOSS = load_prop_tile("prop_moss")
IMG_REED, LIN_REED = load_prop_tile("prop_reed")

# 타일 한 장이 덮는 거리(m). tools/tileize.py PROP_SPEC 의 period 와 같은 값이다.
BARK_UV_SCALE = 1.20
MOSS_UV_SCALE = 0.85


def tri_uv(scale):
    """면 법선의 우세 축으로 고르는 삼중평면 UV를 **배율만 바꿔** 찍어 낸다.
    ★한 축으로만 투영하면 절벽 꼭대기(윗면)와 비탈에서 무늬가 길게 늘어난다.
      벽면은 (둘레, 높이) 로, 윗면은 (x, y) 로 찍어야 어디를 봐도 같은 굵기다.
    ★v96-B. 수피·이끼가 같은 함수를 쓰되 배율이 다르다. 배율은 곧 "타일 한 장이
      덮는 거리" 이고, 물건 크기에 안 맞으면 결이 아니라 얼룩이 된다
      (줄기 지름 0.44m 에 3.2m 짜리 타일을 씌우면 무늬 한 조각만 늘어붙는다)."""
    def f(co, poly):
        n = poly.normal
        ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2]) * ROCK_UP_BIAS
        if az >= ax and az >= ay:
            return (co[0] / scale, co[1] / scale)
        if ax >= ay:
            return (co[1] / scale, co[2] / scale)
        return (co[0] / scale, co[2] / scale)
    return f


rock_uv = tri_uv(ROCK_UV_SCALE)
bark_uv = tri_uv(BARK_UV_SCALE)
moss_uv = tri_uv(MOSS_UV_SCALE)


# ─────────────────────────────────────────────────────────────
# 7) 재질
# ─────────────────────────────────────────────────────────────
MATS = {}


def mat_solid(name, hexcol, rough=0.92, backface=True):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = hex_lin(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.0
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    m.use_backface_culling = backface
    MATS[name] = m
    return m


ROCK_MATS = []       # (재질, 목표색, 곱수, 정점색 평균). 아래 색 규칙 검증이 다시 잰다


def mat_rock(name, hexcol, rough=1.0, backface=False, shade_mean=1.0):
    """돌결 타일(공용 절차 타일) x 목표색. mat_tex 의 얇은 껍질이다."""
    return mat_tex(name, hexcol, IMG_ROCK, _rt_lin,
                   rough=rough, backface=backface, shade_mean=shade_mean)


def mat_tex(name, hexcol, img, tile_lin, rough=1.0, backface=False,
            shade_mean=1.0, alpha=False):
    """타일 x 목표색. 타일은 결만 담고 **색은 재질이 정한다.**

    ★glTF 함정: Principled 에 이미지만 물리면 baseColorFactor 가 1 이라 색을 못 준다.
      Image Texture -> Mix(MULTIPLY) <- 상수색 -> Base Color 로 짜면 익스포터가
      baseColorTexture + baseColorFactor 로 정확히 쪼개서 내보낸다(실측 확인).
    ★곱수 = 목표색(선형) / 타일 평균(선형) / **정점색 평균**.
      최종색 = 곱수 x 타일 x 정점색 이므로, 세 평균을 다 나눠 두면 화면 평균이
      정확히 목표색이 된다. 결과: 타일도 깔고 단 차이 음영도 넣었는데
      "어둡고 차가우면 못 간다" 색 규칙은 한 톨도 안 움직인다(아래에서 잰다)."""
    if name in MATS:
        return MATS[name]
    tgt = hex_lin(hexcol)
    raw = [tgt[i] / max(1e-6, float(tile_lin[i]) * shade_mean) for i in range(3)]
    k = [min(1.0, x) for x in raw]
    if max(raw) > 1.0:
        # ★glTF COLOR_0 은 정규화 ushort 라 1 을 넘으면 잘린다. baseColorFactor 도
        #   1 을 넘기면 안 된다. 타일을 더 밝게 굽거나 음영 폭을 줄여야 한다.
        print("[경고] %s 곱수가 1 을 넘는다(%.3f). 타일을 더 밝게 구워라" % (name, max(raw)))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
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
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    if alpha:
        # ★알파 컷. 익스포터는 **알파 소켓이 실제로 이어져 있을 때만** 그 이미지를
        #   PNG 로 내보낸다(export_image_format="JPEG" 여도 그렇다. 5.2 설명문
        #   "Images that need alpha are saved as PNGs though"). 안 이으면 JPEG 로
        #   재인코딩되면서 **알파가 통째로 사라지고 갈대가 검은 네모**가 된다.
        # ★★그리고 alphaMode 는 **노드 구성에서 읽는다.** 블렌더 4.2+ 는
        #   material.blend_method 가 없어졌고, 5.2 익스포터는
        #   search_node_tree.detect_alpha_clip() 으로 "알파에 비교 노드가 물려 있는가"
        #   를 본다. 그냥 이으면 **BLEND** 로 나가고, BLEND 는 깊이 정렬을 타서
        #   갈대끼리·수풀과 앞뒤가 뒤집힌다. Math(GREATER_THAN, 0.5) 를 끼우면
        #   alphaMode=MASK · alphaCutoff=0.5 로 정확히 나간다(실측 확인).
        cut = nt.nodes.new("ShaderNodeMath")
        cut.operation = "GREATER_THAN"
        cut.inputs[1].default_value = 0.5
        nt.links.new(tex.outputs["Alpha"], cut.inputs[0])
        nt.links.new(cut.outputs[0], bsdf.inputs["Alpha"])
    m.use_backface_culling = backface
    MATS[name] = m
    ROCK_MATS.append((name, hexcol, tuple(k), shade_mean, tuple(tile_lin)))
    return m


# ── 정점색(단 차이 음영)의 평균. 재질 곱수를 이만큼 되올려 색 규칙을 지킨다 ──
# ★값의 근거는 아래 add_ridge / add_skirt 의 상수다. 거기를 고치면 여기도 고쳐야
#   하는데, 잊어버려도 아래 [색규칙] 줄이 어긋난 값을 바로 찍는다.
# ★손으로 어림하지 말고 **실측값**을 적는다. make_obj 가 면적 가중으로 다시 재서
#   "정점색 면적평균" 으로 찍는다. 두 숫자가 어긋나면 화면 평균색이 목표를 벗어난다.
# ★v89. 0.841 -> 0.762. 단 밝기를 0.63~1.00 에서 0.50~1.00 으로 벌리고 아랫도리
#   곱수를 0.80 -> 0.70 으로, 턱을 0.13 -> 0.42m 로 키웠더니 면적 평균이 내려왔다.
#   여기를 안 따라 고치면 절벽이 목표색보다 10% 어둡게 나온다(= 색 규칙 회귀).
#   숫자는 make_obj 가 찍는 "COL_CLIFF ... 정점색 면적평균" 을 그대로 옮긴 것이다.
# ★v94. 0.762 -> 0.780. RIDGE_FOOT 을 0.70 -> 0.78 로 눅이고 단 경계를 흔들면서
#   면적 평균이 올라갔다. 여기를 안 따라 고치면 절벽이 목표색보다 2.4% 밝게 나온다
#   (= 색 규칙 회귀). 숫자는 make_obj 가 찍는 "COL_CLIFF ... 정점색 면적평균" 그대로다.
RIDGE_SHADE_MEAN = 0.780     # 실측(0.50~1.00, 단마다 밑동 x0.78, 3단 + 꼭대기 면)
SKIRT_SHADE_MEAN = 0.847     # 실측(0.66 0.80 0.90 0.97 1.00 을 줄 면적으로 가중)


# ★v94 — 회청색 계열의 **채도를 올리고 명도를 내렸다** (건틀릿 화풍 분열 대응).
#   심사관: "채도 스프레드 58pt(벽 13.6% ↔ 수풀 71.9%). 롤은 8pt. 맵이 캐릭터보다 튄다."
#   롤 실물을 같은 자로 재 보면(tools/terrain_metrics.py card) 협곡의 바위 절벽은
#   **채도 26.8% · 휘도 55** 이고 잔디가 채도 44~54% 다. 우리 바위는 채도 9.8% 짜리
#   거의 무채색 회색이라, 초목(43%)과의 거리가 롤보다 훨씬 멀었다.
#   그래서 회청색 넷을 한 단씩 **더 푸르고 더 어둡게** 옮긴다. 색 규칙(못 가는 곳은
#   어둡고 차갑다)은 오히려 강해진다 — 더 차가워지고 더 어두워지기 때문이다.
#     8a9199 채도 9.8% -> 7c8794 채도 16.2%   (바위 무더기)
#     6e7883 채도 15.7% -> 626e7d 채도 21.6%  (외곽 절벽)
#     76858f 채도 17.2% -> 6a7b8a 채도 23.2%  (배후 스커트)
#     5d6a75 채도 20.9% -> 53616f 채도 25.2%  (스커트 노두)
# ★색 규칙 (탑다운에서 길과 벽을 가르는 유일한 장치다). v67 에서 전체 명도를
#   밤에서 **봄 낮**으로 올렸다. 규칙 자체는 그대로다 — 바뀐 건 밝기 대역이다.
#   걸을 수 있는 곳 = 밝고 따뜻한 색 (흙길·연둣빛 풀·금빛 마른 풀)
#   못 가는 곳     = 어둡고 차가운 색 (회청색 바위 / 진한 암록 덤불)
#   숨는 수풀      = 그 사이의 **진한 신록**. 초원보다 어둡고 훨씬 초록이라 덩어리로 읽힌다
#   폐허(사람 흔적) = 창백한 회백색. 자연물 중에 하나도 없는 색이라 랜드마크로 튄다
# ★v89 (3차 QA #5 "큰 바위 재질 분열"). 한 화면 안에서 s20 이 굽는 바위는 무텍스처
#   밝은 회색 판인데 옆의 Meshy 바위(web/props/rock.glb)는 이끼 낀 돌결이라, 같은
#   "바위"가 두 재질 언어로 갈렸다(증거 P1_04_west.png / BEFORE_A_boulder_nw.png).
#   절벽에 쓰던 **돌결 타일 트라이플래너를 그대로** 입혀 언어를 하나로 합친다.
#   색은 재질이 정한다(곱수 = 목표색/타일평균). 실측 곱수 max 0.810 < 1 이라
#   8a9199 라는 화면 평균색은 한 톨도 안 움직인다(아래 [색규칙] 줄이 잰다).
#   ★buf_rock 에는 정점색이 없으므로 shade_mean=1.0 이다.
#   ★rough·backface 는 예전 mat_solid 값(0.92 / 컬링 켬)을 그대로 물려받는다.
#     여기서 double sided 로 바꾸면 바위 개수가 많아 드로우가 손해다.
M_ROCK = mat_rock("MAT_ROCK", "616d73", rough=0.92, backface=True)   # 바위 무더기(낮 화강암)
# ★v86. 외곽 절벽. 색은 그대로 두고 **돌결 타일만 입혔다**(6b절).
#   평균색이 6e7883 로 유지되므로 "안쪽 바위보다 한 단 눌러 경계를 박는다"는 그대로다
M_ROCK_DARK = mat_rock("MAT_ROCK_DARK", "566169", shade_mean=RIDGE_SHADE_MEAN)
# ★v94 (심사 지적 G7 "무텍스처 단색 갈색 판 = 플레이스홀더 수준").
#   둔덕은 이 맵에 남은 **마지막 무텍스처 면**이었다. v89 에서 큰 바위를 돌결 타일로
#   통일할 때 여기만 빠져 있었다. 같은 타일을 입혀 재질 언어를 하나로 맞춘다.
#   색은 재질이 정하므로(곱수 = 목표색/타일평균) 화면 평균색 8a6f4c 는 안 움직인다
#   ([색규칙] 줄이 잰다). 정점색이 없으니 shade_mean=1.0 이다.
M_EARTH = mat_rock("MAT_EARTH", "66543f", rough=0.92, backface=True)  # 흙 둔덕
# ★v94 (심사 지적 "이끼는 하드에지 네온 데칼", 채도 스프레드 58pt).
#   6f9a45 는 채도 55%·명도 60% 라 회청색 바위(8a9199) 위에서 형광 스티커로 떴다.
#   롤의 이끼는 **바위 틈에 낀 어두운 초록**이라 값이 바위에 녹아 있다.
#   4a6636 = 채도 47% · 명도 40%. 바위보다 확실히 어두워 "틈"으로 읽힌다.
# ★★v96-B. 이끼·수피에 손그림 타일을 입힌다. 색은 한 톨도 안 바꾼다
#   (곱수 = 목표색/타일평균 이라 화면 평균색이 그대로다. 아래 [색규칙] 줄이 증명).
#   · 이끼: 10차 화면에서 바위 위 이끼가 **초록 유리 파편**으로 읽혔다. 정체는
#     결 없는 납작 돔이라 툰 셰이딩이 밝기 띠 두세 개로만 갈라 놓은 것이었다.
#     이끼 알갱이가 그려진 타일이 들어가면 같은 지오메트리가 "낀 이끼"가 된다.
#   · 수피: 줄기가 색만 있는 육각기둥이었다. 세로 결 하나로 나무가 된다.
M_MOSS = mat_tex("MAT_MOSS", "465a3d", IMG_MOSS, LIN_MOSS,
                 rough=0.92, backface=True)         # 이끼. ★v94 채도 47%->36%
M_BARK = mat_tex("MAT_BARK", "594b3a", IMG_BARK, LIN_BARK,
                 rough=0.92, backface=True)         # 나무 줄기·쓰러진 거목
# ★v94. 22391b 는 채도 52.6% 라 소품 초목(37.6~43.3%)보다 쨍했다. 맵 쪽 초록이
#   소품보다 튀면 심사가 지적한 "화풍 분열"이 그대로 남는다. 명도(제일 어둡다)는
#   그대로 두고 채도만 내린다. 2a3a24 = 채도 37.9% · 휘도 22 (thicket 37.6% 와 짝)
M_LEAF_DARK = mat_solid("MAT_LEAF_DARK", "384631", rough=1.0)   # 막는 초목(제일 어두운 초록)
M_CANOPY = mat_solid("MAT_CANOPY", "4b5d3b", rough=1.0)         # 안 막는 나뭇가지(수풀보다 어둡다). ★v94 채도 61%->40%
# ★v94. 수풀 지오메트리는 지금 외부 glb(web/props/bush.glb)라 이 재질은 화면에
#   안 나온다. 그래도 값을 같이 내려 둔다 — 누가 절차 수풀을 다시 켜면 형광이
#   그대로 돌아오는 지뢰이기 때문이다. 6c9b59 는 새 bush 텍스처의 평균색이다.
M_BUSH = mat_solid("MAT_BUSH", "4c5f41", rough=1.0, backface=False)  # 숨는 수풀(외부 glb 로 대체됨)
# ★v89. 폐허 석재에는 돌결 타일을 못 입힌다. 곱수 = 목표색/타일평균 이 1.83 이라
#   glTF baseColorFactor 상한 1 을 넘긴다(= 타일보다 밝은 색이라 곱셈으로 못 만든다).
#   억지로 넣으려면 타일을 더 밝게 다시 구워야 하는데, 그러면 절벽·스커트·바위
#   세 재질의 곱수가 전부 흔들린다. 게다가 폐허는 **자연물에 없는 창백한 색**이
#   랜드마크의 정체라 결이 없는 편이 오히려 자연물과 안 섞인다. 그대로 둔다.
# ★★v96. **해소됐다. 이제 돌결 타일을 입힌다.**
#   9차의 막힘은 "곱수 = 목표색/타일평균 = 1.83 > 1" 이었다. 즉 목표색이 타일보다
#   밝아서 곱셈으로는 못 만드는 색이었다. v96 에서 팔레트를 통째로 내리면서
#   목표가 c2c7c0 -> 7f847c 로 내려왔고 곱수가 1 아래로 들어왔다(굽기 로그의
#   [색규칙] 줄이 증명한다). 밝은 폐허 전용 타일을 따로 굽지 않아도 됐다.
#   ★"자연물에 없는 창백한 색" 이라는 랜드마크 정체는 그대로다 — 여전히 맵에서
#     제일 밝은 무채색 면이고, 이제 결까지 있어서 종잇조각으로 안 읽힌다.
M_STONE_PALE = mat_rock("MAT_STONE_PALE", "71766e", rough=0.92, backface=True)
# ★v86. 개울 수면. 5aa3bd / rough 0.20 은 **판때기**로 읽혔다(QA S11).
#   바닥에 칠한 개울색(539db6)이 발치 그늘·잔결을 먹어 어두워지는데 수면 메시만
#   반짝여서, 흙 위에 파란 아크릴판을 얹은 그림이 됐다. 칠한 색에 맞춰 눌렀다.
M_WATER = mat_solid("MAT_WATER", "467881", rough=0.36)
M_EXIT = mat_solid("MAT_EXIT", "9fdcd2")             # 탈출 표식. 맵 어디에도 안 쓰는 색
# ★v79. 물가 갈대. 숨는 수풀(6fd143)보다 확실히 어둡고 누렇다. 색이 겹치면
#   "들어가서 숨을 수 있는 곳"으로 오해한다. 갈대는 서 있기만 하는 물건이다.
# ★v94. 채도 48.3% -> 38.3%. 소품 초목 밴드(37.6~43.3%) 안으로 들인다
# ★★v96-B. 색종이 조각 -> **알파 카드**. 지오메트리도 같이 갈렸다(add_reeds 참조).
#   backface=False 여야 한다 = 양면. 카드는 뒤에서도 보여야 하는 물건이다.
M_REED = mat_tex("MAT_REED", "657047", IMG_REED, LIN_REED,
                 rough=1.0, backface=False, alpha=True)
# ★v79. 경계 바깥 배후 스커트. 안쪽 절벽(6e7883)보다 한 단 밝고 푸르게 띄운다.
#   "한 겹 더 뒤"로 읽혀야 벽이 아니라 산자락이 된다.
# ★v86. 절벽과 같은 돌결 타일을 쓴다. 색만 다르다 = 같은 재질 언어의 한 겹 뒤
M_SKIRT = mat_rock("MAT_SKIRT", "5c6a76", shade_mean=SKIRT_SHADE_MEAN)
M_SKIRTROCK = mat_rock("MAT_SKIRTROCK", "515d66")   # 노두는 정점색이 없다(평평한 곱수 1)
# ★v94. 채도 48.7% -> 38.7%. 배후 숲이 화면 끝 띠로 들어오는데 거기가 제일 쨍하면
#   눈이 맵 밖으로 끌려간다(심사 G6 "배경 판 노출" 과 같은 자리다)
M_SKIRTWOOD = mat_solid("MAT_SKIRTWOOD", "44573c", rough=1.0, backface=False)
# ★v86. 보스 어귀 선돌에 감은 붉은 끈. 맵에서 붉은색은 보스 결계 원 하나뿐이라
#   같은 붉은색을 어귀에 물들이면 "이 길이 보스"가 지형 단서로 읽힌다(부수 과제).
M_CORD = mat_solid("MAT_CORD", "a8382c", rough=0.85)

# ── ★색 규칙 회귀 검사: 돌결 타일이 색을 옮기지 않았는가 ─────
# 타일을 깔면 "못 가는 곳은 어둡고 차갑다"가 흔들릴 수 있다. 흔들리지 않는다는 걸
# 눈이 아니라 숫자로 남긴다. 곱수 x 타일 평균(선형)을 다시 sRGB 로 되돌려 목표색과 잰다.
def _lin_to_srgb(v):
    return 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055


for (_nm, _hex, _k, _sm, _tl) in ROCK_MATS:
    _got = [_lin_to_srgb(_k[i] * float(_tl[i]) * _sm) for i in range(3)]
    _want = [int(_hex[i * 2:i * 2 + 2], 16) / 255.0 for i in range(3)]
    _d = max(abs(_got[i] - _want[i]) * 255 for i in range(3))
    print("[색규칙] %-14s 목표 #%s -> 화면 평균 #%02x%02x%02x  차 %.1f/255 "
          "(타일 x 곱수 x 정점색평균 %.3f)  %s"
          % (_nm, _hex, int(_got[0] * 255 + 0.5), int(_got[1] * 255 + 0.5),
             int(_got[2] * 255 + 0.5), _d, _sm, "OK" if _d <= 2.0 else "★어긋남"))

# 버퍼. 이름 앞머리가 곧 규칙이다(COL_ 막는다 / BUSH_ 숨는다 / 나머지 안 막는다)
buf_floor = None                                     # 아래에서 텍스처와 함께 만든다
buf_rock = Buf("COL_ROCK", M_ROCK)
buf_cliff = Buf("COL_CLIFF", M_ROCK_DARK)
buf_earth = Buf("COL_EARTH", M_EARTH)
buf_leaf = Buf("COL_THICKET", M_LEAF_DARK)
buf_bark = Buf("COL_TRUNK", M_BARK)
buf_canopy = Buf("CANOPY_TREE", M_CANOPY)      # ★가지는 안 막는다. 밑을 지나가야 한다
buf_moss = Buf("DECO_MOSS", M_MOSS)
buf_stone = Buf("COL_RUIN", M_STONE_PALE)
# ★v89. buf_altar(DECO_ALTAR)는 폐기했다. 3차 QA #6 "보스 마당 상공의 7각형 슬래브"의
#   정체가 이것이다. 자세한 폐기 사유는 11절 보스 자리에 적었다.
buf_water = Buf("WATER_STREAM", M_WATER)
buf_exit = Buf("DECO_EXITMARK", M_EXIT)
buf_reed = Buf("DECO_REED", M_REED)            # 물가 갈대. 안 막고 못 숨는다
buf_skirt = Buf("DECO_SKIRT", M_SKIRT)         # 경계 바깥 비탈. bounds 밖이다
buf_skirtrock = Buf("DECO_SKIRTROCK", M_SKIRTROCK)
buf_skirtwood = Buf("DECO_SKIRTWOOD", M_SKIRTWOOD)
buf_cord = Buf("DECO_CORD", M_CORD)            # 보스 어귀 선돌의 붉은 끈


# ─────────────────────────────────────────────────────────────
# 8) 프롭 등록소 — 배치(테이블)와 모양(함수)을 분리한다
# ─────────────────────────────────────────────────────────────
# PROP_KINDS[종류] = {
#   "build": 지오메트리 함수 (★Meshy 에셋으로 갈아끼울 자리),
#   "col":   콜라이더 규격. None / ("circle", r) / ("box", hx, hz).  ★모양이 아니라
#            종류가 정한다. 모양을 바꿔도 충돌은 그대로다,
#   "h":     콜라이더 높이(기록용. 게임은 2D 로 검사한다),
#   "tag":   level1.json 콜라이더 태그,
#   "desc":  보고용 설명
# }
PROP_KINDS = {}
PROPS = []
rnd = random.Random(20260808)

# ★v69. 이 5종은 **이 glb 에 안 굽는다.**
#   Meshy 상세 모델로 갈아끼웠는데(blender/s22_props.py -> web/props/<종류>.glb)
#   643개를 여기서 구우면 삼각형이 수십만이 되고 파일이 수십 MB 가 된다.
#   대신 배치만 level1.json 의 props[] 로 내보내고 게임(web/props.js)이
#   InstancedMesh 로 심는다. **콜라이더는 이 파일이 그대로 계산한다**
#   (배치 테이블 + 종류 규격에서 나오므로 모양이 바뀌어도 충돌은 안 변한다).
# ★v91. 지형 5종(blender/s28_terrain.py -> web/props/<종류>.glb)이 합류했다.
#   오너 판정 "돌·냇가가 찰흙"의 근본 대응이다. 다섯 다 **장식 전용**이라
#   콜라이더가 한 개도 안 늘어난다(막는 일은 기존 링·물칸·바위 콜라이더가 그대로 한다).
TERRAIN_KINDS = {"cliff_tall", "outcrop", "boulder_xl", "bank", "slab"}
EXTERNAL_KINDS = {"rock", "crag", "thicket", "tree", "bush"} | TERRAIN_KINDS
# 종류별 세로 흔들림 폭. 원래 절차적 소품이 갖고 있던 높이 편차를 그대로 옮긴다.
# 모델 한 벌을 643번 심으면 편차가 없어서 복붙 티가 난다(회전 + 이 값이 그걸 지운다).
# 괄호 안은 출처가 된 옛 build 함수의 높이 식이다.
EXT_YJIT = {
    "rock": (0.80, 1.15),      # hh = 1.9 * s * u(0.62, 1.00)
    "crag": (0.88, 1.25),      # hh = WALL_H * s * u(0.85, 1.30)
    "thicket": (0.90, 1.15),   # hh = 3.2 * s * u(0.88, 1.18)
    "tree": (0.85, 1.18),      # hh = 5.4 * s * u(0.82, 1.20) * (slim 1.18)
    "bush": (0.85, 1.15),      # hh = 1.5 * s * u(0.85, 1.15)
    # ── 지형 5종 ──
    # ★기둥은 마루가 들쭉날쭉해야 능선이 산다(3.6 ~ 5.7m). 절차 절벽 4.0m 을 넘긴다.
    #   폭을 넓게 잡은 이유: v91 1차 게임 화면에서 서쪽 벽이 **벽돌담**으로 보였다.
    #   옆에서 비스듬히 보면 잘린 옆면이 나란히 서는데 키까지 고르면 줄눈이 된다.
    #   키를 크게 흔들고(여기) 앞뒤로도 흔들면(아래 배치의 파묻힘 흔들기) 줄눈이 깨진다.
    # ★v94. 0.78~1.24 -> 0.66~1.42. 마루선이 더 들쭉날쭉해야 "벽돌담"이 안 된다
    "cliff_tall": (0.66, 1.42),
    "outcrop": (0.85, 1.20),
    # ★거대 바위만 1 보다 크다. 랜드마크로 쓰는 자리라 **키로** 눈에 띄어야 하는데
    #   가로는 콜라이더 반지름과 묶여 있어서 못 건드린다. 세로만 늘린다
    #   (모델 높이 1.255 x 1.30~1.62 = 1.6~2.0m. scale 1.3 이면 2.6m).
    "boulder_xl": (1.30, 1.62),
    "bank": (0.72, 1.34),   # ★v94. 기슭 띠 복붙 완화
    "slab": (0.80, 1.30),
}


def prop_kind(name, col=None, h=1.0, tag=None, desc=""):
    def deco(fn):
        PROP_KINDS[name] = {"build": fn, "col": col, "h": h,
                            "tag": tag or name, "desc": desc, "n": 0, "ncol": 0}
        return fn
    return deco


def place(kind, gx, gz, yaw=0.0, scale=1.0, collide=None, **kw):
    """배치 테이블에 한 줄 넣는다. 모양은 나중에 build 가 만든다."""
    k = PROP_KINDS[kind]
    if collide is None:
        collide = k["col"] is not None
    if collide and k["col"] is None:
        raise ValueError("%s 는 콜라이더 규격이 없다" % kind)
    if collide and k["col"][0] == "box":
        # ★게임은 축정렬 박스만 검사한다. 45도로 눕힌 통나무를 막으면
        #   보이는 것과 막히는 게 어긋난다. 막는 통나무는 90도 단위만 허용.
        q = round(yaw / (math.pi / 2)) * (math.pi / 2)
        if abs(yaw - q) > 1e-3:
            raise ValueError("%s: 박스 콜라이더는 90도 단위 회전만 된다" % kind)
    p = {"kind": kind, "x": gx, "z": gz, "yaw": yaw, "scale": scale,
         "collide": collide, "seed": rnd.randint(0, 10 ** 6)}
    p.update(kw)
    PROPS.append(p)
    k["n"] += 1
    if collide:
        k["ncol"] += 1
    return p


COLLIDERS = []   # level1.json 에 나갈 충돌 도형 (게임 좌표)
PLATFORMS = []   # 올라설 수 있는 낮은 단 (무릎 아래라 안 막지만 발이 묻히면 안 된다)


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


def push_plat_circle(gx, gz, r, top, tag):
    """★v89 현재 부르는 데가 없다. 유일한 사용처였던 보스 제단을 뺐다(11절).
    게임(web/level.js)은 platforms[] 의 type='circle' 을 그대로 읽으므로,
    원형 단이 다시 필요해지면 이 함수만 부르면 된다. 그래서 지우지 않는다."""
    PLATFORMS.append({"type": "circle", "x": round(gx, 3), "z": round(gz, 3),
                      "r": round(r, 3), "top": round(top, 3), "tag": tag})


# ── 종류별 모양 ──────────────────────────────────────────────
# ★여기 아래 함수 12개가 "교체 대상"이다. Meshy 에셋이 오면
#   각 함수 몸통을 "glb 를 임포트해 (x, z, yaw, scale) 로 놓는다"로 바꾸면 된다.

@prop_kind("rock", col=("circle", 0.95), h=1.9, tag="rock",
           desc="바위. scale 0.6 이상은 막는 엄폐물, 그 아래는 장식 잔돌")
def b_rock(p):
    r = random.Random(p["seed"])
    s = p["scale"]
    x, z = p["x"], p["z"]
    rx = 0.95 * s * r.uniform(0.85, 1.20)
    rz = 0.95 * s * r.uniform(0.85, 1.20)
    hh = 1.9 * s * r.uniform(0.62, 1.00)
    add_dome(buf_rock, x, z, FLOOR_Y, rx, rz, hh, n=6, seed=p["seed"], squash=1.40)
    if s < 0.55:
        return
    if r.random() < 0.45:                      # 어깨에 얹힌 조각
        add_dome(buf_rock, x + r.uniform(-0.4, 0.4) * s, z + r.uniform(-0.4, 0.4) * s,
                 FLOOR_Y + hh * 0.52, rx * 0.55, rz * 0.55, hh * 0.5,
                 n=5, seed=p["seed"] + 1, squash=1.3)
    if r.random() < 0.30:                      # 이끼
        add_dome(buf_moss, x + r.uniform(-0.35, 0.35) * s, z + r.uniform(-0.35, 0.35) * s,
                 FLOOR_Y + hh * 0.62, rx * 0.5, rz * 0.5, hh * 0.2,
                 n=5, seed=p["seed"] + 2, squash=0.7)


@prop_kind("crag", col=None, h=2.8, tag="crag",
           desc="바위 절벽 덩어리. 막는 칸을 채운다(콜라이더는 칸 격자에서 나온다)")
def b_crag(p):
    r = random.Random(p["seed"])
    s = p["scale"]
    x, z = p["x"], p["z"]
    hh = WALL_H * s * r.uniform(0.85, 1.30)
    rx = 1.25 * s * r.uniform(0.85, 1.15)
    rz = 1.25 * s * r.uniform(0.85, 1.15)
    add_dome(buf_rock, x, z, FLOOR_Y, rx, rz, hh, n=6, seed=p["seed"], squash=1.55)
    if r.random() < 0.55:                      # 첨봉. 실루엣에 각을 준다
        add_prism(buf_rock, x + r.uniform(-0.5, 0.5), z + r.uniform(-0.5, 0.5),
                  FLOOR_Y + hh * 0.45, FLOOR_Y + hh * r.uniform(1.10, 1.45),
                  rx * 0.45, rx * 0.12, 5, phase=r.uniform(0, 1))
    if r.random() < 0.28:
        add_dome(buf_moss, x + r.uniform(-0.6, 0.6), z + r.uniform(-0.6, 0.6),
                 FLOOR_Y + hh * 0.55, rx * 0.5, rz * 0.5, 0.3,
                 n=5, seed=p["seed"] + 3, squash=0.7)


@prop_kind("boulder", col=None, h=1.3, tag="boulder",
           desc="너덜지대 바위. ★1.3m 라 몸은 못 지나가는데 건너편이 보인다(개방감 장치)")
def b_boulder(p):
    r = random.Random(p["seed"])
    s = p["scale"]
    x, z = p["x"], p["z"]
    hh = 1.30 * s * r.uniform(0.72, 1.05)
    rx = 1.15 * s * r.uniform(0.85, 1.25)
    rz = 1.15 * s * r.uniform(0.85, 1.25)
    add_dome(buf_rock, x, z, FLOOR_Y, rx, rz, hh, n=6, seed=p["seed"], squash=1.65)
    if r.random() < 0.5:                       # 옆에 굴러 떨어진 조각
        add_dome(buf_rock, x + r.uniform(-1.1, 1.1) * s, z + r.uniform(-1.1, 1.1) * s,
                 FLOOR_Y, rx * 0.5, rz * 0.5, hh * 0.55,
                 n=5, seed=p["seed"] + 1, squash=1.5)
    if r.random() < 0.45:
        add_dome(buf_moss, x + r.uniform(-0.4, 0.4), z + r.uniform(-0.4, 0.4),
                 FLOOR_Y + hh * 0.72, rx * 0.55, rz * 0.5, 0.18,
                 n=5, seed=p["seed"] + 2, squash=0.6)


@prop_kind("thicket", col=None, h=3.2, tag="thicket",
           desc="막는 초목 덩어리. 거의 검은 암록 + 3m 이상이라 수풀과 안 헷갈린다")
def b_thicket(p):
    r = random.Random(p["seed"])
    s = p["scale"]
    x, z = p["x"], p["z"]
    hh = 3.2 * s * r.uniform(0.88, 1.18)
    rx = 1.30 * s * r.uniform(0.85, 1.12)
    add_dome(buf_leaf, x, z, FLOOR_Y + hh * 0.22, rx, rx * r.uniform(0.85, 1.15),
             hh * 0.82, n=6, seed=p["seed"], squash=0.95)
    if r.random() < 0.6:
        add_dome(buf_leaf, x + r.uniform(-0.7, 0.7), z + r.uniform(-0.7, 0.7),
                 FLOOR_Y + hh * 0.5, rx * 0.66, rx * 0.66, hh * 0.55,
                 n=5, seed=p["seed"] + 1, squash=0.9)
    add_prism(buf_bark, x, z, FLOOR_Y, FLOOR_Y + hh * 0.55,
              0.17 * s, 0.11 * s, 4, phase=r.uniform(0, 1))


@prop_kind("mound", col=None, h=2.1, tag="mound",
           desc="흙·이끼 둔덕. 막는 칸의 높이를 낮춰 지형에 기복을 준다")
def b_mound(p):
    r = random.Random(p["seed"])
    s = p["scale"]
    x, z = p["x"], p["z"]
    hh = 2.1 * s * r.uniform(0.8, 1.1)
    add_dome(buf_earth, x, z, FLOOR_Y, 1.45 * s * r.uniform(0.9, 1.15),
             1.45 * s * r.uniform(0.9, 1.15), hh, n=6, seed=p["seed"], squash=0.72)
    add_dome(buf_moss, x + r.uniform(-0.5, 0.5), z + r.uniform(-0.5, 0.5),
             FLOOR_Y + hh * 0.42, 0.95 * s, 0.85 * s, hh * 0.42,
             n=5, seed=p["seed"] + 1, squash=0.6)


@prop_kind("tree", col=("circle", 0.42), h=5.4, tag="tree",
           desc="나무. ★줄기만 막고 가지(CANOPY_)는 안 막는다. 밑을 지나가야 한다")
def b_tree(p):
    """slim=True 는 **걸어 다니는 땅에 서는 나무**다.
    ★탑다운에서 수관이 넓으면 그 밑에 들어간 캐릭터가 통째로 사라진다. 절벽 자락이나
      막는 칸에 서는 나무는 어차피 못 들어가니 넓어도 되지만, 초원에 심는 나무는
      수관을 좁히고 더 높이 올려서 플레이어를 안 덮게 한다."""
    r = random.Random(p["seed"])
    s = p["scale"]
    x, z = p["x"], p["z"]
    slim = p.get("slim")
    hh = 5.4 * s * r.uniform(0.82, 1.20) * (1.18 if slim else 1.0)
    add_prism(buf_bark, x, z, FLOOR_Y, FLOOR_Y + hh * (0.74 if slim else 0.66),
              0.42 * s, 0.24 * s, 5, phase=r.uniform(0, 1))
    kw = 0.62 if slim else 1.0
    for k in range(2):
        add_dome(buf_canopy,
                 x + r.uniform(-0.5, 0.5) * kw, z + r.uniform(-0.5, 0.5) * kw,
                 FLOOR_Y + hh * ((0.60 if slim else 0.46) + 0.18 * k),
                 (1.55 - 0.45 * k) * s * kw, (1.55 - 0.45 * k) * s * kw,
                 hh * 0.34 * (0.85 if slim else 1.0),
                 n=6, seed=p["seed"] + k, squash=0.85)


@prop_kind("bush", col=None, h=1.5, tag="bush",
           desc="숨는 수풀 한 덩이. 통과 가능·콜라이더 없음. BUSH_xx 메시로 나간다")
def b_bush(p):
    r = random.Random(p["seed"])
    s = p["scale"]
    b = p["buf"]
    if p.get("var") == "reed":                 # 갈대. 위에서 보면 수풀에 세로 악센트
        add_dome(b, p["x"], p["z"], FLOOR_Y, 0.34 * s, 0.34 * s, 2.2 * s,
                 n=5, seed=p["seed"], squash=1.15)
        return
    add_dome(b, p["x"], p["z"], FLOOR_Y,
             0.98 * s * r.uniform(0.85, 1.2), 0.98 * s * r.uniform(0.85, 1.2),
             1.5 * s * r.uniform(0.85, 1.15), n=6, seed=p["seed"], squash=0.85)


@prop_kind("log", col=("box", 2.4, 0.55), h=1.1, tag="log",
           desc="쓰러진 거목. 막는 건 90도 단위로만 눕힌다(축정렬 박스라서)")
def b_log(p):
    r = random.Random(p["seed"])
    s = p["scale"]
    x, z, yaw = p["x"], p["z"], p["yaw"]
    rad = 0.5 * s
    add_log(buf_bark, x, z, FLOOR_Y + rad * 0.92, 2.4 * s, rad, yaw, n=6)
    if r.random() < 0.6:                       # 부러진 가지 그루터기
        bx = x + math.cos(yaw) * 2.0 * s
        bz = z + math.sin(yaw) * 2.0 * s
        add_prism(buf_bark, bx, bz, FLOOR_Y + rad, FLOOR_Y + rad + 0.9 * s,
                  0.16 * s, 0.07 * s, 4, phase=r.uniform(0, 1))
    if r.random() < 0.5:
        # ★v79. 이끼 오프셋을 **통나무 축 기준**으로 돌린다. 예전에는 무조건 X 로만
        #   밀어서, 90도로 눕힌 통나무(여울목·보스 마당) 옆 허공 0.8m 높이에
        #   초록 판때기가 떠 있었다(QA b_01_enter 의 그 조각이 이거다).
        mo = r.uniform(-1.2, 1.2) * s          # 축 방향
        mp = r.uniform(-0.3, 0.3) * s          # 옆 방향
        add_dome(buf_moss,
                 x + math.cos(yaw) * mo - math.sin(yaw) * mp,
                 z + math.sin(yaw) * mo + math.cos(yaw) * mp,
                 FLOOR_Y + rad * 1.35, 0.5 * s, 0.35 * s, 0.22 * s,
                 n=5, seed=p["seed"] + 1, squash=0.6)


@prop_kind("standing_stone", col=("circle", 0.62), h=4.6, tag="gatepost",
           desc="선돌 4.6m. 어귀 표식(사람이 세운 흔적). 멀리서 창백하게 읽힌다")
def b_standing_stone(p):
    r = random.Random(p["seed"])
    s = p["scale"]
    x, z = p["x"], p["z"]
    hh = 4.6 * s * r.uniform(0.90, 1.10)
    ph = p["yaw"] + r.uniform(0, 0.4)
    add_prism(buf_stone, x, z, FLOOR_Y, FLOOR_Y + hh, 0.62 * s, 0.34 * s, 5,
              phase=ph)
    # ★v86. 보스 어귀에만 감는 붉은 끈. 굵은 줄 하나(16cm) + 가는 줄 하나(8cm).
    #   ★일부러 작다. 선돌을 통째로 붉게 칠하면 "폐허 = 창백한 회백색" 규칙이 깨져
    #     선돌이 랜드마크가 아니라 표지판이 된다. 끈만 물들인다.
    #   ★기둥과 같은 5각·같은 phase 로 감아야 면이 맞물린다. 반지름만 3% 키워
    #     Z-파이팅 없이 겉에 감긴다.
    if p.get("cord"):
        for (t0, bh) in ((0.62, 0.16), (0.76, 0.08)):
            rr = (0.62 + (0.34 - 0.62) * t0) * s            # 그 높이의 기둥 반지름
            add_prism(buf_cord, x, z, FLOOR_Y + hh * t0, FLOOR_Y + hh * t0 + bh,
                      rr * 1.03, rr * 1.02, 5, phase=ph)
    add_dome(buf_moss, x, z, FLOOR_Y + hh * 0.10, 0.58 * s, 0.58 * s, hh * 0.13,
             n=5, seed=p["seed"], squash=0.7)
    # 밑동에 괸 받침돌. 4.6m 짜리가 땅에 그냥 꽂혀 있으면 이쑤시개로 보인다
    for k in range(3):
        a = p["yaw"] + k * 2.09 + r.uniform(-0.3, 0.3)
        add_dome(buf_rock, x + math.cos(a) * 0.72 * s, z + math.sin(a) * 0.72 * s,
                 FLOOR_Y, 0.42 * s, 0.42 * s, 0.5 * s,
                 n=5, seed=p["seed"] + 7 + k, squash=1.4)


@prop_kind("stone_lantern", col=("circle", 0.46), h=1.9, tag="lantern",
           desc="무너진 석등. 폐허 흔적이자 엄폐물")
def b_stone_lantern(p):
    r = random.Random(p["seed"])
    x, z = p["x"], p["z"]
    broken = r.random() < 0.45
    add_prism(buf_stone, x, z, FLOOR_Y, FLOOR_Y + 0.16, 0.46, 0.40, 6)
    add_prism(buf_stone, x, z, FLOOR_Y + 0.16, FLOOR_Y + 0.95, 0.17, 0.15, 6)
    if broken:
        # 화사석이 떨어져 옆에 굴러 있다
        add_box(buf_stone, x + r.uniform(-0.9, 0.9), z + r.uniform(-0.9, 0.9),
                FLOOR_Y, FLOOR_Y + 0.42, 0.33, 0.30, rot=r.uniform(0, 1.5))
    else:
        add_box(buf_stone, x, z, FLOOR_Y + 0.95, FLOOR_Y + 1.42, 0.33, 0.33)
        add_pyramid(buf_stone, x, z, FLOOR_Y + 1.42, 0.33, 0.33, 0.34, ov=0.20)
        add_prism(buf_stone, x, z, FLOOR_Y + 1.76, FLOOR_Y + 1.98, 0.10, 0.03, 5)
    add_dome(buf_moss, x + r.uniform(-0.4, 0.4), z + r.uniform(-0.4, 0.4),
             FLOOR_Y, 0.5, 0.42, 0.16, n=5, seed=p["seed"], squash=0.5)


@prop_kind("stone_pillar", col=("circle", 0.62), h=1.8, tag="pillar",
           desc="부러진 석주. 옛 법당 터의 주춧돌. 보스 공터의 엄폐물")
def b_stone_pillar(p):
    r = random.Random(p["seed"])
    x, z = p["x"], p["z"]
    hh = p.get("hh", 1.8)
    add_prism(buf_stone, x, z, FLOOR_Y, FLOOR_Y + hh, 0.62, 0.50, 7,
              phase=r.uniform(0, 1))
    add_dome(buf_moss, x, z, FLOOR_Y + hh * 0.75, 0.5, 0.5, 0.22,
             n=5, seed=p["seed"], squash=0.6)


@prop_kind("pagoda", col=("circle", 2.2), h=13.1, tag="pagoda",
           desc="이끼 낀 석탑 13m. 맵 한가운데 랜드마크(맵에 1개). 5층 옥개석 + 상륜부")
def b_pagoda(p):
    """★탑 100층 중 1층이라는 걸 눈으로 알려주는 물건이다. 4.2m 짜리는 마당의
    소품으로 보였다. 13m 면 옆에 서면 화면 위끝까지 차오르고, 위에서 본 전체
    화면에서는 맵의 중심이 어디인지가 한눈에 잡힌다."""
    r = random.Random(p["seed"])
    x, z = p["x"], p["z"]
    # 기단 두 겹
    add_box(buf_stone, x, z, FLOOR_Y, FLOOR_Y + 0.28, 2.05, 2.05)
    add_box(buf_stone, x, z, FLOOR_Y + 0.28, FLOOR_Y + 0.58, 1.78, 1.78)
    y = FLOOR_Y + 0.58
    for tier in range(5):
        w = 1.52 - tier * 0.20
        add_box(buf_stone, x, z, y, y + 1.55, w, w)
        add_pyramid(buf_stone, x, z, y + 1.55, w, w, 0.62, ov=0.42)
        y += 2.17
    # 상륜부. 꼭대기에 가늘고 긴 실루엣이 있어야 '탑'으로 읽힌다
    add_prism(buf_stone, x, z, y, y + 0.34, 0.42, 0.30, 6)
    add_prism(buf_stone, x, z, y + 0.34, y + 1.55, 0.18, 0.05, 6)
    for k in range(3):                          # 보륜 세 겹
        add_prism(buf_stone, x, z, y + 0.5 + k * 0.32, y + 0.62 + k * 0.32,
                  0.34 - k * 0.07, 0.34 - k * 0.07, 8)
    # 이끼. 천 년 서 있었다는 신호
    for k in range(5):
        a = r.uniform(0, 6.28)
        add_dome(buf_moss, x + math.cos(a) * r.uniform(0.8, 1.9),
                 z + math.sin(a) * r.uniform(0.8, 1.9),
                 FLOOR_Y + r.choice((0.0, 0.28, 0.58)),
                 r.uniform(0.5, 0.9), r.uniform(0.5, 0.9), 0.22,
                 n=5, seed=p["seed"] + k, squash=0.6)
    # 발치에 무너진 돌덩이. 기단이 땅에서 솟은 것처럼 보이게 한다
    for k in range(6):
        a = k * 1.047 + r.uniform(-0.3, 0.3)
        add_dome(buf_rock, x + math.cos(a) * r.uniform(2.0, 2.9),
                 z + math.sin(a) * r.uniform(2.0, 2.9), FLOOR_Y,
                 r.uniform(0.4, 0.8), r.uniform(0.4, 0.8), r.uniform(0.3, 0.6),
                 n=5, seed=p["seed"] + 20 + k, squash=1.4)


@prop_kind("stone_slab", col=None, h=0.3, tag="slab",
           desc="너럭바위 단·부서진 돌계단. 무릎 아래라 안 막고 platforms[] 로 나간다")
def b_stone_slab(p):
    var = p.get("var", "shelf")
    x, z = p["x"], p["z"]
    if var == "exit":
        add_box(buf_exit, x, z, FLOOR_Y, p["y1"], p["hx"], p["hz"])
    else:
        # ★네모난 판떼기로 두면 아무리 자연물 사이에 놔도 콘크리트 패드로 보인다
        #   (첫 렌더에서 실제로 그랬다). 안쪽은 상자로 두되 **가장자리를 돌덩이로
        #   들쭉날쭉하게** 둘러 윤곽을 깬다. platforms[] 의 사각형은 그대로다.
        r = random.Random(p["seed"])
        hx, hz, y1 = p["hx"], p["hz"], p["y1"]
        # ★v79. 여울목 디딤돌은 **창백한 폐허 석재**로 깐다. 바위색(8a9199)으로 깔면
        #   "차갑고 어두우면 못 간다"는 이 맵의 색 규칙을 정면으로 어긴다
        #   (밟고 건너는 자리를 못 가는 색으로 칠하는 셈이다).
        #   창백한 회백색은 폐허에만 쓰는 색이라 "사람이 놓은 징검다리"로도 읽힌다.
        buf = (buf_earth if var == "earth"
               else buf_stone if var == "ford" else buf_rock)
        lump = 0.9 if var == "ford" else 1.4      # 여울목은 납작해야 밟게 생겼다
        add_box(buf, x, z, FLOOR_Y, y1, hx * 0.93, hz * 0.93)
        per = max(4, int((hx + hz) * 0.85))
        for k in range(per):
            t = k / float(per) * 4.0
            side = int(t)
            f = t - side
            if side == 0:
                dx, dz = -hx + 2 * hx * f, -hz
            elif side == 1:
                dx, dz = hx, -hz + 2 * hz * f
            elif side == 2:
                dx, dz = hx - 2 * hx * f, hz
            else:
                dx, dz = -hx, hz - 2 * hz * f
            add_dome(buf, x + dx * r.uniform(0.86, 1.0), z + dz * r.uniform(0.86, 1.0),
                     FLOOR_Y, r.uniform(0.45, 0.9), r.uniform(0.45, 0.9),
                     (y1 - FLOOR_Y) * r.uniform(lump, lump * 2.15),
                     n=5, seed=p["seed"] + k, squash=1.2)
        if p.get("moss", True):
            # ★v94 (심사 G7 "네온 초록 쿼드 = 플레이스홀더 수준"). 정찰로 정체가
            #   확정됐다: 여기서 굽는 이 이끼 돔이다. 반지름 0.5~1.1m 짜리 **5각 판**을
            #   높이 0.16m·squash 0.5 로 눕히니, 위에서 보면 캐릭터 발보다 큰
            #   납작한 오각형 한 장이 단 위에 얹힌 그림이 됐다. 세 가지를 고친다.
            #     ① 크기: 0.5~1.1m -> 0.16~0.42m. 이끼는 **얼룩**이지 판이 아니다
            #     ② 개수: 큰 것 두어 개 대신 작은 것 여럿(면적당 0.05 -> 0.34)
            #     ③ 모양: 정오각형(n=5) -> 6~9각 + 반지름 이방성. 정다각형은
            #        이 맵의 자연물 중 혼자 반듯해서 UI 판으로 읽힌다(v89 제단과 같은 함정)
            #     ★자리도 판 가운데가 아니라 **가장자리 쪽**으로 민다. 이끼는 물이
            #       고이는 턱과 틈에 낀다. 가운데 얹히면 데칼로 보인다.
            #   색은 7절에서 4a6636(어두운 암록)으로 같이 내렸다.
            for k in range(max(3, int(hx * hz * 0.34))):
                _a = r.uniform(0, 2 * math.pi)
                _e = r.uniform(0.55, 1.02)        # 0=중앙 1=테두리
                _rr = r.uniform(0.16, 0.42)
                add_dome(buf_moss, x + math.cos(_a) * hx * _e,
                         z + math.sin(_a) * hz * _e, y1,
                         _rr, _rr * r.uniform(0.6, 1.5), r.uniform(0.05, 0.11),
                         n=r.randint(6, 9), seed=p["seed"] + 40 + k,
                         squash=r.uniform(0.7, 1.4))


# ── 지형 5종 ★v91 ────────────────────────────────────────────
# 전부 **장식 전용**이다. col=None 이고 place(..., collide=False) 로만 부른다.
# 그래서 이 다섯 종을 아무리 심어도 colliders[] 는 한 줄도 안 늘어난다.
#   "그럼 뚫고 지나가지 않나" — 아니다. 다섯 다 **이미 막혀 있는 자리**를 덮는다.
#     cliff_tall  외곽 절벽 링 안쪽 면 (rampart 콜라이더가 이미 막는다)
#     outcrop     절벽 발치 / 너덜 덩어리 가장자리 (wall·boulderfield 콜라이더)
#     boulder_xl  기존 큰 바위를 **모양만** 갈아끼운다 (rock 콜라이더 그대로)
#     bank        개울 기슭 (stream 콜라이더 + 물칸)
#     slab        걸어 다니는 바닥에 까는 얇은 판석 (원래 안 막는 게 맞다)
# build 함수는 아무것도 안 한다. 모양은 web/props/<종류>.glb 가 갖고 있고
# 배치만 level1.json 의 props[] 로 나간다(EXTERNAL_KINDS -> build_props 가 건너뛴다).
def _external_only(p):
    raise RuntimeError("지형 종류는 이 glb 에 안 굽는다(web/props/*.glb)")


@prop_kind("cliff_tall", col=None, h=4.6, tag="cliff_tall",
           desc="절벽 기둥. 외곽 절벽 링 앞에 줄지어 서서 절차 절벽면을 가린다")
def b_cliff_tall(p):
    _external_only(p)


@prop_kind("outcrop", col=None, h=1.55, tag="outcrop",
           desc="낮은 노두. 절벽 발치·너덜 가장자리. 키 1.75 보다 낮아 건너편이 보인다")
def b_outcrop(p):
    _external_only(p)


@prop_kind("boulder_xl", col=None, h=1.9, tag="boulder_xl",
           desc="거대 바위. 랜드마크 자리의 rock 을 모양만 갈아끼운다(콜라이더는 rock 것)")
def b_boulder_xl(p):
    _external_only(p)


@prop_kind("bank", col=None, h=0.6, tag="bank",
           desc="강가 돌무더기 띠. 개울 기슭에 눕는다. 무릎보다 낮아 안 막는다")
def b_bank(p):
    _external_only(p)


@prop_kind("slab", col=None, h=0.15, tag="slab",
           desc="판석 패드. 폐허·석탑 마당·판석길 가장자리. 밟고 지나간다")
def b_slab(p):
    _external_only(p)


def build_props():
    for p in PROPS:
        if p["kind"] in EXTERNAL_KINDS:
            continue            # 모양은 web/props/<종류>.glb 가 갖고 있다
        PROP_KINDS[p["kind"]]["build"](p)


def emit_props_json():
    """게임이 InstancedMesh 로 심을 배치표. 좌표는 이미 three.js 기준이다.

    {kind, x, z, rotY, scale, sy}  (+ bush 는 어느 구역인지, tree 는 slim 여부)
      rotY : 모델이 한 벌뿐이라 회전이 유일한 변주다. 콜라이더가 원(rock·tree)이거나
             아예 없는(crag·thicket·bush) 종류뿐이라 마음대로 돌려도 충돌이 안 어긋난다
      sy   : 세로만 늘리는 배율. 가로는 scale 그대로여야 콜라이더와 안 어긋난다
    ★공용 rnd 를 쓰면 안 된다. 여기서 난수를 하나라도 더 뽑으면 그 뒤 배치가 통째로
      밀려서 콜라이더가 바뀐다. 프롭마다 자기 seed 로 따로 뽑는다.

    ★v91 에서 두 가지가 붙었다.
      rot : 회전을 **명시**한다(라디안). 지형 5종은 모델에 앞뒤가 있어서
            마음대로 돌리면 안 된다. 절벽 기둥은 자른 뒷면이 절벽을 봐야 하고,
            기슭 띠는 긴 축이 물가를 따라 누워야 한다. 안 적으면 종전대로 무작위다.
      as  : 이 프롭을 **다른 종류의 모양으로** 내보낸다(배치·콜라이더는 그대로).
            boulder_xl 이 이걸로 들어간다. 자세한 이유는 아래 ★모양만 교체 참고.
    """
    out = []
    for p in PROPS:
        if p["kind"] not in EXTERNAL_KINDS:
            continue
        kind = p.get("as") or p["kind"]
        r = random.Random(p["seed"] ^ 0x51DE)
        lo, hi = EXT_YJIT[kind]
        sy = r.uniform(lo, hi) * (1.18 if p.get("slim") else 1.0)
        # ★난수를 먼저 다 뽑고 나서 rot 를 덮어쓴다. 뽑는 횟수가 달라지면
        #   같은 seed 라도 sy 가 달라져서, rot 를 준 프롭만 높이가 튄다.
        rot = r.uniform(0.0, 2 * math.pi)
        if p.get("rot") is not None:
            rot = p["rot"]
        e = {"kind": kind,
             "x": round(p["x"], 3), "z": round(p["z"], 3),
             "rotY": round(rot % (2 * math.pi), 3),
             "scale": round(p["scale"], 3), "sy": round(sy, 3)}
        if kind == "bush":
            e["bush"] = p["buf"].name          # BUSH_01 .. BUSH_16
        elif kind == "tree" and p.get("slim"):
            e["slim"] = 1
        out.append(e)
    return out


def emit_prop_colliders():
    """★콜라이더는 모양이 아니라 **배치 테이블 + 종류 규격**에서 나온다.
    build 함수를 Meshy 에셋으로 갈아끼워도 충돌은 그대로다."""
    for p in PROPS:
        if not p["collide"]:
            continue
        k = PROP_KINDS[p["kind"]]
        s = p["scale"]
        h = k["h"] * s
        spec = k["col"]
        if spec[0] == "circle":
            push_col_circle(p["x"], p["z"], spec[1] * s, h, k["tag"])
        else:
            hx, hz = spec[1] * s, spec[2] * s
            if abs(math.sin(p["yaw"])) > 0.5:      # 90도로 눕힌 경우 축을 바꾼다
                hx, hz = hz, hx
            push_col_box(p["x"], p["z"], hx, hz, h, k["tag"])


# ─────────────────────────────────────────────────────────────
# 9) 막는 칸 -> 자연 지형 배치
# ─────────────────────────────────────────────────────────────
T_CRAG, T_THICKET, T_LOW = "crag", "thicket", "low"
T_MOUND, T_WATER, T_CLIFF = "mound", "water", "cliff"


def walkable(c, r):
    return 0 <= c < GRID and 0 <= r < GRID and grid[r][c] not in (W_, BLD)


def patch_noise(c, r, k=3, salt=0):
    """칸을 k x k 덩어리로 묶어 같은 값을 준다. 종류가 소금후추처럼 흩어지면
    지형이 아니라 잡음으로 보인다. 덩어리로 묶여야 '저쪽은 바위 지대'가 읽힌다."""
    return random.Random((c // k) * 7919 + (r // k) * 104729 + salt * 31).random()


boss_c0, boss_r0, boss_c1, boss_r1 = BOSS_ARENA
# ★종류를 난수로 뽑지 않는다. CLUMPS 표에 덩어리마다 적어 뒀다. 덩어리 하나가
#   통째로 같은 종류여야 "저건 너덜지대", "저건 덤불"로 읽힌다.
terr = {}
for r in range(GRID):
    for c in range(GRID):
        if grid[r][c] != W_:
            continue
        if is_outer(c, r):
            terr[(c, r)] = T_CLIFF
        elif (c, r) in WATER_CELLS:
            terr[(c, r)] = T_WATER
        else:
            terr[(c, r)] = CLUMP_KIND.get((c, r), T_CRAG)

# 여울목: 개울이 끊긴 세 자리. ★"물에 닿은 길 칸"으로 뽑으면 안 된다.
#   개울 남안을 따라 흙길이 지나가서 강변 전체가 여울목 색으로 칠해진다.
FORD = set(FORD_CELLS)


def wall_bias(c, r, amt=0.42):
    """열린 칸 쪽으로 안 튀어나오게 프롭 중심을 안쪽으로 민다.
    ★자연물이 통로 위로 넘치면 탑다운에서 플레이어가 가려진다."""
    dx = dz = 0.0
    for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if walkable(c + dc, r + dr):
            dx -= dc
            dz -= dr
    n = math.hypot(dx, dz)
    if n < 1e-6:
        return (0.0, 0.0)
    return (dx / n * amt, dz / n * amt)


# ── 막는 칸을 채운다: 코어 덩어리(지형) + 프롭(교체 대상) ──
# ★너덜(T_LOW)은 코어를 낮고 넓게 깐다. 위에서 보면 자갈밭이고 옆에서 보면
#   허리 위 높이의 돌무더기다. 여기 넘어서 못 가는데 건너편은 다 보인다.
CORE = {T_CRAG: (buf_rock, 1.42, 1.80, 1.30),
        T_THICKET: (buf_leaf, 1.42, 1.70, 1.05),
        T_LOW: (buf_rock, 1.52, 0.95, 1.60),
        T_MOUND: (buf_earth, 1.40, 1.55, 0.80)}
n_core = 0
n_gate_skip = 0
for r in range(GRID):
    for c in range(GRID):
        if grid[r][c] != W_ or is_outer(c, r):
            continue
        t = terr[(c, r)]
        if t == T_WATER:
            continue
        bx, bz = wall_bias(c, r)
        cx, cz = gx_of(c) + bx, gz_of(r) + bz
        cbuf, crad, chgt, csq = CORE[t]
        # 코어. 칸을 살짝 넘게 겹쳐 놔야 칸 사이에 틈이 안 보인다
        add_dome(cbuf, cx, cz, FLOOR_Y, crad, crad, chgt,
                 n=6, seed=(c * 131 + r * 17), squash=csq)
        n_core += 1
        # 프롭
        nprop = int(WALL_PROP_PER_CELL) + (1 if patch_noise(c, r, 1, 5) < (WALL_PROP_PER_CELL % 1) else 0)
        for k in range(nprop):
            jx = cx + rnd.uniform(-0.62, 0.62)
            jz = cz + rnd.uniform(-0.62, 0.62)
            # ★문설주 자리는 비운다. 안 비우면 4.6m 짜리 흰 석주가 바위를 관통해
            #   솟는다(QA terr_07_crag). 반지름은 종류별 실루엣 기준으로 넉넉히.
            if not gate_post_clear(jx, jz, 1.55 if t == T_CRAG else 1.35):
                n_gate_skip += 1
                continue
            if t == T_CRAG:
                place("crag", jx, jz, scale=rnd.uniform(0.85, 1.25))
            elif t == T_LOW:
                place("boulder", jx, jz, scale=rnd.uniform(0.75, 1.15))
            elif t == T_THICKET:
                if rnd.random() < 0.34:
                    place("tree", jx, jz, scale=rnd.uniform(0.80, 1.10), collide=False)
                else:
                    place("thicket", jx, jz, scale=rnd.uniform(0.85, 1.15))
            else:
                place("mound", jx, jz, scale=rnd.uniform(0.9, 1.3))

# ── 바위 언덕(옛 요사채 자리). 터 한가운데 우뚝해서 시야를 끊는다 ──
def rect_decompose(pred):
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
    """칸 사각형 -> (중심 gx, 중심 gz, 반너비 hx, 반너비 hz)"""
    x0 = -HALF + c0 * CELL
    x1 = -HALF + (c1 + 1) * CELL
    z0 = -HALF + r0 * CELL
    z1 = -HALF + (r1 + 1) * CELL
    return ((x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2)


for r in range(GRID):
    for c in range(GRID):
        if grid[r][c] != BLD:
            continue
        bx, bz = wall_bias(c, r, 0.34)
        cx, cz = gx_of(c) + bx, gz_of(r) + bz
        add_dome(buf_rock, cx, cz, FLOOR_Y, 1.5, 1.5, 2.3,
                 n=6, seed=(c * 71 + r * 29), squash=1.4)
        place("crag", cx + rnd.uniform(-0.4, 0.4), cz + rnd.uniform(-0.4, 0.4),
              scale=rnd.uniform(1.05, 1.35))
        if rnd.random() < 0.45:
            place("tree", cx + rnd.uniform(-0.5, 0.5), cz + rnd.uniform(-0.5, 0.5),
                  scale=rnd.uniform(0.9, 1.2), collide=False)

# ── 콜라이더: 칸 격자에서 나온다(모양과 무관) ──────────────
# ★종류마다 따로 쪼갠다. 콜라이더의 h 는 게임이 안 보지만(2D 검사), 여기 적힌
#   높이가 곧 "이걸 넘어서 볼 수 있는가"의 기록이라 정직하게 적어야 한다.
#   너덜(1.45)·개울(0.30)은 캐릭터 키 1.75 보다 낮다 = 건너편이 보인다.
COL_SPEC = {T_CRAG: (WALL_H, "wall"), T_THICKET: (3.2, "wall"),
            T_LOW: (LOW_H, "boulderfield"), T_MOUND: (2.1, "wall"),
            T_WATER: (0.30, "stream")}
wall_rects = []
for _t, (_h, _tag) in COL_SPEC.items():
    for (c0, r0, c1, r1) in rect_decompose(
            lambda c, r, _t=_t: grid[r][c] == W_ and not is_outer(c, r)
            and terr.get((c, r)) == _t):
        gx, gz, hx, hz = rect_world(c0, r0, c1, r1)
        push_col_box(gx, gz, max(0.55, hx - WALL_INSET), max(0.55, hz - WALL_INSET),
                     _h, _tag)
        wall_rects.append((c0, r0, c1, r1))
outer_rects = rect_decompose(lambda c, r: grid[r][c] == W_ and is_outer(c, r))
bld_rects = rect_decompose(lambda c, r: grid[r][c] == BLD)

for (c0, r0, c1, r1) in bld_rects:
    gx, gz, hx, hz = rect_world(c0, r0, c1, r1)
    push_col_box(gx, gz, hx - 0.30, hz - 0.30, KNOLL_H, "building")

# ── 외곽 절벽. 맵 경계를 실루엣으로 박는다 ──────────────────
# ★v86. 절벽을 **단(段)으로 쪼갰다.** QA(S7): "평평한 청회색 단색 = 회색 판".
#   원인이 둘이었다. (1) 결이 없다 -> 6b절 돌결 타일로 해결.
#   (2) 밑동에서 꼭대기까지 **꺾이는 자리가 하나도 없다.** 4m 짜리 면 한 장은
#       빛을 한 값으로만 받아서 무슨 텍스처를 입혀도 판때기로 읽힌다.
#   그래서 벽면을 세 단으로 끊고 단마다 안쪽으로 턱(RIDGE_LEDGE)을 물린다.
#   턱의 윗면은 하늘을 보고 벽면은 옆을 봐서 **한 벽에 밝기 여섯 단**이 생긴다.
# ★단 경계에서 정점을 공유하지 않는다. 공유하면 정점색이 부드럽게 이어져
#   "단 차이"가 아니라 그라데이션이 된다. 같은 자리에 링을 두 벌 두고 색을 끊는다.
# ★v89 (3차 QA S7 잔여 "절벽이 아직 평평하다"). v86 이 단을 셋으로 쪼갰는데도
#   판으로 보였다. 실측해 보니 이유가 숫자에 있었다.
#     - 턱이 0.13m 였다. 4m 벽에 0.13m 물림이면 화면에서 3px 다. 단이 있다는 걸
#       실루엣이 알 수가 없다 -> 0.42m(3.2배). 3단 합쳐 0.84m 계단이 된다
#     - 단 사이 밝기 차가 0.63~1.00 을 세 단으로 나눠 단당 0.12 뿐이었다.
#       0.50~1.00 + 아랫도리 0.70 으로 벌려 단당 0.17, 턱 밑 그늘까지 0.35 로 키웠다
#     - 마루가 sin 두 겹이라 **매끈한 파도**였다. 위에서 보면 자로 그은 곡선이다.
#       3~4개씩 묶은 블록마다 높이를 따로 뽑아 **들쭉날쭉한 능선**으로 바꿨다
#       (정점마다 난수로 흔들면 꼭대기 부채꼴이 방사형 빛줄기가 된다는 v86 함정은
#        블록 안에서는 높이가 같으므로 안 밟는다. 블록 경계에서만 각이 선다)
RIDGE_BANDS = 3
RIDGE_LEDGE = 0.42        # 단마다 안으로 물리는 턱 폭(m)
RIDGE_SHADE = (0.50, 1.00)   # 밑동 ~ 꼭대기 명암 곱수(정점색). 1.0 을 넘기면 안 된다
RIDGE_FOOT = 0.78         # 단마다 **아랫도리**를 한 번 더 누른다(턱 밑 그늘)
# ★v94. 0.70 -> 0.78. 턱 밑이 어두운 것 자체는 맞지만(실제로 그늘진다) 30% 낙차는
#   너무 급해서 "그늘"이 아니라 "선"으로 읽혔다(심사 G6). 22% 로 눅인다.
RIDGE_TJIT = 0.075        # 단 경계 높이를 블록마다 흔드는 폭(높이 비율). 자로 그은
#                           가로줄을 깬다. 0.10 을 넘기면 단이 서로 넘나들어 면이 꼬인다
RIDGE_BLOCK = 3           # 마루 높이를 같이 쓰는 정점 수(이 단위로 능선이 꺾인다)
RIDGE_BLOCK_H = (0.84, 1.19)   # 블록별 마루 높이 곱수. 최저여도 2.2m > 캐릭터 1.75


def add_ridge(buf, gx, gz, hx, hz, h, seed, step=2.4, lean=0.6, bands=RIDGE_BANDS):
    """사각 footprint 를 따라 도는 능선. 밑동은 흔들고 꼭대기는 안으로 기울인다.
    상자로 두면 '담장'이 되지만 이렇게 두르면 '절벽면'이 된다.
    삼각형 (4*bands - 1) * n.

    ★함정: 중심에서 비례로 줄이면(radial shrink) 96m 짜리 긴 사각형이
      끝에서 4m 씩 안으로 말려 들어가 맵 구석에 구멍이 난다. 그래서 **경계에 닿은
      좌표만** 안쪽으로 민다."""
    r = random.Random(seed)
    pts = []
    per = [(-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)]
    for i in range(4):
        ax, az = per[i]
        bx2, bz2 = per[(i + 1) % 4]
        seg = math.hypot(bx2 - ax, bz2 - az)
        n = max(1, int(seg / step))
        for k in range(n):
            t = k / float(n)
            pts.append((ax + (bx2 - ax) * t, az + (bz2 - az) * t))

    def inset(dx, dz, ax_, az_):
        nx, nz = dx, dz
        if abs(abs(dx) - hx) < 1e-6:
            nx = math.copysign(max(0.25, hx - ax_), dx)
        if abs(abs(dz) - hz) < 1e-6:
            nz = math.copysign(max(0.25, hz - az_), dz)
        return nx, nz

    bx, by = gx, -gz
    n = len(pts)
    ph = r.uniform(0, 6.283)
    # 점마다 밑동 흔들림·기울임·꼭대기 높이를 미리 뽑아 둔다(단마다 다시 뽑으면 어긋난다)
    jit = [(r.uniform(0.0, 0.22), r.uniform(0.0, 0.22),
            lean * r.uniform(0.7, 1.6), lean * r.uniform(0.7, 1.6)) for _ in pts]
    # ★꼭대기 높이. 큰 흐름은 파도(sin 두 겹)로 주고, 그 위에 **블록 단위 단차**를
    #   얹는다(v89). 파도만 쓰면 마루가 자로 그은 곡선이라 위에서 봤을 때 판으로
    #   읽힌다. 정점마다 난수로 흔드는 건 여전히 금지다 — 꼭대기 부채꼴이 길쭉한
    #   삼각형이라 법선이 정점마다 튀면 위에서 흰 빛줄기가 방사로 찍힌다(v86 함정).
    #   블록 안에서는 높이가 같아서 부채꼴 법선이 안 튀고, 블록 경계에서만 각이 선다.
    nblk = n // RIDGE_BLOCK + 2
    blk = [r.uniform(*RIDGE_BLOCK_H) for _ in range(nblk)]
    tops = [FLOOR_Y + h * (0.90 + 0.17 * math.sin(i * 0.55 + ph)
                           + 0.09 * math.sin(i * 0.21 + ph * 2))
            * blk[i // RIDGE_BLOCK] for i in range(n)]

    # ★v94 (심사 G6 "가로 이음매 선명"). 정찰로 정체가 확정됐다 — UV 이음매가
    #   아니라 **여기서 굽는 단 경계**다. 단 셋이 전부 높이 비율 1/3·2/3 에 정확히
    #   놓이고 그 자리에서 정점색이 30% 뚝 떨어지니(아래 RIDGE_FOOT), 링 전체를
    #   가로지르는 자로 그은 어두운 줄 두 개가 생겼다.
    #   턱 밑이 어두운 것 자체는 맞다(실제로 그늘진다). 문제는 **높이가 한 줄로
    #   똑같다**는 것이다. 그래서 단 경계를 정점마다 흔든다. 흔들림은 블록 단위라
    #   부채꼴 법선이 튀지 않는다(v86 함정과 같은 이유로 정점 단위 난수는 금지).
    bjit = [r.uniform(-RIDGE_TJIT, RIDGE_TJIT) for _ in range(nblk)]
    bjit2 = [r.uniform(-RIDGE_TJIT, RIDGE_TJIT) for _ in range(nblk)]

    def t_of(i, k, which):
        """정점 i 의 단 k 경계 높이 비율. which 0=아래 링 1=위 링"""
        base = (k + which) / float(bands)
        if k + which in (0, bands):
            return base                       # 밑동과 꼭대기는 흔들지 않는다
        j = (bjit if (k + which) % 2 else bjit2)[i // RIDGE_BLOCK % nblk]
        return min(0.98, max(0.02, base + j))

    def ring(ts, extra):
        """정점별 높이 비율 ts[i] 자리의 링을 쌓고 시작 인덱스를 준다. extra = 추가 안쪽 물림"""
        b0 = len(buf.v)
        for i, (dx, dz) in enumerate(pts):
            j0, j1, l0, l1 = jit[i]
            t = ts[i]
            nx, nz = inset(dx, dz, j0 + (l0 - j0) * t + extra,
                           j1 + (l1 - j1) * t + extra)
            buf.v.append((bx + nx, by - nz, FLOOR_Y + (tops[i] - FLOOR_Y) * t))
        return b0

    s0, s1 = RIDGE_SHADE
    prev_top = None
    for k in range(bands):
        ts0 = [t_of(i, k, 0) for i in range(n)]
        ts1 = [t_of(i, k, 1) for i in range(n)]
        # 단 하나의 아래 링 / 위 링. 아래 링은 턱 밑이라 한 번 더 누른다
        a0 = ring(ts0, k * RIDGE_LEDGE)
        buf.c += [(s0 + (s1 - s0) * ts0[i]) * RIDGE_FOOT for i in range(n)]
        a1 = ring(ts1, k * RIDGE_LEDGE)
        buf.c += [s0 + (s1 - s0) * ts1[i] for i in range(n)]
        # ★감기 방향 함정: 게임 좌표 gz 를 블렌더 y 로 넣을 때 부호가 뒤집힌다(by = -gz).
        #   그래서 (dx, dz) 순서로 도는 둘레는 블렌더에서 **시계 방향**이 되고,
        #   순진하게 감으면 면이 전부 안쪽을 향한다(위에서 보면 시커먼 구멍).
        for i in range(n):
            j = (i + 1) % n
            buf.f.append((a0 + i, a1 + i, a1 + j, a0 + j))
        if prev_top is not None:
            # 턱의 윗면. 바깥 링(prev_top) -> 안쪽 링(a0). 하늘을 봐야 한다
            for i in range(n):
                j = (i + 1) % n
                buf.f.append((a0 + i, a0 + j, prev_top + j, prev_top + i))
        prev_top = a1
    ctr = len(buf.v)
    buf.v.append((bx, by, sum(tops) / len(tops)))
    buf.c.append(s1)
    for i in range(n):                                        # 꼭대기 부채꼴
        j = (i + 1) % n
        buf.f.append((ctr, prev_top + j, prev_top + i))


# ★lean 을 0.60 -> 0.22 로 눕혔다. 꼭대기가 안으로 4m 씩 말려 들어오면 위에서 봤을 때
#   맵이 좁아 보이고 옆에서 보면 짓누른다. 거의 수직으로 세우면 같은 높이인데도 트인다.
for (c0, r0, c1, r1) in outer_rects:
    gx, gz, hx, hz = rect_world(c0, r0, c1, r1)
    add_ridge(buf_cliff, gx, gz, hx + 0.05, hz + 0.05, CLIFF_H,
              seed=int(gx * 7 + gz * 13), lean=0.22)
    push_col_box(gx, gz, hx + 0.05, hz + 0.05, CLIFF_H, "rampart")

# 절벽 안쪽 면에 바위와 나무를 붙인다. 밋밋한 벽면이 아니라 산자락으로 보이게
n_edge = 0
for r in range(GRID):
    for c in range(GRID):
        if grid[r][c] != W_ or not is_outer(c, r):
            continue
        opens = [(dc, dr) for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1))
                 if walkable(c + dc, r + dr)]
        if not opens:
            continue
        dc, dr = opens[rnd.randrange(len(opens))]
        # ★0.42칸까지 밀면 절벽 콜라이더 밖으로 1m 가까이 삐져나와 바위를 뚫고 걷게 된다
        ex = gx_of(c) + dc * CELL * 0.26 + rnd.uniform(-0.5, 0.5)
        ez = gz_of(r) + dr * CELL * 0.26 + rnd.uniform(-0.5, 0.5)
        place("rock", ex, ez, scale=rnd.uniform(0.7, 1.0), collide=False)
        n_edge += 1
        if n_edge % 2 == 0:          # 절벽 위에 숲. 경계가 '벽'이 아니라 '산자락'으로 보인다
            place("tree", gx_of(c) + dc * CELL * 0.15, gz_of(r) + dr * CELL * 0.15,
                  scale=rnd.uniform(0.95, 1.35), collide=False)

print("[지형] 막는 칸 코어 %d / 절벽 rect %d / 절벽자락 프롭 %d / 문설주 자리라 건너뛴 프롭 %d" %
      (n_core, len(outer_rects), n_edge, n_gate_skip))

# ── 절벽 너머의 옅은 봉우리 ★v86 에서 걷어냈다 ──────────────
# QA(v84)가 "흰 다각형 파편"이라고 부른 게 이것이다. 정체는 DECO_HAZE1/2/3,
# 제일 바깥 줄 42자리에 세운 5각 뿔(색 9fb3bd / bccbd3 / **d5dfe4**)이었다.
#   - 만든 이유: "절벽 너머는 아득하게". 그때는 경계 밖에 아무것도 없었다
#   - 지금은 v79 배후 스커트(바깥 26m 비탈 + 바위 96 + 숲 136그루)가 그 자리를 채운다.
#     뿔은 그 앞으로 튀어나와 **회색 비탈 위에 붙은 흰 종잇조각**으로만 보였다
#     (57_camp2 왼쪽, 170_west_edge 왼쪽 아래, north_edge 위쪽 한가운데)
#   - 게다가 맵에서 제일 밝은 색(d5dfe4)이라 "폐허 = 창백한 회백색" 규칙까지 갉아먹었다.
#     선돌(cfd3cd)보다 밝은 물건이 경계에 42개 서 있으면 랜드마크가 안 튄다
# 그래서 통째로 뺐다. 삼각형 672개도 같이 돌려받아 절벽 단 쪼개기에 썼다.
print("[안개] 절벽 위 옅은 봉우리 폐기(v86). 배후 스커트가 그 자리를 대신한다")

# ── 경계 바깥 배후 스커트 ★맵 밖 회색 공백을 막는다 ─────────
# 고정 카메라는 플레이어 **뒤 3.6m**, 가로로 가까운 줄 ±8.4m / 먼 줄 ±12.0m 를 본다.
# 경계 가까이 서면 그 범위가 맵 밖으로 나가면서 하늘색 배경이 그대로 화면에 찍힌다
# (QA #8: 화면 하단 25~30%). 스폰을 안으로 물려서 대부분 없앴지만 어귀·EXIT_2 처럼
# 경계에 붙어 있는 지점이 남는다. 그래서 경계 **바깥**에 지면을 이어 붙인다.
#
# ★예전에 폐기한 "맵 밖 60~150m 안개 능선"과 헷갈리면 안 된다. 그건 멀고 높아서
#   가장자리 스폰에서 화면을 통째로 가렸다. 이건 경계에 딱 붙어서 바깥으로 26m 만
#   뻗고 7.6m 까지만 올라간다. 계산해 보면(카메라 높이 19.3m, 화면 위 끝 25.4m)
#   경계에서 6m 안에 서 있을 때 화면 맨 위 10% 안쪽에만 들어온다. 눈으로도 확인했다.
SKIRT_W = 26.0        # 바깥으로 뻗는 폭
SKIRT_H = 7.6         # 바깥 끝 높이 (안쪽 절벽 4.0 보다 3.6 높다)


# 경계에서 바깥으로의 거리 비율과 그 자리의 높이 비율.
# ★한 장짜리 평면으로 뽑았다가 다시 걷어냈다. 회색 공백은 안 보이는데 이번에는
#   **매끈한 회색 비탈**이 화면 옆을 채워서 결국 "텍스처 없는 면"과 같아 보였다.
#   띠를 다섯 줄로 쪼개 마디마다 높이·깊이를 흔들면 면이 꺾이면서 음영이 생긴다.
SKIRT_BANDS = ((0.00, 0.00), (0.13, 0.26), (0.33, 0.58), (0.62, 0.86), (1.00, 1.00))
# ★v86. 줄마다 정점색(명암 곱수)을 다르게 준다. 경계에 가까운 줄일수록 어둡다.
#   경계 바로 밖은 절벽 그늘에 잠기고 멀수록 하늘을 받는다 = 안쪽 절벽과 배후 산자락이
#   **밝기로 갈린다.** 이게 "한 겹 더 뒤"를 색이 아니라 빛으로 말하는 장치다.
SKIRT_SHADE = (0.66, 0.80, 0.90, 0.97, 1.00)


# v94 seg 3.6 -> 2.4. 정찰 실측: EXIT_2 에 서면 **화면의 41.9%가 맵 밖 스커트**이고
#   그게 매끈한 회색 판으로 읽힌다(심사 G6 "배경 판 그대로 노출").
#   흔들림 진폭은 그대로 두고 **마디만 잘게** 쪼갠다. 진폭을 키우면 위에 앉힌
#   나무·바위가 뜨는데(skirt_y 는 평균 높이만 안다), 마디를 잘게 하면 같은 진폭에서
#   면이 더 자주 꺾여 음영이 는다 = 판이 아니라 비탈로 읽힌다.
def r_n(seed):
    """면 수를 5~8 로 흩는다. 정오각뿔이 96개 늘어서면 그것 자체가 반복 무늬가 된다"""
    return 5 + (seed % 4)


def add_skirt(buf, axis, sign, seg=2.4):
    """경계 한 변에 붙는 바깥 비탈. axis 0 = 동서(x 경계), 1 = 남북(z 경계).
    ★네 변을 모서리 너머까지 길게 뽑아 서로 겹치게 한다. 겹치는 건 안 보이지만
      벌어지면 맵 네 귀퉁이에 회색 삼각형이 뚫린다(그게 원래 증상이다).
    ★맨 안쪽 줄은 경계보다 0.8m 안으로, 바닥보다 5cm 아래로 넣는다. 바닥 메시와
      같은 높이로 맞대면 시야가 스칠 때 실 같은 틈이 번쩍인다."""
    ext = HALF + SKIRT_W
    n = max(4, int(2 * ext / seg))
    r = random.Random(9100 + axis * 17 + (1 if sign > 0 else 0))
    base = len(buf.v)
    for bi, (bu, bh) in enumerate(SKIRT_BANDS):
        for i in range(n + 1):
            t = -ext + 2 * ext * i / n
            if bi == 0:
                u, hh, tt = -0.8, FLOOR_Y - 0.05, t
            else:
                u = (SKIRT_W * bu + r.uniform(-1.1, 1.1)
                     + 1.3 * math.sin(i * 0.55 + bi * 1.7))
                hh = (FLOOR_Y + SKIRT_H * bh + r.uniform(-0.6, 0.8)
                      + 0.6 * math.sin(i * 0.37 + bi))
                tt = t + r.uniform(-0.8, 0.8)
            if axis == 0:
                buf.v.append((sign * (HALF + u), -tt, hh))
            else:
                buf.v.append((tt, -sign * (HALF + u), hh))
            # 같은 줄 안에서도 마디마다 살짝 흔든다. 줄 전체가 한 값이면 띠가 생긴다
            buf.c.append(SKIRT_SHADE[bi] * (0.94 + 0.06 * math.sin(i * 0.83 + bi * 2.1)))
    for bi in range(len(SKIRT_BANDS) - 1):
        for i in range(n):
            a = base + bi * (n + 1) + i
            b = a + (n + 1)
            buf.f.append((a, b, b + 1, a + 1))
    return n


def skirt_y(u):
    """경계에서 u m 바깥일 때의 대략적인 지면 높이(위에 물건을 앉힐 때 쓴다)."""
    for k in range(1, len(SKIRT_BANDS)):
        u0, h0 = SKIRT_BANDS[k - 1]
        u1, h1 = SKIRT_BANDS[k]
        if u <= SKIRT_W * u1 or k == len(SKIRT_BANDS) - 1:
            f = (u / SKIRT_W - u0) / max(1e-6, u1 - u0)
            return FLOOR_Y + SKIRT_H * (h0 + (h1 - h0) * max(0.0, min(1.0, f)))
    return FLOOR_Y


def add_skirt_tree(gx, gz, y0, s, seed):
    """배후 스커트 위의 숲. 실루엣만 필요한 물건이라 최소 폴리곤으로 짠다."""
    r = random.Random(seed)
    hh = 5.4 * s * r.uniform(0.8, 1.25)
    add_prism(buf_bark, gx, gz, y0 - 1.2, y0 + hh * 0.5, 0.22 * s, 0.14 * s, 4,
              phase=r.uniform(0, 1))
    for k in range(2):
        add_dome(buf_skirtwood, gx + r.uniform(-0.4, 0.4) * s,
                 gz + r.uniform(-0.4, 0.4) * s,
                 y0 + hh * (0.34 + 0.24 * k), 1.7 * s, 1.7 * s, 2.0 * s,
                 n=4, seed=seed + k, squash=0.85)


n_skirt_tree, n_skirt_rock = 0, 0
for _ax in (0, 1):
    for _sg in (-1, 1):
        add_skirt(buf_skirt, _ax, _sg)
        _rs = random.Random(4400 + _ax * 131 + (7 if _sg > 0 else 3))

        def _place_on_skirt(u, t, fn):
            if _ax == 0:
                fn(_sg * (HALF + u), t)
            else:
                fn(t, _sg * (HALF + u))

        # 바위 노두. 매끈한 비탈에 그림자를 만드는 게 목적이라 경계 가까이 깐다
        # v94. 24 -> 40. 매끈한 비탈을 깨는 게 목적인데 24개로는 성겼다
        for _k in range(40):
            _u = _rs.uniform(0.8, SKIRT_W * 0.62)
            _t = _rs.uniform(-(HALF + SKIRT_W), HALF + SKIRT_W)
            _rr2 = _rs.uniform(1.6, 3.6)
            _hh2 = _rs.uniform(1.4, 3.4)
            _sd = _rs.randrange(10 ** 6)
            _place_on_skirt(
                _u, _t,
                lambda x, z, a=_rr2, b=_hh2, c=_sd, d=_u:
                add_dome(buf_skirtrock, x, z, skirt_y(d) - 0.9, a, a, b,
                         n=r_n(c), seed=c, squash=1.35))
            n_skirt_rock += 1
        # 배후 숲. 경계에서 가까운 쪽에 몰아야 카메라에 실제로 들어온다
        # v94. 34 -> 46. 그리고 밑동을 0.8m 내려 심는다 — 정찰에서 배후 숲이
        #   "떠 있는 초록 다각형"으로 찍혔다(skirt_y 는 줄 평균이라 실제 지면이
        #   그보다 낮은 자리가 생긴다. 묻히는 건 안 보이지만 뜨는 건 보인다)
        for _k in range(46):
            _u = _rs.uniform(1.5, SKIRT_W * 0.72)
            _t = _rs.uniform(-(HALF + SKIRT_W), HALF + SKIRT_W)
            _sc2 = _rs.uniform(0.8, 1.35)
            _sd = _rs.randrange(10 ** 6)
            _place_on_skirt(
                _u, _t,
                lambda x, z, a=_sc2, c=_sd, d=_u:
                add_skirt_tree(x, z, skirt_y(d) - 0.8, a, c))
            n_skirt_tree += 1
print("[스커트] 경계 바깥 비탈 4변 (폭 %.0fm 높이 %.1fm) / 바위 %d / 배후 숲 %d그루"
      % (SKIRT_W, SKIRT_H, n_skirt_rock, n_skirt_tree))


# ─────────────────────────────────────────────────────────────
# 10) 물: 개울과 웅덩이
# ─────────────────────────────────────────────────────────────
# ★수면은 바닥보다 겨우 1cm 위에 둔다. 파 내려가면 main.js 쪽 바닥과 어긋나고
#   pitch 0.90 카메라에서는 깊이가 어차피 안 읽힌다. 못 건넌다는 신호는
#   **양쪽 기슭을 두르는 바위**가 준다.
#
# ★v86 (QA S11 "물 평면 가장자리 삐져나옴"). 인셋이 0.55m 였는데도 직사각형이
#   흙 위에 얹혀 보였다. 원인이 인셋 하나가 아니었다.
#   (1) 바닥에 칠하는 칸 경계는 저주파 노이즈로 **휘어 있다**(WARP 0.20 = 0.64m).
#       수면 메시는 휘지 않는 직사각형이라 칠한 물길이 안으로 굽은 자리에서
#       파란 판이 흙 위로 삐져나온다
#   (2) 바닥은 발치 그늘·잔결에 눌려 어두운데 수면 메시만 반짝여서, 같은 파랑인데도
#       두 겹으로 갈라져 보였다
#   셋 다 고쳤다: 인셋 0.55 -> 0.80(휨 폭 0.64 를 넘긴다), 수면 색·거칠기를 칠한
#   색에 맞춰 눌렀다(7절 M_WATER), 그리고 물칸 **안쪽 가장자리**에 젖은 그늘 띠를
#   칠해 메시 가장자리를 덮는다(15절 _rim_in).
WATER_INSET = 0.80
WATER_FEATHER = 0.55      # 가장자리를 어둡게 죽이는 폭(m)
WATER_EDGE_SHADE = 0.52   # 가장자리 정점색. 칠한 개울(그늘 먹은 값)에 맞춘 값이다

# ★v89 (3차 QA S8 잔여 "개울이 파란 직사각 상자"). v86 은 수면을 물칸 사각형마다
#   3x3 판으로 깔았다. 인셋과 페더로 **가장자리 밝기**는 죽였지만 모양은 그대로
#   축정렬 직사각형이라, 90도 모서리와 칼로 자른 끝단이 남았다
#   (증거 BEFORE_D_ford_m.png / BEFORE_D3_stream_end.png).
#   그래서 수면을 **중심선을 따라 흐르는 리본**으로 다시 짰다.
#     - 중심선은 열 중심의 행 값을 smoothstep 으로 이어 굽는다 = 사행(蛇行)
#     - 반폭이 자리마다 다르다(안쪽으로만 파고든다) = 들쭉날쭉한 기슭
#     - 여울목에 닿는 끝단은 4분타원으로 코를 둥글리고 그 앞에 자갈톱을 깐다
#     - 절벽에 닿는 끝단은 오히려 0.5m 더 밀어 넣어 바위 밑으로 사라지게 한다
#   ★물칸 격자(WATER_CELLS)와 콜라이더는 한 칸도 안 건드린다. 모양만 바뀐다.
#   ★인셋 예산. 바닥에 칠하는 칸 경계는 저주파 노이즈로 최대 0.64m 휜다(15절 WARP).
#     리본이 중심선에서 벗어나는 최대치 = 반폭 0.80 + 잔사행 0.10 = 0.90m 이고
#     칸 반폭이 1.60m 이므로 남는 여유가 0.70m 다. 휨 폭 0.64m 를 넘긴다 =
#     v86 이 고친 "파란 판이 흙 위로 삐져나옴"이 되돌아올 수 없다.
#     아래 자기 검증이 실제 정점으로 이 여유를 다시 잰다(눈이 아니라 숫자로).
STREAM_STEP = 0.80        # 길이 방향 표본 간격(m)
STREAM_HALF = 0.80        # 반폭 상한(m)
STREAM_WAVE = 0.22        # 기슭 들쭉날쭉 폭. **안쪽으로만** 판다(밖으로 안 넘친다)
STREAM_MEANDER = 0.10     # 중심선 잔사행(m)
STREAM_CAP = 1.30         # 여울목 쪽 둥근 코 길이(m)
STREAM_INTO_CLIFF = 0.50  # 절벽 밑으로 밀어 넣는 길이(m)


def _bank_wave(x, side):
    """기슭 요철. 주기가 다른 사인을 겹쳐 0~1 을 만든다.
    ★난수가 아니라 좌표의 함수다. 같은 자리는 늘 같은 값이라 구간을 나눠 구워도
      이음매가 안 벌어진다.
    ★v94. 심사 지적 "자로 그은 직선 경계". 두 사인(5.5m/2.3m)만으로는 주기가
      너무 규칙적이라 물결이 **파형**으로 읽혔다. 서로 무리수 비에 가까운 네 마디로
      늘려 되풀이 주기를 사실상 없앤다. 진폭 배분은 그대로 합이 1 이라
      STREAM_WAVE 예산(0.22m)을 한 톨도 안 넘긴다 = 아래 여유 검증이 그대로 통과한다."""
    return (0.42 * (0.5 + 0.5 * math.sin(x * 1.15 + side * 2.10))
            + 0.26 * (0.5 + 0.5 * math.sin(x * 2.70 + side * 4.70))
            + 0.20 * (0.5 + 0.5 * math.sin(x * 4.37 + side * 1.31))
            + 0.12 * (0.5 + 0.5 * math.sin(x * 7.93 + side * 5.55)))


def add_stream_ribbon(seg, y, cap_lo, cap_hi):
    """개울 한 구간. seg = [(열, 행), ...] (열 오름차순).
    cap_lo / cap_hi = 서쪽 / 동쪽 끝을 둥글릴 것인가(여울목이면 True, 절벽이면 False).
    삼각형 = 표본수 x 6.

    ★감기 방향: 블렌더는 y = -gz 라 게임 z 가 커지면 블렌더 y 는 작아진다.
      '+x 로 갔다가 +y 로' 도는 순서를 지켜야 면이 하늘을 본다(안 그러면 시커멓다)."""
    c0 = seg[0][0]
    us = [c + 0.5 for (c, _r) in seg]        # 열 중심의 연속 열좌표(x = -HALF + u*CELL)
    rs = [float(_r) for (_c, _r) in seg]

    def row_at(u):
        """★행이 바뀌는 전환을 **그 열 한 칸 안에서** 끝낸다.
        열 중심끼리 이으면 전환이 앞 열의 오른쪽 절반까지 번지는데, 앞 열에는
        새 행의 물칸이 없어서 리본이 기슭에 0.03m 까지 붙어 버린다(실측).
        WATER_CELLS 는 행이 바뀌는 열에 **두 행을 다 채워** 두므로(3절의 그 for 문),
        전환을 그 열 안에 가두면 어디서나 여유가 (1.6 - 반폭)m 로 일정해진다."""
        i = int(math.floor(u)) - c0
        i = max(0, min(len(rs) - 1, i))
        t = min(1.0, max(0.0, u - (c0 + i)))
        t = t * t * (3.0 - 2.0 * t)          # smoothstep
        prev = rs[i - 1] if i > 0 else rs[i]
        return prev + (rs[i] - prev) * t

    # 구간의 x 범위. 여울목 쪽은 인셋만큼 물러서고 절벽 쪽은 오히려 밀어 넣는다
    x_lo = -HALF + (us[0] - 0.5) * CELL + (WATER_INSET if cap_lo else -STREAM_INTO_CLIFF)
    x_hi = -HALF + (us[-1] + 0.5) * CELL - (WATER_INSET if cap_hi else -STREAM_INTO_CLIFF)
    n = max(4, int(round((x_hi - x_lo) / STREAM_STEP)))
    base = len(buf_water.v)
    for k in range(n + 1):
        x = x_lo + (x_hi - x_lo) * k / float(n)
        u = (x + HALF) / CELL
        zc = -HALF + (row_at(u) + 0.5) * CELL + STREAM_MEANDER * math.sin(x * 0.83 + 1.7)
        # 끝단 코. 4분타원이라 뾰족하지 않고 둥글게 닫힌다
        nose = 1.0
        if cap_lo:
            s = min(1.0, (x - x_lo) / STREAM_CAP)
            nose = min(nose, math.sqrt(max(0.0, 1.0 - (1.0 - s) ** 2)))
        if cap_hi:
            s = min(1.0, (x_hi - x) / STREAM_CAP)
            nose = min(nose, math.sqrt(max(0.0, 1.0 - (1.0 - s) ** 2)))
        nose = max(0.07, nose)               # 완전히 0 이면 사면이 겹쳐 퇴화한다
        # ★v94. 단면 표본을 4점 -> 8점으로 늘렸다. 심사 지적 "깊이 그라데이션 전무".
        #   깊이·포말은 web/level.js 의 수면 셰이더가 **기슭까지의 정규화 거리 t** 로
        #   그리는데, 그 t 를 UV 의 v 로 실어 보낸다. 4점(0,1,1,0)이면 가운데가
        #   통짜 평지라 그라데이션을 만들 자리가 없다. 0/0.30/0.68/1 네 계단이면
        #   물가는 얕고 중심은 깊은 단면이 정점 보간만으로 나온다.
        # ★UV 로 싣는 이유: 정점색(COLOR_0)에 넣으면 셰이더 패치가 실패했을 때
        #   물이 통째로 빨강·초록으로 뜬다. UV 는 맵이 없으면 아무 색도 안 바꾼다
        #   = 실패해도 v93 그림 그대로다.
        row = []
        for side in (-1, 1):
            hw = (STREAM_HALF - STREAM_WAVE * _bank_wave(x, side)) * nose
            f = min(WATER_FEATHER, hw * 0.70)
            row.append((zc + side * hw, WATER_EDGE_SHADE, 0.0))
            row.append((zc + side * (hw - f * 0.55), 0.82, 0.30))
            row.append((zc + side * (hw - f), 1.0, 0.68))
            row.append((zc + side * hw * 0.16, 1.0, 1.0))
        row.sort()                           # 게임 z 오름차순 = 블렌더 y 내림차순
        for (z_, sh, t_) in row:
            buf_water.v.append((x, -z_, y))
            buf_water.c.append(sh)
            # u = 흐름 방향 좌표(월드 x, m). 셰이더가 여기에 시간을 더해 물살을 흘린다
            # ★★v 를 뒤집어 넣는다. glTF 의 UV 원점은 **왼쪽 위**이고 블렌더는
            #   **왼쪽 아래**라, 익스포터가 내보낼 때 v 를 1-v 로 바꾼다.
            #   이걸 모르고 t_ 를 그대로 넣었더니 게임에서 v 가 정확히 반대가 됐고
            #   (기슭 v=1 · 한복판 v=0), 깊이 그라데이션이 뒤집혀 **개울 한가운데에
            #   흰 포말 길**이 났다. 화면을 안 봤으면 못 잡을 뻔했다.
            #   web/level.js 의 계약은 "v = 기슭까지의 거리(0 기슭 · 1 중심)" 이고,
            #   그 계약은 **게임이 받는 값** 기준이다. 그래서 여기서 1 - t 로 굽는다.
            buf_water.uv.append((x, 1.0 - t_))
    for k in range(n):
        a, b = base + k * 8, base + (k + 1) * 8
        for m in range(7):
            buf_water.f.append((a + m + 1, b + m + 1, b + m, a + m))
    return n + 1


def add_mouth_gravel(x_tip, zc, into, seed):
    """개울이 여울목에 닿는 자리의 자갈톱. 둥근 코와 같이 끝단을 닫는다.
    ★v79 함정을 다시 밟지 않는다: 개울에 **밟을 만한 크기**의 돌을 두면 통째로
      디딤돌로 읽힌다(밟아 보고 → 못 건너고 → 짜증). 그래서 반지름 0.22~0.5m,
      높이 0.10~0.20m 짜리 자갈만 흩는다. 밟는 물건은 12절 여울목 디딤돌뿐이다.
    ★물칸 안에만 둔다(물칸은 콜라이더라 애초에 발이 못 들어온다)."""
    # ★v94 (심사 지적 "물가 자갈 동일 실루엣 등간격"). k 를 8등분해 t 를 만들면
    #   폭 방향 자리가 **정확히 등간격**이 된다. 게다가 반지름 폭이 0.22~0.50 으로
    #   좁고 면 수(n=5)가 고정이라 아홉이 다 같은 오각 돔이었다.
    #   자리를 흩고(t 자체에 난수), 크기 폭을 넓히고, 면 수를 4~7 로 갈랐다.
    #   ★이 함수는 자기 seed 로 도는 별도 스트림이라 공용 rnd 를 안 건드린다.
    r = random.Random(seed)
    for k in range(11):
        t = r.uniform(-1.0, 1.0)                      # -1 ~ 1 (개울 폭 방향)
        gx = x_tip + into * (0.28 + r.uniform(0.0, 1.55))
        gz = zc + t * r.uniform(0.45, 1.35)
        rad = r.uniform(0.14, 0.62)
        add_dome(buf_rock, gx, gz, FLOOR_Y, rad, rad * r.uniform(0.62, 1.55),
                 r.uniform(0.06, 0.26), n=r.randint(4, 7), seed=seed + k,
                 squash=r.uniform(1.2, 2.1))


n_wv, n_mouth = 0, 0
for _si, _seg in enumerate(STREAM_SEGS):
    _c0, _c1 = _seg[0][0], _seg[-1][0]
    _cap_lo = (_c0 - 1) in FORD_COLS         # 여울목이면 둥글리고, 아니면 절벽이다
    _cap_hi = (_c1 + 1) in FORD_COLS
    n_wv += add_stream_ribbon(_seg, FLOOR_Y + 0.016, _cap_lo, _cap_hi)
    if _cap_lo:
        add_mouth_gravel(-HALF + _c0 * CELL + WATER_INSET,
                         gz_of(_seg[0][1]), +1.0, 7100 + _si * 13)
        n_mouth += 1
    if _cap_hi:
        add_mouth_gravel(-HALF + (_c1 + 1) * CELL - WATER_INSET,
                         gz_of(_seg[-1][1]), -1.0, 7200 + _si * 13)
        n_mouth += 1

# ── 자기 검증: 수면 리본이 물칸 밖으로 새지 않는가 ──────────
# ★리본은 격자를 안 쓴다. 중심선이 굽고 반폭이 흔들리므로 "물칸 안"이 보장되지
#   않는다. 정점 하나라도 물칸 밖이면 파란 판이 흙 위에 얹혀 보인다(v86 이 고친
#   그 증상 그대로다). 그래서 굽는 쪽에서 전부 다시 잰다.
def _wet_margin(z, c, r):
    """(c, r) 칸 안의 z 가 **기슭(남·북)** 까지 남긴 거리(m). 이어진 물칸은 건너뛴다.

    ★남북만 잰다. 개울은 동서로 흐르므로 "파란 판이 흙 위로 삐져나온다"는 사고는
      폭 방향에서만 난다. 동서(흐름 방향)로 재면 행이 바뀌는 열에서 리본이 칸
      모서리를 대각선으로 지나가기 때문에 축정렬 거리가 0 으로 나온다 — 실제로는
      양쪽 다 물칸인데도 그렇다. 그 숫자는 아무것도 안 지킨다."""
    best = 99.0
    for dr in (1, -1):
        k = 0
        while (c, r + dr * (k + 1)) in WATER_CELLS and k < 4:
            k += 1
        e = -HALF + (r + k + 1) * CELL if dr > 0 else -HALF + (r - k) * CELL
        best = min(best, abs(e - z))
    return best


_wet_bad, _wet_min = 0, 99.0
for (_vx, _vy, _vz) in buf_water.v:
    _gz = -_vy
    _cc = int((_vx + HALF) / CELL)
    _rr2 = int((_gz + HALF) / CELL)
    if (_cc, _rr2) not in WATER_CELLS:
        # 절벽 밑으로 밀어 넣은 끝단은 물칸 밖이 정상이다(바위가 덮는다)
        if 0 <= _cc < GRID and is_outer(_cc, _rr2):
            continue
        _wet_bad += 1
        continue
    _wet_min = min(_wet_min, _wet_margin(_gz, _cc, _rr2))
print("[검증] 수면 리본 정점 %d개 중 물칸 밖 %d개 / 남북 기슭까지 최소 여유 %.2fm "
      "(바닥칠 휨 폭 0.64m 보다 커야 한다)  %s"
      % (len(buf_water.v), _wet_bad, _wet_min,
         "OK" if (_wet_bad == 0 and _wet_min > 0.64) else "★어긋남"))
if _wet_bad or _wet_min <= 0.64:
    print("[경고] 수면이 물칸을 넘거나 여유가 모자란다. "
          "STREAM_HALF / STREAM_MEANDER 를 줄여라")
# ── 기슭 ★v79. 여기가 이 맵에서 제일 큰 거짓말이었다 ────────
# 예전에는 물칸 안쪽 0.30칸 자리에 둥근 바위를 둘렀다. 의도는 "못 건넌다는 신호"였는데
# 개울 폭이 3.2m 라 그 바위들이 개울 **한가운데** 놓인 꼴이 됐고, 통째로 디딤돌로
# 읽혔다(밟아 보고 → 못 건너고 → 12초 낭비. QA #6).
# 이제 막힌 구간에는 **밟을 만한 것을 하나도 안 둔다.** 대신 갈대를 촘촘히 세운다.
#   - 얇고 세로로 선 물건은 아무도 밟으려 하지 않는다
#   - 물칸 콜라이더(중심 ±1.26m) 안에 다 들어가서 걸어서 통과할 일도 없다
#   - 높이 1.05m 라 캐릭터 키(1.75)보다 낮다 = 건너편이 그대로 보인다(개방감 유지)
# 밟는 물건(통나무·디딤돌)은 아래 12절에서 **여울목에만** 놓는다.
n_reed = 0
for (c, r) in sorted(WATER_CELLS):
    for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if (c + dc, r + dr) in WATER_CELLS:
            continue
        if not walkable(c + dc, r + dr):
            continue          # 절벽·덤불에 붙은 면은 어차피 안 보인다
        for k in range(3):
            t_ = (k - 1) * 0.95
            rx = gx_of(c) + dc * CELL * 0.28 + (t_ if dc == 0 else 0.0)
            rz = gz_of(r) + dr * CELL * 0.28 + (t_ if dr == 0 else 0.0)
            add_reeds(buf_reed, rx + rnd.uniform(-0.10, 0.10),
                      rz + rnd.uniform(-0.10, 0.10), seed=c * 733 + r * 37 + k)
            n_reed += 1
print("[물] 물칸 %d / 수면 리본 %d구간 %d표본 / 끝단 자갈톱 %d / 기슭 갈대 %d다발 "
      "/ 여울목 %d칸" % (len(WATER_CELLS), len(STREAM_SEGS), n_wv, n_mouth,
                        n_reed, len(FORD)))


# ─────────────────────────────────────────────────────────────
# 11) 보스 공터 — 바위 분지 + 옛 법당 터 폐허
# ─────────────────────────────────────────────────────────────
# ★지붕도 건물도 없다. 탑다운에서 보스가 가리면 전투가 성립하지 않는다.
hall_gx, hall_gz, hall_hx, hall_hz = rect_world(11, 4, 18, 5)
# 너럭바위 단 두 겹(옛 기단이 이끼에 덮여 바위처럼 남았다)
place("stone_slab", hall_gx, hall_gz, var="shelf",
      hx=hall_hx, hz=hall_hz, y1=FLOOR_Y + 0.14)
place("stone_slab", hall_gx, hall_gz, var="shelf",
      hx=hall_hx - 0.5, hz=hall_hz - 0.5, y1=FLOOR_Y + 0.20)
push_plat_box(hall_gx, hall_gz, hall_hx, hall_hz, FLOOR_Y + 0.14, "hall")
push_plat_box(hall_gx, hall_gz, hall_hx - 0.5, hall_hz - 0.5, FLOOR_Y + 0.20, "hall")

# 옛 주춧돌 자리 8곳. 3개만 석주로 남기고 나머지는 바위로 되돌렸다(주역은 자연)
for i in range(4):
    for j in range(2):
        px = hall_gx + (-1 + 2 * i / 3.0) * (hall_hx - 1.0)
        pz = hall_gz + (-1 + 2 * j) * (hall_hz - 1.0)
        if (i + j) % 3 == 0:
            place("stone_pillar", px, pz, hh=rnd.uniform(1.2, 2.3))
        else:
            place("rock", px, pz, scale=rnd.uniform(0.95, 1.35))
# 무너진 서까래 대신 쓰러진 나무 몇 그루가 기단을 덮었다
for k in range(4):
    place("log", hall_gx + rnd.uniform(-hall_hx * 0.8, hall_hx * 0.8),
          hall_gz + rnd.uniform(-hall_hz * 0.6, hall_hz * 0.6),
          yaw=rnd.choice((0.0, math.pi / 2)), scale=rnd.uniform(0.7, 1.0))

# 보스 자리.
# ★v89 (3차 QA #6). 여기 있던 **두 겹 8각 제단**(DECO_ALTAR / MAT_ALTAR 70504a /
#   반지름 1.90·1.35, 높이 0.11·0.24)이 "보스 마당 상공에 지지 없이 떠 있는
#   어두운 7각 판"의 정체다. 실제로는 떠 있지 않았다. 게임 안에서 재 보니
#   (renders/history/v89_qa3map/BEFORE_probe.json) 제단 윗면과 같은 자리 지면의
#   화면 높이 차가 NDC 0.030 뿐인데 판 자체는 NDC 0.438 을 먹는다 = 지면에 붙은
#   높이 0.26m 짜리 낮은 단이다. 그런데도 떠 보인 이유가 셋이다.
#     (1) 정다각형이다. 이 맵의 자연물은 전부 윤곽이 흔들리는데 혼자 반듯한
#         8각형이라 지형이 아니라 **UI 판**으로 읽힌다
#     (2) 접지 그늘이 없다. 맵의 다른 지형은 바닥 텍스처가 발치를 눌러 주는데
#         (15절 block_mask) 제단은 소품이라 그 그늘을 못 받는다
#     (3) 색(70504a)이 맵 어디에도 없다. 붙어 있을 바닥색이 없으니 얹힌 게 아니라
#         떠 있는 것으로 보인다
#   기둥을 받치는 선택지도 있었지만, 탑다운에서 보스 발치에 기둥을 세우면 전투가
#   가려진다(이 마당에 지붕도 건물도 안 둔 이유와 같다). 그래서 **뺐다.**
#   "마른 피가 밴 자리"라는 정보는 15절에서 바닥에 **얼룩으로만** 칠한다.
#   지오메트리가 없으면 떠 보일 수가 없다.
BOSS_X, BOSS_Z = gx_of(BOSS_CELL[0]), gz_of(BOSS_CELL[1])
# ★★공용 rnd 자리 보존. 제단은 place() 를 두 번 불렀고 place() 는 한 번에
#   rnd.randint 를 정확히 한 번 뽑는다. 그냥 지우면 그 뒤 배치가 통째로 두 칸
#   밀려서 **소품 좌표와 콜라이더가 전부 바뀐다**(여울목 디딤돌까지 옮겨 갔다.
#   실제로 첫 재굽기에서 그랬다). 모양만 고치는 작업이 레이아웃을 흔들면 안 되므로
#   빠진 두 번을 여기서 그대로 소비한다. emit_props_json 의 경고와 같은 함정이다.
_ = rnd.randint(0, 10 ** 6)
_ = rnd.randint(0, 10 ** 6)


# ─────────────────────────────────────────────────────────────
# 12) 폐허 랜드마크 + 어귀 표식
# ─────────────────────────────────────────────────────────────
# 이끼 낀 석탑 하나. 맵 한가운데(0, 11.2)에 13m 로 선다.
# ★열린 맵에서 이정표는 하나여야 한다. 둘이면 어느 쪽이 중심인지 헷갈린다.
pgx, pgz = gx_of(14.5), gz_of(18.0)
place("stone_slab", pgx, pgz, var="shelf", hx=4.6, hz=4.6, y1=FLOOR_Y + 0.14)
place("stone_slab", pgx, pgz, var="shelf", hx=3.3, hz=3.3, y1=FLOOR_Y + 0.26)
push_plat_box(pgx, pgz, 4.6, 4.6, FLOOR_Y + 0.14, "pagoda")
push_plat_box(pgx, pgz, 3.3, 3.3, FLOOR_Y + 0.26, "pagoda")
place("pagoda", pgx, pgz)
for k in range(5):                          # 부서진 돌계단이 탑 아래 흩어졌다
    _a = k * 1.257 + rnd.uniform(-0.4, 0.4)
    place("stone_slab", pgx + math.cos(_a) * rnd.uniform(3.4, 5.0),
          pgz + math.sin(_a) * rnd.uniform(3.4, 5.0),
          var="step", hx=rnd.uniform(0.8, 1.4), hz=rnd.uniform(0.5, 0.9),
          y1=FLOOR_Y + rnd.uniform(0.10, 0.22), moss=True)

# 어귀 표식(선돌 두 짝). 붉은 홍살문을 대신한다. v67 에서 3.4m -> 4.6m.
# ★위에 지붕을 안 얹는 이유는 그대로다. 탑다운에서 어귀를 덮으면 매복 사각이 된다.
# ★자리 표(GATES)와 d 값의 근거는 위 3절로 옮겼다. 막는 칸을 채우는 절이
#   문설주 자리를 미리 알아야 석주가 바위를 관통하지 않는다(QA terr_07_crag).
GATE_STONES = []       # (x, z, 콜라이더 반지름). 아래 열린 곳 배치가 이걸 피해 간다


def gate_marker(gx, gz, along_x, d, cord=False):
    for s in (-1, 1):
        px = gx + (d * s if not along_x else 0)
        pz = gz + (d * s if along_x else 0)
        sc_ = rnd.uniform(0.94, 1.10)
        place("standing_stone", px, pz, yaw=rnd.uniform(0, 1.2), scale=sc_,
              cord=cord)
        GATE_STONES.append((px, pz, 0.62 * sc_))


n_cord = 0
for (gx, gz, ax, gd, cd) in GATES:
    gate_marker(gx, gz, ax, gd, cord=cd)
    n_cord += 2 if cd else 0
print("[어귀] 선돌 %d짝 / 붉은 끈을 감은 보스 방향 어귀 %d곳(선돌 %d개)"
      % (len(GATES), sum(1 for g in GATES if g[4]), n_cord))

# ── 여울목 표식 ★밟는 물건은 건널 수 있는 자리에만 ──────────
# QA #6 의 정확한 문장: "여울목 디딤돌이 막힌 개울 한가운데 놓여 밟고 건너라고
# 유혹한다. 실제 도하 지점에는 아무 표식이 없다." 둘 다 맞는 말이었다.
# 이제 규칙이 하나다: **밟을 수 있게 생긴 물건은 실제로 건널 수 있는 자리에만 둔다.**
#   - 통나무   : 여울목 칸마다 개울을 가로질러(yaw 90도) 걸친다
#   - 디딤돌   : 여울목 한복판에 납작한 판돌 여섯. 무릎 아래라 안 막고 platforms 로만 나간다
#   - 선돌 두 짝: 여울목 좌우 물칸에 세운다. 이미 막힌 칸이라 통행에 영향이 없고
#                 멀리서 "저기가 문이다"가 4.6m 실루엣으로 읽힌다
# 아래 자기 검증이 콜라이더로 뚫린 틈 좌표를 다시 뽑아 이 표식과 대조한다.
FORD_MARKS = []          # (x, z, 종류). 검증용

for _cols in FORD_GROUPS:
    _rows = sorted(set(stream_row(c) for c in _cols))
    _fx = sum(gx_of(c) for c in _cols) / len(_cols)
    _fz = sum(gz_of(r) for r in _rows) / len(_rows)
    # (1) 통나무. 개울을 가로지른다
    for c in _cols:
        _r = stream_row(c)
        _lx = gx_of(c) + rnd.uniform(-0.35, 0.35)
        _lz = gz_of(_r) + rnd.uniform(-0.5, 0.5)
        place("log", _lx, _lz, yaw=math.pi / 2,
              scale=rnd.uniform(0.75, 0.95), collide=False)
        FORD_MARKS.append((_lx, _lz, "통나무"))
    # (2) 납작한 디딤돌. 건너는 방향으로 두 줄
    for _i in range(3):
        for _j in range(2):
            _sx = _fx + (_i - 1) * CELL * 0.62 + rnd.uniform(-0.22, 0.22)
            _sz = _fz + (_j - 0.5) * CELL * 0.70 + rnd.uniform(-0.22, 0.22)
            _sh = rnd.uniform(0.78, 1.02)
            _y1 = FLOOR_Y + rnd.uniform(0.09, 0.16)
            place("stone_slab", _sx, _sz, var="ford",
                  hx=_sh, hz=_sh * rnd.uniform(0.68, 0.88), y1=_y1, moss=False)
            push_plat_box(_sx, _sz, _sh, _sh * 0.8, _y1, "ford")
            FORD_MARKS.append((_sx, _sz, "디딤돌"))
    # (3) 좌우 선돌. 이미 막힌 물칸 안에 세워 통행 폭을 안 깎는다
    for _side in (-1, 1):
        _c2 = (_cols[-1] + 1) if _side > 0 else (_cols[0] - 1)
        _cand = [(_c2, _rr) for _rr in range(min(_rows) - 1, max(_rows) + 2)
                 if (_c2, _rr) in WATER_CELLS]
        if not _cand:
            continue
        _cand.sort(key=lambda cr: abs(gz_of(cr[1]) - _fz))
        _wc, _wr = _cand[0]
        _px = gx_of(_wc) - _side * CELL * 0.22
        _pz = gz_of(_wr)
        _sc = rnd.uniform(0.86, 0.98)
        place("standing_stone", _px, _pz, yaw=rnd.uniform(0, 1.2), scale=_sc)
        GATE_STONES.append((_px, _pz, 0.62 * _sc))
        FORD_MARKS.append((_px, _pz, "선돌"))
print("[여울목] %d곳 / 표식 %d개 (통나무·디딤돌·선돌). 막힌 구간에는 0개"
      % (len(FORD_GROUPS), len(FORD_MARKS)))

# 탈출 지점 표식. 맵 어디에도 안 쓰는 창백한 옥색 돌계단 3단.
# ★증표를 들고 뛰는 중에 위에서 한눈에 찾아야 하는 지점이라 색으로 못을 박는다.
for (c, r) in EXIT_CELLS:
    ex, ez = gx_of(c), gz_of(r)
    for (hh, sh_) in ((0.07, 0.52), (0.15, 0.38), (0.23, 0.24)):
        place("stone_slab", ex, ez, var="exit",
              hx=CELL * sh_, hz=CELL * sh_, y1=FLOOR_Y + hh)
        push_plat_box(ex, ez, CELL * sh_, CELL * sh_, FLOOR_Y + hh, "exit")

# 낮은 둔덕 두 곳(걸어 올라갈 수 있다). ★무릎(0.6m)보다 낮아 콜라이더에는 안 넣고
#   platforms[] 에만 넣는다. 안 넣으면 그 위에 섰을 때 발이 두께만큼 묻힌다.
for (c0, r0, c1, r1) in ((2, 18, 3, 19), (26, 18, 27, 19)):
    tx, tz, thx, thz = rect_world(c0, r0, c1, r1)
    place("stone_slab", tx, tz, var="earth", hx=thx, hz=thz, y1=FLOOR_Y + 0.16)
    place("stone_slab", tx, tz, var="earth", hx=thx - 0.7, hz=thz - 0.7, y1=FLOOR_Y + 0.30)
    push_plat_box(tx, tz, thx, thz, FLOOR_Y + 0.16, "terrace")
    push_plat_box(tx, tz, thx - 0.7, thz - 0.7, FLOOR_Y + 0.30, "terrace")
    for k in range(3):
        place("rock", tx + rnd.uniform(-thx, thx), tz + rnd.uniform(-thz, thz),
              scale=rnd.uniform(0.4, 0.6), collide=False)


# ─────────────────────────────────────────────────────────────
# 13) 열린 곳의 엄폐물 — 큰 바위와 무너진 석등
# ─────────────────────────────────────────────────────────────
# ★충돌 선긋기: 무릎(0.6m)보다 높으면 막고 낮으면 안 막는다.
#   여기 놓는 큰 바위·석등은 막는다(그래서 콜라이더가 붙는다).
# ★막는 소품이 요괴 무리·스폰·탈출 지점 위에 앉으면 그 지점이 통째로 막힌다.
#   (첫 굽기에서 큰 바위가 MOB_9 자리를 덮어 요괴가 못 나올 뻔했다)
POI = [(gx_of(c), gz_of(r)) for (c, r) in MOB_CELLS + SPAWN_CELLS + EXIT_CELLS]
POI.append((BOSS_X, BOSS_Z))


def poi_clear(gx, gz, pad):
    return all(math.hypot(gx - px_, gz - pz_) >= pad for (px_, pz_) in POI)


# ★열린 곳에 놓는 **막는 소품**은 서로도, 지형에서도 떨어져 있어야 한다.
#   안 그러면 나무 두 그루 사이가 1m 짜리 틈이 되고(사람은 못 지나가는데 보이지도
#   않는다), 최악은 소품 두 개가 어귀를 통째로 막는 것이다. 실제로 v67 첫 굽기에서
#   쓰러진 거목 하나 + 선돌 두 짝이 EXIT_2 를 봉인해서 탈출이 불가능했다.
OPEN_PROPS = []       # (x, z, 콜라이더 반지름)
WALL_GAP = 2.4        # 소품과 격자 지형 사이 최소 여유
PROP_GAP = 2.9        # 소품끼리 최소 여유


def open_clear(gx, gz, r, wall_gap=WALL_GAP, prop_gap=PROP_GAP, remember=True):
    """wall_gap=None 이면 지형 여유는 안 본다(엄폐물은 벽에 붙는 게 목적이라서)."""
    # ★v79. 스폰 정면 15m 는 무조건 비운다. QA 가 "10m 앞 바위 무더기에 걸려
    #   12초 갇혔다"고 한 그 바위는 격자 지형이 아니라 여기서 놓은 **바위 무더기**였다
    #   (BOULDER_GROUPS (6.5, 26.0) 이 옛 SPAWN_1 정면 10.2m 였다).
    #   막는 소품은 전부 이 함수를 거치므로 여기 한 줄이면 종류를 안 빠뜨린다.
    if not lane_clear(gx, gz, r):
        return False
    if not ford_lane_clear(gx, gz, r):
        return False
    cc, rr_ = cell_of(gx, gz)
    if not walkable(cc, rr_):
        return False
    if wall_gap is not None:
        for k in range(12):                   # 지형까지 여유
            a = k * math.pi / 6
            pc, pr = cell_of(gx + math.cos(a) * (r + wall_gap),
                             gz + math.sin(a) * (r + wall_gap))
            if not walkable(pc, pr):
                return False
    for (ax, az, ar) in OPEN_PROPS:           # 소품끼리 여유
        if math.hypot(gx - ax, gz - az) < r + ar + prop_gap:
            return False
    if remember:
        OPEN_PROPS.append((gx, gz, r))
    return True


OPEN_PROPS.extend(GATE_STONES)                # 문설주가 제일 먼저 자리를 잡는다
OPEN_PROPS.append((pgx, pgz, 2.2))            # 석탑

# 쓰러진 거목 몇 그루를 빈터에 눕힌다. 높이 1m 라 건너편이 보이고 길만 굽는다
# ★거목은 길이 4.8m 짜리 막대다. 여유 검사 없이 놓으면 어귀 하나를 통째로 닫는다
#   (v67 첫 굽기에서 EXIT_2 가 실제로 이렇게 봉인됐다).
n_log = 0
for (cc, rr, ax) in ((5, 20, 0.0), (26, 26, 0.0), (16, 25, math.pi / 2),
                     (12, 15, math.pi / 2), (10, 11, 0.0), (19, 12, 0.0),
                     (8, 12, 0.0), (3, 17, math.pi / 2), (20, 17, 0.0)):
    lx, lz = gx_of(cc), gz_of(rr)
    if not poi_clear(lx, lz, 6.6):
        continue
    if not open_clear(lx, lz, 2.6, wall_gap=0.8, prop_gap=1.6):  # 막대 길이의 절반이 반지름
        continue
    place("log", lx, lz, yaw=ax, scale=rnd.uniform(0.85, 1.15))
    n_log += 1
print("[거목] 쓰러진 나무 %d그루" % n_log)


cover_spots = []
for r in range(2, GRID - 2):
    for c in range(2, GRID - 2):
        if grid[r][c] not in (PATH, OPEN, BOSSF):
            continue
        if (c, r) in BUSH_SET or (c, r) in FORD:
            continue
        if (c + r * 7) % 11 != 0:
            continue
        nb = [(dc, dr) for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if not walkable(c + dc, r + dr)]
        if not nb:
            continue
        dc, dr = nb[0]
        sx_, sz_ = gx_of(c) + dc * CELL * 0.32, gz_of(r) + dr * CELL * 0.32
        if not poi_clear(sx_, sz_, 4.4):
            continue
        cover_spots.append((sx_, sz_))
rnd.shuffle(cover_spots)
placed_cover = []
for (lx, lz) in cover_spots:
    if len(placed_cover) >= 24:
        break
    # 엄폐물은 벽에 붙는 게 목적이라 지형 여유는 안 본다. 소품끼리만 벌린다
    if not open_clear(lx, lz, 1.1, wall_gap=None):
        continue
    placed_cover.append((lx, lz))
for i, (lx, lz) in enumerate(placed_cover):
    if i % 4 == 0:                       # 넷 중 하나만 폐허로 남긴다
        place("stone_lantern", lx, lz)
    else:
        place("rock", lx, lz, scale=rnd.uniform(0.85, 1.25))


# ── 나무 숲 무리 ─────────────────────────────────────────────
# ★열린 초원이 지루해지지 않게 하는 주역이 이것이다. 나무는 **줄기만 막고**
#   가지는 안 막으니(반경 0.42) 밀도를 올려도 길이 안 좁아지고, 위에서 보면
#   초록 덩어리가 초원에 리듬을 준다. 벽 대신 나무로 길을 굽히는 게 이 맵의 방식이다.
GROVES = [
    (3.0, 4.5), (26.0, 4.5),        # 북쪽 곁터
    (11.5, 12.0), (17.5, 12.0),     # 개울 남안 가운데
    (2.5, 13.0), (26.5, 13.0),      # 개울 남안 좌우
    (7.5, 17.5), (21.5, 17.5),      # 첫 띠와 석탑 마당 사이
    (11.0, 21.5), (18.0, 21.5),     # 석탑 마당 남쪽
    (4.0, 26.0), (25.0, 26.0),      # 남쪽 초원
    # ★석탑 발치에는 안 심는다. 랜드마크로 다가가는 길이 가려지면 이정표가 아니다
]
n_grove = 0
for (gc, gr) in GROVES:
    cx0, cz0 = gx_of(gc), gz_of(gr)
    for k in range(8):
        a = k * 0.785 + rnd.uniform(-0.4, 0.4)
        rad = rnd.uniform(1.6, 4.4)
        tx, tz = cx0 + math.cos(a) * rad, cz0 + math.sin(a) * rad
        cc, rr2 = cell_of(tx, tz)
        if (cc, rr2) in BUSH_SET or (cc, rr2) in FORD:
            continue
        if not poi_clear(tx, tz, 4.2):
            continue
        # ★v79. 스폰 둘레는 한 겹 더 벌린다. 나무 줄기는 0.42m 짜리라 통로를 안 막지만
        #   가지(캐노피)는 위에서 캐릭터를 덮는다. 첫 화면에서 내 캐릭터가 잎에 가리면
        #   그게 곧 "여기가 어디고 어디로 가야 하나"를 못 읽는 상태다.
        if any(math.hypot(tx - sx_, tz - sz_) < 5.8 for (sx_, sz_, _, _) in SPAWN_LANES):
            continue
        if not open_clear(tx, tz, 0.45, wall_gap=1.5, prop_gap=2.3):
            continue
        place("tree", tx, tz, scale=rnd.uniform(0.85, 1.30), slim=True)
        n_grove += 1

# ── 바위 무더기(엄폐물) ──────────────────────────────────────
# 큰 바위 셋씩 모아 둔다. 하나는 숨을 수 있고 셋이 모이면 지형처럼 읽힌다.
# ★서로 1.5~3m 씩 벌려 놓는다. 붙여 놓으면 그냥 벽이고, 벌려 놓으면 사이로 보인다.
BOULDER_GROUPS = [
    (5.0, 9.5), (24.0, 9.5),        # 개울 북안
    (12.8, 16.5), (16.2, 16.5),     # 석탑 마당 어귀(중앙 대로 위)
    (9.0, 22.0), (20.0, 22.0),
    (6.5, 26.0), (22.5, 26.0),
    (11.0, 6.0), (18.0, 4.5),       # 보스 마당 안 엄폐물
]
n_bgrp = 0
for (gc, gr) in BOULDER_GROUPS:
    cx0, cz0 = gx_of(gc), gz_of(gr)
    for k in range(4):
        a = k * 1.571 + rnd.uniform(-0.4, 0.4)
        rad = rnd.uniform(2.4, 4.2)
        bx2, bz2 = cx0 + math.cos(a) * rad, cz0 + math.sin(a) * rad
        cc, rr2 = cell_of(bx2, bz2)
        if (cc, rr2) in BUSH_SET or (cc, rr2) in FORD:
            continue
        if not poi_clear(bx2, bz2, 5.0):
            continue
        sc2 = rnd.uniform(0.90, 1.30)
        if not open_clear(bx2, bz2, 0.95 * sc2, wall_gap=1.8, prop_gap=2.4):
            continue
        place("rock", bx2, bz2, scale=sc2)
        n_bgrp += 1
print("[열린 곳] 엄폐 %d / 숲 나무 %d / 바위 무더기 %d" %
      (len(placed_cover), n_grove, n_bgrp))

# 잔돌·이끼: 막는 지형 발치에 흩뿌려 격자 티를 지운다(무릎 아래라 안 막는다)
n_pebble = 0
for r in range(1, GRID - 1):
    for c in range(1, GRID - 1):
        if grid[r][c] in (W_, BLD):
            continue
        if (c * 13 + r * 5) % 9 != 0:
            continue
        nb = [(dc, dr) for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if not walkable(c + dc, r + dr)]
        if not nb:
            continue
        dc, dr = nb[rnd.randrange(len(nb))]
        for k in range(2):
            px = gx_of(c) + dc * CELL * rnd.uniform(0.24, 0.40) + rnd.uniform(-0.5, 0.5)
            pz = gz_of(r) + dr * CELL * rnd.uniform(0.24, 0.40) + rnd.uniform(-0.5, 0.5)
            place("rock", px, pz, scale=rnd.uniform(0.22, 0.45), collide=False)
            n_pebble += 1



# ─────────────────────────────────────────────────────────────
# 14) 수풀 (숨는 곳) — 통과 가능, 콜라이더 없음
# ─────────────────────────────────────────────────────────────
# ★막는 초목(COL_THICKET, 암록 3m+)과 확실히 달라야 한다.
#   여기는 **밝은 연두 + 1.5m + 성긴 덩어리**다. 색·높이·밀도 셋 다 다르다.
BUSH_OBJS = []
BUSH_JSON = []
for bi, region in enumerate(BUSH_CELLS):
    b = Buf("BUSH_%02d" % (bi + 1), M_BUSH)
    for (c, r) in region:
        cx, cz = gx_of(c), gz_of(r)
        for k in range(6):
            ang = k * 2 * math.pi / 6 + rnd.uniform(-0.35, 0.35)
            rad = CELL * (0.12 + 0.26 * (k % 3))
            place("bush", cx + math.cos(ang) * rad + rnd.uniform(-0.3, 0.3),
                  cz + math.sin(ang) * rad + rnd.uniform(-0.3, 0.3),
                  scale=rnd.uniform(0.85, 1.25), buf=b)
        for k in range(2):               # 갈대. 위에서 볼 때 세로 악센트
            place("bush", cx + rnd.uniform(-CELL * 0.34, CELL * 0.34),
                  cz + rnd.uniform(-CELL * 0.34, CELL * 0.34),
                  scale=rnd.uniform(0.85, 1.2), var="reed", buf=b)
    BUSH_OBJS.append(b)
    BUSH_JSON.append({
        "id": "BUSH_%02d" % (bi + 1),
        "cells": [[c, r] for (c, r) in region],
        "rects": [{"x": round(gx_of(c), 3), "z": round(gz_of(r), 3),
                   "hx": round(CELL / 2, 3), "hz": round(CELL / 2, 3)}
                  for (c, r) in region],
    })


# ─────────────────────────────────────────────────────────────
# 14.7) 지형 조각 배치 ★v91 — 오너 판정 "돌·냇가가 찰흙"
# ─────────────────────────────────────────────────────────────
# blender/s28_terrain.py 가 구운 web/props/<종류>.glb 다섯을 심는다.
# 여기서 하는 일은 **좌표를 정하는 것뿐**이고 모양은 그 glb 가 갖고 있다.
#
# ★★이 절이 왜 여기(수풀 다음, 자기 검증 앞)에 있나 — rnd 스트림 보전
#   place() 는 한 번 불릴 때마다 공용 rnd 에서 randint 를 정확히 한 번 뽑는다.
#   이 절을 **앞쪽에 끼워 넣으면 그 뒤의 배치가 통째로 밀려서** 소품 좌표와
#   콜라이더가 전부 바뀐다(11절 제단 폐기 때 실제로 겪은 사고다).
#   그래서 기존 rnd 소비가 전부 끝난 자리에 붙인다. 위쪽 배치는 한 톨도 안 움직인다.
#   = 이 작업의 콜라이더 diff 가 0 인 첫 번째 이유다.
#   (두 번째 이유는 다섯 종이 전부 collide=False 라는 것이다.)
#
# ★모델 앞뒤 — 회전을 무작위로 주면 안 되는 이유
#   s28 이 절벽 2종의 **뒷면을 평면으로 잘라** 놨다. 그 단면이 절벽을 봐야
#   이어붙고, 반대로 돌면 잘린 판때기가 플레이어를 정면으로 본다.
#   blender +Y 가 three.js -Z 이므로(export_yup) rotY=0 에서 단면은 **북쪽**을 본다.
#   아래 back_yaw() 가 "이 방향으로 등을 돌려라"를 rotY 로 바꾼다.
#
# ★치수 출처 — 전부 s28_terrain.py 의 굽기 로그에서 그대로 가져온 값이다(scale 1.0 기준)
#   cliff_tall  반너비 0.541 / 앞뒤 ±0.432(뒷면이 +Y) / 높이 4.60
#   outcrop     반너비 1.233 / 앞뒤 ±0.637(뒷면이 +Y) / 높이 1.55
#   boulder_xl  반너비 0.893 x 1.007 / 높이 1.255   (norm 이 rock 과 같은 0.95)
#   bank        긴축 반너비 1.300 / 앞뒤 ±0.901 / 높이 0.583
#   slab        반너비 1.10 / 두께 0.142
TER_CLIFF_HY = 0.432      # cliff_tall 앞뒤 반너비
TER_CLIFF_HX = 0.541      # cliff_tall 좌우 반너비(자른 폭). 배치 간격의 기준이다
TER_OUT_HY = 0.637        # outcrop 앞뒤 반너비
TER_BANK_HX = 1.300       # bank 긴축 반너비
# 막는 선(콜라이더)보다 몇 m 앞으로 나오게 둘 것인가.
# ★0 이면 절차 절벽면과 같은 자리라 서로 뚫고 지나간다(z-fighting).
#   1m 를 넘기면 "보이는데 안 막히는" 자리가 그만큼 생긴다. 절벽자락 잔돌이 쓰는
#   여유(0.5m 안쪽)와 같은 대역으로 잡는다.
TER_PROTRUDE = 0.35


def back_yaw(nx, nz):
    """등(잘린 단면)을 (nx, nz) 방향으로 돌리는 rotY.
    rotY=0 에서 등이 (0,-1)=북을 보므로 a = atan2(-nx, -nz) 다."""
    return math.atan2(-nx, -nz)


def long_yaw(tx, tz):
    """긴 축(로컬 +X)을 (tx, tz) 방향으로 눕히는 rotY."""
    return math.atan2(-tz, tx)


TER_N = dict(cliff_tall=0, outcrop=0, boulder_xl=0, bank=0, slab=0)
TER_SKIP = dict(gate=0, lane=0, ford=0, occupied=0)

# ── (1) 외곽 절벽 링 앞 기둥 줄 ──────────────────────────────
# ★"줄지어" 를 균일 간격으로 하면 안 된다. 같은 폭으로 늘어선 기둥은 자연 절벽이
#   아니라 **울타리**로 읽힌다. 3~7개를 어깨 맞대 붙인 뭉치와 1.8~5.0m 빈틈을
#   번갈아 낸다. 빈틈으로는 뒤의 절차 절벽 단(段)이 그대로 보이는데, 그게 오히려
#   "기둥이 절벽에서 떨어져 나온 것"으로 읽혀서 두 개가 한 지형이 된다.
# ★빈틈이 3m 이상이면 그 자리에 낮은 노두(outcrop)를 하나 눕힌다. 발치가 비면
#   기둥이 땅에 꽂힌 말뚝처럼 보인다.
RING_IN = HALF - 2 * CELL          # 링 안쪽 면. ±41.6
CLIFF_EDGES = [
    # (고정축, 고정좌표, 안쪽 단위벡터, 등을 돌릴 방향)
    ("z", -RING_IN, (0.0, 1.0), (0.0, -1.0)),    # 북
    ("z", +RING_IN, (0.0, -1.0), (0.0, 1.0)),    # 남
    ("x", -RING_IN, (1.0, 0.0), (-1.0, 0.0)),    # 서
    ("x", +RING_IN, (-1.0, 0.0), (1.0, 0.0)),    # 동
]
ring_gaps = []                      # (x, z, 안쪽벡터, 등방향) 노두를 눕힐 빈틈
for (axis, fixed, inw, back) in CLIFF_EDGES:
    yaw0 = back_yaw(back[0], back[1])
    t = -RING_IN + 0.6
    run_left = 0
    while t < RING_IN - 0.6:
        if run_left <= 0:                       # 새 뭉치 시작 전 빈틈
            gap = rnd.uniform(1.8, 5.0)
            gm = t + gap * 0.5
            gx0, gz0 = (gm, fixed) if axis == "z" else (fixed, gm)
            if gap >= 3.0:
                ring_gaps.append((gx0, gz0, inw, back))
            t += gap
            run_left = rnd.randint(3, 7)
            continue
        s = rnd.uniform(0.95, 1.30)
        step = TER_CLIFF_HX * 2 * s * 0.92      # 0.92 = 어깨를 겹쳐 V자 틈을 막는다
        # 이 자리가 링 안쪽 면 위 어디인가
        px = t if axis == "z" else fixed
        pz = fixed if axis == "z" else t
        # 앞면이 (막는 선 + TER_PROTRUDE) 에 오도록 뒤로 물린다.
        # ★거기서 0~0.45m 를 **더 파묻는다**(밖으로 더 내밀지 않는다).
        #   앞뒤가 고르면 잘린 옆면이 한 평면에 늘어서서 벽돌담이 된다.
        #   바깥으로 내미는 쪽으로 흔들면 "보이는데 안 막히는" 자리만 늘어나므로
        #   흔들림은 **안쪽으로만** 준다. 막는 선은 한 톨도 안 움직인다.
        off = TER_PROTRUDE + 0.05 - TER_CLIFF_HY * s - rnd.uniform(0.0, 0.45)
        px += inw[0] * off
        pz += inw[1] * off
        run_left -= 1
        t += step
        # ── 통과 검사 ──
        cc, rr_ = cell_of(px - inw[0] * 0.8, pz - inw[1] * 0.8)   # 등 뒤의 링 칸
        if not (0 <= cc < GRID and 0 <= rr_ < GRID) or grid[rr_][cc] != W_:
            TER_SKIP["gate"] += 1               # 어귀로 파인 틈이다. 문을 막으면 안 된다
            run_left = 0
            continue
        if not lane_clear(px, pz, TER_CLIFF_HX * s):
            TER_SKIP["lane"] += 1
            continue
        if not ford_lane_clear(px, pz, TER_CLIFF_HX * s):
            TER_SKIP["ford"] += 1
            continue
        if not gate_post_clear(px, pz, TER_CLIFF_HX * s):
            TER_SKIP["gate"] += 1
            continue
        # ★v94 (심사 지적 "절벽 기둥 모듈 반복"). 회전 흔들림이 ±0.09rad(±5도)
        #   뿐이라 134개가 한 각도로 나란히 섰다. ±0.24rad(±14도)로 넓힌다.
        #   더 못 넓히는 이유: 이 모델은 뒷면이 평면으로 잘려 있어서(s28 불리언 컷)
        #   많이 돌리면 잘린 면이 옆으로 드러난다. 14도까지는 TER_PROTRUDE 로
        #   파묻은 깊이 안에 들어간다.
        # ★실루엣 자체를 가르는 건 회전이 아니라 **다른 모델**이다. 여섯에 하나쯤
        #   낮은 노두를 섞어 마루선이 한 줄로 이어지지 않게 한다(장식 전용이라
        #   막는 선은 링 콜라이더가 그대로 쥐고 있다).
        _v = random.Random(int(px * 733) ^ int(pz * 419)).random()
        _as2 = "outcrop" if _v < 0.17 else None
        place("cliff_tall", px, pz, scale=s * (1.35 if _as2 else 1.0), collide=False,
              rot=yaw0 + rnd.uniform(-0.24, 0.24),
              **({"as": _as2} if _as2 else {}))
        TER_N["cliff_tall"] += 1

# ── (2) 낮은 노두 — 절벽 발치의 빈틈 + 너덜 덩어리 가장자리 ──
for (gx0, gz0, inw, back) in ring_gaps:
    s = rnd.uniform(0.85, 1.25)
    off = TER_PROTRUDE + 0.05 - TER_OUT_HY * s
    px, pz = gx0 + inw[0] * off, gz0 + inw[1] * off
    cc, rr_ = cell_of(px - inw[0] * 0.8, pz - inw[1] * 0.8)
    if not (0 <= cc < GRID and 0 <= rr_ < GRID) or grid[rr_][cc] != W_:
        TER_SKIP["gate"] += 1
        continue
    if not (lane_clear(px, pz, 1.3) and ford_lane_clear(px, pz, 1.3)
            and gate_post_clear(px, pz, 1.3)):
        TER_SKIP["lane"] += 1
        continue
    place("outcrop", px, pz, scale=s, collide=False,
          rot=back_yaw(back[0], back[1]) + rnd.uniform(-0.12, 0.12))
    TER_N["outcrop"] += 1

# 너덜(T_LOW) 덩어리의 바깥 면. ★여기가 개방감 장치의 얼굴이다.
#   너덜은 높이 1.45m 라 "몸은 못 지나가는데 건너편이 보인다". 그 가장자리에
#   1.55m 짜리 실제 암반 노두를 눕히면 돔 껍질이던 실루엣이 바위로 바뀐다.
# ★앞면을 **콜라이더 선 안쪽**에 둔다. 칸 격자 콜라이더는 칸 경계에서 WALL_INSET
#   만큼 안으로 들어와 있으므로, 칸 경계 기준으로는 그만큼 더 물려야 한다.
for (c, r) in sorted(terr):
    if terr[(c, r)] != T_LOW or is_outer(c, r):
        continue
    for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if not walkable(c + dc, r + dr):
            continue
        if rnd.random() > 0.62:                 # 전부 두르면 띠가 된다. 띄엄띄엄
            continue
        s = rnd.uniform(0.85, 1.25)
        bx = gx_of(c) + dc * CELL * 0.5
        bz = gz_of(r) + dr * CELL * 0.5
        off = WALL_INSET - TER_PROTRUDE + TER_OUT_HY * s
        px, pz = bx - dc * off, bz - dr * off
        px += (-dr) * rnd.uniform(-0.5, 0.5)    # 칸 모서리를 따라 조금 흔든다
        pz += dc * rnd.uniform(-0.5, 0.5)
        if not (lane_clear(px, pz, 1.3) and ford_lane_clear(px, pz, 1.3)
                and gate_post_clear(px, pz, 1.3)):
            TER_SKIP["lane"] += 1
            continue
        place("outcrop", px, pz, scale=s, collide=False,
              rot=back_yaw(-dc, -dr) + rnd.uniform(-0.14, 0.14))
        TER_N["outcrop"] += 1

# ── (3) 개울 기슭 돌무더기 ───────────────────────────────────
# ★기슭 갈대(10절)와 같은 반복문 구조다. 갈대는 **물칸 안쪽**에 서고
#   여기 돌무더기는 **물과 뭍의 경계**에 눕는다. 둘이 겹치지 않는다.
# ★여울목 차선은 비운다. 개울을 건널 수 있는 유일한 자리라 돌무더기가 한 발짝만
#   들어와도 "여기로 건너는 게 맞나"가 흐려진다(v86 S8 과 같은 규칙이다).
for (c, r) in sorted(WATER_CELLS):
    for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if (c + dc, r + dr) in WATER_CELLS:
            continue
        if not walkable(c + dc, r + dr):
            continue                            # 절벽·덤불에 붙은 면은 안 보인다
        if (c + dc, r + dr) in FORD:
            TER_SKIP["ford"] += 1
            continue
        bx = gx_of(c) + dc * CELL * 0.5
        bz = gz_of(r) + dr * CELL * 0.5
        tan = (-dr, dc)                         # 물가를 따라 눕는 방향
        yaw_b = long_yaw(tan[0], tan[1])
        # ★v94 (심사 지적 "물가 자갈 덩어리 동일 실루엣 등간격").
        #   범인은 세 가지였다. ①회전 흔들림이 ±0.16rad(±9도)뿐이라 50개가 전부
        #   같은 각도로 누웠다 ②크기 폭이 0.62~1.05 로 좁다 ③자리가 칸 면 중앙
        #   ±0.28m 라 사실상 등간격이다. 셋 다 폭만 넓힌다.
        # ★★공용 rnd 스트림을 보전한다. rnd.uniform(a, b) 는 범위가 무엇이든
        #   random() 을 정확히 한 번 뽑으므로 **범위만 넓히는 것은 스트림에 영향이
        #   없다**(호출 횟수가 그대로다). 아래 콜라이더 diff 검증이 이걸 증명한다.
        n = 1 + (1 if rnd.random() < 0.45 else 0)
        for k in range(n):
            s = rnd.uniform(0.62, 1.22) if n == 1 else rnd.uniform(0.48, 1.00)
            u = 0.0 if n == 1 else (k - 0.5) * 1.5
            u += rnd.uniform(-0.62, 0.62)
            # 경계에서 0.25m 물 쪽으로 물린다(뭍 쪽으로 덜 삐져나오게)
            px = bx + tan[0] * u - dc * 0.25
            pz = bz + tan[1] * u - dr * 0.25
            if not ford_lane_clear(px, pz, TER_BANK_HX * s):
                TER_SKIP["ford"] += 1
                continue
            if not lane_clear(px, pz, TER_BANK_HX * s):
                TER_SKIP["lane"] += 1
                continue
            # ★모델을 섞는다. 회전·크기만으로는 **실루엣**이 안 바뀐다(한 벌이니까).
            #   기슭 띠 넷 중 하나쯤은 노두를 작게 눕혀 두면 윤곽이 갈린다.
            #   난수는 자리에서 뽑는다(공용 rnd 를 더 소비하지 않는다).
            _mix = random.Random(int(px * 977) ^ int(pz * 613) ^ (k * 31)).random()
            _as = "outcrop" if _mix < 0.26 else None
            place("bank", px, pz, scale=s * (0.42 if _as else 1.0), collide=False,
                  rot=yaw_b + rnd.uniform(-0.52, 0.52),
                  **({"as": _as} if _as else {}))
            TER_N["bank"] += 1

# ── (4) 랜드마크 거대 바위 ★모양만 교체 ─────────────────────
# ★place() 를 새로 부르지 않는다. 이미 심어 놓은 **큰 바위의 모양만** 갈아끼운다.
#   왜 이렇게 하나:
#     - 새로 심으면 그 자리에 바위가 둘이 된다(기존 rock 이 안 없어진다)
#     - 기존 place() 를 지우면 공용 rnd 가 밀려서 맵 전체 배치가 바뀐다
#     - collide=True 인 프롭을 collide=False 로 바꾸면 콜라이더가 사라진다
#   그래서 배치·콜라이더·rnd 를 하나도 안 건드리고 props[] 에 나갈 **kind 만** 바꾼다.
#   s28 이 boulder_xl 을 rock 과 **같은 규격(norm xy 0.95)** 으로 구웠기 때문에
#   scale 이 그대로 통하고, 콜라이더 반지름(0.95 x scale)과도 정확히 맞는다.
_bg_world = [(gx_of(gc), gz_of(gr)) for (gc, gr) in BOULDER_GROUPS]
_cands = {}
for p in PROPS:
    if p["kind"] != "rock" or not p["collide"]:
        continue
    for gi, (cx0, cz0) in enumerate(_bg_world):
        if math.hypot(p["x"] - cx0, p["z"] - cz0) <= 5.2:
            cur = _cands.get(gi)
            if cur is None or p["scale"] > cur["scale"]:
                _cands[gi] = p          # 무리마다 제일 큰 바위 하나
            break
for p in sorted(_cands.values(), key=lambda q: -q["scale"])[:8]:
    p["as"] = "boulder_xl"
    TER_N["boulder_xl"] += 1

# ── (5) 판석 패드 — 폐허·석탑 마당·판석길 가장자리 ───────────
# ★색이 여울목 젖은 돌(b9c2ba)이다. 걷는 바닥에 놓는 장식이라 밝아야 한다
#   (바위색으로 깔면 "여기는 못 간다"고 거짓말을 하는 셈이다. 여울목 디딤돌을
#    창백한 폐허 석재로 깐 것과 같은 판단이다).
def slab_ok(px, pz, rad):
    cc, rr_ = cell_of(px, pz)
    if not (0 <= cc < GRID and 0 <= rr_ < GRID):
        return False
    if not walkable(cc, rr_):
        return False
    # ★★풀밭에는 안 깐다. 1차 게임 화면에서 잔디 위에 창백한 정사각 판이 흩어져
    #   **바닥에 떨어뜨린 타일**로 보였다(v89 이 제단에서 겪은 "정다각형 + 접지
    #   그늘 없음 + 그 자리 바닥에 없는 색" 세 조건이 그대로 재현됐다).
    #   같은 판이 흙길·판석길 위에서는 멀쩡히 포장으로 읽혔다. 차이는 **깔린 바닥이
    #   이미 돌색인가** 하나다. 그래서 길 칸(PATH)과 보스 마당(BOSSF)에만 깐다.
    if grid[rr_][cc] not in (PATH, BOSSF):
        return False
    # ★단(platform) 가장자리에 걸치면 판이 공중에 뜬다. 게임은 소품을 groundY 에
    #   놓는데 그 값이 단 위에서만 올라가서, 반은 단 위 반은 풀밭인 자리에 놓이면
    #   풀밭 쪽 절반이 붕 뜬다(1차 화면의 석탑 마당이 그랬다). 단 근처는 통째로 뺀다.
    for pl in PLATFORMS:
        if pl["type"] != "box":
            continue
        if (abs(px - pl["x"]) < pl["hx"] + rad + 0.8
                and abs(pz - pl["z"]) < pl["hz"] + rad + 0.8):
            return False
    if (cc, rr_) in BUSH_SET or (cc, rr_) in FORD:
        return False
    if not (lane_clear(px, pz, rad) and ford_lane_clear(px, pz, rad)):
        return False
    return poi_clear(px, pz, 3.2)


# 석탑으로 가는 길 위 — 단(hx 4.6)에서 충분히 떨어진 바깥 고리.
# ★반지름을 6.8 부터 잡는다. 단 배제 반경(4.6 + 판 반너비 + 0.8)이 6.4 근처라
#   그보다 안쪽은 어차피 전부 걸러진다(공중에 뜨는 자리다).
for k in range(14):
    _a = k * 0.449 + rnd.uniform(-0.22, 0.22)
    _rad = rnd.uniform(6.8, 9.2)
    px, pz = pgx + math.cos(_a) * _rad, pgz + math.sin(_a) * _rad
    if not slab_ok(px, pz, 1.2):
        TER_SKIP["occupied"] += 1
        continue
    place("slab", px, pz, scale=rnd.uniform(0.58, 0.92), collide=False,
          rot=rnd.uniform(0, 2 * math.pi))
    TER_N["slab"] += 1

# 옛 법당 터 앞마당 — 기단(단)에서 물러선 자리. 보스 마당 흙바닥 위다.
# ★기단 **위**나 가장자리에는 못 깐다(단 배제). 마당 쪽으로 3~6m 물러나
#   "기단에서 떨어져 나와 마당에 흩어진 판석"으로 놓는다.
for k in range(14):
    _t = k / 13.0
    px = hall_gx + (-1 + 2 * _t) * (hall_hx + rnd.uniform(2.6, 5.4))
    pz = hall_gz + (hall_hz + rnd.uniform(2.4, 5.6)) * (1 if k % 2 else -1)
    if not slab_ok(px, pz, 1.2):
        TER_SKIP["occupied"] += 1
        continue
    place("slab", px, pz, scale=rnd.uniform(0.60, 0.95), collide=False,
          rot=rnd.uniform(0, 2 * math.pi))
    TER_N["slab"] += 1

# 판석길 가장자리 — 중앙 대로와 남안 동서길. ★길 **위**가 아니라 가장자리에 둔다.
#   한복판에 깔면 밟고 지나가면서 발이 판에 잠긴다(콜라이더도 단도 없다).
# ★부호는 **길 안쪽**을 가리킨다. 1차에서는 바깥으로 밀었다가 전부 잔디 위에
#   떨어져서 "잔디에 놓은 타일"이 됐다. 판석은 이미 돌색인 바닥 위에서만 포장으로
#   읽힌다. 그래서 길 가장자리에서 **안쪽으로** 반 발짝 들어와 깐다.
SLAB_EDGES = [
    # (축, 길 가장자리 좌표, 따라갈 범위 시작, 끝, 길 안쪽 방향 부호)
    ("x", -HALF + 14 * CELL, -HALF + 12 * CELL, -HALF + 26 * CELL, +1),
    ("x", -HALF + 16 * CELL, -HALF + 12 * CELL, -HALF + 26 * CELL, -1),
    ("z", -HALF + 13 * CELL, -HALF + 4 * CELL, HALF - 4 * CELL, +1),
    ("z", -HALF + 14 * CELL, -HALF + 4 * CELL, HALF - 4 * CELL, -1),
]
for (axis, edge, t0, t1, sgn) in SLAB_EDGES:
    t = t0 + rnd.uniform(0.0, 4.0)
    while t < t1:
        s = rnd.uniform(0.55, 0.85)
        d = edge + sgn * (0.75 + rnd.uniform(0.0, 0.7))
        px, pz = (d, t) if axis == "x" else (t, d)
        t += rnd.uniform(4.2, 8.5)
        if not slab_ok(px, pz, 1.1):
            TER_SKIP["occupied"] += 1
            continue
        place("slab", px, pz, scale=s, collide=False,
              rot=rnd.uniform(0, 2 * math.pi))
        TER_N["slab"] += 1

print("[지형v91] 절벽기둥 %d / 노두 %d / 거대바위 %d(모양교체) / 기슭 %d / 판석 %d"
      % (TER_N["cliff_tall"], TER_N["outcrop"], TER_N["boulder_xl"],
         TER_N["bank"], TER_N["slab"]))
print("[지형v91] 건너뛴 자리: 어귀 %d / 스폰·통로 %d / 여울목차선 %d / 자리없음 %d"
      % (TER_SKIP["gate"], TER_SKIP["lane"], TER_SKIP["ford"], TER_SKIP["occupied"]))
print("[지형v91] 새로 생긴 콜라이더 0개 (다섯 종 전부 collide=False)")


# ── ★v94. 사람이 놓은 돌 관통 정리 (구 QA "크래그 관통 석주") ──
# 정찰 실측: stone_pillar 관통은 **0건**이었다(그 항목은 사실이 아니다). 대신
# standing_stone(선돌)·stone_lantern(석등)이 rock·tree·outcrop·bank 를 뚫는 자리가
# **11건** 나왔다. 최악은 선돌 (24.0, -33.6) 이 반지름 0.33 짜리 잔돌을 83% 파고든 것.
#
# 원인: 선돌·석등은 어귀/여울목/탈출구 코드가 심고, 잔돌·나무는 **나중에 도는 다른
# 반복문**이 뿌린다. 둘이 서로를 모른다(open_clear 의 OPEN_PROPS 에는 문설주만 들어
# 있고, 잔돌 반복문은 그 검사를 안 탄다).
#
# ★고치는 방식이 중요하다. "겹치면 건너뛴다"로 하면 place() 안의 rnd.randint 가
#   한 번 덜 뽑혀서 **그 뒤 배치가 통째로 밀린다**(v89 제단에서 밟은 그 함정).
#   그래서 **빼먹지 않고 밀어낸다.** 개수도, 난수 소비도, 종류도 그대로다.
_KEEP_KINDS = ("standing_stone", "stone_lantern", "stone_pillar")
_posts = [(p["x"], p["z"], PROP_KINDS[p["kind"]]["col"][1] * p["scale"])
          for p in PROPS if p["kind"] in _KEEP_KINDS and PROP_KINDS[p["kind"]]["col"]]
_PUSH_KINDS = ("rock", "tree", "crag", "outcrop", "bank", "slab", "boulder_xl",
               "thicket", "log")
_pushed, _worst = 0, 0.0
for p in PROPS:
    if p["kind"] not in _PUSH_KINDS:
        continue
    k = PROP_KINDS[p["kind"]]
    spec = k.get("col")
    if spec and spec[0] == "circle":
        pr = spec[1] * p["scale"]
    elif spec and spec[0] == "box":
        pr = math.hypot(spec[1], spec[2]) * p["scale"]
    else:
        pr = {"crag": 1.05, "thicket": 1.25, "outcrop": 0.85, "bank": 0.95,
              "slab": 0.80, "boulder_xl": 1.05}.get(p["kind"], 0.7) * p["scale"]
    for (ax, az, ar) in _posts:
        dx, dz = p["x"] - ax, p["z"] - az
        d = math.hypot(dx, dz)
        need = pr + ar + 0.18                 # 0.18m = 눈에 보이는 최소 틈
        if d >= need:
            continue
        _worst = max(_worst, need - d)
        if d < 1e-4:
            dx, dz, d = 1.0, 0.0, 1.0
        p["x"] += dx / d * (need - d)
        p["z"] += dz / d * (need - d)
        _pushed += 1
print("[관통정리] 선돌·석등·석주 %d개 기준으로 소품 %d개를 밀어냈다 (최대 %.2fm). "
      "★건너뛰지 않고 밀어냈다 = 공용 rnd 소비와 개수가 그대로다"
      % (len(_posts), _pushed, _worst))

# ── ★v94. 스폰 정면 통로 되찾기 ─────────────────────────────
# "스폰마다 정면 15m x 폭 4.4m 를 비운다"는 v79 계약이다(첫 15초를 여기서 증명한다).
# 그런데 그걸 지키는 장치가 **배치 시점의 lane_clear() 하나**뿐이라, 배치 순서가
# 조금만 밀려도(이번엔 수풀 세 곳이 늘면서 공용 rnd 가 밀렸다) 바위 하나가
# 통로 한복판에 들어앉는다. 실제로 SPAWN_1 정면 14.8m 가 막혔다.
# 여기서 **사후에 한 번 더** 옆으로 밀어낸다. 개수도 난수도 안 건드린다.
# ★앞뒤로 밀면 통로가 짧아질 뿐이라 옆으로만 민다(가까운 쪽 가장자리로).
_lane_push, _lane_worst = 0, 0.0
for p in PROPS:
    k = PROP_KINDS[p["kind"]]
    spec = k.get("col")
    if not p["collide"] or not spec:
        continue
    pr = (spec[1] if spec[0] == "circle" else math.hypot(spec[1], spec[2])) * p["scale"]
    for (_sx, _sz, _dx, _dz) in SPAWN_LANES:
        _t = (p["x"] - _sx) * _dx + (p["z"] - _sz) * _dz          # 통로 방향 거리
        # ★검사식은 t=0..15 를 0.4m 간격으로 훑으면서 한가운데는 몸반경 0.55 까지
        #   넣어 본다. 그래서 소품 중심이 통로 끝에서 (반지름 + 0.55) 만큼 더 나가
        #   있어도 걸린다. 실제로 이 여유를 안 준 첫 판에서 SPAWN_1 이 0.09m 차이로
        #   안 잡혔다. 검사식보다 넉넉하게 잡는다.
        if not (-pr - 0.6 <= _t <= SPAWN_LANE_LEN + pr + 0.6):
            continue
        _o = -(p["x"] - _sx) * _dz + (p["z"] - _sz) * _dx          # 옆 거리(부호 있음)
        _need = SPAWN_LANE_HALF + pr + 0.25
        if abs(_o) >= _need:
            continue
        _s = 1.0 if _o >= 0 else -1.0
        _push = _need - abs(_o)
        _lane_worst = max(_lane_worst, _push)
        p["x"] += -_dz * _s * _push
        p["z"] += _dx * _s * _push
        _lane_push += 1
print("[통로정리] 스폰 정면 통로에 걸린 막는 소품 %d개를 옆으로 밀어냈다 (최대 %.2fm)"
      % (_lane_push, _lane_worst))


# ── 배치 완료. 모양을 만들고 콜라이더를 뽑는다 ──────────────
build_props()
emit_prop_colliders()
print("[프롭] 총 %d개 / %d종" % (len(PROPS), len(PROP_KINDS)))
for name in sorted(PROP_KINDS, key=lambda k: -PROP_KINDS[k]["n"]):
    k = PROP_KINDS[name]
    colspec = "없음" if k["col"] is None else (
        "원 r%.2f" % k["col"][1] if k["col"][0] == "circle"
        else "박스 %.2fx%.2f" % (k["col"][1], k["col"][2]))
    print("   %-15s %4d개 (막는 것 %3d) 콜라이더 %-12s %s%s"
          % (name, k["n"], k["ncol"], colspec,
             "[외부 glb] " if name in EXTERNAL_KINDS else "", k["desc"]))
print("[외부 프롭] %d개 = props[] 로 내보내고 이 glb 에는 안 굽는다 (%s)"
      % (sum(PROP_KINDS[n]["n"] for n in EXTERNAL_KINDS), ", ".join(sorted(EXTERNAL_KINDS))))
print("[충돌] %d개 (칸 격자 %d + 프롭 %d)" %
      (len(COLLIDERS), len(wall_rects) + len(outer_rects) + len(bld_rects),
       len(COLLIDERS) - len(wall_rects) - len(outer_rects) - len(bld_rects)))


# ─────────────────────────────────────────────────────────────
# 14.5) 자기 검증 — ★굽는 쪽이 스스로 증명한다
# ─────────────────────────────────────────────────────────────
# ★칸 격자(3.2m)로만 확인하면 소품이 만든 사고를 못 본다. 실제로 v67 첫 굽기에서
#   칸 격자로는 완벽했는데 쓰러진 거목 + 선돌 두 짝이 EXIT_2 를 봉인해서 탈출이
#   불가능했다. 그래서 여기서는 web/nav.js 와 **똑같은 규칙**으로 1.6m 격자를 깔고
#   콜라이더 전부를 넣어서 다시 잰다. 여기 찍히는 걷기 가능 %는 게임 콘솔의
#   '[nav] 격자 ... 걸을 수 있는 칸' 과 같은 숫자여야 한다.
NCELL, NR = 1.6, 0.55          # nav.js CELL / CELL_R
NG = int(SIZE / NCELL)
_bk = {}                       # 성능용 버킷 (4m)


def _bucket_put(key, item):
    _bk.setdefault(key, []).append(item)


for _c in COLLIDERS:
    if _c["type"] == "circle":
        x0, x1 = _c["x"] - _c["r"], _c["x"] + _c["r"]
        z0, z1 = _c["z"] - _c["r"], _c["z"] + _c["r"]
    else:
        x0, x1 = _c["x"] - _c["hx"], _c["x"] + _c["hx"]
        z0, z1 = _c["z"] - _c["hz"], _c["z"] + _c["hz"]
    for _i in range(int((x0 - 1.2 + HALF) // 4.0), int((x1 + 1.2 + HALF) // 4.0) + 1):
        for _j in range(int((z0 - 1.2 + HALF) // 4.0), int((z1 + 1.2 + HALF) // 4.0) + 1):
            _bucket_put((_i, _j), _c)


def hits(px, pz, r, minh=0.0):
    for c in _bk.get((int((px + HALF) // 4.0), int((pz + HALF) // 4.0)), ()):
        if c["h"] < minh:
            continue
        if c["type"] == "circle":
            dx, dz = px - c["x"], pz - c["z"]
            rr = c["r"] + r
            if dx * dx + dz * dz < rr * rr:
                return True
        else:
            ax, az = abs(px - c["x"]) - c["hx"], abs(pz - c["z"]) - c["hz"]
            if ax >= r or az >= r:
                continue
            if ax > 0 and az > 0:
                if ax * ax + az * az < r * r:
                    return True
            else:
                return True
    return False


nwalk = [[0] * NG for _ in range(NG)]
_open = 0
for r in range(NG):
    for c in range(NG):
        ok = 0 if hits(-HALF + (c + 0.5) * NCELL, -HALF + (r + 0.5) * NCELL, NR) else 1
        nwalk[r][c] = ok
        _open += ok
print("[검증] 걷기 가능 %d/%d = %.1f%%  (1.6m 격자·반경 0.55. nav.js 와 같은 규칙)"
      % (_open, NG * NG, _open * 100.0 / (NG * NG)))


def _ncell(x, z):
    return (max(0, min(NG - 1, int((x + HALF) / NCELL))),
            max(0, min(NG - 1, int((z + HALF) / NCELL))))


def _near_open(c, r):
    if nwalk[r][c]:
        return (c, r)
    for rad in range(1, 6):
        for dr in range(-rad, rad + 1):
            for dc in range(-rad, rad + 1):
                nc, nr = c + dc, r + dr
                if 0 <= nc < NG and 0 <= nr < NG and nwalk[nr][nc]:
                    return (nc, nr)
    return None


def _flood(x, z):
    st = _near_open(*_ncell(x, z))
    seen = set()
    if not st:
        return seen
    stack = [st]
    seen.add(st)
    while stack:
        c, r = stack.pop()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if 0 <= nc < NG and 0 <= nr < NG and nwalk[nr][nc] and (nc, nr) not in seen:
                seen.add((nc, nr))
                stack.append((nc, nr))
    return seen


_reach = _flood(gx_of(SPAWN_CELLS[0][0]), gz_of(SPAWN_CELLS[0][1]))
_fail = []
_targets = [("BOSS", BOSS_X, BOSS_Z)]
_targets += [("SPAWN_%d" % (i + 1), gx_of(c), gz_of(r))
             for i, (c, r) in enumerate(SPAWN_CELLS)]
_targets += [("EXIT_%d" % (i + 1), gx_of(c), gz_of(r))
             for i, (c, r) in enumerate(EXIT_CELLS)]
_targets += [("MOB_%d" % (i + 1), gx_of(c), gz_of(r))
             for i, (c, r) in enumerate(MOB_CELLS)]
for bi, reg in enumerate(BUSH_CELLS):
    _targets.append(("BUSH_%02d" % (bi + 1), gx_of(reg[0][0]), gz_of(reg[0][1])))
for (nm, x, z) in _targets:
    if _near_open(*_ncell(x, z)) not in _reach:
        _fail.append(nm)
print("[검증] SPAWN_1 에서 못 닿는 지점: %s" % (_fail if _fail else "없음"))

# 통로 폭 (가로 span 과 세로 span 중 좁은 쪽)
_hs = [[0] * NG for _ in range(NG)]
_vs = [[0] * NG for _ in range(NG)]
for r in range(NG):
    c = 0
    while c < NG:
        if not nwalk[r][c]:
            c += 1
            continue
        c2 = c
        while c2 + 1 < NG and nwalk[r][c2 + 1]:
            c2 += 1
        for k in range(c, c2 + 1):
            _hs[r][k] = (c2 - c + 1) * NCELL
        c = c2 + 1
for c in range(NG):
    r = 0
    while r < NG:
        if not nwalk[r][c]:
            r += 1
            continue
        r2 = r
        while r2 + 1 < NG and nwalk[r2 + 1][c]:
            r2 += 1
        for k in range(r, r2 + 1):
            _vs[k][c] = (r2 - r + 1) * NCELL
        r = r2 + 1
_wd = sorted(min(_hs[r][c], _vs[r][c]) for r in range(NG) for c in range(NG) if nwalk[r][c])
print("[검증] 통로 폭 중앙값 %.1fm / 6.4m 미만 면적 %.0f%% / 3.2m 이하 %.0f%%"
      % (_wd[len(_wd) // 2],
         sum(1 for w in _wd if w < 6.4) * 100.0 / len(_wd),
         sum(1 for w in _wd if w <= 3.3) * 100.0 / len(_wd)))

# 시선 사거리. 걷기 가능한 20곳에서 8방향
_pts = []
for _gx in (-32, -16, 0, 16, 32):
    for _gz in (-32, -16, 0, 16, 32):
        _cr = _near_open(*_ncell(_gx, _gz))
        if _cr:
            _pts.append((-HALF + (_cr[0] + 0.5) * NCELL, -HALF + (_cr[1] + 0.5) * NCELL))
for _mh, _nm in ((0.0, "충돌 격자 그대로"), (CHAR_H, "캐릭터 키보다 높은 것만")):
    _v = []
    for (x, z) in _pts:
        for k in range(8):
            a = k * math.pi / 4
            dx, dz = math.cos(a), math.sin(a)
            d = 0.4
            while d < 60.0:
                if hits(x + dx * d, z + dz * d, 0.0, _mh):
                    break
                d += 0.25
            _v.append(min(d, 60.0))
    _v.sort()
    print("[검증] 시선 사거리 [%s] %d곳x8방향 중앙값 %.1fm / 평균 %.1fm"
          % (_nm, len(_pts), _v[len(_v) // 2], sum(_v) / len(_v)))


# 요괴 개별 자리 x 수풀. ★무리 중심만 보면 이 흠을 또 만든다(예전 BUSH_10 은 0.02m)
def _hash1(n):
    x = math.sin(n * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


_ws, _nspot, _bad2 = 1e9, 0, []
_brects = [("BUSH_%02d" % (bi + 1), gx_of(c), gz_of(r))
           for bi, reg in enumerate(BUSH_CELLS) for (c, r) in reg]
for gi, (mc, mr) in enumerate(MOB_CELLS):
    cx0, cz0 = gx_of(mc), gz_of(mr)
    cnt = 3 + (gi % 3)                      # enemy.js groupsFromMobs
    for k in range(cnt):
        ang = (k / float(cnt)) * 2 * math.pi + gi * 0.7
        rr2 = 2.4 * (0.45 + 0.55 * _hash1(gi * 31 + k))
        sx2, sz2 = cx0 + math.cos(ang) * rr2, cz0 + math.sin(ang) * rr2
        _nspot += 1
        if hits(sx2, sz2, 0.34):
            _bad2.append("MOB_%d#%d 가 벽 속" % (gi + 1, k))
        for (bid, bx3, bz3) in _brects:
            dd = math.hypot(max(0.0, abs(sx2 - bx3) - CELL / 2),
                            max(0.0, abs(sz2 - bz3) - CELL / 2))
            _ws = min(_ws, dd - 0.79)       # 배회 0.45 + 몸반경 0.34
            # ★v79. 기준을 0 에서 0.8m 로 올렸다. 딱 붙지만 않으면 된다가 아니라
            #   "수풀에 들어간 순간 몸이 요괴에 닿지 않는다"가 되게.
            if dd - 0.79 < 0.80:
                _bad2.append("MOB_%d#%d 가 %s 에서 %.2fm" % (gi + 1, k, bid, dd - 0.79))
print("[검증] 요괴 자리 %d개 / 수풀까지 최소 여유 %.2fm / 위반 %s"
      % (_nspot, _ws, _bad2 if _bad2 else "0건"))

# ── 스폰 정면 통로 ★"첫 15초" 를 여기서 증명한다 ────────────
# 격자만 보면 못 잡는다. 옛 SPAWN_1 정면 10.2m 를 막고 있던 건 격자 지형이 아니라
# 바위 무더기 프롭이었다. 그래서 콜라이더 전부를 넣고 실제로 걸어 본다.
print("[검증] 스폰 정면 %.0fm x 폭 %.1fm 통로 (콜라이더 전부 기준)"
      % (SPAWN_LANE_LEN, SPAWN_LANE_HALF * 2))
_lane_bad = 0
for _i, (_sx, _sz, _dx, _dz) in enumerate(SPAWN_LANES):
    _blk, _t = None, 0.0
    while _t <= SPAWN_LANE_LEN + 1e-6 and _blk is None:
        for _s in (-1.0, -0.5, 0.0, 0.5, 1.0):
            _o = _s * SPAWN_LANE_HALF
            if hits(_sx + _dx * _t - _dz * _o, _sz + _dz * _t + _dx * _o, 0.0):
                _blk = (_t, _o)
                break
        # 한가운데는 캐릭터 몸반경까지 넣어서 본다
        if _blk is None and hits(_sx + _dx * _t, _sz + _dz * _t, 0.55):
            _blk = (_t, 0.0)
        _t += 0.4
    _edge = min(HALF - abs(_sx), HALF - abs(_sz))
    print("   SPAWN_%d (%.1f, %.1f) yaw %.3f 경계까지 %.1fm  %s"
          % (_i + 1, _sx, _sz, math.atan2(_dx, _dz), _edge,
             "정면 트임" if _blk is None
             else "★막힘 %.1fm 앞(옆 %.1f)" % _blk))
    if _blk is not None:
        _lane_bad += 1
if _lane_bad:
    print("[경고] 스폰 정면 통로가 막힌 곳 %d 곳. SPAWN_CELLS 를 다시 잡아라" % _lane_bad)

# ── 여울목: 콜라이더로 뚫린 틈 ↔ 표식 대조 ──────────────────
# ★"밟을 수 있게 생긴 물건이 실제로 건널 수 있는 자리에만 있는가"를 눈이 아니라
#   콜라이더로 증명한다. 개울이 흐르는 띠를 세로로 훑어 남북이 통하는 x 구간을 뽑고,
#   그 구간 밖에 표식이 하나라도 있으면 거짓말이므로 소리를 지른다.
_srow = sorted(set(r for (_, r) in WATER_CELLS))
_z0 = -HALF + min(_srow) * CELL          # 개울 띠 북쪽 끝
_z1 = -HALF + (max(_srow) + 1) * CELL    # 남쪽 끝
_gap_cols = []
for _c in range(NG):
    _x = -HALF + (_c + 0.5) * NCELL
    _r0 = max(0, int((_z0 + HALF) / NCELL))
    _r1 = min(NG - 1, int((_z1 + HALF) / NCELL))
    if all(nwalk[_rr][_c] for _rr in range(_r0, _r1 + 1)):
        _gap_cols.append(_c)
_gaps = []
for _c in _gap_cols:
    if _gaps and _c == _gaps[-1][1] + 1:
        _gaps[-1] = (_gaps[-1][0], _c)
    else:
        _gaps.append((_c, _c))
_gap_rng = [(-HALF + a * NCELL, -HALF + (b + 1) * NCELL) for (a, b) in _gaps]
print("[검증] 개울 띠 z %.1f ~ %.1f. 콜라이더 기준 남북이 통하는 x 구간 %d 곳"
      % (_z0, _z1, len(_gap_rng)))
for (a, b) in _gap_rng:
    print("        x %7.1f ~ %6.1f  (폭 %4.1fm)" % (a, b, b - a))
_mark_bad = []
for (mx, mz, mk) in FORD_MARKS:
    if not any(a - 0.9 <= mx <= b + 0.9 for (a, b) in _gap_rng):
        _mark_bad.append("%s(%.1f, %.1f)" % (mk, mx, mz))
_gap_nomark = []
for (a, b) in _gap_rng:
    if not any(a <= mx <= b for (mx, _, _) in FORD_MARKS):
        _gap_nomark.append("x %.1f~%.1f" % (a, b))
print("[검증] 여울목 표식 %d개 / 틈 밖에 있는 표식 %s / 표식 없는 틈 %s"
      % (len(FORD_MARKS), _mark_bad if _mark_bad else "0건",
         _gap_nomark if _gap_nomark else "0건"))

# ── 경계 밖으로 새어 나간 소품 ──────────────────────────────
# ★props[] 는 게임이 그대로 심는다. bounds 밖으로 나가면 배후 스커트 위에
#   나무가 둥둥 뜬 것처럼 보인다(QA #8 의 "경계 밖 소품"). 배후 숲은 소품이 아니라
#   이 glb 안에 구운 지오메트리라 여기 안 걸린다.
_oob = [p for p in PROPS if abs(p["x"]) > HALF or abs(p["z"]) > HALF]
print("[검증] bounds 밖 소품 %s" % (["%s(%.1f,%.1f)" % (p["kind"], p["x"], p["z"])
                                     for p in _oob] if _oob else "0건"))


# ─────────────────────────────────────────────────────────────
# 15) 바닥 텍스처 (2048). 구역 색은 전부 여기서 나온다.
# ─────────────────────────────────────────────────────────────
RES = 2048


def box_blur(a, rad):
    """누적합 박스 블러. ★cumsum 앞에 0 줄을 붙여야 길이가 맞는다."""
    if rad < 1:
        return a
    k = 2 * rad + 1
    p = np.pad(a.astype(np.float32), rad, mode="edge")
    cs = np.concatenate([np.zeros((1, p.shape[1]), np.float32),
                         np.cumsum(p, axis=0, dtype=np.float32)], axis=0)
    a2 = (cs[k:, :] - cs[:-k, :]) / k
    cs2 = np.concatenate([np.zeros((a2.shape[0], 1), np.float32),
                          np.cumsum(a2, axis=1, dtype=np.float32)], axis=1)
    return (cs2[:, k:] - cs2[:, :-k]) / k


def noise(cells, seed, blur=None):
    g = np.random.default_rng(seed)
    small = g.random((cells, cells)).astype(np.float32)
    rep = RES // cells + 1
    big = np.repeat(np.repeat(small, rep, 0), rep, 1)[:RES, :RES]
    return box_blur(big, blur if blur is not None else rep // 2)


px = (np.arange(RES) + 0.5) / RES
gxs = -HALF + px * SIZE
gzs = HALF - px * SIZE
# ★칸 경계를 그대로 칠하면 바닥에 직각 격자가 그려져서 "자연"이 아니라 "타일"로
#   보인다. 칸을 고르는 좌표 자체를 저주파 노이즈로 휘게 해서 경계를 물결지게 만든다.
#   진폭은 0.2칸(0.64m). 이보다 크면 색과 실제 충돌이 어긋나 거짓말이 된다.
WARP = 0.20

# 칸 종류 번호. 0/5/6/7/9 = 못 가는 곳, 1/2/3/8 = 걸을 수 있는 곳, 4 = 숨는 수풀
(K_ROCK, K_PATH, K_OPEN, K_BOSS, K_BUSH, K_THICK, K_WATER, K_MOUND, K_FORD,
 K_LOW) = range(10)
kind_num = np.zeros((GRID, GRID), np.int32)
for r in range(GRID):
    for c in range(GRID):
        ch = grid[r][c]
        if ch == W_:
            t = terr[(c, r)]
            kind_num[r, c] = {T_CRAG: K_ROCK, T_CLIFF: K_ROCK, T_THICKET: K_THICK,
                              T_WATER: K_WATER, T_MOUND: K_MOUND, T_LOW: K_LOW}[t]
        elif ch == BLD:
            kind_num[r, c] = K_ROCK
        elif ch == PATH:
            kind_num[r, c] = K_PATH
        elif ch == OPEN:
            kind_num[r, c] = K_OPEN
        else:
            kind_num[r, c] = K_BOSS
# ★v79. 여울목 색을 건너는 방향으로 두 칸 더 이어 붙인다(FORD_PAINT).
#   6.4 x 9.6m 짜리 창백한 띠가 파란 선을 가로질러 뚫고 나가는 그림이 된다.
for (c, r) in FORD_PAINT:
    if grid[r][c] not in (W_, BLD):
        kind_num[r, c] = K_FORD
for (c, r) in BUSH_SET:
    kind_num[r, c] = K_BUSH

_wx = (noise(26, 91, blur=12) - 0.5) * 2.0
_wz = (noise(26, 92, blur=12) - 0.5) * 2.0
_cf = np.clip((gxs[None, :] + HALF) / CELL + _wx * WARP, 0, GRID - 1e-4).astype(np.int32)
_rf = np.clip((gzs[:, None] + HALF) / CELL + _wz * WARP, 0, GRID - 1e-4).astype(np.int32)
K = kind_num[_rf, _cf]

# sRGB 색. ★이 표가 "길과 벽이 눈으로 구분되는가"의 전부다.
#
# ★★v96 전면 재조율 — 오너 판정 "레퍼런스(롤 실물)처럼 해라. 지금처럼 말고".
#   격차의 기계적 원인을 실측으로 특정했다(tools/color_contract.py):
#
#     조명이 아니라 **ACES 톤매핑**이다. 평평한 바닥에 닿는 빛의 합은 1.00 인데
#     (실측 조도 [0.99, 0.99, 1.00] · 오차 2.9/255), ACES 는 밝은 쪽에서 채도를
#     통째로 씻어낸다. 8x8 색표를 바닥에 굽고 부감으로 읽은 표:
#
#         칠한 V 37% -> 화면 채도가 **올라간다** (S 36 -> 44)
#         칠한 V 60% -> 거의 그대로            (S 36 -> 35)
#         칠한 V 83% -> 반 토막                (S 36 -> 20)
#
#   v67~v95 의 팔레트는 전부 V 71~80% 였다. 즉 **밝게 칠할수록 파스텔이 되는 구간**에
#   팔레트를 통째로 올려 두고 "왜 파스텔이지" 를 고민하고 있었던 것이다.
#   그래서 팔레트를 V 34~59% 로 내린다. 화면 밝기는 매크로 볕(아래)이 되돌린다.
#
# ★여기 적힌 값은 **칠할 색**이고, 주석의 화면색은 tools/color_contract.py 가
#   같은 식으로 계산한 값이다(실측으로 맞춘 모델, 최대오차 8.6/255).
#   색을 고치려거든 `python3 tools/color_contract.py to <화면목표hex>` 로 뽑아라.
#   감으로 고치면 화면에서 딴 색이 나온다 — 그게 이 맵의 색계약 함정이다.
#
#   색 규칙은 그대로다. 걸을 수 있는 곳(흙길·초원·보스 마당·여울목)이 밝고 따뜻하고,
#   못 가는 곳(바위·너덜·덤불·둔덕)이 어둡고 차갑다. 폭이 좁아진 게 아니라
#   **양쪽이 같이 내려갔다**(대비 관계는 아래 [바닥색규칙] 줄이 잰다).
PAL = {
    K_ROCK:  (0x50, 0x57, 0x55),   # 화면 #4d5654  바위 그늘. 제일 어둡고 차갑다
    K_LOW:   (0x64, 0x6a, 0x67),   # 화면 #6a726f  너덜지대. 바위보다 밝지만 여전히 차갑다
    K_PATH:  (0x97, 0x77, 0x4a),   # 화면 #a8854e  밟혀 다져진 흙길. 제일 밝고 따뜻하다
    K_OPEN:  (0x66, 0x81, 0x47),   # 화면 #709049  초원. ★레퍼런스 잔디와 같은 색상대(H 80)
    K_BOSS:  (0x88, 0x6f, 0x49),   # 화면 #97794a  짓밟힌 흙 (길보다 붉고 탁하다)
    K_BUSH:  (0x45, 0x5a, 0x34),   # 화면 #3d5a2a  숨는 수풀 바닥
    K_THICK: (0x33, 0x41, 0x2d),   # 화면 #24361f  막는 초목. 제일 어두운 초록
    K_WATER: (0x46, 0x78, 0x81),   # 화면 #43848f  개울 바닥칠
    K_MOUND: (0x66, 0x54, 0x3f),   # 화면 #6a5238  둔덕 흙
    K_FORD:  (0x66, 0x71, 0x6b),   # 화면 #6d7c75  여울목. 젖은 돌
    # ★여울목이 화면에서 **콘크리트 광장**으로 보였다(9차 실측 #c6cbc7, 명도 199).
    #   3.2m 물칸 좌우로 두 칸씩 이어 붙인 6.4x9.6m 짜리 창백한 판이라 면적이 크다.
    #   "물가에서 유일하게 밝다" 는 여전히 참이지만 기준이 초원이므로 같이 내렸다.
}
col_img = np.zeros((RES, RES, 3), np.float32)
for k, (r8, g8, b8) in PAL.items():
    m = (K == k)
    col_img[m] = (r8 / 255.0, g8 / 255.0, b8 / 255.0)

# 칸 경계를 흐려서 격자 티를 없앤다(손그림 느낌). 자연 지형이라 더 세게 흐린다
for ch in range(3):
    col_img[:, :, ch] = box_blur(col_img[:, :, ch], 9)

# ★v90. 오너 판정 "바닥이 롤 같아야 한다 / 바닥도 자글자글하다" 를 받아 **잔얼룩을
#   눌렀다.** 롤 지면 문법의 첫 줄은 "큰 면적의 깨끗한 평칠"이다.
# ★v96. 오너 보충 지시 "깔끔한 그림 느낌" 을 받아 한 단 더 정리했다.
#   37cm 알갱이(gr)를 통째로 뺐다 — 그 대역은 타일 네 장이 훨씬 잘 그리고 있고,
#   베이스컬러에 같은 대역을 또 얹으면 **두 겹이 서로 간섭해서 지저분해진다.**
#   남긴 것은 2m 이끼 얼룩과 60cm 색 변주뿐이고 둘 다 세기를 낮췄다.
mo = noise(48, 11, blur=14)
sp = noise(160, 22, blur=4)
moss_tint = np.zeros((RES, RES, 3), np.float32)
moss_tint[:, :, 0] = 0.27
moss_tint[:, :, 1] = 0.37
moss_tint[:, :, 2] = 0.19
# 이끼는 얼룩으로만. 세게 깔면 구역 색이 전부 초록으로 뭉개져서
# "여기가 수풀"이라는 신호를 못 준다(예전 렌더에서 실제로 그랬다).
mmask = np.clip((mo - 0.62) * 2.8, 0, 1)[:, :, None] * 0.14
col_img = col_img * (1 - mmask) + moss_tint * mmask
col_img *= (0.94 + 0.12 * sp)[:, :, None]

# ── ★★v96. 매크로 볕·그늘 ────────────────────────────────────
# 오너 레퍼런스와 우리 판의 **1번 격차가 명암 폭**이었다(심사 실측: 명도 sd
# 0.043 ↔ 롤 0.100). 9차에서 톤을 통일하면서 폭까지 같이 죽인 것이다.
# 통일은 지키고 폭만 되살린다 — 그늘은 진하게, 볕은 또렷하게.
#
# ★왜 굳이 바닥 텍스처에 굽는가. 실시간 그림자(key light)의 상자가 캐릭터
#   ±10m 뿐이라 **그 밖의 지면에는 그림자가 한 톨도 없다.** 화면의 2/3 가
#   그늘 없는 평칠이었다. 구운 그늘은 그리는 값이 0 이고 맵 끝까지 간다.
# ★곱수의 평균을 **걸을 수 있는 면에서 정확히 1** 로 맞춘다. 그래야 구역색
#   (= 색 규칙)이 한 톨도 안 밀리고 폭만 벌어진다. 위 팔레트 주석의 화면색은
#   이 평균이 1 이라는 전제 위에 서 있다.
# ★sRGB 공간에서 곱한다. 감마 2.2 때문에 곱수 0.72 가 빛으로는 0.47 이다
#   = 눈에 보이는 그늘의 깊이가 숫자보다 훨씬 깊다. 그래서 폭이 좁아 보여도 충분하다.
_MACRO_AMP = 0.150          # 볕·그늘 진폭(sRGB 곱수). 실측으로 고른 값 — 아래 참조
_px_m = RES / SIZE          # 21.33 px/m
# ① 볕 얼룩. 13.7m 와 7.4m 두 겹. ★고주파를 섞지 않는다 — 그건 얼룩이지 볕이 아니다
_sun = noise(7, 7701, blur=60) * 0.62 + noise(13, 7702, blur=32) * 0.38
_sun = (_sun - float(_sun.mean())) / max(float(_sun.std()), 1e-6)
macro = 1.0 + np.clip(_sun, -2.6, 2.6) * _MACRO_AMP
# ② 막는 덩어리가 드리우는 그늘. 해는 (5, 9, 4) 에서 온다 = 그늘은 -x·-z 로 눕는다.
#    높이 1m 당 (-0.556, -0.444)m. 덩어리 높이를 3.2m 로 보면 (-1.78, -1.42)m 밀린다.
#    ★배열의 0행이 z=+48 이므로 z 가 **줄어드는** 쪽은 행이 **느는** 쪽이다.
_blk = np.isin(K, (K_ROCK, K_THICK, K_MOUND, K_LOW)).astype(np.float32)
_shf = box_blur(_blk, 15)
_cast = np.roll(np.roll(_shf, int(1.42 * _px_m), axis=0), int(-1.78 * _px_m), axis=1)
macro *= (1.0 - 0.34 * np.clip(_cast, 0, 1))     # 드리운 그늘(레퍼런스의 큰 어두운 면)
macro *= (1.0 - 0.20 * np.clip(_shf, 0, 1))      # 발치 그늘(지형이 바닥에 앉아 보인다)
# ③ 물칸 발치는 예전대로 조금만(젖은 띠가 따로 그린다)
macro *= (1.0 - 0.14 * np.clip(box_blur((K == K_WATER).astype(np.float32), 15), 0, 1))
# ④ 평균 1 로 되돌린다. ★걸을 수 있는 면에서만 잰다 — 못 가는 칸까지 넣으면
#    맵 구성이 바뀔 때마다 초원 밝기가 조용히 따라 움직인다.
_wk = np.isin(K, (K_PATH, K_OPEN, K_BOSS, K_FORD)).astype(np.float32)
macro /= max(float((macro * _wk).sum() / max(float(_wk.sum()), 1.0)), 1e-6)
macro = np.clip(macro, 0.56, 1.34)
col_img *= macro[:, :, None]
print("[매크로 명암] 곱수 %.3f~%.3f (걸을수있는면 평균 %.3f · sd %.3f)"
      % (float(macro.min()), float(macro.max()),
         float((macro * _wk).sum() / max(float(_wk.sum()), 1.0)),
         float(macro[_wk > 0].std())))

# ── 개울 기슭의 젖은 돌 띠 ★"여기는 물가다"를 색으로도 박는다 ──
# ★v79. 기슭에서 둥근 바위를 뺐으니(디딤돌로 읽혀서) 신호를 바닥이 대신 낸다.
#   물칸 바깥으로 0.5m 폭의 젖고 어두운 띠. 여울목 색(K_FORD) 위에는 안 올린다.
#   건너는 자리만 창백하게 남아야 대비가 산다.
# ★v89 (QA S8). 이 띠도 물칸을 그대로 따라가는 **평행한 직선 두 줄**이었다.
#   수면 리본을 굽혀 놓고 바닥칠이 자로 그은 줄이면 다시 상자로 읽힌다.
#   문턱과 세기를 저주파 노이즈로 흔들어 폭이 자리마다 달라지게 한다
#   (0.69m 짜리 얼룩. 여울목 색 위에 안 올린다는 규칙은 그대로다).
_wmask = (K == K_WATER).astype(np.float32)
_bnz = noise(140, 941, blur=6)                    # 96/140 = 0.69m 짜리 얼룩
_bank = (np.clip((box_blur(_wmask, 11) - 0.05 - 0.19 * (_bnz - 0.5)) / 0.34, 0, 1)
         * (1.0 - _wmask) * (K != K_FORD).astype(np.float32)
         * (0.30 + 0.30 * _bnz))
col_img = col_img * (1 - _bank[:, :, None]) + \
    np.array((0.29, 0.31, 0.28), np.float32)[None, None, :] * _bank[:, :, None]

# ── ★v94. 물가 포말 선 ───────────────────────────────────────
# 심사: "물가 포말이 전무하다." 처음엔 수면 메시의 셰이더에서 그렸는데, 화면을 보고
# **자리가 틀렸다**는 걸 알았다. 수면 리본은 반폭이 0.8m 라 3.2m 짜리 물칸의
# **한가운데 1.6m** 만 덮는다(인셋 0.80 + 바닥칠 휨 0.64 예산 때문에 더 못 넓힌다).
# 즉 메시 가장자리는 물가가 아니라 **물 한복판**이다. 거기에 흰 띠를 그리면
# 개울 가운데로 흰 길이 난 그림이 된다(실제로 그렇게 나왔다).
# 그래서 층을 나눈다.
#   뭍 → [젖은 어두운 띠] → [흰 포말 선] → 칠한 얕은 물 → (메시) 깊은 물
# 포말은 **바닥칠**이 그린다. 물칸 경계에 걸치는 0.35m 짜리 선이고, 같은 저주파
# 노이즈로 문턱을 흔들어 끊어지게 한다(자로 그은 흰 줄이 되면 안 된다).
_edge = box_blur(_wmask, 8)
_foam = (np.clip(1.0 - np.abs(_edge - 0.52) / 0.30, 0, 1)
         * np.clip((_bnz - 0.34) * 3.1, 0, 1)          # 끊어지는 덩어리
         * (K != K_FORD).astype(np.float32) * 0.62)
# ★v96. 흰색을 한 단 내렸다. (0.92,0.95,0.94) 는 화면에서 #dce6e4(명도 90%) 짜리
#   **종이**다. 팔레트를 전체로 내린 뒤에는 그 흰 줄만 튀어서 물가가 아니라
#   "자로 그은 선"으로 읽힌다. 물빛(화면 V 34~56%)과의 대비는 이 값으로도 충분하다.
col_img = col_img * (1 - _foam[:, :, None]) + \
    np.array((0.72, 0.80, 0.77), np.float32)[None, None, :] * _foam[:, :, None]

# ── ★v86. 물칸 **안쪽** 가장자리 그늘 (QA S11) ──────────────
# 수면 메시는 칸 안쪽으로 0.80m 들어와 끝난다(10절 WATER_INSET). 그 끝선이
# 밝은 물칸 바닥 위에 그대로 얹히면 "파란 판때기의 테두리"로 읽힌다.
# 그래서 칸 가장자리에서 안쪽 1.1m 까지를 어둡게 깎아, 메시가 끝나는 자리가
# **얕은 여울에서 깊은 물로 넘어가는 그라데이션** 한가운데에 놓이게 한다.
# 반지름 24px = 96m/2048*24 = 1.13m. 인셋 0.80 이 이 띠 안에 들어온다.
# ★v89. 안쪽 띠도 같은 얼룩으로 흔든다. 수면 리본의 반폭이 자리마다 다르니
#   그 끝선이 놓이는 그라데이션도 같이 흔들려야 두 줄이 안 겹쳐 보인다.
_rim_in = (np.clip((1.0 - box_blur(_wmask, 24)) / 0.55, 0, 1) * _wmask
           * (0.34 + 0.26 * _bnz))
col_img = col_img * (1 - _rim_in[:, :, None]) + \
    np.array((0.20, 0.29, 0.34), np.float32)[None, None, :] * _rim_in[:, :, None]

# ── ★★v96. 강바닥 자갈 ───────────────────────────────────────
# 위 15b 에서 물칸의 지면 타일을 껐다(박석 무늬가 개울 바닥에 깔려 있었다).
# 껐으면 대신 **강바닥을 그려야** 한다. 안 그리면 개울이 단색 파란 판이 된다.
#
# ★여기 해상도는 21 px/m 라 작은 물건을 못 그린다. 그런데 **물속은 그래도 된다** —
#   물이 위를 덮으므로 원래 흐릿하게 보이는 게 맞다. 지름 0.25~0.75m 짜리
#   둥근 자갈(5~16 텍셀)이면 화면에서 자갈로 읽힌다.
# ★색은 물빛이 아니라 **젖은 돌**이다. 파란 필터를 씌우면 9차와 같은 병으로 돌아간다.
_bed = np.zeros((RES, RES), np.float32)
_bedc = np.zeros((RES, RES, 3), np.float32)
_gb = np.random.default_rng(20260811)
_n_bed = 0
_wi, _wj = np.nonzero(_wmask > 0.5)
if len(_wi):
    for _k in range(2600):
        _t = int(_gb.integers(0, len(_wi)))
        _i, _j = int(_wi[_t]), int(_wj[_t])
        _rp = int(_gb.integers(6, 17))               # 0.28 ~ 0.75m
        _i0, _i1 = max(0, _i - _rp), min(RES, _i + _rp + 1)
        _j0, _j1 = max(0, _j - _rp), min(RES, _j + _rp + 1)
        _yy = (np.arange(_i0, _i1)[:, None] - _i).astype(np.float32)
        _xx = (np.arange(_j0, _j1)[None, :] - _j).astype(np.float32)
        _d = np.sqrt(_yy * _yy + (_xx * 1.25) ** 2) / _rp
        _m = np.clip((1.0 - _d) / 0.32, 0, 1) * _gb.uniform(0.55, 1.0)
        # 젖은 자갈: 어두운 회갈색 ~ 옅은 회색. 물빛을 안 섞는다
        _v = _gb.uniform(0.24, 0.52)
        _c = np.array((_v * 1.02, _v * 1.00, _v * 0.92), np.float32)
        _w = _bed[_i0:_i1, _j0:_j1]
        _wc = _bedc[_i0:_i1, _j0:_j1]
        _wc *= (1 - _m)[:, :, None]
        _wc += _m[:, :, None] * _c[None, None, :]
        np.maximum(_w, _m, out=_w)
        _n_bed += 1
_bed = np.clip(_bed, 0, 1) * _wmask * 0.62           # 물이 덮으므로 세게 안 올린다
col_img = col_img * (1 - _bed[:, :, None]) + _bedc * _bed[:, :, None]
print("[텍스처] 강바닥 자갈 %d개 (물칸 면적 %.2f%%)"
      % (_n_bed, float(_wmask.mean()) * 100))

# ── 꽃·풀무더기 ──────────────────────────────────────────────
# ★넓게 트인 초원은 단색이면 아무리 열려 있어도 지루하다. 걸을 수 있는 칸 위에만
#   색 점을 흩어 놓는다. 못 가는 칸으로는 안 번지게 마스크로 자른다
#   (번지면 "밝으면 걸을 수 있다" 규칙이 깨진다).
# ★★v96. 역할을 갈랐다. **또렷한 꽃잎·자갈은 여기가 아니다** —
#   2048 이 96m 라 21 px/m 뿐이라 15cm 짜리 물건을 그리면 화면에서 뭉갠 얼룩이 된다.
#   그 몫은 전용 산포 타일(tools/bake_scatter_tex.py, 241 px/m)이 가져갔다.
#   여기 남은 몫은 **초원의 큰 색 변주**다. 그래서 지름을 키우고(0.7~2.4m) 세기를
#   낮췄다. 색도 형광 파스텔에서 초원 안에 있을 법한 색으로 내렸다
#   (팔레트가 통째로 내려갔으므로 예전 값을 그대로 두면 이것만 형광으로 뜬다).
meadow = np.isin(K, (K_PATH, K_OPEN, K_BOSS, K_FORD)).astype(np.float32)
SPECKS = [((0.72, 0.74, 0.58), 0.26, 0.16),   # 옅은 마른 자리
          ((0.70, 0.64, 0.31), 0.26, 0.18),   # 금빛 마른 풀무리
          ((0.60, 0.47, 0.44), 0.20, 0.09),   # 흙이 비친 자리
          ((0.31, 0.42, 0.22), 0.30, 0.31),   # 진한 풀무더기
          ((0.56, 0.53, 0.34), 0.22, 0.26)]   # 누런 풀
_cum, _acc = [], 0.0
for (_, _, w) in SPECKS:
    _acc += w
    _cum.append(_acc)
_gf = np.random.default_rng(20260810)
n_speck = 0
for _ in range(3000):
    i = int(_gf.integers(0, RES))
    j = int(_gf.integers(0, RES))
    if not meadow[i, j]:
        continue
    u = _gf.random() * _acc
    ki = 0
    while ki < len(_cum) - 1 and u > _cum[ki]:
        ki += 1
    colr, amt, _ = SPECKS[ki]
    rad = int(_gf.integers(15, 52))            # 0.70 ~ 2.44m ★v96. 큰 색 변주로 역할 변경
    i0, i1 = max(0, i - rad), min(RES, i + rad + 1)
    j0, j1 = max(0, j - rad), min(RES, j + rad + 1)
    yy = (np.arange(i0, i1)[:, None] - i).astype(np.float32)
    xx = (np.arange(j0, j1)[None, :] - j).astype(np.float32)
    m = np.clip(1.0 - np.sqrt(yy * yy + xx * xx) / rad, 0, 1) ** 0.75
    m = m * amt * _gf.uniform(0.7, 1.0) * meadow[i0:i1, j0:j1]
    win = col_img[i0:i1, j0:j1]
    col_img[i0:i1, j0:j1] = win * (1 - m[:, :, None]) + \
        np.array(colr, np.float32)[None, None, :] * m[:, :, None]
    n_speck += 1
print("[텍스처] 꽃·풀무더기 %d개" % n_speck)

# 보스 공터 결계 원. 여기가 목적지라는 걸 위에서 한눈에 알려준다
bx_c, bz_c, bhx, bhz = rect_world(*BOSS_ARENA)
dx = (gxs[None, :] - bx_c)
dz = (gzs[:, None] - bz_c)
dist = np.sqrt(dx * dx + dz * dz)
# ★v96. 팔레트를 통째로 내리면서 이 붉은 원만 남아 소리를 지르게 됐다(실측:
#   주변 바닥이 명도 128 인데 원은 채도 73%). 정보(여기가 보스 자리)는 유지하되
#   색을 한 단 눅이고 세기를 낮춘다. 맵에서 붉은색이 여기뿐인 건 그대로다.
for (rad, wid, colr, amt) in ((9.4, 0.55, (0.40, 0.17, 0.15), 0.62),
                              (10.3, 0.30, (0.40, 0.17, 0.15), 0.46),
                              (5.2, 0.35, (0.34, 0.26, 0.18), 0.42)):
    ring = np.clip(1.0 - np.abs(dist - rad) / wid, 0, 1) * amt
    ring = ring * (K == K_BOSS)
    col_img = col_img * (1 - ring[:, :, None]) + \
        np.array(colr, np.float32)[None, None, :] * ring[:, :, None]

walk_mask = np.isin(K, (K_PATH, K_OPEN, K_BOSS, K_BUSH, K_FORD))


def paint_disc(gx, gz, rad, colr, amt):
    """입구·탈출구 바닥 표식. 걸을 수 있는 칸에만 칠한다"""
    global col_img
    d = np.sqrt((gxs[None, :] - gx) ** 2 + (gzs[:, None] - gz) ** 2)
    m = np.clip(1.0 - d / rad, 0, 1) ** 0.6 * amt * walk_mask
    col_img = col_img * (1 - m[:, :, None]) + \
        np.array(colr, np.float32)[None, None, :] * m[:, :, None]


# ★v94 (심사 지적 "근원 없는 주황 원형 얼룩(에어브러시)"). 스폰 표식이
#   반지름 5.4m 짜리 **완벽한 원**에 세기 0.72 로 칠해져 있었다. 맵 어디에도 없는
#   주황색이고, 그 색을 낼 물건이 화면에 하나도 없으니 "지형"이 아니라 "덧칠"로
#   읽힌다. 정보(여기가 시작점)는 남기되 **근원을 준다**:
#     · 색을 밟혀 드러난 흙(K_BOSS 계열의 탁한 갈색)으로 바꾼다 = 맵에 있는 색이다
#     · 세기를 0.72 -> 0.30 으로 낮춘다
#     · 정원 하나 대신 크기·중심이 다른 셋을 겹치고 저주파 노이즈로 윤곽을 깬다
#     · 스플랫에도 흙을 올려(아래 ⑤) 그 자리에 **결**이 생긴다. 색만 있는 얼룩은
#       아무리 옅어도 에어브러시로 보인다
_spawn_nz = noise(150, 4471, blur=5)


def paint_blot(gx, gz, rad, colr, amt, lobes=3, seed=0):
    """윤곽이 깨진 얼룩. 정원 하나로 칠하면 조준 표식으로 보인다(v89 보스 자리와 같은 이유)."""
    g2 = random.Random(seed)
    for _i in range(lobes):
        _a = g2.uniform(0, 2 * math.pi)
        _d = g2.uniform(0.0, rad * 0.42)
        _rr = rad * g2.uniform(0.55, 1.0)
        d = np.sqrt((gxs[None, :] - gx - math.cos(_a) * _d) ** 2
                    + (gzs[:, None] - gz - math.sin(_a) * _d) ** 2)
        # 반지름 자체를 노이즈로 흔든다(0.64m 얼룩). 원이 아니라 번진 자국이 된다
        m = np.clip(1.0 - d / (_rr * (0.78 + 0.44 * _spawn_nz)), 0, 1) ** 0.7
        m = m * amt * walk_mask
        _paint(m, colr)


def _paint(m, colr):
    global col_img
    col_img = col_img * (1 - m[:, :, None]) + \
        np.array(colr, np.float32)[None, None, :] * m[:, :, None]


for _i, (c, r) in enumerate(SPAWN_CELLS):
    paint_blot(gx_of(c), gz_of(r), CELL * 1.55, (0.62, 0.47, 0.32), 0.30,
               lobes=3, seed=6100 + _i)
# 탈출 표식은 **게임 정보**라 남긴다(맵 어디에도 없는 색이 정체다). 다만 같은
# 에어브러시 원이었으므로 윤곽만 깨고 세기를 0.88 -> 0.52 로 낮춘다.
# ★DECO_EXITMARK 지오메트리가 따로 서 있어서 바닥칠이 약해도 못 찾을 일은 없다.
for _i, (c, r) in enumerate(EXIT_CELLS):
    paint_blot(gx_of(c), gz_of(r), CELL * 1.75, (0.52, 0.80, 0.74), 0.52,
               lobes=3, seed=6200 + _i)

# ── 보스 자리에 밴 마른 피 ★v89. 8각 제단(DECO_ALTAR)을 대신한다 ──
# 11절에서 제단을 뺀 자리다. "여기가 보스 자리"라는 정보는 남기되 **지오메트리를
# 하나도 안 쓴다.** 바닥에 스며든 얼룩은 원리상 떠 보일 수가 없고, 탑다운에서
# 보스 발치를 가리지도 않는다.
# ★정원 하나로 칠하면 조준 표식으로 보인다. 크기와 중심이 다른 셋을 겹쳐
#   윤곽을 깨고, 결계 원(위)보다 옅게 둬서 원의 위계를 안 뺏는다.
for (_bdx, _bdz, _brd, _bam) in ((0.0, 0.0, 2.55, 0.50), (0.95, -0.75, 1.65, 0.42),
                                 (-1.05, 0.85, 1.45, 0.38)):
    paint_disc(BOSS_X + _bdx, BOSS_Z + _bdz, _brd, (0.40, 0.20, 0.17), _bam)

# ── ★v94. 소품 접지 그늘(AO) ────────────────────────────────
# 심사 지적: "접지 AO 없음 — 소품이 바닥에 놓인 게 아니라 얹혀 있다."
# 맞는 지적이고 원인이 분명하다. 위 block_mask 는 **칸 격자**를 보고 발치를 누르는데,
# 소품 827개는 격자에 없다(프롭 테이블에서 나온다). 그래서 바위·나무·수풀은
# 발치 그늘을 한 톨도 못 받고 있었다.
#
# ★지오메트리도, 드로우콜도, 반투명 데칼도 안 쓴다. 바닥 베이스컬러에 **굽는다.**
#   2048 이 96m 를 덮으므로 1px = 4.7cm 다. 반지름 1m 짜리 그늘이 21px = 충분히 부드럽다.
#   (v89 에서 제단이 "떠 보인" 이유 셋 중 하나가 정확히 이 그늘의 부재였다.)
# ★걸을 수 있는 칸에만 올린다. 바위 칸은 이미 어두워서 두 번 누르면 검게 탄다.
# ★소품마다 전체 배열을 만들면 827 x 4M 이라 못 돌린다. 꽃 얼룩과 같은 방식으로
#   **자기 창(window)** 안에서만 계산한다.
_AO_R = {                       # 종류별 접지 그늘 반지름 배수와 세기
    "rock": (1.55, 0.40), "crag": (1.35, 0.42), "boulder": (1.70, 0.44),
    "thicket": (1.45, 0.34), "mound": (1.30, 0.30), "tree": (1.25, 0.46),
    "bush": (1.20, 0.26), "log": (1.30, 0.34), "standing_stone": (1.50, 0.40),
    "stone_lantern": (1.50, 0.36), "stone_pillar": (1.60, 0.38),
    "pagoda": (1.20, 0.50), "stone_slab": (1.10, 0.24),
    "cliff_tall": (1.10, 0.34), "outcrop": (1.35, 0.34),
    "boulder_xl": (1.70, 0.46), "bank": (1.30, 0.30), "slab": (1.15, 0.24),
}


def _prop_foot(p):
    """소품이 바닥에 닿는 반지름(m). 콜라이더 규격이 있으면 그걸, 없으면 종류 기본값."""
    k = PROP_KINDS[p["kind"]]
    spec = k.get("col")
    s = p.get("scale", 1.0)
    if spec and spec[0] == "circle":
        return spec[1] * s
    if spec and spec[0] == "box":
        return math.hypot(spec[1], spec[2]) * 0.72 * s
    return {"crag": 1.05, "thicket": 1.25, "bush": 0.95, "cliff_tall": 1.15,
            "outcrop": 0.85, "boulder_xl": 1.05, "bank": 0.95,
            "slab": 0.80}.get(p["kind"], 0.9) * s


_ao = np.zeros((RES, RES), np.float32)
_px_per_m = RES / SIZE
_ao_n = 0
for _p in PROPS:
    _kd = _p.get("as") or _p["kind"]
    _mul, _amt = _AO_R.get(_kd, (1.35, 0.34))
    _rm = _prop_foot(_p) * _mul
    if _rm < 0.25:
        continue
    _rp = int(_rm * _px_per_m)
    _j = int((_p["x"] + HALF) / SIZE * RES)      # 열(= gx 증가 방향)
    _i = int((HALF - _p["z"]) / SIZE * RES)      # 행(0행이 gz=+48)
    _i0, _i1 = max(0, _i - _rp), min(RES, _i + _rp + 1)
    _j0, _j1 = max(0, _j - _rp), min(RES, _j + _rp + 1)
    if _i1 <= _i0 or _j1 <= _j0:
        continue
    _yy = (np.arange(_i0, _i1)[:, None] - _i).astype(np.float32)
    _xx = (np.arange(_j0, _j1)[None, :] - _j).astype(np.float32)
    _d = np.sqrt(_yy * _yy + _xx * _xx) / max(_rp, 1)
    # 발치는 진하고 밖으로 갈수록 급히 옅어진다(제곱). 선형이면 접시처럼 보인다
    _m = np.clip(1.0 - _d, 0, 1) ** 2.1 * _amt
    _w = _ao[_i0:_i1, _j0:_j1]
    np.maximum(_w, _m, out=_w)                   # 겹치면 진한 쪽(더하면 새까매진다)
    _ao_n += 1
_ao *= walk_mask.astype(np.float32)
# 그늘 색은 검정이 아니라 **그 자리 바닥의 어두운 쪽**이다. 검정으로 곱하면
# 채도가 빠져 회색 얼룩이 된다. 색상은 두고 명도만 눌러 살짝 차갑게 민다.
col_img *= (1.0 - _ao * 0.86)[:, :, None]
col_img[:, :, 2] += _ao * 0.020                  # 그늘은 조금 푸르다
print("[텍스처] 소품 접지 그늘 %d개 (평균 %.3f · 최대 %.3f)"
      % (_ao_n, float(_ao.mean()), float(_ao.max())))

# ── ★v96. 판석·석재의 접지 — "떠 보인다" 대응 ────────────────
# 심사: "석판·데칼이 떠 보인다(하드 엣지 + 접지 그림자 없음)."
# 위 AO 는 **원형**이라 네모난 판석의 모서리를 못 잡는다. 그리고 진짜 원인은
# 그림자가 아니라 **경계가 자로 그은 직선**이라는 것이다. 레퍼런스의 석판길은
# 가장자리가 풀에 먹혀 들어가 있고 틈마다 이끼가 올라타 있다.
#
# 지오메트리도 데칼도 안 쓴다. 판석 발치의 **바닥에** 풀·이끼를 물결지게 올린다.
#   ① 판석 반지름의 0.80~1.25 배 되는 고리에 이끼색을 얹는다
#   ② 고리 두께를 저주파 노이즈로 흔들어 **원이 아니라 번진 자국**으로 만든다
#   ③ 안쪽(판석 밑)은 건드리지 않는다 — 판석 메시가 덮으므로 낭비다
# ★판석 메시 자체에 풀을 그리는 게 더 좋지만 그건 slab.glb 의 UV 를 알아야 한다.
#   바닥에서 올려도 화면에서는 "풀이 판석 가장자리를 먹었다"로 읽힌다(판석이 두께
#   0.06m 짜리 납작한 판이라 옆면이 거의 안 보인다).
_SLAB_KINDS = ("slab", "stone_slab", "pagoda", "stone_lantern", "standing_stone")
_ring = np.zeros((RES, RES), np.float32)
_rnz = noise(190, 5573, blur=4)                  # 0.51m 짜리 얼룩
_ring_n = 0
for _p in PROPS:
    _kd = _p.get("as") or _p["kind"]
    if _kd not in _SLAB_KINDS:
        continue
    _rm = _prop_foot(_p)
    _rp = int(_rm * 1.30 * _px_per_m)
    if _rp < 3:
        continue
    _j = int((_p["x"] + HALF) / SIZE * RES)
    _i = int((HALF - _p["z"]) / SIZE * RES)
    _i0, _i1 = max(0, _i - _rp), min(RES, _i + _rp + 1)
    _j0, _j1 = max(0, _j - _rp), min(RES, _j + _rp + 1)
    if _i1 <= _i0 or _j1 <= _j0:
        continue
    _yy = (np.arange(_i0, _i1)[:, None] - _i).astype(np.float32)
    _xx = (np.arange(_j0, _j1)[None, :] - _j).astype(np.float32)
    _d = np.sqrt(_yy * _yy + _xx * _xx) / max(_rm * _px_per_m, 1.0)
    # 고리: 0.78~1.28 사이에서 가장 진하고 양쪽으로 빠진다. 노이즈로 폭을 흔든다
    _c = 1.03 + (_rnz[_i0:_i1, _j0:_j1] - 0.5) * 0.30
    _m = np.clip(1.0 - np.abs(_d - _c) / 0.30, 0, 1) ** 1.4
    _w = _ring[_i0:_i1, _j0:_j1]
    np.maximum(_w, _m, out=_w)
    _ring_n += 1
_ring *= walk_mask.astype(np.float32) * 0.34
col_img = col_img * (1 - _ring[:, :, None]) + \
    np.array((0.30, 0.40, 0.24), np.float32)[None, None, :] * _ring[:, :, None]
print("[텍스처] 판석 발치 풀·이끼 고리 %d개 (평균 %.4f)" % (_ring_n, float(_ring.mean())))

col_img = np.clip(col_img, 0.0, 1.0)

# ── ★v96. 색계약 실측기 (W10T_CALIB=1 일 때만) ────────────────
# 왜 필요한가: 이 맵의 조명은 반구광 1.55 + 해 2.35 + 림 0.55 에 ACES 톤매핑이라
# **바닥에 칠한 색이 화면에 그대로 안 나온다.** 실측하면 베이스 #aabc6b(채도 43%)가
# 화면에서 #c1c792(채도 27%) 로 나온다 — 밝아지고 채도가 빠진다. 그래서 "레퍼런스
# 색으로 칠했다" 는 말이 증명이 안 된다(LOG 색계약 함정: 목표색은 **화면 실측**으로만
# 증명된다).
#   이 모드는 바닥을 6m 짜리 색표로 통째로 덮는다. 부감으로 한 장 찍어 표를 읽으면
#   "칠한 색 -> 화면 색" 대응표가 나오고, 그걸 거꾸로 풀어 팔레트를 정한다.
# ★평소 굽기에는 한 톨도 영향이 없다(환경변수가 없으면 이 블록을 건너뛴다).
# ★rnd 스트림에도 영향이 없다 — 난수를 한 번도 안 쓴다.
if os.environ.get("W10T_CALIB"):
    _PATCH_M = 6.0                      # 한 칸 6m. 부감(dist 105)에서 약 60px 이다
    _pi = (np.arange(RES) / RES * SIZE / _PATCH_M).astype(np.int32)
    _gi = _pi[None, :] % 8              # 열 = 색상/채도
    _gj = _pi[:, None] % 8              # 행 = 명도
    # 색표: 초록 계열을 촘촘히 (지형 팔레트가 사는 자리)
    _cal = np.zeros((8, 8, 3), np.float32)
    for _r8 in range(8):
        for _c8 in range(8):
            _v = 0.14 + _r8 * 0.115     # 명도 0.14 ~ 0.945
            _s = _c8 / 7.0 * 0.85       # 채도 0 ~ 0.85
            _hh = 0.22 if _c8 < 6 else (0.09 if _c8 == 6 else 0.55)   # 초록/흙/물
            import colorsys as _cs
            _cal[_r8, _c8] = _cs.hsv_to_rgb(_hh, _s, _v)
    col_img = _cal[_gj, _gi]
    print("[색계약] 실측 모드. 바닥을 8x8 색표(%.1fm)로 덮었다" % _PATCH_M)

img = bpy.data.images.new("level1_floor", RES, RES, alpha=False)
img.colorspace_settings.name = "sRGB"
rgba = np.ones((RES, RES, 4), np.float32)
# ★상하 뒤집지 않는다. col_img 의 0행은 gz=+48(남쪽)이고 UV 의 v=0 도 남쪽이라 그대로 맞는다.
# ★감마: image.pixels 에 넣은 값이 그대로 바이트로 저장된다(sRGB 여도 변환이 안 걸린다).
#   위에서 고른 sRGB 색을 그대로 넣는 게 맞다. 미리 선형화하면 절반으로 어두워진다.
rgba[:, :, :3] = col_img
img.pixels.foreach_set(rgba.reshape(-1))
img.filepath_raw = os.path.join(TMP, "level1_floor.png")
img.file_format = "PNG"
img.save()
print("[텍스처] %dx%d 생성 -> %s" % (RES, RES, img.filepath_raw))


# ─────────────────────────────────────────────────────────────
# 15b) 스플랫맵 (1024). "이 자리에 어떤 결을 깔 것인가"
# ─────────────────────────────────────────────────────────────
# 위의 2048 베이스컬러는 **구역 색과 전체 명암**을 정한다. 그건 그대로 둔다.
# 여기서 따로 뽑는 한 장은 색이 아니라 **네 개의 가중치**다.
#   R = 풀(tile_grass)  G = 흙(tile_dirt)  B = 판석 파빙(tile_stone)  A = 마른 풀(tile_dry)
# 게임(web/level.js)이 이 넷으로 지면 타일 네 장을 섞어 베이스컬러에 곱한다.
# 타일은 평균이 1 인 곱수라 **구역 밝기는 한 톨도 안 바뀐다.** 결만 생긴다.
#
# ★★v90. 오너 판정: "바닥이 롤 같은 느낌이 나야지. 무조건 흙바닥이 아니라 좀 깔끔하게."
#   전 배정의 문제는 **흙이 주 동선 전부를 덮은 것**이었다. 스폰에서 나와 중앙 대로를
#   지나 보스 어귀까지, 플레이어가 밟는 자리가 전부 황토 흙탕이었다(BEFORE 렌더 참조).
#   롤 지면의 문법은 넷이다.
#     ① 큰 면적은 깨끗한 평칠   ② 주 동선은 정돈된 돌 포장
#     ③ 명도 대비는 크게, 채도는 정돈   ④ 디테일은 가장자리·경계에 몰아 준다
#   그래서 배정을 통째로 뒤집었다.
#     주 동선(K_PATH: 스폰 진입·중앙 대로·남안 동서길·남북길·보스 어귀) = **판석 파빙**
#     여울목(K_FORD)                                                  = **젖은 판석**
#     넓은 초원(K_OPEN)                                               = **깨끗한 풀**
#     흙(tile_dirt)  = 캠프 반경(요괴 무리)·보스 마당·둔덕·포장 가장자리 닳은 띠 **만**
#
# ★슬롯 사정: 채널은 넷뿐이고 파일 이름 배정은 web/level.js 에 박혀 있다(이 작업의
#   소유가 아니다). 그래서 B 채널의 **내용물**을 젖은 자갈에서 판석 파빙으로 갈았다
#   (tools/bake_fx_tex.py 의 bake_tile_paved -> tile_stone.png). 여울목·폐허·바위
#   발치가 전부 B 라 세계관도 맞는다: 무너진 산사 터에 남은 박석.
#
# 해상도를 512 -> 1024 로 올렸다. 96m / 1024 = 9.4cm 다. 포장과 풀이 갈리는 선이
# 굵으면 "정돈된 길"이 아니라 "번진 얼룩"이 된다. 경계가 그림의 주역이 됐으니
# 경계를 그릴 해상도가 필요하다(용량은 스팀 설치형이라 제약 없음).
#
# ★칸 종류(K)에서 나온다. 즉 **바닥색을 정한 그 표와 같은 데서 나온다.**
#   따로 칠하면 언젠가 색과 결이 어긋나서 "밝은데 돌바닥"같은 게 나온다.
SPLAT_RES = 1024
TMP_SPLAT = os.path.join(ROOT, "web", "tex", "ground_splat_tmp.png")
OUT_SPLAT = os.path.join(ROOT, "web", "tex", "ground_splat.png")

# 칸 종류 -> (풀, 흙, 판석, 마른풀). 합이 1 일 필요는 없다(마지막에 정규화한다)
SPLAT_MIX = {
    K_OPEN:  (0.88, 0.02, 0.01, 0.09),   # 봄 초원. ★거의 순수한 풀 = 큰 면적의 평칠
    K_PATH:  (0.03, 0.09, 0.85, 0.03),   # ★주 동선. 판석 파빙
    K_BOSS:  (0.04, 0.70, 0.18, 0.08),   # 짓밟힌 마당. 흙 + 깨진 포장이 드러난다
    K_FORD:  (0.02, 0.05, 0.91, 0.02),   # 여울목. 젖은 판석 (제일 순수하게)
    K_BUSH:  (0.91, 0.02, 0.01, 0.06),   # 수풀 바닥
    K_THICK: (0.93, 0.02, 0.01, 0.04),   # 막는 초목
    K_ROCK:  (0.05, 0.13, 0.78, 0.04),   # 바위 발치. 깨진 박석으로 읽힌다(바닥색이 어둡다)
    K_LOW:   (0.07, 0.15, 0.74, 0.04),   # 너덜지대
    K_MOUND: (0.08, 0.84, 0.04, 0.04),   # 둔덕 흙
    K_WATER: (0.05, 0.13, 0.80, 0.02),   # 개울 바닥(물 메시가 덮어서 거의 안 보인다)
}

spl = np.zeros((RES, RES, 4), np.float32)
for _k, _mix in SPLAT_MIX.items():
    spl[K == _k] = _mix


def _disc(cx, cz, rad, feather=1.2):
    """게임 좌표 원 마스크. 2048 격자에서 0..1 로 돌려준다"""
    _dx = gxs[None, :] - cx
    _dz = gzs[:, None] - cz
    return np.clip((rad - np.sqrt(_dx * _dx + _dz * _dz)) / max(feather, 1e-3), 0.0, 1.0)


def _capsule(x0, z0, x1, z1, rad, feather=0.9):
    """두 점을 잇는 띠 마스크(선분에서의 거리). 샛길을 그리는 데 쓴다"""
    _ax, _az = x1 - x0, z1 - z0
    _L2 = max(_ax * _ax + _az * _az, 1e-6)
    _px = gxs[None, :] - x0
    _pz = gzs[:, None] - z0
    _t = np.clip((_px * _ax + _pz * _az) / _L2, 0.0, 1.0)
    _qx = _px - _t * _ax
    _qz = _pz - _t * _az
    return np.clip((rad - np.sqrt(_qx * _qx + _qz * _qz)) / max(feather, 1e-3), 0.0, 1.0)


# ── ① 초원의 되풀이 깨기 ────────────────────────────────────
# 초원을 풀 타일 한 장으로 덮으면 그 주기(2.1m)가 그대로 격자로 읽힌다. 주기가 다른
# 마른 풀(2.4m)을 섞어 두 주기가 겹치게 만든다.
# ★v90. 얼룩을 **크고 옅게** 바꿨다. 예전(17칸 = 5.6m, 세기 0.54)은 초원이 두 색
#   얼룩으로 읽혀서 "한 덩이의 깨끗한 면"이 안 나왔다. 9칸 = 10.7m 짜리 완만한
#   흐름이면 되풀이는 그대로 깨면서 면은 하나로 읽힌다.
_sw = noise(9, 771, blur=44)
_dry = np.clip((_sw - 0.47) * 2.2, 0.0, 1.0)
_green = np.isin(K, (K_OPEN, K_BUSH, K_THICK))
spl[..., 3] += np.where(_green, _dry * 0.32, 0.0)
spl[..., 0] -= np.where(_green, _dry * 0.24, 0.0)

# ── ② 캠프 반경 = 흙 ────────────────────────────────────────
# ★"흙은 캠프 반경과 샛길만." 요괴 무리가 진 치고 있는 자리는 풀이 밟혀 죽는다.
#   무리 반경이 2.6m 이고 어그로가 7.0m 이므로 4.2m 원이 "저기 뭔가 있다"의 크기다.
#   ★포장(주 동선) 위에는 안 올린다. 길을 도로 흙으로 덮으면 이번 작업이 무의미해진다.
_walk_soft = np.isin(K, (K_OPEN, K_BUSH, K_BOSS)).astype(np.float32)
_camp = np.zeros((RES, RES), np.float32)
for (_mc, _mr) in MOB_CELLS:
    _camp = np.maximum(_camp, _disc(gx_of(_mc), gz_of(_mr), 4.2, 1.8))
_camp *= _walk_soft
spl[..., 1] += _camp * 0.72
spl[..., 0] -= _camp * 0.58

# ── ③ 샛길 = 흙 ─────────────────────────────────────────────
# 캠프에서 제일 가까운 주 동선 칸까지 이어지는 1.1m 짜리 닳은 띠.
# ★이게 "샛길"의 정체다. 사람이 다니면 생기는 desire path 를 캠프마다 하나씩 놓는다.
#   주 동선(포장)은 정돈돼 있고 거기서 갈라진 흙 자국이 캠프로 이어지는 그림이 된다.
_PATH_CELLS = [(c, r) for r in range(GRID) for c in range(GRID) if grid[r][c] == PATH]
_trail = np.zeros((RES, RES), np.float32)
for (_mc, _mr) in MOB_CELLS:
    _mx, _mz = gx_of(_mc), gz_of(_mr)
    _best = min(_PATH_CELLS, key=lambda cr: (gx_of(cr[0]) - _mx) ** 2 + (gz_of(cr[1]) - _mz) ** 2)
    _trail = np.maximum(_trail, _capsule(_mx, _mz, gx_of(_best[0]), gz_of(_best[1]), 1.1, 1.0))
_trail *= _walk_soft
spl[..., 1] += _trail * 0.62
spl[..., 0] -= _trail * 0.50

# ── ④ 디테일은 경계에 ───────────────────────────────────────
# 포장 **안쪽** 가장자리는 밟혀 줄눈이 흙으로 메워진다(닳은 띠). 포장 **바깥**에는
# 마른 풀이 선다. 두 겹이 길의 윤곽을 또렷하게 만든다 = 롤 문법 ④.
_pav = np.isin(K, (K_PATH, K_FORD)).astype(np.float32)
_pin = np.clip(_pav - box_blur(_pav, 14), 0.0, 1.0) * 2.2      # 안쪽 0.65m 띠
spl[..., 1] += _pin * 0.38
spl[..., 2] -= _pin * 0.30
_fr = np.clip(box_blur(_pav, 20) - _pav, 0.0, 1.0) * 1.8       # 바깥 0.94m 띠
_fr *= np.isin(K, (K_OPEN, K_BUSH)).astype(np.float32)
spl[..., 3] += _fr * 0.40
spl[..., 0] -= _fr * 0.30

# ── ⑤ ★v94. 스폰 자리의 밟힌 흙 ─────────────────────────────
# 15절에서 주황 에어브러시를 걷어내고 탁한 흙색 얼룩으로 바꿨다. 색만 바꾸면
# 여전히 "덧칠"이라 여기서 **결**도 같이 준다. 흙 타일이 깔리면 그 자리가
# 밟혀서 풀이 죽은 땅으로 읽힌다(캠프 반경과 같은 문법이다).
_sp_dirt = np.zeros((RES, RES), np.float32)
for (_c, _r) in SPAWN_CELLS:
    _sp_dirt = np.maximum(_sp_dirt, _disc(gx_of(_c), gz_of(_r), 3.6, 2.4))
_sp_dirt *= _walk_soft
spl[..., 1] += _sp_dirt * 0.46
spl[..., 0] -= _sp_dirt * 0.38

# ── ⑥ ★v94. 초원 매크로 변주 (흙 자국·마른 풀 무리) ─────────
# 심사 지적 "지면 국소대비 부재" 는 붓 대역(타일)에서 고쳤다. 남는 절반이 **매크로**다.
# 롤 잔디를 크롭해 보면 잔디 안에 지름 1~4m 짜리 흙 자국과 마른 풀 무리가 흩어져
# 있어서, 같은 면 안에서도 밝기가 계속 바뀐다. v90 은 그 반대로("큰 면적은 깨끗한
# 평칠") 얼룩을 통째로 눌렀는데, 그건 **얼룩이 두 색으로 나뉘어 위장무늬가 될 때**
# 맞는 처방이었다. 여기서는 색을 안 바꾸고 **결만** 바꾼다(같은 초록 안에서 흙과
# 마른 풀의 비율이 자리마다 달라진다) — 위장무늬가 안 생기는 이유가 그것이다.
# ★주 동선(포장)과 여울목에는 안 올린다. 길이 도로 흙탕이 되면 v90 작업이 무의미해진다.
_open_only = np.isin(K, (K_OPEN, K_BUSH)).astype(np.float32)
_gf2 = np.random.default_rng(20260811)
_n_scuff = 0
for _ in range(260):
    _cx = float(_gf2.uniform(-HALF, HALF))
    _cz = float(_gf2.uniform(-HALF, HALF))
    _rr3 = float(_gf2.uniform(0.7, 2.4))
    _m3 = _disc(_cx, _cz, _rr3, feather=_rr3 * 0.9) * _open_only
    if _m3.max() < 0.2:
        continue
    if _gf2.random() < 0.45:                   # 흙이 드러난 자국
        spl[..., 1] += _m3 * float(_gf2.uniform(0.18, 0.42))
        spl[..., 0] -= _m3 * float(_gf2.uniform(0.14, 0.34))
    else:                                       # 마른 풀 무리
        spl[..., 3] += _m3 * float(_gf2.uniform(0.22, 0.50))
        spl[..., 0] -= _m3 * float(_gf2.uniform(0.16, 0.38))
    _n_scuff += 1
print("[스플랫] 초원 매크로 변주 %d개 (흙 자국·마른 풀 무리 0.7~2.4m)" % _n_scuff)

spl = np.clip(spl, 0.0, 1.0)
# 칸 경계를 흐린다. ★v90 에서 9 -> 6 (0.42m -> 0.28m). 포장과 풀이 갈리는 선이
#   그림의 주역이 됐으니 덜 번지게 한다. 베이스컬러와 **같은 K** 에서 나오므로
#   색과 결이 어긋날 수는 없다(어긋나는 건 반지름이 아니라 출처다).
for _c in range(4):
    spl[..., _c] = box_blur(spl[..., _c], 6)
# 2048 -> 512. 4x4 평균이라 정보가 고르게 줄어든다(단순 샘플링은 계단이 진다)
_f = RES // SPLAT_RES
spl = spl.reshape(SPLAT_RES, _f, SPLAT_RES, _f, 4).mean(axis=(1, 3))
spl /= np.maximum(spl.sum(axis=2, keepdims=True), 1e-4)

# ── ★★v96. 물칸에서는 결을 통째로 끈다 ──────────────────────
# 오너 판정 "강바닥이 지면 텍스처 + 파란 필터로 읽힌다" 의 **기계적 원인이 여기**였다.
# 스플랫이 물칸에도 판석 파빙을 배정하고 있어서, 개울 바닥에 자로 잰 듯한
# 박석 무늬가 그대로 깔렸다(근접 컷 renders/history/v96_wave10/terrain/water/
# W_w2_block.png 에서 물 속의 박석 셀이 또렷하게 보인다).
#
# ★네 채널을 "0 으로 만든다"로는 안 된다 — 게임 셰이더가 합으로 나눠 정규화하므로
#   비율만 남고 세기는 사라진다. 그래서 **합 자체를 세기로 쓴다.**
#     여기: 물칸에서 네 채널을 통째로 0.06 배로 줄인다(비율은 그대로)
#     게임(web/level.js): 정규화 **전** 합을 읽어 uTileAmt 에 곱한다
#   합이 1 인 기존 자리는 한 톨도 안 바뀐다(계약 호환).
_wsplat = (K == K_WATER).astype(np.float32)
_wsplat = box_blur(_wsplat, 10)          # 물가에서 부드럽게 꺼진다(0.47m)
_wsplat = _wsplat.reshape(SPLAT_RES, _f, SPLAT_RES, _f).mean(axis=(1, 3))
_strength = 1.0 - 0.94 * np.clip(_wsplat, 0, 1)
spl *= _strength[:, :, None]
print("[스플랫] 물칸 결 끄기: 세기 최저 %.3f (물칸 %.1f%% 면적)"
      % (float(_strength.min()), float((_wsplat > 0.5).mean() * 100)))
splat8 = np.uint8(np.clip(spl, 0, 1) * 255 + 0.5)


def _write_png_rgba(path, arr):
    """RGBA uint8 배열을 PNG 로 직접 쓴다.

    ★블렌더 이미지로 굽지 않는다. 스플랫맵의 알파는 투명도가 아니라 **네 번째
      가중치**인데, 블렌더 이미지는 알파를 투명도로 다뤄서(알파 모드·색공간 변환)
      값이 조용히 곱해지거나 감마가 걸릴 여지가 있다. 여기서는 바이트를 그대로
      박는 게 제일 안전하다. 읽는 쪽(web/level.js)도 sRGB 가 아니라 데이터로 받는다.
    ★행 순서: 배열 0행 = gz +48(남쪽) 이다. 그대로 PNG 첫 줄에 넣고,
      게임에서 flipY=false 로 읽어 v = (48 - z) / 96 으로 맞춘다.
    """
    h, w = arr.shape[:2]
    raw = b"".join(b"\x00" + arr[y].tobytes() for y in range(h))

    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xffffffff))

    blob = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(blob)
    return path


_write_png_rgba(TMP_SPLAT, splat8)
print("[스플랫] %dx%d RGBA -> %s  %.0f KB  (평균 풀 %.2f 흙 %.2f 돌 %.2f 마른풀 %.2f)"
      % (SPLAT_RES, SPLAT_RES, TMP_SPLAT, os.path.getsize(TMP_SPLAT) / 1024.0,
         spl[..., 0].mean(), spl[..., 1].mean(), spl[..., 2].mean(), spl[..., 3].mean()))

# ── 자기 검증: 아는 자리의 결이 실제로 그 결인가 ─────────────
# ★해상도를 줄이고 흐리는 과정에서 좌표가 밀리면 여울목에 풀이 깔린다. 그러면
#   "건널 수 있는 창백한 띠"라는 신호가 통째로 죽는다. 알려진 칸 네 곳을 되찾아 본다.
_CH = ("풀", "흙", "판석", "마른풀")


def splat_at(gx, gz):
    """게임 좌표 -> 스플랫 가중치. 게임 셰이더가 읽는 것과 같은 식으로 되짚는다"""
    u = (gx + HALF) / SIZE
    v = (HALF - gz) / SIZE
    j = int(np.clip(u * SPLAT_RES, 0, SPLAT_RES - 1))
    i = int(np.clip(v * SPLAT_RES, 0, SPLAT_RES - 1))
    return spl[i, j]


# ★v90. 검사 항목을 넷 -> 열로 늘렸다. 이 표가 곧 "구역 가독"의 증명이다.
#   좌표가 밀렸는지(flipY·행 순서)뿐 아니라 **의도한 배정대로 깔렸는지**를 잰다.
#   주 동선이 판석이 아니면 이번 작업이 통째로 실패한 것이므로 여기서 소리를 지른다.
_splat_bad = 0
_SPLAT_CHECK = (
    ("여울목", (FORD_COLS[0], stream_row(FORD_COLS[0])), (2,)),      # 젖은 박석 -> 판석
    ("여울접근", (14, 12), (2,)),                                    # 여울목 남쪽 접근로
    ("중앙대로", (14, 20), (2,)),                                    # ★주 동선
    # ★칸을 고를 때 수풀(BUSH_CELLS)을 피해야 한다. 수풀 칸은 길 위에 있어도
    #   K_BUSH 라 풀이 우세하다. (8,13) 로 잡았다가 한 번 틀렸다(서쪽 여울목 남안 수풀).
    ("동서길", (11, 13), (2,)),                                      # ★개울 남안 대로
    ("서남북길", (2, 22), (2,)),                                     # ★서쪽 남북 길
    ("보스어귀", (7, 5), (2,)),                                      # ★보스 서쪽 어귀
    ("스폰1진입", (4, 27), (2,)),                                    # ★스폰 진입로
    ("보스마당", BOSS_CELL, (1,)),                                    # 짓밟힌 흙 -> 흙
    # ★캠프는 초원에 있는 무리로 잰다. MOB_6 은 서쪽 길 **위**라 흙을 안 올린다
    #   (포장을 도로 흙으로 덮지 않는다는 규칙). MOB_8(남서 초원)이 규칙대로인 자리다
    ("캠프8", (8.0, 26.5), (1,)),                                    # ★요괴 캠프 반경 -> 흙
    ("외곽절벽", (0, 0), (2,)),                                       # 바위 -> 판석(깨진 박석)
    ("초원서", (9, 21), (0,)),                                       # ★넓은 초원 -> 깨끗한 풀
    ("초원동", (20, 25), (0,)),                                      # ★넓은 초원 -> 깨끗한 풀
    # ★v94. 흙(1)이 기대값에 들어왔다. 스폰 표식을 주황 에어브러시에서 "밟힌 흙"
    #   으로 바꾸면서 그 자리에 흙 결을 올렸기 때문이다(스플랫 ⑤).
    ("스폰1", SPAWN_CELLS[0], (0, 3, 2, 1)),   # 진입로 곁이라 풀·마른풀·판석·흙 다 정상
)
for _nm, (_c, _r), _want in _SPLAT_CHECK:
    _w = splat_at(gx_of(_c), gz_of(_r))
    _top = int(np.argmax(_w))
    _ok = _top in _want
    if not _ok:
        _splat_bad += 1
    print("[스플랫검증] %-8s 칸(%s,%s) 우세=%-4s [%s]  %s"
          % (_nm, _c, _r, _CH[_top], " ".join("%.2f" % x for x in _w),
             "OK" if _ok else "★어긋남"))
if _splat_bad:
    print("[경고] 스플랫 배정이 어긋났다. SPLAT_MIX / flipY / 행 순서를 다시 봐라 (%d건)"
          % _splat_bad)
else:
    print("[스플랫검증] %d 자리 전부 기대한 결이다" % len(_SPLAT_CHECK))

# ── 구역 가독 수치. 걸을 수 있는 곳이 실제로 어떤 결로 덮였는가 ──
# ★"주 동선은 포장, 넓은 면은 풀, 흙은 캠프·샛길만" 이 숫자로 확인되어야 한다.
# ★spl 은 이미 SPLAT_RES 로 줄어 있고 K 는 아직 RES 다. 칸 마스크도 같은 배수로
#   줄여서 곱해야 한다(모양이 안 맞으면 여기서 조용히 터진다. 실제로 한 번 터졌다).
_ZONE = (("주 동선(K_PATH)", K == K_PATH),
         ("여울목(K_FORD)", K == K_FORD),
         ("초원(K_OPEN)", K == K_OPEN),
         ("보스마당(K_BOSS)", K == K_BOSS))
print("[결 배정] %-16s %6s %6s %6s %6s   (면적 %%)" % ("구역", "풀", "흙", "판석", "마른풀"))
for _zn, _zm in _ZONE:
    _zf = _zm.astype(np.float32).reshape(SPLAT_RES, _f, SPLAT_RES, _f).mean(axis=(1, 3))
    _tot = max(float(_zf.sum()), 1e-6)
    _mix = [float((spl[..., _c] * _zf).sum() / _tot) for _c in range(4)]
    _s = max(sum(_mix), 1e-6)
    print("[결 배정] %-16s %5.1f%% %5.1f%% %5.1f%% %5.1f%%   (맵의 %.1f%%)"
          % (_zn, _mix[0] / _s * 100, _mix[1] / _s * 100, _mix[2] / _s * 100,
             _mix[3] / _s * 100, float(_zf.mean()) * 100))
_all = spl.reshape(-1, 4).mean(0)
_all = _all / max(_all.sum(), 1e-6) * 100
print("[결 배정] 맵 전체        %5.1f%% %5.1f%% %5.1f%% %5.1f%%"
      % (_all[0], _all[1], _all[2], _all[3]))
print("[결 배정] ★v89 실측(옛 512 스플랫)은 풀 28.2% 흙 24.3% 돌 27.3% 마른풀 20.1% 였다."
      "  흙이 주 동선을 통째로 덮어 '흙탕'으로 읽혔다")

mat_floor = bpy.data.materials.new("MAT_FLOOR")
mat_floor.use_nodes = True
_nt = mat_floor.node_tree
for n in list(_nt.nodes):
    _nt.nodes.remove(n)
_out = _nt.nodes.new("ShaderNodeOutputMaterial")
_bsdf = _nt.nodes.new("ShaderNodeBsdfPrincipled")
_bsdf.inputs["Roughness"].default_value = 0.95
_bsdf.inputs["Metallic"].default_value = 0.0
_tex = _nt.nodes.new("ShaderNodeTexImage")
_tex.image = img
_nt.links.new(_tex.outputs["Color"], _bsdf.inputs["Base Color"])
_nt.links.new(_bsdf.outputs[0], _out.inputs[0])

buf_floor = Buf("FLOOR", mat_floor)
FN = 16
for i in range(FN + 1):
    for j in range(FN + 1):
        buf_floor.v.append((-HALF + SIZE * i / FN, -HALF + SIZE * j / FN, FLOOR_Y))
for i in range(FN):
    for j in range(FN):
        a = i * (FN + 1) + j
        buf_floor.f.append((a, a + FN + 1, a + FN + 2, a + 1))


def floor_uv(co, poly=None):
    return ((co[0] + HALF) / SIZE, (co[1] + HALF) / SIZE)


# ─────────────────────────────────────────────────────────────
# 16) 메시 생성
# ─────────────────────────────────────────────────────────────
sc = bpy.context.scene


def make_obj(buf, uvfn=None):
    if not buf.f:
        return None
    me = bpy.data.meshes.new(buf.name)
    me.from_pydata(buf.v, [], buf.f)
    me.validate(verbose=False)
    # ★삼중평면 UV(rock_uv)가 면 법선을 본다. update() 를 먼저 돌려야 poly.normal 이 산다
    me.update()
    # ★v94. 정점당 UV(buf.uv)가 있으면 그게 이긴다. uvfn 은 좌표에서 UV 를 만드는
    #   방식이라 "이 정점만 v=0.3" 같은 값을 실을 수가 없다(같은 좌표면 같은 값).
    if buf.uv or uvfn:
        uvl = me.uv_layers.new(name="UVMap")
        arr = []
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                if buf.uv:
                    u, v = buf.uv[vi] if vi < len(buf.uv) else (0.0, 0.0)
                else:
                    u, v = uvfn(me.vertices[vi].co, poly)
                arr += [u, v]
        try:
            uvl.data.foreach_set("uv", arr)
        except Exception:
            uvl.uv.foreach_set("vector", arr)
    if buf.c:
        # ★v86. 정점당 명암 곱수 -> glTF COLOR_0.
        #   FLOAT_COLOR 는 블렌더에서 **선형**이라 익스포터가 감마를 안 건다
        #   (BYTE_COLOR 로 넣으면 sRGB 로 보고 변환해서 값이 달라진다. 실측 확인).
        #   내보내기 옵션은 export_vertex_color="ACTIVE" 여야 한 벌만 나간다
        #   (기본값 "MATERIAL" 은 COLOR_0 과 COLOR_1 을 둘 다 실어 보낸다).
        col = me.color_attributes.new(name="Shade", type="FLOAT_COLOR",
                                      domain="POINT")
        vals = []
        for i in range(len(me.vertices)):
            s = buf.c[i] if i < len(buf.c) else 1.0
            vals += [s, s, s, 1.0]
        col.data.foreach_set("color", vals)
        # ★"활성"이 두 종류다. 편집용(active)과 **렌더용(default)**. 익스포터가 보는 건
        #   렌더용이라 둘 다 못 박는다. 이름 프로퍼티는 버전마다 달라서 hasattr 로 건다.
        for _at in ("active_color_name", "default_color_name"):
            if hasattr(me.color_attributes, _at):
                setattr(me.color_attributes, _at, col.name)
        # ★재질 곱수를 되올릴 때 쓴 상수(RIDGE_SHADE_MEAN 등)가 실제와 맞는지
        #   여기서 **면적 가중**으로 다시 잰다. 눈이 아니라 숫자로 남는다.
        _ta, _tv = 0.0, 0.0
        for p in me.polygons:
            _s = sum(buf.c[vi] if vi < len(buf.c) else 1.0
                     for vi in p.vertices) / len(p.vertices)
            _ta += p.area
            _tv += p.area * _s
        buf.shade_mean = _tv / max(1e-9, _ta)
    me.materials.append(buf.mat)
    for p in me.polygons:
        p.use_smooth = False       # 로우폴리는 각진 게 맞다. 캐릭터 톤과도 붙는다
    me.update()
    ob = bpy.data.objects.new(buf.name, me)
    sc.collection.objects.link(ob)
    return ob


ALL_BUFS = [buf_floor, buf_rock, buf_cliff, buf_earth, buf_leaf, buf_bark,
            buf_canopy, buf_moss, buf_stone, buf_water,
            buf_exit, buf_reed, buf_skirt, buf_skirtrock,
            buf_skirtwood, buf_cord] + BUSH_OBJS
# 돌결 타일을 쓰는 버퍼. 여기만 삼중평면 UV 를 찍는다
# ★v89. buf_rock(바위 언덕·너덜·소품이 굽는 돌덩이)이 여기 들어왔다. UV 를 안 찍으면
#   재질만 바꿔 봐야 타일이 (0,0) 한 점만 물어서 단색으로 나온다.
# ★v96-B. buf_stone(COL_RUIN)이 여기 들어왔다 — **10차의 미완이었다.**
#   10차가 폐허 석재에 돌결 타일을 입혔는데(M_STONE_PALE = mat_rock) UV 를 안 찍어서,
#   glb 실측 결과 COL_RUIN 에 TEXCOORD_0 이 아예 없었다. 그러면 타일의 (0,0) 텍셀
#   한 점만 물어서 결이 없는 단색 판이 되고, 게다가 화면 평균색이 "타일 평균"이 아니라
#   "그 한 점"이 되어 [색규칙] 줄이 참말을 해도 화면은 목표색에서 벗어난다.
#   (v89 주석이 buf_rock 에서 똑같이 경고해 둔 함정을 한 번 더 밟은 것이다.)
ROCK_BUFS = (buf_cliff, buf_skirt, buf_skirtrock, buf_rock, buf_earth, buf_stone)
# ★v96-B. 버퍼 -> UV 함수. 예전에는 삼중평면이 한 배율뿐이라 "ROCK_BUFS 인가"만
#   물으면 됐는데, 수피(1.20m)·이끼(0.85m)가 각자 배율을 갖게 되면서 표가 됐다.
#   ★여기 빠뜨리면 그 재질은 타일의 (0,0) 한 텍셀만 물어 **단색 판**으로 나온다
#     (v89 에 buf_rock 에서 실제로 겪은 함정이다).
#   ★갈대(buf_reed)는 표에 없다. 정점당 UV(buf.uv)를 직접 싣고 오고,
#     make_obj 에서 그쪽이 이긴다.
UV_OF = {b: rock_uv for b in ROCK_BUFS}
UV_OF[buf_floor] = floor_uv
UV_OF[buf_bark] = bark_uv
UV_OF[buf_moss] = moss_uv

tri_total = 0
for b in ALL_BUFS:
    ob = make_obj(b, UV_OF.get(b))
    if ob:
        n = b.tri_count()
        tri_total += n
        # ★v94. 상수와 실측이 어긋나면 여기서 소리를 지른다. 예전엔 사람이 로그를
        #   보고 손으로 옮겨 적어야 했고, 잊으면 색 규칙이 조용히 밀렸다.
        _want = {"COL_CLIFF": RIDGE_SHADE_MEAN, "DECO_SKIRT": SKIRT_SHADE_MEAN}.get(b.name)
        if _want is not None and b.shade_mean is not None \
                and abs(b.shade_mean - _want) > 0.004:
            print("[경고] %s 정점색 면적평균 %.3f 인데 상수는 %.3f 다. "
                  "상수를 %.3f 로 고쳐라(안 고치면 재질 곱수가 어긋나 색 규칙이 밀린다)"
                  % (b.name, b.shade_mean, _want, b.shade_mean))
        if not b.name.startswith("BUSH_") or b.name.endswith("01"):
            print("  %-16s 삼각형 %6d  정점 %6d%s"
                  % (b.name, n, len(b.v),
                     "" if b.shade_mean is None
                     else "  정점색 면적평균 %.3f" % b.shade_mean))
tri_bush = sum(b.tri_count() for b in BUSH_OBJS)
print("  %-16s 삼각형 %6d  (16구역 합계)" % ("BUSH_01..16", tri_bush))
# v94. 30000 -> 40000. 이 예산은 웹 프로토타입 시절 값이다. 지금은 설치형(스팀)이
#   확정이라 오너가 "용량·폴리곤 예산 제약 없음"을 못박았고, 실제 씬 삼각형은
#   소품 인스턴스가 240만이다. 맵 메시 3만은 그 1.3% 다. 스커트 마디를 잘게 쪼개
#   "매끈한 회색 판" 을 깨는 값으로는 싸다. 폭주 감지용으로만 남긴다.
print("[삼각형] 합계 %d (예산 40000)" % tri_total)
if tri_total > 40000:
    print("[경고] 삼각형 예산 초과. WALL_PROP_PER_CELL 을 낮춰라")


# ─────────────────────────────────────────────────────────────
# 17) 빈 오브젝트(게임이 읽는 지점)
# ─────────────────────────────────────────────────────────────
def add_empty(name, gx, gz, y=0.0, size=1.4):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = size
    e.location = bpos(gx, gz, y)
    sc.collection.objects.link(e)
    return e


SPAWNS_JSON, MOBS_JSON, EXITS_JSON = [], [], []
for i, (c, r) in enumerate(SPAWN_CELLS):
    gx, gz = gx_of(c), gz_of(r)
    add_empty("SPAWN_%d" % (i + 1), gx, gz)
    SPAWNS_JSON.append({"id": "SPAWN_%d" % (i + 1),
                        "x": round(gx, 3), "y": 0.0, "z": round(gz, 3),
                        "yaw": round(yaw_to_center(gx, gz), 4)})
for i, (c, r) in enumerate(MOB_CELLS):
    gx, gz = gx_of(c), gz_of(r)
    add_empty("MOB_%d" % (i + 1), gx, gz)
    MOBS_JSON.append({"id": "MOB_%d" % (i + 1),
                      "x": round(gx, 3), "y": 0.0, "z": round(gz, 3),
                      "radius": 2.4})
for i, (c, r) in enumerate(EXIT_CELLS):
    gx, gz = gx_of(c), gz_of(r)
    add_empty("EXIT_%d" % (i + 1), gx, gz)
    EXITS_JSON.append({"id": "EXIT_%d" % (i + 1),
                       "x": round(gx, 3), "y": 0.0, "z": round(gz, 3),
                       "radius": 2.6})
bgx_e, bgz_e = BOSS_X, BOSS_Z
add_empty("BOSS", bgx_e, bgz_e, size=2.6)


# ─────────────────────────────────────────────────────────────
# 18) 텍스처 축소 + glTF 내보내기
# ─────────────────────────────────────────────────────────────
TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))
w, h = img.size
if TEX_SIZE and max(w, h) > TEX_SIZE:
    k = TEX_SIZE / float(max(w, h))
    img.scale(max(1, int(w * k)), max(1, int(h * k)))
    print("[텍스처] %dx%d -> %s" % (w, h, img.size[:]))

bpy.ops.object.select_all(action="SELECT")
# ★export_vertex_color="ACTIVE": 절벽·스커트의 단 차이 음영(COLOR_0)을 내보내는 열쇠다.
#   기본값 "MATERIAL" 은 색 속성이 있으면 COLOR_0 과 COLOR_1 을 **둘 다** 싣는다
#   (실측 확인). 정점색이 없는 메시(FLOOR 등)에는 아무것도 안 붙으므로 안전하다.
#   ★FLOOR 에는 절대 색 속성을 만들지 마라. web/level.js 가 그 재질의 셰이더를
#     직접 기워서 스플랫을 얹는데, 거기에 COLOR_0 이 끼면 결과를 예측할 수 없다.
bpy.ops.export_scene.gltf(
    filepath=TMP_GLB, export_format="GLB", use_selection=False,
    export_animations=False, export_yup=True,
    export_apply=True, export_vertex_color="ACTIVE",
    export_image_format="JPEG", export_image_quality=TEX_QUALITY,
    export_jpeg_quality=TEX_QUALITY)
sz = os.path.getsize(TMP_GLB)
print("[내보내기] %s  %.2f MB (아직 임시 파일)" % (TMP_GLB, sz / 1024 / 1024))
if sz > 5 * 1024 * 1024:
    print("[경고] glb 예산 5MB 초과")


# ─────────────────────────────────────────────────────────────
# 19) level1.json
# ─────────────────────────────────────────────────────────────
PROP_SUMMARY = {}
for name, k in PROP_KINDS.items():
    spec = ("없음" if k["col"] is None else
            ("circle r=%.2f" % k["col"][1] if k["col"][0] == "circle"
             else "box %.2f x %.2f" % (k["col"][1], k["col"][2])))
    PROP_SUMMARY[name] = {"count": k["n"], "blocking": k["ncol"],
                          "collider": spec, "tag": k["tag"], "desc": k["desc"]}
    if name in EXTERNAL_KINDS:
        PROP_SUMMARY[name]["mesh"] = "web/props/%s.glb (외부. props[] 로 배치)" % name

PROPS_JSON = emit_props_json()

data = {
    "name": "level1",
    "title": "탑 1층 - 무너진 산사 터를 삼킨 봄 초원",
    "generatedBy": "blender/s20_level1.py",
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
    "wallHeight": WALL_H,
    "spawns": SPAWNS_JSON,
    "mobs": MOBS_JSON,
    "boss": {
        "id": "BOSS",
        "x": round(bgx_e, 3), "y": 0.0, "z": round(bgz_e, 3),
        "arena": {"x": round(bx_c, 3), "z": round(bz_c, 3),
                  "hx": round(bhx, 3), "hz": round(bhz, 3)},
    },
    "exits": EXITS_JSON,
    "bushes": BUSH_JSON,
    "colliders": COLLIDERS,
    "colliderNote": (
        "박스는 축정렬(회전 없음)이라 2D AABB 로 바로 검사하면 된다. circle 은 원기둥. "
        "glb 안에서 COL_ 로 시작하는 메시가 막는 지형이고(나뭇가지처럼 밑을 지나가야 "
        "하는 건 CANOPY_/DECO_ 로 빼 놨다), BUSH_ 메시는 충돌하지 않는다"
        "(들어가서 숨는 곳이다). DECO_SKIRT* 는 맵 밖 배경이라 "
        "bounds 밖에 있다(경계 바깥 26m 까지 뻗는 비탈과 그 위의 숲이다. "
        "고정 카메라가 경계 너머를 볼 때 회색 공백 대신 이게 보인다). "
        "★v86: DECO_HAZE1/2/3(절벽 위 흰 봉우리 42개)는 폐기했다. 배후 스커트가 "
        "생긴 뒤로는 회색 비탈 위에 붙은 흰 종잇조각으로만 보였다. "
        "★v89: DECO_ALTAR(보스 자리의 두 겹 8각 제단)도 폐기했다. 높이 0.26m 짜리 "
        "지면 위 낮은 단이었는데, 정다각형 + 접지 그늘 없음 + 맵에 없는 색이라 "
        "'마당 상공에 떠 있는 어두운 판'으로 읽혔다(3차 QA #6). 그 자리는 "
        "바닥 얼룩(마른 피)으로만 남는다. platforms[] 의 altar 두 줄도 같이 빠졌다. "
        "DECO_CORD 는 보스 어귀 선돌에 감은 붉은 끈(방향 단서)이라 안 막는다. "
        "DECO_REED 는 개울 기슭 갈대라 안 막고 숨을 수도 없다. "
        "tag: wall=막는 자연 지형(바위 절벽·덤불·둔덕), "
        "boulderfield=너덜지대(h 1.45. 몸은 못 지나가는데 캐릭터 키 1.75 보다 낮아 "
        "건너편이 보인다), stream=개울(h 0.30. 같은 이유로 시야는 통한다), "
        "rampart=외곽 절벽, building=바위 언덕, rock=큰 바위, tree=나무 줄기, "
        "log=쓰러진 거목, gatepost=선돌, lantern=무너진 석등, pillar=부러진 석주, "
        "pagoda=석탑(13m 랜드마크). "
        "★h 는 게임이 안 본다(2D 검사). 다만 '이걸 넘어 볼 수 있는가'의 기록이라 "
        "1.75 를 기준으로 읽으면 된다."
    ),
    # ★v86 키 추가. 절벽·스커트·수면 메시의 재질 계약을 적어 둔다.
    #   web/level.js 는 FLOOR 만 손대면 되고 아래 메시들은 glb 그대로 쓰면 된다.
    "meshLookNote": (
        "★v89. COL_ROCK / COL_CLIFF / DECO_SKIRT / DECO_SKIRTROCK 네 메시가 glb 안의 "
        "**돌결 타일 한 장**(512, 한 장 3.2m, 삼중평면 UV)을 같이 물고 있다. "
        "재질의 baseColorFactor 가 '목표색 / 타일평균 / 정점색평균' 이라 화면 "
        "평균색이 정확히 팔레트 색이 된다"
        "(바위 #8a9199 · 절벽 #6e7883 · 스커트 #76858f · 스커트바위 #5d6a75). "
        "★COL_ROCK 이 v89 에서 합류했다. 3차 QA #5 '큰 바위 재질 분열'(s20 이 굽는 "
        "바위는 무텍스처 회색 판인데 옆의 Meshy 바위는 이끼 낀 돌결)을 없애려고 "
        "절벽과 같은 재질 언어로 통일했다. 색은 한 톨도 안 움직였다. "
        "★폐허 석재(COL_RUIN #cfd3cd)만 타일을 못 쓴다. 곱수가 1.83 이라 "
        "baseColorFactor 상한을 넘긴다(타일보다 밝은 색이라 곱셈으로 못 만든다). "
        "COL_CLIFF / DECO_SKIRT / WATER_STREAM 에는 COLOR_0(정점색)이 실려 있고 "
        "**회색 곱수 하나**다: 절벽은 단 차이 음영(3단, 단마다 아랫도리를 누른다), "
        "스커트는 경계에서 멀어질수록 밝아지는 다섯 줄, 수면은 가장자리를 죽여 "
        "흙 위에 얹힌 판때기로 안 보이게 하는 페더. "
        "★이 메시들의 재질을 게임 쪽에서 갈아끼우면 그 계약이 통째로 깨진다. "
        "지면 결(splatmap)은 FLOOR 재질에만 얹는다."
    ),
    "splatmap": "./tex/ground_splat.png",
    "splatmapNote": (
        "지면 타일 스플랫맵(1024x1024 RGBA). 색이 아니라 **가중치**다. "
        "R=풀(tex/tile_grass.png) G=흙(tile_dirt) "
        "B=판석 파빙(tile_stone.png ★v90 부터 내용물이 젖은 자갈이 아니라 판석이다) "
        "A=마른풀(tile_dry). "
        "web/level.js 가 FLOOR 재질에 '최종색 = 베이스컬러 x 섞은타일/타일평균' 으로 "
        "합성한다. 타일은 평균이 1 인 곱수라 구역 밝기가 안 바뀌고 결만 생긴다"
        "(= '밝고 따뜻하면 걸을 수 있다' 색 규칙이 스플랫 때문에 깨질 수 없다). "
        "★v90 배정: 주 동선(K_PATH: 스폰 진입·중앙 대로·남안 동서길·남북길·보스 어귀)과 "
        "여울목은 판석 파빙, 넓은 초원은 거의 순수한 풀, 흙은 요괴 캠프 반경(4.2m)과 "
        "캠프에서 길로 이어지는 샛길(1.1m 띠)·보스 마당·둔덕·포장 가장자리 닳은 띠에만 "
        "깔린다. 이유는 '롤 지면 문법'이다: 큰 면적은 깨끗한 평칠, 주 동선은 정돈된 포장, "
        "디테일은 경계에 몰기. "
        "★sRGB 로 읽으면 안 된다. 데이터 텍스처다(NoColorSpace). "
        "★행 순서: 첫 줄이 z=+48(남쪽)이다. flipY=false 로 읽고 "
        "u=(x+48)/96, v=(48-z)/96 으로 찍는다. "
        "가중치는 이 파일의 grid[] 와 같은 칸 종류표에서 나온다(blender/s20_level1.py "
        "SPLAT_MIX). 바닥색과 결이 같은 데서 나오므로 어긋날 수가 없다."
    ),
    "platforms": PLATFORMS,
    "platformNote": (
        "올라설 수 있는 낮은 단. 무릎(0.6m)보다 낮아 colliders[] 에는 안 들어가지만, "
        "발이 묻히지 않으려면 그 위에 섰을 때 지면 높이를 top 으로 올려야 한다. "
        "top 은 floorY 를 포함한 절대 높이다(평지는 floorY=0.02). "
        "겹치면 제일 높은 값이 이긴다."
    ),
    "grid": ["".join(row) for row in grid],
    "gridLegend": {"#": "막는 지형(바위·너덜·덤불·개울·외곽 절벽)",
                   "-": "흙길(바닥색만 다르다. '.' 과 똑같이 걷는다)",
                   ".": "열린 초원", "X": "보스 마당", "H": "바위 언덕"},
    "propKinds": PROP_SUMMARY,
    "propNote": (
        "소품은 blender/s20_level1.py 의 배치 테이블(PROPS)에서 나온다. "
        "종류마다 지오메트리 함수 하나가 대응되고, 콜라이더는 모양이 아니라 "
        "종류 규격(PROP_KINDS[...]['col'])에서 계산된다. 나중에 Meshy 에셋으로 "
        "갈아끼울 때 build 함수만 바꾸면 배치와 충돌은 그대로다."
    ),
    "props": PROPS_JSON,
    "propsNote": (
        "★rock·crag·thicket·tree·bush 5종은 level1.glb 에 안 들어 있다. "
        "web/props/<종류>.glb (blender/s22_props.py 가 굽는다) 를 게임이 읽어 "
        "web/props.js 가 InstancedMesh 로 심는다(종류당 드로우콜 1). "
        "여기 좌표는 three.js 기준이고 모델은 이미 '바닥 중심 원점 + scale 1.0 이 "
        "s20 규격 크기' 로 정규화돼 있어서 그대로 놓으면 된다. "
        "필드: kind / x / z / rotY(라디안, Y축) / scale(가로세로 공통) / "
        "sy(세로만 추가로 곱하는 배율) / bush(수풀은 속한 구역 메시 이름) / "
        "slim(초원에 선 나무). "
        "★수풀은 InstancedMesh 가 아니라 bush 값이 같은 것끼리 하나로 합쳐 "
        "BUSH_01..16 이름의 메시로 심어야 한다. web/stealth.js 가 그 이름으로 메시를 "
        "찾아 '내가 들어간 수풀만' 투명도를 낮추기 때문이다(InstancedMesh 는 "
        "인스턴스별 투명도가 안 된다). "
        "콜라이더는 이 배치와 무관하게 colliders[] 에 이미 다 들어 있다."
    ),
}
with open(TMP_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

# ── 원자적 교체 ──────────────────────────────────────────────
# ★둘 다 다 구워진 뒤에 한 번에 갈아끼운다. 순서가 어긋나면 새 json 과 옛 glb 가
#   짝이 안 맞는 한순간이 생긴다. rename 은 같은 파일시스템에서 원자적이다.
os.replace(TMP_GLB, OUT_GLB)
os.replace(TMP_JSON, OUT_JSON)
# ★스플랫맵도 같이 갈아끼운다. 얘만 먼저 바뀌어 있으면 새 결 위에 옛 콜라이더가
#   얹힌 한순간이 생긴다(맵을 다시 굽는 도중 브라우저가 새로고침하면 실제로 본다).
os.replace(TMP_SPLAT, OUT_SPLAT)
print("[JSON] %s  %d bytes  (충돌 %d개 / 낮은단 %d개)"
      % (OUT_JSON, os.path.getsize(OUT_JSON), len(COLLIDERS), len(PLATFORMS)))
print("[교체] level1_tmp.* -> level1.*  ·  ground_splat_tmp.png -> ground_splat.png  (원자적)")
print("DONE")
