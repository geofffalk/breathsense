import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:audio_session/audio_session.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

import '../models/breath_data.dart';
import '../models/settings.dart';

/// Nordic UART Service UUIDs
final Guid uartServiceUuid = Guid("6e400001-b5a3-f393-e0a9-e50e24dcca9e");
final Guid rxCharUuid = Guid("6e400003-b5a3-f393-e0a9-e50e24dcca9e");
final Guid txCharUuid = Guid("6e400002-b5a3-f393-e0a9-e50e24dcca9e");

/// Known device name patterns for the breathing headset
const List<String> knownDeviceNames = ['sonar', 'bliss', 'breathcraft', 'vs-pulse', 'raspberrypi', 'breathing'];

/// Connection state
enum BleConnectionState {
  bluetoothOff,
  disconnected,
  scanning,
  connecting,
  connected,
}

/// BLE Service for communicating with the breathing headset
class BleService extends ChangeNotifier {
  BleConnectionState _connectionState = BleConnectionState.disconnected;
  BluetoothDevice? _connectedDevice;
  BluetoothDevice? _recentConnectedDevice;
  BluetoothCharacteristic? _txChar;
  
  StreamSubscription? _rxSubscription;
  StreamSubscription? _connectionSubscription;
  StreamSubscription? _scanSubscription;
  StreamSubscription? _audioDeviceSubscription;
  StreamSubscription? _adapterStateSubscription;
  StreamSubscription? _isScanningSubscription;

  String? _connectedAudioDeviceName;
  String _statusMessage = 'Initializing...';
  BreathingMode _currentMode = BreathingMode.open;
  bool _ledEnabled = true;
  bool _isBleConnected = false;
  bool _isConnecting = false;
  bool _bluetoothOn = false;

  // Current settings from firmware
  OpenBreathingSettings _openSettings = OpenBreathingSettings();
  GuidedBreathingSettings _guidedSettings = GuidedBreathingSettings();
  bool _settingsReceived = false;

  // Ring buffer for breath data (for graph)
  static const int bufferSize = 300;
  final List<double> _flowBuffer = List.filled(bufferSize, 0.0);
  final List<int> _phaseBuffer = List.filled(bufferSize, -1);
  final List<int> _depthBuffer = List.filled(bufferSize, 0);
  int _writeIndex = 0;
  int _sampleCount = 0;
  int _currentGuidedPhase = -1; // -1=none, 0=inhale, 1=hold_out, 2=exhale, 3=hold_in (matches firmware)

  final _breathDataController = StreamController<BreathData>.broadcast();

  BleConnectionState get connectionState => _connectionState;
  String get statusMessage => _statusMessage;
  BreathingMode get currentMode => _currentMode;
  bool get ledEnabled => _ledEnabled;
  Stream<BreathData> get breathDataStream => _breathDataController.stream;
  int get currentGuidedPhase => _currentGuidedPhase;
  bool get isConnected => _isBleConnected;
  bool get isBluetoothOff => _connectionState == BleConnectionState.bluetoothOff;
  
  OpenBreathingSettings get openSettings => _openSettings;
  GuidedBreathingSettings get guidedSettings => _guidedSettings;
  bool get settingsReceived => _settingsReceived;

  BleService() {
    debugPrint('[BLE] Service created');
    _startBleStateMonitoring();
    _startAudioBluetoothMonitoring();
  }

  /// Request Bluetooth permissions
  Future<void> _requestBluetoothAuthorization() async {
    if (Platform.isAndroid) {
      debugPrint('[BLE] Requesting Bluetooth authorization...');
      await Permission.location.request();
      await Permission.bluetoothScan.request();
      await Permission.bluetoothConnect.request();
    }
  }

  /// Clear the flow buffer - called on connect to show only live data
  void _clearBuffer() {
    _flowBuffer.fillRange(0, bufferSize, 0.0);
    _phaseBuffer.fillRange(0, bufferSize, -1);
    _depthBuffer.fillRange(0, bufferSize, 0);
    _writeIndex = 0;
    _sampleCount = 0;
    debugPrint('[BLE] Buffer cleared');
  }

