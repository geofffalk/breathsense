"""
compare.py - Checks the C++ port against the originals on the same synthetic input:
  breath and pulse detection against the v1 CircuitPython firmware (firmware/), with its hardware
  modules stubbed; mood scores against the app's Dart (lib/services/mood_analyzer.dart).

Run from the repo root:  python3 firmware_v2/test/compare.py
Needs clang++ and dart (Flutter SDK). Writes its files to firmware_v2/test/out/.
TOL (env, default 0.02) is the relative tolerance for values; times are compared to half a sample.
Also compared: both LED displays frame by frame (v1's neopixel stubbed), the B and H lines against
code.py's format strings, and R. As of 1 Nov 2026 everything matches at TOL=0.0005 except one heart
frame out of 3448, one colour level apart (the pulse detector uses 32-bit floats, v1 Python doubles;
the breath detector uses doubles, as its thresholds are sensitive to the last digit).
Gotchas found getting here: float constants (0.22f, 0.35f) put threshold crossings a sample early;
clang's fused multiply-add changes the test clock (built with -ffp-contract=off); relative tolerance
on timestamps hid 10 ms shifts; v1's hide_all() leaves _show_pixels' cache stale (reset here).
"""

import io
import math
import os
import random
import subprocess
import sys
import types
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")
FW = os.path.join(ROOT, "firmware")
TOL = float(os.environ.get("TOL", "0.02"))
DART = os.environ.get("DART", os.path.expanduser("~/workspace/flutter/bin/dart"))

# ---------------------------------------------------------------- synthetic input

def gen_temps(seed=1):
    """Thermistor in a nostril: ~32 C, cooling on each inhale. Breaths of varying length, a pause."""
    rnd = random.Random(seed)
    temps = []
    t = 0.0
    plan = [3.5] * 8 + [5.0] * 6 + [8.0] * 5 + [2.4] * 10 + [None] + [6.0] * 6 + [4.0] * 8
    for cycle in plan:
        if cycle is None:                     # 12 s pause: flat
            for _ in range(1200):
                temps.append(32.0 + rnd.gauss(0, 0.004))
            continue
        cycle *= rnd.uniform(0.9, 1.1)
        n = int(cycle * 100)
        n_in = int(n * 0.4)
        for i in range(n):
            if i < n_in:                      # Inhale: cool air
                u = i / n_in
                v = -0.8 * math.sin(math.pi * u / 2)
            else:                             # Exhale: warm back
                u = (i - n_in) / (n - n_in)
                v = -0.8 * math.cos(math.pi * u / 2)
            temps.append(32.0 + v + rnd.gauss(0, 0.004))
    return temps


def gen_ir(seed=2):
    """MAX3010x IR: ~120000 counts, dipping ~300 on each beat. 65 -> 85 -> 62 BPM with jitter,
    a 6 s sensor-off gap. Returns ticks of (now_ms, skin, [samples]) every 30 ms (3 samples)."""
    rnd = random.Random(seed)
    samples, skin = [], []
    t_ms = 0.0
    next_beat = 500.0
    rate_plan = [(0, 65), (60000, 85), (120000, 62), (180000, 62)]
    total_ms = 180000
    while t_ms < total_ms:
        bpm = rate_plan[0][1]
        for (t0, b0), (t1, b1) in zip(rate_plan, rate_plan[1:]):
            if t0 <= t_ms < t1:
                bpm = b0 + (b1 - b0) * (t_ms - t0) / (t1 - t0)
        if t_ms >= next_beat:
            next_beat += 60000.0 / bpm * rnd.uniform(0.95, 1.05)
        phase = (t_ms - (next_beat - 60000.0 / bpm)) / (60000.0 / bpm)
        dip = 300 * math.exp(-((phase - 0.15) / 0.07) ** 2) + 90 * math.exp(-((phase - 0.45) / 0.08) ** 2)
        off = 90000 <= t_ms < 96000
        v = 2000 if off else 120000 - dip + rnd.gauss(0, 12) + 400 * math.sin(t_ms / 4000.0)
        samples.append(int(v))
        skin.append(not off)
        t_ms += 10
    ticks = []
    for k in range(0, len(samples), 3):
        chunk = samples[k:k + 3]
        now = (k + len(chunk) - 1) * 10
        ticks.append((now, skin[k + len(chunk) - 1], chunk))
    return ticks


def gen_breaths(seed=3):
    rnd = random.Random(seed)
    rows = []
    for i in range(40):
        ex = rnd.uniform(1.5, 6.5) if i < 20 else rnd.uniform(0.8, 2.5)
        inh = rnd.uniform(1.0, 3.0)
        rows.append((round(ex, 2), round(inh, 2), round(ex + inh, 2), rnd.randint(30, 100), round(rnd.uniform(0.05, 0.6), 3)))
    return rows

# ---------------------------------------------------------------- v1 Python, stubbed

class Clock:
    t = 0.0


