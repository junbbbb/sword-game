// ---------------------------------------------------------------------------
// web/nav.js — 요괴가 벽을 돌아 나오게 하는 최소한의 길찾기
//
// 문제: 요괴 추격이 "플레이어 쪽으로 직진"뿐이라 바위에 막히면 벽을 타고 미끄러지다가
//      리쉬에 걸려 귀환한다. 벽 뒤에 서 있으면 아무도 안 온다 = 숨을 필요가 없다.
//
// 설계 원칙
//  1. **개체마다 A* 를 돌리지 않는다.** 쫓는 대상이 플레이어 하나뿐이라, 플레이어에서
//     바깥으로 BFS 를 한 번 돌려 "이 칸에서 다음에 갈 칸"을 통째로 적어두면
//     40마리가 그걸 **배열 한 번 읽는 것**으로 공유한다(흐름장 / flow field).
//     A* 20개 = 매 프레임 수만 번. 흐름장 = 플레이어가 칸을 넘을 때만 3,600칸 한 번.
//  2. **트인 곳에서는 길찾기를 안 쓴다.** 시야가 트였으면 그냥 직진이 제일 자연스럽다
//     (칸 중심을 따라가면 트인 마당에서도 지그재그로 걷는다). 시야 검사는 0.25초에
//     한 번, 개체마다 시간을 어긋나게 돌린다.
//  3. **격자는 ASCII 가 아니라 콜라이더에서 뽑는다.** level1.json 의 grid[] 는 30x30
//     (한 칸 3.2m)이라 요괴 몸(반경 0.34)에 비해 너무 굵다. 한 칸이 3.2m 면 바위
//     하나 때문에 통로 전체가 막힌 것으로 읽힌다. 그래서 1.6m 격자를 새로 만들고
//     칸마다 level.js 의 blocked() 로 직접 물어본다(= 렌더·충돌과 같은 진실).
//     ASCII 격자는 검증용으로만 대조한다(debug.compareAscii).
//
// 좌표계는 level.js 와 같다(three.js. X=동, Z=남).
// ---------------------------------------------------------------------------
// ★main.js·enemy.js 와 **같은 URL** 로 불러야 같은 맵 인스턴스를 본다(캐시 버스팅 쿼리).
const LV = await import('./level.js' + location.search);

// ★부팅 로그는 ?dev 에서만 찍는다.
// 평상 콘솔이 비어 있어야 진짜 경고(출력 중간의 warn·error)가 눈에 들어온다.
//   매 부팅마다 한 줄씩 깔리면 그게 기준선이 되어 사고가 그 옆에 묻힌다.
// 망가진 맵(build 실패)은 ?dev 없이도 그대로 warn 한다 — 그건 상황 보고가 아니라 고장이다.
const DEV = typeof location !== 'undefined' && location.search.includes('dev');

// 한 칸 1.6m.
//  · 요괴 몸이 반경 0.34 이라 1.6m 면 한 칸에 몸이 두 개 들어간다 = 문·통로를 못 지나갈
//    만큼 굵지 않다.
//  · 96m 맵이 60x60 = 3,600칸. BFS 한 번이 3,600칸 x 이웃 8 = 2.9만 번인데,
//    플레이어가 칸을 넘을 때만(달리기 3.2m/s 기준 초당 두 번) 돈다.
//  · 더 잘게(0.8m) 쪼개면 칸이 14,400개가 되고 얻는 건 거의 없다. 맵의 바위·기둥이
//    전부 1.5m 이상짜리라 1.6m 격자로 이미 다 잡힌다.
const CELL = 1.6;

// 칸이 "설 수 있는 자리"인지 물을 때 쓰는 반경.
// ★요괴 반경(0.34)보다 크게 잡는다. 칸 **중심 한 점**만 검사하기 때문에, 몸 반경
//   그대로 물으면 중심은 비었지만 몸이 벽에 걸치는 칸이 통과돼 버린다. 0.55 면
//   칸 중심에서 반 칸(0.8m) 안쪽까지 비어 있어야 통과라, 실제로 지나갈 수 있는 칸만 남는다.
const CELL_R = 0.55;

