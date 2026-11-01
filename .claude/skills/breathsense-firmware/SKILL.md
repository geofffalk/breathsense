---
name: breathsense-firmware
description: BreathSense headset firmware in CircuitPython (firmware/ and firmware_nasalclip/) - main loop and modes, thermistor breath detection, MAX3010x/analog pulse detection with steady rhythm, stress and HRV, LED displays (open, guided, heart), battery, settings storage, config knobs, deploying and debugging, and the planned v2 Arduino port. Use when reading, changing, tuning or deploying headset code.
---

# BreathSense firmware

CircuitPython 10.0.3 on an **ItsyBitsy nRF52840 Express** (v1 headset). Files in `firmware/` are
copied to the CIRCUITPY drive: `code.py config.py breath_detector.py breath_metrics.py
pulse_detector.py max3010x.py led_control.py battery.py settings_storage.py asset_id.txt` and
`lib/` (`adafruit_ble/`, `neopixel.mpy`). `firmware/os/` has the CP `.uf2`, the bootloader zip and
`adafruit-nrfutil` for reflashing (double-tap reset → drag the .uf2). Serial console:
`screen /dev/tty.usbmodem*` (or Mu/Thonny). `log()` only prints when USB is connected.

The protocol is in the `breathsense-protocol` skill; pins and circuits in `breathsense-electronics`.

## Main loop (`code.py`)

~100 Hz loop: `detector.tick()`, `pulse.tick()`, `battery.tick()` always run. Connected: handle RX,
send `H` (Heart mode) or `B` (otherwise), send battery, drive LEDs per mode and the LED toggle.
Not connected: keep advertising and run the standalone LED mode (`STANDALONE_MODE`, currently
`"heart"`). Modes: STANDBY 0, OPEN 1, GUIDED 2, HEART 3. Connect → OPEN + orange comet; boot →
blue comet. `gc.collect()` every 200 loops.

## Breath detection (`breath_detector.py`, `breath_metrics.py`)

- Thermistor on A0: 10k from 3V to A0, NTC from A0 to GND. `read_temp_c()` uses the Beta equation
  (`R_REF`, `R0` 10k, `BETA` 3435, `T0_C` 25). Set `BETA` to the actual bead's B value.
- At 100 Hz: fast EMA (`ALPHA_FAST`) and slow baseline EMA (`ALPHA_SLOW`); flow = -(fast - slow),
  so inhale (cooling) is positive. Low-pass with derivative boost (`alpha_flow`, `deriv_gain`).
  Separate leaky peak trackers for each sign normalise flow to about ±1.
- Phases: inhale when norm > `th_start`, exhale when norm < -`th_start`, with `MIN_PHASE_S` and a
  refractory period; idle after |norm| and slope stay small for `IDLE_HOLD_S`×1.5.
- Sensitivity presets 0-9 (`SENSITIVITY_PRESETS`: alpha_flow, deriv_gain, th_start, th_end).
- Exhale length → depth colour via thresholds 2.0/3.5/5.0/6.5 s (red, white, light blue, purple,
  deep blue).
- `BreathMetrics`: per valid breath (exhale 0.3-15 s, inhale 0.2-10 s) records durations,
  smoothness, peak flow, symmetry. Mood scores themselves are computed in the app.
- Unworn: 6 exhales in a row under 0.6 s; cleared by one of 1.5 s+. (LED blanking on unworn is
  commented out in `OpenBreathingLED.tick`.)

## Pulse detection (`pulse_detector.py`, `max3010x.py`)

- `PULSE_SENSOR = "auto"`: MAX3010x on I2C (addr 0x57, part id 0x15) if it answers, else analog
  PulseSensor on A1. MAX3010x runs SpO2 mode, 100 samples/s, IR channel only, 18-bit; IR current
  `MAX3010X_IR_CURRENT`, skin threshold `MAX3010X_SKIN_LEVEL` (not-worn gating).
- Chain: low-pass (`PULSE_FILTER_HZ` 3) → baseline removal → adaptive envelope → rising-edge
  threshold; beat reported at its peak. Beats must be regular (`PULSE_REGULARITY`), consistent in
  height, 400-2000 ms apart; 3 in rhythm before shown, then locked to a ±25% window.
- LEDs and app follow a **steady rhythm** started by confirmed beats and nudged by detected ones
  (`HEART_PHASE_*`, `HEART_RATE_*`, max ~2 BPM change per beat); coasts `HEART_COAST_S` 8 s.
- Stress = 70% heart rate above a learned resting baseline (falls fast, rises slowly; full-stress
  rise learned as 4× typical rise, 10-30 BPM) + 30% HRV (RMSSD over ~30 beats) below its average.
  Baselines restart each power-on.
