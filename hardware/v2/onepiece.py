"""
BreathSense v2, one-piece temple part: one PETG piece per side that clips onto the temple and
carries the whole 10-LED strip, unbroken, from the temple round the hinge corner onto the frame
front in one long rigid curve. The glasses can't fold while it's fitted, so the curve doesn't
have to bend. Shaped to one measured pair of glasses, not universal.

- The strip runs at top-rim height, so on the frame front it sits above the lens and blocks
  nothing you look through. It can't bend sideways within its own plane, so it stays at that
  height all the way along. That also takes it clear of the hinge knuckle.
- The strip drops into a slot that's open along its top edge, so it never has to be threaded
  through. Print it in translucent PETG: each LED shines straight out through the slot's
  head-side wall, thinned to a single-line skin in front of it.
- The rail hangs on the temple by a rigid hook over its top edge. Two soft-flex bands, closed
  loops, go right round the part and the temple and hold them together. Each sits in a shallow
  pocket so it can't slide, and being closed it can't spring off however soft the flex is. The
  PETG part has no springy features. To fit: take the pod off, slide both bands onto the temple
  over its tip, hook the part over the temple, then roll the bands forward into their pockets.
- The curve is a circular arc tangent to the temple's inner face and to the frame front's back
  face. A short straight run continues along the frame front.
- The pods clip onto the temple tips as before (mount_v2.py).

Prints on its top edge with no supports. The bands print in soft flex, flat on their ends.

Coordinates, as worn on the RIGHT temple (the left part is mirrored): x forward, hinge pin at
x = 0; y outward, temple inner face at y = 0; z up, temple top edge at z = 0.

Run:  python onepiece.py   -> out/step/onepiece_*.step, out/stl/onepiece_*.stl
"""

import math
import sys
from pathlib import Path

from build123d import Compound, Plane, Pos, Rot, export_step, export_stl, mirror

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
sys.path.insert(0, str(Path(__file__).parent))
import glasses_mount as gm   # noqa: E402
from glasses_mount import box, xy_prism, xz_prism, yz_prism   # noqa: E402

OUT = Path(__file__).parent / "out"

# ---------------------------------------------------------------- the glasses (measured)
FRAME_BACK_X = 4.8       # Frame front's back face, ahead of the hinge pin
PIN_Y = -2.2             # Hinge pin: inside the temple's inner face (the knuckle stands out on the head side)
KNUCKLE_R = 1.6          # Hinge knuckle radius (3.2 mm across)
KNUCKLE_Z = (-5.1, -1.4) # Hinge knuckle, from the temple's top edge (from a photo)
GUSSET_L = 6.0           # Hinge plate tapers back this far behind the pin (from a photo)
T_FRONT = (4.0, 8.1)     # Temple thickness, height, 5 mm behind the hinge
T_BEND = (3.2, 4.0)      # ... at the ear bend
BEND_X = -99.0
FRAME_TOP_Z = 1.0        # Frame front's top beside the hinge (from a photo)
LENS_TOP_Z = -4.5        # Where the lens starts below the frame front's top, near the corner (guess: measure)

# ---------------------------------------------------------------- strip and its slot
STRIP_W, STRIP_T = gm.STRIP_W, 1.2   # Strip width, and thickness including the LEDs
WALL = 0.8               # Head-side wall, thinned in front of each LED
WALL_OUT = 1.6           # Temple-side wall: the band's backbone, so it carries the curve
SLOT_T = STRIP_T + 0.4   # Slot width (across the strip)
ZS0 = FRAME_TOP_Z - (STRIP_W + 0.4)   # Bottom of the slot: the strip's top edge sits level with the frame front's top
CLEAR = 0.15             # Fit clearance against the temple
HOOK_T = 1.6             # Top hook thickness over the temple's top edge
ZS1 = CLEAR + HOOK_T     # Top of the part (the print bed), and of the open slot
STRIP_TOP = ZS0 + STRIP_W + 0.2       # Where the strip's top edge sits in the slot
FLOOR = 0.8
BAND_T = WALL_OUT + SLOT_T + WALL     # Band thickness: temple-side wall, slot, head-side wall
WINDOW_W = 3.4           # Thin patch of the head-side wall in front of each LED (along the strip) ...
WINDOW_EDGE = 0.7        # ... leaving full wall this much above and below it to hold the strip
SKIN = 0.45              # Wall left in front of each LED: one 0.4 mm-nozzle line of translucent PETG
TAB = 0.4                # Retaining tabs over the slot's open top edge: overhang ...
TAB_L, TAB_EVERY = 2.0, 2 * gm.LED_PITCH

# ---------------------------------------------------------------- the curve
CURVE_R = 18.0           # Arc radius at the temple/frame faces. The strip turns 90 degrees round it
FRAME_RUN = 7.0          # Straight run along the frame front's back face after the arc
X_T = FRAME_BACK_X - CURVE_R          # Where the arc leaves the temple
ARC_L = CURVE_R * math.pi / 2

