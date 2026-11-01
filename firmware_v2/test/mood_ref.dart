// mood_ref.dart - Runs the app's MoodAnalyzer (with the app settings' defaults) on breaths.txt, for
// compare.py. Usage: dart mood_ref.dart breaths.txt
import 'dart:io';

import 'mood_analyzer_app.dart';

void main(List<String> args) {
  final m = MoodAnalyzer()
    // App settings defaults (lib/models/settings.dart MoodDetectionSettings), which override the
    // analyzer's own field defaults at runtime
    ..calmRatio = 1.5
    ..calmVariabilityCv = 0.10
    ..focusConsistencyCv = 0.15
    ..calibrationBreaths = 6
    ..stressRatioWeight = 0.35
    ..stressDurationWeight = 0.20
    ..stressSmoothnessWeight = 0.15
    ..stressPeakFlowWeight = 0.15
    ..stressRmssdWeight = 0.15;
  for (final line in File(args[0]).readAsLinesSync()) {
    final f = line.trim().split(RegExp(r'\s+'));
    if (f.length < 5) continue;
    m.recordBreath(
      exhaleDuration: double.parse(f[0]),
      inhaleDuration: double.parse(f[1]),
      cycleDuration: double.parse(f[2]),
      smoothness: int.parse(f[3]),
      peakFlow: double.parse(f[4]),
    );
    print('M,${m.stressScore},${m.focusScore},${m.meditationScore},${m.isCalibrating ? 1 : 0}');
  }
}
