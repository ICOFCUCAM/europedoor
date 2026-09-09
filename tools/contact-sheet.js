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
const FAMILIES = [
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

const SCALE = 0.31, COLS = 4, W = 1280, H = 1500;

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

  const browser = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium",
  });
  const page = await browser.newPage({
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
