/* THE HOSTED MEDIA DESK — everything the functions share.
 *
 * THE LOCAL DESK HELD STATE AND THIS ONE CANNOT, WHICH CHANGES TWO THINGS.
 *
 * `tools/desk/serve.py` is one process: a session is a random token in a
 * dictionary and a thumbnail is a token in a map. Two serverless invocations
 * share no memory at all, so a dictionary here would work on the request that
 * wrote it and fail on the next one — the classic port of a stateful design
 * that appears to work in testing because testing hits one warm instance.
 *
 * Both become SIGNED VALUES instead. A session is a signed expiry and a
 * thumbnail is a signed URL: the server can verify it minted the thing
 * without having remembered it.
 *
 * THAT IS NOT THE ALLOWLIST-IN-FRONT-OF-AN-SSRF THE LOCAL DESK REFUSED. The
 * objection there was that a route fetching a caller-supplied address is
 * guarded by something the next person widens. A signature is not a guard on
 * a caller's address; it is proof the address came from a search THIS DESK
 * performed. A caller cannot forge one without the secret, and the host
 * allowlist stays as well, because two independent reasons to refuse is the
 * posture this repository takes everywhere else.
 *
 * NO DEPENDENCIES. Node's own crypto and fetch, same as the rest of the
 * product: `package.json` has no runtime dependency and this does not add
 * one. A desk that needs an npm install is a desk with a supply chain.
 */

import crypto from "node:crypto";
import fs from "node:fs";

export const COOKIE = "desk";
export const SESSION_HOURS = 12;

/* A FAILED SIGN-IN COSTS TIME, and on a public origin that matters far more
 * than it did on 127.0.0.1. Not a lockout — a lockout on a single-operator
 * tool locks the operator out — but a fixed delay, so the passcode cannot be
 * walked quickly. */
export const SIGNIN_DELAY_MS = 700;

function need(name) {
  const v = process.env[name];
  if (!v) throw new Error(`${name} is not set on this deployment`);
  return v;
}

export function secret() {
  /* A SEPARATE SECRET FROM THE PASSCODE, because they are different things
   * with different lifetimes: rotating the passcode should not invalidate
   * nothing else, and the signing key should never be something a person
   * types. If it is unset the desk refuses to sign anything rather than
   * falling back to a constant — a default signing key is no signing key. */
  return need("DESK_SESSION_SECRET");
}

const b64 = (buf) => Buffer.from(buf).toString("base64url");

export function sign(payload) {
  const body = b64(JSON.stringify(payload));
  const mac = b64(crypto.createHmac("sha256", secret()).update(body).digest());
  return `${body}.${mac}`;
}

export function verify(token) {
  if (!token || typeof token !== "string") return null;
  const [body, mac] = token.split(".");
  if (!body || !mac) return null;
  const want = b64(crypto.createHmac("sha256", secret()).update(body).digest());
  /* timingSafeEqual throws on a length mismatch, which is itself a leak of
   * one bit and a crash of the function; compare lengths first. */
  if (mac.length !== want.length) return null;
  if (!crypto.timingSafeEqual(Buffer.from(mac), Buffer.from(want))) return null;
  let payload;
  try { payload = JSON.parse(Buffer.from(body, "base64url").toString()); }
  catch { return null; }
  if (!payload || typeof payload.exp !== "number") return null;
  if (payload.exp < Date.now()) return null;
  return payload;
}

export function cookieFrom(req) {
  const raw = req.headers.cookie || "";
  for (const part of raw.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === COOKIE) return rest.join("=");
  }
  return "";
}

export function authed(req) {
  return !!verify(cookieFrom(req));
}

/* EVERY RESPONSE CARRIES THE HEADERS THE SITE CARRIES. A tool is not the
 * exception to a posture; it is where the credential is. */
