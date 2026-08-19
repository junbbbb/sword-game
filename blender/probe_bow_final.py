# -*- coding: utf-8 -*-
"""궁수 몸 메시에 **등짐으로 구워진 활**이 어느 아일랜드인지 특정한다. (정본 도구)

결과는 blender/dump_bow_verts.py 를 거쳐 blender/archer_backbow_verts.txt 에 정점
인덱스로 굳어지고, s11_archer.py 가 그 파일을 읽어 굽기 전에 지운다.

먼저 실패한 길 다섯 - 같은 길을 또 가지 않도록 남긴다
  1) **기하만 본다**: "등 뒤에서 가장 큰 아일랜드"(158정점 / 주축 0.817m)를 활로 지목했다.
     실제로는 **머리카락 가닥**이었다. 긴 머리와 활대는 기하만으로 안 갈린다.
  2) **아일랜드 평균 텍셀색 순위**: 가죽 부츠·허리띠가 활보다 갈색이라 순위가 뒤집혔다.
  3) **가까운 것끼리 번지기**: 3정점짜리 부스러기를 징검다리 삼아 머리카락까지 먹었다.
  4) **UV 아틀라스 영역**: Meshy 는 조각마다 아틀라스 여기저기에 흩어 놓아 공통 영역이 없다.
  5) **"막대 모양" 필터**: 활 손잡이·양끝 뭉치·시위 매듭이 뭉툭해서 통째로 빠졌다.

여기서 쓰는 방법(가장 단순하고 끝이 있다)
  · 몸을 둘러싼 여러 시점에서 광선을 쏴 **보이는 표면**을 훑고,
    맞은 면의 UV 를 무게중심 보간해 **그 자리의 텍셀색**을 읽는다.
    색이 머리카락(#FDFCFC)과 나무를 확실히 가른다. 이게 1)·2) 의 답이다.
  · 활이 있을 수 있는 공간(등 뒤 · 어깨~허리 높이 · 팔 폭 안)의 **작은** 아일랜드만 본다.
  · 고른 것은 지우지 않고 **멀리 치운다**(면 인덱스가 안 밀린다). 그리고 다시 훑는다.
    가려 있던 시위·안쪽 활채가 그때 드러난다. 더 안 나올 때까지 돈다.
  · 마지막으로 core 가 차지한 얇은 판(슬래브) 안의 아주 작은 조각을 마저 담는다.
    시위는 납작한 리본이라 어느 방위에서도 옆면이어서 광선이 거의 안 맞기 때문이다.
  · 표시 렌더(빨강)와 삭제 렌더(질감)를 남긴다. **눈으로 확정하는 것이 끝**이다.

★파라미터를 넓히면 오히려 나빠진다(실측)
  PADY 0.09 / SMALL 150 으로 넓히면 머리카락 가닥까지 먹어 등에 구멍이 난다.
  기본값(PADB·PADY 0.012 / SMALL 60)이 "활대는 다 지우고 몸·머리는 안 건드리는" 값이다.
  결과: 아일랜드 577 / 정점 2718 / 삼각 1620.

실행: blender --background --python blender/probe_bow_final.py
"""
import bpy
import os
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming/meshy2/Meshy_AI_Moonshadow_Ranger_biped")
BASE = "Meshy_AI_Moonshadow_Ranger_biped_Animation_%s_withSkin.glb"
OUT = os.environ.get("BOW_OUTDIR", os.path.join(ROOT, "renders/v99_wave21_bow/final"))
os.makedirs(OUT, exist_ok=True)
NMAX = int(os.environ.get("NMAX", "200"))
# 활이 있을 수 있는 공간(실측 기반). 활 core 바운딩 x -0.27~0.29 / y -0.02~0.13 /
# z 0.84~1.63 에 여유를 준 것. 팔(|x|>0.36)·다리·부츠·머리는 이 상자 밖이다.
XA, YA, ZA = 0.36, -0.03, (0.78, 1.72)
YB = 0.28
HITMIN = 10


