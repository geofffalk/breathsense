---
name: breathsense-protocol
description: The BreathSense BLE protocol between the headset firmware and the Flutter app - Nordic UART service, every message format in both directions (B, H, P, R from the headset; M, S, L, Q from the app), field meanings and known quirks. Use when changing either side of the link, adding a message, or debugging data between headset and app.
---

# BreathSense BLE protocol

Transport: **Nordic UART Service** over BLE. Lines of ASCII, comma-separated, ending in `\n`.

| | UUID |
|---|---|
| Service | `6e400001-b5a3-f393-e0a9-e50e24dcca9e` |
| App writes to (headset RX) | `6e400002-…` (`txCharUuid` in the app) |
| App subscribes to (headset TX) | `6e400003-…` (`rxCharUuid` in the app) |

Sources of truth: firmware `firmware/code.py` (`send_*`, `parse_message`) and
`firmware/settings_storage.py` (`settings_to_message`); app `lib/services/ble_service.dart`,
`lib/models/breath_data.dart`, `heart_data.dart`, `settings.dart` (`toMessage`). Keep both sides
in step; parsers on both sides accept missing trailing fields with defaults, so append new fields
at the end.

## Discovery and connect

- Headset advertises the UART service with `ble.name` read from `asset_id.txt` on the board
  (currently a MAC-like string, `00:9F:38:AC:83:A5`; default `BreathingV2`).
- App scans without a service filter and connects to, in order: the last connected device; a
  device named like the phone's connected audio device; a name containing one of `sonar, bliss,
  breathcraft, vs-pulse, raspberrypi, breathing`; any name shaped like a MAC address.
- On connect the headset switches to Open mode, plays an orange comet, sends `R,…` (settings) and
  `P,…` (battery). The app waits 500 ms, then sends `M,F`. App writes use write-with-response.

## Headset → app

**`B` breath, 10 Hz (all modes except Heart)**
`B,{ts},{phase},{flow},{depth},{guided},{exhale_dur},{inhale_dur},{cycle_dur},{smoothness},{peak_flow},{symmetry},{unworn}`

| Field | Meaning |
|---|---|
| ts | ms since boot (masked to 32 bits) |
| phase | 0 idle, 1 inhale, 2 exhale |
| flow | normalised flow, about -1..1+ (inhale positive), 3 dp |
| depth | colour index from last exhale length: 0 red, 1 white, 2 light blue, 3 purple, 4 deep blue |
| guided | guided phase: -1 not guided or waiting for first exhale, 0 inhale, 1 hold in, 2 exhale, 3 hold out |
| exhale_dur, inhale_dur, cycle_dur | seconds, of the last complete valid breath |
| smoothness | 0-100 (100 smooth), from 2nd derivative of exhale flow |
| peak_flow | peak exhale flow magnitude (unnormalised flow_lp) |
| symmetry | 0-100: where the exhale peak falls (0 front-loaded, 100 back-loaded) |
| unworn | 1 after 6 consecutive exhales under 0.6 s; cleared by an exhale of 1.5 s+ |

**`H` heart, 25 Hz (Heart mode only; replaces `B`)**
`H,{ts},{wave},{bpm},{signal},{beats},{stress},{hrv}`
wave = live normalised pulse trace; bpm/beats follow the LEDs' steady rhythm (not raw detections);
signal 1 while that rhythm runs; beats wraps at 65535; stress 0-100; hrv = RMSSD ms (0 until ~15
clean beats).

**`P` battery, every 10 s and on connect**
`P,{mv},{percent},{usb}` - percent -1 when no battery seen (< 2.8 V); usb 1 only when enumerated
by a computer (`supervisor.runtime.usb_connected`), not a wall charger.

**`R` settings, on connect and in reply to `Q`**
`R,{very_short},{short},{medium},{long},{sensitivity},{inhale},{hold_in},{exhale},{hold_out},{led_start},{led_end},{calm_ratio},{calm_var},{focus_con},{cal_breaths},{led_enabled},{color_scheme}`

## App → headset

| Message | Effect |
|---|---|
| `M,F` | Open (free) breathing mode; resets mood calibration |
| `M,G` | Guided breathing; restarts the guided cycle |
| `M,H` | Heart mode (stream `H` instead of `B`) |
| `M,O` | Standby: LEDs off, data still sent |
| `S,F,{vs},{s},{m},{l}[,{sens}]` | Exhale-length colour thresholds (s); saved. App appends sensitivity; firmware ignores it here |
| `S,G,{in},{hold_in},{ex},{hold_out},{led_start},{led_end}[,{ex_thresh},{in_thresh}]` | Guided timings, LED range, flow thresholds (0.3-1.0); saved |
| `S,CS,{0-2}` | Guided colour scheme (0 green/orange/cyan, 1 yellow/purple/white, 2 blue/magenta/white) |
| `S,C,{0-9}` | Breath sensitivity preset (5 default) |
| `S,M,{calm_ratio},{calm_var},{focus_con},{cal_breaths}` | Mood settings; firmware uses only cal_breaths |
| `L,{1\|0}` | LEDs on/off; saved |
| `Q` | Ask for `R` |

## v2 changes (agreed 1 Nov 2026; implemented in `firmware_v2/`, app not yet)

- Headset → app **`M,{F|H|O}`**: current mode (breath / heart / off), sent on connect and on every
  change (button, app, wake). The headset no longer switches mode on connect.
- App stops sending `M,F` on connect; waits for the `M` report. `M,O` becomes the app's off
  (LEDs dark, sensing paused, BLE stays on; only the button does a full System OFF).
- Guided is dropped: `M,G`, `S,G`, `S,CS` go; `R` keeps its guided fields in place, unused.
- Headset → app **`K,{stress},{focus},{meditation},{heart_stress},{breath_stress},{nose_worn},{heart_worn},{calibrating}`**
  ~1 Hz: all scores computed on the headset (app's `mood_analyzer` moves to firmware); app → headset
  **`S,W,{heart},{breath},{hr},{hrv}`** sets the fusion weights (defaults 0.6, 0.4, 0.5, 0.5).
  Scales: stress, heart_stress, breath_stress 0-100 (app's breath stress -5..+5 → (s+5)×10);
  focus, meditation 0-10; flags 0/1. Labels (CALM, TENSE...) stay in the app as display only.
- The app's breath-stress tuning (ratio/duration/smoothness/peak-flow/RMSSD weights, calm ratio,
  focus CV) lives only in the app today; with scoring on the headset it must be sent: extend
  `S,M` to `S,M,{calm_ratio},{calm_var},{focus_con},{cal_breaths},{w_ratio},{w_dur},{w_smooth},{w_peak},{w_rmssd}`
  (trailing fields optional, firmware defaults = the app settings' defaults).
- "The v2 plan keeps this protocol unchanged" below is superseded by these additions.

## Known quirks

- LED on/off is stored under `led_on` by `L` but reported from `led_enabled` in `R`, so `R` always
  reports the default 1. Fix both sides together if touched.
- Settings save fails silently (read-only) while the board's drive is mounted on a computer.
- The v2 plan keeps this protocol unchanged so the app needs no changes.
