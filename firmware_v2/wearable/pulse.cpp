// pulse.cpp - see pulse.h. Same signal chain as pulse_detector.py: light low-pass -> two-stage
// baseline removal -> adaptive envelope -> rising-edge threshold, beat reported at its peak; a
// steady display rhythm steered by detected beats; RMSSD from the steepest upstroke of each beat.

#include "pulse.h"

#include <math.h>
#include <string.h>

static constexpr float kLpTau = 1.0f / (2.0f * 3.14159265f * PULSE_FILTER_HZ);
static constexpr float kSign = -1.0f;   // MAX3010x IR dips on each beat

static inline int32_t tdiff(uint32_t a, uint32_t b) { return (int32_t)(a - b); }  // Wrap-safe
static inline float alpha(float dt, float tau) { return dt / (tau + dt); }
static inline float clamp01(float x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }

PulseDetector::PulseDetector() {
  rise_avg_ = HEART_STRESS_BPM_START / HEART_STRESS_SD;
  stress_bpm = HEART_STRESS_BPM_START;
  memset(hist_, 0, sizeof(hist_));
}

void PulseDetector::feed(const uint32_t* samples, int n, uint32_t now, bool skin) {
  if (skin != worn_) {
    worn_ = skin;
    primed_ = false;   // Restart the filters from the new light level
    if (!skin) {
      lose_signal();
      value = env_hi_ = env_lo_ = 0;
      n_sq_ = 0;
      hrv_ms = 0;
    }
  }
  if (!worn_) return;
  for (int i = 0; i < n; i++)
    process((float)samples[i], now - (uint32_t)((n - 1 - i) * PULSE_SAMPLE_MS),
            PULSE_SAMPLE_MS / 1000.0f);
}

void PulseDetector::tick(uint32_t now) {
  if (have_rise_) {
    int32_t since = tdiff(now, last_rise_ms_);
    if (since > PULSE_SIGNAL_TIMEOUT_MS)
      lose_signal();
    else if (locked_ibi_ > 0 && since > 2.5f * locked_ibi_)
      unlock();   // Two beats missed: rhythm lost
  }
  tick_rhythm(now);
}

void PulseDetector::reset_signal() {
  lose_signal();
  primed_ = false;
  r_ibi_ = 0;
  value = env_hi_ = env_lo_ = 0;
  n_sq_ = 0;
  hrv_ms = 0;
}

void PulseDetector::process(float raw, uint32_t now, float dt) {
  float v = kSign * raw;
  if (!primed_) {
    primed_ = true;
    offset_ = v;
    lp_ = dc_ = dc2_ = 0;
    env_hi_ = env_lo_ = cycle_min_ = 0;
    armed_ = true;
    in_beat_ = false;
  } else if (fabsf(v - offset_ - dc_) > 16384.0f) {
    float shift = v - offset_;   // Re-centre on a big level change, for float precision
    offset_ = v;
    lp_ -= shift;
    dc_ -= shift;
  }

  lp_ += alpha(dt, kLpTau) * ((v - offset_) - lp_);
  dc_ += alpha(dt, 0.8f) * (lp_ - dc_);
  float y = lp_ - dc_;
  dc2_ += alpha(dt, 0.8f) * (y - dc2_);
  float x = y - dc2_;
  value = x;
  n_++;
  hist_[n_ % kHist] = x;

  float decay = alpha(dt, 2.0f);
  env_hi_ = x > env_hi_ ? x : env_hi_ * (1.0f - decay);
  env_lo_ = x < env_lo_ ? x : env_lo_ * (1.0f - decay);
  float amp = env_hi_ - env_lo_;
  env_amp = amp;
  if (x < cycle_min_) cycle_min_ = x;

  if (amp >= MAX3010X_MIN_AMP) {
    if (armed_ && x > env_lo_ + 0.55f * amp) {
      armed_ = false;
      on_rise(now);
    } else if (!armed_ && x < env_lo_ + 0.35f * amp) {
      armed_ = true;
    }
  }
  if (in_beat_) {
    if (x > beat_max_)
      beat_max_ = x;
    else if (x < beat_max_ - 0.12f * amp)
      on_peak(now);
  }
}

