# -*- coding: utf-8 -*-
"""1번 칼(녹슨 칼)을 오너가 준 incoming/new_sword.glb 로 갈아끼운다.

    blender -b -P blender/s34_sword1_swap.py
    -> web/basic2.glb   (SW_nokseun 메시만 교체. 2~7번 칼·몸·옷·클립 7종은 그대로)

전체 공정 여섯 줄(1~4 는 s31_basic2_body.py 헤더, 5 는 s33_basic2_cloth.py 헤더에
그대로 있다. 이 스크립트가 **6번**이다. 순서를 지켜야 재현된다)

    # 1) 알몸 basic2 + kensa 칼 7자루      blender -b -P blender/s31_basic2_body.py
    # 2) slayer 무브셋 7종 이식            blender -b -P blender/s24_moveset.py  (환경변수는 s31 헤더)
    # 3) 걷기·달리기 네이티브 교체          blender -b -P blender/s27_kensa_native.py
    # 4) 이름의 .001 떼기                  python3 tools/glb_rename.py web/basic2.glb
    # 5) 옷 입히기                         blender -b -P blender/s33_basic2_cloth.py
    # 6) 1번 칼 교체(이 파일)
    OUTDIR=renders/history/v98_wave12/sword1 blender -b -P blender/s34_sword1_swap.py

★왜 "메시만 바꾸기" 가 아니라 재구성인가
  게임(web/main.js)이 칼에 거는 계약이 둘이다.
    (1) 메시 이름 SW_<키>          equipSword 가 이 이름으로 자루를 찾는다. 없으면
                                   early-return 이라 원소·발광·궤적이 통째로 죽는다.
                                   키 계산(캐릭터 정규화)에서도 SW_ 를 뺀다.
    (2) 재질 이름 앞자리            bd_/bv_ = 칼날(발광 셰이더) · ht_ = 어두운 결 ·
                                   sp_ = 밝은 심. setupGlow 가 이 접두어로 부위를 가른다
                                   (bd_ 를 못 찾으면 발광이 통째로 스킵된다).
  받은 new_sword.glb 는 메시 하나 + 재질 하나(PBR 3장)라 둘 다 없다. 그래서
  **구 녹슨칼(카타나)의 슬롯 구조를 상속해** 부위별로 재질을 다시 나눠 붙인다.
  1번 칼은 el='plain' 이라 지금은 GLOW 항목이 없어 발광이 안 걸리지만, 계약을
  지켜 둬야 나중에 1번에 원소를 주는 순간 그냥 켜진다.

★정합은 **손목 원점 기준**이다 (11차 함정)
  게임의 measureBlade 는 손 본 로컬에서 **원점에서 가장 먼 정점**을 칼끝으로 잡고
  그 방향을 궤적·리치의 축으로 쓴다. 그래서 맞춰야 하는 것은 자루축이 아니라
  "손목 원점 -> 칼끝" 벡터다. 실측으로 이 둘은 이 리그에서 5.39도 어긋나 있다
  (구 녹슨칼: 자루축 [-0.2517,0.2538,-0.9339] vs 칼끝방향 [-0.1620,0.2789,-0.9466]).
  자루 중심으로 맞추면 딱 그만큼 밀린다.
  여기서는 구 칼의 (칼날뿌리 -> 칼끝) 두 점에 새 칼의 같은 두 점을 **정확히** 얹는
  상사변환을 풀고, 변환 뒤 실제로 가장 먼 정점이 칼끝이 아니면 그 정점을 새 기준으로
  삼아 다시 푼다(반복 조임). 그러면 방향각 오차와 리치(pmax)가 동시에 0 으로 간다.

★★2026-08-12 오너 지시: "칼 크기 좀 키워, 손잡이에 손 오게 하고. 거의 1.5배."
  그래서 정합이 **두 판**이 됐다. [4] 는 예전 그대로(구 카타나 자리에 얹는다)를 풀고,
  [4b] 가 그 결과를 다시 옮긴다. 두 판으로 나눈 이유는 [4] 가 만들어 주는 **칼날 평면
  (roll)** 이 그대로 필요하기 때문이다 — 자루로 다시 앉힐 때 축은 3도쯤 돌지만 roll 은
  안 건드려야 한다.

  [4b] 가 푸는 것 (SCALE_K / GRIP_T)
    (1) 크기를 SCALE_K 배 한다(정점에 굳힌다. 오브젝트 스케일은 계속 1).
    (2) **자루(gr_ 구간)의 한 점을 주먹 중심에 앉힌다.** 여기가 오너가 말한 곳이다.
        받은 칼은 자루가 짧아(전체의 6.2%) 예전 정합에서는 주먹이 자루보다 **13.65단위
        = 16.6cm 칼끝 쪽**에 있었다. 즉 손이 자루가 아니라 **코등이를 쥐고** 있었고
        자루·자루끝은 주먹 아래에 통째로 떠 있었다(probe 로 실측한 값이다).
    (3) 그러면서 **손목원점->칼끝 방향(dir)은 그대로 둔다.** 이게 궤적·판정의 축이라
        여기가 돌면 12차에서 맞춰 둔 것이 전부 어긋난다. 그래서 칼끝을 U_O 반직선 위의
        어디에 놓을지(P)를 **풀어서** 정한다:
            |U_O*P - FC| = L1     (L1 = 자루앵커~칼끝 거리 x SCALE_K)
            P = FC·U_O + sqrt((FC·U_O)^2 - |FC|^2 + L1^2)
        회전은 (자루앵커->칼끝) 을 (FC->U_O*P) 로 보내는 **최소회전**이라 roll 이 안 샌다.

★길이(리치)는 SCALE_K 를 주면 **커진다**. 그게 이번 지시다
  bladeA = dir*pmax*0.18(코등이) / bladeB = dir*pmax*0.98(칼끝) 이 그대로 히트 세그먼트와
  궤적 발원점이다. SCALE_K=1 · GRIP_T<0 이면 칼끝을 구 칼과 **같은 자리**에 얹으므로
  pmax 가 소수점까지 같다(2026-08-11 판. md5 a6461e89025a3791930888782d55f08a).
  SCALE_K=1.5 · GRIP_T=0.5 면 칼이 1.5배가 되는 동시에 자루가 주먹까지 올라오므로
  pmax 는 73.87 -> 132 쯤으로 **1.79배**가 된다(칼이 1.5배 + 손이 자루끝 쪽으로 내려감).
  궤적은 dir·pmax 를 그대로 따라가니 저절로 커진 칼끝에서 발원한다.
  일부러 길이만 바꾸고 싶으면 LEN_K 를 준다([4] 판에서 먹는다).

★함정 (하나라도 밟으면 조용히 망가진다)
  1) fps: 임포트 **전에** 30 고정
  2) 임포트 순서: **몸(basic2)을 먼저**. 나중에 읽으면 char1 이 char1.001 이 되어
     그대로 내보내진다
  3) 스키닝·측정은 REST 에서. 포즈 상태로 재면 애니에서 어긋난다
  4) Icosphere: glTF 임포터가 뼈 표시용으로 만드는 반지름 1 구. 안 지우면 게임이
     전 메시로 박스를 재므로 키가 망가진다(몸 1.4371 이 2.4371 이 된다)
  5) 새 칼 오브젝트의 scale 채널은 1 이어야 한다. 배율은 **정점에 굳혀** 넣는다
     (probe_glbscale.py 가 보는 것은 액션의 scale 채널이지만, 오브젝트 스케일이
      남아 있으면 다음 공정에서 그대로 새어 나간다)
  6) 액션에 use_fake_user 를 안 켜면 export 에서 조용히 빠진다
  7) 게임은 재질을 MeshToonMaterial({map}) 로 갈아끼운다. normal/metallic-roughness 는
     아예 안 읽으므로 링크를 끊어 파일에서 뺀다(원본 8.4MB 중 4.4MB 가 그 둘이다)
  8) ★Blender 는 assert 로 죽어도 종료코드가 0 이다. 성공 판정은 로그의
     "EXPORTED" 줄로 해라

손잡이(환경변수)
  BODY_GLB   몸            기본 web/basic2.glb  (칼 7자루 + 클립 7종이 있어야 한다)
  SWORD_GLB  새 칼         기본 incoming/new_sword.glb
  OUT_GLB    결과          기본 web/basic2.glb  (임시파일에 쓰고 os.replace)
  SLOT       바꿀 칼 키     기본 nokseun (1번)
  LEN_K      칼끝 거리 배율 기본 1.0 (구 칼과 같은 리치. [4] 판에서 먹는다)
  SCALE_K    칼 전체 배율   기본 1.5 (오너 지시. 1.0 이면 2026-08-11 판 그대로)
  GRIP_T     주먹이 자루의 어디를 쥐나  기본 0.5
             0=자루의 코등이쪽 끝 · 0.5=자루 한가운데 · 1=자루끝쪽.
             **음수면 [4b] 를 통째로 끈다**(자루 재정렬도 확대도 안 한다)
  ROLL       칼날 평면 추가 회전(도)  기본 0
  ROLL_FLIP  칼날 평면 180도 뒤집기   기본 0
  SW_TEX     칼 텍스처 최대 변  기본 1024 (게임 거리에서 2048 과 구분 불가)
  CUT_GUARD / CUT_GRIP / CUT_POMMEL  부위 자르는 자리(칼끝 0 ~ 자루끝 1)
             기본 0.700 / 0.838 / 0.900 (단면 실측)
  FLAT_N     칼날에서 넓은 판(bd_)으로 볼 법선 문턱  기본 0.70
  TEX_SIZE / TEX_FORMAT / TEX_QUALITY  몸·옷 텍스처 기본 2048 / AUTO / 90
  RENDER     1(기본) 검산 렌더 / 0 생략
  OUTDIR     렌더 폴더  기본 renders/history/v98_wave12/sword1
"""
import bpy
import bmesh
import os
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")
INC = os.path.join(ROOT, "incoming")


