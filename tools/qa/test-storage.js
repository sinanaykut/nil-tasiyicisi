// Run with: node tools/qa/test-storage.js (no browser or npm dependencies).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ROOT = path.resolve(__dirname, '../..');
const read = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const assemble = read('src/assemble.py');
const pre = assemble.split("pre = '''")[1].split("'''\ncore =")[0].replace('(function () {', '');
const state = read('src/ui/03-state-render.txt').split('/* ================= rendering')[0];
const sheets = read('src/ui/04-feedback-sheets.txt');
const slots = sheets.slice(sheets.indexOf('  function doSaveSlot('), sheets.indexOf('  /* ---------- guild'));
const input = read('src/ui/14-input.txt');
const resume = input.slice(input.indexOf('  function resumeVoyage('), input.indexOf("  document.addEventListener('keydown'"));
function harness(initial = {}) {
  const values = new Map(Object.entries(initial)), messages = [], sounds = [], timers = [];
  let fail = false;
  const el = { hidden:false, classList:{ remove() {} } };
  const context = vm.createContext({
    console, Date, JSON, Number, Math, setTimeout:fn => { timers.push(fn); return timers.length; },
    localStorage:{ getItem:k => values.has(k) ? values.get(k) : null,
      setItem:(k, v) => { if (fail) throw new Error('QuotaExceededError'); values.set(k, String(v)); } },
    window:{}, document:{ querySelector:() => el, body:el },
    rpick:a => a[0], toast:t => messages.push(t), play:s => sounds.push(s), showMenu() {}, closeSheet() {},
    renderAll() {}, showTitle() {}, showEnd() {}, bootDone() {},
    Sea:{ stop() {} }, Snd:{ mode() {}, pref:{ music:false } },
    featFor:() => ({}), ARCS:['kedi', 'ba', 'lapis'],
    enterSea() { context.entered = true; }
  });
  vm.runInContext(pre + '\n' + read('src/core.txt') + '\n' + read('src/v8-merchants.txt') + '\n' + state + '\n' + slots + '\n' + resume + '\n' + read('src/ui/15-start.txt') + `
    this.api = { valid, restoreSave, writeSave, save, start, doSaveSlot, doLoadSlot, resumeVoyage,
      create:() => newGame({ feat:{} }), finish:s => finish(s), meta,
      set:s => { S = s; }, get:() => S, setRS:r => { RS = r; }, getRS:() => RS,
      lsSet, key:KEY, slot:slotKey,
      recovery:raw => { recoveryRaw = raw; recoveryKey = KEY + '-test-recovery'; } };
  `, context);
  return { ...context.api, values, messages, sounds, context, timers,
    failWrites:v => { fail = v; }, flush:() => { while (timers.length) timers.shift()(); } };
}
const clone = v => JSON.parse(JSON.stringify(v));
const h = harness();
const game = h.create();
assert.equal(h.valid(game), true, 'a real newGame save is accepted');
for (const v of [10, 11, 12]) {
  const old = clone(game); old.v = v; delete old.trend; delete old.gifted;
  old.prices = old.prices.slice(0, 5); old.trust = old.trust.slice(0, 5);
  const restored = h.restoreSave(old);
  assert.ok(restored, 'legacy v' + v + ' save loads');
  assert.ok(restored.gifted.length >= game.prices.length);
  assert.ok(restored.trend.bugday > 0);
  assert.equal(old.gifted, undefined, 'migration does not mutate the original save');
}
for (const mutate of [
  g => { g.city = 99; }, g => { g.prices[0] = null; }, g => { g.inv.bugday.n = -1; },
  g => { g.inv.bugday.cost = 'bad'; }, g => { g.trust = {}; }, g => { g.gifted = {}; },
  g => { g.trend = []; }, g => { g.orders = [null]; }, g => { g.quest = { id:'missing' }; },
  g => { g.over = true; g.result = null; }, g => { g.voyage = { from:99 }; },
  g => { g.stockBase = []; }, g => { g.prices[1] = {}; }
]) {
  const broken = clone(game); mutate(broken);
  assert.equal(h.restoreSave(broken), null, 'malformed data is rejected before migration');
}
const completed = clone(game); h.finish(completed);
assert.equal(h.valid(completed), true, 'completed runs remain loadable');
h.setRS(123); h.restoreSave(game);
assert.equal(h.getRS(), 123, 'checking a save does not advance the active seeded run');
h.set(game); h.values.set(h.slot(1), 'previous slot');
h.failWrites(true);
assert.equal(h.lsSet('test', 'x'), false);
h.doSaveSlot(1);
assert.equal(h.values.get(h.slot(1)), 'previous slot');
assert.ok(h.messages.at(-1).includes('Kaydedilemedi'));
assert.ok(!h.messages.some(t => /yuvaya kaydedildi/.test(t)));
h.messages.length = 0;
h.save(); h.save(); h.save(); h.flush();
assert.equal(h.messages.length, 1, 'autosave failures warn once until a successful save');
h.failWrites(false); assert.equal(h.save(), true);
h.failWrites(true); h.save(); h.flush();
assert.equal(h.messages.length, 2, 'a later failure after recovery warns again');
h.failWrites(false); h.doSaveSlot(1);
assert.ok(h.messages.at(-1).includes('yuvaya kaydedildi'));
assert.equal(JSON.parse(h.values.get(h.slot(1))).S.cash, game.cash);
const active = clone(game); active.cash = 4321; h.set(active);
const malformed = clone(game); malformed.gifted = {};
h.values.set(h.slot(2), JSON.stringify({ S:malformed, at:'today' }));
h.doLoadSlot(2);
assert.equal(h.get(), active, 'bad slot never replaces current state');
assert.equal(h.values.get(h.key), JSON.stringify(game), 'bad slot never overwrites autosave');
const snap = clone(game); snap.voyage = { from:1, dest:2, days:1, seed:42 }; snap.voyageSnap = malformed;
h.set(snap); h.resumeVoyage();
assert.equal(h.get(), snap, 'bad voyage snapshot never replaces current state');
assert.equal(h.context.entered, undefined, 'bad voyage snapshot never starts a scene');
const badRaw = '{unreadable';
const boot = harness({ [h.key]:badRaw }); boot.start({}); boot.flush();
assert.ok([...boot.values].some(([k, v]) => k.includes('-recovery-') && v === badRaw), 'boot preserves unreadable raw data');
assert.equal(boot.valid(JSON.parse(boot.values.get(h.key))), true, 'boot safely starts a valid new run');
const blocked = harness({ [h.key]:badRaw }); blocked.failWrites(true); blocked.start({}); blocked.flush();
assert.equal(blocked.values.get(h.key), badRaw, 'failed recovery backup cannot overwrite unreadable autosave');
const fallback = harness({ [h.key]:JSON.stringify(game) }); fallback.start({ S:malformed });
assert.equal(fallback.get().cash, game.cash, 'invalid hot state falls back to valid autosave');
assert.equal(fallback.values.get(h.key), JSON.stringify(game), 'valid autosave is left intact at boot');
const legacy = clone(game); delete legacy.quest; legacy.feat.quest = true;
const legacyBoot = harness({ [h.key]:JSON.stringify(legacy) }); legacyBoot.start({});
assert.equal(legacyBoot.get().quest.st, 'offer', 'young legacy save still receives its first story offer');
assert.equal(legacyBoot.get().day, game.day);
assert.equal(legacyBoot.get().cash, game.cash);
const badMeta = harness({ 'nil-kervanci-meta10':JSON.stringify({ lv:null, ach:null, rep:'bad', runs:-1, guide:'bad', tells:'bad' }) });
assert.equal(Object.keys(badMeta.meta.lv).length, 0);
assert.equal(Object.keys(badMeta.meta.ach).length, 0);
assert.equal(badMeta.meta.rep, 0);
assert.equal(badMeta.meta.runs, 0);
assert.equal(Object.keys(badMeta.meta.guide).length, 0);
assert.equal(Object.keys(badMeta.meta.tells).length, 0);
console.log('ALL OK: storage failure, legacy saves, malformed loads and recovery');
