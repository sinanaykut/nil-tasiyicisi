# Paneb prototype (CH34): CC0 Quaternius base + UAL clips

## What was built

- **Rig and clips.** The Quaternius Universal Base Characters (male "Superhero") and both UAL libraries use the same 65-bone UE-style skeleton with the same bone names. Their rest poses differ, though: up to about 11° at `spine_03` and the thumbs, and the bone lengths differ too. So `blender/anims.py` does a **world-space retarget**: for each bone, `R_tgt = R_tgt(parent) · (rest offset)⁻¹ · R_src(parent)⁻¹ · R_src · (rest offset)`. The pelvis translation is scaled by the hip-height ratio. It then bakes at **20 fps**. Leaf bones are not keyed.
- **Body** (`blender/body.py`)
  - The superhero bulk is reduced with a per-bone radial shrink around each bone segment, blended by the skin weights. Shrink factors: arms 0.78/0.86, clavicles 0.72, neck 0.78, chest 0.86 and so on.
  - The head is 1.16× larger.
  - Face: the mouth cavity was cut and the holes were filled. Every front-face vertex was then projected onto an **authored smooth face surface**: a centre-line profile, blended into the real head sides, plus a short Gaussian nose. A tangential relaxation removes folds.
  - Faces that are always hidden under the kilt are deleted. The mesh is decimated with symmetry, and its normals are taken from a smoothed copy so the cel bands come out clean.
- **Costume** (`blender/parts.py`). Every piece is procedural and fitted with ray casts or nearest-surface snapping:
  - Egyptian bob wig with a straight fringe and a straight curtain around the ears and jaw
  - red headband with two tails
  - shendyt kilt: a convex-hull slice envelope with flare and a pleated front apron; its weights move from pelvis to thighs with depth
  - red/gold belt
  - 5-band usekh collar (gold / turquoise / red / blue / turquoise beads)
  - gold armbands

  Colours are point colours. A `_FX` attribute holds the ink width and the shader fx code (hair strands, pleats, beads, gold, face).
- **Face** (`tools/face_atlas.py`). It is not deformed. A 512² RGBA atlas holds channel-packed sprites: 8 eye states (with the kohl wing), 6 brows, 1 nose and 15 mouths. The fragment shader projects them onto the head using the **rest-pose x/y**, so animation cannot break them. The iris and pupil are drawn in the shader inside the eye-white mask, so the eyes follow the pointer. A soft blush is also drawn in the shader.
- **Clips (10):**

  | Clip | Source |
  |---|---|
  | idle | UAL1 Idle_Loop |
  | talk | Idle_Talking_Loop |
  | angry | UAL2 Idle_FoldArms_Loop |
  | cheer | UAL2 Yes |
  | happy | Dance_Loop |
  | walk | Walk_Loop |
  | carry | UAL2 Walk_Carry_Loop |
  | **wave**, **think**, **shrug** | keyframed: 2-bone IK on top of idle, open hands |

- **Runtime** (`src/chars34.txt`, module `CH34`, the same handle API as `CH33.stage`)
  - Rendering: toon cel and the CH33-style inverted-hull ink, with the same light and rim values as the CH33 stage. It uses the shared V3 renderer through `glsClaim`/`glsRelease`.
  - Animation: `THREE.AnimationMixer` with crossfades. One-shot clips play back into the mood clip.
  - Face: blinks (with occasional double blinks), random visemes while the text types (a per-mood viseme set), and a mood mapped to eyes, brows, mouth, blush and clip.
  - Interaction: a tap cycles laugh / wave / cheer / shrug. The head (split neck 35% / head 65%) and the irises follow the pointer. Paneb waves when the dialogue opens.
  - Disposal: materials are disposed, the mixer is uncached, and the canvas is released. The geometry, clips and atlas stay cached, like CH33's KIT.
  - Assets sit in inert blocks (`#c34glb` gzip+base64, `#c34face` lossless WebP) and are decoded on first use.
- **Gating.** `CH34.has('paneb')` requires 3D on (`V3.pref()`) and the data block. It ignores the `face3d` opt-in. It is used in `say()` for Paneb and in the senet coach. Everything else is unchanged. With 3D off, the dialogue keeps the 2D bust (`screenshots/m-2d-01-greet.png`).

## Repo changes (uncommitted)

- New files: `src/chars34.txt` (25 KB) and `src/chars34.dat` (214 KB).
- `src/assemble.py`: `chars34.txt` added to MODULES; `chars34.dat` is placed after `chars33.dat`.
- `src/ui/12-hub.txt`: `say()` tries CH34 first, then CH33, then the 2D bust.
- `src/senet.txt`: the coach uses CH34 when available.
- The diff is in `edits.diff`.
- The service-worker cache name was **not** bumped. Bump `site/sw.js` if this goes out as a release.

