# -*- coding: utf-8 -*-
# 스킬 애니메이션 v2: "칼에 붙는" 물의 호흡
#   - 트레일: 매 프레임 칼밑-칼끝 월드 좌표를 구워 스윕 리본 생성,
#             나이(now-birth) 기반 머티리얼로 별똥별 꼬리처럼 칼을 따라다니게
#   - 랩: 칼날을 휘감는 나선 물줄기 2가닥(칼 로컬 X축 회전으로 스핀)
#   - 거품 소용돌이 + 물방울: 타격 구간 칼끝 위치에 팝
# 실행: SKILL=slash MODE=keys|anim blender --background --python s4_skill.py
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
importlib.reload(fx_water)

SKILL = os.environ.get("SKILL", "slash")
MODE = os.environ.get("MODE", "anim")
FPS = 30

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
sc.render.fps = FPS
try:
    sc.eevee.taa_render_samples = 32
    sc.eevee.use_motion_blur = False
except Exception:
    pass

# 레퍼런스는 배경이 거의 검다(이펙트 고대비). 월드/바닥을 어둡게.
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
mesh_ob = next(o for o in sc.objects if o.type == "MESH" and "Floor" not in o.name)
katana = bpy.data.objects.get("katana_slayer")

A2W = arm.matrix_world
W2A = A2W.inverted()


def pb(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


def swing(key, axis_world, deg):
    b = pb(key)
    if b is None:
        print("!bone", key)
        return
    ax = (W2A.to_3x3() @ Vector(axis_world)).normalized()
    head = b.matrix.translation.copy()
    R = Matrix.Rotation(math.radians(deg), 4, ax)
    b.matrix = Matrix.Translation(head) @ R @ Matrix.Translation(-head) @ b.matrix
    bpy.context.view_layer.update()


def reset_pose():
    for b in arm.pose.bones:
        b.rotation_mode = "QUATERNION"
        b.matrix_basis = Matrix()
    bpy.context.view_layer.update()


def apply_pose(spec):
    reset_pose()
    for key, axis, deg in spec:
        swing(key, axis, deg)


def key_pose(frame):
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=frame)
        b.keyframe_insert("location", frame=frame)


X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

IDLE = [("l upperarm", Y, 75), ("l forearm", Y, 10),
        ("r upperarm", Y, -52), ("r forearm", Y, -60), ("r forearm", X, -28)]
BREATH = [("l upperarm", Y, 74), ("l forearm", Y, 11),
          ("r upperarm", Y, -50), ("r forearm", Y, -62), ("r forearm", X, -26),
          ("spine", X, -3)]
READY = [("spine", Z, -12), ("spine", X, 5),
         ("l upperarm", Y, 66), ("l forearm", Y, 28),
         ("r upperarm", Y, -46), ("r forearm", Y, -76), ("r forearm", X, -18),
         ("head", Z, -6)]
# 어깨 위로 크게 치켜들고(칼끝 우상단 하늘)
WINDUP = [("spine", Z, -30), ("spine", X, 8),
          ("l upperarm", Y, 60), ("l forearm", Y, 30),
          ("r upperarm", Y, -128), ("r forearm", Y, -26),
          ("head", Z, -12)]
# 袈裟 대각선으로 좌하단까지 크게 쓸어내림
STRIKE = [("spine", Z, 42), ("spine", X, -8),
          ("l upperarm", Y, 88), ("l upperarm", Z, 26), ("l forearm", Y, 4),
          ("r upperarm", Y, -24), ("r upperarm", Z, -78), ("r forearm", Y, -6),
          ("head", Z, 18)]
FOLLOW = [("spine", Z, 30), ("spine", X, -4),
          ("l upperarm", Y, 80), ("l forearm", Y, 12),
          ("r upperarm", Y, -30), ("r upperarm", Z, -62), ("r forearm", Y, -26),
          ("head", Z, 12)]

