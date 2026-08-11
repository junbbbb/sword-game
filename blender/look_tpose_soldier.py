# -*- coding: utf-8 -*-
"""병사(ToonSoldier WW2) T 포즈 참고 시트. AI 3D 생성기 입력 이미지용.
정면/측면/후면을 배경 없이 균일 조명으로 뽑는다.

  blender -b -P blender/look_tpose_soldier.py                  # 소총 포함
  MODE=noweapon blender -b -P blender/look_tpose_soldier.py    # 소총만 제거
  MODE=nohelmet blender -b -P blender/look_tpose_soldier.py    # 소총+헬멧 제거
  MODE=bare     blender -b -P blender/look_tpose_soldier.py    # 장비 전부 제거
  DRY=1 MODE=bare blender -b -P ...                            # 분류만 찍고 렌더 생략

(WEAPON=0 은 MODE=noweapon 의 옛 표기. 그대로 동작한다.)

원본은 web/soldier.glb 가 아니라 **FBX 를 직접** 임포트한다(glb 는 다른 작업이
다시 굽는 중). 애니메이션은 붙이지 않고 바인드(레스트) 포즈 그대로 렌더한다.

★함정 1 - ortho_scale 은 렌더의 **긴 변**에 적용된다.
  세로로 긴 프레임에 키 기준 값을 주면 가로 커버리지가 모자라 T 포즈의 손이
  잘린다(검사에서 실제로 잘렸다). 뷰마다 실제 폭·두께·키를 재서 해상도와
  ortho_scale 을 맞춘다. look_tpose.py 와 같은 방식.
  병사는 소총이 오른팔 바깥으로 1.2 만큼 더 튀어나와 좌우 bbox 가 **비대칭**이다.
  그래서 카메라 타깃도 bbox 중심으로 잡아야 한다(원점 아님).

★함정 2 - 텍스처. 이 FBX 의 머티리얼은 존재하지 않는 .psd 를 가리킨다
  (임포트 직후 이미지 0x0). 옆의 US_soldier_simple.tga 를 직접 물려야
  회색 무지가 안 된다. s12_soldier.py 와 같은 처리.

★함정 3 - 장비 제거. 소총도 헬멧도 별도 오브젝트가 아니라 같은 메시 안의
  루즈 파트다. 오브젝트 모드에서 v.select 만 켜고 에디트 모드로 들어가면
  임포트 때 남은 면 선택 플래그가 다시 flush 되어 전체가 딸려나간다.
  정점·엣지·면을 모두 직접 지정해야 한다(probe_rifle2.py 에서 실제로 당했다).
  separate(type='LOOSE') 도 쓰지 않는다(16조각으로 흩어진다).

★함정 4 - 뼈 웨이트만 보고 고르면 손이 뜯긴다. 몸 아일랜드 안에도
  "R Hand 단독 100%" 정점이 10개 있는데 실제 손목·손등이다. 판정은 반드시
  **아일랜드 + 웨이트**를 같이 본다(몸 = 가장 큰 아일랜드, 여기서 나온 건 제외).

메시 구조(probe_rifle.py 로 확정, 삼각형 합 1006 / 루즈 아일랜드 16개)
  몸(얼굴·군복·바지·부츠 한 덩어리) 594 · 헬멧 92(Head 100%)
  멜빵 하네스 61(Spine 100%) · 등 배낭 56(Spine 100%)
  벨트 탄약주머니 6개 각 12(Pelvis 60/Spine 40) · 소총 6조각 131(R Hand 100%)
  옷은 못 뗀다. 재킷 표면이 곧 몸통 지오메트리라 지우면 구멍만 남는다.
"""
import bpy
import os
import math
from collections import defaultdict
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
FBX = os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX")
TGA = os.path.join(PACK, "model/Materials/US_soldier_simple.tga")

# MODE: full(그대로) / noweapon(소총) / nohelmet(소총+헬멧) / bare(장비 전부)
_LEGACY = "full" if os.environ.get("WEAPON", "1") != "0" else "noweapon"
MODE = os.environ.get("MODE", _LEGACY)
DEFAULT_DIR = {"full": "tpose_soldier", "noweapon": "tpose_soldier_noweapon",
               "nohelmet": "tpose_soldier_nohelmet", "bare": "tpose_soldier_bare"}
assert MODE in DEFAULT_DIR, "MODE 는 %s 중 하나" % list(DEFAULT_DIR)
OUTDIR = os.environ.get("OUTDIR", DEFAULT_DIR[MODE])
DRY = os.environ.get("DRY", "0") == "1"      # 분류만 확인하고 렌더 건너뛰기
print("[MODE] %s -> renders/%s%s" % (MODE, OUTDIR, "  (DRY)" if DRY else ""))

