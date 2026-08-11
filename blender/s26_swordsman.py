# -*- coding: utf-8 -*-
"""Meshy 검사(kensa)의 몸을 수술하고 우리 칼 7자루를 오른손에 꿰어 web/kensa_body.glb 를 만든다.

전체 공정 세 줄(이 순서대로 다시 돌리면 언제든 재현된다)

    blender -b -P blender/s26_swordsman.py
    DST_GLB=web/kensa_body.glb OUT_GLB=web/kensa.glb \
      DST_SWORD=SW_baekah.001 GRIP_K=0.64 SWORD_FIT=0 \
      OUTDIR=renders/history/v77_kensa/moveset blender -b -P blender/s24_moveset.py
    python3 tools/glb_rename.py web/kensa.glb

  ★s24 에 넘기는 세 손잡이는 전부 실측에서 나온 값이다. 빼먹으면 조용히 망가진다.
    DST_SWORD=SW_baekah**.001**
        s24 는 소스(slayer.glb)를 먼저 읽는다. 칼 이름이 겹쳐서 우리 칼이 .001 로
        밀린다. 그냥 SW_baekah 라고 주면 **소스 칼을 타깃으로 착각**해 손아래 길이가
        음수로 나오고 왼손 IK 목표가 통째로 헛돈다(1차 시도에서 겪었다).
    GRIP_K=0.64
        왼손목-자루 오프셋은 키가 아니라 **손 크기**로 환산해야 한다. 실측 손 크기가
        소스 0.0853 / kensa 0.0547 (키 정규화) = 0.64. 1.0 으로 두면 왼손이 자루에서
        키의 0.077 (주먹 1.4개)만큼 떠 있다. 0.64 를 주면 0.049 로 붙는다.
    SWORD_FIT=0
        s24 의 검 재장착은 **DST_SWORD 한 자루만** 돌린다. 7자루짜리 캐릭터에서는
        나머지 6자루가 어긋난 채 남는다. 그래서 이 스크립트가 7자루를 전부 소스에
        미리 맞춰 놓고(아래 [칼] 절), s24 는 손대지 않게 끈다. 끈 상태에서도 s24 가
        "레스트 자루축 각도차 0.0 도" 를 찍어 주므로 정합이 맞았는지 로그로 확인된다.
    tools/glb_rename.py
        위의 .001 이 **파일 안 이름에도 남는다**. 게임은 칼 키를 메시 이름에서 뽑으므로
        떼어내지 않으면 1~7 칼 교체가 죽는다. 텍스처를 다시 굽지 않고 JSON 만 고친다.

    blender -b -P blender/s26_swordsman.py
    -> web/kensa_body.glb  (액션 없음. 모션은 s24_moveset.py 가 이어서 이식한다)

받은 것
  incoming/meshy_slayer/..._Character_output.glb
      8,832 삼각 / 조인트 24(Meshy 원명) / 2048 PNG 베이스컬러+emissive / 발 원점 / 키 1.700
      삿갓 쓴 한국식 검사. 삿갓은 **남긴다**(탑다운 시점에서 실루엣이 산다).

★수술 대상 = 어깨 뒤로 가로지르는 막대 무기
  Meshy 가 T포즈 양손에 긴 칼을 가로로 물려 놓고 그걸 **몸 메시에 통째로 융합**했다.
  용접(remove_doubles) 후 아일랜드가 2개뿐(본체 4401정점 + 17정점짜리 장식)이라
  '연결 선택 삭제'가 안 된다. 게다가 용접 후 경계 엣지가 0개, 즉 **닫힌 다양체**다.
  막대 표면이 주먹 표면으로 그대로 이어져 있다는 뜻이다(주먹 속에 따로 막대가
  들어 있는 게 아니다). 그래서 잘라내면 주먹은 **양 끝이 뚫린 통**이 된다.

  실측(월드, 발 원점 z=0):
      막대 축      x 평행, y=+0.0105, z=1.4491   (단면 반폭 y 0.007 / z 0.021)
      주먹         |x| 0.54~0.66 구간에서 축까지 최대 반경 0.05~0.098 로 부푼다
      자루 끝      |x| 0.66~0.73 (주먹 밖으로 나온 손잡이 끝)
  이 세 구간을 자동으로 갈라 **주먹만 남기고 앞뒤 막대를 지운다**.
  선택은 좌표 상자가 아니라 **씨앗 + 엣지 플러드필**이다. 상자만 쓰면 팔뚝 윗면
  (막대와 0.8cm 차이)이나 목 뒤가 같이 딸려 들어간다. 플러드필은 막대 튜브를
  따라서만 번지므로 몸에 안 닿는다.

★잘린 구멍은 메운다
  주먹 양 끝 고리(반지름 2cm 남짓)를 그대로 두면 손 안이 들여다보인다. 정수리
  구멍(s14)처럼 '안 보이면 둔다'가 통하는 자리가 아니다. 고리 중심에 정점 하나를
  세워 부채꼴로 덮고, UV 는 고리 정점 것을 그대로 물려 살색이 이어지게 한다.
  덮고 나면 주먹은 다시 닫힌 덩어리 = **뭔가 쥔 모양의 빈 주먹**이 된다.

★칼 꽂기: 위치는 터널 실측, 방향은 소스(slayer) 정합
  - 위치: 잘라낸 두 고리 중심을 이은 선 = 주먹 터널. 그 중점에 자루 중앙을 놓는다.
  - 방향: **slayer 의 레스트 월드 칼 방향에 그대로 맞춘다.**
    s24 의 SWORD_FIT 이 하는 일이 바로 이건데, s24 는 DST_SWORD **한 자루만**
    돌린다(hero 는 칼이 하나였다). 우리는 7자루라 나머지 6자루가 어긋난 채 남는다.
    그래서 여기서 7자루를 각자 **같은 이름의 소스 칼**에 맞춰 미리 꽂는다.
    맞추는 좌표계는 (칼끝방향 u, 휨방향 b) 다. u 는 s24/main.js measureBlade 와
    같은 절차(손목에서 가장 먼 정점)이고, b 는 칼날 구간의 평균 수직 오프셋이라
    **부호가 분명하다**(고유벡터는 부호가 임의라 180도 뒤집힌 채 수렴할 수 있다).
    u 는 손목 기준인데 회전은 자루 중앙 기준이라 한 번에 안 맞는다. 반복해서 조인다.
  - 터널 축(≈팔 방향 ±X)과 소스 칼 방향은 60도쯤 벌어져 있다. 주먹을 덮어 닫아
    놨으므로 칼이 주먹을 비스듬히 관통해도 '쥔 것'으로 보인다(hero 와 같은 상태).

★함정
  1) 스키닝은 REST 에서 굽는다. 포즈 상태로 재면 애니에서 어긋난다
  2) glTF 는 UV 이음매에서 정점을 쪼갠다. 섬 판정·플러드필 전에 용접할 것
  3) 뼈 이름을 바꿀 때 **정점 그룹 이름도 같이** 바꿔야 스킨이 안 끊긴다
  4) 게임은 오른손 뼈를 /r[_ ]hand/i 로 찾는다. Meshy 원명 RightHand 는 안 걸린다
  5) 게임은 SW_ 로 시작하는 메시를 키 계산에서 뺀다. 칼 이름은 반드시 SW_<키>
  6) 재질의 emissive 에 알베도가 물려 있다(Meshy 기본). 링크를 끊어야 안 나간다
  7) 임포터가 만드는 Icosphere(glTF_not_exported)는 glb 에 없는 물건이다. 지운다

손잡이(환경변수)
  SRC_GLB    칼 방향을 맞출 소스        기본 web/slayer.glb
  OUT_GLB    결과                       기본 web/kensa_body.glb
  MESHY_GLB  원본                       기본 incoming/meshy_slayer/..._Character_output.glb
  CAP        1(기본) 잘린 고리를 덮는다 / 0 뚫린 채로 둔다(비교용)
  PROTECT    1(기본) 머리·목 지배 정점은 절대 안 지운다
  SW_RATIO   칼 배율 = 키 * 이 값        기본 0.235 (s6 와 같다)
  TEX_SIZE/TEX_FORMAT/TEX_QUALITY        기본 2048 / JPEG / 90
  RENDER     1(기본) 전후 비교 렌더
  OUTDIR     렌더 폴더                   기본 renders/history/v77_kensa
"""
import bpy
import bmesh
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
WEB = os.path.join(ROOT, "web")
INC = os.path.join(ROOT, "incoming", "meshy_slayer")
sys.path.insert(0, BLD)

