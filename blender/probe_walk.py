# -*- coding: utf-8 -*-
"""걷기 클립의 **발 궤적**을 프레임별로 재서 미끄러짐을 판정한다.

probe_stride.py 와 뭐가 다른가
  probe_stride 는 "게임 이동 속도 하나"를 뽑는 도구다. 여기는 그 앞 단계,
  즉 **클립이 애초에 보행인지**를 본다. 프레임별 표를 그대로 찍고
  아래 네 가지를 판정한다.
    1) 접지 구간에서 두 발이 **같은 부호로** 뒤로 밀리는가
       (고치기 전 검사 Walk 은 왼발 +2.76 / 오른발 -2.64 로 부호가 반대였다.
        = 두 발이 대칭으로 앞뒤 왕복만 하고 접지 구간이 없다는 뜻)
    2) 접지 중 발 높이가 일정한가 (호를 그리며 들리면 실패)
    3) 프레임별 후퇴 속도가 일정한가 (들쭉날쭉하면 미끄러진다)
    4) 게임 단위 발 속도 (이동 속도 설정에 쓸 값)

부호 규약: 전방축 투영 proj = (발 - 골반)·FWD. + 면 발이 몸 앞.
           속도는 probe_stride 와 같게 **뒤로 밀리는 쪽을 +** 로 적는다.

실행: GLB=slayer.glb TARGET_H=1.75 blender -b -P blender/probe_walk.py
"""
import bpy
import os
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
GLB = os.environ.get("GLB", "slayer.glb")
TARGET_H = float(os.environ.get("TARGET_H", "1.75"))
ACTS = os.environ.get("ACT", "Walk").split(",")

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
# ★glb 는 시간이 **초** 단위다. 임포트 fps 가 원본과 다르면 프레임이 어긋나
# 리샘플 오차가 표에 섞인다(24fps 로 읽으면 30fps 클립의 첫 칸이 0.25 프레임만큼
# 짧게 나온다). 검사 glb 는 30fps 로 구웠다.
sc.render.fps = int(os.environ.get("FPS", "30"))
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "web", GLB))
arm = next(o for o in sc.objects if o.type == "ARMATURE")


def _skip(o):
    # ★무기(SW_)와 임포터가 만든 Icosphere 는 키에서 뺀다. probe_stride 주석 참고.
    if o.name.startswith(("SW_", "SH_")):
        return True
    return any(c.name == "glTF_not_exported" for c in o.users_collection)


meshes = [o for o in sc.objects if o.type == "MESH" and not _skip(o)]
zs = []
for m in meshes:
    zs += [(m.matrix_world @ v.co).z for v in m.data.vertices]
H = max(zs) - min(zs)
FLOOR0 = min(zs)                 # 바인드 포즈(= 서 있는 자세)의 바닥
SCALE = TARGET_H / H
MESH = bool(os.environ.get("MESH"))   # 켜면 프레임마다 메시 최저점을 잰다(느림)
FPS = sc.render.fps or 30
print("=== %s ===" % GLB)
print("원본 키 %.4f -> 게임 키 %.2f (배율 %.4f) / fps %d"
      % (H, TARGET_H, SCALE, FPS))
print("액션:", sorted(a.name for a in bpy.data.actions))


def bone(key):
    for b in arm.pose.bones:
        if key.lower() in b.name.lower():
            return b
    return None


def wp(key):
    b = bone(key)
    return (arm.matrix_world @ b.matrix).translation.copy() if b else None


def use(act):
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        slots = list(getattr(act, "slots", []))
        if slots:
            arm.animation_data.action_slot = slots[0]
    except Exception:
        pass


