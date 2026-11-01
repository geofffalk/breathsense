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

/// Headset mode. The headset reports it (M,{F|H|O}) on connect and on every change; the app
/// can set it. Guided breathing is dropped.
enum BreathingMode {
  open, // Breath (protocol letter F, kept from "free/open breathing")
  heart, // Heart monitor (pulse sensor)
  off, // LEDs dark, sensing paused, Bluetooth on (only the headset's button fully sleeps it)
}

extension BreathingModeExtension on BreathingMode {
  /// Convert to BLE message format
  String toMessage() {
    switch (this) {
      case BreathingMode.open:
        return 'M,F\n';
      case BreathingMode.heart:
        return 'M,H\n';
      case BreathingMode.off:
        return 'M,O\n';
    }
  }

  String get displayName {
    switch (this) {
      case BreathingMode.open:
        return 'Breath';
      case BreathingMode.heart:
        return 'Heart Monitor';
      case BreathingMode.off:
        return 'Off';
    }
  }

  /// Parse the headset's M report letter
  static BreathingMode? fromLetter(String letter) {
    switch (letter.toUpperCase()) {
      case 'F':
        return BreathingMode.open;
      case 'H':
        return BreathingMode.heart;
      case 'O':
        return BreathingMode.off;
    }
    return null;
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

  /// Convert to BLE message format. The headset computes all scores, so the stress weights go too
  /// (as optional trailing fields).
  String toMessage() {
    return 'S,M,$calmRatio,$calmVariability,$focusConsistency,$calibrationBreaths,'
        '$stressRatioWeight,$stressDurationWeight,$stressSmoothnessWeight,$stressPeakFlowWeight,$stressRmssdWeight\n';
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
