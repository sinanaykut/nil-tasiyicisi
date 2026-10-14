# Nil Kervancısı — working notes for Claude

- The owner writes in Turkish: always answer in Turkish (including end-of-task summaries).
- The owner plays on a Samsung Galaxy S26 (portrait, 120 Hz) and an M1 MacBook. Design rules: "simple enough for my mother", smoothness first, attractive 3D/isometric look.
- Published as the claude.ai artifact https://claude.ai/artifact/RSqmbiw3S7LNGBdxBJBcgb: always update that same URL (read it first from a new session). Also hand over `dist/nil-kervancisi-site.zip` (Netlify PWA) and `dist/nil-kervancisi.html`.

## Build
- `./build.sh` → `dist/`. `src/assemble.py` holds the concatenation order (one IIFE). Folders `src/ui`, `src/sea`, `src/v3` are big files split by section; parts are joined by name order and share scope.
- Source map: `docs/kaynak-haritasi.md`. Read only the part you need; grep first.
- Bump the service worker cache name in `site/sw.js` (`nil-vNN`) on every release.
- Syntax check: extract the last `<script>` of `dist/nil-kervanci.html` and run `node --check`.

## Tests (Playwright, Chromium with swiftshader)
- `tools/qa/test-arayuz.js <abs preview.html> <outprefix>` must print `ALL OK`.
- `tools/qa/t153_28.js 1 <abs preview.html>` (30-day bot) must end with `errs: none`.
- `tools/qa/shots.js`: phone 412x915 + desktop screenshots. Always look at the screenshots.
- The scripts have a hard-coded ROOT path and route the cdnjs three.js request to a local copy (`site/three.min.js`); adjust before running. Bash calls are limited to 10 min: run long tests with nohup and poll.
- Debug hooks with `?debug`: `window.__nil` (S, fn.openSpot/closeSheet/travelTo/showTravel/playScene/buyN/sellN, render, V3, T3).

## Constraints
- Three.js r128 from cdnjs only; one shared WebGL renderer (V3 GLS claim/release). Dispose everything; no allocations per frame; town 30 fps, others ≤ 60.
- Large binary assets go in inert `<script type="application/octet-stream">` blocks decoded lazily (see `src/chars33.dat`).
- 3D off (`localStorage['nil-kervanci-3d']='0'`) must keep working with the 2D/portrait fallbacks.
- Close-up characters are code-drawn SVG (CH40 in `src/chars40.txt` + `chars40.css`): one rig, a recipe per character, 12 expressions + haggle tells, CSS-only life. They are the only close-up path in 3D and 2D modes; the town walkers stay 3D (chars33 + chars33.dat).
