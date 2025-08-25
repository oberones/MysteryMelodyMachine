#pragma once

// Pin definitions for Teensy 4.1 Mystery Melody Machine
// Digital pins for buttons, joystick, switches
// Analog pins for potentiometers
// LED data pin for infinity portal

// ===== DIGITAL INPUT PINS =====
// Buttons (10 total)
constexpr uint8_t BUTTON_PINS[] = {
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11
};
constexpr uint8_t BUTTON_COUNT = sizeof(BUTTON_PINS) / sizeof(BUTTON_PINS[0]);

// Joystick directions (4 directions)
constexpr uint8_t JOY_UP_PIN = 12;
constexpr uint8_t JOY_DOWN_PIN = 13;
constexpr uint8_t JOY_LEFT_PIN = 14;
constexpr uint8_t JOY_RIGHT_PIN = 15;

// Switches (3 total)
constexpr uint8_t SWITCH_PINS[] = {
    16, 17, 18
};
constexpr uint8_t SWITCH_COUNT = sizeof(SWITCH_PINS) / sizeof(SWITCH_PINS[0]);

// ===== ANALOG INPUT PINS =====
// Potentiometers (6 total)
constexpr uint8_t POT_PINS[] = {
    A0, A1, A2, A3, A6, A7  // A4/A5 reserved for I2C if needed
};
constexpr uint8_t POT_COUNT = sizeof(POT_PINS) / sizeof(POT_PINS[0]);

// ===== LED OUTPUT PINS =====
constexpr uint8_t LED_DATA_PIN = 1;  // Pin 1 for LED data
constexpr uint8_t LED_COUNT = 60;    // Typical infinity portal LED count

// ===== BUILT-IN PINS =====
constexpr uint8_t BUILTIN_LED_PIN = 13;  // Teensy 4.1 built-in LED
