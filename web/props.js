// ---------------------------------------------------------------------------
// web/props.js — 맵 소품을 씬에 심는다.
//   자연 소품 5종  바위·절벽바위·덤불·나무·수풀   (blender/s22_props.py 가 굽는다)
//   지형   5종  절벽기둥·노두·거대바위·기슭·판석  (blender/s28_terrain.py 가 굽는다, v91)
//
// 왜 별도 파일인가
//   이 10종이 맵에 827개 깔린다. 상세 모델을 level1.glb 에 통째로 구우면
//   삼각형이 수백만이 되고 파일이 수십 MB 가 된다. 그래서
//     · 모양  = web/props/<종류>.glb  (종류당 한 벌만 굽는다)
//     · 배치  = level1.json 의 props[]  (blender/s20_level1.py 가 뽑는다)
//     · 심기  = 이 파일
//   로 셋을 갈라 놨다. 콜라이더는 level1.json 의 colliders[] 에 이미 다 들어 있고
//   이 파일과 아무 관계가 없다(소품을 어떻게 그리든 충돌은 안 변한다).
//   ★v91 지형 5종은 **콜라이더가 아예 없다.** 이미 막혀 있는 자리(외곽 절벽 링·
//     너덜 덩어리·물칸)를 덮는 장식이라 충돌은 기존 것이 그대로 한다.
//
// ★수풀만 InstancedMesh 가 아니다
//   은신 연출(web/stealth.js)은 **BUSH_xx 라는 이름의 메시**를 찾아 그 재질의
//   투명도를 낮춘다("내가 들어간 수풀만 옅어진다"). InstancedMesh 는 인스턴스마다
//   다른 투명도를 줄 수 없으므로, 수풀은 구역(16곳)별로 지오메트리를 합쳐
//   **구역당 메시 하나**로 심고 이름을 BUSH_01..16 으로 붙인다.
//   = 드로우콜 16, 기존 은신 연출 코드는 한 줄도 안 고쳐도 그대로 돈다.
//
// ★인스턴스 단위 컬링 (2026-08-10 9차 파도에 다시 짬)
//   InstancedMesh 는 three.js 가 통째로만 걸러낸다(경계구가 맵 전체를 덮으니
//   사실상 항상 다 그린다). 96m 맵인데 한 화면에 들어오는 건 앞 10.9m·뒤 3.9m·
//   폭 16.3m 뿐이라(= __probe 실측) 그대로 두면 안 보이는 바위 수백 개를 매 프레임 그린다.
//   그래서 매 프레임 절두체로 골라 instanceMatrix 를 다시 채운다.
//
//   ★★핵심: **화면 패스와 그림자 패스는 필요한 목록이 다르다.**
//     화면 = 카메라 절두체.  그림자 = 해의 그림자 상자(캐릭터 ±10m).
//     화면 뒤 8m 에 있는 절벽은 화면엔 없지만 그림자는 화면 안으로 드리운다.
//     예전 판은 목록이 하나뿐이라 "카메라 절두체 + 7m 여유" 로 뭉뚱그렸고,
//     그 7m 때문에 화면 패스가 필요량의 3~4배를 그렸다.
//     지금은 한 버퍼 안에 **[화면에 보이는 것들] + [그림자만 지는 것들]** 순서로 채운다.
//       · 그림자 패스는 count = 전부(nAll)  · 화면 패스는 count = 앞쪽 nCam
//     앞에서부터 채우니 두 패스가 같은 버퍼를 나눠 쓴다. 여유는 0.6m 면 된다.
//
//   ★★그리고 컬링을 **scene.onBeforeRender 에서** 돌린다.
//     three 는 instanceMatrix 를 projectObject 에서 한 번만 GPU 로 올린다.
//     그 뒤에 부르는 mesh.onBeforeRender 에서 배열을 고쳐 봐야 **다음 프레임에** 올라간다
//     (예전 판이 그랬다. 목록과 count 가 한 프레임 어긋나 있었고, 그게 여유 7m 의 진짜 이유다).
//     scene.onBeforeRender 는 projectObject **앞**이라 같은 프레임에 올라간다.
//     같은 자리에서 camera·해 행렬이 둘 다 최신이라 예측도 여유도 필요 없다.
//
// ★크기 기반 LOD (2026-08-10, 9차 파도에 축소)
//   설치형으로 방향이 바뀌면서 소품 예산이 4~8배로 올랐고(s22_props.py),
//   종류별 scale 상위 30% 를 고폴리로 심었더니 씬 삼각형이 242만이 됐다.
//   ★그런데 스크린샷 대조 결과 **수풀 말고는 고폴리와 저폴리가 구분이 안 된다.**
//     (renders/history/v94_wave9/perf/ 에 종류별 근접 대조 9장. 바위·절벽·나무·
//      거대바위 전부 육안 차이 없음. 모양 정보를 텍스처와 툰 셰이딩이 이미 지고 있다.)
//     수풀만 다르다. 플레이어가 **안에 들어가 2~4m 에서 본다**. 저폴리로 내리면
//     잎 조각이 뭉개져 "상추 더미"가 된다.
//   그래서
//     · 수풀      = 종류 안에서 scale 상위 30% 고폴리 (예전 규칙 그대로)
//     · 나머지 9종 = 전부 저폴리(web/props/low/<종류>.glb)
//   씬 삼각형 242만 -> 139만. 화면 품질은 그대로다.
//   ★재질은 고폴리 텍스처 한 장을 두 단계가 같이 쓴다. 저폴리 glb 안의 텍스처를
//     따로 쓰면 같은 종류인데 큰 것과 작은 것의 색이 미묘하게 달라진다. 전부 저폴리로
//     내려간 종류도 **고폴리 텍스처를 그대로 쓴다**(저폴리 텍스처는 해상도가 낮다).
//   ★수풀은 구역 메시 하나 안에 두 단계를 **같이 합친다**(아래 mergeParts).
//     구역당 메시가 둘로 갈라지면 stealth.js 가 이름으로 찾는 메시가 반쪽만 돼서
//     "내가 들어간 수풀만 옅어진다" 가 절반만 먹는다.
//   ?lod=off  전부 고폴리 / ?lod=low  전부 저폴리 (성능·품질 비교용)
// ---------------------------------------------------------------------------
import * as THREE from './lib/three.module.js';
import { GLTFLoader } from './lib/GLTFLoader.js';

