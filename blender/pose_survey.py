# -*- coding: utf-8 -*-
# slayer.blend 를 열어 애니메이션 여러 프레임을 한 장으로 붙여 본다(포즈 고르기용)
# 실행: blender --background --python pose_survey.py
import bpy
import os
import math

ROOT = "/Users/lbj/Documents/gameproject"
BLEND = os.path.join(ROOT, "blender/slayer.blend")
SCRATCH = "/private/tmp/claude-501/-Users-lbj/83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad/poses"
os.makedirs(SCRATCH, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
sc.render.resolution_x = 420
sc.render.resolution_y = 620

FRAMES = [1, 40, 80, 120, 160, 200, 240, 280, 320]
for f in FRAMES:
    sc.frame_set(f)
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(SCRATCH, "f%03d.png" % f)
    bpy.ops.render.render(write_still=True)
    print("frame", f)
print("DONE")
