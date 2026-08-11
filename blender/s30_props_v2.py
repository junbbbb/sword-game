# -*- coding: utf-8 -*-
"""Meshy 재생산본(incoming/meshy_props_v2·v3/*.glb)을 게임용으로 다듬어
web/props/<종류>.glb 로 굽는다. (2026-08-11, 11차 파도 11-소품B·11-소품C)

    blender -b -P blender/s30_props_v2.py
    RENDER=0 blender -b -P blender/s30_props_v2.py            (검증 렌더 생략)
    LOD=low RENDER=0 blender -b -P blender/s30_props_v2.py    (web/props/low/ 한 벌)
    ONLY=bush blender -b -P blender/s30_props_v2.py           (적은 종류만)

★★ONLY 없이 돌리면 **여섯 종 전부** 다시 굽는다. 그러면 그 여섯 종의 텍스처가
   전부 Meshy 원색으로 돌아가므로 뒤 세 단계(재칠·가림굽기·가림칠하기)도
   **여섯 종 전부** 다시 돌려야 한다. 한 종만 손볼 때는 반드시 ONLY 를 준다.

왜 새 파일인가 — 이 셋만 "메시가 범인"이었다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
11차 소품 진단(renders/history/v97_wave11/props/)의 결론은 셋이었다.
  · 셰이딩 = 4단 셀 램프(web/props.js RAMP) + 가림 칠하기(tools/paint_prop_ao.py) 로 닫았다
  · **남은 것은 메시 자체**다 — crag(1,856삼각 찰흙덩이) · bush(깨진 유리 잎) ·
    cliff_tall(민짜 직육면체 115개 반복)
오너가 이 셋을 Meshy 로 다시 뽑아 왔다. 이 파일은 **그 셋만** 굽는다.
s22_props.py / s28_terrain.py 는 손대지 않는다(나머지 7종의 산출물이 그대로 있어야 한다).

s22·s28 과 다른 점 — 색을 여기서 안 칠한다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s22·s28 은 굽는 자리에서 재칠까지 했고, 그 뒤 10차에서 tools/regrade_props.py 가
**화면 목표색**으로 한 번 더 칠했다(색계약의 정본이 그쪽으로 옮겨 갔다).
두 벌을 겹쳐 칠하면 어느 손잡이가 무엇을 했는지 못 읽는다. 그래서 여기서는
텍스처를 **크기만 맞춰 그대로 내보내고**, 팔레트 정합은 regrade_props.py 하나가 한다.
    굽기(이 파일) -> tools/regrade_props.py -> blender/s29_prop_ao.py -> tools/paint_prop_ao.py
★그래서 이 파일이 내보낸 직후의 glb 는 **Meshy 원색**이다. 그대로 게임에 넣으면 튄다.
  반드시 위 세 단계를 이어서 돌려라.

봉투(envelope)를 옛 자산에 **정확히** 맞춘다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
배치 테이블(level1.json props[])과 콜라이더는 한 톨도 안 건드리는 것이 이 작업의
전제다. 그러려면 새 메시의 **치수가 옛 메시와 같아야** 한다(배치의 scale·sy 가
그대로 통해야 하므로). 실측한 옛 치수:
    crag        반너비 1.25 / 높이 2.031      (web/props/crag.glb)
    bush        반너비 0.98 / 높이 1.295      (web/props/bush.glb)
    cliff_tall  반너비 0.541 x 0.432 / 높이 4.60
★그런데 새 crag·bush 는 **더 납작하다**(crag 높이/반너비 1.13, 옛것 1.63).
  가로를 옛 값에 맞추면 키가 2.03 -> 1.40 으로 내려앉는다. crag 는 "시야를 끊는" 물건이라
  (s20_level1.py 주석 "바위 절벽 덩어리 2.6m") 키가 곧 기능이다.
  -> `zfit` : 가로 정규화 뒤 **세로만** 늘려 옛 높이에 맞춘다.
     세로 배율은 원래 web/props.js 의 KIND_Y 가 하던 일이고(crag 1.25 · bush 1.35),
     그 값을 그대로 두려면 여기서 미리 늘려 두는 편이 낫다 — 그래야
     "옛 glb 와 bbox 가 같다"는 한 줄로 배치 불변을 증명할 수 있다.
  ★세로 늘림은 **옆면 텍셀만** 늘린다. 쿼터뷰는 윗면을 주로 보므로 화면 손해가 작다.

cliff_tall_b — 교체가 아니라 **변주**다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cliff_tall 은 텍스처가 좋아서 갈아치울 이유가 없다. 문제는 115개가 **같은 실루엣**인
것이라 답은 변주 추가다. 그래서 이 종류만 새 이름(cliff_tall_b)으로 나가고
web/props.js 가 배치의 일부를 이쪽으로 돌린다(배치 테이블은 안 건드린다).
★들어온 원본이 cliff_tall 보다 **1.42배 넓고 1.93배 깊다.** 그대로 세우면
  (가) 이웃과 어깨 간격(TER_CLIFF_HX 0.541 기준)이 어긋나고
  (나) 앞으로 0.54m 더 튀어나와 "보이는데 안 막히는" 자리가 그만큼 넓어진다
      (s20 은 앞면을 막는 선 + 0.35m 에 세운다).
  -> `squash` 로 x·y 를 눌러 봉투를 cliff_tall 에 맞춘다. 바위는 정해진 비례가 없어서
     눌러도 "다른 바위"로 보일 뿐이고, **깨진 상단·파인 옆면의 실루엣은 그대로 산다.**
     자르는 쪽(cut)만으로 맞추려면 폭의 37%를 썰어야 해서 그 실루엣이 날아간다.

함정 (앞 판들이 이미 밟은 것들)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
★껍질 메움: Meshy 메시는 닫힌 덩어리가 아니다(crag 경계변 485 · bush 259).
  닫히지 않은 껍질을 그대로 데시메이트하면 갈라진 자리마다 면이 따로 무너져
  **깨진 달걀 껍데기**가 된다(s28 v91 1차 굽기가 그랬다). 감축 **전에** 메운다.
★정점 병합: glTF 임포트 직후엔 UV·노멀이 갈리는 자리마다 정점이 쪼개져 들어온다
  (bush 23,818 -> 12,721). 안 하고 깎으면 붙어 있어야 할 면이 따로 무너진다.
★새 bush 는 **낱장 잎이 아니라 잎뭉치 덩어리 72개**다. 그래서 s22 의 복셀 리메시
  (낱장 잎 대응)를 쓰지 않고 데시메이트로 간다 — 복셀을 씌우면 뭉치 사이 틈이 메워져
  실루엣이 감자가 된다.
★모서리: 4단 셀 램프가 붙은 뒤로는 **각진 면이 곧 명암**이다. 전부 부드럽게 펴 버리면
  (s22 는 그렇게 한다) 새로 얻은 베벨·판면이 다시 뭉개진다. 각도별 스무딩을 쓴다.
"""