# ---------------------------------------------------------------- rail and grip
RAIL_X0 = -54.0          # Rail ends just behind the last LED; the wires run on along the temple to the pod
CATCH = 0.8              # Hooks reach this far down/up the temple's outer face ...
CATCH_T = 1.2            # ... with lips this thick
PLATE_T = BAND_T         # Lower plate thickness: flush with the band, one flat head-side face

# Soft-flex bands: closed loops round the whole cross-section (over the top, down the head-side
# face, under both bottom edges, up the temple's outer face and the hook's lip). A rib on each
# band's inside sits in a shallow pocket in the lower plate, so it can't slide along.
CLIPS = (-25.1, -48.0)   # Between two LEDs, and behind the last one
CLIP_L = (3.0, 6.0)      # Band width along the temple: the front one fits in the 3.4 mm between two windows
CLIP_ARM = 1.4           # Band thickness
CLIP_UP = 2.5            # Pocket (and rib) height up the head-side face from the bottom edge
CLIP_SQUEEZE = 0.3       # Band's inside this much smaller than the part + temple on every side (~7% stretch)
POCKET = 0.5             # Pocket depth in the part's head-side face


def temple_t(x):
    """Temple thickness at x (linear between the two measurements)."""
    f = min(max((-5.0 - x) / (-5.0 - BEND_X), 0.0), 1.0)
    return T_FRONT[0] + (T_BEND[0] - T_FRONT[0]) * f


def temple_h(x):
    f = min(max((-5.0 - x) / (-5.0 - BEND_X), 0.0), 1.0)
    return T_FRONT[1] + (T_BEND[1] - T_FRONT[1]) * f


# ================================================================ the band (path)
def path_point(s, o):
    """Point on the band at path length s (0 where the arc leaves the temple; negative back along
    the rail) and offset o from the temple/frame face toward the head side (the arc's inside)."""
    if s <= 0:
        return (X_T + s, -o)
    if s <= ARC_L:
        phi = s / CURVE_R
        r = CURVE_R - o
        return (X_T + r * math.sin(phi), -CURVE_R + r * math.cos(phi))
    return (FRAME_BACK_X - o, -CURVE_R - (s - ARC_L))


def band_outline(s0, s1, o0, o1, n=48):
    """Plan outline of the band between path lengths s0..s1 and offsets o0..o1."""
    ss = [s0 + (s1 - s0) * i / n for i in range(n + 1)]
    # Keep the arc's ends as exact vertices
    ss = sorted(set(ss + [s for s in (0.0, ARC_L) if s0 < s < s1]))
    return [path_point(s, o0) for s in ss] + [path_point(s, o1) for s in reversed(ss)]


def band(s0, s1, o0, o1, z0, z1):
    return xy_prism(band_outline(s0, s1, o0, o1), z0, z1)


S_REAR = RAIL_X0 - X_T                 # Path length at the rail's back end (negative)
S_FRONT = ARC_L + FRAME_RUN            # ... at the frame run's end


def led_path():
    """Path length of each LED's centre, rear first: the front LED sits 3 mm from the band's front
    end, the rest at the strip's pitch behind it."""
    s_last = S_FRONT - 3.0
    return [s_last - (9 - i) * gm.LED_PITCH for i in range(10)]


def tab_positions(s_rear=None):
    """Retaining tabs between LEDs, along the whole band."""
    s_rear = S_REAR if s_rear is None else s_rear
    leds = led_path()
    xs = [(a + b) / 2 for a, b in zip(leds, leds[1:])]
    s = leds[0] - gm.LED_PITCH / 2
    while s > s_rear + 3:
        xs.append(s)
        s -= TAB_EVERY
    return xs