// 종류별 세로 배율.
// ★가로는 절대 안 건드린다. 배치 scale 이 콜라이더 반지름과 같은 숫자라
//   가로를 만지는 순간 보이는 것과 막히는 것이 어긋난다. 세로만 만진다.
//   crag  : Meshy 모델이 낮아서(정규화하면 2.07m) 그냥 두면 캐릭터 키(1.75)를
//           겨우 넘는다. 막는 지형 기준 높이 WALL_H=2.6 에 맞춘다(2.07 x 1.25).
//   thicket: 받은 모델이 납작하다(Y 가 XZ 의 45%). 세워서 덤불로 만든다.
//   bush   : ★2026-08-10. 1.0 이면 잎 높이가 1.10~1.61m 라 키 1.75 캐릭터의
//            **무릎만 잠긴다**(v72 QA: "상추 더미 위에 서 있는 그림").
//            1.35 로 올리면 1.49~2.18m(평균 1.84m)가 되어 가슴~머리가 잎에 걸린다.
//            ★세로 배율일 뿐이다. 콜라이더도 은신 판정 사각형(level1.json bushes[].rects)도
//              가로 좌표로만 정의돼 있어서 이 숫자와 무관하다(수풀에는 콜라이더 자체가 없다).
//              지오메트리 원점이 밑동이라 배율을 올려도 접지는 그대로다.
//   ★v91 지형 5종은 **전부 1.0** 이다. s28_terrain.py 가 이미 게임 안 실치수로
//     정규화해서 굽는다(절벽 기둥 4.60m, 노두 1.55m, 거대바위 1.255m, 기슭 0.583m,
//     판석 0.142m). 세로 변주는 level1.json 의 sy 가 프롭마다 따로 준다.
//     ★여기서 세로를 만지면 안 된다. 절벽 기둥은 뒷면·옆면이 평면으로 잘려 있어서
//       이웃과 어깨를 맞대는데, 종류 단위로 높이를 곱하면 그 줄 전체가 같이 늘어나
//       "같은 비율로 늘린 기둥 여덟 개"가 된다(복붙 티가 나는 바로 그 그림이다).
//   ★2026-08-11(11-소품B). crag·bush 의 메시를 Meshy 재생산본으로 갈았는데
//     **이 표는 한 줄도 안 건드렸다.** 새 원본이 더 납작했지만(crag 높이/반너비
//     1.63 -> 1.13) 굽는 자리(blender/s30_props_v2.py 의 zfit)에서 옛 glb 와
//     **같은 높이·같은 반너비**로 맞춰 내보냈기 때문이다. 세로 배율이 여기와 저기
//     두 곳에 흩어지면 나중에 어느 쪽이 얼마를 곱하는지 아무도 못 읽는다.
const KIND_Y = {
  rock: 1.0, crag: 1.25, thicket: 1.70, tree: 1.0, bush: 1.35,
  cliff_tall: 1.0, outcrop: 1.0, boulder_xl: 1.0, bank: 1.0, slab: 1.0,
  cliff_tall_b: 1.0,          // ★절벽 기둥 변주. 원본과 같은 봉투라 값도 같다
};