- Debug flags in `config.py`: `PULSE_DEBUG_STATS` (1 s summary), `PULSE_DEBUG_PLOT` (plotter),
  `PULSE_DEBUG_RAW` (every sample, for offline replay). Full guide: `firmware/PULSE_SENSOR.md`.
- **Status (1 Nov 2026):** the heart LEDs follow every beat fine from a fingertip. For weaker head
  sites (earlobe, the groove behind the ear under the temple): raise IR drive (`0x2F` = 9.4 mA
  now; up to ~`0x7F`, back off on clipping), retune `MAX3010X_MIN_AMP` and `MAX3010X_SKIN_LEVEL`,
  and consider the MAX30101's **green** LED (LED3, multi-LED mode; the MAX30102 has none), better
  for reflective sites. Site strength, roughly: fingertip > earlobe > behind the ear (needs bare
  skin, no hair; jaw motion when talking). The 3 Hz low-pass adds some lag.

## LEDs (`led_control.py`)

Two strips: left D9, right D7, declared 20 pixels each, brightness 0.1; only indices 0-9 are used
and both sides show the same pattern. Index 9 is the front (near the eye), 0 the back.
- **Open:** inhale lights the front LED in the depth colour; exhale runs a 2-LED comet front→back
  over the predicted exhale length; dark after 4 s idle. Phase changes debounced 0.35 s.
- **Guided:** inhale/hold/exhale/hold cycle with configurable seconds and LED range
  (`led_start`..`led_end`); waits for the first real exhale, and phase time only accumulates while
  flow exceeds the inhale/exhale thresholds (flow-gated timing). Three colour schemes.
- **Heart:** each shown beat fills the arm from the base and empties, with a smaller counter-beat
  (lub-dub). Fill 5 LEDs at rest up to 10 at full stress; colour green → amber → red with stress.

## Battery and settings

- `battery.py`: BAT through 100k/100k to A2, 16-read average, smoothed, LiPo curve to percent;
  `-1` below 2.8 V. `BATTERY_PIN = None` if the divider isn't fitted.
- `settings_storage.py`: `/settings.json` merged over defaults; saving fails (read-only) while
  the drive is mounted on a computer.

## Nasal clip variant (`firmware_nasalclip/`)

XIAO nRF52840, thermistor only, no LEDs, no guided mode; same `B` messages so the app works
unchanged. Same breath detector and metrics, trimmed.

## v2 firmware (`firmware_v2/`, Arduino C++, written 1 Nov 2026)

`firmware_v2/README.md` has the overview, files, build and hardware-test list. Layout:
`wearable/wearable.ino` (stub calling `app_setup`/`app_loop`) + `app.cpp` (BLE via Bluefruit, modes,
button, sleep, scheduling, animations, flash saves, USB-serial debug line) + pure C++ modules `breath.*`, `pulse.*`, `scoring.*` (mood from Dart, nose wear, fusion),
`display.*`, `protocol.*` (no Arduino calls) + hardware `max3010x.*`, `hw.*`, `storage.*`
(LittleFS structs, versioned). `config.h` holds pins (XIAO; ItsyBitsy for compile checks) and every
constant with v1 names/values.
- **Faithfulness check:** `python3 firmware_v2/test/compare.py` runs the C++ (clang++) against the
  v1 Python (hardware modules stubbed via sys.modules, time.monotonic/ticks patched) and the app's
  Dart MoodAnalyzer (`test/mood_ref.dart`, app settings' weights) on synthetic signals, including
  both LED displays frame by frame and the B/H/R lines. Everything matches at 0.05% (one heart frame
  in 3448 off by a colour level). Rerun after any detector/display change. Lessons: breath detector
  must use doubles (float constants like 0.22f/0.35f cross thresholds a sample early); compare
  timestamps absolutely; build the host test with -ffp-contract=off; v1's hide_all() leaves
  _show_pixels' cache stale (the C++ shows the frame v1 skipped).
- **Board build (1 Nov 2026):** compiles for the XIAO nRF52840 Plus (Seeed nRF52 Boards 1.1.13,
  fqbn `Seeeduino:nrf52:xiaonRF52840Plus`): 154.6 KB flash, 16.3 KB RAM; and for the ItsyBitsy
  (Adafruit 1.7.0, `adafruit:nrf52:itsybitsy52840:softdevice=s140v6,debug=l0`) with no warnings in
  this code. This Mac's installed toolchain lacks newlib headers, so builds use ARM GCC 9-2019-q4
  unpacked in the scratchpad, Seeed's core cloned into `<scratchpad>/hw/Seeeduino/nrf52`, and
  Adafruit_NeoPixel 1.12.3 in `<scratchpad>/libs`, via arduino-builder
  (/Applications/Arduino.app/Contents/Java) with `-prefs runtime.tools.arm-none-eabi-gcc.path=`,
  `runtime.tools.arm-none-eabi-gcc-9-2019q4.path=` and `runtime.tools.CMSIS-5.7.0.path=`
  ~/Library/Arduino15/packages/adafruit/tools/CMSIS/5.7.0 (Seeed's core needs CMSIS; without it:
  core_cm4.h not found). Running these needed the user's explicit per-command approval (auto-mode
  classifier). Core links `-u _printf_float`, so `%f` in snprintf works.
