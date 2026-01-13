# mood_analyzer.py - Raw Breath Metrics for App-side Mood Calculation
# Collects raw breath data that the app uses to compute stress/focus/meditation.
# This keeps firmware simple and allows algorithm updates via app store.

import math

# Calibration - firmware just counts breaths, app decides when enough data
CALIBRATION_BREATHS = 6


class BreathMetrics:
    """Collects raw breath metrics for app-side mood calculation."""

    def __init__(self):
        self.breath_count = 0
        self.is_calibrating = True
        self.calibration_breaths = CALIBRATION_BREATHS
        
        # Current breath metrics (sent to app)
        self.last_exhale_duration = 0.0
        self.last_inhale_duration = 0.0
        self.last_cycle_duration = 0.0
        self.last_smoothness = 100  # 0-100, 100=smooth
        self.last_peak_flow = 0.0   # Absolute peak flow magnitude during exhale
        self.last_symmetry = 50     # 0-100, 0=front-loaded, 100=back-loaded, 50=symmetric
        
        # Flow samples during current exhale (for smoothness/symmetry calculation)
        self._exhale_samples = []
        self._max_samples = 50  # Limit memory usage

    def set_thresholds(self, calm_ratio, calm_variability, focus_consistency, calibration_breaths):
        """Update calibration breaths from settings (other params ignored in v2)."""
        self.calibration_breaths = int(calibration_breaths)
        print("[MOOD] Calibration breaths: {}".format(calibration_breaths))

    def reset(self):
        """Reset calibration state for new session."""
        self.breath_count = 0
        self.is_calibrating = True
        self.last_exhale_duration = 0.0
        self.last_inhale_duration = 0.0
        self.last_cycle_duration = 0.0
        self.last_smoothness = 100
        self.last_peak_flow = 0.0
        self.last_symmetry = 50
        self._exhale_samples = []
        print("[MOOD] Reset calibration")

    def start_exhale(self):
        """Called when exhale begins - reset sample collection."""
        self._exhale_samples = []

    def record_sample(self, flow_value):
        """Record exhale flow sample for smoothness/symmetry calculation."""
        if len(self._exhale_samples) < self._max_samples:
            self._exhale_samples.append(flow_value)

    def end_exhale(self, exhale_duration, inhale_duration, now):
        """Process completed breath cycle - compute raw metrics."""
        # Validate breath (filter artifacts)
        if exhale_duration < 0.3 or inhale_duration < 0.2:
            return  # Too short, likely artifact
        if exhale_duration > 15.0 or inhale_duration > 10.0:
            return  # Too long, likely pause/hold
            
        # Store durations
        self.last_exhale_duration = exhale_duration
        self.last_inhale_duration = inhale_duration
        self.last_cycle_duration = exhale_duration + inhale_duration
        
        # Compute metrics from flow samples
        self.last_smoothness = self._compute_smoothness()
        self.last_peak_flow = self._compute_peak_flow()
        self.last_symmetry = self._compute_symmetry()
        
        self.breath_count += 1
        
        # End calibration after enough breaths
        if self.breath_count >= self.calibration_breaths:
            self.is_calibrating = False
        
        # Debug: log first 10 breaths
        if self.breath_count <= 10:
            print("[BD] #{} ex={:.1f}s pk={:.2f} sm={} sy={}".format(
                self.breath_count,
                exhale_duration,
                self.last_peak_flow,
                self.last_smoothness,
                self.last_symmetry
            ))

    def _compute_smoothness(self):
        """
        Compute exhale smoothness from flow samples.
        Returns 0-100 where 100 = perfectly smooth, 0 = very jerky.
        
        Uses SECOND DERIVATIVE (acceleration): rate of change of rate of change.
        Smooth = constant velocity, jerky = sudden acceleration/deceleration.
        """
        if len(self._exhale_samples) < 7:
            return 100  # Not enough samples for 2nd derivative
        
        samples = self._exhale_samples
        
        # Compute mean absolute flow (to normalize)
        mean_abs_flow = sum(abs(s) for s in samples) / len(samples)
        if mean_abs_flow < 0.05:
            return 100  # Near-zero flow, can't compute
        
        # First derivative: velocity changes
        first_deriv = []
        for i in range(1, len(samples)):
            first_deriv.append(samples[i] - samples[i-1])
        
        # Second derivative: acceleration (rate of change of velocity)
        second_deriv = []
        for i in range(1, len(first_deriv)):
            second_deriv.append(abs(first_deriv[i] - first_deriv[i-1]))
        
        if not second_deriv:
            return 100
        
        # Mean acceleration magnitude
        mean_accel = sum(second_deriv) / len(second_deriv)
        
        # Normalize by flow magnitude
        relative_accel = mean_accel / mean_abs_flow
        
        # Map to 0-100: 0 accel -> 100, 0.2+ accel -> 0
        # Middle ground: 0.2 threshold (original was 0.3, too insensitive)
        smoothness = 100 - int(min(0.2, relative_accel) * 500)
        return max(0, min(100, smoothness))

    def _compute_peak_flow(self):
        """
        Get peak (absolute max) flow magnitude during exhale.
        Higher = deeper breath, lower = shallow breath.
        """
        if not self._exhale_samples:
            return 0.0
        # Exhale flow is typically negative, so we use absolute value
        return max(abs(s) for s in self._exhale_samples)

    def _compute_symmetry(self):
        """
        Compute exhale flow symmetry (where the peak occurs).
        Returns 0-100:
          0 = peak at start (front-loaded, explosive exhale)
          50 = peak in middle (symmetric)
          100 = peak at end (back-loaded, gradual exhale)
        
        Front-loaded (low symmetry) may indicate stress/frustration.
        Back-loaded (high symmetry) may indicate controlled exhale.
        """
        if len(self._exhale_samples) < 3:
            return 50  # Not enough data, assume symmetric
        
        samples = self._exhale_samples
        # Find index of peak (max absolute value)
        abs_samples = [abs(s) for s in samples]
        peak_idx = abs_samples.index(max(abs_samples))
        
        # Normalize to 0-100 scale
        symmetry = int((peak_idx / (len(samples) - 1)) * 100)
        return max(0, min(100, symmetry))

    def get_calibrating(self):
        """Return calibration state."""
        return self.is_calibrating

    def get_raw_metrics(self):
        """Return raw metrics dict for BLE transmission."""
        return {
            "exhale_dur": self.last_exhale_duration,
            "inhale_dur": self.last_inhale_duration,
            "cycle_dur": self.last_cycle_duration,
            "smoothness": self.last_smoothness,
            "peak_flow": self.last_peak_flow,
            "symmetry": self.last_symmetry,
            "calibrating": self.is_calibrating,
        }

    # Legacy methods - return None since app calculates these now
    def get_stress_score(self):
        return None
    
    def get_focus_score(self):
        return None
    
    def get_meditation_score(self):
        return None