for name in ACTS:
    act = bpy.data.actions.get(name)
    if act is None:
        print("!! 액션 없음:", name)
        continue
    use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    rows, mins = [], {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        rows.append((f, wp("pelvis"), wp("l foot"), wp("r foot"),
                     wp("l toe"), wp("r toe")))
        if MESH:
            # ★뼈 위치만으로는 신발 밑창이 바닥을 뚫는지 알 수 없다(발끝 본은 관절이지
            # 밑창이 아니다). 실제 메시 최저점을 잰다.
            dg = bpy.context.evaluated_depsgraph_get()
            lo = 1e9
            for ob in meshes:
                ev = ob.evaluated_get(dg)
                me = ev.to_mesh()
                lo = min(lo, min((ev.matrix_world @ v.co).z for v in me.vertices))
                ev.to_mesh_clear()
            mins[f] = lo - FLOOR0

    # 전방축: 확실히 디딘 프레임(발끝이 가장 낮은 쪽) 기준 발끝-발목 수평 방향
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
    GROUND = min(min(r[4].z, r[5].z) for r in rows)   # 발끝 최저점 = 지면

    print("\n[%s] f%d~%d (%d프레임 = %.3f초)  FWD=(%.2f, %.2f, %.2f)"
          % (name, f0, f1, f1 - f0, (f1 - f0) / float(FPS), FWD.x, FWD.y, FWD.z))
    print("  proj = (발-골반)·FWD  (+ 앞)   z = 지면 위 높이   d = 직전 프레임 대비 **뒤로** 이동량")
    print("  %-4s | %-25s | %-25s | %s" % ("f", "왼발 proj    z    d",
                                           "오른발 proj    z    d", "골반z"))
    prev = None
    for r in rows:
        lp = (r[2] - r[1]).dot(FWD)
        rp = (r[3] - r[1]).dot(FWD)
        lz = r[2].z - GROUND
        rz = r[3].z - GROUND
        if prev is None:
            ld = rd = float("nan")
        else:
            ld, rd = prev[0] - lp, prev[1] - rp
        prev = (lp, rp)
        print("  %-4d | %+7.4f %6.4f %+7.4f | %+7.4f %6.4f %+7.4f | %6.4f%s"
              % (r[0], lp, lz, ld, rp, rz, rd, r[1].z - GROUND,
                 ("  메시최저 %+.4f" % mins[r[0]]) if MESH else ""))

    if MESH:
        lo = min(mins.values())
        hi = max(mins.values())
        print("  메시 최저점(서 있는 바닥 기준): %+.4f ~ %+.4f (키의 %.2f%% ~ %.2f%%)"
              % (lo, hi, 100 * lo / H, 100 * hi / H))
        print("     - 값이 음수면 발이 바닥을 뚫은 것, 계속 양수면 떠 있는 것")

    # ---- 접지 구간 판정 ----
    # 창 두 개를 쓴다.
    #  넓은창: 발끝 z <= 최저 + 키의 3%. probe_stride 와 같은 기준(값 비교용).
    #          문턱이 헐거워서 스윙 앞뒤가 섞여 들어온다.
    #  접지창: 발목 z <= 최저 + 키의 1%. **정말 디디고 있는 구간**만 남는다.
    #          발 높이 일정한지·속도 일정한지는 이 창으로 판정한다.
    def longest(flags):
        bi, cur = [], []
        for i, ok in enumerate(flags):
            if not ok:
                if len(cur) > len(bi):
                    bi = cur
                cur = []
                continue
            cur.append(i)
        return cur if len(cur) > len(bi) else bi

    print("  ---- 접지 구간 분석 ----")
    res = []
    for fi, ti, tag in ((2, 4, "왼발"), (3, 5, "오른발")):
        tz = [r[ti].z for r in rows]
        az = [r[fi].z for r in rows]
        for label, bi in (("넓은창", longest([z <= min(tz) + 0.03 * H for z in tz])),
                          ("접지창", longest([z <= min(az) + 0.01 * H for z in az]))):
            if len(bi) < 3:
                print("    %s %s: 구간 없음" % (tag, label))
                continue
            proj = [(rows[i][fi] - rows[i][1]).dot(FWD) for i in bi]
            anz = [rows[i][fi].z - GROUND for i in bi]
            dd = [proj[k] - proj[k + 1] for k in range(len(proj) - 1)]
            med = sorted(dd)[len(dd) // 2]
            avg = sum(dd) / len(dd)
            back = sum(1 for d in dd if d > 0)
            print("    %s %s f%d~%d (%2d프레임): 속도 평균 %+.3f 중앙 %+.3f /초"
                  % (tag, label, rows[bi[0]][0], rows[bi[-1]][0], len(bi),
                     avg * FPS, med * FPS))
            print("       프레임별 후퇴량 %+.4f~%+.4f (뒤로 간 프레임 %d/%d)"
                  % (min(dd), max(dd), back, len(dd)))
            print("       발목 높이 %.4f~%.4f (변동 %.4f = 키의 %.2f%%)"
                  % (min(anz), max(anz), max(anz) - min(anz),
                     100.0 * (max(anz) - min(anz)) / H))
            if label == "접지창":
                res.append((med * FPS, avg * FPS, tag))
    if len(res) == 2:
        same = "같다 ✓" if res[0][0] * res[1][0] > 0 else "★반대 = 보행이 아님"
        print("    두 발 부호: %+.3f / %+.3f -> %s" % (res[0][0], res[1][0], same))
        g = sum(r[0] for r in res) / 2.0 * SCALE
        print("    -> 게임 단위 발 속도 %.3f /초 (키 %.2f 기준)" % (g, TARGET_H))
        for ts in (1.0, 1.2, 1.5, 1.84):
            print("       재생속도 %.2f -> 이동속도 %.2f" % (ts, g * ts))
print("DONE")