// ---------------------------------------------------------------------------
// ★종 변형 — 같은 배치에 다른 메시를 섞는다 (2026-08-11, 11차 파도 11-소품B)
// ---------------------------------------------------------------------------
// 11차 소품 진단: "cliff_tall(115개)은 텍스처가 좋다. 문제는 **실루엣이 민짜
// 직육면체**라 115개가 줄지어 서면 벽돌 복붙으로 보인다. 재생산보다 변주 2~3벌이 답이다."
//
// 변주를 배치 테이블에 넣으려면 blender/s20_level1.py 를 다시 구워야 하는데,
// 그러면 난수 스트림이 흔들려 **배치 878개와 콜라이더 111개가 통째로 다시 뽑힌다.**
// 이 작업의 전제(콜라이더 불변)와 정면으로 부딪힌다. 그래서 여기서 가른다.
//   · level1.json 은 한 바이트도 안 바뀐다(배치·콜라이더·수풀 구역 전부 그대로)
//   · 어느 인스턴스가 변주가 되는지는 **좌표 해시**로 정한다 = 언제 열어도 같은 그림
//     (인덱스로 가르면 배치 순서가 곧 공간 순서라 한 줄이 통째로 갈린다)
//   · 변주 glb 가 없으면 조용히 원래 종 하나로 되돌아간다(맵이 안 죽는다)
// ★변주 메시는 봉투(반너비 0.541 / 높이 4.60)가 원본과 같다. 그래야 배치의
//   scale·sy 가 그대로 통하고, s20 이 앞면을 막는 선 + 0.35m 에 세운 계산이 안 어긋난다.
const VARIANT = {
  cliff_tall: { as: 'cliff_tall_b', frac: 0.35 },
};

// 좌표 해시(0~1). 같은 맵이면 언제나 같은 값이 나온다.
function hash01(x, z) {
  const s = Math.sin(x * 127.1 + z * 311.7) * 43758.5453;
  return s - Math.floor(s);
}
// ★심는 종류 목록은 따로 안 적는다. level1.json 의 props[] 에 나온 kind 를 그대로
//   훑어서 ./props/<kind>.glb 를 읽는다(아래 build). 그래서 s20 이 새 종류를
//   내보내면 이 파일은 한 줄도 안 고쳐도 심긴다. 예외는 딱 하나, 수풀이다
//   (은신 연출 때문에 InstancedMesh 가 아니라 구역 메시로 합친다).
const BUSH_KIND = 'bush';
// 절두체 판정에 더하는 여유(m).
// ★예전엔 7.0 이었다. (가) 목록이 한 프레임 늦게 GPU 로 올라갔고 (나) 그림자 몫까지
//   같은 목록으로 덮어야 했기 때문이다. 둘 다 없앴으니(위 주석) 이제 순수한 안전 여유다.
//   경계구는 이미 지오메트리 실측 + 축 최대배율이라 넉넉한 쪽으로 잡혀 있다.
const CULL_PAD = 0.6;
// 고폴리로 심을 비율(수풀 전용. 종류 안에서 scale 상위 몇 %)
const LOD_HI_FRAC = 0.30;

// ---------------------------------------------------------------------------
// ★소품 전용 명암 램프 (2026-08-11, 11차 소품 진단)
// ---------------------------------------------------------------------------
// 오너: "나무랑 돌 같은 거 너무 저퀄 느낌 나서."
// 자를 대 보니 진범은 메시도 텍스처도 아니었다. **명암 모델링이 통째로 없었다.**
// 같은 바위를 해 쪽 / 반대쪽에서 찍어 밝기를 비교한 실측
// (`tools/prop_lab.html` · 증거 `renders/history/v97_wave11/props/`):
//
//     오너 레퍼런스(롤) 바위 ........ 1.63 배
//     우리 소품 ..................... 1.13 배    <- 사실상 평면
//     민무늬로 조명만 재면 .......... 1.10 배  (램버트라면 1.45)
//
// 원인: three r160 의 MeshToonMaterial 은 gradientMap 이 없으면 램프가
//   `mix(0.7, 1.0, step(dotNL > 0.4))` — **두 단뿐**이고 뒤통수(dotNL = -1)도
//   해의 70% 를 받는다. 조명이 만드는 명암의 **78% 를 램프가 버린다.**
//   (그래서 Meshy 노멀맵을 되살려도 화면이 한 톨도 안 변한다 — 실측 +0%.
//    단이 하나뿐이라 요철이 앉을 자리가 없다.)
//
// → 소품만 **4단 셀 램프**로 바꾼다. 셀(계단)은 그대로라 캐릭터와 화풍이 안 갈린다.
//   밝은 쪽 끝을 1.0 으로 못 박은 이유: 소품 색은 tools/regrade_props.py 가
//   **볕 든 면 기준 화면 목표색**에 맞춰 놓은 값이다. 위를 건드리면 색계약이 깨진다.
//   실측 대가: 볕 든 면 평균 밝기 -3.5%, 볕/그늘 비 1.10 -> 1.23 (민무늬 기준).
//
// ★ 램프 texel 하나가 dotNL 한 구간이다. three 는
//   `texture2D(gradientMap, vec2(dotNL*0.5+0.5, 0)).r` 로 읽으므로
//   칸 i 의 dotNL 은 `2*(i+0.5)/N - 1` 이다. NearestFilter 여야 단이 딱 떨어진다.
// ★★함정: `map` 이 null 이면 three 는 gradientMap 을 **통째로 무시한다**(r160 실측).
//   소품은 전부 텍스처가 있으므로 여기서는 안 걸리지만, 민무늬 재질에 램프를
//   물리려다 "안 먹는다" 로 헤매기 쉽다.
const RAMP_N = 16;
const RAMP = (() => {
  const d = new Uint8Array(RAMP_N * 4);
  for (let i = 0; i < RAMP_N; i++) {
    const dot = 2 * (i + 0.5) / RAMP_N - 1;
    const v = dot <= -0.15 ? 0.22 : dot <= 0.15 ? 0.46 : dot <= 0.50 ? 0.74 : 1.0;
    const b = Math.round(v * 255);
    d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = b; d[i * 4 + 3] = 255;
  }
  const t = new THREE.DataTexture(d, RAMP_N, 1, THREE.RGBAFormat);
  t.minFilter = t.magFilter = THREE.NearestFilter;
  t.generateMipmaps = false;
  t.needsUpdate = true;
  return t;
})();