SPIN_A = [("spine", Z, -70), ("l upperarm", Y, 70), ("l forearm", Y, 20),
          ("r upperarm", Y, -70), ("r upperarm", Z, 40), ("r forearm", Y, -24)]
SPIN_B = [("spine", Z, 80), ("l upperarm", Y, 82), ("l upperarm", Z, 30),
          ("r upperarm", Y, -30), ("r upperarm", Z, -90), ("r forearm", Y, -8)]
THRUST_R = [("spine", Z, -28), ("spine", X, 9),
            ("l upperarm", Y, 64), ("l forearm", Y, 36),
            ("r upperarm", Y, -62), ("r upperarm", Z, 36), ("r forearm", Y, -88)]
THRUST_S = [("spine", Z, 10), ("spine", X, -7),
            ("l upperarm", Y, 78), ("l forearm", Y, 10),
            ("r upperarm", Y, -74), ("r upperarm", Z, -12), ("r forearm", Y, -2)]

SEQ = {
    "slash": [(1, IDLE), (12, BREATH), (22, READY), (32, WINDUP),
              (38, STRIKE), (46, FOLLOW), (60, BREATH), (72, IDLE)],
    "spin": [(1, IDLE), (12, BREATH), (20, READY), (28, SPIN_A),
             (36, SPIN_B), (44, FOLLOW), (58, BREATH), (70, IDLE)],
    "thrust": [(1, IDLE), (12, BREATH), (22, READY), (32, THRUST_R),
               (38, THRUST_S), (48, THRUST_S), (60, BREATH), (72, IDLE)],
}
REC = {"slash": (30, 52), "spin": (26, 50), "thrust": (30, 50)}[SKILL]
seq = SEQ[SKILL]
LAST = seq[-1][0]
IMPACT = {"slash": 38, "spin": 36, "thrust": 38}[SKILL]

zs = [(mesh_ob.matrix_world @ v.co).z for v in mesh_ob.data.vertices]
xs = [(mesh_ob.matrix_world @ v.co).x for v in mesh_ob.data.vertices]
ys = [(mesh_ob.matrix_world @ v.co).y for v in mesh_ob.data.vertices]
H = max(zs) - min(zs)
CTR = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
FOOT = min(zs)
SWS = H * float(os.environ.get("KATANA_SCALE", "0.56"))     # 검 스케일(convert 와 동일)
print("H=%.2f sword_scale=%.2f" % (H, SWS))

# ---------------- 포즈 액션 굽기 ----------------
if arm.animation_data:
    arm.animation_data_clear()
arm.animation_data_create()
act = bpy.data.actions.new("skill_" + SKILL)
arm.animation_data.action = act
try:
    slot = act.slots.new(id_type="OBJECT", name="ArmSlot")
    arm.animation_data.action_slot = slot
except Exception as e:
    print("slot:", e)
for f, spec in seq:
    apply_pose(spec)
    key_pose(f)
try:
    for lay in act.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "BEZIER"
                        kp.easing = "EASE_IN_OUT"
except Exception:
    pass
print("action keys ok")

# ---------------- 칼 궤적 굽기 ----------------
dg = bpy.context.evaluated_depsgraph_get()
base_l = Vector((0.52 * SWS, 0, 0))     # 칼 바깥쪽 절반만 궤적으로(얇은 별똥별 띠)
tip_l = Vector((0.84 * SWS, 0, 0))
R0, R1 = REC
SUB = int(os.environ.get("FX_SUB", "3"))          # 프레임당 서브샘플(궤적 각짐 방지)
bases, tips = [], []
steps = (R1 - R0) * SUB
for si in range(steps + 1):
    f = R0 + si / SUB
    sc.frame_set(int(f), subframe=f - int(f))
    ke = katana.evaluated_get(dg)
    M = ke.matrix_world
    bases.append(M @ base_l)
    tips.append(M @ tip_l)
