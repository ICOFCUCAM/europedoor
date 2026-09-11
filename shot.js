const { chromium } = require('playwright');
const fs=require('fs'),http=require('http'),path=require('path');
const T={'.html':'text/html','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.avif':'image/avif','.ico':'image/x-icon','.xml':'application/xml','.txt':'text/plain'};
(async()=>{
  const srv=http.createServer((req,res)=>{const u=decodeURIComponent(req.url.split('?')[0]);
    for(const c of [path.join('site',u),path.join('site',u,'index.html'),path.join('site',u+'.html')])
      if(fs.existsSync(c)&&fs.statSync(c).isFile()){res.writeHead(200,{'Content-Type':T[path.extname(c)]||'application/octet-stream'});return res.end(fs.readFileSync(c));}
    res.writeHead(404,{'Content-Type':'text/html'});res.end(fs.readFileSync('site/404.html'));}).listen(8300);
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const W=Number(process.env.W||1280),H=Number(process.env.H||900);
  for(const a of process.argv.slice(2)){
    const [url,name]=a.split('::');
    const p=await b.newPage({viewport:{width:W,height:H},colorScheme:process.env.DARK==='1'?'dark':'light'});
    await p.goto('http://localhost:8300'+url,{waitUntil:'networkidle'});
    await p.waitForTimeout(450);
    await p.screenshot({path:'/tmp/shots/'+name+'.png',fullPage:process.env.FULL==='1'});
    await p.close();
  }
  await b.close();srv.close();
})();
