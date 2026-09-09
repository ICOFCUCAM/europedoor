#!/usr/bin/env node
/* A contact sheet of one page per family, in one image.
 *
 *     python3 -m http.server 8899 --directory site &
 *     node tools/contact-sheet.js [out.png]
 *
 * LOOK TO FIND, COUNT TO CONCLUDE. This is the "look" half, and it earns its
 * place: the first sheet it produced found that every touch target added the
 * commit before was PAINTING — three grey blobs the size of a region on every
 * country map, and lime saucers over the month and quiet maps — while 51
 * static checks, 777 browser checks, 1,334 section assertions and 26
 * invariants were green. `.minidot .hit` is specificity (0,2,0) and
 * `.minimap.arched .minidot circle` is (0,3,1). Nothing that counts things
 * was ever going to see it.
 *
 * It is not in the gates. A sheet cannot fail, and a gate that cannot fail is
 * a gate people stop running — the same reason plate-variation.py is kept
 * out. This is for a person to look at, after a visual change, on purpose.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const os = require("os");
const path = require("path");

const BASE = process.env.BASE || "http://localhost:8899";
const OUT = process.argv[2] || "contact-sheet.png";

// One exemplar per rendered family. Add a row when a family appears; the
// point of the sheet is that every family is in one field of view.
// --more shoots the OTHER twelve: the families the first sheet does not
// include, which is exactly the set nobody had looked at.
const MORE = [
  ["macro", "/countries/"],
  ["place", "/europe/austria/vienna-and-the-east/vienna/place/schonbrunn/"],
  ["facet", "/europe/austria/vienna-and-the-east/vienna/things-to-do/"],
  ["interest", "/interests/mountains/"],
  ["experiences", "/experiences/"],
  ["category", "/experiences/food/"],
  ["how it works", "/how-it-works/"],
  ["fund project", "/fund/"],
  ["method", "/method/"],
  ["about", "/about/"],
  ["manifesto", "/manifesto/"],
  ["sources", "/sources/"],
];

const FAMILIES = process.argv.includes("--more") ? MORE : [
  ["home", "/"],
  ["country", "/europe/austria/"],
  ["region", "/europe/austria/tyrol/"],
  ["destination", "/europe/austria/tyrol/innsbruck/"],
  ["journey", "/journeys/the-alpine-grand-tour/"],
  ["motion", "/europe-in/northern-lights/"],
  ["month", "/events/oct/"],
  ["stories", "/stories/"],
  ["themes", "/themes/"],
  ["quiet", "/beyond-the-obvious/"],
  ["map", "/map/"],
  ["plan", "/plan/"],
];

// --phone shoots the same twelve at 390px, which is the width most readers
// have and the one this programme kept measuring and never LOOKING at. The
// scale is higher because the frame is narrower; the sheet stays one image.
const PHONE = process.argv.includes("--phone");
const SCALE = PHONE ? 0.62 : 0.31, COLS = PHONE ? 6 : 4;
const W = PHONE ? 390 : 1280, H = PHONE ? 1400 : 1500;

(async () => {
  const cells = FAMILIES.map(
    ([name, url]) =>
      `<figure><figcaption>${name}</figcaption>` +
      `<iframe src="${BASE}${url}" loading="eager"></iframe></figure>`
  ).join("\n");
  const html = `<!doctype html><meta charset=utf-8><style>
body{margin:0;background:#888;font:11px system-ui;display:grid;
     grid-template-columns:repeat(${COLS},1fr);gap:8px;padding:8px}
figure{margin:0;background:#fff;overflow:hidden;position:relative;
       height:${Math.round(H * SCALE)}px}
iframe{width:${W}px;height:${H}px;border:0;transform:scale(${SCALE});
       transform-origin:0 0;display:block}
figcaption{position:absolute;top:0;left:0;background:#111;color:#fff;
           padding:2px 6px;z-index:9;font-weight:700}
</style>\n${cells}\n`;

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sheet-"));
  const file = path.join(dir, "sheet.html");
  fs.writeFileSync(file, html);

  // --dark shoots the same sheet in the dark colour-scheme preference.
  // DISCOVER is limestone and INTELLIGENCE is graphite in BOTH preferences
  // by design — the world says where the reader is, not how they like their
  // screen — so the two sheets should differ only where the stylesheet
  // deliberately answers prefers-color-scheme.
  const dark = process.argv.includes("--dark");
  // A SHEET THAT PHOTOGRAPHS A 404 LOOKS LIKE A BLANK PAGE.
  // The second sheet carried /experiences/food-and-drink, which does not
  // exist — the route is /experiences/food — and the cell rendered as an
  // empty white rectangle with the server's error text at 31% scale. That is
  // the same failure as a suite that stops counting: the output looks like a
  // result. Every URL is checked before anything is drawn.
  const browser0 = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium",
  });
  const probe = await browser0.newPage();
  const missing = [];
  for (const [name, url] of FAMILIES) {
    const r = await probe.goto(BASE + url, { waitUntil: "commit" });
    if (!r || r.status() !== 200) missing.push(`${name} ${url} -> ${r ? r.status() : "no response"}`);
  }
  await browser0.close();
  if (missing.length) {
    console.error("contact sheet: these are not pages —\n  " + missing.join("\n  "));
    process.exit(1);
  }

  const browser = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium",
  });
  const page = await browser.newPage({
    colorScheme: dark ? "dark" : "light",
    viewport: {
      width: Math.round(W * SCALE) * COLS + 8 * (COLS + 1),
      height: Math.ceil(FAMILIES.length / COLS) * (Math.round(H * SCALE) + 8) + 8,
    },
  });
  // file:// so the iframes are same-origin-free and the sheet itself is not
  // served from the site being photographed.
  await page.goto("file://" + file, { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: OUT });
  await browser.close();
  fs.rmSync(dir, { recursive: true, force: true });
  console.log(`${FAMILIES.length} families → ${OUT}`);
})();
