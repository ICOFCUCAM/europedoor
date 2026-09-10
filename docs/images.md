# Photographs: the architecture, and the fact that there are none

The Brand Bible calls photography one of the most important parts of
EuropeDoor, and it is right. This file is the honest position: the pipeline
that serves a photograph is **built and enforced**, and the number of
photographs currently licensed is **zero**.

Those are two different statements, and most projects blur them. The
distinction matters because the shape of an image pipeline decides what a
licence audit costs two years from now, when there are eight thousand files
and nobody remembers where the third thousand came from.

## The four rules, all enforced

**1. No image without provenance.** A row in `data/images.json` must carry
`file`, `alt`, `photographer`, `source` (an https URL you can open) and
`licence` (from a closed list). `tools/lib/data.py` refuses a row that does
not, and `tools/checks.py` refuses a published page that references a file
with no row. There is no `unknown` and no default, so "we will fill that in
later" is not reachable from here.

An unlicensed photograph on a public page is the most expensive mistake a
travel site can make, and it is always made by accident — by an `<img>`
somebody added in a hurry. That is the specific thing being refused.

**2. Self-hosted, never hotlinked.** Every file is served from our own
origin. The Content-Security-Policy is `default-src 'none'` with `img-src
'self' data:`, so a hotlinked provider URL does not render at all. The policy
enforces the decision rather than a convention doing it. Hotlinking also
hands the provider every reader's IP address on every page view, which
contradicts `/privacy`.

**3. One eager image per page.** The hero is `loading="eager"` with
`fetchpriority="high"`; everything else is lazy and is never fetched until
somebody scrolls. Page weight is therefore **one question per page** rather
than a total, and a card grid of forty places costs nothing until it is
looked at. A check fails a page with two eager images.

**4. Every image carries its own dimensions.** `width` and `height` on the
tag, always, so nothing shifts when the file arrives.

## What is served

`<picture>` with AVIF, then WebP, then JPEG. Five widths — 480, 800, 1260,
1800, 2400 — as a fixed ladder, so filenames are predictable and can be
generated ahead of time.

Each row carries a **focal point** as `[x, y]` percentages, applied as
`object-position`. This is not a nicety: a 21:9 hero crop of a portrait
photograph, centred, takes the sky and loses the subject. It is the
commonest way a responsive hero goes wrong.

Credits are in the markup on every image, shown on hover and focus on a
desktop and always visible on a phone. Always-visible credits on 988 pages is
a design nobody ships; credits that live only in a data file are a licence
risk. This is the compromise, and a screen reader reads them either way.

## Adding one — the automated route, which is the one to use

For a provider the gate clears for automated acquisition, **nobody downloads
or uploads anything by hand.** `.github/workflows/photograph.yml` does the
whole of it and a person makes exactly one decision: which photograph.

1. Declare the purpose in `data/image-purposes.json` if it is not there —
   the surface, the register key, the page, the native width, the
   orientation and the aspect range. A photograph with no declared purpose is
   refused before the socket opens.
2. Dispatch the workflow with **stage: discover** and a query. It prints
   candidates — id, photographer, page, native width, and whether each meets
   the purpose. It downloads nothing and names no winner.
3. Open the pages. Choose one. **This is the only human step.**
4. Dispatch again with **stage: acquire**, that photo id, and an `alt` written
   for somebody who cannot see it. The runner fetches that id, asserts the id
   it got back is the id asked for, downloads, hashes, keeps the untouched
   original, builds the ladder, completes the provenance, runs every gate and
   opens a pull request.
5. Read the PR and merge it. Its body is generated from the register the
   acquisition wrote, so it cannot describe a different photograph.

If the id cannot be retrieved the workflow fails. It never substitutes another
photograph, because a substitute is a picture nobody approved wearing correct
provenance.

## Adding one by hand, where that is the only cleared route

Unsplash is this case: its licence permits the use and its API guidelines
refuse the machine.

1. Put the file through the width ladder as
   `assets/img/<name>.<original-sha-prefix>-<width>.{avif,webp,jpg}` —
   `scripts/images/derive.py` does the naming, and the hash in the name is
   what earns the `immutable` header on `/assets/`.
