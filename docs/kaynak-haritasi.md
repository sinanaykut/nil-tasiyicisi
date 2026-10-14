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
| snd-syn.txt | 54 |
| snd.txt | 30 |
| sprites27.txt | 14 |
| sprites28.txt | 2 |
| temple.css | 3 |
| temple.txt | 26 |
| temple42.css | 9 |
| temple42.txt | 44 |
| tavern42.css | 7 |
| tavern42.txt | 49 |
| quick45.css | 8 |
| quick45.txt | 33 |
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

v42 map miniatures & logo: `v3/04-map-table.txt` CITYK builds each token's diorama as `CITYK[id](k, L, S)`: k = still parts (baked into
the still image), L = moving parts (palm crowns sway, pennants swing via the SWING define, Kharga's shaduf), S = smoke vents. Helpers:
`slab`/`plate`/`furrows` (ground layers: no hull ink, rims inked by drawn lines), `mPalm`, `mFlag`, `tower`, `cornice`, `bastet`, `nubian`,
`chapel`, `rock`, `mElephant`; W33 protos are stamped through `wput` (sphinx, osiris, rams, cats, baboon, incense trees, jars, tent).
`v3/05-map-table-2.txt`: city crease lines become drawn lines (short ones dropped, the LINE_V still-time bend removed) with their own small
depth bias (`cityL`); `lifeSet()` merges every visible town's L into one toon+ink mesh and S into one points mesh (SM_V/SM_F), rebuilt only
when a town appears/moves/dims; `uRow` drives the swing. The plinth is a 24-sided bevelled drum. 2D fallback map tokens: `MTOK`/`mapTok` in
`ui/13-hub-sheets.txt`. `logo31.txt`: `TITLE_SVG` (code-drawn seal) → `TITLE_LOGO`; title CSS (cartouche wordmark) in `motion35.css`;
site icons rendered from the same SVG. Images: docs/qa42-harita.
v42 route, tombs, arrival, race, desert orders (`ui/06-voyage.txt`, `ui/02-faces.txt`, `voy42.css`, `sea/01-02,04`, `v3/03-river-2.txt`, `core.txt`):
route map: lines run label-bottom → rim (column layout, read from `getComputedStyle(#vmap).flexDirection`) or rim → rim (row);
the boat/caravan token docks BESIDE the current stop (`dockAt`: on the incoming path, else to the side; scored against other stops,
labels and the header), the stop gets `.here` (gold ring), and the token sails along a bezier to the next stop (`VG.boatRaf`).
City emblems on start/end are small seals on the rim (`.vnode .vci`). Road temples are gone: river `tomb` (Kaya mezarı) and desert
`dtomb` (Kum mezarı; the old `ruin` light puzzle is no longer rolled) → `tombLock` (three seal stones, tap to turn to the cartouche,
torch = taps left) → `tombCoffin` (take one amulet safely, or everything: +2 muska +1 kitap/lapis +220 and a 40% curse: hull −1,
morale −2) or `tombDark` (torch out). Node choices may return `{ t, kind }`. Village market can caulk the hull (+1, 70 deben).
Arrival (`showArrival`): town picture via `V3.townThumb(ci, 520, 260)` (cached per city/season, painted port/oasis when 3D is off),
name plaque, route ribbon + days, ledger cells (river/road coins, losses or interest, hull or water, purse change `S.last.cash0`),
events sorted bad → good → info (first 4, "+N olay daha"), market news, sticky button.
Race: river 16% wider, we start right (u .4), Sethi left (u −.46) with a home side (`rv.home`, flips after we hold his side 1.4 s),
keeps ~84 px apart when side by side; Sethi sails a green/gold `kadirga` (a `feluka` when we own the galley), `st.sethiBoat`, with a
trail-based V wake in 3D. Orders: desert towns post orders for their cheap goods to Nile markets, hubs sometimes ask for Nile goods
carried to their oasis (`makeOrder`, `o.dz`); waiting a day may post a new order. Images: docs/qa42-yol.
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
v43 fixes (owner report): tavern boards on phones (`tavern42.css`/`.txt`): portrait sheets take the whole screen and the board takes
the room the panel leaves (both board SVGs absolute in `.tgbd`, `meet` keeps them aligned); legend + "Pes et" share the footer
(`.snfoot.tgft`, the foot line lives in the rules card); bigger Mehen cells/numbers, transparent finger-sized tap circles on cells
and pieces (`D.hit`, `D.ps` piece scale, `D.hr` highlight radius); Hounds & Jackals: drawers at the top of the palm right above
hole 1 (`HJ_H` 420, start pins at y 128); Senet's upright board shrinks on short phones and the landscape sheet never scrolls.
Town pan (`v3/06` zoomPan `opt.bound/room/ta`, `fix()`; `town29` `townBound`/`townBox`): the town pans at zoom 1 inside the
built town's box (merged geometry AABB in screen px), never tighter than the fit; touch-action `none` when there is room and
the page does not scroll. Orders on the map (`ui/13` `ordInfo`): gold mark = an order you carry there, dashed = an order waiting
on that town's board or where this board's order goes; a donkey marks caravan jobs; same marks on the travel chips (`ordChip`),
notes in the travel card, "Başka panolarda" list on the board. CH40 arms and hands (`chars40.txt` limbS/limb/finger/handBlock):
scratch = arm raised behind the head (drawn in the back layer, `scratchBack`) with fingertips over the crown (`scratchFront`),
tap = forearm on the counter + drumming hand, arms = forearms folded (clipped to the body), thinking = fist under the chin.
Road `ruin` nodes open the tomb seal (no light puzzle). chars33: the carry clip raises the left arm, so only head loads and
the shoulder jar use it; sack carriers and empty-handed walkers walk. Images: docs/qa43.
v45 economy & hold (`core.txt`, `ui/12-hub.txt`, `ui/06-voyage.txt`, `sea/01,03,06`, `css28.txt` tail): merchant storerooms persist per run —
`S.stockBase` (usual shelf), `S.stock` (now), `stockMax(S, i, g)` = base + `ROOM[g]` × city appetite (`stockWant`), `stockRoom(S, g)`;
selling adds to the stock, `quoteSell`/`dealSell` stop at the max (reason `'full'`, "depo dolu" on tiles, sell button, haggle hint);
`stockDay` drifts every shelf 45%/day back to its base, `stockMods` applies crisis/Sethi shortages and gluts; `finish()` sells with
`force` (end-of-run sale ignores storerooms). Voyage goods respect free hold space: `crateTake(S)` loads a crate at pickup through
the scene hook `o.cargo` ({ room(), take() }); a full hold leaves crates/amphorae behind (`res.left`, "Ambar dolu: N sandık geride
kaldı"), coins and blessings still count; tomb/oasis/events report what stayed behind. Wreck dive: the hull is solid (`dive.hull`
wall segments, `move` with sub-steps and slide, `inHull`, `way` routes through the one gap in the deck; touch steering follows `way`;
bumps cost a little breath; eels only reach their side of the hull). Hold card (`holdHtml`, `.hbody` → `showHold()` list sheet).

v45 travel map & caravan stop (`ui/13-hub-sheets.txt`, `ui/05-actions.txt`, `ui/12-hub.txt`, `v3/05-map-table-2.txt`, `town29.txt`, `art28.txt`, `map45.css`):
every town is always on the map (3D and 2D), the desert towns too (before the caravans open, from any town, with contraband): `mapModel()`
sends all cities, a far one with `why` (short reason) and `via` (`carVia`: "Mennefer'den · 3 gün"); desert roads are always drawn (`shut`
= paler before they open). Any town but the current one can be selected (`selectCity`): a town you cannot reach shows `farCard(i)`
(why not, the caravan hub and days, cheap/dear goods, orders, and an "Önce Mennefer'e git" button for the first leg, `wayTo(i)`);
the empty travel card lists unreachable desert towns in a "Kervanla" group; the 2D map draws the whole way (river to the hub + caravan) pale.
3D plaques (`labHtml`): from afar (tier 0) the name only (a far desert town adds "🐪 Mennefer'den"), days at mid zoom, prices close up;
the chosen town alone is a bubble (days · risk, cheap/dear goods, marks) and the separate route chip is gone. Tokens are smaller from afar
(`TSC()` 0.8 / 0.9 / 1 by tier; life parts, rings, hit and label geometry follow `o.g.scale`); a plaque pushed away from its token gets a
leader line (`.v3m-ll`). Caravan hubs (Mennefer, Abidos, Vaset) have a 'caravan' spot ("Kervan durağı", `spotsHere().caravan` when
desert travel is open): 3D town `CARHUB`/`CARSP` (three pack donkeys, a driver and jars on the quay south of the hero, dynamic parts),
2D `townScene` (two donkeys at the quay's west end); `openSpot('caravan')` opens the travel card on the hub's desert town (`carDest`).
Images: docs/qa45-harita.
v45 characters & tavern (owner report): CH40 scratch tell (`chars40.txt` scratchGeo/scratchUpper/scratchArm/scratchHand):
the character's own right arm is raised: `g.raiseL` gives torsoPath a raised right side (no hanging arm), the upper arm is drawn
before the body (the shoulder covers its root), forearm + hand in front of the hair; the hand is seen from the back, four fingers
curl into the hair (strands drawn over the tips), the thumb lies on the side of the head; `.c40sc` rocks the forearm about the
elbow, `.c40sk` rubs the hand. armband/copperBands/papyrus skip the raised side. tap: the forearm starts at the elbow under the
hanging upper arm. Icons (`frame:'face'`, badges 30–44 px) keep the eyes open (min opening, no squint, light lids, eyes ×1.12);
thinking opens the eyes wider. Senet (`senet.txt`): water = splash (`snSplash`, rings + drops in `#snFx`), the piece sinks
(`.wet`), a wake (`snWake`) carries it to 15 (or the first free square before it) and it rises (`.reborn`); "başka hamlesi
yoktu" when forced; the rival's badge face reacts (`snFace(mood, ms)`, also used by Mehen/Hounds hits, shortcuts, pits, homes,
wins). Hounds & Jackals: HJ_H 440, holes r 10/12, pins ×1.4, 1–10 middle, 11–21 edge, 22–29 over the crown (ellipse
HJ_RX/HJ_RY around HJ_AY), shen at y 36; any pin in the same hole/drawer moves (tgTapPiece). Quick bets (`quick45.txt/.css`):
asik (knucklebones duel, ≈47 %), bakla (shell game, adaptive pace `meta.qShell.r`), tekcift (odd/even sticks, 50 / 43.75 %);
`S.tq[city] = { d, n }`, 3 a day per tavern, stakes 50/100/300; money moves when the outcome is fixed (`qkSettle`), the show
follows (`qkShow`). Tavern menu (ui/13 showTavern): "Uzun oyunlar" = the dialogue choices, "Kısa oyunlar" = `quickMenuHtml(ci)`
tiles (`opts.html`); ui/12 keeps the tavern pin bright while quick bets remain. Debug: `fn.showQuick(id)`, `fn.quickAuto({ fast,
n, cheat })` (tavernAuto drives it too), `fn.quickSim(id, n, call)`, `fn.quickLeft()`. Images: docs/qa45-oyun.

## Music (v44)
- `snd-syn.txt` — `NilSynth()`: self-contained music synthesiser (its source text is also the render Worker's body, so it must not use game names). Instruments (Karplus-Strong oud/bass, modal harp/kanun, ney/reed wind phrases, wavetable drones/choir, modal darbuka/bendir/tabl/riq/sistrum/zills/bowl), buses + EQ, ping-pong echo, half-rate FFT convolution reverb, master compressor + soft ceiling, the six compositions (`composeMenu/Port/Bazaar/Temple/Sail/Chase`) and `TRACKS` (tempo, bars, reverb, measured bus gains and loudness trims). `job(name)` renders in steps (`step(ms)`), `onSeg` streams 1 s segments.
- `snd.txt` — `Snd`: Worker (or main-thread slices) renderer, streaming first playback, IndexedDB cache (`MUSIC_VER`, bump it whenever the music changes), at most 3 decoded tunes (LRU), crossfades by mode, effects.
- QA renders and loudness notes: `docs/qa44-muzik/`.