  List<double> getFlowValues(int count) {
    if (_sampleCount == 0) return List.filled(count, 0.0);

    final result = <double>[];
    final available = _sampleCount < bufferSize ? _sampleCount : bufferSize;
    final start = (_writeIndex - available + bufferSize) % bufferSize;

    for (int i = 0; i < count && i < available; i++) {
      final idx = (start + (available - count + i)) % bufferSize;
      if (available - count + i >= 0) {
        result.add(_flowBuffer[idx]);
      } else {
        result.add(0.0);
      }
    }

    while (result.length < count) {
      result.insert(0, 0.0);
    }

    return result;
  }

  List<int> getPhaseValues(int count) {
    if (_sampleCount == 0) return List.filled(count, -1);

    final result = <int>[];
    final available = _sampleCount < bufferSize ? _sampleCount : bufferSize;
    final start = (_writeIndex - available + bufferSize) % bufferSize;

    for (int i = 0; i < count && i < available; i++) {
      final idx = (start + (available - count + i)) % bufferSize;
      if (available - count + i >= 0) {
        result.add(_phaseBuffer[idx]);
      } else {
        result.add(-1);
      }
    }

    while (result.length < count) {
      result.insert(0, -1);
    }

    return result;
  }

  List<int> getDepthValues(int count) {
    if (_sampleCount == 0) return List.filled(count, 0);

    final result = <int>[];
    final available = _sampleCount < bufferSize ? _sampleCount : bufferSize;
    final start = (_writeIndex - available + bufferSize) % bufferSize;

    for (int i = 0; i < count && i < available; i++) {
      final idx = (start + (available - count + i)) % bufferSize;
      if (available - count + i >= 0) {
        result.add(_depthBuffer[idx]);
      } else {
        result.add(0);
      }
    }

    while (result.length < count) {
      result.insert(0, 0);
    }

    return result;
  }

  void _startAudioBluetoothMonitoring() async {
    debugPrint('[BLE] Starting audio monitoring...');
    try {
      final session = await AudioSession.instance;
      final devices = await session.getDevices(includeInputs: false);
      debugPrint('[BLE] Initial audio devices: ${devices.length}');
      _checkAudioDevices(devices);
      
      _audioDeviceSubscription = session.devicesStream.listen((devices) {
        debugPrint('[BLE] Audio devices changed: ${devices.length}');
        _checkAudioDevices(devices);
      });
    } catch (e) {
      debugPrint('[BLE] Audio session error: $e');
      if (_bluetoothOn) {
        _updateStatus('Tap to scan for breath sensor');
      }
    }
  }

  void _checkAudioDevices(Set<AudioDevice> devices) {
    debugPrint('[BLE] Checking ${devices.length} audio devices...');
    
    for (final device in devices) {
      debugPrint('[BLE] Audio device: ${device.name}, type: ${device.type}');
    }
    
    final audioDevices = devices.toList();
    
    final index = audioDevices.indexWhere((device) =>
        device.type == AudioDeviceType.bluetoothA2dp &&
        knownDeviceNames.any((name) => device.name.toLowerCase().contains(name)));
    
    if (index > -1) {
      _connectedAudioDeviceName = audioDevices[index].name;
      debugPrint('[BLE] Found matching audio device: $_connectedAudioDeviceName');
      
      if (!_isBleConnected && _bluetoothOn) {
        _updateStatus('Scanning for breath sensor...');
        _startScanning();
      }
    } else {
      _connectedAudioDeviceName = null;
      debugPrint('[BLE] No matching audio device found');
      // Don't update status - we'll still scan for BLE devices
    }
  }

  void _startBleStateMonitoring() {
    debugPrint('[BLE] Starting BLE state monitoring...');
    _adapterStateSubscription = FlutterBluePlus.adapterState.listen((state) async {
      debugPrint('[BLE] Adapter state changed: $state');
      
      if (state == BluetoothAdapterState.on) {
        _bluetoothOn = true;
        if (_isBleConnected) {
          return; // Already connected
        }
        _updateConnectionState(BleConnectionState.disconnected);
        _updateStatus('Scanning for breath sensor...');
        _startScanning();
      } else if (state == BluetoothAdapterState.off) {
        _bluetoothOn = false;
        _updateConnectionState(BleConnectionState.bluetoothOff);
        _updateStatus('Turn on Bluetooth to connect');
      }
    });
  }

