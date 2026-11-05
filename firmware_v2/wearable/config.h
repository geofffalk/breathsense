// config.h - GlassesSense v2 wearable: pins and tuning.
//
// Ported from firmware/config.py (the v1 CircuitPython firmware for the ItsyBitsy nRF52840).
// Detector and display constants keep their v1 names and values; v2 adds the button, sleep, the
// LED power switch, wear detection and stress fusion. Behaviour spec: hardware/v2/README.md,
// "Behaviour specification".

#pragma once

#include <stdint.h>

// ---------------------------------------------------------------- board
// The target is the Seeed XIAO nRF52840 Plus (Seeed nRF52 core). The ItsyBitsy nRF52840 build is
// for compile checks on Adafruit's core only; its pins are v1's and it has no button or switch.
// Board macros are ARDUINO_ + build.board from each core's boards.txt (checked 1 Nov 2026).
#if defined(ARDUINO_Seeed_XIAO_nRF52840_Plus) || defined(ARDUINO_Seeed_XIAO_nRF52840_Sense_Plus) || \
    defined(ARDUINO_Seeed_XIAO_nRF52840) || defined(ARDUINO_Seeed_XIAO_nRF52840_Sense)
#define BOARD_XIAO 1
#elif defined(ARDUINO_NRF52_ITSYBITSY)
#define BOARD_XIAO 0
#elif !defined(ARDUINO)
#define BOARD_XIAO 0             // Host build (firmware_v2/test): pins unused
#else
#error "Unknown board: select Seeed XIAO nRF52840 Plus (or ItsyBitsy nRF52840 for a compile check)"
#endif

#if BOARD_XIAO
#define PIN_LED_RIGHT     7      // D7: right strip DIN
#define PIN_LED_LEFT      2      // D2: left strip DIN, through the cord
#define PIN_LED_POWER     3      // D3: S8050 base (high = LED power on)
#define PIN_BUTTON        6      // D6: button to GND
#define PIN_THERM_POWER   1      // D1: top of the thermistor divider (high only while sensing), next
                                 // to D0 so the 10k bridges the two pads
#define PIN_THERM         A0     // The D0 pad: divider midpoint (thermistor through the pogo plug)
#define HAS_BUTTON        1
#define HAS_LED_SWITCH    1
#else  // ItsyBitsy nRF52840 (v1 wiring), compile checks only
#define PIN_LED_RIGHT     7
#define PIN_LED_LEFT      9
#define PIN_LED_POWER     -1
#define PIN_BUTTON        -1
#define PIN_THERM_POWER   -1     // v1 feeds the divider from 3V
#define PIN_THERM         A0
#define HAS_BUTTON        0
#define HAS_LED_SWITCH    0
#endif

// ---------------------------------------------------------------- identity
#define DEVICE_NAME_PREFIX "GlassesSense"   // Advertised as GlassesSense-XXXX (chip ID)
#define FIRMWARE_VERSION   "2.0.0"
#define BOOT_LOG_WAIT_MS   20000   // Bring-up: with USB in, wait this long for a serial monitor before starting

// ---------------------------------------------------------------- breath detection (v1 values)
// Doubles, like v1's Python, so the filters cross thresholds on the same samples (0.22f != 0.22).
constexpr double FS_HZ = 100.0;
constexpr double ALPHA_FAST = 0.22;
constexpr double ALPHA_SLOW = 0.004;
constexpr double ALPHA_FLOW = 0.22;
constexpr double DERIV_GAIN = 0.18;
constexpr double TH_FRAC_START = 0.30;
constexpr double TH_FRAC_END = 0.20;
constexpr double MIN_PHASE_S = 0.20;       // Times are doubles, compared as in v1 (Python floats)
constexpr double EMA_MAG = 0.20;
constexpr double LEAK_DECAY = 0.994;
constexpr double SCALE_FLOOR = 0.02;
constexpr double IDLE_MAG_FRAC = 0.20;
constexpr double IDLE_SLOPE_FRAC = 0.06;
constexpr double IDLE_HOLD_S = 2.2;

// Exhale length -> colour index (0 red, 1 white, 2 light blue, 3 purple, 4 deep blue)
constexpr float DEFAULT_VERY_SHORT_MAX = 2.0f;
constexpr float DEFAULT_SHORT_MAX = 3.5f;
constexpr float DEFAULT_MEDIUM_MAX = 5.0f;
constexpr float DEFAULT_LONG_MAX = 6.5f;

