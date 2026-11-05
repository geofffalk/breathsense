"""
Every current v3 print part in one STEP for Fusion, each as it sits on the printer bed (the same
shapes and orientations as the STLs), in rows: PETG, soft flex, then the test piece. Each body is
named after its STL, with how many to print. A two-colour part (the front: black body and the
translucent U's in front of the LEDs) is a list of (name, shape) pieces placed together.

Run:  python print_layout_v3.py   -> out/print_layout_v3.step
"""

import sys
from pathlib import Path

from build123d import Compound, Plane, Pos, Rot, export_step, mirror

sys.path.insert(0, str(Path(__file__).parent))
import glasses_v3 as g       # noqa: E402
import wayfarer as w         # noqa: E402
import nose_clip as nc       # noqa: E402  (hardware/v2, on the path via glasses_v3)

hp, mv = g.hp, g.mv
GAP = 10.0


def two_colour(prefix, body, clear, whole):
    """Body and translucent pieces, oriented front face down and moved by the whole part's bed offset."""
    rot = Rot(0, 90, 0)
    bb = (rot * whole).bounding_box()
    at = Pos(-bb.min.X, -bb.min.Y, -bb.min.Z)
    return [(f"{prefix}_body_petg", at * (rot * body)), (f"{prefix}_translucent_petg", at * (rot * clear))]


def parts():
    """(name, how many, shape on the bed or [(name, piece), ...]) per row."""
    body, clear, whole = w.front_pieces()
    tb, tc = w.test_front()
    tf, tr, tl = g.temple()
    hpod, hlid, hliner, bpod, blid, bliner = g.pods()
    petg = [
        ("front", 1, two_colour("front", body, clear, whole)),
        ("temple_front_left_petg", 1, mv._to_bed(Rot(-90, 0, 0) * tf)),
        ("temple_front_right_petg", 1, mv._to_bed(Rot(90, 0, 0) * mirror(tf, Plane.XZ))),
        ("temple_rear_left_petg", 1, mv._to_bed(Rot(90, 0, 0) * tr)),
        ("temple_rear_right_petg", 1, mv._to_bed(Rot(-90, 0, 0) * mirror(tr, Plane.XZ))),
        ("pod_board_head_petg", 1, hp.print_orient_head_down_mirrored(mirror(hpod, Plane.XZ))),
        ("pod_battery_petg", 1, hp.print_orient_head_down(bpod)),
    ]
    flex = [
        ("liner_head_flex", 1, hp.print_orient_liner(mirror(hliner, Plane.XZ))),
        ("liner_battery_flex", 1, hp.print_orient_liner(bliner)),
        ("lid_board_head_flex", 1, mv.print_orient_lid(hlid)),
        ("lid_battery_flex", 1, mv.print_orient_lid(blid)),
        ("cap_pocket_flex", 2, mv._to_bed(g.pocket_cap(1))),
        ("cap_temple_pocket_flex", 2, mv._to_bed(g.temple_pocket_cap())),
        ("cap_groove_front_flex", 2, mv._to_bed(Rot(90, 0, 0) * g.groove_cap_front())),
        ("cap_groove_rear_flex", 2, mv._to_bed(Rot(90, 0, 0) * g.groove_cap_rear())),
        ("liner_joint_flex", 2, mv._to_bed(Rot(90, 0, 0) * tl)),
    ] + [(n, 1, o(sh)) for n, sh, o, _ in g.channel_cap_items()] + [(f"shim_{round(t * 10):02d}_flex", 2, mv._to_bed(Rot(0, 90, 0) * g.fold(g.shim(t), g.OPEN_ANGLE))) for t in g.SHIMS]
    flex += [(f"nose_clip_w{round(f * 10)}_flex", 1, nc.print_orient(nc.clip(fit=f))) for f in nc.FITS]
    # Test piece first: the right half of the front (lens fit, pad, socket, hinge, LEDs)
    test = [("test_front", 1, two_colour("test_front", tb, tc, tb + tc))]
    return petg, flex, test


def layout():
    """Each part's copies side by side along x, rows along y, all on z = 0."""
    out = []
    y = 0.0
    for row in parts():
        x = 0.0
        depth = 0.0
        for name, n, shape in row:
            pieces = shape if isinstance(shape, list) else [(name, shape)]
            bb = Compound(children=[sh for _, sh in pieces]).bounding_box()
            for i in range(n):
                for pname, sh in pieces:
                    s = Pos(x - bb.min.X, y - bb.min.Y, -bb.min.Z) * sh
                    s.label = pname if n == 1 else f"{pname} ({i + 1} of {n})"
                    out.append(s)
                x += bb.max.X - bb.min.X + GAP
            depth = max(depth, bb.max.Y - bb.min.Y)
        y += depth + 2 * GAP
    return out


if __name__ == "__main__":
    bodies = layout()
    path = g.OUT / "print_layout_v3.step"
    export_step(Compound(children=bodies, label="BreathSense v3 print parts, as on the bed"), str(path))
    print("wrote", path, len(bodies), "bodies")
