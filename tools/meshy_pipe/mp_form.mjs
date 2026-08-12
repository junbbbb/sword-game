// 왼쪽 생성 패널의 "조작 가능한 것"만 상태와 함께 뽑는다(토글이 켜졌는지 눈이 아니라 속성으로 판정).
//   node tools/meshy_pipe/mp_form.mjs [최대x]
import { attach } from './mp_lib.mjs';

const MAXX = Number(process.argv[2] || 400);
const { b, page } = await attach();
const rows = await page.evaluate((maxx) => {
  const out = [];
  const q = 'button, [role=button], [role=switch], [role=radio], [role=tab], input, select, textarea, label, a[href]';
  for (const el of document.querySelectorAll(q)) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && el.tagName !== 'INPUT') continue;
    if (r.left > maxx) continue;
    const attrs = [];
    for (const a of el.attributes) {
      if (/^(aria-|data-state|data-value|role|type|value|name|id|checked|disabled|accept|multiple)/.test(a.name)) {
        attrs.push(a.name + '=' + a.value.slice(0, 40));
      }
    }
    out.push(`[${el.tagName.toLowerCase()}] (${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}x${Math.round(r.height)}) ` +
      `"${(el.textContent || '').trim().slice(0, 40)}" ${attrs.join(' ')} .${(el.className && el.className.baseVal !== undefined ? el.className.baseVal : String(el.className || '')).slice(0, 60)}`);
  }
  return out;
}, MAXX);
console.log(rows.join('\n'));
await b.close();
