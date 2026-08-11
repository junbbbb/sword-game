# -*- coding: utf-8 -*-
"""고정 쿼터뷰 카메라 후보를 **실제 교전 장면**으로 재현해 렌더한다.

왜 블렌더인가: 크롬 창이 화면에 안 떠 있으면 requestAnimationFrame 이 아예 안 돌아
게임이 멈춘 채로 스크린샷이 찍힌다. 그래서 카메라 판단을 게임에서 못 한다.
main.js 의 카메라 식을 그대로 옮겨 여기서 본다.

★빈 맵에 캐릭터 하나 세워놓고 판단하면 안 된다. 시야 범위는 "이 화면으로 이 전투를
  할 수 있는가"로만 판단할 수 있다. 그래서 파티 3명 + 요괴 무리 하나를 실제 간격으로
  놓고 찍는다(간격 근거는 아래 FORMATION 주석).

실행:
  SPOT=plaza CAMS="a:1.02:11:34:0,b:0.977:24.1:26:0" \
    blender -b -P blender/look_cam.py

  CAMS 는 "태그:pitch(rad):dist(m):fov(세로,도):yaw(rad)" 를 쉼표로 이어 붙인다.
  ★한 번에 3개까지만. 블렌더가 오래 물고 있으면 타임아웃 난다.
  SPOT = plaza(넓은 마당) / corridor(좁은 통로) / boss(보스 마당) / gate(남문 마당)
         또는 "cell:C:R[:FACE]" 로 칸을 직접 지정한다(맵이 바뀌면 이쪽이 안전하다).
  LEAD = main.js CAM.lead. **바라보는 지점을 캐릭터보다 이만큼 앞으로** 민다.
         안 넣으면 main.js 현재값 1.25 를 쓴다. 0 이면 옛 방식(캐릭터 정조준).
  PARTY=0 이면 파티·요괴 없이 맵만. RESX/RESY 로 해상도.
"""

import bpy
import os
import math
import json
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
OUT = os.environ.get("OUTDIR") or os.path.join(ROOT, "renders", "history", "v56_camera")
SPOT_NAME = os.environ.get("SPOT", "plaza")
RESX = int(os.environ.get("RESX", "1280"))
RESY = int(os.environ.get("RESY", "720"))       # 16:9. 게임 창 비율과 같아야 화각이 맞다
WITH_PARTY = os.environ.get("PARTY", "1") != "0"
os.makedirs(OUT, exist_ok=True)

LV = json.load(open(os.path.join(ROOT, "web", "level1.json"), encoding="utf-8"))
CELL = LV["cell"]
HALF = LV["size"]["x"] / 2.0
GRID = LV["grid"]
FLOOR = LV["floorY"]

CHAR_H = 1.75                    # main.js CHAR_CFG.slayer.h
TARGET_Y = CHAR_H * 0.62         # main.js: camTarget.setY(charH*0.62)

# ── 후보 파싱 ────────────────────────────────────────────────
DEFAULT = "cur:1.02:11:34:0"
CAMS = []
for item in os.environ.get("CAMS", DEFAULT).split(","):
    if not item.strip():
        continue
    tag, p, d, f, y = item.split(":")
    CAMS.append((tag, float(p), float(d), float(f), float(y)))
if len(CAMS) > 3:
    raise SystemExit("한 번에 3개까지만. 블렌더가 타임아웃 난다.")


# ── 씬 초기화 ────────────────────────────────────────────────
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"


def drop_importer_junk():
    """★glTF 임포터가 뼈 표시용 Icosphere(반지름 1)를 씬에 만든다. glb 안에는 없는
    물건이라 안 지우면 렌더에 구가 찍히고 키 측정도 통째로 오염된다."""
    n = 0
    for o in list(bpy.context.scene.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)
            n += 1
    return n


def kill_emission():
    """★Meshy 재질은 emissiveFactor (1,1,1) 에 알베도를 그대로 물려놨다.
    안 끄면 태양광이 더해져 살결이 하얗게 날아간다. 게임은 MeshToonMaterial 로
    갈아끼워 이미시브를 버리므로 끄는 쪽이 실제 화면과 가깝다."""
    n = 0
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            for key in ("Emission Strength", "Emission Color"):
                s = nd.inputs.get(key) if hasattr(nd, "inputs") else None
                if s is None:
                    continue
                if key == "Emission Strength":
                    s.default_value = 0.0
                else:
                    s.default_value = (0, 0, 0, 1)
                for l in list(m.node_tree.links):
                    if l.to_socket == s:
                        m.node_tree.links.remove(l)
                n += 1
    return n


