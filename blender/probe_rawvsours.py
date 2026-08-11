# -*- coding: utf-8 -*-
"""★결정적 비교: 무가공 렌더 vs 우리 T포즈 시트.

질문
  "우리가 T포즈를 렌더할 때 팔을 실수로 더 펴거나 늘렸는가?"

방법
  look_tpose_soldier.py 의 흐름을 그대로 복제하되, 포즈 리셋 블록(원본 72~80줄)만
  켰다 껐다 한다. 두 렌더가 픽셀 단위로 같으면 그 블록은 아무 짓도 안 한 것이다.
  덤으로 디스크에 있는 실제 시트(renders/tpose_soldier/tpose_front.png)와도 대조한다.

  변형 A raw   포즈를 전혀 안 건드림 (임포터가 남긴 상태 그대로)
  변형 B ours  원본 72~80줄과 동일:
                 액션 전부 삭제 / animation_data_clear / pose_position="REST"
                 / 모든 pose bone 의 location·quat·euler·scale 을 항등으로

  카메라·해상도·ortho_scale·텍스처·조명은 원본 스크립트와 완전히 동일하게 맞춘다.
  (front 뷰만. MARGIN 1.12, ry 1200, ortho_scale = max(폭·키 필요분))

실행: blender -b -P blender/probe_rawvsours.py
저장: renders/history/v52_proportions/raw_vs_ours/
"""
import bpy
import os
import math
import numpy as np
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
FBX = os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX")
TGA = os.path.join(PACK, "model/Materials/US_soldier_simple.tga")
OUT = os.path.join(ROOT, "renders/history/v52_proportions/raw_vs_ours")
SHEET = os.path.join(ROOT, "renders/tpose_soldier/tpose_front.png")
os.makedirs(OUT, exist_ok=True)


def build(reset_pose):
    """FBX 를 임포트하고 front 를 렌더한다. reset_pose=True 면 원본 72~80줄을 실행."""
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.fbx(filepath=FBX)
    arm = next(o for o in sc.objects if o.type == "ARMATURE")
    mesh = next(o for o in sc.objects if o.type == "MESH")

    if reset_pose:
        # ===== look_tpose_soldier.py 72~80줄 그대로 =====
        for a in list(bpy.data.actions):
            bpy.data.actions.remove(a)
        arm.animation_data_clear()
        arm.data.pose_position = "REST"
        for b in arm.pose.bones:
            b.location = (0, 0, 0)
            b.rotation_quaternion = (1, 0, 0, 0)
            b.rotation_euler = (0, 0, 0)
            b.scale = (1, 1, 1)
        # ===============================================

    # Biped 가 남기는 빈 오브젝트·조명·카메라 제거 (원본 83~89줄, 양쪽 공통)
    for o in list(sc.objects):
        if o.type not in ("ARMATURE", "MESH"):
            for ch in list(o.children):
                mw = ch.matrix_world.copy()
                ch.parent = None
                ch.matrix_world = mw
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()

    # 텍스처 (원본 196~210줄)
    img = bpy.data.images.load(TGA)
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

    # 렌더 설정 (원본 213~230줄)
    ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids
                        else "BLENDER_EEVEE")
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = True
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

    # 치수 실측 + 카메라 (원본 238~270줄, front 만)
    me = mesh.data
    mw = mesh.matrix_world
    co = [mw @ v.co for v in me.vertices]
    xs, ys, zs = [c.x for c in co], [c.y for c in co], [c.z for c in co]
    BW, H = max(xs) - min(xs), max(zs) - min(zs)
    CX = (min(xs) + max(xs)) / 2
    CY = (min(ys) + max(ys)) / 2
    CZ = (min(zs) + max(zs)) / 2
    TGT = Vector((CX, CY, CZ))
    D = max(H, BW) * 4
    MARGIN = 1.12
    w_need, h_need = BW * MARGIN, H * MARGIN
    ry = 1200
    rx = max(400, int(round(ry * w_need / h_need)))
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    cd.ortho_scale = max(w_need, h_need)
    cam.location = TGT + Vector((0, -D, 0))
    dd = TGT - cam.location
    cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()

    tag = "ours" if reset_pose else "raw"
    sc.render.filepath = os.path.join(OUT, "front_%s.png" % tag)
    bpy.ops.render.render(write_still=True)
    print("  [%s] 폭 %.4f 키 %.4f  %dx%d  ortho %.4f  타깃 (%.4f,%.4f,%.4f)"
          % (tag, BW, H, rx, ry, cd.ortho_scale, CX, CY, CZ))
    return dict(tag=tag, BW=BW, H=H, rx=rx, ry=ry, ortho=cd.ortho_scale,
                path=sc.render.filepath)


