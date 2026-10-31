"""
BreathSense v2 nose clip: one soft-flex part on the wing of the right nostril, holding the breath
thermistor just inside the nostril.

- A U that wraps the nostril wing's lower rim: the inner leg inside the nostril, the outer pad on
  the skin outside. The U is printed nearly closed (REST_GAP) and springs shut onto any wall of
  about 2-5 mm; a pair of 2x1 mm magnets in each leg only helps it settle (they pull about 0.02 N
  through a 3 mm wall, too little to hold it on their own). Each stack sits in a hole open on the
  face away from the wing, closed by a lid on a living hinge with a peg that presses into the
  hole over the stack. When worn the magnets pull each other toward the wing, deeper into their
  holes, so the lids only need to stop them dropping out while the clip is off.
- Bead cage: an open square tube at the inner leg's tip, its axis along the nostril (the way the
  air goes), holding the glass bead in the airflow about 4 mm in and 2 mm off the skin. Skin
  contact would read skin temperature, not breath.
- Wires: the bead's leads drop through the cage and down a groove on the inner leg's free face
  to a keel under the U, outside the nostril. There they're soldered to a twisted pair of 30 AWG
  silicone wires, pressed into the keel's channel, which leaves from the clip's back face
  toward the ear. The pair runs loose along the cheek to a 2-pin magnetic pogo plug that snaps
  onto the board pod (see hang_pods.py).
- To fit out: magnets into the holes (check the two legs attract), bead leads into the groove,
  then fold each lid up and press its peg in. The inner leg's lid closes over the groove.

Coordinates (worn, right nostril): x forward, y outward (from inside the nostril through the
wing to the skin outside), z up. The wing's inner face is y = 0 and its rim is at the U's centre,
(y, z) = (gap / 2, 0). The clip's back face is x = X0.

Run:  python nose_clip.py   -> out/step/nose_clip.step, out/stl/nose_clip_flex.stl
"""

import math
import sys
from pathlib import Path

from build123d import Align, Cylinder, Pos, Rot, export_step, export_stl

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
sys.path.insert(0, str(Path(__file__).parent))
import mount_v2 as mv        # noqa: E402
from glasses_mount import box, y_cyl, yz_prism   # noqa: E402

OUT = Path(__file__).parent / "out"

BEAD_D = 0.8                 # Glass bead thermistor (check yours) ...
LEAD_D = 0.2                 # ... and its two leads
PAIR_D = 1.2                 # Twisted pair of 30 AWG silicone wires, across both
MAGNET_D, MAGNET_T = 2.0, 1.0
MAGNETS = 2                  # Per leg, stacked
WALL_T = (2.0, 5.0)          # Nostril wing thicknesses it takes
REST_GAP = 1.6               # As printed: under the thinnest wall, so it always presses

LEG_T = 1.0
X0, X_IN, X_OUT = -6.0, 0.0, 2.0   # Back face; front of the inner leg (and the U); front of the outer pad
OUTER_TOP = 5.0
BEAD_IN = 4.0                # Bead this far up into the nostril from the rim
CAGE = (3.0, 0.5, 1.6)       # Cage: outside square, wall, height (along the nostril)
SKIN = 0.4                   # Between the magnets and the wing
MAG_FIT = 0.05               # Magnet holes this much over the magnets' diameter
MAG_Z = 1.75                 # Magnets' centre height, and across ...
MAG_X = -2.0                 # ... (both legs, so they line up)
BOSS = (0.3, 3.2)            # Magnet bosses' z extent; each spans the leg's full width, so it prints on the bed
STACK = MAGNETS * MAGNET_T
HEAD = 0.9                   # Hole depth above the stack: the lid's peg fills it
BOSS_T = SKIN + STACK + HEAD # Leg plus boss, from the wing's face
LID_T = 0.8                  # Magnet lids: thickness ...
LID_L = 5.6                  # ... length from the hinge at the back face (over the hole at MAG_X) ...
LID_Z = (0.3, 2.9)           # ... z extent (kept 0.3 mm under the cage)
HINGE_T, HINGE_L = 0.5, 1.0  # Living hinge: thinner first part of each lid, as printed flat
PEG_FIT = 0.05               # Pegs this much over the holes' diameter, so they grip
GROOVE = (0.6, 0.4)          # Leads' groove: width, depth
KEEL_H = 2.0                 # Keel under the U, with the pair's channel ...
CHANNEL = (PAIR_D + 0.1, 1.4)   # ... open underneath: width, depth

CAGE_X = X0 + CAGE[0] / 2    # Cage (and bead) centre: at the back face, so it prints on the bed
CAGE_Y = -LEG_T - CAGE[0] / 2


def u_band(gap):
    """The U round the wing's rim: half an annulus under (gap/2, 0), joining the legs' bottoms."""
    n = 24
    ro, ri = gap / 2 + LEG_T, gap / 2
    outer = [(gap / 2 + ro * math.cos(math.pi + math.pi * i / n), ro * math.sin(math.pi + math.pi * i / n))
             for i in range(n + 1)]
    inner = [(gap / 2 + ri * math.cos(math.pi + math.pi * i / n), ri * math.sin(math.pi + math.pi * i / n))
             for i in range(n + 1)]
    pts = [(-LEG_T, 0.01)] + outer + [(gap + LEG_T, 0.01), (gap, 0.01)] + inner[::-1] + [(0.0, 0.01)]
    return yz_prism(pts, X0, X_IN)


