#!/usr/bin/env python3
"""
Simple test to check mido installation and capabilities.
"""

def test_mido():
    print("Testing mido installation...")
    print("=" * 40)
    
    # Test import
    try:
        import mido
        print("✓ mido import successful")
    except ImportError as e:
        print(f"✗ mido import failed: {e}")
        return False
    
    # Test version
    try:
        version = mido.__version__
        print(f"✓ mido version: {version}")
    except AttributeError:
        print("⚠ mido version not available (older installation)")
    
    # Test backend
    try:
        backend = mido.backend
        print(f"✓ mido backend: {backend}")
    except Exception as e:
        print(f"⚠ mido backend error: {e}")
    
    # Test port listing
    try:
        input_ports = mido.get_input_names()
        print(f"✓ Found {len(input_ports)} input ports")
        for i, port in enumerate(input_ports):
            print(f"   {i}: {port}")
    except Exception as e:
        print(f"✗ Error getting input ports: {e}")
        return False
    
    try:
        output_ports = mido.get_output_names()
        print(f"✓ Found {len(output_ports)} output ports")
        for i, port in enumerate(output_ports):
            print(f"   {i}: {port}")
    except Exception as e:
        print(f"✗ Error getting output ports: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("mido appears to be working!")
    
    # Look for specific devices
    rk006_inputs = [p for p in input_ports if 'RK006' in p]
    rk006_outputs = [p for p in output_ports if 'RK006' in p]
    f_midi_inputs = [p for p in input_ports if 'f_midi' in p]
    f_midi_outputs = [p for p in output_ports if 'f_midi' in p]
    
    print(f"\nDevice-specific ports:")
    print(f"RK006 inputs: {rk006_inputs}")
    print(f"RK006 outputs: {rk006_outputs}")
    print(f"f_midi inputs: {f_midi_inputs}")
    print(f"f_midi outputs: {f_midi_outputs}")
    
    return True

if __name__ == "__main__":
    success = test_mido()
    if not success:
        print("\nSuggested fixes:")
        print("1. Install missing dependencies:")
        print("   sudo apt-get install libportmidi-dev portaudio19-dev libasound2-dev")
        print("2. Reinstall python packages:")
        print("   pip uninstall python-rtmidi mido")
        print("   pip install python-rtmidi mido")
        print("3. Try the ALSA-specific version:")
        print("   python quick_rk006_check_alsa.py")
