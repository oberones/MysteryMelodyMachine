#!/usr/bin/env python3
"""
Quick MIDI port name checker for RK006 troubleshooting.
"""

def check_ports():
    try:
        import mido
        print("MIDO INPUT PORTS:")
        input_ports = mido.get_input_names()
        for i, port in enumerate(input_ports):
            print(f"  {i}: '{port}'")
        
        print("\nMIDO OUTPUT PORTS:")
        output_ports = mido.get_output_names()
        for i, port in enumerate(output_ports):
            print(f"  {i}: '{port}'")
        
        # Find RK006 ports specifically
        rk006_inputs = [p for p in input_ports if 'RK006' in p]
        rk006_outputs = [p for p in output_ports if 'RK006' in p]
        
        print(f"\nRK006 INPUT PORTS: {rk006_inputs}")
        print(f"RK006 OUTPUT PORTS: {rk006_outputs}")
        
        if rk006_inputs:
            print(f"\nSuggested input_port: \"{rk006_inputs[0]}\"")
        else:
            print("\nNO RK006 INPUT PORTS FOUND!")
            
        if rk006_outputs:
            print(f"Suggested output_port: \"{rk006_outputs[0]}\"")
        else:
            print("NO RK006 OUTPUT PORTS FOUND!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ports()
