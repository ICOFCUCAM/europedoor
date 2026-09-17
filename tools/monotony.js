#!/usr/bin/env node
/* HOW MUCH OF A PAGE IS ONE COMPONENT, REPEATED.
 *
 * "Design to purpose, not to data shape" is the oldest rule in this
 * repository and the one it has broken most often: /experiences shipped 42
 * rows of one component, the stories index shipped nine three-column grids
 * each holding one card, /interests shipped 728 abstract plates, and every
 * gate was green through all of it. Not one instrument here counts REPETITION
 * — they count contrast, weight, overflow, reach, coverage and correctness,
 * and a page can be perfect on every one of those and still be a CMS listing.
 *
 * So this measures the thing: for each rendered family, the share of the
 * page's own height taken by the single most repeated component. A component
 * is a class token; an element is counted once and never inside another
 * element already counted for that token, so a row nested in a rows wrapper
 * does not count twice.
 *
 * IT REPORTS AND IT CAN FAIL. `--check` fails on a page where one component
 * repeated three times or more covers more than the ceiling — because a
 * report nobody reads is exactly how forty-two identical rows shipped past
 * every green gate. The ceiling is high on purpose: a long list IS the right
 * answer on an index whose subject is a set (the 130 quiet destinations, the
 * 50 countries), and what this is written to catch is a page that is NOTHING
 * ELSE.
 *
 * Run it after any redesign, and read the second column as well as the first:
 * a page at 70% one component with two other bands is a list with a frame
 * round it; a page at 70% with nothing else is the fault.
 */
const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path");
const FAM = require("./lib/families.js");
const ROOT = path.join(__dirname, "..", "site");
const MT = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript",
  ".json": "application/json", ".avif": "image/avif", ".webp": "image/webp",
  ".jpg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml",
  ".xml": "application/xml", ".txt": "text/plain" };

// THE CEILING IS THE CURRENT WORST AND IT IS MEANT TO COME DOWN. Measured
// across all 47 rendered families the day this was written, the spread ran
// 63% to 2%: /countries at 63% (nine identical macro bands), an experience
// category at 62% (48 invites), a motion page at 54% (38 rows). Setting it
// at the current worst means it cannot get worse silently; every page
// recomposed under the doctrine lowers it in a diff somebody reads, which is
// the invariant register's discipline applied to composition. A ceiling set
// at where the work should END would be red for a fortnight, and a gate that
// is red for a fortnight is a gate people stop running.
//
// 63 -> 55: /countries' nine macro bands became three rhythms derived from
// each region's own shape in kilometres (4 portrait / 3 upright / 2
// panoramic), and the page's largest repeated composition is 25% with the
// next two at 20 and 8.
//
// 55 -> 52: a motion page's thirty-eight rows became two groups derived
// from the clause each result satisfied — 31% with 8% behind it. And an
// experience category's forty-eight invitations became budget bands (36%
// with 20% behind it, and its sub-category page 31% -> 16%), so the worst
// left is /how-it-works at 52%: three bands with 20% and 12% behind them,
// which is a composition by this report's own diagnostic rather than a
// listing. The pages above it in the table are all ones nobody has
// redesigned — /for-businesses 51%, a macro region 48%, a facet page 46%,
// /fund 45%, /search 42%.
const CEILING = 0.52;

const srv = http.createServer((q, r) => {
  let p = decodeURIComponent(q.url.split("?")[0]);
  let f = path.join(ROOT, p);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) f = path.join(f, "index.html");
  if (!fs.existsSync(f)) { r.statusCode = 404; return r.end("not found"); }
  r.setHeader("content-type", MT[path.extname(f)] || "application/octet-stream");
  r.end(fs.readFileSync(f));
});

