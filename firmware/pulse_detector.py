# pulse_detector.py - Heartbeat detection from a PPG pulse sensor
#
# Sensor: a MAX3010x on I2C (MAX30102/30101/30105), or an analog PulseSensor.
# Signal chain: light low-pass -> slow baseline removal -> adaptive
# peak/trough envelope -> rising-edge threshold with refractory period.
# A beat is reported at its peak, so its amplitude is known when the LEDs fire.

import math
import board
import analogio
import busio
import supervisor

from config import (
    PULSE_SENSOR, PULSE_PIN, PULSE_INVERT, PULSE_MIN_AMP,
    MAX3010X_IR_CURRENT, MAX3010X_RED_CURRENT, MAX3010X_FINGER_LEVEL, MAX3010X_MIN_AMP,
    PULSE_MIN_IBI_MS, PULSE_MAX_IBI_MS, PULSE_SIGNAL_TIMEOUT_MS,
    PULSE_REGULARITY, PULSE_MIN_RHYTHM, PULSE_AMP_CONSISTENCY, PULSE_LOCK_WINDOW,
    PULSE_FILTER_HZ, PULSE_DEBUG_PLOT, PULSE_DEBUG_STATS, PULSE_DEBUG_RAW,
    HEART_PHASE_WINDOW, HEART_PHASE_GAIN, HEART_RATE_EASE, HEART_MAX_RATE_STEP,
    HEART_COAST_S, HEART_RATE_GAIN,
    HRV_BEATS, HRV_MIN_BEATS, HRV_MAX_DEV,
    HEART_STRESS_SMOOTH, HEART_BASELINE_UP, HEART_BASELINE_DOWN,
    HEART_STRESS_SD, HEART_STRESS_BPM_START, HEART_STRESS_BPM_MIN, HEART_STRESS_BPM_MAX,
    HEART_SCALE_DOWN, HEART_SCALE_UP,
    HEART_HRV_WEIGHT, HEART_HRV_BASELINE, HEART_STRESS_HRV_DROP,
)

# Low-pass time constant: keeps the 0.7-2.5 Hz pulse, drops faster noise
_LP_TAU = 1.0 / (2.0 * math.pi * PULSE_FILTER_HZ)

# supervisor.ticks_ms() wraps at 2**29. Unlike time.monotonic() it keeps
# millisecond precision however long the board has been running.
_TICKS_PERIOD = 1 << 29
_TICKS_HALF = _TICKS_PERIOD // 2

IBI_HISTORY = 5  # Beats in the BPM median
_HIST = 64       # Recent filtered samples kept for beat timing (640 ms at 100/s)


def ticks_ms():
    return supervisor.ticks_ms()


def ticks_diff(a, b):
    """a - b in ms, handling ticks_ms() wraparound."""
    d = (a - b) & (_TICKS_PERIOD - 1)
    if d >= _TICKS_HALF:
        d -= _TICKS_PERIOD
    return d


def ticks_add(a, ms):
    return (a + int(ms)) & (_TICKS_PERIOD - 1)


def _alpha(dt, tau):
    """EMA factor for time constant tau (s) at step dt (s)."""
    return dt / (tau + dt)


class AnalogSource:
    """PulseSensor-style analog sensor, sampled once per main-loop pass."""

    name = "analog PulseSensor on " + PULSE_PIN
    sample_ms = None        # Sampled by the main loop; timing is measured
    inverted = False        # Beats rise
    full_scale = 65535
    clips_low = True        # 0 V is also a rail the signal can stick to
    min_amp = PULSE_MIN_AMP
    finger_present = None   # Not detectable
    drift_filter = False    # Output is already AC-coupled by the sensor's circuit

    def __init__(self):
        self._ain = analogio.AnalogIn(getattr(board, PULSE_PIN))

    def read(self, out):
        out.append(self._ain.value)