def g2b(gx, gz, y=0.0):
    """게임(three.js) 좌표 -> 블렌더. three.z = -blender.y"""
    return Vector((gx, -gz, y))


def spot(c, r):
    """칸 인덱스 -> 게임 좌표. 못 걷는 칸이면 소리 내서 알린다."""
    k = GRID[r][c]
    if k in ("#", "H"):
        print("  [경고] (c%d r%d) 는 '%s' = 못 걷는 칸이다" % (c, r, k))
    return (-HALF + (c + 0.5) * CELL, -HALF + (r + 0.5) * CELL)


bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "web", "level1.glb"))
print("[맵] 잡동사니 제거 %d개" % drop_importer_junk())


# ── 캐릭터 배치 ──────────────────────────────────────────────
def place_char(glb, gx, gz, face_yaw, target_h):
    """glb 를 게임과 같은 방식으로 세운다.

    ★함정 세 개를 여기서 밟았다.
      1) 루트 아마추어에 스케일 0.025 가 이미 박혀 있다. o.scale = (s,s,s) 로
         **덮어쓰면** 40배로 부풀어 화면 밖으로 나간다. 반드시 곱한다.
      2) slayer.glb 안에 칼이 7자루(SW_*) 다 들어 있다. main.js 는 하나만 켠다.
         전부 켠 채로 키를 재면 가로 폭이 칼 길이로 잡히고 키도 부푼다.
      3) 임포터 Icosphere 를 매 임포트마다 지워야 한다(위 drop_importer_junk).
    face_yaw 는 게임 좌표에서 캐릭터가 바라볼 방향각(0 = +Z 를 봄).
    """
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "web", glb))
    drop_importer_junk()
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    body, shown = [], "SW_baekah"
    for o in new:
        if o.type != "MESH":
            continue
        if o.name.startswith("SW_") and not o.name.startswith(shown):
            o.hide_render = True
        elif not o.name.startswith("SW_"):
            body.append(o)
    if not body:
        print("  [경고] %s 캐릭터 메시를 못 찾았다" % glb)
        return

    def bbox():
        ws = [o.matrix_world @ v.co for o in body for v in o.data.vertices]
        return (min(p.x for p in ws), max(p.x for p in ws),
                min(p.y for p in ws), max(p.y for p in ws),
                min(p.z for p in ws), max(p.z for p in ws))

    x0, x1, y0, y1, z0, z1 = bbox()
    h = z1 - z0
    s = target_h / h                    # main.js 1297행: s = cfg.h / h
    for o in roots:
        o.scale = tuple(v * s for v in o.scale)     # ★대입이 아니라 곱
        o.location = tuple(v * s for v in o.location)
        o.rotation_euler[2] = face_yaw
    bpy.context.view_layer.update()
    x0, x1, y0, y1, z0, z1 = bbox()
    for o in roots:
        o.location.x += gx - (x0 + x1) / 2
        o.location.y += (-gz) - (y0 + y1) / 2
        o.location.z += FLOOR - z0
    bpy.context.view_layer.update()
    print("  %-12s (%6.1f,%6.1f) 원본키 %.3f x %.4f = %.3f" % (glb, gx, gz, h, s, h * s))


_YOKAI_MATS = {}


def yokai_mat(name, rgb, emit=0.0):
    key = (name, rgb, emit)
    if key in _YOKAI_MATS:
        return _YOKAI_MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1)
    b.inputs["Roughness"].default_value = 0.75
    if emit:
        b.inputs["Emission Color"].default_value = (rgb[0], rgb[1], rgb[2], 1)
        b.inputs["Emission Strength"].default_value = emit
    _YOKAI_MATS[key] = m
    return m


