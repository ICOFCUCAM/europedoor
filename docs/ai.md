# AI

## What runs today

Everything in the pipeline except the model.

```
reader's sentence
   ↓  intent extraction     RULES, in the browser — parseAsk()
   ↓  read-back             what it understood, shown to the reader
   ↓  retrieval             /api/atlas.json, our own data only
   ↓  planning              deterministic scoring, haversine, costing
   ↓  refusal               a check, not a prompt — whyUnreliable()
   ↓  itinerary
```

`assets/js/planner.js` reads "three weeks by train through the alps in winter,
luxury" into days, month, spending style, transport mode, interests and a
seven-country geography, shows the reader exactly what it understood, and
returns a routed, costed, day-by-day itinerary. **No model is involved and
nothing leaves the browser.**

The consumer-facing name for the assistant is **EuropeDoor Guide**. Never
"our AI".

## The rules a model would have to obey

These exist now, in code, so that adding a model is a constrained change
rather than an open one:

**The model must never plan.** It reads the sentence and it writes prose. The
route, the distances and the costs come from the deterministic engine. A model
that plans is a model that invents a town.

**Narration is given rows, not the question.** It cannot answer from memory
because it is not asked one.

**Refusal is code, not a prompt.** `whyUnreliable()` declines under four
conditions: nothing fits, the stops fill under 60% of the days, half or more
of the stated interests are undelivered, or the cost exceeds a **stated**
budget by 80%. Each names the control that would fix it and offers the
rejected plan marked as rejected. A prompt saying "do not make things up" is a
request; a check is a guarantee.

That word *stated* is load-bearing. The first version refused a sentence
against a €2,500 default the reader never gave — refusing our own assumption
and telling the reader they asked for something impossible. A browser check
holds that line now.

**Volatile fields cannot leak** because there is no field to leak. `hours`,
`price`, `website` and `phone` are rejected by the validator, so no prompt can
produce an opening time from our data.

**The four labels.** Every claim on the site is Verified, Editorial, Computed
or Community, and the difference is visible on the page — see `/manifesto`. A
model's output is none of those four and must be labelled as what it is.

## What is not built

The model itself, and the five services that need one: narration, semantic
retrieval, conversational follow-up, summarisation and translation.
`docs/product-specification.md` §2.4 has the prompts.

That order is deliberate. The retrieval discipline, the refusal path and the
provenance labels had to exist *first*, because every one of them is
unenforceable once a model is already answering.
