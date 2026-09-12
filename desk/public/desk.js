/* THE HOSTED MEDIA DESK, BROWSER HALF.
 *
 * It sends a provider, a photo id, a purpose and an alt text. It never sees a
 * key, never calls a provider, and never fetches an image from anywhere but
 * this deployment — every preview goes through /api/thumb, so the editor's
 * browser makes no request to pexels.com at all.
 *
 * NOTHING HERE RANKS, SORTS OR PRESELECTS. The order is the provider's own
 * and the sheet says so on its face. A highlighted cell is a recommendation
 * by another name, and position is exactly what `--pick 3` got wrong: the
 * photograph a person approves and the photograph that arrives must be the
 * same one, which is why the approval carries an ID and never an index.
 *
 * THE REQUIREMENTS BELONG TO THE SLOT, and this reads them from there. A
 * templated instance carries none of its own — 590 copies of one brief is
 * 590 places for it to differ — so every lookup goes through `specOf`.
 */
(function () {
  "use strict";

  var REG = { purposes: [], slots: {}, providers: {} };
  /* THE SAME NUMBER THE DISPATCH ENFORCES, and the dispatch is the one
     that counts — this copy exists so the button can say what will
     happen instead of the editor finding out from a 400. */
  var BK_CAP = 60;
  var CHOSEN = null;
  var POLL = null;

  function el(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? "" : s); }

  function api(path, opts) {
    opts = opts || {};
    opts.headers = Object.assign({ "X-Desk": "1" }, opts.headers || {});
    if (opts.body) opts.headers["Content-Type"] = "application/json";
    return fetch(path, opts).then(function (r) {
      return r.json().then(function (j) {
        return { ok: r.ok, status: r.status, j: j };
      }, function () { return { ok: r.ok, status: r.status, j: {} }; });
    });
  }

  /* The two halves of a purpose's answer, put back together in one place. */
  function specOf(row) {
    if (!row) return null;
    var slot = row.slot ? REG.slots[row.slot] : null;
    return Object.assign({}, slot || {}, row);
  }

  /* ── sign in ──────────────────────────────────────────────── */
  function show(signedIn) {
    el("gate").hidden = signedIn;
    el("desk").hidden = !signedIn;
    if (signedIn) { basketLoad(); basketBadge(); loadRegistry(); }
    else el("passcode").focus();
  }

  el("signin").addEventListener("submit", function (e) {
    e.preventDefault();
    var box = el("passcode");
    var btn = e.target.querySelector("button");
    btn.disabled = true;
    api("/api/signin", { method: "POST",
      body: JSON.stringify({ passcode: box.value }) }).then(function (r) {
      btn.disabled = false;
      if (r.ok) { box.value = ""; el("gate-err").textContent = ""; show(true); }
      else el("gate-err").textContent = r.j.error || "sign in failed";
    });
  });

  el("signout").addEventListener("click", function () {
    api("/api/signout", { method: "POST" }).then(function () { show(false); });
  });

  /* ── the registry ─────────────────────────────────────────── */
  function loadRegistry() {
    api("/api/registry").then(function (r) {
      if (!r.ok) return show(false);
      REG = r.j;
      showTarget();
      fillSlots();
      fillLibrary();
      fillProvenance();
      /* THE BAND IS DERIVED FROM THE REGISTER AND REDRAWN WHENEVER IT IS
         RE-READ, so the count it states is the count the library actually
         holds rather than the one it held when the desk opened. A figure
         that goes stale reads as a measurement and is not one. */
      topupState();
    });
  }

  /* One option per SLOT plus one per declared purpose. 593 instances in a
     <select> would be a list nobody can use; the target is a second field
     with a datalist, which is how a person actually thinks about it —
     "a destination hero, for Chamonix". */
  function fillSlots() {
    var sel = el("slot"), libSel = el("lib-slot");
    var seen = {}, html = "";
    REG.purposes.forEach(function (p) {
      var v = p.slot || p.purpose;
      if (seen[v]) return;
      seen[v] = true;
      html += '<option value="' + esc(v) + '">' + esc(v) + "</option>";
    });
    sel.innerHTML = html;
    libSel.innerHTML = '<option value="">Any</option>' + html;
    fillCountries();
    if (!sel.dataset.wired) { sel.dataset.wired = "1";
      sel.addEventListener("change", onSlot);
      el("country").addEventListener("change", onCountry);
      el("target-q").addEventListener("input", hits);
      el("sw-slot").addEventListener("change", swSlots);
      el("sweep").addEventListener("submit", sweep);
      el("sw-all").addEventListener("click", function () { tickAll(true); });
      el("sw-none").addEventListener("click", function () { tickAll(false); });
      el("sw-go").addEventListener("click", acquireTicked); }
    onSlot();
  }

  /* EVERY COUNTRY THE REGISTRY KNOWS, ONCE, IN ITS OWN NAME. Derived from
     the rows rather than listed anywhere, so a country added to the atlas
     appears here on the next build and one removed disappears — the same
     reason the targets come from the atlas and not from the spec file. */
  function countries() {
    var seen = {};
    REG.purposes.forEach(function (p) {
      if (p.country) seen[p.country] = p.country_name;
    });
    return Object.keys(seen).sort(function (a, b) {
      return seen[a].localeCompare(seen[b]);
    }).map(function (k) { return [k, seen[k]]; });
  }

  function fillCountries() {
    var opts = countries().map(function (c) {
      return '<option value="' + esc(c[0]) + '">' + esc(c[1]) + "</option>";
    }).join("");
    el("country").innerHTML = '<option value="">Every country</option>' + opts;
    el("lib-country").innerHTML =
      '<option value="">Every country</option>' + opts;
  }

  function onCountry() { onSlot(true); }

  /* An acquisition runs on a branch, and the desk used to say so nowhere.
     The first real batch was refused by GitHub for an input the target
     branch had never heard of — accurate, about a field the editor never
     typed, and silent about the only thing that mattered. */
  function showTarget() {
    var d = REG.dispatch;
    if (!d) { el("target-branch").textContent = ""; return; }
    el("target-branch").textContent = d.repo + " · " + d.branch;
    el("target-branch").title =
      "Acquisitions are dispatched to this branch. Set DESK_BRANCH to change it.";
  }

  function instancesOf(slot) {
    return REG.purposes.filter(function (p) { return p.slot === slot; });
  }

  function onSlot(keepCountry) {
    var v = el("slot").value;
    var rows = instancesOf(v);
    var isSlot = rows.length > 0;
    /* A COUNTRY IS ONLY A QUESTION WHERE THE SLOT HAS ONE. A story-hero has
       no country — its places are in several — so offering the filter there
       would be offering a control that can only ever empty the list. */
    var hasCountry = rows.some(function (p) { return !!p.country; });
    el("country-wrap").hidden = !hasCountry;
    el("target-wrap").hidden = !isSlot;
    el("target").required = isSlot;
    if (!keepCountry && !hasCountry) el("country").value = "";
    if (isSlot) {
      var c = hasCountry ? el("country").value : "";
      POOL = c ? rows.filter(function (p) { return p.country === c; }) : rows;
      if (!keepCountry) setTarget(null);
      else if (el("target").value && POOL.every(function (p) {
        return p.target !== el("target").value;
      })) setTarget(null);
      hits();
    } else { POOL = []; setTarget(null); }
    var spec = specOf(isSlot ? rows[0] : REG.purposes.filter(function (p) {
      return p.purpose === v;
    })[0]);
    showBrief(spec);
    showNeeds(spec);
    showConcepts(spec, isSlot ? null : v);
  }

  /* THE ROLE'S SEARCH CONCEPTS, WITH THE SURFACE'S NAME IN THEM.
     `{name}` is substituted here rather than in the generated registry,
     because one template is one decision and 593 substitutions of it are 593
     copies. Without a chosen place the templated concepts are shown with the
     placeholder visible, so an editor can see the shape before picking one. */
  function showConcepts(spec, declared) {
    var box = el("concepts");
    var list = (spec && spec.search) || [];
    if (!list.length) { box.hidden = true; box.innerHTML = ""; return; }
    var row = REG.purposes.filter(function (p) {
      return p.target && p.target === el("target").value;
    })[0];
    var name = row ? placeName(row) : "";
    box.hidden = false;
    box.innerHTML = '<p class="suggest-lab">What to search for</p>' +
      list.map(function (c) {
        var q = c.replace(/\{name\}/g, name || "…");
        return '<button type="button" class="concept"' +
          (name || c.indexOf("{name}") < 0 ? ' data-q="' + esc(q) + '"' : " disabled") +
          ">" + esc(q) + "</button>";
      }).join("") +
      (name ? "" : '<p class="hint">Choose a place and these fill in.</p>');
    box.querySelectorAll("[data-q]").forEach(function (b) {
      b.addEventListener("click", function () {
        el("q").value = b.dataset.q;
        el("q").focus();
      });
    });
  }

  /* A ONE-OF-A-KIND PURPOSE HAS NO SUBSTITUTION, AND HAD ONE FOR ONE COMMIT.
     The first version filled `{name}` with "Europe" for a declared purpose,
     which is a substitution rule living in the browser rather than in the
     vocabulary — and it hid a real fault: the `food` role's concepts carried
     a placeholder that no slot instantiates. checks.py caught it the run it
     was written. A declared purpose's concepts say what they mean.
     */

  /* The first sentence is the art direction; the rest is how the numbers
     were chosen, which an editor wants once and not on every search. */
  function showBrief(p) {
    var box = el("slot-note");
    var note = (p && p.note) || "";
    if (!note) { box.innerHTML = ""; return; }
    var cut = note.indexOf(". ");
    var lead = cut > 0 ? note.slice(0, cut + 1) : note;
    var rest = cut > 0 ? note.slice(cut + 2) : "";
    box.innerHTML = "<p>" + esc(lead) + "</p>" +
      (rest ? "<details><summary>Why these numbers</summary>" +
              '<p class="rest">' + esc(rest) + "</p></details>" : "");
  }

  function showNeeds(p) {
    if (!p) { el("needs").textContent = ""; return; }
    el("needs").innerHTML =
      "This slot needs <b>" + p.min_width + "px</b> native width, <b>" +
      esc(p.orientation) + "</b>, aspect <b>" + p.min_aspect + "–" +
      p.max_aspect + "</b>. Those come from the slot, not from this form.";
  }

  /* ── finding a place by its name ──────────────────────────────────
     A datalist matches the typed string against an option's VALUE, and the
     value here is a path: `austria/salzburg-and-the-lakes/salzburg`. So
     "Hohensalzburg Fortress" matched nothing and a reader who knows a place
     by its name could not find it. This matches the SURFACE sentence, which
     is where the atlas writes the name, and shows what it matched rather
     than a slug. */
  var POOL = [];

  function hits() {
    var q = el("target-q").value.trim().toLowerCase();
    var box = el("target-hits");
    if (!q || !POOL.length) { box.hidden = true; box.innerHTML = ""; return; }
    var found = POOL.filter(function (p) {
      return (p.surface + " " + p.target).toLowerCase().indexOf(q) >= 0;
    });
    /* THE COUNT IS THE SET'S OWN EXTENT, not the number on the screen. A
       list that shows twelve of forty and says nothing reads as forty. */
    var show = found.slice(0, 12);
    box.hidden = false;
    box.innerHTML = show.map(function (p) {
      return '<li><button type="button" data-t="' + esc(p.target) + '">' +
        esc(placeName(p)) + '<span class="where">' + esc(p.target) +
        "</span></button></li>";
    }).join("") + (found.length > show.length
      ? '<li class="more">' + (found.length - show.length) +
        " more match — keep typing.</li>"
      : (found.length ? "" : '<li class="more">Nothing here matches that.</li>'));
    box.querySelectorAll("[data-t]").forEach(function (b) {
      b.addEventListener("click", function () {
        setTarget(POOL.filter(function (p) {
          return p.target === b.dataset.t;
        })[0]);
      });
    });
  }

  /* The atlas writes the name inside the surface sentence, so it is read out
     of there rather than rebuilt from a slug — which would give "alps and
     east" and "hohensalzburg". */
  function placeName(p) {
    var m = /of the (.+?) (?:destination|place) page/.exec(p.surface || "");
    if (m) return m[1];
    var m2 = /of the story “(.+?)”/.exec(p.surface || "");
    if (m2) return m2[1];
    return p.surface || p.target;
  }

  function setTarget(p) {
    el("target").value = p ? p.target : "";
    if (p) window.setTimeout(function () {
      var v = el("slot").value;
      var rows = instancesOf(v);
      showConcepts(specOf(rows.length ? rows[0] : p), rows.length ? null : v);
    }, 0);
    el("target-chosen").hidden = !p;
    el("target-chosen").textContent = p ? placeName(p) + " · " + p.target : "";
    el("target-hits").hidden = true;
    if (p) el("target-q").value = "";
  }

  function currentPurpose() {
    var v = el("slot").value;
    var rows = instancesOf(v);
    if (!rows.length) return v;
    var t = el("target").value.trim();
    return t ? v + "@" + t : "";
  }

  /* ── search ───────────────────────────────────────────────── */
  el("find").addEventListener("submit", function (e) {
    e.preventDefault();
    var purpose = currentPurpose();
    if (!purpose) {
      el("sheet-note").textContent = "Choose a target for this slot first.";
      return;
    }
    el("sheet").innerHTML = "";
    el("sheet-note").textContent = "Searching…";
    api("/api/search?provider=pexels&purpose=" + encodeURIComponent(purpose) +
        "&q=" + encodeURIComponent(el("q").value))
      .then(function (r) {
        if (!r.ok || r.j.error) {
          el("sheet-note").textContent = (r.j && r.j.error) || "search failed";
          return;
        }
        draw(r.j, purpose);
      });
  });

  function draw(res, purpose) {
    var n = res.candidates.length;
    var suits = res.candidates.filter(function (c) { return c.suits; }).length;
    el("sheet-note").textContent =
      n + " candidate" + (n === 1 ? "" : "s") + ", " + suits +
      " meeting the slot's minimum. Order is " + res.order + ".";
    el("sheet").innerHTML = res.candidates.map(function (c) {
      return '<article class="cand">' +
        '<figure><img loading="lazy" alt="' +
          esc(c.alt || ("photograph " + c.id)) + '" src="/api/thumb?t=' +
          encodeURIComponent(c.thumb) + '"></figure>' +
        "<h3>" + esc(c.alt || "Untitled") + "</h3>" +
        '<p class="by">' + esc(c.photographer) + " · Pexels</p>" +
        '<p class="dims">' + c.width + " × " + c.height + " · " + c.aspect +
          " · id " + esc(c.id) + "</p>" +
        (c.suits
          ? '<p class="verdict ok">Meets this slot</p>'
          : '<p class="verdict no">Does not meet this slot<ul><li>' +
            c.why_not.map(function (w) { return esc(w.split(" — ")[0]); }).join("</li><li>") +
            "</li></ul></p>") +
        (c.already.length
          ? '<p class="dupe">Already registered, for ' +
            c.already.map(esc).join(", ") + "</p>"
          : "") +
        '<p class="acts">' +
          /* TWO ACTS, AND THE BASKET ONE IS FIRST BECAUSE IT IS THE ONE
             THAT COSTS NOTHING. Acquire opens the approval dialogue and
             ends in a pull request; Keep puts the candidate aside and
             leaves the editor in the search they are already in. The
             one-at-a-time path is kept exactly as it was — this family
             of surface is sometimes a single deliberate purchase. */
          (c.suits && !c.already.length
            ? '<button type="button" class="quiet" data-bag="' + esc(c.id) +
                '">Keep</button>' +
              '<button type="button" class="go" data-id="' + esc(c.id) + '">Acquire</button>'
            : "") +
          '<a href="' + esc(c.page) + '" target="_blank" rel="noopener noreferrer">View on Pexels</a>' +
        "</p></article>";
    }).join("");
    el("sheet").querySelectorAll("[data-id]").forEach(function (b) {
      b.addEventListener("click", function () {
        var c = res.candidates.filter(function (x) { return x.id === b.dataset.id; })[0];
        openAcquire(c, purpose, res.surface);
      });
    });
    /* KEPT, NOT ACQUIRED — and the card says which, where the editor is
       looking, rather than only the tab count changing somewhere else. */
    el("sheet").querySelectorAll("[data-bag]").forEach(function (b) {
      b.addEventListener("click", function () {
        var c = res.candidates.filter(function (x) { return x.id === b.dataset.bag; })[0];
        var said = basketAdd(purpose, c);
        b.textContent = "Kept";
        b.disabled = true;
        var note = document.createElement("span");
        note.className = "kept";
        note.textContent = said;
        b.parentNode.appendChild(note);
      });
    });
  }

  /* ── acquire ──────────────────────────────────────────────── */
  function openAcquire(c, purpose, surface) {
    CHOSEN = { candidate: c, purpose: purpose };
    el("ack-shot").innerHTML = '<img alt="' +
      esc(c.alt || ("photograph " + c.id)) + '" src="/api/thumb?t=' +
      encodeURIComponent(c.thumb) + '">';
    el("ack-facts").innerHTML =
      "<dt>Photographer</dt><dd>" + esc(c.photographer) + "</dd>" +
      "<dt>Pexels ID</dt><dd>" + esc(c.id) + "</dd>" +
      "<dt>Original</dt><dd>" + c.width + " × " + c.height + "</dd>" +
      "<dt>Purpose</dt><dd>" + esc(purpose) + "</dd>" +
      "<dt>Surface</dt><dd>" + esc(surface) + "</dd>";
    el("alt").value = "";
    offerAlt(c, purpose);
    el("acquire").showModal();
    el("alt").focus();
  }

  /* ── what the photograph shows ─────────────────────────────────────
     THE FIELD IS NOT PREFILLED, AND THAT IS THE WHOLE DESIGN. A prefilled
     alt is an alt nobody reads: the editor tabs past it and a sentence
     written by somebody who was describing a stock photograph ships as this
     site's description of its own hero. It is offered as a button instead —
     one click to take it, and taking it is a decision.

     ONE SUGGESTION, AND IT IS THE PHOTOGRAPHER'S. Generating three
     alternatives would mean writing descriptions of a photograph nothing
     here has seen, which is the licence-from-memory failure in another
     costume. Pexels publishes `alt` per photograph, written by somebody who
     looked at it; that is a source. Where a photograph has none, the panel
     says so rather than inventing one. */
  function offerAlt(c, purpose) {
    var box = el("alt-suggest");
    if (!c.alt) {
      box.hidden = false;
      box.innerHTML = '<p class="nosuggest">This photograph carries no ' +
        "description from the photographer, so there is nothing to offer. " +
        "Write what is in the frame.</p>";
      return;
    }
    box.hidden = false;
    box.innerHTML = '<p class="suggest-lab">The photographer\u2019s own ' +
      'description</p><button type="button" class="chip" id="alt-take">' +
      esc(c.alt) + "</button>";
    el("alt-take").addEventListener("click", function () {
      el("alt").value = c.alt;
      el("alt").focus();
      warnAlt(purpose);
    });
    warnAlt(purpose);
  }

  /* THE HINT SAYS "NOT THE PLACE NAME" AND A HINT IS NOT A CHECK. The first
     acquisition typed exactly the place name into it, one line under the
     sentence saying not to — so the panel now reads what is there and says
     what is wrong with it, which is what a hint cannot do. It never blocks:
     an editor who means it types it anyway. */
  function warnAlt(purpose) {
    var w = el("alt-warn");
    var v = el("alt").value.trim();
    var t = (purpose.split("@")[1] || "").split("/").pop().replace(/-/g, " ");
    var bare = v.toLowerCase().replace(/[^a-z0-9 ]+/g, " ")
                .replace(/\s+/g, " ").trim();
    var why = "";
    if (v && v.length < 15) {
      why = "That is too short to describe a photograph to somebody who " +
            "cannot see it.";
    } else if (t && bare && (bare === t || bare.indexOf(t) === 0
               && bare.length < t.length + 12)) {
      why = "That is the place name, and the page already carries it. " +
            "Say what is in the frame \u2014 the light, the water, the " +
            "buildings, the weather.";
    }
    w.hidden = !why;
    w.textContent = why;
  }

  el("alt").addEventListener("input", function () {
    if (CHOSEN) warnAlt(CHOSEN.purpose);
  });

  el("acquire").addEventListener("close", function () {
    if (el("acquire").returnValue !== "go" || !CHOSEN) return;
    var alt = el("alt").value.trim();
    if (!alt) return;
    api("/api/acquire", { method: "POST", body: JSON.stringify({
      provider: "pexels", photo_id: CHOSEN.candidate.id,
      purpose: CHOSEN.purpose, alt: alt })
    }).then(function (r) {
      if (!r.ok) { alert(r.j.error || "could not start"); return; }
      watch(r.j.job);
    });
  });

  /* ── progress ─────────────────────────────────────────────── */
  /* THE STEPS ARE THE RUN'S OWN. Nothing here holds a list of them, because
     a list in the browser is a copy of the workflow's shape that drifts the
     first time somebody adds a step to it. */
  function watch(jid) {
    el("prog-title").textContent = "Acquiring photograph…";
    el("prog-why").hidden = true;
    el("prog-steps").innerHTML = "";
    el("progress").showModal();
    tick(jid);
    POLL = setInterval(function () { tick(jid); }, 3000);
  }

  function tick(jid) {
    api("/api/status?job=" + encodeURIComponent(jid)).then(function (r) {
      if (!r.ok) return;
      var job = r.j;
      if (job.state === "queued") {
        el("prog-steps").innerHTML = '<li class="waiting"><span class="tick">·' +
          '</span><span class="lbl">' + esc(job.note) + "</span></li>";
        return;
      }
      el("prog-steps").innerHTML = job.steps.map(function (s) {
        var mark = s.state === "done" ? "✓"
                 : s.state === "failed" ? "✕"
                 : s.state === "running" ? "▸" : "·";
        return '<li class="' + s.state + '"><span class="tick">' + mark +
          '</span><span class="lbl">' + esc(s.label) + "</span></li>";
      }).join("") + (job.run
        ? '<a class="runlink" href="' + esc(job.run) +
          '" target="_blank" rel="noopener noreferrer">Watch the run on GitHub</a>'
        : "");

      if (job.state === "done") {
        stop();
        /* THE WORD FOLLOWS THE PULL REQUEST, NEVER THE RUN.
           The run merges itself now, and `gh pr merge` can still be refused
           by branch protection, a required review or a conflict — and the
           workflow deliberately does not fail on that, because by then the
           photographs are acquired, registered, gated and pushed, and a red
           run would report a loss that did not happen. So a green run does
           not mean a merged one. `merged` is read off the pull request's own
           `merged_at`, and this says one of two different things because
           they ARE two different things. Calling an unmerged acquisition
           published was the boundary this panel was built to hold; calling a
           merged one "waiting for you" is the same fault reversed, and the
           sentence under it has to move with the mechanism. */
        el("prog-title").textContent = job.merged
          ? "Acquired and merged"
          : "Acquired, and waiting for you";
        el("prog-steps").insertAdjacentHTML("beforeend",
          (job.pr
            ? '<a class="prlink" href="' + esc(job.pr) + '" target="_blank" ' +
              'rel="noopener noreferrer">' +
              (job.merged ? "Pull request #" : "Review pull request #") +
              esc(job.pr_number) + "</a>"
            : '<p class="notyet">The branch is <span class="branch">' +
              esc(job.branch) + "</span>.</p>") +
          (job.merged
            ? '<p class="notyet">Merged. europedoor.com carries it from the ' +
              "next deployment. The pull request stays as the record: the " +
              "rendered page, the provenance row and both hashes.</p>"
            : '<p class="notyet">Nothing on europedoor.com has changed. The ' +
              "pull request carries the rendered page, the provenance row " +
              "and both hashes; merging it is what publishes.</p>"));
        loadRegistry();
      } else if (job.state === "approval") {
        /* A RUN WAITING FOR A PERSON IS NOT A FAILED RUN. The panel said
           "Acquisition failed" and pointed at a log that does not exist,
           because nothing had run. */
        stop();
        el("prog-title").textContent = "Waiting for approval on GitHub";
        el("prog-why").hidden = false;
        el("prog-why").textContent = job.failure || "";
      } else if (job.state === "cancelled") {
        stop();
        el("prog-title").textContent = "The run was cancelled";
        el("prog-why").hidden = false;
        el("prog-why").textContent = job.failure || "";
      } else if (job.state === "failed") {
        stop();
        el("prog-title").textContent = "Acquisition failed";
        el("prog-why").hidden = false;
        el("prog-why").textContent = job.failure || "The run failed.";
      }
    });
  }

  function stop() { if (POLL) { clearInterval(POLL); POLL = null; } }
  el("prog-close").addEventListener("click", function () {
    stop(); el("progress").close();
  });

  /* ── fill a country ───────────────────────────────────────────────
     ONE SITTING, ONE GRID, ONE PULL REQUEST. Filling a country one surface
     at a time is thirteen searches, thirteen dialogues and thirteen pull
     requests for what is one editorial decision.

     IT PROPOSES AND IT DOES NOT CHOOSE, and the difference is what the
     editor can see. `--pick 3` was wrong because a POSITION is not an
     identity: the photograph approved and the photograph that arrived could
     differ silently while every provenance field was correct about the wrong
     one. That cannot happen here — every tile shows its photograph, carries
     its own id, and the id on the tile is the id dispatched. NOTHING ARRIVES
     TICKED: "Select all" is a button somebody presses. */
  var SWEEP = { rows: [], ticked: {} };

  function swSlots() {
    var slotNames = Object.keys(REG.slots || {});
    if (!el("sw-slot").options.length) {
      el("sw-slot").innerHTML = slotNames.map(function (n) {
        return '<option value="' + esc(n) + '">' + esc(n) + "</option>";
      }).join("");
    }
    var countryOf = {};
    REG.purposes.forEach(function (p) {
      if (p.slot && p.country) (countryOf[p.slot] = countryOf[p.slot] || {})[p.country] = p.country_name;
    });
    var map = countryOf[el("sw-slot").value] || {};
    var ks = Object.keys(map).sort(function (a, b) {
      return map[a].localeCompare(map[b]);
    });
    /* A SLOT WITH NO COUNTRIES HIDES THE FIELD RATHER THAN OFFERING AN
       EMPTY ONE. Seventeen journeys, seventeen interests, nine macro
       regions, thirteen themes and eight categories are not per-country, and
       they are exactly the families small enough to fill in one sitting —
       so the button that fills a whole family must not be gated on a control
       that can never be satisfied. */
    var wrap = el("sw-country").parentNode;
    wrap.hidden = !ks.length;
    el("sw-country").innerHTML = ks.map(function (k) {
      return '<option value="' + esc(k) + '">' + esc(map[k]) + "</option>";
    }).join("");
    el("sw-note").textContent = ks.length ? ""
      : "This family is not per-country, so one sweep covers all of it.";
  }

  function sweep(e) {
    e.preventDefault();
    el("sw-grid").innerHTML = "";
    el("sw-bar").hidden = true;
    el("sw-note").textContent = "Searching once per empty surface…";
    SWEEP = { rows: [], ticked: {} };
    api("/api/sweep?provider=pexels&slot=" +
        encodeURIComponent(el("sw-slot").value) + "&country=" +
        encodeURIComponent(el("sw-country").value)).then(function (r) {
      if (!r.ok || r.j.error) {
        el("sw-note").textContent = (r.j && r.j.error) || "the sweep failed";
        return;
      }
      SWEEP.rows = r.j.rows;
      var withPhoto = r.j.rows.filter(function (x) { return x.candidate; }).length;
      el("sw-note").textContent =
        (r.j.note ? r.j.note + " " : "") +
        (r.j.rows.length
          ? r.j.swept + " empty surface" + (r.j.swept === 1 ? "" : "s") +
            " of " + r.j.surfaces + " searched, " + withPhoto +
            " with a photograph that meets the slot. " + r.j.order
          : "");
      if (r.j.stopped) el("sw-note").textContent += " " + r.j.stopped;
      drawSweep();
    });
  }

  function drawSweep() {
    el("sw-bar").hidden = !SWEEP.rows.length;
    el("sw-grid").innerHTML = SWEEP.rows.map(function (x) {
      if (!x.candidate) {
        return '<article class="swcell none"><h3>' + esc(x.query) +
          '</h3><p class="dims">Searched for &ldquo;' + esc(x.query) +
          '&rdquo;</p><p class="verdict no">No photograph offered &mdash; ' +
          esc(x.why_none) + ". Search for this one on its own with a " +
          "different wording.</p></article>";
      }
      var c = x.candidate;
      return '<article class="swcell" data-p="' + esc(x.purpose) + '">' +
        '<label class="swpick"><input type="checkbox" data-tick="' +
          esc(x.purpose) + '"><span>' + esc(x.query) + "</span></label>" +
        '<figure><img loading="lazy" alt="' +
          esc(c.alt || ("photograph " + c.id)) + '" src="/api/thumb?t=' +
          encodeURIComponent(c.thumb) + '"></figure>' +
        '<p class="by">' + esc(c.photographer) + " · Pexels · id " + esc(c.id) + "</p>" +
        '<p class="dims">' + c.width + " × " + c.height +
          (c.alternatives ? " · " + c.alternatives + " other candidates met this slot" : "") +
          "</p>" +
        '<label class="swalt"><span>What it shows</span>' +
        '<textarea data-alt="' + esc(x.purpose) + '" maxlength="240" rows="2">' +
          esc(c.alt) + "</textarea></label>" +
        (c.alt ? '<p class="hint">The photographer\u2019s own description. ' +
                 "Edit it if it is wrong.</p>"
               : '<p class="hint warnhint">This photograph carries no ' +
                 "description. Write one, or leave it unticked.</p>") +
        '<p class="acts"><a href="' + esc(c.page) +
          '" target="_blank" rel="noopener noreferrer">View on Pexels</a></p>' +
        "</article>";
    }).join("");
    el("sw-grid").querySelectorAll("[data-tick]").forEach(function (b) {
      b.addEventListener("change", function () {
        SWEEP.ticked[b.dataset.tick] = b.checked;
        countTicked();
      });
    });
    el("sw-grid").querySelectorAll("[data-alt]").forEach(function (t) {
      t.addEventListener("input", countTicked);
    });
    countTicked();
  }

  function tickAll(on) {
    el("sw-grid").querySelectorAll("[data-tick]").forEach(function (b) {
      b.checked = on;
      SWEEP.ticked[b.dataset.tick] = on;
    });
    countTicked();
  }

  /* A TICKED ROW WITH NO DESCRIPTION IS NOT ACQUIRABLE, and the count says
     so rather than the dispatch failing four screens later. */
  function ticked() {
    var out = [];
    el("sw-grid").querySelectorAll("[data-tick]").forEach(function (b) {
      if (!b.checked) return;
      var p = b.dataset.tick;
      var row = SWEEP.rows.filter(function (x) { return x.purpose === p; })[0];
      var ta = el("sw-grid").querySelector('[data-alt="' + p.replace(/"/g, '\\"') + '"]');
      out.push({ purpose: p, photo_id: row.candidate.id,
                 alt: (ta && ta.value || "").trim() });
    });
    return out;
  }

  function countTicked() {
    var t = ticked();
    var noAlt = t.filter(function (x) { return !x.alt; }).length;
    el("sw-count").textContent = t.length
      ? t.length + " ticked" + (noAlt ? ", " + noAlt + " with no description" : "")
      : "Nothing ticked.";
    el("sw-go").disabled = !t.length || !!noAlt;
    el("sw-go").textContent = t.length
      ? "Acquire " + t.length + " photograph" + (t.length === 1 ? "" : "s")
      : "Acquire";
  }

  function acquireTicked() {
    var t = ticked();
    if (!t.length) return;
    el("sw-go").disabled = true;
    api("/api/acquire", { method: "POST",
      body: JSON.stringify({ provider: "pexels", batch: t }) })
      .then(function (r) {
        el("sw-go").disabled = false;
        if (!r.ok) { alert(r.j.error || "could not start"); return; }
        watch(r.j.job);
      });
  }

  /* ── library ──────────────────────────────────────────────── */
  function fillLibrary() {
    var f = el("lib-filters");
    if (!f.dataset.wired) {
      f.dataset.wired = "1";
      f.addEventListener("input", fillLibrary);
      f.addEventListener("submit", function (e) { e.preventDefault(); });
    }
    var status = el("lib-status").value;
    var slot = el("lib-slot").value;
    var country = el("lib-country").value;
    var q = el("lib-q").value.trim().toLowerCase();
    var rows = REG.purposes.filter(function (p) {
      if (status && p.status !== status) return false;
      if (slot && (p.slot || p.purpose) !== slot) return false;
      if (country && p.country !== country) return false;
      if (q && (p.surface + " " + p.purpose).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    /* THE HEADLINE COUNT IS THE COUNT OF WHAT WAS ASKED FOR. Picking Norway
       and being told "0 of 593 slots hold a photograph" answers a question
       nobody asked — a number that is not the set's own extent reads as one,
       which is the failure /europe-in already records. With a country chosen
       the denominator is that country's. */
    var scope = country
      ? REG.purposes.filter(function (p) { return p.country === country; })
      : REG.purposes;
    var scopeName = country
      ? (scope.length && scope[0].country_name) || country
      : "";
    var filled = scope.filter(function (p) { return p.status === "PUBLISHED"; }).length;
    /* THE COUNT SAYS WHAT IS ON THE SCREEN. The first version said
       "Showing 593" while listing 60 — a number that is not the set's own
       extent reads as one. */
    var head = rows.filter(function (p) { return p.status === "PUBLISHED"; });
    var tail = rows.filter(function (p) { return p.status !== "PUBLISHED"; });
    var showing = head.concat(tail.slice(0, 60));
    el("lib-count").innerHTML = "<b>" + filled + "</b> of <b>" +
      scope.length + "</b> " + (scopeName ? esc(scopeName) + " " : "") +
      "slots hold a photograph. " +
      (rows.length === showing.length
        ? "Listing all " + rows.length + " that match."
        : "Matching " + rows.length + ", listing " + showing.length + ".");
    el("lib").innerHTML = showing.map(function (p) {
      var spec = specOf(p);
      /* AN EMPTY ROW IS AN OPENING, AND AN OPENING SHOULD BE A DOOR. The
         library listed 593 slots and every one was a dead end: you read that
         /countries has no photograph and then went to the other tab and
         retyped it. A filled row stays a record — there is nothing to go and
         do about a surface that already holds one. */
      var open = p.status !== "PUBLISHED";
      var tag = open ? "button" : "div";
      var attrs = open ? ' type="button" class="slotrow open" data-go="' +
        esc(p.purpose) + '"' : ' class="slotrow"';
      return "<" + tag + attrs + '><span class="pill ' + p.status + '">' +
        p.status + "</span><div><h3>" + esc(p.surface) + '</h3><p class="where">' +
        esc(p.purpose) + " · " + esc(p.path) + "</p></div>" +
        '<p class="meta">' + (p.photograph
          ? esc(p.photograph.photographer) + "<br>" +
            esc((p.photograph.sha256 || "").slice(0, 16))
          : spec.min_width + "px · " + spec.min_aspect + "–" + spec.max_aspect +
            '<br><span class="findit">Find one →</span>') +
        "</p></" + tag + ">";
    }).join("") + (tail.length > 60
      ? '<p class="hint">' + (tail.length - 60) + " more empty slots not listed.</p>"
      : "");
    el("lib").querySelectorAll("[data-go]").forEach(function (b) {
      b.addEventListener("click", function () { goFind(b.dataset.go); });
    });
  }

  /* Take the reader to the search with this surface already chosen. Setting
     the fields and leaving them on a hidden tab would be the `for=` failure
     in another costume: correct, and invisible. */
  function goFind(purpose) {
    var row = REG.purposes.filter(function (p) { return p.purpose === purpose; })[0];
    if (!row) return;
    show_view("find");
    el("slot").value = row.slot || row.purpose;
    onSlot();
    if (row.country) { el("country").value = row.country; onSlot(true); }
    if (row.slot) setTarget(row);
    el("q").value = placeName(row);
    el("q").focus();
    el("q").select();
  }

  function fillProvenance() {
    var filled = REG.purposes.filter(function (p) { return p.photograph; });
    if (!filled.length) {
      el("prov").innerHTML = '<p class="lede">The register holds no ' +
        "photographs. That is a true statement about this product, and a " +
        "register with a placeholder row in it would not be.</p>";
      return;
    }
    el("prov").innerHTML = filled.map(function (p) {
      var r = p.photograph;
      return "<dl>" + Object.keys(r).sort().map(function (k) {
        return "<dt>" + esc(k) + "</dt><dd>" + esc(
          typeof r[k] === "object" ? JSON.stringify(r[k]) : r[k]) + "</dd>";
      }).join("") + "</dl>";
    }).join("");
  }

  /* ── the basket ───────────────────────────────────────────────────
     ONE SITTING'S WORKING SET, HELD IN THIS BROWSER.

     The desk existed as two one-shot paths: find one photograph and approve
     it, or sweep a country and approve that grid. Both end in a dispatch, so
     the only way to exploit the whole library was to make a decision every
     few minutes and get a pull request for each. The basket is the missing
     middle — look at everything, keep what is right, approve once.

     WHY IT IS IN THE BROWSER. This desk holds no state anywhere: two
     serverless invocations share no memory, which is why a session and a
     preview token are signed values rather than dictionary entries. A basket
     on the server would be the first stored thing in the product and it
     would be shared by everyone who signs in with the one passcode, with no
     notion of whose it is. One editor's working set, in one editor's
     browser, and the interface says so rather than implying a queue.

     AND IT STORES ONLY WHAT CANNOT BE DERIVED. The surface sentence, the
     slot's requirements and whether that surface is already filled all come
     from the registry on every render — the same rule that keeps a country
     off a register row, because a stored copy is a copy that goes stale. */
  var BKEY = "europedoor.desk.basket.v1";
  var BASKET = [];
  var BSTORE = true;

  function basketLoad() {
    try {
      var raw = window.localStorage.getItem(BKEY);
      BASKET = raw ? JSON.parse(raw) : [];
      if (!Array.isArray(BASKET)) BASKET = [];
    } catch (e) {
      /* A PRIVATE WINDOW OR BLOCKED SITE DATA THROWS, and a basket that
         cannot persist still works for the sitting it is open. What must not
         happen is the editor finding out at the end. */
      BASKET = [];
      BSTORE = false;
    }
  }

  function basketSave() {
    try { window.localStorage.setItem(BKEY, JSON.stringify(BASKET)); }
    catch (e) { BSTORE = false; }
  }

  function basketBadge() {
    var live = BASKET.filter(function (x) { return !x.sent; }).length;
    var b = el("basket-n");
    b.hidden = !BASKET.length;
    b.textContent = String(live || BASKET.length);
  }

  /* A SURFACE HOLDS ONE PHOTOGRAPH, so the basket is keyed on the purpose.
     The register refuses a second row for a purpose at the far end; a basket
     that can hold a pair the dispatch will reject wastes the sitting it
     exists to collect. Replacing says so out loud, because silently
     dropping the first pick is the desk deciding. */
  function basketAdd(purpose, c) {
    var had = BASKET.filter(function (x) { return x.purpose === purpose; })[0];
    BASKET = BASKET.filter(function (x) { return x.purpose !== purpose; });
    BASKET.push({
      purpose: purpose, photo_id: c.id, alt: c.alt || "",
      photographer: c.photographer, width: c.width, height: c.height,
      page: c.page, thumb: c.thumb, added: Date.now(), sent: 0,
    });
    basketSave();
    basketBadge();
    if (BASKET.length) basketDraw();
    return had
      ? "Replaced " + had.photo_id + " — a surface holds one photograph."
      : "In the basket.";
  }

  function basketDrop(purpose) {
    BASKET = BASKET.filter(function (x) { return x.purpose !== purpose; });
    basketSave();
    basketBadge();
    basketDraw();
  }

  function basketRow(purpose) {
    return REG.purposes.filter(function (p) { return p.purpose === purpose; })[0];
  }

  /* A BASKET ENTRY CAN GO STALE IN TWO WAYS AND ONLY ONE OF THEM MATTERS.
     The preview token dies with the session and the photograph's identity
     does not, so an expired thumbnail is a missing picture and never a
     missing entry — the workflow fetches BY ID and the id is still exactly
     right. What does disqualify one is the surface being filled while the
     basket sat there, which the registry answers on every render. */
  function basketState(x) {
    var p = basketRow(x.purpose);
    if (!p) return { ok: false, why: "this surface is no longer in the registry" };
    if (p.status === "PUBLISHED") {
      return { ok: false, why: "filled since you added it — remove this one" };
    }
    if (x.sent) return { ok: false, why: "sent to a run at " + hhmm(x.sent) };
    if (!String(x.alt || "").trim()) return { ok: false, why: "needs a description" };
    return { ok: true, why: "" };
  }

  function hhmm(ms) {
    var d = new Date(ms);
    return ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2);
  }

  function basketDraw() {
    var live = BASKET.filter(function (x) { return !x.sent; });
    el("bk-bar").hidden = !BASKET.length;
    if (!BASKET.length) {
      el("bk-note").innerHTML = "The basket is empty. Search or sweep, and "
        + "put candidates in here as you go — it keeps what you picked while "
        + "you carry on looking, and you approve the whole set once.";
      el("bk-grid").innerHTML = "";
      return;
    }
    var ready = BASKET.filter(function (x) { return basketState(x).ok; }).length;
    var sent = BASKET.length - live.length;
    el("bk-sent").hidden = !sent;
    el("bk-sent").textContent = "Clear " + sent + " sent";
    el("bk-note").innerHTML =
      "<b>" + BASKET.length + "</b> in the basket, <b>" + ready +
      "</b> ready to acquire" +
      (BASKET.length - live.length
        ? ", " + (BASKET.length - live.length) + " already sent to a run"
        : "") + ". " +
      (BSTORE
        ? "This basket is held in this browser only. Nobody else signed in "
          + "sees it, and clearing site data clears it."
        : "<b>This browser is refusing to store it</b>, so it will not "
          + "survive a reload. Acquire before you leave the page.") +
      " " + BK_CAP + " is what one pull request carries.";

    el("bk-grid").innerHTML = BASKET.map(function (x) {
      var p = basketRow(x.purpose);
      var st = basketState(x);
      return '<article class="swcell' + (x.sent ? " gone" : "") +
        '" data-p="' + esc(x.purpose) + '">' +
        '<label class="swpick"><input type="checkbox" data-btick="' +
          esc(x.purpose) + '"' + (st.ok ? "" : " disabled") + '><span>' +
          esc(p ? p.surface : x.purpose) + "</span></label>" +
        /* A DEAD PREVIEW IS A MISSING PICTURE AND NEVER A MISSING ENTRY.
           `onerror` swaps in a note rather than leaving a broken frame,
           because the entry is still perfectly acquirable. */
        '<figure><img loading="lazy" alt="' +
          esc(x.alt || ("photograph " + x.photo_id)) + '" src="/api/thumb?t=' +
          encodeURIComponent(x.thumb) + '" data-dead="' + esc(x.purpose) +
          '"></figure>' +
        '<p class="by">' + esc(x.photographer) + " · Pexels · id " +
          esc(x.photo_id) + "</p>" +
        '<p class="dims">' + x.width + " × " + x.height + " · added " +
          hhmm(x.added) + "</p>" +
        '<label class="swalt"><span>What it shows</span>' +
        '<textarea data-balt="' + esc(x.purpose) + '" maxlength="240" rows="2"' +
          (x.sent ? " readonly" : "") + ">" + esc(x.alt) + "</textarea></label>" +
        (st.ok
          ? '<p class="hint">The photographer’s own description. Edit it '
            + "if it is wrong.</p>"
          : '<p class="verdict no">' + esc(st.why) + "</p>") +
        '<p class="acts"><a href="' + esc(x.page) +
          '" target="_blank" rel="noopener noreferrer">View on Pexels</a>' +
        '<button type="button" class="quiet" data-bdrop="' + esc(x.purpose) +
          '">Remove</button></p>' +
        "</article>";
    }).join("");

    el("bk-grid").querySelectorAll("[data-dead]").forEach(function (img) {
      img.addEventListener("error", function () {
        img.parentNode.innerHTML = '<p class="expired">The preview expired '
          + "with your last session. The photograph is unchanged — it is "
          + "fetched by id, and the id is still right.</p>";
      });
    });
    el("bk-grid").querySelectorAll("[data-btick]").forEach(function (b) {
      b.addEventListener("change", basketCount);
    });
    el("bk-grid").querySelectorAll("[data-balt]").forEach(function (t) {
      t.addEventListener("input", function () {
        var e2 = BASKET.filter(function (x) { return x.purpose === t.dataset.balt; })[0];
        if (e2) { e2.alt = t.value; basketSave(); }
        basketCount();
      });
    });
    el("bk-grid").querySelectorAll("[data-bdrop]").forEach(function (b) {
      b.addEventListener("click", function () { basketDrop(b.dataset.bdrop); });
    });
    basketCount();
  }

  function basketTicked() {
    var out = [];
    el("bk-grid").querySelectorAll("[data-btick]").forEach(function (b) {
      if (!b.checked || b.disabled) return;
      var x = BASKET.filter(function (y) { return y.purpose === b.dataset.btick; })[0];
      if (x) out.push(x);
    });
    return out;
  }

  function basketCount() {
    var t = basketTicked();
    var over = t.length > BK_CAP;
    el("bk-count").textContent = t.length
      ? t.length + " ticked" + (over
          ? " — the first " + BK_CAP + " will go, the rest stay in the basket"
          : "")
      : "Nothing ticked.";
    el("bk-go").disabled = !t.length;
    var n = Math.min(t.length, BK_CAP);
    el("bk-go").textContent = t.length
      ? "Acquire " + n + " photograph" + (n === 1 ? "" : "s")
      : "Acquire";
  }

  function basketAcquire() {
    var t = basketTicked().slice(0, BK_CAP);
    if (!t.length) return;
    el("bk-go").disabled = true;
    api("/api/acquire", { method: "POST",
      body: JSON.stringify({ provider: "pexels",
        batch: t.map(function (x) {
          return { purpose: x.purpose, photo_id: x.photo_id,
                   alt: String(x.alt || "").trim() };
        }) }) })
      .then(function (r) {
        el("bk-go").disabled = false;
        if (!r.ok) { alert(r.j.error || "could not start"); return; }
        /* A DISPATCH IS NOT A MERGE, so a sent entry is not a finished one.
           Removing it here would say the work is done at the exact moment
           the question is being asked — and if the run goes red the editor
           would have to find every photograph again. It is marked instead,
           greyed, untickable, and cleared by hand once the pull request is
           merged. */
        var now = Date.now();
        t.forEach(function (x) { x.sent = now; });
        basketSave();
        basketBadge();
        basketDraw();
        watch(r.j.job);
      });
  }

  el("bk-all").addEventListener("click", function () {
    el("bk-grid").querySelectorAll("[data-btick]").forEach(function (b) {
      if (!b.disabled) b.checked = true;
    });
    basketCount();
  });
  el("bk-none").addEventListener("click", function () {
    el("bk-grid").querySelectorAll("[data-btick]").forEach(function (b) {
      b.checked = false;
    });
    basketCount();
  });
  el("bk-drop").addEventListener("click", function () {
    var gone = {};
    el("bk-grid").querySelectorAll("[data-btick]").forEach(function (b) {
      if (b.checked) gone[b.dataset.btick] = 1;
    });
    BASKET = BASKET.filter(function (x) { return !gone[x.purpose]; });
    basketSave();
    basketBadge();
    basketDraw();
  });
  el("bk-sent").addEventListener("click", function () {
    BASKET = BASKET.filter(function (x) { return !x.sent; });
    basketSave();
    basketBadge();
    basketDraw();
  });
  el("bk-go").addEventListener("click", basketAcquire);

  /* ADD TICKED FROM A SWEEP. The sweep already asks the right question of a
     whole country; what it could not do was let the answer wait. */
  el("sw-bag").addEventListener("click", function () {
    var t = ticked();
    t.forEach(function (row) {
      var x = SWEEP.rows.filter(function (y) { return y.purpose === row.purpose; })[0];
      if (x && x.candidate) {
        basketAdd(row.purpose, Object.assign({}, x.candidate, { alt: row.alt }));
      }
    });
    el("sw-count").textContent = t.length
      ? t.length + " added to the basket."
      : "Nothing ticked.";
  });

  /* ── fill the library ─────────────────────────────────────────────
     ONE PRESS, EVERY CATEGORY, THE NEXT TRANCHE — and it is one press
     rather than two because that is what was asked for. Find asks which
     surface and Fill a country asks which country; this asks nothing, so it
     is the thing an editor meets on the way in.

     IT STILL GOES THROUGH THE BASKET. Not as a step to click past — the
     dispatch follows immediately — but because the basket is the record of
     what went out, and a set that publishes without leaving a trace of what
     it chose is a set nobody can audit afterwards. Every row lands there,
     is marked sent, and keeps its photograph, its id, its photographer and
     its description.

     AND IT SAYS WHAT IT WILL DO BEFORE IT DOES IT. "One click" is a promise
     about effort, never about surprise: the band states how many surfaces
     are empty, how many this press takes, and that a green run now merges
     itself. */
  function topupState() {
    if (!REG.purposes.length) return;
    var empty = REG.purposes.filter(function (p) {
      return p.status !== "PUBLISHED";
    }).length;
    var filled = REG.purposes.length - empty;
    el("topup").hidden = false;
    el("topup-go").disabled = !empty;
    if (!empty) {
      el("topup-head").textContent = "The library is full";
      el("topup-note").textContent = "All " + REG.purposes.length +
        " surfaces this product declares hold a photograph.";
      el("topup-fine").textContent = "";
      el("topup-go").textContent = "Nothing left to fill";
      return;
    }
    var take = Math.min(empty, BK_CAP);
    el("topup-head").textContent = "Fill the library";
    el("topup-note").innerHTML = "<b>" + filled + "</b> of <b>" +
      REG.purposes.length + "</b> surfaces hold a photograph. This takes the " +
      "next <b>" + take + "</b> — one from each family in turn, so a press " +
      "fills every category rather than one country. Press it again for more.";
    el("topup-fine").textContent =
      "It takes the provider's own first result for each surface that meets " +
      "the slot and carries the photographer's own description; nothing is " +
      "ranked and nothing here has looked at the pictures. A green run " +
      "merges itself, so these reach europedoor.com on the next deployment. " +
      "Every one lands in the basket, so you can see afterwards what went.";
    el("topup-go").textContent = "Fill the next " + take;
  }

  function topup() {
    var btn = el("topup-go");
    btn.disabled = true;
    btn.textContent = "Looking…";
    api("/api/topup?provider=pexels&n=" + BK_CAP).then(function (r) {
      if (!r.ok || (r.j && r.j.error)) {
        topupState();
        el("topup-note").textContent = (r.j && r.j.error) || "the search failed";
        return;
      }
      var rows = r.j.rows || [];
      if (!rows.length) {
        topupState();
        el("topup-note").textContent = r.j.note || r.j.stopped
          || "Nothing this provider returned for the empty surfaces met "
           + "their slots. Try the search, where you can change the wording.";
        return;
      }
      rows.forEach(function (x) { basketAdd(x.purpose, x.candidate); });
      show_view("basket");
      /* THE DISPATCH IS THE SAME ONE EVERY OTHER PATH USES. A second way to
         acquire would be a second set of refusals to disagree with the
         first, which this repository has paid for five times. */
      api("/api/acquire", { method: "POST",
        body: JSON.stringify({ provider: "pexels",
          batch: rows.map(function (x) {
            return { purpose: x.purpose, photo_id: x.candidate.id,
                     alt: String(x.candidate.alt || "").trim() };
          }) }) })
        .then(function (a) {
          topupState();
          if (!a.ok) { alert(a.j.error || "could not start"); return; }
          var now = Date.now();
          rows.forEach(function (x) {
            var e2 = BASKET.filter(function (y) {
              return y.purpose === x.purpose; })[0];
            if (e2) e2.sent = now;
          });
          basketSave();
          basketBadge();
          basketDraw();
          watch(a.j.job);
        });
    });
  }

  el("topup-go").addEventListener("click", topup);

  /* ── views ────────────────────────────────────────────────── */
  var VIEWS = ["find", "sweep", "basket", "library", "provenance"];

  function show_view(name) {
    document.querySelectorAll(".area").forEach(function (x) {
      x.classList.toggle("on", x.dataset.view === name);
    });
    VIEWS.forEach(function (v) { el("view-" + v).hidden = v !== name; });
    if (name === "sweep") swSlots();
    if (name === "basket") basketDraw();
    window.scrollTo(0, 0);
  }

  document.querySelectorAll(".area").forEach(function (b) {
    b.addEventListener("click", function () { show_view(b.dataset.view); });
  });

  api("/api/session").then(function (r) { show(!!(r.j && r.j.signed_in)); });
})();