def place_yokai(gx, gz, scale=1.0, face=0.0):
    """web/enemy.js buildYokaiGeometry() 의 치수를 그대로 옮긴 대역이다.
    몸통 Icosphere r0.42 (y 1.08 배) 를 y=0.50 에, 아랫자락 원뿔(높이 0.52),
    뿔 2개(0.30/0.21) 를 y=0.84 위에. 전체 높이 약 1.15m 이고
    enemy.js 의 e.scale 이 0.78~1.20 이라 실제로는 0.9~1.4m 로 보인다.
    ★크기가 중요하다. 캐릭터(1.75) 대비 요괴가 얼마나 작게 보이는지가
      "이 시점으로 싸울 수 있나"의 절반이다.
    """
    objs = []
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.42, subdivisions=3,
                                          location=(0, 0, 0.50))
    b = bpy.context.object
    b.scale = (0.95, 0.95, 1.08)
    b.data.materials.append(yokai_mat("yk_body", (0.030, 0.049, 0.100)))
    objs.append(b)

    bpy.ops.mesh.primitive_cone_add(radius1=0.37, radius2=0.02, depth=0.52,
                                    vertices=8, location=(0, 0, 0.26))
    sk = bpy.context.object
    sk.rotation_euler[0] = math.pi        # 뾰족한 끝이 아래
    sk.data.materials.append(yokai_mat("yk_skirt", (0.014, 0.024, 0.055)))
    objs.append(sk)

    for sx, hh in ((-1, 0.30), (1, 0.21)):
        bpy.ops.mesh.primitive_cone_add(radius1=0.075, radius2=0.0, depth=hh,
                                        vertices=6,
                                        location=(sx * 0.20, -0.03, 0.84 + hh * 0.5))
        hn = bpy.context.object
        hn.rotation_euler[1] = sx * 0.38
        hn.data.materials.append(yokai_mat("yk_horn", (0.16, 0.13, 0.09)))
        objs.append(hn)

    for sx in (-1, 1):                    # 눈. 블룸에 걸려 멀리서 이게 제일 먼저 보인다
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.095, subdivisions=2,
                                              location=(sx * 0.155, -0.36, 0.575))
        ey = bpy.context.object
        ey.scale = (1.0, 0.62, 0.80)
        ey.data.materials.append(yokai_mat("yk_eye", (1.0, 0.32, 0.20), emit=6.0))
        objs.append(ey)

    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    y = bpy.context.object
    y.scale = (scale, scale, scale)
    y.rotation_euler[2] = face
    y.location = g2b(gx, gz, FLOOR + 0.10 * scale)   # HOVER_Y. 살짝 떠 있다
    return y


# ── 교전 배치 (FORMATION) ────────────────────────────────────
# 이 숫자가 "한 화면에 뭐가 들어와야 하는가"의 근거다. 근거는 코드 실측값이다.
#   요괴 정지거리 = ENEMY_ATK_RANGE 0.95 + 몸집 0.25 -> 약 1.2m (enemy.js)
#   칼끝 도달 = 캐릭터 앞 약 1.4m (main.js measureBlade 실측)
#   무리 반경 = GROUPS radius 1.4~2.6 (5마리면 2.6)
#   어그로 = 7.0m / 리쉬 = 16.0m / 무리 간격 >= 17m
#   이동 1.71 m/s, 달리기 3.20 m/s (CHAR_CFG)
# 배치(검사=플레이어 기준, +가 전방):
#   탱커  +2.2m 앞, 좌 1.6m   무리를 붙들고 있다. 요괴 정지거리 1.2 + 몸집
#   검사   0                   측면에서 벤다
#   궁수  -6.5m 뒤            요괴 사거리 밖 + 어그로 7m 안쪽에서 쏜다
#   무리   +4.0m 앞을 중심으로 반경 2.0 에 5마리
# => 전투가 차지하는 땅 = 앞 6.0m (무리 끝) ~ 뒤 6.5m (궁수) = 깊이 12.5m,
#    폭은 탱커 -1.6 ~ 측면 요괴 +2.6 = 약 7m. 여기에 지형을 읽을 여백을 더해
#    **최소 필요 지면 = 깊이 13m x 폭 18m** 이 나온다(폭은 16:9 라 저절로 따라온다).
FORMATION = [
    ("soldier.glb", -1.6, +2.2, 2.00),     # 탱커. CHAR_CFG.tank.h = 2.00
    ("slayer.glb", 0.0, 0.0, 1.75),        # 검사 = 플레이어. 카메라가 이쪽을 본다
    ("basic2.glb", +1.1, -6.5, 1.75),      # 궁수/힐러
]
MOB_CENTER = 4.0
MOB_R = 2.0
MOB_N = 5

