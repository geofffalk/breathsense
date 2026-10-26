"""
BreathSense glasses mount: parametric build123d model.

Parts:
  sleeve_right_ear / sleeve_left   TPU. The sock end slides over the temple
      tip like a glasses sock; the arch then lowers down over the temple from
      above (inverted U), with the 10-LED strip on its inner leg facing the
      head. The front flap (last 2 LEDs) folds inward onto the lens at a
      living hinge. One side carries the earlobe sensor arm.
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

Every sleeve feature reaches the same inner plane (y = BED), so the sleeve
prints flat on its inner face with the stud pointing up.

Run:  python glasses_mount.py   -> out/step/*.step (as modelled), out/stl/*.stl (print orientation),
                                   out/all_parts.step (every part in one file, side by side)
"""

import math
from pathlib import Path

from build123d import (
    Box, Compound, Cone, Cylinder, Location, Plane, Pos, Rot, export_step, export_stl, mirror,
)

# ---------------------------------------------------------------- glasses (standard adult)
T_W = 3.5            # Temple thickness (y), straight part
T_H = 6.0            # Temple height (z), straight part
TIP_W = 3.5          # Temple tip thickness (y)
TIP_H = 4.5          # Temple tip height (perpendicular to the tip, in x-z)
TEMPLE_STRAIGHT = 100.0  # Hinge to the start of the ear bend
TIP_ANGLE = 55.0     # Tip slopes down behind the ear, degrees below horizontal
FIT = 0.2            # TPU grip: openings this much smaller than the temple

# ---------------------------------------------------------------- LED strip
STRIP_W = 10.0       # Strip width
STRIP_PCB = 0.6      # Slot for the strip PCB (incl. clearance)
LED_PITCH = 6.5
LEDS_ON_TEMPLE = 8   # The other 2 of the 10 sit on the fold-in flap
LEDS_ON_FLAP = 2
LIP = 1.5            # Channel lips cover this much of each strip edge
LIP_T = 0.8          # Lip thickness

# ---------------------------------------------------------------- sleeve
WALL = 1.2           # TPU wall
ARCH_BACK = 95.0     # Arch runs from x=-ARCH_BACK ...
ARCH_FRONT = 3.0     # ... to x=-ARCH_FRONT (clear of the glasses hinge)
OUTER_LEG = 3.0      # How far the outer leg reaches down the temple's outer face (longer needs print supports)
NUB = 0.4            # Retaining nub at the foot of the outer leg
SOCK_START = 5.0     # Sock covers the tip from this far along it ...
SOCK_END = 37.0      # ... to here (closed end; wires exit through it)
HINGE_LEN = 4.0      # Living hinge before the flap
HINGE_T = 0.8        # Living hinge web thickness
STUD_AT = 25.0       # Band stud position along the tip
STUD_D = 3.0         # Stud shaft diameter
STUD_HEAD_D = 5.0
STUD_SHAFT = 2.4     # Shaft length (band thickness + clearance)
TUNNEL = (1.4, 3.0)  # Wire tunnel inside the inner wall: (y, height)

# ---------------------------------------------------------------- earlobe sensor arm
EAR_SIDE = "right"   # Which sleeve carries the sensor arm
ARM_W = 6.0          # Arm width (in the temple plane)
ARM_T = 1.8          # Arm thickness (y): thin so it flexes toward/away from the head
ARM_TO = (-100.0, -52.0)  # (x, z) of the sensor pod centre: ~behind the earlobe
BOARD_L = 22.5       # Pimoroni MAX30101 breakout (check yours)
BOARD_H = 19.0
BOARD_T = 1.6
BOARD_FRONT = 1.8    # Component height on the sensor side
POD_RIM = 1.5        # Rims front and back hold the board; the sensor side is open to the skin
POD_LIP = 0.8        # Rim thickness

