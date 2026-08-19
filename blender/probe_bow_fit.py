# -*- coding: utf-8 -*-
"""손에 드는 활(BW_bow)의 배치를 **게임 카메라 각도**에서 맞춰 보는 시험대.

s11_archer.py 를 매번 다시 굽지 않고 빠르게 돌려 보려고 web/archer.glb 를 읽는다.
★archer.glb 는 s11 의 결과물이다. **여기서는 읽기만** 하고 s11 의 입력으로는 절대 안 쓴다
  (LOG 함정 15). 최종 산출은 s11_archer.py 가 원본 Meshy glb 에서 다시 굽는다.

★렌더 각도가 이 레포에서 가장 비싼 함정이다(LOG 1위)
  게임 카메라 pitch 49.3도에서는 월드 1m 위 = 화면 43px 위, 월드 1m 앞 = 화면 47px 위라
  "아래로"와 "앞으로"가 상쇄된다. 블렌더 정면 렌더로 판정하면 또 기각당한다.
  그래서 여기서는 **고도 49.3도** 카메라로만 판정한다.

★기준 포즈 비교 결론(BW_REF, 2026-08-19)
  draw(Attack 만작) 로 정했다. idle 로 잡아 보면 만작에서 활이 **가로로 눕는다** -
  쏘는 그림이 통째로 망가진다. 대신 draw 기준은 Idle/Walk 에서 활이 몸을 가로질러
  비스듬히 눕는데, 등짐 활을 지운 뒤에는 "활을 어깨에 걸친" 그림으로 읽혀 무해했다.
  (활은 손 뼈에 강체로 붙으므로 둘 다는 원리적으로 안 된다)

실행: blender --background --python blender/probe_bow_fit.py
환경변수: BW_LEN(활길이/키, 기본 0.68) BW_ROLL(캔트 각, 기본 15)
          BW_GX/BW_GY/BW_GZ(손아귀 오프셋 m) DRAW_F(기준 프레임, 기본 11)
"""
import bpy
import os
import sys
import math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import bow_mesh as BM                                  # noqa: E402

GLB = os.path.join(ROOT, "web/archer.glb")
OUT = os.environ.get("BW_OUT", os.path.join(ROOT, "renders/v99_wave21_bow/fit"))
os.makedirs(OUT, exist_ok=True)
BONE = "Bip001 L Hand"
DRAW_F = int(os.environ.get("DRAW_F", "11"))
ROLL = math.radians(float(os.environ.get("BW_ROLL", "15")))
GX = float(os.environ.get("BW_GX", "0.0"))
GY = float(os.environ.get("BW_GY", "0.0"))
GZ = float(os.environ.get("BW_GZ", "0.0"))

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH" and o.name.startswith("char"))
for o in list(sc.objects):
    if o.type == "MESH" and o is not body:
        print("잡 메시 제거:", o.name)
        bpy.data.objects.remove(o, do_unlink=True)
A2W = arm.matrix_world
for a in bpy.data.actions:
    a.use_fake_user = True


def use(act):
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def wp(n):
    return (A2W @ arm.pose.bones[n].matrix).translation.copy()


# ---------------------------------------------------------------- 실측
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
H = max(zs) - min(zs)
BODY_Z = (min(zs), max(zs))
M_rest = A2W @ arm.pose.bones[BONE].matrix
print("[실측] 키 %.4f  몸통 z %.4f~%.4f" % (H, BODY_Z[0], BODY_Z[1]))

# 만작(Attack f11)은 늘 재 둔다 - 당긴 거리(시위 V 자 깊이)의 근거가 여기서만 나온다.
arm.data.pose_position = "POSE"
use(bpy.data.actions["Attack"])
sc.frame_set(DRAW_F)
bpy.context.view_layer.update()
M_draw = A2W @ arm.pose.bones[BONE].matrix
Lh = wp("Bip001 L Hand")
Rh = wp("Bip001 R Hand")
Lf = wp("Bip001 L Forearm")
draw_len = (Lh - Rh).length
print("[만작 f%d] 왼손(%.3f,%.3f,%.3f) 오른손(%.3f,%.3f,%.3f) 당긴거리 %.3f"
      % (DRAW_F, Lh.x, Lh.y, Lh.z, Rh.x, Rh.y, Rh.z, draw_len))

