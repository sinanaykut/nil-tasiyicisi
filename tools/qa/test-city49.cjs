const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const source = read('src/v3/06-rays-export.txt');
const zoom = source.slice(source.indexOf('    function zoomPan('), source.indexOf('    /* internals'));
const handlers = {}, globals = {}, style = {};
const el = { style, getBoundingClientRect:() => ({left:0,top:0,width:400,height:300}),
  addEventListener:(k,f) => { handlers[k]=f; }, removeEventListener:k => { delete handlers[k]; } };
const ctx = vm.createContext({ RED:false, performance:{now:() => 1000}, window:{
  addEventListener:(k,f) => { globals[k]=f; }, removeEventListener:k => { delete globals[k]; }
} });
vm.runInContext(zoom + '\nthis.zoomPan = zoomPan;', ctx);
let enabled = true;
const control = ctx.zoomPan(el, { enabled:() => enabled, room:() => true, bound:() => true });
const event = (x,y,interactive=false) => ({ pointerId:1, pointerType:'mouse', button:0, clientX:x, clientY:y,
  deltaX:0, deltaY:100, deltaMode:0, preventDefault() {}, stopPropagation() {}, target:{closest:() => interactive ? {} : null} });
handlers.pointerdown(event(30,30,true)); globals.pointermove(event(130,130)); globals.pointerup(event(130,130));
assert.equal(control.tgt.x,0,'a button press must not drag the town beneath its label');
enabled=false;
handlers.pointerdown(event(30,30)); globals.pointermove(event(130,130)); globals.pointerup(event(130,130));
handlers.wheel(event(20,20)); handlers.dblclick(event(20,20));
assert.equal(control.tgt.x,0); assert.equal(control.tgt.z,1,'open modal blocks camera gestures');
enabled=true;
handlers.pointerdown(event(30,30)); globals.pointermove(event(130,130)); globals.pointerup(event(130,130));
assert.notEqual(control.tgt.x,0,'background dragging still works');
control.destroy(); assert.equal(Object.keys(handlers).length,0); assert.equal(Object.keys(globals).length,0);
// The real tutorial positioner follows a moving plaque and clamps to the viewport.
const hub=read('src/ui/12-hub.txt');
const positioner=hub.slice(hub.indexOf('  function positionTutorBox('),hub.indexOf('  /* v47: the guide\'s bubble'));
let target = {left:300,right:360,top:150,bottom:190,width:60,height:40};
const box={ hidden:false, offsetHeight:100, offsetWidth:300, style:{setProperty(){}}, classList:{toggle(){},remove(){},add(){}}, dataset:{} };
const targetEl={isConnected:true};
const tipCtx=vm.createContext({ $:s => s==='#tut' ? box : {getBoundingClientRect:() => ({})},
  isPhone:() => false,tutAvoid:() => target,
  document:{},window:{innerWidth:1000,innerHeight:700,scrollX:0,scrollY:0} });
vm.runInContext(positioner+'\nthis.place=positionTutorBox;',tipCtx);
tipCtx.place(targetEl); const first=box.style.left;
target={left:430,right:490,top:150,bottom:190,width:60,height:40}; tipCtx.place(targetEl);
assert.notEqual(box.style.left,first,'the explanation follows a settled camera target');
target={left:970,right:1030,top:680,bottom:720,width:60,height:40};tipCtx.place(targetEl);
assert.ok(parseFloat(box.style.left)+300<=992);assert.ok(parseFloat(box.style.top)+100<=692);
console.log('ALL OK: city controls, modal camera lock, tutorial anchoring');
