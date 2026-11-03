// app.cpp - GlassesSense v2 firmware (Arduino C++, XIAO nRF52840 Plus). wearable.ino only calls
// app_setup() and app_loop(): keeping the code in a .cpp avoids the Arduino builder's generated
// prototypes (default arguments, [[noreturn]] statics).
//
// Behaviour: hardware/v2/README.md, "Behaviour specification". Ported from the v1 CircuitPython
// firmware in firmware/ (written for the ItsyBitsy nRF52840), which stays the reference for the
// detectors and displays.
//
// Modes: heart (default), breath, off. Standalone, the button switches heart/breath (short press)
// and sleeps (long press); it wakes in the last mode. Connected, the app can set any mode;
// connecting changes nothing and the headset reports its mode (M). All scores are computed here
// and sent as K; the app only displays them.
//
// Libraries: Adafruit nRF52 core (Bluefruit, InternalFileSystem, Wire) or Seeed's nRF52 core for
// the XIAO; Adafruit_NeoPixel from the Library Manager.

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <bluefruit.h>

#include "breath.h"
#include "config.h"
#include "display.h"
#include "hw.h"
#include "max3010x.h"
#include "protocol.h"
#include "pulse.h"
#include "scoring.h"
#include "storage.h"

// ---------------------------------------------------------------- objects
static Adafruit_NeoPixel strip_l(NUM_PIXELS, PIN_LED_LEFT, NEO_GRB + NEO_KHZ800);
static Adafruit_NeoPixel strip_r(NUM_PIXELS, PIN_LED_RIGHT, NEO_GRB + NEO_KHZ800);
static BLEUart bleuart;
static Max3010x sensor;

static BreathDetector breath;
static PulseDetector pulse;
static MoodAnalyzer mood;
static NoseWear nose;
static HeartDisplay heart_display;
static BreathDisplay breath_display;

static Settings settings;
static State state;
static Mode mode = MODE_HEART;

// ---------------------------------------------------------------- runtime state
static volatile bool connected = false, just_connected = false, just_disconnected = false;
static char rx_line[128];
static size_t rx_len = 0;
static Frame frame, shown;
static bool leds_powered = false;
static uint32_t dark_since = 0;
static float battery_v = 0;
static bool usb = false;
static uint32_t t_breath_next = 0, t_breath_tx = 0, t_heart_tx = 0, t_scores_tx = 0;
static uint32_t t_battery = 0, t_battery_tx = 0, t_low_warn = 0, t_save = 0;
static uint32_t last_activity = 0, woke_at = 0;
static bool any_activity_since_wake = false;
static bool button_was_down = false, long_fired = false;
static bool ignore_until_release = true;   // The press that woke the board isn't a command
static uint32_t button_down_at = 0;
static bool state_dirty = false;
static int low_readings = 0;       // Consecutive readings under the cut-off
static uint32_t t_debug = 0;
static uint32_t last_ir = 0;   // Latest raw IR reading, for the debug line

static inline double now_s() { return millis() / 1000.0; }
static inline bool sensing() { return mode != MODE_OFF; }

// ---------------------------------------------------------------- LEDs

static void leds_show(const Frame& f, bool force = false) {
  bool lit = false;
  for (const auto& p : f.px) if (p.r || p.g || p.b) { lit = true; break; }
  uint32_t now = millis();
  if (lit) {
    dark_since = 0;
    if (!leds_powered) {
      hw::led_power(true);
      leds_powered = true;
      strip_l.begin();   // Re-take the data pins after the switch drove them low
      strip_r.begin();
      delay(1);
      force = true;
    }
  } else if (!dark_since) {
    dark_since = now ? now : 1;
  }
  if (leds_powered && (force || !(f == shown))) {
    for (int i = 0; i < STRIP_LEN; i++) {
      strip_l.setPixelColor(i, f.px[i].r, f.px[i].g, f.px[i].b);
      strip_r.setPixelColor(i, f.px[i].r, f.px[i].g, f.px[i].b);
    }
    strip_l.show();
    strip_r.show();
    shown = f;
  }
  // Cut LED power once dark for a while (each pixel draws ~1 mA showing black)
  if (!lit && leds_powered && dark_since && now - dark_since > 2000) {
    hw::led_power(false);
    leds_powered = false;
  }
}

