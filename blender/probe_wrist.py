# -*- coding: utf-8 -*-
"""파지 손 방향·손목 꺾임 실측 (13-손목).

    GLB=web/basic2.glb OUTDIR=renders/history/v99_wave13/wrist/probe \
      blender -b -P blender/probe_wrist.py

오너 지적 세 가지를 **좌표로** 확인하려고 만들었다.
    1) "손등이 왜 하늘을 향하고 있냐"            -> 오른 주먹 손등 노멀의 월드 방향
    2) "손잡이를 쥐고 있어야 하는데"              -> 주먹 구멍축과 칼축의 각도차
    3) "왼쪽(손)은 엄청 꺾여 있음 / X 쓸 때도"    -> 왼손목 굽힘각(클립x프레임)

★주먹 좌표계는 뼈 로컬축을 안 믿는다(Meshy 리그는 축이 제멋대로다).
  손 본에 웨이트 0.5 초과인 **몸 정점**의 주성분으로 직접 만든다.
      길이축 세 개 중 손목->주먹중심 방향과 가장 나란한 것 = 팔축
      남은 둘 중 폭이 좁은 쪽 = 손등 노멀(두께 방향) · 넓은 쪽 = 구멍축(손가락 마디 방향)
  부호(손등이냐 손바닥이냐)는 기하로 못 가른다. RENDER=1 이면 여섯 방향 접사를
  찍어 두므로 눈으로 한 번 정하고 BACK_SIGN 으로 굳힌다.

★손목 꺾임은 두 가지로 잰다. 둘 다 필요하다.
  기하각  = (팔꿈치->손목) 과 (손목->주먹중심) 사이각. 눈에 "꺾였다"고 보이는 그 각이다.
  스윙각  = 레스트 대비 손목 상대회전을 팔뚝축 둘레 비틀림(twist)과 나머지(swing)로
            가른 뒤의 swing 크기. 해부학적으로 손목이 실제로 굽는 양이다.
            (팔뚝 비틀림 pronation 은 손목이 아니라 아래팔이 하는 일이라 빼야 한다)
  사람 손목 굽힘 한계는 굴곡 60~70도 · 신전 60~70도 · 좌우편위 20~30도다.

손잡이(환경변수)
  GLB       볼 파일       기본 web/basic2.glb
  CLIPS     클립 목록     기본 Idle,Walk,Run,Attack,Heavy,Wide,Jump
  RENDER    1 이면 주먹 접사 여섯 방향(부호 판정용) 기본 0
  OUTDIR    렌더 폴더
  JSON      결과를 적을 json 경로(선택. before/after 대조용)
"""
import bpy
import os
import math
import json
from mathutils import Vector, Matrix, Quaternion

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.environ.get("GLB") or os.path.join(ROOT, "web", "basic2.glb")
if not os.path.isabs(GLB):
    GLB = os.path.join(ROOT, GLB)
CLIPS = [c.strip() for c in os.environ.get(
    "CLIPS", "Idle,Walk,Run,Attack,Heavy,Wide,Jump").split(",") if c.strip()]
RENDER = os.environ.get("RENDER", "0") == "1"
OUTDIR = os.environ.get("OUTDIR") or os.path.join(
    ROOT, "renders", "history", "v99_wave13", "wrist", "probe")
JSON_OUT = os.environ.get("JSON", "")
TAG = os.environ.get("TAG", "")

HAND_R, HAND_L = "Bip001 R Hand", "Bip001 L Hand"
FORE_R, FORE_L = "Bip001 R Forearm", "Bip001 L Forearm"
UP_R, UP_L = "Bip001 R UpperArm", "Bip001 L UpperArm"
TORSO, NECK = "Bip001 Spine", "Bip001 Neck"
CLAV_L, CLAV_R = "Bip001 L Clavicle", "Bip001 R Clavicle"
GAME_H = 1.75                                     # 게임이 캐릭터를 이 키로 정규화한다
# 엄지 쪽 구멍축의 레스트 월드 방향(부호 고정용). 13-손목 전 판 기준이고, 주먹을
# 돌린 뒤에는 엄지축이 칼끝 쪽으로 94도 돌아가 있으므로 아래에서 칼축으로 한 번 더
# 바로잡는다(두 판의 표를 같은 부호로 읽으려고 둔 장치다).
THUMB_REF_W = {"Bip001 R Hand": Vector((0.285, -0.953, -0.100)),
               "Bip001 L Hand": Vector((-0.285, -0.953, -0.100))}

