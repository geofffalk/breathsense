# BreathSense v2 hardware (proposal)

A second hardware configuration for the glasses, worked out from the first
prototype (ItsyBitsy nRF52840, LiPo backpack, neck band). It reuses parts
already on hand: a Seeed XIAO nRF52840 Plus, the 10-LED NeoPixel strips, the
MAX30101 and the 250 mAh cell. New parts cost about $10. Nothing here is built
yet.

## What the wearer sees

The display sits in peripheral vision, which sees motion and brightness
changes well but detail and colour poorly. So every cue is motion. Colour is
only a slow background hint.

Both sides show the same thing. The phone app or the button picks the mode:
breath, heart or guided.

| Signal | Shown as |
|---|---|
| Breath phase | A wave travels forward along the front LEDs on the in-breath and back on the out-breath |
| Breath depth | How far the wave travels and how long the lit segment is |
| Breath length | How fast the wave travels |
| Breath regularity | Steady breathing gives a smooth wave; irregular breathing gives a shimmer of small random brightness changes |
| Heartbeat | A short swell runs from the front back into the temple glow |
| HRV | How much the spacing and strength of the swells vary |

The firmware cross-fades the wave crest between neighbouring LEDs, so behind
the diffuser it reads as smooth motion rather than steps.

### Where the light can be seen

These angles are estimated from typical frame geometry. The LED sweep test
(below) measures them on real glasses.

- **Hinge and front flap (about 75–95° from straight ahead):** in direct view.
  Position and direction can be told apart, so the travelling cues go here.
  With 6.8 mm spacing, 5 LEDs per side fall in this zone: 3 on the corner's
  flap, 1 at the hinge and the front LED on the rail.
- **Temple, 15–30 mm behind the hinge (about 95–110°):** at the edge of the
  field. Only bright changes are noticed.
- **Rest of the temple:** out of direct view. Its light reaches the eye only as
  glow off the back of the lens, the frame and the skin. It works as a
  brightness channel (swell, pulse), but not as position.

## Parts

| Part | Notes | Cost |
|---|---|---|
| Seeed XIAO nRF52840 **Plus** (on hand) | Same chip as the ItsyBitsy, but 21×17.5 mm. Built-in LiPo charger (no backpack), extra pads. No IMU or microphone | $0 |
| Adafruit Ultra Skinny NeoPixel 1515 strip, 4 mm, 150 LEDs/m (on hand, as 10-LED pieces) | SK6805-EC15 LEDs. One 10-LED piece per side: 3 on the corner's flap against the frame front, 1 at the hinge, 6 along the temple | $0 |
| MAX30101 earlobe sensor, 502030 250 mAh LiPo (on hand) | | $0 |
| Fast 10k glass-bead NTC thermistor (1 mm or smaller) | Breath sensor, just inside the right nostril on the nose clip | ~$2 |
| 2-pin 4 mm magnetic pogo connector, four 2×1 mm magnets (on hand) | Nose clip's plug at the board pod; the clip's magnets | $0 |
| P-MOSFET (e.g. AO3401) and 100k gate pull-up | Cuts all LED power when the display is off or the battery is low | ~$0.50 |
| 6×6 mm or smaller tactile button | Wake, sleep and mode | ~$0.50 |
| Natural (translucent) PETG (on hand) | The one-piece temple parts: the LEDs shine through the wall (see Mount) | $0 |
| PETG, plus the soft flex filament (on hand) | Rigid rails and clips, with soft-flex liners and corners (see Mount) | $0 |
| **Total** | | **about $8, or $23 with natural PETG** |

About $40 of the budget is left. If 5 visible LEDs per side look too coarse,
the best use is a custom flex PCB with about 12–14 tiny LEDs for the front
section only.

