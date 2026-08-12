// 소품별 카드 썸네일(서버가 구운 최종 렌더)을 한 장씩 저장한다 - 눈으로 신원을 확인하는 판정지용.
//   node tools/meshy_pipe/mp_thumbs.mjs [파일접두어] [--max-tris N]
//   접두어를 주면 thumb<접두어>_<이름>.png 로 저장한다(저폴리판 판정지용).
// 카드를 고른 뒤 뷰어 하단의 원본 이미지 id 로 신원을 확정하고, 그 카드만 잘라 찍는다.
import { readFileSync } from 'fs';
import { attach, closeModal, viewerSource, sleep, stamp, LOG_DIR } from './mp_lib.mjs';

const ids = JSON.parse(readFileSync(new URL('./mp_ids.json', import.meta.url), 'utf8'));
const byImage = {};
for (const [n, v] of Object.entries(ids)) if (v && v.image) byImage[v.image] = n;

const PRE = (process.argv[2] && !process.argv[2].startsWith('--')) ? process.argv[2] : '';
const mi = process.argv.indexOf('--max-tris');
const MAXTRIS = mi >= 0 ? Number(process.argv[mi + 1]) : 0;

const { b, page } = await attach();
await closeModal(page);
await page.keyboard.press('Escape'); await sleep(600);
await page.evaluate(() => {
  const t = document.querySelector('[data-testid=assets-phase-textured-btn]');
  if (t && t.getAttribute('aria-checked') !== 'true') t.click();
});
await sleep(2500);

const seen = new Set();
for (let i = 0; i < 20 && seen.size < 9; i++) {
  await page.evaluate((idx) => {
    const c = document.querySelectorAll('[data-testid=assets-card]')[idx];
    if (c) c.scrollIntoView({ block: 'center', behavior: 'instant' });
  }, i);
  await sleep(1000);
  const rect = await page.evaluate((idx) => {
    const c = document.querySelectorAll('[data-testid=assets-card]')[idx];
    if (!c) return null;
    const r = c.getBoundingClientRect();
    if (r.top < 60 || r.bottom > 1000) return null;
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }, i);
  if (!rect) continue;
  await page.mouse.move(rect.x, rect.y); await sleep(300);
  await page.mouse.click(rect.x, rect.y);
  await sleep(2500);
  const src = await viewerSource(page);
  const name = byImage[src];
  if (!name || seen.has(name)) continue;
  if (MAXTRIS) {
    const tris = await page.evaluate(() => {
      const t = (document.querySelector('[data-testid=viewer-area]')?.innerText || '').replace(/\s+/g, ' ');
      const m = t.match(/면 ([\d,]+)/);
      return m ? Number(m[1].replace(/,/g, '')) : null;
    });
    if (!tris || tris > MAXTRIS) continue;
  }
  const el = page.locator('[data-testid=assets-card]').nth(i);
  await el.screenshot({ path: LOG_DIR + '/thumb' + PRE + '_' + name + '.png' });
  console.log(`[${stamp()}] thumb${PRE}_${name}.png (카드 ${i})`);
  seen.add(name);
}
console.log('찍은 것 ' + seen.size + '/9');
await b.close();
