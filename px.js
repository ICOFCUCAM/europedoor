const { chromium } = require('playwright');
const fs=require('fs'),http=require('http'),path=require('path');
const T={'.html':'text/html','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'};
(async()=>{
  const srv=http.createServer((req,res)=>{const u=decodeURIComponent(req.url.split('?')[0]);
    for(const c of [path.join('site',u),path.join('site',u,'index.html'),path.join('site',u+'.html')])
      if(fs.existsSync(c)&&fs.statSync(c).isFile()){res.writeHead(200,{'Content-Type':T[path.extname(c)]||'application/octet-stream'});return res.end(fs.readFileSync(c));}
    res.writeHead(404,{'Content-Type':'text/html'});res.end(fs.readFileSync('site/404.html'));}).listen(8310);
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const p=await b.newPage({viewport:{width:1280,height:900}});
  const url=process.argv[2]||'/plan';
  await p.goto('http://localhost:8310'+url,{waitUntil:'networkidle'});
  await p.waitForTimeout(400);
  const sels = process.argv.slice(3);
  console.log(await p.evaluate((S)=>{
    const o={};
    for(const s of S){ const e=document.querySelector(s); if(!e){o[s]='—';continue;}
      const c=getComputedStyle(e), r=e.getBoundingClientRect();
      o[s]={accent:c.accentColor,color:c.color,bg:c.backgroundColor,border:c.borderColor,
            cs:c.colorScheme,w:Math.round(r.width),h:Math.round(r.height)};}
    return JSON.stringify(o,null,1);
  }, sels));
  await b.close();srv.close();
})();
