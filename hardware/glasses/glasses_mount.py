"""
BreathSense glasses mount: parametric build123d model.

Parts:
  sleeve_right_ear / sleeve_left   TPU. Clip-on carrier for the 10-LED strip.
      An inner leg against the temple's head side holds the strip in an open
      channel (it presses in past short lips). Three clips and an ear-end arch
      push down over the temple from above: each is a top bar and an outer leg
      with two thin vertical leaves that spring against the temple's outer
      face, fitting temples 2-6 mm thick. The channel runs on round the glasses
      hinge to a front flap with the last 2 LEDs; a low neck takes the ear
      bend. One side carries the earlobe sensor arm.
  band_left / band_right           TPU. Band halves behind the head. The
      outer end presses over the sleeve stud (row of holes = size
      adjustment); the inner end presses over the center module's studs.
      band_left holds the battery; band_right is a plain strap.
  band_center                      TPU. Holds the ItsyBitsy tray (ItsyBitsy
      with the LiPo backpack stacked on it, and the power switch).
  tray_itsybitsy / tray_battery    PLA. Rigid snap-in trays.

Sleeve coordinates are as worn on the RIGHT temple: x forward (glasses hinge
at x=0), y outward (+y = away from the head), z up. Band coordinates: x
along the band, y across it (+y = up when worn), z out from the head.

The sleeve is modelled as printed: straight, flap and ear end in line with
the temple, standing on its top face (z = CLIP_T), which every sleeve
feature reaches. It bends into place when fitted.

Run:  python glasses_mount.py   -> out/step/*.step (as modelled), out/stl/*.stl (print orientation),
                                   out/all_parts.step (every part in one file, side by side),
                                   out/stl/test_sleeve_front.stl, test_sleeve_rear.stl (sleeve ends, to test-print first)
"""

import math
from pathlib import Path

from build123d import (
    Box, Compound, Cone, Cylinder, Location, Plane, Polyline, Pos, Rot, export_step, export_stl, extrude,
    make_face, mirror,
)

# ---------------------------------------------------------------- glasses the sleeve fits
T_W_MIN = 2.0        # Temple thickness range the leaves grip (y)
T_W_MAX = 6.0
# Reference glasses (measured), used only to place the sleeve in renders and fit checks.
# The sleeve itself is sized for the range above, not for these.
REF_T_FRONT = (4.0, 8.1)   # Temple thickness, height 5 mm behind the hinge
REF_T_BEND = (3.2, 4.0)    # ... at the start of the ear bend
REF_TIP = (3.5, 4.5)       # Tip thickness, height
TEMPLE_STRAIGHT = 99.0     # Hinge to the start of the ear bend
TIP_LEN = 39.0
TIP_ANGLE = 40.0           # Tip slopes down behind the ear, degrees below horizontal
SCREW_PROUD = 3.2          # Hinge screw head stands this far out of the temple's inner face

# ---------------------------------------------------------------- LED strip
STRIP_W = 4.0        # Strip width (measured: 4 mm strip, 2 mm LEDs down the middle)
STRIP_PCB = 0.6      # Strip PCB thickness
LED_PITCH = 6.8      # Measured: 10 LEDs over ~61 mm
LEDS_ON_TEMPLE = 8   # The other 2 of the 10 sit on the front flap
LEDS_ON_FLAP = 2

