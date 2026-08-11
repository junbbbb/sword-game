# -*- coding: utf-8 -*-
"""web/level1.glb 를 **다시 임포트해서** 검증 렌더를 찍는다.

★s20_level1.py 안에서 바로 렌더하지 않고 굳이 glb 를 다시 읽는 이유:
  텍스처가 제대로 구워졌는지, 좌표 변환(export_yup)이 안 뒤집혔는지,
  빠진 메시가 없는지는 "내보낸 파일"로만 확인할 수 있다.
  씬 메모리로 렌더하면 익스포트 버그를 통째로 못 본다.

실행: VIEWS=top blender -b -P blender/look_level1.py
      VIEWS=game1,game2,scale blender -b -P blender/look_level1.py
"""

import bpy
import os
import math
import json
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
OUT = os.environ.get("OUTDIR") or os.path.join(ROOT, "renders", "history", "v54_level1")
WANT = [v for v in os.environ.get("VIEWS", "top").split(",") if v]
os.makedirs(OUT, exist_ok=True)

LV = json.load(open(os.path.join(ROOT, "web", "level1.json"), encoding="utf-8"))
SIZE = LV["size"]["x"]

# ── main.js 카메라 값 (읽어서 그대로 옮겼다) ──────────────────
GAME_FOV = math.radians(46.0)   # PerspectiveCamera(46, ...) = 세로 화각
GAME_DIST = 7.0                 # 기본. 휠로 2.4~12
GAME_PITCH = 0.28               # 기본. 드래그로 -0.15~1.15
GAME_YAW = 0.55
CHAR_H = 1.75
TARGET_Y = CHAR_H * 0.62        # camTarget.setY(charH*0.62)

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"

bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "web", "level1.glb"))


def drop_importer_junk():
    """★glTF 임포터가 뼈 표시용 Icosphere(반지름 1)를 씬에 만든다. glb 안에는 없다.
    안 지우면 렌더에 구가 찍히고 치수 측정도 오염된다."""
    n = 0
    for o in list(bpy.context.scene.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)
            n += 1
    return n


print("[임포트] 잡동사니 제거 %d개" % drop_importer_junk())


def g2b(gx, gz, y=0.0):
    """게임(three.js) 좌표 -> 블렌더 좌표. three.z = -blender.y"""
    return Vector((gx, -gz, y))


# ── 소품 5종 (v69) ──────────────────────────────────────────
# ★rock·crag·thicket·tree·bush 는 level1.glb 에 **안 들어 있다.**
#   web/props/<종류>.glb 한 벌 + level1.json 의 props[] 배치로 나뉘어 있고
#   게임은 web/props.js 가 InstancedMesh 로 심는다. 여기서도 같은 규칙으로 심어야
#   검증 렌더가 실제 화면과 같은 그림이 된다(안 심으면 맵이 텅 비어 보인다).
PROPS_KIND_Y = {"rock": 1.0, "crag": 1.25, "thicket": 1.70, "tree": 1.0, "bush": 1.0}


def ground_y(gx, gz):
    """level.js groundY 와 같은 규칙. 낮은 단 위면 그 높이, 아니면 바닥."""
    y = LV["floorY"]
    for p in LV.get("platforms", []):
        if p["top"] <= y:
            continue
        if p["type"] == "circle":
            if (gx - p["x"]) ** 2 + (gz - p["z"]) ** 2 > p["r"] ** 2:
                continue
        elif abs(gx - p["x"]) > p["hx"] or abs(gz - p["z"]) > p["hz"]:
            continue
        y = p["top"]
    return y


def place_props():
    props = LV.get("props") or []
    if not props:
        return 0
    src = {}
    for kind in sorted(set(p["kind"] for p in props)):
        path = os.path.join(ROOT, "web", "props", kind + ".glb")
        if not os.path.exists(path):
            print("  [경고] %s 가 없다. s22_props.py 를 먼저 돌려라" % path)
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        drop_importer_junk()
        new = [o for o in bpy.data.objects
               if o not in before and o.type == "MESH"]
        if not new:
            continue
        base = new[0]
        # ★임포터가 Y-up -> Z-up 회전을 오브젝트 행렬에 걸어 놓는다. 그대로 두고
        #   메시 데이터만 복제하면 눕는다. 행렬을 메시에 구워 넣고 쓴다.
        bpy.ops.object.select_all(action="DESELECT")
        base.select_set(True)
        bpy.context.view_layer.objects.active = base
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        base.hide_render = True            # 원본은 안 그린다(복제본만 그린다)
        src[kind] = base
    n = 0
    for p in props:
        b = src.get(p["kind"])
        if not b:
            continue
        ob = bpy.data.objects.new("%s_%04d" % (p["kind"].upper(), n), b.data)
        sc.collection.objects.link(ob)
        s = p.get("scale", 1.0)
        ky = PROPS_KIND_Y.get(p["kind"], 1.0)
        ob.location = g2b(p["x"], p["z"], ground_y(p["x"], p["z"]))
        # three.js 의 Y축 회전 = 블렌더 Z축 회전(부호까지 같다. 위 좌표 대응에서 나온다)
        ob.rotation_euler = (0.0, 0.0, p.get("rotY", 0.0))
        ob.scale = (s, s, s * p.get("sy", 1.0) * ky)
        n += 1
    print("[소품] %d개 심음 (%s)" % (n, ", ".join(sorted(src))))
    return n