# ================================================================ the part
def part(rail_x0=RAIL_X0):
    zb = ZS0 - FLOOR
    s_rear = rail_x0 - X_T
    # Band: temple-side wall, floor and head-side wall, from the rail's back end round to the frame
    p = band(s_rear, S_FRONT, 0, WALL_OUT, zb, ZS1)
    p += band(s_rear, S_FRONT, WALL_OUT + SLOT_T, BAND_T, zb, ZS1)
    p += band(s_rear, S_FRONT, 0, BAND_T, zb, ZS0)
    p += band(S_FRONT - 0.8, S_FRONT, 0, BAND_T, zb, ZS1)                        # Front end closed
    for s in tab_positions(s_rear):
        p += band(s - TAB_L / 2, s + TAB_L / 2, WALL_OUT - 0.01, WALL_OUT + TAB, STRIP_TOP, ZS1)   # Down to the strip
    # Windows: the head-side wall thinned from the slot side in front of each LED, so the light
    # goes through a thin skin and the outside face stays smooth
    for s in led_path():
        p -= band(s - WINDOW_W / 2, s + WINDOW_W / 2, WALL_OUT + SLOT_T - 0.1, BAND_T - SKIN,
                  ZS0 + WINDOW_EDGE, STRIP_TOP + 0.2 - WINDOW_EDGE)

    # Top hook over the temple's top edge (rigid), along the rail
    xa, xb = rail_x0, X_T
    ya, yb = temple_t(xa) + CLEAR, temple_t(xb) + CLEAR
    p += xy_prism([(xa, -WALL_OUT), (xb, -WALL_OUT), (xb, yb + CATCH_T), (xa, ya + CATCH_T)], CLEAR, ZS1)
    p += xy_prism([(xa, ya), (xb, yb), (xb, yb + CATCH_T), (xa, ya + CATCH_T)], -CATCH, ZS1)

    # Lower plate on the temple's inner face, below the band, down to the bottom edge
    def bottom(x):
        return -temple_h(x) - CLEAR
    xs = [rail_x0 + (X_T - rail_x0) * i / 24 for i in range(25)]
    outline = [(x, zb + 0.01) for x in xs] + [(x, bottom(x)) for x in reversed(xs)]
    p += xz_prism(outline, -PLATE_T, 0.0)

    # Pockets locating the soft-flex bands
    for xc, w in zip(CLIPS, CLIP_L):
        p -= box(xc - w / 2 - 0.2, xc + w / 2 + 0.2, -PLATE_T - 1, -PLATE_T + POCKET,
                 bottom(xc) - 1, bottom(xc) + CLIP_UP + 0.3)
    return p


def clip(xc):
    """Soft-flex band for the clip position xc (the temple's thickness differs along its length),
    modelled in place: a closed loop round the part and the temple, with a rib inside its
    head-side arm for the pocket."""
    w = CLIP_L[CLIPS.index(xc)]
    x0, x1 = xc - w / 2, xc + w / 2
    sq = CLIP_SQUEEZE
    tt = max(temple_t(x0), temple_t(x1))          # Sized for the thicker, taller end of its span
    yh = -PLATE_T                                 # Head-side face
    yl = tt + CLEAR + CATCH_T                     # Hook lip's outer face
    zt = ZS1                                      # Top of the part
    zb = -max(temple_h(x0), temple_h(x1)) - CLEAR # Under both bottom edges
    zr = zb + CLIP_UP + 0.1                       # Top of the rib
    inside = [(yh + sq, zt - sq), (yl - sq, zt - sq), (yl - sq, -CATCH),     # Over the top, down the lip
              (tt - sq, -CATCH), (tt - sq, zb + sq),                         # Down the temple's outer face
              (yh + POCKET + sq, zb + sq), (yh + POCKET + sq, zr),           # Under, then the rib
              (yh + sq, zr + POCKET)]                                        # (sloped top: slides on)
    a, c = CLIP_ARM, 1.0                          # Thickness; outside corner chamfer
    ya, yb, za, zc = yh + sq - a, yl - sq + a, zb + sq - a, zt - sq + a
    outside = [(ya + c, zc), (yb - c, zc), (yb, zc - c), (yb, za + c), (yb - c, za),
               (ya + c, za), (ya, za + c), (ya, zc - c)]
    return yz_prism(outside, x0, x1) - yz_prism(inside, x0 - 1, x1 + 1)


def print_orient_clip(c):
    """On its end: the loop flat on the bed."""
    c = Rot(0, 90, 0) * c
    bb = c.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * c


def print_orient(p):
    """Top edge down on the bed: the band, hook and plate stand up from it."""
    p = Rot(180, 0, 0) * p
    bb = p.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * p


if __name__ == "__main__":
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    # Modelled with y outward: in a right-handed frame with x forward and z up, that's the left
    # temple. The right one is its mirror (as assembly_onepiece.place() does).
    l = part()
    r = mirror(l, Plane.XZ)
    for name, shape in (("onepiece_right", r), ("onepiece_left", l)):
        export_step(shape, str(OUT / "step" / f"{name}.step"))
        export_stl(print_orient(shape), str(OUT / "stl" / f"{name}_petg.stl"))
        print("wrote", name, f"{shape.volume:.0f} mm3")
    for i, xc in enumerate(CLIPS):
        c = clip(xc)                             # A prism along x: the same part fits either side
        name = f"onepiece_clip_{('front', 'rear')[i]}"
        export_step(c, str(OUT / "step" / f"{name}.step"))
        export_stl(print_orient_clip(c), str(OUT / "stl" / f"{name}_flex.stl"))
        print("wrote", name, f"{c.volume:.0f} mm3")
    leds = led_path()
    on_curve = [s for s in leds if s > 0]
    print(f"LEDs on the curve and frame run: {len(on_curve)}; rail LEDs reach back to x = {X_T + leds[0]:.1f}")