# ---------------------------------------------------------------- sleeve
# Sleeve coordinates, as worn on the RIGHT temple: x forward (glasses hinge at x=0), y outward,
# z up. The temple's inner face is at y=0 and its top edge at z=0. The model is the sleeve as
# printed: straight, with the front flap and the ear end in line with the temple. They bend into
# place when fitted (at the corner and the neck).
WALL = 1.2           # TPU wall (sensor pod)
CLIP_T = 1.6         # Top bar thickness. Prints on its top face, so every sleeve feature reaches z = CLIP_T
OL_T = 1.6           # Outer leg thickness
OL_H = 9.0           # Outer leg reaches this far below the temple's top edge
LEAF_T = 1.0         # Leaves: thin vertical springs angled off the outer leg toward the temple
LEAF_ANGLE = 45.0    # Leaf angle from straight across (toward the temple)
LEAF_REST = T_W_MIN - 0.5   # Unloaded, the leaf tips reach this close to the temple's inner face
GAP = T_W_MAX + LEAF_T + 0.3  # Inner face of the outer leg: room for the thickest temple with a leaf folded flat
RAMP = 1.0           # Leaf bottom edges slope up toward the tips (dz/dy), so pushing down opens them
CLIP_N = 3           # Clips along the temple
CLIP_L = 23.0
CLIP_GAP = 5.5
CLIP_FRONT = 6.0     # Front clip starts this far behind the hinge, clear of the hinge screw
BRIDGE_W = 2.0       # Top bar left at each clip end; between them the leaves stand free
CORNER_X1 = -1.2     # Channel bends round the glasses hinge between x = -CLIP_FRONT and here: short
                     # enough to fit between two LEDs (6.8 pitch, 2 mm LEDs), so no LED sits in the bend
CORNER_FLOOR = 0.6   # Thinner channel floor round the corner
KERF = (0.8, 1.4)    # Slots across the channel walls round the corner: width, pitch
NECK_L = 20.0        # Bendy neck between the last clip and the ear-end arch: takes the ear bend
NECK_H = 3.0         # Neck height. Low, because the ear bend is in the plane of the inner leg
TIP_ARCH_L = 25.0    # Ear-end arch over the temple tip, open at its end
STUD_D = 3.0         # Band stud on the ear-end arch: shaft diameter
STUD_HEAD_D = 5.0
STUD_SHAFT = 2.4     # Shaft length (band thickness + clearance)

# Open LED channel in the inner leg's head-side face: the strip presses in past short lips
FLOOR = 1.0          # Channel floor (between the strip and the temple)
LIP = 0.7            # Lips cover this much of each strip edge, leaving a 2.6 mm window over the LEDs
LIP_T = 0.6          # Lip thickness
LIP_L = 2.5          # Lip length along the channel
LIP_EVERY = 2 * LED_PITCH
CH_W = STRIP_W + 0.4
CH_D = STRIP_PCB + 0.2 + LIP_T   # Channel depth: PCB, clearance, lip
WIRE_D = 1.0         # LED strip wire diameter incl. insulation (measure yours); 3 fit side by side in the channel
WIRE_N = 3

# ---------------------------------------------------------------- earlobe sensor arm
EAR_SIDE = "right"   # Which sleeve carries the sensor arm
ARM_W = 6.0          # Arm width (in the temple plane)
ARM_T = 1.8          # Arm thickness (y): thin so it flexes toward/away from the head
POD_DEPTH = 38.0     # Pod centre below the ear-end arch's top (behind the earlobe)
BOARD_L = 22.5       # Pimoroni MAX30101 breakout (check yours)
BOARD_H = 19.0
BOARD_T = 1.6
BOARD_FRONT = 1.8    # Component height on the sensor side
POD_RIM = 1.5        # Rims front and back hold the board; the sensor side is open to the skin
POD_LIP = 0.8        # Rim thickness
POD_DETENT = 0.3     # Bumps at the pod's open bottom edge that the board snaps past, so it can't drop out

# ---------------------------------------------------------------- band
BAND_H = 14.0        # Band height
BAND_T = 2.0         # Band thickness
BAND_HALF_LEN = 121.0  # Inner studs to the first outer hole. The band hangs loose behind the neck, like a
                       # neckband headset: 280-352 mm stud to stud across the holes
ADJ_HOLES = 7        # Size-adjustment holes at the outer end; cut off the tail beyond the one you use
ADJ_PITCH = 6.0
HOLE_D = 3.2         # Fits STUD_D; TPU stretches over the stud head
END_STUD_GAP = 9.0   # Two studs across the band at each center-module end
GROOVE = (4.0, 1.0)  # Wire groove in the band's outer face: width, depth
CHANNEL_RAIL = (1.0, 2.0)  # Rails beside the groove away from sockets: width, height. The channel
                           # (4.0 x 3.0) holds the right band's 7 wires at up to 1 mm, 3 rows deep
WIRE_PASS = (6.0, 3.0)     # Wire openings through tray and socket walls at the band: width, height
BRIDGE_EVERY = 18.0
BRIDGE_LEN = 4.0

