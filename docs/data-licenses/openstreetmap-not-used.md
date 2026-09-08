# OpenStreetMap — deliberately not used

Not an oversight, and not a judgement about the data, which is the best in the
world for what it covers. It is a licensing decision, taken in advance so that
nobody has to unpick it later.

**licence** ODbL 1.0. Free, and share-alike.

**why it is out of the core**
ODbL's share-alike condition attaches to a *derived database*. EuropeDoor's
knowledge graph — countries, regions, destinations, places, scores, the
verification records — is the product. Merging ODbL geometry into it risks
making the graph itself a derived database, and the obligation that follows is
to publish it under ODbL. That may one day be a fine trade. It is not a trade
to make by accident, in a commit that was really about drawing a coastline.

**the second reason**
`tile.openstreetmap.org` is a volunteer-funded service with a usage policy
that a commercial platform should not be leaning on. Pointing production at it
would be free in the sense that matters least.

**when it comes back**
Roads, trails, street-level geography, detailed POIs and routing. OSM is the
only realistic source for all five, and at that point the question is worth
answering properly. The condition for importing it, set now while nothing
depends on the answer:

> OSM-derived geometry lives in its own dataset, in its own directory, with
> its own licence record, and is **joined to** the knowledge graph at render
> time rather than merged into it. If that separation cannot be maintained for
> a given feature, the feature waits.

Do not casually merge ODbL geometry into `data/`.