import bpy
import bmesh
import os
import math

import numpy as np

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming", "meshy_props_v2")
# 11-소품C. codex 콘셉트(incoming/codex_props/*.png)를 Meshy 로 3D 변환해 받은 한 벌.
# ★파일 이름이 dl_a/b/c 로 뒤섞여 왔다. 메시 통계로 갈랐다(아래 KINDS 주석).
SRC_V3 = os.path.join(ROOT, "incoming", "meshy_props_v3")
LOD = os.environ.get("LOD", "hi")               # "hi" | "low"
OUTDIR = os.path.join(ROOT, "web", "props")
if LOD == "low":
    OUTDIR = os.path.join(OUTDIR, "low")
RENDER = os.environ.get("RENDER", "1") != "0"
ONLY = [s.strip() for s in os.environ.get("ONLY", "").split(",") if s.strip()]
RENDER_DIR = os.environ.get("RENDER_DIR") or os.path.join(
    ROOT, "renders", "history", "v97_wave11", "props_b", "bake")
TMP = os.environ.get("TMPDIR_PROPS") or "/tmp"
# 저해상도 판의 텍스처는 게임에서 안 쓰인다(props.js 가 고폴리 것을 물린다). 그릇으로만 필요하다
TEX_SIZE = int(os.environ.get("TEX_SIZE", "512" if LOD == "low" else "2048"))
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

os.makedirs(OUTDIR, exist_ok=True)
if RENDER:
    os.makedirs(RENDER_DIR, exist_ok=True)

LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

