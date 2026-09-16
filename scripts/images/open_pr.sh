#!/usr/bin/env bash
#
# Open the pull request for an acquisition, and report a refusal honestly.
#
# ONE IMPLEMENTATION, BECAUSE THERE WERE TWO AND BOTH WERE WRONG THE SAME
# WAY. The `acquire` job and the `batch` job each carried this block inline,
# so the diagnostic below had to be got right twice and was got wrong twice —
# the eighth time in this repository that a second implementation of one
# thing has been a second chance to make its mistake. `batch.sh` is the
# precedent: a promise that is behavioural belongs in a script that can be
# read and tested, not in a YAML block scalar copied down the file.
#
# THE BRANCH IS ALREADY PUSHED BY THE TIME THIS RUNS, so a refusal here must
# never read as "the acquisition failed". Everything is on the branch either
# way, and the log says where.
#
# AND IT PRINTS THE ERROR RATHER THAN ASSERTING A CAUSE. The previous version
# ended with "The usual cause is Settings -> Actions -> General -> Workflow
# permissions", which is a real cause and was not this one: runs 35 and 36
# were both refused with `GraphQL: Body is too long (maximum is 65536
# characters)`, and the message sent whoever read it to a settings page that
# had nothing to do with it. A failure message with no measurement in it
# cannot be diagnosed — and one that names a cause it never checked is worse
# than silence, because it is confidently wrong. gh's own words go first, the
# body's size goes beside them, and the guess is clearly marked as a guess
# and comes last.
set -euo pipefail

TITLE="$1"; BODY="$2"; BRANCH="$3"; BASE="$4"; REPO="${5:-$GITHUB_REPOSITORY}"

if gh pr create --title "$TITLE" --body-file "$BODY" \
                --head "$BRANCH" --base "$BASE" 2>/tmp/pr-error.txt; then
  exit 0
fi

echo
echo "── THE PULL REQUEST WAS REFUSED AND THE WORK IS SAFE ──"
echo "Everything acquired is on the branch: $BRANCH"
echo "Open it by hand here:"
echo "  https://github.com/$REPO/compare/$BASE...$BRANCH?expand=1"
echo
echo "WHAT GITHUB ACTUALLY SAID:"
sed 's/^/  /' /tmp/pr-error.txt
echo
echo "The body it refused was $(wc -c < "$BODY") characters"
echo "and GitHub's limit is 65536."
echo
echo "If the body is within that limit, the next thing to check is"
echo "Settings -> Actions -> General -> Workflow permissions ->"
echo "'Allow GitHub Actions to create and approve pull requests',"
echo "which is a separate switch from the permissions this workflow"
echo "requests. That is a guess; the lines above are the evidence."
exit 1