# ---------------------------------------------------------------- 씬
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath=GLB)
if sc.render.fps != 30:
    sc.render.fps = 30
arm = next(o for o in sc.objects if o.type == "ARMATURE")
for o in list(sc.objects):                        # ★함정: 뼈 표시용 Icosphere
    if o.type == "MESH" and any(c.name == "glTF_not_exported"
                                for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)
MESH = [o for o in sc.objects if o.type == "MESH"]
BODY = [o for o in MESH if not o.name.startswith(("SW_", "SH_"))]
SWORDS = [o for o in MESH if o.name.startswith("SW_")]
A2W = arm.matrix_world

for b in arm.pose.bones:
    b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
zs = []
for o in BODY:
    zs += [(o.matrix_world @ v.co).z for v in o.data.vertices]
H = max(zs) - min(zs)
FLOOR = min(zs)
K = GAME_H / H                                    # 블렌더 단위 -> 게임 m

print("=" * 78)
print("[파일] %s%s" % (os.path.basename(GLB), ("  (%s)" % TAG if TAG else "")))
print("       키 %.4f (게임 %.2fm 환산계수 %.4f) / 액션 %s"
      % (H, GAME_H, K, sorted(a.name for a in bpy.data.actions)))
print("       메시 %s" % [o.name for o in MESH])


def rest_world(bn):
    """레스트 월드 행렬(회전 정규화)."""
    m = (A2W @ arm.pose.bones[bn].matrix).copy()
    r = m.to_3x3()
    r.normalize()
    return m.translation.copy(), r


# ---------------------------------------------------------------- 주먹 좌표계
def fist_frame(bone):
    """손 본이 지배하는 몸 정점의 주성분으로 손 로컬 좌표계를 만든다.

    반환 dict: c(중심, 손로컬) / tun,arm_,bak(축, 손로컬 단위벡터) / 폭 3개 / 정점수
    """
    import numpy as np
    _, R = rest_world(bone)
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
    if len(pts) < 12:
        return None
    # ★3차원 주성분을 그냥 쓰면 안 된다. 손은 팔축으로 길쭉해서(손목->손끝 20cm)
    #   축 셋이 대각으로 섞이고 구멍축이 팔축과 같은 20cm 로 나온다(첫 판에서 겪었다).
    #   팔축은 기하로 확정(손목원점 -> 중심)하고, 그 **수직 평면에서만** 2차원
    #   주성분을 뽑는다. 그래야 손등 폭(넓은 쪽)과 두께(좁은 쪽)가 갈린다.
    M = np.array([[p.x, p.y, p.z] for p in pts], dtype=float)
    C = Vector(M.mean(axis=0))
    a_arm = C.normalized()                         # 손목 원점 -> 주먹 중심
    P = [Vector(p) - C for p in M]
    P = [q - a_arm * q.dot(a_arm) for q in P]      # 팔축 성분 제거
    e1 = Vector((1, 0, 0)) if abs(a_arm.x) < 0.9 else Vector((0, 1, 0))
    e1 = (e1 - a_arm * e1.dot(a_arm)).normalized()
    e2 = a_arm.cross(e1)
    Q = np.array([[q.dot(e1), q.dot(e2)] for q in P], dtype=float)
    w2, V2 = np.linalg.eigh(Q.T @ Q)
    wide = e1 * V2[0, 1] + e2 * V2[1, 1]           # 큰 고유값 = 넓은 쪽
    a_tun = wide.normalized()                      # 손가락 마디가 늘어선 방향 = 구멍축
    # ★부호를 안 박으면 before/after 표의 손등 방향이 뒤집혀 비교가 안 된다(실제로 겪었다).
    #   구멍축의 **엄지 쪽**을 레스트 월드 기준벡터로 고정한다. 기준벡터는 2026-08-12
    #   에 주먹 접사(renders/history/v99_wave13/wrist/fisttex/)를 눈으로 보고 정했다.
    #   주먹을 돌린 판(13-손목 이후)에서는 엄지축이 칼끝 쪽이므로 그쪽을 먼저 본다.
    R3 = R.copy()
    ref = THUMB_REF_W.get(bone)
    if ref is not None and (R3 @ a_tun).dot(ref) < 0:
        a_tun = -a_tun
    # 손등 노멀은 **월드에서** 팔축 x 엄지축이다(오른손 해부학. 왼손은 부호가 반대).
    aw = (R3 @ a_arm).normalized()
    tw = (R3 @ a_tun).normalized()
    bw = aw.cross(tw) * (1.0 if bone == HAND_R else -1.0)
    a_bak = (R3.inverted() @ bw).normalized()
    ext = []
    for a in (a_arm, a_tun, a_bak):
        pr = [(Vector(p) - C).dot(a) for p in M]
        ext.append(max(pr) - min(pr))
    ext[0] = max(Vector(p).dot(a_arm) for p in M)  # 팔축은 손목에서 손끝까지
    return dict(c=C, arm=a_arm, tun=a_tun, bak=a_bak, n=len(pts),
                ext=ext, HM=HM.copy(), R=R.copy(),
                s=HM.to_3x3().to_scale()[0])


