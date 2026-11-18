"""Fit coupon: calibrates hole/peg clearance and horizontal teardrop holes for one printer.

Print flat, no supports. Contents:
- Plate with a ladder of vertical holes at PEG_D + each clearance, labelled.
- Block with one horizontal teardrop hole at PEG_D + printer hole_allowance_mm.
- One loose test peg (PEG_D), printed flange-down next to the plate.
After printing: find the tightest hole the peg slides into, update printers/<name>.json.
"""

import json
import os
from pathlib import Path

import manifold3d
import trimesh
from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Location,
    Mesher,
    Plane,
    Polygon,
    Pos,
    Rot,
    Text,
    export_step,
    export_stl,
    extrude,
    Circle,
)

ROOT = Path(__file__).resolve().parent.parent
PRINTER = json.loads((ROOT / "printer.json").read_text())
PART = "fit_coupon"
OUT_DIR = ROOT / "out" / PART

# --- Parameters (mm) ---
PEG_D = 5.0
CLEARANCES = (0.1, 0.2, 0.3, 0.4)
HOLE_PITCH = 12.0
EDGE_MARGIN = 5.0
PLATE_T = 4.0
LABEL_SIZE = 3.5
LABEL_DEPTH = 0.6
LABEL_GAP = 2.0  # hole edge to label top
TEARDROP_D = PEG_D + PRINTER["hole_allowance_mm"]
TEARDROP_ANGLE_DEG = PRINTER["max_overhang_deg"]
BLOCK_WALL = PRINTER["min_wall_mm"] * 2
BLOCK_LEN = TEARDROP_D + 2 * BLOCK_WALL
BLOCK_DEPTH = 10.0
PEG_LEN = 10.0
PEG_HEAD_D = 9.0
PEG_HEAD_T = 2.0
PEG_GAP = 4.0
VOLUME_LIMIT_MM3 = 12_000  # keeps print near 20 min at library defaults

# --- Derived layout ---
MAX_HOLE_D = PEG_D + max(CLEARANCES)
PLATE_LEN = 2 * EDGE_MARGIN + (len(CLEARANCES) - 1) * HOLE_PITCH + MAX_HOLE_D
PLATE_W = 2 * EDGE_MARGIN + MAX_HOLE_D + LABEL_GAP + LABEL_SIZE
HOLE_Y = PLATE_W - EDGE_MARGIN - MAX_HOLE_D / 2
LABEL_Y = HOLE_Y - MAX_HOLE_D / 2 - LABEL_GAP - LABEL_SIZE / 2
TEARDROP_R = TEARDROP_D / 2
TEARDROP_Z = PLATE_T + TEARDROP_R  # hole sits on top of the plate thickness
TEARDROP_APEX = TEARDROP_R / (2 ** 0.5) * 2  # apex height above centre for 45°
BLOCK_H = TEARDROP_Z + TEARDROP_APEX + PRINTER["min_wall_mm"]


def hole_x(i: int) -> float:
    return EDGE_MARGIN + MAX_HOLE_D / 2 + i * HOLE_PITCH


def teardrop_profile():
    """Circle plus a 45° roof, in the XZ plane, apex pointing +Z."""
    import math

    a = math.radians(TEARDROP_ANGLE_DEG)
    tx, tz = TEARDROP_R * math.sin(a), TEARDROP_R * math.cos(a)
    apex = TEARDROP_R / math.cos(a)
    roof = Polygon((-tx, tz), (tx, tz), (0, apex), align=None)
    return Circle(TEARDROP_R) + roof


def build():
    plate = Box(PLATE_LEN, PLATE_W, PLATE_T, align=(Align.MIN, Align.MIN, Align.MIN))
    for i, c in enumerate(CLEARANCES):
        d = PEG_D + c
        plate -= Pos(hole_x(i), HOLE_Y, 0) * Cylinder(d / 2, PLATE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        label = Text(f"{c:.1f}", font_size=LABEL_SIZE)
        plate -= Pos(hole_x(i), LABEL_Y, PLATE_T - LABEL_DEPTH) * extrude(label, LABEL_DEPTH)

    block = Pos(PLATE_LEN, 0, 0) * Box(BLOCK_LEN, BLOCK_DEPTH, BLOCK_H, align=(Align.MIN, Align.MIN, Align.MIN))
    tear = Plane.XZ * extrude(teardrop_profile(), -BLOCK_DEPTH)  # XZ normal is -Y; extrude toward +Y
    block -= Pos(PLATE_LEN + BLOCK_LEN / 2, 0, TEARDROP_Z) * tear
    body = plate + block

    peg_x = PLATE_LEN + BLOCK_LEN + PEG_GAP + PEG_HEAD_D / 2
    peg_y = PEG_HEAD_D / 2
    peg = Pos(peg_x, peg_y, 0) * (
        Cylinder(PEG_HEAD_D / 2, PEG_HEAD_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        + Pos(0, 0, PEG_HEAD_T) * Cylinder(PEG_D / 2, PEG_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    return body, peg


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
    body, peg = build()
    solids = list(body.solids()) + list(peg.solids())
    everything = body + peg
    bb = everything.bounding_box()
    size = (bb.size.X, bb.size.Y, bb.size.Z)
    volume = sum(s.volume for s in solids)
    valid = all(s.is_valid for s in solids)

    env = PRINTER["envelope_mm"]
    assert len(solids) == 2, f"expected 2 solids (coupon + peg), got {len(solids)}"
    assert valid, "invalid solid"
    assert all(s <= e for s, e in zip(size, env)), f"bbox {size} exceeds envelope {env}"
    assert volume <= VOLUME_LIMIT_MM3, f"volume {volume:.0f} mm3 over budget {VOLUME_LIMIT_MM3}"
    assert abs(bb.min.Z) < 1e-6, "part not on bed"
    assert BLOCK_H - (TEARDROP_Z + TEARDROP_APEX) >= PRINTER["min_wall_mm"] - 1e-6, "teardrop roof too thin"

    # Each ladder hole must be the right diameter: measure via circular edges on the top face.
    top_edges = body.edges().filter_by_position(Axis.Z, PLATE_T - 1e-3, PLATE_T + 1e-3)
    radii = sorted({round(e.radius, 3) for e in top_edges if e.geom_type.name == "CIRCLE"})
    expected = sorted({round((PEG_D + c) / 2, 3) for c in CLEARANCES})
    assert all(r in radii for r in expected), f"hole radii {radii} missing {expected}"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stl = OUT_DIR / f"{PART}.stl"
    export_stl(everything, str(stl), ascii_format=False)
    export_step(everything, str(OUT_DIR / f"{PART}.step"))
    mesher = Mesher()
    for s in solids:
        mesher.add_shape(s)
    mesher.write(str(OUT_DIR / f"{PART}.3mf"))

    mc = mesh_check(stl)
    assert mc["watertight"] and mc["manifold_ok"], f"mesh check failed: {mc}"

    print(f"part: {PART}")
    print(f"bbox_mm: {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f}")
    print(f"volume_mm3: {volume:.1f}")
    print(f"solids: {len(solids)}  valid: {valid}")
    print(f"hole_diameters_mm: {[round(PEG_D + c, 2) for c in CLEARANCES]}  teardrop_d_mm: {TEARDROP_D}")
    print(f"mesh_check: watertight={mc['watertight']} manifold={mc['manifold_status']}")
    print(f"exported: {sorted(p.name for p in OUT_DIR.iterdir())}")

    if os.environ.get("CAD_SHOW"):
        from ocp_vscode import show

        show(body, peg)


if __name__ == "__main__":
    main()
