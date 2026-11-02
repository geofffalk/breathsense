"""
BreathSense v2 pods that hang off the ends of the temple tips, behind the earlobes.

The tip ends in a paddle that grows from 6.3 mm tall 20 mm back to 8.5 mm at its end (measured),
4.0 mm thick throughout. Each pod has a rigid PETG pocket shaped to the paddle's last GRIP_L,
lined with soft flex, that wraps both faces and the edge nearest the ear. The paddle's wide end
sits in the pocket's wide end and can't pass back through the narrower neck, and its end stops
against the pod's body, so the pod can't slide along the tip either way. The pod goes on from
the paddle's back edge (the edge away from the ear when worn); gravity then pulls the paddle
into the pocket, and a soft-flex band, a closed loop round the whole pocket, holds it there. The
band sits in a groove round the pocket so it stands only a little proud. The rail's wires run
along the back edge, in a channel under the band, into the body. The band goes onto the temple
over its tip before the pod, then rolls back along the paddle into its groove.

The body carries on past the tip's end along the same line, down onto the bone behind the
earlobe, so the pod doesn't rise above the ear.
- Board pod (right): the XIAO under a soft-flex lid, USB-C out of the far end (down and back
  when worn); the button and the nose clip's magnetic pogo socket side by side in the back wall; the
  earlobe lead out of the ear-side wall.
- Battery pod (left): the 502030 cell under a lid; the cord out of the far end.

Coordinates as worn on the right temple, in the straight frame (ear bend not applied): the tip
runs from x = -TEMPLE_STRAIGHT toward -x and ends at TIP_END_X; y outward from its inner face;
z up, its top edge at z = 0. When worn and bent down, +z is the side away from the ear and -z
the side toward it. No z-flip is needed (unlike mount_v2's pods).

Run:  python hang_pods.py   -> out/step/hang_*.step, out/stl/hang_*.stl
"""

import sys
from pathlib import Path

from build123d import Cylinder, Plane, Pos, Rot, export_step, export_stl, mirror

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
sys.path.insert(0, str(Path(__file__).parent))
import glasses_mount as gm   # noqa: E402
import lobe_clip as lc       # noqa: E402
import mount_v2 as mv        # noqa: E402
from glasses_mount import box, xz_prism, yz_prism   # noqa: E402

OUT = Path(__file__).parent / "out"

# ---------------------------------------------------------------- the paddle (measured)
TIP_END_X = -gm.TEMPLE_STRAIGHT - gm.TIP_LEN
TIP_T = 4.0              # Thickness, constant
PADDLE = [(0.0, 8.5), (10.0, 6.5), (20.0, 6.3), (gm.TIP_LEN, gm.REF_TIP[1])]   # (distance back from the end, height)


def paddle_h(d):
    """Paddle height at distance d back from its end (linear between the measurements)."""
    for (d0, h0), (d1, h1) in zip(PADDLE, PADDLE[1:]):
        if d <= d1:
            return h0 + (h1 - h0) * (d - d0) / (d1 - d0)
    return PADDLE[-1][1]


# ---------------------------------------------------------------- pocket and liner
GRIP_L = 22.0            # The pocket covers this much of the paddle, back from its end
GRIP_X1 = TIP_END_X + GRIP_L
W = mv.POD_WALL
POCKET_WALL = 1.6
LINER_T = 1.0            # Soft-flex liner ...
LINER_SQUEEZE = 0.2      # ... inside this much smaller than the paddle on each side it lines ...
LINER_FIT = 0.05         # ... outside this much bigger than the pocket, so it presses in
END_CLEAR = 0.5          # Between the paddle's end and the body
WIRE_D = 1.0
WIRES = 4                # Most wires through any passage: the cord's 4
WIRE_HOLE = (WIRES * WIRE_D + 1.0, 3 * WIRE_D)
CHANNEL_H = 2.2          # Wire channel along the paddle's back edge, between the pocket's walls, under the band

# ---------------------------------------------------------------- band (soft flex)
CLIP_X = TIP_END_X + 15.0   # Band's centre: where the paddle's edge is nearly straight
CLIP_L = 8.0             # Band width along the tip
CLIP_ARM = 1.2           # Band thickness ...
CLIP_GROOVE = 0.7        # ... sunk this deep in a groove round the pocket's faces and ear-side edge (0.5 mm proud) ...
CLIP_GROOVE_TOP = 0.3    # ... and this deep in the walls' top edges, leaving the wires 1.6 mm under it
CLIP_SQUEEZE = 0.3       # Band's inside this much smaller than the groove's floor on every side

