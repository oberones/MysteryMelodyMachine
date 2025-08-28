#!/usr/bin/env python3
"""
MIDI diagnostic script for Raspberry Pi debugging.

This script helps diagnose MIDI port connection issues on Raspberry Pi systems.
Run this script to get detailed information about MIDI ports and ALSA configuration.
"""

import logging
import subprocess
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_alsa_setup():
    """Check ALSA sequencer setup."""
    print("\n=== ALSA Sequencer Status ===")
    
    # Check if ALSA sequencer module is loaded
    code, out, err = run_command("lsmod | grep snd_seq")
    if code == 0 and out.strip():
        print("✓ ALSA sequencer module is loaded:")
        print(f"  {out.strip()}")
    else:
        print("✗ ALSA sequencer module not found")
        print("  Try: sudo modprobe snd-seq")
    
    # Check ALSA sequencer clients
    print("\n--- ALSA Sequencer Clients ---")
    code, out, err = run_command("aconnect -l")
    if code == 0:
        print(out)
    else:
        print(f"Error running aconnect: {err}")
    
    # Check for ALSA configuration files
    print("\n--- ALSA Configuration ---")
    alsa_configs = [
        "/etc/asound.conf",
        "~/.asoundrc",
        "/proc/asound/cards",
        "/proc/asound/devices"
    ]
    
    for config_path in alsa_configs:
        expanded_path = os.path.expanduser(config_path)
        if os.path.exists(expanded_path):
            print(f"✓ Found: {config_path}")
            if config_path.endswith(('cards', 'devices')):
                try:
                    with open(expanded_path, 'r') as f:
                        content = f.read().strip()
                        if content:
                            print(f"  Content:\n{content}")
                except Exception as e:
                    print(f"  Error reading: {e}")
        else:
            print(f"- Not found: {config_path}")

def check_usb_devices():
    """Check USB devices for MIDI controllers."""
    print("\n=== USB Devices ===")
    
    code, out, err = run_command("lsusb")
    if code == 0:
        lines = out.strip().split('\n')
        midi_devices = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['midi', 'audio', 'teensy', 'arduino']):
                midi_devices.append(line)
        
        if midi_devices:
            print("Potential MIDI devices found:")
            for device in midi_devices:
                print(f"  {device}")
        else:
            print("No obvious MIDI devices found in USB list")
            print("Full USB device list:")
            print(out)
    else:
        print(f"Error running lsusb: {err}")

def check_mido_backend():
    """Check which MIDO backend is being used."""
    print("\n=== MIDO Backend Information ===")
    
    try:
        import mido
        
        # Try to get version, but handle older versions gracefully
        try:
            version = mido.__version__
            print(f"MIDO version: {version}")
        except AttributeError:
            print("MIDO version: Not available (older version)")
        
        # Try to get backend info
        try:
            print(f"MIDO backend: {mido.backend}")
        except Exception as e:
            print(f"MIDO backend: Could not determine ({e})")
        
        # Get available backends
        print("\nAvailable backends:")
        try:
            for backend_name in mido.backend._get_backends():
                try:
                    backend = mido.backend._get_backend(backend_name)
                    print(f"  ✓ {backend_name}: {backend}")
                except Exception as e:
                    print(f"  ✗ {backend_name}: {e}")
        except Exception as e:
            print(f"  Error listing backends: {e}")
        
    except ImportError as e:
        print(f"Error importing mido: {e}")

def check_midi_ports():
    """Check available MIDI ports using mido."""
    print("\n=== MIDO MIDI Ports ===")
    
    try:
        import mido
        
        # Input ports
        print("Input ports:")
        input_ports = mido.get_input_names()
        if input_ports:
            for i, port in enumerate(input_ports):
                print(f"  {i}: {port}")
        else:
            print("  No input ports found")
        
        # Output ports
        print("\nOutput ports:")
        output_ports = mido.get_output_names()
        if output_ports:
            for i, port in enumerate(output_ports):
                print(f"  {i}: {port}")
        else:
            print("  No output ports found")
        
        return input_ports, output_ports
        
    except ImportError as e:
        print(f"Error importing mido: {e}")
        return [], []
    except Exception as e:
        print(f"Error getting MIDI ports: {e}")
        return [], []