# ★기준 포즈 선택. 두 갈래를 나란히 보고 고르려고 스위치로 뒀다.
#   draw = Attack 만작. 쏘는 그림(캡처컷)이 정확해지는 대신, 손 뼈가 90도 다르게 도는
#          Idle/Walk 에서 활이 몸을 가로질러 눕는다.
#   idle = Idle. 걷고 서 있는 95% 의 시간에 활이 세로로 서는 대신, 만작에서 활이 눕는다.
#   ★활은 손 뼈에 강체로 붙으므로 **둘 다는 안 된다.** 어느 쪽을 살릴지가 판정거리다.
REF = os.environ.get("BW_REF", "draw")
if REF == "idle":
    use(bpy.data.actions["Idle"])
    sc.frame_set(17)
    bpy.context.view_layer.update()
    M_pose = A2W @ arm.pose.bones[BONE].matrix
    Ih = wp("Bip001 L Hand")
    If_ = wp("Bip001 L Forearm")
    print("[기준=Idle f17] 왼손(%.3f,%.3f,%.3f)" % (Ih.x, Ih.y, Ih.z))
else:
    M_pose = M_draw
print("[기준 포즈] %s" % REF)

# ---------------------------------------------------------------- 기준 좌표계
# ey = 시위를 당기는 방향(왼손 -> 오른손). 실측 벡터를 그대로 쓴다.
#      이렇게 잡아야 만작에서 **시위 V 자의 꼭짓점이 정확히 시위 손 자리**에 온다.
if REF == "idle":
    # Idle 기준: 활은 세로로 서고, 활 평면은 몸 옆으로 살짝 열린다.
    #   ey(시위 쪽) 는 몸 안쪽(-X 방향 = 캐릭터 오른쪽)으로 잡는다. 그래야 시위가 몸 쪽,
    #   활채 등이 바깥을 본다(옆구리에 세워 든 활).
    ey = Vector((-1.0, 0.0, 0.0)).normalized()
else:
    ey = (Rh - Lh).normalized()
# ez = 위. ey 와 직교화한다(활채는 위아래로 뻗는다).
ez = (Vector((0, 0, 1)) - ey * Vector((0, 0, 1)).dot(ey)).normalized()
ex = ey.cross(ez)                       # 오른손 좌표계: ez = ex x ey
print("[기준] ex(%6.3f,%6.3f,%6.3f) ey(%6.3f,%6.3f,%6.3f) ez(%6.3f,%6.3f,%6.3f)"
      % (ex.x, ex.y, ex.z, ey.x, ey.y, ey.z, ez.x, ez.y, ez.z))

# 손아귀는 손목 뼈보다 손끝 쪽으로 조금 나간다(주먹이 활대를 감싼다).
#   팔뚝->손 방향으로 4.5cm. 손 뼈가 손목이고 손바닥 중심이 그쯤이다.
if REF == "idle":
    palm = (Ih - If_).normalized()
    origin = Ih + palm * 0.045
else:
    palm = (Lh - Lf).normalized()
    origin = Lh + palm * 0.045
print("[손아귀] 손목(%.3f,%.3f,%.3f) -> 손아귀(%.3f,%.3f,%.3f)"
      % (Lh.x, Lh.y, Lh.z, origin.x, origin.y, origin.z))

# 캔트(활을 옆으로 눕히는 각). ey(화살 축) 둘레로 돌리므로 **화살과 시위의 관계는 안 깨진다**.
#   게임 카메라가 뒤 위에서 내려다보므로 0도면 활 평면이 정면으로 서서 얇게 읽힌다.
extra = Matrix.Rotation(ROLL, 4, "Y")

info = BM.build(arm, BONE, M_rest, M_pose, H, draw_len,
                basis=(ex, ey, ez), origin=origin, offset=(GX, GY, GZ),
                extra_rot=extra)
bow = info["obj"]
print("[활] 길이 %.3f  끝물러남 %.3f  오늬 %.3f  정점 %d 삼각 %d"
      % (info["BL"], info["TIPY"], info["NOCK"], info["verts"], info["tris"]))
bb = info["rest_bb"]
print("[활 REST 바운딩] x %.3f~%.3f  y %.3f~%.3f  z %.3f~%.3f"
      % bb)
