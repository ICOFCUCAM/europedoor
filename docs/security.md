# Security

## The position

The attack surface of this product is a set of static files. There is no
server, no database, no session, no cookie, no upload, no form that posts
anywhere, and no third-party origin. Most of the standard checklist does not
apply because the thing it protects does not exist.

That is not an argument for complacency. It is an argument for keeping it
true, which is what the checks below do.

## What is enforced, on every build

**Content-Security-Policy: `default-src 'none'`** with no `'unsafe-inline'`
in any directive. This holds only because of two properties of the pages:

- **no inline `<script>` anywhere.** Page data goes in an inert
  `<script type="application/json">` block, parsed by the script that needs
  it. One inline script would force `script-src` open on all 988 pages.
- **no `style=` attribute anywhere.** Chromium's own message says CSP hashes
  do not apply to style attributes, so unlike an inline `<style>` block they
  cannot be excepted individually — one would force `style-src` open
  everywhere. 987 pages' worth were replaced with utility classes.

A check fails the build on either, and on any third-party origin.

**`frame-ancestors` is in the header only.** A browser ignores it in a meta
tag and logs that it did. A directive that is ignored is worse than a missing
one because it reads as protection.

**Both header files derive from one source.** `render.HEADERS` produces
`site/_headers` and is checked against `vercel.json`. See `docs/deployment.md`
for the production gap this closed.

**Full set:** CSP, `Strict-Transport-Security` (1 year, includeSubDomains),
`X-Content-Type-Options: nosniff`, `Referrer-Policy:
strict-origin-when-cross-origin`, `Cross-Origin-Opener-Policy: same-origin`,
and `Permissions-Policy` refusing geolocation, camera, microphone, payment,
USB and interest-cohort — nothing on this site asks for a device capability,
so every one of them is refused rather than left at the browser default.

**No secrets.** There are none to hold: no API key, no token, no connection
string, no `.env`. Nothing to leak and nothing to rotate.

**No third-party code.** Zero external scripts, fonts, tiles, analytics or
error reporting. Verified by a check across all 988 pages.

## Input handling

The two places that take input are both client-side and both validate:

- **The planner's sentence box** is parsed by word-boundary rules in the
  browser. It is never sent anywhere and never interpolated into HTML without
  escaping.
- **My Europe's list transfer** accepts pasted JSON, and treats it as
  untrusted: every item's `url` must be a same-origin absolute path, so an
  off-site or `javascript:` URL is dropped with a count shown to the reader.
  A browser check asserts exactly that.

Server-side escaping is centralised in `render.esc()` and every interpolation
goes through it.

## What is not implemented, and why

RBAC, rate limiting, CSRF, session security, audit logging, secret
management, secure file handling. **All of them protect a server, an account
or an upload, and there are none.** Each is specified in
`docs/technical-foundation.md` §5 and arrives with authentication — which
arrives with a data controller, which arrives with a company.

Building authentication before there is a company legally answerable for the
data is not caution. It is collecting personal data with nobody responsible
for it.

## Reporting

There is no security contact yet, because there is no entity to be
responsible. Until then the repository's issue tracker is the honest answer,
and `/sources` says so.
