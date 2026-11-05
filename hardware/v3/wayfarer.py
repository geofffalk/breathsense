"""
Soft-wayfarer front outline for v3 (user, 4 Nov 2026: the first concept looked blocky; style chosen:
soft wayfarer). One 2D outline in the front view (y, z), extruded along x and rounded:
- a brow that is thicker on top and lifts toward the outer corners (the LED slot runs straight
  under it over the outer half of each lens);
- rims an even RIM round the sides and bottom of the wayfarer lens (g.LENS_SHAPE);
- a low bridge under a continuous brow (keyhole);
- endpieces that sweep out to the hinge line and taper diagonally back into the lower rim.
Concave corners are rounded by closing (offset out, then in), convex corners by opening (in, then
out). Front (bed) edges get a 45-degree chamfer, back edges a fillet: the front prints face down.

Frame: world, as glasses_v3 (x forward, y to the wearer's left, z up; temples' top edge at z = 0).
"""

import math

from build123d import Axis, Cylinder, Edge, Face, Plane, Pos, Solid, Sphere, Vector, Wire, chamfer, extrude, fillet
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

import glasses_v3 as g

BROW_TOP_IN = 2.2        # Brow's top at the bridge (z)
BROW_TOP_OUT = 4.6       # ... and at the outer corner: the wayfarer lift
BROW_LIFT_Y = (10.0, 70.0)   # Lift runs between these y (smoothstep): over the LED run the brow stands >= 0.8
                             # above the slot (asserted in front_pieces)
BRIDGE_LOW = -6.5        # Bridge's underside at the middle: the nose arch's top, just under the lens tops (user, 5 Nov 2026:
                         # -8 with the closing filling the whole gap between the rims put the bridge far too low)
NOSE_R = 5.5             # Nose arch's top corners
BLEND = 1.5              # Rounds where the nose arch meets the rims
BROW_LOW = g.LENS_TOP_Z + 1.0        # Brow's underside over the lenses (inside the rim)
RIM = 3.4                # Rim beyond the lens apex: wayfarer-thick (the groove still uses g.RIM_W's geometry)
END_Y = g.HALF_WIDTH + g.TEMPLE_T    # Endpiece's outer face: the temple's outer face (80.5)
END_LOW = g.END_Z0       # Endpiece's lower outer corner (z), level with the hinge's bottom knuckle
WING_TO = (g.LENS_YC + 0.44 * g.LENS_A, g.LENS_TOP_Z - 0.55 * g.LENS_B)   # Where the endpiece sweeps back into the outer rim
ROUND_IN = 9.0           # Concave corners (brow into rim, endpiece sweep, keyhole)
ROUND_OUT = 2.0          # Convex corners
CHAMFER_FRONT = 0.9      # 45 deg on the bed edge
FILLET_BACK = 1.2        # Back (eye-side) edges (1.6 fails in OCC on the spline)


def _smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def brow_top(y):
    y = abs(y)
    return BROW_TOP_IN + (BROW_TOP_OUT - BROW_TOP_IN) * _smooth((y - BROW_LIFT_Y[0]) / (BROW_LIFT_Y[1] - BROW_LIFT_Y[0]))


def _half(sign):
    """One side's raw outline pieces (overlapping), as a shapely polygon in (y, z)."""
    rim = Polygon(g.lens_outline(sign, g.GROOVE_CLEAR + RIM))
    n = 32
    ys = [-1.0 + (END_Y + 1.0) * i / n for i in range(n + 1)]
    top = [(sign * y, brow_top(y)) for y in ys]
    bottom = [(sign * y, BROW_LOW) for y in reversed(ys)]
    brow = Polygon(top + bottom)
    y_in = g.LENS_YC + g.LENS_A / 2 - 4.0
    wing = Polygon([(sign * y_in, brow_top(y_in) - 1), (sign * END_Y, brow_top(END_Y) - 1), (sign * END_Y, END_LOW),
                    (sign * WING_TO[0], WING_TO[1]), (sign * y_in, WING_TO[1])])
    return unary_union([rim, brow, wing])


