"""Build plates of vinyl holders for the library Ultimaker S3 (one row, floor down, as printed).

Load a plate STL in Cura as-is: the layout and orientation are done.
Sliced time per holder (CuraEngine, UM S3 AA0.4 PLA, 3 walls, 15% infill, no brim):
  0.2 mm layers ~1.1 h, 0.3 mm layers ~0.75 h.
Which plate fits which booking (booking minus ~45 min margin):
  0.2 mm: Oodi 8 h -> plate_6, Pasila 6 h -> plate_4
  0.3 mm: Oodi 8 h -> plate_9, Pasila 6 h -> plate_6
  plate_2: first test pair (print one at 0.2 and compare) or the leftovers.
Chosen: 0.2 mm. For 20 holders: plate_2 (test) + plate_6 x 3 at Oodi. Print card: out/vinyl_holder_plates/PRINT.md
"""

import json
import sys
from pathlib import Path

from build123d import Compound, Mesher, Pos, export_step, export_stl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vinyl_holder import mesh_check, build  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PRINTER = json.loads((ROOT / "printers" / "ultimaker_s3.json").read_text())
PART = "vinyl_holder_plates"
OUT_DIR = ROOT / "out" / PART

# --- Parameters (mm) ---
PLATE_COUNTS = (2, 4, 6, 9)
VIEWER_PLATE = 9  # also written as vinyl_holder_plates.stl for the viewer
GAP = 8.0  # between holders; no brim, so this is just travel/cooling room
BED_TOL = 1e-6


def plate(n: int) -> Compound:
    one = build()
    pitch = one.bounding_box().size.X + GAP
    return Compound([Pos(i * pitch, 0, 0) * one for i in range(n)])


def export(shape: Compound, stem: str) -> Path:
    stl = OUT_DIR / f"{stem}.stl"
    export_stl(shape, str(stl), ascii_format=False)
    export_step(shape, str(OUT_DIR / f"{stem}.step"))
    mesher = Mesher()
    for s in shape.solids():
        mesher.add_shape(s)
    mesher.write(str(OUT_DIR / f"{stem}.3mf"))
    return stl


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    env = PRINTER["envelope_mm"]
    for n in PLATE_COUNTS:
        p = plate(n)
        solids = list(p.solids())
        bb = p.bounding_box()
        size = (bb.size.X, bb.size.Y, bb.size.Z)
        assert len(solids) == n, f"plate_{n}: {len(solids)} solids"
        assert all(s.is_valid for s in solids), f"plate_{n}: invalid solid"
        assert all(s <= e for s, e in zip(size, env)), f"plate_{n}: {size} exceeds {env}"
        assert abs(bb.min.Z) < BED_TOL, f"plate_{n}: not on bed"
        stl = export(p, f"plate_{n}")
        mc = mesh_check(stl)
        assert mc["watertight"] and mc["manifold_ok"], f"plate_{n}: mesh check failed {mc}"
        print(
            f"plate_{n}: bbox {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm, "
            f"volume {sum(s.volume for s in solids):.0f} mm3, solids {n}, valid True, "
            f"mesh watertight={mc['watertight']} manifold={mc['manifold_status']}"
        )
        if n == VIEWER_PLATE:
            export(p, PART)
    print(f"exported: {sorted(p.name for p in OUT_DIR.iterdir())}")


if __name__ == "__main__":
    main()
