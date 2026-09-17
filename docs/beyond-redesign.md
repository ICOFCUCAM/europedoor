# /beyond-the-obvious — the European Counter-Atlas

The owner's brief: BEYOND THE OBVIOUS → RESPONSIBLE TRAVEL → 130 PLACES →
NINE REGIONS → SIX STRAIGHT SWAPS → THE RULE → OPEN THE DOOR, and one
instruction that decides the whole thing — *the page should feel like
EuropeDoor is revealing the other geographic layer of Europe, not presenting a
list of "secret destinations."*

**Every figure the brief quotes is right.** 130 quiet destinations, 44
countries, and all nine macro-region counts — 19, 7, 6, 15, 15, 41, 18, 2, 7 —
checked against the build. Second brief running with no arithmetic to correct,
which means the work is in what the numbers do not say rather than in fixing
them.

## Part 1 — the source audit

| | |
|---|---|
| quiet destinations | **130** of 319, in **44** countries |
| macro regions they fall in | 9 |
| photographs in the register for them | **27** of the 130 |
| photographs the page drew | **8** |
| bytes | 222,306 — the heaviest page on the site |
| `<h2>` bands | 4 |

The page was a `pagehead index`, the quiet map, a strip of nine, 130 rows
grouped by macro region, six swaps, and a `.note`.

**AND THE PAGE'S OWN POSITION WAS THE SMALLEST THING ON IT.** *No page on this
site tells you a place is undiscovered. Publishing that sentence is what ends
it.* That is this product's sharpest editorial line and it sat at the very
bottom, under 130 rows and six swaps, at caption size, inside a `.note`. It is
the /stories fault exactly — the reason a family looks the way it does,
printed smaller than everything it explains.

## Part 2 — the count argues the wrong way

The brief lists the nine counts, and the nine counts alone say **go to the
Mediterranean**: it holds 41 of the 130, three times the next corner. That is
the opposite of what this page argues, and it is an artefact — the
Mediterranean holds 41 because it holds **94 destinations**.

As a share of each corner's own set the order changes:

| corner | quiet | all | share |
|---|---:|---:|---:|
| The Baltic States | 7 | 12 | **58%** |
| The Adriatic & Balkans | 18 | 40 | 45% |
| The Mediterranean | 41 | 94 | 44% |
| The Caucasus & the Bosphorus | 7 | 16 | 44% |
| The Nordics | 19 | 46 | 41% |
| Western Europe | 15 | 42 | 36% |
| Alpine & Central Europe | 15 | 43 | 35% |
| Britain & Ireland | 6 | 18 | 33% |
| Eastern Europe | 2 | 8 | **25%** |
| **the Atlas** | **130** | **319** | **41%** |

**The corner with the most quiet places is not the quietest corner.** That is
/events' *the busiest month is the least characteristic*, one family over.
Both figures are on the group head now — the count because it is what a reader
came for, the share because it is what the count means — and both are derived
on every build.

## Part 3 — the rule had three promises and one of them is not kept

*A refusal nobody can check is a slogan* — /plan's own finding — and this
band's three promises had never been checked. Measured against the built site:

| promise | state |
|---|---|
| when to come | **kept** — "When to come" is a section heading on all 319 destination pages |
| how to arrive without a car | **kept** — "Getting there" and "Getting near" are sections on all of them |
| who locally is worth your money | **NOT BUILT** |

An experience record carries a slug, a name, a kind, a band and a summary —
**no operator, no business, nobody's name.** The Stay layer publishes that we
list neither hotels nor restaurants and refuses a ranking outright, and
`/for-businesses` publishes that there is nothing in this index that could
carry a boost. So the third clause has been promising something this site does
not do anywhere, on the page whose subject is holding ourselves to a rule.

It is **stated as unbuilt with what it would take**, rather than quietly
deleted: the /my-europe futures grammar and /plan's six refusals, and the
standing rule that recording a mistake beats removing the evidence of it.

