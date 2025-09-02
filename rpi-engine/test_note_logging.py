#!/usr/bin/env python3
"""
Test script to verify enhanced note logging functionality.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from note_utils import note_to_name, format_note_with_number, format_rest

def test_note_utils():
    """Test the note utility functions."""
    print("=== Testing Note Utility Functions ===\n")
    
    # Test common MIDI notes
    test_notes = [
        60,  # C4
        69,  # A4 
        61,  # C#4
        70,  # A#4
        48,  # C3
        72,  # C5
        -1,  # Rest (should be handled by format functions)
    ]
    
    print("Note name conversions:")
    for note in test_notes:
        if note == -1:
            print(f"  Rest: {format_rest()}")
        else:
            name = note_to_name(note)
            formatted = format_note_with_number(note)
            print(f"  MIDI {note:3d}: {name:4s} -> {formatted}")
    
    print("\nButton mapping (60-69):")
    for note in range(60, 70):
        formatted = format_note_with_number(note)
        print(f"  Button {note-59}: {formatted}")
    
    print("\nScale examples:")
    # Common scale roots
    roots = [60, 62, 64, 65, 67, 69, 71]  # C, D, E, F, G, A, B
    for root in roots:
        formatted = format_note_with_number(root)
        print(f"  {formatted} major scale")

if __name__ == "__main__":
    test_note_utils()
