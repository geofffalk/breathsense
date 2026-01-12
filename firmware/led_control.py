# led_control.py - LED control for Open Breathing and Guided Breathing modes
# Preserves algorithms from blinkersgame/circuitpython/passive_breath_led.py
# and guided_breath_led.py

import time
import board
import neopixel

from config import (
    COLOR_RED, COLOR_WHITE, COLOR_LIGHT_BLUE, COLOR_PURPLE, COLOR_DEEP_BLUE,
    DEFAULT_INHALE_S, DEFAULT_HOLD_IN_S, DEFAULT_EXHALE_S, DEFAULT_HOLD_OUT_S,
)
from breath_detector import PH_IDLE, PH_INH, PH_EXH

# LED strips
_pixels_left = neopixel.NeoPixel(board.D9, 20, brightness=0.1, auto_write=False)
_pixels_right = neopixel.NeoPixel(board.D7, 20, brightness=0.1, auto_write=False)

# Color lookup by depth index
DEPTH_COLORS = [
    COLOR_RED,
    COLOR_WHITE,
    COLOR_LIGHT_BLUE,
    COLOR_PURPLE,
    COLOR_DEEP_BLUE,
]


# State to prevent redundant LED writes
_last_led_state = None


def _show_pixels(colors):
    """
    Set LED colors on both strips (mirrored) with state persistence.
    colors: list of 10 RGB tuples for the visible strip (indices 0-9)
    """
    global _last_led_state
    
    # Simple state check to avoid redundant I2C/SPI writes and flickering
    if _last_led_state == colors:
        return
        
    for i in range(10):
        c = colors[i] if i < len(colors) else (0, 0, 0)
        _pixels_left[i] = c
        _pixels_right[i] = c
    _pixels_left.show()
    _pixels_right.show()
    _last_led_state = list(colors)


def hide_all():
    """Turn off all LEDs."""
    _pixels_left.fill((0, 0, 0))
    _pixels_right.fill((0, 0, 0))
    _pixels_left.show()
    _pixels_right.show()


