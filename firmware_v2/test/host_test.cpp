// host_test.cpp - Runs the firmware's pure modules on a computer, on input files, so their output
// can be compared with the v1 Python (breath, pulse) and the app's Dart (mood). See compare.py.
//
//   host_test breath temps.txt     one temperature per line, 100 Hz
//   host_test pulse ir.txt         per tick: now_ms skin n s1 .. sn
//   host_test mood breaths.txt     per breath: exhale inhale cycle smoothness peak_flow
//   host_test breathled temps.txt  breath LED frames, v1 motion (bar front always 9)
//   host_test heartled ir.txt      heart LED frames
//   host_test settings             the R line with default settings

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../wearable/breath.h"
#include "../wearable/pulse.h"
#include "../wearable/display.h"
#include "../wearable/protocol.h"
#include "../wearable/scoring.h"

static int run_breath(FILE* in) {
  BreathDetector d;
  double t;
  long i = 0;
  while (fscanf(in, "%lf", &t) == 1) {
    double now = i * 0.01 + 1e-9;
    if (d.process(t, now)) printf("T,%.2f,%d,%d\n", now, (int)d.phase, d.depth_color());
    if (d.new_breath) {
      d.new_breath = false;
      const BreathMetrics& m = d.metrics;
      printf("N,%d,%.2f,%.2f,%d,%.3f,%d\n", m.breath_count, m.last_exhale, m.last_inhale,
             m.last_smoothness, m.last_peak_flow, m.last_symmetry);
      char b[160];
      proto::fmt_breath(b, sizeof(b), 0, d);
      fputs(b, stdout);
    }
    i++;
  }
  return 0;
}

static int run_pulse(FILE* in) {
  PulseDetector p;
  uint32_t seen = 0;
  unsigned long now;
  int skin, n;
  while (fscanf(in, "%lu %d %d", &now, &skin, &n) == 3) {
    uint32_t s[64];
    for (int k = 0; k < n; k++) {
      unsigned long v;
      if (fscanf(in, "%lu", &v) != 1) return 1;
      s[k] = (uint32_t)v;
    }
    p.feed(s, n, (uint32_t)now, skin != 0);
    p.tick((uint32_t)now);
    if (p.rhythm_count != seen) {
      seen = p.rhythm_count;
      printf("R,%lu,%u,%.1f,%.3f,%.1f\n", now, (unsigned)p.rhythm_count, p.rhythm_bpm(), p.stress, p.hrv_ms);
      char b[160];
      proto::fmt_heart(b, sizeof(b), 0, p.normalized(), (int)(p.rhythm_bpm() + 0.5f), p.rhythm_bpm() > 0,
                       p.rhythm_count, (int)(p.stress * 100), (int)(p.hrv_ms + 0.5f));
      fputs(b, stdout);
    }
  }
  return 0;
}

static int run_mood(FILE* in) {
  MoodAnalyzer m;
  float ex, inh, cyc, peak;
  int sm;
  while (fscanf(in, "%f %f %f %d %f", &ex, &inh, &cyc, &sm, &peak) == 5) {
    m.record_breath(ex, inh, cyc, sm, peak);
    printf("M,%d,%d,%d,%d\n", m.stress, m.focus, m.meditation, m.calibrating() ? 1 : 0);
  }
  return 0;
}

static void print_frame(double t, const Frame& f) {
  printf("F,%.2f", t);
  for (const auto& p : f.px) printf(",%d,%d,%d", p.r, p.g, p.b);
  printf("\n");
}

static int run_breathled(FILE* in) {
  BreathDetector d;
  BreathDisplay disp;
  for (int& s : disp.start_by_depth) s = 9;   // v1's motion: the bar's front is always LED 9
  Frame f, last;
  f.clear();
  last.clear();
  double t;
  long i = 0;
  while (fscanf(in, "%lf", &t) == 1) {
    double now = i * 0.01 + 1e-9;
    d.process(t, now);
    disp.tick(d, now, f);
    if (!(f == last)) { print_frame(now, f); last = f; }
    i++;
  }
  return 0;
}

static int run_heartled(FILE* in) {
  PulseDetector p;
  HeartDisplay disp;
  disp.reset(p);
  Frame f, last;
  f.clear();
  last.clear();
  unsigned long now;
  int skin, n;
  while (fscanf(in, "%lu %d %d", &now, &skin, &n) == 3) {
    uint32_t s[64];
    for (int k = 0; k < n; k++) {
      unsigned long v;
      if (fscanf(in, "%lu", &v) != 1) return 1;
      s[k] = (uint32_t)v;
    }
    p.feed(s, n, (uint32_t)now, skin != 0);
    p.tick((uint32_t)now);
    disp.tick(p, (uint32_t)now, f);
    if (!(f == last)) { print_frame(now / 1000.0, f); last = f; }
  }
  return 0;
}

int main(int argc, char** argv) {
  if (argc >= 2 && !strcmp(argv[1], "settings")) {
    char b[200];
    Settings st;
    proto::fmt_settings(b, sizeof(b), st);
    fputs(b, stdout);
    return 0;
  }
  if (argc < 3) return 2;
  FILE* in = fopen(argv[2], "r");
  if (!in) return 2;
  if (!strcmp(argv[1], "breath")) return run_breath(in);
  if (!strcmp(argv[1], "pulse")) return run_pulse(in);
  if (!strcmp(argv[1], "mood")) return run_mood(in);
  if (!strcmp(argv[1], "breathled")) return run_breathled(in);
  if (!strcmp(argv[1], "heartled")) return run_heartled(in);
  return 2;
}
