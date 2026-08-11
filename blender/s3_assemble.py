# -*- coding: utf-8 -*-
# [3/3] 조립: 텍스처 적용 + 세움깃 + 하오리 + 짧은 머리 + 카타나 + 포즈 + 렌더(history)
# 실행: blender --background --python s3_assemble.py
import bpy
import os
import sys
import json
import math
import shutil
import time
import random
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
SCR = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad"
REN = os.path.join(ROOT, "renders")
HIST = os.path.join(REN, "history")
os.makedirs(HIST, exist_ok=True)
RUN = time.strftime("%m%d_%H%M%S")

sys.path.insert(0, BLD)
import build_scenes as BS

lm = json.load(open(os.path.join(SCR, "paint_data.json")))["lm"]
hx0, hx1, hy0, hy1, hz0, hz1 = lm["head_box"]
head_w = hx1 - hx0
head_h = hz1 - hz0
head_d = hy1 - hy0
eye_z = lm["eye_z"]

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer_base.blend"))
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
try:
    sc.eevee.taa_render_samples = 64
except Exception:
    pass
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.020, 0.023, 0.032, 1)

mesh_ob = next(o for o in sc.objects if o.type == "MESH")
arm_ob = next(o for o in sc.objects if o.type == "ARMATURE")
me = mesh_ob.data
IMP_SCALE = arm_ob.matrix_world.to_scale().x     # 0.0254 (인치->미터)

# ---------------- 텍스처 ----------------
img = bpy.data.images.load(os.path.join(ROOT, "refpack/demon_slayer_tex.png"))
mat = bpy.data.materials.new("slayer_tex")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
nt.links.new(tex.outputs[0], diff.inputs[0])
nt.links.new(diff.outputs[0], out.inputs[0])
me.materials.clear()
me.materials.append(mat)

# ---------------- 본 헬퍼 ----------------
def pbone(key):
    for b in arm_ob.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


def bone_world(key):
    b = pbone(key)
    return arm_ob.matrix_world @ b.matrix if b else None


def attach(ob, bone_key, keep_world=True):
    b = pbone(bone_key)
    bpy.context.view_layer.update()          # .location 등 대입 직후의 stale 행렬 방지
    mw = ob.matrix_world.copy()
    con = ob.constraints.new("CHILD_OF")
    con.target = arm_ob
    con.subtarget = b.name
    con.inverse_matrix = (arm_ob.matrix_world @ b.matrix).inverted()
    if keep_world:
        ob.matrix_basis = mw                 # T @ T^-1 @ basis = basis 이므로 basis=원하던 월드
    bpy.context.view_layer.update()


def L2W(p):
    """메시 로컬 -> 월드"""
    return mesh_ob.matrix_world @ Vector(p)


# ---------------- 포즈 ----------------
A2W = arm_ob.matrix_world
W2A = A2W.inverted()


def swing(key, axis_world, deg):
    b = pbone(key)
    if b is None:
        return
    ax = (W2A.to_3x3() @ Vector(axis_world)).normalized()
    head = b.matrix.translation.copy()
    R = Matrix.Rotation(math.radians(deg), 4, ax)
    b.matrix = Matrix.Translation(head) @ R @ Matrix.Translation(-head) @ b.matrix
    bpy.context.view_layer.update()


def E(n, d):
    return float(os.environ.get(n, d))


swing("l upperarm", (0, 1, 0), E("P_LUA", "75"))
swing("l forearm", (0, 1, 0), E("P_LFA", "10"))
swing("r upperarm", (0, 1, 0), E("P_RUA", "-52"))
swing("r forearm", (0, 1, 0), E("P_RFA", "-58"))
swing("r forearm", (1, 0, 0), E("P_RFA2", "-28"))

# ---------------- 하오리 ----------------
# (세움깃은 텍스처로 충분해서 지오메트리 생략)
# 배치는 전부 "메시 로컬 단위"로 계산해서 L2W 로 넘긴다(단위 혼동 금지).
HAORI_ON = os.environ.get("HAORI", "1") != "0"
m_haori = BS.cel_mat("haoriG", "#0f4c53", ramp_pos=0.32, shadow_mul=0.55, soft=0.26)
m_haori_in = BS.cel_mat("haoriIn", "#083038", ramp_pos=0.32, shadow_mul=0.6, soft=0.26)

