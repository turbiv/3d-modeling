"""Display model styled after an Abloy PROTEC2 CLIQ electronic key. Unbranded, decorative cuts.

Not cut to any real lock: the code below is invented and the cut geometry is only
evocative. No logos or markings.

Design spec (from research of Abloy product photos and brochures, 2026-11-18; no
official dimensions are published, sizes are scaled from photos using a 6.6 mm blade):
- Head: shield outline 46.75 long x ~29.8 wide. Pointed-round top arch (apex ~R11,
  ~40 deg straight flanks), sharp-ish shoulders (R1.2), convex sides, shallow chevron
  at the neck. Holds a CR2450 coin cell in the real key, hence the size.
- Head build-up: black frame (side walls FRAME_T) with a raised battery cover inside a
  RIM_W rim. Cover has a centred roof ridge (RIDGE_Z) with flat facets falling
  FACET_DEG to each side, steeper triangular facets dropping into the key-ring window,
  and bevels down to the frame at its V-shaped neck and window edges; the frame band
  below the cover tapers over FRAME_TAPER_L to NECK_Z at the neck.
- Key-ring loop: LOOP_BAND arch band around a flat crescent window; the window's lower
  edge is the cover's top edge, an inverted V of WINDOW_V_DEG.
- Side walls: fine seam groove; small triangular LED window on both sides.
- Metal: concave flare from FLARE_W to the blade over FLARE_L, entering a socket in the
  head. Blade: flat PROTEC2-style bar BLADE_W x BLADE_T with two opposite long corners
  bevelled; 11 positions with wedge cuts in 15 deg steps at two depths, 7th position
  and tip uncut; centre groove with V-grooves and a small ball on the face.

Print orientation: bottom face of head and blade flat on the bed, no supports. Blade
cuts at the bed corner leave short ceilings that bridge only CUT_W; the seam groove
ceiling bridges SEAM_D; the LED recess points up (60 deg faces).
X = along the blade (0 = blade shoulder at the end of the flare, + toward the tip),
Y = across, Z = up.
"""

import json
import math
from pathlib import Path

import manifold3d
import trimesh
from build123d import (
    Align,
    Axis,
    Box,
    Line,
    Mesher,
    Plane,
    Polygon,
    Pos,
    Rot,
    Sphere,
    Spline,
    ThreePointArc,
    Vector,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
    make_face,
    offset,
)

ROOT = Path(__file__).resolve().parent.parent
PRINTER = json.loads((ROOT / "printer.json").read_text())
PART = "abloy_key"
OUT_DIR = ROOT / "out" / PART

# --- Parameters (mm) ---
# Blade: flat bar, two opposite long corners bevelled (+Y top, -Y bottom)
BLADE_W = 6.6
BLADE_T = 2.9
BLADE_L = 32.5  # shoulder (end of flare) to tip
BEVEL = 1.0  # 45 deg bevel leg (45 keeps the bed-side bevel printable)
CODE = (3, 5, 1, 6, 2, 4, 0, 5, 2, 3, 0)  # shoulder -> tip; 0 = uncut (7th and tip always uncut)
DEPTH_CODE = (0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0)  # 0 shallow, 1 deep ("two radii" look)
CUT_DEPTHS = (0.45, 0.85)  # how far the cut plane sits below the bevel face
CUT_STEP_DEG = 15.0
CUT_BASE_DEG = 45.0 - 3.5 * CUT_STEP_DEG  # code 1..6 -> face normals 7.5 .. 82.5 deg from +Y
CUT_PITCH = 2.6  # display spacing (real ~1.5, opened up so the cuts read)
CUT_W = 1.6
SHOULDER_GAP = 2.0  # uncut blade between the shoulder and the first cut slot
CUT_ZONE_Y = 0.8  # cuts stay in the corner: |y| beyond this ...
CUT_ZONE_Z = -0.6  # ... and beyond this from the mid-plane (toward the cut corner)
TIP_CHAMFER = 0.6  # lead-in on the tip top edge
TIP_CORNER_R = 0.8  # rounded vertical tip corners
GROOVE_W = 0.5  # centre groove on the blade face
GROOVE_D = 0.3
GROOVE_TIP_MARGIN = 3.0  # groove stops short of the tip
GROOVE_V_HALF = 1.4  # V-grooves fan from the ball to this half width at the shoulder
BALL_D = 1.6  # floating-ball dome on the face
BALL_PROUD = 0.5

# Flare between head and blade
FLARE_L = 6.3
FLARE_W = 10.2  # at the head
FLARE_SAG = 0.5  # concave arc sag below the straight line
FLARE_EMBED = 2.0  # runs into the head socket

