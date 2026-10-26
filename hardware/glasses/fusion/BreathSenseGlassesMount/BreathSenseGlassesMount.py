"""
BreathSense glasses mount: Fusion 360 script.

Builds the glasses mount as native Fusion components (sketches and extrudes in
the timeline), driven by User Parameters.

First run: creates a new design, adds the parameters, builds every part.
To resize: Modify > Change Parameters, edit values, then run the script
again from Utilities > Add-Ins > Scripts. It deletes the parts it built
earlier (components named "BS ...") and rebuilds them from the new values.
Edits you make by hand to those components are lost on a rebuild, so do the
parameter changes first and the hand edits last.

The geometry here matches glasses_mount.py (the build123d model). The
build functions are plain Python so they can be checked outside Fusion.

Frames:
  Sleeves: Fusion X = forward, Y = up, Z = toward the head (worn x, z, -y).
  Band parts and trays: X along the band, Y across it (up when worn), Z out from the head.
"""

import math
import traceback

try:
    import adsk.core
    import adsk.fusion
except ImportError:   # Running outside Fusion (geometry checks)
    adsk = None

# name, default, unit ("mm", "deg" or "" for counts), comment
PARAMS = [
    ("T_W", 3.5, "mm", "Temple thickness, straight part"),
    ("T_H", 6.0, "mm", "Temple height, straight part"),
    ("TIP_W", 3.5, "mm", "Temple tip thickness"),
    ("TIP_H", 4.5, "mm", "Temple tip height"),
    ("TEMPLE_STRAIGHT", 100.0, "mm", "Glasses hinge to the start of the ear bend"),
    ("TIP_ANGLE", 55.0, "deg", "Tip slope behind the ear, below horizontal"),
    ("FIT", 0.2, "mm", "TPU grip: openings this much smaller than the temple"),
    ("STRIP_W", 10.0, "mm", "LED strip width"),
    ("STRIP_PCB", 0.6, "mm", "Slot for the strip PCB"),
    ("LED_PITCH", 6.5, "mm", "LED spacing"),
    ("LEDS_ON_TEMPLE", 8, "", "LEDs along the temple"),
    ("LEDS_ON_FLAP", 2, "", "LEDs on the fold-in flap"),
    ("LIP", 1.5, "mm", "Channel lips cover this much of each strip edge"),
    ("LIP_T", 0.8, "mm", "Lip thickness"),
    ("WALL", 1.2, "mm", "TPU wall"),
    ("ARCH_BACK", 95.0, "mm", "Arch starts this far behind the glasses hinge"),
    ("ARCH_FRONT", 3.0, "mm", "Arch ends this far behind the glasses hinge"),
    ("OUTER_LEG", 3.0, "mm", "Outer leg reach down the temple (longer needs print supports)"),
    ("NUB", 0.4, "mm", "Retaining nub at the foot of the outer leg"),
    ("SOCK_START", 5.0, "mm", "Sock starts this far along the tip"),
    ("SOCK_END", 37.0, "mm", "Sock ends (closed) this far along the tip"),
    ("HINGE_LEN", 4.0, "mm", "Living hinge length before the flap"),
    ("HINGE_T", 0.8, "mm", "Living hinge thickness"),
    ("STUD_AT", 25.0, "mm", "Band stud position along the tip"),
    ("STUD_D", 3.0, "mm", "Stud shaft diameter"),
    ("STUD_HEAD_D", 5.0, "mm", "Stud head diameter"),
    ("STUD_SHAFT", 2.4, "mm", "Stud shaft length"),
    ("TUNNEL_T", 1.4, "mm", "Wire tunnel thickness"),
    ("TUNNEL_H", 3.0, "mm", "Wire tunnel height"),
    ("EAR_ARM", 1, "", "1 = right sleeve carries the earlobe sensor arm, 0 = left"),
    ("ARM_W", 6.0, "mm", "Sensor arm width"),
    ("ARM_T", 1.8, "mm", "Sensor arm thickness"),
    ("ARM_TO_X", -100.0, "mm", "Sensor pod centre, forward of the glasses hinge"),
    ("ARM_TO_Z", -52.0, "mm", "Sensor pod centre, height relative to the temple"),
    ("BOARD_L", 22.5, "mm", "MAX30101 breakout length"),
    ("BOARD_H", 19.0, "mm", "MAX30101 breakout height"),
    ("BOARD_T", 1.6, "mm", "Breakout PCB thickness"),
    ("BOARD_FRONT", 1.8, "mm", "Component height on the sensor side"),
    ("POD_RIM", 1.5, "mm", "Pod rims holding the board"),
    ("POD_LIP", 0.8, "mm", "Pod rim thickness"),
    ("BAND_H", 14.0, "mm", "Band height"),
    ("BAND_T", 2.0, "mm", "Band thickness"),
    ("BAND_HALF_LEN", 94.0, "mm", "Band half: inner studs to first outer hole"),
    ("ADJ_HOLES", 5, "", "Size-adjustment holes"),
    ("ADJ_PITCH", 6.0, "mm", "Adjustment hole spacing"),
    ("HOLE_D", 3.2, "mm", "Band hole diameter"),
    ("END_STUD_GAP", 9.0, "mm", "Stud spacing across the band at the center module"),
    ("GROOVE_W", 3.2, "mm", "Wire groove width"),
    ("GROOVE_D", 1.0, "mm", "Wire groove depth"),
    ("RAIL_W", 1.0, "mm", "Wire channel rail width"),
    ("RAIL_H", 1.6, "mm", "Wire channel rail height"),
    ("BRIDGE_EVERY", 18.0, "mm", "Wire channel bridge spacing"),
    ("BRIDGE_LEN", 4.0, "mm", "Wire channel bridge length"),
    ("ITSY_L", 36.5, "mm", "ItsyBitsy length"),
    ("ITSY_W", 18.0, "mm", "ItsyBitsy width"),
    ("ITSY_H", 9.5, "mm", "ItsyBitsy + LiPo backpack stack height, pins trimmed"),
    ("BATT_L", 32.5, "mm", "Battery length incl. protection board"),
    ("BATT_W", 20.0, "mm", "Battery width"),
    ("BATT_H", 5.5, "mm", "Battery thickness"),
    ("BATT_LEAD", 4.0, "mm", "Room in the battery tray for the leads to bend"),
    ("SW_L", 10.5, "mm", "Switch plate length, ears snipped (across the tray)"),
    ("SW_D", 8.0, "mm", "Switch depth behind the plate incl. pins (along the tray)"),
    ("SW_H", 5.5, "mm", "Switch plate width"),
    ("SW_SLOT_W", 8.0, "mm", "Switch lever slot width (slide direction)"),
    ("SW_SLOT_H", 3.5, "mm", "Switch lever slot height"),
    ("TRAY_CLEAR", 0.3, "mm", "Tray clearance per side"),
    ("TRAY_WALL", 1.6, "mm", "PLA tray wall"),
    ("TRAY_FLOOR", 1.2, "mm", "PLA tray floor"),
    ("RIDGE", 0.5, "mm", "Tray snap ridge"),
    ("SOCKET_WALL", 1.6, "mm", "TPU socket wall"),
    ("PORT_W", 12.0, "mm", "USB port cut-out width"),
]

