# -*- coding: utf-8 -*-
"""poc 2단계: GLB 의 Heavy 액션을 프레임별로 실측한다.
    GLB=<경로> OUTJSON=<경로> Blender -b --factory-startup --python measure_metrics.py
잰다: (a)프레임간 최대 뼈 회전 (b)움직인 뼈/총 회전량 (c)칼끝 최저 z
      (d)왼손-칼자루축 거리 (e)프레임별 발 최저 높이 (f)칼끝 속도·hot 구간
칼 = SW_nokseun(게임 시작검, R Hand 100% 리지드).
"""
import bpy, json, math, os
from mathutils import Vector, Matrix

GLB = os.environ["GLB"]
OUTJSON = os.environ["OUTJSON"]
ACTION = os.environ.get("ACTION", "Heavy")
SWORD = "SW_nokseun"
HAND_R, HAND_L = "Bip001 R Hand", "Bip001 L Hand"
FEET = ["Bip001 L Foot", "Bip001 R Foot", "Bip001 L Toe0", "Bip001 R Toe0"]
BONES24 = ["Bip001 Pelvis", "Bip001 Chest2", "Bip001 Chest", "Bip001 Spine",
           "Bip001 Neck", "Bip001 Head", "Bip001 HeadFront", "Bip001 HeadNub",
           "Bip001 L Clavicle", "Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand",
           "Bip001 R Clavicle", "Bip001 R UpperArm", "Bip001 R Forearm", "Bip001 R Hand",
           "Bip001 L Thigh", "Bip001 L Calf", "Bip001 L Foot", "Bip001 L Toe0",
           "Bip001 R Thigh", "Bip001 R Calf", "Bip001 R Foot", "Bip001 R Toe0"]

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
sc = bpy.context.scene
sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
ad = arm.animation_data
for t in ad.nla_tracks:
    t.mute = True
act = bpy.data.actions[ACTION]
ad.action = act
try:
    ad.action_slot = act.slots[0]
except Exception as e:
    print("slot 지정 실패:", e)
f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
nf = f1 - f0 + 1
print("[측정] %s 액션 %s f%d~%d (%d장)" % (os.path.basename(GLB), ACTION, f0, f1, nf))

Mw = arm.matrix_world.copy()
rest_base = min((Mw @ arm.data.bones[b].head_local).z for b in FEET)

# ---- 캐릭터 키(게임이 1.75 로 정규화한다 -> 속도 환산 계수) ----
ch = bpy.data.objects['char1']
H = max((ch.matrix_world @ v.co).z for v in ch.data.vertices)
gk = 1.75 / H

# ---- 칼끝/자루축 (바인드에서 잡고 R Hand 강체로 따라간다) ----
sw = bpy.data.objects[SWORD]
Msw = sw.matrix_world.copy()
verts = [Msw @ v.co for v in sw.data.vertices]
hand_rest4 = Mw @ arm.data.bones[HAND_R].matrix_local
hand_rest_p = hand_rest4.to_translation()
tip_bind = max(verts, key=lambda v: (v - hand_rest_p).length)
mean = sum(verts, Vector()) / len(verts)
# 주축: 평균 제거 후 최대 분산 방향(멱승법)
u = (tip_bind - mean).normalized()
for _ in range(30):
    acc = Vector()
    for v in verts:
        d = v - mean
        acc += d * d.dot(u)
    u = acc.normalized()
if u.dot(tip_bind - mean) < 0:
    u = -u                          # +u = 칼끝 쪽
pommel_bind = min(verts, key=lambda v: (v - mean).dot(u))
blade_len = (tip_bind - pommel_bind).length
print("[칼] %s 정점 %d  주축 %s  길이(자루끝~칼끝) %.3fm  칼끝바인드 %s"
      % (SWORD, len(verts), [round(x, 3) for x in u], blade_len,
         [round(x, 3) for x in tip_bind]))
hand_rest_inv = hand_rest4.inverted()

# ---- 프레임 루프 ----
quats = {b: [] for b in BONES24}
tips, poms, lhs, rhs, feet_low = [], [], [], [], []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    for b in BONES24:
        quats[b].append(arm.pose.bones[b].rotation_quaternion.copy())
    T = (Mw @ arm.pose.bones[HAND_R].matrix) @ hand_rest_inv
    tips.append(T @ tip_bind)
    poms.append(T @ pommel_bind)
    lhs.append((Mw @ arm.pose.bones[HAND_L].matrix).translation.copy())
    rhs.append((Mw @ arm.pose.bones[HAND_R].matrix).translation.copy())
    feet_low.append(min((Mw @ arm.pose.bones[b].matrix).translation.z for b in FEET))

