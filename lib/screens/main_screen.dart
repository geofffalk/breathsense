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
                    
                    // Mode-specific mood indicators
                    _BreathingModeIndicator(),
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

/// Displays either mood indicators (Open mode) or phase indicator (Guided mode)
class _BreathingModeIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, child) {
        if (!bleService.isConnected) {
          return const SizedBox.shrink();
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
        // Only show when connected, in Open mode, and has session data
        if (!bleService.isConnected || bleService.currentMode != BreathingMode.open) {
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
