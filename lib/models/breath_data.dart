/// Breath data model received from the headset via BLE
class BreathData {
  final int timestamp;
  final int phase; // 0=idle, 1=inhale, 2=exhale
  final double flowValue;
  final int depthColor; // 0-4 (red, white, light blue, purple, deep blue)
  final int guidedPhase; // -1=none, 0=inhale, 1=hold_in, 2=exhale, 3=hold_out

  BreathData({
    required this.timestamp,
    required this.phase,
    required this.flowValue,
    required this.depthColor,
    this.guidedPhase = -1,
  });

  /// Parse from BLE message format: "B,{timestamp},{phase},{flow},{depth},{guided_phase}\n"
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
}
