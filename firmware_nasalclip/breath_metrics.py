# breath_metrics.py - Raw Breath Metrics for App-side Mood Calculation
# Collects raw breath data that the app uses to compute stress/focus/meditation.

import math

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
        self.last_symmetry = 50     # 0-100, 50=symmetric
        
        # Flow samples during current exhale
        self._exhale_samples = []
        self._max_samples = 50

    def set_thresholds(self, calm_ratio, calm_variability, focus_consistency, calibration_breaths):
        """Update calibration breaths from settings."""
        self.calibration_breaths = int(calibration_breaths)

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

    def start_exhale(self):
        """Called when exhale begins."""
        self._exhale_samples = []

    def record_sample(self, flow_value):
        """Record exhale flow sample."""
        if len(self._exhale_samples) < self._max_samples:
            self._exhale_samples.append(flow_value)

    def end_exhale(self, exhale_duration, inhale_duration, now):
        """Process completed breath cycle."""
        if exhale_duration < 0.3 or inhale_duration < 0.2:
            return
        if exhale_duration > 15.0 or inhale_duration > 10.0:
            return
            
        self.last_exhale_duration = exhale_duration
        self.last_inhale_duration = inhale_duration
        self.last_cycle_duration = exhale_duration + inhale_duration
        
        self.last_smoothness = self._compute_smoothness()
        self.last_peak_flow = self._compute_peak_flow()
        self.last_symmetry = self._compute_symmetry()
        
        self.breath_count += 1
        
        if self.breath_count >= self.calibration_breaths:
            self.is_calibrating = False

    def _compute_smoothness(self):
        """Compute exhale smoothness (0-100)."""
        if len(self._exhale_samples) < 7:
            return 100
        
        samples = self._exhale_samples
        mean_abs_flow = sum(abs(s) for s in samples) / len(samples)
        if mean_abs_flow < 0.05:
            return 100
        
        first_deriv = []
        for i in range(1, len(samples)):
            first_deriv.append(samples[i] - samples[i-1])
        
        second_deriv = []
        for i in range(1, len(first_deriv)):
            second_deriv.append(abs(first_deriv[i] - first_deriv[i-1]))
        
        if not second_deriv:
            return 100
        
        mean_accel = sum(second_deriv) / len(second_deriv)
        relative_accel = mean_accel / mean_abs_flow
        smoothness = 100 - int(min(0.2, relative_accel) * 500)
        return max(0, min(100, smoothness))

    def _compute_peak_flow(self):
        """Get peak flow magnitude during exhale."""
        if not self._exhale_samples:
            return 0.0
        return max(abs(s) for s in self._exhale_samples)

    def _compute_symmetry(self):
        """Compute exhale flow symmetry (0-100)."""
        if len(self._exhale_samples) < 3:
            return 50
        
        samples = self._exhale_samples
        abs_samples = [abs(s) for s in samples]
        peak_idx = abs_samples.index(max(abs_samples))
        symmetry = int((peak_idx / (len(samples) - 1)) * 100)
        return max(0, min(100, symmetry))

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