# Head outline: (distance from the neck point u, half width w)
HEAD_SIDE = ((1.8, 6.0), (4.0, 7.5), (10.0, 10.3), (15.0, 12.1), (21.0, 13.5), (27.0, 14.3), (33.0, 14.8), (38.3, 14.9))
HEAD_FLANK_END = (43.5, 8.7)  # straight ~40 deg flank from the shoulder to here, then the apex arc
HEAD_L = 46.75  # neck point to arch apex
SHOULDER_R = 1.2
NECK_CORNER_R = 1.0

# Head build-up
FRAME_T = 7.5  # side-wall height
RIDGE_Z = 10.5  # cover ridge height (overall thickness)
FACET_DEG = 10.0  # cover facets fall away from the centre ridge
RIM_W = 1.3  # frame rim visible around the cover
FRAME_TOP_FILLET = 0.8
BED_CHAMFER = 0.4
LOOP_BAND = 2.8  # key-ring arch band
WINDOW_BASE_U = 40.0  # window lower edge on the centreline (from the neck point)
WINDOW_V_DEG = 9.0  # inverted-V lower edge
WINDOW_CORNER_R = 0.8
APEX_FACET_L = 5.0  # triangular facets dropping into the window start this far before it
COVER_NECK_U = 8.0  # cover's lower edge: V pointing at the blade, tip this far from the neck point
COVER_NECK_V_DEG = 17.0
NECK_FACET_L = 4.0  # bevel on the cover's lower V edge, down to the frame top
FRAME_TAPER_L = 6.0  # frame band below the cover tapers over this length ...
NECK_Z = 5.0  # ... down to this height at the neck point
SEAM_Z_FRAC = 0.4  # side-wall seam groove height (fraction of FRAME_T)
SEAM_W = 0.6
SEAM_D = 0.4
LED_U = 18.5  # LED window position from the neck
LED_SIDE = 2.5  # triangle side
LED_DEPTH = 0.5
LED_Z_FRAC = 0.65  # LED centre height (fraction of FRAME_T)

CUTTER_BIG = 200.0  # half-space cutter size

# Checks
VOLUME_LIMIT_MM3 = 14_000.0  # ~1-1.5 h at 0.2 mm
SECTION_PROBE = 0.4  # slab thickness for blade section checks
MIN_CUT_AREA = 0.25  # each cut must remove at least this much section (mm2)
AREA_TOL = 0.02  # uncut positions match the blank blade (mm2)
DIM_TOL = 0.01
SPLINE_TOL = 0.5  # spline outline may bulge slightly past its control points
BED_TOL = 1e-6

# --- Derived ---
N_POS = len(CODE)
HEAD_X0 = -FLARE_L  # neck point
HEAD_HALF_W = max(w for _, w in HEAD_SIDE)


def P(u: float, w: float) -> tuple[float, float]:
    """Head coordinates (from the neck point, across) -> XY."""
    return (HEAD_X0 - u, w)


def cut_x(i: int) -> float:
    return SHOULDER_GAP + CUT_W / 2 + i * CUT_PITCH


BALL_X = cut_x(3) + CUT_PITCH / 2  # on a land, ~35 % along the blade


def cut_above(origin, normal):
    """Big box filling the half-space above the plane (origin, normal)."""
    n = Vector(*normal).normalized()
    x_dir = Vector(0, 0, 1).cross(n)
    x_dir = x_dir if x_dir.length > DIM_TOL else Vector(1, 0, 0)
    plane = Plane(origin=origin, x_dir=x_dir.normalized(), z_dir=n)
    return plane * Box(CUTTER_BIG, CUTTER_BIG, CUTTER_BIG, align=(Align.CENTER, Align.CENTER, Align.MIN))


# ---------------- blade ----------------
def corner_cut(i: int, side: int):
    """Wedge cut at position i in the bevelled corner; side +1 = top/+Y, -1 = bottom/-Y."""
    a = math.radians(CUT_BASE_DEG + CODE[i] * CUT_STEP_DEG)
    hw, ht = BLADE_W / 2, BLADE_T / 2
    n45 = Vector(0, 1, 1).normalized()
    q = Vector(0, hw - BEVEL / 2, ht - BEVEL / 2) - n45 * CUT_DEPTHS[DEPTH_CODE[i]]  # rel. to the axis
    origin = Vector(cut_x(i), side * q.Y, ht + side * q.Z)
    half = cut_above(origin, (0, side * math.cos(a), side * math.sin(a)))
    zone_y0, zone_z0 = side * CUT_ZONE_Y, ht + side * CUT_ZONE_Z
    zone = Pos(cut_x(i), zone_y0, zone_z0) * Box(
        CUT_W,
        BLADE_W,
        BLADE_T,
        align=(Align.CENTER, Align.MIN if side > 0 else Align.MAX, Align.MIN if side > 0 else Align.MAX),
    )
    return half & zone


