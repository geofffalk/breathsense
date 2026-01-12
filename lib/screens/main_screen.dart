import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/settings.dart';
import '../services/ble_service.dart';
import '../widgets/breath_graph.dart';
import '../widgets/mode_selector.dart';
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

              const SizedBox(height: 12), // Reduced from 16

              // Breath graph
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: BreathGraph(height: 240), // Slightly reduced from 250
              ),

              const SizedBox(height: 8),

              // Show Lights toggle - standard switch, right justified
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Consumer<BleService>(
                  builder: (context, bleService, _) {
                    return Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Text(
                          'Show lights',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w500,
                            color: bleService.isConnected ? Colors.black87 : Colors.grey[400],
                          ),
                        ),
                        const SizedBox(width: 12),
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

              const SizedBox(height: 12),

              // Mode selector
              const ModeSelector(),

              // Guided Phase Indicator (only in Guided mode)
              // Moved here to prevent mode buttons from jumping
              _GuidedPhaseDisplay(),

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

        // Connected: show compact status bar
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          margin: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(
            color: const Color(0xFFE1F5FE), // Light Cyan background
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFF81D4FA)), // Brand blue border
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF01579B).withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.bluetooth_connected, color: Color(0xFF0288D1), size: 20),
              const SizedBox(width: 8),
              Text(
                status,
                style: const TextStyle(color: Color(0xFF01579B), fontSize: 14, fontWeight: FontWeight.bold),
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

class _GuidedPhaseDisplay extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, child) {
        if (!bleService.isConnected || bleService.currentMode != BreathingMode.guided) {
          return const SizedBox.shrink();
        }

        final phase = bleService.currentGuidedPhase;
        String text;
        Color color;
        
        switch (phase) {
          case 0: // INHALE
            text = 'INHALE';
            color = Colors.green;
            break;
          case 1: // HOLD (In)
            text = 'HOLD';
            color = Colors.red;
            break;
          case 2: // EXHALE
            text = 'EXHALE';
            color = Colors.cyan;
            break;
          case 3: // HOLD (Out)
            text = 'HOLD';
            color = Colors.red;
            break;
          default:
            text = 'SYNCING...';
            color = Colors.grey;
        }

        return Container(
          width: double.infinity,
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
          decoration: BoxDecoration(
            color: color, // Solid brand color fill
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: color.withValues(alpha: 0.3),
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
                  style: const TextStyle(
                    color: Colors.white, // High contrast white text
                    fontWeight: FontWeight.w900,
                    letterSpacing: 4,
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