def play_comet_animation(color, duration_s=1.0, reverse=False):
    """
    Play a comet animation across the LED strip.
    color: RGB tuple for the comet head
    duration_s: total animation duration
    reverse: if True, animate from back to front; else front to back
    """
    tail_color = tuple(c // 4 for c in color)
    strip_len = 10
    steps = 15
    step_delay = duration_s / steps
    
    for step in range(steps + 1):
        progress = step / steps
        if reverse:
            head_pos = int(progress * (strip_len - 1))
        else:
            head_pos = int((1.0 - progress) * (strip_len - 1))
        
        colors = [(0, 0, 0)] * strip_len
        
        # Head
        if 0 <= head_pos < strip_len:
            colors[head_pos] = color
        
        # Tail
        if reverse:
            tail_pos = head_pos - 1
        else:
            tail_pos = head_pos + 1
        if 0 <= tail_pos < strip_len:
            colors[tail_pos] = tail_color
        
        _show_pixels(colors)
        time.sleep(step_delay)
    
    hide_all()


def play_startup_animation():
    """Blue comet animation on firmware boot."""
    COLOR_BLUE = (0, 0, 255)
    play_comet_animation(COLOR_BLUE, duration_s=0.8, reverse=False)


def play_ble_connected_animation():
    """Orange comet animation on BLE connection."""
    COLOR_ORANGE = (255, 100, 0)
    play_comet_animation(COLOR_ORANGE, duration_s=0.6, reverse=True)


class OpenBreathingLED:
    """
    Open Breathing mode LED controller.
    - Inhale: Shows LED at front (index 9)
    - Exhale: Comet moves backward from front to back
    - Color based on breath depth
    """

    def __init__(self, breath_detector):
        self.det = breath_detector
        self.last_phase = PH_IDLE
        self.phase_stable_time = 0
        self.pending_phase = PH_IDLE
        self.PHASE_DEBOUNCE_S = 0.35 # 350ms grace period for stability
        self.exhale_start_time = None
        self.exhale_pred = 2.0  # Predicted exhale duration
        self.exhale_locked = False # Prevent re-triggering after exhale end

        # Comet settings
        self.comet_len = 2
        self.strip_len = 10

    def tick(self):
        """Update LEDs based on breath phase."""
        now = time.monotonic()
        
        # Unworn detection disabled for testing
        # if self.det.unworn:
        #     hide_all()
        #     self.last_phase = PH_IDLE
        #     return
        
        phase = self.det.phase
        depth_color = self.det.get_depth_color()
        color = DEPTH_COLORS[depth_color]

        # Debounced phase transition
        if phase != self.last_phase:
            if self.pending_phase != phase:
                self.pending_phase = phase
                self.phase_stable_time = now
            elif (now - self.phase_stable_time) >= self.PHASE_DEBOUNCE_S:
                # Commit the phase change
                if phase == PH_INH:
                    self._on_inhale_start(color)
                    self.exhale_locked = False # Unlock on inhale
                elif phase == PH_EXH:
                    self._on_exhale_start(now)
                    self.exhale_locked = False # Ensure unlocked on start
                self.last_phase = phase
        else:
            self.pending_phase = phase

        # render based on current phase (use debounced self.last_phase for rendering stability)
        display_phase = self.last_phase
        
        # Sticky Exhale: if we just dropped from exhale, keep rendering exhale for a tiny bit 
        # to handle brief sensor dips below threshold.
        if phase == PH_IDLE and self.last_phase == PH_EXH:
            if (now - self.exhale_start_time) < self.exhale_pred + 0.2:
                display_phase = PH_EXH

        if display_phase == PH_EXH:
            self._render_exhale(now, depth_color)
        elif display_phase == PH_IDLE:
            # Keep the comet visible briefly at the end of exhale
            if self.exhale_start_time and (now - self.exhale_start_time) < self.exhale_pred + 0.5:
                self._render_exhale(now, depth_color)
            # Dim after 4 seconds of idle
            elif self.exhale_start_time and (now - self.exhale_start_time) > 4.0:
                self.exhale_locked = False # Reset on long idle
                hide_all()

    def _on_inhale_start(self, color):
        """Show LED at front for inhale."""
        colors = [(0, 0, 0)] * 10
        colors[9] = color  # Front position
        _show_pixels(colors)
        self.exhale_start_time = None
        self.exhale_locked = False # Reset lock on inhale

    def _on_exhale_start(self, now):
        """Start exhale animation."""
        self.exhale_start_time = now
        # Use last exhale duration as prediction
        self.exhale_pred = max(1.0, self.det.last_exhale_duration)

    def _render_exhale(self, now, depth_color):
        """Render exhale comet moving backward."""
        if self.exhale_locked:
            return

        if self.exhale_start_time is None:
            self.exhale_start_time = now

        elapsed = now - self.exhale_start_time
        pred = max(0.5, self.exhale_pred)
        progress = min(1.0, elapsed / pred)

        color = DEPTH_COLORS[depth_color]
        tail_color = tuple(c // 4 for c in color)

        # Head position: 9 (front) -> 0 (back)
        span = self.strip_len - 1
        head_index = int((1.0 - progress) * span)

        colors = [(0, 0, 0)] * 10

        # Head
        if 0 <= head_index < 10:
            colors[head_index] = color

        # Tail (behind head)
        tail_index = head_index + 1
        if 0 <= tail_index < 10:
            colors[tail_index] = tail_color

        _show_pixels(colors)

        # End of exhale
        if progress >= 1.0:
            self.exhale_locked = True # Lock until next inhale
            hide_all()


class GuidedBreathingLED:
    """
    Guided Breathing mode LED controller.
    Guides user through timed breathing cycles:
    Inhale -> Hold -> Exhale -> Hold -> repeat
    """

    # Guided phases
    G_INHALE = 0
    G_HOLD_IN = 1
    G_EXHALE = 2
    G_HOLD_OUT = 3

    def __init__(self, breath_detector):
        self.det = breath_detector

        # Timing (can be updated via settings)
        self.inhale_s = DEFAULT_INHALE_S
        self.hold_in_s = DEFAULT_HOLD_IN_S
        self.exhale_s = DEFAULT_EXHALE_S
        self.hold_out_s = DEFAULT_HOLD_OUT_S
        
        # LED range (can be updated via settings)
        self.led_start = 0
        self.led_end = 8

        # State
        self.phase = self.G_EXHALE  # Start with exhale
        self.phase_start = time.monotonic()
        self.calibrating = True

        # Colors
        self.active_color = (0, 255, 0)  # Green for active breathing
        self.exhale_color = (0, 255, 255) # Cyan for guided exhale
        self.hold_color = (255, 20, 0)   # Orange-red for hold

        # LED position
        self.current_pos = self.led_end

    def set_durations(self, inhale, hold_in, exhale, hold_out):
        """Update guided breathing timing."""
        self.inhale_s = float(inhale)
        self.hold_in_s = float(hold_in)
        self.exhale_s = float(exhale)
        self.hold_out_s = float(hold_out)

    def set_range(self, start, end):
        """Update LED range for guided animation."""
        self.led_start = int(start)
        self.led_end = int(end)

    def get_phase(self):
        """Return current guided phase (0-3) or -1 if calibrating."""
        if self.calibrating:
            return -1
        return self.phase

    def reset(self):
        """Reset the guided cycle."""
        self.phase = self.G_EXHALE
        self.phase_start = time.monotonic()
        self.current_pos = self.led_end
        self.calibrating = True

    def tick(self, visible=True):
        """Update guided breathing LEDs."""
        now = time.monotonic()
        breath_phase = self.det.phase

        # Calibration: wait for first exhale to sync
        if self.calibrating:
            if breath_phase == PH_EXH:
                self.calibrating = False
                self.phase = self.G_EXHALE
                self.phase_start = now
                self.current_pos = self.led_end
            else:
                hide_all()
                return

        elapsed = now - self.phase_start

        if self.phase == self.G_EXHALE:
            self._tick_exhale(elapsed, breath_phase, visible)
            if elapsed >= self.exhale_s:
                self._enter_phase(self.G_HOLD_OUT, now)

        elif self.phase == self.G_HOLD_OUT:
            if visible:
                self._render_hold(self.led_start)  # Hold at back end of range
            if elapsed >= self.hold_out_s:
                self._enter_phase(self.G_INHALE, now)

        elif self.phase == self.G_INHALE:
            self._tick_inhale(elapsed, breath_phase, visible)
            if elapsed >= self.inhale_s:
                self._enter_phase(self.G_HOLD_IN, now)

        elif self.phase == self.G_HOLD_IN:
            if visible:
                self._render_hold(self.led_end)  # Hold at front end of range
            if elapsed >= self.hold_in_s:
                self._enter_phase(self.G_EXHALE, now)

    def _enter_phase(self, new_phase, now):
        """Transition to new guided phase."""
        self.phase = new_phase
        self.phase_start = now
        if new_phase == self.G_EXHALE:
            self.current_pos = self.led_end
        elif new_phase == self.G_INHALE:
            self.current_pos = self.led_start

    def _tick_exhale(self, elapsed, breath_phase, visible):
        """Exhale phase: LED moves from front to back."""
        if self.exhale_s <= 0:
            progress = 1.0
        else:
            # Only advance if user is actually exhaling
            if breath_phase == PH_EXH:
                progress = min(1.0, elapsed / self.exhale_s)
                self.current_pos = int(self.led_end - progress * (self.led_end - self.led_start))
            else:
                # User is not exhaling correctly, stay at current position (no flashing)
                pass

        if visible:
            self._render_active(self.exhale_color)

    def _tick_inhale(self, elapsed, breath_phase, visible):
        """Inhale phase: LED moves from back to front."""
        if self.inhale_s <= 0:
            progress = 1.0
        else:
            # Only advance if user is actually inhaling
            if breath_phase == PH_INH:
                progress = min(1.0, elapsed / self.inhale_s)
                self.current_pos = int(self.led_start + progress * (self.led_end - self.led_start))
            else:
                # User is not inhaling correctly, stay at current position (no flashing)
                pass

        if visible:
            self._render_active(self.active_color)

    def _render_active(self, color):
        """Render active breathing LED."""
        colors = [(0, 0, 0)] * 10
        pos = max(0, min(9, self.current_pos))
        colors[pos] = color
        _show_pixels(colors)

    def _render_hold(self, position):
        """Render hold phase LED."""
        colors = [(0, 0, 0)] * 10
        pos = max(0, min(9, position))
        colors[pos] = self.hold_color
        _show_pixels(colors)