def load_rgba(p):
    im = bpy.data.images.load(p)
    iw, ih = im.size
    buf = np.empty(iw * ih * 4, dtype=np.float32)
    im.pixels.foreach_get(buf)
    bpy.data.images.remove(im)
    return buf.reshape(ih, iw, 4)


def silhouette_stats(a, name):
    al = a[:, :, 3]
    rows = np.where(al.max(axis=1) > 0.02)[0]
    cols = np.where(al.max(axis=0) > 0.02)[0]
    h, w = rows[-1] - rows[0] + 1, cols[-1] - cols[0] + 1
    print("    %-22s %4dx%-4d  실루엣 %dx%d px  픽셀수 %d"
          % (name, a.shape[1], a.shape[0], w, h, int((al > 0.5).sum())))
    return w, h, (al > 0.5)


print("\n" + "=" * 78)
print("★ 무가공(raw) vs 우리 파이프라인(ours)")
print("=" * 78)
A = build(False)
B = build(True)

print("\n[비교 1] 카메라·해상도·실측 치수")
same = True
for k in ("BW", "H", "rx", "ry", "ortho"):
    d = abs(A[k] - B[k])
    ok = d < 1e-6
    same &= ok
    print("  %-6s raw %-12.6f ours %-12.6f 차 %.3g  %s"
          % (k, A[k], B[k], d, "동일" if ok else "★다름"))

print("\n[비교 2] 렌더 실루엣")
ra, rb = load_rgba(A["path"]), load_rgba(B["path"])
wa, ha, ma = silhouette_stats(ra, "raw")
wb, hb, mb = silhouette_stats(rb, "ours")
print("    폭 raw %d vs ours %d (차 %d) | 키 raw %d vs ours %d (차 %d)"
      % (wa, wb, wa - wb, ha, hb, ha - hb))

if ra.shape == rb.shape:
    diff = int((ma ^ mb).sum())
    rgbd = float(np.abs(ra[:, :, :3] - rb[:, :, :3]).max())
    print("    ★알파 실루엣 차이 픽셀 %d개 (전체 %d, %.6f%%)"
          % (diff, ma.size, 100.0 * diff / ma.size))
    print("    ★RGB 최대 차이 %.6g" % rgbd)
    print("    -> %s" % ("두 렌더는 픽셀 단위로 동일하다" if diff == 0 and rgbd < 1e-4
                         else "★차이 있음"))
else:
    print("    ★해상도가 달라 직접 비교 불가")

print("\n[비교 3] 디스크의 실제 시트 renders/tpose_soldier/tpose_front.png")
if os.path.exists(SHEET):
    rs = load_rgba(SHEET)
    ws, hs, ms = silhouette_stats(rs, "sheet(디스크)")
    print("    시트 폭 %d 키 %d  vs  raw 폭 %d 키 %d" % (ws, hs, wa, ha))
    if rs.shape == ra.shape:
        d1 = int((ms ^ ma).sum())
        print("    ★시트 vs raw 실루엣 차이 픽셀 %d개 (%.6f%%)"
              % (d1, 100.0 * d1 / ms.size))
        print("    -> %s" % ("시트는 무가공 렌더와 동일하다" if d1 == 0 else "★차이 있음"))
    else:
        print("    해상도 다름: 시트 %s vs raw %s" % (rs.shape[:2], ra.shape[:2]))
    # 실루엣 비율로도 대조(해상도가 달라도 성립)
    print("    시트 폭/키 %.5f  |  raw 폭/키 %.5f  |  ours 폭/키 %.5f"
          % (ws / hs, wa / ha, wb / hb))
else:
    print("    시트 파일 없음: %s" % SHEET)

# 차이 시각화(있을 때만)
if ra.shape == rb.shape:
    d = np.abs(ra - rb).max(axis=2)
    if d.max() > 1e-4:
        vis = np.zeros((ra.shape[0], ra.shape[1], 4), dtype=np.float32)
        vis[:, :, 0] = (d > 1e-4).astype(np.float32)
        vis[:, :, 3] = 1.0
        im = bpy.data.images.new("D", ra.shape[1], ra.shape[0], alpha=True)
        im.pixels.foreach_set(vis.ravel())
        im.filepath_raw = os.path.join(OUT, "diff_raw_vs_ours.png")
        im.file_format = "PNG"
        im.save()
        print("\n  차이 맵 저장: %s" % im.filepath_raw)

print("\nDONE")
