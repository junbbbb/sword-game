# -*- coding: utf-8 -*-
# [1/3] 몸통만 남기는 수술 + 체형 재조형 + 페인팅용 데이터(JSON) 내보내기
# 실행: blender --background --python s1_export_base.py
import bpy
import bmesh
import os
import json
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
FBX = os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX")
SCR = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad"
OUT_BLEND = os.path.join(ROOT, "blender/slayer_base.blend")
OUT_JSON = os.path.join(SCR, "paint_data.json")

HEAD_SX = float(os.environ.get("SLAYER_HEADX", "1.40"))   # 폭(원본이 좁고 길쭉함)
HEAD_SY = float(os.environ.get("SLAYER_HEADY", "1.08"))   # 깊이
HEAD_SZ = float(os.environ.get("SLAYER_HEADZ", "1.20"))   # 높이
SHOULDER = float(os.environ.get("SLAYER_SHOULDER", "0.34"))
ARM = float(os.environ.get("SLAYER_ARM", "0.72"))
CHEST_Y = float(os.environ.get("SLAYER_CHESTY", "0.80"))
TORSO_X = float(os.environ.get("SLAYER_TORSOX", "0.92"))
FLARE = float(os.environ.get("SLAYER_FLARE", "1.30"))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.fbx(filepath=FBX)
mesh_ob = next(o for o in sc.objects if o.type == "MESH")
arm_ob = next(o for o in sc.objects if o.type == "ARMATURE")
me = mesh_ob.data

# ---------------- 1) 수술: 최대 연결 요소(몸통)만 남긴다 ----------------
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
seen = set()
comps = []
adj = {v.index: [e.other_vert(v).index for e in v.link_edges] for v in bm.verts}
for vi in adj:
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
comps.sort(key=len, reverse=True)
body = set(comps[0])
dead = [v for v in bm.verts if v.index not in body]
print("surgery: keep %d verts, remove %d parts (%d verts)"
      % (len(body), len(comps) - 1, len(dead)))
bmesh.ops.delete(bm, geom=dead, context="VERTS")
bm.to_mesh(me)
bm.free()
me.update()

# ---------------- 2) 본 랜드마크 ----------------
M = mesh_ob.matrix_world.inverted() @ arm_ob.matrix_world
head_of = {b.name.lower(): (M @ b.head_local) for b in arm_ob.data.bones}
child_of = {}
for b in arm_ob.data.bones:
    if b.children:
        child_of[b.name.lower()] = M @ b.children[0].head_local

neck_j = head_of.get("bip001 neck")
head_j = head_of.get("bip001 head")
pelvis_j = head_of.get("bip001 pelvis")
spine_j = head_of.get("bip001 spine")
lhand_j = head_of.get("bip001 l hand")
rhand_j = head_of.get("bip001 r hand")
print("joints: neck=%.1f head=%.1f pelvis=%.1f spine=%.1f" %
      (neck_j.z, head_j.z, pelvis_j.z, spine_j.z))

vg_name = {g.index: g.name for g in mesh_ob.vertex_groups}
dom = {}
for v in me.vertices:
    best, bw = None, -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, vg_name.get(g.group, "")
    dom[v.index] = (best or "").lower()


def region_of(d):
    if "head" in d:
        return "head"
    if "neck" in d:
        return "neck"
    if "clavicle" in d:
        return "shoulder"
    if "upperarm" in d:
        return "upperarm"
    if "forearm" in d:
        return "forearm"
    if "hand" in d:
        return "hand"
    if "spine" in d:
        return "torso"
    if "pelvis" in d:
        return "pelvis"
    if "thigh" in d:
        return "thigh"
    if "calf" in d:
        return "calf"
    if "foot" in d or "toe" in d:
        return "foot"
    return "other"


# ---------------- 3) 체형 재조형 ----------------
sh_x = max(abs(h.x) for k, h in head_of.items() if "upperarm" in k)
pull = sh_x * SHOULDER
spine_y = spine_j.y
z_hip = pelvis_j.z


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def closest_on_seg(p, a, b):
    ab = b - a
    L2 = ab.length_squared
    if L2 < 1e-9:
        return a
    t = max(0.0, min(1.0, (p - a).dot(ab) / L2))
    return a + ab * t


UPPER = ("clavicle", "upperarm", "forearm", "hand", "spine", "neck", "head")
for v in me.vertices:
    d = dom[v.index]
    if any(k in d for k in UPPER):
        s = smoothstep(abs(v.co.x) / sh_x)
        v.co.x -= math.copysign(pull * s, v.co.x)
    if any(k in d for k in ("upperarm", "forearm", "clavicle")):
        a = head_of.get(d)
        c = child_of.get(d)
        if a is not None:
            if c is None:
                c = a + Vector((math.copysign(6.0, a.x), 0, 0))
            p = closest_on_seg(v.co, a, c)
            v.co = p + (v.co - p) * ARM
    if "spine" in d:
        v.co.x *= TORSO_X
        v.co.y = spine_y + (v.co.y - spine_y) * CHEST_Y
    if ("pelvis" in d or "thigh" in d) and v.co.z < z_hip:
        t = smoothstep((z_hip - v.co.z) / max(1.0, z_hip * 0.60))
        f = 1.0 + (FLARE - 1.0) * (1.0 - t)
        v.co.x *= f
        v.co.y *= f

# 머리 확대(목 관절 기준, 축별) — 토이 비율 + 둥근 두상
pivot = neck_j.copy()
for v in me.vertices:
    d = dom[v.index]
    if "head" in d or "neck" in d:
        r = v.co - pivot
        v.co = pivot + Vector((r.x * HEAD_SX, r.y * HEAD_SY, r.z * HEAD_SZ))

