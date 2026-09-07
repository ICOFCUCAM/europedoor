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

  // The specification puts the question on the homepage; it has to reach
  // the planner and run, or it is a decorative input.
  await page.goto(base + "/", { waitUntil: "networkidle" });
  await page.fill("#homeask", "10 days in September, mountains and local food");
  await page.click(".askhome button[type=submit]");
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

  // Event categories must filter the year.
  await page.goto(base + "/events", { waitUntil: "networkidle" });
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
  await page.goto(base + "/map", { waitUntil: "networkidle" });
  const dots = await page.locator("#dots .dot").count();
  ok(dots > 200, `map drew only ${dots} cities`);
  await page.check('#layers input[value="winter"]');
  await page.waitForTimeout(120);
  const lit = await page.locator("#dots .dot:not(.off)").count();
  ok(lit > 0 && lit < dots, `winter layer lit ${lit} of ${dots} — filtering is not working`);

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
  ok(await page.locator("#places").isHidden(), "the places layer starts visible");
  await page.check('#layers input[value="places"]');
  ok(!(await page.locator("#places").isHidden()), "the places layer will not turn on");


  // ── saved places ───────────────────────────────────────────────────
  await page.goto(base + "/europe/norway/fjord-norway/bergen", { waitUntil: "networkidle" });
  await page.click("[data-save]");
  ok((await page.locator("[data-save]").textContent()).includes("✓"), "save button did not confirm");
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
