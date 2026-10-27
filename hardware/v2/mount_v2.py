"""
BreathSense v2 glasses mount: a rigid PETG rail on each temple, carrying the NeoPixel strip.

Why it changed from v1: the soft-flex sleeve gripped with about 0.03-0.3 N per leaf and its
neck and corner had almost no stiffness, so it flopped about and slid. Here:

- The rail is PETG. It carries the open LED channel on its head side and two clips. Each clip
  has an outer leg with two thin leaves angled toward the temple (the v1 leaf idea, now in a
  stiff material). They press the temple against a soft-flex liner on the rail's face.
- PETG is about 80x stiffer than the soft flex, so one rail can't span 2-6 mm temples without
  overstressing the leaves. The rail comes in three sizes (S, M, L), each covering about
  1.3 mm of temple thickness. The leaves are sized so their bending stress at the thickest
  temple in each size stays under about 30 MPa (PETG yields at about 50 MPa).
- The liner is a soft-flex bar that slides into a dovetail groove along the rail's temple
  face. Soft flex is grippy; the PETG gives the clamping force.
- The corner is a separate soft-flex piece printed already bent (100 degrees, 10 over the
  frame's 90), so at rest it holds its front end against the frame front instead of flopping
  straight. It slides down onto a tongue on the rail's front end and carries the front four
  LEDs: one at the hinge and three on the flap against the frame front. It bends further when the glasses fold.
- There is no neck or ear-end arch: the rail stops before the ear bend. The wires cross the
  bend loose to the pods, which clip onto the temple tips: the XIAO pod on the right, with the
  soft-flex MAX30101 arm, and the battery pod on the left.
- A snap-on diffuser printed in natural PETG covers each rail's LED channel, and two caps
  cover the corner's four LEDs.

Coordinates, as worn on the RIGHT temple (the left parts are mirrored): x forward (glasses
hinge at x = 0), y outward (temple inner face at y = 0), z up (temple top edge at z = 0).
Parts are modelled as fitted, unloaded.

Run:  python mount_v2.py   -> out/step/*.step, out/stl/*.stl (print orientation)
"""

import math
import sys
from pathlib import Path

from build123d import Compound, Plane, Polyline, Pos, Rot, export_step, export_stl, extrude, make_face, mirror

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
import glasses_mount as gm   # noqa: E402  (box/prism helpers and the LED strip's measurements)
from glasses_mount import box, xy_prism, yz_prism   # noqa: E402

OUT = Path(__file__).parent / "out"

# ---------------------------------------------------------------- sizes
# Temple thickness each rail size grips (y). The reference glasses are 4.0 mm at the front
# clip and about 3.5 mm at the rear clip, both inside M.
SIZES = {"S": (2.0, 3.3), "M": (3.3, 4.6), "L": (4.6, 6.0)}
PRELOAD = 0.3        # Unloaded, the leaf tips stand this far inside the thinnest temple of the size

# ---------------------------------------------------------------- material
E_PETG = 2000.0      # MPa, along the printed lines
STRESS_MAX = 30.0    # MPa, peak leaf bending stress allowed at the thickest temple of a size

# ---------------------------------------------------------------- rail
LP = 0.6             # Rail face stands this far off the temple; the liner fills the gap
RB = 2.2             # Rail body thickness behind its face (LED channel plus floor)
RAIL_X0 = -90.0      # Rail runs from just before the ear bend ...
RAIL_X1 = -6.0       # ... to just behind the hinge (clear of the screw head; measure yours)
CLIP_T = 1.6         # Top bar thickness. Prints on its top face, so every rail feature reaches z = CLIP_T
OL_T = 1.6           # Outer leg thickness
OL_H = 9.0           # Rail and outer leg reach this far below the temple's top edge
CLIP_L = 32.0
CLIPS = [(RAIL_X1 - CLIP_L, RAIL_X1), (RAIL_X0 + 2.0, RAIL_X0 + 2.0 + CLIP_L)]
BRIDGE_W = 2.0       # Top bar left at each clip end; between them the leaves stand free

# Leaves: vertical plates, angled in plan off the outer leg toward the temple
LEAF_T = 0.8         # Two perimeters with a 0.4 mm nozzle
LEAF_ANGLE = 65.0    # From straight across, toward the clip's middle
LEAF_L = 13.0        # Root to tip
RAMP = 1.0           # Bottom edges slope up toward the tips (dz/dy), so pushing down opens them

# LED channel (head side), lower on the rail than in v1 to leave the top 3 mm for the liner
CH_W = gm.STRIP_W + 0.4
CH_D = gm.STRIP_PCB + 0.2 + gm.LIP_T
CH_Z1 = -3.4
CH_Z0 = CH_Z1 - CH_W
CH_Y0 = -LP - RB                     # Channel mouth (rail's head-side face)
LIP, LIP_T, LIP_L = gm.LIP, gm.LIP_T, gm.LIP_L

