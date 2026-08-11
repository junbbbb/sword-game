# -*- coding: utf-8 -*-
# ToonSoldiers 병사 -> 귀멸 검사 개조
#   1) FBX 임포트 -> 루즈 파츠 리포트 -> 소총 파츠 삭제
#   2) 리페인트 텍스처 적용
#   3) 카타나 생성 후 오른손 본에 부착
#   4) 포즈 + 렌더 (history 자동 보관)
# 실행: blender --background --python convert_to_slayer.py
import bpy
import bmesh
import os
import sys
import math
import shutil
import time
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
FBX = os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX")
NEWTEX = os.path.join(ROOT, "refpack/demon_slayer_tex.png")
REN = os.path.join(ROOT, "renders")
HIST = os.path.join(REN, "history")
os.makedirs(HIST, exist_ok=True)
RUN = time.strftime("%m%d_%H%M%S")

sys.path.insert(0, BLD)
import build_scenes as BS   # build_katana / cel_mat 재사용

# ---------------------------------------------------------------- 씬 준비
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
ids = [it.identifier for it in sc.render.bl_rna.properties["engine"].enum_items]
for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    if cand in ids:
        sc.render.engine = cand
        break
try:
    sc.eevee.taa_render_samples = 64
except Exception:
    pass
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.020, 0.023, 0.032, 1)

bpy.ops.import_scene.fbx(filepath=FBX)
mesh_ob = next(o for o in sc.objects if o.type == "MESH")
arm_ob = next(o for o in sc.objects if o.type == "ARMATURE")

# ---------------------------------------------------------------- 루즈 파츠 분석 + 소총 제거
me = mesh_ob.data
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()

# 연결 요소 찾기
seen = set()
parts = []
for v in bm.verts:
    if v.index in seen:
        continue
    stack = [v]
    comp = []
    seen.add(v.index)
    while stack:
        cur = stack.pop()
        comp.append(cur)
        for e in cur.link_edges:
            o = e.other_vert(cur)
            if o.index not in seen:
                seen.add(o.index)
                stack.append(o)
    parts.append(comp)

print("\n" + "=" * 70)
print("LOOSE PARTS: %d" % len(parts))
info = []
for i, comp in enumerate(parts):
    xs = [v.co.x for v in comp]
    ys = [v.co.y for v in comp]
    zs = [v.co.z for v in comp]
    span = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    nf = len(set(f.index for v in comp for f in v.link_faces))
    info.append(dict(i=i, nv=len(comp), nf=nf,
                     xr=(min(xs), max(xs)), zr=(min(zs), max(zs)), span=span,
                     verts=[v.index for v in comp]))
    print("  part%-3d verts=%-5d faces=%-5d  x[%7.2f,%7.2f] z[%6.2f,%6.2f] span=(%.2f,%.2f,%.2f)"
          % (i, len(comp), nf, min(xs), max(xs), min(zs), max(zs), *span))

body = max(info, key=lambda d: d["nv"])
print("  -> BODY = part%d (verts=%d)" % (body["i"], body["nv"]))
# 좌표는 로컬(신장 ~94유닛). 소총만 왼손 바깥으로 뻗어 있으므로
# "전체가 몸통 왼쪽 바깥(max_x < -25)에 있는 파츠" = 소총. 헬멧·파우치·머리는 |x|<26 이라 보존됨.
z_top = max(d["zr"][1] for d in info)
kill_verts = set()
for d in info:
    if d["i"] == body["i"]:
        continue
    if d["xr"][1] < -25.0:
        print("  -> REMOVE part%d  x[%.1f,%.1f] = 소총" % (d["i"], d["xr"][0], d["xr"][1]))
        kill_verts.update(d["verts"])
    elif d["zr"][1] >= z_top - 0.5 and d["zr"][0] > 80.0:
        print("  -> REMOVE part%d  z[%.1f,%.1f] = 헬멧" % (d["i"], d["zr"][0], d["zr"][1]))
        kill_verts.update(d["verts"])
    else:
        print("  -> keep   part%d  x[%.1f,%.1f] z[%.1f,%.1f]"
              % (d["i"], d["xr"][0], d["xr"][1], d["zr"][0], d["zr"][1]))
print("=" * 70 + "\n")