## Part 4 — the seven plates

| | class | what it is |
|---|---|---|
| 01 | `btopen gal` | the head, the extent, and the counter-atlas: 130 dots at full size |
| 02 | `hidden pine` | *The alternative is not hidden gems* — the refusal, before the list |
| 03 | `corners gal` | one from each corner: a mosaic of three, a strip of the rest |
| 04 | `quietset paper` | 130 places, nine corners — count and share on every group head |
| 05 | `swaps gal` | six straight swaps, as pairs rather than as metadata |
| 06 | `rule pine` | the rule, and the promise that is not kept |
| 07 | `leave gal` | *Leave the obvious behind* |

**The refusal and the rule are two bands because they are two statements.**
02 says what we will not write and why; 06 says what we write instead and
whether we actually do. Collapsing them would be one band saying a thing
twice, which is the fault /events records about its own two halves — and the
brief separates them for the same reason.

**No photograph in the opening, and that is a refusal rather than a gap.** The
register declares no hero for this family, and the one that could be acquired
for it is by definition a generic European scene — the exact thing a page
refusing the phrase "hidden gems" cannot open on. What this page has and no
stock library has is the distribution: 130 dots a reader can see are nowhere
near the eleven places.

## Part 5 — the defects only rendering found

**`.rowmeta` IS `white-space: nowrap`, AND PROSE IN IT RAN 831 PIXELS OFF THE
PAGE.** The rule band's third row put *needs an operator field nothing here
holds, and a way to choose that is not a ranking* in the metadata column — the
slot that carries a country and a region everywhere else on this site — so the
document scrolled sideways by **223px at 1280 and 263 at 834**. That is `19
DAYS · 5 COUNTRIES · MODERATE` exactly, and the phone-overflow check could not
see it because it is a check about phones: at 390 and 320 the row stacks and
there is no overflow at all. The explanation belongs in the row's subline,
where prose goes; the meta says *Kept* or *Not built*.

**A SWAP IS A PAIR AND THE OLD ROW TYPESET HALF OF IT AS METADATA.** The
alternative went in `.rowmeta` too — so *Naxos or Sifnos, any evening*, the
one thing the band exists to say, was set in the slot that carries a region
name. Both halves are headings now, in their own tracks, so the eye reads
across rather than down.

## Part 6 — and a finding that was mine, three commits old

`.sheet-pine` **has ended `display: block` since the commit that introduced
it**, and so do `.sheet-gal` and `.sheet-bleed`; only `.sheet-paper` and
`.sheet-quiet` do not. The /my-europe commit recorded the opposite — *`.sheet-
pine` sets no `display`, so both pine bands landed in a 40% track* — and
called it the third occurrence in three commits. /stories' feature band at
205 × 154 and /events' year chart at 619 were both **paper**, which is what
made the generalisation look true: a correct diagnosis of two cases, widened
one room too far, then repeated into a commit message and into `CLAUDE.md` as
evidence.

Seven redundant declarations on /my-europe, five on /interests and six here
restated what their room already computes. All eighteen are gone, and twelve
screenshots across six pages at 1280 and 390 are **byte-identical** before and
after — because nothing here is deleted on an argument alone.
`grep -n '^\.sheet-pine' -A 6` is the whole check and it takes a second.

## Part 7 — what is NOT here

| asked for | why not |
|---|---|
| a separate nine-region index above the 130 | the rows are already grouped by macro region with the count on the head, so a ledger above would print the same nine counts twice — the fault 220 place pages had |
| a photographic hero | see Part 4; and the corners band spends what the register actually holds |
| all 27 photographed quiet places as a band | 27 of 130 is a fact about the library, not about Europe, and presenting it as a selection is what this page refuses. The nine picks are editorial — one per corner — and the corner with no photograph shows its slot, which names the acquisition |
| a derived swap | a great-circle distance and a quiet flag cannot say that Kvarner is what somebody wanted from Dubrovnik. The six are authored editorial judgements and are the work |
