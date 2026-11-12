// Build the real Three.js scene without a GPU; inspect animation, shared-canvas
// ownership and resource disposal. Run: node tools/qa/test-desert49.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const THREE = require('../../site/three.min.js');
const source = fs.readFileSync(path.join(__dirname, '../../src/desert49.txt'), 'utf8');
function harness() {
  const queue = new Map(), hosts = new Map(); let id = 0, pref = true, claims = 0, releases = 0, renders = 0, scene;
  const classes = () => { const s = new Set(); return { add:x => s.add(x), remove:x => s.delete(x), contains:x => s.has(x) }; };
  const cv = { classList:classes() };
  const host = name => { const el = { isConnected:true, clientWidth:412, clientHeight:240, classList:classes(), appendChild() {} }; hosts.set(name, el); return el; };
  host('dz48'); const panorama = host('dzpan'), stage = host('dzss');
  hosts.set('pcar', { offsetWidth:240, offsetHeight:40, offsetLeft:16, offsetTop:120, dataset:{ lane:'1' }, classList:classes() });
  const renderer = { setPixelRatio() {}, setSize() {}, setClearColor() {}, render(s) { scene = s; renders++; } };
  const X = { T:() => THREE, GLS:{ cv }, glsClaim(owner) { claims++; owner.mount(cv); return renderer; }, glsRelease() { releases++; } };
  const K = { donkeys:3, dk:[2, 2, 1] };
  const context = vm.createContext({
    console, Float32Array, Set, Map, Math, performance:{ now:() => 0 },
    V3:{ _x:X, pref:() => pref, load:() => Promise.resolve(true) },
    VG:{ dz:true, plan:{ seed:42 }, tod:'day', dzStage:'walk' }, phase:'sea', DZS:null, reduce:false,
    DK_COL:['#A28F7B', '#7F6C5C', '#B4A18A'], dzK:() => K,
    vRng:seed => () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296),
    window:{ devicePixelRatio:2 }, document:{ hidden:false, getElementById:n => hosts.get(n) || null },
    $:q => q === '#voy' ? { hidden:false } : null,
    requestAnimationFrame:fn => { queue.set(++id, fn); return id; }, cancelAnimationFrame:n => queue.delete(n)
  });
  vm.runInContext(source + '\nthis.view = DZ3;', context);
  const frame = now => { const tasks = [...queue.values()]; queue.clear(); tasks.forEach(fn => fn(now)); };
  return { context, view:context.view, panorama, stage, K, cv, frame, pref:v => { pref = v; }, info:() => ({ claims, releases, renders, scene, queued:queue.size }) };
}
(async () => {
  const h = harness(); h.view.start(); await Promise.resolve(); await Promise.resolve(); h.frame(50);
  assert.equal(h.info().renders, 1, 'real scene renders through the supplied shared renderer');
  assert.equal(h.info().claims, 1);
  assert.ok(h.panorama.classList.contains('dz3-ready'));
  const scene = h.info().scene, caravan = scene.getObjectByName('dz3-caravan');
  assert.ok(caravan && caravan.children.length >= 4, 'packed animals and guide are real 3D objects');
  let meshes = 0; const tracked = new Set(); let disposed = 0;
  scene.traverse(o => { if (o.isMesh) meshes++; if (o.geometry && !tracked.has(o.geometry)) { tracked.add(o.geometry); o.geometry.addEventListener('dispose', () => disposed++); } });
  assert.ok(meshes > 20 && meshes < 220, 'rigid scenery is batched to limit draw calls: ' + meshes);
  h.context.DZS = { kind:'dunes', done:false }; h.frame(100);
  assert.ok(h.stage.classList.contains('dz3-ready'), 'the same canvas moves into the active scene');
  assert.equal(h.panorama.classList.contains('dz3-ready'), false);
  assert.ok(Number.isFinite(caravan.position.z) && caravan.scale.x > 0, '3D caravan follows the existing hit target');
  h.context.DZS = { kind:'raid', combat:true, done:false }; h.frame(150);
  assert.equal(h.stage.classList.contains('dz3-ready'), false, 'combat releases the desert canvas');
  assert.ok(h.info().releases > 0);
  h.context.DZS = null; h.context.VG.tod = 'night'; h.context.VG.dzStage = 'camp'; h.frame(200);
  assert.ok(h.panorama.classList.contains('dz3-ready'));
  h.view.stop();
  assert.equal(h.view.active(), false); assert.equal(h.info().queued, 0);
  assert.equal(disposed, tracked.size, 'all visible GPU geometry is disposed');
  assert.equal(h.panorama.classList.contains('dz3-ready'), false, 'SVG fallback is restored on disposal');
  const off = harness(); off.pref(false); off.view.start(); await Promise.resolve();
  assert.equal(off.info().claims, 0, '3D off keeps the SVG fallback and never claims WebGL');
  const pending = harness(); pending.view.start(); pending.view.stop(); await Promise.resolve(); await Promise.resolve();
  assert.equal(pending.info().queued, 0, 'an abandoned async load cannot resurrect the scene');
  console.log('ALL OK: desert Three scene, shared renderer, scene targets and disposal');
})().catch(e => { console.error(e); process.exitCode = 1; });
