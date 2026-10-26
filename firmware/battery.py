# battery.py - LiPo voltage and charge level
# Reads BAT through a 100k/100k divider on BATTERY_PIN (see hardware/glasses/README.md).

import time
import board
import analogio
import supervisor

from config import BATTERY_PIN, BATTERY_DIVIDER, BATTERY_SAMPLE_S, BATTERY_MIN_V

# Resting LiPo voltage -> charge %, under a light load. Voltage reads high while charging.
_CURVE = (
    (4.20, 100), (4.10, 90), (4.00, 80), (3.90, 65), (3.80, 50), (3.75, 40),
    (3.70, 30), (3.65, 20), (3.60, 12), (3.50, 5), (3.40, 0),
)
_READS = 16       # ADC reads averaged per sample
_SMOOTH = 0.3     # Weight of each new sample (load from the LEDs makes single readings jumpy)


def percent_from_volts(v):
    if v >= _CURVE[0][0]:
        return 100
    for (v_hi, p_hi), (v_lo, p_lo) in zip(_CURVE, _CURVE[1:]):
        if v >= v_lo:
            return int(p_lo + (p_hi - p_lo) * (v - v_lo) / (v_hi - v_lo) + 0.5)
    return 0


class Battery:
    """Smoothed battery voltage. volts is 0 when no battery is seen (switch off, or not fitted)."""

    def __init__(self):
        self._ain = analogio.AnalogIn(getattr(board, BATTERY_PIN)) if BATTERY_PIN else None
        self.volts = 0.0
        self._next = 0.0
        if self._ain:
            self.volts = self._read()

    @property
    def enabled(self):
        return self._ain is not None

    @property
    def present(self):
        return self.volts >= BATTERY_MIN_V

    @property
    def percent(self):
        """0-100, or -1 when no battery is seen."""
        return percent_from_volts(self.volts) if self.present else -1

    @property
    def usb(self):
        """True when connected to a computer over USB (a plain charger isn't detected)."""
        try:
            return supervisor.runtime.usb_connected
        except Exception:
            return False

    def _read(self):
        total = 0
        for _ in range(_READS):
            total += self._ain.value
        return total / _READS / 65535 * self._ain.reference_voltage * BATTERY_DIVIDER

    def tick(self):
        if not self._ain:
            return
        now = time.monotonic()
        if now < self._next:
            return
        self._next = now + BATTERY_SAMPLE_S
        v = self._read()
        # Jump straight to a battery appearing or disappearing; smooth everything else
        if (v >= BATTERY_MIN_V) != self.present:
            self.volts = v
        else:
            self.volts += _SMOOTH * (v - self.volts)
