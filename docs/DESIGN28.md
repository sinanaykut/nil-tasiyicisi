# Nil Kervancısı v28 — studio brief (read fully before you start)

ROOT = `/tmp/claude-0/-home-claude/50408ee7-81cd-5d20-8660-e495325793de/scratchpad`.

## The game, and the owner's feedback this round
Single-file HTML trading game in ancient Egypt (Turkish UI), played mostly on a Galaxy S26 phone (Chrome) and
sometimes on an M1 MacBook. Flat "tomb painting / papyrus" style: ink outlines `#2B1D14`, warm paper colours,
gold `#D9A43A`, lapis `#1F5FA8`, red `#B7412E`, turquoise `#2BA59A`, paper `#FBF3DF`. Design rule: *must not be
complicated even for the owner's mother* — few words, big tap targets, pictures over text, no drag-and-drop.
v27 (current) has: 30-day season, 12 goods, 5 Nile cities + 3 desert cities by donkey caravan, boats & ship
devices, workshops, temples (light puzzle), tavern Senet, baboon raids, locust crisis, Three.js 2.5D river view.

The owner's v28 feedback (all of it is in scope, split between the developers below):
1. A character should introduce the game at the start (a friend or a relative).
2. The ship should look more damaged in port the more damage it has taken; at certain stages repair is offered.
3. Haggling must get deeper: face reading, body language, guessing from the shop's state how willing the merchant
   is to sell (or buy) that good.
4. The "Ambar" (hold) box sits under the quay and confuses — it belongs next to the ship; redesign that area.
5. The Sethi race mini-game is too simple; improve it.
6. Gifting a merchant a good he already sells is odd — gifts should be rare / crafted items.
7. Senet is fun but must be taught better the first time.
8. The market list grew and needs scrolling — sort goods into categories in a grid (Diablo / Stardew style) so no
   scrolling is needed.
9. Orders and "Hapu's house: pay debt" boxes must move somewhere else (they force scrolling).
10. City name top-left, travel strip at the bottom, desert trips "look like they have no place" — everything must
    sit in meaningful, connected places on screen.
11. The main harbour/city/ship picture must be redesigned to a high standard; the map should fit with it.
12. Temple, shipyard, tavern and the merchant should be reached by tapping them **in the city picture**, not buttons.
13. The wreck (dive) screen must be redesigned.
14. More 3D and effects. Characters we talk to should appear big, like in a dating sim.
15. A full bug pass at the end (producer + QA).

## How the code is built
* Parts: `ROOT/p28/` is the producer's live copy — **do not edit it**. Frozen snapshot for you: `ROOT/base28/`.
  Make your own copy: `cp -r ROOT/base28 ROOT/work28/<yourname>` and edit only your files there.
* Build: from ROOT run `python3 base28/assemble.py work28/<yourname> out/<yourname>` →
  `ROOT/out/<yourname>-preview.html` (full page; open with Playwright `file://…?debug`).
* Syntax check: `sed -n '/<script>/,/<\/script>/p' out/X.html | sed '1d;$d' > out/X.js && node --check out/X.js`.
* Script order inside ONE IIFE: `core.txt` → merchants block → `merch27.txt` → portrait() → `snd.txt` → `sea.txt` →
  `ui.txt` → modules `art27.txt, art28.txt, chars28.txt, v3.txt, temple.txt, senet.txt, mini.txt, haggle28.txt` →
  `boot.txt` (calls `start()` and enables 3D). CSS module files `css27.txt, art27.css, v3.css, temple.css,
  senet.css, mini.css, css28.txt, art28.css, chars28.css, haggle28.css` are injected into the stylesheet. Extra
  icons: `sprites28.txt` (`<symbol id="i-…" viewBox="0 0 32 32">…</symbol>` lines).
* Module rules: function declarations or lazily-used `const` objects only; nothing at load time that needs another
  module. Compact code style like the rest, comments in English, player-facing text Turkish, short.
