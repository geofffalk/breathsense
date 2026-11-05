"""
BreathSense v3 concept: custom integrated glasses built round optician-cut lenses, carrying the v2
electronics (XIAO head-sensor pod on the right, battery pod on the left, cord behind the head).

What it is (user's decisions, 4 Nov 2026):
- Folds like normal glasses. Printed in three PETG pieces: the FRONT (soft wayfarer, wayfarer.py:
  black PETG with a translucent U in front of each LED run; both rims, bridge, moulded nose pads,
  both corners with the hinges' top and bottom knuckles) and two TEMPLES (hinge to tip,
  each with the middle knuckle). Each hinge is three printed knuckles on an M2 screw, its axis on
  the head side of the temple's front end; the temple's front face stops against the corner when
  open. The front prints front face down, the temples outer face down: no supports.
- Lenses: stock uncut blanks, edged by an optician to the wayfarer LENS_SHAPE in an LENS_A x LENS_B
  box (straight top) with a standard V bevel; held in a CLOSED rim (user, 5 Nov 2026: no split, no
  screw), popped in from behind with the rim warmed. The groove follows the lens's base curve (BASE_CURVE) inside a
  flat-faced rim, so the front still prints flat.
- LEDs: 5 per side, all on the front (user, 4 Nov 2026: LEDs on the temples, at the side of the
  eye, can't be seen at all). Each side's 5-LED strip lies straight under the brow over the outer half of
  the lens, LEDs facing the eye through a 0.8 mm translucent wall, its DIN end at the outer end in
  the corner pocket (soft-flex cap). The temples carry no LEDs: the strip's 3 wires run from the
  pod along the groove in the temple's outer face into the temple's front pocket (soft-flex cap),
  then over the hinge just above its top knuckle, close to the axis, so folding bends them rather
  than stretching them, into the corner pocket. Data runs pod -> front strip (outer to inner).
- Thermistor: magnetic pogo socket in the right nose pad, face down toward the nostril; its wires
  run in a tunnel up the right nasal rim and along the top bar into the corner pocket, across the
  hinge with the LED wires, then back along the groove in the temple's outer face (soft-flex cap) to the pod with the LED wires.
- Pods: v2's head-sensor board pod and battery pod, unchanged inside, on the temple tips, which are
  printed to the measured paddle shape they were designed round. Each is locked on with an M2
  screw through the pocket into a heat-set insert in the tip.

Frames:
- World (assembly): as assembly_onepiece.py: x forward (hinge line x = 0), y to the wearer's left,
  z up; temples' inner faces at y = +/-HALF_WIDTH, their top edge at z = 0.
- Temple frame (temple_front(), temple_rear(), hinge_*()): the v2 pod frame: y outward from the temple's inner face,
  modelled as the LEFT temple; place(..., right=True) mirrors it.

Run:  python glasses_v3.py   -> out/step/*.step, out/stl/*.stl, out/lens_template.svg/.dxf
"""

import math
import sys

from shapely.geometry import Polygon
from pathlib import Path

from build123d import (Cylinder, Plane, Pos, Rot, Sphere, export_step, export_stl, mirror)

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "glasses"))
sys.path.insert(0, str(HERE.parent / "v2"))
import glasses_mount as gm           # noqa: E402
import mount_v2 as mv                # noqa: E402
import hang_pods as hp               # noqa: E402
import assembly_onepiece as ao       # noqa: E402
from glasses_mount import box, xz_prism, yz_prism, xy_prism   # noqa: E402

OUT = HERE / "out"
# The user's glasses, photographed beside a ruler (4 Nov 2026, IMG_3650): hinges 148.6 mm apart (centres),
# lenses 56.2 and 57.2 mm wide where visible, 22-23 mm apart, about 36 mm tall, front about 43 mm tall.
# Photo readings, +/- about 1 mm: check against the size printed inside the temple.
HINGE_SPAN = 148.6       # Hinge axes this far apart
HALF_WIDTH = HINGE_SPAN / 2 + 2.2    # Temples' inner faces (the axis is 2.2 mm inside them: HINGE[1])

# ---------------------------------------------------------------- lens (optician-cut)
LENS_A = 58.0            # Box width (apex of the bevel), the "eye size": 56.7 visible + the bevel each side
LENS_B = 36.0            # Box height
DBL = 22.0               # Distance between lenses (bridge), at the apex
# Wayfarer lens (user, 4 Nov 2026): straight top (the strip runs above it), outer side sloping in toward the
# bottom, a long diagonal into the bottom-outer corner, nasal side nearly vertical. Corners rounded LENS_R.
LENS_SHAPE = [(-0.5, 0.0), (0.5, 0.0), (0.475, -0.42), (0.36, -1.0), (-0.36, -1.0), (-0.5, -0.45)]   # (y / A, z / B) from the
                         # box's top middle, LEFT lens (outer to +y); the right mirrors
