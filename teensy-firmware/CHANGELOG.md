# Changelog

All notable changes to the Mystery Melody Machine Teensy firmware will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.1] - 2025-08-25

### Added - Phase 0: Bootstrap
- Created PlatformIO project structure
- Implemented basic firmware skeleton with main.cpp
- Added pin definitions in `include/pins.h`
- Added configuration constants in `include/config.h`
- Set up USB Dual Serial/MIDI configuration
- Implemented basic LED portal initialization and startup sequence
- Added simple breathing portal animation for testing
- Implemented basic MIDI note on/off for button 0 (test functionality)
- Added built-in LED heartbeat blink at 1 Hz
- Created comprehensive README with setup instructions
- Added serial debug output at 115200 baud

### Technical Details
- Main loop running at 1 kHz target frequency
- Portal animation running at 60 Hz target frequency
- FastLED integration for WS2812B LED strip control
- Placeholder pin assignments for 10 buttons, 6 pots, 4-direction joystick, 3 switches
- MIDI mapping: Button 0 → Note 60 (C4) on Channel 1, Velocity 100
- Memory usage: ~54KB flash, ~11KB RAM (Teensy 4.1 has 8MB flash, 1MB RAM)

### Configuration
- Target: Teensy 4.1
- USB Type: MIDI
- LED Count: 60 (configurable)
- Max LED Brightness: 160/255 (configurable)
- Debug mode: Enabled for Phase 0

### Next Phase
- Phase 1: Implement full input scanning with debouncing for all controls
