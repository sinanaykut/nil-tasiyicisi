const { chromium } = require('playwright'); const fs = require('fs');
const W = ms => new Promise(r => setTimeout(r, ms));
const ROOT = '/tmp/claude-0/-home-claude/50408ee7-81cd-5d20-8660-e495325793de/scratchpad';
const HTML = process.env.HTML || (ROOT + '/audit31/preview31.html'), OUT = process.env.OUT || (ROOT + '/audit31/qa/');
const THREE = ROOT + '/vendor/node_modules/three/build/three.min.js';
const VPS = { d:{ viewport:{ width:1280, height:720 } }, m:{ viewport:{ width:412, height:915 }, isMobile:true, hasTouch:true }, l:{ viewport:{ width:915, height:412 }, isMobile:true, hasTouch:true } };
const SKIP = { rep:4, lv:{}, ach:{}, runs:3, noHints:true, tutDone:true, seenFeat:['haggle','crisis','sethi','quest','contra','desert','atolye','tekne'] };
async function open(vpn, { d3 = true, meta = SKIP, tag = '' } = {}) {
  const b = await chromium.launch({ args:['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const ctx = await b.newContext(VPS[vpn]); const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + e.message + ' @' + (e.stack || '').split('\n')[1]));
  p.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_|net::|WebGL|GL_|swiftshader|deprecat/i.test(m.text())) errs.push('CONSOLE ' + m.text()); });
  await ctx.route('https://fonts.googleapis.com/**', r => r.abort()); await ctx.route('https://fonts.gstatic.com/**', r => r.abort());
  await ctx.route('https://cdnjs.cloudflare.com/**', r => r.fulfill({ path:THREE, contentType:'application/javascript' }));
  await ctx.addInitScript(([m, d3]) => { try { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); if (m) localStorage.setItem('nil-kervanci-meta10', m); localStorage.setItem('nil-kervanci-3d', d3 ? '1' : '0'); sessionStorage.setItem('seeded', '1'); } } catch (e) {} }, [meta ? JSON.stringify(meta) : null, d3]);
  await p.goto('file://' + HTML + '?debug', { timeout:90000 }); await W(d3 ? 1500 : 600);
  const pre = OUT + vpn + (d3 ? '' : '2d') + tag + '-';
  let n = 0;
  const shot = async (name, wait = 0) => { if (wait) await W(wait); const f = pre + String(++n).padStart(2, '0') + '-' + name + '.png'; await p.screenshot({ path:f }); return f; };
  const mark = s => errs.push('--- ' + s);
  return { b, ctx, p, errs, shot, mark, ev:(f, a) => p.evaluate(f, a) };
}
async function newGame(T, hero) {
  const { p } = T;
  await p.evaluate(() => document.querySelector('[data-act="new"]').click()); await W(500);
  if (hero) await p.evaluate(h => { const e = document.querySelector('#sheet [data-hero="' + h + '"]'); if (e) e.click(); }, hero);
  await W(200);
  await p.evaluate(() => { const h = document.querySelector('#sheet [data-act="heroGo"]'); if (h) h.click(); }); await W(2500);
  await settle(T);
}
async function settle(T, max = 25) {
  const { p } = T;
  for (let i = 0; i < max; i++) {
    const st = await p.evaluate(() => { const N = window.__nil; return { veil:!document.querySelector('#veil').hidden, pz:N.PZ && N.PZ.kind, sea:document.body.classList.contains('at-sea') }; });
    if (st.pz) { await p.evaluate(() => { const b = document.querySelector('[data-act="pzCancel"]'); if (b) b.click(); else window.__nil.fn.closeSheet(); }); await W(500); continue; }
    if (st.sea) { await p.evaluate(() => { const b = document.querySelector('[data-act="quick"]'); if (b) b.click(); }); await W(500); continue; }
    if (!st.veil) return true;
    await p.evaluate(() => {
      const q = s => document.querySelector('#sheet ' + s);
      for (const s of ['[data-act="unlockOk"]', '[data-act="qDecline"]', '[data-act="event"]', '[data-choice="0"]:not(:disabled)', '[data-act="land"]', '[data-act="dlgNext"]:not(.done)', '#dlgCh [data-dlg]:last-child', '[data-close]']) { const e = q(s); if (e && !e.disabled) { e.click(); return s; } }
      window.__nil.fn.closeSheet();
    });
    await W(350);
  }
  return false;
}
async function dlgAll(p) {
  for (let i = 0; i < 12; i++) { const n = await p.evaluate(() => { const c = document.querySelectorAll('#dlgCh [data-dlg]').length; if (c) return c; const b = document.querySelector('#sheet .dlg-box'); if (b) b.click(); return 0; }); if (n) return n; await W(150); }
  return 0;
}
/* geometry check: visible elements in the sheet / hud that leave the viewport or overflow their box */
async function geom(p) {
  return p.evaluate(() => {
    const vw = innerWidth, vh = innerHeight, out = [], ovf = [];
    for (const e of document.querySelectorAll('body *')) {
      if (!e.offsetParent && getComputedStyle(e).position !== 'fixed') continue;
      const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
      const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
      if (e.closest('svg') && e.tagName !== 'svg') continue;
      const id = e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
      const scroller = (() => { let a = e.parentElement; while (a) { const s = getComputedStyle(a); if (/(auto|scroll|hidden)/.test(s.overflowY + s.overflowX)) return a; a = a.parentElement; } return null; })();
      if (!scroller && (r.right > vw + 2 || r.left < -2 || r.bottom > vh + 2) && e.children.length === 0 && (e.textContent || '').trim()) out.push(id + ' ' + Math.round(r.left) + ',' + Math.round(r.top) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' "' + e.textContent.trim().slice(0, 25) + '"');
      if ((cs.overflow === 'hidden' || cs.textOverflow === 'ellipsis') && e.scrollWidth > e.clientWidth + 2 && (e.textContent || '').trim() && e.children.length < 3) ovf.push(id + ' "' + e.textContent.trim().slice(0, 30) + '" ' + e.scrollWidth + '>' + e.clientWidth);
    }
    const tiny = [...document.querySelectorAll('#sheet *, .hud *, #mbar *, .abar *')].filter(e => e.offsetParent && e.children.length === 0 && (e.textContent || '').trim().length > 1).filter(e => parseFloat(getComputedStyle(e).fontSize) < 10.5).map(e => (e.className || e.tagName) + ':' + getComputedStyle(e).fontSize + ' "' + e.textContent.trim().slice(0, 20) + '"');
    const de = document.documentElement;
    return { scroll:de.scrollWidth + 'x' + de.scrollHeight + ' vp ' + vw + 'x' + vh, out:out.slice(0, 12), ovf:ovf.slice(0, 12), tiny:[...new Set(tiny)].slice(0, 12) };
  });
}
module.exports = { W, ROOT, OUT, open, newGame, settle, dlgAll, geom, SKIP, VPS };
