// max3010x.h - Minimal MAX30101/30102/30105 driver: SpO2 mode at 100 samples/s, IR channel.
// Port of firmware/max3010x.py, plus shutdown/wake for v2's "off".

#pragma once

#include <Arduino.h>

class Max3010x {
 public:
  bool begin(uint8_t ir_current, uint8_t red_current);   // false if no sensor answers
  int read_ir(uint32_t* out, int max_n);                  // New samples, oldest first
  void set_led_current(uint8_t ir, uint8_t red);
  void shutdown(bool off);
  bool present() const { return present_; }
  bool bus_stuck = false;   // SDA or SCL held low at begin(): the sensor was skipped
  bool ext_pullups = false; // Lines idle high without the nRF's pull-ups (breakout powered)
  bool acked = false;       // Something answered at 0x57
  uint8_t part_id = 0;      // 0x15 for a MAX3010x
  bool shorted = false;     // SDA and SCL bridged together
  bool swapped = false;     // No answer, but one with SDA and SCL swapped: a wiring fault
  bool skin = false;                                      // Skin on the sensor (with hysteresis)

 private:
  bool present_ = false;
  void write_reg(uint8_t reg, uint8_t v);
  uint8_t read_reg(uint8_t reg);
  void clear_fifo();
};
