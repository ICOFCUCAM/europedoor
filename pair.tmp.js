const { chromium } = require("playwright"); const fs=require("fs");
(async()=>{const SP=process.env.SP;
 const imgs=process.argv.slice(2).map(f=>`<figure><img src="data:image/png;base64,${fs.readFileSync(`${SP}/${f}.png`).toString("base64")}"><figcaption>${f}</figcaption></figure>`).join("");
 fs.writeFileSync(SP+"/pair.html",`<style>body{margin:0;background:#666;display:flex;gap:8px;padding:8px;font:12px system-ui;align-items:flex-start}figure{margin:0}img{display:block;border:1px solid #222;width:640px}figcaption{color:#fff;padding:3px}</style>${imgs}`);
 const c=["/opt/pw-browsers/chromium-1194/chrome-linux/chrome","/opt/pw-browsers/chromium/chrome-linux/chrome"].filter(p=>fs.existsSync(p));
 const b=await chromium.launch(c.length?{executablePath:c[0]}:{});
 const p=await b.newPage({viewport:{width:1320,height:800}});
 await p.goto("file://"+SP+"/pair.html",{waitUntil:"load"});
 await p.screenshot({path:SP+"/PAIR.png",fullPage:true}); await b.close(); console.log("pair");})();
