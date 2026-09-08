# Development

## Get a build in five minutes

```bash
git clone <repo> && cd europedoor
python3 --version          # 3.11+
python3 tools/build.py     # → site/, about 4 seconds
python3 -m http.server -d site 8000
```

There is nothing to install. No package manager, no lockfile, no virtualenv,
no `.env`. Python's standard library is the entire dependency list, and that
is a deliberate property rather than an accident — see `docs/architecture.md`.

The one optional dependency is Playwright, for the browser suite:

```bash
npm install --no-save playwright@1.49.0   # dev only, never committed
node tools/browser-checks.js
```

## The gates

All seven must pass before anything is called done. CI runs all seven.

```bash
python3 tools/build.py check         validate the dataset
python3 tools/build.py               988 pages
python3 tools/checks.py              25 static checks
node tools/browser-checks.js         389 checks in Chromium, incl. WCAG 2.2 AA
python3 tools/section-audit.py --check    the 99-section product spec
python3 tools/ux-audit.py --check         the 37-section UI/UX brief + brand
python3 tools/content-report.py --write   what is missing, against target
```

**Three of them write files.** `section-audit.py --write`, `ux-audit.py
--write` and `content-report.py --write` regenerate documents that CI then
checks for staleness, exactly like `site/`. Run them and commit the result.

## The rules that catch people out

**`site/` is deleted on every build.** Editing a generated page is work that
disappears on the next build with no warning and no failing check. If a page
needs to say something new, it says it in `tools/lib/pages.py` or in `data/`.

**The generated site is committed and CI fails if it is stale.** After any
change to `data/`, `tools/` or `assets/`, rebuild and commit `site/` in the
same commit.

**One page shell.** `render.page()` is the only function that emits `<html>`.
A second one diverges within a month.

**No inline `<style>` and no `style=` attribute.** Both fail a check. This is
what lets the Content-Security-Policy run `style-src 'self'` with no
`'unsafe-inline'`; one style attribute anywhere would force the policy open on
all 988 pages, and CSP hashes do not apply to style attributes.

**Security headers live in `render.HEADERS`,** and both `site/_headers` and
`vercel.json` are checked against it. Vercel reads `vercel.json`; it ignores
`_headers`.

## Adding a country

1. Write `data/countries/<slug>.json` against `docs/data-model.md`.
2. Add the slug to exactly one macro region in `data/taxonomy.json`.
3. `python3 tools/build.py check` — the validator lists every problem at once,
   so one run fixes one round of mistakes.
4. Build, run the gates, commit `site/` with the data.

## Adding a photograph

See `docs/images.md`. One row in `data/images.json` with a photographer, a
source and a licence. The validator refuses a row missing any of them.

## Style

Long comments that explain *why*, usually naming the failure that prompted
the change. Keep them. Prefer recording a mistake to quietly deleting the
evidence of it — the note about the 47px mobile overflow is worth more than
the two lines of CSS that fixed it.
