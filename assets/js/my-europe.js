/* My Europe — saved places, in this browser only.
 *
 * localStorage and nothing else. No account, no request, no identifier. It
 * can come back empty (private window, cleared data, a different device) and
 * the page has to be correct when it does, so every read is guarded and the
 * empty state is a real state rather than a spinner. */
(function () {
  "use strict";
  var KEY = "europedoor.saved.v1";

  function read() {
    try {
      var raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  }
  function write(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); return true; }
    catch (e) { return false; }
  }

  /* A destination page carries the same save action twice — once in the rail
   * and once in the sticky bar a phone shows — so relabelling only the
   * button that was pressed leaves the other one saying "Save" for something
   * already saved. Every button for an id is relabelled together.
   *
   * data-short lets the compact one say "Save" / "Saved ✓" without the
   * full wording, which does not fit a thumb bar. */
  function label(btn, saved) {
    if (btn.hasAttribute("data-short")) {
      btn.textContent = saved ? "Saved ✓" : "Save";
    } else {
      btn.textContent = saved ? "Saved to My Europe ✓" : "Save to My Europe";
    }
    btn.setAttribute("aria-pressed", saved ? "true" : "false");
  }

  function labelAll(id, saved) {
    document.querySelectorAll('[data-save="' + id.replace(/"/g, '\\"') + '"]')
      .forEach(function (b) { label(b, saved); });
  }

  document.querySelectorAll("[data-save]").forEach(function (btn) {
    var id = btn.getAttribute("data-save");
    var list = read();
    label(btn, list.some(function (x) { return x.id === id; }));
    btn.addEventListener("click", function () {
      var current = read();
      var at = current.findIndex(function (x) { return x.id === id; });
      if (at >= 0) current.splice(at, 1);
      else current.push({ id: id, kind: btn.getAttribute("data-kind") || "Place",
                          label: btn.getAttribute("data-label"),
                          url: btn.getAttribute("data-url") });
      if (!write(current)) {
        btn.textContent = "This browser will not let us save";
        return;
      }
      labelAll(id, at < 0);
    });
  });

  /* ── Travel DNA ──────────────────────────────────────────────────
   *
   * A travel PREFERENCE model, computed from what this browser has saved.
   * The brief is explicit that it must never be presented as psychological
   * truth, and that matters more than it sounds: a bar chart of percentages
   * with a person's name over it reads as a personality test whatever the
   * caption says. So:
   *
   *   * it says what it is computed from, in numbers — "from the 7 places
   *     you have saved" — because a profile with no denominator is a claim;
   *   * it will not appear at all under four saved places, since three
   *     saves is noise wearing a percentage sign;
   *   * every dimension is adjustable and the whole thing is resettable,
   *     because a model of you that you cannot correct is a model that is
   *     being done to you;
   *   * it never leaves the browser. There is no account here and no
   *     request; the profile is derived on the page every time it is shown
   *     and stored nowhere except your own adjustments.
   *
   * And it is useful, which is the test of whether it should exist: it
   * hands its top interests to the Planner and to Discover Mode.
   */
  var DNA_KEY = "europedoor.dna.v1";
  var DNA_MIN = 4;

  function dnaAdjust() {
    try { return JSON.parse(localStorage.getItem(DNA_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function dnaSave(a) {
    try { localStorage.setItem(DNA_KEY, JSON.stringify(a)); return true; }
    catch (e) { return false; }
  }

  function buildDna(atlas, saved) {
    var byId = {};
    for (var i = 0; i < atlas.cities.length; i++) byId[atlas.cities[i].id] = atlas.cities[i];

    // A saved place resolves to the destination it is in, because interests
    // live on the destination. A journey or a story is not counted: it says
    // what somebody curated, not what this reader chose.
    var counted = 0, tally = {};
    saved.forEach(function (x) {
      var m = /^(?:city|place):([^/]+\/[^/]+\/[^/]+)/.exec(x.id || "");
      if (!m) return;
      var c = byId[m[1]];
      if (!c) return;
      counted++;
      c.interests.forEach(function (t) { tally[t] = (tally[t] || 0) + 1; });
    });
    if (counted < DNA_MIN) return { counted: counted, rows: [] };

    var adj = dnaAdjust();
    var rows = atlas.interests.map(function (i) {
      var share = Math.round(((tally[i.slug] || 0) / counted) * 100);
      var moved = adj[i.slug];
      return {
        slug: i.slug, name: i.name, icon: i.icon,
        raw: share,
        value: Math.max(0, Math.min(100, moved === undefined ? share : moved)),
        adjusted: moved !== undefined,
      };
    }).filter(function (r) { return r.value > 0 || r.adjusted; });
    rows.sort(function (a, b) { return b.value - a.value; });
    return { counted: counted, rows: rows };
  }

  function renderDna(host, atlas, saved) {
    var dna = buildDna(atlas, saved);
    if (!dna.rows.length) {
      host.innerHTML = '<div class="note"><h2 class="mini">Your travel profile</h2>' +
        "<p>Save at least " + DNA_MIN + " places and this will show what you keep choosing. " +
        "You have " + dna.counted + " so far. Fewer than " + DNA_MIN +
        " is noise wearing a percentage sign, so there is nothing here worth showing yet.</p></div>";
      return;
    }
    var top = dna.rows.slice(0, 6);
    host.innerHTML =
      '<div class="note dna"><h2 class="mini">Your travel profile</h2>' +
      "<p>Computed from the <strong>" + dna.counted + " places</strong> you have saved in " +
      "this browser, and from nothing else. It is a record of what you keep choosing — " +
      "<strong>not a personality test</strong>, not a judgement, and not something we hold: " +
      "it is derived on this page every time you open it.</p>" +
      '<div class="dnarows">' + top.map(function (r) {
        return '<div class="dnarow"><span class="dnalabel">' +
          '<span aria-hidden="true">' + r.icon + "</span> " + r.name +
          (r.adjusted ? ' <span class="small">(adjusted)</span>' : "") + "</span>" +
          '<span class="scorebar"><span class="w' + r.value + '"></span></span>' +
          '<span class="scorenum">' + r.value + "</span>" +
          '<span class="dnanudge">' +
          '<button type="button" class="linkish" data-dna="' + r.slug + '" data-by="-10"' +
          ' aria-label="Less ' + r.name + '">−</button>' +
          '<button type="button" class="linkish" data-dna="' + r.slug + '" data-by="10"' +
          ' aria-label="More ' + r.name + '">+</button></span></div>';
      }).join("") + "</div>" +
      '<div class="hero-actions mt0">' +
      '<a class="btn" href="/plan?i=' + top.slice(0, 4).map(function (r) { return r.slug; }).join(",") +
      '">Plan a journey from this</a>' +
      '<a class="btn ghost" href="/discover">Explore with it</a>' +
      '<button class="btn ghost" type="button" id="dnareset">Reset the profile</button>' +
      "</div>" +
      '<p class="small">Adjusting a row overrides what your saves say, and reset removes every ' +
      "override. Nothing here is sent anywhere — <a href=\"/privacy\">how to check that</a>.</p>" +
      "</div>";

    host.querySelectorAll("[data-dna]").forEach(function (b) {
      b.addEventListener("click", function () {
        var slug = b.getAttribute("data-dna");
        var by = Number(b.getAttribute("data-by"));
        var adj = dnaAdjust();
        var row = dna.rows.filter(function (r) { return r.slug === slug; })[0];
        adj[slug] = Math.max(0, Math.min(100, (row ? row.value : 0) + by));
        if (dnaSave(adj)) renderDna(host, atlas, saved);
      });
    });
    var reset = host.querySelector("#dnareset");
    if (reset) {
      reset.addEventListener("click", function () {
        if (dnaSave({})) renderDna(host, atlas, saved);
      });
    }
  }

  var mine = document.getElementById("mine");
  if (!mine) return;
  var list = read();
  if (!list.length) {
    /* AN EMPTY STATE IS A PAGE, AND THIS ONE WAS A GREY BOX AND 250 PIXELS
     * OF NOTHING. It is also the FIRST thing every reader sees here — the
     * list is empty until they save something — so it is the state this page
     * ships in, not a fallback, and it was the only surface on the site that
     * explained what to do without offering a way to do it.
     *
     * It carries three ways in now. They are the site's own top-level
     * surfaces rather than a curated pick, because choosing three
     * destinations to suggest would be a ranking this Atlas does not hold.
     *
     * AND THE ONE LINK IT DID HAVE WAS DEAD. `/atlas` has never been a route
     * here; the country index is `/countries`. It survived because it lives
     * in a string in a script that only runs when nothing is saved, so the
     * link checker — which reads shipped HTML — could not see it. A code
     * path nothing exercises is a code path nothing checks. */
    mine.innerHTML = '<div class="startstate">' +
      '<h2>Nothing saved yet.</h2>' +
      '<p>Open any destination and press <em>Save to My Europe</em>. If you have saved ' +
      'things before and this is empty, you are in a different browser or the site data ' +
      'was cleared — there is no copy anywhere else, which is the point.</p>' +
      '<div class="emptyways">' +
      '<a href="/countries"><b>Countries</b><span>Fifty, and the regions inside them</span></a>' +
      '<a href="/discover"><b>Discover mode</b><span>Say what you travel for</span></a>' +
      '<a href="/journeys"><b>Journeys</b><span>Routes already worked out</span></a>' +
      '</div></div>';
    return;
  }
  /* Collections — the specification's bucket lists. A saved item carries a
   * list name or nothing; "Everything else" is the absence of one rather
   * than a real collection, so nobody has to create one to save something.
   * All of it is still this browser's localStorage and nothing else. */
  var COLL_KEY = "europedoor.collections.v1";
  function readColls() {
    try { return JSON.parse(localStorage.getItem(COLL_KEY) || "[]"); } catch (e) { return []; }
  }
  function writeColls(c) {
    try { localStorage.setItem(COLL_KEY, JSON.stringify(c)); return true; } catch (e) { return false; }
  }
  var colls = readColls();

  var ORDER = ["Itinerary", "Place", "Journey", "Theme", "Story"];

  function rowHtml(x, i) {
    var opts = ['<option value="">Everything else</option>'].concat(
      colls.map(function (c) {
        return '<option value="' + esc(c) + '"' + (x.list === c ? " selected" : "") + ">" +
          esc(c) + "</option>";
      })
    ).join("");
    return '<div class="row saved"><div><h3><a href="' + x.url + '">' + esc(x.label) + "</a></h3>" +
      '<p class="rowsub">' + esc(x.kind || "Place") + "</p></div>" +
      '<p class="rowmeta"><label class="visually-hidden" for="coll' + i + '">Collection for ' +
      esc(x.label) + "</label>" +
      '<select id="coll' + i + '" data-move="' + i + '">' + opts + "</select> " +
      '<button type="button" class="linkish" data-drop="' + i + '">remove</button></p></div>';
  }

  function esc(x) {
    return String(x).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function render() {
    var html = "<h2>" + list.length + (list.length === 1 ? " saved item" : " saved items") +
      (colls.length ? " in " + colls.length + (colls.length === 1 ? " collection" : " collections") : "") +
      "</h2>";

    html += '<form class="form" id="newcoll"><div class="field">' +
      '<label for="collname">Start a collection</label>' +
      '<input type="text" id="collname" placeholder="My European Summer" autocomplete="off">' +
      "</div><div class=\"hero-actions mt0\">" +
      '<button class="btn ghost" type="submit">Create it</button></div></form>';

    var buckets = {};
    list.forEach(function (x, i) { (buckets[x.list || ""] = buckets[x.list || ""] || []).push([x, i]); });
    var names = colls.slice();
    if (buckets[""]) names.push("");
    names.forEach(function (name) {
      var items = buckets[name] || [];
      html += "<h3>" + esc(name || "Everything else") + " <span class=\"small\">" +
        items.length + "</span></h3>";
      if (!items.length) {
        html += '<p class="small">Nothing in this one yet — move something into it below.</p>';
        return;
      }
      items.sort(function (a, b) {
        return ORDER.indexOf(a[0].kind || "Place") - ORDER.indexOf(b[0].kind || "Place");
      });
      html += '<div class="rows">' + items.map(function (pair) {
        return rowHtml(pair[0], pair[1]);
      }).join("") + "</div>";
    });

    /* Move it to another browser, without an account.
     *
     * The specification wants a saved journey to follow a traveller between
     * devices, and files that under "needs authentication". It needs
     * authentication only if the copy has to happen on our side. This is the
     * same list as text: it moves between browsers, survives clearing site
     * data, and can be kept as a file — while we still hold nothing, know
     * nothing, and cannot lose it on anyone's behalf.
     *
     * A textarea rather than a download, because a downloaded file is the
     * one part of this a sandboxed browser can refuse and then the button
     * simply does nothing. Text always copies. */
    html += '<h3 class="mt7">Move this to another browser</h3>' +
      '<p class="small">There is no account here, so nothing syncs on its own. This is your ' +
      'saved list as text: copy it, paste it into the same box on another device, and ' +
      'the list arrives. Keep a copy somewhere and it survives clearing this browser too — ' +
      'which is the part an account would normally be doing for you.</p>' +
      '<form class="form" id="transfer"><div class="field">' +
      '<label for="portable">Your saved list, as text</label>' +
      '<textarea id="portable" rows="4" spellcheck="false"></textarea>' +
      '</div><div class="hero-actions mt0">' +
      '<button class="btn ghost" type="button" id="copymine">Copy it</button>' +
      '<button class="btn ghost" type="submit">Bring a list in</button>' +
      '</div><p class="small" id="transferstate" aria-live="polite"></p></form>';

    mine.innerHTML = html +
      '<p class="mt5"><button class="btn ghost" id="clearmine">Clear everything</button></p>';

    var portable = document.getElementById("portable");
    var tstate = document.getElementById("transferstate");
    portable.value = JSON.stringify({ v: 1, saved: list, collections: colls });

    document.getElementById("copymine").addEventListener("click", function () {
      portable.select();
      /* Two ways, because clipboard.writeText needs a permission the page may
       * not have and execCommand is deprecated but still the fallback that
       * works. If both fail the text is selected and the reader can copy it
       * themselves, so the feature degrades to "slightly more manual"
       * rather than to nothing. */
      var done = false;
      try { done = document.execCommand("copy"); } catch (e) { done = false; }
      if (navigator.clipboard && !done) {
        navigator.clipboard.writeText(portable.value).then(function () {
          tstate.textContent = "Copied. Paste it into the same box on the other device.";
        }, function () {
          tstate.textContent = "This browser will not let a page copy for you — the text is selected, so copy it yourself.";
        });
        return;
      }
      tstate.textContent = done
        ? "Copied. Paste it into the same box on the other device."
        : "The text is selected — copy it yourself, this browser will not let the page do it.";
    });

    document.getElementById("transfer").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var parsed;
      try { parsed = JSON.parse(portable.value); } catch (e) { parsed = null; }
      /* Validate the shape rather than trusting it. This text arrived by
       * being pasted, which means it could be anything, and a saved item
       * whose url is not one of ours would put an arbitrary link on the
       * reader's own page. */
      if (!parsed || !Array.isArray(parsed.saved)) {
        tstate.textContent = "That is not a EuropeDoor list. Paste the whole thing, including the brackets.";
        return;
      }
      var clean = parsed.saved.filter(function (x) {
        return x && typeof x.id === "string" && typeof x.url === "string" &&
               x.url.charAt(0) === "/" && x.url.charAt(1) !== "/";
      }).map(function (x) {
        return { id: x.id, kind: String(x.kind || "Place"), label: String(x.label || x.id),
                 url: x.url, list: x.list ? String(x.list) : undefined };
      });
      var dropped = parsed.saved.length - clean.length;
      /* Merge rather than replace: someone moving a list to a device that
       * already has one should not silently lose the second. */
      var byId = {};
      list.forEach(function (x) { byId[x.id] = true; });
      var added = 0;
      clean.forEach(function (x) { if (!byId[x.id]) { list.push(x); added++; } });
      (Array.isArray(parsed.collections) ? parsed.collections : []).forEach(function (c) {
        if (typeof c === "string" && colls.indexOf(c) < 0) colls.push(c);
      });
      if (!write(list) || !writeColls(colls)) {
        tstate.textContent = "This browser will not let us save.";
        return;
      }
      render();
      document.getElementById("transferstate").textContent =
        added + (added === 1 ? " item added" : " items added") +
        (added < clean.length ? ", the rest were already here" : "") +
        (dropped ? ". " + dropped + " ignored: not a EuropeDoor link." : ".");
    });

    document.getElementById("clearmine").addEventListener("click", function () {
      if (write([]) && writeColls([])) location.reload();
    });
    document.getElementById("newcoll").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var name = document.getElementById("collname").value.trim();
      if (!name || colls.indexOf(name) >= 0) return;
      colls.push(name);
      if (writeColls(colls)) render();
    });
    mine.querySelectorAll("[data-move]").forEach(function (sel) {
      sel.addEventListener("change", function () {
        list[Number(sel.getAttribute("data-move"))].list = sel.value || undefined;
        if (write(list)) render();
      });
    });
    mine.querySelectorAll("[data-drop]").forEach(function (b) {
      b.addEventListener("click", function () {
        list.splice(Number(b.getAttribute("data-drop")), 1);
        if (write(list)) render();
      });
    });
  }

  render();

  /* The Atlas is fetched only here, only on this page, and only to resolve
   * saved ids to the interests that produce the profile. It is the same
   * static document the planner uses, so it is almost certainly cached. */
  var dnaHost = document.getElementById("dna");
  if (dnaHost) {
    fetch("/api/atlas.json").then(function (r) { return r.json(); }).then(function (atlas) {
      renderDna(dnaHost, atlas, list);
    }).catch(function () {
      dnaHost.innerHTML = '<div class="note"><p>The Atlas index did not load, so the ' +
        "travel profile cannot be computed. Your saved list above is unaffected.</p></div>";
    });
  }
})();