MESHY_GLB = os.environ.get("MESHY_GLB") or os.path.join(
    INC, "Meshy_AI_young_Korean_swordsma_biped_Character_output.glb")
SRC_GLB = os.environ.get("SRC_GLB") or os.path.join(WEB, "slayer.glb")
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "kensa_body.glb")
CAP = os.environ.get("CAP", "1") == "1"
PROTECT = os.environ.get("PROTECT", "1") == "1"
SW_RATIO = float(os.environ.get("SW_RATIO", "0.235"))
TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_FORMAT = os.environ.get("TEX_FORMAT", "JPEG").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))
RENDER = os.environ.get("RENDER", "1") == "1"
OUTDIR = os.environ.get("OUTDIR") or os.path.join(ROOT, "renders", "history",
                                                  "v77_kensa")

# Meshy 원명 -> 우리 규칙(s24 의 RENAME 과 같은 표. 여기서 미리 바꿔 두면
# s24 는 "이미 우리 규칙이다"로 건너뛴다)
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
HAND_R_RAW, HAND_L_RAW = "RightHand", "LeftHand"
HAND_R = "Bip001 R Hand"
# 막대가 물려 있는 뼈. 이 중 하나가 지배 뼈면 지워도 되는 후보다.
ARM_BONES = ("LeftShoulder", "RightShoulder", "LeftArm", "RightArm",
             "LeftForeArm", "RightForeArm", "LeftHand", "RightHand")
HEAD_BONES = ("Head", "neck", "head_end", "headfront")

print("=" * 78)
print("[설정] 원본 %s" % os.path.basename(MESHY_GLB))
print("       소스(칼 방향) %s" % SRC_GLB)
print("       결과 %s" % OUT_GLB)

# ================================================================ 1) 임포트
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0


