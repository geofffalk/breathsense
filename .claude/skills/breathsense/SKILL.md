---
name: breathsense
description: Overview of the BreathSense project (glasses-mounted breath and heart biofeedback with LEDs in peripheral vision, a CircuitPython headset and a Flutter app). Use at the start of any BreathSense work, to find which part of the repo and which detailed skill applies, and for the user's standing rules.
---

# BreathSense: project overview

BreathSense is a wearable biofeedback device built by the user (Geoff Falk). A thermistor in the
breath stream and an optical pulse sensor on the earlobe drive LEDs that sit in the wearer's
peripheral vision on their glasses, and a phone app shows live data, mood scores and session
reports. Repo: `/Users/geofffalk/workspace/breathsense` (git, branches `main` and `hardware-v2`).

## Detailed skills

| Skill | Covers |
|---|---|
| `breathsense-firmware` | CircuitPython headset code: breath and pulse detection, LED modes, battery, settings, debugging, the nasal-clip variant, the planned v2 Arduino port |
| `breathsense-protocol` | The BLE UART line protocol between headset and app (every message, both ways) |
| `breathsense-app` | The Flutter app (`lib/`): BLE service, models, app-side mood scoring, screens, building |
| `breathsense-electronics` | Circuits, pins, parts, power: v1 (ItsyBitsy + backpack, built) and v2 (XIAO Plus, proposed) |
| `breathsense-cad` | 3D-printed mounts in build123d: v1 sleeves and v2 parts (one-piece temple part, hang pods, earlobe clip, nose clip), the CAD workflow, checks, printing, Fusion |

Load the relevant one before working; they hold the details and file pointers.

## Repo map

```
firmware/            CircuitPython headset firmware (ItsyBitsy nRF52840 Express, CP 10.0.3)
firmware/os/         CP .uf2, bootloader zip, adafruit-nrfutil
firmware_nasalclip/  Simplified firmware: XIAO nRF52840 nasal clip, thermistor only, no LEDs
lib/                 Flutter app ("BreathSense" on devices; app title/branding "BREATHCRAFT"; pubspec name breathing_app)
android/ ios/ macos/ linux/ windows/ web/   Flutter platform shells (Android package uk.co.visualate.breathsense)
hardware/glasses/    v1 glasses mount (build123d), wiring.svg, Fusion script for v1 parts
hardware/v2/         v2 hardware proposal + current CAD (README.md is the spec)
hardware/*.scad      Early OpenSCAD nasal clip and septum ring ideas (superseded)
```

## Hardware generations

- **v1 (built, prototype):** ItsyBitsy nRF52840 + Adafruit LiPo backpack + slide switch in a band
  behind the neck; two 10-LED NeoPixel strips on soft temple sleeves; MAX30101 on an earlobe arm;
  thermistor for breath. The firmware in `firmware/` targets this.
- **v2 (proposal, being designed on `hardware-v2`):** XIAO nRF52840 Plus in a pod hanging off the
  right temple tip, battery pod on the left, cord behind the head; one PETG part per temple
  carrying the LED strip round the hinge onto the frame front; magnetic earlobe clip for the
  MAX30101; soft-flex U band (nose clip) holding the thermistor inside the right nostril, wired to the pod by a
  magnetic pogo plug. Firmware to move to Arduino C++ (decided 1 Nov 2026), with a few protocol additions.

## Agreed behaviour (spec, 1 Nov 2026)

Full text and a discrepancy table: `hardware/v2/README.md`, "Behaviour specification" (it wins
over older README text). In short:
- Modes heart / breath / off; **guided is dropped**. Both sides mirror.
- Standalone default **heart**: lub-dub ("pa-pum") bars from the back toward the eye; resting rate
  = green, bars hardly reach the front 4 LEDs (flap 3 + hinge 1); stress (rate above resting, low
  HRV) → amber/red, reaching all 10. = v1 `HeartbeatLED`. Resting rate + stress range **saved to
  flash** (v1 relearns each power-on).