2. Add a row keyed by what it illustrates —
   `city:norway/fjord-norway/bergen`, `journey:<slug>`, `story:<slug>`,
   `place:<country>/<region>/<city>/<place>` — carrying the source URL, the
   date and the SHA-256 of the bytes as served.
3. `python3 tools/build.py check`, then build and commit.

Nothing else changes. Callers never branch on whether a photograph exists:
they ask `picture()` for one and get the best thing available. That is what
makes the library adoptable **one photograph at a time** rather than as a
migration.

## Opening the licence gate when the provider refuses the machine

`scripts/images/verify_provider.py` fetches each provider's terms, archives it
with the date and the SHA-256 of the bytes as served, and prints the passages
worth reading. It answers nothing: `checks.py` requires a verbatim quote per
fact and asserts that quote appears in the archived page it cites.

**Both providers refuse an automated request, and that is where this stopped.**
On a GitHub runner Pexels answers 403 and Unsplash answers 401, to a client
that names itself honestly as `EuropeDoor licence check`. The sandbox this
repository is developed in is refused as well, by its own egress proxy, which
is why the gate was built as a gate in the first place.

**The fix is not a browser user-agent.** Sending a Chrome string would get the
page and would misrepresent who made the request, on the one errand here whose
whole purpose is not misrepresenting anything — the gate exists so a claim
about somebody else's terms is backed by the page as served to *us*. A page
obtained by pretending to be a browser is evidence about a request we did not
make. `Accept` and `Accept-Language` are sent because they state truthfully
what this client can read; nothing else is.

So the remaining route is a person:

1. Open each URL in `terms_urls` for that provider in a normal browser.
2. Save the page as text with `python3 scripts/images/save_terms.py`, which
   writes it into `docs/data-licenses/provider-terms/` named
   `<provider>.<slugified-url>.<YYYY-MM-DD>.txt` with the URL, the date and
   the SHA-256 on the first three lines — and records that a person saved it
   from a browser, because a hand-saved page and a fetched one are not the
   same artefact and the difference should not be silent.
3. Fill in `value`, `quote` and `source` for each of `self_host`,
   `attribution` and `download_ping` in
   `docs/data-licenses/photo-providers.json`.
4. `python3 tools/checks.py`. Every quote is matched against the page it
   cites, so a sentence typed from memory fails the build.

A hand-saved page works exactly like a fetched one, because the check reads
the archive rather than the fetcher.

## What the terms actually said, read on 2026-09-10

All five pages were opened in a browser and archived under
`docs/data-licenses/provider-terms/`. Both providers refuse an automated
request, so a person read them; the archives say so in their own headers.

**Pexels is usable and the credit is not what the licence page implies.** The
licence page says attribution is not required. The **API documentation** says
something else for anyone fetching through the API, which is how this pipeline
fetches:

