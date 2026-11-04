// max3010x.cpp - see max3010x.h.

#include "max3010x.h"

#include "config.h"

static constexpr uint8_t ADDR = 0x57;
static constexpr uint8_t FIFO_WR_PTR = 0x04, FIFO_DATA = 0x07, FIFO_CONFIG = 0x08;
static constexpr uint8_t MODE_CONFIG = 0x09, SPO2_CONFIG = 0x0A, LED1_PA = 0x0C, LED2_PA = 0x0D;
static constexpr uint8_t PART_ID = 0xFF, PART_ID_MAX3010X = 0x15;
static constexpr uint8_t MODE_RESET = 0x40, MODE_SPO2 = 0x03, MODE_SHDN = 0x80;
static constexpr uint32_t FULL_SCALE = (1u << 18) - 1;

// Bit-banged I2C at ~80 kHz. The core's Wire (TWIM) spins forever if a transfer stalls (it hung boot
// right after "starting MAX30101"), so every wait here has a timeout and a failed transfer just
// returns false. Lines are open drain: a 0 is driven low, a 1 is released to the pull-ups.
static constexpr uint32_t HALF_US = 5, STRETCH_US = 2000;
static bool i2c_fail;   // A timeout in this transfer
static uint8_t SDA_PIN = PIN_WIRE_SDA, SCL_PIN = PIN_WIRE_SCL;   // Swapped only to diagnose wiring

static void line_low(uint8_t pin) { digitalWrite(pin, LOW); pinMode(pin, OUTPUT); }
static void line_rel(uint8_t pin) { pinMode(pin, INPUT_PULLUP); }
static void scl_rel() {
  line_rel(SCL_PIN);
  uint32_t t0 = micros();
  while (digitalRead(SCL_PIN) == LOW)
    if (micros() - t0 > STRETCH_US) { i2c_fail = true; return; }
}
static void i2c_start() {
  line_rel(SDA_PIN); delayMicroseconds(HALF_US);
  scl_rel(); delayMicroseconds(HALF_US);
  line_low(SDA_PIN); delayMicroseconds(HALF_US);
  line_low(SCL_PIN); delayMicroseconds(HALF_US);
}
static void i2c_stop() {
  line_low(SDA_PIN); delayMicroseconds(HALF_US);
  scl_rel(); delayMicroseconds(HALF_US);
  line_rel(SDA_PIN); delayMicroseconds(HALF_US);
}
static bool i2c_write_byte(uint8_t b) {   // true if acknowledged
  for (int i = 7; i >= 0; i--) {
    if (b >> i & 1) line_rel(SDA_PIN); else line_low(SDA_PIN);
    delayMicroseconds(HALF_US);
    scl_rel(); delayMicroseconds(HALF_US);
    line_low(SCL_PIN);
  }
  line_rel(SDA_PIN); delayMicroseconds(HALF_US);
  scl_rel();
  bool ack = digitalRead(SDA_PIN) == LOW;
  delayMicroseconds(HALF_US);
  line_low(SCL_PIN);
  return ack && !i2c_fail;
}
static uint8_t i2c_read_byte(bool ack) {
  uint8_t b = 0;
  line_rel(SDA_PIN);
  for (int i = 0; i < 8; i++) {
    delayMicroseconds(HALF_US);
    scl_rel();
    b = b << 1 | (digitalRead(SDA_PIN) == HIGH);
    delayMicroseconds(HALF_US);
    line_low(SCL_PIN);
  }
  if (ack) line_low(SDA_PIN);
  delayMicroseconds(HALF_US);
  scl_rel(); delayMicroseconds(HALF_US);
  line_low(SCL_PIN);
  line_rel(SDA_PIN);
  return b;
}
// Register writes and burst reads. false on no acknowledge or a timeout.
static bool i2c_write(uint8_t reg, uint8_t v) {
  i2c_fail = false;
  i2c_start();
  bool ok = i2c_write_byte(ADDR << 1) && i2c_write_byte(reg) && i2c_write_byte(v);
  i2c_stop();
  return ok && !i2c_fail;
}
static bool i2c_read(uint8_t reg, uint8_t* out, int n) {
  i2c_fail = false;
  i2c_start();
  bool ok = i2c_write_byte(ADDR << 1) && i2c_write_byte(reg);
  if (ok) {
    i2c_start();   // Repeated start
    ok = i2c_write_byte(ADDR << 1 | 1);
    for (int i = 0; ok && i < n; i++) out[i] = i2c_read_byte(i < n - 1);
  }
  i2c_stop();
  return ok && !i2c_fail;
}

