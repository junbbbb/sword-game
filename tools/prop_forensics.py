# -*- coding: utf-8 -*-
"""소품이 왜 저퀄로 보이는가 — 범인을 넷 중에서 고르는 자(尺).

    python3 tools/prop_forensics.py tex          # 텍스처 계보(원본 Meshy -> 지금)
    python3 tools/prop_forensics.py mesh         # 메시(실루엣) 정보
    python3 tools/prop_forensics.py ref          # 오너 레퍼런스 크롭 실측
    python3 tools/prop_forensics.py toon         # 툰 램프가 명암을 얼마나 누르는가
    python3 tools/prop_forensics.py all

왜 필요한가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너: "나무랑 돌 같은 거 Meshy 한 거 맞아? 너무 저퀄 느낌 나서."
저퀄 인상의 후보가 넷이다. **고치기 전에 하나를 특정해야** 한다.

    ① 메시(실루엣)   형태 자체가 밋밋한가
    ② 텍스처         손그림 밀도·명암 폭이 모자란가
    ③ 재칠           tools/regrade_props.py 가 명암을 눌렀는가
    ④ 툰 램프        MeshToonMaterial 이 명암 단을 뭉갰는가

이 자는 넷을 **따로따로** 잰다. 그래야 "N% 는 X 때문" 이라고 말할 수 있다.

재는 법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
휘도는 terrain_metrics 와 **같은 규칙**으로 잰다 — sRGB 바이트 그대로(감마 안 푼다).
자가 둘이면 숫자를 못 비교한다.

  span_5_95   휘도 5~95 분위 폭. "이 그림에 명암이 몇 단계나 들어 있나".
              레퍼런스의 손그림 바위는 여기가 넓다(칠에 빛이 그려져 있다).
  p50_range5  5x5 창의 (최대-최소) 중앙값. "붓자국 밀도". 국소대비.
  p99_range5  같은 것의 99 분위. "제일 또렷한 자국".
  sat_mean    HSV S 평균(%).
  texel/m     텍셀 밀도 = sqrt(UV면적 x 해상도^2 / 표면적). 모델 1m 당 텍스처 화소.
              ★이게 낮으면 아무리 잘 칠해도 화면에서 뭉갠다.
"""
import io
import os
import sys
import json
import struct

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import color_contract as CC   # noqa: E402

LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)

# 종류 -> (지금 것, 재칠 전, Meshy 원본)
LINEAGE = {
    "tree":       ("web/props/tree.glb",       None,                          "incoming/meshy_props/tree.glb"),
    "bush":       ("web/props/bush.glb",       None,                          "incoming/meshy_props/bush.glb"),
    "thicket":    ("web/props/thicket.glb",    None,                          "incoming/meshy_props/thicket.glb"),
    "rock":       ("web/props/rock.glb",       "web/props/rock.glb.bak_v93",  "incoming/meshy_props/rock.glb"),
    "crag":       ("web/props/crag.glb",       "web/props/crag.glb.bak_v93",  "incoming/meshy_props/crag.glb"),
    "cliff_tall": ("web/props/cliff_tall.glb", "web/props/cliff_tall.glb.bak_v93", "incoming/meshy_terrain/cliff_wall_tall.glb"),
    "outcrop":    ("web/props/outcrop.glb",    "web/props/outcrop.glb.bak_v93", "incoming/meshy_terrain/cliff_wall.glb"),
    "boulder_xl": ("web/props/boulder_xl.glb", "web/props/boulder_xl.glb.bak_v93", "incoming/meshy_terrain/boulder_xl.glb"),
    "bank":       ("web/props/bank.glb",       "web/props/bank.glb.bak_v93",  "incoming/meshy_terrain/river_bank_stones.glb"),
    "slab":       ("web/props/slab.glb",       "web/props/slab.glb.bak_v93",  "incoming/meshy_terrain/flagstone_slab.glb"),
}


