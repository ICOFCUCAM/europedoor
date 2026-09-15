#!/usr/bin/env node
/* WHAT A READER GETS BEFORE THEY SCROLL, MEASURED RATHER THAN ASSERTED.
 *
 *     node tools/opening.js            every family at 390
 *     node tools/opening.js --wide     at 1280
 *     node tools/opening.js --json     for a diff between two runs
 *
 * `docs/first-class-audit.md` found that twelve of twenty-three surfaces are
 * effectively type to the fold and that seventeen of them place an
 * identically sized h1 at an identical height. Both were measured once, by
 * hand, and then written down — so the only way to know whether a change
 * moved either was to do the whole audit again.
 *
 * THIS IS NOT A GATE AND MUST NOT BECOME ONE. It reports; it has no
 * threshold and cannot fail. A gate on "picture share" would be a number to
 * satisfy, and the fault it exists to find is a page that is dull rather
 * than a page that is wrong — `docs/instruction.md` is explicit that the
 * eye finds a defect and counting settles a proportion.
 *
 * WHAT IS COUNTED IS PAINTED PIXELS OF THE FIRST SCREEN, not whether a
 * figure intersects it and not where the first one starts. The audit's own
 * first version read the document position of the first figure as though it
 * were the answer, and reported twenty-one of twenty-two where the truth was
 * twelve of twenty-three. Overlapping figures are merged before they are
 * summed, because two boxes over one another are one picture.
 */
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');

const ROOT = path.join(__dirname, '..', 'site');
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif',
  '.xml': 'application/xml', '.txt': 'text/plain' };

/* ONE PAGE PER FAMILY, and the slugs are read off the built site rather than
 * typed, because a typed slug is a 404 that reports 0% and looks like a
 * finding. The first run of this said `journey`, `macro` and `place` were
 * the three worst surfaces in the product; all three were bad URLs. */
function pick(dir, fallback) {
  try { const e = fs.readdirSync(path.join(ROOT, dir)).filter(n => !n.includes('.')).sort();
        return e.length ? dir + '/' + e[0] : fallback; } catch { return fallback; }
}
const VIENNA = 'europe/austria/vienna-and-the-east/vienna';
const FAMILIES = [
  ['homepage', '/'],
  ['countries', '/countries/'],
  ['macro', '/' + pick('discover', 'discover/nordic')],
  ['country', '/europe/austria/'],
  ['region', '/europe/austria/tyrol/'],
  ['destination', '/' + VIENNA + '/'],
  ['place', '/' + pick(VIENNA + '/place', VIENNA + '/place/schonbrunn')],
  ['experiences', '/experiences/'],
  ['category', '/experiences/food/'],
  ['journeys', '/journeys/'],
  ['journey', '/' + pick('journeys', 'journeys/carpathian-arc')],
  ['stories', '/stories/'],
  ['story', '/' + pick('stories', 'stories/a-language-with-no-relatives')],
  ['themes', '/themes/'],
  ['theme', '/' + pick('themes', 'themes/wine-europe')],
  ['interests', '/interests/'],
  ['interest', '/interests/mountains/'],
  ['europe-in', '/europe-in/'],
  ['motion', '/' + pick('europe-in', 'europe-in/above-the-arctic-circle')],
  ['events', '/events/'],
  ['quiet', '/beyond-the-obvious/'],
  ['map', '/map/'],
  ['discover', '/discover/'],
  ['plan', '/plan/'],
  ['search', '/search/'],
  ['my-europe', '/my-europe/'],
  ['404', '/404.html'],
];

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

/* RUN INSIDE THE PAGE. The bars are subtracted because a fixed masthead and
 * a fixed thumb bar are not content: on a phone they take 145 of 844, and
 * counting them as screen understates every family by the same amount and
 * flatters none. */
