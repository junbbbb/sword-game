# -*- coding: utf-8 -*-
"""소품 메시의 가림(AO)을 텍셀마다 구워 낸다.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/s29_prop_ao.py -- rock crag ...
    (인자가 없으면 web/props/*.glb 전부)

왜 필요한가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2026-08-11 실측(11차 소품 진단). 오너 레퍼런스의 바위는 **볕 든 면이 그늘 면의
1.63배**로 밝다. 우리 소품은 **1.04배** — 사실상 명암 모델링이 없다. 원인 셋:

  · three r160 MeshToonMaterial 의 기본 램프가 **두 단(0.7 / 1.0)** 뿐이고
    뒤통수도 해의 70% 를 받는다(램버트라면 0 이다)
  · 반구광 1.55 가 방향 없는 큰 채움광이다
  · 실시간 그림자 상자가 캐릭터 ±10m 뿐이라 나머지 소품엔 그림자가 없다

셋 다 재질·조명 쪽이라 자산으로는 못 고친다. **고칠 수 있는 것은 하나** —
가림을 **베이스컬러에 미리 칠해 두는 것**이다. 롤·오버워치의 손그림 텍스처가
쓰는 바로 그 수법이고(빛을 그림에 그려 넣는다), 램프가 무엇이든 항상 보인다.

여기서 굽는 것은 **AO 한 장**이고, 칠하는 것은 tools/paint_prop_ao.py 다.
(굽기와 칠하기를 가르는 이유: 굽기는 느리고 한 번이면 되지만, 세기는 여러 번
 고쳐 보게 된다. 한 파일에 두면 세기 하나 바꿀 때마다 다시 굽는다.)

★고폴리(web/props/<종류>.glb)에서 굽는다. 게임은 저폴리를 그리지만 **텍스처는
  고폴리 것을 같이 쓴다**(web/props.js 주석). UV 배치가 같으므로 그대로 맞는다.
"""
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPS = os.path.join(ROOT, "web", "props")
OUT = os.path.join(ROOT, "blender", "tex", "prop_ao")
RES = 1024          # ★AO 는 저주파다. 2048 로 구워도 얻는 게 없고 굽는 시간만 4배다
SAMPLES = 96

# 종류별 AO 거리(m).
# ★★1차 굽기의 함정: 거리를 "물체 반지름의 1/3"(0.4~1.2m)로 잡았더니
#   cliff_tall·slab 이 **덮인 텍셀의 절반이 완전 검정(p50 = 0.000)** 으로 나왔다.
#   기둥 폭이 1.08m 인데 AO 거리가 1.2m 면 **맞은편 면이 서로를 가려서** 온 면이
#   그늘이 된다. 판석은 두께가 0.14m 라 0.4m 면 아랫면이 통째로 먹힌다.
#   AO 는 "틈새"를 찍는 자이지 "덩어리"를 찍는 자가 아니다.
# → 가로 최대치의 **12~15%** 로 내렸다. 실측으로 p50 이 0.7~0.95 에 들어온다.
DIST = {
    "tree": 0.40, "bush": 0.28, "thicket": 0.35, "rock": 0.28, "crag": 0.35,
    "cliff_tall": 0.22, "outcrop": 0.28, "boulder_xl": 0.28, "bank": 0.25, "slab": 0.15,
    # ★11-소품B 변주. cliff_tall 과 봉투가 같으므로(반너비 0.541) 거리도 같다
    "cliff_tall_b": 0.22,
}


def bake_one(kind):
    path = os.path.join(PROPS, kind + ".glb")
    if not os.path.exists(path):
        print("없음", path)
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        print("메시 없음", kind)
        return
    obj = meshes[0]
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # 구울 대상 이미지를 재질의 **활성 노드**로 꽂는다. 베이크는 활성 이미지 노드에 쓴다.
    img = bpy.data.images.new("AO_" + kind, RES, RES, alpha=False)
    if not obj.data.materials:
        obj.data.materials.append(bpy.data.materials.new("M"))
    mat = obj.data.materials[0]
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    # ★순서가 중요하다. **선택을 먼저 정리하고 그 다음에 active** 로 세워야 한다.
    #   active 를 먼저 세우면 뒤따르는 select 조작이 그것을 지워서
    #   "No active and selected image texture node found" 로 조용히 실패한다
    #   (실패해도 예외가 안 나고 흰 이미지가 저장된다 — 로그를 안 보면 못 잡는다).
    for n in mat.node_tree.nodes:
        n.select = False
    node.select = True
    mat.node_tree.nodes.active = node

    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.device = "CPU"
    sc.cycles.use_denoising = False
    # ★AO 거리는 월드 설정에 있다(베이크 타입 AO 가 이 값을 본다).
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.light_settings.distance = DIST.get(kind, 0.6)
    sc.render.bake.margin = 12           # UV 섬 밖으로 번지게 — 안 하면 이음매에 검은 실선
    # ★★UV 섬 **바깥**을 흰색으로 깔아 두고 굽는다(use_clear 를 끈다).
    #   기본값(use_clear=True)은 이미지를 **검정**으로 지우고 굽는다. 그러면 섬 바깥이
    #   0.0 이 되는데, 이 AO 를 베이스컬러에 곱하면
    #     ① 밉맵 아래 단계에서 검정이 섬 안으로 빨려 들어와 **가장자리가 탄다**
    #     ② "완전 검정 = 완전히 가려짐" 인지 "칠한 적 없음" 인지 자로 구분할 수가 없다
    #   (1차 굽기에서 rock 의 32%·cliff_tall 의 60% 가 완전 검정으로 나와 오진할 뻔했다.
    #    그 대부분은 가려진 게 아니라 **빈 UV 공간**이었다.)
    sc.render.bake.use_clear = False
    sc.render.bake.use_selected_to_active = False
    img.pixels.foreach_set([1.0] * (RES * RES * 4))
    img.update()

    print("굽는다 %s  (%d tri · %dpx · AO거리 %.2fm)"
          % (kind, len(obj.data.polygons), RES, sc.world.light_settings.distance))
    bpy.ops.object.bake(type="AO")

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, kind + ".png")
    img.filepath_raw = p
    img.file_format = "PNG"
    img.save()
    print("  저장", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    kinds = argv or sorted(f[:-4] for f in os.listdir(PROPS) if f.endswith(".glb"))
    for k in kinds:
        bake_one(k)
