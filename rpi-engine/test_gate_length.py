#!/usr/bin/env python3
"""Test gate_length configuration and dynamic changes."""

import sys
import time
sys.path.append('src')

from config import load_config
from state import get_state, reset_state

def test_gate_length_config():
    """Test that gate_length is loaded from config and can be changed."""
    print("=== Gate Length Configuration Test ===")
    
    # Reset state
    reset_state()
    
    # Load config
    config = load_config("config.yaml")
    print(f"Config gate_length: {config.sequencer.gate_length}")
    
    # Initialize state
    state = get_state()
    state.set('gate_length', config.sequencer.gate_length, source='config')
    state.set('bpm', config.sequencer.bpm, source='config')
    
    # Test current settings
    gate_length = state.get('gate_length')
    bpm = state.get('bpm')
    print(f"State gate_length: {gate_length}")
    print(f"State BPM: {bpm}")
    
    # Calculate step duration and note duration
    steps_per_beat = 4  # Standard sequencer setting
    step_duration = 60.0 / (bpm * steps_per_beat)
    note_duration = step_duration * gate_length
    
    print(f"Step duration: {step_duration:.3f}s")
    print(f"Note duration: {note_duration:.3f}s (at gate_length={gate_length})")
    
    # Test changing gate_length
    print("\n--- Testing Gate Length Changes ---")
    test_values = [0.1, 0.5, 0.8, 1.0]
    
    for test_gate_length in test_values:
        state.set('gate_length', test_gate_length, source='test')
        current_gate = state.get('gate_length')
        test_note_duration = step_duration * current_gate
        print(f"Gate length {test_gate_length} -> Note duration: {test_note_duration:.3f}s")
    
    print("\n--- Testing MIDI CC Mapping ---")
    # Test CC value mapping (0-127 -> 0.1-1.0)
    cc_values = [0, 32, 64, 96, 127]
    for cc_val in cc_values:
        mapped_gate = 0.1 + (cc_val / 127.0) * 0.9
        test_note_duration = step_duration * mapped_gate
        print(f"CC {cc_val:3d} -> gate_length {mapped_gate:.2f} -> Note duration: {test_note_duration:.3f}s")
    
    print("\nGate length configuration test completed successfully!")

if __name__ == "__main__":
    test_gate_length_config()
