"""
Render the glasses mount as worn: every part placed on a simple head wearing glasses.

The band parts are printed flat, so here they are bent round the back of the head, along
with the trays in them. The sleeves are printed straight; here their front flaps are bent
round the glasses hinges and their necks bent down at the ears. Their leaves are shown
unloaded, so they cut into the temples where the real ones would turn aside. The head and
glasses are rough stand-ins of standard adult size, not models of anyone.

Run:  pip install build123d pyvista
      python render_worn.py   -> renders/worn_*.png, renders/sleeve_fit_range.png, renders/sleeve_printed.png
"""

import math
from pathlib import Path

import numpy as np
import pyvista as pv
from build123d import Pos, Rot

import glasses_mount as gm

OUT = Path(__file__).parent / "renders"

# ---------------------------------------------------------------- world frame and stand-ins
# World: X forward, Y to the wearer's left, Z up. The glasses hinges are at X = 0.
WT = 70.0                         # Half the distance between the temples' inner faces
HEAD = dict(center=(-100.0, 0.0, -12.0), radii=(97.0, 70.0, 112.0))
EAR = dict(x=-95.0, y=76.0, z=-28.0, radii=(13.0, 5.0, 29.0))

TPU = "#3a3d42"
PLA = "#f39c34"
SKIN = "#e8c4a8"
FRAME = "#1b1b1b"
LED = "#3cff8c"
SENSOR = "#6a3fb5"
LEVER = "#c62828"
SWITCH_LEVER = (3.0, 3.0, 7.5)    # Lever: slide-direction thickness, other thickness, length from the plate


def to_mesh(shape, tol=0.05):
    verts, tris = shape.tessellate(tol, 0.2)
    pts = np.array([(v.X, v.Y, v.Z) for v in verts])
    faces = np.hstack([[3, *t] for t in tris])
    return pv.PolyData(pts, faces)


def dense(mesh, edge=1.5):
    """Subdivide so the mesh can be bent smoothly."""
    return mesh.triangulate().subdivide_adaptive(max_edge_len=edge, max_tri_area=edge * edge)


def finish(mesh):
    return mesh.compute_normals(auto_orient_normals=True, split_vertices=True)


# ---------------------------------------------------------------- sleeves
# The sleeve is modelled straight, as printed. Fitted, its channel bends 90 degrees inward round
# the glasses hinge (the corner) and its neck bends down with the temple at the ear.
CORNER_Y = -gm.FLOOR                  # Bend about the channel floor
BEND_X, BEND_LEN = -gm.TEMPLE_STRAIGHT, 8.0   # Ear bend: where the reference temple bends, spread over 8 mm
BEND_Z = -gm.REF_T_BEND[1] / 2


def bend_points(p, corner=True):
    """Sleeve coordinates as printed -> as fitted on the reference glasses."""
    p = p.copy()
    # Corner: everything in front of x = -CLIP_FRONT wraps 90 degrees toward -y
    xa = -gm.CLIP_FRONT
    lc = gm.CORNER_X1 - xa
    r = lc / (math.pi / 2)
    m = p[:, 0] > xa if corner else np.zeros(len(p), bool)
    u, v = p[m, 0] - xa, p[m, 1] - CORNER_Y
    th = np.minimum(u, lc) / r
    rest = np.maximum(u - lc, 0)
    p[m, 0] = xa + (r + v) * np.sin(th)
    p[m, 1] = CORNER_Y - r + (r + v) * np.cos(th) - rest
    # Ear bend: everything behind it turns down by TIP_ANGLE
    xs = BEND_X + BEND_LEN / 2
    tm = math.radians(gm.TIP_ANGLE)
    r = BEND_LEN / tm
    m = p[:, 0] < xs
    u, v = xs - p[m, 0], p[m, 2] - BEND_Z
    th = np.minimum(u, BEND_LEN) / r
    rest = np.maximum(u - BEND_LEN, 0)
    p[m, 0] = xs - (r + v) * np.sin(th) - rest * math.cos(tm)
    p[m, 2] = BEND_Z - r + (r + v) * np.cos(th) - rest * math.sin(tm)
    return p