SPOTS = {
    # (칸 c, 칸 r, 파티가 바라보는 방향각 rad. 0 = +Z, pi = -Z(북))
    # ★(14,15) 를 쓰면 안 된다. 남쪽 두 칸(r17~18,c13~16)이 건물('H')이라
    #   낮은 카메라(dist 11)에서 지붕이 화면 아래 절반을 가리고 플레이어가 안 보인다.
    #   서쪽으로 3칸 옮기면 남쪽 16m 가 트여서 후보끼리 같은 조건으로 비교된다.
    "plaza": (11, 15, math.pi),     # 중정 서쪽. 사방이 열린 넓은 마당
    "corridor": (12, 20, math.pi),  # 1칸(3.2m) 짜리 남북 통로. 양옆이 벽
    "boss": (14, 10, math.pi),      # 보스 마당 남쪽. 38.4 x 22.4m
    "gate": (14, 26, math.pi),      # 남문 마당, EXIT_1 앞
    "ford": (14, 13, math.pi),      # 개울 남쪽 앞터. 북쪽으로 여울목과 보스 공터가 보인다
    "bush": (10, 15, math.pi),      # 가운데 빈터 서쪽 입구. 양옆이 수풀
}
if SPOT_NAME.startswith("cell:"):
    # ★맵을 새로 구울 때마다 위 표가 낡는다(칸 하나가 벽이 되면 캐릭터가 벽에 박힌다).
    #   칸을 직접 넘기는 길을 열어 둔다: SPOT=cell:14:20 또는 cell:14:20:3.14
    _p = SPOT_NAME.split(":")
    SC, SR = int(_p[1]), int(_p[2])
    FACE = float(_p[3]) if len(_p) > 3 else math.pi
    SPOT_NAME = "cell%02d_%02d" % (SC, SR)
elif SPOT_NAME not in SPOTS:
    raise SystemExit("모르는 위치: %s (%s)" % (SPOT_NAME, list(SPOTS)))
else:
    SC, SR, FACE = SPOTS[SPOT_NAME]
# FACE 로 파티가 보는 방향을 덮어쓴다. 0 = +Z(카메라 쪽). yaw 0 카메라에서 정면이 된다.
# ★"얼굴이 보이나 정수리가 보이나"는 뒤통수만 찍어서는 판단이 안 된다.
#   플레이어가 카메라 쪽으로 걸어올 때를 찍어 봐야 각이 너무 낮은지 알 수 있다.
if os.environ.get("FACE") is not None:
    FACE = float(os.environ["FACE"])
PX, PZ = spot(SC, SR)


def fwd(dist_ahead, side):
    """파티 기준 로컬 좌표 -> 게임 좌표. 전방은 FACE 방향."""
    fx, fz = math.sin(FACE), math.cos(FACE)
    rx, rz = fz, -fx                       # 오른쪽
    return (PX + fx * dist_ahead + rx * side, PZ + fz * dist_ahead + rz * side)


def place_calib():
    """★검증용 자. 카메라 식과 화각이 맞는지 렌더로 확인하는 유일한 방법이다.
    빨간 기둥 = 정확히 1.75m (캐릭터 키). 화면 세로 대비 이 기둥의 픽셀 비가
    계산한 '캐릭%'와 같아야 한다. 흰 정육면체 = 전방 2m 간격, 노란색 = 좌우 2m 간격.
    자로 세어 보면 '보이는 지면 범위'가 계산과 맞는지 바로 안다."""
    def cube(gx, gz, col, size=0.3):
        bpy.ops.mesh.primitive_cube_add(size=size, location=g2b(gx, gz, FLOOR + size / 2))
        bpy.context.object.data.materials.append(yokai_mat("cal_" + col, CAL[col], emit=3.0))

    CAL = {"w": (1, 1, 1), "y": (1, 0.85, 0.1), "r": (1, 0.05, 0.05)}
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=CHAR_H,
                                        location=g2b(PX, PZ, FLOOR + CHAR_H / 2))
    bpy.context.object.data.materials.append(yokai_mat("cal_pole", CAL["r"], emit=4.0))
    for k in range(-8, 9):
        if k:
            gx, gz = fwd(k * 2.0, 0.0)
            cube(gx, gz, "w")
            gx, gz = fwd(0.0, k * 2.0)
            cube(gx, gz, "y")


if os.environ.get("CALIB") == "1":
    place_calib()

if WITH_PARTY:
    for glb, side, ahead, hh in FORMATION:
        gx, gz = fwd(ahead, side)
        place_char(glb, gx, gz, FACE, hh)
    print("[요괴] 무리 %d마리 (중심 %.1fm 앞, 반경 %.1f)" % (MOB_N, MOB_CENTER, MOB_R))
    for k in range(MOB_N):
        a = 2 * math.pi * k / MOB_N + 0.4
        rr = MOB_R * (0.45 + 0.55 * ((k * 7 % 5) / 4.0))
        gx, gz = fwd(MOB_CENTER + math.cos(a) * rr, math.sin(a) * rr)
        place_yokai(gx, gz, scale=0.78 + 0.18 * ((k * 3 % 5) / 4.0),
                    face=FACE + math.pi)
    print("[재질] 이미시브 차단 %d개" % kill_emission())


