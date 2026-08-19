# -*- coding: utf-8 -*-
"""확정된 등짐 활 아일랜드(root 목록)를 **정점 인덱스 목록**으로 굳혀 파일에 적는다.

왜 root 가 아니라 정점 인덱스인가
  root 는 union-find 의 합치는 순서에 따라 달라진다(같은 메시라도 코드가 조금만
  달라지면 다른 번호가 나온다). 실제로 probe_bow_island.py 와 probe_bow_final.py 의
  합치는 순서가 달라 root 가 안 맞았다. 정점 인덱스는 **파일이 같으면 항상 같다.**
  그래서 s11_archer.py 가 읽는 정본은 정점 인덱스 목록으로 둔다.

출력: blender/archer_backbow_verts.txt
  1줄: 헤더 주석(정점수 / 삼각수 / 바운딩)
  2줄: 쉼표로 구분한 정점 인덱스

실행: BOW_SET=1,2,3 blender --background --python blender/dump_bow_verts.py
"""
import bpy
import os

ROOT = "/Users/lbj/Documents/gameproject"
SRC = os.path.join(ROOT, "incoming/meshy2/Meshy_AI_Moonshadow_Ranger_biped")
BASE = "Meshy_AI_Moonshadow_Ranger_biped_Animation_Walking_Woman_withSkin.glb"
SETF = os.environ.get("BOW_SET_FILE",
                      os.path.join(ROOT, "renders/v99_wave21_bow/final/bow_set.txt"))
OUTF = os.path.join(ROOT, "blender/archer_backbow_verts.txt")
ROOTS = set(int(x) for x in
            (os.environ.get("BOW_SET") or open(SETF).read()).strip().split(","))

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, BASE))
for o in list(sc.objects):
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        bpy.data.objects.remove(o, do_unlink=True)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH")
arm.data.pose_position = "REST"
if arm.animation_data:
    arm.animation_data.action = None
bpy.context.view_layer.update()
me = mesh.data
mw = mesh.matrix_world
NV = len(me.vertices)

# ★probe_bow_final.py 와 **같은 합치는 순서**여야 root 번호가 맞는다.
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

vids = sorted(i for i in range(NV) if find(i) in ROOTS)
tris = sum(len(p.vertices) - 2 for p in me.polygons if find(p.vertices[0]) in ROOTS)
pts = [mw @ me.vertices[i].co for i in vids]
bb = (min(p.x for p in pts), max(p.x for p in pts),
      min(p.y for p in pts), max(p.y for p in pts),
      min(p.z for p in pts), max(p.z for p in pts))
hdr = ("# 궁수 등짐 활(몸 메시에 구워진 것) 정점 목록. blender/probe_bow_final.py 가 특정했다.\n"
       "# 원본: incoming/meshy2/.../Walking_Woman_withSkin.glb 의 char1 (정점 %d)\n"
       "# 활: 아일랜드 %d개 / 정점 %d / 삼각 %d / "
       "바운딩 x %.3f~%.3f y %.3f~%.3f z %.3f~%.3f\n"
       % ((NV, len(ROOTS), len(vids), tris) + bb))
with open(OUTF, "w") as f:
    f.write(hdr)
    f.write(",".join(str(i) for i in vids) + "\n")
print(hdr.strip())
print("적었다:", OUTF)
