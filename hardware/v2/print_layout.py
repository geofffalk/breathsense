"""
Every current print part in one STEP for Fusion, each as it sits on the printer bed (the same
shapes and orientations as the STLs), laid out in two rows: PETG, then soft flex. Each body is
named after its STL, with how many to print.

Run:  python print_layout.py   -> out/print_layout.step
"""

import sys
from pathlib import Path

from build123d import Compound, Plane, Pos, export_step, mirror

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
sys.path.insert(0, str(Path(__file__).parent))
import hang_pods as hp       # noqa: E402
import lobe_clip as lc       # noqa: E402
import mount_v2 as mv        # noqa: E402
import nose_clip as nc       # noqa: E402
import onepiece as op        # noqa: E402

GAP = 10.0


def parts():
    """(name, how many, shape on the bed) for the PETG row, the soft-flex row, and the head-side
    sensor variant's row (its parts replace the board pod, its lid, one liner and the earlobe clip)."""
    left = op.part()
    pod, lid, d = hp.board_pod()
    bat, blid, _ = hp.battery_pod()
    petg = [("onepiece_right_petg", 1, op.print_orient(mirror(left, Plane.XZ))),
            ("onepiece_left_petg", 1, op.print_orient(left)),
            ("hang_pod_board_petg", 1, hp.print_orient_head_down_mirrored(mirror(pod, Plane.XZ))),
            ("hang_pod_battery_petg", 1, hp.print_orient_head_down(bat))]
    flex = [("onepiece_band_flex", 2, op.print_orient_clip(op.clip(op.CLIPS[0]))),
            ("hang_liner_flex", 2, hp.print_orient_liner(hp.liner())),
            ("hang_back_clip_flex", 2, hp.print_orient_clip(hp.back_clip(d["y0"], d["y1"]))),
            ("hang_lid_board_flex", 1, mv.print_orient_lid(lid)),
            ("hang_lid_battery_flex", 1, mv.print_orient_lid(blid)),
            ("lobe_clip_flex", 1, lc.print_orient(lc.clip_flat()))]
    flex += [(f"nose_clip_w{round(f * 10)}_flex", 1, nc.print_orient(nc.clip(fit=f))) for f in nc.FITS]
    # Head-side sensor variant: print these instead of the board pod, its lid, its liner, its band and the earlobe clip
    hpod, hlid, hd = hp.board_pod("head")
    head = [("hang_pod_board_head_petg", 1, hp.print_orient_head_down_mirrored(mirror(hpod, Plane.XZ))),
            ("hang_lid_board_head_flex", 1, mv.print_orient_lid(hlid)),
            ("hang_liner_head_flex", 1, hp.print_orient_liner(mirror(hp.liner_head(), Plane.XZ))),
            ("hang_back_clip_head_flex", 1, hp.print_orient_clip(hp.back_clip(hd["y0"], hd["y1"])))]
    return petg, flex, head


def layout():
    """Each part's copies side by side along x, rows along y, all on z = 0."""
    out = []
    y = 0.0
    for row in parts():
        x = 0.0
        depth = 0.0
        for name, n, shape in row:
            bb = shape.bounding_box()
            for i in range(n):
                s = Pos(x - bb.min.X, y - bb.min.Y, -bb.min.Z) * shape
                s.label = name if n == 1 else f"{name} ({i + 1} of {n})"
                out.append(s)
                x += bb.max.X - bb.min.X + GAP
            depth = max(depth, bb.max.Y - bb.min.Y)
        y += depth + 2 * GAP
    return out


if __name__ == "__main__":
    bodies = layout()
    export_step(Compound(children=bodies, label="BreathSense v2 print parts, as on the bed"),
                str(op.OUT / "print_layout.step"))
    print("wrote", op.OUT / "print_layout.step", len(bodies), "bodies")
