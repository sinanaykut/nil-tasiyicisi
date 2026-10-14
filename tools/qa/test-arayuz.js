// v28 arayüz: plays a few days on desktop and phone through the new hub screen
// usage: node test-arayuz.js <preview.html> [outPrefix]
const { chromium } = require('playwright');
const path = require('path');
const W = ms => new Promise(r => setTimeout(r, ms));
const HTML = process.argv[2], PRE = process.argv[3] || 'ta', D3 = process.env.D3 === '1';
const ROOT = '/tmp/claude-0/-home-claude/50408ee7-81cd-5d20-8660-e495325793de/scratchpad';
const SKIP = JSON.stringify({ rep:4, lv:{}, ach:{}, runs:3, noHints:true, tutDone:true, seenFeat:['haggle','crisis','sethi','quest','contra','desert','atolye','tekne'] });
let fails = 0;
const ok = (c, m) => { console.log((c ? '  ok   ' : '  FAIL ') + m); if (!c) fails++; };

async function settle(p, max = 30) {
  /* close whatever sheet stands between us and the port */
  for (let i = 0; i < max; i++) {
    const st = await p.evaluate(() => { const N = window.__nil; return { veil:!document.querySelector('#veil').hidden, pz:N.PZ && N.PZ.kind, sea:document.body.classList.contains('at-sea'), map:!document.querySelector('#voy').hidden }; });
    if (st.pz) { await p.evaluate(async () => { const N = window.__nil; if (!N.PZ) return; if (N.PZ.kind === 'temple') N.fn.templeAutoSolve(); else if (N.PZ.kind === 'senet') N.fn.senetAuto({ fast:true }); else if (N.PZ.kind === 'baboon') N.fn.baboonAuto(); else document.querySelector('[data-act="pzCancel"]') && document.querySelector('[data-act="pzCancel"]').click(); }); await W(st.pz === 'senet' ? 12000 : st.pz === 'baboon' ? 14000 : 2500); continue; }
    if (st.sea) { await p.evaluate(() => { const b = document.querySelector('[data-act="quick"]'); if (b) b.click(); }); await W(500); continue; }
    if (!st.veil) return true;
    await p.evaluate(() => {
      const q = s => document.querySelector('#sheet ' + s);
      for (const s of ['[data-act="unlockOk"]', '[data-act="qDecline"]', '[data-act="event"]', '[data-choice]:not([data-choice="0"]):not(:disabled)', '[data-choice="0"]:not(:disabled)', '[data-act="land"]', '[data-act="dlgNext"]:not(.done)', '#dlgCh [data-dlg]:last-child', '[data-close]']) { const e = q(s); if (e && !e.disabled) { e.click(); return s; } }
      window.__nil.fn.closeSheet();
    });
    await W(350);
  }
  return false;
}
async function dlgAll(p) {
  /* tap the speech box until the choices show */
  for (let i = 0; i < 12; i++) { const n = await p.evaluate(() => { const c = document.querySelectorAll('#dlgCh [data-dlg]').length; if (c) return c; const b = document.querySelector('#sheet .dlg-box'); if (b) b.click(); return 0; }); if (n) return n; await W(150); }
  return 0;
}
async function sail(p, d) {
  const r = await p.evaluate(d => window.__nil.fn.travelTo(d), d);
  for (let i = 0; i < 40; i++) { if (await p.evaluate(() => document.body.classList.contains('at-sea'))) break; await W(200); }
  await settle(p); return r;
}
async function fits(p, label) {
  const r = await p.evaluate(() => {
    const vh = innerHeight, vw = innerWidth, de = document.documentElement;
    const out = [...document.querySelectorAll('.tile, .abar, .mhd, #stage, .hud')].filter(e => e.offsetParent).filter(e => { const b = e.getBoundingClientRect(); return b.bottom > vh + 1 || b.right > vw + 1 || b.left < -1; }).map(e => e.className || e.id);
    const g = document.querySelector('#mgrid'); const gs = g ? g.scrollHeight - g.clientHeight : 0;
    return { sh:de.scrollHeight, vh, sw:de.scrollWidth, vw, out, gs };
  });
  ok(r.sh <= r.vh && r.sw <= r.vw && !r.out.length && r.gs <= 1, label + ' fits without scrolling (' + r.sw + 'x' + r.sh + ' in ' + r.vw + 'x' + r.vh + ', grid overflow ' + r.gs + (r.out.length ? ', out: ' + r.out.join(',') : '') + ')');
}
async function newGame(p, meta) {
  await p.addInitScript(([m, d3]) => { try { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); if (m) localStorage.setItem('nil-kervanci-meta10', m); localStorage.setItem('nil-kervanci-3d', d3 ? '1' : '0'); sessionStorage.setItem('seeded', '1'); } } catch (e) {} }, [meta, D3]);
  await p.goto('file://' + HTML + '?debug'); await W(D3 ? 1500 : 500);
  await p.evaluate(() => { try { window.__nil.V3.river.adapt = false; } catch (e) {} document.querySelector('[data-act="new"]').click(); }); await W(400);
  await p.evaluate(() => { const h = document.querySelector('#sheet [data-act="heroGo"]'); if (h) h.click(); }); await W(D3 ? 2500 : 500);
  /* v35+: the papyrus curtain delays the first sheet: wait for it (max 4 s) */
  if (!meta) for (let i = 0; i < 20; i++) { if (await p.evaluate(() => window.__nil.fn.state().sheet === 'say')) break; await W(200); }
}