let ROOT = null;                 // 소품을 담는 그룹(맵 root 밑에 붙는다)
const INST = [];                 // { kind, lod, mesh, all, cen, rad, n, nCam, nAll, tmp, triOne }
const BUSHES = [];               // { id, mesh }
let culling = true;
let SCENE = null;                // 컬링 훅을 물린 씬(두 번 물지 않게 기억한다)
let SUN = null;                  // 그림자를 지는 직사광. 없으면 그림자 몫을 안 챙긴다
let sunTries = 0;                // 조명이 소품보다 늦게 붙는 경우를 대비해 몇 프레임 더 찾는다
const _frustum = new THREE.Frustum();
const _pv = new THREE.Matrix4();
const _sph = new THREE.Sphere();

// ---------------------------------------------------------------------------
// 지오메트리 합치기 (수풀 구역용)
// ---------------------------------------------------------------------------
// ★lib 에 BufferGeometryUtils 가 없다. 필요한 건 "지오메트리를 행렬 여러 개로
//   복제해 하나로 붙이기" 하나뿐이라 여기 적었다.
// parts = [{ geo, mats }, ...]. **서로 다른 지오메트리를 한 덩어리로** 합칠 수 있다
// (수풀 구역 하나 안에 고폴리·저폴리가 섞이는데 메시는 하나여야 하기 때문이다).
// 두 지오메트리가 같은 텍스처를 쓰므로 UV 를 그대로 이어 붙여도 된다.
//
// shade = 정점색을 굽는 설정(수풀 전용, 없으면 색 속성을 안 만든다). 아래 SHADE 참고.
function mergeParts(parts, shade) {
  let vcTot = 0, icTot = 0;
  for (const p of parts) {
    vcTot += p.geo.attributes.position.count * p.mats.length;
    icTot += p.geo.index.count * p.mats.length;
  }
  const P = new Float32Array(vcTot * 3);
  const N = new Float32Array(vcTot * 3);
  const U = new Float32Array(vcTot * 2);
  const C = shade ? new Float32Array(vcTot * 3) : null;
  const I = (vcTot > 65535) ? new Uint32Array(icTot) : new Uint16Array(icTot);
  const v = new THREE.Vector3();
  const nm = new THREE.Matrix3();
  let vo = 0, io = 0;
  for (const part of parts) {
    const pos = part.geo.attributes.position;
    const nor = part.geo.attributes.normal;
    const uv = part.geo.attributes.uv;
    const idx = part.geo.index;
    const vc = pos.count, ic = idx.count;
    // 이 지오메트리 한 포기의 높이(로컬). 잎 높낮이를 0..1 로 재는 자다
    let lh = 1;
    if (shade) {
      part.geo.computeBoundingBox();
      lh = Math.max(1e-3, part.geo.boundingBox.max.y - part.geo.boundingBox.min.y);
    }
    for (const m of part.mats) {
      nm.getNormalMatrix(m);
      for (let i = 0; i < vc; i++) {
        const o3 = (vo + i) * 3;
        const ly = pos.getY(i);
        v.fromBufferAttribute(pos, i).applyMatrix4(m);
        P[o3] = v.x; P[o3 + 1] = v.y; P[o3 + 2] = v.z;
        if (C) shadeVertex(C, o3, shade, v.x, v.z, ly / lh);
        v.fromBufferAttribute(nor, i).applyMatrix3(nm).normalize();
        N[o3] = v.x; N[o3 + 1] = v.y; N[o3 + 2] = v.z;
        U[(vo + i) * 2] = uv.getX(i);
        U[(vo + i) * 2 + 1] = uv.getY(i);
      }
      for (let i = 0; i < ic; i++) I[io + i] = idx.getX(i) + vo;
      vo += vc; io += ic;
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(P, 3));
  g.setAttribute('normal', new THREE.BufferAttribute(N, 3));
  g.setAttribute('uv', new THREE.BufferAttribute(U, 2));
  if (C) g.setAttribute('color', new THREE.BufferAttribute(C, 3));
  g.setIndex(new THREE.BufferAttribute(I, 1));
  g.computeBoundingSphere();
  return g;
}

// ---------------------------------------------------------------------------
// ★수풀 정점색 — "수풀 속이 텅 비고 균일한 형광 연두" 를 깨는 장치 (2026-08-10)
// ---------------------------------------------------------------------------
// v72 QA: 수풀 덩어리가 어디를 봐도 같은 밝기라 **부피가 없고**, 안에 들어가도
// 안쪽이 어둡지 않아 "숨을 데"로 안 읽혔다. 라이트를 더 넣어 풀 문제가 아니다.
// 잎 뭉치는 실제로 두 가지 이유로 안쪽이 어둡다.
//   1) 위에서 오는 빛이 윗잎에 막힌다  -> 밑동이 어둡다
//   2) 사방이 잎에 둘러싸인다          -> 구역 안쪽이 어둡다 (가장자리는 트여 있다)
// 이 둘을 정점색으로 구워 둔다. 매 프레임 계산이 아니라 로드 때 한 번이고,
// 어떤 셰이더도 안 건드린다(MeshToonMaterial.vertexColors 만 켜면 diffuse 에 곱해진다).
// ★깊이 패스는 정점색을 안 읽으므로 그림자는 그대로다.
const SHADE_DARK = [0.13, 0.21, 0.18];   // 제일 어두운 구석의 색(차가운 먹빛 초록)
const SHADE_BOT = 0.62;                  // 밑동이 먹는 어둠의 양
const SHADE_IN = 0.46;                   // 구역 안쪽이 먹는 어둠의 양
const SHADE_IN_D = 1.9;                  // 이 거리(m)만큼 안으로 들어가면 최대로 어둡다

function shadeVertex(C, o3, sh, wx, wz, hy) {
  // hy: 한 포기 안에서의 높이 0(밑동)~1(꼭대기)
  const up = hy < 0 ? 0 : hy > 1 ? 1 : hy;
  const bot = Math.pow(1 - up, 1.25);
  // 구역 경계까지의 거리. 가장자리 잎은 밖에서 빛을 받아 밝다
  const d = Math.min(wx - sh.x0, sh.x1 - wx, wz - sh.z0, sh.z1 - wz);
  const inn = d <= 0 ? 0 : d >= SHADE_IN_D ? 1 : d / SHADE_IN_D;
  let s = 1 - (SHADE_BOT * bot + SHADE_IN * inn);
  if (s < 0.14) s = 0.14; else if (s > 1) s = 1;
  C[o3] = SHADE_DARK[0] + (1 - SHADE_DARK[0]) * s;
  C[o3 + 1] = SHADE_DARK[1] + (1 - SHADE_DARK[1]) * s;
  C[o3 + 2] = SHADE_DARK[2] + (1 - SHADE_DARK[2]) * s;
}

// ---------------------------------------------------------------------------
// 로드
// ---------------------------------------------------------------------------
// parent : 맵 root(여기 밑에 붙여야 stealth.js 가 BUSH_xx 를 찾는다)
// lv     : level1.json
// q      : 캐시버스팅 쿼리(맵과 같은 값을 물려받는다)
// groundY: 지면 높이 함수(level.js). 낮은 단 위에 선 소품이 묻히지 않게 한다
export async function build(parent, lv, q, groundY) {
  const list = lv.props || [];
  if (!list.length) { console.warn('[props] level1.json 에 props[] 가 없다'); return null; }
  const dev = (q || '').includes('dev');
  ROOT = new THREE.Group();
  ROOT.name = 'PROPS';
  parent.add(ROOT);

  const byKind = {};
  for (const p of list) (byKind[p.kind] = byKind[p.kind] || []).push(p);

  const loader = new GLTFLoader();
  const assets = {}, low = {};
  // ── 변형 섞기 (위 ★종 변형) ──
  // 먼저 변형 glb 를 읽어 보고, **읽힌 것만** 배치를 갈라 준다.
  // 실패해도 그냥 넘어가므로 파일이 빠져 있으면 예전 그대로 돈다.
  const varLog = [];
  await Promise.all(Object.keys(VARIANT).map(base => new Promise(ok => {
    if (!byKind[base]) return ok();
    const as = VARIANT[base].as;
    loader.load('./props/' + as + '.glb' + q, g => { assets[as] = g; ok(); },
                undefined, () => ok());
  })));
  for (const base of Object.keys(VARIANT)) {
    const as = VARIANT[base].as;
    if (!byKind[base] || !assets[as]) continue;
    const keep = [], swap = [];
    for (const p of byKind[base]) (hash01(p.x, p.z) < VARIANT[base].frac ? swap : keep).push(p);
    if (!swap.length || !keep.length) continue;      // 한쪽이 비면 가르는 뜻이 없다
    byKind[base] = keep;
    byKind[as] = swap;
    varLog.push(base + ' ' + keep.length + ' + ' + as + ' ' + swap.length);
  }
  const kinds = Object.keys(byKind);

  await Promise.all(kinds.map(k => assets[k] ? Promise.resolve() : new Promise((ok, bad) => {
    loader.load('./props/' + k + '.glb' + q, g => { assets[k] = g; ok(); }, undefined, bad);
  })));
  // 저폴리 한 벌. **없어도 그냥 돈다**(그 종류는 전부 고폴리로 심는다).
  const lodMode = new URLSearchParams(q || '').get('lod') || 'on';
  if (lodMode !== 'off') {
    await Promise.all(kinds.map(k => new Promise(ok => {
      loader.load('./props/low/' + k + '.glb' + q,
        g => { low[k] = g; ok(); }, undefined, () => ok());
    })));
  }

  const gy = groundY || (() => lv.floorY || 0);
  const qt = new THREE.Quaternion();
  const ax = new THREE.Vector3(0, 1, 0);
  const tr = new THREE.Vector3();
  const sc = new THREE.Vector3();
  let tri = 0;

  const lodLog = [];
  for (const kind of kinds) {
    const src = pickMesh(assets[kind]);
    if (!src) { console.warn('[props] ' + kind + '.glb 안에 메시가 없다'); continue; }
    const geoHi = src.geometry;
    geoHi.computeBoundingSphere();
    const lowSrc = low[kind] ? pickMesh(low[kind]) : null;
    const geoLo = lowSrc ? lowSrc.geometry : null;
    if (geoLo) geoLo.computeBoundingSphere();
    // ★main.js 관례: 맵·캐릭터 전부 MeshToonMaterial 로 갈아끼운다.
    //   Meshy 재질(Standard PBR)을 그대로 두면 이 소품만 셀 셰이딩에서 빠진다.
    // ★재질은 하나뿐이다. 두 LOD 단계가 **같은 텍스처**를 쓴다(위 주석).
    const mat = new THREE.MeshToonMaterial({
      map: src.material && src.material.map ? src.material.map : null,
      color: src.material && src.material.map ? 0xffffff : 0x8a9199,
      gradientMap: RAMP,          // ★위 '소품 전용 명암 램프' 주석 참고
    });
    mat.name = 'MAT_PROP_' + kind.toUpperCase();
    if (lowSrc && lowSrc.material && lowSrc.material.map) lowSrc.material.map.dispose();
    const ky = KIND_Y[kind] || 1;
    const rows = byKind[kind];
    const mats = rows.map(p => {
      const s = p.scale || 1;
      tr.set(p.x, gy(p.x, p.z), p.z);
      qt.setFromAxisAngle(ax, p.rotY || 0);
      sc.set(s, s * (p.sy || 1) * ky, s);
      return new THREE.Matrix4().compose(tr, qt, sc);
    });

    // ── LOD 가르기 ──
    // ★수풀만 두 단계로 나눈다. 나머지는 전부 저폴리다(맨 위 주석의 대조 근거).
    //   thr = 이 값 이상이면 고폴리. -Infinity 면 전부 고폴리, Infinity 면 전부 저폴리.
    let thr = -Infinity;                       // 저폴리가 없는 종류 = 전부 고폴리
    if (geoLo) {
      if (lodMode === 'off') thr = -Infinity;              // 비교용: 전부 고폴리
      else if (lodMode === 'low') thr = Infinity;          // 비교용: 전부 저폴리
      else if (kind === BUSH_KIND) {
        // 같은 scale 이 여럿이면 경계에서 조금 넘칠 수 있다(그래도 상관없다).
        const ss = rows.map(p => p.scale || 1).sort((a, b) => a - b);
        thr = ss[Math.min(ss.length - 1, Math.floor(ss.length * (1 - LOD_HI_FRAC)))];
      } else thr = Infinity;                                // 평시: 수풀 아닌 건 전부 저폴리
    }
    const hiRows = [], loRows = [];
    rows.forEach((p, i) => (((p.scale || 1) >= thr) ? hiRows : loRows).push(i));
    lodLog.push(kind + ' ' + hiRows.length + '/' + loRows.length);
    // 안 쓰는 고폴리 지오메트리는 버린다(텍스처는 위에서 이미 재질로 넘겼다).
    // ★수풀은 절대 버리면 안 된다. 구역 메시가 이 지오메트리로 합쳐진다.
    if (!hiRows.length && geoLo && kind !== BUSH_KIND) geoHi.dispose();

    if (kind === BUSH_KIND) {
      // 구역별로 합쳐서 BUSH_xx 메시 하나씩 (위 주석 참고).
      // ★한 구역 안에서도 고·저폴리가 섞이지만 **메시는 하나**로 합친다.
      // ★정점색(안쪽 그늘)을 굽는다. 재질 하나를 16곳이 같이 쓰므로 여기서 켠다.
      mat.vertexColors = true;
      const reg = {};
      rows.forEach((p, i) => {
        const id = p.bush || 'BUSH_00';
        const r = (reg[id] = reg[id] || { hi: [], lo: [], x0: 1e9, x1: -1e9, z0: 1e9, z1: -1e9 });
        (((p.scale || 1) >= thr) ? r.hi : r.lo).push(mats[i]);
        // 구역 테두리는 심은 포기의 좌표로 잰다. level1.json 의 rects 를 안 읽는 이유는
        // 맵이 수풀을 옮겨도(맵 에이전트 작업) 이 파일이 따라 도는 게 맞기 때문이다.
        if (p.x < r.x0) r.x0 = p.x;
        if (p.x > r.x1) r.x1 = p.x;
        if (p.z < r.z0) r.z0 = p.z;
        if (p.z > r.z1) r.z1 = p.z;
      });
      for (const id of Object.keys(reg).sort()) {
        const r = reg[id];
        const parts = [];
        if (r.hi.length) parts.push({ geo: geoHi, mats: r.hi });
        if (r.lo.length && geoLo) parts.push({ geo: geoLo, mats: r.lo });
        else if (r.lo.length) parts.push({ geo: geoHi, mats: r.lo });
        const m = new THREE.Mesh(mergeParts(parts, r), mat);
        m.name = id;
        m.castShadow = true;
        m.receiveShadow = true;
        ROOT.add(m);
        const t = m.geometry.index.count / 3;
        BUSHES.push({ id, mesh: m, n: r.hi.length + r.lo.length, hi: r.hi.length });
        tri += t;
      }
      continue;
    }

    for (const lvl of [{ tag: 'HI', geo: geoHi, idx: hiRows },
                       { tag: 'LO', geo: geoLo || geoHi, idx: loRows }]) {
      const n = lvl.idx.length;
      if (!n) continue;
      const triOne = lvl.geo.index.count / 3;
      const im = new THREE.InstancedMesh(lvl.geo, mat, n);
      im.name = 'PROP_' + kind.toUpperCase() + (geoLo ? '_' + lvl.tag : '');
      im.castShadow = true;
      im.receiveShadow = true;
      im.frustumCulled = false;        // 우리가 인스턴스 단위로 직접 거른다
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      // 전체 목록을 따로 들고 있는다. instanceMatrix 는 "이번 프레임에 그릴 것"만 담는다
      const all = new Float32Array(n * 16);
      const cen = new Float32Array(n * 3);
      const rad = new Float32Array(n);
      const bs = lvl.geo.boundingSphere;
      for (let i = 0; i < n; i++) {
        const m = mats[lvl.idx[i]];
        m.toArray(all, i * 16);
        // 경계구는 지오메트리 것을 배치 행렬로 옮긴 것이다(Sphere.applyMatrix4 가
        // 축별 최대 배율로 반지름을 키워 준다). 거기에 여유를 더한다
        _sph.copy(bs).applyMatrix4(m);
        cen[i * 3] = _sph.center.x; cen[i * 3 + 1] = _sph.center.y; cen[i * 3 + 2] = _sph.center.z;
        rad[i] = _sph.radius + CULL_PAD;
        im.setMatrixAt(i, m);
      }
      im.count = n;
      im.instanceMatrix.needsUpdate = true;
      const rec = { kind, lod: lvl.tag, mesh: im, all, cen, rad, n,
                    nCam: n, nAll: n, tmp: new Int32Array(n), triOne };
      // 화면 패스 직전에 앞쪽 nCam 개로 줄인다(그림자 패스는 nAll 개를 그린 뒤다).
      im.onBeforeRender = () => { im.count = rec.nCam; };
      ROOT.add(im);
      INST.push(rec);
      tri += triOne * n;
    }
  }

  // ★컬링은 씬 렌더가 시작될 때 한 번 돈다. mesh.onBeforeRender 는 이미 늦다(맨 위 주석).
  hookScene(parent);

  if (dev) {
    console.log('[props] ' + list.length + '개 / 인스턴싱 '
      + INST.map(o => o.kind + (o.lod ? '.' + o.lod : '') + ' ' + o.n).join(', ')
      + ' / 수풀 메시 ' + BUSHES.length + '곳'
      + ' / LOD(고/저) ' + lodLog.join(', ') + ' [' + lodMode + ']'
      + (varLog.length ? ' / 변형 ' + varLog.join(', ') : '')
      + ' / 삼각형 ' + tri.toLocaleString());
  }
  return { instanced: INST.length, bushes: BUSHES.length, tri };
}

function pickMesh(gltf) {
  let found = null;
  gltf.scene.traverse(o => { if (!found && o.isMesh) found = o; });
  return found;
}

// ---------------------------------------------------------------------------
// 인스턴스 단위 절두체 컬링
// ---------------------------------------------------------------------------
// ★scene.onBeforeRender 에 문다. three 의 render() 순서가
//     scene.updateMatrixWorld -> camera.updateMatrixWorld -> **scene.onBeforeRender**
//     -> projectObject(여기서 instanceMatrix 를 GPU 로 올린다) -> 그림자 패스 -> 화면 패스
//   라서, 이 자리에서만 (가) 카메라·해 행렬이 최신이고 (나) 고친 목록이 같은 프레임에 올라간다.
//   mesh.onBeforeRender 에서 고치면 **다음 프레임에** 올라간다(예전 판이 그랬다).
function hookScene(parent) {
  let s = parent;
  while (s && s.parent) s = s.parent;
  if (!s || !s.isScene || s === SCENE) return;
  SCENE = s;
  const prev = s.onBeforeRender;
  s.onBeforeRender = function (renderer, scene, camera, target) {
    if (prev) prev.call(this, renderer, scene, camera, target);
    cullAll(scene, camera);
  };
}

function cullAll(scene, camera) {
  if (!INST.length) return;
  if (!culling) { for (const o of INST) showAll(o); return; }
  _pv.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
  _frustum.setFromProjectionMatrix(_pv);
  // 해의 그림자 상자. 화면 밖이라도 여기 걸리면 그림자가 화면 안으로 드리운다.
  // ★shadow.updateMatrices / getFrustum 은 그림자 패스가 바로 뒤에 부르는 것과 **같은 것**이다.
  //   여기서 먼저 불러 두면 같은 프레임 값을 그대로 쓴다(안 부르면 한 프레임 전 상자가 된다).
  //   updateProjectionMatrix 까지 부르는 이유: three 는 그림자맵을 **처음 만들 때만** 이걸
  //   부른다. 첫 프레임엔 아직 기본 상자(±5)라 우리가 먼저 맞춰야 한다.
  let sun = null;
  if (!SUN && sunTries < 120) { sunTries++; SUN = findSun(scene); }
  if (SUN && SUN.castShadow && SUN.visible && SUN.shadow) {
    SUN.shadow.camera.updateProjectionMatrix();
    SUN.shadow.updateMatrices(SUN);
    sun = SUN.shadow.getFrustum();
  }
  for (const o of INST) cullOne(o, sun);
}

function findSun(scene) {
  let best = null;
  scene.traverse(o => {
    if (o.isDirectionalLight && o.castShadow && (!best || o.intensity > best.intensity)) best = o;
  });
  return best;
}

function showAll(o) {
  if (o.nAll !== o.n) {
    o.mesh.instanceMatrix.array.set(o.all);
    o.mesh.instanceMatrix.needsUpdate = true;
    o.nCam = o.nAll = o.n;
  }
  o.mesh.count = o.n;
  o.mesh.visible = true;
}

// 한 버퍼에 [화면에 보이는 것] 다음 [그림자만 지는 것] 순으로 채운다.
//   그림자 패스 count = nAll,  화면 패스 count = nCam (mesh.onBeforeRender 가 줄인다)
function cullOne(o, sun) {
  const all = o.all, cen = o.cen, rad = o.rad, n = o.n, tmp = o.tmp;
  const dst = o.mesh.instanceMatrix.array;
  let k = 0, m = 0;
  for (let i = 0; i < n; i++) {
    _sph.center.set(cen[i * 3], cen[i * 3 + 1], cen[i * 3 + 2]);
    _sph.radius = rad[i];
    if (_frustum.intersectsSphere(_sph)) {
      // 앞에서부터 빈틈없이 채운다. 행렬 16개 복사라 조건을 따지는 것보다 그냥 쓰는 게 싸다
      dst.set(all.subarray(i * 16, i * 16 + 16), k * 16);
      k++;
    } else if (sun && sun.intersectsSphere(_sph)) {
      tmp[m++] = i;                     // 그림자 몫. 화면 목록 뒤에 붙인다
    }
  }
  o.nCam = k;
  for (let j = 0; j < m; j++) {
    const i = tmp[j];
    dst.set(all.subarray(i * 16, i * 16 + 16), k * 16);
    k++;
  }
  o.nAll = k;
  o.mesh.count = k;                     // 그림자 패스가 이 값으로 그린다
  o.mesh.visible = k > 0;               // 한 개도 없으면 두 패스 다 건너뛴다
  o.mesh.instanceMatrix.needsUpdate = true;
}

// ---------------------------------------------------------------------------
export function root() { return ROOT; }
export function setCulling(v) { culling = !!v; }

export const debug = {
  setCulling,
  // 지금 몇 개가 그려지고 있나(컬링 효과를 콘솔에서 바로 본다)
  //   drawn = 화면 패스, shadow = 그림자 패스(화면 밖 그림자 몫이 더 붙는다)
  drawn: () => INST.map(o => ({ kind: o.kind, lod: o.lod, drawn: o.nCam, shadow: o.nAll,
                                total: o.n, triOne: o.triOne, tri: o.nCam * o.triOne })),
  bushes: () => BUSHES.map(b => ({ id: b.id, n: b.n, hi: b.hi,
                                   tri: b.mesh.geometry.index.count / 3,
                                   // 화면 안인지(수풀은 three.js 가 메시 단위로 거른다)
                                   vis: b.mesh.visible })),
  // 화면에 실제로 들어간 인스턴싱 삼각형
  totalTri: () => INST.reduce((a, o) => a + o.nCam * o.triOne, 0),
  // 그림자 패스가 그리는 인스턴싱 삼각형(화면 밖 그림자 몫 포함)
  shadowTri: () => INST.reduce((a, o) => a + o.nAll * o.triOne, 0),
  // 수풀까지 더한 씬 전체 소품 삼각형(컬링 전)
  sceneTri: () => INST.reduce((a, o) => a + o.n * o.triOne, 0)
    + BUSHES.reduce((a, b) => a + b.mesh.geometry.index.count / 3, 0),
};
