#!/usr/bin/env python3
"""Quick test of fugue mode in the main system."""

import sys
import time
sys.path.append('src')

from state import State
from sequencer import Sequencer

def test_fugue_main_system():
    """Test fugue mode integration with the main sequencer."""
    
    print("=== Testing Fugue Mode in Main System ===\n")
    
    # Set up state for fugue mode
    state = State()
    state.set('direction_pattern', 'fugue')
    state.set('bpm', 120.0)
    state.set('sequence_length', 8)
    state.set('density', 0.7)
    state.set('root_note', 60)
    state.set('scale_index', 0)
    
    # Create sequencer
    scales = ['minor', 'major', 'dorian', 'mixolydian']
    sequencer = Sequencer(state, scales)
    
    # Set up a note callback to capture notes
    notes_received = []
    
    def note_callback(note_event):
        notes_received.append({
            'note': note_event.note,
            'velocity': note_event.velocity,
            'step': note_event.step,
            'duration': note_event.duration
        })
        print(f"♪ Step {note_event.step:2d}: Note {note_event.note:3d}, Vel {note_event.velocity:3d}, Dur {note_event.duration:.3f}s")
    
    sequencer.set_note_callback(note_callback)
    
    # Test direct step generation (simulating what happens in the main loop)
    print("Testing direct step generation...")
    for step in range(15):
        sequencer._generate_step_note(step)
        time.sleep(0.01)  # Small delay
    
    print(f"\nTotal notes generated: {len(notes_received)}")
    if notes_received:
        notes = [n['note'] for n in notes_received]
        print(f"Note range: {min(notes)} - {max(notes)} (span: {max(notes) - min(notes)} semitones)")
        print(f"Steps with notes: {[n['step'] for n in notes_received]}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_fugue_main_system()
