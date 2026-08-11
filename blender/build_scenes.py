# -*- coding: utf-8 -*-
# 검 게임 프리프로덕션 v3: 토이 피규어 비율(4등신대) x 귀멸 소년 체형 캐릭터
# 실행: blender --background --python build_scenes.py -- all
# v3 스타일: 아웃라인 없음, 소프트 램프(도색 피규어 느낌), 좁은 어깨+A라인(하카마) 실루엣,
#            짧은 머리, 카타나 어깨 파지. 레퍼런스: soldier.webp(비율·마감) + 귀멸 공식 일러(체형·복장)
import bpy
import math
import os
import sys
import random
from mathutils import Vector, Matrix, Euler

ROOT = "/Users/lbj/Documents/gameproject"
REN = os.path.join(ROOT, "renders")
BLD = os.path.join(ROOT, "blender")
os.makedirs(REN, exist_ok=True)
os.makedirs(BLD, exist_ok=True)

# ---------------------------------------------------------------- 공통 유틸

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    prop = sc.render.bl_rna.properties["engine"]
    ids = [it.identifier for it in prop.enum_items]
    for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if cand in ids:
            sc.render.engine = cand
            break
    else:
        sc.render.engine = "CYCLES"
    try:
        sc.eevee.taa_render_samples = 64
    except Exception:
        pass
    sc.render.resolution_x = 1400
    sc.render.resolution_y = 1000
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.016, 0.018, 0.026, 1)
    bg.inputs[1].default_value = 1.0
    return sc


def link(obj):
    bpy.context.collection.objects.link(obj)
    return obj


def new_mesh_obj(name, verts, faces, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    if uvs:
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uvl.data[li].uv = uvs[vi]
    ob = bpy.data.objects.new(name, me)
    return link(ob)


CUBE_FACES = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def taper_box(name, wxb, wyb, wxt, wyt, h, loc=(0, 0, 0), shift_top=(0, 0),
              origin="bottom", mat=None, bevel=0.02, seg=3, smooth=True, outline=False):
    if origin == "bottom":
        z0, z1 = 0.0, h
    elif origin == "top":
        z0, z1 = -h, 0.0
    else:
        z0, z1 = -h / 2, h / 2
    sx, sy = shift_top
    hb_x, hb_y, ht_x, ht_y = wxb / 2, wyb / 2, wxt / 2, wyt / 2
    verts = [(-hb_x, -hb_y, z0), (hb_x, -hb_y, z0), (hb_x, hb_y, z0), (-hb_x, hb_y, z0),
             (-ht_x + sx, -ht_y + sy, z1), (ht_x + sx, -ht_y + sy, z1),
             (ht_x + sx, ht_y + sy, z1), (-ht_x + sx, ht_y + sy, z1)]
    ob = new_mesh_obj(name, verts, CUBE_FACES)
    ob.location = loc
    finish(ob, mat, bevel, seg, smooth, outline)
    return ob


def box(name, w, d, h, loc=(0, 0, 0), origin="center", mat=None, bevel=0.02, seg=3, smooth=True, outline=False):
    return taper_box(name, w, d, w, d, h, loc, (0, 0), origin, mat, bevel, seg, smooth, outline)


def prim(kind, name, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), smooth=True, outline=False, bevel=0, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(location=loc, rotation=rot, **kw)
    ob = bpy.context.object
    ob.name = name
    finish(ob, mat, bevel, 2, smooth, outline)
    return ob


def tcyl(name, r_bot, r_top, h, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), origin="bottom",
         verts=24, smooth=True, outline=False, squash_y=1.0):
    off = {"bottom": h / 2, "top": -h / 2, "center": 0}[origin]
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r_bot, radius2=r_top, depth=h,
                                    location=(0, 0, 0), rotation=(0, 0, 0))
    ob = bpy.context.object
    ob.name = name
    me = ob.data
    for v in me.vertices:
        v.co.y *= squash_y
        v.co.z += off
    finish(ob, mat, 0, 2, smooth, outline)
    return_ob = ob
    ob.location = loc
    ob.rotation_euler = rot
    return return_ob


OUTLINE_MAT = None


def get_outline_mat():
    global OUTLINE_MAT
    try:
        stale = OUTLINE_MAT is None or OUTLINE_MAT.name not in bpy.data.materials
    except ReferenceError:
        stale = True
    if stale:
        m = bpy.data.materials.new("OUTLINE")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (0.005, 0.005, 0.008, 1)
        em.inputs[1].default_value = 1.0
        nt.links.new(em.outputs[0], out.inputs[0])
        m.use_backface_culling = True
        OUTLINE_MAT = m
    return OUTLINE_MAT


def finish(ob, mat, bevel, seg, smooth, outline, outline_w=0.010):
    if bevel and bevel > 0:
        b = ob.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = seg
        b.limit_method = "ANGLE"
    if mat is not None:
        ob.data.materials.append(mat)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    if outline:
        ob.data.materials.append(get_outline_mat())
        so = ob.modifiers.new("Outline", "SOLIDIFY")
        so.thickness = outline_w
        so.offset = 1.0
        so.use_flip_normals = True
        so.use_rim = False
        so.material_offset = len(ob.data.materials) - 1


