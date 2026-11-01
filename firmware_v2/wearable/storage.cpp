// storage.cpp - see storage.h. Files hold the raw structs, with a version to reject old layouts.

#include "storage.h"

#include <Adafruit_LittleFS.h>
#include <InternalFileSystem.h>

using namespace Adafruit_LittleFS_Namespace;

static const char* kSettingsFile = "/settings.bin";
static const char* kStateFile = "/state.bin";

template <typename T>
static bool read_file(const char* path, T& out, uint32_t version) {
  File f(InternalFS);
  if (!f.open(path, FILE_O_READ)) return false;
  T tmp;
  bool ok = f.read((uint8_t*)&tmp, sizeof(T)) == (int)sizeof(T) && tmp.version == version;
  f.close();
  if (ok) out = tmp;
  return ok;
}

template <typename T>
static void write_file(const char* path, const T& in) {
  InternalFS.remove(path);
  File f(InternalFS);
  if (f.open(path, FILE_O_WRITE)) {
    f.write((const uint8_t*)&in, sizeof(T));
    f.close();
  }
}

namespace storage {
void begin() { InternalFS.begin(); }
bool load(Settings& s) { return read_file(kSettingsFile, s, Settings().version); }
void save(const Settings& s) { write_file(kSettingsFile, s); }
bool load(State& st) { return read_file(kStateFile, st, State().version); }
void save(const State& st) { write_file(kStateFile, st); }
}  // namespace storage
