// 자산 그리드를 "작업 id" 로 읽는다. 썸네일 URL 에 taskId 가 박혀 있어서 이게 유일한 신원이다
// (카드 인덱스는 새 작업이 위로 끼어들면 밀린다 - 인덱스로 물건을 가리키지 말 것).
//   node tools/meshy_pipe/mp_map.mjs [개수]
import { attach } from './mp_lib.mjs';

const N = Number(process.argv[2] || 20);
const { b, page } = await attach();
const rows = await page.evaluate((n) => {
  return [...document.querySelectorAll('[data-testid=assets-card]')].slice(0, n).map((c, i) => {
    const img = c.querySelector('img');
    const m = img && img.src.match(/tasks\/([0-9a-f-]{36})\//);
    const txt = (c.innerText || '').replace(/\s+/g, ' ').trim();
    const sel = c.className.includes('ring') || (c.querySelector('[class*=border-accent]') ? 'sel' : '');
    return { i, task: m ? m[1] : null, txt, sel };
  });
}, N);
for (const r of rows) console.log(`${String(r.i).padStart(2)} ${r.task || '(썸네일 없음 - 진행 중)'} "${r.txt}" ${r.sel || ''}`);
await b.close();
