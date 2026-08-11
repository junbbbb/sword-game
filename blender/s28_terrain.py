# -*- coding: utf-8 -*-
"""Meshy 지형 5종(incoming/meshy_terrain/*.glb)을 게임용으로 다듬어
web/props/<종류>.glb 로 굽는다.

실행: blender -b -P blender/s28_terrain.py
      RENDER=0 blender -b -P blender/s28_terrain.py            (검증 렌더 생략)
      LOD=low RENDER=0 blender -b -P blender/s28_terrain.py    (저폴리 한 벌)

왜 이 파일이 생겼나 — 오너 판정 "돌·냇가가 찰흙"
  v90 까지 맵의 바위·절벽·기슭은 전부 **s20_level1.py 가 절차적으로 굽는 돔**이었다.
  돔은 정점 몇 개를 난수로 흔든 껍질이라 표면에 결이 없다. 툰 셰이딩에서 결이 없는
  곡면은 밝기 띠 두세 개로만 나뉘고, 그게 정확히 "찰흙을 손으로 뭉친 것" 으로 읽힌다.
  텍스처를 입히고 얼룩을 얹는 것으로는 못 고친다. **실물 스캔 밀도의 메시**가
  들어와야 한다. 그래서 Meshy 지형 5종을 받아 여기서 게임용으로 가공한다.

s22_props.py 와의 관계 — 공정은 같고 함정이 하나 더 있다
  s22 는 바위·나무·덤불 5종을 굽는다. 이 파일은 **지형 조각** 5종을 굽는다.
  임포트 -> 정점 병합 -> 감축 -> 색보정 -> 바닥 정규화 -> 내보내기 골격은 같다.
  다른 점이 셋이다.
    (1) ★불리언 평면 컷 (아래 ★컷)  — 절벽 2종은 이어붙어야 한다
    (2) ★따뜻한 그레이드 (아래 ★그레이드) — 받은 텍스처가 회색으로 죽어 있다
    (3) ★보라 얼룩 제거 (bank) — Meshy 가 이끼 그늘에 자홍색을 섞어 놨다

★컷 — "뒷면이 유기적이라 이어붙질 않는다"
  cliff_wall_tall 은 기둥 하나다. 이걸 외곽 절벽 앞에 줄지어 세우면 절벽면이 된다.
  그런데 받은 그대로는 옆면·뒷면이 둥글어서 두 개를 붙이면 사이에 V 자 틈이 벌어지고
  그 틈으로 뒤의 절차 절벽이 비친다(= 가리려던 것이 더 잘 보인다).
  그래서 **평면으로 자르고 단면을 메운다.**
    - 옆면 두 장: 이웃과 어깨를 맞대는 면. 자른 폭이 곧 배치 간격의 기준이 된다
    - 뒷면 한 장: 절차 절벽 쪽. 안 보이지만 열어 두면 뒤에서 볼 때 구멍이 된다
  ★자르는 순서가 중요하다. **자르고 나서 감축**하면 데시메이트가 단면 모서리를
    둥글게 무너뜨려 다시 안 붙는다. **감축하고 나서 자르면** 단면이 정확히 평면이다.
    그래서 감축 -> 컷 -> (혹시 몰라) 평면 클램프 순서로 간다.
  ★단면에도 UV 를 준다. 안 주면 (0,0) 텍셀 한 점이 단면 전체에 늘어나서
    "회색 판때기 한 장"이 된다(자르기 전 상태로 되돌아가는 셈이다).
    자른 평면 위로 평행투영하고, 배율은 **원본의 텍셀 밀도**에서 뽑는다.

★그레이드 — "회색으로 채도가 죽어 있다"를 봄 초원 팔레트에 맞춘다
  받은 텍스처의 평균 채도가 절벽 2종은 0.07 이다(거의 무채색). 그대로 게임에 넣으면
  연둣빛 초원 한가운데 **색이 빠진 회색 덩어리**가 서 있게 된다.
  방법은 s22 의 색계약을 그대로 따른다 — 목표 평균색을 정하고 픽셀을 그 색으로
  다시 칠하되, 세 가지를 더 한다.
    (1) 목표색 = 맵 팔레트 색을 **따뜻한 쪽으로 d 만큼** 민 값이다.
        R 을 d/2 올리고 B 를 d/2 내린 뒤 **휘도를 원래대로 되돌린다**(아래 warm()).
        그래서 밝기는 한 톨도 안 움직이고 색온도만 따뜻해진다.
    (2) 스플릿 톤: 밝은 면은 더 따뜻하게, 어두운 면은 더 차갑게 가른다.
        볕을 받는 면과 그늘의 색온도가 갈리는 것이 실제 바위가 회색 판과 다른 점이다.
        평균이 0 인 신호를 더하는 것이라 **평균색은 안 움직인다.**
    (3) 마지막에 평균색을 목표색으로 **정확히 되돌린다.**
        ★이게 색 규칙("밝고 따뜻하면 걸을 수 있다 / 차갑고 어두우면 못 간다")의
          안전장치다. 표면은 볕을 받는데 화면 평균색은 팔레트에서 한 톨도 안 나간다.
          아래 로그의 [그레이드] 줄이 목표색과 결과 평균색을 나란히 찍는다.

★보라 얼룩 (bank)
  river_bank_stones 의 이끼 그늘에 R·B 가 G 보다 높은 픽셀이 1.4% 섞여 있다
  (평균 #2a212c). 자홍색은 이 맵 어디에도 없는 색이라 젖은 돌에 곰팡이가 핀 것처럼
  보인다. G 를 R·B 의 평균 쪽으로 끌어올려 자홍기만 뺀다(명도는 안 건드린다).

★게임 쪽 계약 (s22 와 같다)
  - 텍스처는 **베이스컬러 한 장**만 내보낸다. 게임이 MeshToonMaterial 로 갈아끼우므로
    노멀·러프니스·이미시브는 읽히지도 않는다(들고 가면 파일만 커진다)
  - 원점은 **바닥 중심**(최저점 z=0, 발자국 중심이 xy 원점)
  - 크기는 배치 테이블의 scale 이 그대로 통하게 정규화한다(아래 NORM)
  - 콜라이더는 이 파일과 아무 관계가 없다. 지형 5종은 **전부 장식 전용**이고
    막는 일은 기존 콜라이더(외곽 절벽 링·물칸·바위 콜라이더)가 그대로 한다
"""

