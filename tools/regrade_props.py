# -*- coding: utf-8 -*-
"""지형 소품(web/props/*.glb) 안에 박힌 손그림 텍스처를 다시 칠한다.

★★★ 2026-08-11 (12차 파도 12-소품원색) — **여섯 종은 이 파일이 더 이상 안 칠한다** ★★★
    tree · rock · boulder_xl · crag · bush · cliff_tall_b
    오너 판정 "Meshy 에서 뽑힌 건 맘에 드는데 게임에 넣으니 이상해진다. 채도 건드린 거냐"
    -> 답은 "건드렸다" 였고, 그 여섯은 **tools/raw_props.py**(원색 + ACES 역보정)로 옮겼다.
    이 파일을 이름 없이 그냥 돌리면 그 여섯이 팔레트로 도로 칠해진다. **하지 마라.**
    (남은 종류 thicket · outcrop · cliff_tall · bank · slab 은 아직 이 파일 소유다.)

    python3 tools/regrade_props.py            # 전부  ← ★위 여섯 종은 빼고 부를 것
    python3 tools/regrade_props.py bush rock  # 몇 개만
    python3 tools/regrade_props.py --dry      # 안 쓰고 숫자만

왜 필요한가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너 판정: "레퍼런스처럼. 깊은 그늘이 있는 진초록 풀, 어두운 수풀, 지층 결이
보이는 절벽 바위." 바닥은 s20 이 고쳤는데 **화면 면적의 30~50%가 소품**이다.
2026-08-11 실측(화면 기준):

    수풀  #80a774 (S 30.5% V 65.5%)     레퍼런스의 어두운 수풀 #282a2d~#2d3e2b
    바위  #8a99a2 (S 15.0% V 63.5%)     레퍼런스의 절벽 바위   #434542~#2c3e30
    판석  #8c8f84 (S  8.1% V 56.3%)     걸어 다니는 바닥보다 밝고 무채색이다

바닥과 같은 병이다 — ACES 가 밝은 쪽 채도를 씻는데 텍스처가 그 구간(V 56~66%)에
통째로 올라가 있다. 그래서 **V 를 내리고 S 를 올린다.**

방법 — 지오메트리를 한 톨도 안 건드린다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너 승인 방향이 "poly 낮게 하고 그 면에 그림 그려놓는 방법" 이다. 그래서 이
파일은 **텍스처만** 바꾼다. glb 의 정점 버퍼는 바이트째로 그대로 옮긴다
(POSITION 해시를 찍어 증명한다). 삼각형·LOD·콜라이더가 움직일 수 없다.

칠하는 식(HSV):
    V' = Vt * (V / Vm) ** g      Vm = 지금 평균, Vt = 목표 평균, g = 명암 폭 배수
    S' = clamp( S * s + b )
  ★g > 1 이면 **명암 폭이 넓어진다.** 심사 1번 격차가 그것이라 g 를 1 이상으로 둔다.
  ★평균을 목표에 맞추는 것이지 색을 평칠하는 게 아니다. 손그림의 결(붓자국·이끼·
    지층)은 비율로 남으므로 그대로 산다.

목표색은 감으로 안 정한다. tools/color_contract.py 로 **화면 목표 -> 칠할 값**을
거꾸로 풀어 쓴다(같은 함정: 칠한 색은 화면에 그대로 안 나온다).
"""
import os
import io
import sys
import json
import struct
import hashlib

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import color_contract as CC   # noqa: E402

PROPS = os.path.join(ROOT, "web", "props")

