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
  straight. It slides down onto a tongue on the rail's front end and carries the last two LEDs
  round the hinge. It bends further when the glasses fold.
- There is no neck or ear-end arch: the rail stops before the ear bend. The wires cross the
  bend loose to the pods, which clip onto the temple tips (pods to come).

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

# ---------------------------------------------------------------- corner (soft flex)
CORNER_ANGLE = 100.0     # As printed; the frame front holds it at about 90
CORNER_R = 3.0           # Bend radius at the strip
CORNER_FLAP = 10.0       # Straight part after the bend, against the frame front
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
def corner(angle=CORNER_ANGLE):
    """Soft-flex corner: a straight sleeve over the rail's tongue, a bend toward the head side
    about a vertical axis, and a straight flap against the frame front. The same section all
    along: channel open on the concave (head) side. Symmetric about its mid-height, so one
    part serves both sides (flipped over for the left)."""
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
    return part


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
    parts["corner"] = (c, print_orient_flat(c))
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
