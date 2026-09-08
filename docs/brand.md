# EuropeDoor — the brand, as built

The Brand Bible V1, applied. This file records what actually shipped, what
was changed on the way in and why, and the two things in the Bible that this
build does not do.

The name and the trademark position live in `docs/brand-lock.md`. Read that
first — the mark is **not cleared**, and the working-brand rule it sets is
the reason nothing here is announced, filed or printed.

## The core

| | |
|---|---|
| Name | **EuropeDoor** — one word, always. Never `Europe Door`; a check fails the build on the space |
| Domain | europedoor.com |
| Primary tagline | **Open the door to Europe.** |
| Category | European discovery and intelligent journey platform |
| Promise | Discover Europe. Understand it. Experience it. |
| Primary CTA | **Plan my journey** |
| Secondary CTA | Explore Europe |
| The AI | **EuropeDoor Guide** |
| Saved area | My Europe |
| Discovery concept | Beyond the Door |

Secondary taglines — *Discover what lies beyond · Your journey starts here ·
Europe, opened · One door. A continent of possibilities. · Find your Europe ·
See Europe differently* — are campaign lines. None of them appears in the
shell, because a site with six taglines has none.

## The four doors

Discover → Understand → Experience → Journey.

It is on the homepage as four linked cards, and it is a **sequence rather
than a menu**: each door is only worth anything once the one before it has
happened. That is the whole argument against Search → Book, and it is why the
cards are ordered and numbered rather than presented as a grid of equals.

The five pillars that were on the homepage before this (Atlas, Planner,
Journeys, Experiences, Fund) were a list of *our components*. The four doors
are a description of *what a reader does*. That is a better homepage.

## Colour

Not EU blue-and-gold. Looking like an institution we are not is worse than
looking like nothing.

| role | token | value | used for |
|---|---|---|---|
| Primary | `--atlantic` | `#14483c` | the mark, the primary action, focus rings, links |
| Primary, lifted | `--atlantic-3` | `#1d6250` | the door leaf in the mark, second tones |
| Accent | `--terracotta` | `#a4491f` | kickers, hover rules, the onward arrow |
| Ground | `--paper` | `#f7f6f3` | a cool limestone, not a warm sand |
| Type | `--ink` | `#14181c` | near-black charcoal |
| Heritage | `--brass` | `#8a6d34` | reserved. **Never a control** — a gold button reads as a premium upsell, and there is nothing to sell |

Dark mode is not an inversion: the ground becomes the deep end of the
Atlantic green so the brand survives the switch, and terracotta lifts to
`#e08a5c` because `#a4491f` is unreadable on a dark ground.

Every value is measured against WCAG 2.2 AA by `tools/browser-checks.js` in
both schemes, on all three paper tones, on every build.

## The mark

Concept B from the Bible: **two vertical forms, and the negative space
between them is the symbol.** The outer form is the doorway; the inner is the
leaf standing ajar, hinged left. The sliver of ground on the right is what
makes it a door rather than an arch.

Drawn once, in `render.MARK`, inline so it takes its colour from the palette
and costs no request. It holds at 18px and on a dark ground.

Rejected on the way, and worth recording so nobody re-proposes them:

- **a literal door with a knob** — what the site shipped before this; the
  Bible rules it out and it was right to
- **a wedge of light out of a solid arch** — illegible under about 24px
- **two jambs with an open apex** — reads as two curved strokes, or an ∩,
  not as an opening
- **frame plus a separate swung leaf** — two blobs at favicon size

## The illustrations

There are no photographs yet. Every surface that wants one gets a generated
plate: a small landscape built from the SHA-256 of the thing's own slug, with
the motif taken from what the place actually is — peaks, coast, skyline,
tower, isles, forest or plain.

This replaced a gradient with seven random bars on it, which at hero size did
not read as an illustration but as a **broken image**. That is a real cost: a
reader who thinks a picture failed to load stops trusting the rest of the
page.

**The doorway is deliberately not in the plates.** Three attempts —
a stroked arch, a linearly-faded fill, a radially-faded fill — failed as a
scratch, a pane of glass, and a second sun competing with the one already in
the picture. A motif stamped onto 987 surfaces stops being a motif and
becomes a tic. The door lives in the mark, the favicon and the language.

## Voice

Say: discover, explore, wander, experience, understand, follow the road, find
something unexpected.

Never: *optimise your European tourism journey · AI-powered travel solution ·
next-generation travel ecosystem · hyper-personalised destination
optimisation.* Those sound like corporate software, and the whole product is
arranged around not being that.

The editorial rule, from the Bible's own example: write what a place *is*
before writing what it *has*. `Bergen is a tourist destination located in
western Norway` is a database row with a verb in it. The destination pages
already open with a line of the second kind, and 319 of them are written that
way — the summaries are the reason this product is worth reading.

## Two things in the Bible this build does not do

**Photography (§13).** The Bible asks for three categories — Iconic, Human,
Hidden — and calls photography one of the most important parts of the brand.
It is right, and the *architecture* for it now exists: a registry that
refuses an image without a photographer, a source and a licence; `<picture>`
with AVIF, WebP and JPEG; one eager hero per page and everything else lazy.
See `docs/images.md`. What does not exist is a single photograph, because
none has been licensed and this environment cannot reach a provider. The
plates are the honest empty state, and every one of them becomes a photograph
by adding a row to a file.

**Named webfonts (§12).** Playfair Display and Inter are the right pairing.
Loading them from a font CDN would hand every reader's IP address to a third
party on every page view and break `default-src 'none'`, which contradicts
`/privacy` — where the claim is that nothing is loaded from another origin
and here is how to check. The type *roles* are honoured with system stacks: a
serif for display, a sans for interface, one scale of eleven steps. Self-
hosting licensed faces is a change to two custom properties on the day
someone buys them.