PART_PREFIX = "BS "


# ======================================================================= geometry model
# A part is a list of steps on named bodies:
#   ("new" | "join" | "cut", body, profile, z0, z1)   extrude profile from z0 to z1
#   ("combine", target, tool)                           join body tool into target
# A profile is ("poly", [(x, y), ...]) or ("circle", (x, y), r). All mm.

def rect(x0, x1, y0, y1):
    return ("poly", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def circle(x, y, d):
    return ("circle", (x, y), d / 2)


def rrect(origin, ang_deg, s0, s1, t0, t1):
    """Rectangle s0..s1 along direction ang_deg from origin, t0..t1 across it (to the left)."""
    a = math.radians(ang_deg)
    d = (math.cos(a), math.sin(a))
    n = (-math.sin(a), math.cos(a))
    pts = [(origin[0] + s * d[0] + t * n[0], origin[1] + s * d[1] + t * n[1])
           for s, t in ((s0, t0), (s1, t0), (s1, t1), (s0, t1))]
    return ("poly", pts)


def move(steps, dx=0.0, dy=0.0, dz=0.0, rot_deg=0.0):
    """Rotate steps about Z, then translate them."""
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))

    def tp(p):
        return (p[0] * c - p[1] * s + dx, p[0] * s + p[1] * c + dy)

    out = []
    for st in steps:
        if st[0] == "combine":
            out.append(st)
            continue
        kind, body, prof, z0, z1 = st
        if prof[0] == "poly":
            prof = ("poly", [tp(p) for p in prof[1]])
        else:
            prof = ("circle", tp(prof[1]), prof[2])
        out.append((kind, body, prof, z0 + dz, z1 + dz))
    return out


