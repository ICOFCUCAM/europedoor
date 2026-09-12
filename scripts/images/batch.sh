#!/usr/bin/env bash
# ACQUIRE EVERY APPROVED PHOTOGRAPH IN A PLAN, AND DO NOT LOSE THE SITTING
# OVER ONE OF THEM.
#
# Usage: batch.sh <provider> <plan.tsv> <skipped.tsv>
#   plan.tsv     purpose, photo id, alt — one per line, tab separated
#   skipped.tsv  written here: purpose, photo id, reason, for every refusal
# Prints "took=<n>" and "skipped=<n>" on the last two lines.
#
# IT LIVES IN A FILE RATHER THAN IN THE WORKFLOW BODY, because the promise
# it makes is behavioural and a promise asserted as a string inside YAML is
# a shape. This repository has now protected a shape instead of a promise
# eleven times. `tools/photo-tests.py` runs THIS script against the stub
# provider with a plan that contains a candidate the pipeline will refuse,
# and asserts that the others still arrive.
#
# WHAT IT IS NOT: a second implementation of anything. acquire.py decides
# every refusal and derive.py builds every ladder; this reads an exit code
# and keeps a list.
#
#   3  this candidate, and the next one could still succeed  → record, skip
#   1  anything a next candidate would hit too               → stop
#
# Run 23 acquired eighteen photographs, hashed them, derived their ladders
# and completed their provenance, and threw all of them away because the
# nineteenth was a PNG: the loop ran under `set -e` and the branch was never
# pushed. All-or-nothing is right for a malformed PLAN — a reviewer cannot
# tell "these six were chosen" from "these six arrived before it broke", so
# the plan's shape is checked in full before a socket opens — and wrong for
# a judgement about one candidate, because with sixty automatic picks a
# rejection is expected rather than exceptional.
set -uo pipefail

provider="${1:?provider}"
plan="${2:?plan.tsv}"
skips="${3:?skipped.tsv}"
here="$(cd "$(dirname "$0")" && pwd)"

: > "$skips"
took=0

while IFS=$'\t' read -r purpose pid alt; do
  [ -n "${purpose:-}" ] || continue
  echo "── $purpose ── $pid"
  out=$(python3 "$here/acquire.py" \
          --provider "$provider" \
          --photo-id "$pid" \
          --purpose "$purpose" \
          --alt "$alt" \
          --focal "50,50" 2>&1)
  rc=$?
  printf '%s\n' "$out"
  if [ "$rc" = 3 ]; then
    # THE REASON IS acquire.py's OWN SENTENCE, not one composed here. A
    # summary written at this level would be a second opinion about a
    # refusal this script did not make.
    # THE WHOLE REFUSAL, ON ONE LINE. A reason is often several lines —
    # "does not suit" names every requirement it missed — and a newline in
    # a tab-separated field makes the rest of the reason look like more
    # skipped candidates. Taking only the first line instead throws the
    # measurement away and leaves "photo 3110000 does not suit door-coast:"
    # with nothing after the colon, which is the failure-message rule in a
    # new place: a reason with no measurement in it cannot be acted on.
    why=$(printf '%s' "$out" \
          | sed -n '/^CANDIDATE REFUSED: /,$p' \
          | sed 's/^CANDIDATE REFUSED: //' \
          | tr '\n\t' '  ' | sed 's/  */ /g; s/^ //; s/ $//')
    [ -n "$why" ] || why="refused, and printed no reason"
    printf '%s\t%s\t%s\n' "$purpose" "$pid" "$why" >> "$skips"
    echo "   ↳ skipped, and the surface stays empty"
    continue
  fi
  if [ "$rc" != 0 ]; then
    echo "── this is not about one candidate, so the run stops ──"
    exit "$rc"
  fi
  python3 "$here/derive.py" "$purpose" || exit 1
  took=$((took + 1))
done < "$plan"

n=$(wc -l < "$skips" | tr -d ' ')
echo "took=$took"
echo "skipped=$n"

# NOTHING ACQUIRED IS A FAILED RUN, however politely each entry was refused.
# A green run with an empty branch would report a sitting that produced
# nothing as a sitting that worked.
if [ "$took" = 0 ]; then
  echo "every one of the $n approved photographs was refused. Nothing was" \
       "acquired, so there is nothing to review." >&2
  exit 1
fi
