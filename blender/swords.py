# -*- coding: utf-8 -*-
"""검 변형 세트.

레퍼런스(sword.jpeg) 7자루를 뜯어보면 문법이 하나다:
  **송곳니 모양 대검 + 자루에 털 뭉치**, 그리고 재질만 갈아끼운다.
  (맨 위 한 자루만 예외 - 평범한 얇은 칼 = 봉인 상태)
그래서 날 실루엣/표면처리/털색/금구를 파라미터로 뽑고 표로 관리한다.

세계관이 한국 요괴(구미호·도깨비·어둑시니·이무기)이므로 이름은 오리지널로 간다.
원작 용어(철쇄아 등)는 쓰지 않는다.

실행: blender --background --python swords.py        (전 종류 라인업 렌더)
      ONE=이무기비늘 blender --background --python swords.py   (한 자루만 크게)
"""
import bpy
import os
import sys
import math
import random
from mathutils import Vector

ROOT = "/Users/lbj/Documents/gameproject"
BLD = os.path.join(ROOT, "blender")
sys.path.insert(0, BLD)
import build_scenes as BS

link, prim, new_mesh_obj, finish, cel_mat = (
    BS.link, BS.prim, BS.new_mesh_obj, BS.finish, BS.cel_mat)


# ---------------------------------------------------------------- 날 (휜 초승달)
# sword2.webp / sword3.png 를 보고 전면 재작성.
# 이전 판은 **곧은 나뭇잎**이었다(가운데가 불룩, 양끝이 뾰족). 실제는 전혀 다르다:
#   · 크게 휜 초승달 - 사브르처럼 호를 그린다
#   · **자루 쪽이 가장 넓고** 끝으로 갈수록 가늘어져 긴 첨단이 된다
#   · 등(오목한 안쪽)은 얇고, 날(볼록한 바깥쪽)이 폭의 대부분
# 그래서 직선 점열이 아니라 **원호 중심선 + 폭 함수**로 만든다.

def _arc(spec, s, n=52):    # 26 이면 휜 날의 외곽선이 각져 보인다
    """중심선 원호. 시작 접선 +X, 총 bend 만큼 휜다. (점, 법선) 반환."""
    L = spec["length"] * s
    bend = math.radians(spec.get("curve", 52))
    R = L / bend if bend > 1e-4 else 1e9
    pts, nrm = [], []
    for i in range(n + 1):
        t = i / n
        a = bend * t
        pts.append((R * math.sin(a), R * (1.0 - math.cos(a))))
        nrm.append((-math.sin(a), math.cos(a)))
    return pts, nrm


def _width(spec, u):
    """폭 함수. u=0 자루, u=1 칼끝.

    ★sword3.png 실루엣을 픽셀로 실측한 결과(최대폭 대비):
        자루 0.82 → 0.86 → 0.90 → 0.95 → **0.52 지점에서 1.00(최대)**
        → 0.94 → 0.84 → 0.64 → 0.36 → 칼끝 0.04
      즉 **가운데가 제일 두껍고 자루 쪽도 82%**, 끝 30% 에서만 급히 뾰족해진다.
      처음엔 자루가 제일 두껍고 계속 가늘어지게 만들었는데 정반대였다.
    측정값에 cos 곡선이 거의 정확히 맞는다(오차 0.02 이내).
    """
    pk = spec.get("peak", 0.52)
    hb = spec.get("w_hilt", 0.82)          # 자루 쪽 폭 / 최대폭
    if u <= pk:
        f = hb + (1.0 - hb) * (u / pk)
    else:
        f = math.cos(math.pi * 0.5 * (u - pk) / (1.0 - pk))
    return spec["w0"] * max(0.0, f)


def _blade(tag, s, mat, spec):
    pts, nrm = _arc(spec, s)
    n = len(pts) - 1
    back, belly = [], []
    bf = spec.get("back_frac", 0.40)
    for i, ((x, z), (nx, nz)) in enumerate(zip(pts, nrm)):
        t = i / n
        w = _width(spec, t) * s
        back.append((x + nx * w * bf, z + nz * w * bf))
        belly.append((x - nx * w * (1 - bf), z - nz * w * (1 - bf)))
    ring = back + belly[::-1][1:-1]          # 끝점은 폭 0 이라 중복 제거
    verts = [(x + 0.05, 0, z) for (x, z) in ring]
    ob = new_mesh_obj("bl_" + tag, verts, [tuple(range(len(verts)))])
    m = ob.modifiers.new("Sol", "SOLIDIFY")
    m.thickness = spec["thick"] * s
    m.offset = 0
    finish(ob, mat, 0.004, 2, False, False)
    return ob, pts, nrm


