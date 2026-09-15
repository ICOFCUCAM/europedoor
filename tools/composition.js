#!/usr/bin/env node
/* FINDING 2, MEASURED — "the site has one composition, rendered 1,033 times".
 *
 *     node tools/composition.js          the shapes, grouped
 *     node tools/composition.js --json   for a diff between two runs
 *
 * `docs/first-class-audit.md` asserts that above the fold the families are
 * interchangeable, and it measured exactly one half of that: the size and
 * the vertical position of the h1. That half was real and it has been
 * answered — the three head roles, and the drawings that came up into the
 * heads. What nobody had ever measured is the OTHER half, which is what the
 * claim actually says: that below the head every family is the same page.
 *
 * So this reads two things per family and nothing else:
 *
 *   the HEAD    its role, the h1's size and top, the head's own height, and
 *               how much of its width its content reaches — a head that uses
 *               57% of its column is an overture with nothing beside the
 *               name, and one that reads 144% is carrying a drawing wider
 *               than the type.
 *   the BODY    the ordered sequence of band shapes under it, reduced to a
 *               vocabulary of seven: rows, cards, figure, facts, list, note
 *               and the head itself. Consecutive repeats are collapsed,
 *               because "rows rows rows" and "rows" are the same composition
 *               with a different amount of content in it.
 *
 * IT IS NOT A GATE AND MUST NOT BECOME ONE, for the same reason
 * `tools/opening.js` is not: the fault it exists to find is a page that is
 * DULL, and a threshold on "distinct shapes" is a number to satisfy by
 * shuffling bands. It reports. The eye decides whether a shape is the right
 * one; this says how many there are.
 *
 * THE VOCABULARY IS READ OFF THE CLASSES THE PRIMITIVES EMIT, which is the
 * only reading that is the same everywhere — `docs/frontend-architecture.md`
 * says eleven primitives cover 100% of the site, so a band that is not one
 * of them is a band worth seeing in this output.
 */
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');

const ROOT = path.join(__dirname, '..', 'site');
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif',
  '.xml': 'application/xml', '.txt': 'text/plain' };

const { ALL } = require('./lib/families.js');
const JSON_OUT = process.argv.includes('--json');
const W = 1280;

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
  const main = document.querySelector('main');
  const kinds = [];
  /* A BAND IS NAMED BY THE PRIMITIVE INSIDE IT, NOT BY ITS OWN TAG. Every
   * band on this site is a <section> or a bare <div> wrapping one of the
   * eleven primitives, so recursing until a primitive's class is found is
   * what keeps `<section class="band">` from being a shape of its own. */
  const walk = (el) => {
    for (const c of el.children) {
      const cl = (c.className || '').toString();
      if (/\bpagehead\b/.test(cl)) { kinds.push('HEAD'); continue; }
      /* A BAND'S OWN HEADING IS PART OF THE BAND. `section()` emits a
       * `.band-head` holding the h2 and its lede beside the primitive, so
       * without this every single band read as "prose rows" and /destination
       * came back with nine prose bands it does not have. */
      if (/\bband-head\b/.test(cl)) continue;
      if (/\brows\b/.test(cl)) { kinds.push('rows'); continue; }
      if (/\bgrid\b/.test(cl)) { kinds.push('cards'); continue; }
      if (/\bnote\b/.test(cl)) { kinds.push('note'); continue; }
      if (c.tagName === 'FIGURE' || c.querySelector(':scope > svg')) { kinds.push('figure'); continue; }
      if (/\bfact/.test(cl)) { kinds.push('facts'); continue; }
      if (c.tagName === 'OL' || c.tagName === 'UL') { kinds.push('list'); continue; }
      if (['SECTION', 'DIV', 'NAV', 'ARTICLE'].includes(c.tagName)) {
        const before = kinds.length;
        walk(c);
        /* A BAND OF PROSE IS A SHAPE, AND THE FIRST VERSION COULD NOT SEE
         * ONE. Skipping <p> and <h2> made /manifesto, /404 and /search all
         * read as "HEAD" and nothing else — three pages made almost entirely
         * of set text, reported as empty. An instrument that cannot see the
         * commonest band on the prose families is measuring the wrong site. */
        if (kinds.length === before && c.querySelector(':scope > p, :scope > h2'))
          kinds.push('prose');
      }
    }
  };
  walk(main);

  const h = document.querySelector('.pagehead');
  let head = null;
  if (h) {
    const H = h.getBoundingClientRect();
    let far = 0;
    for (const e of h.querySelectorAll('*')) {
      const r = e.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      if (e.children.length && !e.textContent.trim()
          && !e.querySelector('svg,img,picture') && e.tagName !== 'svg') continue;
      if (r.right > far) far = r.right;
    }
    const h1 = document.querySelector('.pagehead h1');
    head = {
      role: ['overture', 'index', 'instrument'].find((r) =>
        (h.className || '').toString().split(' ').includes(r)) || '—',
      h1: h1 ? Math.round(parseFloat(getComputedStyle(h1).fontSize)) : 0,
      h1top: h1 ? Math.round(h1.getBoundingClientRect().top + scrollY) : 0,
      height: Math.round(H.height),
      used: Math.round(100 * (far - H.left) / H.width),
    };
  }
  /* COLLAPSED. Three `rows` bands in a row and one `rows` band are the same
   * composition holding different amounts of content, and counting them
   * apart would report /countries' nine identical bands as the most varied
   * page on the site. */
  const body = kinds.filter((k, i) => k !== kinds[i - 1]).join(' ');
  return { head, body };
};

(async () => {
  const srv = serve().listen(0);
  const base = 'http://127.0.0.1:' + srv.address().port;
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: W, height: 900 } });
  const rows = [];
  for (const [name, url] of ALL) {
    const r = await page.goto(base + url, { waitUntil: 'load' });
    if (!r || r.status() !== 200) { console.error('NOT 200 ' + url); continue; }
    rows.push(Object.assign({ name, url }, await page.evaluate(PROBE)));
  }
  await browser.close();
  srv.close();

  if (JSON_OUT) { console.log(JSON.stringify({ width: W, pages: rows }, null, 1)); return; }

  const byShape = new Map();
  for (const r of rows) {
    if (!byShape.has(r.body)) byShape.set(r.body, []);
    byShape.get(r.body).push(r.name);
  }
  console.log(`\n  BODY SHAPES at ${W} — ${byShape.size} distinct over ${rows.length} families\n`);
  for (const [shape, names] of [...byShape].sort((a, b) => b[1].length - a[1].length)) {
    console.log('  ' + String(names.length).padStart(2) + '  ' + (shape || '(nothing under the head)'));
    console.log('      ' + names.join(', '));
  }

  console.log(`\n  HEADS at ${W}\n`);
  console.log('      role        h1   top   height  width used   family');
  for (const r of rows.filter((x) => x.head).sort(
      (a, b) => a.head.used - b.head.used || a.head.height - b.head.height)) {
    const h = r.head;
    console.log('      ' + h.role.padEnd(11) + String(h.h1).padStart(2) +
                String(h.h1top).padStart(6) + String(h.height).padStart(8) +
                String(h.used + '%').padStart(12) + '   ' + r.name);
  }
  const sizes = new Set(rows.filter((x) => x.head).map((x) => x.head.h1));
  const tops = rows.filter((x) => x.head).map((x) => x.head.h1top);
  console.log(`\n  h1 sizes in use: ${[...sizes].sort((a, b) => a - b).join(', ')}` +
              `   h1 top ranges ${Math.min(...tops)}–${Math.max(...tops)}\n`);
})();
