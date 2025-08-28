#!/usr/bin/env python3
"""
RK006 checker that forces ALSA backend to avoid PortMidi issues.
"""

import os
import sys

# Force mido to use ALSA backend instead of PortMidi
os.environ['MIDO_BACKEND'] = 'mido.backends.rtmidi/LINUX_ALSA'

def check_ports():
    try:
        import mido
        print(f"Using mido backend: {mido.backend}")
        
        print("MIDO INPUT PORTS:")
        try:
            input_ports = mido.get_input_names()
            for i, port in enumerate(input_ports):
                print(f"  {i}: '{port}'")
        except Exception as e:
            print(f"  Error getting input ports: {e}")
            input_ports = []
        
        print("\nMIDO OUTPUT PORTS:")
        try:
            output_ports = mido.get_output_names()
            for i, port in enumerate(output_ports):
                print(f"  {i}: '{port}'")
        except Exception as e:
            print(f"  Error getting output ports: {e}")
            output_ports = []
        
        # Find RK006 ports specifically
        rk006_inputs = [p for p in input_ports if 'RK006' in p or 'rk006' in p.lower()]
        rk006_outputs = [p for p in output_ports if 'RK006' in p or 'rk006' in p.lower()]
        
        print(f"\nRK006 INPUT PORTS: {rk006_inputs}")
        print(f"RK006 OUTPUT PORTS: {rk006_outputs}")
        
        # Check for f_midi ports
        f_midi_inputs = [p for p in input_ports if 'f_midi' in p.lower()]
        f_midi_outputs = [p for p in output_ports if 'f_midi' in p.lower()]
        
        print(f"F_MIDI INPUT PORTS: {f_midi_inputs}")
        print(f"F_MIDI OUTPUT PORTS: {f_midi_outputs}")
        
        # Suggest configuration
        print("\n=== SUGGESTED CONFIGURATION ===")
        
        if rk006_inputs:
            print(f"input_port: \"{rk006_inputs[0]}\"")
        elif f_midi_inputs:
            print(f"input_port: \"{f_midi_inputs[0]}\"")
        else:
            print("input_port: \"auto\"  # No specific devices found")
            
        if rk006_outputs:
            print(f"output_port: \"{rk006_outputs[0]}\"")
        elif f_midi_outputs:
            print(f"output_port: \"{f_midi_outputs[0]}\"")
        else:
            print("output_port: \"auto\"  # No specific devices found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_ports()
