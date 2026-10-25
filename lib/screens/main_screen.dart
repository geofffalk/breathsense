import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/settings.dart';
import '../services/ble_service.dart';
import '../widgets/breath_graph.dart';
import '../widgets/mode_selector.dart';
import '../widgets/mood_indicators.dart';
import '../widgets/stress_indicator.dart';
import 'report_screen.dart';
import 'settings_screen.dart';

/// Main screen with breath graph, mode selector, and connection status
class MainScreen extends StatelessWidget {
  const MainScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Row(
          children: [
            Image.asset(
              'assets/logo.png',
              height: 36,
              fit: BoxFit.contain,
            ),
            const SizedBox(width: 8),
            RichText(
              text: const TextSpan(
                children: [
                  TextSpan(
                    text: 'Breath',
                    style: TextStyle(
                      color: Color(0xFF1565C0), // Blue 800
                      fontWeight: FontWeight.w900,
                      fontSize: 26,
                      letterSpacing: 1,
                    ),
                  ),
                  TextSpan(
                    text: 'Sense',
                    style: TextStyle(
                      color: Color(0xFF2E7D32), // Green 800
                      fontWeight: FontWeight.w900,
                      fontSize: 26,
                      letterSpacing: 1,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              const SizedBox(height: 10),
              // Connection status
              _ConnectionStatus(),

              const SizedBox(height: 12),

              // Mode selector - moved above graph for better flow
              const ModeSelector(),

              const SizedBox(height: 8),

              // Show Lights toggle - right justified
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Consumer<BleService>(
                  builder: (context, bleService, _) {
                    return Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Text(
                          'Show lights on headset',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color: bleService.isConnected ? Colors.black87 : Colors.grey[400],
                          ),
                        ),
                        const SizedBox(width: 8),
                        Switch(
                          value: bleService.ledEnabled,
                          onChanged: bleService.isConnected ? (value) {
                            bleService.toggleLed();
                          } : null,
                          activeColor: Colors.cyan[700],
                        ),
                      ],
                    );
                  },
                ),
              ),

              const SizedBox(height: 8),

              // Unified dark section: Graph + Mood indicators
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1A2E),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  children: [
                    // Breath graph
                    const BreathGraph(height: 220),
                    
                    const SizedBox(height: 12),
                    
                    // Mode-specific readout: mood, guided phase or heart rate
                    _ModeReadout(),
                  ],
                ),
              ),

              const SizedBox(height: 16),
              
              // Generate Session Report button
              _GenerateReportButton(),

              const SizedBox(height: 24), // Replaced Spacer with fixed spacing for scroll view

              // Current mode indicator
              _CurrentModeIndicator(),

              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConnectionStatus extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, child) {
        final isConnected = bleService.isConnected;
        final status = bleService.statusMessage;
        final connectionState = bleService.connectionState;

        // Show prominent alert banner when disconnected
        if (!isConnected) {
          return _DisconnectedAlert(
            connectionState: connectionState,
            status: status,
            onTap: () => bleService.startManualScan(),
          );
        }

        // Connected: show compact status bar (with unworn warning if needed)
        final isUnworn = bleService.isUnworn;
        
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          margin: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(
            color: isUnworn 
                ? const Color(0xFFFFF3E0) // Orange tint when unworn
                : const Color(0xFFE1F5FE), // Light Cyan background
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isUnworn 
                  ? const Color(0xFFFFB74D) // Orange border when unworn
                  : const Color(0xFF81D4FA), // Brand blue border
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF01579B).withAlpha(13),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                isUnworn ? Icons.warning_amber_rounded : Icons.bluetooth_connected, 
                color: isUnworn ? const Color(0xFFE65100) : const Color(0xFF0288D1), 
                size: 20,
              ),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  isUnworn 
                      ? 'Not detecting breath — check sensor is attached and under nostril'
                      : status,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: isUnworn ? const Color(0xFFE65100) : const Color(0xFF01579B), 
                    fontSize: 14, 
                    fontWeight: FontWeight.bold,
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

class _DisconnectedAlert extends StatelessWidget {
  final BleConnectionState connectionState;
  final String status;
  final VoidCallback onTap;

