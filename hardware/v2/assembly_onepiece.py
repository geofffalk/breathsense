"""
Both sides as worn, in one STEP for Fusion: the one-piece temple parts and their clips, the pods
hanging off the temple tips' ends (turned down to their 40 degree slope), their lids and liners, and the MAX30101 earlobe
clip folded onto a reference earlobe (with the smallest and largest lobes it's sized for), the
nose clip on a reference nostril wing with its wire across the cheek, with simple reference glasses (temples, tips, frame front) to show where it all sits. Each
part is a named body. Right side at -y (as modelled), left side mirrored to +y about the head's
centre. The reference glasses are rough stand-ins built from the measurements, not a model.

Run:  python assembly_onepiece.py   -> out/assembly_onepiece.step
"""

import sys
from pathlib import Path

import math

from build123d import Compound, Plane, Pos, Rot, Solid, Vector, export_step, mirror

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
import glasses_mount as gm   # noqa: E402
import mount_v2 as mv        # noqa: E402
import onepiece as op        # noqa: E402
import hang_pods as hp       # noqa: E402
import lobe_clip as lc       # noqa: E402
import nose_clip as nc       # noqa: E402

HALF_WIDTH = 70.0        # Temple inner faces this far either side of the head's centre (stand-in)
BEND = (-gm.TEMPLE_STRAIGHT, -gm.REF_T_BEND[1] / 2)   # Ear bend: x, z of the axis the tip turns about


def onto_tip(shape):
    """A pod part modelled along a straight temple, turned down about the ear bend to the tip."""
    x, z = BEND
    return Pos(x, 0, z) * (Rot(0, -gm.TIP_ANGLE, 0) * (Pos(-x, 0, -z) * shape))


# Stand-in ear, right side, in the worn frame before place(): the lobe's intertragic notch (the
# top of the lobe) and how far out from the temple's inner face the back of the lobe is. Ears
# vary: the lead is checked over NOTCH_RANGE either way, and every lobe size the clip takes.
NOTCH = (-100.0, -36.0)
NOTCH_RANGE = 5.0
LOBE_BACK_Y = 8.0
LOBES = {"small": (2.5, 13.0, 16.0), "mid": (5.0, 20.0, 20.0), "large": (8.0, 27.0, 25.0)}   # Thickness, height, width
LOBE_BACK_X = 4.0        # Lobes hang this far behind the notch


LEAD_SLACK = 25.0


def lead_exit():
    """Where the earlobe lead leaves the board pod, worn frame (before place())."""
    _, _, d = hp.board_pod()
    v = onto_tip(Pos(*d["lead_exit"]) * Solid.make_box(0.01, 0.01, 0.01)).center()
    return v.X, v.Y, v.Z


def lead_entry(chip_x, chip_z):
    """Where the lead enters the clip's pad (rear wall, by the pins), worn frame, chip at (chip_x, chip_z)."""
    x, y, z = lc.LEAD_OUT
    return chip_x + x, LOBE_BACK_Y + y, chip_z + z


def lead_length():
    """Longest straight run from the pod to the clip over every notch position and chip height,
    plus slack: (farthest, length to cut)."""
    ex = lead_exit()
    worst = max(math.dist(ex, lead_entry(NOTCH[0] + dx - LOBE_BACK_X, NOTCH[1] + dz - below))
                for dx in (-NOTCH_RANGE, 0, NOTCH_RANGE) for dz in (-NOTCH_RANGE, 0, NOTCH_RANGE)
                for t, h, w in LOBES.values() for below in (lc.CHIP_BELOW_NOTCH, h - lc.CHIP_BELOW_NOTCH))
    return worst, math.ceil((worst + LEAD_SLACK) / 5) * 5


