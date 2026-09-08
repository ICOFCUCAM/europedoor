# Boundaries

> §14 of the map brief: *treat borders as geographic data, not as editorial
> statements; create a documented policy for disputed or complex boundaries;
> do not hard-code political assumptions into application logic; record the
> dataset and version used; allow the data policy to be changed without
> rebuilding the application.*

This is that policy.

## The position

**EuropeDoor takes no position on any frontier.** It publishes a named,
versioned, third-party cartographic dataset and says which one it is, on the
map and at `/method#map`. Where that dataset draws a line is where the line is
drawn here, and the page tells the reader that is what happened.

That is not neutrality by accident — every boundary dataset in existence takes
positions, and choosing one chooses its positions. It is neutrality by
disclosure: the reader is told which cartographer they are looking at and can
disagree with that cartographer rather than with us.

## What is recorded

| | |
|---|---|
| dataset | Natural Earth `admin_0_countries`, 1:110m and 1:50m |
| version | Natural Earth v5.1.2 |
| licence | public domain |
| bytes held | SHA-256 recorded in `docs/data-licenses/sources.json`, checked by `fetch.py --verify` |
| processing | clipped to a European bounding box, Douglas-Peucker simplified, quantised to 3 decimal places |

Every page that shows the geometry names the dataset in its caption. The
processing is named too, because a simplified border is a *different* border:
at 1:50 million with a 0.012° tolerance, a line on this map can sit a couple
of kilometres from where the source puts it, and the source is itself a
cartographic generalisation of the ground.

**So: nothing on this map is evidence about a frontier**, and `/method#map`
says so in those words rather than in a disclaimer nobody reads.

## Not in application logic

There is no code path anywhere in this repository that branches on whether a
territory is disputed, recognised, or claimed. There is no `disputed` flag, no
recognition list, no override table of "correct" borders. The three things
that come close, and what they actually are:

- **`ISO_FIX` in `scripts/map/process.py`** — a lookup from Natural Earth's
  three-letter code to our own two-letter country code, for the entities where
  `ISO_A2` is `-99`. Kosovo is in it, because Kosovo has no assigned ISO 3166-1
  alpha-2 code and `XK` is the user-assigned code in common use. This is an
  identifier join, not a recognition claim: the row exists because the atlas
  has a Kosovo page, and the atlas has a Kosovo page because there is
  somewhere to travel to.
- **`CONTEXT`** — countries with no EuropeDoor page that are drawn anyway, so
  the Mediterranean has a far shore. They are drawn flat, are not clickable
  and carry no link. Northern Cyprus and Palestine are in that list on exactly
  the same terms as Tunisia: Natural Earth has a polygon, the polygon falls in
  the window, so it is drawn as land.
- **`data/countries/*.json` `advisory`** — a travel-safety field, applied
  today to Ukraine, Russia and Belarus. It is about whether a person should
  travel there now. It says nothing about borders and is not used by any map
  code.

## Changing the policy without rebuilding the application

The dataset is a row in `docs/data-licenses/sources.json` and two lines in
`LODS` in `scripts/map/process.py`. Swapping Natural Earth for another
public-domain or licensed source is:

1. write the new licence record in `docs/data-licenses/`
2. add or replace the row in `sources.json`
3. `python3 scripts/map/fetch.py`
4. `python3 scripts/map/process.py`
5. `python3 tools/build.py` and commit

No page builder, no stylesheet and no JavaScript changes, because none of them
knows where the geometry came from — they know only that
`data/geo/*.json` has countries with rings, a bbox and a slug. That is the
whole point of the format being renderer- and source-neutral.

## The one obligation waiting to be accepted

Eurostat's NUTS dataset carries a required designation footnote — a paragraph
about not implying any position on the legal status of any territory,
including a specific Kosovo clause — that must be reproduced wherever its
boundaries appear. That is an editorial obligation on our pages, not a line in
a licence file, and it is one of the reasons NUTS is not imported. The full
text is in `docs/data-licenses/eurostat-gisco-nuts.md`. Importing that dataset
means accepting that footnote onto the pages, and that is the owner's decision
rather than a build step.

## What would change this policy

One thing: publishing something that reads as a *claim* rather than a
*drawing*. A map that highlights a disputed territory, a page that asserts a
frontier in prose, a search filter that resolves a place to one country rather
than another. None of those exists today. If one is proposed, this document is
where the position gets written down first — before the feature, not after the
complaint.