if kill_verts:
    dead = [v for v in bm.verts if v.index in kill_verts]
    bmesh.ops.delete(bm, geom=dead, context="VERTS")
bm.to_mesh(me)
bm.free()
me.update()

# ---------------------------------------------------------------- 체형 재조형
# 레퍼런스(토이 병사 시트 + 귀멸 소년)는 어깨가 좁고 몸통이 직선 튜브에 가깝다.
# 원본 WW2 병사는 어깨가 벌어진 V자 근육질이라 그대로 쓰면 "헬스인"으로 읽힘.
def reshape_body():
    def E(n, d):
        return float(os.environ.get(n, d))

    SHOULDER = E("SLAYER_SHOULDER", "0.30")   # 어깨 안쪽으로 당기는 비율
    ARM = E("SLAYER_ARM", "0.74")             # 팔 굵기(본 축 주위 반경 스케일)
    CHEST_Y = E("SLAYER_CHESTY", "0.80")      # 가슴 두께(앞뒤)
    TORSO_X = E("SLAYER_TORSOX", "0.90")      # 몸통 폭
    FLARE = E("SLAYER_FLARE", "1.18")         # 하카마 벌어짐
    NECK = E("SLAYER_NECK", "0.88")           # 목 굵기

    vg_name = {g.index: g.name for g in mesh_ob.vertex_groups}
    bones = arm_ob.data.bones
    M = mesh_ob.matrix_world.inverted() @ arm_ob.matrix_world   # 본 좌표 -> 메시 로컬

    # 주의: FBX 임포트된 Biped 는 bone.tail 이 해부학적 방향이 아니다(자동 정렬 안 됨).
    # 관절 위치인 head 만 신뢰하고, 축은 "부모 head -> 자식 head" 로 만든다.
    head = {b.name.lower(): (M @ b.head_local) for b in bones}
    child_head = {}
    for b in bones:
        if b.children:
            child_head[b.name.lower()] = M @ b.children[0].head_local

    def axis_seg(d):
        a = head.get(d)
        if a is None:
            return None
        c = child_head.get(d)
        if c is None:                       # 말단 본은 부모 방향 연장
            c = a + Vector((math.copysign(6.0, a.x), 0, 0))
        return a, c

    def closest_on_seg(p, a, b):
        ab = b - a
        L2 = ab.length_squared
        if L2 < 1e-9:
            return a
        t = max(0.0, min(1.0, (p - a).dot(ab) / L2))
        return a + ab * t

    # 어깨 관절 = UpperArm 의 head (clavicle tail 은 방향이 엉뚱함)
    sh_x = 0.0
    for k, h in head.items():
        if "upperarm" in k:
            sh_x = max(sh_x, abs(h.x))
    if sh_x < 1e-4:
        sh_x = 14.7
    pull = sh_x * SHOULDER
    spine_y = head.get("bip001 spine", Vector((0, 0, 0))).y
    print("reshape: shoulder_x=%.2f pull=%.2f spine_y=%.2f" % (sh_x, pull, spine_y))

    def smoothstep(t):
        t = max(0.0, min(1.0, t))
        return t * t * (3 - 2 * t)

    # 정점별 지배 본
    dom = {}
    for v in me.vertices:
        best, bw = None, -1.0
        for g in v.groups:
            if g.weight > bw:
                bw, best = g.weight, vg_name.get(g.group, "")
        dom[v.index] = (best or "").lower()

    z_hip = None
    for b in bones:
        if "pelvis" in b.name.lower():
            z_hip = (M @ b.head_local).z
    if z_hip is None:
        z_hip = 45.0

    for v in me.vertices:
        d = dom[v.index]
        x, y, z = v.co.x, v.co.y, v.co.z

        # 1) 어깨/팔 안쪽으로: |x| 에 따라 부드럽게 램프 (이음매 없이 어깨가 좁아짐)
        #    상체 부위에만 적용한다. 다리에 걸리면 두 다리가 붙어버린다.
        if any(k in d for k in ("clavicle", "upperarm", "forearm", "hand",
                                "spine", "neck", "head")):
            s = smoothstep(abs(x) / sh_x)
            if x >= 0:
                v.co.x -= pull * s
            else:
                v.co.x += pull * s

        # 2) 팔 가늘게: 관절-관절 축 주위로 반경 축소
        if any(k in d for k in ("upperarm", "forearm", "clavicle")):
            seg = axis_seg(d)
            if seg:
                p = closest_on_seg(v.co, seg[0], seg[1])
                v.co = p + (v.co - p) * ARM

        # 3) 몸통: 폭 줄이고 가슴 두께 줄이기(직선 튜브에 가깝게)
        if "spine" in d:
            v.co.x *= TORSO_X
            v.co.y = spine_y + (v.co.y - spine_y) * CHEST_Y
        if "neck" in d:
            v.co.x *= NECK
            v.co.y = spine_y + (v.co.y - spine_y) * NECK

        # 4) 하카마: 골반 관절 "아래"만 벌린다.
        #    벨트·탄약 파우치는 골반 위라 여기 걸리면 날개처럼 튀어나온다.
        if ("pelvis" in d or "thigh" in d) and v.co.z < z_hip:
            t = smoothstep((z_hip - v.co.z) / max(1.0, z_hip * 0.60))
            f = 1.0 + (FLARE - 1.0) * (1.0 - t)     # 골반 바로 아래가 제일 넓고 아래로 갈수록 좁아짐
            v.co.x *= f
            v.co.y *= f

    me.update()


