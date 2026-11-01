import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/ble_service.dart';
import 'mood_scale_bar.dart';

/// Expandable stress level indicator with animated factor breakdowns
class StressIndicator extends StatefulWidget {
  final int stressScore; // -5 (serene) to +5 (anxious)
  final bool isCalibrating;

  const StressIndicator({
    super.key,
    required this.stressScore,
    required this.isCalibrating,
  });

  @override
  State<StressIndicator> createState() => _StressIndicatorState();
}

class _StressIndicatorState extends State<StressIndicator> {
  bool _expanded = false;

  String get label {
    if (widget.isCalibrating) return 'CALIBRATING...';
    if (widget.stressScore <= -4) return 'SERENE';
    if (widget.stressScore <= -2) return 'CALM';
    if (widget.stressScore <= 1) return 'BALANCED';
    if (widget.stressScore <= 3) return 'TENSE';
    return 'ANXIOUS';
  }

  List<Color> get gradientColors {
    if (widget.isCalibrating) {
      return [Colors.grey[600]!, Colors.grey[700]!];
    }
    if (widget.stressScore <= -4) {
      return [const Color(0xFF87CEEB), const Color(0xFF5DADE2)];
    } else if (widget.stressScore <= -2) {
      return [const Color(0xFF76D7C4), const Color(0xFF48C9B0)];
    } else if (widget.stressScore <= 1) {
      return [const Color(0xFFB2BEB5), const Color(0xFF99A89A)];
    } else if (widget.stressScore <= 3) {
      return [const Color(0xFFFFB347), const Color(0xFFE59400)];
    } else {
      return [const Color(0xFFFF6B6B), const Color(0xFFE74C3C)];
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, _) {
        final k = bleService.scores;   // Computed on the headset
        
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
                      'Stress level:',
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
                          Text('← STRESSED', style: TextStyle(fontSize: 9, color: Colors.red[400], fontWeight: FontWeight.bold)),
                          Text('CALM →', style: TextStyle(fontSize: 9, color: Colors.green[600], fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      // The parts of the headset's combined score (0-100, high = stressed)
                      MoodScaleBar(
                        label: 'Heart',
                        value: k.heartWorn ? 1.0 - k.heartStress / 100.0 : 0.5,
                        displayValue: k.heartWorn ? '${k.heartStress}' : 'not worn',
                      ),
                      MoodScaleBar(
                        label: 'Breath',
                        value: k.noseWorn ? 1.0 - k.breathStress / 100.0 : 0.5,
                        displayValue: k.noseWorn ? '${k.breathStress}' : 'not worn',
                      ),
                      const SizedBox(height: 4),
                      Text(
                        k.noseWorn
                            ? 'Combined: 60% heart, 40% breath'
                            : 'Combined: heart only (nose clip not worn)',
                        style: TextStyle(fontSize: 10, color: Colors.grey[600]),
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
}
