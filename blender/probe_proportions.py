# -*- coding: utf-8 -*-
"""캐릭터 신체 비율을 뼈 단위로 재서 사람 표준과 비교한다.

배경
  오너가 "T포즈 렌더에서 팔이 너무 길어 보인다"고 지적했다. 렌더 자체에는
  왜곡이 없음이 확인됐다(픽셀 폭/키 1.147 이 3D 실측과 소수 셋째 자리까지 일치).
  남은 건 모델의 비율이 실제로 이상한지, 이상하다면 어디가 문제인지다.

실행
  blender -b -P blender/probe_proportions.py                  # 기본: 병사 원본 FBX
  SRC=glb GLB=web/soldier.glb blender -b -P blender/probe_proportions.py
  GLB=web/slayer.glb SRC=glb blender -b -P blender/probe_proportions.py

환경변수
  SRC   fbx(기본) | glb        측정 대상 소스
  GLB   web/soldier.glb        SRC=glb 일 때 파일 경로(ROOT 상대 또는 절대)
  FBX   (기본값 = 병사 원본)     SRC=fbx 일 때 파일 경로

★함정 (이 프로젝트에서 실제로 당한 것들)
  1. glTF 임포터가 반지름 1짜리 Icosphere 를 씬에 만든다. glb 안에는 없다.
     z -1..1 이라 같이 재면 키가 통째로 틀어진다(발 속도 측정이 0.63배로 깎였다).
     -> 스킨 모디파이어가 없고 부모도 없는 메시는 전부 버린다.
  2. 무기를 키·폭에 포함하면 안 된다. 검사는 SW_ 칼 7자루, 탱커는 SH_scutum
     방패가 별도 오브젝트다. 병사는 소총이 몸 메시에 스킨된 채 합쳐져 있어
     오브젝트 이름으로 못 거른다 -> 루즈 아일랜드 + 웨이트로 판별한다.
  3. 아마추어 스케일이 1이 아니다(병사·검사 0.0254, 탱커·궁수·기본 0.01).
     뼈 좌표는 반드시 아마추어 월드 변환을 곱해야 실제 길이가 나온다.
  4. 레스트 포즈로 재야 한다. 애니메이션이 붙은 채 재면 그 프레임 자세가 섞인다.
  5. bone.length 를 믿으면 안 된다. glTF 는 뼈 길이를 저장하지 않아 임포터가
     임의로 정한다(병사에서 원본 FBX 대비 39.37배 차이가 났다).
     반드시 **머리 좌표 사이 거리**로 잰다.
  6. 부분 문자열 검색 주의. Meshy 리그는 Spine/Chest/Chest2 가 있어
     "spine" 부분일치가 엉뚱한 뼈를 잡는다 -> 접미 일치 + 중복 검출로 막는다.
"""
import bpy
import os
import math
from collections import defaultdict
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
SRC = os.environ.get("SRC", "fbx").lower()
FBX = os.environ.get("FBX", os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX"))
GLB = os.environ.get("GLB", "web/soldier.glb")


def abspath(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


# ====================================================================== 임포트
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
if SRC == "fbx":
    SRCPATH = abspath(FBX)
    bpy.ops.import_scene.fbx(filepath=SRCPATH)
else:
    SRCPATH = abspath(GLB)
    bpy.ops.import_scene.gltf(filepath=SRCPATH)

print("\n" + "=" * 78)
print("소스: %s  (%s)" % (os.path.basename(SRCPATH), SRC.upper()))
print("=" * 78)

# ★함정 4 - 레스트 포즈 고정. 딸려온 액션을 전부 지우고 아마추어를 REST 로.
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
arm.animation_data_clear()
arm.data.pose_position = "REST"
for b in arm.pose.bones:
    b.location = (0, 0, 0)
    b.rotation_quaternion = (1, 0, 0, 0)
    b.rotation_euler = (0, 0, 0)
    b.scale = (1, 1, 1)
bpy.context.view_layer.update()

A2W = arm.matrix_world.copy()                      # ★함정 3 - 아마추어 월드 변환
ASCALE = A2W.to_scale()[0]
print("아마추어 '%s'  뼈 %d개  월드 스케일 %.6f"
      % (arm.name, len(arm.data.bones), ASCALE))

# ====================================================================== 메시 선별
# ★함정 1 - Icosphere 배제. 아마추어에 붙지 않은 메시는 캐릭터가 아니다.
# ★함정 2 - 무기 오브젝트(SW_/SH_/WP_) 배제.
WEAPON_PREFIX = ("SW_", "SH_", "WP_")
body_objs, dropped = [], []
for o in sc.objects:
    if o.type != "MESH":
        continue
    skinned = any(m.type == "ARMATURE" for m in o.modifiers) or o.parent is arm
    if not skinned:
        dropped.append((o.name, "스킨 없음(Icosphere 등)"))
    elif o.name.startswith(WEAPON_PREFIX):
        dropped.append((o.name, "무기 오브젝트"))
    else:
        body_objs.append(o)
for n, why in dropped:
    print("  [제외] %-28s %s" % (n, why))
assert len(body_objs) == 1, "몸 메시가 1개가 아니다: %s" % [o.name for o in body_objs]
mesh = body_objs[0]
me = mesh.data
MW = mesh.matrix_world.copy()
print("  [몸] %s  정점 %d  삼각형 %d"
      % (mesh.name, len(me.vertices),
         sum(len(p.vertices) - 2 for p in me.polygons)))

# ====================================================================== 루즈 아일랜드
# ★함정 2 - 병사는 소총이 몸 메시 안에 스킨된 채 들어 있다. bbox 로는 못 거른다.
# 폴리곤 연결 성분(union-find)으로 조각을 나눈 뒤 웨이트로 이름을 붙인다.
nv = len(me.vertices)
parent = list(range(nv))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for e in me.edges:
    ra, rb = find(e.vertices[0]), find(e.vertices[1])
    if ra != rb:
        parent[rb] = ra
groups = defaultdict(list)
for i in range(nv):
    groups[find(i)].append(i)
islands = sorted(groups.values(), key=lambda vs: -len(vs))   # 0번 = 가장 큰 = 몸
vg = [g.name for g in mesh.vertex_groups]
isl_of = {v: k for k, vs in enumerate(islands) for v in vs}
isl_tri = defaultdict(int)
for p in me.polygons:
    isl_tri[isl_of[p.vertices[0]]] += len(p.vertices) - 2


def sole_bone(vi):
    """이 정점이 뼈 하나에만 100% 로 묶였으면 그 뼈 이름, 아니면 None"""
    gs = [(vg[g.group], g.weight) for g in me.vertices[vi].groups if g.weight > 1e-4]
    return gs[0][0] if len(gs) == 1 and gs[0][1] > 0.999 else None


def top_bone(vs):
    w = defaultdict(float)
    for v in vs:
        for g in me.vertices[v].groups:
            w[vg[g.group]] += g.weight
    return max(w.items(), key=lambda kv: kv[1])[0] if w else "?"


# ★함정: 웨이트만 보면 몸의 손목·손등(R Hand 단독 100%)이 소총으로 잡혀 손이 뜯긴다.
# 가장 큰 아일랜드를 먼저 "몸"으로 확정하고, 나머지에만 규칙을 적용한다.
LABEL = {}
for k, vs in enumerate(islands):
    if k == 0:
        LABEL[k] = "body"
    elif all((sole_bone(v) or "").endswith("R Hand") for v in vs):
        LABEL[k] = "rifle"
    elif all((sole_bone(v) or "").endswith("Head") for v in vs):
        LABEL[k] = "helmet"
    else:
        LABEL[k] = "pouch" if top_bone(vs).endswith("Pelvis") else "pack"

print("\n조각 분류 (아일랜드 %d개)" % len(islands))
agg = defaultdict(lambda: [0, 0, 0])
for k, vs in enumerate(islands):
    st = agg[LABEL[k]]
    st[0] += 1
    st[1] += len(vs)
    st[2] += isl_tri[k]
for nm in ("body", "helmet", "pack", "pouch", "rifle"):
    if nm in agg:
        c, v, t = agg[nm]
        print("  %-7s 조각 %-2d 정점 %-5d 삼각형 %-5d" % (nm, c, v, t))

VSET = {nm: set(v for k, vs in enumerate(islands) if LABEL[k] == nm for v in vs)
        for nm in agg}
CO = [MW @ v.co for v in me.vertices]              # 바인드(레스트) 지오메트리


def bbox(vset):
    c = [CO[v] for v in vset]
    if not c:
        return None
    return (min(x.x for x in c), max(x.x for x in c),
            min(x.y for x in c), max(x.y for x in c),
            min(x.z for x in c), max(x.z for x in c))


# ====================================================================== 뼈 조회
BONES = {b.name: b for b in arm.data.bones}
PB = {b.name: b for b in arm.pose.bones}


def bone(*cands):
    """접미 일치로 뼈를 찾는다. ★함정 6 - 부분 문자열 검색 금지, 중복이면 실패."""
    low = {n.lower(): n for n in BONES}
    for c in cands:
        cl = c.lower()
        if cl in low:
            return BONES[low[cl]]
        hits = [n for n in BONES if n.lower().endswith(cl)]
        if len(hits) == 1:
            return BONES[hits[0]]
        if len(hits) > 1:
            raise SystemExit("뼈 이름 모호 '%s' -> %s" % (c, hits))
    return None


def head(b):
    """뼈 머리의 월드 좌표. ★함정 5 - bone.length 대신 머리 좌표로만 잰다."""
    return A2W @ b.head_local


def head_pose(name):
    """pose_bone.matrix 경로(레스트 상태). head_local 경로와 대조용."""
    return A2W @ PB[name].matrix.translation


def dist(a, b):
    return (a - b).length


# 레스트 좌표 두 경로 교차검증 (지시받은 A2W @ pb.matrix 와 A2W @ head_local)
worst = max(dist(head(BONES[n]), head_pose(n)) for n in BONES)
print("\n레스트 좌표 두 경로 최대 오차: %.6g  (head_local vs pose.matrix)" % worst)

L = {}
for side in ("L", "R"):
    L[side] = {
        "clav": bone("%s Clavicle" % side),
        "upper": bone("%s UpperArm" % side),
        "fore": bone("%s Forearm" % side),
        "hand": bone("%s Hand" % side),
        "thigh": bone("%s Thigh" % side),
        "calf": bone("%s Calf" % side),
        "foot": bone("%s Foot" % side),
        "toe": bone("%s Toe0" % side),
    }
PELVIS = bone("Pelvis")
SPINE = bone("Spine")
NECK = bone("Neck")
HEAD = bone("Head")

# ====================================================================== 정점 귀속
# 뼈별 지배 정점(몸 조각 한정). 손끝·발바닥·머리 크기를 재는 데 쓴다.
BODY = VSET["body"]
dom = defaultdict(set)
for v in BODY:
    gs = [(vg[g.group], g.weight) for g in me.vertices[v].groups if g.weight > 1e-4]
    if gs:
        dom[max(gs, key=lambda kv: kv[1])[0]].add(v)


def dom_verts(*bones_):
    s = set()
    for b in bones_:
        if b is not None:
            s |= dom.get(b.name, set())
    return s


# ====================================================================== 치수
BB_BODY = bbox(VSET["body"])
BB_HELM = bbox(VSET["body"] | VSET.get("helmet", set()))
BB_ALL = bbox(set(range(nv)))

H_BARE = BB_BODY[5] - BB_BODY[4]                   # 헬멧 제외 키
H_HELM = BB_HELM[5] - BB_HELM[4]                   # 헬멧 포함 키
W_BARE = BB_BODY[1] - BB_BODY[0]                   # 팔 벌린 폭(장비 제외)
W_ALL = BB_ALL[1] - BB_ALL[0]

print("\n" + "-" * 78)
print("[1~2] 메시 bbox")
print("-" * 78)
print("  몸만(장비 전부 제외)  키 %.4f  폭 %.4f  두께 %.4f   폭/키 %.4f"
      % (H_BARE, W_BARE, BB_BODY[3] - BB_BODY[2], W_BARE / H_BARE))
print("      x %.4f..%.4f   z %.4f..%.4f" % (BB_BODY[0], BB_BODY[1], BB_BODY[4], BB_BODY[5]))
print("  몸+헬멧               키 %.4f  폭 %.4f              폭/키 %.4f"
      % (H_HELM, BB_HELM[1] - BB_HELM[0], (BB_HELM[1] - BB_HELM[0]) / H_HELM))
print("  전체(소총·장비 포함)   키 %.4f  폭 %.4f              폭/키 %.4f"
      % (BB_ALL[5] - BB_ALL[4], W_ALL, W_ALL / (BB_ALL[5] - BB_ALL[4])))

# ---------------------------------------------------------------- 팔
print("\n" + "-" * 78)
print("[3~7] 팔  (머리 좌표 사이 거리 / 괄호는 x축 투영량)")
print("-" * 78)
SHW = dist(head(L["L"]["upper"]), head(L["R"]["upper"]))
SHW_X = abs(head(L["L"]["upper"]).x - head(L["R"]["upper"]).x)
print("  어깨너비(L/R UpperArm 머리 간)  %.4f   (x축 %.4f)" % (SHW, SHW_X))
print("  어깨 z = %.4f / %.4f" % (head(L["L"]["upper"]).z, head(L["R"]["upper"]).z))

ARM = {}
for side in ("L", "R"):
    s = L[side]
    hu, hf, hh = head(s["upper"]), head(s["fore"]), head(s["hand"])
    upper, fore = dist(hu, hf), dist(hf, hh)
    hv = dom_verts(s["hand"])
    # 손끝: 손 뼈 머리에서 가장 먼 손 정점(몸 조각 한정 -> 소총 정점이 안 섞인다)
    if hv:
        tip = max((CO[v] for v in hv), key=lambda c: (c - hh).length)
        hand_len = dist(hh, tip)
    else:
        tip, hand_len = hh, 0.0
    total = dist(hu, tip)
    ARM[side] = dict(upper=upper, fore=fore, hand=hand_len, total=total,
                     hu=hu, hf=hf, hh=hh, tip=tip, nv=len(hv))
    print("  %s: 위팔 %.4f (x %.4f)  팔뚝 %.4f (x %.4f)  손 %.4f (x %.4f)  손끝까지 %.4f (x %.4f)"
          % (side, upper, abs(hf.x - hu.x), fore, abs(hh.x - hf.x),
             hand_len, abs(tip.x - hh.x), total, abs(tip.x - hu.x)))
    print("      손 정점 %d개, 손끝 좌표 (%.4f, %.4f, %.4f)"
          % (len(hv), tip.x, tip.y, tip.z))

# ---------------------------------------------------------------- 다리
print("\n" + "-" * 78)
print("[8] 다리")
print("-" * 78)
LEG = {}
for side in ("L", "R"):
    s = L[side]
    ht, hc, hf2 = head(s["thigh"]), head(s["calf"]), head(s["foot"])
    fv = dom_verts(s["foot"], s["toe"])
    sole = min((CO[v].z for v in fv), default=BB_BODY[4])
    thigh, calf = dist(ht, hc), dist(hc, hf2)
    leg_z = ht.z - sole                            # 다리 전체는 수직 높이로 잰다
    leg_chain = thigh + calf + (hf2.z - sole)
    LEG[side] = dict(thigh=thigh, calf=calf, leg_z=leg_z, chain=leg_chain,
                     ht=ht, sole=sole)
    print("  %s: 허벅지 %.4f  종아리 %.4f  발목높이 %.4f  다리전체(수직) %.4f  체인합 %.4f"
          % (side, thigh, calf, hf2.z - sole, leg_z, leg_chain))
    print("      Thigh 머리 z %.4f  발바닥 z %.4f  (발 정점 %d개)" % (ht.z, sole, len(fv)))

# ---------------------------------------------------------------- 몸통·머리
print("\n" + "-" * 78)
print("[9~10] 몸통 · 머리")
print("-" * 78)
Z0 = BB_BODY[4]                                    # 바닥(몸 bbox 최저점)
print("  바닥 z = %.4f" % Z0)
for nm, b in (("Pelvis", PELVIS), ("Spine", SPINE), ("Neck", NECK), ("Head", HEAD)):
    if b:
        print("  %-7s 머리 높이 %.4f  (키의 %5.1f%% / 헬멧포함 %5.1f%%)"
              % (nm, head(b).z - Z0, 100 * (head(b).z - Z0) / H_BARE,
                 100 * (head(b).z - Z0) / H_HELM))

hverts = dom_verts(HEAD)
hz = [CO[v].z for v in hverts]
CROWN = max(hz)                                    # 정수리(맨머리)
CHIN = min(hz)                                     # Head 뼈 지배 정점의 최저점 = 턱 밑
HEADJ = head(HEAD).z                               # Head 뼈 관절 = 머리 시작
NECKJ = head(NECK).z
helm_z = [CO[v].z for v in VSET.get("helmet", set())]
CROWN_H = max(helm_z) if helm_z else CROWN

print("  머리 정점 %d개   정수리 z %.4f   턱밑 z %.4f   Head 관절 z %.4f   Neck 관절 z %.4f"
      % (len(hverts), CROWN, CHIN, HEADJ, NECKJ))
if helm_z:
    print("  헬멧 정점 %d개   헬멧 꼭대기 z %.4f" % (len(helm_z), CROWN_H))

HH_CHIN = CROWN - CHIN                             # 턱밑~정수리 (미술 표준 1등신)
HH_JOINT = CROWN - HEADJ                           # Head 관절~정수리
HH_NECK = CROWN - NECKJ                            # Neck 관절~정수리
print("\n  머리 높이 정의별")
print("    (a) 턱밑~정수리      %.4f" % HH_CHIN)
print("    (b) Head 관절~정수리  %.4f" % HH_JOINT)
print("    (c) Neck 관절~정수리  %.4f" % HH_NECK)
print("  등신 수 (키 / 머리 높이)")
print("    맨머리 키 %.4f : (a) %.2f등신   (b) %.2f등신   (c) %.2f등신"
      % (H_BARE, H_BARE / HH_CHIN, H_BARE / HH_JOINT, H_BARE / HH_NECK))
if helm_z:
    HH_CHIN_H = CROWN_H - CHIN
    print("    헬멧포함 키 %.4f : (a') 턱밑~헬멧꼭대기 %.4f -> %.2f등신"
          % (H_HELM, HH_CHIN_H, H_HELM / HH_CHIN_H))

# ====================================================================== 표준 대비
print("\n" + "=" * 78)
print("사람 표준 대비 (키로 정규화). 기준 키를 두 가지로 낸다.")
print("=" * 78)
STD = [("팔 벌린 폭", W_BARE, 1.000),
       ("어깨너비", SHW, 0.230),
       ("위팔", (ARM["L"]["upper"] + ARM["R"]["upper"]) / 2, 0.186),
       ("팔뚝", (ARM["L"]["fore"] + ARM["R"]["fore"]) / 2, 0.146),
       ("손", (ARM["L"]["hand"] + ARM["R"]["hand"]) / 2, 0.108),
       ("어깨~손끝", (ARM["L"]["total"] + ARM["R"]["total"]) / 2, 0.440),
       ("다리 전체", (LEG["L"]["leg_z"] + LEG["R"]["leg_z"]) / 2, 0.470),
       ("허벅지", (LEG["L"]["thigh"] + LEG["R"]["thigh"]) / 2, 0.245),
       ("종아리", (LEG["L"]["calf"] + LEG["R"]["calf"]) / 2, 0.246),
       ("골반 높이", head(PELVIS).z - Z0, 0.530),
       ("어깨 높이", head(L["L"]["upper"]).z - Z0, 0.818),
       ("머리 높이(턱밑~정수리)", HH_CHIN, 0.133)]
print("  %-22s %8s %8s %8s %9s %9s"
      % ("항목", "실측", "맨머리%", "헬멧%", "표준%", "표준대비"))
for nm, val, std in STD:
    r1, r2 = val / H_BARE, val / H_HELM
    print("  %-22s %8.4f %7.1f%% %7.1f%% %8.1f%% %8.2f배"
          % (nm, val, 100 * r1, 100 * r2, 100 * std, r1 / std))

# ====================================================================== 폭 분해
print("\n" + "=" * 78)
print("★ 폭/키 분해:  팔 벌린 폭 = 어깨너비 + 2 x (위팔 + 팔뚝 + 손)")
print("=" * 78)
uA = (ARM["L"]["upper"] + ARM["R"]["upper"]) / 2
fA = (ARM["L"]["fore"] + ARM["R"]["fore"]) / 2
hA = (ARM["L"]["hand"] + ARM["R"]["hand"]) / 2
recon = SHW + 2 * (uA + fA + hA)
# x축 투영판(팔이 완전히 수평이 아니면 이쪽이 실제 폭에 더 가깝다)
uX = (abs(ARM["L"]["hf"].x - ARM["L"]["hu"].x) + abs(ARM["R"]["hf"].x - ARM["R"]["hu"].x)) / 2
fX = (abs(ARM["L"]["hh"].x - ARM["L"]["hf"].x) + abs(ARM["R"]["hh"].x - ARM["R"]["hf"].x)) / 2
hX = (abs(ARM["L"]["tip"].x - ARM["L"]["hh"].x) + abs(ARM["R"]["tip"].x - ARM["R"]["hh"].x)) / 2
recon_x = SHW_X + 2 * (uX + fX + hX)
for tag, hgt in (("맨머리 키 %.4f" % H_BARE, H_BARE), ("헬멧포함 키 %.4f" % H_HELM, H_HELM)):
    print("\n  [%s]" % tag)
    print("    %-14s %8s %9s %9s %10s" % ("항", "길이", "키 대비", "표준", "기여(폭/키)"))
    for nm, val, std, mul in (("어깨너비", SHW, 0.230, 1),
                              ("위팔 x2", uA, 0.186, 2),
                              ("팔뚝 x2", fA, 0.146, 2),
                              ("손 x2", hA, 0.108, 2)):
        print("    %-14s %8.4f %8.1f%% %8.1f%% %9.4f"
              % (nm, val, 100 * val / hgt, 100 * std, mul * val / hgt))
    print("    %-14s %8.4f %8.1f%%           %9.4f"
          % ("합(재구성)", recon, 100 * recon / hgt, recon / hgt))
    print("    %-14s %8.4f %8.1f%%           %9.4f"
          % ("실측 bbox 폭", W_BARE, 100 * W_BARE / hgt, W_BARE / hgt))
    print("    표준 사람이라면: 0.230 + 2x(0.186+0.146+0.108) = %.4f" % (0.230 + 2 * 0.44))

print("\n  교차검증: 재구성 %.4f vs 실측 %.4f  오차 %+.4f (%.2f%%)"
      % (recon, W_BARE, recon - W_BARE, 100 * (recon - W_BARE) / W_BARE))
print("  x축 투영 재구성 %.4f vs 실측 %.4f  오차 %+.4f (%.2f%%)"
      % (recon_x, W_BARE, recon_x - W_BARE, 100 * (recon_x - W_BARE) / W_BARE))

# ====================================================================== 실루엣 단면
# 뼈 좌표만 보면 "어깨너비"가 관절 사이 거리다. 사람 표준 0.23 은 견봉(어깨 바깥)
# 사이 거리라 정의가 다르다. 실제 실루엣이 어디서 넓어지는지 가로 슬랩으로 본다.
print("\n" + "=" * 78)
print("[11] 실루엣 가로 단면 (몸 조각만, z 슬랩별 x 폭)")
print("=" * 78)
NSLAB = 24
slab = defaultdict(list)
for v in BODY:
    c = CO[v]
    k = min(NSLAB - 1, int((c.z - BB_BODY[4]) / H_BARE * NSLAB))
    slab[k].append(c.x)
print("  %-6s %-16s %8s %8s" % ("슬랩", "z 범위(키%)", "x 폭", "키 대비"))
for k in range(NSLAB - 1, -1, -1):
    if k not in slab:
        continue
    lo = 100.0 * k / NSLAB
    w = max(slab[k]) - min(slab[k])
    bar = "#" * int(round(40 * w / W_BARE))
    print("  %-6d %5.1f~%5.1f%%      %8.4f %7.1f%%  %s"
          % (k, lo, lo + 100.0 / NSLAB, w, 100 * w / H_BARE, bar))

# 어깨 높이대(UpperArm 관절 z ±5%) 의 **몸통** 폭 = 견봉간 폭에 대응.
# ★T 포즈라 이 높이에 팔이 같이 걸린다. 팔 지배 정점을 빼야 몸통만 남는다.
ARMV = set()
for side in ("L", "R"):
    ARMV |= dom_verts(L[side]["upper"], L[side]["fore"], L[side]["hand"])
TORSO = BODY - ARMV
zs_lo, zs_hi = head(L["L"]["upper"]).z - 0.05 * H_BARE, head(L["L"]["upper"]).z + 0.05 * H_BARE
sh_x = [CO[v].x for v in TORSO if zs_lo <= CO[v].z <= zs_hi]
MESH_SH = (max(sh_x) - min(sh_x)) if sh_x else 0.0
# 몸통 전체에서 가장 넓은 지점(최대 견봉/삼각근 폭)
tx = [CO[v].x for v in TORSO]
TORSO_MAX = max(tx) - min(tx)
print("\n  팔 지배 정점 %d개 제외 -> 몸통 정점 %d개" % (len(ARMV), len(TORSO)))
print("  어깨 높이대 몸통 실루엣 폭   %.4f = 키의 %5.1f%%  (사람 견봉간 23%%, 삼각근간 26%%)"
      % (MESH_SH, 100 * MESH_SH / H_BARE))
print("  몸통 최대 폭               %.4f = 키의 %5.1f%%" % (TORSO_MAX, 100 * TORSO_MAX / H_BARE))
print("  뼈 관절 사이 어깨너비        %.4f = 키의 %5.1f%%  (사람 어깨관절간 ~20%%)"
      % (SHW, 100 * SHW / H_BARE))

# ====================================================================== 머리 재검
# ★등신 수는 머리 높이 정의에 통째로 좌우된다. Head 뼈 지배 정점만 보면
# 목·턱이 빠져 머리가 과소평가될 수 있다. 목 관절 위쪽 전체로도 재서 대조한다.
print("\n" + "=" * 78)
print("[12] 머리 영역 재검 (등신 수 정의 확정용)")
print("=" * 78)
above_neck = [v for v in BODY if CO[v].z >= NECKJ]
anz = [CO[v].z for v in above_neck]
anx = [CO[v].x for v in above_neck]
any_ = [CO[v].y for v in above_neck]
print("  목 관절 위 몸 정점 %d개: z %.4f..%.4f (높이 %.4f)  폭 %.4f  두께 %.4f"
      % (len(above_neck), min(anz), max(anz), max(anz) - min(anz),
         max(anx) - min(anx), max(any_) - min(any_)))
print("  Head 뼈 지배 정점 %d개: z %.4f..%.4f (높이 %.4f)"
      % (len(hverts), CHIN, CROWN, HH_CHIN))
hx = [CO[v].x for v in hverts]
hy = [CO[v].y for v in hverts]
print("  맨머리 폭 %.4f  두께 %.4f  높이 %.4f  -> 폭/높이 %.2f"
      % (max(hx) - min(hx), max(hy) - min(hy), HH_CHIN,
         (max(hx) - min(hx)) / HH_CHIN))
if helm_z:
    hlx = [CO[v].x for v in VSET["helmet"]]
    print("  헬멧 폭 %.4f  z %.4f..%.4f  (맨머리 정수리 위로 %.4f = 키의 %.1f%% 추가)"
          % (max(hlx) - min(hlx), min(helm_z), max(helm_z),
             CROWN_H - CROWN, 100 * (CROWN_H - CROWN) / H_BARE))
# ★턱밑을 제대로 잡았는지 확인. Head 뼈 지배 정점을 얇은 z 슬랩으로 쪼개
# 폭·두께가 어디서 꺾이는지 본다. 목이 섞였다면 아래쪽 슬랩이 확 좁아진다.
print("\n  머리 정점 z 프로파일 (목이 섞였는지 확인)")
print("    %-8s %-14s %8s %8s %6s" % ("슬랩", "z", "x폭", "y두께", "정점"))
NH = 8
hs = defaultdict(list)
for v in hverts:
    k = min(NH - 1, int((CO[v].z - CHIN) / max(HH_CHIN, 1e-9) * NH))
    hs[k].append(CO[v])
for k in range(NH - 1, -1, -1):
    if k not in hs:
        continue
    cs = hs[k]
    z0 = CHIN + HH_CHIN * k / NH
    print("    %-8d %.3f~%.3f  %8.4f %8.4f %6d"
          % (k, z0, z0 + HH_CHIN / NH,
             max(c.x for c in cs) - min(c.x for c in cs),
             max(c.y for c in cs) - min(c.y for c in cs), len(cs)))
# 목 후보: Neck 뼈 지배 정점의 z 범위
nverts = dom_verts(NECK)
if nverts:
    nz = [CO[v].z for v in nverts]
    nx = [CO[v].x for v in nverts]
    print("    Neck 뼈 지배 정점 %d개: z %.4f..%.4f  x폭 %.4f"
          % (len(nverts), min(nz), max(nz), max(nx) - min(nx)))

print("\n  ★등신 수 정리 (분모를 무엇으로 잡느냐)")
print("    맨머리 턱밑~정수리 %.4f  -> 키 %.4f / = %.2f등신" % (HH_CHIN, H_BARE, H_BARE / HH_CHIN))
print("    목관절~정수리     %.4f  -> 키 %.4f / = %.2f등신" % (HH_NECK, H_BARE, H_BARE / HH_NECK))
if helm_z:
    print("    턱밑~헬멧꼭대기   %.4f  -> 키 %.4f / = %.2f등신"
          % (CROWN_H - CHIN, H_HELM, H_HELM / (CROWN_H - CHIN)))
    print("    목관절~헬멧꼭대기 %.4f  -> 키 %.4f / = %.2f등신"
          % (CROWN_H - NECKJ, H_HELM, H_HELM / (CROWN_H - NECKJ)))

# ====================================================================== 팔 처짐
print("\n" + "=" * 78)
print("[13] 팔 처짐 (레스트가 진짜 T 인가 A 인가)")
print("=" * 78)
for side in ("L", "R"):
    a = ARM[side]
    dz = a["hu"].z - a["tip"].z
    dx = abs(a["tip"].x - a["hu"].x)
    print("  %s: 어깨 z %.4f -> 손끝 z %.4f  낙차 %.4f  수평 %.4f  -> 처짐 %.1f도"
          % (side, a["hu"].z, a["tip"].z, dz, dx, math.degrees(math.atan2(dz, dx))))
print("  * 팔을 완전 수평으로 폈을 때의 폭 = 어깨 + 2 x 팔길이 = %.4f" % recon)
print("    그때 폭/키 = %.4f (맨머리) / %.4f (헬멧포함)" % (recon / H_BARE, recon / H_HELM))

print("\n" + "=" * 78)
print("요약 한 줄")
print("=" * 78)
print("  폭/키 = %.4f (맨머리) / %.4f (헬멧포함)" % (W_BARE / H_BARE, W_BARE / H_HELM))
print("  팔 1짝(어깨~손끝) = 키의 %.1f%% (표준 44.0%%, %.2f배)"
      % (100 * (ARM["L"]["total"] + ARM["R"]["total"]) / 2 / H_BARE,
         ((ARM["L"]["total"] + ARM["R"]["total"]) / 2 / H_BARE) / 0.44))
print("  다리 전체 = 키의 %.1f%% (표준 47.0%%, %.2f배)"
      % (100 * (LEG["L"]["leg_z"] + LEG["R"]["leg_z"]) / 2 / H_BARE,
         ((LEG["L"]["leg_z"] + LEG["R"]["leg_z"]) / 2 / H_BARE) / 0.47))
print("  어깨너비 = 키의 %.1f%% (표준 23.0%%, %.2f배)"
      % (100 * SHW / H_BARE, (SHW / H_BARE) / 0.23))
print("  등신(턱밑~정수리) = %.2f등신" % (H_BARE / HH_CHIN))

# ====================================================================== 검증 렌더
# RENDER=1 일 때만. 실측한 높이·폭을 실제 실루엣 위에 선으로 그어 눈으로 대조한다.
# 숫자가 엉뚱한 곳(예: 턱밑을 잘못 잡음)을 가리키면 여기서 바로 드러난다.
if os.environ.get("RENDER", "0") == "1":
    OUT = os.path.join(ROOT, "renders/history/v52_proportions")
    os.makedirs(OUT, exist_ok=True)
    ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                        else "BLENDER_EEVEE")
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = True
    wd = bpy.data.worlds.new("W")
    sc.world = wd
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    # 평면 실루엣: 조명 무관하게 균일한 회색으로 칠한다
    for mat in list(bpy.data.materials):
        nt = mat.node_tree
        nt.nodes.clear()
        o_n = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (0.62, 0.64, 0.68, 1)
        nt.links.new(em.outputs[0], o_n.inputs[0])

    # 장비 숨기기용 Mask 모디파이어(파괴적 삭제 대신)
    kg = mesh.vertex_groups.new(name="KEEP")
    md = mesh.modifiers.new("MASK", "MASK")
    md.vertex_group = "KEEP"

    RX, RY = 900, 855
    WORLD_W, WORLD_H = 3.0, 3.0 * RY / RX
    CX_R, CZ_R = 0.0, H_HELM / 2.0
    sc.render.resolution_x, sc.render.resolution_y = RX, RY
    cd2 = bpy.data.cameras.new("CV")
    camv = bpy.data.objects.new("CV", cd2)
    sc.collection.objects.link(camv)
    sc.camera = camv
    cd2.type = "ORTHO"
    cd2.ortho_scale = WORLD_W                       # 긴 변(x) 기준
    camv.location = Vector((CX_R, -12.0, CZ_R))
    camv.rotation_euler = (math.radians(90), 0, 0)

    SHOTS = [("body_helmet", VSET["body"] | VSET.get("helmet", set())),
             ("body_only", VSET["body"])]
    for nm, keep in SHOTS:
        for g in list(mesh.vertex_groups):
            if g.name == "KEEP":
                mesh.vertex_groups.remove(g)
        kg = mesh.vertex_groups.new(name="KEEP")
        kg.add(list(keep), 1.0, "REPLACE")
        md.vertex_group = "KEEP"
        sc.render.filepath = os.path.join(OUT, "silhouette_%s.png" % nm)
        bpy.ops.render.render(write_still=True)
        print("  렌더 %s (정점 %d)" % (sc.render.filepath, len(keep)))

    # ------------------------------------------------------------ 눈금 + 픽셀 검증
    # Blender 파이썬에 PIL 이 없다(numpy 는 있다). 버퍼에 직접 선을 긋는다.
    import numpy as np

    def px_x(x):
        return int(round((x - CX_R) / WORLD_W * RX + RX / 2.0))

    def px_y(z):
        return int(round(RY / 2.0 - (z - CZ_R) / WORLD_H * RY))

    # (z, 색). 빨강=헬멧꼭대기 주황=정수리/턱밑 파랑=어깨관절 초록=골반 흰=발바닥
    HLINES = [(CROWN_H, (0.95, 0.25, 0.25)), (CROWN, (0.98, 0.62, 0.15)),
              (CHIN, (0.98, 0.62, 0.15)), (head(L["L"]["upper"]).z, (0.25, 0.70, 0.98)),
              (head(PELVIS).z, (0.45, 0.85, 0.40)), (LEG["L"]["sole"], (0.90, 0.90, 0.90))]
    VLINES = [(BB_BODY[0], (1.0, 0.35, 0.75)), (BB_BODY[1], (1.0, 0.35, 0.75)),
              (head(L["L"]["upper"]).x, (0.25, 0.70, 0.98)),
              (head(L["R"]["upper"]).x, (0.25, 0.70, 0.98))]

    print("\n  픽셀 검증 (렌더 실루엣을 다시 재서 3D 실측과 대조)")
    for nm, _ in SHOTS:
        p = os.path.join(OUT, "silhouette_%s.png" % nm)
        im = bpy.data.images.load(p)
        iw, ih = im.size
        buf = np.empty(iw * ih * 4, dtype=np.float32)
        im.pixels.foreach_get(buf)
        a = buf.reshape(ih, iw, 4)                  # 아래에서 위로(y 뒤집힘)
        alpha = a[:, :, 3]
        rows = np.where(alpha.max(axis=1) > 0.02)[0]
        cols = np.where(alpha.max(axis=0) > 0.02)[0]
        h_px, w_px = rows[-1] - rows[0] + 1, cols[-1] - cols[0] + 1
        # 픽셀 -> 월드 환산 (x 는 RX 픽셀이 WORLD_W, z 는 RY 픽셀이 WORLD_H)
        h_w = h_px / RY * WORLD_H
        w_w = w_px / RX * WORLD_W
        print("    %-12s 실루엣 %dx%d px -> 월드 키 %.4f 폭 %.4f  폭/키 %.4f"
              % (nm, w_px, h_px, h_w, w_w, w_px / RX * WORLD_W / (h_px / RY * WORLD_H)))
        # 눈금 합성: 배경을 어둡게 깔고 선을 긋는다
        rgb = a[:, :, :3] * alpha[:, :, None] + np.array([0.09, 0.10, 0.12]) * (1 - alpha[:, :, None])
        for z, col in HLINES:
            yy = ih - 1 - px_y(z)                   # 버퍼는 아래가 0
            if 0 <= yy < ih:
                rgb[yy, :, :] = col
        for x, col in VLINES:
            xx = px_x(x)
            if 0 <= xx < iw:
                rgb[:, xx, :] = col
        out = np.concatenate([rgb, np.ones((ih, iw, 1), dtype=np.float32)], axis=2)
        im.pixels.foreach_set(out.astype(np.float32).ravel())
        im.filepath_raw = p
        im.file_format = "PNG"
        im.save()
        bpy.data.images.remove(im)
        print("      눈금 합성 완료 %s" % p)
    print("    선 색: 빨강=헬멧꼭대기 주황=정수리/턱밑 파랑=어깨관절(가로)·어깨관절x(세로)")
    print("           초록=골반 흰=발바닥 분홍=몸 bbox 좌우끝")

print("\nDONE")
