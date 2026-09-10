# The Stay layer

Accommodation as a first-class part of the atlas, and never a hotel widget.

**Status: one exemplar built and rendered — Chamonix. The referral is designed
and not activated.** The other 318 destinations still carry the honest refusal
they always carried. Propagation waits on the grammar being judged, which is
what an exemplar is for.

## Where it sits

    Europe → Country → Region → Destination → Places / Experiences / Journeys → Stay

Stay is the last rung, and on a destination page it is the last thing before
the reader is handed onward:

    Why go → Places to see → Things to do → Where to stay → Nearest onward stops

That order is not decoration and it is not new: `tools/ux-audit.py` has
asserted the ascending document position of `why-visit`, `places`,
`things-to-do`, `stay` and `onward` since the destination family was given its
own art direction. Accommodation appears where a reader who has decided to
come would look for it, after the reasons and before the exit.

## What this atlas actually knows about staying somewhere

This is the whole design question, and it was asked before "which provider".

EuropeDoor holds **no rooms, no prices, no availability and no ratings**, and
has refused to hold them since the schema was written. So a card grid of
properties would be somebody else's inventory pasted under our masthead, and
a reader would correctly read it as an advertisement inserted into an article.

What it holds instead, and what no booking site has, is a judgement about the
**place**:

| | source | kind |
|---|---|---|
| where a bed can sensibly be | authored per destination | classification — the job |
| how the ground constrains that | `data/geo/terrain-lod1.json` | measurement — derived, never authored |
| when the beds go | the country's own peak and shoulder months | derived |
| how long the place is worth | `nights` on the destination | authored, and already printed above |

Chamonix reads a **1,798 m spread and a 2,752 m crest within 40 km**, and that
measurement is *why* the town is the only answer: the valley floor is the only
ground flat enough to put a bed on and still be at the bottom of the cable
car. Paris reads 102 and 150 and that paragraph would have nothing to say, so
it is omitted there rather than filled with a sentence about nothing.

## The heading is derived from what the place is

"Hotels in Chamonix" is generic listing language and also the wrong promise:
what is on offer is a **base**, and a base means something different in a
valley, on an island and in a capital.

| the place | the heading |
|---|---|
| relief measured under it | Sleep below the peaks |
| island | Stay on the island |
| village / valley | Stay in the village / Stay in the valley |
| capital / city | Stay in the city |
| town | Make a base here |
| anything else | Where to stay |

Derived rather than authored-only, because 319 authored headings is 319
chances to write "Hotels", and a default that comes from the data cannot drift
from the place. A covered destination may override it, and the validator
refuses a heading containing the word *hotel*.

**An audit assertion had to be rewritten for this**, and it is worth recording
why. `section-audit.py` required the literal string `Accommodation &
restaurants` on a destination page — true of all 319 only while none of them
had a Stay layer, so the day the grammar propagated it would have gone red for
a page that had got *better*. That is the seventh assertion in this repository
to pin a shape rather than a promise. It now asserts both states: an uncovered
destination says it lists neither and links to where listings are explained; a
covered one offers a base, names the provider that holds the rooms, states
what we hold, and carries a disclosure.

## The provider abstraction

A provider is a **link mechanism and a credential**, and deliberately nothing
else. `data/stay.json`:

    search_url + place_param + fixed_params  ->  a deep link to their search
    partner_param + partner_id               ->  the referral, when we have one
    inventory_api                            ->  what they can and cannot supply
    programme + programme_url + gate         ->  whose terms this row sits under

Adding a provider is an edit to that file and touches no page code. Three are
declared and one is enabled:

| provider | programme | inventory | enabled |
|---|---|---|---|
| Booking.com | Affiliate Partner Programme | Demand API, **managed partners only** — so not here | yes |
| Expedia | Travel Creator Program | **none** — tracked links, no general API | no |
| Agoda | Online Affiliate / MSE | Search API, the likeliest future real source | no |

