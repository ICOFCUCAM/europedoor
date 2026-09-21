#!/usr/bin/env node
/* HOW MUCH OF EACH SLICE OF A PAGE IS PAINTED AT ALL, PER FAMILY.
 *
 *     node tools/density.js            every family at 1280
 *     node tools/density.js --phone    at 390
 *     node tools/density.js /          one path
 *     node tools/density.js --json     for a diff between two runs
 *
 * `voids.js` finds a band with NOTHING painted in it. This is the other half
 * of the same question and the one nothing here had ever asked: a band with
 * ALMOST nothing in it — a 300-pixel run at four per cent covered is not a
 * void and is exactly what a reader means by "this part of the page is
 * empty". The homepage was reported that way by the owner with a screenshot,
 * and `voids.js` had said zero: every slice of that run held a hairline, a
 * kicker or the top edge of something, so not one of them was empty and the
 * band still read as a hole. Measured as the horizontal UNION of everything
 * that paints, per 50px slice, as a share of the page's own width.
 *
 * THIS IS NOT A GATE AND MUST NOT BECOME ONE, on `voids.js`'s own reason. A
 * floor on coverage is satisfied by widening every measure until the page is
 * a wall of type, which is the opposite of this product; and a run at 8% is
 * right where the thing above it is a closing statement. What the number is
 * for is the OUTLIER, and for the before-and-after of a composition change.
 *
 * A FIXED BOX'S RECT IS VIEWPORT-RELATIVE, and adding `scrollY` to it puts
 * the picture in whatever slice the page happened to be scrolled to. The
 * window plate is exactly that — `position: fixed` revealed through a
 * `clip-path` band — so the first version reported an 850px run at 1% inside
 * the one plate that is a full-bleed photograph, and a screenshot at y=1500
 * showing London filling the frame is what disproved it. What such a box
 * paints is the whole of its CLIPPING ancestor, which is what a reader sees,
 * so it is attributed there. The first correction read `position` on the
 * child alone and changed nothing, because the fixed element is the parent:
 * the walk goes up the whole chain. 31% to 27%.
 */
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');

const ROOT = path.join(__dirname, '..', 'site');
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif',
  '.xml': 'application/xml', '.txt': 'text/plain' };
const { ALL } = require('./lib/families.js');

function serve() {
  return http.createServer((q, r) => {
    const rel = decodeURIComponent(q.url.split('?')[0]);
    let f = path.join(ROOT, rel);
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
    else if (!fs.existsSync(f) && fs.existsSync(f + '.html')) f += '.html';
    if (!fs.existsSync(f)) { r.writeHead(404); return r.end('not built'); }
    r.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' });
    fs.createReadStream(f).pipe(r);
  });
}

const SLICE = 50, THIN = 0.20, RUN = 200;

const PROBE = (SL) => {
  const H = document.documentElement.scrollHeight, n = Math.ceil(H / SL);
  const cover = Array.from({ length: n }, () => []);
  const walk = (el) => {
    for (const c of el.children) {
      const st = getComputedStyle(c);
      if (st.display === 'none' || st.visibility === 'hidden' || st.opacity === '0') continue;
      const tag = c.tagName.toLowerCase();
      /* Anything a reader can see: a picture, a drawing, a rule, or a box
       * holding its own words. A container's rectangle is not ink. */
      const paints = tag === 'img' || tag === 'svg' || tag === 'picture' || tag === 'hr'
        || [...c.childNodes].some(k => k.nodeType === 3 && k.textContent.trim());
      if (paints) {
        const b = c.getBoundingClientRect();
        if (b.width > 0 && b.height > 0) {
          let fx = null;
          for (let a = c; a && a !== document.body; a = a.parentElement)
            if (getComputedStyle(a).position === 'fixed') { fx = a; break; }
          let host = c;
          if (fx) {
            let a = fx.parentElement;
            while (a && getComputedStyle(a).clipPath === 'none') a = a.parentElement;
            if (a) host = a;
          }
          const hb = host === c ? b : host.getBoundingClientRect();
          const top = hb.top + scrollY, bot = hb.bottom + scrollY;
          for (let i = Math.max(0, Math.floor(top / SL)); i < Math.min(n, Math.ceil(bot / SL)); i++)
            cover[i].push([b.left, b.right]);
        }
      }
      if (tag !== 'svg') walk(c);
    }
  };
  walk(document.body);
  const W = document.documentElement.clientWidth;
  return { H, slices: cover.map(rs => {
    if (!rs.length) return 0;
    rs.sort((a, z) => a[0] - z[0]);
    let tot = 0, s0 = rs[0][0], e0 = rs[0][1];
    for (const [s, e] of rs.slice(1)) {
      if (s > e0) { tot += e0 - s0; s0 = s; e0 = e; } else e0 = Math.max(e0, e);
    }
    return Math.min(1, (tot + e0 - s0) / W);
  }) };
};