LENS_R = 6.5             # Corner radius at the apex
LENS_TOP_Z = -4.0        # Apex top, below the temples' top edge (the user's glasses: about -4.5 by the corner)
BASE_CURVE = 2.0         # Lens front curve, dioptres (tooling index 1.53): the groove follows it. 2-base keeps the
TOOL_N = 1.53            # groove inside a 6.5 mm flat-faced rim; 4-base would need about 8.5 mm
R_BASE = (TOOL_N - 1) * 1000 / BASE_CURVE
LENS_EDGE_T = 2.2        # Edge thickness assumed for the model (plano CR-39 / polycarbonate)
BEVEL = 110.0            # Standard V bevel included angle
LIP = 0.8                # The rim overlaps the lens this much (the bevel's height)
GROOVE_CLEAR = 0.2       # Groove's root this far past the bevel's apex

# ---------------------------------------------------------------- front
X0 = ao.op.FRAME_BACK_X  # 4.8: front's back face (the reference frame's)
FRONT_D = 6.5            # Front depth (x): back LED wall 0.8, slot 2.4, wall 0.9, thermistor tunnel 1.2, skin 1.2
X1 = X0 + FRONT_D
RIM_W = 2.2              # Sets the corner pocket's inner end (LENS_YC + LENS_A / 2 + RIM_W + 0.4); the wayfarer's rim is wayfarer.RIM
APEX_X = 8.9             # Bevel apex's x at the lens centre; it moves back by the curve's sag toward the edge
TOP_Z = 2.8              # Old flat front's top edge; the wayfarer's brow is wayfarer.brow_top()
LENS_YC = DBL / 2 + LENS_A / 2       # Lens centres at y = +/-LENS_YC
LENS_ZC = LENS_TOP_Z - LENS_B / 2


# LED strip (v2 measurements)
STRIP_W, PITCH, LED_END = gm.STRIP_W, gm.LED_PITCH, ao.op.LED_END
STRIP_T = 1.2            # Thickness including the LEDs
PIECE_LEDS = 5           # LEDs per side, all on the front: a 10-LED strip cut between LEDs 5 and 6 makes both sides
PIECE_L = PIECE_LEDS * PITCH         # 34 mm: a cut falls midway between LEDs, so each LED's centre is PITCH/2 from a cut
SLOT_T, SLOT_H = 2.4, STRIP_W + 0.6  # Slot across the strip and along its width (prints 0.2-0.4 narrow)
WALL = 0.8               # LED wall: two lines of translucent PETG
# Top bar's slot, LEDs facing back (-x) at the eye
SLOT_X = (X0 + WALL, X0 + WALL + SLOT_T)
SLOT_Z = (-2.6, -2.6 + SLOT_H)
TUNNEL = 1.2             # Thermistor tunnel (2 twisted 30 AWG enamelled wires, ~0.7 mm)
TUN_X = (X1 - 1.2 - TUNNEL, X1 - 1.2)
TUN_Z = (-1.8, -1.8 + TUNNEL)

# Temples and the hinge (temple frame: x along the temple, y outward from its inner face, z up)
TEMPLE_T = hp.TIP_T      # 4.0: one thickness to the tip, so the temple's outer face lies flat on the bed
TEMPLE_H = 9.0           # Height at the hinge (matches the corner block), tapering to the tip's 4.5 at the ear bend
HINGE = (0.0, -2.2)      # Hinge axis (x, y): on the head side of the temple's front end, as normal glasses
KNUCKLE_R = 2.5          # Printed knuckles round an M2 screw as the pin (nyloc, or a nut in a trap)
HINGE_CLEAR = 0.25       # Radial clearance round each knuckle
BANDS = dict(top=(-3.0, -0.2), mid=(-5.8, -3.2), bot=(-8.8, -6.0))   # Front: top and bottom; temple: middle
END_X0 = 0.3             # Corner block's back face: the temple's front face (x = 0) stops against it when open

# Corner pocket (world, left side as modelled; the right mirrors): the front strip's outer end, the
# thermistor tunnel's end and the wires' loop, open at the top under a soft-flex cap. The wires cross
# the hinge just above its top knuckle, close to the axis, into the temple's own front pocket.
POCKET = dict(x=(END_X0 + 0.8, X1 - 0.8), y=(LENS_YC + LENS_A / 2 + RIM_W + 0.4, HALF_WIDTH + TEMPLE_T - 0.8),
              z=(SLOT_Z[0] - 1.0, TOP_Z))
WIRE_GATE = (-3.2, 2.4, BANDS["top"][1] + 0.4)   # Wires' notch over the hinge: y from..to (temple frame), floor z
END_Z0 = BANDS["bot"][0] - 0.7

M2_CLEAR, M2_HEAD, M2_NUT_AF, M2_NUT_T = 2.3, 4.2, 4.2, 1.7

POGO = hp.POGO           # Nose clip's magnetic socket (measured): boss 4.0 x 1.0, ring 4.9, 5.0 long

BEND_X = -gm.TEMPLE_STRAIGHT         # -99: ear bend (as the reference glasses)
TIP_T = hp.TIP_T                     # 4.0: tip thickness, the paddle the pods fit
GROOVE = dict(z=(-2.8, -0.6), d=2.4, cap_t=0.8)   # Wire groove in the temple's OUTER face (on the bed as printed:
                         # outer face down), 2.4 deep: 1.6 for the wires under a 0.8 soft-flex cap