# ---------------------------------------------------------------- band
BAND_H = 14.0        # Band height
BAND_T = 2.0         # Band thickness
BAND_HALF_LEN = 94.0 # Inner studs to the first outer hole
ADJ_HOLES = 5        # Size-adjustment holes at the outer end
ADJ_PITCH = 6.0
HOLE_D = 3.2         # Fits STUD_D; TPU stretches over the stud head
END_STUD_GAP = 9.0   # Two studs across the band at each center-module end
GROOVE = (3.2, 1.0)  # Wire groove in the band's outer face: width, depth
CHANNEL_RAIL = (1.0, 1.6)  # Rails beside the groove away from sockets: width, height
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
SWITCH_SLOT = (8.0, 3.5)       # Slot the lever sweeps (7.5 x 3 measured, plus clearance): width (slide direction), height
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
Y_PCB = -T_W / 2 - WALL               # Strip PCB back sits against the inner leg here
BED = Y_PCB - STRIP_PCB - LIP_T       # Inner plane every sleeve feature reaches (print bed)
ARCH_TOP = T_H / 2 + WALL             # Top of the arch
CH_Z1 = ARCH_TOP                      # LED channel: top flush with the arch ...
CH_Z0 = ARCH_TOP - (STRIP_W + 0.4 + 2 * WALL)  # ... hanging below the temple
STRIP_ZC = (CH_Z0 + CH_Z1) / 2
TIP_DIR = (-math.cos(math.radians(TIP_ANGLE)), 0.0, -math.sin(math.radians(TIP_ANGLE)))
P0 = (-TEMPLE_STRAIGHT, 0.0, 0.0)     # Where the tip bends down


def tip_loc(s):
    """Location s mm along the temple tip, local x pointing along the tip."""
    return Location((P0[0] + TIP_DIR[0] * s, 0.0, P0[2] + TIP_DIR[2] * s), (0, 180 - TIP_ANGLE, 0))


def tip_point(s):
    return (P0[0] + TIP_DIR[0] * s, P0[2] + TIP_DIR[2] * s)


def led_channel(x0, x1):
    """Strip channel on the inner face. Returns (solid, cavity): PCB slot plus an LED window
    through the lips. Cavities are cut after all solids are joined, so nothing refills them."""
    hw = STRIP_W / 2 + 0.2
    body = box(x0, x1, BED, Y_PCB + WALL, CH_Z0, CH_Z1)
    cut = box(x0 - 1, x1 + 1, Y_PCB - STRIP_PCB, Y_PCB, STRIP_ZC - hw, STRIP_ZC + hw)
    cut += box(x0 - 1, x1 + 1, BED - 1, Y_PCB - STRIP_PCB + 0.01,
               STRIP_ZC - (STRIP_W / 2 - LIP), STRIP_ZC + (STRIP_W / 2 - LIP))
    return body, cut