def fit(mesh, corner=True):
    mesh.points = bend_points(mesh.points, corner)
    return mesh


def led_points():
    """LED centres in sleeve coordinates, strip in place (as printed)."""
    y = -gm.IL_T + gm.LIP_T - 0.3
    return np.array([(x, y, gm.STRIP_ZC) for x in gm.LED_X])


def sensor_board():
    y0 = -gm.IL_T + gm.POD_LIP
    return gm.box(gm.ARM_X - gm.BOARD_L / 2, gm.ARM_X + gm.BOARD_L / 2, y0, y0 + gm.BOARD_T,
                  -gm.POD_DEPTH - gm.BOARD_H / 2, -gm.POD_DEPTH + gm.BOARD_H / 2)


def temple():
    """The reference glasses' temple, in fitted sleeve coordinates: inner face at y = 0, top edge
    at z = 0, tapering to the bend, then the tip sloping down behind the ear."""
    (w0, h0), (w1, h1) = gm.REF_T_FRONT, gm.REF_T_BEND
    xf, xb = 0.0, -gm.TEMPLE_STRAIGHT
    pts = []
    for y in (0.0, 1.0):
        pts += [(xf, y * w0, 0), (xb, y * w1, 0), (xb, y * w1, -h1), (xf, y * w0, -h0)]
    straight = pv.PolyData(np.array(pts), np.hstack([[4, 0, 1, 2, 3], [4, 4, 7, 6, 5], [4, 0, 4, 5, 1],
                                                     [4, 1, 5, 6, 2], [4, 2, 6, 7, 3], [4, 3, 7, 4, 0]])).triangulate()
    tw, th = gm.REF_TIP
    tip = to_mesh(gm.box(xb - gm.TIP_LEN, xb + 0.01, 0, tw, -th, 0))
    return fit(dense(straight, 1.0), False) + fit(dense(tip, 1.0), False)


def to_world(mesh, right):
    """Sleeve coordinates (y outward from the temple's inner face) to world: right temple at Y = -WT."""
    p = mesh.points.copy()
    p[:, 1] = -(WT + p[:, 1]) if right else WT + p[:, 1]
    mesh.points = p
    return mesh


def sleeve_meshes(right, with_arm):
    s = fit(dense(to_mesh(gm.sleeve(with_arm)), 1.0))
    out = [(to_world(s, right), TPU, 1.0), (to_world(temple(), right), FRAME, 1.0)]
    leds = pv.PolyData(bend_points(led_points()))
    out.append((to_world(leds.glyph(geom=pv.Sphere(radius=1.4), scale=False, orient=False), right), LED, 1.0))
    if with_arm:
        out.append((to_world(fit(to_mesh(sensor_board())), right), SENSOR, 1.0))
    return out


def stud_world():
    """Band stud base (where the band's inner face sits), right side, world coordinates."""
    p = bend_points(np.array([[gm.STUD_X, gm.GAP + gm.OL_T, gm.STUD_Z]]))[0]
    return p[0], WT + p[1], p[2]


