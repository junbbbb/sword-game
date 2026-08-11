# -*- coding: utf-8 -*-
"""ToonSoldier 원본 FBX 에서 소총이 몸과 분리 가능한지 조사한다.

배경
  web/soldier.glb 는 메시가 1개이고 소총이 손 뼈에 스킨된 채 몸과 합쳐져 있다.
  게임에서 무기를 바꿔 끼우려면(검사는 SW_<이름> 별도 스킨드 메시 7벌을 런타임
  토글한다) 소총이 별도 조각으로 떨어져야 한다.
  궁수 캐릭터에서 같은 걸 시도했다가 활이 몸과 한 재질에 루즈 아일랜드 1437개라
  분리가 불가능했던 전례가 있다. 병사도 그런지 본다.

조사 항목
  1) 오브젝트 수 - 소총이 별도 오브젝트인가
  2) 머티리얼 수 - 소총이 별도 슬롯을 쓰는가
  3) 버텍스 그룹 - 소총 정점이 어느 뼈에 몇 % 로 묶여 있는가
  4) 루즈 파트 - 연결 안 된 조각이 몇 개이고 각각 삼각형 몇 개인가
  5) UV - 소총 정점이 아틀라스의 어느 영역을 쓰는가, 몸과 겹치는가

실행: blender -b -P blender/probe_rifle.py
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

print("\n" + "=" * 72)
print("[1] 오브젝트 구성")
print("=" * 72)
by_type = defaultdict(list)
for o in sc.objects:
    by_type[o.type].append(o)
for t in sorted(by_type):
    print("  %-9s %d개: %s" % (t, len(by_type[t]), [o.name for o in by_type[t]]))

meshes = by_type.get("MESH", [])
arm = by_type["ARMATURE"][0] if by_type.get("ARMATURE") else None
print("  아마추어 본 %d개" % (len(arm.data.bones) if arm else 0))
for m in meshes:
    tri = sum(len(p.vertices) - 2 for p in m.data.polygons)
    print("  메시 '%s': 정점 %d  폴리곤 %d  삼각형 %d"
          % (m.name, len(m.data.vertices), len(m.data.polygons), tri))

mesh = meshes[0]
me = mesh.data

print("\n" + "=" * 72)
print("[2] 머티리얼")
print("=" * 72)
print("  blend 전체 머티리얼 %d개: %s"
      % (len(bpy.data.materials), [m.name for m in bpy.data.materials]))
print("  메시 '%s' 슬롯 %d개" % (mesh.name, len(mesh.material_slots)))
slot_poly = defaultdict(int)
for p in me.polygons:
    slot_poly[p.material_index] += 1
for i, s in enumerate(mesh.material_slots):
    print("    슬롯 %d: %-24s 폴리곤 %d개"
          % (i, s.material.name if s.material else "(없음)", slot_poly.get(i, 0)))

# ------------------------------------------------------------------ 루즈 파트
# 폴리곤을 공유 정점으로 묶어 연결 성분(아일랜드)을 찾는다. union-find.
print("\n" + "=" * 72)
print("[4] 루즈 파트(연결되지 않은 조각)")
print("=" * 72)
nv = len(me.vertices)
parent = list(range(nv))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra


for e in me.edges:
    union(e.vertices[0], e.vertices[1])

islands = defaultdict(list)          # root -> 정점 인덱스
for i in range(nv):
    islands[find(i)].append(i)
print("  아일랜드 %d개" % len(islands))

isl_of_vert = {}
for k, (root, vs) in enumerate(sorted(islands.items(), key=lambda kv: -len(kv[1]))):
    for v in vs:
        isl_of_vert[v] = k
isl_tri = defaultdict(int)
isl_polys = defaultdict(int)
for p in me.polygons:
    k = isl_of_vert[p.vertices[0]]
    isl_tri[k] += len(p.vertices) - 2
    isl_polys[k] += 1

# 아일랜드별 통계: 위치 bbox, 지배 버텍스그룹, UV bbox, 머티리얼 슬롯
vg_names = [g.name for g in mesh.vertex_groups]
uv_layer = me.uv_layers.active
uv_of_vert = defaultdict(list)
if uv_layer:
    for p in me.polygons:
        for li in p.loop_indices:
            uv_of_vert[me.loops[li].vertex_index].append(uv_layer.data[li].uv[:])

mw = mesh.matrix_world
rows = []
for k in range(len(islands)):
    vs = [v for v in range(nv) if isl_of_vert[v] == k]
    co = [mw @ me.vertices[v].co for v in vs]
    bb = (min(c.x for c in co), max(c.x for c in co),
          min(c.y for c in co), max(c.y for c in co),
          min(c.z for c in co), max(c.z for c in co))
    # 지배 뼈: 정점 가중치 합계가 가장 큰 그룹
    wsum = defaultdict(float)
    for v in vs:
        for g in me.vertices[v].groups:
            wsum[vg_names[g.group]] += g.weight
    top = sorted(wsum.items(), key=lambda kv: -kv[1])[:3]
    tot = sum(wsum.values()) or 1.0
    # UV bbox
    uvs = [uv for v in vs for uv in uv_of_vert.get(v, [])]
    ub = (min(u[0] for u in uvs), max(u[0] for u in uvs),
          min(u[1] for u in uvs), max(u[1] for u in uvs)) if uvs else (0, 0, 0, 0)
    slots = set()
    for p in me.polygons:
        if isl_of_vert[p.vertices[0]] == k:
            slots.add(p.material_index)
    rows.append((k, len(vs), isl_tri[k], bb, top, tot, ub, sorted(slots)))

print("  %-4s %-6s %-5s %-8s %-34s %s"
      % ("no", "정점", "삼각", "슬롯", "지배 뼈(가중치 비율)", "위치 z 범위"))
for (k, nvs, tri, bb, top, tot, ub, slots) in rows:
    tops = " ".join("%s=%.0f%%" % (n.replace("Bip001 ", ""), 100 * w / tot) for n, w in top)
    print("  %-4d %-6d %-5d %-8s %-34s z %.3f..%.3f"
          % (k, nvs, tri, str(slots), tops, bb[4], bb[5]))
    print("       위치 x %.3f..%.3f  y %.3f..%.3f  |  UV u %.3f..%.3f  v %.3f..%.3f"
          % (bb[0], bb[1], bb[2], bb[3], ub[0], ub[1], ub[2], ub[3]))

print("\n" + "=" * 72)
print("[3] 버텍스 그룹 전체")
print("=" * 72)
print("  그룹 %d개" % len(vg_names))
gcount = defaultdict(int)
for v in me.vertices:
    for g in v.groups:
        if g.weight > 0.0001:
            gcount[vg_names[g.group]] += 1
for n in vg_names:
    print("    %-26s 영향 정점 %d" % (n, gcount.get(n, 0)))

# 정점당 뼈 개수 분포
per = defaultdict(int)
for v in me.vertices:
    per[sum(1 for g in v.groups if g.weight > 0.0001)] += 1
print("  정점당 뼈 개수 분포:", dict(sorted(per.items())))

print("\nDONE")
