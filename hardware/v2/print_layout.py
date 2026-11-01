"""
Every current print part in one STEP for Fusion, each as it sits on the printer bed (the same
shapes and orientations as the STLs), laid out in rows: PETG, soft flex, then two variants (the
head-side sensor, and the one-piece part's earlier band grip). Each body is named after its STL,
with how many to print. A two-colour part is a list of (name, shape) pieces placed together.

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
    """(name, how many, shape on the bed) for the PETG row, the soft-flex row, the head-side sensor
    variant's row (its parts replace the board pod, its lid, one liner and the earlobe clip), and
    the band-grip variant's row (its parts replace the one-piece parts and their liners)."""
    left = op.part()

    def two_colour(l, grip, suffix):
        """Right and left one-piece parts, each as its body and translucent piece in the same place."""
        out = []
        for side, mir in (("right", True), ("left", False)):
            whole, b, w = l, op.body(l, grip), op.translucent(l, grip)
            if mir:
                whole, b, w = (mirror(x, Plane.XZ) for x in (whole, b, w))
            out.append((f"onepiece_{side}{suffix}", 1, [(f"onepiece_{side}{suffix}_body_petg", op.print_orient(b, whole)),
                                                        (f"onepiece_{side}{suffix}_translucent_petg", op.print_orient(w, whole))]))
        return out

    pod, lid, d = hp.board_pod()
    bat, blid, _ = hp.battery_pod()
    petg = two_colour(left, "liner", "") + [
            ("hang_pod_board_petg", 1, hp.print_orient_head_down_mirrored(mirror(pod, Plane.XZ))),
            ("hang_pod_battery_petg", 1, hp.print_orient_head_down(bat))]
    ln = op.liner()
    flex = [("onepiece_liner_right_flex", 1, op.print_orient_liner(mirror(ln, Plane.XZ))),
            ("onepiece_liner_left_flex", 1, op.print_orient_liner(ln)),
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
    # Band-grip variant of the one-piece part: print these instead of the one-piece parts and their liners
    bl = op.part(grip="band")
    band = two_colour(bl, "band", "_band") + [
            ("onepiece_band_flex", 2, op.print_orient_clip(op.clip(op.CLIPS[0])))]
    return petg, flex, head, band


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
    export_step(Compound(children=bodies, label="BreathSense v2 print parts, as on the bed"),
                str(op.OUT / "print_layout.step"))
    print("wrote", op.OUT / "print_layout.step", len(bodies), "bodies")
