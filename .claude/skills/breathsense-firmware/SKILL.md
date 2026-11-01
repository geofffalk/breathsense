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

## v2 plan (not started)

Port to Arduino C++ on the nRF52 core for the XIAO nRF52840 Plus: same detectors, same BLE
protocol, 100+ fps sub-pixel LED animation (wave crest cross-faded between LEDs), button (short =
mode, long = sleep), auto sleep after ~2 min with no breath or pulse into System OFF, wake on button
or USB, hardware watchdog, S8550 PNP switch (driven by an S8050 on D3) cutting LED power when dark, 3.6 V LED cut-off with amber
warnings. The LED state language is tabled in `hardware/v2/README.md` ("What the LEDs show for
each state"). On v2 the thermistor arrives through the nose clip's pogo socket, still on A0/GND.