def lead(a, b, sag=12.0, r=1.2):
    """The lead as a sagging chain of cylinders from a to b (a stand-in for 4 loose wires)."""
    n = 10
    pts = [Vector(*[a[k] + (b[k] - a[k]) * i / n for k in range(3)]) - Vector(0, 0, sag * math.sin(math.pi * i / n))
           for i in range(n + 1)]
    out = None
    for p0, p1 in zip(pts, pts[1:]):
        seg = Solid.make_cylinder(r, (p1 - p0).length, Plane(origin=p0, z_dir=p1 - p0))
        out = seg if out is None else out + seg
    return out


def earlobe_items():
    """The clip folded on the mid lobe (chip 8 mm below the notch), the lead, and all three lobes."""
    nx, nz = NOTCH
    lx = nx - LOBE_BACK_X
    t, h, w = LOBES["mid"]
    chip_z = nz - 8.0
    clip, _ = lc.clip_worn(t, (nz - h) - chip_z)
    items = [("max_clip", Pos(lx, LOBE_BACK_Y, chip_z) * clip)]
    items.append(("max_lead", lead(lead_exit(), lead_entry(lx, chip_z))))
    for name, (t, h, w) in LOBES.items():
        items.append((f"ref_lobe_{name}", Pos(lx, LOBE_BACK_Y, 0) * lc.lobe(t, h, w, nz - h)))
    return items


# Stand-in nose, right side, in the worn frame before place() (which puts y at -HALF_WIDTH - y): the
# nostril wing's inner face and rim, its thickness, and the nose wire's path across the cheek
# (down behind the earlobe, under its clip, along the cheek, to the side of the nose). Faces vary; the
# length gets generous slack.
NOSTRIL = (0.0, -HALF_WIDTH + 14.0, -54.0)
WING_T = 3.0
CHEEK = [(-134.0, 1.0, -62.0), (-120.0, 2.0, -78.0), (-92.0, 2.0, -76.0), (-55.0, -8.0, -66.0), (-20.0, -26.0, -58.0)]
NOSE_SLACK = 40.0


def polyline(pts, r=0.6):
    """A wire through these points, as a chain of cylinders."""
    out = None
    for p0, p1 in zip(pts, pts[1:]):
        a, b = Vector(*p0), Vector(*p1)
        seg = Solid.make_cylinder(r, (b - a).length, Plane(origin=a, z_dir=b - a))
        out = seg if out is None else out + seg
    return out


def nose_path():
    """The nose wire's points: from the pod's pogo socket (plug on) to the clip's back face."""
    _, _, d = hp.board_pod()
    px, py, pz = d["pogo"]
    plug = onto_tip(Pos(px, py, pz - hp.POGO[1]) * Solid.make_box(0.01, 0.01, 0.01)).center()
    x, y, z = nc.wire_out(WING_T)
    nx, ny, nz = NOSTRIL
    return [(plug.X, plug.Y, plug.Z)] + CHEEK + [(nx + x - 2.0, ny + y, nz + z), (nx + x, ny + y, nz + z)]


def nose_length():
    """Along the path, plus slack: (path, length to cut, plug to clip)."""
    pts = nose_path()
    run = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    return run, math.ceil((run + NOSE_SLACK) / 10) * 10


def nose_items():
    """The nose clip on a reference nostril wing, and its wire."""
    at = Pos(*NOSTRIL)
    return [("nose_clip", at * nc.clip(WING_T)), ("nose_wire", polyline(nose_path())),
            ("ref_nostril_wing", at * nc.wing(WING_T))]


def place(shape, right, flipped_pod=False):
    """A part modelled for the right temple with y outward from the temple's inner face, into the
    world (y to the wearer's left; temples' inner faces at -/+HALF_WIDTH). The right side is
    mirrored, so outward is -y; the left side isn't. A pod part arrives already flipped once by
    worn_pod(), so for the right side it gets the half-turn variant instead of a second mirror,
    which would leave the solid broken."""
    if not right:
        return Pos(0, HALF_WIDTH, 0) * shape
    if flipped_pod:
        return Pos(0, -HALF_WIDTH, 0) * shape
    return Pos(0, -HALF_WIDTH, 0) * mirror(shape, Plane.XZ)


