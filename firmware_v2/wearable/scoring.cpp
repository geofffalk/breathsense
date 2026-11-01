// scoring.cpp - see scoring.h. MoodAnalyzer follows mood_analyzer.dart step for step.

#include "scoring.h"

#include <math.h>
#include <string.h>

#include "config.h"

static inline float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }
static inline int clampi(int x, int lo, int hi) { return x < lo ? lo : (x > hi ? hi : x); }

template <typename T>
static void push(T* arr, int& n, int cap, T v) {
  if (n == cap) { memmove(arr, arr + 1, sizeof(T) * (cap - 1)); n--; }
  arr[n++] = v;
}

void MoodAnalyzer::reset() {
  n_recent_ = n_diffs_ = 0;
  have_last_cycle_ = false;
  breath_count_ = 0;
  stress = 0;
  focus = 5;
  meditation = 0;
  baseline_locked_ = false;
  baseline_cycle_ = baseline_peak_ = 0;
}

void MoodAnalyzer::record_breath(float exhale, float inhale, float cycle, int smoothness,
                                 float peak_flow) {
  if (exhale < 0.3f || inhale < 0.2f) return;
  if (exhale > 15.0f || inhale > 10.0f) return;
  breath_count_++;
  if (n_recent_ == kMaxRecent) {   // Drop the oldest breath from all three
    memmove(cycles_, cycles_ + 1, sizeof(float) * (kMaxRecent - 1));
    memmove(ratios_, ratios_ + 1, sizeof(float) * (kMaxRecent - 1));
    memmove(peaks_, peaks_ + 1, sizeof(float) * (kMaxRecent - 1));
    n_recent_--;
  }
  cycles_[n_recent_] = cycle;
  ratios_[n_recent_] = inhale > 0 ? exhale / inhale : 1.0f;
  peaks_[n_recent_] = peak_flow;
  n_recent_++;

  if (have_last_cycle_) push(diffs_, n_diffs_, kMaxDiffs, fabsf(cycle - last_cycle_));
  last_cycle_ = cycle;
  have_last_cycle_ = true;

  // Baseline from the calibration breaths, then drifting 2% per breath
  if (!baseline_locked_ && breath_count_ == s.calibration_breaths && n_recent_ > 0) {
    float c = 0, p = 0;
    for (int i = 0; i < n_recent_; i++) { c += cycles_[i]; p += peaks_[i]; }
    baseline_cycle_ = c / n_recent_;
    baseline_peak_ = p / n_recent_;
    baseline_locked_ = true;
  } else if (baseline_locked_) {
    const float a = 0.02f;
    baseline_cycle_ = baseline_cycle_ * (1 - a) + cycle * a;
    if (peak_flow > 0) baseline_peak_ = baseline_peak_ * (1 - a) + peak_flow * a;
  }

  update_metrics();
  compute_stress(smoothness, peak_flow);
  compute_focus();
  compute_meditation();
}

void MoodAnalyzer::update_metrics() {
  if (!n_recent_) return;
  float r = 0;
  for (int i = 0; i < n_recent_; i++) r += ratios_[i];
  ratio_ = r / n_recent_;
  if (n_diffs_ >= 2) {
    float q = 0;
    for (int i = 0; i < n_diffs_; i++) q += diffs_[i] * diffs_[i];
    rmssd_ = sqrtf(q / n_diffs_);
  }
  float mean = 0;
  for (int i = 0; i < n_recent_; i++) mean += cycles_[i];
  mean /= n_recent_;
  if (n_recent_ >= 2) {
    float v = 0;
    for (int i = 0; i < n_recent_; i++) v += (cycles_[i] - mean) * (cycles_[i] - mean);
    consistency_ = sqrtf(v / n_recent_);
  }
  cycle_ = mean;
}