def hexc(h, mul=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    def lin(c):
        return min(1.0, max(0.0, (c ** 2.2) * mul))
    return (lin(r), lin(g), lin(b), 1.0)


def cel_mat(name, base_hex, ramp_pos=0.30, shadow_mul=0.55, shadow_blue=0.08, soft=0.28):
    """소프트 램프 = 도색 피규어 느낌. soft=밴드 폭(0=하드 셀)."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs[0].default_value = (1, 1, 1, 1)
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "LINEAR" if soft > 0 else "CONSTANT"
    ramp.color_ramp.elements[0].position = max(0.0, ramp_pos - soft / 2)
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = min(1.0, ramp_pos + soft / 2)
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    base = hexc(base_hex)
    shadow = (base[0] * shadow_mul, base[1] * shadow_mul, min(1, base[2] * shadow_mul + shadow_blue * 0.25), 1)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = shadow
    mix.inputs[7].default_value = base
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[1].default_value = 1.0
    nt.links.new(diff.outputs[0], s2r.inputs[0])
    nt.links.new(s2r.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def glow_mat(name, col_hex, strength):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = hexc(col_hex)
    em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def add_camera(loc, target, lens=50):
    cam = bpy.data.cameras.new("Cam")
    cam.lens = lens
    ob = bpy.data.objects.new("Cam", cam)
    link(ob)
    ob.location = loc
    look_at(ob, target)
    bpy.context.scene.camera = ob
    return ob


def add_sun(rot=(math.radians(55), 0, math.radians(-18)), energy=3.6):
    li = bpy.data.lights.new("Sun", "SUN")
    li.energy = energy
    li.angle = math.radians(4)
    ob = bpy.data.objects.new("Sun", li)
    ob.rotation_euler = rot
    link(ob)
    return ob


def add_area(name, loc, target, size, energy, color=(1, 1, 1)):
    li = bpy.data.lights.new(name, "AREA")
    li.energy = energy
    li.size = size
    li.color = color
    ob = bpy.data.objects.new(name, li)
    ob.location = loc
    link(ob)
    look_at(ob, target)
    return ob


def setup_glare(threshold=1.1, strength=0.55):
    sc = bpy.context.scene
    nt = None
    end_node = None
    try:
        sc.use_nodes = True
        nt = sc.node_tree
        nt.nodes.clear()
        end_node = nt.nodes.new("CompositorNodeComposite")
    except Exception:
        nt = None
    if nt is None:
        try:
            ng = bpy.data.node_groups.new("Compositing", "CompositorNodeTree")
            try:
                ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            except Exception:
                pass
            sc.compositing_node_group = ng
            nt = ng
            end_node = nt.nodes.new("NodeGroupOutput")
        except Exception:
            return
    rl = nt.nodes.new("CompositorNodeRLayers")
    gl = nt.nodes.new("CompositorNodeGlare")
    def set_in(name, val):
        try:
            gl.inputs[name].default_value = val
        except Exception:
            pass
    set_in("Type", "Bloom")
    set_in("Quality", "High")
    set_in("Threshold", threshold)
    set_in("Strength", strength)
    set_in("Size", 0.55)
    set_in("Smoothness", 0.15)
    try:
        items = [i.identifier for i in gl.bl_rna.properties["glare_type"].enum_items]
        for gt in ("BLOOM", "FOG_GLOW"):
            if gt in items:
                gl.glare_type = gt
                break
    except Exception:
        pass
    for attr, val in (("threshold", threshold), ("highlight_threshold", threshold),
                      ("mix", 0.0), ("size", 7), ("quality", "HIGH"), ("strength", strength)):
        try:
            setattr(gl, attr, val)
        except Exception:
            pass
    try:
        nt.links.new(rl.outputs[0], gl.inputs[0])
        nt.links.new(gl.outputs[0], end_node.inputs[0])
    except Exception:
        pass


RUN_TAG = __import__("time").strftime("%m%d_%H%M%S")
HIST = os.path.join(REN, "history")
os.makedirs(HIST, exist_ok=True)


def render(path, x=1400, y=1000):
    sc = bpy.context.scene
    sc.render.resolution_x = x
    sc.render.resolution_y = y
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # 검증 증거 보관: 매 렌더를 history/에 런 태그로 복사
    try:
        import shutil
        shutil.copy2(path, os.path.join(HIST, "%s_%s" % (RUN_TAG, os.path.basename(path))))
    except Exception as e:
        print("history copy fail", e)


def save_blend(name):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, name))


def add_floor(col="#101420", size=40):
    f = box("Floor", size, size, 0.05, loc=(0, 0, -0.05), origin="bottom",
            mat=glow_mat("floor", col, 1.0), bevel=0, outline=False)
    return f


def to_mesh(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def hair_lock(name, pts, radii, mat, thick):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = thick
    cu.bevel_resolution = 3
    cu.resolution_u = 8
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for i, (p, r) in enumerate(zip(pts, radii)):
        sp.points[i].co = (p[0], p[1], p[2], 1)
        sp.points[i].radius = r
    sp.use_endpoint_u = True
    sp.order_u = min(3, len(pts))
    ob = bpy.data.objects.new(name, cu)
    link(ob)
    ob.data.materials.append(mat)
    ob = to_mesh(ob)
    finish(ob, None, 0, 2, True, False)
    return ob


# ---------------------------------------------------------------- 팔레트
COL = {
    "skin": "#eeb488",
    "skin_dark": "#d99a6c",
    "hair": "#33202e",          # 먹빛 자주(짧은 머리)
    "uniform": "#262b38",       # 대원복 차콜
    "uniform_dark": "#1d212c",  # 하카마
    "trim": "#3a4054",
    "belt": "#e9e4d4",
    "cuff": "#e6e1d3",
    "button": "#d9b878",
    "haori": "#0f4c53",         # 심해 청록
    "wrap": "#e7e2d2",          # 흰 각반
    "boot": "#1e1710",
    "sclera": "#f8f5ee",
    "iris": "#7c2f3e",
    "iris_dark": "#471825",
    "pupil": "#190b10",
    "lash": "#241019",
    "blade": "#dde4ea",
    "fur": "#efe6cf",
    "grip": "#283050",
    "tsuba": "#3a3630",
    "gold": "#c9a86a",
    "rust": "#7d6b57",
    "rust_dark": "#4a3a2f",
}

# ---------------------------------------------------------------- v3 캐릭터
# 비율: 4.2등신 토이 피규어. 체형: 귀멸 소년(좁은 어깨, 슬림 상체, 풍성한 하카마 A라인)

def build_character(tag="F", x0=0.0):
    parts = {}
    m_skin = cel_mat("skin", COL["skin"], ramp_pos=0.26, shadow_mul=0.74, soft=0.30)
    m_skind = cel_mat("skind", COL["skin_dark"], ramp_pos=0.26, shadow_mul=0.7, soft=0.30)
    m_hair = cel_mat("hair", COL["hair"], shadow_mul=0.6, soft=0.24)
    m_uni = cel_mat("uniform", COL["uniform"], ramp_pos=0.34, shadow_mul=0.6, soft=0.26)
    m_unid = cel_mat("unidark", COL["uniform_dark"], ramp_pos=0.36, shadow_mul=0.6, soft=0.26)
    m_belt = cel_mat("belt", COL["belt"], soft=0.26)
    m_cuff = cel_mat("cuff", COL["cuff"], soft=0.26)
    m_haori = cel_mat("haori", COL["haori"], soft=0.26)
    m_wrap = cel_mat("wrap", COL["wrap"], shadow_mul=0.72, soft=0.26)
    m_boot = cel_mat("boot", COL["boot"], shadow_mul=0.6, soft=0.26)

    root = bpy.data.objects.new("root_" + tag, None)
    link(root)
    root.location = (x0, 0, 0)
    parts["root"] = root

    def par(ob, parent):
        ob.parent = parent
        return ob

    HEAD = 0.40                  # 머리 높이 -> 총 1.68 = 4.2등신
    # ---- 하체 ----
    hip_x = 0.082
    z_leg_top = 0.66
    for side, sx in (("L", -1), ("R", 1)):
        leg = bpy.data.objects.new("leg%s_%s" % (side, tag), None)
        link(leg)
        leg.location = (sx * hip_x, 0, z_leg_top)
        par(leg, root)
        parts["leg" + side] = leg
        # 하카마 퍼프(위 넓고 아래 조임, 귀멸 실루엣)
        puff = tcyl("puff%s_%s" % (side, tag), 0.072, 0.128, 0.34, mat=m_unid,
                    origin="top", loc=(0, 0, 0.02))
        par(puff, leg)
        # 흰 각반(발목까지 이어짐)
        wrap = tcyl("wrap%s_%s" % (side, tag), 0.056, 0.066, 0.27, mat=m_wrap,
                    origin="top", loc=(0, 0, -0.30))
        par(wrap, leg)
        for i in range(2):
            band = tcyl("band%s%d_%s" % (side, i, tag), 0.0625, 0.0615, 0.014,
                        mat=cel_mat("wrapline", "#cfc8b6", soft=0.26), origin="center",
                        loc=(0, 0, -0.35 - i * 0.09))
            par(band, leg)
        # 신발(짚신풍 로우슈즈)
        shoe = box("shoe%s_%s" % (side, tag), 0.108, 0.21, 0.075, origin="bottom",
                   mat=m_boot, bevel=0.024, seg=3)
        shoe.location = (0, -0.030, -0.66)
        par(shoe, leg)

    # 골반(하카마 상단 스커트)
    hip = tcyl("hip_" + tag, 0.165, 0.132, 0.16, mat=m_unid, origin="bottom",
               loc=(0, 0, 0.62), squash_y=0.9)
    par(hip, root)
    parts["hip"] = hip

    # ---- 상체(슬림, 좁은 어깨) ----
    z_torso0 = 0.76
    torso_h = 0.34
    torso = tcyl("torso_" + tag, 0.118, 0.128, torso_h, mat=m_uni, origin="bottom",
                 loc=(0, 0, z_torso0), squash_y=0.78)
    par(torso, root)
    parts["torso"] = torso

    belt = tcyl("belt_" + tag, 0.130, 0.130, 0.06, mat=m_belt, origin="center",
                loc=(0, 0, 0.05), squash_y=0.80)
    par(belt, torso)
    buckle = box("buckle_" + tag, 0.042, 0.012, 0.032, origin="center", mat=m_cuff,
                 bevel=0.005, seg=2)
    buckle.location = (0, -0.112, 0.05)
    par(buckle, torso)

    collar = tcyl("collar_" + tag, 0.055, 0.061, 0.05, mat=cel_mat("trim2", COL["trim"], soft=0.26),
                  origin="bottom", loc=(0, 0, torso_h - 0.012), squash_y=0.85)
    par(collar, torso)
    for i in range(4):
        z = 0.115 + i * 0.058
        r_here = (0.118 + 0.010 * (z / torso_h)) * 0.78 + 0.010
        b = prim("uv_sphere", "btn%d_%s" % (i, tag), mat=cel_mat("button", COL["button"], soft=0.26),
                 segments=10, ring_count=8, radius=0.0115)
        b.location = (0, -r_here, z)
        par(b, torso)

    # ---- 하오리(어깨에 걸침) ----
    hb = taper_box("haoriB_" + tag, 0.30, 0.05, 0.27, 0.045, 0.50, origin="top",
                   mat=m_haori, bevel=0.02)
    hb.location = (0, 0.105, torso_h - 0.005)
    par(hb, torso)
    parts["haoriB"] = hb
    for side, sx in (("L", -1), ("R", 1)):
        hf = taper_box("haoriF%s_%s" % (side, tag), 0.085, 0.040, 0.075, 0.045, 0.42,
                       origin="top", mat=m_haori, bevel=0.018)
        hf.location = (sx * 0.108, -0.088, torso_h - 0.005)
        hf.rotation_euler = (0, sx * math.radians(-4), 0)
        par(hf, torso)
        parts["haoriF" + side] = hf

    # ---- 팔(슬림) + 흰 커프스 + 손 ----
    sh_z = torso_h - 0.035
    sh_x = 0.128
    arm_l = 0.34
    for side, sx in (("L", -1), ("R", 1)):
        arm = bpy.data.objects.new("arm%s_%s" % (side, tag), None)
        link(arm)
        arm.location = (sx * sh_x, 0, sh_z)
        arm.rotation_euler = (0, sx * math.radians(-8), 0)
        par(arm, torso)
        parts["arm" + side] = arm
        # 어깨 소프트 캡(좁게)
        cap = prim("uv_sphere", "shcap%s_%s" % (side, tag), mat=m_uni, segments=16,
                   ring_count=12, radius=0.048)
        cap.location = (0, 0, 0.006)
        cap.scale = (1.0, 0.9, 0.8)
        par(cap, arm)
        slv = tcyl("sleeve%s_%s" % (side, tag), 0.049, 0.044, arm_l * 0.82, mat=m_uni,
                   origin="top", loc=(0, 0, 0.01))
        par(slv, arm)
        # 하오리 소매(짧고 둥글게)
        hslv = tcyl("hsleeve%s_%s" % (side, tag), 0.061, 0.053, arm_l * 0.36, mat=m_haori,
                    origin="top", loc=(0, 0, 0.0))
        par(hslv, arm)
        cuffz = -arm_l * 0.82 + 0.01
        cuff = tcyl("cuff%s_%s" % (side, tag), 0.050, 0.047, 0.05, mat=m_cuff,
                    origin="top", loc=(0, 0, cuffz + 0.045))
        par(cuff, arm)
        hand = prim("uv_sphere", "hand%s_%s" % (side, tag), mat=m_skin, segments=18,
                    ring_count=14, radius=0.049)
        hand.location = (0, 0, cuffz - 0.028)
        hand.scale = (0.95, 0.85, 1.12)
        par(hand, arm)
        parts["hand" + side] = hand
        thumb = prim("uv_sphere", "thumb%s_%s" % (side, tag), mat=m_skin, segments=12,
                     ring_count=8, radius=0.018)
        thumb.location = (-sx * 0.038, -0.02, 0.012)
        par(thumb, hand)

    # ---- 목 + 두상 ----
    neck = tcyl("neck_" + tag, 0.045, 0.049, 0.075, mat=m_skin, origin="bottom",
                loc=(0, 0, -0.02))
    par(neck, torso)

    head = bpy.data.objects.new("head_" + tag, None)
    link(head)
    head.location = (0, -0.005, torso_h + 0.035)
    par(head, torso)
    parts["head"] = head

    rx, ry_, rz_ = 0.148, 0.150, 0.185   # 소년 두상(약간 세로 긴 달걀)
    zc = rz_ * 0.95
    bpy.ops.mesh.primitive_uv_sphere_add(segments=44, ring_count=32, radius=1.0, location=(0, 0, 0))
    skull = bpy.context.object
    skull.name = "skull_" + tag
    for v in skull.data.vertices:
        x, y, z = v.co
        if z < 0:  # 볼-턱 테이퍼(소년: 볼은 살리고 턱만 좁힘)
            t = min(1.0, -z)
            s = 1.0 - 0.34 * (t ** 1.9)
            x *= s
            y *= s
        if z < -0.55:  # 턱끝 핀치
            p = (-z - 0.55) / 0.45
            x *= 1.0 - 0.22 * (p ** 1.4)
        if y < -0.42:  # 얼굴 플랫(완만)
            y = -0.42 + (y + 0.42) * 0.30
        v.co = (x * rx, y * ry_, z * rz_)
    finish(skull, m_skin, 0, 2, True, False)
    skull.location = (0, 0, zc)
    par(skull, head)

    # 귀
    for side, sx in (("L", -1), ("R", 1)):
        ear = prim("uv_sphere", "ear%s_%s" % (side, tag), mat=m_skin, segments=12, ring_count=10,
                   radius=0.022)
        ear.location = (sx * rx * 0.98, 0.01, zc - rz_ * 0.06)
        ear.scale = (0.45, 0.8, 1.1)
        par(ear, head)

    # ---- 얼굴(귀멸 소년 눈) ----
    fy = -ry_ * 0.42 - 0.035
    eye_z = zc - rz_ * 0.10
    eye_x = 0.066
    ew, eh = 0.062, 0.085
    m_scl = cel_mat("sclera", COL["sclera"], ramp_pos=0.05, soft=0.1)
    m_iris = cel_mat("iris", COL["iris"], ramp_pos=0.05, soft=0.1)
    m_irisd = cel_mat("irisd", COL["iris_dark"], ramp_pos=0.05, soft=0.1)
    m_pup = cel_mat("pupil", COL["pupil"], ramp_pos=0.05, soft=0.1)
    m_lash = cel_mat("lash", COL["lash"], ramp_pos=0.05, soft=0.1)
    for side, sx in (("L", -1), ("R", 1)):
        scl = box("scl%s_%s" % (side, tag), ew, 0.012, eh, origin="center",
                  mat=m_scl, bevel=ew * 0.30, seg=3)
        scl.location = (sx * eye_x, fy, eye_z)
        par(scl, head)
        lash = box("lash%s_%s" % (side, tag), ew * 1.16, 0.012, eh * 0.17, origin="center",
                   mat=m_lash, bevel=0.005, seg=2)
        lash.location = (sx * eye_x, fy - 0.006, eye_z + eh * 0.50)
        lash.rotation_euler = (0, -sx * math.radians(7), 0)
        par(lash, head)
        ird = box("irisd%s_%s" % (side, tag), ew * 0.66, 0.010, eh * 0.82, origin="center",
                  mat=m_irisd, bevel=ew * 0.24, seg=3)
        ird.location = (sx * eye_x, fy - 0.009, eye_z - eh * 0.05)
        par(ird, head)
        ir = box("iris%s_%s" % (side, tag), ew * 0.52, 0.010, eh * 0.60, origin="center",
                 mat=m_iris, bevel=ew * 0.18, seg=3)
        ir.location = (sx * eye_x, fy - 0.015, eye_z - eh * 0.11)
        par(ir, head)
        pup = box("pup%s_%s" % (side, tag), ew * 0.24, 0.008, eh * 0.34, origin="center",
                  mat=m_pup, bevel=ew * 0.08, seg=2)
        pup.location = (sx * eye_x, fy - 0.020, eye_z - eh * 0.11)
        par(pup, head)
        hi = prim("uv_sphere", "hi%s_%s" % (side, tag), mat=glow_mat("eyehi", "#ffffff", 1.1),
                  segments=12, ring_count=8, radius=ew * 0.16)
        hi.location = (sx * (eye_x - ew * 0.16), fy - 0.025, eye_z + eh * 0.16)
        hi.scale = (1, 0.5, 1)
        par(hi, head)
        brow = box("brow%s_%s" % (side, tag), ew * 1.15, 0.012, 0.014, origin="center",
                   mat=m_hair, bevel=0.005, seg=2)
        brow.location = (sx * eye_x, fy - 0.002, eye_z + eh * 0.82)
        brow.rotation_euler = (0, -sx * math.radians(12), 0)
        par(brow, head)
    nose = prim("uv_sphere", "nose_" + tag, mat=m_skind, segments=10, ring_count=8, radius=0.011)
    nose.location = (0, fy - 0.004, eye_z - eh * 0.62)
    nose.scale = (0.8, 0.6, 1.1)
    par(nose, head)
    mouth = box("mouth_" + tag, 0.040, 0.010, 0.011, origin="center",
                mat=cel_mat("mouth", "#7e4437", ramp_pos=0.05, soft=0.1), bevel=0.004, seg=2)
    mouth.location = (0, fy - 0.002, zc - rz_ * 0.56)
    par(mouth, head)

    # ---- 짧은 머리 ----
    bpy.ops.mesh.primitive_uv_sphere_add(segments=36, ring_count=26, radius=1.0, location=(0, 0, 0))
    cap = bpy.context.object
    cap.name = "haircap_" + tag
    cme = cap.data
    import bmesh as _bm
    bm = _bm.new()
    bm.from_mesh(cme)
    kill = [v for v in bm.verts if (v.co.y < -0.20 and v.co.z < 0.34) or v.co.z < -0.42]
    _bm.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(cme)
    bm.free()
    for v in cme.vertices:
        x, y, z = v.co
        v.co = (x * rx * 1.075, y * ry_ * 1.09, z * rz_ * 1.07)
    finish(cap, m_hair, 0, 2, True, False)
    cap.location = (0, 0.008, zc + 0.008)
    par(cap, head)

    rng = random.Random(9)
    # 짧은 앞머리(이마 위 잔갈래)
    n_b = 8
    for i in range(n_b):
        t = (i / (n_b - 1)) - 0.5
        x = t * rx * 1.6
        ln = rz_ * (0.30 + rng.random() * 0.10 - abs(t) * 0.06)
        p0 = (x * 0.55, -ry_ * 0.42, zc + rz_ * 0.86)
        p1 = (x * 0.95, -ry_ * 0.92, zc + rz_ * 0.62)
        p2 = (x * 1.05, -ry_ * 0.98, zc + rz_ * 0.62 - ln)
        lk = hair_lock("bang%d_%s" % (i, tag), [p0, p1, p2], [1.0, 0.7, 0.0],
                       m_hair, 0.030 - abs(t) * 0.006)
        par(lk, head)
    # 옆머리 짧은 갈래
    for side, sx in (("L", -1), ("R", 1)):
        p0 = (sx * rx * 0.62, -ry_ * 0.30, zc + rz_ * 0.72)
        p1 = (sx * rx * 1.02, -ry_ * 0.44, zc + rz_ * 0.22)
        p2 = (sx * rx * 1.05, -ry_ * 0.38, zc - rz_ * 0.12)
        lk = hair_lock("side%s_%s" % (side, tag), [p0, p1, p2], [1.0, 0.65, 0.0], m_hair, 0.028)
        par(lk, head)
    # 뒷머리 짧은 갈래(목덜미 위에서 끝)
    n_k = 7
    for i in range(n_k):
        t = (i / (n_k - 1)) - 0.5
        x = t * rx * 1.35
        p0 = (x * 0.5, ry_ * 0.35, zc + rz_ * 0.80)
        p1 = (x * 0.95, ry_ * 0.95, zc + rz_ * 0.20)
        p2 = (x * 0.98, ry_ * 1.00, zc - rz_ * 0.28 + rng.random() * 0.02)
        lk = hair_lock("back%d_%s" % (i, tag), [p0, p1, p2], [1.0, 0.7, 0.0], m_hair, 0.030)
        par(lk, head)
    # 크라운 짧은 뻗침
    n_f = 6
    for i in range(n_f):
        t = (i / (n_f - 1)) - 0.5
        x = t * rx * 1.0
        p0 = (x * 0.5, ry_ * 0.0, zc + rz_ * 0.92)
        p1 = (x * 0.95, ry_ * 0.28, zc + rz_ * (1.10 + rng.random() * 0.05))
        p2 = (x * 1.15, ry_ * 0.45, zc + rz_ * (1.14 + rng.random() * 0.06))
        lk = hair_lock("flick%d_%s" % (i, tag), [p0, p1, p2], [1.0, 0.5, 0.0], m_hair, 0.024)
        par(lk, head)
    return parts


# ---------------------------------------------------------------- 카타나(일륜도풍)

def build_katana(tag="nichirin", scale=1.0, width_mul=1.0):
    """원점=그립 중앙, +X=칼끝. 밝은 도신+원형 츠바.
    width_mul: 도신 폭 과장(피규어 스케일에선 실물 비율이 바늘처럼 보여서 키운다)."""
    s = scale
    root = bpy.data.objects.new("katana_" + tag, None)
    link(root)
    m_blade = cel_mat("bladeK", COL["blade"], ramp_pos=0.30, shadow_mul=0.66, soft=0.2)
    m_tsuba = cel_mat("tsubaK", COL["tsuba"], soft=0.2)
    m_grip = cel_mat("gripK", COL["grip"], soft=0.2)
    m_gold = cel_mat("goldK", COL["gold"], soft=0.2)

    n = 16
    L = 0.78 * s
    w = 0.024 * s * width_mul
    verts = []
    for i in range(n + 1):
        t = i / n
        x = 0.045 + t * L
        zc = 0.055 * s * (t ** 1.7)
        wi = w * (1.0 - 0.45 * t)
        if t > 0.88:  # 킷사키(칼끝)
            wi *= (1.0 - (t - 0.88) / 0.12 * 0.85)
        verts.append((x, 0, zc + wi))
        verts.append((x, 0, zc - wi * 0.45))
    faces = []
    for i in range(n):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
    blade = new_mesh_obj("bladeK_" + tag, verts, faces)
    sol = blade.modifiers.new("Sol", "SOLIDIFY")
    sol.thickness = 0.011 * s * width_mul
    sol.offset = 0
    finish(blade, m_blade, 0.002, 2, False, False)
    blade.parent = root

    # ★width_mul(2.8) 을 그대로 곱했더니 츠바가 접시만큼 커져 손을 다 덮었다.
    # 실제 카타나 츠바는 자루보다 조금 큰 정도다.
    tsuba = prim("cylinder", "tsubaK_" + tag, mat=m_tsuba, vertices=20,
                 radius=0.052 * s * max(1.0, width_mul * 0.42),
                 depth=0.014 * s, rot=(0, math.radians(90), 0), bevel=0.004)
    tsuba.location = (0.038 * s, 0, 0)
    tsuba.parent = root
    # 양손 파지 카타나는 자루가 길다. 0.24s 로는 두 손이 붙어버린다(실측:
    # 두 손 간격 0.168, 자루 0.324 라 여유가 거의 없었다).
    grip = prim("cylinder", "gripK_" + tag, mat=m_grip, vertices=14,
                radius=0.0235 * s * max(1.0, width_mul * 0.7),
                depth=0.42 * s, rot=(0, math.radians(90), 0), bevel=0.004)
    grip.location = (-0.175 * s, 0, 0)
    grip.parent = root
    for i in range(3):
        ring = prim("cylinder", "ringK%d_%s" % (i, tag), mat=m_gold, vertices=14,
                    radius=0.0255 * s, depth=0.012 * s, rot=(0, math.radians(90), 0))
        ring.location = ((-0.035 - i * 0.108) * s, 0, 0)
        ring.parent = root
    pom = prim("cylinder", "pomK_" + tag, mat=m_gold, vertices=14, radius=0.027 * s,
               depth=0.022 * s, rot=(0, math.radians(90), 0), bevel=0.004)
    pom.location = (-0.372 * s, 0, 0)
    pom.parent = root
    return root


# ---------------------------------------------------------------- 송곳니 대검/봉인검 (유지)

def build_fang_sword(tag="fang", scale=1.0):
    s = scale
    root = bpy.data.objects.new("sword_" + tag, None)
    link(root)
    m_blade = cel_mat("blade", COL["blade"], ramp_pos=0.30, shadow_mul=0.62, soft=0.2)
    m_fur = cel_mat("fur", COL["fur"], shadow_mul=0.6, soft=0.24)
    m_grip = cel_mat("grip", COL["grip"], soft=0.2)
    m_gold = cel_mat("gold2", COL["gold"], soft=0.2)

    back = [(0.00, 0.042), (0.35, 0.052), (0.70, 0.070), (1.00, 0.082), (1.22, 0.070), (1.38, 0.038), (1.52, -0.020)]
    belly = [(1.38, -0.115), (1.18, -0.170), (0.92, -0.200), (0.62, -0.185), (0.32, -0.135), (0.10, -0.070), (0.00, -0.040)]
    pts = back + belly
    verts = [(x * s + 0.05, 0, z * s) for (x, z) in pts]
    face = [tuple(range(len(verts)))]
    blade = new_mesh_obj("blade_" + tag, verts, face)
    sol = blade.modifiers.new("Sol", "SOLIDIFY")
    sol.thickness = 0.034 * s
    sol.offset = 0
    finish(blade, m_blade, 0.006, 2, False, False)
    blade.parent = root

    rng = random.Random(3)
    for i in range(26):
        a = i / 26 * math.tau
        r0 = 0.045 * s
        ln = (0.13 + rng.random() * 0.07) * s
        f = prim("cone", "fur%d_%s" % (i, tag), mat=m_fur, vertices=6,
                 radius1=0.030 * s, depth=ln, smooth=False)
        dy, dz = math.cos(a), math.sin(a)
        f.location = (0.045 * s, dy * r0 * 0.8, dz * r0 * 0.8)
        v = Vector((0.55, dy, dz)).normalized()
        f.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
        f.parent = root

    grip = prim("cylinder", "grip_" + tag, mat=m_grip, vertices=12, radius=0.034 * s, depth=0.34 * s,
                rot=(0, math.radians(90), 0), bevel=0.004)
    grip.location = (-0.14 * s, 0, 0)
    grip.parent = root
    for i in range(4):
        ring = prim("cylinder", "ring%d_%s" % (i, tag), mat=m_gold, vertices=12, radius=0.0365 * s,
                    depth=0.014 * s, rot=(0, math.radians(90), 0))
        ring.location = ((-0.03 - i * 0.075) * s, 0, 0)
        ring.parent = root
    pom = prim("cylinder", "pom_" + tag, mat=m_gold, vertices=12, radius=0.040 * s, depth=0.030 * s,
               rot=(0, math.radians(90), 0), bevel=0.006)
    pom.location = (-0.315 * s, 0, 0)
    pom.parent = root
    return root


def build_sealed_katana(tag="sealed", scale=1.0):
    s = scale
    root = bpy.data.objects.new("sword_" + tag, None)
    link(root)
    m_blade = cel_mat("rust", COL["rust"], ramp_pos=0.38, shadow_mul=0.5, soft=0.2)
    m_tsuba = cel_mat("rustd", COL["rust_dark"], soft=0.2)
    m_grip = cel_mat("gripS", "#3a3630", soft=0.2)

    n = 14
    L = 1.00 * s
    w = 0.030 * s
    verts = []
    for i in range(n + 1):
        t = i / n
        x = 0.05 + t * L
        zc = 0.10 * s * (t ** 1.6)
        wi = w * (1.0 - 0.55 * t) + (0.012 * s if t > 0.9 else 0)
        verts.append((x, 0, zc + wi))
        verts.append((x, 0, zc - wi * 0.4))
    faces = []
    for i in range(n):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
    blade = new_mesh_obj("bladeS_" + tag, verts, faces)
    sol = blade.modifiers.new("Sol", "SOLIDIFY")
    sol.thickness = 0.014 * s
    sol.offset = 0
    finish(blade, m_blade, 0.003, 2, False, False)
    blade.parent = root

    tsuba = prim("cylinder", "tsuba_" + tag, mat=m_tsuba, vertices=16, radius=0.062 * s, depth=0.012 * s,
                 rot=(0, math.radians(90), 0), bevel=0.004)
    tsuba.location = (0.04 * s, 0, 0)
    tsuba.parent = root
    grip = prim("cylinder", "gripS_" + tag, mat=m_grip, vertices=10, radius=0.026 * s, depth=0.26 * s,
                rot=(0, math.radians(90), 0), bevel=0.004)
    grip.location = (-0.10 * s, 0, 0)
    grip.parent = root
    for i in range(3):
        ring = prim("cylinder", "ringS%d_%s" % (i, tag), mat=m_tsuba, vertices=10, radius=0.0285 * s,
                    depth=0.012 * s, rot=(0, math.radians(90), 0))
        ring.location = ((-0.035 - i * 0.07) * s, 0, 0)
        ring.parent = root
    return root


# ---------------------------------------------------------------- 물의 호흡풍 이펙트(유지)

def spiral_curl(name, size, mat, loc, rot):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = size * 0.10
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    n = 42
    sp.points.add(n - 1)
    for i in range(n):
        th = i / (n - 1) * math.pi * 2 * 1.75
        r = size * (0.16 + 0.84 * math.exp(-0.55 * th))
        x = math.cos(th) * r
        z = math.sin(th) * r
        sp.points[i].co = (x, 0, z, 1)
        sp.points[i].radius = 1.0 - 0.85 * (i / (n - 1))
    ob = bpy.data.objects.new(name, cu)
    link(ob)
    ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def build_slash_arc(tag="slash", R=1.15, deg0=-25, deg1=205, width=0.34):
    n = 96
    verts, faces, uvs = [], [], []
    a0, a1 = math.radians(deg0), math.radians(deg1)
    for i in range(n + 1):
        t = i / n
        a = a0 + (a1 - a0) * t
        wv = width * (math.sin(t * math.pi) ** 0.65)
        wave = 0.040 * math.sin(t * 34) * (math.sin(t * math.pi) ** 0.5)
        r_out = R + wv * 0.62 + wave
        r_in = R - wv * 0.38
        verts.append((math.cos(a) * r_in, math.sin(a) * r_in, 0))
        uvs.append((t, 0))
        verts.append((math.cos(a) * r_out, math.sin(a) * r_out, 0))
        uvs.append((t, 1))
    for i in range(n):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))

    if tag + "_mat" in bpy.data.materials:
        m = bpy.data.materials[tag + "_mat"]
    else:
        m = bpy.data.materials.new(tag + "_mat")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        uvn = nt.nodes.new("ShaderNodeUVMap")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        cr = ramp.color_ramp
        cr.elements[0].position = 0.0
        cr.elements[0].color = hexc("#06214f")
        cr.elements[1].position = 0.45
        cr.elements[1].color = hexc("#1173d4")
        e2 = cr.elements.new(0.80)
        e2.color = hexc("#3fd6ff")
        e3 = cr.elements.new(0.97)
        e3.color = hexc("#eaffff")
        st = nt.nodes.new("ShaderNodeValToRGB")
        st.color_ramp.elements[0].position = 0.0
        st.color_ramp.elements[0].color = (1.2, 1.2, 1.2, 1)
        st.color_ramp.elements[1].position = 1.0
        st.color_ramp.elements[1].color = (5.5, 5.5, 5.5, 1)
        em = nt.nodes.new("ShaderNodeEmission")
        mult = nt.nodes.new("ShaderNodeMix")
        mult.data_type = "RGBA"
        mult.blend_type = "MULTIPLY"
        mult.inputs[0].default_value = 1.0
        nt.links.new(uvn.outputs[0], sep.inputs[0])
        nt.links.new(sep.outputs[0], ramp.inputs[0])
        nt.links.new(sep.outputs[0], st.inputs[0])
        nt.links.new(ramp.outputs[0], mult.inputs[6])
        nt.links.new(st.outputs[0], mult.inputs[7])
        nt.links.new(mult.outputs[2], em.inputs[0])
        nt.links.new(em.outputs[0], out.inputs[0])

    arc = new_mesh_obj("arc_" + tag, verts, faces, uvs=uvs)
    arc.data.materials.append(m)

    m_foam = glow_mat("foam", "#f2fdff", 5.0)
    rng = random.Random(11)
    for t in (0.12, 0.28, 0.44, 0.58, 0.72, 0.85, 0.94):
        a = a0 + (a1 - a0) * t
        wv = width * (math.sin(t * math.pi) ** 0.65)
        r = R + wv * 0.72
        size = 0.09 + 0.11 * math.sin(t * math.pi) + rng.random() * 0.03
        c = spiral_curl("curl%02d_%s" % (int(t * 100), tag), size, m_foam,
                        (math.cos(a) * r, math.sin(a) * r, 0.012),
                        (math.radians(90), 0, a - math.pi / 2))
        c.parent = arc
    m_drop = glow_mat("drop", "#bfefff", 3.5)
    for i in range(26):
        t = rng.random()
        a = a0 + (a1 - a0) * t
        r = R + (rng.random() - 0.3) * 0.40
        d = prim("uv_sphere", "drop%d_%s" % (i, tag), mat=m_drop, segments=10, ring_count=8,
                 radius=0.008 + rng.random() * 0.015)
        d.parent = arc
        d.location = (math.cos(a) * r, math.sin(a) * r, (rng.random() - 0.5) * 0.12)
    for off, wmul in ((-0.16, 0.20), (0.20, 0.14)):
        n2 = 64
        v2, f2, u2 = [], [], []
        for i in range(n2 + 1):
            t = i / n2
            a = a0 + 0.25 + (a1 - a0 - 0.5) * t
            wv = width * wmul * (math.sin(t * math.pi) ** 0.8)
            r_o = R + off + wv
            r_i = R + off - wv
            v2.append((math.cos(a) * r_i, math.sin(a) * r_i, -0.02))
            u2.append((t, 0))
            v2.append((math.cos(a) * r_o, math.sin(a) * r_o, -0.02))
            u2.append((t, 1))
        for i in range(n2):
            q = i * 2
            f2.append((q, q + 2, q + 3, q + 1))
        s2 = new_mesh_obj("streak%s_%s" % (off, tag), v2, f2, uvs=u2)
        s2.data.materials.append(m)
        s2.parent = arc
    return arc


# ---------------------------------------------------------------- 장면들

def pose_shoulder_carry(parts, sword):
    """카타나 어깨 걸침(오른손). root는 +26도 돌려 얼굴 가림 방지."""
    parts["armR"].rotation_euler = (math.radians(-95), math.radians(22), 0)
    parts["armL"].rotation_euler = (math.radians(10), 0, math.radians(20))
    sword.parent = parts["handR"]
    sword.location = (0, -0.02, -0.02)
    sword.rotation_euler = (0, math.radians(122), math.radians(90))


def scene_lineup():
    """피규어 턴어라운드: 정면 / 사분면(+칼) / 뒷면"""
    reset()
    add_floor()
    for i, (ang, x) in enumerate(((6, -1.15), (30, 0.0), (180, 1.15))):
        parts = build_character("v%d" % i, x0=x)
        parts["root"].rotation_euler = (0, 0, math.radians(ang))
        if i == 1:
            sw = build_katana(tag="k%d" % i, scale=1.0)
            pose_shoulder_carry(parts, sw)
    add_sun()
    add_area("rim", (-2.5, 3.2, 2.6), (0, 0, 0.85), 3, 300, color=(0.6, 0.85, 1.0))
    add_area("fill", (2.2, -3.5, 1.8), (0, 0, 0.85), 4, 170)
    add_area("backfill", (0.5, 4.5, 1.6), (0, 0, 0.85), 4, 130)
    add_camera((0, -5.5, 1.05), (0, 0, 0.84), lens=58)
    setup_glare(1.5, 0.35)
    save_blend("lineup.blend")
    render(os.path.join(REN, "01_char_turnaround.png"), 1600, 1050)


def scene_figure():
    """피규어 단독 샷(3/4, 카타나 어깨 파지)"""
    reset()
    add_floor()
    parts = build_character("F", x0=0)
    parts["root"].rotation_euler = (0, 0, math.radians(26))
    sw = build_katana(tag="kF", scale=1.0)
    pose_shoulder_carry(parts, sw)
    parts["legL"].rotation_euler = (math.radians(-6), 0, 0)
    parts["legR"].rotation_euler = (math.radians(7), 0, 0)
    add_sun()
    add_area("rim", (-2.5, 3.0, 2.6), (0, 0, 0.9), 3, 320, color=(0.6, 0.85, 1.0))
    add_area("fill", (2.2, -3.4, 1.8), (0, 0, 0.9), 4, 170)
    add_area("backfill", (0.5, 4.5, 1.6), (0, 0, 0.9), 4, 90)
    add_camera((0.75, -3.6, 1.25), (0.03, 0, 0.83), lens=52)
    setup_glare(1.5, 0.35)
    save_blend("figure.blend")
    render(os.path.join(REN, "05_figure.png"), 1200, 1400)


def scene_swords():
    reset()
    add_floor()
    fang = build_fang_sword()
    fang.location = (-0.52, 0, 1.46)
    fang.rotation_euler = (math.radians(4), math.radians(100), math.radians(9))
    sealed = build_sealed_katana()
    sealed.location = (0.66, 0.05, 0.90)
    sealed.rotation_euler = (0, math.radians(85), math.radians(-8))
    add_sun(energy=3.4)
    add_area("rim", (-2.2, 2.8, 2.4), (0, 0, 0.9), 3, 300, color=(0.6, 0.85, 1.0))
    add_area("key", (1.8, -2.6, 2.2), (0, 0, 0.9), 3, 200)
    add_camera((0.05, -4.6, 1.0), (0.05, 0, 0.92), lens=48)
    setup_glare(1.4, 0.4)
    save_blend("swords.blend")
    render(os.path.join(REN, "02_swords.png"), 1400, 1000)


def scene_vfx():
    reset()
    arc = build_slash_arc()
    arc.location = (0, 0, 1.0)
    arc.rotation_euler = (math.radians(70), 0, 0)
    add_camera((0, -5.8, 1.0), (0, 0, 1.0), lens=46)
    setup_glare(1.0, 0.5)
    save_blend("vfx_slash.blend")
    render(os.path.join(REN, "03_slash_vfx.png"), 1400, 1000)


def scene_hero():
    reset()
    add_floor()
    parts = build_character("H", x0=0)
    parts["torso"].rotation_euler = (math.radians(5), 0, math.radians(-20))
    parts["armR"].rotation_euler = (math.radians(-88), math.radians(-30), math.radians(-8))
    parts["armL"].rotation_euler = (math.radians(24), 0, math.radians(14))
    parts["legL"].rotation_euler = (math.radians(-13), 0, 0)
    parts["legR"].rotation_euler = (math.radians(16), 0, 0)
    parts["haoriB"].rotation_euler = (math.radians(-13), 0, 0)
    parts["haoriFL"].rotation_euler = (math.radians(5), 0, math.radians(-7))
    parts["haoriFR"].rotation_euler = (math.radians(4), 0, math.radians(7))
    parts["head"].rotation_euler = (0, 0, math.radians(9))

    sword = build_katana(tag="kH", scale=1.05)
    sword.parent = parts["handR"]
    sword.location = (0, -0.02, -0.01)
    sword.rotation_euler = (0, math.radians(-95), math.radians(90))

    arc = build_slash_arc(tag="hero", R=0.95, deg0=175, deg1=-30, width=0.24)
    arc.location = (0.26, 0.12, 1.02)
    arc.rotation_euler = (math.radians(24), math.radians(-6), 0)

    add_sun(energy=3.4)
    add_area("rim", (-2.6, 2.6, 2.2), (0, 0, 0.95), 3, 320, color=(0.5, 0.85, 1.0))
    add_area("fill", (2.0, -3.0, 1.6), (0, 0, 0.9), 4, 110)
    add_camera((1.85, -3.6, 1.55), (0.10, 0, 0.85), lens=42)
    setup_glare(1.05, 0.5)
    save_blend("hero_swing.blend")
    render(os.path.join(REN, "04_hero_swing.png"), 1400, 1150)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["all"]
    which = args[0] if args else "all"
    t0 = __import__("time").time()
    if which in ("all", "lineup"):
        scene_lineup()
    if which in ("all", "figure"):
        scene_figure()
    if which in ("all", "swords"):
        scene_swords()
    if which in ("all", "vfx"):
        scene_vfx()
    if which in ("all", "hero"):
        scene_hero()
    print("DONE in %.1fs" % (__import__("time").time() - t0))
