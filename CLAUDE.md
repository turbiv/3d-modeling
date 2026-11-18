# 3D modeling workspace

This folder is a CAD workspace. I describe physical parts; you model them as parametric
build123d scripts, render them, look at them, and iterate with me until they're right.
I never run commands or edit files myself — you do all of it.

## How every session works (do this without being asked)

1. **Start the viewer first.** Call preview_start with name `cad-viewer` (http://localhost:3940).
   It shows in the Browser pane, where I watch the model live. If it's already running, reuse it.
2. **When I describe a part:** list the dimensions you're using and ask only about real gaps
   (functional dimensions come from my caliper numbers, not guesses). Then build a first version
   right away — don't wait for a perfect spec.
3. **Build loop, after every change:**
   - Write/edit `parts/<part>.py`. The PostToolUse hook runs it; it must export to `out/<part>/`,
     which makes the viewer reload within ~1 s.
   - Look at it yourself: screenshot the viewer (Iso, plus Top/Front/Right/Bottom/X-ray as relevant).
     The build123d MCP render tools are also available for extra views.
   - Check numbers: bounding box, volume, solid count, validity, key dimensions asserted in the script.
   - Fix anything wrong before replying. Then tell me briefly what changed and what to look at.
4. **I give feedback in plain words** ("wall looks thin", "move the hole left 5 mm"). Make targeted
   edits and repeat the loop. Expect many small iterations.
5. **When I say it's done:** confirm STL/3MF/STEP are in `out/<part>/`, commit, and push.

## CAD rules (all units mm)

Python env: `.venv` (Python 3.12, build123d, bd_warehouse, trimesh, manifold3d).
Run parts with `.venv/bin/python parts/<part>.py`. Use the b123d-modeling skill for build123d help.

- Every dimension is a named UPPER_CASE parameter at the top of the part file. No literal numbers in geometry.
- One part per file in parts/. Assemblies: one file, parts laid out in print orientation.
- Read printer.json first; use min_wall_mm, hole_allowance_mm, slide_clearance_mm, max_overhang_deg, max_bridge_mm.
- Fit inside 200 x 180 x 180 mm unless a specific printer profile is named (printers/<name>.json).
- Target sliced print time <= 3 h (library slot minus ~45 min). Larger parts: split on flat faces, join with 3 mm pins (0.2–0.3 mm clearance) or dovetails.
- Material is PLA. Print without supports: flat face on bed, overhangs <= 45°, teardrop horizontal holes, threads printed upright.
- Default wall 1.6 mm; thicker where screws bear load.
- Threads, fasteners, bearings, gears: use bd_warehouse. Read its installed docs / the build123d://bd_warehouse resource before using it.
- Apply fillets last; if the kernel refuses a radius, retry smaller.
- Report bounding box, volume, solid count, validity, and assert key dimensions against the spec. Renders confirm shape; numbers are the source of truth. `mesh_check: skipped` is not a pass.
- Make targeted edits; don't rewrite a working file.
- Every part script, when run, validates and exports binary STL (mm) + 3MF + STEP to out/<part>/<part>.*. Use coupons/fit_coupon.py as the template for structure, checks and export.
- Don't call show(); the viewer reads out/ directly.
- Commit source and outputs together.
- Never run the build123d-mcp server in HTTP mode beyond localhost (it has no auth).

## Viewer details

viewer/serve.py (stdlib, localhost only) + viewer/index.html (three.js). It follows the newest
exported part; `?part=<name>` pins one. Buttons: Iso, Top, Front, Right, Back, Bottom, Edges,
X-ray, Bed (shows the printer envelope from printer.json).
