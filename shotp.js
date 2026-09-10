const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 390, height: 900 } });
  for (const u of process.argv.slice(2)) {
    const r = await p.goto('http://localhost:8899' + u, { waitUntil: 'networkidle' });
    if (r.status() !== 200) { console.log('SKIP', u, r.status()); continue; }
    await p.screenshot({ path: `/tmp/shots/p${(u.replace(/\//g,'_')||'_home')}.png`, fullPage: true });
    console.log('shot', u);
  }
  await b.close();
})();
