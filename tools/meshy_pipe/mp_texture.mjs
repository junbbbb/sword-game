// 모델 하나에 텍스처를 굽는다(10cr, 2K, PBR 켬).
//   node tools/meshy_pipe/mp_texture.mjs <소품이름|작업id>
//
// ★★사고 기록(2026-08-13): 처음엔 el.click() 으로 카드를 고른 줄 알았다. 리액트는 그 클릭을
//   무시했고, 뷰어는 계속 첫 모델(pillar_intact)을 들고 있었다. 그 상태로 '텍스처'를 여덟 번
//   눌러 같은 기둥에 텍스처를 여덟 번 구웠다(80cr 소각). 그래서 이 스크립트는 매 단계
//   ①전체화면 편집기를 닫고 ②진짜 마우스로 카드를 고르고 ③뷰어가 정말 바뀌었는지
//   (하단 썸네일의 uploads id) 확인하고 ④도구막대가 '텍스처 +10'(=아직 무텍스처)인지 본 뒤에야
//   패널을 연다. 확인 하나라도 실패하면 크레딧을 쓰지 않고 멈춘다.
import { readFileSync, appendFileSync } from 'fs';
import { attach, credits, closeModal, selectCard, barText, shot, sleep, stamp, LOG_DIR } from './mp_lib.mjs';

const ARG = process.argv[2];
if (!ARG) { console.log('소품 이름을 다오'); process.exit(1); }
const ids = JSON.parse(readFileSync(new URL('./mp_ids.json', import.meta.url), 'utf8'));
const task = (ids[ARG] && ids[ARG].model) || ARG;

const { b, page } = await attach();
const die = async (msg, code) => { console.log('★' + msg); await b.close(); process.exit(code); };

// ① 전체화면 편집기 닫기
if (await closeModal(page)) console.log('  (텍스처 편집 화면을 닫았다)');

// ①-2 텍스처 패널이 열린 채면 닫는다(열린 패널은 "열릴 때 물린 모델"을 계속 가리킨다)
const panelOpen = () => page.evaluate(() => [...document.querySelectorAll('div')]
  .some(d => (d.innerText || '').includes('텍스처 해상도') && d.getBoundingClientRect().width < 500));
// (전체화면 편집기는 Escape 로 안 닫히고 X 라야 하지만, 이 패널은 Escape 면 닫힌다)
if (await panelOpen()) {
  await page.keyboard.press('Escape');
  await sleep(1200);
  if (await panelOpen()) await die('텍스처 패널이 안 닫힌다', 5);
  console.log('  (앞 단계 텍스처 패널을 닫았다)');
}

// ② 그리드 필터를 '전체'로
await page.evaluate(() => {
  const all = document.querySelector('[data-testid=assets-phase-all-btn]');
  if (all && all.getAttribute('aria-checked') !== 'true') all.click();
});
await sleep(1500);

// ③ 카드 고르기 + 정말 바뀌었나 확인
const sel = await selectCard(page, task, process.argv[3] || (ids[ARG] && ids[ARG].image) || null);
if (!sel.ok) await die(`${ARG} 카드 선택 실패: ${sel.why}`, 3);
console.log(`[${stamp()}] ${ARG} 선택됨 · 원본이미지 ${sel.source}`);

// ④ 아직 무텍스처 모델인가
const bar = await barText(page);
if (!bar.includes('텍스처')) await die(`${ARG} 는 이미 텍스처된 자산이다(막대: "${bar}"). 텍스처 두 번 굽지 않는다.`, 4);

// ⑤ 패널 열기
const c0 = await credits(page);
await page.click('[data-testid=viewer-edit-texture-btn]');
await sleep(2600);

const st = await page.evaluate(() => {
  const panel = [...document.querySelectorAll('div')].find(d => (d.innerText || '').includes('텍스처 해상도') && d.getBoundingClientRect().width < 500);
  if (!panel) return { err: '텍스처 패널 못 찾음' };
  const img = panel.querySelector('img');
  const pbr = (() => {
    for (const el of panel.querySelectorAll('*')) {
      if ((el.textContent || '').trim() === 'PBR 맵 생성' && el.children.length === 0) {
        const y = el.getBoundingClientRect().top;
        for (const s of panel.querySelectorAll('[role=switch]')) {
          if (Math.abs(s.getBoundingClientRect().top - y) < 14) return s.getAttribute('aria-checked');
        }
      }
    }
    return '?';
  })();
  const res = [...panel.querySelectorAll('button[role=radio]')].filter(x => /^(2K|4K|8K)$/.test((x.innerText || '').trim()))
    .map(x => (x.innerText || '').trim() + ':' + x.getAttribute('aria-checked')).join(' ');
  const cost = (panel.innerText || '').match(/(\d+)분\s*(\d+)/);
  const btn = [...panel.querySelectorAll('button')].filter(x => (x.innerText || '').trim() === '텍스처').pop();
  const r = btn ? btn.getBoundingClientRect() : null;
  return {
    img: img ? (img.src.match(/uploads\/([0-9a-f-]+)\./) || [])[1] : null,
    pbr, res, cost: cost ? cost[0].replace(/\s+/g, ' ') : '?',
    btn: r ? { x: r.left + r.width / 2, y: r.top + r.height / 2 } : null,
  };
});
console.log(`[${stamp()}] 텍스처 패널: ` + JSON.stringify({ ...st, btn: undefined }));
if (st.err || !st.img || !st.btn) { await shot(page, 'tex_fail_' + ARG); await die('패널 상태가 이상하다. 중단.', 2); }
if (st.img !== sel.source) await die(`패널이 다른 모델을 물었다(뷰어 ${sel.source} vs 패널 ${st.img})`, 6);
if (st.pbr !== 'true' || !/2K:true/.test(st.res)) await die('PBR/해상도 설정이 요구와 다르다: ' + st.res + ' pbr=' + st.pbr, 7);

// ⑥ 접수 + 영수증
// ★좌표를 재서 mouse.click 하면 창이 미세하게 리사이즈될 때 빗나가 패널만 닫힌다(실패 1회).
//   요소 핸들을 그대로 클릭시켜 playwright 가 위치를 다시 재게 한다.
const btnH = await page.evaluateHandle(() => {
  const panel = [...document.querySelectorAll('div')].find(d => (d.innerText || '').includes('텍스처 해상도') && d.getBoundingClientRect().width < 500);
  return panel ? [...panel.querySelectorAll('button')].filter(x => (x.innerText || '').trim() === '텍스처').pop() : null;
});
const btnEl = btnH.asElement();
if (!btnEl) await die('텍스처 버튼을 못 잡았다', 8);
await btnEl.click();
console.log(`[${stamp()}] 텍스처 클릭 · 크레딧 ${c0}`);

let c1 = c0;
for (let i = 0; i < 30; i++) {
  await sleep(2000);
  c1 = await credits(page);
  if (c1 !== null && c1 < c0) break;
}
console.log(`[${stamp()}] 크레딧 ${c0} → ${c1} (차이 ${c0 - c1})`);
if (c1 >= c0) console.log('★접수 못 확인. 연타 금지.');
else appendFileSync(LOG_DIR + '/tex_images.txt', `${ARG}\t${sel.source}\t${stamp()}\t-${c0 - c1}cr\n`);
await b.close();
