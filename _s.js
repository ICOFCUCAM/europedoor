const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: parseInt(process.argv[3]||'1000',10) } });
  await p.goto('http://localhost:8899' + process.argv[2], { waitUntil: 'load' });
  await p.waitForTimeout(400);
  await p.screenshot({ path: process.env.SP + '/' + (process.argv[4]||'shot.png') });
  await b.close();
})();
