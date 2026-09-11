/* THE HOSTED DESK'S SCREENS, RENDERED AND MEASURED.
 *
 *     node tools/desk-render.js
 *
 * `tools/hosted-desk-tests.js` proves the BOUNDARY — sessions, signatures,
 * refusals — and deliberately never opens a browser. Neither suite would have
 * seen any of the six defects the local desk's screens had, and every one of
 * them was the same kind: present, correctly wired, and unusable. A hidden
 * screen that laid itself out. A label rendered beside the wrong control with
 * `for=` correct throughout. A confirmation dialogue whose confirm button was
 * off the bottom. Sign out off the right edge at 390.
 *
 * So this is the §27 render pass, with a STUBBED api: the pages are the real
 * files, the layout is the real stylesheet, and every response is fabricated
 * here rather than fetched, so it reaches no provider, holds no key and
 * dispatches nothing.
 *
 * It is a suite rather than a contact sheet on purpose: a sheet cannot fail,
 * and a gate that cannot fail is a gate people stop running.
 */

import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PUB = path.join(path.dirname(HERE), "desk", "public");
const REG = JSON.parse(fs.readFileSync(
  path.join(path.dirname(HERE), "desk", "registry.json"), "utf8"));

let passed = 0;
const failures = [];
const ok = (cond, msg) => { if (cond) passed += 1; else failures.push(msg); };

/* A 1x1 JPEG, so a candidate has an image to lay out without this file
   reaching a provider for one. */
const PIXEL = Buffer.from(
  "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
  + "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAA"
  + "AAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==", "base64");

/* THE CANDIDATES ARE FABRICATED HERE, and one of them carries no `alt`,
   because "the photograph has no description from the photographer" is a
   state the panel has to render and the provider decides when it happens. */
const CANDIDATES = [
  { id: "17241175", photographer: "Daniel Shipilov",
    photographer_url: "https://example.invalid/@d",
    page: "https://example.invalid/photo/1",
    width: 12000, height: 9000, aspect: 1.333,
    alt: "A vibrant view of colorful waterfront houses in Trondheim, Norway "
       + "under overcast skies.",
    thumb: "t1", suits: true, why_not: [], already: [] },
  { id: "26800043", photographer: "Batuhan K",
    photographer_url: "https://example.invalid/@b",
    page: "https://example.invalid/photo/2",
    width: 7728, height: 5152, aspect: 1.5,
    alt: "", thumb: "t2", suits: true, why_not: [], already: [] },
  { id: "99", photographer: "Someone", photographer_url: "https://example.invalid/@s",
    page: "https://example.invalid/photo/3", width: 800, height: 600, aspect: 1.333,
    alt: "too small for this slot", thumb: "t3", suits: false,
    why_not: ["800px wide, and this slot needs 2000 native pixels — "
            + "derive.py refuses to upscale"], already: [] },
];

function serve() {
  return new Promise((res) => {
    const s = http.createServer((req, rq) => {
      const u = new URL(req.url, "http://d");
      const send = (code, body, type) => {
        rq.writeHead(code, { "Content-Type": type });
        rq.end(body);
      };
      if (u.pathname === "/api/session") return send(200, '{"signed_in":true}', "application/json");
      if (u.pathname === "/api/registry") {
        /* The real registry, with every row EMPTY — which is the state the
           product is actually in, and the state the library has to render. */
        return send(200, JSON.stringify({
          providers: REG.providers, slots: REG.slots,
          purposes: REG.purposes.map((p) => ({ ...p, status: "EMPTY", photograph: null })),
        }), "application/json");
      }
      if (u.pathname === "/api/search") {
        return send(200, JSON.stringify({
          candidates: CANDIDATES,
          surface: "The opening of the atlas index — a wide editorial image "
                 + "beside the headline.",
          needs: { min_width: 2000, orientation: "landscape",
                   min_aspect: 1.3, max_aspect: 2.1 },
          order: "the provider's own search order, carrying no judgement",
        }), "application/json");
      }
      if (u.pathname === "/api/thumb") return send(200, PIXEL, "image/jpeg");
      /* The browser asks for one unprompted and a 404 is a console error,
         which this suite counts. The real deployment serves its own. */
      if (u.pathname === "/favicon.ico") { rq.writeHead(204); return rq.end(); }
      const f = path.join(PUB, u.pathname === "/" ? "index.html" : u.pathname.slice(1));
      if (f.startsWith(PUB) && fs.existsSync(f) && fs.statSync(f).isFile()) {
        const type = f.endsWith(".css") ? "text/css"
                   : f.endsWith(".js") ? "text/javascript" : "text/html";
        return send(200, fs.readFileSync(f), type + "; charset=utf-8");
      }
      send(404, "not found", "text/plain");
    });
    s.listen(0, "127.0.0.1", () => res(s));
  });
}