def drop_junk():
    """glTF 임포터가 뼈를 그리려고 만드는 Icosphere. glb 안엔 없다(★함정 7)."""
    for o in list(bpy.data.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            print("   임포터 잡동사니 제거:", o.name)
            bpy.data.objects.remove(o, do_unlink=True)


bpy.ops.import_scene.gltf(filepath=MESHY_GLB)
drop_junk()
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = max((o for o in sc.objects if o.type == "MESH"),
           key=lambda o: len(o.data.vertices))
for b in arm.pose.bones:                                  # ★함정 1
    b.rotation_mode = "QUATERNION"
    b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
A2W = arm.matrix_world.copy()
print("\n[원본] 아마추어 %s (스케일 %.4f) / 뼈 %d / 메시 %s"
      % (arm.name, A2W.to_scale().x, len(arm.data.bones), body.name))

# 용접(★함정 2)
n0 = len(body.data.vertices)
bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(body.data)
bm.free()
body.data.update()
body.data.calc_loop_triangles()
TRI0 = len(body.data.loop_triangles)
print("       용접 정점 %d -> %d / 삼각 %d" % (n0, len(body.data.vertices), TRI0))

MW = body.matrix_world.copy()
W = [MW @ v.co for v in body.data.vertices]
CHAR_H = max(p.z for p in W) - min(p.z for p in W)
FLOOR = min(p.z for p in W)
print("       키 %.4f (z %.4f~%.4f) / 폭 x %.4f~%.4f"
      % (CHAR_H, FLOOR, max(p.z for p in W),
         min(p.x for p in W), max(p.x for p in W)))

GN = {g.index: g.name for g in body.vertex_groups}


def dom_bone(vi):
    best, bw = "-", 0.0
    for g in body.data.vertices[vi].groups:
        if g.weight > bw:
            bw, best = g.weight, GN.get(g.group, "?")
    return best


# ================================================================ 2) 막대 축 실측
# 어깨~팔꿈치 위 구간은 막대만 지나가는 '깨끗한' 자리다(팔은 훨씬 아래에 있다).
# 거기서 축 중심과 단면 반폭을 잰다. 어떤 값도 손으로 적지 않는다.
def median(xs):
    s = sorted(xs)
    return s[len(s) // 2]


# ★'깨끗한 구간'은 어깨끝~팔꿈치 위(|x| 0.20~0.35)뿐이다. 0.40 을 넘으면 팔뚝이
#   축에서 0.04 까지 다가와 1차 창을 채워 버린다(실측: 반폭이 0.028/0.042 로 부품).
rough = [i for i, p in enumerate(W)
         if 0.20 <= abs(p.x) <= 0.35 and 1.38 <= p.z <= 1.52
         and -0.04 <= p.y <= 0.06]
# ★단면을 통계로 짐작하면 반드시 틀린다(중앙값·최빈점·틈 통계 다 해 봤다).
#   창이 조금이라도 좁으면 **막대 아랫날이 살아남고**, 그 조각을 나중에 덮으면
#   어깨를 가로지르는 얇은 판이 생긴다(렌더로 확인). 그래서 두 번에 나눈다.
#     1차 - 어깨~팔꿈치 위 '깨끗한' 구간에서 아주 넉넉한 창으로 막대를 통째로 잡는다.
#            이 구간의 살은 축에서 0.07 이상 떨어져 있어서 넉넉해도 안 딸려온다.
#     2차 - 1차로 잡은 **실제 정점 분포**에서 중심과 반폭을 그대로 읽는다.
W1_Y, W1_Z = CHAR_H * 0.020, CHAR_H * 0.026
YR = median([W[i].y for i in rough])
ZR = median([W[i].z for i in rough])
first = [i for i in rough
         if abs(W[i].y - YR) <= W1_Y and abs(W[i].z - ZR) <= W1_Z]
for _ in range(4):
    YR = (min(W[i].y for i in first) + max(W[i].y for i in first)) / 2
    ZR = (min(W[i].z for i in first) + max(W[i].z for i in first)) / 2
    first = [i for i in rough
             if abs(W[i].y - YR) <= W1_Y and abs(W[i].z - ZR) <= W1_Z]
Y0, Z0 = YR, ZR
DY = max(abs(W[i].y - Y0) for i in first)
DZ = max(abs(W[i].z - Z0) for i in first)
clean = first
print("\n[막대 축] 1차 넉넉한 창(y %.4f z %.4f) 안 정점 %d -> 실측 단면"
      % (W1_Y, W1_Z, len(first)))
print("          중심 y %.5f z %.5f / 반폭 y %.4f z %.4f (얇고 세로로 긴 칼날 단면)"
      % (Y0, Z0, DY, DZ))
if DY > W1_Y * 0.95 or DZ > W1_Z * 0.95:
    print("          ★1차 창에 정점이 꽉 찼다. 살이 딸려왔을 수 있다")
print("          창 안 정점 %d / 지배 뼈 %s"
      % (len(clean), sorted(set(dom_bone(i) for i in clean))))


def rad(i):
    return math.hypot(W[i].y - Y0, W[i].z - Z0)


# ---- 주먹 띠: 손목 바깥 ~ 살이 다시 얇아지는 곳까지 ----
# ★안쪽 끝은 손목 뼈다. 팔뚝과 주먹은 이어진 살이라 반경으로는 못 가른다.
#   바깥 끝은 '축까지 최대 반경이 막대 굵기로 되돌아오는 첫 슬랩' = 자루 끝의 시작.
FIST_R = DZ * 2.2
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
fist_x = {}
for sgn, tag, bn in ((-1, "오른손", HAND_R_RAW), (1, "왼손", HAND_L_RAW)):
    wx = abs((arm.matrix_world @ arm.data.bones[bn].head_local).x)
    hi = wx
    k = 0
    while True:
        x0 = wx + k * 0.02
        if x0 > 0.90:
            break
        sel = [i for i, p in enumerate(W)
               if x0 <= p.x * sgn < x0 + 0.02
               and abs(p.y - Y0) < 0.13 and abs(p.z - Z0) < 0.13]
        if not sel:
            break
        if max(rad(i) for i in sel) <= FIST_R:
            break
        hi = x0 + 0.02
        k += 1
    fist_x[sgn] = (wx, hi)
    print("          %s 손목 |x| %.3f -> 주먹 띠 %.3f~%.3f (반경 문턱 %.4f)"
          % (tag, wx, wx, hi, FIST_R))
FIST_C = {s: Vector((s * (fist_x[s][0] + fist_x[s][1]) / 2, Y0, Z0))
          for s in (-1, 1)}

# ================================================================ 2-1) 전후 비교 렌더
# ★수술은 되돌릴 수 없으니 같은 카메라로 전/후를 찍어 둔다.
RIG = []


def setup_render():
    ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                        else "BLENDER_EEVEE")
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = 620, 800
    sc.render.film_transparent = False
    wd = bpy.data.worlds.new("W")
    sc.world = wd
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs[0].default_value = (0.06, 0.065, 0.08, 1)
    li = bpy.data.lights.new("S", "SUN")
    li.energy = 4.0
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = (math.radians(58), 0, math.radians(-30))
    sc.collection.objects.link(so)
    li2 = bpy.data.lights.new("F", "SUN")
    li2.energy = 1.8
    li2.color = (0.7, 0.82, 1.0)
    so2 = bpy.data.objects.new("F", li2)
    so2.rotation_euler = (math.radians(-40), 0, math.radians(130))
    sc.collection.objects.link(so2)
    bpy.ops.mesh.primitive_plane_add(size=CHAR_H * 6, location=(0, 0, FLOOR))
    fl = bpy.context.object
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        0.32, 0.34, 0.38, 1)
    fl.data.materials.append(fm)
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.lens = 55
    RIG[:] = [so, so2, fl, cam]
    return cam


