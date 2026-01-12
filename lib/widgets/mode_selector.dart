import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/settings.dart';
import '../services/ble_service.dart';

/// Mode selector widget with Open Breathing, Guided Breathing, and Off buttons
class ModeSelector extends StatelessWidget {
  const ModeSelector({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, bleService, child) {
        final currentMode = bleService.currentMode;
        final isConnected = bleService.isConnected;

        return Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
          child: Row(
            children: [
              Expanded(
                child: _ModeButton(
                  label: 'Open',
                  icon: Icons.air,
                  isSelected: currentMode == BreathingMode.open,
                  isEnabled: isConnected,
                  color: const Color(0xFF4CAF50), // Vibrant Green
                  onPressed: () => bleService.setMode(BreathingMode.open),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _ModeButton(
                  label: 'Guided',
                  icon: Icons.timeline,
                  isSelected: currentMode == BreathingMode.guided,
                  isEnabled: isConnected,
                  color: const Color(0xFF03A9F4), // Vibrant Blue/Cyan
                  onPressed: () => bleService.setMode(BreathingMode.guided),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ModeButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isSelected;
  final bool isEnabled;
  final Color? color;
  final VoidCallback onPressed;

  const _ModeButton({
    required this.label,
    required this.icon,
    required this.isSelected,
    required this.isEnabled,
    this.color,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final themeColor = color ?? Theme.of(context).colorScheme.primary;
    // Only show as selected if both selected AND enabled (connected)
    final showSelected = isSelected && isEnabled;
    final displayColor = showSelected
        ? themeColor
        : isEnabled
            ? Colors.grey[500] ?? Colors.grey // Darker icons when enabled but not selected
            : Colors.grey[300] ?? Colors.grey; // Lighter grey when disabled

    return GestureDetector(
      onTap: isEnabled ? onPressed : null,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: BoxDecoration(
          color: showSelected
              ? themeColor.withOpacity(0.85)
              : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: showSelected ? themeColor : Colors.grey[300]!,
            width: showSelected ? 2.5 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(showSelected ? 0.1 : 0.02),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon, 
              color: showSelected ? Colors.white : displayColor, 
              size: 28
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: showSelected ? Colors.white : displayColor,
                fontWeight: showSelected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