def _p(v):
    """상대경로로 줘도 프로젝트 루트 기준으로 읽히게 한다(blender 의 cwd 를 안 믿는다)."""
    if not v:
        return None
    return v if os.path.isabs(v) else os.path.join(ROOT, v)


BODY_GLB = _p(os.environ.get("BODY_GLB")) or os.path.join(WEB, "basic2.glb")
SWORD_GLB = _p(os.environ.get("SWORD_GLB")) or os.path.join(INC, "new_sword.glb")
OUT_GLB = _p(os.environ.get("OUT_GLB")) or os.path.join(WEB, "basic2.glb")
SLOT = os.environ.get("SLOT", "nokseun")
LEN_K = float(os.environ.get("LEN_K", "1.0"))
SCALE_K = float(os.environ.get("SCALE_K", "1.5"))
GRIP_T = float(os.environ.get("GRIP_T", "0.5"))
ROLL = math.radians(float(os.environ.get("ROLL", "0")))
ROLL_FLIP = os.environ.get("ROLL_FLIP", "0") == "1"
SW_TEX = int(os.environ.get("SW_TEX", "1024"))
TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_FORMAT = os.environ.get("TEX_FORMAT", "AUTO").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))
RENDER = os.environ.get("RENDER", "1") == "1"
OUTDIR = _p(os.environ.get("OUTDIR")) or os.path.join(
    ROOT, "renders", "history", "v98_wave12", "sword1")

HAND = "Bip001 R Hand"
SW_NAME = "SW_" + SLOT
# 새 칼을 주축(칼끝 0 ~ 자루끝 1)으로 자르는 자리. 단면 실측으로 정한 값이다.
#   0.700 에서 정점이 70->180 개로 뛰고 두께가 0.032->0.047 로 붇는다(코등이 시작)
#   0.838 에서 폭이 0.116->0.030 으로 꺼진다(자루 시작)
#   0.900 부터 다시 벌어진다(자루끝 장식)
CUT_GUARD = float(os.environ.get("CUT_GUARD", "0.700"))
CUT_GRIP = float(os.environ.get("CUT_GRIP", "0.838"))
CUT_POMMEL = float(os.environ.get("CUT_POMMEL", "0.900"))
# 칼날에서 넓은 판(bd_)과 가장자리 베벨·날(bv_)을 가르는 법선 문턱
FLAT_N = float(os.environ.get("FLAT_N", "0.70"))

print("=" * 78)
print("[설정] 몸   %s" % BODY_GLB)
print("       새 칼 %s" % SWORD_GLB)
print("       슬롯  %s   결과 %s" % (SW_NAME, OUT_GLB))

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30                                    # ★함정 1
sc.render.fps_base = 1.0