# ---------------------------------------------------------------- electronics (estimates)
ITSYBITSY = (36.5, 18.0, 9.5)  # L, W, H: ItsyBitsy with the LiPo backpack on header spacers underneath
                               # (measured, header pins trimmed flush); USB on a short end
BATTERY = (32.5, 20.0, 5.5)    # 502030 200 mAh LiPo incl. its protection board, not counting its leads (measured)
BATTERY_LEAD = 4.0             # Room at the end of the battery tray for the leads to bend (they exit the cell's short end)
BATTERY_BAY = (BATTERY[0] + BATTERY_LEAD, BATTERY[1], BATTERY[2])
SWITCH = (10.5, 8.0, 5.5)      # Panel slide switch with its screw ears snipped off (measured): plate length
                               # (across the tray), depth behind the plate incl. pins (along it), plate width
SWITCH_SLOT = (8.0, 3.5)       # Lever slot: width (lever 3 thick + travel), height. The 7.5 mm lever sticks out ~4.3 mm
ITSY_BAY = (ITSYBITSY[0] + SWITCH[1] + 0.5, ITSYBITSY[1], max(ITSYBITSY[2], SWITCH[2]))  # Switch at the end away from the USB
TRAY_CLEAR = 0.3     # Per side
TRAY_WALL = 1.6      # PLA
TRAY_FLOOR = 1.2
RIDGE = 0.5          # Snap ridge on the tray, groove in the TPU socket
SOCKET_WALL = 1.6    # TPU
PORT_W = 12.0        # Port cut-out width (fits a micro-USB / USB-C plug body)

OUT = Path(__file__).parent / "out"


