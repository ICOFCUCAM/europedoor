# The image philosophy, per family

**Status: this repository holds ZERO licensed photographs.** `data/images.json`
is the register and its `images` list is empty. Everything below is a
specification for what a photograph would have to *do* on each family, not a
description of what is there. Nothing may be committed against it from a
provider's marketing page or from memory — the sandbox proxy answers 403 to
CONNECT for general hosts, so acquisition is a human step. `checks.py` refuses
an `<img>` with no register row, and `safety.img_tags` catches it again.

This document exists because a shared template is not a shared experience and
a shared *image policy* would be worse. "Photographs everywhere" and "no
photographs at all" are both one decision applied to twelve different jobs.
The question is per family: **what is this page's primary visual language, and
what would a photograph add that the built system cannot?**

## The rule that decides it

> A photograph is licensed for a family when the existing visual system has
> been **demonstrably exhausted for that particular purpose** — measured, not
> asserted.

There is exactly one family where that has been done. `docs/hero-brief.md`
records the measurement for the homepage: the plate system rendered at
1200×500 is flat and monochrome with a dead slab across the bottom third, and
that measurement is the whole justification for the seven-question licence
gate, all seven of which are still unanswered.

Every other row below is a *claim* that a photograph would help. None of them
is measured yet, and none should be bought until it is.

## The twelve

| family | primary visual language, as built | what a photograph would do | slot |
|---|---|---|---|
| **Home** | the aperture at screen scale, Europe through it | the one measured case: a hero the plate system cannot draw | wired, empty |
| **Country** | the country's outline as a portrait, filled, in a door whose proportion is the country's | **not** a hero. A country photograph is a cliché generator — one frame standing for 84,000 km² is the Eiffel Tower meaning France. If licensed it sits *below* the portrait as character, because the shape is true of the whole country and a photograph is true of one square kilometre of it | none |
| **Region** | the region as its own destinations, framed on their extent, named at their middle | landscape and environment: the one thing a region genuinely shares. The strongest unwired case after the homepage | none |
| **Destination** | the local view — a wide shallow window, the place at the centre, land painted, neighbours quiet | sense of place: streetscape or the one landmark a reader would recognise on arrival. Already branches on the register | wired, empty |
| **Place** | the same window at the place's own coordinate | the specific location. Architectural or landscape, and the least ambiguous licence to buy because the subject is one object | wired, empty |
| **Experience** | *see the fourth exemplar* | activity and emotion — the only family whose subject is a **verb**. A map cannot draw a verb, which is why this is the family where the visual system is closest to genuinely exhausted | none |
| **Journey** | the spine drawn to scale: each leg's real distance as a bar, on one scale within the journey; the route on the continent with the last stop hollow | a sequence, one frame per stop, which is the only family where a *set* of photographs is the unit rather than one. Would reuse the destination register rows rather than needing its own | none |
| **Story** | the destinations of the story itself, on the real coastline, through the arch | magazine and editorial: the family where photography is native and where a generated illustration was actively wrong. **A story's picture may never be drawn from a hash** — that rule was written after the piece about the last unlogged primeval forest opened on tower blocks | wired, empty |
| **Event / month** | the year band: what is on above the line, how many countries are in their quieter shoulder below it | atmosphere. The **weakest** case in the table: an event photograph dates within a season, carries the heaviest rights, and the family's subject is *time*, which the band already draws | none, and not soon |
| **Search** | INTELLIGENCE: graphite, the instrument, an input and its results | nothing. A photograph on a search page is decoration on a tool | never |
| **Plan** | INTELLIGENCE: the planner, its controls beside what they act on | nothing | never |
| **My Europe** | INTELLIGENCE: the reader's own collection, client state, no server | nothing of ours. Whatever appears here is the destination and place imagery the reader saved | inherits |

## Three things this table is not

**It is not permission to buy.** Six rows say "would". One row is measured.
The gate in `docs/hero-brief.md` applies to each of them separately, and a
licence answered for the homepage answers nothing for the regions.

**It is not a reason to degrade a page.** Every family above must be complete
with no photograph at all — that is what the four wired slots already do, and
it is why `picture()` returns an empty string rather than a placeholder. A
page that looks unfinished without an image is a page designed against a
register that holds nothing.

**It is not a licence to use a plate instead.** A generated plate is an
illustration drawn from the hash of a slug. It is right on a card, where it
says *a thing exists here*, and wrong wherever it would be taken for a
record of somewhere — which is why the story rule exists and why
`checks.py` refuses `og=(seed, None, …)` anywhere.
