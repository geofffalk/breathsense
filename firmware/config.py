# Breathing App V2 Configuration

# ===== Breath Detection Parameters =====
# These values have been tuned for optimal thermistor-based breath detection

# Sampling rate
FS_HZ = 100.0  # Hz

# Temperature filter smoothing
ALPHA_FAST = 0.22  # Fast EMA for temperature
ALPHA_SLOW = 0.004  # Slow EMA (baseline)
ALPHA_FLOW = 0.22  # Flow signal smoothing
DERIV_GAIN = 0.18  # Derivative boost

# Phase detection thresholds
TH_FRAC_START = 0.30  # Threshold to start a phase
TH_FRAC_END = 0.20    # Threshold to end a phase
MIN_PHASE_S = 0.20    # Minimum phase duration (seconds)

# Scaling
EMA_MAG = 0.20        # Magnitude EMA factor
LEAK_DECAY = 0.994    # Peak decay
SCALE_FLOOR = 0.02    # Minimum scale

# Idle detection
IDLE_MAG_FRAC = 0.20   # Idle magnitude threshold
IDLE_SLOPE_FRAC = 0.06 # Idle slope threshold
IDLE_HOLD_S = 2.2      # Idle confirmation hold

# ===== Color-to-Depth Thresholds (seconds) =====
# Exhale duration maps to LED color
DEFAULT_VERY_SHORT_MAX = 2.0   # <= this: Red
DEFAULT_SHORT_MAX = 3.5        # <= this: White
DEFAULT_MEDIUM_MAX = 5.0       # <= this: Light Blue
DEFAULT_LONG_MAX = 6.5         # <= this: Purple
# > LONG_MAX: Deep Blue

# ===== LED Colors (RGB) =====
COLOR_RED = (255, 0, 0)
COLOR_WHITE = (150, 150, 150)
COLOR_LIGHT_BLUE = (0, 160, 160)
COLOR_PURPLE = (110, 0, 160)
COLOR_DEEP_BLUE = (0, 0, 180)

# ===== Guided Breathing Defaults (seconds) =====
DEFAULT_INHALE_S = 5.0
DEFAULT_HOLD_IN_S = 5.0
DEFAULT_EXHALE_S = 5.0
DEFAULT_HOLD_OUT_S = 5.0

# ===== Guided Breathing Color Schemes =====
# Each scheme: (inhale_color, hold_color, exhale_color)
GUIDED_COLOR_SCHEMES = [
    # 0: Default - Green/Orange/Cyan
    ((0, 255, 0), (255, 20, 0), (0, 255, 255)),
    # 1: High Contrast - Yellow/Purple/White (color-blind friendly)
    ((255, 255, 0), (128, 0, 255), (255, 255, 255)),
    # 2: Cool Tones - Blue/Magenta/White
    ((0, 100, 255), (255, 0, 128), (255, 255, 255)),
]

# ===== Sensitivity Presets =====
# Each preset: (alpha_flow, deriv_gain, th_start, th_end)
SENSITIVITY_PRESETS = [
    (0.28, 0.06, 0.45, 0.30),  # 0: Least sensitive
    (0.26, 0.08, 0.42, 0.28),
    (0.24, 0.10, 0.40, 0.26),
    (0.22, 0.12, 0.38, 0.24),
    (0.20, 0.12, 0.36, 0.22),
    (0.18, 0.12, 0.35, 0.20),  # 5: Default
    (0.16, 0.14, 0.33, 0.20),
    (0.14, 0.16, 0.31, 0.18),
    (0.12, 0.18, 0.29, 0.16),
    (0.10, 0.20, 0.27, 0.14),  # 9: Most sensitive
]

# ===== BLE Settings =====
BLE_TX_INTERVAL_MS = 50   # Time between BLE transmissions
BLE_LIVE_HZ = 10.0        # Live data send rate to app

# ===== Hardware =====
LED_PIN_LEFT = "D9"
LED_PIN_RIGHT = "D7"
NUM_LEDS = 20
THERMISTOR_PIN = "A0"

# Thermistor circuit values
ADC_MAX = 65535.0
VSUP = 3.3
R_REF = 10000.0  # Reference resistor
R0 = 10000.0     # Thermistor resistance at T0
BETA = 3435.0    # Beta coefficient
T0_C = 25.0      # Reference temperature

# ===== Pulse Sensor (Heart mode) =====
PULSE_PIN = "A1"               # PulseSensor signal wire
PULSE_INVERT = False           # True if your sensor's beats dip instead of rise
PULSE_MIN_AMP = 500            # Min peak-to-peak (16-bit ADC units) to count beats; raise if noise triggers beats
PULSE_MIN_IBI_MS = 300         # Fastest accepted beat interval (200 BPM)
PULSE_MAX_IBI_MS = 2000        # Slowest accepted beat interval (30 BPM)
PULSE_SIGNAL_TIMEOUT_MS = 2500 # No beat for this long -> flatline
HEART_LIVE_HZ = 25.0           # Heart waveform send rate to app

# Standalone LED mode when no app is connected: "open" or "heart"
STANDALONE_MODE = "open"

# ===== Heart LED Display =====
HEART_BPM_LOW = 55.0           # BPM mapped to the calmest look
HEART_BPM_HIGH = 130.0         # BPM mapped to the most intense look
HEART_RATE_WEIGHT = 0.6        # Colour mix: rate vs. beat strength
HEART_REACH_CALM = 0.45        # Fraction of the arm a typical beat reaches at HEART_BPM_LOW
HEART_REACH_FAST = 0.8         # ...and at HEART_BPM_HIGH (stronger-than-usual beats reach further)
HEART_GLOW_S = 0.3             # Afterglow fade time as the wave falls back (s)
HEART_COLOR_EASE_S = 0.4       # Colour transition time
HEART_BASE_AT_INDEX0 = True    # Arm base is pixel 0 (wired end); False to flip
HEART_CALM_COLOR = (0, 255, 40)    # Monitor green
HEART_MID_COLOR = (255, 170, 0)    # Amber
HEART_HOT_COLOR = (255, 0, 0)      # Red
HEART_FLATLINE_COLOR = (0, 40, 8)  # No pulse