# ---------------------------------------------------------------- 표면
def _bevel_line(tag, s, root, spec, pts, nrm, col):
    """날을 따라 지나가는 베벨 선. 레퍼런스에 반드시 있고, 이게 있어야 '날'로 보인다."""
    m = cel_mat("bv_" + tag, col, shadow_mul=0.62, soft=0.16)
    n = len(pts) - 1
    bf = spec.get("back_frac", 0.40)
    a, b = [], []
    for i, ((x, z), (nx, nz)) in enumerate(zip(pts, nrm)):
        t = i / n
        w = _width(spec, t) * s
        e = -(1 - bf) * w                     # 날 끝
        a.append((x + nx * (e + w * 0.30), z + nz * (e + w * 0.30)))
        b.append((x + nx * (e + w * 0.16), z + nz * (e + w * 0.16)))
    ring = a + b[::-1]
    ob = new_mesh_obj("bv_" + tag, [(x + 0.05, 0, z) for (x, z) in ring],
                      [tuple(range(len(ring)))])
    md = ob.modifiers.new("Sol", "SOLIDIFY")
    md.thickness = spec["thick"] * s * 1.35   # 날 두께보다 두꺼워야 파묻히지 않는다
    md.offset = 0
    finish(ob, m, 0.002, 1, False, False)
    ob.parent = root


def _hatch(tag, s, root, spec, pts, nrm, col, seed, n_marks=22):
    """짧은 빗금. 레퍼런스의 결 표현은 고른 긴 마디가 아니라 **흩어진 짧은 획**이다."""
    m = cel_mat("ht_" + tag, col, shadow_mul=0.5, soft=0.16)
    rng = random.Random(seed)
    n = len(pts) - 1
    bf = spec.get("back_frac", 0.40)
    for k in range(n_marks):
        t = 0.05 + rng.random() ** 0.85 * 0.86
        i = min(n, int(t * n))
        (x, z), (nx, nz) = pts[i], nrm[i]
        w = _width(spec, t) * s
        if w < 0.012 * s:
            continue
        u = rng.uniform(-0.18, 0.30)          # 폭 방향 위치(등 쪽에 더 많이)
        px, pz = x + nx * w * (bf - 0.5 + u), z + nz * w * (bf - 0.5 + u)
        ln = w * rng.uniform(0.10, 0.24)
        o = prim("cube", "ht%d_%s" % (k, tag), mat=m, smooth=False)
        o.scale = (0.0026 * s, spec["thick"] * s * 0.66, ln)
        o.location = (px + 0.05, 0, pz)
        # 획은 날 방향에 대해 비스듬하다
        base = math.atan2(-nx, nz)
        o.rotation_euler = (0, base + math.radians(rng.uniform(20, 42)), 0)
        o.parent = root


def _spine_deco(kind, tag, s, root, spec, pts, nrm, col, seed):
    """자루별 정체성. 등줄기(back)를 따라 얹는다."""
    if kind == "none":
        return
    m = cel_mat("sp_" + tag, col, shadow_mul=0.5, soft=0.18)
    rng = random.Random(seed + 7)
    n = len(pts) - 1
    bf = spec.get("back_frac", 0.40)
    cnt = {"scale": 20, "crystal": 14, "stone": 12, "ember": 16}.get(kind, 12)
    for k in range(cnt):
        t = 0.06 + k / cnt * 0.84
        i = min(n, int(t * n))
        (x, z), (nx, nz) = pts[i], nrm[i]
        w = _width(spec, t) * s
        if w < 0.010 * s:
            continue
        ey = spec["thick"] * s * 0.5 + 0.008 * s     # 날 두께 밖으로

        if kind == "scale":                          # 등줄기 비늘
            for j in range(2):
                off = w * (bf - 0.08 - j * 0.13)
                o = prim("ico_sphere", "sp%d_%d_%s" % (k, j, tag), mat=m,
                         subdivisions=1, radius=w * 0.11, smooth=True)
                o.scale = (0.9, ey / max(1e-6, w * 0.11), 0.62)
                o.location = (x + nx * off + 0.05, 0, z + nz * off)
                o.parent = root

        elif kind == "crystal":                      # 날 밖으로 돋는 결정
            e = -(1 - bf) * w
            ln = w * rng.uniform(0.30, 0.62)
            o = prim("cone", "sp%d_%s" % (k, tag), mat=m, vertices=4,
                     radius1=w * 0.10, depth=ln, smooth=False)
            o.scale = (1.0, ey / max(1e-6, w * 0.10), 1.0)
            o.location = (x + nx * (e - ln * 0.3) + 0.05, 0, z + nz * (e - ln * 0.3))
            o.rotation_euler = (0, math.atan2(-nx, nz) + math.pi, 0)
            o.parent = root

        elif kind == "stone":                        # 길이 방향 굵은 결
            off = w * rng.uniform(-0.30, 0.28)
            o = prim("cube", "sp%d_%s" % (k, tag), mat=m, smooth=False)
            o.scale = (spec["length"] * s * 0.020 * rng.uniform(0.6, 1.4), ey, w * 0.030)
            o.location = (x + nx * off + 0.05, 0, z + nz * off)
            o.rotation_euler = (0, math.atan2(-nx, nz) - math.pi / 2, 0)
            o.parent = root

        elif kind == "ember":                        # 날 쪽을 따라 흐르는 불
            e = -(1 - bf) * w
            h = w * rng.uniform(0.10, 0.20)
            off = e + h * 0.9
            o = prim("cube", "sp%d_%s" % (k, tag), mat=m, smooth=False)
            o.scale = (spec["length"] * s * 0.030 * rng.uniform(0.8, 1.5), ey, h * 0.7)
            o.location = (x + nx * off + 0.05, 0, z + nz * off)
            o.rotation_euler = (0, math.atan2(-nx, nz) - math.pi / 2, 0)
            o.parent = root