ty0, ty1 = lm["torso_y"]              # 몸통 앞뒤(로컬)
txm = lm["torso_xm"]                  # 몸통 반폭(로컬)
arm_r = lm["arm_r"]                   # 팔 반경(로컬)
hip_z = lm["pelvis_z"]
knee_z = hip_z * 0.52
sh_top_z = lm["collar"][0]
coat_h = (sh_top_z - knee_z) * IMP_SCALE

if not HAORI_ON:
    print("haori: OFF")
hb = BS.taper_box("haoriBk", (txm * 2 + 3.0) * IMP_SCALE, 1.6 * IMP_SCALE,
                  (txm * 2 + 7.5) * IMP_SCALE, 1.8 * IMP_SCALE, coat_h, origin="top",
                  mat=m_haori, bevel=0.015, seg=3, smooth=True)
hb.location = L2W((0, ty1 + 1.4, sh_top_z))
attach(hb, "spine")

for sgn, side in ((-1, "L"), (1, "R")):
    # 앞판: 몸 앞면의 "옆쪽"에 걸쳐 가운데(단추·벨트)를 비운다
    hf = BS.taper_box("haoriF" + side, (txm * 0.60) * IMP_SCALE, 1.5 * IMP_SCALE,
                      (txm * 0.70) * IMP_SCALE, 1.7 * IMP_SCALE, coat_h * 0.97, origin="top",
                      mat=m_haori, bevel=0.015, seg=3, smooth=True)
    hf.location = L2W((sgn * txm * 0.86, ty0 - 1.1, sh_top_z))
    hf.rotation_euler = (math.radians(-3), 0, sgn * math.radians(-3))
    attach(hf, "spine")
    # 안감 라인: 앞판 안쪽 모서리에 딱 붙는 얇은 스트립
    tr = BS.taper_box("haoriTr" + side, (txm * 0.13) * IMP_SCALE, 1.6 * IMP_SCALE,
                      (txm * 0.13) * IMP_SCALE, 1.8 * IMP_SCALE, coat_h * 0.97, origin="top",
                      mat=m_haori_in, bevel=0.008, seg=2, smooth=True)
    tr.location = L2W((sgn * txm * 0.52, ty0 - 1.35, sh_top_z))
    tr.rotation_euler = (math.radians(-3), 0, sgn * math.radians(-3))
    attach(tr, "spine")

# 하오리 소매(통소매, 팔 실측 반경에 상한)
arm_r_use = min(arm_r, 3.4)
for side in ("L", "R"):
    ub = bone_world("%s upperarm" % side.lower())
    fb = bone_world("%s forearm" % side.lower())
    if ub is None or fb is None:
        continue
    a = ub.translation
    c = fb.translation
    mid = a * 0.38 + c * 0.62
    axis = (c - a)
    ln = axis.length * 1.15
    r0 = (arm_r_use * 1.30) * IMP_SCALE
    r1 = (arm_r_use * 1.70) * IMP_SCALE
    slv = BS.tcyl("hslv" + side, r0, r1, ln, mat=m_haori, origin="center",
                  verts=18, squash_y=0.95)
    q = axis.normalized().to_track_quat("Z", "Y")
    slv.rotation_euler = q.to_euler()
    slv.location = mid
    attach(slv, "%s upperarm" % side.lower())

if not HAORI_ON:
    for ob in list(sc.objects):
        if ob.name.startswith(("haori", "hslv")):
            bpy.data.objects.remove(ob, do_unlink=True)

# ---------------- 짧은 머리(단정) ----------------
m_hair = BS.cel_mat("hairG", "#33202e", ramp_pos=0.34, shadow_mul=0.55, soft=0.24)
head_top = L2W((0, (hy0 + hy1) / 2 * 0 + 0.0, hz1))
head_ctr_l = ((hx0 + hx1) / 2, (hy0 + hy1) / 2, hz0 + head_h * 0.55)