# Liner groove in the rail's temple face: a dovetail running the rail's length, open at the back
GROOVE_Z = (-2.8, -0.6)              # At the rail face
GROOVE_FLARE = 0.3                   # Wider by this much each side at the bottom
GROOVE_D = 0.6
LINER_CLEAR = 0.1

# Tongue on the rail's front end that the corner slides down onto. It runs up to the top face
# so it stands on the bed when printed.
TONGUE = dict(y=(-1.1, -0.3), z=(CH_Z0 - 0.4, CLIP_T), l=6.0)

# ---------------------------------------------------------------- LED layout
# The 10-LED piece, measured along the strip from the rail's front face (negative: on the rail).
# Three LEDs sit on the corner's flap against the frame front, one on the corner's straight part
# at the hinge, and six along the rail. The flap's first LED is FLAP_LED_D along the flap from
# the bend's end, with the corner fitted at 90 degrees.
LEDS = 10
LEDS_ON_FLAP = 3
FLAP_LED_D = 1.5

# ---------------------------------------------------------------- corner (soft flex)
CORNER_ANGLE = 100.0     # As printed; the frame front holds it at about 90
CORNER_R = 3.0           # Bend radius at the strip
CORNER_FLAP = 20.0       # Straight part after the bend, against the frame front (holds 3 LEDs)
FLAP_LIPS = (FLAP_LED_D + 0.5 * gm.LED_PITCH, FLAP_LED_D + 1.5 * gm.LED_PITCH)   # Between the flap LEDs
CORNER_Z = (CH_Z0 - 1.0, CH_Z1 + 1.0)
SLOT_CLEAR = 0.05        # Tongue slot is this much tighter than the tongue, each side (soft, so it grips)


# ================================================================ leaves
def leaf_geometry(size):
    """(rest, gap): the unloaded tip position and the outer leg's inner face, in y."""
    t_min, _ = SIZES[size]
    a = math.radians(LEAF_ANGLE)
    rest = t_min - PRELOAD
    gap = rest + LEAF_L * math.cos(a) + LEAF_T / 2 * math.sin(a) - 0.5
    return rest, gap


def leaf_check(size):
    """Peak bending stress (MPa) and tip force (N) at the thinnest and thickest temple."""
    t_min, t_max = SIZES[size]
    rest, _ = leaf_geometry(size)
    a = math.radians(LEAF_ANGLE)
    h = OL_H + CLIP_T
    inertia = h * LEAF_T ** 3 / 12
    out = []
    for t in (t_min, t_max):
        d = (t - rest) / math.sin(a)          # Tip deflection across the leaf for this much y
        out.append((3 * E_PETG * LEAF_T * d / (2 * LEAF_L ** 2), 3 * E_PETG * inertia * d / LEAF_L ** 3))
    return out


def leaf_outline(xr, sense, size):
    """Plan (x, y) outline of a leaf rooted in the outer leg at x = xr, leaning toward +x
    (sense 1) or -x (sense -1)."""
    rest, gap = leaf_geometry(size)
    a = math.radians(LEAF_ANGLE)
    d = (sense * math.sin(a), -math.cos(a))
    n = (-d[1] * LEAF_T / 2, d[0] * LEAF_T / 2)
    r = (xr, gap + 0.5)                        # Root buried in the outer leg
    tip = (xr + d[0] * LEAF_L, gap + 0.5 + d[1] * LEAF_L)
    return [(r[0] + n[0], r[1] + n[1]), (tip[0] + n[0], tip[1] + n[1]), (tip[0] - n[0], tip[1] - n[1]),
            (r[0] - n[0], r[1] - n[1])]


def leaf_roots(x0, x1):
    c = BRIDGE_W + 0.8
    return [(x0 + c, 1), (x1 - c, -1)]


# ================================================================ rail
def lip_positions(x0, x1):
    xs, x = [], x1 - 3.0
    while x > x0 + 2.0:
        xs.append(x)
        x -= 2 * gm.LED_PITCH
    return xs


def groove_outline(clear=0.0):
    """(y, z) dovetail outline of the liner groove; with clear > 0, of the liner's rib inside it."""
    z0, z1 = GROOVE_Z
    f = GROOVE_FLARE
    return [(-LP + 0.01, z0 + clear), (-LP - GROOVE_D + clear, z0 - f + clear),
            (-LP - GROOVE_D + clear, z1 + f - clear), (-LP + 0.01, z1 - clear)]