def nose():
    """The opening for the nose: everything between the two rims below BRIDGE_LOW, its top corners rounded.
    Cut after the rounding, whose closing (ROUND_IN) would otherwise fill the 15 mm gap between the rims."""
    gap = box(-g.DBL, -80.0, g.DBL, BRIDGE_LOW).difference(
        unary_union([Polygon(g.lens_outline(sg, g.GROOVE_CLEAR + RIM)) for sg in (-1, 1)]))
    gap = max(getattr(gap, "geoms", [gap]), key=lambda q: q.intersects(box(-0.1, -80.0, 0.1, BRIDGE_LOW)))
    return gap.buffer(-NOSE_R, quad_segs=24).buffer(NOSE_R, quad_segs=24)


def outline_pts(step=0.6):
    """The front's outer outline, (y, z) points every ~step mm, counter-clockwise, all corners rounded."""
    p = unary_union([_half(-1), _half(1)])
    p = p.buffer(ROUND_IN, quad_segs=24).buffer(-ROUND_IN - ROUND_OUT, quad_segs=24).buffer(ROUND_OUT, quad_segs=24)
    p = p.difference(nose()).buffer(BLEND, quad_segs=24).buffer(-BLEND, quad_segs=24)
    ring = p.exterior
    n = int(ring.length / step)
    pts = [ring.interpolate(i / n, normalized=True) for i in range(n)]
    return [(q.x, q.y) for q in pts]


def outline():
    """The outline as one Face on x = 0: a single periodic spline, so the edge rounding is one edge each side."""
    pts = [Vector(0, y, z) for y, z in outline_pts()]
    return Face(Wire([Edge.make_spline(pts, periodic=True)]))


def front_solid():
    """The outline extruded X0..X1, front edge chamfered, back edge filleted (no cuts yet)."""
    face = outline()
    s = Pos(g.X0, 0, 0) * extrude(face, amount=g.FRONT_D, dir=(1, 0, 0))
    s = fillet(s.edges().filter_by_position(Axis.X, g.X0 - 0.01, g.X0 + 0.01), FILLET_BACK)
    s = chamfer(s.edges().filter_by_position(Axis.X, g.X1 - 0.01, g.X1 + 0.01), CHAMFER_FRONT)
    return s


# ================================================================ internals
# Everything below fits the v3 internals (first drawn in glasses_v3's blocky front) into this outline:
# the 5-LED slot under the brow with its translucent U, the corner pockets and their caps, the hinge
# (corner blocks, knuckles, pin), the closed rim's lens groove (no split, no screw), the nose pads
# that follow the rims' flare, and the thermistor's open channel from the right pad's socket to the pocket.

RIM_LIP = 0.5            # The rim overlaps the lens's 0.8 bevel this much: less to stretch when the lens pops in
POCKET = g.POCKET        # Corner pocket box (x, y, z), left side; its top is opened up through the brow here
POCKET_TOP = 20.0        # Cut the pocket (and the wire gate) up through whatever the brow's height is there
HINGE_BLOCK_Y0 = POCKET["y"][0] - 1.0    # Corner block's inner edge (|y|): a 1.0 wall inside the pocket
HINGE_BLOCK_X1 = g.X0 + FILLET_BACK + 0.1   # ... reaching past the front's back fillet, so the top stays whole
PAD_Z = (g.LENS_ZC - 8.0, g.LENS_ZC + 7.5)  # Nose pads' height (as glasses_v3's)
PAD_W = 4.0              # Pad width behind the nasal rim, from its edge outward: stays behind the rim (edge 3.6 + lip 0.5 from the apex)
PAD_X = (g.X0 - 6.3, g.X0 + 0.5)          # Pads stand back from the front; backs in front of the folded temples
# Thermistor wires: an OPEN channel laid in from outside and closed by soft-flex caps (user, 5 Nov 2026: a
# 98 mm, 1.3 mm tunnel with 4 corners couldn't be threaded). Route: out of the socket's back, up the pad's
# back face, forward over the pad's top, up the front's back face, forward over the brow's top, then
# along the brow's top (in front of the LED slot) into the corner pocket.
CH_W = 1.0               # Channel width (2 twisted 30 AWG enamelled wires are ~0.6)
CH_D = 1.6               # Depth: CH_CAP of soft-flex cap over 0.8 for the wires
CH_CAP = 0.8             # Cap thickness
CH_FIT = 0.05            # Cap oversize each side (a squeeze, as the other caps)
CH_TURN_Z = -18.0        # Channel reaches the pad's middle here (above the flare, where the rim is vertical)
BROW_CH_X = 8.3          # Brow run's opening, back edge (x) on the brow's top: in front of the LED slot
BROW_CH_D = 1.4          # Brow run's depth (z); it leans forward 45 deg going down, so the front (printed face
                         # down) has no flat ceiling over it. Front skin under it 0.6
