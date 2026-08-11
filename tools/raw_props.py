# -*- coding: utf-8 -*-
"""소품 텍스처 **원색 장착** — Meshy 원본 색을 게임 화면에 그대로 앉힌다.

    python3 tools/raw_props.py                 # 여섯 종 전부
    python3 tools/raw_props.py tree rock       # 몇 개만
    python3 tools/raw_props.py --dry           # 안 쓰고 숫자만
    python3 tools/raw_props.py --no-ao         # 가림(AO) 없이 색만
    python3 tools/raw_props.py --restore       # .bak_v98_regrade 로 되돌린다

왜 필요한가 — 오너 판정 (2026-08-11, 12차 파도 12-소품원색)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너: **"나무나 지형지물 Meshy에서 뽑힌 거 보니 맘에 드는데 왜 게임 속에 넣으니
이상해지냐? 채도나 뭐 이런 것들 건드린 거냐?"**
답은 "건드렸다" 다. `tools/regrade_props.py` 가 **팔레트 목표색**으로 다시 칠했다
(채도 배수 · 명암폭 배수 · 채널 평균 맞추기 · 조명배수). 그 재칠의 근거는
"기존 맵 팔레트와 조화" 였는데, 바닥이 codex 판으로 갈린 지금 그 목표는 낡았다.
오너 선호는 **Meshy/codex 원본 색** 이다.

그래서 이 파일이 재칠을 대신한다. 하는 일은 **딱 하나** —

    ACES 역보정.  "원본 텍스처의 sRGB 색"이 **게임 화면에서 그 색으로 보이게** 한다.

게임은 `renderer.toneMapping = ACESFilmicToneMapping`(노출 1.05)이라 칠한 색이
화면에 그대로 안 나온다(LOG ★★진범은 조명이 아니라 ACES 톤매핑이었다).
그러니 "원본 충실"은 텍스처를 **그대로 두는 것**이 아니라, 화면을 지난 결과가
원본이 되도록 **미리 거꾸로 밀어 두는 것**이다. 그 역산이 tools/color_contract.py
(= tools/aces_screen.py 와 같은 식)의 `screen_to_paint` 다.

    칠할 색 = screen_to_paint(원본 sRGB, 조도 x lit)
    화면 색 = paint_to_screen(칠할 색, 조도 x lit) = 원본 sRGB      ← 이게 정의다

regrade_props.py 와 무엇이 다른가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    껐다: 팔레트 화면목표색 · 채도 배수/더하기 · 명암폭 배수 g · 채널 평균 맞추기 ·
          자홍 제거 · 잎/껍질 가르기
    남겼다: ACES 역보정 하나 (+ 아래 lit)
색상(hue)도 채도도 명암 구조도 **원본 것을 한 톨도 안 옮긴다.** 화소마다 따로
역산하므로 붓자국·이끼·지층은 물론 원본의 채도 분포까지 그대로 산다.

★조명배수(lit) 는 재칠이 아니다 — 이것도 "원본 충실" 쪽 손잡이다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
색계약의 조도 1.0 은 **평평한 바닥**의 값이다. 소품은 그 위에 선 덩어리라 실제로
받는 빛이 1.0 이 아니다(각진 판 무더기는 위를 보는 면이 늘어 더 밝고, 매끈한 돔은
빛을 비껴 받아 더 어둡다). lit 은 그 차이를 되돌려 **화면 평균이 원본 텍스처 평균에
앉게** 하는 값이다. 팔레트를 향해 미는 값이 아니라, 원본을 향해 되돌리는 값이다.
그래서 1.0 으로 두면 오히려 원본에서 멀어진다.
★값은 감으로 안 정한다. **lit = 1.0 으로 한 벌 굽고 게임 화면을 실측한 뒤**
  (화면 휘도 / 원본 텍스처 휘도) 가 1.0 이 되게 되돌린다. 절차는 LOG
  "★★소품 하나의 화면색을 정확히 재는 법" 그대로다(종류를 껐다 켠 두 장의 차이).

★가림(AO) 은 **화면 쪽에서** 곱한다 (regrade 시절과 순서가 다르다)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AO 는 색이 아니라 **형태**라서 원본 인상을 안 해친다. 다만 곱하는 자리가 중요하다.
    옛 순서:  원본 -> 재칠(칠할 값) -> AO 곱 ......... AO 대비가 ACES 를 지나며 눌린다
    이 파일:  원본 -> **AO 곱(화면 쪽에서)** -> ACES 역산
이 순서라야 "화면에 보이는 것 = 원본색 x 가림" 이 된다. 평균 되돌리기는
paint_prop_ao.py 와 같다(선형에서 곱하고 평균을 되돌린다 — 안 되돌리면 맵이 어두워진다).

★지오메트리는 한 톨도 안 건드린다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
blender/s30_props_v2.py 가 구운 봉투(zfit)·삼각형·UV 를 그대로 두고 **glb 안의
베이스컬러 이미지 한 장만** 갈아 끼운다. POSITION 해시를 찍어 증명한다
(regrade_props.py 와 같은 절차 · 원자적 교체).
★원본 텍스처가 2048x2048 이고 s30 의 TEX_SIZE 도 2048 이라 **크기 조정이 없다** —
  incoming 의 이미지가 web/props/*.glb 의 이미지와 화소 대 화소로 맞는다
  (검증: 원본 vs 재칠본 휘도 상관 0.93~0.997).
★web/props/low/ 는 안 건드린다. props.js 가 저폴리 glb 의 텍스처를 로드 즉시
  dispose 하고 **고폴리 텍스처를 두 단계가 같이 쓴다**(LOG 11차 소품 진단).
"""
import io
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import color_contract as CC                                  # noqa: E402
from regrade_props import glb_read, glb_write, pos_hash      # noqa: E402
from paint_prop_ao import SPEC as AO_SPEC, load_ao           # noqa: E402

