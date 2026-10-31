"""Downward-facing faces steeper than 45 deg past vertical, above the bed, in print-oriented STLs.

Usage:  python overhang.py out/stl/part_flex.stl [more.stl ...]
Lists total overhang area per file, then up to 12 heights with their area and x/y extent, so you
can tell a 1 mm lip or a short bridge (fine) from a real unsupported face (fix the model or the
print orientation).
"""
import sys

import numpy as np
import pyvista as pv

for f in sys.argv[1:]:
    m = pv.read(f).compute_normals(cell_normals=True, point_normals=False)
    n = m.cell_data["Normals"]
    c = m.cell_centers().points
    a = m.compute_cell_sizes()["Area"]
    bad = (n[:, 2] < -0.7072) & (c[:, 2] > 0.05)
    print(f"{f.split('/')[-1]:28s} overhang area {a[bad].sum():6.1f} mm2")
    if bad.any():
        for z in np.unique(np.round(c[bad, 2], 1))[:12]:
            sel = bad & (np.round(c[:, 2], 1) == z)
            lo, hi = c[sel].min(0), c[sel].max(0)
            print(f"   z={z:5.1f}  area {a[sel].sum():5.1f}  x {lo[0]:.1f}..{hi[0]:.1f}  y {lo[1]:.1f}..{hi[1]:.1f}")
