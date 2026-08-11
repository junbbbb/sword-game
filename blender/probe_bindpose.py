# -*- coding: utf-8 -*-
"""병사 원본 FBX 를 **아무 가공 없이** 임포트해 바인드 포즈를 그대로 잰다.

질문
  "우리 T포즈 시트가 팔을 더 펴거나 늘렸는가?"
  이 스크립트는 대조군이다. 임포트 직후 아무것도 건드리지 않고 잰 값이
  곧 원본이 가진 바인드 포즈다. 우리 시트 값과 같으면 우리는 안 건드린 것이다.

★이 스크립트는 포즈를 절대 건드리지 않는다
  pose_position 을 설정하지 않고, 액션을 지우지 않고, 뼈 채널에 쓰지 않는다.
  임포터가 남긴 상태를 그대로 읽기만 한다. 그래야 대조군이 된다.

실행
  blender -b -P blender/probe_bindpose.py                    # 모델 FBX
  FBX=refpack/.../animation/infantry_guard_idle.FBX ANIM=1 blender -b -P ...

측정
  1) 임포트 직후 상태(pose_position, 액션, 프레임)
  2) 좌우 UpperArm/Forearm/Hand 뼈 머리 월드 좌표
     - 레스트 경로(bone.head_local)  와  현재 포즈 경로(pose_bone.matrix) 를 둘 다
     - 두 값이 다르면 임포터가 포즈를 먹인 것이다
  3) 팔꿈치 각도(180도 = 완전히 편 것)
  4) 팔 수평도(어깨->손목 벡터의 z 성분, 0 = 완전 수평)
  5) 팔 벌린 폭(메시 bbox x, 소총 제외)과 키
  6) ANIM=1 이면 전 프레임을 돌며 어깨->손목 거리가 변하는지 본다
     (뼈 길이는 애니메이션에서 안 변해야 정상. 궁수는 다리가 17% 늘어난 전례가 있다)
"""
import bpy
import os
import math
from collections import defaultdict

ROOT = "/Users/lbj/Documents/gameproject"
PACK = os.path.join(ROOT, "refpack/Assets/ToonSoldiers_WW2_demo")
FBX = os.environ.get("FBX", os.path.join(PACK, "model/ToonSoldier_WW2_demo.FBX"))
ANIM = os.environ.get("ANIM", "0") == "1"
path = FBX if os.path.isabs(FBX) else os.path.join(ROOT, FBX)

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.fbx(filepath=path)
# ★여기서부터 아무것도 건드리지 않는다. 읽기만 한다.

print("\n" + "=" * 78)
print("무가공 바인드 포즈 실측: %s" % os.path.basename(path))
print("=" * 78)

arm = next(o for o in sc.objects if o.type == "ARMATURE")
meshes = [o for o in sc.objects if o.type == "MESH"]
A2W = arm.matrix_world.copy()

# ---------------------------------------------------------------- [1] 임포트 직후 상태
print("\n[1] 임포트 직후 상태 (건드리기 전)")
print("  아마추어 '%s'  뼈 %d개  월드스케일 %.6f"
      % (arm.name, len(arm.data.bones), A2W.to_scale()[0]))
print("  pose_position = %s   <- REST 면 포즈 무시, POSE 면 포즈가 먹는다"
      % arm.data.pose_position)
ad = arm.animation_data
act = ad.action if ad else None
print("  animation_data = %s   action = %s"
      % ("있음" if ad else "없음", act.name if act else "없음"))
print("  씬 프레임 = %d  (범위 %d~%d)" % (sc.frame_current, sc.frame_start, sc.frame_end))
print("  blend 안 액션 %d개: %s" % (len(bpy.data.actions), [a.name for a in bpy.data.actions]))
cons = [(b.name, [c.type for c in b.constraints]) for b in arm.pose.bones if b.constraints]
print("  뼈 컨스트레인트: %s" % (cons if cons else "없음"))

# 포즈 채널이 항등인지 확인 (임포터가 값을 넣었는지)
nonid = []
for b in arm.pose.bones:
    if (b.location.length > 1e-6
            or abs(b.rotation_quaternion.w - 1.0) > 1e-6
            or b.rotation_quaternion.to_euler().x != 0.0 and False
            or (b.scale - __import__("mathutils").Vector((1, 1, 1))).length > 1e-6):
        nonid.append(b.name)