# ── 목표표 ──
# (화면 목표 평균색, 채도 배수, 채도 더하기, 명암폭 배수 g
#  [, 자홍제거][, 조명배수][, 껍질 칠할값])
# ★마지막 칸(껍질)은 **화면 목표가 아니라 칠할 값**이다. 껍질은 화면 색계약이 없다
#   (팔레트 계약은 잎 기준이다). 교체 전 출고본의 껍질 텍스처 색에 그대로 앉힌다.
#
# ★조명배수(lit) — s28_terrain.py 의 gain 과 같은 자리다 (2026-08-11 11-소품B)
#   색계약(tools/color_contract.py)의 조도 1.0 은 **평평한 바닥**의 값이다. 소품은
#   그 위에 서 있는 덩어리라 위를 보는 면이 훨씬 많고, 그만큼 더 밝게 그려진다.
#   그래서 "칠한 색"을 계약대로 앉혀도 화면색은 목표를 넘어선다.
#   s28 은 이걸 gain 이라는 스칼라로 눌렀는데(boulder_xl 0.82 · cliff_tall 0.76),
#   여기서는 **조도 자체를 곱해 역산**한다 — 스칼라로 누르면 색상이 같이 밀리지만
#   조도를 곱해 되풀면 hue 가 안 움직인다.
#   값은 감이 아니라 **게임 화면 실측**으로 맞춘다:
#       화면 크롭에서 그 소품 화소의 평균색을 재고
#       paint_to_screen(텍스처 평균, IRRADIANCE x k) 가 그 값이 되는 k 를 찾는다.
#   ★적을 값이 없으면 1.0 = 예전과 완전히 같은 계산이다(다른 종류의 산출물 불변).
# ★화면 목표는 오너 레퍼런스 실측에서 출발해 "밝은 판타지" 쪽으로 한 단 올린 값이다.
#   레퍼런스 그대로 가면 롤의 어둑한 정글이 되고, 오너가 원한 건 SAO 계열의
#   밝고 깨끗한 판타지다. 명암 **구조**는 레퍼런스를 따르고 **평균 밝기**만 올린다.
# ★★화면 목표색(첫 칸)은 **팔레트 계약**이라 함부로 못 옮긴다. 뒤의 세 칸은
#   "그 텍스처를 어떻게 다뤄 그 색에 앉힐 것인가" 라 원자재가 바뀌면 같이 바뀐다.
#   2026-08-11 재생산(11-소품B)에서 crag·bush 의 원자재가 통째로 갈렸다.
#   옛 값을 새 원자재에 그대로 걸면 채도가 2배로 튄다(아래 각 줄의 실측).
TARGET = {
    #                 화면목표    S배수  S더하기   g   [자홍제거]
    # ★11-소품B 재생산. 원자재 S 58.5% (옛 Meshy 원본은 98.2%) 라 옛 배수 1.34 를
    #   그대로 걸면 결과가 63.6% 다(45% 밴드를 한참 넘는다). 0.62 로 내려 34.4% —
    #   교체 전 출고본(33.4%)과 같은 자리다. g 도 1.22 -> 0.90: 새 잎뭉치 텍스처는
    #   이미 명암 폭이 넓어서(span 147) 더 벌리면 잎 사이가 검은 구멍이 된다.
    "bush":        (0x47613a,   0.62,  0.00,  0.90),
    "thicket":     (0x2b3d24,   1.20,  0.03,  1.16),   # 막는 초목. 제일 어둡다
    # ★11-소품C 재생산(codex 콘셉트 -> Meshy). 원자재 S 60.9%(옛 출고본 44.1%)로
    #   **제일 쨍한 원자재**가 들어왔다. 옛 배수 1.18 을 그대로 걸면 S 46% 에
    #   **자홍이 11.56%** 뜬다(어두운 나무껍질이 R·B 우세로 뒤집힌다 — ③ 평균맞추기가
    #   만드는 그 얼룩이다). 0.90 + 자홍제거 0.85 로 S 37.9% · 자홍 0.00%.
    #   g 는 1.18 -> 1.14: 새 잎 텍스처가 이미 명암을 그려 갖고 있다(span 57.3).
    #   ★조명배수 0.87 — crag(1.68)와 **반대 방향**이다. 새 캐노피가 잎뭉치끼리
    #     서로 가려서(가림칠까지 얹히면) 화면 평균이 목표보다 13% 어둡게 나왔다.
    #     실측: 잎 화소만 골라 재면 교체 전 #386c36(휘도 93.1, 목표비 1.01) ->
    #     교체 후 #3f592c(80.0, 0.87). ★나무는 **잎 화소만** 재야 한다 — 새 줄기가
    #     굵어서 마스크 전체로 재면 껍질의 어두움이 섞인다(전체로 재면 0.85).
    #     ★0.87 -> 0.81 로 한 번 더 내렸다. 아래 껍질 가르기를 켜면서 잎 텍스처 평균이
    #       5.5% 내려갔기 때문이다(가르기 전에는 잎이 전체 평균보다 밝은 쪽이었다).
    #       손잡이 하나를 고치면 다른 손잡이의 실측이 낡는다 — 다시 재고 다시 앉혔다.
    #   ★★껍질을 따로 앉힌다(regrade() 의 ⑤). 안 가르면 평균맞추기가 껍질에 B 를
    #     1.8배 곱해 자홍 5.61% -> 자홍을 지우면 **회색**(채도 44% -> 10%)이 된다.
    #     옛 나무의 껍질은 S 48.3% 짜리 갈색이었다(s22 가 마스크로 따로 칠했다).
    #     칠할 값 0x6d4d39 = **교체 전 출고본의 껍질 텍스처 색 그대로**.
    "tree":        (0x4a6535,   0.90,  0.00,  1.14,  0.85,  0.81,  0x6d4d39),   # 나무 잎
    # ★11-소품C 재생산. 새 원자재의 채도가 옛것과 거의 같아서(6.1% vs 9.7%)
    #   **배수는 한 톨도 안 바꿨다.** 결과 S 23.1% = 교체 전 출고본(23.0%)과 같은 자리.
    #   자홍제거만 켰다(0.28% -> 0.00%). "재 보고 정한다"의 반대쪽 예다.
    #   ★★조명배수 1.64 — crag(1.68)와 같은 함정을 **같은 크기로** 밟았다.
    #     새 바위가 각진 판 무더기라 위를 보는 면이 크게 늘었다. 그대로 두면
    #     화면 #879493(휘도 145.4)로 목표(115.2)보다 **+26%** — 못 가는 바위가
    #     맵에서 제일 창백한 물건이 된다(색 규칙 정면 위반). 1.64 로 되돌린다.
    "rock":        (0x66767e,   1.55,  0.06,  1.26,  0.85,  1.64),   # 바위. 채도를 올려 채도밴드를 좁힌다
    # ★11-소품B 재생산. 옛 crag 텍스처는 붓밀도가 0 에 가까운 크림색 판이라
    #   채도를 1.50배로 밀어 올려야 했다. 새 원자재는 결이 살아 있고(p50r5 3.0 -> 17.9)
    #   따뜻한 회록색이라, 1.50 을 걸면 **어두운 틈이 자홍으로 뜬다**(실측 6.65%,
    #   s28 이 bank 에서 겪은 그 함정이다). 0.90 에서 0.14% = 다른 돌들과 같은 자리.
    # ★조명배수 1.68 — 이번 판에서 제일 크게 물린 함정이다. 새 메시가 **각진 판**으로
    #   갈라져 있어서 위를 보는 면이 크게 늘었다. 같은 화면 크롭에서 crag 화소 평균이
    #   교체 전 #56686a(휘도 100.3) -> 교체 후 #778589(휘도 130.5) = **+30%** 로 떴다.
    #   (s28 이 boulder_xl 에서 겪은 것과 같은 일이다: "덩어리가 각진 판으로 갈라져 있어서
    #    위를 보는 면이 훨씬 많다" -> gain 0.82). 안 고치면 못 가는 바위가 제일 창백한
    #   물건이 되고, v89 가 없앤 "같은 돌인데 두 재질 언어"가 그대로 돌아온다.
    "crag":        (0x556571,   0.90,  0.02,  1.20,  0.00,  1.68),
    "outcrop":     (0x5b6b77,   1.50,  0.05,  1.24),
    # ★11-소품C 재생산. rock 과 같은 이유로 배수는 그대로 두고 자홍제거만 켰다
    #   (0.83% -> 0.00%). 결과 S 23.2% 로 rock(23.1%)과 **같은 자리에 앉는다** —
    #   교체 전 출고본은 38.7% 였고 자홍이 3.30% 나 있었다(같은 돌인데 색이 갈렸다).
    #   ★조명배수 0.69 — **rock 과 반대다.** 같은 돌인데 이쪽은 매끈한 돔이라
    #     보이는 면의 대부분이 빛을 비껴 받는다. 화면 #455155(휘도 79.4)로
    #     목표(103.0)보다 -23% = 풀밭 위의 검은 덩어리로 읽혔다.
    #     ★"새 메시 = 무조건 어둡게"가 아니다. 종류마다 재서 부호까지 확인할 것.
    "boulder_xl":  (0x5a6a70,   1.52,  0.06,  1.26,  0.85,  0.69),
    "cliff_tall":  (0x56646f,   1.50,  0.05,  1.30),   # 지층 결이 보여야 한다 -> g 크게
    # ★11-소품B 변주 추가. cliff_tall 과 **같은 화면 목표색**을 쓴다(한 줄에 섞여 서므로
    #   색이 갈리면 변주가 아니라 다른 돌이 된다). 원자재가 어둡고(휘도 57) 채도가
    #   높아서(45%) 배수는 반대로 내린다. 자홍제거 0.85 를 켠 이유는 아래 ★자홍.
    "cliff_tall_b": (0x56646f,  0.66,  0.00,  0.80,  0.85),
    "bank":        (0x64726f,   1.42,  0.06,  1.08),   # 강둑 돌. ★v96 2차: g 1.24 는
    #   하이라이트를 흰 플라스틱으로 만들었다(실측 밝은 면 V 59.7%). 폭을 눅였다
    "slab":        (0x7b8071,   1.55,  0.06,  1.20),   # 판석 패드. 밟는 바닥이라 덜 내린다
}