def drop_junk():
    """glTF 임포터가 뼈를 그리려고 만드는 Icosphere(★함정 4)."""
    for o in list(bpy.data.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)


def imp(path):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    drop_junk()
    return [o for o in sc.objects if o.name not in before]


def use(act):
    """액션을 물린다. ★블렌더 4.4+ 는 액션에 슬롯이 있어 안 물리면 포즈가 안 움직인다."""
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def pca(pts):
    """점구름 주축 3개(길이·폭·두께 순)와 중심."""
    n = len(pts)
    cen = Vector((0, 0, 0))
    for p in pts:
        cen += p
    cen /= n
    c = [[0.0] * 3 for _ in range(3)]
    for p in pts:
        d = p - cen
        for r in range(3):
            for q in range(3):
                c[r][q] += d[r] * d[q]
    M = Matrix(c)
    ax = []
    for _ in range(3):
        v = Vector((0.53, 0.31, 0.79)).normalized()
        for _k in range(90):                          # 거듭제곱법
            v = M @ v
            if v.length < 1e-14:
                break
            v.normalize()
        for a in ax:                                  # 이미 뽑은 축과 직교화
            v -= a * (v @ a)
        if v.length < 1e-9:
            v = Vector((1, 0, 0))
            for a in ax:
                v -= a * (v @ a)
        v.normalize()
        ax.append(v)
        lam = (M @ v) @ v
        M = M - Matrix([[lam * v[r] * v[q] for q in range(3)] for r in range(3)])
    return cen, ax


def frame(e0, e1):
    """e0(길이) 를 축으로 e1(폭) 을 직교화한 오른손 좌표계 3x3."""
    e0 = e0.normalized()
    e1 = (e1 - e0 * (e1 @ e0)).normalized()
    e2 = e0.cross(e1)
    return Matrix([[e0.x, e1.x, e2.x], [e0.y, e1.y, e2.y], [e0.z, e1.z, e2.z]])


# ================================================================ 1) 몸
print("=" * 78)
print("[1] 몸")
objs = imp(BODY_GLB)                                  # ★함정 2: 몸을 먼저
arm = next(o for o in objs if o.type == "ARMATURE")
meshes = [o for o in objs if o.type == "MESH"]
swords = [o for o in meshes if o.name.startswith("SW_")]
body = max((o for o in meshes if not o.name.startswith(("SW_", "SH_"))),
           key=lambda o: len(o.data.vertices))
for a in bpy.data.actions:
    a.use_fake_user = True                            # ★함정 6
print("  아마추어 %s 뼈 %d / 몸 %s / 메시 %s"
      % (arm.name, len(arm.data.bones), body.name,
         sorted(o.name for o in meshes)))
print("  액션 %d개 %s (씬 fps %d)"
      % (len(bpy.data.actions), sorted(a.name for a in bpy.data.actions), sc.render.fps))
assert len(swords) == 7, "칼이 7자루가 아니다(%d). s31~s33 산출물이 맞나" % len(swords)
old = bpy.data.objects.get(SW_NAME)
assert old is not None, "%s 가 없다" % SW_NAME
old_mats = [m.name for m in old.data.materials]
old_tri = sum(len(p.vertices) - 2 for p in old.data.polygons)
print("  구 %s  삼각형 %d  재질 %s" % (SW_NAME, old_tri, old_mats))
# ★결과물을 다시 넣으면 이미 바뀐 칼 위에 또 얹는다. 카타나 서명(ht_ 슬롯)을 본다.
assert any(m.startswith("ht_") for m in old_mats), (
    "%s 가 이미 교체된 것 같다(ht_ 슬롯이 없다). BODY_GLB 는 s33 까지 돈 "
    "**카타나 그대로**인 basic2 여야 한다" % SW_NAME)

arm.data.pose_position = "REST"                       # ★함정 3
bpy.context.view_layer.update()
HM = arm.matrix_world @ arm.data.bones[HAND].matrix_local   # 손뼈 레스트 월드행렬
HMI = HM.inverted()
A2W = arm.matrix_world
print("  아마추어 스케일 %.4f (뼈 로컬 1 = %.2fcm)"
      % (A2W.to_scale().x, A2W.to_scale().x * 100))

# ================================================================ 2) 구 칼 실측
print("=" * 78)
print("[2] 구 %s 실측 (손목 로컬)" % SW_NAME)


def hand_local(ob):
    return [HMI @ (ob.matrix_world @ v.co) for v in ob.data.vertices]


OL = hand_local(old)
# 재질 슬롯별 정점 모음(면 -> 정점)
slot_v = {i: set() for i in range(len(old.data.materials))}
for p in old.data.polygons:
    for vi in p.vertices:
        slot_v[p.material_index].add(vi)
mat_pts = {old.data.materials[i].name: [OL[k] for k in sorted(s)]
           for i, s in slot_v.items() if s}

TIP_O = max(OL, key=lambda p: p.length_squared)
PMAX_O = TIP_O.length
U_O = TIP_O.normalized()
print("  칼끝 %s   pmax %.5f" % (tuple(round(x, 5) for x in TIP_O), PMAX_O))
print("  칼끝방향 %s" % (tuple(round(x, 6) for x in U_O),))

bd_name = next(n for n in mat_pts if n.startswith("bd_"))
BD = mat_pts[bd_name]
t_bd = [p @ U_O for p in BD]
t0 = min(t_bd)
rootpts = [p for p, t in zip(BD, t_bd) if t < t0 + 2.0]
ROOT_O = Vector((0, 0, 0))
for p in rootpts:
    ROOT_O += p
ROOT_O /= len(rootpts)
print("  칼날뿌리 %s (축 위 %.3f, 정점 %d)"
      % (tuple(round(x, 4) for x in ROOT_O), ROOT_O @ U_O, len(rootpts)))
print("  칼날 길이(뿌리~끝) %.3f  = 게임 %.4f m"
      % ((TIP_O - ROOT_O).length,
         (TIP_O - ROOT_O).length * A2W.to_scale().x * 1.75 / 1.4371))

_, bax = pca(BD)
E0_O = (TIP_O - ROOT_O).normalized()
W_O = (bax[1] - E0_O * (bax[1] @ E0_O)).normalized()      # 칼날 폭 방향(=베는 평면)
print("  칼날 폭축 %s" % (tuple(round(x, 5) for x in W_O),))

