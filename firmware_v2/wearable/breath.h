// breath.h - Breath phases from the nose thermistor, and per-breath metrics.
//
// Literal port of firmware/breath_detector.py and breath_metrics.py. Pure C++: the caller supplies
// each temperature sample and the time, so it builds and is tested on a computer too.

#pragma once

#include <stdint.h>

enum BreathPhase : uint8_t { PH_IDLE = 0, PH_INH = 1, PH_EXH = 2 };

// Raw metrics of the last valid breath (breath_metrics.py)
class BreathMetrics {
 public:
  int breath_count = 0;
  bool is_calibrating = true;
  int calibration_breaths = 6;
  float last_exhale = 0, last_inhale = 0, last_cycle = 0;
  int last_smoothness = 100;
  float last_peak_flow = 0;
  int last_symmetry = 50;

  void reset();
  void start_exhale() { n_ = 0; }
  void record_sample(float flow) { if (n_ < kMax) samples_[n_++] = flow; }
  // Returns true if the breath was valid and the metrics were updated
  bool end_exhale(float exhale_s, float inhale_s);

 private:
  static constexpr int kMax = 50;
  float samples_[kMax];
  int n_ = 0;
  int smoothness() const;
  float peak_flow() const;
  int symmetry() const;
};

class BreathDetector {
 public:
  BreathDetector();
  void apply_sensitivity(int preset);
  void apply_color_thresholds(float very_short, float short_, float medium, float long_);
  int depth_color() const;            // From the last exhale's length
  // One 100 Hz sample. now_s: the time this batch is processed (v1 uses the same `now` for every
  // catch-up sample). Returns true on a phase change; new_breath is set when a valid breath ends.
  bool process(double temp_c, double now_s);

  BreathPhase phase = PH_IDLE;
  double norm = 0;                    // Normalised flow, inhale positive
  double flow_lp = 0;
  double last_exhale = 2.0, last_inhale = 2.0;   // Seconds (double, as v1's timing)
  bool unworn = false;
  bool new_breath = false;            // A valid breath just completed (read and clear)
  double last_transition_s = -1e9;    // For wear detection
  BreathMetrics metrics;

 private:
  void record_exhale(float duration_s);
  double t_fast_ = 0, t_slow_ = 0, prev_flow_ = 0;
  double scale_ex_ = 0.10, scale_in_ = 0.10, peak_ex_ = 0.10, peak_in_ = 0.10;
  double t_phase_start_ = 0, refrac_until_ = 0, idle_hold_start_ = -1;
  double exhale_start_ = -1, inhale_start_ = -1;
  double peak_val_ = 0, prev_norm_ = 0;
  int short_streak_ = 0;
  float very_short_max_, short_max_, medium_max_, long_max_;
  double alpha_flow_, deriv_gain_, th_start_, th_end_;
};
