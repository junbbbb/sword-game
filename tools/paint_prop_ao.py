# -*- coding: utf-8 -*-
"""구워 둔 가림(AO)을 소품 베이스컬러에 **칠해 넣는다**.

    python3 tools/paint_prop_ao.py            # 전부
    python3 tools/paint_prop_ao.py rock tree  # 몇 개만
    python3 tools/paint_prop_ao.py --dry      # 안 쓰고 숫자만
    python3 tools/paint_prop_ao.py --restore  # .bak_v96ao 로 되돌린다

★★2026-08-11 (12-소품원색 1차+2차) — **열한 종 전부 이 파일로 칠하지 마라**
  tree · rock · boulder_xl · crag · bush · cliff_tall_b (1차)
  cliff_tall · outcrop · bank · slab · thicket (2차) 은 tools/raw_props.py 가
  원본 -> **AO 곱(화면 쪽)** -> ACES 역산 을 한 번에 한다(순서가 여기와 다르다).
  이 파일로 덧칠하면 가림이 두 번 들어간다. `--restore` 도 쓰지 마라 —
  `.bak_v96ao` 는 **재칠 시절의 가림 전** 텍스처라 원색판이 팔레트판으로 되돌아간다
  (되돌릴 자리는 `.bak_v98_regrade` 이고 손잡이는 `raw_props.py --restore` 다).
  ★단 outcrop 의 `.bak_v96ao` 는 지우면 안 된다. 원자재가 없어서 raw_props.py 의
    SRC 가 그 파일을 **출발점으로 읽는다**(지우면 outcrop 은 다시 못 굽는다).
  ★이 파일 자체는 살아 있다. AO 맵(blender/tex/prop_ao/)을 다시 구우면 세기 표(SPEC)를
    raw_props.py 가 그대로 가져다 쓴다 — 가림의 정본은 아직 여기다.

왜 필요한가 — 11차 소품 진단(2026-08-11)의 결론
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너: "나무랑 돌 같은 거 Meshy 한 거 맞아? 너무 저퀄 느낌 나서."
자를 대 보니 진범은 텍스처도 재칠도 아니고 **명암 모델링이 통째로 없는 것**이었다.

    같은 바위를 해 쪽 / 반대쪽에서 찍어 밝기를 비교(실측)
      오너 레퍼런스(롤) 바위 ......... 1.63 배
      우리 소품 ...................... 1.13 배     <- 사실상 평면
      민무늬로 조명만 재면 ........... 1.10 배 (램버트라면 1.45)

three r160 MeshToonMaterial 의 기본 램프가 **두 단(0.7 / 1.0)** 뿐이고 뒤통수도
해의 70% 를 받는다. 조명이 만드는 명암의 **78% 를 램프가 버린다.**
게다가 실시간 그림자 상자는 캐릭터 ±10m 뿐이라 나머지 소품엔 그림자가 없다.

셋 다 자산으로는 못 고친다. 자산이 할 수 있는 일은 하나 —
**그늘을 그림에 미리 칠해 두는 것**이다. 롤·오버워치 손그림 텍스처의 수법이고
(빛을 albedo 에 그려 넣는다) 램프가 무엇이든 항상 보인다.
LOG 의 "매크로 그늘은 바닥 텍스처에 굽는 게 유일한 답이다"(v96 지형)와 같은 논리다.

칠하는 식
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ① AO 를 눅인다   k = 1 - AMT * (1 - ao^GAMMA)      k ∈ [FLOOR, 1]
    ② 선형에서 곱한다  albedo_lin *= k
    ③ **평균을 되돌린다**  채널 배수로 평균 RGB 를 칠하기 전 값에 다시 앉힌다

  ★③ 이 없으면 안 된다. AO 는 평균을 20~30% 떨어뜨리는데, 소품 색은
    tools/regrade_props.py 가 **화면 목표색**에 맞춰 놓은 값이다. 그냥 곱하면
    맵 전체가 어두워지고 v96 이 세운 색계약이 조용히 깨진다.
    평균을 되돌려도 **대비는 남는다** — 그게 이 칠의 목적이다.
  ★sRGB 가 아니라 **선형에서** 곱한다. LOG v96: "sRGB 에서 곱하는 그늘은
    숫자보다 훨씬 깊다(곱수 0.72 가 빛으로는 0.47)". 그늘을 빛의 양으로 다뤄야
    두 배 어두운 게 진짜 두 배가 된다.

★지오메트리는 한 톨도 안 건드린다(POSITION 해시로 증명한다).
★LOD(web/props/low/)는 칠하지 않는다 — props.js 가 **고폴리 텍스처를 두 단계가
  같이 쓰기** 때문이다(저폴리 glb 안의 텍스처는 로드 즉시 dispose 된다).
"""
import io
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import color_contract as CC          # noqa: E402
from regrade_props import glb_read, glb_write, pos_hash   # noqa: E402

PROPS = os.path.join(ROOT, "web", "props")
AO = os.path.join(ROOT, "blender", "tex", "prop_ao")
BAK = ".bak_v96ao"

