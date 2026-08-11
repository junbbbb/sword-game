# -*- coding: utf-8 -*-
# 에셋 메시의 UV 아일랜드가 몸의 어느 부위인지 매핑해서 JSON 으로 내보낸다.
# 분류 기준 = 각 정점의 지배 본(vertex group weight 최대) -> 신체 부위
# 실행: blender --background --python export_uv_map.py
import bpy
import os
import json
from collections import defaultdict

ROOT = "/Users/lbj/Documents/gameproject"
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
FBX = os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX")
OUT = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad/uvmap.json"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)

ob = next(o for o in bpy.context.scene.objects if o.type == "MESH")
me = ob.data
uvl = me.uv_layers[0]

# 정점 -> 지배 본 이름
vg_names = {g.index: g.name for g in ob.vertex_groups}
vdom = {}
for v in me.vertices:
    best, bestw = None, -1.0
    for g in v.groups:
        if g.weight > bestw:
            bestw = g.weight
            best = vg_names.get(g.group, "?")
    vdom[v.index] = best or "?"


def region_of(bone):
    b = (bone or "").lower()
    if "head" in b or "neck" in b:
        return "head"
    if "clavicle" in b:
        return "shoulder"
    if "upperarm" in b:
        return "upperarm"
    if "forearm" in b:
        return "forearm"
    if "hand" in b:
        return "hand"          # 소총도 여기 붙어 있음
    if "spine" in b or "pelvis" in b:
        return "torso"
    if "thigh" in b:
        return "thigh"
    if "calf" in b:
        return "calf"
    if "foot" in b or "toe" in b:
        return "foot"
    return "other"


faces = []
region_uv = defaultdict(lambda: [1e9, 1e9, -1e9, -1e9])   # umin vmin umax vmax
region_tris = defaultdict(int)
for p in me.polygons:
    uvs = []
    regs = defaultdict(int)
    zs = []
    for li in p.loop_indices:
        vi = me.loops[li].vertex_index
        u, v = uvl.data[li].uv
        uvs.append([round(float(u), 5), round(float(v), 5)])
        regs[region_of(vdom[vi])] += 1
        zs.append(float((ob.matrix_world @ me.vertices[vi].co).z))
    reg = max(regs.items(), key=lambda kv: kv[1])[0]
    faces.append({"uv": uvs, "region": reg, "z": round(sum(zs) / len(zs), 4)})
    region_tris[reg] += 1
    bb = region_uv[reg]
    for u, v in uvs:
        bb[0] = min(bb[0], u)
        bb[1] = min(bb[1], v)
        bb[2] = max(bb[2], u)
        bb[3] = max(bb[3], v)

# head 영역은 헬멧/얼굴이 섞여 있으니 z 로 한 번 더 쪼갠다
head_z = [f["z"] for f in faces if f["region"] == "head"]
if head_z:
    head_z.sort()
    cut = head_z[int(len(head_z) * 0.55)]
    for f in faces:
        if f["region"] == "head":
            f["region"] = "helmet" if f["z"] > cut else "face"
    region_uv = defaultdict(lambda: [1e9, 1e9, -1e9, -1e9])
    region_tris = defaultdict(int)
    for f in faces:
        region_tris[f["region"]] += 1
        bb = region_uv[f["region"]]
        for u, v in f["uv"]:
            bb[0] = min(bb[0], u)
            bb[1] = min(bb[1], v)
            bb[2] = max(bb[2], u)
            bb[3] = max(bb[3], v)

print("\n%-10s %6s   UV bbox (u0,v0,u1,v1)" % ("REGION", "TRIS"))
for r in sorted(region_tris, key=lambda k: -region_tris[k]):
    bb = region_uv[r]
    print("%-10s %6d   (%.3f, %.3f) - (%.3f, %.3f)" % (r, region_tris[r], bb[0], bb[1], bb[2], bb[3]))

with open(OUT, "w") as f:
    json.dump({"faces": faces,
               "regions": {r: {"tris": region_tris[r], "bbox": region_uv[r]} for r in region_tris}},
              f)
print("\nwrote %s (%d faces)" % (OUT, len(faces)))