static void leds_dark() {
  Frame f;
  f.clear();
  leds_show(f, true);
}

// Short blocking animations (under ~1.5 s; the watchdog allows 8 s)
static void play_comet(Rgb c, uint32_t ms, bool back_to_front) {
  const int steps = 15;
  Frame f;
  for (int s = 0; s <= steps; s++) {
    comet_frame(c, (float)s / steps, back_to_front, f);
    leds_show(f);
    delay(ms / steps);
  }
  leds_dark();
}

static void play_pulses(Rgb c, int n) {   // Mode change: 1 heart, 2 breath
  Frame f;
  for (int k = 0; k < n; k++) {
    f.clear();
    for (int i = 0; i < 4; i++) f.px[i] = c;
    leds_show(f);
    delay(140);
    leds_dark();
    delay(160);
  }
}

static void play_flashes(Rgb c, int n) {
  Frame f;
  for (int k = 0; k < n; k++) {
    f.clear();
    for (auto& p : f.px) p = c;
    leds_show(f);
    delay(200);
    leds_dark();
    delay(200);
  }
}

static void blip(Rgb c) {
  Frame f = shown;
  f.px[STRIP_LEN - 1] = c;
  leds_show(f, true);
  delay(120);
  leds_show(shown, true);
}

// ---------------------------------------------------------------- BLE

static void send(const char* buf, int len) {
  if (connected && len > 0) bleuart.write((const uint8_t*)buf, len);
}

static void send_mode() {
  char b[16];
  send(b, proto::fmt_mode(b, sizeof(b), mode));
}

static void send_settings() {
  char b[200];
  send(b, proto::fmt_settings(b, sizeof(b), settings));
}

static void send_battery() {
  char b[32];
  send(b, proto::fmt_battery(b, sizeof(b), (int)(battery_v * 1000), hw::battery_percent(battery_v), usb));
}

static void on_connect(uint16_t conn) {
  BLEConnection* c = Bluefruit.Connection(conn);
  if (c) c->requestMtuExchange(247);
  connected = true;
  just_connected = true;
}

static void on_disconnect(uint16_t, uint8_t) {
  connected = false;
  just_disconnected = true;
}

static void ble_begin() {
  Bluefruit.configPrphBandwidth(BANDWIDTH_MAX);
  Bluefruit.begin();
  Bluefruit.setTxPower(4);
  char name[32];
  snprintf(name, sizeof(name), "%s-%04lX", DEVICE_NAME_PREFIX, (unsigned long)hw::chip_id16());
  Bluefruit.setName(name);
  Bluefruit.Periph.setConnectCallback(on_connect);
  Bluefruit.Periph.setDisconnectCallback(on_disconnect);
  bleuart.begin();
  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.Advertising.addService(bleuart);
  Bluefruit.ScanResponse.addName();
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(160, 800);   // 100 ms fast, then 500 ms
  Bluefruit.Advertising.setFastTimeout(30);
  Bluefruit.Advertising.start(0);
}

// ---------------------------------------------------------------- modes

static void apply_settings() {
  breath.apply_color_thresholds(settings.very_short_max, settings.short_max, settings.medium_max,
                                settings.long_max);
  breath.apply_sensitivity(settings.sensitivity);
  mood.s = settings.mood;
  breath.metrics.calibration_breaths = settings.mood.calibration_breaths;
}

static void set_mode(Mode m, bool announce) {
  if (m == mode) {
    send_mode();
    return;
  }
  bool was_sensing = sensing();
  static const char* const NAMES[] = {"heart", "breath", "off"};
  if (Serial) Serial.printf("mode: %s -> %s\n", NAMES[mode], NAMES[m]);
  mode = m;
  if (sensing() && !was_sensing) {      // Resume sensing
    hw::therm_power(true);
    sensor.shutdown(false);
  } else if (!sensing() && was_sensing) {   // App off: LEDs dark, sensing paused, BLE stays on
    hw::therm_power(false);
    sensor.shutdown(true);
    pulse.reset_signal();
  }
  if (m == MODE_HEART) heart_display.reset(pulse);
  if (m != MODE_OFF) {
    state.last_mode = m;
    state_dirty = true;
  }
  leds_dark();
  if (announce && m != MODE_OFF) play_pulses(m == MODE_HEART ? HEART_CALM_COLOR : DEPTH_COLORS[2],
                                             m == MODE_HEART ? 1 : 2);
  send_mode();
}

