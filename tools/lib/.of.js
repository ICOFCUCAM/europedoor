const { chromium } = require('playwright');
const fams = require('./families.js');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const list = (fams.FAMILIES || fams.families || fams);
  const urls = (Array.isArray(list) ? list : Object.values(list)).map(f => Array.isArray(f) ? f[1] : (f.url || f.path));
  let bad = 0;
  for (const w of [390, 834, 1280]) {
    const p = await b.newPage({ viewport: { width: w, height: 900 } });
    for (const u of urls) {
      if (!u) continue;
      const res = await p.goto('http://127.0.0.1:8899' + u, { waitUntil: 'domcontentloaded' }).catch(() => null);
      if (!res || res.status() !== 200) { console.log(`  ${w} ${u} -> ${res ? res.status() : 'ERR'}`); continue; }
      const o = await p.evaluate(() => {
        const d = document.documentElement;
        const over = [];
        if (d.scrollWidth > d.clientWidth + 1) {
          document.querySelectorAll('body *').forEach(e => {
            const r = e.getBoundingClientRect();
            if (r.right > d.clientWidth + 1 && getComputedStyle(e).overflowX !== 'auto'
                && getComputedStyle(e).overflowX !== 'scroll' && e.children.length === 0)
              over.push(e.tagName + '.' + String(e.className||'').split(' ')[0] + ' r=' + Math.round(r.right));
          });
          return { sw: d.scrollWidth, cw: d.clientWidth, over: over.slice(0, 3) };
        }
        return null;
      });
      if (o) { bad++; console.log(`  ${w}px ${u}  ${o.sw}>${o.cw}  ${o.over.join(' | ')}`); }
    }
    await p.close();
  }
  console.log(bad ? `${bad} overflowing` : 'no document overflow at 390/834/1280');
  await b.close();
})();
