/* THE HOSTED MEDIA DESK — the boundary, and only the boundary.
 *
 *     node tools/hosted-desk-tests.js
 *
 * `tools/photo-tests.py` already proves the pipeline: fetch by id, refusing
 * a mismatched id, keeping the original, never upscaling, generating the PR
 * body from the register. `tools/desk-tests.py` proves the local desk's own
 * boundary. Re-testing either through this one would be testing one thing
 * twice and calling it coverage.
 *
 * WHAT IS NEW HERE IS THAT THE DESK IS ON THE PUBLIC INTERNET AND HOLDS
 * THREE CREDENTIALS, and that every piece of state it used to keep in a
 * dictionary is now a signed value a caller holds. So this asserts the
 * things that changed:
 *
 *   every route refuses without a session; a forged or expired session is
 *   not a session; a signature made with another key is not a signature; a
 *   POST without the desk header is refused; the signed thumbnail token is
 *   NOT the only thing standing between a caller and an arbitrary fetch;
 *   the licence gate's refusal reaches the search route; an acquisition
 *   refuses a photo id that is not an identity, an empty alt, a purpose
 *   that is not one, and a duplicate from either end; and no response and
 *   no log line anywhere contains a key.
 *
 * IT NEVER ACQUIRES AND NEVER REACHES A PROVIDER. `fetch` is replaced for
 * the whole run, so a test that accidentally dispatched a workflow would
 * fail rather than dispatch one — a suite that could write to the
 * repository it is testing is the failure `desk-tests.py` records.
 */

import assert from "node:assert";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const API = path.join(ROOT, "desk", "api");

/* A key shaped like a real one, so a test that leaked it would be visible.
 * It is invented here and exists nowhere else. */
const FAKE_KEY = "TESTKEYTESTKEYTESTKEYTESTKEYTESTKEYTESTKEY0123456789";
const FAKE_GH = "ghp_TESTTESTTESTTESTTESTTESTTESTTESTTEST";

process.env.DESK_SESSION_SECRET = "test-signing-secret-not-a-real-one";
process.env.DESK_PASSCODE = "open-sesame";
process.env.PEXELS_API_KEY = FAKE_KEY;
process.env.DESK_GITHUB_TOKEN = FAKE_GH;
process.env.DESK_REPO = "ICOFCUCAM/europedoor";
process.env.DESK_BRANCH = "main";

let passed = 0;
const failures = [];
const LOG = [];

/* Everything printed during the run is captured, because "the key is absent
 * from the desk's own log" is one of the promises and a promise nobody
 * measures is a sentence. */
const realLog = console.log, realErr = console.error;
console.log = (...a) => LOG.push(a.join(" "));
console.error = (...a) => LOG.push(a.join(" "));

function t(name, fn) {
  return Promise.resolve()
    .then(fn)
    .then(() => { passed += 1; })
    .catch((e) => { failures.push(`${name}: ${e.message}`); });
}

/* ── the network, replaced ──────────────────────────────────────── */
let CALLS = [];
let NEXT = null;                     // what the next fetch should answer
globalThis.fetch = async (url, init = {}) => {
  CALLS.push({ url: String(url), init });
  if (NEXT) { const r = NEXT; NEXT = null; return r; }
  /* GitHub answers a workflow dispatch with 204 and no body, which is the
     whole reason the acquire route has to sign a time window instead of
     holding a run id. A stub that answered 200 would let a route that got
     that wrong pass. A 204 carries no body: `new Response("", {status:204})`
     throws. */
  if (String(url).includes("/dispatches")) {
    return new Response(null, { status: 204 });
  }
  return new Response(JSON.stringify({ photos: [] }), {
    status: 200, headers: { "content-type": "application/json" },
  });
};

/* ── a request and a response, enough of each ───────────────────── */
function req(opts = {}) {
  return {
    method: opts.method || "GET",
    url: opts.url || "/api/x",
    headers: Object.assign({}, opts.headers || {}),
    body: opts.json,
  };
}

function res() {
  const r = {
    statusCode: 0, headers: {}, body: "",
    setHeader(k, v) { this.headers[k.toLowerCase()] = v; },
    end(b) { this.body = b == null ? "" : String(b); this.done = true; },
  };
  r.json = () => { try { return JSON.parse(r.body); } catch { return {}; } };
  return r;
}

const lib = await import(path.join(API, "_lib.js"));
const { queryOf: topupQuery, interleave } =
  await import(path.join(API, "topup.js"));

/* The replaced fetch is restored by name rather than by copying the
 * literal back in three places, because three copies of one stub is
 * three chances for them to drift — which this suite has now watched
 * happen to a predicate twice. */
const BASE_FETCH = globalThis.fetch;
function restoreFetch() { globalThis.fetch = BASE_FETCH; }

function session() {
  return `${lib.COOKIE}=${lib.sign({ exp: Date.now() + 3600e3 })}`;
}

async function call(file, opts = {}) {
  const mod = await import(path.join(API, file));
  const rq = req(opts), rs = res();
  await mod.default(rq, rs);
  return rs;
}

const ROUTES = ["registry.js", "search.js", "thumb.js", "status.js", "sweep.js"];
const POSTS = ["acquire.js", "signout.js"];

/* ── 1. the session ─────────────────────────────────────────────── */