// Sensitivity presets 0-9: alpha_flow, deriv_gain, th_start, th_end (5 = default)
constexpr double SENSITIVITY_PRESETS[10][4] = {
    {0.28, 0.06, 0.45, 0.30}, {0.26, 0.08, 0.42, 0.28}, {0.24, 0.10, 0.40, 0.26},
    {0.22, 0.12, 0.38, 0.24}, {0.20, 0.12, 0.36, 0.22}, {0.18, 0.12, 0.35, 0.20},
    {0.16, 0.14, 0.33, 0.20}, {0.14, 0.16, 0.31, 0.18}, {0.12, 0.18, 0.29, 0.16},
    {0.10, 0.20, 0.27, 0.14},
};

// Thermistor (10k from PIN_THERM_POWER to A0, NTC from A0 to GND); readings are ratiometric
constexpr float R_REF = 10000.0f;
constexpr float R0 = 10000.0f;
constexpr float BETA = 3435.0f;      // Set to your bead's B value
constexpr float T0_C = 25.0f;
constexpr int ADC_BITS = 12;
constexpr float THERM_UNPLUGGED_FRAC = 0.97f;  // Reading above this fraction of full scale = no thermistor

// ---------------------------------------------------------------- nose clip wear detection (v2)
constexpr float NOSE_WARM_C = 28.0f;        // Bead this warm (in the nostril, ~30-34 C) ...
constexpr float NOSE_COOL_C = 26.5f;        // ... and below this it's off the nose (hysteresis)
constexpr float NOSE_RHYTHM_S = 12.0f;      // ... and a breath phase change within this long

// ---------------------------------------------------------------- pulse (MAX3010x, v1 values)
constexpr uint8_t MAX3010X_IR_CURRENT = 0x2F;   // 0.2 mA steps (9.4 mA); raise for head sites
constexpr uint8_t MAX3010X_RED_CURRENT = 0x01;
constexpr uint32_t MAX3010X_SKIN_LEVEL = 50000;
constexpr float MAX3010X_MIN_AMP = 40.0f;
constexpr float PULSE_FILTER_HZ = 3.0f;
constexpr int32_t PULSE_MIN_IBI_MS = 400;
constexpr int32_t PULSE_MAX_IBI_MS = 2000;
constexpr int32_t PULSE_SIGNAL_TIMEOUT_MS = 2500;
constexpr float PULSE_REGULARITY = 0.2f;
constexpr int PULSE_MIN_RHYTHM = 3;
constexpr float PULSE_AMP_CONSISTENCY = 0.55f;
constexpr float PULSE_LOCK_WINDOW = 0.25f;
constexpr int32_t PULSE_SAMPLE_MS = 10;        // MAX3010x at 100 samples/s

// Display rhythm
constexpr float HEART_PHASE_WINDOW = 0.25f;
constexpr float HEART_PHASE_GAIN = 0.2f;
constexpr float HEART_RATE_EASE = 0.15f;
constexpr float HEART_RATE_GAIN = 0.05f;
constexpr float HEART_MAX_RATE_STEP = 0.03f;
constexpr float HEART_COAST_S = 8.0f;

// Heart stress (LEDs: 70% rate, 30% HRV, as v1)
constexpr float HEART_STRESS_SD = 4.0f;
constexpr float HEART_STRESS_BPM_START = 20.0f;
constexpr float HEART_STRESS_BPM_MIN = 10.0f;
constexpr float HEART_STRESS_BPM_MAX = 30.0f;
constexpr float HEART_SCALE_DOWN = 0.002f;
constexpr float HEART_SCALE_UP = 0.0002f;
constexpr float HEART_STRESS_SMOOTH = 0.1f;
constexpr float HEART_BASELINE_DOWN = 0.03f;
constexpr float HEART_BASELINE_UP = 0.001f;
constexpr int HRV_BEATS = 30;
constexpr int HRV_MIN_BEATS = 15;
constexpr float HRV_MAX_DEV = 0.2f;
constexpr float HEART_HRV_WEIGHT = 0.3f;
constexpr float HEART_HRV_BASELINE = 0.002f;
constexpr float HEART_STRESS_HRV_DROP = 0.5f;

