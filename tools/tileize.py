# -*- coding: utf-8 -*-
"""Meshy(나노바나나) 손그림 바닥 원자재 4장을 게임용 지면 타일로 후처리한다.

    incoming/ground_tiles/grass.png     -> tile_grass  (스플랫 R)
    incoming/ground_tiles/dirt.png      -> tile_dirt   (스플랫 G)
    incoming/ground_tiles/paving.jpg    -> tile_stone  (스플랫 B)
    incoming/ground_tiles/drygrass.jpg  -> tile_dry    (스플랫 A)

실행:
    python3 tools/tileize.py                      # 넷 다 굽고 검증 이미지까지
    python3 tools/tileize.py --only=tile_grass    # 한 장만
    python3 tools/tileize.py --out=web/tex/_ab_v91/meshy_built   # 다른 자리에 굽기

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
왜 원본을 그대로 못 쓰는가 — 세 가지가 계약을 깬다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
web/level.js 의 지면 셰이더는 이 네 장을 **색이 아니라 곱수**로 쓴다.

    곱수 = clamp( mix( 1, 타일색 / 타일평균색, TILE_AMT=1.9 ), 0.28, 2.05 )
    최종색 = 베이스컬러(2048 구역색) x 곱수

그래서 원본을 그냥 넣으면 이렇게 된다(실측, 2026-08-10).

  ① **이음매.** 상하 이음매가 안쪽 이웃 대비 +44~187% 로 튄다. 좌우는 대체로
     멀쩡한데 상하만 나쁘다(나노바나나가 가로 되풀이만 신경 쓴 결과로 보인다).
     1.6~2.4m 마다 되풀이되므로 화면에 가로줄이 격자로 깔린다.

  ② **곱수가 안전망을 뚫는다.** 원본 대비가 커서 비율이 0.00~2.65 다. 게임이
     TILE_AMT 1.9 로 폭을 늘리면 화소의 0.6~13.7% 가 클램프 0.28~2.05 밖으로
     나간다. 잘리는 순간 그 자리만 "곱수 평균 1" 계약이 깨져서 검은 구멍이 된다.
     (판석 줄눈·풀 그늘이 통째로 시커메진다.)

  ③ **자글거림.** 오너 최우선 판정이 "자글자글 금지"다. 게임 거리(75px/m)로 줄인
     뒤 남는 이웃 대비가 원본은 1.50~4.61% 다. 절차 v2 는 0.20~1.10% 였다.
     ①②를 고쳐도 이건 안 없어진다. 잔결의 **주파수 분포**가 다르기 때문이다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
공정 4단 (순서가 중요하다)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1) 이어붙임화   periodic-plus-smooth 분해 (+ 필요하면 좁은 거울 페더)
  2) 자글 규격    3대역 분해 후 **잔결 대역만** 눌러 절차 v2 의 끓음 수치 안으로
  3) 곱수 맞춤    평균색·비율 표준편차를 절차 v2 와 같은 값으로 (클램프 밖 0%)
  4) 검증         이음매 / 곱수 / 자글 을 숫자로 재고 2x2 이어붙임 시트를 굽는다

★2 를 3 보다 먼저 하는 이유: 3 이 비율 폭을 목표값으로 **정규화**하므로, 2 에서
  대역을 누르면 그만큼 다른 대역이 부풀어 총 대비는 그대로 유지된다. 즉 2 는
  "전체를 흐리게" 가 아니라 "**어느 주파수에 대비를 쓸지**" 를 고르는 단계가 된다.
  순서를 바꾸면 누른 만큼 전체가 밋밋해져서 그냥 흐린 그림이 된다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
결과 (2026-08-10 · renders/history/v91_tiles/)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                이음매(가로/세로)      클램프 밖    끓음(화면%)      절차 v2
  tile_grass    +12/+134% -> -38/-16%   0.0000%     3.52 -> 1.27%     0.20%
  tile_dirt     +52/+187% -> -50/-44%   0.0000%     1.50 -> 0.46%     0.25%
  tile_stone     -1/ +46% -> -57/-44%   0.0000%     4.61 -> 2.61%     1.10%
  tile_dry      +52/+227% -> -25/-21%   0.0000%     2.29 -> 1.31%     0.22%

  · 이음매·클램프는 **전 장 합격**이다(기준 +10% 이내 / 0%).
  · 끓음은 넷 다 절차 v2 를 못 넘겼다. 위 UNREACH_SLACK 주석이 그 이유이고,
    바닥까지 눌러도 못 닿는다는 걸 대역별 곡선으로 확인한 뒤 내린 결론이다.
  · ★그런데 **화면에서는 그 차이가 텍스처에서만큼 안 난다.** 같은 카메라·같은
    프레이밍으로 두 판을 찍어(9컷, 밝기 차 +0.72% = 공정) 지면 화소의 이웃 대비를
    직접 재 보니 절차 1.22% / 이 판 1.67% = **x1.37** 이었다. 텍스처에서 재면
    x6 인데 화면에서 x1.37 인 이유는, 화면의 지면 대비는 조명·그림자·2048
    베이스컬러·안개가 함께 만들고 타일은 그 중 한 몫일 뿐이기 때문이다.
    (renders/history/v91_tiles/inrender.json)
  · 그 x1.37 을 주고 산 것: 게임 거리에서 초원이 **위장무늬 얼룩**에서 **풀**이 되고,
    주 동선이 **퍼즐 조각**에서 **판석 길**이 된다(AB_*.png).

★해 봤지만 못 쓴 것: "카메라를 1/3픽셀씩 밀어 프레임 변화를 재는" 크롤링 직접
  측정. 게임이 살아 돌아서(요괴 이동·소품) 지면 아닌 자리가 더 크게 변했다
  (초원에서 비지면 12.1% > 지면 4.5%). 장면을 얼릴 수 있어야 성립하는데 그
  창구(__freeze)가 ?dev 에만 있다. 나중에 하려면 dev 모드로 얼리고 재라.
"""
import os
import sys
import json
import importlib.util

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "incoming", "ground_tiles")
TEX_DIR = os.path.join(ROOT, "web", "tex")
OUT_DIR = os.path.join(ROOT, "renders", "history", "v91_tiles")
# ★v96-B. 소품 타일(수피·이끼·갈대)은 web/tex 에 두지 않는다. 이 셋은 브라우저가
#   받는 물건이 아니라 **blender 가 읽어 glb 안에 굽는** 재료다. web/ 밑에 두면
#   tools/build_deploy.py 가 web/ 를 통째로 훑어 복사하므로 배포본에 죽은 1MB 가 실린다.
PROP_TEX_DIR = os.path.join(ROOT, "blender", "tex")


def src_path(rel):
    """SPEC 의 src. '/' 가 들어 있으면 incoming/ 아래 상대경로로 본다.

    ★v96-B 에서 원자재가 두 벌이 됐다(ground_tiles = 91차 · tiles_v2 = 10차B).
      옛 SPEC 이 파일 이름만 적고 있었으므로, 이름만 있으면 옛 자리로 보낸다."""
    return os.path.join(ROOT, "incoming", rel) if "/" in rel \
        else os.path.join(SRC_DIR, rel)

# 절차 타일을 굽는 스크립트에서 계약 상수와 검증 함수를 그대로 빌려 쓴다.
# ★값을 여기 베껴 적지 않는다. 베끼면 저쪽을 고칠 때 이쪽이 조용히 어긋난다.
_spec = importlib.util.spec_from_file_location(
    "bake_fx_tex", os.path.join(ROOT, "tools", "bake_fx_tex.py"))
BFT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BFT)

TILE_PERIOD = BFT.TILE_PERIOD        # 타일 한 판이 몇 m 인가 (web/level.js 와 같은 값)
GAME_PX_PER_M = BFT.GAME_PX_PER_M    # 고정 쿼터뷰의 실측 배율 = 75
MIN_FEAT_M = BFT.MIN_FEAT_M          # 규칙 A. 최소 특징 크기 0.25m
TILE_S = BFT.TILE_S                  # 1024

# web/level.js 의 계약값. 검증이 "늘린 곱수가 클램프에 닿는가"를 재려면 필요하다
TILE_AMT, TILE_MIN, TILE_MAX = 2.05, 0.24, 2.10   # ★web/level.js 와 같은 값이어야 한다

