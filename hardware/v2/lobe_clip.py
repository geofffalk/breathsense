"""
BreathSense v2 earlobe clip: one soft-flex part that fits any adult earlobe.

The magnets set where the sensor sits, so nothing about the clip's shape has to match the lobe:
- Back pad (behind the lobe): the MAX30101 board, sensor window toward the lobe. A stack of
  magnets sits directly behind the sensor chip, so the pinch presses the chip itself onto the
  skin; a tug on the lead can't peel the chip away first, as it would if the magnets were below.
  The board goes in from the back past soft lips, its chip standing proud of the pad's face; a
  flap on a living hinge folds over the back and presses in, holding the magnets against the
  board. The wires leave from the pins at the board's bottom, out through the rear wall.
- Keeper strap: a flat floppy strap from the pad's bottom edge, round whatever free edge the lobe
  has (under a free lobe; round the back edge of an attached one) and up the front to the front
  puck, whose magnets pull through the lobe onto the pad's. A lid on a living hinge at the
  puck's side folds over its outer face, with a plug pressing into the magnet pocket, so the
  magnets can't drop out when the clip is off. It doesn't set the height: it's long
  enough for the longest, thickest lobe with the chip high on it, and on smaller lobes the spare
  length hangs as a loop under the lobe.
- Lead: 4 loose silicone wires, not a printed tether, long enough to reach any lobe from the pod
  with slack (see assembly_onepiece.py for the check).

Sized for adult lobes about 13-27 mm tall (intertragic notch to the bottom; mean about 19-20 mm)
and 2.5-8 mm thick. Prints flat on the skin side with no supports: pad, strap, puck and the open
flap and lid all start on the bed.

Coordinates (worn, right ear): x forward, y outward (away from the head), z up. The lobe's back
face is y = 0, so the pad is at y < 0 and the lobe and puck at y > 0. The chip is at x = z = 0.

Run:  python lobe_clip.py   -> out/step/lobe_clip.step, out/stl/lobe_clip.stl
"""

import math
import sys
from pathlib import Path

from build123d import Pos, Rot, export_step, export_stl

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
sys.path.insert(0, str(Path(__file__).parent))
import mount_v2 as mv        # noqa: E402
from glasses_mount import box, y_cyl, yz_prism   # noqa: E402

OUT = Path(__file__).parent / "out"

MAX_BOARD = (19.0, 19.0, 1.6, 1.55)   # Pimoroni MAX30101 breakout: width, height, PCB, chip height (every part on its sensor face)
BOARD_TAB = (15.0, 5.0)      # Its bottom narrows to this width for this height: the pin holes, wired from the back
CHIP_OFFSET = (0.0, 7.2)     # Sensor chip's centre from the board's centre (x across, z up): at the top edge
CHIP_PROUD = 0.5             # Chip's face stands this far proud of the pad's skin face, so it presses into the lobe
MAGNET_D, MAGNET_T = 9.5, 0.8
MAGNETS = 3                  # Per side. Pinch about 1.3 N on a 2.5 mm lobe, 0.3 N on an 8 mm one
STACK = MAGNETS * MAGNET_T + 0.1

LOBE_T = (2.5, 8.0)          # Thinnest and thickest lobes it's sized for
LOBE_H = (13.0, 27.0)        # Shortest and longest
CHIP_BELOW_NOTCH = 6.0       # Highest the chip goes: this far below the notch, still on lobe tissue

# Back pad, from the skin outward (toward the head, -y)
WALL = 1.2                   # Side walls round the board
RIM_W = 0.8                  # Front rims over the board's side edges, above the tab
CORNER = (3.5, 1.5)          # Front tabs over the board's top corners (round its mounting holes, clear of the
                             # chip): width in from the side, depth down from the top
