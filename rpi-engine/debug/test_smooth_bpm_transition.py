#!/usr/bin/env python3
"""
Test script to verify smooth BPM transition functionality.
This demonstrates the new BPM transition feature for idle mode.
"""

import sys
import os
import time
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from state import State
from sequencer import Sequencer

# Configure logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)


def test_smooth_bpm_transition():
    """Test that BPM transitions smoothly from one value to another."""
    print("\n=== Smooth BPM Transition Test ===")
    
    # Create state and sequencer
    state = State()
    scales = ['major']
    sequencer = Sequencer(state, scales)
    
    # Configure transition settings
    state.set('smooth_idle_transitions', True, source='test')
    state.set('idle_transition_duration_s', 2.0, source='test')  # Short duration for testing
    
    # Set initial BPM
    initial_bpm = 120.0
    state.set('bpm', initial_bpm, source='test')
    
    print(f"Initial BPM: {initial_bpm}")
    print(f"Smooth transitions enabled: {state.get('smooth_idle_transitions')}")
    print(f"Transition duration: {state.get('idle_transition_duration_s')}s")
    
    # Start the sequencer to activate the clock
    sequencer.start()
    
    try:
        # Wait a moment for initial setup
        time.sleep(0.5)
        
        # Simulate idle mode BPM change
        target_bpm = 60.0
        print(f"\n🔄 Starting transition from {initial_bpm} BPM to {target_bpm} BPM...")
        
        # This simulates what the idle manager does
        state.set('bpm', target_bpm, source='idle')
        
        # Monitor the transition
        transition_duration = 2.5  # Slightly longer than our configured duration
        start_time = time.time()
        samples = []
        
        while time.time() - start_time < transition_duration:
            current_bpm = sequencer.clock.bpm  # Get actual clock BPM
            elapsed = time.time() - start_time
            samples.append((elapsed, current_bpm))
            
            print(f"  Time: {elapsed:.2f}s, BPM: {current_bpm:.1f}")
            time.sleep(0.2)  # Sample every 200ms
        
        # Check final BPM
        final_bpm = sequencer.clock.bpm
        print(f"\n✅ Transition complete. Final BPM: {final_bpm:.1f}")
        
        # Verify we reached the target
        if abs(final_bpm - target_bpm) < 1.0:
            print("✅ Successfully reached target BPM")
        else:
            print(f"⚠️  Did not reach target BPM (expected {target_bpm}, got {final_bpm})")
        
        # Verify the transition was smooth (BPM should increase steadily)
        if len(samples) >= 3:
            bpm_changes = []
            for i in range(1, len(samples)):
                prev_bpm = samples[i-1][1]
                curr_bpm = samples[i][1]
                bpm_changes.append(curr_bpm - prev_bpm)
            
            # Check if transition was monotonic (always moving toward target)
            if target_bpm < initial_bpm:
                # Should be decreasing
                decreasing = all(change <= 2.0 for change in bpm_changes)  # Allow small noise
                if decreasing:
                    print("✅ BPM decreased smoothly")
                else:
                    print("⚠️  BPM transition was not smooth")
            else:
                # Should be increasing
                increasing = all(change >= -2.0 for change in bpm_changes)
                if increasing:
                    print("✅ BPM increased smoothly")
                else:
                    print("⚠️  BPM transition was not smooth")
    
    finally:
        sequencer.stop()


def test_immediate_bpm_change():
    """Test that non-idle BPM changes are immediate (no transition)."""
    print("\n=== Immediate BPM Change Test ===")
    
    # Create state and sequencer
    state = State()
    scales = ['major']
    sequencer = Sequencer(state, scales)
    
    # Configure transition settings (enabled)
    state.set('smooth_idle_transitions', True, source='test')
    state.set('idle_transition_duration_s', 2.0, source='test')
    
    # Set initial BPM
    initial_bpm = 100.0
    state.set('bpm', initial_bpm, source='test')
    
    sequencer.start()
    
    try:
        time.sleep(0.5)  # Let it settle
        
        # Simulate MIDI BPM change (should be immediate)
        target_bpm = 140.0
        print(f"🎹 MIDI BPM change from {initial_bpm} to {target_bpm} (should be immediate)")
        
        state.set('bpm', target_bpm, source='midi')
        
        # Check immediately
        time.sleep(0.1)
        current_bpm = sequencer.clock.bpm
        
        print(f"Current BPM after 0.1s: {current_bpm:.1f}")
        
        if abs(current_bpm - target_bpm) < 1.0:
            print("✅ MIDI BPM change was immediate")
        else:
            print(f"⚠️  MIDI BPM change was not immediate (expected {target_bpm}, got {current_bpm})")
    
    finally:
        sequencer.stop()


def test_transition_cancellation():
    """Test that ongoing transitions are cancelled by immediate changes."""
    print("\n=== Transition Cancellation Test ===")
    
    # Create state and sequencer
    state = State()
    scales = ['major']
    sequencer = Sequencer(state, scales)
    
    # Configure transition settings
    state.set('smooth_idle_transitions', True, source='test')
    state.set('idle_transition_duration_s', 3.0, source='test')  # Longer duration
    
    # Set initial BPM
    initial_bpm = 80.0
    state.set('bpm', initial_bpm, source='test')
    
    sequencer.start()
    
    try:
        time.sleep(0.5)
        
        # Start a long transition
        target_bpm_1 = 150.0
        print(f"🔄 Starting transition from {initial_bpm} to {target_bpm_1}...")
        state.set('bpm', target_bpm_1, source='idle')
        
        # Let it transition for a bit
        time.sleep(1.0)
        mid_transition_bpm = sequencer.clock.bpm
        print(f"Mid-transition BPM: {mid_transition_bpm:.1f}")
        
        # Interrupt with MIDI change
        target_bpm_2 = 110.0
        print(f"🎹 Interrupting with MIDI change to {target_bpm_2}")
        state.set('bpm', target_bpm_2, source='midi')
        
        # Check that it's immediately at the new value
        time.sleep(0.1)
        final_bpm = sequencer.clock.bpm
        print(f"Final BPM after interruption: {final_bpm:.1f}")
        
        if abs(final_bpm - target_bpm_2) < 1.0:
            print("✅ Transition was successfully cancelled by MIDI change")
        else:
            print(f"⚠️  Transition cancellation failed (expected {target_bpm_2}, got {final_bpm})")
    
    finally:
        sequencer.stop()


if __name__ == '__main__':
    test_smooth_bpm_transition()
    test_immediate_bpm_change()
    test_transition_cancellation()
    print("\n=== BPM Transition Tests Completed ===")
