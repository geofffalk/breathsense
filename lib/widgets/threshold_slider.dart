import 'package:flutter/material.dart';

/// A multi-thumb range slider for setting exhale duration thresholds.
/// Shows 5 color zones with 4 draggable dividers between them.
class ThresholdRangeSlider extends StatelessWidget {
  /// The 4 threshold values (dividers between the 5 zones)
  final double veryShortMax;  // Divider 1: Red | White
  final double shortMax;       // Divider 2: White | Blue
  final double mediumMax;      // Divider 3: Blue | Purple  
  final double longMax;        // Divider 4: Purple | Deep Blue
  
  /// The overall min and max of the slider
  final double min;
  final double max;
  
  /// Callback when values change
  final void Function(double veryShort, double short, double medium, double long) onChanged;

  const ThresholdRangeSlider({
    super.key,
    required this.veryShortMax,
    required this.shortMax,
    required this.mediumMax,
    required this.longMax,
    this.min = 0.5,
    this.max = 10.0,
    required this.onChanged,
  });

  // Colors for each zone (5 zones, 4 dividers)
  static const List<Color> zoneColors = [
    Colors.red,          // Very short (left of thumb 1)
    Colors.white,        // Short (reverted for user preference)
    Color(0xFF80D8FF),   // Medium (Lighter sky blue)
    Color(0xFFBA68C8),   // Long (Light Purple)
    Color(0xFF0D47A1),   // Deep Blue (Dark navy)
  ];

  static const List<String> zoneLabels = [
    'V.Short',
    'Short',
    'Medium',
    'Long',
    'Deep',
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Zone labels and colors legend
        _buildLegend(),
        const SizedBox(height: 12),
        
        // The slider track with colored zones
        LayoutBuilder(
          builder: (context, constraints) {
            final width = constraints.maxWidth;
            return SizedBox(
              height: 80,
              child: _ThresholdSliderTrack(
                width: width,
                min: min,
                max: max,
                values: [veryShortMax, shortMax, mediumMax, longMax],
                onChanged: onChanged,
              ),
            );
          },
        ),
        
        // Min/max labels
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('${min.toStringAsFixed(1)}s', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
            Text('${max.toStringAsFixed(1)}s', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
          ],
        ),
      ],
    );
  }

  Widget _buildLegend() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: List.generate(5, (i) => Column(
        children: [
          Container(
            width: 14,
            height: 14,
            decoration: BoxDecoration(
              color: zoneColors[i],
              shape: BoxShape.circle,
              border: i == 1 ? Border.all(color: Colors.grey) : null, // Border for white
            ),
          ),
          const SizedBox(height: 2),
          Text(
            zoneLabels[i],
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[700], fontSize: 9, fontWeight: FontWeight.w500),
          ),
        ],
      )),
    );
  }
}

class _ThresholdSliderTrack extends StatefulWidget {
  final double width;
  final double min;
  final double max;
  final List<double> values;
  final void Function(double, double, double, double) onChanged;

  const _ThresholdSliderTrack({
    required this.width,
    required this.min,
    required this.max,
    required this.values,
    required this.onChanged,
  });

  @override
  State<_ThresholdSliderTrack> createState() => _ThresholdSliderTrackState();
}

class _ThresholdSliderTrackState extends State<_ThresholdSliderTrack> {
  int? _draggingIndex;
  late List<double> _values;
  
  @override
  void initState() {
    super.initState();
    _values = List.from(widget.values);
  }
  
  @override
  void didUpdateWidget(_ThresholdSliderTrack oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Only update if not actively dragging
    if (_draggingIndex == null) {
      _values = List.from(widget.values);
    }
  }

  double _valueToPosition(double value) {
    return ((value - widget.min) / (widget.max - widget.min)) * widget.width;
  }

  double _positionToValue(double position) {
    final value = widget.min + (position / widget.width) * (widget.max - widget.min);
    return (value * 2).round() / 2.0; // Round to 0.5s
  }

