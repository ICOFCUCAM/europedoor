const { chromium } = require("playwright");
const http=require("http"),fs=require("fs"),path=require("path");
const ROOT="/home/user/europedoor/site";
const T={".html":"text/html",".css":"text/css",".js":"text/javascript",".json":"application/json",".svg":"image/svg+xml",".png":"image/png"};
(async()=>{
 const srv=http.createServer((q,r)=>{let p=decodeURIComponent(q.url.split("?")[0]);let f=path.join(ROOT,p);
  if(!fs.existsSync(f)||fs.statSync(f).isDirectory()){if(fs.existsSync(f+".html"))f=f+".html";else if(fs.existsSync(path.join(f,"index.html")))f=path.join(f,"index.html");else{r.writeHead(404);return r.end()}}
  r.writeHead(200,{"Content-Type":T[path.extname(f)]||"application/octet-stream"});r.end(fs.readFileSync(f));}).listen(0);
 const base="http://127.0.0.1:"+srv.address().port;
 const c=["/opt/pw-browsers/chromium-1194/chrome-linux/chrome","/opt/pw-browsers/chromium/chrome-linux/chrome"].filter(p=>fs.existsSync(p));
 const b=await chromium.launch(c.length?{executablePath:c[0]}:{});
 const page=await b.newPage({viewport:{width:1280,height:1400}});
 await page.goto(base+process.argv[2],{waitUntil:"networkidle"});
 await page.evaluate(v=>scrollTo(0,v), +process.argv[4]);
 await page.waitForTimeout(120);
 await page.screenshot({path:`${process.env.SP}/${process.argv[3]}.png`});
 await b.close(); srv.close(); console.log("ok");
})();
