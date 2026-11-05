# GlassesSense v2 firmware (Arduino C++)

Firmware for the v2 wearable (Seeed XIAO nRF52840 Plus). Behaviour is set by the spec in
`hardware/v2/README.md` ("Behaviour specification"), and the wiring by `hardware/v2/wiring.svg`.
It's a port of the v1 CircuitPython firmware in `firmware/`, which was written for the ItsyBitsy
nRF52840 and stays the reference for the detectors and displays.

**Status:** checked against the originals on a computer, and compiles for the board.
- **XIAO nRF52840 Plus** (Seeed nRF52 Boards 1.1.13): 159.5 KB of 811 KB flash, 16.3 KB of 238 KB
  RAM.
- **ItsyBitsy nRF52840** (Adafruit's core 1.7.0, compile check only): no warnings in this code.

Not yet run on hardware.

## What it does

- **Modes:** heart (the default), breath and off.
  - **Button:** a short press switches heart and breath; a long press (1.2 s) is full sleep.
  - **Waking:** the button or USB wakes it, in the last mode (saved to flash).
- **Breath and heart:** both are sensed in heart and breath modes, because the combined score
  needs both. Off (from the app) pauses sensing and darkens the LEDs, but Bluetooth stays on.
- **LEDs:** the v1 heart display unchanged. The v1 breath motion, with the bar's front set by the
  exhale colour (5 LEDs per side, v3 front: index 4/4/3/2/2 for red/white/light blue/purple/deep blue;
  10 LEDs, v2 temple strips, built with `-DLED_STRIP_LEN=10`: 9/8/6/5/5).
- **Scores:** the app's breath scoring (ported unchanged), nose-clip wear detection, and the
  combined stress (60% heart, 40% breath) all run here. They're sent as `K` about once a second.
- **Connecting changes nothing:** the headset reports its mode (`M,{F|H|O}`) on connect and on
  every change.
- **Bluetooth name:** `GlassesSense-XXXX`.
- **Power:**
  - **Auto sleep:** after 2 minutes with no breath and no pulse, never while connected or on
    USB. It also sleeps 30 s after waking if nothing is sensed.
  - **Auto sleep coming:** three dim white swells over the last 5 s; breath, a pulse or the button
    cancels it.
  - **Charging:** on USB with nothing sensed for 10 s, a slow amber swell every 3 s, or steady dim
    green once the battery reads 4.15 V or more (the XIAO has no charge-status pin, so it's judged
    from the voltage).
  - **LED power:** cut whenever the LEDs have been dark for 2 s.
  - **Battery:** below 3.6 V for 5 readings in a row (10 s): a battery message to the app, three
    amber flashes, sleep. An amber warning blip below 3.75 V.
  - **Watchdog:** 8 s; after a hang it gives one red blip, shuts the MAX30101 down and goes back
    to sleep.
- **Bring-up:** with USB attached it prints a status line once a second on the serial monitor
  (115200): battery, thermistor reading and plug state, nose-clip wear, sensor and skin, heart rate,
  stress, HRV, breath count, connection.
- **Saved to flash:** the heart's resting rate, stress range and HRV baseline, every 5 minutes,
  on a mode change and before sleep.

## Files (`wearable/`)

| File | What it is |
|---|---|
| `wearable.ino` | Just calls `app_setup()` / `app_loop()` (keeps the Arduino builder's generated prototypes out of the main code) |
| `app.cpp` | Main loop: BLE, modes, button, sleep, scheduling, animations, saving, a debug line over USB serial |
| `config.h` | Pins (XIAO, with ItsyBitsy for compile checks) and every tuned constant |
| `breath.*` | Breath phases and per-breath metrics (from `breath_detector.py`, `breath_metrics.py`) |
| `pulse.*` | Beats, display rhythm, HRV and heart stress (from `pulse_detector.py`) |
| `scoring.*` | Mood scores (from `mood_analyzer.dart`), nose-clip wear, combined stress |
| `display.*` | LED frames: heart, breath, comets |
| `protocol.*` | BLE message formats and parsing |
| `max3010x.*`, `hw.*`, `storage.*` | Sensor driver, board I/O (thermistor, battery, LED switch, button, sleep, watchdog), flash |

The detector, scoring, display and protocol files are plain C++ with no Arduino calls, so they
build and run on a computer too.

## Checking the port

```
python3 firmware_v2/test/compare.py
```

This runs the C++ on synthetic breathing and pulse signals and compares it with:
- the v1 Python (its hardware modules stubbed): breath and pulse detection, both LED displays frame
  by frame, and the `B`, `H` and `R` messages;
- the app's Dart mood analyzer.

Needs `clang++` and the Flutter SDK's `dart`. As of 1 Nov 2026 everything matches, even at 0.05%
tolerance, except one heart frame in 3,448 (one colour level, from 32-bit floats in the pulse
detector). The breath detector uses doubles: with float constants its thresholds crossed a sample
early.

## Building for the board

1. In the Arduino IDE's Boards Manager, install **Seeed nRF52 Boards** (the non-mbed core, which
   has the XIAO nRF52840 Plus).
2. In the Library Manager, install **Adafruit NeoPixel**.
3. Open `wearable/wearable.ino` and select the XIAO nRF52840 Plus board.

The Adafruit nRF52 1.7.0 core installed on this Mac is incomplete (its ARM compiler has no C
library headers), so it can't build anything until it's reinstalled. The builds above used the ARM
GCC 9-2019-q4 toolchain unpacked separately, and pointed Seeed's core at the CMSIS 5.7.0 that
Adafruit's core installed (`runtime.tools.CMSIS-5.7.0.path`), because Seeed's core wasn't installed
through the Boards Manager.

## To test on the hardware

- USB plug-in waking it from full sleep. The nRF52840 supports this, but it's untested here with
  the Bluetooth stack running.
- Battery reading: the XIAO's divider factor and reference are from its schematic. Check against
  a meter.
- Thermistor: `BETA`, and the wear thresholds (`NOSE_WARM_C` 28, `NOSE_COOL_C` 26.5). The bead now sits at
  the nostril's entrance, where each in-breath cools it further than it did higher up.
- MAX30101 at the head site: raise `MAX3010X_IR_CURRENT`; consider the green LED.
- Breath start indices (9/8/6/5/5) on the real glasses.

## Not done yet

- Over-the-air firmware updates.
