/* Browser checks for Europedoor.
 *
 *   npm install playwright && node tools/browser-checks.js
 *
 * tools/checks.py reads the generated HTML. This runs it. The three things
 * that can only fail in a browser are the Journey Planner (which is the
 * product), the map's layer filtering, and horizontal overflow on a phone —
 * so those are what this tests, plus a hard rule that no page may log a
 * console error.
 *
 * It serves site/ over a local static server with cleanUrls semantics, the
 * same way the host will, because a link to /countries that only works as
 * /countries/index.html is a bug that never shows up locally.
 */

const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "site");

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".xml": "application/xml",
  ".txt": "text/plain; charset=utf-8",
};

function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split("?")[0]);
      const candidates = [
        path.join(OUT, url),
        path.join(OUT, url, "index.html"),
        path.join(OUT, url + ".html"),
      ];
      for (const c of candidates) {
        if (fs.existsSync(c) && fs.statSync(c).isFile()) {
          res.writeHead(200, { "Content-Type": TYPES[path.extname(c)] || "application/octet-stream" });
          return res.end(fs.readFileSync(c));
        }
      }
      res.writeHead(404, { "Content-Type": "text/html" });
      res.end(fs.readFileSync(path.join(OUT, "404.html")));
    });
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

const failures = [];
let checked = 0;
function ok(cond, msg) {
  checked++;
  if (!cond) failures.push(msg);
}