# 자루축(구 칼) - 나중에 새 칼이 얼마나 돌아 앉는지 재는 기준
gpts = []
for n, ps in mat_pts.items():
    if n.startswith(("gr_", "ft_")):
        gpts += [p for p in ps if p @ U_O < 3.0]
gcen, gax = pca(gpts)
GA_O = gax[0] if gax[0] @ U_O > 0 else -gax[0]
print("  자루축 %s   칼끝방향과 %.3f도"
      % (tuple(round(x, 5) for x in GA_O), math.degrees(math.acos(max(-1, min(1, GA_O @ U_O))))))

# 주먹 중심(몸 정점 중 손뼈 웨이트 > 0.5)
hg = body.vertex_groups[HAND].index
fist = []
for v in body.data.vertices:
    for gel in v.groups:
        if gel.group == hg and gel.weight > 0.5:
            fist.append(HMI @ (body.matrix_world @ v.co))
            break
FC = Vector((0, 0, 0))
for p in fist:
    FC += p
FC /= len(fist)
d = FC - gcen
print("  주먹 정점 %d  중심 %s  -> 구 자루축까지 %.3f"
      % (len(fist), tuple(round(x, 3) for x in FC), (d - GA_O * (d @ GA_O)).length))

# ================================================================ 3) 새 칼 실측
print("=" * 78)
print("[3] 새 칼 실측")
nobjs = imp(SWORD_GLB)
new = max((o for o in nobjs if o.type == "MESH"), key=lambda o: len(o.data.vertices))
bpy.context.view_layer.update()
# ★부모를 지우기 전에 정점을 월드로 굳힌다. 지운 뒤에는 matrix_world 가 변한다
new.data.transform(new.matrix_world)
new.parent = None
new.matrix_world = Matrix.Identity(4)
for o in nobjs:
    if o is not new:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()
NV = [v.co.copy() for v in new.data.vertices]
new_tri = sum(len(p.vertices) - 2 for p in new.data.polygons)
print("  %s  정점 %d  삼각형 %d  재질 %s"
      % (new.name, len(NV), new_tri, [m.name for m in new.data.materials]))
assert new_tri < 12000, "폴리가 너무 많다(%d). 칼답게 줄여라" % new_tri

ncen, nax = pca(NV)
AX = nax[0]
tn = [(p - ncen) @ AX for p in NV]
if abs(min(tn)) < abs(max(tn)):                       # 칼끝이 t 최소가 되게
    AX = -AX
    tn = [-x for x in tn]
TMIN, TMAX = min(tn), max(tn)
SPAN = TMAX - TMIN
TT = [(x - TMIN) / SPAN for x in tn]                  # 0=칼끝 1=자루끝
print("  주축 %s  길이 %.4f" % (tuple(round(x, 5) for x in AX), SPAN))
seg = [sum(1 for x in TT if a <= x < b) for a, b in
       ((0, CUT_GUARD), (CUT_GUARD, CUT_GRIP), (CUT_GRIP, CUT_POMMEL), (CUT_POMMEL, 1.01))]
print("  구간 정점  칼날 %d / 코등이 %d / 자루 %d / 자루끝 %d" % tuple(seg))
assert all(s > 20 for s in seg), "구간 자르기가 틀렸다 %s" % seg

# 새 칼의 칼날뿌리 = 코등이 바로 위 단면 중심
band = [p for p, x in zip(NV, TT) if CUT_GUARD - 0.045 <= x < CUT_GUARD]
ROOT_N = Vector((0, 0, 0))
for p in band:
    ROOT_N += p
ROOT_N /= len(band)
BLADE_N = [p for p, x in zip(NV, TT) if x < CUT_GUARD]
_, nbax = pca(BLADE_N)
W_N = nbax[1]
print("  칼날뿌리 %s (단면 정점 %d)" % (tuple(round(x, 5) for x in ROOT_N), len(band)))
print("  칼날 폭축 %s" % (tuple(round(x, 5) for x in W_N),))

# ================================================================ 4) 상사변환 + 반복 조임
print("=" * 78)
print("[4] 정합 (손목 원점 기준 반복 조임)")
TIP_TGT = U_O * (PMAX_O * LEN_K)                      # 칼끝이 앉을 자리
F_O = frame(TIP_TGT - ROOT_O, W_O)                    # 목표 좌표계
tip_src = min(zip(NV, tn), key=lambda z: z[1])[0]     # 새 칼 칼끝 후보


def fit(tip_src):
    """(ROOT_N -> ROOT_O, tip_src -> TIP_TGT) 를 정확히 얹는 상사변환."""
    w = W_N
    if ROLL_FLIP:
        w = -w
    F_N = frame(tip_src - ROOT_N, w)
    R = F_O @ F_N.transposed()
    if abs(ROLL) > 1e-12:
        ax = (TIP_TGT - ROOT_O).normalized()
        R = Matrix.Rotation(ROLL, 3, ax) @ R
    s = (TIP_TGT - ROOT_O).length / (tip_src - ROOT_N).length
    return R, s


hist = []
for it in range(12):
    R, s = fit(tip_src)
    L = [ROOT_O + (R @ (p - ROOT_N)) * s for p in NV]
    far = max(L, key=lambda p: p.length_squared)
    ang = math.degrees(math.acos(max(-1, min(1, far.normalized() @ U_O))))
    hist.append((it, far.length, ang))
    print("   조임 %d  pmax %.6f  칼끝방향 오차 %.6f도" % (it, far.length, ang))
    if ang < 1e-4:
        break
    tip_src = NV[L.index(far)]
R, S = fit(tip_src)
NL = [ROOT_O + (R @ (p - ROOT_N)) * S for p in NV]     # 손목 로컬 최종 좌표
far = max(NL, key=lambda p: p.length_squared)
PMAX_N = far.length
ANG = math.degrees(math.acos(max(-1, min(1, far.normalized() @ U_O))))
srt = sorted(NL, key=lambda p: -p.length_squared)[:5]
print("  배율 %.4f  (새 칼 원본 1 = 손목로컬 %.4f)" % (S, S))
print("  pmax  구 %.5f -> 새 %.5f  (차 %.6f, %.4f%%)"
      % (PMAX_O, PMAX_N, PMAX_N - PMAX_O, 100.0 * (PMAX_N - PMAX_O) / PMAX_O))
