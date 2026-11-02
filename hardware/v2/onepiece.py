"""
BreathSense v2, one-piece temple part: one PETG piece per side that clips onto the temple and
carries the whole 10-LED strip, unbroken, from the temple round the hinge corner onto the frame
front in one long rigid curve. The glasses can't fold while it's fitted, so the curve doesn't
have to bend. Shaped to one measured pair of glasses, not universal.

- The strip runs at top-rim height, so on the frame front it sits above the lens and blocks
  nothing you look through. It can't bend sideways within its own plane, so it stays at that
  height all the way along. That also takes it clear of the hinge knuckle.
- The strip slides into an enclosed slot from the rail's open back end, round the curve (it bends
  through its thickness, which it does easily); the slot's roof is part of the coloured body, so
  no light leaks out of the top. Each LED shines straight out through the slot's head-side wall,
  full 0.8 mm translucent PETG (two lines), which spreads the light so neighbouring LEDs blend.
- Two colours: a U round the slot along the whole LED run (translucent(): the head-side wall, the
  floor under the slot and a skin inside the temple-side wall, dovetailed into it) prints in
  translucent PETG, so light still spreads between the LEDs and the moving bars stay smooth; the
  rest (body()) in any colour chosen in the slicer. They're exported as a pair of STLs in the same place on the bed.
- Grip (grip="liner", the default): a rigid channel along the rail, open underneath: a top over
  the temple's top edge and a leg 4 mm down its outer face, lined on those two sides with a
  soft-flex L (liner()). The liner squeezes the temple onto the plate on its inner face, the
  same wedge as the pods' pockets. Push the part straight down onto the temple. No band, nothing
  round the LEDs.
- grip="band" (the earlier design, kept as a variant): a rigid hook over the top edge, and one
  soft-flex band, a closed loop just behind the last LED, right round the part and the temple,
  in grooves in the part. To fit: take the pod off, slide the band onto the temple over its tip,
  hook the part over the temple, then roll the band forward into its grooves.
- The PETG part has no springy features.
- The curve is a circular arc tangent to the temple's inner face and to the frame front's back
  face. A short straight run continues along the frame front.
- The pods clip onto the temple tips as before (mount_v2.py).

Prints on its top edge with no supports. The liner prints in soft flex on its top face; the band
flat on its end.

Coordinates, as worn on the RIGHT temple (the left part is mirrored): x forward, hinge pin at
x = 0; y outward, temple inner face at y = 0; z up, temple top edge at z = 0.

Run:  python onepiece.py   -> out/step/onepiece_*.step, out/stl/onepiece_*.stl (the band variant as
      onepiece_*_band_*)
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
WALL = 0.8               # Head-side wall: two 0.4 mm-nozzle lines, translucent over the LED run, not thinned
WALL_OUT = 1.6           # Temple-side wall: the band's backbone, so it carries the curve
SLOT_T = STRIP_T + 1.2   # Slot width (across the strip): a printed slot comes out 0.2-0.4 mm narrow, and the strip
                         # slides in along the whole closed slot
ZS0 = FRAME_TOP_Z - (STRIP_W + 0.4)   # Bottom of the slot: the strip's top edge sits level with the frame front's top
CLEAR = 0.15             # Fit clearance against the temple
HOOK_T = 1.6             # Top hook thickness over the temple's top edge
ZS1 = CLEAR + HOOK_T     # Top of the part (the print bed), and of the open slot
STRIP_TOP = ZS0 + STRIP_W + 0.2       # Where the strip's top edge sits in the slot
FLOOR = 0.8
BAND_T = WALL_OUT + SLOT_T + WALL     # Band thickness: temple-side wall, slot, head-side wall
END_T = 0.8              # Front end wall: the strip slides in until it stops against it
LED_END = 3.5            # Measured: front LED's centre from the strip's front end (its 2 mm LED starts ~2.5 mm along)
CLEAR_TAIL = 4.0         # The translucent piece starts this far behind the rear LED's centre

# ---------------------------------------------------------------- the curve
CURVE_R = 18.0           # Arc radius at the temple/frame faces. The strip turns 90 degrees round it
FRAME_RUN = 7.0          # Straight run along the frame front's back face after the arc
X_T = FRAME_BACK_X - CURVE_R          # Where the arc leaves the temple
ARC_L = CURVE_R * math.pi / 2

# ---------------------------------------------------------------- rail and grip
RAIL_X0 = -60.0          # Rail ends past the band behind the last LED; the wires run on along the temple to the pod
CATCH = 0.8              # Hooks reach this far down/up the temple's outer face ...
CATCH_T = 1.2            # ... with lips this thick
PLATE_T = BAND_T         # Lower plate thickness: flush with the band, one flat head-side face

# Soft-flex band: a closed loop round the whole cross-section (over the top, down the head-side
# face, under both bottom edges, up the temple's outer face and the hook's lip), just behind the
# last LED so it covers none. It sits in grooves in the part's top, the hook's lip and the
# plate's bottom edge, so it can't slide along. The head-side face has no groove: the LED wall
# there is only 0.8 mm. Where it crosses the temple itself it just lies on it.
CLIPS = (-56.0,)         # Band's centre: its front edge just behind the translucent piece (x -51.8)
CLIP_L = (6.0,)          # Band width along the temple
CLIP_ARM = 1.2           # Band thickness
CLIP_SQUEEZE = 0.3       # Band's inside this much smaller than what it goes round, every side (~7% stretch)
GROOVE = 0.5             # Groove depth in the part's top, the hook's lip and the plate's bottom edge
GROOVE_FIT = 0.1         # Groove this much wider than the band, each side


# Liner grip (grip="liner"): a soft-flex L on the temple's top and outer faces, in a rigid channel
LINER_T = 1.6            # Outer pad thickness: thick, so a temple a few tenths off the measurement still fits ...
LINER_TOP_T = 0.8        # ... top pad thickness (thinner: keeps the part low)
LINER_SQUEEZE = 0.45     # Outer pad's face this far inside the temple's outer face (one side lined, so all the squeeze
                         # is here): 28% of the pad, 9-47% for a temple 0.3 mm either side of the measurement
LINER_SQUEEZE_TOP = 0.1  # Top pad's face this far below the temple's top edge (gravity does most of it)
LINER_FIT = 0.05         # Liner this much bigger than its channel, so it presses in
LINER_D = 4.0            # Outer pad reaches this far down the temple's outer face
LEG_T = 1.2              # Rigid leg outside it (3 lines; PETG is ~80x stiffer than the flex, so still rigid next to it)
RETURN = 0.8             # Return at the leg's foot, under the liner's edge, so it can't drop out (its tip 0.3 mm clear of the temple) ...
RETURN_H = 1.1           # ... this tall, so its slope prints unsupported (54 degrees from the bed)
LINER_LEAD = 0.5         # Lead-in chamfer on the liner's bottom inside edge
STOP_L = 0.8             # Front end of the channel closed over the liner's section
ZS1_LINER = LINER_TOP_T - LINER_SQUEEZE_TOP + HOOK_T   # Top of the part with the liner
ROOF = 0.6               # The slot is closed over its top along its whole length (part of the coloured body), so no
                         # light leaks upward; the strip slides in from the rail's open back end ...



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
    """Path length of each LED's centre, rear first, with the strip pushed home against the front end
    wall. Path length is measured on the temple/frame face, but the strip runs down the slot's middle,
    nearer the arc's centre, so round the arc a mm of strip covers more than a mm of path."""
    k = (CURVE_R - (WALL_OUT + SLOT_T / 2)) / CURVE_R      # Strip length per path length on the arc
    end = S_FRONT - END_T
    run = end - ARC_L                                       # Straight run in front of the arc

    def s_of(d):                                            # Path length at d along the strip from its front end
        if d <= run:
            return end - d
        d -= run
        if d <= ARC_L * k:
            return ARC_L - d / k
        return -(d - ARC_L * k)
    return [s_of(LED_END + i * gm.LED_PITCH) for i in range(10)][::-1]