def teardown_render():
    for o in list(RIG):
        bpy.data.objects.remove(o, do_unlink=True)
    RIG[:] = []
    sc.camera = None


def shots(tag, cam):
    def shoot(name, tgt, eye, dist):
        cam.location = Vector(tgt) + Vector(eye).normalized() * dist
        dd = Vector(tgt) - cam.location
        cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUTDIR, "s26_%s_%s.png" % (tag, name))
        bpy.ops.render.render(write_still=True)

    T = (0, 0, FLOOR + CHAR_H * 0.5)
    shoot("front", T, (0, -1, 0.05), CHAR_H * 1.55)
    shoot("back", T, (0, 1, 0.05), CHAR_H * 1.55)
    shoot("side", T, (-1, 0, 0.05), CHAR_H * 1.55)
    shoot("34", T, (-0.8, -1, 0.25), CHAR_H * 1.55)
    shoot("rhand", FIST_C[-1], (-0.3, -1, 0.45), 0.60)
    shoot("rhand_top", FIST_C[-1], (0, -0.2, 1), 0.52)
    shoot("lhand", FIST_C[1], (0.3, -1, 0.45), 0.42)
    shoot("neck", (0, 0, Z0), (0, 1, 0.15), CHAR_H * 0.45)
    shoot("neck_front", (0, 0, Z0), (0, -1, 0.05), CHAR_H * 0.45)
    print("   렌더 %s 8장" % tag)


if RENDER:
    os.makedirs(OUTDIR, exist_ok=True)
    shots("before", setup_render())
    teardown_render()

# ================================================================ 3) 막대 선택
# 씨앗: 깨끗한 구간의 튜브 + 주먹 바깥(자루 끝)의 튜브
# 성장: 엣지로 이웃하면서 튜브 창 안. 주먹 띠는 절대 안 넘는다.
# 실측 단면에 여유를 더한다. 여유가 모자라면 막대 조각이 남고, 과하면 살이 딸려온다.
MID_Y, MID_Z = DY + CHAR_H * 0.004, DZ + CHAR_H * 0.004   # 팔 위 막대 본체
POM_Y, POM_Z = DY + CHAR_H * 0.015, DZ + CHAR_H * 0.010   # 주먹 밖 자루 끝(굵다)
print("\n[선택] 창 본체 |dy|<%.4f |dz|<%.4f / 자루끝 |dy|<%.4f |dz|<%.4f"
      % (MID_Y, MID_Z, POM_Y, POM_Z))


def in_window(i):
    p = W[i]
    ax = abs(p.x)
    sgn = -1 if p.x < 0 else 1
    lo, hi = fist_x[sgn]
    if lo <= ax <= hi:                       # 주먹은 손대지 않는다
        return False
    if PROTECT and dom_bone(i) in HEAD_BONES:
        return False
    dy, dz = (POM_Y, POM_Z) if ax > hi else (MID_Y, MID_Z)
    return abs(p.y - Y0) <= dy and abs(p.z - Z0) <= dz


# 씨앗은 두 군데. (1) 어깨~팔꿈치 위의 깨끗한 막대 (2) 주먹 밖으로 나온 자루 끝.
# 주먹이 둘 사이를 막고 있어서 한 쪽 씨앗만으로는 반대편에 못 간다.
seed = set()
for i, p in enumerate(W):
    if not in_window(i):
        continue
    ax = abs(p.x)
    sgn = -1 if p.x < 0 else 1
    lo, hi = fist_x[sgn]
    if 0.15 <= ax <= 0.45 or ax > hi + 0.005:
        seed.add(i)
print("       씨앗 %d정점 (본체 %d / 자루끝 %d)"
      % (len(seed), sum(1 for i in seed if abs(W[i].x) <= 0.45),
         sum(1 for i in seed if abs(W[i].x) > 0.45)))

bm = bmesh.new()
bm.from_mesh(body.data)
bm.verts.ensure_lookup_table()
sel = set(seed)
stack = list(seed)
while stack:
    i = stack.pop()
    for e in bm.verts[i].link_edges:
        j = e.other_vert(bm.verts[i]).index
        if j not in sel and in_window(j):
            sel.add(j)
            stack.append(j)
# 막대에 붙은 작은 별개 조각(장식 매듭 등)도 같이
comp_extra = 0
seen = set()
for v in bm.verts:
    if v.index in seen:
        continue
    st, comp = [v], []
    seen.add(v.index)
    while st:
        x = st.pop()
        comp.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen:
                seen.add(o.index)
                st.append(o)
    if len(comp) < 200 and all(abs(W[i].y - Y0) < DY * 4 and abs(W[i].z - Z0) < DZ * 2
                               for i in comp):
        sel |= set(comp)
        comp_extra += len(comp)
print("       플러드필 -> %d정점 (막대에 붙은 작은 섬 %d정점 포함)"
      % (len(sel), comp_extra))