import bpy
import bmesh
import os
import math
import numpy as np

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming", "meshy_terrain")
LOD = os.environ.get("LOD", "hi")               # "hi" | "low"
OUTDIR = os.path.join(ROOT, "web", "props")
if LOD == "low":
    OUTDIR = os.path.join(OUTDIR, "low")
RENDER = os.environ.get("RENDER", "1") != "0"
RENDER_DIR = os.environ.get("RENDER_DIR") or os.path.join(
    ROOT, "renders", "history", "v91_terrain")
TMP = os.environ.get("TMPDIR_TERRAIN") or "/tmp"
# 저해상도 판의 텍스처는 게임에서 안 쓰인다(props.js 가 고폴리 것을 물린다). 그릇으로만 필요하다
TEX_SIZE = int(os.environ.get("TEX_SIZE", "512" if LOD == "low" else "2048"))
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

os.makedirs(OUTDIR, exist_ok=True)
if RENDER:
    os.makedirs(RENDER_DIR, exist_ok=True)

LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)],
                    dtype=np.float32)


def warm(h, d):
    """팔레트 색을 **휘도를 지키면서** 따뜻한 쪽으로 d(0~255 단위) 민다.
    R += d/2, B -= d/2 로 색온도를 밀면 휘도가 0.0702*d 만큼 올라가므로
    세 채널을 같은 비율로 되내려 원래 휘도에 정확히 맞춘다.
    = 맵의 명암 관계('어두우면 못 간다')는 안 건드리고 색온도만 바꾼다."""
    c = hex_rgb(h) * 255.0
    L0 = float((c / 255.0 * LUM).sum())
    c2 = np.array([c[0] + d / 2.0, c[1], c[2] - d / 2.0], dtype=np.float32)
    L1 = float((c2 / 255.0 * LUM).sum())
    c2 *= (L0 / max(L1, 1e-6))
    c2 = np.clip(c2, 0, 255)
    return "%02x%02x%02x" % (int(round(c2[0])), int(round(c2[1])), int(round(c2[2])))