CH_END_X = 10.0          # Crossing over the brow's top ends here (meets the brow run's wire space)
SOCKET_WALL = 0.8        # Round the pogo socket's 4.9 ring


def _rim_poly(sign):
    return Polygon(g.lens_outline(sign, g.GROOVE_CLEAR + RIM))


def nasal_edge(sign, z):
    """|y| of the rim's nasal edge (the nose opening's side) at height z."""
    hit = _rim_poly(sign).intersection(LineString([(0.0, z), (sign * g.LENS_YC, z)]))
    return min(abs(c[0]) for c in hit.coords)


def outline_prism(x0, x1):
    return Pos(x0, 0, 0) * extrude(outline(), amount=x1 - x0, dir=(1, 0, 0))


def hinge_block(sign):
    """Corner block behind one endpiece, from END_X0 (the open temple stops on it) into the front: cut
    from the outline itself, so it never shows past the wayfarer shape."""
    ya, yb = sorted((sign * HINGE_BLOCK_Y0, sign * (END_Y + 1)))
    return outline_prism(g.END_X0, HINGE_BLOCK_X1) & g.box(g.END_X0 - 1, g.X0 + 5, ya, yb, -40, 20)


def pad(sign):
    """Nose pad: a band PAD_W wide behind the nasal rim, from its edge outward, following the rim's
    flare (so it sits along the nose, wider apart lower down). Walls along x: prints with no overhang.
    The right pad also carries the pogo socket's boss at its foot."""
    nasal = box(min(0.0, sign * g.LENS_YC), PAD_Z[0], max(0.0, sign * g.LENS_YC), PAD_Z[1])
    band = (_rim_poly(sign) - Polygon(g.lens_outline(sign, g.GROOVE_CLEAR + RIM - PAD_W))) & nasal
    p = g.yz_prism(list(band.exterior.coords)[:-1], *PAD_X)
    if sign < 0:
        sx, sy, sz = socket_xyz(sign)
        r = g.POGO[2] / 2 + SOCKET_WALL
        p += Pos(sx, sy, sz + (g.POGO[3] + 1.5) / 2) * Cylinder(r, g.POGO[3] + 1.5)
    return p


def socket_xyz(sign=-1):
    """Pogo socket's axis at the pad's foot (x, y, z of its face), its inner side flush with the pad's."""
    r = g.POGO[2] / 2 + SOCKET_WALL
    return ((PAD_X[0] + PAD_X[1]) / 2, sign * (nasal_edge(sign, PAD_Z[0]) + r), PAD_Z[0])


def _seg(a, b, d):
    """Round bar from point a to b, diameter d, with a ball at b (smooth joints)."""
    a, b = Vector(*a), Vector(*b)
    v = b - a
    c = Solid.make_cylinder(d / 2, v.length, Plane(origin=a, z_dir=v))
    return c + Pos(b) * Sphere(d / 2)


def ch_y():
    """|y| of the channel's straight runs: the pad's middle where the rim is vertical."""
    return nasal_edge(-1, CH_TURN_Z) + PAD_W / 2


def pad_path(sign=-1):
    """Pad run's (y, z) points: from the socket's top, up the pad's back face (its middle) to its top."""
    sx, sy, sz = socket_xyz(sign)
    zb = sz + g.POGO[3] + 1.5                                  # Top of the socket's boss
    return [(sy, sz + g.POGO[3] - 0.3), (sign * (nasal_edge(sign, zb) + PAD_W / 2), zb),
            (sign * ch_y(), CH_TURN_Z), (sign * ch_y(), PAD_Z[1] + 1.0)]


def _pad_run(x0, x1, grow=0.0):
    pts = pad_path(-1)
    band = LineString(pts).buffer(CH_W / 2 + grow, quad_segs=8, cap_style="round", join_style="round")
    return g.yz_prism(list(band.exterior.coords)[:-1], x0, x1)


