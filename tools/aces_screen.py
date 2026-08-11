# -*- coding: utf-8 -*-
"""화면 색 역산기 — 팔레트 hex 가 **화면에서** 무슨 색·채도·휘도로 앉는지 되돌려 준다.

왜 필요한가 (v99 11-FX-B 에서 이것 때문에 한 판을 통째로 헛짚었다):
  web/main.js 의 셰이더는 팔레트 hex 를 255 로 나눠 **선형 그대로** 색으로 쓰는데,
  renderer 에 ACESFilmicToneMapping 이 걸려 있다. ACES 는 밝은 쪽을 흰색으로 말아
  올리면서 **채도를 통째로 먹는다.** 그래서 "팔레트 채도 0.556" 같은 기록은 화면에
  대한 참말이 아니다(#4884A2 는 화면에서 채도 0.264 로 앉는다).

  원리 한 줄: **같은 화면 휘도에서 채도를 지키려면 빨강을 비우고 초록·파랑으로 밝기를
  들어야 한다.** 화면 휘도의 79%를 G·B 가 지므로, 밝기를 R 이 지면 곧장 흰색이 된다.

  ★THREE.Color(0x...) 는 자가 다르다 — sRGB 로 읽어 선형으로 변환한다(r160 기본).
    셰이더에 직접 넣는 uPal 과 같은 hex 를 적으면 훨씬 어두워진다.

실행:
    python3 tools/aces_screen.py           # 물 팔레트가 화면에서 앉는 자리
    python3 tools/aces_screen.py fit       # 밴드 단면을 모사해 채도 중앙값을 미리 잰다
"""

import numpy as np

EXPO = 1.05

IN = np.array([[0.59719, 0.35458, 0.04823],
               [0.07600, 0.90834, 0.01566],
               [0.02840, 0.13383, 0.83777]])
OUT = np.array([[ 1.60475, -0.53108, -0.07367],
                [-0.10208,  1.10813, -0.00605],
                [-0.00327, -0.07276,  1.07602]])

def rrt_odt(v):
    a = v * (v + 0.0245786) - 0.000090537
    b = v * (0.983729 * v + 0.4329510) + 0.238081
    return a / b

def aces(lin):
    c = np.asarray(lin, dtype=np.float64) * EXPO
    c = c @ IN.T
    c = rrt_odt(c)
    c = c @ OUT.T
    return np.clip(c, 0, 1)

def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1/2.4) - 0.055)

def hex2lin(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)])

def sat(rgb):
    rgb = np.asarray(rgb, dtype=np.float64)
    mx = rgb.max(-1); mn = rgb.min(-1)
    return np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)

def lum(rgb):
    return np.asarray(rgb) @ np.array([0.2126, 0.7152, 0.0722])

def screen(hexstr):
    """팔레트 hex 한 개가 화면(sRGB 8비트)에서 어떤 색·채도·휘도가 되는가."""
    lin = hex2lin(hexstr)
    out = lin2srgb(aces(lin))
    b = np.round(out * 255).astype(int)
    return dict(hex=hexstr, src_sat=float(sat(lin)), rgb=tuple(b.tolist()),
                out_sat=float(sat(out)), out_lum=float(lum(out) * 255),
                out_hex='%02X%02X%02X' % tuple(b.tolist()))

# 밴드 단면을 셰이더와 같은 순서로 모사해 **화면(ACES+sRGB) 채도 중앙값·휘도**를 미리 잰다.
# 손잡이를 돌리기 전에 여기서 먼저 맞춰 두면 촬영을 두 번 덜 한다.
import numpy as np


BG = 156.0   # 밝은 모래 배경 휘도 실측(metrics_table lumBg 평균)

def profile(pal, ws_head=0.82, ws_tail=0.96, cuts=(0.38, 0.62, 0.74),
            ow=0.16, rw=0.24, tail_mix=0.40, tail_dim=0.10, tex=1.0):
    """한 획의 화소를 밴드 비율대로 뽑아 화면 색을 만든다.
       머리(u=0)와 꼬리(u=1) 구간을 면적비로 섞는다(수명 11칸이라 꼬리가 더 넓다)."""
    P = {k: hex2lin(v) for k, v in pal.items()}
    px = []
    # u 를 0..1 로 훑는다. 꼬리로 갈수록 폭이 얇아지므로 면적 가중을 pow(1-u,1.3) 로 준다.
    for u in np.linspace(0.02, 0.98, 49):
        wgt = max(0.08, (1 - u) ** 1.30)
        ws = ws_head + (ws_tail - ws_head) * min(1.0, u * 1.3)
        ls = min(1.0, np.floor(u * 5.0) / 4.0)
        for bt in np.linspace(0.005, 0.995, 200):
            dN = 1.0 - abs(bt - 0.5) * 2.0
            if bt < cuts[0]:   c = P['DK1']
            elif bt < cuts[1]: c = P['MID']
            elif bt < cuts[2]: c = P['LT1']
            elif bt < ws:      c = P['LT3']
            else:              c = P['WHT']
            c = np.array(c, dtype=np.float64)
            if dN < ow:   c = P['DK2'] * 0.42
            elif dN < rw: c = np.array(P['LT3'], dtype=np.float64)
            else:         c = c * tex
            c = c * (1 - tail_mix * ls) + P['DK1'] * (tail_mix * ls)
            c = c * (1 - tail_dim * ls)
            px.append((c, wgt))
    lin = np.array([p[0] for p in px]); w = np.array([p[1] for p in px])
    out = lin2srgb(aces(lin))
    S = sat(out); L = lum(out) * 255
    # 가중 중앙값
    o = np.argsort(S); cw = np.cumsum(w[o]); med = S[o][np.searchsorted(cw, cw[-1] * 0.5)]
    return dict(sat_med=float(med), sat_mean=float((S * w).sum() / w.sum()),
                lum_mean=float((L * w).sum() / w.sum()),
                dLum=float((L * w).sum() / w.sum() - BG))

def show(name, pal, **kw):
    r = profile(pal, **kw)
    cols = ' '.join('%s' % ('%02X%02X%02X' % tuple(np.round(lin2srgb(aces(hex2lin(pal[k])))*255).astype(int)))
                    for k in ['DK2','DK1','MID','LT1','LT3','WHT'])
    print(f"{name:12s} 채도중앙 {r['sat_med']:.3f}  평균 {r['sat_mean']:.3f}  "
          f"휘도 {r['lum_mean']:6.1f} (배경대비 {r['dLum']:+5.1f})   화면색 {cols}")
    return r

OLD = dict(DK2='123054', DK1='1E4272', MID='4884A2', LT1='549CBA',
           LT2='60A8C6', LT3='72C0E4', WHT='F0F0F8')



def _demo_fit():
    """지금 물 팔레트와 옛 팔레트를 밴드 단면으로 모사해 나란히 잰다."""
    show('옛 물팔레트', OLD)
    NEW = dict(DK2='112F54', DK1='186095', MID='1E81B1', LT1='239DCC',
               LT2='38A5D0', LT3='3BCCF9', WHT='E8F2FA')
    show('지금(v99)', NEW)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'fit':
        _demo_fit()
    else:
        WATER = ['112F54', '186095', '1E81B1', '239DCC', '38A5D0', '3BCCF9', 'E8F2FA']
        print('  hex     원채도  ->  화면hex  화면채도  화면휘도')
        for h in WATER:
            r = screen(h)
            print(f"  {r['hex']}  {r['src_sat']:.3f}  ->  {r['out_hex']}  {r['out_sat']:.3f}   {r['out_lum']:6.1f}")