# 오너 지시(0731): 체형 변형 되돌림. 필요할 때만 RESHAPE=1 로 켠다.
if os.environ.get("RESHAPE", "0") == "1":
    reshape_body()
else:
    print("reshape: OFF (원본 체형 유지)")

# ---------------------------------------------------------------- 리페인트 텍스처 적용
img = bpy.data.images.load(NEWTEX)
mat = bpy.data.materials.new("slayer_tex")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
nt.links.new(tex.outputs[0], diff.inputs[0])
nt.links.new(diff.outputs[0], out.inputs[0])
me.materials.clear()
me.materials.append(mat)

# ---------------------------------------------------------------- 포즈: 동봉 애니메이션 재사용
ANIM = os.environ.get("SLAYER_ANIM", "infantry_guard_idle")
FRAME = int(os.environ.get("SLAYER_FRAME", "1"))
anim_path = os.path.join(PACK, "animation/%s.FBX" % ANIM)
before = set(o.name for o in sc.objects)
bpy.ops.import_scene.fbx(filepath=anim_path)
new_objs = [o for o in sc.objects if o.name not in before]
action = None
for o in new_objs:
    if o.type == "ARMATURE" and o.animation_data and o.animation_data.action:
        action = o.animation_data.action
        break
if action:
    if not arm_ob.animation_data:
        arm_ob.animation_data_create()
    arm_ob.animation_data.action = action
    # Blender 4.4+ 슬롯형 액션: 슬롯을 지정하지 않으면 아무것도 적용되지 않는다
    try:
        slots = list(getattr(action, "slots", []))
        if slots:
            arm_ob.animation_data.action_slot = slots[0]
            print("action_slot = %s" % slots[0].identifier)
    except Exception as e:
        print("slot assign fail:", e)
    fr = action.frame_range
    print("applied action '%s' range=%s frame=%d" % (action.name, tuple(fr), FRAME))
    sc.frame_set(FRAME)
    bpy.context.view_layer.update()
    for probe in ("R UpperArm", "L UpperArm"):
        for b in arm_ob.pose.bones:
            if probe.lower() in b.name.lower():
                q = b.rotation_quaternion
                print("  pose check %-12s quat=(%.3f, %.3f, %.3f, %.3f)"
                      % (probe, q.w, q.x, q.y, q.z))
                break
else:
    print("! no action found in", anim_path)
for o in new_objs:                      # 애니메이션용 임시 오브젝트 정리
    bpy.data.objects.remove(o, do_unlink=True)
# 액션을 붙여두면 depsgraph 평가마다 포즈를 덮어써서 수동 포즈가 무효화된다.
# 이 팩의 액션은 회전 커브가 사실상 0(포즈가 rest 에 구워짐)이라 얻을 게 없으므로 해제한다.
if arm_ob.animation_data:
    arm_ob.animation_data.action = None
    arm_ob.animation_data_clear()
    print("action cleared (수동 포즈 사용)")
bpy.context.view_layer.update()