# ─────────────────────────────────────────────────────────────
# 종류별 규격
# ─────────────────────────────────────────────────────────────
# src     : incoming/meshy_props_v2 의 파일 이름
# tri     : 목표 삼각형(고폴리). None 이면 원본 그대로 내보낸다
# lowtri  : LOD=low 목표. ★공정은 고폴리와 **완전히 같고** 삼각형 목표만 다르다
#           (s22 ★LOD1: 두 벌을 다른 설정으로 구우면 한 무리 안에서 한 포기만 튄다)
# squash  : 감축 뒤·컷 앞에 곱하는 축별 배율(봉투 맞추기용)
# cut     : 평면 컷 [(축, 부호 또는 "back", 남길 비율)]. s28_terrain.py 와 같은 규격
# norm    : ("xy", r) 가로 반지름을 r 로 / ("z", h) 높이를 h 로
# zfit    : 가로 정규화 뒤 **세로만** 이 높이에 맞춘다(위 ★봉투)
# smooth  : 각도별 스무딩 한계(도). None 이면 전부 부드럽게
KINDS = [
    # ── crag : 43개. 옛것은 1,856삼각 + 요철이 노멀맵에만 있어 "회색 찰흙"이었다 ──
    # 새 원본은 7,185삼각에 각진 판·베벨·이끼 틈새가 **메시에 들어 있다.**
    # 그래서 s22 가 crag 에만 걸어 두었던 세분(subdiv) + 휘도 디스플레이스를 **버린다.**
    # (그 둘은 "요철이 그림에만 있는 메시"를 살리려던 응급처치였다.)
    # 삼각형은 안 깎는다 — 7,185 는 옛 산출물(7,424)과 사실상 같은 예산이다.
    dict(name="crag", src="crag_v2", tri=None, lowtri=1600,
         norm=("xy", 1.25), zfit=2.031, smooth=38.0),
    # ── bush : 304개. 옛것은 낱장 잎을 복셀로 싸서 "깨진 유리 조각"이었다 ──
    # 새 원본은 잎뭉치 덩어리 72개(경계변 259). 복셀을 씌우면 뭉치 사이가 메워지므로
    # **껍질만 메우고 데시메이트**한다.
    # ★삼각형 목표는 실루엣 실측으로 정했다. 원본(24,990)을 기준으로 정사영 두 각도의
    #   실루엣 IoU 를 재면
    #       5,000 -> 0.971 / 0.977      4,200 -> 0.966 / 0.973
    #       3,600 -> 0.965 / 0.972        900 -> 0.895 / 0.915  (저폴리 판)
    #   5,000 과 4,200 의 차이가 **0.5pt** 뿐이다. 수풀은 맵에 304개라 이 한 종류가
    #   씬 삼각형의 3분의 1을 쓴다 — 눈에 안 보이는 0.5pt 에 8만 삼각형을 낼 이유가 없다.
    #   (5,000 으로 구웠을 때 씬 1,452,752 -> 1,542,842 = +6.2%, fps 중앙값 -3.9%.
    #    4,200/780 으로 내리면 씬이 교체 전과 거의 같아진다.)
    # ★그래도 옛 3,969 보다 높은 이유: 수풀은 플레이어가 **안에 들어가 2~4m 에서 보는**
    #   유일한 종류다(props.js 의 LOD 규칙도 수풀만 상위 30%를 고폴리로 심는다).
    dict(name="bush", src="bush_v2", tri=4200, lowtri=780,
         norm=("xy", 0.98), zfit=1.295, smooth=52.0),
    # ── cliff_tall_b : 변주 추가(교체 아님). 위 ★cliff_tall_b 주석 ──
    # 원본 3,954삼각은 cliff_tall(8,000)보다 성기지만 **덩어리가 단순해서** 모자라지 않는다.
    # 깎으면 깨진 상단의 각이 무너지므로 고폴리는 원본 그대로 간다.
    # squash: x 0.78 -> 반너비 0.666, 옆면 컷 0.81 -> 0.540 (cliff_tall 0.541)
    #         y 0.62 -> 반너비 0.600, 뒷면 컷 0.72 -> 0.432 (cliff_tall 0.432)
    dict(name="cliff_tall_b", src="cliff_var_v2", tri=None, lowtri=1600,
         squash=(0.78, 0.62, 1.0),
         cut=[(0, +1, 0.81), (0, -1, 0.81), (1, "back", 0.72)],
         norm=("z", 4.60), smooth=34.0),

    # ══ 11-소품C (2026-08-11) — codex 콘셉트 → Meshy 변환 3종 ══════════════
    # 앞 판들과 출처가 다르다. 오너의 새 아트 방향("사실적과 일러스트 사이")대로
    # codex(gpt-5.6-sol)가 콘셉트 그림을 그리고(incoming/codex_props/*.png)
    # 그것을 Meshy 이미지→3D 로 변환해 받았다. 그래서 **화풍이 콘셉트에 묶여 있다** —
    # 큰 판면 + 경계선 몇 개(롤 손그림 문법)가 메시와 텍스처 양쪽에 들어 있다.
    #
    # ★받은 파일 이름이 dl_a/b/c 로 뒤섞여 있었다. 메시 통계로 갈랐다(콘셉트 PNG 와 대조 확인):
    #     dl_c  8,838삼각 · 텍스처 평균 #535d24 S61%  -> tree   (초록 = 잎)
    #     dl_b  6,544삼각 · 텍스처 평균 #50504f S 6%  -> rock   (납작한 판석 무더기)
    #     dl_a  8,698삼각 · 텍스처 평균 #53534d S 9%  -> boulder_xl (돔형 큰 바위)
    #   ★dl_a 만 노멀·러프니스까지 세 장이 딸려 왔다. clean_material 이 베이스컬러
    #     한 장만 남기므로 그대로 두면 된다(게임이 나머지를 안 읽는다).
    #
    # ★★셋 다 **옛 자산보다 납작하다**(이미지 한 장에서 뽑은 3D 의 공통 성질이다).
    #      높이/반너비   tree 2.15 (옛 3.49) · rock 0.64 (옛 1.24) · boulder 0.75 (옛 1.32)
    #   가로를 옛 값에 맞추면 키가 각각 3.33 / 0.61 / 0.71m 로 내려앉는다. 그러면
    #     · 나무 79그루가 5.4m -> 3.3m = 맵의 스카이라인이 통째로 바뀐다
    #     · 바위 172개가 "넘어다볼 수 있는가"의 기록(콜라이더 h 1.9~2.5)과 어긋난다
    #   -> zfit 으로 **세로만** 늘려 옛 glb 와 봉투를 똑같이 맞춘다(11-소품B 와 같은 손잡이).
    #      늘림 배수 tree x1.62 · rock x1.93 · boulder x1.77. 옆면 텍셀만 늘어나는데
    #      쿼터뷰는 윗면을 주로 보므로 화면 손해가 작다.
    #
    # ★삼각형은 **안 깎는다**(고폴리). 셋 다 옛 산출물과 같은 예산이다
    #   (tree 8,838 vs 옛 9,994 · rock 6,544 vs 9,000 · boulder 8,698 vs 7,976).
    #   ★게임이 실제로 그리는 것은 저폴리다 — props.js 는 수풀 말고는 전부 low/ 를
    #     심는다. 그래서 씬 예산도 실루엣도 lowtri 가 정한다. 옛 값과 같게 맞췄다
    #     (tree 2,000 · rock 1,800 · boulder 1,600) = 씬 삼각형 불변.
    # ★캐노피가 **부채꼴**로 들어왔다 — 이미지 한 장에서 뽑은 3D 의 두 번째 성질이다.
    #   가로 반너비 x 0.587 / y 0.318 = 1.84 : 1 (옛 나무는 1.530 / 1.563 = 거의 원).
    #   맵의 나무 79그루는 rotY 가 제각각이라, 그대로 두면 **어떤 나무는 공 두 개를
    #   쌓은 것처럼** 좁게 선다(실측 회전 렌더 renders/.../props_c/bake/SHEET_yaw.png:
    #   yaw0 폭 3.42m · yaw90 폭 2.06m). 그렇다고 완전히 둥글게 펴려면 y 를 1.67배
    #   늘려야 해서 잎뭉치가 위에서 보면 계란이 된다.
    #   -> 절반만 편다. squash(0.86, 1.16) 로 1.84 -> **1.37 : 1**. 잎뭉치의 가로
    #      찌그러짐은 1.35배뿐이라 유기체에서는 안 읽힌다. 봉투(평균 반너비·높이)는
    #      squash 가 곱셈이라 정규화가 도로 맞춘다 = 배치 불변은 그대로다.
    # ★저폴리 목표만 옛 값(2,000)보다 높다 — **새 캐노피가 잎뭉치가 잘아서** 같은
    #   삼각형으로는 실루엣이 안 버틴다. 게임 카메라각(49.3도) 정사영 IoU 실측:
    #       목표 2,000 -> 실제 1,523 tri  IoU 0.874 / 0.857  (면적비 0.89 = 8% 쪼그라듦)
    #       목표 2,600 -> 실제 2,303 tri  IoU 0.912 / 0.898
    #       목표 3,400 -> 실제 3,332 tri  IoU 0.943 / 0.936  (옛 나무 LOD 0.936 과 동급)
    #     (옛 나무는 1,993 tri 로 0.936 이었다. 캐노피가 큰 덩어리라 잘 버텼다)
    #   3,400 이면 옛 품질과 같아지지만 나무 79그루 x1,339 = 씬 +7.3% 다. 11-소품B 가
    #   수풀에서 **+6.2% 에 fps -3.9%** 를 보고 되돌린 바로 그 자리라 안 간다.
    #   2,600 은 씬 +1.7%(+24.5k)에 IoU 0.90 대 = 수풀 저폴리(0.895/0.915)와 같은 급.
    # ★★목표와 실제가 다른 이유: `data.validate()` 가 데시메이트가 만든 퇴화면을
    #   지운다(2,599 -> 2,303). 목표 숫자만 보고 예산을 세우면 어긋난다.
    dict(name="tree", src="dl_c", dir=SRC_V3, tri=None, lowtri=2600,
         squash=(0.86, 1.16, 1.0),
         norm=("xy", 1.5465), zfit=5.40, smooth=50.0),
    # ★나무 스무딩만 50도로 무르다. 잎뭉치 경계는 세우되(값 계단) 뭉치 **안**은
    #   펴야 한다 — 잎 한 장씩 각이 서면 게임 거리에서 지지직거린다(11-소품B 가
    #   수풀에서 겪은 "제일 시끄러운 물체"가 그것이다).
    dict(name="rock", src="dl_b", dir=SRC_V3, tri=None, lowtri=1800,
         norm=("xy", 0.95), zfit=1.173, smooth=32.0),
    # ★rock 은 11차 진단에서 "AO 가 평균 0.99 = 가릴 것이 없다. 지오메트리가 매끈한
    #   덩어리이고 균열은 전부 그림이다. rock 계열의 답은 셰이딩이 아니라 메시다"로
    #   닫혔던 바로 그 종류다. 새 원본은 판과 판이 실제로 어긋나 있어서 가림이 생긴다.
    dict(name="boulder_xl", src="dl_a", dir=SRC_V3, tri=None, lowtri=1600,
         norm=("xy", 0.95), zfit=1.255, smooth=32.0),
    # ★boulder_xl 의 norm 은 rock 과 **같은 0.95** 여야 한다(s28_terrain.py 의 이유
    #   그대로): 배치 scale 이 콜라이더 반지름(0.95 x scale)과 1:1 로 통해야 보이는 것과
    #   막히는 것이 안 어긋난다.
]