def sleeve(with_arm):
    ch_back = -ARCH_FRONT - LEDS_ON_TEMPLE * LED_PITCH - 4.0
    inner = -T_W / 2 + FIT / 2           # Inner face of the temple (with grip)
    outer = T_W / 2 - FIT / 2

    # Inner wall: runs along the temple and round the bend into the sock, from BED out to the temple
    wall = box(-TEMPLE_STRAIGHT, -ARCH_FRONT, BED, inner, -T_H / 2, ARCH_TOP)
    wall += tip_loc(0) * box(0, SOCK_END, BED, -TIP_W / 2 + FIT / 2, -(TIP_H / 2 + WALL), TIP_H / 2 + WALL)
    wall += y_cyl(P0[0], P0[2], BED, inner, T_H + 2 * WALL)

    # Arch over the straight temple: top bar and an outer leg with a retaining nub at its foot
    arch = box(-ARCH_BACK, -ARCH_FRONT, BED, outer + WALL, T_H / 2 - FIT / 2, ARCH_TOP)
    arch += box(-ARCH_BACK, -ARCH_FRONT, outer, outer + WALL, T_H / 2 - OUTER_LEG, ARCH_TOP)
    arch += box(-ARCH_BACK, -ARCH_FRONT, outer - NUB, outer, T_H / 2 - OUTER_LEG, T_H / 2 - OUTER_LEG + 0.8)

    # Sock: closed tube over the tip
    hh = TIP_H / 2 - FIT / 2
    sock = tip_loc(0) * box(SOCK_START, SOCK_END, BED, TIP_W / 2 + WALL, -(TIP_H / 2 + WALL), TIP_H / 2 + WALL)
    cuts = tip_loc(0) * box(SOCK_START - 1, SOCK_END - WALL, -TIP_W / 2 + FIT / 2, TIP_W / 2 - FIT / 2, -hh, hh)

    # LED channel on the inner leg, living hinge, fold-in flap
    flap0 = -ARCH_FRONT + HINGE_LEN
    flap1 = flap0 + LEDS_ON_FLAP * LED_PITCH + 3.0
    ch_t, cut_t = led_channel(ch_back, -ARCH_FRONT)
    ch_f, cut_f = led_channel(flap0, flap1)
    leds = ch_t + ch_f
    cuts += cut_t + cut_f
    hinge = box(-ARCH_FRONT - 0.5, flap0 + 0.5, BED, BED + HINGE_T, CH_Z0, CH_Z1)

    # Stud for the band, on the sock's outer face (points up when printing)
    sx, sz = tip_point(STUD_AT)
    y_out = TIP_W / 2 + WALL
    stud = y_cyl(sx, sz, y_out - 0.2, y_out + STUD_SHAFT, STUD_D)
    stud += Location((sx, y_out + STUD_SHAFT - 0.01, sz), (-90, 0, 0)) * Cone(STUD_D / 2, STUD_HEAD_D / 2, 1.0, align=None)
    stud += y_cyl(sx, sz, y_out + STUD_SHAFT + 0.98, y_out + STUD_SHAFT + 1.8, STUD_HEAD_D)

    part = wall + arch + sock + leds + hinge + stud
    if with_arm:
        arm, arm_cuts = ear_arm()
        part += arm
        cuts += arm_cuts

    # Wire tunnel inside the inner wall: from inside the LED slot (it overlaps the slot's back
    # end), round the bend, out of the sock's end
    ty0, ty1 = BED + 0.6, BED + 0.6 + TUNNEL[0]
    th = TUNNEL[1] / 2
    cuts += box(-TEMPLE_STRAIGHT, ch_back + 6.0, ty0, ty1, -th, th)
    cuts += tip_loc(0) * box(-1.0, SOCK_END + 1.0, ty0, ty1, -th, th)
    cuts += y_cyl(P0[0], P0[2], ty0, ty1, TUNNEL[1])
    return part - cuts


def ear_arm():
    """Flexible arm from the sock end down to a pod holding the MAX30101 against the earlobe.
    Returns (solid, cavity)."""
    ex, ez = tip_point(SOCK_END - 3)
    tx, tz = ARM_TO
    length = math.hypot(tx - ex, tz - ez)
    ang = math.degrees(math.atan2(tz - ez, tx - ex))
    arm = Location((ex, 0, ez), (0, -ang, 0)) * box(0, length, BED, BED + ARM_T, -ARM_W / 2, ARM_W / 2)

    # Pod: board held between a back rim (on the bed) and a front rim; the sensor side faces +y
    y1 = BED + POD_LIP + BOARD_T + BOARD_FRONT + POD_LIP
    hl, hh = BOARD_L / 2 + 0.2, BOARD_H / 2 + 0.2
    pod = box(tx - hl - WALL, tx + hl + WALL, BED, y1, tz - hh - WALL, tz + hh + WALL)
    cut = box(tx - hl, tx + hl, BED + POD_LIP, y1 - POD_LIP, tz - hh, tz + hh)           # board space
    for ya, yb in ((BED - 1, BED + POD_LIP + 0.01), (y1 - POD_LIP - 0.01, y1 + 1)):        # rim openings
        cut += box(tx - hl + POD_RIM, tx + hl - POD_RIM, ya, yb, tz - hh + POD_RIM, tz + hh - POD_RIM)
    cut += box(tx - 4, tx + 4, BED + POD_LIP, y1 - POD_LIP, tz + hh - 0.1, tz + hh + WALL + 1)  # wire exit
    return arm + pod, cut


