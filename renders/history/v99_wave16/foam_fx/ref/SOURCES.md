# 귀멸 물의 호흡 거품 — 실측 근거 출처

## 원본
- `water-breathing.mp4` (프로젝트 루트, 1080x1920 60fps) — 애니 『귀멸의 칼날』 물의 호흡 클립
- `water-breathing2.mp4` (프로젝트 루트, 1920x1080 30fps) — 같은 계열 클립
두 파일은 11차(v97) FX 조사에서 이미 쓴 것과 같은 원본이다(`renders/history/v97_wave11/fx_research.md` 0절).

## 추출 방법
원작이 24fps 작화라 컨테이너의 중복 프레임을 걷어내려고 **fps=24 로 재추출**했다.
```
ffmpeg -ss 15.2 -i water-breathing.mp4  -t 1.0 -vf "fps=24,scale=1080:-1" ref/raw/wb1_a_%03d.png
ffmpeg -ss  7.0 -i water-breathing.mp4  -t 1.0 -vf "fps=24,scale=1080:-1" ref/raw/wb1_b_%03d.png
ffmpeg -ss 172.0 -i water-breathing2.mp4 -t 1.5 -vf "fps=24,scale=1280:-1" ref/raw/wb2_a_%03d.png
ffmpeg -ss 133.6 -i water-breathing2.mp4 -t 1.5 -vf "fps=24,scale=1280:-1" ref/raw/wb2_b_%03d.png
```
총 120장. 거품이 제일 또렷한 여섯 칸을 잘라 `foam_ref_1..6_*.png` 로 남겼다.

| 파일 | 원본 프레임 | 무엇을 보나 |
|---|---|---|
| foam_ref_1_head_hook.png | wb1_a_011 | 갈고리·와권 거품 뭉치가 리본 바깥면에 붙은 정본 |
| foam_ref_2_crest_a.png | wb1_a_013 | 마루 거품이 연달아 붙은 긴 리본 |
| foam_ref_3_crest_b.png | wb1_a_015 | 거품이 리본에서 떨어져 나가기 시작하는 칸 |
| foam_ref_4_crest_c.png | wb1_a_019 | 여러 가닥 + 거품 동시 |
| foam_ref_5_scroll.png | wb1_a_022 | 와권(소용돌이) 형태가 제일 또렷 |
| foam_ref_6_strike.png | wb1_a_008 | 베는 순간(머리 쪽) |
| sheet_wb1_a.jpg | wb1_a_001~024 | 24칸 연속 — 거품의 발생·소멸 순서 |

## 내가 잰 것 (numpy, 위 6장)
- 거품 흰색 평균 rgb (0.90~0.95, 0.94~0.98, 0.96~0.99) · 채도 0.03~0.05 · 화면 V 중앙값 253/255
- 면적비 흰 거품 10~30% : 청색 밴드 24~41% (머리 쪽에서는 거의 맞먹는다)
- 먹선 V 0.13 안팎 — 순검정이 아니라 감청 먹

## 웹 조사 (2차 근거. 11차에서 확인한 것을 그대로 물려받는다)
- 감독 소토자키 하루오 공식 인터뷰: "호쿠사이 우키요에를 모티브", "흰 파도(포말)의 균형이 관건"
- 호쿠사이 「가나가와 앞바다 높은 파도 아래」 해부: 마루가 말려 **갈퀴(claw) 손가락 3~7개**가 되고
  각 손가락 끝에서 물방울이 떨어진다. **말림은 진행 방향 마루에 있다**(꼬리가 아니다)
- 프로듀서 타카하시 유마(ANN 2019-08-28): 물의 호흡 파도는 거의 전부 수작업 작화
출처 URL 은 `renders/history/v97_wave11/fx_research.md` 5·6절에 그대로 있다.