export function send(res, code, body, extra = {}) {
  const text = typeof body === "string" ? body : JSON.stringify(body);
  res.statusCode = code;
  res.setHeader("Content-Type",
    typeof body === "string" ? "text/plain; charset=utf-8" : "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("Referrer-Policy", "no-referrer");
  for (const [k, v] of Object.entries(extra)) res.setHeader(k, v);
  res.end(text);
}

/* A cross-site form can POST with the cookie attached and cannot set a
 * custom header. SameSite=Strict is the first answer and this is the second,
 * because one control is not a control. */
export function guardPost(req, res) {
  if (req.method !== "POST") { send(res, 405, { error: "POST only" }); return false; }
  if (req.headers["x-desk"] !== "1") {
    send(res, 400, { error: "not a desk request" });
    return false;
  }
  return true;
}

export function requireSession(req, res) {
  if (authed(req)) return true;
  send(res, 401, { error: "sign in first" });
  return false;
}

export async function body(req) {
  if (req.body && typeof req.body === "object") return req.body;
  const chunks = [];
  let n = 0;
  for await (const c of req) {
    n += c.length;
    if (n > 1 << 20) throw new Error("body too large");
    chunks.push(c);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString() || "{}"); }
  catch { return {}; }
}

/* ── the generated slot registry ────────────────────────────────── */
/*
 * READ AS A FILE RATHER THAN IMPORTED, AND THAT IS A DEPLOYMENT FACT RATHER
 * THAN A PREFERENCE. `import reg from "../registry.json" with {type:"json"}`
 * is the tidier line and it is a runtime-version bet: import attributes need
 * Node 22, the older spelling was `assert`, and a desk that stops deploying
 * when the platform's default runtime moves is a desk nobody can fix at the
 * moment they need it. `new URL(..., import.meta.url)` is the idiom Vercel's
 * own file tracer recognises, so the JSON is bundled, and readFileSync works
 * on every Node this could ever run on.
 *
 * ONE COPY, READ ONCE PER COLD START. Every function that needs a slot's
 * numbers reads them from here, because two copies of the requirements is
 * two answers to "what does this slot need" — which is the failure the slot
 * system was built to end.
 */
let REG = null;

export function registry() {
  if (!REG) {
    REG = JSON.parse(
      fs.readFileSync(new URL("../registry.json", import.meta.url), "utf8"));
  }
  return REG;
}

/* The requirements of a purpose. A TEMPLATED INSTANCE HAS NONE OF ITS OWN —
 * they belong to the slot, stated once — so this is where the two halves are
 * put back together, in one place, rather than in each caller. */
export function specOf(purpose) {
  const reg = registry();
  const row = reg.purposes.find((p) => p.purpose === purpose);
  if (!row) return null;
  const slot = row.slot ? reg.slots[row.slot] : null;
  return { ...(slot || {}), ...row };
}

/* ── the provider ───────────────────────────────────────────────── */

export const PROVIDERS = {
  pexels: {
    name: "Pexels",
    env: "PEXELS_API_KEY",
    base: "https://api.pexels.com/v1",
    thumbHosts: ["images.pexels.com"],
  },
};

export async function providerSearch(slug, query, orientation, perPage) {
  const cfg = PROVIDERS[slug];
  if (!cfg) return { error: `${slug} is not a provider this desk knows` };
  const key = process.env[cfg.env];
  if (!key) return { error: `${cfg.env} is not set on this deployment` };
  const qs = new URLSearchParams({
    query, orientation, per_page: String(perPage), size: "large",
  });
  const r = await fetch(`${cfg.base}/search?${qs}`, {
    headers: { Authorization: key, Accept: "application/json" },
  });
  /* RATE LIMITS ARE REPORTED AND NEVER RETRIED AROUND. A loop that retries
   * into a 429 is how an integration gets a key revoked, and the brief
   * forbids it by name. One attempt, and the reader is told to wait. */
  if (r.status === 429 || r.status === 403) {
    return { error: "The provider is rate-limiting or has refused this key. "
                  + "Nothing here retries, because retrying into a limit is "
                  + "how a key gets revoked. Wait and search again.",
             rateLimited: true };
  }
  if (!r.ok) return { error: `the provider answered ${r.status}` };
  return { payload: await r.json() };
}