# ---- 목 뒤 토막 잇기 ----
# ★막대는 목 뒤에서 몸 메시에 그대로 이어 붙어 있다. 머리·목 보호를 켜 두면
#   플러드필이 거기서 멈춰 **양 옆으로 삐져나온 토막**이 남는다(뒷목 렌더로 확인).
#   막대는 끊긴 물건이 아니므로, 좌우 토막의 안쪽 끝 사이는 통째로 막대다.
#   그 구간만 보호를 풀고 좁은 창으로 마저 지운다. 뚫린 데는 뒤에서 덮는다.
bridged = 0
if sel:
    neg = [W[i].x for i in sel if W[i].x < 0]
    pos = [W[i].x for i in sel if W[i].x > 0]
    if neg and pos:
        xl, xr = max(neg), min(pos)
        for i, p in enumerate(W):
            if i in sel or not (xl <= p.x <= xr):
                continue
            if abs(p.y - Y0) <= MID_Y and abs(p.z - Z0) <= MID_Z:
                sel.add(i)
                bridged += 1
        print("       목 뒤 토막 잇기: x %.3f~%.3f 구간에서 %d정점 추가"
              % (xl, xr, bridged))
if sel:
    xs = [W[i].x for i in sel]
    print("       선택 x %.3f~%.3f / y %.4f~%.4f / z %.4f~%.4f"
          % (min(xs), max(xs), min(W[i].y for i in sel), max(W[i].y for i in sel),
             min(W[i].z for i in sel), max(W[i].z for i in sel)))
    cnt = {}
    for i in sel:
        b = dom_bone(i)
        cnt[b] = cnt.get(b, 0) + 1
    print("       지배 뼈 %s" % sorted(cnt.items(), key=lambda t: -t[1]))

# ---- 삭제 ----
before_bound = sum(1 for e in bm.edges if len(e.link_faces) < 2)
del_tris = sum(1 for t in body.data.loop_triangles
               if any(v in sel for v in t.vertices))
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in sel], context="VERTS")
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
after_bound = [e for e in bm.edges if len(e.link_faces) < 2]
print("\n[수술] 삭제 정점 %d / 삼각 %d 감소 예상" % (len(sel), del_tris))
print("       경계 엣지 수술 전 %d -> 수술 후 %d" % (before_bound, len(after_bound)))

# ---- 구멍(경계 고리) 찾기 ----
loops = []
used = set()
for e in after_bound:
    if e.index in used:
        continue
    ring, stack2 = [], [e]
    while stack2:
        x = stack2.pop()
        if x.index in used:
            continue
        used.add(x.index)
        ring.append(x)
        for v in x.verts:
            for e2 in v.link_edges:
                if len(e2.link_faces) < 2 and e2.index not in used:
                    stack2.append(e2)
    loops.append(ring)
print("       구멍(경계 고리) %d개" % len(loops))
for k, ring in enumerate(loops):
    vs = set()
    for e in ring:
        vs |= set(e.verts)
    c = Vector((0, 0, 0))
    for v in vs:
        c += MW @ v.co
    c /= len(vs)
    r = max((MW @ v.co - c).length for v in vs)
    print("        #%d 엣지 %2d 정점 %2d 중심 (%.4f,%.4f,%.4f) 반경 %.4f (키의 %.2f%%)"
          % (k, len(ring), len(vs), c.x, c.y, c.z, r, r / CHAR_H * 100))

# ================================================================ 4) 구멍 덮기
uvl = bm.loops.layers.uv.active
dvl = bm.verts.layers.deform.active
RINGS = []          # (중심 월드, 반경, 축 후보) - 터널 실측에 쓴다
for ring in loops:
    vs = set()
    for e in ring:
        vs |= set(e.verts)
    c = Vector((0, 0, 0))
    for v in vs:
        c += MW @ v.co
    c /= len(vs)
    RINGS.append((c, max((MW @ v.co - c).length for v in vs), sorted(v.index for v in vs)))

def medoid_uv(verts):
    """고리 정점들의 UV 중 나머지와 가장 가까운 하나(메도이드). 튀는 값에 안 흔들린다."""
    uvs = []
    for v in verts:
        for l in v.link_loops:
            uvs.append(Vector(l[uvl].uv))
            break
    if not uvs:
        return Vector((0, 0))
    return min(uvs, key=lambda a: sum((a - b).length for b in uvs))


capped = 0
if CAP and loops:
    for ring in loops:
        # 고리를 순서대로 잇는다(각 정점의 경계 엣지는 정확히 2개)
        vset = set()
        for e in ring:
            vset |= set(e.verts)
        adj = {v: [] for v in vset}
        for e in ring:
            a, b = e.verts
            adj[a].append(b)
            adj[b].append(a)
        if any(len(a) != 2 for a in adj.values()):
            # 갈래진 고리는 부채꼴로 못 덮는다. bmesh 삼각 채우기로 넘긴다.
            print("        ★고리가 단순 폐곡선이 아니다(분기 %d). 삼각 채우기로 덮는다"
                  % sum(1 for a in adj.values() if len(a) != 2))
            res = bmesh.ops.triangle_fill(bm, edges=list(ring), use_beauty=True)
            uvm = medoid_uv(vset)
            for f in res.get("geom", []):
                if isinstance(f, bmesh.types.BMFace):
                    for l in f.loops:
                        l[uvl].uv = uvm
                    capped += 1
            continue
        start = next(iter(vset))
        order, prev, cur = [start], None, start
        while True:
            nxt = adj[cur][0] if adj[cur][0] is not prev else adj[cur][1]
            if nxt is start:
                break
            order.append(nxt)
            prev, cur = cur, nxt
        # 중심 정점: 위치·UV·웨이트를 고리 평균으로
        cen = Vector((0, 0, 0))
        for v in order:
            cen += v.co
        cen /= len(order)
        nv = bm.verts.new(cen)
        if dvl:
            acc = {}
            for v in order:
                for gi, w in v[dvl].items():
                    acc[gi] = acc.get(gi, 0.0) + w
            tot = sum(acc.values()) or 1.0
            for gi, w in acc.items():
                nv[dvl][gi] = w / tot
        bm.verts.index_update()
        # ★UV 는 고리 전체에 **한 값**을 쓴다. 정점마다 제 UV 를 물리면 고리가
        #   살갗 섬과 옷 섬에 걸쳐 있을 때 아틀라스를 가로질러 무지개 얼룩이 진다
        #   (뒷목 렌더로 확인). 메도이드 하나로 칠하면 단색 그늘로 읽힌다.
        cuv = medoid_uv(order)
        # 부채꼴로 덮는다(n각형보다 비평면에 강하다)
        made = 0
        for k in range(len(order)):
            a, b = order[k], order[(k + 1) % len(order)]
            try:
                f = bm.faces.new((a, b, nv))
            except ValueError:
                continue
            for l in f.loops:
                l[uvl].uv = cuv
            f.normal_update()
            made += 1
        capped += made
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    print("       구멍 덮기: 새 삼각형 %d개" % capped)
elif loops:
    print("       CAP=0 이라 구멍을 그대로 둔다")

