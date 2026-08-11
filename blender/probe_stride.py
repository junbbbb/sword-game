# -*- coding: utf-8 -*-
"""glb 의 걷기·달리기 클립에서 **발이 미끄러지지 않는 이동 속도**를 잰다.

원리
  제자리 루프 애니메이션에서 접지한 발은 몸 기준으로 뒤로 밀린다.
  그 '뒤로 밀리는 속도'와 게임 이동 속도가 같아야 발이 안 미끄러진다.
  게임은 캐릭터를 특정 키로 정규화하므로, 결과는 그 키 기준으로 환산해 준다.

실행: GLB=tank.glb TARGET_H=2.0 blender -b -P probe_stride.py
"""
import bpy
import os
import sys
import math
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.environ.get("GLB", "tank.glb")
TARGET_H = float(os.environ.get("TARGET_H", "1.75"))

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "web", GLB))
arm = next(o for o in sc.objects if o.type == "ARMATURE")
# ★게임과 같은 방식으로 키를 잰다: 무기(SW_)는 빼야 한다.
# 칼 7자루가 바인드 포즈에서 위아래로 삐져나와 키가 3.912 로 부풀었고,
# 그 탓에 발 속도가 0.62 배로 과소평가됐다(1.52 vs 실제 2.45).
#
# ★★2026-08-05 발견: Icosphere 도 빼야 한다.
# Blender 의 glTF **임포터**가 뼈를 화면에 그리려고 반지름 1 짜리 Icosphere 를
# 만들어 'glTF_not_exported' 컬렉션에 넣는다. glb 안에는 없는 물건이다
# (archer/tank/slayer/원본 Meshy glb 전부 JSON 에 Icosphere 노드가 없다).
# 그런데 이걸 같이 재면 키가 몸 1.700 대신 (-1 ~ 1.700) = 2.700 이 되어
# 배율이 0.63 배로 깎이고, **발 속도가 그만큼 과소평가된다**.
# three.js 는 이 구를 아예 못 보므로 게임 배율은 몸만 기준이다.
# 이 버그 때문에 이전 측정값(검사 0.98/1.74, 탱커 1.31/1.48)도 전부 작다.
def _skip(o):
    if o.name.startswith("SW_"):
        return True
    return any(c.name == "glTF_not_exported" for c in o.users_collection)


meshes = [o for o in sc.objects if o.type == "MESH" and not _skip(o)]
zs = []
for m in meshes:
    zs += [(m.matrix_world @ v.co).z for v in m.data.vertices]
H = max(zs) - min(zs)
SCALE = TARGET_H / H                     # 게임에서 적용될 배율
print("=== %s ===" % GLB)
print("원본 키 %.3f  ->  게임 키 %.2f  (배율 %.4f)" % (H, TARGET_H, SCALE))

# 캐릭터가 바라보는 방향을 찾는다: 발가락이 발목보다 앞이다.
# ★★2026-08-05 수정: **접지한 프레임**에서 재야 한다.
# 예전엔 클립 첫 프레임에서 쟀는데, 궁수 달리기 f0 은 무릎을 접어 뒤꿈치를
# 엉덩이까지 올린 순간이라 발끝이 발목보다 **뒤**에 있었다. 그래서 FWD 가
# 통째로 뒤집혔고, '뒤로 밀리는 최장 구간'으로 접지가 아니라 **스윙**
# (공중에서 발을 앞으로 휘두르는 짧고 빠른 구간)을 잡아 속도가 3배 부풀었다.
FWD = None


