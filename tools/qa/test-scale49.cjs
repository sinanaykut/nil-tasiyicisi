// No browser dependencies: prove all eight light-fake branches and test live puzzle state.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const elements = new Map();
const element = selector => { if (!elements.has(selector)) elements.set(selector, { innerHTML:'', textContent:'', disabled:false, hidden:false, focus() {} }); return elements.get(selector); };
const notices = [], sounds = []; let picked, markup;
const ctx = vm.createContext({ console, Math, Number, Array, performance:{ now:() => 0 }, reduce:true,
  $:element, document:{ querySelector:element }, setTimeout, clearTimeout,
  requestAnimationFrame:() => 1, cancelAnimationFrame() {},
  openSheet:s => { markup = s; }, esc:s => String(s), play:s => sounds.push(s), toast:s => notices.push(s),
  INK:'#2B1D14', pth:(d, fill, extra) => '<path d="' + d + '" fill="' + fill + '" ' + (extra || '') + '/>',
  ink:() => '', grad:() => ''
});
vm.runInContext(fs.readFileSync(path.join(root, 'src/ui/08-puzzles.txt'), 'utf8') + `
  this.api = { pzScale, scaleWeigh, scaleMove, scalePick, scaleCandidates, scaleHint, balanceSVG,
    setFake:k => { PZ.fake = k; }, setPos:p => { PZ.pos = p; }, get:() => PZ };
`, ctx);
const api = ctx.api;
const start = fake => { picked = undefined; api.pzScale({ title:'Test', sub:'', text:'', cb:r => { picked = r; } }); api.setFake(fake); };
const weigh = (left, right) => { const positions = Array(8).fill(0); left.forEach(k => { positions[k] = 1; }); right.forEach(k => { positions[k] = 2; }); api.setPos(positions); api.scaleWeigh(); };
for (let fake = 0; fake < 8; fake++) {
  start(fake);
  weigh([0, 1, 2], [3, 4, 5]);
  let candidates = Array.from(api.scaleCandidates());
  assert.equal(candidates.includes(fake), true);
  assert.equal(candidates.length, fake < 6 ? 3 : 2);
  // Decide the second weighing using only the observed candidates, never fake.
  weigh([candidates[0]], [candidates[1]]);
  assert.deepEqual(Array.from(api.scaleCandidates()), [fake], 'fake ' + (fake + 1) + ' is uniquely solvable');
  assert.equal(api.get().left, 0);
  const positions = Array.from(api.get().pos); api.scaleMove(0);
  assert.deepEqual(Array.from(api.get().pos), positions, 'placement locks when both weighings are used');
  api.scalePick(fake); assert.equal(picked, true);
  assert.equal(api.get(), null, 'the callback completes and clears the puzzle');
}
start(0); weigh([0, 1], [2]);
assert.equal(api.get().left, 2, 'unequal counts do not waste a weighing');
weigh([], []); assert.equal(api.get().left, 2, 'empty pans do not waste a weighing');
weigh([0, 1, 2], [3, 4, 5]);
weigh([0, 1, 2], [3, 4, 5]);
assert.equal(api.get().left, 1, 'repeating an identical observation does not waste the last weighing');
weigh([3, 4, 5], [0, 1, 2]);
assert.equal(api.get().left, 1, 'reversing the same pans does not waste the last weighing');
assert.equal(api.get().weighs.length, 1, 'a reversed observation does not duplicate history');
api.scaleMove(7); assert.equal(api.get().pos[7], 1);
assert.equal(api.get().tilt, 0, 'changed pan contents cannot retain a misleading tilt');
assert.equal(api.get().weighs.length, 1, 'moving stones preserves the observation history');
api.scaleHint(); assert.equal(element('#pzScaleHint').hidden, false);
assert.ok(element('#pzScaleHistory').innerHTML.includes('Sağ kefe') || element('#pzScaleHistory').innerHTML.includes('Sol kefe'));
start(7); api.scalePick(7); assert.equal(picked, true, 'existing bot can still use the direct answer hook');
start(1); api.scalePick(0); assert.equal(picked, false, 'wrong answer follows the failure callback');
start(2); api.scalePick(9); assert.equal(api.get().left, 2, 'out-of-range answers cannot finish the puzzle');
assert.ok(markup.includes('data-act="pzScaleHint"'));
console.log('ALL OK: all 8 fakes solved in 2 weighings; placement, history, hints and answer hooks');
