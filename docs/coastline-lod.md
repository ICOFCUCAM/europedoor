# Local coastline resolution — the experiment, and the rule it produced

**Question:** does finer geometry materially improve the geographic portrait
at the scale at which EuropeDoor displays it?

**Answer: yes, and for two reasons, one of which was not the one being
tested.** The rule is now: a destination plate framing **under 1,000 km**
draws from the local geometry; above that it draws from the continental file.
Nothing else in the atlas changed.

## What was measured

Five destinations, at their real frames, three ways. **A** the continental
file (0.04° ≈ 4.4 km), **B** the local file (0.012° ≈ 1.3 km) unclipped,
**C** the local file clipped to the window.

| place | frame | | coords | bytes | build ms |
|---|---|---|---|---|---|
| Athens | 578 km | A | 492 | 6,280 | 5.5 |
| | | B | 7,271 | 89,661 | 19.4 |
| | | **C** | **895** | **11,119** | **7.0** |
| Bergen | 582 km | A | 305 | 3,928 | 5.1 |
| | | B | 7,768 | 95,517 | 20.2 |
| | | **C** | **560** | **6,988** | **6.7** |
| Corfu | 581 km | A | 578 | 7,529 | 5.5 |
| | | B | 7,271 | 89,661 | 19.2 |
| | | **C** | **990** | **12,475** | **7.3** |
| Chamonix | 589 km | A | 405 | 5,449 | 5.1 |
| | | B | 7,230 | 89,268 | 19.3 |
| | | **C** | **729** | **9,377** | **6.7** |
| Kraków | 739 km | A | 462 | 6,122 | 5.3 |
| | | B | 7,496 | 92,357 | 19.4 |
| | | **C** | **894** | **11,306** | **7.4** |

**Browser render time is the same for all three.** Measured as load time on
the shipped page at 1280 px: every variant lands between 13 and 23 ms, and the
spread within one variant across repeats is as large as the spread between
variants. The cost of finer geometry here is bytes and build time, not paint.

**B is the same picture as C.** Everything B carries beyond C is outside the
window and thrown away by the viewBox — 8 times the bytes for nothing a reader
can see. That is not a footnote: it is the whole reason this is affordable.
The clip is not an optimisation of the idea, it *is* the idea.

## What it looks like

**Athens is the case the experiment was opened for.** At A the Gulf of Corinth
is a chevron, Attica is a wedge and the Cyclades are lozenges. At C the gulf
tapers, the Argolic peninsulas exist and the islands have shape. 4.4 km is
nine pixels on a 578 km frame drawn 900 units wide; 1.3 km is under three.

**Bergen** gains articulated fjord arms and the coastal islands. The outer
coast stays nearly straight at both levels, because the skerries are
individually below the smaller file's own minimum feature size — a limit of
1:50m, not of this rule.

**Kraków, the inland control, found the second defect.** It has no coastline
at all, and at A it had thin slivers of **sea colour running along the Polish
frontier and the Danube**: two neighbouring countries simplified independently
do not share an edge, so the gap between them shows the ocean through. At C
they are gone. That defect was on inland pages, where nobody was looking for a
coastline problem.

**At 390 px the gain is small.** Athens is still visibly better — the gulf
reads as a taper — and Corfu is close to indistinguishable. The rule does not
vary by viewport anyway: a geometry that changes with screen width is two maps
of the same place, which is the same argument that removed the second terrain
strength.

## The rule

    frame < geo.LOCAL_LOD_MAX_KM (1,000 km)  ->  local geometry, clipped
    frame >= that                            ->  the continental file

277 of 319 destinations are under the cap. The 42 above frame between 1,100
and 2,400 km — Iceland, Nordkapp, Svalbard, Moscow, Skye — and at that scale
4.4 km of simplification is a third of a pixel.

**No new data.** The finer file has been in the repository since the country
plates were built: one per country, carrying that country and every neighbour
whose box comes within 0.75°. `geo.local()` merges it over the continental
file so a frame that reaches two countries further still has land in it.

**Nothing else moved.** `/map`, the country plates, the macro regions, the
journeys and every instrument keep the level they had. This is a local-frame
rule, not an upgrade of the atlas.

`checks.py` recovers each plate's own frame from its transform and its
caption, rebuilds the land both ways, and requires the page to carry the one
the rule selects — sampled at the boundary, the widest frames below the cap
and the narrowest above it, because that is the only place a threshold can be
wrong. Proved red by inverting the comparison.

## And the thing the experiment found by accident

Building the harness meant rendering plates through `cartography.plate()`
directly, and the same rivers appeared on every one of them regardless of
where it was. They appeared on the shipped pages too.

**`plate()` conflated two coordinate spaces, and every destination and journey
plate drew the same 111 watercourses.** `w` and `h` are the viewBox; `view` is
the window in the projection's coordinates. On a country plate they are the
same thing, because the projection is fitted to the frame. On a destination
plate they are not: the continent is drawn at 1000×780 and the plate scales a
small window of it up inside a translate-and-scale. Every caller passed
`view=(0, 0, w, h)` regardless, so the layers the renderer draws itself asked
"which rivers are in the rectangle (0,0)–(900,320) of Europe" — the North Sea
and Finland — and drew the answer at continent coordinates on top of a picture
of the Alps.

The Kama, the Dalälven, the Kemijoki and the Neva were on Chamonix, on Bergen
and on Athens, identically, on all 824 of them. **It survived because it looks
right**: blue lines and lakes on a map read as rivers wherever they are. The
country plates were correct throughout, because they pass a real projection
and no transform, and that is exactly what kept the fault from ever being
compared against anything.

Two more faults were underneath it:

* **A river was emitted whole if any point of it was in the window**, so a
  plate showing fifty kilometres of the Danube shipped the Danube from the
  Black Forest to the Black Sea. Clipped now, in runs, with one point either
  side so the line still reaches the frame edge.
* **The pad was a flat 40 units**, written when `view` was the 900-unit
  continent frame and left when it became a 90-unit window — 44% of the
  picture on each side. Proportional now, like the coastline's own clip.

And `macromap` was passing the continent projection while drawing with its
own, so anything the renderer placed for it was placed by a projection that
picture does not use.

The fix is not the three call sites: `plate()` takes `view` and `transform` as
separate parameters and applies the transform to everything it renders itself.
A caller cannot get half of it right any more, because a caller no longer does
any of it.

Chamonix went from 93,039 bytes to 71,819 — a finer coastline, real terrain,
and twenty-one kilobytes of the wrong rivers gone.