# 스컬 캡
import bmesh as _bm
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=22, radius=1.0, location=(0, 0, 0))
cap = bpy.context.object
cap.name = "hair_cap"
cme = cap.data
bmh = _bm.new()
bmh.from_mesh(cme)
kill = [v for v in bmh.verts if v.co.z < -0.25 or (v.co.y < -0.42 and v.co.z < 0.42)]
_bm.ops.delete(bmh, geom=kill, context="VERTS")
bmh.to_mesh(cme)
bmh.free()
for v in cme.vertices:
    v.co.x *= head_w * 0.565 * IMP_SCALE
    v.co.y *= head_d * 0.585 * IMP_SCALE
    v.co.z *= head_h * 0.56 * IMP_SCALE
for p in cme.polygons:
    p.use_smooth = True
cme.materials.append(m_hair)
cap.location = L2W((head_ctr_l[0], head_ctr_l[1] + head_d * 0.02, head_ctr_l[2] + head_h * 0.06))
attach(cap, "bip001 head")

rng = random.Random(11)
hairs = []
# 앞머리: 이마 위에서 끝나는 짧은 지그재그 (눈 안 가림)
n_b = 7
fringe_y = hy0 + head_d * 0.06
fringe_top = hz0 + head_h * 0.92
fringe_bot = eye_z + head_h * 0.16
for i in range(n_b):
    t = (i / (n_b - 1)) - 0.5
    x = head_ctr_l[0] + t * head_w * 0.74
    ln = (fringe_top - fringe_bot) * (0.85 + rng.random() * 0.3)
    p0 = (x * 0.9, fringe_y + head_d * 0.10, fringe_top)
    p1 = (x, fringe_y, fringe_top - ln * 0.55)
    p2 = (x * 1.03, fringe_y + head_d * 0.02, fringe_top - ln)
    lk = BS.hair_lock("fr%d" % i, [L2W(p0), L2W(p1), L2W(p2)], [1.0, 0.72, 0.0],
                      m_hair, head_w * 0.052 * IMP_SCALE)
    hairs.append(lk)
# 옆머리(귀 위 짧게)
for sgn in (-1, 1):
    p0 = (head_ctr_l[0] + sgn * head_w * 0.40, hy0 + head_d * 0.28, hz0 + head_h * 0.86)
    p1 = (head_ctr_l[0] + sgn * head_w * 0.52, hy0 + head_d * 0.22, hz0 + head_h * 0.58)
    p2 = (head_ctr_l[0] + sgn * head_w * 0.55, hy0 + head_d * 0.26, hz0 + head_h * 0.40)
    lk = BS.hair_lock("side%d" % sgn, [L2W(p0), L2W(p1), L2W(p2)], [1.0, 0.7, 0.0],
                      m_hair, head_w * 0.05 * IMP_SCALE)
    hairs.append(lk)
# 뒷머리 목덜미
n_k = 6
for i in range(n_k):
    t = (i / (n_k - 1)) - 0.5
    x = head_ctr_l[0] + t * head_w * 0.62
    p0 = (x * 0.9, hy1 - head_d * 0.30, hz0 + head_h * 0.72)
    p1 = (x, hy1 - head_d * 0.12, hz0 + head_h * 0.42)
    p2 = (x * 0.96, hy1 - head_d * 0.20, hz0 + head_h * 0.22)
    lk = BS.hair_lock("bk%d" % i, [L2W(p0), L2W(p1), L2W(p2)], [1.0, 0.7, 0.0],
                      m_hair, head_w * 0.05 * IMP_SCALE)
    hairs.append(lk)
# 크라운 뻗침 약간
for i in range(4):
    t = (i / 3.0) - 0.5
    x = head_ctr_l[0] + t * head_w * 0.5
    p0 = (x, (hy0 + hy1) / 2, hz1 - head_h * 0.05)
    p1 = (x * 1.3, (hy0 + hy1) / 2 + head_d * 0.16, hz1 + head_h * (0.10 + rng.random() * 0.06))
    lk = BS.hair_lock("cr%d" % i, [L2W(p0), L2W(p1)], [0.9, 0.0],
                      m_hair, head_w * 0.045 * IMP_SCALE)
    hairs.append(lk)
for h in hairs:
    attach(h, "bip001 head")