# 종류별 세기.
#   AMT   가림을 얼마나 믿을 것인가(1.0 = AO 그대로)
#   GAMMA AO 를 눅이는 감마(>1 이면 옅은 그늘이 사라지고 깊은 틈만 남는다)
#   FLOOR 제일 어두운 자리의 하한(0.30 이면 아무리 깊어도 30% 는 남는다)
# ★초목은 약하게. 잎은 원래 서로 가려서 AO 가 온통 어둡게 나오는데 그걸 다 칠하면
#   덩어리가 먹빛이 된다(수풀은 props.js 가 정점색으로 이미 안쪽 그늘을 굽는다).
SPEC = {
    "rock":       (0.85, 1.15, 0.30),
    "crag":       (0.90, 1.10, 0.28),   # 텍스처가 비어 있어 그늘이라도 넣어야 형태가 산다
    "outcrop":    (0.85, 1.15, 0.30),
    "boulder_xl": (0.85, 1.15, 0.30),
    "cliff_tall": (0.80, 1.20, 0.32),
    "cliff_tall_b": (0.80, 1.20, 0.32),   # ★11-소품B 변주. 원본과 같은 세기여야 한 줄로 읽힌다
    "bank":       (0.80, 1.20, 0.32),
    "slab":       (0.70, 1.25, 0.38),   # 밟는 바닥이라 덜 어둡게
    "tree":       (0.70, 1.30, 0.38),
    "bush":       (0.45, 1.45, 0.55),   # ★정점색 그늘과 겹친다. 약하게
    "thicket":    (0.50, 1.40, 0.52),
}


def load_ao(kind, size):
    p = os.path.join(AO, kind + ".png")
    if not os.path.exists(p):
        return None
    a = Image.open(p).convert("L")
    if a.size != size:
        a = a.resize(size, Image.LANCZOS)
    return np.asarray(a, np.float32) / 255.0


def paint(img, ao, spec):
    amt, gam, floor = spec
    k = 1.0 - amt * (1.0 - np.clip(ao, 0, 1) ** gam)
    k = np.clip(k, floor, 1.0)[:, :, None]
    src = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lin = CC.srgb_to_lin(src)
    m0 = lin.reshape(-1, 3).mean(0)                 # 칠하기 전 평균(선형)
    out = lin * k
    # ③ 평균 되돌리기. 두 번 돌린다 — 자르기가 평균을 조금 되민다(regrade 와 같은 이유)
    for _ in range(2):
        m = out.reshape(-1, 3).mean(0)
        g = np.clip(m0 / np.maximum(m, 1e-6), 0.2, 5.0)
        out = np.clip(out * g[None, None, :], 0.0, 1.0)
    return Image.fromarray(np.uint8(np.clip(CC.lin_to_srgb(out), 0, 1) * 255 + 0.5))


LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)


def stats(img):
    a = np.asarray(img.convert("RGB"), np.float32)
    L = a @ LUMW
    p = np.percentile(L, [5, 95])
    return L.mean(), p[1] - p[0], "#%02x%02x%02x" % tuple(
        int(x + .5) for x in a.reshape(-1, 3).mean(0))


def restore():
    n = 0
    for f in sorted(os.listdir(PROPS)):
        if not f.endswith(BAK):
            continue
        src = os.path.join(PROPS, f)
        dst = os.path.join(PROPS, f[:-len(BAK)])
        os.replace(src, dst)
        print("되돌림", os.path.basename(dst))
        n += 1
    print("총 %d개" % n)


def main(argv):
    if "--restore" in argv:
        restore()
        return
    dry = "--dry" in argv
    names = [a for a in argv if not a.startswith("-")]
    for f in sorted(os.listdir(PROPS)):
        if not f.endswith(".glb"):
            continue
        kind = f[:-4]
        if kind not in SPEC or (names and kind not in names):
            continue
        path = os.path.join(PROPS, f)
        js, bin_ = glb_read(path)
        h0 = pos_hash(js, bin_)
        if not js.get("images"):
            print("%-12s 텍스처 없음" % kind)
            continue
        im0 = js["images"][0]
        bv = js["bufferViews"][im0["bufferView"]]
        o = bv.get("byteOffset", 0)
        src = bytes(bin_[o:o + bv["byteLength"]])
        img = Image.open(io.BytesIO(src))
        ao = load_ao(kind, img.size)
        if ao is None:
            print("%-12s AO 없음 — blender/s29_prop_ao.py 를 먼저 돌려라" % kind)
            continue
        new = paint(img, ao, SPEC[kind])
        b0, s0, x0 = stats(img)
        b1, s1, x1 = stats(new)
        print("%-12s 평균L %5.1f -> %5.1f   span %5.1f -> %5.1f (%+.0f%%)   %s -> %s"
              % (kind, b0, b1, s0, s1, (s1 / max(s0, 1e-6) - 1) * 100, x0, x1))
        if dry:
            continue
        buf = io.BytesIO()
        if (im0.get("mimeType") or "").endswith("jpeg"):
            new.save(buf, "JPEG", quality=90, subsampling=0)
        else:
            new.save(buf, "PNG", optimize=True)
        data = buf.getvalue()
        # ── bufferView 갈아 끼우기 (regrade_props.py 와 같은 절차) ──
        old_len = bv["byteLength"]
        pad = (4 - len(data) % 4) % 4
        old_pad = (4 - old_len % 4) % 4
        delta = (len(data) + pad) - (old_len + old_pad)
        bin2 = bytearray(bytes(bin_[:o]) + data + b"\0" * pad
                         + bytes(bin_[o + old_len + old_pad:]))
        bv["byteLength"] = len(data)
        for other in js["bufferViews"]:
            if other is not bv and other.get("byteOffset", 0) > o:
                other["byteOffset"] = other.get("byteOffset", 0) + delta
        js["buffers"][0]["byteLength"] = len(bin2)
        h1 = pos_hash(js, bin2)
        if h0 != h1:
            print("   ★POSITION 해시가 바뀌었다(%s -> %s). 안 쓴다." % (h0, h1))
            continue
        bak = path + BAK
        if not os.path.exists(bak):
            with open(bak, "wb") as fb:
                fb.write(open(path, "rb").read())
        glb_write(path, js, bin2)
        print("   저장 (POSITION %s 그대로 · %d KB)" % (h1, os.path.getsize(path) // 1024))


if __name__ == "__main__":
    main(sys.argv[1:])