# ─────────────────────────────────────────────────────────────
# 종류별 규격
# ─────────────────────────────────────────────────────────────
# src    : incoming 파일 이름
# tri    : 목표 삼각형(고폴리). lowtri = LOD=low 목표(대략 1/5)
# cut    : 평면 컷. [(축, 부호, 남길 비율), ...]
#          축 0=x 1=y 2=z, 부호 +1 이면 "그 축의 큰 쪽을 잘라낸다".
#          비율은 그 방향 bbox 반너비의 몇 배까지 남기나(1.0 = 안 자름).
#          ★자르기 전에 xy 중심을 bbox 중심으로 맞춘 뒤 잰다
# norm   : 크기 정규화. ("z", h)   = 높이를 h 로
#                       ("xy", r)  = 가로 반지름(x·y 반너비 평균)을 r 로
#                       ("len", r) = **긴 축** 반너비를 r 로 (띠 모양 전용)
# base   : 목표 평균색의 출발점. s20_level1.py 의 팔레트에서 그대로 가져온다
# warmd  : base 를 따뜻한 쪽으로 미는 양(0~255 단위. 휘도는 안 변한다)
# keep   : 원본 색편차를 얼마나 남기나(0=완전 단색조, 1=원본 색차 유지)
# keepg  : ★이끼(초록 우세) 픽셀에만 따로 주는 keep. 없으면 keep 과 같다.
#          왜 갈랐나 — boulder_xl·bank·slab 은 받은 텍스처의 **평균이 이끼색**이다
#          (#888e6c / #555f49 / #6b7665). 평균을 회색으로 옮기면 이끼가 아닌 돌은
#          "평균보다 초록이 적은 픽셀" 이 되고, keep 이 크면 그 편차가 그대로 남아
#          **돌 몸통이 연보라로 뜬다**(첫 굽기 텍스처가 실제로 그랬다).
#          그래서 돌 몸통은 keep 을 낮춰 순수한 명암으로 돌리고, 이끼 픽셀만
#          keepg 로 초록을 살린다. 이끼는 "찰흙이 아니다"의 핵심 단서라 못 버린다.
# weld   : 정점 병합 거리(없으면 1e-4). ★boulder_xl 만 크게 준다. 아래 ★껍질 참고
# gain   : ★조명 보정. 그레이드가 끝난 알베도에 마지막으로 곱하는 수.
#          왜 필요한가 — 게임은 소품과 맵 메시를 **다른 밝기로** 그린다.
#          맵의 절벽(COL_CLIFF)은 정점색(단 차이 음영, 평균 곱수 0.762)을 굽고
#          들어가서 알베도 #6e7883 이 화면에서 #4a5256 으로 내려앉는다.
#          반면 소품은 정점색이 없어서 알베도가 거의 그대로 화면에 나온다
#          (v91 1차 실측: cliff_tall 알베도 #73777c -> 화면 #727773).
#          그대로 두면 같은 "절벽"인데 새로 세운 기둥만 1.5배 밝아서
#          **재질이 분열된다**(v89 3차 QA #5 가 바위에서 잡았던 바로 그 증상).
#          게다가 밝기는 이 맵에서 "갈 수 있나"의 신호라, 못 가는 절벽이 밝아지면
#          색 규칙 자체가 흔들린다. 그래서 화면 실측으로 역산한 곱수를 여기 박는다.
#          ★평균색 계약은 안 깨진다. 목표색은 그대로 두고 **밝기만** 내리는 스칼라라
#            색상(hue)이 안 움직인다. 아래 [조명보정] 줄이 결과 알베도를 찍는다.
# ctr    : 휘도 대비 배수(1.0 = 원본 그대로)
# split  : 스플릿 톤 세기. 밝은 면 +R/-B, 어두운 면 -R/+B
# purple : 자홍 얼룩 제거 세기(0 이면 안 한다)
KINDS = [
    # ── 절벽 기둥. 외곽 절벽 링 앞에 줄지어 세워 절차 절벽을 가린다 ──
    # ★H/W 4.18 로 이 다섯 중 제일 수직이다. 옆면 두 장 + 뒷면 한 장을 자른다.
    #   옆면을 0.90 으로 남기는 이유: 더 깎으면 판때기가 되고, 안 깎으면 이웃과
    #   어깨가 안 맞아 V 자 틈이 벌어진다(그 틈으로 가리려던 절벽이 비친다).
    dict(name="cliff_tall", src="cliff_wall_tall", tri=8000, lowtri=1600,
         cut=[(0, +1, 0.90), (0, -1, 0.90), (1, "back", 0.72)],
    # ★warmd 를 12 -> 6, split 을 0.11 -> 0.08 로 줄였다. 12/0.11 로 구웠더니
    #   게임 화면에서 기둥은 따뜻한 회갈색(#5b5f56, R>B)인데 그 뒤 절차 절벽은
    #   찬 청회색(#474f53, B>R)이라 **같은 절벽인데 색온도가 갈렸다.**
    #   기둥이 절벽 앞을 가리는 물건이라 둘은 한 지형으로 읽혀야 한다.
    #   따뜻하게 만드는 목적(찰흙 회색 탈출)은 채도 0.07->0.20 이 이미 달성했다.
    # ★v94. base 를 s20 팔레트 변경에 맞춰 626e7d 로 따라 옮긴다. 이 값은 맵 절벽
    #   (MAT_ROCK_DARK)과 **같은 색이어야 한다** — 기둥이 그 절벽 앞을 가리는
    #   물건이라 색이 갈리면 v89 가 고친 "재질 분열"이 그대로 돌아온다.
         norm=("z", 4.60), base="626e7d", warmd=6, keep=0.55, ctr=1.15, split=0.08,
         gain=0.76),
    # ── 낮은 노두. 절벽 발치·너덜 가장자리에 붙는다 ──
    # ★높이로 정규화한다(1.55m). 캐릭터 키 1.75 보다 낮아야 "몸은 못 지나가는데
    #   건너편이 보인다"는 이 맵의 개방감 문법(너덜 1.45m)과 같은 말이 된다.
    dict(name="outcrop", src="cliff_wall", tri=4000, lowtri=800,
         cut=[(1, "back", 0.80)],
    # ★실측 결과 화면 중앙값이 #747876 으로, 맵 팔레트의 너덜 바닥색 #74787c 과
    #   거의 정확히 겹쳤다(우연이지만 그대로 둔다). 노두는 너덜과 같은 언어여야 한다.
         norm=("z", 1.55), base="6f7c8a", warmd=6, keep=0.55, ctr=1.15, split=0.08,
         gain=0.76),   # ★v94 팔레트 이동(채도 15.2%->19.6%)
    # ── 거대 바위. 랜드마크 자리의 큰 바위를 통째로 갈아끼운다 ──
    # ★norm 을 rock 과 **같은 0.95** 로 맞춘다. 그래야 배치 테이블의 scale 이
    #   콜라이더 반지름(0.95 x scale)과 1:1 로 통해서, 보이는 것과 막히는 것이
    #   한 톨도 안 어긋난 채로 모양만 갈린다.
    dict(name="boulder_xl", src="boulder_xl", tri=8000, lowtri=1600,
         cut=None,
    # ★gain 0.82 의 근거: 알베도가 옛 rock 과 사실상 같은데(#8f9092 vs #8a9199)
    #   화면에서는 21% 더 밝게 나왔다(실측 중앙값 #b7b7aa 휘도 182 vs 옛 돔 150).
    #   덩어리가 각진 판으로 갈라져 있어서 위를 보는 면이 훨씬 많기 때문이다.
    #   그대로 두면 **못 가는 바위가 걸어 다니는 풀밭(휘도 192)만큼 밝아진다.**
    #   교체 대상인 옛 바위의 화면 밝기에 맞춰 되돌린다(150/182 = 0.82).
         norm=("xy", 0.95), base="7c8794", warmd=12, weld=0.003,   # ★v94 팔레트 이동
         keep=0.18, keepg=0.60, ctr=1.14, split=0.08, gain=0.82),
    # ── 강가 돌무더기 띠. 개울 기슭을 따라 눕는다 ──
    # ★긴 축 기준으로 정규화한다. 기슭은 칸 모서리를 따라 흐르는 **띠**라
    #   가로 반지름 평균으로 재면 길이가 들쭉날쭉해진다.
    dict(name="bank", src="river_bank_stones", tri=5000, lowtri=1000,
         cut=None,
         norm=("len", 1.30), base="7c8794", warmd=10,   # ★v94 팔레트 이동
         keep=0.20, keepg=0.65, ctr=1.14, split=0.07, purple=0.85, gain=0.90),
    # ── 판석 패드. 폐허·석탑 마당·판석길 가장자리 ──
    # ★목표색이 여울목 젖은 돌(b9c2ba)이다. 걸어 다니는 바닥에 놓는 장식이라
    #   바위색(어둡고 차갑다)으로 칠하면 "여기는 못 간다"고 거짓말을 하게 된다.
    dict(name="slab", src="flagstone_slab", tri=3000, lowtri=600,
         cut=None,
    # ★이끼 마스크는 안 쓴다. 이 판석은 돌 자체가 초록기를 띠어서 마스크가
    #   "이끼 vs 돌"이 아니라 "판 vs 틈"을 가른다(픽셀의 73%가 초록 우세로 잡혔다).
    #   가르는 의미가 없으므로 keep 하나로 균일하게 남긴다.
    # ★v94. 화면에서 판석이 **하얀 종잇조각**으로 떴다(텍스처 휘도 167 · 채도 9.4%
    #   = 다섯 중 제일 밝고 제일 무채색). 걸어 다니는 바닥이라 어둡게 만들 수는
    #   없지만(색 규칙), 여울목 젖은 돌보다 한 단 눌러 종이 티를 뺀다.
    #   base 휘도 -6% · gain 0.87 -> 0.80 = 화면 휘도 약 -13%.
    #   ★2차 조정: 0.80 으로도 화면에서 흰 종이 조각으로 읽혔다. keep 을 0.30 -> 0.52
    #   로 올려 원본 돌결의 색편차를 더 남기고(채도 10.6% -> 위로), gain 을 0.72 까지
    #   내린다. 걸어 다니는 바닥이라 여기가 하한이다(더 내리면 "못 가는 색"이 된다).
         norm=("xy", 1.10), base="a9b3ab", warmd=12, keep=0.52, ctr=1.12, split=0.07,
         gain=0.72),
]


