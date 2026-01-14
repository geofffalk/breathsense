# BreathSense Nasal Clip - Configuration
# Simplified config for XIAO nRF52840 without LEDs

# ===== Breath Detection Parameters =====
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
# Exhale duration maps to depth category
DEFAULT_VERY_SHORT_MAX = 2.0   # <= this: Very short
DEFAULT_SHORT_MAX = 3.5        # <= this: Short
DEFAULT_MEDIUM_MAX = 5.0       # <= this: Medium
DEFAULT_LONG_MAX = 6.5         # <= this: Long
# > LONG_MAX: Very long

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

# ===== Hardware (XIAO nRF52840) =====
THERMISTOR_PIN = "A0"

# Thermistor circuit values
ADC_MAX = 65535.0
VSUP = 3.3
R_REF = 10000.0  # Reference resistor (10k)
R0 = 10000.0     # Thermistor resistance at T0 (10k NTC)
BETA = 3435.0    # Beta coefficient
T0_C = 25.0      # Reference temperature