class Max3010xSource:
    """MAX30102 / MAX30101 / MAX30105 on I2C, IR channel at 100 samples/s."""

    inverted = True         # More blood absorbs more light: IR dips on each beat
    clips_low = False       # A low reading just means no finger
    min_amp = MAX3010X_MIN_AMP
    drift_filter = True     # Raw light level drifts with pressure and temperature

    def __init__(self):
        import max3010x
        self._i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
        try:
            self._sensor = max3010x.MAX3010x(
                self._i2c, ir_current=MAX3010X_IR_CURRENT, red_current=MAX3010X_RED_CURRENT)
        except Exception:
            self._i2c.deinit()
            raise
        self.name = "MAX3010x on I2C"
        self.sample_ms = max3010x.SAMPLE_MS
        self.full_scale = max3010x.FULL_SCALE
        self.finger_present = False

    def read(self, out):
        start = len(out)
        self._sensor.read_ir(out)
        if len(out) > start:
            # Reflected IR jumps when skin covers the sensor (with hysteresis)
            ir = out[-1]
            if self.finger_present:
                self.finger_present = ir > MAX3010X_FINGER_LEVEL * 0.8
            else:
                self.finger_present = ir > MAX3010X_FINGER_LEVEL


def _open_source():
    """Pick the sensor named by PULSE_SENSOR; 'auto' prefers a MAX3010x if one answers."""
    if PULSE_SENSOR in ("auto", "max3010x"):
        try:
            return Max3010xSource()
        except Exception as e:
            if PULSE_SENSOR == "max3010x":
                print("Pulse: MAX3010x not found ({}); heart mode disabled".format(e))
                return None
    try:
        return AnalogSource()
    except Exception as e:
        print("Pulse: analog sensor unavailable ({}); heart mode disabled".format(e))
        return None