class Sleeve:
    """Sleeve geometry in the worn frame (x forward, y outward, z up), emitted in Fusion's frame."""

    def __init__(self, P, right, with_arm):
        self.P = P
        self.zs = -1.0 if right else 1.0   # Fusion Z = -y on the right; mirrored on the left
        self.with_arm = with_arm
        T_W, WALL, STRIP_PCB, LIP_T = P["T_W"], P["WALL"], P["STRIP_PCB"], P["LIP_T"]
        self.Y_PCB = -T_W / 2 - WALL
        self.BED = self.Y_PCB - STRIP_PCB - LIP_T
        self.ARCH_TOP = P["T_H"] / 2 + WALL
        self.CH_Z1 = self.ARCH_TOP
        self.CH_Z0 = self.ARCH_TOP - (P["STRIP_W"] + 0.4 + 2 * WALL)
        self.STRIP_ZC = (self.CH_Z0 + self.CH_Z1) / 2
        self.P0 = (-P["TEMPLE_STRAIGHT"], 0.0)
        self.TIP_ANG = 180.0 + P["TIP_ANGLE"]   # Tip direction in the x-z plane
        self.steps = []

    def _z(self, y0, y1):
        a, b = self.zs * y0, self.zs * y1
        return min(a, b), max(a, b)

    def box(self, kind, x0, x1, y0, y1, z0, z1):
        self.steps.append((kind, "sleeve", rect(x0, x1, z0, z1)) + self._z(y0, y1))

    def tip_box(self, kind, s0, s1, y0, y1, t0, t1):
        # Local t is the tip's "up" (n = (sin a, -cos a)); rrect's left normal is the opposite
        self.steps.append((kind, "sleeve", rrect(self.P0, self.TIP_ANG, s0, s1, -t1, -t0)) + self._z(y0, y1))

    def y_cyl(self, kind, x, z, y0, y1, d):
        self.steps.append((kind, "sleeve", circle(x, z, d)) + self._z(y0, y1))

    def tip_point(self, s):
        a = math.radians(self.P["TIP_ANGLE"])
        return (self.P0[0] - math.cos(a) * s, self.P0[1] - math.sin(a) * s)

    def build(self):
        P = self.P
        BED, Y_PCB, WALL, FIT = self.BED, self.Y_PCB, P["WALL"], P["FIT"]
        T_W, T_H, TIP_W, TIP_H = P["T_W"], P["T_H"], P["TIP_W"], P["TIP_H"]
        AF, AB = P["ARCH_FRONT"], P["ARCH_BACK"]
        ch_back = -AF - P["LEDS_ON_TEMPLE"] * P["LED_PITCH"] - 4.0
        inner = -T_W / 2 + FIT / 2
        outer = T_W / 2 - FIT / 2
        cuts = []

        # Inner wall, along the temple and round the bend
        self.box("new", -P["TEMPLE_STRAIGHT"], -AF, BED, inner, -T_H / 2, self.ARCH_TOP)
        self.tip_box("join", 0, P["SOCK_END"], BED, -TIP_W / 2 + FIT / 2, -(TIP_H / 2 + WALL), TIP_H / 2 + WALL)
        self.y_cyl("join", self.P0[0], self.P0[1], BED, inner, T_H + 2 * WALL)
        # Arch: top bar, outer leg, nub
        self.box("join", -AB, -AF, BED, outer + WALL, T_H / 2 - FIT / 2, self.ARCH_TOP)
        self.box("join", -AB, -AF, outer, outer + WALL, T_H / 2 - P["OUTER_LEG"], self.ARCH_TOP)
        self.box("join", -AB, -AF, outer - P["NUB"], outer, T_H / 2 - P["OUTER_LEG"], T_H / 2 - P["OUTER_LEG"] + 0.8)
        # Sock
        hh = TIP_H / 2 - FIT / 2
        self.tip_box("join", P["SOCK_START"], P["SOCK_END"], BED, TIP_W / 2 + WALL, -(TIP_H / 2 + WALL), TIP_H / 2 + WALL)
        cuts.append(("tip", P["SOCK_START"] - 1, P["SOCK_END"] - WALL, -TIP_W / 2 + FIT / 2, TIP_W / 2 - FIT / 2, -hh, hh))
        # LED channels, hinge, flap
        flap0 = -AF + P["HINGE_LEN"]
        flap1 = flap0 + P["LEDS_ON_FLAP"] * P["LED_PITCH"] + 3.0
        for x0, x1 in ((ch_back, -AF), (flap0, flap1)):
            self.box("join", x0, x1, BED, Y_PCB + WALL, self.CH_Z0, self.CH_Z1)
            hw = P["STRIP_W"] / 2 + 0.2
            cuts.append(("box", x0 - 1, x1 + 1, Y_PCB - P["STRIP_PCB"], Y_PCB, self.STRIP_ZC - hw, self.STRIP_ZC + hw))
            win = P["STRIP_W"] / 2 - P["LIP"]
            cuts.append(("box", x0 - 1, x1 + 1, BED - 1, Y_PCB - P["STRIP_PCB"] + 0.01, self.STRIP_ZC - win, self.STRIP_ZC + win))
        self.box("join", -AF - 0.5, flap0 + 0.5, BED, BED + P["HINGE_T"], self.CH_Z0, self.CH_Z1)
        # Stud on the sock's outer face (head stepped so it prints without a steep overhang)
        sx, sz = self.tip_point(P["STUD_AT"])
        y_out = TIP_W / 2 + WALL
        sh = P["STUD_SHAFT"]
        self.y_cyl("join", sx, sz, y_out - 0.2, y_out + sh, P["STUD_D"])
        for i, f in enumerate((0.33, 0.67, 1.0)):
            d = P["STUD_D"] + (P["STUD_HEAD_D"] - P["STUD_D"]) * f
            self.y_cyl("join", sx, sz, y_out + sh - 0.01 + i / 3, y_out + sh + (i + 1) / 3, d)
        self.y_cyl("join", sx, sz, y_out + sh + 0.98, y_out + sh + 1.8, P["STUD_HEAD_D"])
        # Ear arm and sensor pod
        if self.with_arm:
            ex, ez = self.tip_point(P["SOCK_END"] - 3)
            tx, tz = P["ARM_TO_X"], P["ARM_TO_Z"]
            length = math.hypot(tx - ex, tz - ez)
            ang = math.degrees(math.atan2(tz - ez, tx - ex))
            aw = P["ARM_W"] / 2
            self.steps.append(("join", "sleeve", rrect((ex, ez), ang, 0, length, -aw, aw)) + self._z(BED, BED + P["ARM_T"]))
            y1 = BED + P["POD_LIP"] + P["BOARD_T"] + P["BOARD_FRONT"] + P["POD_LIP"]
            hl, hh2 = P["BOARD_L"] / 2 + 0.2, P["BOARD_H"] / 2 + 0.2
            rim, lip = P["POD_RIM"], P["POD_LIP"]
            self.box("join", tx - hl - WALL, tx + hl + WALL, BED, y1, tz - hh2 - WALL, tz + hh2 + WALL)
            cuts.append(("box", tx - hl, tx + hl, BED + lip, y1 - lip, tz - hh2, tz + hh2))
            cuts.append(("box", tx - hl + rim, tx + hl - rim, BED - 1, BED + lip + 0.01, tz - hh2 + rim, tz + hh2 - rim))
            cuts.append(("box", tx - hl + rim, tx + hl - rim, y1 - lip - 0.01, y1 + 1, tz - hh2 + rim, tz + hh2 - rim))
            cuts.append(("box", tx - 4, tx + 4, BED + lip, y1 - lip, tz + hh2 - 0.1, tz + hh2 + WALL + 1))
        # Wire tunnel
        ty0, ty1 = BED + 0.6, BED + 0.6 + P["TUNNEL_T"]
        th = P["TUNNEL_H"] / 2
        cuts.append(("box", -P["TEMPLE_STRAIGHT"], ch_back + 6.0, ty0, ty1, -th, th))
        cuts.append(("tip", -1.0, P["SOCK_END"] + 1.0, ty0, ty1, -th, th))
        cuts.append(("cyl", self.P0[0], self.P0[1], ty0, ty1, P["TUNNEL_H"]))

        # Cavities last, so no solid refills them
        for c in cuts:
            if c[0] == "box":
                self.box("cut", *c[1:])
            elif c[0] == "tip":
                self.tip_box("cut", *c[1:])
            else:
                self.y_cyl("cut", *c[1:])
        return self.steps


