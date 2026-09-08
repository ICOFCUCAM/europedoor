const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  for (const t of process.argv.slice(2)) {
    const [file, out, h, w] = t.split('|');
    await p.setViewportSize({ width: parseInt(w || '1280', 10), height: parseInt(h || '1000', 10) });
    await p.goto('http://localhost:8899/' + file, { waitUntil: 'load' });
    await p.waitForTimeout(400);
    await p.screenshot({ path: '/tmp/claude-0/-home-user/34dc148c-0efe-5ec5-91b5-011dc475a2b3/scratchpad/' + out });
  }
  await b.close();
})();