static void save_state() {
  state.heart = pulse.baselines();
  storage::save(state);
  state_dirty = false;
}

[[noreturn]] static void go_to_sleep(Rgb sweep) {
  save_state();
  play_comet(sweep, 1000, true);   // Back to front, then dark
  sensor.shutdown(true);
  hw::system_off();
}

static void handle_command(const char* line) {
  proto::Command c = proto::parse(line);
  switch (c.type) {
    case proto::Command::MODE:
      set_mode(c.mode, true);
      break;
    case proto::Command::COLOR_THRESHOLDS:
      settings.very_short_max = c.f[0];
      settings.short_max = c.f[1];
      settings.medium_max = c.f[2];
      settings.long_max = c.f[3];
      apply_settings();
      storage::save(settings);
      break;
    case proto::Command::SENSITIVITY:
      settings.sensitivity = c.i;
      apply_settings();
      storage::save(settings);
      break;
    case proto::Command::MOOD: {
      MoodSettings& m = settings.mood;
      m.calm_ratio = c.f[0];
      m.calm_variability = c.f[1];
      m.focus_consistency = c.f[2];
      m.calibration_breaths = (int)c.f[3];
      if (c.count >= 9) {   // Optional component weights
        m.w_ratio = c.f[4]; m.w_duration = c.f[5]; m.w_smoothness = c.f[6]; m.w_peak = c.f[7]; m.w_rmssd = c.f[8];
      }
      apply_settings();
      storage::save(settings);
      break;
    }
    case proto::Command::WEIGHTS:
      settings.fuse.heart = c.f[0];
      settings.fuse.breath = c.f[1];
      settings.fuse.hr = c.f[2];
      settings.fuse.hrv = c.f[3];
      storage::save(settings);
      break;
    case proto::Command::LED:
      settings.led_enabled = c.i ? 1 : 0;
      if (!settings.led_enabled) leds_dark();
      storage::save(settings);
      break;
    case proto::Command::QUERY:
      send_settings();
      send_mode();
      break;
    default:
      break;
  }
}

static void handle_rx() {
  while (bleuart.available()) {
    int ch = bleuart.read();
    if (ch == '\n' || ch == '\r') {
      if (rx_len) {
        rx_line[rx_len] = 0;
        handle_command(rx_line);
        rx_len = 0;
      }
    } else if (rx_len < sizeof(rx_line) - 1 && ch >= 32 && ch <= 126) {
      rx_line[rx_len++] = (char)ch;
    }
  }
}

// ---------------------------------------------------------------- button

static void handle_button(uint32_t now) {
  bool down = hw::button_down();
  if (ignore_until_release) {
    if (!down) ignore_until_release = false;
    button_was_down = false;
    return;
  }
  if (down && !button_was_down) {
    button_down_at = now;
    long_fired = false;
  } else if (down && !long_fired && now - button_down_at >= BUTTON_LONG_MS) {
    long_fired = true;
    go_to_sleep({255, 255, 255});   // Long press: sleep
  } else if (!down && button_was_down && !long_fired && now - button_down_at >= BUTTON_DEBOUNCE_MS) {
    any_activity_since_wake = true;
    last_activity = now;
    if (mode == MODE_OFF) set_mode((Mode)state.last_mode, true);   // Back on, in the last mode
    else set_mode(mode == MODE_HEART ? MODE_BREATH : MODE_HEART, true);
  }
  button_was_down = down;
}

// ---------------------------------------------------------------- setup / loop

// Bring-up: with USB in, wait up to BOOT_LOG_WAIT_MS for the serial monitor, then log each start-up step,
// so a hang shows where it stopped
static void boot_log(const char* step) {
  if (Serial) {
    Serial.printf("boot %6lu ms: %s\n", (unsigned long)millis(), step);
    Serial.flush();
  }
}