/* A document that scrolls sideways is the defect this repository has now
   recorded four times, in four components. */
const overflows = (page) => page.evaluate(() =>
  document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);

/* NO ELEMENT MAY HOLD MORE TEXT THAN IT SHOWS. The same assertion the site's
   own suite makes, because the sticky phone action cut its place name on 146
   destination pages and every count was green. */
const clipped = (page) => page.evaluate(() => {
  const bad = [];
  for (const el of document.querySelectorAll("body *")) {
    if (!el.offsetParent && el.tagName !== "BODY") continue;
    if (el.children.length) continue;
    /* AN EMPTY FIELD IS NOT CUT-OFF TEXT, and the first run of this check
       reported one. A text input's scrollWidth exceeds its clientWidth by a
       caret's worth whether or not anything is in it, so the test is about
       TEXT: what is the element showing, and is there more of it. An input
       holding nothing is showing all of nothing. */
    const text = el.tagName === "INPUT" ? el.value : (el.textContent || "");
    if (!text.trim()) continue;
    if (el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== "auto") {
      bad.push(`${el.tagName}.${el.className} "${text.slice(0, 40)}"`);
    }
  }
  return bad;
});

const server = await serve();
const base = `http://127.0.0.1:${server.address().port}`;
const candidates = [
  process.env.CHROMIUM_PATH,
  "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
  "/opt/pw-browsers/chromium/chrome-linux/chrome",
].filter(Boolean).filter((p) => fs.existsSync(p));
const browser = await chromium.launch(
  candidates.length ? { executablePath: candidates[0] } : {});

const errors = [];

