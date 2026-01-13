import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/ble_service.dart';
import 'mood_scale_bar.dart';

/// Focus level indicator with expandable consistency breakdown
class FocusIndicator extends StatefulWidget {
  final int focusScore; // 0-10 scale
  final bool isCalibrating;

  const FocusIndicator({
    super.key,
    required this.focusScore,
    required this.isCalibrating,
  });

  @override
  State<FocusIndicator> createState() => _FocusIndicatorState();
}

class _FocusIndicatorState extends State<FocusIndicator> {
  bool _expanded = false;

  String get label {
    if (widget.isCalibrating) return 'CALIBRATING...';
    if (widget.focusScore >= 8) return 'DEEP FOCUS';
    if (widget.focusScore >= 6) return 'FOCUSED';
    if (widget.focusScore >= 4) return 'ATTENTIVE';
    if (widget.focusScore >= 2) return 'DISTRACTED';
    return 'SCATTERED';
  }

  List<Color> get gradientColors {
    if (widget.isCalibrating) {
      return [Colors.grey[600]!, Colors.grey[700]!];
    }
    if (widget.focusScore >= 8) {
      return [const Color(0xFF667EEA), const Color(0xFF764BA2)];
    } else if (widget.focusScore >= 6) {
      return [const Color(0xFF6B8DD6), const Color(0xFF8E37D7)];
    } else if (widget.focusScore >= 4) {
      return [const Color(0xFF89CFF0), const Color(0xFF5DADE2)];
    } else if (widget.focusScore >= 2) {
      return [const Color(0xFFB8B8B8), const Color(0xFF9E9E9E)];
    } else {
      return [const Color(0xFFD4A574), const Color(0xFFC19660)];
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, _) {
        final analyzer = bleService.moodAnalyzer;
        
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Column(
            children: [
              // Main row with expand caret
              GestureDetector(
                onTap: () => setState(() => _expanded = !_expanded),
                child: Row(
                  children: [
                    // Expand caret
                    Icon(
                      _expanded ? Icons.expand_more : Icons.chevron_right,
                      color: Colors.white54,
                      size: 20,
                    ),
                    // Label
                    const Text(
                      'Focus level:',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const Spacer(),
                    // Value in colored box
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
              ),
              // Expanded detail panel
              AnimatedCrossFade(
                duration: const Duration(milliseconds: 200),
                crossFadeState: _expanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
                firstChild: const SizedBox.shrink(),
                secondChild: Container(
                  margin: const EdgeInsets.only(top: 8, left: 24),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Direction hint
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('← DISTRACTED', style: TextStyle(fontSize: 9, color: Colors.orange[700], fontWeight: FontWeight.bold)),
                          Text('FOCUSED →', style: TextStyle(fontSize: 9, color: Colors.purple[700], fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      // Consistency CV: high CV (distracted, left) to low CV (focused, right)
                      MoodScaleBar(
                        label: 'Consistency',
                        value: _normalizeConsistency(analyzer.currentConsistency, analyzer.currentCycle),
                        displayValue: '${(analyzer.currentConsistency / analyzer.currentCycle.clamp(0.1, 100)).toStringAsFixed(2)} CV',
                      ),
                      // Also show cycle duration as reference
                      MoodScaleBar(
                        label: 'Cycle Time',
                        value: _normalizeCycleForFocus(analyzer.currentCycle),
                        displayValue: '${analyzer.currentCycle.toStringAsFixed(1)}s',
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
  
  // Normalize consistency CV: 0.3 (left, distracted) to 0.15 (right, focused)
  double _normalizeConsistency(double consistency, double cycle) {
    final cv = consistency / cycle.clamp(0.1, 100);
    // Invert: high CV = left (distracted), low CV = right (focused)
    return 1.0 - ((cv - 0.15) / (0.30 - 0.15)).clamp(0.0, 1.0);
  }
  
  // Normalize cycle for focus: moderate cycles (4-8s) are optimal
  double _normalizeCycleForFocus(double cycle) {
    // 4-8s is optimal range, showing as middle to right
    if (cycle < 4) return 0.2;
    if (cycle > 10) return 0.8;
    return ((cycle - 4) / 6).clamp(0.0, 1.0);
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
