// max3010x.cpp - see max3010x.h.

#include "max3010x.h"

#include "config.h"

static constexpr uint8_t ADDR = 0x57;
static constexpr uint8_t FIFO_WR_PTR = 0x04, FIFO_DATA = 0x07, FIFO_CONFIG = 0x08;
static constexpr uint8_t MODE_CONFIG = 0x09, SPO2_CONFIG = 0x0A, LED1_PA = 0x0C, LED2_PA = 0x0D;
static constexpr uint8_t PART_ID = 0xFF, PART_ID_MAX3010X = 0x15;
static constexpr uint8_t MODE_RESET = 0x40, MODE_SPO2 = 0x03, MODE_SHDN = 0x80;
static constexpr uint32_t FULL_SCALE = (1u << 18) - 1;

// The core's Wire waits forever if SDA or SCL is held low (no sensor power, a short, a stuck chip), so check
// the bus first: both lines should idle high on their pull-ups. A stuck SDA gets nine clocks to free it.
static bool bus_idle() {
  pinMode(PIN_WIRE_SDA, INPUT_PULLUP);
  pinMode(PIN_WIRE_SCL, INPUT_PULLUP);
  delay(2);
  if (digitalRead(PIN_WIRE_SCL) == LOW) return false;
  for (int i = 0; i < 9 && digitalRead(PIN_WIRE_SDA) == LOW; i++) {
    pinMode(PIN_WIRE_SCL, OUTPUT);
    digitalWrite(PIN_WIRE_SCL, LOW);
    delayMicroseconds(5);
    pinMode(PIN_WIRE_SCL, INPUT_PULLUP);
    delayMicroseconds(5);
  }
  return digitalRead(PIN_WIRE_SDA) == HIGH && digitalRead(PIN_WIRE_SCL) == HIGH;
}

bool Max3010x::begin(uint8_t ir, uint8_t red) {
  bus_stuck = !bus_idle();
  if (bus_stuck) {
    present_ = false;
    return false;
  }
  Wire.begin();
  Wire.setClock(400000);
  present_ = read_reg(PART_ID) == PART_ID_MAX3010X;
  if (!present_) return false;
  write_reg(MODE_CONFIG, MODE_RESET);
  uint32_t t0 = millis();
  while ((read_reg(MODE_CONFIG) & MODE_RESET) && millis() - t0 < 100) {}
  write_reg(FIFO_CONFIG, (0b001 << 5) | 0x10);                // Average pairs; roll over when full
  write_reg(SPO2_CONFIG, (0b01 << 5) | (0b010 << 2) | 0b11);  // 4096 nA, 200 sps, 411 us, 18-bit
  set_led_current(ir, red);
  write_reg(MODE_CONFIG, MODE_SPO2);
  clear_fifo();
  return true;
}

void Max3010x::set_led_current(uint8_t ir, uint8_t red) {
  write_reg(LED2_PA, ir);
  write_reg(LED1_PA, red);
}

void Max3010x::shutdown(bool off) {
  if (!present_) return;
  write_reg(MODE_CONFIG, off ? (MODE_SHDN | MODE_SPO2) : MODE_SPO2);
  if (!off) clear_fifo();
  skin = false;
}

void Max3010x::clear_fifo() {
  write_reg(0x04, 0);
  write_reg(0x05, 0);
  write_reg(0x06, 0);
}

int Max3010x::read_ir(uint32_t* out, int max_n) {
  if (!present_) return 0;
  Wire.beginTransmission(ADDR);
  Wire.write(FIFO_WR_PTR);
  Wire.endTransmission(false);
  if (Wire.requestFrom(ADDR, (uint8_t)3) != 3) return 0;
  uint8_t wr = Wire.read() & 0x1F, ovf = Wire.read(), rd = Wire.read() & 0x1F;
  int n = (wr - rd) & 0x1F;
  if (n == 0 && ovf) n = 32;   // FIFO filled up and wrapped
  if (n > max_n) n = max_n;
  int got = 0;
  while (got < n) {
    int chunk = n - got > 5 ? 5 : n - got;   // 6 bytes each; keep under the 32-byte Wire buffer
    Wire.beginTransmission(ADDR);
    Wire.write(FIFO_DATA);
    Wire.endTransmission(false);
    if (Wire.requestFrom(ADDR, (uint8_t)(chunk * 6)) != chunk * 6) break;
    for (int i = 0; i < chunk; i++) {
      Wire.read(); Wire.read(); Wire.read();   // Red (unused)
      uint32_t ir = ((uint32_t)Wire.read() << 16) | ((uint32_t)Wire.read() << 8) | Wire.read();
      out[got++] = ir & FULL_SCALE;
    }
  }
  if (got) {
    uint32_t ir = out[got - 1];   // Reflected IR jumps when skin covers the sensor
    skin = skin ? ir > MAX3010X_SKIN_LEVEL * 8 / 10 : ir > MAX3010X_SKIN_LEVEL;
  }
  return got;
}

void Max3010x::write_reg(uint8_t reg, uint8_t v) {
  Wire.beginTransmission(ADDR);
  Wire.write(reg);
  Wire.write(v);
  Wire.endTransmission();
}

uint8_t Max3010x::read_reg(uint8_t reg) {
  Wire.beginTransmission(ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 0;
  if (Wire.requestFrom(ADDR, (uint8_t)1) != 1) return 0;
  return Wire.read();
}