# ---------------------------------------------------------------- body
FLANGE_ZONE = 2.0        # Room inside the board pod's ear-side wall for the earlobe lead (held by a dab of glue
                         # inside its hole: a knot needed 3.6 mm)
LEAD_HOLE = 4.0          # Earlobe lead's 4 wires (1 mm), loose, out through the ear-side wall
POGO = (4.0, 1.0, 4.9, 5.0)   # Nose clip's 2-pin magnetic pogo socket (measured): face boss diameter and height (through
                         # the back wall, flush), ring diameter (seats inside), length including the tails
POGO_FIT = 0.1           # Holes this much over its diameters (press it in from inside; a drop of glue if loose)
BUTTON_H = 3.2           # Button's body height (measured; 7.0 with the plunger)
BUTTON_AT = 5.0          # Button's centre from the far end's inside (its 6 mm base clear of the far wall) ...
POGO_AT = 16.5           # ... and the socket's: holes 7.3 mm apart, its ring 2.2 mm short of the XIAO's front end
                         # (past it the switch board's transistors lie against the back wall)
BAY = 17.0               # Board pod's cavity this much longer (16 was a little tight for XIAO + board), at its front beside the XIAO, for the LED switch
                         # on a stripboard (switch_board.svg): about 15 x 22 mm, 1.5 mm thick, parts lying flat
SWITCH_STACK = 5.7       # Switch board's height: solder 0.7, board 1.5, a flat TO-92 3.5
BOARD_LIFT = 1.0         # XIAO raised this much on two rails under its ends: room for the battery wires on its back pads
RAIL_W = 1.5             # ... rails this wide along its length
BUTTON = (6.0, 6.0)      # Omron B3F (measured): 6 x 6 base, across the cavity's depth and along the back wall; body 3.2 tall,
                         # 7.0 with the plunger, so the plunger stands 2.6 mm proud of the back wall ...
BUTTON_ROOM = 6.35       # Between the XIAO's edge and the back wall for the button and its legs: 3.6 let it push the
                         # XIAO 2.5-3 mm toward the ear-side wall (measured). The pogo socket shares it
PLUNGER_HOLE = 4.3       # ... its round plunger (about 3.5 mm) out through the back wall (prints ~0.3 mm small; 3.8 was too tight)

# ---------------------------------------------------------------- head-side sensor (board_pod(sensor="head"))
# The MAX30101 sits in the pocket's head-side wall at the paddle's end, where the temple presses on
# the head: its back on the paddle (the liner cut away there, liner_head()), its sensor-side parts
# out through a window, held by rims in the wall. Its chip edge faces the ear bend; the rest of it
# runs back past the paddle's end under the body's floor, below the bay. It slides in from the
# cavity through a slot in the body's front wall. The temple's own grip presses it on: no springs.
SENSOR_AT = 4.5          # Chip's centre this far from the paddle's end (where the user's temple presses hardest) ...
SENSOR_Z = 0.0           # ... at this height (the paddle's top edge is z = 0; the board spans 9.6 mm either side)
HEAD_DEEPER = 1.6        # Head variant's cavity this much deeper: the switch board's resistor end (4.5 mm: solder,
                         # board, flat resistors) sits over the MAX30101's back and its wires (1.1 mm); its transistor
                         # end goes toward the back wall, past the MAX30101's edge, where the floor is lower


def ys():
    """y extents: (liner inside, liner outside, pocket inside, pocket outside), each (y0, y1)."""
    q, t, f = LINER_SQUEEZE, LINER_T, LINER_FIT
    li = (q, TIP_T - q)
    lo = (li[0] - t, li[1] + t)
    pi = (lo[0] + f, lo[1] - f)
    po = (pi[0] - POCKET_WALL, pi[1] + POCKET_WALL)
    return li, lo, pi, po


def bottom(d, offset):
    """z of the paddle's ear-side edge at distance d back from its end, moved by offset (+ up)."""
    return -paddle_h(d) + offset