def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from min/max coordinates."""
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def y_cyl(x, z, y0, y1, d):
    """Cylinder along y from y0 to y1."""
    return Location((x, (y0 + y1) / 2, z), (90, 0, 0)) * Cylinder(d / 2, abs(y1 - y0))


# ================================================================ sleeve
IL_T = FLOOR + CH_D                   # Inner leg thickness: y from -IL_T (head side) to 0 (temple)
CH_Z1 = -0.2                          # LED channel, top ...
CH_Z0 = CH_Z1 - CH_W                  # ... and bottom
IL_Z0 = CH_Z0 - 1.2                   # Bottom of the inner leg
STRIP_ZC = (CH_Z0 + CH_Z1) / 2
TEMPLE_END = -CLIP_FRONT - CLIP_N * CLIP_L - (CLIP_N - 1) * CLIP_GAP   # Back of the last clip
TIP_X1 = TEMPLE_END - NECK_L          # Ear-end arch, front ...
TIP_X0 = TIP_X1 - TIP_ARCH_L          # ... and open end
LED_X = ([-CLIP_FRONT - 1.0 - LED_PITCH * (LEDS_ON_TEMPLE - 1 - i) for i in range(LEDS_ON_TEMPLE)]
         + [CORNER_X1 + 1.0 + LED_PITCH * i for i in range(LEDS_ON_FLAP)])   # LED centres, strip in place
FLAP_X1 = LED_X[-1] + LED_PITCH / 2 + 1.0
STUD_X = (TIP_X0 + TIP_X1) / 2
STUD_Z = CLIP_T - STUD_D / 2          # Shaft tangent to the print bed
ARM_X = TIP_X0 + ARM_W / 2            # Ear arm at the arch's open end


def clip_spans():
    """(x0, x1) of each clip along the temple, then the ear-end arch."""
    spans = []
    for k in range(CLIP_N):
        x1 = -CLIP_FRONT - k * (CLIP_L + CLIP_GAP)
        spans.append((x1 - CLIP_L, x1))
    return spans + [(TIP_X0, TIP_X1)]


def leaf_outline(xr, sense):
    """Plan (x, y) outline of a leaf rooted in the outer leg at x = xr, leaning toward +x (sense 1)
    or -x (sense -1), its tip reaching y = LEAF_REST."""
    a = math.radians(LEAF_ANGLE)
    d = (sense * math.sin(a), -math.cos(a))
    n = (-d[1] * LEAF_T / 2, d[0] * LEAF_T / 2)
    y_root = GAP + 0.5                   # Root buried in the outer leg
    length = (y_root - LEAF_REST - LEAF_T / 2 * math.sin(a)) / math.cos(a)
    r, t = (xr, y_root), (xr + d[0] * length, y_root + d[1] * length)
    return [(r[0] + n[0], r[1] + n[1]), (t[0] + n[0], t[1] + n[1]), (t[0] - n[0], t[1] - n[1]),
            (r[0] - n[0], r[1] - n[1])]


def leaf_roots(x0, x1):
    """Two leaves per clip, rooted just inside the end bridges and leaning toward each other,
    so each can fold flat along the outer leg without meeting the other."""
    c = BRIDGE_W + 0.8
    return [(x0 + c, 1), (x1 - c, -1)]


def ramp_outline():
    """(y, z) outline cut from under the leaves: their bottom edges rise toward the tips."""
    return [(GAP, -OL_H), (0.2, -OL_H + (GAP - 0.2) * RAMP), (0.2, -OL_H - 1), (GAP, -OL_H - 1)]


def lip_positions():
    """x of the channel lips: every LIP_EVERY along the strip and wire channel, none round the corner."""
    xs, x = [], FLAP_X1 - 3.0
    while x > TEMPLE_END + 2.0:
        if not -CLIP_FRONT - 1.5 < x < CORNER_X1 + 1.5:
            xs.append(x)
        x -= LIP_EVERY
    x = TIP_X1 - 3.0
    while x > TIP_X0 + 2.0:
        xs.append(x)
        x -= LIP_EVERY
    return xs


def kerf_positions():
    return [x for x in [-CLIP_FRONT + 0.6 + i * KERF[1] for i in range(20)] if x + KERF[0] <= CORNER_X1 - 0.6]


def xz_prism(pts, y0, y1):
    """Prism from an (x, z) outline, spanning y0..y1."""
    face = make_face(Polyline(*[(x, y0, z) for x, z in pts], close=True))
    return extrude(face, amount=y1 - y0, dir=(0, 1, 0))


def yz_prism(pts, x0, x1):
    """Prism from a (y, z) outline, spanning x0..x1."""
    face = make_face(Polyline(*[(x0, y, z) for y, z in pts], close=True))
    return extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def xy_prism(pts, z0, z1):
    """Prism from an (x, y) outline, spanning z0..z1."""
    face = make_face(Polyline(*[(x, y, z0) for x, y in pts], close=True))
    return extrude(face, amount=z1 - z0, dir=(0, 0, 1))


def sleeve(with_arm):
    """Inner leg carrying the open LED channel from the front flap to the ear end; three clips
    and the ear-end arch over the temple, each a top bar and an outer leg with two leaves; a
    low neck between the last clip and the arch."""
    # Inner leg: flap, corner and temple in one piece; the ear-end arch's own piece; the neck between
    part = box(TEMPLE_END, FLAP_X1, -IL_T, 0, IL_Z0, CLIP_T)
    part += box(TIP_X0, TIP_X1, -IL_T, 0, IL_Z0, CLIP_T)
    part += box(TIP_X1 - 0.5, TEMPLE_END + 0.5, -IL_T, 0, CLIP_T - NECK_H, CLIP_T)

    # Clips: top bar and outer leg. The top bar between the end bridges is removed so the leaves stand free
    spans = clip_spans()
    for x0, x1 in spans:
        part += box(x0, x1, -IL_T, GAP + OL_T, 0, CLIP_T)
        part += box(x0, x1, GAP, GAP + OL_T, -OL_H, CLIP_T)
    for x0, x1 in spans:
        part -= box(x0 + BRIDGE_W, x1 - BRIDGE_W, 0, GAP, -1, CLIP_T + 1)
    for x0, x1 in spans:
        for xr, sense in leaf_roots(x0, x1):
            part += xy_prism(leaf_outline(xr, sense), -OL_H, CLIP_T)

    # Band stud on the arch's outer leg, pointing out; flat on top (the print bed)
    y_out = GAP + OL_T
    part += y_cyl(STUD_X, STUD_Z, y_out - 0.2, y_out + STUD_SHAFT, STUD_D)
    part += Location((STUD_X, y_out + STUD_SHAFT - 0.01, STUD_Z), (-90, 0, 0)) * Cone(STUD_D / 2, STUD_HEAD_D / 2, 1.0, align=None)
    part += y_cyl(STUD_X, STUD_Z, y_out + STUD_SHAFT + 0.98, y_out + STUD_SHAFT + 1.8, STUD_HEAD_D)

    cuts = box(STUD_X - 4, STUD_X + 4, y_out, y_out + 6, CLIP_T, CLIP_T + 4)
    if with_arm:
        arm, arm_cuts = ear_arm()
        part += arm
        cuts += arm_cuts

    # Open channel in the head-side face, from the flap's tip to the neck, and along the arch
    cuts += box(TEMPLE_END - 1, FLAP_X1 + 1, -IL_T - 1, -IL_T + CH_D, CH_Z0, CH_Z1)
    cuts += box(TIP_X0 - 1, TIP_X1 + 1, -IL_T - 1, -IL_T + CH_D, CH_Z0, CH_Z1)
    # Corner: thinner floor, and slots across both channel walls so they close up as it bends
    cuts += box(-CLIP_FRONT, CORNER_X1, -(FLOOR - CORNER_FLOOR), 1, IL_Z0 - 1, CLIP_T + 1)
    for x in kerf_positions():
        cuts += box(x, x + KERF[0], -IL_T - 1, -FLOOR, IL_Z0 - 1, CH_Z0 + 0.01)
        cuts += box(x, x + KERF[0], -IL_T - 1, -FLOOR, CH_Z1 - 0.01, CLIP_T + 1)
    # Lead-in ramps under the leaves
    for x0, x1 in spans:
        cuts += yz_prism(ramp_outline(), x0 + BRIDGE_W, x1 - BRIDGE_W)
    part -= cuts

    # Lips at the channel mouth, and the pod's detents, added after the cavities are cut
    for x in lip_positions():
        for z0, z1 in ((CH_Z0 - 0.3, CH_Z0 + LIP), (CH_Z1 - LIP, CH_Z1 + 0.3)):
            part += box(x - LIP_L / 2, x + LIP_L / 2, -IL_T, -IL_T + LIP_T, z0, z1)
    if with_arm:
        part += pod_detents()
    return part


def ear_arm():
    """Flexible arm hanging from the ear-end arch's inner leg down to a pod holding the MAX30101
    against the back of the earlobe. Returns (solid, cavity). The board slides in from below; the
    pod's openings run out through its bottom edge, and the gusset widens at 45 degrees in both
    directions, so it prints standing up without supports."""
    px, pz = ARM_X, -POD_DEPTH
    y0 = -IL_T
    y1 = y0 + POD_LIP + BOARD_T + BOARD_FRONT + POD_LIP
    hl, hh = BOARD_L / 2 + 0.2, BOARD_H / 2 + 0.2
    top = pz + hh + WALL
    pw = hl + WALL
    zg = top + pw - ARM_W / 2                          # Top of the gusset
    dy = y1 - y0 - ARM_T
    arm = box(px - ARM_W / 2, px + ARM_W / 2, y0, y0 + ARM_T, zg - 0.5, IL_Z0 + 0.5)
    g = [(px - ARM_W / 2, zg), (px + ARM_W / 2, zg), (px + pw, top - 0.5), (px - pw, top - 0.5)]
    arm += xz_prism(g, y0, y1)
    arm += yz_prism([(y0 + ARM_T - 0.01, zg - 0.01), (y1, zg - 0.01), (y0 + ARM_T - 0.01, zg + dy)],
                    px - ARM_W / 2, px + ARM_W / 2)    # Thickens the arm into the gusset at 45 degrees
    pod = box(px - pw, px + pw, y0, y1, pz - hh - WALL, top)
    cut = box(px - hl, px + hl, y0 + POD_LIP, y1 - POD_LIP, pz - hh - WALL - 1, pz + hh)    # board space
    for ya, yb in ((y0 - 1, y0 + POD_LIP + 0.01), (y1 - POD_LIP - 0.01, y1 + 1)):          # rim openings
        cut += box(px - hl + POD_RIM, px + hl - POD_RIM, ya, yb, pz - hh - WALL - 1, pz + hh - POD_RIM)
    cut += box(px + hl - 0.1, px + pw + 1, y0 + POD_LIP, y1 - POD_LIP, pz + hh - 6, pz + hh)  # wire exit, front end
    return arm + pod, cut


def pod_detents():
    """Bumps on the front rim's two side strips, below where the board's bottom edge sits."""
    px, pz = ARM_X, -POD_DEPTH
    y1 = -IL_T + POD_LIP + BOARD_T + BOARD_FRONT + POD_LIP
    hl, hh = BOARD_L / 2 + 0.2, BOARD_H / 2 + 0.2
    d = None
    for xa, xb in ((px - hl - 0.3, px - hl + POD_RIM), (px + hl - POD_RIM, px + hl + 0.3)):
        b = box(xa, xb, y1 - POD_LIP - POD_DETENT, y1 - POD_LIP + 0.3, pz - hh - WALL, pz - hh - 0.2)
        d = b if d is None else d + b
    return d


# ================================================================ trays and sockets
def tray_outer(comp):
    l, w, h = comp
    return (l + 2 * (TRAY_CLEAR + TRAY_WALL), w + 2 * (TRAY_CLEAR + TRAY_WALL), h + TRAY_CLEAR + TRAY_FLOOR)


def tray(comp, port=True, switch=False, wire_exit="sides"):
    """PLA tray, floor at z=0, open top (the open side faces the band). Snap ridge round the outside.
    With switch, the -x end wall has a slot for the slide switch's actuator. Wires leave at the rim
    through openings in the middle of both long sides, or in the -x end wall (wire_exit="end")."""
    l, w, h = comp
    ol, ow, oh = tray_outer(comp)
    t = box(-ol / 2, ol / 2, -ow / 2, ow / 2, 0, oh)
    rz = oh - 1.5
    t += box(-ol / 2 - RIDGE, ol / 2 + RIDGE, -ow / 2 + 2, ow / 2 - 2, rz - 0.5, rz + 0.5)
    t += box(-ol / 2 + 2, ol / 2 - 2, -ow / 2 - RIDGE, ow / 2 + RIDGE, rz - 0.5, rz + 0.5)
    t -= box(-ol / 2 + TRAY_WALL, ol / 2 - TRAY_WALL, -ow / 2 + TRAY_WALL, ow / 2 - TRAY_WALL, TRAY_FLOOR, oh + 1)
    if port:      # Port on the +x short end
        t -= box(ol / 2 - TRAY_WALL - 1, ol / 2 + RIDGE + 1, -PORT_W / 2, PORT_W / 2, TRAY_FLOOR, oh + 1)
    if switch:
        t -= switch_slot(-ol / 2, TRAY_FLOOR + SWITCH[2] / 2)
    pw, ph = WIRE_PASS
    if wire_exit == "sides":
        t -= box(-pw / 2, pw / 2, -ow / 2 - RIDGE - 1, ow / 2 + RIDGE + 1, oh - ph, oh + 1)
    else:
        t -= box(-ol / 2 - RIDGE - 1, -ol / 2 + TRAY_WALL + 1, -pw / 2, pw / 2, oh - ph, oh + 1)
    return t


def switch_slot(x_wall, zc):
    """Actuator slot through an end wall whose inner face is near x_wall (the -x end), centred at height zc."""
    w, h = SWITCH_SLOT
    return box(x_wall - SOCKET_WALL - 1, x_wall + TRAY_WALL + 1, -w / 2, w / 2, zc - h / 2, zc + h / 2)


def socket(comp, port=True, switch=False, wire_exit="sides"):
    """TPU socket in tray coordinates (band surface at z=0, rising in +z), with wire openings
    matching the tray's. Returns (shape, length along tray x, width along tray y)."""
    ol, ow, oh = tray_outer(comp)
    sl, sw = ol + 2 * SOCKET_WALL, ow + 2 * SOCKET_WALL
    s = box(-sl / 2, sl / 2, -sw / 2, sw / 2, 0, oh)
    s -= box(-ol / 2, ol / 2, -ow / 2, ow / 2, -1, oh + 1)
    gz = 1.5   # Groove height above the band: the tray's ridge sits 1.5 below its rim
    s -= box(-ol / 2 - RIDGE, ol / 2 + RIDGE, -ow / 2 + 1.5, ow / 2 - 1.5, gz - 0.6, gz + 0.6)
    s -= box(-ol / 2 + 1.5, ol / 2 - 1.5, -ow / 2 - RIDGE, ow / 2 + RIDGE, gz - 0.6, gz + 0.6)
    if port:
        s -= box(ol / 2 - 1, sl / 2 + 1, -PORT_W / 2 - 0.5, PORT_W / 2 + 0.5, -1, oh + 1)
    if switch:   # The tray goes in upside down, so its slot height is measured from the top
        s -= switch_slot(-ol / 2, oh - (TRAY_FLOOR + SWITCH[2] / 2))
    pw, ph = WIRE_PASS
    if wire_exit == "sides":
        s -= box(-pw / 2, pw / 2, -sw / 2 - 1, sw / 2 + 1, -1, ph)
    else:
        s -= box(-sl / 2 - 1, -ol / 2 + 1, -pw / 2, pw / 2, -1, ph)
    return s, sl, sw


