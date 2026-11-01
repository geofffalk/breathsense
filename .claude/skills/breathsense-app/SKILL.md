---
name: breathsense-app
description: The BreathSense / BREATHCRAFT Flutter app in lib/ - BLE service (scan, connect, parse, send), data models, app-side mood scoring (stress, focus, meditation), session reports, screens and widgets, platform permissions, and how to build and run it. Use when working on the phone app.
---

# BreathSense app (Flutter)

Flutter app at the repo root (`pubspec.yaml`: name `breathing_app`, version 1.0.1+2, Dart SDK
^3.10.7). Shown as **BreathSense** on devices; in-app title/branding **BREATHCRAFT**
(`BreathCraftApp` in `lib/main.dart`). Android package `uk.co.visualate.breathsense`.

Key packages: `flutter_blue_plus` (BLE), `provider` (state), `fl_chart` (graphs),
`permission_handler`, `audio_session` (pairs with an audio headset's name), `wakelock_plus` (screen
stays on while connected), `share_plus` (share report), `flutter_launcher_icons` (icon from
`assets/logo.png`).

Build/run: `flutter pub get`, `flutter run` (device attached), `flutter build apk` / `ios`.
Permissions: Android BLUETOOTH_SCAN/CONNECT (+ legacy and location); iOS
`NSBluetoothAlwaysUsageDescription`, peripheral and microphone usage strings in `Info.plist`.

## Structure

```
lib/main.dart                     ChangeNotifierProvider(BleService) → MaterialApp → MainScreen
lib/services/ble_service.dart     All BLE: scan/connect/reconnect, parse B/H/P/R, send M/S/L/Q,
                                  ring buffers for graphs, session tracking, battery state
lib/models/scores.dart            Scores from the headset's K line, display labels
lib/models/breath_data.dart       Parses B lines (E/I ratio helper)
lib/models/heart_data.dart        Parses H lines
lib/models/settings.dart          OpenBreathingSettings, MoodDetectionSettings, BreathingMode
                                  (open/guided/heart → M,F / M,G / M,H), MoodDetectionSettings;
                                  each has toMessage()
lib/models/session_data.dart      SessionData, MoodSnapshot, GuidedPeriod; trends, trajectories
lib/screens/main_screen.dart      Live view: connection, battery, mode selector, breath/heart graph,
                                  mood indicators, LED toggle, reset/report
lib/screens/settings_screen.dart  Colour thresholds, sensitivity, guided presets and timings, LED
                                  range, guided flow sensitivity, mood/calibration settings
lib/screens/report_screen.dart    Session report (stress, focus, meditation, cycle length), share
lib/screens/main_screen_minimal.dart  Stripped screen used for crash testing
lib/widgets/                      breath_graph, mode_selector, mood_indicators, mood_scale_bar,
                                  stress_indicator, threshold_slider
```

## v2 changes (done 1 Nov 2026)

The app is now a displayer for the v2 headset (`firmware_v2/`):
- **Modes:** `BreathingMode { open, heart, off }` (open = Breath, protocol letter F); Guided removed
  everywhere (settings model and screen section, graph colouring, phase indicator, session guided
  periods, report annotations). Mode selector: Breath / Heart / Off (`M,O`).
- **Mode comes from the headset:** no `M,F` on connect (sends `Q`); `_parseModeReport` handles
  `M,{F|H|O}`; `modeKnown` false until the first report ("Waiting for the headset..."). `setMode`
  sends and applies immediately (`_applyMode`).
- **Scores from `K`:** `lib/models/scores.dart` (`Scores.fromMessage`, labels, `stressScale` maps
  0-100 to the widgets' old -5..+5). `mood_analyzer.dart` removed from the app (reference copy kept
  at `firmware_v2/test/mood_analyzer_app.dart` for the firmware check). Session snapshots per
  breath use the latest K. Heart mode shows the heart readout plus the combined stress. Stress
  panel shows heart/breath parts and wear; focus panel shows focus/meditation.
- **Settings out:** `S,M` now carries the five stress weights. Settings > Mood (advanced) has a
  "Combined stress" block: heart vs breath and rate vs HRV sliders; drag previews
  (`previewFusionWeights`), release sends `S,W` once (each is a flash write on the headset). R
  doesn't report the weights, so the app shows the last values it sent (defaults 0.6, 0.5). R's guided fields ignored; LED state from field 16.
- Auto-connect names include `glassessense`.
- `flutter analyze lib`: no errors (17 issues, down from 27; remaining warnings pre-date this).

## Behaviour worth knowing

- Message formats: see the `breathsense-protocol` skill. After connecting the app sends `M,F` and
  starts a session; switching Guided → Open resets the session and mood calibration.
- Guided presets on the settings screen: Box Breathing 5/5/5/5, Flow Breathing 5/0/5/0 (HRV),
  Extended Exhale 4/0/8/0 (anxiety).
- `MoodAnalyzer`: valid breaths only (same limits as firmware); baseline cycle and peak flow taken
  after `calibrationBreaths` (6), then adapted 2% per breath. Stress weights: E/I ratio 0.40,
  duration vs baseline 0.25, peak flow 0.15, RMSSD of cycle lengths 0.15, smoothness 0.05 (calm at
  E/I 1.5, anxious at 0.8). Focus from cycle consistency (CV); meditation from slow, stable cycles
  (optimal ~10 s). Advanced settings can override weights.
- Heart mode: graph shows the live `wave`; heart icon beats on `beats` changes; stress and HRV
  shown from the headset.
- Battery shown next to settings: voltage, percent, charging icon when `usb` is 1; "No battery seen
  (switch off?)" for -1.
- Main screen hints: "Clip sensor to earlobe" (heart), "Not detecting breath — check sensor is
  attached and under nostril" (unworn).
