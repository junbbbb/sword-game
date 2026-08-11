# -*- coding: utf-8 -*-
# 루즈 파츠를 색으로 구분해 렌더 (군장비 식별용)
import bpy
import bmesh
from mathutils import Vector

SCR = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.1, 0.1, 0.12, 1)

bpy.ops.import_scene.fbx(
    filepath="/Users/lbj/Documents/gameproject/refpack/Assets/ToonSoldiers_WW2_demo/model/ToonSoldier_WW2_demo.FBX")
mo = [o for o in sc.objects if o.type == "MESH"][0]
me = mo.data

bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()

seen = set()
comps = []          # 인덱스 리스트로 저장(BMVert 참조는 머티리얼 추가 시 무효화됨)
coords = {v.index: v.co.copy() for v in bm.verts}
adj = {v.index: [e.other_vert(v).index for e in v.link_edges] for v in bm.verts}
face_first = {f.index: f.verts[0].index for f in bm.faces}
for vi in coords:
    if vi in seen:
        continue
    stack = [vi]
    comp = []
    seen.add(vi)
    while stack:
        c = stack.pop()
        comp.append(c)
        for o in adj[c]:
            if o not in seen:
                seen.add(o)
                stack.append(o)
    comps.append(comp)
comps.sort(key=lambda c: -len(c))
bm.free()

NAMES = ["grey", "RED", "GREEN", "BLUE", "YELLOW", "MAGENTA", "CYAN", "ORANGE",
         "PURPLE", "DKGREEN", "BROWN", "PINK", "LTBLUE", "LIME", "AQUA", "ROSE"]
COLS = [(0.55, 0.55, 0.55), (1, 0, 0), (0, 1, 0), (0, 0.35, 1), (1, 1, 0), (1, 0, 1),
        (0, 1, 1), (1, 0.5, 0), (0.55, 0, 1), (0, 0.45, 0), (0.6, 0.35, 0.12),
        (1, 0.65, 0.75), (0.45, 0.65, 1), (0.7, 1, 0.25), (0.35, 1, 0.8), (1, 0.35, 0.55)]

me2 = me
me2.materials.clear()
for i, c in enumerate(COLS):
    m = bpy.data.materials.new("c%d" % i)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*c, 1)
    nt.links.new(em.outputs[0], out.inputs[0])
    me2.materials.append(m)

vert2comp = {}
for ci, comp in enumerate(comps):
    for vi in comp:
        vert2comp[vi] = min(ci, len(COLS) - 1)
for p in me2.polygons:
    p.material_index = vert2comp[me2.loops[p.loop_start].vertex_index]
me2.update()

print("parts sorted by size:")
for ci, comp in enumerate(comps[:16]):
    xs = [coords[vi].x for vi in comp]
    ys = [coords[vi].y for vi in comp]
    zs = [coords[vi].z for vi in comp]
    print("  %-8s verts=%-4d x[%6.1f,%6.1f] y[%5.1f,%5.1f] z[%5.1f,%5.1f]"
          % (NAMES[min(ci, 15)], len(comp), min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

cam_d = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam_d.lens = 55


def shoot(name, loc, tgt):
    cam.location = loc
    d = Vector(tgt) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = 800
    sc.render.resolution_y = 1100
    sc.render.filepath = SCR + "/" + name
    bpy.ops.render.render(write_still=True)


shoot("parts_front.png", (0.3, -6.5, 1.35), (0, 0, 1.3))
shoot("parts_back.png", (0.3, 6.5, 1.35), (0, 0, 1.3))
print("saved")
