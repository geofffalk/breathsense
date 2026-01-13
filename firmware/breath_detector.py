# breath_detector.py - Breath detection using thermistor
# Preserves tuned algorithms from blinkersgame/circuitpython/breath_monitor.py

import time
import math
import board
import analogio

from config import (
    FS_HZ, ALPHA_FAST, ALPHA_SLOW, ALPHA_FLOW, DERIV_GAIN,
    TH_FRAC_START, TH_FRAC_END, MIN_PHASE_S,
    EMA_MAG, LEAK_DECAY, SCALE_FLOOR,
    IDLE_MAG_FRAC, IDLE_SLOPE_FRAC, IDLE_HOLD_S,
    ADC_MAX, VSUP, R_REF, R0, BETA, T0_C,
    DEFAULT_VERY_SHORT_MAX, DEFAULT_SHORT_MAX,
    DEFAULT_MEDIUM_MAX, DEFAULT_LONG_MAX,
    SENSITIVITY_PRESETS,
)
from mood_analyzer import MoodAnalyzer

# Phase constants
PH_IDLE = 0
PH_INH = 1  # Inhale
PH_EXH = 2  # Exhale

# Sampling
DT = 1.0 / FS_HZ

# Thermistor ADC
_ain = analogio.AnalogIn(board.A0)


def read_temp_c():
    """Read temperature from thermistor in Celsius."""
    raw = _ain.value
    raw = max(1, min(int(ADC_MAX - 1), raw))
    v = (raw / ADC_MAX) * VSUP
    r_ntc = (R_REF * v) / max(1e-6, (VSUP - v))
    inv_t = (1.0 / (T0_C + 273.15)) + (1.0 / BETA) * math.log(r_ntc / R0)
    return (1.0 / inv_t) - 273.15


