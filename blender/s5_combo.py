# -*- coding: utf-8 -*-
# 3연타 콤보 검술 애니메이션 (전신 모션 + 각 타격마다 물의 호흡 궤적)
#   문제였던 점: 정지 구간이 길고 팔만 돌아서 "가만히 서 있는" 영상이 됐음.
#   -> 대기 구간 최소화, 포즈 진폭 대폭 확대, 상체 비틀기 + 스텝(루트 모션) 추가.
# 실행: MODE=keys|anim blender --background --python s5_combo.py
import bpy
import os
import sys
import math
import random
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
SCR = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad"
sys.path.insert(0, BLD)
import build_scenes as BS
import importlib
import fx_water
import combo_poses as CP
importlib.reload(fx_water)
importlib.reload(CP)

MODE = os.environ.get("MODE", "anim")
FPS = 30
OUTDIR = os.path.join(SCR, "anim_combo")
os.makedirs(OUTDIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
sc.render.fps = FPS
try:
    sc.eevee.taa_render_samples = 24
except Exception:
    pass

w = bpy.data.worlds.new("Wdark")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.0, 0.0, 0.004, 1)
for _o in sc.objects:
    if _o.type == "MESH" and (_o.name.startswith("Floor") or _o.name.startswith("Plane")):
        for _m in _o.data.materials:
            if _m and _m.use_nodes:
                for _n in _m.node_tree.nodes:
                    if _n.type == "EMISSION":
                        _n.inputs[0].default_value = (0.0, 0.001, 0.006, 1)

arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh_ob = next(o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("Floor", "Plane")))
katana = bpy.data.objects.get("katana_slayer")
A2W = arm.matrix_world
W2A = A2W.inverted()
ARM_HOME = arm.location.copy()

zs = [(mesh_ob.matrix_world @ v.co).z for v in mesh_ob.data.vertices]
xs = [(mesh_ob.matrix_world @ v.co).x for v in mesh_ob.data.vertices]
ys = [(mesh_ob.matrix_world @ v.co).y for v in mesh_ob.data.vertices]
H = max(zs) - min(zs)
CTR = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
FOOT = min(zs)
SWS = H * float(os.environ.get("KATANA_SCALE", "0.56"))
print("H=%.2f" % H)


# 포즈 정의는 combo_poses.py 가 정본이다. 여기와 s6_export_game 에 각각
# 복제해 두었더니 한쪽만 고쳐서 어긋났다.
# SKILL=heavy 로 일격기(수면참)를 렌더한다.
SKILL = os.environ.get("SKILL", "combo")
if SKILL == "heavy":
    SEQ, LAST = CP.HEAVY_SEQ, CP.HEAVY_LAST
    WINDUP_F, STRIKE_F = CP.HEAVY_WINDUP_F, CP.HEAVY_STRIKE_F
    TRAILS, IMPACTS = CP.HEAVY_TRAILS, CP.HEAVY_IMPACTS
    OUTDIR = os.path.join(SCR, "anim_heavy")
    os.makedirs(OUTDIR, exist_ok=True)
    FX_BIG = 1.9              # 일격기는 파도를 크게
else:
    SEQ, LAST = CP.SEQ, CP.LAST
    WINDUP_F, STRIKE_F = CP.WINDUP_F, CP.STRIKE_F
    TRAILS, IMPACTS = CP.TRAILS, CP.IMPACTS
    FX_BIG = 1.0
print("SKILL =", SKILL)
ps = CP.Poser(arm, H)


def apply(p):
    ps.apply(p)


def key_pose(frame):
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=frame)
        b.keyframe_insert("location", frame=frame)
    arm.keyframe_insert("location", frame=frame)


if arm.animation_data:
    arm.animation_data_clear()
arm.animation_data_create()
act = bpy.data.actions.new("combo")
arm.animation_data.action = act
try:
    slot = act.slots.new(id_type="OBJECT", name="ArmSlot")
    arm.animation_data.action_slot = slot
except Exception as e:
    print("slot:", e)
for f, p in SEQ:
    apply(p)
    key_pose(f)
try:
    for lay in act.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        fr = int(round(kp.co[0]))
                        if fr in WINDUP_F:
                            kp.interpolation = "QUAD"      # 윈드업 -> 타격: 가속
                            kp.easing = "EASE_IN"
                        elif fr in STRIKE_F:
                            kp.interpolation = "QUAD"      # 타격 -> 여파: 급감속
                            kp.easing = "EASE_OUT"
                        else:
                            kp.interpolation = "BEZIER"
                            kp.easing = "EASE_IN_OUT"