N = len(bases)
sweep = sum((tips[i + 1] - tips[i]).length for i in range(N - 1))
print("trail baked N=%d (sub=%d) sweep=%.2fm" % (N, SUB, sweep))

# 다발 리본 (레퍼런스 실측: 가닥 인접 배치 + 곡률 연동 두께 + 하드 온/오프)
samples = list(zip(bases, tips))
N_STR = int(os.environ.get("FX_STRANDS", "9"))
TAIL = float(os.environ.get("FX_TAIL", "0.34"))
ribbons, now_nodes, thickness = fx_water.build_ribbon_bundle(
    "wtrail", samples, n_strands=N_STR, seed=7,
    inner=float(os.environ.get("FX_INNER", "0.24")),
    strand_w=float(os.environ.get("FX_SW", "0.155")),
    gap=-0.030,
    curve_boost=float(os.environ.get("FX_CURVE", "2.8")),
    wobble=float(os.environ.get("FX_WOBBLE", "0.085")),
    radial_swing=float(os.environ.get("FX_SWING", "0.13")),
    tail=TAIL, strength=float(os.environ.get("FX_STR", "4.2")))
print("ribbons: %d  thick %.2f~%.2f" % (len(ribbons), min(thickness), max(thickness)))


def key_now(frame, val):
    for nv in now_nodes:
        nv.outputs[0].default_value = val
        nv.outputs[0].keyframe_insert("default_value", frame=frame)


key_now(R0 - 1, -0.002)
key_now(R1, 1.0)
key_now(min(LAST, R1 + int(TAIL * (R1 - R0)) + 6), 1.0 + TAIL + 0.06)
for nv in now_nodes:
    try:
        for lay in nv.id_data.animation_data.action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"
    except Exception:
        pass

# 거품: 바깥 모서리에만, 시간이 갈수록 개수 3배로 증가(레퍼런스: 물면적 대비 10%->29%)
foam_mat, foam_mix = fx_water.make_foam_material("foamM", strength=13.0)
NF = int(os.environ.get("FX_FOAM", "46"))
frng = random.Random(21)
for i in range(NF):
    si = frng.randrange(1, N - 1)
    bpos, tpos = samples[si]
    axis = tpos - bpos
    L = axis.length
    adir = axis.normalized() if L > 1e-6 else Vector((1, 0, 0))
    r_out = 0.24 + N_STR * 0.115 * thickness[si]
    p = bpos + adir * (L * r_out * frng.uniform(0.97, 1.05))
    rr = H * (0.010 + frng.random() ** 1.6 * 0.030)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rr, location=tuple(p))
    fo = bpy.context.object
    fo.name = "foam%03d" % i
    fo.scale = (1.0 + frng.random(), 0.55 + frng.random() * 0.5, 0.7 + frng.random() * 0.7)
    fo.rotation_euler = (frng.uniform(0, 6.28), frng.uniform(0, 6.28), frng.uniform(0, 6.28))
    fo.data.materials.append(foam_mat)
    fb = int(round(R0 + si / SUB))
    # 늦게 태어난 거품일수록 오래 남아 "끓는" 누적감
    grow = int(3 + 16 * (i / max(1, NF - 1)))
    for f, sc_ in ((1, 0.001), (fb - 1, 0.001), (fb + 1, 1.0),
                   (fb + grow, 1.25), (fb + grow + 3, 0.001)):
        fo.scale = (fo.scale.x if f > 1 else fo.scale.x, fo.scale.y, fo.scale.z)
        fo.keyframe_insert("scale", frame=f)
print("foam:", NF)
for f, a_ in ((1, 0.0), (R0 - 1, 0.0), (R0 + 1, 1.0),
              (LAST - 14, 1.0), (LAST - 6, 0.0)):
    foam_mix.inputs[0].default_value = a_
    foam_mix.inputs[0].keyframe_insert("default_value", frame=f)