def test_port_connection(port_name, is_input=True):
    """Test connecting to a specific MIDI port."""
    print(f"\n--- Testing {'input' if is_input else 'output'} port: {port_name} ---")
    
    try:
        import mido
        
        if is_input:
            port = mido.open_input(port_name)
            print(f"✓ Successfully opened input port: {port_name}")
        else:
            port = mido.open_output(port_name)
            print(f"✓ Successfully opened output port: {port_name}")
        
        port.close()
        print(f"✓ Successfully closed port: {port_name}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to open port {port_name}: {e}")
        return False

def check_permissions():
    """Check user permissions for audio/MIDI access."""
    print("\n=== User Permissions ===")
    
    # Check user groups
    code, out, err = run_command("groups")
    if code == 0:
        groups = out.strip().split()
        audio_groups = ['audio', 'dialout', 'plugdev']
        
        print(f"User groups: {' '.join(groups)}")
        
        for group in audio_groups:
            if group in groups:
                print(f"✓ User is in {group} group")
            else:
                print(f"✗ User NOT in {group} group (may be needed for MIDI access)")
                print(f"  To add: sudo usermod -a -G {group} $USER")
    
    # Check device permissions
    devices_to_check = [
        "/dev/snd/seq",
        "/dev/midi*",
        "/dev/ttyACM*",
        "/dev/ttyUSB*"
    ]
    
    print("\nDevice permissions:")
    for device_pattern in devices_to_check:
        code, out, err = run_command(f"ls -l {device_pattern} 2>/dev/null")
        if code == 0 and out.strip():
            print(f"  {device_pattern}:")
            for line in out.strip().split('\n'):
                print(f"    {line}")
        else:
            print(f"  {device_pattern}: Not found or no access")

def suggest_fixes():
    """Suggest potential fixes for common issues."""
    print("\n=== Suggested Fixes ===")
    
    fixes = [
        "1. Load ALSA sequencer module:",
        "   sudo modprobe snd-seq",
        "",
        "2. Add user to audio groups:",
        "   sudo usermod -a -G audio,dialout,plugdev $USER",
        "   (then logout and login again)",
        "",
        "3. Install ALSA utilities if missing:",
        "   sudo apt-get update",
        "   sudo apt-get install alsa-utils",
        "",
        "4. Check if PulseAudio is interfering:",
        "   pulseaudio --check -v",
        "   (if running, try: pulseaudio -k)",
        "",
        "5. Create minimal ALSA config (~/.asoundrc):",
        "   pcm.!default {",
        "       type hw",
        "       card 0",
        "   }",
        "   ctl.!default {",
        "       type hw",
        "       card 0",
        "   }",
        "",
        "6. Force reload ALSA:",
        "   sudo alsa force-reload",
        "",
        "7. Check dmesg for USB/MIDI device messages:",
        "   dmesg | grep -i 'usb\\|midi\\|audio'",
    ]
    
    for fix in fixes:
        print(fix)

def main():
    """Main diagnostic function."""
    print("MIDI Diagnostic Tool for Raspberry Pi")
    print("=====================================")
    
    # System info
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current user: {os.getenv('USER', 'unknown')}")
    
    # Run all checks
    check_alsa_setup()
    check_usb_devices()
    check_permissions()
    check_mido_backend()
    
    # Test MIDI ports
    input_ports, output_ports = check_midi_ports()
    
    # Test connecting to found ports
    if input_ports:
        print(f"\n=== Testing Input Port Connections ===")
        for port in input_ports[:3]:  # Test first 3 ports to avoid spam
            test_port_connection(port, is_input=True)
    
    if output_ports:
        print(f"\n=== Testing Output Port Connections ===")
        for port in output_ports[:3]:  # Test first 3 ports to avoid spam
            test_port_connection(port, is_input=False)
    
    suggest_fixes()
    
    print("\n=== Diagnostic Complete ===")
    print("Please share this output when reporting MIDI issues.")

if __name__ == "__main__":
    main()
