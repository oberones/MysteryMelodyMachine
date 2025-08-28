#!/usr/bin/env python3
"""
Main engine with forced ALSA backend for Raspberry Pi PortMidi issues.
"""

import os
import sys

# Force ALSA backend before importing mido
os.environ['MIDO_BACKEND'] = 'mido.backends.rtmidi/LINUX_ALSA'

# Now import the main function from the original main script
sys.path.insert(0, '/Users/oberon/Projects/coding/other/MysteryMelodyMachine/rpi-engine/src')

def main_with_alsa():
    """Main function with ALSA backend forced."""
    print("Mystery Music Engine - ALSA Backend Mode")
    print("=" * 40)
    
    try:
        import mido
        print(f"Using mido backend: {mido.backend}")
    except Exception as e:
        print(f"Error with mido: {e}")
        return 1
    
    # Import and run the original main
    try:
        from main import main
        return main()
    except ImportError:
        print("Could not import main function")
        return 1
    except Exception as e:
        print(f"Error running main: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_with_alsa())
