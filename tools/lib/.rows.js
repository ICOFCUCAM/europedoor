const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  for (const u of process.argv.slice(2)) {
    await p.goto('http://127.0.0.1:8899' + u, { waitUntil: 'networkidle' });
    console.log(u);
    console.log(await p.evaluate(() => [...document.querySelectorAll('.jrow, .journeyrow')].map(r => {
      const kids = [...r.children].map(k => Math.round(k.getBoundingClientRect().height));
      const h = Math.round(r.getBoundingClientRect().height);
      return `  row ${String(h).padStart(4)}px  columns ${kids.join(' / ')}  void ${h - Math.max(...kids)}..${h - Math.min(...kids)}  "${(r.querySelector('h2,h3')||{textContent:''}).textContent.trim().slice(0,24)}"`;
    }).join('\n')));
  }
  await b.close();
})();