# ─────────────────────────────────────────────────────────────
# 잡동사니 / 재질
# ─────────────────────────────────────────────────────────────
def drop_importer_junk():
    """★glTF 임포터가 'glTF_not_exported' 컬렉션에 Icosphere 를 만든다.
    glb 안에는 없는 물건이라 안 지우면 렌더와 치수 측정이 오염된다."""
    n = 0
    for o in list(bpy.context.scene.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)
            n += 1
    return n


def find_basecolor_image(ob):
    for slot in ob.material_slots:
        m = slot.material
        if not m or not m.node_tree:
            continue
        bsdf = next((n for n in m.node_tree.nodes
                     if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            li = bsdf.inputs.get("Base Color")
            if li and li.is_linked:
                src = li.links[0].from_node
                if src.type == "TEX_IMAGE" and src.image:
                    return src.image
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image and "base_color" in n.image.name:
                return n.image
    return None


def prep_texture(img, name):
    """크기만 맞춘다. **색은 안 건드린다**(위 ★색은 여기서 안 칠한다).

    ★s22 의 함정 3(픽셀을 고치면 익스포터가 팩된 원본을 도로 내보낸다)은
      여기서는 안 걸린다 — 픽셀을 아예 안 고치기 때문이다. 크기를 줄일 때만
      Image.scale() 을 쓰는데 이건 데이터블록 자체가 작아지므로 그대로 나간다."""
    w, h = img.size[0], img.size[1]
    a = np.empty(w * h * 4, dtype=np.float32)
    prev = img.colorspace_settings.name
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_get(a)
    img.colorspace_settings.name = prev
    rgb = a.reshape(-1, 4)[:, :3]
    mx, mn = rgb.max(axis=1), rgb.min(axis=1)
    S = float(np.where(mx > 1e-9, (mx - mn) / np.maximum(mx, 1e-9), 0.0).mean())
    print("      [원색] 평균 #%02x%02x%02x  S %.1f%%  V %.1f%%  휘도 %.1f  (%dx%d)"
          % (int(rgb[:, 0].mean() * 255), int(rgb[:, 1].mean() * 255),
             int(rgb[:, 2].mean() * 255), S * 100, mx.mean() * 100,
             float((rgb * LUM).sum(axis=1).mean()) * 255, w, h))
    if w > TEX_SIZE:
        img.scale(TEX_SIZE, TEX_SIZE)
        print("      [축소] %dx%d -> %dx%d" % (w, h, TEX_SIZE, TEX_SIZE))
    return img


def clean_material(ob, img, name):
    """베이스컬러 1장만 쓰는 새 재질로 갈아끼운다.
    ★게임은 MeshToonMaterial({map}) 로 다시 만든다(web/props.js). 여기 재질은
      '텍스처를 glb 에 담아 보내는 그릇' 이고 검증 렌더에서 눈으로 볼 대상이다.
    ★노멀·러프니스·이미시브는 안 담는다. 게임이 읽지도 않는데 파일만 커진다."""
    m = bpy.data.materials.new("MAT_" + name.upper())
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.location = (-380, 0)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    ob.data.materials.clear()
    ob.data.materials.append(m)
    return m


# ─────────────────────────────────────────────────────────────
# 메시
# ─────────────────────────────────────────────────────────────
def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def weld(ob, dist=1e-4):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    n0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    n1 = len(bm.verts)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return n0, n1


def uv_density(ob):
    """UV 면적 / 3D 면적의 제곱근 = 1m 당 UV 몇 칸인가.
    메운 면·단면에 평행투영으로 UV 를 줄 때 이 배율을 써야 텍셀 크기가 옆면과 같다."""
    me = ob.data
    uvl = me.uv_layers.active
    if uvl is None:
        return 1.0
    uv = np.empty(len(me.loops) * 2, dtype=np.float32)
    uvl.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    a3 = a2 = 0.0
    for p in me.polygons:
        ls = list(p.loop_indices)
        if len(ls) < 3:
            continue
        a3 += p.area
        for i in range(1, len(ls) - 1):
            p0, p1, p2 = uv[ls[0]], uv[ls[i]], uv[ls[i + 1]]
            a2 += abs((p1[0] - p0[0]) * (p2[1] - p0[1])
                      - (p2[0] - p0[0]) * (p1[1] - p0[1])) * 0.5
    if a3 <= 1e-9:
        return 1.0
    return math.sqrt(a2 / a3)


def fill_holes(ob, dens):
    """★껍질 메움(s28_terrain.py 의 fill_holes 와 같은 함수·같은 이유).
    닫히지 않은 껍질을 그대로 감축하면 갈라진 자리마다 면이 따로 무너진다.
    메운 면에도 UV 를 준다 — 안 주면 (0,0) 텍셀 한 점이 그 면 전체에 늘어난다."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    holes = [e for e in bm.edges if e.is_boundary]
    if not holes:
        bm.free()
        return 0, 0
    n_edge = len(holes)
    try:
        faces = bmesh.ops.holes_fill(bm, edges=holes, sides=0).get("faces", [])
    except Exception as ex:
        print("      [구멍] holes_fill 실패 %s" % ex)
        bm.free()
        return n_edge, 0
    faces = [f for f in faces if f.is_valid]
    for f in faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a2 = [i for i in (0, 1, 2) if i != ax]
        for l in f.loops:
            v = l.vert.co
            l[uvl].uv = (0.5 + v[a2[0]] * dens, 0.5 + v[a2[1]] * dens)
    if faces:
        bmesh.ops.triangulate(bm, faces=faces)
    left = len([e for e in bm.edges if e.is_boundary])
    bm.to_mesh(me)
    bm.free()
    me.update()
    return n_edge, left


def decimate(ob, target):
    tri0 = tri_count(ob)
    if not target or tri0 <= target:
        return
    md = ob.modifiers.new("DEC", "DECIMATE")
    md.decimate_type = "COLLAPSE"
    md.ratio = target / float(tri0)
    md.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=md.name)


def scale_axes(ob, sx, sy, sz):
    for v in ob.data.vertices:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    ob.data.update()


def detect_back(ob, axis):
    """어느 쪽이 '뒷면'인가 = 세부(삼각형)가 적은 쪽. s28 과 같은 판정이다."""
    pos = neg = 0
    for p in ob.data.polygons:
        n = p.normal[axis]
        if n > 0.35:
            pos += 1
        elif n < -0.35:
            neg += 1
    return (+1 if pos < neg else -1), pos, neg


def plane_cut(ob, axis, sign, coord, dens):
    """평면 하나로 자르고 단면을 메운다(s28 과 같은 함수).
    sign=+1 이면 co[axis] > coord 쪽을 버린다."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    uvl = bm.loops.layers.uv.active
    no = [0.0, 0.0, 0.0]
    no[axis] = float(sign)
    co = [0.0, 0.0, 0.0]
    co[axis] = coord
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no,
                           clear_outer=True, clear_inner=False)
    bm.verts.ensure_lookup_table()
    holes = [e for e in bm.edges if e.is_boundary]
    n_hole = len(holes)
    new = []
    if holes:
        try:
            new = bmesh.ops.holes_fill(bm, edges=holes, sides=0).get("faces", [])
        except Exception as ex:
            print("      [컷] holes_fill 실패 %s" % ex)
        left = [e for e in bm.edges if e.is_boundary]
        if left:
            try:
                new += bmesh.ops.triangle_fill(bm, edges=left,
                                               use_beauty=True).get("geom", [])
            except Exception as ex:
                print("      [컷] triangle_fill 실패 %s" % ex)
    faces = [f for f in new if isinstance(f, bmesh.types.BMFace)]
    if faces:
        bmesh.ops.triangulate(bm, faces=faces)
    ax2 = [i for i in (0, 1, 2) if i != axis]
    for f in bm.faces:
        if abs(f.normal[axis]) < 0.85:
            continue
        if abs(f.calc_center_median()[axis] - coord) > 1e-3:
            continue
        for l in f.loops:
            v = l.vert.co
            l[uvl].uv = (0.5 + v[ax2[0]] * dens, 0.5 + v[ax2[1]] * dens)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return n_hole, len(faces)


def clamp_plane(ob, axis, sign, coord):
    """평면 밖으로 나간 정점을 평면 위로 눌러 붙인다(어깨가 안 맞으면 컷한 뜻이 없다)."""
    n = 0
    for v in ob.data.vertices:
        if sign > 0 and v.co[axis] > coord + 1e-6:
            v.co[axis] = coord
            n += 1
        elif sign < 0 and v.co[axis] < coord - 1e-6:
            v.co[axis] = coord
            n += 1
    ob.data.update()
    return n


def world_verts(ob):
    mw = ob.matrix_world
    return np.array([(mw @ v.co)[:] for v in ob.data.vertices], dtype=np.float64)


def centre_xy(ob):
    vs = world_verts(ob)
    cx = (vs[:, 0].min() + vs[:, 0].max()) / 2.0
    cy = (vs[:, 1].min() + vs[:, 1].max()) / 2.0
    for v in ob.data.vertices:
        v.co.x -= cx
        v.co.y -= cy
    ob.data.update()


def recentre_ground(ob):
    """원점을 바닥 중심으로. 최저점 z=0, **발자국 중심**이 xy 원점.
    ★전체 bbox 중심으로 잡으면 위가 한쪽으로 뻗은 조각에서 밑동이 배치 좌표를 벗어난다."""
    vs = world_verts(ob)
    z0, z1 = vs[:, 2].min(), vs[:, 2].max()
    H = z1 - z0
    foot = vs[vs[:, 2] <= z0 + H * 0.30]
    if len(foot) < 20:
        foot = vs
    cx = (foot[:, 0].min() + foot[:, 0].max()) / 2.0
    cy = (foot[:, 1].min() + foot[:, 1].max()) / 2.0
    for v in ob.data.vertices:
        v.co.x -= cx
        v.co.y -= cy
        v.co.z -= z0
    ob.data.update()


def normalize_size(ob, mode, target):
    vs = world_verts(ob)
    rx = max(abs(vs[:, 0]).max(), 1e-6)
    ry = max(abs(vs[:, 1]).max(), 1e-6)
    hh = max(vs[:, 2].max(), 1e-6)
    f = target / hh if mode == "z" else target / ((rx + ry) / 2.0)
    for v in ob.data.vertices:
        v.co *= f
    ob.data.update()
    return f


def fit_height(ob, h):
    """세로만 늘려 목표 높이에 맞춘다(위 ★봉투). 배율을 돌려준다."""
    vs = world_verts(ob)
    hh = max(vs[:, 2].max(), 1e-6)
    f = h / hh
    for v in ob.data.vertices:
        v.co.z *= f
    ob.data.update()
    return f


def shade(ob, angle_deg):
    """각도별 스무딩. ★4단 셀 램프가 붙은 뒤로는 각진 면이 곧 명암이다.
    전부 부드럽게 펴면(s22 의 방식) 새로 얻은 베벨·판면이 도로 뭉개진다.
    ★블렌더 4.1+ 는 mesh.auto_smooth 가 없다. shade_smooth_by_angle 오퍼레이터가
      같은 일을 하는데, 이름이 판마다 갈려서 없으면 그냥 전부 부드럽게 둔다."""
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.update()
    if angle_deg is None:
        return "smooth"
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))
        return "by_angle %.0f도" % angle_deg
    except Exception as ex:
        print("      [스무딩] shade_smooth_by_angle 없음(%s) -> 전부 부드럽게" % ex)
        return "smooth(폴백)"