def groove_strip(p0, p1):
    """Groove of GROOVE_W x GROOVE_D along the blade top face from p0 to p1 (XY)."""
    d = (Vector(*p1, 0) - Vector(*p0, 0)).normalized()
    n = Vector(-d.Y, d.X, 0) * (GROOVE_W / 2)
    a, b = Vector(*p0, 0), Vector(*p1, 0)
    pts = [(v.X, v.Y) for v in (a + n, b + n, b - n, a - n)]
    return Pos(0, 0, BLADE_T - GROOVE_D) * extrude(Polygon(*pts, align=None), GROOVE_D)


def blade(with_cuts: bool = True):
    x0 = HEAD_X0  # bar starts under the flare (no coincident faces at the shoulder)
    bar = Pos(x0, -BLADE_W / 2, 0) * Box(BLADE_L - x0, BLADE_W, BLADE_T, align=(Align.MIN, Align.MIN, Align.MIN))
    long_x = bar.edges().filter_by(Axis.X)
    top_y = long_x.filter_by_position(Axis.Y, BLADE_W / 2 - DIM_TOL, BLADE_W / 2 + DIM_TOL).filter_by_position(
        Axis.Z, BLADE_T - DIM_TOL, BLADE_T + DIM_TOL
    )
    bot_y = long_x.filter_by_position(Axis.Y, -BLADE_W / 2 - DIM_TOL, -BLADE_W / 2 + DIM_TOL).filter_by_position(
        Axis.Z, -DIM_TOL, DIM_TOL
    )
    bar = chamfer(top_y + bot_y, BEVEL)

    tip = bar.edges().filter_by_position(Axis.X, BLADE_L - DIM_TOL, BLADE_L + DIM_TOL)
    bar = chamfer(tip.filter_by(Axis.Y).filter_by_position(Axis.Z, BLADE_T - DIM_TOL, BLADE_T + DIM_TOL), TIP_CHAMFER)
    tip_vertical = bar.edges().filter_by(Axis.Z).filter_by_position(Axis.X, BLADE_L - TIP_CHAMFER - DIM_TOL, BLADE_L + DIM_TOL)
    bar = fillet(tip_vertical, TIP_CORNER_R)

    bar -= groove_strip((BALL_X, 0), (BLADE_L - GROOVE_TIP_MARGIN, 0))
    bar -= groove_strip((BALL_X, 0), (0, GROOVE_V_HALF))
    bar -= groove_strip((BALL_X, 0), (0, -GROOVE_V_HALF))
    # Sphere poles turned sideways: a pole on the groove line gives a non-watertight mesh.
    bar += Pos(BALL_X, 0, BLADE_T + BALL_PROUD - BALL_D / 2) * Rot(90, 0, 0) * Sphere(BALL_D / 2)

    if with_cuts:
        for i in range(N_POS):
            if CODE[i]:
                bar -= corner_cut(i, +1)
                bar -= corner_cut(i, -1)
    return bar


def flare():
    hw0, hw1 = BLADE_W / 2, FLARE_W / 2
    mid = (-FLARE_L / 2, (hw0 + hw1) / 2 - FLARE_SAG)
    x_end = HEAD_X0 - FLARE_EMBED
    edges = [
        Line((0, -hw0), (0, hw0)),
        ThreePointArc((0, hw0), mid, (HEAD_X0, hw1)),
        Line((HEAD_X0, hw1), (x_end, hw1)),
        Line((x_end, hw1), (x_end, -hw1)),
        Line((x_end, -hw1), (HEAD_X0, -hw1)),
        ThreePointArc((HEAD_X0, -hw1), (mid[0], -mid[1]), (0, -hw0)),
    ]
    return extrude(make_face(edges), BLADE_T)


# ---------------- head ----------------
def head_outline():
    side = [P(u, w) for u, w in HEAD_SIDE]
    side_m = [P(u, -w) for u, w in reversed(HEAD_SIDE)]
    fu, fw = HEAD_FLANK_END
    face = make_face(
        [
            Line(P(0, 0), side[0]),
            Spline(*side),
            Line(side[-1], P(fu, fw)),
            ThreePointArc(P(fu, fw), P(HEAD_L, 0), P(fu, -fw)),
            Line(P(fu, -fw), side_m[0]),
            Spline(*side_m),
            Line(side_m[-1], P(0, 0)),
        ]
    )
    shoulder_w, neck_w = HEAD_SIDE[-1][1], HEAD_SIDE[0][1]
    face = fillet(face.vertices().filter_by(lambda v: abs(abs(v.Y) - shoulder_w) < DIM_TOL), SHOULDER_R)
    face = fillet(face.vertices().filter_by(lambda v: abs(abs(v.Y) - neck_w) < DIM_TOL), NECK_CORNER_R)
    return face


