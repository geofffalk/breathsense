// protocol.cpp - see protocol.h. Field formats match firmware/code.py and settings_storage.py.

#include "protocol.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace proto {

int fmt_breath(char* buf, size_t n, uint32_t ts, const BreathDetector& d) {
  const BreathMetrics& m = d.metrics;
  // B,{ts},{phase},{flow},{depth},{guided},{exhale},{inhale},{cycle},{smooth},{peak},{sym},{unworn}
  // guided is always -1 now (guided mode dropped)
  return snprintf(buf, n, "B,%lu,%d,%.3f,%d,-1,%.2f,%.2f,%.2f,%d,%.2f,%d,%d\n", (unsigned long)ts,
                  (int)d.phase, d.norm, d.depth_color(), m.last_exhale, m.last_inhale, m.last_cycle,
                  m.last_smoothness, m.last_peak_flow, m.last_symmetry, d.unworn ? 1 : 0);
}

int fmt_heart(char* buf, size_t n, uint32_t ts, float wave, int bpm, bool signal, uint32_t beats,
              int stress, int hrv) {
  return snprintf(buf, n, "H,%lu,%.3f,%d,%d,%lu,%d,%d\n", (unsigned long)ts, wave, bpm, signal ? 1 : 0,
                  (unsigned long)(beats & 0xFFFF), stress, hrv);
}

int fmt_battery(char* buf, size_t n, int mv, int percent, bool usb) {
  return snprintf(buf, n, "P,%d,%d,%d\n", mv, percent, usb ? 1 : 0);
}

int fmt_settings(char* buf, size_t n, const Settings& s) {
  // R,{vs},{s},{m},{l},{sens},{in},{hold_in},{ex},{hold_out},{led_start},{led_end},
  //   {calm_ratio},{calm_var},{focus_con},{cal_breaths},{led_enabled},{color_scheme}
  // The guided fields are gone; their old defaults stay in place so parsers line up.
  return snprintf(buf, n, "R,%.2f,%.2f,%.2f,%.2f,%ld,5.0,5.0,5.0,5.0,2,9,%.2f,%.2f,%.2f,%d,%d,0\n",
                  s.very_short_max, s.short_max, s.medium_max, s.long_max, (long)s.sensitivity,
                  s.mood.calm_ratio, s.mood.calm_variability, s.mood.focus_consistency,
                  s.mood.calibration_breaths, s.led_enabled);
}

int fmt_mode(char* buf, size_t n, Mode m) {
  return snprintf(buf, n, "M,%c\n", m == MODE_HEART ? 'H' : (m == MODE_BREATH ? 'F' : 'O'));
}

int fmt_scores(char* buf, size_t n, const Scores& k) {
  return snprintf(buf, n, "K,%d,%d,%d,%d,%d,%d,%d,%d\n", k.stress, k.focus, k.meditation,
                  k.heart_stress, k.breath_stress, k.nose_worn ? 1 : 0, k.heart_worn ? 1 : 0,
                  k.calibrating ? 1 : 0);
}

// Splits "A,B,1,2" into fields; returns the count
static int split(char* s, char** out, int max) {
  int n = 0;
  char* p = s;
  while (n < max) {
    out[n++] = p;
    char* c = strchr(p, ',');
    if (!c) break;
    *c = 0;
    p = c + 1;
  }
  return n;
}

Command parse(const char* line) {
  Command cmd;
  char buf[128];
  strncpy(buf, line, sizeof(buf) - 1);
  buf[sizeof(buf) - 1] = 0;
  for (char* p = buf; *p; p++)
    if (*p == '\r' || *p == '\n') *p = 0;
  char* f[14];
  int n = split(buf, f, 14);
  if (n < 1 || !f[0][0]) return cmd;
  auto nums = [&](int from) {
    cmd.count = 0;
    for (int k = from; k < n && cmd.count < 9; k++) cmd.f[cmd.count++] = (float)atof(f[k]);
  };

  if (!strcmp(f[0], "M") && n >= 2) {
    char c = f[1][0];
    if (c == 'F' || c == 'f') { cmd.type = Command::MODE; cmd.mode = MODE_BREATH; }
    else if (c == 'H' || c == 'h') { cmd.type = Command::MODE; cmd.mode = MODE_HEART; }
    else if (c == 'O' || c == 'o') { cmd.type = Command::MODE; cmd.mode = MODE_OFF; }
  } else if (!strcmp(f[0], "S") && n >= 3) {
    if (!strcmp(f[1], "F") && n >= 6) { cmd.type = Command::COLOR_THRESHOLDS; nums(2); }
    else if (!strcmp(f[1], "C")) { cmd.type = Command::SENSITIVITY; cmd.i = atoi(f[2]); }
    else if (!strcmp(f[1], "M") && n >= 6) { cmd.type = Command::MOOD; nums(2); }
    else if (!strcmp(f[1], "W") && n >= 6) { cmd.type = Command::WEIGHTS; nums(2); }
  } else if (!strcmp(f[0], "L") && n >= 2) {
    cmd.type = Command::LED;
    cmd.i = atoi(f[1]);
  } else if (!strcmp(f[0], "Q")) {
    cmd.type = Command::QUERY;
  }
  return cmd;
}

}  // namespace proto
