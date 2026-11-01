// scoring.h - Breath mood scores (ported from the app), nose clip wear detection, and the
// combined stress score sent to the app.
//
// MoodAnalyzer is lib/services/mood_analyzer.dart unchanged, with the app settings' defaults
// (lib/models/settings.dart). Pure C++.

#pragma once

#include <stdint.h>

struct MoodSettings {          // Set by S,M (weights are its optional trailing fields)
  float calm_ratio = 1.5f;
  float calm_variability = 0.10f;
  float focus_consistency = 0.15f;
  int calibration_breaths = 6;
  float w_ratio = 0.35f, w_duration = 0.20f, w_smoothness = 0.15f, w_peak = 0.15f, w_rmssd = 0.15f;
};

class MoodAnalyzer {
 public:
  MoodSettings s;
  void record_breath(float exhale, float inhale, float cycle, int smoothness, float peak_flow);
  void reset();
  bool calibrating() const { return breath_count_ < s.calibration_breaths; }
  int stress = 0;       // -5 (serene) .. +5 (anxious)
  int focus = 5;        // 0..10
  int meditation = 0;   // 0..10

 private:
  static constexpr int kMaxRecent = 10, kMaxDiffs = 4;
  float cycles_[kMaxRecent], ratios_[kMaxRecent], peaks_[kMaxRecent];
  int n_recent_ = 0;
  float diffs_[kMaxDiffs];
  int n_diffs_ = 0;
  bool have_last_cycle_ = false;
  float last_cycle_ = 0;
  int breath_count_ = 0;
  bool baseline_locked_ = false;
  float baseline_cycle_ = 0, baseline_peak_ = 0;
  float ratio_ = 1.0f, rmssd_ = 1.0f, cycle_ = 4.0f, consistency_ = 0.5f;
  // Constants the app doesn't expose
  static constexpr float kAnxiousRatio = 0.8f, kAnxiousVariabilityCv = 0.40f;
  static constexpr float kMedMinCycle = 6.0f, kMedOptimalCycle = 10.0f, kMedStability = 0.15f;
  void update_metrics();
  void compute_stress(int smoothness, float peak_flow);
  void compute_focus();
  void compute_meditation();
};

// Is the nose clip on the nose? Plugged in (reading below full scale), the bead warm, and a breath
// rhythm recently.
class NoseWear {
 public:
  void update(bool plugged, float temp_c, double last_transition_s, double now_s);
  bool worn = false;
  bool plugged = false;
 private:
  bool warm_ = false;
};

struct FuseWeights {           // Set by S,W
  float heart = 0.6f, breath = 0.4f, hr = 0.5f, hrv = 0.5f;
};

struct Scores {                // The K message
  int stress = 0;              // 0..100 combined
  int focus = 5, meditation = 0;
  int heart_stress = 0, breath_stress = 0;   // 0..100 each
  bool nose_worn = false, heart_worn = false, calibrating = true;
};

// heart_valid: the display rhythm is running; hrv_valid: hrv_ms > 0
Scores fuse(const FuseWeights& w, bool heart_valid, float rate_k, bool hrv_valid, float hrv_k,
            bool heart_worn, const MoodAnalyzer& mood, bool nose_worn);
