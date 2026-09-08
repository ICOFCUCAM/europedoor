# Eurostat / GISCO NUTS regions — NOT IMPORTED

> **Status: blocked, awaiting the owner's acceptance of Eurostat's terms.**
> Nothing from this dataset is in `data/`, in `site/`, or in any published
> page. This file exists because §24 of the map brief says to stop on a
> licensing question and explain, rather than to import and find out later.

**dataset**
NUTS 2024 statistical regions, levels 1–3, as republished by
[Nuts2json](https://github.com/eurostat/Nuts2json) — Eurostat's own
simplified GeoJSON/TopoJSON distribution. This is Layer 4 in the map brief,
and it is the only layer of the seven that is blocked.

**source**
`https://raw.githubusercontent.com/eurostat/Nuts2json/master/pub/v2/2024/4326/20M/nutsrg_<level>.json`
Reachable and measured: level 1 is 180 KB, level 2 is 267 KB, level 3 is
574 KB of raw GeoJSON, which after our simplification would be roughly
90–125 KB for the whole continent. Size is not the problem.

**licence — two layers, and the second one is the problem**

1. The **Nuts2json software** is EUPL 1.2. Fine, and irrelevant: we would take
   the data, not the code.
2. The **NUTS dataset itself is copyrighted.** The repository's own README
   says so without hedging:

   > The Eurostat NUTS dataset is copyrighted. There are specific provisions
   > for the usage of this dataset which must be respected. **The usage of
   > these data is subject to their acceptance.**

   "Subject to their acceptance" is a person accepting terms, not a build
   script fetching a file.

**version / date**
Would be NUTS 2024, scale 1:20M, EPSG:4326. Not fetched.

**permitted use**
Believed to be free reuse including commercial, on the standard GISCO terms.
**Not verified.** `ec.europa.eu` is unreachable from this environment — the
sandbox proxy refuses it — so I could not read the primary terms page and will
not summarise from memory a document that governs what we publish. That is the
whole reason this is a STOP rather than a recommendation.

**attribution requirements**
Believed to require, visibly, wording close to:

    © EuroGeographics for the administrative boundaries

The exact required string matters, and I could not fetch it.

**redistribution requirements**
Unverified. GISCO terms are generally understood to permit redistribution of
derived maps with the attribution above. Our architecture redistributes
processed geometry as static files on our own CDN, which is redistribution,
not merely display.

**share-alike requirements**
Believed none. Unverified.

**modification requirements**
Believed none beyond attribution. Note that the source carries a **required
designation footnote**, reproduced here in full because it is an editorial
obligation on our pages, not a line in a licence file:

> The designations employed and the presentation of material on these maps do
> not imply the expression of any opinion whatsoever on the part of the
> European Union concerning the legal status of any country, territory, city
> or area or of its authorities, or concerning the delimitation of its
> frontiers or boundaries. Kosovo*: This designation is without prejudice to
> positions on status, and is in line with UNSCR 1244/1999 and the ICJ Opinion
> on the Kosovo declaration of independence.

EuropeDoor publishes a Kosovo country page. Importing this dataset therefore
imports a position — or rather, imports the obligation to print a specific
disclaimer about not taking one. That is a product decision, not a build step.

## The seven answers §24 asks for

1. **Dataset** — Eurostat NUTS 2024 levels 1–3, via Nuts2json.
2. **Licence** — code EUPL 1.2; data copyrighted, use conditional on
   accepting Eurostat's provisions, which I could not read from here.
3. **What we want to do with it** — Layer 4 of the map: real administrative
   region polygons, so that clicking into a country shows region shapes rather
   than region labels.
4. **Obligations** — a visible EuroGeographics attribution, and the
   designation footnote above wherever the boundaries appear.
5. **Alternatives** — three, and one of them is already shipping:
   - **Ship without NUTS.** EuropeDoor already holds its own regions
     (`regions[]` in every `data/countries/*.json`, with slugs, names and
     cities). Layer 3 is built from those and needs no third-party geometry at
     all. This is what is in production. The cost is that a region is drawn as
     the territory its destinations describe, not as a surveyed polygon.
   - **Natural Earth admin 1** (states and provinces) — public domain, same
     zero-obligation terms as the country layer. Coarser than NUTS and not
     aligned to EU statistical regions, but it would draw real region shapes
     with no new licence at all. **This is the cheapest way to unblock, and it
     is the one I would take if the answer to NUTS is slow.**
   - **NUTS**, once the terms are read and accepted.
6. **Estimated infrastructure cost** — €0 either way. All three are static
   files on the CDN we already pay for. NUTS would add roughly 120 KB to the
   committed repository and nothing to the bill.
7. **Recommendation** — **do not import NUTS yet.** Ship Layers 1, 2, 3, 5 and
   6 on public-domain data, which is what this session did. If region polygons
   turn out to matter more than region membership, take Natural Earth admin 1
   first, because it costs nothing and asks nothing. Reach for NUTS only when
   EU-statistical alignment is itself the requirement — and when somebody has
   read the provisions and is willing to accept them on the company's behalf.

**Nothing proceeds on this file without that answer.**
