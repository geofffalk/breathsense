"""
BreathSense v2 nose clip: a soft-flex U band over the rim of the right nostril's wing, holding the
breath thermistor upright at the nostril's entrance.

- A 4 mm wide band bent into a U: one leg inside the nostril, one on the skin outside, the bend
  under the rim. It's printed shaped to your wing, its legs SQUEEZE closer than the wing is thick,
  so the grip is only that light squeeze, spread over both legs. Print the size nearest your wing
  (FITS: pinch the wing gently with calipers). An earlier PETG ring sprang open from under 1 mm
  onto the wing and pinched hard; PETG is too stiff for a short U (0.3 mm of squeeze would be 3 N).
- Thermistor: a short post joined to the bend on the inside holds the glass bead upright at the
  nostril's entrance, about 1 mm above the rim's lowest point: higher up the nostril it didn't
  cool fast enough to register the end of an out-breath. It sits STALK_OFF from the wing's inner
  face so it reads breath, not skin. One straight tunnel runs down the post: the sleeved leads
  slot in from the top, the bead stays on top, and the leads come out at the post's foot, below
  the rim, outside the nose, where they're soldered to a twisted pair of 30 AWG silicone wires
  (heat-shrink each joint). The pair runs loose along the cheek to a 2-pin magnetic pogo plug that snaps onto
  the board pod (see hang_pods.py).
- Prints flat on its back face (x = X0): the U's profile is on the bed, so the lines run round the
  band and take its bending along their length; the tunnel's diamond section has a 45 deg roof,
  so there are no bridges.

Coordinates (worn, right nostril): x forward, y outward (from inside the nostril through the
wing to the skin outside), z up. The wing's inner face is y = 0, its rim's bottom z = -gap / 2.
The U's profile lies in the y-z plane, its back face at x = X0.

Run:  python nose_clip.py   -> out/step/nose_clip.step, out/stl/nose_clip_w<fit>_flex.stl
"""

import math
import sys
from pathlib import Path

from build123d import Pos, Rot, export_step, export_stl

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
sys.path.insert(0, str(Path(__file__).parent))
import mount_v2 as mv        # noqa: E402
from glasses_mount import box, yz_prism   # noqa: E402

OUT = Path(__file__).parent / "out"

BEAD_D = 0.8                 # Glass bead thermistor (check yours)
WING = 3.0                   # Your nostril wing's thickness, pinched gently (check yours) ...
FITS = (2.5, 3.0, 3.5, 4.0)  # ... and the sizes exported: print the nearest, or two and keep the better
SQUEEZE = 0.8                # Legs this much closer than the wing as printed: the whole grip

BAND_W = 4.0                 # Band's width along the rim (x)
BAND_T = 1.2                 # ... and thickness (3 lines)
LEG_H = 6.0                  # Legs' height above the bend's centre
LEAD_IN = 0.6                # Chamfer on the legs' inner top edges, so the wing slides in
E_FLEX = 25.0                # MPa, soft flex (TPE/TPU about 85-95A), for the grip estimate (check yours)

STALK_OFF = 2.5              # Bead's axis this far from the wing's inner face
BEAD_Z = 0.0                 # Bead's centre this high above the bend's centre: about 1 mm above the rim's lowest point,
                             # at the nostril's entrance (higher up, it cooled too slowly to catch the out-breath's end)
STALK = (2.8, 2.8)           # Post's size along x and y
LEAD_TUNNEL = 1.0            # Leads' tunnel straight down the post: a diamond (45 deg roof as printed, no
                             # bridge) this wide across its flats, a snug fit for two leads in 0.5 mm sleeving
POST_Z0 = -3.0               # Post's foot, below the rim, outside the nose: the leads come out here

X0, X1 = -BAND_W / 2, BAND_W / 2


def grip(gap, fit=WING):
    """(grip N, squeeze mm) on a wing this thick, for the size made for `fit`: each leg a cantilever
    from the bend, loaded at its middle."""
    rest = fit - SQUEEZE
    d = max(gap - rest, 0.0)
    i = BAND_W * BAND_T ** 3 / 12
    arm = rest / 2 + BAND_T / 2 + LEG_H / 2
    return 3 * E_FLEX * i * d / (2 * arm ** 3), d