# ── 렌더 준비(검증용. s22·s28 과 같은 조명·카메라) ───────────
def setup_render_scene():
    sc = bpy.context.scene
    ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                        else "BLENDER_EEVEE")
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("W") if sc.world is None else sc.world
    sc.world = w
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.47, 0.52, 1)
    for nm, en, rot in (("SUN", 3.0, (44, 0, -40)), ("FILL", 1.2, (-50, 0, 150))):
        li = bpy.data.lights.new(nm, "SUN")
        li.energy = en
        so = bpy.data.objects.new(nm, li)
        so.rotation_euler = tuple(math.radians(a) for a in rot)
        sc.collection.objects.link(so)
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam, cd


def shot(cam, cd, ob, path, px=560, yaw=-28.0):
    from mathutils import Vector
    vs = world_verts(ob)
    lo, hi = vs.min(axis=0), vs.max(axis=0)
    ctr = Vector(((lo + hi) / 2.0).tolist())
    rad = float(np.linalg.norm(hi - lo)) * 0.5
    sc = bpy.context.scene
    sc.render.resolution_x = px * 2
    sc.render.resolution_y = px
    cd.type = "ORTHO"
    cd.ortho_scale = rad * 2.35
    d = Vector((math.cos(math.radians(yaw)) * math.cos(math.radians(22)),
                math.sin(math.radians(yaw)) * math.cos(math.radians(22)),
                math.sin(math.radians(22))))
    cam.location = ctr + d * (rad * 4.0)
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