## Sizes and performance

| | |
|---|---|
| Triangles | **7,746**: body + face 4.6k, wig 1.45k, kilt 0.6k, collar 0.4k, band 0.28k, belt 0.24k, armbands 0.19k |
| Vertices | 4,313 |
| Draw calls | **2** (body + ink hull); 15.5k tris rendered |
| Material | 1 cel material + 1 ink material; no body texture; one 512² face atlas |
| GLB | **402,576 B raw / 129,467 B gzip / 172,624 B base64** |
| Atlas | 30,684 B WebP (40,912 B base64) |
| `chars34.dat` total | 213,677 B (for comparison, `chars33.dat` is 664 KB) |
| GLB packing | KHR_mesh_quantization; i8 normals, u8 colour, weights and fx; i16 rotations; constant tracks dropped; linear key reduction (0.006 rad); about 50 tracks per clip |
| Load | decode + parse happen once (lazy, the first time Paneb speaks) |

## How to rebuild

```
./rebuild.sh            # Blender build -> retarget/bake/export -> pack -> atlas -> chars34.dat -> harness.html
cp out/chars34.dat <repo>/src/ && ./build.sh
```

The Blender scripts run as `python3 -I blender/<x>.py` (bpy 5.2). `tools/hshots.js` is a quick multi-pose harness. `tools/game_shots.js` covers the in-game flow: new game → hero → Paneb greets.

## Extending to all ~26 characters and town walkers

1. **Generalise the build into recipes.** Each recipe sets base (male/female), slim factors, head scale, skin and palette, wig type (bob, long braided, bald, short cap, plus the UAL beard), clothing (kilt, long dress, priest sash with leopard skin, scribe kilt, cloak) and props.
   - The face profile and the atlas can be **shared**: the same sprite style, with per-character colours (iris, brow, lips) and optionally 2–3 eye/brow variants for identity.
   - Rect positions come from the recipe.
2. **Put the clips in one shared GLB** (same skeleton for everyone) and keep a mesh-only GLB per character, about 60–80 KB gz each. A one-cast data block of about 26 × 70 KB plus about 120 KB for the clips comes to roughly 2 MB base64, which replaces `chars33.dat`. Load each character lazily.
3. **Town walkers.** Make an LOD1 at about 1.2–1.8k tris, with no face sprites (a dot-eyes cell at most) and no ink hull beyond 10 m. Walkers share one geometry per archetype with palette swaps. Use a single mixer per crowd with clip offsets, or bake 6–8 walk/idle/carry frames into a texture (VAT) so InstancedMesh can draw them in 1 call. The 30 fps town budget makes per-walker mixers and 8k-tri meshes unrealistic past about 6 people.
4. **Estimate:**

   | Work | Time |
   |---|---|
   | Recipe tooling and shared clip pack | 1–1.5 days |
   | Female base, dress and long wig | 0.5–1 day |
   | 26 characters at about 1.5 h each, art direction and QA | 4–5 days |
   | Town LOD, instancing and integration | 2 days |
   | **Total** | **about 8–10 working days** |

## Missing or weak

- **Clips not in UAL:**
  - a real wave
  - think/chin
  - shrug
  - laugh
  - bow or obeisance (for nobles and priests)
  - sitting cross-legged (senet table)
  - steering oar or rowing (Paneb is a helmsman)
  - haggling gestures
  - pointing

  The ones I keyframed with IK are serviceable, not polished.
- UAL hands are mostly fists. Open hands are forced only in wave and shrug.
- **No Egyptian costume or hair assets exist in the pack**; everything is procedural. Sandals and props are missing: oar, scroll, basket for carry, staff.
- The kilt is a skinned shell. On big leg lifts (dance, stairs) a thigh can still graze it. A short cloth spring or a separate front panel bone would fix that.
- Face sprites are projected along +z. In profile views (more than about 60°) they stretch and fade at the cheek. That is fine for the dialogue camera (about 16–20°), but walkers in profile need the LOD face.
- In swiftshader the clips play slower because dt is clamped at 50 ms. Real phones run at 60 fps, so this is a test artefact only.

## QA (dist/preview.html built with these changes)

- `tools/qa/test-arayuz.js`, run in default (2D) mode and again with `D3=1`, printed **ALL OK** both times. The first D3=1 attempt timed out on a screenshot while three swiftshader browsers ran in parallel; it passed when rerun alone.
- `tools/qa/t153_28.js 1` (30-day bot) finished with **errs: none**.
- `node --check` on the last `<script>` of `dist/nil-kervanci.html` passes.
- Shots: the phone run (412x915 @2x) and the desktop run (1280x720) covered greet, mid-talk, a second line, happy, angry, thinking, tap/laugh and tap/wave, with 0 page errors. After the dialogue closed, the stage was disposed and 0 canvases were left.
