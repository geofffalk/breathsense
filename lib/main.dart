import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/main_screen.dart';
import 'services/ble_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const BreathCraftApp());
}

class BreathCraftApp extends StatelessWidget {
  const BreathCraftApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => BleService(),
      child: MaterialApp(
        title: 'BREATHCRAFT',
        debugShowCheckedModeBanner: false,
        theme: ThemeData.light().copyWith(
          colorScheme: ColorScheme.light(
            primary: Colors.cyan[700]!,
            secondary: Colors.cyanAccent[700]!,
            surface: Colors.white,
          ),
          scaffoldBackgroundColor: Colors.white,
          appBarTheme: const AppBarTheme(
            backgroundColor: Colors.white,
            elevation: 0,
            iconTheme: IconThemeData(color: Colors.black87),
          ),
          sliderTheme: SliderThemeData(
            activeTrackColor: Colors.cyan[700],
            inactiveTrackColor: Colors.cyan[100],
            thumbColor: Colors.cyan[700],
            overlayColor: Colors.cyan[700]!.withOpacity(0.2),
          ),
        ),
        home: const MainScreen(),
      ),
    );
  }
}
