# mood_analyzer.py - Mood/State Detection from Breath Patterns
# Computes stress score (-5 serene to +5 anxious), focus level (0-10),
# and meditation depth (0-10) from thermistor breath data.
#
# SCIENTIFIC BASIS:
# 1. Respiratory Sinus Arrhythmia (RSA): Longer exhales activate parasympathetic
# 2. Heart Rate Variability proxied by breath variability: Lower HRV = more stress
# 3. Attentional control: Consistent timing = focused state
# 4. Mindfulness literature: Slow, rhythmic breathing (6 breaths/min) = meditative

import math

# === STRESS DETECTION ===
# Based on exhale/inhale ratio and breath-to-breath consistency
# Research: E/I ratio > 1.0 correlates with parasympathetic activation
STRESS_RATIO_ANXIOUS = 0.8    # Short exhale relative to inhale = stressed
STRESS_RATIO_CALM = 1.5       # Long exhale = calm (1.5x inhale length)

# Successive breath difference (RMSSD analog for breathing)
# Large jumps between consecutive breaths = stress response
STRESS_RMSSD_ANXIOUS = 2.0    # >2 second jumps between breaths = stressed  
STRESS_RMSSD_CALM = 0.5       # <0.5 second variation = very calm

# === FOCUS DETECTION ===
# Based on consistency of breath timing (like HRV for attention)
# Research: Focused attention produces regular, consistent breathing
FOCUS_CONSISTENCY_THRESHOLD = 0.5  # Std dev of last 5 breaths in seconds (was 0.3)
FOCUS_DRIFT_THRESHOLD = 1.0        # Max acceptable drift from target rhythm

# === MEDITATION DETECTION ===
# Based on breath cycle duration and stability
# Research: 4-6 breaths/min (10-15s cycles) = resonance breathing
MEDITATION_CYCLE_MIN = 6.0    # Below 6s = too fast for meditation
MEDITATION_CYCLE_OPTIMAL = 10.0  # 6 breaths/min = HRV resonance
MEDITATION_STABILITY_THRESHOLD = 0.15  # CV below this = stable rhythm

# Calibration
CALIBRATION_BREATHS = 6  # Reduced for faster feedback


