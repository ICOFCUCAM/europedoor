const { chromium } = require('playwright');
(async()=>{
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const p=await b.newPage({viewport:{width:200,height:100}});
  await p.setContent(`<style>
    body{margin:0}
    .wrap .src { fill: #ff0000; }          /* on the GROUP, so the paths inherit */
    .wrap .clone { fill: #00ff00; }
  </style>
  <svg width="0" height="0"><defs><g id="g1" class="src"><path d="M10 10H60V60H10Z"/></g></defs></svg>
  <svg class="wrap" width="200" height="100" viewBox="0 0 200 100">
    <use class="clone" href="#g1" transform="translate(100,0)"/>
  </svg>`);
  const buf = await p.screenshot();
  const fs=require('fs'); fs.writeFileSync('/tmp/probe.png', buf);
  // read pixel via canvas in page
  const px = await p.evaluate(async (b64)=>{
    const img=new Image(); img.src='data:image/png;base64,'+b64;
    await img.decode();
    const c=document.createElement('canvas'); c.width=img.width;c.height=img.height;
    c.getContext('2d').drawImage(img,0,0);
    const d=c.getContext('2d').getImageData(0,0,img.width,img.height).data;
    const at=(x,y)=>{const i=(y*img.width+x)*4;return [d[i],d[i+1],d[i+2]];};
    return {source: at(130,30), clone: at(130,30)};
  }, buf.toString('base64'));
  console.log('source square', px.source, ' clone square', px.clone);
  await b.close();
})();
