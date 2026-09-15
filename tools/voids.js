#!/usr/bin/env node
/* EMPTY PAGE, MEASURED, PER FAMILY.
 *
 *     node tools/voids.js            every family at 1280
 *     node tools/voids.js --phone    at 390
 *     node tools/voids.js --json     for a diff between two runs
 *
 * A band of page with nothing in it is the one defect a count cannot see and
 * a thumbnail hides: the old stories index was thrown away for being 5,792
 * pixels of nine cards alone in nine rows, and the only reason anybody found
 * it was by looking. This asks the question the whole site at once.
 *
 * THIS IS NOT A GATE AND MUST NOT BECOME ONE, on `opening.js`'s own reason.
 * A ceiling on empty page is satisfied by tightening the section rhythm,
 * which would make the site worse: the 104px between two bands is not a hole,
 * it is what says the bands are separate. What the number is for is the
 * OUTLIER — a 296px column beside a picture, a lede alone in the right half.
 *
 * AND MEASURING THE BOXES IS WRONG, which the first version proved: reading
 * h2/h3/p/li/figure/nav/ul/ol reported 1,702px empty on a destination page
 * against a real 804, because the Europe Experience Score is drawn in divs
 * and spans and the instrument could not see it. A painted ground and a
 * border count as content, and a box whose only ink is its rules contributes
 * those two edges and not its middle.
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

const PROBE = () => {
  const ground = getComputedStyle(document.body).backgroundColor;
  const spans = [];
  for (const e of document.querySelectorAll('main *')) {
    const cs = getComputedStyle(e), rc = e.getBoundingClientRect();
    if (rc.height <= 0 || cs.visibility === 'hidden') continue;
    const leaf = e.children.length === 0 && (e.textContent || '').trim() !== '';
    const painted = cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== ground;
    const drawn = e.tagName === 'svg' || e.tagName === 'IMG';
    const top = parseFloat(cs.borderTopWidth), bot = parseFloat(cs.borderBottomWidth);
    if (leaf || painted || drawn) { spans.push([rc.top + scrollY, rc.bottom + scrollY]); continue; }
    /* A box whose only ink is its rules draws two edges and not its middle. */
    if (top > 0) spans.push([rc.top + scrollY, rc.top + scrollY + top]);
    if (bot > 0) spans.push([rc.bottom + scrollY - bot, rc.bottom + scrollY]);
  }
  spans.sort((a, z) => a[0] - z[0]);
  const heads = [...document.querySelectorAll('main :is(h1,h2,h3)')].map(e =>
    ({ y: e.getBoundingClientRect().top + scrollY, t: (e.textContent || '').trim().slice(0, 40) }));
  const H = document.documentElement.scrollHeight;
  const gaps = []; let low = 0, total = 0;
  for (const [s, e] of spans) {
    if (s - low > 90) {
      gaps.push({ at: Math.round(low), px: Math.round(s - low),
                  before: (heads.find(h => h.y >= s - 4) || { t: '(end of page)' }).t });
      total += s - low;
    }
    low = Math.max(low, e);
  }
  return { gaps, total: Math.round(total), H };
};

(async () => {
  const phone = process.argv.includes('--phone');
  const srv = serve().listen(0);
  const base = 'http://127.0.0.1:' + srv.address().port;
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: phone ? { width: 390, height: 844 }
                                              : { width: 1280, height: 1000 } });
  const rows = [];
  for (const [name, url] of ALL) {
    const res = await p.goto(base + url, { waitUntil: 'networkidle' });
    if (!res || res.status() !== 200) { console.error(`  ${name} ${url} -> ${res ? res.status() : 'ERR'}`); continue; }
    rows.push({ name, url, ...(await p.evaluate(PROBE)) });
  }
  await b.close(); srv.close();

  if (process.argv.includes('--json')) { console.log(JSON.stringify(rows, null, 1)); return; }
  rows.sort((a, z) => z.total - a.total);
  for (const x of rows) {
    if (!x.total) continue;
    console.log(`${String(x.total).padStart(5)}px  ${String((100 * x.total / x.H).toFixed(1)).padStart(5)}%  `
      + `${String(x.gaps.length).padStart(2)} voids  ${x.name.padEnd(15)} ${x.url}`);
    for (const g of x.gaps.filter(g => g.px >= 130))
      console.log(`         ${String(g.px).padStart(4)}px before "${g.before}"`);
  }
  const T = rows.reduce((a, x) => a + x.total, 0), P = rows.reduce((a, x) => a + x.H, 0);
  console.log(`\n${rows.length} families at ${phone ? 390 : 1280} · ${T}px empty of ${P}px (${(100 * T / P).toFixed(1)}%)`
    + `\nA void is a band over 90px with nothing painted in it. There is no threshold here;`
    + `\nthe section rhythm is about 104px and that is not a hole. Read the outliers.`);
})();
