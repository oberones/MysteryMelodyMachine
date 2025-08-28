#!/usr/bin/env python3
"""
MIDI test that tries multiple approaches to work around Raspberry Pi issues.
"""

import sys
import os

def try_method_1_direct():
    """Try importing mido directly."""
    print("Method 1: Direct mido import")
    try:
        import mido
        print("✓ Direct import successful")
        
        input_ports = mido.get_input_names()
        output_ports = mido.get_output_names()
        
        print(f"  Input ports: {input_ports}")
        print(f"  Output ports: {output_ports}")
        
        return True, input_ports, output_ports
    except Exception as e:
        print(f"✗ Direct import failed: {e}")
        return False, [], []

def try_method_2_alsa_backend():
    """Try forcing ALSA backend."""
    print("\nMethod 2: Force ALSA backend")
    try:
        os.environ['MIDO_BACKEND'] = 'mido.backends.rtmidi/LINUX_ALSA'
        
        # Clear any cached imports
        if 'mido' in sys.modules:
            del sys.modules['mido']
        if 'mido.backends' in sys.modules:
            del sys.modules['mido.backends']
        
        import mido
        print(f"✓ ALSA backend import successful: {mido.backend}")
        
        input_ports = mido.get_input_names()
        output_ports = mido.get_output_names()
        
        print(f"  Input ports: {input_ports}")
        print(f"  Output ports: {output_ports}")
        
        return True, input_ports, output_ports
    except Exception as e:
        print(f"✗ ALSA backend failed: {e}")
        return False, [], []

def try_method_3_subprocess():
    """Try using aconnect directly via subprocess."""
    print("\nMethod 3: Direct ALSA via aconnect")
    try:
        import subprocess
        result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ aconnect successful")
            lines = result.stdout.strip().split('\n')
            
            # Parse for RK006 and f_midi
            rk006_ports = []
            f_midi_ports = []
            
            for line in lines:
                if 'RK006' in line and ('IN' in line or 'OUT' in line):
                    rk006_ports.append(line.strip())
                elif 'f_midi' in line:
                    f_midi_ports.append(line.strip())
            
            print(f"  RK006 ports: {rk006_ports}")
            print(f"  f_midi ports: {f_midi_ports}")
            
            return True, f_midi_ports, rk006_ports
        else:
            print(f"✗ aconnect failed: {result.stderr}")
            return False, [], []
    except Exception as e:
        print(f"✗ aconnect method failed: {e}")
        return False, [], []

def analyze_results(results):
    """Analyze results and provide recommendations."""
    print("\n" + "=" * 50)
    print("ANALYSIS AND RECOMMENDATIONS")
    print("=" * 50)
    
    working_methods = [method for method, success, _, _ in results if success]
    
    if not working_methods:
        print("❌ NO METHODS WORKED")
        print("\nTroubleshooting steps:")
        print("1. Install system dependencies:")
        print("   sudo apt-get update")
        print("   sudo apt-get install libportmidi-dev portaudio19-dev libasound2-dev alsa-utils")
        print("2. Reinstall Python packages:")
        print("   pip uninstall python-rtmidi mido")
        print("   pip install python-rtmidi mido")
        print("3. Load ALSA sequencer:")
        print("   sudo modprobe snd-seq")
        return
    
    print(f"✅ {len(working_methods)} method(s) worked")
    
    # Find available ports across all methods
    all_inputs = set()
    all_outputs = set()
    
    for method, success, inputs, outputs in results:
        if success:
            all_inputs.update(inputs)
            all_outputs.update(outputs)
    
    print(f"\nAvailable input ports: {list(all_inputs)}")
    print(f"Available output ports: {list(all_outputs)}")
    
    # Suggest configuration
    rk006_inputs = [p for p in all_inputs if 'RK006' in str(p)]
    rk006_outputs = [p for p in all_outputs if 'RK006' in str(p)]
    f_midi_inputs = [p for p in all_inputs if 'f_midi' in str(p)]
    f_midi_outputs = [p for p in all_outputs if 'f_midi' in str(p)]
    
    print(f"\nDevice-specific ports:")
    print(f"RK006 inputs: {rk006_inputs}")
    print(f"RK006 outputs: {rk006_outputs}")
    print(f"f_midi inputs: {f_midi_inputs}")
    print(f"f_midi outputs: {f_midi_outputs}")
    
    print(f"\nSUGGESTED CONFIG.YAML:")
    print("midi:")
    
    if rk006_inputs:
        print(f'  input_port: "{rk006_inputs[0]}"')
    elif f_midi_inputs:
        print(f'  input_port: "{f_midi_inputs[0]}"')
    else:
        print('  input_port: "auto"')
    
    if rk006_outputs:
        print(f'  output_port: "{rk006_outputs[0]}"')
    elif f_midi_outputs:
        print(f'  output_port: "{f_midi_outputs[0]}"')
    else:
        print('  output_port: "auto"')
    
    # Recommend which method to use
    if "Method 1: Direct mido import" in working_methods:
        print(f"\nRECOMMENDED: Use standard engine (Method 1 works)")
        print("python src/main.py --config config.yaml")
    elif "Method 2: Force ALSA backend" in working_methods:
        print(f"\nRECOMMENDED: Use ALSA backend version")
        print("python main_alsa.py --config config.yaml")
    else:
        print(f"\nRECOMMENDED: ALSA-only approach, may need custom integration")

def main():
    print("Multi-Method MIDI Test for Raspberry Pi")
    print("=" * 50)
    
    results = []
    
    # Try each method
    success1, inputs1, outputs1 = try_method_1_direct()
    results.append(("Method 1: Direct mido import", success1, inputs1, outputs1))
    
    success2, inputs2, outputs2 = try_method_2_alsa_backend()
    results.append(("Method 2: Force ALSA backend", success2, inputs2, outputs2))
    
    success3, inputs3, outputs3 = try_method_3_subprocess()
    results.append(("Method 3: Direct ALSA via aconnect", success3, inputs3, outputs3))
    
    # Analyze and provide recommendations
    analyze_results(results)

if __name__ == "__main__":
    main()
