# Glasses mount

A parametric model, written in [build123d](https://github.com/gumyr/build123d),
for wearing BreathSense on an ordinary pair of glasses:

- **Temple sleeves** slide over the temple tips like glasses socks.
- **An arch** on each sleeve lowers down over the temple. It holds the LED strip
  against the inside of the temple.
- **The last two LEDs** fold inward onto the lens.
- **A band behind the head** carries the electronics: the ItsyBitsy with an
  Adafruit LiPo backpack stacked on it, a power switch and the battery.
- **One sleeve** has an arm that holds the MAX30101 against the earlobe.

**First draft, not yet printed.** It uses standard adult glasses sizes and
estimated electronics sizes. Measure your parts, change the numbers at the top
of `glasses_mount.py`, and test-fit one sleeve before printing everything.

## Parts

| File | Material | What it is |
|---|---|---|
| `sleeve_right_ear` | TPU | Right temple sleeve with the earlobe sensor arm |
| `sleeve_left` | TPU | Left temple sleeve |
| `band_left` | TPU | Band half with the battery socket |
| `band_right` | TPU | Plain band half. Its groove carries the right LED strip and sensor wires. |
| `band_center` | TPU | Center module with the ItsyBitsy socket (USB faces down, switch faces up) |
| `tray_itsybitsy` | PLA | Holds the ItsyBitsy with the backpack on it, and the slide switch |
| `tray_battery` | PLA | Holds the battery |

`out/step/` holds the parts as modelled. Open them in Fusion 360 with File →
Open, or upload them to a Fusion project. They come in as solid bodies you can
edit. `out/stl/` holds the same parts in print orientation, ready to slice.

## Building it in Fusion 360

`fusion/BreathSenseGlassesMount/` is a Fusion script that builds the same parts
as native Fusion components. Each part is ordinary sketches and extrudes in the
timeline, and the sizes are User Parameters.

1. **Add the script.** In Fusion, open Utilities → Add-Ins → Scripts and
   Add-Ins. Click **+** next to "My Scripts" and choose the
   `BreathSenseGlassesMount` folder.
2. **Run it.** It creates a new design, adds the parameters, and builds all 7
   parts as components named `BS …`.
3. **Resize.** Open Modify → Change Parameters, edit the values, then run the
   script again. It deletes the `BS …` components and rebuilds them from the
   new values in the same design.

Changing a parameter doesn't update the parts on its own; run the script again
to rebuild. Any hand edits to the `BS …` components are lost on a rebuild, so
settle the parameters first and make hand edits last.

The script's geometry has been checked against `glasses_mount.py` by running its
build steps through build123d (last checked after the backpack and switch change). All parts match, apart from the stud heads, which
are made of small steps in the script instead of a cone. The script has not been
run inside Fusion yet. If it fails, it shows the error in a message box.

## Wiring

Power comes from a LiPo through an [Adafruit LiIon/LiPoly Backpack](https://www.adafruit.com/product/2124)
(product 2124). It charges the battery from the ItsyBitsy's USB port at 100 mA,
which suits a ~250 mAh cell. Leave the 500 mA jumper open. Two resistors let the
firmware read the battery voltage on A2.

```
 LiPo 3.7 V ──JST──┐
           ┌───────┴────────────┐
           │  LiPo backpack     ├── switch pads ── slide switch
           │  BAT    G    USB   │   (cut the trace between the pads first;
           └───┬─────┬─────┬────┘    wire the middle pin and one outer pin)
               │     │     │         soldered straight onto the ItsyBitsy's pins
 ItsyBitsy nRF52840
   BAT ──┬──────────── battery, after the switch
         │
        100k
         ├──────────── A2   (battery ÷ 2)
        100k
         │
   G  ───┘

   Vhi ─────────────── LED strips +  (both)
   G   ─────────────── LED strips −
   D9  ─────────────── left strip DIN
   D7  ─────────────── right strip DIN

   3V, G, SDA, SCL ─── MAX30101  (see firmware/PULSE_SENSOR.md)
```

- **Divider:** two 100k resistors in series from **BAT** to **G**, with their
  midpoint to **A2**. A full cell (4.2 V) reads 2.1 V, within the 3.3 V input.
  Battery voltage = `AnalogIn(board.A2).value / 65535 * 3.3 * 2`. Roughly
  4.2 V is full and 3.4 V is nearly empty. Tap BAT on the ItsyBitsy, after the
  switch, so the divider draws nothing when the device is off. Don't use A1:
  in `auto` mode the firmware reads A1 as the analog pulse sensor when no
  MAX3010x answers.
- **Firmware:** `firmware/battery.py` reads it every 2 s and sends
  `P,{mV},{percent},{usb}` to the app every 10 s and on connect. Percent is
  `-1` when no battery is seen (below 2.8 V: switch off or not fitted). The
  app shows the level next to the settings icon, with a charging icon while
  `usb` is 1. That flag comes from `supervisor.runtime.usb_connected`, so it's
  only set when the headset is plugged into a computer, not a wall charger.
  Voltage reads high while charging. If the divider isn't fitted, set
  `BATTERY_PIN = None` in `config.py`; a floating pin reads noise.
- **LED strips on Vhi.** Vhi carries the higher of USB and battery, so the
  strips stay lit on battery. The USB pin is dead without a cable.
- **Switch:** a panel-mount slide switch across the backpack's switch pads.
  Snip the two screw ears off its metal plate with flush cutters. That leaves
  a plate 10.5 × 5.5 mm, 8 mm deep including the pins, which fits inside the
  tray's end wall, with the lever through the slot. It disconnects the battery from BAT. With USB plugged
  in, the ItsyBitsy runs from USB whatever the switch is set to. Adafruit don't
  say whether the battery still charges with the switch off, so test it: switch
  off, plug in USB, and watch the backpack's charge LED.
- **Backpack underneath:** mount the backpack on the underside of the
  ItsyBitsy, at the USB end, on the header spacers. That keeps the reset and
  user buttons usable. Mounted on top, it covers them; then short **RST** to
  **G** twice quickly to get into the bootloader.
- **Header pins:** trim them flush on both boards. They stick out about 2 mm
  below the backpack, and the tray allows for a 9.5 mm stack.
- **Battery leads:** the 502030 cell has three wires. Red is **+** and black
  is **−**. White is usually a temperature sensor, which the backpack doesn't
  use, so cover its end with heat-shrink and leave it unconnected. Check this
  with the seller if you can. Either crimp or solder a 2-pin JST-PH plug onto
  red and black, which keeps the battery removable, or solder
  them straight to the backpack. Get the polarity right: red to **+** as marked
  on the backpack. Cut and strip one lead at a time so the bare ends can't
  touch. Put the cell in its tray with the leads at the end nearest the center
  module. The tray leaves `BATTERY_LEAD` (4 mm) there for them to bend. They run
  out under the tray's end wall, along the band groove, to the backpack.

## Regenerating the STEP and STL files

```
pip install build123d
python glasses_mount.py
```

Set `EAR_SIDE = "left"` to put the sensor arm on the left sleeve.

## Fitting

1. **Sock.** Slide the sock end onto the temple tip.
2. **Arch.** Lower the arch down over the straight part of the temple. The top
   bar rests on the temple, the outer leg grips its outer face, and the inner
   leg (with the LED channel) hangs down the inside.
3. **LED strip.** Slide it into the channel on the inner leg, with the LEDs
   facing the head through the window. Eight LEDs lie along the temple and two
   sit on the flap.
4. **Flap.** Fold it 90° inward at the thin hinge so its two LEDs rest against
   the inside of the lens, facing the eye.
5. **Wiring.** The strip's wires run through the tunnel inside the inner wall,
   round the bend and out through the end of the sock.
6. **Band.** Each band half's outer end presses over the stud on the outside of
   its sock. The row of holes sets the size. The inner ends press over the
   center module's studs.
   - Wires run in the groove along the band's outer face, under the sockets.
     The trays close over the groove.
7. **Trays.** Put the ItsyBitsy (with its backpack) in its tray with the USB at
   the port cut-out, and the switch at the other end with its actuator through
   the slot. Snap the trays in with their open side against the band. Line up
   the port cut-out and switch slot with the gaps in the socket wall. The USB
   port then faces down and the switch faces up, both clear of the band.
8. **Ear arm.** Bend it so the sensor faces the inner side of the earlobe. The
   board's sensor side is open to the skin. Glue an insulated magnet to the
   board's back and use a second magnet on the outside of the lobe.

## Printing

- **Sleeves** print flat on their inner face, with the stud and the outer leg
  facing up. These parts span gaps with nothing underneath:
  - the roof of the LED slot, about 10 mm
  - the roofs of the wire tunnel and the sock, 3–4 mm
  - the outer leg, which overhangs about 3 mm

  They should print in TPU without supports. Expect some sag on the LED slot
  roof.
- **Band parts** print flat with the sockets facing up.
- **Trays** print floor-down in PLA.
- **Bed size.** The longest part is the sleeve at 141 mm.
- **Center module** is about 52 mm tall, because the switch sits above the
  ItsyBitsy.

## What has been checked, and what hasn't

Checked in the model:
- Each part is one solid.
- The arch fits over a temple of the set size, with only the intended 0.1 mm
  grip on each face.
- Insert checks, each a test body that must not touch the part:
  - the strip slides through the temple and flap channels
  - the LEDs' light path through the window is clear
  - the sensor board and its components fit the pod
  - the sensor side is open to the skin, and the back is open for the magnet
  - the wire tunnel joins the LED slot and stays open out through the sock end

  The lips do overlap the strip's edges, which is what holds it in.
- Each part's print orientation has a flat base. Overhangs are limited to the
  spans listed above.
- Each tray clears its component by 0.3 mm per side.
- The switch body fits its bay at the end of the ItsyBitsy tray. The actuator
  slot runs clear through the tray wall and the socket wall.
- Band length is 226–274 mm from sleeve stud to sleeve stud, across the
  adjustment holes.

Not checked:
- Nothing has been printed yet, so TPU stiffness, grip and hinge behaviour are
  untested.
- Fit on real glasses or a real head.
- Part sizes are measured, but no tray has been test-fitted. Print the
  ItsyBitsy tray first and check the board and switch drop in.
- USB plug clearance with real plugs.

Measure these and adjust:

| Setting | What it is |
|---|---|
| `T_W`, `T_H` | Temple thickness and height |
| `TEMPLE_STRAIGHT`, `TIP_ANGLE` | Length to the ear bend, and the bend angle |
| `STRIP_W` | LED strip width; check the LEDs line up with the window |
| `ARCH_FRONT`, `HINGE_LEN` | Where the flap folds relative to the glasses hinge |
| `ITSYBITSY`, `BATTERY` | Board stack (ItsyBitsy + backpack) and battery sizes |
| `BATTERY_LEAD` | Room in the battery tray for the leads to bend |
| `SWITCH`, `SWITCH_SLOT` | Slide switch body and the actuator slot it needs |
| `BOARD_L`, `BOARD_H`, `SENSOR_OFFSET` | Pimoroni MAX30101 breakout |
| `BAND_HALF_LEN` | Band length; it should be snug, not tight |
