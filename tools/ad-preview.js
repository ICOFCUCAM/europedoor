#!/usr/bin/env node
/* The simulated paid bands, shot inside the real pages.
 *
 *     python3 tools/ad-preview.py && node tools/ad-preview.js
 *
 * NOT A GATE. It writes images and asserts nothing, because the question it
 * exists for is whether a sponsored band reads as bought rather than as
 * editorial, and no count can answer that. The pages come from
 * `.cache/ad-preview` and everything else — the stylesheet, the maps, the
 * photographs — is served from `site/`, so what is photographed is the real
 * page with one band added and nothing else changed.
 *
 * It refuses a page that is not 200 and a page with no band, for the reason
 * the contact sheet refuses a 404: a blank cell still looks like a result.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const http = require("http");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const ROOTS = [path.join(ROOT, ".cache", "ad-preview"), path.join(ROOT, "site")];
const EXE = process.env.HERO_SHEET_EXE || "/opt/pw-browsers/chromium";
const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
  ".json": "application/json", ".jpg": "image/jpeg", ".png": "image/png",
  ".webp": "image/webp", ".avif": "image/avif", ".svg": "image/svg+xml",
};
const PAGES = [["home", "/"], ["bergen", "/europe/norway/fjord-norway/bergen"]];

(async () => {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split("?")[0]);
    for (const base of ROOTS) {
      for (const c of [path.join(base, url), path.join(base, url, "index.html")]) {
        if (fs.existsSync(c) && fs.statSync(c).isFile()) {
          res.writeHead(200, { "Content-Type": TYPES[path.extname(c)] || "application/octet-stream" });
          return res.end(fs.readFileSync(c));
        }
      }
    }
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("not here");
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const BASE = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ executablePath: EXE });
  const out = [];
  for (const [name, url] of PAGES) {
    for (const [suffix, viewport] of [
      ["wide", { width: 1280, height: 900 }],
      ["phone", { width: 390, height: 844 }],
    ]) {
      const page = await browser.newPage({ viewport });
      const r = await page.goto(BASE + url, { waitUntil: "networkidle" });
      if (r.status() !== 200) throw new Error(`${url} answered ${r.status()}`);
      const band = page.locator(".adband").first();
      if (!(await band.count())) throw new Error(`${url} drew no paid band`);
      /* LAZY IMAGES DO NOT LOAD FOR A SCREENSHOT TAKEN WITHOUT SCROLLING,
       * which this repository already records: `loading="lazy"` keys on the
       * viewport, so a band below the fold photographs as empty boxes and an
       * empty box under a scrim looks exactly like a missing photograph. */
      await band.scrollIntoViewIfNeeded();
      await page.waitForTimeout(400);
      const file = `ad-preview-${name}-${suffix}.png`;
      /* The band AND what is above it, because the question is whether a
       * reader can tell the two apart — a photograph of the band alone
       * answers "is it legible" and not "is it distinguishable". */
      await page.screenshot({ path: file, clip: await (async () => {
        const b = await band.boundingBox();
        const top = Math.max(0, b.y - 360);
        return { x: 0, y: top, width: viewport.width, height: Math.min(b.y + b.height + 40 - top, 1400) };
      })() });
      out.push(file);
      await page.close();
    }
  }
  await browser.close();
  server.close();
  console.log(out.join("\n"));
})();