# ---- 월드 축 기준 본 스윙(본 로컬 축 추측을 피한다) ----
# 동봉 애니메이션은 회전 커브가 거의 0이라(포즈가 rest 에 구워져 있음) 직접 포즈를 잡는다.
A2W = arm_ob.matrix_world
W2A = A2W.inverted()


def find_bone(key):
    for b in arm_ob.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


def swing(key, axis_world, deg):
    """본의 head 를 중심으로 월드 axis 둘레로 deg 만큼 회전."""
    b = find_bone(key)
    if b is None:
        print("  ! bone not found:", key)
        return
    ax = (W2A.to_3x3() @ Vector(axis_world)).normalized()
    head = b.matrix.translation.copy()
    R = Matrix.Rotation(math.radians(deg), 4, ax)
    b.matrix = Matrix.Translation(head) @ R @ Matrix.Translation(-head) @ b.matrix
    bpy.context.view_layer.update()


def E(name, default):
    return float(os.environ.get(name, default))


# 팔 내리기: 월드 Y축 둘레로 스윙하면 X 방향 팔이 아래로 내려간다
swing("l upperarm", (0, 1, 0), E("SLAYER_LUA", "-72"))
swing("l forearm", (0, 1, 0), E("SLAYER_LFA", "-12"))
swing("r upperarm", (0, 1, 0), E("SLAYER_RUA", "72"))
swing("r forearm", (0, 1, 0), E("SLAYER_RFA", "40"))
swing("r forearm", (1, 0, 0), E("SLAYER_RFA2", "-25"))
bpy.context.view_layer.update()

# ---------------------------------------------------------------- 카타나 부착
bpy.context.view_layer.update()
hand_bone_name = None
for b in arm_ob.pose.bones:
    if "r hand" in b.name.lower():
        hand_bone_name = b.name
        break
print("hand bone:", hand_bone_name)

# 캐릭터 스케일에 맞춰 검 크기 결정 (신장 대비)
zs = [(mesh_ob.matrix_world @ v.co).z for v in me.vertices]
height = max(zs) - min(zs)
sword_scale = height * float(os.environ.get("KATANA_SCALE", "0.56"))
katana = BS.build_katana(tag="slayer", scale=sword_scale,
                         width_mul=float(os.environ.get("KATANA_W", "2.8")))
if hand_bone_name:
    hb = arm_ob.pose.bones[hand_bone_name]
    M = arm_ob.matrix_world @ hb.matrix
    loc, rotq, _scl = M.decompose()
    M_norm = Matrix.Translation(loc) @ rotq.to_matrix().to_4x4()

    # 그립 위치 = 손 정점(변형된 메시)의 실제 중심.
    # 본 head 는 손목 관절이라 거기 붙이면 "손목에 칼이 달린" 그림이 된다.
    dgx = bpy.context.evaluated_depsgraph_get()
    evx = mesh_ob.evaluated_get(dgx)
    me_ev = evx.to_mesh()
    vgn = {g.index: g.name for g in mesh_ob.vertex_groups}
    hidx = []
    for v in mesh_ob.data.vertices:
        best, bw = None, -1
        for g in v.groups:
            if g.weight > bw:
                bw, best = g.weight, vgn.get(g.group, "")
        if best and "r hand" in best.lower():
            hidx.append(v.index)
    if hidx:
        pw = [evx.matrix_world @ me_ev.vertices[i].co for i in hidx]
        palm = sum(pw, Vector((0, 0, 0))) / len(pw)
    else:
        palm = loc
    evx.to_mesh_clear()
    palm_local = M_norm.inverted() @ palm
    print("grip: palm_local=%s (hand verts=%d)"
          % (tuple(round(v, 4) for v in palm_local), len(hidx)))

    # 칼 로컬 +X(칼끝)를 손 본 로컬 -Y 로 정렬.
    # 6축 실측 비교 결과 -Y 만 주먹에서 앞으로 뻗고 몸을 관통하지 않는다.
    q = Vector((1, 0, 0)).rotation_difference(Vector((0, -1, 0)))
    tilt = Matrix.Rotation(math.radians(float(os.environ.get("KAT_TILT", "22"))), 4, "Z")
    roll = Matrix.Rotation(math.radians(float(os.environ.get("KAT_ROLL", "0"))), 4, "X")
    # ★칼 원점(자루 상단 근처)을 손바닥에 그대로 놓으면 **츠바·칼날이 주먹 안에서
    # 시작해 손등을 뚫고 나온다**(실측: 칼날 시작이 손목에서 0.116, 주먹 반경 안).
    # 칼을 로컬 +X(칼끝 쪽)로 밀어 손이 자루를 더 아래쪽에서 쥐게 한다.
    shift = Matrix.Translation((float(os.environ.get("KAT_SHIFT", "0.075")) * sword_scale, 0, 0))
    off = Matrix.Translation(palm_local) @ q.to_matrix().to_4x4() @ tilt @ roll @ shift
    katana.matrix_world = M_norm @ off
    con = katana.constraints.new("CHILD_OF")
    con.target = arm_ob
    con.subtarget = hand_bone_name
    con.inverse_matrix = M.inverted()
