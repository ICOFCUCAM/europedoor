const {chromium} = require('playwright');
const {ALL} = require('./families.js');
(async () => {
  const b = await chromium.launch({executablePath: '/opt/pw-browsers/chromium'});
  const rows = [];
  for (const W of [390, 704, 834, 900, 1024, 1280, 1600]) {
    const pg = await b.newPage({viewport:{width:W, height:900}});
    for (const [name, url] of ALL) {
      const r = await pg.goto('http://localhost:8899'+url, {waitUntil:'load'});
      if (!r || r.status() !== 200) continue;
      const d = await pg.evaluate(() => {
        const h1 = document.querySelector('main h1, header.pagehead h1, .pagehead h1');
        if (!h1) return null;
        const t = h1.textContent.trim();
        const lh = parseFloat(getComputedStyle(h1).lineHeight);
        const lines = Math.max(1, Math.round(h1.getBoundingClientRect().height / lh));
        return {chars: t.length, lines, per: t.length / lines, text: t.slice(0, 30)};
      });
      if (d && d.chars > 12) rows.push([W, name, d.per, d.lines, d.chars, d.text]);
    }
    await pg.close();
  }
  rows.sort((a,b)=>a[2]-b[2]);
  console.log('worst characters-per-line for an h1, any family, any width:');
  for (const r of rows.slice(0, 12))
    console.log(`  ${r[2].toFixed(1)} chars/line  ${String(r[0]).padStart(4)}px  ${r[1].padEnd(14)} ${r[4]} chars on ${r[3]} lines  "${r[5]}"`);
  const bad = rows.filter(r=>r[2]<14);
  console.log(`\n${rows.length} measurements · ${bad.length} under 14 chars per line`);
  await b.close();
})();
