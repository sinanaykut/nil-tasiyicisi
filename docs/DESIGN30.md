# Nil Kervancısı v30 — studio brief addendum (read DESIGN28.md first for build/test rules)

Paths change: frozen snapshot `ROOT/base30/` (integrated v29 = live game), your copy `ROOT/work30/<you>/`,
build `python3 base30/assemble.py work30/<you> out/<you>30`, deliver to `ROOT/deliver30/<you>/`.
Module order now: … ui.txt → art27, art28, chars28, **chars30 (new)**, v3, town29, temple, senet, mini, haggle28 → boot.
CSS adds `chars30.css`. Owner's screenshots of v29 problems: `ROOT/ref/fb30-*.png`; style references `ROOT/ref/iso1.png`, `iso2.png`.

## Owner feedback on v29 (all in scope)
1. The long quay stone between the tiles and the water flickers/alternates light-dark along its length (fb30-quay).
2. Palm tree shapes are broken (fb30-town, fb30-quay).
3. When the window loses focus the town animations become very slow (and stay slow).
4. Characters at the market, tavern etc. must be 3D and carefully made (today: crude chibi blobs).
5. Player character faces must be designed much better, 3D if possible, and must NOT look like children.
6. The player's portrait in the right market panel is unnecessary — put the hero somewhere that makes the game feel personal.
7. The map must be redesigned from scratch: it isn't optimized and must reflect the game's character better (fb30-map).
8. The travel screens and travel mini-games must match the new game look (isometric, cel-shaded, ink outlines, warm palette).
Fluidity and 3D appeal stay the top priorities (phone first: Galaxy S26).

## New contracts
### FIG — 3D characters (owner: karakter) — `chars30.txt` (+ `chars30.css` if needed)
`const FIG = { keys, build(T, key, o) → THREE.Group, animate(group, t, state), portrait(key, o) → Promise<string dataURL> }`
* `T` = THREE (passed in; never touch window.THREE at load). Characters are stylized ADULTS (head ≈ 1/6.5–1/7 of height,
  real shoulders, necks, hands, clothing folds as shapes), Egyptian dress and props per role, cel/toon shading with 2–3
  steps and ink outlines matching the town (inverted-hull outline, ink #2B1D14). Faces: readable at small size from the
  isometric camera (eyes, brows, kohl, nose, mouth shapes; beards/wigs). Height 1.0 = adult; `o.scale` to resize.
* keys: heroes `h_ahmose h_neferet h_sitre h_bakenre`, `paneb`, merchants `0..7`, `hapu`, `sethi`, `tv0 tv1 tv3 tv4 tv7`,
  `priest`, `guard`, `scribe`, generic townsfolk `folk` (use `o.seed` for many varied men/women: porters with baskets
  or jars, fishermen, farmers, women with water jars, a few kids — clearly kids, small and few).
* `o = { seed, scale, mat:(hex)=>Material optional host material factory, outline:true, lod:0|1 }`; keep each figure
  light (≲ 1.5k tris at lod 0, ≲ 400 at lod 1) and share geometries/materials across instances.
* `animate(g, t, state)` with states `idle | walk | talk | wave | carry | sit | cheer` — subtle, cheap (rotate limbs).
* `portrait(key, {mood, size, bg})` renders a head-and-shoulders portrait with `V3.snap` (below), caches by key+mood+size,
  returns a dataURL; moods neutral/happy/angry/sly/surprised/thinking via face shapes. Used for hero cards, HUD avatar,
  dialogue busts. If 3D is unavailable the UI keeps the SVG `bustSVG/heroAvatar`.

### V3 additions (owner: 3B) — v3.txt / town29.txt
* `V3.snap(scene, camera, w, h)` → dataURL using the shared renderer (offscreen size, restores state).
* Town: use `FIG.build` for every person (merchant at the stall = merchant key, tavern host/players = tv*, priests at the
  temple, guards, workers at the yard/workshop, walkers = folk with seeds) with `FIG.animate`; fall back to your current
  people if `typeof FIG === 'undefined'`. New `o.hero` (hero key, e.g. 'h_neferet'): the player's hero stands on the quay
  by our boat as a spot `hero` (label = hero name) → onSpot('hero').
* Map: redesign (see the 3B brief). River 3D view: same art language as the town.

### UI (owner: arayüz)
* Remove the hero from the market header; the hero lives in the world (spot `hero` in the town), in a personal HUD
  profile (portrait + name), and on journeys. Use `FIG.portrait` when available.
* Travel screens (voyage route board, arrival summary, caravan prep, node cards) restyled to the new look.

### Sea scenes (owner: deniz) — sea.txt
* All 2D canvas scenes (river kinds as 2D fallback, desert kinds, storm, dive, race) restyled to the isometric cel look.