float PulseDetector::median_ibi() const {
  float s[kIbiHistory];
  memcpy(s, ibis_, sizeof(float) * n_ibis_);
  for (int i = 1; i < n_ibis_; i++)   // Insertion sort (5 values)
    for (int j = i; j > 0 && s[j - 1] > s[j]; j--) { float t = s[j]; s[j] = s[j - 1]; s[j - 1] = t; }
  return s[n_ibis_ / 2];
}

void PulseDetector::add_ibi(float ibi) {
  if (n_ibis_ == kIbiHistory) { memmove(ibis_, ibis_ + 1, sizeof(float) * (kIbiHistory - 1)); n_ibis_--; }
  ibis_[n_ibis_++] = ibi;
  bpm = 60000.0f / median_ibi();
}

void PulseDetector::on_rise(uint32_t now) {
  rise_regular_ = false;
  if (have_rise_) {
    float ibi = (float)tdiff(now, last_rise_ms_);
    if (ibi < PULSE_MIN_IBI_MS) return;   // Dicrotic notch or noise
    if (locked_ibi_ > 0) {
      // Locked: only a rise where a beat is due counts (one missed beat tolerated)
      int n = ibi > 1.5f * locked_ibi_ ? 2 : 1;
      if (fabsf(ibi - n * locked_ibi_) > PULSE_LOCK_WINDOW * locked_ibi_) return;
      add_ibi(ibi / n);
      locked_ibi_ = median_ibi();
      rise_regular_ = true;
    } else if (ibi <= PULSE_MAX_IBI_MS) {
      add_ibi(ibi);
      float med = median_ibi();
      if (n_ibis_ >= PULSE_MIN_RHYTHM) {
        rise_regular_ = true;
        for (int i = n_ibis_ - PULSE_MIN_RHYTHM; i < n_ibis_; i++)
          if (fabsf(ibis_[i] - med) > PULSE_REGULARITY * med) rise_regular_ = false;
      }
    }
  }
  have_rise_ = true;
  last_rise_ms_ = now;
  rise_n_ = n_;
  in_beat_ = true;
  beat_max_ = value;
}

void PulseDetector::on_peak(uint32_t now) {
  in_beat_ = false;
  float amp = beat_max_ - cycle_min_;
  cycle_min_ = beat_max_;

  if (amp_ref_ <= 0) amp_ref_ = amp;
  beat_amp = amp;
  if (n_amps_ == kIbiHistory) { memmove(amps_, amps_ + 1, sizeof(float) * (kIbiHistory - 1)); n_amps_--; }
  amps_[n_amps_++] = amp;
  float rel = amp / fmaxf(1.0f, amp_ref_);
  amp_beats_++;
  amp_ref_ += fmaxf(0.08f, 1.0f / amp_beats_) * (amp - amp_ref_);
  beat_strength = clamp01((rel - 0.6f) / 0.8f);

  if (locked_ibi_ > 0 && rel > 2.5f) {
    unlock();   // Far bigger than recent beats: movement, not pulse
    beat_confirmed = false;
  } else if (locked_ibi_ > 0) {
    beat_confirmed = rise_regular_;
  } else if (rise_regular_ && amps_consistent()) {
    locked_ibi_ = median_ibi();
    beat_confirmed = true;
  } else {
    beat_confirmed = false;
  }
  beat_count++;
  hrv_beat();
  rhythm_on_beat(now);
}