def glb_read(path):
    d = open(path, "rb").read()
    assert d[:4] == b"glTF", path
    ver, total = struct.unpack_from("<II", d, 4)
    off, js, bin_ = 12, None, b""
    while off < len(d):
        ln, ty = struct.unpack_from("<II", d, off)
        ch = d[off + 8: off + 8 + ln]
        if ty == 0x4E4F534A:
            js = json.loads(ch.decode("utf-8"))
        elif ty == 0x004E4942:
            bin_ = ch
        off += 8 + ln
    return js, bytearray(bin_)


def glb_write(path, js, bin_):
    jb = json.dumps(js, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    jb += b" " * ((4 - len(jb) % 4) % 4)
    bb = bytes(bin_)
    bb += b"\0" * ((4 - len(bb) % 4) % 4)
    total = 12 + 8 + len(jb) + 8 + len(bb)
    out = bytearray()
    out += b"glTF" + struct.pack("<II", 2, total)
    out += struct.pack("<II", len(jb), 0x4E4F534A) + jb
    out += struct.pack("<II", len(bb), 0x004E4942) + bb
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(out)
    os.replace(tmp, path)          # ★원자적 교체. 다른 에이전트가 동시에 읽는다


def pos_hash(js, bin_):
    """POSITION 접근자들의 바이트 해시. 지오메트리가 안 변했음을 증명한다."""
    h = hashlib.md5()
    for m in js.get("meshes", []):
        for p in m.get("primitives", []):
            ai = p.get("attributes", {}).get("POSITION")
            if ai is None:
                continue
            acc = js["accessors"][ai]
            bv = js["bufferViews"][acc["bufferView"]]
            o = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            h.update(bytes(bin_[o:o + bv["byteLength"]]))
    return h.hexdigest()[:12]


def rgb_to_hsv_np(a):
    mx = a.max(2)
    mn = a.min(2)
    d = mx - mn
    v = mx
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    h = np.zeros_like(mx)
    m = d > 1e-6
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    hr = np.where((mx == r) & m, ((g - b) / np.maximum(d, 1e-6)) % 6, 0)
    hg = np.where((mx == g) & m, (b - r) / np.maximum(d, 1e-6) + 2, 0)
    hb = np.where((mx == b) & m, (r - g) / np.maximum(d, 1e-6) + 4, 0)
    h = (hr + hg + hb) / 6.0
    return h, s, v


def hsv_to_rgb_np(h, s, v):
    i = np.floor(h * 6.0)
    f = h * 6.0 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i = (i % 6).astype(np.int32)
    out = np.zeros(h.shape + (3,), np.float32)
    for k, (rr, gg, bb) in enumerate(((v, t, p), (q, v, p), (p, v, t),
                                      (p, q, v), (t, p, v), (v, p, q))):
        m = i == k
        out[m] = np.stack([rr, gg, bb], -1)[m]
    return out


def regrade(img, spec):
    """세 단. ★순서가 중요하다.

      ① 명암 폭 넓히기  V' = Vm * (V/Vm)**g     (평균은 안 움직이고 폭만 넓어진다)
      ② 채도 올리기     S' = S*smul + sadd
      ③ **평균 맞추기** 채널마다 배수를 걸어 평균 RGB 를 목표에 정확히 앉힌다

    ★③ 이 마지막이어야 한다. ①② 가 평균을 밀기 때문이다. 처음에는 ① 에서
      목표 V 로 바로 갔는데, ② 가 채도를 올리면서 평균이 다시 어긋나 바위가
      목표(#6c7a7c)보다 한참 어둡고 푸르게(#4c6375) 나왔다.

    ★자홍(④, 2026-08-11 11-소품B) — **③ 이 만들어 내는** 얼룩이다
      ③ 의 채널 배수는 "따뜻한 원자재를 차가운 목표에 앉히는" 일이라 B 를 크게 곱한다.
      원자재에 적갈색 얼룩이 있으면 그 화소만 R·B 가 G 를 넘어 **자홍**으로 뜬다
      (cliff_var 원자재 0.01% -> 그레이드 후 2.46%, 휘도 92 = 한복판이라 눈에 띈다).
      s28_terrain.py 가 bank 에서 겪은 함정과 같은 것인데, 거기는 원자재에 있던
      얼룩이었고 여기는 **우리가 만든 것**이다. 그래서 지우는 자리도 ③ 뒤다.
      G 를 R·B 평균 쪽으로 끌어올려 자홍기만 뺀다(명도는 안 건드린다). 그리고
      ③ 을 한 번 더 돌려 평균을 목표에 다시 앉힌다(G 를 올린 만큼 평균이 밀리므로).

    ★★잎/껍질 가르기(⑤, 2026-08-11 11-소품C) — **③ 은 두 재료를 못 다룬다**
      한 텍스처 안에 초록 잎과 갈색 껍질이 같이 있으면, 평균 하나를 초록 목표에
      앉히는 순간 껍질에는 B 를 1.8배 곱하게 된다. 그러면 껍질이 자홍으로 뜨고
      (실측 5.61%), 자홍을 지우면 이번엔 **회색이 된다**(껍질 채도 44% -> 10%).
      새 나무 원자재에서 실제로 벌어진 일이다. 옛 나무가 안 그랬던 이유는
      s22_props.py 가 마스크로 **잎과 껍질을 따로 칠했기** 때문이다(껍질 S 48.3%).
      -> 목표표에 `bark`(칠할 값)를 적으면 **초록 우세 화소 = 잎 / 나머지 = 껍질**로
         갈라 각각 따로 평균을 앉힌다. 마스크는 반드시 **원자재**에서 잡는다
         (칠한 뒤에 잡으면 이미 색이 밀려 있어서 잎이 껍질로 넘어간다).
    """
    tgt_hex, smul, sadd, g = spec[:4]
    purple = spec[4] if len(spec) > 4 else 0.0
    lit = spec[5] if len(spec) > 5 else 1.0
    bark_hex = spec[6] if len(spec) > 6 else None
    tgt = np.array([(tgt_hex >> 16) & 255, (tgt_hex >> 8) & 255, tgt_hex & 255],
                   np.float64) / 255.0
    # ★화면 목표 -> 칠할 값. lit 은 **그 소품이 실제로 받는 빛의 배수**다(아래 ★조명보정)
    paint, _ = CC.screen_to_paint(tgt, CC.IRRADIANCE * lit)
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    # ⑤ 잎/껍질 마스크는 **원자재**에서 잡는다(위 ★★)
    leaf = (a[:, :, 1] > a[:, :, 0]) & (a[:, :, 1] > a[:, :, 2]) if bark_hex else None
    h, s, v = rgb_to_hsv_np(a)
    vm = float(v.mean())
    v2 = np.clip(vm * (np.maximum(v, 1e-4) / max(vm, 1e-4)) ** g, 0.0, 1.0)
    s2 = np.clip(s * smul + sadd, 0.0, 1.0)
    out = hsv_to_rgb_np(h, s2, v2)

    # ③ 채널 배수로 평균을 목표에 앉힌다. ★두 번 돌린다 — 자르기(clip)가 평균을
    #   조금 되민다. 두 번이면 0.5/255 안으로 들어온다(실측).
    def fit_part(o, m, target, n=2):
        for _ in range(n):
            mean = o[m].mean(0)
            gain = np.clip(np.asarray(target, np.float32) / np.maximum(mean, 1e-4), 0.2, 5.0)
            o[m] = np.clip(o[m] * gain[None, :], 0.0, 1.0)
        return o

    def fit(o, n=2):
        if leaf is None:
            for _ in range(n):
                m = o.reshape(-1, 3).mean(0)
                gain = np.clip(np.asarray(paint, np.float32) / np.maximum(m, 1e-4), 0.2, 5.0)
                o = np.clip(o * gain[None, None, :], 0.0, 1.0)
            return o
        bark = np.array([(bark_hex >> 16) & 255, (bark_hex >> 8) & 255, bark_hex & 255],
                        np.float32) / 255.0
        o = fit_part(o, leaf, paint, n)
        o = fit_part(o, ~leaf, bark, n)
        return o

    out = fit(out)
    if purple:
        r, gg, b = out[:, :, 0], out[:, :, 1], out[:, :, 2]
        low = np.minimum(r, b)                     # R·B 중 작은 쪽이 G 보다 높으면 자홍
        w = np.clip((low - gg) / 0.03, 0.0, 1.0) * purple
        n0 = float(((low - gg) > 0.012).mean())
        out[:, :, 1] = gg + w * ((r + b) * 0.5 - gg)
        out = fit(out, 1)                          # 평균을 다시 목표에 앉힌다
        r, gg, b = out[:, :, 0], out[:, :, 1], out[:, :, 2]
        print("   자홍 %.2f%% -> %.2f%% (세기 %.2f)"
              % (n0 * 100, float(((np.minimum(r, b) - gg) > 0.012).mean()) * 100, purple))
    clipped = float((out >= 0.999).any(2).mean())
    if clipped > 0.02:
        print("   ※ 흰색으로 잘린 화소 %.1f%% — 목표가 너무 밝거나 g 가 크다" % (clipped * 100))
    return Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255 + 0.5)), paint


