const assert = require('node:assert/strict');
const { assertRunComplete } = require('./run-status.js');
const done = { completed:true, over:true, score:0, errs:[], guard:20, lastState:{ day:30 } };
assert.doesNotThrow(() => assertRunComplete(done));
assert.doesNotThrow(() => assertRunComplete({ ...done, score:-1200 }));
// Previously all of these runs could print "errs: none" and exit successfully.
assert.throws(() => assertRunComplete({ ...done, completed:false, guard:1600, lastState:{ day:4, sheet:'Takıldı' } }), /1600.*Takıldı/);
assert.throws(() => assertRunComplete({ ...done, over:false }), /Tamamlanmış sefer/);
for (const score of [undefined, null, NaN, Infinity, '1200']) {
  assert.throws(() => assertRunComplete({ ...done, score }), /geçerli sonuç/);
}
assert.throws(() => assertRunComplete({ ...done, errs:['TypeError: broken'] }), /TypeError: broken/);
// Exercise the runner with a fake browser: validation and evaluation failures
// must both close the page and browser, even before a screenshot can be made.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, 't153_28.js'), 'utf8');
async function checkCleanup(failure) {
  let pageClosed = false, browserClosed = false, calls = 0;
  const page = {
    on() {}, addInitScript:async () => {}, route:async () => {}, goto:async () => {}, screenshot:async () => {},
    evaluate:async () => {
      if (failure === 'evaluate') throw new Error('evaluation failed');
      calls++;
      if (calls <= 2) return;
      if (calls === 3) return { over:true, veil:true, sheet:'Sefer bitti' };
      return { over:true, score:failure === 'result' ? null : 0 };
    },
    close:async () => { pageClosed = true; }
  };
  const context = {
    require:n => n === 'playwright' ? { chromium:{ launch:async () => ({ newPage:async () => page, close:async () => { browserClosed = true; } }) } } : require(n),
    process:{ argv:['node', 'bot', '1', '/tmp/preview.html'], env:{} },
    setTimeout:fn => { fn(); }, console:{ log() {}, error() {} }, module:{ exports:{} }
  };
  vm.runInNewContext(source.replace(/main\(\)\.catch\([^\n]+\);/, 'module.exports = { main };'), context);
  if (failure) await assert.rejects(context.module.exports.main(), failure === 'evaluate' ? /evaluation failed/ : /geçerli sonuç/);
  else await context.module.exports.main();
  assert.equal(pageClosed, true);
  assert.equal(browserClosed, true);
}
(async () => {
  await checkCleanup(null);
  await checkCleanup('evaluate');
  await checkCleanup('result');
  console.log('ALL OK: bot completion, page errors and browser cleanup');
})().catch(e => { console.error(e); process.exitCode = 1; });