# ---------------- 칼날 랩(나선 물줄기) ----------------
def build_wrap(tag, phase, r0, thick):
    n = 120
    turns = 3.2
    vv, ff, uu = [], [], []
    x0, x1 = 0.10 * SWS, 0.80 * SWS
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        a = phase + t * turns * math.tau
        r = r0 * (1.0 - 0.55 * t)
        cy = math.cos(a) * r
        cz = math.sin(a) * r
        w = thick * (1.0 - 0.6 * t)
        # 리본 폭은 축방향
        vv.append((x - w, cy, cz))
        uu.append((t, 0))
        vv.append((x + w, cy, cz))
        uu.append((t, 1))
    for i in range(n):
        a = i * 2
        ff.append((a, a + 2, a + 3, a + 1))
    ob = BS.new_mesh_obj("wrap_" + tag, vv, ff, uvs=uu)
    m = bpy.data.materials.new("wrap_" + tag)
    m.use_nodes = True
    m.blend_method = "BLEND"
    nt2 = m.node_tree
    nt2.nodes.clear()
    o2 = nt2.nodes.new("ShaderNodeOutputMaterial")
    uv2 = nt2.nodes.new("ShaderNodeUVMap")
    sp2 = nt2.nodes.new("ShaderNodeSeparateXYZ")
    rp2 = nt2.nodes.new("ShaderNodeValToRGB")
    rp2.color_ramp.elements[0].position = 0.0
    rp2.color_ramp.elements[0].color = (*[c / 255 for c in (0xBF, 0xEF, 0xFF)], 1)
    rp2.color_ramp.elements[1].position = 1.0
    rp2.color_ramp.elements[1].color = (*[c / 255 for c in (0x11, 0x73, 0xD4)], 1)
    em2 = nt2.nodes.new("ShaderNodeEmission")
    em2.name = "WEM"
    em2.inputs[1].default_value = 0.0
    tr2 = nt2.nodes.new("ShaderNodeBsdfTransparent")
    mx2 = nt2.nodes.new("ShaderNodeMixShader")
    mx2.inputs[0].default_value = 0.85
    nt2.links.new(uv2.outputs[0], sp2.inputs[0])
    nt2.links.new(sp2.outputs[0], rp2.inputs[0])
    nt2.links.new(rp2.outputs[0], em2.inputs[0])
    nt2.links.new(tr2.outputs[0], mx2.inputs[1])
    nt2.links.new(em2.outputs[0], mx2.inputs[2])
    nt2.links.new(mx2.outputs[0], o2.inputs[0])
    ob.data.materials.append(m)
    ob.parent = katana
    return ob, em2


wraps = []
for ph, rr, th in ((0, 0.075 * SWS, 0.020 * SWS), (math.pi, 0.058 * SWS, 0.014 * SWS)):
    wraps.append(build_wrap("w%d" % int(ph), ph, rr, th))
for i, (wob, wem) in enumerate(wraps):
    for f, rot in ((1, 0), (LAST, math.tau * 3.0)):
        wob.rotation_euler = (rot + i * 1.7, 0, 0)
        wob.keyframe_insert("rotation_euler", frame=f)
    for f, e in ((1, 0.0), (14, 0.0), (24, 2.4), (IMPACT, 4.0),
                 (IMPACT + 10, 1.6), (58, 0.0)):
        wem.inputs[1].default_value = e
        wem.inputs[1].keyframe_insert("default_value", frame=f)