export function normalise(slug, payload) {
  if (slug !== "pexels") return [];
  return (payload.photos || []).map((p) => ({
    id: String(p.id ?? ""),
    photographer: p.photographer || "",
    photographer_url: p.photographer_url || "",
    page: p.url || "",
    width: Number(p.width || 0),
    height: Number(p.height || 0),
    alt: p.alt || "",
    /* THE PREVIEW IS FOR LOOKING AT AND IS NEVER THE ACQUISITION. The
     * workflow fetches `original` by id and hashes THAT; these bytes never
     * touch the register. */
    preview: (p.src && (p.src.large2x || p.src.large)) || "",
    hasOriginal: !!(p.src && p.src.original),
  })).filter((c) => c.id && c.page && c.preview && c.hasOriginal);
}

/* The mechanical half of "does this photograph suit this slot". The
 * editorial half — subject placement, whether it reads as generic stock — is
 * why candidates go to a person instead of being picked here. */
export function fits(c, spec) {
  const bad = [];
  if (spec.min_width && c.width < spec.min_width) {
    bad.push(`${c.width}px wide, and this slot needs ${spec.min_width} native `
           + `pixels — derive.py refuses to upscale`);
  }
  const aspect = c.height ? c.width / c.height : 0;
  if (spec.orientation === "landscape" && aspect < 1) bad.push("it is portrait");
  if (spec.orientation === "portrait" && aspect > 1) bad.push("it is landscape");
  if (spec.min_aspect && aspect < spec.min_aspect) {
    bad.push(`aspect ${aspect.toFixed(2)}, below this slot's ${spec.min_aspect}`);
  }
  if (spec.max_aspect && aspect > spec.max_aspect) {
    bad.push(`aspect ${aspect.toFixed(2)}, above this slot's ${spec.max_aspect}`);
  }
  return bad;
}

/* ── GitHub ─────────────────────────────────────────────────────── */
/* The desk dispatches a workflow and reads the register; both go through the
 * same token, which lives only in this deployment's environment. */

export function repo() {
  return {
    slug: process.env.DESK_REPO || "ICOFCUCAM/europedoor",
    branch: process.env.DESK_BRANCH || "main",
    workflow: "photograph.yml",
  };
}

export async function gh(path, init = {}) {
  const token = need("DESK_GITHUB_TOKEN");
  const r = await fetch(`https://api.github.com${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "europedoor-media-desk",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(init.headers || {}),
    },
  });
  return r;
}

/* ── the live register ──────────────────────────────────────────── */
/*
 * READ FROM THE REPOSITORY, ON THE DEFAULT BRANCH, AND NOT FROM A BUNDLE.
 *
 * A photograph acquired an hour ago must show as filled without redeploying
 * this desk, so the status cannot be generated into `registry.json` — a
 * status baked into a build is a status that goes stale.
 *
 * AND THE DEFAULT BRANCH IS THE HONEST SOURCE, not the branch an acquisition
 * just pushed. The pull request IS the gate: a photograph sitting in an open
 * PR has been acquired and has not been accepted, and a desk that called it
 * PUBLISHED would be reporting the reviewer's decision before the reviewer
 * made it. The site does not publish the register either, which is the other
 * reason this reads the repository — adding a public document to carry it
 * would put a new surface on the production origin to serve an internal
 * tool.
 */
export async function register() {
  const { slug, branch } = repo();
  try {
    const r = await gh(`/repos/${slug}/contents/data/images.json?ref=${branch}`,
                       { headers: { Accept: "application/vnd.github.raw+json" } });
    if (!r.ok) return {};
    const j = JSON.parse(await r.text());
    return j.images || {};
  } catch { return {}; }
}
