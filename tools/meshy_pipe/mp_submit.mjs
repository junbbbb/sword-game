// 소품 한 개를 이미지→3D 로 접수한다.
//   node tools/meshy_pipe/mp_submit.mjs <이름> [--dry]
//   --dry 는 이미지만 올리고 "생성하다"는 누르지 않는다(설정 확인용).
//
// ★영수증 규칙: 누르기 전/후 크레딧을 비교한다. 안 줄었으면 클릭이 삼켜진 것 —
//   그래도 연타하지 않는다(LOG.md). 한 번 더 확인하고 안 되면 사람이 본다.
import { attach, credits, dump, shot, SRC_DIR, sleep, stamp } from './mp_lib.mjs';

const NAME = process.argv[2];
const DRY = process.argv.includes('--dry');
if (!NAME) { console.log('이름을 다오'); process.exit(1); }
const png = SRC_DIR + '/' + NAME + '.png';

const { b, page } = await attach();
const c0 = await credits(page);
console.log(`[${stamp()}] ${NAME} 접수 시작 · 크레딧 ${c0}`);

// 설정 실측(눈이 아니라 속성으로)
const state = await page.evaluate(() => {
  // ★라벨의 부모에 스위치가 있다고 가정하면 행마다 깊이가 달라 헛짚는다.
  //   라벨과 "같은 y 줄"에 있는 스위치를 좌표로 짝짓는다.
  const sw = (labelText) => {
    let lab = null;
    for (const l of document.querySelectorAll('label')) {
      if ((l.textContent || '').trim() === labelText) { lab = l; break; }
    }
    if (!lab) return '(라벨 못 찾음)';
    const ly = lab.getBoundingClientRect().top;
    for (const s of document.querySelectorAll('[role=switch]')) {
      const r = s.getBoundingClientRect();
      if (Math.abs(r.top - ly) < 12) return s.getAttribute('aria-checked');
    }
    return '(스위치 못 찾음)';
  };
  const radio = (txt) => {
    for (const btn of document.querySelectorAll('button[role=radio]')) {
      if ((btn.textContent || '').trim() === txt) return btn.getAttribute('aria-checked');
    }
    return '(못 찾음)';
  };
  return {
    ultra: sw('울트라 모드'), multiview: sw('멀티 뷰'), enhance: sw('이미지 향상'),
    autosplit: sw('자동 분할'), licensePrivate: radio('비공식적인'), hiDetail: radio('높은 디테일'),
  };
});
console.log('설정: ' + JSON.stringify(state));
if (state.ultra !== 'true' || state.multiview !== 'false' || state.enhance !== 'true' || state.licensePrivate !== 'true') {
  console.log('★설정이 요구와 다르다. 중단.');
  await b.close(); process.exit(2);
}

// 이미지 투입
await page.setInputFiles('input[type=file][accept*=".png"]', png);
await sleep(2500);
console.log('업로드 후 패널:');
console.log((await dump(page, 'body')).split('\n').filter(l => Number(l.match(/\((\d+),/)?.[1] || 999) < 380).join('\n'));
const cost = await page.evaluate(() => {
  const btn = [...document.querySelectorAll('button')].find(x => (x.textContent || '').trim() === '생성하다');
  return btn ? (btn.parentElement.parentElement.textContent || '').trim().slice(0, 60) : null;
});
console.log('생성 버튼 주변: ' + cost);

if (DRY) { console.log('(dry - 생성 안 누름)'); await shot(page, NAME + '_form'); await b.close(); process.exit(0); }

// 접수
const btn = page.locator('button[type=submit]', { hasText: '생성하다' }).first();
await btn.click();
console.log(`[${stamp()}] 생성 클릭`);

// 영수증: 크레딧 감소를 기다린다
let c1 = c0;
for (let i = 0; i < 30; i++) {
  await sleep(2000);
  c1 = await credits(page);
  if (c1 !== null && c1 < c0) break;
}
console.log(`[${stamp()}] 크레딧 ${c0} → ${c1} (차이 ${c0 - c1})`);
if (c1 >= c0) console.log('★접수 못 확인. 연타 금지 - 사람이 화면을 볼 것.');
await b.close();
