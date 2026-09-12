/* WHAT THE ACQUISITION IS DOING, READ FROM THE RUN ITSELF.
 *
 * THE STEPS ARE THE WORKFLOW'S OWN AND ARE NOT RESTATED HERE. The local desk
 * owned its eight steps because it ran them; this desk runs nothing, so a
 * list of step names in this file would be a copy of `photograph.yml`'s
 * shape that drifts the first time somebody adds a step — the ninth thing in
 * this repository to pin a shape rather than a promise. GitHub reports every
 * step it actually ran, with its conclusion, and that is what is shown.
 *
 * FINDING THE RUN. `workflow_dispatch` answers 204 with no body, so there is
 * no run id to hold. The acquire route signs the instant before it
 * dispatched; this asks for dispatches of `photograph.yml` created since
 * then and takes the oldest. The window is inside a signed token, so a
 * caller cannot widen it to read a run they did not start.
 *
 * A RUN THAT HAS NOT APPEARED YET IS QUEUED, NOT FAILED. GitHub takes a few
 * seconds to create it, and a desk that said "failed" in that gap would be
 * reporting a verdict nobody has reached — which is the same error as
 * calling an open pull request PUBLISHED.
 */

import { requireSession, send, verify, repo, gh } from "./_lib.js";

export default async function handler(req, res) {
  if (!requireSession(req, res)) return;

  const url = new URL(req.url, "http://desk");
  const job = verify(url.searchParams.get("job") || "");
  if (!job || typeof job.since !== "number") {
    send(res, 400, { error: "that job token is not one this desk minted, or "
                          + "it has expired" });
    return;
  }

  const { slug, workflow } = repo();
  const created = `>=${new Date(job.since).toISOString()}`;
  const q = new URLSearchParams({
    event: "workflow_dispatch", created, per_page: "20",
  });
  const r = await gh(`/repos/${slug}/actions/workflows/${workflow}/runs?${q}`);
  if (!r.ok) {
    send(res, 502, { error: `GitHub answered ${r.status} for the run list` });
    return;
  }
  const runs = (await r.json()).workflow_runs || [];
  const mine = runs
    .filter((x) => new Date(x.created_at).getTime() >= job.since - 60000)
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))[0];

  if (!mine) {
    send(res, 200, {
      state: "queued", steps: [],
      note: "GitHub has not created the run yet. It takes a few seconds.",
    });
    return;
  }

  const jr = await gh(`/repos/${slug}/actions/runs/${mine.id}/jobs`);
  const jobs = jr.ok ? ((await jr.json()).jobs || []) : [];
  const steps = jobs.flatMap((j) =>
    (j.steps || []).map((s) => ({
      label: s.name,
      /* GitHub's vocabulary, mapped once: `status` is where it is and
       * `conclusion` is how it ended, and only a finished step has both. */
      state: s.conclusion === "success" ? "done"
           : s.conclusion === "skipped" ? "skipped"
           : s.conclusion ? "failed"
           : s.status === "in_progress" ? "running" : "waiting",
    })));

  /* GITHUB HAS SEVEN CONCLUSIONS AND THIS TREATED SIX OF THEM AS "FAILED".
   *
   * The first batch to reach GitHub came back `action_required`: the run was
   * created, held for approval, and concluded two seconds later having run
   * NOTHING. The desk called that a failure and told the editor "the run's
   * log has what it said" — and there is no log, because there are no jobs.
   * A verdict nobody reached, reported as a verdict, which is the same error
   * as calling an open pull request published.
   *
   * `action_required` is a question waiting for a person. `cancelled` is a
   * person's own decision. `timed_out` and `stale` are the platform. Only a
   * real `failure` is the pipeline saying no, and only that one has a log
   * worth reading. */
  const state = mine.status !== "completed" ? "running"
              : mine.conclusion === "success" ? "done"
              : mine.conclusion === "action_required" ? "approval"
              : mine.conclusion === "cancelled" ? "cancelled"
              : "failed";

  const out = { state, steps, run: mine.html_url, run_id: mine.id };

  if (state === "done") {
    /* THE PULL REQUEST IS THE DELIVERABLE, so the desk hands over the link
     * rather than saying "acquired". Nothing is published until somebody
     * merges it, and the wording here has to keep that true.
     *
     * THE RUN MERGES ITSELF NOW, AND THE DESK STILL MAY NOT ASSUME IT.
     * `gh pr merge` can be refused — branch protection, a required review, a
     * conflict — and the workflow deliberately does NOT fail on that, because
     * the photographs are acquired, registered, gated and pushed by then and
     * a red run would report a loss that did not happen. So the step is green
     * either way and its state says nothing about the outcome. The only
     * honest source is the pull request itself, which carries `merged_at`
     * in the same listing this already reads for the URL. Reporting the
     * merge from the STEP would be the `action_required` failure again: a
     * verdict nobody has reached.
     *
     * A SINGLE ACQUISITION HAS A BRANCH NAME THIS DESK CAN PREDICT AND A
     * BATCH DOES NOT: the batch names its branch from the clock inside the
     * run, because thirteen purposes cannot make one branch name that means
     * anything. So a batch is found by TIME instead — the pull requests this
     * repository opened since the instant the dispatch went out, which is the
     * same signed window the run itself was found by. */
    const owner = slug.split("/")[0];
    if (!job.batch) {
      const branch = `photo/${job.purpose}-${job.photo_id}`;
      const pr = await gh(`/repos/${slug}/pulls?head=${encodeURIComponent(
        `${owner}:${branch}`)}&state=all`);
      if (pr.ok) {
        const list = await pr.json();
        if (list.length) {
          out.pr = list[0].html_url;
          out.pr_number = list[0].number;
          out.merged = !!list[0].merged_at;
        }
      }
      out.branch = branch;
    } else {
      const pr = await gh(`/repos/${slug}/pulls?state=all&sort=created`
                        + `&direction=desc&per_page=20`);
      if (pr.ok) {
        const list = await pr.json();
        const mine = list.find((x) => (x.head && x.head.ref || "").startsWith("photo/batch-")
          && new Date(x.created_at).getTime() >= job.since - 60000);
        if (mine) {
          out.pr = mine.html_url;
          out.pr_number = mine.number;
          out.branch = mine.head.ref;
          out.merged = !!mine.merged_at;
        }
      }
      out.count = job.count;
    }
  }

  if (state === "approval") {
    out.failure =
      "GitHub created the run and is holding it for approval, so nothing "
      + "has run yet — there are no steps and no log. Open the run and press "
      + "Approve and run; GitHub's own banner there says which policy asked. "
      + "Nothing was acquired and nothing was published.";
  }

  if (state === "cancelled") {
    out.failure = "The run was cancelled before it finished. Nothing was "
                + "acquired and no pull request was opened.";
  }

  if (state === "failed") {
    /* NEVER SILENTLY CONTINUE: which step failed, and the fact that nothing
     * was published — which is true, because the pull request is the last
     * step and a failure before it leaves no branch behind. */
    /* AND THE FAILURE SENTENCE ONLY PROMISES A LOG WHEN THERE IS ONE. A run
     * with no jobs has nothing to read, and sending an editor to look for it
     * is the journey caption promising "a note under the leg" after the note
     * was removed. */
    const bad = steps.filter((s) => s.state === "failed").map((s) => s.label);
    out.failure = (bad.length ? `Failed at: ${bad.join(", ")}. ` : "")
      + "Nothing was published and no pull request was opened. "
      + (steps.length
         ? "The run's log has what it said."
         : "The run produced no steps at all, so there is no log — it was "
           + "stopped before any job started.");
  }

  send(res, 200, out);
}
