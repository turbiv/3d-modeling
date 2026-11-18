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
- PLA, printer.json defaults, print without supports, ≤ 3 h (expected ~25 min).
- Jacket ~314 × 314 mm; record + jacket 0.25–0.6 kg. One medium Command strip (~70 × 19 mm incl. tab, ~1 kg+ rating — check pack).

## Approaches
1. **Tall hidden back plate (picked).** 60 mm plate sits behind the jacket; one strip mounted vertically, tab down out under the ledge (Command's pull direction). Only the ledge is visible.
2. Short U-channel (25 mm plate, like the reference photo). Strip only fits sideways, tab hidden, less bonded area.
3. Wall plate + clip-on ledge. Extra part with no gain since Command already removes cleanly.

## Design (parameters, all adjustable)
- Width 76; back plate 60 tall × 3 thick; floor 3 thick; jacket gap 11 (was 9: an 8 mm jacket would touch the plate top; widened to 11 so jackets up to ~9.5 mm lean on the wall, up to 11 mm fit); front lip 3 thick × 12 tall above floor, rounded top; lip root kept sharp so the jacket seats at the lip face. Visible ledge depth 17 mm (+ strip thickness).
- Lean comes from the lip position: ~1° for an 8 mm jacket, ~2° for a 3 mm one. No angled geometry needed.
- Print on its side (L/U profile on the bed, 76 mm tall): no overhangs, layer lines can't split the lip off.

## Left to the builder
- Fillet radii (lip top, inner corners for stiffness); exact strip outline is not modeled.
