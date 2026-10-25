# Pulse Sensor (Heart Mode)

Heart mode reads an optical pulse sensor and shows each heartbeat on the
LED arms. The app's **Heart** button switches the headset into this mode.
The main-page graph then shows the live pulse waveform, and breath output
pauses.

Two sensor types work. With the default `PULSE_SENSOR = "auto"`, the
firmware uses a MAX3010x if one answers on I2C, and falls back to the
analog sensor otherwise. The serial console shows which one it picked at
startup, e.g. `Pulse sensor: MAX3010x on I2C`.

| | MAX3010x (recommended) | Analog PulseSensor |
|---|---|---|
| Chips | MAX30102, MAX30101, MAX30105 | Generic 3-wire "PulseSensor" boards |
| Connection | I2C (SDA/SCL) | A1 |
| Signal | 18-bit, ambient light cancelled | Weak at 3.3 V, picks up room light |
| Wear detection | Yes: LEDs stay dark when not worn | No |

## Option 1: MAX3010x on I2C (recommended)

### Buying

- Look for a **MAX30102 heart rate / pulse oximeter module**. A MAX30101
  or MAX30105 board also works. (Maxim markets the MAX30105 as a particle
  or smoke sensor, but it's the same family.)
- **Check the I2C logic level.** Some cheap purple MAX30102 boards pull SDA
  and SCL up to only 1.8 V. The nRF52840 needs about 2.3 V to read a high,
  so those boards can fail to respond. Choose one sold as working with
  3.3 V logic, or with a jumper that sets the pull-ups to 3.3 V.

### Wiring

| Sensor pin (Pimoroni label) | ItsyBitsy pin | Notes                                  |
|-----------------------------|---------------|----------------------------------------|
| **VIN** (**2-6V**)          | **3V**        | Shared with the thermistor (see below). |
| **GND**                     | **G**         |                                        |
| **SDA**                     | **SDA**       | I2C data                               |
| **SCL**                     | **SCL**       | I2C clock                              |
| INT                         | not connected | Not needed                             |

The Pimoroni MAX30101/MAX30105 breakout has these five pins in a row
along one edge. It works with 3.3 V logic, so it connects directly.

```
 MAX3010x                ItsyBitsy nRF52840
 ┌──────────┐
 │  VIN     ├──────────── 3V   (shared with thermistor)
 │  GND     ├──────────── G
 │  SDA     ├──────────── SDA
 │  SCL     ├──────────── SCL
 │  INT     │  (leave unconnected)
 └──────────┘
```

Once the MAX3010x is in, A1 isn't used, so you can remove the analog
sensor.

### Settings (`config.py`)

| Setting                  | Default | Change it when…                                        |
|--------------------------|---------|--------------------------------------------------------|
| `MAX3010X_IR_CURRENT`    | `0x2F` (9.4 mA) | Raise it (e.g. `0x3F`) if the pulse is weak, as is likely on an earlobe; lower it if the summary shows `CLIPPING`. |
| `MAX3010X_RED_CURRENT`   | `0x01` (0.2 mA) | Leave it. Only IR is used for heart rate, so red is kept nearly off. |
| `MAX3010X_SKIN_LEVEL`    | `50000` | The IR reading above which skin counts as present. Check the `raw` value in the summary with the sensor on and off, and set it between them. Set this from earlobe readings: they differ from a fingertip's. |
| `MAX3010X_MIN_AMP`       | `40`    | Lower it if the sensor is on and still but shows no beats, raise it if noise gets through. |

## Option 2: Analog PulseSensor on A1

| PulseSensor wire          | ItsyBitsy pin | Notes                                    |
|---------------------------|---------------|------------------------------------------|
| **+** / VCC (red)         | **3V**        | 3.3 V supply. Shared with the thermistor. |
| **−** / GND (black)       | **G**         | Any ground pin.                          |
| **S** / signal (purple)   | **A1**        | Analog input. A0 is the thermistor.      |

- **Power the sensor from 3V. Do not use USB or VHi (5 V).** The
  nRF52840's analog pins are not 5 V tolerant.
- Cheap analog boards give a weak signal at 3.3 V. Expect missed beats.
- Cover the exposed electronics side with the vinyl dot or hot glue, so
  skin and sweat can't short it.

## Shared pins

Pins already in use: **A0** (thermistor), **D7** (right LED strip) and
**D9** (left LED strip).

The 3V pin also powers the thermistor divider. Solder both power wires
into the same hole, or join the sensor's power wire to the 3V end of the
thermistor's 10k resistor. Do the same for ground if needed. The sensor
draws only a few mA, which is well within what the 3V pin can supply.

## Placement

The sensor is meant to be clipped to the earlobe. A fingertip also works
and is handy for bench testing.

- **Earlobe:** clip the sensor window against the fleshy lower part of the
  lobe. The clip should hold it in steady contact without pinching.
  Pressing squeezes the blood out and flattens the signal.
- **Fingertip (testing):** rest the window lightly against the pad of a
  finger. Pimoroni suggest looping a rubber band or a piece of wire through
  the breakout's mounting holes and around the fingertip, which keeps the
  pressure even.
- The earlobe gives a weaker pulse than a fingertip, especially when cold.
  If beats aren't found, raise `MAX3010X_IR_CURRENT` and check
  `MAX3010X_SKIN_LEVEL` (see Settings above).
- The sensor is very sensitive to movement. Head turns, talking and chewing
  move the earlobe; the steady LED rhythm rides through short movements.
- Shade the sensor from bright light; the clip housing should cover it.
- On a cable to an ear clip, twist SDA and SCL together with GND (or run a
  ribbon with GND between them). If readings drop out, lower the I2C speed
  in `pulse_detector.py` from 400 kHz to 100 kHz.
- The LEDs start after about 4 steady beats.

## What the LEDs show

- On each detected heartbeat, both arms **fill** smoothly from the base to
  a set position, then **empty**. A smaller **counter-beat** fill follows
  (lub-dub). Then the arms stay dark until the next beat.
- **Stress fills further and looks redder.** At rest the beat fills half
  the arm (5 LEDs) in monitor green. Full stress fills all 10 in red. See
  [Stress](#stress) below.
- **No beat detected: the LEDs stay off.** Beats appear only after about 4
  beats in a steady rhythm, so random noise doesn't flash the LEDs. Expect
  about 3 to 4 seconds after putting the sensor on.
- **Once started, the beat stays steady.** The LEDs keep their own rhythm.
  Detected beats nudge its timing slightly, and beats that don't fit are
  ignored. A real change in heart rate is followed gradually, about 2 BPM
  per beat at most. The beat stops when the sensor is removed, or after
  `HEART_COAST_S` (8 s) with no beats that fit.

## Using it

- **With the app:** tap **Heart**. Tap **Open** or **Guided** to go back to
  breathing.
- **Without the app:** set `STANDALONE_MODE = "heart"` in `config.py`.
- BLE command: `M,H` enters Heart mode. The headset then streams
  `H,{ts},{wave},{bpm},{signal},{beats},{stress},{hrv}` at 25 Hz instead
  of `B,…` breath lines. `wave` is the live sensor trace. `bpm` and `beats`
  follow the same steady rhythm as the LEDs, and `signal` is 1 while that
  rhythm is running, so the app's heart beats in time with the headset.
  `stress` is 0–100 and `hrv` is in ms (0 until measured).

## Stress

The LEDs and the app's heart show stress, worked out from two signals. Both
are compared with baselines learned continuously while you wear it, so
there is no calibration step.

- **Heart rate above your resting rate (70%).** The resting baseline follows
  a lower rate quickly (about 30 beats) and a higher rate slowly (about 15
  minutes). So it settles on your calm rate, and a stressful stretch stays
  visible rather than being absorbed. How big a rise counts as full stress
  is learned too: 4× the wearer's typical rise above baseline
  (`HEART_STRESS_SD`), kept between 10 and 30 BPM. It starts at 20 BPM
  and narrows to a steady pulse over about 8 minutes. It widens much more
  slowly, so a stressful stretch isn't learned as normal.
- **HRV below its average (30%).** HRV is RMSSD, the typical change in the
  gap between consecutive beats, over the last ~30 beats. A relaxed body
  varies the gap, and under stress it becomes more even. Half the long-run
  average (`HEART_STRESS_HRV_DROP`) is full stress. HRV appears after about
  15 clean beats.

Baselines start fresh at power-on, so put the headset on while calm. The
summary line shows them, e.g.
`SHOWING 71 BPM (base 65, full +18) HRV 20 ms (avg 18) stress 0.21`.

Beat times for HRV are taken at the steepest point of each upstroke on the
sensor's own sample clock, and interpolated between samples. Only
consecutive confirmed beats count, and intervals more than 20% off the
rhythm are skipped as artifacts. HRV needs the MAX3010x; the analog sensor
reports 0.

## Troubleshooting: is it the sensor or the code?

Work through these in order:

1. **Check the waveform in the app.** Tap **Heart** and look at the main
   graph. A working sensor on skin shows a regular wave that repeats once
   per heartbeat. A flat line or random fuzz means the sensor isn't giving
   a usable signal. Check the wiring and placement.
2. **Check the serial console** (USB connected; Mu, Thonny, or
   `screen /dev/tty.usbmodem*`). Every detected beat logs a line:
   - `Beat: 72 BPM, strength 0.48`: detection works, and these beats light
     the LEDs.
   - `Beat: … (unconfirmed)`: beats are found but their timing or height
     isn't steady yet, or they're noise. These don't light the LEDs.
   - No `Beat:` lines at all: the signal is too weak, too noisy or
     upside-down for detection.
3. **Read the once-a-second summary** (`PULSE_DEBUG_STATS = True`):

   ```
   PULSE raw 25417-39534 p-p 14117 mean 32139 | 100 samples | wave p-p 6820 | beats 1 confirmed 1 | last amp 6240 | 72 BPM
   ```

   - `raw … p-p`: the sensor's reading range over that second. Analog:
     0–65535 = 0–3.3 V. MAX3010x: 0–262143, roughly 100,000–200,000 on skin.
   - `samples`: readings per second. Analog: the loop rate, about 60–100.
     MAX3010x: 100.
   - `NOT WORN` (MAX3010x): the IR reading is below
     `MAX3010X_SKIN_LEVEL`, so beat detection is paused.
   - `LOCKED`: a steady rhythm has been found, and beats are being shown.
   - `CLIPPING`: the signal is hitting 0 V or 3.3 V. Usually this means too
     much pressure, a wiring fault, or the sensor powered from the wrong
     supply.

   Compare about 10 seconds with the sensor off against 10 seconds with it
   on. Set the minimum amplitude between the two `wave p-p` values
   (`PULSE_MIN_AMP` for analog, `MAX3010X_MIN_AMP` for MAX3010x): above the
   off value, below the on value.

4. **Plot the raw signal.** Set `PULSE_DEBUG_PLOT = True` in `config.py`
   and open the plotter in Mu or Thonny. It shows three lines:
   - the pulse signal
   - the beat threshold (0 while the signal is too small)
   - a marker that jumps up during each detected beat

   Each heartbeat should cross the threshold once. Then:
   - If the peaks point **down**, set `PULSE_INVERT = True`.
   - If the threshold stays at 0 with the sensor on, the waveform is
     smaller than `PULSE_MIN_AMP`. Lower it, or adjust the clip pressure.
   - If beats are found with the sensor off, raise `PULSE_MIN_AMP`.

   Set it back to `False` afterwards. Printing slows the main loop.

5. **Record the raw signal.** Set `PULSE_DEBUG_RAW = True` to print every
   sensor sample as `R,{ms},{raw},…`. Save about 2 minutes of console output
   with the sensor on. The recording can be replayed offline
   through `pulse_detector.py` to tune detection against your real signal.

## Tuning (`config.py`)

| Setting                 | Change it when…                                              |
|-------------------------|--------------------------------------------------------------|
| `PULSE_SENSOR`          | Force `"max3010x"` or `"analog"` instead of auto-detecting. |
| `PULSE_MIN_AMP`         | Analog only. Raise it if beats are detected with the sensor off. Lower it if real beats are missed. |
| `PULSE_INVERT`          | The plotted beats point down instead of up. The MAX3010x is already corrected, so this is mainly for analog clones. |
| `PULSE_LOCK_WINDOW`     | Once 3 steady beats lock the rhythm, beats are only accepted when due (±25%). Widen it for a very irregular pulse. |
| `PULSE_FILTER_HZ`       | Lower it (e.g. 2.5) for a noisier signal, raise it if beats look smeared. |
| `PULSE_REGULARITY`, `PULSE_MIN_RHYTHM`, `PULSE_AMP_CONSISTENCY` | Make the rhythm check looser if real beats are rejected (very irregular pulse), or stricter if noise still flashes the LEDs. |
| `HEART_BASE_AT_INDEX0`  | The fill grows from the tip instead of the base.             |
| `HEART_STRESS_SD`       | Full stress at this many times the wearer's typical rise; lower is more sensitive. |
| `HEART_STRESS_BPM_MIN/MAX` | Limits on the learned full-stress rise (BPM).             |
| `HEART_HRV_WEIGHT`      | Share of stress from HRV (the rest is heart rate).           |
| `HEART_BASELINE_UP/DOWN`, `HEART_HRV_BASELINE` | How quickly the baselines follow you. |
| `HEART_MIN_FILL`        | Change how many LEDs a beat fills at rest.                   |
| `HEART_COUNTER_BEAT`    | Make the counter-beat fill bigger or smaller (0 turns it off). |