class PulseDetector:
    """Detects heartbeats, BPM and relative beat strength from a pulse sensor."""

    def __init__(self):
        self._source = _open_source()
        self.source_name = self._source.name if self._source else "none"
        src = self._source
        self._sign = -1 if (src and src.inverted) != PULSE_INVERT else 1
        self._min_amp = src.min_amp if src else PULSE_MIN_AMP
        self._drift_filter = src.drift_filter if src else False
        self._last_tick = ticks_ms()
        self._stats_reset(self._last_tick)

        self._primed = False  # Filters start from the first sample
        self._finger = True   # Last known finger state (always True if not detectable)
        self._offset = 0      # Large constant removed so floats keep their precision
        self.lp = 0.0         # Low-passed signal
        self.dc = 0.0         # Slow baseline
        self.dc2 = 0.0        # Second baseline stage (removes leftover drift)
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
        self.amps = []        # Recent beat amplitudes
        self.locked_ibi = 0   # Beat interval of the rhythm we're locked onto (0 = not locked)
        self.rise_regular = False
        self._plot_skip = 0

        # Outputs
        self.value = 0.0          # Baseline-removed signal (sensor units)
        self.bpm = 0.0            # 0 when unknown
        self.beat_count = 0       # Increments on every detected beat
        self.beat_confirmed = False  # Last beat fits a regular rhythm (not noise)
        self.beat_strength = 0.5  # 0..1, last beat vs. recent average (0.5 = typical)
        self.beat_amp = 0.0       # Peak-to-peak of the last beat (sensor units)

        # Display rhythm: a steady beat for the LEDs, steered by detected beats
        self._r_ibi = 0.0         # Shown beat interval (ms); 0 = stopped
        self._r_next_ms = 0       # When the next shown beat is due
        self._r_support_ms = 0    # Last detected beat that fitted the rhythm
        self.rhythm_count = 0     # Increments on every shown beat

        # Beat timing for HRV, on the sensor's own sample clock (exact 10 ms
        # steps, unlike main-loop time). Positions are (sample count, fraction)
        # so float precision doesn't run out on long sessions.
        self._sample_ms = src.sample_ms if src else None
        self._n = 0               # Samples processed
        self._hist = [0.0] * _HIST  # Recent filtered samples, indexed by sample count
        self._rise_n = 0          # Sample count at the last beat's rise
        self._fid = None          # Last confirmed beat's position
        self._last_iv = None      # Last clean beat interval (ms)
        self._sq_diffs = []       # Squared successive interval differences
        self.hrv_ms = 0.0         # RMSSD over recent beats; 0 until enough clean beats

        # Stress: heart rate above the resting baseline, plus HRV below its average
        self._hr_avg = 0.0        # Smoothed shown rate (evens out breathing swings)
        self.baseline_bpm = 0.0   # Resting rate: follows drops quickly, rises slowly
        self.baseline_hrv = 0.0   # Long-run average HRV
        # Typical rise above baseline: sets this wearer's stress scale
        self._rise_avg = HEART_STRESS_BPM_START / HEART_STRESS_SD
        self.stress_bpm = HEART_STRESS_BPM_START  # Rise above baseline that shows full stress
        self.stress = 0.0         # 0 (at baseline) .. 1 (stressed)

    def tick(self):
        """Read new sensor samples. Call every main-loop iteration."""
        src = self._source
        if src is None:
            return
        now = ticks_ms()

        samples = []
        src.read(samples)
        n = len(samples)
        if PULSE_DEBUG_RAW and n:
            print("R,{},{}".format(now, ",".join(str(x) for x in samples)))
        if PULSE_DEBUG_STATS:
            for raw in samples:
                if raw < self._st_min:
                    self._st_min = raw
                if raw > self._st_max:
                    self._st_max = raw
                self._st_sum += raw
            self._st_n += n

        finger = src.finger_present is not False
        if finger != self._finger:
            self._finger = finger
            self._primed = False  # Restart filters from the new light level
            if not finger:
                self._lose_signal()
                self.value = self.env_hi = self.env_lo = 0.0
                self._sq_diffs = []
                self.hrv_ms = 0.0

        if finger and n:
            if src.sample_ms:
                # Sensor-timed samples: spread their timestamps back from now
                dt = src.sample_ms / 1000.0
                for i in range(n):
                    self._process(samples[i], now - (n - 1 - i) * src.sample_ms, dt)
            else:
                dt = ticks_diff(now, self._last_tick) / 1000.0
                if dt > 0:
                    self._process(samples[-1], now, min(dt, 0.1))
        self._last_tick = now

        if self.last_rise_ms is not None:
            since = ticks_diff(now, self.last_rise_ms)
            if since > PULSE_SIGNAL_TIMEOUT_MS:
                self._lose_signal()
            elif self.locked_ibi and since > 2.5 * self.locked_ibi:
                self._unlock()  # Two beats missed: rhythm lost

        self._tick_rhythm(now)

        amp = self.env_hi - self.env_lo
        if PULSE_DEBUG_PLOT:
            self._plot(amp)
        if PULSE_DEBUG_STATS and ticks_diff(now, self._st_start) >= 1000:
            self._print_stats(now, amp)

    def _process(self, raw, now, dt):
        """Run one sample through the filters and beat detector."""
        v = self._sign * raw
        if not self._primed:
            self._primed = True
            self._offset = v
            self.lp = self.dc = self.dc2 = 0.0
            self.env_hi = self.env_lo = self.cycle_min = 0.0
            self.armed = True
            self.in_beat = False
        elif abs(v - self._offset - self.dc) > 16384:
            # Re-centre on a big level change so float precision stays fine
            shift = v - self._offset
            self._offset = v
            self.lp -= shift
            self.dc -= shift

        self.lp += _alpha(dt, _LP_TAU) * ((v - self._offset) - self.lp)
        if self._drift_filter:
            # Two-stage baseline removal: slow drift (pressure, temperature) is
            # cut ~25x while the 0.7-2.5 Hz pulse passes almost untouched
            self.dc += _alpha(dt, 0.8) * (self.lp - self.dc)
            y = self.lp - self.dc
            self.dc2 += _alpha(dt, 0.8) * (y - self.dc2)
            x = y - self.dc2
        else:
            self.dc += _alpha(dt, 1.5) * (self.lp - self.dc)      # Wander removal
            x = self.lp - self.dc
        self.value = x
        self._n += 1
        self._hist[self._n % _HIST] = x

        # Envelope jumps to new extremes and relaxes back toward the baseline
        decay = _alpha(dt, 2.0)
        self.env_hi = x if x > self.env_hi else self.env_hi * (1.0 - decay)
        self.env_lo = x if x < self.env_lo else self.env_lo * (1.0 - decay)
        amp = self.env_hi - self.env_lo

        if x < self.cycle_min:
            self.cycle_min = x

        if amp >= self._min_amp:
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

    def _stats_reset(self, now):
        self._st_start = now
        self._st_min = 1 << 30
        self._st_max = 0
        self._st_sum = 0
        self._st_n = 0
        self._st_beats = 0
        self._st_confirmed = 0

    def _print_stats(self, now, amp):
        """Once a second: raw sensor range and what the detector made of it."""
        src = self._source
        n = max(1, self._st_n)
        flags = ""
        if self.locked_ibi:
            flags += "  LOCKED"
        if self._r_ibi:
            flags += "  SHOWING {:.0f} BPM (base {:.0f}, full +{:.0f}) HRV {:.0f} ms (avg {:.0f}) stress {:.2f}".format(
                self.rhythm_bpm, self.baseline_bpm, self.stress_bpm, self.hrv_ms, self.baseline_hrv, self.stress)
        if src.finger_present is False:
            flags += "  NO FINGER"
        elif self._st_n and (self._st_max > 0.985 * src.full_scale or
                             (src.clips_low and self._st_min < 0.015 * src.full_scale)):
            flags += "  CLIPPING"
        lo = self._st_min if self._st_n else 0
        print("PULSE raw {}-{} p-p {} mean {} | {} samples | wave p-p {} | beats {} confirmed {} | last amp {} | {:.0f} BPM{}".format(
            lo, self._st_max, self._st_max - lo, self._st_sum // n, self._st_n,
            int(amp), self._st_beats, self._st_confirmed, int(self.beat_amp), self.bpm, flags))
        self._stats_reset(now)

    def _plot(self, amp):
        """Print (signal, beat threshold, beat marker) for the Mu/Thonny plotter."""
        self._plot_skip = (self._plot_skip + 1) % 3
        if self._plot_skip:
            return
        threshold = self.env_lo + 0.55 * amp if amp >= self._min_amp else 0
        marker = self.env_hi if self.in_beat else self.env_lo
        print((int(self.value), int(threshold), int(marker)))

    def _median_ibi(self):
        s = sorted(self.ibis)
        return s[len(s) // 2]

    def _add_ibi(self, ibi):
        self.ibis.append(ibi)
        if len(self.ibis) > IBI_HISTORY:
            self.ibis.pop(0)
        # Median shrugs off an occasional missed or doubled beat
        self.bpm = 60000.0 / self._median_ibi()

    def _on_rise(self, now):
        """Upstroke crossed threshold: candidate beat; timing is taken here."""
        self.rise_regular = False
        if self.last_rise_ms is not None:
            ibi = ticks_diff(now, self.last_rise_ms)
            if ibi < PULSE_MIN_IBI_MS:
                return  # Dicrotic notch or noise
            if self.locked_ibi:
                # Locked onto a rhythm: only a rise where a beat is due counts,
                # so noise between beats can't break the lock. One missed
                # beat (about twice the interval) is tolerated.
                n = 2 if ibi > 1.5 * self.locked_ibi else 1
                if abs(ibi - n * self.locked_ibi) > PULSE_LOCK_WINDOW * self.locked_ibi:
                    return
                self._add_ibi(ibi / n)
                self.locked_ibi = self._median_ibi()
                self.rise_regular = True
            elif ibi <= PULSE_MAX_IBI_MS:
                self._add_ibi(ibi)
                # Noise triggers at random intervals; real beats keep a rhythm
                med = self._median_ibi()
                recent = self.ibis[-PULSE_MIN_RHYTHM:]
                self.rise_regular = len(recent) >= PULSE_MIN_RHYTHM and all(
                    abs(i - med) <= PULSE_REGULARITY * med for i in recent)
        self.last_rise_ms = now
        self._rise_n = self._n
        self.in_beat = True
        self.beat_max = self.value

    def _on_peak(self, now):
        """Signal turned down after an upstroke: the beat is complete."""
        self.in_beat = False
        beat_amp = self.beat_max - self.cycle_min
        self.cycle_min = self.beat_max  # Track the next trough from here

        if self.amp_ref <= 0:
            self.amp_ref = beat_amp
        self.beat_amp = beat_amp
        self.amps.append(beat_amp)
        if len(self.amps) > IBI_HISTORY:
            self.amps.pop(0)
        rel = beat_amp / max(1.0, self.amp_ref)
        # Settle quickly after a finger is placed, then follow slowly
        self.amp_beats += 1
        self.amp_ref += max(0.08, 1.0 / self.amp_beats) * (beat_amp - self.amp_ref)
        self.beat_strength = max(0.0, min(1.0, (rel - 0.6) / 0.8))

        self.last_beat_ms = now
        if self.locked_ibi and rel > 2.5:
            # Far bigger than recent beats: movement, not pulse
            self._unlock()
            self.beat_confirmed = False
        elif self.locked_ibi:
            self.beat_confirmed = self.rise_regular
        elif self.rise_regular and self._amps_consistent():
            # Steady timing and height: lock onto this rhythm
            self.locked_ibi = self._median_ibi()
            self.beat_confirmed = True
        else:
            self.beat_confirmed = False
        self.beat_count += 1
        if PULSE_DEBUG_STATS:
            self._st_beats += 1
            self._st_confirmed += 1 if self.beat_confirmed else 0
        if self._sample_ms:
            self._hrv_beat()
        self._rhythm_on_beat(now)

    def _fiducial(self):
        """Position of the steepest upstroke: a precise, amplitude-independent beat time."""
        h = self._hist
        lo = max(self._rise_n - 20, self._n - _HIST + 3)
        best = None
        bk = lo
        for k in range(lo, self._n + 1):
            d = h[k % _HIST] - h[(k - 1) % _HIST]
            if best is None or d > best:
                best = d
                bk = k
        # Parabola through the neighbouring slopes places the peak between samples
        frac = 0.0
        if lo < bk < self._n:
            d0 = h[(bk - 1) % _HIST] - h[(bk - 2) % _HIST]
            d2 = h[(bk + 1) % _HIST] - h[bk % _HIST]
            den = d0 - 2.0 * best + d2
            if den < 0:
                frac = 0.5 * (d0 - d2) / den
        return bk, frac

    def _hrv_beat(self):
        """Add a beat to the HRV (RMSSD) window; only consecutive confirmed beats count."""
        prev = self._fid
        if not self.beat_confirmed:
            self._fid = self._last_iv = None
            return
        fid = self._fiducial()
        self._fid = fid
        if prev is None:
            return
        iv = ((fid[0] - prev[0]) + (fid[1] - prev[1])) * self._sample_ms
        ref = self.locked_ibi or iv
        if abs(iv - ref) > HRV_MAX_DEV * ref:
            self._last_iv = None  # Missed or extra beat: don't count this gap
            return
        if self._last_iv is not None:
            d = iv - self._last_iv
            self._sq_diffs.append(d * d)
            if len(self._sq_diffs) > HRV_BEATS:
                self._sq_diffs.pop(0)
            if len(self._sq_diffs) >= HRV_MIN_BEATS:
                self.hrv_ms = math.sqrt(sum(self._sq_diffs) / len(self._sq_diffs))
        self._last_iv = iv

    def _rhythm_on_beat(self, now):
        """Steer the display rhythm with a detected beat; beats off the rhythm are ignored."""
        if not self._r_ibi:
            if self.beat_confirmed and self.locked_ibi:
                # Start on the first confirmed beat, at the locked rate
                self._r_ibi = float(self.locked_ibi)
                self._r_next_ms = now
                self._r_support_ms = now
            return

        # Timing error against the nearest shown beat (last one or next one)
        ibi = self._r_ibi
        err = ticks_diff(now, self._r_next_ms) + ibi
        if err > ibi / 2:
            err -= ibi
        if abs(err) > HEART_PHASE_WINDOW * ibi and not self.beat_confirmed:
            return  # Anomaly: doesn't fit the rhythm
        # Confirmed beats have passed the detector's own rhythm checks, so they
        # always steer (gradually), letting the display re-sync if it drifts
        self._r_next_ms = ticks_add(self._r_next_ms, HEART_PHASE_GAIN * err)
        self._r_support_ms = now

        # Ease the rate toward the detector's rate, but only while it's locked
        # onto a steady rhythm (so a burst of noise can't drag it). Beats that
        # keep landing early or late also pull the rate, so it can't lag behind.
        if self.locked_ibi:
            step = HEART_RATE_EASE * (self.locked_ibi - ibi) + HEART_RATE_GAIN * err
            limit = HEART_MAX_RATE_STEP * ibi
            self._r_ibi = ibi + max(-limit, min(limit, step))

    def _tick_rhythm(self, now):
        """Fire shown beats on schedule; stop when the finger is lifted or support runs out."""
        if not self._r_ibi:
            return
        if not self._finger or ticks_diff(now, self._r_support_ms) > HEART_COAST_S * 1000:
            self._r_ibi = 0.0
            return
        if ticks_diff(now, self._r_next_ms) >= 0:
            self.rhythm_count += 1
            self._update_stress()
            self._r_next_ms = ticks_add(self._r_next_ms, self._r_ibi)
            if ticks_diff(now, self._r_next_ms) >= 0:
                self._r_next_ms = ticks_add(now, self._r_ibi)  # Fell behind (slow loop)

    def _update_stress(self):
        """Once per shown beat: compare rate and HRV with this session's baselines."""
        bpm = self.rhythm_bpm
        if not self._hr_avg:
            self._hr_avg = self.baseline_bpm = bpm
        self._hr_avg += HEART_STRESS_SMOOTH * (bpm - self._hr_avg)
        rate = HEART_BASELINE_DOWN if self._hr_avg < self.baseline_bpm else HEART_BASELINE_UP
        self.baseline_bpm += rate * (self._hr_avg - self.baseline_bpm)
        rise = self._hr_avg - self.baseline_bpm
        rate = HEART_SCALE_DOWN if rise < self._rise_avg else HEART_SCALE_UP
        self._rise_avg += rate * (max(0.0, rise) - self._rise_avg)
        self.stress_bpm = max(HEART_STRESS_BPM_MIN, min(HEART_STRESS_BPM_MAX,
                              HEART_STRESS_SD * self._rise_avg))
        k = max(0.0, min(1.0, rise / self.stress_bpm))

        if self.hrv_ms:
            if not self.baseline_hrv:
                self.baseline_hrv = self.hrv_ms
            self.baseline_hrv += HEART_HRV_BASELINE * (self.hrv_ms - self.baseline_hrv)
            drop = (1.0 - self.hrv_ms / self.baseline_hrv) / HEART_STRESS_HRV_DROP
            k = (1.0 - HEART_HRV_WEIGHT) * k + HEART_HRV_WEIGHT * max(0.0, min(1.0, drop))
        self.stress = k

    @property
    def rhythm_bpm(self):
        """Rate of the shown beat (0 when stopped)."""
        return 60000.0 / self._r_ibi if self._r_ibi else 0.0

    def _amps_consistent(self):
        """Real beats have similar heights; noise peaks vary widely."""
        recent = self.amps[-PULSE_MIN_RHYTHM:]
        if len(recent) < PULSE_MIN_RHYTHM:
            return False
        s = sorted(self.amps)
        med = s[len(s) // 2]
        return all(abs(a - med) <= PULSE_AMP_CONSISTENCY * med for a in recent)

    def _unlock(self):
        self.locked_ibi = 0
        self.ibis = []
        self.amps = []

    def _lose_signal(self):
        self._unlock()
        self.last_rise_ms = None
        self.last_beat_ms = None
        self.in_beat = False
        self.bpm = 0.0
        self.amp_ref = 0.0
        self.amp_beats = 0
        self.beat_strength = 0.5
        self.rise_regular = False
        self.beat_confirmed = False
        self._fid = self._last_iv = None

    def has_signal(self):
        """True while beats are arriving regularly."""
        return self.bpm > 0 and self.last_rise_ms is not None

    def level(self):
        """
        Live analog pulse height: 0 at the trough, ~1 at a typical beat's
        peak, above 1 (up to 1.6) for beats stronger than recent ones.
        """
        ref = self.amp_ref if self.amp_ref > 0 else self.env_hi - self.env_lo
        ref = max(self._min_amp, ref)
        return max(0.0, min(1.6, (self.value - self.env_lo) / ref))

    def normalized(self):
        """Live waveform for the app graph: trough -1, typical peak +1 (flat 0 with no finger)."""
        if not self._finger:
            return 0.0
        return self.level() * 2.0 - 1.0