FR = fist_frame(HAND_R)
FL = fist_frame(HAND_L)
print("\n[주먹 좌표계] 손 본 로컬. 폭은 게임 cm 환산")
for nm, F in (("오른", FR), ("왼", FL)):
    if not F:
        print("   %s 손: 정점을 못 찾았다" % nm)
        continue
    # ★손 로컬 길이는 아마추어 스케일(0.01)이 붙어 있다. 월드로 바꿀 때 곱해야 한다
    print("   %s 손 정점 %4d / 중심 (%.4f,%.4f,%.4f) 손목에서 %.1fcm"
          % (nm, F["n"], F["c"].x, F["c"].y, F["c"].z,
             F["c"].length * F["s"] * K * 100))
    print("        폭  팔축 %.1fcm · 구멍축 %.1fcm · 두께(손등노멀) %.1fcm"
          % tuple(e * F["s"] * K * 100 for e in F["ext"]))
    for k in ("arm", "tun", "bak"):
        wv = (F["R"] @ F[k]).normalized()
        print("        %-4s 손로컬 (%+.3f,%+.3f,%+.3f)  레스트월드 (%+.3f,%+.3f,%+.3f)"
              % (k, F[k].x, F[k].y, F[k].z, wv.x, wv.y, wv.z))

# ---------------------------------------------------------------- 칼
def tip_dir(ob, bone=HAND_R):
    HMi = (A2W @ arm.pose.bones[bone].matrix).inverted()
    loc = [HMi @ (ob.matrix_world @ v.co) for v in ob.data.vertices]
    far = max(loc, key=lambda p: p.length)
    return far.normalized(), far.length, loc


print("\n[칼] 손 본 로컬 '손목원점->칼끝' (measureBlade 와 같은 기준)")
SW = {}
for o in sorted(SWORDS, key=lambda x: x.name):
    d, L, loc = tip_dir(o)
    SW[o.name] = (d, L)
    ex = ""
    if FR:
        ex = "   구멍축과 %.1f도" % math.degrees(d.angle(FR["tun"]))
    print("   %-16s dir (%+.6f,%+.6f,%+.6f) pmax %.5f%s" % (o.name, d.x, d.y, d.z, L, ex))
SW_MAIN = next((n for n in SW if n.startswith("SW_nokseun")), None)
UD = SW[SW_MAIN][0] if SW_MAIN else None

