# -*- coding: utf-8 -*-
"""걷기·달리기 **팔 스윙**을 눈으로 본다 (13-걷기팔). before/after 같은 카메라.

    GLB=web/basic2.glb TAG=before OUTDIR=renders/history/v99_wave13/walkarm/before \
      blender -b -P blender/render_walkarm_ab.py

★카메라를 캐릭터에 고정한다(모델 원점 기준). 클립마다 골반이 움직이므로 프레임마다
  카메라를 다시 잡으면 before/after 가 다른 그림이 된다. 여기서는 **레스트 골반**을
  기준으로 한 번만 잡는다.
★뒤로 뺀 팔은 **옆면**에서 제일 잘 보인다(오른쪽 옆 = 칼 든 쪽). 그래서 옆면을
  기본으로 하고 앞·뒤·위를 같이 찍는다.

손잡이: GLB / TAG / OUTDIR / CLIPS(기본 Walk,Run) / NF(클립당 프레임 수, 기본 8)
        VIEWS(기본 sideR,sideL,front,top)
"""
import bpy
import os
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.environ.get("GLB") or os.path.join(ROOT, "web", "basic2.glb")
if not os.path.isabs(GLB):
    GLB = os.path.join(ROOT, GLB)
TAG = os.environ.get("TAG", "x")
OUTDIR = os.environ.get("OUTDIR") or os.path.join(
    ROOT, "renders", "history", "v99_wave13", "walkarm", TAG)
CLIPS = [c.strip() for c in os.environ.get("CLIPS", "Walk,Run").split(",") if c.strip()]
VIEWS = [v.strip() for v in os.environ.get(
    "VIEWS", "sideR,sideL,front,top").split(",") if v.strip()]
NF = int(os.environ.get("NF", "8"))
RES = int(os.environ.get("RES", "420"))
os.makedirs(OUTDIR, exist_ok=True)

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath=GLB)
if sc.render.fps != 30:
    sc.render.fps = 30
arm = next(o for o in sc.objects if o.type == "ARMATURE")
for o in list(sc.objects):                        # ★뼈 표시용 Icosphere
    if o.type == "MESH" and (o.name.startswith("Icosphere")
                             or any(c.name == "glTF_not_exported"
                                    for c in o.users_collection)):
        bpy.data.objects.remove(o, do_unlink=True)
MESH = [o for o in sc.objects if o.type == "MESH"]
BODY = [o for o in MESH if not o.name.startswith(("SW_", "SH_"))]
# 게임 시작 칼(1번 nokseun)만 남긴다. 일곱 자루가 겹치면 실루엣을 못 본다.
for o in MESH:
    if o.name.startswith("SW_") and "nokseun" not in o.name:
        o.hide_render = True

for b in arm.pose.bones:
    b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
zs, xs, ys = [], [], []
for o in BODY:
    for v in o.data.vertices:
        p = o.matrix_world @ v.co
        zs.append(p.z)
        xs.append(p.x)
        ys.append(p.y)
H = max(zs) - min(zs)
CEN = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs) + H * 0.55))
arm.data.pose_position = "POSE"

# ---------------------------------------------------------------- 조명·바닥
mat = bpy.data.materials.new("floor")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (.18, .18, .2, 1)
bpy.ops.mesh.primitive_plane_add(size=H * 8, location=(CEN.x, CEN.y, min(zs)))
bpy.context.object.data.materials.append(mat)
for loc, e in (((3, -4, 5), 900), ((-4, -2, 3), 400), ((0, 5, 4), 300)):
    bpy.ops.object.light_add(type="AREA", location=(CEN.x + loc[0] * H / 2,
                                                    CEN.y + loc[1] * H / 2,
                                                    min(zs) + loc[2] * H / 2))
    lt = bpy.context.object.data
    lt.energy = e * H * H
    lt.size = H
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.film_transparent = False
if sc.world is None:                              # ★빈 홈파일에는 월드가 없다
    sc.world = bpy.data.worlds.new("W")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (.05, .05, .07, 1)

cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
D = H * 2.1
PELVIS = "Bip001 Pelvis"


def look(pos, tgt):
    cam.location = pos
    d = (tgt - pos)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


# ★캐릭터는 월드 **-Y** 를 본다(실측: 발->발끝·얼굴 방향). 그래서 오른쪽 옆은 -X 다.
#   여기를 반대로 잡으면 칼 든 팔이 몸에 가려 아무것도 안 보인다(첫 판에서 밟았다).
VIEWPOS = {
    "sideR": Vector((-D, 0, H * 0.10)),       # 오른쪽 옆 = 칼 든 쪽
    "sideL": Vector((D, 0, H * 0.10)),
    "front": Vector((0, -D, H * 0.10)),
    "back": Vector((0, D, H * 0.10)),
    "top": Vector((0, 0.01, D * 0.9)),
}


def use(act):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    if hasattr(act, "slots") and len(act.slots):
        try:
            ad.action_slot = act.slots[0]
        except Exception:
            pass


try:                                          # ★블렌더 번들 파이썬엔 PIL 이 없다
    from PIL import Image                      # noqa: E402
except ImportError:                            # 시트는 시스템 python3 로 따로 붙인다
    Image = None

for nm in CLIPS:
    act = bpy.data.actions.get(nm)
    if not act:
        continue
    use(act)
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    frames = [f0 + int(round(i * (f1 - f0) / float(NF))) for i in range(NF)]
    for vw in VIEWS:
        tiles = []
        for f in frames:
            sc.frame_set(f)
            bpy.context.view_layer.update()
            # ★프레임마다 골반 위치를 따라간다(클립이 제자리가 아니다). before/after 가
            #   같은 골반을 쓰므로 A/B 비교는 그대로 성립한다.
            pv = (arm.matrix_world @ arm.pose.bones[PELVIS].matrix).translation
            tgt = Vector((pv.x, pv.y, CEN.z))
            look(tgt + VIEWPOS[vw], tgt)
            p = os.path.join(OUTDIR, "%s_%s_f%02d.png" % (nm, vw, f))
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            tiles.append(p)
        sp = os.path.join(OUTDIR, "SHEET_%s_%s_%s.png" % (nm, vw, TAG))
        if Image:
            sheet = Image.new("RGB", (RES * len(tiles), RES), (10, 10, 12))
            for i, t in enumerate(tiles):
                sheet.paste(Image.open(t).convert("RGB"), (i * RES, 0))
            sheet.save(sp)
        else:
            with open(sp + ".txt", "w") as fp:
                fp.write("\n".join(tiles))
        print("[시트] %s" % sp)
print("[끝] %s" % OUTDIR)