except Exception:
    pass
print("posed", len(SEQ))

# ---------------- 궤적 3개 ----------------
dg = bpy.context.evaluated_depsgraph_get()
base_l = Vector((0.50 * SWS, 0, 0))
tip_l = Vector((0.86 * SWS, 0, 0))
SUB = 3
all_now = []
for ti, (r0, r1) in enumerate(TRAILS):
    bases, tips = [], []
    for si in range((r1 - r0) * SUB + 1):
        f = r0 + si / SUB
        sc.frame_set(int(f), subframe=f - int(f))
        M = katana.evaluated_get(dg).matrix_world
        bases.append(M @ base_l)
        tips.append(M @ tip_l)
    n = len(bases)
    sweep = sum((tips[i + 1] - tips[i]).length for i in range(n - 1))
    print("trail%d N=%d sweep=%.2fm" % (ti, n, sweep))
    # 곡률 기반 두께(꺾이는 곳이 두껍게)
    cv = []
    for i in range(n):
        v0 = (tips[max(0, i - 2)] - bases[max(0, i - 2)]).normalized()
        v1 = (tips[min(n - 1, i + 2)] - bases[min(n - 1, i + 2)]).normalized()
        cv.append(math.acos(max(-1.0, min(1.0, v0.dot(v1)))))
    cmx = max(cv) or 1.0
    thick = [0.85 + 0.55 * (c / cmx) ** 0.7 for c in cv]
    sm = [sum(thick[max(0, i - 3):i + 4]) / len(thick[max(0, i - 3):i + 4]) for i in range(n)]
    thick = sm

    # ★ 파도 시트(메인) — 말려 올라가는 마루 + 포말
    wave, wnow, crest_pts = fx_water.build_wave(
        "wave%d" % ti, list(zip(bases, tips)), seed=13 + ti,
        inner=0.12, crest=float(os.environ.get("FX_CREST", "1.15")) * FX_BIG,
        curl_r=float(os.environ.get("FX_CURL", "0.40")) * FX_BIG, curl_turns=1.55,
        rise=float(os.environ.get("FX_RISE", "0.42")) * FX_BIG,
        tail=0.40, strength=1.35, thick=thick)
    nows = [wnow]
    # 보조 가닥(파도 안쪽 결)
    ribbons, nows2, _t = fx_water.build_ribbon_bundle(
        "wt%d" % ti, list(zip(bases, tips)), n_strands=4, seed=7 + ti,
        inner=0.16, strand_w=0.13, gap=0.02,
        curve_boost=2.2, wobble=0.06, radial_swing=0.10,
        tail=0.30, strength=1.15)
    nows = nows + nows2
    for nv in nows:
        fx_water.drive_now(nv, r0 - 1, r1)     # 키프레임 대신 드라이버(확실)
    all_now.extend(nows)

    # 마루 포말 덩어리(손가락/산호 실루엣)
    fmat, fmix = fx_water.make_foam_material("crestM%d" % ti, strength=1.5)
    frng = random.Random(31 + ti)
    for ci in range(0, n, 5):
        p = crest_pts[ci]
        for lobe in range(1):
            rr = H * (0.007 + frng.random() ** 1.6 * 0.016)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rr, location=tuple(p))
            fo = bpy.context.object
            fo.name = "crest%d_%03d_%d" % (ti, ci, lobe)
            fo.scale = (0.7 + frng.random() * 1.3, 0.6 + frng.random() * 0.9,
                        0.8 + frng.random() * 1.4)
            fo.rotation_euler = (frng.uniform(0, 6.28), frng.uniform(0, 6.28), frng.uniform(0, 6.28))
            fo.location = p + Vector((frng.uniform(-1, 1), frng.uniform(-1, 1),
                                      frng.uniform(-0.3, 1.0))).normalized() * H * 0.035
            fo.data.materials.append(fmat)
            fb = int(round(r0 + ci / SUB))
            for f_, s_ in ((1, 0.001), (fb - 1, 0.001), (fb + 1, 1.0),
                           (fb + 9, 1.2), (fb + 13, 0.001)):
                fo.scale = (fo.scale.x * (1 if f_ > 1 else 1), fo.scale.y, fo.scale.z)
                fo.keyframe_insert("scale", frame=f_)
    for f_, a_ in ((1, 0.0), (r0 - 1, 0.0), (r0 + 1, 1.0),
                   (r1 + 8, 1.0), (r1 + 14, 0.0)):
        fmix.inputs[0].default_value = a_
        fmix.inputs[0].keyframe_insert("default_value", frame=f_)

    # 물보라
    dmat, dmix = fx_water.make_foam_material("sprayM%d" % ti, strength=1.6)
    rng = random.Random(11 + ti)
    for i in range(26):
        si = rng.randrange(1, n - 1)
        p0 = tips[si].lerp(bases[si], rng.random())
        v = (tips[min(si + 2, n - 1)] - tips[max(si - 2, 0)])
        v = v.normalized() if v.length > 1e-6 else Vector((0, 0, 1))
        side = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
        rr = H * (0.003 + rng.random() ** 2 * 0.008)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rr, location=tuple(p0))
        d = bpy.context.object
        d.name = "spray%d_%03d" % (ti, i)
        d.data.materials.append(dmat)
        fb = int(round(r0 + si / SUB))
        life = int(5 + rng.random() * 7)
        d.location = p0
        d.keyframe_insert("location", frame=fb)
        d.location = p0 + v * H * rng.uniform(0.05, 0.18) + side * H * rng.uniform(0.03, 0.14)
        d.keyframe_insert("location", frame=fb + life)
        for f_, s_ in ((1, 0.001), (fb - 1, 0.001), (fb + 1, 1.0),
                       (fb + life - 2, 1.0), (fb + life, 0.001)):
            d.scale = (s_, s_, s_)
            d.keyframe_insert("scale", frame=f_)
    for f_, a_ in ((1, 0.0), (r0 - 1, 0.0), (r0 + 1, 1.0),
                   (r1 + 6, 1.0), (r1 + 12, 0.0)):
        dmix.inputs[0].default_value = a_
        dmix.inputs[0].keyframe_insert("default_value", frame=f_)