void MoodAnalyzer::compute_stress(int smoothness, float peak_flow) {
  float ratio_norm = (ratio_ - kAnxiousRatio) / fmaxf(0.1f, s.calm_ratio - kAnxiousRatio);
  float ratio_score = clampf(5 - ratio_norm * 10, -5, 5);

  float duration_score = 0;
  if (baseline_locked_) {
    float dr = cycle_ / fmaxf(0.1f, baseline_cycle_);
    duration_score = clampf(-((dr - 1.0f) / 0.3f) * 5, -5, 5);
  }
  float smooth_score = clampf(5 - smoothness / 10.0f, -5, 5);
  float peak_score = 0;
  if (baseline_locked_ && baseline_peak_ > 0 && peak_flow > 0)
    peak_score = clampf((peak_flow / baseline_peak_ - 1.0f) * 5, -5, 5);

  float rmssd_cv = rmssd_ / fmaxf(0.1f, cycle_);
  float rmssd_norm = (rmssd_cv - s.calm_variability) / fmaxf(0.01f, kAnxiousVariabilityCv - s.calm_variability);
  float rmssd_score = clampf(-5 + rmssd_norm * 10, -5, 5);

  float short_penalty = cycle_ < 3.0f ? 3.0f : (cycle_ < 4.0f ? 2.0f : (cycle_ < 5.0f ? 1.0f : 0.0f));

  float raw = s.w_ratio * ratio_score + s.w_duration * duration_score + s.w_smoothness * smooth_score +
              s.w_peak * peak_score + s.w_rmssd * rmssd_score + short_penalty;
  stress = clampi((int)lroundf(raw), -5, 5);
}

void MoodAnalyzer::compute_focus() {
  float cv = consistency_ / fmaxf(0.1f, cycle_);
  float norm = (cv - s.focus_consistency) / fmaxf(0.01f, 0.30f - s.focus_consistency);
  focus = clampi((int)lroundf(10 - norm * 10), 0, 10);
}

void MoodAnalyzer::compute_meditation() {
  float d;
  if (cycle_ < kMedMinCycle) d = 0;
  else if (cycle_ >= kMedOptimalCycle) d = 10;
  else d = 10 * (cycle_ - kMedMinCycle) / (kMedOptimalCycle - kMedMinCycle);
  float cv = consistency_ / fmaxf(0.1f, cycle_);
  float m;
  if (cv <= kMedStability) m = 1.0f;
  else if (cv >= 0.4f) m = 0.5f;
  else m = 1.0f - ((cv - kMedStability) / 0.25f) * 0.5f;
  meditation = clampi((int)lroundf(d * m), 0, 10);
}

// ---------------------------------------------------------------- nose wear

void NoseWear::update(bool plugged_in, float temp_c, double last_transition_s, double now_s) {
  plugged = plugged_in;
  if (!plugged) { warm_ = false; worn = false; return; }
  if (warm_) warm_ = temp_c > NOSE_COOL_C;
  else warm_ = temp_c > NOSE_WARM_C;
  worn = warm_ && (now_s - last_transition_s) < NOSE_RHYTHM_S;
}

// ---------------------------------------------------------------- fusion

Scores fuse(const FuseWeights& w, bool heart_valid, float rate_k, bool hrv_valid, float hrv_k,
            bool heart_worn, const MoodAnalyzer& mood, bool nose_worn) {
  Scores out;
  out.heart_worn = heart_worn;
  out.nose_worn = nose_worn;
  out.focus = mood.focus;
  out.meditation = mood.meditation;

  float heart = 0;
  if (heart_valid) {
    float tw = w.hr + (hrv_valid ? w.hrv : 0);
    heart = tw > 0 ? (w.hr * rate_k + (hrv_valid ? w.hrv * hrv_k : 0)) / tw : rate_k;
  }
  bool breath_valid = nose_worn && !mood.calibrating();
  float breath = (mood.stress + 5) / 10.0f;   // -5..+5 -> 0..1

  out.heart_stress = heart_valid ? (int)lroundf(heart * 100) : 0;
  out.breath_stress = breath_valid ? (int)lroundf(breath * 100) : 0;

  float combined;
  if (heart_valid && breath_valid) {
    float tw = w.heart + w.breath;
    combined = tw > 0 ? (w.heart * heart + w.breath * breath) / tw : heart;
  } else if (heart_valid) {
    combined = heart;
  } else if (breath_valid) {
    combined = breath;
  } else {
    combined = 0;
  }
  out.stress = (int)lroundf(clampf(combined, 0, 1) * 100);
  out.calibrating = !heart_valid && !breath_valid;
  return out;
}
