// Exercise the cached SVG rig for every character, expression and tell without a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const ctx = vm.createContext({ console });
vm.runInContext(fs.readFileSync(path.join(root, 'src/chars40.txt'), 'utf8') + '\nthis.api = CH40;', ctx);
const api = ctx.api;
const idsOf = svg => [...svg.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
let count = 0;
function check(key, options) {
  const svg = api.svg(key, options);
  assert.ok(svg.startsWith('<svg'), key + ' renders');
  assert.ok(!/(?:NaN|Infinity|undefined|§)/.test(svg), key + ' has finite, resolved SVG values');
  const ids = idsOf(svg), unique = new Set(ids);
  assert.equal(ids.length, unique.size, key + ' has no duplicate local IDs');
  for (const ref of svg.matchAll(/url\(#([^\)]+)\)/g)) assert.ok(unique.has(ref[1]), key + ' resolves ' + ref[1]);
  assert.ok(svg.includes('linearGradient id="skin'), 'shared lighting is native SVG');
  count++;
}
for (const key of api.keys) {
  for (const frame of ['bust', 'card', 'head', 'face']) check(key, { frame, live:true });
  for (const mood of api.MOODS) check(key, { frame:'bust', mood, live:true });
  for (const tell of api.TELLS) check(key, { frame:'bust', tell, live:true });
  const one = new Set(idsOf(api.svg(key, { frame:'bust' }))), two = idsOf(api.svg(key, { frame:'bust' }));
  assert.ok(two.every(id => !one.has(id)), 'cached portraits receive unique IDs on reuse');
}
assert.equal(api.svg('missing-character'), '');
console.log('ALL OK: ' + count + ' character SVG combinations; finite geometry and unique, resolved IDs');
