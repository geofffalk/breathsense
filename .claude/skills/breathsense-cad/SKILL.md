---
name: breathsense-cad
description: BreathSense 3D-printed hardware in build123d (hardware/v2 and hardware/glasses) - the v2 parts (one-piece temple part, hang pods, magnetic MAX30101 earlobe clip, thermistor nose clip), assembly and print layout, coordinate and handedness conventions, the Python environment, geometry checks (solids, overlaps, overhangs, magnet pull), rendering, PETG and soft-flex printing, Fusion hand-off, and lessons learned. Use for any CAD, printing or fit work.
---

# BreathSense CAD

All parts are parametric **build123d** Python scripts; units mm. Spec and status live in
`hardware/v2/README.md` ("Mount" section onward) - keep it updated when parts change.

## Environment

```
~/.venvs/breathsense-cad/bin/python      # Python 3.11, build123d 0.13, pyvista, numpy
```
If missing: `/usr/local/bin/python3.11 -m venv ~/.venvs/breathsense-cad && ~/.venvs/breathsense-cad/bin/pip install build123d pyvista numpy`
(system `python3` is 3.9, which only gets build123d 0.8 - too old). Run scripts from
`hardware/v2/` (they add `../glasses` to `sys.path`).

Bundled checks (in this skill's `scripts/`):
- `overhang.py STL…` - downward faces > 45° above the bed in print-oriented STLs, by height.
- `magnet_force.py D T N GAP…` - pull between two N-disc stacks across a gap (±30%).

## Files (`hardware/v2/`)

| Script | Makes | Notes |
|---|---|---|
| `onepiece.py` | `onepiece_right_petg`, `onepiece_left_petg`, `onepiece_band_flex` | One PETG part per temple: slot for the 10-LED strip (2.2 mm wide for the 1.2 mm strip, open top with no tabs - 0.4 mm tabs on a 1.6 mm slot blocked the strip; held by its stiffness in the curve, the band over its end, silicone if needed; wall 0.8 mm, thinned from inside to a 0.45 mm `SKIN` over a 3.4 × 3 mm patch per LED; print in translucent PETG), 18 mm-radius rigid curve round the hinge onto the frame front's back face, above the lens; rail to 60 mm behind the hinge; top hook + ONE closed soft-flex band, 6 mm, just behind the last LED (45-51 mm) - a band between LEDs covers light, so never put one on the LED run; 0.3 mm squeeze; 0.5 mm grooves in top, hook lip and plate bottom, none in the 0.8 mm head-side wall (0.4 mm left was too thin); slid on over the tip with the pod off - open C-clips fell off, TPE too soft. Glasses can't fold while fitted |
| `hang_pods.py` | `hang_pod_board_petg`, `hang_pod_battery_petg`, `hang_lid_*_flex`, `hang_liner_flex` (×2), `hang_back_clip_flex` (×2) | Pods over the last 22 mm of each temple-tip paddle, lined with soft flex, held by a closed soft-flex band (`back_clip()`, 8 mm, 11-19 mm from the paddle end) in a groove round the pocket (0.7 mm faces/edge, 0.3 mm top edges); bands go on over the bare tip before the pod; body continues down behind the earlobe. Board pod: XIAO on two 1 mm rails (`BOARD_LIFT`: battery wires on its back pads), 16 mm `BAY` in front of it for the LED switch's stripboard (`switch_board.svg`, ~15 × 22 mm, 1.5 mm board, parts flat, `SWITCH_STACK` 5.7 mm tall; transistor end toward the back wall), USB-C at far end, Omron B3F button in back wall (base `BUTTON` 5 × 3 mm, round 3.8 mm plunger hole), earlobe lead hole (4 mm) and nose-clip pogo socket (4.1 mm, 7 mm behind it) in the ear-side wall. `board_pod(sensor="lobe"|"head")` returns `(pod, lid, d)`; `d["lead_exit"]`, `d["pogo"]`, `d["board_y"]`. **Head variant** (`hang_pod_board_head_petg`, `hang_lid_board_head_flex`, `hang_liner_head_flex`; `head_frame()`, `liner_head()`, `assembly_onepiece_head.step`, print_layout's third row): MAX30101 in the pocket's head-side wall at the paddle's end, where the user's temple presses (4-5 mm from its end): board back on the paddle (liner cut away), parts out through a window with lobe-clip-style rims/corner tabs/tab cover in the PETG wall, chip edge toward the ear bend, chip 0.8 mm proud (the board's 3.15 mm minus the pocket's 2.35). Board runs back under the body floor; slides in from the cavity through a slot in the front wall. Pod 9.4 mm thick (`HEAD_DEEPER` 1.6: the switch board's resistor end sits over the sensor's back and wires; its transistor end past the sensor's edge), own band `hang_back_clip_head_flex`; both pods 62 mm long. Temple grip presses it: no springs. History: a first head variant put the sensor in the body's head wall on soft bows + shelf (pod 11.9 mm) - rejected: chip ~14 mm past the tip's end, where the head curves away, so it would hang in air; user wanted it under the actual temple and the offset under ~1 mm (3.5-4 mm "too wide") |
| `lobe_clip.py` | `lobe_clip_flex` | Universal magnetic earlobe clip for the Pimoroni MAX30101 (see below) |
| `nose_clip.py` | `nose_clip_w25_flex` … `w40_flex` | Thermistor U band on the right nostril's wing, one per wing thickness (see below) |
| `assembly_onepiece.py` | `out/assembly_onepiece.step` | Both sides as worn on stand-in glasses, ear, lobes (small/mid/large) and nostril wing; leads drawn; prints lead cut lengths. Checks overlaps only by intersecting bodies |
| `print_layout.py` | `out/print_layout.step` | Every print part in print orientation, PETG row then flex row, one named body per copy |
| `render_onepiece.py`, `render_v2.py` | `renders/*.png` | pyvista renders |
| `mount_v2.py` | (superseded parts) | Still imported for helpers and constants: `_to_bed`, `print_orient_lid`, `POD_WALL` 1.2, `LID_T`, `XIAO` (17.8, 21.0, 1.0, 3.2), `USB_W` 9.2, `BATTERY` (34, 21, 5.6) |