TAB_COVER = BOARD_TAB[1] - 0.5   # Front cover over the tab, up from its bottom edge (stops short of the parts)
PIN_ROW = 1.3                # Pins' centres above the board's bottom edge ...
PIN_RECESS = (2.4, 0.5)      # ... with a recess in the cover's back face for solder that wicks through: height, depth
POCKET_FIT = 0.1             # Board pocket over the board, each side
BOARD_GAP = 0.1
LIP_T = 1.4                  # Back lips over the board's side edges (above the tab); room behind the board
LIP_W = 1.0                  # Lips overlap the board's edges this much
FLAP_T = 1.6                 # Flap's cover plate, on the lips
WIRE_RECESS = 0.8            # Cover plate is this much thinner over the tab, for the wires off the pins
PLUG_W = 1.0                 # Flap's press-in bars, inside the side lips
PLUG_H = 1.0
PLUG_FIT = 0.05              # Bars are this much wider apart than the lips' opening, each side
BOSS_D = MAGNET_D + 1.6      # Flap's magnet boss, down onto the board's back
LEAD_SLOT = 4.4              # Lead's 4 wires (1 mm) out through the rear wall beside the tab: this tall, and
                             # the pocket's full depth plus the recess (3.9 mm)
HINGE_L = 8.5                # Living hinge, flat, from the pad's side to the open flap
HINGE_T = 0.6
HINGE_W = 10.0

# Keeper strap and front puck
STRAP_T = 1.0
STRAP_W = 8.0
PUCK_D = 14.0                # Wide, to spread the pinch on a thin lobe
PUCK_SKIN = 0.6              # Between the puck's magnets and the lobe
PUCK_LIP = 0.5               # Retaining lip over the magnets (they snap in past it)
PUCK_T = PUCK_SKIN + STACK + PUCK_LIP
LID_T = 0.8                  # Puck's lid over its outer face ...
LID_PLUG_FIT = 0.1           # ... with a plug this much over the lip's opening, filling it down to the magnets
LID_HINGE = (4.5, 6.0, 0.6)  # Lid's living hinge at the puck's forward side: gap as printed, width, thickness

bl, bh, bt, bf = MAX_BOARD
HL, HH = bl / 2 + POCKET_FIT, bh / 2 + POCKET_FIT   # Board pocket half sizes
TW = BOARD_TAB[0] / 2 + POCKET_FIT                   # Tab's half width, with clearance
PX0, PX1 = -CHIP_OFFSET[0] - HL - WALL, -CHIP_OFFSET[0] + HL + WALL   # Pad's extent, x
PZ0, PZ1 = -CHIP_OFFSET[1] - HH - WALL, -CHIP_OFFSET[1] + HH + WALL   # ... and z
BCX, BCZ = -CHIP_OFFSET[0], -CHIP_OFFSET[1]          # Board's centre
Z_SHOULDER = BCZ - HH + BOARD_TAB[1]                 # Where the tab widens to the full board
Y_PCB_FRONT = CHIP_PROUD - bf
Y_PCB_BACK = Y_PCB_FRONT - bt
Y_BOARD = (Y_PCB_BACK - BOARD_GAP, Y_PCB_FRONT)      # Board pocket
Y_LIPS = Y_BOARD[0] - LIP_T                          # Lips' back face
Y_BACK = Y_LIPS - FLAP_T                             # Pad's back face, flap closed
PAD_T = -Y_BACK
MAG_Z = min(0.0, BCZ + HH - 0.2 - BOSS_D / 2)        # Magnets' centre: on the chip if they fit, else as high as
                                                     # the pocket's top lets them (still over the chip)
GAP_EXTRA = -Y_PCB_BACK + PUCK_SKIN                  # Magnet gap = lobe thickness + this
LEAD_OUT = (PX0, (Y_LIPS + Y_BOARD[1]) / 2, BCZ - HH + BOARD_TAB[1] / 2)   # Where the lead leaves the pad