# ─────────────────────────────────────────────────────────────────────────────
# 장별 규격 — 전부 **절차 v2 실측값**이다 (renders/history/v91_tiles/table.json)
# ─────────────────────────────────────────────────────────────────────────────
# ref   평균색. 게임이 png 에서 직접 재서 나누므로 화면 결과에는 영향이 없다.
#       그런데도 절차판 값에 맞추는 이유는 둘이다.
#         · 어두운 채널을 안 만든다. 원본 grass 는 평균 R 이 0.283 이라 그 채널만
#           8비트 한 칸이 비율 1.4% 다(= 계단). 0.44 로 올리면 0.9% 가 된다
#         · 절차판과 **같은 자리에서** A/B 를 하게 된다(밝기 차로 이기지 않는다)
# std   비율의 표준편차 = 곱수의 세기. 절차 v2 와 같은 값을 쓴다. 이걸 맞춰야
#       "무늬만 다르고 대비는 같은" 정직한 A/B 가 된다
# hue   칠한 색 계단을 밝기 대비 얼마나 남길지. 구역색은 2048 베이스컬러가 정하므로
#       타일이 색까지 세게 밀면 구역 가독이 죽는다
# floor 비율의 하한(하드 클립). 판석 줄눈처럼 한 값으로 평칠된 아주 어두운 자리가
#       TILE_AMT 로 늘어나 클램프를 뚫는 걸 막는다
# boil  게임 거리 끓음의 **상한**. 절차 v2 가 낸 값이다. 여기 안으로 들어가야 한다
# hfr   25cm 미만 잔결비의 상한. 같은 출처
# lowcut/midboost  ★v94 신설. 대역 재배치 이득(위 MID_HI 주석의 근거).
#       저역(>25cm)을 lowcut 배로 깎고 붓맛(2.6~8cm)을 midboost 배로 올린다.
#       판석만 값이 얌전한 이유: 판석의 붓맛 대역은 **줄눈**이라 이미 세다
#       (v93 실측 끓음 2.61% = 넷 중 최고). 더 올리면 줄눈이 검은 격자로 탄다.
# ★★v96-B. 풀·판석 두 장을 10차B 원자재(incoming/tiles_v2/)로 갈았다.
#   왜 갈았나 — 10차 지형이 남긴 신고 두 개다.
#     ① 풀이 **융단**으로 읽힌다. v94 원자재(grass.png)는 붓결이 한 방향으로 도는
#        소용돌이라, 대역 재배치로 국소대비를 살려 놔도 "포기"가 안 생긴다.
#        새 원자재는 뾰족 클럼프 + 흙 틈이라 0.10~0.25m 대역에 30.8% 가 들어 있다
#        (옛 판 39.2% 인데 그게 전부 소용돌이 결이었다).
#     ② 판석이 **잔균열 유약**이다. paving.jpg 는 손바닥만 한 파빙이고 게다가
#        period 가 1.28m 이라 화면에서 조각 하나가 30cm 였다. 레퍼런스(롤)의 길은
#        **사람 어깨폭 판돌**이다. slab.jpg + period 2.75m 로 조각 하나가 90cm 가 된다.
#   ★색은 갈리지 않는다. _fit_ratio 가 평균을 ref 로 못 박고 색편차만 hue 배로
#     남기므로, 원자재가 청록으로 치우쳐 있어도(grass_spiky 는 hue 130~170 이 86%)
#     화면 팔레트는 v96 그대로다. 실제로 옛 판과 **같은 ref** 를 쓴다 = 정직한 A/B.
SPEC = {
    # ★lowcut 0.30 -> 0.26. 새 원자재는 0.5m 짜리 격자(나노바나나가 클럼프를 격자로
    #   찍었다. 게임 거리 미리보기에서 사선 격자가 보였다)를 저역에 갖고 있다.
    #   저역을 더 깎으면 그 격자가 같이 죽는다.
    # ★midboost 3.0 -> 1.45. 옛 판은 붓맛 대역에 에너지가 2% 밖에 없어 3배가 필요했다.
    #   새 판은 2~4cm 12.6% · 4~10cm 17.2% 라 이미 차 있다. 3배로 올리면 클럼프
    #   가장자리가 톱니로 튄다(그리고 _fit_ratio 가 폭을 정규화하므로 클럼프 자체가 죽는다).
    # ★warp: 원자재의 포기가 바둑판으로 앉아 있다(첫 굽기 화면 자기상관 0.450 /
    #   주기 0.83m / 기준 0.35 / 레퍼런스 0.304). delattice 주석 참조.
    # ═════════════════════════════════════════════════════════════════════════
    # ★★v97(11차). 오너: **"너무 패턴 느낌이라 별로야, 화장실 타일 같잖아."**
    #   자로 정체를 특정했다(renders/history/v97_wave11/ground/w11g_probe.py).
    #     · 자기상관은 이미 0.118 로 규격 안이었다 → **이 신고는 자기상관이 못 잡는다**
    #     · 진짜 값은 **중앙값 국소대비(p50_range5)** 다.
    #         레퍼런스 잔디 5.7~10.7  ↔  우리 화면 25~27  (**3.5배 시끄럽다**)
    #     · 그리고 v96-B 판 tile_grass 는 에너지의 **66.4% 가 10~25cm 한 대역**에
    #       몰려 있었다. 크기가 하나뿐인 밝은 C 자 붓자국이 2.10m 마다 되돌아오니,
    #       상관값이 낮아도 사람 눈은 "같은 무늬가 돈다"고 읽는다. 그게 화장실 타일이다.
    #   → 문법을 바꾼다. **잔디는 표식이 없는 조용한 면**이 되고, 표식은
    #     비반복 메달리온 데칼(web/tex/ground_medallion.png)이 준다. 레퍼런스
    #     (refpack/lol_ground_owner_ref2.png)의 구성이 정확히 그것이다.
    # ★원자재 codex grass_soft 는 접힘이 없다(자기상관 0.096). 그래서 warp_m=0 이다.
    #   delattice 를 걸면 이음매만 나빠진다(실측 -93% -> -35%).
    # ★lowcut 0.26 -> 0.50. 이 원자재는 에너지의 59% 가 25cm 이상(큰 얼룩)이고
    #   그 큰 얼룩이 곧 되풀이다. 다만 0.80 까지 깎으면 자기상관이 0.348 로 **거꾸로
    #   올라간다**(남은 대역이 상대적으로 더 주기적이 된다). 0.50 이 실측 바닥이다.
    # ★std 0.138 -> 0.085. 게임 거리 실측 p50_range5 18.3 -> 13.8,
    #   p99_range5 59.3 -> 33.1(레퍼런스 27~35), 자기상관 0.168 -> 0.220.
    "tile_grass": dict(src="codex_ground/grass_soft.png", ref=(0.4401, 0.5493, 0.3606),
                       std=0.085, hue=0.45, floor=None, boil=0.00200, hfr=0.331,
                       lowcut=0.50, midboost=1.30,
                       warp_m=0.0, warp_lo_m=1.10, warp_hi_m=2.40),
    # ★★v97. 흙 = **길**이 됐다. period 1.32 -> 2.55.
    #   v90 이 주 동선을 판석(B 채널)으로 깔았는데, 2.75m 판돌이 6.4m 폭 직선 복도를
    #   따라 줄줄이 반복되면서 화면에서 **황토색 다각형 격자**가 됐다(= 오너가 본
    #   "화장실 타일" 의 절반). 스플랫에서 주 동선의 판석 가중치 72% 를 이 채널로
    #   옮긴다(tools/ground_splat_remix.py). 그래서 이 타일이 곧 길의 얼굴이다.
    #   codex path_organic 은 흙이 지배하고 판석 **조각**이 불규칙하게 박혀 있어
    #   "열 맞춘 판석" 인상이 안 생긴다.
    # ★period 는 조각 크기가 정한다. 1024px 이 2.55m 면 조각 하나가 12~18cm 다.
    #   ★네 주기가 서로 안 나누어떨어져야 한다는 규칙은 그대로: 2.10 / 2.55 / 2.75 / 2.40.
    #   ★tools/bake_fx_tex.py TILE_PERIOD · web/level.js TILES[].period 와 **한 쌍**이다.
    # ★std 0.128 -> 0.075. 게임 거리 p50_range5 26.8 -> 15.4(레퍼런스 길 12.0).
    "tile_dirt":  dict(src="codex_ground/path_organic.png",
                       ref=(0.5795, 0.5111, 0.4200),
                       std=0.075, hue=0.45, floor=None, boil=0.00251, hfr=0.335,
                       lowcut=0.60, midboost=1.00),
    # ★lowcut 0.60 -> 1.00 (안 깎는다). 판돌 자체가 저역이다. 여기를 깎으면
    #   "큰 판돌"이라는 교체 목적이 그대로 사라진다(옛 파빙은 조각이 30cm 라
    #   저역이 곧 되풀이 얼룩이었고, 그래서 깎는 게 이득이었다. 전제가 바뀌었다).
    # ★midboost 1.7 -> 1.15. 붓맛 대역의 정체가 줄눈이라 세게 올리면 검은 격자로 탄다
    #   (v94 주석에 적힌 것과 같은 이유. 값만 더 보수적으로 잡는다).
    # ★floor 0.70 -> None. span_guard(v94)가 꼬리를 tanh 로 접어 클램프 밖 0% 를
    #   보장하므로 하드 클립이 필요 없다. 클립을 두면 줄눈 속이 한 값으로 뭉친다.
    "tile_stone": dict(src="tiles_v2/slab.jpg", ref=(0.6044, 0.6100, 0.5799),
                       std=0.150, hue=0.45, floor=None, boil=0.01105, hfr=0.861,
                       lowcut=1.00, midboost=1.15),
    # ★floor 0.66 이 없으면 마른 풀 줄기 사이의 깊은 그늘이 늘어난 곱수 0.166 이 되어
    #   클램프 0.28 을 뚫는다(화소의 0.039%). 적어 보여도 그 자리는 평균 1 계약이
    #   깨진 검은 점이라 초원 위에 후추를 뿌린 것처럼 보인다
    "tile_dry":   dict(src="drygrass.jpg", ref=(0.6053, 0.5498, 0.3792),
                       std=0.130, hue=0.45, floor=0.66, boil=0.00217, hfr=0.342,
                       lowcut=0.32, midboost=2.8),
}
TILE_SET = ("tile_grass", "tile_dirt", "tile_stone", "tile_dry")

