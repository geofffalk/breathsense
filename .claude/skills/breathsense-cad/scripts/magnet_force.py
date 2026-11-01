"""Pull between two coaxial stacks of disc magnets facing each other across a gap (attracting),
by the charged-surface model with numerical integration.

Usage:  python magnet_force.py DIAMETER_MM THICKNESS_MM PER_SIDE GAP_MM [GAP_MM ...]
e.g.    python magnet_force.py 9.5 0.8 3 5.75 11.25   (earlobe clip: 2.5 and 8 mm lobes + 3.25)
        python magnet_force.py 2 1 2 3.8              (nose clip: 3 mm wing + 2 x 0.4 skins)
Gap = tissue thickness + everything between the magnet faces (PCB, parts, plastic skins).
Assumes Br = 1.2 T: N35 neodymium, the usual unlabelled grade (N52 is about 1.45 T, ~1.45x the pull;
ferrite about 0.4 T, ~1/9). Treat results as +-30%.
"""
import sys

import numpy as np

mu0 = 4e-7 * np.pi
Br = 1.2
M = Br / mu0


def bz_disc(r, z, R):
    """Axial field at (r, z) from a uniformly charged disc of radius R (sigma = M) at z = 0."""
    n = 60
    rs = (np.arange(n) + 0.5) / n * R
    dr = R / n
    th = (np.arange(64) + 0.5) / 64 * 2 * np.pi
    dth = 2 * np.pi / 64
    Rr, T = np.meshgrid(rs, th)
    d2 = r ** 2 + Rr ** 2 - 2 * r * Rr * np.cos(T) + z ** 2
    return (mu0 * M / (4 * np.pi)) * np.sum(z / d2 ** 1.5 * Rr * dr * dth)


def force(R, t1, t2, gap):
    """Newtons between a magnet of thickness t1 (faces at 0 and -t1) and one of thickness t2
    (faces at gap and gap + t2), radius R, all in metres."""
    n = 12
    rs = (np.arange(n) + 0.5) / n * R
    dr = R / n
    F = 0.0
    for zf, sB in ((gap, 1), (gap + t2, -1)):
        for r in rs:
            B = bz_disc(r, zf, R) - bz_disc(r, zf + t1, R)
            F += sB * M * B * 2 * np.pi * r * dr
    return abs(F)


if __name__ == "__main__":
    d, t, n = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
    for g in map(float, sys.argv[4:]):
        f = force(d / 2e3, n * t / 1e3, n * t / 1e3, g / 1e3)
        print(f"{n} x {d} x {t} mm per side, gap {g} mm: {f:.3f} N")
