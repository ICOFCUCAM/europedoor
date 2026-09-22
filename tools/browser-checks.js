/* Browser checks for EuropeDoor.
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

// THE REGISTER IS WHERE A COLOUR IS DECIDED, and this suite used to carry
// copies: a literal `#8398ff` for the INTELLIGENCE accent, two hue bounds
// typed into a ternary, and a "blue > red + 40" test for the signature
// family. All three are claims about cobalt, and all three would have gone
// silently wrong the day the signature stopped being cobalt — an instrument
// that cannot survive the change it exists to police.
const PALETTE = JSON.parse(fs.readFileSync(
  path.join(ROOT, "docs", "palette.json"), "utf8"));

/* ONE CLASSIFIER, BUILT FROM THE REGISTER, USED BY EVERY CHECK THAT ASKS
 * "WHAT FAMILY IS THIS COLOUR IN".
 *
 * Two checks asked it with a HUE WINDOW and both broke on the same palette
 * change: the ratio reported the signature at 0.1% because pine (174.2) and
 * the owner's map water (174.5) are three tenths of a degree apart, and the
 * kicker probe asked whether a label is "in the accent" by the signature
 * band, which is a different question wearing the same numbers. A second
 * implementation of a thing is a second chance to make its mistake — sixth
 * occurrence here, and this one is the fix rather than the occurrence.
 *
 * `SWATCH` is every declared token with the family the register puts it in;
 * `familyOf` returns that family for a painted colour, or "" when the colour
 * is further than `max_distance` from every token, which is what a
 * photograph, a blend or a shadow is. */
const SWATCH = (() => {
  const out = [];
  for (const [family, names] of Object.entries(PALETTE.ratio.$families)) {
    if (!Array.isArray(names)) continue;
    for (const nm of names) out.push({ family, hex: PALETTE.tokens[nm].hex });
  }
  return out;
})();
const MAXD = PALETTE.ratio.$families.max_distance;

function rgbOf(v) {
  const m = String(v).match(/\d+/g);
  if (m && m.length >= 3) return m.slice(0, 3).map(Number);
  const h = String(v).replace("#", "");
  return h.length === 6 ? [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) : null;
}
function sameColour(a, b, tol = 2) {
  const x = rgbOf(a), y = rgbOf(b);
  return !!x && !!y && x.every((v, i) => Math.abs(v - y[i]) <= tol);
}

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

  // ── the sentence box must report the plan, not the parse ───────────
  // /plan ships the claim that it "shows you exactly what it understood,
  // naming anything it could not take account of rather than quietly
  // dropping it". It was composing that readback from the PARSE while the
  // route beside it came from something else, and `plan()` runs four lines
  // before the readback is built, so every disagreement was already known
  // and thrown away. Three shipped, and none is visible to any static
  // check: the readback is composed at runtime, so a page that reports its
  // plan and a page that reports its parse are the same bytes until
  // somebody types a sentence.
  async function askFor(sentence) {
    await page.goto(base + "/plan", { waitUntil: "networkidle" });
    await page.fill("#ask", sentence);
    await page.click("#askform button[type=submit]");
    await page.waitForSelector("#result .note h3");
    // A REFUSAL IS A VALID ANSWER AND MUST NOT LOOK LIKE A HANG. The
    // planner declines to build a trip it cannot fund — "EUR 4,618 against
    // a budget of EUR 2,500. That is not a plan you can take." — and the
    // specification's own flagship sentence (EUR 2,500, twelve days, "my
    // wife") is exactly that case now the party size reaches the
    // arithmetic. Reading `.result-summary` straight would wait thirty
    // seconds and die on a locator instead of failing with a sentence,
    // which is the crash-stops-counting fault in the instrument.
    const priced = await page.locator("#result .result-summary dd").count();
    const money = priced
      ? await page.locator("#result .result-summary dd").first().textContent()
      : "0";
    return {
      priced: priced > 0,
      // .first(), because the result carries three `.note` blocks — the
      // readback, the what-if rail and the budget line — and a strict
      // locator resolving to several is how this suite died once before.
      say: (await page.locator("#result .note").first().innerText()).replace(/\s+/g, " "),
      days: await page.locator("#days").inputValue(),
      people: await page.locator("#travellers").inputValue(),
      cost: parseInt(money.replace(/[^0-9]/g, ""), 10),
    };
  }

  // 1. THE PARTY SIZE, WHICH IS THE EXPENSIVE ONE. `applyAsk` never set
  //    form.travellers, so the cost model multiplied food, transport and
  //    activities by the control's default of one while the page said "for
  //    4". The cost model itself is careful — a double is not twice a
  //    single, so the second traveller adds 55% of a room and everything
  //    else scales linearly — which makes total(n)/total(1) land between
  //    1 + 0.55(n-1) and n. Asserted as that BAND rather than as a figure,
  //    because a number typed here is a second copy of the cost model.
  // The FORM path's party size is already asserted further down, with the
  // same cost band — which is the whole shape of this defect: the tested
  // path worked and the untested one did not. A code path nothing
  // exercises is a code path nothing checks.
  const askOne = await askFor("Ten days in Italy starting in Rome");
  const four = await askFor("Ten days in Italy starting in Rome for 4 people");
  ok(four.people === "4",
     `the sentence named four travellers and the form carried ${four.people}: ` +
     "a party size that does not reach readForm is a cost for somebody else");
  ok(/for <?4|for 4/.test(four.say) || four.say.includes("for 4"),
     "the readback did not state the party size it planned for");
  ok(askOne.priced && four.priced,
     "one of the two party-size sentences was refused on budget, so the cost " +
     "band below has nothing to compare. Both must produce a priced plan for " +
     "this assertion to mean anything.");
  const ratio = four.cost / askOne.cost;
  ok(ratio >= 1 + 0.55 * 3 - 0.15 && ratio <= 4 + 0.15,
     `four travellers cost ${ratio.toFixed(2)}x one traveller (EUR ${askOne.cost} ` +
     `to EUR ${four.cost}). The cost model scales beds by 1+0.55(n-1) and ` +
     "everything else by n, so the ratio has to sit between 2.65 and 4. " +
     "Outside that band the party size is reaching the page and not the money.");

  // 2. THE DAY FLOOR. A trip shorter than the planner builds is clamped,
  //    and the clamp has to be named rather than applied behind a number
  //    the page has already printed.
  const short = await askFor("2 days in Vienna");
  ok(short.days === "3",
     `"2 days" left the day field at ${short.days}, so the floor moved`);
  ok(/You said .*2 days.* and the route below is .*3/.test(short.say),
     "the planner clamped a two-day request to three and did not say so. " +
     "It printed the number the reader typed beside a route of a different " +
     "length: " + short.say.slice(0, 200));

  // 3. THE NAMED GEOGRAPHY, which is the dishonest one, because it was not
  //    silence but a false statement. plan() honours a named country only
  //    where four destinations sit inside it, and 12 of the 47 countries in
  //    the index hold fewer — so "A week in Slovakia" planned the whole
  //    continent under the words "within Slovakia".
  const askThin = await askFor("A week in Slovakia in June");
  ok(!/within .*Slovakia/.test(askThin.say),
     "the readback claimed the route was held within Slovakia. The planner " +
     "drops a geography holding fewer than four destinations, so that " +
     "sentence describes a route through six countries: " + askThin.say.slice(0, 200));
  ok(/You named .*Slovakia.* not held to it/.test(askThin.say),
     "the planner dropped the named geography and did not name the drop. " +
     "opts.geoTooNarrow is computed on every run for exactly this: " +
     askThin.say.slice(0, 200));
  // And a country with enough to plan inside keeps its constraint, or the
  // fix above would have been satisfied by never honouring a geography.
  const wide = await askFor("Twelve days in Italy in June");
  ok(/within .*Italy/.test(wide.say),
     "Italy holds far more than four destinations and the readback stopped " +
     "claiming the route is inside it: " + wide.say.slice(0, 200));

  // ── the planner inputs the specification asks for ──────────────────
  // Every one of these was added because §10 lists it as an input. An
  // input that renders but does not change the answer is decoration, so
  // each check below asserts the *output* moved, not that the field
  // exists.
  async function planWith(fill) {
    await page.goto(base + "/plan", { waitUntil: "networkidle" });
    await page.fill("#days", "14");
    await page.fill("#budget", "3000");
    await page.check('input[name="interest"][value="history"]');
    await fill();
    await page.click('#planner button[type="submit"]');
    await page.waitForSelector("#result .leg");
    const money = await page.locator("#result .result-summary dd").first().textContent();
    return {
      route: (await page.locator("#result .leg h3 a").allTextContents()).join(" > "),
      cost: parseInt(money.replace(/[^0-9]/g, ""), 10),
      money: money.trim(),
      html: await page.locator("#result").innerHTML(),
    };
  }

  // "End near" must land the route on the city asked for, or say in words
  // that it could not. Before this was checked the planner silently
  // appended a 2,500 km final leg and called it an itinerary.
  const endOptions = await page.locator("#end option").count();
  ok(endOptions > 100, `end select carried ${endOptions} options, so it was not populated`);
  const ended = await planWith(async () => {
    await page.selectOption("#start", "france/paris-and-ile-de-france/paris");
    await page.selectOption("#end", "italy/rome-and-lazio/rome");
  });
  const lastStop = ended.route.split(" > ").pop();
  ok(lastStop === "Rome" || /a long way|straight to|forced/i.test(ended.html),
     `asked to end in Rome, ended in ${lastStop} without saying why`);
  ok(ended.route.split(" > ")[0] === "Paris", "the start city was not honoured");

  // Travellers: two people cost more than one, and not merely double —
  // the second bed is cheaper than the first.
  const one = await planWith(async () => { await page.fill("#travellers", "1"); });
  const two = await planWith(async () => { await page.fill("#travellers", "2"); });
  ok(two.cost > one.cost, `two travellers cost ${two.cost}, one cost ${one.cost}`);
  ok(two.cost < one.cost * 2, "the second traveller was charged a full second trip");

  // Accommodation style must move the number in the direction it claims.
  const guest = await planWith(async () => { await page.selectOption("#accommodation", "guesthouse"); });
  const hotel = await planWith(async () => { await page.selectOption("#accommodation", "hotel"); });
  ok(guest.cost < hotel.cost, `guesthouses (${guest.cost}) did not come in under hotels (${hotel.cost})`);

  // Rail and ferry, no flights: the route must not string together the
  // long hops that only make sense in the air.
  const rail = await planWith(async () => {
    await page.selectOption("#start", "portugal/lisbon-and-the-west/lisbon");
    await page.selectOption("#transport", "rail");
  });
  ok(!/by air/.test(rail.html), "a rail-only trip still offered a flying time");

  // Currency: the figure must change shape, and the page must say the
  // rate is dated rather than quietly presenting it as live.
  const inSek = await planWith(async () => { await page.selectOption("#currency", "SEK"); });
  ok(!inSek.money.startsWith("€"), `asked for SEK and got ${inSek.money}`);
  ok(/indicative, dated rate/.test(inSek.html),
     "a converted figure did not say the rate is indicative and dated");

  // Travel time between stops, in words, on every hop after the first.
  const hopNotes = await page.locator("#result .hop").allTextContents();
  ok(hopNotes.length >= 2, "the itinerary carried no travel notes between stops");
  // hoursText writes "3h 20m" and "45 minutes"; a note carrying only a
  // distance is the thing being ruled out here.
  ok(hopNotes.every((t) => /\d+h\b|\d+ minutes/.test(t)),
     "a travel note gave a distance but no travelling time");

  // Saved places: a place saved in My Europe must be favoured. We seed
  // localStorage on the origin the page will read it from.
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.evaluate(() => {
    // The same shape My Europe writes: the id is what the planner keys on.
    localStorage.setItem("europedoor.saved.v1", JSON.stringify([
      { id: "city:north-macedonia/ohrid-and-the-southwest/ohrid", kind: "City", label: "Ohrid" },
    ]));
  });
  // Started next door to the saved place, so this tests the boost rather
  // than testing whether one 1.6x multiplier can beat the whole continent:
  // the boost is a preference, and claiming it is a guarantee would be the
  // check lying about the code.
  const withSaved = await planWith(async () => {
    await page.selectOption("#start", "albania/tirana-and-the-south/tirana");
    await page.check("#saved");
  });
  ok(/Ohrid/.test(withSaved.route),
     `favouring a saved place did not put it in the route: ${withSaved.route}`);
  await page.evaluate(() => localStorage.removeItem("europedoor.saved.v1"));

  // ── why each stop, and not the runner-up ───────────────────────────
  // The old line said "Matches history & ruins, food." on every leg of an
  // itinerary built from history and food — the reader's own filter read
  // back to them twelve times. Same rule as Discover Mode: the shared
  // reason goes once, each leg carries what distinguishes it.
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.fill("#days", "14");
  await page.selectOption("#month", "oct");
  for (const i of ["mountains", "history"]) {
    await page.check(`input[name="interest"][value="${i}"]`);
  }
  await page.click('#planner button[type="submit"]');
  await page.waitForSelector("#result .leg");
  const hoists = await page.locator("#result .whyall").allTextContents();
  ok(hoists.some((t) => /because that is what you asked for/.test(t)),
     "the itinerary does not hoist the shared reason");
  ok(hoists.some((t) => /out in both directions/.test(t)),
     "the itinerary does not hoist what its distances and times are worth");
  ok(hoists.length <= 3,
     `${hoists.length} hoisted blocks above the first stop — a preamble, ` +
     "which is the boilerplate the hoist exists to prevent");
  const legWhy = await page.locator("#result .leg .mt-tight").allTextContents();
  ok(legWhy.length >= 3, "legs carry no why-line");

  // AND THE PROMISE THE CEILING WAS STANDING IN FOR: no clause may appear on
  // every leg. Rendering a real twelve-day Italian route showed five of six
  // stops opening on the same forty words — "is here for the shape of the
  // route rather than your interests — it sits between two places that did
  // match" — and closing on the same "€123 a day here", with the one
  // differing clause buried between them. Individually true, collectively
  // boilerplate, and this repository's own rule for exactly this surface.
  //
  // Split on the semicolons the sentence is joined with, and on the rate,
  // and count how many legs carry each clause.
  {
    const legs = await page.locator("#result .leg").count();
    const seen = {};
    for (const t of legWhy) {
      const own = new Set(t.replace(/^[^ ]+ is /, "")
                           .split(/[;.] ?/)
                           .map((x) => x.trim())
                           .filter((x) => x.length > 12));
      for (const clause of own) seen[clause] = (seen[clause] || 0) + 1;
    }
    const everywhere = Object.keys(seen).filter((k) => seen[k] === legs && legs >= 3);
    ok(everywhere.length === 0,
       `a clause is on all ${legs} legs and was not hoisted: ` +
       everywhere.map((c) => JSON.stringify(c.slice(0, 60))).join(", "));
  }
  ok(!legWhy.some((t) => /^Matches /.test(t.trim())),
     "a leg still restates the interests the reader chose");
  ok(legWhy.some((t) => /also |shoulder season|discoverability|not written it up/.test(t)),
     "no leg says anything the reader did not already ask for");
  // Two conjunctions colliding is what happens when clauses that each
  // contain "and" are joined with another one.
  ok(!legWhy.some((t) => / and .* and at its /.test(t)),
     "a why-line has two conjunctions colliding");

  // ── What if? ───────────────────────────────────────────────────────
  // What separates this from a row of preset buttons is that it shows the
  // consequence BEFORE applying it. A button that silently rebuilds the
  // itinerary is a slot machine: after three presses the reader has lost
  // the plan they liked and cannot tell what any press cost them.
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.fill("#days", "12");
  await page.fill("#budget", "2500");
  for (const i of ["history", "food"]) {
    await page.check(`input[name="interest"][value="${i}"]`);
  }
  await page.click('#planner button[type="submit"]');
  await page.waitForSelector("#result .leg");
  const routeBefore = (await page.locator("#result .leg h3 a").allTextContents()).join(">");

  ok(await page.locator("#whatif [data-whatif]").count() >= 5,
     "fewer than five what-ifs offered");
  // The one it refuses, and says why. We hold no weather data.
  ok(/What if it rains/.test(await page.locator("#whatif").innerText()),
     "the panel does not name the question it cannot answer");
  ok(/no weather data/.test(await page.locator("#whatif").innerText()),
     "and does not say why it cannot answer it");

  // Preview first: the route must not move until Apply is pressed.
  await page.click('[data-whatif="cheaper"]');
  await page.waitForSelector("#whatif-out .whatif-preview");
  const preview = await page.locator("#whatif-out").innerText();
  ok(/instead of/.test(preview), "the preview does not compare against the current plan");
  ok(/€/.test(preview), "the preview does not price the change");
  ok((await page.locator("#result .leg h3 a").allTextContents()).join(">") === routeBefore,
     "previewing a what-if changed the itinerary before it was applied");
  ok(await page.locator("#whatif-keep").count() === 1,
     "there is no way to decline a what-if");

  // Keeping leaves it alone.
  await page.click("#whatif-keep");
  await page.waitForTimeout(120);
  ok((await page.locator("#result .leg h3 a").allTextContents()).join(">") === routeBefore,
     "declining a what-if still changed the plan");

  // Applying does change it, says so, and is not a dead end.
  await page.click('[data-whatif="quieter"]');
  await page.waitForSelector("#whatif-out .whatif-preview");
  const quietPreview = await page.locator("#whatif-out").innerText();
  ok(/You lose|Nothing would change/.test(quietPreview),
     "the crowd-avoiding what-if says nothing about what it swaps");
  if (/You lose/.test(quietPreview)) {
    await page.click("#whatif-apply");
    await page.waitForTimeout(400);
    const routeAfter = (await page.locator("#result .leg h3 a").allTextContents()).join(">");
    ok(routeAfter !== routeBefore, "applying a what-if did not change the itinerary");
    ok(/Applied:/.test(await page.locator("#result .note").first().innerText()),
       "an applied what-if does not say it was applied");
    ok(await page.locator("#replan").count() === 1,
       "an applied what-if leaves no way back to the form");
  }

  // The two that replan must warn that they do — the order can move more
  // than a reader expects.
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.fill("#days", "12");
  await page.click('#planner button[type="submit"]');
  await page.waitForSelector("#result .leg");
  await page.click('[data-whatif="rail"]');
  await page.waitForSelector("#whatif-out");
  const railText = await page.locator("#whatif-out").innerText();
  ok(/replans|Nothing would change/.test(railText),
     "the rail what-if does not warn that it replans");

  // ── editing an itinerary ───────────────────────────────────────────
  // The difference between a suggestion and a plan. Every control is a real
  // button with a real label, so this is also the accessibility check for
  // the feature — there is no drag-and-drop to be untestable.
  async function freshPlan() {
    await page.goto(base + "/plan", { waitUntil: "networkidle" });
    await page.fill("#days", "14");
    await page.fill("#budget", "3000");
    await page.check('input[name="interest"][value="history"]');
    await page.click('#planner button[type="submit"]');
    await page.waitForSelector("#result .leg");
    return (await page.locator("#result .leg h3 a").allTextContents());
  }
  const startRoute = await freshPlan();
  ok(startRoute.length >= 4, `only ${startRoute.length} stops to edit`);

  // Reorder. The second stop becomes the first.
  await page.click('.leg:nth-child(2) [data-move][data-dir="-1"]');
  await page.waitForSelector("#result .note");
  const reordered = await page.locator("#result .leg h3 a").allTextContents();
  ok(reordered[0] === startRoute[1] && reordered[1] === startRoute[0],
     `reorder did not swap: ${startRoute.slice(0,2)} -> ${reordered.slice(0,2)}`);
  ok(/You have changed this itinerary/.test(await page.locator("#result").innerHTML()),
     "an edited itinerary did not say it had been edited");
  // The first stop can never move earlier.
  ok(await page.locator('.leg:nth-child(1) [data-move][data-dir="-1"]').isDisabled(),
     "the first stop offers to move earlier");

  // Remove. The route shortens and the days follow the nights, rather than
  // silently reflowing into a length the reader did not choose.
  const daysBefore = Number(await page.inputValue("#days"));
  await page.click('.leg:nth-child(2) [data-drop]');
  await page.waitForTimeout(150);
  const afterDrop = await page.locator("#result .leg h3 a").allTextContents();
  ok(afterDrop.length === reordered.length - 1,
     `removing a stop left ${afterDrop.length} of ${reordered.length}`);
  ok(!afterDrop.includes(reordered[1]), `${reordered[1]} was removed but is still in the route`);
  const daysAfter = Number(await page.inputValue("#days"));
  ok(daysAfter < daysBefore, `days did not follow the removed stop: ${daysBefore} -> ${daysAfter}`);

  // Nights. The estimate must move with them — an editable itinerary whose
  // cost does not change is a list, not a plan.
  const costBefore = parseInt((await page.locator("#result .result-summary dd").first()
                              .textContent()).replace(/[^0-9]/g, ""), 10);
  await page.click('.leg:nth-child(1) [data-nights][data-by="1"]');
  await page.waitForTimeout(150);
  const costAfter = parseInt((await page.locator("#result .result-summary dd").first()
                             .textContent()).replace(/[^0-9]/g, ""), 10);
  ok(costAfter > costBefore, `adding a night did not change the estimate: ${costBefore} -> ${costAfter}`);
  // And a stop can never go below one night.
  for (let i = 0; i < 20; i++) {
    const btn = page.locator('.leg:nth-child(1) [data-nights][data-by="-1"]');
    if (await btn.isDisabled()) break;
    await btn.click();
    await page.waitForTimeout(60);
  }
  ok(await page.locator('.leg:nth-child(1) [data-nights][data-by="-1"]').isDisabled(),
     "a stop can be reduced below one night");

  // Adding a stop. A filter over the Atlas already in memory, rendered as
  // real buttons — so this is also the accessibility check.
  const beforeAdd = await page.locator("#result .leg h3 a").allTextContents();
  await page.click('.leg:nth-child(1) [data-add]');
  await page.waitForSelector(".addstop:not([hidden]) .addq");
  ok(await page.locator('.leg:nth-child(1) [data-add]').getAttribute("aria-expanded") === "true",
     "the add control does not report that it opened");
  await page.fill(".addstop:not([hidden]) .addq", "gh");
  await page.waitForTimeout(120);
  ok(await page.locator(".addstop:not([hidden]) .addhit").count() > 0,
     "two letters returned nothing");
  // Accent folding, the same as search: a reader who can find Malmö there
  // and not here would be right to think one of them is broken.
  await page.fill(".addstop:not([hidden]) .addq", "malmo");
  await page.waitForTimeout(120);
  const addRow = await page.locator(".addstop:not([hidden]) .addhit").first().textContent();
  ok(/Malmö/.test(addRow), `"malmo" did not find Malmö: ${addRow}`);
  // Every row states the distance from the stop it would follow.
  ok(/\d+ km/.test(addRow), `an add-a-stop row gave no distance: ${addRow}`);

  await page.click(".addstop:not([hidden]) .addhit");
  await page.waitForTimeout(200);
  const afterAdd = await page.locator("#result .leg h3 a").allTextContents();
  ok(afterAdd.length === beforeAdd.length + 1,
     `adding a stop gave ${afterAdd.length} from ${beforeAdd.length}`);
  ok(afterAdd[1] === "Malmö", `the stop landed at ${afterAdd[1]}, not second`);
  ok(afterAdd[0] === beforeAdd[0], "adding a stop moved the one before it");

  // A stop already on the route must never be offered twice.
  await page.click('.leg:nth-child(1) [data-add]');
  await page.waitForSelector(".addstop:not([hidden]) .addq");
  await page.fill(".addstop:not([hidden]) .addq", "malmo");
  await page.waitForTimeout(120);
  const offeredAgain = await page.locator(".addstop:not([hidden]) .addhit").allTextContents();
  ok(!offeredAgain.some((t) => /Malmö/.test(t)),
     "a city already on the route was offered again");
  await page.click('.leg:nth-child(1) [data-add]');   // close it

  // A disclosure that TAKES focus has to give it back. The panel focused its
  // search box on open and offered no keyboard way out at all: shift-tab
  // over the trigger was the only exit, and nothing closed it.
  await page.click('.leg:nth-child(1) [data-add]');
  await page.waitForSelector(".addstop:not([hidden]) .addq");
  await page.press(".addstop:not([hidden]) .addq", "Escape");
  await page.waitForTimeout(150);
  ok(await page.locator(".addstop:not([hidden])").count() === 0,
     "Escape did not close the add-a-stop panel");
  ok(await page.evaluate(() => document.activeElement &&
                               document.activeElement.hasAttribute("data-add")),
     "Escape closed the panel and dropped focus to nowhere");

  // The result of typing has to be ANNOUNCED. It used to be an <li> inside a
  // role="listbox" whose children carried no role — a listbox reporting zero
  // options while eight buttons were on the screen.
  ok(await page.locator("#result [role=listbox]").count() === 0,
     "the add-a-stop results still claim to be a listbox");
  await page.click('.leg:nth-child(1) [data-add]');
  await page.waitForSelector(".addstop:not([hidden]) .addq");
  const sayRest = await page.locator(".addstop:not([hidden]) .addsay").innerText();
  ok(/letters/.test(sayRest), `the add panel says nothing at rest: "${sayRest}"`);
  await page.fill(".addstop:not([hidden]) .addq", "gh");
  await page.waitForTimeout(150);
  const sayHits = await page.locator(".addstop:not([hidden]) .addsay").innerText();
  const nHits = await page.locator(".addstop:not([hidden]) .addhit").count();
  ok(new RegExp("\\b" + nHits + "\\b").test(sayHits),
     `the status says "${sayHits}" over ${nHits} rows`);
  await page.press(".addstop:not([hidden]) .addq", "Escape");

  // Sharing an edited plan must carry the EDIT, not the inputs. This is the
  // whole point of the frozen route: regenerating from the form would run
  // the planner again, and the planner jitters.
  const editedRoute = await page.locator("#result .leg h3 a").allTextContents();
  await page.click("#shareplan");
  await page.waitForTimeout(150);
  const sharedUrl = page.url();
  ok(/[?&]r=/.test(sharedUrl), "the shared link does not carry the route itself");
  await page.goto(sharedUrl, { waitUntil: "networkidle" });
  await page.waitForSelector("#result .leg");
  const restored = await page.locator("#result .leg h3 a").allTextContents();
  ok(restored.join("|") === editedRoute.join("|"),
     `a shared edited plan came back different:\n  saved:    ${editedRoute.join(" > ")}\n  restored: ${restored.join(" > ")}`);

  // Starting again from the form abandons the edit rather than compounding it.
  await page.click('#planner button[type="submit"]');
  await page.waitForSelector("#result .leg");
  ok(!/You have changed this itinerary/.test(await page.locator("#result").innerHTML()),
     "a fresh plan still claimed to be an edited one");

  // ── refusing, instead of fabricating ───────────────────────────────
  // The UI specification's sharpest line: "Do not fabricate a result just to
  // avoid an error." This planner scores every city in the Atlas, so it can
  // always return SOMETHING — which is exactly the failure being described.
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.fill("#days", "21");
  await page.fill("#budget", "300");
  await page.selectOption("#style", "high");
  await page.selectOption("#accommodation", "hotel");
  await page.click('#planner button[type="submit"]');
  await page.waitForSelector("#result .note.warn");
  const refused = await page.locator("#result").innerHTML();
  ok(/could not build a journey we would stand behind/.test(refused),
     "a hopeless budget produced a confident itinerary instead of a refusal");
  ok(/against a budget of/.test(refused), "the refusal did not name the constraint");
  ok(/data-focus="budget"/.test(refused),
     "the refusal did not offer the control that would fix it");
  ok(await page.locator("#result .leg").count() === 0,
     "the refusal rendered the rejected itinerary as if it were an answer");
  // Never a dead end: the rejected plan is available, marked as rejected.
  await page.click("#result details summary");
  await page.waitForSelector("#result details .leg");
  ok(await page.locator("#result details .leg").count() > 0,
     "the rejected plan could not be inspected at all");

  // And the refusal must not fire on a budget the reader never gave. The
  // first version refused "three weeks in the Alps, luxury" against our own
  // €2,500 default, which is refusing our own assumption.
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.fill("#ask", "three weeks by train through the alps in winter, luxury");
  await page.click('#askform button[type="submit"]');
  await page.waitForSelector("#result .leg");
  const assumed = await page.locator("#result").innerHTML();
  ok(!/could not build a journey/.test(assumed),
     "the planner refused against a budget the sentence never stated");
  ok(/over budget/.test(assumed),
     "an expensive plan on an assumed budget said nothing about the cost");

  // A NAME THIS PLANNER CANNOT SEE IS THE ONE THING IT CANNOT REPORT.
  //
  // `words()` stripped the sentence to [a-z0-9] and compared it against names
  // that were only lowercased, so 77 of 313 destinations and Türkiye could
  // not be typed at all — and the planner's whole pitch is that it names
  // anything it could not take account of. It cannot name a word it never
  // saw. One name per spelling this repository actually has to handle: a
  // combining acute, a stroked o with no decomposition, a compound name
  // whose ampersand the sentence loses, and the one country.
  for (const [typed, expect] of [["Ten days from Kraków", "Kraków"],
                                 ["A week from Tromsø", "Tromsø"],
                                 ["Five days from Kardamyli & the Mani", "Kardamyli"],
                                 ["Twelve days in Türkiye", "Türkiye"]]) {
    await page.goto(base + "/plan", { waitUntil: "networkidle" });
    await page.fill("#ask", typed);
    await page.click('#askform button[type="submit"]');
    await page.waitForSelector("#result");
    const read = await page.locator("#result").innerText();
    ok(read.includes(expect),
       `the planner read ${JSON.stringify(typed)} and its readback never `
       + `mentions ${expect} — a name it cannot see is the one failure it `
       + `cannot report`);
  }

  // ── the staged wait ────────────────────────────────────────────────
  // Never a bare "Loading…". Each step is ticked when its work has actually
  // finished, so a failure marks where it stopped.
  // ASSETS ARE CONTENT-ADDRESSED, so the served URL carries a hash and the
  // literal path 404s. Resolve it from the page that loads it — which is
  // also the stronger test: it fetches the script this page actually runs,
  // not one that happens to sit at a path.
  const plannerUrl = await page.evaluate(() => {
    const el = [...document.querySelectorAll("script[src]")]
      .find((s) => /\/assets\/js\/planner\./.test(s.getAttribute("src")));
    return el ? el.getAttribute("src") : null;
  });
  ok(!!plannerUrl, "/plan does not load a planner script");
  const js = await (await page.request.get(base + plannerUrl)).text();
  ok(/Building your journey/.test(js), "there is no staged wait");
  ok(/Understanding what you asked for/.test(js), "the wait does not say what it is doing");
  ok(!/>Loading\.\.\.</.test(js) && !/>Loading…</.test(js),
     "a bare Loading… survived somewhere");
  ok(/role="status"/.test(js), "the staged wait is not announced to a screen reader");

  // ── My Europe: moving a saved list between browsers ────────────────
  // The specification files "a saved journey follows you between devices"
  // under authentication. It needs authentication only if the copy happens
  // on our side. This does it as text, so we still hold nothing.
  await page.goto(base + "/my-europe", { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("europedoor.saved.v1", JSON.stringify([
      { id: "city:norway/fjord-norway/bergen", kind: "City", label: "Bergen",
        url: "/europe/norway/fjord-norway/bergen" },
    ]));
    localStorage.setItem("europedoor.collections.v1", JSON.stringify(["Summer"]));
  });
  await page.reload({ waitUntil: "networkidle" });
  const exported = await page.locator("#portable").inputValue();
  const parsed = JSON.parse(exported);
  ok(parsed.saved.length === 1 && parsed.saved[0].label === "Bergen",
     "the saved list did not export as text");
  ok(parsed.collections.includes("Summer"), "collections were not carried in the export");

  // A second browser: clear everything, paste the text back, expect the list.
  await page.evaluate(() => { localStorage.clear(); });
  await page.reload({ waitUntil: "networkidle" });
  ok(await page.locator("#portable").count() === 0,
     "the empty state should not offer a transfer box with nothing in it");
  await page.evaluate(() => {
    localStorage.setItem("europedoor.saved.v1", JSON.stringify([
      { id: "city:italy/rome-and-lazio/rome", kind: "City", label: "Rome",
        url: "/europe/italy/rome-and-lazio/rome" },
    ]));
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.fill("#portable", exported);
  await page.click('#transfer button[type="submit"]');
  await page.waitForFunction(() => /item.? added/.test(
    document.getElementById("transferstate").textContent));
  const imported = await page.locator("#mine .saved h3").allTextContents();
  ok(imported.some((t) => /Bergen/.test(t)), "the imported item did not appear");
  ok(imported.some((t) => /Rome/.test(t)),
     "importing replaced the list that was already there instead of merging into it");

  // Pasted text is untrusted: it arrived by being pasted and could be
  // anything. An off-site url must not end up as a link on the reader's own
  // page.
  await page.evaluate(() => { localStorage.clear(); });
  await page.reload({ waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("europedoor.saved.v1", JSON.stringify([
      { id: "city:italy/rome-and-lazio/rome", kind: "City", label: "Rome",
        url: "/europe/italy/rome-and-lazio/rome" },
    ]));
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.fill("#portable", JSON.stringify({ v: 1, saved: [
    { id: "evil", kind: "City", label: "Elsewhere", url: "https://example.invalid/" },
    { id: "evil2", kind: "City", label: "Protocol", url: "javascript:alert(1)" },
    { id: "evil3", kind: "City", label: "Schemeless", url: "//example.invalid/" },
  ] }));
  await page.click('#transfer button[type="submit"]');
  await page.waitForFunction(() => /ignored/.test(
    document.getElementById("transferstate").textContent));
  const links = await page.locator("#mine .saved h3 a").evaluateAll(
    (as) => as.map((a) => a.getAttribute("href")));
  for (const h of links) {
    ok(h.startsWith("/") && !h.startsWith("//"),
       `an imported list put an off-site link on the page: ${h}`);
  }
  await page.evaluate(() => { localStorage.clear(); });

  // ── the follow-up questions ────────────────────────────────────────
  // §19: ask only what changes the answer, and answer anyway. A sentence
  // with no length and no budget must still produce a plan AND put both
  // questions.
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.fill("#ask", "somewhere with good food and old towns");
  await page.click('#askform button[type="submit"]');
  await page.waitForSelector("#result .leg");
  const askHtml = await page.locator("#result").innerHTML();
  ok(/How many days/.test(askHtml), "an ask with no length did not ask how many days");
  ok(/can you spend/.test(askHtml), "an ask with no budget did not ask about spending");
  ok(await page.locator("#result .leg").count() >= 3,
     "the planner asked the questions but did not answer anyway");

  // And a sentence that says everything must ask nothing.
  await page.goto(base + "/plan", { waitUntil: "networkidle" });
  await page.fill("#ask", "10 days in Italy in May, about 2000 euros, art and food");
  await page.click('#askform button[type="submit"]');
  await page.waitForSelector("#result .leg");
  const fullHtml = await page.locator("#result").innerHTML();
  ok(!/How many days|can you spend/.test(fullHtml),
     "the planner asked for information the sentence had already given");

  // ── the travel profile ─────────────────────────────────────────────
  // A preference model, and the brief is explicit it must never read as
  // psychological truth. These checks are mostly about that: the
  // denominator, the floor, the editability, and the wording.
  await page.goto(base + "/my-europe", { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("europedoor.saved.v1", JSON.stringify([
      { id: "city:norway/fjord-norway/bergen", kind: "City", label: "Bergen", url: "/x" },
      { id: "city:italy/tuscany-and-the-centre/siena", kind: "City", label: "Siena", url: "/x" },
    ]));
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(300);
  const thin = await page.locator("#dna").innerText();
  // Three saves is noise wearing a percentage sign.
  ok(/Save at least 4/.test(thin), "the profile appears below its own floor");
  ok(/You have 2 so far/.test(thin), "and does not say how far off the floor you are");
  ok(await page.locator("#dna .dnarow").count() === 0,
     "rows were drawn from two saved places");

  await page.evaluate(() => {
    localStorage.setItem("europedoor.saved.v1", JSON.stringify([
      "norway/fjord-norway/bergen", "italy/tuscany-and-the-centre/siena",
      "greece/the-peloponnese/kardamyli", "france/alps-and-east/chamonix",
      "austria/salzburg-and-the-lakes/hallstatt",
    ].map((id) => ({ id: "city:" + id, kind: "City", label: id, url: "/x" }))));
    localStorage.removeItem("europedoor.dna.v1");
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(400);
  const dna = await page.locator("#dna").innerText();
  ok(await page.locator("#dna .dnarow").count() >= 3, "the profile drew no rows");
  // A profile with no denominator is a claim.
  ok(/Computed from the \d+ places/.test(dna),
     "the profile does not say what it was computed from");
  ok(/not a personality test/.test(dna),
     "the profile does not say what it is not");
  ok(/derived on this page every time/.test(dna),
     "the profile does not say it is not stored");

  // A model of you that you cannot correct is a model being done to you.
  const firstBefore = await page.locator("#dna .dnarow").first().innerText();
  await page.click('#dna [data-dna][data-by="-10"]');
  await page.waitForTimeout(250);
  ok(/\(adjusted\)/.test(await page.locator("#dna").innerText()),
     "an adjusted row is not marked as adjusted");
  await page.click("#dnareset");
  await page.waitForTimeout(250);
  ok(!/\(adjusted\)/.test(await page.locator("#dna").innerText()),
     "resetting the profile left an override behind");
  ok((await page.locator("#dna .dnarow").first().innerText()) === firstBefore,
     "resetting did not restore what the saves say");

  // And it has to be useful, or it should not exist: the CTA must land on a
  // planner with those interests already chosen. No dead buttons.
  const dnaPlan = await page.locator('#dna a[href^="/plan?i="]').getAttribute("href");
  ok(dnaPlan && dnaPlan.length > 9, "the profile does not hand anything to the planner");
  await page.goto(base + dnaPlan, { waitUntil: "networkidle" });
  /* NOT `checked`: that is the suite's own counter, declared at module
   * scope, and a const of the same name inside main() put the whole
   * function body in its temporal dead zone. The suite reported "all 4
   * browser checks passed" and exited 0 — a green run that had silently
   * stopped counting. A test harness that can lie about how much it ran is
   * worse than one that fails. */
  const preselected = await page.locator('input[name="interest"]:checked').count();
  ok(preselected >= 3, `the profile's link pre-selected ${preselected} interests`);

  await page.evaluate(() => localStorage.clear());

  // ── Discover Mode ──────────────────────────────────────────────────
  // The surface that answers "I don't know where I want to go", and the
  // only one on the site where every recommendation has to justify itself.
  await page.goto(base + "/discover", { waitUntil: "networkidle" });
  // IT PINNED THE LOOK OF THE CONTROL AND THE LOOK WAS THE THING THAT
  // CHANGED. `.chip.pick` was the outlined pill; Decision 2 made the
  // seventeen large type, and the assertion went red for a page that had
  // got better — the twelfth shape pinned instead of a promise here. What
  // matters is that seventeen interests are on the page as real controls a
  // reader can press, so it reads `data-interest`, which is the contract
  // the application binds to, and asserts the control rather than its skin.
  {
    const picks = page.locator("#discover-interests [data-interest]");
    ok(await picks.count() >= 16,
       `Discover offers ${await picks.count()} interests to choose from`);
    ok(await page.locator('#discover-interests button[aria-pressed]').count()
       === await picks.count(),
       "every interest is a button that reports whether it is pressed");
  }
  ok(await page.locator("#discover-results .row").count() === 0,
     "Discover Mode showed results before anything was chosen");

  // THE DRAWING IS THE OUTPUT, AND AT REST IT IS THE WHOLE CONTINENT.
  //
  // /discover was a filter panel with a picture of Europe under it that did
  // not respond to the panel — the GIS-application reading, and the one the
  // brief names first. These assert the PROMISE rather than the markup: a
  // page nobody has touched draws every place as itself, a narrowing lights
  // exactly what the page says it found, a place that drops out keeps its
  // dot, and an advisory place is never lit.
  const dotsAll = await page.locator("#discover-map [data-city]").count();
  ok(dotsAll > 300, `the discover map draws ${dotsAll} places`);
  ok(await page.locator("#discover-map .unlit, #discover-map .lit").count() === 0,
     "a page nobody has touched drew a dimmed Europe");

  for (const i of ["mountains", "history", "food"]) {
    await page.click(`[data-interest="${i}"]`);
  }
  await page.waitForTimeout(150);
  // Toggle buttons, not styled checkboxes: a screen reader should hear
  // "Mountains, pressed".
  ok(await page.locator('[data-interest="mountains"]').getAttribute("aria-pressed") === "true",
     "a chosen interest does not report itself pressed");
  const picked = await page.locator("#discover-results .row").count();
  ok(picked > 0 && picked <= 12, `Discover Mode returned ${picked} rows`);

  // The number above the map and the number of lit places are the same
  // claim, and a drawing that disagrees with the sentence over it is worse
  // than a drawing that says nothing.
  const stateLine = (await page.locator("#discover-count").textContent()).trim();
  const stated = Number((stateLine.match(/^(\d+) plac/) || [])[1]);
  const litNow = await page.locator("#discover-map .lit").count();
  ok(stated > 0 && litNow === stated,
     `the page says ${stated} places fit and the map lights ${litNow}`);
  // Nothing is deleted: the shape of Europe is the point of the drawing.
  ok(await page.locator("#discover-map [data-city]").count() === dotsAll,
     "narrowing removed places from the map instead of dimming them");
  ok(await page.locator("#discover-map .advisory.lit").count() === 0,
     "an advisory country's place was lit by Discover Mode");
  // A dimmed place has to be visibly dimmer than a lit one, or "narrows
  // itself" is a sentence with no picture behind it. Measured on the
  // computed values, because both are painted by a class.
  const step = await page.evaluate(() => {
    const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
      const c = getComputedStyle(e); return [Number(c.opacity), Number(c.r.replace('px',''))]; };
    return { lit: g("#discover-map .lit"), unlit: g("#discover-map .unlit") };
  });
  ok(step.lit && step.unlit && step.lit[0] > step.unlit[0] && step.lit[1] > step.unlit[1],
     `a lit place measures ${JSON.stringify(step.lit)} and an unlit one ` +
     `${JSON.stringify(step.unlit)} — no step, so the map says nothing`);

  // Every result explains itself. This is the point of the feature.
  const whys = await page.locator("#discover-results .whythis").count();
  ok(whys === picked, `${picked} results but ${whys} explanations`);

  // At most two per country, or the list has told you about one corner of
  // Europe rather than about Europe.
  const countries = await page.locator("#discover-results .rowmeta").allTextContents();
  const perCountry = {};
  for (const c of countries) {
    const k = c.split("\n")[0].trim();
    perCountry[k] = (perCountry[k] || 0) + 1;
  }
  ok(Object.values(perCountry).every((n) => n <= 2),
     `a country appears ${Math.max(...Object.values(perCountry))} times in twelve results`);

  // Constraints must actually constrain.
  await page.check("#discover-quiet");
  await page.waitForTimeout(200);
  const quietRows = await page.locator("#discover-results .whythis").allTextContents();
  ok(quietRows.every((t) => /discoverability/.test(t)),
     "asking for off-the-circuit places did not change what the results say");
  // SCOPED TO THE RESULTS. `.whyall` is the shared-reason primitive and
  // /discover now carries a second one: the year band's legend, which is the
  // same promise about a different set. A bare `.whyall` on this page matched
  // two elements and the run died in strict mode — the assertion was reading
  // "the page has a hoisted reason" when it means "these results do".
  const lead = await page.locator("#discover-results .whyall").textContent();
  ok(/off the obvious circuit/.test(lead),
     "the shared reason was not hoisted out of the individual cards");
  // The filter itself must not be repeated on every card — that is the
  // boilerplate this design exists to remove.
  ok(!quietRows.some((t) => /carries every one of/.test(t)),
     "each card still restates the filter the reader set");

  // AND THE GENERAL FORM, WHICH THE NAMED ONE WAS STANDING IN FOR. The
  // hoist looked only at the clauses coming from the reader's filters, not
  // at the ones a place adds on its own — so "is one we have written up
  // properly" was on all twelve rows, under a line saying that what follows
  // is what else is true of EACH one. Same fault the planner had, on the
  // page where this rule was written.
  // Read from the state this section has already built rather than
  // navigating: the assertions that follow depend on the off-the-circuit
  // filter being set, and reloading the page to run this test silently
  // cleared it — two capitals "survived" a filter that was no longer on.
  {
    const rows = quietRows;
    const seen = {};
    for (const t of rows) {
      const own = new Set(t.replace(/^Why this \S+ /, "")
                           .split(/[;.] ?/).map((x) => x.trim())
                           .filter((x) => x.length > 10));
      for (const c of own) seen[c] = (seen[c] || 0) + 1;
    }
    const everywhere = Object.keys(seen).filter((k) => seen[k] === rows.length);
    ok(rows.length >= 3, "Discover Mode returned too few rows to test the hoist");
    ok(everywhere.length === 0,
       `a clause is on all ${rows.length} Discover Mode rows and was not ` +
       `hoisted: ${everywhere.map((c) => JSON.stringify(c.slice(0, 60))).join(", ")}`);
  }

  // No capital should survive the off-the-circuit filter, since not being
  // one is the largest single term in the score.
  await page.selectOption("#discover-month", "oct");
  await page.waitForTimeout(200);
  const names = await page.locator("#discover-results h3").allTextContents();
  for (const capital of ["Paris", "London", "Madrid", "Rome", "Berlin", "Vienna"]) {
    ok(!names.includes(capital), `${capital} survived the off-the-circuit filter`);
  }

  // Clearing puts it back to the empty state rather than a stale list.
  await page.click("#discover-clear");
  await page.waitForTimeout(150);
  ok(await page.locator("#discover-results .row").count() === 0,
     "clearing Discover Mode left the previous results on screen");
  ok(await page.locator('[data-interest="mountains"]').getAttribute("aria-pressed") === "false",
     "clearing left a chip still pressed");
  ok(await page.locator("#discover-map .unlit, #discover-map .lit").count() === 0,
     "clearing left the previous search lit on the map");

  // The score behind it is published, or it is a ranking nobody should trust.
  const method = await page.request.get(base + "/method");
  ok(method.status() === 200, "/method is not served");
  const methodHtml = await method.text();
  ok(/id="discoverability"/.test(methodHtml), "discoverability is not published on /method");
  ok(/not a crowd measurement/i.test(methodHtml),
     "/method does not say what discoverability is not");

  // ── the homepage as a progression ──────────────────────────────────
  // The specification asks the homepage to move a reader through open,
  // discover, wonder, understand, plan, go — rather than be a grid of
  // thirty cards. A progression nobody can see is just an ordering, so the
  // steps are named on the page and checked in order here.
  //
  // THE HOMEPAGE IS NOW THREE BANDS AND NAMES TWO OF THOSE SIX STEPS. It
  // used to name all six, one per band, and that was the version of this
  // page that read as a contents list: every step present because every
  // step was worth a section. The progression survives as an ordering the
  // reader walks — hero, then discover, then go — and what is checked is
  // that whatever steps ARE named appear in the canonical order. That is a
  // weaker assertion than the one it replaces, deliberately: a check that
  // demands six bands is a check that forbids restraint.
  await page.goto(base + "/", { waitUntil: "networkidle" });
  // THE PROGRESSION IS NUMBERED NOW, NOT CHIPPED. This read `.stage`, which
  // `render.section()` emits and which the homepage stopped using when it
  // became a plate sequence — so it found an empty list and died on
  // `stages[-1].trim()`, taking the whole suite down before check one.
  // Eighteenth assertion here to pin a mechanism rather than a promise.
  const acts = await page.locator(".actmark").evaluateAll((els) => els.map((e) => [
    e.querySelector(".actno") ? e.querySelector(".actno").textContent.trim() : "",
    e.querySelector(".actname") ? e.querySelector(".actname").textContent.trim() : ""]));
  const seq = acts.map((a) => a[1]).join(" > ");
  ok(acts.length >= 4, `the homepage names ${acts.length} plates (${seq})`);
  ok(acts.every((a, i) => a[0] === String(i + 1).padStart(2, "0")),
     `the plates are not numbered in order: ${acts.map((a) => a[0]).join(",")}`);
  ok(acts.length > 0 && /door/i.test(acts[0][1]),
     `the sequence opens on ${acts.length ? acts[0][1] : "nothing"} rather than the door`);
  // AND IT HANDS THE READER ONWARD AT THE END, which is what "ends on Go"
  // was claiming. The last plate carries a link out of the page.
  ok(await page.locator("section:last-of-type .go").count() >= 1,
     "the last plate does not hand the reader anywhere");
  // One plate changes ground, so the rhythm is felt rather than merely
  // intended. It was `.band.tone-quiet`; it is the atlas plate now.
  const grounds = await page.locator("main section").evaluateAll((els) => {
    const seen = new Set();
    for (const e of els) seen.add(getComputedStyle(e).backgroundColor);
    return Array.from(seen);
  });
  ok(grounds.length >= 2,
     `every plate is on the same ground (${grounds.join(", ")}) — no rhythm`);
  for (const w of [1280, 390]) {
    await page.setViewportSize({ width: w, height: 900 });
    const over = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    ok(over <= 1, `the full-bleed band overflows by ${over}px at ${w}`);
  }
  await page.setViewportSize({ width: 1280, height: 900 });

  // ── Europe in Motion ───────────────────────────────────────────────
  // The trap in "dynamic discovery layer" is that the cheap version — a
  // banner over a hand-picked list — looks identical to the real one on the
  // day it ships and is wrong within a season. These checks are all about
  // that distinction.
  await page.goto(base + "/europe-in", { waitUntil: "networkidle" });
  // COUNTED AS LINKS AND QUERIES, NOT AS CARDS. This asserted `.card` and
  // went red when the index stopped being a card grid — which is the shape,
  // not the promise, and this repository has now made that mistake in five
  // separate assertions. The promise is that the index lists every motion
  // and prints the query that made each one, which is the whole argument of
  // the family: a list somebody curated by hand looks identical to one a
  // query produced, on the day it ships and never again.
  const motionRows = await page.locator(".motionrow").count();
  ok(motionRows >= 12, `the motion index lists ${motionRows} motions`);
  const motionQ = await page.locator(".motionq").allTextContents();
  ok(motionQ.length === motionRows,
     `${motionRows} motions listed and ${motionQ.length} queries printed`);
  ok(motionQ.every(t => t.trim().length > 20 && t.trim().endsWith(".")),
     "a motion on the index is listed without the query that made it");

  const motionLinks = await page.locator('a[href^="/europe-in/"]').evaluateAll(
    (as) => Array.from(new Set(as.map((a) => a.getAttribute("href")))));
  ok(motionLinks.length >= 12, "the index does not link every motion");

  for (const href of motionLinks) {
    const r = await page.request.get(base + href);
    ok(r.status() === 200, `${href} returned ${r.status()}`);
    const html = await r.text();
    // Every motion page must print the query that produced it. A landing
    // page that will not say what produced it is an assertion.
    //
    // THESE PINNED THE STRINGS OF A PANEL RATHER THAN THE PROMISE. The query
    // used to be a grey `.note` box with an h2 reading "The query that made
    // this page", sitting between the head and the map — the mechanism in
    // front of the answer — and it printed the match and shown counts that
    // the map caption printed again, on all twelve pages. Moving it turned
    // these red for the right reason and the wrong claim.
    //
    // The promise is: the page says what produced it, says it is a query and
    // not a list, says how many matched, and says each of those ONCE. The
    // last one is the half the old assertions could never have caught,
    // because the duplication was in the shape they were protecting.
    ok(/class="whyall"[^>]*>\s*<span>The query<\/span>/.test(html),
       `${href} does not state its query`);
    ok(/\d+ match, in \d+ countr/.test(html), `${href} does not say how many matched`);
    ok(/nothing here is hand-picked/i.test(html), `${href} does not say it is a query`);
    const said = (html.match(/matched the query/g) || []).length +
                 (html.match(/ match, in \d+ countr/g) || []).length;
    ok(said === 1, `${href} states its match count ${said} times, not once`);
    // And the query has to read as a sentence. Four of the twelve were
    // relative clauses with no subject — "The query lying above 63° north."
    // — which parsed under a heading and stopped parsing the moment the
    // query became one hoisted line.
    const q = (html.match(/<span>The query<\/span>\s*([^<]{4,120})/) || [])[1] || "";
    ok(/^\s*(Any|Every) destination /.test(q),
       `${href} query does not start with its subject: ${JSON.stringify(q.slice(0, 60))}`);
    // And it must have actually matched something.
    const n = (html.match(/class="row"/g) || []).length;
    ok(n >= 3, `${href} matched only ${n} destinations`);
  }

  // The queries must actually differ from one another. Two motions returning
  // the same list would mean the query is decorative.
  async function motionNames(href) {
    const html = await (await page.request.get(base + href)).text();
    return (html.match(/<h3>([^<]+)<\/h3>/g) || []).join("|");
  }
  const railMotion = await motionNames("/europe-in/by-rail");
  const islandMotion = await motionNames("/europe-in/islands");
  ok(railMotion !== islandMotion, "two motions returned the same destinations");

  // The latitude query is geographic, not editorial: nothing south of 63N.
  const nl = await (await page.request.get(base + "/europe-in/northern-lights")).text();
  ok(/above 63° north/.test(nl), "the northern-lights query is not stated as a latitude");
  for (const south of ["Lisbon", "Athens", "Rome", "Madrid", "Paris"]) {
    ok(!nl.includes(">" + south + "<"), `${south} appeared above 63° north`);
  }

  // Hidden villages must be genuinely hidden: no capitals.
  const hidden = await (await page.request.get(base + "/europe-in/hidden-villages")).text();
  for (const capital of ["Paris", "London", "Berlin", "Madrid", "Vienna", "Rome"]) {
    ok(!hidden.includes(">" + capital + "<"), `${capital} is in Europe's hidden villages`);
  }

  // ── search ─────────────────────────────────────────────────────────
  await page.goto(base + "/search", { waitUntil: "networkidle" });
  await page.fill("#q", "bergen");
  // WAIT FOR THE RESULTS, NOT FOR A ROW. /search has a resting state now —
  // the index by kind, so the page opens on the thing it operates over
  // rather than on a box and 280 pixels of nothing — and that is built from
  // the same `row` primitive. `#results .row` matched it instantly and this
  // assertion read "Countries" as the top hit for "bergen". The results
  // announce their own count; that is what tells them apart from the state
  // they replace — and "an h2 is present" is not that, because the resting
  // state has one too, which is the point of it.
  // A LOCATOR, NOT waitForFunction: that one evaluates a string, and this
  // site's own Content-Security-Policy has no 'unsafe-eval', so the suite
  // died with the page's CSP error rather than a verdict.
  await page.locator("#results h2").filter({ hasText: /\d+ results?/ }).waitFor();
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

  // The specification puts the question on the homepage; it has to reach
  // the planner and run, or it is a decorative input.
  await page.goto(base + "/", { waitUntil: "networkidle" });
  await page.fill("#homeask", "10 days in September, mountains and local food");
  await page.click(".askhero button[type=submit]");
  await page.waitForSelector("#result .leg");
  ok(/plan/.test(page.url()), "the homepage question did not reach the planner");
  const homeRead = await page.locator("#result .note").first().textContent();
  ok(/10 days/.test(homeRead) && /September/.test(homeRead),
     `the homepage question was not read: ${homeRead.slice(0, 80)}`);

  // A homepage map filter must open the map with that layer already on.
  await page.goto(base + "/map?layer=mountains", { waitUntil: "networkidle" });
  ok(await page.isChecked('#layers input[value="mountains"]'),
     "?layer=mountains did not preselect the layer");
  const litCount = await page.locator("#dots .dot:not(.off)").count();
  const allCount = await page.locator("#dots .dot").count();
  ok(litCount > 0 && litCount < allCount, "the preselected layer did not filter anything");

  // Event categories must filter the month.
  //
  // THIS RAN ON /events AND THE ROWS MOVED. The index printed all 197
  // fixtures across twelve bands and fifteen screens, so the filter was a
  // control on a page nobody could scroll; the rows live on the month pages
  // now and the control went with them. The promise is unchanged — checking
  // a category narrows the list and does not empty it — and it is asserted
  // where a reader can actually use it.
  await page.goto(base + "/events/jun", { waitUntil: "networkidle" });
  const beforeEvents = await page.locator(".row.event:not([hidden])").count();
  await page.check('#eventkinds input[value="food"]');
  await page.waitForTimeout(150);
  const afterEvents = await page.locator(".row.event:not([hidden])").count();
  ok(afterEvents > 0 && afterEvents < beforeEvents,
     `event filtering lit ${afterEvents} of ${beforeEvents}`);

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
  //
  // THIS ASSERTED THE DISCLOSURE AND THE DISCLOSURE WAS THE DEFECT. The
  // controls used to live in a closed <details> under the drawing, and this
  // check opened it with `.maptools > summary` before touching anything —
  // which made the shape of the page a precondition of the assertion rather
  // than the assertion. The controls are a band of their own now, because
  // they ARE the instrument and a reader met a map they could only click.
  //
  // The reason the <details> existed is still true and is still honoured:
  // the first layout put the filters and two selects BETWEEN the headline
  // and the drawing, so a 1280x1000 laptop opened the page called "the map"
  // with no map on it. The controls are below the drawing, not above it, and
  // that is what the added assertion pins — the map is in the first screen
  // and the controls are reachable without opening anything.
  await page.goto(base + "/map", { waitUntil: "networkidle" });
  const dots = await page.locator("#dots .dot").count();
  ok(dots > 200, `map drew only ${dots} cities`);
  const mapTop = await page.locator("#europemap").evaluate(
    (e) => e.getBoundingClientRect().top + window.scrollY);
  const ctlTop = await page.locator("#layers").evaluate(
    (e) => e.getBoundingClientRect().top + window.scrollY);
  ok(mapTop < 900,
     `the drawing starts at y=${Math.round(mapTop)} on the page called "the map"`);
  ok(ctlTop > mapTop,
     `the controls start at y=${Math.round(ctlTop)} and the drawing at ` +
     `y=${Math.round(mapTop)} — the filters are above the map again`);
  ok(await page.locator('#layers input[value="winter"]').isVisible(),
     "an interest filter is not reachable without opening a disclosure");

  /* A KEY'S SWATCH MUST PAINT WHAT THE DRAWING PAINTS, AND ONE OF THE THREE
   * DID NOT. `.legend .sw.dest` is `var(--sea)` and the map's dots are
   * `var(--sea)` too — the same token and two different colours, because a
   * `var()` resolves where the DECLARATION lives: inside the graphite map
   * figure `--sea` is cobalt-air and inside a light band it is pine-deep. So
   * the key said a destination is pine while the drawing drew it cobalt:
   * rgb(7,48,43) against a painted rgb(64,118,231). **A key that names the
   * wrong colour is worse than no key**, and it was invisible for as long as
   * the key sat inside a closed <details> — nothing counts a swatch.
   *
   * This reads the computed paint off BOTH ends, which is the only honest
   * instrument: the declaration is the same string in both places, so
   * comparing declarations would agree with itself. The fix was to put the
   * key in the same band as its drawing rather than to hard-code a hex. */
  for (const [sw, drawn, what] of [
    [".legend .sw.land", "#europemap .countries path", "a country in the Atlas"],
    [".legend .sw.ctx", "#europemap #context path", "land outside the Atlas"],
    [".legend .sw.dest", "#europemap .dot circle", "a destination"],
  ]) {
    const a = await page.locator(sw).evaluate(
      (e) => getComputedStyle(e).backgroundColor);
    const b2 = await page.locator(drawn).first().evaluate(
      (e) => getComputedStyle(e).fill);
    ok(a === b2,
       `the key says ${what} is ${a} and the map draws it ${b2}. A key that ` +
       `names the wrong colour is worse than no key`);
  }

  await page.check('#layers input[value="winter"]');
  await page.waitForTimeout(120);
  const lit = await page.locator("#dots .dot:not(.off)").count();
  ok(lit > 0 && lit < dots, `winter layer lit ${lit} of ${dots} — filtering is not working`);

  // ── real geography ─────────────────────────────────────────────────
  //
  // The map used to be 313 dots on an empty rectangle and its own note said
  // there were no coastlines because we had no licence to draw any. These
  // assertions are what stops that regressing quietly: a map that loses its
  // land still renders, still passes every HTML check, and looks like a
  // styling accident rather than a missing dataset.
  await page.goto(base + "/map", { waitUntil: "networkidle" });
  const shapes = await page.locator("#countries .cshape").count();
  const pts = await page.locator("#nogeo .cpoint").count();
  ok(shapes > 40, `the map drew only ${shapes} country shapes`);
  ok(shapes + pts === 50, `${shapes} shapes + ${pts} points is not the 50 countries in the Atlas`);
  const noHref = await page.locator("#countries .cshape:not([href])").count();
  ok(noHref === 0, `${noHref} country shapes have no href — the drill-down must be links first`);

  // Nothing is fetched from anywhere but this origin. The whole point of the
  // architecture is that there is no map bill, and a stray absolute URL is
  // how that stops being true.
  const external = [];
  page.on("request", (r) => {
    if (!r.url().startsWith(base)) external.push(r.url());
  });
  await page.goto(base + "/map", { waitUntil: "networkidle" });

  // Clicking a country: panel, regions, destinations, a way in, and the
  // selection in the URL so a drilled-in map can be sent to somebody.
  await page.evaluate(() =>
    document.getElementById("cshape-norway").dispatchEvent(
      new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 })));
  await page.waitForSelector("#countrypanel:not([hidden])");
  const cpanel = await page.locator("#countrypanel").textContent();
  ok(/Norway/.test(cpanel), "the country panel does not name the country");
  const regionLinks = await page.locator("#countrypanel .regionlist .rlink").count();
  ok(regionLinks >= 5, `Norway shows ${regionLinks} regions in the panel`);
  ok(await page.locator("#countrypanel .btn").getAttribute("href") === "/europe/norway",
     "the panel's way in does not point at the country page");
  ok(/c=norway/.test(await page.evaluate(() => location.search)),
     "the selection is not in the URL, so a drilled-in map cannot be shared");

  // The region and destination rows are real pages, not decoration. This is
  // the §58 rule: no dead buttons.
  const rHref = await page.locator("#countrypanel .rlink").first().getAttribute("href");
  const dHref = await page.locator("#countrypanel .regionlist a").nth(1).getAttribute("href");
  for (const href of [rHref, dHref]) {
    const res = await page.request.get(base + href);
    ok(res.status() === 200, `the panel links to ${href}, which is ${res.status()}`);
  }

  // Selecting a country zooms to it and loads that country's own geometry.
  const vb = await page.locator("#europemap").getAttribute("viewBox");
  ok(Number(vb.split(/\s+/)[2]) < 1000, `selecting a country did not zoom the map (${vb})`);
  await page.waitForFunction(() => document.querySelectorAll("#detail .cshape").length > 0,
                             null, { timeout: 8000 });
  const detailed = await page.locator("#detail .cshape").count();
  ok(detailed > 0, "the country's own level of detail never loaded");
  ok(external.length === 0,
     `the map fetched ${external.length} thing(s) off this origin: ${external.slice(0, 2)}`);

  // Back to the whole continent, and the selection leaves the URL with it.
  await page.locator("#zoomreset").click();
  ok(await page.locator("#countrypanel").isHidden(), "the panel will not close");
  // Compared as numbers, not as a string: applyView writes the viewBox with
  // toFixed(1), so the reset value is "0.0 0.0 1000.0 780.0" and a string
  // comparison against the markup's "0 0 1000 780" fails on formatting while
  // reporting a behavioural fault.
  const back = (await page.locator("#europemap").getAttribute("viewBox")).split(/\s+/).map(Number);
  ok(back[0] === 0 && back[1] === 0 && back[2] === 1000 && back[3] === 780,
     `'Whole of Europe' left the view at ${back.join(" ")}`);

  // Map popups, the places layer and distance from a chosen origin.
  await page.goto(base + "/map", { waitUntil: "networkidle" });
  await page.selectOption("#mapfrom", { index: 5 });
  await page.locator("#dots .dot").nth(40).click();
  await page.waitForSelector("#mappopup:not([hidden])");
  const popup = await page.locator("#mappopup").textContent();
  ok(/km from/.test(popup), "the popup does not give a distance from the chosen origin");
  ok(/Open /.test(popup), "the popup has no way into the page");
  await page.locator(".mappopup-close").click();
  ok(await page.locator("#mappopup").isHidden(), "the popup will not close");

  // A LAYER ASSERTION THAT SAYS ONLY "IT IS VISIBLE" IS NOT A MEASUREMENT.
  // These two checks were red on the CI runner and green here for eighty-nine
  // runs, and the message carried no number, so every diagnosis of them was a
  // theory about a browser nobody could look at. Adding the state to the
  // message answered it in one run:
  //
  //   computed-display=none  box=479x727  children=255
  //
  // THE LAYER WAS HIDDEN IN BOTH BROWSERS AND THE INSTRUMENT WAS WRONG.
  // Playwright's isHidden() is "the element has an empty bounding box", and
  // Chromium 131 returns the children's geometry for an SVG <g> whose
  // computed display is none, where 141 returns a zero rect. So the suite
  // asked a question about a BOX and reported it as a question about
  // VISIBILITY, and the two browsers disagreed about the box while agreeing
  // exactly about the drawing. Nothing was ever wrong with the map.
  //
  // Same shape as the map labels sized in viewBox units and read as pixels:
  // the number was real and it was not the number the promise is about. The
  // promise here is that the layer is not DRAWN, so the assertion reads the
  // computed display, which is what decides that, and keeps the rest of the
  // state in the message so the next disagreement is one run to diagnose
  // rather than three.
  const layerDrawn = (sel) => page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return false;
    const cs = getComputedStyle(el);
    return cs.display !== "none" && cs.visibility !== "hidden";
  }, sel);

  const layerState = (sel) => page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return "absent";
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return [
      `hidden=${el.hasAttribute("hidden")}`,
      `display-attr=${el.getAttribute("display")}`,
      `computed-display=${cs.display}`,
      `visibility=${cs.visibility}`,
      `box=${Math.round(r.width)}x${Math.round(r.height)}`,
      `children=${el.children.length}`,
    ].join(" ");
  }, sel);

  ok(!(await layerDrawn("#places")),
     `the places layer starts visible: ${await layerState("#places")}`);
  await page.check('#geolayers input[value="places"]');
  ok(await layerDrawn("#places"),
     `the places layer will not turn on: ${await layerState("#places")}`);
  await page.check('#geolayers input[value="regions"]');
  await page.waitForTimeout(120);
  const rlabels = await page.locator("#regions .rlabel").count();
  ok(rlabels > 10, `the regions layer drew ${rlabels} groupings`);
  await page.uncheck('#geolayers input[value="cities"]');
  ok(!(await layerDrawn("#dots")),
     `the destinations layer will not turn off: ${await layerState("#dots")}`);

  // ── the country map ────────────────────────────────────────────────
  //
  // The middle rung of Europe -> country -> region -> destination, which did
  // not exist before there was geometry: a country page could list its
  // regions and could not show you where any of them were.
  await page.goto(base + "/europe/italy", { waitUntil: "networkidle" });
  ok(await page.locator(".countrymap svg").count() === 1, "Italy has no country map");
  ok(await page.locator(".countrymap .countries path.here").count() > 0,
     "the country map does not pick out the country it is of");
  const cmDots = await page.locator(".countrymap .minidot").count();
  ok(cmDots > 15, `the Italy map drew ${cmDots} destinations`);
  const cmCap = await page.locator(".countrymap figcaption").textContent();
  ok(/Natural Earth/.test(cmCap), "the country map does not say where its coastline came from");
  ok(/groupings, not boundaries/.test(cmCap),
     "the country map does not say that its regions are not boundaries");


  // ── saved places ───────────────────────────────────────────────────
  await page.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
  // A destination carries the save action twice: the rail, and the sticky bar
  // a phone shows. Pressing one must relabel both — the first version
  // relabelled only the button that was clicked, so the other went on
  // offering to save something already saved. (The phone block below clicks
  // the other one; this is the desktop half of the same assertion.)
  // Scoped to the destination's own save action. It used to be the only
  // [data-save] on the page that was not the sticky bar; §2.16 added one per
  // experience, and the bare selector started matching seventeen things.
  const cityBtn = '[data-save^="city:"]:not([data-short])';
  await page.click(cityBtn);
  ok((await page.locator(cityBtn).textContent()).includes("✓"),
     "save button did not confirm");
  ok((await page.locator("[data-save][data-short]").textContent()).includes("✓"),
     "saving from the rail did not update the sticky bar's button");
  ok(await page.locator('[data-save^="city:"][aria-pressed="true"]').count() === 2,
     "the save buttons did not report their pressed state to assistive tech");
  await page.goto(base + "/my-europe", { waitUntil: "networkidle" });
  ok((await page.locator("#mine").textContent()).includes("Bergen"), "saved place did not appear in My Europe");

  // Collections — the specification's bucket lists.
  await page.fill("#collname", "My European Summer");
  await page.click("#newcoll button[type=submit]");
  await page.waitForTimeout(120);
  ok(/My European Summer/.test(await page.locator("#mine").textContent()),
     "a new collection did not appear");
  await page.selectOption("[data-move]", "My European Summer");
  await page.waitForTimeout(120);
  const mineText = await page.locator("#mine").textContent();
  ok(mineText.indexOf("My European Summer") < mineText.indexOf("Everything else"),
     "a saved item did not move into its collection");
  await page.reload({ waitUntil: "networkidle" });
  ok(/My European Summer/.test(await page.locator("#mine").textContent()),
     "the collection did not survive a reload");

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
    /* `domcontentloaded` MEASURED A PAGE THAT WAS NOT LAID OUT YET, and it
     * failed on one region page in twenty-five with a 2,058-pixel overflow
     * that is 0 when the same page at the same width is measured after
     * load. A check that jitters teaches whoever hits it to re-run until
     * green, which is how a real overflow gets through. */
    await phone.goto(base + url, { waitUntil: "load" });
    const over = await phone.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    ok(over <= 1, `${url} overflows by ${over}px at 390 CSS pixels`);
    const h1 = await phone.locator("h1").count();
    ok(h1 === 1, `${url} has ${h1} h1 elements`);
  }

  // ── the thumb bar and the sticky action, on a phone ────────────────
  // Both are display:none above 44rem, so they can only be tested here.
  await phone.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
  const bottomLinks = phone.locator(".bottomnav a");
  ok(await bottomLinks.count() === 5, "the thumb bar does not carry five items");
  for (let i = 0; i < 5; i++) {
    const box = await bottomLinks.nth(i).boundingBox();
    // WCAG 2.2 AA sets a 24x24 floor for a target; 44 is the comfortable
    // version, and a bar meant for a thumb has no excuse for less.
    ok(box && box.height >= 44 && box.width >= 44,
       `thumb bar item ${i} is ${box && Math.round(box.width)}x${box && Math.round(box.height)}, under 44px`);
  }
  ok(await phone.locator('.bottomnav a[aria-current="page"]').count() === 1,
     "the thumb bar does not say where you are");
  ok(/Explore/.test(await phone.locator('.bottomnav a[aria-current="page"]').textContent()),
     "a destination page did not light Explore in the thumb bar");

  // "Add to my journey", never "Book now". There is nothing to book.
  const cta = phone.locator(".stickycta");
  ok(await cta.isVisible(), "the sticky action is not shown on a destination page");
  const ctaText = await cta.textContent();
  ok(/Add to my journey/.test(ctaText), "the sticky action does not offer the journey");
  ok(!/Book/i.test(ctaText), "a booking button appeared on a site with nothing to book");
  const ctaBox = await cta.boundingBox();
  const navBox = await phone.locator(".bottomnav").boundingBox();
  ok(ctaBox.y + ctaBox.height <= navBox.y + 1,
     "the sticky action overlaps the thumb bar");

  // Saving from the sticky bar must relabel the button in the rail too.
  await phone.click("[data-save][data-short]");
  ok((await phone.locator("[data-save][data-short]").textContent()).includes("✓"),
     "the compact save button did not confirm");
  ok((await phone.locator('[data-save^="city:"]:not([data-short])').textContent()).includes("✓"),
     "saving from the sticky bar did not update the button in the rail");
  await phone.evaluate(() => localStorage.clear());

  // The bars must not cover the end of the page.
  await phone.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
  const covered = await phone.evaluate(() => {
    window.scrollTo(0, document.body.scrollHeight);
    const links = Array.from(document.querySelectorAll(".footer-nav a"));
    const last = links[links.length - 1].getBoundingClientRect();
    const bar = document.querySelector(".stickycta").getBoundingClientRect();
    return last.bottom > bar.top;
  });
  ok(!covered, "the sticky bars cover the last link on the page");

  // And they must not appear where they do not belong.
  await phone.goto(base + "/plan", { waitUntil: "networkidle" });
  ok(await phone.locator(".stickycta").count() === 0,
     "the destination action appeared on a page with no destination");
  ok(await phone.locator(".bottomnav").isVisible(), "the thumb bar is missing on /plan");

  // ── the destination page's own contents ────────────────────────────
  await phone.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
  const tabs = phone.locator(".sectionnav a");
  ok(await tabs.count() >= 3, "the section nav did not render");
  // A tab pointing at an anchor that is not on the page is worse than no tab.
  const anchors = await tabs.evaluateAll((as) => as.map((a) => a.getAttribute("href")));
  for (const a of anchors) {
    ok(await phone.locator(a).count() === 1, `section nav links to ${a}, which is not on the page`);
  }
  // It scrolls sideways rather than wrapping, so the page below it does not
  // move by a different amount on every destination.
  const wraps = await phone.evaluate(() => {
    const n = document.querySelector(".sectionnav");
    return n.scrollHeight > n.clientHeight + 4;
  });
  ok(!wraps, "the section nav wraps instead of scrolling");

  // ── AN ANCHOR MUST LAND BELOW THE STICKY MASTHEAD, NOT BEHIND IT ───
  // Every in-page anchor on this site scrolled its target to y=0, which is
  // where the sticky masthead is. On a wide screen the section's own top
  // margin absorbed it; ON A PHONE the bar is two rows and 89 pixels and the
  // margin is 80, so the heading landed nine pixels BEHIND the bar, on the
  // jump nav all 319 destination pages carry. Proved red at 390 by deleting
  // the scroll-margin rule and re-measuring.
  //
  // This asserts the PROMISE and not the number. `--mast` is a ceiling on
  // the bar and a floor on what has to clear it, so a masthead that grows a
  // row fails here rather than quietly eating a heading again — and it is
  // measured by actually navigating, because a rule stating an offset is not
  // an offset the browser applied.
  for (const [pg, w] of [[page, 1280], [phone, 390]]) {
    await pg.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
    const navs = await pg.locator(".sectionnav a").evaluateAll(
      (as) => as.map((a) => a.getAttribute("href")));
    ok(navs.length >= 3, `no jump nav to test at ${w}`);
    for (const href of navs) {
      await pg.evaluate((h) => document.querySelector(`a[href="${h}"]`).click(), href);
      // MEASURE AFTER THE SCROLL, NOT DURING IT. The first version read the
      // rectangle in the same frame as the click, which is a measurement of
      // where the page was about to stop being.
      await pg.waitForTimeout(220);
      const r = await pg.evaluate((h) => {
        const t = document.querySelector(h).getBoundingClientRect();
        const m = document.querySelector(".masthead").getBoundingClientRect();
        return { top: t.top, bar: m.bottom };
      }, href);
      ok(r.top >= r.bar - 1,
         `at ${w}, jumping to ${href} put the heading at ${Math.round(r.top)} ` +
         `with the masthead reaching ${Math.round(r.bar)} — it lands behind the bar`);
    }
  }

  /* ── AND THE CEILING HAS TO BE ONE, WHICH NOTHING HAD EVER ASKED ──────
   * `--mast`'s own comment says it is "a ceiling on the bar and a floor on
   * everything that has to clear it", and no check asserted the first half.
   * The bar then grew — `.masthead-in` went from --s3 to --s5 of block
   * padding, 58 to 82 at desk width, with its own comment recording the
   * move — and the token stayed at 60. Swept at twenty-seven widths:
   *
   *      >= 961   bar 82.0   --mast 60   OVER by 22.0
   *   704..960    bar 90.4   --mast 60   OVER by 30.4
   *      < 704    bar 90.4   --mast 92   ok
   *
   * and the 44rem breakpoint was wrong as well as the value, because the
   * bar becomes TWO ROWS at 60rem. Nothing went red, because the three
   * rules that read the token are offsets a section's own top margin was
   * absorbing: a latent defect, of exactly the kind this token was invented
   * to stop, in the token invented to stop it.
   *
   * The sweep is the check. It is cheap — one page, a `setViewportSize` per
   * width — and it is the only thing that can catch a bar that grows a row
   * at a width nobody photographs. 961 and 960 are both in it on purpose:
   * the two-row transition is between them, and a defect that lives in one
   * pixel of width is what the 834 finding is about. */
  {
    const mp = await browser.newPage({ viewport: { width: 1280, height: 844 } });
    await mp.goto(base + "/europe/austria/", { waitUntil: "load" });
    const over = [];
    for (const W of [2560, 1920, 1440, 1280, 1152, 1024, 992, 961, 960, 900,
                     834, 760, 705, 704, 600, 480, 390, 320]) {
      await mp.setViewportSize({ width: W, height: 844 });
      await mp.waitForTimeout(40);
      const r = await mp.evaluate(() => {
        const h = document.querySelector(".masthead").getBoundingClientRect().height;
        const t = parseFloat(getComputedStyle(document.documentElement)
                               .getPropertyValue("--mast")) * 16;
        return { h: +h.toFixed(1), t };
      });
      checked++;
      if (r.h > r.t + 0.5) over.push(`${W}: bar ${r.h} against --mast ${r.t}`);
    }
    checked++;
    ok(over.length === 0,
       `the masthead is taller than --mast at ${over.length} width(s) — ` +
       `${over.slice(0, 4).join("; ")}. Every offset that clears the bar ` +
       `reads that token, so a bar taller than it puts a heading, a sticky ` +
       `rail and an essay margin behind the bar by the difference`);
    await mp.close();
  }

  // ── A <br> INSIDE A FLEX CONTAINER DOES NOTHING ────────────────────
  // Adding `display: flex` to `.rowmeta` for the state marks turned every
  // child and every text run into a flex ITEM, and a <br> between two items
  // has no effect — so `2026-09-05<br><span>5 min</span>` on the stories
  // index rendered as "2026-09-055 min", a date and a reading time run
  // together, on every row of that page. It is invisible from the source:
  // the markup asks for a break and gets one everywhere else.
  //
  // The generic form of the fault, over the families that use a <br>.
  for (const url of ["/stories", "/how-it-works", "/journeys", "/themes"]) {
    const bp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await bp.goto(base + url, { waitUntil: "networkidle" });
    const bad = await bp.evaluate(() =>
      Array.from(document.querySelectorAll("br"))
        .map((b) => b.parentElement)
        .filter((p) => /flex|grid/.test(getComputedStyle(p).display))
        .map((p) => p.className + " {" + getComputedStyle(p).display + "}")
        .filter((v, i, a) => a.indexOf(v) === i));
    ok(bad.length === 0,
       `${url}: a <br> sits inside a flex or grid container, where it does ` +
       `nothing — ${bad.join(", ")}`);
    // And the promise the fault broke, asserted directly on the one family
    // that ships a two-line meta.
    if (url === "/stories") {
      const t = await bp.locator(".storyrow .rowmeta").first().innerText();
      ok(/\n/.test(t),
         `the stories index runs the date and the reading time together: ${JSON.stringify(t)}`);
    }
    await bp.close();
  }

  // ── AN INSTRUMENT AT REST REPORTS NO WORK IN PROGRESS ──────────────
  // /plan opened on a panel headed "Building your journey" with
  // "Understanding what you asked for" marked as happening now, and it
  // stayed there for as long as the page was open. Nothing was being built:
  // the boot borrowed the build's five-step progress report to say the index
  // was loading, ticked the first step when it arrived, and never took it
  // down. A reader who had asked for nothing was shown a machine working on
  // their behalf, permanently stuck on step two.
  //
  // The promise is the one thing a live region owes: what it says is true at
  // the moment it says it. Measured across every live region visible at rest
  // on all 44 families, /plan was the only one claiming work in progress —
  // the other six say what they actually are ("Nothing saved yet", "Choose
  // what you are travelling for"). So this reads every ARIA live region on
  // every application page after load and nothing else, and fails on a
  // progressive verb of work.
  //
  // It counts the regions it read, because a page that has stopped
  // publishing a live region at all would pass this silently, and an empty
  // scan that reports clean is the failure this suite already records twice.
  {
    const REST = ["/plan", "/discover", "/search", "/my-europe", "/map"];
    const WORKING = /\b(building|loading|scoring|estimating|working|calculating|please wait|one moment)\b/i;
    let regions = 0;
    for (const u of REST) {
      const rp = await page.goto(base + u, { waitUntil: "load" });
      if (!rp || rp.status() !== 200) { ok(false, `${u} did not load`); continue; }
      // networkidle would hide exactly the defect this is about: the index
      // fetch is what the panel was reporting, and the panel survived it.
      await page.waitForTimeout(1500);
      const found = await page.evaluate(() =>
        [...document.querySelectorAll("[role=status], [aria-live], .staged")]
          .filter((e) => e.getClientRects().length)
          .map((e) => e.textContent.replace(/\s+/g, " ").trim()));
      regions += found.length;
      for (const t of found) {
        ok(!WORKING.test(t),
           `${u} at rest: a live region reports work in progress with nothing ` +
           `asked for — "${t.slice(0, 110)}"`);
      }
    }
    ok(regions >= 4,
       `the at-rest scan found only ${regions} live regions across ` +
       `${REST.length} application pages — it has stopped finding them`);
  }

  // ── THE PLANNER DRAWS THE ROUTE IT BUILT ───────────────────────────
  // The most complex thing on this site had no geography in its output at
  // all: a summary table, a budget verdict and a column of stops, on a
  // product whose every other family draws where its places are.
  //
  // Nothing is projected in the browser — every destination arrives with the
  // x and y the build put it at, so the projection stays decided in one
  // place. The FRAME is a second implementation, of pages.glyph_view(), and
  // this asserts the two agree exactly on the frames the site already draws.
  // Framing is not projection and cannot put a place in the wrong country,
  // but it can still drift.
  {
    await page.goto(base + "/plan", { waitUntil: "networkidle" });
    await page.click('#planner button[type="submit"]');
    await page.waitForSelector("#result .leg");
    const fig = page.locator(".planmap svg");
    ok(await fig.count() === 1, "the planner draws no map of the route it built");
    const stops = await page.locator("#result .leg").count();
    ok(await page.locator(".planmap .constel-lit circle").count() === stops,
       "the planner's map does not draw one mark per stop");
    ok(await page.locator(".planmap polyline").count() === 2,
       "the planner's route has no casing — a single stroke cannot clear 3:1 " +
       "on both the land and the water");
    // A dot with no radius is not a dot: `.constel-lit circle` sets only a
    // fill and every family sets its own r.
    const r = await page.locator(".planmap .constel-lit circle").first()
      .evaluate((c) => c.getBoundingClientRect().width);
    ok(r > 4, `the planner's stop marks render ${r.toFixed(1)}px wide`);
    // The two framings, on the real journeys the build already framed.
    const cases = await page.evaluate(() => window.__europedoorGlyphView
      ? [[[100, 100], [200, 300]], [[420, 480], [470, 520], [500, 560]],
         [[10, 10], [990, 770]], [[500, 400]]].map(
          (pts) => pts.length + ":" + window.__europedoorGlyphView(pts))
      : null);
    ok(cases !== null, "planner.js exposes no framing function to compare");
    const want = JSON.parse(await page.evaluate(() =>
      document.getElementById("europedoor-glyphview-cases")
        ? document.getElementById("europedoor-glyphview-cases").textContent
        : "null"));
    ok(want !== null, "/plan publishes no framing cases to check the browser against");
    if (want) {
      ok(JSON.stringify(cases) === JSON.stringify(want),
         `the browser frames a route differently from the build:\n  browser ` +
         `${JSON.stringify(cases)}\n  build   ${JSON.stringify(want)}`);
    }
  }

  // ── MY EUROPE WITH SOMETHING IN IT ─────────────────────────────────
  // Every check and every screenshot of /my-europe has looked at the empty
  // state, because that is what a fresh browser gets. The POPULATED state is
  // what a returning reader always gets, and it had two faults nobody could
  // have seen from the other one: the portable list rendered at the browser's
  // default twenty columns — 182 by 66 pixels holding the whole saved list
  // as JSON, on the control whose purpose is to be copied from — and a
  // collection heading sat exactly on the bottom edge of the panel above it.
  for (const w of [1280, 390]) {
    const mp = await browser.newPage({ viewport: { width: w, height: 900 } });
    await mp.goto(base + "/my-europe", { waitUntil: "networkidle" });
    await mp.evaluate(() => {
      localStorage.setItem("europedoor.saved.v1", JSON.stringify([
        { id: "city:norway/fjord-norway/bergen", kind: "City", label: "Bergen",
          url: "/europe/norway/fjord-norway/bergen" },
        { id: "city:austria/vienna-and-the-east/vienna", kind: "City",
          label: "Vienna", url: "/europe/austria/vienna-and-the-east/vienna" },
      ]));
    });
    await mp.reload({ waitUntil: "networkidle" });
    await mp.waitForSelector("#mine .row, #mine h3");
    const r = await mp.evaluate(() => {
      const ta = document.querySelector("#portable");
      const panel = document.querySelector("#mine .form");
      const h = [...document.querySelectorAll("#mine h3")]
        .find((x) => /Everything else/.test(x.textContent));
      return {
        over: document.documentElement.scrollWidth
              - document.documentElement.clientWidth,
        col: document.querySelector("main").getBoundingClientRect().width,
        ta: ta ? ta.getBoundingClientRect().width : 0,
        gap: (panel && h)
          ? Math.round(h.getBoundingClientRect().top
                       - panel.getBoundingClientRect().bottom)
          : null,
      };
    });
    ok(r.over <= 1, `a populated /my-europe overflows by ${r.over}px at ${w}`);
    ok(r.ta > r.col * 0.6,
       `at ${w} the portable list is ${Math.round(r.ta)}px in a ` +
       `${Math.round(r.col)}px column — it exists to be copied from`);
    ok(r.gap === null || r.gap >= 8,
       `at ${w} a collection heading sits ${r.gap}px from the panel above it`);
    await mp.close();
  }

  // ── THE INTERFACE THE BROWSER PAINTS FOR YOU ───────────────────────
  // Selection and the form controls' accent were Chromium's defaults on
  // every page: dragging across a paragraph in the graphite world gave a
  // pale platform highlight with the page's own light text inside it, and
  // the planner's seventeen interest checkboxes rendered in Chrome's blue,
  // a second slightly different blue beside the one band of signature
  // colour this site has.
  //
  // Read as RESOLVED values in both worlds and both preferences, because
  // `accent-color: auto` is what it looked like before and is a legal
  // computed value.
  for (const [url, w] of [["/", "discover"], ["/plan", "intelligence"]]) {
    for (const scheme of ["light", "dark"]) {
      const cp = await browser.newPage({ viewport: { width: 1280, height: 900 },
                                         colorScheme: scheme });
      await cp.goto(base + url, { waitUntil: "networkidle" });
      const r = await cp.evaluate(() => {
        const num = (v) => (v.match(/\d+/g) || []).map(Number).slice(0, 3);
        const lin = (v) => { const x = v / 255;
          return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
        const rel = (c) => 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
        // THE BODY, NOT THE ROOT. `accent-color` moved off `:root` because a
        // var() resolves where the DECLARATION lives and the world tokens sit
        // on `body[data-world]`, so the root resolved the light world's value
        // and inherited that one number into the dark one. This check read
        // the root and went red on the fix — pinning the element rather than
        // the promise. What a reader gets is the value on the element their
        // checkbox is inside.
        const cs = getComputedStyle(document.body);
        const sel = getComputedStyle(document.body, "::selection");
        const a = rel(num(sel.color)), b = rel(num(sel.backgroundColor));
        const [hi, lo] = [a, b].sort((x, y) => y - x);
        return { accent: cs.accentColor, ratio: (hi + 0.05) / (lo + 0.05),
                 bg: sel.backgroundColor, fg: sel.color };
      });
      ok(r.accent !== "auto",
         `${url} in ${scheme}: accent-color is auto, so the browser picks the ` +
         `colour of every checkbox on the page`);
      ok(r.ratio >= 4.5,
         `${url} in ${scheme}: selected text measures ${r.ratio.toFixed(2)}:1 ` +
         `against its own highlight (${r.fg} on ${r.bg})`);
      await cp.close();
    }
  }

  // ── NO GRADIENT STOP FALLS BACK TO BLACK ───────────────────────────
  // The hero's shadow is described in three places as "two rectangles of
  // graphite", and every stop of both gradients resolved to #000 for the
  // life of the drawn hero. The stops live in <defs> and the rule that
  // coloured them selected `.herodusk stop` — the group only REFERENCES the
  // gradients, so the selector matched nothing and the SVG default for
  // stop-color, which is black, applied instead. Measured (0, 0, 0) against
  // the (16, 18, 20) of the ground beside it.
  //
  // The dead-rule scan cannot see this: it finds rules that MATCH elements
  // and change none of them, and a rule matching no element at all is a
  // different fault. Reading the RESOLVED value is the only honest
  // instrument, and this palette contains no black at all.
  //
  // AND THE LIST GREW BECAUSE THE SAME MISTAKE WAS MADE TWICE MORE. The
  // picture plates' `datacut()` emitted its defs BESIDE the group rather than
  // inside it, so `.datacut stop` matched none of them; and `cut_fade()` had
  // exactly the same shape and stayed green only because /map colours its
  // stops by ID. The moment a class-scoped caller arrived — the 21 index
  // openings — the southern ramp came out as a black wash across North
  // Africa. Every family that draws a gradient is in this list now.
  for (const url of ["/", "/map", "/europe/norway/fjord-norway/bergen",
                     "/interests/mountains", "/journeys", "/countries",
                     "/stories", "/experiences", "/404.html"]) {
    const sp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await sp.goto(base + url, { waitUntil: "networkidle" });
    const stops = await sp.evaluate(() =>
      Array.from(document.querySelectorAll("svg stop")).map((s) => ({
        c: getComputedStyle(s).stopColor,
        id: s.parentElement.id || s.parentElement.tagName,
      })));
    const black = stops.filter((s) => /^rgba?\(0,\s*0,\s*0/.test(s.c));
    ok(black.length === 0,
       `${url}: ${black.length} of ${stops.length} gradient stops resolve to ` +
       `black — the SVG default, which this palette does not contain ` +
       `(${black.slice(0, 3).map((s) => s.id).join(", ")})`);
    await sp.close();
  }

  // ── THE BAR ABOVE THE PAGE ─────────────────────────────────────────
  // On a phone the address bar and the task-switcher card take
  // `theme-color`, and with none declared they took the platform default —
  // so a site whose one band of signature colour is a cobalt masthead
  // arrived on every Android phone with a white or black strip directly
  // above it, on all 1,033 pages.
  //
  // The value is stated in render.py and asserted here against the colour
  // Chromium ACTUALLY PAINTS on the masthead, in both worlds and both
  // preferences. Two places that must agree, and a check on the drift — the
  // same arrangement vercel.json has against render.HEADERS, for the same
  // reason. The bar is translucent, so this composites it over the ground
  // behind it rather than reading the declaration.
  for (const [url, world] of [["/about", "discover"], ["/map", "intelligence"]]) {
    for (const scheme of ["light", "dark"]) {
      const tp = await browser.newPage({ viewport: { width: 390, height: 800 },
                                         colorScheme: scheme });
      await tp.goto(base + url, { waitUntil: "networkidle" });
      const r = await tp.evaluate(() => {
        const num = (s) => (s.match(/[\d.]+/g) || []).map(Number);
        const m = getComputedStyle(document.querySelector(".masthead")).backgroundColor;
        const g = num(getComputedStyle(document.body).backgroundColor);
        let [r0, g0, b0, a] = num(m);
        // color() srgb notation reports 0-1 components; rgb() reports 0-255.
        if (r0 <= 1 && g0 <= 1 && b0 <= 1) { r0 *= 255; g0 *= 255; b0 *= 255; }
        if (a === undefined) a = 1;
        const mix = (f, b) => Math.round(f * a + b * (1 - a));
        const hex = (n) => n.toString(16).padStart(2, "0");
        const metas = Array.from(document.querySelectorAll('meta[name="theme-color"]'));
        const media = window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark" : "light";
        const pick = metas.find((t) => {
          const q = t.getAttribute("media");
          return !q || window.matchMedia(q).matches;
        });
        return {
          painted: "#" + hex(mix(r0, g[0])) + hex(mix(g0, g[1])) + hex(mix(b0, g[2])),
          declared: pick ? pick.getAttribute("content").toLowerCase() : null,
          n: metas.length, media,
        };
      });
      ok(r.declared !== null,
         `${url} declares no theme-color for the ${scheme} preference — the ` +
         `browser paints the bar above the masthead itself`);
      ok(r.declared === r.painted,
         `${url} in ${scheme}: theme-color is ${r.declared} and the masthead ` +
         `paints ${r.painted}`);
      // INTELLIGENCE is dark in both preferences on purpose, so it declares
      // ONE value: a media-switched pair there would paint a light bar above
      // a page that is never light.
      ok(world === "intelligence" ? r.n === 1 : r.n === 2,
         `${url} declares ${r.n} theme-colors for the ${world} world`);
      await tp.close();
    }
  }

  // ── WHAT A DESTINATION PAGE PRINTS ─────────────────────────────────
  // A destination page is the one thing on this site people print, and there
  // was no print rule anywhere in 4,700 lines of stylesheet: a cobalt
  // masthead across every sheet, the dark world's near-black ground through
  // the printer on any embedded map, and a thumb bar, a sticky action and
  // twenty footer links on paper where none of them can be pressed.
  //
  // Asserted in the print MEDIA rather than by reading the rules, because a
  // declaration is not what the browser resolved.
  {
    const pr = await browser.newPage({ viewport: { width: 1000, height: 1200 } });
    await pr.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
    await pr.emulateMedia({ media: "print" });
    const r = await pr.evaluate(() => {
      const disp = (s) => { const e = document.querySelector(s);
                            return e ? getComputedStyle(e).display : "absent"; };
      const b = getComputedStyle(document.body);
      const m = document.querySelector(".minimap svg, .minimap");
      return { mast: disp(".masthead"), nav: disp(".bottomnav"),
               cta: disp(".stickycta"), fnav: disp(".footer-nav"),
               legal: disp(".footer-legal"), map: disp(".minimap"),
               bg: b.backgroundColor, ink: b.color,
               right: m ? m.getBoundingClientRect().right : 0,
               w: document.documentElement.clientWidth };
    });
    for (const [k, what] of [["mast", "the masthead"], ["nav", "the thumb bar"],
                             ["cta", "the sticky action"], ["fnav", "the footer links"]])
      ok(r[k] === "none" || r[k] === "absent", `${what} is printed (${r[k]})`);
    // The legal line is the only thing on paper that says who published this.
    ok(r.legal !== "none", "the footer's legal line is not printed");
    ok(r.map !== "none", "the map is not printed — it is why the page is printed");
    ok(/255, 255, 255/.test(r.bg),
       `the printed ground is ${r.bg}, not paper — the dark world is a screen idea`);
    // AND THE MEASURE. The first print rule set `main { padding: 0 }`, so the
    // page printed flush to both edges and the destination map ran off the
    // right-hand side, arch and all.
    ok(r.right <= r.w - 1,
       `the printed map reaches ${Math.round(r.right)} of ${r.w} — it runs off the sheet`);
    await pr.close();
  }

  // ── the map, as a list ─────────────────────────────────────────────
  // A point map is a picture; role="img" says what it is of and nothing more.
  await phone.goto(base + "/map", { waitUntil: "networkidle" });
  const described = await phone.getAttribute(".europemap", "aria-describedby");
  ok(described === "maplist", "the map does not point at its text alternative");
  ok(await phone.locator("#maplist").count() === 1, "there is no text alternative to the map");
  // THIS COUNTED EVERY LINK IN THE LIST AND THE LIST GREW A SECOND JOB.
  // The alternative now also carries the fifty countries, because twenty of
  // them draw between 3.6 and 12 pixels wide on a phone and their shape was
  // the only way in — SC 2.5.8 allows a small target where the same function
  // is on the same page, and this list is that control. So a bare count of
  // `#maplist li a` went from 319 to 369 and failed for the right reason and
  // the wrong claim. The promise is that every place the map DRAWS is in the
  // list; it is now asserted against the destination links specifically, and
  // the countries are asserted as their own half.
  const listed = await phone.locator('#maplist li a[href^="/europe/"]')
    .evaluateAll((as) => as.filter((a) => a.getAttribute("href").split("/").length > 3).length);
  const dotted = await phone.locator("#dots .dot").count();
  ok(listed === dotted, `the map draws ${dotted} places and lists ${listed}`);
  const listedCountries = await phone.locator('#maplist li a[href^="/europe/"]')
    .evaluateAll((as) => as.filter((a) => a.getAttribute("href").split("/").length === 3).length);
  // Six countries have no polygon at 1:50m and are drawn as a ringed point
  // instead — Andorra, Liechtenstein, Malta, Monaco, San Marino and Vatican
  // City — so the drawn total is shapes plus points, not shapes alone. The
  // first version asserted against `.cshape` only and read 44 against 50,
  // which is the check being wrong rather than the page.
  const mapShapes = await phone.locator("#countries a.cshape").count();
  const mapPoints = await phone.locator("#nogeo a.cpoint").count();
  ok(listedCountries === mapShapes + mapPoints,
     `the map draws ${mapShapes + mapPoints} countries ` +
     `(${mapShapes} as shapes, ${mapPoints} as points) and the list names ` +
     `${listedCountries}`);

  // The map is allowed to scroll inside its own container, and must not
  // make the page scroll.
  await phone.goto(base + "/map", { waitUntil: "domcontentloaded" });
  const mapOver = await phone.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth
  );
  ok(mapOver <= 1, `/map overflows the page by ${mapOver}px instead of scrolling its own wrapper`);

  // ── the knowledge graph, and what the search does with it ──────────
  //
  // §2.14-§2.19. These run in a browser rather than as static checks
  // because the thing being tested is what a reader actually gets: a search
  // that parses a sentence, and an empty result that explains itself.
  const gp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const graph = await (await gp.request.get(base + "/api/graph.json")).json();
  ok(graph.edges.length > 3000, `the graph has only ${graph.edges.length} edges`);
  ok(Object.keys(graph.relationships).length >= 9,
     `only ${Object.keys(graph.relationships).length} relationship types`);
  for (const rel of ["part_of", "located_in", "near", "includes", "serves",
                     "gathers", "about", "happens_in", "available_at"]) {
    ok((graph.relationships[rel] || 0) > 0, `the graph has no ${rel} edges`);
  }
  ok(!JSON.stringify(graph.edges).includes('"weight"'),
     "the graph carries a weight; the only weight here is km, a real distance");
  await gp.close();

  // §2.19, run as the spec's own example. It found two real gaps the first
  // time it was run — "villages" silently dropped, and an empty result that
  // explained nothing — so it stays in the suite.
  const sp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await sp.goto(base + "/search", { waitUntil: "networkidle" });
  await sp.fill("#q", "romantic mountain villages near Milan");
  await sp.waitForTimeout(320);
  const und = (await sp.locator("#searchunderstood").textContent()).replace(/\s+/g, " ");
  ok(/near Milan/.test(und), `proximity was not read: ${und}`);
  ok(/villages/.test(und), `the kind of place was not read: ${und}`);
  ok(/mountains/.test(und), `the interests were not read: ${und}`);
  // A query that genuinely matches nothing: Czechia is not a low-cost
  // country, so every part of this parses and together they find none.
  await sp.fill("#q", "cheap food cities near Prague");
  await sp.waitForTimeout(320);
  const empty = (await sp.locator("#results").textContent()).replace(/\s+/g, " ");
  ok(/would leave \d+/.test(empty),
     "an empty result does not say which constraint emptied it");
  ok(/319 destinations/.test(empty),
     "the empty state's counts are typed rather than read from the index");
  // The kind filter has to actually filter, not just be read back.
  await sp.fill("#q", "villages");
  await sp.waitForTimeout(320);
  const villages = await sp.locator("#results h3").allTextContents();
  ok(villages.length > 1, "no destinations are recorded as villages");
  await sp.close();

  // §2.16: an experience is savable, which it was not before it had an id.
  const xp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await xp.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
  const saveExp = xp.locator('[data-save^="experience:"]').first();
  ok(await saveExp.count() > 0, "an experience cannot be saved");
  await saveExp.click();
  await xp.waitForTimeout(150);
  const stored = await xp.evaluate(() => localStorage.getItem("europedoor.saved.v1") || "");
  ok(stored.includes("experience:"), "saving an experience did not store it");
  await xp.close();

  // ── styling that cannot apply ──────────────────────────────────────
  //
  // TWICE IN THREE COMMITS A RULE LOST A SPECIFICITY FIGHT AND THE RESULT
  // RENDERED AS "THE THING IS SIMPLY NOT THERE". The touch targets painted
  // because `.minidot .hit` (0,2,0) lost to `.minimap.arched .minidot circle`
  // (0,3,1); the macro members were not filled because `.macromap .countries
  // path.here` and `.minimap.arched .countries path` are both (0,3,1) and the
  // second is further down the file. Neither is visible in any count.
  //
  // This finds them the only way that is not guesswork: delete each
  // declaration in turn and see whether anything on the page moves. A rule
  // that matches elements and changes none of them cannot apply.
  //
  // The first thing it found, on its first run: `.countrymap .countries
  // path.here` never won, so a country was drawn on its own page in exactly
  // the same grey as its neighbours — all fifty of them.
  //
  // A CEILING, not zero. Several base rules are legitimately superseded by
  // an `.arched` variant on every page that has one, and the honest fix for
  // those is a refactor rather than a deletion. Raising this number is
  // allowed; doing it without reading the list is not.
  {
    // 27 -> 18. Two things moved it. The media filter above stopped
    // reporting a rule that is asleep as one that is dead, and the base
    // fills that could never apply were deleted: every minimap this build
    // emits is arched — 824 of 824 — so `.minidot circle { fill }`,
    // `.minilabel { fill }` and `.countrymap .rlabel text { fill, stroke }`
    // had been superseded on every page since the map became an opening.
    // What survives is mostly REDUNDANT rather than unreachable: a `color`
    // that restates what the element already inherits. That is a different
    // and much smaller fault, and it is what the remaining number is.
    // 18 -> 21 WITH THE MIGRATION THAT MOVED THEM, and the list was read.
    // Every picture-family map became an atlas plate in one commit, so three
    // base rules that still apply on the INSTRUMENT maps — the country
    // reference map, /map, the macro maps — are superseded on every page
    // this scan visits: `.scalebar text`, `.minimap.arched .minidot.here
    // circle` and `.minimap.arched .minilabel.here`. They are not deletable,
    // because the instruments still need them, and they are not reachable
    // from here, because the scan looks at the pages a reader looks at. The
    // honest fix is to scope the base rules to `:not(.atlas)`, which is a
    // refactor of every minimap selector and is not this commit.
    //
    // Two rules WERE genuinely dead and were deleted rather than counted: a
    // lime route override, superseded because every route map is now an
    // atlas plate, and an atlas-scoped `.routeline` that restated the
    // cobalt and opacity the base rule already sets.
    // 21 -> 23 when the macro map became an editorial illustration. Its own
    // fill selector was superseded and was DELETED rather than counted; what
    // remains are `.minimap.arched .context path`'s fill and stroke, which
    // now only the country reference map and the /discover hero map can
    // reach, and neither shows a context country on the pages this scan
    // visits. Same category as the three above: needed by the instruments,
    // unreachable from here, and the honest fix is scoping the base rules
    // `:not(.atlas)` — a refactor of every minimap selector.
    // 23 -> 25, AND THE TWO ARE HOVER STATES THIS SCAN CANNOT TRIGGER.
    // `.storylead:hover h3` and `.storyleadwide:hover h3` colour a headline
    // when a reader points at it; the scan removes a declaration and asks
    // whether anything on the page moves, and nothing is hovered while it
    // looks. So they are reported as never winning and they win every time a
    // reader touches them. That is a limit of the instrument rather than
    // dead code — the same reason a @media block that does not currently
    // apply is asleep and not dead, which this scan already had to learn.
    //
    // The list was read before this number moved. Raising it is allowed;
    // raising it without reading is what the ceiling exists to stop.
    //
    // IT SITS EXACTLY AT 25 TODAY, over 256 rules and seventeen pages. Two
    // repairs to the instrument in one commit — sampling across the matches
    // instead of off the front, and measuring background-color at all — took
    // it from 28 back to the ceiling rather than through it. The margin is
    // zero, which is worth knowing before the next visual change: the next
    // redundant declaration fails here, and that is the check working.
    // 36, MEASURED AFTER THE REMOVALS RATHER THAN BEFORE THEM, AND THE LIST
    // WAS READ. Raising this number is allowed and raising it without
    // reading the list is not, which is the rule this ceiling carries.
    //
    // What moved it from 25 is the eight-family redesign. Three groups, and
    // none of them is a rule nobody meant:
    //
    //   the `ed-` heads state a colour their family rule then supersedes —
    //   `.ed-eyebrow`, `.ed-section-index`, `.ed-split-copy p`,
    //   `.ed-index dd`. Every page has a family, so the base never wins;
    //   the honest fix is for the base to state no colour at all, which
    //   means the institution and the arrival cases have to be written out
    //   first, and that is its own piece of work.
    //
    //   the `.arched` map variants supersede their own base on every page
    //   that has one — 824 of 824 — which this repository already records
    //   as *a ceiling, not zero*, with a refactor as the honest answer.
    //
    //   and `display` restated where an element already has it.
    //
    // THREE WERE REMOVED AND ONE WAS PUT BACK. `.band > .band-head`'s
    // `display: grid` looks like a duplicate of the declaration 7,300 lines
    // up and is not: that one is inside a media query, so below its
    // breakpoint this is the only one and removing it drops the band head to
    // block layout on every phone. The scan reports it dead because it scans
    // at a width where the media rule applies — *a media rule that does not
    // currently apply is asleep, not dead*, from the other end.
    //
    // AND THE SCAN WAS WRONG ONCE THIS SESSION, WHICH IS WHY NONE OF THESE
    // WAS DELETED ON ITS WORD ALONE. It called the inverting masthead's
    // `color: var(--bone)` redundant; it was the inheritance escape, and
    // deleting it measured 1.05:1 on three families. Every removal here was
    // measured at 390 and 1280 afterwards.
    // THE SCAN INHERITED ITS VIEWPORT AND ITS POINTER FROM WHATEVER RAN
    // BEFORE IT, AND BOTH CHANGE ITS ANSWER. It reported 37 against a
    // ceiling of 36 in a run where no stylesheet byte had moved; rerun
    // standalone on the identical build it said 34, and the three extra
    // were `.staged .now` and two `:hover, :focus-visible` rules. A `:hover`
    // selector matches NOTHING when the pointer is nowhere, so the scan
    // skipped those rules entirely — and matched them, and judged them, in a
    // suite where an earlier check had left the mouse on a card. **Where the
    // mouse was last put is not an input to a stylesheet audit.** So the
    // scan takes its own page, which no earlier check can have touched.
    //
    // AND IT SCANS BOTH WIDTHS, WHICH IS THIS CHECK'S OWN PRINCIPLE FINALLY
    // APPLIED. Its comment already says *a media rule that does not
    // currently apply is asleep, not dead*, and says it specifically about
    // `.band > .band-head`'s `display: grid` — which is a duplicate at 1280
    // and the only declaration below the breakpoint. The principle was
    // written down and the scan went on judging at one width, so that rule
    // and two others were counted dead while being load-bearing on every
    // phone. A rule alive at ANY width is alive, which is exactly the union
    // the scan already does across PAGES, extended to the axis the comment
    // was about. Measured: 34 dead at 1280, 34 at 390, and only 31 at both —
    // the three that leave at each width are the asleep ones, named.
    //
    // THE NUMBER MOVED 36 -> 35 AND EVERY PART OF THAT WAS READ. Two rules
    // LEFT because the scan stopped calling an asleep rule dead
    // (`.band > .band-head` and `.storylead, .storysm`, both `display`,
    // both the only declaration below the breakpoint). Three ENTERED
    // because scanning at 390 put the `@media (max-width: 44rem)` block in
    // this scan's reach for the first time. Two more ENTERED with the theme
    // page and were then REMOVED, because they were real: `display: block`
    // on the photograph inside an opening, restating what a grid item
    // already computes — which is the third and fourth time a dead
    // `display: block` has been found on a photograph container here, each
    // time in the first run where a photograph was actually rendered.
    // AND A CEILING IS THE WRONG INSTRUMENT, BECAUSE THE NUMBER MOVES.
    // With the pointer and the viewport both fixed, two consecutive runs on
    // one build still read 34 of 332 rules examined and 35 of 334 — the
    // REACH varies, so the population differs rather than the verdicts.
    // A ceiling on a quantity that jitters does not merely fail at random:
    // it teaches whoever hits it to re-run until green, which is how a real
    // dead rule gets through. And this check's own comment already said the
    // LIST is the thing — *raising this number is allowed and raising it
    // without reading the list is not* — which makes the count a proxy for
    // a set somebody was asked to read by hand.
    //
    // So the set is written down. A rule NOT on it fails and is named; a
    // run that happens to find one fewer still passes, because a subset is
    // not a regression. That is jitter-immune, it says exactly what is new,
    // and it turns an instruction to a human into code.
    //
    // Every entry was read. Two rules LEFT the old count because the scan
    // stopped calling an asleep rule dead — `.band > .band-head` and
    // `.storylead, .storysm`, both `display`, both the only declaration
    // below the breakpoint. Three ENTERED because scanning at 390 put the
    // `@media (max-width: 44rem)` block in this scan's reach for the first
    // time. Two more entered with the theme page and were REMOVED from the
    // stylesheet, because they were real: `display: block` on the
    // photograph inside an opening, restating what a grid item already
    // computes — the third and fourth dead `display: block` found on a
    // photograph container here, each in the first run where a photograph
    // actually rendered.
    const WIDTHS = [[1280, 900], [390, 844]];
    //
    // AND FOUR ENTERED BECAUSE THE PLATE SEQUENCE MADE THE BASE RULE THE
    // SUPERSEDED ONE, which is the case this comment already describes as
    // legitimate — a base rule beaten by a variant on every page that has
    // one, where the honest fix is a refactor rather than a deletion. The
    // hero's shore band and its country names are both stated on
    // `.heroeurope` and then restated on `.sheet-door .op .heroeurope`,
    // because the picture's ground changed when the plate's wall did and
    // the drawing exists on exactly one page today: `--ocean-deep` at 34%
    // against `--ocean-shallow` at 26%, and a 48% graphite name against the
    // map's own ink with a white halo. Deleting the base would leave the
    // next caller of `heroeurope()` with no shore and black names.
    // `.sheet {display}` is the same shape one level up: `display: grid` is
    // the plate's own default and every `.sheet-*` variant that exists sets
    // its own, so the grid is what a plate with no variant would get and
    // there is not one yet. `.doorgo {opacity}` is the fourth, and it is
    // the reveal on the homepage's four doors — measured dead because the
    // pointer is nowhere, which is this scan's own recorded finding.
    const DEAD_KNOWN = new Set([
      ".band > .band-head > .lede {color}",
      ".heroeurope .lyr-coastal-water use {fill}",
      ".heroeurope .lyr-labels .cname {fill}",
      ".sheet {display}",
      ".band-head {display}",
      ".card {display}",
      ".credit {opacity}",
      ".doorgo {opacity}",
      ".ed-eyebrow {color}",
      ".ed-index dd {color}",
      ".ed-opening-visual svg {display}",
      ".ed-section-index {color}",
      ".ed-split-copy p {color}",
      ".leg .hop {color}",
      ".locator svg {display}",
      ".masthead {color}",
      ".minidot circle {opacity}",
      ".minidot.here circle {opacity}",
      ".minimap figcaption {color}",
      ".minimap {color}",
      ".minimap.arched .context path {fill}",
      ".minimap.arched .context path {stroke}",
      ".minimap.arched .minidot.here circle {fill}",
      ".minimap.arched figcaption {color}",
      ".minimap.arched.atlas .lyr-destinations .minidot.here circle {fill,stroke}",
      ".minimap.arched.atlas .lyr-labels .minilabel {fill,stroke}",
      ".minimap.arched.atlas .lyr-land .countries path {fill,stroke}",
      ".minimap.arched.atlas .lyr-ocean rect {fill}",
      ".nav a[aria-current=\"page\"] {color}",
      ".navsearch {color}",
      ".plate {display}",
      ".portrait svg {display}",
      ".reasons .rt {color}",
      ".route .hop {color}",
      ".route .leg-nights {color}",
      ".scalebar text {fill}",
      ".sheet-atlas {color}",
      ".staged .now {color}",
    ]);
    const seen = new Map();
    const dsp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    // AND THE PAGE SET IS THE INSTRUMENT'S REACH. `.regionglyph .countries
    // path` was reported dead and it is what paints the nine lit regions on
    // /countries — a whole family this scan had never visited, so a rule that
    // wins on the atlas index looked like one that wins nowhere. A ceiling
    // raised for that would have been a ceiling raised for a gap in the
    // scan. Five families added: the atlas index, an interest page, a
    // motion, the search instrument and the Fund. Adding pages does NOT only
    // lower the count, which was the first guess and was wrong: a rule that
    // matched no element anywhere in the old set was not counted at all, and
    // a new page can make it match and still not win.
    for (const [vw, vh] of WIDTHS) {
    await dsp.setViewportSize({ width: vw, height: vh });
    for (const u of ["/", "/europe/austria", "/europe/austria/tyrol",
                     "/europe/austria/tyrol/innsbruck",
                     "/journeys/the-alpine-grand-tour", "/discover/nordic",
                     // AND IT READ `/events/oct` AND NEVER `/events`, so
                     // the index's own two `display: block` bands were
                     // measured only on the HOMEPAGE, where `.sheet-year`
                     // is already `sheet-gal` and block — and reported
                     // dead. Removing them on /events takes the year chart
                     // from 1,152 pixels to 619 and the shoulder
                     // photograph from 752 to 392. *A rule measured only
                     // where it loses looks like a rule that wins
                     // nowhere*, for the fourth time, and for the fourth
                     // time the answer is a page.
                     "/events", "/events/oct", "/beyond-the-obvious", "/map", "/plan",
                     "/stories", "/themes", "/countries",
                     "/interests/mountains", "/europe-in/by-rail",
                     // AND THE ONE FAMILY THAT CARRIES A PHOTOGRAPH HAD
                     // NEVER BEEN SCANNED. Widening to 390 made
                     // `.credit {opacity}` visible to this scan for the
                     // first time — the phone rule that reveals the licence
                     // credit, which is `opacity: 0` until hover on a desk —
                     // and it was reported dead because not one of the
                     // seventeen pages here carries a `.credit` where the
                     // rule decides anything. Measured on a real theme page
                     // it is 1 at 390 and 0 at 1280, which is the rule
                     // working. That is this check's own recorded finding
                     // about `.regionglyph .countries path`: a rule measured
                     // only where it loses looks like a rule that wins
                     // nowhere, and a ceiling raised for that is a ceiling
                     // raised for a gap in the scan.
                     "/themes/mountain-europe",
                     // AND THREE OF THE FOUR INDEXES THE ROOM SYSTEM WAS
                     // BUILT FOR ARE STILL NOT IN THIS LIST, WHICH IS
                     // MEASURED AND DEFERRED RATHER THAN UNKNOWN. It
                     // carries `/discover/nordic` — a macro REGION page —
                     // and no `/discover`, no `/experiences`, no
                     // `/journeys`. The cost showed up as a false verdict:
                     // the only page here that has ever carried a
                     // `.sheet-paper` band is /plan, where `.sheet-desk`
                     // used to set the same colour later at the same
                     // specificity, so `.sheet-paper {color}` was reported
                     // dead — and removing it in the browser turns every
                     // word on /discover's six light bands from
                     // rgb(20,23,22) to rgb(243,240,230). Bone on bone, on
                     // six bands of the page this room system was written
                     // for. That is this check's own recorded finding for
                     // the third time, after `.regionglyph .countries path`
                     // and `.credit {opacity}`: a rule measured only where
                     // it loses looks like a rule that wins nowhere — and
                     // the reason nothing here is deleted on this scan's
                     // word alone.
                     //
                     // Adding the three takes the population from 381 rules
                     // to 506 and the dead list from 42 to 71, with 31
                     // fresh — ten of them `.sheet-X { display: block }`
                     // restating `.sheet-gal`, the rest needing to be read
                     // one at a time. That is its own commit with its own
                     // triage rather than a widening smuggled into a page
                     // build, which is how `c_photo_safe_area`'s ten
                     // templated slots were handled for the same reason.
                     "/search", "/fund"]) {
      await dsp.goto(base + u, { waitUntil: "load" });
      const rows = await dsp.evaluate(() => {
        const PROPS = ["fill", "stroke", "display", "color",
                       "background-color", "opacity", "visibility"];
        const sheet = [...document.styleSheets]
          // The stylesheet is content-addressed — europedoor.<hash>.css — so
          // this matched nothing the day assets were hashed and the scan's
          // own reach assertion caught it, which is what that assertion is
          // for. Matched by stem rather than by full filename.
          .find((s) => /\/assets\/css\/europedoor\./.test(s.href || ""));
        if (!sheet) return [];
        const flat = [];
        // A CSSStyleRule carries an EMPTY cssRules list for CSS nesting, and
        // an empty list is truthy — the first version of this walker recursed
        // into nothing for every rule, collected none of the 630, and
        // reported a clean result. That is the failure this check is about.
        // AND A MEDIA RULE THAT DOES NOT CURRENTLY APPLY IS NOT DEAD, IT IS
        // ASLEEP. The first version flattened every @media block, so the
        // dark-preference stroke on the aperture's edge was reported as a
        // rule that never wins — true in the light preference this runs in,
        // and exactly the wrong conclusion.
        const walk = (rs, live) => {
          for (const r of rs) {
            const cond = r.conditionText || r.media?.mediaText;
            const on = cond ? live && matchMedia(cond).matches : live;
            if (r.cssRules && r.cssRules.length) walk([...r.cssRules], on);
            else if (on && r.selectorText && r.style) flat.push(r);
          }
        };
        walk([...sheet.cssRules], true);
        // AND THE SCAN READS A RESTING PAGE, BECAUSE A TRANSITIONED
        // PROPERTY DOES NOT ANSWER THIS QUESTION. `getComputedStyle`
        // returns the INTERPOLATED value while a transition is in flight,
        // and removing the declaration behind it does not change that
        // value in the same frame — so a rule that decides everything
        // reads as a rule that changes nothing. Measured on the homepage's
        // atlas band: `.atstage[data-at] .atname {opacity}` read 0.344667
        // and then 0.665944 on two runs of the same build, where a single
        // clean read of the same element returns exactly 0.34 and names
        // that rule as the only one that matches it. Two live rules were
        // reported dead, and the values differed between runs — which is
        // the jitter this check already refuses in its own count.
        // Inserted AFTER the walk so the guard is not itself scanned, and
        // removed at the end; `insertRule` on a same-origin sheet rather
        // than a `<style>` element, because this site's CSP has no
        // `style-src` opening and the scan may not be the thing that
        // needs one.
        const stopIdx = sheet.cssRules.length;
        sheet.insertRule("*, *::before, *::after { transition: none " +
                         "!important; animation: none !important }", stopIdx);
        const out = [];
        for (const rule of flat) {
          const props = PROPS.filter((p) => rule.style.getPropertyValue(p));
          if (!props.length) continue;
          let els;
          try { els = document.querySelectorAll(rule.selectorText); }
          catch (e) { continue; }
          if (!els.length) continue;
          // SAMPLED ACROSS THE MATCHES, NOT OFF THE FRONT. This was
          // `.slice(0, 40)`, and on /countries the first forty elements
          // matching `.regionglyph .countries path` are all inside the hero
          // glyph, where `.iheroart` overrides the fill — so the rule that
          // paints the nine lit macro regions further down the page was
          // measured only where it loses, and reported as dead. A cap is
          // fine; taking it off one end is not.
          const pick = [...els];
          const step = Math.max(1, Math.ceil(pick.length / 40));
          const sample = pick.filter((_, i) => i % step === 0).slice(0, 40);
          // AND `getPropertyValue`, NOT INDEXING. This read
          // `getComputedStyle(e)[p]`, and `p` is a hyphenated CSS name —
          // `getComputedStyle(e)["background-color"]` is `undefined` for
          // every element that has ever existed. So one of the seven
          // properties this scan claims to measure was never measured at
          // all: before and after both read "undefined", they matched, and
          // any rule whose only measured property was a background was
          // reported dead. The other six survive indexing because their
          // names have no hyphen, which is exactly why nobody noticed.
          const read = () => sample
            .map((e) => props.map((p) => getComputedStyle(e).getPropertyValue(p))
                             .join("|"));
          const before = read();
          const saved = props.map((p) => [p, rule.style.getPropertyValue(p),
                                          rule.style.getPropertyPriority(p)]);
          for (const [p] of saved) rule.style.removeProperty(p);
          const after = read();
          for (const [p, v, pr] of saved) rule.style.setProperty(p, v, pr);
          out.push([`${rule.selectorText} {${props.join(",")}}`,
                    before.some((b, i) => b !== after[i])]);
        }
        sheet.deleteRule(stopIdx);
        return out;
      });
      for (const [k, won] of rows) {
        seen.set(k, (seen.get(k) || false) || won);
      }
    }
    }
    await dsp.close();
    const dead = [...seen.entries()].filter(([, won]) => !won).map(([k]) => k);
    ok(seen.size > 100,
       `the dead-rule scan examined only ${seen.size} rules — it has stopped ` +
       "walking the stylesheet, which is exactly how its first version " +
       "reported a clean result while collecting nothing");
    // THE WHOLE LIST, NOT THE FIRST FOUR. For the life of this check the
    // failure printed four names out of two dozen, so the list it demanded
    // you read was the one thing it would not show you.
    const fresh = dead.filter((d) => !DEAD_KNOWN.has(d));
    ok(fresh.length === 0,
       `${fresh.length} stylesheet rule(s) match elements and change none of ` +
       `them at ${WIDTHS.map(([w]) => w).join(" or ")}, and are not on the ` +
       `known list (${dead.length} dead of ${seen.size} examined). Read them, ` +
       `then either fix them or add them to DEAD_KNOWN with the reason:\n    ` +
       fresh.join(";\n    "));
  }
  await page.setViewportSize({ width: 1280, height: 900 });

  // ── the colour the BROWSER paints, on the ground it paints it on ───
  //
  // `accent-color` is what a checkbox, a radio and a range thumb are drawn
  // in, and it was bound on `:root` to a light-world token. A var() in a
  // declaration resolves where the DECLARATION lives, and the world tokens
  // sit on `body[data-world]` — a descendant — so every world inherited the
  // light world's number: cobalt-deep, which is 6.31:1 on limestone and
  // **2.75:1 on the graphite ground**, under the 3:1 SC 1.4.11 asks of a
  // user interface component. On the five INTELLIGENCE pages, which are the
  // pages that hold the checkboxes the property was added for.
  //
  // Read off the browser rather than off the stylesheet, because the failure
  // was invisible in the source: the rule said var(--sea) and meant it.
  for (const u of ["/plan", "/discover", "/events", "/fund", "/"]) {
    await page.goto(base + u, { waitUntil: "load" });
    const m = await page.evaluate(() => {
      const px = (c) => (c.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
      const lum = ([r, g, b]) => {
        const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
      };
      const ground = (el) => {
        for (let e = el; e; e = e.parentElement) {
          const b = getComputedStyle(e).backgroundColor;
          const p = px(b);
          if (p.length === 3 && !/rgba\(.*,\s*0\)/.test(b)) return p;
        }
        return [255, 255, 255];
      };
      const b = document.body;
      const a = px(getComputedStyle(b).accentColor);
      const g = ground(b);
      const la = lum(a), lg = lum(g);
      return { accent: a, ground: g,
               ratio: (Math.max(la, lg) + 0.05) / (Math.min(la, lg) + 0.05) };
    });
    ok(m.ratio >= 3.0,
       `${u}: accent-color rgb(${m.accent}) measures ${m.ratio.toFixed(2)}:1 on ` +
       `rgb(${m.ground}) — a checkbox the browser paints needs 3:1`);
  }

  // ── THE CONTRAST UNDER THE GLYPHS, NOT UNDER THE TOKEN ─────────────
  //
  // Every contrast assertion in this suite reads a declared colour against a
  // declared background, and the hero has neither: its type sits on a
  // drawing of Europe, so the ratio varies from letter to letter and the
  // number in the stylesheet's own comment ("7.7:1 bare, 6.9:1 on the
  // lightest pool") was measured against the WATER, before the continent was
  // drawn over it. Nothing here had ever asked what colour is actually under
  // the words.
  //
  // The instrument shoots the page twice, with the type and without it. A
  // pixel that differs between the two is a pixel a glyph paints, and the
  // ground under exactly those pixels is what the reader's eye is up
  // against. MEASURING THE BOX INSTEAD IS WRONG AND SAYS SO LOUDLY: the h1's
  // measure is 14ch and the headline does not fill it, so a scan over the
  // rectangle reported the bright parchment in the gutter past the last
  // letter as a failure of the type — 2.15:1 against a real 9.58.
  //
  // The screenshots come back into the page as data: URLs, which `img-src
  // 'self' data:` already allows, rather than through a PNG decoder here.
  {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(base + "/", { waitUntil: "networkidle" });
    await page.waitForTimeout(400);
    // `.herobody` WAS THE DRAWN HERO'S TYPE AND THE PLATE SEQUENCE REPLACED
    // IT, so this measured nothing and said so. The successor is plate 03,
    // which is the one surface on the homepage where type stands over a
    // PHOTOGRAPH — exactly the case a token-based ratio cannot answer and
    // this instrument exists for.
    //
    // Measure where the GLYPHS are, not where the box is: shoot the page
    // twice, with the ink and without, and a pixel that differs is a pixel
    // a glyph paints. Scanning the rectangle instead reads the bright
    // ground in the gutter past the last letter as a failure of the type.
    //
    // FOUR THINGS ABOUT THIS INSTRUMENT WERE WRONG AND EACH ONE PASSED.
    //
    // 1 · IT WAS READING PAST THE END OF ITS OWN SCREENSHOT. Plate 03 is
    //     1,818 pixels below the fold and `page.screenshot()` without
    //     `fullPage` photographs the VIEWPORT, so the type sat at
    //     y=2301..2447 of a 900-pixel image. Every index was past the end
    //     of the pixel data, `A.data[i]` was `undefined`, and
    //     `Math.abs(undefined - undefined)` is NaN — so `NaN < 40` is false
    //     and the "no glyph paints here" test never fired, which meant
    //     every out-of-bounds pixel was COUNTED as a glyph and satisfied
    //     the reach guard; and `NaN < worst` is false too, so `worst`
    //     stayed Infinity and the ratio passed. One NaN defeated the
    //     measurement and the guard written to catch a defeated
    //     measurement, in the same loop. That is the year band's own
    //     recorded failure — a sampler that reads outside its own image
    //     reports the canvas — arriving through the one hole its guard did
    //     not cover, because the guard counted PIXELS rather than asserting
    //     the rectangle was IN the picture. Both now.
    //
    // 2 · ONE FRAME CANNOT HOLD FOUR ELEMENTS. Scrolling the plate to the
    //     middle puts the headline and the standfirst in shot and pushes
    //     the licence credit 21 pixels past the bottom edge — so a single
    //     pair of screenshots would have measured two elements and failed
    //     the reach guard on a third for a reason that is about the
    //     instrument rather than the page. Each element is scrolled into
    //     its own frame and shot there.
    //
    // 3 · HIDING THE ELEMENT HID ITS SCRIM. `visibility: hidden` was right
    //     while every measured element painted nothing of its own, and
    //     wrong the moment one carried a tint: hiding the credit hid the
    //     scrim the credit exists to sit on, so the "ground" shot was the
    //     bare photograph and the instrument reported the defect the scrim
    //     had already fixed — 2.00:1 against a real 10.39. The ground a
    //     glyph is painted over includes whatever its own box paints, so
    //     the ink is removed and the box is left standing.
    //
    // 4 · AND `color: transparent` IS READ BACK AS rgba(0,0,0,0), so the
    //     foreground has to be captured BEFORE it is removed or every ratio
    //     collapses to about 1:1 — a failure that looks exactly like the
    //     defect being measured.
    /* AND THE CREDIT IS MEASURED WHEN THERE IS ONE. A production
     * photograph publishes its photographer and its licence, and while a
     * DESIGN asset stands in for that surface there is nothing to credit
     * and nothing to measure — a design asset shows a reader nothing about
     * where it came from, which is the whole point of it. `optional` says
     * which of these may honestly be absent, so the check still fails on a
     * headline that has gone missing and no longer fails on a credit that
     * is correctly not there. */
    const SEL = [[".sheet-bleed .mega", 3.0], [".sheet-bleed .lede", 4.5],
                 [".sheet-bleed .go", 4.5],
                 [".sheet-bleed .sheetcred", 4.5, "optional"]];
    const OPTIONAL = new Set([".sheet-bleed .sheetcred"]);
    for (const [sel, floor] of SEL) {
      const there = await page.evaluate((s) => {
        const e = document.querySelector(s);
        if (!e) return false;
        e.scrollIntoView({ block: "center" });
        return true;
      }, sel);
      if (!there && OPTIONAL.has(sel)) continue;
      ok(there, `${sel} is not on the homepage to measure`);
      if (!there) continue;
      await page.waitForTimeout(250);
      const withType = (await page.screenshot()).toString("base64");
      await page.evaluate((s) => {
        const e = document.querySelector(s);
        e.dataset.edInk = getComputedStyle(e).color;
        e.style.setProperty("color", "transparent", "important");
        e.querySelectorAll("*").forEach((k) =>
          k.style.setProperty("color", "transparent", "important"));
      }, sel);
      const noType = (await page.screenshot()).toString("base64");
      const r = await page.evaluate(async ({ a, b, s }) => {
        const load = (d) => new Promise((res) => {
          const i = new Image(); i.onload = () => res(i); i.src = "data:image/png;base64," + d;
        });
        const grab = async (d) => {
          const img = await load(d);
          const c = document.createElement("canvas");
          c.width = img.width; c.height = img.height;
          c.getContext("2d").drawImage(img, 0, 0);
          return c.getContext("2d").getImageData(0, 0, img.width, img.height);
        };
        const A = await grab(a), B = await grab(b);
        const lum = (r, g, bl) => {
          const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
          return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(bl);
        };
        const e = document.querySelector(s);
        const rc = e.getBoundingClientRect();
        const col = e.dataset.edInk || getComputedStyle(e).color;
        let fg = [255, 255, 255], al = 1;
        const m = col.match(/color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)(?: \/ ([\d.]+))?\)/);
        if (m) { fg = [m[1] * 255, m[2] * 255, m[3] * 255]; al = m[4] ? +m[4] : 1; }
        else { const n = (col.match(/[\d.]+/g) || []).map(Number); fg = n.slice(0, 3); al = n[3] === undefined ? 1 : n[3]; }
        const dpr = A.width / innerWidth;
        const inside = rc.top >= 0 && rc.left >= 0
                    && Math.round(rc.bottom * dpr) <= A.height
                    && Math.round(rc.right * dpr) <= A.width;
        let worst = Infinity, at = null, painted = 0;
        if (inside) {
          for (let y = Math.round(rc.top * dpr); y < Math.round(rc.bottom * dpr); y++) {
            for (let x = Math.round(rc.left * dpr); x < Math.round(rc.right * dpr); x++) {
              const i = (y * A.width + x) * 4;
              const d = Math.abs(A.data[i] - B.data[i]) + Math.abs(A.data[i + 1] - B.data[i + 1])
                      + Math.abs(A.data[i + 2] - B.data[i + 2]);
              if (d < 40) continue;             // no glyph paints here
              painted++;
              const g = [B.data[i], B.data[i + 1], B.data[i + 2]];
              const Lb = lum(g[0], g[1], g[2]);
              const Lf = lum(fg[0] * al + g[0] * (1 - al), fg[1] * al + g[1] * (1 - al),
                             fg[2] * al + g[2] * (1 - al));
              const cr = (Math.max(Lf, Lb) + 0.05) / (Math.min(Lf, Lb) + 0.05);
              if (cr < worst) { worst = cr; at = [x, y, g]; }
            }
          }
        }
        return { worst, at, painted, inside,
                 rect: [Math.round(rc.top), Math.round(rc.bottom)],
                 shot: [A.width, A.height] };
      }, { a: withType, b: noType, s: sel });
      ok(r.inside,
         `${sel} sits at y=${r.rect.join("..")} and the screenshot is ` +
         `${r.shot.join("x")} — the sample landed OUTSIDE its own image, so ` +
         "every reading from it is of undefined pixels");
      if (!r.inside) continue;
      // A count of the glyph pixels, because a diff that finds none reports
      // Infinity and passes — the same shape as a suite that stops counting.
      ok(r.painted > 400,
         `${sel}: only ${r.painted} glyph pixels found — the two shots did ` +
         "not differ, so this measured nothing and would pass on anything");
      ok(r.worst >= floor,
         `${sel} over the photograph measures ${r.worst.toFixed(2)}:1 at its ` +
         `worst glyph pixel, under the ${floor}:1 floor — ground ` +
         `rgb(${(r.at || [])[2]}) at ${(r.at || []).slice(0, 2)}`);
    }
  }

  // ── the photograph is a window, and a window is proved by scrolling ─
  //
  // Plate 03 is a full-bleed photograph fixed to the VIEWPORT and clipped by
  // the band, so the picture stands still and the page is drawn past it.
  // Six CSS properties silently destroy that: `transform`, `filter`,
  // `backdrop-filter`, `perspective`, `will-change` naming any of them, and
  // `contain`. Each makes an element a containing block for FIXED
  // descendants, so `position: fixed` resolves against that element instead
  // of the viewport — the picture starts scrolling with the page again and
  // NOTHING reports a fault, because every box is still the right size in
  // the right place and every contrast, layout and count check goes on
  // passing. The stylesheet already carries three of those six properties
  // elsewhere (`backdrop-filter` on the masthead, `filter: drop-shadow` on
  // two map layers), so this is not a hypothetical.
  //
  // Three assertions, because the first two are the cause and the third is
  // the promise. Walking the chain names WHICH element broke it, which a
  // measurement alone cannot; scrolling and re-measuring is the only proof
  // that the effect a reader gets is the effect that was written — the same
  // reasoning as the label metrics, where the model cannot check itself and
  // the browser's own geometry is the instrument.
  for (const w of [1280, 390]) {
    await page.setViewportSize({ width: w, height: w === 1280 ? 900 : 844 });
    await page.goto(base + "/", { waitUntil: "networkidle" });
    const r = await page.evaluate(() => {
      const band = document.querySelector(".sheet-bleed");
      if (!band) return { missing: true };
      const pic = band.querySelector(".shotfull");
      if (!pic) return { nopic: true };
      const NAMES = { transform: "transform", filter: "filter",
                      backdropFilter: "backdrop-filter", perspective: "perspective",
                      willChange: "will-change", contain: "contain" };
      const IDLE = { transform: "none", filter: "none", backdropFilter: "none",
                     perspective: "none", willChange: "auto", contain: "none" };
      const blockers = [];
      for (let e = pic; e && e !== document.documentElement; e = e.parentElement) {
        const c = getComputedStyle(e);
        for (const k of Object.keys(NAMES)) {
          if (c[k] && c[k] !== IDLE[k]) {
            const cls = String(e.className || "").trim();
            blockers.push(e.tagName.toLowerCase()
              + (cls ? "." + cls.split(/\s+/).join(".") : "")
              + ` sets ${NAMES[k]}: ${c[k]}`);
          }
        }
      }
      /* WHAT IS PROMISED IS THAT THE PICTURE STANDS STILL, NOT THAT IT IS
       * `position: fixed`. The first version asserted the mechanism, and
       * the mechanism changed for a reason that is about correctness: a
       * fixed box inside a `clip-path` is two undefined-in-practice
       * behaviours stacked on one composition — the six containing-block
       * properties this same check walks for, and the CSS Masking rule
       * that a `clip-path` other than `none` creates a containing block
       * for fixed descendants, which Chromium does not implement and
       * other engines do. The picture stands by STICKING now. So the
       * question is whether anything between it and the band detaches it
       * from the wall's flow, and the measurement below is what actually
       * proves the promise. */
      const pos = getComputedStyle(pic).position;
      let stands = "";
      for (let e = pic; e && e !== document.body; e = e.parentElement) {
        const q = getComputedStyle(e).position;
        if (q === "fixed" || q === "sticky") {
          const cls = String(e.className || "").trim();
          stands = e.tagName.toLowerCase()
            + (cls ? "." + cls.split(/\s+/).join(".") : "") + ` is ${q}`;
          break;
        }
      }
      /* THE APERTURE IS `.shotclip` AND NOT THE BAND, and the band is what
       * this read when it was repointed off the class that no longer
       * exists. The stylesheet says why: a clip on the band clipped the
       * band's OWN background and its label away, so the opening is its own
       * absolutely positioned box in the top of the wall — which is also
       * what makes its lower edge sweeping down across the standing picture
       * read as a window closing. The promise is unchanged: something
       * between the viewport and the picture has to carry a clip, because
       * `overflow: hidden` cannot clip a fixed descendant. */
      const cliphost = band.querySelector(".shotclip") || band;
      const clip = getComputedStyle(cliphost).clipPath;
      const ap = cliphost.getBoundingClientRect();
      // The reveal itself: put the band in view, note where the picture is,
      // scroll a third of a screen, and ask again.
      /* FROM THE START OF THE BAND, NOT ITS MIDDLE. A picture that stands
       * by sticking stands for a bounded distance — its container's height
       * less one viewport — so a measurement that begins halfway through
       * the band can begin after the standing has ended and report the
       * picture travelling when it has simply finished. `start` is where
       * the standing starts, which is the only place this promise can
       * honestly be measured from.
       *
       * AND THE BAND'S START IS NOT THE OPENING'S. The wall carries the
       * plate mark and the aperture is cut BELOW it, so a scroll to the top
       * of the band begins 230 pixels before the sticky box engages — and
       * the picture then travels those 230 with the wall, exactly as it
       * should, and the measurement calls that a panel. The aperture is
       * where the standing starts, which is why this scrolls the clip host
       * rather than the section. */
      cliphost.scrollIntoView({ block: "start" });
      const img = pic.querySelector("img") || pic;
      const before = img.getBoundingClientRect();
      const y0 = scrollY;
      scrollBy(0, 300);
      const after = img.getBoundingClientRect();
      return { position: pos, stands, clip, blockers,
               scrolled: scrollY - y0,
               moved: Math.round(Math.abs(after.top - before.top)),
               /* AND IT FILLS THE APERTURE RATHER THAN THE VIEWPORT.
                * The first version asked for the whole screen, which was
                * true while the picture was `inset: 0` — and the crop-box
                * measurement then bounded it deliberately, because a
                * viewport-filling slot guaranteed only 9% of a
                * photograph's frame at some window shapes and this one
                * guarantees 35.5%. So the question is whether the window
                * is full, not whether the screen is: a gap here is the
                * wall showing through the opening. */
               /* AND THE WINDOW IS MOUNTED RATHER THAN FULL. The first
                * version asked the picture to fill the viewport, which was
                * true while it was `inset: 0` — and the crop-box
                * measurement then bounded it deliberately, because a
                * viewport-filling slot guaranteed only 9% of a
                * photograph's frame at some window shapes against 35.5%
                * for this one. So the picture is narrower or shorter than
                * the opening by design, and the promise is not that there
                * is no gap: it is that the gap is the OPENING's own
                * ground and not the wall's. Light wall, dark opening is
                * this atlas's whole reading of an aperture, and a gallery
                * mounts a picture smaller than its frame rather than
                * leaving the wall showing through. Measured as the step
                * between the two grounds, which is the same instrument
                * the arch's reveal is held to.
                * The WIDTH still has to reach, because a mount down the
                * sides of a landscape is a hole beside it rather than a
                * mount under it. */
               wide: Math.round(before.width) >= Math.round(ap.width) - 1,
               wall: getComputedStyle(band).backgroundColor,
               mount: getComputedStyle(cliphost).backgroundColor,
               ap: [Math.round(ap.width), Math.round(ap.height)],
               pic: [Math.round(before.width), Math.round(before.height)] };
    });
    ok(!r.missing && !r.nopic,
       `${w}: the homepage has no plate-03 photograph to measure — ` +
       `${r.missing ? "no .sheet-bleed" : "no .shotfull inside it"}`);
    if (r.missing || r.nopic) continue;
    ok(Boolean(r.stands),
       `${w}: the plate-03 picture computes position: ${r.position} and ` +
       "nothing between it and <body> is fixed or sticky — it is a panel " +
       "that scrolls with the wall, not a window the wall moves past");
    ok(r.clip && r.clip !== "none",
       `${w}: the plate-03 aperture has clip-path: ${r.clip} — `+
       "`overflow: hidden` does NOT clip a fixed descendant, because a fixed " +
       "box is laid out against the viewport rather than against any " +
       "scrolling ancestor, so without the clip the picture is loose over " +
       "the whole page");
    ok(r.blockers.length === 0,
       `${w}: ${r.blockers.length} element(s) between <body> and the ` +
       "plate-03 picture make a containing block for fixed descendants, " +
       "which turns it into an absolute box silently — " + r.blockers.join("; "));
    ok(r.scrolled > 0,
       `${w}: the page did not scroll (${r.scrolled}px), so the reveal was ` +
       "not exercised and the measurement below means nothing");
    ok(r.moved <= 1,
       `${w}: the plate-03 picture moved ${r.moved}px while the page ` +
       `scrolled ${r.scrolled}px — it is travelling with the page rather ` +
       "than standing still behind it");
    ok(r.wide,
       `${w}: the plate-03 picture is ${(r.pic || []).join("x")} inside an ` +
       `aperture of ${(r.ap || []).join("x")} — it does not reach the sides, ` +
       `so the opening shows ground beside the picture rather than under it`);
    {
      const px = (c) => (String(c).match(/\d+/g) || [0, 0, 0]).slice(0, 3).map(Number);
      const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92
        : Math.pow((v + 0.055) / 1.055, 2.4); };
        return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
      const a = lum(px(r.wall)), b2 = lum(px(r.mount));
      const step = (Math.max(a, b2) + 0.05) / (Math.min(a, b2) + 0.05);
      checked++;
      ok(step >= 3,
         `${w}: the plate-03 opening measures ${step.toFixed(2)}:1 against the ` +
         `wall around it — ${r.mount} inside ${r.wall}. The picture is bounded ` +
         `on purpose, so what shows above and below it has to read as the ` +
         `opening's own ground: light wall, dark opening, or it is a hole`);
    }
  }

  // ── an accent on every row is a texture, and the rule named classes ─
  //
  // A kicker says what KIND of thing is being read. One per head answers
  // that; inside a repeated item it answers nothing, because every sibling
  // carries the same signal — which is "never explain the constraint back"
  // arriving in colour, and on /themes it inverted the hierarchy it sat in.
  // That was fixed as `.row .kicker, .card .kicker`, which names two classes
  // rather than the situation, so it reached neither family on the HOMEPAGE:
  // measured here across nine surfaces, every index came back at zero accent
  // kickers inside a link and the homepage came back at SIX — three journey
  // rows carrying their country chain in cobalt uppercase above a serif
  // name, and three story cards carrying their desk. The chain is the
  // journey's own route, which is content rather than a label, and it was
  // the brightest thing in the row on the one page that opens the site.
  //
  // The situation is the rule now: a kicker inside a LINK labels one item in
  // a set, a kicker outside one labels the page or the band. This reads the
  // colour the browser PAINTS rather than the selector, because the defect
  // was invisible to a selector — two correct rules that matched nothing.
  for (const u of ["/", "/journeys/", "/themes/", "/interests/", "/stories/",
                   "/countries/", "/beyond-the-obvious/"]) {
    const r = await page.goto(base + u, { waitUntil: "load" });
    if (!r || r.status() !== 200) continue;
    const k = await page.evaluate(({ SWATCH, MAXD }) => {
      const srgb = (c) => (c <= 0.04045 ? c / 12.92
                                        : Math.pow((c + 0.055) / 1.055, 2.4));
      const oklab = (R, G, B) => {
        const r = srgb(R), g = srgb(G), b = srgb(B);
        const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
        const m2 = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
        const s2 = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
        return [0.2104542553 * l + 0.7936177850 * m2 - 0.0040720468 * s2,
                1.9779984951 * l - 2.4285922050 * m2 + 0.4505937099 * s2,
                0.0259040371 * l + 0.7827717662 * m2 - 0.8086757660 * s2];
      };
      const marks = SWATCH.map((t) => ({
        family: t.family,
        lab: oklab(parseInt(t.hex.slice(1, 3), 16) / 255,
                   parseInt(t.hex.slice(3, 5), 16) / 255,
                   parseInt(t.hex.slice(5, 7), 16) / 255),
      }));
      const familyOf = (rgb) => {
        const lab = oklab(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255);
        let best = "", bd = Infinity;
        for (const m of marks) {
          const dl = lab[0] - m.lab[0], da = lab[1] - m.lab[1],
                db = lab[2] - m.lab[2];
          const dist = dl * dl + da * da + db * db;
          if (dist < bd) { bd = dist; best = m.family; }
        }
        return Math.sqrt(bd) > MAXD ? "" : best;
      };
      // `.actname` IS A KICKER. The plate sequence labels each band with one
      // — THE DOOR, THE QUESTION — and carries no `.kicker` at all, so this
      // probe examined zero elements on the homepage and its own
      // stopped-finding guard fired. The promise is about a label painted
      // in the accent inside a link, and an act name is that kind of label.
      // AND `.ed-eyebrow` IS A KICKER TOO. The non-home redesign gave eight
      // families a new opening whose label is `ed-eyebrow`, so /countries
      // carried no `.kicker` at all and this probe's own stopped-finding
      // guard fired — correctly, about a page that had got better. A check
      // on a class name is a check on a shape; the promise is about a label
      // painted in the accent inside a link.
      const all = [...document.querySelectorAll(
        ".kicker, .actname, .ed-eyebrow, .ed-section-index")];
      const hot = all.filter((e) => {
        // AN ACCENT IS A FAMILY, NOT A HUE WINDOW. This tested `blue > red +
        // 40`, which is a claim about cobalt rather than about the accent —
        // so the day the signature became pine it matched nothing and the
        // check reported every page clean. Rewritten as a hue band it then
        // read the SIGNATURE's window, which the owner's palette made
        // three tenths of a degree from the water's. The register says
        // which family a colour is in; the question here is whether the
        // label is painted in one of the two families that ARE accents.
        const f = familyOf(getComputedStyle(e).color.match(/\d+/g).map(Number));
        return f === "accent" || f === "pine";
      });
      const inLink = hot.filter((e) => e.closest("a"));
      return { all: all.length,
               bad: inLink.map((e) => e.textContent.trim().slice(0, 40)) };
    }, { SWATCH, MAXD });
    checked++;
    ok(k.all > 0, `${u}: no kicker at all — this check has stopped finding ` +
       `the element it is about`);
    ok(k.bad.length === 0,
       `${u}: ${k.bad.length} of ${k.all} kickers are painted in the accent ` +
       `inside a link — "${k.bad[0]}". A signal every sibling carries is a ` +
       `texture, not an accent, and it makes the label brighter than the ` +
       `name under it`);
  }

  // ── a head that is worse in the middle of its own range ────────────
  //
  // Two commits found the same fault at the same width in two different
  // heads, and neither was visible at 390 or at 1280. The country portrait
  // head splits into two columns at 52rem with the door on an `auto` track,
  // so at 834 the type column was 174 pixels and the tagline set on five
  // lines of three words. The instrument head is `auto 1fr auto`, and a grid
  // hands an `auto` track its max-content before an `fr` track takes what is
  // left, so /plan's title had 127 pixels and set 43 characters on FIVE
  // lines — against one at 704, where the head has not split yet, and two at
  // 1280.
  //
  // THE PROMISE IS RELATIVE, BECAUSE AN ABSOLUTE ONE IS WRONG. "Tyrol & the
  // West" sets on two lines at every width from 390 to 1600 and that is the
  // overture's own design — a narrow measure and air above it, where the
  // name is the event. Eight characters per line is not a defect there. What
  // IS a defect is a head that takes two more lines at some width than at
  // both a narrower and a wider one: nothing about the content changed, only
  // the track sizing, and a layout that is worse in the middle of its range
  // than at either end is a sizing fault rather than a design.
  //
  // Both elements, because the two faults landed on different ones: the
  // instrument's was its `h1` and the country's was its tagline.
  {
    const WIDTHS = [390, 704, 834, 900, 1024, 1280, 1600];
    const seen = new Map();
    for (const vw of WIDTHS) {
      const hp = await browser.newPage({ viewport: { width: vw, height: 900 } });
      for (const u of ["/", "/countries", "/europe/austria",
                       "/europe/austria/tyrol",
                       "/europe/austria/tyrol/innsbruck", "/journeys",
                       "/journeys/the-alpine-grand-tour", "/themes",
                       "/interests/mountains", "/europe-in/northern-lights",
                       "/events", "/beyond-the-obvious", "/map", "/plan",
                       "/search", "/discover", "/my-europe", "/experiences"]) {
        const r = await hp.goto(base + u, { waitUntil: "load" });
        if (!r || r.status() !== 200) continue;
        const d = await hp.evaluate(() => {
          const out = {};
          // `.ed-intro` IS THE REDESIGN'S STANDFIRST, WHICH IS WHAT
          // `.statement` WAS. The scan measures how many lines a head's
          // largest elements take at each width, and the eight rebuilt
          // families carry their standfirst in `.ed-intro` — so counting
          // only `.statement` asked about a class most heads no longer
          // have. The promise is about the head's own type, not about one
          // spelling of it.
          for (const sel of ["h1", ".statement", ".ed-intro"]) {
            // THE HEAD IS NO LONGER ONLY `.pagehead`. Eight families open
            // on `ed-opening`, `ed-arrival`, `ed-journey-hero` or
            // `ed-story-opening`, so this scan collected 11 elements of the
            // 20 its own reach assertion asks for — it had stopped finding
            // most of the heads it is about, which is exactly what that
            // assertion exists to say.
            // AND THE HOMEPAGE'S HEAD IS A SHEET, NOT A `pagehead`. It is
            // the one family that opens on an act rather than on a page
            // head — `.sheet-door` carries the `h1.mega` — so adding the
            // eight redesigned head shapes took the scan from 11 to 19 and
            // left it one under its own floor of 20. A scan that cannot see
            // the largest heading on the most-visited page is not measuring
            // the thing it is about.
            const el = document.querySelector(
              ":is(.pagehead, .ed-opening, .ed-arrival, .ed-journey-hero, " +
              ".ed-story-opening, .ed-institution, .sheet) " + sel);
            if (!el) continue;
            const lh = parseFloat(getComputedStyle(el).lineHeight);
            out[sel] = { lines: Math.max(1, Math.round(
              el.getBoundingClientRect().height / lh)),
              chars: el.textContent.trim().length };
          }
          return out;
        });
        for (const [sel, v] of Object.entries(d)) {
          const k = u + " " + sel;
          if (!seen.has(k)) seen.set(k, {});
          seen.get(k)[vw] = v;
        }
      }
      await hp.close();
    }
    // AGAINST THE BEST NARROWER AND THE BEST WIDER, not the immediate
    // neighbours. A fault can ramp: the country tagline set 3 lines at 704,
    // 5 at 834 and 4 at 900, so comparing with the neighbour on each side
    // misses it while the shape — worse in the middle than at either end —
    // is exactly the same.
    let worst = null, bad = 0;
    for (const [k, m] of seen) {
      const at = (w) => (m[w] ? m[w].lines : null);
      for (let i = 1; i < WIDTHS.length - 1; i++) {
        const c = m[WIDTHS[i]];
        if (!c) continue;
        const below = WIDTHS.slice(0, i).map(at).filter((v) => v !== null);
        const above = WIDTHS.slice(i + 1).map(at).filter((v) => v !== null);
        if (!below.length || !above.length) continue;
        const a = Math.min(...below), e = Math.min(...above);
        if (c.lines >= a + 2 && c.lines >= e + 2) {
          bad++;
          const gap = Math.min(c.lines - a, c.lines - e);
          if (!worst || gap > worst.gap) {
            worst = { gap, k, vw: WIDTHS[i], c, a: { lines: a },
                      e: { lines: e }, wa: "any narrower", we: "any wider" };
          }
        }
      }
    }
    checked++;
    ok(seen.size > 20,
       `the head-range scan collected only ${seen.size} elements — it has ` +
       "stopped finding the heads it is about");
    ok(bad === 0, worst
      ? `${bad} head(s) take two or more extra lines in the middle of their ` +
        `own range: ${worst.k} at ${worst.vw}px sets ${worst.c.chars} ` +
        `characters on ${worst.c.lines} lines, against ${worst.a.lines} at ` +
        `${worst.wa} and ${worst.e.lines} at ${worst.we}. Nothing about the ` +
        `content changed, only the track sizing.`
      : "no head is worse in the middle of its range");
  }

  // ── an option that does not fit the box it closes into ─────────────
  //
  // The planner's spending style read `{name} — {note}` and "Generous —
  // Well-reviewed hotels, restaurants that book out, flights and
  // first-class rail where it saves a day." is 118 characters: 810 pixels
  // in a 325-pixel field. A `<select>` clips without an ellipsis, so a
  // reader was shown forty per cent of their own choice and it did not even
  // look like a truncation.
  //
  // THE LINE IS HAND-WRITTEN ENUM AGAINST A LIST OF RECORDS. `#start` and
  // `#end` carry 314 real destinations and the longest is "Gura Humorului &
  // the painted monasteries, Romania" — the only repair available there is
  // truncating a place name, which this atlas refuses, and opening the
  // select is what a reader does to read the list. A list somebody TYPED
  // has no such excuse: every option in it is copy, and copy that does not
  // fit its control is copy in the wrong place. Thirty is the line and
  // every enum on the site is under five.
  for (const [vw, vh] of [[1280, 900], [390, 800]]) {
    const sp = await browser.newPage({ viewport: { width: vw, height: vh } });
    for (const u of ["/plan", "/discover", "/events", "/search"]) {
      const r = await sp.goto(base + u, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      const over = await sp.evaluate(() => {
        const out = [];
        for (const s of document.querySelectorAll("select")) {
          if (s.options.length > 30) continue;      // a list of records
          const cs = getComputedStyle(s);
          // the arrow the UA draws, plus the field's own padding
          const box = s.clientWidth - parseFloat(cs.paddingLeft)
                    - parseFloat(cs.paddingRight) - 28;
          const m = document.createElement("span");
          m.style.cssText = "position:absolute;visibility:hidden;white-space:pre;font:" + cs.font;
          document.body.appendChild(m);
          for (const o of s.options) {
            m.textContent = o.textContent;
            const w = m.getBoundingClientRect().width;
            if (w > box) out.push([s.id || s.name, o.textContent.slice(0, 40),
                                   Math.round(w), Math.round(box)]);
          }
          m.remove();
        }
        return out;
      });
      checked++;
      ok(over.length === 0,
         `${u} at ${vw}: ${over.length} hand-written option(s) wider than the ` +
         `select they close into — #${(over[0] || [])[0]} "${(over[0] || [])[1]}" ` +
         `needs ${(over[0] || [])[2]}px in ${(over[0] || [])[3]}px. A select ` +
         `clips without an ellipsis, so the reader is shown part of their own ` +
         `choice and it does not look like a truncation.`);
    }
    await sp.close();
  }

  // ── a placeholder that does not fit the box it is in ───────────────
  //
  // The homepage's own placeholder was cut mid-word at 390 and was fixed;
  // /search's was not, and it is the one control that page exists to be. It
  // carried three examples joined by middots — 84 characters — and rendered
  // as "quiet beaches in september · medieva". A rule that exists is not a
  // rule that is inherited.
  //
  // MEASURED AGAINST THE BOX, NOT COUNTED IN CHARACTERS. A character ceiling
  // is a proxy for a width and would be wrong the day the face or the
  // padding changes; the honest test is to put the placeholder in the field
  // as a value and ask the browser whether the field has to scroll. An input
  // is a scroll container, which is why the clipped-text check cannot see
  // this: scrolling is the right answer inside one, and a HINT nobody can
  // read is not.
  await page.setViewportSize({ width: 390, height: 800 });
  for (const u of ["/", "/search", "/plan"]) {
    await page.goto(base + u, { waitUntil: "load" });
    const cut = await page.evaluate(() => {
      const out = [];
      for (const el of document.querySelectorAll("input[placeholder], textarea[placeholder]")) {
        const ph = el.getAttribute("placeholder");
        if (!ph) continue;
        const was = el.value;
        el.value = ph;
        const over = el.scrollWidth - el.clientWidth;
        el.value = was;
        // A textarea wraps, so only a single-line field can cut sideways.
        if (el.tagName === "INPUT" && over > 1) out.push([ph, over]);
      }
      return out;
    });
    checked++;
    ok(cut.length === 0,
       `${u} at 390: ${cut.length} placeholder(s) wider than the field — ` +
       `"${(cut[0] || [""])[0]}" overflows by ${(cut[0] || [0, 0])[1]}px. A hint ` +
       `a reader cannot read is worse than no hint, and it is in the one ` +
       `control these pages exist to be.`);
  }
  await page.setViewportSize({ width: 1280, height: 900 });

  // ── a divider with nothing on the other side of it ─────────────────
  //
  // A separator belongs to the RELATIONSHIP, not to the element, and the
  // index hero's rule had been written as a property of the head. On the
  // 404 — whose drawing is the entire body — that shipped as a hairline
  // across the column followed by two hundred and seventy pixels of nothing
  // above the footer, on the one page a reader reaches having already failed
  // to find something. No count sees an empty band, and no check reads a
  // divider for what is on the other side of it.
  for (const u of ["/404", "/", "/countries", "/map"]) {
    await page.goto(base + u, { waitUntil: "load" });
    const bad = await page.evaluate(() => {
      const out = [];
      document.querySelectorAll("main > *").forEach((e) => {
        if (e.nextElementSibling) return;
        const c = getComputedStyle(e);
        // A DIVIDER, NOT A BOX. The first version asked only whether a bottom
        // border existed, and /map's `.maplist` is a bordered panel whose
        // fourth side is not a separator from anything — the check was
        // pinning a shape where the promise is "a rule with nothing on the
        // other side of it". A divider is a bottom edge and three bare ones.
        const box = ["Top", "Left", "Right"]
          .some((k) => parseFloat(c["border" + k + "Width"]) > 0);
        if (!box && parseFloat(c.borderBottomWidth) > 0) {
          out.push(e.className || e.tagName);
        }
      });
      return out;
    });
    ok(bad.length === 0,
       `${u}: the last thing in main draws a bottom rule with nothing under ` +
       `it — ${bad.join(", ")}`);
  }

  // ── a macro region has to look like one ────────────────────────────
  //
  // A macro region is the only grouping in this atlas with real polygons
  // behind it: a region is a set of destinations with no boundary and is
  // drawn as those, but the Nordics IS five whole countries and Natural
  // Earth has all five. It was the last geographic family with no geography
  // — a headline and a grid of cards.
  //
  // The first render drew the members in the same grey as the rest of
  // Europe: `.macromap .countries path.here` and `.minimap.arched .countries
  // path` are both specificity (0,3,1) and the second is further down the
  // file, so `fill: none` won and the map of the Nordics had the Nordics
  // indistinguishable — while the caption said "filled". That is the second
  // specificity collision in three commits rendering as "the thing simply is
  // not there", and neither is visible in any count.
  for (const u of ["/discover/nordic", "/discover/baltic", "/discover/alpine-central"]) {
    await page.goto(base + u, { waitUntil: "load" });
    const m = await page.evaluate(() => {
      const fig = document.querySelector("figure.macromap");
      if (!fig) return null;
      const here = fig.querySelector(".countries path.here");
      const ctx = fig.querySelector(".context path");
      if (!here) return { members: 0 };
      return { members: fig.querySelectorAll(".countries path.here").length,
               fill: getComputedStyle(here).fill,
               ctxFill: ctx ? getComputedStyle(ctx).fill : "none",
               names: fig.querySelectorAll("text.mmlabel").length };
    });
    ok(m !== null, `${u}: the macro region draws no map`);
    if (!m) continue;
    ok(m.members >= 2, `${u}: the map fills ${m.members} member countries`);
    ok(m.fill !== "none" && !/rgba\(0, 0, 0, 0\)/.test(m.fill),
       `${u}: the member countries are not filled (${m.fill}). A map of a ` +
       "region on which the region is not distinguishable is a map of Europe.");
    ok(m.fill !== m.ctxFill,
       `${u}: the members are painted the same as everything else`);
    ok(m.names >= 1, `${u}: no member country is named on the map`);
  }

  // ── enlarging the type broke the rule that placed it ───────────────
  //
  // Labels are positioned at build time against boxes measured at 11 units,
  // and the phone rule draws a sparse map's names at 26 so they resolve into
  // glyphs at all. Nothing re-ran the collision pass at the new size.
  // Measured across every page that draws a labelled map, at 390px:
  //
  //     434 overlapping pairs on 275 of 815 pages
  //     "Hallstatt" through "Berchtesgaden" by 49px
  //     "Andorra la Vella" through "Madriu-Perafita-Claror" by 91px
  //
  // Found by LOOKING — a contact sheet at phone width — after a commit whose
  // own measurements (label size in CSS pixels) were all green. Size and
  // arrangement are different questions and only one of them was tested.
  //
  // The build now re-tests every box at the phone's scale and marks the ones
  // that lose `wide-only`: 30% of labels are not drawn on a narrow screen,
  // and every one of them keeps its dot, its <title> and its row below.
  await page.setViewportSize({ width: 390, height: 800 });
  for (const u of ["/europe/andorra/the-valleys/andorra-la-vella",
                   "/europe/austria/salzburg-and-the-lakes/salzburg",
                   "/europe/austria/vienna-and-the-east/vienna",
                   "/journeys/the-alpine-grand-tour", "/events/oct",
                   "/europe/austria"]) {
    await page.goto(base + u, { waitUntil: "load" });
    const clashes = await page.evaluate(() => {
      const out = [];
      for (const svg of document.querySelectorAll("figure.minimap svg")) {
        const ls = [...svg.querySelectorAll("text.minilabel")]
          .filter((t) => getComputedStyle(t).display !== "none")
          .map((t) => ({ t: t.textContent.trim(), r: t.getBoundingClientRect() }));
        for (let i = 0; i < ls.length; i++) {
          for (let j = i + 1; j < ls.length; j++) {
            const a = ls[i].r, c = ls[j].r;
            if (Math.min(a.right, c.right) - Math.max(a.left, c.left) > 1 &&
                Math.min(a.bottom, c.bottom) - Math.max(a.top, c.top) > 1) {
              out.push(`"${ls[i].t}" over "${ls[j].t}"`);
            }
          }
        }
      }
      return out;
    });
    ok(clashes.length === 0,
       `${u} at 390px: ${clashes.length} map labels overlap — ` +
       clashes.slice(0, 2).join(", "));
  }
  await page.setViewportSize({ width: 1280, height: 900 });

  // ── the door exists in both colour-scheme preferences ──────────────
  //
  // "Light wall, dark opening" is the whole reading of the aperture: a map
  // figure paints no background so the corners outside the arch show the
  // page through. Measured as the contrast between the page those corners
  // reveal and the ground inside the opening, on every arched map:
  //
  //     light preference   17.94:1
  //     dark preference     1.03:1
  //
  // In the dark preference the wall is graphite and so is the opening. There
  // is no step and there is no door, on every page that draws one — the
  // site's signature existed in one system setting. It cannot be fixed by
  // darkening the opening either: two near-blacks are always about 1:1, and
  // pure black against the graphite ground measures 1.11.
  //
  // So the door is read the way a real one is when the wall is dark: by its
  // cut edge. This asserts that a reader can see the opening EITHER WAY —
  // by the step from the wall, or by the reveal — in both preferences, and
  // it is the second half that was missing.
  for (const scheme of ["light", "dark"]) {
    const ctx = await browser.newContext({ colorScheme: scheme });
    const pg = await ctx.newPage();
    // AND A DESTINATION IS IN THE LIST NOW. 319 pages, the largest family
    // that draws this aperture, and the one where the ground under the crown
    // is land rather than sea — which is the case the declared measurement
    // cannot see.
    for (const u of ["/europe/austria", "/europe/austria/tyrol",
                     "/europe/france/alps-and-east/chamonix",
                     "/journeys/the-alpine-grand-tour", "/beyond-the-obvious",
                     "/events/oct"]) {
      await pg.goto(base + u, { waitUntil: "load" });
      const m = await pg.evaluate(() => {
        // color(srgb r g b / a) gives 0..1 channels, rgb() gives 0..255.
        const parse = (s) => {
          const n = (s.match(/[\d.]+/g) || [0, 0, 0]).map(Number);
          const k = /^color\(/.test(s) ? 255 : 1;
          return [n[0] * k, n[1] * k, n[2] * k, n.length > 3 ? n[3] : 1];
        };
        const fig = document.querySelector("figure.minimap.arched");
        if (!fig) return null;
        const ground = parse(getComputedStyle(fig.querySelector(".archground")).fill);
        const edge = fig.querySelector(".archedge");
        let el = fig.parentElement, bg = "rgba(0, 0, 0, 0)";
        while (el && /rgba\(0, 0, 0, 0\)/.test(bg)) {
          bg = getComputedStyle(el).backgroundColor; el = el.parentElement;
        }
        if (!edge) return { wall: parse(bg), ground, edge: null };
        const e = parse(getComputedStyle(edge).stroke);
        const a = e[3];
        return { wall: parse(bg), ground,
                 edge: [0, 1, 2].map((i) => e[i] * a + ground[i] * (1 - a)) };
      });
      ok(m !== null, `${u}: no arched map to measure in ${scheme}`);
      if (!m) continue;
      const lin = (v) => { const x = v / 255;
        return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
      const rel = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
      const ratio = (a, b) => {
        const [hi, lo] = [rel(a), rel(b)].sort((x, y) => y - x);
        return (hi + 0.05) / (lo + 0.05);
      };
      ok(m.edge !== null, `${u} in ${scheme}: the aperture has no cut edge`);
      // AND THE STEP IS MEASURED ON THE PAINTED PIXEL, because `.archground`
      // is the SEA RECT and on an inland frame a reader never sees it. The
      // declared step on Chamonix is 11.32:1 — limestone against
      // --atlas-sea — and the ground actually under the crown is the land
      // tone, which measures 1.39. Same class as every other contrast claim
      // read off a declaration: the ratio a reader gets is the ratio of the
      // pixel. The door still reads there, on its cut edge at 3.55, which is
      // exactly why this had to be split — the reveal was carrying a plate
      // the step was being credited for.
      // AND THE FIGURE HAS TO BE IN THE PICTURE BEING SAMPLED. This shoots
      // the VIEWPORT and then reads pixels at the figure's own box, and
      // nothing checked that the two overlap: on /events/oct the arch sits
      // at y=750 in a 720-tall viewport, so every sample fell off the bottom
      // of the canvas, `getImageData` handed back transparent black for both
      // points, and the check reported 1.12:1 — a red run measuring nothing,
      // which is the green-run-that-stopped-counting failure with the sign
      // flipped. It surfaced when an overture's h1 grew and pushed the month
      // map below the fold: the drawing never changed.
      //
      // Scroll it into view, then shoot, then read the box — in that order,
      // because the box is read page-side after the screenshot and a rect
      // taken before a scroll describes a different picture.
      //
      // A QUARTER DOWN, NOT CENTRED. `scrollIntoView({block:"center"})` puts
      // the figure's MIDDLE at the middle of the viewport, and the crown is
      // what this measures: on /beyond-the-obvious, whose arch is taller
      // than the viewport, that put its top at y=-81 and the sampler read
      // off the top of the canvas instead of off the bottom — the same fault
      // in the other direction, and it reported 2.98:1 against a real 17.37.
      // A quarter down clears the sticky masthead and leaves the crown and
      // the sixteen pixels under it inside the shot at any figure height.
      await pg.evaluate(() => {
        const f = document.querySelector("figure.minimap.arched");
        if (!f) return;
        window.scrollBy(0, f.getBoundingClientRect().top
                           - Math.round(innerHeight * 0.25));
      });
      const shot = (await pg.screenshot()).toString("base64");
      const px = await pg.evaluate(async (d) => {
        const fig = document.querySelector("figure.minimap.arched svg");
        if (!fig) return null;
        const b = fig.getBoundingClientRect();
        const img = await new Promise((res) => {
          const i = new Image(); i.onload = () => res(i);
          i.src = "data:image/png;base64," + d;
        });
        const c = document.createElement("canvas");
        c.width = img.width; c.height = img.height;
        const x = c.getContext("2d");
        x.drawImage(img, 0, 0);
        const at = (px2, py) => [...x.getImageData(px2, py, 1, 1).data].slice(0, 3);
        const cx = Math.round(b.x + b.width / 2);
        const top = Math.round(b.y);
        // outside the arch, on the cut, and inside the crown
        const out = at(cx, Math.max(0, top - 6));
        const lin2 = (v) => { const q = v / 255;
          return q <= 0.03928 ? q / 12.92 : Math.pow((q + 0.055) / 1.055, 2.4); };
        const rel2 = (p2) => 0.2126 * lin2(p2[0]) + 0.7152 * lin2(p2[1]) + 0.0722 * lin2(p2[2]);
        const cr2 = (a2, b2) => { const [h, l] = [rel2(a2), rel2(b2)].sort((m, n) => n - m);
          return (h + 0.05) / (l + 0.05); };
        // THE DARKEST PIXEL IS THE WRONG ONE IN THE DARK PREFERENCE. The
        // reveal is `--limestone` — the wall's own face laid over the
        // drawing's edge — so on a graphite page it is the LIGHTEST thing at
        // the cut, and a sampler hunting for the darkest reported 1.00:1 on
        // /beyond-the-obvious where the real figure is 17.37. The instrument
        // has to look for the greatest step from the wall, in either
        // direction, which is what a cut edge is.
        let cut = out, best = 0;
        for (let dy = -3; dy <= 8; dy++) {
          const p2 = at(cx, Math.min(c.height - 1, top + dy));
          const v = cr2(p2, out);
          if (v > best) { best = v; cut = p2; }
        }
        return { out, cut, in: at(cx, Math.min(c.height - 1, top + 16)),
                 // The sample window, so a failure can be told apart from a
                 // sampler that missed the figure. A failure message with no
                 // measurement in it cannot be diagnosed.
                 win: [cx, top, c.width, c.height] };
      }, shot);
      if (px) {
        const [sx, sy, sw, sh] = px.win;
        ok(sx >= 0 && sx < sw && sy - 6 >= 0 && sy + 16 < sh,
           `${u} in ${scheme}: the aperture sampler read outside the image — ` +
           `x=${sx} y=${sy} on a ${sw}x${sh} shot. Every sample would come ` +
           `back transparent black and the ratio would be about the canvas, ` +
           `not about the door.`);
      }
      if (px) {
        const stepPx = ratio(px.out, px.in);
        const edgePx = ratio(px.out, px.cut);
        checked++;
        ok(Math.max(stepPx, edgePx) >= 3.0,
           `${u} in ${scheme}: the aperture measures ${stepPx.toFixed(2)}:1 as a ` +
           `step and ${edgePx.toFixed(2)}:1 on its cut edge, ON THE PAINTED ` +
           `PIXEL. One of the two has to clear 3:1 — SC 1.4.11 puts the ` +
           `boundary of a graphical object there, and the declared step is ` +
           `the sea rect a reader does not see on an inland frame`);
      }
      const byWall = ratio(m.wall, m.ground);
      const byEdge = m.edge ? ratio(m.edge, m.ground) : 1;
      ok(Math.max(byWall, byEdge) >= 1.5,
         `${u} in ${scheme}: the opening is invisible — ` +
         `${byWall.toFixed(2)}:1 against the wall it is cut into and ` +
         `${byEdge.toFixed(2)}:1 on its own edge. The door has to be readable ` +
         "in both preferences or it is not a signature.");
    }
    await ctx.close();
  }

  // ── an invisible thing that painted ────────────────────────────────
  //
  // The touch targets added behind each map dot are transparent circles.
  // `.minidot .hit` is specificity (0,2,0) and `.minimap.arched .minidot
  // circle` is (0,3,1), so every one of them painted at 55% limestone:
  // three grey blobs the size of a region across every country map, and
  // lime saucers over the month and quiet maps.
  //
  // 51 static checks, 777 browser checks, 1,334 section assertions and 26
  // invariants were all green. A contact sheet of twelve families found it
  // in one look — rendering finds defects, counting settles proportions —
  // and this is the assertion that would have found it without one.
  for (const u of ["/europe/austria", "/europe/austria/tyrol",
                   "/europe/austria/tyrol/innsbruck",
                   "/journeys/the-alpine-grand-tour", "/events/oct",
                   "/beyond-the-obvious"]) {
    await page.goto(base + u, { waitUntil: "load" });
    const painted = await page.evaluate(() =>
      [...document.querySelectorAll(".minidot .hit")].filter((c) => {
        const f = getComputedStyle(c).fill;
        return f !== "none" && !/rgba\(0, 0, 0, 0\)/.test(f);
      }).length);
    ok(painted === 0,
       `${u}: ${painted} touch target(s) are painting. They are meant to be ` +
       "invisible, and a fill on them is a blob the size of the target.");
  }

  // ── a target too small to hit, and no other way in ─────────────────
  //
  // A .minidot is r=5.5 in a 1000-unit viewBox: 3.9px across on a 358px
  // phone, against WCAG 2.2 AA's 24px floor. The suite already measured the
  // thumb bar's five items and nothing else, so 130 links on
  // /beyond-the-obvious, 12 on a destination page and 345 country shapes on
  // /map went unlooked-at for the life of the map.
  //
  // A geographic dot cannot always be 24px — 130 of them at that size on a
  // 358px map is a solid block — and SC 2.5.8 does not ask it to: a small
  // target is allowed where the same function is available from another
  // control on the SAME page. So this asserts the pair. Each dot's target is
  // as large as it can be without stealing its neighbour's tap (build-time,
  // half the nearest-neighbour distance), and where that is still under 24
  // the destination must be reachable as a text link on the page.
  //
  // Inline text links are exempt from the size floor by SC 2.5.8's own
  // Inline exception, so the equivalent is judged on existing, not on being
  // 24px itself. Measuring it the strict way first said the journey pages
  // had six unreachable stops, which was the measurement being wrong: they
  // are links inside an h3, 22px tall because that is the line.
  for (const u of ["/europe/austria/tyrol/innsbruck", "/europe/austria",
                   "/journeys/the-alpine-grand-tour", "/beyond-the-obvious",
                   "/events/oct", "/europe-in/northern-lights", "/map"]) {
    await page.setViewportSize({ width: 390, height: 800 });
    await page.goto(base + u, { waitUntil: "load" });
    const gaps = await page.evaluate(() => {
      const text = new Set();
      for (const a of document.querySelectorAll("a")) {
        if (a.closest("svg")) continue;
        const h = a.getAttribute("href");
        if (h) text.add(h);
      }
      const out = [];
      for (const a of document.querySelectorAll("svg a.minidot, svg a.cshape")) {
        const r = a.getBoundingClientRect();
        if (Math.min(r.width, r.height) >= 24) continue;
        const h = a.getAttribute("href");
        if (!text.has(h)) out.push(h);
      }
      return out;
    });
    ok(gaps.length === 0,
       `${u}: ${gaps.length} map link(s) under 24px with no text equivalent ` +
       `on the page — ${gaps.slice(0, 2).join(", ")}`);
    // And the marker for the page you are already on is a marker, not a
    // link: a 5.5-unit self-link costs a tap and goes nowhere.
    const self = await page.evaluate((path) =>
      [...document.querySelectorAll("svg a.minidot")]
        .filter((a) => a.getAttribute("href") === path).length, new URL(base + u).pathname);
    ok(self === 0, `${u}: the map links to the page it is drawn on`);
  }
  await page.setViewportSize({ width: 1280, height: 900 });

  // ── a name too small to be a name ──────────────────────────────────
  //
  // `.minilabel` is 11 units in a 1000-unit viewBox, and the browser scales
  // the viewBox to its container — so the size a reader gets is
  // 11 x (width / 1000), not 11px. Measured across four map families before
  // the fix:
  //
  //     viewport   390   480   704   900  1024  1280
  //     label px   3.9   4.9   7.4   9.4  10.7  12.8
  //
  // Under about 860px it is below 9px, which is not small type — it is type
  // that does not resolve into glyphs. Every phone and most tablets were
  // shown names nobody can read, on eight hundred pages, for the life of the
  // embedded map. Every existing check asked whether a label was PLACED and
  // whether it survived the aperture; none asked whether it was legible.
  //
  // There is no non-scaling-text in SVG, so the build marks each map sparse
  // or dense from the names it actually emitted, and the phone rule enlarges
  // the first and drops the second. This asserts the outcome rather than the
  // mechanism: whatever is still drawn at 390px is at least 9px.
  //
  // WHAT COUNTS AS A DOT MAP IS MEASURED, AND THE DOTS ARE COUNTED AS DRAWN.
  // The dot half of this check used to assert that EVERY `figure.minimap`
  // had a `.minidot` — a claim about dot maps written as a claim about maps.
  // The country portrait is a map with no dots at any width, because it is a
  // picture of a shape rather than an instrument, and it turned this red for
  // the right reason and the wrong claim.
  //
  // Rewriting it to compare the DOM across widths would have been WORSE THAN
  // WRONG, it would have been VACUOUS: `.minidot` elements are emitted by the
  // build and the phone rules are CSS, so the two counts can never disagree
  // and the check could not fail at all. The promise is that a map carrying
  // names still SHOWS its dots on a phone, so the dots are counted as the
  // browser draws them — laid out, not display:none, not zero-sized — and
  // only figures that carry names are asked.
  // AND THE CHECK ABOVE ASKS ABOUT ONE CLASS ON A SITE WITH SIX LABEL
  // FAMILIES, WHICH IS HOW TWO MORE OF THEM SHIPPED UNREADABLE.
  //
  // `figure.minimap text.minilabel` is the family the 9px floor was written
  // for. It cannot see `.cname` (the hero's country names), `.seaname` (its
  // five sea names), `.mmlabel` (the nine macro maps), `.peakname`,
  // `.fname` or `.sname`. Measured at 390 before this block existed:
  //
  //     NORTH SEA, MEDITERRANEAN SEA, BLACK SEA, TYRRHENIAN SEA,
  //     BAY OF BISCAY                            5px, on the homepage
  //     Denmark, Finland, Iceland, Greece, ...    6px, on nine macro pages
  //
  // The hero's country names come off below 44rem exactly as designed and
  // the water labels sat in `.lyr-water-labels`, a second layer the rule
  // never named; `.mmlabel` was written directly beneath
  // `.countrymap .rlabel text`, which takes `calc(15px / var(--z))`, and did
  // not take it. *A rule that exists is not a rule that is inherited*, for
  // the third and fourth time in this stylesheet.
  //
  // SO THE PROMISE IS ASSERTED ON EVERY `<text>` A MAP DRAWS, whatever its
  // class: if a reader can see it at 390 it resolves into glyphs. The
  // instrument is the browser's own laid-out box rather than a font-size,
  // because a font-size in an SVG is in user units and the whole family of
  // defects is that those are not pixels.
  const LABELFAM_PAGES = ["/", "/map", "/discover", "/discover/nordic",
                          "/discover/mediterranean", "/countries", "/journeys",
                          "/themes/mountain-europe", "/interests/mountains",
                          "/europe/austria", "/europe/austria/tyrol",
                          "/europe/austria/tyrol/innsbruck",
                          "/journeys/the-alpine-grand-tour",
                          "/europe-in/northern-lights", "/beyond-the-obvious"];
  {
    await page.setViewportSize({ width: 390, height: 844 });
    let examined = 0;
    for (const u of LABELFAM_PAGES) {
      await page.goto(base + u, { waitUntil: "load" });
      const r = await page.evaluate(() => {
        let n = 0; const bad = [];
        for (const t of document.querySelectorAll("svg text")) {
          const st = getComputedStyle(t);
          if (st.display === "none" || st.visibility === "hidden") continue;
          const b = t.getBoundingClientRect();
          if (!b.width || !b.height) continue;
          n++;
          if (b.height < 9) bad.push(`${(t.getAttribute("class") || "(none)")} ` +
                                     `"${t.textContent.trim().slice(0, 20)}" ${b.height.toFixed(1)}px`);
        }
        return { n, bad };
      });
      examined += r.n;
      ok(r.bad.length === 0,
         `${u} at 390 draws ${r.bad.length} map label(s) under 9px — type that ` +
         `does not resolve into glyphs: ${r.bad.slice(0, 4).join("; ")}`);
    }
    // A check reading zero looks exactly like a healthy one in the column of
    // counts, which this repository has now found twice.
    ok(examined >= 20,
       `the label-legibility sweep laid out only ${examined} SVG text elements ` +
       `across ${LABELFAM_PAGES.length} pages — it has stopped finding them.`);
  }

  const MAPWIDTH_PAGES = ["/europe/austria/tyrol/innsbruck", "/europe/austria",
                          "/europe/austria/tyrol", "/journeys/the-alpine-grand-tour",
                          "/europe-in/northern-lights", "/events/oct",
                          "/beyond-the-obvious"];
  for (const w of [390, 480]) {
    await page.setViewportSize({ width: w, height: 800 });
    for (const u of MAPWIDTH_PAGES) {
      await page.goto(base + u, { waitUntil: "load" });
      const small = await page.evaluate(() => {
        const bad = [];
        for (const t of document.querySelectorAll("figure.minimap text.minilabel")) {
          const st = getComputedStyle(t);
          if (st.display === "none" || st.visibility === "hidden") continue;
          const svg = t.closest("svg");
          const vw = Number(svg.getAttribute("viewBox").split(/\s+/)[2]);
          const k = svg.getBoundingClientRect().width / vw;
          const px = parseFloat(st.fontSize) * k;
          if (px < 9) bad.push({ t: t.textContent.trim(), px: +px.toFixed(1) });
        }
        return bad;
      });
      ok(small.length === 0,
         `${u} at ${w}px draws ${small.length} map label(s) below 9px — ` +
         small.slice(0, 3).map((b) => `"${b.t}" at ${b.px}px`).join(", "));
      // And a map that dropped its names must not have dropped its dots:
      // the names live in the list under the figure, the dots are the map.
      const lost = await page.evaluate(() =>
        [...document.querySelectorAll("figure.minimap svg")]
          .filter((s) => s.querySelectorAll(".minilabel").length > 0)
          .filter((s) => ![...s.querySelectorAll(".minidot circle")].some((d) => {
            const st = getComputedStyle(d);
            if (st.display === "none" || st.visibility === "hidden") return false;
            const b = d.getBoundingClientRect();
            return b.width > 0 && b.height > 0;
          })).length);
      ok(lost === 0,
         `${u} at ${w}px has ${lost} named map(s) drawing no dots`);
    }
  }
  await page.setViewportSize({ width: 1280, height: 900 });

  // ── a heading is not cut in half ───────────────────────────────────
  //
  // A WORD BROKEN MID-WORD IS A RENDERING FAULT, AND IT HAS HAPPENED TWICE.
  // `overflow-wrap: break-word` is right and stays — a headline running off
  // the right edge is worse, and hyphenation is refused because an English
  // dictionary breaks Norwegian compounds wrongly. What is wrong when it
  // fires is the SIZE or the MEASURE.
  //
  // First: `.overture h1` is held at 14ch, which is a character count wearing
  // a length's clothes — a `ch` is the width of a zero — so Elbphilharmonie
  // measured 214px inside a 210px box and dropped its last glyph onto a line
  // of its own, on four pages. Then the fix for that was capped with
  // `min(100%, min-content)` to stop a 320px screen scrolling, which is
  // INVALID CSS: an intrinsic keyword is not allowed inside a math function,
  // so the declaration was dropped, min-width computed to 0 and the four
  // broke again. Nothing saw it — the overflow sweep passed BECAUSE the fix
  // was off — and it was found by looking at a contact sheet.
  //
  // A HYPHENATED WORD BREAKING AT ITS HYPHEN IS CORRECT TYPOGRAPHY, not a
  // fault: the break is where the author put one. Only a break inside an
  // unbroken run of letters counts.
  {
    const { ALL } = require("./lib/families.js");
    const CUT = [];
    let looked = 0;
    for (const w of [320, 390]) {
      await page.setViewportSize({ width: w, height: 844 });
      for (const [name, u] of ALL) {
        const res = await page.goto(base + u, { waitUntil: "load" });
        if (!res || res.status() !== 200) continue;
        looked++;
        const bad = await page.evaluate(() => {
          const out = [];
          const rg = document.createRange();
          for (const h of document.querySelectorAll("main :is(h1,h2,h3)")) {
            for (const n of h.childNodes) {
              if (n.nodeType !== 3) continue;
              let i = 0;
              for (const word of n.textContent.split(/(\s+)/)) {
                if (word.trim() && !/[-‐‑]/.test(word.slice(1, -1))) {
                  rg.setStart(n, i); rg.setEnd(n, i + word.length);
                  const tops = new Set([...rg.getClientRects()]
                    .filter((r) => r.width > 0).map((r) => Math.round(r.top)));
                  if (tops.size > 1) out.push(word);
                }
                i += word.length;
              }
            }
          }
          return out;
        });
        for (const word of bad) CUT.push(`${name} at ${w}: "${word}"`);
      }
    }
    await page.setViewportSize({ width: 1280, height: 900 });
    ok(CUT.length === 0,
       `${CUT.length} heading word(s) cut in half: ${CUT.slice(0, 6).join(", ")}. `
       + "overflow-wrap is right; the size or the measure is what is wrong when "
       + "it fires.");
    ok(looked >= 80,
       `only ${looked} pages were examined for a cut heading across two widths `
       + "— the family list or the h1 selector has stopped matching");
  }

  // ── a country on the instrument is drawn, not merely declared ──────
  //
  // `docs/palette.json` declares --map-context against --map-sea at 1.35
  // with the reason written out — "a country outside the subject is still
  // drawn; 1.24 is not quiet, it is absent" — and `checks.py` recomputes it
  // from the token hexes, so it has been green since it was written. The
  // DATA-CUT FADE paints on top of both and nothing measured the result.
  //
  // A SEPARATION BETWEEN TWO TOKENS SAYS NOTHING ABOUT WHETHER EITHER IS
  // PAINTED. That sentence is already in this repository, about /discover
  // drawing fifty countries with `fill: none` under a rule that declared
  // 1.8. This is the same fault through a different mechanism: the tokens
  // were right and an overlay put Armenia at 1.06 against the sea.
  //
  // Sampled inside each real polygon, because a bounding-box centre is in
  // the Adriatic for Italy and in the Aegean for Greece — a bounding box is
  // not a country, which this atlas has now learned three times.
  {
    /* ON /map, WHERE THE CLAIM IS SHARPEST. /discover draws the same fade
       and took the same cap, but its countries are context rather than
       links — the page is a filter, not a navigator — so the one page where
       every country is a door is the one asserted. */
    for (const u of ["/map"]) {
      await page.setViewportSize({ width: 1280, height: 1400 });
      await page.goto(base + u, { waitUntil: "networkidle" });
      await page.waitForTimeout(400);
      const shot = (await page.screenshot({ fullPage: true })).toString("base64");
      const m = await page.evaluate(async (d) => {
        const img = await new Promise((r) => {
          const i = new Image(); i.onload = () => r(i); i.src = "data:image/png;base64," + d; });
        const c = document.createElement("canvas");
        c.width = img.width; c.height = img.height;
        c.getContext("2d").drawImage(img, 0, 0);
        const D = c.getContext("2d").getImageData(0, 0, img.width, img.height);
        const dpr = D.width / innerWidth;
        /* AND THE FLOOR IS THE ONE THE PALETTE IN FRONT OF IT DECLARES.
         * 1.35 is the DARK map's: `--map-context` against `--map-sea`, on a
         * near-black ground where a country outside the subject is either
         * lit or absent. The light map answers the same question a
         * different way and says so in `docs/palette.json` — its only
         * declared separations are the BORDER ink against the land (3.39)
         * and against the water (4.02), because a printed atlas is stone on
         * pale water and the COASTLINE is what separates them. Land against
         * water is 1.18 there by design, and asserting 1.35 on it would be
         * this check measuring one cartography with the other's number.
         * What it is FOR survives either way: a country has to be drawn
         * rather than absent, so the step is still measured, at the value
         * the drawing's own palette sets. */
        const FLOOR = document.querySelector(".europemap.atlas") ? 1.15 : 1.35;
        const lum = (r, g, bl) => { const f = (v) => { v /= 255;
          return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
          return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(bl); };
        const at = (x, y) => { const i = ((Math.round(y) * D.width) + Math.round(x)) * 4;
          return lum(D.data[i], D.data[i + 1], D.data[i + 2]); };
        const ratio = (a, b) => { const [h, l] = [a, b].sort((x, y) => y - x);
          return (h + 0.05) / (l + 0.05); };
        const svg = document.querySelector(".europemap svg") || document.querySelector("svg.europemap");
        if (!svg) return null;
        const sr = svg.getBoundingClientRect();
        /* Mid-Atlantic: sea on every frame this atlas draws. */
        const sea = at((sr.left + sr.width * 0.12) * dpr, (sr.top + scrollY + sr.height * 0.55) * dpr);
        const pt = svg.createSVGPoint();
        const bad = []; let seen = 0;
        for (const s of document.querySelectorAll(".europemap .cshape")) {
          const path = s.tagName === "path" ? s : s.querySelector("path");
          if (!path) continue;
          const bb = path.getBBox();
          if (bb.width < 2 || bb.height < 2) continue;
          let inside = null;
          for (let gy = 1; gy < 8 && !inside; gy++)
            for (let gx = 1; gx < 8 && !inside; gx++) {
              pt.x = bb.x + bb.width * gx / 8; pt.y = bb.y + bb.height * gy / 8;
              if (path.isPointInFill(pt)) inside = [pt.x, pt.y];
            }
          if (!inside) continue;
          seen++;
          const t = path.getScreenCTM();
          const sx = t.a * inside[0] + t.c * inside[1] + t.e;
          const sy = t.b * inside[0] + t.d * inside[1] + t.f;
          const r = ratio(at(sx * dpr, (sy + scrollY) * dpr), sea);
          if (r < FLOOR) {
            const ti = s.querySelector("title");
            bad.push(`${ti ? ti.textContent.trim() : "?"} ${r.toFixed(2)}`);
          }
        }
        return { seen, bad };
      }, shot);
      ok(m !== null, `${u}: no instrument map to measure`);
      if (!m) continue;
      ok(m.bad.length === 0,
         `${u}: ${m.bad.length} country/countries painted under the floor that `
         + `docs/palette.json declares against the sea — ${m.bad.join(", ")}. `
         + "The tokens clear it; the data-cut fade paints on top of them, and a "
         + "separation between two tokens says nothing about whether either is "
         + "painted.");
      ok(m.seen >= 40,
         `${u}: only ${m.seen} countries were sampled — the shapes or their `
         + "fills have been renamed and this check is reporting on nothing");
    }
    await page.setViewportSize({ width: 1280, height: 900 });
  }

  // ── a control a reader can see the edge of ─────────────────────────
  //
  // THE HOMEPAGE'S ASK FIELD PAINTED rgb(247,246,243) ON A BODY OF
  // rgb(247,246,243), with a transparent border. Present, labelled,
  // keyboard-reachable, correctly sized, and no edge at all — the one
  // control that page exists to be. It was right while the form sat INSIDE
  // the hero, where paper on graphite is a field; it moved out to the light
  // band and kept the fill. Its own LABEL had made the same move and gone
  // limestone on limestone at 1.00:1, and that half was found and fixed
  // while the fill was left behind.
  //
  // Nothing could see it. A field has no text of its own, so every contrast
  // assertion here had nothing to measure; the dead-rule scan is happy
  // because the rule applies and does change something; and at thumbnail
  // size a pale field on a pale page looks like a field.
  //
  // WCAG 1.4.11 puts a user-interface component's boundary at 3:1, and the
  // only honest way to ask is the pixels: a control may be bounded by a
  // border, a fill, an underline or a shadow, and a declaration check would
  // have to know all four. So the strip that crosses each edge is read, and
  // the question is whether ANY step along it reaches 3:1.
  {
    const FORMS = ["/", "/search", "/plan", "/discover", "/my-europe"];
    let seen = 0;
    for (const u of FORMS) {
      await page.goto(base + u, { waitUntil: "networkidle" });
      await page.waitForTimeout(200);
      const shot = (await page.screenshot()).toString("base64");
      const weak = await page.evaluate(async (d) => {
        const img = await new Promise((res) => {
          const i = new Image(); i.onload = () => res(i); i.src = "data:image/png;base64," + d;
        });
        const c = document.createElement("canvas");
        c.width = img.width; c.height = img.height;
        c.getContext("2d").drawImage(img, 0, 0);
        const D = c.getContext("2d").getImageData(0, 0, img.width, img.height);
        const dpr = D.width / innerWidth;
        const lum = (r, g, b) => { const f = (v) => { v /= 255;
          return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
          return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
        const at = (x, y) => { const i = ((y * D.width) + x) * 4;
          return lum(D.data[i], D.data[i + 1], D.data[i + 2]); };
        const step = (a, b) => { const [hi, lo] = [a, b].sort((x, y) => y - x);
          return (hi + 0.05) / (lo + 0.05); };
        const out = [];
        for (const e of document.querySelectorAll("input:not([type=hidden]), textarea, select")) {
          const r = e.getBoundingClientRect();
          if (r.width < 8 || r.height < 8) continue;
          if (getComputedStyle(e).visibility === "hidden") continue;
          if (r.top < 0 || r.bottom > innerHeight || r.left < 6 || r.right > innerWidth - 6) continue;
          /* Four crossings: left, right, top, bottom. A control bounded on
             one side only — a ruled field — passes, because that is a real
             and deliberate boundary and a reader sees it. */
          const mx = Math.round((r.left + r.width / 2) * dpr);
          const my = Math.round((r.top + r.height / 2) * dpr);
          const cross = [
            [Math.round((r.left - 5) * dpr), my, Math.round((r.left + 3) * dpr), my],
            [Math.round((r.right + 5) * dpr), my, Math.round((r.right - 3) * dpr), my],
            [mx, Math.round((r.top - 5) * dpr), mx, Math.round((r.top + 3) * dpr)],
            [mx, Math.round((r.bottom + 5) * dpr), mx, Math.round((r.bottom - 3) * dpr)],
          ];
          let best = 1;
          for (const [ox, oy, ix, iy] of cross) {
            if (ox < 0 || oy < 0 || ix < 0 || iy < 0
                || ox >= D.width || ix >= D.width || oy >= D.height || iy >= D.height) continue;
            /* The strongest pixel anywhere across the edge, not just the two
               ends: a 2px rule sits between them. */
            const ax = Math.sign(ix - ox), ay = Math.sign(iy - oy);
            const n = Math.max(Math.abs(ix - ox), Math.abs(iy - oy));
            const outside = at(ox, oy);
            for (let k = 0; k <= n; k++)
              best = Math.max(best, step(outside, at(ox + ax * k, oy + ay * k)));
          }
          if (best < 3.0)
            out.push(`${e.tagName.toLowerCase()}${e.id ? "#" + e.id : ""} at ${best.toFixed(2)}:1`);
        }
        return out;
      }, shot);
      seen++;
      ok(weak.length === 0,
         `${u}: ${weak.length} form control(s) whose edge does not reach 3:1 `
         + `against what is behind it — ${weak.join(", ")}. A field a reader `
         + `cannot see the edge of is the homepage's own ask box, which `
         + `painted the page's exact colour with a transparent border.`);
    }
    ok(seen === FORMS.length,
       `only ${seen} of ${FORMS.length} form pages were examined`);
  }

  // ── a country plate names its OWN mountain ─────────────────────────
  //
  // A SINGLE TRIANGLE WITH A HEIGHT READS AS THIS COUNTRY'S MOUNTAIN, and
  // thirty of the fifty portraits named somebody else's. `summit_points`
  // returns the highest peaks in FRAME and a country plate frames its
  // neighbours, so the tallest thing on screen is usually across the border:
  // Austria named Triglav, which is Slovenian, Switzerland named Mont Blanc,
  // Germany named Finsteraarhorn, Greece named Musala, and Croatia named
  // three peaks of which none was Croatian.
  //
  // THE MODEL CANNOT CHECK ITSELF. The build decides this with a ray-cast
  // against the same rings it draws, so a static check re-running it would
  // only ever agree — the instrument fault this repository already records
  // three times. `isPointInFill` is the browser asking the rendered path,
  // which is a different implementation of the same question, and it is what
  // the one-off measurement behind the country-name rule used.
  //
  // The subject's own name is asserted here too, for the same reason and with
  // the same instrument: nine portraits once set it entirely on a neighbour.
  {
    const PLATES = ["/europe/austria", "/europe/switzerland", "/europe/germany",
                    "/europe/croatia", "/europe/greece", "/europe/slovakia",
                    "/europe/hungary", "/europe/france", "/europe/italy",
                    "/europe/norway", "/europe/portugal", "/europe/turkiye"];
    let checked = 0;
    for (const u of PLATES) {
      await page.goto(base + u, { waitUntil: "load" });
      const off = await page.evaluate(() => {
        const svg = document.querySelector("figure.minimap.portrait svg");
        if (!svg) return null;
        const here = svg.querySelector("path.here") || svg.querySelector(".countries path.here");
        if (!here) return null;
        /* A MARK'S POINT IS WHERE IT POINTS. A peak is drawn as a triangle
           AROUND its coordinate, so the bounding box's centre is a little
           north of the summit itself — and on Sněžka, whose summit is
           literally the Czech-Polish frontier, that 0.8 units is the whole
           question. Either the box's middle or its foot being on the country
           is enough; a peak that is actually in the next country, like
           Triglav on Austria's plate, is sixty units away and fails both. */
        const inside = (el) => {
          const b = el.getBBox();
          const p = svg.createSVGPoint();
          p.x = b.x + b.width / 2;
          for (const y of [b.y + b.height / 2, b.y + b.height]) {
            p.y = y;
            if (here.isPointInFill(p)) return true;
          }
          return false;
        };
        const bad = [];
        /* THE MARK, NOT THE LABEL. A peak's name is set beside its triangle,
           and a printed atlas lets a name run over a neighbour — that is the
           country name's own rule. What must be on this country is the
           TRIANGLE. Testing the label's box instead reported Zugspitze off
           Germany, which is where the build had just correctly put it. */
        for (const t of svg.querySelectorAll("path.peak"))
          if (!inside(t)) bad.push(`peak "${(t.querySelector("title") || {}).textContent || "?"}"`);
        for (const t of svg.querySelectorAll("text.cname"))
          if (!inside(t)) bad.push(`name "${t.textContent.trim()}"`);
        return bad;
      });
      if (off === null) continue;
      checked++;
      ok(off.length === 0,
         `${u} sets ${off.length} label(s) off its own country: ${off.join(", ")}`);
    }
    ok(checked >= 10,
       `only ${checked} of ${PLATES.length} country portraits were examined — `
       + "the plate or its subject path has been renamed and this check has "
       + "stopped looking at anything");
  }

  // ── the signature does not eat the content ─────────────────────────
  //
  // THE APERTURE WAS DELETING THE NAMES IT EXISTS TO FRAME.
  //
  // Labels were placed with a rule that tested the RECTANGLE — put the name
  // on the other side of the dot if it runs off the right-hand edge — and
  // the drawing is clipped by the ARCH. rx = span/2, ry = 34% of the height,
  // so the top corners are removed entirely and a name can sit well inside
  // the viewBox and be sliced by the curve above it.
  //
  // Measured across all 815 pages that draw a labelled map: 5,184 labels, of
  // which 184 on 142 pages had a corner outside the aperture and FOURTEEN
  // were drawn entirely inside the removed corner. "Dürnstein & the Wachau"
  // did not exist on the Hallstatt map, with nothing anywhere saying a place
  // was missing. A rectangle check reported those same pages as at most 0.7%
  // over: the instrument was measuring the wrong boundary.
  //
  // This is the browser's own getBBox, which is the only thing that knows
  // how wide a name really is — pages.py places from a fitted model, and a
  // static check re-running that model would only ever agree with itself.
  // The three emitters are covered on purpose: pointsmap (a journey),
  // minimap (a destination and its neighbours) and the country map.
  for (const u of ["/journeys/the-alpine-grand-tour",
                   "/europe/austria/salzburg-and-the-lakes/hallstatt",
                   "/europe/austria",
                   "/events/oct",
                   "/europe/spain/andalusia/cadiz",
                   "/beyond-the-obvious"]) {
    await page.goto(base + u, { waitUntil: "load" });
    const cut = await page.evaluate(() => {
      const bad = [];
      for (const svg of document.querySelectorAll("svg[viewBox]")) {
        const [vx, vy, vw, vh] = svg.getAttribute("viewBox").split(/\s+/).map(Number);
        if (!svg.querySelector("text.minilabel")) continue;
        const rise = Math.min(vh * 0.34, vw * 0.5);
        const inside = (x, y) => {
          if (x < vx || x > vx + vw || y > vy + vh) return false;
          if (y >= vy + rise) return true;
          const dx = (x - (vx + vw / 2)) / (vw / 2), dy = (y - (vy + rise)) / rise;
          return dx * dx + dy * dy <= 1;
        };
        for (const t of svg.querySelectorAll("text.minilabel")) {
          let b; try { b = t.getBBox(); } catch (e) { continue; }
          if (!b.width) continue;
          const corners = [[b.x, b.y], [b.x + b.width, b.y],
                           [b.x, b.y + b.height], [b.x + b.width, b.y + b.height]];
          const out = corners.filter((c) => !inside(c[0], c[1])).length;
          if (out) bad.push({ txt: t.textContent.trim(), out });
        }
      }
      return bad;
    });
    ok(cut.length === 0,
       `${u}: ${cut.length} map label(s) cut by the aperture — ` +
       cut.slice(0, 3).map((c) => `"${c.txt}" (${c.out}/4 corners)`).join(", "));
    // And a map that solved the clipping by drawing no names at all has
    // solved nothing: every map with dots keeps at least one label.
    const cover = await page.evaluate(() => {
      const o = [];
      for (const svg of document.querySelectorAll("svg[viewBox]")) {
        const d = svg.querySelectorAll(".minidot").length;
        if (d) o.push([d, svg.querySelectorAll("text.minilabel").length]);
      }
      return o;
    });
    ok(cover.every((c) => c[1] > 0),
       `${u}: a map draws ${cover.filter((c) => !c[1]).length} dot cluster(s) ` +
       "with no name on any of them");
  }

  // ── arrival: the destination page's own grammar ────────────────────
  //
  // A destination page is about being SOMEWHERE, and two things carry that.
  //
  // First, WHAT YOU WOULD DO IS BESIDE THE NAME. The three reasons a person
  // would go used to sit below the head in a three-across band, and the view
  // of where the place is sat below THAT — at y=840 on a 900-tall screen. So
  // the first screen of the page carried a name, a sentence, four chips and
  // 620 pixels of empty limestone. Asserted as position rather than as
  // markup: the reasons start above the view, and the view starts inside the
  // first screen.
  //
  // Second, THE LOCAL VIEW PAINTS ITS LAND. Every other map on this site
  // draws land as outline only, which is right at continent and country
  // scale where adjacent fills merge into one mass and the borders are the
  // information. At 600 km across it is wrong: the Aegean was the same
  // near-black as the Peloponnese, so a page whose whole promise is "you are
  // here" showed an island nowhere. The first attempt at the fix LOST A
  // SPECIFICITY FIGHT — `.minimap.arched .countries path` is (0,3,1), not
  // the (0,2,1) it looks like — and rendered as the thing simply not being
  // there, which is the third time in this stylesheet. So this measures the
  // painted colours, not the rule.
  for (const u of ["/europe/austria/tyrol/innsbruck",
                   "/europe/greece/athens-and-the-peloponnese/hydra"]) {
    await page.goto(base + u, { waitUntil: "load" });
    const a = await page.evaluate(() => {
      const top = (e) => (e ? e.getBoundingClientRect().top + scrollY : null);
      const r = document.querySelector(".reasons");
      const v = document.querySelector("figure.minimap");
      const land = document.querySelector(".countries path");
      const sea = document.querySelector(".archground");
      // The place's own sentence, wherever the composition puts it.
      const say = document.querySelector(
        ".ed-arrival-copy p, .arrivalhead .statement, .arrivalhead p");
      const onward = document.querySelector("#onward, [id='onward']");
      const stay = document.querySelector("#stay, [id='stay']");
      return {
        reasons: top(r), view: top(v), say: top(say),
        onward: top(onward), stay: top(stay),
        land: land && getComputedStyle(land).fill,
        sea: sea && getComputedStyle(sea).fill,
      };
    });
    // THE ARGUMENT COMES BEFORE THE TRANSACTION, AND THE VIEW IS NOW IN THE
    // HEAD. This asserted `.arrivalhead .reasons` above `.placeband-map`,
    // which was the order when the view was a band BELOW the head — and the
    // arrival composition puts the map in the opening with the place's name
    // and its own sentence over it, so the reasons follow at 1065 where the
    // drawing starts at 275. That is a deliberate change and this assertion
    // is deliberately weaker for it: it no longer says where the drawing is.
    //
    // What it says instead is the part that was always the point. The
    // place's own sentence — its one-line argument — must be at or above the
    // view rather than below it, so a reader meets what this place IS before
    // they read the instrument; and the reasons must come before anything
    // transactional, which is the order `docs/ux-specification.md` has
    // asserted by id since before the Stay layer existed.
    ok(a.say !== null && a.view !== null && a.say <= a.view + 1,
       `${u}: the place's own sentence is below the view (${a.say} / ` +
       `${a.view}) — a reader meets the instrument before they are told ` +
       `what the place is`);
    for (const [k, what] of [["stay", "the Stay layer"],
                             ["onward", "the onward stops"]])
      if (a[k] !== null)
        ok(a.reasons !== null && a.reasons < a[k],
           `${u}: the reasons are not above ${what} (${a.reasons} / ` +
           `${a[k]}) — the argument has to come before the transaction`);
    ok(a.view !== null && a.view < 900,
       `${u}: the view starts at ${a.view}, below the first screen`);
    ok(a.land && a.land !== "none" && a.land !== a.sea,
       `${u}: the local view paints its land the same as its sea ` +
       `(${a.land} vs ${a.sea})`);
  }

  // ── the Stay layer: a referral a reader can see the edges of ────────
  //
  // The commercial surface, and the one place on this site where somebody
  // else's interest is involved. Four things are asserted in the browser
  // because none of them can be read off the source:
  //
  //   1. NOTHING IS FETCHED FROM THE PROVIDER. The whole section is text and
  //      one anchor, so loading the page must make zero requests off this
  //      origin — no pixel, no script, no availability call. That is what
  //      makes `default-src 'none'` true rather than merely declared, and it
  //      is also the answer to "how does this behave on a slow network":
  //      there is nothing to be slow.
  //   2. THE LINK IS A REAL TARGET AND HAS A REAL NAME. WCAG 2.2 puts the
  //      floor at 24px, and an outbound commercial link that is hard to hit
  //      or unnamed is the worst possible one to get wrong.
  //   3. THE DISCLOSURE IS VISIBLE, NOT MERELY PRESENT. `.askhero label` was
  //      limestone at 76% on graphite and measured 1.00:1 — present,
  //      labelled, keyboard-reachable and invisible. A disclosure is exactly
  //      the element somebody would be accused of hiding, so it is measured
  //      against what the browser paints, in both preferences.
  //   4. IT SITS AFTER THE REASONS AND BEFORE THE EXIT. Accommodation
  //      appears where a reader who has decided to come would look for it.
  {
    const u = "/europe/france/alps-and-east/chamonix";
    for (const scheme of ["light", "dark"]) {
      const ctx = await browser.newContext({
        viewport: { width: 1280, height: 900 }, colorScheme: scheme,
      });
      const p2 = await ctx.newPage();
      const offOrigin = [];
      p2.on("request", (rq) => {
        if (!rq.url().startsWith(base) && !rq.url().startsWith("data:")) {
          offOrigin.push(rq.url());
        }
      });
      await p2.goto(base + u, { waitUntil: "load" });
      ok(offOrigin.length === 0,
         `${u} (${scheme}): loading it reaches ${offOrigin.length} off-origin ` +
         `URL(s): ${offOrigin.slice(0, 2).join(", ")}`);
      const a = await p2.evaluate(() => {
        const lum = (c) => {
          const nums = (c.match(/-?\d*\.?\d+/g) || []).map(Number);
          const [r, g, b] = nums.slice(0, 3).map((v) => {
            const x = v > 1 ? v / 255 : v;
            return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
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
        const ratio = (x, y) => {
          const [l1, l2] = [lum(x), lum(y)].sort((m, n) => n - m);
          return (l1 + 0.05) / (l2 + 0.05);
        };
        const stay = document.querySelector("#stay");
        const link = stay && stay.querySelector("a[target=_blank]");
        const disc = stay && stay.querySelector(".staydisc");
        const who = stay && stay.querySelector(".staywho");
        const reasons = document.querySelector(".arrivalhead .reasons");
        const onward = document.querySelector("#onward");
        const r = (el) => (el ? el.getBoundingClientRect() : null);
        const lb = r(link);
        return {
          hasLink: !!link,
          name: link ? link.textContent.trim() : "",
          w: lb && lb.width, h: lb && lb.height,
          disc: disc ? ratio(getComputedStyle(disc).color, bgOf(disc)) : null,
          discSize: disc ? parseFloat(getComputedStyle(disc).fontSize) : null,
          who: who ? ratio(getComputedStyle(who).color, bgOf(who)) : null,
          stayTop: stay ? r(stay).top + p2Scroll() : null,
          reasonsTop: reasons ? r(reasons).top + p2Scroll() : null,
          onwardTop: onward ? r(onward).top + p2Scroll() : null,
        };
        function p2Scroll() { return window.scrollY; }
      });
      ok(a.hasLink, `${u} (${scheme}): the stay section has no outbound link`);
      ok(a.name.length > 8 && !/^(here|link|more)$/i.test(a.name),
         `${u} (${scheme}): the referral's accessible name is "${a.name}"`);
      ok(a.h >= 24 && a.w >= 24,
         `${u} (${scheme}): the referral is ${a.w}x${a.h}, under the 24px floor`);
      ok(a.disc !== null && a.disc >= 4.5,
         `${u} (${scheme}): the affiliate disclosure measures ${a.disc && a.disc.toFixed(2)}:1 ` +
         `at ${a.discSize}px — a disclosure nobody can read is not a disclosure`);
      ok(a.who !== null && a.who >= 4.5,
         `${u} (${scheme}): "who holds the rooms" measures ${a.who && a.who.toFixed(2)}:1`);
      ok(a.reasonsTop < a.stayTop && a.stayTop < a.onwardTop,
         `${u} (${scheme}): stay is not between the reasons and the onward stops ` +
         `(${a.reasonsTop} / ${a.stayTop} / ${a.onwardTop})`);
      await ctx.close();
    }
  }

  // ── the two worlds ─────────────────────────────────────────────────
  //
  // A palette can be correct in a token file and wrong on the page: what
  // matters is what the browser paints after cascade, media query and
  // inheritance. So these read computed colour, not CSS source.
  //
  // The load-bearing claim is that INTELLIGENCE is dark in BOTH colour-scheme
  // preferences. If it went light for a light-mode reader the two worlds
  // would collapse into one and the whole idea would be a theme toggle.
  const LUM = (c) => {
    const n = (c.match(/-?\d*\.?\d+/g) || []).map(Number);
    const scale = /^color\(/.test(c) ? 255 : 1;
    const [r, g, b] = n.slice(0, 3).map((v) => {
      const x = (v * scale) / 255;
      return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const CR = (a, b) => {
    const [h, l] = [LUM(a), LUM(b)].sort((m, n) => n - m);
    return (h + 0.05) / (l + 0.05);
  };
  const worldProbe = () => ({
    world: document.body.dataset.world || "discover",
    accent: document.body.dataset.accent || "",
    bg: getComputedStyle(document.body).backgroundColor,
    door: getComputedStyle(document.body).getPropertyValue("--door").trim(),
    // THE OLD VERSION READ `color` AND NOTHING ELSE, so it asked whether
    // lime was set on TEXT — and lime was never mostly on text. It was on
    // fill: seventeen journey routes, 894 homepage dots, 319 destinations,
    // 172 experiences and every lit country on every region glyph. The
    // property it was actually spent on was the one property this probe did
    // not read. Four properties now, and the whole document, in both worlds.
    limeAnywhere: [...document.querySelectorAll("*")].map((el) => {
      const cs = getComputedStyle(el);
      for (const prop of ["color", "fill", "stroke", "backgroundColor"]) {
        const m = String(cs[prop] || "").match(/\d+/g);
        if (m && m.length >= 3 && Number(m[0]) > 150 && Number(m[1]) > 220 &&
            Number(m[2]) < 130 && !(m.length > 3 && Number(m[3]) === 0)) {
          return el.tagName.toLowerCase() + "." + String(el.getAttribute("class") || "")
                 + " " + prop + "=" + cs[prop];
        }
      }
      return "";
    }).filter(Boolean)[0] || "",
  });

  for (const scheme of ["light", "dark"]) {
    const w = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await w.emulateMedia({ colorScheme: scheme });

    for (const url of ["/map", "/plan", "/my-europe", "/search", "/discover"]) {
      await w.goto(base + url, { waitUntil: "load" });
      const r = await w.evaluate(worldProbe);
      ok(r.world === "intelligence", `${url} is not in the INTELLIGENCE world`);
      ok(LUM(r.bg) < 0.06, `${scheme} ${url}: INTELLIGENCE is not dark (${r.bg})`);
      // The accent is the cobalt family, in both worlds and both
      // preferences. It was electric lime here, asserted by its own hex —
      // which is the fifth assertion in this suite to pin a value rather
      // than a promise. The promise is that INTELLIGENCE has ONE accent, it
      // is readable on the card as well as the ground, and it is not the
      // colour that ended up drawing continents.
      // AND IT WAS PINNED BY ITS LITERAL VALUE, which is the sixth
      // assertion in this suite to protect a number rather than a promise.
      // The promise is that INTELLIGENCE has ONE accent and it is the
      // register's declared one; the register is where that is decided.
      // THE INSTRUMENT'S ACCENT IS COBALT, AND THIS PINNED A HEX FROM
      // BEFORE THE OWNER'S PALETTE. It asserted `pine-air` — the previous
      // system's dark accent — and the brief that replaced it says in as
      // many words that the instrument is "Graphite + Bone + Cobalt". So
      // the check went red for the right event and the wrong claim, which
      // is the shape this repository has now recorded eleven times.
      // Read from the register rather than typed, so a rename moves the
      // assertion with the colour: the promise is that the instrument world
      // carries a COBALT accent and is therefore told apart from DISCOVER,
      // not that it carries one particular rung of that family.
      {
        const cob = Object.entries(PALETTE.tokens)
          .filter(([k]) => /^cobalt(-|$)/.test(k)).map(([, v]) => v.hex);
        ok(cob.some((h) => sameColour(r.door, h)),
           `${scheme} ${url}: the INTELLIGENCE accent is ${r.door}, and the ` +
           `owner's palette gives the instrument cobalt — none of ` +
           `${cob.join(", ")}`);
      }
      ok(!r.limeAnywhere, `${scheme} ${url}: electric lime is painted — ${r.limeAnywhere}`);
    }

    // DISCOVER: three accents, and never the electric one.
    for (const [url, want] of [["/", "structural"], ["/europe/norway", "structural"],
                               ["/stories", "cultural"], ["/events/oct", "cultural"],
                               ["/method", "heritage"], ["/sources", "heritage"]]) {
      await w.goto(base + url, { waitUntil: "load" });
      const r = await w.evaluate(worldProbe);
      ok(r.world === "discover", `${url} should be DISCOVER, is ${r.world}`);
      ok(!r.limeAnywhere, `${scheme} ${url}: electric lime is painted — ${r.limeAnywhere}`);
      if (want === "heritage") ok(r.accent === "heritage", `${url} is not marked heritage`);
      if (want === "cultural") {
        // --door is a custom property, so it comes back as the authored
        // value — a hex — not as the rgb() a computed colour would give.
        // AND THIS ONE TYPED FOUR SPELLINGS OF TWO HEXES. `terracotta-2`
        // moved from #a4491f to #a6573a with the owner's palette and the
        // regex went on naming the old one. The register is the list.
        const terra = Object.entries(PALETTE.tokens)
          .filter(([k]) => /^terracotta(-|$)/.test(k)).map(([, v]) => v.hex);
        ok(terra.some((h) => sameColour(r.door, h)),
           `${scheme} ${url}: the cultural accent is ${r.door}, and it has ` +
           `to be one of the terracotta family — ${terra.join(", ")}`);
      }
    }

    // DISCOVER follows the reader's preference; INTELLIGENCE does not.
    await w.goto(base + "/", { waitUntil: "load" });
    const home = await w.evaluate(worldProbe);
    ok(scheme === "light" ? LUM(home.bg) > 0.7 : LUM(home.bg) < 0.06,
       `${scheme}: DISCOVER did not follow the colour-scheme preference (${home.bg})`);

    // A map is INTELLIGENCE wherever it is embedded — and this pair of
    // assertions had encoded the old IMPLEMENTATION of that promise rather
    // than the promise. They demanded the <figure> carry data-world and paint
    // a dark background, which is what a map was when it was a dark panel
    // sitting on the page. It is now an aperture cut INTO the page: the
    // figure keeps the page's own world so its caption is legible, the
    // drawing carries the dark world, and the corners outside the arch show
    // the page through. A figure with a dark background would fill those
    // corners back in and destroy the door.
    //
    // So the claim is what it always meant: light wall, dark opening. The
    // drawing is INTELLIGENCE, the ground inside the aperture is dark, and
    // in the light scheme the page around it is not. It still fails if a
    // map stops being an INTELLIGENCE component, and it now also fails if
    // the wall goes dark — which the old version could not see.
    // AND THEN THE OWNER'S PALETTE MADE A COUNTRY PORTRAIT A PICTURE.
    // `docs/cartography.md` splits every drawing on what it IS — a picture
    // is warm paper, pale water and an ink coast; an instrument is graphite
    // — and a country's reference map is a picture. It carried
    // `data-world="intelligence"` anyway, which resolved `--map-ink` to the
    // DARK map's bone on a pale continent and measured Italy's own labels
    // at 1.00:1. So the attribute came off, correctly, and this assertion
    // went red for the right event and the wrong claim. Twelfth time.
    //
    // What it protects is that there IS a drawing: the figure still holds
    // the land this page is about. `.atlas` was the obvious replacement and
    // is wrong — a country portrait is `.minimap .countrymap .arched` and
    // the atlas skin is a different family with the same pale ground, which
    // is the same confusion that scoped a map-mark fix to `.atlas` and
    // missed every country plate.
    await w.goto(base + "/europe/italy", { waitUntil: "load" });
    ok(await w.locator(".countrymap .lyr-land, .countrymap .countries").count() >= 1,
       "the country portrait has no land layer — it has stopped being a " +
       "drawing of anywhere");
    const ap = await w.evaluate(() => {
      const g = document.querySelector(".countrymap .archground");
      const fig = document.querySelector(".countrymap");
      // The wall is the first ancestor that actually paints. Reading
      // fig.parentElement alone returned rgba(0,0,0,0) and failed the
      // assertion on a page whose wall is limestone — the transparency was
      // mine, not the design's.
      let n = fig.parentElement, wall = "";
      while (n && n !== document.documentElement) {
        const b = getComputedStyle(n).backgroundColor;
        if (b && !/rgba\(0, 0, 0, 0\)|transparent/.test(b)) { wall = b; break; }
        n = n.parentElement;
      }
      return { ground: g && getComputedStyle(g).fill,
               panel: getComputedStyle(fig).backgroundColor,
               wall: wall || getComputedStyle(document.body).backgroundColor };
    });
    // AND "DARK OPENING" STOPPED BEING TRUE WHEN THE WATER WENT PALE.
    // The owner's light map is #D8D4C7 land on #DDE8E7 water — stone on
    // pale water, with the COASTLINE separating them — so an opening whose
    // luminance must be under 0.06 is an opening from the previous palette.
    // This file already records the consequence one check over: the
    // aperture is read by its REVEAL now, and that is measured on the
    // painted pixel by `c_aperture` rather than on a token here.
    // What survives is the half that is still true and still worth
    // protecting: the opening and the wall must not be the same thing.
    ok(ap.ground && ap.wall && CR(ap.ground, ap.wall) >= 1.1,
       `the opening and the wall are the same tone — opening ${ap.ground}, ` +
       `wall ${ap.wall}. A door is a step or a cut edge, and this is the ` +
       `step; the cut edge is measured on the painted pixel elsewhere`);
    // The figure must paint NOTHING. That is the whole difference between an
    // aperture and a panel: the corners outside the arch have to show the
    // page through, and any background on the figure fills them back in —
    // which is the shape a well-meaning "the map should have a frame" change
    // would take. The first version of this assertion read the wall around
    // the figure instead, and could not fail: a dark background put back on
    // the figure left the section around it light and the suite green.
    ok(/rgba\(0, 0, 0, 0\)|transparent/.test(ap.panel),
       `${scheme}: the map figure paints ${ap.panel} — it is a panel again, `
       + `and the corners outside the arch are filled in`);
    if (scheme === "light") {
      ok(LUM(ap.wall) > 0.7, `${scheme}: the wall the map is cut into is not `
         + `light (${ap.wall}) — there is no light wall, dark opening`);
    }
    // WHAT THE DRAWING ACTUALLY PAINTS.
    //
    // This replaces what the CSS contrast probe was pretending to measure
    // inside the maps. An aperture's ground is an SVG <rect class="archground">
    // and its labels are fills, several of them translucent — a limestone at
    // 72% over a near-black. Nothing about that pair is visible to
    // getComputedStyle().color and a walk up the CSS background chain, so it
    // is read here from the fills themselves, with alpha composited over the
    // ground before the ratio, because 72% of limestone is what a reader
    // sees and 100% of it is not.
    //
    // Small text: 4.5. The labels are 11px.
    for (const url of ["/europe/italy",
                       "/europe/austria/salzburg-and-the-lakes/hallstatt"]) {
      await w.goto(base + url, { waitUntil: "load" });
      const paint = await w.evaluate(() => {
        const parse = (c) => {
          const n = (c.match(/-?\d*\.?\d+/g) || []).map(Number);
          const k = /^color\(/.test(c) ? 255 : 1;
          return [n[0] * k, n[1] * k, n[2] * k,
                  n.length > 3 ? n[3] : 1];
        };
        const out = [];
        for (const fig of document.querySelectorAll(".minimap.arched")) {
          const g = fig.querySelector(".archground");
          if (!g) continue;
          const ground = parse(getComputedStyle(g).fill);
          // `:not(.hit)` because a dot now carries a transparent touch
          // target as its FIRST circle, and querySelector takes the first:
          // this measured the invisible one and reported 1.00:1 on the
          // ground, which is true of the target and says nothing about the
          // dot the reader sees.
          for (const sel of [".minilabel", ".minilabel.here",
                             ".minidot circle:not(.hit)",
                             ".minidot.here circle:not(.hit)", ".routeline",
                             ".rlabel text", ".scalebar text", ".scalebar path"]) {
            const el = fig.querySelector(sel);
            if (!el) continue;
            const cs = getComputedStyle(el);
            const raw = (sel === ".routeline" || sel === ".scalebar path")
            ? cs.stroke : cs.fill;
            const f = parse(raw);
            const a = f[3] * parseFloat(cs.opacity || "1");
            // THE GROUND IS THE HALO WHERE THERE IS ONE. A name on an atlas
            // plate is drawn with `paint-order: stroke` and a paper stroke
            // under it, which is how a printed atlas keeps a name legible
            // across a coastline: the reader sees ink on paper wherever the
            // name falls. Measuring it against the WATER instead reports
            // 1.67:1 for something nobody has any trouble reading, and would
            // push the design towards putting names only over land.
            // Only a stroke that is opaque and at least 1.2px counts — a
            // hairline is not a ground, and a transparent one is not there.
            let bg = ground.slice(0, 3);
            const hs = parse(cs.stroke);
            const hw = parseFloat(cs.strokeWidth || "0");
            if (/stroke/.test(cs.paintOrder || "") && hs[3] >= 0.999 && hw >= 1.2
                && sel !== ".routeline" && sel !== ".scalebar path") {
              bg = hs.slice(0, 3);
            }
            out.push({ sel, fg: [0, 1, 2].map((i) => f[i] * a + bg[i] * (1 - a)),
                       bg });
          }
        }
        return out;
      });
      ok(paint.length > 0, `${url}: no arched map to measure`);
      const lin = (v) => { const x = v / 255;
        return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
      const rel = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
      for (const m of paint) {
        const [hi, lo] = [rel(m.fg), rel(m.bg)].sort((a, b) => b - a);
        const r = (hi + 0.05) / (lo + 0.05);
        // A dot and a route line are graphics, not text: 3:1 is the
        // non-text threshold. The two label selectors are text.
        const need = (m.sel.startsWith(".minilabel")
                      || m.sel === ".rlabel text"
                      || m.sel === ".scalebar text") ? 4.5 : 3;
        ok(r >= need, `${scheme} ${url}: ${m.sel} inside the aperture is `
           + `${r.toFixed(2)}:1 on the opening's ground, needs ${need}`);
      }
    }

    await w.close();
  }

  // A SENTENCE BESIDE A CHECKBOX IS NOT A LABEL IN CAPS.
  //
  // .inlinecheck resets text-transform, and that reset was written twice, in
  // two places, and lost both times: the markup put it inside a .field next
  // to another <label>, so `.field > label` at (0,1,1) beat `.inlinecheck` at
  // (0,1,0) and "Only places with a high discoverability score" rendered as
  // two lines of capitals on /discover and /plan. Nothing caught it because
  // nothing read a computed style — which is the only place a lost cascade
  // is visible. So this reads it.
  //
  // The second assertion is the reason the markup changed rather than the
  // specificity: each of those checkboxes had an explicit `for=` label AND a
  // wrapping one, so its accessible name was both of them concatenated.
  for (const url of ["/discover", "/plan"]) {
    const cp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await cp.goto(base + url, { waitUntil: "load" });
    const boxes = await cp.evaluate(() => {
      const out = [];
      for (const el of document.querySelectorAll(".inlinecheck")) {
        const cs = getComputedStyle(el);
        const input = el.querySelector('input[type="checkbox"]');
        const forLabels = input
          ? document.querySelectorAll(`label[for="${input.id}"]`).length : 0;
        out.push({ text: el.textContent.trim().slice(0, 40),
                   transform: cs.textTransform, forLabels });
      }
      return out;
    });
    ok(boxes.length > 0, `${url}: no .inlinecheck to measure`);
    for (const b of boxes) {
      ok(b.transform === "none",
         `${url}: "${b.text}" is painted text-transform:${b.transform} — a `
         + `sentence beside a checkbox, in capitals, because a more specific `
         + `selector beat the reset`);
      ok(b.forLabels === 0,
         `${url}: "${b.text}" also has a label[for] pointing at its input, so `
         + `the control has two labels and its accessible name is both`);
    }
    await cp.close();
  }

  /* ── AND THE BAR HAS TO SAY WHERE YOU ARE, ON EVERY PAGE THAT IS IN IT ──
   * `aria-current` was decided by the AREA string a page builder passes,
   * and the table's area sets cover the indexes rather than the pages the
   * fields point at. Measured across every rendered family before the
   * repair: 28 lit exactly one room, 0 lit two, and 19 lit NONE — among
   * them /about, /how-it-works, /method, /sources, /beyond-the-obvious and,
   * most plainly, /manifesto, which is the EUROPE room's own href. A reader
   * standing on the page a word in the bar links to was told nothing by
   * that word.
   *
   * THE TWO HALVES OF THE ASSERTION ARE DIFFERENT PROMISES. At most one
   * room may be lit, because a bar that lights two has stopped saying where
   * you are — and the first repair lit two on /discover/<macro>, whose area
   * is ATLAS and whose path is under DISCOVER. And a page that IS a room's
   * href, or one of the entries in its field, must light that room: that is
   * the half no count could report, because a hand-listed area set is
   * always internally consistent.
   *
   * The utilities are in it too. They carried the marker in the markup and
   * had no rule for the marked state, so /search and /my-europe announced a
   * current page to a screen reader and showed nothing to anybody else. */
  {
    const ap = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    let lit = 0, none = 0;
    for (const [fam, url] of require("./lib/families.js").ALL) {
      const r = await ap.goto(base + url, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      const m = await ap.evaluate(() => ({
        rooms: [...document.querySelectorAll('.nav [aria-current="page"]')]
          .map((a) => a.textContent.trim()),
        util: [...document.querySelectorAll('.navutil [aria-current="page"]')]
          .map((a) => a.textContent.trim()),
        // the room this page SHOULD light, read off the bar's own hrefs
        owed: [...document.querySelectorAll(".nav .navtop, .nav .navfield a")]
          .filter((a) => {
            const h = a.getAttribute("href");
            return h === location.pathname ||
                   location.pathname.startsWith(h.replace(/\/$/, "") + "/");
          })
          .map((a) => (a.closest(".navroom") || a).querySelector(".navtop")
                        ? (a.closest(".navroom") || a.parentElement).querySelector(".navtop").textContent.trim()
                        : a.textContent.trim()),
      }));
      checked++;
      ok(m.rooms.length <= 1,
         `${fam} (${url}) lights ${m.rooms.length} rooms — ${m.rooms.join(", ")}. ` +
         `A bar that lights two has stopped saying where you are`);
      if (m.owed.length) {
        checked++;
        ok(m.rooms.length === 1,
           `${fam} (${url}) is the page ${m.owed[0]} links to and the bar ` +
           `lights no room at all`);
      }
      if (m.rooms.length === 1) lit++; else none++;
    }
    checked++;
    ok(lit >= 30,
       `only ${lit} of ${lit + none} families light a room in the masthead, ` +
       `which is below what this check was written at — the bar has stopped ` +
       `saying where a reader is on most of the site`);
    // AND A MARKED LINK HAS TO LOOK MARKED, which is the half the markup
    // cannot answer: the utilities carried the attribute and no rule.
    await ap.goto(base + "/search", { waitUntil: "load" });
    const seen = await ap.evaluate(() => {
      const a = document.querySelector('.navutil [aria-current="page"]');
      if (!a) return null;
      const plain = document.querySelector('.navutil a:not([aria-current])');
      const cs = getComputedStyle(a), ps = getComputedStyle(plain);
      return { border: cs.borderBottomColor, other: ps.borderBottomColor,
               colour: cs.color, othercolour: ps.color };
    });
    checked++;
    ok(seen && (seen.border !== seen.other || seen.colour !== seen.othercolour),
       `/search marks its own utility link current and paints it exactly ` +
       `like the one beside it (${seen && seen.border} against ` +
       `${seen && seen.other}) — present, announced, and invisible`);
    await ap.close();
  }

  // ONE PROJECTION, TWO IMPLEMENTATIONS, AND A CHECK THAT THEY AGREE.
  //
  // The map used to be equirectangular, so the build could hand the browser
  // six numbers and one multiplication. A conic is not affine — the scale
  // along a parallel has to change with latitude for shape to be right
  // anywhere but one line — so map.js now derives the cone constant from the
  // four angles the build publishes. That is a second copy of a formula, and
  // a second copy of a projection is a second copy that drifts; you find out
  // when a coastline sits two pixels off the city on it.
  //
  // The build writes the Python answer for nine points spread across the
  // extent into the page; this reads map.js's answer for the same nine and
  // requires them to agree to a hundredth of a pixel.
  {
    const pp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await pp.goto(base + "/map", { waitUntil: "load" });
    const cmp = await pp.evaluate(() => {
      const probe = window.__europedoorProjectionProbe;
      const el = document.getElementById("europedoor-projection-probe");
      if (!probe || !el) return { missing: true };
      const want = JSON.parse(el.textContent);
      return { missing: false, rows: want.map((r) => {
        const got = probe(r[0], r[1]);
        return { lat: r[0], lon: r[1], dx: got[0] - r[2], dy: got[1] - r[3] };
      }) };
    });
    ok(!cmp.missing, "/map publishes no projection probe — the two "
       + "implementations of the projection cannot be compared");
    if (!cmp.missing) {
      ok(cmp.rows.length >= 9, `only ${cmp.rows.length} projection probe points`);
      for (const r of cmp.rows) {
        ok(Math.abs(r.dx) < 0.01 && Math.abs(r.dy) < 0.01,
           `the browser projects ${r.lat}°N ${r.lon}°E ${r.dx.toFixed(3)}, `
           + `${r.dy.toFixed(3)} px away from the build — one projection, two `
           + `implementations, and they have drifted`);
      }
    }
    await pp.close();
  }

  // No gold anywhere in what the browser actually paints.
  const goldPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await goldPage.goto(base + "/sources", { waitUntil: "load" });
  const golds = await goldPage.evaluate(() => {
    const bad = [];
    for (const el of document.querySelectorAll("*")) {
      const cs = getComputedStyle(el);
      for (const prop of ["color", "backgroundColor", "borderTopColor"]) {
        const m = (cs[prop] || "").match(/\d+/g);
        if (!m) continue;
        const [r, g, b] = m.map(Number);
        if (r >= 90 && r <= 215 && Math.abs(r - g) < 55 && g - b > 45 && r - b > 70) {
          bad.push(`${el.tagName}.${el.className} ${prop} rgb(${r},${g},${b})`);
        }
      }
    }
    return bad.slice(0, 3);
  });
  ok(golds.length === 0, `gold is painted on /sources: ${golds[0]}`);
  await goldPage.close();

  // ── accessibility: WCAG 2.2 AA, the part a machine can hold ─────────
  //
  // Not a conformance claim. These are the failures a build can catch, run
  // on every page shape, in both colour schemes. The audit that matters —
  // somebody using a screen reader daily — is named as missing on
  // /accessibility rather than implied by a green tick here.
  // AND THE LIST WAS TWENTY PAGES TYPED BY HAND, WHICH LEFT TWENTY-SIX PAGE
  // SHAPES NEVER SCANNED IN EITHER COLOUR SCHEME — a macro region, a theme,
  // a motion, a month, a sub-category, a fund project, a facet list, the
  // four legal pages, the public API, contact, help and the manifesto among
  // them. That is the same fault as the four overflow assertions that each
  // named their pages, and as the family list that had never carried a fund
  // project page: a hand-typed list of surfaces is a list of the surfaces
  // somebody thought of. `tools/lib/families.js` is the one list of rendered
  // families and is enumerated against the built site, so a template that
  // exists is a template this scan opens.
  //
  // The extras below are STATES rather than families, which is the one thing
  // that list cannot hold.
  const a11yPages = [
    ...require("./lib/families.js").ALL.map(([, url]) => url),
    // THE STAY EXEMPLAR. The destination shape was represented by Bergen,
    // which has no accommodation context, so the two quietest paragraphs on
    // that section — who holds the rooms, and the affiliate disclosure —
    // were never contrast-checked in either colour scheme.
    "/europe/france/alps-and-east/chamonix",
    // A place page that is not the one families.js picks, and the freshness
    // board, which is a table nothing else in this suite opens.
    "/europe/norway/fjord-norway/bergen/place/bryggen",
    "/sources/freshness",
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

    // ownerSVGElement excludes everything inside a drawing, and that is a
    // correction rather than a convenience. A map's dots are <a
    // class="minidot"> whose textContent is a <title> — an accessible name,
    // a tooltip, not one painted pixel. Both halves of the ratio are then
    // fiction: getComputedStyle().color on an element that paints with
    // `fill`, against a background found by walking up through elements that
    // have no CSS background at all, to the body. On the arched maps that
    // reported 1.00:1 on every dot in Norway — light INTELLIGENCE ink,
    // inherited from the <svg>, measured against the limestone page — while
    // the dots sit on a dark <rect> the walk cannot see, at about 15:1.
    //
    // A contrast probe that cannot see the ground is not measuring contrast.
    // The drawings are measured below instead, from the fills they actually
    // paint.
    const sample = [...document.querySelectorAll("p, li, a, h1, h2, h3, dt, dd, button, label, span.chip, .rowmeta, .kicker, .footer-legal")]
      .filter((el) => el.textContent.trim().length > 3 && !el.ownerSVGElement)
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
      /* AN `<img alt>` INSIDE A LINK IS A NAME, and this probe did not know
       * it: the accessible-name algorithm walks the subtree and an image's
       * alternative text is part of it. So the homepage's story lead — a
       * `<picture>` inside an `<a>`, alt written by the photographer — was
       * reported as a link with no discernible text. It was the right
       * finding for the wrong reason: the name existed and it was the
       * PICTURE's description rather than the story's, so a reader heard
       * "A picturesque view of a Swiss village at twilight" and had to
       * guess where the link went. The page carries an `aria-label` now and
       * the probe counts an alt, because otherwise it fires on every
       * image-only link on the site. */
      const text = (a.textContent || "").trim() || a.getAttribute("aria-label")
        || a.querySelector("svg[aria-label]")
        || [...a.querySelectorAll("img[alt]")].some(i => i.getAttribute("alt").trim());
      if (!text) out.emptyLinks.push(a.getAttribute("href") || "(no href)");
    }
    // A GRAPHIC IS NAMED OR IT IS HIDDEN, AND NEVER BOTH. `role="img"`
    // announces a meaningful image and `aria-hidden` removes it, so the two
    // together are an image with no name; in practice aria-hidden wins, so
    // nothing is broken for a reader and nothing goes red either — which is
    // why eight of them sat on /method until this scan was pointed at every
    // family instead of at twenty typed URLs. The message names the element,
    // because "svg without a name" on a page with eleven of them is a
    // failure message with no measurement in it.
    for (const g of document.querySelectorAll('svg[role="img"]')) {
      const who = `<svg class="${(g.getAttribute("class") || "(none)")}">`;
      if (g.getAttribute("aria-hidden") === "true")
        out.noAlt.push(`${who} claims role="img" and hides itself`);
      else if (!g.getAttribute("aria-label") && !g.querySelector("title"))
        out.noAlt.push(`${who} has role="img" and no name`);
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

  /* NO TWO NAMES ON A MAP MAY OVERLAP, AT EITHER WIDTH.
   *
   * The destination plate — one per destination and one per place, the
   * most-seen map on this site — never had a collision pass at production
   * size. The country map and the macro map both ran a greedy declutter; the
   * destination map ran only the PHONE pass, which decides what fits at the
   * enlarged phone size and marks the losers `wide-only`, and `wide-only` is
   * `display: none` below 44rem and DRAWN above it. So every label the phone
   * pass rejected came back on a desktop and nothing resolved it: measured
   * across all 319 destination plates at 1280, **160 of them carried at least
   * one overlapping pair**, 271 pairs in all, the worst "Levoča & the Spiš"
   * through "Poprad & the High Tatras" by 135 pixels.
   *
   * Three more families were wrong underneath it. The route/region/motion
   * maps tested a DISTANCE between dots rather than an overlap of boxes,
   * which is the mistake this repository already has a note about one family
   * over — it let "Omodos & the wine villages" run 156 px through "Kardamyli
   * & the Mani" while dropping names that were merely near. The country
   * portrait composed its own country name at the END and never measured it,
   * so it landed on whatever was at the middle of the country: 27 of 50
   * pages, the worst "ARMENIA" through "THE NORTH & SOUTH" by 125 px. And
   * the phone pass tested bare overlap with no clearance, so two names could
   * be placed touching.
   *
   * THE MODEL CANNOT CHECK ITSELF. Every one of those passes works from
   * `LABEL_METRICS`, a fitted upper envelope on the width of a name; a static
   * check re-running that model would only ever agree with it. The browser's
   * own `getBoundingClientRect` is the only honest instrument, which is why
   * this lives here and not in checks.py.
   *
   * Both widths, because the two passes are different rules: 1280 is where
   * the placement decides, 390 is where the enlargement re-decides.
   *
   * AND THE SAMPLE REPRESENTED THE PORTRAIT WITH TWO PLATES THAT DID NOT
   * HAVE THE THING. /europe/armenia and /europe/cyprus were here because a
   * country name once landed on top of whatever was at the middle of the
   * country — and neither of them carries a physical name, so neither could
   * ever have shown the defect underneath: the portrait was the fifth
   * drawing that names things and the only one that never ran
   * `phone_declutter`. Measured across all fifty at 390: **32 overlapping
   * pairs on 18 plates**, the worst "Mount Ararat 5,137 m" through "PONTIC
   * MOUNTAINS" by 158 pixels, and zero at 1280 — size was right and
   * arrangement was never asked. Türkiye, Ukraine and Switzerland are the
   * three deepest, so the sample now contains the case.
   */
  /* AND THE LIST WAS FIFTEEN URLs TYPED BY HAND FOR 817 PAGES, ANSWERED
   * TWICE BY TYPING MORE. The paragraph above records the sample being
   * widened when it turned out to hold two plates that did not have the
   * thing — and the answer both times was three more strings. That is the
   * hand-typed-list fault this repository records twice already: the
   * accessibility scan's twenty URLs, and the crop sweep's three entries
   * which had every one of them drifted. Since this list was last touched
   * the country portraits and the macro maps changed frame shape, the region
   * maps took a frame floor, the atlas register was built and two indexes
   * were recomposed; the list did not move.
   *
   * Measured before deriving it, with a one-off instrument over EVERY page
   * carrying a `figure.minimap` — 817 pages, 867 figures — the answer is
   * **zero overlapping pairs at 1280 and zero at 390**. So the typed list
   * was not hiding a defect, and that measurement is what makes a derived
   * sample defensible rather than a shot in the dark: it is the reach that
   * was wrong, not the verdict.
   *
   * SAMPLED RATHER THAN EXHAUSTIVE, AND THE SAMPLE IS SPREAD. 817 pages at
   * two widths is about ten minutes on a suite that already takes forty;
   * a handful per FAMILY, taken at even intervals through each family's own
   * list, costs under two and moves as the site moves. The twelve URLs that
   * are EVIDENCE stay in the set unconditionally — each one is a plate a
   * recorded defect was measured on, and a sample that can drop the case is
   * the fault above. Every family has to contribute, and that is asserted:
   * a family that stops being found reports zero overlaps and passes.
   *
   * AND IT READ THE PAGE BEFORE THE BROWSER HAD SETTLED. With no wait after
   * `goto` on a reused page, `getClientRects()` can hand back a box for an
   * element the stylesheet has since hidden: measured on /europe/sweden at
   * 390, the sweep reported "Skåne & the South" through "Ystad" by 17px on
   * **three runs of eight** — a region name that is `display: none` at that
   * width and is not drawn at all. Two frames of settle takes it to zero of
   * eight. A check that can fail for a reason that is not about the page is
   * a check whoever hits it re-runs until green, which is how a real defect
   * gets through — the same argument that replaced the dead-rule scan's
   * jittering count with a named list. */
  /* THE TWELVE THAT ARE EVIDENCE. Each is a plate a recorded defect was
   * measured on — Chamonix and Athens for the 271 pairs, Levoča for the
   * worst of them, Andorra la Vella for the 91px phone clash, Türkiye,
   * Ukraine and Switzerland for the 32 pairs the portrait's missing phone
   * pass produced, the Alpine Grand Tour and /europe-in/islands for the
   * box-versus-distance test. A sample that can drop the case it was written
   * for is the fault this block is being repaired for, so these are in the
   * set whatever the sampling says. */
  const EVIDENCE_PLATES = [
    "/europe/france/alps-and-east/chamonix",
    "/europe/greece/athens-and-the-peloponnese/athens",
    "/europe/norway/fjord-norway/bergen",
    "/europe/poland/lesser-poland/krakow",
    "/europe/andorra/the-valleys/andorra-la-vella",
    "/europe/slovakia/tatras-and-the-north/levoca",
    "/europe/armenia/yerevan-and-ararat/yerevan",
    "/europe/turkiye",
    "/europe/ukraine",
    "/europe/switzerland",
    "/journeys/the-alpine-grand-tour",
    "/europe-in/islands",
  ];
  const _mmPages = (() => {
    const out = [];
    const walk = (d) => {
      for (const e of fs.readdirSync(d, { withFileTypes: true })) {
        const q = path.join(d, e.name);
        if (e.isDirectory()) walk(q);
        else if (e.name === "index.html" &&
                 fs.readFileSync(q, "utf8").includes('class="minimap'))
          out.push("/" + path.relative(OUT, q).replace(/\/?index\.html$/, ""));
      }
    };
    walk(OUT);
    // The family key is the ROUTE's own shape, which is what decides which
    // builder drew the map: /europe/<c> is a country, /europe/<c>/<r> a
    // region, and so on down. render.ed_family() makes the same argument
    // about a page's room — a family is what a route IS.
    const fam = (u) => {
      const p = u.split("/").filter(Boolean);
      if (!p.length) return "home";
      if (p[0] === "europe") return "europe/" + p.length;
      return p.length > 1 ? p[0] + "/*" : p[0];
    };
    const by = new Map();
    for (const u of out) {
      const k = fam(u);
      if (!by.has(k)) by.set(k, []);
      by.get(k).push(u);
    }
    // PROPORTIONAL, WITH A FLOOR AND A CEILING, because a flat four per
    // family samples 4 of 319 destination plates and 4 of 1 story — one
    // number cannot be right for both ends of a 319:1 spread. A thirty-second
    // of a family, never fewer than four and never more than twelve, spreads
    // 817 pages over about sixty at two widths, which is a couple of minutes
    // on a forty-minute suite.
    const pick = new Set(EVIDENCE_PLATES);
    for (const [, list] of [...by].sort()) {
      list.sort();
      const want = Math.max(4, Math.min(12, Math.round(list.length / 32)));
      const n = Math.min(want, list.length);
      for (let i = 0; i < n; i++)
        pick.add(list[Math.floor((i * list.length) / n)]);
    }
    return { urls: [...pick].sort(), families: by.size, total: out.length };
  })();

  for (const [vw, vh] of [[1280, 900], [390, 800]]) {
    const lc = await browser.newPage({ viewport: { width: vw, height: vh } });
    let pairs = 0, worst = 0, worstAt = "", seen = 0, figs = 0;
    for (const u of _mmPages.urls) {
      const r = await lc.goto(base + u, { waitUntil: "domcontentloaded" });
      if (!r || r.status() !== 200) continue;
      await lc.evaluate(() => new Promise((rr) =>
        requestAnimationFrame(() => requestAnimationFrame(rr))));
      seen++;
      const hit = await lc.evaluate(() => {
        const out = [];
        for (const fig of document.querySelectorAll("figure.minimap")) {
          const t = [...fig.querySelectorAll("text")]
            .filter((e) => e.getClientRects().length)
            .map((e) => { const b = e.getBoundingClientRect();
                          return [e.textContent.trim(), b.x, b.y, b.width, b.height]; });
          for (let i = 0; i < t.length; i++)
            for (let j = i + 1; j < t.length; j++) {
              const a = t[i], c = t[j];
              const ox = Math.min(a[1] + a[3], c[1] + c[3]) - Math.max(a[1], c[1]);
              const oy = Math.min(a[2] + a[4], c[2] + c[4]) - Math.max(a[2], c[2]);
              if (ox > 0 && oy > 0) out.push([a[0] + " / " + c[0], ox]);
            }
        }
        return { out, figs: document.querySelectorAll("figure.minimap").length };
      });
      figs += hit.figs;
      for (const [names, ox] of hit.out) {
        pairs++;
        if (ox > worst) { worst = ox; worstAt = `${u}: ${names}`; }
      }
      checked++;   // one plate examined, at this width
    }
    ok(pairs === 0,
       `${pairs} overlapping label pair(s) on the map plates at ${vw}px — ` +
       `worst ${worst.toFixed(0)}px, ${worstAt}. A name drawn through another ` +
       `name is the one defect on these plates a reader cannot work around: ` +
       `the dot, the <title> and the row below survive a DROPPED label, and ` +
       `nothing survives an unreadable one`);
    // AND THE REACH IS ASSERTED, because a page set that stops finding the
    // drawings reports zero overlaps and passes — which is how the crop
    // sweep made two green assertions a run about elements the site no
    // longer had, and how `.qtile` printed "it examined 0 states" for three
    // redesigns. The floors are a fraction of what the built site holds
    // rather than a typed number: the figure count moves whenever a family
    // gains or loses a map, and a floor that has to be re-typed is a floor
    // somebody raises instead of reading.
    ok(seen === _mmPages.urls.length && seen >= _mmPages.families,
       `the plate sweep loaded ${seen} of ${_mmPages.urls.length} sampled ` +
       `page(s) at ${vw}px across ${_mmPages.families} families of the ` +
       `${_mmPages.total} carrying a figure.minimap — a page that 404s is ` +
       `skipped silently and takes its family's coverage with it`);
    ok(figs >= seen,
       `the plate sweep found ${figs} figure.minimap over ${seen} page(s) at ` +
       `${vw}px, fewer than one each. Every page in this set was chosen ` +
       `because its HTML carries that class, so a page contributing none ` +
       `means the selector and the markup have parted company`);
    await lc.close();
  }

  /* AND THE SWEEP ABOVE READS `figure.minimap`, WHICH IS EVERY MULTI-FAMILY
   * DRAWING ON THIS SITE EXCEPT THE TWO LARGEST.
   *
   * Counted across the built site, twenty-nine shapes carry more than one
   * label family and twenty-eight of them are a `.minimap`. The twenty-ninth
   * is the hero — `.heroeurope`, which is not a figure at all — and the
   * thirtieth is `#europemap`. Those two are the only drawings here that
   * carry `.seaname` beside `.cname`, they are the biggest pictures on the
   * site, and no arrangement check has ever looked at either. Measured in
   * Chromium at 1280, 1440 and 1920 before this block existed:
   *
   *     "NORTH SEA" through "UNITED KINGDOM"      68px   /
   *     "BAY OF BISCAY" through "FRANCE"          41px   /
   *     "BLACK SEA" through "ROMANIA"             18px   /
   *     "NORTH SEA" through "UNITED KINGDOM"      80px   /map
   *     "IONIAN SEA" through "GREECE"             49px   /map
   *
   * A selector, not a figure class: the question is whether two labels on
   * one drawing overlap, and which element the build chose to wrap it in is
   * not part of that question. That is what confined the sweep above.
   *
   * AND IT ASSERTS ITS OWN REACH, because a selector that matches nothing
   * reports zero overlapping pairs and passes — which is how `.qtile` printed
   * "it examined 0 states" for three redesigns and how the crop-box sweep
   * made two green assertions a run about elements the site no longer had.
   * Three widths rather than one, because the hero is `slice` and crops a
   * different part of its frame at every window shape. */
  {
    const lc = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    let drawings = 0, pairs = 0, worst = 0, worstAt = "";
    for (const [vw, vh] of [[1280, 900], [1440, 900], [1920, 1080]]) {
      await lc.setViewportSize({ width: vw, height: vh });
      for (const u of ["/", "/map"]) {
        const r0 = await lc.goto(base + u, { waitUntil: "load" });
        if (!r0 || r0.status() !== 200) continue;
        await lc.evaluate(() => new Promise((r) =>
          requestAnimationFrame(() => requestAnimationFrame(r))));
        const r = await lc.evaluate(() => {
          const out = { svgs: 0, hits: [] };
          for (const svg of document.querySelectorAll("svg")) {
            const fams = new Set();
            const t = [...svg.querySelectorAll("text")]
              .filter((e) => e.getClientRects().length &&
                             getComputedStyle(e).display !== "none")
              .map((e) => { fams.add(e.getAttribute("class") || "(none)");
                            const b = e.getBoundingClientRect();
                            return [e.textContent.trim(), b.x, b.y, b.width, b.height]; });
            if (fams.size < 2) continue;
            out.svgs++;
            for (let i = 0; i < t.length; i++)
              for (let j = i + 1; j < t.length; j++) {
                const a = t[i], c = t[j];
                const ox = Math.min(a[1] + a[3], c[1] + c[3]) - Math.max(a[1], c[1]);
                const oy = Math.min(a[2] + a[4], c[2] + c[4]) - Math.max(a[2], c[2]);
                if (ox > 0 && oy > 0) out.hits.push([a[0] + " / " + c[0], ox]);
              }
          }
          return out;
        });
        drawings += r.svgs;
        for (const [names, ox] of r.hits) {
          pairs++;
          if (ox > worst) { worst = ox; worstAt = `${vw}px ${u}: ${names}`; }
        }
      }
    }
    ok(drawings === 6,
       `the two-family sweep found ${drawings} drawing(s) carrying two label ` +
       `families over 2 pages x 3 widths, expected 6. The hero and /map are ` +
       `the only two, and a sweep that stops finding them reports zero ` +
       `overlaps and passes`);
    ok(pairs === 0,
       `${pairs} overlapping label pair(s) where two label families share one ` +
       `drawing — worst ${worst.toFixed(0)}px, ${worstAt}. The sea names are ` +
       `PINNED (one position each, the middle of their own water) and the ` +
       `country names are FREE (nine anchors, four positions), so the pinned ` +
       `family is composed first and name_countries() is handed its boxes as ` +
       `reserved. A pair here means that wiring came undone`);
    checked += drawings;

    /* AND THE MODEL THAT RESERVES THEM IS CHECKED AGAINST THE DRAWING.
     *
     * `LABEL_METRICS["seaname"]` is a fitted upper envelope on the width of a
     * sea name, so the build reserves a box it has MODELLED rather than one
     * it has measured — and a static check re-running that model would only
     * ever agree with it. getBBox is the different implementation of the same
     * question, in the drawing's own user units, which is what the model is
     * stated in. An envelope that UNDERSTATES is the failure that matters:
     * the reserved box would be smaller than the type and a country name
     * would be let through into it. */
    const MODEL = { "/": [0.5, 12.75], "/map": [11.0, 10.2] };
    let names = 0, under = [];
    for (const u of ["/", "/map"]) {
      await lc.setViewportSize({ width: 1280, height: 900 });
      const r0 = await lc.goto(base + u, { waitUntil: "load" });
      if (!r0 || r0.status() !== 200) continue;
      const got = await lc.evaluate(() => [...document.querySelectorAll("text.seaname")]
        .map((e) => { const b = e.getBBox();
                      return { t: e.textContent.trim(), w: b.width,
                               up: parseFloat(e.getAttribute("y")) - b.y,
                               down: (b.y + b.height) - parseFloat(e.getAttribute("y")) }; }));
      const [pad, ch] = MODEL[u];
      for (const g of got) {
        names++;
        const model = pad + ch * g.t.length;
        if (model < g.w - 0.01)
          under.push(`${u} "${g.t}" real ${g.w.toFixed(1)}u model ${model.toFixed(1)}u`);
      }
    }
    ok(names >= 11,
       `the sea-name model check measured ${names} rendered name(s), expected ` +
       `at least 11 — it has stopped finding the layer it is about`);
    ok(under.length === 0,
       `${under.length} sea name(s) are WIDER than the box the build reserves ` +
       `for them: ${under.slice(0, 3).join("; ")}. The envelope in ` +
       `LABEL_METRICS understates the type, so a country name can be placed ` +
       `into ground the drawing has already spent`);
    await lc.close();
  }


  /* THE RATIO IS THE INSTRUCTION, AND NOTHING HAD EVER MEASURED IT.
   *
   * docs/palette.json opens with "the ratio is the instruction, not the hex
   * codes: a palette gives you a blue website with gold buttons; a ratio
   * gives you European editorial design over futuristic infrastructure" —
   * 60 limestone, 25 graphite, 10 cobalt, 5 accent. The only assertion on it
   * was that the four numbers add to 100. A declaration nobody measures is a
   * mood board with a schema.
   *
   * Measured here on the pixels a reader is actually painted, over twelve
   * pages chosen to span the families rather than to flatter: both worlds,
   * an index, a destination, a country, an instrument, a prose page.
   * Classified by CHROMA rather than by HSL saturation, because limestone is
   * #f7f6f3 and HSL calls that 20% saturated — the first version of this
   * counted the paper as an accent and reported the site 60% terracotta.
   * Chroma (max - min) is 0.016 for limestone and 0.055 for the atlas
   * parchment, so a tenth separates the neutrals from everything that is a
   * colour.
   *
   * The bands are wide on purpose. This is not a target to hit per page — a
   * country page is nearly all paper and /map is nearly all graphite, and
   * both are correct. It is a guard against the two ways a palette dies:
   * the ground stops being the ground, and the accent eats the page.
   */
  {
    /* /europe-in IS ABSENT AND THAT HID A REAL FINDING. The scan reported
     * `.thtile {display,color}` dead on /themes, and `.motile` on
     * /europe-in carries the identical three declarations for the identical
     * reason — a grid item is blockified by the layout and `a { color:
     * inherit }` already applies — and was never reported, because no page
     * in this list has ever held one. *A rule measured only where it loses
     * looks like a rule that wins nowhere* is already recorded here; a rule
     * measured NOWHERE looks exactly like a rule that is fine, which is
     * worse. Widening the list is its own commit with its own triage: the
     * three index families take the population from 381 rules to 506 and
     * the dead list from 42 to 71, with 31 fresh, and a ceiling raised
     * without reading the list is a ceiling raised for a gap in the scan. */
    const PAGES = ["/", "/europe/austria/", "/europe/norway/fjord-norway/bergen/",
                   "/themes/", "/journeys/", "/stories/", "/map/", "/plan/",
                   "/experiences/food/", "/method/", "/beyond-the-obvious/",
                   "/events/"];
    const rc = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    /* A HUE BAND CANNOT SEPARATE THE SIGNATURE FROM THE SEA ANY MORE.
     * pine is at hue 174.2 and the owner's map water at 174.5 — three
     * tenths of a degree — so the water window swallowed the masthead and
     * this instrument reported the signature at 0.1% against a declared 10.
     * The bands were already DATA rather than a ternary, which is the only
     * reason the reading could be diagnosed at all, and data was not
     * enough: two overlapping windows are two windows whichever file they
     * live in.
     * A pixel is classified by the TOKEN IT IS NEAREST TO now, in OKLab,
     * and the register says which family each token belongs to. A lookup,
     * never a shape. Pixels further than max_distance from every token are
     * neither — a photograph, a blend, a shadow — and are left out of the
     * denominator rather than called paper. SWATCH and MAXD are built once
     * at the top of this file, because two checks ask this question and two
     * implementations of it is how both hue windows got written. */
    const tot = { limestone: 0, graphite: 0, water: 0, pine: 0, accent: 0 };
    const per = [];
    let px = 0;
    for (const u of PAGES) {
      const r = await rc.goto(base + u, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      const buf = await rc.screenshot();
      const got = await rc.evaluate(async ({ b64, SWATCH, MAXD }) => {
        const img = new Image();
        img.src = "data:image/png;base64," + b64;
        await img.decode();
        const c = document.createElement("canvas");
        c.width = img.width; c.height = img.height;
        const x = c.getContext("2d");
        x.drawImage(img, 0, 0);
        const d = x.getImageData(0, 0, c.width, c.height).data;
        // AND THE BUCKET THE CLASSIFIER WRITES MUST BE ONE THIS DECLARES.
        // The palette rename moved the signature from `cobalt` to `pine` in
        // the classifier below and left this line saying `cobalt`, so
        // `out.pine++` was `undefined++` — NaN. NaN propagated into the
        // total, `px || 1` is 1 because NaN is falsy, and every share came
        // back as a raw pixel count wearing a percent sign: "limestone
        // 956561700.0%". The assertion under it fails loudly on a NaN now,
        // because a share that is not a number is not a small share. The
        // buckets are built FROM the register here, so the two cannot
        // disagree at all.
        const srgb = (c) => (c <= 0.04045 ? c / 12.92
                                          : Math.pow((c + 0.055) / 1.055, 2.4));
        const oklab = (R, G, B) => {
          const r = srgb(R), g = srgb(G), b = srgb(B);
          const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
          const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
          const s2 = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
          return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s2,
                  1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s2,
                  0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s2];
        };
        const marks = SWATCH.map((t) => ({
          family: t.family,
          lab: oklab(parseInt(t.hex.slice(1, 3), 16) / 255,
                     parseInt(t.hex.slice(3, 5), 16) / 255,
                     parseInt(t.hex.slice(5, 7), 16) / 255),
        }));
        const out = { limestone: 0, graphite: 0, water: 0, pine: 0, accent: 0 };
        const NAME = { bone: "limestone", graphite: "graphite", pine: "pine",
                       water: "water", accent: "accent" };
        let other = 0;
        for (let i = 0; i < d.length; i += 4) {
          const lab = oklab(d[i] / 255, d[i + 1] / 255, d[i + 2] / 255);
          let best = null, bd = Infinity;
          for (const m of marks) {
            const dl = lab[0] - m.lab[0], da = lab[1] - m.lab[1],
                  db = lab[2] - m.lab[2];
            const dist = dl * dl + da * da + db * db;
            if (dist < bd) { bd = dist; best = m; }
          }
          if (Math.sqrt(bd) > MAXD) { other++; continue; }
          out[NAME[best.family]]++;
        }
        out.$other = other;
        return out;
      }, { b64: buf.toString("base64"), SWATCH, MAXD });
      delete got.$other;   // counted, and deliberately not in the denominator
      const pn = Object.values(got).reduce((a, b) => a + b, 0) || 1;
      per.push([u, 100 * got.accent / pn]);
      for (const k of Object.keys(tot)) { tot[k] += got[k]; px += got[k]; }
      checked++;                       // one page measured
    }
    await rc.close();
    const pc = {};
    for (const k of Object.keys(tot)) pc[k] = 100 * tot[k] / (px || 1);
    const say = Object.entries(pc)
      .map(([k, v]) => `${k} ${v.toFixed(1)}%`).join(", ");
    ok(px > 0, "the palette-ratio measurement examined no pixels at all");
    ok(Object.values(pc).every(Number.isFinite),
       `the palette-ratio measurement produced a share that is not a number ` +
       `(${say}). A bucket the classifier writes is not one the counter ` +
       `declares, so its count is NaN and every other share is divided by it`);
    ok(pc.limestone >= 45 && pc.limestone <= 78,
       `limestone paints ${pc.limestone.toFixed(1)}% of the measured pages ` +
       `and the ratio makes it the ground at 60 (${say}). Outside 45-78 the ` +
       `paper has stopped being what the site is made of`);
    ok(pc.graphite >= 8,
       `graphite paints ${pc.graphite.toFixed(1)}% (${say}). It is the ink, ` +
       `the dark world and every map opening — below 8 one of those has gone`);
    ok(pc.pine <= 13,
       `the signature paints ${pc.pine.toFixed(1)}% of the measured pages and the ` +
       `ratio gives it 10 (${say}). A continent drawn in the signature is a ` +
       `network diagram, which is the association the cartography split ` +
       `exists to escape. The ceiling is 13 rather than 24 because water is ` +
       `counted separately now and the old figure was mostly the Atlantic`);
    ok(pc.water <= 24,
       `the water families paint ${pc.water.toFixed(1)}% (${say}). They have ` +
       `no line in the declared ratio because they are the DRAWINGS rather ` +
       `than the interface, and a ceiling is what keeps that true: above ` +
       `this the maps have stopped being figures on a page`);
    // THE ACCENT IS ASSERTED WHERE IT BELONGS, NOT AS A SITE-WIDE SHARE.
    // A floor on the aggregate was 0.3% against a threshold of 0.2 — close
    // enough that one page dropping out of the sample flipped it, which is
    // a check that fails without saying anything. The accent has a home:
    // the families whose --door is terracotta or atlantic. So the assertion
    // is that it still paints SOMEWHERE, and the message carries every
    // page's figure, because a failure with no measurement in it cannot be
    // diagnosed.
    per.sort((a, b) => b[1] - a[1]);
    ok(per.length > 0 && per[0][1] >= 0.5,
       `no measured page paints as much as half a per cent of accent — the ` +
       `best is ${per[0] ? per[0][0] + " at " + per[0][1].toFixed(2) + "%" : "none"} ` +
       `(${say}). Terracotta and atlantic are the entire art-directional ` +
       `difference between a story and a country encyclopedia. Per page: ` +
       per.map(([u, v]) => `${u} ${v.toFixed(2)}`).join(", "));
    console.log(`    palette ratio measured: ${say}  ` +
                `(declared 60/25/10/5, water unbudgeted)`);
  }


  /* A WORD CUT IN HALF IS A RENDERING FAULT, and one family had it on 146
   * pages. The destination page's sticky phone action carried the place name
   * in a flexed span with an ellipsis, and two buttons take 230 pixels of a
   * 390-pixel bar: measured on all 319 destinations, 46% rendered a cut word.
   * "Innsbr...", and "Gura Humorului & the painted monasteries" 255 pixels
   * over its slot. This repository already refuses a map label sliced by the
   * aperture for exactly this reason — a name drawn through another name, or
   * cut mid-word, is the one defect a reader cannot work around.
   *
   * So the rule is general rather than about that bar: no element anywhere
   * may hold more text than it shows. Scroll containers are excluded because
   * scrolling IS the answer there, and `.visually-hidden` is excluded because
   * clipping is how it hides.
   */
  {
    const CLIPPED = ["/", "/europe/austria/", "/europe/austria/tyrol/innsbruck/",
                     "/themes/", "/journeys/", "/stories/", "/map/", "/plan/",
                     "/experiences/food/", "/method/", "/beyond-the-obvious/",
                     "/events/", "/search/", "/my-europe/", "/europe-in/islands/",
                     "/interests/mountains/", "/sources/", "/about/"];
    // 320 IS IN THE LIST BECAUSE THE WORDMARK WAS CUT THERE AND NOWHERE
    // ELSE. This ran at 390 and 1280 and reported clean while `.wordmark`
    // measured 116px of content in a 90px box at 320 — the brand name,
    // sliced, on the narrowest phone still in use, because the masthead's
    // two utility links were taking the width. A clipping check that only
    // runs at the design width tests the width somebody already looked at.
    for (const W of [320, 390, 1280]) {
      const cp = await browser.newPage({ viewport: { width: W, height: 900 } });
      const hits = [];
      for (const u of CLIPPED) {
        const r = await cp.goto(base + u, { waitUntil: "load" });
        if (!r || r.status() !== 200) continue;
        const got = await cp.evaluate(() => {
          const out = [];
          for (const e of document.querySelectorAll("*")) {
            if (!e.clientWidth) continue;
            if (e.closest(".visually-hidden")) continue;
            const cs = getComputedStyle(e);
            if (cs.overflowX !== "hidden" && cs.overflowX !== "clip") continue;
            if (e.scrollWidth > e.clientWidth + 1 && e.textContent.trim())
              out.push(`${e.tagName.toLowerCase()}.${(e.className || "")
                .toString().trim().split(/\s+/)[0]} "${e.textContent.trim()
                .slice(0, 30)}" ${e.scrollWidth - e.clientWidth}px over`);
          }
          return out;
        });
        for (const g of got) hits.push(`${u} ${g}`);
        checked++;                     // one page read, at this width
      }
      await cp.close();
      ok(hits.length === 0,
         `${hits.length} element(s) hold more text than they show at ${W}px — ` +
         `${hits.slice(0, 3).join("; ")}. A word cut in half reads as a broken ` +
         `renderer, which is why a map label sliced by the aperture is dropped ` +
         `rather than drawn`);
    }
  }


  /* ── NOT ONE PAGE SCROLLS SIDEWAYS, ON EVERY FAMILY, AT EVERY PHONE ──
   *
   * There were four overflow assertions in this suite and every one of them
   * named a page by hand: the homepage's full-bleed band, a populated
   * /my-europe, /map, and the clipping sweep's list of eighteen. None of
   * them is a place page, so the place family scrolled sideways at 390 — the
   * width every gate here runs at — and nothing said so.
   *
   * What it was: Europe writes `Jugendstilsenteret`, `Kunsthistorisches` and
   * `Groeningemuseum`, an h1 is set at 76px, and a word longer than the
   * column ran off the right edge. Measured before the fix: Groeningemuseum
   * 381 units of word in a 336-pixel box at 390, pushing the document 7px
   * sideways; 37 at 360 and 77 at 320. And separately the country door,
   * sized by height on a frame held to a constant 1.299, is always 312
   * pixels wide against a 288-pixel column at 320.
   *
   * THE LIST IS `tools/lib/families.js`, which is the one list of rendered
   * families and is enumerated against the built site. A hand-typed list is
   * how three templates went unmeasured until a fund project page was found
   * shipping at 0% picture, and it is how this went unmeasured too.
   *
   * 360 is in the widths because the fault was 7px at 390 and 37 at 360: a
   * defect that is one pixel under the threshold at the design width is a
   * defect somebody will call a rounding error.
   */
  {
    const FAM = require("./lib/families.js").ALL;
    for (const W of [320, 360, 390]) {
      const op = await browser.newPage({ viewport: { width: W, height: 900 } });
      const hits = [];
      let seen = 0;
      for (const [name, url] of FAM) {
        const r = await op.goto(base + url, { waitUntil: "load" });
        if (!r || r.status() !== 200) continue;
        seen++;
        const over = await op.evaluate(() =>
          document.documentElement.scrollWidth
          - document.documentElement.clientWidth);
        if (over > 1) hits.push(`${name} +${over}px`);
      }
      await op.close();
      checked += seen;
      ok(seen >= 40,
         `the sideways-scroll sweep read only ${seen} families at ${W} — it ` +
         `has stopped finding them`);
      ok(hits.length === 0,
         `${hits.length} of ${seen} families scroll sideways at ${W}px: ` +
         `${hits.slice(0, 5).join(", ")}. A reader cannot put the page back.`);
    }
  }

  /* NOTHING HERE HAD EVER MEASURED A LAYOUT SHIFT, AND ONE PAGE OF THIRTY
   * WAS AT 0.3025.
   *
   * §49 of the Build Package asks for "excellent Core Web Vitals" and this
   * repository measures BYTES — `weight.home_kb` and `weight.max_page_kb`
   * are ceilings and they are the whole of what any gate here knew about
   * performance. Bytes are not movement: a page can be 26 KB and still
   * throw its own content down the screen after it has painted.
   *
   * Measured across every family at 1280: twenty-nine of thirty are
   * EXACTLY 0.0000, which is what a static site with `width`/`height` on
   * all 1,617 of its `<img>` and 64 `aspect-ratio` declarations should be
   * — and /search was 0.3025, past the 0.25 that Google calls poor.
   * `search.js` replaced the build's own 1,185-pixel index breakdown with
   * `<p class="small">Loading the index…</p>` and put it back when the
   * fetch resolved: `#results` 25px at 72ms with `readyState` already
   * complete, 1,185px the instant /api/search.json arrived, 266 pixels of
   * push that sent the footer off the fold. Delaying the index by 400ms
   * moved the jump to 448ms, which is what proves the FETCH is the trigger
   * rather than the parse.
   *
   * AND THE LINE THAT DID IT SAT 168 LINES BELOW A COMMENT SAYING IT HAD
   * BEEN REMOVED. `AT_REST` captures the band and restores it — the half
   * that got written — and the assignment that threw it away first was
   * left standing. A loading state over a complete page is a regression
   * dressed as feedback, and it is honest only where the reader is waiting
   * for something they asked for, which is the `?q=` arrival.
   *
   * THE CEILING IS 0.02 RATHER THAN 0.1. Google's "good" is 0.1, and a
   * threshold a site is nowhere near is a threshold that admits a real
   * regression: every family here is at zero, so the honest ceiling is
   * "essentially zero" and the number a reader would notice is far above
   * it. The message names the ELEMENT that moved and its box before and
   * after, because a CLS figure with no element in it cannot be diagnosed.
   */
  {
    const FAM = require("./lib/families.js").ALL;
    // Its own page, because `PerformanceObserver` with `buffered: true`
    // reports the shifts of whatever this page has already loaded — the
    // dead-rule scan's recorded failure, where a shared page carried the
    // pointer position of an earlier check into this one.
    const cp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await cp.addInitScript(() => {
      window.__cls = 0;
      window.__shifts = [];
      new PerformanceObserver((l) => {
        for (const e of l.getEntries()) {
          if (e.hadRecentInput) continue;
          window.__cls += e.value;
          for (const s of e.sources || []) {
            const n = s.node;
            window.__shifts.push({
              v: e.value,
              el: n && n.tagName
                ? n.tagName.toLowerCase() + (n.id ? "#" + n.id : "") +
                  (n.className ? "." + String(n.className).split(" ").slice(0, 2).join(".") : "")
                : "(anonymous)",
              was: s.previousRect
                ? `y${Math.round(s.previousRect.y)}+${Math.round(s.previousRect.height)}` : "-",
              now: s.currentRect
                ? `y${Math.round(s.currentRect.y)}+${Math.round(s.currentRect.height)}` : "-",
            });
          }
        }
      }).observe({ type: "layout-shift", buffered: true });
    });
    const shifty = [];
    let seenCls = 0;
    for (const [name, url] of FAM) {
      const r = await cp.goto(base + url, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      seenCls++;
      // Long enough for a fetch to land and re-render: the defect this was
      // written for happened at 90ms with the index served locally and at
      // 448ms with it delayed, and a reader on a real network is slower
      // than either.
      await cp.evaluate(() => new Promise((res) => setTimeout(res, 700)));
      const v = await cp.evaluate(() => ({ cls: window.__cls, shifts: window.__shifts }));
      if (v.cls > 0.02) {
        const worst = v.shifts.sort((a, b) => b.v - a.v)[0];
        shifty.push(`${name} ${v.cls.toFixed(4)}` +
                    (worst ? ` (${worst.el} ${worst.was} -> ${worst.now})` : ""));
      }
    }
    await cp.close();
    checked += seenCls;
    ok(seenCls >= 40,
       `the layout-shift sweep read only ${seenCls} families — it has ` +
       `stopped finding them, and a sweep of nothing reports no shift`);
    ok(shifty.length === 0,
       `${shifty.length} of ${seenCls} families shift after painting: ` +
       `${shifty.slice(0, 6).join("; ")}. Content that moves once a reader ` +
       `has started reading it is the one performance fault bytes cannot see.`);
  }

  /* A LINK AT ZERO ALPHA IS PRESENT, PLACED, SIZED, KEYBOARD-REACHABLE AND
   * NOT THERE — AND EVERY COUNT ON THIS SITE SAYS IT IS FINE.
   *
   * /experiences closed on two links that paint nothing. `.doorgo` already
   * existed: it belongs to the homepage's four doors, where the go-link is
   * revealed on hover, and `opacity: 0` is declared hundreds of lines above
   * the composition that reused the name. So the class was a rule the new
   * band inherited silently. This file already records the rule against a
   * second NAME for one colour; this is one name for two things, which is
   * the same fault from the other end and has no guard at all.
   *
   * Nothing could see it. `getComputedStyle` says `visibility: visible` and
   * `opacity: 1` ON THE LINK — the zero is two elements up, so a check that
   * reads the element's own style passes. The contrast sweep reads declared
   * colours and the ratio was correct. The clipping scan asks whether an
   * element holds more text than it shows and it showed all of it. The
   * layout sweep measured 732 x 21 in the right place. Only walking the
   * ancestor chain for the composited alpha finds it, which is exactly what
   * `checkVisibility({ checkOpacity: true })` does.
   *
   * AND A HIDDEN LINK IS NOT AUTOMATICALLY A DEFECT, which is why the test
   * FOCUSES it first. Hover-revealed navigation is a real pattern and this
   * site ships it: the four doors, the licence credit on a photograph. Every
   * one of those reveals on `:focus-visible` as well, because a link a
   * keyboard reaches has to become visible when it does — so focusing each
   * link and then asking is one test that admits the pattern and refuses the
   * accident. A link that is still invisible with focus on it is a link
   * nobody can use by any route.
   *
   * THE LIST IS `tools/lib/families.js` — the one list of rendered families,
   * enumerated against the built site — because a hand-typed list is how the
   * fund project page shipped at 0% picture and how this would go unmeasured
   * on the next family that reuses a name.
   */
  {
    const FAM = require("./lib/families.js").ALL;
    const op = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const hits = [];
    let seen = 0, links = 0;
    for (const [name, url] of FAM) {
      const r = await op.goto(base + url, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      seen++;
      /* THE ELEMENT IS FOUND, FOCUSED AND ASKED, one at a time, because
       * `:focus-visible` applies to exactly one element at a time and a
       * batch evaluation would ask about the reveal of a link nothing is
       * focused on. `aria-hidden` and `display: none` links are skipped:
       * a thumb-bar duplicate below its breakpoint is not a defect, and
       * `checkVisibility` without `checkOpacity` is the test for that. */
      const n = await op.evaluate(() => {
        window.__L = [...document.querySelectorAll("main a[href], footer a[href]")]
          .filter(a => a.checkVisibility() && !a.closest("[aria-hidden='true']"));
        return window.__L.length;
      });
      /* TWO PASSES, AND THE FIRST RUN OF THIS CHECK WAS WRONG BECAUSE IT
       * HAD ONLY ONE. A reveal is a TRANSITION — `.credit` runs
       * `opacity .16s ease` — so the used value the instant after
       * `focus()` is still zero, and the first run reported 182 links at
       * zero alpha on every photograph credit on the site. Every one of
       * them reveals correctly: `picture:focus-within .credit` has been
       * there since the credit was written. The instrument was measuring
       * the frame before the animation rather than the state.
       *
       * Waiting on every link would cost 3,591 waits. So the fast pass
       * collects candidates and the slow pass waits for the element's own
       * animations to finish and asks again — which is the state a reader
       * actually gets, and it is derived from the transition rather than
       * from a number somebody picked. */
      const cand = await op.evaluate((n) => {
        const out = [];
        for (let i = 0; i < n; i++) {
          const a = window.__L[i];
          a.focus();
          if (!a.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true }))
            out.push(i);
        }
        return out;
      }, n);
      for (const i of cand) {
        const bad = await op.evaluate(async (i) => {
          const a = window.__L[i];
          a.focus();
          const anims = [];
          for (let e = a; e && e !== document.documentElement; e = e.parentElement)
            anims.push(...e.getAnimations());
          await Promise.race([
            Promise.all(anims.map(x => x.finished.catch(() => {}))),
            new Promise(r => setTimeout(r, 400)),
          ]);
          if (a.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return null;
          let e = a, zero = "";
          while (e && e !== document.documentElement) {
            if (getComputedStyle(e).opacity === "0") {
              zero = e.tagName.toLowerCase() +
                     (e.className ? "." + e.className.toString().trim().split(/\s+/)[0] : "");
              break;
            }
            e = e.parentElement;
          }
          return `${(a.textContent || a.getAttribute("aria-label") || "?").trim().slice(0, 28)}`
                 + ` — zero alpha on ${zero || "an ancestor this walk did not find"}`;
        }, i);
        if (bad) hits.push(`${name}: ${bad}`);
      }
      links += n;
    }
    await op.close();
    checked += links;
    ok(seen >= 40,
       `the invisible-link sweep read only ${seen} families — it has stopped ` +
       `finding them`);
    ok(links >= 500,
       `the invisible-link sweep examined only ${links} links across ${seen} ` +
       `families — it has stopped finding them`);
    ok(hits.length === 0,
       `${hits.length} link(s) of ${links} paint nothing even with focus on ` +
       `them: ${hits.slice(0, 6).join(" | ")}. Present, placed, sized, ` +
       `keyboard-reachable and unseeable — which is the one fault no count ` +
       `on this site can report.`);
  }

  /* AND THE ZERO IS NOT ALWAYS ON THE LINK. THE SWEEP ABOVE WALKS
   * ANCESTORS; THIS ONE WALKS IN.
   *
   * `.doorgo` is the homepage doors' hover-reveal — `opacity: 0` at rest,
   * restored by `.door:hover` and by a `max-width: 60rem` rule — and the
   * commit that documented what it cost on /experiences put the same class
   * on the /stories ledger lead's call to action. Measured in Chromium:
   * `Read the story` at 1280 is 544 x 33 with computed `opacity: 0` and
   * `checkVisibility` false, and `opacity: 1` at 390. So the one call to
   * action on the editorial ledger existed for phones and painted nothing
   * on every desk.
   *
   * THE SWEEP ABOVE PASSED IT, CORRECTLY, AND THAT IS THE FINDING.
   * `.storylead` IS the anchor and the anchor is visible; the `<p>` inside
   * it is what carries the alpha. `checkVisibility` on an element is false
   * when the element or an ANCESTOR is transparent, so asking it of every
   * link cannot see a transparent child, and the ancestor walk that names
   * the culprit starts at the link and goes up. The guard was written for
   * the element that is the link, and a class carrying an unexpected zero
   * is not always the link.
   *
   * IT ASKS ONLY OF ELEMENTS THAT HOLD THEIR OWN WORDS, because those are
   * the ones a reader loses: an element with element children is a box and
   * its text belongs to something deeper. And it FOCUSES the link first,
   * for the same reason the sweep above does — a hover-revealed child is a
   * pattern this site ships and every one of those reveals on
   * `:focus-visible` too. */
  {
    const FAM = require("./lib/families.js").ALL;
    const ip = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const inhits = [];
    let infams = 0, inwords = 0;
    for (const [name, url] of FAM) {
      const r = await ip.goto(base + url, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      infams++;
      /* The fast pass focuses each link once and collects the transparent
       * text-bearing children under it; the slow pass waits out that
       * element's own transition and asks again, which is the two-pass
       * shape the sweep above needed for exactly the same reason. */
      const n = await ip.evaluate(() => {
        window.__IL = [];
        const links = [...document.querySelectorAll("main a[href], footer a[href]")]
          .filter(a => a.checkVisibility() && !a.closest("[aria-hidden='true']"));
        for (const a of links) {
          a.focus();
          for (const e of a.querySelectorAll("*")) {
            if (e.children.length) continue;
            if (!(e.textContent || "").trim()) continue;
            if (e.closest("[aria-hidden='true']")) continue;
            if (!e.checkVisibility()) continue;
            if (!e.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true }))
              window.__IL.push(e);
          }
        }
        window.__ILN = links.length;
        return window.__IL.length;
      });
      inwords += await ip.evaluate(() => window.__ILN);
      for (let i = 0; i < n; i++) {
        const bad = await ip.evaluate(async (i) => {
          const e = window.__IL[i];
          const a = e.closest("a[href]");
          if (a) a.focus();
          const anims = [];
          for (let x = e; x && x !== document.documentElement; x = x.parentElement)
            anims.push(...x.getAnimations());
          await Promise.race([
            Promise.all(anims.map(z => z.finished.catch(() => {}))),
            new Promise(r => setTimeout(r, 400)),
          ]);
          if (e.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true }))
            return null;
          let z = e, at = "";
          while (z && z !== document.documentElement) {
            if (getComputedStyle(z).opacity === "0") {
              at = z.tagName.toLowerCase() +
                   (z.className ? "." + z.className.toString().trim().split(/\s+/)[0] : "");
              break;
            }
            z = z.parentElement;
          }
          const cls = e.className ? "." + e.className.toString().trim().split(/\s+/)[0] : e.tagName.toLowerCase();
          return `${cls} "${(e.textContent || "").trim().slice(0, 24)}" — zero alpha on ${at || "something this walk did not find"}`;
        }, i);
        if (bad) inhits.push(`${name}: ${bad}`);
      }
    }
    await ip.close();
    checked += inwords;
    ok(infams >= 40,
       `the transparent-child sweep read only ${infams} families — it has ` +
       `stopped finding them`);
    ok(inwords >= 500,
       `the transparent-child sweep looked inside only ${inwords} links ` +
       `across ${infams} families — it has stopped finding them`);
    ok(inhits.length === 0,
       `${inhits.length} element(s) inside a link hold words and paint ` +
       `nothing even with focus on the link: ` +
       `${inhits.slice(0, 6).join(" | ")}. The link is visible and its own ` +
       `words are not, which is why asking the question of the link cannot ` +
       `find this.`);
  }

  /* A PLACEHOLDER A READER CANNOT READ IS A TUTORIAL WITH ITS LAST LINE
   * MISSING.
   *
   * The planner's sentence box is the one control that page IS, and its
   * example is what teaches somebody what the parser reads — days, budget,
   * a starting city, interests. At 390 the box was 88px and the placeholder
   * needed 116, so "mountains and food" was cut off below the fold of a box
   * two lines tall. The clipped-text scan cannot see it: a textarea is a
   * scroll container, and scrolling IS the right answer inside one once
   * there is content. It is not the right answer for a hint.
   */
  {
    const tp = await browser.newPage({ viewport: { width: 390, height: 900 } });
    for (const W of [320, 390, 834, 1280]) {
      await tp.setViewportSize({ width: W, height: 900 });
      const r = await tp.goto(base + "/plan/", { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      const got = await tp.evaluate(() => {
        const t = document.querySelector("#ask");
        if (!t) return null;
        const v = t.value;
        t.value = t.placeholder;
        const o = { c: Math.round(t.clientHeight), s: Math.round(t.scrollHeight) };
        t.value = v;
        return o;
      });
      if (!got) { checked++; ok(false, `/plan at ${W}: no sentence box`); continue; }
      checked++;
      ok(got.s <= got.c + 1,
         `/plan at ${W}: the sentence box shows ${got.c}px of a placeholder ` +
         `that needs ${got.s}. The example is what teaches a reader what the ` +
         `planner understands, and its last line was under the fold of the box`);
    }
    await tp.close();
  }

  /* NO HEADING ENDS ON AN ORPHAN.
   *
   * `text-wrap: balance` was on seven elements, chosen one at a time
   * wherever somebody looked at a page. Measured across 668 headings on
   * twenty-two pages at 390: thirty run to more than one line and FIVE of
   * those ended on a last line under a third of the widest — the worst a
   * 24-pixel last line under a 341-pixel one on /how-it-works, which is two
   * characters alone under a heading.
   *
   * It is one declaration on `h1, h2, h3, h4` now, and this is what keeps
   * it: a heading that breaks badly is a typographic defect nothing else
   * here counts, and the browser's own line-breaker is the only thing that
   * can see it. Measured with Range rects, because a heading's box tells
   * you nothing about where its lines fall.
   */
  {
    const OP = ["/", "/countries/", "/europe/italy/", "/europe/austria/tyrol/",
      "/europe/france/alps-and-east/chamonix/", "/experiences/",
      "/journeys/", "/stories/", "/events/", "/themes/", "/interests/",
      "/beyond-the-obvious/", "/about/", "/method/", "/how-it-works/", "/fund/"];
    for (const W of [390, 1280]) {
      const op = await browser.newPage({ viewport: { width: W, height: 900 } });
      const bad = [];
      let seen = 0;
      for (const u of OP) {
        const r = await op.goto(base + u, { waitUntil: "load" });
        if (!r || r.status() !== 200) continue;
        const got = await op.evaluate(() => {
          const out = [];
          const range = document.createRange();
          for (const h of document.querySelectorAll("main h1, main h2, main h3")) {
            const t = (h.textContent || "").trim();
            if (!t || h.closest(".visually-hidden")) continue;
            range.selectNodeContents(h);
            const rects = [...range.getClientRects()].filter((x) => x.width > 1);
            const tops = [...new Set(rects.map((x) => Math.round(x.top)))];
            if (tops.length < 2) { out.push([t, false]); continue; }
            const wide = (tp) => rects.filter((x) => Math.round(x.top) === tp)
              .reduce((a, x) => a + x.width, 0);
            const last = wide(Math.max(...tops));
            const full = Math.max(...tops.map(wide));
            out.push([t, last < full * 0.34, Math.round(last), Math.round(full)]);
          }
          return out;
        });
        for (const [t, isOrphan, lw, fw] of got) {
          seen++;
          if (isOrphan) bad.push(`${u} "${t.slice(0, 40)}" ${lw}/${fw}px`);
        }
      }
      await op.close();
      checked++;
      ok(seen > 300,
         `the orphan scan read ${seen} headings at ${W} and this site has ` +
         `hundreds — it has stopped finding them`);
      checked++;
      ok(bad.length === 0,
         `${bad.length} heading(s) end on a line under a third of their widest ` +
         `at ${W}: ${bad.slice(0, 3).join("; ")}. text-wrap: balance is on every ` +
         `heading and something is overriding it`);
    }
  }

  /* THE PHOTOGRAPH ROW AT EVERY LENGTH THE LIBRARY CAN REACH.
   *
   * This was written against the homepage's four-door strip, which had four
   * photograph slots and a rule saying "the strip is composed at every step
   * rather than only when all four are licensed". Rendered with stand-in
   * pictures it jumped 304px to 522 the moment the FIRST one landed and the
   * three unfilled doors became holes.
   *
   * THE STRIP IS GONE — the plate sequence replaced it — AND THE SUITE
   * CRASHED ON ITS ABSENCE rather than reporting it: `.wayin` was null,
   * `getBoundingClientRect` threw, and every assertion after this point in
   * the file never ran. That is the second time in two runs a missing
   * element has taken the whole gate dark, which is worse than a red one
   * because nobody reads a run that did not finish.
   *
   * The promise outlived the component. Plate 02 draws one thumbnail per
   * theme that HOLDS a photograph, and its own comment makes the same claim:
   * "It grows to the full thirteen as the library fills and the layout does
   * not change." That is testable without touching the register — remove
   * tiles and re-measure — and it is a live claim rather than a vacuous one,
   * because the row got it wrong this morning: a grid item's automatic
   * minimum is its min-content, so RENAISSANCE refused its track and three
   * tile widths appeared in a row of eight equal columns.
   */
  {
    /* THE COMPONENT THIS CHECK WAS WRITTEN FOR HAS LEFT THE SITE. It read
     * `.qtile`, the homepage's row of theme photographs, and measured the
     * promise that every tile is one slot in one row whatever the library
     * holds. `.qtile` appears on ZERO pages and in no page builder — the
     * homepage became the plate sequence and the row went with it — and the
     * check has been reporting "it examined 0 states" ever since, which is
     * its own guard working and nobody reading it. Its five stylesheet rules
     * were left behind too and are deleted in this commit.
     *
     * The promise did not leave with the component. `.moswrap` on /discover
     * is the same claim in a stronger form: the composition follows the
     * COUNT, so the set can grow as the library fills and no cell is ever
     * left empty. That is testable the same way — remove tiles and
     * re-measure — and it is a live claim rather than a vacuous one, because
     * the first version of that grid typed four columns and stranded two
     * tiles on a third row beside two empty cells.
     */
    const dp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const r0 = await dp.goto(base + "/discover", { waitUntil: "load" });
    const seen = [];
    if (r0 && r0.status() === 200) {
      const full = await dp.locator(".mosrest .mos").count();
      for (let drop = 0; drop < Math.min(4, full); drop++) {
        await dp.goto(base + "/discover", { waitUntil: "load" });
        await dp.evaluate((d) => {
          const t = [...document.querySelectorAll(".mosrest .mos")];
          t.slice(t.length - d).forEach((x) => x.remove());
        }, drop);
        await dp.waitForTimeout(80);
        seen.push(await dp.evaluate(() => {
          const box = (e) => e.getBoundingClientRect();
          const rest = document.querySelector(".mosrest");
          const t = [...rest.querySelectorAll(".mos")];
          const lead = document.querySelector(".moswrap > .mos");
          return {
            n: t.length,
            widths: [...new Set(t.map((x) => Math.round(box(x).width)))],
            heights: [...new Set(t.map((x) => Math.round(box(x).height)))],
            /* A WIDE TILE IS THE COMPOSITION, NOT A DEFECT, and the first
             * version of this assertion refused the thing it was written to
             * protect. Where the smalls are an odd number the LAST one spans
             * both columns, because that is the one case a two-column block
             * would otherwise leave a cell empty in. So the promise is not
             * "one width": it is that every tile is either one slot or two,
             * and only the last may be two. */
            wide: t.map((x, i) => Math.round(box(x).width) > Math.round(box(t[0]).width) + 2
                                  ? i : -1).filter((i) => i >= 0),
            /* A HOLE IS A ROW THE LAST TILE DOES NOT REACH THE END OF.
             * With an odd number of smalls the last one spans both
             * columns, so the right-hand block's own right edge is the
             * right edge of its last tile — whatever the count. */
            gap: Math.round(box(rest).right - box(t[t.length - 1]).right),
            /* AND THE LEAD IS AS TALL AS THE GRID BESIDE IT. That is what
             * `grid-row: 1 / -1` could not do and a sibling grid can. */
            leadDelta: Math.round(box(lead).height - box(rest).height),
          };
        }));
      }
    }
    await dp.close();
    checked++;
    ok(seen.length >= 2,
       `the photographic response was not found on /discover — it examined ` +
       `${seen.length} states, and this check has already once gone dark on a ` +
       `component that left`);
    for (const st of seen) {
      checked++;
      ok(st.widths.length <= 2 && st.wide.every((i) => i === st.n - 1),
         `with ${st.n} tiles the response draws ${st.widths.length} widths ` +
         `(${st.widths.join(", ")}px) and the wide one(s) are at ` +
         `${st.wide.join(", ") || "none"} of ${st.n - 1}. Every tile is one ` +
         `slot or two, and only the last may be two — which is the rule that ` +
         `makes the block hole-free at an odd count`);
      checked++;
      ok(st.gap <= 1,
         `with ${st.n} tiles the last one stops ${st.gap}px short of the ` +
         `grid's right edge — that gap is an empty cell, which is the fault ` +
         `this composition exists to make impossible at every count`);
      checked++;
      ok(Math.abs(st.leadDelta) <= 2,
         `with ${st.n} tiles the lead is ${st.leadDelta}px taller than the ` +
         `grid beside it. The lead has no height of its own: it stretches to ` +
         `whatever the rest resolve to, which is the whole reason they are a ` +
         `separate grid`);
    }

  }

  /* THE YEAR BAND'S CAPTION NAMES A LINE, MEASURED ON THE PAINTED PIXEL.
   *
   * "Above the line is what is on. Below it is how many countries are in
   * their quieter shoulder" — and the axis that sentence depends on was
   * --rule, which sampled rgb(231,230,223) against a page of
   * rgb(247,246,243): 1.16:1. A reader had to infer the line from where the
   * bars stop.
   *
   * It is measured on the PIXEL rather than on the token because a 1px line
   * in a viewBox scaled by preserveAspectRatio="none" does not land on a
   * device pixel: --ink-2 at 1px sampled 2.59 where the token itself is far
   * darker, and only 1.5 clears the 3:1 that SC 1.4.11 puts on the boundary
   * of a graphical object. The declaration was never the thing a reader
   * gets.
   */
  {
    for (const [u, W] of [["/events/", 1280], ["/events/", 390]]) {
      const yp = await browser.newPage({ viewport: { width: W, height: 900 } });
      const r = await yp.goto(base + u, { waitUntil: "load" });
      if (!r || r.status() !== 200) { await yp.close(); continue; }
      await yp.waitForTimeout(150);
      // SCROLL IT INTO THE SHOT FIRST. `screenshot()` without `fullPage`
      // photographs the VIEWPORT, and the year band sits at y=905 on a
      // 900-pixel page — so every sample landed outside the image and came
      // back as the canvas, which reads 1.00:1 whatever the drawing does.
      // The check reported the baseline invisible at both widths on a band
      // whose line measures 9.36, and it would have gone on doing that for
      // any change that made /events one band taller. That is the aperture
      // sampler's own recorded failure, in a check written after it and
      // without its guard.
      await yp.locator(".ybars").first().scrollIntoViewIfNeeded();
      await yp.waitForTimeout(120);
      const box = await yp.evaluate(() => {
        const e = document.querySelector(".ybars");
        if (!e) return null;
        const b = e.getBoundingClientRect();
        // BASE is 66 of the 104-unit viewBox; the box scales vertically.
        // The arithmetic was right all along — with the band in the shot,
        // `b.y + 66 * (b.height / 104)` lands on the stroke at both widths.
        // An offset was tried and moved the sample OFF it, which is worth
        // recording: when a sampler reports 1.00 the first question is
        // whether it is looking at the drawing at all, not whether it is
        // looking a pixel too high.
        return { x: Math.round(b.x + 4), y: Math.round(b.y + 4),
                 base: Math.round(b.y + 66 * (b.height / 104)),
                 h: Math.round(window.innerHeight) };
      });
      if (!box) { checked++; ok(false, `${u} at ${W}: no year band`); await yp.close(); continue; }
      const shot = (await yp.screenshot()).toString("base64");
      const got = await yp.evaluate(async ({ d, pts }) => {
        const img = await new Promise((res) => {
          const i = new Image(); i.onload = () => res(i);
          i.src = "data:image/png;base64," + d;
        });
        const c = document.createElement("canvas");
        c.width = img.width; c.height = img.height;
        const x = c.getContext("2d");
        x.drawImage(img, 0, 0);
        const lum = (p) => {
          const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
          return 0.2126 * f(p[0]) + 0.7152 * f(p[1]) + 0.0722 * f(p[2]);
        };
        const at = (px, py) => lum(x.getImageData(px, py, 1, 1).data);
        // A STROKE IS CENTRED ON ITS GEOMETRIC LINE, SO IT LANDS BETWEEN
        // DEVICE PIXELS. `b.y + 66 * (b.height / 104)` is where the line IS;
        // a 2px non-scaling stroke straddles it, and which row comes back
        // solid depends on where that lands in the device grid — row 971 at
        // 1280 and row 501 at 390, one either side of the same arithmetic.
        // Sampling one exact row therefore read the line at one width and an
        // anti-aliased blend at the other, and reported 1.54 for a line that
        // measures 8.26 where it is solid.
        //
        // The aperture check already answers this: look for the greatest
        // step from the ground within a small window, because that is what a
        // cut edge IS. A reader sees whichever row is solid.
        const page = at(pts.x, pts.y);
        let base = page;
        for (let dy = -2; dy <= 2; dy++) {
          const v = at(pts.x, pts.base + dy);
          if (Math.abs(v - page) > Math.abs(base - page)) base = v;
        }
        return { base, page };
      }, { d: shot, pts: box });
      await yp.close();
      const cr = (Math.max(got.base, got.page) + 0.05) /
                 (Math.min(got.base, got.page) + 0.05);
      checked++;
      // A sampler that reads outside its own image reports the canvas. Say
      // so, rather than reporting the drawing.
      ok(box.base < box.h && box.y >= 0,
         `${u} at ${W}: the year-band sampler read outside the shot — ` +
         `baseline at ${box.base} on a ${box.h}px viewport. Every sample ` +
         `comes back as the canvas and the ratio is about nothing`);
      ok(cr >= 3.0,
         `${u} at ${W}: the year band's baseline measures ${cr.toFixed(2)}:1 ` +
         `against the page on the painted pixel. The caption says "above the ` +
         `line" and a reader has to be able to see the line — SC 1.4.11 puts ` +
         `the boundary of a graphical object at 3:1`);
    }
  }

  /* MY EUROPE DRAWS THE LIST IT IS ABOUT, and only a browser can see it.
   *
   * The empty case is the state this page SHIPS in — the list is empty
   * until somebody saves something — and it was a heading, a paragraph and
   * three bordered boxes on graphite, with no picture, on the one page
   * whose subject is a set of PLACES. The continent is server-rendered
   * with nothing on it and the marks are lit from /api/atlas.json.
   *
   * Nothing static can check this: the dots exist only after localStorage
   * has something in it and the Atlas index has resolved the ids. So the
   * suite writes a real saved list, reloads, and reads the drawing.
   */
  {
    const mp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const r = await mp.goto(base + "/my-europe/", { waitUntil: "load" });
    if (r && r.status() === 200) {
      checked++;
      ok(await mp.$(".minemap .constel"),
         "/my-europe draws no continent. The empty state is the state this " +
         "page ships in and it is the one page whose subject is a set of places");
      const empty = await mp.textContent("#minecap");
      checked++;
      ok(/nothing on it yet/i.test(empty || ""),
         `/my-europe empty caption reads ${JSON.stringify(empty)} and must say the ` +
         `drawing is empty rather than leaving a reader to count zero dots`);
      await mp.evaluate(() => localStorage.setItem("europedoor.saved.v1", JSON.stringify([
        { id: "city:france/alps-and-east/chamonix", kind: "Place", label: "Chamonix", url: "/x" },
        { id: "city:norway/fjord-norway/bergen", kind: "Place", label: "Bergen", url: "/x" },
        { id: "journey:the-alpine-grand-tour", kind: "Journey", label: "Alpine", url: "/x" }])));
      await mp.reload({ waitUntil: "networkidle" });
      await mp.waitForTimeout(400);
      const got = await mp.evaluate(() => ({
        dots: document.querySelectorAll(".minemap .constel-lit circle").length,
        cap: (document.getElementById("minecap") || {}).textContent || "" }));
      checked++;
      ok(got.dots === 2,
         `/my-europe lit ${got.dots} mark(s) for two saved places and a saved ` +
         `journey. A journey has no single point and must not be given one`);
      // AND THE TWO COUNTS HAVE TO AGREE OR THE DIFFERENCE HAS TO BE SAID.
      // The heading under the drawing counts saved ITEMS and only places
      // carry a point, so three dots under a heading reading five is a
      // discrepancy a reader sees and nothing explains.
      checked++;
      ok(/2 of your 3/.test(got.cap),
         `/my-europe caption reads ${JSON.stringify(got.cap)} — with two of three ` +
         `saved items drawn it has to say so, or the dots and the heading ` +
         `disagree with nothing accounting for it`);
      await mp.evaluate(() => localStorage.removeItem("europedoor.saved.v1"));
    }
    await mp.close();
  }

  /* A SEPARATION BETWEEN TWO TOKENS SAYS NOTHING ABOUT WHETHER EITHER IS
   * PAINTED.
   *
   * docs/palette.json declares --map-land against --map-sea at 1.8, with
   * the reason spelled out: "the land is a mass, not a hairline. Europe is
   * what the light falls on — the hero's reading, applied to the
   * instrument." checks.py recomputes that ratio from the hexes in the
   * stylesheet, and it has been green since the day it was written.
   *
   * /discover drew all fifty countries with `fill: none`. Unfilled outlines
   * at one pixel on #0b0e11 under 319 dots — a wireframe continent on
   * black, on the page whose whole job is to make a continent explorable.
   * The rule was older than its only user: it was written for a homepage
   * hero map that has since been removed, where an outline WAS the look.
   *
   * This is the pixel end of that claim. Every instrument that draws the
   * atlas has to PAINT the land, and the painted land has to clear the
   * painted water by what the register says. Reading the computed fill
   * rather than the token is the whole point: `none` and `#3b424c` are the
   * same declaration as far as the register is concerned.
   */
  {
    const palette = JSON.parse(fs.readFileSync(
      path.join(__dirname, "..", "docs", "palette.json"), "utf8"));
    const wantLand = (palette.cartography.separations.find(
      (r) => r.a === "--map-land" && r.b === "--map-sea") || {}).min || 1.8;
    const ip = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    for (const u of ["/discover/", "/map/"]) {
      const r = await ip.goto(base + u, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      const got = await ip.evaluate(() => {
        const svg = [...document.querySelectorAll("svg")]
          .find((e) => e.getBoundingClientRect().width > 400);
        if (!svg) return null;
        // EVERY drawn country path, not the <a> or <g> around it. Those
        // paint nothing and compute to the SVG default black, and the
        // first version of this check read one of them and reported /map
        // at 1.12 against a real 1.91 — an instrument that does not
        // recognise the good case it was written to protect, which this
        // repository has now built twice.
        const paths = [...svg.querySelectorAll(".countries path")];
        const tally = {};
        for (const e of paths) {
          const f = getComputedStyle(e).fill;
          tally[f] = (tally[f] || 0) + 1;
        }
        const land = Object.keys(tally).sort((a, c) => tally[c] - tally[a])[0];
        const ground = svg.querySelector(".archground") ||
                       svg.querySelector(".lyr-ocean rect");
        const bg = getComputedStyle(document.body).backgroundColor;
        return { land: land || null, n: paths.length,
                 fills: Object.keys(tally).length,
                 sea: ground ? getComputedStyle(ground).fill : bg };
      });
      checked++;
      if (!got || !got.land) { ok(false, `${u}: no drawn country shape found`); continue; }
      ok(got.land !== "none" && !/rgba\(0, 0, 0, 0\)/.test(got.land),
         `${u}: the land computes to ${got.land} — the atlas is drawn as an ` +
         `outline, and docs/palette.json says the land is a mass rather than ` +
         `a hairline`);
      const rgb = (c) => (c.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
      const lum = (c) => { const v = rgb(c); if (v.length < 3) return null;
        const f = v.map((x) => { x /= 255; return x <= 0.03928 ? x / 12.92
          : Math.pow((x + 0.055) / 1.055, 2.4); });
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]; };
      const a = lum(got.land), bl = got.sea ? lum(got.sea) : null;
      if (a !== null && bl !== null) {
        const cr = (Math.max(a, bl) + 0.05) / (Math.min(a, bl) + 0.05);
        checked++;
        ok(cr >= wantLand - 0.02,
           `${u}: the painted land measures ${cr.toFixed(2)}:1 against the ` +
           `painted water and docs/palette.json requires ${wantLand}. ` +
           `Measured on the pixels, not on the tokens`);
      }
    }
    await ip.close();
  }

  /* THE OTHER END OF THE CROP RULE: the box a photograph would sit in.
   *
   * data/image-purposes.json declares a `container` aspect range per slot
   * and derives `safe_area` from it, and checks.py owns that arithmetic.
   * Arithmetic on a declared number proves nothing about the page — the
   * palette register asserted a contrast for a colour the stylesheet no
   * longer had, for exactly this reason. So this end MEASURES.
   *
   * The measurement is possible without a photograph because the class a
   * photograph adds can be added here: `.shot` on the element, and the
   * drawing a photograph would replace removed. That is DOM, not style
   * injection — the CSP forbids the second and is right to.
   *
   * The numbers this produced the first time are the whole reason the rule
   * exists: the homepage hero's box swings 0.435 to 2.326, so 15% of a
   * source frame is guaranteed visible, and the four doors 14%. An
   * off-centre composition is unusable in either.
   */
  /* AND THE LIST OF SURFACES IS DERIVED, BECAUSE A TYPED ONE WENT ON
   * REPORTING GREEN ABOUT SIX SURFACES OUT OF SEVEN.
   *
   * The list was three entries typed by hand. Two of the three named an
   * element the site no longer has: `.way`, which left when the four
   * homepage doors became the plate sequence, and `.herofull`, which left
   * in the same commit — `homepage-hero` renders inside `.opening` on
   * plate 01. A selector that matches nothing has no aspect ratio, so `lo`
   * stayed Infinity and `hi` stayed -Infinity, and `Infinity >= min` and
   * `-Infinity <= max` are BOTH true: two green assertions per run, about
   * nothing, for the life of the plate sequence.
   *
   * That is this repository's own recorded failure twice over — the check
   * matching `pointsmap arched"><svg` that examined 0 dots on a site with
   * 130 region maps, and the one-plate-per-thing check that read zero once
   * the last abstract plate came off. Both were found by READING THE COLUMN
   * OF COUNTS, which does not exist here: `ok()` counts an assertion made,
   * and an assertion about an empty set counts exactly like one about a
   * page.
   *
   * THE THIRD ENTRY WAS WORSE THAN THE TWO THAT MATCHED NOTHING, BECAUSE IT
   * MATCHED AND MEASURED THE WRONG STATE. `.iheroart` holds the drawing
   * until a photograph replaces it, and the check added `.shot` — the class
   * the build adds — WITHOUT taking the drawing out. Measured both ways at
   * twenty viewports:
   *
   *     .iheroart with the drawing in it    1.333 – 1.500
   *     .iheroart with a photograph in it   0.692 – 1.500
   *
   * so the declared floor of 1.333 was a fact about the page as it is and
   * not about the page a photograph makes, and the guaranteed frame it
   * produced — 55% — was nearly double the real 29%. *A code path nothing
   * exercises is a code path nothing checks*, about the one measurement
   * whose entire subject is a state the register has never been in.
   *
   * So: the SET comes from the declarations, and the SIMULATION is the
   * whole substitution rather than half of it — the drawing and any empty
   * slot come out, a picture goes in, and `.shot` goes on. Surfaces are
   * grouped by SELECTOR, because a crop box is a property of a component
   * rather than of a page: `.iheroart.shot` exists on /journeys and not yet
   * on /experiences or /stories, whose openings render no figure at all
   * until a photograph exists, and measuring the component once is the only
   * way to say anything true about either. Each group asserts its own
   * REACH, so a selector that matches nothing on any of its pages fails and
   * names them instead of satisfying both bounds by having no value. */
  {
    /* AND THE TEN TEMPLATED SLOTS WERE IN NOBODY'S SET AT THIS END.
     * `checks.py`'s own `c_photo_safe_area` merges `slots` into `purposes`
     * with the reason written on it — "a slot's crop rule is the same claim
     * as a purpose's, and a template that escaped this check would be 319
     * pages of unchecked crop" — and this end, whose comment says the two
     * exist so that "neither can drift without the other noticing", read
     * `.purposes` alone. So the arithmetic covered seventeen entries and the
     * measurement covered seven, and the ten it never looked at are every
     * templated family on the site: 319 destinations, 255 places, 130
     * regions, 50 countries. A rule stated once and applied to one of its
     * call sites, in the pair of checks written to keep each other honest. */
    const spec = JSON.parse(fs.readFileSync(
      path.join(__dirname, "..", "data", "image-purposes.json"), "utf8"));
    const purposes = { ...spec.purposes, ...spec.slots };
    /* the registry is where a surface's PATH is declared, and it is
     * generated and stale-checked; a second copy typed here is the fault
     * above in a different field. */
    const regrows = JSON.parse(fs.readFileSync(
      path.join(__dirname, "..", "desk", "registry.json"), "utf8")).purposes;
    const pathOf = new Map(regrows.map((r) => [r.purpose, r.path]));
    /* A SLOT HAS NO PATH OF ITS OWN — the registry keys its INSTANCES
     * (`destination-hero@albania/.../theth`) and carries the slot name
     * beside each. So a slot's pages are a sample of its instances, spread
     * across the list rather than taken from the front: this session's first
     * reading of `.placeband-art` sampled twelve destinations, reported the
     * container as 1.500-1.778 and was wrong, because all twelve happened to
     * be 3:2 sources and the 26 at 16:9 and the one at 2.125 were further
     * down the alphabet. A sample that is not spread is a fact about its own
     * first entries. */
    const slotPaths = new Map();
    for (const r of regrows) {
      if (!r.slot || !r.path) continue;
      if (!slotPaths.has(r.slot)) slotPaths.set(r.slot, []);
      slotPaths.get(r.slot).push(r.path);
    }
    const SAMPLE = 6;
    const sampleOf = (slot) => {
      const all = slotPaths.get(slot) || [];
      if (all.length <= SAMPLE) return all;
      const step = (all.length - 1) / (SAMPLE - 1);
      return [...new Set(Array.from({ length: SAMPLE },
        (_, i) => all[Math.round(i * step)]))];
    };
    const groups = new Map();
    for (const [of_, v] of Object.entries(purposes)) {
      const con = v.container;
      if (!con || !con.selector || con.unmeasurable) continue;
      const sel = con.selector.replace(/\.shot\b/g, "").trim();
      if (!groups.has(sel)) groups.set(sel, { sel, want: con, of: [], urls: [] });
      const g = groups.get(sel);
      g.of.push(of_);
      const us = pathOf.has(of_) ? [pathOf.get(of_)] : sampleOf(of_);
      for (const u of us) if (u && !g.urls.includes(u)) g.urls.push(u);
      /* AND THE EQUALITY ASSERTION THAT USED TO SIT HERE WAS TRUE TODAY AND
       * UNSOUND IN GENERAL. It said two purposes naming one component may
       * not declare two boxes, "because a crop box is a property of the
       * component" — which holds for `.iheroart`, whose own rule is
       * `aspect-ratio: 4/3`, and fails for a component sized by its parent.
       * Measured: `.headshot` is 0.692-1.333 inside a theme page's
       * `.ed-opening-visual` and 0.941-1.129 inside a country page's
       * `.pagehead.opening` — one class, two real boxes, because the class
       * sets no ratio of its own and the two families put it in different
       * grids. An assertion that is green today and wrong in principle is
       * the landmine this repository keeps recording, so it is gone.
       *
       * Nothing is lost: the group measures the UNION over every path its
       * purposes declare, so two families whose real boxes differ produce a
       * union wider than either declaration and the two bounds below fail
       * and name it. The union is the stronger test AND the honest one —
       * the remedy it points at is separate selectors, not one number. */
    }
    ok(groups.size > 0,
       "no purpose in data/image-purposes.json declares a measurable "
       + "container, so the crop-box measurement has nothing to measure and "
       + "the safe-area arithmetic in checks.py is unchecked against the "
       + "real page");
    const WS = [320, 390, 480, 760, 834, 980, 1280, 1440, 1800, 2000];
    const HS = [640, 900];
    for (const g of groups.values()) {
      ok(g.urls.length > 0,
         `${g.of.join(", ")} declare the container ${g.sel} and `
         + `desk/registry.json gives none of them a path, so there is no `
         + `page on which to measure the box`);
      if (!g.urls.length) continue;
      let lo = Infinity, hi = -Infinity, loAt = "", hiAt = "";
      let boxes = 0, loaded = 0;
      for (const url of g.urls) for (const w of WS) for (const h of HS) {
        const bp = await browser.newPage({ viewport: { width: w, height: h } });
        const r = await bp.goto(base + url, { waitUntil: "load" });
        if (!r || r.status() !== 200) { await bp.close(); continue; }
        loaded++;
        /* THE SUBSTITUTION IS THE WHOLE ONE. `.shot` is the class the build
         * adds; the drawing and the empty slot are what a photograph
         * REPLACES, and a box measured around either is a box no photograph
         * will ever be in. The stand-in carries real dimensions so the
         * figure is not laid out as a broken image — measured with and
         * without a loading source, the numbers are identical, and the one
         * that cannot be argued with is the one that loads. */
        await bp.evaluate((sel) => {
          for (const e of document.querySelectorAll(sel)) {
            e.classList.add("shot");
            for (const k of e.querySelectorAll(".ed-slot, svg, .constel")) k.remove();
            if (!e.querySelector("picture")) {
              const pic = document.createElement("picture");
              const img = document.createElement("img");
              img.width = 2000; img.height = 1200; img.alt = "";
              img.src = "data:image/svg+xml;charset=utf8," + encodeURIComponent(
                '<svg xmlns="http://www.w3.org/2000/svg" width="2000" '
                + 'height="1200"><rect width="2000" height="1200" '
                + 'fill="#888"/></svg>');
              pic.appendChild(img);
              e.appendChild(pic);
            }
          }
        }, g.sel);
        const got = await bp.evaluate((sel) => [...document.querySelectorAll(sel)]
          .map((e) => e.getBoundingClientRect())
          .filter((r) => r.width > 4 && r.height > 4)
          .map((r) => r.width / r.height), g.sel);
        await bp.close();
        boxes += got.length;
        for (const a of got) {
          if (a < lo) { lo = a; loAt = `${w}x${h}`; }
          if (a > hi) { hi = a; hiAt = `${w}x${h}`; }
        }
      }
      /* THE REACH FIRST, because both bounds below are satisfied by an
       * empty set and neither says so. The message carries the numbers that
       * separate the three ways this fails — the pages did not load, they
       * loaded and the selector matched nothing, or it matched something
       * too small to be a picture. */
      const want = g.want;
      ok(boxes > 0,
         `${g.of.join(", ")}: the container ${g.sel} matched no box larger `
         + `than 4px on ${g.urls.join(", ")} at any of `
         + `${g.urls.length * WS.length * HS.length} viewports (${loaded} `
         + `loaded). Its declared box is being asserted against nothing: an `
         + `empty set satisfies the floor and the ceiling at once, because `
         + `Infinity >= ${want.min_aspect} and -Infinity <= `
         + `${want.max_aspect} are both true`);
      if (boxes === 0) continue;
      ok(lo >= want.min_aspect - 0.02,
         `${g.of.join(", ")}: the container measures ${lo.toFixed(3)} at ` +
         `${loAt} and the file declares a floor of ${want.min_aspect}. A box ` +
         `narrower than declared crops more width than the safe area allows`);
      ok(hi <= want.max_aspect + 0.02,
         `${g.of.join(", ")}: the container measures ${hi.toFixed(3)} at ` +
         `${hiAt} and the file declares a ceiling of ${want.max_aspect}. A ` +
         `box wider than declared crops more height than the safe area allows`);
    }
  }

  /* THE PAGE'S OWN TYPE STANDS OVER THE REGISTER'S DRAWING, AND THE DRAWING
   * DID NOT KNOW.
   *
   * `place_label_box` tests every label against the frame, against its own
   * country's ground and against every box already taken — and what was in
   * `taken` on plate 05 was only the labels that drawing placed itself. The
   * headline and the region card are set ON the continent, in the page's
   * own grid, and the name layer had never heard of either: measured at
   * 1280, ICELAND ran 109 pixels through `One continent. Fifty doors.`; at
   * 1920 six names collided; at 2560 UNITED KINGDOM ran 256 pixels through
   * the headline. The wash under the column is why nobody called it a
   * contrast fault — a name arrives faintly through a 76px serif rather
   * than being deleted by it, which is worse than either.
   *
   * `ATLAS_TYPE_ZONES` WAS THE REPAIR AND THE COMPOSITION REPLACED IT.
   * That reserve was a union over 385 samples of where the headline and the
   * card land in the projection's own units, seeded into the label placer's
   * `taken` so a country name could not be set under either. It cost six of
   * the seventeen names and it was the right trade while the type stood on
   * the drawing.
   *
   * THE MAP IS THE RIGHT TWO THIRDS NOW, so the promise is stronger and
   * needs no declared number at all: the editorial column is WEST OF THE
   * FRAME. `.atlead` is `min(29%, 25rem)` and `.atread` is `min(30%, 23rem)`
   * against a `.atwin` that starts at 34%, so the column cannot reach the
   * drawing at any width by construction — and the same 385 samples report
   * the headline's union ending at x=140.7 and the card's at x=174.5 against
   * a frame that begins at x=201.
   *
   * THIS END MEASURES AND READS THE PAGE'S OWN viewBox. Arithmetic on a
   * declared number proves nothing about a page — the palette register
   * asserted a contrast for a colour the stylesheet no longer had, for
   * exactly this reason — and a constant two files have to agree on is what
   * four typed dispatch caps cost this repository a sitting. The frame's
   * left edge comes off the `<svg>` in front of the browser.
   *
   * The viewports are the ones the sweep found binding — 1152x640 drives the
   * headline's depth, 1024x1440 its width, 3440x1080 the card's left edge —
   * plus the three a reader is most likely on. A check that sampled only the
   * common widths would go green on a composition that is wrong on an
   * ultrawide, which is the state the reserve was written from.
   *
   * PROVED RED by serving the stylesheet with `.atlead` and `.atread`
   * widened to 60%: **30 failures over the eighteen samples** — both
   * elements at every one — each naming the element, the viewport, the
   * scroll position, the right edge measured and the frame's left edge,
   * against 0 of 18 as shipped. A check is not proved by passing.
   */
  {
    const VPS = [[1152, 640], [1024, 1440], [3440, 1080],
                 [1280, 900], [1920, 1080], [2560, 900]];
    let seen = 0;
    const onDrawing = [];
    for (const [w, h] of VPS) {
      const bp = await browser.newPage({ viewport: { width: w, height: h } });
      await bp.goto(base + "/", { waitUntil: "load" });
      for (const step of [0, 0.4, 0.85]) {
        const got = await bp.evaluate((s) => {
          const at = document.querySelector(".atlas");
          window.scrollTo(0, at.offsetTop + s * (at.offsetHeight - innerHeight));
          if (getComputedStyle(document.querySelector(".atstage")).position
              !== "sticky") return null;
          const svg = document.querySelector("#act5 svg.instrmap");
          const m = svg.getScreenCTM().inverse();
          const P = (x, y) => { const p = svg.createSVGPoint();
            p.x = x; p.y = y; const q = p.matrixTransform(m);
            return [q.x, q.y]; };
          const right = (e) => { if (!e) return null;
            const b = e.getBoundingClientRect(); if (!b.width) return null;
            return P(b.right, b.bottom)[0]; };
          let card = null;
          for (const c of document.querySelectorAll(".atcard")) {
            if (+getComputedStyle(c).opacity <= 0.5) continue;
            const r = right(c);
            if (r !== null) card = card === null ? r : Math.max(card, r);
          }
          return { mega: right(document.querySelector("#act5 .mega")), card,
                   frame: parseFloat(svg.getAttribute("viewBox").split(/\s+/)[0]) };
        }, step);
        if (!got) break;
        seen++;
        for (const k of ["mega", "card"]) {
          if (got[k] === null || got[k] === undefined) continue;
          if (got[k] > got.frame - 1)
            onDrawing.push(`${k === "mega" ? "headline" : "card"} at `
              + `${w}x${h}+${step} reaches x=${got[k].toFixed(1)} against a `
              + `frame beginning at x=${got.frame}`);
        }
      }
      await bp.close();
    }
    ok(seen >= 12,
       `the atlas register's editorial column was measured at only ${seen} `
       + `samples of ${VPS.length * 3}. The two-column composition has `
       + `stopped being sticky at widths this check assumes it is, so the `
       + `promise that the type never stands on the drawing is being `
       + `asserted about nothing`);
    ok(onDrawing.length === 0,
       "the page's own type has reached the atlas register's drawing, where "
       + "a country name may be set under it and the label placer has no "
       + "reserve any more: " + onDrawing.slice(0, 4).join("; "));
  }

  /* A PAGE'S BAND NUMBERS RUN 01, 02, 03 — AND ON 753 PAGES TWO OF THEM WERE
   * THE SAME NUMBER.
   *
   * There were two numbering systems. `section()` draws its index from a CSS
   * counter — `main` resets `band`, every `.band` increments it — with the
   * reason written on that rule: a number typed per call site is wrong the
   * day somebody reorders a page. The 2036 section head was then given the
   * number as its FIRST ARGUMENT, so a page carrying both shapes numbered
   * each sequence from one. A place page opened "01 · NEARBY / The rest of
   * Vienna" and then, directly under it, "01 / Other places in Vienna".
   *
   * THE DIGITS A READER SEES CANNOT BE READ BACK. `content` on a pseudo
   * element computes to the SPECIFIED value — `"0" counter(band)` — not to
   * the resolved string, so a first version of this check regex-matched that
   * literal "0" and reported nineteen of forty-seven families broken when
   * not one of them was. That is this repository's own instrument fault
   * again: the reading came from the model rather than from the page.
   *
   * So the assertion is the STRUCTURE that makes the sequence right, which
   * is exact and needs no digits. One reset on `main`; every element that
   * increments `band` also draws an index; every drawn index sits inside an
   * element that increments. Given those three, the numbers are 1..n by
   * construction — and each half is a real defect this has already had:
   * `.ed-section` drew an index and did not increment (two systems, the same
   * number twice), and `div.headmeta.ed-section` incremented and drew
   * nothing (every later number one too high, and no 01 on the page). */
  {
    const { ALL } = require("./lib/families.js");
    const seen = new Set();
    for (const [fam, url] of ALL) {
      if (seen.has(url)) continue;
      seen.add(url);
      const r = await page.goto(base + url, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      const st = await page.evaluate(() => {
        const incs = [], draws = [];
        for (const e of document.querySelectorAll("*")) {
          const ci = getComputedStyle(e).counterIncrement || "";
          if (/\bband\b/.test(ci)) incs.push(e);
          const head = e.matches(".band > .band-head")
            || e.matches(".ed-section-head > div > .ed-section-index");
          if (head) draws.push(e);
        }
        const name = (e) => e.tagName.toLowerCase()
          + (e.className ? "." + String(e.className).trim().replace(/\s+/g, ".") : "");
        const resets = [...document.querySelectorAll("*")].filter(
          (e) => /\bband\b/.test(getComputedStyle(e).counterReset || ""));
        return {
          resets: resets.length,
          silent: incs.filter((e) => !draws.some((d) => e.contains(d))).map(name),
          orphan: draws.filter((d) => !incs.some((e) => e.contains(d))).map(name),
          n: draws.length,
        };
      });
      checked++;   // one page read
      ok(st.resets === 1,
         `${fam} (${url}): the band counter is reset ${st.resets} times and `
         + `must be reset exactly once, on main — a second reset restarts the `
         + `numbering part-way down the page`);
      ok(st.silent.length === 0,
         `${fam} (${url}): ${st.silent.join(", ")} increments the band `
         + `counter and draws no number, so every band after it is one too `
         + `high and the page has no 01`);
      ok(st.orphan.length === 0,
         `${fam} (${url}): ${st.orphan.join(", ")} draws a band number and `
         + `nothing above it increments the counter, which is how two `
         + `numbering systems printed the same number on one page`);
    }
  }

  /* A LINK A READER CANNOT SEE IS NOT REACHABLE BECAUSE IT IS FOCUSABLE.
   *
   * Below 44rem the masthead's seven sections were one line that scrolled
   * sideways, and the comment above the rule called the mask fade at its
   * right edge "the affordance saying so". Measured: at 390 the row held
   * 552px of content in a 366px box, so PLAN, STORIES and EVENTS were
   * wholly off-screen, and at 320 JOURNEYS was too — three of seven
   * primary sections behind a horizontal swipe inside a 24px strip, with a
   * 44px gradient as the only signal that there was anything to swipe to.
   *
   * Nothing counted it. Every link was in the DOM, in the tab order, of
   * the right size and the right colour, and the document did not scroll
   * sideways — which is the thing the suite DID assert, because that is
   * the 47-pixel city-page overflow it was written for. Overflow contained
   * inside a scroller passes that check by design.
   *
   * So this asserts the promise instead: every visible link in the
   * masthead is inside the viewport. It is deliberately about VISIBLE
   * links — /discover, /plan and /my-europe are hidden here at this
   * breakpoint because the thumb bar carries all three at the same
   * breakpoint, and hiding a duplicate is not hiding a destination.
   *
   * AND THE GUTTERS MUST AGREE. `main` is padded --s4 on a phone and
   * `.masthead-in` was left on the desk's --s5, so the wordmark and the
   * whole navigation were indented eight pixels further than the h1, the
   * breadcrumb and every line of prose, on every page. Nothing counts a
   * gutter, and at thumbnail size nothing sees one.
   */
  /* ── A ROOM OPENS ITS FIELD FOR A KEYBOARD, AND THE ORDER IS THE TRICK ──
   * The bar names six rooms and two of them carry a field of four or five
   * links. The field is `display: none` until `:hover` or `:focus-within`,
   * with no JavaScript anywhere — this site loads no script on most of its
   * pages and a navigation that needed one would be the first script on the
   * homepage.
   *
   * `display: none` takes the field out of the tab order AND out of the
   * accessibility tree, so the thing that reveals it cannot be inside it.
   * It is the ROOM link, which is always visible and always focusable: Tab
   * reaches the room, `:focus-within` matches, the field displays, and the
   * next Tab enters it. A field revealed by focus on ITSELF is the
   * chicken-and-egg this pattern is usually got wrong by, and it is
   * invisible to every static check — the markup is identical either way.
   *
   * THE ASSERTION IS THE SEQUENCE RATHER THAN THE STATE. `display: grid`
   * on a focused room proves the rule fires; only pressing Tab proves a
   * reader can actually get in. */
  {
    const kp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await kp.goto(base + "/", { waitUntil: "load" });
    const rooms = await kp.locator(".nav .navroom").count();
    checked++;
    ok(rooms >= 2, `the bar carries ${rooms} room(s) with a field, expected at least 2`);
    for (let i = 0; i < rooms; i++) {
      await kp.evaluate((n) => document.querySelectorAll(".nav .navroom .navtop")[n].focus(), i);
      const r = await kp.evaluate((n) => {
        const room = document.querySelectorAll(".nav .navroom")[n];
        const f = room.querySelector(".navfield");
        const links = [...f.querySelectorAll("a")];
        return { name: room.querySelector(".navtop").textContent.trim(),
                 display: getComputedStyle(f).display,
                 n: links.length,
                 seen: links.filter((a) =>
                   a.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })).length };
      }, i);
      checked++;
      ok(r.display !== "none" && r.n > 0 && r.seen === r.n,
         `the room opens its field for a keyboard: ${r.name} computed ` +
         `display:${r.display} with ${r.seen} of ${r.n} links visible while ` +
         `its own link had focus — a field a keyboard cannot reveal is a ` +
         `field a keyboard cannot enter`);
      // And Tab must land inside it, which is the half a computed style
      // cannot answer.
      await kp.keyboard.press("Tab");
      const inside = await kp.evaluate((n) => {
        const f = document.querySelectorAll(".nav .navroom")[n].querySelector(".navfield");
        return document.activeElement && f.contains(document.activeElement);
      }, i);
      checked++;
      ok(inside, `${r.name}: Tab from the room did not land inside its field`);
    }
    await kp.close();
  }

  /* ── AND A POINTER HAS TO CROSS THE GAP THE KEYBOARD NEVER TOUCHES ──
   * The field sits `calc(100% + var(--s3))` below its room, and an
   * absolutely positioned child contributes nothing to its parent's box —
   * so those twelve pixels belonged to neither element, `.navroom:hover`
   * stopped matching the instant the pointer entered them, and the panel
   * was `display: none` before the hand arrived. Measured at 1280 by
   * moving from the middle of the word to the first link in the panel:
   * with ONE mouse event the panel survived and with five, twelve or
   * thirty it did not, on all three rooms, at every width. Thirteen links
   * reachable with a keyboard and not with a mouse, on 1,032 pages.
   *
   * The block above could not see it and is right not to: `:focus-within`
   * never crosses the gap, because Tab moves focus straight from the room
   * into the field. So this is the same promise asked of the other input
   * device, and it is asked the only way a promise about movement can be —
   * by moving. `steps` is what makes it a hand rather than a teleport: one
   * event is the case that always worked and is the case no reader has.
   *
   * IT ALSO ASSERTS THE ROOM IS STILL CLICKABLE, because the obvious
   * bridge — a transparent strip — is one that covers the word that opens
   * the menu if it is given a pixel too many. */
  {
    const hp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await hp.goto(base + "/", { waitUntil: "load" });
    const nrooms = await hp.locator(".nav .navroom").count();
    for (let i = 0; i < nrooms; i++) {
      const room = hp.locator(".nav .navroom").nth(i);
      const name = (await room.locator(".navtop").textContent()).trim();
      await hp.mouse.move(5, 500);
      const tb = await room.locator(".navtop").boundingBox();
      await hp.mouse.move(tb.x + tb.width / 2, tb.y + tb.height / 2);
      const fb = await room.locator(".navfield").boundingBox();
      checked++;
      ok(fb !== null, `${name}: the field did not open under a pointer at all`);
      if (!fb) continue;
      for (const steps of [5, 12, 30]) {
        await hp.mouse.move(5, 500);
        await hp.mouse.move(tb.x + tb.width / 2, tb.y + tb.height / 2);
        await hp.mouse.move(fb.x + fb.width / 2, fb.y + 30, { steps });
        const land = await hp.evaluate(([x, y, n]) => {
          const f = document.querySelectorAll(".nav .navroom")[n].querySelector(".navfield");
          const e = document.elementFromPoint(x, y);
          return { display: getComputedStyle(f).display,
                   inField: !!(e && f.contains(e)),
                   hit: e ? e.tagName + "." + (e.className || "") : "nothing" };
        }, [fb.x + fb.width / 2, fb.y + 30, i]);
        checked++;
        ok(land.display !== "none" && land.inField,
           `${name}: moving a pointer into its field in ${steps} steps left ` +
           `display:${land.display} and the point under the cursor is ` +
           `${land.hit} — the gap between the room and the panel belongs to ` +
           `neither, so the menu closes before the hand gets there`);
      }
      // the bridge must not steal the word it hangs from
      await hp.mouse.move(5, 500);
      await hp.mouse.move(tb.x + tb.width / 2, tb.y + tb.height / 2);
      const own = await hp.evaluate(([x, y]) => {
        const e = document.elementFromPoint(x, y);
        return e ? (e.classList.contains("navtop") ? "navtop" : e.tagName + "." + e.className) : "nothing";
      }, [tb.x + tb.width / 2, tb.y + tb.height / 2]);
      checked++;
      ok(own === "navtop",
         `${name}: the element under the pointer on the room's own word is ` +
         `${own} — the hover bridge is covering the link that opens the menu`);
    }
    await hp.close();
  }

  /* ── AND A WORD THAT OPENS A DIRECTORY HAS TO SAY SO BEFORE IT IS
   * HOVERED ─────────────────────────────────────────────────────────────
   * Three of the six rooms carry a field — DISCOVER's four links, ATLAS's
   * four, EUROPE's five — and at rest all six were the same word in the
   * same type at the same weight. Thirteen of the bar's destinations could
   * only be found by hovering a word at random, which is the same thirteen
   * the block above had just made reachable with a pointer.
   *
   * THE ASSERTION IS THE PAINTED ADVANCE RATHER THAN THE `content`
   * PROPERTY. `getComputedStyle(e, "::after").content` computes to the
   * SPECIFIED value — this repository already records a check defeated by
   * exactly that, reading back `"0" counter(band)` and reporting nineteen
   * families broken when none was. What is measurable is that the link's
   * box is wider than its own text: a Range over the text node gives the
   * glyphs, the element gives the box, and the difference is the mark.
   *
   * Both directions, because a mark on every room says nothing at all. */
  {
    const cp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await cp.goto(base + "/", { waitUntil: "load" });
    const marks = await cp.evaluate(() => [...document.querySelectorAll(".nav .navtop")].map((a) => {
      const r = document.createRange(); r.selectNodeContents(a);
      const cs = getComputedStyle(a);
      const pad = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
      return { name: a.textContent.trim(),
               // `a.parentElement` is `.nav` for a room with no field, and
               // `.nav` contains every OTHER room's field — so the first
               // version reported all six as carrying one and went red on
               // the three that are correct. The question is about THIS
               // room, so it is asked of this room.
               field: !!(a.closest(".navroom") || a).querySelector(".navfield"),
               extra: +(a.getBoundingClientRect().width - r.getBoundingClientRect().width - pad).toFixed(1) };
    }));
    checked++;
    ok(marks.filter((m) => m.field).length >= 2 && marks.some((m) => !m.field),
       `the bar carries ${marks.filter((m) => m.field).length} rooms with a ` +
       `field and ${marks.filter((m) => !m.field).length} without — this ` +
       `check cannot say anything unless both kinds are on the page`);
    for (const m of marks) {
      checked++;
      ok(m.field ? m.extra >= 6 : m.extra < 3,
         `${m.name}: the link's box is ${m.extra}px wider than its own ` +
         `glyphs and it ${m.field ? "opens a directory of links" : "opens a page"} — ` +
         (m.field ? "a word that opens a directory draws a mark saying so"
                  : "a word that leads to one page must not"));
    }
    // AND THE MARK COMES OFF WHERE THE FIELD DOES, because a caret on a bar
    // where no word opens a field is a claim the page cannot keep.
    await cp.setViewportSize({ width: 390, height: 844 });
    await cp.waitForTimeout(120);
    const narrow = await cp.evaluate(() => [...document.querySelectorAll(".nav .navtop")]
      .filter((a) => a.checkVisibility({ checkVisibilityCSS: true }))
      .map((a) => {
        const r = document.createRange(); r.selectNodeContents(a);
        return { name: a.textContent.trim(),
                 extra: +(a.getBoundingClientRect().width - r.getBoundingClientRect().width).toFixed(1) };
      }));
    checked++;
    ok(narrow.length > 0 && narrow.every((m) => m.extra < 3),
       `at 390 the fields cannot open and ` +
       `${narrow.filter((m) => m.extra >= 3).map((m) => m.name).join(", ")} ` +
       `still draws the mark that promises one`);
    await cp.close();
  }

  {
    const NAVPAGES = ["/", "/europe/austria/", "/journeys/", "/stories/", "/events/",
                      "/europe/france/alps-and-east/chamonix/"];
    for (const W of [320, 390, 430]) {
      const np = await browser.newPage({ viewport: { width: W, height: 844 } });
      for (const u of NAVPAGES) {
        const r = await np.goto(base + u, { waitUntil: "load" });
        if (!r || r.status() !== 200) continue;
        const got = await np.evaluate(() => {
          const vis = (e) => {
            const b = e.getBoundingClientRect();
            return b.width > 0 && b.height > 0 && getComputedStyle(e).display !== "none";
          };
          const out = [];
          // The masthead AND the page's own contents row: the same defect
          // was in both, and the second one hid half the sections of the
          // richest family in the product.
          for (const a of document.querySelectorAll(".masthead a, .sectionnav a")) {
            if (!vis(a)) continue;
            const b = a.getBoundingClientRect();
            if (b.right > window.innerWidth + 1 || b.left < -1)
              out.push(`${(a.textContent || "").trim()} @${Math.round(b.left)}..${Math.round(b.right)}`);
          }
          const g = (s) => {
            const e = document.querySelector(s);
            return e ? Math.round(e.getBoundingClientRect().left) : null;
          };
          return { off: out, mast: g(".masthead-in .wordmark"), main: g("main h1") };
        });
        checked++;
        ok(got.off.length === 0,
           `${u} at ${W}: ${got.off.length} masthead link(s) outside the ` +
           `viewport — ${got.off.slice(0, 4).join(", ")}. A section a reader ` +
           `cannot see is reachable only by a gesture nobody discovers`);
        if (got.mast !== null && got.main !== null) {
          checked++;
          ok(Math.abs(got.mast - got.main) <= 1,
             `${u} at ${W}: the masthead starts at ${got.mast}px and the page ` +
             `content at ${got.main}px. The brand and the navigation must sit ` +
             `on the same gutter as the words underneath them`);
        }
      }
      await np.close();
    }
  }


  /* KEYBOARD FOCUS, MEASURED ON THE PIXELS RATHER THAN ON THE TOKEN.
   *
   * Every contrast assertion on this site reads a declared colour against a
   * declared background, and a focus ring has neither: it is drawn three
   * pixels outside its element, so what it sits on is whatever happens to be
   * there. On the masthead that is the band itself, and #2a4ad9 on #2847d0
   * measures 1.06:1 — focus present, correctly placed, correctly sized, and
   * invisible, on the navigation of every page.
   *
   * SC 2.4.11 asks for 3:1 between the focused and unfocused states, which is
   * literally what this measures: shoot the element's neighbourhood twice,
   * with focus and without, and compare every pixel that changed against what
   * was there before. No token is consulted, so a ring drawn over a picture,
   * a gradient or a band is measured the same way as one on paper.
   */
  {
    const FOCUS = [
      ["/", ".masthead nav a", "the masthead navigation"],
      ["/", ".wordmark", "the wordmark"],
      ["/", ".way", "a homepage door"],
      ["/europe/austria/", ".crumbs a", "a breadcrumb"],
      ["/plan/", "#planner select", "a planner control"],
      ["/search/", "input[type=text]", "the search field"],
      ["/my-europe/", "a", "a link in the dark world"],
    ];
    const fp = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    for (const [u, sel, what] of FOCUS) {
      const r = await fp.goto(base + u, { waitUntil: "load" });
      if (!r || r.status() !== 200) continue;
      const box = await fp.evaluate((sel) => {
        const e = document.querySelector(sel);
        if (!e) return null;
        e.scrollIntoView({ block: "center" });
        const b = e.getBoundingClientRect();
        const pad = 8;
        return { x: Math.max(0, b.x - pad), y: Math.max(0, b.y - pad),
                 width: Math.min(600, b.width + pad * 2),
                 height: Math.min(300, b.height + pad * 2) };
      }, sel);
      if (!box || box.width < 4 || box.height < 4) continue;
      // BLUR FIRST. /search autofocuses its field, so the "before" shot
      // already had the ring in it and the diff came back empty — which this
      // check correctly reported as "focusing changes no pixel at all" about
      // an instrument fault rather than a site one. An unfocused baseline has
      // to be made, not assumed.
      await fp.evaluate(() => {
        if (document.activeElement && document.activeElement.blur)
          document.activeElement.blur();
      });
      const before = await fp.screenshot({ clip: box });
      await fp.evaluate((sel) => document.querySelector(sel).focus(), sel);
      // focus-visible follows keyboard intent, so give the element a real one
      await fp.keyboard.press("Tab");
      await fp.keyboard.press("Shift+Tab");
      const after = await fp.screenshot({ clip: box });
      const got = await fp.evaluate(async ([a, b]) => {
        const load = async (s) => {
          const i = new Image(); i.src = "data:image/png;base64," + s;
          await i.decode();
          const c = document.createElement("canvas");
          c.width = i.width; c.height = i.height;
          c.getContext("2d").drawImage(i, 0, 0);
          return c.getContext("2d").getImageData(0, 0, c.width, c.height).data;
        };
        const [A, B] = [await load(a), await load(b)];
        const lin = (v) => { v /= 255;
          return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
        const L = (r, g, b) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
        let n = 0, best = 1;
        for (let i = 0; i < A.length; i += 4) {
          if (A[i] === B[i] && A[i+1] === B[i+1] && A[i+2] === B[i+2]) continue;
          n++;
          const la = L(A[i], A[i+1], A[i+2]), lb = L(B[i], B[i+1], B[i+2]);
          const hi = Math.max(la, lb), lo = Math.min(la, lb);
          best = Math.max(best, (hi + 0.05) / (lo + 0.05));
        }
        return { n, best };
      }, [before.toString("base64"), after.toString("base64")]);
      ok(got.n > 0, `focusing ${what} changes no pixel at all — the ring is ` +
                    `either not drawn or drawn outside the element's own box`);
      ok(got.best >= 3.0,
         `the focus indicator on ${what} measures ${got.best.toFixed(2)}:1 ` +
         `against what it is drawn over, and SC 2.4.11 asks for 3. A ring in ` +
         `the same colour as the surface it sits on is focus that is present, ` +
         `correctly placed, correctly sized and invisible`);
    }
    await fp.close();
  }

  ok(errors.length === 0, `console errors:\n    ${errors.slice(0, 5).join("\n    ")}`);

  await browser.close();
  server.close();

  /* A floor on the count itself.
   *
   * This suite once reported "all 4 browser checks passed" and exited 0,
   * because a `const checked` inside main() shadowed the module-level
   * counter and put it in a temporal dead zone. Every assertion still ran;
   * almost none of them was counted. A green run that has silently stopped
   * counting is worse than a red one, because nobody looks at it.
   *
   * So the suite now refuses to call itself passing if it ran far fewer
   * checks than it did last time. Raise this when the real number grows;
   * it is a ratchet, not a target.
   */
  // 1000 -> 1150. The suite grew by the navigation-reachability block, the
  // container measurement, the painted-land probe and 320 joining the
  // clipping widths: 1,071 -> 1,182. A ratchet, not a target.
  const FLOOR = 1150;
  if (checked < FLOOR) {
    console.log(`\nonly ${checked} browser checks ran, and this suite has ${FLOOR}+. ` +
                "Something exited early or stopped counting — that is a failure, " +
                "not a pass.");
    process.exit(1);
  }

  if (failures.length) {
    console.log(`\n${failures.length} browser check failure(s) of ${checked}:`);
    failures.forEach((f) => console.log("  - " + f));
    process.exit(1);
  }
  console.log(`all ${checked} browser checks passed`);
}

main().catch((e) => { console.error(e); process.exit(1); });
