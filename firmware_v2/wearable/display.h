// display.h - What the LEDs show, as 10-LED frames (index 0 = back, 9 = front). Both sides mirror.
//
// HeartDisplay is v1's HeartbeatLED unchanged. BreathDisplay is v1's OpenBreathingLED motion
// (in-breath lights the bar's front LED, out-breath runs a comet back over the predicted exhale
// length) with the v2 rule that the bar's front is set by the exhale colour, so calm breaths stay
// off the front 4 LEDs. Pure C++.

#pragma once

#include <stdint.h>

#include "breath.h"
#include "config.h"
#include "pulse.h"

struct RgbF { float r, g, b; };

struct Frame {
  Rgb px[STRIP_LEN];
  void clear() { for (auto& p : px) p = {0, 0, 0}; }
  bool operator==(const Frame& o) const;
};

class HeartDisplay {
 public:
  void reset(const PulseDetector& p) { seen_ = p.rhythm_count; active_ = false; }
  void tick(const PulseDetector& p, uint32_t now_ms, Frame& f);
 private:
  uint32_t seen_ = 0, beat_ms_ = 0;
  bool active_ = false;
  float reach_ = 0, time_scale_ = 1;
  RgbF color_ = {0, 0, 0};
};

class BreathDisplay {
 public:
  // Draws into f, which the caller keeps between calls: like v1, some states leave the last frame up
  void tick(const BreathDetector& d, double now_s, Frame& f);
 private:
  BreathPhase last_ = PH_IDLE, pending_ = PH_IDLE;
  double stable_since_ = 0;
  double exhale_start_ = -1;
  double exhale_pred_ = 2.0;
  bool locked_ = false;
  int start_ = 9;            // Front-most LED for this breath
 public:
  int start_by_depth[5] = {BREATH_START_BY_DEPTH[0], BREATH_START_BY_DEPTH[1], BREATH_START_BY_DEPTH[2],
                           BREATH_START_BY_DEPTH[3], BREATH_START_BY_DEPTH[4]};
 private:
  Frame hold_;               // What the in-breath shows until the exhale starts
  bool holding_ = false;
  void render_exhale(double now, int depth, Frame& f);
};

// Short animations (comets, swells) for wake, sleep, connect, mode change, warnings
void comet_frame(Rgb color, float progress, bool back_to_front, Frame& f);
