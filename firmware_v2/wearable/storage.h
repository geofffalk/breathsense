// storage.h - Settings and learned state in internal flash (LittleFS).
// Replaces v1's /settings.json. Guided settings are gone; R still reports their default values in
// place so app parsers line up.

#pragma once

#include <stdint.h>

#include "pulse.h"
#include "scoring.h"

enum Mode : uint8_t { MODE_HEART = 0, MODE_BREATH = 1, MODE_OFF = 2 };

struct Settings {
  uint32_t version = 2;
  float very_short_max = 2.0f, short_max = 3.5f, medium_max = 5.0f, long_max = 6.5f;
  int32_t sensitivity = 5;
  uint8_t led_enabled = 1;     // L,{1|0}; reported in R (fixes v1's led_on/led_enabled split)
  MoodSettings mood;
  FuseWeights fuse;
};

struct State {                 // Learned over days; saved every few minutes and before sleep
  uint32_t version = 1;
  uint8_t last_mode = MODE_HEART;   // Heart or breath (never off): the mode to wake in
  HeartBaselines heart;
};

namespace storage {
void begin();
bool load(Settings& s);
void save(const Settings& s);
bool load(State& st);
void save(const State& st);
}  // namespace storage