def profile_pts(offset, n=22):
    """(x, z) points along the paddle's ear-side edge from its end to the pocket's front."""
    return [(TIP_END_X + GRIP_L * i / n, bottom(GRIP_L * i / n, offset)) for i in range(n + 1)]


def pocket(depth):
    """The rigid pocket, joined to the body's front wall. Returns (solid, dims)."""
    li, lo, pi, po = ys()
    in_off = LINER_SQUEEZE - LINER_T + LINER_FIT         # Pocket inside, relative to the paddle's edge
    y1 = max(po[1], po[0] + W + depth + mv.LID_T)
    x_end = TIP_END_X - END_CLEAR                         # The body's front face
    outer = profile_pts(in_off - POCKET_WALL)
    p = xz_prism([(x_end - 0.01, CHANNEL_H)] + [(GRIP_X1, CHANNEL_H)] + outer[::-1] + [(x_end - 0.01, outer[0][1])],
                 po[0], y1)
    cav = profile_pts(in_off)
    p -= xz_prism([(x_end, CHANNEL_H + 1)] + [(GRIP_X1 + 1, CHANNEL_H + 1), (GRIP_X1 + 1, cav[-1][1])]
                  + cav[::-1] + [(x_end, cav[0][1])], *pi)
    # Band's groove, right round: both faces, the ear-side edge and the walls' top edges
    ga, gb = CLIP_X - CLIP_L / 2 - 0.2, CLIP_X + CLIP_L / 2 + 0.2
    g = CLIP_GROOVE
    groove = box(ga, gb, po[0] - 1, y1 + 1, band_floor() - 5, CHANNEL_H + 1)
    groove -= box(ga - 1, gb + 1, po[0] + g, y1 - g, band_floor() + g, CHANNEL_H - CLIP_GROOVE_TOP)
    p -= groove
    return p, dict(y0=po[0], y1=y1, x_end=x_end, z_low=outer[0][1], pocket_in=pi)


def band_floor():
    """The pocket's ear-side outer face under the band, at its higher end (so the groove is at
    least CLIP_GROOVE deep all along)."""
    in_off = LINER_SQUEEZE - LINER_T + LINER_FIT
    return max(bottom(d, in_off - POCKET_WALL) for d in (CLIP_X - TIP_END_X - CLIP_L / 2 - 0.2,
                                                         CLIP_X - TIP_END_X + CLIP_L / 2 + 0.2))


def liner():
    """Soft-flex liner, modelled in place: a U lining the pocket's two faces and its ear-side edge,
    following the paddle's shape."""
    li, lo, _, _ = ys()
    x0, x1 = TIP_END_X, GRIP_X1
    outer = profile_pts(LINER_SQUEEZE - LINER_T)
    inner = profile_pts(LINER_SQUEEZE)
    s = xz_prism([(x0, CHANNEL_H - 0.3), (x1, CHANNEL_H - 0.3)] + outer[::-1], *lo)
    s -= xz_prism([(x0 - 1, CHANNEL_H + 1), (x1 + 1, CHANNEL_H + 1), (x1 + 1, inner[-1][1])] + inner[::-1]
                  + [(x0 - 1, inner[0][1])], *li)
    return s


def back_clip(y0, y1):
    """Soft-flex band at CLIP_X, modelled in place: a closed loop in the pocket's groove, over the
    walls' top edges (and the wire channel between them), down both faces and under the ear-side
    edge."""
    g, sq, a, c = CLIP_GROOVE, CLIP_SQUEEZE, CLIP_ARM, 1.0      # c: outside corner chamfer
    yi0, yi1 = y0 + g + sq, y1 - g - sq
    zi0, zi1 = band_floor() + g + sq, CHANNEL_H - CLIP_GROOVE_TOP - sq
    ya, yb, za, zb = yi0 - a, yi1 + a, zi0 - a, zi1 + a
    outside = [(ya + c, zb), (yb - c, zb), (yb, zb - c), (yb, za + c), (yb - c, za),
               (ya + c, za), (ya, za + c), (ya, zb - c)]
    x0, x1 = CLIP_X - CLIP_L / 2, CLIP_X + CLIP_L / 2
    return (yz_prism(outside, x0, x1)
            - box(x0 - 1, x1 + 1, yi0, yi1, zi0, zi1))