# ---------------- 물보라(레퍼런스: 작고 불규칙한 흰 파편이 촘촘히) ----------------
rng = random.Random(5)
dmat, dmix = fx_water.make_foam_material("dropletM", strength=16.0)
spray = []
NDROP = int(os.environ.get("FX_DROPS", "90"))
for i in range(NDROP):
    si = rng.randrange(2, N - 2)
    f_birth = R0 + si / SUB
    if not (IMPACT - 6 <= f_birth <= IMPACT + 8):
        continue
    p0 = tips[si].lerp(bases[si], rng.random())          # 칼 축 위 임의 지점
    v = (tips[min(si + 2, N - 1)] - tips[max(si - 2, 0)])
    v = v.normalized() if v.length > 1e-6 else Vector((0, 0, 1))
    side = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
    r = H * (0.004 + rng.random() ** 2 * 0.013)          # 작은 것이 훨씬 많게
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=tuple(p0))
    d = bpy.context.object
    d.name = "spray%03d" % i
    d.scale = (1.0 + rng.random() * 1.8, 1.0, 1.0)       # 길쭉한 파편
    d.rotation_euler = v.to_track_quat("X", "Z").to_euler()
    d.data.materials.append(dmat)
    fb = int(round(f_birth))
    life = int(6 + rng.random() * 8)
    d.location = p0
    d.keyframe_insert("location", frame=fb)
    d.location = p0 + v * H * rng.uniform(0.05, 0.20) + side * H * rng.uniform(0.03, 0.16)
    d.keyframe_insert("location", frame=fb + life)
    sx = d.scale.x
    for f, sc_ in ((1, 0.001), (fb - 1, 0.001), (fb + 1, 1.0),
                   (fb + life - 2, 1.0), (fb + life, 0.001)):
        d.scale = (sx * sc_, sc_, sc_)
        d.keyframe_insert("scale", frame=f)
    spray.append(d)
for f, a_ in ((1, 0.0), (IMPACT - 7, 0.0), (IMPACT - 4, 1.0),
              (IMPACT + 8, 1.0), (IMPACT + 16, 0.0)):
    dmix.inputs[0].default_value = a_
    dmix.inputs[0].keyframe_insert("default_value", frame=f)
print("spray:", len(spray))

# ---------------- 전집중 광원 ----------------
gl = bpy.data.lights.new("focus", "POINT")
gl.color = (0.35, 0.75, 1.0)
gl.shadow_soft_size = H * 0.12
glo = bpy.data.objects.new("focus", gl)
sc.collection.objects.link(glo)
glo.parent = katana
glo.location = (0.45 * SWS, 0, 0)
for f, e in ((1, 0.0), (20, 10.0), (32, 26.0), (IMPACT, 140.0),
             (IMPACT + 8, 30.0), (IMPACT + 18, 0.0), (LAST, 0.0)):
    gl.energy = e
    gl.keyframe_insert("energy", frame=f)

# ---------------- 카메라 ----------------
cam = sc.camera
camd = cam.data
base = Vector((CTR.x + H * 0.95, CTR.y - H * 2.05, FOOT + H * 0.72))
tgt = Vector((CTR.x - H * 0.05, CTR.y, FOOT + H * 0.58))


def key_cam(frame, pos, target, lens):
    cam.location = pos
    d = Vector(target) - Vector(pos)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    camd.lens = lens
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)
    camd.keyframe_insert("lens", frame=frame)


key_cam(1, base, tgt, 42)
key_cam(IMPACT - 2, base + Vector((-H * 0.06, H * 0.12, 0)), tgt, 46)
key_cam(IMPACT + 12, base + Vector((-H * 0.02, H * 0.05, 0)), tgt, 44)
key_cam(LAST, base, tgt, 42)

# ---------------- 출력 ----------------
sc.frame_start = 1
sc.frame_end = LAST
OUTDIR = os.path.join(SCR, "anim_" + SKILL)
os.makedirs(OUTDIR, exist_ok=True)
if MODE == "keys":
    sc.render.resolution_x = 640
    sc.render.resolution_y = 820
    for f in (22, 32, IMPACT, IMPACT + 4, IMPACT + 9, IMPACT + 14):
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUTDIR, "key_%03d.png" % f)
        bpy.ops.render.render(write_still=True)
        print("key", f)
else:
    sc.render.resolution_x = 720
    sc.render.resolution_y = 940
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.join(OUTDIR, "f_")
    bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, "skill_%s.blend" % SKILL))
print("DONE", OUTDIR)