def u_half(g, side):
    """One leg plus its half of the bend: leg's inner face at y = side * g, the bend's centre at
    the origin."""
    t = BAND_T
    n = 24
    pts = [(side * g, LEG_H - LEAD_IN), (side * (g + LEAD_IN), LEG_H), (side * (g + t), LEG_H)]
    pts += [(side * (g + t) * math.cos(math.pi / 2 * k / n), -(g + t) * math.sin(math.pi / 2 * k / n))
            for k in range(n + 1)]
    pts += [(side * g * math.cos(math.pi / 2 * k / n), -g * math.sin(math.pi / 2 * k / n))
            for k in range(n, -1, -1)]
    pts = [(y if abs(y) > 1e-9 else -side * 0.05, z) for y, z in pts]    # Overlap the halves at y = 0
    return yz_prism(pts, X0, X1)


def halves(fit=WING):
    """The clip as printed, the bend centred on the origin. Returns (inside half with the post,
    outside half)."""
    g = (fit - SQUEEZE) / 2
    inner, outer = u_half(g, -1), u_half(g, 1)
    sx, sy = STALK
    ys = -g - STALK_OFF
    z_top = BEAD_Z - BEAD_D / 2 - 0.1
    # Post, joined to the bend's inside quarter (it stops at the wing's inner face, y = -g, so it
    # stays out of the U)
    inner += box(X0, X0 + sx, ys - sy / 2, -g - 0.05, POST_Z0, z_top)
    w = LEAD_TUNNEL
    inner -= Pos(X0 + sx / 2, ys, 0) * (Rot(0, 0, 45) * box(-w / 2, w / 2, -w / 2, w / 2, POST_Z0 - 1, z_top + 1))
    return inner, outer


def drop(gap, fit=WING):
    """How far the bend's centre sits below the wing's rim centre when worn, so the rim clears it."""
    return max(gap - (fit - SQUEEZE), 0.0) / 2 + 0.3


def clip(gap=None, fit=WING):
    """The clip for `fit` on a wing `gap` thick (None: as printed), placed with the inside leg on
    y = 0. Worn, each half is shown moved out by half the squeeze, joined under the bend."""
    rest = fit - SQUEEZE
    gap = rest if gap is None else gap
    inner, outer = halves(fit)
    s = max(gap - rest, 0.0) / 2
    c = Pos(0, -s, 0) * inner + Pos(0, s, 0) * outer
    g = rest / 2
    if s > 0:
        c += box(X0, X1, -s - 0.05, s + 0.05, -g - BAND_T, -g)
    return Pos(0, gap / 2, -drop(gap, fit) if gap > rest else 0.0) * c


def wing(t, h=10.0, w=12.0):
    """Reference nostril wing: a slab t thick from its rounded rim up, inner face on y = 0."""
    import lobe_clip as lc
    return Pos(0, 0, 0) * lc.lobe(t, h, w, -t / 2)


def wire_out(gap, fit=WING):
    """Where the leads come out of the groove's bottom, toward the pair's joint (clip frame, worn)."""
    rest = fit - SQUEEZE
    s = max(gap - rest, 0.0) / 2
    return X0 + STALK[0] / 2, gap / 2 - s - rest / 2 - STALK_OFF, POST_Z0 - drop(gap, fit)


def print_orient(p):
    """Flat on its back face (x = X0): the U's profile on the bed."""
    return mv._to_bed(Rot(0, -90, 0) * p)


if __name__ == "__main__":
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    export_step(clip(), str(OUT / "step" / "nose_clip.step"))
    for f in FITS:
        c = clip(fit=f)
        export_stl(print_orient(c), str(OUT / "stl" / f"nose_clip_w{round(f * 10)}_flex.stl"))
        bb = c.bounding_box()
        print(f"nose_clip_w{round(f * 10)}: {c.volume:.0f} mm3, {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
              f"{len(c.solids())} solid; legs {f - SQUEEZE:.1f} apart")
        print("   " + ", ".join(f"{t} mm wing {grip(t, f)[0]:.2f} N" for t in (f - 0.5, f, f + 0.5)))
