import 'package:flutter/material.dart';

/// Calm level indicator - label on dark background, value in colored box
class StressIndicator extends StatelessWidget {
  final int stressScore; // -5 (serene) to +5 (anxious)
  final bool isCalibrating;

  const StressIndicator({
    super.key,
    required this.stressScore,
    required this.isCalibrating,
  });

  String get label {
    if (isCalibrating) return 'CALIBRATING...';
    if (stressScore <= -4) return 'SERENE';
    if (stressScore <= -2) return 'CALM';
    if (stressScore <= 1) return 'BALANCED';
    if (stressScore <= 3) return 'TENSE';
    return 'ANXIOUS';
  }

  List<Color> get gradientColors {
    if (isCalibrating) {
      return [Colors.grey[600]!, Colors.grey[700]!];
    }
    if (stressScore <= -4) {
      return [const Color(0xFF87CEEB), const Color(0xFF5DADE2)];
    } else if (stressScore <= -2) {
      return [const Color(0xFF76D7C4), const Color(0xFF48C9B0)];
    } else if (stressScore <= 1) {
      return [const Color(0xFFB2BEB5), const Color(0xFF99A89A)];
    } else if (stressScore <= 3) {
      return [const Color(0xFFFFB347), const Color(0xFFE59400)];
    } else {
      return [const Color(0xFFFF6B6B), const Color(0xFFE74C3C)];
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Label with small indent
          const Padding(
            padding: EdgeInsets.only(left: 4),
            child: Text(
              'Stress level:',
              style: TextStyle(
                color: Colors.white70,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          // Value in colored box (fixed width)
          SizedBox(
            width: 120,
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: gradientColors,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                label,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 12,
                  letterSpacing: 0.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
