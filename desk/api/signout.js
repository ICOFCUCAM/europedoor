import { COOKIE, guardPost, send } from "./_lib.js";

export default function handler(req, res) {
  if (!guardPost(req, res)) return;
  send(res, 200, { signed_in: false }, {
    "Set-Cookie": `${COOKIE}=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0`,
  });
}