# ★12-소품원색(2026-08-11)에서 tools/raw_props.py 로 넘어간 종류. 여기서 칠하면
#   오너가 고른 Meshy 원색이 팔레트로 도로 덮인다. --force 없이는 손대지 않는다.
# ★★2차(같은 날)에서 **남은 다섯 종까지 전부** 넘어갔다. 그래서 이 표는 이제
#   TARGET 의 열한 종과 같다 = 이 파일은 사실상 **읽기 전용 기록**이다.
#   위의 TARGET 표는 지우지 않는다 — "그때 무엇을 어떻게 칠했는가"가 남아 있어야
#   원색판이 무엇을 걷어낸 것인지 다음 사람이 읽을 수 있다(그 근거가 LOG 12차다).
MOVED_TO_RAW = {"tree", "rock", "boulder_xl", "crag", "bush", "cliff_tall_b",
                "cliff_tall", "outcrop", "bank", "slab", "thicket"}


def main(argv):
    dry = "--dry" in argv
    force = "--force" in argv
    names = [a for a in argv if not a.startswith("-")]
    files = sorted(f for f in os.listdir(PROPS) if f.endswith(".glb"))
    for f in files:
        key = f[:-4]
        if key not in TARGET:
            continue
        if names and key not in names:
            continue
        if key in MOVED_TO_RAW and not force:
            print("%-14s 건너뜀 — tools/raw_props.py 소유다(12-소품원색). 정말이면 --force" % key)
            continue
        path = os.path.join(PROPS, f)
        js, bin_ = glb_read(path)
        h0 = pos_hash(js, bin_)
        if not js.get("images"):
            print("%-14s 텍스처 없음 — 건너뜀" % key)
            continue
        im0 = js["images"][0]
        bv = js["bufferViews"][im0["bufferView"]]
        o = bv.get("byteOffset", 0)
        src = bytes(bin_[o:o + bv["byteLength"]])
        img = Image.open(io.BytesIO(src))
        before = np.asarray(img.convert("RGB"), np.float32).reshape(-1, 3).mean(0) / 255
        new, paint = regrade(img, TARGET[key])
        after = np.asarray(new, np.float32).reshape(-1, 3).mean(0) / 255
        buf = io.BytesIO()
        # ★원본이 jpeg 이면 jpeg 로 다시 굽는다(png 로 바꾸면 파일이 4배가 된다).
        if (im0.get("mimeType") or "").endswith("jpeg"):
            new.save(buf, "JPEG", quality=90, subsampling=0)
        else:
            new.save(buf, "PNG", optimize=True)
        data = buf.getvalue()
        # ★조명배수를 넣어 예측해야 참말이 된다(1.0 이면 예전과 같은 계산이다)
        _lit = TARGET[key][5] if len(TARGET[key]) > 5 else 1.0
        s_before = CC.paint_to_screen(before, CC.IRRADIANCE * _lit)
        s_after = CC.paint_to_screen(after, CC.IRRADIANCE * _lit)
        print("%-14s 텍스처 %s -> %s   화면 %s -> %s   (%d KB -> %d KB)"
              % (key, CC.hexs(before), CC.hexs(after), CC.hexs(s_before),
                 CC.hexs(s_after), len(src) // 1024, len(data) // 1024))
        if dry:
            continue
        # ── bufferView 를 갈아 끼운다. 뒤 것들의 오프셋을 밀어야 한다 ──
        old_len = bv["byteLength"]
        pad = (4 - len(data) % 4) % 4
        new_len = len(data) + pad
        old_pad = (4 - old_len % 4) % 4
        delta = new_len - (old_len + old_pad)
        head = bytes(bin_[:o])
        tail = bytes(bin_[o + old_len + old_pad:])
        bin2 = bytearray(head + data + b"\0" * pad + tail)
        bv["byteLength"] = len(data)
        for other in js["bufferViews"]:
            if other is bv:
                continue
            if other.get("byteOffset", 0) > o:
                other["byteOffset"] = other.get("byteOffset", 0) + delta
        js["buffers"][0]["byteLength"] = len(bin2)
        h1 = pos_hash(js, bin2)
        if h0 != h1:
            print("   ★POSITION 해시가 바뀌었다(%s -> %s). 안 쓴다." % (h0, h1))
            continue
        glb_write(path, js, bin2)
        print("   저장 (POSITION 해시 %s 그대로 · %d KB)" % (h1, os.path.getsize(path) // 1024))


if __name__ == "__main__":
    main(sys.argv[1:])