(async () => {
  const phone = process.argv.includes('--phone');
  const one = process.argv.slice(2).find(a => a.startsWith('/'));
  const list = one ? [['(path)', one]] : ALL;
  const srv = serve().listen(0);
  const base = 'http://127.0.0.1:' + srv.address().port;
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: phone ? { width: 390, height: 844 }
                                              : { width: 1280, height: 900 } });
  const rows = [];
  for (const [name, url] of list) {
    const res = await p.goto(base + url, { waitUntil: 'load' });
    if (!res || res.status() !== 200) { console.error(`  ${name} ${url} -> ${res ? res.status() : 'ERR'}`); continue; }
    /* LAZY IMAGES DO NOT LOAD FOR A PAGE NOBODY SCROLLED, and an unloaded
     * picture measures as a box with no ink — which is the defect this
     * instrument exists to report, arriving from the instrument. */
    const H0 = await p.evaluate(() => document.documentElement.scrollHeight);
    for (let y = 0; y < H0; y += 700) { await p.evaluate(v => scrollTo(0, v), y); await p.waitForTimeout(80); }
    await p.evaluate(() => scrollTo(0, 0)); await p.waitForTimeout(150);
    const { H, slices } = await p.evaluate(PROBE, SLICE);
    const runs = []; let run = null;
    slices.forEach((v, i) => {
      if (v < THIN) { if (!run) run = { a: i, b: i, sum: 0, k: 0 }; run.b = i; run.sum += v; run.k++; }
      else if (run) { runs.push(run); run = null; }
    });
    if (run) runs.push(run);
    rows.push({ name, url, H,
      thin: slices.filter(v => v < THIN).length, n: slices.length,
      runs: runs.filter(x => (x.b - x.a + 1) * SLICE >= RUN)
                .map(x => ({ at: x.a * SLICE, px: (x.b - x.a + 1) * SLICE,
                             pc: Math.round(100 * x.sum / x.k) }))
                .sort((a, z) => z.px - a.px) });
  }
  await b.close(); srv.close();

  if (process.argv.includes('--json')) { console.log(JSON.stringify(rows, null, 1)); return; }
  rows.sort((a, z) => z.thin / z.n - a.thin / a.n);
  for (const x of rows) {
    console.log(`${String(Math.round(100 * x.thin / x.n)).padStart(3)}%  ${String(x.H).padStart(6)}px  `
      + `${String(x.runs.length).padStart(2)} runs  ${x.name.padEnd(15)} ${x.url}`);
    for (const r of x.runs.slice(0, 4))
      console.log(`         ${String(r.px).padStart(5)}px from y=${String(r.at).padStart(6)} at ${r.pc}% covered`);
  }
  const t = rows.reduce((a, x) => a + x.thin, 0), n = rows.reduce((a, x) => a + x.n, 0);
  console.log(`\n${rows.length} ${one ? 'path' : 'families'} at ${phone ? 390 : 1280} · `
    + `${t} of ${n} slices of ${SLICE}px under ${100 * THIN}% covered (${(100 * t / n).toFixed(0)}%)`
    + `\nThere is no threshold here and there must not be one: a floor on coverage`
    + `\nis satisfied by widening every measure until the page is a wall of type.`
    + `\nRead the runs — a 700px band at 1% is a hole, a 200px one at 8% is air.`);
})();