def port_down(shape):
    """Turn tray-coordinate geometry so the tray's +x end (the port) faces -y: down when worn."""
    return Rot(0, 0, -90) * shape


# ================================================================ band
def rails(x0, x1):
    """Rails each side of the groove on the band's outer face, bridged every BRIDGE_EVERY."""
    rw, rh = CHANNEL_RAIL
    g = GROOVE[0] / 2
    ch = box(x0, x1, g, g + rw, BAND_T - 0.01, BAND_T + rh) + box(x0, x1, -g - rw, -g, BAND_T - 0.01, BAND_T + rh)
    x = x0 + BRIDGE_EVERY / 2
    while x + BRIDGE_LEN < x1:
        ch += box(x, x + BRIDGE_LEN, -g - rw, g + rw, BAND_T + rh - 0.01, BAND_T + rh + 0.8)
        x += BRIDGE_EVERY
    return ch


def band_half(comp=None, port=False):
    """Flat band half: x along the band (inner end at x=0), y across it, z thickness.
    One electronics socket, or none for a plain strap; a board with a port is turned so the port
    faces down (-y). A plain strap still carries wires, so it keeps the groove and rails."""
    outer = BAND_HALF_LEN + (ADJ_HOLES - 1) * ADJ_PITCH + 6.0
    b = box(-6.0, outer, -BAND_H / 2, BAND_H / 2, 0, BAND_T)
    rails_from = 6.0                     # Clear of the center module's stud heads
    if comp is not None:
        sock, sl, sw = socket(comp, port, wire_exit="end")   # Wires leave toward the center module
        if port:
            sock, sl, sw = port_down(sock), sw, sl   # Port faces down; footprint now sl along x, sw along y
        cx = 8.0 + sl / 2
        b += box(cx - sl / 2, cx + sl / 2, -sw / 2, sw / 2, 0, BAND_T)   # Widen the band under the socket
        b += Pos(cx, 0, BAND_T - 0.01) * sock
        rails_from = cx + sl / 2
    b += rails(rails_from, BAND_HALF_LEN - 5)
    # Wire groove along the whole band, under the socket (the tray closes over it)
    b -= box(-7.0, BAND_HALF_LEN - 5, -GROOVE[0] / 2, GROOVE[0] / 2, BAND_T - GROOVE[1], BAND_T + 0.01)
    for yc in (-END_STUD_GAP / 2, END_STUD_GAP / 2):
        b -= Pos(0, yc, BAND_T / 2) * Cylinder(HOLE_D / 2, BAND_T + 2)
    for i in range(ADJ_HOLES):
        b -= Pos(BAND_HALF_LEN + i * ADJ_PITCH, 0, BAND_T / 2) * Cylinder(HOLE_D / 2, BAND_T + 2)
    return b


