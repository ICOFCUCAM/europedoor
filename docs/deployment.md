# Deployment

## How it deploys

Vercel. `buildCommand: python3 tools/build.py`, `outputDirectory: site`,
`cleanUrls: true`. No runtime, no functions, no environment variables, no
secrets.

```bash
python3 tools/build.py     # 988 pages + 4 APIs + sitemap + robots + _headers
```

Every deploy is a full rebuild from `data/`. There is no incremental path and
there does not need to be: the whole site builds in about four seconds.

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
