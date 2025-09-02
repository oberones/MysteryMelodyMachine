#!/usr/bin/env python3
"""Test fugue mode for a longer duration to see cycling behavior."""

import sys
import time
sys.path.append('src')

from state import State
from sequencer import Sequencer

def test_long_fugue_cycling():
    """Test fugue mode for multiple cycles."""
    
    print("=== Testing Long-Duration Fugue Cycling ===\n")
    
    # Set up state for fugue mode
    state = State()
    state.set('direction_pattern', 'fugue')
    state.set('bpm', 120.0)  # Faster BPM for quicker cycling
    state.set('sequence_length', 8)
    state.set('density', 0.7)
    state.set('root_note', 60)
    state.set('scale_index', 0)
    
    # Create sequencer
    scales = ['minor', 'major', 'dorian', 'mixolydian']
    sequencer = Sequencer(state, scales)
    
    # Set up a note callback
    notes_received = []
    fugue_cycles = []
    current_cycle_notes = []
    
    def note_callback(note_event):
        notes_received.append({
            'note': note_event.note,
            'velocity': note_event.velocity,
            'step': note_event.step,
            'duration': note_event.duration,
            'timestamp': note_event.timestamp
        })
        current_cycle_notes.append(note_event.step)
        print(f"♪ Step {note_event.step:2d}: Note {note_event.note:3d}")
    
    sequencer.set_note_callback(note_callback)
    
    print("Running fugue mode for extended period...")
    
    # Run for many steps to potentially trigger a new fugue cycle
    for step in range(100):  # Much longer test
        prev_active = sequencer._fugue_sequencer._active_fugue is not None if sequencer._fugue_sequencer else False
        
        sequencer._generate_step_note(step)
        
        # Check if fugue cycled (active -> inactive -> active)
        if sequencer._fugue_sequencer:
            current_active = sequencer._fugue_sequencer._active_fugue is not None
            if prev_active and not current_active:
                # Fugue just ended
                print(f"\n--- FUGUE CYCLE ENDED at step {step} ---")
                print(f"Notes in this cycle: {len(current_cycle_notes)}")
                print(f"Steps: {current_cycle_notes}")
                fugue_cycles.append(current_cycle_notes.copy())
                current_cycle_notes.clear()
            elif not prev_active and current_active:
                # New fugue started
                print(f"\n--- NEW FUGUE CYCLE STARTED at step {step} ---")
        
        time.sleep(0.02)  # Small delay
        
        # Stop if we've seen multiple cycles
        if len(fugue_cycles) >= 2:
            print(f"\nStopping after {len(fugue_cycles)} complete cycles")
            break
    
    # Final cycle if still active
    if current_cycle_notes:
        fugue_cycles.append(current_cycle_notes)
    
    print(f"\n=== Results ===")
    print(f"Total notes generated: {len(notes_received)}")
    print(f"Number of fugue cycles: {len(fugue_cycles)}")
    
    for i, cycle in enumerate(fugue_cycles):
        print(f"Cycle {i+1}: {len(cycle)} notes at steps {cycle[:10]}{'...' if len(cycle) > 10 else ''}")
        
        # Check if any cycle shows forward pattern
        if len(cycle) > 5:
            is_forward = all(cycle[j] <= cycle[j+1] for j in range(len(cycle)-1))
            print(f"  Forward pattern: {is_forward}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_long_fugue_cycling()
