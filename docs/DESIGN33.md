# Nil Kervancısı — v33 studio brief (shared by all agents)

ROOT = /tmp/claude-0/-home-claude/50408ee7-81cd-5d20-8660-e495325793de/scratchpad

## The game
Single-file HTML browser trading game (Turkish UI, ancient Egypt, Nile). 30 days, 8 cities (5 river, 3 desert by caravan), market trading, voyages with minigames, 3D isometric town (Three.js r128), 3D river at sea, 3D isometric travel map. Players: the owner on a Samsung Galaxy S26 phone (portrait, 120 Hz) and an M1 MacBook. Design rules: "simple enough for my mother", fluidity first, attractive 3D. Stylized, warm, clean cel/toon look with ink outlines (see current town).

## Source and build
- Frozen base: ROOT/base33 (do NOT edit). Your private copy: ROOT/work33/<you>/src. Deliver changed files ONLY to ROOT/deliver33/<you>/ (same file names as in src, plus any new files) with a NOTES.md describing every change, new public APIs and how to test.
- Build: `python3 ROOT/p32/assemble.py <your src dir> <outname>` writes ROOT/<outname>.html and ROOT/<outname>-preview.html (run from ROOT; it reads backup-v8.html there). Use outname like `w33-<you>` so agents do not collide. Order of JS: core, merchants, merch27, portrait, snd, sea, ui, then modules art27, art28, chars28, chars30, portraits31, v3, town29, temple, senet, mini, haggle28, boot. If you add a new module file, ALSO patch your copy of assemble.py (copy p32/assemble.py into your work dir, edit, run that) and mention it in NOTES.md.
- Syntax check: extract the last <script> of the built html and run `node --check`.
- Tests: Playwright (node, require('playwright')); chromium args ['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']; route https://cdnjs.cloudflare.com/** to ROOT/vendor/node_modules/three/build/three.min.js; set localStorage 'nil-kervanci-3d'='1' and meta (see ROOT/qa31/shots.js); start: click [data-act="new"], then [data-act="heroGo"]. Debug hooks: window.__nil (S, fn.openSpot('market'|'ship'|'temple'|'tavern'|'yard'|'hapu'|'board'|'work'), fn.closeSheet(), fn.travelTo(i), fn.showTravel(i), fn.playScene(kind,nodeType), render(), V3, T3). Helper lib: ROOT/audit31/qa/lib.js (env HTML=path OUT=dir). Regression suite at the end: `node ROOT/qa31/test-arayuz.js <abs path to your preview html> <outprefix>` must print ALL OK; 30-day bot `node ROOT/qa31/t153_28.js 1 <abs preview path>` must show errs: none. Bash calls have a 10-minute limit: run long jobs with nohup in background and poll.
- Look at your screenshots yourself (Read the png) at 412x915 phone and 1280x720 desktop. Swiftshader is slow: judge visuals, not fps; for cost use renderer.info and CPU throttling (CDP Emulation.setCPUThrottlingRate 4).

## Hard constraints
- Performance is a feature: phone must stay smooth. One shared WebGL renderer exists (V3 GLS: X.glsClaim / glsRelease); do not create extra WebGL contexts unless unavoidable (and then one, reused). Dispose everything you create (geometries, materials, textures, skeleton.dispose()). Cap frame rates (town 30 fps, others ≤60). No allocations in per-frame loops.
- Big binary assets (GLB, textures) must NOT be parsed as JS at startup: embed as base64 inside `<script type="application/octet-stream" id="...">` blocks (or similar inert container) and decode lazily on first use; keep total new payload modest and report its size.
- 3D off (localStorage 'nil-kervanci-3d'='0') or WebGL failure must still work with the existing 2D/portrait fallbacks.
- Keep all UI text Turkish. No new external network dependencies (only cdnjs three r128 already used).
- Blender: `import bpy` works in this container (Blender 5.2.2, Cycles/EEVEE CPU). glTF export works.
- Prior art: DESIGN30.md, deliver31/karakter/blender (portrait pipeline), chars30.txt (current procedural 3D figures, FIG API), town29.txt (3D town), v3.txt (river, map table, ship viewer, Kit/bake).