* Debug: `?debug` exposes `window.__nil` = `{ S, meta, Sea, Snd, PZ, V3, render(), vg(), fn:{…} }`.
* Playwright + Chromium installed (`require('playwright')`; never run `playwright install`). WebGL in headless:
  `chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']})`. Three.js r128 local
  copy: `ROOT/vendor/node_modules/three/build/three.min.js` — route `https://cdnjs.cloudflare.com/**` to it with
  `page.route`. 3D is OFF by default on this 2-core sandbox: set `localStorage['nil-kervanci-3d']='1'` and
  `__nil.V3.river.adapt=false` in tests. Google Fonts are blocked here (harmless console errors).
* Skip onboarding in tests: `localStorage.setItem('nil-kervanci-meta10', JSON.stringify({rep:4,lv:{},ach:{},runs:3,
  noHints:true,tutDone:true,seenFeat:['haggle','crisis','sethi','quest','contra','desert','atolye','tekne']}))`,
  click `[data-act="new"]`, then `[data-act="qDecline"]` if present.
* Test on 1280×720 AND phone 412×915 (`isMobile:true, hasTouch:true`). Look at your screenshots with the Read tool
  and iterate until they are genuinely beautiful and readable.
* Shared helpers (ui.txt/core): `esc, ico(id,size), gIco(g,size), cIco(i,size), play(sound), buzz(k), toast(t),
  openSheet(html, lock, name, wide), closeSheet(), xBtn, choiceHtml, banner, portrait(i,lvl), pth(d,fill,extra),
  ink(w), grad(id,stops,vertical), mix(a,b,k), INK, fmt/fmtN, meta, saveMeta(), S, uid (use ++uid for SVG ids),
  dayPal(si, day)` (sky palette: top/mid/low/sun/water[3]/sunX/sunY/stars/tint/t), `merchantFig(ci, mood)`,
  `palmSVG, personSVG, shipSVG2(spec, loadN, id)` (art27), `MERCHANTS[i].look`, `CITIES`, `GOODS`, `deals(i,g)`.
  Mini-game framework: `PZ` object + `pzClear()`; see `pzBalance` in ui.txt.

## Cast (names are fixed — use them)
* **Paneb** — the player's childhood friend and helmsman (dümenci), cheerful, a bit cheeky, mid-20s, red headband,
  short kilt, steering-oar pin. He is the guide: introduces the game, teaches new systems the first time, comments.
* Merchants: 0 Meret (Per-Bastet, cats), 1 Ptahhotep (Mennefer, old pyramid mason), 2 Nefer (Abidos, temple
  scribe), 3 Kha (Vaset, loud copper trader), 4 Tiye (Abu, lapis trader), 5 Tefnakht (Siwa), 6 Hatnefer (Harga),
  7 Parahu (Saww, Puntite). Their `look` objects are in MERCHANTS (backup-v8 + merch27.txt).
* Others: Hapu (moneylender, Mennefer), Sethi (rival trader, green & gold), story NPCs Merenre, Djedi, Nakht;
  tavern players `TAVERN_WHO` = { 0:'Kedici Ipi', 1:'Taşçı Seni', 3:'Kör Bata', 4:'Nubyalı Meri', 7:'Kaptan Weni' }.

## Contracts between developers