print("  항등이 아닌 포즈 채널 %d개%s"
      % (len(nonid), (": " + ", ".join(nonid[:6])) if nonid else " (전부 항등)"))

BONES = {b.name: b for b in arm.data.bones}
PB = {b.name: b for b in arm.pose.bones}


def rest_head(name):
    """레스트(바인드) 머리 월드 좌표"""
    return A2W @ BONES[name].head_local


def pose_head(name):
    """현재 포즈가 반영된 머리 월드 좌표"""
    return A2W @ PB[name].matrix.translation


def find(suffix):
    hits = [n for n in BONES if n.lower().endswith(suffix.lower())]
    assert len(hits) == 1, "뼈 모호 %s -> %s" % (suffix, hits)
    return hits[0]


ARMB = {s: {k: find("%s %s" % (s, k)) for k in ("UpperArm", "Forearm", "Hand")}
        for s in ("L", "R")}

# ---------------------------------------------------------------- [2] 뼈 머리 좌표
print("\n[2] 팔 뼈 머리 월드 좌표  (레스트 경로 vs 현재 포즈 경로)")
maxdiff = 0.0
for s in ("L", "R"):
    for k in ("UpperArm", "Forearm", "Hand"):
        n = ARMB[s][k]
        r, p = rest_head(n), pose_head(n)
        d = (r - p).length
        maxdiff = max(maxdiff, d)
        print("  %-22s 레스트 (%8.4f,%8.4f,%8.4f)  포즈 (%8.4f,%8.4f,%8.4f)  차 %.6f"
              % (n.replace("Bip001 ", ""), r.x, r.y, r.z, p.x, p.y, p.z, d))
print("  ★레스트 vs 포즈 최대 차이 %.6f -> %s"
      % (maxdiff, "동일(임포터가 포즈를 안 먹였다)" if maxdiff < 1e-4 else "★다르다(포즈가 먹었다)"))

# ---------------------------------------------------------------- [3][4] 각도
print("\n[3][4] 팔꿈치 각도와 수평도  (현재 포즈 기준 = 실제 렌더되는 자세)")
for s in ("L", "R"):
    sh = pose_head(ARMB[s]["UpperArm"])
    el = pose_head(ARMB[s]["Forearm"])
    wr = pose_head(ARMB[s]["Hand"])
    v1, v2 = (sh - el), (wr - el)
    cosang = v1.normalized().dot(v2.normalized())
    ang = math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
    upper, fore = (el - sh).length, (wr - el).length
    straight = (wr - sh).length
    sag = sh.z - wr.z
    horiz = (wr - sh)
    droop = math.degrees(math.atan2(sh.z - wr.z, math.hypot(wr.x - sh.x, wr.y - sh.y)))
    print("  [%s] 위팔 %.4f  팔뚝 %.4f  합 %.4f | 어깨~손목 직선 %.4f"
          % (s, upper, fore, upper + fore, straight))
    print("      팔꿈치 각도 %.2f도  (180 = 완전히 편 것, 굽힘 결손 %.2f도)"
          % (ang, 180.0 - ang))
    print("      굽힘 손실 = 합 - 직선 = %.6f  (0 이면 완전 일직선)" % (upper + fore - straight))
    print("      수평도: 어깨 z %.4f -> 손목 z %.4f  낙차 %.4f  처짐각 %.2f도"
          % (sh.z, wr.z, sag, droop))
    print("      어깨~손목 벡터 (%.4f, %.4f, %.4f)" % (horiz.x, horiz.y, horiz.z))

