# -*- coding: utf-8 -*-
"""옷(basic_cloth)이 몸(basic2)에서 얼마나 떠 있는지 **숫자로** 잰다.

    BODY_GLB=web/basic2_native.glb blender -b -P blender/probe_cloth_fit.py

s33 의 [2] 절(용접 -> 벨트 안착 -> 배율)까지만 그대로 재현한 뒤,
정점마다 "몸 표면까지의 부호 있는 거리"를 재서 섬별 히스토그램을 찍는다.
- 음수 = 몸을 뚫고 들어감
- 큰 양수 = 헐렁하게 떠 있음   <- 오너가 말한 "옷이 크다"
"""
import bpy, bmesh, os, math
from mathutils import Vector, Matrix

ROOT = "/Users/lbj/Documents/gameproject"


def _p(v):
    return v if os.path.isabs(v) else os.path.join(ROOT, v)


BODY_GLB = _p(os.environ.get("BODY_GLB", "web/basic2.glb"))
CLOTH_GLB = _p(os.environ.get("CLOTH_GLB", "incoming/basic_cloth.glb"))
HIP_F = float(os.environ.get("HIP_F", "0.560"))
CLOTH_S = float(os.environ.get("CLOTH_S", "1.035"))
NANG = 36

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30


def drop_junk():
    for o in list(bpy.data.objects):
        if any(c.name == "glTF_not_exported" for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)


