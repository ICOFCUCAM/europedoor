const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  for (const u of process.argv.slice(2)) {
    await p.goto('http://127.0.0.1:8899' + u, { waitUntil: 'networkidle' });
    console.log(u);
    console.log(await p.evaluate(() => [...document.querySelectorAll('.band-head')].map(h => {
      const t = h.querySelector('h2'), l = h.querySelector('.lede');
      if (!t || !l) return null;
      const a = t.getBoundingClientRect(), c = l.getBoundingClientRect();
      return `  h2 x=${Math.round(a.left)} w=${Math.round(a.width)} · lede x=${Math.round(c.left)} w=${Math.round(c.width)} · gap ${Math.round(c.left - a.left)}  "${t.textContent.trim().slice(0,26)}"`;
    }).filter(Boolean).join('\n')));
  }
  await b.close();
})();
