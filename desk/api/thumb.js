/* SERVE ONE PREVIEW, BY SIGNED TOKEN.
 *
 * The token is `sign({u, exp})` minted by a search THIS DESK performed. A
 * caller cannot make one without the signing secret, so there is no
 * caller-supplied address here even though a URL travels through the token —
 * which is the distinction the local desk's comment draws and is worth
 * restating, because the shape looks the same from outside.
 *
 * THE HOST ALLOWLIST STAYS. A signature proves this desk minted the address;
 * it does not prove the address is a provider's image CDN, and it would go
 * on proving nothing if the signing secret ever leaked. Two independent
 * reasons to refuse is the posture this repository takes everywhere else.
 *
 * A PREVIEW IS NEVER THE ACQUISITION. These bytes are somebody else's
 * photographs with no register row, no hash and no date — the exact thing
 * the licence gate refuses — so they are proxied for looking at and never
 * written anywhere. The workflow fetches `original` BY ID and hashes that.
 */

import { requireSession, send, verify, PROVIDERS } from "./_lib.js";

const HOSTS = new Set(
  Object.values(PROVIDERS).flatMap((p) => p.thumbHosts));

export default async function handler(req, res) {
  if (!requireSession(req, res)) return;

  const url = new URL(req.url, "http://desk");
  const payload = verify(url.searchParams.get("t") || "");
  if (!payload || !payload.u) {
    /* An expired or forged token serves NOTHING, and says which so the
     * editor searches again rather than reloading a dead sheet. */
    send(res, 400, { error: "that preview token is not one this desk minted, "
                          + "or it has expired. Search again." });
    return;
  }

  let target;
  try { target = new URL(payload.u); } catch { target = null; }
  if (!target || target.protocol !== "https:" || !HOSTS.has(target.hostname)) {
    send(res, 400, { error: "not a provider image host" });
    return;
  }

  const r = await fetch(target.href);
  if (!r.ok) { send(res, 502, { error: `the provider answered ${r.status}` }); return; }

  const type = r.headers.get("content-type") || "";
  if (!/^image\//.test(type)) {
    send(res, 502, { error: "that was not an image" });
    return;
  }
  const bytes = Buffer.from(await r.arrayBuffer());
  res.statusCode = 200;
  res.setHeader("Content-Type", type);
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("Referrer-Policy", "no-referrer");
  /* PRIVATE AND SHORT. A preview belongs to one editor's session and is not
   * a public asset; `immutable` is a promise about a URL, and this URL can
   * change — the lesson the stylesheet already taught this repository. */
  res.setHeader("Cache-Control", "private, max-age=600");
  res.end(bytes);
}
