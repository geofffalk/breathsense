// breath.cpp - see breath.h. Mirrors breath_detector.py / breath_metrics.py line for line where it
// matters (the idle check before the refractory skip, IDLE_HOLD_S * 1.5, the phase-age rule).

#include "breath.h"

#include <math.h>

#include "config.h"

static constexpr double DT = 1.0 / FS_HZ;

// ---------------------------------------------------------------- metrics

void BreathMetrics::reset() {
  breath_count = 0;
  is_calibrating = true;
  last_exhale = last_inhale = last_cycle = 0;
  last_smoothness = 100;
  last_peak_flow = 0;
  last_symmetry = 50;
  n_ = 0;
}

bool BreathMetrics::end_exhale(float exhale_s, float inhale_s) {
  if (exhale_s < 0.3f || inhale_s < 0.2f) return false;   // Too short: artifact
  if (exhale_s > 15.0f || inhale_s > 10.0f) return false; // Too long: pause or hold
  last_exhale = exhale_s;
  last_inhale = inhale_s;
  last_cycle = exhale_s + inhale_s;
  last_smoothness = smoothness();
  last_peak_flow = peak_flow();
  last_symmetry = symmetry();
  breath_count++;
  if (breath_count >= calibration_breaths) is_calibrating = false;
  return true;
}

int BreathMetrics::smoothness() const {
  // Second derivative (jerk) of exhale flow, relative to its mean size: 100 smooth .. 0 jerky
  if (n_ < 7) return 100;
  float mean_abs = 0;
  for (int i = 0; i < n_; i++) mean_abs += fabsf(samples_[i]);
  mean_abs /= n_;
  if (mean_abs < 0.05f) return 100;
  float sum = 0;
  int count = 0;
  for (int i = 2; i < n_; i++) {
    float d1 = samples_[i] - samples_[i - 1];
    float d0 = samples_[i - 1] - samples_[i - 2];
    sum += fabsf(d1 - d0);
    count++;
  }
  if (!count) return 100;
  float rel = (sum / count) / mean_abs;
  int s = 100 - (int)(fminf(0.2f, rel) * 500);
  return s < 0 ? 0 : (s > 100 ? 100 : s);
}

float BreathMetrics::peak_flow() const {
  float m = 0;
  for (int i = 0; i < n_; i++) m = fmaxf(m, fabsf(samples_[i]));
  return m;
}

int BreathMetrics::symmetry() const {
  // Where the exhale's peak falls: 0 front-loaded, 50 middle, 100 back-loaded
  if (n_ < 3) return 50;
  int peak = 0;
  for (int i = 1; i < n_; i++)
    if (fabsf(samples_[i]) > fabsf(samples_[peak])) peak = i;
  int s = (int)((float)peak / (n_ - 1) * 100);
  return s < 0 ? 0 : (s > 100 ? 100 : s);
}

// ---------------------------------------------------------------- detector

BreathDetector::BreathDetector() {
  apply_color_thresholds(DEFAULT_VERY_SHORT_MAX, DEFAULT_SHORT_MAX, DEFAULT_MEDIUM_MAX,
                         DEFAULT_LONG_MAX);
  alpha_flow_ = ALPHA_FLOW;
  deriv_gain_ = DERIV_GAIN;
  th_start_ = TH_FRAC_START;
  th_end_ = TH_FRAC_END;
}

void BreathDetector::apply_sensitivity(int preset) {
  if (preset < 0) preset = 0;
  if (preset > 9) preset = 9;
  alpha_flow_ = SENSITIVITY_PRESETS[preset][0];
  deriv_gain_ = SENSITIVITY_PRESETS[preset][1];
  th_start_ = SENSITIVITY_PRESETS[preset][2];
  th_end_ = SENSITIVITY_PRESETS[preset][3];
  t_fast_ = t_slow_ = prev_flow_ = flow_lp = 0;   // Reset filters
}

void BreathDetector::apply_color_thresholds(float vs, float s, float m, float l) {
  very_short_max_ = vs;
  short_max_ = s;
  medium_max_ = m;
  long_max_ = l;
}

int BreathDetector::depth_color() const {
  float d = last_exhale;
  if (d <= very_short_max_) return 0;
  if (d <= short_max_) return 1;
  if (d <= medium_max_) return 2;
  if (d <= long_max_) return 3;
  return 4;
}