async function main() {
  let chromium;
  try {
    ({ chromium } = require("playwright"));
  } catch (e) {
    console.log("playwright is not installed — skipping browser checks");
    console.log("  npm install playwright && node tools/browser-checks.js");
    process.exit(0);
  }

  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}`;
  // The sandbox ships its own Chromium build, which will not match whatever
  // version of playwright npm resolves. Prefer an explicit binary when one
  // is present and fall back to playwright's own download.
  const candidates = [
    process.env.CHROMIUM_PATH,
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
  ].filter(Boolean).filter((p) => fs.existsSync(p));
  const browser = await chromium.launch(
    candidates.length ? { executablePath: candidates[0] } : {}
  );

  const errors = [];
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on("console", (m) => { if (m.type() === "error") errors.push(`${page.url()}: ${m.text()}`); });
  page.on("pageerror", (e) => errors.push(`${page.url()}: ${e.message}`));

  // ── the planner, which is the product ──────────────────────────────
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  ok(await page.locator("#planner").count() === 1, "planner form did not render");
  ok(await page.locator("#start option").count() > 100, "start select was not populated from the atlas index");

  await page.fill("#days", "12");
  await page.fill("#budget", "2500");
  await page.selectOption("#month", "sep");
  await page.check('input[name="interest"][value="history"]');
  await page.check('input[name="interest"][value="mountains"]');
  await page.check('input[name="interest"][value="food"]');
  await page.click('#planner button[type="submit"]');
  await page.waitForSelector("#result .leg");

  const legs = await page.locator("#result .leg").count();
  ok(legs >= 3, `planner produced only ${legs} stops for 12 days`);

  const days = await page.locator("#result .leg-when").allTextContents();
  const last = days[days.length - 1];
  const lastDay = parseInt(last.replace(/[^0-9–-]/g, "").split(/[–-]/).pop(), 10);
  ok(lastDay <= 12, `itinerary runs to day ${lastDay} on a 12-day trip`);
  ok(lastDay >= 9, `itinerary only fills ${lastDay} of 12 days`);

  const total = await page.locator("#result .result-summary dd").first().textContent();
  ok(/^€[\d,]+$/.test(total.trim()), `cost estimate did not render as money: ${total}`);

  // Every stop must link to a page that exists.
  const hrefs = await page.locator("#result .leg h3 a").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
  for (const h of hrefs) {
    const r = await page.request.get(base + h);
    ok(r.status() === 200, `planner linked to ${h}, which returned ${r.status()}`);
  }

  // Interests must actually steer it: an all-coast request and an
  // all-mountain request must not return the same route.
  async function routeFor(interests) {
    await page.goto(base + "/plan", { waitUntil: "networkidle" });
    await page.fill("#days", "14");
    for (const i of interests) await page.check(`input[name="interest"][value="${i}"]`);
    await page.click('#planner button[type="submit"]');
    await page.waitForSelector("#result .leg");
    return (await page.locator("#result .leg h3 a").allTextContents()).join(" > ");
  }
  const coast = await routeFor(["coast", "islands"]);
  const alps = await routeFor(["mountains", "winter"]);
  ok(coast !== alps, "the planner returned the same route for coast and for mountains");

  // A country under a travel advisory must never appear.
  for (const banned of ["Kyiv", "Lviv", "Moscow", "Minsk", "Saint Petersburg"]) {
    ok(!coast.includes(banned) && !alps.includes(banned), `planner routed into ${banned}`);
  }

  // ── search ─────────────────────────────────────────────────────────
  await page.goto(base + "/search", { waitUntil: "networkidle" });
  await page.fill("#q", "bergen");
  await page.waitForSelector("#results .row");
  const first = await page.locator("#results .row h3").first().textContent();
  ok(first.trim() === "Bergen", `searching "bergen" put ${first!==null?first.trim():"nothing"} first`);

  // Accent folding: the index holds Malmö, the visitor types Malmo.
  await page.fill("#q", "malmo");
  await page.waitForTimeout(200);
  const folded = await page.locator("#results .row h3").first().textContent();
  ok(folded.trim() === "Malmö", `accent folding failed: got ${folded}`);

  // A thematic word must reach more than one kind of thing.
  await page.fill("#q", "medieval");
  await page.waitForTimeout(200);
  const kinds = new Set(await page.locator("#results .rowmeta").allTextContents());
  ok(kinds.size >= 2, `"medieval" returned only ${[...kinds].join(", ")}`);

  // Every result must resolve.
  await page.fill("#q", "wine");
  await page.waitForTimeout(200);
  const shrefs = await page.locator("#results .row").evaluateAll((as) =>
    as.slice(0, 8).map((a) => a.getAttribute("href")));
  for (const h of shrefs) {
    const r = await page.request.get(base + h);
    ok(r.status() === 200, `search linked to ${h}, which returned ${r.status()}`);
  }

  // Nonsense must say so rather than guessing.
  await page.fill("#q", "qqzzxx");
  await page.waitForTimeout(200);
  ok((await page.locator("#results").textContent()).includes("Nothing for"),
     "an unmatched search did not say it found nothing");

  // A budget that cannot buy Switzerland must not return Switzerland.
  async function routeOnBudget(budget) {
    await page.goto(base + "/plan", { waitUntil: "networkidle" });
    await page.fill("#days", "12");
    await page.fill("#budget", String(budget));
    await page.check('input[name="interest"][value="mountains"]');
    await page.click('#planner button[type="submit"]');
    await page.waitForSelector("#result .leg");
    const text = await page.locator("#result").textContent();
    const totalTxt = await page.locator("#result .result-summary dd").first().textContent();
    return { text, total: parseInt(totalTxt.replace(/[^0-9]/g, ""), 10) };
  }
  const lean = await routeOnBudget(700);
  ok(lean.total <= 700 * 1.35,
     `a €700 mountain trip was planned at €${lean.total}`);
  ok(!/Switzerland|Zermatt|Lauterbrunnen/.test(lean.text),
     "a €700 budget still routed through Switzerland");
  const rich = await routeOnBudget(6000);
  ok(rich.total > lean.total, "a nine-fold budget produced no more expensive a trip");

  // ── the sentence box ───────────────────────────────────────────────
  async function ask(text) {
    await page.goto(base + "/plan", { waitUntil: "networkidle" });
    await page.fill("#ask", text);
    await page.click('#askform button[type="submit"]');
    await page.waitForSelector("#result .leg");
    return {
      read: (await page.locator("#result .note").first().textContent()).replace(/\s+/g, " "),
      route: (await page.locator("#result .leg h3 a").allTextContents()).join(" | "),
      days: await page.inputValue("#days"),
      budget: await page.inputValue("#budget"),
      month: await page.inputValue("#month"),
      style: await page.inputValue("#style"),
      pace: await page.inputValue("#pace"),
    };
  }

  const a1 = await ask("I have 12 days, €2,500, I love history, mountains and food.");
  ok(a1.days === "12", `"12 days" parsed as ${a1.days}`);
  ok(a1.budget === "2500", `"€2,500" parsed as ${a1.budget}`);
  ok(/history/.test(a1.read) && /food/.test(a1.read) && /mountains/.test(a1.read),
     "the three stated interests were not all read back");

  const a2 = await ask("three weeks by train through the alps in winter, luxury");
  ok(a2.days === "21", `"three weeks" parsed as ${a2.days}`);
  ok(a2.style === "high", `"luxury" parsed as ${a2.style}`);
  ok(a2.month === "jan", `"winter" parsed as ${a2.month}`);
  ok(!/weather forecast/.test(a2.read),
     'the word "train" matched the weather keyword "rain" again');
  ok(/Switzerland|Austria|Italy|Slovenia|France|Germany/.test(a2.read),
     '"the alps" did not constrain the plan to alpine countries');

  const a3 = await ask("ten days in Portugal and Spain, wine, starting in Oslo");
  ok(/Oslo is outside/.test(a3.read),
     "a start outside the named region was silently kept or silently dropped");
  ok(!/Oslo|Bergen|Norway/.test(a3.route), `named Iberia and routed to ${a3.route}`);

  const a4 = await ask("a fortnight in Greece in May, islands and ruins, moderate budget");
  ok(a4.style === "moderate", `"moderate budget" parsed as ${a4.style}`);
  ok(a4.days === "14", `"a fortnight" parsed as ${a4.days}`);

  const a5 = await ask("a week of museums, and my wife uses a wheelchair, we are vegan");
  ok(/accessibility needs/.test(a5.read) && /dietary requirements/.test(a5.read),
     "the planner did not name what it cannot take account of");

  const a6 = await ask("£1800 for ten days of coast");
  ok(/no conversion/.test(a6.read), "a pound figure was silently shown as euros");

  const a7 = await ask("hello");
  ok(/Nothing I could use/.test(a7.read), "an unparseable sentence did not say so");

  // ── the specification's planner output ─────────────────────────────
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.fill("#days", "12");
  await page.fill("#budget", "2500");
  await page.check('input[name="interest"][value="history"]');
  await page.click('#planner button[type="submit"]');
  await page.waitForSelector("#result .leg");

  const costLabels = await page.locator("#result .result-summary dt").allTextContents();
  for (const want of ["Accommodation", "Food", "Transport", "Activities"]) {
    ok(costLabels.some((l) => l.includes(want)), `cost breakdown has no ${want} line`);
  }
  ok((await page.locator("#result .daylist li").count()) > 3,
     "the itinerary has no day-by-day breakdown");

  // Sharing: the link must carry the route, not just the inputs, because the
  // planner jitters and would otherwise return a different trip.
  const before = await page.locator("#result .leg h3 a").allTextContents();
  await page.click("#shareplan");
  await page.waitForTimeout(150);
  const shared = await page.evaluate(() => location.pathname + location.search);
  ok(/[?&]r=/.test(shared), "the share link does not carry the route");
  const p2 = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await p2.goto(base + shared, { waitUntil: "networkidle" });
  await p2.waitForSelector("#result .leg");
  const after = await p2.locator("#result .leg h3 a").allTextContents();
  ok(before.join("|") === after.join("|"),
     `a shared plan came back different: ${before.join(">")} vs ${after.join(">")}`);
  ok(/saved itinerary/i.test(await p2.locator("#result .note").first().textContent()),
     "a restored plan does not say where it came from");
  await p2.close();

  // Saving an itinerary must survive into My Europe.
  await page.click("#saveplan");
  await page.waitForTimeout(150);
  await page.goto(base + "/my-europe", { waitUntil: "networkidle" });
  ok(/Itinerar/i.test(await page.locator("#mine").textContent()),
     "a saved itinerary did not reach My Europe");

  // The specification's four search intents, each of which returned nothing
  // before the query was read for modifiers rather than matched as a string.
  async function searchFor(q) {
    await page.goto(base + "/search", { waitUntil: "networkidle" });
    await page.fill("#q", q);
    await page.waitForTimeout(260);
    return {
      understood: (await page.locator("#searchunderstood").textContent()).replace(/\s+/g, " "),
      count: await page.locator("#results .row").count(),
      heads: (await page.locator("#results h3").allTextContents()).join(" | "),
    };
  }
  const s1 = await searchFor("quiet beaches in september");
  ok(s1.count > 0, "\"quiet beaches in september\" returned nothing");
  ok(/quiet/.test(s1.understood) && /September/.test(s1.understood),
     `the modifiers were not read back: ${s1.understood}`);
  const s2 = await searchFor("medieval castles near prague");
  ok(s2.count > 0, "\"medieval castles near prague\" returned nothing");
  ok(/near Prague/.test(s2.understood), "the proximity was not understood");
  const s3 = await searchFor("cheap mountains");
  ok(s3.count > 0 && /cheap/.test(s3.understood), "a budget query was not understood");
  const s4 = await searchFor("romantic places");
  ok(s4.count > 0 && /reading that as/.test(s4.understood), "an intent query was not understood");
  const s5 = await searchFor("bergen");
  ok(/Cit|Region|Place/.test(s5.heads), "results are not grouped by type");

  // ── the map ────────────────────────────────────────────────────────
  await page.goto(base + "/map", { waitUntil: "networkidle" });
  const dots = await page.locator("#dots .dot").count();
  ok(dots > 200, `map drew only ${dots} cities`);
  await page.check('#layers input[value="winter"]');
  await page.waitForTimeout(120);
  const lit = await page.locator("#dots .dot:not(.off)").count();
  ok(lit > 0 && lit < dots, `winter layer lit ${lit} of ${dots} — filtering is not working`);

  // ── saved places ───────────────────────────────────────────────────
  await page.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
  await page.click("[data-save]");
  ok((await page.locator("[data-save]").textContent()).includes("✓"), "save button did not confirm");
  await page.goto(base + "/my-europe", { waitUntil: "networkidle" });
  ok((await page.locator("#mine").textContent()).includes("Bergen"), "saved place did not appear in My Europe");

  // ── no horizontal overflow at phone width ──────────────────────────
  const phone = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const sample = [
    "/", "/countries", "/discover/mediterranean", "/europe/italy",
    "/europe/italy/tuscany-and-the-centre",
    "/europe/italy/tuscany-and-the-centre/florence",
    "/journeys", "/journeys/the-alpine-grand-tour", "/plan", "/themes/sacred-europe",
    "/stories", "/stories/the-last-forest", "/experiences", "/experiences/join",
    "/fund", "/fund/qvevri-apprenticeship", "/events", "/method", "/beyond-the-obvious",
    "/about", "/how-it-works", "/sources", "/for-businesses", "/my-europe", "/search",
  ];
  for (const url of sample) {
    await phone.goto(base + url, { waitUntil: "domcontentloaded" });
    const over = await phone.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    ok(over <= 1, `${url} overflows by ${over}px at 390 CSS pixels`);
    const h1 = await phone.locator("h1").count();
    ok(h1 === 1, `${url} has ${h1} h1 elements`);
  }

  // The map is allowed to scroll inside its own container, and must not
  // make the page scroll.
  await phone.goto(base + "/map", { waitUntil: "domcontentloaded" });
  const mapOver = await phone.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth
  );
  ok(mapOver <= 1, `/map overflows the page by ${mapOver}px instead of scrolling its own wrapper`);

  // ── accessibility: WCAG 2.2 AA, the part a machine can hold ─────────
  //
  // Not a conformance claim. These are the failures a build can catch, run
  // on every page shape, in both colour schemes. The audit that matters —
  // somebody using a screen reader daily — is named as missing on
  // /accessibility rather than implied by a green tick here.
  const a11yPages = [
    "/", "/discover", "/countries", "/europe/norway", "/europe/norway/fjord-norway/bergen",
    "/europe/norway/fjord-norway/bergen/place/bryggen", "/plan", "/search", "/map",
    "/journeys/the-alpine-grand-tour", "/experiences", "/experiences/nature",
    "/stories/the-last-forest", "/events/oct", "/fund", "/privacy", "/accessibility",
    "/my-europe", "/sources/freshness",
  ];

  const a11yProbe = () => {
    const out = { headingSkips: [], unlabelled: [], emptyLinks: [], noAlt: [], issues: [] };

    // Contrast, computed from what the browser actually paints.
    const lum = (c) => {
      // Chromium reports color-mix() as color(srgb 0.07 0.08 0.1 / .88) —
      // components 0–1 rather than 0–255. Reading those as 8-bit made the
      // masthead look like it had a contrast failure it did not have.
      const nums = (c.match(/-?\d*\.?\d+/g) || []).map(Number);
      const scale = /^color\(/.test(c) ? 255 : 1;
      const [r, g, b] = nums.slice(0, 3).map((v) => {
        const s = (v * scale) / 255;
        return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const bgOf = (el) => {
      let n = el;
      while (n && n !== document.documentElement) {
        const bg = getComputedStyle(n).backgroundColor;
        if (bg && !/rgba\(0, 0, 0, 0\)|transparent/.test(bg)) return bg;
        n = n.parentElement;
      }
      return getComputedStyle(document.body).backgroundColor;
    };
    const ratio = (a, b) => {
      const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x);
      return (l1 + 0.05) / (l2 + 0.05);
    };

    const sample = [...document.querySelectorAll("p, li, a, h1, h2, h3, dt, dd, button, label, span.chip, .rowmeta, .kicker, .footer-legal")]
      .filter((el) => el.textContent.trim().length > 3)
      .slice(0, 220);
    for (const el of sample) {
      const cs = getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.display === "none") continue;
      const size = parseFloat(cs.fontSize);
      const bold = parseInt(cs.fontWeight, 10) >= 700;
      const large = size >= 24 || (size >= 18.66 && bold);
      const need = large ? 3 : 4.5;
      const r = ratio(cs.color, bgOf(el));
      if (r < need) {
        out.issues.push(`contrast ${r.toFixed(2)}:1 (needs ${need}) on <${el.tagName.toLowerCase()}> "${el.textContent.trim().slice(0, 40)}"`);
      }
    }

    // Heading order.
    let prev = 0;
    for (const h of document.querySelectorAll("h1,h2,h3,h4,h5,h6")) {
      const lvl = Number(h.tagName[1]);
      if (prev && lvl > prev + 1) out.headingSkips.push(`h${prev} → h${lvl} at "${h.textContent.trim().slice(0, 40)}"`);
      prev = lvl;
    }

    // Labels, link text, image alternatives, landmarks.
    for (const f of document.querySelectorAll("input, select, textarea")) {
      const id = f.getAttribute("id");
      const labelled = (id && document.querySelector(`label[for="${id}"]`)) ||
        f.closest("label") || f.getAttribute("aria-label") || f.getAttribute("aria-labelledby");
      if (!labelled) out.unlabelled.push(f.outerHTML.slice(0, 60));
    }
    for (const a of document.querySelectorAll("a")) {
      const text = (a.textContent || "").trim() || a.getAttribute("aria-label") || a.querySelector("svg[aria-label]");
      if (!text) out.emptyLinks.push(a.getAttribute("href") || "(no href)");
    }
    for (const g of document.querySelectorAll('svg[role="img"]')) {
      if (!g.getAttribute("aria-label") && !g.querySelector("title")) out.noAlt.push("svg without a name");
    }
    if (!document.querySelector("main")) out.issues.push("no <main> landmark");
    if (!document.querySelector('nav[aria-label]')) out.issues.push("no labelled nav");
    if (!document.documentElement.getAttribute("lang")) out.issues.push("no lang on <html>");
    if (!document.querySelector('a.skip')) out.issues.push("no skip link");
    return out;
  };

  for (const scheme of ["light", "dark"]) {
    const a11y = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await a11y.emulateMedia({ colorScheme: scheme });
    for (const url of a11yPages) {
      await a11y.goto(base + url, { waitUntil: "load" });
      const r = await a11y.evaluate(a11yProbe);
      ok(r.issues.length === 0, `${scheme} ${url}: ${r.issues.slice(0, 2).join("; ")}`);
      ok(r.headingSkips.length === 0, `${scheme} ${url}: heading level skipped — ${r.headingSkips[0]}`);
      ok(r.unlabelled.length === 0, `${scheme} ${url}: unlabelled form control ${r.unlabelled[0]}`);
      ok(r.emptyLinks.length === 0, `${scheme} ${url}: link with no discernible text (${r.emptyLinks[0]})`);
      ok(r.noAlt.length === 0, `${scheme} ${url}: ${r.noAlt[0]}`);
    }
    await a11y.close();
  }

  // Keyboard: the skip link must be the first stop and must actually move focus.
  const kb = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await kb.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "domcontentloaded" });
  await kb.keyboard.press("Tab");
  const firstStop = await kb.evaluate(() => document.activeElement.className);
  ok(/skip/.test(firstStop), `the first tab stop is "${firstStop}", not the skip link`);
  const focusVisible = await kb.evaluate(() => {
    const el = document.activeElement;
    const cs = getComputedStyle(el);
    return cs.outlineStyle !== "none" || cs.boxShadow !== "none";
  });
  ok(focusVisible, "the focused skip link has no visible focus indicator");
  await kb.close();

  // Reduced motion must actually remove motion, not merely shorten it.
  const rm = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await rm.emulateMedia({ reducedMotion: "reduce" });
  await rm.goto(base + "/countries", { waitUntil: "domcontentloaded" });
  const anyTransition = await rm.evaluate(() =>
    [...document.querySelectorAll(".card, .chip, .btn, a")].some((el) => {
      const d = getComputedStyle(el).transitionDuration;
      return d && d !== "0s" && !/^0s(, 0s)*$/.test(d);
    })
  );
  ok(!anyTransition, "transitions still run under prefers-reduced-motion");
  await rm.close();

  ok(errors.length === 0, `console errors:\n    ${errors.slice(0, 5).join("\n    ")}`);

  await browser.close();
  server.close();

  if (failures.length) {
    console.log(`\n${failures.length} browser check failure(s) of ${checked}:`);
    failures.forEach((f) => console.log("  - " + f));
    process.exit(1);
  }
  console.log(`all ${checked} browser checks passed`);
}

main().catch((e) => { console.error(e); process.exit(1); });