def clear_s0():
    """Path length where the translucent piece's LED run starts."""
    return led_path()[0] - CLEAR_TAIL


# ================================================================ the part
def leg_in(x):
    """Liner grip: y of the rigid leg's inner face (the liner's outer face, less its fit)."""
    return temple_t(x) - LINER_SQUEEZE + LINER_T - LINER_FIT


def part(rail_x0=RAIL_X0, grip="liner"):
    zs1 = ZS1_LINER if grip == "liner" else ZS1
    zb = ZS0 - FLOOR
    s_rear = rail_x0 - X_T
    # Band: temple-side wall, floor and head-side wall, from the rail's back end round to the frame
    p = band(s_rear, S_FRONT, 0, WALL_OUT, zb, zs1)
    p += band(s_rear, S_FRONT, WALL_OUT + SLOT_T, BAND_T, zb, zs1)
    p += band(s_rear, S_FRONT, 0, BAND_T, zb, ZS0)
    p += band(S_FRONT - END_T, S_FRONT, 0, BAND_T, zb, zs1)                      # Front end closed
    p += band(s_rear, S_FRONT, WALL_OUT - 0.01, WALL_OUT + SLOT_T + 0.01, zs1 - ROOF, zs1)   # Roof over the slot
    xa, xb = rail_x0, X_T
    if grip == "liner":
        # Channel: a top over the liner's top pad and a leg outside its outer pad, along the rail
        za = LINER_TOP_T - LINER_SQUEEZE_TOP + LINER_FIT        # Top's underside
        ya, yb = leg_in(xa), leg_in(xb)
        p += xy_prism([(xa, -WALL_OUT), (xb, -WALL_OUT), (xb, yb + LEG_T), (xa, ya + LEG_T)], za, zs1)
        p += xy_prism([(xa, ya), (xb, yb), (xb, yb + LEG_T), (xa, ya + LEG_T)], -LINER_D - RETURN_H, zs1)
        # Return at the leg's foot, in short steps along the temple's taper
        n = 8
        for i in range(n):
            x0, x1 = xa + (xb - xa) * i / n, xa + (xb - xa) * (i + 1) / n
            y = max(leg_in(x0), leg_in(x1))
            p += yz_prism([(y + 0.1, -LINER_D), (y - RETURN, -LINER_D - RETURN_H), (y + 0.1, -LINER_D - RETURN_H)], x0, x1)
        # Front stop over the liner's section (clear of the temple, which runs on to the hinge)
        x0 = xb - STOP_L
        p += xy_prism([(x0, -0.01), (xb, -0.01), (xb, yb), (x0, leg_in(x0))], CLEAR, za + 0.01)
        p += xy_prism([(x0, temple_t(x0) + CLEAR), (xb, temple_t(xb) + CLEAR), (xb, yb + 0.01), (x0, leg_in(x0) + 0.01)],
                      -LINER_D, za + 0.01)
    else:
        # Top hook over the temple's top edge (rigid), along the rail
        ya, yb = temple_t(xa) + CLEAR, temple_t(xb) + CLEAR
        p += xy_prism([(xa, -WALL_OUT), (xb, -WALL_OUT), (xb, yb + CATCH_T), (xa, ya + CATCH_T)], CLEAR, ZS1)
        p += xy_prism([(xa, ya), (xb, yb), (xb, yb + CATCH_T), (xa, ya + CATCH_T)], -CATCH, ZS1)

    # Lower plate on the temple's inner face, below the band, down to the bottom edge
    def bottom(x):
        return -temple_h(x) - CLEAR
    xs = [rail_x0 + (X_T - rail_x0) * i / 24 for i in range(25)]
    outline = [(x, zb + 0.01) for x in xs] + [(x, bottom(x)) for x in reversed(xs)]
    p += xz_prism(outline, -PLATE_T, 0.0)
    if grip == "liner":
        return p

    # Grooves for the soft-flex band (not in the head-side face)
    for xc, w in zip(CLIPS, CLIP_L):
        xa, xb = xc - w / 2 - GROOVE_FIT, xc + w / 2 + GROOVE_FIT
        yl = min(temple_t(xa), temple_t(xb)) + CLEAR + CATCH_T     # Lip's outer face
        zlow = min(bottom(xa), bottom(xb))
        p -= box(xa, xb, -PLATE_T - 1, yl + 1, ZS1 - GROOVE, ZS1 + 1)              # Top
        p -= box(xa, xb, yl - GROOVE, yl + 1, -CATCH - 1, ZS1 + 1)                  # Hook's lip
        p -= box(xa, xb, -PLATE_T - 1, 0.0, zlow - 1, max(bottom(xa), bottom(xb)) + GROOVE)   # Plate's bottom
    return p


