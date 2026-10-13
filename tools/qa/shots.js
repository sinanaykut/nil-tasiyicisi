const { chromium } = require('playwright'); const fs = require('fs');
const W = ms => new Promise(r => setTimeout(r, ms));
const ROOT = '/tmp/claude-0/-home-claude/50408ee7-81cd-5d20-8660-e495325793de/scratchpad';
const THREE = fs.readFileSync(ROOT + '/vendor/node_modules/three/build/three.min.js');
(async () => {
  const b = await chromium.launch({ args:['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  for (const [nm, vp, mob] of [['d', { width:1280, height:720 }, false], ['m', { width:412, height:915 }, true]]) {
    const p = await b.newPage({ viewport:vp, isMobile:mob, hasTouch:mob }); const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    await p.route('https://cdnjs.cloudflare.com/**', r => r.fulfill({ body:THREE, contentType:'application/javascript' }));
    await p.addInitScript(() => { localStorage.setItem('nil-kervanci-3d', '1'); localStorage.setItem('nil-kervanci-meta10', JSON.stringify({ rep:4, lv:{}, ach:{}, runs:3, noHints:true, tutDone:true, seenFeat:['haggle', 'crisis', 'sethi', 'quest', 'contra', 'desert', 'atolye', 'tekne'] })); });
    await p.goto('file://' + ROOT + '/preview33.html?debug'); await W(900);
    await p.evaluate(() => document.querySelector('[data-act="new"]').click()); await W(500); await p.evaluate(() => { const g = document.querySelector('[data-act="heroGo"]'); if (g) g.click(); }); await W(2500);
    await p.evaluate(() => { const b = document.querySelector('[data-act="qDecline"]'); if (b) b.click(); for (const s of ['[data-act="unlockOk"]']) { const e = document.querySelector(s); if (e) e.click(); } }); await W(800);
    await p.screenshot({ path:ROOT + '/qa33/s-' + nm + '-hub1.png' });
    await p.evaluate(() => __nil.fn.openSpot('market')); await W(1200);
    await p.screenshot({ path:ROOT + '/qa33/s-' + nm + '-merchant.png' });
    await p.evaluate(() => __nil.fn.closeSheet()); await W(300);
    await p.evaluate(() => __nil.fn.openSpot('ship')); await W(6000);
    await p.screenshot({ path:ROOT + '/qa33/s-' + nm + '-travel.png' });
    await p.evaluate(() => __nil.fn.closeSheet()); await W(300);
    await p.evaluate(() => { const S = __nil.S; S.city = 3; S.day = 12; S.hull = 1; __nil.render(); }); await W(6000);
    await p.screenshot({ path:ROOT + '/qa33/s-' + nm + '-vaset.png' });
    console.log(nm, errs.join('|') || 'ok');
    await p.close();
  }
  await b.close();
})();