# ---------------------------------------------------------------- 임포트
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.fbx(filepath=FBX)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH")

# 바인드(레스트) 포즈 고정. 딸려온 bind take 를 지우고 아마추어도 레스트로 둔다.
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
arm.animation_data_clear()
arm.data.pose_position = "REST"
for b in arm.pose.bones:
    b.location = (0, 0, 0)
    b.rotation_quaternion = (1, 0, 0, 0)
    b.rotation_euler = (0, 0, 0)
    b.scale = (1, 1, 1)

# Biped 가 남기는 빈 오브젝트·조명·카메라 제거
for o in list(sc.objects):
    if o.type not in ("ARMATURE", "MESH"):
        for ch in list(o.children):
            mw = ch.matrix_world.copy()
            ch.parent = None
            ch.matrix_world = mw
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()

# ---------------------------------------------------------------- 조각 분류
# 루즈 아일랜드(union-find)로 조각을 나누고, 조각마다 지배 뼈를 봐서 이름을 붙인다.
# 웨이트만 보면 몸의 손목·손등(R Hand 단독 100% 10개)이 소총으로 잡혀 손이 뜯긴다.
# 그래서 "가장 큰 아일랜드 = 몸"을 먼저 빼고, 나머지에만 웨이트 규칙을 적용한다.
me = mesh.data
nv0 = len(me.vertices)
parent = list(range(nv0))


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
for i in range(nv0):
    groups[find(i)].append(i)
order = sorted(groups.values(), key=lambda vs: -len(vs))   # 0번 = 몸
vg = [g.name for g in mesh.vertex_groups]
isl_of = {v: k for k, vs in enumerate(order) for v in vs}
isl_tri = defaultdict(int)
for p in me.polygons:
    isl_tri[isl_of[p.vertices[0]]] += len(p.vertices) - 2


def sole_bone(vi):
    """이 정점이 뼈 하나에만 100% 로 묶였으면 그 뼈 이름, 아니면 None"""
    gs = [(vg[g.group], g.weight) for g in me.vertices[vi].groups if g.weight > 0.0001]
    return gs[0][0] if len(gs) == 1 and gs[0][1] > 0.999 else None


def top_bone(vs):
    """조각 전체의 가중치 합이 가장 큰 뼈"""
    w = defaultdict(float)
    for v in vs:
        for g in me.vertices[v].groups:
            w[vg[g.group]] += g.weight
    return max(w.items(), key=lambda kv: kv[1])[0] if w else "?"


LABEL = {}                                   # 아일랜드 번호 -> 이름
for k, vs in enumerate(order):
    if k == 0:
        LABEL[k] = "body"                    # 몸: 얼굴·군복·바지·부츠 한 덩어리
    elif all(sole_bone(v) == "Bip001 R Hand" for v in vs):
        LABEL[k] = "rifle"                   # 소총 6조각
    elif all(sole_bone(v) == "Bip001 Head" for v in vs):
        LABEL[k] = "helmet"                  # 헬멧
    else:
        # 하네스·배낭(Spine 100%) 과 탄약주머니(Pelvis 60/Spine 40)
        LABEL[k] = "pouch" if top_bone(vs).endswith("Pelvis") else "pack"

print("\n조각 분류 (아일랜드 %d개, 삼각형 합 %d)" % (len(order), sum(isl_tri.values())))
by_label = defaultdict(lambda: [0, 0, 0])
for k, vs in enumerate(order):
    st = by_label[LABEL[k]]
    st[0] += 1
    st[1] += len(vs)
    st[2] += isl_tri[k]
for nm in ("body", "helmet", "pack", "pouch", "rifle"):
    if nm in by_label:
        c, v, t = by_label[nm]
        print("  %-7s 조각 %d개  정점 %-5d 삼각형 %-5d  지배 뼈 %s"
              % (nm, c, v, t, top_bone([x for k, g in enumerate(order)
                                        if LABEL[k] == nm for x in g])))

# ---------------------------------------------------------------- 조각 제거
DROP = {"full": set(), "noweapon": {"rifle"},
        "nohelmet": {"rifle", "helmet"},
        "bare": {"rifle", "helmet", "pack", "pouch"}}[MODE]
kill = set(v for k, vs in enumerate(order) if LABEL[k] in DROP for v in vs)
if kill:
    print("제거 대상 %s -> 정점 %d개 삭제 (전체 %d)"
          % (sorted(DROP), len(kill), nv0))
    # ★함정: v.select 만 켜고 EDIT 로 들어가면 남아 있던 면·엣지 플래그가
    # 다시 flush 되어 전체가 딸려나간다. 세 플래그를 모두 직접 지정한다.
    for v in me.vertices:
        v.select = v.index in kill
    for e in me.edges:
        e.select = all(i in kill for i in e.vertices)
    for p in me.polygons:
        p.select = all(i in kill for i in p.vertices)
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    me = mesh.data