def rail(size, x0=RAIL_X0, x1=RAIL_X1, clips=CLIPS, tongue=True):
    """Rail body, its clips and the LED channel. x0..x1 trims it (for test pieces)."""
    rest, gap = leaf_geometry(size)
    _, t_max = SIZES[size]
    part = box(x0, x1, CH_Y0, -LP, -OL_H, CLIP_T)
    for c0, c1 in clips:
        part += box(c0, c1, CH_Y0, gap + OL_T, 0, CLIP_T)          # Top bar
        part += box(c0, c1, gap, gap + OL_T, -OL_H, CLIP_T)        # Outer leg
    for c0, c1 in clips:
        part -= box(c0 + BRIDGE_W, c1 - BRIDGE_W, -LP, gap, -1, CLIP_T + 1)
    for c0, c1 in clips:
        for xr, sense in leaf_roots(c0, c1):
            part += xy_prism(leaf_outline(xr, sense, size), -OL_H, CLIP_T)
    if tongue:
        part += box(x1 - 0.5, x1 + TONGUE["l"], *TONGUE["y"], *TONGUE["z"])

    cuts = box(x0 - 1, x1 + 1, CH_Y0 - 1, CH_Y0 + CH_D, CH_Z0, CH_Z1)              # LED and wire channel
    cuts += yz_prism(groove_outline(), x0 - 1, x1 - 1.0)                          # Liner groove, open at the back
    ramp = [(t_max + 0.5, -OL_H - 1), (t_max + 0.5, -OL_H), (0.2, -OL_H + (t_max + 0.3) * RAMP), (0.2, -OL_H - 1)]
    for c0, c1 in clips:
        cuts += yz_prism(ramp, c0 + BRIDGE_W, c1 - BRIDGE_W)
    part -= cuts
    for x in lip_positions(x0, x1):
        for z0, z1 in ((CH_Z0 - 0.3, CH_Z0 + LIP), (CH_Z1 - LIP, CH_Z1 + 0.3)):
            part += box(x - LIP_L / 2, x + LIP_L / 2, CH_Y0, CH_Y0 + LIP_T, z0, z1)
    return part


def liner(length):
    """Soft-flex bar: a dovetail rib in the groove and a pad standing proud to the temple face."""
    rib = yz_prism(groove_outline(LINER_CLEAR), 0, length)
    pad = box(0, length, -LP, 0, GROOVE_Z[0] + LINER_CLEAR, GROOVE_Z[1] - LINER_CLEAR)
    return rib + pad


# ================================================================ corner
def bend_centre():
    """(x, y) of the corner's bend axis."""
    return RAIL_X1 + TONGUE["l"], (CH_Y0 + CH_D / 2) - CORNER_R


def on_flap(shape, angle=CORNER_ANGLE):
    """Something modelled straight on past the bend's end (x > the bend's start), carried round
    onto the flap of a corner bent to angle."""
    xc, yc = bend_centre()
    return Pos(xc, yc, 0) * (Rot(0, 0, -angle) * (Pos(-xc, -yc, 0) * shape))


def led_path():
    """Path length of each LED along the strip from the rail's front face, rear LED first."""
    s_first_flap = TONGUE["l"] + CORNER_R * math.pi / 2 + FLAP_LED_D
    s0 = s_first_flap - (LEDS - LEDS_ON_FLAP) * gm.LED_PITCH
    return [s0 + i * gm.LED_PITCH for i in range(LEDS)]


def led_points(angle=90.0):
    """(x, y) of each LED on the strip's centre line, with the corner bent to angle."""
    xc, yc = bend_centre()
    a = math.radians(angle)
    pts = []
    for s in led_path():
        if s <= TONGUE["l"]:
            pts.append((RAIL_X1 + s, yc + CORNER_R))
        elif s <= TONGUE["l"] + CORNER_R * a:
            th = (s - TONGUE["l"]) / CORNER_R
            pts.append((xc + CORNER_R * math.sin(th), yc + CORNER_R * math.cos(th)))
        else:
            d = s - TONGUE["l"] - CORNER_R * a
            pts.append((xc + CORNER_R * math.sin(a) + d * math.cos(a), yc + CORNER_R * math.cos(a) - d * math.sin(a)))
    return pts


