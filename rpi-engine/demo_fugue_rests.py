#!/usr/bin/env python3
"""
Demonstration script showing fugue mode's enhanced rest support.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fugue import FugueEngine, FugueParams, Note
from scale_mapper import ScaleMapper
from state import State
import logging
import random

def demo_rest_variety():
    """Demonstrate variety in rest placement across multiple subjects."""
    print("🎼 Fugue Mode Rest Support Demonstration\n")
    
    class MockScaleMapper:
        def get_note(self, degree, octave=0):
            return 60 + degree + (octave * 12)
    
    scale_mapper = MockScaleMapper()
    
    params = FugueParams(key_root=60, mode="minor")
    
    print("Generating subjects with varied rest patterns:")
    print("=" * 50)
    
    for i in range(5):
        # Create a new engine each time to get different seeds
        engine = FugueEngine(scale_mapper)
        
        subject = engine.generate_subject(params, bars=1)
        
        print(f"\nSubject {i+1}:")
        total_duration = 0
        rest_count = 0
        
        for j, note in enumerate(subject):
            if note['pitch'] is None:
                print(f"  Beat {total_duration + note['dur']/2:.2f}: 🔇 REST (dur={note['dur']:.2f})")
                rest_count += 1
            else:
                print(f"  Beat {total_duration + note['dur']/2:.2f}: 🎵 Note {note['pitch']} (dur={note['dur']:.2f})")
            total_duration += note['dur']
        
        print(f"  → Total duration: {total_duration:.2f} beats, {rest_count} rests")
    
    print("\n" + "=" * 50)
    print("Demonstrating rest preservation in transformations:")
    
    # Create a subject with strategic rests
    test_subject = [
        Note(pitch=60, dur=0.5, vel=96),    # C
        Note(pitch=None, dur=0.5, vel=0),   # REST
        Note(pitch=64, dur=1.0, vel=96),    # E
        Note(pitch=None, dur=0.25, vel=0),  # REST
        Note(pitch=67, dur=1.75, vel=96),   # G
    ]
    
    engine = FugueEngine(scale_mapper)
    
    print(f"\nOriginal Subject:")
    for i, note in enumerate(test_subject):
        if note['pitch'] is None:
            print(f"  {i+1}. 🔇 REST (dur={note['dur']})")
        else:
            print(f"  {i+1}. 🎵 Note {note['pitch']} (dur={note['dur']})")
    
    # Show transposition preserves rests
    transposed = engine.transpose(test_subject, 7)  # Up a perfect 5th
    print(f"\nTransposed (+7 semitones):")
    for i, note in enumerate(transposed):
        if note['pitch'] is None:
            print(f"  {i+1}. 🔇 REST (dur={note['dur']}) [preserved]")
        else:
            print(f"  {i+1}. 🎵 Note {note['pitch']} (dur={note['dur']}) [was {test_subject[i]['pitch']}]")
    
    # Show inversion preserves rests
    inverted = engine.invert(test_subject, 64)  # Around E
    print(f"\nInverted (around E/64):")
    for i, note in enumerate(inverted):
        if note['pitch'] is None:
            print(f"  {i+1}. 🔇 REST (dur={note['dur']}) [preserved]")
        else:
            print(f"  {i+1}. 🎵 Note {note['pitch']} (dur={note['dur']}) [was {test_subject[i]['pitch']}]")
    
    # Show retrograde preserves rests
    retrograde = engine.retrograde(test_subject)
    print(f"\nRetrograde (reversed):")
    for i, note in enumerate(retrograde):
        if note['pitch'] is None:
            print(f"  {i+1}. 🔇 REST (dur={note['dur']}) [preserved]")
        else:
            print(f"  {i+1}. 🎵 Note {note['pitch']} (dur={note['dur']}) [was position {len(test_subject)-i}]")

def demo_musical_benefits():
    """Show the musical benefits of including rests in fugue generation."""
    print(f"\n🎭 Musical Benefits of Rest Support:")
    print("=" * 50)
    
    benefits = [
        "🫁 Breathing spaces for phrasing",
        "🎯 Clearer voice separation in polyphonic texture", 
        "⚡ Dramatic tension through strategic silences",
        "🔄 Rhythmic variety and syncopation",
        "🎼 More authentic Bach-like subjects",
        "🎺 Space for other voices to be heard clearly",
        "🎨 Enhanced musical expression and articulation"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")
    
    print(f"\n📊 Implementation Features:")
    print("=" * 30)
    features = [
        "✅ Rests preserved in all transformations (transpose, invert, retrograde)",
        "✅ Strategic rest placement in subject generation (30% probability)", 
        "✅ Complementary rests in countersubjects",
        "✅ Phrase-boundary rests in episodes",
        "✅ Dramatic rests in cadences",
        "✅ Staggered entries in complex episodes",
        "✅ Proper MIDI handling (None pitch = silence)"
    ]
    
    for feature in features:
        print(f"  {feature}")

if __name__ == "__main__":
    # Disable debug logging for cleaner output
    logging.getLogger('fugue').setLevel(logging.WARNING)
    
    demo_rest_variety()
    demo_musical_benefits()
    
    print(f"\n🎉 Fugue mode now includes comprehensive rest support!")
    print("   Rests are strategically placed to enhance musical expression")
    print("   and create more authentic contrapuntal textures.")