for (const width of [1280, 390]) {
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  page.on("pageerror", (e) => errors.push(`${width}: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errors.push(`${width}: ${m.text()}`); });
  await page.goto(base + "/", { waitUntil: "networkidle" });

  ok(await page.locator("#desk").isVisible(), `${width}: the desk did not open`);
  ok(await page.locator("#gate").isHidden(), `${width}: the sign-in screen is laid out behind the desk`);
  ok(!(await overflows(page)), `${width}: the document scrolls sideways`);

  /* ── the country field, which is what this pass was written for ── */
  const opts = await page.locator("#country option").count();
  ok(opts > 40, `${width}: the country select holds ${opts} options`);
  ok(await page.locator("#country-wrap").isHidden(),
     `${width}: a declared purpose was offered a country it does not have`);

  await page.selectOption("#slot", "destination-hero");
  ok(await page.locator("#country-wrap").isVisible(),
     `${width}: destination-hero was not offered a country`);
  const all = await page.locator("#targets option").count();
  await page.selectOption("#country", "norway");
  const few = await page.locator("#targets option").count();
  ok(few > 0 && few < all,
     `${width}: choosing Norway narrowed ${all} targets to ${few}`);
  const first = await page.locator("#targets option").first().getAttribute("value");
  ok((first || "").startsWith("norway/"),
     `${width}: the narrowed list starts with ${first}`);

  /* A COUNTRY THAT IS STILL SET WHEN THE SLOT CHANGES MUST NOT STRAND A
     TARGET FROM THE OLD ONE. */
  await page.fill("#target", first);
  await page.selectOption("#slot", "place-hero");
  const kept = await page.inputValue("#target");
  ok(kept === "" || kept.startsWith("norway/"),
     `${width}: changing the slot left ${kept} in the target field`);

  /* ── the sheet, and the alt panel ── */
  await page.selectOption("#slot", "countries-hero");
  await page.fill("#q", "norway");
  await page.click("#find button[type=submit]");
  await page.waitForSelector(".cand");
  ok(await page.locator(".cand").count() === 3, `${width}: the sheet drew the wrong number of candidates`);
  ok(await page.locator(".cand button.go").count() === 2,
     `${width}: a candidate that does not meet the slot was offered Acquire`);
  ok(!(await overflows(page)), `${width}: the sheet makes the document scroll sideways`);

  await page.locator(".cand button.go").first().click();
  await page.waitForSelector("dialog[open] #alt");
  ok(await page.locator("#alt-suggest .chip").isVisible(),
     `${width}: no suggestion was offered for a candidate that has one`);
  ok((await page.inputValue("#alt")) === "",
     `${width}: the alt field was PREFILLED — a prefilled alt is one nobody reads`);

  /* THE WARNING IS THE POINT: the hint says "not the place name" and the
     first acquisition typed exactly that, one line under it. */
  await page.fill("#alt", "Norway");
  ok(await page.locator("#alt-warn").isVisible(),
     `${width}: typing the place name raised no warning`);
  await page.locator("#alt-suggest .chip").click();
  const taken = await page.inputValue("#alt");
  ok(taken.startsWith("A vibrant view"),
     `${width}: the suggestion did not fill the field (${taken.slice(0, 30)})`);
  ok(await page.locator("#alt-warn").isHidden(),
     `${width}: the warning stayed up after a real description was taken`);

  /* A CONFIRMATION WHOSE CONFIRM BUTTON CANNOT BE SEEN IS NOT A
     CONFIRMATION — the defect adding the photograph to this dialogue caused
     the first time. */
  for (const id of ["#ack-go", "#alt"]) {
    const box = await page.locator(id).boundingBox();
    ok(box && box.y >= 0 && box.y + box.height <= 900 + 1,
       `${width}: ${id} is outside the viewport at y=${box && Math.round(box.y)}`);
  }
  await page.keyboard.press("Escape");

  /* ── the library, scoped to a country ── */
  await page.click('[data-view="library"]');
  await page.waitForSelector("#lib .slotrow");
  const wide = (await page.textContent("#lib-count")) || "";
  ok(/593/.test(wide), `${width}: the library count is not the whole set: ${wide}`);
  await page.selectOption("#lib-country", "norway");
  const narrow = (await page.textContent("#lib-count")) || "";
  ok(/Norway/.test(narrow) && !/593/.test(narrow),
     `${width}: the scoped count still reports the whole set: ${narrow}`);
  const rows = await page.locator("#lib .slotrow").count();
  ok(rows > 0 && rows < 100, `${width}: Norway listed ${rows} slots`);
  ok(!(await overflows(page)), `${width}: the library makes the document scroll sideways`);

  const cut = await clipped(page);
  ok(cut.length === 0, `${width}: text is cut off in ${cut.length}: ${cut.slice(0, 3).join(" | ")}`);

  await page.close();
}

await browser.close();
server.close();

ok(errors.length === 0, "the page logged errors: " + errors.slice(0, 3).join(" | "));

console.log("EuropeDoor — the hosted Media Desk, rendered\n");
if (failures.length) {
  console.log(`${failures.length} failure(s):`);
  for (const f of failures) console.log("  - " + f);
  console.log(`\n${passed} passed, ${failures.length} failed`);
  process.exit(1);
}
console.log(`all ${passed} render checks passed at 1280 and 390.`);
