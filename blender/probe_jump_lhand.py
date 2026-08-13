# -*- coding: utf-8 -*-
"""점프 체공 중 **왼손(빈손) 주먹이 어디를 향하는가** 실측 (17-점프왼손).

    GLB=web/basic2.glb JSON=/tmp/before.json blender -b -P blender/probe_jump_lhand.py

오너 지시: **"점프했을때 검안쥔손 주먹이 왜 하늘을향하고있냐"**
그 "주먹이 향하는 방향"을 좌표로 못 박으려고 만들었다.

★무엇이 '주먹이 향하는 쪽'인가
  주먹 메시에는 손가락·엄지·너클이 없다(13-손목에서 확인). 방향 단서는 셋뿐이다.
      팔축   손목원점 -> 주먹중심.  **주먹의 앞면(손가락 마디가 보이는 쪽)** 이 이쪽이다
             (13-손목이 접사 t_armP.png 로 확인. 골 네 개가 이 축을 보고 찍힌다)
      구멍축 손가락 마디가 늘어선 방향(엄지 -> 새끼). 막대를 쥐면 이 축으로 지난다
      손등축 나머지. **월드에서** 팔축 x 구멍축(오른손) / 그 반대(왼손)
  그래서 "주먹이 하늘을 향한다" = **팔축의 월드 고도가 크게 양수**다.

★손목 기하각과 같이 봐야 뜻이 산다
  기하각 = (팔꿈치->손목) 과 (손목->주먹중심) 사이각. 레스트 중립이 16.8도다.
  이 각이 120도를 넘으면 손이 팔뚝 위로 접혀 있다는 뜻이고, 그 상태에서 팔이
  아래를 향하면 주먹은 자동으로 위(하늘)를 본다.

손잡이(환경변수)
  GLB     볼 파일      기본 web/basic2.glb
  CLIPS   클립 목록    기본 Jump
  JSON    결과 json    (선택. before/after 대조용)
  TAG     표 제목
"""
import bpy
import os
import math
import json
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.environ.get("GLB") or os.path.join(ROOT, "web", "basic2.glb")
if not os.path.isabs(GLB):
    GLB = os.path.join(ROOT, GLB)
CLIPS = [c.strip() for c in os.environ.get("CLIPS", "Jump").split(",") if c.strip()]
JSON_OUT = os.environ.get("JSON", "")
TAG = os.environ.get("TAG", os.path.basename(GLB))

HAND_R, HAND_L = "Bip001 R Hand", "Bip001 L Hand"
FORE_R, FORE_L = "Bip001 R Forearm", "Bip001 L Forearm"
UP_L = "Bip001 L UpperArm"
TORSO, NECK = "Bip001 Spine", "Bip001 Neck"
CLAV_L, CLAV_R = "Bip001 L Clavicle", "Bip001 R Clavicle"
GAME_H = 1.75
# 엄지 쪽 구멍축의 레스트 월드 방향(부호 고정용). s24_moveset.py / probe_wrist.py 와 같은 값.
THUMB_REF_W = {HAND_R: Vector((0.285, -0.953, -0.100)),
               HAND_L: Vector((-0.285, -0.953, -0.100))}

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath=GLB)
if sc.render.fps != 30:
    sc.render.fps = 30
arm = next(o for o in sc.objects if o.type == "ARMATURE")
for o in list(sc.objects):                          # ★뼈 표시용 Icosphere
    if o.type == "MESH" and any(c.name == "glTF_not_exported"
                                for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)
MESH = [o for o in sc.objects if o.type == "MESH"]
BODY = [o for o in MESH if not o.name.startswith(("SW_", "SH_"))]
A2W = arm.matrix_world

for b in arm.pose.bones:
    b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
zs = []
for o in BODY:
    zs += [(o.matrix_world @ v.co).z for v in o.data.vertices]
H = max(zs) - min(zs)
K = GAME_H / H                                      # 블렌더 단위 -> 게임 m


def pose_world(bn):
    m = (A2W @ arm.pose.bones[bn].matrix).copy()
    r = m.to_3x3()
    r.normalize()
    return m.translation.copy(), r


