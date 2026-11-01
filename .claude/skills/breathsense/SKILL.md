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
  magnetic pogo plug. Firmware to move to Arduino C++ keeping the same BLE protocol.

## The user's standing rules

- **Never commit without an explicit "yes".** Ask; don't assume. Branch `hardware-v2` holds the
  v2 work; much of it was uncommitted as of 31 Oct 2026 (last commit 961433b).
- **Everything on the glasses must be removable:** clips and snaps only. No tape, glue or
  heat-shrink on the glasses themselves (glue/heat-shrink on printed parts or wires is fine).
- **Writing style for READMEs and replies:** short plain sentences, bullets with bold lead-ins,
  tables for parts and settings, concrete numbers with units, say what's unverified.
- **Show work in Fusion:** export STEP and open it with `open -a "Autodesk Fusion" file.step`
  when the user wants to see or edit geometry. STL names end in their filament: `_petg` / `_flex`.
- The user prints in **PETG** (rigid parts) and **soft flex** filament (TPU-like; clips, liners,
  lids, skin-contact parts).

## Known open items (as of 31 Oct 2026)

- Not measured yet: the MAX30101 chip's exact position on the Pimoroni board (`CHIP_OFFSET`),
  the thermistor bead size, the pogo connector's real size, `LENS_TOP_Z`, which edge of the temple
  paddle grows.
- Untested: the closed soft-flex temple bands (open C-clips were judged too soft and replaced),
  the 0.45 mm translucent-PETG skin in front of each LED (does the slicer print it, how much light
  spreads), nose-clip comfort, LED visibility angles (sweep test), low-voltage LED behaviour.
- `render_onepiece.py` is broken (uses `mv.ARM_UP`, removed from `mount_v2.py`).
- Nothing since commit 961433b is committed (all v2 clip, nose, one-piece and skill work); ask.
- Firmware still targets v1 hardware; v2 firmware (Arduino) not started.
