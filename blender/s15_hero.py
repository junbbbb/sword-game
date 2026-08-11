# -*- coding: utf-8 -*-
"""Meshy 로 뽑은 옷(벨트+모피 치마+어깨끈)과 검을 기본 캐릭터에 입혀 web/hero.glb 를 만든다.

받은 것
  incoming/basic_cloth.glb  메시 1개 2093삼각 / 스킨·뼈 없음 / 텍스처 4장(JPEG)
                            실제 형태는 '옷 한 벌'이 아니라 **허리 벨트 + 모피 로인클로스
                            + 어깨에 두른 가죽 끈** 이다(렌더로 확인).
  incoming/basic_sword.glb  메시 1개 1545삼각 / 스킨·뼈 없음 / 텍스처 3장(PNG)
                            휜 외날검. 코등이가 불꽃 모양이라 bbox 세 축이 다 비슷하다.

몸은 basic2 를 고른다(판정 근거는 아래 [몸 선택] 주석).

★스키닝은 전부 REST(바인드) 포즈에서 굽는다. 포즈 상태에서 재면 애니에서 어긋난다.
★좌표계: glTF 임포트 후 정면 -Y, 위 +Z, 캐릭터 오른쪽 -X. 내보낼 때 export_yup=True.

실행: blender --background --python s15_hero.py
환경변수: HIP_F(벨트 높이 z/키) CLOTH_S(배율 배수) SW_LEN_R(검 길이/키)
          SW_TILT(칼날 들어올림 도) SW_ROLL(칼날 축 회전 도) SW_DY(그립 앞뒤 cm)
          TEX_SIZE TEX_FORMAT TEX_QUALITY OUT_GLB
"""
import bpy
import bmesh
import os
import math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = "/Users/lbj/Documents/gameproject"
WEB = os.path.join(ROOT, "web")
INC = os.path.join(ROOT, "incoming")

# ---------------------------------------------------------------- [몸 선택]
# basic / basic2 둘 다에 옷을 얹어 재 본 결과(probe 기록):
#
#   측정                                     basic          basic2
#   옷 정점이 몸 안에 박힌 비율              2.3%(25/1089)  1.5%(16/1089)
#   최대 박힘 깊이                           2.63cm(어깨끈) 0.66cm(치마)
#   어깨끈만                                 18.3% 박힘     3.8% 박힘
#   벨트가 허리에 맞으려면 필요한 배율 S_b   0.3769         0.3872
#   어깨끈이 몸을 안 파고들 최소 배율 S_s    0.4221         0.3988
#   ★S_s / S_b  (1.0 이면 옷 자체 비례가 그 몸과 일치)   1.120          1.030
#   허리 단면 종횡비 x/y (벨트는 1.05)       1.51           1.29
#
# 결정적 근거는 마지막 줄이다. 옷은 벨트 둘레와 어깨끈 고리 길이라는 **서로 독립인
# 두 치수**를 갖고 있는데, basic 에서는 두 치수가 요구하는 배율이 12.0% 어긋나고
# basic2 에서는 3.0% 밖에 안 어긋난다. 즉 이 옷의 자체 비례는 basic2 몸통에 맞다.
# 직접 박힘 비율(2.3% vs 1.5%)과 최악 깊이(2.63cm vs 0.66cm)도 같은 방향이다.
BODY_GLB = os.environ.get("BODY_GLB", "basic2.glb")
CLOTH_GLB = os.path.join(INC, "basic_cloth.glb")
SWORD_GLB = os.path.join(INC, "basic_sword.glb")
OUT_GLB = os.environ.get("OUT_GLB") or os.path.join(WEB, "hero.glb")

HIP_F = float(os.environ.get("HIP_F", "0.560"))     # 벨트를 앉힐 높이 z/키
CLOTH_S = float(os.environ.get("CLOTH_S", "1.035"))  # 벨트 최소배율에 곱할 여유
SW_LEN_R = float(os.environ.get("SW_LEN_R", "0.68"))  # 검 전체 길이 / 키
SW_TILT = float(os.environ.get("SW_TILT", "35.0"))   # 주먹 터널축 둘레로 돌린 각(도)
# ★SW_TILT 만으로는 칼끝 높이를 못 잡는다. 그 회전축이 팔뚝축(뼈 +Y)이라
#   T포즈에서는 위아래로 돌지만 팔을 내린 Idle 에서는 **수평으로** 돌 뿐이다.
#   칼끝을 들려면 팔뚝축 쪽으로 눕히는 각이 따로 필요하다. 그게 SW_LIFT 다.
#   (0 으로 두면 Walk f21 에서 칼이 바닥 아래 15.8cm 까지 내려간다. 실측)
SW_LIFT = float(os.environ.get("SW_LIFT", "38.0"))   # 칼날을 손목쪽으로 눕힌 각(도)
SW_ROLL = float(os.environ.get("SW_ROLL", "0.0"))    # 칼날 축 둘레 미세 회전(도)
SW_DY = float(os.environ.get("SW_DY", "0.0"))        # 그립을 손끝쪽(+)으로 (cm)

TEX_SIZE = int(os.environ.get("TEX_SIZE", "2048"))
TEX_FORMAT = os.environ.get("TEX_FORMAT", "JPEG").upper()
TEX_QUALITY = int(os.environ.get("TEX_QUALITY", "90"))

HAND = "Bip001 R Hand"
NANG = 36
# 옷이 물어도 되는 뼈. 팔(UpperArm/Forearm/Hand)·다리·목·머리는 뺀다.
#  - 팔을 물면 겨드랑이에서 소매가 몸통에 끌려 늘어난다(어깨끈이 그 위험 구간이다)
#  - 다리를 물면 치마가 두 허벅지 사이에서 찢어진다
#  - 목/머리를 물면 어깨끈이 고개를 따라 움직인다
ALLOW = ("Bip001 Pelvis", "Bip001 Spine", "Bip001 Chest", "Bip001 Chest2",
         "Bip001 L Clavicle", "Bip001 R Clavicle")