def load_v1():
    """Import the v1 modules with board, analogio, busio and supervisor stubbed."""
    for name in ("board", "analogio", "busio", "supervisor", "neopixel"):
        sys.modules[name] = types.ModuleType(name)
    sys.modules["board"].A0 = sys.modules["board"].A1 = sys.modules["board"].SCL = sys.modules["board"].SDA = 0

    class AnalogIn:
        def __init__(self, *_):
            self.value = 0
    sys.modules["analogio"].AnalogIn = AnalogIn
    sys.modules["supervisor"].ticks_ms = lambda: int(round(Clock.t * 1000))   # Round: t*1000 can land just under
    sys.modules["board"].D7 = sys.modules["board"].D9 = 0

    class NeoPixel:                       # Records what the first (left) strip shows
        instances = []
        shown = []

        def __init__(self, *_, **__):
            self.buf = [(0, 0, 0)] * 20
            NeoPixel.instances.append(self)

        def __setitem__(self, i, c):
            self.buf[i] = tuple(int(x) for x in c)

        def fill(self, c):
            self.buf = [tuple(int(x) for x in c)] * 20

        def show(self):
            if self is NeoPixel.instances[0]:
                NeoPixel.shown.append((Clock.t, list(self.buf[:10])))
    sys.modules["neopixel"].NeoPixel = NeoPixel
    Clock.NeoPixel = NeoPixel
    sys.path.insert(0, FW)
    import config
    config.PULSE_DEBUG_STATS = False
    config.PULSE_DEBUG_PLOT = False
    config.PULSE_DEBUG_RAW = False
    import time as _time
    _time.monotonic = lambda: Clock.t
    import breath_detector
    import pulse_detector
    import led_control
    import settings_storage
    # v1 quirk: hide_all() doesn't reset _show_pixels' "last shown" cache, so a frame identical to
    # the one before a hide_all is skipped and the strip stays dark. The C++ shows it (as intended);
    # reset the cache here so the comparison is like for like.
    _hide = led_control.hide_all

    def hide_all():
        _hide()
        led_control._last_led_state = None
    led_control.hide_all = hide_all
    Clock.led = led_control
    Clock.settings = settings_storage
    return breath_detector, pulse_detector


def py_breath(bd_mod, temps):
    feed = iter(temps)
    bd_mod.read_temp_c = lambda: next(feed)
    Clock.t = 0.0
    out = []
    with redirect_stdout(io.StringIO()):
        d = bd_mod.BreathDetector()
        last_count = 0
        for i in range(len(temps)):
            Clock.t = i * 0.01 + 1e-9
            if d.tick():
                out.append("T,%.2f,%d,%d" % (Clock.t, d.phase, d.get_depth_color()))
            m = d.mood
            if m.breath_count != last_count:
                last_count = m.breath_count
                out.append("N,%d,%.2f,%.2f,%d,%.3f,%d" % (m.breath_count, m.last_exhale_duration,
                           m.last_inhale_duration, m.last_smoothness, m.last_peak_flow, m.last_symmetry))
                st = d.get_state()         # code.py send_breath_data()'s format
                out.append("B,{},{},{:.3f},{},{},{:.2f},{:.2f},{:.2f},{},{:.2f},{},{}".format(
                    0, st["phase"], st["norm"], st["depth_color"], -1, st["exhale_dur"], st["inhale_dur"],
                    st["cycle_dur"], st["smoothness"], st["peak_flow"], st["symmetry"], 1 if st["unworn"] else 0))
    return out


def py_pulse(pd_mod, ticks):
    class Src:
        name = "synthetic"
        inverted = True
        clips_low = False
        drift_filter = True
        sample_ms = 10
        full_scale = (1 << 18) - 1

        def __init__(self):
            self.min_amp = pd_mod.MAX3010X_MIN_AMP
            self.skin_present = True
            self.pending = []

        def read(self, out):
            out.extend(self.pending)
            self.pending = []

    src = Src()
    pd_mod._open_source = lambda: src
    Clock.t = 0.0
    p = pd_mod.PulseDetector()
    out = []
    seen = 0
    for now, skin, chunk in ticks:
        Clock.t = now / 1000.0
        src.skin_present = skin
        src.pending = list(chunk) if skin else []
        p.tick()
        if p.rhythm_count != seen:
            seen = p.rhythm_count
            out.append("R,%d,%d,%.1f,%.3f,%.1f" % (now, p.rhythm_count, p.rhythm_bpm, p.stress, p.hrv_ms))
            out.append("H,{},{:.3f},{},{},{},{},{}".format(   # code.py send_heart_data()'s format
                0, p.normalized(), int(p.rhythm_bpm + 0.5), 1 if p.rhythm_bpm > 0 else 0,
                p.rhythm_count & 0xFFFF, int(p.stress * 100), int(p.hrv_ms + 0.5)))
    return out

def frames(shown):
    """What the strip showed, as 'F,t,r,g,b,...' at each change."""
    out, last = [], [(0, 0, 0)] * 10
    for t, px in shown:
        if px != last:
            out.append("F,%.2f," % t + ",".join("%d,%d,%d" % c for c in px))
            last = px
    return out


