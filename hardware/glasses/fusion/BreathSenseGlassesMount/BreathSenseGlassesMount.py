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
  Sleeves: Fusion X = forward, Y = up, Z = toward the head (worn x, z, -y),
           modelled straight, as printed (standing on Y = CLIP_T).
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
    ("T_W_MIN", 2.0, "mm", "Thinnest temple the leaves grip"),
    ("T_W_MAX", 6.0, "mm", "Thickest temple the clips take"),
    ("STRIP_W", 4.0, "mm", "LED strip width"),
    ("STRIP_PCB", 0.6, "mm", "LED strip PCB thickness"),
    ("LED_PITCH", 6.8, "mm", "LED spacing"),
    ("LEDS_ON_TEMPLE", 8, "", "LEDs along the temple"),
    ("LEDS_ON_FLAP", 2, "", "LEDs on the front flap"),
    ("WALL", 1.2, "mm", "TPU wall (sensor pod)"),
    ("CLIP_T", 1.6, "mm", "Top bar thickness"),
    ("OL_T", 1.6, "mm", "Outer leg thickness"),
    ("OL_H", 9.0, "mm", "Outer leg reach below the temple's top edge"),
    ("LEAF_T", 1.0, "mm", "Leaf thickness"),
    ("LEAF_ANGLE", 45.0, "deg", "Leaf angle from straight across"),
    ("RAMP", 1.0, "", "Leaf lead-in slope (rise per mm toward the tip)"),
    ("CLIP_N", 3, "", "Clips along the temple"),
    ("CLIP_L", 23.0, "mm", "Clip length"),
    ("CLIP_GAP", 5.5, "mm", "Gap between clips"),
    ("CLIP_FRONT", 6.0, "mm", "Front clip starts this far behind the hinge"),
    ("BRIDGE_W", 2.0, "mm", "Top bar left at each clip end"),
    ("CORNER_X1", -1.2, "mm", "Front end of the corner bend (it starts at -CLIP_FRONT)"),
    ("CORNER_FLOOR", 0.6, "mm", "Channel floor round the corner"),
    ("KERF_W", 0.8, "mm", "Corner slot width"),
    ("KERF_PITCH", 1.4, "mm", "Corner slot spacing"),
    ("NECK_L", 20.0, "mm", "Neck length (takes the ear bend)"),
    ("NECK_H", 3.0, "mm", "Neck height"),
    ("TIP_ARCH_L", 25.0, "mm", "Ear-end arch length"),
    ("STUD_D", 3.0, "mm", "Stud shaft diameter"),
    ("STUD_HEAD_D", 5.0, "mm", "Stud head diameter"),
    ("STUD_SHAFT", 2.4, "mm", "Stud shaft length"),
    ("FLOOR", 1.0, "mm", "LED channel floor"),
    ("LIP", 0.7, "mm", "Channel lips cover this much of each strip edge"),
    ("LIP_T", 0.6, "mm", "Lip thickness"),
    ("LIP_L", 2.5, "mm", "Lip length along the channel"),
    ("EAR_ARM", 1, "", "1 = right sleeve carries the earlobe sensor arm, 0 = left"),
    ("ARM_W", 6.0, "mm", "Sensor arm width"),
    ("ARM_T", 1.8, "mm", "Sensor arm thickness"),
    ("POD_DEPTH", 38.0, "mm", "Sensor pod centre below the ear-end arch's top"),
    ("BOARD_L", 22.5, "mm", "MAX30101 breakout length"),
    ("BOARD_H", 19.0, "mm", "MAX30101 breakout height"),
    ("BOARD_T", 1.6, "mm", "Breakout PCB thickness"),
    ("BOARD_FRONT", 1.8, "mm", "Component height on the sensor side"),
    ("POD_RIM", 1.5, "mm", "Pod rims holding the board"),
    ("POD_LIP", 0.8, "mm", "Pod rim thickness"),
    ("POD_DETENT", 0.3, "mm", "Bumps the board snaps past at the pod's open edge"),
    ("BAND_H", 14.0, "mm", "Band height"),
    ("BAND_T", 2.0, "mm", "Band thickness"),
    ("BAND_HALF_LEN", 121.0, "mm", "Band half: inner studs to first outer hole"),
    ("ADJ_HOLES", 7, "", "Size-adjustment holes"),
    ("ADJ_PITCH", 6.0, "mm", "Adjustment hole spacing"),
    ("HOLE_D", 3.2, "mm", "Band hole diameter"),
    ("END_STUD_GAP", 9.0, "mm", "Stud spacing across the band at the center module"),
    ("GROOVE_W", 4.0, "mm", "Wire groove width"),
    ("GROOVE_D", 1.0, "mm", "Wire groove depth"),
    ("RAIL_W", 1.0, "mm", "Wire channel rail width"),
    ("RAIL_H", 2.0, "mm", "Wire channel rail height"),
    ("PASS_W", 6.0, "mm", "Wire opening width through tray and socket walls"),
    ("PASS_H", 3.0, "mm", "Wire opening height"),
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
    ("SW_SLOT_W", 8.0, "mm", "Switch lever slot width: lever thickness + travel"),
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
#   ("new" | "join" | "cut", body, profile, z0, z1)   extrude profile from Z = z0 to z1
#   (..., z0, z1, "x")    profile in (Y, Z), extruded from X = z0 to z1
#   (..., z0, z1, "y")    profile in (X, Z), extruded from Y = z0 to z1
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
    """Rotate steps about Z, then translate them. Z-axis steps only (band parts and trays)."""
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
    """Sleeve geometry in the worn frame (x forward, y outward, z up; temple inner face at y=0, top
    edge at z=0), as printed: straight. Emitted in Fusion's frame. Mirrors glasses_mount.sleeve()."""

    def __init__(self, P, right, with_arm):
        self.P = P
        self.zs = -1.0 if right else 1.0   # Fusion Z = -y on the right; mirrored on the left
        self.with_arm = with_arm
        self.steps = []
        ch_w = P["STRIP_W"] + 0.4
        self.CH_D = P["STRIP_PCB"] + 0.2 + P["LIP_T"]
        self.IL_T = P["FLOOR"] + self.CH_D
        self.CH_Z1 = -0.2
        self.CH_Z0 = self.CH_Z1 - ch_w
        self.IL_Z0 = self.CH_Z0 - 1.2
        self.STRIP_ZC = (self.CH_Z0 + self.CH_Z1) / 2
        self.GAP = P["T_W_MAX"] + P["LEAF_T"] + 0.3
        self.LEAF_REST = P["T_W_MIN"] - 0.5
        n, L, g, front = int(P["CLIP_N"]), P["CLIP_L"], P["CLIP_GAP"], P["CLIP_FRONT"]
        self.TEMPLE_END = -front - n * L - (n - 1) * g
        self.TIP_X1 = self.TEMPLE_END - P["NECK_L"]
        self.TIP_X0 = self.TIP_X1 - P["TIP_ARCH_L"]
        pitch = P["LED_PITCH"]
        nt, nf = int(P["LEDS_ON_TEMPLE"]), int(P["LEDS_ON_FLAP"])
        self.LED_X = ([-front - 1.0 - pitch * (nt - 1 - i) for i in range(nt)]
                      + [P["CORNER_X1"] + 1.0 + pitch * i for i in range(nf)])
        self.FLAP_X1 = self.LED_X[-1] + pitch / 2 + 1.0
        self.spans = [(-front - k * (L + g) - L, -front - k * (L + g)) for k in range(n)] + [(self.TIP_X0, self.TIP_X1)]

    # Worn-frame primitives. Fusion X = x, Y = z, Z = zs * y.
    def _z(self, y0, y1):
        a, b = self.zs * y0, self.zs * y1
        return min(a, b), max(a, b)

    def box(self, kind, x0, x1, y0, y1, z0, z1):
        self.steps.append((kind, "sleeve", rect(x0, x1, z0, z1)) + self._z(y0, y1))

    def y_cyl(self, kind, x, z, y0, y1, d):
        self.steps.append((kind, "sleeve", circle(x, z, d)) + self._z(y0, y1))

    def xz_poly(self, kind, pts, y0, y1):
        """Prism from an (x, z) outline across y0..y1."""
        self.steps.append((kind, "sleeve", ("poly", pts)) + self._z(y0, y1))

    def yz_poly(self, kind, pts, x0, x1):
        """Prism from a (y, z) outline along x0..x1: sketched on Fusion's YZ plane, (Y, Z) = (z, zs * y)."""
        self.steps.append((kind, "sleeve", ("poly", [(z, self.zs * y) for y, z in pts]), x0, x1, "x"))

    def xy_poly(self, kind, pts, z0, z1):
        """Prism from an (x, y) outline over z0..z1: sketched on Fusion's XZ plane, (X, Z) = (x, zs * y)."""
        self.steps.append((kind, "sleeve", ("poly", [(x, self.zs * y) for x, y in pts]), z0, z1, "y"))

    def leaf_outline(self, xr, sense):
        P = self.P
        a = math.radians(P["LEAF_ANGLE"])
        t = P["LEAF_T"]
        d = (sense * math.sin(a), -math.cos(a))
        n = (-d[1] * t / 2, d[0] * t / 2)
        y_root = self.GAP + 0.5
        length = (y_root - self.LEAF_REST - t / 2 * math.sin(a)) / math.cos(a)
        r, e = (xr, y_root), (xr + d[0] * length, y_root + d[1] * length)
        return [(r[0] + n[0], r[1] + n[1]), (e[0] + n[0], e[1] + n[1]), (e[0] - n[0], e[1] - n[1]),
                (r[0] - n[0], r[1] - n[1])]

    def lip_positions(self):
        P = self.P
        xs, x = [], self.FLAP_X1 - 3.0
        while x > self.TEMPLE_END + 2.0:
            if not -P["CLIP_FRONT"] - 1.5 < x < P["CORNER_X1"] + 1.5:
                xs.append(x)
            x -= 2 * P["LED_PITCH"]
        x = self.TIP_X1 - 3.0
        while x > self.TIP_X0 + 2.0:
            xs.append(x)
            x -= 2 * P["LED_PITCH"]
        return xs

    def kerf_positions(self):
        P = self.P
        return [x for x in [-P["CLIP_FRONT"] + 0.6 + i * P["KERF_PITCH"] for i in range(20)]
                if x + P["KERF_W"] <= P["CORNER_X1"] - 0.6]

    def build(self):
        P = self.P
        IL_T, GAP, CT, OL_T, OL_H = self.IL_T, self.GAP, P["CLIP_T"], P["OL_T"], P["OL_H"]
        BW = P["BRIDGE_W"]
        TE, X0, X1 = self.TEMPLE_END, self.TIP_X0, self.TIP_X1

        # Inner leg (flap, corner and temple; ear-end arch) and the neck between
        self.box("new", TE, self.FLAP_X1, -IL_T, 0, self.IL_Z0, CT)
        self.box("join", X0, X1, -IL_T, 0, self.IL_Z0, CT)
        self.box("join", X1 - 0.5, TE + 0.5, -IL_T, 0, CT - P["NECK_H"], CT)
        # Clips: top bar and outer leg; top bar opened between the end bridges; two leaves each
        for x0, x1 in self.spans:
            self.box("join", x0, x1, -IL_T, GAP + OL_T, 0, CT)
            self.box("join", x0, x1, GAP, GAP + OL_T, -OL_H, CT)
        for x0, x1 in self.spans:
            self.box("cut", x0 + BW, x1 - BW, 0, GAP, -1, CT + 1)
        for x0, x1 in self.spans:
            c = BW + 0.8
            for xr, sense in ((x0 + c, 1), (x1 - c, -1)):
                self.xy_poly("join", self.leaf_outline(xr, sense), -OL_H, CT)
        # Band stud on the arch's outer leg (head stepped so it prints without a steep overhang)
        sx, sz = (X0 + X1) / 2, CT - P["STUD_D"] / 2
        y_out = GAP + OL_T
        sh = P["STUD_SHAFT"]
        self.y_cyl("join", sx, sz, y_out - 0.2, y_out + sh, P["STUD_D"])
        for i, f in enumerate((0.33, 0.67, 1.0)):
            d = P["STUD_D"] + (P["STUD_HEAD_D"] - P["STUD_D"]) * f
            self.y_cyl("join", sx, sz, y_out + sh - 0.01 + i / 3, y_out + sh + (i + 1) / 3, d)
        self.y_cyl("join", sx, sz, y_out + sh + 0.98, y_out + sh + 1.8, P["STUD_HEAD_D"])
        cuts = [("box", sx - 4, sx + 4, y_out, y_out + 6, CT, CT + 4)]
        # Ear arm, gusset and sensor pod
        if self.with_arm:
            WALL, lip = P["WALL"], P["POD_LIP"]
            aw, at = P["ARM_W"], P["ARM_T"]
            px, pz = X0 + aw / 2, -P["POD_DEPTH"]
            y0 = -IL_T
            y1 = y0 + lip + P["BOARD_T"] + P["BOARD_FRONT"] + lip
            hl, hh = P["BOARD_L"] / 2 + 0.2, P["BOARD_H"] / 2 + 0.2
            top = pz + hh + WALL
            pw = hl + WALL
            zg = top + pw - aw / 2
            dy = y1 - y0 - at
            self.box("join", px - aw / 2, px + aw / 2, y0, y0 + at, zg - 0.5, self.IL_Z0 + 0.5)
            self.xz_poly("join", [(px - aw / 2, zg), (px + aw / 2, zg), (px + pw, top - 0.5), (px - pw, top - 0.5)], y0, y1)
            self.yz_poly("join", [(y0 + at - 0.01, zg - 0.01), (y1, zg - 0.01), (y0 + at - 0.01, zg + dy)],
                         px - aw / 2, px + aw / 2)
            self.box("join", px - pw, px + pw, y0, y1, pz - hh - WALL, top)
            rim = P["POD_RIM"]
            cuts.append(("box", px - hl, px + hl, y0 + lip, y1 - lip, pz - hh - WALL - 1, pz + hh))
            cuts.append(("box", px - hl + rim, px + hl - rim, y0 - 1, y0 + lip + 0.01, pz - hh - WALL - 1, pz + hh - rim))
            cuts.append(("box", px - hl + rim, px + hl - rim, y1 - lip - 0.01, y1 + 1, pz - hh - WALL - 1, pz + hh - rim))
            cuts.append(("box", px + hl - 0.1, px + pw + 1, y0 + lip, y1 - lip, pz + hh - 6, pz + hh))
        # Open LED channel, corner floor and slots, lead-in ramps under the leaves
        cd = self.CH_D
        cuts.append(("box", TE - 1, self.FLAP_X1 + 1, -IL_T - 1, -IL_T + cd, self.CH_Z0, self.CH_Z1))
        cuts.append(("box", X0 - 1, X1 + 1, -IL_T - 1, -IL_T + cd, self.CH_Z0, self.CH_Z1))
        cuts.append(("box", -P["CLIP_FRONT"], P["CORNER_X1"], -(P["FLOOR"] - P["CORNER_FLOOR"]), 1, self.IL_Z0 - 1, CT + 1))
        for x in self.kerf_positions():
            cuts.append(("box", x, x + P["KERF_W"], -IL_T - 1, -P["FLOOR"], self.IL_Z0 - 1, self.CH_Z0 + 0.01))
            cuts.append(("box", x, x + P["KERF_W"], -IL_T - 1, -P["FLOOR"], self.CH_Z1 - 0.01, CT + 1))
        ramp = [(GAP, -OL_H), (0.2, -OL_H + (GAP - 0.2) * P["RAMP"]), (0.2, -OL_H - 1), (GAP, -OL_H - 1)]
        for x0, x1 in self.spans:
            cuts.append(("ramp", ramp, x0 + BW, x1 - BW))

        # Cavities after all solids, so no solid refills them
        for c in cuts:
            if c[0] == "box":
                self.box("cut", *c[1:])
            else:
                self.yz_poly("cut", *c[1:])
        # Lips at the channel mouth, after the channel is cut
        for x in self.lip_positions():
            for z0, z1 in ((self.CH_Z0 - 0.3, self.CH_Z0 + P["LIP"]), (self.CH_Z1 - P["LIP"], self.CH_Z1 + 0.3)):
                self.box("join", x - P["LIP_L"] / 2, x + P["LIP_L"] / 2, -IL_T, -IL_T + P["LIP_T"], z0, z1)
        if self.with_arm:   # Pod detents, below the board's bottom edge
            lip, rim, WALL = P["POD_LIP"], P["POD_RIM"], P["WALL"]
            px, pz = X0 + P["ARM_W"] / 2, -P["POD_DEPTH"]
            y1 = -IL_T + lip + P["BOARD_T"] + P["BOARD_FRONT"] + lip
            hl, hh = P["BOARD_L"] / 2 + 0.2, P["BOARD_H"] / 2 + 0.2
            for xa, xb in ((px - hl - 0.3, px - hl + rim), (px + hl - rim, px + hl + 0.3)):
                self.box("join", xa, xb, y1 - lip - P["POD_DETENT"], y1 - lip + 0.3, pz - hh - WALL, pz - hh - 0.2)
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


