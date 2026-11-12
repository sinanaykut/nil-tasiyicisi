const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const ROOT = path.resolve(__dirname, '../..');
class Element {
  constructor() {
    this.handlers = {}; this.children = []; this.innerHTML = ''; this.hidden = true;
    const classes = new Set();
    this.classList = { add:k => classes.add(k), remove:k => classes.delete(k), contains:k => classes.has(k) || this.className?.split(' ').includes(k) };
  }
  setAttribute() {}
  appendChild(el) { this.children.push(el); el.parent = this; }
  remove() { this.removed = true; if (this.parent) this.parent.children = this.parent.children.filter(x => x !== this); }
  addEventListener(k, fn) { this.handlers[k] = fn; }
  removeEventListener(k, fn) { if (this.handlers[k] === fn) delete this.handlers[k]; }
  querySelector(s) { return { focus() {} }; }
}
function fixture() {
  const nodes = new Map(), keys = new Set(), buttons = ['fight','run'].map(action => ({ dataset:{ambushAction:action} }));
  const get = id => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
  const ctx = vm.createContext({
    console, document:{ createElement:() => new Element(), body:new Element(), querySelectorAll:() => buttons },
    window:{ addEventListener:(k, fn) => keys.add(fn), removeEventListener:(k, fn) => keys.delete(fn) },
    $:get, play() {}, setTimeout() {}, Sea:{stop() {}}, Snd:{mode() {}},
    S:{hero:'ahmose',hp:3,cash:1000,cargo:20,stats:{trips:0,hits:0,perfect:0,caught:0,escapes:0,crates:0}}, closeSheet() {}, openSheet() {}, renderPlate() {}, renderPanel() {},
    vnote() {}, toast() {}, buzz() {}, heroOverlay() {}, FIGHT:{haydut:1, djedi:1, bedevi:1},
    showMap() {}, dzResult() {}, dzSkip() {}, playScene:kind => { ctx.sceneStarted = kind; },
    quickSea:() => ({hits:0, caught:true, hurt:1, coins:0}),
    heroMax:() => 3, heroHp:s => s.hp, HEALER:80, fmtN:String, goodsList:() => [],
    loseFrac:(s, fraction) => { ctx.lossCalls++; s.cargo -= Math.round(s.cargo*fraction); return ['yük']; }, lossCalls:0,
    landed:r => { ctx.results.push(r); ctx.settlement=ctx.applySea(ctx.S,ctx.plan,r); }, results:[], VG:null
  });
  vm.runInContext(fs.readFileSync(path.join(ROOT,'src/combat49.txt'),'utf8'),ctx);
  const voyageSource = fs.readFileSync(path.join(ROOT,'src/ui/06-voyage.txt'),'utf8');
  vm.runInContext(voyageSource.slice(voyageSource.indexOf('  function afterStop('), voyageSource.indexOf('  /* ---------- stops without a scene')),ctx);
  const core=fs.readFileSync(path.join(ROOT,'src/core.txt'),'utf8');
  vm.runInContext(core.slice(core.indexOf('function applySea('),core.indexOf("/* v48: the desert road's damage")),ctx);
  return {ctx,keys,buttons,get,run:s => vm.runInContext(s,ctx)};
}
const f=fixture(), run=f.run;
// All tell phases can be won without spending a heart, using the visible cues.
for (let seed=0;seed<9;seed++) {
  f.ctx.seed=seed;
  const s=run('ambushNew({seed,hp:1,maxHp:4})'); f.ctx.s=s;
  for(let i=0;i<12&&!s.done;i++) run("ambushTurn(s, ambushTell(s).id === 'lunge' ? 'guard' : ambushTell(s).id === 'sweep' ? 'dodge' : 'strike')");
  assert.equal(s.won,true); assert.equal(s.hp,1); assert.equal(s.hits,0);
  const snap=JSON.stringify(s); run("ambushTurn(s,'strike')"); assert.equal(JSON.stringify(s),snap,'terminal state cannot be applied twice');
}
f.ctx.s=run('ambushNew({seed:1,hp:3})');
run("ambushTurn(s,'guard')"); assert.equal(f.ctx.s.hp,2,'guarding a sweep hurts');
f.ctx.s.stamina=0;
assert.equal(run("ambushTurn(s,'strike')"),false);
assert.equal(run("ambushTurn(s,'dodge')"),false);
assert.equal(run("ambushTurn(s,'nonsense')"),false);
run("ambushTurn(s,'retreat')"); assert.equal(f.ctx.s.done,true); assert.equal(f.ctx.s.won,false); assert.equal(f.ctx.s.hp,2);
f.ctx.s=run('ambushNew({hp:0})');
assert.equal(f.ctx.s.done,true);
assert.equal(run("ambushTurn(s,'strike')"),false,'zero hearts cannot attack');
// Controller closes listeners/DOM before delivering a result and delivers once.
let finished=0;
f.ctx.options={host:new Element(),seed:0,hp:3,maxHp:3};
f.ctx.finish=() => { finished++; assert.equal(f.keys.size,0); };
const ctl=run('startAmbushCombat(options,finish)');
assert.equal(f.keys.size,1);
for(let i=0;i<15&&!finished;i++) ctl.bot();
assert.equal(finished,1); ctl.bot(); ctl.dispose(); assert.equal(finished,1);
assert.equal(f.ctx.options.host.children.length,0);
const old=run('startAmbushCombat(options,finish)'), fresh=run('startAmbushCombat(options,finish)');
old.dispose(); assert.equal(f.keys.size,1,'disposing replaced fight does not remove new listener');
fresh.dispose(); fresh.bot(); assert.equal(f.keys.size,0); assert.equal(finished,1,'cancellation does not settle a result');
f.ctx.options.hp=0;
const fainted=run('startAmbushCombat(options,finish)'); assert.equal(fainted.peek().done,true); fainted.dispose();
function river(mode) {
  const g=fixture();
  g.ctx.plan={seed:0,chaser:'haydut'};
  g.ctx.VG={scene:null,dz:false,plan:g.ctx.plan,layer:0,layers:[[{t:'calm',amb:true}]],picks:[0],hp:5,hh:mode==='faint'?1:3,hhMax:3,chaseDone:false,raceDone:true,
    acc:{hits:0,caught:false,escaped:true,coins:0,crates:0,got:{},overboard:0,notes:[]}};
  g.run('afterStop({amb:true})');
  assert.equal(g.ctx.VG.chaseDone,true); assert.equal(g.ctx.VG.inChase,true);
  g.buttons[mode==='run'?1:0].onclick();
  if(mode==='run') { assert.equal(g.ctx.sceneStarted,'chase'); return; }
  const c=g.run('activeAmbushCombat');
  if(mode==='retreat') {
    const root=g.get('#stage').children[0].children[0];
    root.handlers.click({target:{closest:()=>({dataset:{ac:'retreat'}})},preventDefault(){}});
  } else if(mode==='faint') {
    const root=g.get('#stage').children[0].children[0];
    // A reckless strike from one heart exercises faintCheck -> skipVoyage.
    root.handlers.click({target:{closest:()=>({dataset:{ac:'strike'}})},preventDefault(){}});
  }
  for(let i=0;i<15&&!g.ctx.results.length;i++) c.bot();
  assert.equal(g.ctx.results.length,1); const r=g.ctx.results[0];
  assert.equal(r.fought,true); assert.equal(r.hits,0,'personal combat does not damage the hull');
  assert.equal(r.hp,5); assert.equal(r.caught,mode!=='win'); assert.equal(r.escaped,mode==='win');
  assert.equal(r.hh,mode==='faint'?0:3);
  assert.equal(g.ctx.lossCalls,mode==='win'?0:1,'cargo penalty feeds applySea once');
  assert.equal(g.ctx.S.cargo,mode==='win'?20:14);
  assert.equal(g.ctx.S.hp,3,'retreat has no extra heart penalty; a faint is healed');
  assert.equal(g.ctx.S.stats.faints||0,mode==='faint'?1:0);
  assert.equal(g.ctx.S.cash,mode==='faint'?920:1000);
  c.bot(); assert.equal(g.ctx.results.length,1,'landed is called only once');
}
river('win'); river('retreat'); river('faint'); river('run');
// Live wounds reach the voyage immediately. Skipping cannot erase them or
// settle cargo while the fight still owns the stage.
const mid=fixture(); mid.ctx.plan={seed:0,chaser:'haydut'};
mid.ctx.VG={plan:mid.ctx.plan,layer:0,layers:[[{t:'calm',amb:true}]],picks:[0],hp:5,hh:3,hhMax:3,chaseDone:false,raceDone:true,
  acc:{hits:0,caught:false,escaped:true,coins:0,crates:0,got:{},overboard:0,notes:[]}};
mid.run('afterStop({amb:true})'); mid.buttons[0].onclick();
const midRoot=mid.get('#stage').children[0].children[0], midCtl=mid.run('activeAmbushCombat');
const strike=() => midRoot.handlers.click({target:{closest:()=>({dataset:{ac:'strike'}})},preventDefault(){}});
strike(); strike();
assert.equal(mid.ctx.VG.hh,1,'HUD/voyage hearts track wounds before finish');
assert.equal(mid.ctx.VG.hp,5,'combat wounds never become plank damage');
mid.run('skipVoyage()');
assert.equal(mid.ctx.results.length,0,'skip is blocked during active combat');
assert.equal(mid.ctx.VG.hh,1); assert.equal(mid.keys.size,1);
assert.equal(mid.ctx.S.cargo,20,'cargo settles at landing, not on every hit');
midCtl.bot(); midCtl.bot();
assert.equal(mid.ctx.results.length,1); assert.equal(mid.ctx.results[0].hh,1);
assert.equal(mid.ctx.S.hp,1,'applySea receives remaining hearts without healing or a second hit');
assert.equal(mid.ctx.S.cargo,20,'winning a wounded fight preserves cargo');
console.log('ALL OK: armed combat rules, cleanup and river result settlement');