for (const f of ROUTES) {
  await t(`${f} refuses without a session`, async () => {
    const r = await call(f);
    assert.strictEqual(r.statusCode, 401, `answered ${r.statusCode}`);
  });
}

await t("acquire refuses without a session", async () => {
  const r = await call("acquire.js", {
    method: "POST", headers: { "x-desk": "1" }, json: {},
  });
  assert.strictEqual(r.statusCode, 401);
});

await t("a session signed with another key is not a session", async () => {
  const other = crypto.createHmac("sha256", "a different secret")
    .update(Buffer.from(JSON.stringify({ exp: Date.now() + 3600e3 }))
      .toString("base64url")).digest().toString("base64url");
  const body = Buffer.from(JSON.stringify({ exp: Date.now() + 3600e3 }))
    .toString("base64url");
  assert.strictEqual(lib.verify(`${body}.${other}`), null);
});

await t("an expired session is not a session", () => {
  assert.strictEqual(lib.verify(lib.sign({ exp: Date.now() - 1 })), null);
});

await t("a token of the wrong shape is refused rather than crashing", () => {
  /* timingSafeEqual THROWS on a length mismatch, which is both a leak of one
   * bit and a 500 from the function. Lengths are compared first, and this is
   * the assertion that says so. */
  for (const bad of ["", "x", "a.b", "....", "a.".repeat(50)]) {
    assert.strictEqual(lib.verify(bad), null, `${bad} was accepted`);
  }
});

await t("a wrong passcode does not issue a cookie", async () => {
  const r = await call("signin.js", {
    method: "POST", headers: { "x-desk": "1" }, json: { passcode: "wrong" },
  });
  assert.notStrictEqual(r.statusCode, 200);
  assert.ok(!r.headers["set-cookie"], "it set a cookie anyway");
});

await t("the right passcode issues an HttpOnly, Secure, SameSite cookie",
  async () => {
    const r = await call("signin.js", {
      method: "POST", headers: { "x-desk": "1" },
      json: { passcode: "open-sesame" },
    });
    assert.strictEqual(r.statusCode, 200);
    const c = String(r.headers["set-cookie"]);
    for (const flag of ["HttpOnly", "Secure", "SameSite=Strict", "Path=/"]) {
      assert.ok(c.includes(flag), `the cookie is missing ${flag}`);
    }
  });

/* ── 2. the second CSRF control ─────────────────────────────────── */

for (const f of POSTS.concat(["signin.js"])) {
  await t(`${f} refuses a POST with no desk header`, async () => {
    const r = await call(f, { method: "POST", headers: { cookie: session() },
                              json: { passcode: "open-sesame" } });
    assert.strictEqual(r.statusCode, 400, `answered ${r.statusCode}`);
  });
  await t(`${f} refuses a GET`, async () => {
    const r = await call(f, { headers: { cookie: session() } });
    assert.strictEqual(r.statusCode, 405);
  });
}

/* ── 3. the thumbnail, which is the shape that looks like an SSRF ─ */

await t("an unsigned thumbnail token serves nothing", async () => {
  const r = await call("thumb.js", {
    url: "/api/thumb?t=" + encodeURIComponent("https://images.pexels.com/a.jpg"),
    headers: { cookie: session() },
  });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0, "it fetched something");
});

await t("a SIGNED token for a host that is not a provider serves nothing",
  async () => {
    /* THE SIGNATURE IS NOT THE ONLY CONTROL, and this is the assertion that
     * says so. A signature proves this desk minted the address; it proves
     * nothing about where the address points, and it would go on proving
     * nothing if the signing secret ever leaked. */
    CALLS = [];
    const tok = lib.sign({ u: "https://169.254.169.254/latest/meta-data/",
                           exp: Date.now() + 3600e3 });
    const r = await call("thumb.js", {
      url: "/api/thumb?t=" + encodeURIComponent(tok),
      headers: { cookie: session() },
    });
    assert.strictEqual(r.statusCode, 400);
    assert.strictEqual(CALLS.length, 0, "it fetched the link-local address");
  });

await t("a signed token for http rather than https serves nothing", async () => {
  CALLS = [];
  const tok = lib.sign({ u: "http://images.pexels.com/a.jpg",
                         exp: Date.now() + 3600e3 });
  const r = await call("thumb.js", {
    url: "/api/thumb?t=" + encodeURIComponent(tok),
    headers: { cookie: session() },
  });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0);
});

await t("an expired thumbnail token serves nothing", async () => {
  CALLS = [];
  const tok = lib.sign({ u: "https://images.pexels.com/a.jpg", exp: Date.now() - 1 });
  const r = await call("thumb.js", {
    url: "/api/thumb?t=" + encodeURIComponent(tok),
    headers: { cookie: session() },
  });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0);
});

await t("a provider host that answers something that is not an image is refused",
  async () => {
    CALLS = [];
    NEXT = new Response("<html>", { status: 200,
      headers: { "content-type": "text/html" } });
    const tok = lib.sign({ u: "https://images.pexels.com/a.jpg",
                           exp: Date.now() + 3600e3 });
    const r = await call("thumb.js", {
      url: "/api/thumb?t=" + encodeURIComponent(tok),
      headers: { cookie: session() },
    });
    assert.strictEqual(r.statusCode, 502);
  });

/* ── 4. the licence gate reaches the search route ───────────────── */