// 시야 검사(직진해도 되는가)에 쓰는 반경과 간격.
// ★반경을 요괴 몸(0.34)보다 살짝 크게 둬야 "보이니까 직진했는데 어깨가 걸린다"가 안 난다.
//   간격은 반경의 두 배보다 좁아야 검사 원들이 겹쳐서 얇은 벽이 사이로 새지 않는다.
const LOS_R = 0.42;
const LOS_STEP = 0.55;            // 0.55 < 2*0.42 = 0.84 이므로 원이 겹친다
const LOS_MAX = 15.0;             // 리쉬(16m)보다 조금 짧게. 그보다 멀면 어차피 포기한다

let GW = 0, GH = 0, X0 = 0, Z0 = 0;
let walk = null;                  // Uint8Array. 1 = 설 수 있는 칸
let next = null;                  // Int32Array. 이 칸에서 플레이어 쪽으로 한 칸 = next[c]
let seen = null;                  // Int32Array. BFS 방문 표식(세대 번호를 적어 초기화를 없앤다)
let gen = 0;                      // BFS 세대. 배열을 매번 0으로 지우지 않으려고 쓴다
let queue = null;                 // Int32Array. BFS 대기열(고정 크기, 매번 재사용)
let srcCell = -1;                 // 지금 흐름장의 출발 칸(= 플레이어가 서 있는 칸)
let builds = 0;                   // 흐름장을 몇 번 다시 깔았는지(성능 검증용)
let lastMs = 0;                   // 마지막 BFS 소요 시간(ms)

export function ready() { return !!walk; }
export function cellSize() { return CELL; }

// ---------------------------------------------------------------------------
// 격자 만들기 (맵 로드 후 한 번)
// ---------------------------------------------------------------------------
export function build() {
  const d = LV.data();
  if (!d) { console.warn('[nav] 맵이 아직 없다'); return false; }
  const b = d.bounds;
  X0 = b.minX; Z0 = b.minZ;
  GW = Math.ceil((b.maxX - b.minX) / CELL);
  GH = Math.ceil((b.maxZ - b.minZ) / CELL);
  const n = GW * GH;
  walk = new Uint8Array(n);
  next = new Int32Array(n);
  seen = new Int32Array(n);
  queue = new Int32Array(n);
  let open = 0;
  for (let r = 0; r < GH; r++) {
    for (let c = 0; c < GW; c++) {
      const x = X0 + (c + 0.5) * CELL, z = Z0 + (r + 0.5) * CELL;
      const ok = !LV.blocked(x, z, CELL_R) ? 1 : 0;
      walk[r * GW + c] = ok;
      open += ok;
    }
  }
  gen = 0;
  srcCell = -1;
  if (DEV) console.log('[nav] 격자 ' + GW + 'x' + GH + ' (' + CELL + 'm), 걸을 수 있는 칸 '
    + open + '/' + n + ' = ' + (open / n * 100).toFixed(0) + '%');
  return true;
}

const clampi = (v, a, b) => (v < a ? a : (v > b ? b : v));

export function cellAt(x, z) {
  if (!walk) return -1;
  const c = clampi(Math.floor((x - X0) / CELL), 0, GW - 1);
  const r = clampi(Math.floor((z - Z0) / CELL), 0, GH - 1);
  return r * GW + c;
}
export function centerX(ci) { return X0 + ((ci % GW) + 0.5) * CELL; }
export function centerZ(ci) { return Z0 + (((ci / GW) | 0) + 0.5) * CELL; }