bpy.context.view_layer.update()

# ---------------------------------------------------------------- 머리카락 (헬멧 자리)
head_bone_name = None
for b in arm_ob.pose.bones:
    if b.name.lower().endswith("head"):
        head_bone_name = b.name
        break
print("head bone:", head_bone_name)

# 머리 본이 지배하는 정점의 월드 바운즈로 크기 산출
hgi = None
for g in mesh_ob.vertex_groups:
    if g.name == head_bone_name:
        hgi = g.index
        break
hv = []
if hgi is not None:
    for v in me.vertices:
        dom, dw = None, -1
        for g in v.groups:
            if g.weight > dw:
                dw, dom = g.weight, g.group
        if dom == hgi:
            hv.append(mesh_ob.matrix_world @ v.co)
if hv:
    hlo = Vector((min(p.x for p in hv), min(p.y for p in hv), min(p.z for p in hv)))
    hhi = Vector((max(p.x for p in hv), max(p.y for p in hv), max(p.z for p in hv)))
    hctr = (hlo + hhi) / 2
    hsz = hhi - hlo
    print("head bounds size=(%.3f, %.3f, %.3f) ctr=(%.3f, %.3f, %.3f)" % (*hsz, *hctr))

    m_hair = BS.cel_mat("hair_slayer", "#3a2432", ramp_pos=0.34, shadow_mul=0.55, soft=0.26)

    # 스컬 캡: 구를 머리 크기에 맞춘 뒤 아래·앞면을 잘라낸다
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=22, radius=1.0,
                                         location=(0, 0, 0))
    cap = bpy.context.object
    cap.name = "hair_cap"
    cme = cap.data
    bmh = bmesh.new()
    bmh.from_mesh(cme)
    kill = [v for v in bmh.verts if v.co.z < -0.30 or (v.co.y < -0.34 and v.co.z < 0.30)]
    bmesh.ops.delete(bmh, geom=kill, context="VERTS")
    bmh.to_mesh(cme)
    bmh.free()
    for v in cme.vertices:
        v.co.x *= hsz.x * 0.56
        v.co.y *= hsz.y * 0.58
        v.co.z *= hsz.z * 0.52
    for p in cme.polygons:
        p.use_smooth = True
    cme.materials.append(m_hair)
    cap.location = (hctr.x, hctr.y + hsz.y * 0.02, hctr.z + hsz.z * 0.20)

    hair_objs = [cap]
    # 짧은 갈래(앞머리 + 뒤쪽 뻗침)
    import random as _rnd
    rng = _rnd.Random(4)
    for i in range(9):
        t = (i / 8.0) - 0.5
        front = i < 5
        ln = hsz.z * (0.34 if front else 0.30) * (0.85 + rng.random() * 0.4)
        p0 = (t * hsz.x * 0.62,
              (-hsz.y * 0.30 if front else hsz.y * 0.36),
              hctr.z + hsz.z * (0.44 if front else 0.40))
        p1 = (t * hsz.x * 0.80,
              (-hsz.y * 0.50 if front else hsz.y * 0.52),
              hctr.z + hsz.z * (0.20 if front else 0.16))
        p2 = (t * hsz.x * 0.86,
              (-hsz.y * 0.52 if front else hsz.y * 0.56),
              hctr.z + hsz.z * (0.20 if front else 0.16) - ln)
        lk = BS.hair_lock("hl%d" % i, [(p0[0], p0[1], p0[2]),
                                       (p1[0], p1[1], p1[2]),
                                       (p2[0], p2[1], p2[2])],
                          [1.0, 0.7, 0.0], m_hair, hsz.x * 0.075)
        lk.location.x += hctr.x
        hair_objs.append(lk)

    # 머리 본에 부착
    if head_bone_name:
        hb2 = arm_ob.pose.bones[head_bone_name]
        M2 = arm_ob.matrix_world @ hb2.matrix
        for ob in hair_objs:
            mw = ob.matrix_world.copy()
            c2 = ob.constraints.new("CHILD_OF")
            c2.target = arm_ob
            c2.subtarget = head_bone_name
            c2.inverse_matrix = M2.inverted()
            ob.matrix_world = mw
