"""
Render the one-piece temple parts (onepiece.py) on the stand-in head and glasses, with the pods
from mount_v2.py, and a frozen moment of a breath wave on the LEDs in direct view.

Run:  python render_onepiece.py   -> renders/onepiece_*.png
"""

import numpy as np
import pyvista as pv

import onepiece as op
import render_v2 as rv
from render_v2 import rw

OUT = rv.OUT
NATURAL_PETG = "#dfe9f2"


def onepiece_meshes(right):
    out = []
    mesh = rw.to_mesh(op.part())
    mesh.points = rv.world(mesh.points, right)
    out.append((mesh, NATURAL_PETG, 0.75))
    for xc in op.CLIPS:
        cm = rw.to_mesh(op.clip(xc))
        cm.points = rv.world(cm.points, right)
        out.append((cm, rw.TPU, 1.0))
    leds = op.led_path()
    crest = leds[-3]
    for s in leds:
        x, y = op.path_point(s, op.WALL_OUT + op.SLOT_T / 2)
        p = rv.world((x, y, op.ZS0 + op.STRIP_W / 2), right)
        front = x > rv.FRONT_X
        a = max(np.exp(-((s - crest) / 7.0) ** 2), 0.15) if front else None
        c = rv.GLOW if a is None else rv.OFF + (rv.LIT - rv.OFF) * a
        out.append((pv.Cube(center=p, x_length=1.6, y_length=1.6, z_length=1.6), c, 1.0))
        if a is not None and a > 0.3:
            out.append((pv.Sphere(radius=2 + 4 * a, center=p), rv.LIT, 0.35 * a))
    return out


def scene(head=True):
    meshes = (rw.head_meshes() if head else []) + rw.glasses_meshes()
    for right in (True, False):
        meshes.append((rw.to_world(rw.temple(), right), rw.FRAME, 1.0))
        meshes += onepiece_meshes(right)
    pods, r, l, lobe = rv.pod_meshes()
    therm, bead = rv.thermistor_meshes()
    return meshes + pods + therm, dict(r=r, l=l, lobe=lobe, bead=bead)


def shot(meshes, name, pos, focus, angle, background="white", labels=None):
    p = pv.Plotter(off_screen=True, window_size=(1800, 1300))
    p.set_background(background)
    rv.add(p, meshes)
    if labels:
        rv.label(p, *labels)
    p.camera_position = [pos, focus, (0, 0, 1)]
    p.camera.view_angle = angle
    p.enable_anti_aliasing("ssaa")
    p.screenshot(str(OUT / f"onepiece_{name}.png"))
    p.close()


def main():
    OUT.mkdir(exist_ok=True)
    corner = rv.world((*op.path_point(op.ARC_L / 2, op.BAND_T), op.ZS1), True)
    rail = rv.world((-50.0, -op.BAND_T, -4.0), True)
    meshes, at = scene(head=False)
    shot(meshes, "inside_right", (-120, 30, 40), (-10, -60, -5), 40, "#20242a",
         ([corner + [-4, 8, 8], rail + [0, 8, 6]],
          ["Curve round the corner: 5 LEDs in direct view", "One-piece PETG rail; soft-flex clips under it"]))
    meshes, at = scene(head=False)
    shot(meshes, "top_right", (10, -60, 220), (-10, -60, -5), 40, "white")
    meshes, at = scene()
    shot(meshes, "rear_three_quarter", (-430, -360, 70), (-110, 0, -40), 30)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
