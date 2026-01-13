/// Breath data model received from the headset via BLE
class BreathData {
  final int timestamp;
  final int phase; // 0=idle, 1=inhale, 2=exhale
  final double flowValue;
  final int depthColor; // 0-4 (red, white, light blue, purple, deep blue)
  final int guidedPhase; // -1=none, 0=inhale, 1=hold_in, 2=exhale, 3=hold_out
  final int stressScore; // -5 (serene) to +5 (anxious), -99 if calibrating
  final int focusScore; // 0 (unfocused) to 10 (highly focused), -1 if calibrating
  final int meditationScore; // 0 (not meditative) to 10 (deep), -1 if calibrating
  final bool isCalibrating; // true if still in calibration phase
  final bool isUnworn; // true if headset is not detecting breath (not being worn)

  BreathData({
    required this.timestamp,
    required this.phase,
    required this.flowValue,
    required this.depthColor,
    this.guidedPhase = -1,
    this.stressScore = 0,
    this.focusScore = 0,
    this.meditationScore = 0,
    this.isCalibrating = true,
    this.isUnworn = false,
  });

  /// Parse from BLE: "B,{ts},{phase},{flow},{depth},{guided},{stress},{focus},{meditation},{calibrating},{unworn}\n"
  factory BreathData.fromMessage(String message) {
    final parts = message.trim().split(',');
    if (parts.length < 5 || parts[0] != 'B') {
      throw FormatException('Invalid breath data message: $message');
    }
    return BreathData(
      timestamp: int.parse(parts[1]),
      phase: int.parse(parts[2]),
      flowValue: double.parse(parts[3]),
      depthColor: int.parse(parts[4]),
      guidedPhase: parts.length >= 6 ? int.parse(parts[5]) : -1,
      stressScore: parts.length >= 7 ? int.parse(parts[6]) : 0,
      focusScore: parts.length >= 8 ? int.parse(parts[7]) : 0,
      meditationScore: parts.length >= 9 ? int.parse(parts[8]) : 0,
      isCalibrating: parts.length >= 10 ? parts[9] == '1' : true,
      isUnworn: parts.length >= 11 ? parts[10] == '1' : false,
    );
  }

  bool get isIdle => phase == 0;
  bool get isInhale => phase == 1;
  bool get isExhale => phase == 2;

  String get phaseName {
    switch (phase) {
      case 1:
        return 'Inhale';
      case 2:
        return 'Exhale';
      default:
        return 'Idle';
    }
  }

  /// Get stress level label for display
  String get stressLabel {
    if (isCalibrating) return 'Calibrating...';
    if (stressScore <= -4) return 'SERENE';
    if (stressScore <= -2) return 'CALM';
    if (stressScore <= 1) return 'BALANCED';
    if (stressScore <= 3) return 'TENSE';
    return 'ANXIOUS';
  }

  /// Get focus level label for display
  String get focusLabel {
    if (isCalibrating) return 'Calibrating...';
    if (focusScore >= 8) return 'DEEP FOCUS';
    if (focusScore >= 6) return 'FOCUSED';
    if (focusScore >= 4) return 'ATTENTIVE';
    if (focusScore >= 2) return 'DISTRACTED';
    return 'SCATTERED';
  }

  /// Get meditation depth label for display
  String get meditationLabel {
    if (isCalibrating) return 'Calibrating...';
    if (meditationScore >= 8) return 'DEEP';
    if (meditationScore >= 6) return 'MEDITATIVE';
    if (meditationScore >= 4) return 'RELAXED';
    if (meditationScore >= 2) return 'SETTLING';
    return 'ACTIVE';
  }
}
