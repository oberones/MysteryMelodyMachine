# Teensy Firmware - Mystery Melody Machine

This is the Teensy 4.1 firmware for the Mystery Melody Machine project.

## Hardware Requirements

- Teensy 4.1 microcontroller
- WS2812B LED strip (60 LEDs recommended for infinity portal)
- 10 buttons (connected to digital pins with pullup resistors)
- 6 potentiometers (connected to analog pins)
- 4-direction joystick (connected to digital pins)
- 3 switches (connected to digital pins)

## Software Requirements

- [PlatformIO](https://platformio.org/) IDE or CLI
- [Teensyduino](https://www.pjrc.com/teensy/teensyduino.html) (automatically handled by PlatformIO)

## USB Configuration Instructions

**IMPORTANT**: For this firmware to work properly, you need to configure the Teensy for MIDI mode:

### Using Arduino IDE with Teensyduino:
1. Install [Teensyduino](https://www.pjrc.com/teensy/teensyduino.html)
2. In Arduino IDE, go to **Tools** menu
3. Set **Board** to "Teensy 4.1"
4. Set **USB Type** to "MIDI"
5. This enables MIDI functionality (Serial is available for debugging when connected to PC)

### Using PlatformIO:
The `platformio.ini` file is already configured with:
```ini
build_flags = -D USB_MIDI
```
This automatically sets the USB type to MIDI mode.

## Building and Uploading

### Using PlatformIO CLI:
```bash
# Build the project
pio run

# Upload to Teensy
pio run --target upload

# Open serial monitor for debugging
pio device monitor
```

### Using PlatformIO IDE:
1. Open this folder in PlatformIO IDE
2. Click the build button (✓)
3. Click the upload button (→)
4. Use the serial monitor to see debug output

## Project Structure

```
teensy-firmware/
├── src/
│   └── main.cpp              # Main firmware code
├── include/
│   ├── pins.h                # Pin definitions
│   └── config.h              # Configuration constants
├── platformio.ini            # PlatformIO configuration
├── docs/
│   └── TeensySoftwareRoadmap.md
└── README.md                 # This file
```

## Phase 1 Implementation Status

- [x] Implement InputScanner class for all hardware inputs
- [x] Implement MidiOut class with conditional compilation  
- [x] Implement InputMidiMapper for input-to-MIDI conversion
- [x] Full hardware scanning: 10 buttons, 6 pots, 4-direction joystick, 3 switches
- [x] Raw input polling without debouncing (Phase 1 spec)
- [x] MIDI output for all input types with proper mappings

### Current Features (Phase 1):
- **Full Input System**: All 19 physical inputs scanned at 1kHz
- **Button MIDI**: 10 buttons → MIDI Notes 60-69 (C4-A4) with Note On/Off
- **Potentiometer MIDI**: 6 pots → MIDI CC 1-6 with raw 0-127 mapping
- **Joystick MIDI**: 4 directions → MIDI CC 10-13 (edge triggered)
- **Switch MIDI**: 3 switches → MIDI CC 20-22 (state change triggered)
- **Dual Build System**: Production (MIDI) vs Debug (Serial) environments
- **Portal Animation**: Maintained from Phase 0 for visual feedback
- **Serial Debugging**: Comprehensive debug output in debug mode

## Testing Phase 1

1. **Upload the firmware** to your Teensy 4.1:
   ```bash
   # For production (MIDI mode) - full input scanning with MIDI output
   pio run --target upload
   
   # For debugging (Serial mode) - input scanning with serial debug output
   pio run -e teensy41-debug --target upload
   ```

2. **Monitor debug output** (debug mode only):
   ```bash
   pio device monitor -e teensy41-debug
   ```

3. **Test all inputs**:
   - **Buttons (Pins 2-11)**: Press any button → sends MIDI Note On/Off (Notes 60-69)
   - **Potentiometers (A0-A3,A6-A7)**: Turn any pot → sends MIDI CC 1-6 (0-127 range)
   - **Joystick (Pins 12-15)**: Move joystick → sends MIDI CC 10-13 (edge triggered)
   - **Switches (Pins 16-18)**: Toggle switches → sends MIDI CC 20-22 (on/off)

4. **MIDI Device Testing**:
   - Production mode: Device appears as "Teensy MIDI" in DAW
   - Debug mode: MIDI messages shown in serial output as "MIDI NoteOn Ch:1 P1:60 P2:100"

5. **Portal Animation**: LEDs show startup sequence, then breathing animation at 60Hz

6. **Performance**: Built-in LED blinks every second, confirming 1kHz main loop

## Development Workflow

### For Production/MIDI Testing:
```bash
pio run --target upload          # Upload MIDI version
# Use Arduino IDE Serial Monitor or DAW to verify MIDI
```

### For Debugging/Development:
```bash
pio run -e teensy41-debug --target upload    # Upload debug version
pio device monitor -e teensy41-debug         # Monitor serial output
```

### Switch Between Modes:
- **Production**: Full MIDI functionality, no serial monitoring via PlatformIO
- **Debug**: Serial monitoring, no MIDI functionality
- Use Arduino IDE Serial Monitor for MIDI mode debugging if needed

## Expected Serial Output (Debug Mode)

```
=== Mystery Melody Machine Teensy Firmware ===
Phase 1: Raw Input + MIDI
Firmware compiled: Jan 15 2025 14:30:45
USB Type: Serial (Debug Mode)
Initializing input scanner...
Initializing MIDI output...
Input mapping: 10 buttons, 6 pots, 3 switches, 4-way joystick
FastLED initialized: 60 LEDs on pin 1
Testing MIDI enumeration...
MIDI not available - debug mode active
Starting portal initialization sequence...
Portal startup sequence complete
=== Setup Complete ===
Main loop target: 1000 Hz
Portal target: 60 Hz
Entering main loop...
MIDI NoteOn Ch:1 P1:60 P2:100    # Button 0 pressed
MIDI NoteOff Ch:1 P1:60 P2:0     # Button 0 released
MIDI CC Ch:1 P1:1 P2:64          # Pot 0 moved to center
MIDI CC Ch:1 P1:10 P2:127        # Joystick up pressed
MIDI CC Ch:1 P1:20 P2:127        # Switch 0 turned on
```

## Pin Assignments

### Digital Inputs (with pullups):
- **Buttons**: Pins 2-11 (10 buttons)
- **Joystick**: Pins 12-15 (Up/Down/Left/Right)
- **Switches**: Pins 16-18 (3 switches)

### Analog Inputs:
- **Potentiometers**: Pins A0-A3, A6-A7 (6 pots)

### Outputs:
- **LED Data**: Pin 1 (WS2812B data)
- **Built-in LED**: Pin 13 (heartbeat)

## MIDI Mapping (Phase 1 Complete)

### Buttons (Digital Input, Active Low):
- **Button 0-9 (Pins 2-11)**: MIDI Notes 60-69 (C4-A4) on Channel 1, Velocity 100

### Potentiometers (Analog Input):
- **Pot 0-5 (Pins A0-A3,A6-A7)**: MIDI CC 1-6 on Channel 1, Value 0-127

### Joystick (Digital Input, Edge Triggered):
- **Up (Pin 12)**: MIDI CC 10 = 127 on press
- **Down (Pin 13)**: MIDI CC 11 = 127 on press  
- **Left (Pin 14)**: MIDI CC 12 = 127 on press
- **Right (Pin 15)**: MIDI CC 13 = 127 on press

### Switches (Digital Input, State Change):
- **Switch 0-2 (Pins 16-18)**: MIDI CC 20-22 on Channel 1, Value 0 (off) or 127 (on)

## Next Phases

- **Phase 2**: Add debouncing, analog smoothing, and input filtering for production quality
- **Phase 3**: Integrate complete portal animation system with MIDI-reactive effects
- **Phase 4**: Performance optimization and hardening for live performance use

## Troubleshooting

### No serial output (production/MIDI mode):
1. This is normal - MIDI mode doesn't provide serial monitoring via PlatformIO
2. Use debug mode for serial monitoring: `pio run -e teensy41-debug --target upload`
3. Or use Arduino IDE Serial Monitor with production MIDI mode

### No MIDI device appears (debug mode):
1. This is normal - debug mode has no MIDI functionality
2. Use production mode for MIDI: `pio run -e teensy41 --target upload`
3. Verify device appears as "Teensy MIDI" in your DAW

### No MIDI device appears (production mode):
1. Verify USB Type is set to "MIDI"
2. Try different USB cable
3. Check if Teensy Loader shows the device

### LEDs not working:
1. Verify LED_DATA_PIN connection (Pin 1)
2. Check LED strip power supply
3. Ensure LED_COUNT matches your strip length