def strap_len():
    """Pad's bottom edge to the puck's centre, for the longest, thickest lobe with the chip at
    its highest: down to the bend, which wraps the lobe's bottom (centred half its thickness up),
    round it, and up to the chip's height, plus 4 mm."""
    t = LOBE_T[1]
    bend_z = -(LOBE_H[1] - CHIP_BELOW_NOTCH) + t / 2      # Bend's centre, chip at z = 0
    down = max(PZ0 - bend_z, 0)
    return down + math.pi * (t + STRAP_T) / 2 + (MAG_Z - bend_z) + 4.0


STRAP_L = strap_len()


def pad():
    """Back pad, flap open (not included). The board sits in it sensor face first, held in front
    by rims along its side edges, tabs over its top corners and a cover over its pin tab, and behind
    by lips along its side edges; the window is open over the chip and the parts. Beside the tab
    the pocket is open behind the board but closed in front: the wires come off the pins' backs,
    along behind the tab and out through the rear wall."""
    p = box(PX0, PX1, Y_LIPS, 0, PZ0, PZ1)
    p -= box(BCX - HL, BCX + HL, *Y_BOARD, BCZ - HH, BCZ + HH)                               # Board
    z0 = BCZ - HH + POCKET_FIT + TAB_COVER
    cw, cd = CORNER
    win = box(BCX - HL + RIM_W, BCX + HL - RIM_W, Y_BOARD[1] - 0.01, 1, Z_SHOULDER, BCZ + HH)
    win += box(BCX - TW, BCX + TW, Y_BOARD[1] - 0.01, 1, z0, Z_SHOULDER + 0.01)
    for s in (-1, 1):
        win -= box(*sorted((BCX + s * HL, BCX + s * (HL - cw))), Y_BOARD[1] - 1, 2, BCZ + HH - cd, BCZ + HH + 1)
    p -= win                                                                                   # Sensor window
    rh, rd = PIN_RECESS
    zp = BCZ - HH + POCKET_FIT + PIN_ROW
    p -= box(BCX - TW + 0.5, BCX + TW - 0.5, Y_BOARD[1] - 0.01, Y_BOARD[1] + rd, zp - rh / 2, zp + rh / 2)   # Pins' solder
    p -= box(BCX - HL + LIP_W, BCX + HL - LIP_W, Y_LIPS - 1, Y_BOARD[0] + 0.01, Z_SHOULDER, BCZ + HH)   # Back opening ...
    p -= box(BCX - HL, BCX + HL, Y_LIPS - 1, Y_BOARD[0] + 0.01, BCZ - HH, Z_SHOULDER + 0.01)          # ... behind the tab
    zl = LEAD_OUT[2]
    p -= box(PX0 - 1, BCX - HL + 0.01, Y_LIPS - 1, Y_BOARD[1], zl - LEAD_SLOT / 2, zl + LEAD_SLOT / 2)  # Lead, rear wall
    return p


def flap_closed():
    """The flap where it sits when closed: cover plate on the lips (recessed over the tab for the
    wires), press-in bars inside the side lips, and the magnet boss down onto the board's back,
    holding the stack against it."""
    f = box(PX0, PX1, Y_BACK, Y_LIPS, PZ0, PZ1)
    f -= box(BCX - HL, BCX + HL, Y_LIPS - WIRE_RECESS, Y_LIPS + 1, BCZ - HH, Z_SHOULDER)       # Wires' recess ...
    zl = LEAD_OUT[2]
    f -= box(PX0 - 1, BCX - HL + 0.01, Y_LIPS - WIRE_RECESS, Y_LIPS + 1,
             zl - LEAD_SLOT / 2, zl + LEAD_SLOT / 2)                                           # ... out to the lead's slot
    for s in (-1, 1):
        xo = BCX + s * (HL - LIP_W + PLUG_FIT)
        f += box(*sorted((xo, xo - s * PLUG_W)), Y_LIPS, Y_LIPS + PLUG_H, Z_SHOULDER + 0.5, BCZ + HH - 0.5)
    f += y_cyl(0, MAG_Z, Y_LIPS - 0.01, Y_PCB_BACK - 0.05, BOSS_D)
    f -= y_cyl(0, MAG_Z, Y_PCB_BACK - STACK, Y_PCB_BACK + 1, MAGNET_D + 0.25)                 # Magnets, against the board
    return f


