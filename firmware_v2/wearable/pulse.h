// pulse.h - Heartbeats, steady display rhythm, HRV and heart stress from MAX3010x IR samples.
//
// Literal port of firmware/pulse_detector.py (MAX3010x path only; v2 has no analog sensor). Pure
// C++: the caller passes samples (oldest first, 10 ms apart) and the time in ms.
// v2 additions: the rate and HRV parts of stress are kept apart (the LEDs mix them 70/30 as v1,
// the app's combined score 50/50), and the learned baselines can be saved and restored.

#pragma once

#include <stdint.h>

#include "config.h"

struct HeartBaselines {      // What's saved to flash
  float baseline_bpm = 0;
  float rise_avg = 0;
  float baseline_hrv = 0;
};

class PulseDetector {
 public:
  PulseDetector();
  // New IR samples from the sensor; skin: the sensor's skin-contact flag
  void feed(const uint32_t* samples, int n, uint32_t now_ms, bool skin);
  void tick(uint32_t now_ms);     // Call every loop, after feed()
  void reset_signal();            // Sensing paused or sensor off

  float rhythm_bpm() const { return r_ibi_ > 0 ? 60000.0f / r_ibi_ : 0.0f; }
  float normalized() const;       // Live waveform for the app: trough -1, typical peak +1
  bool worn() const { return worn_; }

  HeartBaselines baselines() const;
  void restore(const HeartBaselines& b);

  // Outputs
  float value = 0, bpm = 0, beat_strength = 0.5f, beat_amp = 0;
  float env_amp = 0;              // Signal's swing (envelope high - low); beats need MAX3010X_MIN_AMP
  uint32_t beat_count = 0;
  bool beat_confirmed = false;
  uint32_t rhythm_count = 0;      // Increments on every shown beat
  float hrv_ms = 0;
  float stress = 0;               // LED stress 0..1 (70% rate, 30% HRV)
  float rate_stress = 0;          // Rate part 0..1
  float hrv_stress = 0;           // HRV part 0..1 (valid when hrv_ms > 0)
  float stress_bpm;
  float baseline_bpm = 0, baseline_hrv = 0;

 private:
  void process(float raw, uint32_t now, float dt);
  void on_rise(uint32_t now);
  void on_peak(uint32_t now);
  void fiducial(int32_t& k, float& frac) const;
  void hrv_beat();
  void rhythm_on_beat(uint32_t now);
  void tick_rhythm(uint32_t now);
  void update_stress();
  bool amps_consistent() const;
  float median_ibi() const;
  void add_ibi(float ibi);
  void unlock();
  void lose_signal();
  float level() const;

  static constexpr int kIbiHistory = 5;
  static constexpr int kHist = 64;

  bool primed_ = false, worn_ = true;
  float offset_ = 0, lp_ = 0, dc_ = 0, dc2_ = 0, env_hi_ = 0, env_lo_ = 0;
  bool armed_ = true, in_beat_ = false;
  float beat_max_ = 0, cycle_min_ = 0;
  bool have_rise_ = false;
  uint32_t last_rise_ms_ = 0;
  float ibis_[kIbiHistory];
  int n_ibis_ = 0;
  float amp_ref_ = 0;
  int amp_beats_ = 0;
  float amps_[kIbiHistory];
  int n_amps_ = 0;
  float locked_ibi_ = 0;
  bool rise_regular_ = false;

  float r_ibi_ = 0;
  uint32_t r_next_ms_ = 0, r_support_ms_ = 0;

  int32_t n_ = 0;
  float hist_[kHist];
  int32_t rise_n_ = 0;
  bool have_fid_ = false;
  int32_t fid_k_ = 0;
  float fid_frac_ = 0;
  bool have_last_iv_ = false;
  float last_iv_ = 0;
  float sq_diffs_[HRV_BEATS];
  int n_sq_ = 0;

  float hr_avg_ = 0, rise_avg_;

};
