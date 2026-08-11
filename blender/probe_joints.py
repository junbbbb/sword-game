# -*- coding: utf-8 -*-
"""관절별 전수 검증. 모든 액션의 모든 키프레임에서 관절 각도를 재고
사람 가동범위(AAOS 표준)와 대조한다.

기준값 출처: AAOS 정상 가동범위표
  어깨 굴곡 0~180 / 신전 0~60 / 외전 0~180
  팔꿈치 굴곡 0~150 / 신전 0 (과신전 불가)
  손목 굴곡 0~80 / 신전 0~70 / 요측 0~20 / 척측 0~30
  고관절 굴곡 0~120 / 신전 0~30 / 외전 0~45
  무릎 굴곡 0~135 / 신전 0
  목 굴곡 70~90 / 신전 55 / 측굴 35 / 회전 70
  체간 굴곡 75 / 신전 30 / 측굴 35 / 회전 45

각도 정의(우리 리그에서 잴 수 있는 형태로)
  팔꿈치/무릎 = 세 점이 이루는 각. 180 이면 완전히 펴짐 -> 굴곡각 = 180 - 각
  어깨 굴곡 = 위팔이 몸통 축에서 앞으로 벌어진 각
  어깨 외전 = 위팔이 몸통 축에서 옆으로 벌어진 각
  손목 = 팔뚝 방향과 손 방향의 각
  목/체간 = 뼈 방향이 수직에서 기운 각 (앞/뒤, 좌/우)
실행: blender -b -P probe_joints.py
"""
import bpy
import os
import sys
import math
import json
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import importlib
import combo_poses as CP
import asset_anim as AA
importlib.reload(CP)
importlib.reload(AA)

