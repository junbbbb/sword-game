# UI 에셋

## `abyss-skills.webp`

`512 × 512` WebP 스프라이트 시트다. CSS에서 `background-size: 200% 200%`로 사용한다.

| 위치 | 기술 |
|---|---|
| 왼쪽 위 | `Basic` · 연속 베기 |
| 오른쪽 위 | `Heavy` · 수면참 |
| 왼쪽 아래 | `Wide` · 횡일섬 |
| 오른쪽 아래 | `Jump` / `Dash` · 도약 |

교체할 때는 같은 크기와 2×2 배치만 지키면 CSS를 수정하지 않아도 된다. 키 문자와
기술명은 이미지에 굽지 않고 DOM으로 올리므로 이미지에는 글자를 넣지 않는다.

### 생성 정보

- 방식: Codex 내장 ImageGen
- 용도: 독자적인 다크 판타지 검사 스킬 아이콘
- 핵심 프롬프트: `exact 2x2 sprite sheet; triple slash, vertical moon-cleave,
  horizontal crescent slash, upward leap; icy cyan core, electric violet edge;
  uniform near-black navy background; no text, frame, logo, trademark, character or
  recognizable symbol from existing media`
- 원본 생성 크기: `1254 × 1254` PNG
- 게임용 변환: `512 × 512`, WebP 품질 90