# ================================================================ trays and sockets
def tray_outer(comp):
    l, w, h = comp
    return (l + 2 * (TRAY_CLEAR + TRAY_WALL), w + 2 * (TRAY_CLEAR + TRAY_WALL), h + TRAY_CLEAR + TRAY_FLOOR)


def tray(comp, port=True, switch=False):
    """PLA tray, floor at z=0, open top (the open side faces the band). Snap ridge round the outside.
    With switch, the -x end wall has a slot for the slide switch's actuator."""
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
    # Wire notches at the rim, middle of both long sides (they sit over the band's groove)
    t -= box(-2.5, 2.5, -ow / 2 - RIDGE - 1, ow / 2 + RIDGE + 1, oh - 1.2, oh + 1)
    return t


def switch_slot(x_wall, zc):
    """Actuator slot through an end wall whose inner face is near x_wall (the -x end), centred at height zc."""
    w, h = SWITCH_SLOT
    return box(x_wall - SOCKET_WALL - 1, x_wall + TRAY_WALL + 1, -w / 2, w / 2, zc - h / 2, zc + h / 2)


def socket(comp, port=True, switch=False):
    """TPU socket in tray coordinates (band surface at z=0, rising in +z).
    Returns (shape, length along tray x, width along tray y)."""
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
        sock, sl, sw = socket(comp, port)
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
def print_orient_sleeve(p, right_side):
    """Lay a sleeve on its inner face (y = BED, or -BED when mirrored), stud up."""
    p = (Rot(90, 0, 0) if right_side else Rot(-90, 0, 0)) * p
    bb = p.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * p


def build():
    right_arm = EAR_SIDE == "right"
    sleeve_r = sleeve(with_arm=right_arm)
    sleeve_l = mirror(sleeve(with_arm=not right_arm), Plane.XZ)
    return {
        f"sleeve_right{'_ear' if right_arm else ''}": (sleeve_r, print_orient_sleeve(sleeve_r, True)),
        f"sleeve_left{'' if right_arm else '_ear'}": (sleeve_l, print_orient_sleeve(sleeve_l, False)),
        "band_left": (band_half(BATTERY_BAY),) * 2,
        "band_right": (band_half(),) * 2,
        "band_center": (band_center(),) * 2,
        "tray_itsybitsy": (tray(ITSY_BAY, switch=True),) * 2,
        "tray_battery": (tray(BATTERY_BAY, port=False),) * 2,
    }


if __name__ == "__main__":
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    for old in list((OUT / "step").glob("*.step")) + list((OUT / "stl").glob("*.stl")):
        old.unlink()
    parts = build()
    laid_out, y = [], 0.0
    for name, (model, printable) in parts.items():
        bb = model.bounding_box()
        laid_out.append(Pos(-bb.min.X, y - bb.min.Y, -bb.min.Z) * model)
        y += bb.size.Y + 10.0
    export_step(Compound(laid_out), str(OUT / "all_parts.step"))
    for name, (model, printable) in parts.items():
        export_step(model, str(OUT / "step" / f"{name}.step"))
        export_stl(printable, str(OUT / "stl" / f"{name}.stl"))
        bb = printable.bounding_box()
        print(f"{name:18s} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:5.1f} mm  "
              f"vol {model.volume / 1000:5.2f} cm3  solids {len(model.solids())}")
