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
    stage.dataset.at = slug;
    for (const s of steps) {
      if (s.dataset.corner === slug) {
        s.dataset.on = '';
        /* AND THE CONTINENT MOVES, which is the other half of what a
           selector cannot reach. `data-pan` is DERIVED at build time from
           the mean of the paths the drawing actually emitted for that
           corner's countries — west, centre or east third of the drawn
           span — so this file carries no geography and no number. It
           copies one attribute from the step to the stage; the stylesheet
           holds three rules. The reason it is needed at all is measured:
           the panel's wash begins at the middle of the plate and the card
           sits over Ukraine, so four of the nine corners were lighting
           ground behind the panel. */
        if (s.dataset.pan) stage.dataset.pan = s.dataset.pan;
      } else s.removeAttribute('data-on');
    }
  };

  const io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) mark(e.target.dataset.corner);
  }, { rootMargin: '-46% 0px -46% 0px', threshold: 0 });
  for (const s of steps) io.observe(s);

  /* THE FIRST CORNER IS MARKED BEFORE A READER SCROLLS, because the stage
     is pinned from the moment the section arrives and a panel slot with
     nothing in it is a hole where the composition promised a reading. The
     observer only fires on a CHANGE, so the opening state has to be set. */
  mark(steps[0].dataset.corner);
})();
