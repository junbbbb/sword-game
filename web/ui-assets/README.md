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
- 원본 보관 위치: Codex 생성 이미지 저장소
- 게임용 변환: `512 × 512`, WebP 품질 90

## `bronze-ornament-frame.webp`

주요 알림창에 얹는 `768 × 768` 투명 장식 프레임이다. 얇은 청동 이중선과 네 종류의
고유한 모서리 장식을 한 장에 담았다. 상시 HUD에는 쓰지 않고 로딩·입장·레벨업·사망·
클리어처럼 화면의 주인이 되는 카드에만 사용한다.

### 생성 정보

- 방식: Codex 내장 ImageGen + 로컬 크로마키 제거
- 핵심 프롬프트: `original square 9-slice fantasy UI frame; thin antique-bronze
  double rails; four restrained leaf, horn, knot and shield-scroll corners; flat
  magenta chroma key; no panel fill, text, logo, trademark or recognizable motif`
- 원본 생성 크기: `1254 × 1254` PNG
- 원본 보관 위치: Codex 생성 이미지 저장소
- 게임용 변환: 투명 배경 `768 × 768` WebP

## `bronze-skills.webp`

Bronze Story 테마용 `512 × 512` 스킬 스프라이트다. 위치 계약은 위 Abyss 시트와 같다.
아이보리 검광, 꿀빛 금색, 낡은 구리와 작은 불씨색만 사용해 작은 슬롯에서도 읽히게 했다.

### 생성 정보

- 방식: Codex 내장 ImageGen
- 핵심 프롬프트: `exact 2x2 sword-skill sprite; triple slash, vertical cleave,
  horizontal crescent, upward leap; warm ivory, honey gold, aged copper; charcoal
  brown background; no purple, cyan, text, keycap, character, logo or trademark`
- 원본 생성 크기: `1254 × 1254` PNG
- 게임용 변환: `512 × 512`, WebP 품질 91

## `fonts/Galmuri11-Bold.woff2`

주요 제목과 알림 문구에 쓰는 한글 픽셀 폰트다. Galmuri v2.40.4의 공식 WOFF2를
자체 호스팅한다. SIL Open Font License 1.1 원문과 저작권 고지는
`fonts/OFL-Galmuri.md`에 함께 보관한다.