def tray_outer(P, comp):
    l, w, h = comp
    return (l + 2 * (P["TRAY_CLEAR"] + P["TRAY_WALL"]), w + 2 * (P["TRAY_CLEAR"] + P["TRAY_WALL"]),
            h + P["TRAY_CLEAR"] + P["TRAY_FLOOR"])


def itsy_bay(P):
    """ItsyBitsy tray contents: the board stack plus the switch at the end away from the USB."""
    return (P["ITSY_L"] + P["SW_D"] + 0.5, P["ITSY_W"], max(P["ITSY_H"], P["SW_H"]))


def switch_slot(P, x_wall, zc, body):
    """Actuator slot through the -x end wall (inner face near x_wall), centred at height zc."""
    w, h = P["SW_SLOT_W"], P["SW_SLOT_H"]
    return ("cut", body, rect(x_wall - P["SOCKET_WALL"] - 1, x_wall + P["TRAY_WALL"] + 1, -w / 2, w / 2), zc - h / 2, zc + h / 2)


def tray_steps(P, comp, port=True, switch=False):
    ol, ow, oh = tray_outer(P, comp)
    R, TW = P["RIDGE"], P["TRAY_WALL"]
    rz = oh - 1.5
    s = [("new", "tray", rect(-ol / 2, ol / 2, -ow / 2, ow / 2), 0, oh),
         ("join", "tray", rect(-ol / 2 - R, ol / 2 + R, -ow / 2 + 2, ow / 2 - 2), rz - 0.5, rz + 0.5),
         ("join", "tray", rect(-ol / 2 + 2, ol / 2 - 2, -ow / 2 - R, ow / 2 + R), rz - 0.5, rz + 0.5),
         ("cut", "tray", rect(-ol / 2 + TW, ol / 2 - TW, -ow / 2 + TW, ow / 2 - TW), P["TRAY_FLOOR"], oh + 1)]
    if port:
        s.append(("cut", "tray", rect(ol / 2 - TW - 1, ol / 2 + R + 1, -P["PORT_W"] / 2, P["PORT_W"] / 2), P["TRAY_FLOOR"], oh + 1))
    if switch:
        s.append(switch_slot(P, -ol / 2, P["TRAY_FLOOR"] + P["SW_H"] / 2, "tray"))
    s.append(("cut", "tray", rect(-2.5, 2.5, -ow / 2 - R - 1, ow / 2 + R + 1), oh - 1.2, oh + 1))
    return s