def imp(path):
    before = set(o.name for o in sc.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    drop_junk()
    return [o for o in sc.objects if o.name not in before]


def weld(ob, dist=1e-5):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def islands(ob):
    adj = {i: set() for i in range(len(ob.data.vertices))}
    for p in ob.data.polygons:
        vs = list(p.vertices)
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            adj[a].add(b)
            adj[b].add(a)
    seen, out = set(), []
    for i in range(len(ob.data.vertices)):
        if i in seen:
            continue
        st, comp = [i], []
        seen.add(i)
        while st:
            a = st.pop()
            comp.append(a)
            for nb in adj[a]:
                if nb not in seen:
                    seen.add(nb)
                    st.append(nb)
        out.append(comp)
    out.sort(key=len, reverse=True)
    return out


def ring(pts, cx, cy, mode):
    r = [None] * NANG
    for p in pts:
        d = math.hypot(p.x - cx, p.y - cy)
        k = int((math.atan2(p.y - cy, p.x - cx) + math.pi) / (2 * math.pi) * NANG) % NANG
        if r[k] is None:
            r[k] = d
        elif mode == "min":
            r[k] = min(r[k], d)
        else:
            r[k] = max(r[k], d)
    return r


objs = imp(BODY_GLB)
arm = next(o for o in objs if o.type == "ARMATURE")
meshes = [o for o in objs if o.type == "MESH"]
body = max((o for o in meshes if not o.name.startswith(("SW_", "SH_", "cloth"))),
           key=lambda o: len(o.data.vertices))
arm.data.pose_position = "REST"
bpy.context.view_layer.update()
A2W = arm.matrix_world
BW = [body.matrix_world @ v.co for v in body.data.vertices]
H = max(p.z for p in BW) - min(p.z for p in BW)
FOOT = min(p.z for p in BW)
print("[몸] %s 정점 %d  키 %.4f  발바닥z %.4f" % (body.name, len(BW), H, FOOT))

cobjs = imp(CLOTH_GLB)
cloth = next(o for o in cobjs if o.type == "MESH")
weld(cloth)
cloth.data.transform(cloth.matrix_world)
cloth.matrix_world = Matrix.Identity(4)
cloth.data.update()
CV = [v.co.copy() for v in cloth.data.vertices]
isl = islands(cloth)
print("[옷] 정점 %d  섬 %d개" % (len(CV), len(isl)))
for k, s in enumerate(isl):
    xs = [CV[i].x for i in s]; ys = [CV[i].y for i in s]; zs = [CV[i].z for i in s]
    print("   섬%-2d 정점%-5d x %.3f~%.3f  y %.3f~%.3f  z %.3f~%.3f"
          % (k, len(s), min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

belt = next(s for s in isl
            if (max(CV[i].x for i in s) - min(CV[i].x for i in s)) > 0.9
            and (max(CV[i].z for i in s) - min(CV[i].z for i in s)) < 0.3)
BELT_K = isl.index(belt)
bp = [CV[i] for i in belt]
BCX = (max(p.x for p in bp) + min(p.x for p in bp)) / 2
BCY = (max(p.y for p in bp) + min(p.y for p in bp)) / 2
BZ0, BZ1 = min(p.z for p in bp), max(p.z for p in bp)
BMID = (BZ0 + BZ1) / 2
strap = max(isl, key=lambda s: max(CV[i].z for i in s) - min(CV[i].z for i in s))
STRAP_K = isl.index(strap)
print("[옷] 벨트=섬%d  어깨끈=섬%d" % (BELT_K, STRAP_K))

RIN = ring(bp, BCX, BCY, "min")
ARMG = [g.index for g in body.vertex_groups
        if any(t in g.name for t in ("UpperArm", "Forearm", "Hand"))]
armv = set()
for v in body.data.vertices:
    for g in v.groups:
        if g.group in ARMG and g.weight > 0.25:
            armv.add(v.index)
            break
ZC = FOOT + H * HIP_F
band = [p for i, p in enumerate(BW) if i not in armv and abs(p.z - ZC) <= (BZ1 - BZ0) * 0.5]
WCX = (max(p.x for p in band) + min(p.x for p in band)) / 2
WCY = (max(p.y for p in band) + min(p.y for p in band)) / 2
RB = ring(band, WCX, WCY, "max")
S_MIN = max(RB[i] / RIN[i] for i in range(NANG) if RIN[i] and RB[i])
S = S_MIN * CLOTH_S
print("[배율] S_MIN(max비) %.4f x %.3f = %.4f" % (S_MIN, CLOTH_S, S))

# ★핵심 진단: 각도별 (몸 반경 / 벨트 안쪽 반경). 이게 균일하지 않으면 통짜 배율은
#   가장 큰 각도에만 맞고 나머지는 그만큼 뜬다.
rr = [(RB[i] / RIN[i]) for i in range(NANG) if RIN[i] and RB[i]]
rr_s = sorted(rr)
print("[배율] 각도별 요구배율 %d개  최소 %.4f  중앙 %.4f  90%% %.4f  최대 %.4f"
      % (len(rr), rr_s[0], rr_s[len(rr_s) // 2], rr_s[int(len(rr_s) * 0.9)], rr_s[-1]))
print("       -> 최대/중앙 = %.3f 배. 통짜 배율은 중앙 각도에서 벨트가 몸보다"
      " %.1f%% 크다" % (rr_s[-1] / rr_s[len(rr_s) // 2],
                      (rr_s[-1] * CLOTH_S / rr_s[len(rr_s) // 2] - 1) * 100))
print("       각도별 요구배율(뒤->앞 36칸):")
print("       " + " ".join("%.2f" % (RB[i] / RIN[i]) if RIN[i] and RB[i] else " -- "
                           for i in range(NANG)))

# s33 배치를 그대로 적용
for v in cloth.data.vertices:
    p = v.co
    v.co = Vector((WCX + (p.x - BCX) * S, WCY + (p.y - BCY) * S, ZC + (p.z - BMID) * S))
cloth.data.update()
CV = [v.co.copy() for v in cloth.data.vertices]
BELT_TOP = ZC + (BZ1 - BMID) * S
print("[배치] 벨트 윗선 %.4f  옷 z %.4f~%.4f" % (BELT_TOP, min(p.z for p in CV), max(p.z for p in CV)))

# ---- 간격 실측 ----
Minv = body.matrix_world.inverted()
M3 = body.matrix_world.to_3x3()
ISL_OF = {}
for k, s in enumerate(isl):
    for i in s:
        ISL_OF[i] = k
gaps = {}
allg = []
for vi, p in enumerate(CV):
    hit, loc, nrm, _ = body.closest_point_on_mesh(Minv @ p)
    if not hit:
        continue
    lw = body.matrix_world @ loc
    nw = (M3 @ nrm).normalized()
    d = (p - lw).dot(nw)
    gaps.setdefault(ISL_OF[vi], []).append(d)
    allg.append(d)


def stat(name, arr):
    a = sorted(arr)
    n = len(a)
    q = lambda f: a[min(n - 1, int(n * f))]
    print("  %-26s n%-5d  min%7.1f  10%%%7.1f  50%%%7.1f  90%%%7.1f  max%7.1f  평균%7.1f (mm)"
          % (name, n, a[0] * 1000, q(.1) * 1000, q(.5) * 1000, q(.9) * 1000,
             a[-1] * 1000, sum(a) / n * 1000))


print("[간격] 옷 정점 -> 몸 표면 부호거리 (음수=관통)")
stat("전체", allg)
for k in sorted(gaps, key=lambda k: -len(gaps[k])):
    tag = " <=벨트" if k == BELT_K else (" <=어깨끈" if k == STRAP_K else "")
    stat("섬%d%s" % (k, tag), gaps[k])

# 벨트만: 높이대별
bz = [(CV[i].z, gaps[BELT_K][j]) for j, i in enumerate(isl[BELT_K])]
print("[벨트] 정점별 간격 상위 10: %s"
      % ["%.0fmm" % (g * 1000) for _, g in sorted(bz, key=lambda x: -x[1])[:10]])

# 어깨끈 정점을 몸 표면에 붙였을 때 필요한 이동량
sg = sorted(gaps[STRAP_K])
print("[어깨끈] 몸 표면까지 %d mm 이상 뜬 정점 %d/%d (%.0f%%)"
      % (20, sum(1 for g in sg if g > 0.020), len(sg),
         100.0 * sum(1 for g in sg if g > 0.020) / len(sg)))
print("DONE")
