# max3010x.py - Minimal I2C driver for MAX30102 / MAX30101 / MAX30105 pulse sensors
#
# Runs the sensor in SpO2 mode (red + IR LEDs) at 100 samples/s and returns
# the IR channel, which gives the clearest pulse. Samples queue in the
# sensor's 32-deep FIFO, so the main loop only needs to read every ~300 ms.

import time

_ADDR = 0x57

_FIFO_WR_PTR = 0x04   # Followed by OVF_COUNTER (0x05) and FIFO_RD_PTR (0x06)
_FIFO_DATA = 0x07
_FIFO_CONFIG = 0x08
_MODE_CONFIG = 0x09
_SPO2_CONFIG = 0x0A
_LED1_PA = 0x0C       # Red
_LED2_PA = 0x0D       # IR
_PART_ID = 0xFF

_PART_ID_MAX3010X = 0x15  # Shared by MAX30101, MAX30102 and MAX30105

_MODE_RESET = 0x40
_MODE_SPO2 = 0x03     # Red + IR

_BYTES_PER_SAMPLE = 6  # 3 bytes red, 3 bytes IR
_FIFO_DEPTH = 32

FULL_SCALE = (1 << 18) - 1
SAMPLE_MS = 10         # 100 samples/s


class MAX3010x:
    """MAX3010x pulse sensor streaming IR samples at 100 samples/s."""

    def __init__(self, i2c, ir_current=0x1F, red_current=0x01, address=_ADDR):
        self._i2c = i2c
        self._addr = address
        self._out = bytearray(2)
        self._in = bytearray(3)
        self._fifo = bytearray(_FIFO_DEPTH * _BYTES_PER_SAMPLE)

        part = self._read_reg(_PART_ID)
        if part != _PART_ID_MAX3010X:
            raise RuntimeError("Unexpected MAX3010x part id 0x{:02X}".format(part))

        self._write_reg(_MODE_CONFIG, _MODE_RESET)
        deadline = time.monotonic() + 0.1
        while self._read_reg(_MODE_CONFIG) & _MODE_RESET and time.monotonic() < deadline:
            pass

        # Average pairs of samples (200 -> 100 samples/s); keep the newest if the FIFO fills
        self._write_reg(_FIFO_CONFIG, (0b001 << 5) | 0x10)
        # ADC range 4096 nA, 200 samples/s, 411 us LED pulses (18-bit resolution)
        self._write_reg(_SPO2_CONFIG, (0b01 << 5) | (0b010 << 2) | 0b11)
        self.set_led_current(ir_current, red_current)
        self._write_reg(_MODE_CONFIG, _MODE_SPO2)
        self.clear_fifo()

    def set_led_current(self, ir, red):
        """LED drive in 0.2 mA steps (0x00-0xFF). Only IR is read; red can stay near off."""
        self._write_reg(_LED2_PA, ir)
        self._write_reg(_LED1_PA, red)

    def clear_fifo(self):
        for reg in (0x04, 0x05, 0x06):
            self._write_reg(reg, 0)

    def read_ir(self, out):
        """Append new IR samples (oldest first) to out; return how many."""
        self._read_into(_FIFO_WR_PTR, self._in, 3)
        wr, ovf, rd = self._in[0] & 0x1F, self._in[1], self._in[2] & 0x1F
        n = (wr - rd) & 0x1F
        if n == 0 and ovf:
            n = _FIFO_DEPTH  # FIFO filled up and wrapped
        if n == 0:
            return 0

        f = self._fifo
        self._read_into(_FIFO_DATA, f, n * _BYTES_PER_SAMPLE)
        for i in range(n):
            b = i * _BYTES_PER_SAMPLE + 3
            out.append(((f[b] << 16) | (f[b + 1] << 8) | f[b + 2]) & FULL_SCALE)
        return n

    def _write_reg(self, reg, value):
        self._out[0] = reg
        self._out[1] = value
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(self._addr, self._out)
        finally:
            self._i2c.unlock()

    def _read_reg(self, reg):
        self._read_into(reg, self._in, 1)
        return self._in[0]

    def _read_into(self, reg, buf, count):
        self._out[0] = reg
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto_then_readfrom(self._addr, self._out, buf, out_end=1, in_end=count)
        finally:
            self._i2c.unlock()