print("  칼끝방향 오차 %.6f도  (목표 0.02 이내)" % ANG)
print("  가장 먼 정점 5개 길이 %s"
      % [round(p.length, 5) for p in srt])
print("  그 5개의 방향 벌어짐 %s도"
      % [round(math.degrees(math.acos(max(-1, min(1, p.normalized() @ U_O)))), 4) for p in srt])
assert ANG < 0.02, "칼끝방향이 %.4f도 어긋났다" % ANG
assert abs(PMAX_N - PMAX_O * LEN_K) < 1e-3, "리치가 틀어졌다"

# ================================================ 4b) 확대 + 자루 파지 재정렬
# 오너 지시("칼 1.5배 · 손잡이에 손 오게"). 위 [4] 는 손대지 않았다 — 저기서 나온
# roll(칼날 평면)을 그대로 쓰려고 두 판으로 나눈 것이다. 여기서 하는 일은 딱 둘:
#   · 크기 x SCALE_K
#   · **자루(gr_) 위의 한 점**을 주먹 중심 FC 로 옮긴다
# 그러면서 손목원점->칼끝 방향(U_O)은 건드리지 않는다. 그래서 칼끝을 U_O 반직선
# 위 어디에 놓을지는 고르는 게 아니라 **푸는 것**이다(헤더 ★★ 절 공식).


def rot_between(a, b):
    """a 를 b 로 보내는 최소회전. 축 밖으로 도는 성분이 없어 roll 이 안 샌다."""
    a = a.normalized()
    b = b.normalized()
    c = a.cross(b)
    d = max(-1.0, min(1.0, a @ b))
    if c.length < 1e-12:                              # 같은 방향(또는 정반대)
        return Matrix.Identity(3) if d > 0 else Matrix.Rotation(math.pi, 3, a.orthogonal())
    return Matrix.Rotation(math.acos(d), 3, c.normalized())


def axial(pts, ax):
    t = [p @ ax for p in pts]
    return min(t), max(t)


if GRIP_T >= 0.0:
    print("=" * 78)
    print("[4b] 확대 x%.3f + 자루 파지 재정렬 (GRIP_T %.2f)" % (SCALE_K, GRIP_T))
    # 자루 정점 = **면 기준**으로 고른다([6] 의 gr_ 배분과 글자 그대로 같은 식이라
    # "빨간색으로 칠해지는 곳" 과 앵커가 어긋나지 않는다)
    GSET = set()
    for poly in new.data.polygons:
        x = sum(TT[vi] for vi in poly.vertices) / len(poly.vertices)
        if CUT_GRIP <= x < CUT_POMMEL:
            GSET.update(poly.vertices)
    assert len(GSET) > 30, "자루 정점이 너무 적다(%d)" % len(GSET)
    AXW = (R @ (-AX)).normalized()                    # 칼 제 몸의 긴 축(칼끝 쪽 +)
    GP = [NL[i] for i in sorted(GSET)]
    CG = Vector((0, 0, 0))
    for p in GP:
        CG += p
    CG /= len(GP)
    g0, g1 = axial(GP, AXW)                           # 자루의 축 범위(제 몸 축 기준)
    # GRIP_T 0=코등이쪽 끝(g1) · 1=자루끝쪽(g0)
    ANCHOR = CG + AXW * ((g1 - GRIP_T * (g1 - g0)) - CG @ AXW)
    print("  자루 정점 %d  중심 %s  축범위 %.3f..%.3f  앵커 %s"
          % (len(GP), tuple(round(x, 3) for x in CG), g0, g1,
             tuple(round(x, 3) for x in ANCHOR)))
    print("  주먹중심 FC %s  (손목원점에서 %.3f)"
          % (tuple(round(x, 3) for x in FC), FC.length))

    # ★반복 조임. [4] 와 같은 뜻인데 **칼끝 후보를 한 정점으로 잡으면 안 된다.**
    #   [4] 는 0.000000도까지 갔지만 그건 그 배치에서 최원점이 **같은 자리에 겹친
    #   이음매 복제 정점 두 개**였기 때문이다. 1.78배로 다시 앉히면 최원점이 칼끝
    #   좌우로 갈린 **다른 두 정점**(2060/2063, 0.0385단위 떨어져 있다)으로 바뀐다.
    #   이 둘은 칼 중심선에 대해 대칭이라 **어떤 강체 배치로도 둘을 동시에 U_O 위에
    #   못 올린다** — 0.0168도가 이 메시의 바닥이다(반지름 131.5에서 0.5mm).
    #   한 정점만 앵커로 쓰면 매 회차 둘이 자리를 바꿔 12회를 다 돌고도 안 멈춘다.
    #   그래서 **동률 칼끝들의 무게중심**을 앵커로 쓴다. 그 자리가 고정점이라 두 번에
    #   멈추고, 남는 0.0168도는 계약(0.02도)을 지킨다.
    FCU = FC @ U_O
    FC2 = FC.length_squared
    A = NL[NL.index(far)]                             # [4] 가 찾아 놓은 칼끝에서 출발
    NL2, prev = NL, None
    for it in range(16):
        d0 = A - ANCHOR                               # 앵커 -> 칼끝 (재정렬 전)
        L1 = d0.length * SCALE_K                      # 재정렬 뒤 앵커 -> 칼끝
        disc = FCU * FCU - FC2 + L1 * L1
        assert disc > 0, "칼끝을 U_O 위에 놓을 수 없다(자루가 너무 짧다)"
        P = FCU + math.sqrt(disc)
        R2 = rot_between(d0, U_O * P - FC)
        NL2 = [FC + (R2 @ (p - ANCHOR)) * SCALE_K for p in NL]
        m2 = max(p.length_squared for p in NL2)
        tie = [i for i, p in enumerate(NL2) if p.length_squared > m2 * (1 - 2e-5)]
        a2 = max(math.degrees(math.acos(max(-1, min(1, NL2[i].normalized() @ U_O))))
                 for i in tie)
        print("   조임 %d  pmax %.5f  칼끝방향 오차 %.6f도  (축 %.3f도 · 동률 칼끝 %d개)"
              % (it, math.sqrt(m2), a2,
                 math.degrees(math.acos(max(-1, min(1, d0.normalized()
                                                    @ (U_O * P - FC).normalized())))),
                 len(tie)))
        if a2 < 1e-4 or (prev is not None and abs(prev - a2) < 1e-9):
            break
        prev = a2
        A = Vector((0, 0, 0))
        for i in tie:
            A += NL[i]
        A /= len(tie)
    NL = NL2
    S = S * SCALE_K
    far = max(NL, key=lambda p: p.length_squared)
    PMAX_N = far.length
    ANG = math.degrees(math.acos(max(-1, min(1, far.normalized() @ U_O))))
    print("  pmax  %.5f -> %.5f  (x%.4f)   칼끝방향 오차 %.6f도"
          % (PMAX_O, PMAX_N, PMAX_N / PMAX_O, ANG))
    print("  게임 좌표 손목~칼끝  %.4f m -> %.4f m"
          % (PMAX_O * A2W.to_scale().x * 1.75 / 1.4371,
             PMAX_N * A2W.to_scale().x * 1.75 / 1.4371))
    assert ANG < 0.02, "칼끝방향이 %.4f도 어긋났다" % ANG

    # ---- 파지 검산: 자루가 주먹 안에 들어왔나 (오너 지시의 합격선) ----
    CMU = A2W.to_scale().x * 1.75 / 1.4371 * 100.0    # 1단위 -> 게임 cm
    GP2 = [NL[i] for i in sorted(GSET)]
    ga, gb = axial(GP2, U_O)
    fa, fb = axial(fist, U_O)
    ov = max(0.0, min(gb, fb) - max(ga, fa))
    print("  [파지] 주먹 축 %7.2f..%7.2f (폭 %.1fcm) / 자루 축 %7.2f..%7.2f (길이 %.1fcm)"
          % (fa, fb, (fb - fa) * CMU, ga, gb, (gb - ga) * CMU))
    print("         겹침 %.2f단위 = 자루의 %.0f%% (주먹의 %.0f%%)"
          % (ov, 100.0 * ov / (gb - ga), 100.0 * ov / (fb - fa)))
    dcen = ((ga + gb) * 0.5 - (fa + fb) * 0.5) * CMU
    print("         자루중심 - 주먹중심 = %+.1fcm (0 에 가까울수록 한가운데를 쥔다)" % dcen)
    assert ov > 0.6 * (gb - ga), "주먹이 자루를 %.0f%% 밖에 안 덮는다" % (100 * ov / (gb - ga))

