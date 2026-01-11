# settings_storage.py - Settings persistence for firmware
# Saves and loads settings from JSON file on the device

import json

SETTINGS_FILE = "/settings.json"

# Default settings
DEFAULT_SETTINGS = {
    # Open breathing color thresholds (seconds)
    "very_short_max": 2.0,
    "short_max": 3.5,
    "medium_max": 5.0,
    "long_max": 6.5,
    # Sensitivity preset (0-9)
    "sensitivity": 5,
    # Guided breathing durations (seconds)
    "inhale_s": 4.0,
    "hold_in_s": 2.0,
    "exhale_s": 5.0,
    "hold_out_s": 1.0,
    "led_start": 2,
    "led_end": 9,
}


def load_settings() -> dict:
    """Load settings from file, returning defaults if not found."""
    try:
        with open(SETTINGS_FILE, "r") as f:
            saved = json.load(f)
        # Merge with defaults (in case new keys were added)
        settings = dict(DEFAULT_SETTINGS)
        settings.update(saved)
        return settings
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    """Save settings to file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
    except OSError as e:
        if e.args[0] == 30: # Read-only filesystem
            print("Settings save ignored: Filesystem is read-only (unplug from PC if you want to save)")
        else:
            print("Settings save error:", e)
    except Exception as e:
        print("Settings save error:", e)


def settings_to_message(settings: dict) -> str:
    """
    Convert settings dict to BLE message for app.
    Format: R,{very_short},{short},{medium},{long},{sensitivity},{inhale},{hold_in},{exhale},{hold_out},{led_start},{led_end}
    """
    return "R,{},{},{},{},{},{},{},{},{},{},{}\n".format(
        settings.get("very_short_max", 2.0),
        settings.get("short_max", 3.5),
        settings.get("medium_max", 5.0),
        settings.get("long_max", 6.5),
        settings.get("sensitivity", 5),
        settings.get("inhale_s", 4.0),
        settings.get("hold_in_s", 2.0),
        settings.get("exhale_s", 5.0),
        settings.get("hold_out_s", 1.0),
        settings.get("led_start", 2),
        settings.get("led_end", 9),
    )
