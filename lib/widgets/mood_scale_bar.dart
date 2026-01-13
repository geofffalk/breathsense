import 'package:flutter/material.dart';

/// Animated scale bar showing a marker position on a horizontal scale.
/// Left = stressed (red), Right = calm (green).
class MoodScaleBar extends StatelessWidget {
  final String label;
  final double value; // 0.0 (left/stressed) to 1.0 (right/calm)
  final String? displayValue; // Optional value text (e.g., "1.2", "4.8s")
  
  const MoodScaleBar({
    super.key,
    required this.label,
    required this.value,
    this.displayValue,
  });

  @override
  Widget build(BuildContext context) {
    final clampedValue = value.clamp(0.0, 1.0);
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          // Label
          SizedBox(
            width: 90,
            child: Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          // Scale bar with animated marker
          Expanded(
            child: Container(
              height: 16,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                gradient: LinearGradient(
                  colors: [
                    Colors.red[300]!,
                    Colors.orange[200]!,
                    Colors.yellow[200]!,
                    Colors.lightGreen[200]!,
                    Colors.green[300]!,
                  ],
                ),
              ),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final markerX = clampedValue * (constraints.maxWidth - 12) + 6;
                  return Stack(
                    children: [
                      // Center line
                      Positioned(
                        left: constraints.maxWidth / 2 - 0.5,
                        top: 0,
                        bottom: 0,
                        child: Container(
                          width: 1,
                          color: Colors.black26,
                        ),
                      ),
                      // Animated marker
                      AnimatedPositioned(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeOut,
                        left: markerX - 6,
                        top: 2,
                        child: Container(
                          width: 12,
                          height: 12,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.grey[800]!, width: 2),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.2),
                                blurRadius: 2,
                                offset: const Offset(0, 1),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ),
          // Value display
          if (displayValue != null)
            SizedBox(
              width: 50,
              child: Text(
                displayValue!,
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.grey[500],
                  fontFamily: 'monospace',
                ),
              ),
            ),
        ],
      ),
    );
  }
}
