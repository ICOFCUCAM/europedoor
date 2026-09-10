#!/usr/bin/env node
/* Every discovered candidate, inside the real hero, in one image.
 *
 *     node tools/hero-sheet.js [out.png] [--phone] [--dark]
 *
 * THE STEP THIS EXISTS FOR IS HUMAN ART DIRECTION. Discovery answers what is
 * available and acquisition takes one id; between them is the only question
 * in this pipeline that no check can answer — whether a photograph works in
 * THIS composition. The arch removes both top corners, the masthead sits on
 * the top edge in cobalt, a 60px serif headline and a form sit over the lower
 * half behind a scrim, and the whole thing is a lit opening in a limestone
 * wall. A picture that is lovely in a provider's grid can be unusable here,
 * and the reverse.
 *
 * IT SHOOTS THE TOP OF THE PAGE, NOT THE .herofull ELEMENT, and the first
 * sheet it drew is why. Shooting the element gives the photograph inside its
 * aperture and crops away the two things a reviewer most needs: the cobalt
 * masthead that sits ON the hero's top edge, and the limestone wall the arch
 * is cut into. "Is there anywhere for the masthead to sit" was the question
 * the sheet existed to answer and it was the one thing not in frame — an
 * instrument that removes its own subject.
 *
 * What it shoots is the VIEWPORT — the first screen, exactly as a reader at
 * this width gets it. A clip of "the hero plus a margin" needs a margin, and
 * an invented number is a decision nobody can check; the viewport is the
 * reader's own frame, it is the same for every cell, and it shows the handoff
 * from the opening to whatever is under it. The hero is still measured, but
 * only to refuse a page that has not laid one out.
 *
 * NOTHING HERE RANKS ANYTHING. The cells are in the manifest's order, which
 * is the provider's search order, and the sheet says so on its own face. No
 * cell is highlighted, sorted, starred or defaulted. The id under each cell
 * is the only thing to copy, and copying it is a decision a person makes.
 *
 * It is not a gate. A sheet cannot fail — the same reason contact-sheet.js
 * and plate-variation.py are kept out of the suite — except in one way it
 * MUST: a cell that photographs a 404 looks like a blank hero, which reads as
 * a result. Every page is checked for 200 before anything is drawn.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SCRATCH = process.env.HERO_SHEET_DIR || path.join(ROOT, ".cache", "contact");
const SITE = path.join(ROOT, "site");
const OUT = process.argv.find((a) => a.endsWith(".png")) || "hero-sheet.png";
const PHONE = process.argv.includes("--phone");
const DARK = process.argv.includes("--dark");
/* THE SANDBOX HAS A CHROMIUM AT A FIXED PATH AND A RUNNER HAS NOT, and that
 * difference cost this repository eighty-nine consecutive red CI runs once
 * already. The suites hard-code /opt/pw-browsers/chromium because that is the
 * only build here; on a runner the workflow exports the path of the one
 * Playwright just installed. Falling back silently to a different browser is
 * how two instruments that agree about a drawing disagree about a box. */
const EXE = process.env.HERO_SHEET_EXE || "/opt/pw-browsers/chromium";

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
  ".json": "application/json", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".png": "image/png", ".webp": "image/webp", ".avif": "image/avif",
  ".svg": "image/svg+xml", ".woff2": "font/woff2", ".txt": "text/plain",
};

/* TWO ROOTS, AND THE ORDER MATTERS. The candidate pages live in the scratch
 * directory and every asset they reference — the shipped stylesheet at its
 * content-addressed URL, the scripts, the social cards — lives in site/. A
 * server that only knew the scratch directory would render each candidate
 * unstyled, which would still produce a sheet, and the sheet would be of
 * nothing. */
function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split("?")[0]);
      const candidates = [];
      for (const base of [SCRATCH, SITE]) {
        candidates.push(path.join(base, url), path.join(base, url, "index.html"));
      }
      for (const c of candidates) {
        if (!path.resolve(c).startsWith(SCRATCH) && !path.resolve(c).startsWith(SITE)) continue;
        if (fs.existsSync(c) && fs.statSync(c).isFile()) {
          res.writeHead(200, { "Content-Type": TYPES[path.extname(c)] || "application/octet-stream" });
          return res.end(fs.readFileSync(c));
        }
      }
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("not here");
    });
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

