# -*- coding: utf-8 -*-
"""점프 체공 중 **왼팔 팔꿈치가 몸통에서 얼마나 떨어져 있는가** 실측 (17-점프왼팔).

    GLB=web/basic2.glb JSON=/tmp/before.json blender -b -P blender/probe_jump_larm.py

오너 지시: **"점프할때 칼안든손 팔꿈치가 몸통에왜이렇게 붙어있음.
              칼든손처럼 좀 자연스러운자세가 되어야지."**
왼팔을 **오른팔(칼 든 팔)과 같은 잣대로 나란히** 재려고 만들었다. 17-점프기하가
오른팔에 EB(팔꿈치) 채널을 내면서 세운 규칙 셋을 그대로 쓴다:

  1. ★**어깨 외전은 '어깨->손목'이 아니라 '어깨->팔꿈치'로 잰다.**
     팔꿈치를 굽히면 손목 기준 각이 10~15도 부풀어 "살짝 벌림 15~30도"를 잘못 판정한다.
     (BAL_KEYS 의 A · SWD_KEYS 의 A 는 둘 다 **손목 기준**이다. 목표값이지 실측이 아니다.)
  2. 각은 **가슴 좌표계**에서 뽑는다(X=왼쪽 / Y=위 / Z=앞). 월드 위를 기준으로 잡으면
     몸이 기운 프레임에서 투영이 무너진다.
  3. 판정은 게임이 멈춰 세우는 **두 장(f7 상승 · f13 하강)** 이 1순위다.

무엇을 '몸통에 붙었다'로 재나 — 셋을 같이 본다(하나만 보면 속는다)
    팔꿈치-척추축 거리   팔꿈치에서 골반->목 선분까지의 수직 거리(게임 m).
                         팔을 아래로 늘어뜨리면 어깨너비 절반(약 0.19m)에서 멈춘다.
    팔꿈치 옆벌림 out     팔꿈치의 가슴좌표 '바깥' 성분(어깨 원점, 게임 m).
                         ★이게 음수면 팔꿈치가 **몸 안쪽으로** 들어간 것이다.
    팔꿈치-몸통 메시 틈   팔꿈치 관절점에서 몸통·다리 정점까지의 최소 거리(게임 m).
                         눈에 보이는 '겨드랑이 틈'에 제일 가깝다.

손잡이(환경변수)
  GLB     볼 파일      기본 web/basic2.glb
  CLIPS   클립 목록    기본 Jump
  JSON    결과 json    (선택. before/after 대조용)
  TAG     표 제목
  PEN     1 이면 메시 틈까지 잰다(기본 1)
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
PEN = os.environ.get("PEN", "1") == "1"

UP_L, FORE_L, HAND_L = "Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand"
UP_R, FORE_R, HAND_R = "Bip001 R UpperArm", "Bip001 R Forearm", "Bip001 R Hand"
PELVIS, TORSO, NECK = "Bip001 Pelvis", "Bip001 Spine", "Bip001 Neck"
CLAV_L, CLAV_R = "Bip001 L Clavicle", "Bip001 R Clavicle"
GAME_H = 1.75
TRUNK = ("Bip001 Spine", "Bip001 Spine1", "Bip001 Pelvis", "Bip001 Head",
         "Bip001 L Thigh", "Bip001 R Thigh", "Bip001 L Calf", "Bip001 R Calf",
         "Bip001 Neck")

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


def wpos(bn):
    return (A2W @ arm.pose.bones[bn].matrix).translation.copy()


def torso_frame():
    """가슴 좌표계 (열이 축) X=왼쪽 / Y=위(척추) / Z=앞.  s24 torso_frame 과 같은 식."""
    up = (wpos(NECK) - wpos(TORSO)).normalized()
    lat = wpos(CLAV_L) - wpos(CLAV_R)
    lat = (lat - up * lat.dot(up)).normalized()
    return Matrix((lat, up, lat.cross(up))).transposed()


SH_W = (wpos(UP_L) - wpos(UP_R)).length * K         # 어깨 사이 폭(게임 m)
ARM_UP = (wpos(FORE_L) - wpos(UP_L)).length * K
ARM_FO = (wpos(HAND_L) - wpos(FORE_L)).length * K
arm.data.pose_position = "POSE"
print("\n[리그 상수] 어깨폭 %.3fm · 위팔 %.3fm · 팔뚝 %.3fm  (게임 m, 키 %.2fm 환산)"
      % (SH_W, ARM_UP, ARM_FO, GAME_H))


# ---------------------------------------------------------------- 몸통 메시 틈
def _verts_of(bones, thr=0.5):
    out = []
    for o in BODY:
        gi = [o.vertex_groups[b].index for b in bones if b in o.vertex_groups]
        if not gi:
            continue
        for v in o.data.vertices:
            if sum(x.weight for x in v.groups if x.group in gi) > thr:
                out.append((o, v.index))
    return out


TRUNK_V = _verts_of(TRUNK) if PEN else []


def trunk_pts():
    """이 프레임의 몸통·다리 정점 좌표 배열(블렌더 단위)."""
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    out, cache = [], {}
    for o, i in TRUNK_V:
        me = cache.get(o.name)
        if me is None:
            me = cache[o.name] = o.evaluated_get(dg).to_mesh()
        p = o.matrix_world @ me.vertices[i].co
        out.append([p.x, p.y, p.z])
    for o in {o for o, _ in TRUNK_V}:
        o.evaluated_get(dg).to_mesh_clear()
    return np.array(out)


def _seg_dist(p, a, b):
    """점 p 에서 선분 ab 까지의 거리."""
    ab = b - a
    L2 = ab.dot(ab)
    if L2 < 1e-9:
        return (p - a).length
    s = max(0.0, min(1.0, (p - a).dot(ab) / L2))
    return (p - (a + ab * s)).length


def use(act):
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def arm_row(side, TP):
    """한 팔의 실측 한 줄. side 'L' 이면 바깥 = 가슴 +X, 'R' 이면 -X."""
    import numpy as np
    S, E, W = (wpos(UP_L), wpos(FORE_L), wpos(HAND_L)) if side == "L" \
        else (wpos(UP_R), wpos(FORE_R), wpos(HAND_R))
    C = torso_frame()
    Ci = C.transposed()                             # 월드 -> 가슴
    sgn = 1.0 if side == "L" else -1.0
    ue = (E - S).normalized()                       # ★위팔(어깨->팔꿈치)
    uw = (W - S).normalized()                       # 어깨->손목(BAL_KEYS 의 A 가 이쪽)
    fu = (W - E).normalized()                       # 팔뚝
    lu, lw = Ci @ ue, Ci @ uw
    # 외전 A = '바깥' 성분의 각(BAL_KEYS 의 u = (sinA, -cosA cosF, cosA sinF) 와 같은 식)
    abd_up = math.degrees(math.asin(max(-1.0, min(1.0, lu.x * sgn))))
    abd_wr = math.degrees(math.asin(max(-1.0, min(1.0, lw.x * sgn))))
    fwd_up = math.degrees(math.atan2(lu.z, max(1e-9, math.hypot(lu.x, lu.y))))
    flex = math.degrees(ue.angle(fu))               # 팔꿈치 굽힘(0 = 완전히 편 팔)
    ext = (W - S).length / max(1e-9, (E - S).length + (W - E).length)   # 뻗음 비 k
    Ep = Ci @ (E - S)                               # 어깨 원점, 가슴 좌표(블렌더 단위)
    spine = _seg_dist(E, wpos(PELVIS), wpos(NECK)) * K
    gap = -1.0
    if PEN and TP is not None:
        d = np.sqrt(((TP - np.array([E.x, E.y, E.z])) ** 2).sum(-1))
        gap = float(d.min()) * K
    return dict(abd_up=abd_up, abd_wr=abd_wr, fwd_up=fwd_up, flex=flex, ext=ext,
                el_out=Ep.x * sgn * K, el_up=Ep.y * K, el_fwd=Ep.z * K,
                spine=spine, gap=gap,
                fore_elev=math.degrees(math.asin(max(-1.0, min(1.0, fu.z)))))


OUT = {}
for nm in CLIPS:
    act = bpy.data.actions.get(nm)
    if not act:
        print("   %s 액션이 없다" % nm)
        continue
    use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    print("\n[%s] f%d~%d   ★과녁 = 왼 팔꿈치가 몸통에서 떨어져 있는가" % (nm, f0, f1))
    print("   외전 = 어깨->팔꿈치의 바깥 각(오너 기준 '살짝' 15~30도) · 굽힘 = 0 이면 편 팔")
    print("   %3s %5s | %-34s | %-34s"
          % ("f", "위상", "왼팔 외전/굽힘/팔꿈치out/척추/틈",
             "오른팔 외전/굽힘/팔꿈치out/척추/틈"))
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        TP = trunk_pts() if PEN else None
        L = arm_row("L", TP)
        R = arm_row("R", TP)
        ph = (f - f0) / max(1, f1 - f0)
        rows.append(dict(f=f, t=round(ph, 3), L=L, R=R))
        print("   %3d %5.2f | %+5.1f %5.1f %+6.3f %5.3f %5.3f | %+5.1f %5.1f %+6.3f %5.3f %5.3f"
              % (f, ph, L["abd_up"], L["flex"], L["el_out"], L["spine"], L["gap"],
                 R["abd_up"], R["flex"], R["el_out"], R["spine"], R["gap"]))
    OUT[nm] = rows
    hold = [r for r in rows if abs(r["t"] - 0.27) < 0.03 or abs(r["t"] - 0.55) < 0.03]
    if hold:
        print("\n   ★게임이 멈춰 세우는 두 장 — 왼팔 vs 오른팔 나란히")
        print("   %-4s %-6s %8s %8s %9s %9s %8s %7s"
              % ("장", "팔", "외전(위팔)", "외전(손목)", "팔꿈치굽힘", "팔꿈치out",
                 "척추거리", "메시틈"))
        for r in hold:
            for k, nmk in (("L", "왼(빈손)"), ("R", "오른(칼)")):
                d = r[k]
                print("   f%-3d %-6s %+7.1f도 %+7.1f도 %8.1f도 %+8.3fm %7.3fm %6.3fm"
                      % (r["f"], nmk, d["abd_up"], d["abd_wr"], d["flex"],
                         d["el_out"], d["spine"], d["gap"]))
    air = [r for r in rows if 4 <= r["f"] <= 14]
    if air:
        for k, nmk in (("L", "왼(빈손)"), ("R", "오른(칼)")):
            v = [r[k] for r in air]
            print("   체공 f4~f14 %s 외전 %+.1f~%+.1f도 · 굽힘 %.1f~%.1f도"
                  " · 팔꿈치out %+.3f~%+.3fm · 척추거리 %.3f~%.3fm"
                  % (nmk, min(x["abd_up"] for x in v), max(x["abd_up"] for x in v),
                     min(x["flex"] for x in v), max(x["flex"] for x in v),
                     min(x["el_out"] for x in v), max(x["el_out"] for x in v),
                     min(x["spine"] for x in v), max(x["spine"] for x in v)))

if JSON_OUT:
    with open(JSON_OUT, "w") as fp:
        json.dump(dict(tag=TAG, glb=GLB, sh_w=SH_W, arm_up=ARM_UP, arm_fo=ARM_FO,
                       clips=OUT), fp, indent=1)
    print("\n[json] %s" % JSON_OUT)
