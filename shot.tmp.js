const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.goto("http://127.0.0.1:8899/themes/grand-tour-europe/", { waitUntil: "networkidle" });
  await p.screenshot({ path: "/tmp/claude-0/mock/theme-new.png" });
  await b.close();
})();