### A. `townScene(ci, o)` — art28.txt (owner: **sahne**)
The new main picture of every city (replaces portScene/oasisScene in the main screen). Returns an SVG string:
`<svg class="ts" viewBox="0 0 1000 560" preserveAspectRatio="xMidYMax slice" data-vb="1000 560" data-water="Y0 Y1">`
(`data-water` = vertical extent of the water band in viewBox units, omit if no water; put `<!--r-->` right before the
water band and `class="wat"` on its main rect — the WebGL water reflection uses these).
`o = { si, day, nar, mood, boat:{ boat, up, dev, dmg }, cargo:[goodIds for crates], caravan:{donkeys}|null,
spots:{ market, temple, tavern, work, yard, hapu, board, well } (booleans: which places exist here),
notes:{ board:n, work:'ready'|'busy'|null, temple:'done'|null }, crisis:'cekirge'|'kitlik'|'bayram'|'maden'|'liman'|null,
sethiHere:bool }`.
* Every interactive place is `<g class="spot" data-spot="KEY" tabindex="0" role="button" aria-label="…">` with a
  small label plaque inside `<g class="spot-lab">` (Turkish: Pazar, Tapınak, Meyhane, Atölye, Tersane, Hapu'nun evi,
  Sipariş panosu, Kuyu, and the ship: "Tekne · yola çık" / caravan: "Kervan · yola çık"). KEYS: `market` (stall +
  the merchant via `merchantFig`), `ship` (our boat via a new `shipSVG3(spec, loadN, id)` with damage, or the donkey
  caravan in desert cities), `temple`, `tavern`, `work`, `yard` (slipway/kalafatçı in every river port; Mennefer's is
  a big royal dockyard), `hapu` (Mennefer only), `board` (notice board with papyrus notes, everywhere), `well`
  (Siwa/Harga). Spots must sit inside the safe zone x 110–890 (phones crop the sides) and keep the top-centre
  x 330–670, y 0–70 free (the city name cartouche is an HTML overlay there). Spots must be big enough to tap on a
  412-px-wide phone (≥ 70 viewBox units wide). The ship spot stays in the same area in every river city
  (right-middle water) so players learn it.
* `shipSVG3(spec, loadN, id)`: like `shipSVG2` (same frame) plus `spec.dmg` 0..3 — 0 pristine, 1 scuffed
  (scratches, a loose rope), 2 damaged (patched sail, cracked planks, a missing oar, a bucket bailing water),
  3 critical (torn sail, broken yard, listing, smoke, planks missing). Must read clearly at harbour size.
* Effects/life: drifting dust in sunlight, birds, smoke, crowd walkers, small fishing boats crossing, lantern glow
  at dusk, crisis visuals (locust cloud, empty grain stalls, festival banners…). Put depth layers in groups with
  classes `px1` (far), `px2` (mid), `px3` (near) — the UI will move them slightly with the pointer / phone tilt.
  Respect `prefers-reduced-motion`. Keep the SVG light enough for phones (avoid filters on big areas, no blur).
* Must look clearly different per city (Per-Bastet cats & delta reeds, Mennefer pyramids & royal dockyard,
  Abidos Osiris temple, Vaset Karnak pylons & obelisks, Abu granite & elephants island, Siwa Shali fortress & salt lake,
  Harga Hibis temple & date groves, Saww Red Sea with Punt ship). Time of day from `dayPal(si, day)`.
* Also `townMini(ci)` → a small (≈ 120×80) emblem picture of the city for map cards.

### B. `bustSVG(who, o)` — chars28.txt (owner: **karakter**)
Big "dating sim" half-body character art. `who` = merchant index 0..7, or `'paneb' | 'hapu' | 'sethi' | 'merenre' |
'djedi' | 'nakht' | 'tv0' | 'tv1' | 'tv3' | 'tv4' | 'tv7'`. Returns `<svg class="bust" viewBox="0 0 320 420" …>`.
`o = { mood:'neutral'|'happy'|'angry'|'sly'|'sad'|'surprised'|'thinking', tell:null|'sweat'|'glance'|'smile'|'frown'|
'tap'|'arms'|'lean'|'scratch'|'eyebrow', talk:bool, lv:0..3 }`. Tells must be readable body language/face cues and
softly animated (CSS in chars28.css; `.bust.talk` mouth flap; respect reduced motion). Also export `CAST` =
`{ key:{ name, title, color } }` for all non-merchant characters and `castName(who)`.

### C. `V3.mapTable(el, model, onPick)` and damage — v3.txt (owner: **3B**)
A tilted 3D relief "map table" of Egypt for the travel screen: Nile valley, delta, deserts, Red Sea strip, city
markers as little models, routes (river + dashed desert roads), Sethi's boat, crisis markers. Tap a city →
`onPick(i)`. Returns `{ update(model), dispose() }`. `model = { cities:[{ i, id, name, x, y, river, here, reach,
days, sel, badges:{ sethi, crisis, order, work } }], roads:[{ a, b, desert, days }], sethi:{ x, y, label }|null,
si, day }` where x,y are 0..1 map coordinates (north up): Per-Bastet (0.55,0.07), Mennefer (0.52,0.21),
Abidos (0.56,0.50), Vaset (0.62,0.65), Abu (0.58,0.90), Siwa (0.12,0.16), Harga (0.30,0.60), Saww (0.90,0.55).
Portrait-friendly (phones) and landscape. Also: `shipViewer` spec gains `dmg` 0..3; the river 3D view should show
`st.plan.dmg` (smoke / patched sail) and the redesigned race/dive kinds keep working (the race is a river kind
drawn by Sea — see D).

