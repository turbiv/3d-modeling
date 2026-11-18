# Vinyl Wall Holder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One printable part, `parts/vinyl_holder.py`, that builds, self-checks and exports the LP wall ledge.

**Architecture:** One build123d script in the style of `coupons/fit_coupon.py`: UPPER_CASE parameters, `build()`, in-script asserts as the test, STL/3MF/STEP export to `out/vinyl_holder/`, mesh check, printed build report.

**Tech Stack:** build123d, trimesh, manifold3d (`.venv`).

**Spec:** `docs/superpowers/specs/2026-11-18-vinyl-wall-holder-design.md`

## Global Constraints
- All units mm; every dimension a named UPPER_CASE parameter; no literal numbers in geometry.
- Read `printer.json`; walls ≥ `min_wall_mm` (1.6); fit 200 × 180 × 180; print ≤ 3 h; no supports, overhangs ≤ 45°.
- Fillets applied last; if the kernel refuses a radius, retry smaller.
- Export binary STL + 3MF + STEP to `out/vinyl_holder/`; don't call show().
- Report bbox, volume, solid count, validity; `mesh_check: skipped` is not a pass.

## Review Focus
1. Thickest jacket (8 mm) touching the top of the back plate instead of the wall → assert clearance at plate top ≥ 0.
2. Lean too steep for a thin (3 mm) single LP → assert lean ≤ 3°.
3. Lip too low to stop the jacket sliding out → assert lip height above floor ≥ 10.
4. Strip not fitting behind the plate → assert plate ≥ strip adhesive length + margin and ≥ strip width.
5. Part not printable as oriented (not on bed, overhang) → assert min Z = 0 and profile is a pure extrusion along Z.

---

### Task 1: `parts/vinyl_holder.py`

**Files:** Create `parts/vinyl_holder.py`. Output `out/vinyl_holder/vinyl_holder.{stl,3mf,step}`.

**Interfaces:** Produces `build() -> Part` and `main()`; viewer picks up the newest STL.

**Parameters (from spec + caliper):**
`WIDTH=76, BACK_T=3, BACK_H=60, FLOOR_T=3, JACKET_GAP=10, LIP_T=3, LIP_H=12, LIP_FILLET=1.4, TOP_FILLET=1.4, INNER_FILLET=1.0,`
`JACKET_T_MAX=8 (caliper), JACKET_T_MIN=3, JACKET_H=314, STRIP_T=1.0 (assumed, Command medium), STRIP_ADHESIVE_L=50, STRIP_W=19, STRIP_MARGIN=5, MAX_LEAN_DEG=3`.
Note: JACKET_GAP is 10, not the 9 in the spec — at 9 an 8 mm jacket's back meets the plate top (Review Focus 1).

**Geometry (print orientation):** profile in XY (X = away from wall, 0 = wall face of plate; Y = up the wall, 0 = underside of floor), extruded +Z by WIDTH.
Back plate X 0..BACK_T, Y 0..BACK_H. Floor X 0..BACK_T+JACKET_GAP+LIP_T, Y 0..FLOOR_T. Lip X BACK_T+JACKET_GAP..+LIP_T, Y 0..FLOOR_T+LIP_H.
Fillets last: LIP_FILLET on the lip's top edges, TOP_FILLET on the plate's top edges, INNER_FILLET on the two inside floor corners.

- [ ] **Step 1: Write asserts in `main()`** (these are the test):
  - 1 solid, valid; bbox == (BACK_T+JACKET_GAP+LIP_T, BACK_H, WIDTH) ±0.01; within envelope; min Z == 0.
  - `lean(t) = degrees(atan((BACK_T+JACKET_GAP - t + STRIP_T) / JACKET_H))`; assert `lean(JACKET_T_MIN) <= MAX_LEAN_DEG` and `lean(JACKET_T_MAX) > 0`.
  - Plate-top clearance for thickest jacket: `(BACK_T+JACKET_GAP-JACKET_T_MAX) - BACK_H*tan(lean) - BACK_T >= 0`.
  - `LIP_H >= 10`; `BACK_H >= STRIP_ADHESIVE_L + STRIP_MARGIN`; `WIDTH >= STRIP_W`; all wall params ≥ min_wall_mm.
  - mesh check watertight + manifold.
- [ ] **Step 2: Implement `build()`** per Geometry; report prints bbox, volume, solids, valid, lean angles, plate-top clearance, mesh check.
- [ ] **Step 3: Run** `.venv/bin/python parts/vinyl_holder.py` → all asserts pass, report printed, three files in `out/vinyl_holder/`.

### Task 2: Visual check and commit
- [ ] **Step 1:** preview_start `cad-viewer`, open `?part=vinyl_holder`; screenshot Iso + Front (profile). Expect the plate-floor-lip U profile with rounded tops.
- [ ] **Step 2:** Commit spec, plan, `parts/vinyl_holder.py` and `out/vinyl_holder/` together.