- **Breath**: original v1 motion (in-breath lights the bar's front, out-breath comet back) and
  original 5-colour exhale-length palette; stress = **exhale length only**; the bar's start index
  by colour: deep blue/purple 5, light blue 6, white 8, red 9 (tunable).
- Button: short = heart ⇄ breath, long = System OFF; wake (button/USB) in the **last mode** (saved).
- App: **connecting changes nothing**; the headset reports its mode (`M,{F|H|O}`); the app can set
  heart / breath / off. App off = LEDs dark + sensing paused, BLE on. Only the button fully offs.
- **All scoring on the wearable; the app is a displayer** (keeps session history/reports only).
  Nose clip worn = pogo plugged (A0 not full scale) + bead warm (~30-34 °C) + breath rhythm.
  Combined stress (app only, LEDs keep their rules) = 60% heart (50/50 HR and HRV) + 40% breath
  when the nose clip is worn, heart alone otherwise; the user asked for "whatever is medically shown
  to be better": HRV is the best-supported marker, breathing adds independent info, no validated
  fixed weights - say it's a personal trend, not medical. Focus/meditation ported from
  `mood_analyzer.dart` as-is. New `K` scores message (~1 Hz) and `S,W` weights.
- No auto sleep while the app is connected. BLE name `GlassesSense-XXXX` (chip-ID suffix); the
  user is considering renaming the product/app GlassesSense - app's name filter needs it.
- Order of work agreed: document (done) → C++ firmware (written in `firmware_v2/`, host-checked
  against v1 Python + app Dart; compiles for the ItsyBitsy, XIAO build pending) → app (done: modes from
  the headset, Off, scores from K, guided removed).

## The user's standing rules

- **Never commit without an explicit "yes".** Ask; don't assume. Branch `hardware-v2` holds the
  v2 work (last commit 67d9f69, 1 Nov 2026).
- **Everything on the glasses must be removable:** clips and snaps only. No tape, glue or
  heat-shrink on the glasses themselves (glue/heat-shrink on printed parts or wires is fine).
- **Writing style for READMEs and replies:** short plain sentences, bullets with bold lead-ins,
  tables for parts and settings, concrete numbers with units, say what's unverified.
- **Show work in Fusion:** export STEP and open it with `open -a "Autodesk Fusion" file.step`
  when the user wants to see or edit geometry. STL names end in their filament: `_petg` / `_flex`.
- **Heart feedback must be real time:** the LEDs animate in step with each heartbeat, so every
  beat must be caught live (no averaging over beats hides misses). Judge any pulse-sensor site or
  firmware change by missed beats and lag, not heart-rate accuracy.
- The user prints in **PETG** (rigid parts) and **soft flex** filament (TPU-like; clips, liners,
  lids, skin-contact parts).

## Known open items (as of 1 Nov 2026)

- Not measured yet: the MAX30101 chip's exact position on the Pimoroni board (`CHIP_OFFSET`),
  the thermistor bead size, the pogo connector's real size, `LENS_TOP_Z`, which edge of the temple
  paddle grows.
- Untested: the closed soft-flex temple bands (open C-clips were judged too soft and replaced),
  the 0.45 mm translucent-PETG skin in front of each LED (does the slicer print it, how much light
  spreads), nose-clip comfort, LED visibility angles (sweep test), low-voltage LED behaviour.
- `render_onepiece.py` is broken (uses `mv.ARM_UP`, removed from `mount_v2.py`).
- Pulse sensor site: the MAX30101 drives the heart LEDs fine from a fingertip. Two printable
  variants to compare by missed beats: the earlobe clip, and the head-side variant of the board pod
  (sensor in the pocket's head-side wall under the temple tip's end, where the temple presses;
  chip 0.8 mm proud).
- Earlobe clip resized for 12 × 3 mm neodymium discs (the first black 9.5 × 0.8 mm ones were
  ferrite, far too weak); untested. Nose clip is now a soft-flex U band in four sizes; untested.
- Firmware still targets v1 hardware (CircuitPython, ItsyBitsy); the v2 Arduino C++ port is next.
  Gaps to the spec are tabled in the v2 README (Discrepancies).
