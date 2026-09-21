/* THE ATLAS STAGE — the homepage's fifth plate, and the ONE thing on that
   band a stylesheet cannot do.
 *
 * The composition is scroll-native by design: the stage is sticky, the nine
 * corners are real blocks in the document, and each one's card is pinned in
 * the panel slot for the length of its own step. All of that happens with
 * the stylesheet alone, which is the whole reason it was built that way —
 * this homepage's only other `<script>` is the inert JSON-LD block, and a
 * band that exists only while JavaScript runs is nine corners of this atlas
 * that a reader without it never sees.
 *
 * What CSS cannot do is tell the DRAWING which corner is being read. No
 * selector reaches from a scrolled block to an unrelated `<text>` in the
 * figure above it, and that connection is the band's whole argument: the
 * continent answers the reading. So this file does exactly two things —
 * it says which step is in the middle of the screen, and it says that the
 * stage is live so the stylesheet may show one card rather than the
 * flowing list it falls back to.
 *
 * IT IS AN ENHANCEMENT BY THIS SITE'S OWN TEST: it fetches no index, owns
 * no client state, writes nothing to storage, and operates only on markup
 * the build already put in the page. `data/contracts.json` is for the five
 * APPLICATIONS, which this is not.
 *
 * AND IT MUST FAIL SOFT, because the page is complete without it. Every
 * exit below returns rather than throwing: a stage that never goes live
 * reads as the nine corners in a column, which is what a phone gets by
 * design and what a reader with no JavaScript has always got. */
(() => {
  const track = document.querySelector('.atlas');
  const stage = track && track.querySelector('.atstage');
  const steps = track ? [...track.querySelectorAll('.atcorner')] : [];
  if (!track || !stage || steps.length < 2) return;

  /* THE STYLESHEET OPTS IN RATHER THAN OUT. `[data-live]` scopes every rule
     that only makes sense once something is choosing a corner — hiding
     eight of the nine cards among them — so the no-script state cannot be
     a page with eight invisible blocks on it. */
  track.dataset.live = '';

  /* A BAND ACROSS THE MIDDLE OF THE SCREEN, not the top edge and not the
     whole viewport. `-46%` top and bottom leaves an 8%-tall strip: the
     corner crossing it is the one being read, which is where a reader's
     eye is and is the same judgement the prototype makes by dividing the
     section's scroll into nine. A whole-viewport root reports three or four
     at once and the last one to fire wins, which is a different corner on
     the way down than on the way up. */
  let at = '';
  const mark = (slug) => {
    if (slug === at) return;
    at = slug;
    /* ONE ATTRIBUTE ON THE STAGE IS THE WHOLE CONNECTION. The stylesheet
       reads it to light that corner's countries, to lift them out of the
       continent, and to bring their names to full ink — and every one of
       those is keyed on a `data-lift` and a `data-corner` the BUILD wrote
       from the drawn geometry, so this file carries no geography, no
       direction and no number. It says which corner is being read. */
    stage.dataset.at = slug;
    for (const s of steps) {
      if (s.dataset.corner === slug) s.dataset.on = '';
      else s.removeAttribute('data-on');
    }
  };

  const io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) mark(e.target.dataset.corner);
  }, { rootMargin: '-46% 0px -46% 0px', threshold: 0 });
  for (const s of steps) io.observe(s);

  /* A CARD AT ZERO ALPHA IS STILL IN THE TAB ORDER, AND EIGHT OF THE NINE
     ARE AT ZERO. `pointer-events: none` stops a mouse and says nothing
     about a keyboard, so the browser suite measured **38 links of 5,391
     painting nothing even with focus on them** — every country link and
     every corner heading in the eight cards that are not current. That is
     `.doorgo` for the third time here: present, placed, sized,
     keyboard-reachable and unseeable.
     Removing them from the tab order would be worse, because this page is
     the only route to them. So focus DRIVES the stage: tabbing into a
     corner makes it the corner being read, the card comes up, and the
     continent lights and pans to match. The browser scrolls a focused
     element into view by itself, and the card is sticky in the panel slot,
     so the step arrives where the card already is. It is the rule this
     site already applies to every hover-revealed link it ships: a link a
     keyboard reaches has to become visible when it does. */
  track.addEventListener('focusin', (e) => {
    const step = e.target.closest && e.target.closest('.atcorner');
    if (step && step.dataset.corner) mark(step.dataset.corner);
  });

  /* THE FIRST CORNER IS MARKED BEFORE A READER SCROLLS, because the stage
     is pinned from the moment the section arrives and a panel slot with
     nothing in it is a hole where the composition promised a reading. The
     observer only fires on a CHANGE, so the opening state has to be set. */
  mark(steps[0].dataset.corner);

  /* AND THE OPENING STATE IS SET BEFORE ANYTHING MAY ANIMATE. Two frames,
     because one is not enough: the style that `mark()` just wrote has to
     be computed once before the transition rules arrive, or the browser
     coalesces both into a single change and animates it anyway. */
  requestAnimationFrame(() => requestAnimationFrame(() => {
    track.dataset.ready = '';
  }));
})();
