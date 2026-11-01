/// Scores computed on the headset, from its K line (about once a second):
/// K,{stress},{focus},{meditation},{heart_stress},{breath_stress},{nose_worn},{heart_worn},{calibrating}
/// stress, heart_stress and breath_stress are 0-100; focus and meditation 0-10. The app only displays
/// them (labels below are display wording, not analysis).
class Scores {
  final int stress;
  final int focus;
  final int meditation;
  final int heartStress;
  final int breathStress;
  final bool noseWorn;
  final bool heartWorn;
  final bool calibrating;

  const Scores({
    this.stress = 0,
    this.focus = 5,
    this.meditation = 0,
    this.heartStress = 0,
    this.breathStress = 0,
    this.noseWorn = false,
    this.heartWorn = false,
    this.calibrating = true,
  });

  static Scores? fromMessage(String line) {
    final p = line.trim().split(',');
    if (p.length < 9 || p[0] != 'K') return null;
    final v = p.sublist(1).map(int.tryParse).toList();
    if (v.any((x) => x == null)) return null;
    return Scores(
      stress: v[0]!,
      focus: v[1]!,
      meditation: v[2]!,
      heartStress: v[3]!,
      breathStress: v[4]!,
      noseWorn: v[5] == 1,
      heartWorn: v[6] == 1,
      calibrating: v[7] == 1,
    );
  }

  /// Combined stress on the app's old -5 (serene) .. +5 (anxious) scale, for the existing widgets
  int get stressScale => ((stress / 10.0) - 5).round().clamp(-5, 5);

  String get stressLabel {
    if (calibrating) return 'Calibrating...';
    final s = stressScale;
    if (s <= -4) return 'SERENE';
    if (s <= -2) return 'CALM';
    if (s <= 1) return 'BALANCED';
    if (s <= 3) return 'TENSE';
    return 'ANXIOUS';
  }

  String get focusLabel {
    if (calibrating) return 'Calibrating...';
    if (focus >= 8) return 'DEEP FOCUS';
    if (focus >= 6) return 'FOCUSED';
    if (focus >= 4) return 'ATTENTIVE';
    if (focus >= 2) return 'DISTRACTED';
    return 'SCATTERED';
  }

  String get meditationLabel {
    if (calibrating) return 'Calibrating...';
    if (meditation >= 8) return 'DEEP';
    if (meditation >= 6) return 'MEDITATIVE';
    if (meditation >= 4) return 'RELAXED';
    if (meditation >= 2) return 'SETTLING';
    return 'ACTIVE';
  }
}
