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
    "inhale_s": 5.0,
    "hold_in_s": 5.0,
    "exhale_s": 5.0,
    "hold_out_s": 5.0,
    "led_start": 2,
    "led_end": 9,
    # Mood detection settings
    "mood_calm_ratio": 1.5,         # E/I ratio for calm detection
    "mood_calm_variability": 0.5,   # RMSSD threshold for calm (lower = calmer)
    "mood_focus_consistency": 0.5,  # Std dev for focus (lower = more focused)
    "mood_calibration_breaths": 6,  # Breaths before showing scores
    # LED state and color scheme
    "led_enabled": 1,               # 1 = on, 0 = off
    "color_scheme": 0,              # 0 = default, 1 = high contrast, 2 = cool tones
    # Guided breathing flow thresholds (sensitivity)
    "exhale_threshold": 0.8,        # Flow magnitude to detect exhale (0.3-1.0, higher = less sensitive)
    "inhale_threshold": 0.5,        # Flow magnitude to detect inhale (0.3-1.0, higher = less sensitive)
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
    Format: R,{very_short},{short},{medium},{long},{sensitivity},{inhale},{hold_in},{exhale},{hold_out},{led_start},{led_end},{calm_ratio},{calm_var},{focus_con},{cal_breaths},{led_enabled},{color_scheme}
    """
    return "R,{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
        settings.get("very_short_max", 2.0),
        settings.get("short_max", 3.5),
        settings.get("medium_max", 5.0),
        settings.get("long_max", 6.5),
        settings.get("sensitivity", 5),
        settings.get("inhale_s", 5.0),
        settings.get("hold_in_s", 5.0),
        settings.get("exhale_s", 5.0),
        settings.get("hold_out_s", 5.0),
        settings.get("led_start", 2),
        settings.get("led_end", 9),
        settings.get("mood_calm_ratio", 1.5),
        settings.get("mood_calm_variability", 0.5),
        settings.get("mood_focus_consistency", 0.5),
        settings.get("mood_calibration_breaths", 6),
        settings.get("led_enabled", 1),
        settings.get("color_scheme", 0),
    )