# ---------------- 카타나 ----------------
zs = [(mesh_ob.matrix_world @ v.co).z for v in me.vertices]
height = max(zs) - min(zs)
katana = BS.build_katana(tag="slayer", scale=height * 0.44, width_mul=2.4)
hb_w = bone_world("r hand")
loc, rotq, _ = hb_w.decompose()
M_norm = Matrix.Translation(loc) @ rotq.to_matrix().to_4x4()
bx, by, bz = E("K_BX", "0.15"), E("K_BY", "-0.50"), E("K_BZ", "0.84")
fwd = Vector((bx, by, bz)).normalized()
ref = Vector((0, 0, 1)) if abs(fwd.z) < 0.95 else Vector((0, 1, 0))
side_v = fwd.cross(ref).normalized()
up_v = side_v.cross(fwd).normalized()
R = Matrix((fwd, side_v, up_v)).transposed().to_4x4()
katana.matrix_world = Matrix.Translation(loc + fwd * height * 0.03) @ R
attach(katana, "r hand")

# ---------------- 씬/렌더 ----------------
lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for v in me.vertices:
    wc = mesh_ob.matrix_world @ v.co
    for i in range(3):
        lo[i] = min(lo[i], wc[i])
        hi[i] = max(hi[i], wc[i])
ctr = (hi + lo) / 2
H = hi.z - lo.z

bpy.ops.mesh.primitive_plane_add(size=H * 14, location=(ctr.x, ctr.y, lo.z - 0.002))
fl = bpy.context.object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fnt = fm.node_tree
fnt.nodes.clear()
fo = fnt.nodes.new("ShaderNodeOutputMaterial")
fe = fnt.nodes.new("ShaderNodeEmission")
fe.inputs[0].default_value = (0.035, 0.04, 0.055, 1)
fnt.links.new(fe.outputs[0], fo.inputs[0])
fl.data.materials.append(fm)

li = bpy.data.lights.new("Sun", "SUN")
li.energy = 3.4
so = bpy.data.objects.new("Sun", li)
so.rotation_euler = (math.radians(55), 0, math.radians(-22))
sc.collection.objects.link(so)
for nm, off, en, colr in (("rim", (-3.0, 3.0, 3.0), 500, (0.6, 0.82, 1.0)),
                          ("fill", (3.0, -3.2, 2.0), 280, (1, 1, 1)),
                          ("back", (0.5, 4.0, 2.0), 200, (0.8, 0.85, 1.0))):
    al = bpy.data.lights.new(nm, "AREA")
    al.energy = en
    al.size = H * 2
    al.color = colr
    ao = bpy.data.objects.new(nm, al)
    ao.location = (ctr.x + off[0] * H * 0.5, ctr.y + off[1] * H * 0.5, lo.z + off[2] * H * 0.5)
    sc.collection.objects.link(ao)
    d = Vector(ctr) - ao.location
    ao.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

camd = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", camd)
sc.collection.objects.link(cam)
sc.camera = cam

try:
    ng = bpy.data.node_groups.new("Compositing", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    sc.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers")
    gl = ng.nodes.new("CompositorNodeGlare")
    for k, v in (("Type", "Bloom"), ("Quality", "High"), ("Threshold", 1.5), ("Strength", 0.3)):
        try:
            gl.inputs[k].default_value = v
        except Exception:
            pass
    gout = ng.nodes.new("NodeGroupOutput")
    ng.links.new(rl.outputs[0], gl.inputs[0])
    ng.links.new(gl.outputs[0], gout.inputs[0])
except Exception as e:
    print("glare skip", e)


def shoot(name, ang_deg, dist=2.45, zmul=0.10, x=1000, y=1300, lens=62):
    a = math.radians(ang_deg)
    d = H * dist
    camd.lens = lens
    cam.location = (ctr.x + math.sin(a) * d, ctr.y - math.cos(a) * d, ctr.z + H * zmul)
    v = Vector(ctr) - cam.location
    cam.rotation_euler = v.to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = x
    sc.render.resolution_y = y
    p = os.path.join(REN, name)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    try:
        shutil.copy2(p, os.path.join(HIST, "%s_%s" % (RUN, name)))
    except Exception as e:
        print("hist fail", e)


shoot("07_slayer_front.png", 0)
shoot("07_slayer_34.png", 32)
shoot("07_slayer_back.png", 180)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
print("DONE")