# 자글 규격에 못 미쳐도 여기까지만 누른다. 이 아래로 내리면 붓맛이 죽는다.
# ★"규격 안으로" 와 "질감이 뭉개지지 않는 선" 이 부딪히면 **후자가 이긴다.**
#   규격은 절차판이 낸 값이고, 절차판은 게임 거리에서 위장무늬로 읽혔다
#   (renders/history/v91_tiles/02_gamedist_3way.png 아래 줄). 규격을 맞추자고
#   손그림을 같은 위장무늬로 만들면 A/B 를 할 이유가 없어진다.
MID_FLOOR = 0.34      # (v94 부터 안 쓴다. 아래 재배치 주석 참조)
FINE_MIN = 0.12       # 2.6cm 미만(순수 지글거림)은 여기까지 눌러도 그림이 안 상한다
ALIAS_M = 0.026       # 잔결/지글 경계(m). 게임 거리에서 약 2px = 진짜 앨리어싱 시작점

# ═════════════════════════════════════════════════════════════════════════════
# ★v94 — 대역 재배치. 건틀릿 1회차 지형 FAIL(12/50) 의 근본 대응
# ═════════════════════════════════════════════════════════════════════════════
# 심사관 판정: "잔디 1:1 국소대비 p99 = 5, 롤은 52. 붓자국 한 종류가 반복될 뿐
# 명암 폭이 거의 0." 원인을 주파수로 뜯어 보니 v93 풀 타일의 밝기 에너지가
#
#     >50cm 28.0% │ 25~50cm 11.7% │ 10~25cm 39.2% │ 4~10cm 19.6%
#     2~4cm 1.0%  │ <2cm 0.5%
#
# 였다. 화면 1 디바이스픽셀 = 0.67cm(150px/m, DPR2) 이므로 **국소대비로 보이는
# 대역(1.3~8cm = 2~12px)에 에너지가 2% 밖에 없었다.** 위 regrain 이 그 대역을
# 규격(끓음)에 맞추려고 MID_FLOOR 까지 눌러 온 결과다. 자를 잘못 들고 있었다.
#
# ★그런데 대비를 **키울 수는 없다.** 게임의 계약이 비율 폭을 묶어 놓는다.
#     늘린곱수 = 1 + (비율-1) x TILE_AMT(1.9)  ∈ [0.28, 2.05]
#   -> 비율이 [0.621, 1.553] 밖으로 나가는 순간 잘리고, 잘리면 그 자리만
#      "곱수 평균 1" 이 깨져서 검은 점이 된다. v93 은 이미 0.659~1.514 로
#      허용 폭을 거의 다 쓰고 있었다.
#
# 그래서 **키우지 않고 옮긴다.** 저역(>25cm)을 깎아 그 에너지를 붓맛 대역으로
# 넘긴다. 총 대비는 그대로인데 눈에 보이는 자리로 옮겨 앉는다.
#   · 실측(tools/ground_sim.py, 셰이더를 그대로 계산): 초원 p99range5 41.3 -> 60.3,
#     p99hp 6.4 -> 13.4. 클램프 밖 0.000% 유지. (롤 잔디 실측 51.4 / 14.4)
#   · 덤: 저역은 한 판(1.6~2.4m)에 큰 얼룩 몇 개라 **그게 곧 되풀이 무늬**였다.
#     깎으면 타일 티도 같이 준다.
#   · 앨리어싱은 안 늘어난다. 올리는 대역의 아래 끝이 ALIAS_M(2.6cm = 3.9 디바이스px)
#     이고 나이퀴스트는 1.33cm 다. 그 아래(<2.6cm)는 그대로 FINE_MIN 으로 눌러 둔다.
MID_HI = 0.080        # 붓맛 대역 위 끝(m). 8cm = 화면 12px
LOW_M = 0.25          # 저역 경계(m). MIN_FEAT_M 과 같은 자리다


# ★규격에 못 미치는 장을 어떻게 할 것인가 — 실측이 정한 규칙.
#   대역별 끓음 곡선을 다 훑어 봤다(renders/history/v91_tiles/table.json 의 curve).
#   결론이 셋이다.
#     ① fine(2.6cm 미만)을 죽이는 건 **공짜다.** 게임 거리에서 2px 도 안 되는 것이라
#        눈에 보이는 그림이 안 바뀌는데 끓음은 grass 1.70->1.33%, dry 2.35->1.38%
#        내려간다. 그래서 이건 무조건 한다
#     ② mid 를 누르는 건 **비싸고 잘 안 듣는다.** grass 는 mid 를 0 까지 내려도
#        0.69% 라 규격 0.20% 에 못 닿는다. 판석은 mid 를 0 으로 해도 2.6% 그대로다
#        (끓음의 정체가 줄눈이고, 줄눈이 곧 그림이라 누르면 판석이 아니게 된다)
#     ③ 게다가 3단계가 비율 폭을 규격값으로 **정규화**하므로, 한 대역을 누르면 남은
#        대역이 그만큼 부푼다. 그래서 무작정 누르면 손해만 보고 끓음은 그대로다
#   그래서 규격에 못 닿는 장은 **바닥까지 누르지 않는다.** 바닥값(MID_FLOOR)에서
#   나오는 끓음을 '이 장이 낼 수 있는 최선' 으로 보고, 그 값의 UNREACH_SLACK 안에
#   드는 **가장 덜 누른** mid 를 고른다. 못 딸 상을 쫓느라 붓맛을 태우지 않는다.
UNREACH_SLACK = 1.20