def bone(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


def wp(key):
    b = bone(key)
    return (arm.matrix_world @ b.matrix).translation.copy() if b else None


FPS = sc.render.fps or 30
for act in sorted(bpy.data.actions, key=lambda a: a.name):
    if act.name not in ("Walk", "Run"):
        continue
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        rows.append((f, wp("pelvis"), wp("l foot"), wp("r foot"),
                     wp("l toe"), wp("r toe")))
    if FWD is None:
        # 발끝이 가장 낮은(=확실히 디딘) 프레임들만 골라 그때의 발끝-발목 평균.
        order = sorted(range(len(rows)), key=lambda i: min(rows[i][4].z, rows[i][5].z))
        acc = Vector((0, 0, 0))
        for i in order[:max(1, len(rows) // 4)]:
            r = rows[i]
            a, t = (r[2], r[4]) if r[4].z <= r[5].z else (r[3], r[5])
            d = t - a
            d.z = 0
            if d.length > 1e-6:
                acc += d.normalized()
        FWD = acc.normalized() if acc.length > 1e-6 else Vector((0, -1, 0))
        print("전방 FWD = (%.2f, %.2f, %.2f)" % (FWD.x, FWD.y, FWD.z))

    # ---- ①본 측정: 발끝이 바닥에 닿아 있는 구간의 기울기 ----
    # ★단조 감소 구간(아래 ②)은 접지 앞뒤의 '되돌아가는 꼬리'까지 물고 들어와
    # 속도를 낮게 잡는다. 실제로 미끄러짐을 결정하는 건 **디디고 있는 동안**의
    # 기울기다. 끝단(뒤꿈치 닿는 순간·발 떼는 순간)은 완만하므로 프레임별
    # 변화량의 **중앙값**을 쓴다(평균은 끝단에 끌려간다).
    grip = []
    for fi, ti, tag in ((2, 4, "왼발"), (3, 5, "오른발")):
        zs = [r[ti].z for r in rows]
        thr = min(zs) + 0.03 * H          # 키의 3%(1.7m 기준 5cm) 안이면 디딘 것
        on = [i for i, z in enumerate(zs) if z <= thr]
        bi, cur = [], []
        for i in on:
            if cur and i == cur[-1] + 1:
                cur.append(i)
            else:
                if len(cur) > len(bi):
                    bi = cur
                cur = [i]
        if len(cur) > len(bi):
            bi = cur
        if len(bi) < 3:
            continue
        proj = [(rows[i][fi] - rows[i][1]).dot(FWD) for i in bi]
        dd = sorted(proj[k] - proj[k + 1] for k in range(len(proj) - 1))
        med = dd[len(dd) // 2]
        grip.append((med * FPS, len(bi), tag))

    # ---- ②참고 측정: 예전 방식(단조 감소 최장 구간) ----
    best = []
    for idx, tag in ((2, "왼발"), (3, "오른발")):
        proj = [(r[idx] - r[1]).dot(FWD) for r in rows]
        # 단조 감소(뒤로 밀림) 최장 구간
        bi, cur = [], []
        for i in range(1, len(proj)):
            if proj[i] < proj[i - 1] - 1e-5:
                if not cur:
                    cur = [i - 1]
                cur.append(i)
            else:
                if len(cur) > len(bi):
                    bi = cur
                cur = []
        if len(cur) > len(bi):
            bi = cur
        if len(bi) >= 2:
            d = proj[bi[0]] - proj[bi[-1]]
            dt = (bi[-1] - bi[0]) / FPS
            best.append((d / dt, d, dt, tag))
    cycle = (f1 - f0) / FPS
    print("\n  [%s] %d프레임 = %.3f초" % (act.name, f1 - f0, cycle))
    if not grip:
        print("    접지 구간 못 찾음")
        continue
    for sp, n, tag in grip:
        print("    %s 접지 %d프레임: %.2f (원본단위)" % (tag, n, sp))
    if best:
        v2 = sum(b[0] for b in best) / len(best) * SCALE
        print("    (참고) 예전 단조감소 방식이면 %.2f" % v2)
    game_v = sum(g[0] for g in grip) / len(grip) * SCALE
    print("    -> 게임 단위 발 속도 %.2f /초" % game_v)
    print("       재생속도 1.0 이면 이동속도를 %.2f 로" % game_v)
    for ts in (0.6, 0.8, 1.2, 1.5):
        print("       재생속도 %.1f 이면 이동속도 %.2f" % (ts, game_v * ts))