// Both lines should idle high. Free a stuck SDA with up to nine clocks; report whether the lines
// also read high without the nRF's own pull-ups (the breakout's pull-ups, so the sensor has power).
static bool bus_idle(bool* ext_pullups) {
  pinMode(SDA_PIN, INPUT);
  pinMode(SCL_PIN, INPUT);
  delay(2);
  *ext_pullups = digitalRead(SDA_PIN) == HIGH && digitalRead(SCL_PIN) == HIGH;
  line_rel(SDA_PIN);
  line_rel(SCL_PIN);
  delay(2);
  if (digitalRead(SCL_PIN) == LOW) return false;
  for (int i = 0; i < 9 && digitalRead(SDA_PIN) == LOW; i++) {
    line_low(SCL_PIN); delayMicroseconds(HALF_US);
    line_rel(SCL_PIN); delayMicroseconds(HALF_US);
  }
  if (digitalRead(SDA_PIN) == LOW) return false;
  line_low(SCL_PIN);   // A clean stop to reset the sensor's I2C state
  delayMicroseconds(HALF_US);
  i2c_stop();
  return true;
}

// Pull one line low and see if the other follows: a solder bridge between SDA and SCL.
static bool lines_shorted() {
  bool shorted = false;
  for (int k = 0; k < 2; k++) {
    uint8_t drive = k ? SCL_PIN : SDA_PIN, sense = k ? SDA_PIN : SCL_PIN;
    line_rel(sense);
    line_low(drive);
    delayMicroseconds(50);
    if (digitalRead(sense) == LOW) shorted = true;
    line_rel(drive);
    delayMicroseconds(50);
  }
  return shorted;
}

bool Max3010x::begin(uint8_t ir, uint8_t red) {
  present_ = acked = false;
  part_id = 0;
  bus_stuck = !bus_idle(&ext_pullups);
  if (bus_stuck) return false;
  shorted = lines_shorted();
  acked = i2c_read(PART_ID, &part_id, 1);
  present_ = acked && part_id == PART_ID_MAX3010X;
  if (!acked) {   // Diagnose: does it answer with SDA and SCL the other way round?
    uint8_t id = 0;
    SDA_PIN = PIN_WIRE_SCL; SCL_PIN = PIN_WIRE_SDA;
    bool idle_swapped = bus_idle(&ext_pullups);
    swapped = idle_swapped && i2c_read(PART_ID, &id, 1);
    SDA_PIN = PIN_WIRE_SDA; SCL_PIN = PIN_WIRE_SCL;
    bus_idle(&ext_pullups);
  }
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
  uint8_t ptr[3];
  if (!i2c_read(FIFO_WR_PTR, ptr, 3)) return 0;
  uint8_t wr = ptr[0] & 0x1F, ovf = ptr[1], rd = ptr[2] & 0x1F;
  int n = (wr - rd) & 0x1F;
  if (n == 0 && ovf) n = 32;   // FIFO filled up and wrapped
  if (n > max_n) n = max_n;
  int got = 0;
  uint8_t buf[8 * 6];
  while (got < n) {
    int chunk = n - got > 8 ? 8 : n - got;   // 6 bytes each: red (unused), then IR
    if (!i2c_read(FIFO_DATA, buf, chunk * 6)) break;
    for (int i = 0; i < chunk; i++) {
      const uint8_t* s = buf + i * 6 + 3;
      out[got++] = (((uint32_t)s[0] << 16) | ((uint32_t)s[1] << 8) | s[2]) & FULL_SCALE;
    }
  }
  if (got) {
    uint32_t ir = out[got - 1];   // Reflected IR jumps when skin covers the sensor
    skin = skin ? ir > MAX3010X_SKIN_LEVEL * 8 / 10 : ir > MAX3010X_SKIN_LEVEL;
  }
  return got;
}

void Max3010x::write_reg(uint8_t reg, uint8_t v) { i2c_write(reg, v); }

uint8_t Max3010x::read_reg(uint8_t reg) {
  uint8_t v = 0;
  return i2c_read(reg, &v, 1) ? v : 0;
}
