#!/usr/bin/env python3
"""
Simple test to verify smooth BPM transition functionality.
"""

import sys
import os
import time
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from state import State
from sequencer import Sequencer

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def main():
    print("=== Testing Smooth BPM Transitions ===")
    
    # Create state and sequencer
    state = State()
    sequencer = Sequencer(state, ['major'])
    
    # Configure transition settings
    state.set('smooth_idle_transitions', True, source='test')
    state.set('idle_transition_duration_s', 2.0, source='test')
    
    # Set initial BPM
    state.set('bpm', 120.0, source='test')
    sequencer.start()
    
    try:
        print(f"Initial BPM: {sequencer.clock.bpm}")
        time.sleep(0.5)
        
        # Trigger smooth transition (like idle mode would)
        print("Triggering smooth transition to 60 BPM...")
        state.set('bpm', 60.0, source='idle')
        
        # Monitor transition progress
        for i in range(10):
            current_bpm = sequencer.clock.bpm
            print(f"  t={i*0.3:.1f}s: {current_bpm:.1f} BPM")
            time.sleep(0.3)
        
        print("Transition complete!")
        
        # Test immediate change
        print("\nTesting immediate MIDI change...")
        state.set('bpm', 100.0, source='midi')
        time.sleep(0.1)
        print(f"Immediate BPM: {sequencer.clock.bpm}")
        
    finally:
        sequencer.stop()
    
    print("✅ Test completed")


if __name__ == '__main__':
    main()