# ---------------------------------------------------------------- [5] 메시 치수
# ★소총 제외. 소총은 몸 메시 안에 스킨돼 있어 오브젝트로는 못 거른다.
# 루즈 아일랜드 + "R Hand 단독 100%" 웨이트로 판별한다(probe_rifle.py 로직).
print("\n[5] 메시 치수 (실제 렌더되는 평가 후 메시 = 포즈 반영)")
dg = bpy.context.evaluated_depsgraph_get()
for mo in meshes:
    me0 = mo.data
    nv = len(me0.vertices)
    par = list(range(nv))

    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for e in me0.edges:
        ra, rb = f(e.vertices[0]), f(e.vertices[1])
        if ra != rb:
            par[rb] = ra
    gg = defaultdict(list)
    for i in range(nv):
        gg[f(i)].append(i)
    isl = sorted(gg.values(), key=lambda v: -len(v))
    vg = [g.name for g in mo.vertex_groups]

    def sole(vi):
        w = [(vg[g.group], g.weight) for g in me0.vertices[vi].groups if g.weight > 1e-4]
        return w[0][0] if len(w) == 1 and w[0][1] > 0.999 else None

    def topb(vs):
        d = defaultdict(float)
        for v in vs:
            for g in me0.vertices[v].groups:
                d[vg[g.group]] += g.weight
        return max(d.items(), key=lambda kv: kv[1])[0] if d else "?"

    lab = {}
    for k, vs in enumerate(isl):
        if k == 0:
            lab[k] = "body"
        elif all((sole(v) or "").endswith("R Hand") for v in vs):
            lab[k] = "rifle"
        elif all((sole(v) or "").endswith("Head") for v in vs):
            lab[k] = "helmet"
        else:
            lab[k] = "pouch" if topb(vs).endswith("Pelvis") else "pack"
    sets = defaultdict(set)
    for k, vs in enumerate(isl):
        sets[lab[k]] |= set(vs)

    # 평가 후(모디파이어·아마추어 적용) 정점 = 실제로 렌더되는 좌표
    ev = mo.evaluated_get(dg)
    mev = ev.to_mesh()
    MWE = ev.matrix_world
    CO_E = [MWE @ v.co for v in mev.vertices]
    CO_B = [mo.matrix_world @ v.co for v in me0.vertices]   # 바인드 지오메트리
    drift = max((CO_E[i] - CO_B[i]).length for i in range(min(len(CO_E), len(CO_B))))
    print("  메시 '%s' 정점 %d  조각 %s"
          % (mo.name, nv, {k: len(v) for k, v in sets.items()}))
    print("    바인드 지오메트리 vs 평가 후 최대 어긋남 %.6f -> %s"
          % (drift, "동일" if drift < 1e-4 else "★포즈로 변형됨"))

    for tag, co in (("바인드", CO_B), ("평가후", CO_E)):
        for name, vs in (("전체", set(range(nv))),
                         ("소총제외", set(range(nv)) - sets.get("rifle", set())),
                         ("몸만", sets["body"]),
                         ("몸+헬멧", sets["body"] | sets.get("helmet", set()))):
            if not vs or max(vs) >= len(co):
                continue
            c = [co[v] for v in vs]
            w = max(x.x for x in c) - min(x.x for x in c)
            h = max(x.z for x in c) - min(x.z for x in c)
            print("    %-5s %-9s 폭 %.4f  키 %.4f  폭/키 %.4f  (x %.4f..%.4f  z %.4f..%.4f)"
                  % (tag, name, w, h, w / h,
                     min(x.x for x in c), max(x.x for x in c),
                     min(x.z for x in c), max(x.z for x in c)))
    ev.to_mesh_clear()

# ---------------------------------------------------------------- [6] 애니 프레임
if ANIM:
    print("\n[6] 애니메이션 프레임별 뼈 길이 변화 (길이는 변하면 안 된다)")
    f0, f1 = sc.frame_start, sc.frame_end
    print("  프레임 %d~%d" % (f0, f1))
    stat = defaultdict(list)
    for fr in range(f0, f1 + 1):
        sc.frame_set(fr)
        for s in ("L", "R"):
            sh = pose_head(ARMB[s]["UpperArm"])
            el = pose_head(ARMB[s]["Forearm"])
            wr = pose_head(ARMB[s]["Hand"])
            stat["%s 위팔" % s].append((el - sh).length)
            stat["%s 팔뚝" % s].append((wr - el).length)
            stat["%s 어깨~손목" % s].append((wr - sh).length)
        for s in ("L", "R"):
            th = pose_head(find("%s Thigh" % s))
            ca = pose_head(find("%s Calf" % s))
            fo = pose_head(find("%s Foot" % s))
            stat["%s 허벅지" % s].append((ca - th).length)
            stat["%s 종아리" % s].append((fo - ca).length)
    print("  %-14s %9s %9s %9s %9s" % ("항목", "최소", "최대", "변동", "변동%"))
    for k, v in stat.items():
        lo, hi = min(v), max(v)
        mark = "" if (hi - lo) / max(lo, 1e-9) < 0.005 else "   ★늘어남"
        print("  %-14s %9.4f %9.4f %9.4f %8.2f%%%s"
              % (k, lo, hi, hi - lo, 100 * (hi - lo) / max(lo, 1e-9), mark))

print("\nDONE")