def qang(a, b):
    d = min(1.0, abs(a.dot(b)))
    return math.degrees(2.0 * math.acos(d))

# (a) 프레임간 최대 뼈 회전
step_max, per_bone_total = [], {}
gmax = (0.0, None, None)
for b in BONES24:
    tot = 0.0
    for i in range(1, nf):
        ang = qang(quats[b][i - 1], quats[b][i])
        tot += ang
        if ang > gmax[0]:
            gmax = (ang, b, f0 + i)
    per_bone_total[b] = tot
top5 = []
for b in BONES24:
    m = max((qang(quats[b][i - 1], quats[b][i]), f0 + i) for i in range(1, nf))
    top5.append((round(m[0], 1), b, m[1]))
top5.sort(reverse=True)

# (b) 움직인 뼈(총 회전 1도 초과)
moved = [b for b in BONES24 if per_bone_total[b] > 1.0]
total_rot = sum(per_bone_total.values())

# (d) 왼손-자루축 거리 (자루축 = pommel->tip 무한선)
def line_dist(p, a, b):
    ab = b - a
    return ((p - a).cross(ab)).length / ab.length
lh_d = [line_dist(lhs[i], poms[i], tips[i]) for i in range(nf)]
rh_d = [line_dist(rhs[i], poms[i], tips[i]) for i in range(nf)]

# (f) 칼끝 속도 (클립 시간 기준, 게임 키 1.75 정규화 환산 포함)
spd_raw = [0.0] + [(tips[i] - tips[i - 1]).length * 30.0 for i in range(1, nf)]
spd_game = [v * gk for v in spd_raw]
# 시각: f0 를 0초로. 인덱스 i -> i/30 초
def runs_of(vs, thr):
    runs, s = [], None
    for i, v in enumerate(vs):
        on = v >= thr
        if on and s is None:
            s = i
        if not on and s is not None:
            runs.append((s / 30.0, (i - 1) / 30.0))
            s = None
    if s is not None:
        runs.append((s / 30.0, (nf - 1) / 30.0))
    return runs

res = dict(
    glb=GLB, action=ACTION, frames=[f0, f1], nf=nf,
    char_h=round(H, 4), gk=round(gk, 4), rest_feet_base=round(rest_base, 4),
    blade_len=round(blade_len, 4),
    a_max_step=dict(deg=round(gmax[0], 2), bone=gmax[1], frame=gmax[2],
                    t=round((gmax[2] - f0) / 30.0, 3)),
    a_top5=top5[:5],
    b_moved=len(moved), b_moved_names=moved,
    b_total_deg=round(total_rot, 1),
    b_parts={k: round(per_bone_total[k], 1) for k in
             ["Bip001 Head", "Bip001 L Clavicle", "Bip001 R Clavicle",
              "Bip001 Chest2", "Bip001 Chest", "Bip001 Spine", "Bip001 Neck", "Bip001 Pelvis"]},
    b_per_bone={k: round(v, 1) for k, v in sorted(per_bone_total.items(), key=lambda x: -x[1])},
    c_tip_z=[round(t.z, 4) for t in tips],
    c_tip_min=dict(z=round(min(t.z for t in tips), 4),
                   frame=f0 + min(range(nf), key=lambda i: tips[i].z),
                   t=round(min(range(nf), key=lambda i: tips[i].z) / 30.0, 3)),
    d_lh=[round(v, 4) for v in lh_d], d_lh_max=dict(m=round(max(lh_d), 4),
        frame=f0 + lh_d.index(max(lh_d)), t=round(lh_d.index(max(lh_d)) / 30.0, 3)),
    d_rh=[round(v, 4) for v in rh_d], d_rh_max=round(max(rh_d), 4),
    e_feet=[round(v, 4) for v in feet_low],
    e_feet_rel=[round(v - rest_base, 4) for v in feet_low],
    f_spd_raw=[round(v, 2) for v in spd_raw],
    f_spd_game=[round(v, 2) for v in spd_game],
    f_vmax=dict(raw=round(max(spd_raw), 2), game=round(max(spd_game), 2),
                frame=f0 + spd_game.index(max(spd_game)),
                t=round(spd_game.index(max(spd_game)) / 30.0, 3)),
    f_hot_189=runs_of(spd_game, 18.9),
    f_hot_158=runs_of(spd_game, 15.8),
    tips=[[round(x, 4) for x in t] for t in tips],
)
with open(OUTJSON, 'w') as fh:
    json.dump(res, fh, indent=1)
print(json.dumps({k: v for k, v in res.items() if not k.startswith(('c_tip_z', 'd_lh', 'd_rh', 'e_', 'f_spd', 'tips')) or k.endswith('max') or k.endswith('min')}, ensure_ascii=False, indent=1))
print("MEASURE_DONE")
