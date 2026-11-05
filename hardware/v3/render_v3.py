"""
Render the v3 concept (open on the stand-in head, and folded) on the stand-in head (render_worn.head_meshes()), with a frozen breath wave
on the LEDs.

Run:  python render_v3.py   -> renders/v3_*.png
"""

import sys
from pathlib import Path

import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).parent))
import assembly_v3 as a3     # noqa: E402

g = a3.g
rw = g.ao.op  # noqa: F841  (keeps onepiece loaded the same way as the v2 scripts)
sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
import render_worn as rwn    # noqa: E402

OUT = Path(__file__).parent / "renders"
COL = {"front_body": "#2b2e33", "front_translucent": "#dfe9f2", "temple_translucent": "#dfe9f2", "temple": "#2b2e33", "pod": "#3a3d42",
       "lid": "#555b63", "liner": "#555b63", "cap": "#555b63", "lens": "#bfe3ff", "strip": "#e0e0e0",
       "nose": "#555b63"}
LIT = np.array([0.75, 1.0, 1.0])
OFF = np.array([0.20, 0.22, 0.25])


def colour(name):
    for k, v in COL.items():
        if name.startswith(k):
            return v
    return "#888888"


def led_points():
    """World points of the 10 LEDs, in data order per side (front strip, outer -> inner)."""
    return {side: [(g.SLOT_X[0] + 0.3, y, z) for y, z in g.leds_front(sign)]
            for sign, side in ((-1, "right"), (1, "left"))}


def meshes(angle=0.0):
    items, _ = a3.parts(angle)
    out = []
    for name, s in items:
        if name.startswith("ref_") or name.startswith("strip"):
            continue
        op = 0.35 if name.startswith("lens") else (0.8 if "translucent" in name else 1.0)
        out.append((rwn.to_mesh(s), colour(name), op))
    for side, pts in (led_points().items() if angle == 0.0 else []):
        n = len(pts)
        for i, p in enumerate(pts):
            a = max(np.exp(-((i - (n - 3)) / 2.2) ** 2), 0.12)
            c = OFF + (LIT - OFF) * a
            out.append((pv.Cube(center=p, x_length=1.6, y_length=1.6, z_length=1.6), c, 1.0))
            if a > 0.3:
                out.append((pv.Sphere(radius=1.5 + 3 * a, center=p), LIT, 0.3 * a))
    return out


def shot(ms, name, pos, focus, angle, head=True, bg="white"):
    p = pv.Plotter(off_screen=True, window_size=(1600, 1150))
    p.set_background(bg)
    if head:
        for m, c, o in rwn.head_meshes():
            p.add_mesh(m, color=c, opacity=0.55 if head == "faint" else o, smooth_shading=True)
    for m, c, o in ms:
        p.add_mesh(m, color=c, opacity=o, smooth_shading=False)
    p.camera_position = [pos, focus, (0, 0, 1)]
    p.camera.view_angle = angle
    p.enable_anti_aliasing("ssaa")
    p.screenshot(str(OUT / f"v3_{name}.png"))
    p.close()


def main():
    OUT.mkdir(exist_ok=True)
    ms = meshes()
    shot(ms, "front", (260, -20, 10), (0, 0, -12), 34, head="faint")
    shot(ms, "front_three_quarter", (230, -230, 90), (-50, 0, -20), 36)
    shot(ms, "right_side", (-70, -420, -10), (-70, 0, -30), 36)
    shot(ms, "rear_inside", (-60, 25, 15), (5, -40, -6), 55, head=False, bg="#20242a")
    shot(ms, "corner_top", (-10, -95, 60), (2, -62, -4), 40, head=False)
    shot(ms, "no_head_three_quarter", (180, -200, 120), (-60, 0, -20), 38, head=False)
    shot(ms, "hinge_top", (-6, -80, 45), (0, -70, -4), 32, head=False)
    fm = meshes((80.0, 90.0))
    shot(fm, "folded_rear", (-160, -60, 110), (0, 0, -20), 45, head=False)
    shot(fm, "folded_top", (20, 0, 260), (0, 0, -15), 45, head=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