bm.to_mesh(body.data)
bm.free()
body.data.update()
body.data.calc_loop_triangles()
TRI1 = len(body.data.loop_triangles)
W = [MW @ v.co for v in body.data.vertices]
print("       삼각 %d -> %d (%+d) / 정점 %d"
      % (TRI0, TRI1, TRI1 - TRI0, len(body.data.vertices)))
print("       수술 후 bbox x %.4f~%.4f z %.4f~%.4f (키 %.4f)"
      % (min(p.x for p in W), max(p.x for p in W),
         min(p.z for p in W), max(p.z for p in W),
         max(p.z for p in W) - min(p.z for p in W)))

# ================================================================ 5) 주먹 터널 실측
# 잘린 두 고리 중심을 이은 선이 곧 주먹을 관통하는 터널이다.
def hand_rings(sgn):
    """주먹 띠 안에 있으면서 중심이 막대 축 근처인 고리만. 엉뚱한 구멍을 안 집게."""
    lo, hi = fist_x[sgn]
    got = [r for r in RINGS
           if lo - 0.05 <= r[0].x * sgn <= hi + 0.05
           and abs(r[0].y - Y0) < DY * 6 and abs(r[0].z - Z0) < DZ * 3]
    return sorted(got, key=lambda r: r[0].x * sgn)


TUNNEL = {}
for sgn, tag in ((-1, "오른손"), (1, "왼손")):
    rr = hand_rings(sgn)
    if len(rr) >= 2:
        a, b = rr[0][0], rr[-1][0]
        c = (a + b) / 2
        u = (b - a).normalized()
        TUNNEL[sgn] = (c, u, (rr[0][1] + rr[-1][1]) / 2, (b - a).length)
        print("\n[터널] %s 고리 %d개 -> 중심 (%.4f,%.4f,%.4f) 축 (%+.4f,%+.4f,%+.4f)"
              % (tag, len(rr), c.x, c.y, c.z, u.x, u.y, u.z))
        print("       터널 길이 %.4f / 반경 %.4f (게임 키 1.75 환산 지름 %.1fcm)"
              % ((b - a).length, (rr[0][1] + rr[-1][1]) / 2,
                 (rr[0][1] + rr[-1][1]) * 1.75 / CHAR_H * 100))
    else:
        print("\n[터널] %s 고리를 %d개밖에 못 찾았다. 주먹 중심으로 대신한다"
              % (tag, len(rr)))
        lo, hi = fist_x[sgn]
        pts = [p for p in W if lo <= p.x * sgn <= hi
               and abs(p.y - Y0) < 0.13 and abs(p.z - Z0) < 0.13]
        c = (sum(pts, Vector()) / len(pts)) if pts else FIST_C[sgn]
        TUNNEL[sgn] = (c, Vector((sgn, 0, 0)), DZ * 1.5, max(hi - lo, DZ))

# ================================================================ 6) 뼈 이름 정규화
have = set(b.name for b in arm.data.bones)
todo = [(o, n) for o, n in RENAME if o in have and n not in have]
print("\n[뼈] Meshy 원명 %d개를 우리 규칙으로 바꾼다" % len(todo))
for old, new in todo:
    arm.data.bones[old].name = new
nm = dict(todo)
for g in body.vertex_groups:                              # ★함정 3
    if g.name in nm:
        g.name = nm[g.name]
print("     %s" % sorted(b.name for b in arm.data.bones))
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
HM_R = (arm.matrix_world @ arm.pose.bones[HAND_R].matrix).copy()
WRIST = HM_R.translation.copy()
print("     오른손 뼈 레스트 월드 원점 (%.4f,%.4f,%.4f)" % (WRIST.x, WRIST.y, WRIST.z))
c, u, r, L = TUNNEL[-1]
d = (c - WRIST)
print("     손목->터널중심 %.4f (뼈축 성분 %.1f%%)"
      % (d.length, abs(d.normalized().dot(
          (HM_R.to_3x3() @ Vector((0, 1, 0))).normalized())) * 100))

# ================================================================ 7) 소스 칼 방향
# 같은 이름의 소스 칼이 레스트에서 월드 어느 방향을 보는지 잰다. s24 가 나중에
# 계산하는 보정 회전은 (소스 프레임) @ (타깃 프레임)^-1 이므로, 여기서 미리
# 두 프레임을 같게 만들어 두면 s24 의 SWORD_FIT 이 할 일이 없어진다.
def blade_frame(pts, origin):
    """(칼끝방향 u, 휨방향 b, 손아래길이, 칼끝길이). u 는 measureBlade 와 같은 절차."""
    d = [p - origin for p in pts]
    u = max(d, key=lambda v: v.length).normalized()
    pr = [v.dot(u) for v in d]
    hi = max(pr)
    perp = [v - u * v.dot(u) for v, t in zip(d, pr) if t > hi * 0.35]
    b = Vector((0, 0, 0))
    for v in perp:
        b += v
    b /= max(1, len(perp))
    if b.length < 1e-6:
        b = u.cross(Vector((0, 0, 1)))
    b = (b - u * b.dot(u)).normalized()
    return u, b, -min(pr), hi