def socket_steps(P, comp, port, body, switch=False):
    """TPU socket in tray coordinates (band surface at z=0). Returns (steps, length, width)."""
    ol, ow, oh = tray_outer(P, comp)
    sl, sw = ol + 2 * P["SOCKET_WALL"], ow + 2 * P["SOCKET_WALL"]
    R = P["RIDGE"]
    s = [("new", body, rect(-sl / 2, sl / 2, -sw / 2, sw / 2), 0, oh),
         ("cut", body, rect(-ol / 2, ol / 2, -ow / 2, ow / 2), -1, oh + 1),
         ("cut", body, rect(-ol / 2 - R, ol / 2 + R, -ow / 2 + 1.5, ow / 2 - 1.5), 0.9, 2.1),
         ("cut", body, rect(-ol / 2 + 1.5, ol / 2 - 1.5, -ow / 2 - R, ow / 2 + R), 0.9, 2.1)]
    if port:
        s.append(("cut", body, rect(ol / 2 - 1, sl / 2 + 1, -P["PORT_W"] / 2 - 0.5, P["PORT_W"] / 2 + 0.5), -1, oh + 1))
    if switch:   # The tray goes in upside down, so its slot height is measured from the top
        s.append(switch_slot(P, -ol / 2, oh - (P["TRAY_FLOOR"] + P["SW_H"] / 2), body))
    return s, sl, sw


def rails_steps(P, x0, x1, body):
    g, rw, rh, T = P["GROOVE_W"] / 2, P["RAIL_W"], P["RAIL_H"], P["BAND_T"]
    s = [("join", body, rect(x0, x1, g, g + rw), T - 0.01, T + rh),
         ("join", body, rect(x0, x1, -g - rw, -g), T - 0.01, T + rh)]
    x = x0 + P["BRIDGE_EVERY"] / 2
    while x + P["BRIDGE_LEN"] < x1:
        s.append(("join", body, rect(x, x + P["BRIDGE_LEN"], -g - rw, g + rw), T + rh - 0.01, T + rh + 0.8))
        x += P["BRIDGE_EVERY"]
    return s


