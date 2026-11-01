// hw.cpp - see hw.h.

#include "hw.h"

#include <math.h>
#include <nrf.h>
#include <nrf_gpio.h>
#include <nrf_sdm.h>
#include <nrf_soc.h>

#include "config.h"

namespace hw {

static bool reset_by_wdt_ = false;

void begin() {
  reset_by_wdt_ = (NRF_POWER->RESETREAS & POWER_RESETREAS_DOG_Msk) != 0;
  NRF_POWER->RESETREAS = 0xFFFFFFFF;   // Clear (write 1s)

  analogReadResolution(ADC_BITS);
#if BOARD_XIAO
  // Ratiometric thermistor: the divider is fed from D1 (VDD), so read against VDD
  analogReference(AR_VDD4);
  pinMode(PIN_THERM_POWER, OUTPUT);
  digitalWrite(PIN_THERM_POWER, LOW);
#ifdef VBAT_ENABLE
  pinMode(VBAT_ENABLE, OUTPUT);
  digitalWrite(VBAT_ENABLE, LOW);      // Keep low: high while charging risks the P0.31 input
#endif
#endif
#if HAS_LED_SWITCH
  pinMode(PIN_LED_POWER, OUTPUT);
  digitalWrite(PIN_LED_POWER, LOW);
#endif
#if HAS_BUTTON
  pinMode(PIN_BUTTON, INPUT_PULLUP);
#endif
}

void therm_power(bool on) {
#if BOARD_XIAO
  digitalWrite(PIN_THERM_POWER, on ? HIGH : LOW);
#else
  (void)on;
#endif
}

bool read_therm(float& temp_c) {
  const float full = (float)((1 << ADC_BITS) - 1);
  int raw = analogRead(PIN_THERM);
  if (raw >= full * THERM_UNPLUGGED_FRAC) {   // Nothing pulling A0 down: plug out
    temp_c = 0;
    return false;
  }
  if (raw < 1) raw = 1;
  float r_ntc = R_REF * raw / (full - raw);   // NTC from A0 to GND, R_REF from the supply to A0
  float inv_t = 1.0f / (T0_C + 273.15f) + logf(r_ntc / R0) / BETA;
  temp_c = 1.0f / inv_t - 273.15f;
  return true;
}

float battery_volts() {
#if BOARD_XIAO && defined(PIN_VBAT)
  analogReference(AR_INTERNAL_3_0);
  uint32_t sum = 0;
  for (int i = 0; i < 16; i++) sum += analogRead(PIN_VBAT);
  analogReference(AR_VDD4);
  // 1M/510k divider; 3.0 V reference
  float v = (sum / 16.0f) / ((1 << ADC_BITS) - 1) * 3.0f * (1510.0f / 510.0f);
  return v >= BATTERY_MIN_V ? v : 0.0f;
#else
  return 0.0f;   // v1 wiring (A2 divider) isn't used on v2; compile-check board reports none
#endif
}

int battery_percent(float v) {
  static const float curve[][2] = {{4.20f, 100}, {4.10f, 90}, {4.00f, 80}, {3.90f, 65}, {3.80f, 50},
                                   {3.75f, 40},  {3.70f, 30}, {3.65f, 20}, {3.60f, 12}, {3.50f, 5},
                                   {3.40f, 0}};
  if (v < BATTERY_MIN_V) return -1;
  if (v >= curve[0][0]) return 100;
  for (int i = 0; i < 10; i++) {
    float vh = curve[i][0], ph = curve[i][1], vl = curve[i + 1][0], pl = curve[i + 1][1];
    if (v >= vl) return (int)(pl + (ph - pl) * (v - vl) / (vh - vl) + 0.5f);
  }
  return 0;
}

bool usb_powered() { return (NRF_POWER->USBREGSTATUS & POWER_USBREGSTATUS_VBUSDETECT_Msk) != 0; }

void led_power(bool on) {
#if HAS_LED_SWITCH
  if (!on) {
    // Data pins low before cutting power, or the strips power up through them
    pinMode(PIN_LED_LEFT, OUTPUT);
    pinMode(PIN_LED_RIGHT, OUTPUT);
    digitalWrite(PIN_LED_LEFT, LOW);
    digitalWrite(PIN_LED_RIGHT, LOW);
  }
  digitalWrite(PIN_LED_POWER, on ? HIGH : LOW);
#else
  (void)on;
#endif
}

bool button_down() {
#if HAS_BUTTON
  return digitalRead(PIN_BUTTON) == LOW;
#else
  return false;
#endif
}

void system_off() {
  led_power(false);
  therm_power(false);
#if HAS_BUTTON
  // Wake on the button (pin sense low). Wait for release first, or it wakes straight away.
  while (button_down()) delay(10);
  delay(50);
  nrf_gpio_cfg_sense_input(g_ADigitalPinMap[PIN_BUTTON], NRF_GPIO_PIN_PULLUP, NRF_GPIO_PIN_SENSE_LOW);
#endif
  // USB plug-in (VBUS detected) also wakes the nRF52840 from System OFF. To test on the board.
  uint8_t sd_enabled = 0;
  sd_softdevice_is_enabled(&sd_enabled);
  if (sd_enabled)
    sd_power_system_off();
  NRF_POWER->SYSTEMOFF = 1;
  while (true) {}
}

void watchdog_begin(uint32_t seconds) {
  NRF_WDT->CONFIG = (WDT_CONFIG_SLEEP_Run << WDT_CONFIG_SLEEP_Pos) | (WDT_CONFIG_HALT_Pause << WDT_CONFIG_HALT_Pos);
  NRF_WDT->CRV = seconds * 32768;
  NRF_WDT->RREN = WDT_RREN_RR0_Msk;
  NRF_WDT->TASKS_START = 1;
}

void watchdog_feed() { NRF_WDT->RR[0] = WDT_RR_RR_Reload; }

bool reset_by_watchdog() { return reset_by_wdt_; }

uint32_t chip_id16() { return NRF_FICR->DEVICEID[0] & 0xFFFF; }

}  // namespace hw
