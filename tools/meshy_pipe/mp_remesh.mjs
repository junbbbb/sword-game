// 텍스처까지 끝난 자산을 저폴리로 리메시한다(크레딧 0, 1분).
//   node tools/meshy_pipe/mp_remesh.mjs <소품이름> [3K|10K|30K|100K]
// ★리메시는 공짜다. 울트라 모드가 3백만 삼각형을 뱉으므로 게임에 넣으려면 어차피 줄여야 하고,
//   Meshy 가 직접 줄이면 UV·텍스처를 자기가 옮겨 준다(블렌더 데시메이트보다 안전하다).
//   다만 "정말 텍스처가 따라왔는지"는 받은 glb 를 열어 확인할 것(mp_glbinfo.mjs).
import { readFileSync } from 'fs';
import { attach, credits, closeModal, viewerSource, sleep, stamp } from './mp_lib.mjs';

const ARG = process.argv[2];
const TARGET = process.argv[3] || '3K';
if (!ARG) { console.log('소품 이름을 다오'); process.exit(1); }
const ids = JSON.parse(readFileSync(new URL('./mp_ids.json', import.meta.url), 'utf8'));
const want = ids[ARG] && ids[ARG].image;

const { b, page } = await attach();
const die = async (m, c) => { console.log('★' + m); await b.close(); process.exit(c); };

await closeModal(page);
await page.keyboard.press('Escape'); await sleep(800);

// 텍스처 단계 카드들 중에서 이 소품을 찾는다(리메시는 텍스처 입은 것에 걸어야 의미가 있다)
await page.evaluate(() => {
  const t = document.querySelector('[data-testid=assets-phase-textured-btn]');
  if (t && t.getAttribute('aria-checked') !== 'true') t.click();
});
await sleep(2500);

let found = null;
for (let i = 0; i < 20 && !found; i++) {
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
  if (src !== want) continue;
  // ★같은 소품의 "이미 리메시된 카드"를 또 리메시하지 않는다(폴리로 가른다)
  const tris = await page.evaluate(() => {
    const t = (document.querySelector('[data-testid=viewer-area]')?.innerText || '').replace(/\s+/g, ' ');
    const m = t.match(/면 ([\d,]+)/);
    return m ? Number(m[1].replace(/,/g, '')) : null;
  });
  if (!tris || tris < 500000) { console.log(`  카드 ${i}: 폴리 ${tris} - 원본 풀디테일이 아니다, 계속 찾는다`); continue; }
  found = i;
}
if (found === null) await die(`${ARG} 의 텍스처 자산을 못 찾았다`, 3);
console.log(`[${stamp()}] ${ARG} 텍스처 자산 선택(카드 ${found})`);

const c0 = await credits(page);
await page.click('[data-testid=viewer-remesh-btn]');
await sleep(2000);

const st = await page.evaluate((target) => {
  const panel = [...document.querySelectorAll('div')].find(d => (d.innerText || '').includes('폴리곤 수') && d.getBoundingClientRect().width < 520);
  if (!panel) return { err: '리메시 패널 못 찾음' };
  const pick = (txt) => [...panel.querySelectorAll('button')].find(x => (x.innerText || '').trim() === txt);
  const poly = pick(target), tri = pick('삼각형 면'), ok = pick('확인하다');
  const rect = (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; };
  return {
    text: (panel.innerText || '').replace(/\s+/g, ' ').slice(0, 120),
    poly: poly ? rect(poly) : null, tri: tri ? rect(tri) : null, ok: ok ? rect(ok) : null,
  };
}, TARGET);
if (st.err || !st.poly || !st.tri || !st.ok) await die('리메시 패널이 예상과 다르다: ' + JSON.stringify(st), 4);
console.log('  패널: ' + st.text);

await page.mouse.click(st.poly.x, st.poly.y); await sleep(600);
await page.mouse.click(st.tri.x, st.tri.y); await sleep(600);
const okH = await page.evaluateHandle(() => {
  const panel = [...document.querySelectorAll('div')].find(d => (d.innerText || '').includes('폴리곤 수') && d.getBoundingClientRect().width < 520);
  return panel ? [...panel.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '확인하다') : null;
});
await okH.asElement().click();
console.log(`[${stamp()}] 리메시 접수(${TARGET}, 삼각형) · 크레딧 ${c0} (0 이어야 정상)`);
await sleep(6000);
console.log(`[${stamp()}] 접수 후 크레딧 ${await credits(page)}`);
await b.close();
