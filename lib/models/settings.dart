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

  GuidedBreathingSettings({
    this.inhaleLength = 4.0,
    this.holdAfterInhale = 2.0,
    this.exhaleLength = 5.0,
    this.holdAfterExhale = 1.0,
    this.ledStart = 2,
    this.ledEnd = 9,
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
  }) {
    return GuidedBreathingSettings(
      inhaleLength: inhaleLength ?? this.inhaleLength,
      holdAfterInhale: holdAfterInhale ?? this.holdAfterInhale,
      exhaleLength: exhaleLength ?? this.exhaleLength,
      holdAfterExhale: holdAfterExhale ?? this.holdAfterExhale,
      ledStart: ledStart ?? this.ledStart,
      ledEnd: ledEnd ?? this.ledEnd,
    );
  }
}

/// Breathing mode enum
enum BreathingMode {
  off, // Standby - LEDs off, just monitoring
  open, // Open Breathing mode
  guided, // Guided Breathing mode
}

extension BreathingModeExtension on BreathingMode {
  /// Convert to BLE message format
  String toMessage() {
    switch (this) {
      case BreathingMode.off:
        return 'M,O\n';
      case BreathingMode.open:
        return 'M,F\n';
      case BreathingMode.guided:
        return 'M,G\n';
    }
  }

  String get displayName {
    switch (this) {
      case BreathingMode.off:
        return 'Off';
      case BreathingMode.open:
        return 'Open Breathing';
      case BreathingMode.guided:
        return 'Guided Breathing';
    }
  }
}
