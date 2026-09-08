# Roadmap

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
| **3** | Journey system | **mostly done** | 17 curated journeys, itinerary builder, save, share. Day-level drag-reorder is missing |
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

4. **Structured data.** No page emits JSON-LD. `TouristDestination`,
   `Country`, `Article`, `ItemList` and `BreadcrumbList` are all directly
   supported by data we already hold and validate. This is the highest-value
   unblocked work in the repository: it is what turns 988 correct pages into
   988 pages a search engine understands.
5. **Open Graph images.** `og:image` is absent. The plate generator already
   produces one per entity; it needs a rasterised endpoint or a committed PNG
   per surface.

### Phase 3 — finish the journey system

6. **Reorder and edit a saved itinerary.** The planner builds and saves; it
   cannot yet be edited stop-by-stop. This needs the frozen-document model in
   `docs/technical-foundation.md` §1.2, not a database.

### Phase 1 — the dataset, which is the actual asset

7. **Places: 192 of a 1,000 MVP target.** 44 countries have none at all.
8. **Stories: 9 of 100.** Roughly a day each, and not automatable.
9. **Fact verification: 0 of 50 countries.** The machinery is built and
   expires correctly; nobody has done a check. This is the single biggest
   credibility gap on the site and it is published as such.

`docs/content-report.md` is regenerated every build and is the authority on
these three.

### Blocked, and the order they unblock in

10. Entity incorporated → data controller → accounts → **Phase 5**
11. Accounts → operator claims → **Phase 6**
12. Accounts → contributor roles → **Phase 7** browser CMS
13. Traffic → **Phase 9**

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