(async () => {
  const b = await chromium.launch({ args:['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  for (const vp of [{ n:'d', o:{ viewport:{ width:1280, height:720 } } }, { n:'m', o:{ viewport:{ width:412, height:915 }, isMobile:true, hasTouch:true } }]) {
    console.log('== viewport ' + vp.n);
    const ctx = await b.newContext(vp.o), p = await ctx.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_|net::/.test(m.text())) errs.push('console: ' + m.text()); });
    await ctx.route('https://fonts.googleapis.com/**', r => r.abort()); await ctx.route('https://fonts.gstatic.com/**', r => r.abort());
    await ctx.route('https://cdnjs.cloudflare.com/**', r => r.fulfill({ path:ROOT + '/vendor/node_modules/three/build/three.min.js', contentType:'application/javascript' }));
    /* ---- 0. closing the hero pick before any game goes back to the title ---- */
    {
      const c0 = await b.newContext(vp.o); await c0.route('https://fonts.googleapis.com/**', r => r.abort()); const p0 = await c0.newPage();
      await p0.goto('file://' + HTML + '?debug'); await W(500);
      await p0.evaluate(() => document.querySelector('[data-act="new"]').click()); await W(300);
      await p0.evaluate(() => document.querySelector('#sheet .sh-h .x').click()); await W(400);
      ok(await p0.evaluate(() => window.__nil.fn.state().sheet === 'title' && !!document.querySelector('#sheet [data-act="new"]')), 'hero pick: X before any game returns to the title');
      await c0.close();
    }
    /* ---- 1. Paneb's intro on a first run ---- */
    await newGame(p, null);
    let st = await p.evaluate(() => Object.assign(window.__nil.fn.state(), { txt:document.querySelector('#sheet').innerText }));
    ok(st.sheet === 'say' && /Paneb/.test(st.txt), 'Paneb greets on the first run');
    await p.screenshot({ path:PRE + '-' + vp.n + '-intro.png' });
    await dlgAll(p);
    await p.evaluate(() => document.querySelector('#dlgCh [data-dlg="0"]').click()); await W(400);
    st = await p.evaluate(() => ({ g:window.__nil.meta.guide.step, tut:!document.querySelector('#tut').hidden, tgt:!!document.querySelector('.tut-target[data-spot="market"]') }));
    ok(st.g === 'market' && st.tut && st.tgt, 'guide points at the market spot (' + JSON.stringify(st) + ')');
    await p.screenshot({ path:PRE + '-' + vp.n + '-guide1.png' });
    /* tap the market in the picture */
    await p.click(await p.evaluate(() => document.querySelector('#spots [data-spot="market"]') ? '#spots [data-spot="market"]' : document.querySelector('#port .v3t-l[data-spot="market"]:not([hidden])') ? '#port .v3t-l[data-spot="market"]' : '#port .pscene [data-spot="market"]'), { force:true }); await W(300); await dlgAll(p);
    st = await p.evaluate(() => ({ sheet:window.__nil.fn.state().sheet, mark:!!document.querySelector('#dlgCh .tut-target') }));
    if (vp.n === 'm') ok(await p.evaluate(() => document.body.classList.contains('mk-open')), 'phone: tapping the market opens the market sheet');
    else { ok(st.sheet === 'say' && st.mark, 'merchant dialogue opens from the picture and Paneb marks "Pazar"');
    await p.evaluate(() => document.querySelector('#dlgCh [data-dlg="0"]').click()); await W(400); }
    st = await p.evaluate(() => ({ g:window.__nil.meta.guide.step, t:document.querySelector('.tut-target') && document.querySelector('.tut-target').dataset.tile }));
    ok(st.g === 'buy' && !!st.t, 'guide moves to buying, points at a tile (' + st.t + ')');
    const gid = st.t;
    await p.click('.tile[data-tile="' + gid + '"]'); await W(250);
    await p.click('.abar .chip[data-qty="Infinity"]'); await W(250);
    await p.click('.abar [data-buy="' + gid + '"]'); await W(400);
    st = await p.evaluate(g => ({ n:window.__nil.S.inv[g].n, g:window.__nil.meta.guide.step }), gid);
    ok(st.n > 0 && st.g === 'ship', 'bought ' + st.n + ' ' + gid + ' through the action bar; guide moves to the ship');
    await fits(p, 'port screen with a selection');
    await p.screenshot({ path:PRE + '-' + vp.n + '-guide2.png' });
    if (vp.n === 'm') { await W(900); ok(await p.evaluate(() => !document.body.classList.contains('mk-open')), 'phone: market sheet closes after buying'); await p.click('#mbar [data-act="travel"]'); }
    else await p.click(await p.evaluate(() => document.querySelector('#spots [data-spot="ship"]') ? '#spots [data-spot="ship"]' : document.querySelector('#port .v3t-l[data-spot="ship"]:not([hidden])') ? '#port .v3t-l[data-spot="ship"]' : '#port .pscene [data-spot="ship"]'), { force:true });
    await W(600);
    st = await p.evaluate(() => ({ sheet:window.__nil.fn.state().sheet, coach:!!document.querySelector('#sheet .coach'), mark:document.querySelector('#sheet .tut-target') && document.querySelector('#sheet .tut-target').dataset.city }));
    ok(st.sheet === 'travel' && st.coach && st.mark != null, 'ship opens the travel sheet; Paneb points at ' + st.mark);
    await p.screenshot({ path:PRE + '-' + vp.n + '-travel-guide.png' });
    await p.click('#sheet [data-city="' + st.mark + '"]:visible'); await W(300);
    st = await p.evaluate(() => ({ g:window.__nil.meta.guide.step, go:!!document.querySelector('#sheet [data-act="go"].tut-target') }));
    ok(st.g === 'sail' && st.go, 'city picked; guide points at "Yelken aç"');
    await p.click('#sheet [data-act="go"]');
    for (let i = 0; i < 40; i++) { if (await p.evaluate(() => document.body.classList.contains('at-sea'))) break; await W(200); }
    st = await p.evaluate(() => ({ sea:document.body.classList.contains('at-sea'), g:window.__nil.meta.guide.step }));
    ok(st.sea && st.g === 'voyage', 'set sail from the travel sheet');
    await p.evaluate(() => document.querySelector('[data-act="quick"]').click()); await W(800);
    await settle(p);
    ok(await p.evaluate(() => window.__nil.fn.hull() === window.__nil.S.hull && window.__nil.fn.dmgStage() === 0), 'the first quick crossing is gentle: no damage');
    st = await p.evaluate(() => window.__nil.meta.guide.step);
    ok(st === 'sell' || st === 'done', 'after landing Paneb teaches selling (' + st + ')');
    await p.screenshot({ path:PRE + '-' + vp.n + '-guide-sell.png' });
    /* the first visit to a place gets one line of explanation */
    await p.evaluate(() => window.__nil.fn.openSpot('board')); await W(300); await dlgAll(p);
    st = await p.evaluate(() => ({ sheet:window.__nil.fn.state().sheet, txt:document.querySelector('#sheet').innerText }));
    ok(st.sheet === 'say' && /Paneb/.test(st.txt) && /Sipariş/.test(st.txt), 'first visit to the board: Paneb explains it (' + st.sheet + ': ' + st.txt.slice(0, 60).replace(/\n/g, ' ') + ')');
    await p.evaluate(() => document.querySelector('#dlgCh [data-dlg="0"]').click()); await W(400);
    ok(await p.evaluate(() => window.__nil.fn.state().sheet === 'board'), '...then the board opens');
    await p.evaluate(() => window.__nil.fn.closeSheet()); await W(200);
    await p.evaluate(() => window.__nil.fn.openSpot('board')); await W(300);
    ok(await p.evaluate(() => window.__nil.fn.state().sheet === 'board'), 'second visit goes straight to the board');
    await p.evaluate(() => window.__nil.fn.closeSheet()); await W(200);
    /* turn the guide off for the rest */
    await p.evaluate(() => window.__nil.fn.guideOff()); await W(200);
    ok(await p.evaluate(() => document.querySelector('#tut').hidden), 'guide can be switched off');
    await ctx.close();

    /* ---- 2. a seasoned player: market, haggle fallback, gift, travel, desert, repair, places ---- */
    const ctx2 = await b.newContext(vp.o); await ctx2.route('https://fonts.googleapis.com/**', r => r.abort()); await ctx2.route('https://cdnjs.cloudflare.com/**', r => r.fulfill({ path:ROOT + '/vendor/node_modules/three/build/three.min.js', contentType:'application/javascript' })); await ctx2.route('https://fonts.gstatic.com/**', r => r.abort()); const q = await ctx2.newPage();
    q.on('pageerror', e => errs.push(e.message)); q.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_|net::/.test(m.text())) errs.push('console: ' + m.text()); });
    await newGame(q, SKIP); await settle(q);
    await W(400); await q.screenshot({ path:PRE + '-' + vp.n + '-c1.png' });
    await fits(q, 'port screen');
    ok(await q.evaluate(() => !document.querySelector('#route') && !document.querySelector('#news') && !document.querySelector('#cargoBox')), 'old travel strip, news ticker and cargo box are gone');
    const spots = await q.evaluate(() => window.__nil.fn.spots());
    ok(['market', 'ship', 'temple', 'tavern', 'yard', 'hapu', 'board'].every(k => spots.includes(k)), 'Mennefer places: ' + spots.join(','));
    const t3 = await q.evaluate(() => { const t = window.__nil.fn.town(); return t && t.on ? window.__nil.fn.spots().map(k => { const w = t.where(k); return { k, w:w ? Math.round(w.w) : 0, h:w ? Math.round(w.h) : 0 }; }) : null; });
    if (D3) ok(!!t3 && t3.every(x => x.w >= 30 && x.h >= 20), '3D town is live and every place has a spot (' + JSON.stringify(t3) + ')');
    if (D3) ok(await q.evaluate(() => !document.querySelector('#spots [data-spot]')), '3D: no HTML pins over the town');
    const pins = t3 ? [{ k:'3d', in:true, w:99, h:99 }] : await q.evaluate(() => [...document.querySelectorAll(document.querySelector('#spots [data-spot]') ? '#spots [data-spot]' : '#port .pscene [data-spot]')].map(e => { const r = e.getBoundingClientRect(), s = document.querySelector('#stage').getBoundingClientRect(); return { k:e.dataset.spot, in:r.left >= s.left - 1 && r.right <= s.right + 1 && r.top >= s.top - 1 && r.bottom <= s.bottom + 1, w:r.width, h:r.height }; }));
    const tagged = await q.evaluate(() => !!document.querySelector('#spots .stag'));
    if (tagged) { const sv = await q.evaluate(() => [...document.querySelectorAll('#port .pscene [data-spot]')].map(e => { const r = e.getBoundingClientRect(); return { k:e.dataset.spot, w:r.width, h:r.height }; })); ok(sv.every(x => x.w >= 40 && x.h >= 30), 'phone: every place in the picture is a big tap target (' + sv.map(x => x.k + ':' + Math.round(x.w) + 'x' + Math.round(x.h)).join(' ') + ')'); }
    ok(pins.length && pins.every(x => x.in && (tagged || (x.w >= 36 && x.h >= 30))), 'every pin is inside the picture and big enough to tap (' + pins.map(x => x.k + ':' + Math.round(x.w) + 'x' + Math.round(x.h)).join(' ') + ')');
    const hold = await q.evaluate(() => { const h = document.querySelector('#hold').getBoundingClientRect(), s = document.querySelector('#stage').getBoundingClientRect(); return h.width > 0 && h.left >= s.left && h.right <= s.right && h.bottom <= s.bottom; });
    ok(hold, 'the hold sits inside the picture next to the ship');
    /* buy / sell through hooks and the bar */
    let r = await q.evaluate(() => { const N = window.__nil; const a = N.fn.buyN('bugday', 10); const c1 = N.S.cash; const s = N.fn.sellN('bugday', 4); return { a, s, n:N.S.inv.bugday.n, cash:N.S.cash > c1 }; });
    ok(r.a === 10 && r.s === 4 && r.n === 6 && r.cash, 'buyN/sellN: bought 10, sold 4, cash went up');
    r = await q.evaluate(() => { const N = window.__nil, q0 = N.fn.quoteBuy('bugday', 12); const d = N.fn.dealBuy('bugday', q0.n, q0.cost / q0.n); return { q:q0.cost, d:d.cost, n:d.n, qn:q0.n }; });
    ok(r.n > 0 && r.n === r.qn && r.d >= r.q, 'a 0% haggle never beats the normal price (normal ' + r.q + ', haggle ' + r.d + ')');
    await q.evaluate(() => window.__nil.fn.sellN('bugday', 30));
    await q.evaluate(() => window.__nil.fn.market && window.__nil.fn.market(true)); await W(300);
    await q.click('.tile[data-tile="bugday"]').catch(() => {}); await W(200);
    const tileSel = await q.evaluate(() => window.__nil.fn.state().msel);
    if (tileSel !== 'bugday') await q.click('.tile[data-tile="bugday"]');
    const inv0 = await q.evaluate(() => ({ n:window.__nil.S.inv.bugday.n, cash:window.__nil.S.cash }));
    await q.click('.abar [data-act="hag28"]'); await W(400);
    st = await q.evaluate(() => ({ n:document.querySelector('.abar .qstep b') && +document.querySelector('.abar .qstep b').textContent, hint:document.querySelector('.abar .hgh') && document.querySelector('.abar .hgh').textContent }));
    ok(st.n > 0 && !!st.hint, 'haggle setup shows the amount (' + st.n + ') and one plain hint: ' + st.hint);
    await q.screenshot({ path:PRE + '-' + vp.n + '-hgsetup.png' });
    await q.click('.abar [data-hgq="-1"]'); await W(150);
    ok(await q.evaluate(n => +document.querySelector('.abar .qstep b').textContent === n - 1, st.n), 'the amount can be changed');
    if (await q.evaluate(() => typeof window.__nil.fn.haggleAuto === 'function')) {
      /* leaving before any offer does not use up the good's haggle */
      await q.click('.abar [data-act="hgStart"]'); await W(500);
      await q.evaluate(() => { const l = document.querySelector('#sheet [data-hg="leave"]'); if (l) l.click(); }); await W(300);
      await q.evaluate(() => { const d = document.querySelector('#sheet [data-hg="done"]'); if (d) d.click(); }); await W(300);
      ok(await q.evaluate(() => window.__nil.fn.canHaggle28('bugday')), 'leaving before an offer keeps today\'s haggle');
      await settle(q); await q.evaluate(() => window.__nil.fn.pick('bugday')); await W(150);
      await q.click('.abar [data-act="hag28"]'); await W(300);
    }
    await q.click('.abar [data-act="hgStart"]'); await W(500);
    await dlgAll(q); await q.evaluate(() => { const b = document.querySelector('#dlgCh [data-dlg="0"]'); if (b && /Anladım/.test(b.innerText)) b.click(); }); await W(400);
    st = await q.evaluate(() => ({ sheet:window.__nil.fn.state().sheet, pz:window.__nil.PZ && window.__nil.PZ.kind, hd:!!window.__nil.fn.haggleAuto }));
    ok(/hagpick|face|haggle|say|pz/.test(st.sheet) || st.pz === 'haggle', 'Pazarlık opens a haggle (sheet ' + st.sheet + ', pz ' + st.pz + ')');
    await q.screenshot({ path:PRE + '-' + vp.n + '-haggle.png' });
    if (st.pz === 'haggle') {
      await q.evaluate(() => window.__nil.fn.haggleAuto('read', { ms:120 })); 
      for (let i = 0; i < 40 && await q.evaluate(() => !!(window.__nil.PZ && window.__nil.PZ.kind === 'haggle')); i++) await W(250);
      r = await q.evaluate(() => ({ k:Object.keys(window.__nil.S.hg28 || {}), n:window.__nil.S.inv.bugday.n, cash:window.__nil.S.cash, veil:!document.querySelector('#veil').hidden }));
      ok(r.k.some(k => /:bugday$/.test(k)), 'haggleDeal settled once for buğday today (' + r.k.join(',') + '), stock ' + inv0.n + '→' + r.n + ', cash ' + inv0.cash + '→' + r.cash);
      await q.click('.tile[data-tile="bugday"]').catch(() => {}); await W(150);
      ok(await q.evaluate(() => { const b = document.querySelector('.abar [data-act="hag28"]'); return !b || b.disabled; }), 'one haggle per good per day: the button is now off');
    } else {
      await q.evaluate(() => { const b = document.querySelector('#sheet [data-hag="face"]'); if (b) b.click(); }); await W(300);
      await q.evaluate(() => { const b = document.querySelector('#sheet [data-act="faceOk"]'); if (b) b.click(); }); await W(400);
      r = await q.evaluate(() => ({ h:window.__nil.S.haggle, n:window.__nil.S.stats.haggles }));
      ok(!!r.h || r.n > 0, 'fallback face-reading haggle settles a bonus');
    }
    await settle(q);
    /* gift: Ptahhotep loves a Book of the Dead */
    r = await q.evaluate(() => { const N = window.__nil; N.S.inv.kitap.n = 1; N.S.hull = 1; N.render(); return N.S.trust[1]; });
    await q.evaluate(() => window.__nil.fn.showMerchant()); await W(300); await dlgAll(q);
    await q.evaluate(() => [...document.querySelectorAll('#dlgCh [data-dlg]')].find(b => /Hediye/.test(b.innerText)).click()); await W(1400);
    await q.screenshot({ path:PRE + '-' + vp.n + '-gift.png' });
    let g2 = await q.evaluate(() => ({ g:window.__nil.S.gifted[1], t:window.__nil.S.trust[1], k:window.__nil.S.inv.kitap.n, hull:window.__nil.fn.hull() }));
    ok(g2.g && g2.t >= r + 450 && g2.k === 0 && g2.hull >= 3, 'gift: book given, trust ' + r + '→' + g2.t + ', hull mended to ' + g2.hull);
    await settle(q);
    /* the merchant dialog: Sohbet changes the line, Pazar closes to the grid */
    await q.evaluate(() => window.__nil.fn.showMerchant()); await W(300); await dlgAll(q);
    await q.screenshot({ path:PRE + '-' + vp.n + '-merchant.png' });
    await q.evaluate(() => document.querySelector('#dlgCh [data-dlg="0"]').click()); await W(300);
    ok(await q.evaluate(() => document.querySelector('#veil').hidden && document.querySelector('#mgrid').classList.contains('flash')), '"Pazar" closes the dialogue and flashes the grid');
    /* the hero card (HUD profile and the town spot) */
    await q.evaluate(() => window.__nil.fn.openSpot('hero')); await W(200); await dlgAll(q);
    ok(await q.evaluate(() => window.__nil.fn.state().sheet === 'say' && !!document.querySelector('#sheet .hstats')), 'hero spot opens the hero card with the run so far');
    await settle(q);
    await q.evaluate(() => document.querySelector('#hplate').click()); await W(200); await dlgAll(q);
    ok(await q.evaluate(() => window.__nil.fn.state().sheet === 'say' && !!document.querySelector('#sheet .hcard')), 'HUD portrait opens the hero card');
    await q.screenshot({ path:PRE + '-' + vp.n + '-herocard.png' });
    await settle(q);
    ok(await q.evaluate(() => !document.querySelector('.mhrow .hmini')), 'no hero portrait in the market header');
    /* board, yard (repair), hapu */
    await q.evaluate(() => window.__nil.fn.openSpot('board')); await W(500);
    ok(await q.evaluate(() => window.__nil.fn.state().sheet === 'board' && /Siparişler/.test(document.querySelector('#sheet').innerText)), 'board shows orders, Sethi and crises');
    await q.screenshot({ path:PRE + '-' + vp.n + '-board.png' });
    await q.evaluate(() => { const a = document.querySelector('#sheet [data-act="accept"]'); if (a) a.click(); }); await W(200);
    await settle(q);
    r = await q.evaluate(() => { const N = window.__nil; N.S.cash = Math.max(N.S.cash, 800); N.S.hull = 1; N.render(); N.fn.openSpot('yard'); return { d:N.fn.dmgStage(), cash:N.S.cash }; });
    await W(500);
    await q.screenshot({ path:PRE + '-' + vp.n + '-yard.png' });
    await q.evaluate(() => document.querySelector('#sheet [data-act="repairAll"]').click()); await W(300);
    g2 = await q.evaluate(() => ({ hull:window.__nil.fn.hull(), d:window.__nil.fn.dmgStage(), cash:window.__nil.S.cash }));
    ok(r.d === 3 && g2.d === 0 && r.cash - g2.cash === 120, 'yard: stage ' + r.d + ' → ' + g2.d + ' for ' + (r.cash - g2.cash) + ' deben (2 × 60 in Mennefer)');
    await settle(q);
    await q.evaluate(() => window.__nil.fn.openSpot('hapu')); await W(300); await dlgAll(q);
    await q.screenshot({ path:PRE + '-' + vp.n + '-hapu.png' });
    ok(await q.evaluate(() => /Hapu/.test(document.querySelector('#sheet').innerText)), 'Hapu\'s house opens a dialogue');
    await settle(q);
    /* temple and tavern by tapping the picture */
    await q.evaluate(() => window.__nil.fn.openSpot('temple')); await W(500);
    ok(await q.evaluate(() => window.__nil.PZ && window.__nil.PZ.kind === 'temple'), 'temple spot opens the light puzzle');
    await settle(q);
    ok(await q.evaluate(() => !!window.__nil.S.temple[1]), 'temple solved and remembered');
    await q.evaluate(() => window.__nil.fn.openSpot('tavern')); await W(300); await dlgAll(q);
    await q.screenshot({ path:PRE + '-' + vp.n + '-tavern.png' });
    await q.evaluate(() => { const b = document.querySelector('#dlgCh [data-dlg="0"]'); if (b) b.click(); }); await W(600);
    ok(await q.evaluate(() => window.__nil.PZ && window.__nil.PZ.kind === 'senet'), 'tavern dialogue starts Senet');
    await settle(q);
    ok(await q.evaluate(() => window.__nil.S.tavern[1] === window.__nil.S.day), 'Senet played today');
    /* travel to two cities */
    const reach = () => q.evaluate(() => window.__nil.fn.mapModel().cities.filter(c => c.reach).map(c => c.i));
    let hubC = null;
    for (const pref of [[2, 0, 3, 4], [3, 2, 4, 0]]) {
      const rc = await reach(), cur = await q.evaluate(() => window.__nil.S.city), dest = pref.find(i => i !== cur && rc.includes(i));
      hubC = dest;
      r = await sail(q, dest);
      st = await q.evaluate(() => ({ c:window.__nil.S.city, d:window.__nil.S.day }));
      if (!(r && st.c === dest)) console.log('    debug', r, JSON.stringify(await q.evaluate(() => ({ s:window.__nil.fn.state(), veil:!document.querySelector('#veil').hidden, t:document.querySelector('#sheet').innerText.slice(0, 90), sea:document.body.classList.contains('at-sea') }))));
      ok(r && st.c === dest, 'sailed to ' + dest + ' (day ' + st.d + ')');
      await fits(q, 'port at city ' + dest);
      await q.screenshot({ path:PRE + '-' + vp.n + '-c' + dest + '.png' });
    }
    /* workshop here (Abidos, Vaset or Per-Bastet) */
    await q.evaluate(() => { const N = window.__nil, S = N.S; Object.assign(S.inv.papirus, { n:10 }); Object.assign(S.inv.bakir, { n:2 }); Object.assign(S.inv.tuz, { n:4 }); Object.assign(S.inv.tutsu, { n:1 }); Object.assign(S.inv.sarap, { n:2 }); Object.assign(S.inv.hurma, { n:4 }); S.cash += 300; N.render(); N.fn.openSpot('work'); }); await W(400);
    ok(await q.evaluate(() => window.__nil.fn.state().sheet === 'work'), 'workshop spot opens the workshop');
    await q.evaluate(() => { const b = document.querySelector('#sheet [data-act="workGo"]'); if (b) b.click(); }); await W(300);
    ok(await q.evaluate(() => (window.__nil.S.work || []).length === 1), 'workshop job started');
    await settle(q);
    /* desert caravan round trip from this hub and back */
    const dzC = { 1:5, 2:6, 3:7 }[hubC];
    r = await sail(q, dzC);
    st = await q.evaluate(() => ({ c:window.__nil.S.city, k:!!window.__nil.S.caravan }));
    ok(r && st.c === dzC && st.k, 'caravan reached desert city ' + dzC);
    await fits(q, 'port in the desert');
    await q.screenshot({ path:PRE + '-' + vp.n + '-c' + dzC + '.png' });
    await q.evaluate(() => window.__nil.fn.showTravel()); await W(500);
    ok(await q.evaluate(h => window.__nil.fn.state().sel === h, hubC), 'in the desert the hub is preselected');
    await q.screenshot({ path:PRE + '-' + vp.n + '-travel-desert.png' });
    await q.evaluate(() => document.querySelector('#sheet [data-act="go"]').click());
    for (let i = 0; i < 40; i++) { if (await q.evaluate(() => document.body.classList.contains('at-sea'))) break; await W(200); }
    await settle(q);
    st = await q.evaluate(() => ({ c:window.__nil.S.city, k:!!window.__nil.S.caravan }));
    ok(st.c === hubC && !st.k, 'caravan back at the hub, boat reloaded');
    /* damage persists: arrive with a hurt hull and Paneb asks for the yard */
    await q.evaluate(() => { const N = window.__nil; N.S.repNag = false; });
    r = await q.evaluate(() => { const N = window.__nil, S = N.S; const dest = [2, 4].find(i => N.fn.mapModel().cities.find(c => c.i === i && c.reach)); return dest; });
    await q.evaluate(d => window.__nil.fn.travelTo(d), r);
    for (let i = 0; i < 40; i++) { if (await q.evaluate(() => !!window.__nil.vg())) break; await W(200); }
    await q.evaluate(() => { const v = window.__nil.vg(); if (v) v.hp = 1; });
    await W(800); await q.screenshot({ path:PRE + '-' + vp.n + '-sea.png' });
    await q.evaluate(() => document.querySelector('[data-act="quick"]').click()); await W(900);
    await q.evaluate(() => { const b = document.querySelector('#sheet [data-act="land"]') || document.querySelector('#sheet [data-act="event"]'); if (b) b.click(); }); await W(400);
    for (let i = 0; i < 10; i++) { const sh = await q.evaluate(() => window.__nil.fn.state().sheet); if (sh === 'say') break; await q.evaluate(() => { const b = document.querySelector('#sheet [data-choice="1"], #sheet [data-choice="0"]:not(:disabled), #sheet [data-act="land"]'); if (b) b.click(); }); await W(500); }
    st = await q.evaluate(() => ({ hull:window.__nil.fn.hull(), d:window.__nil.fn.dmgStage(), sheet:window.__nil.fn.state().sheet, txt:document.querySelector('#sheet').innerText.slice(0, 80) }));
    ok(st.hull <= 1 && st.d === 3 && st.sheet === 'say' && /Paneb/.test(st.txt), 'hull stays damaged after landing (' + st.hull + ') and Paneb suggests the yard [' + st.sheet + ': ' + st.txt.replace(/\n/g, ' ') + ']');
    await q.screenshot({ path:PRE + '-' + vp.n + '-damaged.png' });
    await settle(q);
    /* save and reload */
    const before = await q.evaluate(() => ({ d:window.__nil.S.day, c:window.__nil.S.city, h:window.__nil.fn.hull(), cash:window.__nil.S.cash }));
    await q.close(); const q2 = await ctx2.newPage(); q2.on('pageerror', e => errs.push(e.message));
    await q2.goto('file://' + HTML + '?debug', { waitUntil:'domcontentloaded' }); await W(900);
    await q2.evaluate(() => document.querySelector('[data-act="cont"]').click()); await W(500); await settle(q2);
    const after = await q2.evaluate(() => ({ d:window.__nil.S.day, c:window.__nil.S.city, h:window.__nil.fn.hull(), cash:window.__nil.S.cash }));
    ok(JSON.stringify(before) === JSON.stringify(after), 'save/reload keeps day, city, hull, cash ' + JSON.stringify(after));
    /* the last day: nothing to reach, finish the season from the action bar */
    await q2.evaluate(() => { const N = window.__nil; N.S.day = N.S.days; N.render(); }); await W(300);
    await q2.evaluate(() => window.__nil.fn.market && window.__nil.fn.market(true));
    await q2.evaluate(() => window.__nil.fn.pick('bugday')); await W(200);
    await q2.evaluate(() => document.querySelector('.abar [data-act="finish"]').click()); await W(800);
    ok(await q2.evaluate(() => window.__nil.S.over && /Sefer bitti/.test(document.querySelector('#sheet').innerText)), 'last day: "Seferi bitir" in the action bar ends the season');
    await q2.screenshot({ path:PRE + '-' + vp.n + '-end.png' });
    ok(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 5).join(' | ') : ''));
    await ctx2.close();
  }
  await b.close();
  console.log(fails ? fails + ' FAILED' : 'ALL OK');
  process.exit(fails ? 1 : 0);
})();