# 새 자루축이 주먹을 지나는지
gn = [p for p, x in zip(NL, TT) if x >= CUT_GRIP]
gncen, gnax = pca(gn)
GA_N = gnax[0] if gnax[0] @ U_O > 0 else -gnax[0]
d = FC - gncen
GRIP_D = (d - GA_N * (d @ GA_N)).length
print("  새 자루축 %s  구 자루축과 %.3f도"
      % (tuple(round(x, 5) for x in GA_N),
         math.degrees(math.acos(max(-1, min(1, GA_N @ GA_O))))))
print("  주먹 중심 -> 새 자루축 거리 %.3f (구 칼 0.544, 주먹 폭 약 17)" % GRIP_D)
assert GRIP_D < 5.0, "자루가 주먹을 안 지난다(%.3f)" % GRIP_D
tt = [p @ U_O for p in NL]
print("  손목 로컬 축범위 %.2f .. %.2f (구 칼 -30.59 .. 73.87)" % (min(tt), max(tt)))

# ================================================================ 5) 이식 + 스키닝
print("=" * 78)
print("[5] 이식 · 스키닝")
BL = arm.data.bones[HAND].matrix_local
for v, p in zip(new.data.vertices, NL):
    v.co = BL @ p                                     # 손뼈로컬 -> 아마추어 로컬
new.data.update()
# ★함정 5: 배율은 정점에 굳혔다. 오브젝트 스케일은 1 로 둔다.
new.parent = arm
new.matrix_parent_inverse = Matrix.Identity(4)
new.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
assert max(abs(x - 1.0) for x in new.matrix_basis.to_scale()) < 1e-9
vg = new.vertex_groups.new(name=HAND)
vg.add(range(len(new.data.vertices)), 1.0, "REPLACE")
md = new.modifiers.new("Armature", "ARMATURE")
md.object = arm
print("  부모 %s  스케일 %s  웨이트그룹 %s x %d정점"
      % (new.parent.name, tuple(round(x, 6) for x in new.scale), HAND,
         len(new.data.vertices)))
chk = [HMI @ (new.matrix_world @ v.co) for v in new.data.vertices]
err = max((a - b).length for a, b in zip(chk, NL))
print("  이식 오차 %.3e (손목 로컬)" % err)
assert err < 1e-4

