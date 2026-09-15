const {chromium} = require('playwright');
const ALL = require('./families.js').ALL;
let SEEN = 0;
(async () => {
  const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const pg = await b.newPage({viewport:{width:1280, height:1200}});
  for (const [name, url] of ALL) {
    const r = await pg.goto('http://localhost:8899'+url, {waitUntil:'load'});
    if (!r || r.status() !== 200) { console.log('NOT 200 ' + url); continue; }
    const d = await pg.evaluate(() => {
      const out = [];
      let seen = 0;
      for (const fig of document.querySelectorAll('svg')) {
        const labs = [...fig.querySelectorAll('.minilabel, .rlabel text, .cname, .pname, .peakname, .fname, .sname')]
          .filter(e => e.getClientRects().length && getComputedStyle(e).display !== 'none');
        seen += labs.length;
        const bx = labs.map(e => [e, e.getBoundingClientRect()]);
        for (let i = 0; i < bx.length; i++) for (let j = i+1; j < bx.length; j++) {
          const a = bx[i][1], c = bx[j][1];
          const ox = Math.min(a.right, c.right) - Math.max(a.left, c.left);
          const oy = Math.min(a.bottom, c.bottom) - Math.max(a.top, c.top);
          if (ox > 1 && oy > 1)
            out.push([bx[i][0].textContent.trim().slice(0,28), bx[j][0].textContent.trim().slice(0,28), Math.round(ox)]);
        }
      }
      return {out, seen};
    });
    SEEN += d.seen;
    if (d.out.length) console.log(`${name.padEnd(14)} ${d.out.length} overlapping pair(s), worst ` +
      JSON.stringify(d.out.sort((a,c)=>c[2]-a[2])[0]));
  }
  await b.close();
  console.log('labels examined: ' + SEEN);
})();
