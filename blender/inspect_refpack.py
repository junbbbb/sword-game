# -*- coding: utf-8 -*-
# 구매 에셋(ToonSoldiers WW2 demo) 구조 분석 + 렌더
# 실행: blender --background --python inspect_refpack.py
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
FBX = os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX")
TEX = os.path.join(PACK, "model/Materials/US_soldier_simple.tga")
REN = os.path.join(ROOT, "renders")
os.makedirs(REN, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
prop = sc.render.bl_rna.properties["engine"]
ids = [it.identifier for it in prop.enum_items]
for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    if cand in ids:
        sc.render.engine = cand
        break
try:
    sc.eevee.taa_render_samples = 64
except Exception:
    pass
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.055, 0.07, 1)

bpy.ops.import_scene.fbx(filepath=FBX)

# ---- 구조 리포트 ----
print("\n" + "=" * 70)
print("IMPORTED OBJECTS")
meshes = []
armatures = []
for ob in bpy.context.scene.objects:
    print("  %-38s type=%-9s parent=%s" % (ob.name, ob.type, ob.parent.name if ob.parent else "-"))
    if ob.type == "MESH":
        meshes.append(ob)
    if ob.type == "ARMATURE":
        armatures.append(ob)

for ob in meshes:
    me = ob.data
    print("\nMESH '%s'" % ob.name)
    print("  verts=%d  polys=%d  tris=%d" % (
        len(me.vertices), len(me.polygons), sum(len(p.vertices) - 2 for p in me.polygons)))
    print("  uv_layers=%s" % [l.name for l in me.uv_layers])
    print("  materials=%s" % [m.name if m else None for m in me.materials])
    print("  vertex_groups=%d" % len(ob.vertex_groups))
    print("  shape_keys=%s" % (len(me.shape_keys.key_blocks) if me.shape_keys else 0))

for arm in armatures:
    bones = arm.data.bones
    print("\nARMATURE '%s': %d bones" % (arm.name, len(bones)))
    for b in bones:
        print("    %s" % b.name)
print("=" * 70 + "\n")

# ---- 텍스처 적용 ----
img = bpy.data.images.load(TEX)
mat = bpy.data.materials.new("soldier_tex")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Closest"
diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
nt.links.new(tex.outputs[0], diff.inputs[0])
nt.links.new(diff.outputs[0], out.inputs[0])
for ob in meshes:
    ob.data.materials.clear()
    ob.data.materials.append(mat)

# ---- 바운딩 계산 ----
lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for ob in meshes:
    for c in ob.bound_box:
        wc = ob.matrix_world @ Vector(c)
        for i in range(3):
            lo[i] = min(lo[i], wc[i])
            hi[i] = max(hi[i], wc[i])
size = hi - lo
ctr = (hi + lo) / 2
print("BOUNDS lo=%s hi=%s size=%s" % (
    tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi), tuple(round(v, 3) for v in size)))
height = size.z
print("HEIGHT=%.3f" % height)

# 바닥
bpy.ops.mesh.primitive_plane_add(size=height * 12, location=(ctr.x, ctr.y, lo.z - 0.001))
fl = bpy.context.object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fnt = fm.node_tree
fnt.nodes.clear()
fo = fnt.nodes.new("ShaderNodeOutputMaterial")
fe = fnt.nodes.new("ShaderNodeEmission")
fe.inputs[0].default_value = (0.03, 0.035, 0.05, 1)
fnt.links.new(fe.outputs[0], fo.inputs[0])
fl.data.materials.append(fm)

# 라이트
li = bpy.data.lights.new("Sun", "SUN")
li.energy = 3.2
so = bpy.data.objects.new("Sun", li)
so.rotation_euler = (math.radians(55), 0, math.radians(-25))
bpy.context.collection.objects.link(so)
for nm, loc, en, col in (("rim", (-3, 3, 3), 400, (0.6, 0.8, 1.0)),
                         ("fill", (3, -3, 2), 220, (1, 1, 1))):
    al = bpy.data.lights.new(nm, "AREA")
    al.energy = en
    al.size = height * 2
    al.color = col
    ao = bpy.data.objects.new(nm, al)
    ao.location = (ctr.x + loc[0] * height * 0.5, ctr.y + loc[1] * height * 0.5, lo.z + loc[2] * height * 0.5)
    bpy.context.collection.objects.link(ao)
    d = Vector((ctr.x, ctr.y, ctr.z)) - ao.location
    ao.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 60
cam = bpy.data.objects.new("Cam", cam_d)
bpy.context.collection.objects.link(cam)
sc.camera = cam


def shoot(name, ang_deg, dist_mul=2.6, x=1000, y=1300):
    a = math.radians(ang_deg)
    d = height * dist_mul
    cam.location = (ctr.x + math.sin(a) * d, ctr.y - math.cos(a) * d, ctr.z + height * 0.12)
    v = Vector((ctr.x, ctr.y, ctr.z)) - cam.location
    cam.rotation_euler = v.to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = x
    sc.render.resolution_y = y
    sc.render.filepath = os.path.join(REN, name)
    bpy.ops.render.render(write_still=True)


shoot("06_refpack_front.png", 0)
shoot("06_refpack_side.png", 90)
shoot("06_refpack_back.png", 180)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender/refpack.blend"))
print("DONE")
