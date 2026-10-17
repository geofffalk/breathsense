# Pulse Sensor (Heart Mode)

Heart mode reads an analog PulseSensor (the common 3-wire optical
heart-rate sensor) and shows each heartbeat on the LED arms as a
heart-monitor trace. The app's **Heart** button switches the headset into
this mode. The main-page graph then shows the live pulse waveform, and
breath output pauses.

## Wiring (ItsyBitsy nRF52840 Express)

| PulseSensor wire          | ItsyBitsy pin | Notes                                    |
|---------------------------|---------------|------------------------------------------|
| **+** / VCC (red)         | **3V**        | 3.3 V supply. Shared with the thermistor. |
| **−** / GND (black)       | **G**         | Any ground pin.                          |
| **S** / signal (purple)   | **A1**        | Analog input. A0 is the thermistor.      |

```
 PulseSensor             ItsyBitsy nRF52840
 ┌──────────┐
 │   red  + ├──────────── 3V
 │ black  − ├──────────── G
 │ purple S ├──────────── A1
 └──────────┘
```

Pins already in use: **A0** (thermistor), **D7** (right LED strip) and
**D9** (left LED strip). Don't use those for the sensor.

### Important

- **Power the sensor from 3V. Do not use USB or VHi (5 V).** The
  nRF52840's analog pins are not 5 V tolerant. A 5 V supply can push the
  signal above 3.3 V and damage the chip.
- The 3V pin is already used by the thermistor divider. You can solder
  both red wires into the same hole, or splice them together with one lead
  to the pin. Do the same for ground if needed.
- Keep the signal wire short, and keep it away from the LED data lines
  (D7/D9), so LED updates don't add noise.
- Many sensors have a small electronics side with exposed components.
  Cover it with the clear vinyl dot that comes with the sensor, or a dab of
  hot glue, so skin and sweat can't short it.

## Placement

- Rest the **heart-logo side** against a fingertip or earlobe.
- Press lightly. Pressing too hard squeezes the blood out and flattens the
  signal. Pressing too lightly lets room light leak in. A velcro strap or
  ear clip works well.
- Keep still for a few seconds. Beats appear after 2 to 3 heartbeats.

## What the LEDs show

The LEDs follow the sensor's **live analog waveform**, updated about 100
times a second. They don't just blink once per detected beat.

- Light extends from the base of each arm in proportion to the current
  pulse height. Each heartbeat makes a sharp surge outward, a fall back,
  and a smaller second push (the dicrotic wave). A fading afterglow trails
  behind as the wave recedes, like the persistence of a heart-monitor
  trace.
- **Stronger beats reach further.** Height is measured against your recent
  beats. A typical beat reaches about half the arm at a calm rate. A beat
  that is clearly stronger reaches beyond that.
- **A faster heart rate reaches further and looks redder.** At 55 BPM a
  typical beat reaches about 45% of the arm. At 130 BPM it reaches about
  80%.
- **Colour** eases from monitor green, through amber, to red as heart rate
  and beat strength rise.
- No pulse for 2.5 s: a dim green **flatline** along the whole arm. Any
  live signal still shows on top of it, so you can see the response as soon
  as you place a finger.

Height is measured against your own recent beats, because the raw
amplitude depends mostly on how the sensor sits on the skin. The app graph
uses the same scaling: a typical beat spans the graph from bottom to top,
and stronger beats plot taller.

## Using it

- **With the app:** tap **Heart**. Tap **Open** or **Guided** to go back to
  breathing.
- **Without the app:** set `STANDALONE_MODE = "heart"` in `config.py`.
- BLE command: `M,H` enters Heart mode. The headset then streams
  `H,{ts},{wave},{bpm},{signal},{beats},{strength}` at 25 Hz instead of
  `B,…` breath lines.

## Tuning (`config.py`)

| Setting                 | Change it when…                                              |
|-------------------------|--------------------------------------------------------------|
| `PULSE_MIN_AMP`         | Raise it if beats are detected with no finger on the sensor. Lower it if real beats are missed. |
| `PULSE_INVERT`          | Your sensor's beats dip instead of rise (some clones do).    |
| `HEART_BASE_AT_INDEX0`  | Traces run from tip to base instead of base to tip.          |
| `HEART_BPM_LOW/HIGH`    | Change which heart rates count as calm and as intense.        |
| `HEART_REACH_CALM/FAST` | Change how far along the arm a typical beat reaches at low and high heart rates. |
| `HEART_GLOW_S`          | Make the afterglow trail longer or shorter.                  |

With USB connected, the serial console logs each beat:
`Beat: 72 BPM, strength 0.48`.