# ─────────────────────────────────────────────────────────────
# 임포트 잡동사니
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


# ─────────────────────────────────────────────────────────────
# 텍스처 — 축소 + 자홍 제거 + 따뜻한 그레이드
# ─────────────────────────────────────────────────────────────
def sat_of(rgb):
    mx = rgb.max(axis=1)
    mn = rgb.min(axis=1)
    return float((np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0)).mean())


def prep_texture(img, spec, name):
    """축소 -> 자홍 제거 -> 그레이드. 결과를 PNG 로 저장하고 다시 읽어서 돌려준다.

    ★함정(s22 와 같다): Image.pixels 를 만지고 그대로 익스포트하면 익스포터가
      팩된 **원본**을 도로 내보낸다. 새 이미지 데이터블록 -> PNG 저장 -> 재로드 해야
      실제로 바뀐 그림이 나간다. 원본 데이터블록은 손대지 않는다.
    ★Image.pixels 는 컬러스페이스를 거쳐 선형으로 준다. sRGB 바이트 그대로 만지려면
      읽기 전에 Non-Color 로 바꾼다."""
    prev = img.colorspace_settings.name
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size[0], img.size[1]
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    img.colorspace_settings.name = prev
    a = buf.reshape(h, w, 4)

    tw = th = TEX_SIZE
    if w > tw and w % tw == 0 and h % th == 0:
        ky, kx = h // th, w // tw
        a = a.reshape(th, ky, tw, kx, 4).mean(axis=(1, 3))
        print("      [축소] %dx%d -> %dx%d" % (w, h, tw, th))
    else:
        tw, th = w, h

    rgb = a[:, :, :3].reshape(-1, 3).astype(np.float32)
    m0 = rgb.mean(axis=0)
    s0 = sat_of(rgb)
    L0 = (rgb * LUM).sum(axis=1)
    sd0 = float(L0.std())

    # ── 자홍 얼룩 제거 ─────────────────────────────────────
    if spec.get("purple"):
        g = rgb[:, 1]
        low = np.minimum(rgb[:, 0], rgb[:, 2])       # R·B 중 작은 쪽이 G 보다 높으면 자홍
        wgt = np.clip((low - g) / 0.03, 0.0, 1.0) * spec["purple"]
        n_pur = float((wgt > 0.05).mean()) * 100.0
        tgt_g = (rgb[:, 0] + rgb[:, 2]) * 0.5
        rgb[:, 1] = g + wgt * (tgt_g - g)
        after = ((np.minimum(rgb[:, 0], rgb[:, 2]) - rgb[:, 1]) > 0.02).mean() * 100.0
        print("      [자홍제거] 대상 %.2f%% -> 남은 %.2f%%" % (n_pur, after))

    # ── 그레이드 ───────────────────────────────────────────
    tgt_hex = warm(spec["base"], spec["warmd"])
    tgt = hex_rgb(tgt_hex)
    tl = float((tgt * LUM).sum())
    tint = tgt / max(tl, 1e-6)
    L = (rgb * LUM).sum(axis=1, keepdims=True)
    lm = float(L.mean())
    ls = float(L.std())
    k = spec.get("ctr", 1.0)
    # ★이끼 마스크. 초록이 나머지 두 채널보다 우세한 정도를 0~1 로 잰다.
    #   경계를 0.06 폭으로 부드럽게 넘겨야 이끼 테두리에 계단이 안 생긴다.
    kp = float(spec["keep"])
    kg = float(spec.get("keepg", kp))
    if abs(kg - kp) > 1e-6:
        gm = np.clip((rgb[:, 1] - np.maximum(rgb[:, 0], rgb[:, 2])) / 0.06,
                     0.0, 1.0)[:, None]
        keep = kp + (kg - kp) * gm
        print("      [이끼마스크] 초록 우세 픽셀 %.1f%% (keep %.2f, 나머지 %.2f)"
              % (float((gm > 0.5).mean()) * 100.0, kg, kp))
    else:
        keep = kp
    # s22 색계약과 같은 식: 휘도를 목표 휘도로 옮기고 색편차는 keep 만큼만 남긴다
    out = ((L - lm) * k + tl) * tint + (rgb - L) * keep * tint
    # 스플릿 톤. t 는 평균 0 이라 평균색을 안 민다(밝은 면 +R/-B, 어두운 면 -R/+B).
    # ★B 계수를 0.75 로 눌렀다. -1.0 이면 그늘이 순수한 파랑으로 들려서
    #   돌이 아니라 얼음처럼 보인다(봄 초원 팔레트에 안 맞는다).
    t = np.clip((L - lm) / max(ls * 2.0, 1e-6), -1.0, 1.0)
    sp = spec.get("split", 0.0)
    if sp:
        out[:, 0:1] += t * sp
        out[:, 1:2] += t * sp * 0.18
        out[:, 2:3] -= t * sp * 0.75
    np.clip(out, 0.0, 1.0, out=out)
    # ★마지막 안전장치: 평균색을 목표색으로 **정확히** 되돌린다.
    #   클리핑 때문에 평균이 조금 밀린다. 채널별 곱수로 다시 앉힌다
    #   (곱수라 결·대비는 그대로고 평균만 움직인다).
    # ★★단, 평균은 **이끼를 뺀 돌 몸통**에서 잰다.
    #   이끼까지 넣고 평균을 맞추면 이끼의 초록을 상쇄하려고 곱수가 G<1, R·B>1 이 되고,
    #   그 곱수를 돌 몸통도 같이 먹어서 **몸통이 연보라로 뜬다**(두 번째 굽기가 그랬다).
    #   색 규칙이 보는 것도 "그 물건의 몸통 색" 이지 이끼 얼룩이 아니다.
    bw = (1.0 - gm) if not np.isscalar(keep) else np.ones((len(out), 1), np.float32)
    bsum = float(bw.sum())
    body = (out * bw).sum(axis=0) / max(bsum, 1e-6)
    gain = tgt / np.maximum(body, 1e-6)
    out *= gain
    np.clip(out, 0.0, 1.0, out=out)

    body1 = (out * bw).sum(axis=0) / max(bsum, 1e-6)
    m1 = body1
    s1 = sat_of(out)
    sd1 = float((out * LUM).sum(axis=1).std())
    print("      [그레이드] 팔레트 #%s +warm%d -> 목표 #%s" % (spec["base"], spec["warmd"], tgt_hex))
    gn = float(spec.get("gain", 1.0))
    if abs(gn - 1.0) > 1e-6:
        out *= gn
        np.clip(out, 0.0, 1.0, out=out)
        ga = (out * bw).sum(axis=0) / max(bsum, 1e-6)
        print("      [조명보정] 곱수 %.2f -> 실제 알베도 #%02x%02x%02x "
              "(게임이 소품을 맵 메시보다 밝게 그린다. 위 gain 주석)"
              % (gn, int(round(ga[0] * 255)), int(round(ga[1] * 255)),
                 int(round(ga[2] * 255))))
    mall = out.mean(axis=0)
    print("      [그레이드] 돌몸통 평균 #%02x%02x%02x -> #%02x%02x%02x (목표 #%s, 오차 %.1f/255)"
          % (int(m0[0] * 255), int(m0[1] * 255), int(m0[2] * 255),
             int(round(m1[0] * 255)), int(round(m1[1] * 255)), int(round(m1[2] * 255)),
             tgt_hex, float(np.abs(m1 - tgt).max() * 255)))
    print("      [그레이드] 이끼까지 넣은 전체 평균 #%02x%02x%02x (참고값)"
          % (int(mall[0] * 255), int(mall[1] * 255), int(mall[2] * 255)))
    print("      [그레이드] 채도 %.3f -> %.3f  /  휘도σ %.3f -> %.3f  (keep %.2f 대비 x%.2f 스플릿 %.2f)"
          % (s0, s1, sd0, sd1, spec["keep"], k, sp))

    a[:, :, :3] = out.reshape(th, tw, 3)
    a[:, :, 3] = 1.0

    path = os.path.join(TMP, "terrain_%s_basecolor.png" % name)
    ni = bpy.data.images.new("TEX_" + name, tw, th, alpha=False, float_buffer=False)
    ni.colorspace_settings.name = "Non-Color"
    ni.pixels.foreach_set(a.reshape(-1))
    ni.filepath_raw = path
    ni.file_format = "PNG"
    ni.save()
    bpy.data.images.remove(ni)
    fin = bpy.data.images.load(path)
    fin.colorspace_settings.name = "sRGB"
    return fin, dict(mean=m1, sat0=s0, sat1=s1, target=tgt_hex)


