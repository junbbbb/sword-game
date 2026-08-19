// 궁수 활 검증용 독립 크롬. 게임 카메라 그대로 찍는다.
//   node tools/bow_shot.mjs [출력폴더] [캐시버스터]
//
// ★공유 MCP 브라우저(Playwright MCP)를 쓰면 안 된다 - 메인이 같은 창으로 작업 중이다.
//   여기서는 launch() 로 **새 크롬**을 띄운다(프로필도 임시).
// ★로컬 python http.server 는 Cache-Control 을 안 준다. 브라우저가 옛 glb 를 물기 때문에
//   주소에 ?cb= 를 매번 바꿔 붙인다.
// ★window.__slow = 0 은 정지가 아니다. main.js:5355 가 (window.__slow || 1) 로 읽어
//   0 이 1 로 되살아난다. 느리게 보려면 작은 양수를 넣는다.
import { chromium } from '/Users/lbj/Documents/real-estate-agent/node_modules/playwright/index.mjs';
import fs from 'node:fs';

const OUT = process.argv[2] || '/Users/lbj/Documents/gameproject/renders/v99_wave21_bow/game';
const CB = process.argv[3] || String(Date.now());
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const browser = await chromium.launch({ headless: false, args: ['--window-size=1360,900'] });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
page.on('console', m => { const t = m.text(); if (/error|Error|실패/.test(t)) console.log('  [콘솔]', t); });
page.on('pageerror', e => console.log('  [페이지오류]', e.message));

const url = `http://localhost:8777/?map=field&char=archer&cb=${CB}`;
console.log('열기:', url);
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120000 });

// 로딩 화면이 사라질 때까지(= 캐릭터 glb 가 들어올 때까지) 기다린다
await page.waitForFunction(() => {
  const el = document.getElementById('loading') || document.querySelector('.loading, #load');
  return !el || el.style.display === 'none';
}, { timeout: 120000 }).catch(() => console.log('  (로딩 감지 실패 - 그냥 진행)'));
await sleep(2500);

// 활이 실제로 씬에 들어왔는지 이름으로 확인한다
const found = await page.evaluate(() => {
  const out = [];
  if (window.__fx && window.__fx.scene) {
    window.__fx.scene.traverse(o => { if (o.isMesh) out.push(o.name); });
  }
  return out;
});
if (found.length) console.log('  씬 메시:', found.filter(n => /BW_|char/.test(n)));

await page.click('canvas', { position: { x: 640, y: 400 } }).catch(() => {});

async function shot(name) {
  await page.screenshot({ path: `${OUT}/${name}.png` });
  console.log('  찍음', name);
}

// ── 1) 대기 자세 ──
await shot('01_idle');

// ── 2) 여덟 방향으로 돌려 가며 대기 자세(활이 어느 각도에서 어떻게 읽히나) ──
const DIRS = [['KeyW', 'n'], ['KeyD', 'e'], ['KeyS', 's'], ['KeyA', 'w']];
for (const [k, tag] of DIRS) {
  await page.keyboard.down(k);
  await sleep(700);
  await shot(`02_walk_${tag}`);
  await page.keyboard.up(k);
  await sleep(500);
  await shot(`03_idle_${tag}`);
}

// ── 3) 달리기 ──
await page.keyboard.down('ShiftLeft');
await page.keyboard.down('KeyW');
await sleep(900);
await shot('04_run');
await page.keyboard.up('KeyW');
await page.keyboard.up('ShiftLeft');
await sleep(600);

// ── 4) 점프 ──
await page.keyboard.press('Space');
await sleep(280);
await shot('05_jump');
await sleep(900);

// ── 5) 쏘기: 게임 시계를 20배 늦춰(0.05) 만작 프레임을 놓치지 않게 연사 촬영 ──
for (const [az, tag] of [['KeyS', 'toward'], ['KeyD', 'side'], ['KeyW', 'away']]) {
  await page.keyboard.down(az);
  await sleep(450);
  await page.keyboard.up(az);
  await sleep(400);
  await page.evaluate(() => { window.__slow = 0.05; });
  await page.keyboard.press('KeyZ');
  for (let i = 0; i < 10; i++) {
    await sleep(700);
    await shot(`06_shoot_${tag}_${String(i).padStart(2, '0')}`);
  }
  await page.evaluate(() => { window.__slow = 1; });
  await sleep(700);
}

// ── 6) 정지 상태에서 만작 근처를 크게 ──
await page.evaluate(() => { window.__slow = 0.02; });
await page.keyboard.press('KeyZ');
await sleep(3000);
await shot('07_draw_freeze');
await page.evaluate(() => { window.__slow = 1e-6; });
await sleep(400);
await shot('08_draw_stop');

await browser.close();
console.log('완료:', OUT);