def lid(face, out, closed):
    """Magnet lid hinged on the boss face at y = face (out = +1 or -1, the way that face looks).
    Open: lying flat on the bed (x = X0), pointing away from the boss, peg up. Closed: folded up
    against the boss face, peg in the hole."""
    d = MAGNET_D + MAG_FIT + PEG_FIT
    if closed:
        f = box(X0, X0 + LID_L, *sorted((face, face + out * LID_T)), *LID_Z)
        return f + y_cyl(MAG_X, MAG_Z, *sorted((face - out * HEAD, face + out * 0.01)), d)
    y = lambda a: face + out * a                 # noqa: E731
    f = box(X0, X0 + HINGE_T, *sorted((y(-0.01), y(HINGE_L))), *LID_Z)
    f += box(X0, X0 + LID_T, *sorted((y(HINGE_L), y(LID_L))), *LID_Z)
    peg = Pos(X0 + LID_T - 0.01, y(MAG_X - X0), MAG_Z) * Cylinder(d / 2, HEAD + 0.01,
                                                                  align=(Align.CENTER, Align.CENTER, Align.MIN),
                                                                  rotation=(0, 90, 0))
    return f + peg


def clip(gap=REST_GAP, lids_open=True):
    """The clip with its legs this far apart: REST_GAP as printed, or a wing's thickness as worn;
    the magnet lids open (as printed) or closed."""
    zc = BEAD_IN - CAGE[2] / 2
    c = box(X0, X_IN, -LEG_T, 0, 0, zc + CAGE[2])                                   # Inner leg
    c += box(X0, X_OUT, gap, gap + LEG_T, 0, OUTER_TOP)                             # Outer pad
    c += u_band(gap)
    # Bead cage: a square tube along z at the inner leg's tip, off its free face
    s, w, h = CAGE
    cage = box(CAGE_X - s / 2, CAGE_X + s / 2, CAGE_Y - s / 2, CAGE_Y + s / 2 + 0.01, zc, zc + h)
    cage -= box(CAGE_X - s / 2 + w, CAGE_X + s / 2 - w, CAGE_Y - s / 2 + w, CAGE_Y + s / 2 - w, zc - 1, zc + h + 1)
    c += cage
    # Magnet bosses, the holes open on the faces away from the wing
    c += box(X0, X_IN, -BOSS_T, -LEG_T + 0.01, *BOSS)
    c += box(X0, X_IN, gap + LEG_T - 0.01, gap + BOSS_T, *BOSS)
    d = MAGNET_D + MAG_FIT
    c -= y_cyl(MAG_X, MAG_Z, -BOSS_T - 1, -SKIN, d)
    c -= y_cyl(MAG_X, MAG_Z, gap + SKIN, gap + BOSS_T + 1, d)
    # Keel under the U, outside the nostril, with the pair's channel open underneath and out the back
    zb = -(gap / 2 + LEG_T)
    c += box(X0, X_IN, -LEG_T, gap + LEG_T, zb - KEEL_H, zb + 0.6)           # Top stays under the rim's space
    cw, ch = CHANNEL
    c -= box(X0 - 1, X_IN - 0.8, gap / 2 - cw / 2, gap / 2 + cw / 2, zb - KEEL_H - 1, zb - KEEL_H + ch)
    # Leads' groove: from the cage's open bottom, down the inner leg's boss and free face and the
    # keel's side, round under into the channel
    gw, gd = GROOVE
    c -= box(CAGE_X - gw / 2, CAGE_X + gw / 2, -BOSS_T - 1, -LEG_T + gd, zb - KEEL_H - 1, zc + 0.01)
    # Magnet lids
    c += lid(-BOSS_T, -1, not lids_open)
    c += lid(gap + BOSS_T, 1, not lids_open)
    return c


def wing(t, h=10.0, w=12.0):
    """Reference nostril wing: a slab t thick from its rounded rim up, inner face on y = 0."""
    import lobe_clip as lc
    return Pos((X0 + X_OUT) / 2, 0, 0) * lc.lobe(t, h, w, -t / 2)


def wire_out(gap):
    """Where the pair leaves the clip's back face (its centre), in the clip's frame."""
    zb = -(gap / 2 + LEG_T)
    return X0, gap / 2, zb - KEEL_H + CHANNEL[1] / 2


def print_orient(p):
    """Back face down: every feature is an extrusion up from the bed, the magnet holes and the
    cage's sides the only bridges (2-3 mm). The lids lie flat on the bed, pegs up."""
    return mv._to_bed(Rot(0, -90, 0) * p)


if __name__ == "__main__":
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    c = clip()
    export_step(c, str(OUT / "step" / "nose_clip.step"))
    export_stl(print_orient(c), str(OUT / "stl" / "nose_clip_flex.stl"))
    bb = c.bounding_box()
    print(f"wrote nose_clip {c.volume:.0f} mm3; {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
