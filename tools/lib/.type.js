const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  await p.goto(process.argv[2], { waitUntil: 'networkidle' });
  console.log(await p.evaluate(() => {
    const m = new Map();
    document.querySelectorAll('main *').forEach(e => {
      if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
      const c = getComputedStyle(e);
      const k = `${c.fontSize} / ${c.lineHeight} ${c.fontWeight} ${c.fontFamily.split(',')[0]}`;
      const n = m.get(k) || { n: 0, chars: 0, eg: '' };
      n.n++; n.chars += e.textContent.trim().length;
      if (!n.eg) n.eg = e.tagName + '.' + String(e.className || '').split(' ')[0];
      m.set(k, n);
    });
    return [...m].sort((a, z) => z[1].chars - a[1].chars)
      .map(([k, v]) => `${String(v.chars).padStart(6)} chars  ${String(v.n).padStart(3)}x  ${k}  ${v.eg}`).join('\n');
  }));
  await b.close();
})();
