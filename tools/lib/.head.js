const {chromium} = require('playwright');
const ALL = require('./families.js').ALL;
(async () => {
  const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const pg = await b.newPage({viewport:{width:1280, height:900}});
  const out = [];
  for (const [name, url] of ALL) {
    const r = await pg.goto('http://localhost:8899'+url, {waitUntil:'load'});
    if (!r || r.status() !== 200) continue;
    const d = await pg.evaluate(() => {
      const h = document.querySelector('.pagehead');
      if (!h) return null;
      const H = h.getBoundingClientRect();
      if (!H.height) return null;
      // widest painted child, as a share of the head's own width
      let maxR = 0;
      for (const e of h.querySelectorAll('*')) {
        const r = e.getBoundingClientRect();
        if (!r.height || !r.width) continue;
        if (e.children.length && !e.textContent.trim() && e.tagName !== 'svg'
            && !e.querySelector('svg,img,picture')) continue;
        if (r.right > maxR) maxR = r.right;
      }
      return {used: Math.round(100 * (maxR - H.left) / H.width),
              w: Math.round(H.width), ht: Math.round(H.height),
              cls: h.className};
    });
    if (d) out.push([d.used, name, d.w, d.ht, d.cls]);
  }
  out.sort((a,c)=>a[0]-c[0]);
  for (const [u,n,w,ht,cls] of out) console.log(String(u).padStart(4)+'%', n.padEnd(14), 'head '+w+'x'+ht, cls);
  await b.close();
})();