def loop_side():
    """Region beyond the window's inverted-V lower edge (toward the arch)."""
    t = math.tan(math.radians(WINDOW_V_DEG))
    span = 2 * HEAD_HALF_W
    far = HEAD_L + span
    return Polygon(
        P(WINDOW_BASE_U, 0),
        P(WINDOW_BASE_U - span * t, span),
        P(far, span),
        P(far, -span),
        P(WINDOW_BASE_U - span * t, -span),
        align=None,
    )


def neck_side():
    """Region below the cover's V-shaped lower edge (toward the neck)."""
    t = math.tan(math.radians(COVER_NECK_V_DEG))
    span = 2 * HEAD_HALF_W
    return Polygon(
        P(COVER_NECK_U, 0),
        P(COVER_NECK_U + span * t, span),
        P(-span, span),
        P(-span, -span),
        P(COVER_NECK_U + span * t, -span),
        align=None,
    )


def neck_taper():
    a = math.atan2(FRAME_T - NECK_Z, FRAME_TAPER_L)
    return cut_above(Vector(*P(FRAME_TAPER_L, 0), FRAME_T), (math.sin(a), 0, math.cos(a)))


def chevron_bevels(base_u: float, v_deg: float, run: float, toward_neck: bool):
    """Two planes bevelling the cover down to FRAME_T along a V edge.

    The V tip sits on the centreline at base_u; each half gets a plane parallel to it,
    starting `run` inside the cover at RIDGE_Z and reaching FRAME_T at the edge."""
    t = math.tan(math.radians(v_deg))
    a = math.atan2(RIDGE_Z - FRAME_T, run)
    cutters = None
    for s in (+1, -1):
        # horizontal normal to this half of the V, pointing out of the cover
        n_h = Vector(1, s * t, 0) if toward_neck else Vector(-1, s * t, 0)
        n_h = n_h.normalized()
        origin = Vector(*P(base_u, 0), RIDGE_Z) - n_h * run
        c = cut_above(origin, n_h * math.sin(a) + Vector(0, 0, math.cos(a)))
        cutters = c if cutters is None else cutters + c
    return cutters


def head():
    outline = head_outline()

    # Frame: full outline to FRAME_T, tapered at the neck, rounded outer top edge.
    frame = extrude(outline, FRAME_T) - neck_taper()
    tops = [f for f in frame.faces() if f.normal_at().Z > DIM_TOL]
    crease = [e for e in tops[0].edges() if any(e.is_same(o) for t in tops[1:] for o in t.edges())]
    rim_edges = [e for f in tops for e in f.edges() if not any(e.is_same(c) for c in crease)]
    frame = fillet(rim_edges, FRAME_TOP_FILLET)

    # Cover: inside the rim, between the neck V and the window V; roof ridge + facets,
    # bevelled down to the frame at both V edges.
    cover = extrude(offset(outline, -RIM_W) - loop_side() - neck_side(), RIDGE_Z)
    f = math.radians(FACET_DEG)
    for s in (+1, -1):
        cover -= cut_above((0, 0, RIDGE_Z), (0, s * math.sin(f), math.cos(f)))
    cover -= chevron_bevels(WINDOW_BASE_U, WINDOW_V_DEG, APEX_FACET_L, toward_neck=False)
    cover -= chevron_bevels(COVER_NECK_U, COVER_NECK_V_DEG, NECK_FACET_L, toward_neck=True)

    body = frame + cover

    # Key-ring window through everything.
    window = offset(outline, -LOOP_BAND) & loop_side()
    window = fillet(window.vertices().filter_by(lambda v: abs(v.Y) > DIM_TOL), WINDOW_CORNER_R)
    body -= extrude(window, RIDGE_Z)

    # Side-wall seam and LED windows.
    seam = offset(outline, SEAM_D * 2) - offset(outline, -SEAM_D)
    body -= Pos(0, 0, SEAM_Z_FRAC * FRAME_T) * extrude(seam, SEAM_W)
    body -= led_windows(body)

    return chamfer(body.edges().group_by(Axis.Z)[0], BED_CHAMFER)