def clean_material(ob, img, name):
    """베이스컬러 1장만 쓰는 새 재질로 갈아끼운다(게임은 MeshToonMaterial 로 다시 만든다)."""
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
    """★glTF 임포트 직후에는 UV·노멀이 갈리는 자리마다 정점이 쪼개져 들어온다.
    그대로 데시메이트하면 붙어 있어야 할 면이 따로 무너져 껍질이 조각조각 갈라진다."""
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


def decimate(ob, target):
    tri0 = tri_count(ob)
    if tri0 <= target:
        return
    md = ob.modifiers.new("DEC", "DECIMATE")
    md.decimate_type = "COLLAPSE"
    md.ratio = target / float(tri0)
    md.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=md.name)


def uv_density(ob):
    """UV 면적 / 3D 면적의 제곱근 = 1m 당 UV 몇 칸인가.
    단면에 평행투영으로 UV 를 줄 때 이 배율을 써야 텍셀 크기가 옆면과 같아진다."""
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
            a2 += abs((p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1])) * 0.5
    if a3 <= 1e-9:
        return 1.0
    return math.sqrt(a2 / a3)


def fill_holes(ob, dens):
    """★껍질 — Meshy 모델은 닫힌 덩어리가 아니다
    boulder_xl 은 경계변이 1,099개다(표면 여기저기가 갈라진 껍질이다).
    닫히지 않은 껍질을 그대로 데시메이트하면 갈라진 자리마다 면이 따로 무너져서
    **깨진 달걀 껍데기**가 된다(v91 1차 굽기 게임 화면이 정확히 그랬다.
    흰 파편이 삐죽 서고 안쪽 빈 속이 들여다보였다).
    그래서 감축 **전에** 구멍을 메워 닫힌 덩어리로 만든다. 1,099변이 17면으로
    덮이므로 삼각형 예산에는 사실상 영향이 없다.
    ★메운 면에도 UV 를 준다. 안 주면 (0,0) 텍셀 한 점이 그 면 전체에 늘어난다.
      면의 법선이 제일 큰 축을 빼고 나머지 두 축으로 평행투영한다."""
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


