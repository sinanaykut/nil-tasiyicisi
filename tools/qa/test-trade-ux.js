const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const listeners = {}, calls = [], focused = [], focusTargets = new Map();
const ctx = vm.createContext({
  console, S:{ day:3, city:1, over:false, inv:{ bugday:{ n:12 } } },
  qty:10, msel:'bugday', hgSide:false, phase:'port', DLG:null, sheetName:'',
  gById:() => ({ id:'bugday', name:'Buğday', short:'Buğday' }),
  quoteBuy:() => ({ n:40 }), quoteSell:() => ({ n:12 }),
  canHaggle28:() => true, haggleDeal() {}, renderPanel() { calls.push('panel'); },
  play() {}, toast() {}, placeTutor() {}, save() {}, renderAll() {},
  floatAt() {}, fmt:String, trustToast() {}, MERCHANT_NAMES:['a', 'b'], BLESS:{},
  trade(kind) { calls.push(kind); },
  document:{
    addEventListener(name, fn) { (listeners[name] ||= []).push(fn); },
    querySelectorAll:() => [], querySelector:s => focusTargets.get(s) || null
  },
  window:{ addEventListener() {} },
  $:() => ({ hidden:true }), Snd:{ unlock() {} }, Sea:{ init() {} },
  showBoard() { calls.push('board'); }, showMerchant() { calls.push('merchant'); }
});
function ev(s) { return vm.runInContext(s, ctx); }
const root = path.resolve(__dirname, '../..');
ev(fs.readFileSync(path.join(root, 'src/ui/13-hub-sheets.txt'), 'utf8'));
ev(fs.readFileSync(path.join(root, 'src/ui/14-input.txt'), 'utf8'));
// Replace actual sheet painters after source loads; preserve the refresh function.
ev("showBoard = () => calls.push('board'); showMerchant = () => calls.push('merchant');");
ctx.calls = calls;
ev("hag28('bugday', 'sell')");
assert.equal(ctx.hgSide.n, 10, 'preselected quantity survives entering haggle');
assert.equal(ctx.hgSide.side, 'sell');
ctx.hgSide = false; ctx.qty = Infinity;
ev("hag28('bugday', 'sell')");
assert.equal(ctx.hgSide.n, 12, 'Hepsi uses the sell bound, not the buy capacity');
function click(dataset) {
  const t = { dataset, hasAttribute:() => false };
  listeners.click.at(-1)({ target:{ closest:s => s === 'button' ? t : null }, preventDefault() {} });
}
for (const [attr, value] of [['hgside','buy'], ['hgq','-1'], ['hgq','all'], ['tradeq','1'], ['tradeq','all']]) {
  const key = '[data-' + attr + '="' + value + '"]:not(:disabled)';
  focusTargets.set(key, { focus(options) { assert.equal(options.preventScroll, true); focused.push(attr + ':' + value); } });
}
ctx.hgSide.n = 3;
click({ hgside:'buy' });
assert.equal(ctx.hgSide.n, 3, 'switching sides preserves quantity');
assert.equal(focused.at(-1), 'hgside:buy', 'side repaint restores the same enabled control');
click({ hgq:'-1' }); assert.equal(ctx.hgSide.n, 2);
assert.equal(focused.at(-1), 'hgq:-1', 'haggle amount repaint restores keyboard focus');
click({ hgq:'all' }); assert.equal(ctx.hgSide.n, 40);
function change(attr, value) {
  listeners.change[0]({ target:{ value, hasAttribute:s => s === attr, closest:() => null } });
}
change('data-hgqty', '7.9'); assert.equal(ctx.hgSide.n, 7);
change('data-hgqty', '999'); assert.equal(ctx.hgSide.n, 40);
change('data-hgqty', '-5'); assert.equal(ctx.hgSide.n, 1);
change('data-hgqty', ''); assert.equal(ctx.hgSide.n, 1);
ctx.hgSide = false;
ctx.qty = 4; click({ tradeq:'1' });
assert.equal(ctx.qty, 5); assert.equal(focused.at(-1), 'tradeq:1', 'market amount repaint restores keyboard focus');
click({ tradeq:'all' }); assert.equal(ctx.qty, Infinity); assert.equal(focused.at(-1), 'tradeq:all');
const focusedBefore = focused.length;
click({ tradeq:'-1' }); assert.equal(focused.length, focusedBefore, 'missing/disabled replacement is not focused');
click({ sell:'bugday' });
ev("hag28('bugday')");
assert.equal(ctx.hgSide.side, 'sell', 'sell intent opens Satarken');
ctx.qty = 5;
ctx.DLG = {}; ctx.sheetName = 'say';
ctx.dlgSay = () => {};
ctx.priceSig = () => ({});
ctx.gIco = () => ''; ctx.esc = String; ctx.ico = () => '';
ev("hgSetupHtml = () => ''; hagSetupInDialog('bugday', 'buy')");
assert.equal(ctx.hgSide.n, 5, 'dialog setup also keeps selected quantity');
const oldQuery = ctx.$;
ctx.$ = selector => selector === '#dlgX' ? { querySelector:s => ({ focus() { focused.push('dialog:' + s); } }) } : oldQuery(selector);
ev("focusAmountControl('data-hgq', '-1')");
assert.equal(focused.at(-1), 'dialog:[data-hgq="-1"]:not(:disabled)', 'dialog focus stays in the foreground setup');
ctx.$ = oldQuery;

for (const [value, max, expected] of [[Infinity,12,12], ['all',12,12], [3.8,12,3], [999,12,12], [4,0,0], [NaN,12,1]]) {
  ctx.value=value; ctx.max=max;
  assert.equal(ev('tradeAmount(value,max)'), expected);
}
ctx.sheetName='board'; ev('refreshOrderSheet()'); assert.equal(calls.at(-1),'board');
ctx.sheetName='say'; ctx.DLG={who:1}; ev('refreshOrderSheet()'); assert.equal(calls.at(-1),'merchant');
const n=calls.length;
ctx.DLG={who:'paneb'}; ev('refreshOrderSheet()'); assert.equal(calls.length,n,'unrelated dialogue is preserved');
let pending = true, paid = 0;
ctx.deliverable = () => pending ? [{}] : [];
ctx.deliver = () => { pending = false; paid++; return { from:1, reward:100 }; };
ctx.sheetName = 'board';
click({ act:'deliver' });
assert.equal(paid,1); assert.equal(calls.at(-1),'board','delivery refreshes the open board');
click({ act:'deliver' }); assert.equal(paid,1,'stale delivery cannot pay twice');
assert.match(ev("tradeQtyControls(0,0,'hg',false)"), /max="0"/);
console.log('ALL OK: trade quantity, side intent and order-sheet refresh');