def led_windows(body):
    x = P(LED_U, 0)[0]
    z = LED_Z_FRAC * FRAME_T
    probe = Pos(x, 0, z) * Box(DIM_TOL * 10, 2 * CUTTER_BIG, DIM_TOL * 10)
    wall_y = (body & probe).bounding_box().max.Y  # side wall at the LED station
    h = LED_SIDE * math.sqrt(3) / 2
    cutters = None
    for s in (+1, -1):
        plane = Plane(origin=(x, s * (wall_y - LED_DEPTH), z), x_dir=(1, 0, 0), z_dir=(0, s, 0))
        # plane local y is global -s*Z; apex must point up
        tri = Polygon((-LED_SIDE / 2, s * h / 3), (LED_SIDE / 2, s * h / 3), (0, -s * 2 * h / 3), align=None)
        c = extrude(plane * tri, LED_DEPTH * 4)
        cutters = c if cutters is None else cutters + c
    return cutters


def build():
    return head() + flare() + blade()


# ---------------- checks / export ----------------
def section_area(shape, x: float) -> float:
    slab = Pos(x, 0, 0) * Box(SECTION_PROBE, 2 * BLADE_W, 2 * BLADE_T + BALL_D)
    return (shape & slab).volume / SECTION_PROBE


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
    key = build()
    solids = list(key.solids())
    bb = key.bounding_box()
    size = (bb.size.X, bb.size.Y, bb.size.Z)
    volume = sum(s.volume for s in solids)
    valid = all(s.is_valid for s in solids)

    env = PRINTER["envelope_mm"]
    assert len(solids) == 1, f"expected 1 solid, got {len(solids)}"
    assert valid, "invalid solid"
    assert all(s <= e for s, e in zip(size, env)), f"bbox {size} exceeds envelope {env}"
    assert volume <= VOLUME_LIMIT_MM3, f"volume {volume:.0f} mm3 over budget {VOLUME_LIMIT_MM3}"
    assert abs(bb.min.Z) < BED_TOL, "part not on bed"
    assert abs(bb.max.X - BLADE_L) < DIM_TOL, f"tip at {bb.max.X:.2f}, expected {BLADE_L:.2f}"
    assert abs(size[2] - RIDGE_Z) < DIM_TOL, f"height {size[2]:.2f}, expected {RIDGE_Z}"
    assert abs(bb.min.X - P(HEAD_L, 0)[0]) < SPLINE_TOL, f"head apex at {bb.min.X:.2f}, expected {P(HEAD_L, 0)[0]:.2f}"
    assert abs(size[1] / 2 - HEAD_HALF_W) < SPLINE_TOL, f"width {size[1]:.2f}, expected ~{2 * HEAD_HALF_W}"
    assert LOOP_BAND >= PRINTER["min_wall_mm"], "ring arch band too thin"
    assert RIM_W > FRAME_TOP_FILLET, "rim fillet would run into the cover"
    assert FLARE_W > BLADE_W, "flare must widen toward the head"
    assert CODE[6] == 0 and CODE[-1] == 0, "7th position and tip must stay uncut"
    assert CUT_PITCH - CUT_W >= PRINTER["nozzle_mm"], "lands between cuts thinner than one line"
    assert CUT_W <= PRINTER["max_bridge_mm"], "cut ceiling bridge too long"

    # Blade sections: uncut positions match a blank blade, cut positions remove material.
    blank = blade(with_cuts=False)
    removed = []
    for i in range(N_POS):
        got, full = section_area(key, cut_x(i)), section_area(blank, cut_x(i))
        if CODE[i]:
            assert full - got >= MIN_CUT_AREA, f"pos {i}: cut removes only {full - got:.2f} mm2"
        else:
            assert abs(full - got) <= AREA_TOL, f"pos {i}: uncut position differs by {full - got:.2f} mm2"
        removed.append(round(full - got, 2))
    land = cut_x(0) + CUT_PITCH / 2
    assert abs(section_area(key, land) - section_area(blank, land)) <= AREA_TOL, "cut spills onto a land"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stl = OUT_DIR / f"{PART}.stl"
    export_stl(key, str(stl), ascii_format=False)
    export_step(key, str(OUT_DIR / f"{PART}.step"))
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
    print(f"cut_angles_deg: {[CUT_BASE_DEG + c * CUT_STEP_DEG if c else 0 for c in CODE]}")
    print(f"section_removed_mm2: {removed}")
    print(f"mesh_check: watertight={mc['watertight']} manifold={mc['manifold_status']}")
    print(f"exported: {sorted(p.name for p in OUT_DIR.iterdir())}")


if __name__ == "__main__":
    main()