place_props()


# ── 캐릭터 배치 (스케일 확인용) ──────────────────────────────
def place_slayer(gx, gz, yaw=0.0):
    """slayer.glb 를 게임과 같은 크기(키 1.75)로 세운다.

    ★함정 두 개를 여기서 밟았다.
      1) 루트 아마추어 Bip001 에 **스케일 0.025 가 이미 박혀 있다.**
         o.scale = (s,s,s) 로 덮어쓰면 40배로 부풀어서 화면 밖으로 나가
         "캐릭터가 안 보인다"가 된다. 반드시 곱해야 한다.
      2) glb 안에 칼이 7자루 다 들어 있다(SW_*). main.js 는 하나만 켠다.
         전부 켠 채로 재면 가로 폭이 칼 길이로 잡힌다.
    """
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "web", "slayer.glb"))
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
        print("  [경고] 캐릭터 메시를 못 찾았다")
        return None

    def bbox():
        ws = [o.matrix_world @ v.co for o in body for v in o.data.vertices]
        return (min(p.x for p in ws), max(p.x for p in ws),
                min(p.y for p in ws), max(p.y for p in ws),
                min(p.z for p in ws), max(p.z for p in ws))

    x0, x1, y0, y1, z0, z1 = bbox()
    h = z1 - z0
    s = CHAR_H / h                      # main.js 1290행: s = cfg.h / h
    for o in roots:
        o.scale = tuple(v * s for v in o.scale)
        o.location = tuple(v * s for v in o.location)
        o.rotation_euler[2] = yaw
    bpy.context.view_layer.update()
    x0, x1, y0, y1, z0, z1 = bbox()
    for o in roots:
        o.location.x += gx - (x0 + x1) / 2
        o.location.y += (-gz) - (y0 + y1) / 2
        o.location.z += LV["floorY"] - z0
    bpy.context.view_layer.update()
    print("  캐릭터 (%.1f, %.1f) 원본키 %.3f x %.4f = %.3f" % (gx, gz, h, s, h * s))
    return h * s


# ── 조명 ────────────────────────────────────────────────────
def setup_world(bgcol, sun_e, fill_e):
    w = bpy.data.worlds.new("W") if sc.world is None else sc.world
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = bgcol
    for nm, en, rot in (("SUN", sun_e, (34, 0, -38)), ("FILL", fill_e, (-52, 0, 140))):
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


def aim(loc, tgt):
    cam.location = loc
    d = tgt - loc
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def render(name, rx, ry):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("  -> %s.png" % name)


def game_cam(gx, gz, dist=GAME_DIST, pitch=GAME_PITCH, yaw=GAME_YAW):
    """main.js 의 카메라 식을 그대로 옮긴다.
       cx = t.x + sin(yaw)cos(pitch)d / cy = t.y + sin(pitch)d / cz = t.z + cos(yaw)cos(pitch)d"""
    tgt = g2b(gx, gz, TARGET_Y)
    cx = gx + math.sin(yaw) * math.cos(pitch) * dist
    cz = gz + math.cos(yaw) * math.cos(pitch) * dist
    cy = TARGET_Y + math.sin(pitch) * dist
    cd.type = "PERSP"
    cd.sensor_fit = "VERTICAL"       # 세로 화각을 고정해야 main.js 와 크기가 같다
    cd.angle_y = GAME_FOV
    aim(g2b(cx, cz, cy), tgt)


# ── 시점 정의 ───────────────────────────────────────────────
BOSS = LV["boss"]
SP = {s["id"]: s for s in LV["spawns"]}
EX = {e["id"]: e for e in LV["exits"]}


def view_top():
    setup_world((0.30, 0.33, 0.38, 1), 2.3, 1.0)
    cd.type = "ORTHO"
    cd.ortho_scale = SIZE * 1.02
    aim(Vector((0, 0, 120)), Vector((0, 0, 0)))
    render("01_top_all", 1700, 1700)


