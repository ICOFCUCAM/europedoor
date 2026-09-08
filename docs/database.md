# Database

## There is no database

The source of truth is `data/`: 50 country files and 7 shared files, plain
JSON under version control, validated on every build.

This is not a stage before a database. It is the correct storage layer for a
product whose entire write path is "an editor opens a pull request", and it
buys four things a database would take away:

| | |
|---|---|
| **Review** | every change is a diff a human reads before it ships |
| **History and rollback** | free, per field, for ever, with blame |
| **No operational surface** | nothing to back up, patch, scale or breach |
| **Deterministic builds** | the same input produces the same 988 pages |

## The schema, in code

`tools/lib/data.py` is the schema. It validates on every build and it
**collects every problem before raising**, so one run fixes one round of
mistakes rather than one mistake.

What it enforces that a naive schema would not:

- **Volatile fields are refused, not nullable.** `hours`, `price`, `website`
  and `phone` on a place are rejected outright. A nullable column invites
  somebody to fill it in with something stale; a wrong opening time sends
  somebody across a city.
- **Confidence is derived, never authored.** A `confidence` key in a data
  file is a validation error. A field a person can type is a field somebody
  types "high" into.
- **A verification record expires.** A check is good for `REVIEW_DAYS` and
  then reads as *due for review*. Four states — never, current, due,
  unverified — because "never checked" and "checked a year ago" are different
  problems with different fixes.
- **No image without a photographer, a source and an https licence URL.**
- **No `rank`, `boost`, `featured` or `sponsored` on a place.** Enforced by
  the absence of a field, which is the only version of that promise worth
  making.

`docs/data-model.md` is the field-by-field reference.

## The relational model, for when it is needed

`docs/technical-foundation.md` §1 has the full PostgreSQL/PostGIS schema:
spatial types on destinations, the account/saved_item/itinerary tables the
static build has no equivalent for, per-claim `fact_check` with generated
confidence, the `image` register, and the constraints that carry the
product's public promises.

**It is not built.** The trigger list is in that document and in
`docs/roadmap.md`. The short version: a database becomes correct the day
somebody who is not a committer needs to write, and that needs accounts,
which need a data controller, which needs a company.

## Backups

`git`. Every version of every fact, for ever, on every clone.
