// hw.h - Board-level I/O: thermistor, battery, LED power switch, button, sleep, watchdog.

#pragma once

#include <Arduino.h>

namespace hw {

void begin();

// Thermistor: power the divider (XIAO D1) only while breath sensing runs
void therm_power(bool on);
// One reading: temperature (C) and whether a thermistor is plugged in at all
bool read_therm(float& temp_c);   // Returns plugged

// Battery (XIAO: on-board divider, P0.14 kept low; see the Seeed caveat about driving it high)
float battery_volts();            // 0 when no battery is seen
int battery_percent(float v);     // 0-100, -1 when none
bool usb_powered();               // VBUS present (computer or charger)

// LED power through the S8550/S8050 switch on D3. Turning off drives the data pins low first.
void led_power(bool on);

// Button on D6 to GND
bool button_down();

// Full sleep (System OFF): wakes on the button or USB, which resets the board
[[noreturn]] void system_off();

void watchdog_begin(uint32_t seconds);
void watchdog_feed();
bool reset_by_watchdog();

uint32_t chip_id16();             // For the advertised name

}  // namespace hw
