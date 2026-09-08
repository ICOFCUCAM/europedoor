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
  const hoisted = await page.locator("#result .whyall").textContent();
  ok(/because that is what you asked for/.test(hoisted),
     "the itinerary does not hoist the shared reason");
  const legWhy = await page.locator("#result .leg .mt-tight").allTextContents();
  ok(legWhy.length >= 3, "legs carry no why-line");
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

  // ── the staged wait ────────────────────────────────────────────────
  // Never a bare "Loading…". Each step is ticked when its work has actually
  // finished, so a failure marks where it stopped.
  const js = await (await page.request.get(base + "/assets/js/planner.js")).text();
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
  ok(await page.locator("#discover-interests .chip.pick").count() >= 16,
     "the interest chips did not render from the Atlas");
  ok(await page.locator("#discover-results .row").count() === 0,
     "Discover Mode showed results before anything was chosen");

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
  const lead = await page.locator(".whyall").textContent();
  ok(/off the obvious circuit/.test(lead),
     "the shared reason was not hoisted out of the individual cards");
  // The filter itself must not be repeated on every card — that is the
  // boilerplate this design exists to remove.
  ok(!quietRows.some((t) => /carries every one of/.test(t)),
     "each card still restates the filter the reader set");

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
  const CANON = ["Open", "Discover", "Wonder", "Understand", "Browse", "Plan", "Go"];
  const stages = await page.locator(".stage").allTextContents();
  const seq = stages.join(">");
  ok(stages.length >= 2, `the homepage names ${stages.length} steps`);
  const ranks = stages.map((t) => CANON.indexOf(t.trim()));
  ok(ranks.every((r) => r >= 0),
     `the homepage names a step that is not in the progression: ${seq}`);
  ok(ranks.every((r, i) => i === 0 || ranks[i - 1] < r),
     `the progression is out of order: ${seq}`);
  // It still ends on Go: the last thing the homepage asks for is a journey.
  ok(stages[stages.length - 1].trim() === "Go",
     `the homepage ends on ${stages[stages.length - 1]} rather than Go`);
  // The wonder band changes ground, so the rhythm is felt rather than
  // merely intended — and it must not blow out the page at any width.
  ok(await page.locator(".band.tone-quiet").count() === 1,
     "the wonder band is missing or duplicated");
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
  const motionCards = await page.locator(".card").count();
  ok(motionCards >= 12, `the motion index lists ${motionCards} motions`);

  const motionLinks = await page.locator('a[href^="/europe-in/"]').evaluateAll(
    (as) => Array.from(new Set(as.map((a) => a.getAttribute("href")))));
  ok(motionLinks.length >= 12, "the index does not link every motion");

  for (const href of motionLinks) {
    const r = await page.request.get(base + href);
    ok(r.status() === 200, `${href} returned ${r.status()}`);
    const html = await r.text();
    // Every motion page must print the query that produced it. A landing
    // page that will not say what produced it is an assertion.
    ok(/The query that made this page/.test(html), `${href} does not state its query`);
    ok(/destinations match, in \d+/.test(html), `${href} does not say how many matched`);
    ok(/Nothing here is hand-picked/.test(html), `${href} does not say it is a query`);
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
  //
  // The controls live in a closed <details> under the map, because the first
  // layout put thirteen interest filters and two selects between the headline
  // and the drawing and a 1280x1000 laptop opened the page called "the map"
  // with no map on it. Opening it is now a real user action, so the check
  // performs it rather than assuming it.
  await page.goto(base + "/map", { waitUntil: "networkidle" });
  const dots = await page.locator("#dots .dot").count();
  ok(dots > 200, `map drew only ${dots} cities`);
  await page.locator(".maptools > summary").click();
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
  await page.locator(".maptools > summary").click();
  await page.selectOption("#mapfrom", { index: 5 });
  await page.locator("#dots .dot").nth(40).click();
  await page.waitForSelector("#mappopup:not([hidden])");
  const popup = await page.locator("#mappopup").textContent();
  ok(/km from/.test(popup), "the popup does not give a distance from the chosen origin");
  ok(/Open /.test(popup), "the popup has no way into the page");
  await page.locator(".mappopup-close").click();
  ok(await page.locator("#mappopup").isHidden(), "the popup will not close");
  ok(await page.locator("#places").isHidden(), "the places layer starts visible");
  await page.check('#geolayers input[value="places"]');
  ok(!(await page.locator("#places").isHidden()), "the places layer will not turn on");
  await page.check('#geolayers input[value="regions"]');
  await page.waitForTimeout(120);
  const rlabels = await page.locator("#regions .rlabel").count();
  ok(rlabels > 10, `the regions layer drew ${rlabels} groupings`);
  await page.uncheck('#geolayers input[value="cities"]');
  ok(await page.locator("#dots").isHidden(), "the destinations layer will not turn off");

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
    await phone.goto(base + url, { waitUntil: "domcontentloaded" });
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

  // ── the map, as a list ─────────────────────────────────────────────
  // A point map is a picture; role="img" says what it is of and nothing more.
  await phone.goto(base + "/map", { waitUntil: "networkidle" });
  const described = await phone.getAttribute(".europemap", "aria-describedby");
  ok(described === "maplist", "the map does not point at its text alternative");
  ok(await phone.locator("#maplist").count() === 1, "there is no text alternative to the map");
  const listed = await phone.locator("#maplist li a").count();
  const dotted = await phone.locator("#dots .dot").count();
  ok(listed === dotted, `the map draws ${dotted} places and lists ${listed}`);

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
  const worldProbe = () => ({
    world: document.body.dataset.world || "discover",
    accent: document.body.dataset.accent || "",
    bg: getComputedStyle(document.body).backgroundColor,
    door: getComputedStyle(document.body).getPropertyValue("--door").trim(),
    limeAnywhere: [...document.querySelectorAll("*")].some((el) => {
      const c = getComputedStyle(el).color;
      const m = c.match(/\d+/g);
      return m && Number(m[0]) > 150 && Number(m[1]) > 220 && Number(m[2]) < 130;
    }),
  });

  for (const scheme of ["light", "dark"]) {
    const w = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await w.emulateMedia({ colorScheme: scheme });

    for (const url of ["/map", "/plan", "/my-europe", "/search", "/discover"]) {
      await w.goto(base + url, { waitUntil: "load" });
      const r = await w.evaluate(worldProbe);
      ok(r.world === "intelligence", `${url} is not in the INTELLIGENCE world`);
      ok(LUM(r.bg) < 0.06, `${scheme} ${url}: INTELLIGENCE is not dark (${r.bg})`);
      ok(/200,\s*255,\s*77|#c8ff4d/i.test(r.door),
         `${scheme} ${url}: the INTELLIGENCE accent is ${r.door}, not electric lime`);
    }

    // DISCOVER: three accents, and never the electric one.
    for (const [url, want] of [["/", "structural"], ["/europe/norway", "structural"],
                               ["/stories", "cultural"], ["/events/oct", "cultural"],
                               ["/method", "heritage"], ["/sources", "heritage"]]) {
      await w.goto(base + url, { waitUntil: "load" });
      const r = await w.evaluate(worldProbe);
      ok(r.world === "discover", `${url} should be DISCOVER, is ${r.world}`);
      ok(!r.limeAnywhere, `${scheme} ${url}: electric lime is set on text in the light world`);
      if (want === "heritage") ok(r.accent === "heritage", `${url} is not marked heritage`);
      if (want === "cultural") {
        // --door is a custom property, so it comes back as the authored
        // value — a hex — not as the rgb() a computed colour would give.
        ok(/#a4491f|#e08a5c|164,\s*73,\s*31|224,\s*138,\s*92/i.test(r.door),
           `${scheme} ${url}: the cultural accent is ${r.door}, not terracotta`);
      }
    }

    // DISCOVER follows the reader's preference; INTELLIGENCE does not.
    await w.goto(base + "/", { waitUntil: "load" });
    const home = await w.evaluate(worldProbe);
    ok(scheme === "light" ? LUM(home.bg) > 0.7 : LUM(home.bg) < 0.06,
       `${scheme}: DISCOVER did not follow the colour-scheme preference (${home.bg})`);

    // A map is INTELLIGENCE wherever it is embedded.
    await w.goto(base + "/europe/italy", { waitUntil: "load" });
    ok(await w.locator('.countrymap[data-world="intelligence"]').count() === 1,
       "the country map is not an INTELLIGENCE component");
    const figBg = await w.evaluate(() =>
      getComputedStyle(document.querySelector(".countrymap")).backgroundColor);
    ok(LUM(figBg) < 0.06, `the embedded map is not dark (${figBg})`);
    await w.close();
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
  const FLOOR = 620;
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
