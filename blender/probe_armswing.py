# -*- coding: utf-8 -*-
"""걷기·달리기 **팔 스윙 앞/뒤 최대각** 실측 (13-걷기팔).

    GLB=web/basic2.glb CLIPS=Walk,Run TAG=after JSON=... \
      blender -b -P blender/probe_armswing.py

오너 지적 "걸을 때 팔을 너무 뒤로 뺀다" 를 좌표로 확인하려고 만들었다.
네이티브 원본 glb(Meshy 뼈 이름)도 그대로 읽는다 - 이름을 s27 과 같은 표로 바꾼다.

★각도 정의 (가슴 좌표계. X=왼쪽 / Y=위(척추) / Z=앞)
    스윙각  = (어깨->손목) 을 시상면(위-앞 평면)에 투영한 각. **0=수직 아래**,
              **양수=앞**, 음수=뒤. 사람 걷기는 앞 스윙이 뒤 스윙보다 크거나 비슷하다
              (보행 문헌: 어깨 굴곡 20~25도 / 신전 10~20도).
    벌림각  = 몸 바깥으로 벌린 각(어깨 외전). 0=몸에 붙음.
    이 둘은 몸이 기울어도 안 흔들린다(가슴 기준이라). 월드 기준이 아니다.

★어깨 원점은 위팔 본 머리다. 쇄골까지 넣으면 몸통 회전이 섞인다.

손잡이
  GLB     볼 파일          기본 web/basic2.glb
  CLIPS   클립 목록        기본 Walk,Run
  TAG     표 제목에 붙임
  JSON    결과 json 경로(before/after 대조용)
  TIP     1 이면 칼끝 고도·바닥여유도 잰다(칼이 있는 파일만)
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
CLIPS = [c.strip() for c in os.environ.get("CLIPS", "Walk,Run").split(",") if c.strip()]
TAG = os.environ.get("TAG", "")
JSON_OUT = os.environ.get("JSON", "")
WANT_TIP = os.environ.get("TIP", "1") == "1"
TIP_K = float(os.environ.get("TIP_K", "1.0"))     # 하류에서 칼이 커질 배율(s27 과 같은 뜻)
SOLE = 0.045                                      # 게임 groundFeet 이 발을 띄우는 몫
GAME_H = 1.75                                     # 게임이 캐릭터를 이 키로 정규화한다

# Meshy 원명 -> 우리 규칙 (s27 RENAME 과 같은 표. 긴 것부터)
RENAME = [
    ("LeftToeBase", "Bip001 L Toe0"), ("RightToeBase", "Bip001 R Toe0"),
    ("LeftUpLeg", "Bip001 L Thigh"), ("RightUpLeg", "Bip001 R Thigh"),
    ("LeftForeArm", "Bip001 L Forearm"), ("RightForeArm", "Bip001 R Forearm"),
    ("LeftShoulder", "Bip001 L Clavicle"), ("RightShoulder", "Bip001 R Clavicle"),
    ("LeftHand", "Bip001 L Hand"), ("RightHand", "Bip001 R Hand"),
    ("LeftFoot", "Bip001 L Foot"), ("RightFoot", "Bip001 R Foot"),
    ("LeftLeg", "Bip001 L Calf"), ("RightLeg", "Bip001 R Calf"),
    ("LeftArm", "Bip001 L UpperArm"), ("RightArm", "Bip001 R UpperArm"),
    ("Spine02", "Bip001 Chest2"), ("Spine01", "Bip001 Chest"),
    ("Spine", "Bip001 Spine"), ("Hips", "Bip001 Pelvis"),
    ("head_end", "Bip001 HeadNub"), ("headfront", "Bip001 HeadFront"),
    ("Head", "Bip001 Head"), ("neck", "Bip001 Neck"),
]

UP_R, UP_L = "Bip001 R UpperArm", "Bip001 L UpperArm"
HAND_R, HAND_L = "Bip001 R Hand", "Bip001 L Hand"
TORSO, NECK = "Bip001 Spine", "Bip001 Neck"
CLAV_L, CLAV_R = "Bip001 L Clavicle", "Bip001 R Clavicle"
FEET = ["Bip001 L Foot", "Bip001 R Foot", "Bip001 L Toe0", "Bip001 R Toe0"]

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
    if o.type == "MESH" and (o.name.startswith("Icosphere")
                             or any(c.name == "glTF_not_exported"
                                    for c in o.users_collection)):
        bpy.data.objects.remove(o, do_unlink=True)

# ★네이티브 원본은 Meshy 원명이다. **이름을 바꾸지 않고** 읽기만 한다
#   (뼈 이름을 바꾸면 fcurve 경로가 따라가는지 아닌지에 의존하게 된다. s27 함정 3)
NAT = {dst: src for src, dst in RENAME}


def B(bn):
    """우리 이름 -> 이 아마추어에 실제로 있는 이름."""
    if bn in arm.pose.bones:
        return bn
    alt = NAT.get(bn)
    if alt and alt in arm.pose.bones:
        return alt
    return bn

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
K = GAME_H / H                                    # 블렌더 단위 -> 게임 m
arm.data.pose_position = "POSE"

print("=" * 78)
print("[파일] %s%s" % (os.path.basename(GLB), ("  (%s)" % TAG if TAG else "")))
print("       키 %.4f  게임환산 %.4f  액션 %s"
      % (H, K, sorted(a.name for a in bpy.data.actions)))


def fcs_of(act):
    """4.4+ 슬롯형 액션의 fcurve 를 전부 모은다."""
    if hasattr(act, "fcurves") and len(act.fcurves):
        return list(act.fcurves)
    out = []
    for lay in act.layers:
        for st in lay.strips:
            for slot in act.slots:
                cb = st.channelbag(slot)
                if cb:
                    out += list(cb.fcurves)
    return out


def use(act):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    if hasattr(act, "slots") and len(act.slots):   # ★함정 4: 슬롯을 안 물리면 무효
        try:
            ad.action_slot = act.slots[0]
        except Exception:
            pass


def pw(bn):
    m = A2W @ arm.pose.bones[B(bn)].matrix
    r = m.to_3x3()
    r.normalize()
    return m.translation.copy(), r


def torso_frame():
    """가슴 좌표계 (열이 축) X=왼쪽 / Y=위(척추) / Z=앞."""
    up = (pw(NECK)[0] - pw(TORSO)[0]).normalized()
    lat = pw(CLAV_L)[0] - pw(CLAV_R)[0]
    lat = (lat - up * lat.dot(up)).normalized()
    return Matrix((lat, up, lat.cross(up))).transposed()


def sword_axis():
    """오른손 로컬에서 본 칼끝 방향과 손목-칼끝 거리(블렌더 단위)."""
    if not SWORDS:
        return None, 0.0
    sw = None
    for o in SWORDS:                              # 게임 시작 칼
        if "nokseun" in o.name:
            sw = o
    sw = sw or SWORDS[0]
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    Wp, Wr = pw(HAND_R)
    far, dmax = None, -1
    for v in sw.data.vertices:
        p = sw.matrix_world @ v.co
        d = (p - Wp).length
        if d > dmax:
            dmax, far = d, p
    loc = Wr.inverted() @ (far - Wp)
    arm.data.pose_position = "POSE"
    bpy.context.view_layer.update()
    return loc, dmax


TIPLOC, TIPD = (sword_axis() if WANT_TIP else (None, 0.0))
if TIPLOC and TIP_K != 1.0:                       # s34 가 같은 반직선 위에 다시 놓는다
    TIPLOC = TIPLOC * TIP_K
    TIPD *= TIP_K
if TIPLOC:
    print("       칼(%s) 손목->칼끝 %.4f (게임 %.3fm)"
          % ([o.name for o in SWORDS if "nokseun" in o.name] or "?", TIPD, TIPD * K))

RES = {}
print("\n[팔 스윙] 가슴 좌표계 · 0=수직 아래 · **양수=앞** · 음수=뒤 (도)")
print("  %-5s %-4s | %7s %7s %7s %7s | %7s %7s | %s"
      % ("클립", "팔", "앞최대", "뒤최대", "중립", "진폭", "벌림중앙", "벌림최대", "앞/뒤 비"))
for nm in CLIPS:
    act = bpy.data.actions.get(nm)
    if not act and len(bpy.data.actions) == 1:     # 네이티브 원본은 액션이 하나뿐
        act = bpy.data.actions[0]
    if not act:
        print("  %-5s 없음" % nm)
        continue
    use(act)
    fr = act.frame_range
    f0, f1 = int(round(fr[0])), int(round(fr[1]))
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        C = torso_frame()
        Ci = C.transposed()                       # 월드 -> 가슴
        row = dict(f=f)
        # 접지: 이 프레임 가장 낮은 발 본 (게임 groundFeet 근사)
        foot = min(pw(b)[0].z for b in FEET if B(b) in arm.pose.bones)
        row["foot"] = foot
        for side, ub, hb in (("R", UP_R, HAND_R), ("L", UP_L, HAND_L)):
            S = pw(ub)[0]
            W = pw(hb)[0]
            d = Ci @ (W - S)
            dn = -d.y                             # 아래 성분
            fwd = d.z                             # 앞 성분
            out = (-d.x if side == "R" else d.x)  # 몸 바깥
            row[side] = dict(
                swing=math.degrees(math.atan2(fwd, dn)),
                abd=math.degrees(math.atan2(out, dn)),
                hx=out * K, hy=d.y * K, hz=fwd * K,
                hw=W.z,                           # 손목 월드 z(블렌더 단위)
            )
        if TIPLOC:
            Wp, Wr = pw(HAND_R)
            tip = Wp + Wr @ TIPLOC
            row["tip"] = tip.z
            td = (Wr @ TIPLOC).normalized()
            row["tip_elev"] = math.degrees(math.asin(max(-1, min(1, td.z))))
            t = Ci @ (tip - pw(UP_R)[0])          # 오른어깨 기준 가슴 좌표
            row["tip_out"] = -t.x * K
            row["tip_up"] = t.y * K
            row["tip_fwd"] = t.z * K
        rows.append(row)
    ground = min(r["foot"] for r in rows)          # 사이클 최저 발 = 바닥(달리기 규칙)
    RES[nm] = rows
    for side in ("R", "L"):
        sw = [r[side]["swing"] for r in rows]
        ab = [r[side]["abd"] for r in rows]
        fmax, bmax = max(sw), min(sw)
        mid = (fmax + bmax) / 2.0
        amp = fmax - bmax
        sab = sorted(ab)
        print("  %-5s %-4s | %+7.1f %+7.1f %+7.1f %7.1f | %7.1f %7.1f | %s"
              % (nm, "오른" if side == "R" else "왼", fmax, bmax, mid, amp,
                 sab[len(sab) // 2], max(ab, key=abs),
                 ("%.2f" % (fmax / -bmax)) if bmax < -0.01 else "-"))
    if TIPLOC:
        # ★s27 measure 와 같은 잣대: (칼최저 - 발본) * 환산 + 1.75*0.045
        cl = [(r["tip"] - ground) * K + GAME_H * SOLE for r in rows]
        clf = [(r["tip"] - r["foot"]) * K + GAME_H * SOLE for r in rows]
        te = [r["tip_elev"] for r in rows]
        hw = [(r["R"]["hw"] - ground) * K + GAME_H * SOLE for r in rows]
        print("        칼끝 바닥여유 최소 %+.3f m (사이클접지) / %+.3f m (프레임접지)"
              "   칼끝고도 평균 %+.1f도 (%+.1f~%+.1f)"
              % (min(cl), min(clf), sum(te) / len(te), min(te), max(te)))
        print("        오른손목 바닥 위 %.3f~%.3f m   (여유 = 손목높이 - %.3f*sin(-고도))"
              % (min(hw), max(hw), TIPD * K))
        print("        칼끝 자리(오른어깨 기준 가슴좌표) 밖 %+.2f~%+.2f / 앞 %+.2f~%+.2f m"
              % (min(r["tip_out"] for r in rows), max(r["tip_out"] for r in rows),
                 min(r["tip_fwd"] for r in rows), max(r["tip_fwd"] for r in rows)))

if JSON_OUT:
    p = JSON_OUT if os.path.isabs(JSON_OUT) else os.path.join(ROOT, JSON_OUT)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fp:
        json.dump({"glb": GLB, "tag": TAG, "K": K, "clips": RES}, fp)
    print("\n[json] %s" % p)
print("=" * 78)
