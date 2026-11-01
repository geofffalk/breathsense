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
lib/services/mood_analyzer.dart   App-side stress/focus/meditation from per-breath metrics
lib/models/breath_data.dart       Parses B lines (E/I ratio helper)
lib/models/heart_data.dart        Parses H lines
lib/models/settings.dart          OpenBreathingSettings, GuidedBreathingSettings, BreathingMode
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

## Planned changes for v2 (spec agreed 1 Nov 2026, not implemented)

Do these after the C++ firmware speaks the new protocol (see `breathsense-protocol`): remove
Guided (`BreathingMode.guided`, `GuidedBreathingSettings`, mode button, guided session periods);
add an **Off** mode (`M,O`; today the enum has no off and `M,O` is never sent - only `L,0` blanks
the LEDs); stop sending `M,F` on connect (`ble_service.dart` ~line 530) and stop assuming Open
(`_currentMode = BreathingMode.open`); parse the headset's `M,{F|H|O}` and show that mode. Stress
display stays as is (app-side breath score; the headset's LEDs use exhale length).

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