def body(depth, height, length, d, wire_high=False, cord_in=0.3, cord_h=None):
    """The body box past the tip's end, its ear-side face level with the pocket's lowest point.
    wire_high: the rail's wires come in just under the lid, above the switch board in the bay.
    cord_in, cord_h: the cord's hole in the far end starts this far in from the back wall's inside, this tall.
    Returns (solid, cavity, (xf, zb0, zb1))."""
    y0, y1, x_end = d["y0"], d["y1"], d["x_end"]
    zb0 = d["z_low"]
    zb1 = zb0 + height
    xf = x_end - length
    cy0 = y0 + W
    p = box(xf, x_end, y0, y1, zb0, zb1)
    cav = box(xf + W, x_end - W, cy0, y1 + 1, zb0 + W, zb1 - W)
    cav += box(xf + 0.6, x_end - 0.6, y1 - mv.LID_T, y1 + 1, zb0 + 0.6, zb1 - 0.6)          # Lid recess
    # Wires from the channel along the paddle's back edge, through the front wall
    hw, hh = WIRE_HOLE
    yc = (d["pocket_in"][0] + d["pocket_in"][1]) / 2
    if wire_high:
        # Top at the lid's underside, 4 mm tall (clear of the stripboard, 2.2 mm with its solder), and
        # 0.5 mm higher up the back edge, clear of R1's lead
        yt = y1 - mv.LID_T
        cav += box(x_end - W - 0.1, x_end + 0.5, yt - WIRES * WIRE_D, yt, 0.6, 0.6 + hh)
    else:
        cav += box(x_end - W - 0.1, x_end + 0.5, yc - hw / 2, yc + hw / 2, 0.1, 0.1 + hh)
    # Cord, out of the far end, at the back
    ch = hh if cord_h is None else cord_h
    cav += box(xf - 1, xf + W + 0.1, yc - hw / 2, yc + hw / 2, zb1 - W - cord_in - ch, zb1 - W - cord_in)
    return p, cav, (xf, zb0, zb1)


def lid_for(xf, x_end, zb0, zb1, y1):
    return box(xf + 0.6 - mv.LID_FIT, x_end - 0.6 + mv.LID_FIT, y1 - mv.LID_T, y1,
               zb0 + 0.6 - mv.LID_FIT, zb1 - 0.6 + mv.LID_FIT)


def head_frame():
    """Lobe-clip pad frame (skin face y = 0 toward +y, chip at x = z = 0, the board's top edge at
    +z) -> pod frame: skin face toward the head (-y), the board's back on the paddle's face (y = 0),
    its top edge toward the ear bend (+x), chip SENSOR_AT from the paddle's end."""
    cx, cz, ty = TIP_END_X + SENSOR_AT, SENSOR_Z, lc.Y_PCB_BACK
    loc = Plane(origin=(cx, ty, cz), x_dir=(0, 0, 1), z_dir=(1, 0, 0)).location
    return lambda shape: loc * shape, (cx, ty, cz)


def sensor_cuts():
    """Board pocket (carried on past the board's far end, so it slides in from the cavity) and the
    sensor window with rims, corner tabs and the tab cover, as lobe_clip.pad() has, in its frame."""
    HL, HH, BCZ, TW = lc.HL, lc.HH, lc.BCZ, lc.TW
    slide = SENSOR_AT + lc.BCZ + lc.HH + 1.0               # How far it slides from the cavity into the pocket, plus room
    c = box(-HL, HL, *lc.Y_BOARD, BCZ - HH - slide, BCZ + HH)
    z0 = BCZ - HH + lc.POCKET_FIT + lc.TAB_COVER
    cw, cd = lc.CORNER
    yf = lc.Y_BOARD[1]
    win = box(-HL + lc.RIM_W, HL - lc.RIM_W, yf - 0.01, 3, lc.Z_SHOULDER, BCZ + HH)
    win += box(-TW, TW, yf - 0.01, 3, z0, lc.Z_SHOULDER + 0.01)
    for s_ in (-1, 1):
        win -= box(*sorted((s_ * HL, s_ * (HL - cw))), yf - 1, 4, BCZ + HH - cd, BCZ + HH + 1)
    rh, rd = lc.PIN_RECESS
    zp = BCZ - HH + lc.POCKET_FIT + lc.PIN_ROW
    c += box(-TW + 0.5, TW - 0.5, yf - 0.01, yf + rd, zp - rh / 2, zp + rh / 2)                # Pins' solder
    return c + win