def corner(angle=CORNER_ANGLE):
    """Soft-flex corner: a straight sleeve over the rail's tongue, a bend toward the head side
    about a vertical axis, and a straight flap against the frame front. The same section all
    along: channel open on the concave (head) side. The tongue slot is open at the top only,
    so the left corner is a mirrored part, not this one flipped over."""
    tl = TONGUE["l"]
    z0, z1 = CORNER_Z
    yc = (CH_Y0 + CH_D / 2) - CORNER_R          # Bend centre, on the head side
    xc = RAIL_X1 + tl
    a = math.radians(angle)

    def section_ring(y_lo, y_hi, za, zb):
        """Solid for the band y_lo..y_hi (rail-side offsets), za..zb: straight, bent, straight."""
        s = box(RAIL_X1, xc, y_lo, y_hi, za, zb)
        r_in, r_out = y_lo - yc, y_hi - yc
        n = 24
        pts = [(xc + r_out * math.sin(a * i / n), yc + r_out * math.cos(a * i / n)) for i in range(n + 1)]
        pts += [(xc + r_in * math.sin(a * i / n), yc + r_in * math.cos(a * i / n)) for i in range(n, -1, -1)]
        s += xy_prism(pts, za, zb)
        # Flap: straight on from the bend's end, along the bent direction
        dx, dy = -math.sin(a - math.pi / 2), -math.cos(a - math.pi / 2)   # Tangent at the bend's end
        ox, oy = math.sin(a), math.cos(a)                                 # Outward normal there
        e = (xc, yc)
        q = [(e[0] + ox * r_in, e[1] + oy * r_in), (e[0] + ox * r_out, e[1] + oy * r_out)]
        flap = [q[0], q[1], (q[1][0] + dx * CORNER_FLAP, q[1][1] + dy * CORNER_FLAP),
                (q[0][0] + dx * CORNER_FLAP, q[0][1] + dy * CORNER_FLAP)]
        s += xy_prism(flap, za, zb)
        return s

    part = section_ring(CH_Y0, 0.0, z0, z1)
    part -= section_ring(CH_Y0 - 1, CH_Y0 + CH_D, CH_Z0, CH_Z1)      # Channel
    slot_y = (TONGUE["y"][0] + SLOT_CLEAR, TONGUE["y"][1] - SLOT_CLEAR)
    part -= box(RAIL_X1 - 1, xc + 0.2, *slot_y, TONGUE["z"][0], z1 + 1)  # Tongue slot, open at the back and top
    # Lips over the channel mouth, on the flap and on the sleeve over the tongue
    for xa in (RAIL_X1 + 1.5,):
        for za, zb in ((CH_Z0 - 0.3, CH_Z0 + LIP), (CH_Z1 - LIP, CH_Z1 + 0.3)):
            part += box(xa, xa + LIP_L, CH_Y0, CH_Y0 + LIP_T, za, zb)
    for d in FLAP_LIPS:
        for za, zb in ((CH_Z0 - 0.3, CH_Z0 + LIP), (CH_Z1 - LIP, CH_Z1 + 0.3)):
            lip = box(xc + d - LIP_L / 2, xc + d + LIP_L / 2, CH_Y0, CH_Y0 + LIP_T, za, zb)
            part += on_flap(lip, angle)
    return part


# ================================================================ diffuser
DIFF_T = 0.8         # Cover thickness. Print in natural (translucent) PETG
DIFF_GAP = 1.5       # Air between the channel mouth and the cover, so the LEDs blur into a line
DIFF_X = (RAIL_X1 + min(led_path()) - 4.0, RAIL_X1 - 0.2)   # Over the six rail LEDs
DIFF_HOOK = 0.8      # How far the hooks reach over the rail's top and bottom edges
DIFF_CLEAR = 0.05


def diffuser():
    """Snap-on cover over the rail's LED channel: a plate standing off the head-side face, with
    hooks over the rail's top and bottom edges. Fit it after the strip is in."""
    x0, x1 = DIFF_X
    yp0, yp1 = CH_Y0 - DIFF_GAP - DIFF_T, CH_Y0 - DIFF_GAP
    zt, zb = CLIP_T + DIFF_CLEAR, -OL_H - DIFF_CLEAR
    part = box(x0, x1, yp0, yp1, zb - DIFF_T, zt + DIFF_T)                        # Plate
    for z0, z1 in ((zt, zt + DIFF_T), (zb - DIFF_T, zb)):
        part += box(x0, x1, yp0, CH_Y0 + DIFF_HOOK, z0, z1)                       # Hooks
    return part


# ================================================================ corner caps
# The corner LEDs are the ones in direct view, so they get diffusers too: a short natural-PETG
# cap on the corner's straight part (over the hinge LED) and a long one along its flap (over
# the three flap LEDs), with the bend left open between them so the corner can still bend when
# the glasses fold. Each hooks over the corner's top and bottom edges like the rail diffuser.
# Both are symmetric top to bottom, so they fit either side (turned over).
CAP_HINGE_L = 5.6
CAP_FLAP_L = CORNER_FLAP - 1.0
CAP_FLAP_D = 0.2     # Flap cap starts this far along the flap from the bend's end


def corner_cap(length, x0=0.0):
    """A cap, in the corner's straight-part coordinates, from x0 to x0 + length."""
    x1 = x0 + length
    z0, z1 = CORNER_Z
    yp0, yp1 = CH_Y0 - DIFF_GAP - DIFF_T, CH_Y0 - DIFF_GAP
    zt, zb = z1 + DIFF_CLEAR, z0 - DIFF_CLEAR
    part = box(x0, x1, yp0, yp1, zb - DIFF_T, zt + DIFF_T)
    for za, zc in ((zt, zt + DIFF_T), (zb - DIFF_T, zb)):
        part += box(x0, x1, yp0, CH_Y0 + DIFF_HOOK, za, zc)
    return part