if FR and UD:
    # ★주먹을 돌린 판(13-손목 이후)에서는 엄지축이 기준벡터와 거의 수직이라 부호가
    #   흔들린다. 그 판은 엄지축이 곧 칼끝 쪽이므로 칼축으로 다시 잡는다.
    if abs((FR["R"] @ FR["tun"]).dot(THUMB_REF_W[HAND_R])) < 0.5 \
            and FR["tun"].dot(UD) < 0:
        FR["tun"] = -FR["tun"]
        FR["bak"] = -FR["bak"]                     # 팔축 x 엄지축 이라 같이 뒤집힌다
        print("   (엄지축 부호를 칼끝 쪽으로 다시 잡았다 = 주먹을 돌린 판이다)")
    print("\n[진단1] 주먹 구멍축 vs 칼축 (파지가 자연스러우려면 0 도에 가까워야 한다)")
    print("   구멍축-칼축 각도  %.1f 도" % math.degrees(UD.angle(FR["tun"])))
    print("   손등노멀-칼축 각도 %.1f 도 (90 도면 칼이 손등 평면 안을 지난다 = 정상)"
          % math.degrees(UD.angle(FR["bak"])))
    print("   팔축-칼축 각도     %.1f 도" % math.degrees(UD.angle(FR["arm"])))
    # 칼축 둘레 롤: 손등 노멀을 칼축에 수직인 평면에 투영한 각(팔축 투영 기준 0도)
    b = (FR["bak"] - UD * FR["bak"].dot(UD)).normalized()
    a = (FR["arm"] - UD * FR["arm"].dot(UD)).normalized()
    print("   손등노멀의 칼축둘레 위상 %.1f 도 (팔축 투영을 0 으로)"
          % math.degrees(math.atan2(b.cross(a).dot(UD), b.dot(a))))

arm.data.pose_position = "POSE"


def use(act):
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def pose_world(bn):
    m = (A2W @ arm.pose.bones[bn].matrix).copy()
    r = m.to_3x3()
    r.normalize()
    return m.translation.copy(), r


def torso_frame():
    """가슴 좌표계 (열이 축) X=왼쪽 / Y=위(척추) / Z=앞."""
    up = (pose_world(NECK)[0] - pose_world(TORSO)[0]).normalized()
    lat = pose_world(CLAV_L)[0] - pose_world(CLAV_R)[0]
    lat = (lat - up * lat.dot(up)).normalized()
    return Matrix((lat, up, lat.cross(up))).transposed()


def swing_twist(q, axis):
    """q = swing * twist 로 가른다. 반환 (swing 각도, twist 각도) 도."""
    v = Vector((q.x, q.y, q.z))
    p = axis * v.dot(axis)
    tw = Quaternion((q.w, p.x, p.y, p.z))
    if tw.magnitude < 1e-9:
        tw = Quaternion()
    tw.normalize()
    sw = q @ tw.inverted()
    return math.degrees(sw.angle), math.degrees(tw.angle)


# 레스트 상대(손목 중립) 저장
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
REST = {}
for bn in (HAND_R, HAND_L, FORE_R, FORE_L, UP_R, UP_L):
    REST[bn] = pose_world(bn)
arm.data.pose_position = "POSE"


def wrist_bend(side):
    """손목 꺾임. 반환 (기하각, 스윙각, 비틀림각) 도."""
    hb, fb = (HAND_R, FORE_R) if side == "R" else (HAND_L, FORE_L)
    F = FR if side == "R" else FL
    Wp, Wr = pose_world(hb)
    Ep, _ = pose_world(fb)
    f = (Wp - Ep).normalized()
    h = (Wr @ F["c"]).normalized() if F else Vector((0, 0, 1))
    geo = math.degrees(f.angle(h))
    # 레스트 대비 손목 상대회전(손 레스트 로컬 표현)
    Hr0, Fr0 = REST[hb][1], REST[fb][1]
    _, Fr = pose_world(fb)
    J = Hr0.inverted() @ Fr0 @ Fr.inverted() @ Wr
    ax = (Hr0.inverted() @ (REST[hb][0] - REST[fb][0])).normalized()
    sw, tw = swing_twist(J.to_quaternion(), ax)
    return geo, sw, tw


# 레스트에서의 기하각(중립 기준선)
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
GEO0 = {s: wrist_bend(s)[0] for s in ("R", "L")}
arm.data.pose_position = "POSE"
print("   레스트 기하각(중립) 오른 %.1f도 / 왼 %.1f도" % (GEO0["R"], GEO0["L"]))

# ---------------------------------------------------------------- 클립별 실측
print("\n[진단2] 왼손목 꺾임 (기하각 = 팔꿈치->손목 vs 손목->주먹중심)")
print("  %-7s %5s | %-22s | %-22s | %s"
      % ("클립", "프레임", "왼 기하각 최소/중앙/최대", "왼 스윙각 최소/중앙/최대",
         "왼 최대 프레임"))