T_POCKET_X = (-7.0, -0.8)            # Temple's front pocket (open at the top, soft-flex cap): the groove's wires
T_POCKET_Y = (0.8, 3.2)              # turn up here to cross the hinge; it holds their slack loop
T_POCKET_Z0 = GROOVE["z"][0] - 0.8   # Floor, just under the groove's
POD_SCREW_D = 15.0                   # Pod's lock screw this far back from the tip's end, mid-height

# Telescopic temple (user, 5 Nov 2026: fit different heads and keep the sensor on the skin). Two PETG pieces per
# temple: the FRONT piece (hinge knuckle, front pocket, then a sleeve) and the REAR piece (a tongue sliding in the
# sleeve, then the ear bend, tip and pod). A soft-flex liner in the sleeve's head-side wall presses the tongue
# against the outer wall: friction holds the length and it adjusts by hand, as the pods' TPE wedge. The wires lie
# loose (PTFE-insulated 30 AWG slides; silicone grips), anchored at the front pocket, along the front groove, into
# the sleeve, back along a trough in the tongue's top, out into the rear groove and on to the pod, whose cavity
# keeps the spare loop. Modelled at extension 0 (ear bend at BEND_X, as before); extension e moves the rear
# piece back by e.
JOINT_X0 = -20.0         # Front piece full section to here; the sleeve's cavity starts here
SLEEVE_X1 = -55.0        # Sleeve's rear end
TRAVEL = (-4.0, 8.0)     # Extension range: hinge to ear bend 95..107 mm
TONGUE_FRONT = JOINT_X0 - 0.5 + TRAVEL[0]   # Tongue's front end (rear piece, e = 0): 0.5 short of the cavity's end when shortest
SHOULDER_X = SLEEVE_X1 - 0.5 + TRAVEL[0]    # Rear piece's full section starts here (e = 0): 0.5 behind the sleeve when shortest
JOINT_CLEAR = 0.15       # Round the tongue in the sleeve (each side)
TONGUE_Y = (0.0, 2.8)    # Tongue across (flush with the rear piece's inner face, which prints on the bed)
TONGUE_Z = (-8.05, -0.95)   # The cavity's height; the tongue's body stops at TONGUE_TOP, the wires run over it
TONGUE_TOP = -3.15       # Tongue's flat top: the wires lie on it, inside the sleeve, under its roof
TONGUE_LIP = 1.55        # A 45-degree lip along the top's outer edge (prints unsupported, head side down) hides
                         # them where the tongue shows, pulled out
CAVITY_Y = (TONGUE_Y[0] - JOINT_CLEAR, TONGUE_Y[1] + JOINT_CLEAR)   # Outer wall 1.05 beyond (the outer face stays flat)
CAVITY_Z = (TONGUE_Z[0] - JOINT_CLEAR, TONGUE_Z[1] + JOINT_CLEAR)
SLEEVE_Y0 = CAVITY_Y[0] - 0.8 - 1.0   # Sleeve's head side: liner recess 0.8 + wall 1.0 (it bulges 1.95 toward the head)
J_LINER = dict(x=(SLEEVE_X1 + 1.0, JOINT_X0 - 1.0), z=(-7.4, TONGUE_TOP - 0.45), t=0.8, proud=0.4)   # Recess (closed both ends: the
                         # liner is pressed in sideways from the cavity) and the liner: 0.8 in it, 0.4 proud
                         # (0.25 squeeze on the tongue, 21% of its 1.2)
J_RIDGE = dict(x=(J_LINER["x"][0] + 0.5, J_LINER["x"][0] + 2.5), z=(-5.9, -4.6), h=0.4)   # Liner's ridge, riding in
J_SLOT = dict(x=(J_RIDGE["x"][0] + TRAVEL[0], J_RIDGE["x"][1] + TRAVEL[1]), z=(-6.0, -4.5), d=0.4)   # the tongue's slot:
                         # the slot's ends are soft end stops at both ends of TRAVEL
OPEN_ANGLE = 2.0         # Temples rest this far in (deg) when open, with no shim: they squeeze the head, so the sensor
                         # stays on. A shim on the stop face stops the temple sooner: more squeeze (SHIMS)
STOP_Y = (0.6, TEMPLE_T)                # The squeeze stop: the front piece's front face, angled to meet the corner block
SHIM_POCKET = dict(y=(2.4, 3.8), z=(-7.0, -2.0), d=0.6)   # Pocket in the stop face for a soft-flex shim (more squeeze)
SHIMS = (0.8, 0.9)       # Shim thicknesses (0.6 would sit flush): rest angles about 4.5 and 5.7 deg (shim_angle); print at 0.1 mm layers
TEMPLE_E = 1.9e3         # PETG modulus, MPa (for the squeeze estimate)


def leds_front(sign=-1):
    """World (y, z) of the front piece's LED centres, outer first, for the right (sign -1) side."""
    y_outer_end = LENS_YC + LENS_A / 2 + RIM_W + 0.4          # The piece's outer end, at the pocket
    return [(sign * (y_outer_end - PITCH / 2 - i * PITCH), (SLOT_Z[0] + SLOT_Z[1]) / 2) for i in range(PIECE_LEDS)]