(async () => {
  const manifest = path.join(SCRATCH, "sheet.json");
  if (!fs.existsSync(manifest)) {
    console.error(
      "no sheet to draw. Run, in order:\n" +
      "  python3 scripts/images/discover.py --purpose <p> --query <q> --manifest <f>\n" +
      "  python3 scripts/images/contact_sheet.py --manifest <f>");
    process.exit(1);
  }
  const sheet = JSON.parse(fs.readFileSync(manifest, "utf8"));
  const cells = sheet.cells || [];
  if (!cells.length) { console.error("the sheet has no cells"); process.exit(1); }

  const server = await serve();
  const BASE = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ executablePath: EXE });
  const page = await browser.newPage({
    colorScheme: DARK ? "dark" : "light",
    viewport: { width: PHONE ? 390 : 1280, height: PHONE ? 844 : 900 },
  });

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "hero-sheet-"));
  const missing = [];
  for (const c of cells) {
    const r = await page.goto(BASE + c.url, { waitUntil: "load" });
    if (!r || r.status() !== 200) {
      missing.push(`${c.id} ${c.url} -> ${r ? r.status() : "no response"}`);
      continue;
    }
    await page.waitForTimeout(400);
    const hero = page.locator(".herofull").first();
    if (!(await hero.count())) { missing.push(`${c.id}: no .herofull on the page`); continue; }
    const box = await hero.boundingBox();
    if (!box || box.height < 100) {
      missing.push(`${c.id}: .herofull measured ${box ? Math.round(box.height) : "no"} px tall`);
      continue;
    }
    c.shot = path.join(dir, `${c.id}.png`);
    await page.screenshot({ path: c.shot });
  }
  if (missing.length) {
    await browser.close(); server.close();
    console.error("hero sheet: these did not render —\n  " + missing.join("\n  "));
    process.exit(1);
  }

  /* The caption carries the id, who took it and the native size, and no
   * fourth thing. A "score", a tick or a highlighted cell would be this
   * repository making the one decision it has said all the way through the
   * pipeline that it must not make. */
  const cols = PHONE ? 5 : 3;
  const grid = cells.map((c) => `
    <figure>
      <img src="file://${c.shot}">
      <figcaption><b>${c.id}</b><span>${c.photographer.replace(/</g, "&lt;")}
      · ${c.native}</span></figcaption>
    </figure>`).join("");
  const html = `<!doctype html><meta charset=utf-8><style>
  body{margin:0;background:#14161a;color:#f3f0ea;font:13px/1.5 system-ui,sans-serif;padding:20px}
  header{margin:0 0 16px;max-width:1100px}
  h1{font:600 20px/1.3 system-ui;margin:0 0 6px}
  p{margin:0 0 4px;color:#b9b4aa}
  strong{color:#f3f0ea}
  .grid{display:grid;grid-template-columns:repeat(${cols},1fr);gap:16px}
  figure{margin:0}
  img{width:100%;display:block;background:#000}
  figcaption{display:flex;gap:10px;align-items:baseline;padding:6px 2px}
  b{font:600 15px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.02em}
  span{color:#b9b4aa;font-size:12px}
  </style>
  <header>
    <h1>${sheet.purpose} — candidates in the real hero</h1>
    <p>${sheet.surface}</p>
    <p>${sheet.provider} · query <strong>${(sheet.query || "").replace(/</g, "&lt;")}</strong>
       · searched ${sheet.searched || ""} · shown at ${PHONE ? "390px" : "1280px"},
       ${DARK ? "dark" : "light"} preference</p>
    <p><strong>The order is the provider's search order. It is not a ranking,
       and position here means nothing.</strong> Every one of these meets the
       mechanical minimum for the purpose; which is RIGHT is what you are
       looking for. Copy an id.</p>
  </header>
  <div class="grid">${grid}</div>`;
  const file = path.join(dir, "sheet.html");
  fs.writeFileSync(file, html);

  const shot = await browser.newPage({
    colorScheme: "dark",
    viewport: { width: PHONE ? 1500 : 1560, height: 900 },
  });
  await shot.goto("file://" + file, { waitUntil: "networkidle" });
  await shot.screenshot({ path: OUT, fullPage: true });
  await browser.close();
  server.close();
  fs.rmSync(dir, { recursive: true, force: true });
  console.log(`${cells.length} candidates → ${OUT}` +
              `  (${PHONE ? "390" : "1280"}px, ${DARK ? "dark" : "light"})`);
})();
