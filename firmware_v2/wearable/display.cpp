// display.cpp - see display.h.

#include "display.h"

#include <math.h>

bool Frame::operator==(const Frame& o) const {
  for (int i = 0; i < STRIP_LEN; i++)
    if (px[i].r != o.px[i].r || px[i].g != o.px[i].g || px[i].b != o.px[i].b) return false;
  return true;
}

// Colours stay as floats until the final scale, as in v1 (int() once, at the end)
static RgbF lerp(Rgb a, Rgb b, float t) {
  return {a.r + (b.r - a.r) * t, a.g + (b.g - a.g) * t, a.b + (b.b - a.b) * t};
}

static RgbF heart_color(float k) {   // Monitor green -> amber -> red
  return k < 0.5f ? lerp(HEART_CALM_COLOR, HEART_MID_COLOR, k * 2.0f)
                  : lerp(HEART_MID_COLOR, HEART_HOT_COLOR, (k - 0.5f) * 2.0f);
}

static Rgb scale(RgbF c, float v) {
  return {(uint8_t)(int)(c.r * v), (uint8_t)(int)(c.g * v), (uint8_t)(int)(c.b * v)};
}

// ---------------------------------------------------------------- heart

// Beat at 60 BPM (s): start, rise, hold, fall, height: main beat then a smaller counter-beat
struct Pulse { float start, rise, hold, fall, height; };
static const Pulse kBeat[2] = {
    {0.00f, 0.08f, 0.06f, 0.18f, 1.0f},
    {0.36f, 0.07f, 0.04f, 0.17f, HEART_COUNTER_BEAT},
};

static float pulse_fill(float t, const Pulse& p) {
  t -= p.start;
  if (t < 0) return 0;
  if (t < p.rise) { float u = t / p.rise; return p.height * (1.0f - (1.0f - u) * (1.0f - u)); }
  t -= p.rise;
  if (t < p.hold) return p.height;
  t -= p.hold;
  if (t < p.fall) { float u = t / p.fall; return p.height * (1.0f - u * u); }
  return 0;
}

void HeartDisplay::tick(const PulseDetector& p, uint32_t now, Frame& f) {
  if (p.rhythm_count != seen_) {
    seen_ = p.rhythm_count;
    float k = p.stress;
    reach_ = HEART_MIN_FILL + k * (STRIP_LEN - HEART_MIN_FILL);
    color_ = heart_color(k);
    float bpm = p.rhythm_bpm();
    time_scale_ = bpm > 0 ? fminf(1.0f, 60.0f / bpm) : 1.0f;
    beat_ms_ = now;
    active_ = true;
  }
  float fill = 0;
  if (active_) {
    float t = (int32_t)(now - beat_ms_) / 1000.0f / time_scale_;
    for (const auto& b : kBeat) fill = fmaxf(fill, pulse_fill(t, b));
    const Pulse& last = kBeat[1];
    if (t > last.start + last.rise + last.hold + last.fall) active_ = false;
  }
  float pos = fill * reach_;   // Solid bar from the back; the end LED fades in
  for (int i = 0; i < STRIP_LEN; i++) {
    float v = (i + 1 <= pos) ? 1.0f : fmaxf(0.0f, pos - i);
    f.px[i] = scale(color_, v);
  }
}

// ---------------------------------------------------------------- breath

void BreathDisplay::tick(const BreathDetector& d, double now, Frame& f) {
  BreathPhase phase = d.phase;
  int depth = d.depth_color();

  // Debounced phase change (0.35 s)
  if (phase != last_) {
    if (pending_ != phase) {
      pending_ = phase;
      stable_since_ = now;
    } else if (now - stable_since_ >= BREATH_DEBOUNCE_S) {
      if (phase == PH_INH) {
        start_ = start_by_depth[depth];
        hold_.clear();
        hold_.px[start_] = DEPTH_COLORS[depth];
        holding_ = true;
        exhale_start_ = -1;
        locked_ = false;
      } else if (phase == PH_EXH) {
        exhale_start_ = now;
        exhale_pred_ = fmax(1.0, d.last_exhale);
        locked_ = false;
        holding_ = false;
      }
      last_ = phase;
    }
  } else {
    pending_ = phase;
  }

  BreathPhase show = last_;
  // Sticky exhale: brief dips below threshold keep the comet going
  if (phase == PH_IDLE && last_ == PH_EXH && exhale_start_ >= 0 &&
      (now - exhale_start_) < exhale_pred_ + 0.2)
    show = PH_EXH;

  if (show == PH_EXH) {
    render_exhale(now, depth, f);
  } else if (show == PH_IDLE) {
    if (exhale_start_ >= 0 && (now - exhale_start_) < exhale_pred_ + 0.5) {
      render_exhale(now, depth, f);
    } else if (exhale_start_ >= 0 && (now - exhale_start_) > 4.0) {
      locked_ = false;
      f.clear();
    } else if (exhale_start_ < 0 && !holding_) {
      f.clear();
    }
  } else if (holding_) {
    f = hold_;
  }
}

void BreathDisplay::render_exhale(double now, int depth, Frame& f) {
  if (locked_) { f.clear(); return; }
  if (exhale_start_ < 0) exhale_start_ = now;
  double pred = fmax(0.5, exhale_pred_);
  double progress = fmin(1.0, (now - exhale_start_) / pred);
  Rgb c = DEPTH_COLORS[depth];
  Rgb tail = {(uint8_t)(c.r / 4), (uint8_t)(c.g / 4), (uint8_t)(c.b / 4)};
  int head = (int)((1.0 - progress) * start_);   // start_ (front of this bar) -> 0 (back)
  f.clear();
  if (head >= 0 && head < STRIP_LEN) f.px[head] = c;
  if (head + 1 <= start_ && head + 1 < STRIP_LEN) f.px[head + 1] = tail;   // Never past the bar's front
  if (progress >= 1.0) {
    locked_ = true;
    f.clear();
  }
}

// ---------------------------------------------------------------- animations

void comet_frame(Rgb color, float progress, bool back_to_front, Frame& f) {
  f.clear();
  int head = back_to_front ? (int)(progress * (STRIP_LEN - 1)) : (int)((1.0f - progress) * (STRIP_LEN - 1));
  int tail = back_to_front ? head - 1 : head + 1;
  Rgb t = {(uint8_t)(color.r / 4), (uint8_t)(color.g / 4), (uint8_t)(color.b / 4)};
  if (head >= 0 && head < STRIP_LEN) f.px[head] = color;
  if (tail >= 0 && tail < STRIP_LEN) f.px[tail] = t;
}