> Whenever you are doing an API request make sure to show a prominent link to
> Pexels. […] Always credit our photographers when possible (e.g. "Photo by
> John Doe on Pexels" with a link to the photo page on Pexels).

Two documents, both true, and the narrower one binds. `picture()` renders
`Photo by <photographer> on Pexels` with the name linked to the photo's page
and "Pexels" linked to pexels.com — derived from the register row, not from a
table of providers, so a second provider needs no second renderer. It prints
no download ping because the guidelines enumerate the obligations and none is
an event, which is recorded as the `basis` for that negative.

**Unsplash: the LICENCE permits use and the API ROUTE is refused.** The first
version of this said Unsplash was unusable, full stop. That was wrong, and it
was corrected by being told so. The licence grants the thing outright:

> Unsplash grants you an irrevocable, nonexclusive, worldwide copyright license
> to download, copy, modify, distribute, perform, and use images from Unsplash
> for free, including for commercial purposes, without permission from or
> attributing the photographer or Unsplash.

It attaches no hotlinking condition and no attribution condition. Its two
exclusions are selling unaltered images and *compiling images from Unsplash to
replicate a similar or competing service* — this is a European travel atlas
illustrating the places it writes about, and is neither.

What requires hotlinking is the **API**:

> All API uses must use the hotlinked image URLs returned by the API under the
> `photo.urls` properties.

`scripts/images/acquire.py` is an API client, so that route is refused: taking it
would mean embedding Unsplash's CDN URLs, and this site sends
`img-src 'self' data:` with a check enforcing it, so it would open the
Content-Security-Policy on all 1,033 pages to a host we do not control. That is
an owner decision about the whole site's security posture. The API route also
carries the download event on `photo.links.download_location` and attribution
naming both photographer and Unsplash; both are recorded against their quotes
so that if the policy question is ever answered, what the code owes is already
written down.

**So an Unsplash photograph enters by hand, not by pipeline.** Download it from
the website under the licence, run it through the width ladder, and add a
register row. No API call is made, no `download_location` exists to call, and
the credit this site prints anyway — no image enters without a photographer, a
source and a licence — comes out as
`Photo by <name> on Unsplash`, with the name linked to the photo page. That is
character for character the example the licence page itself gives.

**Two Unsplash documents are recorded as unread**, in the gate's `unread` field:
`unsplash.com/terms` and `unsplash.com/api-terms`. Nothing here relies on
either — the licence is the document that grants image rights, and the API
terms govern a route that is refused — but an unread governing document is a
gap, and a gap that is written down is one somebody can close.

**THE REFUSED THING IS A ROUTE, NOT A PROVIDER**, and collapsing the two is the
mistake this section records. It cost a correct provider a wrong refusal, and
the second version of the gate answers per route: `self_host` is a reading of
the LICENCE, `api_route` is a reading of the API guidelines, and
`acquire.py` enforces the second because it is the thing that takes that
route.

**Answered is not the same as permitted**, and the gate had no way to say that
either: its first version failed the build on any `self_host` that was not
true, which turns "we read the terms and they forbid this" into a red CI run
forever. `usable` is that distinction.

## Until then: the plates

Every surface without a photograph gets a generated plate — a small landscape
built from the SHA-256 of the thing's own slug, with the motif taken from
what the place actually is. See `docs/brand.md`.

The plate is the honest empty state, **not the policy**. The policy used to
be "no photographs at all", enforced by refusing every `<img>`, and that was
the right rule while there was no pipeline: it made the licensing question
impossible to get wrong. It is the wrong rule now, because it bans the
correct behaviour along with the incorrect one. The replacement is stricter
in the way that matters and permissive in the way that does not.

## Social cards

`og:image` is a separate problem from photography and it is solved. 718 cards
at 1200×630, one per entity, rendered by `tools/lib/raster.py` — a scanline
polygon filler and a PNG encoder written on `zlib` and `struct`.

Written rather than installed: the alternative is Pillow plus a headless SVG
renderer, two large dependencies (one of them a browser) added to a project
whose dependency list is empty, in order to draw gradients, circles and
filled polygons.

They render from `render.plate_shapes()` — the same geometry the SVG on the
page comes from, never a second drawing. That matters more here than
anywhere else on the site: a social card is the one image its own authors
never look at, because it is rendered inside somebody else's product days
later. A check asserts both renderers still come from that one function.

Content-addressed and cached in `assets/og/`, keyed by exactly the inputs
that determine the picture. First build 24 s; every build after that, 2 s.
Anything no page asks for is pruned, so a change to the drawing cannot leave
the cache full of orphans nobody can account for.

## The acquisition problem, stated plainly

The Bible asks for three categories, and the third is the one that matters:

| category | what | how hard |
|---|---|---|
| **Iconic Europe** | Eiffel Tower, the Alps, Venice, Santorini | easy — free-licence stock is saturated with these |
| **Human Europe** | markets, families, pilgrims, artists, chefs, craftspeople | harder, and needs release paperwork for recognisable faces |
| **Hidden Europe** | small villages, remote landscapes, local festivals, mountain roads, quiet coastlines | **hard, and it is the whole product** |

319 destinations need a hero each. Free-licence stock will cover the iconic
tier and will not cover Albarracín, Theth or Bitola — which are precisely the
places this site exists to show. Stock for those either does not exist or is
the same four images everyone else is using.

That points at commissioning and at contributor licensing, both of which need
the entity that does not exist yet. It is a real constraint and it is not
solved by trying harder at stock.

**No photograph is downloadable from this environment in any case:** the
sandbox proxy does not reach an image provider, and it should not — acquiring
images is a decision with a licence attached, not a build step.
