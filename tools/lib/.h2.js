const {chromium} = require('playwright');
const {ALL} = require('./families.js');
const WIDTHS = [390, 704, 834, 900, 1024, 1280, 1600];
(async () => {
  const b = await chromium.launch({executablePath: '/opt/pw-browsers/chromium'});
  const per = new Map();
  for (const W of WIDTHS) {
    const pg = await b.newPage({viewport:{width:W, height:900}});
    for (const [name, url] of ALL) {
      const r = await pg.goto('http://localhost:8899'+url, {waitUntil:'load'});
      if (!r || r.status() !== 200) continue;
      const d = await pg.evaluate(() => {
        const h1 = document.querySelector('.pagehead h1, main h1');
        if (!h1) return null;
        const lh = parseFloat(getComputedStyle(h1).lineHeight);
        return {lines: Math.max(1, Math.round(h1.getBoundingClientRect().height/lh)),
                chars: h1.textContent.trim().length};
      });
      if (!d) continue;
      if (!per.has(name)) per.set(name, {});
      per.get(name)[W] = d;
    }
    await pg.close();
  }
  console.log('a head worse in the middle of its range than at both ends:');
  let n = 0;
  for (const [name, m] of per) {
    for (let i = 1; i < WIDTHS.length - 1; i++) {
      const a = m[WIDTHS[i-1]], c = m[WIDTHS[i]], d = m[WIDTHS[i+1]];
      if (!a || !c || !d) continue;
      if (c.lines > a.lines && c.lines > d.lines) {
        n++;
        console.log(`  ${name.padEnd(14)} ${WIDTHS[i]}px: ${c.lines} lines, against ${a.lines} at ${WIDTHS[i-1]} and ${d.lines} at ${WIDTHS[i+1]}  (${c.chars} chars)`);
      }
    }
  }
  if (!n) console.log('  none');
  await b.close();
})();