### D. Sea engine — sea.txt (owner: **deniz**)
* Redesign the **Sethi race** (`kind 'race'`) into a real race: both boats on the river, Sethi's AI steering and
  boosting, currents to catch, his wake/draft, obstacles, a finish line at the city quay, a live position gap.
  Keep the API: `Sea.play('race', o, cb)`, result `beat` boolean (+ existing fields). Make it a river kind (in `RK`,
  so `st.cfg` is set and the 3D view can draw it) unless that breaks something; tell the producer.
* Redesign the **wreck dive** (`kind 'dive'`) screen: clear underwater picture of the sunken boat, light from above,
  a breath bar that reads instantly, simple controls (tap/drag direction on phone, arrows on desktop), items as clear
  shapes (amphorae, chests, the quest lute when `o.special==='lute'`), eels with readable warnings. Keep the result
  fields (`coins, crates, goods, special`).
* `o.dmg` 0..3: draw the player's boat damaged accordingly in river scenes (patched sail, smoke at 3).

### E. Haggling 2.0 and the Senet tutorial (owner: **bulmaca**) — haggle28.txt/.css, senet.txt/.css
* `haggleDeal(o, cb)`: one negotiation about ONE good. `o = { ci, g, side:'buy'|'sell', qty, unit, stock,
  stockFull, want, trust, mood, seed, who }` (`unit` = current unit price, `stock`/`stockFull` = the merchant's
  shelf, `want` = city multiplier for that good: >1 means the city craves it, <1 means it is plentiful there,
  `trust` 0..3, `mood` −1..1). Willingness: buying a good he is overstocked on, or selling him a good his city
  craves, leaves a lot of room; low stock / unwanted goods leave little. The player must be able to *guess* this
  from visible cues: the shop shelf drawn in the scene of the haggle (full / half / empty crates), the big bust
  (`bustSVG(o.who, {mood, tell})` — fall back to `portrait()` if bustSVG is missing) with face + body-language tells
  that mean "has room" vs "near his limit" per merchant (each merchant has their own tells; occasionally bluffs),
  and his lines. Simple choices only (e.g. three offer buttons + "Kabul" + "Vazgeç"; maybe "Övgü" / "Gidiyormuş gibi
  yap"), at most ~3–4 rounds, readable by a non-gamer. Learned tells are remembered in `meta.tells28[ci]` and shown.
  `cb({ done:true, mult, angry })` exactly once — `mult` is the final unit-price multiplier (e.g. 0.84 when buying,
  1.12 when selling); `done:false` = no deal. `PZ.kind='haggle'`, `haggleAuto()` test helper.
* Senet tutorial: `playSenet({ stake, who, cb, tutorial:true })` — the first game is coached by Paneb
  (`bustSVG('paneb', …)` in a speech bubble, fallback if missing): sticks, moving, swapping, safe squares, the water
  square, bearing off — taught *while playing* one step at a time, plus a "Kurallar" button showing a one-screen
  picture card of the rules. Normal games unchanged.

### F. Main screen, flow and core (owner: **arayüz**) — ui.txt, core.txt, body.txt, css.txt, css28.txt, boot.txt
See that developer's own brief. Uses A–E through the contracts above, with fallbacks while they are missing
(portScene/oasisScene, portrait(), the SVG map, old race/dive).

## Delivery
Copy ONLY the files you own into `ROOT/deliver28/<yourname>/`, plus your test scripts (`test-*.js`) and 3–5
representative screenshots. Final message (≤ 400 words): what you built, exact public functions, what the producer
must wire up, known limits. Do not edit outside `ROOT/work28/<yourname>/`, `ROOT/out/`, `ROOT/deliver28/<yourname>/`.
