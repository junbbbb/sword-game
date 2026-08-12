// 붙어서 지금 화면이 무엇인지 읽는다. 인자로 CSS 선택자를 주면 그 안만 덤프.
//   node tools/meshy_pipe/mp_probe.mjs [선택자] [스샷이름]
import { attach, credits, dump, shot } from './mp_lib.mjs';

const sel = process.argv[2] || 'body';
const name = process.argv[3] || null;
const { b, page } = await attach();
console.log('URL: ' + page.url());
console.log('크레딧: ' + await credits(page));
console.log('--- 화면 텍스트 ---');
console.log(await dump(page, sel));
if (name) console.log('스샷: ' + await shot(page, name));
await b.close();
