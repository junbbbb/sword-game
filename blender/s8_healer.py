# -*- coding: utf-8 -*-
"""검사 모델을 개조해 **여성 힐러 겸 궁수**를 만든다. healer.blend 로 저장.

왜 개조인가
  에셋에 여성 모델이 없다(팩 전체에 ToonSoldier 남성 하나뿐).
  같은 뼈대를 쓰면 지금까지 만든 동작(달리기·베기·점프·리타게터)이 **그대로 돈다**.
  나중에 모델을 통째로 교체하더라도, 지금은 힐러가 게임에서 어떻게 움직이는지
  잡는 게 먼저다.

형태를 어떻게 바꾸나
  저폴리에서 여성 실루엣을 읽히게 하는 건 얼굴 디테일이 아니라 **비율**이다.
    어깨 좁게 / 허리 잘록 / 골반 넓게 / 팔다리 가늘게 / 머리 작게 / 키 살짝 작게
  ★z 높이 밴드로만 처리하면 T 포즈에서 **팔이 어깨 높이**라 같이 눌린다.
  그래서 부위 판정은 반드시 **버텍스 그룹**으로 한다.

덧붙이는 것
  치마(군복 웨빙·탄창 파우치를 가린다) / 긴 머리 / 활
실행: blender --background --python s8_healer.py
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
import build_scenes as BS
import combo_poses as CP
importlib.reload(BS)
importlib.reload(CP)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
body = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))

# 칼은 힐러에겐 필요없다
for o in list(sc.objects):
    if o.name.startswith(("bladeK", "gripK", "tsubaK", "pomK", "ringK", "katana")):
        bpy.data.objects.remove(o, do_unlink=True)

for b in arm.pose.bones:
    b.rotation_mode = "QUATERNION"
    b.matrix_basis = Matrix()
arm.data.pose_position = "REST"
bpy.context.view_layer.update()

zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
H = max(zs) - min(zs)
Z0 = min(zs)
xs = [(body.matrix_world @ v.co).x for v in body.data.vertices]
CX = (min(xs) + max(xs)) / 2
print("원본 키 %.3f" % H)

# ---------------------------------------------------------------- 부위 판정
vgn = {g.index: g.name for g in body.vertex_groups}
PART = {}
for v in body.data.vertices:
    best, bw = None, -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, vgn.get(g.group, "")
    PART[v.index] = (best or "").lower()


def is_part(i, *keys):
    return any(k in PART[i] for k in keys)


# ---------------------------------------------------------------- 비율 개조
MW = body.matrix_world
MWI = MW.inverted()


def bone_axis(key):
    """뼈의 월드 시작점과 방향(자식 쪽)."""
    ps = CP.Poser(arm, H)
    p = ps.wpos(key)
    d = ps.bone_dir(key)
    return p, (d if d else Vector((1, 0, 0)))


for v in body.data.vertices:
    w = MW @ v.co
    i = v.index
    t = (w.z - Z0) / H                      # 0 = 발, 1 = 정수리

    if is_part(i, "upperarm", "forearm", "hand"):
        # 팔: 뼈 축에서의 반경만 줄인다(길이는 유지 = 리깅이 안 깨진다)
        key = ("l " if " l " in (" " + PART[i] + " ") or "l upperarm" in PART[i]
               or "l forearm" in PART[i] or "l hand" in PART[i] else "r ")
        nm = ("l" if "l " in PART[i] else "r")
        base, d = bone_axis("%s upperarm" % nm)
        rel = w - base
        along = rel.dot(d)
        perp = rel - d * along
        w = base + d * along + perp * 0.80          # 팔 굵기 -20%
    elif is_part(i, "thigh", "calf", "foot", "toe"):
        w.x = CX + (w.x - CX) * 0.93                # 다리 살짝 가늘게
        w.y *= 0.94
    elif is_part(i, "head", "neck"):
        # 머리 작게(여성·소녀 비율). 목 기준으로 축소.
        pivot = Z0 + H * 0.845
        w.x = CX + (w.x - CX) * 0.92
        w.y *= 0.92
        w.z = pivot + (w.z - pivot) * 0.93
    else:
        # 몸통: 높이 밴드로 어깨/가슴/허리/골반
        if t > 0.74:                                # 어깨
            k = 0.84
        elif t > 0.655:                             # 가슴
            k = 0.90
        elif t > 0.575:                             # 허리 (가장 잘록)
            k = 0.80
        elif t > 0.47:                              # 골반
            k = 1.06
        else:
            k = 0.97
        w.x = CX + (w.x - CX) * k
        # 앞뒤: 허리는 얇게, 골반·가슴은 유지
        w.y *= (0.82 if 0.575 < t <= 0.655 else (0.88 if t > 0.74 else 1.0))
        # 가슴 볼륨: 앞쪽(-y)으로 살짝
        if 0.645 < t < 0.735 and w.y < 0:
            w.y -= H * 0.022 * math.sin((t - 0.645) / 0.09 * math.pi)
    v.co = MWI @ w

print("비율 개조 완료")

# ---------------------------------------------------------------- 긴 머리
hair = [o for o in sc.objects if o.type == "MESH" and o.name.startswith(("hl", "hair"))]
HEAD_BONE = next(b.name for b in arm.pose.bones if b.name.lower().endswith("head"))
for o in hair:
    # 머리 크기 축소에 맞춰 같이 줄이고, 뒤쪽 가닥은 길게 늘여 뒷머리를 만든다
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        pivot = Z0 + H * 0.845
        w.x = CX + (w.x - CX) * 0.92
        w.y *= 0.92
        w.z = pivot + (w.z - pivot) * 0.93
        v.co = o.matrix_world.inverted() @ w
print("머리카락 %d개 조정" % len(hair))

# 긴 뒷머리: 목덜미에서 등까지 내려오는 판 몇 장
mat_hair = None
for o in hair:
    if o.data.materials:
        mat_hair = o.data.materials[0]
        break
strands = []
for i in range(7):
    u = (i / 6.0 - 0.5)                     # -0.5 ~ 0.5 좌우
    wdt = H * (0.055 - abs(u) * 0.030)
    lng = H * (0.30 - abs(u) * 0.10)
    top = Z0 + H * 0.895
    yb = H * 0.075                          # 뒤통수 뒤쪽
    vs = []
    for k in range(5):
        s = k / 4.0
        zz = top - lng * s
        # 등을 따라 살짝 앞으로 붙는다
        yy = yb + H * 0.02 * s
        ww = wdt * (1.0 - 0.55 * s)
        vs.append((CX + u * H * 0.115 - ww, yy, zz))
        vs.append((CX + u * H * 0.115 + ww, yy, zz))
    fs = [(k * 2, k * 2 + 1, k * 2 + 3, k * 2 + 2) for k in range(4)]
    me = bpy.data.meshes.new("hb%d" % i)
    me.from_pydata(vs, [], fs)
    me.validate()
    ob = bpy.data.objects.new("hb%d" % i, me)
    sc.collection.objects.link(ob)
    if mat_hair:
        ob.data.materials.append(mat_hair)
    sol = ob.modifiers.new("Sol", "SOLIDIFY")
    sol.thickness = H * 0.012
    strands.append(ob)
print("뒷머리 %d가닥" % len(strands))

# ---------------------------------------------------------------- 치마
# 군복 웨빙·탄창 파우치를 가리면서 여성 실루엣을 만든다.
mat_robe = BS.cel_mat("robe_healer", "6E4A7A", soft=0.2)
SK_N = 20
vs, fs = [], []
z_top = Z0 + H * 0.505
z_bot = Z0 + H * 0.325
r_top = H * 0.125
r_bot = H * 0.205
for k in range(SK_N):
    a = 2 * math.pi * k / SK_N
    ca, sa = math.cos(a), math.sin(a)
    flare = 1.0 + 0.10 * math.sin(a * 5)        # 가장자리 물결
    vs.append((CX + ca * r_top, sa * r_top * 0.86, z_top))
    vs.append((CX + ca * r_bot * flare, sa * r_bot * flare * 0.86,
               z_bot - H * 0.02 * abs(math.sin(a * 5))))
for k in range(SK_N):
    a0 = k * 2
    a1 = ((k + 1) % SK_N) * 2
    fs.append((a0, a1, a1 + 1, a0 + 1))
me = bpy.data.meshes.new("skirt")
me.from_pydata(vs, [], fs)
me.validate()
skirt = bpy.data.objects.new("skirt", me)
sc.collection.objects.link(skirt)
skirt.data.materials.append(mat_robe)
sol = skirt.modifiers.new("Sol", "SOLIDIFY")
sol.thickness = H * 0.008
print("치마 생성")

# ---------------------------------------------------------------- 뼈 웨이트 후 병합
PELVIS = next(b.name for b in arm.pose.bones if b.name.lower().endswith("pelvis"))
extra = [(o, HEAD_BONE) for o in strands] + [(skirt, PELVIS)]
for ob, bone in extra:
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    for md in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.shade_smooth()
    vg = ob.vertex_groups.new(name=bone)
    vg.add(range(len(ob.data.vertices)), 1.0, "REPLACE")
    m = ob.modifiers.new("Armature", "ARMATURE")
    m.object = arm

bpy.ops.object.select_all(action="DESELECT")
for ob, _ in extra:
    ob.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print("병합 후 면 %d  정점 %d" % (len(body.data.polygons), len(body.data.vertices)))

# ---------------------------------------------------------------- 활
# 원점 = 손잡이 중앙, +Z = 위(활 상하), 시위는 -X 쪽
BOW_S = H * 0.62
m_wood = BS.cel_mat("bow_wood", "6B4A2E", soft=0.2)
m_grip = BS.cel_mat("bow_grip", "3C2A44", soft=0.2)
m_str = BS.cel_mat("bow_str", "E8E4D8", soft=0.15)
root = bpy.data.objects.new("bow_root", None)
sc.collection.objects.link(root)

NB = 14
bw, bfs = [], []
for k in range(NB + 1):
    s = k / NB - 0.5                       # -0.5(아래) ~ 0.5(위)
    zz = s * BOW_S
    # 활대: 가운데가 앞(+x)으로 나오고 양끝이 뒤로 젖혀진 리커브
    xx = (0.10 - 0.62 * s * s) * BOW_S * 0.5
    if abs(s) > 0.40:                       # 끝에서 다시 앞으로 꺾인다(리커브)
        xx += (abs(s) - 0.40) * 1.9 * BOW_S * 0.5
    wdt = BOW_S * (0.030 - 0.016 * abs(s) * 2)
    bw.append((xx, -wdt, zz))
    bw.append((xx, wdt, zz))
for k in range(NB):
    a = k * 2
    bfs.append((a, a + 2, a + 3, a + 1))
me = bpy.data.meshes.new("bow_limb")
me.from_pydata(bw, [], bfs)
me.validate()
limb = bpy.data.objects.new("bow_limb", me)
sc.collection.objects.link(limb)
limb.data.materials.append(m_wood)
sol = limb.modifiers.new("Sol", "SOLIDIFY")
sol.thickness = BOW_S * 0.022
sol.offset = 0
limb.parent = root

grip = BS.prim("cylinder", "bow_grip", mat=m_grip, vertices=12,
               radius=BOW_S * 0.038, depth=BOW_S * 0.20,
               rot=(math.radians(90), 0, 0), bevel=0.004)
grip.rotation_euler = (0, 0, 0)
grip.location = (bw[NB][0], 0, 0)
grip.scale = (1, 1, 1)
grip.parent = root
# 시위
sx = bw[0][0]
top = bw[NB * 2][2]
bot = bw[0][2]
strv = [(sx - BOW_S * 0.02, -BOW_S * 0.006, bot), (sx - BOW_S * 0.02, BOW_S * 0.006, bot),
        (sx - BOW_S * 0.02, BOW_S * 0.006, top), (sx - BOW_S * 0.02, -BOW_S * 0.006, top)]
me = bpy.data.meshes.new("bow_string")
me.from_pydata(strv, [], [(0, 1, 2, 3)])
me.validate()
st = bpy.data.objects.new("bow_string", me)
sc.collection.objects.link(st)
st.data.materials.append(m_str)
st.parent = root
print("활 생성 (길이 %.3f = 키의 %.0f%%)" % (BOW_S, BOW_S / H * 100))

arm.data.pose_position = "POSE"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, "healer.blend"))
print("SAVED healer.blend")
