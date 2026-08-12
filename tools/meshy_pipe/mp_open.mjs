// 독립 크롬 창을 띄우고 살려 둔다. 이 프로세스가 죽으면 창도 죽는다 → 백그라운드로 돌릴 것.
//   node tools/meshy_pipe/mp_open.mjs &
// ★원본 MCP 프로필(mcp-chrome-27edcdf)은 절대 열지 않는다. 복제본만 연다.
import { chromium } from '/Users/lbj/Documents/real-estate-agent/node_modules/playwright/index.mjs';
import { PROFILE, WORKSPACE, sleep } from './mp_lib.mjs';

const ctx = await chromium.launchPersistentContext(PROFILE, {
  channel: 'chrome',
  headless: false,                       // Meshy 는 WebGL 무거운 사이트 - headless 금지
  viewport: { width: 1500, height: 900 },
  acceptDownloads: true,
  args: [
    '--remote-debugging-port=9333',      // 단계 스크립트가 붙는 문
    '--window-size=1520,1010',
    '--window-position=0,0',
  ],
});

const page = ctx.pages()[0] || await ctx.newPage();
await page.goto(WORKSPACE, { waitUntil: 'domcontentloaded', timeout: 120000 });
console.log('열림: ' + page.url());

// 살려 둔다
process.on('SIGTERM', async () => { await ctx.close(); process.exit(0); });
for (;;) await sleep(60000);
