import 'dart:math';

/// App-side mood calculation from raw breath metrics.
/// Computes stress, focus, and meditation scores with configurable parameters.
class MoodAnalyzer {
  // Rolling window of recent breaths for calculations
  final List<BreathMetrics> _recentBreaths = [];
  static const int _maxRecent = 10;  // Increased for better smoothing
  
  // Calibration baseline (locked after calibration)
  double? _baselineCycle;  // Average cycle during calibration
  double? _baselinePeakFlow;  // Average peak flow during calibration
  bool _baselineLocked = false;
  
  // Successive differences for RMSSD calculation
  final List<double> _successiveDiffs = [];
  static const int _maxDiffs = 4;
  double? _lastCycleDuration;
  
  // Breath count for calibration
  int _breathCount = 0;
  
  // Current computed scores
  int _stressScore = 0;
  int _focusScore = 5;
  int _meditationScore = 0;
  
  // Current metrics
  double _currentRatio = 1.0;
  double _currentRmssd = 1.0;
  double _currentCycle = 4.0;
  double _currentConsistency = 0.5;
  
  // === CONFIGURABLE THRESHOLDS ===
  
  // Stress calculation
  double calmRatio = 1.5;           // E/I ratio at which stress is lowest
  double anxiousRatio = 0.8;        // E/I ratio at which stress is highest
  double calmVariabilityCv = 0.10;  // CV below this = calm
  double anxiousVariabilityCv = 0.40; // CV above this = stressed
  
  // Stress component weights (must sum to 1.0)
  double stressRatioWeight = 0.40;      // E/I ratio is primary indicator
  double stressDurationWeight = 0.25;    // Duration vs baseline
  double stressSmoothnessWeight = 0.05;  // Reduced - less reliable
  double stressPeakFlowWeight = 0.15;    // Shallow breaths = stressed
  double stressRmssdWeight = 0.15;
  
  // Focus calculation
  double focusConsistencyCv = 0.15; // CV threshold for focus
  
  // Meditation calculation
  double meditationMinCycle = 6.0;  // Below this = too fast
  double meditationOptimalCycle = 10.0; // Optimal cycle for meditation
  double meditationStabilityThreshold = 0.15;
  
  int calibrationBreaths = 6;
  
  bool get isCalibrating => _breathCount < calibrationBreaths;
  int get breathCount => _breathCount;
  
  // === SCORE GETTERS ===
  int get stressScore => _stressScore;
  int get focusScore => _focusScore;
  int get meditationScore => _meditationScore;
  
  // === RAW METRIC GETTERS (for expandable UI) ===
  double get currentRatio => _currentRatio;
  double get currentCycle => _currentCycle;
  double get currentConsistency => _currentConsistency;
  double get currentRmssd => _currentRmssd;
  double? get baselineCycle => _baselineCycle;
  double? get baselinePeakFlow => _baselinePeakFlow;
  bool get isBaselineLocked => _baselineLocked;
  
  // Latest smoothness and peak flow (from most recent breath)
  int get currentSmoothness => _recentBreaths.isEmpty ? 50 : _recentBreaths.last.smoothness;
  double get currentPeakFlow => _recentBreaths.isEmpty ? 0.0 : _recentBreaths.last.peakFlow;
  
  /// Process a new breath with raw metrics
  void recordBreath({
    required double exhaleDuration,
    required double inhaleDuration,
    required double cycleDuration,
    required int smoothness,
    double peakFlow = 0.0,
    int symmetry = 50,
  }) {
    // Validate breath (filter artifacts)
    if (exhaleDuration < 0.3 || inhaleDuration < 0.2) return;
    if (exhaleDuration > 15.0 || inhaleDuration > 10.0) return;
    
    _breathCount++;
    
    // Store recent breath
    _recentBreaths.add(BreathMetrics(
      exhaleDuration: exhaleDuration,
      inhaleDuration: inhaleDuration,
      cycleDuration: cycleDuration,
      smoothness: smoothness,
      peakFlow: peakFlow,
      symmetry: symmetry,
    ));
    if (_recentBreaths.length > _maxRecent) {
      _recentBreaths.removeAt(0);
    }
    
    // Track successive differences (RMSSD-like)
    if (_lastCycleDuration != null) {
      final diff = (cycleDuration - _lastCycleDuration!).abs();
      _successiveDiffs.add(diff);
      if (_successiveDiffs.length > _maxDiffs) {
        _successiveDiffs.removeAt(0);
      }
    }
    _lastCycleDuration = cycleDuration;
    
    // HYBRID ADAPTIVE BASELINE:
    // Initialize from calibration, then adapt SLOWLY (2% per breath) toward current patterns
    if (!_baselineLocked && _breathCount == calibrationBreaths && _recentBreaths.isNotEmpty) {
      // Initial baseline from calibration
      _baselineCycle = _recentBreaths.map((b) => b.cycleDuration).reduce((a, b) => a + b) / _recentBreaths.length;
      _baselinePeakFlow = _recentBreaths.map((b) => b.peakFlow).reduce((a, b) => a + b) / _recentBreaths.length;
      _baselineLocked = true;
    } else if (_baselineLocked) {
      // Slowly adapt baseline toward current values (2% adaptation rate - very slow)
      const adaptRate = 0.02;
      _baselineCycle = _baselineCycle! * (1 - adaptRate) + cycleDuration * adaptRate;
      if (peakFlow > 0 && _baselinePeakFlow != null) {
        _baselinePeakFlow = _baselinePeakFlow! * (1 - adaptRate) + peakFlow * adaptRate;
      }
    }
    
    // Compute all metrics and scores
    _updateMetrics();
    _computeStressScore(smoothness, peakFlow);
    _computeFocusScore();
    _computeMeditationScore();
  }
  
