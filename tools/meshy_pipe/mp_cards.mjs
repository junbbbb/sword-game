// 오른쪽 자산 그리드의 카드들을 순서대로 읽는다(제목·상태·진행률·썸네일).
// ★API 토큰은 손대지 않는다 — 화면이 보여 주는 것만 읽는다.
//   node tools/meshy_pipe/mp_cards.mjs [개수]
import { attach } from './mp_lib.mjs';

const N = Number(process.argv[2] || 12);
const { b, page } = await attach();
const cards = await page.evaluate((n) => {
  // 그리드 카드: 썸네일 img 를 품고 가로 200~400 인 박스들
  const boxes = [];
  for (const el of document.querySelectorAll('div,li,a')) {
    const r = el.getBoundingClientRect();
    if (r.left < 900 || r.width < 90 || r.width > 420 || r.height < 90) continue;
    if (el.querySelector('div,li,a') && [...el.children].some(c => c.getBoundingClientRect().height > r.height * 0.9 && c.getBoundingClientRect().width > r.width * 0.9)) continue;
    boxes.push(el);
  }
  const uniq = [];
  for (const el of boxes) {
    const r = el.getBoundingClientRect();
    if (uniq.some(u => Math.abs(u.r.left - r.left) < 6 && Math.abs(u.r.top - r.top) < 6)) continue;
    uniq.push({ el, r });
  }
  uniq.sort((a, b) => a.r.top - b.r.top || a.r.left - b.r.left);
  return uniq.slice(0, n).map((u, i) => {
    const img = u.el.querySelector('img');
    const txt = (u.el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80);
    return `${i} (${Math.round(u.r.left)},${Math.round(u.r.top)} ${Math.round(u.r.width)}x${Math.round(u.r.height)}) "${txt}" img=${img ? img.src.slice(-46) : '-'}`;
  });
}, N);
console.log(cards.join('\n'));
await b.close();