(async () => {
  const check = process.argv.includes("--check");
  await new Promise(res => srv.listen(0, res));
  const base = "http://127.0.0.1:" + srv.address().port;
  const b = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
  const rows = [];
  for (const [name, url] of FAM.ALL) {
    const pg = await b.newPage({ viewport: { width: 1280, height: 900 } });
    let m = null;
    try {
      const resp = await pg.goto(base + url, { waitUntil: "load" });
      if (resp && resp.status() === 200) {
        // LAZY IMAGES DO NOT LOAD FOR A FULL-PAGE MEASUREMENT, and a picture
        // that has not laid out is a band with no height.
        await pg.evaluate(async () => {
          for (const i of document.querySelectorAll("img")) i.loading = "eager";
          window.scrollTo(0, document.body.scrollHeight);
          await new Promise(x => setTimeout(x, 250));
          window.scrollTo(0, 0);
          await new Promise(x => setTimeout(x, 150));
        });
        m = await pg.evaluate(() => {
          // A REPEATED COMPONENT IS A RUN OF SIBLINGS WITH THE SAME CLASS
          // ATTRIBUTE, and defining it any other way measures the wrong
          // thing. The first version counted class TOKENS anywhere on the
          // page and reported every plate page at 99% `sheet` — which is
          // true and is the room wrapper, not a listing. A plate sequence is
          // seven siblings that each carry `sheet` and each carry a
          // different composition class, so their full class attributes
          // differ; thirteen theme rows carry the same attribute thirteen
          // times. That difference IS the difference between a composition
          // and a CMS listing, so it is what gets counted — and it needs no
          // list of wrapper names to exclude, which is the kind of guard
          // whoever adds the next wrapper gets to choose.
          const docH = document.documentElement.scrollHeight;
          const main = document.querySelector("main") || document.body;
          // THE DENOMINATOR IS THE PAGE A READER SCROLLS. `main.scrollHeight`
          // reported /map at 2,062px while its own children measured 15,700
          // — an instrument's main is a fixed box whose grid overflows it —
          // so three families came back over 100% and a share over 100% is
          // an instrument saying it does not know what it is dividing by.
          const total = Math.max(
            main.scrollHeight, main.getBoundingClientRect().height,
            document.documentElement.scrollHeight
              - (document.querySelector("footer")?.getBoundingClientRect().height || 0)
              - (document.querySelector("header")?.getBoundingClientRect().height || 0));
          const groups = [];
          const walk = (parent) => {
            const by = new Map();
            for (const e of parent.children) {
              const cls = typeof e.className === "string" ? e.className.trim() : "";
              if (!cls) continue;
              const r = e.getBoundingClientRect();
              if (r.height < 8) continue;
              // A BOX A READER CANNOT SCROLL TO IS NOT PART OF THE PAGE, and
              // /map is the case that needs it: its text twin — the
              // alternative naming all fifty countries and all 319
              // destinations — measured from y=2,087 to y=18,355 inside a
              // 2,665px document, because it sits inside a CLOSED
              // `<details>` whose children Chromium still lays out.
              // Counting it reported /map at 789%. (It is a disclosure and
              // not `display: none`, deliberately: a text version nobody
              // sighted ever sees is a text version that rots. The first
              // version of this comment said "clipped", which is a wrong
              // reason recorded as evidence.) What is outside the scrollable
              // page is outside the measurement.
              if (r.top + window.scrollY > docH) continue;
              // SAME CLASS IS NOT ENOUGH — SAME INNER SHAPE IS. Six
              // `section class="band"` siblings on a country page share a
              // class attribute and contain six different compositions, and
              // the first version reported that page at 76% and /how-it-works
              // at 69%: `band` is `section()`'s wrapper, which is the `sheet`
              // false positive arriving through the older primitive. Thirteen
              // theme rows differ from six sections in that their CONTENTS
              // are the same shape too, and that is what a CMS listing IS. So
              // the key is the class attribute plus a signature of the
              // children's class attributes, and a group is three or more
              // siblings that agree on both.
              const sig = cls + "|" + [...e.children]
                .map(k => (typeof k.className === "string" ? k.className : ""))
                .join(",");
              let rec = by.get(sig);
              if (!rec) { rec = { cls, n: 0, iv: [] }; by.set(sig, rec); }
              rec.n++;
              rec.iv.push([r.top + window.scrollY, r.bottom + window.scrollY]);
            }
            // THE MERGED UNION OF INTERVALS, WHICH IS THE THIRD DEFINITION
            // AND THE FIRST CORRECT ONE.
            //
            // Summing heights reported /macro at 144% and /map at 762%,
            // because nine cards in a three-column grid sit three rows deep
            // and an instrument's layers overlap — a share over 100% is an
            // instrument saying it does not know what it is dividing by.
            // Taking min-top to max-bottom fixed that and overstated the
            // other way: four identical bands SCATTERED through a sequence
            // of thirteen span the whole sequence, so /themes reported 58%
            // for four bands of a run whose other nine are composed
            // differently. Merging the intervals is correct for all three
            // cases at once — side-by-side siblings overlap in y and merge,
            // a contiguous run merges into one band, and a scattered group
            // counts only the page it actually covers.
            for (const rec of by.values()) {
              if (rec.n < 3) continue;
              const iv = rec.iv.slice().sort((a, c) => a[0] - c[0]);
              let covered = 0, [lo, hi] = iv[0];
              for (const [a, c] of iv.slice(1)) {
                if (a <= hi) { hi = Math.max(hi, c); continue; }
                covered += hi - lo; lo = a; hi = c;
              }
              covered += hi - lo;
              groups.push([rec.cls, rec.n, Math.min(1, covered / (total || 1))]);
            }
            for (const e of parent.children) walk(e);
          };
          walk(main);
          groups.sort((a, c) => c[2] - a[2]);
          return { total: Math.round(total), top: groups.slice(0, 3) };
        });
      }
    } catch (e) { m = null; }
    await pg.close();
    if (m && m.top.length) rows.push([name, url, m]);
  }
  await b.close(); srv.close();

  rows.sort((a, c) => c[2].top[0][2] - a[2].top[0][2]);
  console.log("EuropeDoor — one component's share of its own page, at 1280\n");
  console.log("  share  n   component            page      family");
  let bad = 0;
  for (const [name, url, m] of rows) {
    const [t, n, s] = m.top[0];
    const mark = s > CEILING ? "!" : " ";
    if (s > CEILING) bad++;
    console.log(`${mark} ${(s * 100).toFixed(0).padStart(5)}% ${String(n).padStart(3)}  `
                + `${t.slice(0, 20).padEnd(20)} ${String(m.total).padStart(6)}px  ${name}`);
    if (m.top[1]) {
      const rest = m.top.slice(1).map(([a, b2, c]) =>
        `${a} ${(c * 100).toFixed(0)}%`).join(", ");
      console.log(`        then ${rest}`);
    }
  }
  console.log(`\n${rows.length} families measured, ceiling ${(CEILING * 100).toFixed(0)}%`);
  if (check && bad) {
    console.log(`\n${bad} page(s) are one component and little else. `
                + `A page whose composition IS the shape of its data is the `
                + `fault this measures; see docs/redesign-doctrine.md.`);
    process.exit(1);
  }
})();