bpy.ops.wm.open_mainfile(filepath=os.path.join(BLD, "slayer.blend"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
mesh = next(o for o in sc.objects if o.type == "MESH"
            and not o.name.startswith(("Floor", "Plane", "hl", "hair",
                                       "bladeK", "gripK", "tsubaK", "pomK", "ringK")))
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
H = max(zs) - min(zs)
ps = CP.Poser(arm, H)
R, U, F = CP.RIGHT, CP.UP, CP.FWD

# 관절: 이름 -> (한계 설명, 최소, 최대)
LIMIT = {
    "팔꿈치 굴곡": (0, 150),
    "무릎 굴곡": (0, 135),
    "어깨 굴곡/신전": (-60, 180),      # 음수 = 뒤로(신전)
    # 음수는 내전(팔이 몸 쪽으로). 내전도 정상 동작이라 0 을 하한으로 두면
    # 팔을 몸 앞으로 모으는 자세가 전부 "위반"으로 나온다(내 잣대 오류였다).
    "어깨 외전/내전": (-45, 180),
    "손목 꺾임": (0, 80),
    "목 앞뒤": (-55, 90),              # 음수 = 뒤로 젖힘
    "목 좌우": (-35, 35),
    "목 회전": (-70, 70),
    "체간 앞뒤": (-30, 75),
    "체간 좌우": (-35, 35),
    "고관절 굴곡/신전": (-30, 120),
}


def ang(a, b, c):
    u, v = (a - b), (c - b)
    if u.length < 1e-9 or v.length < 1e-9:
        return 180.0
    return math.degrees(u.angle(v))


def measure():
    """현재 포즈의 관절 각도 전부."""
    out = {}
    # 체간 기준축 (골반 -> 목)
    pel, nk = ps.wpos("pelvis"), ps.wpos("neck")
    trunk = (nk - pel).normalized()
    out["체간 앞뒤"] = math.degrees(math.atan2(trunk.dot(F), trunk.dot(U)))
    out["체간 좌우"] = math.degrees(math.atan2(trunk.dot(R), trunk.dot(U)))
    nd = ps.bone_dir("neck")
    if nd:
        out["목 앞뒤"] = math.degrees(math.atan2(nd.dot(F), nd.dot(U))) - out["체간 앞뒤"]
        out["목 좌우"] = math.degrees(math.atan2(nd.dot(R), nd.dot(U))) - out["체간 좌우"]
    hb = ps.pb("head")
    if hb:
        m = (ps.A2W @ hb.matrix).to_3x3()
        fd = (m @ CP.HEAD_FACE_LOCAL).normalized()
        out["목 회전"] = math.degrees(math.atan2(fd.dot(R), fd.dot(F)))
    for s, tag in (("l", "왼"), ("r", "오른")):
        sh, el, wr = (ps.wpos("%s upperarm" % s), ps.wpos("%s forearm" % s),
                      ps.wpos("%s hand" % s))
        if sh and el and wr:
            out["%s 팔꿈치 굴곡" % tag] = 180.0 - ang(sh, el, wr)
            ua = (el - sh).normalized()
            # 몸통 축 기준으로 분해. 위팔이 아래를 향하면 0 도
            down = -trunk
            fwd = (F - trunk * F.dot(trunk)).normalized()
            lat = (R * (1 if s == "r" else -1))
            lat = (lat - trunk * lat.dot(trunk)).normalized()
            out["%s 어깨 굴곡/신전" % tag] = math.degrees(
                math.atan2(ua.dot(fwd), ua.dot(down)))
            out["%s 어깨 외전/내전" % tag] = math.degrees(
                math.atan2(ua.dot(lat), ua.dot(down)))
        pw = ps.palm_world(s)
        if el and wr and pw:
            a = (wr - el)
            b = (pw - wr)
            if a.length > 1e-9 and b.length > 1e-9:
                out["%s 손목 꺾임" % tag] = math.degrees(a.angle(b))
        hip, kn, an = (ps.wpos("%s thigh" % s), ps.wpos("%s calf" % s),
                       ps.wpos("%s foot" % s))
        if hip and kn and an:
            out["%s 무릎 굴곡" % tag] = 180.0 - ang(hip, kn, an)
            th = (kn - hip).normalized()
            down = -trunk
            fwd = (F - trunk * F.dot(trunk)).normalized()
            out["%s 고관절 굴곡/신전" % tag] = math.degrees(
                math.atan2(th.dot(fwd), th.dot(down)))
    return out


BLADE_L = None


def blade_tip():
    """칼끝 위치(몸통 기준 r,u,f). 칼 오브젝트가 없어도 손 본으로 구한다."""
    b = ps.pb("r hand")
    if b is None:
        return None
    M = ps.A2W @ b.matrix
    pw = ps.palm_world("r")
    bd = ps.blade_dir()
    if pw is None or bd is None:
        return None
    tip = pw + bd * (H * 0.52)          # 칼 길이 = 키의 0.52 (실측)
    org = ps.origin()
    d = tip - org
    return (d.dot(R) / H, d.dot(U) / H, d.dot(F) / H)


def lim_for(k):
    for name, v in LIMIT.items():
        if k.endswith(name):
            return name, v
    return None, None


def run(title, frames, build):
    rows = []
    for f, spec in frames:
        build(spec)
        bpy.context.view_layer.update()
        m = measure()
        rows.append((f, m))
    keys = sorted(rows[0][1].keys())
    tips = []
    for f, spec in frames:
        build(spec)
        bpy.context.view_layer.update()
        tips.append((f, blade_tip()))
    print("\n" + "=" * 78)
    print("[%s]  키프레임 %d개" % (title, len(rows)))
    print("=" * 78)
    print("%-22s %8s %8s | %-14s %s" % ("관절", "최소", "최대", "사람 한계", "판정"))
    bad = []
    for k in keys:
        vs = [m[k] for _, m in rows if k in m]
        if not vs:
            continue
        lo, hi = min(vs), max(vs)
        nm, L = lim_for(k)
        if L is None:
            print("%-22s %8.1f %8.1f | %-14s -" % (k, lo, hi, "-"))
            continue
        ok = (lo >= L[0] - 2) and (hi <= L[1] + 2)
        over = []
        if lo < L[0] - 2:
            over.append("최소 %.0f < %d" % (lo, L[0]))
        if hi > L[1] + 2:
            over.append("최대 %.0f > %d" % (hi, L[1]))
        tag = "OK" if ok else ("초과: " + ", ".join(over))
        if not ok:
            worst = max(rows, key=lambda r: abs(r[1].get(k, 0)))
            bad.append((k, tag, worst[0], worst[1].get(k, 0)))
            tag += "  (최악 f%s = %.0f도)" % (worst[0], worst[1].get(k, 0))
        print("%-22s %8.1f %8.1f | %-14s %s" % (k, lo, hi, "%d~%d" % L, tag))
    # ---- 칼끝 궤적 ----
    print("\n  칼끝 (몸통 기준, 키 대비 %):   r=오른쪽  u=위  f=앞")
    prev = None
    for f, t in tips:
        if t is None:
            continue
        mv = ""
        if prev is not None:
            dr, du, df = (t[0] - prev[0]) * 100, (t[1] - prev[1]) * 100, (t[2] - prev[2]) * 100
            L2 = math.sqrt(dr * dr + du * du + df * df)
            if L2 > 8:
                # 이 구간이 세로베기인가 가로베기인가
                vert = abs(du) / max(1e-6, L2)
                horiz = abs(dr) / max(1e-6, L2)
                kind = ("세로" if vert > 0.72 else
                        "가로" if horiz > 0.72 else "비스듬")
                mv = "  <- %s 이동 %.0f (좌우%+.0f 상하%+.0f 앞뒤%+.0f)" % (kind, L2, dr, du, df)
        print("   f%-4s r%+6.1f u%+6.1f f%+6.1f%s" % (f, t[0] * 100, t[1] * 100, t[2] * 100, mv))
        prev = t
    return bad


ALL_BAD = {}
for nm, seq in (("3연타 Attack", CP.SEQ), ("수면참 Heavy", CP.HEAVY_SEQ),
                ("횡일섬 Wide", CP.WIDE_SEQ), ("점프 Jump", CP.JUMP_SEQ)):
    ALL_BAD[nm] = run(nm, seq, lambda p: ps.apply(p))

# 중단세 단독
ALL_BAD["중단세 GUARD"] = run("중단세 GUARD", [(1, CP.GUARD)], lambda p: ps.apply(p))

# 달리기
src, f0, f1, tmp = AA.load("infantry_combat_run")


def build_run(sf):
    sc.frame_set(sf)
    ps.reset()
    arm.location = ps.home
    AA.copy_pose(src, arm, AA.LOWER_NOHEAD)
    d = ps.bone_dir("r thigh")
    sw = 0.0 if d is None else max(-1.0, min(1.0, d.dot(CP.FWD) / 0.55))
    ps.apply({"b": CP.run_arms(sw)}, reset=False)


ALL_BAD["달리기 Run"] = run("달리기 Run", [(i, f0 + i) for i in range(0, f1 - f0 + 1, 2)],
                          build_run)
AA.drop(tmp)

print("\n" + "=" * 78)
print("요약")
print("=" * 78)
tot = 0
for k, v in ALL_BAD.items():
    if v:
        print("  %s" % k)
        for a, b, wf, wv in v:
            print("     - %s : %s (최악 f%s = %.0f도)" % (a, b, wf, wv))
            tot += 1
    else:
        print("  %s : 위반 없음" % k)
print("\n총 위반 항목 %d" % tot)