def tray_steps(P, comp, port=True, switch=False, wire_exit="sides"):
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
    pw, ph = P["PASS_W"], P["PASS_H"]
    if wire_exit == "sides":
        s.append(("cut", "tray", rect(-pw / 2, pw / 2, -ow / 2 - R - 1, ow / 2 + R + 1), oh - ph, oh + 1))
    else:
        s.append(("cut", "tray", rect(-ol / 2 - R - 1, -ol / 2 + TW + 1, -pw / 2, pw / 2), oh - ph, oh + 1))
    return s


def socket_steps(P, comp, port, body, switch=False, wire_exit="sides"):
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
    pw, ph = P["PASS_W"], P["PASS_H"]
    if wire_exit == "sides":
        s.append(("cut", body, rect(-pw / 2, pw / 2, -sw / 2 - 1, sw / 2 + 1), -1, ph))
    else:
        s.append(("cut", body, rect(-sl / 2 - 1, -ol / 2 + 1, -pw / 2, pw / 2), -1, ph))
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
        sock, sl, sw = socket_steps(P, comp, port, "socket", wire_exit="end")
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
        "tray battery": tray_steps(P, (P["BATT_L"] + P["BATT_LEAD"], P["BATT_W"], P["BATT_H"]), port=False, wire_exit="end"),
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

    AXES = {"x": 0, "y": 1, "z": 2}

    def __init__(self, comp):
        self.comp = comp
        self.planes = {}
        self.bodies = {}
        self.base = {"x": comp.yZConstructionPlane, "y": comp.xZConstructionPlane, "z": comp.xYConstructionPlane}
        self.sense = {}

    @staticmethod
    def _point(axis, u, v, w):
        """Profile point (u, v) on the plane at w along axis, in mm -> model (x, y, z)."""
        return {"z": (u, v, w), "x": (w, u, v), "y": (u, w, v)}[axis]

    def _normal_sign(self, axis):
        """+1 if the base plane's normal and its sketches' normals point along +axis, else -1.
        Read from Fusion, not assumed: extrudes then run the intended way on every plane."""
        if axis not in self.sense:
            i = self.AXES[axis]
            n = self.base[axis].geometry.normal
            sk = self.comp.sketches.add(self.base[axis])
            sn = sk.xDirection.crossProduct(sk.yDirection)
            sk.deleteMe()
            self.sense[axis] = (1.0 if n.asArray()[i] > 0 else -1.0, 1.0 if sn.asArray()[i] > 0 else -1.0)
        return self.sense[axis]

    def plane(self, axis, w):
        key = (axis, round(w, 4))
        if key not in self.planes:
            if abs(w) < 1e-9:
                self.planes[key] = self.base[axis]
            else:
                inp = self.comp.constructionPlanes.createInput()
                offset = w * self._normal_sign(axis)[0]
                inp.setByOffset(self.base[axis], adsk.core.ValueInput.createByReal(offset / 10.0))
                pl = self.comp.constructionPlanes.add(inp)
                pl.isLightBulbOn = False
                self.planes[key] = pl
        return self.planes[key]

    def profile(self, prof, axis, w):
        sk = self.comp.sketches.add(self.plane(axis, w))
        sk.isComputeDeferred = True

        def pt(u, v):
            x, y, z = self._point(axis, u, v, w)
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
        kind, body, prof, z0, z1 = st[:5]
        axis = st[5] if len(st) > 5 else "z"
        if axis not in self.sense:
            self._verify(axis)
        op = {"new": F.NewBodyFeatureOperation, "join": F.JoinFeatureOperation, "cut": F.CutFeatureOperation}[kind]
        self._extrude(op, prof, axis, z0, z1, body if kind != "new" else None)
        feat = self.last
        if kind == "new":
            b = feat.bodies.item(0)
            b.name = body
            self.bodies[body] = b
            self._check(b, axis, z0, z1, body)

    def _extrude(self, op, prof, axis, z0, z1, body):
        # Extrudes run along the sketch normal: start from whichever end that normal points away from
        start = z0 if self._normal_sign(axis)[1] > 0 else z1
        ext = self.comp.features.extrudeFeatures
        ei = ext.createInput(self.profile(prof, axis, start), op)
        ei.setDistanceExtent(False, adsk.core.ValueInput.createByReal((z1 - z0) / 10.0))
        if body is not None:
            ei.participantBodies = [self.bodies[body]]
        self.last = ext.add(ei)

    def _verify(self, axis):
        """Before the first step on a plane, extrude a test block 1..2 mm off it and check where it lands."""
        self._extrude(adsk.fusion.FeatureOperations.NewBodyFeatureOperation, rect(1, 2, 1, 2), axis, 1.0, 2.0, None)
        b = self.last.bodies.item(0)
        try:
            self._check(b, axis, 1.0, 2.0, "test block")
        finally:
            self.last.deleteMe()

    def _check(self, b, axis, z0, z1, name):
        """Stop if a new body doesn't span z0..z1 along its axis."""
        i = self.AXES[axis]
        lo = b.boundingBox.minPoint.asArray()[i] * 10.0
        hi = b.boundingBox.maxPoint.asArray()[i] * 10.0
        if abs(lo - z0) > 0.05 or abs(hi - z1) > 0.05:
            raise RuntimeError("Extrude landed in the wrong place for {} ({:.2f}..{:.2f} mm along {}, "
                               "expected {:.2f}..{:.2f}). Please report this.".format(name, lo, hi, axis, z0, z1))


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
