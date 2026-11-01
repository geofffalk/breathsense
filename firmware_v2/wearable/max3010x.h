// max3010x.h - Minimal MAX30101/30102/30105 driver: SpO2 mode at 100 samples/s, IR channel.
// Port of firmware/max3010x.py, plus shutdown/wake for v2's "off".

#pragma once

#include <Arduino.h>
#include <Wire.h>

class Max3010x {
 public:
  bool begin(uint8_t ir_current, uint8_t red_current);   // false if no sensor answers
  int read_ir(uint32_t* out, int max_n);                  // New samples, oldest first
  void set_led_current(uint8_t ir, uint8_t red);
  void shutdown(bool off);
  bool present() const { return present_; }
  bool skin = false;                                      // Skin on the sensor (with hysteresis)

 private:
  bool present_ = false;
  void write_reg(uint8_t reg, uint8_t v);
  uint8_t read_reg(uint8_t reg);
  void clear_fifo();
};