def _box_runs(d, grow=0.0):
    """The three straight runs at |y| = ch_y (right side): over the pad's top (along x), up the front's back
    face (z), over the brow's top (x). d: depth from each face (CH_D for the cut, CH_CAP for the caps)."""
    y = ch_y()
    ya, yb = -y - CH_W / 2 - grow, -y + CH_W / 2 + grow
    top = brow_top(y)
    pz = PAD_Z[1]
    return (g.box(PAD_X[0] - 1, g.X0 + d, ya, yb, pz - d, pz + 1)            # Over the pad's top
            + g.box(g.X0 - 1, g.X0 + d, ya, yb, pz - d, top + 1)             # Up the front's back face
            + g.box(g.X0 - 1, CH_END_X, ya, yb, top - d, top + 1))           # Over the brow's top


def _brow_section(y, d, grow):
    """Brow run's cross-section at y (right side): a parallelogram leaning forward 45 deg, d deep below the
    brow's top there, CH_W wide along x at the top (grow added across, as x)."""
    t = brow_top(y)
    a, w = BROW_CH_X - grow * math.sqrt(2), CH_W + 2 * grow * math.sqrt(2)
    pts = [(a - 1, t + 1), (a + w - 1, t + 1), (a + w + d, t - d), (a + d, t - d)]
    return Wire.make_polygon([Vector(x, -y, z) for x, z in pts], close=True)


def _brow_run(d, grow=0.0, y0=None, y1=None):
    """The cut runs into the corner pocket; the cap stops at its wall (y1), clear of the pocket cap."""
    y0 = ch_y() if y0 is None else y0
    y1 = POCKET["y"][0] + 0.5 if y1 is None else y1
    n = 12
    ys = [y0 + (y1 - y0) * i / n for i in range(n + 1)]
    return Solid.make_loft([_brow_section(y, d, grow) for y in ys], ruled=True)


def channel(sign=-1):
    """The whole open channel (right side), as a cut."""
    return _pad_run(PAD_X[0] - 1, PAD_X[0] + CH_D) + _box_runs(CH_D) + _brow_run(BROW_CH_D)


def _envelope():
    return front_solid() + pad(-1)


def channel_caps():
    """The channel's three soft-flex caps as fitted (right side): (pad, corner, brow). Pad: a flat strip on
    the pad's back face. Corner: one zigzag strip over the pad's top, up the front's back and over the
    brow's top. Brow: the long strip along the brow's top into the pocket. CH_FIT oversize across."""
    env = _envelope()
    corner = _box_runs(CH_CAP, CH_FIT) & env
    pad_cap = (_pad_run(PAD_X[0], PAD_X[0] + CH_CAP, CH_FIT) & env) - _box_runs(CH_CAP, 0.5)
    brow = _clip_top(_brow_run(CH_CAP, CH_FIT, y0=ch_y() + CH_W / 2 + CH_FIT, y1=POCKET["y"][0] - 0.1))
    return pad_cap, corner, brow


def _clip_top(s):
    """Trim a brow-run piece to the brow's top (the run's sections reach 1 mm above it)."""
    return s & outline_prism(g.X0 - 1, g.X1 + 1)


def brow_cap_flat():
    """The brow cap straight, for printing (soft flex bends to the brow's 2.4 mm rise): its section at the
    pocket end, lying on its bottom face."""
    y0, y1 = ch_y() + CH_W / 2 + CH_FIT, POCKET["y"][0] - 0.1
    a, w = BROW_CH_X - CH_FIT * math.sqrt(2), CH_W + 2 * CH_FIT * math.sqrt(2)
    d = CH_CAP
    pts = [(a, d), (a + w, d), (a + w + d, 0.0), (a + d, 0.0)]
    return g.xz_prism(pts, 0.0, y1 - y0)


def socket_cut(sign=-1):
    sx, sy, sz = socket_xyz(sign)
    boss, boss_h, ring, length = g.POGO
    c = Pos(sx, sy, sz + boss_h / 2 - 0.2) * Cylinder((boss + 0.1) / 2, boss_h + 0.4)
    c += Pos(sx, sy, sz + boss_h + (length + 0.5 - boss_h) / 2) * Cylinder((ring + 0.1) / 2, length + 0.5 - boss_h)   # +0.5 for the solder joints
    return c


