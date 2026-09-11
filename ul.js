const { chromium } = require('playwright');
const fs=require('fs'),http=require('http'),path=require('path');
const T={'.html':'text/html','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'};
(async()=>{
  const srv=http.createServer((req,res)=>{const u=decodeURIComponent(req.url.split('?')[0]);
    for(const c of [path.join('site',u),path.join('site',u,'index.html'),path.join('site',u+'.html')])
      if(fs.existsSync(c)&&fs.statSync(c).isFile()){res.writeHead(200,{'Content-Type':T[path.extname(c)]||'application/octet-stream'});return res.end(fs.readFileSync(c));}
    res.writeHead(404,{'Content-Type':'text/html'});res.end(fs.readFileSync('site/404.html'));}).listen(8330);
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const p=await b.newPage({viewport:{width:1280,height:900}});
  await p.goto('http://localhost:8330'+process.argv[2],{waitUntil:'networkidle'});
  console.log(await p.evaluate(()=>{
    const out=[];
    for (const e of document.querySelectorAll('main a')) {
      const c=getComputedStyle(e);
      if (c.textDecorationLine !== 'underline') continue;
      out.push({t:e.textContent.trim().slice(0,24), off:c.textUnderlineOffset, th:c.textDecorationThickness});
      if (out.length>3) break;
    }
    return JSON.stringify(out,null,1);
  }));
  await b.close();srv.close();
})();
