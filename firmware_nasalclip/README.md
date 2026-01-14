# BreathSense Nasal Clip Firmware

Simplified firmware for **XIAO nRF52840** without LED support.

## Hardware Setup

### Wiring
```
     3.3V
       │
      [10kΩ]  ← Fixed resistor
       │
       ├───────► A0 (analog input)
       │
      [NTC]   ← 10kΩ NTC thermistor
       │
      GND
```

### Components
- Seeed XIAO nRF52840
- 10kΩ NTC thermistor
- 10kΩ resistor
- Small LiPo battery (40-100mAh)

## Installation

1. **Install CircuitPython** on XIAO nRF52840:
   - Download from [circuitpython.org/board/seeeduino_xiao_nrf52840](https://circuitpython.org/board/seeeduino_xiao_nrf52840/)
   - Double-tap reset to enter bootloader
   - Drag `.uf2` file to the `XIAO-SENSE` drive

2. **Copy files** to CIRCUITPY drive:
   ```
   code.py
   config.py
   breath_detector.py
   breath_metrics.py
   settings_storage.py
   asset_id.txt
   lib/
   ```

3. **Copy required libraries** to `lib/` folder:
   - `adafruit_ble/` (entire folder)
   - Any other dependencies

4. **Customize device name** (optional):
   - Edit `asset_id.txt` to change BLE name

## BLE Protocol

Same as headset version - broadcasts `B,` messages with breath data.

The app will connect and receive data automatically.

## Differences from Headset Version

| Feature | Headset | Nasal Clip |
|---------|---------|------------|
| LEDs | ✅ 40 NeoPixels | ❌ None |
| Guided breathing | ✅ | ❌ |
| Open breathing mode | ✅ | ✅ (data only) |
| BLE data | ✅ | ✅ |
| Sensitivity settings | ✅ | ✅ |
