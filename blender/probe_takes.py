# -*- coding: utf-8 -*-
"""원본 애니메이션 FBX 가 임포트 시 액션을 **몇 개** 만드는지 센다(숨은 테이크 감사).

왜 필요한가
  FBX 하나에 AnimationStack(테이크)이 여러 개 들어 있으면 Blender 임포터는
  스택마다 액션을 따로 만든다. 우리가 첫 액션만 집어 쓰면 나머지가 조용히 버려진다.
  s12_soldier.py 는 asset_anim.load() 로 **첫 번째** 액션만 잡으므로 여기서
  누락 여부를 반드시 확인한다.

같이 보는 것
  - 아마추어 오브젝트 월드 높이(★FBX 마다 달라서 접지 보정이 필요한 원인)
  - 클립 길이/루프 여부(마지막 프레임 == 첫 프레임인지)
  - 어떤 뼈가 얼마나 움직이는지(무슨 동작인지 글로 설명하려고)

실행: blender -b -P blender/probe_takes.py
"""
import bpy
import os
import sys

ROOT = "/Users/lbj/Documents/gameproject"
sys.path.insert(0, os.path.join(ROOT, "blender"))
import asset_anim as AA  # noqa: E402

PACK = AA.PACK
CLIPS = ["infantry_guard_idle", "infantry_combat_idle",
         "infantry_combat_run", "infantry_combat_shoot"]

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene


def fcurves_of(act):
    fcs = []
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    fcs.extend(cb.fcurves)
    except Exception:
        pass
    if not fcs:
        fcs = list(act.fcurves)
    return fcs


# ---------------------------------------------------------------- 모델 FBX 먼저
before_a = set(bpy.data.actions.keys())
bpy.ops.import_scene.fbx(filepath=os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX"))
new_a = [a for a in bpy.data.actions if a.name not in before_a]
marm = next(o for o in sc.objects if o.type == "ARMATURE")
print("[모델] ToonSoldier_WW2_demo.FBX -> 액션 %d개 %s / 아마추어 월드 z %.4f"
      % (len(new_a), [a.name for a in new_a], marm.matrix_world.translation.z))
for o in list(sc.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)

# ---------------------------------------------------------------- 애니메이션 FBX 4개
for clip in CLIPS:
    before_o = set(o.name for o in sc.objects)
    before_a = set(a.name for a in bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=os.path.join(PACK, "animation/%s.FBX" % clip))
    new_o = [o for o in sc.objects if o.name not in before_o]
    new_a = [a for a in bpy.data.actions if a.name not in before_a]
    arms = [o for o in new_o if o.type == "ARMATURE"]
    print("\n[%s]" % clip)
    print("  ★임포트가 만든 액션 %d개: %s" % (len(new_a), [a.name for a in new_a]))
    print("  오브젝트 %d개(아마추어 %d, 메시 %d, 기타 %d)"
          % (len(new_o), len(arms),
             len([o for o in new_o if o.type == "MESH"]),
             len([o for o in new_o if o.type not in ("ARMATURE", "MESH")])))
    for a in new_a:
        fr = tuple(round(float(x), 2) for x in a.frame_range)
        print("     - %-40s 프레임 %s (%d프레임) fcurve %d개"
              % (a.name, fr, int(fr[1] - fr[0]) + 1, len(fcurves_of(a))))
    for o in arms:
        act = o.animation_data.action if o.animation_data else None
        print("  아마추어 %-20s 월드 z %.4f  본 %d개  걸린 액션 %s"
              % (o.name, o.matrix_world.translation.z, len(o.data.bones),
                 act.name if act else None))

    # ---- 동작 요약: 뼈별 아마추어공간 이동 폭 ----
    src = arms[0]
    act = src.animation_data.action
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            src.animation_data.action_slot = slots[0]
    except Exception:
        pass
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    track = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        for b in src.pose.bones:
            m = src.matrix_world @ b.matrix
            track.setdefault(b.name, []).append(m.translation.copy())
    rows = []
    for bn, ps in track.items():
        amp = max((p - ps[0]).length for p in ps)
        rows.append((amp, bn))
    rows.sort(reverse=True)
    print("  움직임 큰 뼈 6개(월드 이동 폭):",
          ", ".join("%s %.3f" % (bn.replace("Bip001 ", ""), a) for a, bn in rows[:6]))
    loop = max((track[bn][-1] - track[bn][0]).length for bn in track)
    print("  루프 여부: 마지막-첫 프레임 최대 차이 %.4f (%s)"
          % (loop, "루프 완벽" if loop < 1e-4 else "루프 아님"))
    # 발 최저(발끝 뼈 기준. 정확한 접지는 s12 가 메시로 다시 잰다)
    for s in ("L", "R"):
        bn = "Bip001 %s Toe0" % s
        if bn in track:
            zs = [p.z for p in track[bn]]
            print("  %s 발끝 z %.4f ~ %.4f" % (s, min(zs), max(zs)))

    AA.drop(new_o)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)

print("\nDONE")
