#!/usr/bin/env python3
"""
Integration test for root_note parameter functionality.
Tests that root_note can be set via config, state, and mutations.
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from state import get_state, reset_state
from sequencer import create_sequencer
from scale_mapper import ScaleMapper
from mutation import create_mutation_engine, MutationRule


def test_config_integration():
    """Test that root_note is loaded from config."""
    print("Testing config integration...")
    
    # Load the config
    config = load_config("config.yaml")
    print(f"Config root_note: {config.sequencer.root_note}")
    
    # Check it matches our expectation
    assert config.sequencer.root_note == 60, f"Expected 60, got {config.sequencer.root_note}"
    print("✓ Config integration works")


def test_state_integration():
    """Test that root_note can be set and retrieved from state."""
    print("\nTesting state integration...")
    
    reset_state()
    state = get_state()
    
    # Check default value
    default_root = state.get('root_note')
    print(f"Default root_note: {default_root}")
    assert default_root == 60, f"Expected 60, got {default_root}"
    
    # Test setting valid values
    assert state.set('root_note', 72) is True  # C5
    assert state.get('root_note') == 72
    
    # Test clamping
    assert state.set('root_note', -10) is True  # Below min
    assert state.get('root_note') == 0
    
    assert state.set('root_note', 150) is True  # Above max
    assert state.get('root_note') == 127
    
    print("✓ State integration works")


def test_scale_mapper_integration():
    """Test that scale mapper uses root_note from state."""
    print("\nTesting scale mapper integration...")
    
    reset_state()
    state = get_state()
    
    # Create a scale mapper
    mapper = ScaleMapper()
    
    # Test different root notes
    for root_note in [60, 72, 48]:  # C4, C5, C3
        state.set('root_note', root_note)
        mapper.set_scale("major", root_note=root_note)
        
        # Test that the mapper uses the correct root
        assert mapper.root_note == root_note
        
        # Test note generation
        root_note_result = mapper.get_note(0)  # Root note (degree 0)
        assert root_note_result == root_note, f"Expected {root_note}, got {root_note_result}"
        
        print(f"✓ Root note {root_note} works correctly")
    
    print("✓ Scale mapper integration works")


def test_sequencer_integration():
    """Test that sequencer respects root_note changes."""
    print("\nTesting sequencer integration...")
    
    reset_state()
    state = get_state()
    scales = ["major", "minor", "pentatonic_major"]
    
    # Create sequencer
    sequencer = create_sequencer(state, scales)
    
    # Test that root_note changes are reflected in scale_mapper
    initial_root = sequencer.scale_mapper.root_note
    print(f"Initial sequencer root_note: {initial_root}")
    
    # Change root note in state
    state.set('root_note', 67)  # G4
    
    # The sequencer should pick this up when the scale is updated
    # Since we're testing without actually starting the sequencer,
    # we'll force the update by calling the private method
    sequencer._update_scale_from_state(force=True)
    
    updated_root = sequencer.scale_mapper.root_note
    print(f"Updated sequencer root_note: {updated_root}")
    assert updated_root == 67, f"Expected 67, got {updated_root}"
    
    print("✓ Sequencer integration works")


def test_mutation_integration():
    """Test that mutation engine can mutate root_note."""
    print("\nTesting mutation integration...")
    
    reset_state()
    state = get_state()
    
    # Create a minimal mutation config
    class MockMutationConfig:
        interval_min_s = 60
        interval_max_s = 120
        max_changes_per_cycle = 1
    
    # Create mutation engine
    mutation_engine = create_mutation_engine(MockMutationConfig(), state)
    
    # Check that root_note rule exists
    root_note_rules = [rule for rule in mutation_engine._rules if rule.parameter == 'root_note']
    assert len(root_note_rules) == 1, f"Expected 1 root_note rule, got {len(root_note_rules)}"
    
    rule = root_note_rules[0]
    print(f"Root note mutation rule: {rule.description}")
    print(f"Delta range: {rule.delta_range}")
    
    # Test the rule application
    original_value = 60.0
    state.set('root_note', original_value)
    
    # Apply the rule multiple times to see it working
    for i in range(5):
        new_value = rule.apply_delta(original_value)
        print(f"  Iteration {i+1}: {original_value} -> {new_value:.1f}")
        
        # Verify it's within expected range
        expected_min = original_value + rule.delta_range[0]
        expected_max = original_value + rule.delta_range[1]
        assert expected_min <= new_value <= expected_max, f"Value {new_value} outside expected range [{expected_min}, {expected_max}]"
    
    print("✓ Mutation integration works")


def test_full_integration():
    """Test the full pipeline from config to mutation."""
    print("\nTesting full integration...")
    
    # Load config
    config = load_config("config.yaml")
    
    # Initialize state from config
    reset_state()
    state = get_state()
    state.set('root_note', config.sequencer.root_note, source='config')
    
    # Create components
    sequencer = create_sequencer(state, config.scales)
    mutation_engine = create_mutation_engine(config.mutation, state)
    
    # Force scale update to use the configured root note
    sequencer._update_scale_from_state(force=True)
    
    print(f"Initial state root_note: {state.get('root_note')}")
    print(f"Sequencer scale mapper root_note: {sequencer.scale_mapper.root_note}")
    
    # Verify they match
    assert state.get('root_note') == sequencer.scale_mapper.root_note
    
    # Test a state change propagates to sequencer
    state.set('root_note', 64)  # E4
    sequencer._update_scale_from_state(force=True)
    
    assert sequencer.scale_mapper.root_note == 64
    
    print("✓ Full integration works")


if __name__ == "__main__":
    print("Testing root_note parameter integration...")
    
    try:
        test_config_integration()
        test_state_integration()
        test_scale_mapper_integration()
        test_sequencer_integration()
        test_mutation_integration()
        test_full_integration()
        
        print("\n🎉 All tests passed! Root note parameter is working correctly.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