def liner(rail_x0=RAIL_X0):
    """Soft-flex L for grip="liner", modelled in place: a top pad on the temple's top edge and an
    outer pad down its outer face, in the part's channel from the rail's back end to the front stop.
    Handed: this is the left one as modelled; the right is its mirror."""
    xa, xb = rail_x0, X_T - STOP_L
    z0 = -LINER_SQUEEZE_TOP                              # Top pad's face, on the temple
    z1 = LINER_TOP_T - LINER_SQUEEZE_TOP + LINER_FIT     # ... its top, in the channel
    def yin(x):
        return temple_t(x) - LINER_SQUEEZE
    def yout(x):
        return leg_in(x) + LINER_FIT
    top = xy_prism([(xa, 0.0), (xb, 0.0), (xb, yout(xb)), (xa, yout(xa))], z0, z1)
    outer = xy_prism([(xa, yin(xa)), (xb, yin(xb)), (xb, yout(xb)), (xa, yout(xa))], -LINER_D, z1)
    s = top + outer
    # Lead-in on the bottom inside edge, so the temple slides in past it (short steps along the taper)
    k, n = LINER_LEAD, 8
    for i in range(n):
        x0, x1 = xa + (xb - xa) * i / n, xa + (xb - xa) * (i + 1) / n
        y = min(yin(x0), yin(x1))
        s -= yz_prism([(y - 1, -LINER_D - 1), (y + k + 1, -LINER_D - 1), (y - 1, -LINER_D + k + 1)], x0 - 0.01, x1 + 0.01)
    return s


