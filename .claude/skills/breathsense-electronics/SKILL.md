---
name: breathsense-electronics
description: BreathSense circuitry and parts - v1 headset (ItsyBitsy nRF52840, Adafruit LiPo backpack, switch, battery divider, NeoPixel strips, MAX30101, thermistor) and the v2 proposal (XIAO nRF52840 Plus, P-MOSFET LED switch, button, pods, nose-clip pogo plug), pin assignments, wiring, wire routes and power budget. Use for wiring, soldering, choosing parts, or pin questions.
---

# BreathSense electronics

Sources: `hardware/glasses/README.md` (v1 wiring section), `hardware/glasses/wiring.svg`,
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
| MAX30101 (Pimoroni, on hand) | Magnetic earlobe clip; 4 loose silicone wires (3V, GND, SDA, SCL), 70 mm, out of the right pod's ear-side wall (4 mm hole, knot inside) |
| 10k glass-bead NTC, ≤1 mm | In the nose clip just inside the right nostril; twisted 30 AWG pair, ~220 mm, loose along the cheek to a **2-pin 4 mm magnetic pogo** socket in the right pod's ear-side wall → A0 and GND |
| 502030 250 mAh LiPo (on hand) | Left pod; charges via USB-C in the right pod through the cord |
| P-MOSFET (AO3401) + 100k gate pull-up | Cuts LED power when dark (strips draw ~1 mA/LED idle) |
| 6 × 6 mm tactile button | Wake, sleep, mode; reset pinhole over the XIAO's reset |
| Magnets | Earlobe clip: 9.5 × 0.8 mm discs, 3 stacked each side. Nose clip: 2 × 1 mm, 2 stacked each leg |

- **Cord behind the head** between pods: battery +, ground, switched LED supply, left strip data.
- **Power rules:** LEDs off below 3.6 V (blue fails first as voltage drops; amber/red warnings),
  warning at ~3.75 V. Budget awake: XIAO+BLE ~5 mA, MAX30101 ~3 mA, 20 LEDs ~30-45 mA → ~3-3.5 h on
  250 mAh; asleep a few µA (System OFF, MOSFET off).
- **Bench checks before building:** LED sweep test for visibility angles, PWM flicker test in the
  dark, step a strip from 4.2 V down to 3.4 V to set the cut-off.
