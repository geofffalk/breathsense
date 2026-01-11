# code.py - Breathing App V2 Firmware
# Simplified main loop with optimized BLE communication

import time
import gc
import board
import supervisor

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from config import BLE_TX_INTERVAL_MS, BLE_LIVE_HZ
from breath_detector import BreathDetector, PH_IDLE, PH_INH, PH_EXH
from led_control import (
    OpenBreathingLED, GuidedBreathingLED, hide_all,
    play_startup_animation, play_ble_connected_animation,
)
from settings_storage import load_settings, save_settings, settings_to_message

# ========== Modes ==========
MODE_STANDBY = 0  # BLE connected, LEDs off, just sending data
MODE_OPEN = 1     # Open Breathing mode
MODE_GUIDED = 2   # Guided Breathing mode


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

# Load device name from asset_id.txt
try:
    with open("asset_id.txt", "r") as f:
        ble.name = f.read().strip()
except Exception:
    ble.name = "BreathingV2"

log("Device name: " + ble.name)

# ========== Settings ==========
settings = load_settings()
log("Settings loaded")

# ========== Breath Detection ==========
detector = BreathDetector()

# Apply loaded settings to detector
detector.apply_color_thresholds(
    settings["very_short_max"],
    settings["short_max"],
    settings["medium_max"],
    settings["long_max"],
)
detector.apply_sensitivity(settings["sensitivity"])

# ========== LED Controllers ==========
open_led = OpenBreathingLED(detector)
guided_led = GuidedBreathingLED(detector)

# Apply loaded settings to guided LED
guided_led.set_durations(
    settings["inhale_s"],
    settings["hold_in_s"],
    settings["exhale_s"],
    settings["hold_out_s"],
)
guided_led.set_range(
    settings["led_start"],
    settings["led_end"],
)

# ========== State ==========
current_mode = MODE_OPEN  # Default to open breathing when standalone
last_tx_ms = 0
live_interval_ms = int(1000 / BLE_LIVE_HZ)
gc_counter = 0


def now_ms():
    return int(time.monotonic() * 1000)


def send_breath_data():
    """Send breath data to app: B,{timestamp},{phase},{flow},{depth_color}"""
    global last_tx_ms

    now = now_ms()
    if now - last_tx_ms < live_interval_ms:
        return
    last_tx_ms = now

    state = detector.get_state()
    guided_phase = -1
    if current_mode == MODE_GUIDED:
        guided_phase = guided_led.get_phase()

    msg = "B,{},{},{:.3f},{},{}\n".format(
        now & 0xFFFFFFFF,
        state["phase"],
        state["norm"],
        state["depth_color"],
        guided_phase,
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
        log("Settings sent to app")
    except Exception as e:
        log("Settings TX err: " + str(e))


def update_and_save_settings(key, value):
    """Update a setting value and save to storage."""
    global settings
    settings[key] = value
    save_settings(settings)


def parse_message(msg):
    """Parse incoming message from app."""
    global current_mode, settings

    msg = msg.strip()
    if not msg:
        return

    parts = msg.split(",")
    if len(parts) < 1:
        return

    cmd = parts[0]

    if cmd == "M" and len(parts) >= 2:
        # Mode command: M,{F|G|O}
        mode_char = parts[1].upper()
        if mode_char == "F":
            current_mode = MODE_OPEN
            log("Mode: OPEN")
        elif mode_char == "G":
            current_mode = MODE_GUIDED
            guided_led.reset()
            log("Mode: GUIDED")
        elif mode_char == "O":
            current_mode = MODE_STANDBY
            hide_all()
            log("Mode: STANDBY")

    elif cmd == "S" and len(parts) >= 3:
        # Settings command
        setting_type = parts[1].upper()

        if setting_type == "F" and len(parts) >= 6:
            # Open breathing settings: S,F,veryShort,short,medium,long
            try:
                vs = float(parts[2])
                s = float(parts[3])
                m = float(parts[4])
                l = float(parts[5])
                detector.apply_color_thresholds(vs, s, m, l)
                # Save to settings
                settings["very_short_max"] = vs
                settings["short_max"] = s
                settings["medium_max"] = m
                settings["long_max"] = l
                save_settings(settings)
                log("Color thresholds saved")
            except Exception:
                pass

        elif setting_type == "G" and len(parts) >= 8:
            # Guided breathing settings: S,G,inhale,holdIn,exhale,holdOut,ledStart,ledEnd
            try:
                inh = float(parts[2])
                hi = float(parts[3])
                exh = float(parts[4])
                ho = float(parts[5])
                ls = int(parts[6])
                le = int(parts[7])
                
                guided_led.set_durations(inh, hi, exh, ho)
                guided_led.set_range(ls, le)
                
                # Save to settings
                settings["inhale_s"] = inh
                settings["hold_in_s"] = hi
                settings["exhale_s"] = exh
                settings["hold_out_s"] = ho
                settings["led_start"] = ls
                settings["led_end"] = le
                save_settings(settings)
                log("Guided settings saved")
            except Exception as e:
                log("Guided set err: " + str(e))

        elif setting_type == "C" and len(parts) >= 3:
            # Sensitivity: S,C,{0-9}
            try:
                preset = int(parts[2])
                detector.apply_sensitivity(preset)
                settings["sensitivity"] = preset
                save_settings(settings)
                log("Sensitivity saved: " + str(preset))
            except Exception:
                pass

    elif cmd == "Q":
        # Query settings: Q
        send_settings()


def handle_rx():
    """Handle incoming BLE data."""
    if not uart.in_waiting:
        return

    try:
        data = uart.read(uart.in_waiting)
        if data:
            # CircuitPython's decode often doesn't take keyword arguments
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
    """Periodic garbage collection to prevent memory buildup."""
    global gc_counter
    gc_counter += 1
    if gc_counter >= 200:
        gc.collect()
        gc_counter = 0


# ========== Main Loop ==========
log("BOOT V2")
play_startup_animation()

try:
    while True:
        was_connected = False
        is_advertising = False

        while True:
            # Breath detection always runs
            detector.tick()

            if ble.connected:
                if not was_connected:
                    # Just connected - start in Open mode (LEDs work immediately)
                    was_connected = True
                    is_advertising = False
                    current_mode = MODE_OPEN  # Start in Open mode, not Standby
                    # Purge any stale data in UART buffer
                    if uart.in_waiting:
                        uart.read(uart.in_waiting)
                        log("UART buffer purged")
                    log("BLE connected - Open mode")
                    play_ble_connected_animation()
                    # Send settings to app on connect
                    send_settings()

                # Handle incoming commands
                handle_rx()

                # Send breath data to app
                send_breath_data()

                # Update LEDs based on mode
                if current_mode == MODE_OPEN:
                    open_led.tick()
                elif current_mode == MODE_GUIDED:
                    guided_led.tick()
                # STANDBY: LEDs stay off

            else:
                if was_connected:
                    # Disconnected - return to open breathing
                    was_connected = False
                    is_advertising = False
                    current_mode = MODE_OPEN
                    log("BLE disconnected")

                # Keep advertising when not connected
                if not is_advertising:
                    try:
                        ble.start_advertising(advertisement)
                        is_advertising = True
                        log("Advertising...")
                    except Exception:
                        pass

                # Standalone: always run open breathing
                open_led.tick()

            garbage_collect()
            time.sleep(0.01)  # ~100Hz loop

except Exception as e:
    log("FATAL: " + str(e))
    time.sleep(1)