  void _handleHorizontalDrag(DragUpdateDetails details, int index) {
    // Use delta for relative movement instead of localPosition which is relative to the thumb
    final valueDelta = (details.delta.dx / widget.width) * (widget.max - widget.min);
    final newValue = _values[index] + valueDelta;
    
    // Ensure ordering with minimum gap
    const minGap = 0.5;
    final minAllowed = index > 0 ? _values[index - 1] + minGap : widget.min;
    // Prevent 4th thumb from reaching absolute max (leaves room for dragging back)
    final maxAllowed = index < 3 ? _values[index + 1] - minGap : widget.max - 0.5;
    
    final clampedValue = newValue.clamp(minAllowed, maxAllowed);
    
    if (_values[index] != clampedValue) {
      setState(() {
        _values[index] = clampedValue;
      });
      widget.onChanged(_values[0], _values[1], _values[2], _values[3]);
    }
  }

  @override
  Widget build(BuildContext context) {
    const trackHeight = 40.0;
    const thumbRadius = 18.0; // Larger hit area
    
    return Stack(
      clipBehavior: Clip.none,
      children: [
        // Track with colored zones
        Positioned(
          top: 20,
          left: 0,
          right: 0,
          child: Container(
            height: trackHeight,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(4),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: Row(
                children: [
                  // Zone 0: Very Short (red)
                  _buildZone(widget.min, _values[0], ThresholdRangeSlider.zoneColors[0]),
                  // Zone 1: Short (white)
                  _buildZone(_values[0], _values[1], ThresholdRangeSlider.zoneColors[1]),
                  // Zone 2: Medium (blue)
                  _buildZone(_values[1], _values[2], ThresholdRangeSlider.zoneColors[2]),
                  // Zone 3: Long (purple)
                  _buildZone(_values[2], _values[3], ThresholdRangeSlider.zoneColors[3]),
                  // Zone 4: Deep Blue
                  _buildZone(_values[3], widget.max, ThresholdRangeSlider.zoneColors[4]),
                ],
              ),
            ),
          ),
        ),
        
        // 4 Thumbs (draggable dividers) with callouts
        for (int i = 0; i < 4; i++)
          Positioned(
            left: _valueToPosition(_values[i]) - thumbRadius,
            top: 20 + (trackHeight / 2) - thumbRadius,
            child: GestureDetector(
              behavior: HitTestBehavior.opaque, // Better hit testing
              onHorizontalDragStart: (_) => setState(() => _draggingIndex = i),
              onHorizontalDragUpdate: (details) => _handleHorizontalDrag(details, i),
              onHorizontalDragEnd: (_) => setState(() => _draggingIndex = null),
              onHorizontalDragCancel: () => setState(() => _draggingIndex = null),
              child: SizedBox(
                width: thumbRadius * 2,
                height: thumbRadius * 2 + 28, // Extra height for callout
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    // Callout bubble (visible when dragging)
                    if (_draggingIndex == i)
                      Positioned(
                        top: -28,
                        left: thumbRadius - 24,
                        child: Container(
                          width: 48,
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF01579B),
                            borderRadius: BorderRadius.circular(6),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.2),
                                blurRadius: 4,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          child: Text(
                            '${_values[i].toStringAsFixed(1)}s',
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    // Thumb
                    Positioned(
                      top: _draggingIndex == i ? 28 : 0,
                      child: Container(
                        width: thumbRadius * 2,
                        height: thumbRadius * 2,
                        color: Colors.transparent, // Expand hit area
                        child: Center(
                          child: Container(
                            width: 24, // Visual thumb size
                            height: 24,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: Colors.white,
                              border: Border.all(
                                color: _draggingIndex == i ? Colors.cyan[700]! : Colors.grey[400]!,
                                width: 2,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: 0.1),
                                  blurRadius: 4,
                                  offset: const Offset(0, 2),
                                ),
                              ],
                            ),
                            child: Center(
                              child: Text(
                                _values[i].toStringAsFixed(1),
                                style: TextStyle(
                                  color: Colors.grey[900],
                                  fontSize: 8,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildZone(double start, double end, Color color) {
    final startPos = _valueToPosition(start.clamp(widget.min, widget.max));
    final endPos = _valueToPosition(end.clamp(widget.min, widget.max));
    final zoneWidth = (endPos - startPos).clamp(0.0, widget.width);
    
    if (zoneWidth <= 0) return const SizedBox.shrink();
    
    return Container(
      width: zoneWidth,
      color: color.withValues(alpha: 0.7),
    );
  }
}
