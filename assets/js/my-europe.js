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

  function label(btn, saved) {
    btn.textContent = saved ? "Saved to My Europe ✓" : "Save to My Europe";
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
      label(btn, at < 0);
    });
  });

  var mine = document.getElementById("mine");
  if (!mine) return;
  var list = read();
  if (!list.length) {
    mine.innerHTML = '<div class="note"><p>Nothing saved yet. Open any city in the ' +
      '<a href="/atlas">Atlas</a> and press <em>Save to My Europe</em>. If you have saved things ' +
      'before and this is empty, you are in a different browser or the site data was cleared — ' +
      'there is no copy anywhere else, which is the point.</p></div>';
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
        tstate.textContent = "That is not a Europedoor list. Paste the whole thing, including the brackets.";
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
        (dropped ? ". " + dropped + " ignored: not a Europedoor link." : ".");
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
})();
