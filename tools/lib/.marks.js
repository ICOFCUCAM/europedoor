const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  for (const u of process.argv.slice(2)) {
    await p.goto('http://127.0.0.1:8899' + u, { waitUntil: 'networkidle' });
    const r = await p.evaluate(() => [...document.querySelectorAll('svg.constel.framed')].map(s => {
      const c = s.querySelector('.constel-lit circle:not(.term)') || s.querySelector('.constel-lit circle');
      if (!c) return null;
      const vb = s.getAttribute('viewBox').split(' ').map(Number);
      return { vw: vb[2], px: +(c.getBoundingClientRect().width / 2).toFixed(2),
               fam: String(s.parentElement.className || s.className.baseVal).split(' ')[0] };
    }).filter(Boolean));
    r.forEach(x => console.log(`  ${u.padEnd(30)} frame ${String(Math.round(x.vw)).padStart(4)}u  mark ${String(x.px).padStart(5)}px  ${x.fam}`));
  }
  await b.close();
})();