bpy.context.view_layer.update()

# ---------------------------------------------------------------- 조명/카메라/렌더
lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for v in me.vertices:
    wc = mesh_ob.matrix_world @ v.co
    for i in range(3):
        lo[i] = min(lo[i], wc[i])
        hi[i] = max(hi[i], wc[i])
ctr = (hi + lo) / 2
H = hi.z - lo.z
print("char height=%.3f" % H)

bpy.ops.mesh.primitive_plane_add(size=H * 14, location=(ctr.x, ctr.y, lo.z - 0.002))
fl = bpy.context.object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fnt = fm.node_tree
fnt.nodes.clear()
fo = fnt.nodes.new("ShaderNodeOutputMaterial")
fe = fnt.nodes.new("ShaderNodeEmission")
fe.inputs[0].default_value = (0.035, 0.04, 0.055, 1)
fnt.links.new(fe.outputs[0], fo.inputs[0])
fl.data.materials.append(fm)

li = bpy.data.lights.new("Sun", "SUN")
li.energy = 3.4
so = bpy.data.objects.new("Sun", li)
so.rotation_euler = (math.radians(55), 0, math.radians(-22))
sc.collection.objects.link(so)
for nm, off, en, col in (("rim", (-3.0, 3.0, 3.0), 500, (0.6, 0.82, 1.0)),
                         ("fill", (3.0, -3.2, 2.0), 260, (1, 1, 1)),
                         ("back", (0.5, 4.0, 2.0), 180, (0.8, 0.85, 1.0))):
    al = bpy.data.lights.new(nm, "AREA")
    al.energy = en
    al.size = H * 2
    al.color = col
    ao = bpy.data.objects.new(nm, al)
    ao.location = (ctr.x + off[0] * H * 0.5, ctr.y + off[1] * H * 0.5, lo.z + off[2] * H * 0.5)
    sc.collection.objects.link(ao)
    d = Vector(ctr) - ao.location
    ao.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

camd = bpy.data.cameras.new("Cam")
camd.lens = 60
cam = bpy.data.objects.new("Cam", camd)
sc.collection.objects.link(cam)
sc.camera = cam

# 블룸
try:
    ng = bpy.data.node_groups.new("Compositing", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    sc.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers")
    gl = ng.nodes.new("CompositorNodeGlare")
    for k, v in (("Type", "Bloom"), ("Quality", "High"), ("Threshold", 1.5), ("Strength", 0.3)):
        try:
            gl.inputs[k].default_value = v
        except Exception:
            pass
    gout = ng.nodes.new("NodeGroupOutput")
    ng.links.new(rl.outputs[0], gl.inputs[0])
    ng.links.new(gl.outputs[0], gout.inputs[0])
except Exception as e:
    print("glare skip", e)


def shoot(name, ang_deg, dist=2.5, zmul=0.10, x=1000, y=1300, lens=60):
    a = math.radians(ang_deg)
    d = H * dist
    camd.lens = lens
    cam.location = (ctr.x + math.sin(a) * d, ctr.y - math.cos(a) * d, ctr.z + H * zmul)
    v = Vector(ctr) - cam.location
    cam.rotation_euler = v.to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = x
    sc.render.resolution_y = y
    p = os.path.join(REN, name)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    try:
        shutil.copy2(p, os.path.join(HIST, "%s_%s" % (RUN, name)))
    except Exception as e:
        print("hist fail", e)


shoot("07_slayer_front.png", 0)
shoot("07_slayer_34.png", 32)
shoot("07_slayer_side.png", 90)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
print("DONE")
