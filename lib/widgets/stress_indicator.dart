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
                      // E/I Ratio: 0.8 (stressed) to 1.5 (calm)
                      MoodScaleBar(
                        label: 'E/I Ratio',
                        value: _normalizeRatio(analyzer.currentRatio),
                        displayValue: analyzer.currentRatio.toStringAsFixed(2),
                      ),
                      // Duration: compare to baseline
                      MoodScaleBar(
                        label: 'Duration',
                        value: _normalizeDuration(analyzer.currentCycle, analyzer.baselineCycle),
                        displayValue: '${analyzer.currentCycle.toStringAsFixed(1)}s',
                      ),
                      // Smoothness: 0% (stressed) to 100% (calm)
                      MoodScaleBar(
                        label: 'Smoothness',
                        value: analyzer.currentSmoothness / 100.0,
                        displayValue: '${analyzer.currentSmoothness}%',
                      ),
                      // Peak Flow: compare to baseline
                      MoodScaleBar(
                        label: 'Peak Flow',
                        value: _normalizePeakFlow(analyzer.currentPeakFlow, analyzer.baselinePeakFlow),
                        displayValue: analyzer.baselinePeakFlow != null 
                            ? '${(analyzer.currentPeakFlow / analyzer.baselinePeakFlow!).toStringAsFixed(2)}x'
                            : '--',
                      ),
                      // Variability: 0.4 CV (stressed, left) to 0.1 CV (calm, right)
                      MoodScaleBar(
                        label: 'Variability',
                        value: _normalizeVariability(analyzer.currentConsistency, analyzer.currentCycle),
                        displayValue: (analyzer.currentConsistency / analyzer.currentCycle.clamp(0.1, 100)).toStringAsFixed(2),
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
  
  // Normalize E/I ratio: 0.8 (left) to 1.5 (right)
  double _normalizeRatio(double ratio) {
    return ((ratio - 0.8) / (1.5 - 0.8)).clamp(0.0, 1.0);
  }
  
  // Normalize duration vs baseline: < 70% = left, > 130% = right
  double _normalizeDuration(double current, double? baseline) {
    if (baseline == null || baseline <= 0) return 0.5;
    final ratio = current / baseline;
    return ((ratio - 0.7) / (1.3 - 0.7)).clamp(0.0, 1.0);
  }
  
  // Normalize peak flow vs baseline
  double _normalizePeakFlow(double current, double? baseline) {
    if (baseline == null || baseline <= 0 || current <= 0) return 0.5;
    final ratio = current / baseline;
    return ((ratio - 0.7) / (1.3 - 0.7)).clamp(0.0, 1.0);
  }
  
  // Normalize variability CV: 0.4 (left) to 0.1 (right)
  double _normalizeVariability(double consistency, double cycle) {
    final cv = consistency / cycle.clamp(0.1, 100);
    // Invert: high CV = left (stressed), low CV = right (calm)
    return 1.0 - ((cv - 0.1) / (0.4 - 0.1)).clamp(0.0, 1.0);
  }
}
