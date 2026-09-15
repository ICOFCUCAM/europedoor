const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 1 });
  await p.goto(process.argv[2], { waitUntil: 'networkidle' });
  const y0 = +process.argv[4], n = +process.argv[5] || 1;
  for (let i = 0; i < n; i++)
    await p.screenshot({ path: `${process.argv[3]}-${i}.png`, fullPage: true,
      clip: { x: 0, y: y0 + i * 1000, width: 1280, height: 1000 } });
  await b.close();
})();
