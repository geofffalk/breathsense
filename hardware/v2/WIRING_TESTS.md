# v2 wiring: multimeter tests on the finished build

For the headset fully wired:
- everything soldered;
- the LED strips, the LiPo and the MAX30101 on their temporary connectors;
- the nose clip on its pogo plug.

Every solder joint on `wiring.svg` (1–38) is checked by at least one test, and the
table at the end says which. Strips S1–S6 and holes h1–h8 are on
`switch_board.svg`, with holes counted from the transistor end. There's a
checklist version of this to tick through, linked from the README.

## Set-up and rules

- **Resistance, beep and diode tests (stages 1–9):**
  - LiPo **unplugged** and USB **out**.
  - Everything else plugged in: both strips, the MAX30101, the nose plug.
  - Across a live battery these settings give nonsense, and they can blow the meter's fuse.
- **Plug and unplug connectors only with the LiPo out.** Hot-plugging a strip can
  kill its first LED.
- **Probe the far contact:** the pad, pin or leg itself, not the wire beside it. Each
  test then covers the wire, its joints and any connector in between.
- **Where the probes go:** "A to B" means one probe on each. For diode tests, red
  and black are given; black is in COM.
- **Words used below:**
  - *Beep*: under about 1 Ω on the continuity setting.
  - *Open*: OL.
  - *Not near 0*: anything over about 1 kΩ, including OL.
- **Ohms range:** use 20 kΩ unless a test says otherwise. On the 2 kΩ range the meter's
  higher current can switch on the XIAO's protection diodes and read a few hundred Ω
  where there's no fault.
- **Low readings:** next to a transistor or a XIAO pin, a reading can come out low in
  one direction because a junction is in parallel. Swap the probes and use the
  higher reading.
- **Write every reading down,** including the ones that pass. If something fails
  later, the numbers show what changed.

## 1. Shorts on the power nets

Do these first. **Any reading near 0 Ω: stop**, and find the bridge before going on.