await t("the search route refuses a provider the licence gate refuses",
  async () => {
    CALLS = [];
    const r = await call("search.js", {
      url: "/api/search?provider=unsplash&purpose=homepage-hero&q=alps",
      headers: { cookie: session() },
    });
    assert.strictEqual(r.statusCode, 400);
    assert.match(r.json().error, /REFUSED/);
    assert.strictEqual(CALLS.length, 0, "it searched anyway");
  });

await t("the search route refuses a purpose that is not one", async () => {
  CALLS = [];
  const r = await call("search.js", {
    url: "/api/search?provider=pexels&purpose=not-a-purpose&q=alps",
    headers: { cookie: session() },
  });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0);
});

await t("the search route refuses an empty query", async () => {
  CALLS = [];
  const r = await call("search.js", {
    url: "/api/search?provider=pexels&purpose=homepage-hero&q=",
    headers: { cookie: session() },
  });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0);
});

await t("a rate limit is reported and never retried around", async () => {
  CALLS = [];
  NEXT = new Response("{}", { status: 429 });
  const r = await call("search.js", {
    url: "/api/search?provider=pexels&purpose=homepage-hero&q=alps",
    headers: { cookie: session() },
  });
  assert.strictEqual(r.statusCode, 429);
  assert.strictEqual(CALLS.length, 1, `it made ${CALLS.length} attempts`);
});

/* ── 5. the requirements come from the SLOT ─────────────────────── */

await t("a templated instance inherits its slot's numbers", () => {
  const reg = lib.registry();
  const row = reg.purposes.find((p) => p.slot);
  assert.ok(row, "the registry declares no templated purposes at all");
  assert.strictEqual(row.min_width, undefined,
    "a templated row carries its own copy of the slot's numbers");
  const spec = lib.specOf(row.purpose);
  assert.strictEqual(spec.min_width, reg.slots[row.slot].min_width);
  assert.ok(spec.note && spec.note.length > 40, "it inherited no brief");
});

await t("fits() refuses an original too small to derive from", () => {
  const bad = lib.fits({ width: 800, height: 500 },
                       { min_width: 1800, orientation: "landscape" });
  assert.ok(bad.length, "an 800px original passed an 1800px slot");
  assert.match(bad.join(" "), /upscale/);
});

/* ── the stylesheet's own tokens ────────────────────────────────── */

/* AN UNRESOLVABLE var() IS NOT A MISSING VALUE, IT IS A DIFFERENT ONE: the
 * whole declaration is invalid at computed-value time and the property takes
 * its INHERITED value. The main stylesheet records this failure at length —
 * `--serif` for `--display`, in twelve rules, silently replacing the right
 * font on most of the largest headings on the site — and this desk was
 * written afterwards and had two of its own: `--sea` where the token is
 * `--cobalt`, leaving the running step's tick painting whatever it inherits,
 * and `--paper` where it is `--limestone`, on both textareas including the
 * one control here that must be read in full before it is approved.
 *
 * Nothing that counts declarations can see it and nothing that renders can
 * either, because the wrong value is a real value. Comparing the two sets is
 * the only instrument, and it costs a millisecond. */
await t("every custom property the desk spends is one it declares", () => {
  const css = fs.readFileSync(path.join(ROOT, "desk", "public", "desk.css"),
                              "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const declared = new Set([...css.matchAll(/(--[a-z0-9-]+)\s*:/g)].map((m) => m[1]));
  const used = new Set([...css.matchAll(/var\((--[a-z0-9-]+)/g)].map((m) => m[1]));
  const missing = [...used].filter((n) => !declared.has(n));
  assert.deepStrictEqual(missing, [],
    `these resolve to nothing, so the rules that ask for them take the `
    + `INHERITED value instead: ${missing.join(", ")}`);
});

/* ── 6. acquisition refuses before it dispatches ────────────────── */

const acq = (json) => call("acquire.js", {
  method: "POST", headers: { "x-desk": "1", cookie: session() }, json,
});

await t("a photo id that is not an identity is refused", async () => {
  CALLS = [];
  for (const id of ["", "abc", "12 3", "1;rm -rf /", "../../etc/passwd",
                    "9".repeat(30)]) {
    const r = await acq({ provider: "pexels", photo_id: id,
                          purpose: "homepage-hero", alt: "a valley" });
    assert.strictEqual(r.statusCode, 400, `${id} was accepted`);
  }
  assert.strictEqual(CALLS.length, 0, "it dispatched something");
});

await t("an empty alt text is refused", async () => {
  CALLS = [];
  const r = await acq({ provider: "pexels", photo_id: "12345",
                        purpose: "homepage-hero", alt: "   " });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0);
});

await t("a purpose that is not one is refused", async () => {
  CALLS = [];
  const r = await acq({ provider: "pexels", photo_id: "12345",
                        purpose: "homepage-hero@nowhere", alt: "a valley" });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0);
});

await t("a provider the licence gate refuses cannot be acquired", async () => {
  CALLS = [];
  const r = await acq({ provider: "unsplash", photo_id: "12345",
                        purpose: "homepage-hero", alt: "a valley" });
  assert.strictEqual(r.statusCode, 400);
  assert.match(r.json().error, /REFUSED/);
  assert.strictEqual(CALLS.length, 0);
});

/* ── 6b. a batch is many acquisitions and one decision ───────────── */

