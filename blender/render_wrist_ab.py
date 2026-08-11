# -*- coding: utf-8 -*-
"""파지·손목 before/after 접사를 같은 카메라 규칙으로 찍는다 (13-손목).

    GLB=web/basic2.glb TAG=after OUTDIR=renders/history/v99_wave13/wrist/after \
      blender -b -P blender/render_wrist_ab.py

★접사는 '고정 카메라'로 찍으면 판정이 안 된다. 자세마다 손이 도는 만큼 카메라도
  같이 돌려야 같은 것을 본다. 그래서 컷마다 기준을 기하로 잡는다.
    grip   두 손 사이를 보되 **자루축에 수직**인 방향에서(자루를 팔이 가리지 않게)
    rfist  오른 주먹. **자루축과 팔축 둘 다에 수직**인 방향에서
           (자루가 손가락 사이로 지나는지 / 손등을 뚫는지가 이 방향에서만 보인다)
    lwrist 왼 손목. **굽힘 평면의 법선** 방향에서(꺾인 각이 실제 각으로 보인다)
  ±두 방향 중에서는 몸 반대쪽을 고른다(머리·어깨에 안 가리게).

손잡이: GLB / TAG / OUTDIR / POSES("Idle:1,Heavy:34,..." 형식으로 덮어쓰기)
"""
import bpy
import os
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.environ.get("GLB") or os.path.join(ROOT, "web", "basic2.glb")
if not os.path.isabs(GLB):
    GLB = os.path.join(ROOT, GLB)
TAG = os.environ.get("TAG", "x")
OUTDIR = os.environ.get("OUTDIR") or os.path.join(
    ROOT, "renders", "history", "v99_wave13", "wrist", TAG)
POSES = os.environ.get("POSES", "Idle:1,Walk:5,Run:5,Attack:13,Heavy:16,"
                                "Heavy:34,Heavy:47,Wide:14,Jump:7")
HAND_R, HAND_L = "Bip001 R Hand", "Bip001 L Hand"
FORE_L = "Bip001 L Forearm"
PELVIS = "Bip001 Pelvis"

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath=GLB)
if sc.render.fps != 30:
    sc.render.fps = 30
arm = next(o for o in sc.objects if o.type == "ARMATURE")
for o in list(sc.objects):
    if o.type == "MESH" and any(c.name == "glTF_not_exported"
                                for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)
MESH = [o for o in sc.objects if o.type == "MESH"]
BODY = [o for o in MESH if not o.name.startswith(("SW_", "SH_"))]
SW = next((o for o in MESH if o.name.startswith("SW_nokseun")), None)
A2W = arm.matrix_world

for b in arm.pose.bones:
    b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
zs = []
for o in BODY:
    zs += [(o.matrix_world @ v.co).z for v in o.data.vertices]
H = max(zs) - min(zs)
HM = A2W @ arm.pose.bones[HAND_R].matrix
HS = HM.to_3x3().to_scale()[0]
HMi = HM.inverted()
UD = max((HMi @ (SW.matrix_world @ v.co) for v in SW.data.vertices),
         key=lambda p: p.length).normalized() if SW else Vector((0, 0, 1))


def fist_c(bone):
    """주먹 중심(손뼈 로컬, 스케일 포함해서 월드로 바로 더할 수 있게)."""
    M = (A2W @ arm.pose.bones[bone].matrix).inverted()
    P = []
    for o in BODY:
        g = o.vertex_groups.get(bone)
        if g is None:
            continue
        for v in o.data.vertices:
            w = next((x.weight for x in v.groups if x.group == g.index), 0.0)
            if w > 0.5:
                P.append(M @ (o.matrix_world @ v.co))
    C = Vector((sum(p.x for p in P) / len(P), sum(p.y for p in P) / len(P),
                sum(p.z for p in P) / len(P)))
    return C * HS


FCR, FCL = fist_c(HAND_R), fist_c(HAND_L)
arm.data.pose_position = "POSE"

os.makedirs(OUTDIR, exist_ok=True)
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids \
    else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x = sc.render.resolution_y = 620
for e, rot in ((4.2, (math.radians(52), 0, math.radians(-30))),
               (2.0, (math.radians(-35), 0, math.radians(140))),
               (1.3, (math.radians(8), 0, math.radians(62)))):
    li = bpy.data.lights.new("S", "SUN")
    li.energy = e
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = rot
    sc.collection.objects.link(so)
cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam


def use(act):
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def pw(bn):
    m = (A2W @ arm.pose.bones[bn].matrix).copy()
    r = m.to_3x3()
    r.normalize()
    return m.translation.copy(), r


def shoot(path, tgt, eye, dist, lens=55):
    cam.data.lens = lens
    cam.location = tgt + eye.normalized() * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def away(v, p):
    """몸 반대쪽 부호를 고른다(머리·어깨에 가리지 않게)."""
    d = p - pw(PELVIS)[0]
    d.z *= 0.2
    return v if v.dot(d) >= 0 else -v


print("[%s] %s  키 %.4f" % (TAG, os.path.basename(GLB), H))
for item in POSES.split(","):
    nm, fs = item.split(":")
    act = bpy.data.actions.get(nm.strip())
    if not act:
        continue
    use(act)
    f = int(fs)
    sc.frame_set(f)
    bpy.context.view_layer.update()
    Rp, Rr = pw(HAND_R)
    Lp, Lr = pw(HAND_L)
    Ep, _ = pw(FORE_L)
    uh = (Rr @ UD).normalized()
    rc = Rp + Rr @ FCR                                  # 오른 주먹 중심(월드)
    lc = Lp + Lr @ FCL
    ra = (rc - Rp).normalized()
    # 1) 두 손 + 자루
    mid = (rc + lc) / 2
    e = uh.cross(Vector((0, 0, 1)))
    if e.length < 1e-3:
        e = uh.cross(Vector((0, 1, 0)))
    shoot(os.path.join(OUTDIR, "grip_%s_f%02d.png" % (nm, f)), mid,
          away(e.normalized(), mid), H * 0.55, 60)
    # 2) 오른 주먹: 자루축·팔축 둘 다에 수직인 눈
    e2 = uh.cross(ra)
    if e2.length < 1e-3:
        e2 = uh.cross(Vector((0, 0, 1)))
    shoot(os.path.join(OUTDIR, "rfist_%s_f%02d.png" % (nm, f)), rc,
          away(e2.normalized(), rc), H * 0.42, 52)
    # 3) 왼 손목: 굽힘 평면의 법선
    fdir = (Lp - Ep).normalized()
    hdir = (lc - Lp).normalized()
    e3 = fdir.cross(hdir)
    if e3.length < 1e-3:
        e3 = fdir.cross(Vector((0, 0, 1)))
    bend = math.degrees(fdir.angle(hdir))
    shoot(os.path.join(OUTDIR, "lwrist_%s_f%02d.png" % (nm, f)), (Lp + lc) / 2,
          away(e3.normalized(), lc), H * 0.44, 52)
    # 4) 전신(맥락)
    ctr = pw(PELVIS)[0] + Vector((0, 0, H * 0.12))
    shoot(os.path.join(OUTDIR, "body_%s_f%02d.png" % (nm, f)), ctr,
          Vector((-0.75, -0.62, 0.16)), H * 1.9, 50)
    print("   %-7s f%02d  왼손목 기하각 %5.1f도" % (nm, f, bend))

print("RENDER_DONE %s" % OUTDIR)
