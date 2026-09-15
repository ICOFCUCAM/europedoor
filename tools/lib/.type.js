const {chromium} = require('playwright');
const {ALL} = require('./families.js');
(async () => {
  const b = await chromium.launch({executablePath: '/opt/pw-browsers/chromium'});
  const pg = await b.newPage({viewport: {width: 1280, height: 900}});
  const all = new Map();
  for (const [name, url] of ALL) {
    const r = await pg.goto('http://localhost:8899' + url, {waitUntil: 'load'});
    if (!r || r.status() !== 200) continue;
    const d = await pg.evaluate(() => {
      const seen = new Map();
      const walk = (n) => {
        for (const c of n.childNodes) {
          if (c.nodeType === 3 && c.textContent.trim()) {
            const cs = getComputedStyle(n);
            const k = `${Math.round(parseFloat(cs.fontSize)*10)/10}/${cs.fontWeight}/${cs.fontFamily.split(',')[0]}`;
            seen.set(k, (seen.get(k)||0) + c.textContent.trim().length);
          } else if (c.nodeType === 1 && !['SCRIPT','STYLE','SVG'].includes(c.tagName)) walk(c);
        }
      };
      walk(document.querySelector('main'));
      return [...seen.entries()];
    });
    const sizes = new Set(d.map(([k]) => k.split('/')[0]));
    console.log(`${name.padEnd(14)} ${String(sizes.size).padStart(2)} distinct sizes · ${d.length} size/weight/face combinations`);
    for (const [k,v] of d) all.set(k, (all.get(k)||0)+v);
  }
  const sizes = [...new Set([...all.keys()].map(k=>parseFloat(k)))].sort((a,b)=>a-b);
  console.log(`\nacross every family: ${sizes.length} distinct rendered sizes`);
  console.log('  ' + sizes.join(', '));
  const combos = [...all.entries()].sort((a,b)=>b[1]-a[1]);
  console.log(`  ${combos.length} size/weight/face combinations; the ten most used:`);
  for (const [k,v] of combos.slice(0,10)) console.log(`     ${k}  ${v} chars`);
  await b.close();
})();
