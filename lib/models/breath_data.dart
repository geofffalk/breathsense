/// Breath data model received from the headset via BLE
/// New format: raw metrics for app-side mood calculation
class BreathData {
  final int timestamp;
  final int phase; // 0=idle, 1=inhale, 2=exhale
  final double flowValue;
  final int depthColor; // 0-4 (red, white, light blue, purple, deep blue)
  final int guidedPhase; // -1=none, 0=inhale, 1=hold_in, 2=exhale, 3=hold_out
  
  // Raw breath metrics from firmware (for app-side mood calculation)
  final double exhaleDuration;  // seconds
  final double inhaleDuration;  // seconds
  final double cycleDuration;   // seconds (exhale + inhale)
  final int smoothness;         // 0-100 (100=smooth, 0=jerky)
  final double peakFlow;        // Absolute peak flow magnitude
  final int symmetry;           // 0-100 (0=front-loaded, 100=back-loaded)
  final bool isUnworn;          // true if headset not detecting breath

  BreathData({
    required this.timestamp,
    required this.phase,
    required this.flowValue,
    required this.depthColor,
    this.guidedPhase = -1,
    this.exhaleDuration = 0.0,
    this.inhaleDuration = 0.0,
    this.cycleDuration = 0.0,
    this.smoothness = 100,
    this.peakFlow = 0.0,
    this.symmetry = 50,
    this.isUnworn = false,
  });

  /// Parse from BLE: "B,{ts},{phase},{flow},{depth},{guided},{exhale_dur},{inhale_dur},{cycle_dur},{smoothness},{peak_flow},{symmetry},{unworn}\n"
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
      exhaleDuration: parts.length >= 7 ? double.parse(parts[6]) : 0.0,
      inhaleDuration: parts.length >= 8 ? double.parse(parts[7]) : 0.0,
      cycleDuration: parts.length >= 9 ? double.parse(parts[8]) : 0.0,
      smoothness: parts.length >= 10 ? int.parse(parts[9]) : 100,
      peakFlow: parts.length >= 11 ? double.parse(parts[10]) : 0.0,
      symmetry: parts.length >= 12 ? int.parse(parts[11]) : 50,
      isUnworn: parts.length >= 13 ? parts[12] == '1' : false,
    );
  }

  bool get isIdle => phase == 0;
  bool get isInhale => phase == 1;
  bool get isExhale => phase == 2;
  
  /// E/I Ratio - exhale duration / inhale duration
  double get eiRatio => inhaleDuration > 0 ? exhaleDuration / inhaleDuration : 1.0;

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