# ═════════════════════════════════════════════════════════════
# 0) 감아 도는(=타일이므로 양끝이 이어진) 흐림
# ═════════════════════════════════════════════════════════════
def wrap_blur(a, k, passes=2):
    """감아 도는 박스 흐림을 여러 번. 박스 두 번이면 삼각 커널이라 링잉이 훨씬 적다.

    ★일반 gaussian_filter 를 쓰면 안 된다. 가장자리를 반사·연장으로 채우기 때문에
      타일의 양끝이 서로를 못 본다 = 흐린 뒤 이음매가 다시 생긴다.
    """
    if k <= 1:
        return np.asarray(a, np.float32).copy()
    out = np.asarray(a, np.float32)
    if out.ndim == 2:
        out = out[..., None]
        squeeze = True
    else:
        squeeze = False
    n = out.shape[0]
    k = int(min(max(k, 1), n))
    for _ in range(passes):
        for ax in (0, 1):
            # 세 벌 이어 붙여 누적합을 내면 감아 도는 이동평균이 된다
            c = np.cumsum(np.concatenate([out, out, out], axis=ax),
                          axis=ax, dtype=np.float32)
            sl, sl2 = [slice(None)] * 3, [slice(None)] * 3
            sl[ax] = slice(n + k // 2, 2 * n + k // 2)
            sl2[ax] = slice(n + k // 2 - k, 2 * n + k // 2 - k)
            out = (c[tuple(sl)] - c[tuple(sl2)]) / k
    return out[..., 0] if squeeze else out


# ═════════════════════════════════════════════════════════════
# 1) 이어붙임화
# ═════════════════════════════════════════════════════════════
def periodic_component(a):
    """Moisan 의 periodic + smooth 분해에서 **periodic 쪽**만 남긴다.

    ── 왜 이 방법인가 ────────────────────────────────────────
    "이어붙임화" 라고 하면 보통 오프셋 블렌드(반 칸 밀고 가운데 십자 이음매를
    문지르기)나 거울+페더를 쓴다. 둘 다 **그림을 지운다**. 오프셋은 십자 자리의
    붓질을 뭉개고, 거울은 가장자리 띠에 좌우 대칭 유령을 남긴다. 이 원자재는
    손그림 붓맛이 유일한 장점이라 그걸 지우면 살 이유가 없다.

    Moisan 분해는 그림을 **하나도 안 지운다.** 원리는 이렇다.
      · 양끝이 안 맞는 정도를 경계에만 놓은 힘 v 로 적는다
      · 그 v 를 푸아송 방정식의 우변으로 놓고 푼 해 s 가 "양끝 불일치를 통째로
        떠안은 아주 매끄러운 면"이다 (경계 말고는 힘이 없으니 안쪽은 조화함수다)
      · p = a - s 는 정확히 주기적이고, 뺀 것은 매끄러운 면뿐이라 잔결·붓질·
        경계선은 한 톨도 안 상한다
    푸리에로 풀면 나눗셈 한 번이다(아래).

    ★s 의 평균은 0 이다(아래 s_hat[0,0]=0). 그래서 평균색이 안 밀린다.
    ★상하만 나빴어도 좌우까지 같이 푼다. 한 축만 풀면 모서리 네 점이 안 맞는다.
    """
    a = np.asarray(a, np.float32)
    h, w = a.shape[:2]
    ch = a.shape[2] if a.ndim == 3 else 1
    src = a.reshape(h, w, ch)
    out = np.empty_like(src)

    # 주파수 나눗셈의 분모. 2cos(2pi i/h) + 2cos(2pi j/w) - 4 = 이산 라플라시안
    ii = 2.0 * np.cos(2.0 * np.pi * np.arange(h, dtype=np.float64) / h)
    jj = 2.0 * np.cos(2.0 * np.pi * np.arange(w, dtype=np.float64) / w)
    den = ii[:, None] + jj[None, :] - 4.0
    den[0, 0] = 1.0                      # 0 나눗셈 방지. 아래에서 그 항을 0 으로 죽인다

    for c in range(ch):
        x = src[..., c].astype(np.float64)
        v = np.zeros_like(x)
        # 위아래 끝줄이 서로 얼마나 안 맞는가 (부호가 반대로 한 쌍)
        v[0, :] += x[-1, :] - x[0, :]
        v[-1, :] += x[0, :] - x[-1, :]
        # 좌우 끝줄
        v[:, 0] += x[:, -1] - x[:, 0]
        v[:, -1] += x[:, 0] - x[:, -1]
        s_hat = np.fft.fft2(v) / den
        s_hat[0, 0] = 0.0                # 평균 이동 금지
        s = np.real(np.fft.ifft2(s_hat))
        out[..., c] = (x - s).astype(np.float32)

    out = out if a.ndim == 3 else out[..., 0]
    return out


def mirror_feather(a, band):
    """마무리용 좁은 거울 페더. Moisan 만으로 +10% 안에 못 들어올 때만 쓴다.

    가장자리에서 거리 d 인 열은 **반대쪽 짝 열**과 섞는다. 섞는 비율이 끝에서
    정확히 반반이라 0열과 마지막열이 **같은 값**이 된다(수학적으로 이음매 0).
    ★띠가 넓으면 좌우 대칭 유령이 보인다. 그래서 band 는 아주 좁게만 준다.
    """
    a = np.asarray(a, np.float32).copy()
    h, w = a.shape[:2]
    for ax, n in ((1, w), (0, h)):
        idx = np.arange(n)
        d = np.minimum(idx, n - 1 - idx).astype(np.float32)
        t = np.clip(d / max(band, 1), 0.0, 1.0)
        wgt = 0.5 + 0.5 * (t * t * (3.0 - 2.0 * t))       # 끝 0.5 -> 띠 밖 1.0
        shape = [1, 1, 1][:a.ndim]
        shape[ax] = n
        wgt = wgt.reshape(shape)
        partner = np.flip(a, axis=ax)                      # 짝 = 반대쪽 끝
        a = a * wgt + partner * (1.0 - wgt)
    return a


def seam_score(a):
    """이음매를 '안쪽 이웃 대비 몇 %' 로 잰다. 검증 기준이 이 숫자다(+10% 이내)."""
    lum = np.asarray(a, np.float32)
    lum = lum.mean(axis=2) if lum.ndim == 3 else lum
    dcol = np.abs(np.diff(lum, axis=1)).mean()
    drow = np.abs(np.diff(lum, axis=0)).mean()
    sx = float(np.abs(lum[:, 0] - lum[:, -1]).mean())
    sy = float(np.abs(lum[0, :] - lum[-1, :]).mean())
    return {
        "seam_x": round(sx, 6), "seam_y": round(sy, 6),
        "inner_x": round(float(dcol), 6), "inner_y": round(float(drow), 6),
        "pct_x": round((sx / max(float(dcol), 1e-9) - 1.0) * 100.0, 1),
        "pct_y": round((sy / max(float(drow), 1e-9) - 1.0) * 100.0, 1),
    }


def make_tileable(rgb, name):
    """1단계. 이어붙임화. Moisan 으로 풀고, 그래도 남으면 좁은 페더로 마무리한다"""
    before = seam_score(rgb)
    out = periodic_component(rgb)
    mid = seam_score(out)
    used = "periodic"
    if max(mid["pct_x"], mid["pct_y"]) > 10.0:
        # 4px 띠. 1024 의 0.4% 라 유령이 화면에서 0.5mm 도 안 된다
        out = mirror_feather(out, 4)
        used += "+feather4"
    after = seam_score(out)
    print("   [이음매] %s  가로 %+.0f%% -> %+.0f%%   세로 %+.0f%% -> %+.0f%%   (%s)"
          % (name, before["pct_x"], after["pct_x"],
             before["pct_y"], after["pct_y"], used))
    return np.clip(out, 0.0, 1.0), {"before": before, "after": after, "method": used}


# ═════════════════════════════════════════════════════════════
# 2) 자글 규격
# ═════════════════════════════════════════════════════════════
def split_bands(rgb, period):
    """세 대역으로 가른다. 자를 자리가 **미터** 기준이라 주기마다 픽셀 수가 다르다.

      low   25cm 위     면. 손그림의 큰 붓과 얼룩. 절대 안 건드린다
      mid   2.6~25cm    붓맛. 풀잎·판석·자갈 = 이 원자재를 산 이유
      fine  2.6cm 아래  게임 거리에서 2px 도 안 되는 것. 결이 아니라 지글거림이다
    """
    s = rgb.shape[0]
    k_low = max(3, int(round(s / period * MIN_FEAT_M)))     # 25cm
    k_fine = max(3, int(round(s / period * ALIAS_M)))       # 2.6cm
    low = wrap_blur(rgb, k_low)
    fine_lp = wrap_blur(rgb, k_fine)
    return low, (fine_lp - low), (rgb - fine_lp), k_low, k_fine


def reband(rgb, name, spec):
    """★v94 신설. 저역을 깎아 붓맛 대역으로 에너지를 옮긴다(위 상수 주석 참조).

    푸리에에서 반지름(=사이클/판)을 특징 크기(m)로 환산해 대역별 이득을 건다.
    ★공간 필터(블러 뺄셈)로 하면 대역 사이가 겹쳐서 저역을 깎을 때 붓맛까지
      같이 깎인다. 여기서는 정확히 갈라야 하므로 주파수에서 한다.
    ★이어붙임 뒤에 한다. FFT 는 그림이 이미 주기적이라고 가정하는데, 이어붙임을
      안 한 그림에 걸면 경계 불연속이 링잉으로 번져 이음매가 되살아난다.
    """
    lowk = spec.get("lowcut", 1.0)
    midk = spec.get("midboost", 1.0)
    if abs(lowk - 1.0) < 1e-6 and abs(midk - 1.0) < 1e-6:
        return rgb
    per = TILE_PERIOD[name]
    s = rgb.shape[0]
    fy = np.fft.fftfreq(s)[:, None] * s
    fx = np.fft.fftfreq(s)[None, :] * s
    r = np.sqrt(fy * fy + fx * fx)
    with np.errstate(divide="ignore"):
        feat = per / np.maximum(r, 1e-9)          # 특징 크기(m)
    G = np.ones_like(r)
    G[feat > LOW_M] = lowk                        # 25cm 위 = 면. 깎는다
    G[(feat > ALIAS_M) & (feat <= MID_HI)] = midk  # 2.6~8cm = 붓맛. 올린다
    G[0, 0] = 1.0                                 # DC(평균)는 절대 안 건드린다
    out = np.empty_like(rgb)
    for c in range(3):
        ch = rgb[:, :, c]
        mu = float(ch.mean())
        out[:, :, c] = np.real(np.fft.ifft2(np.fft.fft2(ch - mu) * G)) + mu
    return np.clip(out, 0.0, 1.0)


def delattice(rgb, name, spec):
    """★v96-B 신설. **원자재가 격자로 찍혀 있을 때** 그 격자만 흐트러뜨린다.

    왜 필요한가 — 나노바나나가 그린 풀(grass_spiky)은 포기가 예쁜데 그 포기가
    **바둑판으로 앉아 있다.** 화면 실측 자기상관이 0.450(주기 0.83m)으로, 기준
    0.35 와 레퍼런스 0.304 를 둘 다 넘겼다. 눈으로도 밝은 포기가 사선 격자로 보인다.

    ★★정체는 격자가 아니라 **원자재가 속으로 2x2 로 접혀 있는 것**이었다. 자기상관
      최고점이 정확히 **반 판(79px = 타일 157px 의 절반)**에 0.898 로 선다. 즉 게임이
      2.10m 로 깔아도 사람 눈에는 1.05m 마다 같은 그림이 도는 것이다.
    ★대역으로는 못 지운다. 실측했다 — lowcut 을 0.26 -> 0.12 -> 0.05 로 내려 봐도
      자기상관이 **0.898 에서 한 톨도 안 움직인다.** 접힘은 특정 대역이 아니라
      그림 전체에 걸린 성질이라 그렇다.
    ★진폭을 크게 주면 그림이 죽는다. 0.16m(=포기 하나 크기) 로 밀었더니 자기상관은
      0.083 까지 떨어졌는데 잎이 대리석 마블링으로 녹아 버렸다(prev/warp_wl.png).
      0.06m + 긴 물결(1.1~2.4m)이면 **포기 모양은 그대로 두고 자리만** 어긋난다.
    ★그래서 지우지 말고 **자리를 흔든다.** 그림을 매끄러운 변위장으로 밀면 붓질·
      명암·색은 한 톨도 안 상하고 "같은 자리에 같은 것" 만 깨진다.
      변위장은 띠제한 잡음이라 **정확히 주기적**이다(푸리에에서 고리 하나만 남긴다)
      = 이어붙임이 안 깨진다. 샘플링도 감아 돈다.
    ★진폭이 격자 주기의 1/4 을 넘으면 잎이 엿가락처럼 늘어난다. 실측으로 고른 값이
      아래 warp_m 이고, 늘어남은 자기상관과 함께 눈으로 같이 본다.
    """
    amp_m = spec.get("warp_m", 0.0)
    if amp_m <= 0:
        return rgb
    per = TILE_PERIOD[name]
    s = rgb.shape[0]
    amp = amp_m / per * s                       # 화소 단위 진폭
    rng = np.random.default_rng(spec.get("warp_seed", 96_202_608))
    fy = np.fft.fftfreq(s)[:, None] * s
    fx = np.fft.fftfreq(s)[None, :] * s
    r = np.sqrt(fy * fy + fx * fx)
    # 변위장의 파장 = 타일/주기수. 격자보다 **성긴** 물결이어야 격자가 통째로 밀린다
    k_lo = per / spec.get("warp_hi_m", 1.30)    # 파장 위 끝
    k_hi = per / spec.get("warp_lo_m", 0.55)    # 파장 아래 끝
    ring = ((r >= k_lo) & (r <= k_hi)).astype(np.float32)
    dxy = []
    for _ in range(2):
        w = np.fft.ifft2(np.fft.fft2(rng.standard_normal((s, s))) * ring).real
        dxy.append((w / max(float(w.std()), 1e-9) * amp).astype(np.float32))
    yy, xx = np.meshgrid(np.arange(s), np.arange(s), indexing="ij")
    sy = (yy + dxy[0]) % s
    sx = (xx + dxy[1]) % s
    y0 = np.floor(sy).astype(np.int32) % s
    x0 = np.floor(sx).astype(np.int32) % s
    y1, x1 = (y0 + 1) % s, (x0 + 1) % s
    ty, tx = (sy - np.floor(sy))[..., None], (sx - np.floor(sx))[..., None]
    out = ((rgb[y0, x0] * (1 - tx) + rgb[y0, x1] * tx) * (1 - ty)
           + (rgb[y1, x0] * (1 - tx) + rgb[y1, x1] * tx) * ty)
    print("   [격자흐트림] %s 진폭 %.2fm(%.0fpx) · 물결 파장 %.2f~%.2fm"
          % (name, amp_m, amp, spec.get("warp_lo_m", 0.55),
             spec.get("warp_hi_m", 1.30)))
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def span_guard(rgb, amt=TILE_AMT, lo=TILE_MIN, hi=TILE_MAX):
    """비율 꼬리를 접어 **클램프 밖 0%** 를 보장한다.

    ★자르지 않고 접는다(tanh). 자르면 그 자리가 평평해져서 판석 줄눈처럼
      한 값으로 뭉친 자리가 통째로 같은 색이 된다. 접으면 순서는 남는다.
    ★평균은 안 지킨다 — 게임(web/level.js)이 png 에서 평균을 **직접 재서**
      나누기 때문이다. 여기서 지켜야 하는 건 폭뿐이다.
    """
    m = rgb.reshape(-1, 3).mean(0)
    ratio = rgb / np.maximum(m, 1e-4)[None, None, :]
    d = ratio - 1.0
    dl = 1.0 - (1.0 + (lo - 1.0) / amt)           # 허용 아래 폭
    dh = (1.0 + (hi - 1.0) / amt) - 1.0           # 허용 위 폭
    # 여유 3% 를 남긴다. 8비트로 저장하며 반올림이 한 칸 밀려도 안 걸리게
    dl *= 0.97
    dh *= 0.97
    d = np.where(d > 0, dh * np.tanh(d / dh), -dl * np.tanh(-d / dl))
    return np.clip((1.0 + d) * m[None, None, :], 0.0, 1.0)


def regrain(rgb, name, spec):
    """2단계. **잔결 대역만** 눌러 끓음을 규격 안으로.

    통짜 흐림이나 중앙값 필터를 안 쓴다. 둘 다 큰 면까지 같이 뭉개서 손그림이
    플라스틱이 된다. 여기서는 대역을 갈라 놓고 위쪽 두 대역의 세기만 고른다.

    누르는 순서가 정해져 있다.
      ① fine(2.6cm 미만)을 먼저 끝까지 누른다. 게임 거리에서 2px 도 안 되는 것이라
         눌러도 **눈에 보이는 그림이 안 바뀐다.** 공짜로 얻는 몫이다
      ② 그래도 규격을 넘으면 mid 를 이분법으로 낮춘다. 여기서부터는 붓맛이 준다.
         MID_FLOOR 아래로는 안 내려간다(위 상수 주석 참조)

    ★재는 값은 **3단계까지 다 끝낸 뒤의** 끓음이다. 3단계가 비율 폭을 규격값으로
      정규화하기 때문에, 여기서 mid 를 누르면 low 가 그만큼 부풀어 총 대비는
      유지된다. 그래서 "누른 뒤 다시 재기" 를 한 덩이로 묶어야 답이 맞는다.
    """
    period = TILE_PERIOD[name]
    low, mid, fine, k_low, k_fine = split_bands(rgb, period)

    def build(a_mid, a_fine):
        out = np.clip(low + mid * a_mid + fine * a_fine, 0.0, 1.0)
        return fit_ratio(out, spec)

    def boil_of(img):
        return measure_grain(img, name)["boil"]

    target = spec["boil"]

    # ★v94. **붓맛 대역을 더 이상 누르지 않는다.**
    #   v91 까지는 여기서 mid 를 이분법으로 낮춰 '끓음' 규격에 맞췄다. 그런데 그
    #   규격의 출처가 절차 v2 타일이고, 절차 v2 는 심사에서 "명암 폭 거의 0" 으로
    #   진 그림이다. 규격을 지키느라 국소대비를 통째로 갖다 버리고 있었다.
    #   지금은 대역 재배치(reband)가 그 대역을 오히려 키워 놓으므로, 여기서 도로
    #   누르면 앞 단계를 무효로 만든다.
    #   ① fine(2.6cm 미만 = 나이퀴스트 근처)만 끝까지 누른다. 이건 여전히 공짜다
    #      — 화면에서 2px 도 안 되는 것이라 그림이 안 바뀌는데 반짝임만 준다.
    #   ② mid 는 손대지 않는다. 끓음은 이제 **제어값이 아니라 보고값**이다.
    a_fine, a_mid = FINE_MIN, 1.0
    cand = build(a_mid, a_fine)
    got = boil_of(cand)
    verdict = ("끓음 %.4f%% (옛 규격 %.4f%%, %s) — v94 부터 규격은 보고용이다"
               % (got * 100, target * 100, "안" if got <= target else "초과"))

    print("   [자글] %s  잔결대역 %.2f (2.6cm 미만, 눌러 둔다) · 붓맛대역 %.2f (안 누른다)"
          "   [자른 픽셀 %d / %d]  %s"
          % (name, a_fine, a_mid, k_fine, k_low, verdict))
    return cand, {"a_fine": round(a_fine, 3), "a_mid": round(a_mid, 3),
                  "k_fine": k_fine, "k_low": k_low, "verdict": verdict}


# ═════════════════════════════════════════════════════════════
# 3) 곱수 맞춤
# ═════════════════════════════════════════════════════════════
def fit_ratio(rgb, spec):
    """3단계. 평균색·비율 폭을 규격으로. 절차 타일이 쓰는 것과 **같은 함수**다.

    ★여기서 하는 일이 곧 "레벨 보정"이다. 원자재가 어둡거나(grass 평균 R 0.28)
      채도가 튀어도(dirt 는 채도 0.63) 이 한 번으로 절차판과 같은 자리에 온다.
      게임이 png 평균을 실측해 나누므로 **구역 명도 관계**는 베이스컬러가 그대로
      쥐고 있고, 여기서는 타일 자체의 대비만 관리하면 된다.
    """
    return BFT._fit_ratio(rgb, spec["ref"], std=spec["std"],
                          hue_keep=spec["hue"], floor=spec["floor"])


# ═════════════════════════════════════════════════════════════
# 4) 검증
# ═════════════════════════════════════════════════════════════
def measure_grain(rgb_or_path, name):
    """자글거림. bake_fx_tex.measure_tile_grain 과 **같은 정의**다.

    절차판과 한 표에 놓아야 하므로 정의를 새로 만들지 않는다. 다만 저쪽은 파일
    경로만 받아서 굽는 도중에 못 쓴다. 배열도 받게 여기서 다시 적는다.
    """
    if isinstance(rgb_or_path, str):
        a = np.asarray(Image.open(rgb_or_path).convert("RGB"), np.float32) / 255.0
    else:
        a = np.asarray(rgb_or_path, np.float32)
    period = TILE_PERIOD.get(name, 2.0)
    lum = a.mean(axis=2)
    s = lum.shape[0]

    feat_px = max(1, int(round(s / period * MIN_FEAT_M)))
    hf = lum - BFT._wrap_box(lum, feat_px)
    hf_ratio = float(hf.std()) / max(float(lum.std()), 1e-6)

    gpx = max(4, int(round(period * GAME_PX_PER_M)))
    step = max(1, s // gpx)
    small = BFT._wrap_box(lum, step)[::step, ::step]
    boil = float(np.abs(np.diff(small, axis=1)).mean()
                 + np.abs(np.diff(small, axis=0)).mean()) / 2.0
    return {"hf_ratio": round(hf_ratio, 4), "boil": round(boil, 5), "game_px": gpx}


def measure_ratio(rgb):
    """곱수 계약. 늘린 뒤 클램프 밖 화소가 0% 여야 한다"""
    a = np.asarray(rgb, np.float32)
    m = a.reshape(-1, 3).mean(0)
    r = a / np.maximum(m, 1e-4)[None, None, :]
    wide = 1.0 + (r - 1.0) * TILE_AMT
    out = ((wide < TILE_MIN) | (wide > TILE_MAX)).mean() * 100.0
    return {"mean": [round(float(x), 4) for x in m],
            "rmin": round(float(r.min()), 3), "rmax": round(float(r.max()), 3),
            "rstd": round(float(r.std()), 4),
            "wmin": round(float(wide.min()), 3), "wmax": round(float(wide.max()), 3),
            "clamp_pct": round(float(out), 4)}


def _font(sz):
    for p in ("/System/Library/Fonts/AppleSDGothicNeo.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def tile_sheet(paths, out_name, title):
    """2x2 로 깔고 가운데를 잘라 낸 검증 그림. 이음매가 그림 **안쪽**으로 들어온다"""
    os.makedirs(OUT_DIR, exist_ok=True)
    names = [n for n in TILE_SET if n in paths]
    cell = 420
    sheet = Image.new("RGB", (cell * len(names), cell + 46), (18, 18, 20))
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 6), title, font=_font(17), fill=(240, 240, 230))
    for i, n in enumerate(names):
        t = Image.open(paths[n]).convert("RGB")
        big = Image.new("RGB", (t.width * 2, t.height * 2))
        for yy in range(2):
            for xx in range(2):
                big.paste(t, (xx * t.width, yy * t.height))
        # 가운데 한 판만큼 잘라내면 그 안에 십자 이음매가 정확히 들어온다
        crop = big.crop((t.width // 2, t.height // 2,
                         t.width // 2 + t.width, t.height // 2 + t.height))
        sheet.paste(crop.resize((cell, cell), Image.LANCZOS), (i * cell, 40))
        dr.text((i * cell + 8, 22), "%s  2x2 이어붙임" % n, font=_font(14),
                fill=(210, 210, 200))
    p = os.path.join(OUT_DIR, out_name)
    sheet.save(p)
    return p


def gamedist_sheet(sets, out_name, title):
    """게임 거리(75px/m)로 줄인 뒤 다시 확대. **자글거림의 재료**를 눈으로 본다"""
    os.makedirs(OUT_DIR, exist_ok=True)
    cell = 330
    rows = len(sets[0][1])
    sheet = Image.new("RGB", (cell * 4, rows * (cell + 22) + 24), (18, 18, 20))
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 5), title, font=_font(17), fill=(240, 240, 230))
    for i, (name, variants) in enumerate(sets):
        gpx = int(round(TILE_PERIOD[name] * GAME_PX_PER_M))
        for j, (lbl, path) in enumerate(variants):
            im = Image.open(path).convert("RGB")
            big = Image.new("RGB", (im.width * 2, im.height * 2))
            for y in range(2):
                for x in range(2):
                    big.paste(im, (x * im.width, y * im.height))
            small = big.resize((gpx * 2, gpx * 2), Image.BOX)   # 박스 평균 = 밉맵
            y0 = 24 + j * (cell + 22)
            sheet.paste(small.resize((cell, cell), Image.NEAREST), (i * cell, y0 + 18))
            dr.text((i * cell + 6, y0 + 2), "%s · %s (%dpx/타일)" % (name, lbl, gpx),
                    font=_font(13), fill=(200, 220, 200))
    p = os.path.join(OUT_DIR, out_name)
    sheet.save(p)
    return p


# ═════════════════════════════════════════════════════════════
# 실행
# ═════════════════════════════════════════════════════════════
def build_one(name, out_dir, spec=None, out_name=None):
    spec = spec or SPEC[name]
    out_name = out_name or name
    src = src_path(spec["src"])
    raw = np.asarray(Image.open(src).convert("RGB"), np.float32) / 255.0
    if raw.shape[0] != TILE_S or raw.shape[1] != TILE_S:
        raw = np.asarray(Image.open(src).convert("RGB")
                         .resize((TILE_S, TILE_S), Image.LANCZOS), np.float32) / 255.0
    print("── %s  <-  %s" % (name, spec["src"]))
    rec = {"src": spec["src"],
           "raw": {"grain": measure_grain(raw, name), "ratio": measure_ratio(raw),
                   "seam": seam_score(raw)}}

    tiled, seam_info = make_tileable(raw, name)
    rec["seam"] = seam_info
    # ★v96-B. 이어붙인 **뒤**, 대역 재배치 **앞**이다. 뒤에 두면 reband 가 갈라
    #   놓은 대역이 다시 섞이고, 앞에 두면 아직 안 이어진 경계가 밀려 이음매가 산다.
    tiled = delattice(tiled, name, spec)
    # ★v94. 이어붙임 -> **대역 재배치** -> 자글 -> 곱수 맞춤 -> 폭 보장 순서다.
    #   재배치를 이어붙임 뒤에 두는 이유는 reband 주석에, 폭 보장을 맨 뒤에 두는
    #   이유는 span_guard 주석에 적었다.
    banded = reband(tiled, name, spec)
    fitted, grain_info = regrain(banded, name, spec)
    fitted = span_guard(fitted)
    rec["regrain"] = grain_info

    path = os.path.join(out_dir, out_name + ".png")
    BFT.save_rgb(path, fitted)
    rec["out"] = {"grain": measure_grain(fitted, name), "ratio": measure_ratio(fitted),
                  "seam": seam_score(fitted),
                  "kb": round(os.path.getsize(path) / 1024.0, 1)}
    g, r, s = rec["out"]["grain"], rec["out"]["ratio"], rec["out"]["seam"]
    print("   [결과] 잔결비 %.3f (규격 %.3f) · 끓음 %.5f=화면 %.2f%% (규격 %.5f=%.2f%%)"
          % (g["hf_ratio"], spec["hfr"], g["boil"], g["boil"] * 100,
             spec["boil"], spec["boil"] * 100))
    print("   [계약] 평균 %.4f %.4f %.4f · 비율 %.3f~%.3f std %.4f"
          " · 늘린 곱수 %.3f~%.3f · 클램프 밖 %.4f%% (0 이어야 한다)"
          % (r["mean"][0], r["mean"][1], r["mean"][2], r["rmin"], r["rmax"],
             r["rstd"], r["wmin"], r["wmax"], r["clamp_pct"]))
    print("   [이음매] 가로 %+.1f%% · 세로 %+.1f%%  (+10%% 이내여야 한다)  %.1f KB"
          % (s["pct_x"], s["pct_y"], rec["out"]["kb"]))
    print()
    return path, rec


# ═════════════════════════════════════════════════════════════
# 5) 소품 타일 — 수피 · 이끼 · 갈대 (★v96-B 신설)
# ═════════════════════════════════════════════════════════════
# 위 넷과 **계약이 다르다.** 지면 타일은 셰이더가 평균으로 나눠 곱수로 쓰지만,
# 이 셋은 blender/s20_level1.py 의 재질이 통째로 곱한다.
#
#     최종색 = baseColorFactor(k) x 타일         k = 목표색(선형) / 타일 평균(선형)
#
# 그래서 규칙이 둘이다.
#   ★① **밝게 구워야 한다.** k 는 1 을 못 넘는다(glTF baseColorFactor 상한).
#      타일이 목표색보다 어두운 채널이 하나라도 있으면 그 색을 못 만든다.
#      원자재 그대로는 걸린다 — bark.jpg 평균 #7c5335 의 B(0x35)가 M_BARK #594b3a
#      의 B(0x3a)보다 어둡다. 그래서 평균을 밝은 중성색으로 옮긴다.
#   ★② **색은 원자재가 아니라 재질이 정한다.** _fit_ratio 가 평균을 중성 ref 로
#      못 박고 색편차만 hue 배로 남기므로, v96 팔레트(M_BARK/M_MOSS/M_REED)가
#      한 톨도 안 움직인다. s20 의 [색규칙] 줄이 그걸 매 굽기마다 잰다.
#   ★③ 지면 타일과 달리 TILE_AMT 로 폭이 늘어나지 않는다. 즉 **여기 std 가 곧
#      화면 대비**다. 지면 std(0.13~0.15)보다 크게 잡아야 결이 보인다.
#   ★④ ctr = 명암 **재분배**. _fit_ratio 가 폭(std)을 규격으로 정규화하므로,
#      앞에서 감마를 걸어도 총 대비는 안 변한다. 바뀌는 것은 "어느 쪽에 대비를
#      쓸 것인가" 다. g>1 이면 어두운 쪽이 더 깊어진다 = 수피의 갈라진 골, 이끼
#      사이의 틈이 산다. 첫 판은 이게 없어서 수피가 **비누 조각**으로 나왔다.
PROP_SPEC = {
    # 수피. 나무 줄기(COL_TRUNK) · 쓰러진 거목. 세로 결이 정체라 period 를 줄기
    # 지름(0.44m)의 두세 배로 잡아 한 줄기에 결이 서너 줄 지나가게 한다.
    "prop_bark": dict(src="tiles_v2/bark.jpg", period=1.20,
                      ref=(0.615, 0.615, 0.615), std=0.205, hue=0.34, ctr=1.55),
    # 이끼. 바위 위 이끼 돔(DECO_MOSS)의 반지름이 0.16~0.42m 다. period 0.85m 면
    # 돔 하나에 이끼 덩이가 서넛 올라간다(한 덩이만 걸리면 다시 단색 판이 된다).
    # ★hue 0.38 -> 0.14. s28 이 bank 에서 겪은 **연보라 함정**이 여기서 그대로 났다.
    #   원자재의 평균이 이끼색(초록)이라, 평균을 중성으로 옮기는 순간 이끼가 아닌
    #   돌 픽셀이 "평균보다 초록이 적은 값" = 자홍으로 뜬다. 색편차를 거의 안 남기면
    #   사라진다. 초록은 어차피 M_MOSS 가 준다.
    "prop_moss": dict(src="tiles_v2/moss.jpg", period=0.85,
                      ref=(0.615, 0.615, 0.615), std=0.175, hue=0.14, ctr=1.30),
}
# 소품 타일은 게임 거리에서 지면만큼 크게 안 깔리므로 잔결을 지면만큼 안 누른다
PROP_FINE = 0.45


def prop_contrast(rgb, g):
    """명암 재분배. 휘도에만 감마를 걸고 색은 비율로 따라가게 둔다.

    ★색까지 감마를 걸면 채도가 같이 흔들린다. 여기서 하려는 것은 "골을 깊게" 지
      "색을 진하게" 가 아니다(색은 어차피 재질이 정한다)."""
    if abs(g - 1.0) < 1e-6:
        return rgb
    a = np.asarray(rgb, np.float32)
    lum = a.mean(axis=2, keepdims=True)
    mu = float(lum.mean())
    tgt = mu * np.power(np.maximum(lum, 1e-5) / mu, g)
    return np.clip(a * (tgt / np.maximum(lum, 1e-5)), 0.0, 1.0)


def build_prop_tile(name, out_dir):
    """소품용 이어붙임 타일 한 장. 굽고, 재고, 선형 평균을 돌려준다."""
    spec = PROP_SPEC[name]
    raw = np.asarray(Image.open(src_path(spec["src"])).convert("RGB"),
                     np.float32) / 255.0
    if raw.shape[0] != TILE_S:
        raw = np.asarray(Image.open(src_path(spec["src"])).convert("RGB")
                         .resize((TILE_S, TILE_S), Image.LANCZOS), np.float32) / 255.0
    print("── %s  <-  %s" % (name, spec["src"]))
    tiled, _seam = make_tileable(raw, name)
    low, mid, fine, _kl, _kf = split_bands(tiled, spec["period"])
    out = np.clip(low + mid + fine * PROP_FINE, 0.0, 1.0)
    out = prop_contrast(out, spec.get("ctr", 1.0))
    out = BFT._fit_ratio(out, spec["ref"], std=spec["std"], hue_keep=spec["hue"])
    path = os.path.join(out_dir, name + ".png")
    BFT.save_rgb(path, out)
    return path, prop_report(name, path, out, None)


def prop_report(name, path, rgb, alpha):
    """소품 타일의 계약 보고. **선형 평균**이 핵심이다(재질 곱수가 여기서 나온다).

    ★알파가 있으면 알파 가중 평균을 낸다. 갈대 카드는 화면의 8할이 투명이라
      전체 평균을 쓰면 새까만 값이 나오고, s20 의 곱수가 1 을 훌쩍 넘는다."""
    a = np.asarray(rgb, np.float32)
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    if alpha is None:
        m_srgb = a.reshape(-1, 3).mean(0)
        m_lin = lin.reshape(-1, 3).mean(0)
        cov = 1.0
    else:
        w = np.asarray(alpha, np.float32)[:, :, None]
        s = float(w.sum()) * 1.0
        m_srgb = (a * w).reshape(-1, 3).sum(0) / max(s, 1e-6)
        m_lin = (lin * w).reshape(-1, 3).sum(0) / max(s, 1e-6)
        cov = float(np.asarray(alpha).mean())
    seam = seam_score(a)
    rec = {"file": os.path.basename(path),
           "mean_srgb": [round(float(x), 4) for x in m_srgb],
           "mean_lin": [round(float(x), 5) for x in m_lin],
           "coverage": round(cov, 4),
           "seam_pct": [seam["pct_x"], seam["pct_y"]],
           "kb": round(os.path.getsize(path) / 1024.0, 1)}
    print("   [계약] 평균 sRGB #%02x%02x%02x · **선형 %.4f %.4f %.4f** "
          "· 덮개 %.1f%% · 이음매 %+.0f/%+.0f%% · %.0f KB"
          % (int(m_srgb[0] * 255 + .5), int(m_srgb[1] * 255 + .5),
             int(m_srgb[2] * 255 + .5), m_lin[0], m_lin[1], m_lin[2],
             cov * 100, seam["pct_x"], seam["pct_y"], rec["kb"]))
    return rec


def _fit_ratio_masked(rgb, alpha, ref, std, hue_keep):
    """BFT._fit_ratio 와 같은 식인데 통계를 **덮개로 가중**해서 낸다.

    ★알파 카드에 그냥 _fit_ratio 를 걸면 안 된다. 투명한 자리(면적의 65%)가
      새까만 값으로 평균에 끼어서, 보이는 잎이 통째로 흰색으로 날아간다."""
    a = np.asarray(rgb, np.float32)
    w = np.asarray(alpha, np.float32)[:, :, None]
    sw = max(float(w.sum()), 1e-6)
    m = (a * w).reshape(-1, 3).sum(0) / sw
    d = a / np.maximum(m, 1e-4)[None, None, :] - 1.0
    db = d.mean(axis=2, keepdims=True)
    d = db + (d - db) * hue_keep
    cur = float(np.sqrt((w * d * d).sum() / (sw * 3.0)))   # 덮개 가중 표준편차
    d *= std / max(cur, 1e-6)
    ref = np.asarray(ref, np.float32)
    out = ref[None, None, :] * (1.0 + d)
    for _ in range(4):
        out = np.clip(out, 0.0, 1.0)
        c = (out * w).reshape(-1, 3).sum(0) / sw
        out = out * (ref / np.maximum(c, 1e-4))[None, None, :]
    return np.clip(out, 0.0, 1.0)


# ── 갈대 알파 카드 ────────────────────────────────────────────
# 원자재는 **검은 배경에 그린 갈대 한 포기**다(타일이 아니다). 카드 한 장으로 쓴다.
REED = dict(src="tiles_v2/reed_black.jpg", res=512,
            # 휘도 키잉 문턱. lo 아래는 완전 투명, hi 위는 완전 불투명.
            # ★lo 를 0 으로 두면 JPEG 링잉(검은 배경의 ±2/255)이 통째로 반투명
            #   먼지가 되어 카드가 네모로 보인다. 실측 배경 휘도 p99 가 0.028 이라
            #   그 위에서 끊는다.
            lo=0.035, hi=0.150,
            margin=0.03,      # 잘라낸 뒤 남기는 여백(카드 폭 대비)
            root=0.26,        # 밑동 어둡게 할 높이 비율
            root_k=0.52,      # 밑동 곱수(0.52 = 절반쯤 그늘)
            # ★위 ①② 와 같은 계약이다. 원자재가 노랑연두 일변도(선형 평균 B 0.052)라
            #   그대로 두면 k_B = M_REED 의 B / 0.052 = **1.21 > 1** 이 되어 못 만드는
            #   색이 된다. 평균을 밝은 중성으로 옮기고 색편차만 hue 배로 남긴다.
            ref=(0.60, 0.60, 0.60), std=0.200, hue=0.45)


def build_reed_card(out_dir):
    """검은 배경 원자재 -> RGBA 알파 카드.

    세 가지를 한다.
      ① **휘도 키잉.** 배경이 순검정이라 휘도가 그대로 덮개다. smoothstep 으로
         부드럽게 끊어야 잎 끝이 톱니가 안 된다.
      ② ★**언프리멀티플라이.** 이게 없으면 잎 가장자리에 검은 테두리가 남는다.
         원자재는 이미 "잎색 x 덮개 + 검정 x (1-덮개)" 로 합성된 그림이라, 색을
         덮개로 되나눠야 진짜 잎색이 나온다. 안 하면 알파 컷 뒤에도 잎이
         **가장자리만 시커먼 채로** 남아 게임에서 그을린 갈대가 된다.
      ③ **밑동 어둡게.** 카드 아래쪽을 곱수로 눌러 물가 그늘에 박힌 것처럼 만든다.
         카드는 밑이 잘린 물건이라 밑동이 밝으면 공중에 뜬 그림으로 읽힌다.
    ★알파는 감마를 안 탄다. 그래서 색만 sRGB 로 두고 알파는 선형 그대로 굽는다.
    """
    a = np.asarray(Image.open(src_path(REED["src"])).convert("RGB"),
                   np.float32) / 255.0
    lum = a.mean(axis=2)
    lo, hi = REED["lo"], REED["hi"]
    t = np.clip((lum - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    alpha = t * t * (3.0 - 2.0 * t)                       # smoothstep
    # ② 언프리멀티플라이. 덮개가 아주 작은 자리는 색이 발산하므로 하한을 둔다
    col = a / np.maximum(alpha, 0.20)[:, :, None]
    col = np.clip(col, 0.0, 1.0)
    # 잘라내기: 덮개가 있는 자리의 경계상자 + 여백
    ys, xs = np.nonzero(alpha > 0.35)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    mg = int(round(max(y1 - y0, x1 - x0) * REED["margin"]))
    y0 = max(0, y0 - mg); y1 = min(alpha.shape[0], y1 + mg)
    x0 = max(0, x0 - mg); x1 = min(alpha.shape[1], x1 + mg)
    # ★정사각으로 맞춘 뒤 자른다. 안 그러면 정사각 텍스처로 늘리면서 갈대가
    #   가로로 눌린다(실측 원자재 가로/세로 1.076). 카드는 정사각이라고 s20 이
    #   가정하므로(hw = hh x 0.52) 여기서 비를 1 로 못 박는 게 맞다.
    side = max(y1 - y0, x1 - x0)
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    y0, y1 = cy - side // 2, cy - side // 2 + side
    x0, x1 = cx - side // 2, cx - side // 2 + side
    pad = ((max(0, -y0), max(0, y1 - alpha.shape[0])),
           (max(0, -x0), max(0, x1 - alpha.shape[1])))
    if any(v for p in pad for v in p):
        col = np.pad(col, pad + ((0, 0),))
        alpha = np.pad(alpha, pad)
        y0 += pad[0][0]; y1 += pad[0][0]; x0 += pad[1][0]; x1 += pad[1][0]
    col, alpha = col[y0:y1, x0:x1], alpha[y0:y1, x0:x1]
    R = REED["res"]
    col = np.asarray(Image.fromarray((col * 255 + .5).astype(np.uint8))
                     .resize((R, R), Image.LANCZOS), np.float32) / 255.0
    alpha = np.asarray(Image.fromarray((alpha * 255 + .5).astype(np.uint8))
                       .resize((R, R), Image.LANCZOS), np.float32) / 255.0
    # ③ 색 계약. 덮개로 가중해서 재고 옮긴다(투명한 자리는 평균에 못 낀다)
    col = _fit_ratio_masked(col, alpha, REED["ref"], REED["std"], REED["hue"])
    # ④ 밑동. v=0 이 카드 아래다(아래에서 s20 이 그렇게 UV 를 찍는다)
    yy = np.linspace(1.0, 0.0, R)[:, None]                # 위 1 -> 아래 0
    k = np.where(yy < REED["root"],
                 REED["root_k"] + (1.0 - REED["root_k"]) * (yy / REED["root"]), 1.0)
    col = np.clip(col * k[:, :, None], 0.0, 1.0)
    path = os.path.join(out_dir, "prop_reed.png")
    rgba = np.concatenate([(col * 255 + .5).astype(np.uint8),
                           (alpha * 255 + .5).astype(np.uint8)[:, :, None]], axis=2)
    Image.fromarray(rgba, "RGBA").save(path)
    print("── prop_reed  <-  %s   (%dx%d 알파 카드)" % (REED["src"], R, R))
    return path, prop_report("prop_reed", path, col, alpha)


def build_props(out_dir):
    """소품 타일 셋을 굽고 계약값을 json 으로 남긴다.

    ★json 이 필요한 이유: blender/s20_level1.py 에는 PIL 이 없어서 png 의 평균색을
      스스로 못 잰다. 재질 곱수 k = 목표색/타일평균 이 그 값에서 나오므로,
      **여기서 재서 넘긴다.** (s20 이 어림으로 적으면 팔레트가 조용히 밀린다.)"""
    os.makedirs(out_dir, exist_ok=True)
    table = {}
    for n in PROP_SPEC:
        _p, table[n] = build_prop_tile(n, out_dir)
    _p, table["prop_reed"] = build_reed_card(out_dir)
    with open(os.path.join(out_dir, "prop_tiles.json"), "w") as f:
        json.dump(table, f, ensure_ascii=False, indent=1)
    print("[소품타일] %s (%d장) + prop_tiles.json"
          % (out_dir, len(table)))
    return table


def main():
    only, out_dir = None, TEX_DIR
    # ★소품 타일은 지면 타일과 나가는 자리가 다르다(web/tex 가 아니라 blender/tex).
    #   같이 굽되 따로 내보낸다.
    if "--props" in sys.argv:
        pd = PROP_TEX_DIR
        for a in sys.argv[1:]:
            if a.startswith("--propout="):
                pd = a[10:] if os.path.isabs(a[10:]) else os.path.join(ROOT, a[10:])
        build_props(pd)
        if "--only-props" in sys.argv:
            return
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = set(a[7:].split(","))
        elif a.startswith("--out="):
            out_dir = a[6:] if os.path.isabs(a[6:]) else os.path.join(ROOT, a[6:])
    os.makedirs(out_dir, exist_ok=True)

    paths, table = {}, {}
    for name in TILE_SET:
        if only and name not in only:
            continue
        paths[name], table[name] = build_one(name, out_dir)

    # 절차 v2 도 같은 자로 재서 한 표에 놓는다.
    # ★백업을 web/ 밑에 두면 안 된다. tools/build_deploy.py 가 web/ 를 통째로 훑어
    #   복사하기 때문에(이름에 bak 이 든 파일만 뺀다) 배포본에 7MB 가 그대로 실린다.
    proc_dir = os.path.join(OUT_DIR, "_ab", "proc_v2")
    for name in paths:
        p = os.path.join(proc_dir, name + ".png")
        if os.path.exists(p):
            a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255.0
            table[name]["proc_v2"] = {"grain": measure_grain(a, name),
                                      "ratio": measure_ratio(a),
                                      "seam": seam_score(a),
                                      "kb": round(os.path.getsize(p) / 1024.0, 1)}

    print("═" * 96)
    print("%-11s %-9s %8s %9s %9s %9s %8s" %
          ("장", "판", "잔결비", "끓음", "화면%", "비율std", "클램프%"))
    for name in TILE_SET:
        if name not in table:
            continue
        rows = [("MESHY 원본", table[name]["raw"]),
                ("MESHY 후처리", table[name]["out"])]
        if "proc_v2" in table[name]:
            rows.append(("절차 v2", table[name]["proc_v2"]))
        for lbl, d in rows:
            print("%-11s %-9s %8.3f %9.5f %8.2f%% %9.4f %7.3f%%"
                  % (name if lbl.startswith("MESHY 원") else "", lbl,
                     d["grain"]["hf_ratio"], d["grain"]["boil"],
                     d["grain"]["boil"] * 100, d["ratio"]["rstd"],
                     d["ratio"]["clamp_pct"]))
    print("═" * 96)
    tot = sum(t["out"]["kb"] for t in table.values())
    print("[예산] 지면 타일 %d장 합계 %.0f KB (상한 4096 KB)" % (len(table), tot))
    # ★v94. 3072 -> 4096. 대역 재배치로 붓맛이 살아나면서 png 가 3019 -> 3274 KB 가
    #   됐다. 압축이 나빠진 게 아니라 **그림에 정보가 늘어난 것**이라 줄일 이유가 없다
    #   (오너 지시: 설치형이라 용량·폴리곤 예산 제약 없음). 폭주 감지용으로만 남긴다.
    # ★손그림은 절차 타일보다 색이 훨씬 많아서 png 가 40~60배 커진다(14KB -> 650KB).
    #   설치형(스팀)이라 용량 제약이 없고 상한 안이지만, 넘기면 여기서 걸린다
    if tot > 4096:
        print("      ★상한 초과. 색 수를 줄이거나 해상도를 낮춰야 한다")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "table.json"), "w") as f:
        json.dump(table, f, ensure_ascii=False, indent=1)

    if paths and "--no-sheet" not in sys.argv:
        print("검증 이미지: %s" % tile_sheet(paths, "01_seam_meshy_2x2.png",
                                        "MESHY 후처리 · 2x2 이어붙임 (가운데 십자가 이음매)"))
        proc = {n: os.path.join(proc_dir, n + ".png") for n in paths
                if os.path.exists(os.path.join(proc_dir, n + ".png"))}
        if proc:
            print("검증 이미지: %s" % tile_sheet(proc, "01_seam_proc_2x2.png",
                                            "절차 v2 · 2x2 이어붙임"))
        sets = []
        for n in TILE_SET:
            if n not in paths:
                continue
            v = [("MESHY 원본", os.path.join(SRC_DIR, SPEC[n]["src"])),
                 ("MESHY 후처리", paths[n])]
            if n in proc:
                v.append(("절차 v2", proc[n]))
            sets.append((n, v))
        print("검증 이미지: %s" % gamedist_sheet(sets, "02_gamedist_3way.png",
                                            "게임 거리(75px/m)로 줄인 뒤 확대 = 자글거림의 재료"))


if __name__ == "__main__":
    main()