# ─────────────────────────────────────────────────────────────
# 본작업
# ─────────────────────────────────────────────────────────────
REPORT = []
if ONLY:
    unknown = [n for n in ONLY if n not in [k["name"] for k in KINDS]]
    if unknown:
        raise RuntimeError("ONLY 에 모르는 종류가 있다: %s" % ", ".join(unknown))
for spec in KINDS:
    name = spec["name"]
    if ONLY and name not in ONLY:
        print("\n===== %s (ONLY 로 건너뜀) =====" % name)
        continue
    print("\n===== %s (%s) [%s] =====" % (name, spec["src"], LOD))
    bpy.ops.wm.read_homefile(use_empty=True)
    cam, cd = setup_render_scene() if RENDER else (None, None)

    src = os.path.join(spec.get("dir") or SRC, spec["src"] + ".glb")
    src_mb = os.path.getsize(src) / 1024.0 / 1024.0
    bpy.ops.import_scene.gltf(filepath=src)
    drop_importer_junk()
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError("%s: 메시가 %d개다(1개를 기대했다)" % (name, len(meshes)))
    ob = meshes[0]
    ob.name = name.upper()
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    tri0 = tri_count(ob)

    img = find_basecolor_image(ob)
    if img is None:
        raise RuntimeError("%s: 베이스컬러 이미지를 못 찾았다" % name)
    print("  원본 삼각형 %d / 이미지 %s %s / 파일 %.2fMB"
          % (tri0, img.name, tuple(img.size), src_mb))
    tex = prep_texture(img, name)

    # ── 1) 병합 -> 껍질 메움 -> 감축 ────────────────────────
    n0, n1 = weld(ob)
    print("  정점 병합 %d -> %d" % (n0, n1))
    nh, nleft = fill_holes(ob, uv_density(ob))
    if nh:
        print("  껍질 메움: 경계변 %d -> 남은 %d (삼각형 %d)" % (nh, nleft, tri_count(ob)))
    tgt = spec.get("lowtri") if LOD == "low" else spec.get("tri")
    decimate(ob, tgt)
    print("  삼각형 %d -> %d (목표 %s)" % (tri0, tri_count(ob), tgt or "안 깎음"))

    # ── 2) 봉투 누르기 + 평면 컷 ★감축 뒤에 자른다(s28 ★컷) ─
    if spec.get("squash"):
        sq = spec["squash"]
        scale_axes(ob, *sq)
        print("  봉투 누르기 x%.2f y%.2f z%.2f" % sq)
    cuts_done = []
    if spec.get("cut"):
        dens = uv_density(ob)
        centre_xy(ob)
        vs = world_verts(ob)
        half = [max(abs(vs[:, i]).max(), 1e-6) for i in range(3)]
        planes = []
        for (axis, sgn, frac) in spec["cut"]:
            if sgn == "back":
                s_, npos, nneg = detect_back(ob, axis)
                print("  [컷] 축%d 앞뒤 면수 +%d / -%d -> 뒷면은 %s 쪽"
                      % (axis, npos, nneg, "+" if s_ > 0 else "-"))
            else:
                s_ = sgn
            planes.append((axis, s_, s_ * half[axis] * frac))
        for (axis, s_, coord) in planes:
            nh2, nf = plane_cut(ob, axis, s_, coord, dens)
            cuts_done.append((axis, s_, coord))
            print("  [컷] 축%d %s%.3f 에서 자름 -> 단면 경계 %d변, 메운 면 %d"
                  % (axis, "+" if s_ > 0 else "-", abs(coord), nh2, nf))
        for (axis, s_, coord) in cuts_done:
            nc = clamp_plane(ob, axis, s_, coord)
            if nc:
                print("  [컷] 축%d 평면 클램프 %d정점" % (axis, nc))
        print("  컷 후 삼각형 %d" % tri_count(ob))

    ob.data.validate(verbose=False)
    how = shade(ob, spec.get("smooth"))
    tri1 = tri_count(ob)
    clean_material(ob, tex, name)

    # ── 3) 원점(바닥) + 크기 정규화 + 세로 맞춤 ─────────────
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    recentre_ground(ob)
    mode, target = spec["norm"]
    f = normalize_size(ob, mode, target)
    fz = 1.0
    if spec.get("zfit"):
        fz = fit_height(ob, spec["zfit"])
    recentre_ground(ob)

    vs = world_verts(ob)
    hx, hy, hz = abs(vs[:, 0]).max(), abs(vs[:, 1]).max(), vs[:, 2].max()
    ymin, ymax = vs[:, 1].min(), vs[:, 1].max()
    print("  정규화 x%.4f (%s %.2f) + 세로맞춤 x%.4f  스무딩 %s"
          % (f, mode, target, fz, how))
    print("  -> 반너비 x %.3f / y %.3f (%.3f~%.3f) / 높이 %.3f"
          % (hx, hy, ymin, ymax, hz))
    print("  접지 최저점 z=%.5f (0 이어야 한다)" % vs[:, 2].min())

    if RENDER and LOD == "hi":
        shot(cam, cd, ob, os.path.join(RENDER_DIR, "%s_front.png" % name))
        shot(cam, cd, ob, os.path.join(RENDER_DIR, "%s_back.png" % name), yaw=152.0)

    # ── 4) 내보내기 (★원자적 교체) ──────────────────────────
    dst = os.path.join(OUTDIR, name + ".glb")
    tmp = os.path.join(OUTDIR, "_tmp_" + name + ".glb")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=tmp, export_format="GLB", use_selection=True,
        export_animations=False, export_yup=True, export_apply=True,
        export_image_format="JPEG", export_image_quality=TEX_QUALITY,
        export_jpeg_quality=TEX_QUALITY)
    os.replace(tmp, dst)
    mb = os.path.getsize(dst) / 1024.0 / 1024.0
    print("  -> %s  %.3f MB (텍스처 %d JPEG q%d)" % (dst, mb, TEX_SIZE, TEX_QUALITY))
    REPORT.append(dict(name=name, tri0=tri0, tri1=tri1, mb=mb,
                       hx=hx, hy=hy, hz=hz))

print("\n" + "=" * 84)
print("%-14s %8s %8s %8s  %s" % ("종류", "원본tri", "결과tri", "결과MB", "반너비x / y / 높이"))
for r in REPORT:
    print("%-14s %8d %8d %8.3f  %.3f / %.3f / %.3f"
          % (r["name"], r["tri0"], r["tri1"], r["mb"], r["hx"], r["hy"], r["hz"]))
print("합계 %.3f MB" % sum(r["mb"] for r in REPORT))
print("★다음: tools/regrade_props.py -> blender/s29_prop_ao.py -> tools/paint_prop_ao.py")
print("DONE")