def print_orient_liner(s):
    """Top pad's top face down: the outer pad stands up from it."""
    s = Rot(180, 0, 0) * s
    bb = s.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * s


def clip(xc):
    """Soft-flex band for the clip position xc (the temple's thickness differs along its length),
    modelled in place: a closed loop round the part and the temple, in the part's grooves."""
    w = CLIP_L[CLIPS.index(xc)]
    x0, x1 = xc - w / 2, xc + w / 2
    sq, g = CLIP_SQUEEZE, GROOVE
    tt = max(temple_t(x0), temple_t(x1))          # Sized for the thicker, taller end of its span
    th = max(temple_h(x0), temple_h(x1))
    yh = -PLATE_T                                 # Head-side face (no groove)
    yl = tt + CLEAR + CATCH_T - g                 # Hook lip's outer face, in the groove
    zt = ZS1 - g                                  # Top of the part, in the groove
    zp = -th - CLEAR + g                          # Plate's bottom edge, in the groove
    inside = [(yh + sq, zt - sq), (yl - sq, zt - sq), (yl - sq, -CATCH),     # Over the top, down the lip
              (tt - sq, -CATCH), (tt - sq, -th + sq),                        # Down the temple's outer face
              (0.0, -th + sq), (0.0, zp + sq), (yh + sq, zp + sq)]           # Under the temple, then the plate
    a, c = CLIP_ARM, 1.0                          # Thickness; outside corner chamfer
    ya, yb, za, zc = yh + sq - a, yl - sq + a, -th + sq - a, zt - sq + a
    outside = [(ya + c, zc), (yb - c, zc), (yb, zc - c), (yb, za + c), (yb - c, za),
               (ya + c, za), (ya, za + c), (ya, zc - c)]
    return yz_prism(outside, x0, x1) - yz_prism(inside, x0 - 1, x1 + 1)


def print_orient_clip(c):
    """On its end: the loop flat on the bed."""
    c = Rot(0, 90, 0) * c
    bb = c.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * c