const PROBE = () => {
  const H = innerHeight;
  let bars = 0;
  for (const e of document.querySelectorAll('.masthead, .thumbbar')) {
    const pos = getComputedStyle(e).position;
    if (pos === 'fixed' || pos === 'sticky') bars += e.getBoundingClientRect().height;
  }
  const screen = H - bars;
  const spans = [];
  let first = null;
  for (const e of document.querySelectorAll('figure, svg, img, picture, .card-art, .constel, .plate, .yearband')) {
    if (e.tagName.toLowerCase() !== 'svg' && e.closest('svg')) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 40 || r.height < 30) continue;            // a mark is not a picture
    const top = r.top + scrollY;
    if (first === null || top < first) first = top;
    const t = Math.max(r.top, 0), b = Math.min(r.bottom, H);
    if (b > t) spans.push([t, b]);
  }
  spans.sort((a, b) => a[0] - b[0]);
  let painted = 0, end = -1;
  for (const [t, b] of spans) { const s = Math.max(t, end); if (b > s) { painted += b - s; end = b; } }
  const h1 = document.querySelector('h1');
  const head = h1 && h1.closest('.pagehead');
  return {
    share: screen > 0 ? Math.round(1000 * painted / screen) / 10 : 0,
    first: first === null ? null : Math.round(first),
    h1: h1 ? Math.round(parseFloat(getComputedStyle(h1).fontSize)) : null,
    h1top: h1 ? Math.round(h1.getBoundingClientRect().top + scrollY) : null,
    role: head ? ['overture', 'index', 'instrument'].find(r => head.classList.contains(r)) || '—' : '—',
    doc: document.documentElement.scrollHeight,
  };
};

(async () => {
  const wide = process.argv.includes('--wide');
  const asJson = process.argv.includes('--json');
  const srv = serve();
  await new Promise(r => srv.listen(0, r));
  const base = 'http://127.0.0.1:' + srv.address().port;
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({
    viewport: wide ? { width: 1280, height: 900 } : { width: 390, height: 844 } });

  const out = [];
  for (const [name, url] of FAMILIES) {
    const res = await page.goto(base + url, { waitUntil: 'load' });
    if (!res || res.status() !== 200) {
      // A 404 MEASURES 0% AND LOOKS EXACTLY LIKE A FINDING, so it is named
      // as an error rather than reported as a share.
      out.push({ name, url, error: 'HTTP ' + (res ? res.status() : 'none') });
      continue;
    }
    out.push({ name, url, ...(await page.evaluate(PROBE)) });
  }
  await browser.close(); srv.close();

  if (asJson) { console.log(JSON.stringify({ width: wide ? 1280 : 390, pages: out }, null, 1)); return; }

  const bad = out.filter(r => r.error);
  const ok = out.filter(r => !r.error).sort((a, b) => a.share - b.share);
  console.log(`EuropeDoor — the first screen at ${wide ? 1280 : 390}\n`);
  console.log('family'.padEnd(13) + 'role'.padEnd(12) + 'picture'.padStart(8)
              + 'first fig'.padStart(11) + 'h1'.padStart(6) + 'h1 top'.padStart(8) + 'page'.padStart(8));
  for (const r of ok) {
    console.log(r.name.padEnd(13) + r.role.padEnd(12)
      + (r.share + '%').padStart(8)
      + String(r.first === null ? 'none' : r.first).padStart(11)
      + String(r.h1 === null ? '—' : r.h1).padStart(6)
      + String(r.h1top === null ? '—' : r.h1top).padStart(8)
      + String(r.doc).padStart(8));
  }
  const blank = ok.filter(r => r.share === 0).length;
  const thin = ok.filter(r => r.share > 0 && r.share < 20).length;
  console.log(`\n${ok.length} families · ${blank} open with no picture at all · `
            + `${thin} more under a fifth of the screen`);
  const sizes = {};
  for (const r of ok) if (r.h1) sizes[r.h1] = (sizes[r.h1] || 0) + 1;
  console.log('h1 sizes: ' + Object.entries(sizes).sort((a, b) => b[1] - a[1])
    .map(([s, n]) => `${n}×${s}px`).join(', '));
  for (const r of bad) console.log(`\n!! ${r.name} ${r.url} — ${r.error}`);
})();
