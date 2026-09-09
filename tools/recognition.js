#!/usr/bin/env node
/* THE RECOGNITION TEST.
 *
 *     python3 -m http.server 8899 --directory site &
 *     node tools/recognition.js [out.png] [--dark] [--phone]
 *
 * Nine families, with the MARK, the WORDMARK and the PAGE TITLE removed, in
 * one field of view. Two questions, in this order:
 *
 *   1. Could someone reasonably identify these as one product?
 *   2. Could someone identify them as EuropeDoor rather than as a generic
 *      premium European travel website?
 *
 * The second is the hard one and it is the standard. Not "does it look
 * professional", not "is it polished", and emphatically not "are all the
 * checks green" — every check in this repository counts something, and none
 * of them counts what a reader sees.
 *
 * Stripping the name is the whole point. A logo in the corner answers
 * question 1 for free and tells you nothing about question 2. What has to
 * carry the identity is the aperture, the two worlds, the projection, the
 * type, the palette and the composition — the things that are still there
 * when the name is gone.
 *
 * Like the contact sheet, this is NOT a gate. It cannot fail. It is for a
 * person to look at.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const os = require("os");
const path = require("path");

const BASE = process.env.BASE || "http://localhost:8899";
const OUT = process.argv[2] && !process.argv[2].startsWith("--")
  ? process.argv[2] : "recognition.png";
const DARK = process.argv.includes("--dark");
const PHONE = process.argv.includes("--phone");

// One per family, chosen so no two are the same KIND of page.
const FAMILIES = [
  ["home", "/"],
  ["country", "/europe/austria/"],
  ["destination", "/europe/austria/tyrol/innsbruck/"],
  ["journey", "/journeys/the-alpine-grand-tour/"],
  ["experience", "/experiences/food/"],
  ["story", "/stories/the-last-forest/"],
  ["index", "/themes/"],
  ["map", "/map/"],
  ["motion", "/europe-in/northern-lights/"],
];

// Everything that answers question 1 for free.
const STRIP = `
  (() => {
    const kill = (sel) => document.querySelectorAll(sel).forEach((e) => e.remove());
    kill(".brand svg, .brand img, .masthead .brand svg");
    document.querySelectorAll(".brand, .brand a, .wordmark").forEach((e) => {
      // keep the box so the masthead does not reflow; empty the name
      [...e.childNodes].forEach((n) => {
        if (n.nodeType === 3) n.textContent = "";
        else if (n.tagName === "SVG" || n.tagName === "svg") n.remove();
        else if (/brandname|wordmark/i.test(n.className || "")) n.remove();
      });
    });
    document.querySelectorAll("a,span,p,div").forEach((e) => {
      if (e.children.length === 0 && /^\\s*europedoor\\s*$/i.test(e.textContent))
        e.textContent = "";
    });
    document.title = "";
  })();
`;

(async () => {
  const scale = PHONE ? 0.62 : 0.31;
  const cols = PHONE ? 5 : 3;
  const W = PHONE ? 390 : 1280;
  const H = PHONE ? 1400 : 1500;

  const browser = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium",
  });
  const page = await browser.newPage({
    viewport: { width: W, height: H },
    colorScheme: DARK ? "dark" : "light",
  });

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "recog-"));
  const shots = [];
  for (const [name, url] of FAMILIES) {
    const r = await page.goto(BASE + url, { waitUntil: "load" });
    if (!r || r.status() !== 200) {
      console.error(`recognition: ${name} ${url} -> ${r ? r.status() : "no response"}`);
      process.exit(1);
    }
    await page.waitForTimeout(500);
    await page.evaluate(STRIP);
    await page.waitForTimeout(120);
    const f = path.join(dir, `${name}.png`);
    await page.screenshot({ path: f });
    shots.push([name, f]);
  }
  await page.close();

  // The sheet carries NO captions either: a label under a cell is a name,
  // and the name is the thing being removed.
  const cells = shots.map(([, f]) =>
    `<figure><img src="file://${f}"></figure>`).join("\n");
  const html = `<!doctype html><meta charset=utf-8><style>
body{margin:0;background:${DARK ? "#3a3a3a" : "#8c8c8c"};display:grid;
     grid-template-columns:repeat(${cols},1fr);gap:10px;padding:10px}
figure{margin:0;overflow:hidden;height:${Math.round(H * scale)}px}
img{width:${W}px;transform:scale(${scale});transform-origin:0 0;display:block}
</style>\n${cells}\n`;
  const sheet = path.join(dir, "sheet.html");
  fs.writeFileSync(sheet, html);

  const shot = await browser.newPage({
    viewport: {
      width: Math.round(W * scale) * cols + 10 * (cols + 1),
      height: Math.ceil(FAMILIES.length / cols) * (Math.round(H * scale) + 10) + 10,
    },
  });
  await shot.goto("file://" + sheet, { waitUntil: "networkidle" });
  await shot.waitForTimeout(600);
  await shot.screenshot({ path: OUT });
  await browser.close();
  fs.rmSync(dir, { recursive: true, force: true });
  console.log(`${FAMILIES.length} families, unnamed → ${OUT}`);
})();
