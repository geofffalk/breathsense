"""
Render the proposed v2 hardware on the stand-in head and glasses from ../glasses/render_worn.py.

Shows the PETG rails (size M, from mount_v2.py) and soft-flex corners on the temples, and a
frozen moment of a breath wave: the front LEDs (corner and the first 15 mm of temple) light as
a travelling crest, the rest of the temple glows dimly. The pods, cord and thermistor are
rough blocks for layout only; they are not modelled yet.

Run:  python render_v2.py   -> renders/v2_*.png
"""

import math
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).parent.parent / "glasses"))
sys.path.insert(0, str(Path(__file__).parent))
import glasses_mount as gm   # noqa: E402
import render_worn as rw     # noqa: E402
import mount_v2 as mv        # noqa: E402

OUT = Path(__file__).parent / "renders"

FRONT_X = -15.0                    # LEDs in front of this are in direct view
RAIL_SIZE = "M"                    # The reference glasses' temples (4.0 and 3.5 mm) take the M rail
PETG = "#7d93a8"
LIT = np.array([0.75, 1.00, 1.00])
GLOW = np.array([0.10, 0.35, 0.45])
OFF = np.array([0.20, 0.22, 0.25])
POD = "#2b2e33"
BOARD = "#1565c0"
BATTERY = "#9e9e9e"
CORD = "#444444"
THERM = "#ff7043"
LED_Y = mv.CH_Y0 + mv.LIP_T - 0.2       # LED faces, just inside the channel mouth
LED_Z = (mv.CH_Z0 + mv.CH_Z1) / 2


def world(p, right):
    """Rail coordinates (y outward from the temple's inner face) to world."""
    p = np.array(p, float)
    p[..., 1] = -(rw.WT + p[..., 1]) if right else rw.WT + p[..., 1]
    return p


def led_positions():
    """(path length along the strip, rail-coordinate point) for the 10 LEDs on the strip's centre
    line, corner at 90 degrees."""
    return [(p, (x, y, LED_Z)) for p, (x, y) in zip(mv.led_path(), mv.led_points(90.0))]


def led_levels(leds, crest_s=None, width=6.0):
    """Wave crest on the LEDs in direct view (0..1), None for the temple's dim glow."""
    if crest_s is None:
        crest_s = mv.led_path()[-2]
    return [max(math.exp(-((s - crest_s) / width) ** 2), 0.15) if p[0] > FRONT_X else None for s, p in leds]


def strip_meshes(right):
    """Rail, corner piece and LEDs on one side."""
    rail = mv.rail(RAIL_SIZE)
    corner = mv.corner(angle=90.0)
    out = []
    for shape, colour in ((rail, PETG), (corner, rw.TPU)):
        mesh = rw.to_mesh(shape)
        mesh.points = world(mesh.points, right)       # world() mirrors the left side
        out.append((mesh, colour, 1.0))
    leds = led_positions()
    for (_, p), a in zip(leds, led_levels(leds)):
        c = GLOW if a is None else OFF + (LIT - OFF) * a
        out.append((pv.Cube(center=world(p, right), x_length=1.6, y_length=0.8, z_length=1.6), c, 1.0))
        if a is not None and a > 0.3:
            out.append((pv.Sphere(radius=2 + 4 * a, center=world(p, right)), LIT, 0.35 * a))
    return out


POD_SIZE = "M"                     # The reference tips (3.5 x 4.5 mm) take the M pods


def placed(shape, right):
    """A pod part (straight coordinates, as returned by mount_v2) bent onto the tip and put in
    the world. Left parts are modelled on the right; world() mirrors them."""
    mesh = rw.to_mesh(shape)
    mesh.points = world(rw.bend_points(mesh.points, False), right)
    return mesh


def placed_point(p, right):
    return world(rw.bend_points(np.array([p], float), False)[0], right)


