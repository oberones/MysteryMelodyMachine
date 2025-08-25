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

## Phase 0 Implementation Status

- [x] Create `teensy/firmware/` structure
- [x] Basic blink / Serial Hello
- [x] Confirm USB Type = MIDI enumerates

### Current Features (Phase 0):
- Built-in LED heartbeat blink (1 Hz)
- Serial debug output at 115200 baud
- Basic MIDI note on/off for button 0 (test functionality)
- Portal LED initialization and startup sequence
- Simple breathing portal animation
- MIDI USB configuration

## Testing Phase 0

1. **Upload the firmware** to your Teensy 4.1:
   ```bash
   # For production (MIDI mode)
   pio run --target upload
   
   # For debugging (Serial mode, no MIDI)
   pio run -e teensy41-debug --target upload
   ```

2. **Monitor serial output**:
   ```bash
   # For debug version only
   pio device monitor -e teensy41-debug
   ```

3. **Test MIDI enumeration**: 
   - Production mode: Device appears as "Teensy MIDI" in your DAW/MIDI software
   - Debug mode: No MIDI functionality, serial monitoring available

4. **Test basic input**: Press button connected to pin 2
   - Production mode: Sends MIDI Note 60 (C4)
   - Debug mode: Shows button press in serial output

5. **Observe portal**: LEDs should show startup sequence, then gentle blue breathing

6. **Verify heartbeat**: Built-in LED should blink every second

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

## Expected Serial Output

```
=== Mystery Melody Machine Teensy Firmware ===
Phase 0: Bootstrap
Firmware compiled: Aug 25 2025 14:30:45
USB Type: MIDI
Button 0: Pin 2 configured
Button 1: Pin 3 configured
...
Joystick pins configured
Switch 0: Pin 16 configured
...
FastLED initialized: 60 LEDs on pin 1
Testing MIDI enumeration...
MIDI test note sent (C4)
Starting portal initialization sequence...
Portal startup sequence complete
=== Setup Complete ===
Main loop target: 1000 Hz
Portal target: 60 Hz
Entering main loop...
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

## MIDI Mapping (Phase 0 Test)

- **Button 0**: MIDI Note 60 (C4) on Channel 1, Velocity 100

## Next Phases

- **Phase 1**: Implement full input scanning with all buttons, pots, joystick, switches
- **Phase 2**: Add debouncing and analog smoothing
- **Phase 3**: Integrate complete portal animation system
- **Phase 4**: Performance optimization and hardening

## Troubleshooting

### No serial output (production/MIDI mode):
1. This is normal - MIDI mode doesn't provide serial monitoring via PlatformIO
2. Use debug mode for serial monitoring: `pio run -e teensy41-debug --target upload`
3. Or use Arduino IDE Serial Monitor with production MIDI mode

### No MIDI device appears (debug mode):
1. This is normal - debug mode has no MIDI functionality
2. Use production mode for MIDI: `pio run --target upload`
3. Verify device appears as "Teensy MIDI" in your DAW

### No MIDI device appears (production mode):
1. Verify USB Type is set to "MIDI"
2. Try different USB cable
3. Check if Teensy Loader shows the device

### LEDs not working:
1. Verify LED_DATA_PIN connection (Pin 1)
2. Check LED strip power supply
3. Ensure LED_COUNT matches your strip length