  Future<void> _startScanning() async {
    if (!_bluetoothOn) {
      debugPrint('[BLE] Cannot scan - Bluetooth is off');
      _updateConnectionState(BleConnectionState.bluetoothOff);
      _updateStatus('Turn on Bluetooth to connect');
      return;
    }
    
    if (_connectionState == BleConnectionState.scanning ||
        _connectionState == BleConnectionState.connecting ||
        _connectionState == BleConnectionState.connected) {
      debugPrint('[BLE] Already scanning/connecting/connected, skipping');
      return;
    }

    _updateConnectionState(BleConnectionState.scanning);
    
    _updateStatus('Scanning for breath sensor...');

    debugPrint('[BLE] Starting scan (no service filter - matching by name)');
    
    try {
      // Scan without service filter - CircuitPython may not advertise services properly
      await FlutterBluePlus.startScan(
        timeout: const Duration(seconds: 15),
      );
    } catch (e) {
      debugPrint('[BLE] Scan start error: $e');
      _updateConnectionState(BleConnectionState.disconnected);
      _updateStatus('Scan failed: $e');
      return;
    }

    _scanSubscription?.cancel();
    _scanSubscription = FlutterBluePlus.scanResults.listen((results) {
      debugPrint('[BLE] Scan results: ${results.length} devices');
      
      for (final result in results) {
        final name = result.device.platformName;
        debugPrint('[BLE] Found: "$name" (${result.device.remoteId})');
        
        if (name.isEmpty) continue;

        // Priority 1: Recent device
        if (_recentConnectedDevice != null && 
            result.device.remoteId == _recentConnectedDevice!.remoteId) {
          debugPrint('[BLE] Reconnecting to recent device');
          _connect(result.device);
          return;
        }

        // Priority 2: Exact name match with audio device
        if (_connectedAudioDeviceName != null && name == _connectedAudioDeviceName) {
          debugPrint('[BLE] Exact match with audio device name');
          _connect(result.device);
          return;
        }

        // Priority 3: Known name patterns
        final lowerName = name.toLowerCase();
        if (knownDeviceNames.any((pattern) => lowerName.contains(pattern))) {
          debugPrint('[BLE] Matched by name pattern');
          _connect(result.device);
          return;
        }
        
        // Priority 4: MAC address format (like 00:9F:38:AC:83:A5) - likely CircuitPython
        if (RegExp(r'^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$').hasMatch(name)) {
          debugPrint('[BLE] Matched MAC address format: $name');
          _connect(result.device);
          return;
        }
      }
    });

    _isScanningSubscription?.cancel();
    _isScanningSubscription = FlutterBluePlus.isScanning.listen((isScanning) {
      debugPrint('[BLE] isScanning: $isScanning');
      if (!isScanning && _connectionState == BleConnectionState.scanning) {
        _updateConnectionState(BleConnectionState.disconnected);
        _updateStatus('Breath sensor not found. Tap to retry.');
      }
    });
  }

  Future<void> _connect(BluetoothDevice device) async {
    if (_isConnecting) {
      debugPrint('[BLE] Already connecting, skipping');
      return;
    }
    
    _isConnecting = true;
    _connectedDevice = device;
    
    debugPrint('[BLE] Stopping scan...');
    await FlutterBluePlus.stopScan();
    _scanSubscription?.cancel();
    _isScanningSubscription?.cancel();

    _updateConnectionState(BleConnectionState.connecting);
    _updateStatus('Connecting to ${device.platformName}...');

    try {
      debugPrint('[BLE] Connecting to ${device.platformName}...');
      await device.connect(timeout: const Duration(seconds: 10));
      debugPrint('[BLE] Connected! Setting up...');
      
      _connectionSubscription?.cancel();
      _connectionSubscription = device.connectionState.listen((state) {
        debugPrint('[BLE] Connection state: $state');
        if (state == BluetoothConnectionState.connected) {
          if (!_isBleConnected) {
            _isBleConnected = true;
            _isConnecting = false;
            _recentConnectedDevice = device;
            _clearBuffer(); // Clear old data so graph shows only live data
            _setupDevice(device);
          }
        } else if (state == BluetoothConnectionState.disconnected) {
          _handleDisconnect();
        }
      });
    } catch (e) {
      debugPrint('[BLE] Connection error: $e');
      _isConnecting = false;
      _updateConnectionState(BleConnectionState.disconnected);
      _updateStatus('Connection failed. Tap to retry.');
      
      Future.delayed(const Duration(seconds: 3), () {
        if (_connectedAudioDeviceName != null && !_isBleConnected) {
          _startScanning();
        }
      });
    }
  }

