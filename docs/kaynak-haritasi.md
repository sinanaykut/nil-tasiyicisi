# Nil Kervancısı source map (v40)

Build: `./build.sh` (runs `python3 src/assemble.py`) → dist/. Order is in assemble.py.
Folders ui/, sea/, v3/ are single files split by section; parts are joined in name order (same IIFE scope, so names are shared).

| part | KB |
|---|---|
| art27.css | 1 |
| art27.txt | 68 |
| art28.css | 5 |
| art28.txt | 92 |
| assemble.py | 5 |
| body.txt | 4 |
| boot.txt | 3 |
| chars30.txt | 60 |
| chars33.dat | 649 |
| chars33.txt | 90 |
| chars40.css | 5 |
| chars40.txt | 90 |
| core.txt | 79 |
| css.txt | 64 |
| css27.txt | 6 |
| css28.txt | 51 |
| haggle28.css | 10 |
| haggle28.txt | 35 |
| logo31.txt | 27 |
| merch27.txt | 6 |
| mini.css | 3 |
| mini.txt | 13 |
| motion35.css | 11 |
| sea/01-run-setup.txt | 33 |
| sea/02-run-steer.txt | 27 |
| sea/03-run-draw.txt | 46 |
| sea/04-run-scenes.txt | 40 |
| sea/05-special-scenes.txt | 7 |
| sea/06-special-scenes-2.txt | 62 |
| senet.css | 9 |
| senet.txt | 39 |
| snd.txt | 40 |
| sprites27.txt | 14 |
| sprites28.txt | 2 |
| temple.css | 3 |
| temple.txt | 26 |
| temple42.css | 9 |
| temple42.txt | 44 |
| tavern42.css | 7 |
| tavern42.txt | 49 |
| town29.css | 2 |
| town29.txt | 134 |
| ui/01-port-scene.txt | 36 |
| ui/02-faces.txt | 26 |
| ui/03-state-render.txt | 25 |
| ui/04-feedback-sheets.txt | 28 |
| ui/04b-motion.txt | 7 |
| ui/05-actions.txt | 3 |
| ui/06-voyage.txt | 54 |
| ui/07-heroes.txt | 13 |
| ui/08-puzzles.txt | 24 |
| ui/09-haggle-story-board.txt | 32 |
| ui/10-share-device-water.txt | 16 |
| ui/11-places27.txt | 6 |
| ui/12-hub.txt | 36 |
| ui/13-hub-sheets.txt | 48 |
| ui/14-input.txt | 18 |
| ui/15-start.txt | 1 |
| v3.css | 8 |
| v3/01-core-kit.txt | 35 |
| v3/02-river.txt | 44 |
| v3/03-river-2.txt | 37 |
| v3/04-map-table.txt | 36 |
| v3/05-map-table-2.txt | 69 |
| v3/06-rays-export.txt | 16 |
| v8-merchants.txt | 4 |
| v8-portrait.txt | 1 |
| v8-sprites.svg | 20 |
| world33.txt | 55 |

v35 motion & menus: `motion35.css` holds the motion tokens (`--m-*` durations, `--e-*` easings; reduced motion sets them to ~0), sheet rise/stagger/ghost-close, toasts, HUD pops, the papyrus curtain and the boot splash. `ui/04b-motion.txt` has `curtain(card, fn, opt)` (covers big scene changes: new run, hub→river, landing, waiting a day), `sheetMotion`/`sheetGhost` (used by openSheet/closeSheet), `hudNum`/`hudFlip` (HUD count-up and day flip) and `bootDone`.

