# The Europe Experience Score

Six numbers on every city and country page. The whole formula is published at
`/method` and implemented in `tools/lib/score.py`. This file is the reasoning
behind it.

## The formula

Five structural dimensions — nature, history, food, culture, adventure — are
computed from editorial interest tags:

```
score = 34                                   (base)
      + Σ weight(tag) for each tag on the city or its region
      + 4 per matching experience kind, up to 3
      clamped to [12, 97]
```

The weight tables are in `score.py` and rendered verbatim onto `/method`, so
a change to the code is a change to the published methodology on the next
build. There is no second copy to forget.

The sixth dimension, **value**, is the only one anchored outside our own
judgement:

```
value = 110 − (midpoint of the country's daily cost band − 40) × 0.382
```

The daily band is printed on every country page, so anyone who thinks the
value score is wrong can argue with the number it came from.

A country scores as the mean of its cities. A country cannot be stronger on a
dimension than the places you would actually visit.

## Four constraints, and why each exists

**Recomputed, never stored.** No score appears in `data/`. A stored score and
its explanation drift apart the first time somebody edits one and not the
other. `checks.py` fails if a `scores` key appears in a country file.

**Ceiling 97, floor 12.** Nothing is perfect and nothing is worthless. A 100
invites the question "compared to what", and a 0 is a claim we cannot
support about any real place.

**Descriptive, not evaluative.** A 94 for Adventure means the place is
*about* adventure, not that it does adventure better than a 71. This
sentence is printed under every score block, because it is the interpretation
everybody gets wrong.

**Not for sale, structurally.** There is no field in the schema that could
carry a paid adjustment and no code path that reads one. That is a stronger
promise than a policy, because a policy can be changed quietly.

## What the scores are not

They are not measurements. They are derived from our own tagging by a
published rule, which makes them auditable and reproducible, not objective.
If we tag a city wrongly, its score is wrong, and the fix is to fix the tag.
`/sources` says how to tell us.

## The alternative that was rejected

The obvious thing to build is a rating: stars, or a 0–100 "how good is this
place". It would be more clickable and it would be indefensible — every such
number in travel is either a popularity proxy or an opinion wearing a
statistic's clothes, and both corrode trust the first time a reader disagrees
with one about somewhere they know.

A structural score survives disagreement. Somebody who loves Bergen and
thinks its food score is low can look at the tags, see that we did not tag it
`food`, and tell us we are wrong about a specific, checkable thing.