CLEAR_SKIN = 0.6         # Translucent skin on the inside of the temple-side wall (of its 1.6 mm)
KEY = ((0.2, 1.2), (0.2, 0.8))   # Dovetail key along that skin, into the coloured wall: (depth, half-height) steps,
                                 # widest deepest, so the translucent piece can't pull out toward the face


def clear_zone(grip="liner"):
    """The translucent region along the LED run, from 4 mm behind the rear LED to the front
    end, up to the roof: a U round the slot (the head-side wall, the floor under the slot, and a skin on the inside
    of the temple-side wall), so it's bonded along the whole height of the coloured wall, plus a
    dovetail key into that wall. One continuous piece, so the LEDs blend into each other."""
    zs1 = ZS1_LINER if grip == "liner" else ZS1
    zb = ZS0 - FLOOR
    s0, s1 = clear_s0(), S_FRONT + 0.01
    o_in = WALL_OUT - CLEAR_SKIN
    # Up to the roof's underside: the roof covers the U's top edges too
    z = band(s0, s1, o_in, BAND_T + 0.5, zb - 0.01, zs1 - ROOF)   # Past the outer face: the curve's facets differ
    zm = (zb + zs1) / 2
    o = o_in
    for depth, half in KEY[::-1]:                 # Narrow step first (next to the skin), widest deepest
        z += band(s0, s1, o - depth, o + 0.01, zm - half, zm + half)
        o -= depth
    return z


def translucent(p, grip="liner"):
    """The translucent piece of part p (as modelled: the left part; mirror both for the right)."""
    return p & clear_zone(grip)


def body(p, grip="liner"):
    """Part p less its translucent piece: any colour."""
    return p - clear_zone(grip)


def print_orient(p, ref=None):
    """Top edge down on the bed: the band, hook and plate stand up from it. ref: the whole part,
    so its body and translucent piece land in the same place."""
    ref = p if ref is None else ref
    bb = (Rot(180, 0, 0) * ref).bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * (Rot(180, 0, 0) * p)


if __name__ == "__main__":
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    # Modelled with y outward: in a right-handed frame with x forward and z up, that's the left
    # temple. The right one is its mirror (as assembly_onepiece.place() does).
    for grip, suffix in (("liner", ""), ("band", "_band")):
        l = part(grip=grip)
        r = mirror(l, Plane.XZ)
        for name, shape, mir in ((f"onepiece_right{suffix}", r, True), (f"onepiece_left{suffix}", l, False)):
            export_step(shape, str(OUT / "step" / f"{name}.step"))
            b, w = body(l, grip), translucent(l, grip)
            if mir:
                b, w = mirror(b, Plane.XZ), mirror(w, Plane.XZ)
            export_stl(print_orient(b, shape), str(OUT / "stl" / f"{name}_body_petg.stl"))
            export_stl(print_orient(w, shape), str(OUT / "stl" / f"{name}_translucent_petg.stl"))
            print("wrote", name, f"{shape.volume:.0f} mm3: body {b.volume:.0f}, translucent {w.volume:.0f} "
                  f"({len(w.solids())} piece)")
    ln = liner()
    for name, shape in (("onepiece_liner_right", mirror(ln, Plane.XZ)), ("onepiece_liner_left", ln)):
        export_step(shape, str(OUT / "step" / f"{name}.step"))
        export_stl(print_orient_liner(shape), str(OUT / "stl" / f"{name}_flex.stl"))
        print("wrote", name, f"{shape.volume:.0f} mm3")
    for xc in CLIPS:
        c = clip(xc)                             # A prism along x: the same part fits either side
        name = "onepiece_band"
        export_step(c, str(OUT / "step" / f"{name}.step"))
        export_stl(print_orient_clip(c), str(OUT / "stl" / f"{name}_flex.stl"))
        print("wrote", name, f"{c.volume:.0f} mm3")
    leds = led_path()
    on_curve = [s for s in leds if s > 0]
    print(f"LEDs on the curve and frame run: {len(on_curve)}; rail LEDs reach back to x = {X_T + leds[0]:.1f}")