def fist_frame(bone):
    """손 본이 지배하는 몸 정점으로 주먹 좌표계를 만든다(손 본 로컬. 레스트에서)."""
    import numpy as np
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    _, R3 = pose_world(bone)
    HM = A2W @ arm.pose.bones[bone].matrix
    HMi = HM.inverted()
    pts = []
    for o in BODY:
        g = o.vertex_groups.get(bone)
        if g is None:
            continue
        for v in o.data.vertices:
            w = next((x.weight for x in v.groups if x.group == g.index), 0.0)
            if w > 0.5:
                pts.append(HMi @ (o.matrix_world @ v.co))
    arm.data.pose_position = "POSE"
    if len(pts) < 12:
        return None
    M = np.array([[p.x, p.y, p.z] for p in pts], dtype=float)
    C = Vector(M.mean(axis=0))
    a_arm = C.normalized()                          # ★팔축은 기하로 확정한다
    P = [Vector(p) - C for p in M]
    P = [q - a_arm * q.dot(a_arm) for q in P]       # 그 수직 평면에서만 2차원 주성분
    e1 = Vector((1, 0, 0)) if abs(a_arm.x) < 0.9 else Vector((0, 1, 0))
    e1 = (e1 - a_arm * e1.dot(a_arm)).normalized()
    e2 = a_arm.cross(e1)
    Q = np.array([[q.dot(e1), q.dot(e2)] for q in P], dtype=float)
    _, V2 = np.linalg.eigh(Q.T @ Q)
    a_tun = (e1 * V2[0, 1] + e2 * V2[1, 1]).normalized()
    if (R3 @ a_tun).dot(THUMB_REF_W[bone]) < 0:     # 엄지 쪽으로 부호 고정
        a_tun = -a_tun
    # ★손등은 **월드에서** 팔축 x 구멍축(오른손). 왼손은 부호가 반대다.
    #   로컬 외적을 쓰면 안 된다 — 이 리그의 손 행렬은 행렬식이 음수라 부호가 뒤집힌다.
    aw = (R3 @ a_arm).normalized()
    tw = (R3 @ a_tun).normalized()
    bw = aw.cross(tw) * (1.0 if bone == HAND_R else -1.0)
    a_bak = (R3.inverted() @ bw).normalized()
    return dict(c=C, arm=a_arm, tun=a_tun, bak=a_bak, n=len(pts),
                s=HM.to_3x3().to_scale()[0], det=R3.determinant())


FL = fist_frame(HAND_L)
FR = fist_frame(HAND_R)
print("\n[왼 주먹 좌표계] 손 본 로컬 (레스트에서 잰 값. 자세와 무관한 상수)")
print("   정점 %d / 중심 손목에서 %.1fcm / 손행렬 det %+.3f"
      % (FL["n"], FL["c"].length * FL["s"] * K * 100, FL["det"]))
for k in ("arm", "tun", "bak"):
    print("   %-4s 손로컬 (%+.3f,%+.3f,%+.3f)" % (k, FL[k].x, FL[k].y, FL[k].z))


# ---------------------------------------------------------------- 몸 관통
# ★손뼈만 돌려도 주먹은 손목 둘레로 20cm 를 움직인다(주먹 중심이 손목에서 11.4cm).
#   그러니 "몸을 안 뚫는가"는 매번 다시 재야 한다. 정확한 자기교차 판정 대신
#   **왼 주먹 정점 <-> 몸통·다리 정점**의 최소 거리를 잰다(양수면 안 닿은 것이고,
#   before/after 를 같은 잣대로 비교할 수 있다).
PEN = os.environ.get("PEN", "1") == "1"
TRUNK = ("Bip001 Spine", "Bip001 Spine1", "Bip001 Pelvis", "Bip001 Head",
         "Bip001 L Thigh", "Bip001 R Thigh", "Bip001 L Calf", "Bip001 R Calf",
         "Bip001 Neck", "Bip001 L Clavicle", "Bip001 R Clavicle")


def _verts_of(bones, thr=0.5):
    """해당 뼈들이 지배하는 정점의 (오브젝트, 인덱스) 목록."""
    out = []
    for o in BODY:
        gi = [o.vertex_groups[b].index for b in bones if b in o.vertex_groups]
        if not gi:
            continue
        for v in o.data.vertices:
            if sum(x.weight for x in v.groups if x.group in gi) > thr:
                out.append((o, v.index))
    return out


FIST_V = _verts_of([HAND_L]) if PEN else []
TRUNK_V = _verts_of(TRUNK) if PEN else []


def fist_trunk_gap():
    """이 프레임의 왼 주먹-몸통 최소 거리(게임 m). 크면 안 닿았다는 뜻."""
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    A_, B_ = [], []
    for tgt, src in ((A_, FIST_V), (B_, TRUNK_V)):
        cache = {}
        for o, i in src:
            me = cache.get(o.name)
            if me is None:
                me = cache[o.name] = o.evaluated_get(dg).to_mesh()
            p = o.matrix_world @ me.vertices[i].co
            tgt.append([p.x, p.y, p.z])
        for o in {o for o, _ in src}:
            o.evaluated_get(dg).to_mesh_clear()
    a = np.array(A_)
    b = np.array(B_)
    d = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    return d.min() * K


