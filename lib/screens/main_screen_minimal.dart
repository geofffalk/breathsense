import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/ble_service.dart';

/// Minimal main screen for crash testing
class MainScreen extends StatelessWidget {
  const MainScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          'BREATHCRAFT',
          style: TextStyle(
            color: Color(0xFF01579B),
            fontWeight: FontWeight.w900,
            fontSize: 24,
          ),
        ),
      ),
      body: Center(
        child: Consumer<BleService>(
          builder: (context, bleService, _) {
            return Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  bleService.statusMessage,
                  style: const TextStyle(fontSize: 18),
                ),
                const SizedBox(height: 20),
                Text(
                  'Connection: ${bleService.connectionState}',
                  style: const TextStyle(fontSize: 16),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