def pod_meshes():
    out = []
    pod, lid, arm, d = mv.board_pod(POD_SIZE)
    for shape, colour in ((pod, PETG), (lid, rw.TPU), (arm, rw.TPU)):
        out.append((placed(mv.worn_pod(shape), True), colour, 1.0))
    h = gm.REF_TIP[1]
    flip = lambda x, y, z: (x, y, -z - h)          # Same flip as mv.worn_pod, for single points
    r_label = placed_point(flip(d["xm"], d["y1"], d["zb"] + 6), True)
    rx = (d["xa"] + mv.POD_WALL + d["xm"] - mv.XIAO[0] / 2) / 2
    r_cord = placed_point(flip(rx, d["cy0"] + 1.8, d["zb"]), True)
    lobe = placed_point(flip(d["xa"] - mv.ARM_OUT - mv.ARM_W / 2, d["y1"], mv.ARM_UP + 12), True)

    bat, blid, bd = mv.battery_pod(POD_SIZE)
    for shape, colour in ((bat, PETG), (blid, rw.TPU)):
        out.append((placed(mv.worn_pod(shape), False), colour, 1.0))
    l_cord = placed_point(flip(bd["xa"], bd["cy0"] + 1.8, bd["zb"] + mv.POD_WALL + 7.75), False)

    # Cord round the back of the head
    hx = rw.HEAD["center"][0] - rw.HEAD["radii"][0]
    cord = np.array([r_cord, r_cord + [-12, 4, 2], (-175, -55, -40), (hx - 4, 0, -48), (-175, 55, -40),
                     l_cord + [-14, -4, 0], l_cord])
    out.append((pv.Spline(cord, 160).tube(radius=1.2), CORD, 1.0))
    return out, r_label, placed_point(flip(bd["xm"], bd["y1"], bd["zb"] + 6), False), lobe


def thermistor_meshes():
    """Bead on the right nose pad, its wire along the lower rim to the right hinge."""
    bead = np.array([8.0, -9.0, -20.0])
    t = np.linspace(math.radians(215), math.radians(345), 30)
    rim = np.stack([np.full(len(t), 6.0), -33 + 26 * np.cos(t), -4 + 20 * np.sin(t)], axis=1)
    rim = rim[::-1] * [1, 1, 1]
    wire = np.vstack([bead, rim, [(2.0, -rw.WT + 1, -2.0), (0.0, -rw.WT - 0.5, -3.0)]])
    return [(pv.Sphere(radius=1.6, center=bead), THERM, 1.0),
            (pv.Spline(wire, 120).tube(radius=0.5), THERM, 1.0)], bead


def scene(head=True):
    meshes = (rw.head_meshes() if head else []) + rw.glasses_meshes()
    for right in (True, False):
        meshes.append((rw.to_world(rw.temple(), right), rw.FRAME, 1.0))
        meshes += strip_meshes(right)
        for shape in (mv.diffuser(),) + mv.corner_caps(90.0):
            dfu = rw.to_mesh(shape)
            dfu.points = world(dfu.points, right)
            meshes.append((dfu, "#eef4ff", 0.45))
    pods, r, l, lobe = pod_meshes()
    therm, bead = thermistor_meshes()
    return meshes + pods + therm, dict(r=r, l=l, lobe=lobe, bead=bead)


def add(p, meshes):
    for m, colour, opacity in meshes:
        lit = not isinstance(colour, str)
        p.add_mesh(m, color=colour, opacity=opacity, smooth_shading=True, specular=0.2,
                   ambient=0.9 if lit else 0.15, diffuse=0.3 if lit else 1.0)


def label(p, pts, texts):
    p.add_point_labels(np.array(pts), texts, font_size=22, point_size=1, shape_opacity=0.85,
                       shape_color="white", text_color="black", always_visible=True, margin=4)


def main():
    OUT.mkdir(exist_ok=True)
    right_front = world((mv.RAIL_X1 + 6, LED_Y, LED_Z), True)
    right_temple = world((-55.0, LED_Y, LED_Z), True)

    # Outside, rear three-quarter: pods, cord, earlobe sensor
    meshes, at = scene()
    p = pv.Plotter(off_screen=True, window_size=(1800, 1300))
    p.set_background("white")
    add(p, meshes)
    label(p, [at["r"] + [0, -10, 0], at["lobe"] + [0, -6, -4], (-200, -10, -50), right_temple + [0, -6, 8]],
          ["XIAO pod (button, USB-C at the top)", "MAX30101 arm (soft flex)", "Cord to the battery pod",
           "PETG rail, size M"])
    p.camera_position = [(-430, -360, 70), (-110, 0, -40), (0, 0, 1)]
    p.camera.view_angle = 30
    p.enable_anti_aliasing("ssaa")
    p.screenshot(str(OUT / "v2_rear_three_quarter.png"))
    p.close()

    # Inside, head hidden: what faces the wearer at the right hinge
    meshes, at = scene(head=False)
    p = pv.Plotter(off_screen=True, window_size=(1800, 1300))
    p.set_background("#20242a")
    add(p, meshes)
    label(p, [right_front + [4, 10, 10], right_temple + [0, 8, 10], at["bead"] + [0, 6, -8]],
          ["Front LEDs: travelling wave (in direct view)", "Temple LEDs: glow only (out of direct view)",
           "Thermistor on the nose pad"])
    p.camera_position = [(-120, 30, 40), (-10, -60, -5), (0, 0, 1)]
    p.camera.view_angle = 40
    p.enable_anti_aliasing("ssaa")
    p.screenshot(str(OUT / "v2_inside_right.png"))
    p.close()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