def band_center():
    """Center module: ItsyBitsy socket (USB facing down, switch slot facing up), two studs at each
    end for the band halves."""
    sock, sl, sw = socket(ITSY_BAY, port=True, switch=True)
    sock = port_down(sock)               # sw along x, sl along y
    stud_x = sw / 2 + 6.5                # Band ends (6 mm past their holes) clear the socket
    half = stud_x + 3.5
    h = max(sl, BAND_H)
    c = box(-half, half, -h / 2, h / 2, 0, BAND_T)
    c += Pos(0, 0, BAND_T - 0.01) * sock
    c -= box(-half - 1, half + 1, -GROOVE[0] / 2, GROOVE[0] / 2, BAND_T - GROOVE[1], BAND_T + 0.01)
    for xe in (-stud_x, stud_x):
        for yc in (-END_STUD_GAP / 2, END_STUD_GAP / 2):
            # Pieces overlap slightly: faces that only touch don't fuse into one solid
            c += Pos(xe, yc, BAND_T - 0.2 + (STUD_SHAFT + 0.2) / 2) * Cylinder(STUD_D / 2, STUD_SHAFT + 0.2)
            c += Pos(xe, yc, BAND_T + STUD_SHAFT - 0.01 + 0.5) * Cone(STUD_D / 2, STUD_HEAD_D / 2, 1.0)
            c += Pos(xe, yc, BAND_T + STUD_SHAFT + 0.98 + 0.4) * Cylinder(STUD_HEAD_D / 2, 0.8)
    return c


