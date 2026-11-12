// Run: node tools/qa/test-sea49.cjs. Exercise the real fallback drawing code
// without a browser; gameplay objects and Canvas state must stay unchanged.
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../../src/sea/03-run-draw.txt'), 'utf8');
const section = (from, to) => {
  const start = source.indexOf(from), end = source.indexOf(to, start);
  assert.ok(start >= 0 && end > start, 'drawing section exists: ' + from);
  return source.slice(start, end);
};
const drawing = section('    function drawObs(', '    function drawStream(') +
  section('    function drawPick(', '    /* ---------- desert skin');
const stack = [];
let calls = 0, tags = 0, minimumAlpha = 1;
const methods = new Set(['beginPath', 'closePath', 'moveTo', 'lineTo', 'quadraticCurveTo', 'ellipse', 'arc', 'rect', 'roundRect', 'fillRect', 'fill', 'stroke', 'translate', 'rotate', 'fillText']);
const canvasState = { globalAlpha:1, fillStyle:'#000', strokeStyle:'#000', lineWidth:1, font:'10px sans-serif', textAlign:'start' };
const cx = new Proxy(canvasState, {
  get(target, key) {
    if (key === 'save') return () => stack.push({ ...target });
    if (key === 'restore') return () => {
      assert.ok(stack.length > 0, 'Canvas restore has a matching save');
      Object.assign(target, stack.pop());
    };
    if (methods.has(key)) return (...args) => {
      calls++;
      for (const arg of args) if (typeof arg === 'number') assert.ok(Number.isFinite(arg), key + ' receives finite coordinates');
      if (key === 'arc') assert.ok(args[2] >= 0, 'arc radius is nonnegative');
      if (key === 'ellipse') assert.ok(args[2] >= 0 && args[3] >= 0, 'ellipse radii are nonnegative');
    };
    return target[key];
  },
  set(target, key, value) {
    if (key === 'globalAlpha') { assert.ok(value >= 0 && value <= 1); minimumAlpha = Math.min(minimumAlpha, value); }
    target[key] = value; return true;
  }
});
const st = { t:1, desert:false, plan:{} };
const context = vm.createContext({
  cx, st, H:800, sx:u => u, sy:y => y, Math,
  C:{ wood:'#A87440', wood2:'#694A37', ink:'#2B1D14', foam:'#E8FAFC', gold:'#D9A43A', log:'#7A4E2C' },
  outline:() => { cx.fill(); cx.stroke(); }, holdFull:() => false, fullTag:() => { tags++; }
});
vm.runInContext(drawing + '\nthis.drawPick = drawPick; this.drawObs = drawObs;', context);
function unchanged(draw, input) {
  const before = JSON.stringify(input), gameBefore = JSON.stringify(st);
  draw(input);
  assert.equal(JSON.stringify(input), before, 'drawing never changes its input');
  assert.equal(JSON.stringify(st), gameBefore, 'drawing never changes game state');
  assert.equal(stack.length, 0, 'save/restore calls remain balanced');
  assert.equal(cx.globalAlpha, 1, 'drawing restores alpha');
}
for (const k of ['crate', 'cache', 'coin']) unchanged(context.drawPick, { k, u:100, y:100 });
unchanged(context.drawPick, { k:'crate', u:100, y:100, full:true });
assert.equal(tags, 1, 'full cargo keeps its visible full marker');
assert.equal(minimumAlpha, .4, 'full cargo retains its faded appearance');
for (const len of [40, 90, 150]) {
  const before = { ...canvasState };
  unchanged(context.drawObs, { k:'log', u:100, y:100, len });
  assert.deepEqual(canvasState, before, 'log drawing restores all saved Canvas properties');
}
const before = calls;
unchanged(context.drawPick, { k:'crate', u:100, y:-100 });
unchanged(context.drawObs, { k:'log', u:100, y:1000, len:90 });
assert.equal(calls, before, 'offscreen objects are culled');
assert.ok(calls > 100, 'actual drawing paths were exercised');
console.log('ALL OK: sea crate/cache/deben/log drawing, finite coordinates and Canvas state');