def corner_caps(angle=CORNER_ANGLE):
    """(hinge cap, flap cap) placed on a corner bent to angle. The hinge cap ends 1 mm into the
    bend."""
    xc, _ = bend_centre()
    hinge = corner_cap(CAP_HINGE_L, xc + 1.0 - CAP_HINGE_L)
    flap = on_flap(corner_cap(CAP_FLAP_L, xc + CAP_FLAP_D), angle)
    return hinge, flap


# ================================================================ pods
# The pods clip onto the temple tips behind the ears. Same leaf idea as the rail, but the
# leaves sit below the tip, in the pod's plane, and push the tip up into the pod's top bar, so
# the pod adds no bulk sideways. The pod slides onto the tip from its end: the leaves lean
# toward the tip's end, so sliding on cams them down, and pulling off doesn't dig them in.
# Modelled in the same straight coordinates as the rail, with the ear bend not applied: the
# tip runs from x = -TEMPLE_STRAIGHT toward -x, inner face at y = 0. The functions below build
# each pod with the tip's top edge at z = 0 and the body below; worn_pod() flips it over so the
# body sits behind the tip (see there). The leaves then press the tip onto the bar under it.
# Sizes are set by the tip's height (the leaves) and thickness (the slot).
POD_SIZES = {"S": ((2.5, 3.3), (3.0, 4.3)), "M": ((3.3, 4.2), (4.3, 5.6)), "L": ((4.2, 5.2), (5.6, 7.0))}
POD_X1 = -gm.TEMPLE_STRAIGHT - 3.0   # Pod's front end, just past the ear bend
POD_L = 36.0
POD_WALL = 1.2
POD_TOP = 1.6        # Bar along the tip's top edge (unflipped), with a liner groove in its face
POD_LP = 0.6         # Bar face stands this far off the tip; the liner fills the gap
POD_GROOVE_Y = (0.3, 2.3)            # Liner groove across the bar face (fits the thinnest tip)
POD_LIP = 2.0        # Inner lip reaches this far down the tip's inner face
POD_Y0 = -POD_WALL   # Head-side face (the pod prints on it)
LID_T = 1.0          # Soft-flex lid over the cavity, on the outer face
LID_FIT = 0.05       # Lid is this much bigger than its recess, each side (soft, so it presses in)
XIAO = (17.8, 21.0, 1.0, 3.2)        # XIAO nRF52840 Plus: width, length, PCB, USB-C height (check yours)
USB_W = 9.2
BUTTON = 6.2         # Tactile button pocket (up to 6x6 mm), plunger out through the bottom
BATTERY = (34.0, 21.0, 5.6)          # 502030 cell with its protection board, plus clearance
ARM_W, ARM_T = 6.0, 1.8
ARM_OUT = 4.0        # MAX30101 arm runs this far past the tip's end ...
ARM_UP = 4.0         # ... then across to this far beyond the tip's top edge, where the cradle starts
MAX_BOARD = (22.5, 19.0, 1.6, 1.8)   # MAX30101 breakout: length, height, PCB, parts on the sensor side
CRADLE_RIM, CRADLE_LIP = 1.5, 0.8


def pod_leaf_geometry(size):
    """(rest, gap) for the pod leaves, measured down from the tip's top edge."""
    (h_min, _) = POD_SIZES[size][1]
    a = math.radians(LEAF_ANGLE)
    rest = h_min - PRELOAD
    return rest, rest + LEAF_L * math.cos(a) + LEAF_T / 2 * math.sin(a) - 0.5


def pod_groove(clear=0.0):
    """(y, z) dovetail outline of the pod liner's groove in the bar face; with clear > 0, of the
    liner's rib inside it."""
    y0, y1 = POD_GROOVE_Y
    f = GROOVE_FLARE
    return [(y0 + clear, POD_LP - 0.01), (y1 - clear, POD_LP - 0.01), (y1 + f - clear, POD_LP + GROOVE_D - clear),
            (y0 - f + clear, POD_LP + GROOVE_D - clear)]


def pod_liner():
    """Soft-flex bar in the pod's groove, standing proud to the tip's edge (z = 0, unflipped)."""
    xa, xb = POD_X1 - POD_L, POD_X1
    rib = yz_prism(pod_groove(LINER_CLEAR), xa, xb - 1.2)
    pad = box(xa, xb - 1.2, POD_GROOVE_Y[0] + LINER_CLEAR, POD_GROOVE_Y[1] - LINER_CLEAR, 0, POD_LP)
    return rib + pad


