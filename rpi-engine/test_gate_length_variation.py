#!/usr/bin/env python3
"""
Test script to verify gate length variation functionality.
This demonstrates the new gate length variation feature working alongside velocity variation.
"""

import sys
import os
import time
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from state import State
from sequencer import Sequencer, NoteEvent

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)


def test_gate_length_variation():
    """Test that gate length varies per step based on probability."""
    print("\n=== Gate Length Variation Test ===")
    
    # Create state and sequencer
    state = State()
    scales = ['major', 'minor', 'pentatonic']
    sequencer = Sequencer(state, scales)
    
    # Set up gate length parameters with variation
    sequencer.set_gate_length_params(base_gate_length=0.7, gate_length_range=0.4)
    
    # Set up velocity parameters for comparison
    sequencer.set_velocity_params(base_velocity=80, velocity_range=30)
    
    # Set up step probabilities with different values to see variation
    sequencer.set_step_probabilities([0.2, 0.5, 0.8, 0.3, 0.9, 0.4, 0.7, 0.6])
    
    # Set up a simple pattern
    sequencer.set_step_pattern([True, True, True, True, True, True, True, True])
    
    # Collect note events
    note_events = []
    
    def note_callback(note_event: NoteEvent):
        note_events.append(note_event)
        print(f"Step {note_event.step}: Note={note_event.note}, "
              f"Velocity={note_event.velocity}, "
              f"Gate Length={note_event.duration:.3f}s")
    
    sequencer.set_note_callback(note_callback)
    
    # Configure sequencer parameters
    state.set('bpm', 120.0, source='test')
    state.set('sequence_length', 8, source='test')
    state.set('density', 1.0, source='test')  # Ensure all notes play
    
    print(f"\nBase gate length: {state.get('base_gate_length', 0.8)}")
    print(f"Gate length range: {state.get('gate_length_range', 0.3)}")
    print(f"Base velocity: {state.get('base_velocity', 80)}")
    print(f"Velocity range: {state.get('velocity_range', 40)}")
    print("\nGenerating notes for one full sequence...")
    
    # Generate notes for each step manually
    for step in range(8):
        state.set('step_position', step, source='test')
        sequencer._generate_step_note(step)
    
    print(f"\nGenerated {len(note_events)} notes")
    
    if note_events:
        # Analyze gate length variation
        gate_lengths = [event.duration for event in note_events]
        velocities = [event.velocity for event in note_events]
        
        print(f"\nGate Length Analysis:")
        print(f"  Min gate length: {min(gate_lengths):.3f}s")
        print(f"  Max gate length: {max(gate_lengths):.3f}s")
        print(f"  Average gate length: {sum(gate_lengths)/len(gate_lengths):.3f}s")
        print(f"  Gate length range: {max(gate_lengths) - min(gate_lengths):.3f}s")
        
        print(f"\nVelocity Analysis:")
        print(f"  Min velocity: {min(velocities)}")
        print(f"  Max velocity: {max(velocities)}")
        print(f"  Average velocity: {sum(velocities)/len(velocities):.1f}")
        
        # Verify gate lengths are different (showing variation)
        unique_gate_lengths = len(set(f"{gl:.3f}" for gl in gate_lengths))
        print(f"\nUnique gate lengths: {unique_gate_lengths} out of {len(gate_lengths)} notes")
        
        if unique_gate_lengths > 1:
            print("✓ Gate length variation is working!")
        else:
            print("⚠ No gate length variation detected")
        
        # Verify velocities are different (showing variation)
        unique_velocities = len(set(velocities))
        print(f"Unique velocities: {unique_velocities} out of {len(velocities)} notes")
        
        if unique_velocities > 1:
            print("✓ Velocity variation is working!")
        else:
            print("⚠ No velocity variation detected")
    else:
        print("⚠ No notes were generated")


def test_gate_length_bounds():
    """Test that gate length stays within valid bounds."""
    print("\n=== Gate Length Bounds Test ===")
    
    state = State()
    scales = ['major']
    sequencer = Sequencer(state, scales)
    
    # Test extreme parameters
    sequencer.set_gate_length_params(base_gate_length=0.1, gate_length_range=0.9)
    
    note_events = []
    
    def note_callback(note_event: NoteEvent):
        note_events.append(note_event)
    
    sequencer.set_note_callback(note_callback)
    
    # Configure for testing
    state.set('bpm', 120.0, source='test')
    state.set('density', 1.0, source='test')
    
    # Generate many notes to test bounds
    for step in range(50):
        sequencer._generate_step_note(step % 8)
    
    if note_events:
        gate_lengths = [event.duration for event in note_events]
        step_duration = 60.0 / (120.0 * 4)  # 16th note at 120 BPM
        
        print(f"Step duration: {step_duration:.3f}s")
        print(f"Generated {len(gate_lengths)} notes")
        print(f"Gate lengths range: {min(gate_lengths):.3f}s to {max(gate_lengths):.3f}s")
        
        # Check bounds (gate length should never exceed step duration)
        max_valid_gate = step_duration
        invalid_gates = [gl for gl in gate_lengths if gl > max_valid_gate or gl <= 0]
        
        if not invalid_gates:
            print("✓ All gate lengths are within valid bounds")
        else:
            print(f"⚠ Found {len(invalid_gates)} invalid gate lengths")
    else:
        print("⚠ No notes were generated")


if __name__ == '__main__':
    test_gate_length_variation()
    test_gate_length_bounds()
    print("\n=== Tests completed ===")