def view_top_boss():
    setup_world((0.30, 0.33, 0.38, 1), 2.3, 1.0)
    cd.type = "ORTHO"
    cd.ortho_scale = 52
    a = BOSS["arena"]
    aim(g2b(a["x"], a["z"], 90), g2b(a["x"], a["z"], 0))
    render("02_top_boss", 1300, 1000)


def view_top_mid():
    setup_world((0.30, 0.33, 0.38, 1), 2.3, 1.0)
    cd.type = "ORTHO"
    cd.ortho_scale = 46
    aim(g2b(0, 8, 90), g2b(0, 8, 0))
    render("03_top_mid", 1300, 1100)


def view_game(tag, gx, gz, dist=GAME_DIST, pitch=GAME_PITCH, yaw=GAME_YAW, stand=True):
    # ★게임 톤(배경 0x05070d)을 그대로 쓰면 검증 렌더가 새까맣게 나와서 아무것도 못 본다.
    #   main.js 는 HemisphereLight 1.15 + Directional 2.0 + ACES + 블룸이라 실제 화면은
    #   훨씬 밝다. 여기서는 형태를 보는 게 목적이라 환경광을 올려 잡는다.
    setup_world((0.060, 0.078, 0.100, 1), 2.7, 1.0)
    if stand:
        place_slayer(gx, gz, -yaw)
    game_cam(gx, gz, dist, pitch, yaw)
    render(tag, 1280, 720)


GRID_ROWS = LV["grid"]
CELL = LV["cell"]
HALF = LV["size"]["x"] / 2.0


def spot(c, r):
    """칸 인덱스 -> 게임 좌표. ★걸을 수 없는 칸이면 소리 내서 알린다.
    처음에 눈대중으로 좌표를 찍었더니 캐릭터가 벽 속에 박혀서 화면이 새까맸다."""
    k = GRID_ROWS[r][c]
    if k in ("#", "H"):
        print("  [경고] (c%d r%d) 는 '%s' = 못 걷는 칸이다" % (c, r, k))
    return (-HALF + (c + 0.5) * CELL, -HALF + (r + 0.5) * CELL)


# ★v67 개방 레이아웃 기준. 맵을 다시 구울 때마다 여기가 낡는다(칸 하나가 벽이 되면
#   캐릭터가 벽에 박혀 화면이 새까맣게 나온다). 위 spot() 이 경고를 찍어 준다.
S_SPAWN1 = spot(4, 27)      # 남서 초원(스폰 바로 안쪽)
S_BOSS = spot(14, 8)        # 보스 마당, 제단 남쪽
S_CORR = spot(14, 10)       # 중앙 여울목 = 보스 마당 어귀
S_BUSH = spot(13, 13)       # 중앙 여울목 남쪽(양옆이 수풀)
S_PLAZA = spot(14, 19)      # 석탑 마당
S_SGATE = spot(14, 26)      # 남쪽 초원, EXIT_1 앞
S_LANE = spot(3, 18)        # 서쪽 초원 남북 길

VIEWS = {
    "top": view_top,
    "topboss": view_top_boss,
    "topmid": view_top_mid,
    # 게임 기본 시점(pitch 0.28 / dist 7)
    "g_spawn": lambda: view_game("10_game_spawn1", *S_SPAWN1, yaw=0.35),
    "g_boss": lambda: view_game("11_game_boss", *S_BOSS, yaw=math.pi),
    "g_corridor": lambda: view_game("12_game_corridor", *S_CORR, yaw=1.62),
    "g_bush": lambda: view_game("13_game_bush", *S_BUSH, yaw=1.62),
    "g_plaza": lambda: view_game("14_game_plaza", *S_PLAZA, yaw=0.55),
    "g_lane": lambda: view_game("18_game_lane", *S_LANE, yaw=math.pi),
    # 가장 탑다운에 가까운 자리(드래그 상한 pitch 1.15 / 휠 상한 dist 12)
    "g_top": lambda: view_game("15_gametop_plaza", *S_BUSH, dist=12.0, pitch=1.15,
                               yaw=0.55),
    "g_topboss": lambda: view_game("16_gametop_boss", *S_BOSS, dist=12.0, pitch=1.15,
                                   yaw=math.pi),
    "g_gate": lambda: view_game("17_game_gate", *S_SGATE, dist=9.0, pitch=0.60, yaw=0.0),
}

for k in WANT:
    fn = VIEWS.get(k)
    if not fn:
        print("[경고] 모르는 시점: %s" % k)
        continue
    print("[렌더] %s" % k)
    fn()
print("DONE", OUT)