HINGE_AXIS = (PX1 + HINGE_L / 2, Y_BACK / 2)


def open_flap(f):
    """Closed flap -> lying open beside the pad, its outer face on the skin-side plane."""
    xa, ya = HINGE_AXIS
    return Pos(xa, ya, 0) * (Rot(0, 0, 180) * (Pos(-xa, -ya, 0) * f))


def hinge_flat():
    return box(PX1 - 0.5, PX1 + HINGE_L + 0.5, -HINGE_T, 0, BCZ - HINGE_W / 2, BCZ + HINGE_W / 2)


def hinge_closed():
    return box(PX1 - 0.3, PX1 + HINGE_T, Y_BACK, 0, BCZ - HINGE_W / 2, BCZ + HINGE_W / 2)


def puck(y_skin, z, outward):
    """Front puck centred at (0, z), its skin face at y_skin, built toward -y (outward=False, as
    printed) or +y (outward=True, folded onto the lobe). Magnets snap in from its outer face."""
    s = 1 if outward else -1
    ys = lambda a, b: sorted((y_skin + s * a, y_skin + s * b))
    p = y_cyl(0, z, *ys(0, PUCK_T), PUCK_D)
    p -= y_cyl(0, z, *ys(PUCK_SKIN, PUCK_SKIN + STACK), MAGNET_D + 0.1)
    p -= y_cyl(0, z, *ys(PUCK_SKIN + STACK - 0.01, PUCK_T + 1), MAGNET_D - 0.7)               # Retaining lip
    return p


def puck_lid(y_skin, z, outward):
    """The puck's lid closed on its outer face, its plug in the lip's opening, plus the hinge
    down the puck's forward side (+x). Same frame and sides as puck()."""
    s = 1 if outward else -1
    ys = lambda a, b: sorted((y_skin + s * a, y_skin + s * b))
    f = y_cyl(0, z, *ys(PUCK_T - 0.01, PUCK_T + LID_T), PUCK_D)
    f += y_cyl(0, z, *ys(PUCK_T - PUCK_LIP, PUCK_T), MAGNET_D - 0.7 + LID_PLUG_FIT)
    hw, ht = LID_HINGE[1], LID_HINGE[2]
    f += box(PUCK_D / 2 - 1.0, PUCK_D / 2 + ht, *ys(0, PUCK_T + LID_T), z - hw / 2, z + hw / 2)
    return f


def puck_lid_open(z):
    """As printed: the lid lying on the bed beside the puck (+x), plug up, joined by a flat hinge."""
    gap, hw, ht = LID_HINGE
    xa, ya = (PUCK_D + gap) / 2, -(PUCK_T + LID_T) / 2           # Fold axis, along z
    lid = y_cyl(0, z, -(PUCK_T + LID_T), -(PUCK_T - 0.01), PUCK_D)
    lid += y_cyl(0, z, -PUCK_T - 0.01, -(PUCK_T - PUCK_LIP), MAGNET_D - 0.7 + LID_PLUG_FIT)
    lid = Pos(xa, ya, z) * (Rot(0, 0, 180) * (Pos(-xa, -ya, -z) * lid))
    xi = math.sqrt((PUCK_D / 2) ** 2 - (hw / 2) ** 2) - 0.3        # Inside both discs' edges
    return lid + box(xi, PUCK_D + gap - xi, -ht, 0, z - hw / 2, z + hw / 2)