class MoodAnalyzer:
    """Analyzes breath patterns using evidence-based metrics."""

    def __init__(self):
        self.breath_count = 0
        self.is_calibrating = True

        # Configurable thresholds (can be updated via set_thresholds)
        self.calm_ratio = STRESS_RATIO_CALM
        self.calm_variability = STRESS_RMSSD_CALM
        self.focus_consistency = FOCUS_CONSISTENCY_THRESHOLD
        self.calibration_breaths = CALIBRATION_BREATHS

        # Rolling window of recent breaths (short for responsiveness)
        self.recent_breaths = []  # List of (exhale_dur, inhale_dur, total_dur)
        self.max_recent = 5       # Only last 5 breaths for quick response
        
        # Successive difference tracking (RMSSD-like)
        self.last_breath_duration = None
        self.successive_diffs = []
        self.max_diffs = 4
        
        # Current computed metrics
        self.current_ratio = 1.0
        self.current_rmssd = 1.0  # Root mean square of successive differences
        self.current_consistency = 0.5  # Std dev of recent breath durations
        self.current_cycle = 4.0  # Average breath cycle duration

        # Scores
        self._stress_score = 0
        self._focus_score = 5
        self._meditation_score = 0

    def set_thresholds(self, calm_ratio, calm_variability, focus_consistency, calibration_breaths):
        """Update configurable thresholds from settings."""
        self.calm_ratio = calm_ratio
        self.calm_variability = calm_variability
        self.focus_consistency = focus_consistency
        self.calibration_breaths = int(calibration_breaths)
        print("[MOOD] Thresholds: ratio={} var={} focus={} cal={}".format(
            calm_ratio, calm_variability, focus_consistency, calibration_breaths
        ))

    def start_exhale(self):
        """Called when exhale begins."""
        pass  # Not needed with new algorithm

    def record_sample(self, flow_value):
        """Record exhale sample (limited to prevent memory issues)."""
        pass  # Not needed - using duration-based analysis

    def end_exhale(self, exhale_duration, inhale_duration, now):
        """Process completed breath cycle."""
        # Validate breath (filter artifacts)
        if exhale_duration < 0.3 or inhale_duration < 0.2:
            return  # Too short, likely artifact
        if exhale_duration > 15.0 or inhale_duration > 10.0:
            return  # Too long, likely pause/hold
            
        total_duration = exhale_duration + inhale_duration
        self.breath_count += 1
        
        # Store recent breath
        self.recent_breaths.append((exhale_duration, inhale_duration, total_duration))
        if len(self.recent_breaths) > self.max_recent:
            self.recent_breaths.pop(0)
        
        # Track successive differences (RMSSD-like)
        if self.last_breath_duration is not None:
            diff = abs(total_duration - self.last_breath_duration)
            self.successive_diffs.append(diff)
            if len(self.successive_diffs) > self.max_diffs:
                self.successive_diffs.pop(0)
        self.last_breath_duration = total_duration
        
        # Compute all metrics
        self._update_metrics()
        
        # Compute scores
        self._compute_stress_score()
        self._compute_focus_score()
        self._compute_meditation_score()
        
        # End calibration after enough breaths
        if self.breath_count >= self.calibration_breaths:
            self.is_calibrating = False

    def _update_metrics(self):
        """Update derived metrics from recent breaths."""
        if not self.recent_breaths:
            return
            
        # Exhale/Inhale ratio (averaged over recent breaths)
        ratios = [ex / max(0.1, inh) for ex, inh, _ in self.recent_breaths]
        self.current_ratio = sum(ratios) / len(ratios)
        
        # RMSSD (root mean square of successive differences)
        if len(self.successive_diffs) >= 2:
            squared = [d * d for d in self.successive_diffs]
            self.current_rmssd = math.sqrt(sum(squared) / len(squared))
        
        # Consistency (std dev of breath durations)
        durations = [total for _, _, total in self.recent_breaths]
        if len(durations) >= 2:
            mean_dur = sum(durations) / len(durations)
            variance = sum((d - mean_dur) ** 2 for d in durations) / len(durations)
            self.current_consistency = math.sqrt(variance)
        
        # Average cycle duration
        self.current_cycle = sum(durations) / len(durations)

    def _compute_stress_score(self):
        """
        Stress: -5 (serene) to +5 (anxious)
        
        Based on:
        1. E/I Ratio: Low ratio (short exhale) = stress (sympathetic)
        2. RMSSD: High variability between successive breaths = stress
        """
        # Ratio component: higher ratio = more calm = negative stress
        ratio_range = self.calm_ratio - STRESS_RATIO_ANXIOUS
        ratio_norm = (self.current_ratio - STRESS_RATIO_ANXIOUS) / max(0.1, ratio_range)
        ratio_score = 5 - (ratio_norm * 10)  # Invert: high ratio = low stress
        ratio_score = max(-5, min(5, ratio_score))
        
        # RMSSD component: high RMSSD = erratic = stressed
        rmssd_range = STRESS_RMSSD_ANXIOUS - self.calm_variability
        rmssd_norm = (self.current_rmssd - self.calm_variability) / max(0.1, rmssd_range)
        rmssd_score = -5 + (rmssd_norm * 10)  # High RMSSD = high stress
        rmssd_score = max(-5, min(5, rmssd_score))
        
        # Combine: 70% ratio (primary), 30% RMSSD (secondary)
        raw_stress = 0.7 * ratio_score + 0.3 * rmssd_score
        self._stress_score = int(round(max(-5, min(5, raw_stress))))
        
        # Debug: log first few scores
        if self.breath_count <= 10:
            print("[STRESS] ratio={:.2f} rmssd={:.2f} -> ratio_sc={:.1f} rmssd_sc={:.1f} -> {}".format(
                self.current_ratio, self.current_rmssd, ratio_score, rmssd_score, self._stress_score
            ))

    def _compute_focus_score(self):
        """
        Focus: 0 (distracted) to 10 (deeply focused)
        
        Based on breath consistency (std dev of timing).
        Focused attention = regular, consistent breathing rhythm.
        """
        # Low consistency (low std dev) = high focus
        thresh = self.focus_consistency
        if self.current_consistency < thresh * 0.5:
            # Very consistent = high focus
            focus = 9 + min(1, (thresh * 0.5 - self.current_consistency) * 5)
        elif self.current_consistency < thresh:
            # Moderately consistent
            norm = self.current_consistency / thresh
            focus = 6 + (1 - norm) * 3  # 6-9 range
        elif self.current_consistency < thresh * 2:
            # Some variation
            norm = (self.current_consistency - thresh) / thresh
            focus = 3 + (1 - norm) * 3  # 3-6 range
        else:
            # Highly variable = distracted
            focus = max(0, 3 - (self.current_consistency - thresh * 2))
        
        self._focus_score = int(round(max(0, min(10, focus))))
        
        # Debug: log first few
        if self.breath_count <= 10:
            print("[FOCUS] consistency={:.2f}s -> score={}".format(
                self.current_consistency, self._focus_score
            ))

    def _compute_meditation_score(self):
        """
        Meditation: 0 (active) to 10 (deep meditation)
        
        Based on:
        1. Breath cycle duration (longer = deeper)
        2. Rhythm stability (consistent = meditative)
        """
        if len(self.recent_breaths) < 3:
            self._meditation_score = 0
            return
        
        # Cycle duration component (50% weight)
        if self.current_cycle < MEDITATION_CYCLE_MIN:
            # Too fast
            cycle_score = (self.current_cycle / MEDITATION_CYCLE_MIN) * 4
        elif self.current_cycle < MEDITATION_CYCLE_OPTIMAL:
            # Good range, increasing
            progress = (self.current_cycle - MEDITATION_CYCLE_MIN) / (MEDITATION_CYCLE_OPTIMAL - MEDITATION_CYCLE_MIN)
            cycle_score = 4 + progress * 6
        else:
            # At or above optimal
            cycle_score = 10
        
        # Stability component (50% weight)
        cv = self.current_consistency / max(0.1, self.current_cycle)  # Coefficient of variation
        if cv < MEDITATION_STABILITY_THRESHOLD:
            stability_score = 10
        elif cv < MEDITATION_STABILITY_THRESHOLD * 2:
            norm = (cv - MEDITATION_STABILITY_THRESHOLD) / MEDITATION_STABILITY_THRESHOLD
            stability_score = 10 - norm * 5
        else:
            stability_score = max(0, 5 - (cv - MEDITATION_STABILITY_THRESHOLD * 2) * 10)
        
        # Combine
        raw_med = 0.5 * cycle_score + 0.5 * stability_score
        self._meditation_score = int(round(max(0, min(10, raw_med))))

    def get_stress_score(self):
        """Get stress score or None if calibrating."""
        return None if self.is_calibrating else self._stress_score

    def get_focus_score(self):
        """Get focus score or None if calibrating."""
        return None if self.is_calibrating else self._focus_score

    def get_meditation_score(self):
        """Get meditation score or None if calibrating.""" 
        return None if self.is_calibrating else self._meditation_score

    def get_calibrating(self):
        """Returns True if still calibrating."""
        return self.is_calibrating

    def get_calibration_progress(self):
        """Returns calibration progress 0.0 to 1.0."""
        return min(1.0, self.breath_count / CALIBRATION_BREATHS)
