# -*- coding: utf-8 -*-
"""완성된 basic2.glb 의 베기 3종을 **실루엣 스트립**으로 뽑는다 (14-베기수정, 2026-08-12).

    blender -b -P blender/probe_moves_strip.py
    OUT=renders/history/v99_wave14/moves_fix/strip GLB=web/basic2.glb blender -b -P ...

왜 실루엣인가
  오너 지시가 "X 는 세로, C 는 가로, 투구 폼 금지"다. 셋 다 **형태**의 문제라
  색·재질이 오히려 눈을 흐린다. 워크벤치 FLAT 단색으로 굽고 프레임을 늘어놓으면
  "위->아래인가 옆->옆인가", "팔이 어깨 위로 감기나"가 한눈에 갈린다.

찍는 각
  front  캐릭터 정면(-Y 쪽에서)          = 좌우 스윙이 제일 잘 보인다
  side   캐릭터 오른쪽(+X 쪽에서)        = 위아래 스윙이 제일 잘 보인다
  game   게임 카메라와 같은 뒤 45도 위    = 오너가 실제로 보는 각

★캐릭터 정면은 -Y 다(발목->발끝·headfront 두 잣대로 실측 확인. probe_meshy_plane 참고).
"""
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.environ.get("GLB", os.path.join(ROOT, "web", "basic2.glb"))
OUT = os.environ.get("OUT", os.path.join(
    ROOT, "renders/history/v99_wave14/moves_fix/strip"))
CLIPS = [c for c in os.environ.get("CLIPS", "Attack,Heavy,Wide").split(",") if c]
NF = int(os.environ.get("NF", "12"))          # 클립당 장수
RES = int(os.environ.get("RES", "300"))
TAG = os.environ.get("TAG", "sil")
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath=GLB)

arm = next(o for o in sc.objects if o.type == "ARMATURE")
for o in list(sc.objects):
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        bpy.data.objects.remove(o, do_unlink=True)
# 게임은 1번 칼(SW_baekah)만 들려 준다. 나머지 칼은 숨긴다(실루엣이 지저분해진다)
KEEP_SW = os.environ.get("KEEP_SW", "SW_baekah")
for o in sc.objects:
    if o.type == "MESH" and o.name.startswith("SW_") and not o.name.startswith(KEEP_SW):
        o.hide_render = True

acts = {a.name: a for a in bpy.data.actions}
if arm.animation_data is None:
    arm.animation_data_create()

# ── 워크벤치 단색 실루엣 ──
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "FLAT"
sh.color_type = "SINGLE"
sh.single_color = (0.06, 0.06, 0.08)
sh.show_shadows = False
sh.show_cavity = False
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("W")
sc.world.color = (0.92, 0.93, 0.96)
sc.render.resolution_x = RES
sc.render.resolution_y = int(RES * 1.5)
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"

cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.lens = 50

# 캐릭터 키·중심 (레스트)
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
body = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith("SW_")]
zs, xs, ys = [], [], []
dg = bpy.context.evaluated_depsgraph_get()
for m in body:
    ev = m.evaluated_get(dg)
    for v in ev.data.vertices:
        w = m.matrix_world @ v.co
        zs.append(w.z); xs.append(w.x); ys.append(w.y)
H = max(zs) - min(zs)
CTR = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs) + H * 0.55))
arm.data.pose_position = "POSE"

# 앞 = -Y (실측). 오른쪽 = -X (왼쪽이 +X 였다)
VIEWS = {
    "front": Vector((0, -1, 0.10)),
    "side":  Vector((-1, 0, 0.10)),     # 캐릭터의 오른쪽에서
    "game":  Vector((0.0, 1.0, 0.95)),  # 뒤 위 45도 = 게임 카메라
}
DIST = H * 3.1


def shoot(path, view):
    d = VIEWS[view].normalized()
    cam.location = CTR + d * DIST
    dd = CTR - cam.location
    cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


for clip in CLIPS:
    act = acts.get(clip)
    if act is None:
        print("★없는 액션 %s (있는 것: %s)" % (clip, sorted(acts)))
        continue
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    n = min(NF, f1 - f0 + 1)
    frames = [f0 + round(i * (f1 - f0) / (n - 1)) for i in range(n)]
    print("[%s] f%d~%d (%.3f초) -> %d장 %s" % (clip, f0, f1, (f1 - f0) / 30.0,
                                              n, frames))
    for f in frames:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        for view in VIEWS:
            shoot(os.path.join(OUT, "%s_%s_%s_f%02d.png" % (TAG, clip, view, f)),
                  view)
print("[저장] %s" % OUT)