await t("a batch refuses one bad entry and dispatches nothing", async () => {
  CALLS = [];
  const r = await acq({ provider: "pexels", batch: [
    { purpose: "door-coast", photo_id: "111", alt: "a long enough description" },
    { purpose: "door-food", photo_id: "not-an-id", alt: "another description" },
  ] });
  assert.strictEqual(r.statusCode, 400);
  assert.match(r.json().error, /entry 2/);
  assert.strictEqual(CALLS.length, 0, "a malformed batch reached the network");
});

await t("one surface may not be ticked twice in a batch", async () => {
  CALLS = [];
  const r = await acq({ provider: "pexels", batch: [
    { purpose: "door-coast", photo_id: "111", alt: "a long enough description" },
    { purpose: "door-coast", photo_id: "222", alt: "another description" },
  ] });
  assert.strictEqual(r.statusCode, 400);
  assert.match(r.json().error, /ticked twice/);
  assert.strictEqual(CALLS.length, 0);
});

await t("one photograph may not be ticked for two surfaces in a batch",
  async () => {
    /* The register cannot refuse this one: neither row exists yet. It is the
     * same promise from inside the batch. */
    CALLS = [];
    const r = await acq({ provider: "pexels", batch: [
      { purpose: "door-coast", photo_id: "111", alt: "a long enough description" },
      { purpose: "door-food", photo_id: "111", alt: "another description" },
    ] });
    assert.strictEqual(r.statusCode, 400);
    assert.match(r.json().error, /two surfaces/);
    assert.strictEqual(CALLS.length, 0);
  });

/* THE CAP IS WHAT ONE PULL REQUEST CARRIES, and the number moved when the
 * basket arrived: 30 was a claim about how long a sitting takes, and run 18
 * measured it at 4.25 seconds a photograph against 215 seconds of fixed
 * cost, so the workflow was never the constraint. The basket is where a
 * sitting accumulates; this is where one question stops.
 *
 * ITS FIRST VERSION SENT 31 COPIES OF ONE PURPOSE and asserted the cap
 * message, which passed for as long as the cap was under 31 and then started
 * reporting the DUPLICATE refusal instead — a test that was reading a
 * different rule than the one it named. Distinct purposes, taken from the
 * registry rather than typed, so it is asking the question it says it is. */
await t("a batch bigger than one pull request can carry is refused", async () => {
  CALLS = [];
  const reg = lib.registry();
  /* AND THE SIZES COME FROM THE REGISTRY, not from a typed 61. A test that
   * types the cap is a fifth copy of it, and copies of this number are the
   * defect being guarded against. */
  const cap = reg.dispatch_cap;
  const many = reg.purposes.slice(0, cap + 1).map((p, i) => (
    { purpose: p.purpose, photo_id: String(i + 1), alt: "a description here" }));
  assert.strictEqual(many.length, cap + 1,
    `the registry holds fewer than ${cap + 1} purposes`);
  const r = await acq({ provider: "pexels", batch: many });
  assert.strictEqual(r.statusCode, 400);
  assert.match(r.json().error, new RegExp(`cap is ${cap}\\b`));
  assert.strictEqual(CALLS.length, 0);
});

/* AND SIXTY IS ACCEPTED, because a cap nothing reaches is a cap nobody has
 * tested the far side of. The old suite asserted only the refusal, so a cap
 * of one would have passed it. */
await t("and a batch of exactly the cap is dispatched as one run", async () => {
  CALLS = [];
  const reg = lib.registry();
  const cap = reg.dispatch_cap;
  const full = reg.purposes.slice(0, cap).map((p, i) => (
    { purpose: p.purpose, photo_id: String(i + 1), alt: "a description here" }));
  const r = await acq({ provider: "pexels", batch: full });
  assert.strictEqual(r.statusCode, 200, JSON.stringify(r.json()));
  const sent = CALLS.filter((c) => c.url.includes("/dispatches"));
  assert.strictEqual(sent.length, 1, `it made ${sent.length} dispatches`);
  const inputs = JSON.parse(sent[0].init.body).inputs;
  assert.strictEqual(JSON.parse(inputs.batch).length, cap);
});

await t("an empty batch is refused", async () => {
  CALLS = [];
  const r = await acq({ provider: "pexels", batch: [] });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0);
});

await t("a valid batch dispatches the batch stage with every id", async () => {
  /* THE ONLY TEST HERE THAT LETS A DISPATCH THROUGH, and it inspects what
   * went out: the stage, and that every entry travels as an ID. A list of
   * ids is as incapable of choosing as a single id is — `--pick 3` was wrong
   * because a POSITION is not an identity, which has nothing to do with how
   * many identities travel together. */
  CALLS = [];
  /* The default stub answers `{"photos":[]}` with a 200, which `register()`
     reads as a register holding nothing — which is true, and is the state
     this product is actually in. The dispatch that follows gets the same
     answer; the assertions below read what went OUT rather than what came
     back. */
  const r = await acq({ provider: "pexels", batch: [
    { purpose: "door-coast", photo_id: "111", alt: "a long enough description" },
    { purpose: "door-food", photo_id: "222", alt: "another long description" },
  ] });
  const dispatch = CALLS.find((c) => c.url.includes("/dispatches"));
  assert.ok(dispatch, "no dispatch was made");
  const body = JSON.parse(dispatch.init.body);
  assert.strictEqual(body.inputs.stage, "batch");
  const sent = JSON.parse(body.inputs.batch);
  assert.strictEqual(sent.length, 2);
  assert.ok(sent.every((e) => /^[0-9]+$/.test(e.photo_id) && e.purpose && e.alt),
            "an entry travelled without an id, a purpose or a description");
  assert.ok(!("key" in sent[0]) && !("surface" in sent[0]),
            "the dispatch carried the desk's own bookkeeping");
  assert.strictEqual(r.statusCode, 200);
  assert.strictEqual(r.json().count, 2);
});

