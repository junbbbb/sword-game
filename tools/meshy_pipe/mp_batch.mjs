// 남은 소품들을 차례로 접수한다(Meshy 는 여러 작업을 동시에 굴린다 — 하나씩 기다릴 이유가 없다).
//   node tools/meshy_pipe/mp_batch.mjs 이름1 이름2 ...
// ★한 건이라도 크레딧이 안 줄면 거기서 멈춘다(삼킴을 못 보고 계속 누르면 유령 접수가 쌓인다).
import { spawnSync } from 'child_process';
import { attach, credits, sleep, stamp } from './mp_lib.mjs';

const names = process.argv.slice(2);
for (const n of names) {
  const { b, page } = await attach();
  const before = await credits(page);
  await b.close();
  const r = spawnSync('node', [new URL('./mp_submit.mjs', import.meta.url).pathname, n],
    { encoding: 'utf8' });
  const line = (r.stdout || '').split('\n').filter(l => l.includes('크레딧') || l.includes('★')).join(' | ');
  console.log(`[${stamp()}] ${n}: ${line}`);
  if (/★/.test(r.stdout || '')) { console.log('멈춘다.'); break; }
  const { b: b2, page: p2 } = await attach();
  const after = await credits(p2);
  await b2.close();
  if (!(after < before)) { console.log(`★${n} 접수 미확인(${before}→${after}) — 멈춘다.`); break; }
  await sleep(4000);
}
