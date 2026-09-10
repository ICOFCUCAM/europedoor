#!/usr/bin/env node
/* The built homepage, as shipped, with whatever the register now holds.
 *
 *     node tools/hero-shot.js [out-prefix]   # writes -wide.png and -phone.png
 *
 * THE LAST STEP BEFORE A MERGE IS A PERSON LOOKING AGAIN. The contact sheet
 * answers "which of these", from previews; this answers "and it actually
 * works", from the real derivatives, the real widths and the real page that
 * every gate has just passed. They are different questions and the second one
 * has been wrong before while every count was green: the hero once shipped as
 * a 1280x736 hole because the derivatives were registered, referenced and
 * never copied into site/, and <picture> does not fall back once a <source>
 * has matched.
 *
 * So this shoots what the build produced, at both widths, and the workflow
 * attaches it to the pull request. It asserts nothing — looking is the step.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const http = require("http");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SITE = path.join(ROOT, "site");
const PREFIX = process.argv[2] || "hero-shot";
const EXE = process.env.HERO_SHEET_EXE || "/opt/pw-browsers/chromium";
const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
  ".json": "application/json", ".jpg": "image/jpeg", ".png": "image/png",
  ".webp": "image/webp", ".avif": "image/avif", ".svg": "image/svg+xml",
};

(async () => {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split("?")[0]);
    for (const c of [path.join(SITE, url), path.join(SITE, url, "index.html")]) {
      if (fs.existsSync(c) && fs.statSync(c).isFile()) {
        res.writeHead(200, { "Content-Type": TYPES[path.extname(c)] || "application/octet-stream" });
        return res.end(fs.readFileSync(c));
      }
    }
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("not here");
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const BASE = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ executablePath: EXE });

  /* A 404 UNDER THE PHOTOGRAPH IS THE FAILURE THIS IS FOR, and a screenshot
   * of it looks like a design decision. Every request the page makes is
   * recorded, so a missing derivative is named rather than photographed. */
  const missed = [];
  for (const [suffix, viewport] of [
    ["wide", { width: 1280, height: 900 }],
    ["phone", { width: 390, height: 844 }],
  ]) {
    const page = await browser.newPage({ viewport });
    page.on("response", (r) => { if (r.status() >= 400) missed.push(`${r.status()} ${r.url()}`); });
    await page.goto(BASE + "/", { waitUntil: "networkidle" });
    await page.locator(".herofull").first().screenshot({ path: `${PREFIX}-${suffix}.png` });
    await page.close();
  }
  await browser.close();
  server.close();
  if (missed.length) {
    console.error("the homepage asked for things that are not there —\n  " +
                  [...new Set(missed)].join("\n  "));
    process.exit(1);
  }
  console.log(`${PREFIX}-wide.png and ${PREFIX}-phone.png`);
})();
