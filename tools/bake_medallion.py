# -*- coding: utf-8 -*-
"""메달리온 데칼 굽기 — codex 원자재 한 덩이를 **월드 고정 1장짜리 데칼**로.

왜 이게 있나 (11차 파도, 2026-08-11)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
오너: **"바닥 좀 바꿔줘. 지금 너무 패턴 느낌이라 별로야, 화장실 타일 같잖아."**
자로 재 보니 신고의 정체는 자기상관이 아니었다(이미 0.118 로 규격 안이었다).

  · 레퍼런스 잔디 p50_range5 5.7~10.7  ↔  우리 25~27  = **면이 3.5배 시끄럽다**
  · 그리고 v96-B tile_grass 는 에너지의 66% 가 10~25cm 한 대역에 몰려 있었다.
    크기가 하나뿐인 밝은 C 자 붓자국이 2.1m 마다 돌아오니 사람 눈이 바로 잡아낸다.

★그래서 **텍스처 교체만으로는 안 풀린다. 배치 문법이 바뀌어야 한다.**
  레퍼런스(refpack/lol_ground_owner_ref2.png)의 문법은 셋이다.
    ① 조용한 잔디 바탕   ② 큰 **비반복** 문양 덩어리가 명소에 하나씩   ③ 유기적 경계
  ①은 tools/tileize.py 가, ②③이 이 파일이 굽는 데칼이다.

무엇을 굽나
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`web/tex/ground_medallion.png` — 2048x1024 RGBA **아틀라스 두 칸**.

    칸 0 : 온전한 메달리온(동심 깨진 석판)      — 명소 한복판에 놓는다
    칸 1 : 부서진 조각 고리(가운데를 비웠다)     — 광장 가장자리·판석 구역 희석용

★칸을 둘로 가르는 이유. 같은 그림을 회전만 해서 여섯 군데 놓으면 그게 다시
  "되풀이"다. 조각 고리는 중심 문양이 없어서 옆에 놓여도 같은 그림으로 안 읽힌다.
★한 장짜리 아틀라스인 이유는 셰이더 조회를 **한 번**으로 묶기 위해서다
  (web/level.js 의 uMed 주석 참조).

세 가지 함정을 여기서 처리한다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
★① **덮개를 원형으로 자르면 스티커가 된다.** 원자재의 잔디 배경째로 둥글게
   페이드하면 화면에서 "잔디 위에 놓인 둥근 접시"로 보인다. 레퍼런스는 그 반대다 —
   **풀이 석판을 삼키고 있다.** 그래서 덮개를 **돌다움(greenness)** 에서 뽑는다.
   경계가 저절로 깨진 석판의 실루엣을 따라가고, 조각 사이에는 우리 잔디가 그대로 뚫고 올라온다.
★② **틈까지 뚫으면 안 된다.** 석판 사이 이끼 낀 틈에 우리 밝은 잔디가 올라오면
   줄눈이 형광 연두가 된다. 그래서 돌 마스크를 한 번 **닫아(close)** 안쪽 틈을 메우고,
   그 안에서는 원자재가 그린 어두운 이끼를 그대로 쓴다. 삼켜지는 것은 **바깥 가장자리**뿐이다.
★③ **투명한 자리의 색이 밉맵으로 끌려온다.** 알파 0 인 잔디 배경색이 그대로 남아
   있으면 멀어질 때 데칼 가장자리에 초록 테가 돈다. 알파 가중 push-pull 로
   **돌색을 바깥으로 밀어** 채운다(solidify).

색계약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
★이 겹만은 곱수가 아니라 **색**이다(산포 겹과 같은 계약). 그래서 칠한 색이
  화면에 그대로 안 나온다 — ACES 를 지나야 한다.
    화면 목표 #7c8171  ->  칠할 #717568   (`python3 tools/color_contract.py to 7c8171`)
  이 값은 우리 판석의 화면 실측(보스마당 lum 127.5)과 같은 자리다. 즉 메달리온은
  "이 세계에 원래 있던 돌"로 읽힌다. ★codex 원자재는 훨씬 어둡다(평균 V 27%).
  그대로 넣으면 화면에서 검은 구멍이 된다 — 반드시 여기서 역산해 옮긴다.

쓰는 법
    python3 tools/bake_medallion.py            # 굽는다
    python3 tools/bake_medallion.py sheet      # 눈 확인용 시트만 다시
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "incoming", "codex_ground", "medallion.png")
OUT = os.path.join(ROOT, "web", "tex", "ground_medallion.png")
SHEET_DIR = os.path.join(ROOT, "renders", "history", "v97_wave11", "ground", "bake")

CELL = 1024                    # 칸 한 변(px). 지름 7m 데칼이면 146 px/m = 화면 150 과 같다

# ── 덮개(알파) 손잡이 ──────────────────────────────────────────
# greenness = G - (R+B)/2. 원자재 실측: 잔디 0.110~0.133 · 석판 0.018~0.047.
# 사이가 텅 비어 있어서 문턱 하나로 깨끗하게 갈린다.
GREEN_STONE = 0.055            # 이 아래는 확실히 돌
GREEN_GRASS = 0.098            # 이 위는 확실히 잔디
CLOSE_R = 30                   # 틈 메우기 반경(px, 2048 기준). 2*R 보다 좁은 틈이 메워진다
EDGE_SOFT = 13                 # 가장자리 페이드 폭(px). 좁아야 "삼켜진" 것으로 읽힌다
SMOOTH_R = 9                   # 닫기가 남긴 사각 계단을 지우는 반경(px)
RIM0, RIM1 = 0.455, 0.498      # 안전망 원형 페이드(칸 반지름 대비). 아틀라스 여백을 보장한다

# ── 색 손잡이 ──────────────────────────────────────────────────
PAINT = (0x71, 0x75, 0x68)     # 칠할 색(= 화면 #7c8171). 위 색계약 절 참조
HUE_KEEP = 0.55                # 색편차를 얼마나 남길지. 1 이면 원자재 색이 그대로
CTR = 1.00                     # 명암 재분배(>1 이면 어두운 쪽이 깊어진다)
SPAN = 1.00                    # 대비 배수. 1 = 원자재 그대로

# 칸 1(조각 고리)에서 파낼 중심 구멍(칸 반지름 대비)
HOLE0, HOLE1 = 0.17, 0.245


# ─────────────────────────────────────────────────────────────────────────────
def _disc_kernel_max(a, r):
    """반경 r 원판 최대값 필터(팽창). 분리 가능한 사각 두 번으로 어림한다."""
    from scipy import ndimage                                    # noqa
    return ndimage.maximum_filter(a, size=2 * r + 1)


def _box(a, r):
    """감아 돌지 않는 박스 블러(데칼은 이어붙지 않는다)."""
    if r < 1:
        return a.astype(np.float32)
    out = a.astype(np.float32)
    for ax in (0, 1):
        c = np.cumsum(np.pad(out, [(r + 1, r) if i == ax else (0, 0)
                                   for i in range(out.ndim)], mode="edge"), axis=ax)
        out = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax)
               - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return out


def _morph(mask, r, grow):
    """★scipy 없이 도는 형태 연산. 박스 블러 + 문턱으로 팽창/침식을 흉내낸다.

    정확한 원판 커널은 아니지만 여기서 필요한 것은 "2R 보다 좁은 틈을 메운다" 뿐이라
    사각 근사로 충분하다. scipy 의존을 안 만드는 게 이 저장소 관례에 맞는다."""
    b = _box(mask.astype(np.float32), r)
    return (b > (1e-4 if grow else 1.0 - 1e-4)).astype(np.float32)


def smoothstep(e0, e1, x):
    """★e0 > e1 (내림차순) 도 써야 한다. 분모를 max(d, eps) 로 가드하면 그 경우
       부호가 뭉개져서 마스크가 통째로 **뒤집힌다**(첫 굽기에서 밟았다:
       돌이 투명해지고 잔디가 불투명해졌고, 덕분에 grade 의 가중평균이 잔디로 잡혀
       돌이 자홍으로 떴다 = s28 연보라 함정의 재현). 크기만 가드한다."""
    d = e1 - e0
    d = d if abs(d) > 1e-9 else 1e-9
    t = np.clip((x - e0) / d, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


SOLID_A = 0.30                 # 이 알파 위의 색만 "믿을 만한 색"으로 본다


def solidify(rgb, a, rounds=9):
    """투명한 자리를 이웃 돌색으로 밀어 채운다(가장자리 색 번짐 방지).

    안 하면 멀어질 때(밉맵) 투명한 자리의 색이 데칼 가장자리로 끌려와 테가 돈다.
    glTF 알파 카드에서 겪은 언프리멀티플라이 함정과 같은 종류다.

    ★★첫 판은 여기서 **흰 테**를 만들었다(게임 화면에서 문양 윤곽을 따라 밝은 선이
      그어졌다. renders/history/v97_wave11/ground/after 1차). 원인은 정확히 이것이다 —
      "프리멀티한 색을 흐려서 무게로 나눠 채운" 뒤 그 결과를 **다시 프리멀티가 아닌
      채로** 다음 회차에 넣었다. 2회차의 나누기가 이미 나눠진 값을 또 나눠서
      색이 2.5배로 불었다(알파 0.02~0.25 띠의 휘도 실측 0.695, p99 = 1.000).
    ★그래서 무게를 **0/1 이진**으로만 둔다. "색이 있는 자리"는 채워지는 순간 1 이
      되고 그 뒤로는 나눗셈에 안 걸린다. 한 번 채운 색은 다시 안 건드린다.
    """
    kn = (a > SOLID_A).astype(np.float32)          # 색이 믿을 만한 자리(0/1)
    col = rgb.astype(np.float32) * kn[:, :, None]
    for r in (1, 2, 4, 8, 16, 32, 64, 128, 256)[:rounds]:
        bw = _box(kn, r)
        bc = np.stack([_box(col[:, :, i], r) for i in range(3)], -1)
        fill = bc / np.maximum(bw, 1e-6)[:, :, None]
        take = (kn < 0.5) & (bw > 1e-4)
        col = np.where(take[:, :, None], fill, col)
        kn = np.where(take, 1.0, kn)
    # 아직도 못 채운 자리(아주 먼 구석)는 전체 돌 평균으로
    m = (a > SOLID_A)
    if m.any():
        col = np.where((kn < 0.5)[:, :, None], rgb[m].mean(0)[None, None, :], col)
    # ★가장자리 띠(알파 0<a<=SOLID_A)의 색은 원자재 것을 안 쓴다. 거기는 원자재가
    #   "돌 x 덮개 + 잔디 x (1-덮개)" 로 이미 합성해 놓은 값이라, 우리 잔디 위에
    #   다시 얹으면 남의 잔디가 한 겹 낀다. 채운 돌색이 맞다.
    return np.clip(col, 0.0, 1.0)


def grade(rgb, w):
    """돌 화소의 평균을 PAINT 로 못 박고, 색편차는 HUE_KEEP 배만 남긴다.

    ★tileize._fit_ratio 와 **같은 식**이다. 다른 점은 통계를 덮개로 가중한다는 것뿐
      (투명한 잔디 배경이 평균에 끼면 목표색이 통째로 밀린다 — 갈대 카드에서 겪은 함정).
    """
    a = rgb.astype(np.float32)
    ww = w[:, :, None].astype(np.float32)
    sw = max(float(ww.sum()), 1e-6)
    m = (a * ww).reshape(-1, 3).sum(0) / sw
    d = a / np.maximum(m, 1e-4)[None, None, :] - 1.0
    db = d.mean(axis=2, keepdims=True)
    # 명암 재분배: 휘도 쪽에만 감마를 건다(색에 걸면 채도가 흔들린다)
    if abs(CTR - 1.0) > 1e-6:
        s = np.sign(db)
        db = s * (np.abs(db) ** CTR)
    d = (db + (d - db) * HUE_KEEP) * SPAN
    ref = np.asarray(PAINT, np.float32) / 255.0
    out = ref[None, None, :] * (1.0 + d)
    for _ in range(6):                          # 클립 뒤 평균이 밀리므로 되맞춘다
        out = np.clip(out, 0.0, 1.0)
        c = (out * ww).reshape(-1, 3).sum(0) / sw
        out = out * (ref / np.maximum(c, 1e-4))[None, None, :]
    return np.clip(out, 0.0, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
def build():
    raw = np.asarray(Image.open(SRC).convert("RGB"), np.float32) / 255.0
    n = raw.shape[0]
    green = raw[..., 1] - 0.5 * (raw[..., 0] + raw[..., 2])

    # ① 돌다움 -> 덮개. 문턱 사이가 비어 있어서 깨끗하게 갈린다
    stone = smoothstep(GREEN_GRASS, GREEN_STONE, green)          # 1=돌, 0=잔디
    hard = (stone > 0.5)

    # ② 안쪽 틈만 메운다(닫기 = 팽창 뒤 침식). 바깥 조각들은 따로 떨어져 있으므로
    #    닫혀도 서로 안 붙는다 = 조각이 풀에 박힌 그림이 그대로 산다
    closed = _morph(_morph(hard, CLOSE_R, True), CLOSE_R, False)
    body = np.maximum(closed, hard.astype(np.float32))

    # ③ 가장자리 페이드. 좁게(EDGE_SOFT) 잡아야 "풀이 삼킨" 접촉선이 된다
    #    ★그 전에 한 번 더 문지른다. _morph 가 사각 커널이라 닫기 자국이 **계단**으로
    #      남는데, 그 계단이 그대로 데칼 윤곽이 되면 손그림이 아니라 도트가 된다.
    body = (_box(body, SMOOTH_R) > 0.5).astype(np.float32)
    alpha = np.clip(_box(body, EDGE_SOFT) * 1.35 - 0.175, 0.0, 1.0)

    # ④ 안전망 원형 페이드 — 아틀라스 칸 경계에 알파가 남으면 밉에서 옆 칸이 샌다
    yy = (np.arange(n)[:, None] - (n - 1) / 2) / n
    xx = (np.arange(n)[None, :] - (n - 1) / 2) / n
    rad = np.sqrt(yy * yy + xx * xx)
    alpha = alpha * (1.0 - smoothstep(RIM0, RIM1, rad))

    # ⑤ 색. 돌 화소만으로 평균을 내서 PAINT 로 옮긴다
    graded = grade(raw, alpha * (stone * 0.75 + 0.25))
    rgb = solidify(graded, alpha)

    # ── 칸 0: 온전한 메달리온 ──
    a0 = alpha
    c0 = rgb
    # ── 칸 1: 부서진 조각 고리 (중심 문양을 파낸다) ──
    a1 = alpha * smoothstep(HOLE0, HOLE1, rad)
    c1 = rgb
    # 90도 돌려 둔다. 같은 그림으로 안 읽히게 하는 제일 싼 방법이다
    a1 = np.rot90(a1)
    c1 = np.rot90(c1)

    def cell(c, a):
        """★★Pillow 의 RGBA `resize` 는 **알파를 프리멀티해서 줄인다.** 알파 0 인
           자리의 RGB 가 통째로 0 이 된다 — 바로 위 solidify 가 채워 넣은 돌색이
           저장 직전에 지워진다(첫 판에서 밟았다. 실측: 투명 자리 RGB 0.002).
           RGB 와 알파를 **따로** 줄여서 다시 합쳐야 한다."""
        c8 = (np.clip(c, 0, 1) * 255.0 + 0.5).astype(np.uint8)
        a8 = (np.clip(a, 0, 1) * 255.0 + 0.5).astype(np.uint8)
        rgb = Image.fromarray(c8).resize((CELL, CELL), Image.LANCZOS)
        alp = Image.fromarray(a8).resize((CELL, CELL), Image.LANCZOS)
        return np.concatenate([np.asarray(rgb), np.asarray(alp)[:, :, None]], axis=2)

    atlas = np.concatenate([cell(c0, a0), cell(c1, a1)], axis=1)
    atlas = Image.fromarray(atlas)
    atlas.save(OUT)

    # ── 계약 검사 ──
    aa = np.asarray(atlas, np.float32) / 255.0
    for i, nm in ((0, "칸0 온전"), (1, "칸1 조각고리")):
        c = aa[:, i * CELL:(i + 1) * CELL, :3]
        al = aa[:, i * CELL:(i + 1) * CELL, 3]
        w = al.sum()
        mean = (c * al[:, :, None]).reshape(-1, 3).sum(0) / max(w, 1e-6)
        print("%s  덮개 %.1f%%  덮개가중 평균 #%02x%02x%02x  (목표 칠할색 #%02x%02x%02x)"
              % (nm, al.mean() * 100, *(mean * 255 + 0.5).astype(int), *PAINT))
        print("      가장자리 알파 최대 %.4f (0 이어야 아틀라스가 안 샌다)"
              % max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max()))
    print("저장: %s  (%.0f KB)" % (OUT, os.path.getsize(OUT) / 1024))
    make_sheet(atlas)


def make_sheet(atlas=None):
    """눈 확인용 — 잔디 위에 얹은 모습 + 알파."""
    os.makedirs(SHEET_DIR, exist_ok=True)
    if atlas is None:
        atlas = Image.open(OUT).convert("RGBA")
    aa = np.asarray(atlas, np.float32) / 255.0
    # 새 잔디 타일을 게임 거리로 깐 바탕
    g = np.asarray(Image.open(os.path.join(ROOT, "web", "tex", "tile_grass.png"))
                   .convert("RGB"), np.float32) / 255.0
    gm = g.reshape(-1, 3).mean(0)
    base = np.asarray([0x8e, 0xa8, 0x55], np.float32) / 255.0
    grass = np.clip(base[None, None, :] * np.clip(1 + (g / gm - 1) * 2.05, 0.24, 2.10), 0, 1)
    grass = np.asarray(Image.fromarray((grass * 255).astype(np.uint8))
                       .resize((CELL, CELL), Image.LANCZOS), np.float32) / 255.0
    rows = []
    for i in range(2):
        c = aa[:, i * CELL:(i + 1) * CELL, :3]
        al = aa[:, i * CELL:(i + 1) * CELL, 3:4]
        over = grass * (1 - al) + c * al
        rows.append(np.concatenate([over, np.repeat(al, 3, 2)], axis=1))
    sh = (np.concatenate(rows, axis=0) * 255).astype(np.uint8)
    p = os.path.join(SHEET_DIR, "medallion_sheet.jpg")
    Image.fromarray(sh).resize((sh.shape[1] // 2, sh.shape[0] // 2),
                               Image.LANCZOS).save(p, quality=90)
    print("검증 시트:", p)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sheet":
        make_sheet()
    else:
        build()
