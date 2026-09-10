const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const urls = process.argv.slice(2);
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  for (const u of urls) {
    const r = await p.goto('http://localhost:8899' + u, { waitUntil: 'networkidle' });
    if (r.status() !== 200) { console.log('SKIP', u, r.status()); continue; }
    const name = (u.replace(/\//g, '_') || '_home');
    await p.screenshot({ path: `/tmp/shots/${name}.png`, fullPage: true });
    console.log('shot', u);
  }
  await b.close();
})();