bool BreathDetector::process(double t, double now) {
  bool transition = false;

  t_fast_ = (1.0 - ALPHA_FAST) * t_fast_ + ALPHA_FAST * t;
  t_slow_ = (1.0 - ALPHA_SLOW) * t_slow_ + ALPHA_SLOW * t;
  double flow = -(t_fast_ - t_slow_);   // Cooling (inhale) is positive
  double dflow = (flow - prev_flow_) / DT;
  prev_flow_ = flow;
  flow_lp = (1.0 - alpha_flow_) * flow_lp + alpha_flow_ * (flow + deriv_gain_ * dflow);

  if (flow_lp > 0.0) {
    peak_ex_ = fmax(peak_ex_ * LEAK_DECAY, flow_lp);
    scale_ex_ = fmax((1.0 - EMA_MAG) * scale_ex_ + EMA_MAG * peak_ex_, SCALE_FLOOR);
  } else if (flow_lp < 0.0) {
    double mag = -flow_lp;
    peak_in_ = fmax(peak_in_ * LEAK_DECAY, mag);
    scale_in_ = fmax((1.0 - EMA_MAG) * scale_in_ + EMA_MAG * peak_in_, SCALE_FLOOR);
  }

  double denom = fmax(1e-6, flow_lp >= 0 ? scale_ex_ : scale_in_);
  double n = flow_lp / denom;
  double dnorm = (n - prev_norm_) / DT;
  prev_norm_ = n;
  norm = n;

  if (phase == PH_EXH) metrics.record_sample((float)flow_lp);
  peak_val_ = fmax(peak_val_, fabs(n));

  double phase_age = now - t_phase_start_;

  // Idle: small and flat for a while
  if (phase != PH_IDLE) {
    if (fabs(n) <= IDLE_MAG_FRAC && fabs(dnorm) <= IDLE_SLOPE_FRAC) {
      if (idle_hold_start_ < 0) idle_hold_start_ = now;
      if ((now - idle_hold_start_) >= (IDLE_HOLD_S * 1.5) && phase_age >= MIN_PHASE_S) {
        if (phase == PH_EXH && exhale_start_ >= 0) {
          last_exhale = now - exhale_start_;
          record_exhale((float)last_exhale);
        }
        phase = PH_IDLE;
        t_phase_start_ = now;
        peak_val_ = 0;
        transition = true;
        last_transition_s = now;
      }
    } else {
      idle_hold_start_ = -1;
    }
  }

  if (now < refrac_until_) return transition;

  if (phase != PH_INH && n > th_start_) {
    if (phase_age >= MIN_PHASE_S || phase == PH_IDLE) {
      if (phase == PH_EXH && exhale_start_ >= 0) {
        last_exhale = now - exhale_start_;
        record_exhale((float)last_exhale);
        if (metrics.end_exhale((float)last_exhale, (float)last_inhale)) new_breath = true;
      }
      phase = PH_INH;
      t_phase_start_ = now;
      inhale_start_ = now;
      peak_val_ = 0;
      idle_hold_start_ = -1;
      refrac_until_ = now + MIN_PHASE_S * 0.5;
      transition = true;
      last_transition_s = now;
    }
  } else if (phase != PH_EXH && n < -th_start_) {
    if (phase_age >= MIN_PHASE_S || phase == PH_IDLE) {
      if (phase == PH_INH && inhale_start_ >= 0) last_inhale = now - inhale_start_;
      phase = PH_EXH;
      t_phase_start_ = now;
      exhale_start_ = now;
      peak_val_ = 0;
      idle_hold_start_ = -1;
      refrac_until_ = now + MIN_PHASE_S * 0.5;
      metrics.start_exhale();
      transition = true;
      last_transition_s = now;
    }
  }
  return transition;
}

void BreathDetector::record_exhale(float d) {
  // Unworn: 6 exhales in a row under 0.6 s; one of 1.5 s or more clears it
  if (d <= 0.6f) {
    if (++short_streak_ >= 6) unworn = true;
    return;
  }
  short_streak_ = 0;
  if (unworn && d >= 1.5f) unworn = false;
}
