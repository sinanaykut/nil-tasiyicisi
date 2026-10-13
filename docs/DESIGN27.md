# Nil Kervancısı v27 — studio brief (read fully before you start)

Scratchpad root: `/tmp/claude-0/-home-claude/50408ee7-81cd-5d20-8660-e495325793de/scratchpad` (call it ROOT).

## What the game is
A single-file HTML browser trading game set in ancient Egypt, played mostly on phones (Galaxy S26 Chrome) and
sometimes desktop. Everything visible to the player is **Turkish**. Style: flat "tomb painting / papyrus" look —
warm paper colours, ink outlines (`#2B1D14`, ~1.5–2.5px), bold flat fills, gentle CSS animation. Design rule from
the owner: *"must not be complicated even for my mother"* — few words, big tap targets, pictures over paragraphs,
no drag-and-drop, nothing that needs fine motor timing to *progress* (timing games are fine as optional bonus).

## How the code is built
* Source parts live in `ROOT/p27/` (the producer's live copy) — **do not edit p27**. A frozen snapshot for you is
  `ROOT/base27/`. Make your own working copy: `cp -r ROOT/base27 ROOT/work/<yourname>` and work there.
* Build: from ROOT run `python3 base27/assemble.py work/<yourname> out/<yourname>` → writes
  `ROOT/out/<yourname>.html` and `ROOT/out/<yourname>-preview.html` (the preview is a full page you can open with
  Playwright: `file://ROOT/out/<yourname>-preview.html?debug`). Create `ROOT/out/` if missing.
* Syntax check: extract the `<script>` body and run `node --check`, e.g.
  `sed -n '/<script>/,/<\/script>/p' out/x.html | sed '1d;$d' > out/x.js && node --check out/x.js`.
* All JS ends up inside ONE IIFE in this order:
  `core.txt` → merchants block → `merch27.txt` → portrait() → `snd.txt` → `sea.txt` → `ui.txt` →
  module files `art27.txt`, `v3.txt`, `temple.txt`, `senet.txt`, `mini.txt` → `boot.txt` (calls `start()`).
  Module CSS files `art27.css`, `v3.css`, `temple.css`, `senet.css`, `mini.css` (plain CSS, no `<style>` tag) are
  injected into the stylesheet. Extra icons go in `sprites27.txt` as `<symbol id="i-…" viewBox="0 0 32 32">…</symbol>`
  lines (they are inserted into the hidden sprite sheet; use them with `ico('i-x', size)`).
* Module rules: put code in **function declarations** or in `const` objects that are only used lazily (from event
  handlers / later calls). Never run code at load time that needs another module. Two-space indent, same code style
  as the rest (compact, comments in English, all player-facing text Turkish).
* Debug: with `?debug` the page exposes `window.__nil` = `{ S (state), meta, Sea, Snd, PZ, render(), vg(), V3,
  fn:{ pzTemple, playSenet, pzBaboon, showHaggle, … } }`. Your functions are exposed automatically if they are
  top-level function declarations with exactly those names.
* Playwright + Chromium are installed (`require('playwright')`, browsers in /opt/pw-browsers; never run
  `playwright install`). For WebGL in headless use
  `chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']})`.
  Google Fonts are blocked in this sandbox (harmless console errors). Test both 1280×720 and a phone
  (412×915, `isMobile:true, hasTouch:true`). Look at your screenshots with the Read tool.
* Before a new game shows, set meta so onboarding is skipped:
  `localStorage.setItem('nil-kervanci-meta10', JSON.stringify({rep:4,lv:{},ach:{},runs:3,noHints:true,tutDone:true,seenFeat:['haggle','crisis','sethi','quest','contra']}))`
  then click `[data-act="new"]`, then click `[data-act="qDecline"]` if present.

## Shared UI helpers you may call (defined in ui.txt / core)
`esc(str)`, `ico(id,size)`, `play(soundKey)` (keys: click, tick, no, good, bad, coin, fanfare, weigh, splash, …),
`buzz(hapticKey)`, `toast(text)`, `openSheet(html, lock, name, wide)` / `closeSheet()` (the modal "sheet"),
`xBtn` (close button html), `choiceHtml(c, attr, first)`, `banner(o)`, `portrait(merchantIndex, lvl)`,
`pth(d, fill, extra)`, `ink(w)` (stroke attrs), `grad(id, stops, vertical)`, `mix(hexA, hexB, k)`, `INK`,
`fmt(n)`/`fmtN(n)` number formatting, `meta` + `saveMeta()` (persistent meta progress), `S` (current run state),
`uid` (increment for unique SVG ids: `++uid`).
Mini-game framework: global `PZ` object (`PZ = { kind, tok:Math.random(), timers:[], cb, … }`), `pzClear()` clears it
and its timers; `closeSheet()` calls `pzClear()`. Puzzles render into the sheet with
`openSheet(html, true, 'pz')`. Look at `pzBalance`, `pzLiar`, `pzMemory` in ui.txt as reference. Click handling:
the global click handler in ui.txt dispatches `data-act` values; for your own buttons use your own delegated
listener on `#sheet` keyed by your own `data-*` attributes, OR `onclick` wiring after `openSheet` — keep it inside
your module (do NOT edit ui.txt).

## The v27 game design (producer implements core/ui; you implement your module against these contracts)

### World
River cities (index: id, name): 0 perbastet Per-Bastet, 1 mennefer Mennefer, 2 abidos Abidos, 3 vaset Vaset,
4 abu Abu. **New off-river cities** reached by donkey caravan from a hub river city (round trips only):
5 `siwa` **Siwa** (hub Mennefer, 3 days; Amun oracle, salt lakes, mud-brick Shali fortress, date palms),
6 `kharga` **Harga** (hub Abidos, 2 days; Hibis temple, date groves, wells),
7 `saww` **Saww** (hub Vaset, 2 days via Wadi Hammamat; Red Sea harbour — Punt ships, incense, ebony).
`CITIES[i].river` true/false, `CITIES[i].hub`, `CITIES[i].days`.

### Goods (ids, Turkish short names, base price)
bugday Buğday 16 · papirus Papirüs 50 · hurma Hurma 40 (new) · sarap Şarap 120 · tuz Tuz 90 (new, Siwa) ·
bakir Bakır 280 · sedir Sedir 620 · tutsu Tütsü 900 (new, Saww/Punt incense) · lapis Lapis 1400 ·
crafted: muska Muska 300 (faience amulet, made in Abidos) · kitap Ölüler Kitabı 450 (papyrus scroll, made in Vaset) ·
kyphi Kyphi 900 (temple perfume, made in Per-Bastet).

### Boats (`S.boat`)  — bought/sold at the shipyard
`nehir` Nehir teknesi (start: cap 40, hp 3) · `feluka` Feluka (fast, cap 35, hp 3, +1 sail, +1 rowers) ·
`mavna` Yük mavnası (slow wide barge, cap 80, hp 4) · `kadirga` Sedir kadırga (big cedar galley, cap 70, hp 5,
+1 sail, +2 rowers). Upgrades per boat as before: `S.up = {govde, yelken, kurek, ambar}` each 0–2.
**Ship devices** (`S.dev = {burun, fener, goz}` booleans, crafted from goods at the Mennefer shipyard):
`burun` Bakır mahmuz (copper ram on the bow; ignores the first hit each voyage),
`fener` Gece feneri (bronze lantern on the stern post; night patrol lights smaller),
`goz` Horus gözü (big painted Eye of Horus on the bow; fewer chasers).

### Desert caravan
Off-river trips use donkeys (historically accurate — no camels). The player rents 2–8 donkeys; each carries
10 units. The caravan carries **water** (in "days"); every day costs water; at 0 water the caravan loses a donkey
per day. The trip is a node map like the river voyage, whose action scenes are the river engine in desert skin.

### Sea engine contract for desert scenes (owner: "çöl" agent, file sea.txt)
`Sea.play(kind, o, cb)` — existing kinds calm, rapids, chase, night (+ storm, dive, race special scenes).
New: when `o.terrain === 'desert'` the river kinds are played as desert walks:
* `calm` → "Kum tepeleri" (dune field walk), `chase` → "Çöl akıncıları" (chaser type `bedevi`, name
  'Çöl akıncıları'), new kind `sandstorm` → "Kum fırtınası" (only used with terrain desert: low visibility like
  night + lateral gusts that push the caravan; it must be in `RK` so `st.cfg` is set).
* In desert state set `st.desert = true`. Obstacle kinds (`st.obs[].k`): `dune` (wide low dune ridge — like sand
  bar), `boulder` (rock), `snake` (static coiled cobra, strikes when near), `scorpion` (small, scuttles sideways
  like a log), `quick` (quicksand: pulls like a whirlpool). Pick kinds (`st.picks[].k`): `water` (water skin,
  counts into `res.water`), `coin`, `crate`, `date` (refills one "Koş!" charge — replaces lotus), `ankh`.
* The player's "boat" is a donkey caravan (lead donkey + 2–3 donkeys behind, a driver). `o.donkeys` (2–8) can
  set how many donkeys are drawn (cap the drawn number to keep it readable).
* Result object gains `water` (number of water skins picked). Everything else in the result stays as is.
* Season palettes are irrelevant in the desert; use a desert palette that still follows `st.tod` (dawn → dusk).

### 3D view contract (owner: "3B" agent, file v3.txt)
`Sea.setView(view)` registers a renderer. While a river-kind scene runs (`st.cfg` truthy) Sea calls
`view.wants(st)` each frame; if true, Sea clears its 2D canvas to transparent, calls `view.draw(st, api)` and then
draws only its 2D HUD on top. If `draw` returns `false` or throws, Sea falls back to 2D. `view.hide()` is called
when the 3D picture should disappear (scene over, special scenes). `api = { W, H, dpr, sx(u,y), sy(y),
centerX(y), halfW(), boatY(), hash(n), C (colours), RIVAL (chaser colours), P (season palette), RV (river params),
coarse }`. World: `st.dist` = distance travelled forward, objects have world `y` (forward) and lateral `u`
(−1..1 of the half width); screen x of a thing is `sx(u, y)`, screen y is `sy(y)`; the player is at `st.u`,
`st.dist`. See sea.txt `draw()`, `drawObs`, `drawPick`, `boat`, `drawNight` for everything that must be shown.
Desert kinds (above) must also be drawn in 3D (sand ground, dunes, the caravan).

### Module function contracts (owner: "bulmaca" agent)
* `pzTemple({ title, sub, level, seed, cb })` — temple light-and-mirror room. `level` 0..4 (difficulty).
  Calls `cb(q)` exactly once with `'perfect' | 'good' | 'miss'`. `PZ.kind = 'temple'`. Must provide
  `templeAutoSolve()` (test helper) that solves the current room through the same code path a tap uses.
* `playSenet({ stake, who, cb })` — tavern Senet against an AI (`who` = opponent display name).
  `cb({ win:boolean, stake })` exactly once (also on give-up = loss). `PZ.kind = 'senet'`. Provide
  `senetAuto()` that plays the player's turns automatically (test helper).
* `pzBaboon({ n, dur, cb })` — baboons raid the cargo on the quay: tap them away. `cb(caught, total)`.
  `PZ.kind = 'baboon'`. Provide `baboonAuto()`.

### Art contract (owner: "sanat" agent)
* `shipSVG2(spec, loadN, id)` — like ui.txt `shipSVG(up, cargo, id)` (same coordinate system: stern left, bow right,
  waterline y=0, fits viewBox `-250 -236 500 290`) but `spec = { boat, up, dev }` draws the four boat types with
  their upgrades and the three devices.
* `oasisScene(ci, si, day, nar, mood)` — harbour picture for the off-river cities 5,6,7, same frame as ui.txt
  `portScene` (viewBox `0 0 900 400`, `preserveAspectRatio="xMidYMax slice"`, `class="ps"`), using `dayPal(si,day)`
  for the time of day, `merchantFig(ci, mood)` for the merchant and the caravan of donkeys instead of our ship.
* `merch27.txt`: `MERCHANTS.push(...)` three desert merchants (indexes 5,6,7 — same object shape as existing
  merchants: name, title, fav, favQty, reward, look, lines[4][2], thanks), `MERCHANT_NAMES.push(...)`,
  `FAVS.push(...)`, and a `const DESERT_UI = { faceLines:[…3], mtell:[…3], favStyle:[…3], duel:[…3] }` with the same
  shapes as `FACE_LINES`, `MTELL`, `FAV_STYLE`, `DUEL_M` in ui.txt.
* `sprites27.txt`: icons `i-hurma i-tuz i-tutsu i-muska i-kitap i-kyphi i-c-siwa i-c-kharga i-c-saww i-donkey
  i-water i-temple i-senet i-baboon i-locust i-workshop i-boat i-burun i-fener i-goz`.

## Delivery
When done, copy ONLY the files you own into `ROOT/deliver/<yourname>/` (e.g. `v3.txt`, `v3.css`), plus any test
scripts you wrote (`test-*.js`) and 2–4 representative screenshots (`*.png`). Your final message: what you built,
the exact public functions, anything the producer must wire up in ui/core (be concrete), known limits. Keep it
under 400 words. Do not edit files outside `ROOT/work/<yourname>/`, `ROOT/out/` and `ROOT/deliver/<yourname>/`.
Three.js r128 for local testing: `ROOT/vendor/node_modules/three/build/three.min.js` (in Playwright, route
`https://cdnjs.cloudflare.com/**three.min.js` to that file with `page.route`).