  const _DisconnectedAlert({
    required this.connectionState,
    required this.status,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final bleService = context.read<BleService>();
    final isBluetoothOff = connectionState == BleConnectionState.bluetoothOff;
    final isScanning = connectionState == BleConnectionState.scanning ||
                       connectionState == BleConnectionState.connecting;

    // Determine colors and icons
    Color primaryColor;
    IconData icon;
    String title;
    
    if (isBluetoothOff) {
      primaryColor = Colors.grey[700]!;
      icon = Icons.bluetooth_disabled;
      title = 'Bluetooth is Off';
    } else if (isScanning) {
      primaryColor = const Color(0xFF0288D1); // Brand Blue
      icon = Icons.bluetooth_searching;
      title = 'Connecting...';
    } else {
      primaryColor = const Color(0xFF455A64); // Professional Blue-Grey for "Not Found"
      icon = Icons.bluetooth_disabled;
      title = 'Breath Sensor Not Found';
    }

    return GestureDetector(
      onTap: isBluetoothOff ? () => bleService.openBluetoothSettings() : (isScanning ? null : onTap),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        margin: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: primaryColor.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: primaryColor.withOpacity(0.2),
            width: 1.5,
          ),
        ),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, color: primaryColor, size: 24),
                const SizedBox(width: 10),
                Text(
                  title,
                  style: TextStyle(
                    color: primaryColor,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            if (!isScanning) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: primaryColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  isBluetoothOff ? 'ENABLE BLUETOOTH' : 'TAP TO RETRY',
                  style: TextStyle(
                    color: primaryColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1.2,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}


class _CurrentModeIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, child) {
        if (!bleService.isConnected) {
          return Container(
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.symmetric(horizontal: 16),
            decoration: BoxDecoration(
              color: const Color(0xFFE1F5FE), // Unified Light Cyan
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF81D4FA)), // Brand blue border
            ),
            child: const Text(
              'Headset runs Open Breathing when not connected to app',
              style: TextStyle(
                color: Color(0xFF01579B), // Unified Deep Blue
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
            ),
          );
        }

        final mode = bleService.currentMode;
        String message;
        IconData icon;
        Color color = Colors.grey;

        switch (mode) {
          case BreathingMode.open:
            message = 'Open Breathing active on headset';
            icon = Icons.air;
            color = Colors.green[700]!; // Darker for light theme
            break;
          case BreathingMode.guided:
            message = 'Guided Breathing active on headset';
            icon = Icons.timeline;
            color = Colors.cyan[700]!; // Darker for light theme
            break;
          case BreathingMode.heart:
            message = 'Heart Monitor active on headset';
            icon = Icons.favorite;
            color = Colors.red[700]!;
            break;
          default:
            message = 'Headset LEDs off (standby)';
            icon = Icons.power_settings_new;
        }

        return Container(
          padding: const EdgeInsets.all(12),
          margin: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(
            color: Colors.grey[50],
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey[200]!, width: 1),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.02),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 10),
              Text(
                message,
                style: TextStyle(color: color.withValues(alpha: 0.9), fontSize: 14, fontWeight: FontWeight.bold),
              ),
            ],
          ),
        );
      },
    );
  }
}

/// Displays mood indicators (Open), phase indicator (Guided) or heart rate (Heart)
class _ModeReadout extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, child) {
        if (!bleService.isConnected) {
          return const SizedBox.shrink();
        }

        // Heart mode doesn't depend on the breath sensor being worn
        if (bleService.currentMode == BreathingMode.heart) {
          return _HeartRateIndicator(
            bpm: bleService.heartBpm,
            hasSignal: bleService.hasPulseSignal,
            beatCount: bleService.heartBeatCount,
            stress: bleService.heartStress,
            hrvMs: bleService.heartHrv,
          );
        }

        // Hide mood indicators when not detecting breath (unworn)
        if (bleService.isUnworn) {
          return const SizedBox.shrink();
        }

        // In Open mode: show calm and focus indicators (meditation in report only)
        if (bleService.currentMode == BreathingMode.open) {
          return Column(
            children: [
              StressIndicator(
                stressScore: bleService.currentStressScore,
                isCalibrating: bleService.isMoodCalibrating,
              ),
              FocusIndicator(
                focusScore: bleService.currentFocusScore,
                isCalibrating: bleService.isMoodCalibrating,
              ),
            ],
          );
        }

        // In Guided mode: show phase indicator
        if (bleService.currentMode == BreathingMode.guided) {
          return _GuidedPhaseIndicator(phase: bleService.currentGuidedPhase);
        }

        return const SizedBox.shrink();
      },
    );
  }
}

/// Heart rate and HRV readout; the heart icon beats in time with the headset
/// LEDs, with the same lub-dub animation and stress colour (green -> amber -> red)
class _HeartRateIndicator extends StatefulWidget {
  final int bpm;
  final bool hasSignal;
  final int beatCount;
  final int stress; // 0-100 from the headset
  final int hrvMs; // HRV (RMSSD); 0 until measured