await t("a dispatch GitHub refuses is explained, not relayed", async () => {
  /* THE FIRST REAL BATCH CAME BACK AS GITHUB'S OWN WORDS — "Unexpected
   * inputs provided: [batch]" with a documentation link. Accurate, about a
   * JSON field the editor never typed, and silent about the only thing that
   * mattered: the desk was dispatching at a branch older than itself. A
   * message with no measurement in it cannot be diagnosed. */
  const { explain } = await import(path.join(API, "acquire.js"));
  const m = explain(422, JSON.stringify(
    { message: 'Unexpected inputs provided: ["batch"]' }), "main", true);
  assert.match(m, /branch "main"/);
  assert.match(m, /DESK_BRANCH/);
  assert.match(m, /Nothing was acquired/);
  assert.ok(!/documentation_url/.test(m), "it relayed GitHub's raw body");
  for (const [code, want] of [[404, /DESK_REPO/], [403, /Read and write/]]) {
    assert.match(explain(code, "{}", "main", false), want);
  }
  /* AND AN UNKNOWN FAILURE STILL CARRIES THE BRANCH AND THE REASON, because
   * a catch-all that drops the state is the same fault one step along. */
  const other = explain(500, JSON.stringify({ message: "boom" }), "trunk", false);
  assert.match(other, /trunk/);
  assert.match(other, /boom/);
});

await t("a run GitHub is holding is not reported as a failure", async () => {
  /* THE FIRST BATCH TO REACH GITHUB CAME BACK `action_required`: created,
   * held for approval, concluded two seconds later having run NOTHING. The
   * desk called that a failure and told the editor "the run's log has what
   * it said" — and there is no log, because there are no jobs. A verdict
   * nobody reached, reported as a verdict. */
  const run = {
    id: 1, html_url: "https://github.invalid/run/1",
    created_at: new Date().toISOString(), status: "completed",
  };
  const cases = [
    ["action_required", "approval", /Approve and run/],
    ["cancelled", "cancelled", /cancelled/i],
    ["failure", "failed", /no steps at all/],
    ["success", "done", null],
  ];
  for (const [conclusion, want, saying] of cases) {
    CALLS = [];
    let n = 0;
    const real = globalThis.fetch;
    globalThis.fetch = async (u) => {
      n += 1;
      if (String(u).includes("/jobs")) {
        return new Response(JSON.stringify({ jobs: [] }), { status: 200 });
      }
      if (String(u).includes("/runs?")) {
        return new Response(JSON.stringify(
          { workflow_runs: [{ ...run, conclusion }] }), { status: 200 });
      }
      return new Response(JSON.stringify([]), { status: 200 });
    };
    const job = lib.sign({ since: Date.now() - 1000, batch: false,
                           purpose: "door-coast", photo_id: "1",
                           exp: Date.now() + 3600e3 });
    const r = await call("status.js", {
      url: "/api/status?job=" + encodeURIComponent(job),
      headers: { cookie: session() },
    });
    globalThis.fetch = real;
    const j = r.json();
    assert.strictEqual(j.state, want, `${conclusion} read as ${j.state}`);
    if (saying) assert.match(j.failure || "", saying);
    if (conclusion === "success") {
      assert.ok(!j.failure, "a successful run carried a failure sentence");
    }
  }
});

await t("the registry says where a dispatch will go", async () => {
  const r = await call("registry.js", { headers: { cookie: session() } });
  const d = r.json().dispatch || {};
  assert.ok(d.repo && d.branch && d.workflow,
            "the desk cannot say which branch it fires at");
});

/* ── 6c. the sweep proposes and does not choose ──────────────────── */

await t("the sweep refuses a slot that is not one", async () => {
  CALLS = [];
  const r = await call("sweep.js", {
    url: "/api/sweep?provider=pexels&slot=nope&country=norway",
    headers: { cookie: session() },
  });
  assert.strictEqual(r.statusCode, 400);
  assert.strictEqual(CALLS.length, 0);
});

await t("the sweep refuses a provider the licence gate refuses", async () => {
  CALLS = [];
  const r = await call("sweep.js", {
    url: "/api/sweep?provider=unsplash&slot=destination-hero&country=norway",
    headers: { cookie: session() },
  });
  assert.strictEqual(r.statusCode, 400);
  assert.match(r.json().error, /REFUSED/);
  assert.strictEqual(CALLS.length, 0);
});

await t("the sweep's query is the surface's own name, not its slug", async () => {
  /* A slug gives "alps and east" and "hohensalzburg"; the atlas writes the
   * name inside the surface sentence, so that is where it comes from. */
  const { queryFor } = await import(path.join(API, "sweep.js"));
  assert.strictEqual(
    queryFor({ surface: "The opening image of the Bergen, Norway destination page.",
               target: "norway/fjord-norway/bergen" }),
    "Bergen, Norway");
  assert.strictEqual(
    queryFor({ surface: "The opening image of the Hohensalzburg Fortress, "
                      + "Salzburg place page.",
               target: "austria/x/salzburg/hohensalzburg" }),
    "Hohensalzburg Fortress, Salzburg");
});