print("[키 상자 영향] 몸통 z %.3f~%.3f / 활 z %.3f~%.3f -> %s"
      % (BODY_Z[0], BODY_Z[1], bb[4], bb[5],
         "안전(몸통 안)" if (bb[4] >= BODY_Z[0] - 1e-4 and bb[5] <= BODY_Z[1] + 1e-4)
         else "★삐져나감 - main.js 키 계산에서 BW_ 를 빼야 한다"))

# ---------------------------------------------------------------- 클립별 활 위치
mwb = bow.matrix_world


def bow_bb(actname, frames=None):
    a = bpy.data.actions.get(actname)
    if not a:
        return None
    use(a)
    f0 = int(round(a.frame_range[0]))
    f1 = int(round(a.frame_range[1]))
    lo = [9e9] * 3
    hi = [-9e9] * 3
    for f in (frames or range(f0, f1 + 1)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = bow.evaluated_get(dg)
        m = ev.to_mesh()
        for v in m.vertices:
            p = mwb @ v.co
            for k in range(3):
                lo[k] = min(lo[k], p[k])
                hi[k] = max(hi[k], p[k])
        ev.to_mesh_clear()
    return lo, hi


print("\n[클립별 활 바운딩]  (z<0 이면 땅을 뚫는다)")
for nm in ("Idle", "Walk", "Run", "Jump", "Attack"):
    r = bow_bb(nm)
    if not r:
        continue
    lo, hi = r
    print("  %-7s x %6.3f~%6.3f  y %6.3f~%6.3f  z %6.3f~%6.3f  %s"
          % (nm, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
             "★땅 뚫음" if lo[2] < -0.005 else ""))

# ---------------------------------------------------------------- 렌더
# ★게임 카메라 각도(고도 49.3도)로만 본다. 정면 렌더로 판정하면 기각당한다.
PITCH = 49.3
DIST = 3.4


def cam_at(az_deg, target=Vector((0, 0, 0.95))):
    ph = math.radians(PITCH)
    th = math.radians(az_deg)
    eye = target + Vector((math.sin(th) * math.cos(ph),
                           math.cos(th) * math.cos(ph),
                           math.sin(ph))) * DIST
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    cd.type = "PERSP"
    cd.lens = 50
    cam.location = eye
    d = (target - eye).normalized()
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    return cam


sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.display.shading.show_shadows = False
sc.render.resolution_x = 640
sc.render.resolution_y = 640
sc.world = bpy.data.worlds.new("W")
sc.world.color = (0.13, 0.15, 0.13)

# 게임에서 캐릭터는 카메라 기준으로 어느 방향이든 될 수 있다. 네 방위를 본다.
#   az 0   = 등을 보이고 정면(-Y)을 향해 쏘는 그림(카메라가 뒤에)
#   az 90  = 옆으로 쏘는 그림
SHOTS = [("Attack", DRAW_F, 0), ("Attack", DRAW_F, 45), ("Attack", DRAW_F, 90),
         ("Attack", DRAW_F, 135),
         ("Idle", 17, 30), ("Walk", 8, 30), ("Run", 6, 30), ("Jump", 22, 30)]
for (nm, f, az) in SHOTS:
    a = bpy.data.actions.get(nm)
    if not a:
        continue
    use(a)
    sc.frame_set(f)
    bpy.context.view_layer.update()
    cam_at(az)
    sc.render.filepath = os.path.join(OUT, "%s_f%02d_az%03d.png" % (nm, f, az))
    bpy.ops.render.render(write_still=True)
print("완료:", OUT)

# ---- 진단: 활 로컬축이 REST 에서 어디를 향하나 ----
# ★키 상자 문제를 풀려면 이게 필요하다. 활채의 어느 팔이 REST 에서 위로 가는지에 따라
#   "위 팔을 줄일지 아래 팔을 줄일지"(비대칭 활, 화궁 모양)가 갈린다.
FIN = info["FINAL"]
o0 = FIN @ Vector((0, 0, 0))
oz = FIN @ Vector((0, 0, 1)) - o0
oy = FIN @ Vector((0, 1, 0)) - o0
print("[REST 축] 손아귀(%.3f,%.3f,%.3f)  로컬+Z -> (%.3f,%.3f,%.3f)  로컬+Y -> (%.3f,%.3f,%.3f)"
      % (o0.x, o0.y, o0.z, oz.x, oz.y, oz.z, oy.x, oy.y, oy.z))