def frame_of(u, b):
    return Matrix((u, b, u.cross(b))).transposed()


SRC_FRAME = {}
if os.path.exists(SRC_GLB):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=SRC_GLB)
    drop_junk()
    new = [o for o in sc.objects if o.name not in before]
    sarm = next(o for o in new if o.type == "ARMATURE")
    for b in sarm.pose.bones:
        b.rotation_mode = "QUATERNION"
        b.matrix_basis = Matrix()
    sarm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    SW_ = sarm.matrix_world @ sarm.pose.bones[HAND_R].matrix
    SWRIST = SW_.translation.copy()
    sbody = [o for o in new if o.type == "MESH" and not o.name.startswith("SW_")]
    szs = []
    for o in sbody:
        szs += [(o.matrix_world @ v.co).z for v in o.data.vertices]
    SH = max(szs) - min(szs)
    print("\n[소스] %s 키 %.4f / 손목 (%.4f,%.4f,%.4f)"
          % (os.path.basename(SRC_GLB), SH, SWRIST.x, SWRIST.y, SWRIST.z))
    for o in new:
        if o.type == "MESH" and o.name.startswith("SW_"):
            pts = [o.matrix_world @ v.co for v in o.data.vertices]
            u, b, below, tip = blade_frame(pts, SWRIST)
            SRC_FRAME[o.name[3:]] = (u, b, below / SH, tip / SH)
            print("   %-12s u (%+.4f,%+.4f,%+.4f) 휨 (%+.4f,%+.4f,%+.4f)"
                  "  손아래 %.4f 칼끝 %.4f (키 정규화)"
                  % (o.name[3:], u.x, u.y, u.z, b.x, b.y, b.z, below / SH, tip / SH))
    for o in list(new):
        bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
else:
    print("\n★소스 %s 가 없다. 칼 방향을 터널 축에 맞춘다(s24 SWORD_FIT 이 고칠 것)"
          % SRC_GLB)

# ================================================================ 8) 칼 7자루
import importlib
import swords as SW
importlib.reload(SW)

SW_SCALE = CHAR_H * SW_RATIO
print("\n[칼] 배율 = 키 %.4f * %.3f = %.4f" % (CHAR_H, SW_RATIO, SW_SCALE))
GRIP_C, TUN_U = TUNNEL[-1][0], TUNNEL[-1][1]
print("     자루 중앙을 터널 중심 (%.4f,%.4f,%.4f) 에 놓는다"
      % (GRIP_C.x, GRIP_C.y, GRIP_C.z))

sword_objs = {}
for v in SW.VARIANTS:
    key = v["key"]
    r = SW.build_sword(v, scale=SW_SCALE)
    parts = [c for c in r.children if c.type == "MESH"]
    # 모디파이어를 굽고(칼날 Solidify 소실 방지) 월드로 내린 뒤 하나로 합친다
    for ob in parts:
        mw = ob.matrix_world.copy()
        ob.constraints.clear()
        ob.parent = None
        ob.matrix_world = mw
        bpy.context.view_layer.update()
        ob.data.transform(mw)
        ob.matrix_world = Matrix()
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        for md in list(ob.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=md.name)
            except Exception as e:
                print("     modifier_apply 실패", ob.name, md.name, e)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in parts:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    s = bpy.context.view_layer.objects.active
    s.name = s.data.name = "SW_" + key                     # ★함정 5
    bpy.data.objects.remove(r, do_unlink=True)

    # build_sword 원점 = 자루 중앙. 터널 중심으로 옮긴다.
    for vt in s.data.vertices:
        vt.co = GRIP_C + vt.co
    s.data.update()

    # 방향 정합: 손목 기준 프레임을 소스와 같게. u 가 손목 기준이라 반복해서 조인다.
    tgt = SRC_FRAME.get(key) or SRC_FRAME.get("baekah")
    if tgt:
        Fs = frame_of(tgt[0], tgt[1])
        ang = 0.0
        for it in range(16):
            pts = [vt.co.copy() for vt in s.data.vertices]
            u, b, below, tip = blade_frame(pts, WRIST)
            R = Fs @ frame_of(u, b).inverted()
            ang = math.degrees(R.to_quaternion().angle)
            if ang < 0.02:
                break
            for vt in s.data.vertices:
                vt.co = GRIP_C + R @ (vt.co - GRIP_C)
        s.data.update()
        pts = [vt.co.copy() for vt in s.data.vertices]
        u, b, below, tip = blade_frame(pts, WRIST)
        err = math.degrees(u.angle(tgt[0]))
        print("     %-12s 정합 %2d회 잔차 %.3f도 / 축오차 %.3f도  손아래 %.4f 칼끝 %.4f"
              " (소스 %.4f/%.4f)"
              % (key, it + 1, ang, err, below / CHAR_H, tip / CHAR_H, tgt[2], tgt[3]))
    else:
        # 소스가 없으면 터널 축에 꿴다(칼끝은 몸 바깥쪽)
        u0, b0, _, _ = blade_frame([vt.co.copy() for vt in s.data.vertices], WRIST)
        R = Vector(u0).rotation_difference(TUN_U).to_matrix()
        for vt in s.data.vertices:
            vt.co = GRIP_C + R @ (vt.co - GRIP_C)
        s.data.update()
        print("     %-12s 터널 축에 꿰었다" % key)

    vg = s.vertex_groups.new(name=HAND_R)
    vg.add(range(len(s.data.vertices)), 1.0, "REPLACE")
    md = s.modifiers.new("Armature", "ARMATURE")
    md.object = arm
    s.parent = arm
    s.matrix_parent_inverse = arm.matrix_world.inverted()
    sword_objs[key] = s