PROPS = os.path.join(ROOT, "web", "props")
BAK = ".bak_v98_regrade"        # 재칠판(12차 파도 이전 상태)

# 종류 -> (원본 glb, 베이스컬러 이미지 인덱스)
# ★dl_a/b/c 의 짝은 s30_props_v2.py 의 KINDS 표가 정본이다(메시 통계로 갈랐다).
SRC = {
    "tree":         ("incoming/meshy_props_v3/dl_c.glb", 0),
    "rock":         ("incoming/meshy_props_v3/dl_b.glb", 0),
    "boulder_xl":   ("incoming/meshy_props_v3/dl_a.glb", 0),   # 1=러프니스 2=노멀(안 쓴다)
    "crag":         ("incoming/meshy_props_v2/crag_v2.glb", 0),
    "bush":         ("incoming/meshy_props_v2/bush_v2.glb", 0),
    "cliff_tall_b": ("incoming/meshy_props_v2/cliff_var_v2.glb", 0),
}

# 조명배수. 1.0 = 평평한 바닥과 같은 빛(색계약 기본값).
# ★게임 화면 실측으로 채운다 — 자세한 것은 위 ★조명배수 주석.
#   측정 절차: tools/raw_props.py 로 lit=1.0 한 벌 굽기 -> 게임에서 종류별 화면 평균
#   휘도 측정(종류를 껐다 켠 두 장의 차이) -> lit *= (화면휘도 / 원본텍스처휘도).
#
# ★2026-08-11 1차 실측(lit 전부 1.00 으로 굽고 게임 화면에서 종류별로 잰 값).
#   E = 그 소품이 실제로 받는 조도. paint_to_screen(칠한값평균, 조도xE) 가 화면
#   실측색이 되는 E 를 이분법으로 풀었다. **화면색 = 원본색** 이 되려면 lit = E 다.
#       tree 1.01 · boulder_xl 1.02   -> 그대로 둔다(오차 2% 안)
#       rock 1.48 · cliff_tall_b 1.40 · crag 1.32
#         -> 셋 다 **각진 판 무더기**라 위를 보는 면이 늘었다(LOG 11-소품B·C 의 그 함정).
#            안 고치면 못 가는 바위가 맵에서 제일 창백한 물건이 된다. 재서 되돌린다.
#       bush 0.70 -> **안 고친다.** 수풀이 어두운 것은 조명이 모자라서가 아니라
#         props.js 가 **정점색으로 밑동·구역 안쪽 그늘을 굽기** 때문이다(은신 연출).
#         lit 로 되돌리면 그 장치를 통째로 지우고 볕 든 겉잎이 원본보다 18% 밝아진다.
#         (재칠 시절에도 bush 는 화면이 목표의 0.75 였고 아무도 안 고쳤다 — 같은 이유다.)
#         ※ 오너가 "수풀이 어둡다" 고 판정하면 여기 0.70 을 적는 것으로 끝난다.
LIT = {
    "tree":         1.00,
    "rock":         1.48,
    "boulder_xl":   1.00,
    "crag":         1.32,
    "bush":         1.00,
    "cliff_tall_b": 1.40,
}

LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)


def read_tex(path, idx=0):
    """glb 안의 이미지 한 장을 PIL 로 꺼낸다."""
    js, bin_ = glb_read(path)
    im = js["images"][idx]
    bv = js["bufferViews"][im["bufferView"]]
    o = bv.get("byteOffset", 0)
    return Image.open(io.BytesIO(bytes(bin_[o:o + bv["byteLength"]]))).convert("RGB")


def sat_mean(a01):
    """평균 채도(HSV S). a01 은 0~1 sRGB 배열."""
    mx = a01.max(-1)
    mn = a01.min(-1)
    return float(np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0).mean())


def describe(a01, tag):
    m = a01.reshape(-1, 3).mean(0)
    return "%s %s S%5.1f%% 휘도%6.1f" % (tag, CC.hexs(m), sat_mean(a01) * 100,
                                        float((a01 @ LUMW).mean()) * 255)


def apply_ao(target01, ao, spec):
    """화면 목표색에 가림을 곱한다(선형) + 평균 되돌리기. paint_prop_ao.paint 와 같은 식."""
    amt, gam, floor = spec
    k = np.clip(1.0 - amt * (1.0 - np.clip(ao, 0, 1) ** gam), floor, 1.0)[:, :, None]
    lin = CC.srgb_to_lin(target01)
    m0 = lin.reshape(-1, 3).mean(0)
    out = lin * k
    for _ in range(2):                      # 자르기가 평균을 되미므로 두 번
        m = out.reshape(-1, 3).mean(0)
        out = np.clip(out * np.clip(m0 / np.maximum(m, 1e-6), 0.2, 5.0)[None, None, :],
                      0.0, 1.0)
    return np.asarray(CC.lin_to_srgb(out), np.float64)


def invert_aces(target01, irr, rows=128):
    """화면 목표(0~1 sRGB) -> 칠할 색. 줄 단위로 잘라 푼다(4M 화소 x 40회라 통째로는 무겁다).

    ★도달 못 하는 목표가 있다(ACES 가 못 내는 밝기·채도). 최대 오차를 같이 돌려준다."""
    out = np.empty_like(target01)
    worst = 0.0
    for y in range(0, target01.shape[0], rows):
        blk = target01[y:y + rows]
        p, err = CC.screen_to_paint(blk, irr)
        out[y:y + rows] = p
        worst = max(worst, err)
    return out, worst