  const _HeartRateIndicator({
    required this.bpm,
    required this.hasSignal,
    required this.beatCount,
    required this.stress,
    required this.hrvMs,
  });

  @override
  State<_HeartRateIndicator> createState() => _HeartRateIndicatorState();
}

class _HeartRateIndicatorState extends State<_HeartRateIndicator>
    with SingleTickerProviderStateMixin {
  // Matching firmware config.py (Heart LED Display)
  static const double _counterBeat = 0.55;
  static const Color _calmColor = Color(0xFF00FF28);
  static const Color _midColor = Color(0xFFFFAA00);
  static const Color _hotColor = Color(0xFFFF0000);

  // Beat animation at 60 BPM (s): (start, rise, hold, fall, height), as in
  // firmware led_control.py: main beat, then a smaller counter-beat
  static const List<List<double>> _pulses = [
    [0.00, 0.08, 0.06, 0.18, 1.0],
    [0.36, 0.07, 0.04, 0.17, _counterBeat],
  ];
  static const double _beatSeconds = 0.64; // End of the counter-beat

  late final AnimationController _controller;
  double _timeScale = 1.0;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this);
  }

  @override
  void didUpdateWidget(_HeartRateIndicator oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.beatCount != oldWidget.beatCount && _showBpm) {
      // Faster rates shorten the beat so it finishes before the next one
      _timeScale = widget.bpm > 60 ? 60.0 / widget.bpm : 1.0;
      _controller.duration =
          Duration(milliseconds: (_beatSeconds * _timeScale * 1000).round());
      _controller.forward(from: 0.0);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  bool get _showBpm => widget.hasSignal && widget.bpm > 0;

  Color get _beatColor {
    final k = (widget.stress / 100.0).clamp(0.0, 1.0);
    return k < 0.5
        ? Color.lerp(_calmColor, _midColor, k * 2.0)!
        : Color.lerp(_midColor, _hotColor, (k - 0.5) * 2.0)!;
  }

  /// Fill 0..1 at [t] seconds into the (60 BPM) beat animation
  static double _fill(double t) {
    var fill = 0.0;
    for (final p in _pulses) {
      var u = t - p[0];
      final rise = p[1], hold = p[2], fall = p[3], height = p[4];
      double f;
      if (u < 0) {
        f = 0.0;
      } else if (u < rise) {
        final x = u / rise;
        f = height * (1.0 - (1.0 - x) * (1.0 - x));
      } else if ((u -= rise) < hold) {
        f = height;
      } else if ((u -= hold) < fall) {
        final x = u / fall;
        f = height * (1.0 - x * x);
      } else {
        f = 0.0;
      }
      if (f > fill) fill = f;
    }
    return fill;
  }

  @override
  Widget build(BuildContext context) {
    final showBpm = _showBpm;
    final color = showBpm ? _beatColor : Colors.grey[500]!;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.06),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(showBpm ? 0.6 : 0.2)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          AnimatedBuilder(
            animation: _controller,
            builder: (context, child) {
              final t = _controller.value * _beatSeconds;
              final fill = showBpm ? _fill(t) : 0.0;
              return Transform.scale(scale: 1.0 + 0.35 * fill, child: child);
            },
            child: Icon(
              showBpm ? Icons.favorite : Icons.favorite_border,
              color: color,
              size: 40,
            ),
          ),
          const SizedBox(width: 16),
          if (showBpm)
            Flexible(
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      '${widget.bpm}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 44,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      'BPM',
                      style: TextStyle(
                        color: Colors.grey[400],
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(width: 20),
                    Text(
                      widget.hrvMs > 0 ? '${widget.hrvMs}' : '--',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      'HRV ms',
                      style: TextStyle(
                        color: Colors.grey[400],
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                      ),
                    ),
                  ],
                ),
              ),
            )
          else
            Flexible(
              child: Text(
                'Clip sensor to earlobe',
                style: TextStyle(
                  color: Colors.grey[400],
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Guided breathing phase indicator (INHALE/HOLD/EXHALE)
class _GuidedPhaseIndicator extends StatelessWidget {
  final int phase;
  
  const _GuidedPhaseIndicator({required this.phase});
  
  // Color schemes matching firmware: (inhale, hold, exhale)
  static const List<List<Color>> _colorSchemes = [
    // 0: Default - Green/Orange/Cyan
    [Color(0xFF00FF00), Color(0xFFFF3200), Color(0xFF00FFFF)],
    // 1: High Contrast - Yellow/Purple/White
    [Color(0xFFFFFF00), Color(0xFF8000FF), Color(0xFFFFFFFF)],
    // 2: Cool Tones - Blue/Magenta/White
    [Color(0xFF0064FF), Color(0xFFFF0080), Color(0xFFFFFFFF)],
  ];
  
  /// Check if a color is light enough to need dark text
  bool _isLightColor(Color color) {
    // Use relative luminance calculation
    final luminance = (0.299 * color.red + 0.587 * color.green + 0.114 * color.blue) / 255;
    return luminance > 0.5;
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, _) {
        final schemeId = bleService.guidedSettings.colorScheme.clamp(0, 2);
        final colors = _colorSchemes[schemeId];
        final settings = bleService.guidedSettings;
        
        String text;
        Color bgColor;
        
        switch (phase) {
          case 0: // INHALE
            text = 'INHALE';
            bgColor = colors[0];
            break;
          case 1: // HOLD (In) - skip if duration is 0
            if (settings.holdAfterInhale == 0) {
              return const SizedBox.shrink();
            }
            text = 'HOLD';
            bgColor = colors[1];
            break;
          case 2: // EXHALE
            text = 'EXHALE';
            bgColor = colors[2];
            break;
          case 3: // HOLD (Out) - skip if duration is 0
            if (settings.holdAfterExhale == 0) {
              return const SizedBox.shrink();
            }
            text = 'HOLD';
            bgColor = colors[1];
            break;
          default:
            text = 'SYNCING...';
            bgColor = Colors.grey;
        }
        
        // Determine text color based on background luminance
        final isLight = _isLightColor(bgColor);
        final textColor = isLight ? Colors.black87 : Colors.white;

        return Container(
          width: double.infinity,
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: bgColor.withOpacity(0.3),
                blurRadius: 12,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Center(
            child: SizedBox(
              height: 50,
              child: FittedBox(
                fit: BoxFit.contain,
                child: Text(
                  text,
                  style: TextStyle(
                    color: textColor,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 4,
                    shadows: isLight ? [
                      Shadow(
                        color: Colors.black.withOpacity(0.2),
                        offset: const Offset(1, 1),
                        blurRadius: 2,
                      ),
                    ] : null,
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

class _SimpleBoldLogo extends StatelessWidget {
  final double size;

  const _SimpleBoldLogo({this.size = 32});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF0288D1), // Brand Blue
            Color(0xFF00BCD4), // Brand Cyan
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0288D1).withOpacity(0.2),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Center(
        child: Text(
          'B',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w900,
            fontSize: size * 0.65,
            height: 1.1,
          ),
        ),
      ),
    );
  }
}

/// Button to generate and view session report
class _GenerateReportButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, child) {
        // Show button if we have session data, even when disconnected
        // Hide when in Guided mode (no mood data collected in Guided)
        if (!bleService.hasSessionData || 
            (bleService.isConnected && bleService.currentMode != BreathingMode.open)) {
          return const SizedBox.shrink();
        }

        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            children: [
              ElevatedButton.icon(
                onPressed: () {
                  final session = bleService.currentSession;
                  if (session != null) {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ReportScreen(sessionData: session),
                      ),
                    );
                  }
                },
                icon: const Icon(Icons.analytics_outlined, size: 20),
                label: Text(
                  bleService.hasSessionData 
                      ? 'View Session Report' 
                      : 'Session Report (collecting data...)',
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: bleService.hasSessionData 
                      ? const Color(0xFF4A6572) 
                      : Colors.grey[400],
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: bleService.hasSessionData ? 2 : 0,
                ),
              ),
              const SizedBox(height: 8),
              TextButton.icon(
                onPressed: bleService.hasSessionData ? () {
                  showDialog(
                    context: context,
                    builder: (ctx) => AlertDialog(
                      title: const Text('Reset Session?'),
                      content: const Text('This will clear all recorded breath and mood data. Are you sure?'),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(ctx),
                          child: const Text('Cancel'),
                        ),
                        TextButton(
                          onPressed: () {
                            bleService.resetSession();
                            Navigator.pop(ctx);
                          },
                          child: const Text('Reset', style: TextStyle(color: Colors.red)),
                        ),
                      ],
                    ),
                  );
                } : null,
                icon: Icon(Icons.refresh, size: 18, color: bleService.hasSessionData ? Colors.grey[600] : Colors.grey[400]),
                label: Text(
                  'Reset Session Data',
                  style: TextStyle(
                    color: bleService.hasSessionData ? Colors.grey[600] : Colors.grey[400],
                    fontSize: 13,
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
