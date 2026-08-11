# -*- coding: utf-8 -*-
"""CMU 검술 모캡을 우리 리그에 얹어 눈으로 확인한다.
실행: CLIP=02_07 F0=0 N=12 STEP=12 blender -b -P look_mocap.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import importlib
import combo_poses as CP
import mocap_asf as MA
importlib.reload(CP)
importlib.reload(MA)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "blender", "slayer.blend"))
sc = bpy.context.scene
ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
xs = [(mesh.matrix_world @ v.co).x for v in mesh.data.vertices]
H = max(zs) - min(zs)
FOOT = min(zs)
CX = (min(xs) + max(xs)) / 2
ps = CP.Poser(arm, H)

CLIP = os.environ.get("CLIP", "02_07")
sk = MA.Skel(os.path.join(ROOT, "mocap", "02.asf"))
F0 = int(os.environ.get("F0", "0"))
N = int(os.environ.get("N", "12"))
STEP = int(os.environ.get("STEP", "12"))
frames = MA.read_amc(os.path.join(ROOT, "mocap", CLIP + ".amc"),
                     limit=F0 + N * STEP + 2)
GRIP = os.environ.get("GRIP", "1") == "1"

li = bpy.data.lights.new("S", "SUN"); li.energy = 4.0
so = bpy.data.objects.new("S", li)
so.rotation_euler = (math.radians(58), 0, math.radians(-30))
sc.collection.objects.link(so)
li2 = bpy.data.lights.new("F", "SUN"); li2.energy = 1.5; li2.color = (0.7, 0.82, 1.0)
so2 = bpy.data.objects.new("F", li2)
so2.rotation_euler = (math.radians(-30), 0, math.radians(130))
sc.collection.objects.link(so2)
cam = sc.camera
if cam is None:
    cd = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
TGT = Vector((CX, 0, FOOT + H * 0.60))
D = H * 2.6
VIEWS = {"q": Vector((-D * 0.68, -D * 0.68, H * 0.18)),
         "side": Vector((-D, 0, H * 0.08))}
OUT = os.path.join(ROOT, "renders", "history", "v37_mocap")
os.makedirs(OUT, exist_ok=True)
sc.render.resolution_x, sc.render.resolution_y = 460, 700

for i in range(N):
    fi = F0 + i * STEP
    if fi >= len(frames):
        break
    ps.reset()
    MODE = os.environ.get("MODE", "kendo")
    MCL = set(["pelvis","spine","l thigh","l calf","l foot","l toe0",
               "r thigh","r calf","r foot","r toe0"])
    MCA = set(["l clavicle","l upperarm","l forearm","l hand",
               "r clavicle","r upperarm","r forearm","r hand"])
    MA.apply_frame(ps, sk, frames[fi], parts=(MCL | MCA) if MODE == "full" else MCL)
    ps.apply({"b": [("spine", CP.X, -12)]}, reset=False)
    if MODE == "full":
        bd = MA.blade_dir(sk, frames[fi])
        ops = [("neck", CP.AIM, (0.0, 1.0, 0.22)),
               ("head", CP.AIM, (0.0, 1.0, -0.04)),
               ("head", CP.FACE, (0.0, 0.0, 1.0))]
        if bd is not None:
            ops.append(("r hand", CP.BLADE,
                        (bd.dot(CP.RIGHT), bd.dot(CP.UP), bd.dot(CP.FWD), 55.0)))
        ops.append(("l", CP.GRIP, CP.GB))
        ps.apply({"b": ops}, reset=False)
    else:
        KEYS=[(1,"chudan"),(12,"raise"),(22,"jodan"),(26,"strike"),(32,"settle"),(44,"chudan")]
        of=(fi-60)//4+1
        a=b=KEYS[-1][1]; t=0.0
        for k in range(len(KEYS)-1):
            if KEYS[k][0]<=of<=KEYS[k+1][0]:
                t=(of-KEYS[k][0])/float(max(1,KEYS[k+1][0]-KEYS[k][0])); a,b=KEYS[k][1],KEYS[k+1][1]; break
        ps.apply({"b": CP.kendo_arms(a,b,t)}, reset=False)
    bpy.context.view_layer.update()
    # 모캡은 루트 위치를 안 옮기므로 발이 뜨거나 잠긴다. 최저점을 바닥에 맞춘다.
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    lo = min((ev.matrix_world @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    arm.location = ps.home + Vector((0, 0, FOOT - lo))
    bpy.context.view_layer.update()
    for nm, off in VIEWS.items():
        cam.location = TGT + off
        dd = TGT - cam.location
        cam.rotation_euler = dd.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, "%s_%s_%04d.png" % (CLIP, nm, fi))
        bpy.ops.render.render(write_still=True)
print("DONE", OUT)