// ---------------------------------------------------------------- stress fusion for the app (v2)
constexpr float FUSE_HEART = 0.6f;      // Combined = heart and breath when the nose clip is worn
constexpr float FUSE_BREATH = 0.4f;
constexpr float FUSE_HR = 0.5f;         // Heart part of the combined score: rate vs HRV
constexpr float FUSE_HRV = 0.5f;

// ---------------------------------------------------------------- LEDs
// LEDs per side. v3 frame: 5 along the front's top bar, index 0 = outer end (DIN, by the hinge), 4 = inner
// end (toward the nose). v2 temple strips: 10, index 0 = back (DIN, at the temple), 9 = front flap. Build
// a v2 headset (and the host tests, which compare with v1's 10-LED Python) with -DLED_STRIP_LEN=10.
// "Back"/"front" below mean outer/inner on v3.
#ifndef LED_STRIP_LEN
#define LED_STRIP_LEN 5
#endif
static_assert(LED_STRIP_LEN == 5 || LED_STRIP_LEN == 10, "LED_STRIP_LEN: 5 (v3) or 10 (v2)");
constexpr int STRIP_LEN = LED_STRIP_LEN;
constexpr int NUM_PIXELS = STRIP_LEN;
constexpr uint8_t LED_BRIGHTNESS = 26;  // v1's 0.1
constexpr float HEART_MIN_FILL = STRIP_LEN / 2.0f;   // LEDs filled at rest (full stress: all)
constexpr float HEART_COUNTER_BEAT = 0.55f;

struct Rgb { uint8_t r, g, b; };
constexpr Rgb HEART_CALM_COLOR = {0, 255, 40};
constexpr Rgb HEART_MID_COLOR = {255, 170, 0};
constexpr Rgb HEART_HOT_COLOR = {255, 0, 0};
constexpr Rgb DEPTH_COLORS[5] = {
    {255, 0, 0}, {150, 150, 150}, {0, 160, 160}, {110, 0, 160}, {0, 0, 180},
};
// Breath bar's start (front-most) LED by depth colour: calm breaths stay off the front LEDs
// (5 LEDs: 4/4/3/2/2, off the front one or two; 10 LEDs: 9/8/6/5/5, off the front four)
constexpr int BREATH_START_BY_DEPTH[5] = {STRIP_LEN == 5 ? 4 : 9, STRIP_LEN == 5 ? 4 : 8, STRIP_LEN == 5 ? 3 : 6,
                                          STRIP_LEN == 5 ? 2 : 5, STRIP_LEN == 5 ? 2 : 5};
constexpr double BREATH_DEBOUNCE_S = 0.35;   // double: 0.35f is just under 0.35, a sample early

// ---------------------------------------------------------------- BLE rates
constexpr uint32_t BREATH_TX_MS = 100;  // B at 10 Hz
constexpr uint32_t HEART_TX_MS = 40;    // H at 25 Hz
constexpr uint32_t SCORES_TX_MS = 1000; // K at 1 Hz
constexpr uint32_t BATTERY_TX_MS = 10000;

// ---------------------------------------------------------------- power
constexpr uint32_t BATTERY_SAMPLE_MS = 2000;
constexpr float BATTERY_MIN_V = 2.8f;
constexpr float LED_CUTOFF_V = 3.6f;    // LEDs off below this (SK6805 rated 3.7-5.5 V)
constexpr float LED_WARN_V = 3.75f;
constexpr int LOW_READINGS_TO_CUT = 5;     // Consecutive low readings (2 s apart) before the cut-off
constexpr uint32_t LOW_WARN_EVERY_MS = 30000;
constexpr uint32_t AUTO_SLEEP_MS = 120000;     // No breath and no pulse this long (not connected)
constexpr uint32_t WAKE_GRACE_MS = 30000;      // After waking, sleep again if nothing within this
constexpr uint32_t SLEEP_WARN_MS = 5000;       // "Auto sleep coming": three dim swells over the last 5 s
constexpr uint32_t CHARGE_SHOW_AFTER_MS = 10000;   // On USB with nothing sensed this long, show charging
constexpr float CHARGE_FULL_V = 4.15f;         // On USB at or above this: full (steady dim green)
constexpr uint32_t BUTTON_LONG_MS = 1200;
constexpr uint32_t BUTTON_DEBOUNCE_MS = 30;
constexpr uint32_t SAVE_STATE_EVERY_MS = 300000;  // Heart baselines to flash every 5 min
constexpr uint32_t WATCHDOG_S = 8;