`../glasses/glasses_mount.py` (v1 sleeves) supplies helpers `box(x0,x1,y0,y1,z0,z1)`,
`y_cyl(x,z,y0,y1,d)`, `xz_prism(pts,y0,y1)`, `yz_prism(pts,x0,x1)` and the measured glasses:
`TEMPLE_STRAIGHT` 99, `TIP_LEN` 39, `TIP_ANGLE` 40°, `REF_T_FRONT` (4.0, 8.1), `REF_T_BEND`
(3.2, 4.0). Paddle: 4.0 thick, 6.3 tall 20 mm back growing to 8.5 at the end.

Outputs: `out/step/*.step` as modelled, `out/stl/*_{petg|flex}.stl` already in print orientation
(don't rotate in the slicer). Each script's `__main__` writes its own; old STLs without a material
suffix are from superseded designs.

## Conventions

- **Frames:** x forward, y outward from the temple's inner face (pods/temple) or from the skin
  (clips), z up. Each script's docstring states its frame. Temple parts are modelled straight;
  `assembly_onepiece.onto_tip()` turns pod parts down 40° about the ear bend.
- **Handedness:** y-outward in a right-handed frame is the LEFT side. Right-side exports are
  `mirror(part, Plane.XZ)`. Never mirror twice (broken solids) - use `Rot(180,0,0)` or the
  `flipped_pod` path in `place()`. Exports before 28 Oct 2026 had right/left swapped.
- **Print orientation** functions live with each part (`print_orient*`), ending in
  `mv._to_bed()`.
- **Named bodies for Fusion:** set `shape.label`, wrap in `Compound(children=[…], label=…)`,
  `export_step`. Open with `open -a "Autodesk Fusion" file.step` (opens a new tab each time;
  re-running a script overwrites the STEP, so the user saves edits as .f3d).
- Constants at the top of each script, ALL_CAPS, each with a short trailing comment saying what it
  is and, when guessed, "(check yours)". Keep that style.

## Earlobe clip (`lobe_clip.py`)

One soft-flex part, printed flat skin side down: back pad (board pocket + flap on a living hinge
holding the magnets), a 32 mm floppy keeper strap from the pad's bottom edge round the lobe's free
edge, and a 15.5 mm front puck (magnet behind a lip, closed by a living-hinge lid at its +x side whose plug fills the lip opening; `puck_lid`/`puck_lid_open`). Magnets (one 12 × 3 mm neodymium disc each side, 50-pack from Amazon UK B088FNGGNQ, grade unstated so assume N35; the user's first black 9.5 × 0.8 discs were ferrite, ~1/9 the pull, and felt like nothing) set the sensor's position, so one
size fits lobes 13-27 mm tall and 2.5-8 mm thick; spare strap hangs as a loop.
- Board `MAX_BOARD = (19, 19, 1.6, 1.55)`, tab `BOARD_TAB = (15, 5)`, `CHIP_OFFSET = (0, 7.2)`
  (chip 2.3 mm below top edge - from a photo, unverified), `POCKET_FIT` 0.1.
- Chip face stands `CHIP_PROUD` 0.5 mm proud of the pad face. Front retention on all four edges:
  0.8 mm side rims, 3.5 × 1.5 mm top-corner tabs (round the mounting holes, clear of the chip), a
  cover over the pin tab with a 0.5 mm solder recess. Back lips along the side edges only.
- Magnets centred `MAG_Z` = -4.6 mm below the chip (can't centre: chip at top edge; the boss clears
  the pin tab by 0.4 mm). Gap = lobe + 3.25 mm → ~2.9 N at 2.5 mm, 1.6 N at 5 mm, 0.8 N at 8 mm.
  `FLAP_T` grows to leave `MAG_FLOOR` behind the magnet (2.2 mm); pad 6.4 mm thick, puck 4.2 mm.
  `magnet_force.py` assumes N35 (Br 1.2 T); N52 is ~1.45x, ferrite is ~1/9 (Br^2) - check the user's magnets' material.
- Wires solder to the pins from the back, run behind the tab, out a 4.4 × 3.9 mm slot in the rear
  wall (side away from the hinge). `LEAD_OUT` gives the exit point; lead 70 mm.

## Nose clip (`nose_clip.py`)

Soft-flex U band (4 mm wide, 1.2 mm thick, legs 6 mm above the bend) over the right nostril's
wing rim, printed flat on its back face. Shaped to the wing: legs `SQUEEZE` 0.8 mm closer than the
wing, so grip is ~0.15-0.2 N on its own size (`grip()`: each leg a cantilever from the bend, E 25
MPa). `FITS` 2.5-4.0 mm exported as `nose_clip_w<10×fit>_flex`; `WING` 3.0 is the default/display
size. `clip(gap, fit)` shows it worn (halves moved apart, joined under the bend, dropped so the rim
clears). Stalk off the inside leg's top: bead 2.5 mm off the wing, 1.5 mm above the legs; the stalk
carries on down as a post, solid with the inside leg, with one straight 1 mm diamond
tunnel down both for the sleeved leads (45° roof as printed, no bridge; the user wanted a tunnel to
slot the thermistor into, not an open groove to glue it in) (an eyelet with its hole across the band made them turn 90° -
keep the lead path straight). No bridges or overhangs.
History: soft-flex U with 2×1 mm magnets (0.02 N, too weak); magnet lids (bulky - "like a
football"); metal clip-on nose rings (look like jewellery); a PETG open ring (R 4, 0.7 × 1.5 mm
strip): too small and flimsy, its 0.7 mm lead hole didn't print, and springing open from a <1 mm
gap onto the wing "pinches like hell". Lessons: holes under ~1.2 mm don't print (use open grooves
or vertical holes); size the clip to the wing with a small squeeze instead of a big spring travel;
PETG is far too stiff for short springs on skin. The user wants it subtle and sturdy, a band
"2-3x wider than the ring", not wide. Assumed: `BEAD_D` 0.8, pogo 4.0 × 4.0 mm no flange.

## Checks to run after any change

1. Each part is one solid: `len(shape.solids()) == 1` (clips: flat and folded/worn at every size).
2. Overlaps: intersect new bodies with every assembly body; only designed squeezes may overlap
   (pod vs lid/liner/back clip, clip vs the large reference lobe when shown on the mid one).
3. Overhangs: `overhang.py` on the print STLs; only lips and short bridges allowed, no supports.
4. Rebuild `assembly_onepiece.py` and `print_layout.py`; update the README; reopen in Fusion if the
   user is following there.
5. Render to look at it: export STL, `pyvista` off-screen `Plotter`, `screenshot()`, then view the
   PNG (pyvista colours must be 6-digit hex like `#555555`).

## Lessons learned

- **Coplanar faces break booleans** (null shape, or parts that should join come out as 2 solids).
  Overlap joins by 0.05-1.0 mm and nudge faces off shared planes (e.g. the lobe-clip strap starts
  0.1 mm inside the pad face).
- Sharp turns in a polygon band self-intersect; use segment boxes plus round joints instead.
- Rounded reference shapes (lobes, wings) avoid false overlaps from square corners.
- Stand-in anatomy is rough (ear ±5 mm): give leads generous slack and say so.
- Soft flex: 100% infill, 20-25 mm/s, little/no retraction, brim for small parts. PETG: 0.2 mm
  layers, 3 perimeters, 30-40% infill. All give goes in the flex parts; nothing thin or springy in
  PETG.
- Check physical claims with numbers (magnet pull, strap length, lead length) before stating them;
  the nose-clip magnet guess was 2.5× too optimistic until computed.
- When the user reports a fit problem from a print, ask or check which file version they printed.

## v1 glasses mount (`hardware/glasses/`)

TPU temple sleeves with spring leaves (fit 2-6 mm temples), LED channel bending round the hinge,
neck band with ItsyBitsy/battery trays, earlobe arm. Second sleeve design not printed. A Fusion
script (`fusion/BreathSenseGlassesMount/`) builds the v1 parts natively. Superseded by v2.