s_tris = 0
for k, s in sword_objs.items():
    s.data.calc_loop_triangles()
    s_tris += len(s.data.loop_triangles)
print("     칼 %d자루 / 삼각 합 %d" % (len(sword_objs), s_tris))

# 자루가 주먹을 실제로 지나가는지(쥔 것처럼 보이는지) 검산
hg = body.vertex_groups[HAND_R]
hp = []
for vt in body.data.vertices:
    w = next((x.weight for x in vt.groups if x.group == hg.index), 0.0)
    if w > 0.5:
        hp.append(MW @ vt.co)
ref = sword_objs.get("baekah") or list(sword_objs.values())[0]
u, b, below, tip = blade_frame([vt.co.copy() for vt in ref.data.vertices], WRIST)
inside = 0
for p in hp:
    q = p - GRIP_C
    t = q.dot(u)
    if abs(t) <= below * 0.6 and (q - u * t).length <= TUNNEL[-1][2] * 1.6:
        inside += 1
print("     [검산] 자루 원통 안에 든 주먹 정점 %d/%d (관통 = 쥔 것처럼 보인다)"
      % (inside, len(hp)))

# ================================================================ 9) 텍스처
# ★재질은 게임에서 MeshToonMaterial({map}) 로 갈아끼운다. 베이스컬러 말고는 안 쓴다.
#   Meshy 는 emissive 에도 알베도를 물려 놓는다(★함정 6). 노드 비교는 반드시 이름으로.
print("\n[텍스처]")


def strip_material(m):
    if not m or not m.node_tree:
        return
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    bn, kept = bsdf.name, None
    for l in list(nt.links):
        if l.to_node.name != bn:
            continue
        if l.to_socket.name == "Base Color":
            kept = l.from_node.name
            continue
        print("   %-14s 링크 끊음: %-16s (from %s)"
              % (m.name, l.to_socket.name, l.from_node.name))
        nt.links.remove(l)
    for key, val in (("Emission Strength", 0.0), ("Metallic", 0.0),
                     ("Roughness", 0.75), ("Specular IOR Level", 0.35)):
        s2 = bsdf.inputs.get(key)
        if s2 is not None:
            s2.default_value = val
    s2 = bsdf.inputs.get("Emission Color")
    if s2 is not None:
        s2.default_value = (0, 0, 0, 1)
    keepset, stack2 = set(), ([kept] if kept else [])
    while stack2:
        n2 = stack2.pop()
        if n2 is None or n2 in keepset:
            continue
        keepset.add(n2)
        nd = nt.nodes.get(n2)
        if nd is None:
            continue
        for i2 in nd.inputs:
            for l in i2.links:
                stack2.append(l.from_node.name)
    for nd in list(nt.nodes):
        if nd.type == "TEX_IMAGE" and nd.name not in keepset:
            print("   %-14s 텍스처 노드 제거: %s"
                  % (m.name, getattr(nd.image, "name", "?")))
            nt.nodes.remove(nd)
    print("   %-14s 남긴 베이스컬러 노드: %s" % (m.name, kept))


for m in body.data.materials:
    strip_material(m)
used = []
for m in body.data.materials:
    if not m or not m.node_tree:
        continue
    for nd in m.node_tree.nodes:
        im = getattr(nd, "image", None)
        if im is not None and im not in used:
            used.append(im)
for im in used:
    w, h = im.size
    print("   %-16s %dx%d %s" % (im.name, w, h, im.file_format))
    if TEX_SIZE and (w > TEX_SIZE or h > TEX_SIZE):
        k = TEX_SIZE / float(max(w, h))
        im.scale(max(1, int(round(w * k))), max(1, int(round(h * k))))
        print("      -> %dx%d 로 축소" % im.size[:])

# ================================================================ 10) 내보내기
arm.data.pose_position = "POSE"
bpy.context.view_layer.update()
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
print("\n[내보내기] 오브젝트 %s" % [(o.name, o.type) for o in sc.objects])
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB, export_format="GLB", use_selection=False,
    export_animations=False, export_apply=True, export_yup=True,
    export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
    export_jpeg_quality=TEX_QUALITY)
sz = os.path.getsize(OUT_GLB)
print("EXPORTED %s  %d bytes (%.2f MB)  %s q%d  삼각 몸 %d + 칼 %d  뼈 %d"
      % (OUT_GLB, sz, sz / 1e6, TEX_FORMAT, TEX_QUALITY, TRI1, s_tris,
         len(arm.data.bones)))

# ================================================================ 11) 렌더
if not RENDER:
    print("\nDONE (렌더 생략)")
    raise SystemExit(0)

# ★7자루가 다 보이면 겹쳐서 아무것도 판정이 안 된다. 게임 기본(백아)만 켠다.
for k, o in sword_objs.items():
    o.hide_render = (k != "baekah")
cam = setup_render()
shots("after", cam)
# 칼 접사: 자루가 주먹을 어떻게 지나가는지 본다
c0 = TUNNEL[-1][0]
for nm, eye, dist in (("grip", (-0.5, -1, 0.3), 0.42),
                      ("grip2", (-0.2, -0.6, 1.0), 0.42),
                      ("sword", (0, -1, 0.15), CHAR_H * 1.2)):
    cam.location = c0 + Vector(eye).normalized() * dist
    dd = c0 - cam.location
    cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUTDIR, "s26_after_%s.png" % nm)
    bpy.ops.render.render(write_still=True)
print("\n렌더 완료:", OUTDIR)
print("DONE")
