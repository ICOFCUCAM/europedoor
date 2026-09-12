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

/* Four real Norwegian destination surfaces out of the registry, so the sweep
   stub answers about the same entities the registry holds. */
const SWEEP_TARGETS = REG.purposes
  .filter((p) => p.slot === "destination-hero" && p.country === "norway")
  .slice(0, 4)
  .map((p) => ({
    target: p.target, surface: p.surface,
    name: (/of the (.+?) destination page/.exec(p.surface) || [, p.target])[1],
  }));

const DISPATCHED = [];

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
          dispatch: { repo: "ICOFCUCAM/europedoor", branch: "main",
                      workflow: "photograph.yml" },
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
      if (u.pathname === "/api/sweep") {
        const rows = SWEEP_TARGETS.map((t, i) => ({
          purpose: "destination-hero@" + t.target,
          surface: t.surface, target: t.target, query: t.name,
          /* ONE SURFACE WITH NOTHING OFFERED, because a grid that silently
             omits it reads as a complete answer about the country. */
          candidate: i === 1 ? null : {
            id: String(700000 + i), photographer: "Someone " + i,
            photographer_url: "https://example.invalid/@s",
            page: "https://example.invalid/p/" + i,
            width: 4000, height: 2400,
            /* AND ONE WITH NO DESCRIPTION, which must not be acquirable
               until somebody writes one. */
            alt: i === 2 ? "" : `A ${t.name} photograph, described by the `
                              + `photographer who took it.`,
            thumb: "t" + i, alternatives: 2,
          },
          why_none: i === 1 ? "nothing in this provider's first page of "
                            + "results for this name meets the slot" : "",
        }));
        return send(200, JSON.stringify({
          rows, stopped: "", surfaces: rows.length, swept: rows.length,
          needs: { min_width: 1800, orientation: "landscape",
                   min_aspect: 1.5, max_aspect: 2.4 },
          order: "each row is the provider's own first result for that "
               + "surface's own name that meets the slot.",
        }), "application/json");
      }
      /* FILL THE LIBRARY. Three rows from three different families, because
         the one thing this button promises that the sweep does not is that a
         press covers every category rather than one country. */
      if (u.pathname === "/api/topup") {
        const rows = [
          ["theme-hero@medieval-europe", "Medieval Europe theme"],
          ["country-hero@austria", "Austria country"],
          ["interest-hero@architecture", "Architecture interest"],
        ].map(([purpose, name], i) => ({
          purpose,
          surface: `The opening band of the ${name} page.`,
          target: purpose.split("@")[1],
          query: name,
          candidate: {
            id: String(800000 + i), photographer: "Filler " + i,
            photographer_url: "https://example.invalid/@f",
            page: "https://example.invalid/f/" + i,
            width: 5000, height: 3000,
            alt: `A ${name} photograph, described by the photographer.`,
            thumb: "f" + i,
          },
        }));
        return send(200, JSON.stringify({
          rows, stopped: "", empty: 826, looked: 3, cap: 60,
          covered: ["country-hero", "interest-hero", "theme-hero"],
          order: "one surface from each family in turn.",
        }), "application/json");
      }
      if (u.pathname === "/api/acquire") {
        let raw = "";
        req.on("data", (c) => { raw += c; });
        return req.on("end", () => {
          let b = {};
          try { b = JSON.parse(raw || "{}"); } catch { b = {}; }
          DISPATCHED.push(b);
          send(200, JSON.stringify({ job: "stub-job", count: (b.batch || []).length }),
               "application/json");
        });
      }
      if (u.pathname === "/api/status") {
        return send(200, JSON.stringify({ state: "running", steps: [], run: "" }),
                    "application/json");
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
/* A <dialog> LEFT OPEN SWALLOWS EVERY CLICK AFTER IT, and Escape closes only
   one the browser considers focused — which, after a programmatic click on a
   button inside it, it may not. Closing them by name is the reliable form,
   and a suite that moves between screens has to do it deliberately. */
const closeDialogs = (page) => page.evaluate(() => {
  document.querySelectorAll("dialog[open]").forEach((d) => d.close());
});

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

/* A CRASH MID-RUN MUST STILL PRINT WHAT WAS ALREADY FOUND. Removing the
   `dialog:not([open])` guard makes an invisible panel swallow every click
   after it, so the suite died on a 30-second timeout — and the assertion that
   had ALREADY caught the real fault, at the top of the run, was never
   printed. A red run that cannot say why is the failure this repository
   records one level up: a message with no measurement in it cannot be
   diagnosed. */
for (const width of [1280, 390]) {
  try {
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  page.on("pageerror", (e) => errors.push(`${width}: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errors.push(`${width}: ${m.text()}`); });
  await page.goto(base + "/", { waitUntil: "networkidle" });

  ok(await page.locator("#desk").isVisible(), `${width}: the desk did not open`);
  /* WHERE AN ACQUISITION WILL RUN, ON THE SCREEN. A target the editor cannot
     see is a target nobody checks, and the first real batch was refused by
     GitHub for an input the target branch had never heard of. */
  ok(/ICOFCUCAM\/europedoor · main/.test(
       await page.textContent("#target-branch") || ""),
     `${width}: the masthead does not say which branch a dispatch goes to`);
  ok(await page.locator("#gate").isHidden(), `${width}: the sign-in screen is laid out behind the desk`);
  /* A CLOSED DIALOG IS HIDDEN BY THE USER AGENT AND AN AUTHOR RULE BEATS A UA
     RULE. `dialog { display: flex }` laid out both panels in normal flow at
     the foot of every screen, permanently, with no way to dismiss them
     because they were never open — the `[hidden]` failure in a third
     element. */
  for (const d of ["#acquire", "#progress"]) {
    ok(await page.locator(d).isHidden(),
       `${width}: ${d} is laid out while closed`);
  }
  ok(!(await overflows(page)), `${width}: the document scrolls sideways`);

  /* ── the country field, which is what this pass was written for ── */
  const opts = await page.locator("#country option").count();
  ok(opts > 40, `${width}: the country select holds ${opts} options`);
  ok(await page.locator("#country-wrap").isHidden(),
     `${width}: a declared purpose was offered a country it does not have`);

  await page.selectOption("#slot", "destination-hero");
  ok(await page.locator("#country-wrap").isVisible(),
     `${width}: destination-hero was not offered a country`);

  /* A PLACE IS FOUND BY ITS NAME. The datalist this replaced matched the
     typed string against a path — `austria/salzburg-and-the-lakes/salzburg`
     — so "Hohensalzburg Fortress" matched nothing and a reader who knows a
     place by its name could not find it. */
  await page.selectOption("#country", "norway");
  await page.fill("#target-q", "bergen");
  await page.waitForSelector("#target-hits button");
  const label = await page.locator("#target-hits button").first().textContent();
  ok(/Bergen/i.test(label || ""),
     `${width}: searching for a name returned "${label}"`);
  await page.locator("#target-hits button").first().click();
  const chosen = await page.inputValue("#target");
  ok(chosen.startsWith("norway/"), `${width}: picking a name set ${chosen}`);
  ok(await page.locator("#target-chosen").isVisible(),
     `${width}: nothing on screen says which place is chosen`);

  /* AND A NAME FROM ANOTHER COUNTRY IS NOT IN THE LIST, because the country
     above it is what decides the pool. */
  await page.fill("#target-q", "salzburg");
  await page.waitForTimeout(60);
  const wrongCountry = await page.locator("#target-hits button").count();
  ok(wrongCountry === 0,
     `${width}: an Austrian place was offered while Norway was chosen`);

  /* A COUNTRY THAT IS STILL SET WHEN THE SLOT CHANGES MUST NOT STRAND A
     TARGET FROM THE OLD ONE. */
  await page.selectOption("#slot", "place-hero");
  const kept = await page.inputValue("#target");
  ok(kept === "" || kept.startsWith("norway/"),
     `${width}: changing the slot left ${kept} in the target field`);

  /* ── what to search for ────────────────────────────────────────
     Twelve roles said what a picture of each kind is for and none of them
     said what to TYPE, so every acquisition started from whatever wording
     came to mind — which is how a library drifts generic one search at a
     time. */
  await page.selectOption("#slot", "destination-hero");
  await page.selectOption("#country", "norway");
  ok(await page.locator("#concepts .concept").count() > 3,
     `${width}: the slot offered no search concepts`);
  const placeholder = await page.locator("#concepts .concept").first().textContent();
  ok(!/\{name\}/.test(placeholder || ""),
     `${width}: a concept still shows its template: ${placeholder}`);
  ok(await page.locator("#concepts .concept[disabled]").count() > 0,
     `${width}: a concept needing a place was live before one was chosen`);

  await page.fill("#target-q", "bergen");
  await page.waitForSelector("#target-hits button");
  await page.locator("#target-hits button").first().click();
  await page.waitForTimeout(40);
  const withName = await page.locator("#concepts .concept").first().textContent();
  ok(/Bergen/i.test(withName || ""),
     `${width}: choosing a place did not fill the concepts: ${withName}`);
  await page.locator("#concepts .concept").nth(1).click();
  ok(/Bergen/i.test(await page.inputValue("#q")),
     `${width}: pressing a concept did not fill the search box`);

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
  await closeDialogs(page);

  /* ── the library, scoped to a country ── */
  await page.click('[data-view="library"]');
  await page.waitForSelector("#lib .slotrow");
  /* THE EXTENT IS READ OUT OF THE REGISTRY, NOT TYPED HERE. The first
     version asserted the literal 593 and went red the day a fourth slot was
     declared — which is an assertion pinning a NUMBER rather than the
     promise, the fault this repository has recorded ten times. What matters
     is that an unscoped count is the whole set's own extent and a scoped one
     is not. */
  const total = String(REG.purposes.length);
  const wide = (await page.textContent("#lib-count")) || "";
  ok(wide.includes(total),
     `${width}: the library count is not the whole set (${total}): ${wide}`);
  await page.selectOption("#lib-country", "norway");
  const narrow = (await page.textContent("#lib-count")) || "";
  ok(/Norway/.test(narrow) && !narrow.includes(total),
     `${width}: the scoped count still reports the whole set: ${narrow}`);
  const rows = await page.locator("#lib .slotrow").count();
  ok(rows > 0 && rows < 100, `${width}: Norway listed ${rows} slots`);
  ok(!(await overflows(page)), `${width}: the library makes the document scroll sideways`);

  /* ── fill a country ───────────────────────────────────────────── */
  await closeDialogs(page);
  await page.click('[data-view="sweep"]');
  ok(await page.locator("#view-sweep").isVisible(), `${width}: the sweep view did not open`);
  /* THE COUNTRY LIST BELONGS TO THE SLOT, so the slot is chosen first. The
     first version read the count before choosing and passed only while every
     slot happened to be per-country; the day four slots arrived that are
     not, it reported "the sweep offers 1 countries" — an assertion that was
     reading a default rather than a promise. */
  await page.selectOption("#sw-slot", "destination-hero");
  const swCountries = await page.locator("#sw-country option").count();
  ok(swCountries > 40, `${width}: the sweep offers ${swCountries} countries`);
  ok(await page.locator("#sw-country").isVisible(),
     `${width}: a per-country slot was not offered a country`);
  await page.selectOption("#sw-slot", "journey-hero");
  ok(!(await page.locator("#sw-country").isVisible()),
     `${width}: a slot with no countries still offers the field`);
  await page.selectOption("#sw-slot", "destination-hero");
  await page.selectOption("#sw-country", "norway");
  await page.click("#sweep button[type=submit]");
  await page.waitForSelector(".swcell");
  ok(await page.locator(".swcell").count() === 4,
     `${width}: the grid drew the wrong number of surfaces`);
  ok(await page.locator(".swcell.none").count() === 1,
     `${width}: the surface with no candidate was dropped rather than named`);

  /* NOTHING ARRIVES TICKED. A grid that arrives pre-ticked makes the default
     "acquire everything the provider happened to return first". */
  ok(await page.locator("#sw-grid input:checked").count() === 0,
     `${width}: the grid arrived with rows already ticked`);
  ok(await page.locator("#sw-go").isDisabled(),
     `${width}: Acquire was live with nothing ticked`);

  await page.click("#sw-all");
  const tickedNow = await page.locator("#sw-grid input:checked").count();
  ok(tickedNow === 3, `${width}: Select all ticked ${tickedNow} of 3 offerable rows`);

  /* A TICKED ROW WITH NO DESCRIPTION IS NOT ACQUIRABLE, and the bar says so
     rather than the dispatch failing four screens later. */
  ok(await page.locator("#sw-go").isDisabled(),
     `${width}: Acquire was live with a ticked row that has no description`);
  ok(/no description/.test(await page.textContent("#sw-count") || ""),
     `${width}: the bar does not say why Acquire is refused`);

  await page.locator("#sw-grid textarea").nth(1).fill(
    "A harbour at first light, with the fishing boats still tied up.");
  await page.waitForTimeout(30);
  ok(!(await page.locator("#sw-go").isDisabled()),
     `${width}: Acquire stayed disabled after every description was written`);

  /* THE DISPATCH CARRIES IDS, NEVER POSITIONS. */
  DISPATCHED.length = 0;
  await page.click("#sw-go");
  await page.waitForFunction(() => true);
  await page.waitForTimeout(200);
  const sent = DISPATCHED[0] || {};
  ok(Array.isArray(sent.batch) && sent.batch.length === 3,
     `${width}: the dispatch carried ${(sent.batch || []).length} entries`);
  ok((sent.batch || []).every((e) => /^[0-9]+$/.test(String(e.photo_id))
        && e.purpose && e.alt),
     `${width}: an entry travelled without an id, a purpose or a description`);
  await closeDialogs(page);

  /* ── fill the library ──────────────────────────────────────────────
     THE ONE PRESS THAT NEEDS NO DECISION FIRST, so what it has to be is
     PRESENT on the way in and honest about what it will do. An editor
     opening a desk with 826 empty slots should meet the button before the
     filters, and should not be surprised by it afterwards. */
  await page.click('[data-view="find"]');
  ok(await page.locator("#topup").isVisible(),
     `${width}: the fill band is not on the screen an editor arrives at`);
  const band = await page.textContent("#topup") || "";
  ok(/\d/.test(band), `${width}: the fill band states no count`);
  ok(/merges itself|deployment|europedoor\.com/.test(band),
     `${width}: the fill band does not say that a green run publishes`);
  ok(/nothing is ranked|nothing here has looked/i.test(band),
     `${width}: the fill band claims a judgement nothing here makes`);
  ok(!(await page.locator("#topup-go").isDisabled()),
     `${width}: the fill button is dead with 826 surfaces empty`);

  /* ONE PRESS: it gathers, it puts every row in the basket, and it
     dispatches — and the basket keeps them, because a set that publishes
     without leaving a trace of what it chose is a set nobody can audit. */
  DISPATCHED.length = 0;
  await page.click("#topup-go");
  await page.waitForTimeout(400);
  const filled = DISPATCHED[0] || {};
  ok(Array.isArray(filled.batch) && filled.batch.length === 3,
     `${width}: the fill dispatched ${(filled.batch || []).length} entries`);
  ok((filled.batch || []).every((e) => /^[0-9]+$/.test(String(e.photo_id))
        && e.purpose && e.alt),
     `${width}: an entry travelled without an id, a purpose or a description`);
  const fams = new Set((filled.batch || []).map((e) => e.purpose.split("@")[0]));
  ok(fams.size === 3,
     `${width}: one press covered ${fams.size} families, not every category`);
  await closeDialogs(page);
  await page.click('[data-view="basket"]');
  await page.waitForSelector("#bk-grid .swcell");
  ok(await page.locator("#bk-grid .swcell.gone").count() === 3,
     `${width}: what the fill sent left no trace in the basket`);
  /* AND A SENT ENTRY CAN BE CLEARED. It is deliberately untickable so it
     cannot be sent twice, which means Select all skips it and Remove ticked
     cannot reach it — so the two controls that look like they would empty
     the basket could not touch the only thing that accumulates in it. */
  ok(await page.locator("#bk-sent").isVisible(),
     `${width}: sent entries cannot be cleared except one at a time`);
  await page.click("#bk-sent");
  await page.waitForTimeout(50);
  ok(await page.locator("#bk-grid .swcell").count() === 0,
     `${width}: Clear sent left entries behind`);

  /* ── the basket ────────────────────────────────────────────────────
     WHAT THE BASKET HAS TO BE IS A PLACE WORK SURVIVES, so the assertions
     are about surviving: a candidate kept from a search is still there when
     the search is gone, a whole sweep can be kept instead of sent, a purpose
     cannot be in it twice, and it comes back after a reload. None of that is
     visible in a count of anything. */
  await page.click('[data-view="basket"]');
  ok(await page.locator("#view-basket").isVisible(),
     `${width}: the basket view did not open`);
  ok(/empty/.test(await page.textContent("#bk-note") || ""),
     `${width}: an empty basket does not say it is empty`);
  ok(!(await page.locator("#bk-bar").isVisible()),
     `${width}: an empty basket still offers Acquire`);

  /* KEEP FROM A SEARCH. The one-at-a-time path is untouched; this is the
     act that costs nothing and leaves the editor in the search. */
  await page.click('[data-view="find"]');
  await page.selectOption("#slot", "countries-hero");
  await page.fill("#q", "a european coast");
  await page.click("#find button[type=submit]");
  await page.waitForSelector(".cand");
  ok(await page.locator("[data-bag]").count() > 1,
     `${width}: a candidate offers no way to keep it without acquiring it`);
  await page.locator("[data-bag]").first().click();
  ok(/Kept/.test(await page.textContent("[data-bag] >> nth=0") || ""),
     `${width}: keeping a candidate said nothing where the editor was looking`);
  ok((await page.textContent("#basket-n") || "") === "1",
     `${width}: the tab count did not move`);

  /* A SURFACE HOLDS ONE PHOTOGRAPH, and replacing says so. The register
     refuses that pair at the far end, so a basket that can hold it wastes
     the sitting it exists to collect. */
  const second = page.locator(".cand").nth(1).locator("[data-bag]");
  await second.click();
  ok((await page.textContent("#basket-n") || "") === "1",
     `${width}: a second photograph for one surface was added rather than `
     + `replacing the first`);
  ok(/Replaced/.test(
       await page.locator(".cand").nth(1).locator(".kept").textContent() || ""),
     `${width}: it replaced a pick silently`);

  /* KEEP A WHOLE SWEEP WITHOUT DISPATCHING IT. */
  await page.click('[data-view="sweep"]');
  await page.waitForSelector(".swcell");
  await page.click("#sw-all");
  DISPATCHED.length = 0;
  await page.click("#sw-bag");
  await page.waitForTimeout(50);
  ok(DISPATCHED.length === 0, `${width}: keeping a sweep dispatched a run`);
  const held = Number(await page.textContent("#basket-n") || "0");
  ok(held === 4, `${width}: the basket holds ${held} after keeping 3 and 1`);

  await page.click('[data-view="basket"]');
  await page.waitForSelector("#bk-grid .swcell");
  ok(await page.locator("#bk-grid .swcell").count() === 4,
     `${width}: the basket drew the wrong number of entries`);
  ok(/held in this browser/.test(await page.textContent("#bk-note") || ""),
     `${width}: the basket does not say whose it is or where it lives`);

  ok(await page.locator("#bk-grid input:checked").count() === 0,
     `${width}: the basket arrived with entries already ticked`);
  ok(await page.locator("#bk-go").isDisabled(),
     `${width}: Acquire was live with nothing ticked`);

  /* AN ENTRY WITH NO DESCRIPTION CANNOT BE TICKED AT ALL, which is a
     stronger promise than the sweep's — there the row is ticked and the bar
     explains, and here the basket is a list you come back to, where a tick
     that cannot be acted on is a tick that misleads. */
  const undesc = await page.locator("#bk-grid input:disabled").count();
  ok(undesc === 1,
     `${width}: ${undesc} entries with no description were tickable`);

  await page.click("#bk-all");
  const bkOn = await page.locator("#bk-grid input:checked").count();
  ok(bkOn === 3, `${width}: Select all ticked ${bkOn} of 3 acquirable entries`);
  ok(!(await page.locator("#bk-go").isDisabled()),
     `${width}: Acquire stayed disabled with three entries ready`);

  /* IT SURVIVES A RELOAD, which is the whole point of it. */
  await page.reload();
  await page.waitForSelector("#desk:not([hidden])");
  await page.click('[data-view="basket"]');
  await page.waitForSelector("#bk-grid .swcell");
  ok(await page.locator("#bk-grid .swcell").count() === 4,
     `${width}: the basket did not survive a reload`);

  await page.click("#bk-all");
  DISPATCHED.length = 0;
  await page.click("#bk-go");
  await page.waitForTimeout(250);
  const bkSent = DISPATCHED[0] || {};
  ok(Array.isArray(bkSent.batch) && bkSent.batch.length === 3,
     `${width}: the basket dispatched ${(bkSent.batch || []).length} entries`);
  ok((bkSent.batch || []).every((e) => /^[0-9]+$/.test(String(e.photo_id))),
     `${width}: an entry travelled without an id`);
  await closeDialogs(page);

  /* A DISPATCH IS NOT A MERGE, so a sent entry stays and says so. Removing
     it would call the work done at the moment the question is asked, and a
     red run would leave the editor hunting for every photograph again. */
  ok(await page.locator("#bk-grid .swcell.gone").count() === 3,
     `${width}: sent entries were dropped rather than marked`);
  ok(await page.locator("#bk-grid input:checked").count() === 0,
     `${width}: a sent entry is still ticked and can be sent twice`);

  /* AND THE BASKET IS EMPTIED BY HAND. */
  await page.click("#bk-all");
  await page.click("#bk-drop");
  await page.waitForTimeout(50);

  await page.click('[data-view="library"]');
  await page.waitForSelector("#lib .slotrow");

  /* ── an opening is a door ─────────────────────────────────────── */
  ok(await page.locator("#lib button.slotrow").count() > 0,
     `${width}: an empty library row is still a dead end`);
  await page.locator("#lib button.slotrow").first().click();
  ok(await page.locator("#view-find").isVisible(),
     `${width}: clicking an opening did not take the reader to the search`);
  ok((await page.inputValue("#q")).length > 0,
     `${width}: it arrived at the search with an empty query`);
  await page.click('[data-view="library"]');
  await page.waitForSelector("#lib .slotrow");

  const cut = await clipped(page);
  ok(cut.length === 0, `${width}: text is cut off in ${cut.length}: ${cut.slice(0, 3).join(" | ")}`);

  await page.close();
  } catch (e) {
    failures.push(`${width}: the run stopped — ${String(e).split("\n")[0]}`);
  }
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