def torso_frame():
    up = (pose_world(NECK)[0] - pose_world(TORSO)[0]).normalized()
    lat = pose_world(CLAV_L)[0] - pose_world(CLAV_R)[0]
    lat = (lat - up * lat.dot(up)).normalized()
    return Matrix((lat, up, lat.cross(up))).transposed()


def use(act):
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def elev(v):
    return math.degrees(math.asin(max(-1.0, min(1.0, v.z))))


arm.data.pose_position = "REST"
bpy.context.view_layer.update()
_Wp, _Wr = pose_world(HAND_L)
_Ep, _ = pose_world(FORE_L)
GEO0 = math.degrees((_Wp - _Ep).normalized().angle((_Wr @ FL["c"]).normalized()))
arm.data.pose_position = "POSE"
print("   레스트 왼손목 기하각(중립) %.1f도" % GEO0)

OUT = {}
for nm in CLIPS:
    act = bpy.data.actions.get(nm)
    if not act:
        print("   %s 액션이 없다" % nm)
        continue
    use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    print("\n[%s] f%d~%d  ★'주먹면 고도'가 이번 지시의 과녁이다"
          " (+90=주먹이 똑바로 하늘 / -90=똑바로 땅)" % (nm, f0, f1))
    print("  %3s %5s | %-26s | %-26s | %-20s | %6s"
          % ("f", "위상", "주먹면(팔축) 고도/밖/위/앞", "손등 고도/밖/위/앞",
             "구멍축 고도/밖/앞", "손목각"))
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        Wp, Wr = pose_world(HAND_L)
        Ep, _ = pose_world(FORE_L)
        Sp, _ = pose_world(UP_L)
        aw = (Wr @ FL["arm"]).normalized()
        tw = (Wr @ FL["tun"]).normalized()
        bw = (Wr @ FL["bak"]).normalized()
        fdir = (Wp - Ep).normalized()
        Ci = torso_frame().transposed()             # 월드 -> 가슴(X=왼쪽=왼손의 바깥)
        at, bt, tt = Ci @ aw, Ci @ bw, Ci @ tw
        geo = math.degrees(fdir.angle(aw))
        ph = (f - f0) / max(1, f1 - f0)
        r = dict(f=f, t=round(ph, 3),
                 arm_elev=elev(aw), arm_out=at.x, arm_up=at.y, arm_fwd=at.z,
                 bak_elev=elev(bw), bak_out=bt.x, bak_up=bt.y, bak_fwd=bt.z,
                 tun_elev=elev(tw), tun_out=tt.x, tun_fwd=tt.z,
                 geo=geo, fore_elev=elev(fdir),
                 # 팔뚝 기준 손 방향(자세에 안 흔들리는 값)
                 hand_out=(Ci @ (Wp - Sp).normalized()).x,
                 gap=(fist_trunk_gap() if PEN else -1.0))
        rows.append(r)
        print("  %3d %5.2f | %+6.1f도 %+5.2f %+5.2f %+5.2f | %+6.1f도 %+5.2f %+5.2f %+5.2f"
              " | %+6.1f도 %+5.2f %+5.2f | %5.1f도"
              % (f, ph, r["arm_elev"], r["arm_out"], r["arm_up"], r["arm_fwd"],
                 r["bak_elev"], r["bak_out"], r["bak_up"], r["bak_fwd"],
                 r["tun_elev"], r["tun_out"], r["tun_fwd"], geo))
    OUT[nm] = rows
    if PEN:
        g = sorted(r["gap"] for r in rows)
        print("   왼 주먹 - 몸통·다리 최소 거리(게임 m): %.4f ~ %.4f  (f%d 가 최소)"
              % (g[0], g[-1], min(rows, key=lambda r: r["gap"])["f"]))
    hold = [r for r in rows if abs(r["t"] - 0.27) < 0.03 or abs(r["t"] - 0.55) < 0.03]
    if hold:
        print("   ★게임이 멈춰 세우는 두 장(t 0.27 상승 / 0.55 하강):")
        for r in hold:
            print("      f%-2d 주먹면 고도 %+.1f도 · 손등 고도 %+.1f도 · 손목각 %.1f도"
                  % (r["f"], r["arm_elev"], r["bak_elev"], r["geo"]))

if JSON_OUT:
    with open(JSON_OUT, "w") as fp:
        json.dump(dict(tag=TAG, glb=GLB, geo0=GEO0, clips=OUT), fp, indent=1)
    print("\n[json] %s" % JSON_OUT)