def head_footprint():
    """(x0, x1, z0, z1) of the board pocket in the pod frame (x1 at the board's top edge)."""
    _, (cx, _, cz) = head_frame()
    return cx + lc.BCZ - lc.HH, cx + lc.BCZ + lc.HH, cz - lc.HL, cz + lc.HL


def liner_head():
    """The right pod's liner for the head variant: the head-side face cut away over the board."""
    li, lo, _, _ = ys()
    x0, x1, z0, z1 = head_footprint()
    return liner() - box(TIP_END_X - 1, x1 + 0.1, lo[0] - 0.1, li[0] + 0.1, z0 - 0.1, z1 + 0.1)


def xiao_rails(xs, bz, y):
    """Two rails under the XIAO's ends, from y up BOARD_LIFT."""
    w_, length = mv.XIAO[0], mv.XIAO[1] + 0.2
    out = None
    for x0 in (xs, xs + length - RAIL_W):
        r = box(x0, x0 + RAIL_W, y - 0.01, y + BOARD_LIFT, bz - w_ / 2, bz + w_ / 2)
        out = r if out is None else out + r
    return out


def board_pod(sensor="lobe"):
    """Right pod. Returns (pod, lid, dims); dims["lead_exit"] is where the earlobe lead leaves.
    sensor="lobe": the MAX30101 is on the earlobe clip, its lead out of the ear-side wall.
    sensor="head": it sits in the pocket's head-side wall at the paddle's end (see head_frame()),
    with liner_head() in place of the liner; no earlobe lead."""
    w_, length, pcb, usb_h = mv.XIAO
    depth = BOARD_LIFT + pcb + usb_h + 0.4 + (HEAD_DEEPER if sensor == "head" else 0.0)
    p, d = pocket(depth)
    height = 2 * W + FLANGE_ZONE + (w_ + 0.4) + BUTTON_ROOM   # Ear-side wall, lead's knot, board, button, back wall
    b, cav, (xf, zb0, zb1) = body(depth, height, length + 0.2 + 2 * W + BAY, d, wire_high=True,
                              cord_in=BUTTON_H + 0.3, cord_h=2.6)   # Cord between the button and the XIAO's edge
    p += b
    y0, y1, x_end = d["y0"], d["y1"], d["x_end"]
    cy0 = y0 + W
    board_y = cy0 + BOARD_LIFT                             # XIAO's underside
    bz = zb0 + W + FLANGE_ZONE + (w_ + 0.4) / 2            # Board's centre (across)
    xs = xf + W                                            # Board's far end (USB-C end)
    cav += box(xf - 1, xf + W + 0.1, board_y + pcb - 0.2, board_y + pcb + usb_h + 0.4,
               bz - mv.USB_W / 2 - 0.2, bz + mv.USB_W / 2 + 0.2)                                 # USB-C, far end
    bx = xf + W + BUTTON_AT
    # Button plunger, back wall: centred on the wall's outer face, kept where the button's base still fits
    # between the floor and the lid
    by = min(max((y0 + y1) / 2, cy0 + BUTTON[0] / 2), y1 - mv.LID_T - BUTTON[0] / 2)
    cav += Pos(bx, by, zb1 - W / 2) * Cylinder(PLUNGER_HOLE / 2, W + 0.4)
    lx = x_end - W - 6.4 - BAY                             # Lead near the board's front: closest to the earlobe
    ly = (cy0 + y1 - mv.LID_T) / 2
    # Nose clip's socket in the back wall beside the button, toward the bay: the boss through a hole, flush,
    # the ring in a counterbore from inside so the wall left under it is the boss's height
    boss, boss_h, ring, _ = POGO
    px = xf + W + POGO_AT
    cav += Pos(px, by, zb1 - W / 2) * Cylinder((boss + POGO_FIT) / 2, W + 0.4)
    cav += Pos(px, by, zb1 - boss_h - 0.5) * Cylinder((ring + POGO_FIT) / 2, 1.0)
    if sensor != "head":
        cav += Pos(lx, ly, zb0 + W / 2) * Cylinder(LEAD_HOLE / 2, W + 0.4)                     # Earlobe lead
    if sensor == "head":
        place, (cx, ty, cz) = head_frame()
        fx0, fx1, fz0, fz1 = head_footprint()
        # Wall round the board where it runs past the pocket's top and bottom edges: the head-side
        # wall carried on, with a backing behind the board clear of the paddle and its liner
        xr = fx1 + W
        p += box(x_end - 0.01, xr, y0, -0.75, fz0 - W, fz1 + W)
        p += box(x_end - 0.01, xr, -0.75 - 0.01, 0.8, CHANNEL_H, fz1 + W)
        p += box(x_end - 0.01, xr, -0.75 - 0.01, 0.8, fz0 - W, bottom(0.0, LINER_SQUEEZE - LINER_T + LINER_FIT))
        p -= place(sensor_cuts())
        d.update(chip=(cx, ty - lc.CHIP_PROUD, cz))
    p -= cav
    p += xiao_rails(xs, bz, cy0)
    d.update(xf=xf, zb=(zb0, zb1), cy0=cy0, bz=bz, board_y=board_y, sensor=sensor,
             lead_exit=(lx, ly, zb0), pogo=(px, by, zb1))
    lid = lid_for(xf, x_end, zb0, zb1, y1)
    rst = (xf + W + 4.0, bz + 5.0)                         # XIAO reset button, next to the USB-C (check yours)
    lid -= box(rst[0] - 0.6, rst[0] + 0.6, y1 - mv.LID_T - 1, y1 + 1, rst[1] - 0.6, rst[1] + 0.6)
    return p, lid, d


