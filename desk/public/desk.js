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
    if (signedIn) loadRegistry();
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
      fillSlots();
      fillLibrary();
      fillProvenance();
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
    if (!sel.dataset.wired) { sel.dataset.wired = "1";
      sel.addEventListener("change", onSlot); }
    onSlot();
  }

  function instancesOf(slot) {
    return REG.purposes.filter(function (p) { return p.slot === slot; });
  }

  function onSlot() {
    var v = el("slot").value;
    var rows = instancesOf(v);
    var isSlot = rows.length > 0;
    el("target-wrap").hidden = !isSlot;
    el("target").required = isSlot;
    if (isSlot) {
      el("targets").innerHTML = rows.slice(0, 2000).map(function (p) {
        return '<option value="' + esc(p.target) + '">' + esc(p.surface) + "</option>";
      }).join("");
      el("target").value = "";
    }
    var spec = specOf(isSlot ? rows[0] : REG.purposes.filter(function (p) {
      return p.purpose === v;
    })[0]);
    showBrief(spec);
    showNeeds(spec);
  }

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
          (c.suits && !c.already.length
            ? '<button type="button" class="go" data-id="' + esc(c.id) + '">Acquire</button>'
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
    el("acquire").showModal();
    el("alt").focus();
  }

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
        el("prog-title").textContent = "Acquired, and waiting for you";
        /* THE WORD IS NOT "PUBLISHED", AND THAT IS THE WHOLE BOUNDARY. The
           photograph is in a branch behind a pull request; europedoor.com is
           unchanged until somebody merges it. A desk that said "published"
           would be reporting the reviewer's decision for them. */
        el("prog-steps").insertAdjacentHTML("beforeend",
          (job.pr
            ? '<a class="prlink" href="' + esc(job.pr) + '" target="_blank" ' +
              'rel="noopener noreferrer">Review pull request #' +
              esc(job.pr_number) + "</a>"
            : '<p class="notyet">The branch is <span class="branch">' +
              esc(job.branch) + "</span>.</p>") +
          '<p class="notyet">Nothing on europedoor.com has changed. The pull ' +
          "request carries the rendered page, the provenance row and both " +
          "hashes; merging it is what publishes.</p>");
        loadRegistry();
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
    var q = el("lib-q").value.trim().toLowerCase();
    var rows = REG.purposes.filter(function (p) {
      if (status && p.status !== status) return false;
      if (slot && (p.slot || p.purpose) !== slot) return false;
      if (q && (p.surface + " " + p.purpose).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    var filled = REG.purposes.filter(function (p) { return p.status === "PUBLISHED"; }).length;
    /* THE COUNT SAYS WHAT IS ON THE SCREEN. The first version said
       "Showing 593" while listing 60 — a number that is not the set's own
       extent reads as one. */
    var head = rows.filter(function (p) { return p.status === "PUBLISHED"; });
    var tail = rows.filter(function (p) { return p.status !== "PUBLISHED"; });
    var showing = head.concat(tail.slice(0, 60));
    el("lib-count").innerHTML = "<b>" + filled + "</b> of <b>" +
      REG.purposes.length + "</b> slots hold a photograph. " +
      (rows.length === showing.length
        ? "Listing all " + rows.length + " that match."
        : "Matching " + rows.length + ", listing " + showing.length + ".");
    el("lib").innerHTML = showing.map(function (p) {
      var spec = specOf(p);
      return '<div class="slotrow"><span class="pill ' + p.status + '">' +
        p.status + "</span><div><h3>" + esc(p.surface) + '</h3><p class="where">' +
        esc(p.purpose) + " · " + esc(p.path) + "</p></div>" +
        '<p class="meta">' + (p.photograph
          ? esc(p.photograph.photographer) + "<br>" +
            esc((p.photograph.sha256 || "").slice(0, 16))
          : spec.min_width + "px · " + spec.min_aspect + "–" + spec.max_aspect) +
        "</p></div>";
    }).join("") + (tail.length > 60
      ? '<p class="hint">' + (tail.length - 60) + " more empty slots not listed.</p>"
      : "");
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

  /* ── views ────────────────────────────────────────────────── */
  document.querySelectorAll(".area").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll(".area").forEach(function (x) {
        x.classList.toggle("on", x === b);
      });
      ["find", "library", "provenance"].forEach(function (v) {
        el("view-" + v).hidden = v !== b.dataset.view;
      });
    });
  });

  api("/api/session").then(function (r) { show(!!(r.j && r.j.signed_in)); });
})();
