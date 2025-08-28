#!/usr/bin/env python3
"""
Simple MIDI connection test for Raspberry Pi.

This script attempts to connect to MIDI ports with more detailed error reporting
and fallback strategies for common Raspberry Pi MIDI issues.
"""

import logging
import sys
import time
from typing import Optional

# Configure logging to match your engine's format
logging.basicConfig(
    level=logging.INFO,
    format='ts=%(asctime)s.%(msecs)03d level=%(levelname)s logger=%(name)s msg="%(message)s"',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
log = logging.getLogger("midi_test")

def safe_import_mido():
    """Safely import mido with error handling."""
    try:
        import mido
        
        # Try to get version, but don't fail if not available
        try:
            version = mido.__version__
            log.info(f"Successfully imported mido version {version}")
        except AttributeError:
            log.info("Successfully imported mido (version info not available)")
        
        # Try to get backend info
        try:
            log.info(f"Using backend: {mido.backend}")
        except Exception as e:
            log.warning(f"Could not get backend info: {e}")
        
        return mido
    except ImportError as e:
        log.error(f"Failed to import mido: {e}")
        log.error("Install with: pip install mido python-rtmidi")
        return None
    except Exception as e:
        log.error(f"Unexpected error importing mido: {e}")
        return None

def list_midi_ports(mido):
    """List all available MIDI ports."""
    try:
        input_ports = mido.get_input_names()
        output_ports = mido.get_output_names()
        
        log.info(f"Found {len(input_ports)} input ports:")
        for i, port in enumerate(input_ports):
            log.info(f"  Input {i}: {port}")
        
        log.info(f"Found {len(output_ports)} output ports:")
        for i, port in enumerate(output_ports):
            log.info(f"  Output {i}: {port}")
        
        return input_ports, output_ports
    except Exception as e:
        log.error(f"Failed to list MIDI ports: {e}")
        return [], []

def test_port_open(mido, port_name: str, is_input: bool = True) -> bool:
    """Test opening a specific MIDI port."""
    port_type = "input" if is_input else "output"
    log.info(f"Testing {port_type} port: {port_name}")
    
    try:
        if is_input:
            port = mido.open_input(port_name)
        else:
            port = mido.open_output(port_name)
        
        log.info(f"Successfully opened {port_type} port: {port_name}")
        port.close()
        log.info(f"Successfully closed {port_type} port: {port_name}")
        return True
        
    except Exception as e:
        log.error(f"Failed to open {port_type} port '{port_name}': {e}")
        
        # Additional error analysis
        if "ALSA error making port connection" in str(e):
            log.error("This is an ALSA sequencer connection error")
            log.error("Possible causes:")
            log.error("  1. ALSA sequencer module not loaded (try: sudo modprobe snd-seq)")
            log.error("  2. Permission issues (user not in audio group)")
            log.error("  3. Device not properly enumerated in ALSA")
            log.error("  4. Port name exists but device is disconnected")
        
        return False

def test_virtual_port(mido):
    """Test creating a virtual MIDI port as fallback."""
    log.info("Testing virtual port creation as fallback...")
    
    try:
        # Try creating a virtual input port
        virtual_input = mido.open_input("test_virtual_input", virtual=True)
        log.info("Successfully created virtual input port")
        virtual_input.close()
        
        # Try creating a virtual output port
        virtual_output = mido.open_output("test_virtual_output", virtual=True)
        log.info("Successfully created virtual output port")
        virtual_output.close()
        
        return True
        
    except Exception as e:
        log.error(f"Failed to create virtual ports: {e}")
        return False

def test_midi_message(mido, port_name: str):
    """Test sending a MIDI message to an output port."""
    log.info(f"Testing MIDI message send to: {port_name}")
    
    try:
        port = mido.open_output(port_name)
        
        # Send a simple note on/off message
        note_on = mido.Message('note_on', channel=0, note=60, velocity=64)
        port.send(note_on)
        log.info("Sent note on message")
        
        time.sleep(0.1)
        
        note_off = mido.Message('note_off', channel=0, note=60, velocity=0)
        port.send(note_off)
        log.info("Sent note off message")
        
        port.close()
        return True
        
    except Exception as e:
        log.error(f"Failed to send MIDI message: {e}")
        return False

def auto_select_port(ports: list[str], prefer_keywords: list[str]) -> Optional[str]:
    """Auto-select a port based on preferred keywords."""
    if not ports:
        return None
    
    # Look for preferred keywords
    for keyword in prefer_keywords:
        for port in ports:
            if keyword.lower() in port.lower():
                log.info(f"Auto-selected port with keyword '{keyword}': {port}")
                return port
    
    # Fallback to first available port
    log.info(f"No preferred ports found, using first available: {ports[0]}")
    return ports[0]

def main():
    """Main test function."""
    log.info("Starting MIDI connection test for Raspberry Pi")
    
    # Import mido
    mido = safe_import_mido()
    if not mido:
        return False
    
    # List available ports
    input_ports, output_ports = list_midi_ports(mido)
    
    if not input_ports and not output_ports:
        log.error("No MIDI ports found - this indicates a deeper ALSA/system issue")
        return False
    
    # Test virtual ports as baseline
    virtual_success = test_virtual_port(mido)
    if virtual_success:
        log.info("Virtual ports work - ALSA sequencer is functional")
    else:
        log.error("Virtual ports failed - ALSA sequencer may not be working")
    
    # Test input ports
    if input_ports:
        # Try to find Teensy or similar device
        preferred_input = auto_select_port(input_ports, ["teensy", "midi", "usb"])
        if preferred_input:
            input_success = test_port_open(mido, preferred_input, is_input=True)
        else:
            input_success = False
    else:
        log.warning("No input ports available")
        input_success = False
    
    # Test output ports
    if output_ports:
        preferred_output = auto_select_port(output_ports, ["midi", "usb", "synth"])
        if preferred_output:
            output_success = test_port_open(mido, preferred_output, is_input=False)
            
            # If port opens successfully, test sending a message
            if output_success:
                message_success = test_midi_message(mido, preferred_output)
            else:
                message_success = False
        else:
            output_success = False
            message_success = False
    else:
        log.warning("No output ports available")
        output_success = False
        message_success = False
    
    # Summary
    log.info("=== Test Results Summary ===")
    log.info(f"Virtual ports: {'✓' if virtual_success else '✗'}")
    log.info(f"Input ports: {'✓' if input_success else '✗'}")
    log.info(f"Output ports: {'✓' if output_success else '✗'}")
    log.info(f"MIDI messages: {'✓' if message_success else '✗'}")
    
    if not any([input_success, output_success]):
        log.error("All MIDI port tests failed!")
        log.error("Next steps:")
        log.error("  1. Run: python debug_rpi_midi.py")
        log.error("  2. Check ALSA setup: aconnect -l")
        log.error("  3. Load sequencer: sudo modprobe snd-seq")
        log.error("  4. Check user groups: groups")
        return False
    else:
        log.info("Some MIDI functionality is working")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