Strip sources:
- [Adafruit 4368](https://adafruit.com/product/4368)
- [SK6805-EC15 (LCSC)](https://www.lcsc.com/product-detail/C2890035.html): 1 kHz PWM, 3.7–5.5 V

## Layout

- **Behind the right ear:** a pod with the XIAO Plus, the button and a reset
  pinhole. The MAX30101 earlobe arm reaches from it to the back of the
  earlobe.
- **Behind the left ear:** a pod with the battery.
- **Behind the head:** a thin cord with four wires joins the pods: battery +,
  ground, the switched LED supply and the left strip's data. There is no neck
  band.
- **LEDs:** a 10-LED piece on each side: 6 in the rail's channel, 4 in the
  corner piece (1 at the hinge, 3 on the flap). Nothing touches the lens rim, so it fits any frames. Each strip
  has its own data pin, as in v1.
- **Thermistor:** on a soft clip on the right nostril's wing, just inside the
  nostril. Its two wires run loose along the cheek and under the ear to a
  magnetic pogo socket on the board pod (see Nose clip).

## Power and switching

There is no power switch.

- **LED power** comes from the battery through the P-MOSFET. The MOSFET is off
  whenever the LEDs are dark, because each NeoPixel draws about 1 mA even when
  showing black.
- **LED low-voltage cut-off at 3.6 V.** The SK6805 is rated for 3.7–5.5 V.
  Below that, blue dims and the LEDs can misread data. When the battery reads
  under 3.6 V, the firmware:
  1. switches the LEDs off;
  2. sends a low-battery notice to the app;
  3. goes into deep sleep until USB is plugged in.

  This gives up roughly the last 20% of the cell. A 5 V boost converter for
  the LEDs would recover it, if needed later.
- **Auto sleep.** With no breath and no pulse for about 2 minutes (glasses off),
  the board switches off the LEDs and the MAX30101 and goes into nRF52 System
  OFF, drawing a few µA.
- **Wake.** Press the button. Plugging in USB also wakes it. After waking it
  shows a short start-up sweep. If it sees no breath or pulse within 30 s, it
  goes back to sleep, so a knock in a bag doesn't leave it running.
- **Button while awake.** A short press changes mode. A long press puts it to
  sleep.
- **Watchdog timer.** The nRF52 hardware watchdog resets the board if the
  firmware hangs. After the reset it goes back to sleep, so a hang can't drain
  the battery.
- **Reset pinhole** over the XIAO's reset button, for when everything else
  fails.
- **Charging:** plug USB-C into the right pod. The battery charges through
  the cord.

### What the LEDs show for each state

Every power change shows on the LEDs, so the wearer always knows the state.
These use the same motion language as the main display.

| Event | LEDs |
|---|---|
| Wake (button, USB) | One soft white sweep from the front to the back, about 0.8 s |
| Auto sleep coming | Three slow, dim swells over about 5 s. Pressing the button or breathing on the sensor cancels it |
| Going to sleep (auto or long press) | A sweep from the back to the front that fades out, about 1 s; then dark |
| Mode change | The new mode's pattern plays once (1, 2 or 3 short pulses), then the display starts |
| BLE connected / disconnected | The existing connect animation / one dim blip |
| Low battery warning (about 3.75 V) | One amber blip every 30 s, on top of the display |
| Low battery cut-off (3.6 V) | Three amber flashes, then the sleep sweep in amber |
| Charging, plugged in while asleep | A slow amber swell every few seconds; steady dim green when full. Runs on USB power, so it costs the battery nothing |
| Recovered from a hang (watchdog reset) | One short red blip, then back to sleep |

The low-battery signals use amber and red because blue fails first as the
voltage drops. Red and green still work at 3.6 V.

### Estimates

| Load | Awake | Asleep |
|---|---|---|
| XIAO with BLE | ~5 mA | ~3 µA |
| MAX30101 | ~3 mA | ~1 µA |
| 20 NeoPixels at indoor brightness, including their idle draw | ~30–45 mA | 0 (MOSFET off) |

Runtime is about 3–3.5 h on 250 mAh, down to the 3.6 V cut-off. Standby is
months.

## Mount

### What to print (current)

The STLs in `out/stl/` are already oriented: don't rotate them. Each name ends in its filament: `_petg` or `_flex` (soft flex). `out/print_layout.step` (from `print_layout.py`) has them all
in one file for Fusion, as they sit on the bed, one body per copy to print.

| File (`out/stl/`) | Material | Qty | What it is |
|---|---|---|---|
| `onepiece_right_petg`, `onepiece_left_petg` | Translucent PETG | 1 each | LED band and rail. 5 mm brim: they stand on a narrow edge |
| `hang_pod_board_petg` | PETG | 1 | Right pod: XIAO |
| `hang_pod_battery_petg` | PETG | 1 | Left pod: battery |
| `onepiece_band_flex` | Soft flex | 2 | Temple band (closed loop) behind the last LED, one per side (fits either side) |
| `hang_liner_flex` | Soft flex | 2 | Lines each pod's pocket |
| `hang_back_clip_flex` | Soft flex | 2 | Closed band round each pod's pocket and the paddle (fits either side) |
| `hang_lid_board_flex`, `hang_lid_battery_flex` | Soft flex | 1 each | Press-in pod lids |
| `lobe_clip_flex` | Soft flex | 1 | Magnetic earlobe clip (see Earlobe clip) |
| `nose_clip_flex` | Soft flex | 1 | Thermistor clip for the nostril (see Nose clip) |

- **PETG:** 0.2 mm layers, 3 perimeters, 30–40% infill, no supports.
- **Soft flex:** 0.2 mm layers, 20–25 mm/s, little or no retraction, 100%
  infill, no supports. A brim helps the small clips stay down.
- **Handedness:** the parts are modelled for the left temple (y outward, in a
  right-handed frame), so the right-side files are mirrored. Files exported
  before 28 Oct had right and left swapped.
- **Liner:** prints open edge down, so its walls stand up and only the 3.6 mm
  bottom bridges.
- **Test fits first:** a pod with a liner and band on the glasses tip;
  `onepiece_right_petg` with its band; the earlobe clip on your ear; the nose clip on your nostril.

### One-piece temple part (current design)

`onepiece.py` replaces the rail, corner, liners, caps and diffuser below with
**one PETG part per side**. The pods still clip onto the tips (see Pods). It's
shaped to one measured pair of glasses, not universal.

![One-piece part, inside view](renders/onepiece_inside_right.png)

- **The strip stays in one piece.** It runs along the temple, then round the
  hinge corner in one rigid 18 mm-radius curve onto the frame front's back
  face. The glasses can't fold while the part is fitted, so the curve doesn't
  have to bend. 5 LEDs sit on the curve and the frame run, and 1 more at the
  front of the rail, so 6 are in direct view.
- **Nothing over the lens.** The strip can't bend sideways within its own
  plane, so it stays at one height all the way along. That height is the top
  rim: on the frame front it sits above the lens, and it passes over the
  hinge knuckle.
- **No threading.** The strip drops into a slot that's open along its top
  edge. The slot is 2.2 mm wide for the 1.2 mm strip (PCB plus LEDs), because
  printed slots come out 0.2–0.4 mm narrow, and nothing narrows the opening.
  Round the curve the strip is held by its own stiffness: it can't bend
  within its own width, so it can't climb out of a curved slot. The band
  crosses the slot behind the last LED, over the strip's end. If the strip
  lifts anywhere else, a dab of silicone in the slot (on the part, not the
  glasses) holds it.
- **Windows.** Print the part in translucent PETG. The slot's head-side wall
  is 0.8 mm thick, but in front of each LED it's thinned from the slot side to
  a 0.45 mm skin (one line from a 0.4 mm nozzle) over a 3.4 × 3 mm patch.
  Each LED shines through its skin as a soft spot, and the outside face stays
  smooth. The full-thickness wall above and below each patch holds the strip
  in. Some light also spreads along the wall, which blurs the LEDs together;
  if that's too much, darken the outside between the windows with a marker.
  Check that the slicer prints the skin as one line and doesn't leave it out:
  set the line width to 0.45 mm, or detect thin walls.
- **Length.** The rail ends 60 mm behind the hinge, past the band behind the
  last LED. From there the strip's wires run along the temple's inner face to
  the pod.
- **Grip.** A rigid hook over the temple's top edge carries the part. One
  soft-flex band (`onepiece_band`), 6 mm wide, holds it to the temple just
  behind the last LED, 45–51 mm behind the hinge, so it covers no LEDs. It's
  a closed loop right round both: over the top, down the head-side face,
  under both bottom edges, up the temple's outer face and the hook's lip.
  However soft the flex, a closed loop can't spring off the way an open clip
  can. It's about 7% smaller than what it goes round, so it stretches on
  snugly. It sits in 0.5 mm grooves in the part's top, the hook's lip and the
  plate's bottom edge, so it can't slide along. There's no groove in the
  head-side face, because the LED wall there is only 0.8 mm; the band stands
  1.2 mm proud on that side. In front of the band, the hook and the part's
  stiffness hold it.
- **Fitting.** The bands can't go on from the front (the hinge and frame are
  in the way), so they go on over the tip:
  1. Take the pod off the tip.
  2. Slide the band onto the temple over the tip. It's loose on the bare
     temple; the tip paddle is smaller than it is. Then the pod's band (see
     Pods).
  3. Hook the part over the temple's top edge and swing its bottom in.
  4. Roll the band forward onto the part's back end and into its grooves,
     just behind the last LED.
  5. Put the pod back on and roll its band back into its groove.
  To remove, reverse it. Nothing is stuck to the glasses.