def pod_frame(size, depth):
    """Common pod geometry: (solid, cuts, dims). depth is the cavity depth needed (y)."""
    (_, t_max), _ = POD_SIZES[size]
    rest, gap = pod_leaf_geometry(size)
    slot = t_max + 0.3
    y1 = max(slot + 1.6, POD_Y0 + POD_WALL + depth + LID_T)   # Outer face
    xb, xa = POD_X1, POD_X1 - POD_L
    floor = -gap - POD_WALL
    top = POD_LP + POD_TOP
    part = box(xa, xb, POD_Y0, y1, POD_LP, top)                         # Bar the leaves press the tip onto
    part += box(xa, xb, POD_Y0, 0, -POD_LIP, top)                       # Inner lip
    part += box(xa, xb, slot, y1, floor, top)                           # Outer wall beside the tip
    part += box(xa, xb, POD_Y0, y1, floor, -gap)                        # Floor the leaves stand on
    a = math.radians(LEAF_ANGLE)
    d = (-math.sin(a), math.cos(a))
    n = (-d[1] * LEAF_T / 2, d[0] * LEAF_T / 2)
    for xr in (xb - 2.0, xb - 17.0):
        r = (xr, -gap - 0.5)
        t = (xr + d[0] * LEAF_L, -gap - 0.5 + d[1] * LEAF_L)
        outline = [(r[0] + n[0], r[1] + n[1]), (t[0] + n[0], t[1] + n[1]), (t[0] - n[0], t[1] - n[1]),
                   (r[0] - n[0], r[1] - n[1])]
        part += gm.xz_prism(outline, POD_Y0, slot - 0.4)
    part -= yz_prism(pod_groove(), xa - 1, xb - 1.0)                   # Liner groove, open at the tip end
    dims = dict(xa=xa, xb=xb, xm=(xa + xb) / 2, y1=y1, floor=floor, slot=slot, cy0=POD_Y0 + POD_WALL)
    return part, dims


def pod_body(dims, cav_h):
    """The box below the floor holding the cavity (cav_h tall); returns (solid, zb, zc1)."""
    zc1 = dims["floor"] - 1.0
    zb = zc1 - cav_h - POD_WALL
    return box(dims["xa"], dims["xb"], POD_Y0, dims["y1"], zb, dims["floor"] + 0.01), zb, zc1


def lid_outline(dims, zb, zc1, grow=0.0):
    return (dims["xa"] + 0.6 - grow, dims["xb"] - 0.6 + grow, zb + 0.6 - grow, zc1 + 0.6 + grow)