  void _updateMetrics() {
    if (_recentBreaths.isEmpty) return;
    
    // E/I Ratio (average over recent breaths)
    final ratios = _recentBreaths.map((b) => 
      b.inhaleDuration > 0 ? b.exhaleDuration / b.inhaleDuration : 1.0
    ).toList();
    _currentRatio = ratios.reduce((a, b) => a + b) / ratios.length;
    
    // RMSSD
    if (_successiveDiffs.length >= 2) {
      final squared = _successiveDiffs.map((d) => d * d).toList();
      _currentRmssd = sqrt(squared.reduce((a, b) => a + b) / squared.length);
    }
    
    // Consistency (std dev of breath durations)
    final durations = _recentBreaths.map((b) => b.cycleDuration).toList();
    if (durations.length >= 2) {
      final mean = durations.reduce((a, b) => a + b) / durations.length;
      final variance = durations.map((d) => pow(d - mean, 2)).reduce((a, b) => a + b) / durations.length;
      _currentConsistency = sqrt(variance);
    }
    
    // Average cycle duration
    _currentCycle = durations.reduce((a, b) => a + b) / durations.length;
  }
  
  void _computeStressScore(int smoothness, double peakFlow) {
    // 1. Ratio component: higher ratio = more calm = negative stress
    final ratioRange = calmRatio - anxiousRatio;
    final ratioNorm = (_currentRatio - anxiousRatio) / max(0.1, ratioRange);
    double ratioScore = 5 - (ratioNorm * 10);
    ratioScore = ratioScore.clamp(-5, 5);
    
    // 2. Duration component: compare to CALIBRATION baseline (not sliding window)
    double durationScore = 0;
    if (_baselineLocked && _baselineCycle != null) {
      final durationRatio = _currentCycle / max(0.1, _baselineCycle!);
      // <0.7 (faster than calibration) = stressed, >1.3 (slower) = calm
      final durationNorm = (durationRatio - 1.0) / 0.3;
      durationScore = (-durationNorm * 5).clamp(-5, 5);
    }
    
    // 3. Smoothness component: lower smoothness = more stress
    // smoothness 100 = score -5 (calm), smoothness 0 = score +5 (stressed)
    final smoothnessScore = (5 - (smoothness / 10)).clamp(-5.0, 5.0);
    
    // 4. Peak flow component: compare to CALIBRATION baseline
    double peakFlowScore = 0;
    if (_baselineLocked && _baselinePeakFlow != null && _baselinePeakFlow! > 0 && peakFlow > 0) {
      final peakRatio = peakFlow / _baselinePeakFlow!;
      // < 0.7 = shallow vs calibration = stressed, > 1.3 = deeper = calm
      peakFlowScore = ((peakRatio - 1.0) * 5).clamp(-5.0, 5.0);
    }
    
    // 5. RMSSD CV component
    final rmssdCv = _currentRmssd / max(0.1, _currentCycle);
    final rmssdRange = anxiousVariabilityCv - calmVariabilityCv;
    final rmssdNorm = (rmssdCv - calmVariabilityCv) / max(0.01, rmssdRange);
    double rmssdScore = -5 + (rmssdNorm * 10);
    rmssdScore = rmssdScore.clamp(-5, 5);
    
    // 6. ABSOLUTE SHORT BREATH PENALTY
    // Short breaths are stressful regardless of personal baseline
    double absoluteShortPenalty = 0;
    if (_currentCycle < 3.0) {
      absoluteShortPenalty = 3.0;  // Very short = add stress
    } else if (_currentCycle < 4.0) {
      absoluteShortPenalty = 2.0;  // Short = moderate stress
    } else if (_currentCycle < 5.0) {
      absoluteShortPenalty = 1.0;  // Slightly short = mild stress
    }
    
    // Combine with configurable weights
    final rawStress = stressRatioWeight * ratioScore +
                      stressDurationWeight * durationScore +
                      stressSmoothnessWeight * smoothnessScore +
                      stressPeakFlowWeight * peakFlowScore +
                      stressRmssdWeight * rmssdScore +
                      absoluteShortPenalty;
    
    _stressScore = rawStress.round().clamp(-5, 5);
  }
  
