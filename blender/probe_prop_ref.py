# -*- coding: utf-8 -*-
"""Meshy 원본(incoming/*.glb)을 **뉴트럴 라이트**로 렌더한다 — 판정지 1열용.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/probe_prop_ref.py -- tree rock

왜 필요한가 (2026-08-11, 12차 파도 12-소품원색)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너 판정의 기준점이 **"Meshy 에서 뽑힌 그것"** 이다. 그러니 판정지에는 그 인상을
그대로 담은 열이 있어야 하고, 그 열은 우리 파이프라인(재칠·가림·ACES)을 **한 단계도
안 지난** 그림이어야 한다.

뉴트럴 라이트의 정의 — "렌더 = 알베도" 가 되는 조명
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
확산면이 균일한 흰 환경광 L 안에 있으면 나가는 복사휘도가 **정확히 알베도 x L** 이다
(BRDF = albedo/PI, 조도 = PI x L). 그래서 흰 월드 하나만 켜고 L 을 1 로 두면
렌더 화소가 곧 텍스처 sRGB 다. 다만 그러면 형태가 안 읽혀서(그림자가 없다)
**해를 조금 섞는다** — 구 전체 평균 조도가 1.0 근처가 되도록 나눠 갖는다:

    흰 월드 0.78 + 해 0.60   ->  평균 조도 0.78 + 0.60/4 = 0.93

★뷰 트랜스폼은 **Standard** 다. Filmic/AgX/ACES 를 태우면 이 열이 "우리 화면"과
  같은 병을 앓게 되고 비교가 뜻을 잃는다.
★재질은 **베이스컬러 한 장 + 디퓨즈**로 다시 만든다. 원본 glb 에 딸려 온 노멀·
  러프니스(boulder_xl)를 태우면 게임(MeshToonMaterial map 하나)과 조건이 갈린다.
"""
import os
import sys
import math

import bpy

ROOT = "/Users/lbj/Documents/gameproject"
OUT = os.path.join(ROOT, "renders", "history", "v98_wave12", "props_raw", "ref")
PX = int(os.environ.get("PX", "640"))
SAMPLES = int(os.environ.get("SAMPLES", "48"))

# 종류 -> 원본 glb (tools/raw_props.py 의 SRC 와 같은 표. 바꾸면 둘 다 바꿔라)
SRC = {
    "tree":         "incoming/meshy_props_v3/dl_c.glb",
    "rock":         "incoming/meshy_props_v3/dl_b.glb",
    "boulder_xl":   "incoming/meshy_props_v3/dl_a.glb",
    "crag":         "incoming/meshy_props_v2/crag_v2.glb",
    "bush":         "incoming/meshy_props_v2/bush_v2.glb",
    "cliff_tall_b": "incoming/meshy_props_v2/cliff_var_v2.glb",
    # ── 2차(12-소품원색2차) ──
    "cliff_tall":   "incoming/meshy_terrain/cliff_wall_tall.glb",
    "bank":         "incoming/meshy_terrain/river_bank_stones.glb",
    "slab":         "incoming/meshy_terrain/flagstone_slab.glb",
    "thicket":      "incoming/meshy_props/thicket.glb",
    # ★outcrop 은 Meshy 원자재가 없다(s22 생성물). 이 열은 "원자재" 가 아니라
    #   **출발점**(재칠판의 가림 전 텍스처)을 보여 주는 칸이 된다 — 판정지에 그렇게 적는다.
    "outcrop":      "web/props/outcrop.glb.bak_v96ao",
}


def find_basecolor(ob):
    """베이스컬러 이미지를 찾는다(s30_props_v2.py 와 같은 절차)."""
    for slot in ob.material_slots:
        m = slot.material
        if not m or not m.node_tree:
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            li = bsdf.inputs.get("Base Color")
            if li and li.is_linked and li.links[0].from_node.type == "TEX_IMAGE":
                if li.links[0].from_node.image:
                    return li.links[0].from_node.image
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image and "base_color" in n.image.name:
                return n.image
    return None


def neutral_world():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.device = "CPU"
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.film_transparent = True
    w = bpy.data.worlds.new("W") if sc.world is None else sc.world
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.78
    li = bpy.data.lights.new("SUN", "SUN")
    li.energy = 0.60
    li.angle = math.radians(12.0)          # 조금 무른 그림자 — 뷰어 인상에 가깝다
    so = bpy.data.objects.new("SUN", li)
    so.rotation_euler = tuple(math.radians(a) for a in (46, 0, -38))
    sc.collection.objects.link(so)


def render_one(kind, path):
    bpy.ops.wm.read_homefile(use_empty=True)
    neutral_world()
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, SRC[kind]))
    # ★glTF 임포터가 'glTF_not_exported' 컬렉션에 Icosphere 를 만든다. 안 지우면 치수가 오염된다
    for o in list(bpy.context.scene.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    assert meshes, "%s: 메시가 없다" % kind
    # ★2차: 지형 원자재(cliff_wall_tall 등)는 조각이 여럿으로 들어온다. 제일 큰 것만
    #   쓰면 색 통계가 기울므로 **합친다**(이 그림은 색 인상을 보는 칸이다).
    ob = max(meshes, key=lambda o: len(o.data.vertices))
    if len(meshes) > 1:
        print("  메시 %d개 -> 합친다" % len(meshes))
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    img = find_basecolor(ob)
    assert img is not None, "%s: 베이스컬러를 못 찾았다" % kind
    m = bpy.data.materials.new("REF_" + kind.upper())
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.location = (-380, 0)
    nt.links.new(tex.outputs["Color"], dif.inputs["Color"])
    nt.links.new(dif.outputs[0], out.inputs[0])
    ob.data.materials.clear()
    ob.data.materials.append(m)

    # ── 카메라: s30_props_v2.shot 과 같은 각(yaw -28 / 앙각 22) 정사영 ──
    from mathutils import Vector
    lo = [min(v.co[i] for v in ob.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in ob.data.vertices) for i in range(3)]
    ctr = Vector([(lo[i] + hi[i]) / 2 for i in range(3)])
    rad = math.sqrt(sum((hi[i] - lo[i]) ** 2 for i in range(3))) * 0.5
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = PX
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.type = "ORTHO"
    cd.ortho_scale = rad * 2.15
    d = Vector((math.cos(math.radians(-28)) * math.cos(math.radians(22)),
                math.sin(math.radians(-28)) * math.cos(math.radians(22)),
                math.sin(math.radians(22))))
    cam.location = ctr + d * (rad * 4.0)
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("  저장", path)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    os.makedirs(OUT, exist_ok=True)
    for k in (argv or list(SRC)):
        print("\n===== %s =====" % k)
        render_one(k, os.path.join(OUT, k + ".png"))
