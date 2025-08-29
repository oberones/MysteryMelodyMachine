#!/usr/bin/env python3
"""Test the exact main.py note timing logic."""

import time
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sequencer import NoteEvent

class TimingTestOutput:
    """Test MIDI output that records timing."""
    
    def __init__(self):
        self.events = []
    
    def send_note_on(self, note, velocity, channel=1):
        timestamp = time.perf_counter()
        self.events.append(('note_on', timestamp, note, velocity, channel))
        print(f"[{timestamp:.6f}] NOTE ON: {note} vel={velocity}")
        return True
    
    def send_note_off(self, note, velocity=0, channel=1):
        timestamp = time.perf_counter()
        self.events.append(('note_off', timestamp, note, velocity, channel))
        print(f"[{timestamp:.6f}] NOTE OFF: {note} vel={velocity}")
        return True
    
    @property
    def is_connected(self):
        return True

class DummyExternalHardware:
    """Dummy external hardware that delegates to latency optimizer."""
    
    def __init__(self, midi_output):
        self.midi_output = midi_output
        self.scheduled_notes = []
    
    def send_note_on(self, note, velocity, when=None):
        """Send note on immediately."""
        return self.midi_output.send_note_on(note, velocity)
    
    def send_note_off(self, note, when=None):
        """Schedule note off for the specified time."""
        if when is None:
            return self.midi_output.send_note_off(note)
        
        # Schedule for later
        self.scheduled_notes.append((when, note))
        print(f"SCHEDULED note off for {note} at {when:.6f}")
        
        # Use threading to simulate the latency optimizer
        import threading
        def delayed_send():
            sleep_time = when - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.midi_output.send_note_off(note)
        
        thread = threading.Thread(target=delayed_send, daemon=True)
        thread.start()
        return True

def test_main_py_logic():
    """Test the exact logic from main.py handle_note_event."""
    
    print("=== Testing Main.py Note Timing Logic ===\n")
    
    # Create test components
    midi_output = TimingTestOutput()
    external_hardware = DummyExternalHardware(midi_output)
    
    # Simulate a note event from sequencer
    note_event = NoteEvent(
        note=60,
        velocity=100,
        timestamp=time.perf_counter(),
        step=0,
        duration=0.200  # 200ms note
    )
    
    print(f"Note event generated at: {note_event.timestamp:.6f}")
    print(f"Note duration: {note_event.duration:.3f}s")
    print()
    
    # Exact logic from main.py handle_note_event
    print("Executing main.py logic:")
    
    if external_hardware:
        # Send note on immediately with latency optimization
        external_hardware.send_note_on(note_event.note, note_event.velocity)
        
        # Schedule note off after duration
        note_off_time = time.perf_counter() + note_event.duration
        external_hardware.send_note_off(note_event.note, note_off_time)
        
        print(f"Note off scheduled for: {note_off_time:.6f}")
        print(f"Current time: {time.perf_counter():.6f}")
        print(f"Sleep time: {note_off_time - time.perf_counter():.6f}")
    
    # Wait for note to finish
    print("\nWaiting for note to complete...")
    time.sleep(note_event.duration + 0.050)  # Extra 50ms to ensure completion
    
    # Analyze results
    print("\n=== ANALYSIS ===")
    
    note_on_events = [e for e in midi_output.events if e[0] == 'note_on']
    note_off_events = [e for e in midi_output.events if e[0] == 'note_off']
    
    print(f"Note ON events: {len(note_on_events)}")
    print(f"Note OFF events: {len(note_off_events)}")
    
    if note_on_events and note_off_events:
        note_on_time = note_on_events[0][1]
        note_off_time = note_off_events[0][1]
        actual_duration = note_off_time - note_on_time
        
        print(f"Note ON time:  {note_on_time:.6f}")
        print(f"Note OFF time: {note_off_time:.6f}")
        print(f"Actual duration: {actual_duration:.6f}s")
        print(f"Expected duration: {note_event.duration:.6f}s")
        print(f"Timing error: {abs(actual_duration - note_event.duration):.6f}s")
        
        if abs(actual_duration - note_event.duration) < 0.010:  # 10ms tolerance
            print("✅ TIMING IS CORRECT!")
        else:
            print("❌ TIMING IS INCORRECT!")
    else:
        print("❌ Missing note events!")

if __name__ == "__main__":
    test_main_py_logic()
