import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/settings.dart';
import '../services/ble_service.dart';
import '../widgets/threshold_slider.dart';

/// Settings screen: breath display and scoring settings (all sent to the headset)
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  // Open Breathing settings
  late OpenBreathingSettings _openSettings;
  OpenBreathingSettings? _originalOpenSettings; // For tracking changes

  // Mood Detection settings
  late MoodDetectionSettings _moodSettings;
  
  // Debounce timer for sensitivity auto-send
  Timer? _sensitivityTimer;
  
  bool _initialized = false;
  
  @override
  void dispose() {
    _sensitivityTimer?.cancel();
    try {
      context.read<BleService>().removeListener(_onBleServiceUpdate);
    } catch (_) {}
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _openSettings = OpenBreathingSettings();
    _moodSettings = MoodDetectionSettings();
    
    // Load settings from BLE service after build
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadSettingsFromFirmware();
    });
  }
  
  void _loadSettingsFromFirmware() {
    final bleService = context.read<BleService>();
    
    // If settings already received, use them
    if (bleService.settingsReceived) {
      setState(() {
        _openSettings = bleService.openSettings.copyWith();
        _originalOpenSettings = bleService.openSettings.copyWith();
        _moodSettings = bleService.moodSettings.copyWith();
        _initialized = true;
      });
    } else if (bleService.isConnected) {
      // Request settings from firmware
      bleService.requestSettings();
    }
    
    // Listen for settings updates
    bleService.addListener(_onBleServiceUpdate);
  }
  
  void _onBleServiceUpdate() {
    if (!mounted) return; // Prevent context access after unmount
    
    final bleService = context.read<BleService>();
    if (bleService.settingsReceived && !_initialized) {
      setState(() {
        _openSettings = bleService.openSettings.copyWith();
        _originalOpenSettings = bleService.openSettings.copyWith();
        _moodSettings = bleService.moodSettings.copyWith();
        _initialized = true;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    final bleService = context.watch<BleService>();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
        title: const Text(
          'Settings',
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Breath settings
            _buildSectionHeader('Breath', Icons.air),
            const SizedBox(height: 8),
            _buildOpenBreathingSettings(bleService),

            const SizedBox(height: 32),

            // Mood Detection
            _buildSectionHeader('Mood Detection', Icons.psychology),
            const SizedBox(height: 8),
            _buildMoodSettings(bleService),

            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: Colors.cyan[700], size: 20),
        const SizedBox(width: 8),
        Text(
          title,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.grey[900],
          ),
        ),
      ],
    );
  }

  Widget _buildOpenBreathingSettings(BleService bleService) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50], // Very light background
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Exhale Duration Thresholds',
                  style: TextStyle(color: Color(0xFF424242), fontSize: 14, fontWeight: FontWeight.bold),
                ),
              ),
              TextButton(
                onPressed: () => setState(() {
                  _openSettings = _openSettings.copyWith(
                    veryShortMax: 2.0,
                    shortMax: 3.5,
                    mediumMax: 5.0,
                    longMax: 6.5,
                  );
                }),
                child: Text('Reset', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Drag dividers to set color thresholds based on exhale length.',
            style: TextStyle(color: Colors.grey[700], fontSize: 12, fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: 16),

          ThresholdRangeSlider(
            veryShortMax: _openSettings.veryShortMax,
            shortMax: _openSettings.shortMax,
            mediumMax: _openSettings.mediumMax,
            longMax: _openSettings.longMax,
            min: 0.5,
            max: 10.0,
            onChanged: (veryShort, short, medium, long) {
              setState(() {
                _openSettings = _openSettings.copyWith(
                  veryShortMax: veryShort,
                  shortMax: short,
                  mediumMax: medium,
                  longMax: long,
                );
              });
            },
          ),

          const SizedBox(height: 24),
          
          // Breath Sensitivity slider
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Breath Sensitivity', style: TextStyle(color: Colors.grey[900], fontWeight: FontWeight.w500)),
              Text(
                '${_openSettings.sensitivity}',
                style: TextStyle(color: Colors.cyan[700], fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Text('Low', style: TextStyle(color: Colors.grey, fontSize: 12)),
              Expanded(
                child: Slider(
                  value: _openSettings.sensitivity.toDouble(),
                  min: 0,
                  max: 9,
                  divisions: 9,
                  activeColor: Colors.cyan[700],
                  inactiveColor: Colors.grey[200],
                  onChanged: (v) => _updateSensitivity(v.round()),
                ),
              ),
              const Text('High', style: TextStyle(color: Colors.grey, fontSize: 12)),
            ],
          ),

          const SizedBox(height: 24),

          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: (bleService.isConnected && _hasOpenSettingsChanged())
                  ? () {
                      bleService.updateOpenSettings(_openSettings);
                      setState(() => _originalOpenSettings = _openSettings.copyWith());
                    }
                  : null,
              icon: const Icon(Icons.send),
              label: const Text('Send to Headset'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.cyan,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  bool _hasOpenSettingsChanged() {
    if (_originalOpenSettings == null) return true;
    return _openSettings.veryShortMax != _originalOpenSettings!.veryShortMax ||
           _openSettings.shortMax != _originalOpenSettings!.shortMax ||
           _openSettings.mediumMax != _originalOpenSettings!.mediumMax ||
           _openSettings.longMax != _originalOpenSettings!.longMax;
  }

  Widget _buildSensitivitySettings(BleService bleService) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Sensitivity', style: TextStyle(color: Colors.grey[900], fontWeight: FontWeight.w500)),
              Text(
                '${_openSettings.sensitivity}',
                style: TextStyle(color: Colors.cyan[700], fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Text('Low', style: TextStyle(color: Colors.grey, fontSize: 12)),
              Expanded(
                child: Slider(
                  value: _openSettings.sensitivity.toDouble(),
                  min: 0,
                  max: 9,
                  divisions: 9,
                  activeColor: Colors.cyan[700],
                  inactiveColor: Colors.grey[200],
                  onChanged: (v) => _updateSensitivity(v.round()),
                ),
              ),
              const Text('High', style: TextStyle(color: Colors.grey, fontSize: 12)),
            ],
          ),
        ],
      ),
    );
  }
  
  /// Update sensitivity with debounced auto-send
  void _updateSensitivity(int value) {
    setState(() {
      _openSettings = _openSettings.copyWith(sensitivity: value);
    });
    
    _sensitivityTimer?.cancel();
    _sensitivityTimer = Timer(const Duration(milliseconds: 300), () {
      final bleService = Provider.of<BleService>(context, listen: false);
      if (bleService.isConnected) {
        bleService.sendSensitivity(_openSettings.sensitivity);
      }
    });
  }

  Widget _buildMoodSettings(BleService bleService) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Fine-tune how your breathing patterns are interpreted.',
            style: TextStyle(color: Colors.grey[700], fontSize: 12),
          ),
          const SizedBox(height: 16),
          
          // Calibration Breaths (always visible)
          Text('Calibration Breaths', style: TextStyle(color: Colors.grey[900], fontWeight: FontWeight.w500)),
          const SizedBox(height: 4),
          Text(
            'Number of breaths before mood readings start.',
            style: TextStyle(color: Colors.grey[600], fontSize: 11),
          ),
          Row(
            children: [
              Expanded(
                child: Slider(
                  value: _moodSettings.calibrationBreaths.toDouble(),
                  min: 3,
                  max: 15,
                  divisions: 12,
                  activeColor: Colors.orange[700],
                  inactiveColor: Colors.grey[200],
                  onChanged: (v) => _updateMoodSettings(
                    _moodSettings.copyWith(calibrationBreaths: v.round()),
                  ),
                ),
              ),
              Text(
                '${_moodSettings.calibrationBreaths}',
                style: TextStyle(color: Colors.orange[700], fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          
          const SizedBox(height: 12),
          
          // Advanced Mode Toggle
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: _moodSettings.advancedMode ? Colors.indigo[50] : Colors.grey[100],
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: _moodSettings.advancedMode ? Colors.indigo[200]! : Colors.grey[300]!,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.tune,
                  size: 18,
                  color: _moodSettings.advancedMode ? Colors.indigo[700] : Colors.grey[600],
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Advanced Mode',
                    style: TextStyle(
                      color: _moodSettings.advancedMode ? Colors.indigo[700] : Colors.grey[700],
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                Switch(
                  value: _moodSettings.advancedMode,
                  activeColor: Colors.indigo,
                  onChanged: (v) => setState(() {
                    _moodSettings = _moodSettings.copyWith(advancedMode: v);
                  }),
                ),
              ],
            ),
          ),
          
          // Advanced settings (hidden by default)
          if (_moodSettings.advancedMode) ...[
            const SizedBox(height: 20),
            
            // Threshold Settings Section
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.indigo[100]!),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        'Detection Thresholds',
                        style: TextStyle(
                          color: Colors.indigo[700],
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                      const Spacer(),
                      TextButton(
                        onPressed: () => _updateMoodSettings(
                          _moodSettings.copyWith(
                            calmRatio: 1.5,
                            calmVariability: 0.10,
                            focusConsistency: 0.15,
                          ),
                        ),
                        child: Text('Reset', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  
                  // Calm Ratio
                  _buildMoodSliderWithDesc(
                    label: 'Calm Threshold (E/I Ratio)',
                    description: 'Exhale/inhale ratio needed to show as calm.',
                    value: _moodSettings.calmRatio,
                    min: 0.5,
                    max: 3.0,
                    unit: 'x',
                    activeColor: Colors.teal,
                    onChanged: (v) => _updateMoodSettings(
                      _moodSettings.copyWith(calmRatio: v),
                    ),
                  ),
                  
                  // Calm Variability
                  _buildMoodSliderWithDesc(
                    label: 'Calm Variability',
                    description: 'Breath consistency needed to show as calm.',
                    value: _moodSettings.calmVariability,
                    min: 0.05,
                    max: 0.50,
                    unit: '',
                    displayAsPercent: true,
                    activeColor: Colors.teal,
                    onChanged: (v) => _updateMoodSettings(
                      _moodSettings.copyWith(calmVariability: v),
                    ),
                  ),
                  
                  // Focus Consistency
                  _buildMoodSliderWithDesc(
                    label: 'Focus Threshold',
                    description: 'Rhythm consistency needed to show as focused.',
                    value: _moodSettings.focusConsistency,
                    min: 0.05,
                    max: 0.50,
                    unit: '',
                    displayAsPercent: true,
                    activeColor: Colors.purple,
                    onChanged: (v) => _updateMoodSettings(
                      _moodSettings.copyWith(focusConsistency: v),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Stress Factor Weights Section
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.indigo[100]!),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        'Stress Factor Weights',
                        style: TextStyle(
                          color: Colors.indigo[700],
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                      const Spacer(),
                      TextButton(
                        onPressed: () => _updateMoodSettings(
                          _moodSettings.copyWith(
                            stressRatioWeight: 0.35,
                            stressDurationWeight: 0.20,
                            stressSmoothnessWeight: 0.15,
                            stressPeakFlowWeight: 0.15,
                            stressRmssdWeight: 0.15,
                          ),
                        ),
                        child: Text('Reset', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                      ),
                    ],
                  ),
                  Text(
                    'Adjust how much each factor contributes to stress calculation.',
                    style: TextStyle(color: Colors.grey[600], fontSize: 11),
                  ),
                  const SizedBox(height: 12),
                  
                  _buildWeightSlider('E/I Ratio', _moodSettings.stressRatioWeight, Colors.teal,
                    (v) => _updateMoodSettings(_moodSettings.copyWith(stressRatioWeight: v))),
                  _buildWeightSlider('Duration', _moodSettings.stressDurationWeight, Colors.blue,
                    (v) => _updateMoodSettings(_moodSettings.copyWith(stressDurationWeight: v))),
                  _buildWeightSlider('Smoothness', _moodSettings.stressSmoothnessWeight, Colors.green,
                    (v) => _updateMoodSettings(_moodSettings.copyWith(stressSmoothnessWeight: v))),
                  _buildWeightSlider('Breath Depth', _moodSettings.stressPeakFlowWeight, Colors.orange,
                    (v) => _updateMoodSettings(_moodSettings.copyWith(stressPeakFlowWeight: v))),
                  _buildWeightSlider('Variability', _moodSettings.stressRmssdWeight, Colors.red,
                    (v) => _updateMoodSettings(_moodSettings.copyWith(stressRmssdWeight: v))),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
  
  Widget _buildWeightSlider(String label, double value, Color color, ValueChanged<double> onChanged) {
    // Calculate normalized percentage (relative to total of all weights)
    final total = _moodSettings.stressRatioWeight +
                  _moodSettings.stressDurationWeight +
                  _moodSettings.stressSmoothnessWeight +
                  _moodSettings.stressPeakFlowWeight +
                  _moodSettings.stressRmssdWeight;
    final normalizedPercent = total > 0 ? (value / total * 100).round() : 0;
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 90,
            child: Text(label, style: TextStyle(color: Colors.grey[700], fontSize: 12)),
          ),
          Expanded(
            child: SliderTheme(
              data: SliderThemeData(
                trackHeight: 4,
                thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
              ),
              child: Slider(
                value: value,
                min: 0.0,
                max: 0.6,
                activeColor: color,
                inactiveColor: Colors.grey[200],
                onChanged: onChanged,
              ),
            ),
          ),
          SizedBox(
            width: 40,
            child: Text(
              '$normalizedPercent%',
              style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
  
  /// Update mood settings and auto-apply to MoodAnalyzer
  void _updateMoodSettings(MoodDetectionSettings newSettings) {
    setState(() {
      _moodSettings = newSettings;
    });
    
    // Send to the headset, which computes the scores
    final bleService = Provider.of<BleService>(context, listen: false);
    if (bleService.isConnected) {
      bleService.sendMoodSettings(_moodSettings);
    }
  }
  
  Widget _buildMoodSliderWithDesc({
    required String label,
    required String description,
    required double value,
    required double min,
    required double max,
    required String unit,
    required Color activeColor,
    required ValueChanged<double> onChanged,
    bool displayAsPercent = false,
  }) {
    final displayValue = displayAsPercent 
        ? '${(value * 100).round()}%'
        : '${value.toStringAsFixed(2)}$unit';
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Flexible(
                child: Text(label, style: TextStyle(color: Colors.grey[900], fontWeight: FontWeight.w500)),
              ),
              Text(
                displayValue,
                style: TextStyle(color: activeColor, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            description,
            style: TextStyle(color: Colors.grey[600], fontSize: 11),
          ),
          Slider(
            value: value.clamp(min, max),
            min: min,
            max: max,
            activeColor: activeColor,
            inactiveColor: Colors.grey[200],
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}
