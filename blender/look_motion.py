# -*- coding: utf-8 -*-
"""베기 모션을 **눈으로** 본다. 수치만으로는 "그림이 되는가"를 못 고른다.

두 가지를 뽑는다.
  1) 스트립: 타격 구간을 프레임마다 렌더한다. 넘겨 보면 호가 이어지는지 보인다.
  2) 궤적: 칼끝이 지나간 자리를 리본으로 만들어 임팩트 자세와 같이 한 장에 담는다.
     "호가 화면을 시원하게 가로지르는가"는 이 그림으로만 판단할 수 있다.

액션 만드는 절차는 probe_swing / s6 와 같다(같은 결과를 봐야 하므로).

실행:
  SKILL=combo OUTDIR=renders/history/v74_motion/round1 blender -b -P blender/look_motion.py
  FRAMES="4,6,8,10,12"  안 주면 타격 구간을 자동으로 고른다
  VIEWS="q,side"        q=3/4 앞 · front · side · top
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
importlib.reload(CP)

SKILL = os.environ.get("SKILL", "combo")
OUT = os.environ.get("OUTDIR", os.path.join(ROOT, "renders", "history", "v74_motion"))
os.makedirs(OUT, exist_ok=True)
RESX = int(os.environ.get("RESX", "420"))
RESY = int(os.environ.get("RESY", "520"))

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x = RESX
sc.render.resolution_y = RESY
sc.render.film_transparent = False

arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair", "bladeK",
                                       "gripK", "tsubaK", "pomK", "ringK")))
katana = bpy.data.objects.get("katana_slayer")
zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
xs = [(body.matrix_world @ v.co).x for v in body.data.vertices]
H = max(zs) - min(zs)
FOOT = min(zs)
CTRX = (min(xs) + max(xs)) / 2
if arm.animation_data:
    arm.animation_data_clear()
ps = CP.Poser(arm, H)

SWS = H * float(os.environ.get("KATANA_SCALE", "0.56"))
TIP_L = Vector((0.86 * SWS, 0, 0))          # 칼 로컬 +X = 칼끝 (tune_swing 과 같은 기준)

# LINEAR 집합은 v74 에서 생긴 것이라 옛 combo_poses(백업)로 전후 비교를 찍을 땐 없다.
CFG = {
    "combo": (CP.SEQ, CP.TRAILS, CP.IMPACTS,
              getattr(CP, "ATTACK_LINEAR", set()), CP.LAST),
    "heavy": (CP.HEAVY_SEQ, CP.HEAVY_TRAILS, CP.HEAVY_IMPACTS,
              getattr(CP, "HEAVY_LINEAR", set()), CP.HEAVY_LAST),
    "wide": (CP.WIDE_SEQ, CP.WIDE_TRAILS, CP.WIDE_IMPACTS,
             getattr(CP, "WIDE_LINEAR", set()), CP.WIDE_LAST),
}
SEQ, TR, IMP, LIN, LAST = CFG[SKILL]

# ---------- 액션 (s6.make_action 과 같은 절차) ----------
arm.animation_data_create()
act = bpy.data.actions.new(SKILL)
arm.animation_data.action = act
try:
    act.slots.new(id_type="OBJECT", name="S")
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
for f, p in SEQ:
    ps.apply(p)
    for b in arm.pose.bones:
        b.keyframe_insert("rotation_quaternion", frame=f)
        b.keyframe_insert("location", frame=f)
    arm.keyframe_insert("location", frame=f)
try:
    for lay in act.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        if int(round(kp.co[0])) in LIN:
                            kp.interpolation = "LINEAR"
except Exception:
    pass
CP.relock_grip(ps, SEQ)

# ---------- 칼끝 궤적을 리본으로 ----------
dg = bpy.context.evaluated_depsgraph_get()


def tip_at(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    return (katana.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
            @ TIP_L)


def make_trail(f0, f1, name, rgb):
    pts = []
    for i in range((f1 - f0) * 4 + 1):
        f = f0 + i / 4.0
        sc.frame_set(int(f), subframe=f - int(f))
        bpy.context.view_layer.update()
        km = katana.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
        pts.append(km @ TIP_L)
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = H * 0.012
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1.0)
    ob = bpy.data.objects.new(name, cu)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (rgb[0], rgb[1], rgb[2], 1)
    em.inputs[1].default_value = 6.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    cu.materials.append(mat)
    sc.collection.objects.link(ob)
    return ob


COLORS = [(0.25, 0.75, 1.0), (1.0, 0.55, 0.15), (0.55, 1.0, 0.45)]
trails = [make_trail(a, b, "trail%d" % i, COLORS[i % 3])
          for i, (a, b) in enumerate(TR)]

# ---------- 카메라/조명 ----------
li = bpy.data.lights.new("S", "SUN")
li.energy = 4.5
so = bpy.data.objects.new("S", li)
so.rotation_euler = (math.radians(58), 0, math.radians(-30))
sc.collection.objects.link(so)
li2 = bpy.data.lights.new("S2", "SUN")
li2.energy = 1.6
so2 = bpy.data.objects.new("S2", li2)
so2.rotation_euler = (math.radians(70), 0, math.radians(150))
sc.collection.objects.link(so2)
cam = sc.camera
if cam is None:
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
cam.data.lens = 42
CTR = Vector((CTRX, 0, FOOT + H * 0.58))
ZOOM = float(os.environ.get("ZOOM", "1.0"))    # 궤적 그림은 1.4 로 물러나 호 전체를 담는다
OFFS = {
    "q": Vector((-H * 1.30, -H * 1.45, H * 0.34)),     # 3/4 앞. 게임 시점과 가깝다
    "front": Vector((0, -H * 2.0, H * 0.12)),
    "side": Vector((-H * 2.0, 0, H * 0.12)),
    "top": Vector((0, -0.001, H * 2.4)),
}
VIEWS = {k: CTR + v * ZOOM for k, v in OFFS.items()}


# ★게임은 매 프레임 **가장 낮은 발 본**을 바닥에 붙인다(main.js groundFeet).
# 이걸 안 흉내내면 무릎을 굽힌 프레임에서 발이 공중에 뜬 채로 렌더돼서
# "몸이 안 내려앉는다"고 잘못 판단하게 된다. 3연타는 루트 이동을 안 쓰므로
# 앉는 그림은 전적으로 이 보정이 만든다.
FOOT_BONES = [b for b in arm.pose.bones
              if ("foot" in b.name.lower() or "toe" in b.name.lower())]
HOME_Z = arm.location.z


def ground_feet():
    arm.location.z = HOME_Z
    bpy.context.view_layer.update()
    lo = min((arm.matrix_world @ b.matrix).translation.z for b in FOOT_BONES)
    arm.location.z += (FOOT - lo)
    bpy.context.view_layer.update()


def shoot(tag, view):
    ground_feet()
    pos = VIEWS[view]
    cam.location = pos
    cam.rotation_euler = (CTR - pos).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "%s_%s_%s.png" % (SKILL, tag, view))
    bpy.ops.render.render(write_still=True)


views = [v.strip() for v in os.environ.get("VIEWS", "q,side").split(",") if v.strip()]

# 1) 궤적 그림 (임팩트 자세 + 지나간 자리)
sc.frame_set(IMP[-1])
for v in views:
    shoot("arc", v)

# 2) 스트립 (궤적은 끄고 자세만)
for t in trails:
    t.hide_render = True
if os.environ.get("FRAMES"):
    frames = [int(x) for x in os.environ["FRAMES"].split(",")]
else:
    frames = []
    for (a, b) in TR:
        frames += list(range(a, b + 1, max(1, (b - a) // 4)))
    frames = sorted(set(frames))
for f in frames:
    sc.frame_set(f)
    for v in views[:1]:
        shoot("f%02d" % f, v)
print("rendered ->", OUT, "frames", frames, "views", views)
