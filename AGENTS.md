# Nil Kervancısı — notes for AI coding agents (Gemini CLI, Jules, others)

A single-file HTML browser trading game set in ancient Egypt (Nile trade, desert caravans). The source lives in `src/`; a build step joins it into one HTML file.

## Owner and design rules
- The owner writes in Turkish. Answer in Turkish, and write all in-game text in simple, natural Turkish.
- Target devices: Samsung Galaxy S26 phone (portrait, 412x915 CSS px, 120 Hz) and an M1 MacBook.
- Design rules: "simple enough for my mother", smoothness first, attractive 3D/isometric look.

## Workflow (important)
- Work on a new branch and open a pull request. Never push directly to `main`. The owner and Claude merge, test and publish.
- Keep each change small and focused on one topic. Don't reformat unrelated code.
- Don't touch `site/sw.js` and don't publish anything. Releases (version bump, claude.ai artifact, Netlify zip) are done on the Claude side.
- In the PR description, say in Turkish what changed and how you checked it.

## Build
- `./build.sh` writes `dist/`, which is git-ignored, so don't commit it. `dist/preview.html` is the file to open and test.
- `src/assemble.py` holds the concatenation order. Everything ends up in one IIFE, so top-level names are shared.
- Folders `src/ui`, `src/sea` and `src/v3` are big files split by section. Their parts are joined in name order and share scope.
- Source map: `docs/kaynak-haritasi.md`. Grep first and read only the part you need. Some files are very large; `src/chars33.dat` is binary data, so don't open it.
- Syntax check: extract the last `<script>` of `dist/nil-kervanci.html` into a file and run `node --check` on it.
- Debug: open `dist/preview.html?debug`. `window.__nil` exposes:
  - `S`: the game state
  - `fn.*`: `openSpot`, `closeSheet`, `travelTo`, `showTravel`, `playScene`, `buyN`, `sellN`
  - `render`, `V3`, `T3`

## Tests (optional, need Playwright + Chromium)
The scripts are in `tools/qa/`. Each has a hard-coded `ROOT` path near the top; change it to your setup before running.
- `test-arayuz.js <abs preview.html> <outprefix>`: must print `ALL OK`.
- `t153_28.js 1 <abs preview.html>`: the 30-day bot. Must end with `errs: none`.

## Technical constraints
- Three.js r128, loaded from cdnjs only. One shared WebGL renderer (V3 GLS claim/release).
- Dispose everything and avoid allocations per frame. Town runs at 30 fps; other scenes at most 60.
- With 3D off (`localStorage['nil-kervanci-3d']='0'`), the game must keep working through its 2D fallbacks.
- Close-up characters are code-drawn SVG (CH40 in `src/chars40.txt` + `src/chars40.css`). Town walkers are 3D (`src/chars33.txt` + `chars33.dat`).
- Economy changes need care: there is a same-day buy/sell cap, and the 30-day bot checks that the balance still works.
