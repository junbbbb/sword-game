#!/usr/bin/env python3
# 19차 UI — 청동 당초문(덩굴) 모서리 오나먼트 마감.
#
# 입력은 codex ImageGen 이 그린 초록 배경 봉(rod) 스크롤이고, 여기서 두 가지를 한다.
#   ① 크로마키 제거는 tools/ui_chroma.py 가 이미 했다(투명 PNG).
#   ② 여기서는 **광도로 팔레트를 갈아끼운다**. 생성 이미지는 매번 채도가 튀는데,
#      광도(명암)만 살리고 색은 실측 램프로 강제하면 레퍼런스와 색이 정확히 맞는다.
#
# 실측 램프(레퍼런스 KakaoTalk_Photo_2026-08-14-05-48-26.png 의 테·오나먼트에서 뽑았다):
#   #392E21 #59412B #825A39 #B1794B #D8A274 #E6B78E #FDEFC9
# 레퍼런스 오나먼트의 지배색은 #876349·#68472F 대(채도 ~0.46)라 생성물(0.71)보다
# 훨씬 눅눅하다. 램프 매핑이 그 차이를 자동으로 없앤다.
#
#   python3 tools/bake_ui_vine.py <keyed_rgba.png> <out_dir> [--size 512]
import sys, os
import numpy as np
from PIL import Image

RAMP = [(0x39, 0x2E, 0x21), (0x59, 0x41, 0x2B), (0x82, 0x5A, 0x39),
        (0xB1, 0x79, 0x4B), (0xD8, 0xA2, 0x74), (0xE6, 0xB7, 0x8E),
        (0xFD, 0xEF, 0xC9)]

src = sys.argv[1]
out = sys.argv[2]
size = 512
if '--size' in sys.argv:
    size = int(sys.argv[sys.argv.index('--size') + 1])
# 장식은 레일보다 밝으면 안 된다. 같은 금속으로 읽혀야 하는데 생성물은 마루가
# 늘 더 튄다. 램프를 먹인 뒤 한 번 더 눌러서 레일 마루(#E6B78E) 아래로 내린다.
dim = 0.86
if '--dim' in sys.argv:
    dim = float(sys.argv[sys.argv.index('--dim') + 1])
os.makedirs(out, exist_ok=True)

im = Image.open(src).convert('RGBA')
a = np.asarray(im).astype(np.float32)
rgb, al = a[..., :3], a[..., 3]
ink = al > 8

lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
# 잉크 화소만 보고 정규화한다. 배경(0)을 섞으면 램프가 통째로 밝은 쪽으로 밀린다.
lo = np.percentile(lum[ink], 2)
hi = np.percentile(lum[ink], 98)
t = np.clip((lum - lo) / max(1.0, hi - lo), 0.0, 1.0)

stops = np.array(RAMP, dtype=np.float32)
pos = t * (len(RAMP) - 1)
i0 = np.clip(np.floor(pos).astype(int), 0, len(RAMP) - 2)
u = (pos - i0)[..., None]
graded = (stops[i0] * (1 - u) + stops[i0 + 1] * u) * dim

res = np.concatenate([np.clip(graded, 0, 255), al[..., None]], axis=-1).astype(np.uint8)
img = Image.fromarray(res)

# ── 여백을 잘라 잉크가 모서리에 닿게 한다 ──
# 생성물은 캔버스 안에 떠 있어서 그대로 쓰면 장식이 판 **안쪽**에 얌전히 들어앉는다.
# 레퍼런스의 장식은 레일 위에 걸터앉아 판 밖으로 흘러나간다. CSS 배경은 상자 밖으로
# 못 나가므로, 최소한 **레일에 닿게**는 해야 한다 - 잉크 상자를 좌상단에 붙여 자른다.
ys, xs = np.where(np.asarray(img)[..., 3] > 8)
x0, y0 = int(xs.min()), int(ys.min())
side = max(int(xs.max()) - x0, int(ys.max()) - y0) + 1
side = min(side, img.width - x0, img.height - y0)
img = img.crop((x0, y0, x0 + side, y0 + side))
print('crop to ink  origin(%d,%d) side %d' % (x0, y0, side))

if img.size != (size, size):
    img = img.resize((size, size), Image.LANCZOS)

# WebP 로 낸다. 화면에서 92px 로 쓰는 장식이라 512 PNG(107KB x4)는 과하다.
# 256 이면 deviceScaleFactor 2 에서도(92 -> 184 실화소) 여유가 있다.
KW = dict(format='WEBP', quality=92, method=6)
img.save(os.path.join(out, 'ui_vine_tl.webp'), **KW)
img.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(out, 'ui_vine_tr.webp'), **KW)
img.transpose(Image.FLIP_TOP_BOTTOM).save(os.path.join(out, 'ui_vine_bl.webp'), **KW)
img.transpose(Image.ROTATE_180).save(os.path.join(out, 'ui_vine_br.webp'), **KW)

tot = sum(os.path.getsize(os.path.join(out, 'ui_vine_%s.webp' % k))
          for k in ('tl', 'tr', 'bl', 'br'))
print('graded ->', out, img.size, ' dim', dim, ' 4장 합계 %.1fKB' % (tot / 1024))