# ---------------------------------------------------------------- 자루/털
def _fur(tag, s, root, col, spec):
    """자루의 털 뭉치. 레퍼런스는 방사형이 아니라 **아래로 처져 흘러내린다**.
    사방으로 고르게 뻗으면 성게처럼 보인다."""
    m = cel_mat("fur_" + tag, col, shadow_mul=0.58, soft=0.26)
    rng = random.Random(abs(hash(tag)) % 9999)
    R = spec["w0"] * s * 0.50
    for i in range(30):
        a = rng.uniform(0, math.tau)
        # 아래쪽(-Z)에 몰리게 가중
        droop = 0.35 + 0.65 * (0.5 - 0.5 * math.sin(a))
        ln = R * rng.uniform(1.1, 2.4) * droop
        f = prim("cone", "fur%d_%s" % (i, tag), mat=m, vertices=5,
                 radius1=R * 0.20, depth=ln, smooth=False)
        dy, dz = math.cos(a), math.sin(a)
        f.location = (0.055 * s + rng.uniform(-0.2, 0.2) * R,
                      dy * R * 0.55, dz * R * 0.55 - R * 0.25)
        # 뒤/아래로 흘러내린다
        v = Vector((-0.30 - rng.random() * 0.5, dy * 0.7, dz * 0.7 - 0.85)).normalized()
        f.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
        f.parent = root


def _hilt(tag, s, root, spec, grip_col, fit_col, guard=None):
    """엮은 끈 자루. 레퍼런스는 마름모로 교차해 감은 게 뚜렷하다."""
    mg = cel_mat("gr_" + tag, grip_col, soft=0.2)
    mf = cel_mat("ft_" + tag, fit_col, soft=0.2)
    # ★자루 길이. 예전 계산이 틀려서 **왼 주먹이 물미 밖으로 나가 있었다**
    # (출고본 실측: 왼 주먹 u -0.16 ~ -0.08, 주먹의 28~35% 만 자루에 물림).
    # 오른 주먹은 자루 끝(츠바쪽)에서 0.1213 월드 지점에 고정이고, 양손 간격은
    # GB*H = 0.2702 다. 물미가 왼 주먹 밖으로 0.10 은 나와야 "자루 끝"이 읽히므로
    # 필요한 길이 = (0.1213 + 0.2702 + 0.10) / 0.5669 = 0.867. 여유를 둬 0.88.
    GL = spec.get("grip_len", 0.98) * s
    # ★반지름을 칼날 폭에서 뽑으면 안 된다. 봉인칼(nokseun)만 w0 가 1/4 이라
    # 자루가 주먹 반경의 6% 짜리 **실**이 됐다(다른 칼은 24~32%).
    # 자루 굵기는 칼날이 아니라 **손**이 정한다. 사람 주먹 대비 약 26%.
    r = spec.get("grip_r", 0.078) * s
    core = prim("cylinder", "gr_" + tag, mat=mg, vertices=12, radius=r * 0.86,
                depth=GL, rot=(0, math.radians(90), 0), bevel=0.003)
    core.location = (-GL * 0.5 + 0.02 * s, 0, 0)
    core.parent = root
    # 감은 띠. 마름모 큐브를 45도로 돌렸더니 대각선이 자루 굵기 밖으로 튀어나와
    # 부채처럼 벌어졌다. 얇은 원반을 번갈아 기울여 감은 결만 보이게 한다.
    NB = 10
    for i in range(NB):
        u = -GL * 0.94 + (i + 0.5) / NB * GL * 0.90 + 0.02 * s
        b = prim("cylinder", "wp%d_%s" % (i, tag), mat=mf, vertices=12,
                 radius=r * 0.97, depth=GL * 0.045,
                 rot=(0, math.radians(90), math.radians(11 if i % 2 else -11)))
        b.location = (u, 0, 0)
        b.parent = root
    p = prim("cylinder", "pm_" + tag, mat=mf, vertices=12, radius=r * 1.05,
             depth=r * 0.7, rot=(0, math.radians(90), 0), bevel=0.005)
    p.location = (-GL * 0.98 + 0.02 * s, 0, 0)
    p.parent = root
    if guard:
        t = prim("cylinder", "gd_" + tag, mat=mf, vertices=20, radius=guard * s,
                 depth=0.012 * s, rot=(0, math.radians(90), 0), bevel=0.004)
        t.location = (0.040 * s, 0, 0)
        t.parent = root