def side(right, sensor="lobe"):
    """One side's parts. sensor="lobe": MAX30101 on the earlobe clip; "head": in the board pod's
    head-side wall (right side only differs)."""
    pod, lid, d = hp.board_pod(sensor)
    bat, blid, bd = hp.battery_pod()
    s = "right" if right else "left"
    items = [(f"onepiece_{s}", place(op.part(), right))]
    items += [(f"clip_{s}_{i + 1}", place(op.clip(x), right)) for i, x in enumerate(op.CLIPS)]
    if right:
        pods = [("pod_board", pod), ("lid_board", lid), (f"back_clip_{s}", hp.back_clip(d["y0"], d["y1"]))]
        pods += [(f"liner_{s}", hp.liner_head() if sensor == "head" else hp.liner())]
        if sensor == "head":
            from glasses_mount import box
            frame, _ = hp.head_frame()
            bl, bh, bt, bf = lc.MAX_BOARD
            pods += [("max30101_board", frame(box(lc.BCX - bl / 2, lc.BCX + bl / 2, lc.Y_PCB_BACK, lc.Y_PCB_FRONT,
                                                  lc.BCZ - bh / 2, lc.BCZ + bh / 2)))]
    else:
        pods = [("pod_battery", bat), ("lid_battery", blid), (f"back_clip_{s}", hp.back_clip(bd["y0"], bd["y1"])),
                (f"liner_{s}", hp.liner())]
    items += [(n, place(onto_tip(p), right)) for n, p in pods]
    if right:
        items += [(n, place(p, right)) for n, p in (earlobe_items() if sensor == "lobe" else []) + nose_items()]
    return items


def glasses():
    """Rough reference glasses from the measurements: tapered temples with their tips turned down,
    and a frame front with lens openings."""
    from glasses_mount import box
    out = []
    xs = [op.BEND_X + (-1.0 - op.BEND_X) * i / 12 for i in range(13)]
    temple = None
    for xa, xb in zip(xs, xs[1:]):
        seg = box(xa, xb + 0.01, 0, op.temple_t(xa), -op.temple_h(xa), 0)
        temple = seg if temple is None else temple + seg
    from glasses_mount import xz_prism
    n = 39
    pts = [(hp.TIP_END_X + gm.TIP_LEN * i / n, -hp.paddle_h(gm.TIP_LEN * i / n)) for i in range(n + 1)]
    tip = onto_tip(xz_prism([(hp.TIP_END_X, 0.0), (op.BEND_X + 0.01, 0.0)] + pts[::-1], 0, hp.TIP_T))
    for right in (True, False):
        out.append((f"ref_temple_{'right' if right else 'left'}", place(temple + tip, right)))
    front = box(op.FRAME_BACK_X, op.FRAME_BACK_X + 5, -HALF_WIDTH - 4, HALF_WIDTH + 4, -32, op.FRAME_TOP_Z)
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * (HALF_WIDTH - 3), sgn * (HALF_WIDTH - 3 - 50)))
        front -= box(op.FRAME_BACK_X - 1, op.FRAME_BACK_X + 6, y0, y1, -29, op.LENS_TOP_Z)
    front -= box(op.FRAME_BACK_X - 1, op.FRAME_BACK_X + 6, -14, 14, -32, -12)       # Nose bridge
    out.append(("ref_frame_front", front))
    return out


if __name__ == "__main__":
    for sensor, fname in (("lobe", "assembly_onepiece.step"), ("head", "assembly_onepiece_head.step")):
        parts = []
        for name, shape in side(True, sensor) + side(False, sensor) + glasses():
            shape.label = name
            parts.append(shape)
        export_step(Compound(children=parts, label=f"BreathSense v2, both sides on reference glasses ({sensor} sensor)"),
                    str(op.OUT / fname))
        print("wrote", op.OUT / fname, len(parts), "parts")
    worst, length = lead_length()
    print(f"earlobe lead: farthest {worst:.1f} mm; cut it {length:.0f} mm")
    run, length = nose_length()
    print(f"nose wire: path {run:.0f} mm; cut it {length:.0f} mm")