def clip_flat():
    """As printed: pad, strap straight down from its bottom edge, puck at the strap's end, flap
    open beside the pad. Everything's skin side is on y = 0."""
    c = pad()
    z_end = PZ0 - STRAP_L
    c += box(-STRAP_W / 2, STRAP_W / 2, -STRAP_T, 0, z_end, PZ0 + 0.5)
    c += puck(0, z_end, outward=False)
    c += puck_lid_open(z_end)
    c += hinge_flat()
    c += open_flap(flap_closed())
    return c


def yz_band(path, width, x0, x1):
    """A strip of the given thickness along a (y, z) polyline, spanning x0..x1."""
    left, right = [], []
    for i, (y, z) in enumerate(path):
        ya_, za_ = path[max(i - 1, 0)]
        yb_, zb_ = path[min(i + 1, len(path) - 1)]
        dy, dz = yb_ - ya_, zb_ - za_
        L = math.hypot(dy, dz)
        ny, nz = -dz / L * width / 2, dy / L * width / 2
        left.append((y + ny, z + nz))
        right.append((y - ny, z - nz))
    return yz_prism(left + right[::-1], x0, x1)


def clip_worn(lobe_t, lobe_bottom):
    """Folded onto a lobe of thickness lobe_t whose bottom is at z = lobe_bottom (chip at z = 0):
    strap down from the pad, round under the lobe (hanging as low as its spare length takes it),
    up the front, puck opposite the chip. Returns (clip, how far the loop hangs below the lobe)."""
    r = (lobe_t + STRAP_T) / 2
    yc = lobe_t / 2
    # Down e, half round, up to the magnets: e + pi r + (MAG_Z - (PZ0 - e)) = STRAP_L
    e = (STRAP_L - math.pi * r - MAG_Z + PZ0) / 2
    zf = PZ0 - e
    n = 24
    path = [(-STRAP_T / 2 - 0.1, PZ0 + 1.0), (-STRAP_T / 2 - 0.1, zf + 0.5)]   # Just inside the pad's face: no coplanar faces
    path += [(yc - r * math.cos(math.pi * i / n), zf - r * math.sin(math.pi * i / n)) for i in range(1, n)]
    path += [(lobe_t + STRAP_T / 2, zf), (lobe_t + STRAP_T / 2, MAG_Z)]
    c = pad() + flap_closed() + hinge_closed()
    c += puck(lobe_t, MAG_Z, outward=True) + puck_lid(lobe_t, MAG_Z, outward=True)
    c += yz_band(path, STRAP_T, -STRAP_W / 2, STRAP_W / 2)
    return c, (lobe_bottom - (zf - r - STRAP_T / 2))


def lobe(t, h, w, z_bottom):
    """Reference earlobe: a slab with a rounded bottom, back face on y = 0, centred on x = 0."""
    n = 16
    pts = [(-w / 2, z_bottom + h)]
    pts += [(-w / 2 * math.cos(math.pi * i / n), z_bottom + w / 2 - w / 2 * math.sin(math.pi * i / n))
            for i in range(n + 1)]
    pts += [(w / 2, z_bottom + h)]
    from glasses_mount import xz_prism
    m = 12
    edge = [(t / 2 - t / 2 * math.cos(math.pi * i / m), z_bottom + t / 2 - t / 2 * math.sin(math.pi * i / m))
            for i in range(m + 1)]                            # Rounded bottom edge, across its thickness
    return xz_prism(pts, 0, t) & yz_prism([(0, z_bottom + h)] + edge + [(t, z_bottom + h)], -w, w)


def print_orient(p):
    """Skin side down."""
    return mv._to_bed(Rot(-90, 0, 0) * p)


if __name__ == "__main__":
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    c = clip_flat()
    export_step(c, str(OUT / "step" / "lobe_clip.step"))
    export_stl(print_orient(c), str(OUT / "stl" / "lobe_clip_flex.stl"))
    print(f"wrote lobe_clip {c.volume:.0f} mm3; strap {STRAP_L:.1f} mm; pad {PX1 - PX0:.1f} x {PZ1 - PZ0:.1f} x {PAD_T:.1f} mm")
