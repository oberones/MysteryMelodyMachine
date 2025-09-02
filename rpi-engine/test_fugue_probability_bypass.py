#!/usr/bin/env python3
"""
Test script to verify that fugue mode ignores probability controls.

This script demonstrates that when in fugue mode, the sequencer completely
bypasses normal probability controls like density gates, step probabilities,
and step patterns.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from state import State
from sequencer import Sequencer
from scale_mapper import ScaleMapper
import time


def test_probability_bypass():
    """Test that fugue mode ignores probability controls."""
    print("Testing fugue mode probability control bypass...")
    
    # Setup
    state = State()
    scales = ['minor', 'major', 'dorian', 'mixolydian']
    sequencer = Sequencer(state, scales)
    
    # Set up very restrictive probability controls that would block normal generation
    state.set('density', 0.1)  # Very low density (10%)
    state.set('note_probability', 0.05)  # Very low note probability (5%)
    state.set('step_probabilities', [0.0] * 8)  # All steps have 0% probability
    state.set('step_pattern', [False] * 8)  # All steps are disabled
    
    print(f"Set restrictive probability controls:")
    print(f"  density: {state.get('density')}")
    print(f"  note_probability: {state.get('note_probability')}")
    print(f"  step_probabilities: {state.get('step_probabilities')}")
    print(f"  step_pattern: {state.get('step_pattern')}")
    
    # Test normal mode - should be blocked by probability controls
    print(f"\nTesting FORWARD mode (should be blocked by probability controls):")
    sequencer.set_direction_pattern('forward')
    
    notes_generated_forward = 0
    def count_notes_forward(note_event):
        nonlocal notes_generated_forward
        notes_generated_forward += 1
        print(f"  Generated note: {note_event.note} (velocity: {note_event.velocity})")
    
    sequencer.set_note_callback(count_notes_forward)
    
    # Try to generate notes for several steps
    for step in range(16):
        sequencer._generate_step_note(step)
    
    print(f"  Notes generated in forward mode: {notes_generated_forward}")
    
    # Test fugue mode - should ignore probability controls
    print(f"\nTesting FUGUE mode (should ignore probability controls):")
    sequencer.set_direction_pattern('fugue')
    
    notes_generated_fugue = 0
    def count_notes_fugue(note_event):
        nonlocal notes_generated_fugue
        notes_generated_fugue += 1
        print(f"  Generated note: {note_event.note} (velocity: {note_event.velocity})")
    
    sequencer.set_note_callback(count_notes_fugue)
    
    # Try to generate notes for several steps
    for step in range(16):
        sequencer._generate_step_note(step)
    
    print(f"  Notes generated in fugue mode: {notes_generated_fugue}")
    
    # Results analysis
    print(f"\nResults:")
    print(f"  Forward mode (with restrictive controls): {notes_generated_forward} notes")
    print(f"  Fugue mode (ignoring controls): {notes_generated_fugue} notes")
    
    if notes_generated_forward == 0 and notes_generated_fugue > 0:
        print(f"  ✅ SUCCESS: Fugue mode correctly bypassed probability controls!")
    elif notes_generated_forward > 0:
        print(f"  ⚠️  WARNING: Forward mode generated notes despite restrictive controls")
    elif notes_generated_fugue == 0:
        print(f"  ❌ FAILURE: Fugue mode was blocked by probability controls")
    else:
        print(f"  ❓ UNCLEAR: Unexpected result pattern")
    
    # Test switching back to normal mode
    print(f"\nTesting switch back to FORWARD mode:")
    sequencer.set_direction_pattern('forward')
    
    notes_generated_forward_2 = 0
    def count_notes_forward_2(note_event):
        nonlocal notes_generated_forward_2
        notes_generated_forward_2 += 1
        print(f"  Generated note: {note_event.note} (velocity: {note_event.velocity})")
    
    sequencer.set_note_callback(count_notes_forward_2)
    
    # Try to generate notes for several steps
    for step in range(16):
        sequencer._generate_step_note(step)
    
    print(f"  Notes generated in forward mode (after fugue): {notes_generated_forward_2}")
    
    if notes_generated_forward_2 == 0:
        print(f"  ✅ SUCCESS: Probability controls resumed after leaving fugue mode!")
    else:
        print(f"  ❌ FAILURE: Probability controls not working after leaving fugue mode")


if __name__ == "__main__":
    test_probability_bypass()