- **Nothing springy in the PETG.** All the give is in the soft-flex band, so
  the PETG part has nothing thin to snap.
- **Printing.** PETG, top edge down on the bed, no supports. The band prints
  in soft flex, lying flat (standing on one end), no supports.
- **No separate test piece.** The part is short enough to print whole as the
  first test, about 2 g. Check that the curve sits against the frame front,
  clears the hinge and stays above the lens, that the strip drops in, and
  that the band holds.

**Measurements to check.** These come from photos or are guesses:
- Where the lens starts below the frame front's top, near the corner
  (`LENS_TOP_Z`, guessed at 4.5 mm below the temple's top edge).
- The frame front's top height beside the hinge (`FRAME_TOP_Z`).
- The hinge knuckle's size and height (`KNUCKLE_Z`, `GUSSET_L`).
- The temple's outline. It assumes a straight top edge and a straight taper
  from 8.1 to 4.0 mm tall, and 4.0 to 3.2 mm thick.

`CLEAR` sets the fit against the temple, and `CURVE_R` the corner radius. A
bigger radius carries more LEDs round the corner, but reaches further along
the frame front.

### Pods hanging off the tips (current)

`hang_pods.py` replaces the earlier pods. The temple tip ends in a paddle: 4.0
mm thick, growing from 6.3 mm tall 20 mm back to 8.5 mm at the end (measured).
Each pod fits over the paddle's last 22 mm, and its body carries on past the
end, down onto the bone behind the earlobe. It doesn't rise above the ear.

| File (`out/stl/`) | Material | What it is |
|---|---|---|
| `hang_pod_board` | PETG | Right pod: XIAO (USB-C out of the far end, down and back when worn), button in the back wall, earlobe lead out of the ear-side wall |
| `hang_pod_battery` | PETG | Left pod: 502030 cell; cord out of the far end |
| `hang_liner` | Soft flex | Lines each pod's pocket. Print 2 |
| `hang_back_clip` | Soft flex | Closed band round each pod's pocket and the paddle, in a groove. Print 2 |
| `hang_lid_board`, `hang_lid_battery` | Soft flex | Press-in lids |
| `lobe_clip` | Soft flex | Magnetic earlobe clip for any adult lobe (see below), on a loose 4-wire lead |

- **Pocket:** a rigid PETG pocket shaped to the paddle, lined with soft flex.
  It wraps both faces and the edge nearest the ear.
- **Locked along the tip:** the paddle's 8.5 mm end can't pass back through
  the pocket's narrower neck, and its end stops against the body. So the pod
  can't slide along the tip either way. It may creep a few mm, squeezing the
  liner, before the rigid stop.
- **Fitting:** the pod goes on from the paddle's back edge (the edge away from
  the ear). Gravity pulls the paddle into the pocket. A soft-flex band, a
  closed loop right round the pocket and the paddle, holds it there. The band
  sits in a groove round the pocket (0.7 mm deep on the faces and the
  ear-side edge, 0.3 mm on the walls' top edges), so it stands only 0.5 mm
  proud on the side against your head. It's 8 mm wide, 11–19 mm back from the
  paddle's end, where the edge is nearly straight.
  1. Slide the band onto the temple over its bare tip (it's loose there),
     after the one-piece part's band.
  2. Put the pod on the paddle.
  3. Roll the band back along the paddle onto the pocket and into its
     groove, 3 mm in from the pocket's open end.
  To remove: roll the band forward off the pocket onto the temple, lift the
  pod away.
- **Wires:** the rail's wires (up to 4 of about 1 mm) run along the paddle's
  back edge in a 2.2 mm channel under the band (1.6 mm where the band crosses), into the body through its
  front wall. The cord between the pods leaves the far end through a 5 × 3 mm
  hole.
- **Assumption to check:** the paddle grows on its lower edge (nearest the ear
  when worn) and its top edge is straight. If it's the other way round, the
  pocket needs flipping.
- **Weight:** the pods sit behind the ear pivot, so they take a little weight
  off your nose rather than lifting the glasses.
- **Printing:** pods in PETG, head-side face down, no supports (the pocket's
  outer wall bridges over the paddle's space). The liner prints open edge
  down, and the bands lying flat. The band's groove on the head-side face
  makes an 8 mm bridge 0.7 mm up.

### Earlobe clip (current)

`lobe_clip.py` makes one soft-flex part sized for adult earlobes 13–27 mm tall
(intertragic notch to the bottom; the mean is about 19–20 mm) and 2.5–8 mm
thick, free or attached. The magnets set where the sensor sits, so the clip's
shape doesn't have to match the lobe.

![Clip folded onto a lobe](renders/lobe_clip_worn.png)

- **Back pad:** 21.6 × 21.6 × 5.8 mm, behind the lobe, sensor window facing it.
  Sized for the Pimoroni MAX30101 breakout: 19 × 19 mm, narrowing to 15 mm
  over the bottom 5 mm where the pin holes are, every part on the sensor face,
  chip centred at the top edge.
  - **Board:** goes in from the back, past soft lips along its side edges,
    into a pocket 0.1 mm over its size. At the front it's held on all four
    edges: thin rims along the sides, tabs over the two top corners (round the
    mounting holes, clear of the chip) and a cover over the pin tab, with a
    0.5 mm recess behind the pins for solder that wicks through.
  - **Chip proud:** the chip's face stands 0.5 mm proud of the pad's skin face,
    so it presses into the lobe rather than sitting back behind a rim.
  - **Magnets:** three 9.5 × 0.8 mm discs behind the chip. The chip is too
    near the top edge for them to centre on it, so they sit 3.35 mm lower,
    still covering the chip. The pinch presses the chip itself onto the skin.
  - **Flap:** folds over the back on a living hinge and presses in. It holds
    the magnets against the board.
  - **Wires:** solder them to the pins from the back, run them along behind the
    tab and out of the rear wall beside it (4.4 × 3.9 mm slot; the flap is
    recessed 0.8 mm over the tab to make room). Rear is the side away from the
    hinge, toward the pod.
- **Keeper strap:** flat and floppy, 32 mm from the pad's bottom edge to the
  front puck. It goes round whatever free edge the lobe has: under a free
  lobe, or round the back edge of an attached one. It replaces the pre-curled
  finger, which fixed the chip's height above the lobe's bottom and needed a
  free lobe. The strap only keeps the clip on.
  - **Length:** long enough for the longest, thickest lobe with the chip high
    on it. On smaller lobes the spare hangs as a loop under the lobe: about
    13 mm on an average lobe, 19 mm on the smallest.
- **Front puck:** 14 mm across, to spread the pinch, with three discs that
  snap in past a lip.
  - **Lid:** a lid on a living hinge at the puck's forward side folds over
    its outer face. A plug on the lid presses into the lip's opening, down
    onto the magnets, so they can't drop out while the clip is off. (When
    it's worn, the pull toward the pad's magnets holds them in anyway.) A dab
    of glue on the plug makes it permanent. With only two discs in the puck,
    the plug no longer reaches them, so add a 0.8 mm shim or glue.
  - **Polarity:** put the stacks in so they attract when the strap is folded.
- **Pinch:** the magnets are the lobe's thickness plus 3.25 mm apart (board,
  chip and skins). That gives about 1.3 N on a 2.5 mm lobe and 0.3 N on an
  8 mm one. The clip weighs about 6 g, so even the weakest pinch holds it. On
  very thin lobes, use two discs in the puck if it pinches.
- **Wearing it:** put the chip on the upper, fleshy part of the lobe, at
  least 6 mm below the notch. Fold the strap round and let the puck snap on.
- **Lead:** 4 loose silicone wires (power, ground, SDA, SCL), 70 mm long. The
  farthest a lobe sits from the pod's exit is 42 mm, checked over ±5 mm of
  ear position and every lobe size, plus 25 mm of slack. Tie a knot inside
  the pod as strain relief; it leaves through a 4 mm hole in the ear-side
  wall.
- **Check:** `CHIP_OFFSET` puts the chip's centre 2.3 mm below the board's
  top edge, from a photo; and the side rims (0.8 mm) must clear the parts
  nearest the side edges.
- **Printing:** flat, skin side down, no supports: pad, strap, puck, open
  flap and open puck lid all start on the bed. The only overhangs are the 1 mm lips and the puck's lip.

### Nose clip (current)

`nose_clip.py` makes one small soft-flex part (8 × 11 × 9 mm worn) that clips onto
the wing of the right nostril and holds the breath thermistor just inside it.
It's held by the nose, not the glasses, so it stays put when the glasses move.

- **The U:** wraps the wing's lower rim, the inner leg inside the nostril and
  the outer pad on the skin outside. It prints nearly closed (1.6 mm) and
  springs shut onto any wing about 2–5 mm thick.
- **Magnets:** two 2×1 mm discs stacked in each leg, pushed in from the faces
  away from the skin; put them in so the legs attract. They only help it
  settle: through a 3 mm wing they pull about 0.02 N. The spring does the
  holding.
- **Magnet lids:** each hole is closed by a lid on a living hinge at the
  clip's back edge, with a peg that presses into the hole on top of the
  stack. They print lying flat, out to either side, pegs up. When worn, the
  magnets pull toward each other, deeper into their holes, so the lids only
  have to stop them dropping out while the clip is off. A dab of glue on the
  peg makes it permanent (it's all on the printed part).
- **Bead cage:** an open square tube on the inner leg's tip, along the nostril
  (the way the air goes). It holds the bead about 4 mm in and 2 mm off the
  skin, in the airflow; touching skin, it would read skin temperature.
- **Wiring:** the bead's leads drop through the cage, down the groove on the
  inner leg's free face to the keel under the U, outside the nostril. Solder
  them to a twisted pair of 30 AWG silicone wires there (heat-shrink each
  joint), and press the pair into the keel's channel; it leaves from the back,
  toward the ear.
- **Order:** magnets in, bead leads in the groove, then fold both lids up and
  press the pegs home. The inner leg's lid closes over the groove and holds
  the leads in.
- **Wire:** 220 mm, loose: down behind the earlobe, under its clip, along the
  cheek. The path on the stand-in head is 178 mm, plus 40 mm slack. It ends in
  the plug half of a 2-pin 4 mm magnetic pogo connector; the socket half
  presses into the board pod's ear-side wall, 7 mm behind the earlobe lead's
  hole, and its tails solder to A0 and ground (the
  firmware's divider: 10k from 3V to A0, thermistor from A0 to ground). Set
  `BETA` in `firmware/config.py` to your bead's B value (3435 now).
- **Tugs:** the pogo connector's magnets probably hold harder than the clip
  grips, so a snag could pull the clip off the nose before the plug lets go.
  Leave a slack loop under the ear; if tugs still reach the nose, add a tie-off
  where the wire passes the earlobe clip.
- **Check:** the bead (`BEAD_D`, 0.8 mm assumed) and the pogo socket
  (`hang_pods.POGO`, 4.0 × 4.0 mm assumed, no flange). The socket's tails sit
  in the knot space under the XIAO; bend them flat.
- **Printing:** back face down, no supports. The only overhangs are short
  bridges over the magnet holes, the groove and the cage. The lids lie on the
  bed; peel them up gently, the hinges are 0.5 mm.

### Earlier v2 mount (superseded)


`mount_v2.py` models the mount; `render_v2.py` draws it on the stand-in head
(`renders/`).

The first print, in soft flex filament, was too flimsy everywhere: the clips
didn't grip, and the neck, the hinge corner and the straight sections all
flopped. The v2 mount moves the structure into PETG and uses the soft flex
only where it helps (grip and the corner).

![Inside view, right side](renders/v2_inside_right.png)

### Parts

| File (`out/stl/`) | Material | What it is |
|---|---|---|
| `test_clip_S`, `_M`, `_L` | PETG | One clip on a short length of rail. Print these first and try them on your glasses |
| `rail_right_S/M/L`, `rail_left_S/M/L` | PETG | The full rail for each temple, in three sizes |
| `liner` | Soft flex | Grip liner. Print 4 (two per rail) |
| `corner_right`, `corner_left` | Soft flex | Carry the front four LEDs round the hinge and along the frame front |
| `diffuser` | Natural (translucent) PETG | Snap-on cover over each rail's LED channel. Print 2; it fits either side |
| `corner_cap_hinge`, `corner_cap_flap` | Natural (translucent) PETG | Covers over the corner's LEDs. Print 2 of each |
| `pod_board_S/M/L` | PETG | Right pod: XIAO, button, MAX30101 arm root. Sized by the temple tip |
| `pod_battery_S/M/L` | PETG | Left pod: battery and the cord junction |
| `lid_board`, `lid_battery` | Soft flex | Press-in lids on the pods' outer faces |
| `pod_liner` | Soft flex | Grip liner under each pod's tip bar. Print 2 |
| `max_arm` | Soft flex | MAX30101 arm and cradle |

`out/step/` holds the same parts as fitted, in worn coordinates.

For Fusion 360, open these with File → Open. Each part comes in as its own
named body:
- `out/all_parts.step`: every part, laid out side by side in print
  orientation.
- `out/assembly_right_M.step`: the right side in place, in size M. It is
  modelled on a straight temple, so the pod sits in line with the temple
  rather than bent down behind the ear.

### Rail

- **Shape:** a PETG bar on the temple's inner face, from 6 mm behind the hinge
  to just before the ear bend. Its open LED channel is on the head side, with
  snap lips, as in v1. The wires carry on along the same channel to the rail's
  back end, then cross the ear bend loose to the pods.
- **Clips:** two clips, each 32 mm long, push down over the temple from above.
  Each has a top bar, an outer leg and two thin PETG leaves angled toward the
  temple. Pushing down, the leaves' sloped bottom edges ride over the temple's
  top edge and swing aside.
- **Grip:** the leaves press the temple against a soft-flex liner. The liner
  slides into a dovetail groove along the rail's temple face from the back end:
  push the front clip's liner all the way forward first, then fit the rear one.
- **Any temple height:** the leaves span the full 9 mm clip height, so they
  grip temples of any height from about 3 mm up.

### Sizes

PETG is far stiffer than the soft flex, so one rail can't safely grip 2–6 mm
temples. Each size covers about 1.3 mm of temple thickness:

| Size | Temple thickness | Grip per leaf | Peak leaf stress |
|---|---|---|---|
| S | 2.0–3.3 mm | 0.4–2.2 N | 5–25 MPa |
| M | 3.3–4.6 mm | 0.4–2.2 N | 5–25 MPa |
| L | 4.6–6.0 mm | 0.4–2.3 N | 5–27 MPa |

The reference glasses (4.0 mm at the front clip, about 3.5 mm at the rear)
take **M**.

The grip figures are 10–70 times the v1 sleeve's. The stresses stay under about
30 MPa (PETG yields at about 50). These come from simple beam formulas, not a
test. PETG also creeps a little under constant load, so the grip may ease off
over weeks. If it does, step down a size.

If a temple tapers past a size boundary between the clips, use the size that
fits the front clip.

### Corner

The corner is soft flex, but printed already bent at 100°, 10° past the
frame's 90°. The old corner was printed straight and kept trying to
straighten, which is why the flap flopped. This one holds its flap against the
frame front at rest, and bends further when the glasses fold.

It slides down onto a tongue on the rail's front end and grips it by a slight
interference fit. It carries the front four LEDs:
- **Hinge:** the 7th LED, on the corner's straight part just before the
  bend.
- **Flap:** the 8th, 9th and 10th LEDs, 1.5, 8.3 and 15.1 mm along it. Two
  snap lips between them hold the strip in.

The flap is 20 mm long, so on most frames it reaches in behind the outer edge
of the lens.

### Diffuser

A thin PETG plate stands 1.5 mm off the channel mouth, so the LEDs blur into a
line, with hooks over the rail's top and bottom edges. Fit it after the strip
is in: hook the bottom edge on, then press the top hook over. Print it in
natural PETG. If the LEDs still show as dots, a thicker plate or a bigger gap
(`DIFF_T`, `DIFF_GAP`) blurs them more.

**Corner caps.** The corner LEDs are the ones in direct view, the ones that
carry the travelling wave, so they get covers too:
- **Hinge cap:** a short cap on the corner's straight part, over the hinge
  LED.
- **Flap cap:** a long cap along the flap, over its three LEDs.

The bend between them is left open, so the corner can still bend when the
glasses fold. Both caps hook over the corner's top and bottom edges like the
rail diffuser. Both fit either side: turn them over for the left.
On soft flex, the hooks hold less firmly than on the rigid rail; if a cap
won't stay, a dot of flexible glue fixes it.

### Pods

![Rear view](renders/v2_rear_three_quarter.png)

- **On the tip:** each pod clips onto the temple tip behind the ear. It slides
  on from the tip's end and sits flat on the bone behind the ear. Only a thin
  bar runs under the tip, on the ear side.
- **Grip:** two PETG leaves inside press the tip down onto that bar, which
  carries a soft-flex liner like the rail's. The liner slides in from the
  tip-end face. The leaves lie in the pod's own plane, so they add no
  thickness. They lean toward the tip's
  end, so sliding the pod on bends them aside, and pulling it off doesn't
  catch.
- **Sizes:** sized by the tip. The reference tip (3.5 × 4.5 mm) takes **M**.

  | Size | Tip thickness | Tip height |
  |---|---|---|
  | S | 2.5–3.3 mm | 3.0–4.3 mm |
  | M | 3.3–4.2 mm | 4.3–5.6 mm |
  | L | 4.2–5.2 mm | 5.6–7.0 mm |

  The pod leaves are shallower (4 mm) than the rail's, so each presses with
  only about 0.15–0.85 N. That is over 10 times a pod's weight, but the tip
  slopes down toward its open end, there's no end stop, and the cord tugs on
  the pods when you turn your head. Pod grip is the weakest in the build:
  test it first.
- **Will it fit your tip?** The pod's slot is a straight, rigid 36 mm run,
  nearly the tip's whole length. Hold a straightedge along your tips: a tip
  that curves along its length, or ends in a ball, won't slide in. A shorter
  pod would fit a curved tip; tell me if you need one.
- **Board pod (right):**
  - **XIAO:** sits under a soft-flex lid on the outer face, with its USB-C
    pointing out of the pod's far end (up and back when worn). Check where
    your board's reset button is: the lid's 1.2 mm reset pinhole assumes it is
    5 mm to one side of the USB-C.
  - **Button:** a 6×6 mm tactile button in the front column. Its plunger
    comes out beside the USB-C.
  - **Wires:** the rail's wires enter at the front. The cord leaves from the
    far end.
- **MAX30101 earlobe clip** (`max_clip`, soft flex, one part):
  - **Tether:** a slack strap, about 47 mm from where it leaves the pod to
    the sensor. It carries the wires and catches the clip if it comes off;
    the magnets, not the tether, set the position. A flange is trapped
    inside the board pod under the lid.
  - **Cradle:** sits behind the earlobe, with the sensor window facing it.
    The breakout slides in from one end, with its 19 mm side along the
    tether and its pin edge toward the tether. An open strip across the back
    along the pin edge leaves room for the solder joints.
  - **Magnets:** two 9.5 × 0.8 mm discs stacked, pressed into a pocket right
    behind the board. Another stack goes in the finger.
  - **Finger:** printed already curled into a U from the cradle's far end. It
    goes under the lobe and up its front, with its magnets opposite the
    cradle's, so the two pull together through the lobe. The gap is 5 mm
    (soft, so roughly 3–7 mm lobes fit), giving 8 mm between the magnets.
    At that distance two stacked discs pull about 0.35 N, a light ear-clip
    squeeze. A single disc each side (about 0.1 N) would slip.
  - **Polarity:** put the cradle's and the finger's stacks in so they
    attract.
  - **Wires:** 4 thin wires (about 0.9 mm: power, ground, SDA, SCL) press
    into a groove along the tether's head-side face. It's 4 mm wide and
    1.4 mm deep, with a 3.4 mm mouth. It runs from inside the pod to the
    solder strip behind the board's pin edge.
  - **Printing:** on its flat side, with no supports.
- **Battery pod (left):** holds the 502030 cell under its lid. The cord comes
  in at the tip end, and the left strip's wires at the front.

### Printing

- **Rails and test clips:** PETG, top face down on the bed, no supports. The
  leaves and outer legs stand up from the bed. Use at least 2 perimeters (the
  leaves are 0.8 mm thick, two lines with a 0.4 mm nozzle). The only overhangs
  are the 45° lead-in ramps and the 1.4 mm channel and lip ledges.
- **Pods:** PETG, head-side face down, no supports. The leaves stand up from
  the bed, and the cavity opens upward. The outer wall bridges 9–11 mm over
  the tip slot.
- **Diffuser and corner caps:** natural PETG, plate down.
- **Liners, lids and arm:** soft flex, flat face down. The arm's cradle rims
  overhang 1.5 mm.
- **Corner:** soft flex, standing on its bottom end.

### Not done or not checked yet

- **Pod placement.** The render's head and ears are rough stand-ins. Where
  the pod sits behind a real ear, and whether the arm reaches the earlobe,
  needs a test fit.
- **Pod grip** comes from the same beam estimates as the rail, and is the
  weakest in the build. Print one pod with its liner and try it, including a
  tug on the cord.
- **Diffusion.** How well 0.8 mm of natural PETG, 1.5 mm off the LEDs,
  smooths them into a line is untested.
- **Hinge screw.** The rail starts 6 mm behind the hinge, and the corner and
  tongue pass over the hinge area. Both are guesses until the screw head's
  position and size are measured.
- **Folding.** How much the corner, and the strip inside it, put up with
  repeated folding is untested. The strip bends tightest at the corner when
  the glasses are folded.
- **Fusion.** The Fusion 360 script in `../glasses/fusion/` builds the v1
  parts only.

## Firmware

The firmware moves to Arduino C++ on the nRF52 core:
- It carries over the existing breath and pulse detectors.
- It keeps the same BLE UART protocol, so the Flutter app is unchanged.
- The animation runs at 100+ fps with sub-pixel interpolation, so waves glide
  between LEDs.
- It handles the button, auto sleep, the watchdog and the 3.6 V cut-off.

## To check before building

1. **LED sweep test on the current glasses.** Light one LED at a time from the
   flap toward the ear. Note where the dot stops being seen as a dot and where
   it stops being noticed at all.
2. **Flicker.** In a dark room, light one LED dimly and move your eyes quickly
   past it. A smooth streak is fine. A dotted trail means the 1 kHz PWM shows,
   and a thicker diffuser or a brighter, more distant glow is needed.
3. **Low-voltage behaviour.** Run a strip from a bench supply, stepping down
   from 4.2 V to 3.4 V. Note where the colours go wrong, then set the cut-off
   just above it.
4. **Test clips.** Print `test_clip_M` (and S and L if you have other glasses)
   and push it onto the temple. It should take a firm push, then not slide or
   twist.