def build():
    bpy.ops.wm.read_homefile(use_empty=True)
    s = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, BASE % "Walking_Woman"))
    for o in list(s.objects):
        if o.type == "MESH" and o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o, do_unlink=True)
    a = next(o for o in s.objects if o.type == "ARMATURE")
    m = next(o for o in s.objects if o.type == "MESH")
    a.data.pose_position = "REST"
    if a.animation_data:
        a.animation_data.action = None
    bpy.context.view_layer.update()
    return s, a, m


sc, arm, mesh = build()
me = mesh.data
mw = mesh.matrix_world
mwi = mw.inverted()
NV = len(me.vertices)
par = list(range(NV))


def find(a):
    while par[a] != a:
        par[a] = par[par[a]]
        a = par[a]
    return a


for p in me.polygons:
    vs = list(p.vertices)
    r = find(vs[0])
    for v in vs[1:]:
        rb = find(v)
        if rb != r:
            par[rb] = r
comp = {}
for i in range(NV):
    comp.setdefault(find(i), []).append(i)
tri_of = {}
for p in me.polygons:
    r = find(p.vertices[0])
    tri_of[r] = tri_of.get(r, 0) + (len(p.vertices) - 2)
WP0 = [mw @ v.co for v in me.vertices]
face_root = [find(p.vertices[0]) for p in me.polygons]

img = bpy.data.images[0]
TW, TH = img.size
TP = list(img.pixels)
NCH = img.channels
uvl = me.uv_layers.active.data


def srgb(x):
    return 12.92 * x if x <= 0.0031308 else 1.055 * (x ** (1 / 2.4)) - 0.055


def texel_at(fi, loc):
    p = me.polygons[fi]
    vs = list(p.vertices)
    lis = list(p.loop_indices)
    a = me.vertices[vs[0]].co
    for k in range(1, len(vs) - 1):
        v0 = me.vertices[vs[k]].co - a
        v1 = me.vertices[vs[k + 1]].co - a
        v2 = loc - a
        d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
        d20, d21 = v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-12:
            continue
        vv = (d11 * d20 - d01 * d21) / den
        ww = (d00 * d21 - d01 * d20) / den
        uu = 1.0 - vv - ww
        if uu < -0.02 or vv < -0.02 or ww < -0.02:
            continue
        uv = uvl[lis[0]].uv * uu + uvl[lis[k]].uv * vv + uvl[lis[k + 1]].uv * ww
        x = int(min(TW - 1, max(0, round(uv[0] * (TW - 1)))))
        y = int(min(TH - 1, max(0, round(uv[1] * (TH - 1)))))
        i = (y * TW + x) * NCH
        return (srgb(TP[i]), srgb(TP[i + 1]), srgb(TP[i + 2]))
    return None


AZ, ELS, GU, GV, DIST = 28, (-16.0, -6.0, 4.0, 14.0), 150, 170, 2.4
U0, U1 = -0.45, 0.45


def scan():
    cnt, col = {}, {}
    for ai in range(AZ):
        th = 2 * math.pi * ai / AZ
        for el in ELS:
            ph = math.radians(el)
            fw = Vector((-math.cos(th) * math.cos(ph),
                         -math.sin(th) * math.cos(ph), -math.sin(ph)))
            right = Vector((-math.sin(th), math.cos(th), 0.0))
            up = right.cross(fw).normalized()
            eye = Vector((math.cos(th) * math.cos(ph) * DIST,
                          math.sin(th) * math.cos(ph) * DIST,
                          1.25 + math.sin(ph) * DIST))
            ld = (mwi.to_3x3() @ fw).normalized()
            for iu in range(GU):
                u = U0 + (U1 - U0) * iu / (GU - 1)
                for iv in range(GV):
                    z = ZA[0] + (ZA[1] - ZA[0]) * iv / (GV - 1)
                    org = eye + right * u + up * ((z - eye.z) / up.z)
                    ok, loc, nor, fi = mesh.ray_cast(mwi @ org, ld)
                    if not ok:
                        continue
                    c = texel_at(fi, loc)
                    if c is None:
                        continue
                    r = face_root[fi]
                    cnt[r] = cnt.get(r, 0) + 1
                    a = col.setdefault(r, [0.0, 0.0, 0.0, 0])
                    a[0] += c[0]
                    a[1] += c[1]
                    a[2] += c[2]
                    a[3] += 1
    return cnt, col


