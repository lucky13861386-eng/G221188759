const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport:{width:1080,height:1920}, deviceScaleFactor:1 });
  for (const kf of [1,2,3,4]) {
    await pg.goto('file://'+__dirname+'/brain_preview.html?kf='+kf);
    await pg.waitForTimeout(500);
    await pg.screenshot({ path:`kf${kf}.png` });
    console.log('kf'+kf+' shot');
  }
  await b.close();
})();