def board_pod(size):
    """Right pod: XIAO nRF52840 Plus with its USB-C out of the far end, the button beside it,
    the wires from the rail in through the front, and the MAX30101 arm out of the tip-end face
    near the tip (the earlobe is that way). Returns (pod, lid, arm, dims), unflipped."""
    w, length, pcb, usb_h = XIAO
    depth = pcb + usb_h + 0.4
    part, dims = pod_frame(size, depth)
    body, zb, zc1 = pod_body(dims, length + 0.2)
    part += body
    xa, xb, xm, y1, cy0 = dims["xa"], dims["xb"], dims["xm"], dims["y1"], dims["cy0"]
    cav_y = (cy0, y1 + 1)
    cz0 = zb + POD_WALL
    fx = (xm + w / 2, xb - POD_WALL)               # Front column: button, wires from the rail
    rx = (xa + POD_WALL, xm - w / 2)               # Rear column: arm root, cord
    cuts = box(xm - w / 2 - 0.2, xm + w / 2 + 0.2, *cav_y, cz0, zc1)                 # Board
    cuts += box(*fx, *cav_y, cz0, zc1)
    cuts += box(*rx, *cav_y, cz0, zc1)
    lx0, lx1, lz0, lz1 = lid_outline(dims, zb, zc1)
    cuts += box(lx0, lx1, y1 - LID_T, y1 + 1, lz0, lz1)                              # Lid recess
    usb_y = (cy0 + pcb - 0.2, cy0 + pcb + usb_h + 0.4)
    cuts += box(xm - USB_W / 2 - 0.2, xm + USB_W / 2 + 0.2, *usb_y, zb - 1, cz0 + 0.1)   # USB-C
    bx = (fx[0] + fx[1]) / 2
    cuts += box(bx - 1.6, bx + 1.6, cy0 + 0.5, cy0 + 3.7, zb - 1, cz0 + 0.1)         # Button plunger
    wy = (cy0 + 0.6, cy0 + 3.0)
    cuts += box(xb - POD_WALL - 1, xb + 1, *wy, zc1 - 2.6, zc1 - 0.4)                # Wires from the rail
    cx = (rx[0] + rx[1]) / 2
    cuts += box(cx - 1.4, cx + 1.4, *wy, zb - 1, cz0 + 0.1)                          # Cord, out of the far end
    arm_y = (y1 - LID_T - ARM_T - 0.4, y1 + 1)
    arm_z = (zc1 - 1.0 - ARM_W - 0.4, zc1 - 1.0)
    cuts += box(xa - 1, xa + POD_WALL + 0.1, *arm_y, *arm_z)                         # Arm slot, open to the lid side
    part -= cuts

    lid = box(*lid_outline(dims, zb, zc1, LID_FIT)[:2], y1 - LID_T, y1, *lid_outline(dims, zb, zc1, LID_FIT)[2:])
    rst = (xm - 5.0, cz0 + 2.5)                       # XIAO reset button, next to the USB-C (check yours)
    lid -= box(rst[0] - 0.6, rst[0] + 0.6, y1 - LID_T - 1, y1 + 1, rst[1] - 0.6, rst[1] + 0.6)

    # MAX30101 arm (soft flex), an L: a flange held inside the pod under the lid, a strap out
    # through the tip-end face past the end of the tip, then across toward the ear (above the
    # tip's top edge here; in front of the tip when worn), ending in a cradle that holds the
    # breakout with its sensor window outward, against the back of the earlobe. The cradle's
    # open end, where the board slides in, faces away from the strap. Strap, flange and cradle
    # are flush on their outer face, so it prints flat on it.
    ys = (arm_y[0] + 0.1, arm_y[0] + 0.1 + ARM_T)
    zs = (arm_z[0] + 0.2, arm_z[1] - 0.2)
    arm = box(rx[0] + 0.2, rx[0] + 3.2, ys[0] - 0.6, ys[1], zs[0] - 1.5, min(zs[1] + 0.8, zc1 - 0.1))  # Flange
    kx = xa - ARM_OUT                                                                       # The L's corner
    arm += box(kx - ARM_W, rx[0] + 0.5, *ys, *zs)                                           # Out past the tip end
    arm += box(kx - ARM_W, kx, *ys, zs[0], ARM_UP + 0.5)                                    # Across toward the ear
    bl, bh, bt, bf = MAX_BOARD
    hl, hh = bl / 2 + 0.2, bh / 2 + 0.2
    c_y1 = ys[1]
    c_y0 = c_y1 - CRADLE_LIP - bf - bt
    cxm = kx - ARM_W / 2
    c_z0 = ARM_UP
    czm = c_z0 + POD_WALL + hh
    arm += box(cxm - hl - POD_WALL, cxm + hl + POD_WALL, c_y0 - CRADLE_LIP, c_y1, c_z0, czm + hh + POD_WALL)
    arm -= box(cxm - hl, cxm + hl, c_y0, c_y1 - CRADLE_LIP, czm - hh, czm + hh + POD_WALL + 1)       # Board, in from the far end
    for ya, yb in ((c_y0 - CRADLE_LIP - 1, c_y0 + 0.01), (c_y1 - CRADLE_LIP - 0.01, c_y1 + 1)):
        arm -= box(cxm - hl + CRADLE_RIM, cxm + hl - CRADLE_RIM, ya, yb, czm - hh + CRADLE_RIM, czm + hh + POD_WALL + 1)
    arm -= box(cxm - 2.5, cxm + 2.5, c_y0, c_y1 - CRADLE_LIP, c_z0 - 1, czm - hh + 0.1)              # Wires along the strap
    dims.update(zb=zb, zc1=zc1)
    return part, lid, arm, dims


def worn_pod(p, left=False):
    """Pods are modelled with the tip's top edge at z = 0 and the body below it. Worn, the body
    must sit behind the tip, on the bone behind the ear, and the bar under the tip's bottom
    edge, so the pod is flipped over: mirrored in z and set under the reference tip. A left
    pod is also mirrored in y; the two mirrors together are a half turn about x (mirroring a
    mirrored solid twice leaves it broken)."""
    if left:
        return Pos(0, 0, -gm.REF_TIP[1]) * (Rot(180, 0, 0) * p)
    return Pos(0, 0, -gm.REF_TIP[1]) * mirror(p, Plane.XY)


def battery_pod(size):
    """Left pod (modelled on the right, then mirrored): the 502030 cell, and the junction where
    the cord meets the left strip's wires. Returns (pod, lid, dims)."""
    bw, bh, bd = BATTERY
    part, dims = pod_frame(size, bd)
    body, zb, zc1 = pod_body(dims, bh)
    part += body
    xa, xb, xm, y1, cy0 = dims["xa"], dims["xb"], dims["xm"], dims["y1"], dims["cy0"]
    cz0 = zb + POD_WALL
    cuts = box(xm - bw / 2, xm + bw / 2, cy0, y1 + 1, cz0, zc1)
    lx0, lx1, lz0, lz1 = lid_outline(dims, zb, zc1)
    cuts += box(lx0, lx1, y1 - LID_T, y1 + 1, lz0, lz1)
    wy = (cy0 + 0.6, cy0 + 3.0)
    cuts += box(xm + bw / 2 - 1, xb + 1, *wy, zc1 - 2.6, zc1 - 0.4)                # Left strip wires
    cuts += box(xa - 1, xm - bw / 2 + 1, *wy, cz0 + 6.5, cz0 + 9.0)                # Cord
    part -= cuts
    lid = box(*lid_outline(dims, zb, zc1, LID_FIT)[:2], y1 - LID_T, y1, *lid_outline(dims, zb, zc1, LID_FIT)[2:])
    dims.update(zb=zb, zc1=zc1)
    return part, lid, dims