picked = set()
for rnd in range(1, 12):
    cnt, col = scan()
    got = []
    for r, n_hit in cnt.items():
        if r in picked or n_hit < HITMIN:
            continue
        idx = comp[r]
        if len(idx) > NMAX or len(idx) < 3:
            continue
        xs = [WP0[i].x for i in idx]
        ys = [WP0[i].y for i in idx]
        zs = [WP0[i].z for i in idx]
        if max(abs(min(xs)), abs(max(xs))) > XA:
            continue
        if min(ys) < YA or max(ys) > YB:
            continue
        if min(zs) < ZA[0] or max(zs) > ZA[1]:
            continue
        a = col[r]
        R, G, B = a[0] / a[3], a[1] / a[3], a[2] / a[3]
        # 나무색: 붉은 쪽으로 기울었거나(가죽·나무) 어둡다(시위·그림자면)
        if not ((R - B) >= 0.05 and R <= 0.82) and not (R <= 0.45):
            continue
        got.append((r, n_hit, len(idx), tri_of.get(r, 0), R, G, B,
                    min(zs), max(zs)))
    if not got:
        print("\n[%d회차] 새 조각 없음 - 수렴" % rnd)
        break
    got.sort(key=lambda t: -t[1])
    print("\n[%d회차] 새 조각 %d개 (삼각 %d)"
          % (rnd, len(got), sum(g[3] for g in got)))
    for (r, nh, n, tr, R, G, B, z0, z1) in got[:14]:
        print("  root %-6d 화소 %5d 정점 %3d 삼각 %3d #%02X%02X%02X z %.3f~%.3f"
              % (r, nh, n, tr, int(R * 255), int(G * 255), int(B * 255), z0, z1))
    for g in got:
        picked.add(g[0])
        for i in comp[g[0]]:
            me.vertices[i].co.z += 50.0
    me.update()

# ---- 마무리: core 가 차지한 얇은 판(슬래브) 안의 작은 조각을 마저 담는다 ----
# ★시위는 납작한 리본이라 어느 방위에서 봐도 거의 옆면이다 -> 광선이 거의 안 맞아
#   HITMIN 을 못 넘고 남았다(1회차 후 렌더에 얇은 막대가 그대로 남은 이유).
#   core 159개가 그린 상자는 두께 16cm 짜리 얇은 판이라, 그 안에 통째로 들어오는
#   **아주 작은** 아일랜드는 활 부품으로 본다. 몸·옷·머리카락 판은 훨씬 커서 안 들어온다.
cp = [WP0[i] for r in picked for i in comp[r]]
PADB = float(os.environ.get("PADB","0.012"))
PADY = float(os.environ.get("PADY", "0.012"))
SB = (min(p.x for p in cp) - PADB, max(p.x for p in cp) + PADB,
      min(p.y for p in cp) - PADY, max(p.y for p in cp) + PADY,
      min(p.z for p in cp) - PADB, max(p.z for p in cp) + PADB)
SMALL = int(os.environ.get("SMALL", "60"))
print("\n[슬래브] x %.3f~%.3f y %.3f~%.3f z %.3f~%.3f / %d정점 이하 흡수"
      % (SB + (SMALL,)))