def band_half_steps(P, comp=None, port=False):
    """Band half with one socket, or a plain strap (still grooved for wires) when comp is None."""
    T, H = P["BAND_T"], P["BAND_H"]
    outer = P["BAND_HALF_LEN"] + (P["ADJ_HOLES"] - 1) * P["ADJ_PITCH"] + 6.0
    s = [("new", "band", rect(-6.0, outer, -H / 2, H / 2), 0, T)]
    rails_from = 6.0                     # Clear of the center module's stud heads
    if comp is not None:
        sock, sl, sw = socket_steps(P, comp, port, "socket")
        if port:
            sock, sl, sw = move(sock, rot_deg=-90), sw, sl   # Port faces down (-y)
        cx = 8.0 + sl / 2
        s.append(("join", "band", rect(cx - sl / 2, cx + sl / 2, -sw / 2, sw / 2), 0, T))
        s += move(sock, dx=cx, dz=T - 0.01)
        s.append(("combine", "band", "socket"))
        rails_from = cx + sl / 2
    s += rails_steps(P, rails_from, P["BAND_HALF_LEN"] - 5, "band")
    s.append(("cut", "band", rect(-7.0, P["BAND_HALF_LEN"] - 5, -P["GROOVE_W"] / 2, P["GROOVE_W"] / 2), T - P["GROOVE_D"], T + 0.01))
    for yc in (-P["END_STUD_GAP"] / 2, P["END_STUD_GAP"] / 2):
        s.append(("cut", "band", circle(0, yc, P["HOLE_D"]), -1, T + 1))
    for i in range(int(P["ADJ_HOLES"])):
        s.append(("cut", "band", circle(P["BAND_HALF_LEN"] + i * P["ADJ_PITCH"], 0, P["HOLE_D"]), -1, T + 1))
    return s


def band_center_steps(P):
    T, H = P["BAND_T"], P["BAND_H"]
    sock, sl, sw = socket_steps(P, itsy_bay(P), True, "socket", switch=True)
    sock = move(sock, rot_deg=-90)                     # USB faces down, switch up
    stud_x = sw / 2 + 6.5
    half = stud_x + 3.5
    h = max(sl, H)
    s = [("new", "center", rect(-half, half, -h / 2, h / 2), 0, T)]
    s += move(sock, dz=T - 0.01)
    s.append(("combine", "center", "socket"))
    s.append(("cut", "center", rect(-half - 1, half + 1, -P["GROOVE_W"] / 2, P["GROOVE_W"] / 2), T - P["GROOVE_D"], T + 0.01))
    sh = P["STUD_SHAFT"]
    for xe in (-stud_x, stud_x):
        for yc in (-P["END_STUD_GAP"] / 2, P["END_STUD_GAP"] / 2):
            s.append(("join", "center", circle(xe, yc, P["STUD_D"]), T - 0.2, T + sh))
            for i, f in enumerate((0.33, 0.67, 1.0)):
                d = P["STUD_D"] + (P["STUD_HEAD_D"] - P["STUD_D"]) * f
                s.append(("join", "center", circle(xe, yc, d), T + sh - 0.01 + i / 3, T + sh + (i + 1) / 3))
            s.append(("join", "center", circle(xe, yc, P["STUD_HEAD_D"]), T + sh + 0.98, T + sh + 1.8))
    return s


def all_parts(P):
    """{part name: steps} for every part."""
    right_arm = int(P["EAR_ARM"]) == 1
    return {
        "sleeve right" + (" (ear arm)" if right_arm else ""): Sleeve(P, True, right_arm).build(),
        "sleeve left" + ("" if right_arm else " (ear arm)"): Sleeve(P, False, not right_arm).build(),
        "band left (battery)": band_half_steps(P, (P["BATT_L"] + P["BATT_LEAD"], P["BATT_W"], P["BATT_H"])),
        "band center (ItsyBitsy)": band_center_steps(P),
        "band right (strap)": band_half_steps(P),
        "tray ItsyBitsy": tray_steps(P, itsy_bay(P), switch=True),
        "tray battery": tray_steps(P, (P["BATT_L"] + P["BATT_LEAD"], P["BATT_W"], P["BATT_H"]), port=False),
    }