// 벽 속에 있는 칸이면 가장 가까운 걸을 수 있는 칸으로 옮긴다.
// ★플레이어는 반경 0.35 로 서 있고 격자는 0.55 로 판정하므로, 벽에 붙어 서면
//   자기 칸이 '막힘'으로 나온다. 그대로 BFS 를 돌리면 흐름장이 통째로 비어서
//   요괴가 아무도 못 온다. 반드시 근처 칸으로 흘려보낼 것.
function nearestOpen(ci) {
  if (ci < 0) return -1;
  if (walk[ci]) return ci;
  const c0 = ci % GW, r0 = (ci / GW) | 0;
  for (let rad = 1; rad <= 3; rad++) {
    for (let dr = -rad; dr <= rad; dr++) {
      for (let dc = -rad; dc <= rad; dc++) {
        if (Math.abs(dr) !== rad && Math.abs(dc) !== rad) continue;   // 테두리만
        const c = c0 + dc, r = r0 + dr;
        if (c < 0 || r < 0 || c >= GW || r >= GH) continue;
        const k = r * GW + c;
        if (walk[k]) return k;
      }
    }
  }
  return -1;
}

// ---------------------------------------------------------------------------
// 흐름장 (플레이어에서 바깥으로 BFS)
// ---------------------------------------------------------------------------
// next[c] = c 에서 한 칸 갔을 때 플레이어에 더 가까워지는 칸.
// ★부모를 적는 방향이 헷갈리기 쉽다. BFS 는 플레이어에서 **퍼져 나가므로**,
//   이웃 n 을 c 에서 처음 만났다면 c 가 n 보다 플레이어에 가깝다 = next[n] = c 다.
export function rebuild(px, pz) {
  if (!walk) return false;
  const src = nearestOpen(cellAt(px, pz));
  if (src < 0) return false;
  const t0 = performance.now();
  gen++;
  let head = 0, tail = 0;
  queue[tail++] = src;
  seen[src] = gen;
  next[src] = -1;
  while (head < tail) {
    const c = queue[head++];
    const cx = c % GW, cz = (c / GW) | 0;
    for (let i = 0; i < 8; i++) {
      const dx = NB[i * 2], dz = NB[i * 2 + 1];
      const nx = cx + dx, nz = cz + dz;
      if (nx < 0 || nz < 0 || nx >= GW || nz >= GH) continue;
      const nk = nz * GW + nx;
      if (seen[nk] === gen || !walk[nk]) continue;
      // ★대각선으로 모서리를 잘라 지나가지 못하게 막는다. 이걸 빼면 바위 두 개가
      //   대각으로 붙은 틈으로 경로가 나고, 실제로 걸으면 몸이 껴서 못 지나간다.
      if (dx && dz && (!walk[cz * GW + nx] || !walk[nz * GW + cx])) continue;
      seen[nk] = gen;
      next[nk] = c;
      queue[tail++] = nk;
    }
  }
  srcCell = src;
  builds++;
  lastMs = performance.now() - t0;
  return true;
}
// 8방향 이웃(dx, dz)
const NB = new Int8Array([1, 0, -1, 0, 0, 1, 0, -1, 1, 1, 1, -1, -1, 1, -1, -1]);

// 플레이어가 칸을 넘었는가(= 흐름장을 다시 깔아야 하는가)
export function needRebuild(px, pz) {
  if (!walk) return false;
  return nearestOpen(cellAt(px, pz)) !== srcCell;
}
export function source() { return srcCell; }

// 이 칸에서 다음에 갈 칸. 못 가는 자리면 -1.
export function step(ci) {
  if (!walk || ci < 0 || seen[ci] !== gen) return -1;
  return next[ci];
}

// ---------------------------------------------------------------------------
// 시야 (직진해도 되는가)
// ---------------------------------------------------------------------------
// 선분을 따라 원을 겹쳐 놓고 하나라도 벽에 걸리면 막힌 것으로 본다.
// ★격자가 아니라 **콜라이더**에 직접 묻는다. 격자로 재면 1.6m 해상도라
//   "칸은 비었는데 실제로는 바위가 걸친" 경우를 놓친다.
export function los(ax, az, bx, bz) {
  const dx = bx - ax, dz = bz - az;
  const d = Math.hypot(dx, dz);
  if (d > LOS_MAX) return false;
  if (d < 1e-4) return true;
  const n = Math.ceil(d / LOS_STEP);
  const ux = dx / n, uz = dz / n;
  for (let i = 1; i <= n; i++) {
    if (LV.blocked(ax + ux * i, az + uz * i, LOS_R)) return false;
  }
  return true;
}

