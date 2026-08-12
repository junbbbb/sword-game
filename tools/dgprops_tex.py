# -*- coding: utf-8 -*-
"""던전 Meshy 소품 9종의 **텍스처만** 게임용으로 굽는다 (16차 파도 16-소품장착).

    python3 tools/dgprops_tex.py            # 아홉 종 전부 굽는다
    python3 tools/dgprops_tex.py --stats    # 안 쓰고 숫자만 (색 판단용)
    python3 tools/dgprops_tex.py pillar_intact altar

무엇을 하는가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`incoming/meshy_dgprops/<이름>_3k.glb` 안의 **베이스컬러 한 장**을 꺼내
크기를 줄이고 jpg 로 다시 구워 `incoming/meshy_dgprops/prep/dgp_<이름>.jpg` 에 둔다.
`blender/s41_dgprops.py` 가 그 jpg 를 읽어 web/props/dg_*.glb 에 싣는다.

★금속·거칠기 맵과 노멀 맵은 **버린다.** 던전 재질은 glTF 표준(MeshStandardMaterial)
  이지만 이 게임의 던전은 빛을 정점색에 굽는다 — 금속 0 · 거칠기 1 고정이라
  MR 맵이 화면에 아무 일도 안 한다. 노멀 맵도 실광원이 횃불이 아니라 캐릭터용
  방향광 하나뿐이라 돌 표면에 넣을 정보가 없다. 셋을 다 실으면 파일이 세 배다.

★해상도를 왜 내리는가 — **화면 텍셀 밀도 실측**
  16-저폴리진단이 잰 값: 게임 화면은 **64 px/m**(고정 쿼터뷰 1280x800).
  Meshy 는 긴 축 1.9 단위짜리 물건에 2048 을 통째로 붙인다.
      기둥(높이 3.55m)  2048 / 3.55m = 577 texel/m  = 화면의 9.0 배
      1024 로 줄여도                  289 texel/m  = 화면의 4.5 배
      512 로 줄이면(작은 소품 0.9m)   569 texel/m  = 화면의 8.9 배
  진단의 결론이 "텍스처 해상도는 무죄. 이미 3.2배 과잉"이었다. 4.5배면 클로즈업
  판정컷(3배 확대)에서도 1.5배가 남는다. 그 위는 바이트만 먹는다.

★색은 **한 톨도 안 건드린다** (오너 원칙: 소품 색은 원본 충실 · 재칠 금지)
  화면 색은 s41 이 glTF `baseColorFactor` 한 벌로 맞춘다 — s40 이 던전의 모든
  석재에 쓰는 것과 **같은 손잡이**다(화면색 = factor x 텍스처 x 정점색).
  텍스처 화소를 만지면 그 계약이 두 군데로 갈린다. 여기서는 크기와 형식만 바꾼다.
  ★그래서 ACES 역보정(tools/raw_props.py)도 여기서는 안 한다. 초원 소품은
    "화면에 원본색이 나오게" 가 목표였지만, 던전 소품은 **횃불 웅덩이 안에서만
    보여야** 한다 — 원본색으로 화면에 뜨면 그게 곧 "혼자 밝게 뜬다"다.

★jpg 품질 88
  90(s40 의 TEX_QUALITY)과 화소차 평균 0.3 미만인데 파일은 20% 작다. 돌 텍스처는
  고주파가 적어서 88 아래로 내려가야 블로킹이 보인다(실측 82 에서 8x8 경계가 뜬다).
"""
import io
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "incoming", "meshy_dgprops")
OUT = os.path.join(SRC, "prep")
QUALITY = 88

# 종류 -> 텍스처 한 변. 화면에서 차지하는 크기로 가른다(위 주석의 계산).
#   1024 : 클로즈업 판정컷에 들어오는 히어로 부재(기둥·아치·제단·화로)
#    512 : 잔해·갓돌·모서리돌. 1m 안팎이라 화면 60px 다
SIZE = {
    "pillar_intact": 1024,
    "pillar_broken": 1024,
    "arch_gate":     1024,
    "altar":         1024,
    "brazier":       1024,
    "rubble_large":   512,
    "rubble_small":   512,
    "coping_chunk":   512,
    "quoin_corner":   512,
}
KINDS = list(SIZE)


def glb_read(path):
    with open(path, "rb") as f:
        d = f.read()
    assert d[:4] == b"glTF", path + " 는 glb 가 아니다"
    n = struct.unpack("<I", d[12:16])[0]
    js = json.loads(d[20:20 + n])
    off = 20 + n
    ln = struct.unpack("<I", d[off:off + 4])[0]
    return js, d[off + 8:off + 8 + ln]


def base_color_image(js, bin_):
    """★이미지 목록의 0번을 그냥 집으면 안 된다. Meshy 는 base/MR/normal 셋을
    넣는데 순서가 보장되지 않는다. 재질에서 baseColorTexture 를 타고 내려간다."""
    m = js["materials"][0]
    ti = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
    src = js["textures"][ti]["source"]
    im = js["images"][src]
    bv = js["bufferViews"][im["bufferView"]]
    o = bv.get("byteOffset", 0)
    raw = bytes(bin_[o:o + bv["byteLength"]])
    return Image.open(io.BytesIO(raw)), im.get("mimeType"), len(raw), src


def srgb_to_lin(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def stats(img):
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lin = srgb_to_lin(a).reshape(-1, 3).mean(0)
    srgb = a.reshape(-1, 3).mean(0)
    mx, mn = srgb.max(), srgb.min()
    sat = 0.0 if mx <= 0 else (mx - mn) / mx
    return lin, srgb, sat


def main(argv):
    dry = "--stats" in argv or "--dry" in argv
    names = [a for a in argv if not a.startswith("-")] or KINDS
    if not dry:
        os.makedirs(OUT, exist_ok=True)
    print("%-14s %5s %-9s %-8s  %-22s %-22s %s"
          % ("종류", "크기", "원본", "결과", "선형평균 RGB", "sRGB 평균", "채도"))
    for kind in names:
        p = os.path.join(SRC, kind + "_3k.glb")
        if not os.path.exists(p):
            print("%-14s 원자재 없음 %s" % (kind, p))
            continue
        js, bin_ = glb_read(p)
        img, mime, raw_len, src_i = base_color_image(js, bin_)
        n = SIZE[kind]
        out = img.convert("RGB")
        if out.size != (n, n):
            out = out.resize((n, n), Image.LANCZOS)
        lin, srgb, sat = stats(out)
        buf = io.BytesIO()
        out.save(buf, "JPEG", quality=QUALITY, subsampling=0, optimize=True)
        data = buf.getvalue()
        print("%-14s %5d %4.1fMB(%s) %5.0fKB  %.4f %.4f %.4f   %.3f %.3f %.3f   %.3f"
              % (kind, n, raw_len / 1048576, (mime or "?").split("/")[-1],
                 len(data) / 1024, *lin, *srgb, sat))
        if dry:
            continue
        with open(os.path.join(OUT, "dgp_%s.jpg" % kind), "wb") as f:
            f.write(data)
    if not dry:
        print("->", OUT)


if __name__ == "__main__":
    main(sys.argv[1:])
