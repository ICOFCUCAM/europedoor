# Deployment

## How it deploys

Vercel. **`buildCommand` is empty**, `outputDirectory: site`,
`cleanUrls: true`. No runtime, no functions, no environment variables, no
secrets. The host copies `site/` and serves it.

```bash
python3 tools/build.py     # here, in the commit that changes data/ or tools/
```

The build runs on a contributor's machine and in CI, and CI fails if `site/`
differs from what the generator produces. **It does not run on the host, and
it used to.** `buildCommand: python3 tools/build.py` asked the deploy image to
reproduce, byte for byte, an artefact already sitting in the commit — so its
only two outcomes were "identical" and "the deployment failed". The second one
is silent from here: Vercel keeps the last good deployment live, so a build
that stops working leaves the site frozen on old pages while the repository,
the commit and every gate are correct. That is the same shape as the
`site/_headers` gap below and the `immutable` one above — repository right,
response wrong — and the fix is the same: take away the place the two can
disagree.

Rebuilding on the host was also the only reason the deploy image needed a
Python at all. It needs nothing now.

## The headers

`vercel.json` carries a catch-all rule with the full security header set, and
`tools/checks.py` **fails the build if it drifts from `render.HEADERS`**.

This check exists because of a real production gap: the headers lived only in
`site/_headers`, which is Netlify and Cloudflare Pages syntax. Vercel ignores
it. For as long as that was true, HSTS, `X-Content-Type-Options`,
`Permissions-Policy`, `Cross-Origin-Opener-Policy` and `frame-ancestors`
were **absent from every response in production**, while the repository looked
correct.

A security header that exists in the repository and not in the response is
worse than a missing one, because it stops anybody looking.

Caching: `/assets/*` immutable for a year (filenames are stable and content is
too), `/api/*` for 600s.

## Rollback

`git revert` and redeploy. `site/` is committed, so any previous deploy is a
complete, inspectable artefact — not a build that has to be reproduced.

## Environments

One: production. There is no staging, no preview database and no seeded
environment, because there is no database and no state. A Vercel preview
deployment of a branch is a complete, isolated copy of the whole product.

## Portability

The output is static files with no server requirement. Moving to Cloudflare
Pages, Netlify or S3 is a change of host, not of architecture — `site/_headers`
is already the Netlify/Cloudflare form of the same policy. That is deliberate:
no vendor holds anything that would be expensive to leave.
