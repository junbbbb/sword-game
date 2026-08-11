# -*- coding: utf-8 -*-
"""장비를 뗀 몸(bare) 에 뚫린 구멍이 어디인지 센다.

look_tpose_soldier.py MODE=bare 렌더에서 머리 정수리·뒤통수가 비어 보였다.
눈으로 본 걸 숫자로 확정한다. 판정 기준은 **경계 엣지**(면 하나에만 붙은 엣지)다.
닫힌 껍데기라면 경계 엣지가 0개여야 한다. 경계 엣지를 루프로 묶어 구멍마다
위치·크기를 찍는다.

실행: blender -b -P blender/probe_bare_holes.py
"""
import bpy
import os
from collections import defaultdict

ROOT = "/Users/lbj/Documents/gameproject"
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
FBX = os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX")

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.fbx(filepath=FBX)
mesh = next(o for o in sc.objects if o.type == "MESH")
me = mesh.data
vg = [g.name for g in mesh.vertex_groups]

# ------------------------------------------------------- 아일랜드 분류(본 스크립트와 동일)
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
order = sorted(groups.values(), key=lambda vs: -len(vs))
isl_of = {v: k for k, vs in enumerate(order) for v in vs}


def sole(vi):
    gs = [(vg[g.group], g.weight) for g in me.vertices[vi].groups if g.weight > 0.0001]
    return gs[0][0] if len(gs) == 1 and gs[0][1] > 0.999 else None


def top_bone(vs):
    w = defaultdict(float)
    for v in vs:
        for g in me.vertices[v].groups:
            w[vg[g.group]] += g.weight
    return max(w.items(), key=lambda kv: kv[1])[0] if w else "?"


LABEL = {}
for k, vs in enumerate(order):
    if k == 0:
        LABEL[k] = "body"
    elif all(sole(v) == "Bip001 R Hand" for v in vs):
        LABEL[k] = "rifle"
    elif all(sole(v) == "Bip001 Head" for v in vs):
        LABEL[k] = "helmet"
    else:
        LABEL[k] = "pouch" if top_bone(vs).endswith("Pelvis") else "pack"

mw = mesh.matrix_world

# 조각별 z 범위: 헬멧이 머리 어디를 덮고 있었는지 본다
print("\n[1] 조각별 위치 범위 (월드 좌표)")
for nm in ("body", "helmet", "pack", "pouch", "rifle"):
    vs = [v for k, g in enumerate(order) if LABEL[k] == nm for v in g]
    co = [mw @ me.vertices[v].co for v in vs]
    print("  %-7s z %.3f..%.3f  x %.3f..%.3f  y %.3f..%.3f"
          % (nm, min(c.z for c in co), max(c.z for c in co),
             min(c.x for c in co), max(c.x for c in co),
             min(c.y for c in co), max(c.y for c in co)))

# ------------------------------------------------------- 경계 엣지
body = set(order[0])
face_of_edge = defaultdict(int)
for p in me.polygons:
    if p.vertices[0] not in body:
        continue
    vs = list(p.vertices)
    for i in range(len(vs)):
        a, b = vs[i], vs[(i + 1) % len(vs)]
        face_of_edge[(min(a, b), max(a, b))] += 1

border = [e for e, c in face_of_edge.items() if c == 1]
print("\n[2] 몸(bare) 경계 엣지 %d개 / 전체 엣지 %d개" % (len(border), len(face_of_edge)))
if not border:
    print("  구멍 없음(닫힌 껍데기)")

# 경계 엣지를 정점 공유로 묶어 구멍(루프) 단위로 만든다
bv = sorted(set(v for e in border for v in e))
idx = {v: i for i, v in enumerate(bv)}
par2 = list(range(len(bv)))


def find2(a):
    while par2[a] != a:
        par2[a] = par2[par2[a]]
        a = par2[a]
    return a


for a, b in border:
    ra, rb = find2(idx[a]), find2(idx[b])
    if ra != rb:
        par2[rb] = ra
loops = defaultdict(list)
for v in bv:
    loops[find2(idx[v])].append(v)

print("\n[3] 구멍 %d개" % len(loops))
HEIGHT = max((mw @ me.vertices[v].co).z for v in body)
for n, (_, vs) in enumerate(sorted(loops.items(), key=lambda kv: -len(kv[1]))):
    co = [mw @ me.vertices[v].co for v in vs]
    zc = sum(c.z for c in co) / len(co)
    ext = max(max(c.x for c in co) - min(c.x for c in co),
              max(c.y for c in co) - min(c.y for c in co))
    print("  구멍%-2d 경계정점 %-3d  z %.3f..%.3f (중앙 %.3f, 키의 %.0f%% 높이)  최대폭 %.3f"
          % (n, len(vs), min(c.z for c in co), max(c.z for c in co), zc,
             100 * zc / HEIGHT, ext))
    print("        x %.3f..%.3f  y %.3f..%.3f"
          % (min(c.x for c in co), max(c.x for c in co),
             min(c.y for c in co), max(c.y for c in co)))

print("\nDONE  몸 키 %.3f" % HEIGHT)
