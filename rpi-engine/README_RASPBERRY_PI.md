# Raspberry Pi MIDI Setup and Troubleshooting

This guide helps you set up and troubleshoot MIDI connections on Raspberry Pi systems, particularly for the Mystery Music Engine.

## Quick Start

1. **Clone and setup the project:**
   ```bash
   cd /path/to/MysteryMelodyMachine/rpi-engine
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the setup check:**
   ```bash
   ./rpi_start.sh setup
   ```

3. **Test MIDI functionality:**
   ```bash
   ./rpi_start.sh test
   ```

4. **Start the engine:**
   ```bash
   # Standard MIDI handling
   ./rpi_start.sh start
   
   # Or with Raspberry Pi optimized MIDI handling
   ./rpi_start.sh start-robust
   ```

## Common Issues and Solutions

### Error: "ALSA error making port connection"

This is the most common MIDI issue on Raspberry Pi. It indicates that the ALSA sequencer isn't properly configured.

**Solution 1: Load ALSA sequencer module**
```bash
sudo modprobe snd-seq
```

**Solution 2: Install ALSA utilities**
```bash
sudo apt-get update
sudo apt-get install alsa-utils
```

**Solution 3: Check user permissions**
```bash
# Add user to audio groups
sudo usermod -a -G audio,dialout,plugdev $USER
# Then logout and login again
```

### Error: "No MIDI ports available"

This means the system can't see any MIDI devices.

**Check USB devices:**
```bash
lsusb | grep -i midi
```

**Check ALSA sequencer clients:**
```bash
aconnect -l
```

**If no devices appear:**
1. Unplug and replug the USB MIDI device
2. Check dmesg for USB messages: `dmesg | tail -20`
3. Try a different USB port
4. Check if the device works on another system

### Error: "MidiInAlsa::openPort: ALSA error making port connection"

This is specifically for input ports and usually indicates permission or sequencer issues.

**Try these steps in order:**
1. `sudo modprobe snd-seq`
2. `sudo alsa force-reload`
3. Check `/dev/snd/` permissions
4. Restart the Pi if other steps don't work

## Diagnostic Tools

### 1. Comprehensive MIDI Diagnostics
```bash
python debug_rpi_midi.py
```

This script checks:
- ALSA sequencer status
- USB MIDI devices
- User permissions
- MIDI port availability
- System configuration

### 2. Simple MIDI Connection Test
```bash
python test_rpi_midi.py
```

This script:
- Tests MIDI port connections
- Verifies message sending
- Provides detailed error analysis

### 3. Manual ALSA Checks
```bash
# List sequencer clients
aconnect -l

# List ALSA cards
cat /proc/asound/cards

# Check sequencer module
lsmod | grep snd_seq

# Check USB devices
lsusb
```

## Alternative Configuration

If you continue to have issues with the standard MIDI handling, try the Raspberry Pi optimized version:

```bash
# Use the robust MIDI classes
python main_rpi.py --use-robust-midi --config config.yaml
```

Or use the startup script:
```bash
./rpi_start.sh start-robust
```

The robust MIDI classes provide:
- Multiple connection retry attempts
- Better error handling for ALSA issues
- Automatic ALSA sequencer loading
- Enhanced logging for debugging

## Configuration for Raspberry Pi

Create a minimal ALSA configuration file `~/.asoundrc` if you have issues:

```
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
```

## Systemd Service (Optional)

To run the engine automatically on boot, create `/etc/systemd/system/mystery-music.service`:

```ini
[Unit]
Description=Mystery Music Engine
After=network.target sound.target

[Service]
Type=simple
User=pi
Group=audio
WorkingDirectory=/home/pi/MysteryMelodyMachine/rpi-engine
Environment=PATH=/home/pi/MysteryMelodyMachine/rpi-engine/.venv/bin
ExecStartPre=/bin/bash -c 'modprobe snd-seq || true'
ExecStart=/home/pi/MysteryMelodyMachine/rpi-engine/.venv/bin/python main_rpi.py --use-robust-midi --config config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable with:
```bash
sudo systemctl enable mystery-music.service
sudo systemctl start mystery-music.service
```

## Hardware-Specific Notes

### Teensy Devices
- Usually appear as "Teensy MIDI" in port lists
- May need the Teensy to be programmed with MIDI firmware
- Check that the Teensy is properly powered

### Generic USB MIDI Devices
- Often appear with manufacturer names
- May need device-specific drivers
- Some cheap MIDI adapters don't work well with Linux

### f_midi Devices
The error message mentions "f_midi:f_midi 28:0" which suggests a gadget MIDI device. This could be:
- A Raspberry Pi configured as a USB MIDI gadget
- Another embedded device presenting as USB MIDI
- May need special configuration or different connection approach

## Logging and Debugging

The engine uses structured logging. Enable debug logging in `config.yaml`:

```yaml
logging:
  level: DEBUG
```

This will show detailed MIDI connection attempts and error information.

## Getting Help

If you continue to have issues:

1. Run the diagnostic script and save the output:
   ```bash
   python debug_rpi_midi.py > midi_debug.txt 2>&1
   ```

2. Check the system logs:
   ```bash
   dmesg | grep -i 'usb\|midi\|audio' > usb_debug.txt
   ```

3. Include this information when reporting issues:
   - Raspberry Pi model and OS version
   - MIDI device make/model
   - Output from diagnostic scripts
   - Any error messages from the engine

## Advanced Troubleshooting

### Force USB Device Reset
```bash
# Find the USB device
lsusb
# Reset the USB bus (replace X with bus number)
sudo bash -c 'echo 0 > /sys/bus/usb/devices/usb1/authorized'
sudo bash -c 'echo 1 > /sys/bus/usb/devices/usb1/authorized'
```

### Check PulseAudio Interference
```bash
# Check if PulseAudio is running
pulseaudio --check -v
# If it's causing issues, stop it temporarily
pulseaudio -k
```

### Rebuild ALSA State
```bash
sudo alsactl store
sudo alsactl restore
```

## Performance Notes

On Raspberry Pi systems:
- MIDI latency may be higher than desktop systems
- USB MIDI is generally more reliable than built-in audio MIDI
- Consider using a powered USB hub for multiple MIDI devices
- SD card speed can affect overall system performance
