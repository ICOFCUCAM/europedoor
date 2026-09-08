# EuropeDoor — working notes

A static site: 1,059 generated HTML files, no dependencies, no database. Every
page comes from `data/` via `tools/build.py`. Nothing in `site/` was written
by a human and nothing ever should be.

**The name is EuropeDoor, at europedoor.com — one word, title case. It does
not change, and the mark is NOT cleared.** Strategy
documents keep arriving with alternatives on them — Europe Atlas, Europia,
Via Europa. Take their architecture and drop their branding section. See
`docs/brand-lock.md`; `tools/checks.py` enforces it.

## Read these first, depending on the work

| doing | read |
|---|---|
| **starting a session — read this first** | **`docs/audit-2026-09.md`** — the repository audit: current stack, what exists, technical debt, and the one open architectural decision (Next.js/Postgres: not yet, and why). Then **`docs/roadmap.md`** |
| **anything substantial** | **`docs/product-specification.md`** — both specifications answered: the 36-section brief in Parts 1–3, the 99-section one in Part 4. Plus the Postgres schema, the API, the AI pipeline with actual prompts, the dashboards, the money and the risks |
| changing how pages are generated | **`docs/architecture.md`** — the four rules the build depends on |
| adding or editing a place | **`docs/data-model.md`** — every field, and what the validator rejects |
| the scores | **`docs/scoring-method.md`** — and note the formula is published at `/method`, so changing `score.py` changes a public page |
| anything involving money | **`docs/europe-fund.md`** and **`docs/legal-position.md`** — three gates, all currently shut |
| naming, branding, domains | **`docs/brand-lock.md`** — settled, enforced, and the trademark is contested: EUROPEDOOR is in use in the doors trade, so no ®, no ™, nothing announced |
| **colour, the mark, voice, the manifesto** | **`docs/brand.md`** — the Brand Bible as built, including the four logo directions that were rejected and why |
| photographs, or "why is there no picture here" | **`docs/images.md`** — the pipeline is built and enforced; the library is empty |
| **the Postgres/PostGIS model, the API, Next.js, auth, search, the AI pipeline** | **`docs/technical-foundation.md`** — a destination with a trigger, not a plan for Monday. Nothing in it should be built yet |
| what to build next | **`docs/roadmap.md`**, and **`docs/content-report.md`** for where the dataset is thin |
| **"did we actually implement section N?"** | **`docs/section-audit.md`** — generated, never hand-edited. 100 sections, 1,273 assertions against the real build, and CI fails if any of them stops being true |
| **anything visual — layout, navigation, states, mobile** | **`docs/ux-specification.md`** — the 37-section design brief answered, including the seven things it asks for that this product will not do and why. **`docs/ux-audit.md`** is the generated evidence: 43 sections, 231 assertions |

## The rules that catch people out

**`site/` is deleted on every build.** Editing a generated page is work that
disappears on the next `build.py` with no warning and no failing check. If a
page needs to say something new, it says it in `tools/lib/pages.py` or in
`data/`.

**There is exactly one page shell.** `render.page()` is the only function
that emits `<html>`. Do not add a second, and do not add an inline `<style>`
to a page — `checks.py` fails on both, because a masthead that exists twice
diverges within a month.

**The generated site is committed, and CI fails if it is stale.** After any
change to `data/`, `tools/` or `assets/`, run `python3 tools/build.py` and
commit `site/` in the same commit. A stale `site/` means the checks validated
output nobody is going to serve.

**Advisory countries are stripped from the planner index at build time**, not
hidden in the UI. Ukraine, Russia and Belarus keep a page carrying the
warning and are absent from `/api/atlas.json`. Do not "fix" this by filtering
in JavaScript.

**One drawing, two renderers.** `render.plate_shapes()` is the geometry;
`plate()` emits SVG and `raster.plate_png()` emits the social card. Never add
a shape to one only — a card that stops matching its page is invisible from
here, because it is rendered inside somebody else's product. A check asserts
both still come from `plate_shapes`. Cards are cached in `assets/og/`,
content-addressed, and pruned: first build 24s, every build after that 2s.

**Structured data claims only what we hold.** JSON-LD is a machine-readable
claim republished by people who cannot check it, so `checks.py` refuses
`aggregateRating`, `offers`, `price` and `openingHours` anywhere in it, refuses
an empty property (present-but-empty says "we have this" and then does not),
and asserts every `BreadcrumbList` matches the breadcrumb a reader can see.
`application/ld+json` is exempt from the inline-script rule because Chromium
reports zero CSP violations for it — verified, not assumed.