# ================================================================ lens outline
def rrect(cy, cz, w, h, rt, rb, n=10):
    """Rounded rectangle (y, z) points, counter-clockwise: top corners radius rt, bottom rb."""
    pts = []
    corners = [(cy + w / 2 - rt, cz + h / 2 - rt, rt, 0), (cy - w / 2 + rt, cz + h / 2 - rt, rt, 90),
               (cy - w / 2 + rb, cz - h / 2 + rb, rb, 180), (cy + w / 2 - rb, cz - h / 2 + rb, rb, 270)]
    for x, z, r, a0 in corners:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((x + r * math.cos(a), z + r * math.sin(a)))
    return pts


def _lens_poly(d=0.0):
    """Shapely polygon of the left lens's bevel apex offset by d, in (y, z) about the box centre."""
    raw = Polygon([(u * LENS_A, LENS_B / 2 + v * LENS_B) for u, v in LENS_SHAPE])
    apex = raw.buffer(-LENS_R, quad_segs=12).buffer(LENS_R, quad_segs=12)
    return apex.buffer(d, quad_segs=12) if d else apex


def lens_outline(sign, d=0.0):
    """The bevel apex's outline offset by d (+ outward), right lens sign -1, left +1: (y, z) points."""
    pts = list(_lens_poly(d).exterior.coords)[:-1]
    return [(sign * (LENS_YC + y), LENS_ZC + z) for y, z in pts]


def lens_perimeter():
    return _lens_poly().exterior.length


def _r_max():
    """Farthest point of the apex outline from the lens's optical (box) centre."""
    return max(math.hypot(y, z) for y, z in _lens_poly().exterior.coords)


_sag = R_BASE - math.sqrt(R_BASE ** 2 - _r_max() ** 2)
_h0 = (LIP + GROOVE_CLEAR) * math.tan(math.radians(BEVEL / 2))
assert APEX_X + _h0 <= X1 - 0.6 and APEX_X - _sag - _h0 >= X0 + 0.5, "lens groove runs out of the rim: deepen FRONT_D"


def sag(r):
    return R_BASE - math.sqrt(R_BASE ** 2 - r ** 2)


def shell(sign, h0, h1):
    """The lens's curve as a solid: between spheres h0 and h1 (x offsets at the centre) from the apex surface."""
    c = Pos(APEX_X - R_BASE, sign * LENS_YC, LENS_ZC)
    return c * Sphere(R_BASE + h1) - c * Sphere(R_BASE + h0)


def groove(sign):
    """V groove round the lens, following the curve: stepped (4 steps), 0.2 mm past the apex."""
    depth = LIP + GROOVE_CLEAR
    t = math.tan(math.radians(BEVEL / 2))
    out = None
    steps = 4
    for i in range(steps):
        rho = depth * i / steps                                   # From the root toward the lens's centre
        h = (rho + depth / steps) * t                             # Half-width at the step's outer edge (conservative)
        ring = yz_prism(lens_outline(sign, GROOVE_CLEAR - rho), X0 - 5, X1 + 5) & shell(sign, -h, h)
        out = ring if out is None else out + ring
    return out


def lens(sign):
    """The edged lens: LENS_EDGE_T thick on the curve, its V bevel's apex on the outline."""
    t = math.tan(math.radians(BEVEL / 2))
    body = yz_prism(lens_outline(sign, -LIP), X0 - 5, X1 + 5) & shell(sign, -LENS_EDGE_T / 2, LENS_EDGE_T / 2)
    steps = 4
    for i in range(1, steps):
        u = LIP * i / steps                                        # In from the apex (stepped small: no overlap)
        h = min(u * t, LENS_EDGE_T / 2) - 0.05
        body += yz_prism(lens_outline(sign, -u), X0 - 5, X1 + 5) & shell(sign, -h, h)
    return body


# ================================================================ temple (temple frame)
def temple_bottom(x):
    """z of the rear piece's lower edge: full height at its shoulder, tapering to the tip's at the bend."""
    x_run = SHOULDER_X
    if x >= x_run:
        return -TEMPLE_H
    h1 = hp.paddle_h(gm.TIP_LEN)                              # 4.5: the tip's height at the bend
    f = min((x - x_run) / (BEND_X - x_run), 1.0)
    return -(TEMPLE_H + (h1 - TEMPLE_H) * f)


def straight(x0, x1, n=8):
    """Straight temple between x1 (front) and x0 (back), top at z = 0."""
    out = None
    xs = [x1 + (x0 - x1) * i / n for i in range(n + 1)]
    for xa, xb in zip(xs, xs[1:]):
        seg = xz_prism([(xa + 0.01, 0), (xb - 0.01, 0), (xb - 0.01, temple_bottom(xb)),
                        (xa + 0.01, temple_bottom(xa))], 0, TEMPLE_T)
        out = seg if out is None else out + seg
    return out


def groove_cut(x0, x1, t):
    """The wire groove in the outer face (y = t), for x0..x1."""
    return box(x0, x1, t - GROOVE["d"], t + 1, *GROOVE["z"])


