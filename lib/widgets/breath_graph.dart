import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:provider/provider.dart';

import '../models/settings.dart';
import '../services/ble_service.dart';

/// Real-time chart: inhales/exhales, or the live pulse waveform in Heart mode
class BreathGraph extends StatefulWidget {
  final double height;

  const BreathGraph({super.key, this.height = 200});

  @override
  State<BreathGraph> createState() => _BreathGraphState();
}

class _BreathGraphState extends State<BreathGraph>
    with SingleTickerProviderStateMixin {
  static const int windowSize = 200; // Points to display
  static const double yLimit = 1.2; // Y-axis range
  static const int frameMs = 100; // Update interval
  static const int heartFrameMs = 40; // Faster updates so the pulse trace scrolls smoothly
  static const Color heartColor = Color(0xFFFF5252);

  late Ticker _ticker;
  DateTime _lastUpdate = DateTime.now();
  List<FlSpot> _spots = [];
  List<int> _phases = [];
  List<int> _depths = [];
  BreathingMode _mode = BreathingMode.open;
  int _colorSchemeId = 0; // Cached color scheme
  int _xCounter = 0;

  @override
  void initState() {
    super.initState();

    _ticker = createTicker((_) {
      final now = DateTime.now();
      final interval = _mode == BreathingMode.heart ? heartFrameMs : frameMs;
      if (now.difference(_lastUpdate).inMilliseconds < interval) return;
      _lastUpdate = now;
      _updateGraph();
    });
    _ticker.start();
  }

  void _updateGraph() {
    if (!mounted) return; // Prevent context access after unmount
    
    final bleService = context.read<BleService>();
    final mode = bleService.currentMode;
    final isHeart = mode == BreathingMode.heart;
    final flowValues = isHeart
        ? bleService.getHeartValues(windowSize)
        : bleService.getFlowValues(windowSize);
    final phases = isHeart ? const <int>[] : bleService.getPhaseValues(windowSize);
    final depths = isHeart ? const <int>[] : bleService.getDepthValues(windowSize);
    final schemeId = bleService.guidedSettings.colorScheme.clamp(0, 2);

    final newSpots = <FlSpot>[];
    for (int i = 0; i < flowValues.length; i++) {
      final x = (_xCounter - (windowSize - 1 - i)).toDouble();
      final y = flowValues[i].clamp(-yLimit, yLimit);
      newSpots.add(FlSpot(x, y));
    }

    _xCounter++;

    if (mounted) {
      setState(() {
        _spots = newSpots;
        _phases = phases;
        _depths = depths;
        _mode = mode;
        _colorSchemeId = schemeId; // Cache scheme ID
      });
    }
  }

  // Color schemes matching firmware: (inhale, hold, exhale)
  static const List<List<Color>> _colorSchemes = [
    // 0: Default - Green/Orange/Cyan
    [Color(0xFF00FF00), Color(0xFFFF3200), Color(0xFF00FFFF)],
    // 1: High Contrast - Yellow/Purple/White
    [Color(0xFFFFFF00), Color(0xFF8000FF), Color(0xFFFFFFFF)],
    // 2: Cool Tones - Blue/Magenta/White
    [Color(0xFF0064FF), Color(0xFFFF0080), Color(0xFFFFFFFF)],
  ];

  Color _getColorForPhase(int phase, int depth) {
    if (_mode == BreathingMode.open) {
      // depthColor: 0-4 (red, white, cyan, purple, pink/magenta)
      switch (depth) {
        case 0: return Colors.redAccent;
        case 1: return Colors.white; 
        case 2: return Colors.cyan[600]!;
        case 3: return Colors.purple[300]!;
        case 4: return const Color(0xFF2962FF); // Deep Blue (Brighter)
        default: return Colors.cyan[600]!;
      }
    }
    
    // Guided mode: Use cached color scheme (avoids context access in build)
    final colors = _colorSchemes[_colorSchemeId];
    
    switch (phase) {
      case 0: return colors[0]; // Inhale
      case 1: return colors[1]; // Hold In
      case 2: return colors[2]; // Exhale
      case 3: return colors[1]; // Hold Out
      default: return Colors.grey;
    }
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  LinearGradient _lineGradient() {
    if (_mode == BreathingMode.heart) {
      return const LinearGradient(colors: [heartColor, heartColor]);
    }
    if (_phases.length > 1) {
      return LinearGradient(
        colors: List.generate(_phases.length, (i) => _getColorForPhase(_phases[i], _depths[i])),
        stops: List.generate(_phases.length, (index) => index / (_phases.length - 1)),
      );
    }
    return const LinearGradient(colors: [Colors.cyan, Colors.cyan]);
  }

  @override
  Widget build(BuildContext context) {
    final isHeart = _mode == BreathingMode.heart;
    final minX = (_xCounter - windowSize).toDouble();
    final maxX = _xCounter.toDouble();

    return RepaintBoundary(
      child: Container(
        height: widget.height,
        padding: const EdgeInsets.fromLTRB(8, 16, 16, 8),
        decoration: BoxDecoration(
          color: Colors.grey[800], // Restored mid-dark grey for best contrast
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey[300]!, width: 1),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: LineChart(
          LineChartData(
            lineTouchData: const LineTouchData(enabled: false),
            minY: -yLimit,
            maxY: yLimit,
            minX: minX,
            maxX: maxX,
            clipData: const FlClipData.all(),
            gridData: FlGridData(
              show: true,
              drawVerticalLine: false,
              horizontalInterval: 0.5,
              getDrawingHorizontalLine: (value) => FlLine(
                color: Colors.grey[400]!, // Darker grid lines for visibility on grey[800]
                strokeWidth: 0.5,
                dashArray: [5, 5],
              ),
            ),
            titlesData: FlTitlesData(
              show: true,
              topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 34,
                  interval: 0.5,
                  getTitlesWidget: (value, meta) {
                    TextStyle style = TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey[400], 
                    );
                    if (isHeart) {
                      return const Text('');
                    }
                    if (value == 1) {
                      return Text('IN', style: style.copyWith(color: Colors.green[800]));
                    }
                    if (value == -1) {
                      return Text('OUT', style: style.copyWith(color: Colors.blue[800]));
                    }
                    return const Text('');
                  },
                ),
              ),
            ),
            borderData: FlBorderData(show: false),
            lineBarsData: [
              LineChartBarData(
                spots: _spots.isEmpty ? [const FlSpot(0, 0)] : _spots,
                isCurved: true,
                curveSmoothness: 0.3,
                preventCurveOverShooting: true,
                shadow: const Shadow(
                  color: Colors.black26,
                  offset: Offset(0, 2),
                  blurRadius: 3,
                ),
                gradient: _lineGradient(),
                barWidth: 1.5,
                isStrokeCapRound: true,
                dotData: const FlDotData(show: false),
                belowBarData: BarAreaData(
                  show: true,
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.cyan.withOpacity(0.05),
                      Colors.blue.withOpacity(0.01),
                    ],
                  ),
                ),
              ),
            ],
          ),
          duration: Duration.zero,
        ),
      ),
    );
  }
}
