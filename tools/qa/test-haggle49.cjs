const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../../src/haggle28.txt'), 'utf8');
const ctx = vm.createContext({});
vm.runInContext(source + '\nthis.api = { hgNew, hgStep };', ctx);
for (const side of ['buy','sell']) for (let seed=1;seed<=20;seed++) {
  const s = ctx.api.hgNew({ seed, side, ci:seed%8 });
  assert.equal(s.log.length,0);
  assert.equal(ctx.api.hgStep(s,'offer',99),null);
  assert.equal(s.log.length,0,'invalid requests do not add misleading history');
  let out = ctx.api.hgStep(s,'offer',1);
  assert.ok(out); assert.equal(s.log[0].act,'offer'); assert.equal(s.log[0].asked,.12);
  assert.equal(s.log[0].price,s.cur,'history records the actual counteroffer');
  assert.equal(s.log[0].R,undefined,'history never reveals the hidden reservation price');
  if (!s.fin) ctx.api.hgStep(s,'accept');
  const length = s.log.length;
  ctx.api.hgStep(s,'accept');
  assert.equal(s.log.length,length,'finished deals cannot append another settlement');
}
console.log('ALL OK: haggle offer history, public prices and terminal actions');
