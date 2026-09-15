/* ONE PAGE PER RENDERED FAMILY, IN ONE PLACE.
 *
 * `opening.js` derives this list and reads the slugs off the built site;
 * `contact-sheet.js` had its own, typed by hand, and the two disagreed. The
 * sheet's `--more` set carried `["macro", "/countries/"]` — the countries
 * INDEX under the macro family's name — so the macro page has never appeared
 * on a contact sheet, and neither has the story, the theme, the journeys
 * index, the interests index, /europe-in, /events, /discover, /search,
 * /my-europe or the 404. The sheet's own comment says "the point of the
 * sheet is that every family is in one field of view", and it was covering
 * 23 of 27 while naming one of them wrong.
 *
 * A second implementation of a thing is a second chance to make its mistake
 * — ninth occurrence here, and the first where the thing was a LIST. The
 * answer on the third occurrence of that rule was to stop having a second
 * implementation, and this is that.
 *
 * A SLUG IS READ OFF THE BUILT SITE RATHER THAN TYPED, because a typed slug
 * is a 404 that reports 0% and looks like a finding: the first run of
 * `opening.js` called `journey`, `macro` and `place` the three worst
 * surfaces in the product and all three were bad URLs.
 */
const fs = require('fs'), path = require('path');

const ROOT = path.join(__dirname, '..', '..', 'site');

function pick(dir, fallback) {
  try {
    const e = fs.readdirSync(path.join(ROOT, dir))
      .filter((n) => !n.includes('.')).sort();
    return e.length ? dir + '/' + e[0] : fallback;
  } catch { return fallback; }
}

const VIENNA = 'europe/austria/vienna-and-the-east/vienna';

const FAMILIES = [
  ['homepage', '/'],
  ['countries', '/countries/'],
  ['macro', '/' + pick('discover', 'discover/nordic')],
  ['country', '/europe/austria/'],
  ['region', '/europe/austria/tyrol/'],
  ['destination', '/' + VIENNA + '/'],
  ['place', '/' + pick(VIENNA + '/place', VIENNA + '/place/schonbrunn')],
  ['experiences', '/experiences/'],
  ['category', '/experiences/food/'],
  ['journeys', '/journeys/'],
  ['journey', '/' + pick('journeys', 'journeys/carpathian-arc')],
  ['stories', '/stories/'],
  ['story', '/' + pick('stories', 'stories/a-language-with-no-relatives')],
  ['themes', '/themes/'],
  ['theme', '/' + pick('themes', 'themes/wine-europe')],
  ['interests', '/interests/'],
  ['interest', '/interests/mountains/'],
  ['europe-in', '/europe-in/'],
  ['motion', '/' + pick('europe-in', 'europe-in/above-the-arctic-circle')],
  ['events', '/events/'],
  ['quiet', '/beyond-the-obvious/'],
  ['map', '/map/'],
  ['discover', '/discover/'],
  ['plan', '/plan/'],
  ['search', '/search/'],
  ['my-europe', '/my-europe/'],
  ['404', '/404.html'],
];

/* THE FAMILIES THE TWO SHEETS LEFT OUT ARE NOT FAMILIES, THEY ARE PAGES the
 * sheet is also worth pointing at — the facet list under a destination and
 * the two sides of the fund. They ride at the end so the family pages fill
 * the earlier sets. */
const EXTRA = [
  ['facet', '/' + VIENNA + '/things-to-do/'],
  ['how it works', '/how-it-works/'],
  ['fund', '/fund/'],
  ['method', '/method/'],
  ['about', '/about/'],
  ['manifesto', '/manifesto/'],
  ['sources', '/sources/'],
  /* THE PROSE PAGES, WHICH NOTHING HAD EVER PHOTOGRAPHED. Fifteen documents
   * — the two business pages, the public API, the accessibility statement,
   * the four legal ones, contact and help — carry the same shell, the same
   * head roles and the same primitives as everything above, and not one of
   * them had appeared on a contact sheet. A page nobody looks at is a page
   * that drifts, and these are the ones a reader reaches when they have a
   * question about the product rather than about Europe. */
  ['for businesses', '/for-businesses/'],
  ['tourism boards', '/for-tourism-boards/'],
  ['api docs', '/api-docs/'],
  ['accessibility', '/accessibility/'],
  ['contact', '/contact/'],
  ['help', '/help/'],
  ['privacy', '/privacy/'],
  ['terms', '/terms/'],
  ['cookies', '/cookies/'],
  ['join', '/experiences/join/'],
];

module.exports = { FAMILIES, EXTRA, ALL: FAMILIES.concat(EXTRA), pick, ROOT };