extra = []
for r, idx in comp.items():
    if r in picked or len(idx) > SMALL:
        continue
    if all(SB[0] <= WP0[i].x <= SB[1] and SB[2] <= WP0[i].y <= SB[3]
           and SB[4] <= WP0[i].z <= SB[5] for i in idx):
        extra.append(r)
print("[슬래브] +%d개 (삼각 %d)" % (len(extra), sum(tri_of.get(r, 0) for r in extra)))
picked.update(extra)

tv = sum(len(comp[r]) for r in picked)
tt = sum(tri_of.get(r, 0) for r in picked)
allp = [WP0[i] for r in picked for i in comp[r]]
print("\n[활 최종] 아일랜드 %d / 정점 %d / 삼각 %d" % (len(picked), tv, tt))
print("[바운딩] x %.3f~%.3f y %.3f~%.3f z %.3f~%.3f"
      % (min(p.x for p in allp), max(p.x for p in allp),
         min(p.y for p in allp), max(p.y for p in allp),
         min(p.z for p in allp), max(p.z for p in allp)))
print("BOW_SET=" + ",".join(str(r) for r in sorted(picked)))
with open(os.path.join(OUT, "bow_set.txt"), "w") as f:
    f.write(",".join(str(r) for r in sorted(picked)))

# -------------------------------------------------------------- 렌더 검증
VIEWS = {
    "back": ((0.0, 3.0, 0.95), (math.radians(90), 0, math.radians(180))),
    "side": ((3.0, 0.0, 0.95), (math.radians(90), 0, math.radians(90))),
    "q34":  ((2.1, 2.1, 1.10), (math.radians(90), 0, math.radians(135))),
    "rq34": ((-2.1, 2.1, 1.10), (math.radians(90), 0, math.radians(225))),
    "front": ((0.0, -3.0, 0.95), (math.radians(90), 0, 0)),
}


def shoot(s, prefix, tag):
    s.render.engine = "BLENDER_WORKBENCH"
    s.display.shading.light = "STUDIO"
    s.display.shading.color_type = "TEXTURE" if tag == "tex" else "MATERIAL"
    s.display.shading.show_shadows = False
    s.render.resolution_x = 700
    s.render.resolution_y = 900
    s.world = bpy.data.worlds.new("W")
    s.world.color = (0.10, 0.11, 0.13)
    cd = bpy.data.cameras.new("CAM")
    cam = bpy.data.objects.new("CAM", cd)
    s.collection.objects.link(cam)
    cd.type = "ORTHO"
    cd.ortho_scale = 2.0
    s.camera = cam
    for vn, (loc, rot) in VIEWS.items():
        cam.location = Vector(loc)
        cam.rotation_euler = rot
        s.render.filepath = os.path.join(OUT, "%s_%s.png" % (prefix, vn))
        bpy.ops.render.render(write_still=True)


# 원본(비교 기준)
sc, arm, mesh = build()
shoot(sc, "before", "tex")

# 표시(빨강)
sc, arm, mesh = build()
me = mesh.data
me.materials.clear()
mb = bpy.data.materials.new("BODY")
mb.diffuse_color = (0.34, 0.34, 0.37, 1)
me.materials.append(mb)
mr = bpy.data.materials.new("BOW")
mr.diffuse_color = (1.0, 0.06, 0.06, 1)
me.materials.append(mr)
for i, p in enumerate(me.polygons):
    p.material_index = 1 if face_root[i] in picked else 0
shoot(sc, "mark", "mat")

# 삭제(질감)
sc, arm, mesh = build()
me = mesh.data
kill = [i for i, p in enumerate(me.polygons) if face_root[i] in picked]
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.object.mode_set(mode="OBJECT")
for i in kill:
    me.polygons[i].select = True
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.delete(type="VERT")
bpy.ops.object.mode_set(mode="OBJECT")
print("[삭제] 면 %d -> 남은 정점 %d 면 %d"
      % (len(kill), len(me.vertices), len(me.polygons)))
shoot(sc, "after", "tex")
print("완료:", OUT)
