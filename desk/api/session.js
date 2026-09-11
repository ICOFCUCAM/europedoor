import { authed, send } from "./_lib.js";

export default function handler(req, res) {
  send(res, 200, { signed_in: authed(req) });
}