# ================================================================ build and export
def print_orient_sleeve(p):
    """Turn a sleeve over onto its top face (z = CLIP_T), the inner leg, outer legs and leaves standing up."""
    p = Rot(180, 0, 0) * p
    bb = p.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * p


def test_piece():
    """Front of the right sleeve for a test print: flap, corner and the front clip."""
    return sleeve(False) & box(-CLIP_FRONT - CLIP_L - 1.0, FLAP_X1 + 1, -20, 20, -20, 20)


def test_piece_rear():
    """Back of the right sleeve for a test print: last clip, neck and ear-end arch with the stud."""
    return sleeve(False) & box(TIP_X0 - 1, clip_spans()[CLIP_N - 1][1] + 1.0, -20, 20, -20, 20)


def build():
    right_arm = EAR_SIDE == "right"
    sleeve_r = sleeve(with_arm=right_arm)
    sleeve_l = mirror(sleeve(with_arm=not right_arm), Plane.XZ)
    return {
        f"sleeve_right{'_ear' if right_arm else ''}": (sleeve_r, print_orient_sleeve(sleeve_r)),
        f"sleeve_left{'' if right_arm else '_ear'}": (sleeve_l, print_orient_sleeve(sleeve_l)),
        "band_left": (band_half(BATTERY_BAY),) * 2,
        "band_right": (band_half(),) * 2,
        "band_center": (band_center(),) * 2,
        "tray_itsybitsy": (tray(ITSY_BAY, switch=True),) * 2,
        "tray_battery": (tray(BATTERY_BAY, port=False, wire_exit="end"),) * 2,
    }


def build_test():
    f, r = test_piece(), test_piece_rear()
    return {"test_sleeve_front": (f, print_orient_sleeve(f)), "test_sleeve_rear": (r, print_orient_sleeve(r))}


if __name__ == "__main__":
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    for old in list((OUT / "step").glob("*.step")) + list((OUT / "stl").glob("*.stl")):
        old.unlink()
    parts = build()
    tests = build_test()
    laid_out, y = [], 0.0
    for name, (model, printable) in parts.items():
        bb = model.bounding_box()
        laid_out.append(Pos(-bb.min.X, y - bb.min.Y, -bb.min.Z) * model)
        y += bb.size.Y + 10.0
    export_step(Compound(laid_out), str(OUT / "all_parts.step"))
    for name, (model, printable) in {**parts, **tests}.items():
        export_step(model, str(OUT / "step" / f"{name}.step"))
        export_stl(printable, str(OUT / "stl" / f"{name}.stl"))
        bb = printable.bounding_box()
        print(f"{name:18s} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:5.1f} mm  "
              f"vol {model.volume / 1000:5.2f} cm3  solids {len(model.solids())}")
