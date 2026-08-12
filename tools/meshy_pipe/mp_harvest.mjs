// 텍스처가 끝난 자산들을 훑어 소품 이름을 붙여 내려받는다.
//   node tools/meshy_pipe/mp_harvest.mjs [훑을카드수] [--suffix _3k] [--max-tris 50000] [--all]
//   --suffix    파일 이름 뒤에 붙인다(저폴리 리메시본을 따로 받을 때)
//   --max-tris  뷰어가 말하는 삼각형 수가 이 값보다 크면 건너뛴다(리메시본만 고르는 체)
//   --all       그리드 필터를 '텍스처'가 아니라 '전체'로 둔다
//
// ★두 가지 함정을 넘는다.
//  ①뷰어의 다운로드 버튼은 "무텍스처(generate) 버전"을 준다. 텍스처 입은 파일은
//    **카드의 ⋮ 메뉴 → 다운로드** 라야 나온다(파일명이 _texture 로 끝나는지가 증거).
//  ②어느 카드가 어느 소품인지는 카드만 봐서는 모른다. 카드를 고르면 뷰어 하단 썸네일에
//    원본 콘셉트 이미지 id 가 뜬다 - mp_ids.json 의 image 와 맞춰 신원을 확정한다.
import fs from 'fs';
import os from 'os';
import { readFileSync, existsSync, statSync, openSync, readSync, closeSync, mkdirSync, copyFileSync, unlinkSync } from 'fs';
import { attach, closeModal, viewerSource, setDownloadDir, waitNewFile, sleep, stamp, shot, OUT_DIR } from './mp_lib.mjs';

// 크롬이 파일을 떨굴 폴더(우리가 직접 지정한다. 세션 임시폴더에 의존하지 않는다)
const DROP = os.tmpdir() + '/meshy_drop';
mkdirSync(DROP, { recursive: true });

const argv = process.argv.slice(2);
const MAX = Number(argv.find(a => /^\d+$/.test(a)) || 20);
const flag = (k, d = null) => { const i = argv.indexOf(k); return i >= 0 ? (argv[i + 1] ?? true) : d; };
const SUFFIX = flag('--suffix', '');
const MAXTRIS = Number(flag('--max-tris', 0)) || 0;
const ALLPHASE = argv.includes('--all');
const ids = JSON.parse(readFileSync(new URL('./mp_ids.json', import.meta.url), 'utf8'));
const byImage = {};
for (const [name, v] of Object.entries(ids)) if (v && v.image) byImage[v.image] = name;

const { b, page } = await attach();
await setDownloadDir(page, DROP);
await closeModal(page);
await page.keyboard.press('Escape'); await sleep(800);

// 볼 단계 고르기
await page.evaluate((all) => {
  const t = document.querySelector(all ? '[data-testid=assets-phase-all-btn]' : '[data-testid=assets-phase-textured-btn]');
  if (t && t.getAttribute('aria-checked') !== 'true') t.click();
}, ALLPHASE);
await sleep(2500);

const done = new Set();
for (const name of Object.keys(ids)) {
  if (name.startsWith('_')) continue;
  if (existsSync(OUT_DIR + '/' + name + SUFFIX + '.glb')) done.add(name);
}
console.log(`[${stamp()}] 이미 받은 것: ${[...done].join(', ') || '없음'}`);

