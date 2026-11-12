// v28 (arayüz): the old v19 full-run bot, driven through the __nil.fn hooks of the new hub screen
// v19 full runs: a bot trades, sails real voyages (scenes played by an in-page bot), follows the story and finishes
const { assertRunComplete } = require('./run-status.js');
const W = ms => new Promise(r => setTimeout(r, ms));
const BOT = () => {
  const N = window.__nil; let lastB = 0; const keys = {};
  const key = (k, on) => { if (!!keys[k] === on) return; keys[k] = on; window.dispatchEvent(new KeyboardEvent(on ? 'keydown' : 'keyup', { key:k })); };
  setInterval(() => {
    if (N.fn.combatState && N.fn.combatState()) { N.fn.combatBot(); return; }
    if (N.fn.desertBot) N.fn.desertBot();   /* v48: the desert road's own scenes (DOM, not Sea) */
    const st = N.Sea.peek(); if (!st || st.end || st.count > 0) { N.Sea.setPad('L', false); N.Sea.setPad('R', false); ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].forEach(k => key(k, false)); return; }
    const g = N.Sea.geo();
    if (st.cfg) {
      let push = 0;
      for (const o of st.obs) { const ahead = o.y - st.dist; if (ahead < -20 || ahead > 260 || o.k === 'whirl') continue; const du = o.u - st.u, w = (o.k === 'log' ? o.len * 0.45 : o.k === 'sand' ? o.w * 0.45 : o.r) / g.hw + 0.13; if (Math.abs(du) < w) push += (du > 0 ? -1 : 1) * (1 - ahead / 300) * 2; }
      (st.patrols || []).forEach(p => { const ahead = p.y - st.dist; if (ahead > -60 && ahead < 300) { const du = p.u - st.u; if (Math.abs(du) < 0.6) push += (du > 0 ? -1 : 1) * 1.5; } });
      if (Math.abs(st.u) > 0.7) push += -Math.sign(st.u) * 0.6;
      N.Sea.setPad('L', push < -0.15); N.Sea.setPad('R', push > 0.15);
      if (st.chaser && st.chaser.on && performance.now() - lastB > 700) { N.Sea.boost(); lastB = performance.now(); }
    } else if (st.kind === 'storm') {
      const want = st.gust && st.gust.warn < 0.25 ? -st.gust.dir : (Math.abs(st.a) > 0.25 ? -Math.sign(st.a) : 0);
      N.Sea.setPad('L', want < 0); N.Sea.setPad('R', want > 0);
      if (st.charges > 0 && st.boxes.some(b => b.on && !b.lash && Math.abs(b.p) > 0.75) && performance.now() - lastB > 400) { N.Sea.boost(); lastB = performance.now(); }
    } else if (st.kind === 'dive') {
      const d = st.dv; let tx, ty;
      /* v45: breathe up to full at the surface; the hull is solid, so follow st.way through the gap in the deck */
      if (d.item || (st.air < 0.42 && d.y > st.sea + 26)) { tx = st.boatX || g.W / 2; ty = st.sea; }
      else if (d.y < st.sea + 30 && st.air < 0.95) { tx = d.x; ty = st.sea; }
      else { const it = st.items.filter(i => !i.banked && !i.taken && !i.full).sort((a, b) => (!!b.special - !!a.special) || (Math.hypot(a.x - d.x, a.y - d.y) - Math.hypot(b.x - d.x, b.y - d.y)))[0]; if (it) { tx = it.x; ty = it.y; } else { tx = g.W / 2; ty = st.sea; } }
      if (st.way) { const w = st.way(tx, ty); tx = w[0]; ty = w[1]; }
      key('ArrowLeft', tx - d.x < -12); key('ArrowRight', tx - d.x > 12); key('ArrowUp', ty - d.y < -12); key('ArrowDown', ty - d.y > 12);
    } else if (st.kind === 'race') {
      const b = st.beats.find(b => !b.hit && Math.abs(b.t - st.t) < 0.04); if (b) N.Sea.boost();
    }
  }, 20);
};
async function solvePuzzle(p) {
  return p.evaluate(async () => {
    const N = window.__nil, P = N.PZ; if (!P) return null;
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    const click = s => { const e = document.querySelector(s); if (e) e.click(); return !!e; };
    if (P.kind === 'mem') { click('[data-act="pzStart"]'); await sleep(600 + P.seq.length * 720 + 200); for (const k of P.seq) { click('[data-pz="' + k + '"]'); await sleep(60); } await sleep(700); return 'mem'; }
    if (P.kind === 'scale') { click('[data-pzpick="' + P.fake + '"]'); return 'scale'; }
    if (P.kind === 'liar') { click('[data-pzliar="' + P.c + '"]'); return 'liar'; }
    if (P.kind === 'duel') { for (let r = 0; r < 3 && N.PZ; r++) { click('[data-pzduel="' + N.PZ.opts.indexOf(N.PZ.k) + '"]'); await sleep(1000); } return 'duel'; }
    if (P.kind === 'temple') { N.fn.templeAutoSolve && N.fn.templeAutoSolve(); await sleep(2600); return 'temple'; }
    if (P.kind === 'baboon') { N.fn.baboonAuto && N.fn.baboonAuto(); await sleep(16000); return 'baboon'; }
    if (P.kind === 'senet') { N.fn.senetAuto && N.fn.senetAuto({ fast:true }); await sleep(20000); return 'senet'; }
    return P.kind;
  });
}
async function main() {
  const HTML = process.argv[3];
  if (!HTML) throw new Error('Kullanım: node t153_28.js 1 <tam preview.html yolu>');
  const { chromium } = require('playwright');
  const b = await chromium.launch();
  try {
  for (const runs of (process.argv[2] || '1').split(',').map(Number)) {
    const p = await b.newPage({ viewport:{ width:1366, height:768 } }); const errs = []; p.on('pageerror', e => errs.push(e.message));
    try {
    await p.addInitScript(r => { try { localStorage.setItem('nil-kervanci-meta10', JSON.stringify({ rep:4, lv:{}, ach:{}, runs:r, noHints:true, tutDone:true })); } catch (e) {} }, runs);
    await p.route('https://fonts.googleapis.com/**', r => r.abort());
    await p.goto('file://' + HTML + '?debug'); await W(300);
    await p.evaluate(() => document.querySelector('[data-act="new"]').click()); await W(300);
    await p.evaluate(BOT);
    const seen = new Set(); let guard = 0, voyages = 0, completed = false, lastState = null;
    while (guard++ < 1600) {
      const st = await p.evaluate(() => { const N = window.__nil, S = N.S; return { over:S.over, veil:!document.querySelector('#veil').hidden, sheet:document.querySelector('#sheet').innerText.slice(0, 50).replace(/\n/g, ' '), pz:N.PZ && N.PZ.kind, map:!document.querySelector('#voy').hidden, scene:N.Sea.active(), phase:document.body.classList.contains('at-sea') ? 'sea' : 'port', day:S.day, city:S.city, q:S.quest && (S.quest.id + ':' + S.quest.st + ':' + S.quest.step) }; });
      lastState = st;
      if (process.env.V) console.log(guard, JSON.stringify(st));
      if (st.over && st.veil && /Sefer bitti/.test(st.sheet)) { completed = true; break; }
      if (st.pz) { seen.add('pz:' + st.pz); await solvePuzzle(p); await W(300); continue; }
      if (st.veil) {
        const btn = await p.evaluate(() => { const box = document.querySelector('#sheet .dlg-box'); if (box && (!box.classList.contains('done') || box.classList.contains('more'))) { box.click(); return 'dlgNext'; }
          const order = ['[data-ambush-action="fight"]', '[data-act="heroGo"]', '[data-act="unlockOk"]', '[data-act="carGo"]', '[data-act="qAccept"]', '[data-qriddle="0"]', '[data-act="qScene"]', '[data-act="qDuel"]', '[data-nchoice="0"]', '[data-act="event"]', '[data-choice="0"]:not(:disabled)', '[data-choice="1"]:not(:disabled)', '[data-choice]:not(:disabled)', '[data-act="land"]', '[data-act="pzStart"]', '#dlgCh [data-dlg]:last-child', '[data-close]']; for (const s of order) { const e = document.querySelector('#sheet ' + s); if (e && !e.disabled) { e.click(); return s; } } return null; });
        if (btn) seen.add(btn); await W(250); continue;
      }
      if (st.phase === 'sea') {
        if (st.map) { const pick = await p.evaluate(() => { const ns = [...document.querySelectorAll('.vnode[data-vnode]:not(:disabled)')]; const q = ns.find(n => n.querySelector('.vq')); const n = q || ns[0]; if (!n) return null; n.click(); return n.className.match(/t-\w+/)[0] + (q ? '*' : ''); }); if (pick) seen.add(pick); await W(600); continue; }
        await W(500); continue;
      }
      // port: sell everything, buy the cheapest-looking good, sail to a reachable city (prefer the quest city)
      const act = await p.evaluate(() => {
        const N = window.__nil, S = N.S, F = N.fn, click = s => { const e = document.querySelector(s); if (e && !e.disabled) { e.click(); return true; } return false; };
        /* the board: deliver and accept orders */
        if (S.orders.some(o => o.to === S.city && S.inv[o.g].n >= o.q) || (S.offers[S.city] && S.orders.length < 2)) { F.openSpot('board'); click('#sheet [data-act="deliver"]'); click('#sheet [data-act="accept"]'); F.closeSheet(); }
        click('[data-act="sellAll"]');
        if (S.city === 1 && S.debt > 0 && S.cash > S.debt + 400) { F.showDebt(); click('#sheet [data-payq="all"]'); click('#sheet [data-act="payAmt"]'); F.closeSheet(); }
        if (F.dmgStage() >= 2 && S.cash > 600 && F.spots().includes('yard')) F.repair();
        const tiles = [...document.querySelectorAll('.tile[data-tile]:not(.off)')].map(t => ({ id:t.dataset.tile, cls:t.className })).filter(t => !/muska|kitap|kyphi/.test(t.id));
        const pickG = tiles.find(t => /t-steal|t-cheap/.test(t.cls)) || tiles[2] || tiles[0];
        if (pickG) F.buyN(pickG.id, Infinity);
        const reach = F.mapModel().cities.filter(c => c.reach).map(c => c.i), ok = i => reach.includes(i);
        const g = F.qGoal(); let dest = g && g.c != null && g.c !== S.city ? g.c : null;
        const dz = { 1:5, 2:6, 3:7 }[S.city]; if (dz != null && (S.stats.trips % 4 === 2) && ok(dz)) dest = dz;
        if (!N.S.caravan && dest != null && dest > 4) {} else if (S.caravan) { dest = [0,1,2,3,4].find(i => ok(i)); }
        if (dest == null || !ok(dest)) { const cands = [0, 1, 2, 3, 4].filter(i => i !== S.city && ok(i)); dest = cands.length ? cands[(S.day * 3 + S.city) % cands.length] : null; }
        if (dest == null) { click('[data-act="unpick"]'); click('[data-act="sellAll"]'); click('[data-act="unpick"]'); click('[data-act="finish"]'); return 'finish'; }
        if (F.travelTo(dest)) return 'go' + dest;
        const alt = [0, 1, 2, 3, 4].filter(i => i !== S.city && i !== dest && ok(i));
        for (const i of alt) if (F.travelTo(i)) return 'go' + i;
        if (!S.caravan && !alt.length) { click('[data-act="unpick"]'); click('[data-act="finish"]'); return 'finish'; }
        return 'stuck';
      });
      if (act.startsWith('go')) voyages++;
      await W(400);
    }
    const res = await p.evaluate(() => { const S = window.__nil.S; return { over:S.over, score:S.result && S.result.score, ach:S.result && S.result.ach, quest:S.quest && { id:S.quest.id, st:S.quest.st, step:S.quest.step, log:S.quest.log.map(l => l.d + ':' + l.t.slice(0, 50)) } }; });
    console.log('runs=' + runs, 'voyages', voyages, JSON.stringify(res), '\n  seen:', [...seen].join(' '), '\n  errs:', errs.join(' | ') || 'none');
    await p.screenshot({ path:'run28-' + runs + '.png' });
    assertRunComplete({ completed, over:res.over, score:res.score, errs, guard:Math.min(guard, 1600), lastState });
    } finally {
      await p.close();
    }
  }
  } finally {
    await b.close();
  }
}
main().catch(e => { console.error('FAIL:', e.stack || e.message || e); process.exitCode = 1; });

