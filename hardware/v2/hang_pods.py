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
  when worn); the button in the back wall; the earlobe lead out of the ear-side wall, and the nose clip's
  magnetic pogo socket beside it.
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
FLANGE_ZONE = 3.6        # Room inside the board pod's ear-side wall for a knot in the earlobe lead (strain relief)
LEAD_HOLE = 4.0          # Earlobe lead's 4 wires (1 mm), loose, out through the ear-side wall
POGO = (4.0, 4.0)        # Nose clip's 2-pin magnetic pogo socket, flush in the ear-side wall: diameter, length (check yours)
POGO_FIT = 0.1           # Hole this much over its diameter (press it in; a drop of glue if loose)
POGO_BACK = 7.0          # This far behind the earlobe lead's hole, toward the far end


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


def body(depth, height, length, d):
    """The body box past the tip's end, its ear-side face level with the pocket's lowest point.
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
    cav += box(x_end - W - 0.1, x_end + 0.5, yc - hw / 2, yc + hw / 2, 0.1, 0.1 + hh)
    # Cord, out of the far end, at the back
    cav += box(xf - 1, xf + W + 0.1, yc - hw / 2, yc + hw / 2, zb1 - W - 0.3 - hh, zb1 - W - 0.3)
    return p, cav, (xf, zb0, zb1)


def lid_for(xf, x_end, zb0, zb1, y1):
    return box(xf + 0.6 - mv.LID_FIT, x_end - 0.6 + mv.LID_FIT, y1 - mv.LID_T, y1,
               zb0 + 0.6 - mv.LID_FIT, zb1 - 0.6 + mv.LID_FIT)


def board_pod():
    """Right pod. Returns (pod, lid, dims); dims["lead_exit"] is where the earlobe lead leaves."""
    w_, length, pcb, usb_h = mv.XIAO
    depth = pcb + usb_h + 0.4
    p, d = pocket(depth)
    height = 2 * W + FLANGE_ZONE + (w_ + 0.4) + 3.6       # Ear-side wall, lead's knot, board, button, back wall
    b, cav, (xf, zb0, zb1) = body(depth, height, length + 0.2 + 2 * W, d)
    p += b
    y0, y1, x_end = d["y0"], d["y1"], d["x_end"]
    cy0 = y0 + W
    bz = zb0 + W + FLANGE_ZONE + (w_ + 0.4) / 2            # Board's centre (across)
    cav += box(xf - 1, xf + W + 0.1, cy0 + pcb - 0.2, cy0 + pcb + usb_h + 0.4,
               bz - mv.USB_W / 2 - 0.2, bz + mv.USB_W / 2 + 0.2)                                 # USB-C, far end
    bx = xf + W + 8.0
    cav += box(bx - 1.6, bx + 1.6, cy0 + 0.5, cy0 + 3.7, zb1 - W - 0.1, zb1 + 1)               # Button plunger, back wall
    lx = x_end - W - 6.4                                   # Lead near the body's front: closest to the earlobe
    ly = (cy0 + y1 - mv.LID_T) / 2
    cav += Pos(lx, ly, zb0 + W / 2) * Cylinder(LEAD_HOLE / 2, W + 0.4)                          # Earlobe lead
    px = lx - POGO_BACK
    cav += Pos(px, ly, zb0 + W / 2) * Cylinder((POGO[0] + POGO_FIT) / 2, W + 0.4)               # Nose clip's socket
    p -= cav
    lid = lid_for(xf, x_end, zb0, zb1, y1)
    rst = (xf + W + 4.0, bz + 5.0)                         # XIAO reset button, next to the USB-C (check yours)
    lid -= box(rst[0] - 0.6, rst[0] + 0.6, y1 - mv.LID_T - 1, y1 + 1, rst[1] - 0.6, rst[1] + 0.6)
    d.update(xf=xf, zb=(zb0, zb1), cy0=cy0, bz=bz, lead_exit=(lx, ly, zb0), pogo=(px, ly, zb0))
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
    items = [("hang_pod_board", mirror(pod, Plane.XZ), print_orient_head_down_mirrored),
             ("hang_pod_battery", bat, print_orient_head_down),
             ("hang_lid_board", lid, mv.print_orient_lid), ("hang_lid_battery", blid, mv.print_orient_lid),
             ("hang_liner", liner(), print_orient_liner),
             ("hang_back_clip", back_clip(d["y0"], d["y1"]), print_orient_clip)]
    for name, shape, orient in items:
        export_step(shape, str(OUT / "step" / f"{name}.step"))
        material = "petg" if name.startswith("hang_pod_") else "flex"
        export_stl(orient(shape), str(OUT / "stl" / f"{name}_{material}.stl"))
        print("wrote", name, f"{shape.volume:.0f} mm3")