# ---------------------------------------------------------------- 변형 표
# length=호 길이 / curve=휨(도) / w0=자루쪽 폭 / taper=끝으로 가늘어지는 정도
# back_frac=등 쪽이 가져가는 폭 비율(작을수록 날이 두툼)
VARIANTS = [
    dict(key="nokseun", name="녹슨 칼", note="봉인 상태. 평범해 보여야 한다",
         length=2.05, curve=14, w0=0.070, peak=0.30, w_hilt=0.92, back_frac=0.45, thick=0.020,
         blade="6E6A58", bevel="8C8874", hatch="5A5648", spine=("none", None),
         fur=None, guard=0.055, grip="3C5A3A", fit="8A7A46"),

    dict(key="baekah", name="백아(白牙)", note="송곳니 각성. 뼈결이 빗금으로",
         length=2.20, curve=54, w0=0.304, peak=0.52, w_hilt=0.82, back_frac=0.38, thick=0.036,
         blade="D8DCE0", bevel="F0F2F4", hatch="8E9298", spine=("none", None),
         fur="EDE6D2", guard=None, grip="6B4A2E", fit="C6A24A"),

    dict(key="hongyeom", name="홍염", note="피를 먹은 형태. 날 쪽이 타오른다",
         length=2.18, curve=58, w0=0.315, peak=0.52, w_hilt=0.82, back_frac=0.36, thick=0.038,
         blade="B8342A", bevel="E86A3C", hatch="7A1E18", spine=("ember", "F2A24E"),
         fur="8E4632", guard=None, grip="4A2620", fit="C8A24A"),

    dict(key="seorikkot", name="서리꽃", note="결정이 날 밖으로 돋는다",
         length=2.26, curve=48, w0=0.278, peak=0.52, w_hilt=0.82, back_frac=0.40, thick=0.032,
         blade="C6DEEC", bevel="F2FAFE", hatch="7FA6BC", spine=("crystal", "9FD4EC"),
         fur="F2F5F8", guard=None, grip="3E5A6A", fit="B8C8D2"),

    dict(key="imugi", name="이무기 비늘", note="한국 요괴 축. 등줄기에 비늘",
         length=2.02, curve=64, w0=0.347, peak=0.52, w_hilt=0.82, back_frac=0.34, thick=0.042,
         blade="3E4A3A", bevel="6A7A5E", hatch="2A3228", spine=("scale", "6FA046"),
         fur="7A6248", guard=None, grip="2E3A2C", fit="A08A4C"),

    dict(key="bawigyeol", name="바위결", note="무겁고 거칠다. 길이 방향 돌결",
         length=1.98, curve=44, w0=0.362, peak=0.52, w_hilt=0.82, back_frac=0.38, thick=0.046,
         blade="8A8276", bevel="ADA598", hatch="5E584E", spine=("stone", "5E584E"),
         fur="EFEAE0", guard=None, grip="4A4238", fit="C2A44E"),

    dict(key="eoduk", name="어둑", note="어둑시니. 빛을 먹은 칠흑, 장식 없음",
         length=2.34, curve=52, w0=0.268, peak=0.52, w_hilt=0.82, back_frac=0.42, thick=0.034,
         blade="2A2A30", bevel="4E4E5A", hatch="17171C", spine=("none", None),
         fur="E6DEEA", guard=None, grip="1E1E24", fit="7A6E8A"),
]


