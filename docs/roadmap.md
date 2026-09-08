# Roadmap

> **September 2026:** a transformation brief has arrived and its audit is in
> [`EUROPEDOOR_2036_TRANSFORMATION.md`](EUROPEDOOR_2036_TRANSFORMATION.md).
> That document supersedes the ordering below for anything visual or
> geographic; this file remains the record of the ten-phase development brief
> and of what each blocked phase is blocked on. The two agree on the
> substance: the stack does not change yet, and the map is the largest gap.

Read `docs/audit-2026-09.md` first — it is the repository audit this roadmap
came out of, and it explains the one decision that governs everything below:
**the stack does not change yet.**

Regenerate the counts before trusting them: this file was stale for three
sessions (it claimed 8 journeys, 8 stories, 23 checks and 204 assertions long
after all four had moved). Where a number matters, it is now stated as
"see the generated document" rather than copied here.

## The governing constraint

Every remaining phase in the product brief is blocked on the same thing, and
it is not technical:

> **There is no incorporated entity.** No entity means no data controller;
> no data controller means no accounts; no accounts means no user profiles,
> no reviews, no business dashboards, no CMS for a writer who is not a
> committer, no analytics and no payments.

Phases 5, 6, 7 and 9 of the brief are downstream of that, entirely. Building
authentication before there is a company to be responsible for the data is
not "getting ahead" — it is collecting personal data with nobody legally
answerable for it.

Phases 0–4 are not blocked, and that is where the work is.

## Where each phase actually stands

| phase | brief calls it | state | why |
|---|---|---|---|
| **0** | Foundation | **mostly done, gaps named below** | design system, error handling, test infra and CI all exist. Auth and DB are deliberately absent |
| **1** | Europe knowledge foundation | **done** | 50 countries → 130 regions → 319 destinations → 192 places → 197 experiences, validated, with sources and verification states |
| **2** | Public discovery | **done** | every surface ships; SEO gap named below |
| **3** | Journey system | **done** | curated journeys, itinerary builder, save, share, and full stop-level editing: reorder, lengthen, shorten, remove, add |
| **4** | AI | **rules, no model** | the whole pipeline except the model: intent extraction, retrieval, planning, refusal. See `docs/ai.md` |
| **5** | Users | **blocked** | browser-local only. Needs a data controller |
| **6** | Businesses | **blocked** | needs authentication |
| **7** | Editorial | **git is the CMS** | works for committers; a browser editor needs auth |
| **8** | Events | **partial** | the recurring European year ships. Dated listings need a feed and a rights position |
| **9** | Analytics and monetisation | **blocked** | needs traffic and an entity |

## Next, in order

### Phase 0 — close the foundation gaps

1. ~~**Security headers never reached production.**~~ **Done.**
   `site/_headers` is Netlify syntax and this deploys to Vercel, which
   ignores it. HSTS, nosniff, Permissions-Policy and frame-ancestors were
   absent from every response. Both files now come from `render.HEADERS` and
   a check fails on drift.
2. **The documentation set the brief asks for** — `product.md`,
   `development.md`, `database.md`, `api.md`, `ai.md`, `deployment.md`,
   `security.md`, `content-model.md`. **Done this session.**
3. **A `README` that gets a new engineer to a running build in five
   minutes.** Currently thin.

### Phase 2 — the one real SEO gap

4. ~~**Structured data.**~~ **Done.** Seven schema types across the Atlas,
   journeys, stories and the homepage — `Country`, `TouristDestination`,
   `TouristAttraction`, `TouristTrip`, `Article`, `WebSite` and a
   `BreadcrumbList` on every entity page. 2,152 items, validated on every
   build against the *visible* page, so a machine-readable breadcrumb cannot
   drift from the one a reader sees.

   The absences are deliberate and enforced: no `aggregateRating` (there are
   no reviews), no `offers` or `price` (nothing is bookable), no
   `openingHours` (the validator refuses the field), no `image` (there are no
   photographs), and no `Event` (our festivals are recurring fixtures with no
   dated instance, and `schema.org/Event` requires `startDate`). A wrong rich
   result is worse than none: it is a claim, in a format designed to be
   trusted, republished by somebody who cannot check it.

5. ~~**Open Graph images.**~~ **Done.** 718 social cards at 1200×630, one
   per entity, rendered in pure Python — `tools/lib/raster.py`, a scanline
   filler and a PNG encoder on `zlib` and `struct`. No Pillow, no headless
   browser, no change to a dependency list that is still empty.

   They render from `render.plate_shapes()`, the **same geometry the SVG on
   the page comes from**. A second drawing would only ever be seen inside
   somebody else's product, so nobody here would notice it drifting — a
   check asserts both renderers are still driven by that one function.

   Cost: ~23 ms each, so they are content-addressed and cached in
   `assets/og/`. First build 24 s, every build after that 2 s, and anything
   no page asks for is pruned so the cache cannot fill with orphans from
   past versions of the drawing.

### Phase 2 — what is left

6. **Text on the social cards.** They are the illustration alone. A card
   carrying the place name would be stronger, and rendering text needs
   glyph outlines — a bitmap font compiled into the repository, or the one
   dependency this would justify. Not obviously worth it yet.

### Phase 3 — finish the journey system

7. ~~**Reorder and edit a saved itinerary.**~~ **Done.** Any stop can be
   moved earlier or later, lengthened, shortened or removed, and the days,
   distances and estimate all recompute from the reader's version rather
   than the planner's.

   Buttons, not drag handles. Drag-and-drop is unusable with a keyboard,
   unusable with a screen reader and miserable on a phone; for a list of at
   most fourteen things, "move earlier" is a better interaction that merely
   looks less impressive — and it is testable, which drag is not.

   The edited route is carried explicitly and travels in the share link,
   because regenerating from the form inputs would re-run a planner that
   deliberately jitters and hand somebody a different trip.

8. ~~**Adding a stop to an existing route.**~~ **Done.** Every leg carries
   "+ stop after", opening a filter over the whole Atlas — which is already
   in memory, so it is an array filter rather than a request.

   Three things make it usable rather than merely present: a city already on
   the route is never offered, the distance from the stop it would follow is
   on every row (on a route the question is always what a stop *costs*, and
   a list that hides it invites a 900 km detour that looks like a small
   edit), and accents fold exactly as they do in search — a reader who can
   find Malmö there and not here would be right to think one of them is
   broken.

**Phase 3 is complete.**

### Phase 1 — the dataset, which is the actual asset

9. **Places: 192 of a 1,000 MVP target.** 44 countries have none at all.
10. **Stories: 9 of 100.** Roughly a day each, and not automatable.
11. **Fact verification: 0 of 50 countries.** The machinery is built and
   expires correctly; nobody has done a check. This is the single biggest
   credibility gap on the site and it is published as such.

`docs/content-report.md` is regenerated every build and is the authority on
these three.

### Blocked, and the order they unblock in

12. Entity incorporated → data controller → accounts → **Phase 5**
13. Accounts → operator claims → **Phase 6**
14. Accounts → contributor roles → **Phase 7** browser CMS
15. Traffic → **Phase 9**

## What this roadmap deliberately does not do

- **No Next.js rewrite.** `docs/technical-foundation.md` describes the
  destination and names the trigger. None of the triggers has fired.
- **No database.** 988 pages are generated from validated files in 4 seconds
  with zero dependencies. A database would add a bill, an attack surface and
  an operational burden, and unblock nothing on this list.
- **No seeded business listings.** A directory of businesses that have not
  claimed their entry and cannot be verified is the exact thing this project
  refuses to publish.
- **No AI-generated factual content.** Ever, in bulk, without review.