# 머리 치수(확대 후)
hv = [v.co.copy() for v in me.vertices if "head" in dom[v.index]]
hx0, hx1 = min(p.x for p in hv), max(p.x for p in hv)
hy0, hy1 = min(p.y for p in hv), max(p.y for p in hv)
hz0, hz1 = min(p.z for p in hv), max(p.z for p in hv)
head_w, head_d, head_h = hx1 - hx0, hy1 - hy0, hz1 - hz0
print("head after scale: w=%.1f d=%.1f h=%.1f  z[%.1f,%.1f] yfront=%.1f"
      % (head_w, head_d, head_h, hz0, hz1, hy0))

# 코 낮추기: 머리 앞쪽(y 하위 12%) & 눈높이 아래 정점을 뒤로
eye_z = hz0 + head_h * 0.52
ys = sorted(p.y for p in hv)
y_front_thresh = ys[max(0, int(len(ys) * 0.10))]
y_plane = ys[int(len(ys) * 0.30)]
n_flat = 0
for v in me.vertices:
    if "head" not in dom[v.index]:
        continue
    if v.co.y <= y_front_thresh + 0.4 and (hz0 + head_h * 0.15) < v.co.z < eye_z + head_h * 0.10:
        v.co.y = y_plane + (v.co.y - y_plane) * 0.45
        n_flat += 1
print("nose flatten: %d verts (front<=%.2f plane=%.2f)" % (n_flat, y_front_thresh, y_plane))
me.update()

# ---------------- 4) 페인트 데이터 내보내기 ----------------
uvl = me.uv_layers[0]
faces = []
for p in me.polygons:
    reg_cnt = {}
    tri_uv = []
    tri_xyz = []
    for li in p.loop_indices:
        vi = me.loops[li].vertex_index
        u, vv = uvl.data[li].uv
        co = me.vertices[vi].co
        tri_uv.append([float(u), float(vv)])
        tri_xyz.append([float(co.x), float(co.y), float(co.z)])
        r = region_of(dom[vi])
        reg_cnt[r] = reg_cnt.get(r, 0) + 1
    reg = max(reg_cnt.items(), key=lambda kv: kv[1])[0]
    faces.append({"uv": tri_uv, "xyz": tri_xyz, "region": reg})

# 몸통·팔 실측(재조형 후) — 하오리 배치용
tv = [v.co for v in me.vertices if "spine" in dom[v.index]]
torso_y0 = min(p.y for p in tv)
torso_y1 = max(p.y for p in tv)
torso_xm = max(abs(p.x) for p in tv)
ua = head_of.get("bip001 r upperarm")
uc = child_of.get("bip001 r upperarm", ua + Vector((-6, 0, 0)))
arm_r = 0.0
for v in me.vertices:
    if dom[v.index] == "bip001 r upperarm":
        p = closest_on_seg(v.co, ua, uc)
        arm_r = max(arm_r, (v.co - p).length)
print("torso y[%.1f,%.1f] xm=%.1f arm_r=%.2f" % (torso_y0, torso_y1, torso_xm, arm_r))

landmarks = {
    "neck_z": neck_j.z, "head_z": head_j.z, "pelvis_z": pelvis_j.z,
    "spine_y": spine_y,
    "torso_y": [torso_y0, torso_y1], "torso_xm": torso_xm, "arm_r": arm_r,
    "head_box": [hx0, hx1, hy0, hy1, hz0, hz1],
    "eye_z": eye_z,
    "sh_x_после": sh_x - pull,
    "lhand": [lhand_j.x, lhand_j.y, lhand_j.z],
    "rhand": [rhand_j.x, rhand_j.y, rhand_j.z],
    "belt": [pelvis_j.z + 6.0, pelvis_j.z + 11.5],
    "collar": [neck_j.z - 1.0, neck_j.z + 2.6],
    "buttons_z": [pelvis_j.z + 14.0, neck_j.z - 2.5],
}
with open(OUT_JSON, "w") as f:
    json.dump({"faces": faces, "lm": landmarks}, f)
print("json faces=%d -> %s" % (len(faces), OUT_JSON))
for k, v in landmarks.items():
    print("  lm %-12s %s" % (k, v))

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("saved", OUT_BLEND)

# ---------------- 5) AO 베이크 ----------------
# 체형을 바꿨으니 원본 텍스처의 명암은 더 이상 이 형태와 안 맞는다.
# 현재 지오메트리에서 AO 를 구워 "진짜 볼륨 음영"을 새로 얻는다.
AO_PATH = os.path.join(SCR, "ao_bake.png")
try:
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 24
    try:
        sc.cycles.device = "CPU"
    except Exception:
        pass
    ao_img = bpy.data.images.new("AObake", 1024, 1024)
    m = bpy.data.materials.new("bake_mat")
    m.use_nodes = True
    nt = m.node_tree
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = ao_img
    nt.nodes.active = node
    node.select = True
    me.materials.clear()
    me.materials.append(m)

    bpy.ops.object.select_all(action="DESELECT")
    mesh_ob.select_set(True)
    bpy.context.view_layer.objects.active = mesh_ob
    sc.render.bake.use_selected_to_active = False
    sc.render.bake.margin = 8
    bpy.ops.object.bake(type="AO")
    ao_img.filepath_raw = AO_PATH
    ao_img.file_format = "PNG"
    ao_img.save()
    print("AO baked ->", AO_PATH)
except Exception as e:
    print("AO bake FAILED:", e)
