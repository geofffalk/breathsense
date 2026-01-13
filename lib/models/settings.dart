// Settings models for the breathing app

/// Open Breathing mode settings (color-to-depth thresholds in seconds)
class OpenBreathingSettings {
  double veryShortMax; // seconds - breath <= this is red
  double shortMax; // seconds - breath <= this is white
  double mediumMax; // seconds - breath <= this is light blue
  double longMax; // seconds - breath <= this is purple
  // above longMax is deep blue
  int sensitivity; // 0-9 preset

  OpenBreathingSettings({
    this.veryShortMax = 2.0,
    this.shortMax = 3.5,
    this.mediumMax = 5.0,
    this.longMax = 6.5,
    this.sensitivity = 5,
  });

  /// Convert to BLE message format: "S,F,{veryShort},{short},{medium},{long},{sensitivity}\n"
  String toMessage() {
    return 'S,F,$veryShortMax,$shortMax,$mediumMax,$longMax,$sensitivity\n';
  }

  OpenBreathingSettings copyWith({
    double? veryShortMax,
    double? shortMax,
    double? mediumMax,
    double? longMax,
    int? sensitivity,
  }) {
    return OpenBreathingSettings(
      veryShortMax: veryShortMax ?? this.veryShortMax,
      shortMax: shortMax ?? this.shortMax,
      mediumMax: mediumMax ?? this.mediumMax,
      longMax: longMax ?? this.longMax,
      sensitivity: sensitivity ?? this.sensitivity,
    );
  }
}

/// Guided Breathing mode settings (durations in seconds)
class GuidedBreathingSettings {
  double inhaleLength; // seconds
  double holdAfterInhale; // seconds
  double exhaleLength; // seconds
  double holdAfterExhale; // seconds
  int ledStart; // 0-9
  int ledEnd; // 0-9
  int colorScheme; // 0=Default, 1=High Contrast, 2=Cool Tones

  GuidedBreathingSettings({
    this.inhaleLength = 5.0,
    this.holdAfterInhale = 5.0,
    this.exhaleLength = 5.0,
    this.holdAfterExhale = 5.0,
    this.ledStart = 2,
    this.ledEnd = 9,
    this.colorScheme = 0,
  });

  /// Convert to BLE message format: "S,G,{inhale},{holdIn},{exhale},{holdOut},{ledStart},{ledEnd}\n"
  String toMessage() {
    return 'S,G,$inhaleLength,$holdAfterInhale,$exhaleLength,$holdAfterExhale,$ledStart,$ledEnd\n';
  }

  GuidedBreathingSettings copyWith({
    double? inhaleLength,
    double? holdAfterInhale,
    double? exhaleLength,
    double? holdAfterExhale,
    int? ledStart,
    int? ledEnd,
    int? colorScheme,
  }) {
    return GuidedBreathingSettings(
      inhaleLength: inhaleLength ?? this.inhaleLength,
      holdAfterInhale: holdAfterInhale ?? this.holdAfterInhale,
      exhaleLength: exhaleLength ?? this.exhaleLength,
      holdAfterExhale: holdAfterExhale ?? this.holdAfterExhale,
      ledStart: ledStart ?? this.ledStart,
      ledEnd: ledEnd ?? this.ledEnd,
      colorScheme: colorScheme ?? this.colorScheme,
    );
  }
}

/// Breathing mode enum
enum BreathingMode {
  open, // Open Breathing mode
  guided, // Guided Breathing mode
}

extension BreathingModeExtension on BreathingMode {
  /// Convert to BLE message format
  String toMessage() {
    switch (this) {
      case BreathingMode.open:
        return 'M,F\n';
      case BreathingMode.guided:
        return 'M,G\n';
    }
  }

  String get displayName {
    switch (this) {
      case BreathingMode.open:
        return 'Open Breathing';
      case BreathingMode.guided:
        return 'Guided Breathing';
    }
  }
}

/// Mood detection settings (thresholds for stress/focus/meditation)
class MoodDetectionSettings {
  // Basic settings
  double calmRatio; // E/I ratio for calm detection (higher = calmer required)
  double calmVariability; // RMSSD CV threshold for calm (e.g., 0.10 = 10% relative variation)
  double focusConsistency; // CV threshold for focus (e.g., 0.15 = 15% relative variation)
  int calibrationBreaths; // Number of breaths before showing scores
  
  // Advanced mode toggle
  bool advancedMode; // When true, show advanced weight sliders
  
  // Stress calculation weights (only used in advanced mode, must sum to 1.0)
  double stressRatioWeight;      // E/I ratio contribution
  double stressDurationWeight;   // Breath duration contribution
  double stressSmoothnessWeight; // Exhale smoothness contribution
  double stressPeakFlowWeight;   // Breath depth contribution
  double stressRmssdWeight;      // Variability contribution

  MoodDetectionSettings({
    this.calmRatio = 1.5,
    this.calmVariability = 0.10, // CV: 10% relative variation = calm
    this.focusConsistency = 0.15, // CV: 15% relative variation = focused
    this.calibrationBreaths = 6,
    this.advancedMode = false,
    this.stressRatioWeight = 0.35,
    this.stressDurationWeight = 0.20,
    this.stressSmoothnessWeight = 0.15,
    this.stressPeakFlowWeight = 0.15,
    this.stressRmssdWeight = 0.15,
  });

  /// Convert to BLE message format (basic settings only - weights are app-side)
  String toMessage() {
    return 'S,M,$calmRatio,$calmVariability,$focusConsistency,$calibrationBreaths\n';
  }

  MoodDetectionSettings copyWith({
    double? calmRatio,
    double? calmVariability,
    double? focusConsistency,
    int? calibrationBreaths,
    bool? advancedMode,
    double? stressRatioWeight,
    double? stressDurationWeight,
    double? stressSmoothnessWeight,
    double? stressPeakFlowWeight,
    double? stressRmssdWeight,
  }) {
    return MoodDetectionSettings(
      calmRatio: calmRatio ?? this.calmRatio,
      calmVariability: calmVariability ?? this.calmVariability,
      focusConsistency: focusConsistency ?? this.focusConsistency,
      calibrationBreaths: calibrationBreaths ?? this.calibrationBreaths,
      advancedMode: advancedMode ?? this.advancedMode,
      stressRatioWeight: stressRatioWeight ?? this.stressRatioWeight,
      stressDurationWeight: stressDurationWeight ?? this.stressDurationWeight,
      stressSmoothnessWeight: stressSmoothnessWeight ?? this.stressSmoothnessWeight,
      stressPeakFlowWeight: stressPeakFlowWeight ?? this.stressPeakFlowWeight,
      stressRmssdWeight: stressRmssdWeight ?? this.stressRmssdWeight,
    );
  }
  
  /// Normalize weights to sum to 1.0
  void normalizeWeights() {
    final total = stressRatioWeight + stressDurationWeight + 
                  stressSmoothnessWeight + stressPeakFlowWeight + stressRmssdWeight;
    if (total > 0) {
      stressRatioWeight /= total;
      stressDurationWeight /= total;
      stressSmoothnessWeight /= total;
      stressPeakFlowWeight /= total;
      stressRmssdWeight /= total;
    }
  }
}
