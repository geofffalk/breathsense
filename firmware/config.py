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

# ===== Battery =====
# LiPo voltage via two 100k resistors from BAT to G, midpoint to this pin.
# Set to None if the divider isn't fitted (a floating pin reads noise).
BATTERY_PIN = "A2"
BATTERY_DIVIDER = 2.0          # Battery volts per volt at the pin
BATTERY_SAMPLE_S = 2.0         # Seconds between readings
BATTERY_MIN_V = 2.8            # Below this, no battery is connected (or the switch is off)
BATTERY_TX_S = 10.0            # Seconds between battery lines to the app
BATTERY_LOW_PCT = 10           # Log a warning on the console at or below this

# Thermistor circuit values
ADC_MAX = 65535.0
VSUP = 3.3
R_REF = 10000.0  # Reference resistor
R0 = 10000.0     # Thermistor resistance at T0
BETA = 3435.0    # Beta coefficient
T0_C = 25.0      # Reference temperature

# ===== Pulse Sensor (Heart mode) =====
# "auto": MAX3010x on I2C if one answers, else the analog sensor on PULSE_PIN
# "max3010x": MAX30102/30101/30105 on SDA/SCL only; "analog": PulseSensor only
PULSE_SENSOR = "auto"
MAX3010X_IR_CURRENT = 0x2F     # IR LED drive in 0.2 mA steps (0x2F = 9.4 mA); raise if the pulse is weak, lower if CLIPPING
MAX3010X_RED_CURRENT = 0x01    # Red LED isn't used for heart rate; nearly off saves power and glow
MAX3010X_SKIN_LEVEL = 50000    # IR reading above this means skin is on the sensor (set from earlobe readings)
MAX3010X_MIN_AMP = 40          # MAX3010x: min wave p-p (sensor counts) to look for beats
PULSE_PIN = "A1"               # Analog sensor signal wire
PULSE_INVERT = False           # True if beats dip instead of rise (applied on top of the sensor's own setting)
PULSE_MIN_AMP = 300            # Analog: min wave p-p (16-bit ADC units) to look for beats: above not-worn noise, below your pulse
PULSE_FILTER_HZ = 3.0          # Low-pass cutoff; the pulse itself is 0.7-2.5 Hz
PULSE_MIN_IBI_MS = 400        # Fastest accepted beat interval (150 BPM); faster detections are noise
PULSE_MAX_IBI_MS = 2000        # Slowest accepted beat interval (30 BPM)
PULSE_SIGNAL_TIMEOUT_MS = 2500 # No beat for this long -> pulse lost
PULSE_REGULARITY = 0.2         # Beat intervals must be within 20% of the recent median
PULSE_MIN_RHYTHM = 3           # Beat intervals in rhythm before beats are shown (filters noise)
PULSE_AMP_CONSISTENCY = 0.55   # Beat heights must be within 55% of the recent median
PULSE_LOCK_WINDOW = 0.25       # Once locked, a beat must land within 25% of when it's due
PULSE_DEBUG_PLOT = False       # True: print (signal, threshold, beat) for the Mu/Thonny plotter
PULSE_DEBUG_RAW = False        # True: print every raw sample as R,{ms},{raw},... for offline analysis
PULSE_DEBUG_STATS = True       # Print a once-a-second signal summary to the serial console
HEART_LIVE_HZ = 25.0           # Heart waveform send rate to app

# Standalone LED mode when no app is connected: "open" or "heart"
STANDALONE_MODE = "heart"

# ===== Heart LED Display =====
HEART_MIN_FILL = 5.0           # LEDs filled at rest (full stress fills all 10)
# The LEDs beat on their own steady rhythm, started by a confirmed pulse and
# steered gently by detected beats, so odd beats can't make the display jump.
HEART_PHASE_WINDOW = 0.25      # A detected beat within 25% of an interval of a shown beat nudges its timing; others are ignored
HEART_PHASE_GAIN = 0.2         # Fraction of that timing error corrected per beat
HEART_RATE_EASE = 0.15         # Fraction of the gap to the detected rate closed per beat
HEART_RATE_GAIN = 0.05         # Fraction of a beat's timing error added to the shown interval (stops lag)
HEART_MAX_RATE_STEP = 0.03     # Most the shown beat interval can change per beat (~2 BPM at 65 BPM)
HEART_COAST_S = 8.0            # Keep beating this long without supporting beats (sensor still on)

# ===== Stress (LED colour and reach) =====
# Stress = heart rate above your resting baseline, plus HRV below its average.
# Baselines are learned from the start of each power-on, so start calm.
# How far above baseline counts as full stress is learned per person too: a
# multiple of how much their rate normally rises above it, within limits.
HEART_STRESS_SD = 4.0          # Rise of this many times the wearer's typical rise = full stress (all LEDs, red)
HEART_STRESS_BPM_START = 20.0  # Full-stress rise (BPM) until the wearer's own range is learned
HEART_STRESS_BPM_MIN = 10.0    # Learned range limits (BPM), so a very steady or very
HEART_STRESS_BPM_MAX = 30.0    # jumpy pulse still gives a sensible scale
HEART_SCALE_DOWN = 0.002       # Range narrows to a steadier pulse over ~500 beats (~8 min)...
HEART_SCALE_UP = 0.0002        # ...and widens slowly (~5000 beats), so stress isn't learned as normal
HEART_STRESS_SMOOTH = 0.1      # Rate smoothing per beat (evens out the rise and fall with each breath)
HEART_BASELINE_DOWN = 0.03     # Baseline follows a lower rate quickly (~30 beats)...
HEART_BASELINE_UP = 0.001      # ...and a higher one slowly (~1000 beats, ~15 min), so stress stays visible
HRV_BEATS = 30                 # Beat-to-beat differences in the HRV (RMSSD) window (~30 s)
HRV_MIN_BEATS = 15             # Differences needed before HRV is reported
HRV_MAX_DEV = 0.2              # Intervals more than 20% off the rhythm are artifacts, not HRV
HEART_HRV_WEIGHT = 0.3         # Share of stress from HRV (the rest is heart rate)
HEART_HRV_BASELINE = 0.002     # HRV average follows over ~500 beats (~8 min)
HEART_STRESS_HRV_DROP = 0.5    # HRV this far below its average (50%) counts as full stress
HEART_COUNTER_BEAT = 0.55      # Counter-beat fill as a fraction of the main beat
HEART_BASE_AT_INDEX0 = True    # Arm base is pixel 0 (wired end); False to flip
HEART_CALM_COLOR = (0, 255, 40)    # Monitor green
HEART_MID_COLOR = (255, 170, 0)    # Amber
HEART_HOT_COLOR = (255, 0, 0)      # Red