void PulseDetector::fiducial(int32_t& bk, float& frac) const {
  // Steepest upstroke since the rise, refined between samples by a parabola
  auto h = [this](int32_t k) { return hist_[((k % kHist) + kHist) % kHist]; };
  int32_t lo = rise_n_ - 20;
  if (n_ - kHist + 3 > lo) lo = n_ - kHist + 3;
  bool have = false;
  float best = 0;
  bk = lo;
  for (int32_t k = lo; k <= n_; k++) {
    float d = h(k) - h(k - 1);
    if (!have || d > best) { have = true; best = d; bk = k; }
  }
  frac = 0;
  if (lo < bk && bk < n_) {
    float d0 = h(bk - 1) - h(bk - 2);
    float d2 = h(bk + 1) - h(bk);
    float den = d0 - 2.0f * best + d2;
    if (den < 0) frac = 0.5f * (d0 - d2) / den;
  }
}

void PulseDetector::hrv_beat() {
  bool had = have_fid_;
  int32_t pk = fid_k_;
  float pf = fid_frac_;
  if (!beat_confirmed) {
    have_fid_ = have_last_iv_ = false;
    return;
  }
  fiducial(fid_k_, fid_frac_);
  have_fid_ = true;
  if (!had) return;
  float iv = ((fid_k_ - pk) + (fid_frac_ - pf)) * PULSE_SAMPLE_MS;
  float ref = locked_ibi_ > 0 ? locked_ibi_ : iv;
  if (fabsf(iv - ref) > HRV_MAX_DEV * ref) {
    have_last_iv_ = false;   // Missed or extra beat: don't count this gap
    return;
  }
  if (have_last_iv_) {
    float d = iv - last_iv_;
    if (n_sq_ == HRV_BEATS) { memmove(sq_diffs_, sq_diffs_ + 1, sizeof(float) * (HRV_BEATS - 1)); n_sq_--; }
    sq_diffs_[n_sq_++] = d * d;
    if (n_sq_ >= HRV_MIN_BEATS) {
      float s = 0;
      for (int i = 0; i < n_sq_; i++) s += sq_diffs_[i];
      hrv_ms = sqrtf(s / n_sq_);
    }
  }
  last_iv_ = iv;
  have_last_iv_ = true;
}

void PulseDetector::rhythm_on_beat(uint32_t now) {
  if (r_ibi_ <= 0) {
    if (beat_confirmed && locked_ibi_ > 0) {   // Start on the first confirmed beat
      r_ibi_ = locked_ibi_;
      r_next_ms_ = now;
      r_support_ms_ = now;
    }
    return;
  }
  float ibi = r_ibi_;
  float err = (float)tdiff(now, r_next_ms_) + ibi;   // Against the nearest shown beat
  if (err > ibi / 2) err -= ibi;
  if (fabsf(err) > HEART_PHASE_WINDOW * ibi && !beat_confirmed) return;   // Doesn't fit
  r_next_ms_ += (int32_t)(HEART_PHASE_GAIN * err);
  r_support_ms_ = now;
  if (locked_ibi_ > 0) {
    float step = HEART_RATE_EASE * (locked_ibi_ - ibi) + HEART_RATE_GAIN * err;
    float limit = HEART_MAX_RATE_STEP * ibi;
    r_ibi_ = ibi + fmaxf(-limit, fminf(limit, step));
  }
}

void PulseDetector::tick_rhythm(uint32_t now) {
  if (r_ibi_ <= 0) return;
  if (!worn_ || tdiff(now, r_support_ms_) > (int32_t)(HEART_COAST_S * 1000)) {
    r_ibi_ = 0;
    return;
  }
  if (tdiff(now, r_next_ms_) >= 0) {
    rhythm_count++;
    update_stress();
    r_next_ms_ += (uint32_t)r_ibi_;
    if (tdiff(now, r_next_ms_) >= 0) r_next_ms_ = now + (uint32_t)r_ibi_;   // Fell behind
  }
}