**Security headers live in `render.HEADERS`, and `vercel.json` is checked
against it.** Vercel does NOT read `site/_headers` — that is Netlify and
Cloudflare Pages syntax — so for as long as the headers lived only there,
HSTS, nosniff, Permissions-Policy and frame-ancestors were absent from every
production response while the repository looked correct. A check now fails on
drift between the two.

**The Fund holds nothing, and the checks enforce it.** No form, no payment
link, no amount raised, no progress bar on any `/fund` page; no `amount`,
`raised`, `goal` or `target` in `data/fund.json`. This is the single easiest
thing for a well-meaning person to break.

**No image without a photographer, a source and a licence.** This replaced
"no photographs at all", which was the right rule until there was a pipeline
and the wrong one after. `data/images.json` is the register, the validator
refuses a row missing any of the three, and `checks.py` refuses a published
page referencing a file with no row. Zero photographs are licensed today;
`docs/images.md` says why and what it would take. Everything else is a
generated plate — a landscape from the hash of the slug, with the motif taken
from what the place actually is.

**The Content-Security-Policy is strict, and the pages are what make it
possible.** `default-src 'none'`, no `'unsafe-inline'` in any directive. That
holds only because there is no inline `<script>` anywhere (page data goes in
an inert `application/json` block — see `render.jsondata`) and no `style="..."`
attribute anywhere (utility classes instead; CSP hashes do **not** apply to
style attributes, so one of them would force `style-src` open on all 987
pages). `checks.py` fails on either. `frame-ancestors` lives in `site/_headers`
only, because a browser ignores it in a meta tag and logs that it did.

**Two fixed bars on a phone, one token.** `--thumbbar` is the height of the
bottom navigation, and the sticky destination action, the footer padding and
the destination-page footer padding all derive their offsets from it. The
first version hard-coded 44px in those offsets while the bar rendered at 63,
so the action sat on top of the navigation. Only measuring both boxes in
Chromium finds that.

**A verification record expires.** A check is good for `REVIEW_DAYS` and then
reads as *due for review* again. Confidence is derived from the source kind
and the age of the check — the validator refuses an authored `confidence`
field, because a field a person can type is a field somebody will type "high"
into.

**No `rank`, `boost`, `featured` or `sponsored` field on a place.**
Sponsorship attaches to a provider and affects directory surfaces only. That
wall is enforced in the schema, which is the only version of the promise
worth making.

## Gates

Run all seven before claiming anything is done.

    python3 tools/build.py check       validate the data
    python3 tools/build.py           1,059 pages
    python3 tools/checks.py            28 checks, ~97,300 things examined
    node tools/browser-checks.js       409 checks in Chromium, incl. accessibility
    python3 tools/section-audit.py --check   the 99 spec sections, 1,273 assertions
    python3 tools/ux-audit.py --check        the 37 UI/UX + 6 brand sections, 231 assertions
    python3 tools/content-report.py --write  what is missing, against the spec's targets

The browser checks need `npm install playwright` and take a couple of
minutes. They earn their place repeatedly: a 47-pixel mobile overflow on
every city page, two colour tokens below the WCAG contrast line, a places
layer that could never be turned on because `.hidden` is not a property of an
SVG element, and a €700 fortnight routed through Switzerland. They also
caught the planner producing a 2,500 km final leg to reach a named end city
and calling it an itinerary. None of those was findable by reading the code.
They launch the sandbox's own Chromium via `executablePath` because the npm
package version will not match the installed browser build.

**Three of the gates write files.** `section-audit.py --write`, `ux-audit.py --write`
and `content-report.py --write` regenerate documents that CI then checks for
staleness, exactly like `site/`. Run them and commit the result.

## Adding a country

1. Write `data/countries/<slug>.json` against `docs/data-model.md`.
2. Add the slug to exactly one macro region in `data/taxonomy.json`.
3. `python3 tools/build.py check` — the validator lists every problem at
   once, so one run fixes one round of mistakes.
4. Build, run both check suites, commit `site/` with the data.

Depth beats breadth. 244 cities written properly beats 40,000 imported, and
there is no importer in this repository on purpose.

## Style

Long comments that explain *why*, usually naming the failure that prompted
the change. Keep them. Prefer recording a mistake to quietly deleting the
evidence of it — the note in `assets/css/europedoor.css` about the 47px
overflow is worth more than the two lines of CSS that fixed it.