# ================================================================ build
def print_orient_rail(p):
    """Top face (z = CLIP_T) down on the bed: leaves and outer legs stand up from it."""
    p = Rot(180, 0, 0) * p
    bb = p.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * p


def print_orient_flat(p):
    """Bottom face down (corner: standing on its end face; liner: rib up)."""
    bb = p.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * p


def print_orient_liner(p):
    p = Rot(90, 0, 0) * p                       # Pad face (y = 0) down
    bb = p.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * p


def _to_bed(p):
    bb = p.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * p


def print_orient_diffuser(p):
    return _to_bed(Rot(90, 0, 0) * p)           # Plate (head side) down, hooks up


def print_orient_pod(p):
    """Head-side face down: the leaves stand on the bed and the cavity opens upward. Works for
    the mirrored left pod too, whose head-side face is at +y."""
    bb = p.bounding_box()
    return _to_bed((Rot(90, 0, 0) if abs(bb.min.Y - POD_Y0) < 1e-6 else Rot(-90, 0, 0)) * p)


def print_orient_lid(p):
    return _to_bed(Rot(-90, 0, 0) * p)          # Outer face down


def test_clip(size):
    """One clip on a short length of rail, to try the grip before printing whole rails."""
    c0, c1 = CLIPS[0]
    return rail(size, x0=c0 - 3, x1=c1 + 3, clips=[(c0, c1)], tongue=False)


def build():
    parts = {}
    for s in SIZES:
        r = rail(s)
        parts[f"rail_right_{s}"] = (r, print_orient_rail(r))
        left = mirror(r, Plane.XZ)
        parts[f"rail_left_{s}"] = (left, print_orient_rail(left))
        t = test_clip(s)
        parts[f"test_clip_{s}"] = (t, print_orient_rail(t))
    ln = liner(CLIP_L - 2 * BRIDGE_W)
    parts["liner"] = (ln, print_orient_liner(ln))
    c = corner()
    parts["corner_right"] = (c, print_orient_flat(c))
    cl = mirror(c, Plane.XZ)
    parts["corner_left"] = (cl, print_orient_flat(cl))
    d = diffuser()
    parts["diffuser"] = (d, print_orient_diffuser(d))
    for name, length in (("hinge", CAP_HINGE_L), ("flap", CAP_FLAP_L)):
        cc = corner_cap(length)
        parts[f"corner_cap_{name}"] = (cc, print_orient_diffuser(cc))
    for s in POD_SIZES:
        pod, lid, arm, _ = (worn_pod(x) if not isinstance(x, dict) else x for x in board_pod(s))
        parts[f"pod_board_{s}"] = (pod, print_orient_pod(pod))
        bat, blid, _ = (worn_pod(x, left=True) if not isinstance(x, dict) else x for x in battery_pod(s))
        parts[f"pod_battery_{s}"] = (bat, print_orient_pod(bat))
        if s == "M":
            # The lids and liner are the same for every size. The arm's cross-piece is about
            # 1.3 mm shorter for S and longer for L; the soft arm takes that up.
            parts["lid_board"] = (lid, print_orient_lid(lid))
            parts["lid_battery"] = (blid, print_orient_lid(blid))
            parts["max_arm"] = (arm, print_orient_lid(arm))
            pl = pod_liner()
            parts["pod_liner"] = (pl, _to_bed(pl))
    return parts


if __name__ == "__main__":
    for s in SIZES:
        rest, gap = leaf_geometry(s)
        (s_lo, f_lo), (s_hi, f_hi) = leaf_check(s)
        print(f"{s}: temple {SIZES[s][0]}-{SIZES[s][1]} mm, leaf rest {rest:.2f}, outer leg at {gap:.2f}; "
              f"per leaf {f_lo:.1f}-{f_hi:.1f} N, stress {s_lo:.0f}-{s_hi:.0f} MPa")
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    for name, (model, printable) in build().items():
        export_step(model, str(OUT / "step" / f"{name}.step"))
        export_stl(printable, str(OUT / "stl" / f"{name}.stl"))
        print("wrote", name, f"{model.volume:.0f} mm3")