// ---------------------------------------------------------------------------
// 경로에서 조준점 뽑기
// ---------------------------------------------------------------------------
// 흐름장을 최대 hops 칸 따라가면서, **내가 직접 볼 수 있는 가장 먼 칸**을 고른다
// (string pulling). 이걸 안 하면 칸 중심을 하나씩 밟느라 계단처럼 걷는다.
const _t = { x: 0, z: 0, ok: false, hops: 0 };
export function target(x, z, hops) {
  _t.ok = false; _t.hops = 0;
  if (!walk) return _t;
  let ci = seen[cellAt(x, z)] === gen ? cellAt(x, z) : nearestOpen(cellAt(x, z));
  if (ci < 0 || seen[ci] !== gen) return _t;
  const H = hops || 6;
  let bestX = 0, bestZ = 0, bestN = 0;
  for (let i = 0; i < H; i++) {
    const nx = next[ci];
    if (nx < 0) break;                       // 출발 칸(플레이어)에 닿았다
    ci = nx;
    const cx = centerX(ci), cz = centerZ(ci);
    if (los(x, z, cx, cz)) { bestX = cx; bestZ = cz; bestN = i + 1; }
    else if (bestN) break;                   // 한 번 보이다가 안 보이면 거기까지가 최선
  }
  if (!bestN) return _t;
  _t.x = bestX; _t.z = bestZ; _t.ok = true; _t.hops = bestN;
  return _t;
}

// ---------------------------------------------------------------------------
// 검증 창구
// ---------------------------------------------------------------------------
export const debug = {
  size: () => ({ gw: GW, gh: GH, cell: CELL,
                 open: walk ? walk.reduce((s, v) => s + v, 0) : 0, n: GW * GH }),
  // 흐름장이 몇 번 깔렸고 한 번에 얼마나 걸리는지(성능 근거)
  stats: () => ({ builds, lastMs: +lastMs.toFixed(3), src: srcCell }),
  reachable: (x, z) => seen[cellAt(x, z)] === gen,
  // 한 지점에서 플레이어까지 흐름장을 따라가 본다(막히면 짧게 끊긴다)
  trace(x, z, max) {
    const out = [];
    let ci = cellAt(x, z);
    if (seen[ci] !== gen) ci = nearestOpen(ci);
    for (let i = 0; i < (max || 60); i++) {
      if (ci < 0 || seen[ci] !== gen) break;
      out.push([+centerX(ci).toFixed(1), +centerZ(ci).toFixed(1)]);
      const nx = next[ci];
      if (nx < 0) break;
      ci = nx;
    }
    return out;
  },
  // ★level1.json 의 30x30 ASCII 격자와 대조한다. 완전히 같을 수는 없다
  //   (ASCII 는 3.2m 한 칸을 한 글자로 뭉갠 것이고 이쪽은 1.6m 라 더 곱다).
  //   "ASCII 가 길이라는데 여기는 통째로 막힘"인 칸이 있으면 그게 사고다.
  compareAscii() {
    const d = LV.data();
    if (!d || !d.grid) return null;
    const bad = [];
    for (let r = 0; r < d.grid.length; r++) {
      const row = d.grid[r];
      for (let c = 0; c < row.length; c++) {
        const ch = row[c];
        if (ch === '#') continue;                       // 막는 지형은 대조 대상이 아니다
        const x = d.bounds.minX + (c + 0.5) * d.cell;
        const z = d.bounds.minZ + (r + 0.5) * d.cell;
        // 3.2m 칸 하나에 1.6m 칸 네 개가 들어간다. 넷 다 막혔으면 문제다.
        let open = 0;
        for (const ox of [-0.8, 0.8]) for (const oz of [-0.8, 0.8]) {
          const k = cellAt(x + ox, z + oz);
          if (k >= 0 && walk[k]) open++;
        }
        if (!open) bad.push({ cell: [c, r], ch, at: [+x.toFixed(1), +z.toFixed(1)] });
      }
    }
    return { asciiOpenButNavBlocked: bad.length, list: bad.slice(0, 12) };
  },
};
