"""
The v3 concept as worn, in one STEP for Fusion: the front (body and translucent LED walls), both
lenses, the 5-LED strips along the front, both telescopic temples (front and rear pieces, joint liner; no LEDs), the v2 pods locked on the tips
with their lids and liners, the soft-flex caps, and the nose clip on a reference nostril with its
short lead up to the right pad's socket. Each part is a named body. Also a folded STEP (both
temples turned in) and a fold check: what the temples and pods hit as they fold.

Run:  python assembly_v3.py   -> out/assembly_v3.step, out/assembly_v3_folded.step, reports
"""

import math
import sys
from pathlib import Path

from build123d import Compound, Pos, Vector, export_step

sys.path.insert(0, str(Path(__file__).parent))
import glasses_v3 as g        # noqa: E402

ao, hp, nc = g.ao, g.hp, g.ao.nc


def socket_bottom(sign=-1):
    import wayfarer
    return Vector(*wayfarer.socket_xyz(sign))


def nose_items():
    """Nose clip on the stand-in nostril (right), and its short lead from the pad's socket (plug on)."""
    at = Pos(*ao.NOSTRIL)
    x, y, z = nc.wire_out(ao.WING_T)
    nx, ny, nz = ao.NOSTRIL
    wy = -ao.HALF_WIDTH - (ny + y)                            # place() mirrors y for the right side
    clip_end = Vector(nx + x, wy, nz + z)
    s = socket_bottom()
    pts = [(s.X, s.Y, s.Z - 4.0), (s.X - 1.0, s.Y, (s.Z + clip_end.Z) / 2), (clip_end.X, clip_end.Y, clip_end.Z)]
    run = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    return ([("nose_clip", ao.place(at * nc.clip(ao.WING_T), True)),
             ("ref_nostril_wing", ao.place(at * nc.wing(ao.WING_T), True)),
             ("nose_lead", ao.polyline(pts))], run)


def front_items():
    import wayfarer
    body, clear, _ = g.front_pieces()
    items = [("front_body", body), ("front_translucent", clear)]
    for sign, side in ((-1, "right"), (1, "left")):
        items += [(f"lens_{side}", g.lens(sign)), (f"strip_front_{side}", g.strip_front(sign)),
                  (f"cap_pocket_{side}", g.pocket_cap(sign))]
    items += [(f"cap_thermistor_{n}", c) for n, c in zip(("pad", "corner", "brow"), wayfarer.channel_caps())]
    return items


def temple_items(angle=None, e=0.0):
    """Everything that moves with each temple, turned about its hinge by angle (default: open, resting
    g.OPEN_ANGLE in; 90 folded), with the rear piece at extension e."""
    if angle is None:
        angle = g.OPEN_ANGLE
    tf, tr, tl = g.temple(e)
    hpod, hlid, hliner, bpod, blid, bliner = g.pods()
    back = Pos(-e, 0, 0)
    items = []
    for right, side in ((True, "right"), (False, "left")):
        pod = [("pod_board_head", hpod), ("lid_board_head", hlid), ("liner_right", hliner)] if right else \
              [("pod_battery", bpod), ("lid_battery", blid), ("liner_left", bliner)]
        parts = [(f"temple_front_{side}", tf), (f"temple_rear_{side}", tr), (f"liner_joint_{side}", tl),
                 (f"cap_groove_front_{side}", g.groove_cap_front()), (f"cap_groove_rear_{side}", g.groove_cap_rear(e)),
                 (f"cap_temple_pocket_{side}", g.temple_pocket_cap())]
        parts += [(n, back * ao.onto_tip(p)) for n, p in pod]
        a = angle if not isinstance(angle, tuple) else (angle[0] if right else angle[1])
        items += [(n, g.side_place(g.fold(p, a), right)) for n, p in parts]
    return items


def parts(angle=None, e=0.0):
    nose, run = nose_items()
    return front_items() + temple_items(angle, e) + (nose if angle is None else []), run