def py_breathled(bd_mod, temps):
    feed = iter(temps)
    bd_mod.read_temp_c = lambda: next(feed)
    Clock.t = 0.0
    Clock.NeoPixel.shown = []
    with redirect_stdout(io.StringIO()):
        d = bd_mod.BreathDetector()
        led = Clock.led.OpenBreathingLED(d)
        for i in range(len(temps)):
            Clock.t = i * 0.01 + 1e-9
            d.tick()
            led.tick()
    return frames(Clock.NeoPixel.shown)


def py_heartled(pd_mod, ticks):
    class Src:
        name, inverted, clips_low, drift_filter, sample_ms = "synthetic", True, False, True, 10
        full_scale = (1 << 18) - 1

        def __init__(self):
            self.min_amp = pd_mod.MAX3010X_MIN_AMP
            self.skin_present = True
            self.pending = []

        def read(self, out):
            out.extend(self.pending)
            self.pending = []

    src = Src()
    pd_mod._open_source = lambda: src
    Clock.t = 0.0
    Clock.NeoPixel.shown = []
    p = pd_mod.PulseDetector()
    led = Clock.led.HeartbeatLED(p)
    for now, skin, chunk in ticks:
        Clock.t = now / 1000.0
        src.skin_present = skin
        src.pending = list(chunk) if skin else []
        p.tick()
        led.tick()
    return frames(Clock.NeoPixel.shown)


def py_settings():
    return [Clock.settings.settings_to_message(Clock.settings.DEFAULT_SETTINGS).strip()]

# ---------------------------------------------------------------- compare

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.split()


TIMED = ("T", "F", "R")   # Lines whose first field is a time: compared to within half a sample


def close(a, b, tol):
    fa, fb = a.split(","), b.split(",")
    if len(fa) != len(fb) or fa[0] != fb[0]:
        return False
    for k, (x, y) in enumerate(zip(fa[1:], fb[1:])):
        if k == 0 and fa[0] in TIMED:
            # Seconds (T, F) or ms (R): absolute, not relative (2% of 120 s would hide whole breaths)
            if abs(float(x) - float(y)) > (5.0 if fa[0] == "R" else 0.005):
                return False
        elif abs(float(x) - float(y)) > tol * max(1.0, abs(float(y))):
            return False
    return True


def report(name, ours, ref, tol):
    n = min(len(ours), len(ref))
    bad = [i for i in range(n) if not close(ours[i], ref[i], tol)]
    print("%-6s C++ %4d lines, reference %4d lines, %d differ (tolerance %g)" % (name, len(ours), len(ref), len(bad), tol))
    for i in bad[:5]:
        print("   #%d  C++ %s\n        ref %s" % (i, ours[i], ref[i]))
    return not bad and len(ours) == len(ref)


def main():
    os.makedirs(OUT, exist_ok=True)
    temps = [float("%.5f" % t) for t in gen_temps()]   # Exactly what the C++ reads from the file
    ticks = gen_ir()
    breaths = gen_breaths()
    tp, ip, bp = (os.path.join(OUT, f) for f in ("temps.txt", "ir.txt", "breaths.txt"))
    with open(tp, "w") as f:
        f.write("\n".join("%.5f" % t for t in temps))
    with open(ip, "w") as f:
        for now, skin, chunk in ticks:
            f.write("%d %d %d %s\n" % (now, 1 if skin else 0, len(chunk) if skin else 0,
                                        " ".join(str(s) for s in chunk) if skin else ""))
    with open(bp, "w") as f:
        f.write("\n".join(" ".join(str(x) for x in r) for r in breaths))

    exe = os.path.join(OUT, "host_test")   # Built with -ffp-contract=off: no fused multiply-add, as Python rounds each step
    w = os.path.join(ROOT, "firmware_v2", "wearable")
    subprocess.run(["clang++", "-std=c++17", "-O1", "-ffp-contract=off", "-Wall", "-o", exe, os.path.join(HERE, "host_test.cpp"),
                    os.path.join(w, "breath.cpp"), os.path.join(w, "pulse.cpp"), os.path.join(w, "scoring.cpp"),
                    os.path.join(w, "display.cpp"), os.path.join(w, "protocol.cpp")],
                   check=True)

    bd, pd = load_v1()
    ok = True
    ok &= report("breath", run([exe, "breath", tp]), py_breath(bd, temps), TOL)
    ok &= report("pulse", run([exe, "pulse", ip]), py_pulse(pd, ticks), TOL)
    ok &= report("mood", run([exe, "mood", bp]), run([DART, os.path.join(HERE, "mood_ref.dart"), bp]), 0.0)
    ok &= report("bleds", run([exe, "breathled", tp]), py_breathled(bd, temps), TOL)
    ok &= report("hleds", run([exe, "heartled", ip]), py_heartled(pd, ticks), TOL)
    # R: the C++ reports the app's mood defaults (calm_var 0.10, focus_con 0.15) where v1's file
    # had 0.5 (unused by v1); those two fields are left out
    ours, ref = run([exe, "settings"]), py_settings()
    drop = lambda line: ",".join(f for i, f in enumerate(line.split(",")) if i not in (13, 14))
    ok &= report("R", [drop(x) for x in ours], [drop(x) for x in ref], 0.0)
    print("ALL MATCH" if ok else "DIFFERENCES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
