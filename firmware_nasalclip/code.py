# code.py - BreathSense Nasal Clip Firmware
# Simplified main loop for XIAO nRF52840 without LEDs

import time
import gc
import board
import supervisor

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from config import BLE_TX_INTERVAL_MS, BLE_LIVE_HZ
from breath_detector import BreathDetector, PH_IDLE, PH_INH, PH_EXH
from settings_storage import load_settings, save_settings, settings_to_message


def log(msg):
    """Debug logging (only when USB connected)."""
    try:
        if supervisor.runtime.usb_connected:
            print("[{:.2f}] {}".format(time.monotonic(), msg))
    except Exception:
        pass


# ========== BLE Setup ==========
ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

# Load device name
try:
    with open("asset_id.txt", "r") as f:
        ble.name = f.read().strip()
except Exception:
    ble.name = "BreathClip"

log("Device name: " + ble.name)

# ========== Settings ==========
settings = load_settings()
log("Settings loaded")

# ========== Breath Detection ==========
detector = BreathDetector()

# Apply loaded settings
detector.apply_color_thresholds(
    settings["very_short_max"],
    settings["short_max"],
    settings["medium_max"],
    settings["long_max"],
)
detector.apply_sensitivity(settings["sensitivity"])

detector.mood.set_thresholds(
    1.5,  # calm_ratio (not used in simplified version)
    0.5,  # calm_variability
    0.5,  # focus_consistency
    settings.get("mood_calibration_breaths", 6),
)

# ========== State ==========
last_tx_ms = 0
live_interval_ms = int(1000 / BLE_LIVE_HZ)
gc_counter = 0


def now_ms():
    return int(time.monotonic() * 1000)


def send_breath_data():
    """Send breath data over BLE."""
    global last_tx_ms

    now = now_ms()
    if now - last_tx_ms < live_interval_ms:
        return
    last_tx_ms = now

    try:
        state = detector.get_state()
    except Exception as e:
        log("get_state err: " + str(e))
        return

    unworn = 1 if state.get("unworn", False) else 0

    # Format: B,{ts},{phase},{flow},{depth},{guided},{exhale},{inhale},{cycle},{smoothness},{peak},{symmetry},{unworn}
    msg = "B,{},{},{:.3f},{},{},{:.2f},{:.2f},{:.2f},{},{:.2f},{},{}\n".format(
        now & 0xFFFFFFFF,
        state.get("phase", 0),
        state.get("norm", 0.0),
        state.get("depth_color", 0),
        -1,  # No guided mode
        state.get("exhale_dur", 0.0),
        state.get("inhale_dur", 0.0),
        state.get("cycle_dur", 0.0),
        state.get("smoothness", 100),
        state.get("peak_flow", 0.0),
        state.get("symmetry", 50),
        unworn,
    )

    try:
        uart.write(msg.encode("utf-8"))
    except Exception as e:
        log("TX err: " + str(e))


def send_settings():
    """Send current settings to app."""
    try:
        msg = settings_to_message(settings)
        uart.write(msg.encode("utf-8"))
        log("Settings sent")
    except Exception as e:
        log("Settings TX err: " + str(e))


def parse_message(msg):
    """Parse incoming message from app."""
    global settings

    msg = msg.strip()
    if not msg:
        return

    parts = msg.split(",")
    if len(parts) < 1:
        return

    cmd = parts[0]

    if cmd == "S" and len(parts) >= 3:
        setting_type = parts[1].upper()

        if setting_type == "F" and len(parts) >= 6:
            # Depth thresholds: S,F,veryShort,short,medium,long
            try:
                vs = float(parts[2])
                s = float(parts[3])
                m = float(parts[4])
                l = float(parts[5])
                detector.apply_color_thresholds(vs, s, m, l)
                settings["very_short_max"] = vs
                settings["short_max"] = s
                settings["medium_max"] = m
                settings["long_max"] = l
                save_settings(settings)
                log("Thresholds saved")
            except Exception:
                pass

        elif setting_type == "C" and len(parts) >= 3:
            # Sensitivity: S,C,{0-9}
            try:
                preset = int(parts[2])
                detector.apply_sensitivity(preset)
                settings["sensitivity"] = preset
                save_settings(settings)
                log("Sensitivity: " + str(preset))
            except Exception:
                pass

    elif cmd == "Q":
        # Query settings
        send_settings()


def handle_rx():
    """Handle incoming BLE data."""
    if not uart.in_waiting:
        return

    try:
        data = uart.read(uart.in_waiting)
        if data:
            try:
                msg = data.decode("utf-8")
            except Exception:
                msg = "".join([chr(b) for b in data if 32 <= b <= 126 or b == 10 or b == 13])
            
            if msg:
                log("RX: " + msg.strip())
                for line in msg.split("\n"):
                    if line.strip():
                        parse_message(line)
    except Exception as e:
        log("RX err: " + str(e))


def garbage_collect():
    """Periodic garbage collection."""
    global gc_counter
    gc_counter += 1
    if gc_counter >= 200:
        gc.collect()
        gc_counter = 0


# ========== Main Loop ==========
log("BOOT NasalClip")

try:
    while True:
        was_connected = False
        is_advertising = False

        while True:
            # Breath detection always runs
            detector.tick()

            if ble.connected:
                if not was_connected:
                    was_connected = True
                    is_advertising = False
                    if uart.in_waiting:
                        uart.read(uart.in_waiting)
                    log("BLE connected")
                    send_settings()

                handle_rx()
                send_breath_data()

            else:
                if was_connected:
                    was_connected = False
                    is_advertising = False
                    log("BLE disconnected")

                if not is_advertising:
                    try:
                        ble.start_advertising(advertisement)
                        is_advertising = True
                        log("Advertising...")
                    except Exception:
                        pass

            garbage_collect()
            time.sleep(0.01)  # ~100Hz loop

except Exception as e:
    log("FATAL: " + str(e))
    time.sleep(1)
