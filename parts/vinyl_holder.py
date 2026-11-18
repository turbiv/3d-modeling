"""Vinyl record wall holder: a small ledge that holds one 12" LP jacket upright.

The jacket's bottom stands in the channel, its front edge stops against the lip,
and its top leans on the wall at ~1-2°. A tall back plate hides behind the jacket
and carries one 3M Command medium strip, mounted vertically with the tab pointing
down out under the ledge.

Print orientation: side profile flat on the bed, extruded WIDTH upward (Z).
X = away from the wall (0 = wall face of the plate), Y = up the wall (0 = underside of floor).
Spec: docs/superpowers/specs/2026-11-18-vinyl-wall-holder-design.md
"""

import json
import math
from pathlib import Path

import manifold3d
import trimesh
from build123d import Axis, Mesher, Polygon, export_step, export_stl, extrude, fillet

ROOT = Path(__file__).resolve().parent.parent
PRINTER = json.loads((ROOT / "printer.json").read_text())
PART = "vinyl_holder"
OUT_DIR = ROOT / "out" / PART

# --- Parameters (mm) ---
WIDTH = 76.0  # along the wall; reference product width (7.6 cm)
BACK_T = 3.0  # back plate thickness
BACK_H = 60.0  # back plate height, hidden behind the jacket
FLOOR_T = 3.0
JACKET_GAP = 11.0  # plate-to-lip channel; jackets up to ~9.5 mm still lean on the wall
LIP_T = 3.0
LIP_H = 12.0  # lip height above the floor
LIP_FILLET = 1.4  # rounded lip top so it doesn't mark covers
TOP_FILLET = 1.4  # rounded plate top
PLATE_ROOT_FILLET = 1.0  # plate-to-floor inside corner only; the lip root stays sharp
# so the jacket's front edge seats exactly at LIP_X0 (a fillet there pushes it back ~0.5 mm)

# Record / mounting inputs
JACKET_T_MAX = 8.0  # thickest jacket, caliper-measured
JACKET_T_MIN = 3.0  # thin single LP
JACKET_H = 314.0  # 12.375" jacket
STRIP_T = 1.0  # Command medium strip thickness (assumed; verify on the pack)
STRIP_ADHESIVE_L = 50.0  # adhesive part of a medium strip (tab hangs below)
STRIP_W = 19.0
STRIP_MARGIN = 5.0

# Checks
MAX_LEAN_DEG = 3.0
MIN_PLATE_CLEARANCE = 0.5  # thickest jacket must clear the plate top by this much
MIN_LIP_H = 10.0
VOLUME_LIMIT_MM3 = 30_000.0  # keeps print well under the 3 h slot
EPS = 1e-3  # edge-selection window
DIM_TOL = 0.01  # bbox vs spec
BED_TOL = 1e-6

# --- Derived ---
LIP_X0 = BACK_T + JACKET_GAP  # inner face of the lip
LIP_X1 = LIP_X0 + LIP_T
LIP_TOP = FLOOR_T + LIP_H


def lean_deg(jacket_t: float) -> float:
    """Lean of a jacket whose bottom front edge is on the lip and top rests on the wall."""
    bottom_back_x = LIP_X0 - jacket_t + STRIP_T  # measured from the wall surface
    return math.degrees(math.atan(bottom_back_x / JACKET_H))


def plate_clearance(jacket_t: float) -> float:
    """Gap between the jacket's back face and the plate front, at the plate top."""
    rise = BACK_H - FLOOR_T
    return (LIP_X0 - jacket_t) - rise * math.tan(math.radians(lean_deg(jacket_t))) - BACK_T


def max_jacket_on_wall() -> float:
    """Thickest jacket that still clears the plate top by MIN_PLATE_CLEARANCE (bisection)."""
    lo, hi = 0.0, JACKET_GAP
    while hi - lo > EPS:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if plate_clearance(mid) >= MIN_PLATE_CLEARANCE else (lo, mid)
    return lo


def build():
    profile = Polygon(
        (0, 0),
        (LIP_X1, 0),
        (LIP_X1, LIP_TOP),
        (LIP_X0, LIP_TOP),
        (LIP_X0, FLOOR_T),
        (BACK_T, FLOOR_T),
        (BACK_T, BACK_H),
        (0, BACK_H),
        align=None,
    )
    part = extrude(profile, WIDTH)

    z_edges = part.edges().filter_by(Axis.Z)
    lip_top = z_edges.filter_by_position(Axis.Y, LIP_TOP - EPS, LIP_TOP + EPS)
    plate_top = z_edges.filter_by_position(Axis.Y, BACK_H - EPS, BACK_H + EPS)
    assert len(lip_top) == 2 and len(plate_top) == 2, "fillet edge selection"

    part = fillet(lip_top, LIP_FILLET)
    edges = part.edges().filter_by(Axis.Z).filter_by_position(Axis.Y, BACK_H - EPS, BACK_H + EPS)
    part = fillet(edges, TOP_FILLET)
    root = (
        part.edges()
        .filter_by(Axis.Z)
        .filter_by_position(Axis.Y, FLOOR_T - EPS, FLOOR_T + EPS)
        .filter_by_position(Axis.X, BACK_T - EPS, BACK_T + EPS)
    )
    assert len(root) == 1, "plate root edge selection"
    return fillet(root, PLATE_ROOT_FILLET)