# 전집중 광원
gl = bpy.data.lights.new("focus", "POINT")
gl.color = (0.35, 0.75, 1.0)
gl.shadow_soft_size = H * 0.12
glo = bpy.data.objects.new("focus", gl)
sc.collection.objects.link(glo)
glo.parent = katana
glo.location = (0.45 * SWS, 0, 0)
keys = [(1, 0.0)]
for im in IMPACTS:
    keys += [(im - 5, 3.0), (im, 11.0), (im + 5, 3.5)]
keys += [(LAST, 0.0)]
for f, e in keys:
    gl.energy = e
    gl.keyframe_insert("energy", frame=f)

# ---------------- 조명 보강(캐릭터가 어둡지 않게) ----------------
key_l = bpy.data.lights.new("keyL", "AREA")
key_l.energy = 420
key_l.size = H
klo = bpy.data.objects.new("keyL", key_l)
klo.location = (CTR.x + H * 0.9, CTR.y - H * 1.1, FOOT + H * 1.5)
sc.collection.objects.link(klo)
d = Vector(CTR) - klo.location
klo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# ---------------- 카메라 ----------------
cam = sc.camera
camd = cam.data
base = Vector((CTR.x + H * 1.15, CTR.y - H * 2.0, FOOT + H * 0.80))
tgt = Vector((CTR.x - H * 0.05, CTR.y, FOOT + H * 0.58))


def key_cam(frame, pos, target, lens):
    cam.location = pos
    dd = Vector(target) - Vector(pos)
    cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
    camd.lens = lens
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)
    camd.keyframe_insert("lens", frame=frame)


key_cam(1, base, tgt, 40)
key_cam(12, base + Vector((-H * 0.10, H * 0.12, 0)), tgt, 44)
key_cam(22, base + Vector((H * 0.10, H * 0.06, H * 0.05)), tgt, 42)
key_cam(36, base + Vector((-H * 0.05, H * 0.22, -H * 0.05)), tgt, 48)
key_cam(LAST, base, tgt, 40)

sc.frame_start = 1
sc.frame_end = LAST
if MODE == "keys":
    sc.render.resolution_x = 520
    sc.render.resolution_y = 680
    for f in range(1, LAST + 1, 3):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUTDIR, "k_%03d.png" % f)
        bpy.ops.render.render(write_still=True)
    print("keys done")
else:
    sc.render.resolution_x = 720
    sc.render.resolution_y = 940
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.join(OUTDIR, "f_")
    bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, "combo.blend"))
print("DONE", OUTDIR)