class BreathDetector:
    """Detects breath phases (inhale/exhale/idle) from thermistor readings."""

    def __init__(self):
        # Filter state
        self.t_fast = 0.0
        self.t_slow = 0.0
        self.prev_flow = 0.0
        self.flow_lp = 0.0

        # Scaling / peaks
        self.scale_ex = 0.10
        self.scale_in = 0.10
        self.peak_ex = 0.10
        self.peak_in = 0.10

        # Phase state
        self.phase = PH_IDLE
        self.t_phase_start = time.monotonic()
        self.refrac_until = 0.0

        # Metrics
        self.peak_val = 0.0
        self.prev_norm = 0.0
        self.idle_hold_start = None
        self.norm = 0.0  # Current normalized flow

        # Exhale duration tracking for color selection
        self.last_exhale_duration = 2.0
        self.exhale_start_time = None

        # Inhale duration tracking for stress analysis
        self.last_inhale_duration = 2.0
        self.inhale_start_time = None

        # Stress analyzer
        self.mood = MoodAnalyzer()

        # Off-head (unworn) detection
        # Detects when headset is not being worn based on short/artifact exhales
        self.unworn = False
        self.short_streak = 0           # Count of consecutive short exhales
        self._artifact_short_max = 0.6  # Exhale shorter than this = artifact
        self._unworn_streak_needed = 6  # How many short exhales to mark unworn
        self._worn_recovery_min = 1.5   # Normal exhale length to clear unworn
        self._last_exhale_time = None
        self._last_exhale_short = False

        # Color thresholds (can be updated via settings)
        self.very_short_max = DEFAULT_VERY_SHORT_MAX
        self.short_max = DEFAULT_SHORT_MAX
        self.medium_max = DEFAULT_MEDIUM_MAX
        self.long_max = DEFAULT_LONG_MAX

        # Tunable parameters (can be updated via sensitivity presets)
        self.alpha_flow = ALPHA_FLOW
        self.deriv_gain = DERIV_GAIN
        self.th_start = TH_FRAC_START
        self.th_end = TH_FRAC_END

        # Timing
        self.next_proc = time.monotonic()

    def apply_sensitivity(self, preset_id: int):
        """Apply a sensitivity preset (0-9)."""
        preset_id = max(0, min(9, preset_id))
        af, dg, ts, te = SENSITIVITY_PRESETS[preset_id]
        self.alpha_flow = af
        self.deriv_gain = dg
        self.th_start = ts
        self.th_end = te

        # Reset filters
        self.t_fast = 0.0
        self.t_slow = 0.0
        self.prev_flow = 0.0
        self.flow_lp = 0.0

    def apply_color_thresholds(self, very_short, short, medium, long):
        """Update color-to-depth thresholds."""
        self.very_short_max = float(very_short)
        self.short_max = float(short)
        self.medium_max = float(medium)
        self.long_max = float(long)

    def get_depth_color(self, exhale_duration: float = None) -> int:
        """
        Get color code based on exhale duration.
        Returns: 0=red, 1=white, 2=light_blue, 3=purple, 4=deep_blue
        """
        dur = exhale_duration if exhale_duration is not None else self.last_exhale_duration
        if dur <= self.very_short_max:
            return 0  # Red
        elif dur <= self.short_max:
            return 1  # White
        elif dur <= self.medium_max:
            return 2  # Light blue
        elif dur <= self.long_max:
            return 3  # Purple
        else:
            return 4  # Deep blue

    def tick(self):
        """
        Process one tick of breath detection.
        Call this frequently (at least 100Hz).
        Returns True if a phase transition occurred.
        """
        now = time.monotonic()
        transition = False

        while now >= self.next_proc:
            self.next_proc += DT

            # Read temperature
            t = read_temp_c()

            # Fast/slow EMA
            self.t_fast = (1.0 - ALPHA_FAST) * self.t_fast + ALPHA_FAST * t
            self.t_slow = (1.0 - ALPHA_SLOW) * self.t_slow + ALPHA_SLOW * t

            # Flow = negative derivative (inhale = positive)
            flow = -(self.t_fast - self.t_slow)

            # Derivative
            dflow = (flow - self.prev_flow) / DT
            self.prev_flow = flow

            # Low-pass with derivative boost
            self.flow_lp = (
                (1.0 - self.alpha_flow) * self.flow_lp
                + self.alpha_flow * (flow + self.deriv_gain * dflow)
            )
            
            # Smooth flow_lp slightly to reduce jitter in normalization
            # self.flow_lp = 0.8 * self.flow_lp + 0.2 * flow # Optional extra smoothing

            # Update scaling
            if self.flow_lp > 0.0:
                self.peak_ex = max(self.peak_ex * LEAK_DECAY, self.flow_lp)
                self.scale_ex = max(
                    (1.0 - EMA_MAG) * self.scale_ex + EMA_MAG * self.peak_ex,
                    SCALE_FLOOR,
                )
            elif self.flow_lp < 0.0:
                mag = -self.flow_lp
                self.peak_in = max(self.peak_in * LEAK_DECAY, mag)
                self.scale_in = max(
                    (1.0 - EMA_MAG) * self.scale_in + EMA_MAG * self.peak_in,
                    SCALE_FLOOR,
                )

            # Normalize
            denom = self.scale_ex if self.flow_lp >= 0 else self.scale_in
            denom = max(1e-6, denom)
            norm = self.flow_lp / denom
            dnorm = (norm - self.prev_norm) / DT
            self.prev_norm = norm
            self.norm = norm

            # Feed samples to stress analyzer during exhale phase
            if self.phase == PH_EXH:
                self.mood.record_sample(self.flow_lp)

            # Update peak
            self.peak_val = max(self.peak_val, abs(norm))

            # Phase detection
            phase_age = now - self.t_phase_start

            # Check for idle
            if self.phase != PH_IDLE:
                if abs(norm) <= IDLE_MAG_FRAC and abs(dnorm) <= IDLE_SLOPE_FRAC:
                    if self.idle_hold_start is None:
                        self.idle_hold_start = now
                    if (now - self.idle_hold_start) >= (IDLE_HOLD_S * 1.5) and phase_age >= MIN_PHASE_S:
                        # Transition to idle
                        if self.phase == PH_EXH and self.exhale_start_time is not None:
                            self.last_exhale_duration = now - self.exhale_start_time
                            self._record_exhale(self.last_exhale_duration, now)
                        self.phase = PH_IDLE
                        self.t_phase_start = now
                        self.peak_val = 0.0
                        transition = True
                else:
                    self.idle_hold_start = None

            # Refractory period
            if now < self.refrac_until:
                continue

            # Detect inhale start
            if self.phase != PH_INH and norm > self.th_start:
                if phase_age >= MIN_PHASE_S or self.phase == PH_IDLE:
                    # End previous exhale and record it
                    if self.phase == PH_EXH and self.exhale_start_time is not None:
                        self.last_exhale_duration = now - self.exhale_start_time
                        self._record_exhale(self.last_exhale_duration, now)
                        # Feed stress analyzer with completed breath
                        self.mood.end_exhale(
                            self.last_exhale_duration,
                            self.last_inhale_duration,
                            now
                        )
                        # Debug: log breath count
                        if self.mood.breath_count <= 10:
                            print("[BD] Breath #{} ex={:.1f}s in={:.1f}s cal={}".format(
                                self.mood.breath_count,
                                self.last_exhale_duration,
                                self.last_inhale_duration,
                                self.mood.is_calibrating
                            ))
                    self.phase = PH_INH
                    self.t_phase_start = now
                    self.inhale_start_time = now  # Track inhale start
                    self.peak_val = 0.0
                    self.idle_hold_start = None
                    self.refrac_until = now + MIN_PHASE_S * 0.5
                    transition = True

            # Detect exhale start
            elif self.phase != PH_EXH and norm < -self.th_start:
                if phase_age >= MIN_PHASE_S or self.phase == PH_IDLE:
                    # Record inhale duration before transitioning
                    if self.phase == PH_INH and self.inhale_start_time is not None:
                        self.last_inhale_duration = now - self.inhale_start_time
                    self.phase = PH_EXH
                    self.t_phase_start = now
                    self.exhale_start_time = now
                    self.peak_val = 0.0
                    self.idle_hold_start = None
                    self.refrac_until = now + MIN_PHASE_S * 0.5
                    # Start collecting exhale samples for stress analysis
                    self.mood.start_exhale()
                    transition = True

        return transition

    def _record_exhale(self, duration_s: float, now: float):
        """
        Record an exhale and update unworn detection.
        Called at the end of each exhale.
        """
        short_limit = self._artifact_short_max

        # Detect very short exhales (artifacts / not worn)
        if duration_s <= short_limit:
            self.short_streak += 1
            if self.short_streak >= self._unworn_streak_needed:
                self.unworn = True
            self._last_exhale_time = now
            self._last_exhale_short = True
            return

        # Normal exhale - reset streak
        self._last_exhale_time = now
        self._last_exhale_short = False
        self.short_streak = 0

        # If we thought unworn but now see proper exhale -> clear it
        if self.unworn and duration_s >= self._worn_recovery_min:
            self.unworn = False

    def get_state(self):
        """Get current breath state as a dict."""
        stress_score = self.mood.get_stress_score()
        focus_score = self.mood.get_focus_score()
        meditation_score = self.mood.get_meditation_score()
        return {
            "phase": self.phase,
            "norm": self.norm,
            "depth_color": self.get_depth_color(),
            "exhale_duration": self.last_exhale_duration,
            "unworn": self.unworn,
            "stress_score": stress_score if stress_score is not None else -99,
            "focus_score": focus_score if focus_score is not None else -1,
            "meditation_score": meditation_score if meditation_score is not None else -1,
            "calibrating": self.mood.get_calibrating(),
        }