def mesh_check(stl_path: Path) -> dict:
    m = trimesh.load_mesh(stl_path)
    mm = manifold3d.Manifold(
        manifold3d.Mesh(vert_properties=m.vertices.astype("float32"), tri_verts=m.faces.astype("uint32"))
    )
    return {
        "watertight": bool(m.is_watertight),
        "manifold_status": str(mm.status()),
        "manifold_ok": mm.status() == manifold3d.Error.NoError,
    }


def main():
    part = build()
    solids = list(part.solids())
    bb = part.bounding_box()
    size = (bb.size.X, bb.size.Y, bb.size.Z)
    volume = part.volume
    valid = all(s.is_valid for s in solids)
    env = PRINTER["envelope_mm"]
    min_wall = PRINTER["min_wall_mm"]

    assert len(solids) == 1, f"expected 1 solid, got {len(solids)}"
    assert valid, "invalid solid"
    expected = (LIP_X1, BACK_H, WIDTH)
    assert all(abs(a - b) < DIM_TOL for a, b in zip(size, expected)), f"bbox {size} != {expected}"
    assert all(s <= e for s, e in zip(sorted(size), sorted(env))), f"bbox {size} exceeds envelope {env}"
    assert abs(bb.min.Z) < BED_TOL, "part not on bed"
    # Pure Z extrusion = no overhangs in print orientation: every face is a cap (normal ±Z) or a wall (normal ⟂ Z).
    for f in part.faces():
        nz = abs(f.normal_at().Z)
        assert nz < BED_TOL or abs(nz - 1) < BED_TOL, f"face not cap/wall (|nz|={nz:.3f})"
    assert volume <= VOLUME_LIMIT_MM3, f"volume {volume:.0f} over {VOLUME_LIMIT_MM3}"
    assert min(BACK_T, FLOOR_T, LIP_T) >= min_wall, "wall thinner than min_wall_mm"
    assert JACKET_GAP > JACKET_T_MAX, "thickest jacket doesn't fit the channel"
    assert LIP_H >= MIN_LIP_H, "lip too low to stop the jacket sliding out"
    assert BACK_H >= STRIP_ADHESIVE_L + STRIP_MARGIN, "Command strip doesn't fit behind plate"
    assert WIDTH >= STRIP_W + 2 * STRIP_MARGIN, "plate narrower than strip"
    lean_thin, lean_thick = lean_deg(JACKET_T_MIN), lean_deg(JACKET_T_MAX)
    assert 0 < lean_thick <= lean_thin <= MAX_LEAN_DEG, f"lean {lean_thick:.2f}..{lean_thin:.2f}°"
    clear = plate_clearance(JACKET_T_MAX)
    assert clear >= MIN_PLATE_CLEARANCE, f"8 mm jacket hits plate top (clearance {clear:.2f})"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stl = OUT_DIR / f"{PART}.stl"
    export_stl(part, str(stl), ascii_format=False)
    export_step(part, str(OUT_DIR / f"{PART}.step"))
    mesher = Mesher()
    mesher.add_shape(part)
    mesher.write(str(OUT_DIR / f"{PART}.3mf"))

    mc = mesh_check(stl)
    assert mc["watertight"] and mc["manifold_ok"], f"mesh check failed: {mc}"

    print(f"part: {PART}")
    print(f"bbox_mm: {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f}")
    print(f"volume_mm3: {volume:.1f}")
    print(f"solids: {len(solids)}  valid: {valid}")
    print(f"channel_mm: {JACKET_GAP}  lip_above_floor_mm: {LIP_H}")
    print(f"lean_deg: {lean_thick:.2f} ({JACKET_T_MAX} mm jacket) .. {lean_thin:.2f} ({JACKET_T_MIN} mm jacket)")
    print(f"plate_top_clearance_mm ({JACKET_T_MAX} mm jacket): {clear:.2f}")
    print(f"max_jacket_on_wall_mm: {max_jacket_on_wall():.1f}  (fits up to {JACKET_GAP} mm)")
    print(f"mesh_check: watertight={mc['watertight']} manifold={mc['manifold_status']}")
    print(f"exported: {sorted(p.name for p in OUT_DIR.iterdir())}")


if __name__ == "__main__":
    main()