/* ── 7. no credential anywhere ──────────────────────────────────── */

await t("no response body or header carries a key", async () => {
  const seen = [];
  NEXT = null;
  for (const f of ["registry.js", "search.js", "status.js"]) {
    const r = await call(f, {
      url: "/api/x?provider=pexels&purpose=homepage-hero&q=alps&job=nope",
      headers: { cookie: session() },
    });
    seen.push(r.body, JSON.stringify(r.headers));
  }
  const all = seen.join("\n");
  assert.ok(!all.includes(FAKE_KEY), "a response carried the provider key");
  assert.ok(!all.includes(FAKE_GH), "a response carried the GitHub token");
});

await t("nothing printed during this run carries a key", () => {
  const all = LOG.join("\n");
  assert.ok(!all.includes(FAKE_KEY), "the log carried the provider key");
  assert.ok(!all.includes(FAKE_GH), "the log carried the GitHub token");
});

await t("no committed desk file carries anything credential-shaped", () => {
  /* The key is an environment variable on the deployment and nowhere else.
   * This is the same grep `photo-tests.py --committed-only` runs over the
   * repository, pointed at the directory that was added after it. */
  const bad = [];
  const walk = (d) => {
    for (const name of fs.readdirSync(d)) {
      const p = path.join(d, name);
      if (fs.statSync(p).isDirectory()) { walk(p); continue; }
      if (!/\.(js|json|html|css)$/.test(name)) continue;
      const text = fs.readFileSync(p, "utf8");
      for (const m of text.match(/\b(ghp_|github_pat_|sk-|Bearer\s+[A-Za-z0-9]{20,})\S*/g) || []) {
        /* A NAME IS NOT A VALUE. `Bearer ${token}` is the code that sends
         * one; a literal is the thing being looked for. */
        if (!m.includes("${") && !m.includes("token")) bad.push(`${p}: ${m}`);
      }
      for (const m of text.match(/[A-Za-z0-9_-]{40,}/g) || []) {
        if (/^[A-Za-z0-9]{40,}$/.test(m) && !/^[a-f0-9]+$/i.test(m)) {
          bad.push(`${p}: a 40-character token-shaped literal`);
        }
      }
    }
  };
  walk(path.join(ROOT, "desk"));
  assert.deepStrictEqual(bad, [], bad.join("\n"));
});

await t("the desk directory declares no runtime dependency", () => {
  const pkg = JSON.parse(
    fs.readFileSync(path.join(ROOT, "desk", "package.json"), "utf8"));
  assert.ok(!pkg.dependencies, "a dependency arrived");
  assert.strictEqual(pkg.type, "module",
    "the functions are ESM and the package does not say so");
});

await t("the deployment's headers are as strict as the site's", () => {
  const v = JSON.parse(
    fs.readFileSync(path.join(ROOT, "desk", "vercel.json"), "utf8"));
  const h = {};
  for (const rule of v.headers) for (const x of rule.headers) h[x.key] = x.value;
  const csp = h["Content-Security-Policy"];
  assert.match(csp, /default-src 'none'/);
  assert.ok(!csp.includes("unsafe-inline"), "the desk's CSP allows inline");
  assert.match(csp, /img-src 'self'/);      // never a provider CDN
  assert.match(csp, /frame-ancestors 'none'/);
  assert.match(h["X-Robots-Tag"] || "", /noindex/);
  assert.match(h["Strict-Transport-Security"] || "", /max-age=\d{7,}/);
});