# ── 조명 ────────────────────────────────────────────────────
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.060, 0.078, 0.100, 1)
for nm, en, rot in (("SUN", 2.7, (34, 0, -38)), ("FILL", 1.0, (-52, 0, 140))):
    li = bpy.data.lights.new(nm, "SUN")
    li.energy = en
    li.angle = math.radians(6)
    so = bpy.data.objects.new(nm, li)
    so.rotation_euler = tuple(math.radians(a) for a in rot)
    sc.collection.objects.link(so)

cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.clip_start = 0.1
cd.clip_end = 400.0            # main.js 는 200 이다. 먼 후보를 보려고 여기만 늘렸다


# ── 지표 (렌더마다 같이 찍는다. 눈 판단만으로는 재현이 안 된다) ──
def metrics(pitch, dist, fov_deg, aspect):
    f = math.radians(fov_deg)
    half = f / 2
    H = TARGET_Y + math.sin(pitch) * dist
    # 캐릭터가 화면 세로의 몇 % 인가 (타깃 자리의 1.75m 수직선을 실제로 투영)
    camp = (TARGET_Y + math.sin(pitch) * dist, math.cos(pitch) * dist)   # (y, z)
    fy, fz = TARGET_Y - camp[0], -camp[1]
    n = math.hypot(fy, fz)
    fy, fz = fy / n, fz / n
    uy, uz = fz, -fy

    def py(y):
        vy, vz = y - camp[0], 0.0 - camp[1]
        return (vy * uy + vz * uz) / ((vy * fy + vz * fz) * math.tan(half))

    char = abs(py(CHAR_H) - py(0.0)) / 2 * 100
    a_bot, a_top = pitch + half, pitch - half
    d_bot = H / math.tan(a_bot)
    d_top = H / math.tan(a_top) if a_top > 1e-4 else float("inf")
    depth = d_top - d_bot
    slant_mid = math.hypot(H - TARGET_Y, math.cos(pitch) * dist)
    w_mid = 2 * slant_mid * math.tan(half) * aspect
    z_bot = math.hypot(H, d_bot) * math.cos(half)
    z_top = math.hypot(H, d_top) * math.cos(half) if d_top != float("inf") else float("inf")
    return char, depth, w_mid, (z_top / z_bot if z_top != float("inf") else float("inf")), H


aspect = RESX / float(RESY)
sc.render.resolution_x, sc.render.resolution_y = RESX, RESY
lines = []
LEAD = float(os.environ.get("LEAD", "1.25"))     # main.js CAM.lead
for tag, pitch, dist, fov, yaw in CAMS:
    # ★main.js 의 카메라 식을 그대로 옮긴다.
    #   camTarget = 캐릭터 위치에서 **보는 방향으로 lead 만큼 앞** (main.js 2088행)
    tx = PX - math.sin(yaw) * LEAD
    tz = PZ - math.cos(yaw) * LEAD
    tgt = (tx, TARGET_Y, tz)
    cx = tx + math.sin(yaw) * math.cos(pitch) * dist
    cz = tz + math.cos(yaw) * math.cos(pitch) * dist
    cy = TARGET_Y + math.sin(pitch) * dist
    cd.type = "PERSP"
    cd.sensor_fit = "VERTICAL"        # ★fov 는 세로 기준. AUTO 면 가로에 물려 크기가 달라진다
    cd.angle_y = math.radians(fov)
    cam.location = g2b(cx, cz, cy)
    d = g2b(tgt[0], tgt[2], tgt[1]) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    ch, dep, wm, dist_r, H = metrics(pitch, dist, fov, aspect)
    name = "%s_%s_p%.3f_d%.1f_f%02d_y%.2f" % (SPOT_NAME, tag, pitch, dist, fov, yaw)
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    line = ("%-9s pitch %.3f(%.1f도) dist %5.1f fov %2d yaw %.2f | "
            "캐릭 %5.2f%% 깊이 %5.1fm 폭 %5.1fm 왜곡 %.2f 카메높이 %5.1fm" %
            (tag, pitch, math.degrees(pitch), dist, fov, yaw, ch, dep, wm, dist_r, H))
    print("[렌더] " + line + " -> " + name + ".png")
    lines.append(line)

print("\n===== 지표 =====")
for l in lines:
    print(l)
print("DONE", OUT)
