#!/usr/bin/env python3
"""
Quick integration test for smooth BPM transitions with the idle system.
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from state import get_state
from sequencer import create_sequencer
from idle import create_idle_manager
from config import IdleConfig


def main():
    print("=== Idle Mode Smooth BPM Transition Test ===")
    
    # Get global state
    state = get_state()
    
    # Configure for testing
    state.update_multiple({
        'bpm': 120.0,
        'density': 0.8,
        'sequence_length': 8,
        'smooth_idle_transitions': True,
        'idle_transition_duration_s': 3.0,  # 3 second transition
    }, source='test')
    
    # Create sequencer
    sequencer = create_sequencer(state, ['major'])
    
    # Create idle manager with short timeout
    idle_config = IdleConfig(
        timeout_ms=2000,  # 2 second timeout for quick testing
        ambient_profile="slow_fade",
        fade_in_ms=1000,
        fade_out_ms=500,
        smooth_bpm_transitions=True,
        bpm_transition_duration_s=3.0
    )
    idle_manager = create_idle_manager(idle_config, state)
    
    sequencer.start()
    idle_manager.start()
    
    try:
        print(f"Initial BPM: {sequencer.clock.bpm}")
        print("Waiting for automatic idle mode entry (2 seconds)...")
        
        # Wait for idle mode to trigger
        for i in range(8):
            time.sleep(0.5)
            current_bpm = sequencer.clock.bpm
            is_idle = idle_manager.is_idle
            print(f"  t={i*0.5:.1f}s: BPM={current_bpm:.1f}, Idle={is_idle}")
        
        print("\nSimulating user interaction to exit idle...")
        idle_manager.touch()
        
        # Monitor exit transition
        for i in range(8):
            time.sleep(0.5)
            current_bpm = sequencer.clock.bpm
            is_idle = idle_manager.is_idle
            print(f"  exit t={i*0.5:.1f}s: BPM={current_bpm:.1f}, Idle={is_idle}")
        
    finally:
        idle_manager.stop()
        sequencer.stop()
    
    print("✅ Integration test completed")


if __name__ == '__main__':
    main()
