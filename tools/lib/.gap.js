const {chromium} = require('playwright');
const ALL = require('./families.js').ALL;
(async () => {
  const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const pg = await b.newPage({viewport:{width:1280, height:900}});
  let seen = 0; const out = [];
  for (const [name, url] of ALL) {
    const r = await pg.goto('http://localhost:8899'+url, {waitUntil:'load'});
    if (!r || r.status() !== 200) continue;
    const d = await pg.evaluate(() => {
      const main = document.querySelector('main'), foot = document.querySelector('footer');
      if (!main || !foot) return null;
      // the lowest painted bottom inside main
      let low = 0, who = '';
      for (const e of main.querySelectorAll('*')) {
        const r = e.getBoundingClientRect();
        if (!r.height || !r.width) continue;
        if (e.children.length && !e.textContent.trim()) continue;
        const bot = r.bottom + scrollY;
        if (bot > low) { low = bot; who = e.tagName.toLowerCase() + '.' + (e.className||'').toString().split(' ')[0]; }
      }
      return {gap: Math.round(foot.getBoundingClientRect().top + scrollY - low), who,
              doc: document.documentElement.scrollHeight};
    });
    if (!d) continue;
    seen++;
    out.push([d.gap, name, d.who, d.doc]);
  }
  out.sort((a,c)=>c[0]-a[0]);
  for (const [g,n,w,doc] of out.slice(0,12)) console.log(String(g).padStart(5), n.padEnd(14), w, ' doc='+doc);
  console.log('pages measured: ' + seen);
  await b.close();
})();
