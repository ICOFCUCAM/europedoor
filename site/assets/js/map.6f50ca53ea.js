/* The map.
 *
 * Three things happen here and they are kept apart on purpose:
 *
 *   geography   the land, the borders, the levels of detail, the zoom
 *   the graph   which country, region and destination a shape stands for
 *   the layers  what is lit, and the journey overlay
 *
 * The map keeps no list of anything. Every country, region and destination
 * on it was read from data/countries/*.json at build time and carries the id
 * of the record it came from, so a destination added to the atlas appears
 * here without anybody remembering to update the map. That is the whole
 * reason the shapes are <a href> elements with real URLs: with scripting off
 * this is still a navigable map of Europe, and the click below is
 * intercepted rather than invented.
 */
(function () {
  "use strict";

  /* Page data arrives as an inert application/json block rather than an
   * inline script, so the site can run script-src 'self' with no
   * 'unsafe-inline'. Guarded because a missing block must degrade to a map
   * that does less, not to a thrown exception that takes the rest of the
   * page with it. */
  function pageData(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  function esc(x) {
    return String(x).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  var NS = "http://www.w3.org/2000/svg";
  var svg = document.getElementById("europemap");
  var box = document.getElementById("layers");
  var dots = Array.prototype.slice.call(document.querySelectorAll("#dots .dot"));
  var count = document.getElementById("mapcount");
  if (!svg) return;

  var PROJ = pageData("europedoor-projection");
  var COUNTRIES = pageData("europedoor-countries") || {};
  var INFO = pageData("europedoor-mapinfo") || {};
  var JOURNEYS = pageData("europedoor-journeys") || [];

  /* Lambert conformal conic, from the same four ANGLES the build used.
   *
   * This was six numbers and one multiplication, because the projection was
   * equirectangular and affine. A conic is not affine — that is the whole
   * point of it, since the scale along a parallel has to change with
   * latitude for shape to be right anywhere but one line — so the browser
   * now derives the cone constant and the scale factor here.
   *
   * That is a second implementation of a formula, which this file has always
   * refused. The refusal is kept where it matters: the four parallels are
   * DECIDED in one place, tools/lib/geo.py, and handed here as data; nothing
   * about the projection is chosen twice. And a browser check asserts the
   * two implementations agree to a hundredth of a pixel on nine points
   * spread across the extent, so a drift is a failing build rather than a
   * coastline sitting two pixels off the city on it. */
  var LCC = (function () {
    var p1 = PROJ.p1 * Math.PI / 180, p2 = PROJ.p2 * Math.PI / 180;
    var t1 = Math.tan(Math.PI / 4 + p1 / 2), t2 = Math.tan(Math.PI / 4 + p2 / 2);
    var n = Math.log(Math.cos(p1) / Math.cos(p2)) / Math.log(t2 / t1);
    var f = Math.cos(p1) * Math.pow(t1, n) / n;
    var rho0 = f / Math.pow(Math.tan(Math.PI / 4 + PROJ.lat0 * Math.PI / 360), n);
    return { n: n, f: f, rho0: rho0 };
  }());

  function px(lat, lon) {
    var rho = LCC.f / Math.pow(Math.tan(Math.PI / 4 + lat * Math.PI / 360), LCC.n);
    var theta = LCC.n * (lon - PROJ.lon0) * Math.PI / 180;
    var x = rho * Math.sin(theta), y = LCC.rho0 - rho * Math.cos(theta);
    return [PROJ.ox + (x - PROJ.px0) * PROJ.scale,
            PROJ.oy + (PROJ.py1 - y) * PROJ.scale];
  }

  /* Exposed for the browser check that asserts this implementation and the
     build's agree. Not used by anything on the page. */
  window.__europedoorProjectionProbe = px;

  function ringPath(flat) {
    var d = "", last = null, i, p;
    for (i = 0; i < flat.length; i += 2) {
      p = px(flat[i + 1], flat[i]);
      p = [Math.round(p[0] * 10) / 10, Math.round(p[1] * 10) / 10];
      if (last && p[0] === last[0] && p[1] === last[1]) continue;
      d += (last ? "L" : "M") + p[0] + " " + p[1];
      last = p;
    }
    return d ? d + "Z" : "";
  }

  /* ── zoom ───────────────────────────────────────────────────────────
   *
   * The viewBox is the only thing that moves. Nothing is re-projected and
   * nothing is redrawn, so panning a continent costs the browser one
   * attribute write — which is why this is smooth on a phone where a
   * canvas renderer would not be.
   *
   * Stroke widths are the catch: an SVG stroke scales with the viewBox, so
   * a 1px border becomes 8px at 8x zoom and Europe turns into a coloured
   * blob. The scale is published as a CSS custom property on the wrapper
   * and every stroke in the map is expressed in terms of it. */
  var W = PROJ ? PROJ.w : 1000, H = PROJ ? PROJ.h : 780;
  var view = { x: 0, y: 0, w: W, h: H };
  var MINW = W / 40, MAXW = W;
  var where = document.getElementById("zoomwhere");

  function applyView() {
    view.w = Math.max(MINW, Math.min(MAXW, view.w));
    view.h = view.w * (H / W);
    view.x = Math.max(-view.w * 0.15, Math.min(W - view.w * 0.85, view.x));
    view.y = Math.max(-view.h * 0.15, Math.min(H - view.h * 0.85, view.y));
    svg.setAttribute("viewBox",
      view.x.toFixed(1) + " " + view.y.toFixed(1) + " " +
      view.w.toFixed(1) + " " + view.h.toFixed(1));
    svg.style.setProperty("--z", (W / view.w).toFixed(3));
    maybeUpgrade();
  }

  function zoomBy(f, cx, cy) {
    if (cx === undefined) { cx = view.x + view.w / 2; cy = view.y + view.h / 2; }
    var nw = Math.max(MINW, Math.min(MAXW, view.w * f));
    var k = nw / view.w;
    view.x = cx - (cx - view.x) * k;
    view.y = cy - (cy - view.y) * k;
    view.w = nw;
    applyView();
  }

  function zoomToBox(bbox, label) {
    /* bbox is lon/lat from the geometry pipeline. Projected here rather than
     * stored as pixels so the same number works at any output size. */
    var a = px(bbox[3], bbox[0]), b = px(bbox[1], bbox[2]);
    var w = Math.abs(b[0] - a[0]), h = Math.abs(b[1] - a[1]);
    var pad = 1.35;
    view.w = Math.max(w * pad, (h * pad) * (W / H), MINW);
    view.h = view.w * (H / W);
    view.x = (a[0] + b[0]) / 2 - view.w / 2;
    view.y = (a[1] + b[1]) / 2 - view.h / 2;
    applyView();
    if (where) where.textContent = label ? "Showing " + label : "";
  }

  function resetView(silent) {
    view = { x: 0, y: 0, w: W, h: H };
    applyView();
    if (where && !silent) where.textContent = "";
  }

  /* ── levels of detail ───────────────────────────────────────────────
   *
   * The page ships 1:110m inline: the right amount of coastline for a view
   * of the whole continent, and about a quarter of the bytes of the next
   * level up. Zooming past 1.6x fetches 1:50m once and swaps it in;
   * selecting a country fetches that country's own file, which is finer
   * still and carries its neighbours so the country is not floating.
   *
   * Everything is fetched from our own origin, which is what makes
   * connect-src 'self' hold. There is no tile server, no key and no
   * request that leaves this domain. */
  var lodState = 0;          // 0 = inline 110m, 1 = fetched 50m
  var lodPending = false;
  var group = document.getElementById("countries");
  var detail = document.getElementById("detail");
  var contextG = document.getElementById("context");

  function shapeEl(ident, ent) {
    var d = "", i;
    for (i = 0; i < ent.rings.length; i++) d += ringPath(ent.rings[i]);
    if (!d) return null;
    var path = document.createElementNS(NS, "path");
    path.setAttribute("d", d);
    var title = document.createElementNS(NS, "title");
    title.textContent = ent.name;
    if (!ent.atlas) {
      path.appendChild(title);
      return path;
    }
    var a = document.createElementNS(NS, "a");
    a.setAttribute("class", "cshape");
    a.setAttribute("href", "/europe/" + ent.slug);
    a.setAttribute("id", "cshape-" + ent.slug);
    a.setAttribute("data-slug", ent.slug);
    a.setAttribute("data-name", ent.name);
    a.setAttribute("data-bbox", ent.bbox.join(","));
    a.appendChild(path);
    a.appendChild(title);
    return a;
  }

  function fill(target, doc, atlasOnly) {
    var frag = document.createDocumentFragment(), ident, el;
    for (ident in doc.countries) {
      if (!Object.prototype.hasOwnProperty.call(doc.countries, ident)) continue;
      if (atlasOnly && !doc.countries[ident].atlas) continue;
      if (!atlasOnly && doc.countries[ident].atlas) continue;
      el = shapeEl(ident, doc.countries[ident]);
      if (el) frag.appendChild(el);
    }
    target.textContent = "";
    target.appendChild(frag);
  }

  function maybeUpgrade() {
    if (lodState || lodPending || W / view.w < 1.6) return;
    lodPending = true;
    fetch("/api/geo/europe-lod1.json", { credentials: "omit" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (doc) {
        if (!doc) return;
        fill(group, doc, true);
        if (contextG) fill(contextG, doc, false);
        lodState = 1;
        wireShapes();
      })
      .catch(function () { /* a coarser map is a fine outcome; keep the one
                            * that is already drawn rather than blanking it */ })
      .then(function () { lodPending = false; });
  }

  var detailFor = null;
  function loadDetail(slug) {
    if (detailFor === slug || !detail) return;
    detailFor = slug;
    detail.textContent = "";
    fetch("/api/geo/country/" + slug + ".json", { credentials: "omit" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (doc) {
        if (!doc || detailFor !== slug) return;
        var frag = document.createDocumentFragment(), ident, el;
        for (ident in doc.countries) {
          if (!Object.prototype.hasOwnProperty.call(doc.countries, ident)) continue;
          el = shapeEl(ident, doc.countries[ident]);
          if (el) {
            if (doc.countries[ident].slug === slug) el.setAttribute("class", "cshape on");
            frag.appendChild(el);
          }
        }
        detail.appendChild(frag);
        wireShapes();
      })
      .catch(function () { detailFor = null; });
  }

  /* ── selecting a country ────────────────────────────────────────────
   *
   * Europe -> country -> region -> destination, which is the same ladder
   * the URLs use. The panel is built from the knowledge graph, so every row
   * in it is a real page: /europe/norway, /europe/norway/vestland,
   * /europe/norway/vestland/bergen. Nothing here is a button that does
   * nothing. */
  var panel = document.getElementById("countrypanel");
  var popup = document.getElementById("mappopup");
  var stage = document.querySelector(".mapstage");
  var selected = null;

  /* The side column is created by opening something into it and removed when
   * both things in it are closed, so the map is full width whenever there is
   * nothing to put beside it. */
  function sizeStage() {
    if (!stage) return;
    var open = (panel && !panel.hidden) || (popup && !popup.hidden);
    stage.classList.toggle("withpanel", !!open);
  }

  function markSelected(slug) {
    var all = svg.querySelectorAll(".cshape.on");
    for (var i = 0; i < all.length; i++) all[i].classList.remove("on");
    if (!slug) return;
    var el = document.getElementById("cshape-" + slug);
    if (el) el.classList.add("on");
  }

  function selectCountry(slug, push) {
    var c = COUNTRIES[slug];
    if (!c || !panel) return;
    selected = slug;
    if (popup) popup.hidden = true;
    markSelected(slug);
    loadDetail(slug);

    var el = document.getElementById("cshape-" + slug);
    var bbox = el && el.getAttribute("data-bbox");
    if (bbox) zoomToBox(bbox.split(",").map(Number), c.n);

    var dcount = 0, i;
    for (i = 0; i < c.r.length; i++) dcount += c.r[i].d.length;

    var regions = c.r.map(function (r) {
      var d = r.d.slice(0, 6).map(function (t) {
        return '<a href="' + t.u + '">' + esc(t.n) + "</a>";
      }).join(", ");
      var more = r.d.length > 6 ? " and " + (r.d.length - 6) + " more" : "";
      return '<li><a class="rlink" href="' + r.u + '">' + esc(r.n) + "</a>" +
             (d ? '<span class="small"> — ' + d + more + "</span>" : "") + "</li>";
    }).join("");

    panel.innerHTML =
      '<button class="mappopup-close" type="button" aria-label="Close">×</button>' +
      '<p class="kicker">Country</p>' +
      '<h2 class="mini">' + esc(c.n) + "</h2>" +
      "<p>" + esc(c.t) + "</p>" +
      '<p class="small">' + c.r.length + (c.r.length === 1 ? " region" : " regions") +
        " · " + dcount + (dcount === 1 ? " destination" : " destinations") + "</p>" +
      (c.adv ? '<p class="small">This country is under a travel advisory. It is not in the ' +
               "planner, and the country page says why.</p>" : "") +
      '<ul class="regionlist">' + regions + "</ul>" +
      '<p><a class="btn" href="' + c.u + '">Explore ' + esc(c.n) + " →</a></p>";
    panel.hidden = false;
    sizeStage();
    panel.querySelector(".mappopup-close").addEventListener("click", function () {
      clearCountry(true);
    });
    drawRegions();

    /* The selection is in the URL, so a map someone has drilled into is a
     * map they can send to somebody else. replaceState on the first select
     * and pushState after, so Back leaves the map rather than stepping
     * through every country visited on the way. */
    if (push !== false && window.history && window.history.pushState) {
      var url = "/map?c=" + encodeURIComponent(slug);
      if (selectedOnce) window.history.pushState({ c: slug }, "", url);
      else window.history.replaceState({ c: slug }, "", url);
      selectedOnce = true;
    }
  }
  var selectedOnce = false;

  function clearCountry(push) {
    selected = null;
    detailFor = null;
    if (detail) detail.textContent = "";
    markSelected(null);
    if (panel) panel.hidden = true;
    sizeStage();
    resetView();
    drawRegions();
    if (push && window.history && window.history.pushState) {
      window.history.pushState({}, "", "/map");
    }
  }

  function wireShapes() {
    var shapes = svg.querySelectorAll(".cshape, .cpoint");
    for (var i = 0; i < shapes.length; i++) {
      if (shapes[i].getAttribute("data-wired")) continue;
      shapes[i].setAttribute("data-wired", "1");
      shapes[i].addEventListener("click", onShapeClick);
    }
  }

  function onShapeClick(ev) {
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button !== 0) return;
    var slug = this.getAttribute("data-slug");
    if (!COUNTRIES[slug]) return;      // no panel to show: let the link work
    ev.preventDefault();
    if (selected === slug) {
      /* Second click on the country already open follows the link. A shape
       * that stops responding once it is selected reads as broken. */
      window.location.href = COUNTRIES[slug].u;
      return;
    }
    selectCountry(slug);
  }
  wireShapes();

  window.addEventListener("popstate", function () {
    var want = new URLSearchParams(location.search).get("c");
    if (want && COUNTRIES[want]) selectCountry(want, false);
    else clearCountry(false);
  });

  /* ── the region layer ───────────────────────────────────────────────
   *
   * Regions are drawn as what we actually hold: which destinations belong to
   * which region. Not as boundaries. We have no region geometry — the
   * dataset that has it (Eurostat NUTS) is copyrighted and its terms have
   * not been accepted, which is written down in
   * docs/data-licenses/eurostat-gisco-nuts.md — and drawing a hull around
   * Bergen and Ålesund and labelling it Vestland would look like an answer
   * while being a guess.
   *
   * So: a label at the centre of a region's destinations, with hairlines to
   * each of them. It reads as a grouping, which is what it is. */
  var regionsG = document.getElementById("regions");

  function drawRegions() {
    if (!regionsG) return;
    var on = geoOn("regions");
    if (!on) { showGroup(regionsG, false); regionsG.textContent = ""; return; }
    regionsG.textContent = "";
    var slugs = selected ? [selected] : Object.keys(COUNTRIES);
    var frag = document.createDocumentFragment();
    var drawn = 0;
    slugs.forEach(function (cs) {
      var c = COUNTRIES[cs];
      if (!c) return;
      c.r.forEach(function (r) {
        var pts = [], i, d, t;
        for (i = 0; i < r.d.length; i++) {
          d = INFO[r.d[i].id];
          if (d) pts.push(px(d.la, d.lo));
        }
        if (!pts.length) return;
        /* Without a country selected, only label regions holding more than
         * one destination. 150-odd single-destination labels at continent
         * zoom is not a layer, it is a fog. */
        if (!selected && pts.length < 2) return;
        var cx = 0, cy = 0;
        for (i = 0; i < pts.length; i++) { cx += pts[i][0]; cy += pts[i][1]; }
        cx /= pts.length; cy /= pts.length;
        for (i = 0; i < pts.length; i++) {
          var line = document.createElementNS(NS, "line");
          line.setAttribute("x1", cx.toFixed(1)); line.setAttribute("y1", cy.toFixed(1));
          line.setAttribute("x2", pts[i][0].toFixed(1));
          line.setAttribute("y2", pts[i][1].toFixed(1));
          line.setAttribute("class", "rtie");
          frag.appendChild(line);
        }
        var a = document.createElementNS(NS, "a");
        a.setAttribute("class", "rlabel");
        a.setAttribute("href", r.u);
        t = document.createElementNS(NS, "text");
        t.setAttribute("x", cx.toFixed(1));
        t.setAttribute("y", (cy - 9).toFixed(1));
        t.textContent = r.n;
        a.appendChild(t);
        var ttl = document.createElementNS(NS, "title");
        ttl.textContent = r.n + " — " + r.d.length +
          (r.d.length === 1 ? " destination" : " destinations");
        a.appendChild(ttl);
        frag.appendChild(a);
        drawn++;
      });
    });
    regionsG.appendChild(frag);
    showGroup(regionsG, drawn);
  }

  /* ── layers ─────────────────────────────────────────────────────────
   *
   * Every layer is a group that is shown or hidden, never a redraw. Note
   * setAttribute rather than `.hidden`: these are SVG <g> elements, and
   * `.hidden` is an HTMLElement property — assigning it defines a JS
   * property nobody reads and the layer never appears. That cost an
   * afternoon once and the comment is cheaper than the second afternoon.
   *
   * AND THE ATTRIBUTE ALONE HIDES NOTHING WITHOUT A STYLESHEET. The UA
   * sheet's `[hidden] { display: none }` is namespaced to HTML, so an SVG
   * group marked hidden went on drawing until europedoor.css added a rule
   * of its own — which means the map's layer switches were one stylesheet
   * request away from being inert, and the eight hundred pages carrying an
   * embedded map with them. CI found the other half of it: Chromium 131
   * does not apply that author rule to these groups while Chromium 141
   * does, so `places` shipped visible on the runner and hidden here, and
   * the two browser checks that read a layer's visibility disagreed for
   * three months. `display` is a PRESENTATION ATTRIBUTE in SVG: it needs
   * no stylesheet, no cascade and no browser version. The `hidden`
   * attribute stays because it is what a reader's assistive technology is
   * told; the presentation attribute is what actually removes the ink. */
  var geobox = document.getElementById("geolayers");

  function geoOn(name) {
    if (!geobox) return name === "cities" || name === "borders";
    var el = geobox.querySelector('input[name="geo"][value="' + name + '"]');
    return el ? el.checked : false;
  }

  function showGroup(g, on) {
    if (on) { g.removeAttribute("hidden"); g.removeAttribute("display"); }
    else { g.setAttribute("hidden", ""); g.setAttribute("display", "none"); }
  }

  function toggleGroup(id, on) {
    var g = document.getElementById(id);
    if (!g) return;
    showGroup(g, on);
  }

  function applyGeo() {
    svg.classList.toggle("noborders", !geoOn("borders"));
    toggleGroup("places", geoOn("places"));
    toggleGroup("dots", geoOn("cities"));
    drawRegions();
  }
  if (geobox) geobox.addEventListener("change", applyGeo);

  /* Interest filters, unchanged in behaviour: the dots are already in the
   * page, this only decides which are lit, so the map works as a map of
   * everywhere with JavaScript off. */
  function applyInterests() {
    if (!box || !dots.length) return;
    var on = [], i;
    var boxes = box.querySelectorAll('input[name="layer"]:checked');
    for (i = 0; i < boxes.length; i++) on.push(boxes[i].value);
    var lit = 0;
    dots.forEach(function (d) {
      var tags = (d.getAttribute("data-tags") || "").split(" ");
      var show = !on.length || on.some(function (t) { return tags.indexOf(t) >= 0; });
      d.classList.toggle("off", !show);
      if (show) lit++;
    });
    if (count) {
      count.textContent = on.length
        ? lit + " of " + dots.length + " destinations match the layers you turned on."
        : dots.length + " destinations across " + Object.keys(COUNTRIES).length +
          " countries. Turn on a layer to narrow it.";
    }
  }
  var wanted = new URLSearchParams(location.search).get("layer");
  if (wanted && box) {
    var pre = box.querySelector('input[name="layer"][value="' + wanted + '"]');
    if (pre) pre.checked = true;
  }
  if (box) box.addEventListener("change", applyInterests);
  applyInterests();
  applyGeo();

  /* ── pan, wheel, keys ───────────────────────────────────────────────
   *
   * Pointer events rather than mouse events, so a finger drag on a phone is
   * the same code path as a mouse drag. The map is also operable from the
   * keyboard once focused, because a zoom you can only reach with a wheel
   * is a zoom half the audience does not have. */
  var zin = document.getElementById("zoomin");
  var zout = document.getElementById("zoomout");
  var zreset = document.getElementById("zoomreset");
  if (zin) zin.addEventListener("click", function () { zoomBy(1 / 1.5); });
  if (zout) zout.addEventListener("click", function () { zoomBy(1.5); });
  if (zreset) zreset.addEventListener("click", function () { clearCountry(true); });

  var drag = null;
  svg.addEventListener("pointerdown", function (ev) {
    if (ev.button !== 0) return;
    drag = { x: ev.clientX, y: ev.clientY, vx: view.x, vy: view.y, moved: 0 };
  });
  svg.addEventListener("pointermove", function (ev) {
    if (!drag) return;
    var r = svg.getBoundingClientRect();
    var dx = (ev.clientX - drag.x) * (view.w / r.width);
    var dy = (ev.clientY - drag.y) * (view.h / r.height);
    drag.moved = Math.max(drag.moved, Math.abs(dx) + Math.abs(dy));
    if (drag.moved < 3) return;
    view.x = drag.vx - dx;
    view.y = drag.vy - dy;
    applyView();
  });
  function endDrag() { drag = null; }
  svg.addEventListener("pointerup", endDrag);
  svg.addEventListener("pointercancel", endDrag);
  svg.addEventListener("pointerleave", endDrag);

  /* A drag that ends on a country must not also open that country. Three
   * pixels of slop, because a click on a touchscreen always moves a little. */
  svg.addEventListener("click", function (ev) {
    if (drag && drag.moved >= 3) { ev.preventDefault(); ev.stopPropagation(); }
  }, true);

  svg.addEventListener("wheel", function (ev) {
    if (!ev.deltaY) return;
    ev.preventDefault();
    var r = svg.getBoundingClientRect();
    var cx = view.x + ((ev.clientX - r.left) / r.width) * view.w;
    var cy = view.y + ((ev.clientY - r.top) / r.height) * view.h;
    zoomBy(ev.deltaY > 0 ? 1.18 : 1 / 1.18, cx, cy);
  }, { passive: false });

  svg.setAttribute("tabindex", "0");
  svg.addEventListener("keydown", function (ev) {
    var step = view.w * 0.12, handled = true;
    if (ev.key === "ArrowLeft") view.x -= step;
    else if (ev.key === "ArrowRight") view.x += step;
    else if (ev.key === "ArrowUp") view.y -= step;
    else if (ev.key === "ArrowDown") view.y += step;
    else if (ev.key === "+" || ev.key === "=") zoomBy(1 / 1.5);
    else if (ev.key === "-" || ev.key === "_") zoomBy(1.5);
    else if (ev.key === "Escape") clearCountry(true);
    else handled = false;
    if (handled) { ev.preventDefault(); applyView(); }
  });

  /* Arriving at /map?c=norway opens Norway. The state is in the URL so a
   * drilled-in map is a map you can send to someone. */
  var initial = new URLSearchParams(location.search).get("c");
  if (initial && COUNTRIES[initial]) selectCountry(initial, false);
  else applyView();

  /* ── the journey overlay ────────────────────────────────────────────
   *
   * The legs are projected at build time and handed to the page, so the line
   * and the dots cannot drift apart — a map that draws a route two pixels
   * off the city it visits looks broken in a way nobody can quite name. */
  var sel = document.getElementById("journeylayer");
  var route = document.getElementById("route");
  var note = document.getElementById("routenote");

  function drawJourney() {
    if (!route) return;
    route.textContent = "";
    var j = null, i;
    for (i = 0; i < JOURNEYS.length; i++) if (JOURNEYS[i].slug === sel.value) j = JOURNEYS[i];
    if (!j) { if (note) note.textContent = ""; return; }

    var d = j.pts.map(function (p, n) { return (n ? "L" : "M") + p.x + " " + p.y; }).join(" ");
    var line = document.createElementNS(NS, "path");
    line.setAttribute("d", d);
    line.setAttribute("class", "routeline");
    route.appendChild(line);

    j.pts.forEach(function (p, n) {
      var c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", p.x); c.setAttribute("cy", p.y); c.setAttribute("r", 7);
      c.setAttribute("class", "routedot");
      var t = document.createElementNS(NS, "title");
      t.textContent = (n + 1) + ". " + p.name;
      c.appendChild(t);
      route.appendChild(c);
    });

    if (note) {
      note.innerHTML = esc(j.name) + " — " + j.pts.length + " stops over " + j.days +
        ' days. <a href="' + j.url + '">Read the route</a>. The line is straight ' +
        "between stops: the order is real, the line is not a route.";
    }
  }
  if (sel) { sel.addEventListener("change", drawJourney); drawJourney(); }

  /* ── destination popups ─────────────────────────────────────────────
   *
   * A card on click: name, region, a sentence, the distance, and a way in.
   * The dots stay real links so the map still works with JavaScript off —
   * the click is intercepted, not replaced. */
  var fromSel = document.getElementById("mapfrom");

  function kmBetween(a, b) {
    var R = 6371, p1 = a.la * Math.PI / 180, p2 = b.la * Math.PI / 180;
    var dp = p2 - p1, dl = (b.lo - a.lo) * Math.PI / 180;
    var h = Math.sin(dp / 2) * Math.sin(dp / 2) +
            Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
    return Math.round(2 * R * Math.asin(Math.sqrt(h)));
  }

  function showPopup(id) {
    var d = INFO[id];
    if (!d || !popup) return;
    if (panel) panel.hidden = true;
    var origin = fromSel && fromSel.value ? INFO[fromSel.value] : null;
    var dist = origin && origin !== d
      ? '<p class="small">' + kmBetween(origin, d) + " km from " + esc(origin.n) + "</p>" : "";
    var counts = [];
    if (d.p) counts.push(d.p + (d.p === 1 ? " place" : " places"));
    if (d.e) counts.push(d.e + (d.e === 1 ? " experience" : " experiences"));
    popup.innerHTML =
      '<button class="mappopup-close" type="button" aria-label="Close">×</button>' +
      '<p class="kicker">' + esc(d.r) + " · " + esc(d.c) + "</p>" +
      '<h2 class="mini">' + esc(d.n) + "</h2>" +
      "<p>" + esc(d.s) + "</p>" +
      (counts.length ? '<p class="small">' + counts.join(" · ") + "</p>" : "") +
      dist +
      (d.adv ? '<p class="small">This country is under a travel advisory.</p>' : "") +
      '<p><a class="btn ghost" href="' + d.u + '">Open ' + esc(d.n) + "</a></p>";
    popup.hidden = false;
    sizeStage();
    popup.querySelector(".mappopup-close").addEventListener("click", function () {
      popup.hidden = true;
      sizeStage();
    });
  }

  dots.forEach(function (a) {
    a.addEventListener("click", function (ev) {
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button !== 0) return;
      if (drag && drag.moved >= 3) return;
      ev.preventDefault();
      showPopup(a.getAttribute("data-id"));
    });
  });
  if (fromSel) fromSel.addEventListener("change", function () {
    if (popup) popup.hidden = true;
    sizeStage();
  });
})();
