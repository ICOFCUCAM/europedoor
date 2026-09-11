import crypto from "node:crypto";
import { COOKIE, SESSION_HOURS, SIGNIN_DELAY_MS, body, guardPost, send, sign }
  from "./_lib.js";

/* ONE PASSCODE, ONE OPERATOR, AND NO USER STORE.
 *
 * Inventing accounts, roles and password hashes for a single-operator tool
 * is security theatre with a migration attached. What a public origin does
 * change from the local desk is the cost of a guess, so the comparison is
 * constant-time and every attempt — right or wrong — costs the same fixed
 * delay. The delay is not a lockout: locking a one-person tool out of itself
 * is a worse failure than the one it prevents. */
export default async function handler(req, res) {
  if (!guardPost(req, res)) return;
  const want = process.env.DESK_PASSCODE || "";
  if (!want) {
    return send(res, 500, { error: "DESK_PASSCODE is not set on this deployment" });
  }
  const given = String((await body(req)).passcode || "");
  await new Promise((r) => setTimeout(r, SIGNIN_DELAY_MS));
  const a = Buffer.from(crypto.createHash("sha256").update(given).digest());
  const b = Buffer.from(crypto.createHash("sha256").update(want).digest());
  if (!crypto.timingSafeEqual(a, b)) {
    return send(res, 401, { error: "that is not the passcode" });
  }
  const token = sign({ exp: Date.now() + SESSION_HOURS * 3600_000 });
  /* Secure, because this one is served over https and a session cookie that
   * can travel in clear is not a session cookie. */
  send(res, 200, { signed_in: true }, {
    "Set-Cookie": `${COOKIE}=${token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=${SESSION_HOURS * 3600}`,
  });
}
