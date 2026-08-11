# -*- coding: utf-8 -*-
"""소총 분리 2차 조사: UV 아틀라스 실제 겹침 + 실제 분리 실행 검증.

1차(probe_rifle.py) 결과
  메시 1개 / 머티리얼 1개 / 루즈 아일랜드 16개.
  아일랜드 4~9 는 전부 "Bip001 R Hand" 100% 이고 몸(아일랜드 0)과 연결되어 있지
  않다. 이게 소총으로 보인다. 여기서 확정하고 실제로 떼본다.

확인
  A) 소총 판정 규칙: 몸과 연결 안 됨 + 모든 정점이 R Hand 단일 뼈 100%
  B) UV 겹침: bbox 가 아니라 실제 삼각형을 256x256 격자에 래스터라이즈해
     소총이 쓰는 칸과 몸이 쓰는 칸이 겹치는지 센다
  C) 실제 분리: separate(type='LOOSE') 대신 판정된 정점만 골라 P 분리하고
     양쪽 삼각형 수와 치수를 잰다

실행: blender -b -P blender/probe_rifle2.py
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

# ----------------------------------------------------------- 아일랜드 재계산
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
isl_of = {}
for k, vs in enumerate(order):
    for v in vs:
        isl_of[v] = k

body_isl = 0  # 가장 큰 아일랜드 = 몸


def only_rhand(vi):
    """이 정점이 R Hand 하나에만 100% 로 묶였는가"""
    gs = [(vg[g.group], g.weight) for g in me.vertices[vi].groups if g.weight > 0.0001]
    return len(gs) == 1 and gs[0][0] == "Bip001 R Hand" and gs[0][1] > 0.999


print("\n[A] 소총 판정 (몸과 미연결 + R Hand 단독 100%)")
rifle_isl = []
for k, vs in enumerate(order):
    if k == body_isl:
        continue
    if all(only_rhand(v) for v in vs):
        rifle_isl.append(k)
print("  소총 아일랜드:", rifle_isl)
rifle_verts = set(v for k in rifle_isl for v in order[k])
print("  소총 정점 %d / 전체 %d" % (len(rifle_verts), nv))
# 몸쪽에 R Hand 100% 인 정점이 있는지(손 자체와 헷갈리면 안 된다)
body_rhand = [v for v in order[body_isl] if only_rhand(v)]
print("  몸 아일랜드 안의 R Hand 단독 100%% 정점 %d개 (실제 손목·손등)" % len(body_rhand))

# ----------------------------------------------------------- UV 실제 겹침
print("\n[B] UV 아틀라스 겹침 (256x256 격자 래스터라이즈)")
N = 256
uvl = me.uv_layers.active.data
grid_r = set()
grid_b = set()
tri_uv = []
for p in me.polygons:
    is_r = p.vertices[0] in rifle_verts
    loops = list(p.loop_indices)
    # n각형을 팬 삼각분할
    for a in range(1, len(loops) - 1):
        t = [uvl[loops[0]].uv, uvl[loops[a]].uv, uvl[loops[a + 1]].uv]
        tri_uv.append((is_r, [(u[0], u[1]) for u in t]))

for is_r, t in tri_uv:
    xs = [p[0] for p in t]
    ys = [p[1] for p in t]
    i0, i1 = int(min(xs) * N), int(max(xs) * N) + 1
    j0, j1 = int(min(ys) * N), int(max(ys) * N) + 1
    (ax, ay), (bx, by), (cx, cy) = t
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    tgt = grid_r if is_r else grid_b
    for i in range(max(0, i0), min(N, i1)):
        for j in range(max(0, j0), min(N, j1)):
            px, py = (i + 0.5) / N, (j + 0.5) / N
            if abs(den) < 1e-12:
                continue
            w1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
            w2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
            w3 = 1 - w1 - w2
            if w1 >= -0.001 and w2 >= -0.001 and w3 >= -0.001:
                tgt.add((i, j))

both = grid_r & grid_b
print("  소총이 쓰는 칸 %d, 몸이 쓰는 칸 %d, 겹치는 칸 %d (%.2f%%)"
      % (len(grid_r), len(grid_b), len(both),
         100.0 * len(both) / max(1, len(grid_r))))
if grid_r:
    print("  소총 UV 영역 u %.3f..%.3f  v %.3f..%.3f"
          % (min(i for i, j in grid_r) / N, (max(i for i, j in grid_r) + 1) / N,
             min(j for i, j in grid_r) / N, (max(j for i, j in grid_r) + 1) / N))

# ----------------------------------------------------------- 실제 분리
print("\n[C] 실제 분리 실행")
mw = mesh.matrix_world


def dims(obj):
    co = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return (max(c.x for c in co) - min(c.x for c in co),
            max(c.y for c in co) - min(c.y for c in co),
            max(c.z for c in co) - min(c.z for c in co),
            min(c.z for c in co), max(c.z for c in co),
            min(c.x for c in co), max(c.x for c in co),
            min(c.y for c in co), max(c.y for c in co))


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


d = dims(mesh)
print("  분리 전 전체: 삼각형 %d, 폭(x) %.3f  두께(y) %.3f  키(z) %.3f"
      % (tris(mesh), d[0], d[1], d[2]))
print("           x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f"
      % (d[5], d[6], d[7], d[8], d[3], d[4]))

# ★함정: 오브젝트 모드에서 v.select 만 켜고 에디트 모드로 들어가면,
# 임포트 직후 남아 있던 **면·엣지 선택 플래그**가 다시 정점으로 flush 되어
# 결국 전체가 선택된다(실제로 한 번 전부 딸려나갔다).
# 정점·엣지·면 세 가지를 모두 직접 지정해야 한다.
for v in me.vertices:
    v.select = v.index in rifle_verts
for e in me.edges:
    e.select = all(i in rifle_verts for i in e.vertices)
for p in me.polygons:
    p.select = all(i in rifle_verts for i in p.vertices)
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.separate(type="SELECTED")
bpy.ops.object.mode_set(mode="OBJECT")

parts = [o for o in sc.objects if o.type == "MESH"]
print("  분리 후 메시 오브젝트 %d개" % len(parts))
for o in parts:
    if len(o.data.vertices) == 0:
        print("    %-32s 정점 0 (빈 오브젝트)" % o.name)
        continue
    dd = dims(o)
    print("    %-32s 정점 %-5d 삼각형 %-5d  x %.3f..%.3f  z %.3f..%.3f"
          % (o.name, len(o.data.vertices), tris(o), dd[5], dd[6], dd[3], dd[4]))
    # 아마추어 모디파이어·버텍스그룹이 살아있는지
    mods = [m.type for m in o.modifiers]
    used = set()
    for v in o.data.vertices:
        for g in v.groups:
            if g.weight > 0.0001:
                used.add(o.vertex_groups[g.group].name)
    print("      모디파이어 %s / 실제 쓰는 뼈 %s" % (mods, sorted(used)))

print("\nDONE")