DESIGNED = {("pod_board_head", "lid_board_head"), ("pod_battery", "lid_battery"), ("pod_board_head", "liner_right"),
            ("pod_battery", "liner_left"), ("liner_right", "temple_rear_right"), ("liner_left", "temple_rear_left"),
            ("liner_joint_right", "temple_rear_right"), ("liner_joint_left", "temple_rear_left"),
            ("front_body", "cap_pocket_right"), ("front_body", "cap_pocket_left"),
            ("front_body", "cap_thermistor_pad"), ("front_body", "cap_thermistor_corner"),
            ("front_body", "cap_thermistor_brow"),
            ("temple_front_right", "cap_groove_front_right"), ("temple_front_left", "cap_groove_front_left"),
            ("temple_rear_right", "cap_groove_rear_right"), ("temple_rear_left", "cap_groove_rear_left"),
            ("temple_front_right", "cap_temple_pocket_right"), ("temple_front_left", "cap_temple_pocket_left")}


def overlaps(items, only=None):
    out = []
    names = [n for n, _ in items if not n.startswith("ref_") and n != "nose_lead"]
    d = dict(items)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if only and not only(a, b):
                continue
            v = d[a] & d[b]
            v = v.volume if v is not None else 0.0
            if v > 0.01:
                out.append((a, b, v, (a, b) in DESIGNED or (b, a) in DESIGNED))
    return out


def side_of(n):
    return "right" if n.endswith("right") or n in ("pod_board_head", "lid_board_head") else \
        "left" if n.endswith("left") or n in ("pod_battery", "lid_battery") else "front"


def fold_sequence(step=5, e=0.0):
    """Left temple folded first (90); the right folds onto it: the largest angle it reaches clear,
    and whether anything hits the front, the lenses or the pads on the way."""
    moving = lambda n: side_of(n) != "front"                              # noqa: E731
    left = [(n, s) for n, s in temple_items((0.0, 90.0), e) if side_of(n) == "left"]
    front = front_items()
    lf = overlaps(front + left, only=lambda x, y: (moving(x) or moving(y)) and side_of(x) != side_of(y))
    rest = None
    for a in range(step, 91, step):
        right = [(n, s) for n, s in temple_items((float(a), 90.0), e) if side_of(n) == "right"]
        hits = overlaps(front + left + right, only=lambda x, y: side_of(x) == "right" or side_of(y) == "right")
        hits = [h for h in hits if side_of(h[0]) != side_of(h[1]) and not h[3]]
        if hits:
            return [h for h in lf if not h[3]], rest, a, hits
        rest = a
    return [h for h in lf if not h[3]], rest, None, []


def fold_check(angles=(30, 60, 90)):
    """What each temple (with its pod) hits as it folds: the front and lenses, and the other side."""
    rows = []
    for a in angles:
        items, _ = parts(a)
        moving = lambda n: side_of(n) != "front"                      # noqa: E731
        hits = overlaps(items, only=lambda x, y: (moving(x) or moving(y)) and side_of(x) != side_of(y))
        rows.append((a, [h for h in hits if not h[3]]))
    return rows


if __name__ == "__main__":
    items, run = parts()
    shapes = []
    for name, s in items:
        s.label = name
        shapes.append(s)
    export_step(Compound(children=shapes), str(g.OUT / "assembly_v3.step"))
    print(f"wrote assembly_v3.step: {len(shapes)} parts; nose lead run {run:.0f} mm")
    for a, b, v, ok in overlaps(items):
        print(f"  {'designed' if ok else 'CLASH   '} {a} x {b}: {v:.2f} mm3")
    folded, _ = parts((80.0, 90.0))
    shapes = []
    for name, s in folded:
        s.label = name
        shapes.append(s)
    export_step(Compound(children=shapes), str(g.OUT / "assembly_v3_folded.step"))
    print("wrote assembly_v3_folded.step")
    for e in (g.TRAVEL[0], 0.0, g.TRAVEL[1]):
        lf, rest, at, hits = fold_sequence(e=e)
        print(f"  extension {e:+.0f}: left folded 90 deg vs front/lenses/pads: " +
              ("clear" if not lf else str([(x, y, round(v, 1)) for x, y, v, _ in lf])))
        print(f"    right then folds clear to {rest} deg" + ("" if at is None else
              f"; at {at} deg it meets: " + "; ".join(f"{x} x {y} {v:.1f} mm3" for x, y, v, _ in hits)))
    for e in g.TRAVEL:
        items_e, _ = parts(None, e)
        bad = [h for h in overlaps(items_e) if not h[3]]
        print(f"  open at extension {e:+.0f}: " + ("only designed overlaps" if not bad else str([(a, b, round(v, 2)) for a, b, v, _ in bad])))