# 열린 메시인가(게임은 FrontSide 라 뒷면이 사라진다. LOG v98 옷 사례).
# ★glTF 는 UV·노멀 이음매에서 정점을 쪼갠다. 붙이지 않고 세면 이음매가 전부
#   "경계"로 잡혀 수천 개가 나온다. 사본을 용접해서 센다(원본 UV 는 안 건드린다).
def open_edges(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    n = sum(1 for e in bm.edges if len(e.link_faces) < 2)
    bm.free()
    return n


print("  경계 모서리 새 칼 %d개 / 구 칼 %d개 (용접 후. 0 이면 닫힌 덩어리)"
      % (open_edges(new.data), open_edges(old.data)))

# ================================================================ 6) 재질 계약 재구성
print("=" * 78)
print("[6] 재질 (게임 계약 bd_/bv_/ht_/sp_ 상속)")
img = None
for m in new.data.materials:
    if not m or not m.node_tree:
        continue
    for nd in m.node_tree.nodes:
        if nd.type == "TEX_IMAGE" and nd.image is not None:
            for l in m.node_tree.links:
                # ★bpy_struct 는 접근할 때마다 새 래퍼라 `is` 비교가 항상 거짓이다
                if l.from_node == nd and l.to_socket.name == "Base Color":
                    img = nd.image
assert img is not None, "새 칼에서 베이스컬러 텍스처를 못 찾았다"
print("  베이스컬러 %s %dx%d %s" % (img.name, img.size[0], img.size[1], img.file_format))


def toon_mat(name):
    """게임이 어차피 MeshToonMaterial({map}) 로 갈아끼운다. 베이스컬러 한 장만 문다."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    for k, v in (("Metallic", 0.0), ("Roughness", 0.95), ("Specular IOR Level", 0.2)):
        s = bsdf.inputs.get(k)
        if s is not None:
            s.default_value = v
    s = bsdf.inputs.get("Emission Color")
    if s is not None:
        s.default_value = (0, 0, 0, 1)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return m


# 부위 가르기.
#  · 길이축(TT)으로 칼날 / 코등이 / 자루 / 자루끝 을 자른다(단면 실측으로 정한 문턱)
#  · 칼날 안에서는 **법선**으로 넓은 판(bd_)과 가장자리 베벨·날(bv_)을 가른다.
#    구 카타나도 bd_(몸) 1292 / bv_(밝은 날) 860 으로 같은 뜻의 두 장이었다.
#    ★색으로 가르려다 접었다. Meshy 아틀라스는 삼각형 단위로 조각조각 재배치돼
#      있어서 면 UV 중심 표본이 이웃 섬을 물어 온다(칼날이 통째로 밝은 날이 됐다).
#      법선은 그런 함정이 없고 결과를 s34_08_matsplit.png 로 눈으로 검산할 수 있다.
BLADE_CO = [v.co for v, x in zip(new.data.vertices, TT) if x < CUT_GUARD]
_, bax2 = pca(BLADE_CO)
NRM = bax2[2]                                         # 칼날 두께축(넓은 판의 법선)
print("  칼날 두께축 %s  넓은 판 문턱 |n·축| > %.2f"
      % (tuple(round(x, 4) for x in NRM), FLAT_N))

NAMES = ["bd_" + SLOT, "bv_" + SLOT, "ft_" + SLOT, "gr_" + SLOT]
SLOTIDX = []
for poly in new.data.polygons:
    x = sum(TT[vi] for vi in poly.vertices) / len(poly.vertices)
    if x < CUT_GUARD:                                 # 칼날
        i = 0 if abs(poly.normal @ NRM) > FLAT_N else 1
    elif x < CUT_GRIP:
        i = 2                                         # 코등이(금구)
    elif x < CUT_POMMEL:
        i = 3                                         # 자루(가죽)
    else:
        i = 2                                         # 자루끝(금구)
    SLOTIDX.append(i)

# 표본을 다 뜬 뒤에 축소한다(위 ★ 참조)
if SW_TEX and max(img.size) > SW_TEX:
    k = SW_TEX / float(max(img.size))
    img.scale(max(1, int(round(img.size[0] * k))), max(1, int(round(img.size[1] * k))))
    print("  베이스컬러 -> %dx%d 로 축소 (게임은 베이스컬러만 읽는다)" % img.size[:])
img.name = "sw_" + SLOT

new.data.materials.clear()
for n in NAMES:
    new.data.materials.append(toon_mat(n))
cnt = [0] * 4
for poly, i in zip(new.data.polygons, SLOTIDX):
    poly.material_index = i
    cnt[i] += 1
new.data.update()
print("  면 배분  %s" % dict(zip(NAMES, cnt)))
assert all(c > 0 for c in cnt), "빈 재질 슬롯이 있다 %s" % cnt
print("  재질 %s" % [m.name for m in new.data.materials])

# ================================================================ 7) 교체
print("=" * 78)
print("[7] 교체")
old_name = old.name
old_me = old.data
bpy.data.objects.remove(old, do_unlink=True)
# ★오브젝트만 지우면 메시 데이터가 남아 구 재질을 붙들고 있다. 그러면 아래 이름
#   정리에서 bd_nokseun 이 안 비어 .001 이 안 떨어진다.
bpy.data.meshes.remove(old_me)
for m in list(bpy.data.materials):
    if m.users == 0:
        bpy.data.materials.remove(m)
for i in list(bpy.data.images):
    if i.users == 0:
        bpy.data.images.remove(i)
new.name = old_name
new.data.name = old_name
# ★재질 이름의 .001 떼기. 새 재질을 만들 때 구 칼의 같은 이름이 아직 살아 있어서
#   bd_nokseun.001 로 밀린다. startsWith 규칙은 견디지만 다음 공정이 이 이름을
#   그대로 물려받으므로 여기서 정리한다(메시 이름 .001 을 떼는 것과 같은 이유).
for m, want in zip(new.data.materials, NAMES):
    if m.name != want:
        print("  재질 이름 %s -> %s" % (m.name, want))
        m.name = want
    assert m.name == want, "재질 이름 %s 를 %s 로 못 돌렸다(중복이 남았나)" % (m.name, want)
print("  %s 를 새 칼로 갈았다 (삼각형 %d -> %d)" % (old_name, old_tri, new_tri))
sw_now = sorted(o.name for o in sc.objects if o.name.startswith("SW_"))
print("  칼 %d자루 %s" % (len(sw_now), sw_now))
assert len(sw_now) == 7 and SW_NAME in sw_now

# ================================================================ 8) 검산
print("=" * 78)
print("[8] 검산")
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
for o in sc.objects:
    if o.type != "MESH":
        continue
    sca = o.matrix_basis.to_scale()
    assert max(abs(x - 1.0) for x in sca) < 1e-6, "%s 스케일 오염 %s" % (o.name, sca)
print("  메시 오브젝트 스케일 채널 오염 0개")
dot = [o.name for o in sc.objects if ".00" in o.name]
dot += [m.name for o in sc.objects if o.type == "MESH" for m in o.data.materials
        if ".00" in m.name]
dot += [i.name for i in bpy.data.images if ".00" in i.name]
print("  이름 .001 : %s" % dot)
assert not dot, "이름이 .001 로 밀렸다 %s" % dot
mats = [m.name for m in bpy.data.objects[SW_NAME].data.materials]
print("  %s 재질 %s" % (SW_NAME, mats))
assert any(m.startswith("bd_") for m in mats), "칼날 재질 bd_ 가 없다(발광이 통째로 죽는다)"
# 게임 키 박스(SW_/SH_ 제외)
mn = Vector((1e9,) * 3)
mx = Vector((-1e9,) * 3)
for o in sc.objects:
    if o.type != "MESH" or o.name.startswith(("SW_", "SH_")):
        continue
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
print("  게임 키 박스 %.4f (칼은 빠진다. 1.4371 이어야 한다)" % (mx.z - mn.z))
assert abs((mx.z - mn.z) - 1.4371) < 0.01
# 게임이 다시 재는 것과 같은 식으로 한 번 더
FL = [HMI @ (new.matrix_world @ v.co) for v in new.data.vertices]
f2 = max(FL, key=lambda p: p.length_squared)
print("  최종 pmax %.5f  방향 %s  오차 %.6f도"
      % (f2.length, tuple(round(x, 6) for x in f2.normalized()),
         math.degrees(math.acos(max(-1, min(1, f2.normalized() @ U_O))))))
print("  게임 좌표 환산: 손목~칼끝 %.4f m  (구 칼 %.4f m)"
      % (f2.length * A2W.to_scale().x * 1.75 / 1.4371,
         PMAX_O * A2W.to_scale().x * 1.75 / 1.4371))

# ================================================================ 9) 내보내기
print("=" * 78)
print("[9] 내보내기")
IDLE = bpy.data.actions.get("Idle")
if IDLE:
    use(IDLE)
    sc.frame_set(int(IDLE.frame_range[0]))
arm.data.pose_position = "POSE"
bpy.context.view_layer.update()
for a in bpy.data.actions:
    a.use_fake_user = True                            # ★함정 6
imgs = []
for o in sc.objects:
    if o.type != "MESH":
        continue
    for m in o.data.materials:
        if not m or not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            if getattr(nd, "image", None) is not None and nd.image not in imgs:
                imgs.append(nd.image)
for i in imgs:
    if TEX_SIZE and max(i.size) > TEX_SIZE:
        k = TEX_SIZE / float(max(i.size))
        i.scale(max(1, int(round(i.size[0] * k))), max(1, int(round(i.size[1] * k))))
    print("  이미지 %-14s %dx%d %s" % (i.name, i.size[0], i.size[1], i.file_format))
tri = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons)
       for o in sc.objects if o.type == "MESH"}
print("  삼각형 %s 합계 %d" % (tri, sum(tri.values())))
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
TMP = OUT_GLB + ".tmp.glb"                            # ★원자적 교체
kw = dict(filepath=TMP, export_format="GLB", use_selection=False,
          export_apply=True, export_yup=True,
          export_animations=True, export_animation_mode="ACTIONS",
          export_nla_strips=False, export_bake_animation=True,
          export_frame_range=False)
if TEX_FORMAT not in ("AUTO", ""):
    kw.update(export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
              export_jpeg_quality=TEX_QUALITY)
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.export_scene.gltf(**kw)
os.replace(TMP, OUT_GLB)
sz = os.path.getsize(OUT_GLB)
print("EXPORTED %s  %d bytes (%.2f MB)  칼 %d자루 / 액션 %d개 / %s 삼각형 %d"
      % (OUT_GLB, sz, sz / 1e6, len(sw_now), len(bpy.data.actions), SW_NAME, new_tri))

# ================================================================ 10) 검산 렌더
if not RENDER:
    print("DONE (렌더 생략)")
    raise SystemExit(0)

os.makedirs(OUTDIR, exist_ok=True)
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                    else "BLENDER_EEVEE")
sc.view_settings.view_transform = "Standard"
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
BW = [body.matrix_world @ v.co for v in body.data.vertices]
Hh = max(p.z for p in BW) - min(p.z for p in BW)
FOOT = min(p.z for p in BW)
bpy.ops.mesh.primitive_plane_add(size=Hh * 6, location=(0, 0, FOOT))
cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
for o in sc.objects:                                  # 1번 칼만 보이게
    if o.name.startswith("SW_"):
        o.hide_render = (o.name != SW_NAME)

CEN = Vector((0, 0, FOOT + Hh * 0.55))


def look(eye, tgt):
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()


def handpos():
    bpy.context.view_layer.update()
    return arm.matrix_world @ arm.pose.bones[HAND].head


SHOTS = [
    ("01_front", "Idle", None, (620, 800), "full", (0, -1.9, 0.10)),
    ("02_side", "Idle", None, (620, 800), "full", (-1.9, 0, 0.10)),
    ("03_hand", "Idle", None, (800, 620), "hand", (-0.55, -0.85, 0.25)),
    ("04_hand_b", "Idle", None, (800, 620), "hand", (0.75, -0.7, 0.20)),
    ("05_attack", "Attack", 0.62, (800, 620), "hand", (-0.9, -1.1, 0.30)),
    ("06_heavy", "Heavy", 0.55, (620, 800), "full", (-1.2, -1.5, 0.10)),
    ("07_run", "Run", 0.4, (620, 800), "full", (-1.2, -1.5, 0.10)),
]
for nm, clip, tk, res, mode, off in SHOTS:
    act = bpy.data.actions.get(clip)
    if act is None:
        continue
    use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    sc.frame_set(f0 if tk is None else int(f0 + (f1 - f0) * tk))
    bpy.context.view_layer.update()
    tgt = CEN if mode == "full" else handpos()
    k = Hh if mode == "full" else Hh * 0.62
    look(tgt + Vector(off) * k, tgt)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUTDIR, "s34_%s.png" % nm)
    bpy.ops.render.render(write_still=True)
    print("   렌더 %s" % sc.render.filepath)

# 재질 분할 확인용 거짓색 (bd 회색 / bv 흰 / ft 노랑 / gr 빨강)
dbg = [(0.25, 0.25, 0.28), (0.95, 0.95, 0.95), (0.95, 0.75, 0.10), (0.85, 0.15, 0.10)]
for m, c in zip(new.data.materials, dbg):
    nt = m.node_tree
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (c[0], c[1], c[2], 1)
    nt.links.new(em.outputs["Emission"],
                 [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
use(bpy.data.actions["Idle"])
sc.frame_set(int(bpy.data.actions["Idle"].frame_range[0]))
bpy.context.view_layer.update()
tgt = handpos()
look(tgt + Vector((-0.55, -0.85, 0.25)) * Hh * 0.62, tgt)
sc.render.resolution_x, sc.render.resolution_y = (800, 620)
sc.render.filepath = os.path.join(OUTDIR, "s34_08_matsplit.png")
bpy.ops.render.render(write_still=True)
print("   렌더 %s" % sc.render.filepath)
print("DONE")
