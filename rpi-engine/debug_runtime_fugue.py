#!/usr/bin/env python3
"""Debug the actual runtime behavior of fugue mode."""

import sys
import time
sys.path.append('src')

from state import State
from sequencer import Sequencer
from note_utils import format_note_with_number, format_rest

def debug_runtime_fugue():
    """Debug what happens during actual fugue mode execution."""
    
    print("=== Debugging Runtime Fugue Behavior ===\n")
    
    # Set up state for fugue mode
    state = State()
    state.set('direction_pattern', 'fugue')
    state.set('bpm', 80.0)  # Slower BPM to match the logs
    state.set('sequence_length', 8)
    state.set('density', 0.7)
    state.set('root_note', 60)
    state.set('scale_index', 0)
    
    # Create sequencer
    scales = ['minor', 'major', 'dorian', 'mixolydian']
    sequencer = Sequencer(state, scales)
    
    # Set up a note callback to capture notes with detailed logging
    notes_received = []
    
    def note_callback(note_event):
        notes_received.append({
            'note': note_event.note,
            'velocity': note_event.velocity,
            'step': note_event.step,
            'duration': note_event.duration,
            'timestamp': note_event.timestamp
        })
        print(f"♪ Step {note_event.step:2d}: Note {format_note_with_number(note_event.note) if note_event.note != -1 else format_rest()}, Vel {note_event.velocity:3d}, Dur {note_event.duration:.3f}s")
    
    sequencer.set_note_callback(note_callback)
    
    # Check initial state
    print(f"Direction pattern: {state.get('direction_pattern')}")
    print(f"Fugue sequencer exists: {sequencer._fugue_sequencer is not None}")
    
    # Test step generation to see what really happens
    print("\nGenerating steps with debug info...")
    for step in range(20):
        print(f"\n--- Step {step} ---")
        
        # Check direction pattern before generating
        direction = state.get('direction_pattern')
        print(f"Current direction pattern: {direction}")
        
        # Check fugue sequencer state
        if sequencer._fugue_sequencer:
            fugue_active = sequencer._fugue_sequencer._active_fugue is not None
            print(f"Fugue sequencer active: {fugue_active}")
            if fugue_active:
                print(f"Voice positions: {sequencer._fugue_sequencer._voice_positions}")
                print(f"Voice next times: {sequencer._fugue_sequencer._voice_next_times}")
                print(f"Musical time: {sequencer._fugue_sequencer._fugue_musical_time:.2f}")
        else:
            print("No fugue sequencer created yet")
        
        # Generate the step
        sequencer._generate_step_note(step)
        time.sleep(0.1)  # Small delay to simulate real timing
        
        # Check if the direction pattern changed
        new_direction = state.get('direction_pattern')
        if new_direction != direction:
            print(f"DIRECTION CHANGED: {direction} -> {new_direction}")
    
    print(f"\nTotal notes generated: {len(notes_received)}")
    if notes_received:
        steps = [n['step'] for n in notes_received]
        print(f"Steps with notes: {steps}")
        # Check for forward pattern
        is_forward_pattern = all(steps[i] <= steps[i+1] for i in range(len(steps)-1))
        print(f"Forward pattern detected: {is_forward_pattern}")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    debug_runtime_fugue()