- Gotchas handled: D7 (thermistor divider top) high whenever sensing, low in off/sleep - the
  unplugged check (A0 ≥ 97% full scale) needs it; `analogReference(AR_VDD4)` for the ratiometric
  divider, AR_INTERNAL_3_0 briefly for VBAT; P0.14 kept low (Seeed warning); data pins driven low
  before the LED switch turns off and NeoPixels re-`begin()` after power-on; LED power cut after 2 s
  dark; MTU 247 requested; heart baselines restored so `update_stress` doesn't overwrite them.
- Board macros (from boards.txt): `ARDUINO_Seeed_XIAO_nRF52840_Plus` (+ Sense/non-Plus),
  `ARDUINO_NRF52_ITSYBITSY`; anything else is an #error. XIAO variant: A0 = D0 pad, PIN_VBAT 35,
  VBAT_ENABLE 14, SDA/SCL 4/5. The waking button press is ignored until released. Battery cut-off
  needs 5 low readings in a row. No auto sleep on USB (spec updated).
- Auto-sleep warning (3 dim swells, last 5 s) and charging display (USB + 10 s idle: amber swell, or
  dim green at >= 4.15 V; no charge-status pin on the XIAO) are in (`display.*`, `app.cpp`).
- Not yet: OTA DFU.

## v2 spec notes (agreed 1 Nov 2026)

Behaviour to implement is the spec in `hardware/v2/README.md` ("Behaviour specification" +
Discrepancies; summary in the `breathsense` skill). Differences from this v1 code: modes heart /
breath / off only (drop GuidedBreathingLED, `M,G`, `S,G`, `S,CS`); don't switch to Open on
connect, send `M,{F|H|O}` on connect and every change; breath LEDs keep OpenBreathingLED's motion
but start the inhale LED/comet at index 5/5/6/8/9 for depth 4/3/2/1/0 (deep blue..red); heart =
HeartbeatLED unchanged; save the heart baseline/stress range and the last mode to flash; button
short = heart⇄breath, long = sleep; `M,O` = LEDs dark + sensing paused, BLE on. v1 code was
written for the ItsyBitsy nRF52840 (D7/D9 strips, A2 battery divider, slide switch) - use it as the
reference for detectors and displays, not pins.
**All scoring moves to the firmware** (app becomes a displayer):
- Port `lib/services/mood_analyzer.dart` unchanged (stress -5..+5 from E/I ratio, cycle vs
  calibration baseline, smoothness, peak flow vs baseline, breath-cycle RMSSD, short-breath
  penalty; focus 0-10 from cycle CV; meditation 0-10 from cycle length × stability; 6-breath
  calibration, 2%/breath baseline drift). Use the app settings' weights as defaults
  (`lib/models/settings.dart`), not the analyzer's own field defaults, where they differ.
- Nose clip worn = A0 not near full scale (pogo plugged) + bead temp ~30-34 °C (well above room)
  + a breath rhythm in the last few seconds. Heart worn = MAX3010x skin level (exists).
- Combined stress (app only; LEDs keep their rules) = 0.6 heart + 0.4 breath when the nose clip
  is worn, heart alone otherwise; heart part here = 0.5 rate + 0.5 HRV (the LEDs keep 0.7/0.3).
  Breath stress mapped (s+5)×10 to 0-100. Weights settable by `S,W`. Send `K` ~1 Hz.
LED index 0 = back (DIN end, fitted at the temple end nearest the pod), 9 = front flap LED;
front 4 = indices 6-9 (flap 3 + hinge 1).


Port to Arduino C++ on the nRF52 core for the XIAO nRF52840 Plus: same detectors, same BLE
protocol, 100+ fps sub-pixel LED animation (wave crest cross-faded between LEDs), button (short =
mode, long = sleep), auto sleep after ~2 min with no breath or pulse into System OFF, wake on button
or USB, hardware watchdog, S8550 PNP switch (driven by an S8050 on D3) cutting LED power when dark, 3.6 V LED cut-off with amber
warnings. The LED state language is tabled in `hardware/v2/README.md` ("What the LEDs show for
each state"). On v2 the thermistor arrives through the nose clip's pogo socket, still on A0/GND.