v40 characters: every close-up character is drawn in code. `chars40.txt` holds `CAST` (names, titles, ring colours) and `CH40`:
one SVG rig (head/jaw path, ears, kohl eyes with iris clip, tapered brows, noses, closed and open mouths with teeth/tongue, wigs:
bob/longbob/shoulder/long/braids/shortwig/crop/curly/curls/bald/wrap, bands, beards, usekh and other collars, clothes, props, hands)
and a recipe per character in `REC` (heroes h_*, merchants '0'..'7', paneb hapu sethi merenre djedi nakht tv0 tv1 tv3 tv4 tv7 guard priest scribe folk).
Expressions are rows of `EX` (neutral happy laugh angry surprised thinking sad blink talk talk_happy talk_angry talk_surprised + sly);
haggle tells (sweat glance smile frown tap arms lean scratch eyebrow) change the face or add arms/hands (`tellParts`).
API: `CH40.svg(who, { mood, tell, frame:'bust'|'card'|'head'|'face' })` (strings are cached per look; ids get a fresh suffix),
`CH40.icon(who, mood)` (round face for badges, strips, HUD), `CH40.stage(el, who, { mood, tell, frame })` → `{ update({ mood, talk, tell, act }), react(kind), dispose() }`.
Life is CSS only (`chars40.css`): breathing, blinking (`.c40bl` overlay), head sway, mouth frames `.m0/.m1/.m2` while `.talk`, crossfade
between moods, tap = laugh + hop; reduced motion stops all of it. `portrait(i, lvl)` (v8-portrait.txt) and `faceOf(who, mood)` are thin wrappers.
Used by: say() dialogues (merchants, Paneb, Hapu, heroes, tavern players), haggle bust (#hgBust), Senet coach + rival badge,
hero pick cards, HUD plate / quips / scene overlay (heroImg), market header, Hapu sheet, guide strips, story/board badges, ledger.
The 3D town people stay on chars33 (FIG.build/animate re-pointed, chars33.dat); its close-up stages and snapshots were removed.
`logo31.txt` keeps the title emblem that used to live in the portrait pack.

v41 town & map fixes: `chars33.txt` sampleInto builds its face-bone mask itself (town figures were frozen in the bind pose since v40);
town walk cycle runs at the walker's speed (`t * v / 8.6`), walkers and movers ease their turns (`turn()`), a play clock (`clk`, map `mclk`)
replaces the wall clock; the still mode retries full speed after 6 s (doubling) and ignores single stalls > 1 s. Kit lines (`bakeLines`):
positive-width crease lines stay culled (the look never had them), negative-width leaf/frond edges are drawn; fronds are `noOut` and
cancelled outline normals fall back to the vertex normal (no black wedges). Paths, boats, rocks, role figures and plaques were moved off
each other (debug: `T3.debug()` returns B (with B.puts), figs, movs, dyn, zp, frame). Saww reached by caravan: donkeys on the quay, not our
ship in the sea. Map: river boats fade at both ends of their run, caravan beasts follow in phase and turn smoothly. 2D map in caravan
prep: town buttons scaled with the smaller map. Images: docs/qa41.

v42 temple & tavern games: `temple42.txt` adds four temple riddles next to the mirror room (`temple.txt`): glyph (spell a king's name in a
cartouche from the priests' sign list; worn-off signs are read from an example cartouche), slide (sliding relief stones, A* solver),
scale (balance Maat's scale with deben weights: table → right pan → left pan), stars (turn the ceiling rings, some chained, until the
constellation sits in its gold rings). All are PZ.kind 'temple' with PZ.type; `pzTemple({ type, level, seed, cb })` dispatches,
`templeTypeFor(ci, rs)` gives each temple city its type (shuffled per run), goTemple (ui/11) raises the level with every temple solved.
The mirror room gained a second (lapis) statue lit through the prism at levels 3–4. `templeAutoSolve(gap)` solves every type through the
real buttons. `tavern42.txt`: Mehen (snake board, 2 lions, 3 sticks, hits send home, eye scales safe) and Hounds & Jackals (palm board,
3 pins, one knucklebone 1/3/4/6, shortcuts 6→20 and 8→12, pit 24→16) on one race engine (`TG`, `playTavernGame(id, o)`) with
Paneb's first-game coaching (meta.mehenTaught / houndsTaught) and a rules card; `tavernGames(ci, day)` picks today's game and the
alternative the host offers (ui/13 showTavern). Debug: `fn.playTavernGame`, `fn.tavernAuto({ fast })` (also drives Senet), `fn.TG`.
Images: docs/qa42-oyun.