NTRI = sum(len(p.vertices) - 2 for p in me.polygons)
print("남은 메시: 정점 %d  삼각형 %d" % (len(me.vertices), NTRI))
EXPECT = {"full": 1006, "noweapon": 875, "nohelmet": 783, "bare": 594}[MODE]
print("  기대 삼각형 %d -> %s" % (EXPECT, "일치" if NTRI == EXPECT else "★불일치"))
if DRY:
    print("DRY 모드: 렌더 생략")
    raise SystemExit(0)

# ---------------------------------------------------------------- 텍스처
img = bpy.data.images.load(TGA)
print("텍스처 %s -> %dx%d" % (os.path.basename(TGA), img.size[0], img.size[1]))
assert img.size[0] > 0, "TGA 로드 실패"
for mat in list(bpy.data.materials):
    nt = mat.node_tree
    nt.nodes.clear()
    out_n = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs[0], out_n.inputs[0])
    print("  머티리얼 %s -> Principled + %s" % (mat.name, img.name))

# ---------------------------------------------------------------- 렌더 설정
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.film_transparent = True          # 배경 투명

# 균일 조명(그림자가 지면 생성기가 그걸 형태로 오해한다)
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.15
for i, rot in enumerate(((60, 0, -40), (60, 0, 140), (-40, 0, 40))):
    li = bpy.data.lights.new("S%d" % i, "SUN")
    li.energy = 1.2
    so = bpy.data.objects.new("S%d" % i, li)
    so.rotation_euler = tuple(math.radians(a) for a in rot)
    sc.collection.objects.link(so)

cd = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.type = "ORTHO"

# ---------------------------------------------------------------- 치수 실측
mw = mesh.matrix_world
co = [mw @ v.co for v in me.vertices]
xs = [c.x for c in co]
ys = [c.y for c in co]
zs = [c.z for c in co]
BW, BD, H = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
CX, CY, CZ = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
print("치수: 폭 %.3f  두께 %.3f  키 %.3f" % (BW, BD, H))
print("      x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f"
      % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

OUT = os.path.join(ROOT, "renders", OUTDIR)
os.makedirs(OUT, exist_ok=True)
TGT = Vector((CX, CY, CZ))
D = max(H, BW) * 4
# 뷰: (카메라 오프셋, 화면 가로로 보이는 실제 폭)
VIEWS = [("front", Vector((0, -D, 0)), BW),
         ("side", Vector((-D, 0, 0)), BD),
         ("back", Vector((0, D, 0)), BW)]
MARGIN = 1.12
for nm, off, wide in VIEWS:
    w_need = wide * MARGIN
    h_need = H * MARGIN
    ry = 1200
    rx = max(400, int(round(ry * w_need / h_need)))
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    cd.ortho_scale = max(w_need, h_need)     # 긴 변 기준이므로 큰 쪽을 준다
    cam.location = TGT + off
    dd = TGT - cam.location
    cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "tpose_%s.png" % nm)
    bpy.ops.render.render(write_still=True)
    print("  %-6s %dx%d  ortho %.3f (필요 폭 %.3f)" % (nm, rx, ry, cd.ortho_scale, w_need))

# ---------------------------------------------------------------- 픽셀 검증
# 파일이 생긴 것으로는 성공이 아니다. 알파 실루엣의 상하좌우 여백을 실제로 잰다.
# 색 편차도 같이 본다(0 에 가까우면 텍스처가 안 물려 회색 무지라는 뜻).
import numpy as np  # noqa: E402
print("\n검증(알파 실루엣 여백, 단위 px)")
for nm, _, _ in VIEWS:
    path = os.path.join(OUT, "tpose_%s.png" % nm)
    im = bpy.data.images.load(path)
    iw, ih = im.size
    buf = np.empty(iw * ih * 4, dtype=np.float32)
    im.pixels.foreach_get(buf)
    px = buf.reshape(ih, iw, 4)
    a = px[:, :, 3]
    rows = np.where(a.max(axis=1) > 0.02)[0]
    cols = np.where(a.max(axis=0) > 0.02)[0]
    m = px[:, :, :3][a > 0.5]
    chroma = float((m.max(axis=1) - m.min(axis=1)).mean()) if len(m) else 0.0
    print("  %-6s %4dx%-4d  좌 %3d  우 %3d  하 %3d  상 %3d  | 실루엣 %.1f%%  색편차 %.3f"
          % (nm, iw, ih, cols[0], iw - 1 - cols[-1], rows[0], ih - 1 - rows[-1],
             100.0 * (a > 0.5).mean(), chroma))
    bpy.data.images.remove(im)

print("DONE", OUT, "H=%.3f" % H)