void app_setup() {
  hw::begin();
  if (hw::usb_powered()) {
    uint32_t t0 = millis();
    while (!Serial && millis() - t0 < BOOT_LOG_WAIT_MS) delay(10);
  }
  boot_log(hw::reset_by_watchdog() ? "start (after a watchdog reset)" : "start");
  boot_log(hw::usb_powered() ? "USB power seen" : "USB power NOT seen");
  storage::begin();
  boot_log("flash storage ok");
  storage::load(settings);
  storage::load(state);
  if (state.last_mode > MODE_BREATH) state.last_mode = MODE_HEART;
  pulse.restore(state.heart);
  apply_settings();
  boot_log("settings loaded");

  strip_l.begin();
  strip_r.begin();
  strip_l.setBrightness(LED_BRIGHTNESS);
  strip_r.setBrightness(LED_BRIGHTNESS);

  if (hw::reset_by_watchdog()) {   // Recovered from a hang: one red blip, back to sleep
    blip({255, 0, 0});
    sensor.begin(MAX3010X_IR_CURRENT, MAX3010X_RED_CURRENT);
    sensor.shutdown(true);           // It isn't reset with the nRF, so would keep running
    hw::system_off();
  }

  boot_log("starting MAX30101 (I2C)");
  sensor.begin(MAX3010X_IR_CURRENT, MAX3010X_RED_CURRENT);
  boot_log(sensor.bus_stuck ? "I2C bus held low (SDA or SCL): MAX30101 skipped"
                           : sensor.present() ? "MAX30101 found" : "MAX30101 NOT found");
  hw::therm_power(true);
  boot_log("starting Bluetooth");
  ble_begin();
  boot_log("Bluetooth ok");

  mode = (Mode)state.last_mode;   // Wake in the last mode
  heart_display.reset(pulse);
  boot_log("wake comet");
  play_comet({255, 255, 255}, 800, false);   // Wake: soft white sweep, front to back
  woke_at = last_activity = millis();
  t_breath_next = millis();
  hw::watchdog_begin(WATCHDOG_S);
  boot_log("running");
}