def default_params():
    return {name: float(v) for name, v, _, _ in PARAMS}


# ======================================================================= Fusion
def _params(design):
    """Read the user parameters (creating any that are missing), in mm / degrees / counts."""
    up = design.userParameters
    vals = {}
    for name, default, unit, comment in PARAMS:
        p = up.itemByName(name)
        if p is None:
            text = "{} {}".format(default, unit).strip()
            p = up.add(name, adsk.core.ValueInput.createByString(text), unit, comment)
        if unit == "mm":
            vals[name] = p.value * 10.0          # Fusion stores lengths in cm
        elif unit == "deg":
            vals[name] = math.degrees(p.value)   # ... and angles in radians
        else:
            vals[name] = p.value
    return vals


class _Builder:
    """Turns steps into sketches and extrudes inside one component."""

    def __init__(self, comp):
        self.comp = comp
        self.planes = {}
        self.bodies = {}

    def plane(self, z):
        key = round(z, 4)
        if key not in self.planes:
            if abs(z) < 1e-9:
                self.planes[key] = self.comp.xYConstructionPlane
            else:
                inp = self.comp.constructionPlanes.createInput()
                inp.setByOffset(self.comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(z / 10.0))
                pl = self.comp.constructionPlanes.add(inp)
                pl.isLightBulbOn = False
                self.planes[key] = pl
        return self.planes[key]

    def profile(self, prof, z):
        sk = self.comp.sketches.add(self.plane(z))
        sk.isComputeDeferred = True

        def pt(x, y):
            return sk.modelToSketchSpace(adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0))

        if prof[0] == "circle":
            (x, y), r = prof[1], prof[2]
            sk.sketchCurves.sketchCircles.addByCenterRadius(pt(x, y), r / 10.0)
        else:
            pts = prof[1]
            lines = sk.sketchCurves.sketchLines
            first = lines.addByTwoPoints(pt(*pts[0]), pt(*pts[1]))
            prev = first
            for p in pts[2:]:
                prev = lines.addByTwoPoints(prev.endSketchPoint, pt(*p))
            lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
        sk.isComputeDeferred = False
        sk.isVisible = False
        return sk.profiles.item(0)

    def step(self, st):
        F = adsk.fusion.FeatureOperations
        if st[0] == "combine":
            target, tool = self.bodies[st[1]], self.bodies[st[2]]
            tools = adsk.core.ObjectCollection.create()
            tools.add(tool)
            ci = self.comp.features.combineFeatures.createInput(target, tools)
            ci.operation = F.JoinFeatureOperation
            self.comp.features.combineFeatures.add(ci)
            return
        kind, body, prof, z0, z1 = st
        op = {"new": F.NewBodyFeatureOperation, "join": F.JoinFeatureOperation, "cut": F.CutFeatureOperation}[kind]
        ext = self.comp.features.extrudeFeatures
        ei = ext.createInput(self.profile(prof, z0), op)
        ei.setDistanceExtent(False, adsk.core.ValueInput.createByReal((z1 - z0) / 10.0))
        if kind != "new":
            ei.participantBodies = [self.bodies[body]]
        feat = ext.add(ei)
        if kind == "new":
            b = feat.bodies.item(0)
            b.name = body
            self.bodies[body] = b
            # Every step assumes extrusions run up from their plane (+Z). Stop if not.
            zmin = b.boundingBox.minPoint.z * 10.0
            if abs(zmin - z0) > 0.05:
                raise RuntimeError("Extrude went the wrong way for {} (bottom at {:.2f} mm, "
                                   "expected {:.2f} mm). Please report this.".format(body, zmin, z0))


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None or design.userParameters.itemByName("LED_PITCH") is None:
            app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        P = _params(design)
        for occ in [o for o in root.occurrences if o.component.name.startswith(PART_PREFIX)]:
            occ.deleteMe()

        y = 0.0
        for name, steps in all_parts(P).items():
            m = adsk.core.Matrix3D.create()
            m.translation = adsk.core.Vector3D.create(0, y / 10.0, 0)
            occ = root.occurrences.addNewComponent(m)
            occ.component.name = PART_PREFIX + name
            b = _Builder(occ.component)
            for st in steps:
                b.step(st)
            y += 90.0 if name.startswith("sleeve") else 60.0
        ui.messageBox("BreathSense glasses mount built.\n\n"
                      "Resize: Modify > Change Parameters, then run this script again.")
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