# ---------------------------------------------------------------- band, bent round the head
class BandPath:
    """Path the band hangs along: down from the stud on each side, behind the ear, round the
    back of the neck like a neckband headset. How low it hangs is solved so its length from
    the back centre to the stud matches the band (center-module stud + band half to its middle
    adjustment hole). s > 0 runs toward the right side (-Y), s < 0 toward the left."""

    def __init__(self, stud_x):
        self.stud = stud_world()                         # Band's inner face sits on the arch's outer leg
        want = stud_x + gm.BAND_HALF_LEN + (gm.ADJ_HOLES // 2) * gm.ADJ_PITCH
        lo, hi = -60.0, -200.0
        for _ in range(40):                              # Solve the nape height for that length
            self.nape = (lo + hi) / 2
            self._table()
            if self.s[-1] < want:
                lo = self.nape
            else:
                hi = self.nape

    def _table(self):
        sx, sy, sz = self.stud
        side = [(sx, sy, sz), (-135.0, 66.0, -75.0), (-163.0, 42.0, self.nape + 7), (-180.0, 0.0, self.nape)]
        # Left half, nape, right half; then extend past each stud along the last direction
        pts = np.array(side + [(x, -y, z) for x, y, z in side[::-1][1:]])
        curve = pv.Spline(pts, 3001).points
        d = np.linalg.norm(np.diff(curve, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(d)])
        s -= s[-1] / 2
        ext = 60.0
        t0 = (curve[0] - curve[1]) / d[0]
        t1 = (curve[-1] - curve[-2]) / d[-1]
        self.pts = np.vstack([curve[0] + t0 * ext, curve, curve[-1] + t1 * ext])
        self.sv = np.concatenate([[s[0] - ext], s, [s[-1] + ext]])
        self.s = np.array([0.0, s[-1]])                  # s[-1]: back centre to stud

    def map(self, s, up, out):
        sv = s                                           # Path runs from the left (+Y) side to the right
        p = np.stack([np.interp(sv, self.sv, self.pts[:, i]) for i in range(3)], axis=1)
        h = 0.5
        t = np.stack([np.interp(sv + h, self.sv, self.pts[:, i]) - np.interp(sv - h, self.sv, self.pts[:, i])
                      for i in range(3)], axis=1)
        t /= np.linalg.norm(t, axis=1, keepdims=True)
        # Out from the head: away from a vertical axis through the head and neck
        r = p - np.array([-112.0, 0.0, 0.0])
        r[:, 2] = 0
        n = r - t * np.sum(r * t, axis=1, keepdims=True)
        n /= np.linalg.norm(n, axis=1, keepdims=True)
        u = np.cross(n, t)                               # Band "up", across its width
        return p + n * out[:, None] + u * up[:, None]


def trim_tail(mesh):
    """Cut a band half off just past the middle adjustment hole, as it would be cut when fitted."""
    keep = gm.BAND_HALF_LEN + (gm.ADJ_HOLES // 2) * gm.ADJ_PITCH + 5.0
    return mesh.clip(normal=(1, 0, 0), origin=(keep, 0, 0), invert=True)


def bend(mesh, path, s_of_x):
    p = mesh.points
    mesh.points = path.map(s_of_x(p[:, 0]), p[:, 1], p[:, 2])
    return mesh


def tray_in_socket(comp, at_x=0.0, port=True, port_down=False, switch=False, wire_exit="sides"):
    """Tray turned open-side-down into its socket, in band coordinates."""
    ol, ow, oh = gm.tray_outer(comp)
    t = Pos(0, 0, oh) * Rot(180, 0, 0) * gm.tray(comp, port=port, switch=switch, wire_exit=wire_exit)
    if port_down:
        t = gm.port_down(t)
    return Pos(at_x, 0, gm.BAND_T) * t


def band_meshes():
    ol, ow, oh = gm.tray_outer(gm.ITSY_BAY)
    stud_x = ow + 2 * gm.SOCKET_WALL
    stud_x = stud_x / 2 + 6.5                          # As in band_center()
    path = BandPath(stud_x)
    out = []

    center = dense(to_mesh(gm.band_center()))
    out.append((bend(center, path, lambda x: x), TPU, 1.0))
    tray_c = dense(to_mesh(tray_in_socket(gm.ITSY_BAY, port_down=True, switch=True)))
    out.append((bend(tray_c, path, lambda x: x), PLA, 1.0))
    # Switch lever, through the slot at the top of the center module
    lt, lw, ll = SWITCH_LEVER
    wall_in = ol / 2 - gm.TRAY_WALL                     # Inner face of the tray's end wall (now at the top)
    zc = gm.BAND_T + oh - (gm.TRAY_FLOOR + gm.SWITCH[2] / 2)
    lever = gm.box(-lt / 2, lt / 2, wall_in, wall_in + ll, zc - lw / 2, zc + lw / 2)
    out.append((bend(dense(to_mesh(lever)), path, lambda x: x), LEVER, 1.0))

    right = trim_tail(dense(to_mesh(gm.band_half())))
    out.append((bend(right, path, lambda x: stud_x + x), TPU, 1.0))

    bl, bw, bh = gm.tray_outer(gm.BATTERY_BAY)
    sl = bl + 2 * gm.SOCKET_WALL
    left = trim_tail(dense(to_mesh(gm.band_half(gm.BATTERY_BAY))))
    out.append((bend(left, path, lambda x: -(stud_x + x)), TPU, 1.0))
    tray_b = dense(to_mesh(tray_in_socket(gm.BATTERY_BAY, at_x=8.0 + sl / 2, port=False, wire_exit="end")))
    out.append((bend(tray_b, path, lambda x: -(stud_x + x)), PLA, 1.0))
    return out, path


# ---------------------------------------------------------------- head and glasses
def head_meshes():
    hx, hy, hz = HEAD["center"]
    head = pv.ParametricEllipsoid(*HEAD["radii"]).translate((hx, hy, hz))
    nose = pv.Cone(center=(hx + HEAD["radii"][0] + 8, 0, -30), direction=(1, 0, -0.35), height=26, radius=10, resolution=40)
    neck = pv.Cylinder(center=(-120, 0, -170), direction=(0, 0, 1), radius=55, height=130)
    out = [(head, SKIN, 1.0), (nose, SKIN, 1.0), (neck, SKIN, 1.0)]
    for side in (1, -1):
        ear = pv.ParametricEllipsoid(*EAR["radii"]).translate((EAR["x"], side * EAR["y"], EAR["z"]))
        out.append((ear, SKIN, 1.0))
    return out


def ellipse(cy, cz, x, ry, rz, n=80):
    t = np.linspace(0, 2 * math.pi, n)
    return np.stack([np.full(n, x), cy + ry * np.cos(t), cz + rz * np.sin(t)], axis=1)


def glasses_meshes():
    out = []
    lens_x, lens_y, lens_z, ry, rz = 5.0, 33.0, -4.0, 25.0, 19.0
    for side in (1, -1):
        rim = pv.Spline(ellipse(side * lens_y, lens_z, lens_x, ry, rz), 200).tube(radius=1.6)
        out.append((rim, FRAME, 1.0))
        lens = pv.ParametricEllipsoid(1.0, ry, rz).translate((lens_x, side * lens_y, lens_z))
        out.append((lens, "#bfe3ff", 0.25))
        # End piece from the rim's outer edge back to the hinge
        end = pv.Spline(np.array([(lens_x, side * (lens_y + ry), lens_z + 6), (3.0, side * (WT - 1), 2.0),
                                  (0.0, side * WT, 0.0)]), 20).tube(radius=1.8)
        out.append((end, FRAME, 1.0))
    bridge = pv.Spline(np.array([(lens_x, 9.0, 6.0), (lens_x + 1.5, 0.0, 8.0), (lens_x, -9.0, 6.0)]), 20).tube(radius=1.5)
    out.append((bridge, FRAME, 1.0))
    return out


# ---------------------------------------------------------------- render
def scene():
    meshes = head_meshes() + glasses_meshes()
    right_arm = gm.EAR_SIDE == "right"
    meshes += sleeve_meshes(True, right_arm) + sleeve_meshes(False, not right_arm)
    band, _ = band_meshes()
    return meshes + band


VIEWS = {
    "rear_three_quarter": ((-460, -340, 60), (-140, 0, -65)),
    "right_side": ((-90, -520, -10), (-90, 0, -40)),
    "front_three_quarter": ((260, -300, 120), (-60, 0, -15)),
    "rear": ((-620, 0, -10), (-140, 0, -70)),
}


def leaf_at(xr, sense, t):
    """Leaf outline turned about its root (rigid-leaf approximation) until its tip just touches
    a temple whose outer face is at y = t. Returns (outline, turn in degrees)."""
    pts = np.array(gm.leaf_outline(xr, sense))
    root = np.array([xr, gm.GAP])

    def turned(deg):
        a = math.radians(deg) * sense          # Positive turns fold the leaf toward the outer leg
        c, s = math.cos(a), math.sin(a)
        q = pts - root
        return np.stack([root[0] + q[:, 0] * c - q[:, 1] * s, root[1] + q[:, 0] * s + q[:, 1] * c], axis=1)

    lo, hi = 0.0, 89.0
    if turned(0)[:, 1].min() >= t:
        return turned(0), 0.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if turned(mid)[:, 1].min() < t:
            lo = mid
        else:
            hi = mid
    return turned(hi), hi


def render_fit_range():
    """Plan and section of one clip on temples 2, 4 and 6 mm thick."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    x0, x1 = gm.clip_spans()[0]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.2), gridspec_kw={"width_ratios": [2.2, 1]})
    cases = [(2.0, 3.0, "#1e63c8"), (gm.REF_T_FRONT[0], gm.REF_T_FRONT[1], "#2e7d32"), (6.0, 10.0, "#d32f2f")]

    # Plan from below, 1 mm under the temple's top edge
    ax1.add_patch(Rectangle((x0 - 4, -gm.IL_T), x1 - x0 + 8, gm.IL_T, color="#6b7078"))
    ax1.add_patch(Rectangle((x0, gm.GAP), x1 - x0, gm.OL_T, color="#6b7078"))
    for xr, sense in gm.leaf_roots(x0, x1):
        ax1.add_patch(Polygon(gm.leaf_outline(xr, sense), closed=True, fill=False, ls="--", ec="#444", lw=1))
    for t, h, col in cases:
        ax1.plot([x0 - 4, x1 + 4], [t, t], color=col, lw=1.2, ls=":")
        for xr, sense in gm.leaf_roots(x0, x1):
            outline, deg = leaf_at(xr, sense, t)
            ax1.add_patch(Polygon(outline, closed=True, color=col, alpha=0.55))
        ax1.text(x1 + 4.5, t, f"{t:g} mm temple: leaves turn {deg:.0f}°", va="center", color=col, fontsize=10)
    ax1.text(x0 - 3.5, -gm.IL_T / 2, "inner leg (LED channel on the far side)", va="center", color="white", fontsize=8.5)
    ax1.text((x0 + x1) / 2, gm.GAP + gm.OL_T / 2, "outer leg", ha="center", va="center", color="white", fontsize=8.5)
    ax1.text(x0 - 3.5, (gm.GAP) / 2, "temple\nface", fontsize=8.5, color="#555")
    ax1.set_xlim(x0 - 5, x1 + 30)
    ax1.set_ylim(-gm.IL_T - 1, gm.GAP + gm.OL_T + 1)
    ax1.set_aspect("equal")
    ax1.set_title("Plan, from below: dashed = leaves unloaded; filled = touching each temple (rigid-leaf estimate)", fontsize=10)
    ax1.set_xlabel("x along the temple (mm)")
    ax1.set_ylabel("y outward (mm)")

    # Section across the clip at an end bridge, with a leaf seen end-on behind it
    sec = [(-gm.IL_T, gm.IL_Z0), (0, gm.IL_Z0), (0, 0), (gm.GAP, 0), (gm.GAP, -gm.OL_H), (gm.GAP + gm.OL_T, -gm.OL_H),
           (gm.GAP + gm.OL_T, gm.CLIP_T), (-gm.IL_T, gm.CLIP_T)]
    ax2.add_patch(Polygon(sec, closed=True, color="#6b7078"))
    ch = [(-gm.IL_T, gm.CH_Z0), (-gm.IL_T + gm.CH_D, gm.CH_Z0), (-gm.IL_T + gm.CH_D, gm.CH_Z1), (-gm.IL_T, gm.CH_Z1)]
    ax2.add_patch(Polygon(ch, closed=True, color="white"))
    ax2.add_patch(Rectangle((-gm.IL_T + gm.LIP_T + 0.2, gm.STRIP_ZC - gm.STRIP_W / 2), gm.STRIP_PCB, gm.STRIP_W, color="#111"))
    ax2.add_patch(Rectangle((-gm.IL_T + gm.LIP_T - 0.7, gm.STRIP_ZC - 1), 0.9, 2, color="#3cff8c"))
    leaf = [(gm.LEAF_REST, gm.CLIP_T), (gm.GAP, gm.CLIP_T), (gm.GAP, -gm.OL_H),
            (gm.LEAF_REST, -gm.OL_H + (gm.GAP - gm.LEAF_REST) * gm.RAMP)]
    ax2.add_patch(Polygon(leaf, closed=True, color="#9aa0a8", alpha=0.6))
    for t, h, col in cases:
        ax2.add_patch(Rectangle((0, -h), t, h, fill=False, ec=col, lw=1.6))
        ax2.text(t + 0.15, -h + 0.2, f"{t:g}×{h:g}", color=col, fontsize=9)
    ax2.text(-gm.IL_T - 0.3, gm.STRIP_ZC, "LED strip", ha="right", va="center", fontsize=9)
    ax2.text((gm.LEAF_REST + gm.GAP) / 2, -2.2, "leaf\n(end-on)", ha="center", fontsize=8.5)
    ax2.annotate("lead-in: pushing down\nturns the leaves aside", xy=(4.0, -6.2), xytext=(1.0, -12.5), fontsize=8.5,
                 arrowprops=dict(arrowstyle="->", color="#444"))
    ax2.set_xlim(-gm.IL_T - 4.5, gm.GAP + gm.OL_T + 1)
    ax2.set_ylim(-13.5, gm.CLIP_T + 1)
    ax2.set_aspect("equal")
    ax2.set_title("Section at a clip end, temples outlined", fontsize=10)
    ax2.set_xlabel("y outward (mm)")
    ax2.set_ylabel("z up (mm)")
    fig.tight_layout()
    fig.savefig(OUT / "sleeve_fit_range.png", dpi=130)
    plt.close(fig)
    print("wrote", OUT / "sleeve_fit_range.png")


def render_printed():
    """Both sleeves as they come off the printer, and the front test piece."""
    p = pv.Plotter(off_screen=True, window_size=(1800, 1000))
    p.set_background("white")
    right_arm = gm.EAR_SIDE == "right"
    y = 0.0
    for shape in (gm.print_orient_sleeve(gm.sleeve(right_arm)), gm.print_orient_sleeve(gm.test_piece())):
        m = to_mesh(shape).translate((0, y, 0))
        p.add_mesh(finish(m), color="#5b6068", smooth_shading=True, specular=0.2)
        y += shape.bounding_box().size.Y + 25
    p.add_mesh(pv.Plane(center=(80, 30, -0.05), i_size=200, j_size=110), color="#d8d2c4")
    p.camera_position = [(-40, -120, 150), (75, 25, 8), (0, 0, 1)]
    p.camera.view_angle = 32
    p.enable_anti_aliasing("ssaa")
    p.screenshot(str(OUT / "sleeve_printed.png"))
    p.close()
    print("wrote", OUT / "sleeve_printed.png")


def main():
    OUT.mkdir(exist_ok=True)
    render_fit_range()
    render_printed()
    meshes = scene()
    for name, (pos, focus) in VIEWS.items():
        p = pv.Plotter(off_screen=True, window_size=(1600, 1200))
        p.set_background("white")
        for m, color, opacity in meshes:
            p.add_mesh(finish(m) if isinstance(m, pv.PolyData) and m.n_cells else m, color=color,
                       opacity=opacity, smooth_shading=True, specular=0.2,
                       ambient=0.5 if color == LED else 0.15)
        p.camera_position = [pos, focus, (0, 0, 1)]
        p.camera.view_angle = 26
        p.enable_anti_aliasing("ssaa")
        p.screenshot(str(OUT / f"worn_{name}.png"))
        p.close()
        print("wrote", OUT / f"worn_{name}.png")


if __name__ == "__main__":
    main()