| # | Probes | Expect |
|---|---|---|
| 1.1 | XIAO BAT+ pad to GND | Not near 0 (the charger) |
| 1.2 | XIAO 3V3 to GND | Not near 0. kΩ that climbs is its capacitors charging: normal |
| 1.3 | XIAO 5V to GND | Not near 0. Nothing should be wired to 5V |
| 1.4 | S1 h2 to S6 h2 (battery + to ground, on the board) | Not near 0, the same as 1.1 |
| 1.5 | S3 h3 to S3 h7 (LED + to ground, across S3's cut) | Not near 0. With the strips in, it reads their supply input: kΩ or more |
| 1.6 | S1 h2 to S3 h3 (battery + to LED +), both ways | Over 10 kΩ. Near 0: the PNP is shorted, or E and C are bridged |
| 1.7 | XIAO BAT+ to 3V3 | Not near 0 |

## 2. Neighbouring XIAO pads

Solder bridges between pads are the most likely fault on the XIAO. With USB-C at
the top, it has two rows of pads:
- **Left row:** D0, D1, D2, D3, D4, D5, D6.
- **Right row:** 5V, GND, 3V3, D10, D9, D8, D7.

| # | Probes | Expect |
|---|---|---|
| 2.1 | D0 to D1 | About 10 kΩ (R5, the divider's 10k, meant to bridge them) |
| 2.2 | D1–D2, D2–D3, D3–D4, D5–D6 | Not near 0 |
| 2.3 | D4 to D5 (SDA to SCL) | Not near 0: the MAX30101's pull-ups put some kΩ here |
| 2.4 | 5V–GND, GND–3V3, 3V3–D10, D8–D7 | Not near 0 |
| 2.5 | D7 to GND, D2 to GND, D6 to GND (button released) | Not near 0 |
| 2.6 | BAT+ pad to BAT− pad, on the back | Not near 0, the same as 1.1 |

## 3. Switch board in place (joints 6–11)

| # | Probes | What it checks | Expect |
|---|---|---|---|
| 3.1 | S1 h2 to S2 h2 | R1 (PNP emitter to base) | About 10 kΩ |
| 3.2 | S2 h2 to S4 h2 | R2, via link L2 | About 2.2 kΩ |
| 3.3 | S5 h8 to S5 h2 | R3 | About 10 kΩ |
| 3.4 | S5 h2 to S6 h2 | R4 (NPN base to ground) | About 100 kΩ, lower one way |
| 3.5 | S1 h8 to S2 h8 | Link L1 | Beep |
| 3.6 | S6 h3 to S3 h5 | Link L4: ground onto S3 | Beep |
| 3.7 | Diode: red S5 h2, black S6 h2 | NPN base to emitter | 0.5–0.9 V (meters differ; compare 3.8–3.10). Probes swapped: OL or high |
| 3.8 | Diode: black S2 h2, red S1 h2 | PNP base to emitter | 0.5–0.9 V. It may read lower: R1 is across it |
| 3.9 | Diode: black S2 h2, red S3 h3 | PNP base to collector | 0.5–0.9 V. The strips' input is in parallel, so it may read lower |
| 3.10 | Diode: red S5 h2, black S4 h2 | NPN base to collector | 0.5–0.9 V |

## 4. XIAO and the pod wiring (joints 12–15, 22–25, 33–34)

| # | Probes | Wire or joint | Expect |
|---|---|---|---|
| 4.1 | XIAO BAT+ pad to S1 h2 | W2, joints 6 and 12 | Beep |
| 4.2 | XIAO BAT− pad to S6 h2 | W7 via S3 and L4, joints 11 and 14 | Beep |
| 4.3 | XIAO BAT− pad to the GND pad | The same net on the XIAO | Beep |
| 4.4 | XIAO D3 to S5 h8 | W8, joint 13 | Beep |
| 4.5 | XIAO D6 to GND, button released | Joints 15, 24, 25 | Open, or not near 0 |
| 4.6 | Same, button pressed through the lid | | Beep. Open: the wires are on two joined pins. Use diagonal pins |
| 4.7 | Button: the leg wired to the ground star, to XIAO GND | W5 | Beep |
| 4.8 | XIAO D1 to D0 | R5, joints 22 and 23 | About 10 kΩ (the same as 2.1) |
| 4.9 | Pogo socket pin 1 to XIAO D0 | Joints 23 and 33 | Beep |
| 4.10 | Pogo socket pin 2 to XIAO GND | W6, joint 34 | Beep |
| 4.11 | Pogo socket pin 1 to S1 h2, and to S3 h3 | Its wire passes the XIAO's edge | Not near 0 |

## 5. Right LED strip, plugged in (joints 8, 17, 18, 26–28)

| # | Probes | Expect |
|---|---|---|
| 5.1 | Strip's + pad to S3 h3 | Beep (W4, through the connector) |
| 5.2 | Strip's DIN pad to XIAO D7 | Beep |
| 5.3 | Strip's GND pad to XIAO GND | Beep |
| 5.4 | Strip's + pad to its GND pad | Not near 0 |
| 5.5 | Strip's DIN pad to its + pad, and to its GND pad | Not near 0 |
| 5.6 | Repeat 5.1–5.3 while wiggling the connector, then while flexing the wires where they enter the pod | Steady beeps. A beep that drops out is a loose contact or a broken strand |

## 6. MAX30101, plugged in (joints 18–21, 29–32)

| # | Probes (at its pins) | Expect |
|---|---|---|
| 6.1 | 3-5V to XIAO 3V3 | Beep |
| 6.2 | GND to XIAO GND | Beep |
| 6.3 | SDA to XIAO D4 | Beep |
| 6.4 | SCL to XIAO D5 | Beep |
| 6.5 | SDA to SCL, SDA to GND, SCL to GND, 3-5V to GND | Not near 0 |
| 6.6 | On the 20 kΩ range: SDA to 3-5V, and SCL to 3-5V, both ways round | A few kΩ in at least one direction, the same for SDA and SCL (the breakout's pull-ups). The two directions can differ: XIAO diodes. A few hundred Ω both ways: a short to 3V3 |
| 6.7 | INT to anything | Not wired: should be open to every other pin |
| 6.8 | Repeat 6.1–6.4 while flexing the earlobe lead at the pod's wall and at the clip | Steady. The lead bends every time the clip goes on |

## 7. Cord and left pod (joints 1–5, 16)

Probe at the left pod's end: the strip's pads, and the pod's half of the LiPo
connector.

| # | Probes | Expect |
|---|---|---|
| 7.1 | LiPo connector, pod side: the + contact to XIAO BAT+ | Beep (cord BAT+, W1, S1, W2). **Mark this contact +** |
| 7.2 | LiPo connector, pod side: the − contact to XIAO GND | Beep (cord GND, W9) |
| 7.3 | Left strip's + pad to S3 h3 | Beep (cord LED+, W3) |
| 7.4 | Left strip's DIN pad to XIAO D2 | Beep (cord DIN) |
| 7.5 | Left strip's GND pad to XIAO GND | Beep (joints 2 and 5) |
| 7.6 | Left strip's GND pad to the LiPo connector's − contact | Beep |
| 7.7 | Left strip's + pad to its GND, and its DIN to + and to GND | Not near 0 |
| 7.8 | LiPo connector, pod side: + to − | Not near 0, the same as 1.1 |
| 7.9 | Repeat 7.1–7.4 while flexing the cord at both pod walls and along its length | Steady |

## 8. Nose wire (joints 35–38)

| # | Probes | Expect |
|---|---|---|
| 8.1 | Plug pulled out of the socket, 20 kΩ range: across the plug's two pins | 8–12.5 kΩ at room temperature (10 kΩ at 25 °C) |
| 8.2 | Same, holding the clip between finger and thumb | Falls steadily: about 8 kΩ at skin temperature |
| 8.3 | Same, breathing in and out through that nostril | Moves by a few hundred Ω each breath. Doesn't move: the bead is too far up or not at the entrance |
| 8.4 | Same, flexing the wire at the plug, along the cheek run and at the clip | Steady. Jumps are a broken strand |
| 8.5 | Plug in, 20 kΩ range: XIAO D0 to GND | Close to 8.1, a little lower with the XIAO in parallel. Either way round: the bead has no polarity |
| 8.6 | Plug in, swapped round | The same as 8.5 |

## 9. LiPo connector polarity

Do this before the battery is ever plugged in. Two-pin JST plugs are wired opposite
ways round by different sellers, and a reversed LiPo destroys the XIAO's charger.

| # | Probes | Expect |
|---|---|---|
| 9.1 | Volts on the battery's own half: red on the contact you expect to be + | +3.0 to 4.2 V. Negative: that contact is − |
| 9.2 | Hold the halves side by side. Does the battery's + meet the contact marked + in 7.1? | Yes. If not, swap the pins in one housing. Don't plug it in until it does |

## 10. Power on, no firmware running

Voltages only from here, with the black probe on XIAO GND. The steps:
1. Unplug both strips and the MAX30101.
2. Plug in the LiPo.
3. Take readings 10.1–10.4.
4. LiPo out, everything else back in, LiPo back in.
5. Take 10.5.

| # | Measure | Expect |
|---|---|---|
| 10.1 | XIAO BAT+ pad | The same as 9.1, within 0.05 V. **Negative: unplug at once** |
| 10.2 | XIAO 3V3 | 3.25–3.35 V |
| 10.3 | S3 h3 (LED +) | Near 0 V. Tens of mV of leakage is fine |
| 10.4 | MAX30101 connector, pod side: 3V3 contact | 3.25–3.35 V |
| 10.5 | Everything plugged in: S3 h3, BAT+ and 3V3 again | Unchanged. If 3V3 falls, something on a connector is shorting it |
| 10.6 | Plug in USB, then watch BAT+ for a few minutes | Rises toward 4.2 V (charging) |

**If LED + reads the battery voltage with no firmware running**, the LED switch is
stuck on. Check:
- 1.6 (PNP shorted);
- 3.1 (R1 missing);
- 3.7 (NPN shorted, or its pins swapped).

## 11. With the firmware running

| # | Do | Measure | Expect |
|---|---|---|---|
| 11.1 | Awake, LEDs lit | XIAO D3 | About 3.3 V |
| 11.2 | Same | S3 h3, and each strip's + pad | Battery minus 0.05–0.2 V |
| 11.3 | LEDs off, or asleep after a long press | D3, then S3 h3 | 0 V, then near 0 V |
| 11.4 | Asleep | D7 and D2 | 0 V. If high, the strips power up through their data pins |
| 11.5 | Short press | — | Wakes |
| 11.6 | Right strip lights but left doesn't | Left strip's + pad, and D2 continuity (7.3, 7.4) | Battery minus 0.1 V at +. If + is fine, it's the DIN wire |
| 11.7 | Breathe through the nose | D0, on the DC volts range | Stays near 0 V for most of the time, because D1 only feeds the divider while it reads. Check the breath signal in the app, not with the meter |
| 11.8 | App shows a pulse | — | The MAX30101 answers on I2C. No sensor found: recheck 6.1–6.6 |

## 12. Current (optional)

Put the meter in series with the battery: in the LiPo's + lead, through the mA socket,
with USB out.

| # | State | Expect |
|---|---|---|
| 12.1 | Awake, LEDs off | About 5–10 mA |
| 12.2 | Awake, LEDs lit | 30–50 mA |
| 12.3 | Asleep: switch to µA only once it has gone to sleep | A few to a few tens of µA |

**If sleep current is about 1 mA per LED or more**, either:
- the LED switch is still on (check 11.3); or
- D2 or D7 is high (check 11.4).

The µA range's burden voltage can reset the XIAO when it wakes. That's the meter,
not the wiring: switch back to mA before you press the button.

## Joint coverage

| Joints (`wiring.svg`) | Checked by |
|---|---|
| 1 LiPo + to cord BAT+ | 7.1, 9.2, 10.1 |
| 2 LiPo −, left strip GND, cord GND | 7.2, 7.5, 7.6 |
| 3, 4, 5 Left strip +, DIN, GND | 7.3, 7.4, 7.5, 7.7 |
| 6–11 Switch board | 1.4–1.6, 3.1–3.10, 4.1, 4.2, 10.3, 11.2, 11.3 |
| 12, 14 BAT+, BAT− | 4.1–4.3, 10.1 |
| 13 D3 | 4.4, 11.1 |
| 15, 24, 25 D6 and button | 4.5–4.7, 11.5 |
| 16 D2 | 7.4, 11.4, 11.6 |
| 17 D7 | 5.2, 11.4 |
| 18 GND (right strip, MAX30101) | 5.3, 6.2 |
| 19–21 3V3, SDA, SCL | 6.1, 6.3, 6.4, 6.6, 10.4 |
| 22, 23 D1, D0 and R5 | 2.1, 4.8, 4.9 |
| 26–28 Right strip pads | 5.1–5.5 |
| 29–32 MAX30101 pins | 6.1–6.7 |
| 33, 34 Pogo socket | 4.9–4.11, 8.5 |
| 35–38 Pogo plug, thermistor | 8.1–8.6 |
