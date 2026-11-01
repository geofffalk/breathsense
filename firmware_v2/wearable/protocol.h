// protocol.h - BLE line protocol (Nordic UART). See .claude/skills/breathsense-protocol.
//
// Headset -> app: B (breath, breath mode), H (heart, heart mode), P (battery), R (settings),
// M,{F|H|O} (current mode, on connect and every change; new in v2), K (scores, ~1 Hz; new).
// App -> headset: M,{F|H|O}, S,F / S,C / S,M (+ optional weights) / S,W (new), L,{1|0}, Q.
// Dropped with guided: M,G, S,G, S,CS (ignored if sent).

#pragma once

#include <stddef.h>
#include <stdint.h>

#include "breath.h"
#include "scoring.h"
#include "storage.h"

namespace proto {

int fmt_breath(char* buf, size_t n, uint32_t ts, const BreathDetector& d);
int fmt_heart(char* buf, size_t n, uint32_t ts, float wave, int bpm, bool signal, uint32_t beats,
              int stress, int hrv);
int fmt_battery(char* buf, size_t n, int mv, int percent, bool usb);
int fmt_settings(char* buf, size_t n, const Settings& s);
int fmt_mode(char* buf, size_t n, Mode m);
int fmt_scores(char* buf, size_t n, const Scores& k);

// A parsed app command
struct Command {
  enum Type { NONE, MODE, COLOR_THRESHOLDS, SENSITIVITY, MOOD, WEIGHTS, LED, QUERY } type = NONE;
  Mode mode = MODE_HEART;
  float f[9] = {0};
  int count = 0;     // Numbers given (optional trailing fields)
  int i = 0;
};
Command parse(const char* line);

}  // namespace proto
