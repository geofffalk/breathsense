# settings_storage.py - Settings persistence
# Simplified for nasal clip (no LED settings)

import json

SETTINGS_FILE = "/settings.json"

DEFAULT_SETTINGS = {
    # Breath depth thresholds (seconds)
    "very_short_max": 2.0,
    "short_max": 3.5,
    "medium_max": 5.0,
    "long_max": 6.5,
    # Sensitivity preset (0-9)
    "sensitivity": 5,
    # Mood detection settings
    "mood_calibration_breaths": 6,
}


def load_settings() -> dict:
    """Load settings from file."""
    try:
        with open(SETTINGS_FILE, "r") as f:
            saved = json.load(f)
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
    except Exception as e:
        print("Settings save error:", e)


def settings_to_message(settings: dict) -> str:
    """Convert settings to BLE message."""
    return "R,{},{},{},{},{},{}\n".format(
        settings.get("very_short_max", 2.0),
        settings.get("short_max", 3.5),
        settings.get("medium_max", 5.0),
        settings.get("long_max", 6.5),
        settings.get("sensitivity", 5),
        settings.get("mood_calibration_breaths", 6),
    )
