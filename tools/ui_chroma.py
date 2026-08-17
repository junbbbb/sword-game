#!/usr/bin/env python3
# 크로마키(초록) 제거 + 디스필. codex ImageGen 이 뱉은 오나먼트를 투명 PNG 로 만든다.
#
# 왜 단순 "초록이면 지운다"가 아닌가: 봉의 가장자리는 배경과 섞인 반투명 화소다.
# 그걸 통째로 지우면 테두리가 톱니가 되고, 남기면 초록 테가 두른다. 그래서
#   ① 초록 정도(spill = G - max(R,B))로 **알파를 연속값으로** 만들고
#   ② 남은 화소의 G 를 max(R,B) 수준으로 눌러 초록 물을 뺀다(디스필).
#
#   python3 tools/ui_chroma.py in.png out.png [--size 1024] [--tight]
import sys
import numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
size = 1024
if '--size' in sys.argv:
    size = int(sys.argv[sys.argv.index('--size') + 1])

im = Image.open(src).convert('RGB')
a = np.asarray(im).astype(np.float32)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
m = np.maximum(R, B)
spill = G - m                      # 초록일수록 크다. 청동 화소는 0 이하

# 알파: spill 이 LO 밑이면 완전 불투명, HI 위면 완전 투명. 사이는 선형.
LO, HI = 10.0, 70.0
alpha = 1.0 - (spill - LO) / (HI - LO)
alpha = np.clip(alpha, 0.0, 1.0)

# 디스필: 남은 화소에서 G 를 max(R,B) 로 눌러 초록 테를 없앤다.
G2 = np.minimum(G, m)
out = np.stack([R, G2, B], axis=-1)

# 반투명 가장자리는 배경 초록이 섞여 어두워져 있다. 알파로 나눠(언프리멀티플라이)
# 색을 되살린다 - 안 하면 테두리에 검은 띠가 생긴다.
safe = np.maximum(alpha, 0.15)[..., None]
bgmix = np.array([0.0, 255.0, 0.0], dtype=np.float32)
out = (out - bgmix * (1.0 - alpha)[..., None]) / safe
out = np.clip(out, 0, 255)

rgba = np.concatenate([out, (alpha * 255)[..., None]], axis=-1).astype(np.uint8)
img = Image.fromarray(rgba, 'RGBA')

# 알파가 아주 낮은 티끌 제거
arr = np.asarray(img).copy()
arr[..., 3] = np.where(arr[..., 3] < 8, 0, arr[..., 3])
img = Image.fromarray(arr, 'RGBA')

if img.size != (size, size):
    img = img.resize((size, size), Image.LANCZOS)
img.save(dst)
al = np.asarray(img)[..., 3]
print('wrote', dst, img.size, 'alpha0%%=%.1f' % (100.0 * (al == 0).mean()),
      'alpha255%%=%.1f' % (100.0 * (al == 255).mean()))