def swap_texture(path, kind, new_img, mime_jpeg=True):
    """glb 의 첫 이미지를 갈아 끼운다(regrade_props.py 와 같은 절차)."""
    js, bin_ = glb_read(path)
    h0 = pos_hash(js, bin_)
    im0 = js["images"][0]
    bv = js["bufferViews"][im0["bufferView"]]
    o = bv.get("byteOffset", 0)
    old_len = bv["byteLength"]
    buf = io.BytesIO()
    if (im0.get("mimeType") or "").endswith("jpeg"):
        new_img.save(buf, "JPEG", quality=90, subsampling=0)
    else:
        new_img.save(buf, "PNG", optimize=True)
    data = buf.getvalue()
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
        raise RuntimeError("%s: POSITION 해시가 바뀌었다(%s -> %s)" % (kind, h0, h1))
    bak = path + BAK
    if not os.path.exists(bak):
        with open(bak, "wb") as f:
            f.write(open(path, "rb").read())
    glb_write(path, js, bin2)
    return h1, len(data)


def restore():
    n = 0
    for f in sorted(os.listdir(PROPS)):
        if not f.endswith(BAK):
            continue
        os.replace(os.path.join(PROPS, f), os.path.join(PROPS, f[:-len(BAK)]))
        print("되돌림", f[:-len(BAK)])
        n += 1
    print("총 %d개" % n)


def main(argv):
    if "--restore" in argv:
        restore()
        return
    dry = "--dry" in argv
    use_ao = "--no-ao" not in argv
    names = [a for a in argv if not a.startswith("-")]
    for kind in (names or list(SRC)):
        if kind not in SRC:
            print("모르는 종류:", kind)
            continue
        src_path = os.path.join(ROOT, SRC[kind][0])
        dst_path = os.path.join(PROPS, kind + ".glb")
        orig = np.asarray(read_tex(src_path, SRC[kind][1]), np.float64) / 255.0
        cur = np.asarray(read_tex(dst_path), np.float64) / 255.0
        lit = LIT.get(kind, 1.0)
        print("\n===== %s  (lit %.2f%s) =====" % (kind, lit, "" if use_ao else " · AO 없음"))
        print("   " + describe(orig, "원본 텍스처 "))
        print("   " + describe(cur, "현 재칠판   "))

        target = orig
        if use_ao:
            ao = load_ao(kind, (orig.shape[1], orig.shape[0]))
            if ao is None:
                print("   ★AO 없음 — blender/s29_prop_ao.py 를 먼저 돌려라. 색만 간다.")
            else:
                target = apply_ao(orig, ao, AO_SPEC[kind])
                print("   " + describe(target, "가림 얹은 뒤"))

        paint, err = invert_aces(target, CC.IRRADIANCE * lit)
        back = CC.paint_to_screen(paint, CC.IRRADIANCE * lit)
        print("   " + describe(paint, "칠할 값     "))
        print("   " + describe(np.asarray(back, np.float64), "예측 화면색 ")
              + "   역산오차 %.1f/255" % (err * 255))
        # 예측 화면색 vs 원본: 이 두 줄이 같아야 "원본 충실"이다
        d = (np.asarray(back, np.float64) - target).reshape(-1, 3)
        ad = np.abs(d).max(1) * 255
        print("   ※ 예측화면 - 목표 : 평균 %+.2f/255  p99 %.1f  p99.9 %.1f  최대 %.1f"
              " (2/255 넘는 화소 %.3f%%)"
              % (d.mean() * 255, np.percentile(ad, 99), np.percentile(ad, 99.9),
                 ad.max(), float((ad > 2).mean()) * 100))
        if dry:
            continue
        img = Image.fromarray(np.uint8(np.clip(paint, 0, 1) * 255 + 0.5))
        h1, nb = swap_texture(dst_path, kind, img)
        print("   저장 (POSITION %s 그대로 · 텍스처 %d KB · 파일 %d KB)"
              % (h1, nb // 1024, os.path.getsize(dst_path) // 1024))


if __name__ == "__main__":
    main(sys.argv[1:])
