# pulse_detector.py - Heartbeat detection from an analog PulseSensor (PPG)
#
# Signal chain: light low-pass -> slow baseline removal -> adaptive
# peak/trough envelope -> rising-edge threshold with refractory period.
# A beat is reported at its peak, so its amplitude is known when the LEDs fire.

import board
import analogio
import supervisor

from config import (
    PULSE_PIN, PULSE_INVERT, PULSE_MIN_AMP,
    PULSE_MIN_IBI_MS, PULSE_MAX_IBI_MS, PULSE_SIGNAL_TIMEOUT_MS,
)

# supervisor.ticks_ms() wraps at 2**29. Unlike time.monotonic() it keeps
# millisecond precision however long the board has been running.
_TICKS_PERIOD = 1 << 29
_TICKS_HALF = _TICKS_PERIOD // 2

IBI_HISTORY = 5  # Beats in the BPM median


def ticks_ms():
    return supervisor.ticks_ms()


def ticks_diff(a, b):
    """a - b in ms, handling ticks_ms() wraparound."""
    d = (a - b) & (_TICKS_PERIOD - 1)
    if d >= _TICKS_HALF:
        d -= _TICKS_PERIOD
    return d


def _alpha(dt, tau):
    """EMA factor for time constant tau (s) at step dt (s)."""
    return dt / (tau + dt)


class PulseDetector:
    """Detects heartbeats, BPM and relative beat strength from a PulseSensor."""

    def __init__(self):
        self._ain = analogio.AnalogIn(getattr(board, PULSE_PIN))
        self._last_tick = ticks_ms()

        raw = self._read()
        self.lp = raw         # Low-passed signal
        self.dc = raw         # Slow baseline
        self.env_hi = 0.0     # Envelope (relative to baseline)
        self.env_lo = 0.0

        self.armed = True
        self.in_beat = False
        self.beat_max = 0.0
        self.cycle_min = 0.0
        self.last_rise_ms = None
        self.last_beat_ms = None
        self.ibis = []
        self.amp_ref = 0.0    # Slow average beat amplitude
        self.amp_beats = 0    # Beats folded into amp_ref

        # Outputs
        self.value = 0.0          # Baseline-removed signal (ADC units)
        self.bpm = 0.0            # 0 when unknown
        self.beat_count = 0       # Increments on every detected beat
        self.beat_strength = 0.5  # 0..1, last beat vs. recent average (0.5 = typical)

    def _read(self):
        v = float(self._ain.value)
        return 65535.0 - v if PULSE_INVERT else v

    def tick(self):
        """Sample the sensor. Call every main-loop iteration (~100 Hz)."""
        now = ticks_ms()
        dt = ticks_diff(now, self._last_tick) / 1000.0
        if dt <= 0:
            return
        self._last_tick = now
        dt = min(dt, 0.1)

        self.lp += _alpha(dt, 0.025) * (self._read() - self.lp)  # ~6 Hz low-pass
        self.dc += _alpha(dt, 1.5) * (self.lp - self.dc)          # Wander removal
        x = self.lp - self.dc
        self.value = x

        # Envelope jumps to new extremes and relaxes back toward the baseline
        decay = _alpha(dt, 2.0)
        self.env_hi = x if x > self.env_hi else self.env_hi * (1.0 - decay)
        self.env_lo = x if x < self.env_lo else self.env_lo * (1.0 - decay)
        amp = self.env_hi - self.env_lo

        if x < self.cycle_min:
            self.cycle_min = x

        if amp >= PULSE_MIN_AMP:
            if self.armed and x > self.env_lo + 0.55 * amp:
                self.armed = False
                self._on_rise(now)
            elif not self.armed and x < self.env_lo + 0.35 * amp:
                self.armed = True

        if self.in_beat:
            if x > self.beat_max:
                self.beat_max = x
            elif x < self.beat_max - 0.12 * amp:
                self._on_peak(now)

        if self.last_rise_ms is not None and ticks_diff(now, self.last_rise_ms) > PULSE_SIGNAL_TIMEOUT_MS:
            self._lose_signal()

    def _median_ibi(self):
        s = sorted(self.ibis)
        return s[len(s) // 2]

    def _on_rise(self, now):
        """Upstroke crossed threshold: candidate beat; timing is taken here."""
        if self.last_rise_ms is not None:
            ibi = ticks_diff(now, self.last_rise_ms)
            if ibi < PULSE_MIN_IBI_MS:
                return  # Dicrotic notch or noise
            if ibi <= PULSE_MAX_IBI_MS:
                self.ibis.append(ibi)
                if len(self.ibis) > IBI_HISTORY:
                    self.ibis.pop(0)
                # Median shrugs off an occasional missed or doubled beat
                self.bpm = 60000.0 / self._median_ibi()
        self.last_rise_ms = now
        self.in_beat = True
        self.beat_max = self.value

    def _on_peak(self, now):
        """Signal turned down after an upstroke: the beat is complete."""
        self.in_beat = False
        beat_amp = self.beat_max - self.cycle_min
        self.cycle_min = self.beat_max  # Track the next trough from here

        if self.amp_ref <= 0:
            self.amp_ref = beat_amp
        rel = beat_amp / max(1.0, self.amp_ref)
        # Settle quickly after a finger is placed, then follow slowly
        self.amp_beats += 1
        self.amp_ref += max(0.08, 1.0 / self.amp_beats) * (beat_amp - self.amp_ref)
        self.beat_strength = max(0.0, min(1.0, (rel - 0.6) / 0.8))

        self.last_beat_ms = now
        self.beat_count += 1

    def _lose_signal(self):
        self.last_rise_ms = None
        self.last_beat_ms = None
        self.in_beat = False
        self.ibis = []
        self.bpm = 0.0
        self.amp_ref = 0.0
        self.amp_beats = 0
        self.beat_strength = 0.5

    def has_signal(self):
        """True while beats are arriving regularly."""
        return self.bpm > 0 and self.last_rise_ms is not None

    def level(self):
        """
        Live analog pulse height: 0 at the trough, ~1 at a typical beat's
        peak, above 1 (up to 1.6) for beats stronger than recent ones.
        """
        ref = self.amp_ref if self.amp_ref > 0 else self.env_hi - self.env_lo
        ref = max(PULSE_MIN_AMP, ref)
        return max(0.0, min(1.6, (self.value - self.env_lo) / ref))

    def normalized(self):
        """Live waveform for the app graph: trough -1, typical peak +1."""
        return self.level() * 2.0 - 1.0
