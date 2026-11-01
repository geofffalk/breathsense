---
name: breathsense-electronics
description: BreathSense circuitry and parts - v1 headset (ItsyBitsy nRF52840, Adafruit LiPo backpack, switch, battery divider, NeoPixel strips, MAX30101, thermistor) and the v2 proposal (XIAO nRF52840 Plus, PNP transistor LED switch, button, pods, nose-clip pogo plug), pin assignments, wiring, wire routes and power budget. Use for wiring, soldering, choosing parts, or pin questions.
---

# BreathSense electronics

Sources: `hardware/glasses/README.md` (v1 wiring section), `hardware/glasses/wiring.svg` (v1), `hardware/v2/wiring.svg` (v2),
`firmware/PULSE_SENSOR.md`, `firmware/config.py`, `hardware/v2/README.md` (Parts, Layout, Power).

## Pins (firmware as it stands, v1)

| Pin | Use |
|---|---|
| A0 | Thermistor divider midpoint (10k 3V→A0, 10k NTC A0→GND) |
| A1 | Analog PulseSensor signal (only if no MAX3010x answers) |
| A2 | Battery ÷2 (100k BAT→A2, 100k A2→G) |
| D7 / D9 | Right / left NeoPixel strip DIN |
| SDA / SCL | MAX30101 (I2C 0x57) |
| 3V, G | Sensor power (shared by thermistor divider and MAX30101) |
| Vhi | LED strip + (higher of USB and battery, so strips run on battery) |

## v1 headset (built)

- **ItsyBitsy nRF52840 Express** + **Adafruit LiPo backpack #2124** underneath on header spacers
  (keeps reset/user buttons usable), charging at 100 mA (500 mA jumper open), **502030** LiPo
  (~200-250 mAh; red +, black -, white = thermistor, unused, heat-shrink it).
- Slide switch across the backpack's switch pads (cut the trace between them first); with USB in
  the board runs from USB regardless.
- Strips: Adafruit Ultra Skinny NeoPixel 1515, 4 mm, cut to 10-LED pieces (SK6805-EC15, rated
  3.7-5.5 V, ~1 mA each idle).
- Sensor: **Pimoroni MAX30101 breakout** (19 × 19 mm, narrows to 15 mm over its bottom 5 mm,
  pins in a row on that tab: 3-5V, SDA, SCL, INT, GND; every part on the sensor face; chip at the
  top edge, centred; mounting holes in the top corners). 3.3 V logic. INT unused. Twist SDA/SCL
  with GND on the run to the ear; drop I2C to 100 kHz if it drops out.
- Wire: 28-30 AWG silicone, ≤1 mm. v1 wire routes (sleeve channel, band grooves) are tabled in
  the glasses README.

## v2 proposal (designed, not built)

| Part | Notes |
|---|---|
| Seeed **XIAO nRF52840 Plus** (on hand) | 21 × 17.5 mm, built-in LiPo charger, USB-C |
| 2 × 10-LED NeoPixel 1515 pieces (on hand) | One per side: 6 in direct view around the hinge corner |
| MAX30101 (Pimoroni, on hand) | Magnetic earlobe clip; 4 loose silicone wires (3V, GND, SDA, SCL), 70 mm, out of the right pod's ear-side wall (4 mm hole, knot inside). Or (head variant) in the board pod's head-side wall on short internal wires |
| 10k glass-bead NTC, ≤1 mm | In the nose clip at the right nostril's entrance (~1 mm above the rim: higher up it cooled too slowly); twisted 30 AWG pair, ~220 mm, loose along the cheek to a **2-pin 4 mm magnetic pogo** socket in the right pod's ear-side wall → A0 and GND |
| 502030 250 mAh LiPo (on hand) | Left pod; charges via USB-C in the right pod through the cord |
| S8550 PNP + S8050 NPN (TO-92, user's transistor kit), 10k/2.2k/10k/100k | High-side LED switch on a 6-strip × 8-hole stripboard (`hardware/v2/switch_board.svg`: 5 cuts, 4 links, wires W1-W9); cuts LED power when dark (strips draw ~1 mA/LED idle) |
| Omron B3F tactile button (on hand, tall round plunger) | Wake, sleep, mode (diagonal pins: D6, GND); reset pinhole over the XIAO's reset |
| Magnets | Earlobe clip: one 12 × 3 mm neodymium disc each side (N35 or better; black ferrite is too weak). Nose clip: none (its soft-flex band grips by a light squeeze) |

- **v2 pins (proposed, `hardware/v2/wiring.svg`):** BAT+/BAT− pads ← LiPo via the cord (on-board
  charger and battery reading, no A2 divider); D7 right DIN; D2 left DIN (cord); D3 → 10k → S8050 base
  (100k base-GND), its collector → 2.2k → S8550 base (10k base-emitter, emitter BAT+, collector
  LED+); a 3.3 V pin alone can't turn a PNP on a 4.2 V rail off. D3 high = LEDs on. ~0.1 V drop,
  ~1.5 mA base drive while lit. Chosen because the user has only through-hole parts (no SMD
  AO3401; it would be better: ~0 V drop) and wants simple wiring, little to buy. Not low-side: a
  cut NeoPixel ground makes the strips power through their data pins; D4/D5 SDA/SCL MAX30101 (3V3 power); D6 button to GND, wakes
  from System OFF; D1 feeds the thermistor divider's 10k (high only to read; D1 not D7 because it neighbours D0, so the 10k bridges the pads - D0 and D7 are diagonally opposite corners; from 3V3 it would draw
  165 µA asleep); A0 (= the D0 pad: XIAO A0-A5 are D0-D5, the board only labels D0) divider midpoint, NTC via the pogo plug to GND. Drive DINs low before cutting
  LED+ (else the strips power through data). No power switch: button + System OFF.
- **Cord behind the head** between pods: battery +, ground, switched LED supply, left strip data.
- **Power rules:** LEDs off below 3.6 V (blue fails first as voltage drops; amber/red warnings),
  warning at ~3.75 V. Budget awake: XIAO+BLE ~5 mA, MAX30101 ~3 mA, 20 LEDs ~30-45 mA → ~3-3.5 h on
  250 mAh; asleep a few µA (System OFF, LED switch off).
- **Bench checks before building:** LED sweep test for visibility angles, PWM flicker test in the
  dark, step a strip from 4.2 V down to 3.4 V to set the cut-off.