def knuckle(band, r=KNUCKLE_R):
    z0, z1 = BANDS[band]
    return Pos(HINGE[0], HINGE[1], (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def hinge_pin():
    """M2 pin screw: clearance through all three knuckles, head counterbore on top, nut trap below."""
    hx, hy = HINGE
    z0, z1 = BANDS["bot"][0], BANDS["top"][1]
    c = Pos(hx, hy, (z0 + z1) / 2) * Cylinder(M2_CLEAR / 2, z1 - z0 + 2)
    c += Pos(hx, hy, z1) * Cylinder(M2_HEAD / 2, 2.4)
    c += Pos(hx, hy, z0) * Cylinder(M2_NUT_AF / math.sqrt(3) + 0.1, 2 * M2_NUT_T)
    return c


def hinge_front():
    """The front's two knuckles (top, bottom) on webs back from the corner block (temple frame)."""
    hx, hy = HINGE
    out = None
    for band in ("top", "bot"):
        z0, z1 = BANDS[band]
        k = knuckle(band) + box(hx, END_X0 + 0.5, hy - KNUCKLE_R, hy + KNUCKLE_R, z0, z1)
        out = k if out is None else out + k
    return out


def temple_front():
    """The temple's front piece (left as modelled, temple frame): the middle knuckle on the head side of
    the front end, the squeeze stop and its shim pocket, the front pocket (open at the top) where the
    wires turn up to cross the hinge, the outer-face groove, then the sleeve (JOINT_X0..SLEEVE_X1),
    bulging toward the head, with the liner's recess in its head-side wall."""
    hx, hy = HINGE
    t = box(SLEEVE_X1, 0.0, 0.0, TEMPLE_T, -TEMPLE_H, 0.0)
    t += box(SLEEVE_X1, JOINT_X0 + 2.0, SLEEVE_Y0, 0.1, -TEMPLE_H, 0.0)                         # Sleeve's head side
    z0, z1 = BANDS["mid"]
    t += knuckle("mid") + box(hx - KNUCKLE_R, hx, hy, 0.2, z0, z1)                          # Knuckle and web
    t += stop_wedge()
    for band in ("top", "bot"):
        t -= knuckle(band, KNUCKLE_R + HINGE_CLEAR)
    t -= hinge_pin()
    t -= shim_pocket()
    t -= box(T_POCKET_X[0], T_POCKET_X[1], *T_POCKET_Y, T_POCKET_Z0, 1)                        # Front pocket
    t -= box(T_POCKET_X[1] - 0.1, 0.5, 0.0, WIRE_GATE[1], WIRE_GATE[2] - 1.5, 1)                 # Wires in from the hinge
    t -= groove_cut(JOINT_X0 - 0.5, T_POCKET_X[0] + 0.5, TEMPLE_T)                             # Pocket to the sleeve
    t -= box(SLEEVE_X1 - 1, JOINT_X0, *CAVITY_Y, *CAVITY_Z)                                    # Sleeve's cavity
    t -= box(*J_LINER["x"], CAVITY_Y[0] - J_LINER["t"], CAVITY_Y[0] + 0.01, *J_LINER["z"])     # Liner's recess
    return t


def stop_wedge():
    """Material on the front piece's front face that meets the corner block (x = END_X0) when the temple
    is turned OPEN_ANGLE in: the open temples rest squeezing the head."""
    face = fold(box(-3.0, END_X0, *STOP_Y, -TEMPLE_H, 0.0), -OPEN_ANGLE)
    return face & box(-0.5, 3.0, *STOP_Y, -TEMPLE_H, 0.0)


def shim_pocket():
    sp = SHIM_POCKET
    return fold(box(END_X0 - sp["d"], END_X0 + 1.0, *sp["y"], *sp["z"]), -OPEN_ANGLE)


def shim(t):
    """Soft-flex shim, t thick, in the stop's pocket (0.05 under size round it): the temple then rests
    shim_angle(t) in instead of OPEN_ANGLE (it stops sooner). Modelled in place (temple frame)."""
    sp = SHIM_POCKET
    return fold(box(END_X0 - sp["d"], END_X0 - sp["d"] + t, sp["y"][0] + 0.05, sp["y"][1] - 0.05,
                    sp["z"][0] + 0.05, sp["z"][1] - 0.05), -OPEN_ANGLE)


def shim_angle(t):
    """Rest angle (deg in) with a shim t thick: where the shim's face first touches the corner block."""
    s = shim(t)
    lo, hi = OPEN_ANGLE - 1.0, 15.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if fold(s, mid).bounding_box().max.X > END_X0:
            lo = mid
        else:
            hi = mid
    return hi


def temple_rear(e=0.0):
    """The temple's rear piece (left as modelled, temple frame) at extension e: the tongue (the wires
    run over its flat top, behind its 45-degree lip; the stop slot in its head-side face), the full section from the shoulder,
    tapering to the bend, the outer-face groove, and the tip (the measured paddle, turned down 40
    degrees) with the heat-set insert hole for the pod's lock screw."""
    t = straight(BEND_X, SHOULDER_X)
    t += box(SHOULDER_X - 0.5, TONGUE_FRONT, *TONGUE_Y, TONGUE_Z[0], TONGUE_TOP)                # Tongue
    y1 = TONGUE_Y[1]
    t += yz_prism([(y1 - TONGUE_LIP, TONGUE_TOP - 0.01), (y1, TONGUE_TOP - 0.01), (y1, TONGUE_TOP + TONGUE_LIP)],
                  SHOULDER_X - 0.5, TONGUE_FRONT)                                                # Its lip
    t -= box(*J_SLOT["x"], TONGUE_Y[0] - 1, TONGUE_Y[0] + J_SLOT["d"], *J_SLOT["z"])            # Stop slot
    t -= groove_cut(BEND_X - 1, SHOULDER_X - 0.5, TEMPLE_T)
    t -= box(SHOULDER_X - 3.0, SHOULDER_X + 0.1, 0.3, TEMPLE_T + 1, TONGUE_TOP, GROOVE["z"][1])   # Wires out to the groove
    n = 24
    d1 = gm.TIP_LEN
    pts = [(hp.TIP_END_X + d1 * i / n, -hp.paddle_h(d1 * i / n)) for i in range(n + 1)]
    tip = xz_prism([(hp.TIP_END_X, 0.0), (BEND_X + 0.6, 0.0)] + [(BEND_X + 0.6, pts[-1][1])] + pts[::-1], 0, TIP_T)
    tip -= groove_cut(hp.GRIP_X1, BEND_X + 1.5, TIP_T)
    tip -= box(hp.GRIP_X1, hp.GRIP_X1 + 3.0, TIP_T - GROOVE["d"], TIP_T + 1, GROOVE["z"][0], 1)   # Wires up into the pod's channel
    xi, zi = hp.TIP_END_X + POD_SCREW_D, -hp.paddle_h(POD_SCREW_D) / 2
    tip -= Pos(xi, TIP_T - 1.5, zi) * Rot(90, 0, 0) * Cylinder(3.2 / 2, 3.2)                  # M2 heat-set insert
    bx, bz = ao.BEND
    t += Pos(bx, TIP_T / 2, bz) * Rot(90, 0, 0) * Cylinder(-bz + 0.3, TIP_T)                 # Round the bend
    t -= box(BEND_X - 2.5, BEND_X + 2.0, TIP_T - GROOVE["d"], TEMPLE_T + 1, GROOVE["z"][0] - 0.5, GROOVE["z"][1])
    return Pos(-e, 0, 0) * (t + ao.onto_tip(tip))


def joint_liner():
    """Soft-flex liner in the sleeve's head-side recess (temple frame, fixed to the front piece): 0.05
    under size along and across the recess, 0.4 proud into the cavity, with the stop ridge at its rear."""
    L = J_LINER
    y0 = CAVITY_Y[0] - L["t"]
    s = box(L["x"][0] + 0.05, L["x"][1] - 0.05, y0, CAVITY_Y[0] + L["proud"], L["z"][0] + 0.05, L["z"][1] - 0.05)
    s += box(*J_RIDGE["x"], CAVITY_Y[0] + L["proud"] - 0.1, CAVITY_Y[0] + L["proud"] + J_RIDGE["h"], *J_RIDGE["z"])
    return s


def temple(e=0.0):
    """(front piece, rear piece at extension e, liner)."""
    return temple_front(), temple_rear(e), joint_liner()


def squeeze_estimate(at_x=None):
    """Rough stiffness (N/mm) of an open temple, pushed outward at at_x (default: the sensor, near the
    paddle's end), as a cantilever from the hinge stop: front 4.0 thick, the sleeve section, the tapering
    rear, the tip. Bending in y (across the thickness)."""
    if at_x is None:
        at_x = BEND_X - gm.TIP_LEN * math.cos(math.radians(gm.TIP_ANGLE)) + 5.0
    L = -at_x
    n = 400
    c = 0.0
    for i in range(n):
        x = -(i + 0.5) * L / n
        h = -temple_bottom(x) if x < SHOULDER_X else TEMPLE_H
        if x < BEND_X:
            h = 6.0                                           # Paddle with the pod round it: stiffer; rough
        t = TEMPLE_T
        I = h * t ** 3 / 12
        if SLEEVE_X1 < x < JOINT_X0:                          # Sleeve walls plus the tongue (liner-coupled): sum
            I = TEMPLE_H * (TEMPLE_T - SLEEVE_Y0) ** 3 / 12 - (CAVITY_Z[1] - CAVITY_Z[0]) * (CAVITY_Y[1] - SLEEVE_Y0 - 1.0) ** 3 / 12
        c += (L - (-x)) ** 2 / (TEMPLE_E * I) * (L / n)
    return 1.0 / c, L


def fold(shape, angle):
    """A temple-frame shape (left as modelled) turned about the hinge axis by angle (90 = folded in)."""
    hx, hy = HINGE
    return Pos(hx, hy, 0) * Rot(0, 0, angle) * Pos(-hx, -hy, 0) * shape


def pod_lock_hole(pod_d):
    """Through the pod's pocket outer wall (and the liner's outer leg) to the tip: M2 x 10."""
    xi, zi = hp.TIP_END_X + POD_SCREW_D, -hp.paddle_h(POD_SCREW_D) / 2
    y1 = pod_d["y1"]
    h = Pos(xi, (TIP_T + y1) / 2, zi) * Rot(90, 0, 0) * Cylinder(M2_CLEAR / 2, y1 - TIP_T + 2)
    h += Pos(xi, y1, zi) * Rot(90, 0, 0) * Cylinder(M2_HEAD / 2, 3.0)                           # Head counterbore
    return h


def pods():
    """v2 pods with the lock hole: (head pod, its lid, its liner, battery pod, its lid, liner)."""
    hpod, hlid, hd = hp.board_pod("head")
    bpod, blid, bd = hp.battery_pod()
    hole_h, hole_b = pod_lock_hole(hd), pod_lock_hole(bd)
    return (hpod - hole_h, hlid, hp.liner_head() - hole_h, bpod - hole_b, blid, hp.liner() - hole_b)


# ================================================================ front (world)
def side_place(shape, right):
    """Temple-frame shape (left as modelled) into the world: inner faces at y = +/-HALF_WIDTH, the
    right side mirrored."""
    if not right:
        return Pos(0, HALF_WIDTH, 0) * shape
    return Pos(0, -HALF_WIDTH, 0) * mirror(shape, Plane.XZ)


# The front itself (outline, rounding, LED slot and translucent U, pockets, hinge, closed-rim groove, pads,
# socket and thermistor tunnel) is built in wayfarer.py, which imports this module for its constants.
def front_pieces():
    """(body, translucent, whole): the two-colour pair, same bed position."""
    import wayfarer
    return wayfarer.front_pieces()


# ================================================================ small parts
def pocket_cap(sign):
    import wayfarer
    return wayfarer.pocket_cap(sign)


def groove_cap_front():
    """Soft-flex cap over the front piece's wire groove (temple frame), front pocket to the sleeve. 0.05
    oversize each side."""
    g = GROOVE
    return box(JOINT_X0 - 0.3, T_POCKET_X[0] + 0.3, TEMPLE_T - g["cap_t"], TEMPLE_T, g["z"][0] - 0.05, g["z"][1] + 0.05)


def groove_cap_rear(e=0.0):
    """Soft-flex cap over the rear piece's groove, shoulder to the bend; cut the tip's 17 mm piece off its end."""
    g = GROOVE
    return Pos(-e, 0, 0) * box(BEND_X, SHOULDER_X - 0.3, TEMPLE_T - g["cap_t"], TEMPLE_T, g["z"][0] - 0.05, g["z"][1] + 0.05)


def temple_pocket_cap():
    """Soft-flex plug over the temple's front pocket (temple frame), 0.05 oversize."""
    return box(T_POCKET_X[0] - 0.05, T_POCKET_X[1] + 0.05, T_POCKET_Y[0] - 0.05, T_POCKET_Y[1] + 0.05, -0.8, 0)


def strip_front(sign):
    y_outer = LENS_YC + LENS_A / 2 + RIM_W + 0.4
    ya, yb = sorted((sign * y_outer, sign * (y_outer - PIECE_L)))
    return box(SLOT_X[0] + 0.3, SLOT_X[0] + 0.3 + STRIP_T, ya, yb, SLOT_Z[0] + 0.3, SLOT_Z[0] + 0.3 + STRIP_W)


def test_front():
    import wayfarer
    return wayfarer.test_front()


# ================================================================ print orientation
def print_orient_front(p):
    """Front face down (x up out of the bed becomes -x): the knuckles stand up at the back."""
    return mv._to_bed(Rot(0, 90, 0) * p)


def print_orient_temple(p):
    """Outer face down (the left temple as modelled): the knuckle stands up on the head side, the
    tip's outer face is in the same plane, and the groove opens onto the bed."""
    return mv._to_bed(Rot(-90, 0, 0) * p)


def lens_template():
    """SVG and DXF, 1:1 in mm: the bevel apex outline for the optician, with the box, centre and datum."""
    pts = lens_outline(1)
    yc, zc = LENS_YC, LENS_ZC
    rel = [(y - yc, z - zc) for y, z in pts]
    W = LENS_A + 30
    H = LENS_B + 40
    path = " ".join(("M" if i == 0 else "L") + f"{y + W / 2:.3f},{H / 2 - z:.3f}" for i, (y, z) in enumerate(rel)) + " Z"
    per = lens_perimeter()
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<path d="{path}" fill="none" stroke="black" stroke-width="0.2"/>',
        f'<line x1="{W / 2 - LENS_A / 2 - 5}" y1="{H / 2}" x2="{W / 2 + LENS_A / 2 + 5}" y2="{H / 2}" stroke="red" stroke-width="0.15"/>',
        f'<line x1="{W / 2}" y1="{H / 2 - LENS_B / 2 - 5}" x2="{W / 2}" y2="{H / 2 + LENS_B / 2 + 5}" stroke="red" stroke-width="0.15"/>',
        f'<rect x="{W / 2 - 25}" y="{H - 8}" width="50" height="0.3" fill="black"/>',
        f'<text x="{W / 2 - 25}" y="{H - 9}" font-size="2.2">50 mm check bar</text>',
        f'<text x="2" y="4" font-size="2.4">BreathSense v3 lens shape, LEFT lens viewed from the front (mirror for the right); 1:1 mm</text>',
        f'<text x="2" y="7" font-size="2.2">Bevel apex: A {LENS_A} x B {LENS_B} mm, DBL {DBL}, frame PD {LENS_A + DBL} mm, apex perimeter {per:.1f} mm.'
        f' V bevel {BEVEL:.0f} deg, {BASE_CURVE:.0f}-base front curve, edge >= 2.0 mm.</text>',
        f'<text x="2" y="10" font-size="2.2">Datum: red lines = box centre (horizontal = 180 deg line). Nasal side toward the centre of the glasses.</text>',
        '</svg>']
    (OUT / "lens_template.svg").write_text("\n".join(lines))
    dxf = ["0", "SECTION", "2", "ENTITIES", "0", "LWPOLYLINE", "8", "LENS", "90", str(len(rel)), "70", "1"]
    for y, z in rel:
        dxf += ["10", f"{y:.4f}", "20", f"{z:.4f}"]
    for a, b in (((-LENS_A / 2 - 5, 0), (LENS_A / 2 + 5, 0)), ((0, -LENS_B / 2 - 5), (0, LENS_B / 2 + 5))):
        dxf += ["0", "LINE", "8", "DATUM", "10", f"{a[0]}", "20", f"{a[1]}", "11", f"{b[0]}", "21", f"{b[1]}"]
    dxf += ["0", "ENDSEC", "0", "EOF"]
    (OUT / "lens_template.dxf").write_text("\n".join(dxf) + "\n")
    return per


def main():
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    body, clear, whole = front_pieces()
    tb, tc = test_front()
    tf, tr, tl = temple()
    hpod, hlid, hliner, bpod, blid, bliner = pods()
    front_rot = Rot(0, 90, 0)
    left_rot, right_rot = Rot(-90, 0, 0), Rot(90, 0, 0)
    mx = lambda p: mirror(p, Plane.XZ)                                      # noqa: E731
    items = [
        ("front_body_petg", body, front_rot, whole),
        ("front_translucent_petg", clear, front_rot, whole),
        ("test_front_body_petg", tb, front_rot, tb + tc),
        ("test_front_translucent_petg", tc, front_rot, tb + tc),
        ("temple_front_left_petg", tf, left_rot, tf),                     # Outer face down
        ("temple_front_right_petg", mx(tf), right_rot, mx(tf)),
        ("temple_rear_left_petg", tr, right_rot, tr),                     # Inner (head) face down
        ("temple_rear_right_petg", mx(tr), left_rot, mx(tr)),
        ("liner_joint_flex", tl, lambda p: mv._to_bed(Rot(90, 0, 0) * p), None),   # Recess face down (x2)
        ("pod_board_head_petg", mirror(hpod, Plane.XZ), hp.print_orient_head_down_mirrored, None),
        ("pod_battery_petg", bpod, hp.print_orient_head_down, None),
        ("liner_head_flex", mirror(hliner, Plane.XZ), hp.print_orient_liner, None),
        ("liner_battery_flex", bliner, hp.print_orient_liner, None),
        ("lid_board_head_flex", hlid, mv.print_orient_lid, None),
        ("lid_battery_flex", blid, mv.print_orient_lid, None),
        ("cap_pocket_flex", pocket_cap(1), lambda p: mv._to_bed(p), None),
        ("cap_temple_pocket_flex", temple_pocket_cap(), lambda p: mv._to_bed(p), None),
        ("cap_groove_front_flex", groove_cap_front(), lambda p: mv._to_bed(Rot(90, 0, 0) * p), None),
        ("cap_groove_rear_flex", groove_cap_rear(), lambda p: mv._to_bed(Rot(90, 0, 0) * p), None),
    ] + [
        (f"shim_{round(t * 10):02d}_flex", shim(t), lambda p: mv._to_bed(Rot(0, 90, 0) * fold(p, OPEN_ANGLE)), None) for t in SHIMS
    ]
    for name, shape, orient, ref in items:
        export_step(shape, str(OUT / "step" / f"{name}.step"))
        if ref is not None:
            # Two-colour pairs: place by the whole part's bed offset so they stay registered
            bb = (orient * ref).bounding_box()
            placed = Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * (orient * shape)
        else:
            placed = orient(shape)
        export_stl(placed, str(OUT / "stl" / f"{name}.stl"))
        print(f"wrote {name:30s} {shape.volume:8.0f} mm3  solids {len(shape.solids())}")
    per = lens_template()
    print(f"lens: A {LENS_A} B {LENS_B} DBL {DBL} PD {LENS_A + DBL}  apex perimeter {per:.1f}  R_base {R_BASE:.0f}"
          f"  max sag {sag(_r_max()):.2f}")


if __name__ == "__main__":
    main()