# ── glb 뜯기 ──────────────────────────────────────────────────────────────────
def glb_read(path):
    d = open(path, "rb").read()
    assert d[:4] == b"glTF", path
    off, js, bin_ = 12, None, b""
    while off < len(d):
        ln, ty = struct.unpack_from("<II", d, off)
        ch = d[off + 8: off + 8 + ln]
        if ty == 0x4E4F534A:
            js = json.loads(ch.decode("utf-8"))
        elif ty == 0x004E4942:
            bin_ = ch
        off += 8 + ln
    return js, bin_


_CT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
       5125: ("I", 4), 5126: ("f", 4)}
_NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def acc_read(js, bin_, i):
    """접근자 하나를 numpy 로. ★byteStride(인터리브)를 반드시 존중해야 한다."""
    acc = js["accessors"][i]
    n = acc["count"]
    nc = _NC[acc["type"]]
    ch, sz = _CT[acc["componentType"]]
    bv = js["bufferViews"][acc["bufferView"]]
    base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or (nc * sz)
    dt = np.dtype({"b": np.int8, "B": np.uint8, "h": np.int16, "H": np.uint16,
                   "I": np.uint32, "f": np.float32}[ch])
    if stride == nc * sz:
        a = np.frombuffer(bin_, dt, n * nc, base).reshape(n, nc)
    else:
        raw = np.frombuffer(bin_, np.uint8, stride * n, base).reshape(n, stride)
        a = raw[:, :nc * sz].copy().view(dt).reshape(n, nc)
    return a.astype(np.float64) if ch == "f" else a.astype(np.int64)


def first_image(js, bin_, want=None):
    """이미지 하나를 PIL 로. want='base'/'normal' 이면 이름으로 고른다."""
    for im in js.get("images", []):
        nm = (im.get("name") or "").lower()
        if want and want not in nm:
            continue
        bv = js["bufferViews"][im["bufferView"]]
        o = bv.get("byteOffset", 0)
        return Image.open(io.BytesIO(bytes(bin_[o:o + bv["byteLength"]])))
    return None


def has_image(js, want):
    return any(want in (im.get("name") or "").lower() for im in js.get("images", []))


# ── 자 ────────────────────────────────────────────────────────────────────────
def _range5(L, mask=None):
    """5x5 창의 (최대-최소). 붓자국 밀도.

    ★mask 를 주면 **창이 통째로 마스크 안에 든 자리만** 센다. 가장자리 창을 세면
      소품과 배경의 경계(하늘/잔디)가 들어와서 국소대비가 부풀려진다 — 그러면
      "질감이 있다"는 거짓 신호가 나온다.
    """
    from numpy.lib.stride_tricks import sliding_window_view
    if min(L.shape) < 5:
        return np.zeros(1, np.float32)
    w = sliding_window_view(L, (5, 5))
    r = w.max((-1, -2)) - w.min((-1, -2))
    if mask is None:
        return r.ravel()
    mw = sliding_window_view(mask, (5, 5)).all((-1, -2))
    return r[mw] if mw.any() else np.zeros(1, np.float32)


