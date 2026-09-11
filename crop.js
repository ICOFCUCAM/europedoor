const { chromium } = require('playwright');
const fs=require('fs'),http=require('http'),path=require('path');
const T={'.html':'text/html','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'};
(async()=>{
  const srv=http.createServer((req,res)=>{const u=decodeURIComponent(req.url.split('?')[0]);
    for(const c of [path.join('site',u),path.join('site',u,'index.html'),path.join('site',u+'.html')])
      if(fs.existsSync(c)&&fs.statSync(c).isFile()){res.writeHead(200,{'Content-Type':T[path.extname(c)]||'application/octet-stream'});return res.end(fs.readFileSync(c));}
    res.writeHead(404,{'Content-Type':'text/html'});res.end(fs.readFileSync('site/404.html'));}).listen(8311);
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const p=await b.newPage({viewport:{width:1280,height:900},deviceScaleFactor:2});
  const [url,sel,name]=process.argv.slice(2);
  await p.goto('http://localhost:8311'+url,{waitUntil:'networkidle'});
  await p.waitForTimeout(400);
  const e=p.locator(sel).first();
  await e.scrollIntoViewIfNeeded();
  await p.waitForTimeout(200);
  await e.screenshot({path:'/tmp/shots/'+name+'.png'});
  await b.close();srv.close();
})();