RES = {}
for nm in CLIPS:
    act = bpy.data.actions.get(nm)
    if not act:
        continue
    use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        gL, sL, tL = wrist_bend("L")
        gR, sR, tR = wrist_bend("R")
        C = torso_frame()
        _, Rr = pose_world(HAND_R)
        bak = (Rr @ FR["bak"]).normalized() if FR else Vector((0, 0, 1))
        tun = (Rr @ FR["tun"]).normalized() if FR else Vector((0, 0, 1))
        Ci = C.transposed()                       # 월드 -> 가슴
        bt = Ci @ bak
        tt = Ci @ tun
        # 왼손: 주먹 구멍축·팔뚝이 자루축과 이루는 각(파지가 되려면 구멍축 0도)
        lt = lf = lmin = -1.0
        if FL and UD:
            uw = (Rr @ UD).normalized()             # 월드 자루축(오른손이 물고 있다)
            _, Lr = pose_world(HAND_L)
            ltun = (Lr @ FL["tun"]).normalized()
            lt = math.degrees(min(ltun.angle(uw), math.pi - ltun.angle(uw)))
            fdir = (pose_world(HAND_L)[0] - pose_world(FORE_L)[0]).normalized()
            fa = math.degrees(fdir.angle(uw))
            lf = min(fa, 180 - fa)
            lmin = abs(90 - fa)                     # 구멍축을 자루에 맞췄을 때 남는 굽힘
        rows.append(dict(f=f, gL=gL, sL=sL, tL=tL, gR=gR, sR=sR, tR=tR,
                         bak_elev=math.degrees(math.asin(max(-1, min(1, bak.z)))),
                         bak_out=-bt.x, bak_up=bt.y, bak_fwd=bt.z,
                         tun_out=-tt.x, tun_up=tt.y, tun_fwd=tt.z,
                         tun_elev=math.degrees(math.asin(max(-1, min(1, tun.z)))),
                         lt=lt, lf=lf, lmin=lmin))
    RES[nm] = rows
    gs = sorted(r["gL"] for r in rows)
    ss = sorted(r["sL"] for r in rows)
    mx = max(rows, key=lambda r: r["gL"])
    print("  %-7s %5d | %6.1f %6.1f %6.1f      | %6.1f %6.1f %6.1f      | f%02d"
          % (nm, len(rows), gs[0], gs[len(gs) // 2], gs[-1],
             ss[0], ss[len(ss) // 2], ss[-1], mx["f"]))

print("\n[진단3] 오른 주먹 손등 노멀 방향 (가슴 좌표계 성분. 월드 고도는 +90=하늘)")
print("  %-7s %5s | %7s %7s | %7s %7s %7s | %s"
      % ("클립", "프레임", "고도중앙", "고도최대", "바깥", "위", "앞", "오른손목 기하각"))
for nm in CLIPS:
    rows = RES.get(nm)
    if not rows:
        continue
    es = sorted(r["bak_elev"] for r in rows)
    md = rows[len(rows) // 2]
    gr = sorted(r["gR"] for r in rows)
    print("  %-7s %5d | %7.1f %7.1f | %+7.2f %+7.2f %+7.2f | %.1f/%.1f/%.1f"
          % (nm, len(rows), es[len(es) // 2], es[-1],
             md["bak_out"], md["bak_up"], md["bak_fwd"], gr[0], gr[len(gr) // 2], gr[-1]))

# 대표 프레임 상세(게임이 오래 보여 주는 자세 + X)
print("\n[진단4] 대표 프레임 상세")
SPOT = {"Idle": [1], "Run": [1, 5, 9], "Attack": None, "Heavy": None,
        "Wide": None, "Jump": [7, 13], "Walk": [1, 5]}
for nm in CLIPS:
    rows = RES.get(nm)
    if not rows:
        continue
    want = SPOT.get(nm)
    if want is None:                              # 공격류는 5등분
        f0, f1 = rows[0]["f"], rows[-1]["f"]
        want = [f0 + int(round(t * (f1 - f0))) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    for r in rows:
        if r["f"] not in want:
            continue
        print("   %-7s f%02d  손등 고도 %+6.1f (바깥%+.2f 위%+.2f 앞%+.2f)"
              "   왼손목 기하 %5.1f 스윙 %5.1f 비틀림 %5.1f   오른손목 기하 %5.1f"
              % (nm, r["f"], r["bak_elev"], r["bak_out"], r["bak_up"], r["bak_fwd"],
                 r["gL"], r["sL"], r["tL"], r["gR"]))

print("\n[진단5] 왼손 파지 가능성 (구멍축이 자루축과 0도여야 쥔 것이다)")
print("  %-7s | %-20s | %-20s | %s"
      % ("클립", "왼구멍축-자루 최소/중앙/최대", "왼팔뚝-자루 최소/중앙/최대",
         "구멍축을 맞췄을 때 남는 손목굽힘 중앙/최대"))
for nm in CLIPS:
    rows = [r for r in RES.get(nm, []) if r["lt"] >= 0]
    if not rows:
        continue
    a1 = sorted(r["lt"] for r in rows)
    a2 = sorted(r["lf"] for r in rows)
    a3 = sorted(r["lmin"] for r in rows)
    print("  %-7s | %5.1f %5.1f %5.1f    | %5.1f %5.1f %5.1f    | %5.1f %5.1f"
          % (nm, a1[0], a1[len(a1) // 2], a1[-1], a2[0], a2[len(a2) // 2], a2[-1],
             a3[len(a3) // 2], a3[-1]))

print("\n[진단6] 오른 주먹을 팔축 둘레로 돌리면 손등이 어디를 보나(=현재 구멍축 방향)")
print("  %-7s | %7s %7s %7s %7s" % ("클립", "고도중앙", "바깥", "위", "앞"))
for nm in CLIPS:
    rows = RES.get(nm)
    if not rows:
        continue
    es = sorted(r["tun_elev"] for r in rows)
    md = rows[len(rows) // 2]
    print("  %-7s | %7.1f %+7.2f %+7.2f %+7.2f"
          % (nm, es[len(es) // 2], md["tun_out"], md["tun_up"], md["tun_fwd"]))

if JSON_OUT:
    p = JSON_OUT if os.path.isabs(JSON_OUT) else os.path.join(ROOT, JSON_OUT)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fp:
        json.dump(dict(glb=GLB, tag=TAG, H=H, K=K, clips=RES,
                       fist=dict(
                           R=dict(c=list(FR["c"]), arm=list(FR["arm"]),
                                  tun=list(FR["tun"]), bak=list(FR["bak"]),
                                  ext=FR["ext"]) if FR else None),
                       sword={k: (list(v[0]), v[1]) for k, v in SW.items()}), fp)
    print("\n[JSON] %s" % p)

# ---------------------------------------------------------------- 접사 렌더
if RENDER and FR:
    os.makedirs(OUTDIR, exist_ok=True)
    ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids \
        else "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = 700
    for e, rot in ((5.0, (math.radians(58), 0, math.radians(-30))),
                   (2.5, (math.radians(-40), 0, math.radians(150)))):
        li = bpy.data.lights.new("S", "SUN")
        li.energy = e
        so = bpy.data.objects.new("S", li)
        so.rotation_euler = rot
        sc.collection.objects.link(so)
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = 50
    act = bpy.data.actions.get(CLIPS[0])
    if act:
        use(act)
        sc.frame_set(int(act.frame_range[0]))
    bpy.context.view_layer.update()
    Wp, Wr = pose_world(HAND_R)
    ctr = Wp + Wr @ (FR["c"] * FR["s"])           # ★스케일을 빼먹으면 카메라가 10배 밖에 선다
    D = H * 0.45          # 손+팔뚝+자루가 한 화면에 들어오는 거리
    for nm, v in (("bak+", FR["bak"]), ("bak-", -FR["bak"]),
                  ("tun+", FR["tun"]), ("tun-", -FR["tun"]),
                  ("arm+", FR["arm"]), ("arm-", -FR["arm"])):
        d = (Wr @ v).normalized()
        cam.location = ctr + d * D
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUTDIR, "fist_%s.png" % nm)
        bpy.ops.render.render(write_still=True)
        print("   rendered fist_%s.png" % nm)

print("\nPROBE_DONE")
