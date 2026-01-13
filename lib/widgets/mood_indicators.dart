import 'package:flutter/material.dart';

/// Focus level indicator - label on dark background, value in colored box
class FocusIndicator extends StatelessWidget {
  final int focusScore; // 0-10 scale
  final bool isCalibrating;

  const FocusIndicator({
    super.key,
    required this.focusScore,
    required this.isCalibrating,
  });

  String get label {
    if (isCalibrating) return 'CALIBRATING...';
    if (focusScore >= 8) return 'DEEP FOCUS';
    if (focusScore >= 6) return 'FOCUSED';
    if (focusScore >= 4) return 'ATTENTIVE';
    if (focusScore >= 2) return 'DISTRACTED';
    return 'SCATTERED';
  }

  List<Color> get gradientColors {
    if (isCalibrating) {
      return [Colors.grey[600]!, Colors.grey[700]!];
    }
    if (focusScore >= 8) {
      return [const Color(0xFF667EEA), const Color(0xFF764BA2)];
    } else if (focusScore >= 6) {
      return [const Color(0xFF6B8DD6), const Color(0xFF8E37D7)];
    } else if (focusScore >= 4) {
      return [const Color(0xFF89CFF0), const Color(0xFF5DADE2)];
    } else if (focusScore >= 2) {
      return [const Color(0xFFB8B8B8), const Color(0xFF9E9E9E)];
    } else {
      return [const Color(0xFFD4A574), const Color(0xFFC19660)];
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
              'Focus level:',
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

/// Meditation depth indicator (kept for Session Report)
class MeditationIndicator extends StatelessWidget {
  final int meditationScore; // 0-10 scale
  final bool isCalibrating;

  const MeditationIndicator({
    super.key,
    required this.meditationScore,
    required this.isCalibrating,
  });

  String get label {
    if (isCalibrating) return 'CALIBRATING...';
    if (meditationScore >= 8) return 'DEEP';
    if (meditationScore >= 6) return 'MEDITATIVE';
    if (meditationScore >= 4) return 'RELAXED';
    if (meditationScore >= 2) return 'SETTLING';
    return 'ACTIVE';
  }

  List<Color> get gradientColors {
    if (isCalibrating) {
      return [Colors.grey[600]!, Colors.grey[700]!];
    }
    if (meditationScore >= 8) {
      return [const Color(0xFF2C3E50), const Color(0xFF1A252F)];
    } else if (meditationScore >= 6) {
      return [const Color(0xFF4A6572), const Color(0xFF344955)];
    } else if (meditationScore >= 4) {
      return [const Color(0xFF5C8984), const Color(0xFF4A7268)];
    } else if (meditationScore >= 2) {
      return [const Color(0xFF7D8F8C), const Color(0xFF6A7B78)];
    } else {
      return [const Color(0xFFA0A0A0), const Color(0xFF888888)];
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.zero,
      child: Row(
        children: [
          const Text(
            'Meditation',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
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
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 14,
                  letterSpacing: 1,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
