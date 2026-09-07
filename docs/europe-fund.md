# The Europe Fund, and why it holds nothing

The Fund is the distinctive part of the model and the part most likely to
get somebody into trouble. This document is why it currently holds no money,
and what has to be true before it does.

## What it is today

A public register of twelve projects — heritage repair, landscape, language,
craft, trails, memory — each with a named local partner, what it needs, and a
status. Nothing more.

There is **no balance, no total raised, no progress bar, and no donate
button** anywhere on the site. `tools/checks.py` fails the build if a fund
page grows a `<form>`, a link to a payment processor, a button offering to
give, or an amount described as raised. `tools/lib/data.py` rejects a project
record carrying `amount`, `raised`, `goal` or `target`.

That enforcement exists because this is exactly the kind of thing that gets
added by a well-meaning person in a hurry, six months from now, without
anybody re-reading this file.

## Why not just take contributions

Because taking money from the public for the benefit of third parties is a
regulated activity almost everywhere in Europe, and the specific regulation
depends on how it is framed. Three gates:

**1. There is no entity.** No company is incorporated. Every page carries
`[OPERATOR ENTITY — NOT YET INCORPORATED]` in the footer, and `checks.py`
verifies that no page names a company form. You cannot hold money for others
without being someone.

**2. There is no named payee.** The rule we hold ourselves to: **the day a
card field appears on this site without naming who receives the money, the
check has failed.** A traveller must be able to see, before typing a number,
which legal person is taking it.

**3. There is no written position on treatment.** Whether a contribution is a
donation, a restricted gift, a purchase with a charitable element, or agency
money held for a partner changes the accounting, the tax, the consumer law
and — in several countries — whether a fundraising registration is required.
That is a question for a lawyer in each collecting jurisdiction, not a
question for a product decision.

## What "operational" would look like

When those three are cleared, each project page shows, in this order:

1. what was received;
2. what was paid to the named partner;
3. what was retained for running costs, as a percentage stated in advance.

In that order, because a page that leads with the total raised is a page
about us, and a page that leads with what reached the partner is a page about
the project. If the retained percentage is embarrassing, the answer is to
change it, not to move it further down.

## Why the projects were chosen this way

Two filters, both deliberate:

* **Small enough that a travel platform could plausibly matter.** Roofs on
  village churches nobody tours, blades for hand-scythed hay meadows, kiln
  repair for the eight remaining qvevri makers. Not cathedral restoration.
* **Specific enough that you could go and look at the result.** Every project
  names a partner and a place that exists in the Atlas. "Supporting
  communities" is not a project.

## The connection to the rest of the product

The Fund is not a charity bolted onto a travel site. It is the answer to a
question the rest of the product raises: `/beyond-the-obvious` argues that
tourism pressure is a distribution problem, and the Fund is what the
distribution is for. A platform that sends people to a quiet valley and puts
nothing back into the path they walked on has just moved the problem.

That argument only works if the money actually arrives. Which is why it does
not start until it can be shown arriving.