void PulseDetector::update_stress() {
  float b = rhythm_bpm();
  if (hr_avg_ == 0) {
    hr_avg_ = b;
    if (baseline_bpm == 0) baseline_bpm = b;   // Kept when restored from flash
  }
  hr_avg_ += HEART_STRESS_SMOOTH * (b - hr_avg_);
  float rate = hr_avg_ < baseline_bpm ? HEART_BASELINE_DOWN : HEART_BASELINE_UP;
  baseline_bpm += rate * (hr_avg_ - baseline_bpm);
  float rise = hr_avg_ - baseline_bpm;
  rate = rise < rise_avg_ ? HEART_SCALE_DOWN : HEART_SCALE_UP;
  rise_avg_ += rate * (fmaxf(0.0f, rise) - rise_avg_);
  stress_bpm = fmaxf(HEART_STRESS_BPM_MIN, fminf(HEART_STRESS_BPM_MAX, HEART_STRESS_SD * rise_avg_));
  float k = clamp01(rise / stress_bpm);
  rate_stress = k;

  if (hrv_ms > 0) {
    if (baseline_hrv == 0) baseline_hrv = hrv_ms;
    baseline_hrv += HEART_HRV_BASELINE * (hrv_ms - baseline_hrv);
    hrv_stress = clamp01((1.0f - hrv_ms / baseline_hrv) / HEART_STRESS_HRV_DROP);
    k = (1.0f - HEART_HRV_WEIGHT) * k + HEART_HRV_WEIGHT * hrv_stress;
  }
  stress = k;
}

bool PulseDetector::amps_consistent() const {
  if (n_amps_ < PULSE_MIN_RHYTHM) return false;
  float s[kIbiHistory];
  memcpy(s, amps_, sizeof(float) * n_amps_);
  for (int i = 1; i < n_amps_; i++)
    for (int j = i; j > 0 && s[j - 1] > s[j]; j--) { float t = s[j]; s[j] = s[j - 1]; s[j - 1] = t; }
  float med = s[n_amps_ / 2];
  for (int i = n_amps_ - PULSE_MIN_RHYTHM; i < n_amps_; i++)
    if (fabsf(amps_[i] - med) > PULSE_AMP_CONSISTENCY * med) return false;
  return true;
}

void PulseDetector::unlock() {
  locked_ibi_ = 0;
  n_ibis_ = 0;
  n_amps_ = 0;
}

void PulseDetector::lose_signal() {
  unlock();
  have_rise_ = false;
  in_beat_ = false;
  bpm = 0;
  amp_ref_ = 0;
  amp_beats_ = 0;
  beat_strength = 0.5f;
  rise_regular_ = false;
  beat_confirmed = false;
  have_fid_ = have_last_iv_ = false;
}

float PulseDetector::level() const {
  float ref = amp_ref_ > 0 ? amp_ref_ : env_hi_ - env_lo_;
  ref = fmaxf(MAX3010X_MIN_AMP, ref);
  float l = (value - env_lo_) / ref;
  return l < 0 ? 0 : (l > 1.6f ? 1.6f : l);
}

float PulseDetector::normalized() const { return worn_ ? level() * 2.0f - 1.0f : 0.0f; }

HeartBaselines PulseDetector::baselines() const {
  HeartBaselines b;
  b.baseline_bpm = baseline_bpm;
  b.rise_avg = rise_avg_;
  b.baseline_hrv = baseline_hrv;
  return b;
}

void PulseDetector::restore(const HeartBaselines& b) {
  if (b.baseline_bpm > 30 && b.baseline_bpm < 200) baseline_bpm = b.baseline_bpm;
  if (b.rise_avg > 0 && b.rise_avg < 20) rise_avg_ = b.rise_avg;
  if (b.baseline_hrv > 0 && b.baseline_hrv < 500) baseline_hrv = b.baseline_hrv;
  stress_bpm = fmaxf(HEART_STRESS_BPM_MIN, fminf(HEART_STRESS_BPM_MAX, HEART_STRESS_SD * rise_avg_));
}
