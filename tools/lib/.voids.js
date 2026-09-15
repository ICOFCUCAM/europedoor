// Vertical bands of a page where nothing is drawn: no leaf box, no painted
// ground, no border. Measuring the boxes is wrong where a section paints a
// tone, so a painted ancestor counts as content too.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  await p.goto(process.argv[2], { waitUntil: 'networkidle' });
  const r = await p.evaluate(() => {
    const ground = getComputedStyle(document.body).backgroundColor;
    const spans = [];
    document.querySelectorAll('main *').forEach(e => {
      const cs = getComputedStyle(e), rc = e.getBoundingClientRect();
      if (rc.height <= 0 || cs.visibility === 'hidden') return;
      const leaf = e.children.length === 0 && (e.textContent || '').trim() !== '';
      const painted = cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== ground;
      const bordered = ['Top','Bottom'].some(s => parseFloat(cs['border' + s + 'Width']) > 0);
      const svg = e.tagName === 'svg' || e.tagName === 'IMG';
      if (!(leaf || painted || bordered || svg)) return;
      if (bordered && !leaf && !painted && !svg) {
        // a box with rules: only its two edges are drawn
        const t = parseFloat(cs.borderTopWidth), bo = parseFloat(cs.borderBottomWidth);
        if (t > 0) spans.push([rc.top + scrollY, rc.top + scrollY + t]);
        if (bo > 0) spans.push([rc.bottom + scrollY - bo, rc.bottom + scrollY]);
        return;
      }
      spans.push([rc.top + scrollY, rc.bottom + scrollY]);
    });
    spans.sort((a, z) => a[0] - z[0]);
    const heads = [...document.querySelectorAll('main :is(h1,h2,h3)')].map(e =>
      ({ y: e.getBoundingClientRect().top + scrollY, t: (e.textContent||'').trim().slice(0,38) }));
    const H = document.documentElement.scrollHeight;
    const gaps = []; let low = 0, total = 0;
    for (const [s, e] of spans) {
      if (s - low > 90) { gaps.push({ at: Math.round(low), px: Math.round(s - low),
        before: (heads.find(h => h.y >= s - 4) || { t: '(end)' }).t }); total += s - low; }
      low = Math.max(low, e);
    }
    return { gaps, total: Math.round(total), H };
  });
  r.gaps.forEach(g => console.log(`  ${String(g.px).padStart(4)}px  at y=${g.at}  before "${g.before}"`));
  console.log(`page ${r.H}px · ${r.gaps.length} voids over 90px · ${r.total}px empty (${(100*r.total/r.H).toFixed(1)}%)`);
  await b.close();
})();