# 치마(벨트 아래)는 다리를 물려야 한다. 골반에만 묶으면 무릎을 들 때 허벅지가
# 치마를 그대로 뚫고 나온다(1차 굽기 실측: Run 프레임당 평균 71정점, 최대 8.0cm).
# 대신 벨트 선에서 밑단으로 갈수록 서서히 넘긴 뒤 웨이트를 스무딩해서 이음매를 없앤다.
ALLOW_LEG = ("Bip001 Pelvis", "Bip001 Spine", "Bip001 L Thigh", "Bip001 R Thigh")
LEG_MAX = float(os.environ.get("LEG_MAX", "0.85"))  # 밑단에서 다리 추종 강도
SMOOTH_N = int(os.environ.get("SMOOTH_N", "14"))    # 웨이트 라플라시안 스무딩 횟수
# ★스무딩 횟수가 이 캐릭터에서 가장 민감한 손잡이다(실측).
#     6회  : 최대 늘음 7.75배 / Run 뚫림 25.8개  = 웨이트 경계가 날카로워 치마가 찢어진다
#     14회 : 최대 늘음 4.72배 / Run 뚫림 34.1개  = 늘음이 여러 정점에 퍼져 고무처럼 부드럽다
#   둘 다 못 잡는다(보폭 1.4m 짜리 전력질주라 강체 스키닝의 한계다).
#   찢어짐이 더 눈에 띄므로 14회를 고르고, 뚫림은 밑단 여유(CONFORM_HEM)로 줄인다.

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene


