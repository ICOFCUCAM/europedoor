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
      "</div><div class=\"hero-actions\" style=\"margin-top:0\">" +
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

    mine.innerHTML = html +
      '<p style="margin-top:var(--s5)"><button class="btn ghost" id="clearmine">Clear everything</button></p>';

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