def build_sword(v, tag=None, scale=1.0):
    """변형 하나. 원점=자루 중앙 부근, +X=칼끝 방향(휘어 올라간다)."""
    t = tag or v["key"]
    spec = dict(v)
    spec["length"] = v["length"] * scale
    spec["w0"] = v["w0"] * scale
    spec["thick"] = v["thick"] * scale
    spec["grip_len"] = v.get("grip_len", 0.98) * scale
    spec["grip_r"] = v.get("grip_r", 0.078) * scale
    root = bpy.data.objects.new("sw_" + t, None)
    link(root)
    m = cel_mat("bd_" + t, v["blade"], ramp_pos=0.30, shadow_mul=0.64, soft=0.2)
    b, pts, nrm = _blade(t, 1.0, m, spec)
    b.parent = root
    _bevel_line(t, 1.0, root, spec, pts, nrm, v["bevel"])
    _hatch(t, 1.0, root, spec, pts, nrm, v["hatch"], seed=abs(hash(t)) % 9999)
    _spine_deco(v["spine"][0], t, 1.0, root, spec, pts, nrm,
                v["spine"][1] or v["blade"], seed=abs(hash(t)) % 9999)
    if v["fur"]:
        _fur(t, 1.0, root, v["fur"], spec)
    _hilt(t, 1.0, root, spec, v["grip"], v["fit"], guard=v.get("guard"))
    return root


# ---------------------------------------------------------------- 렌더
if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    ids = [i.identifier for i in sc.render.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.055, 0.06, 0.075, 1)

    li = bpy.data.lights.new("S", "SUN")
    li.energy = 3.6
    so = bpy.data.objects.new("S", li)
    so.rotation_euler = (math.radians(56), 0, math.radians(-34))
    sc.collection.objects.link(so)
    li2 = bpy.data.lights.new("F", "SUN")
    li2.energy = 1.5
    li2.color = (0.6, 0.75, 1.0)
    so2 = bpy.data.objects.new("F", li2)
    so2.rotation_euler = (math.radians(-40), 0, math.radians(120))
    sc.collection.objects.link(so2)

    cam_d = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.type = "ORTHO"

    ONE = os.environ.get("ONE")
    OUT = os.path.join(ROOT, "renders", "swords")
    os.makedirs(OUT, exist_ok=True)

    if ONE:
        v = next(x for x in VARIANTS if x["key"] == ONE or x["name"] == ONE)
        r = build_sword(v)
        r.rotation_euler = (0, math.radians(v.get("curve", 52)) * 0.5, 0)
        L = v["length"]
        cam_d.ortho_scale = L + 0.75
        cam.location = ((L + 0.05 - 0.45) * 0.5, -4, 0.0)
        cam.rotation_euler = (math.radians(90), 0, 0)
        sc.render.resolution_x, sc.render.resolution_y = 1400, 620
        sc.render.filepath = os.path.join(OUT, "one_%s.png" % v["key"])
        bpy.ops.render.render(write_still=True)
        print("DONE", sc.render.filepath)
    else:
        gap = 0.62
        for i, v in enumerate(VARIANTS):
            r = build_sword(v)
            # 휜 칼은 칼끝이 위로 크게 솟는다. 현(자루->칼끝)이 수평이 되게
            # -bend/2 만큼 눕혀야 겹치지 않고 무기 도감처럼 보인다.
            r.rotation_euler = (0, math.radians(v.get("curve", 52)) * 0.5, 0)
            r.location = (0, 0, -i * gap)
        # ★정사영 카메라의 ortho_scale 은 렌더의 '긴 변'에 걸린다.
        # 세로로 쌓으면 세로가 길어지므로 ortho_scale 을 세로 범위에 맞추고
        # 가로는 해상도 비율로 확보해야 한다(안 그러면 칼끝이 잘린다).
        x0, x1 = -0.55, max(v["length"] for v in VARIANTS) * 0.99 + 0.15
        w_ext = x1 - x0
        h_ext = (len(VARIANTS) - 1) * gap + 1.05
        cam_d.ortho_scale = max(w_ext, h_ext)
        cam.location = ((x0 + x1) * 0.5, -4, -(len(VARIANTS) - 1) * gap * 0.5)
        cam.rotation_euler = (math.radians(90), 0, 0)
        H = 1500
        sc.render.resolution_y = H
        sc.render.resolution_x = int(H * w_ext / h_ext)
        sc.render.filepath = os.path.join(OUT, "lineup.png")
        bpy.ops.render.render(write_still=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLD, "swords_set.blend"))
        print("DONE", sc.render.filepath, sc.render.resolution_x, "x", H)