for (let i = 0; i < MAX; i++) {
  if (done.size >= 9) break;
  // 카드 고르기(진짜 클릭)
  const box = await page.evaluate((idx) => {
    const cards = document.querySelectorAll('[data-testid=assets-card]');
    if (idx >= cards.length) return null;
    const c = cards[idx];
    c.scrollIntoView({ block: 'center', behavior: 'instant' });
    return null;
  }, i);
  await sleep(1200);
  const rect = await page.evaluate((idx) => {
    const c = document.querySelectorAll('[data-testid=assets-card]')[idx];
    if (!c) return null;
    if (/\d+\s*%/.test(c.innerText || '')) return { busy: true };   // 아직 굽는 중인 카드
    const r = c.getBoundingClientRect();
    if (r.top < 60 || r.bottom > 1000) return null;
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }, i);
  if (!rect) { console.log(`  카드 ${i}: 화면 밖`); continue; }
  if (rect.busy) { console.log(`  카드 ${i}: 아직 진행 중 - 건너뜀`); continue; }
  await page.mouse.move(rect.x, rect.y); await sleep(400);
  await page.mouse.click(rect.x, rect.y);
  await sleep(3000);

  const src = await viewerSource(page);
  const name = byImage[src];
  if (!name) { console.log(`  카드 ${i}: 우리 소품 아님(${src})`); continue; }
  if (done.has(name)) { console.log(`  카드 ${i}: ${name} 이미 받음`); continue; }

  // 폴리 체: 리메시본만 고르고 싶을 때(뷰어가 말하는 삼각형 수로 가른다)
  if (MAXTRIS) {
    const tris = await page.evaluate(() => {
      const t = (document.querySelector('[data-testid=viewer-area]')?.innerText || '').replace(/\s+/g, ' ');
      const m = t.match(/면 ([\d,]+)/);
      return m ? Number(m[1].replace(/,/g, '')) : null;
    });
    if (!tris || tris > MAXTRIS) { console.log(`  카드 ${i}: ${name} 폴리 ${tris} - 이 판에서 찾는 물건이 아니다`); continue; }
    console.log(`  카드 ${i}: ${name} 폴리 ${tris}`);
  }

  if (!SUFFIX) await shot(page, 'view_' + name);

  // ⋮ 메뉴 → 다운로드
  const menuBtn = await page.evaluateHandle((idx) => {
    const c = document.querySelectorAll('[data-testid=assets-card]')[idx];
    return c ? c.querySelector('[data-testid=assets-hover-menu-btn]') : null;
  }, i);
  const mEl = menuBtn.asElement();
  if (!mEl) { console.log(`  카드 ${i}: 메뉴 버튼 없음`); continue; }
  await mEl.click({ force: true });
  await sleep(1200);
  const item = page.locator('[role=menuitem]', { hasText: /^다운로드$/ }).first();
  await item.click();
  await sleep(2000);

  // 대화상자: 포맷 glb 확인 후 다운로드
  const fmt = await page.evaluate(() => {
    const d = [...document.querySelectorAll('[role=dialog]')].pop();
    const cb = d && [...d.querySelectorAll('[role=combobox]')].find(x => /^(glb|fbx|obj|usdz|stl|blend|3mf|dxf)$/i.test((x.innerText || '').trim()));
    return cb ? (cb.innerText || '').trim() : null;
  });
  if (fmt !== 'glb') { console.log(`  ★${name}: 포맷이 glb 가 아니다(${fmt})`); await page.keyboard.press('Escape'); continue; }

  const before = new Set(fs.readdirSync(DROP));
  const dlBtn = await page.evaluateHandle(() => {
    const d = [...document.querySelectorAll('[role=dialog]')].pop();
    return d ? [...d.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '다운로드') : null;
  });
  await dlBtn.asElement().click();
  const got = await waitNewFile(fs, DROP, before, 300000);
  const out = OUT_DIR + '/' + name + SUFFIX + '.glb';
  if (!got) {
    console.log(`  ★${name} 내려받기 실패(파일이 안 떨어졌다)`);
    await page.keyboard.press('Escape'); await sleep(1000);
    continue;
  }
  const suggested = got.split('/').pop();
  copyFileSync(got, out); unlinkSync(got);
  const sz = statSync(out).size;

  // 매직바이트 + 텍스처 유무
  const fd = openSync(out, 'r'); const buf = Buffer.alloc(20); readSync(fd, buf, 0, 20, 0); closeSync(fd);
  const magic = buf.toString('ascii', 0, 4);
  console.log(`[${stamp()}] ${name} ← ${suggested} (${(sz / 1048576).toFixed(1)}MB, 머리 ${magic})`);
  if (!/_texture\.glb$/.test(suggested)) console.log(`  ★${name}: 파일명이 _texture 가 아니다 - 무텍스처일 수 있다`);
  done.add(name);
  await page.keyboard.press('Escape'); await sleep(800);
}

console.log(`[${stamp()}] 받은 소품 ${done.size}/9: ${[...done].join(', ')}`);
await b.close();