  Future<void> _setupDevice(BluetoothDevice device) async {
    try {
      debugPrint('[BLE] Setting up device ${device.platformName}...');
      
      if (Platform.isAndroid) {
        try {
          await device.requestMtu(250);
          debugPrint('[BLE] MTU set to ${device.mtuNow}');
        } catch (e) {
          debugPrint('[BLE] MTU request failed: $e');
        }
      }

      debugPrint('[BLE] Discovering services...');
      final services = await device.discoverServices();
      debugPrint('[BLE] Found ${services.length} services');
      
      for (final service in services) {
        debugPrint('[BLE] Service: ${service.uuid}');
      }
      
      final uartService = services.firstWhere(
        (s) => s.uuid == uartServiceUuid,
        orElse: () => throw Exception('UART service not found'),
      );
      debugPrint('[BLE] Found UART service');

      _txChar = uartService.characteristics.firstWhere(
        (c) => c.uuid == txCharUuid,
        orElse: () => throw Exception('TX characteristic not found'),
      );
      debugPrint('[BLE] Found TX characteristic');

      final rxChar = uartService.characteristics.firstWhere(
        (c) => c.uuid == rxCharUuid,
        orElse: () => throw Exception('RX characteristic not found'),
      );
      debugPrint('[BLE] Found RX characteristic');

      await rxChar.setNotifyValue(true);
      debugPrint('[BLE] Notifications enabled');

      _rxSubscription?.cancel();
      _rxSubscription = rxChar.onValueReceived.listen(_handleIncomingData);

      _updateConnectionState(BleConnectionState.connected);
      _updateStatus('Connected to breath sensor');
      _currentMode = BreathingMode.open;  // Start in open breathing mode
      
      // Mark as ready and clear any buffered junk
      _incomingBuffer = '';
      _connectionReadyTime = DateTime.now();
      
      notifyListeners();
      
      // Auto-start Open Breathing mode so LEDs work immediately
      await Future.delayed(const Duration(milliseconds: 500));
      await _sendMessage('M,F\n'); // M,F is still the protocol command
      debugPrint('[BLE] Sent Open Breathing mode command');
      
      debugPrint('[BLE] Setup complete!');
    } catch (e) {
      debugPrint('[BLE] Setup error: $e');
      _updateConnectionState(BleConnectionState.disconnected);
      _updateStatus('Setup failed: $e');
    }
  }

  String _incomingBuffer = '';
  DateTime? _connectionReadyTime;

  void _handleIncomingData(List<int> data) {
    if (_connectionReadyTime == null) return;
    
    // Ignore any data for the first 5 seconds after connection to skip stale/buffered data
    if (DateTime.now().difference(_connectionReadyTime!).inSeconds < 5) {
      _incomingBuffer = ''; // Keep clearing to toss any partial junk
      return;
    }

    try {
      _incomingBuffer += utf8.decode(data);
      
      while (_incomingBuffer.contains('\n')) {
        final index = _incomingBuffer.indexOf('\n');
        final line = _incomingBuffer.substring(0, index).trim();
        _incomingBuffer = _incomingBuffer.substring(index + 1);

        if (line.isEmpty) continue;

        if (line.startsWith('B,')) {
          final breathData = BreathData.fromMessage(line);
          _flowBuffer[_writeIndex] = breathData.flowValue;
          _phaseBuffer[_writeIndex] = breathData.guidedPhase;
          _depthBuffer[_writeIndex] = breathData.depthColor;
          
          if (_currentGuidedPhase != breathData.guidedPhase) {
            _currentGuidedPhase = breathData.guidedPhase;
            notifyListeners();
          }
          
          _writeIndex = (_writeIndex + 1) % bufferSize;
          _sampleCount++;
          _breathDataController.add(breathData);
        } else if (line.startsWith('R,')) {
          _parseSettingsResponse(line);
        }
      }
    } catch (e) {
      debugPrint('[BLE] Parse error: $e');
      // If decode fails, clear buffer to recover
      _incomingBuffer = '';
    }
  }