def detect_back(ob, axis):
    """어느 쪽이 '뒷면'인가. 세부가 적은 쪽 = 뒷면이다.
    그 축을 보는 면들의 **삼각형 수**로 센다(세부가 많으면 삼각형이 많다).
    돌려주는 값은 잘라낼 방향의 부호(+1 이면 그 축의 큰 쪽을 잘라낸다)."""
    me = ob.data
    pos = neg = 0
    for p in me.polygons:
        n = p.normal[axis]
        if n > 0.35:
            pos += 1
        elif n < -0.35:
            neg += 1
    return (+1 if pos < neg else -1), pos, neg


def plane_cut(ob, axis, sign, coord, dens):
    """평면 하나로 자르고 단면을 메운다. sign=+1 이면 co[axis] > coord 쪽을 버린다.
    ★단면 UV 는 자른 평면 위로 평행투영한다. 배율은 원본 텍셀 밀도(dens)라
      단면과 옆면의 텍셀 크기가 같다(= 단면만 늘어난 그림으로 안 보인다)."""
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
    # 남은 구멍(단면) 메우기
    holes = [e for e in bm.edges if e.is_boundary]
    n_hole = len(holes)
    new = []
    if holes:
        try:
            new = bmesh.ops.holes_fill(bm, edges=holes, sides=0).get("faces", [])
        except Exception as ex:
            print("      [컷] holes_fill 실패 %s" % ex)
        left = [e for e in bm.edges if e.is_boundary]
        if left:                       # 남은 경계는 삼각 팬으로 한 번 더
            try:
                new += bmesh.ops.triangle_fill(bm, edges=left, use_beauty=True).get("geom", [])
            except Exception as ex:
                print("      [컷] triangle_fill 실패 %s" % ex)
    faces = [f for f in new if isinstance(f, bmesh.types.BMFace)]
    if faces:
        bmesh.ops.triangulate(bm, faces=faces)
    # 단면 UV. 자른 축이 아닌 나머지 두 축을 UV 로 쓴다
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
    """평면 밖으로 나간 정점을 평면 위로 눌러 붙인다.
    ★데시메이트가 단면 모서리를 몇 mm 씩 밀어낼 수 있다. 그러면 이웃과 어깨가
      안 맞아 컷을 한 이유가 사라진다. 마지막에 한 번 눌러 정확한 평면으로 만든다."""
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
    """xy 를 bbox 중심으로. 컷 좌표를 대칭으로 잡기 위한 사전 정렬이다."""
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
    if mode == "z":
        f = target / hh
    elif mode == "len":
        f = target / max(rx, ry)
    else:
        f = target / ((rx + ry) / 2.0)
    for v in ob.data.vertices:
        v.co *= f
    ob.data.update()
    return f


