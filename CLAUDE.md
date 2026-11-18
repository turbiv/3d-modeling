# CAD rules (all units mm)

Project root: this folder. Python env: `.venv` (Python 3.12, build123d, bd_warehouse, trimesh, manifold3d, ocp_vscode).
Run parts with `.venv/bin/python parts/<part>.py`.

- Every dimension is a named UPPER_CASE parameter at the top of the part file. No literal numbers in geometry.
- One part per file in parts/. Assemblies: one file, parts laid out in print orientation.
- Read printer.json first; use min_wall_mm, hole_allowance_mm, slide_clearance_mm, max_overhang_deg, max_bridge_mm.
- Fit inside 200 x 180 x 180 mm unless a specific printer profile is named (printers/<name>.json).
- Target sliced print time <= 3 h (library slot minus ~45 min). Larger parts: split on flat faces, join with 3 mm pins (0.2–0.3 mm clearance) or dovetails.
- Material is PLA. Print without supports: flat face on bed, overhangs <= 45°, teardrop horizontal holes, threads printed upright.
- Default wall 1.6 mm; thicker where screws bear load.
- Threads, fasteners, bearings, gears: use bd_warehouse. Read its installed docs / the build123d://bd_warehouse resource before using it.
- Apply fillets last; if the kernel refuses a radius, retry smaller.
- Before modeling from a drawing or photo, list every dimension you read and ask me to confirm gaps. Functional dimensions come from my caliper measurements, not from images.
- After every change, report bounding box, volume, solid count, validity, and assert key dimensions against the spec. Use renders only to confirm topology. `mesh_check: skipped` is not a pass.
- Make targeted edits; don't rewrite a working file.
- Export binary STL (mm) + 3MF + STEP to out/<part>/. Commit source and outputs together.
- Don't call show(); the live viewer reads out/ directly.

## Viewer (shared between me and Claude)
- At the start of any modeling session, start the viewer with the Browser pane: preview_start name `cad-viewer` (http://localhost:3940). It is a local three.js page (viewer/) served by viewer/serve.py.
- It shows the newest out/<part>/<part>.stl and reloads within ~1 s of a rebuild. `?part=<name>` pins a part.
- Every part script exports when run, and the PostToolUse hook runs it after each edit, so an edit updates the viewer automatically.
- After each change, look at it yourself: screenshot the viewer (Iso plus whichever of Top/Front/Right/Bottom shows the change; X-ray for internal features) and check the shape matches the intent before reporting back. Numbers from the build report remain the source of truth.
- I give feedback by looking at the same pane; don't ask me to run anything.
- Never run the build123d-mcp server in HTTP mode beyond localhost (it has no auth).
