/// Heart data received from the headset's pulse sensor via BLE (Heart mode)
class HeartData {
  final int timestamp;
  final double waveValue; // Pulse waveform, roughly -1..1
  final int bpm; // Rate of the headset's steady LED rhythm; 0 when stopped
  final bool hasSignal; // true while the LED rhythm is running
  final int beatCount; // Increments on every beat shown on the LEDs (wraps at 65535)
  final int strength; // 0-100, smoothed beat strength (50 = typical)

  HeartData({
    required this.timestamp,
    required this.waveValue,
    this.bpm = 0,
    this.hasSignal = false,
    this.beatCount = 0,
    this.strength = 50,
  });

  /// Parse from BLE: "H,{ts},{wave},{bpm},{signal},{beats},{strength}\n"
  factory HeartData.fromMessage(String message) {
    final parts = message.trim().split(',');
    if (parts.length < 3 || parts[0] != 'H') {
      throw FormatException('Invalid heart data message: $message');
    }
    return HeartData(
      timestamp: int.parse(parts[1]),
      waveValue: double.parse(parts[2]),
      bpm: parts.length >= 4 ? int.parse(parts[3]) : 0,
      hasSignal: parts.length >= 5 ? parts[4] == '1' : false,
      beatCount: parts.length >= 6 ? int.parse(parts[5]) : 0,
      strength: parts.length >= 7 ? int.parse(parts[6]) : 50,
    );
  }
}