# ── 렌더 준비(검증용. s22 와 같은 조명·카메라를 쓴다) ────────
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
for spec in KINDS:
    name = spec["name"]
    print("\n===== %s (%s) =====" % (name, spec["src"]))
    bpy.ops.wm.read_homefile(use_empty=True)
    cam, cd = setup_render_scene() if RENDER else (None, None)

    src = os.path.join(SRC, spec["src"] + ".glb")
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

    tex, ginfo = prep_texture(img, spec, name)
    if RENDER and LOD == "hi":
        clean_material(ob, tex, name + "_pre")
        shot(cam, cd, ob, os.path.join(RENDER_DIR, "tex_%s_before.png" % name))

    # ── 1) 감축 ─────────────────────────────────────────────
    tgt = spec.get("lowtri") if LOD == "low" else spec.get("tri")
    n0, n1 = weld(ob, spec.get("weld", 1e-4))
    print("  정점 병합 %d -> %d (거리 %.4f)" % (n0, n1, spec.get("weld", 1e-4)))
    # ★감축 **전에** 구멍을 메운다(위 fill_holes 의 ★껍질)
    nh, nleft = fill_holes(ob, uv_density(ob))
    if nh:
        print("  구멍 메우기: 경계변 %d -> 남은 %d (삼각형 %d)"
              % (nh, nleft, tri_count(ob)))
    decimate(ob, tgt)
    tri_dec = tri_count(ob)
    print("  삼각형 %d -> %d (목표 %d)" % (tri0, tri_dec, tgt))

    # ── 2) 평면 컷 ★감축 뒤에 자른다(위 ★컷) ───────────────
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
            nh, nf = plane_cut(ob, axis, s_, coord, dens)
            cuts_done.append((axis, s_, coord))
            print("  [컷] 축%d %s%.3f 에서 자름 -> 단면 경계 %d변, 메운 면 %d"
                  % (axis, "+" if s_ > 0 else "-", abs(coord), nh, nf))
        for (axis, s_, coord) in cuts_done:
            nc = clamp_plane(ob, axis, s_, coord)
            if nc:
                print("  [컷] 축%d 평면 클램프 %d정점" % (axis, nc))
        print("  컷 후 삼각형 %d" % tri_count(ob))

    ob.data.validate(verbose=False)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.update()
    tri1 = tri_count(ob)

    clean_material(ob, tex, name)

    # ── 3) 원점을 바닥 중심으로 + 크기 정규화 ───────────────
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    recentre_ground(ob)
    mode, target = spec["norm"]
    f = normalize_size(ob, mode, target)
    recentre_ground(ob)

    vs = world_verts(ob)
    fx, fy, fz = abs(vs[:, 0]).max(), abs(vs[:, 1]).max(), vs[:, 2].max()
    ymin, ymax = vs[:, 1].min(), vs[:, 1].max()
    print("  정규화 x%.4f (%s %.2f 기준) -> 반너비 x %.3f / y %.3f (%.3f~%.3f) / 높이 %.3f"
          % (f, mode, target, fx, fy, ymin, ymax, fz))
    print("  접지 최저점 z=%.5f (0 이어야 한다)" % vs[:, 2].min())

    if RENDER and LOD == "hi":
        shot(cam, cd, ob, os.path.join(RENDER_DIR, "tex_%s_after.png" % name))
        shot(cam, cd, ob, os.path.join(RENDER_DIR, "tex_%s_back.png" % name), yaw=152.0)

    # ── 4) 내보내기 ─────────────────────────────────────────
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
    print("  -> %s  %.3f MB  (텍스처 %d JPEG q%d)" % (dst, mb, TEX_SIZE, TEX_QUALITY))
    REPORT.append(dict(name=name, tri0=tri0, tri1=tri1, src_mb=src_mb, mb=mb,
                       fx=fx, fy=fy, fz=fz, ymin=ymin, ymax=ymax,
                       cuts=len(cuts_done), tgt=ginfo["target"],
                       sat0=ginfo["sat0"], sat1=ginfo["sat1"]))

print("\n" + "=" * 92)
print("%-11s %8s %8s %7s %8s  %-7s %6s  %s"
      % ("종류", "원본tri", "결과tri", "컷", "결과MB", "목표색", "채도", "반너비x / y / 높이"))
for r in REPORT:
    print("%-11s %8d %8d %7d %8.3f  #%-6s %.2f→%.2f  %.2f / %.2f / %.2f"
          % (r["name"], r["tri0"], r["tri1"], r["cuts"], r["mb"], r["tgt"],
             r["sat0"], r["sat1"], r["fx"], r["fy"], r["fz"]))
print("합계 결과 %.3f MB" % sum(r["mb"] for r in REPORT))
print("DONE")
