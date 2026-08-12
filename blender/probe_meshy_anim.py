# -*- coding: utf-8 -*-
"""Meshy 애니메이트 프리셋(incoming/meshy_anim/*.glb)의 뼈대·레스트·클립을 실측한다.

    blender -b -P blender/probe_meshy_anim.py

목적 (13-모션이식, 2026-08-12)
  오너 "베는 모션을 meshy ai로 해와" -> 받아온 sword_slash / axe_chop / left_slash 를
  게임 basic2 의 Z/X/C 에 이식하기 전에, **이 스켈레톤이 우리 것과 같은 물건인지**를
  먼저 증명한다(다르면 s24 식 레스트 델타 리타게팅이 필요하다).

찍는 것
  1) 파일별 뼈 이름·계층·개수, 액션 이름·프레임 범위·길이(초)
  2) 타깃(web/basic2_body.glb)·현행 소스(web/slayer.glb) 와의 뼈 이름 교집합
  3) 레스트 포즈 월드 각도 차(같은 뼈끼리 축을 재서 도 단위로)
  4) 클립별 오른손 뼈의 월드 궤적 — 손 로컬 +Y(칼 방향 대용) 끝점 속도로
     "임팩트 프레임"이 어디인지 찾는다
"""
import bpy
import os
import math
import json
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"
ANIM = os.path.join(ROOT, "incoming", "meshy_anim")
OUT = os.environ.get("OUT_JSON", "/private/tmp/claude-501/-Users-lbj/"
                     "83528719-e722-44e4-9cc6-5a3da35ecb4b/scratchpad/meshy_probe.json")

FILES = ["sword_slash", "axe_chop", "left_slash", "character", "walking", "running"]


def act_fcurves(a):
    """★블렌더 4.4+ 는 액션이 슬롯/레이어로 쪼개져 a.fcurves 가 없다."""
    fcs = list(getattr(a, "fcurves", []) or [])
    if fcs:
        return fcs
    for lay in getattr(a, "layers", []):
        for st in getattr(lay, "strips", []):
            for slot in getattr(a, "slots", []):
                cb = st.channelbag(slot)
                if cb:
                    fcs.extend(list(cb.fcurves))
    return fcs


def fresh():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0


def imp(path):
    sc = bpy.context.scene
    b_o = set(o.name for o in sc.objects)
    b_a = set(a.name for a in bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    if sc.render.fps != 30:
        sc.render.fps = 30
    objs = [o for o in sc.objects if o.name not in b_o]
    acts = [a for a in bpy.data.actions if a.name not in b_a]
    arm = None
    for o in objs:
        if o.type == 'ARMATURE':
            arm = o
            break
    return objs, acts, arm


def bone_info(arm):
    """뼈 이름 -> (부모, 월드 head, 월드 tail, 월드 회전행렬)"""
    M = arm.matrix_world
    out = {}
    for b in arm.data.bones:
        wm = M @ b.matrix_local
        out[b.name] = {
            "parent": b.parent.name if b.parent else None,
            "head": list(M @ b.head_local),
            "tail": list(M @ b.tail_local),
            "len": (b.tail_local - b.head_local).length * M.to_scale()[0],
            "rot": [list(r) for r in wm.to_3x3().normalized()],
        }
    return out


def hier(info):
    """계층을 들여쓰기 문자열로"""
    kids = {}
    roots = []
    for n, d in info.items():
        if d["parent"] is None:
            roots.append(n)
        else:
            kids.setdefault(d["parent"], []).append(n)
    lines = []

    def walk(n, dep):
        lines.append("  " * dep + n)
        for k in sorted(kids.get(n, [])):
            walk(k, dep + 1)
    for r in sorted(roots):
        walk(r, 0)
    return lines


report = {}
print("=" * 78)

# ── 1) Meshy 애니 파일들 ──────────────────────────────────────────
for stem in FILES:
    p = os.path.join(ANIM, stem + ".glb")
    if not os.path.exists(p):
        continue
    fresh()
    objs, acts, arm = imp(p)
    meshes = [o for o in objs if o.type == 'MESH']
    info = bone_info(arm) if arm else {}
    d = {
        "bones": sorted(info.keys()),
        "nbones": len(info),
        "meshes": [(m.name, len(m.data.vertices), len(m.vertex_groups)) for m in meshes],
        "actions": [],
        "hier": hier(info) if info else [],
        "restinfo": info,
        "arm_scale": list(arm.matrix_world.to_scale()) if arm else None,
    }
    for a in acts:
        fr = a.frame_range
        fcs = act_fcurves(a)
        d["actions"].append({
            "name": a.name,
            "f0": fr[0], "f1": fr[1],
            "sec": (fr[1] - fr[0]) / 30.0,
            "nfcurves": len(fcs),
            "paths": sorted(set(fc.data_path.split('"')[1] for fc in fcs
                                if '"' in fc.data_path))[:40],
        })
    report[stem] = d
    print("── %s" % stem)
    print("   뼈 %d개 / 메시 %s / 아마추어 스케일 %s"
          % (d["nbones"], d["meshes"], d["arm_scale"]))
    for a in d["actions"]:
        print("   액션 '%s'  프레임 %.1f~%.1f (%.3f초)  fcurve %d"
              % (a["name"], a["f0"], a["f1"], a["sec"], a["nfcurves"]))

# ── 2) 우리 파일들 ────────────────────────────────────────────────
for stem, p in (("basic2_body", os.path.join(ROOT, "web", "basic2_body.glb")),
                ("slayer", os.path.join(ROOT, "web", "slayer.glb"))):
    if not os.path.exists(p):
        continue
    fresh()
    objs, acts, arm = imp(p)
    info = bone_info(arm) if arm else {}
    report[stem] = {
        "bones": sorted(info.keys()),
        "nbones": len(info),
        "actions": [{"name": a.name, "f0": a.frame_range[0], "f1": a.frame_range[1],
                     "sec": (a.frame_range[1] - a.frame_range[0]) / 30.0} for a in acts],
        "hier": hier(info),
        "restinfo": info,
        "arm_scale": list(arm.matrix_world.to_scale()) if arm else None,
    }
    print("── %s : 뼈 %d개, 액션 %s"
          % (stem, len(info), [a.name for a in acts]))

# ── 3) 뼈 이름 대조 ───────────────────────────────────────────────
print("=" * 78)
src = set(report.get("sword_slash", {}).get("bones", []))
dst = set(report.get("basic2_body", {}).get("bones", []))
sla = set(report.get("slayer", {}).get("bones", []))
print("[대조] meshy_anim 뼈 %d / basic2_body 뼈 %d / slayer 뼈 %d"
      % (len(src), len(dst), len(sla)))
print("  meshy∩basic2 = %d" % len(src & dst))
print("  meshy 에만  : %s" % sorted(src - dst))
print("  basic2 에만 : %s" % sorted(dst - src))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
print("[저장] %s" % OUT)