def drop_importer_junk():
    """임포터가 뼈를 그리려고 만드는 Icosphere 등. glb 안에는 없는 물건이다."""
    for o in list(sc.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            print("  임포터 잡동사니 제거:", o.name)
            bpy.data.objects.remove(o, do_unlink=True)


def imp(path):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    drop_importer_junk()
    return [o for o in sc.objects if o.name not in before]


def weld(ob, dist=1e-5):
    """glTF 는 UV/노멀 이음매에서 정점을 쪼갠다. 섬 판정과 웨이트 전이 전에 붙인다."""
    n0 = len(ob.data.vertices)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return n0, len(ob.data.vertices)


def islands(ob):
    adj = {i: set() for i in range(len(ob.data.vertices))}
    for p in ob.data.polygons:
        vs = list(p.vertices)
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            adj[a].add(b)
            adj[b].add(a)
    seen, out = set(), []
    for i in range(len(ob.data.vertices)):
        if i in seen:
            continue
        st, comp = [i], []
        seen.add(i)
        while st:
            a = st.pop()
            comp.append(a)
            for nb in adj[a]:
                if nb not in seen:
                    seen.add(nb)
                    st.append(nb)
        out.append(comp)
    out.sort(key=len, reverse=True)
    return out


def bake_world(ob):
    """정점을 월드 좌표로 굽고 오브젝트 행렬을 단위행렬로."""
    ob.data.transform(ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)
    ob.data.update()


# ================================================================ 1) 몸
print("=" * 72)
print("[1] 몸 %s" % BODY_GLB)
objs = imp(os.path.join(WEB, BODY_GLB))
arm = next(o for o in objs if o.type == "ARMATURE")
body = next(o for o in objs if o.type == "MESH")
body.name = body.data.name = "char1"
for a in bpy.data.actions:
    a.use_fake_user = True      # ★안 켜면 export 에서 조용히 빠진다
ACT_NAMES = sorted(a.name for a in bpy.data.actions)
print("  아마추어 %s 뼈 %d개 / 메시 %s 정점 %d / 액션 %s"
      % (arm.name, len(arm.data.bones), body.name, len(body.data.vertices),
         ACT_NAMES))
print("  씬 fps %d  (★FBX 임포터가 fps 를 바꾸는 함정이 있어 찍어 둔다)"
      % sc.render.fps)
for a in bpy.data.actions:
    print("    액션 %-6s 프레임 %.1f~%.1f (%.3f초 @%dfps)"
          % (a.name, a.frame_range[0], a.frame_range[1],
             (a.frame_range[1] - a.frame_range[0]) / sc.render.fps, sc.render.fps))

arm.data.pose_position = "REST"
bpy.context.view_layer.update()
A2W = arm.matrix_world
BW = [body.matrix_world @ v.co for v in body.data.vertices]
H = max(p.z for p in BW) - min(p.z for p in BW)
FOOT = min(p.z for p in BW)
print("  키 %.4f  발바닥z %.4f  아마추어 스케일 %.4f (뼈 로컬 1 = %.1fcm)"
      % (H, FOOT, A2W.to_scale().x, A2W.to_scale().x * 100))

# ================================================================ 2) 옷 얹기
print("=" * 72)
print("[2] 옷")
cobjs = imp(CLOTH_GLB)
cloth = next(o for o in cobjs if o.type == "MESH")
n0, n1 = weld(cloth)
bake_world(cloth)
print("  정점 %d -> 용접 후 %d / 삼각형 %d"
      % (n0, n1, sum(len(p.vertices) - 2 for p in cloth.data.polygons)))
CV = [v.co.copy() for v in cloth.data.vertices]
isl = islands(cloth)
print("  섬 %d개" % len(isl))
# 벨트 고리 = 가로로 넓고 세로로 얇은 섬
belt = next(s for s in isl
            if (max(CV[i].x for i in s) - min(CV[i].x for i in s)) > 0.9
            and (max(CV[i].z for i in s) - min(CV[i].z for i in s)) < 0.3)
bp = [CV[i] for i in belt]
BCX = (max(p.x for p in bp) + min(p.x for p in bp)) / 2
BCY = (max(p.y for p in bp) + min(p.y for p in bp)) / 2
BZ0, BZ1 = min(p.z for p in bp), max(p.z for p in bp)
BMID = (BZ0 + BZ1) / 2
strap = max(isl, key=lambda s: max(CV[i].z for i in s) - min(CV[i].z for i in s))
print("  벨트 = 정점 %d  z %.3f~%.3f  중심(%.3f,%.3f)"
      % (len(belt), BZ0, BZ1, BCX, BCY))
print("  어깨끈 = 정점 %d  z %.3f~%.3f"
      % (len(strap), min(CV[i].z for i in strap), max(CV[i].z for i in strap)))


def ring(pts, cx, cy, mode):
    """각도 구간별 반경. 고리의 안쪽면(min) / 바깥면(max)."""
    r = [None] * NANG
    for p in pts:
        d = math.hypot(p.x - cx, p.y - cy)
        k = int((math.atan2(p.y - cy, p.x - cx) + math.pi) / (2 * math.pi) * NANG) % NANG
        if r[k] is None:
            r[k] = d
        elif mode == "min":
            r[k] = min(r[k], d)
        else:
            r[k] = max(r[k], d)
    return r


RIN = ring(bp, BCX, BCY, "min")
# 허리 프로파일(팔 제외). 벨트 띠 높이만큼의 밴드에서 잰다.
ARMG = [g.index for g in body.vertex_groups
        if any(t in g.name for t in ("UpperArm", "Forearm", "Hand"))]
armv = set()
for v in body.data.vertices:
    for g in v.groups:
        if g.group in ARMG and g.weight > 0.25:
            armv.add(v.index)
            break
ZC = FOOT + H * HIP_F
band = [p for i, p in enumerate(BW)
        if i not in armv and abs(p.z - ZC) <= (BZ1 - BZ0) * 0.5]
WCX = (max(p.x for p in band) + min(p.x for p in band)) / 2
WCY = (max(p.y for p in band) + min(p.y for p in band)) / 2
RB = ring(band, WCX, WCY, "max")
S_MIN = max(RB[i] / RIN[i] for i in range(NANG) if RIN[i] and RB[i])
S = S_MIN * CLOTH_S
print("  허리 밴드 정점 %d 중심(%.4f,%.4f) z %.4f" % (len(band), WCX, WCY, ZC))
print("  벨트 최소배율 %.4f x 여유 %.3f = %.4f (키 대비 %.4f)"
      % (S_MIN, CLOTH_S, S, S / H))

for v in cloth.data.vertices:
    p = v.co
    v.co = Vector((WCX + (p.x - BCX) * S, WCY + (p.y - BCY) * S,
                   ZC + (p.z - BMID) * S))
cloth.data.update()
BELT_TOP = ZC + (BZ1 - BMID) * S
CV = [v.co.copy() for v in cloth.data.vertices]
knee_z = (A2W @ arm.data.bones["Bip001 R Calf"].head_local).z
print("  배치 후 옷 z %.4f~%.4f  (벨트 윗선 %.4f, 무릎 %.4f)"
      % (min(p.z for p in CV), max(p.z for p in CV), BELT_TOP, knee_z))
print("  치마 밑단 z/키 %.3f  무릎 z/키 %.3f  -> %s"
      % ((min(p.z for p in CV) - FOOT) / H, (knee_z - FOOT) / H,
         "무릎 위" if min(p.z for p in CV) > knee_z else "★무릎 아래(다리가 뚫을 수 있다)"))

# ---- 2-1) 몸이 옷을 뚫는 문제: 옷 정점을 몸 표면 밖으로 밀어낸다 ----
# ★"옷에 가려지는 몸 정점을 지운다" 는 쓸 수 없다. 이 옷은 몸을 덮는 옷이 아니라
#   벨트 + 허리에서 늘어진 로인클로스 + 어깨끈이다. 가려지는 몸 면적이 거의 없고,
#   치마 틈새로 맨살이 그대로 보이므로 지우면 구멍이 뚫린다.
# ★"몸을 안쪽으로 줄인다" 도 안 쓴다. 실루엣(근육)이 캐릭터 정체성인데 옷 몇 개
#   정점 때문에 몸 전체를 깎는 건 비용이 반대다.
# 그래서 **옷 쪽을 몸 표면 바깥으로 밀어낸다**(conform). 아래 실측대로 최대 6.6mm 라
# 옷 모양은 눈으로 구분이 안 되고, 뚫림은 0 이 된다.
# ★여유 간격은 높이에 따라 다르게 준다. 벨트 선은 몸에 붙어야 벨트답고(4mm),
#   치마 밑단은 넉넉히 떨어져 있어야 달릴 때 허벅지가 앞으로 나와도 안 뚫는다(18mm).
CONFORM_M = float(os.environ.get("CONFORM_M", "0.004"))
CONFORM_HEM = float(os.environ.get("CONFORM_HEM", "0.028"))
Minv = body.matrix_world.inverted()
M3 = body.matrix_world.to_3x3()
SK_BOT0 = min(p.z for p in CV)
SK_D0 = max(1e-6, BELT_TOP - SK_BOT0)
moved, worst = 0, 0.0
for v in cloth.data.vertices:
    p = v.co
    tt = min(1.0, max(0.0, (BELT_TOP - p.z) / SK_D0))
    marg = CONFORM_M + (CONFORM_HEM - CONFORM_M) * (tt * tt * (3 - 2 * tt))
    hit, loc, nrm, _ = body.closest_point_on_mesh(Minv @ p)
    if not hit:
        continue
    lw = body.matrix_world @ loc
    nw = (M3 @ nrm).normalized()
    d = (p - lw).dot(nw)
    if d < marg:
        v.co = lw + nw * marg
        moved += 1
        worst = max(worst, marg - d)
cloth.data.update()
CV = [v.co.copy() for v in cloth.data.vertices]
print("  [conform] 몸에 너무 붙은 정점 %d개를 표면 밖(벨트 %.0fmm ~ 밑단 %.0fmm)으로 밀어냄"
      " (최대 이동 %.1fmm)"
      % (moved, CONFORM_M * 1000, CONFORM_HEM * 1000, worst * 1000))

# ---- 2-2) 웨이트 전이 ----
# 옷에 뼈가 없다. 몸의 정점 그룹을 옷으로 옮긴다.
# ★벨트 아래(치마)는 **벨트 높이에서 샘플**한다. 그대로 재면 허벅지 웨이트를 물어
#   다리를 벌릴 때 치마가 두 갈래로 찢어진다. 벨트 높이에서 뜨면 골반에 고정돼
#   치마가 통째로 엉덩이를 따라 흔들린다(실제 로인클로스가 그렇다).
GNAME = {g.index: g.name for g in body.vertex_groups}


def sample(p, allow):
    """몸 표면에서 가장 가까운 면을 찾아 그 면 정점들의 웨이트를 거리 역수로 섞는다."""
    hit, loc, nrm, fi = body.closest_point_on_mesh(Minv @ p)
    acc = {}
    if not hit:
        return acc
    lw = body.matrix_world @ loc
    for vi in body.data.polygons[fi].vertices:
        bv = body.matrix_world @ body.data.vertices[vi].co
        w = 1.0 / ((bv - lw).length + 1e-4)
        for g in body.data.vertices[vi].groups:
            nm = GNAME[g.group]
            if nm not in allow:
                continue
            acc[nm] = acc.get(nm, 0.0) + w * g.weight
    tot = sum(acc.values())
    return {k: v / tot for k, v in acc.items()} if tot > 1e-6 else {}


SK_BOT = min(p.z for p in CV)
SK_DEPTH = max(1e-6, BELT_TOP - SK_BOT)
WT = []
fallback = 0
for v in cloth.data.vertices:
    p = v.co
    if p.z >= BELT_TOP:
        w = sample(p, ALLOW)
    else:
        # ★1차 굽기에서는 깊이에 비례해 천천히 넘겼더니, 정작 가장 많이 뚫리는
        #   치마 **윗부분**(엉덩이·허벅지 뿌리)이 골반에 묶여 그대로 뚫렸다.
        #   달릴 때 허벅지는 고관절 바로 아래부터 앞으로 나온다. 그래서 위에서부터
        #   빨리 넘기고 깊이 55% 지점에서 이미 다리를 100% 따라가게 한다.
        k = min(1.0, max(0.0, (BELT_TOP - p.z) / SK_DEPTH) / 0.55)
        k = k * k * (3 - 2 * k) * LEG_MAX          # 부드럽게 다리로 넘긴다
        w_top = sample(Vector((p.x, p.y, BELT_TOP)), ALLOW)
        w_leg = sample(p, ALLOW_LEG)
        w = {}
        for nm, val in w_top.items():
            w[nm] = w.get(nm, 0.0) + (1 - k) * val
        for nm, val in w_leg.items():
            w[nm] = w.get(nm, 0.0) + k * val
    if sum(w.values()) < 1e-6:
        w = {"Bip001 Pelvis": 1.0}
        fallback += 1
    WT.append(w)
print("  [웨이트] 폴백(주변에 허용 뼈가 없어 골반 1.0) %d개" % fallback)

# ★라플라시안 스무딩: 이웃 정점과 웨이트를 섞어 이음매를 없앤다.
#   웨이트가 정점마다 툭툭 바뀌면 그 경계에서 옷이 찢어져 보인다.
nb = {i: set() for i in range(len(cloth.data.vertices))}
for e in cloth.data.edges:
    a, b = e.vertices
    nb[a].add(b)
    nb[b].add(a)
for _ in range(SMOOTH_N):
    NW = []
    for i, w in enumerate(WT):
        acc = dict(w)
        for j in nb[i]:
            for nm, val in WT[j].items():
                acc[nm] = acc.get(nm, 0.0) + val
        tot = sum(acc.values())
        NW.append({k: v / tot for k, v in acc.items()})
    WT = NW

# ★가랑이 함정: 앞판이 **두 허벅지를 동시에** 물면 다리를 벌릴 때 양쪽으로 찢어진다.
#   1차 굽기 실측에서 7.5mm 모서리가 57.9mm(7.75배)로 벌어졌고, 원인은 인접 정점이
#   L 0.528/R 0.424 와 L 0.367/R 0.578 처럼 좌우가 뒤집힌 것이었다. 보폭이 1.4m 라
#   웨이트 7% 차이가 3cm 벌어짐이 된다.
#   ★이 보정은 반드시 **스무딩 뒤**에 해야 한다. 앞에서 하면 스무딩이 이웃한테서
#     허벅지 웨이트를 다시 끌어와 그대로 원복된다(실제로 그래서 안 먹었다).
LT, RT = "Bip001 L Thigh", "Bip001 R Thigh"
merged = 0
for i, w in enumerate(WT):
    wl, wr = w.get(LT, 0.0), w.get(RT, 0.0)
    if wl + wr < 1e-6:
        continue
    c = 2.0 * min(wl, wr) / (wl + wr)     # 1 = 양다리를 똑같이 뭄 = 가랑이
    if c < 1e-3:
        continue
    give = c * (wl + wr)
    w[LT] = wl * (1 - c)
    w[RT] = wr * (1 - c)
    w["Bip001 Pelvis"] = w.get("Bip001 Pelvis", 0.0) + give
    merged += 1
print("  [웨이트] 양다리를 같이 문 정점 %d개의 다리 웨이트를 골반으로 이관" % merged)

# ★glTF 는 정점당 뼈 4개까지다. 여기서 안 자르면 익스포터가 조용히 잘라 정규화해
#   내가 검증한 것과 다른 게 나간다.
# ★단순 상위 4개 자르기는 이웃끼리 **다른 뼈**가 살아남아 그 자체로 틈을 만든다
#   (실측: 어깨끈에서 한 정점은 Pelvis 0.182, 옆 정점은 L Clavicle 0.177 이 살아남아
#    6.2mm 가 22.6mm 로 벌어졌다). 먼저 작은 웨이트를 잘라내 이웃끼리 같은 뼈만
#   남게 만든 뒤 4개로 줄인다.
PRUNE = float(os.environ.get("PRUNE", "0.02"))
over = 0
for i, w in enumerate(WT):
    items = [(k, v) for k, v in w.items() if v >= PRUNE]
    if not items:
        items = [max(w.items(), key=lambda x: x[1])]
    items.sort(key=lambda x: -x[1])
    if len(items) > 4:
        over += 1
        items = items[:4]
    tot = sum(v for _, v in items)
    WT[i] = {k: v / tot for k, v in items}
print("  [웨이트] %.2f 미만 가지치기 후에도 4개 초과라 자른 정점 %d개" % (PRUNE, over))
print("  [웨이트] 정점당 뼈 수 분포 %s"
      % sorted({n: sum(1 for w in WT if len(w) == n) for n in (1, 2, 3, 4)}.items()))

used = {}
for bn in set(ALLOW) | set(ALLOW_LEG):
    if bn not in cloth.vertex_groups:
        cloth.vertex_groups.new(name=bn)
for i, w in enumerate(WT):
    for nm, val in w.items():
        cloth.vertex_groups[nm].add([i], val, "REPLACE")
        used[nm] = used.get(nm, 0) + 1
sums = [sum(w.values()) for w in WT]
print("  [웨이트] 뼈별 영향 정점 수 %s" % sorted(used.items(), key=lambda x: -x[1]))
print("  [웨이트] ★합 최소 %.6f 최대 %.6f / 1과 다른 정점 %d개 (0 이어야 원점으로 안 빨린다)"
      % (min(sums), max(sums), sum(1 for s in sums if abs(s - 1.0) > 1e-5)))
md = cloth.modifiers.new("Armature", "ARMATURE")
md.object = arm
cloth.parent = arm          # ★익스포터 경고 "Armature must be the parent" 방지
cloth.matrix_parent_inverse = arm.matrix_world.inverted()
cloth.name = cloth.data.name = "cloth1"   # ★SW_/SH_ 로 시작하면 안 된다(게임이 무기로 본다)

# ================================================================ 3) 검
print("=" * 72)
print("[3] 검")
sobjs = imp(SWORD_GLB)
sword = next(o for o in sobjs if o.type == "MESH")
n0, n1 = weld(sword)
bake_world(sword)
SV = [v.co.copy() for v in sword.data.vertices]
print("  정점 %d -> 용접 후 %d / 삼각형 %d"
      % (n0, n1, sum(len(p.vertices) - 2 for p in sword.data.polygons)))


def pca3(pts):
    """공분산 고유벡터 3개를 큰 순서로. (중심, [(고유값, 방향), ...])"""
    n = len(pts)
    c = Vector((sum(p.x for p in pts) / n, sum(p.y for p in pts) / n,
                sum(p.z for p in pts) / n))
    C = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
    for p in pts:
        d = p - c
        for i in range(3):
            for j in range(3):
                C[i][j] += d[i] * d[j] / n
    A = C.copy()
    out = []
    for k in range(3):
        v = Vector((1.0, 0.37, 0.11)).normalized()
        for _ in range(400):
            nv = A @ v
            if nv.length < 1e-14:
                break
            v = nv.normalized()
        lam = v.dot(A @ v)
        out.append((lam, v.copy()))
        for i in range(3):
            for j in range(3):
                A[i][j] -= lam * v[i] * v[j]
    return c, out


SC_, SAX = pca3(SV)
AX = SAX[0][1]
t = [(p - SC_).dot(AX) for p in SV]
T0, T1 = min(t), max(t)
print("  주축 (%+.4f,%+.4f,%+.4f)  투영 %+.4f~%+.4f 길이 %.4f"
      % (AX.x, AX.y, AX.z, T0, T1, T1 - T0))
# 주축 40구간의 단면 지름 -> 최대 구간이 코등이
NSEG = 40
segs = []
for i in range(NSEG):
    a = T0 + (T1 - T0) * i / NSEG
    b = T0 + (T1 - T0) * (i + 1) / NSEG
    sel = [p for p, tv in zip(SV, t) if a <= tv <= b]
    if len(sel) < 2:
        segs.append(((a + b) / 2, len(sel), 0.0))
        continue
    per = []
    for p in sel:
        d = p - SC_
        per.append(d - d.dot(AX) * AX)
    step = max(1, len(per) // 60)
    sub = per[::step]
    dia = 0.0
    for x in range(len(sub)):
        for y in range(x + 1, len(sub)):
            dia = max(dia, (sub[x] - sub[y]).length)
    segs.append(((a + b) / 2, len(sel), dia))
GT = max(segs, key=lambda s: s[2])[0]
print("  코등이 t=%.4f 단면지름 %.4f / 양쪽 길이 -쪽 %.4f +쪽 %.4f"
      % (GT, max(s[2] for s in segs), GT - T0, T1 - GT))
# 자루 = 코등이에서 짧은 쪽. 칼날 = 긴 쪽.
GRIP_NEG = (GT - T0) < (T1 - GT)
print("  -> 자루는 주축 %s쪽 (짧은 쪽), 칼날은 %s쪽"
      % ("-" if GRIP_NEG else "+", "+" if GRIP_NEG else "-"))
gr_lo, gr_hi = (T0, GT - (GT - T0) * 0.20) if GRIP_NEG else (GT + (T1 - GT) * 0.20, T1)
bl_lo, bl_hi = (GT + (T1 - GT) * 0.18, T1) if GRIP_NEG else (T0, GT - (GT - T0) * 0.18)
grip_pts = [p for p, tv in zip(SV, t) if gr_lo <= tv <= gr_hi]
blade_pts = [p for p, tv in zip(SV, t) if bl_lo <= tv <= bl_hi]
GC, GAX = pca3(grip_pts)
GDIR = GAX[0][1]
# 자루 축은 코등이(=칼날) 쪽을 향하게 부호를 맞춘다
if GDIR.dot(AX) * (1 if GRIP_NEG else -1) < 0:
    GDIR = -GDIR
gt = [(p - GC).dot(GDIR) for p in grip_pts]
GRIP_LEN = max(gt) - min(gt)
GRIP_R = max(((p - GC) - (p - GC).dot(GDIR) * GDIR).length for p in grip_pts)
TIP = max(SV, key=lambda p: (p - GC).dot(GDIR))
print("  자루 정점 %d  중심 (%.3f,%.3f,%.3f)  축 (%+.4f,%+.4f,%+.4f)"
      % (len(grip_pts), GC.x, GC.y, GC.z, GDIR.x, GDIR.y, GDIR.z))
print("  자루 길이 %.4f 반경 %.4f / 자루중심->칼끝 %.4f / 검 전체 %.4f"
      % (GRIP_LEN, GRIP_R, (TIP - GC).dot(GDIR), T1 - T0))
# 칼날 평면: 날 정점 PCA 의 최소축 = 납작한 면의 법선
BC, BAX = pca3(blade_pts)
FLAT = BAX[2][1]
FLAT = (FLAT - FLAT.dot(GDIR) * GDIR).normalized()
EDGE = GDIR.cross(FLAT).normalized()
# 어느 쪽이 날(얇은 쪽)인가: EDGE 축 기준 위/아래 절반의 두께를 잰다
ep = [(p - BC).dot(EDGE) for p in blade_pts]
emid = (max(ep) + min(ep)) / 2
th = {}
for side in (-1, 1):
    sel = [p for p, e in zip(blade_pts, ep) if (e - emid) * side > (max(ep) - min(ep)) * 0.22]
    if sel:
        f = [(p - BC).dot(FLAT) for p in sel]
        th[side] = max(f) - min(f)
print("  칼날 평면법선 (%+.4f,%+.4f,%+.4f) / 폭축 두께 -쪽 %.4f +쪽 %.4f"
      % (FLAT.x, FLAT.y, FLAT.z, th.get(-1, -1), th.get(1, -1)))
if th.get(1, 9e9) < th.get(-1, 9e9):
    EDGE_DIR = EDGE
else:
    EDGE_DIR = -EDGE
print("  -> 날(얇은 쪽)은 %s EDGE 방향" % ("+" if EDGE_DIR is EDGE else "-"))

# ---- 3-1) 손 그립 소켓 실측 ----
hb = arm.data.bones[HAND]
HM = A2W @ hb.matrix_local          # 뼈 로컬 -> 월드 (REST)
HMi = HM.inverted()
BONE_U = A2W.to_scale().x           # 뼈 로컬 1 단위 = 몇 m 인가
hvg = body.vertex_groups[HAND]
HP = []
for v in body.data.vertices:
    for g in v.groups:
        if g.group == hvg.index and g.weight > 0.5:
            HP.append(HMi @ (body.matrix_world @ v.co))
            break
n = len(HP)
FC = Vector((sum(p.x for p in HP) / n, sum(p.y for p in HP) / n,
             sum(p.z for p in HP) / n))
print("  [손] %s 정점 %d  주먹 중심(뼈로컬 cm) (%.2f, %.2f, %.2f)"
      % (HAND, n, FC.x, FC.y, FC.z))
print("       bbox x %+.2f~%+.2f y %+.2f~%+.2f z %+.2f~%+.2f (cm)"
      % (min(p.x for p in HP), max(p.x for p in HP),
         min(p.y for p in HP), max(p.y for p in HP),
         min(p.z for p in HP), max(p.z for p in HP)))
for k, nm in enumerate("XYZ"):
    v = Vector((HM[0][k], HM[1][k], HM[2][k])).normalized()
    print("       뼈 %s축 월드방향 (%+.4f,%+.4f,%+.4f)" % (nm, v.x, v.y, v.z))
# 주먹 터널 축 = +Y(손목->손끝)에 수직인 평면에서 가장 긴 축.
# 주먹을 쥐면 손가락이 만드는 구멍이 이 방향으로 뚫린다. 자루가 여기로 지나가야 한다.
per = []
for p in HP:
    d = p - FC
    d.y = 0.0
    per.append(d)
C2 = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
for d in per:
    for i in range(3):
        for j in range(3):
            C2[i][j] += d[i] * d[j]
u = Vector((1, 0, 0.3)).normalized()
for _ in range(300):
    nv = C2 @ u
    nv.y = 0
    if nv.length < 1e-12:
        break
    u = nv.normalized()
uw = (HM.to_3x3() @ u).normalized()
if uw.y > 0:                     # 캐릭터 정면은 -Y. 엄지쪽(=정면) 으로 칼날이 나가게
    u, uw = -u, -uw
print("       주먹 터널축(뼈로컬) (%+.4f,%+.4f,%+.4f) 폭 %.2fcm / 월드 (%+.4f,%+.4f,%+.4f)"
      % (u.x, u.y, u.z, max(d.dot(u) for d in per) - min(d.dot(u) for d in per),
         uw.x, uw.y, uw.z))
# 칼날을 팔뚝 축(뼈 +Y) 둘레로 SW_TILT 만큼 들어올린다.
tilt = math.radians(SW_TILT)
a_local = Vector((0, 1, 0))
u_t = (Matrix.Rotation(tilt, 3, a_local) @ u).normalized()
# -Y 쪽으로 눕히면 팔을 내렸을 때 칼끝이 올라간다(+Y 가 손목->손끝이므로)
lift = math.radians(SW_LIFT)
d_local = (u_t * math.cos(lift) - a_local * math.sin(lift)).normalized()
# 날 방향 = d 와 팔뚝축에 동시에 수직인 방향 중 월드에서 아래를 보는 쪽
e_local = d_local.cross(a_local).normalized()
if (HM.to_3x3() @ e_local).normalized().z > 0:
    e_local = -e_local
if abs(SW_ROLL) > 1e-6:
    R = Matrix.Rotation(math.radians(SW_ROLL), 3, d_local)
    e_local = (R @ e_local).normalized()
d_w = (HM.to_3x3() @ d_local).normalized()
e_w = (HM.to_3x3() @ e_local).normalized()
print("  [목표] 칼날 방향(뼈로컬) (%+.4f,%+.4f,%+.4f) -> 월드 REST (%+.4f,%+.4f,%+.4f)"
      % (d_local.x, d_local.y, d_local.z, d_w.x, d_w.y, d_w.z))
print("  [목표] 날 방향(뼈로컬) (%+.4f,%+.4f,%+.4f) -> 월드 REST (%+.4f,%+.4f,%+.4f)"
      % (e_local.x, e_local.y, e_local.z, e_w.x, e_w.y, e_w.z))

# 크기: 검 전체 길이가 키의 SW_LEN_R
SWS = (H * SW_LEN_R) / (T1 - T0)
SOCK = FC + Vector((0, SW_DY, 0))
P_TGT = HM @ SOCK
Fsrc = Matrix((GDIR, EDGE_DIR, GDIR.cross(EDGE_DIR))).transposed()
Fdst = Matrix((d_w, e_w, d_w.cross(e_w))).transposed()
ROT = Fdst @ Fsrc.transposed()
for v in sword.data.vertices:
    v.co = P_TGT + ROT @ ((v.co - GC) * SWS)
sword.data.update()
sword.name = sword.data.name = "SW_hero"    # ★게임이 SW_ 로 무기를 걸러낸다
vg = sword.vertex_groups.new(name=HAND)
vg.add(range(len(sword.data.vertices)), 1.0, "REPLACE")
md = sword.modifiers.new("Armature", "ARMATURE")
md.object = arm
sword.parent = arm
sword.matrix_parent_inverse = arm.matrix_world.inverted()
SWV = [v.co.copy() for v in sword.data.vertices]
tipw = P_TGT + ROT @ ((TIP - GC) * SWS)
print("  [배치] 배율 %.4f -> 검 길이 %.4f (키의 %.1f%%) / 자루 길이 %.4f 반경 %.4f"
      % (SWS, (T1 - T0) * SWS, SW_LEN_R * 100, GRIP_LEN * SWS, GRIP_R * SWS))
print("  [배치] 그립 중심(월드 REST) (%.4f,%.4f,%.4f) / 칼끝 (%.4f,%.4f,%.4f)"
      % (P_TGT.x, P_TGT.y, P_TGT.z, tipw.x, tipw.y, tipw.z))
print("  [배치] 그립 중심(뼈로컬 cm) (%.2f, %.2f, %.2f)" % (SOCK.x, SOCK.y, SOCK.z))
print("  [배치] 검 bbox z %.4f~%.4f (몸 %.4f~%.4f)"
      % (min(p.z for p in SWV), max(p.z for p in SWV), FOOT, FOOT + H))
# 자루가 주먹을 실제로 관통하는지 확인(기본 캐릭터 손은 꽉 쥔 주먹이라 구멍이 없다)
hw = [HM @ p for p in HP]
inside = 0
for p in hw:
    q = p - P_TGT
    along = q.dot(d_w)
    if abs(along) <= GRIP_LEN * SWS * 0.5:
        if (q - along * d_w).length <= GRIP_R * SWS:
            inside += 1
print("  [검산] 자루 원통 안에 들어온 손 정점 %d/%d (관통 = 쥔 것처럼 보인다)"
      % (inside, len(hw)))

# ---- 3-2) SW_LIFT 후보별 칼 높이 훑기 ----
# 검은 손 뼈에 웨이트 1.0 이라 프레임별 위치가 M_pose @ M_rest⁻¹ @ v 로 딱 떨어진다.
# 다시 굽지 않고 후보를 전부 재서 **바닥을 안 뚫는 최소 각**을 고른다.
# (칼끝이 땅에 박히면 게임에서 바로 보인다. Idle 은 몇 초씩 서 있으므로 더 치명적)
arm.data.pose_position = "POSE"
if arm.animation_data is None:
    arm.animation_data_create()
POSE_M = {}
for nm in ("Idle", "Walk", "Run"):
    act = bpy.data.actions.get(nm)
    if not act:
        continue
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass
    ms = []
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        ms.append((f, A2W @ arm.pose.bones[HAND].matrix))
    POSE_M[nm] = ms
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
HMr = A2W @ arm.pose.bones[HAND].matrix
print("  [훑기] SW_LIFT 후보별 검 최저z (바닥 %.3f). 자루 방향은 그대로 두고 각만 바꾼다"
      % FOOT)
print("        %6s %10s %10s %10s" % ("LIFT", "Idle최저", "Walk최저", "Run최저"))
for cand in (0, 15, 25, 32, 38, 45, 55, 65):
    lf = math.radians(cand)
    dl = (u_t * math.cos(lf) - a_local * math.sin(lf)).normalized()
    el = dl.cross(a_local).normalized()
    if (HM.to_3x3() @ el).normalized().z > 0:
        el = -el
    Fd = Matrix(((HM.to_3x3() @ dl).normalized(), (HM.to_3x3() @ el).normalized(),
                 (HM.to_3x3() @ dl).normalized().cross(
                     (HM.to_3x3() @ el).normalized()))).transposed()
    R2 = Fd @ Fsrc.transposed()
    loc = [P_TGT + R2 @ ((p - GC) * SWS) for p in SV]
    row = []
    for nm in ("Idle", "Walk", "Run"):
        lo = 9e9
        for f, M in POSE_M.get(nm, []):
            D = M @ HMr.inverted()
            lo = min(lo, min((D @ p).z for p in loc))
        row.append(lo)
    print("        %6d %10.4f %10.4f %10.4f%s"
          % (cand, row[0], row[1], row[2],
             "" if min(row) > FOOT else "  ★바닥 뚫음"))

# ================================================================ 4) 검증: 애니메이션
print("=" * 72)
print("[4] 애니메이션 검증 (찢어짐 = 옷 모서리 늘어남 / 뚫림 = 옷 정점이 몸 안)")
arm.data.pose_position = "POSE"
if arm.animation_data is None:
    arm.animation_data_create()
# ★모서리 늘어남 = 찢어짐. 다만 모피 끝의 1mm 짜리 모서리는 배율이 크게 나와도
#   실제로는 안 보인다. 키의 0.4%(약 6mm) 이상인 모서리만 본다.
edges = [(e.vertices[0], e.vertices[1]) for e in cloth.data.edges]
REST_L = [(cloth.data.vertices[a].co - cloth.data.vertices[b].co).length
          for a, b in edges]
ELIM = H * 0.004
EIDX = [k for k in range(len(edges)) if REST_L[k] >= ELIM]
print("  모서리 %d개 중 %.1fmm 이상 %d개만 판정 대상"
      % (len(edges), ELIM * 1000, len(EIDX)))
ISL_OF = {}
for k, s in enumerate(isl):
    for i in s:
        ISL_OF[i] = k


def use(act):
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


def eval_verts(ob, dg):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    out = [ob.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return out


NAMES = {}
for k, s in enumerate(isl):
    zs = [CV[i].z for i in s]
    NAMES[k] = "섬%d(정점%d z%.2f~%.2f)" % (k, len(s), min(zs), max(zs))
print("  %-6s %8s %8s %8s %9s %9s %9s %9s"
      % ("클립", "프레임", "최대늘음", "1.2배초과", "프레임당뚫림", "최대깊이",
         "칼끝z최저", "칼끝z최고"))
for nm in ("Idle", "Walk", "Run"):
    act = bpy.data.actions.get(nm)
    if not act:
        continue
    use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    st_max, bad = 1.0, 0
    st_worst = None
    pk_n, pk_d, nfr = 0, 0.0, 0
    pk_isl = {}
    tipz = []
    for f in range(f0, f1 + 1, max(1, (f1 - f0) // 12)):
        nfr += 1
        sc.frame_set(f)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        cw = eval_verts(cloth, dg)
        for k in EIDX:
            a, b = edges[k]
            r = (cw[a] - cw[b]).length / REST_L[k]
            if r > st_max:
                st_max = r
                st_worst = (f, k, a, REST_L[k], (cw[a] - cw[b]).length)
            if r > 1.2:
                bad += 1
        bt = BVHTree.FromObject(body, dg)
        for vi, p in enumerate(cw):
            loc, nrm, idx, dist = bt.find_nearest(body.matrix_world.inverted() @ p)
            if loc is None:
                continue
            lw = body.matrix_world @ loc
            nw = (body.matrix_world.to_3x3() @ nrm).normalized()
            d = (p - lw).dot(nw)
            if d < 0:
                pk_n += 1
                pk_d = max(pk_d, -d)
                k = ISL_OF.get(vi, -1)
                a0, a1 = pk_isl.get(k, (0, 0.0))
                pk_isl[k] = (a0 + 1, max(a1, -d))
        sv = eval_verts(sword, dg)
        tipz.append(max(p.z for p in sv))
    print("  %-6s %3d~%-4d %8.3f %8d %9.1f %9.4f %9.4f %9.4f"
          % (nm, f0, f1, st_max, bad, pk_n / nfr, pk_d, min(tipz), max(tipz)))
    for k, (c, d) in sorted(pk_isl.items(), key=lambda x: -x[1][0])[:3]:
        print("        뚫림 상위 %s  프레임당 %.1f개 최대 %.1fmm"
              % (NAMES.get(k, "?"), c / nfr, d * 1000))
    if st_worst and st_max > 1.2:
        f, k, a, r0, r1 = st_worst
        print("        최악 늘음 f%d %s  %.1fmm -> %.1fmm (정점 z %.3f)"
              % (f, NAMES.get(ISL_OF.get(a, -1), "?"), r0 * 1000, r1 * 1000,
                 CV[a].z))

# ================================================================ 5) 텍스처
print("=" * 72)
print("[5] 텍스처")
# ★게임은 재질을 MeshToonMaterial({map}) 로 갈아끼운다. 베이스컬러 말고는 안 쓴다.
#   옷의 normal / metallic_roughness / emissive, 검의 MetallicRoughness / Emit 은
#   전부 낭비다(옷 9.5MB + 검 8.0MB). 링크를 끊으면 익스포터가 안 내보낸다
#   (export_unused_images 기본 False).
# ★알파: 옷 텍스처는 JPEG(알파 없음), 검 텍스처는 PNG RGBA 지만 재질이
#   alphaMode=OPAQUE 라 알파를 안 쓴다(실측 알파 160~255, glTF 가 무시).
#   three.js MeshToonMaterial 도 transparent=false 기본이라 무시한다. JPEG 안전.
KEEP_MAT = {cloth.data.materials[0].name if cloth.data.materials else None,
            sword.data.materials[0].name if sword.data.materials else None}


def strip_material(m):
    """Principled 의 Base Color 만 남기고 나머지 입력 링크를 끊는다.

    ★Blender RNA 오브젝트는 접근할 때마다 새 래퍼가 나와서 `is` 비교가 안 먹는다.
      1차 굽기에서 이걸로 링크를 하나도 못 끊고 베이스컬러까지 통째로 날렸다.
      노드 비교는 반드시 **이름**으로."""
    if not m or not m.node_tree:
        return
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    bn = bsdf.name
    kept = None
    for l in list(nt.links):
        if l.to_node.name != bn:
            continue
        if l.to_socket.name == "Base Color":
            kept = l.from_node.name
            continue
        print("    %-18s 링크 끊음: %-16s (from %s)"
              % (m.name, l.to_socket.name, l.from_node.name))
        nt.links.remove(l)
    for key, val in (("Emission Strength", 0.0), ("Metallic", 0.0),
                     ("Roughness", 0.75), ("Specular IOR Level", 0.35)):
        s = bsdf.inputs.get(key)
        if s is not None:
            s.default_value = val
    s = bsdf.inputs.get("Emission Color")
    if s is not None:
        s.default_value = (0, 0, 0, 1)
    # 베이스컬러로 이어지는 노드만 남기고 나머지 텍스처 노드는 지운다
    keepset, stack = set(), ([kept] if kept else [])
    while stack:
        nm = stack.pop()
        if nm is None or nm in keepset:
            continue
        keepset.add(nm)
        nd = nt.nodes.get(nm)
        if nd is None:
            continue
        for i in nd.inputs:
            for l in i.links:
                stack.append(l.from_node.name)
    for nd in list(nt.nodes):
        if nd.type == "TEX_IMAGE" and nd.name not in keepset:
            print("    %-18s 텍스처 노드 제거: %s"
                  % (m.name, getattr(nd.image, "name", "?")))
            nt.nodes.remove(nd)
    print("    %-18s 남긴 베이스컬러 노드: %s" % (m.name, kept))


for ob in (cloth, sword):
    for m in ob.data.materials:
        strip_material(m)

used_imgs = []
for ob in (body, cloth, sword):
    for m in ob.data.materials:
        if not m or not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            img = getattr(nd, "image", None)
            if img is not None and img not in used_imgs:
                used_imgs.append(img)
print("  남은 이미지 %d장" % len(used_imgs))
for img in used_imgs:
    w, h = img.size
    print("    %-22s %dx%d 채널%d %s" % (img.name, w, h, img.channels, img.file_format))
    if TEX_SIZE and (w > TEX_SIZE or h > TEX_SIZE):
        k = TEX_SIZE / float(max(w, h))
        img.scale(max(1, int(round(w * k))), max(1, int(round(h * k))))
        print("      -> %dx%d 로 축소" % img.size[:])

# ================================================================ 6) 내보내기
print("=" * 72)
print("[6] 내보내기")
use(bpy.data.actions["Idle"])
sc.frame_set(int(bpy.data.actions["Idle"].frame_range[0]))
arm.data.pose_position = "POSE"
bpy.context.view_layer.update()
for a in bpy.data.actions:
    a.use_fake_user = True
print("  액션:", [a.name for a in bpy.data.actions])
print("  오브젝트:", [(o.name, o.type) for o in sc.objects])
tri = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons)
       for o in sc.objects if o.type == "MESH"}
print("  삼각형:", tri, "합계", sum(tri.values()))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB, export_format="GLB", use_selection=False,
    export_animations=True, export_animation_mode="ACTIONS",
    export_nla_strips=False, export_bake_animation=True,
    export_frame_range=False, export_yup=True,
    export_image_format=TEX_FORMAT, export_image_quality=TEX_QUALITY,
    export_jpeg_quality=TEX_QUALITY)
print("EXPORTED %s  %d bytes (%.2f MB)  TEX_SIZE=%d %s q%d"
      % (OUT_GLB, os.path.getsize(OUT_GLB), os.path.getsize(OUT_GLB) / 1e6,
         TEX_SIZE, TEX_FORMAT, TEX_QUALITY))