void app_loop() {
  hw::watchdog_feed();
  uint32_t now = millis();

  // ---- connection events
  if (just_connected) {
    just_connected = false;
    play_comet({255, 100, 0}, 600, true);   // v1's orange connect comet; the mode doesn't change
    send_settings();
    send_battery();
    send_mode();
  }
  if (just_disconnected) {
    just_disconnected = false;
    blip({40, 40, 40});
    last_activity = now;
  }
  if (connected) handle_rx();
  handle_button(now);

  // ---- sensing (both run in heart and breath modes: the combined score needs both)
  if (sensing()) {
    while ((int32_t)(now - t_breath_next) >= 0) {   // Thermistor at 100 Hz, catching up
      t_breath_next += (uint32_t)(1000.0f / FS_HZ);
      float temp;
      bool plugged = hw::read_therm(temp);
      if (plugged && breath.process(temp, now_s())) {
        last_activity = now;
        any_activity_since_wake = true;
      }
      nose.update(plugged, temp, breath.last_transition_s, now_s());
    }
    if (breath.new_breath) {
      breath.new_breath = false;
      const BreathMetrics& m = breath.metrics;
      mood.record_breath(m.last_exhale, m.last_inhale, m.last_cycle, m.last_smoothness, m.last_peak_flow);
    }
    uint32_t samples[32];
    int n = sensor.read_ir(samples, 32);
    if (n > 0) last_ir = samples[n - 1];
    uint32_t beats_before = pulse.rhythm_count;
    pulse.feed(samples, n, now, sensor.present() ? sensor.skin : false);
    pulse.tick(now);
    if (pulse.rhythm_count != beats_before) {
      last_activity = now;
      any_activity_since_wake = true;
    }
  } else {
    t_breath_next = now;
  }

  // ---- battery
  if (now - t_battery >= BATTERY_SAMPLE_MS || !t_battery) {
    t_battery = now ? now : 1;
    float v = hw::battery_volts();
    battery_v = (v > 0) != (battery_v > 0) ? v : battery_v + 0.3f * (v - battery_v);
    usb = hw::usb_powered();
    low_readings = (battery_v > 0 && !usb && battery_v < LED_CUTOFF_V) ? low_readings + 1 : 0;
  }
  if (battery_v > 0 && !usb) {
    if (low_readings >= LOW_READINGS_TO_CUT) {   // Tell the app, three amber flashes, sleep until USB
      send_battery();
      play_flashes({255, 120, 0}, 3);
      go_to_sleep({255, 120, 0});
    }
    if (battery_v < LED_WARN_V && now - t_low_warn >= LOW_WARN_EVERY_MS) {
      t_low_warn = now;
      blip({255, 120, 0});
    }
  }

  // ---- LEDs
  // When auto sleep is due (never while connected or on USB)
  uint32_t sleep_at = last_activity + AUTO_SLEEP_MS;
  if (!any_activity_since_wake && woke_at + WAKE_GRACE_MS < sleep_at) sleep_at = woke_at + WAKE_GRACE_MS;
  bool may_sleep = !connected && !usb;
  int32_t ms_to_sleep = (int32_t)(sleep_at - now);
  bool idle = now - last_activity >= CHARGE_SHOW_AFTER_MS;

  if (mode == MODE_OFF || !settings.led_enabled) {
    frame.clear();
  } else if (may_sleep && ms_to_sleep <= (int32_t)SLEEP_WARN_MS) {
    // Auto sleep coming: three dim swells; breath, a pulse or the button cancels it (resets last_activity)
    sleep_warning_frame(ms_to_sleep > 0 ? (uint32_t)ms_to_sleep : 0, frame);
  } else if (usb && battery_v > 0 && idle) {
    charging_frame(now, battery_v >= CHARGE_FULL_V, frame);   // On USB with nothing sensed
  } else if (mode == MODE_HEART) {
    heart_display.tick(pulse, now, frame);
  } else {
    breath_display.tick(breath, now_s(), frame);
  }
  leds_show(frame);

  // ---- data to the app
  if (connected) {
    char b[160];
    if (mode == MODE_HEART && now - t_heart_tx >= HEART_TX_MS) {
      t_heart_tx = now;
      send(b, proto::fmt_heart(b, sizeof(b), now, pulse.normalized(), (int)(pulse.rhythm_bpm() + 0.5f),
                               pulse.rhythm_bpm() > 0, pulse.rhythm_count, (int)(pulse.stress * 100),
                               (int)(pulse.hrv_ms + 0.5f)));
    } else if (mode == MODE_BREATH && now - t_breath_tx >= BREATH_TX_MS) {
      t_breath_tx = now;
      send(b, proto::fmt_breath(b, sizeof(b), now, breath));
    }
    if (sensing() && now - t_scores_tx >= SCORES_TX_MS) {
      t_scores_tx = now;
      Scores k = fuse(settings.fuse, pulse.rhythm_bpm() > 0, pulse.rate_stress, pulse.hrv_ms > 0,
                      pulse.hrv_stress, pulse.worn() && sensor.present(), mood, nose.worn);
      send(b, proto::fmt_scores(b, sizeof(b), k));
    }
    if (now - t_battery_tx >= BATTERY_TX_MS) {
      t_battery_tx = now;
      send_battery();
    }
  }

  // ---- learned state to flash, every few minutes
  if (now - t_save >= SAVE_STATE_EVERY_MS) {
    t_save = now;
    save_state();
  } else if (state_dirty) {
    save_state();
  }

  // ---- auto sleep (never while the app is connected)
  if (may_sleep && ms_to_sleep <= 0) go_to_sleep({255, 255, 255});

  // ---- debug line over USB serial (for bring-up), once a second
  if (Serial && now - t_debug >= 1000) {   // Serial is only up with USB attached and a monitor open
    t_debug = now;
    float temp = 0;
    bool plugged = sensing() ? hw::read_therm(temp) : false;
    static const char* const NAMES[] = {"heart", "breath", "off"};
    Serial.printf("mode %s bat %.2fV usb %d | therm %s %.2fC nose %d | max %d ir %lu skin %d amp %.0f bpm %.0f "
                  "stress %.2f hrv %.0f | breaths %d phase %d | conn %d\n",
                  NAMES[mode], battery_v, usb, plugged ? "in" : "out", temp, nose.worn, sensor.present(),
                  (unsigned long)last_ir, sensor.skin, pulse.env_amp, pulse.rhythm_bpm(), pulse.stress, pulse.hrv_ms, breath.metrics.breath_count,
                  (int)breath.phase, connected);
  }

  delay(5);
}