def measure(img, sub=1, mask=None):
    """텍스처/크롭 한 장의 숫자. sub 는 계산량을 줄이는 솎기 배수."""
    a = np.asarray(img.convert("RGB"), np.float32)
    if sub > 1:
        a = a[::sub, ::sub]
    L = a @ LUMW
    if mask is not None:
        m = mask[::sub, ::sub] if sub > 1 else mask
        Lv = L[m]
        av = a[m]
    else:
        Lv, av = L.ravel(), a.reshape(-1, 3)
    mx = av.max(1); mn = av.min(1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    r5 = _range5(L, None if mask is None else (m if sub > 1 else mask))
    p = np.percentile(Lv, [1, 5, 50, 95, 99])
    return {
        "res": "%dx%d" % img.size,
        "lum_mean": float(Lv.mean()),
        "p5": float(p[1]), "p50": float(p[2]), "p95": float(p[3]),
        "span_5_95": float(p[3] - p[1]),
        "p50_range5": float(np.percentile(r5, 50)),
        "p99_range5": float(np.percentile(r5, 99)),
        "sat_mean": float(sat.mean() * 100),
        "hex": "#%02x%02x%02x" % tuple(int(x + .5) for x in av.mean(0)),
    }


HDR = ("%-13s %-10s  평균L  p5   p50   p95  |span| p50r5 p99r5  S%%   평균색")


def line(name, m):
    return ("%-13s %-10s %5.1f %5.1f %5.1f %5.1f  %5.1f  %5.1f %5.1f %5.1f  %s"
            % (name, m["res"], m["lum_mean"], m["p5"], m["p50"], m["p95"],
               m["span_5_95"], m["p50_range5"], m["p99_range5"],
               m["sat_mean"], m["hex"]))


# ── ① 텍스처 계보 ─────────────────────────────────────────────────────────────
def cmd_tex():
    print(HDR)
    print("-" * 92)
    rows = {}
    for kind, (cur, bak, orig) in LINEAGE.items():
        for tag, path in (("Meshy원본", orig), ("재칠전", bak), ("지금", cur)):
            if not path:
                continue
            p = os.path.join(ROOT, path)
            if not os.path.exists(p):
                continue
            js, bin_ = glb_read(p)
            img = first_image(js, bin_, "base") or first_image(js, bin_)
            if img is None:
                continue
            m = measure(img, sub=2)
            rows.setdefault(kind, {})[tag] = m
            print(line(kind + " " + tag, m))
        print("-" * 92)
    # 요약 — 재칠이 명암을 눌렀나
    print("\n[재칠 전후] span_5_95 · p50_range5 변화")
    for kind, r in rows.items():
        if "재칠전" in r and "지금" in r:
            a, b = r["재칠전"], r["지금"]
            print("  %-12s span %5.1f -> %5.1f (%+.0f%%)   p50r5 %5.1f -> %5.1f (%+.0f%%)"
                  % (kind, a["span_5_95"], b["span_5_95"],
                     (b["span_5_95"] / max(a["span_5_95"], 1e-6) - 1) * 100,
                     a["p50_range5"], b["p50_range5"],
                     (b["p50_range5"] / max(a["p50_range5"], 1e-6) - 1) * 100))
    print("\n[Meshy 원본 대비] 지금")
    for kind, r in rows.items():
        if "Meshy원본" in r and "지금" in r:
            a, b = r["Meshy원본"], r["지금"]
            print("  %-12s span %5.1f -> %5.1f (%+.0f%%)   p50r5 %5.1f -> %5.1f (%+.0f%%)   S %4.1f -> %4.1f"
                  % (kind, a["span_5_95"], b["span_5_95"],
                     (b["span_5_95"] / max(a["span_5_95"], 1e-6) - 1) * 100,
                     a["p50_range5"], b["p50_range5"],
                     (b["p50_range5"] / max(a["p50_range5"], 1e-6) - 1) * 100,
                     a["sat_mean"], b["sat_mean"]))


# ── ② 메시 ────────────────────────────────────────────────────────────────────
def mesh_stats(path):
    js, bin_ = glb_read(path)
    tri = vtx = 0
    area = 0.0
    uva = 0.0
    lo = np.array([1e9] * 3); hi = np.array([-1e9] * 3)
    attrs = set()
    for m in js.get("meshes", []):
        for p in m.get("primitives", []):
            at = p.get("attributes", {})
            attrs |= set(at.keys())
            if "POSITION" not in at:
                continue
            P = acc_read(js, bin_, at["POSITION"])
            vtx += len(P)
            lo = np.minimum(lo, P.min(0)); hi = np.maximum(hi, P.max(0))
            idx = acc_read(js, bin_, p["indices"]).ravel().astype(np.int64)
            tri += len(idx) // 3
            f = idx.reshape(-1, 3)
            a, b, c = P[f[:, 0]], P[f[:, 1]], P[f[:, 2]]
            area += float(np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() * 0.5)
            if "TEXCOORD_0" in at:
                T = acc_read(js, bin_, at["TEXCOORD_0"])
                ta, tb, tc = T[f[:, 0]], T[f[:, 1]], T[f[:, 2]]
                uva += float(np.abs(np.cross(tb - ta, tc - ta)).sum() * 0.5)
    img = first_image(js, bin_, "base") or first_image(js, bin_)
    res = img.size[0] if img else 0
    return dict(tri=tri, vtx=vtx, size=hi - lo, area=area, uva=uva, res=res,
                attrs=sorted(attrs), normal=has_image(js, "normal"),
                nimg=len(js.get("images", [])))


def cmd_mesh():
    print("%-13s %-9s %8s %7s %8s %9s %8s  %s"
          % ("종류", "단계", "삼각형", "정점", "크기m", "표면적m2", "텍셀/m", "속성"))
    print("-" * 104)
    for kind, (cur, bak, orig) in LINEAGE.items():
        for tag, path in (("Meshy원본", orig), ("지금", cur),
                          ("저폴리LOD", cur.replace("web/props/", "web/props/low/"))):
            p = os.path.join(ROOT, path)
            if not os.path.exists(p):
                continue
            s = mesh_stats(p)
            # 텍셀/m : UV 가 덮는 텍셀 수를 표면적으로 나눈 뒤 제곱근
            tpm = ((s["uva"] * s["res"] ** 2 / max(s["area"], 1e-9)) ** 0.5) if s["res"] else 0
            print("%-13s %-9s %8d %7d %8s %9.2f %8.0f  %s%s"
                  % (kind, tag, s["tri"], s["vtx"],
                     "%.1fx%.1fx%.1f" % tuple(s["size"]), s["area"], tpm,
                     ",".join(x.replace("TEXCOORD_0", "UV").replace("POSITION", "P")
                              .replace("NORMAL", "N").replace("TANGENT", "T")
                              for x in s["attrs"]),
                     "  +노멀맵" if s["normal"] else ""))
        print("-" * 104)


# ── ③ 레퍼런스 크롭 ───────────────────────────────────────────────────────────
# 오너 레퍼런스(560x504)에서 손으로 고른 자리. 눈으로 확인하려면 crops 명령을 쓴다.
REF_CROPS = [
    ("레퍼 절벽바위", 60, 20, 120, 150),
    ("레퍼 바위면",   95, 150, 110, 110),
    ("레퍼 나무",      0, 0,  75, 130),
    ("레퍼 수풀",    290, 30, 110, 110),
    ("레퍼 판석길",  330, 360, 150, 120),
]


def cmd_ref():
    p = os.path.join(ROOT, "refpack", "lol_ground_owner_ref.png")
    img = Image.open(p).convert("RGB")
    print("레퍼런스", img.size)
    print(HDR)
    print("-" * 92)
    for name, x, y, w, h in REF_CROPS:
        print(line(name, measure(img.crop((x, y, x + w, y + h)))))


def cmd_crops(out):
    """레퍼런스 크롭 자리를 눈으로 확인한다."""
    p = os.path.join(ROOT, "refpack", "lol_ground_owner_ref.png")
    img = Image.open(p).convert("RGB")
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for name, x, y, w, h in REF_CROPS:
        d.rectangle([x, y, x + w, y + h], outline=(255, 0, 0), width=2)
    img.save(out)
    print("저장", out)


# ── ④ 툰 램프 ─────────────────────────────────────────────────────────────────
# web/main.js 의 조명을 그대로 옮긴 것. ★main.js 를 고치면 여기도 거짓이 된다.
HEMI_SKY = np.array([0xcf, 0xe4, 0xf2]) / 255.0
HEMI_GND = np.array([0x5b, 0x51, 0x40]) / 255.0
HEMI_I = 1.55
KEY_COL = np.array([0xff, 0xf0, 0xd4]) / 255.0
KEY_I = 2.35
RIM_COL = np.array([0x9d, 0xc8, 0xee]) / 255.0
RIM_I = 0.55


def toon_ramp(dotNL):
    """three r160 MeshToonMaterial 의 기본 램프. gradientMap 이 없을 때."""
    return np.where(dotNL * 0.5 + 0.5 > 0.7, 1.0, 0.7)


def shade(albedo_srgb, dotNL_key, dotNL_rim, n_up, ramp=toon_ramp):
    """칠한 색 + 법선 -> 화면색. three 의 툰 조명 + ACES 를 그대로 따른다."""
    alb = CC.srgb_to_lin(albedo_srgb)
    hemi = CC.srgb_to_lin(HEMI_GND) + (CC.srgb_to_lin(HEMI_SKY) - CC.srgb_to_lin(HEMI_GND)) * (0.5 * n_up + 0.5)
    irr = hemi * HEMI_I
    irr = irr + CC.srgb_to_lin(KEY_COL) * KEY_I * ramp(dotNL_key)
    irr = irr + CC.srgb_to_lin(RIM_COL) * RIM_I * ramp(dotNL_rim)
    return CC.lin_to_srgb(CC.aces(alb * irr / np.pi))


def cmd_toon():
    print("""툰 램프가 명암을 얼마나 누르는가 — three r160 MeshToonMaterial 기본값

  램프 = mix(0.7, 1.0, step(dotNL > 0.4))   ★단이 **둘뿐**이고
  ★뒤통수(dotNL=-1)도 0.7 을 받는다. 램버트라면 0 이다.
""")
    lam = lambda d: np.maximum(d, 0.0)
    # 대표 albedo: 지금 바위 텍스처 평균
    for nm, alb in (("바위 #616d73", np.array([0x61, 0x6d, 0x73]) / 255),
                    ("나무잎 #4e623d", np.array([0x4e, 0x62, 0x3d]) / 255)):
        print("── %s ──" % nm)
        print("  %-22s %-9s %-9s %s" % ("면 방향", "툰", "램버트", "툰이 누른 폭"))
        rows = []
        for face, d, up in (("해를 정면으로 (1.0)", 1.0, 0.7),
                            ("비스듬히      (0.5)", 0.5, 0.4),
                            ("경계 바로 위  (0.45)", 0.45, 0.2),
                            ("경계 바로 밑  (0.35)", 0.35, 0.2),
                            ("옆면          (0.0)", 0.0, 0.0),
                            ("뒤통수       (-0.8)", -0.8, -0.3)):
            t = shade(alb, d, d * 0.3, up, toon_ramp)
            l = shade(alb, d, d * 0.3, up, lam)
            Lt = float(np.dot(t * 255, LUMW)); Ll = float(np.dot(l * 255, LUMW))
            rows.append((face, Lt, Ll, t, l))
            print("  %-22s L%5.1f    L%5.1f" % (face, Lt, Ll))
        st = max(r[1] for r in rows) - min(r[1] for r in rows)
        sl = max(r[2] for r in rows) - min(r[2] for r in rows)
        print("  ★명암 폭  툰 %.1f  vs  램버트 %.1f   -> 툰이 %.0f%% 를 눌렀다\n"
              % (st, sl, (1 - st / max(sl, 1e-6)) * 100))


def cmd_labtex():
    """tools/prop_lab.html 이 쓸 Meshy 원본 텍스처를 꺼내 놓는다(파생물).

    ★glb 안에 박혀 있으면 브라우저가 못 읽는다. 실험대는 파일로 물어야 한다.
    """
    out = os.path.join(ROOT, "tools", "labtex")
    os.makedirs(out, exist_ok=True)
    for kind, (cur, bak, orig) in LINEAGE.items():
        js, bin_ = glb_read(os.path.join(ROOT, orig))
        for tag, want in (("", "base"), ("_n", "normal")):
            img = first_image(js, bin_, want)
            if img is None:
                continue
            p = os.path.join(out, kind + tag + ".jpg")
            img.convert("RGB").save(p, "JPEG", quality=88, subsampling=0)
            print("%-14s %-8s %s  %d KB" % (kind, tag or "base", img.size,
                                            os.path.getsize(p) // 1024))


def cmd_all():
    print("\n########## ① 텍스처 계보 ##########\n"); cmd_tex()
    print("\n########## ② 메시 ##########\n"); cmd_mesh()
    print("\n########## ③ 오너 레퍼런스 ##########\n"); cmd_ref()
    print("\n########## ④ 툰 램프 ##########\n"); cmd_toon()


if __name__ == "__main__":
    a = sys.argv[1:]
    c = a[0] if a else "all"
    if c == "tex":
        cmd_tex()
    elif c == "mesh":
        cmd_mesh()
    elif c == "ref":
        cmd_ref()
    elif c == "toon":
        cmd_toon()
    elif c == "labtex":
        cmd_labtex()
    elif c == "crops":
        cmd_crops(a[1])
    else:
        cmd_all()