def slot_y_in():
    return POCKET["y"][0] - g.PIECE_L - 0.8         # LED slot's inner end (|y|): the strip pushed home from the pocket


def translucent_u(sign):
    """The translucent U along the LED run: the eye-side wall, the floor under the slot and a skin on
    the slot's far face (as onepiece.translucent()), so the 5 LEDs blend into one bar."""
    ya, yb = sorted((sign * (POCKET["y"][0] - g.PIECE_L - 2.0), sign * (POCKET["y"][0] - 0.1)))
    return g.box(g.X0 - 0.5, g.SLOT_X[1] + 0.6, ya, yb, g.SLOT_Z[0] - 0.6, g.SLOT_Z[1] + 0.4)


def cuts(sign):
    right = sign < 0
    c = g.yz_prism(g.lens_outline(sign, -RIM_LIP), g.X0 - 1, g.X1 + 1)     # Lens opening (not the pads behind)
    c += g.groove(sign)                                                       # Closed rim: V groove, no split
    ya, yb = sorted((sign * slot_y_in(), sign * POCKET["y"][1]))
    c += g.box(*g.SLOT_X, ya, yb, *g.SLOT_Z)                                  # LED slot (strip in from the pocket)
    ya, yb = sorted((sign * POCKET["y"][0], sign * POCKET["y"][1]))
    c += g.box(*POCKET["x"], ya, yb, POCKET["z"][0], POCKET_TOP)              # Corner pocket, open at the top
    g0, g1, gz = g.WIRE_GATE
    c += g.side_place(g.box(g.END_X0 - 1, POCKET["x"][0] + 0.1, g0, g1, gz, POCKET_TOP), right)   # Wires over the hinge
    c += g.side_place(g.knuckle("mid", g.KNUCKLE_R + g.HINGE_CLEAR) + g.hinge_pin(), right)
    if right:
        c += socket_cut(sign) + channel(sign)
    return c


def front_whole():
    s = front_solid()
    for sign in (-1, 1):
        s += hinge_block(sign) + g.side_place(g.hinge_front(), sign < 0) + pad(sign)
    for sign in (-1, 1):
        s -= cuts(sign)
    return s


def front_pieces():
    """(body, translucent, whole): the two-colour pair, black PETG body and the translucent U's, same
    bed position."""
    y_in = slot_y_in()
    roof = min(brow_top(y) for y in (y_in, POCKET["y"][0])) - g.SLOT_Z[1]
    assert roof >= 0.8, f"brow only {roof:.2f} over the LED slot"
    whole = front_whole()
    clear = whole & (translucent_u(-1) + translucent_u(1))
    return whole - clear, clear, whole


def pocket_cap(sign):
    """Soft-flex plug in a corner pocket's top, 0.05 oversize: 0.8 thick at its lowest, its top
    following the brow's top (cut from the outline)."""
    ya, yb = sorted((sign * POCKET["y"][0], sign * POCKET["y"][1]))
    top = outline_prism(g.END_X0 - 1, g.X1 + 1) & g.box(POCKET["x"][0] - 0.05, POCKET["x"][1] + 0.05,
                                                        ya - 0.05, yb + 0.05, -20, POCKET_TOP)
    z_low = top.bounding_box().max.Z
    for y in (POCKET["y"][0], POCKET["y"][1]):
        z_low = min(z_low, _top_at(y))
    return top & g.box(-50, 50, -100, 100, z_low - 0.8, POCKET_TOP)


def _top_at(y):
    pts = outline_pts()
    poly = Polygon(pts)
    hit = poly.intersection(LineString([(abs(y), -50), (abs(y), 50)]))
    return hit.bounds[3]


def test_front():
    """The right half of the front (to 2 mm past the bridge's middle) with its pocket, hinge, pad,
    socket and thermistor channel: tries the lens fit, the nose pad, the hinge and the LEDs."""
    body, clear, _ = front_pieces()
    keep = g.box(-14, g.X1 + 2, -g.HALF_WIDTH - 10, 2.0, -60, 20)
    return body & keep, clear & keep