def battery_pod():
    """Left pod, modelled as for the right temple (the assembly places it). Returns (pod, lid, dims)."""
    bw, bh, bd = mv.BATTERY
    p, d = pocket(bd)
    b, cav, (xf, zb0, zb1) = body(bd, bh + 2 * W, bw + 2 * W, d)
    p += b
    p -= cav
    d.update(xf=xf, zb=(zb0, zb1), cy0=d["y0"] + W)
    return p, lid_for(xf, d["x_end"], zb0, zb1, d["y1"]), d


def print_orient_head_down(p):
    """Head-side face down: the pocket's outer face bridges over the paddle's space, the body's
    cavity opens upward."""
    return mv._to_bed(Rot(90, 0, 0) * p)


def print_orient_head_down_mirrored(p):
    """The same, for a pod mirrored to the right side (its head-side face is now at +y)."""
    return mv._to_bed(Rot(-90, 0, 0) * p)


def print_orient_liner(p):
    """Open edge down: the walls stand up and only the U's bottom bridges (3.6 mm). Face down, the
    far wall would overhang the whole liner."""
    return mv._to_bed(Rot(180, 0, 0) * p)


def print_orient_clip(p):
    """On its end: the loop flat on the bed."""
    return mv._to_bed(Rot(0, 90, 0) * p)


if __name__ == "__main__":
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    for old in list((OUT / "step").glob("hang_*")) + list((OUT / "stl").glob("hang_*")):
        old.unlink()
    pod, lid, d = board_pod()
    bat, blid, bd = battery_pod()
    # Modelled with y outward, which in a right-handed frame is the left temple: the board pod
    # (right) is exported mirrored, the battery pod (left) as modelled. The lids, liner and band
    # are symmetric through their thickness, so one of each fits either side.
    hpod, hlid, hd = board_pod("head")
    items = [("hang_pod_board", mirror(pod, Plane.XZ), print_orient_head_down_mirrored),
             ("hang_pod_board_head", mirror(hpod, Plane.XZ), print_orient_head_down_mirrored),
             ("hang_lid_board_head", hlid, mv.print_orient_lid),
             ("hang_liner_head", mirror(liner_head(), Plane.XZ), print_orient_liner),
             ("hang_back_clip_head", back_clip(hd["y0"], hd["y1"]), print_orient_clip),
             ("hang_pod_battery", bat, print_orient_head_down),
             ("hang_lid_board", lid, mv.print_orient_lid), ("hang_lid_battery", blid, mv.print_orient_lid),
             ("hang_liner", liner(), print_orient_liner),
             ("hang_back_clip", back_clip(d["y0"], d["y1"]), print_orient_clip)]
    for name, shape, orient in items:
        export_step(shape, str(OUT / "step" / f"{name}.step"))
        material = "petg" if name.startswith("hang_pod_") else "flex"
        export_stl(orient(shape), str(OUT / "stl" / f"{name}_{material}.stl"))
        print("wrote", name, f"{shape.volume:.0f} mm3")
