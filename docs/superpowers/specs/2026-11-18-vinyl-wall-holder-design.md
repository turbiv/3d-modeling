# Vinyl record wall holder — short design (approved 2026-11-18)

## Intent
Display one 12" LP (in its jacket) on a rented wall. The jacket stands in a small
printed ledge and its top leans against the wall at a very slight angle. No screws:
mounted with a single 3M Command **medium** strip so it removes cleanly.

## Goals / non-goals / anti-goals
- Goal: holds jackets from a thin single LP (~3 mm) up to an 8 mm gatefold (caliper-measured thickest).
- Goal: almost invisible — only a ~15 mm deep ledge shows under the cover.
- Non-goal: holding several records; screw mounting; 7" singles.
- Anti-goal: marks on the cover, a visibly tilted record, a pull tab hidden where it can't be reached.

## Constraints
- Black PLA on the library Ultimaker S3 (printers/ultimaker_s3.json): Oodi bookings ≤ 8 h, Pasila ≤ 6 h, one at a time. 20 holders needed. **Looks are the top priority.**
- Jacket ~314 × 314 mm; record + jacket 0.25–0.6 kg. One medium Command strip (~70 × 19 mm incl. tab, ~1 kg+ rating — check pack).

## Approaches
1. **Tall hidden back plate (picked).** 60 mm plate sits behind the jacket; one strip mounted vertically, tab down out under the ledge (Command's pull direction). Only the ledge is visible.
2. Short U-channel (25 mm plate, like the reference photo). Strip only fits sideways, tab hidden, less bonded area.
3. Wall plate + clip-on ledge. Extra part with no gain since Command already removes cleanly.

## Design (parameters, all adjustable)
- Width 76; back plate 60 tall × 2 thick; floor 2 thick (2 mm walls: ~30× strength margin, half the print time of 3 mm); jacket gap 11 (was 9: an 8 mm jacket would touch the plate top; widened to 11 so jackets up to ~9.5 mm lean on the wall, up to 11 mm fit); front lip 2 thick × 12 tall above floor, rounded top; lip root kept sharp so the jacket seats at the lip face. Visible ledge depth 15 mm (+ strip thickness).
- Lean comes from the lip position: ~1° for an 8 mm jacket, ~2° for a 3 mm one. No angled geometry needed.
- Print floor down, as mounted (changed from on-its-side, for looks): glossy underside, both ends match, horizontal layer lines along the lip, no brim. Strength margin ~10–20× across layers. 0.4 mm 45° bevel on the bed edges hides first-layer squish. Cura: Z seam at the back of the plate, support off, skirt.
- Plates (parts/vinyl_holder_plates.py, one row): 0.2 mm layers — Oodi plate_6 (~7.0 h), Pasila plate_4 (~4.6 h); 0.3 mm — Oodi plate_9 (~7.2 h), Pasila plate_6 (~4.8 h); plate_2 for the test pair / leftovers.

## Left to the builder
- Fillet radii (lip top, inner corners for stiffness); exact strip outline is not modeled.