await t("the desk page loads no inline script and no style attribute", () => {
  const html = fs.readFileSync(
    path.join(ROOT, "desk", "public", "index.html"), "utf8");
  assert.ok(!/<script(?![^>]*\bsrc=)/.test(html), "an inline script");
  assert.ok(!/\sstyle="/.test(html), "a style attribute");
});

/* ── fill the library ───────────────────────────────────────────── */

await t("the fill route refuses without a session", async () => {
  const r = await call("topup.js");
  assert.strictEqual(r.statusCode, 401, `answered ${r.statusCode}`);
});

await t("it round-robins the families rather than draining one", () => {
  /* THE ORDER IS THE WHOLE POINT OF THE BUTTON. Taken in registry order one
   * press is sixty Austrian destinations — a complete answer about Austria
   * and no answer about the product. One from each family in turn means a
   * press touches themes, countries, journeys, interests, macro regions,
   * categories, stories, regions, destinations and places.
   *
   * THE FIRST VERSION OF THIS COUNTED SEARCHES and asserted "at least ten",
   * which is true of registry order too — so replacing the round-robin with
   * `const order = empty` left it green. It reads the ordering itself now.  */
  const reg = lib.registry();
  const order = interleave(reg.purposes);
  const families = (p) => p.slot || p.purpose;
  const lanes = new Set(reg.purposes.map(families));
  const head = order.slice(0, lanes.size).map(families);
  assert.strictEqual(new Set(head).size, lanes.size,
    `the first ${lanes.size} surfaces cover ${new Set(head).size} of `
    + `${lanes.size} families — it is draining one queue`);
  assert.strictEqual(order.length, reg.purposes.length,
    "interleaving lost or duplicated a surface");
});

await t("and the route itself walks that order", async () => {
  /* THE FUNCTION BEING RIGHT IS NOT THE ROUTE USING IT. The assertion above
   * reads `interleave` directly, so swapping `interleave(empty)` for `empty`
   * inside the handler left it green — the same gap as a test that proves a
   * predicate and never puts it in the path. The response reports which
   * families the press touched, so this reads the route's own answer. */
  globalThis.fetch = async () => new Response(JSON.stringify({ photos: [] }), {
    status: 200, headers: { "content-type": "application/json" } });
  const r = await call("topup.js", {
    url: "/api/topup?provider=pexels&n=60", headers: { cookie: session() } });
  const j = r.json();
  const reg = lib.registry();
  const lanes = new Set(reg.purposes.map((p) => p.slot || p.purpose));
  assert.ok(j.looked > 0, "it looked at nothing");
  assert.strictEqual(j.covered.length, Math.min(j.looked, lanes.size),
    `it looked at ${j.looked} surfaces across only ${j.covered.length} `
    + `families — the route is draining one queue`);
  restoreFetch();
});

await t("one press cannot make 837 requests against the rate limit", async () => {
  /* THE CAP WAS ON THE WRONG QUANTITY. A surface whose search returns
   * nothing qualifying costs a request and yields no row, so bounding only
   * the TAKE let the loop walk every empty surface on a provider having a
   * bad day — 837 requests against a rate limit nobody here owns. The sweep
   * has had `MAX_SURFACES` for exactly this since it was written.
   *
   * It surfaced because the ordering test could not discriminate: look at
   * everything and every order covers every family. A test that cannot fail
   * and a route that cannot stop were the same bug. */
  /* COUNTED BY HOST, because the route also reads the register from GitHub
   * and the first version of this counted that as a provider request and
   * reported 121 against a ceiling of 120. An assertion that names the rate
   * limit has to count the thing the rate limit governs. */
  let n = 0;
  globalThis.fetch = async (url) => {
    if (/pexels/.test(String(url))) n += 1;
    return new Response(JSON.stringify({ photos: [] }), {
      status: 200, headers: { "content-type": "application/json" } });
  };
  const topup = await import(path.join(API, "topup.js"));
  const r = await call("topup.js", {
    url: "/api/topup?provider=pexels&n=60", headers: { cookie: session() } });
  assert.strictEqual(r.statusCode, 200);
  assert.ok(n <= topup.maxLooks(),
    `it made ${n} provider requests for a ceiling of ${topup.maxLooks()}`);
  assert.ok(r.json().stopped, "it stopped early and did not say so");
  restoreFetch();
});

await t("a candidate with no description is never taken automatically",
  async () => {
    /* THE ALTERNATIVE TO A REAL DESCRIPTION IS WRITING ONE ABOUT A
     * PHOTOGRAPH NOTHING HERE HAS SEEN, which is the licence-from-memory
     * failure in another costume. A candidate without the photographer's own
     * alt is not unusable — it is un-AUTOMATABLE, and it stays available to
     * the two paths where a person is looking. */
    globalThis.fetch = async () => new Response(JSON.stringify({ photos: [{
      id: 999001, width: 6000, height: 4000, alt: "",
      photographer: "Nobody", photographer_url: "https://www.pexels.com/@x",
      url: "https://www.pexels.com/photo/x-999001/",
      src: { original: "https://images.pexels.com/photos/999001/x.jpg",
             large: "https://images.pexels.com/photos/999001/x.jpg" },
    }] }), { status: 200, headers: { "content-type": "application/json" } });
    const r = await call("topup.js", {
      url: "/api/topup?provider=pexels&n=3", headers: { cookie: session() } });
    assert.strictEqual(r.statusCode, 200);
    assert.strictEqual((r.json().rows || []).length, 0,
      "it took a photograph it would have had to invent a description for");
    restoreFetch();
  });

await t("it never proposes one photograph for two surfaces", async () => {
  /* The provider returns the same picture for neighbouring queries, and the
   * register refuses one id against two purposes — so a set this button
   * gathers must not contain a pair the dispatch will reject four screens
   * later. */
  globalThis.fetch = async () => new Response(JSON.stringify({ photos: [{
    id: 999002, width: 6000, height: 4000, alt: "a wide landscape",
    photographer: "Somebody", photographer_url: "https://www.pexels.com/@y",
    url: "https://www.pexels.com/photo/y-999002/",
    src: { original: "https://images.pexels.com/photos/999002/y.jpg",
           large: "https://images.pexels.com/photos/999002/y.jpg" },
  }] }), { status: 200, headers: { "content-type": "application/json" } });
  const r = await call("topup.js", {
    url: "/api/topup?provider=pexels&n=8", headers: { cookie: session() } });
  const ids = (r.json().rows || []).map((x) => x.candidate.id);
  assert.strictEqual(ids.length, new Set(ids).size,
    `it offered one id for ${ids.length - new Set(ids).size + 1} surfaces`);
  assert.ok(ids.length <= 1, `it offered ${ids.length} rows from one photograph`);
  restoreFetch();
});

await t("it gathers no more than the dispatch will accept", async () => {
  /* AND BOTH READ THE ONE DECLARATION, because for one commit they did
   * not: three copies of this number were raised to sixty and the
   * WORKFLOW — the only one that is a gate — stayed at thirty, so a full
   * sitting was gathered, approved, dispatched and refused on the first
   * step. The earlier version of this test compared the two JS copies to
   * each other and could never have seen that, because the copy it could
   * not read was the one that mattered. `checks.py` owns the four-way
   * assertion; this one asserts the route actually spends it. */
  const topup = await import(path.join(API, "topup.js"));
  const cap = lib.registry().dispatch_cap;
  assert.ok(Number.isInteger(cap) && cap > 0,
    `the registry declares no dispatch_cap: ${cap}`);
  assert.strictEqual(topup.maxFill(), cap,
    `the button gathers ${topup.maxFill()} and the dispatch takes ${cap}`);
  assert.strictEqual(topup.maxLooks(), 2 * cap,
    `it looks at ${topup.maxLooks()} surfaces to take ${cap}`);
});

await t("the registry route serves the cap, so the basket can state it", async () => {
  /* The browser holds no copy: `desk.js` reads `REG.dispatch_cap` and says
   * the number on the basket's own face. A route that did not serve it
   * would leave the button guessing, which is where the typed copy came
   * from in the first place. */
  const r = await call("registry.js", { headers: { cookie: session() } });
  assert.strictEqual(r.statusCode, 200, `registry answered ${r.statusCode}`);
  assert.strictEqual(r.json().dispatch_cap, lib.registry().dispatch_cap,
    "the registry route does not serve dispatch_cap");
});

await t("the query is the role's own concept, with the name in it", () => {
  /* A country wants `{name} landscape` and a destination wants `{name}`, and
   * that difference is the editorial knowledge the roles were written to
   * hold. Nothing looks at these pictures, so the query has to carry the
   * intent the eye would have. */
  const reg = lib.registry();
  const row = reg.purposes.find((p) => p.slot === "country-hero");
  assert.ok(row, "the registry declares no country heroes");
  const spec = lib.specOf(row.purpose);
  assert.ok((spec.search || []).length, "the slot declares no concepts");
  assert.ok(!/\{name\}/.test(topupQuery(row, spec)),
    "the placeholder reached the provider unsubstituted");
  assert.notStrictEqual(topupQuery(row, spec), row.target,
    "it searched the slug rather than the subject");
});

/* ── 8. what a green run is called ──────────────────────────────── */

await t("the desk never calls an unmerged acquisition published", () => {
  /* A pull request is a question until something answers it. The run merges
   * itself now, so the panel has two endings — and the promise this check
   * protects is not a string, it is that the two are TOLD APART. `gh pr
   * merge` can be refused by branch protection, a required review or a
   * conflict, and the workflow deliberately stays green on that because the
   * photographs are already acquired, registered, gated and pushed. So a
   * green run is not a merged one, and the desk must read `merged` off the
   * pull request rather than infer it from the step.
   *
   * The unmerged sentence is the one that must survive verbatim: it is the
   * boundary the whole design is built on. */
  const js = fs.readFileSync(
    path.join(ROOT, "desk", "public", "desk.js"), "utf8");
  assert.ok(!/textContent = "Published/.test(js));
  assert.match(js, /Nothing on europedoor\.com has changed/);
  assert.match(js, /job\.merged/,
    "the panel reports one outcome for two different states");
  /* AND THE MERGED SENTENCE MAY NOT CLAIM THE SITE HAS ALREADY CHANGED.
   * A merge is a commit to the default branch; a reader sees it when the
   * deployment runs, which is a different moment. */
  assert.match(js, /next deployment/);
});

await t("the merge is read from the pull request, never from the run", () => {
  /* THE STEP IS GREEN WHETHER THE MERGE HAPPENED OR NOT — that is a
   * deliberate choice in the workflow, so that a refused merge does not
   * report a loss that did not occur. Which makes the step useless as
   * evidence, and `merged_at` on the pull request the only honest source.
   * Reporting it from the step would be the `action_required` failure
   * again: a verdict nobody has reached. */
  const st = fs.readFileSync(path.join(API, "status.js"), "utf8");
  assert.match(st, /merged_at/);
  const wf = fs.readFileSync(
    path.join(ROOT, ".github", "workflows", "photograph.yml"), "utf8");
  const merges = wf.match(/gh pr merge/g) || [];
  assert.strictEqual(merges.length, 2,
    `both the single and the batch job merge: found ${merges.length}`);
  /* IT RUNS AFTER EVERY GATE, so it cannot reach a red run. */
  assert.ok(wf.indexOf("Run every gate") < wf.indexOf("gh pr merge"),
    "the merge runs before the gates");
});

console.log = realLog; console.error = realErr;

console.log("EuropeDoor — the hosted Media Desk\n");
if (failures.length) {
  console.log(`${failures.length} failure(s):`);
  for (const f of failures) console.log("  - " + f);
  console.log(`\n${passed} passed, ${failures.length} failed`);
  process.exit(1);
}
/* THE CLOSING LINE SAYS WHAT IS TRUE AND NOT WHAT IT USED TO SAY. It read
   "nothing was acquired, dispatched or fetched" and one test now lets a
   dispatch through on purpose, to inspect what goes out. A suite whose
   summary is a sentence nobody re-read is the same failure as a green run
   that has stopped counting: the output still looks like a result. */
console.log(`all ${passed} checks passed. Every request went to a replaced `
          + `fetch, so no provider was reached and no workflow was started; `
          + `one test inspects a dispatch that never left this process.`);
