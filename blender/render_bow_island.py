# -*- coding: utf-8 -*-
"""등짐 활 후보를 색칠하거나 지워서 **눈으로 확인**하는 렌더 도구.

특정 자체는 blender/probe_bow_final.py 가 한다. 이건 그 결과를 보는 자리다.
  a_tex_*   원본 질감 그대로
  b_mark_*  등 뒤 후보 아일랜드마다 다른 색
  c_del_*   BOW_DEL 로 준 성분을 지운 판(몸에 구멍이 나는지 = 잘못 지웠는지)

★"등 뒤 최대 아일랜드가 활" 이라는 전제는 틀렸다. 그건 머리카락이다(probe_bow_final 머리말).
  그래서 이 스크립트의 후보 목록(모든 정점 y>0 인 큰 성분)은 **활 목록이 아니다.**
  활을 지운 판을 보려면 BOW_DEL 에 probe_bow_final 이 준 목록을 넣어라.

실행: blender --background --python blender/render_bow_island.py
환경변수: BOW_DEL="3466,3582"  지울 성분 root (c_del 렌더용)
          BOW_OUTDIR          출력 폴더
"""
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming/meshy2/Meshy_AI_Moonshadow_Ranger_biped")
BASE = "Meshy_AI_Moonshadow_Ranger_biped_Animation_%s_withSkin.glb"
OUT = os.environ.get("BOW_OUTDIR", os.path.join(ROOT, "renders/v99_wave21_bow"))
os.makedirs(OUT, exist_ok=True)
DEL = [int(x) for x in os.environ.get("BOW_DEL", "3466").split(",") if x.strip()]

# 후보별 색(구분이 되게 순색으로). probe 가 뽑은 순서와 같다.
PALETTE = [
    (1.0, 0.05, 0.05, 1), (0.05, 0.45, 1.0, 1), (0.15, 1.0, 0.15, 1),
    (1.0, 0.85, 0.0, 1), (1.0, 0.2, 0.9, 1), (0.0, 0.95, 0.95, 1),
    (1.0, 0.5, 0.0, 1), (0.6, 0.3, 1.0, 1), (0.5, 1.0, 0.0, 1),
    (0.9, 0.9, 0.9, 1), (0.4, 0.2, 0.05, 1), (0.0, 0.4, 0.25, 1),
]


def build():
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, BASE % "Walking_Woman"))
    for o in list(sc.objects):
        if o.type == "MESH" and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o, do_unlink=True)
    arm = next(o for o in sc.objects if o.type == "ARMATURE")
    mesh = next(o for o in sc.objects if o.type == "MESH")
    arm.data.pose_position = "REST"
    # 액션이 붙어 있으면 REST 여도 프레임에 따라 흔들린다. 끊는다.
    if arm.animation_data:
        arm.animation_data.action = None
    bpy.context.view_layer.update()
    return sc, arm, mesh


def components(me):
    NV = len(me.vertices)
    par = list(range(NV))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for p in me.polygons:
        vs = list(p.vertices)
        r = find(vs[0])
        for v in vs[1:]:
            rb = find(v)
            if rb != r:
                par[rb] = r
    return find


def setup_render(sc, tag, ortho, loc, rot):
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE" if tag == "tex" else "MATERIAL"
    sc.display.shading.show_shadows = False
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 700
    sc.render.resolution_y = 900
    sc.render.film_transparent = False
    sc.world = bpy.data.worlds.new("W")
    sc.world.color = (0.10, 0.11, 0.13)
    cam = bpy.data.objects.get("CAM")
    if cam is None:
        cd = bpy.data.cameras.new("CAM")
        cam = bpy.data.objects.new("CAM", cd)
        sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ortho
    cam.location = loc
    cam.rotation_euler = rot
    sc.camera = cam


# 시점: Blender 규약 = 정면 -Y, 위 +Z, 캐릭터 오른쪽 -X
#   back  = 등 뒤에서(+Y 에서 -Y 를 본다)
#   side  = 캐릭터의 왼쪽(+X)에서 본 옆모습. 등이 오른쪽에 온다
#   q34   = 뒤-왼쪽 45도
VIEWS = {
    "back": ((0.0, 3.0, 0.95), (math.radians(90), 0, math.radians(180))),
    "side": ((3.0, 0.0, 0.95), (math.radians(90), 0, math.radians(90))),
    "q34":  ((2.1, 2.1, 1.10), (math.radians(90), 0, math.radians(135))),
}


def shoot(sc, prefix, tag):
    for vn, (loc, rot) in VIEWS.items():
        setup_render(sc, tag, 2.0, Vector(loc), rot)
        sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (prefix, vn))
        bpy.ops.render.render(write_still=True)
        print("  saved", sc.render.filepath)


# ---------------------------------------------------------------- a) 원본 질감
sc, arm, mesh = build()
shoot(sc, "a_tex", "tex")

# ---------------------------------------------------------------- b) 후보 색칠
sc, arm, mesh = build()
me = mesh.data
find = components(me)
# probe 가 준 후보 목록을 그대로 다시 계산한다(파일 의존 없이 자립)
comp = {}
for i in range(len(me.vertices)):
    comp.setdefault(find(i), []).append(i)
mw = mesh.matrix_world
WP = [mw @ v.co for v in me.vertices]
cands = []
for r, idx in comp.items():
    if len(idx) < 25:
        continue
    if min(WP[i].y for i in idx) <= 0.0:      # 등 뒤(+Y)에만 있는 성분만
        continue
    cands.append((len(idx), r))
cands.sort(reverse=True)
print("[후보]", [(r, n) for n, r in cands])


def plain(name, rgba, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = False
    m.diffuse_color = rgba
    m.roughness = rough
    return m


me.materials.clear()
me.materials.append(plain("BODY", (0.30, 0.30, 0.33, 1)))
slot_of = {}
for k, (n, r) in enumerate(cands):
    me.materials.append(plain("C%d" % r, PALETTE[k % len(PALETTE)]))
    slot_of[r] = k + 1
for p in me.polygons:
    p.material_index = slot_of.get(find(p.vertices[0]), 0)
shoot(sc, "b_mark", "mat")
print("[색표] " + " / ".join(
    "%s=root %d(%d정점)" % (["빨강", "파랑", "초록", "노랑", "자홍", "청록",
                             "주황", "보라", "연두", "흰색", "갈색", "짙초록"][k],
                            r, n)
    for k, (n, r) in enumerate(cands)))

# ---------------------------------------------------------------- c) 지운 판
sc, arm, mesh = build()
me = mesh.data
find = components(me)
kill = set()
for p in me.polygons:
    if find(p.vertices[0]) in DEL:
        kill.add(p.index)
print("[삭제] root %s -> 면 %d개" % (DEL, len(kill)))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.object.mode_set(mode="OBJECT")
for i in kill:
    me.polygons[i].select = True
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.delete(type="VERT")
bpy.ops.object.mode_set(mode="OBJECT")
print("[삭제후] 정점 %d 면 %d" % (len(me.vertices), len(me.polygons)))
shoot(sc, "c_del", "tex")
print("완료:", OUT)