`inventory_api` is a **required** field of at least forty characters, and that
is the point: the standing temptation is to assume every large provider has an
API and design a card that silently has nothing to fill it. Expedia's row says
NONE in capitals for that reason.

Two providers, not five, and the third recorded rather than built. A fourth
enabled provider costs a reader a decision they did not ask for.

## Two honest states, and a check that keeps them apart

| | today | with a credential |
|---|---|---|
| link | plain deep link | `aid` appended |
| `rel` | `nofollow noopener` | `sponsored nofollow noopener` |
| disclosure | "not a partner and earns nothing" | "may earn a commission" |

The state is read off the credential, never typed into a page. `checks.py`
asserts `sponsored` appears **if and only if** a partner id exists — both
directions, both proved red.

**A disclosure that only appears when we are paid is an advertisement with a
conscience.** Both states carry one, because what a reader wants to know is
what our interest in the link is, and "we earn nothing from this" answers that
as squarely as the other sentence.

## The card, and why there is not one yet

The brief for this layer asked for a card: a photograph, a property name, a
9.1, "From €184", "View availability". Every one of the five is refused here,
each refusal enforced at least twice:

| | why it cannot be drawn |
|---|---|
| photograph | no licensed photograph exists; a provider's marketing image has no photographer, source or licence; `safety.img_tags` is an exact zero |
| rating | `★` may not appear on any page; we hold no reviews for anywhere in Europe |
| price | `price` is refused on every record; "a price we cannot keep current is worse than no price" |
| availability | we hold no inventory |
| property name | the same — nothing supplies one |

**None of that is because a card is a bad idea.** It is because under a
link-only affiliate mechanism there is no honest source for any of it.
`stay.inventory()` is the seam, it returns nothing, and a page that gets
nothing draws the editorial reading rather than an empty frame — because
present-but-empty says "we have this" and then does not, which is the pattern
`checks.py` already refuses in JSON-LD.

The trigger is named per provider in the registry. When one opens, that
function is the only thing that learns about it, and what it may return is a
property name, a canonical provider URL carrying our attribution, and whatever
of price and rating **that provider publishes, with its own figure attached** —
never a number this atlas computed and never one it stored.

## No ranking, and no second map

**A ranking module was asked for and is refused.** `rank`, `boost`, `featured`
and `sponsored` are refused on every editorial record, refused again by key in
this registry, refused again at the API level, and `/for-businesses` publishes
the sentence "there is nothing in its index that could carry a boost". A
module that ranked accommodation would be the mechanism those published
sentences claim does not exist. Ordering, where it is ever needed, is the
registry's declared order — data, visible, and not a score.

**Accommodation as geography is the right long idea and needs coordinates we
do not have.** A destination page already draws one arch, and a second four
screens down would be the signature as wallpaper — the same argument the facet
pages and the events band already lost. And a pin has no page here to link to,
which makes it a dot the page cannot name. It arrives, if it arrives, with an
inventory API that supplies real coordinates; inventing them would be the
region-hull failure with beds.

## What it was tested at

Rendered and looked at, not only counted: **1280 and 390**, and in **both
colour-scheme preferences**. The no-image state is not a fallback here, it is
the shipped state, so there is nothing to degrade to. The section loads no
JavaScript and no third-party subresource, so there is no slow-network
behaviour to design — the outbound link is a navigation the reader chooses.

## The visual grammar, for whoever propagates it

Rules and space, and four things deliberately absent: **no border box, no
radius, no shadow, no fill.** Those four are what say "separate object, placed
here by a system", which is exactly the reading to avoid. A heavy rule over
each reading groups without enclosing, and the action sits below a hairline
rather than inside a panel, because a panel around a commercial link is a
banner.

The action and the boundary sit **side by side**. The first version stacked the
button, the who-holds-what and the disclosure in the left half of a 1,168-pixel
band with six hundred pixels of white beside them — the same fault as the
280-pixel card alone in its row on the old stories index, and found the same
way, by rendering the page instead of reading it.