  void _parseSettingsResponse(String message) {
    try {
      final parts = message.split(',');
      if (parts.length >= 12) {
        _openSettings = OpenBreathingSettings(
          veryShortMax: double.parse(parts[1]),
          shortMax: double.parse(parts[2]),
          mediumMax: double.parse(parts[3]),
          longMax: double.parse(parts[4]),
          sensitivity: int.parse(parts[5]),
        );
        _guidedSettings = GuidedBreathingSettings(
          inhaleLength: double.parse(parts[6]),
          holdAfterInhale: double.parse(parts[7]),
          exhaleLength: double.parse(parts[8]),
          holdAfterExhale: double.parse(parts[9]),
          ledStart: int.parse(parts[10]),
          ledEnd: int.parse(parts[11]),
        );
        _settingsReceived = true;
        debugPrint('[BLE] Settings received');
        notifyListeners();
      }
    } catch (e) {
      debugPrint('[BLE] Settings parse error: $e');
    }
  }

  Future<void> requestSettings() async {
    await _sendMessage('Q\n');
  }

  void _handleDisconnect() {
    debugPrint('[BLE] Disconnected');
    _rxSubscription?.cancel();
    _connectionSubscription?.cancel();
    _connectedDevice = null;
    _txChar = null;
    _currentMode = BreathingMode.open;
    _isBleConnected = false;
    _isConnecting = false;
    _connectionReadyTime = null;
    _incomingBuffer = '';
    _currentGuidedPhase = -1;

    _updateConnectionState(BleConnectionState.disconnected);
    
    if (_connectedAudioDeviceName != null) {
      _updateStatus('Disconnected. Reconnecting...');
      Future.delayed(const Duration(seconds: 2), () {
        if (_bluetoothOn) _startScanning();
      });
    } else {
      _updateStatus('Disconnected');
    }
  }

  Future<void> _sendMessage(String message) async {
    if (_txChar == null || !isConnected) {
      debugPrint('[BLE] Cannot send: not connected');
      return;
    }

    try {
      final bytes = utf8.encode(message);
      // Use write WITH response for reliable delivery
      await _txChar!.write(bytes, withoutResponse: false);
      debugPrint('[BLE] Sent: ${message.trim()}');
    } catch (e) {
      debugPrint('[BLE] Send error: $e');
    }
  }

  Future<void> setMode(BreathingMode mode) async {
    await _sendMessage(mode.toMessage());
    _currentMode = mode;
    notifyListeners();
  }

  Future<void> toggleLed() async {
    _ledEnabled = !_ledEnabled;
    await _sendMessage('L,${_ledEnabled ? 1 : 0}\n');
    notifyListeners();
  }

  Future<void> updateOpenSettings(OpenBreathingSettings newSettings) async {
    _openSettings = newSettings;
    if (_currentMode == BreathingMode.open) {
      await _sendMessage(newSettings.toMessage());
    }
    notifyListeners();
  }

  Future<void> sendGuidedBreathingSettings(GuidedBreathingSettings settings) async {
    await _sendMessage(settings.toMessage());
  }

  Future<void> sendSensitivity(int preset) async {
    await _sendMessage('S,C,$preset\n');
  }

  void startManualScan() {
    debugPrint('[BLE] Manual scan requested');
    _scanSubscription?.cancel();
    _isScanningSubscription?.cancel();
    FlutterBluePlus.stopScan();
    _updateConnectionState(BleConnectionState.disconnected);
    Future.delayed(const Duration(milliseconds: 200), () {
      _startScanning();
    });
  }
  
  /// Open system Bluetooth settings
  Future<void> openBluetoothSettings() async {
    debugPrint('[BLE] Opening Bluetooth settings...');
    try {
      await FlutterBluePlus.turnOn();
    } catch (e) {
      debugPrint('[BLE] Could not open settings: $e');
    }
  }

  void _updateConnectionState(BleConnectionState state) {
    debugPrint('[BLE] State: $state');
    _connectionState = state;
    notifyListeners();
  }

  void _updateStatus(String message) {
    debugPrint('[BLE] Status: $message');
    _statusMessage = message;
    notifyListeners();
  }

  @override
  void dispose() {
    debugPrint('[BLE] Disposing service');
    _rxSubscription?.cancel();
    _connectionSubscription?.cancel();
    _scanSubscription?.cancel();
    _isScanningSubscription?.cancel();
    _audioDeviceSubscription?.cancel();
    _adapterStateSubscription?.cancel();
    _breathDataController.close();
    _connectedDevice?.disconnect();
    super.dispose();
  }
}
