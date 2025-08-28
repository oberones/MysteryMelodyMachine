#!/usr/bin/env python3
"""
RK006 specific MIDI port detection and configuration helper.
"""

import logging
import sys
import subprocess

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def get_rk006_ports():
    """Get RK006 specific port information from aconnect."""
    try:
        result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            log.error(f"aconnect failed: {result.stderr}")
            return [], []
        
        lines = result.stdout.split('\n')
        rk006_client = None
        input_ports = []
        output_ports = []
        
        # Find RK006 client
        for line in lines:
            if 'RK006' in line and 'client' in line:
                # Extract client number
                parts = line.split(':')
                if len(parts) > 0:
                    client_part = parts[0].strip().replace('client', '').strip()
                    try:
                        rk006_client = int(client_part)
                        log.info(f"Found RK006 at client {rk006_client}")
                    except ValueError:
                        pass
                break
        
        if rk006_client is None:
            log.error("RK006 client not found")
            return [], []
        
        # Parse ports for RK006 client
        in_rk006_section = False
        for line in lines:
            line = line.strip()
            
            if f"client {rk006_client}:" in line:
                in_rk006_section = True
                continue
            elif line.startswith("client ") and in_rk006_section:
                # Moved to next client
                break
            elif in_rk006_section and line and not line.startswith('Connecting'):
                # This is a port line
                if 'IN' in line.upper():
                    input_ports.append(line)
                elif 'OUT' in line.upper():
                    output_ports.append(line)
        
        return input_ports, output_ports
        
    except Exception as e:
        log.error(f"Error parsing aconnect output: {e}")
        return [], []

def test_mido_import():
    """Test mido import and get version info."""
    try:
        import mido
        log.info("✓ mido imported successfully")
        
        # Try to get version
        try:
            version = mido.__version__
            log.info(f"mido version: {version}")
        except AttributeError:
            log.warning("mido version not available (older version?)")
        
        # Test backend
        try:
            backend = mido.backend
            log.info(f"mido backend: {backend}")
        except Exception as e:
            log.warning(f"Could not get mido backend: {e}")
        
        return mido
    except ImportError as e:
        log.error(f"Failed to import mido: {e}")
        return None

def get_mido_ports(mido):
    """Get MIDI ports using mido."""
    try:
        input_names = mido.get_input_names()
        output_names = mido.get_output_names()
        
        log.info(f"Mido found {len(input_names)} input ports:")
        for i, name in enumerate(input_names):
            log.info(f"  {i}: '{name}'")
        
        log.info(f"Mido found {len(output_names)} output ports:")
        for i, name in enumerate(output_names):
            log.info(f"  {i}: '{name}'")
        
        return input_names, output_names
    except Exception as e:
        log.error(f"Error getting mido ports: {e}")
        return [], []

def find_rk006_mido_ports(input_names, output_names):
    """Find RK006 ports in mido port lists."""
    rk006_inputs = [name for name in input_names if 'RK006' in name]
    rk006_outputs = [name for name in output_names if 'RK006' in name]
    
    log.info(f"RK006 input ports in mido: {rk006_inputs}")
    log.info(f"RK006 output ports in mido: {rk006_outputs}")
    
    return rk006_inputs, rk006_outputs

def suggest_config(rk006_inputs, rk006_outputs):
    """Suggest configuration based on available ports."""
    log.info("\n=== SUGGESTED CONFIGURATION ===")
    
    if rk006_inputs:
        suggested_input = rk006_inputs[0]  # Use first available input
        log.info(f"Suggested input_port: \"{suggested_input}\"")
    else:
        log.warning("No RK006 input ports found - you may need to configure the RK006")
        suggested_input = "auto"
        log.info(f"Fallback input_port: \"{suggested_input}\"")
    
    if rk006_outputs:
        suggested_output = rk006_outputs[0]  # Use first available output
        log.info(f"Suggested output_port: \"{suggested_output}\"")
    else:
        log.warning("No RK006 output ports found")
        suggested_output = "auto"
        log.info(f"Fallback output_port: \"{suggested_output}\"")
    
    print(f"\nAdd this to your config.yaml:")
    print(f"midi:")
    print(f"  input_port: \"{suggested_input}\"")
    print(f"  output_port: \"{suggested_output}\"")
    print(f"  input_channel: 11")
    print(f"  output_channel: 1")

def main():
    log.info("RK006 MIDI Configuration Helper")
    log.info("===============================")
    
    # Check ALSA level
    log.info("\n--- ALSA Level Detection ---")
    input_ports, output_ports = get_rk006_ports()
    log.info(f"ALSA RK006 input ports: {input_ports}")
    log.info(f"ALSA RK006 output ports: {output_ports}")
    
    # Check mido level
    log.info("\n--- Mido Level Detection ---")
    mido = test_mido_import()
    if not mido:
        log.error("Cannot continue without mido")
        return 1
    
    input_names, output_names = get_mido_ports(mido)
    rk006_inputs, rk006_outputs = find_rk006_mido_ports(input_names, output_names)
    
    # Suggest configuration
    suggest_config(rk006_inputs, rk006_outputs)
    
    # Additional diagnostic info
    log.info("\n--- Additional Diagnostics ---")
    if not rk006_inputs:
        log.warning("RK006 has no input ports visible to mido")
        log.info("This might indicate:")
        log.info("  - RK006 is configured in output-only mode")
        log.info("  - RK006 firmware needs updating")
        log.info("  - RK006 needs different mode selection")
    
    if not rk006_outputs:
        log.error("RK006 has no output ports - this is unexpected")
        log.info("Try:")
        log.info("  - Unplugging and replugging the RK006")
        log.info("  - Checking RK006 mode settings")
        log.info("  - Power cycling the Raspberry Pi")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