  void _computeFocusScore() {
    // Focus = inverse of consistency CV
    final consistencyCv = _currentConsistency / max(0.1, _currentCycle);
    
    // Low CV = high focus
    final cvRange = 0.30 - focusConsistencyCv;
    final cvNorm = (consistencyCv - focusConsistencyCv) / max(0.01, cvRange);
    final rawFocus = 10 - (cvNorm * 10);
    
    _focusScore = rawFocus.round().clamp(0, 10);
  }
  
  void _computeMeditationScore() {
    // Meditation based on cycle duration and stability
    
    // Duration component: 6-10s cycles are meditative
    double durationScore;
    if (_currentCycle < meditationMinCycle) {
      durationScore = 0; // Too fast
    } else if (_currentCycle >= meditationOptimalCycle) {
      durationScore = 10; // Optimal or slower
    } else {
      // Linear interpolation
      durationScore = 10 * (_currentCycle - meditationMinCycle) / (meditationOptimalCycle - meditationMinCycle);
    }
    
    // Stability bonus: consistent breathing deepens meditation
    final consistencyCv = _currentConsistency / max(0.1, _currentCycle);
    double stabilityMultiplier;
    if (consistencyCv <= meditationStabilityThreshold) {
      stabilityMultiplier = 1.0; // Very stable
    } else if (consistencyCv >= 0.4) {
      stabilityMultiplier = 0.5; // Unstable
    } else {
      stabilityMultiplier = 1.0 - ((consistencyCv - meditationStabilityThreshold) / 0.25) * 0.5;
    }
    
    final rawMeditation = durationScore * stabilityMultiplier;
    _meditationScore = rawMeditation.round().clamp(0, 10);
  }
  
  /// Reset analyzer state (for new session)
  void reset() {
    _recentBreaths.clear();
    _successiveDiffs.clear();
    _lastCycleDuration = null;
    _breathCount = 0;
    _stressScore = 0;
    _focusScore = 5;
    _meditationScore = 0;
    // Clear calibration baselines for next session
    _baselineCycle = null;
    _baselinePeakFlow = null;
    _baselineLocked = false;
  }
  
  /// Get stress level label for display
  String get stressLabel {
    if (isCalibrating) return 'Calibrating...';
    if (_stressScore <= -4) return 'SERENE';
    if (_stressScore <= -2) return 'CALM';
    if (_stressScore <= 1) return 'BALANCED';
    if (_stressScore <= 3) return 'TENSE';
    return 'ANXIOUS';
  }

  /// Get focus level label for display
  String get focusLabel {
    if (isCalibrating) return 'Calibrating...';
    if (_focusScore >= 8) return 'DEEP FOCUS';
    if (_focusScore >= 6) return 'FOCUSED';
    if (_focusScore >= 4) return 'ATTENTIVE';
    if (_focusScore >= 2) return 'DISTRACTED';
    return 'SCATTERED';
  }

  /// Get meditation depth label for display
  String get meditationLabel {
    if (isCalibrating) return 'Calibrating...';
    if (_meditationScore >= 8) return 'DEEP';
    if (_meditationScore >= 6) return 'MEDITATIVE';
    if (_meditationScore >= 4) return 'RELAXED';
    if (_meditationScore >= 2) return 'SETTLING';
    return 'ACTIVE';
  }
}

/// A single breath's raw metrics
class BreathMetrics {
  final double exhaleDuration;
  final double inhaleDuration;
  final double cycleDuration;
  final int smoothness;
  final double peakFlow;
  final int symmetry;
  
  BreathMetrics({
    required this.exhaleDuration,
    required this.inhaleDuration,
    required this.cycleDuration,
    required this.smoothness,
    this.peakFlow = 0.0,
    this.symmetry = 50,
  });
}
