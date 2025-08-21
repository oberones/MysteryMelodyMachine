"""Tests for idle mode functionality.

Phase 6: Comprehensive testing of idle mode detection, state saving/restoration,
and integration with mutation engine and action handlers.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from state import State, reset_state
from idle import IdleManager, IdleProfile, create_idle_manager
from config import IdleConfig
from action_handler import ActionHandler
from mutation import create_mutation_engine, MutationEngine
from events import SemanticEvent


@pytest.fixture
def state():
    """Fresh state instance for each test."""
    reset_state()
    return State()


@pytest.fixture
def idle_config():
    """Standard idle configuration for testing."""
    return IdleConfig(
        timeout_ms=1000,  # 1 second for fast tests
        ambient_profile="slow_fade",
        fade_in_ms=100,
        fade_out_ms=50
    )


@pytest.fixture
def idle_manager(state, idle_config):
    """Idle manager instance for testing."""
    return create_idle_manager(idle_config, state)


class TestIdleManager:
    """Test idle manager functionality."""
    
    def test_initialization(self, idle_manager, idle_config):
        """Test idle manager initialization."""
        assert idle_manager.config == idle_config
        assert idle_manager.timeout_seconds == 1.0  # 1000ms
        assert not idle_manager.is_idle
        assert idle_manager.saved_active_state is None
        assert idle_manager.current_profile is not None
        assert idle_manager.current_profile.name == "slow_fade"
    
    def test_idle_profiles_creation(self, idle_manager):
        """Test that idle profiles are created correctly."""
        profiles = idle_manager.idle_profiles
        
        # Check that expected profiles exist
        assert "slow_fade" in profiles
        assert "minimal" in profiles
        assert "meditative" in profiles
        
        # Check slow_fade profile
        slow_fade = profiles["slow_fade"]
        assert slow_fade.name == "slow_fade"
        assert "density" in slow_fade.params
        assert slow_fade.params["density"] == 0.3
        assert "bpm" in slow_fade.params
        assert slow_fade.params["bpm"] == 65.0
    
    def test_interaction_tracking(self, idle_manager):
        """Test interaction tracking and time calculations."""
        # Initial state
        initial_time = idle_manager.get_time_since_last_interaction()
        assert initial_time >= 0.0
        assert initial_time < 0.1  # Should be very recent
        
        # Touch interaction
        time.sleep(0.1)
        idle_manager.touch()
        new_time = idle_manager.get_time_since_last_interaction()
        assert new_time < initial_time
        
        # Time to idle calculation
        time_to_idle = idle_manager.get_time_to_idle()
        assert time_to_idle > 0.9  # Should be close to 1 second
        assert time_to_idle <= 1.0
    
    def test_manual_idle_control(self, idle_manager, state):
        """Test manual idle mode control."""
        # Set up some initial state
        state.set('density', 0.8, source='test')
        state.set('bpm', 120.0, source='test')
        
        # Force idle mode
        idle_manager.force_idle()
        assert idle_manager.is_idle
        assert idle_manager.saved_active_state is not None
        
        # Check that idle profile was applied
        assert state.get('density') == 0.3  # From slow_fade profile
        assert state.get('bpm') == 65.0
        
        # Force active mode
        idle_manager.force_active()
        assert not idle_manager.is_idle
        assert idle_manager.saved_active_state is None
        
        # Check that state was restored
        assert state.get('density') == 0.8
        assert state.get('bpm') == 120.0
    
    def test_automatic_idle_detection(self, idle_manager, state):
        """Test automatic idle detection after timeout."""
        # Set up initial state
        state.set('density', 0.9, source='test')
        state.set('bpm', 140.0, source='test')
        
        # Start idle manager
        idle_manager.start()
        
        try:
            # Should not be idle initially
            assert not idle_manager.is_idle
            
            # Wait longer than timeout (1 second + margin)
            time.sleep(1.2)
            
            # Should now be idle
            assert idle_manager.is_idle
            assert state.get('density') == 0.3  # Idle profile applied
            
            # Touch to exit idle
            idle_manager.touch()
            
            # Should exit idle mode immediately
            assert not idle_manager.is_idle
            assert state.get('density') == 0.9  # Original state restored
            
        finally:
            idle_manager.stop()
    
    def test_idle_state_callbacks(self, idle_manager):
        """Test idle state change callbacks."""
        callback_mock = Mock()
        idle_manager.add_idle_state_callback(callback_mock)
        
        # Force idle
        idle_manager.force_idle()
        callback_mock.assert_called_with(True)
        
        callback_mock.reset_mock()
        
        # Force active
        idle_manager.force_active()
        callback_mock.assert_called_with(False)
        
        # Remove callback
        idle_manager.remove_idle_state_callback(callback_mock)
        callback_mock.reset_mock()
        
        # Should not be called anymore
        idle_manager.force_idle()
        callback_mock.assert_not_called()
    
    def test_status_reporting(self, idle_manager):
        """Test status reporting functionality."""
        status = idle_manager.get_status()
        
        # Check initial status
        assert 'is_idle' in status
        assert 'timeout_seconds' in status
        assert 'time_since_last_interaction' in status
        assert 'time_to_idle' in status
        assert 'current_profile' in status
        assert 'saved_state_available' in status
        
        assert not status['is_idle']
        assert status['timeout_seconds'] == 1.0
        assert status['current_profile'] == 'slow_fade'
        assert not status['saved_state_available']
        
        # Check status after going idle
        idle_manager.force_idle()
        status = idle_manager.get_status()
        assert status['is_idle']
        assert status['saved_state_available']
        assert status['time_to_idle'] == -1.0  # Negative when already idle


class TestIdleIntegration:
    """Test idle mode integration with other components."""
    
    def test_action_handler_integration(self, state, idle_config):
        """Test action handler integration with idle manager."""
        idle_manager = create_idle_manager(idle_config, state)
        action_handler = ActionHandler(state)
        action_handler.set_idle_manager(idle_manager)
        
        # Force idle mode first
        idle_manager.force_idle()
        assert idle_manager.is_idle
        
        # Handle a semantic event - should exit idle mode
        event = SemanticEvent(type='tempo', source='test', value=64, raw_note=None)
        action_handler.handle_semantic_event(event)
        
        # Should have exited idle mode due to interaction
        assert not idle_manager.is_idle
    
    def test_mutation_engine_integration(self, state, idle_config):
        """Test mutation engine integration with idle mode."""
        from config import MutationConfig
        
        mutation_config = MutationConfig(
            interval_min_s=1,
            interval_max_s=1,
            max_changes_per_cycle=1
        )
        
        idle_manager = create_idle_manager(idle_config, state)
        mutation_engine = create_mutation_engine(mutation_config, state)
        
        # Connect idle manager to mutation engine
        mutation_engine.set_idle_manager(idle_manager)
        
        # Initially mutations should be disabled (before idle state is set)
        assert not mutation_engine.are_mutations_enabled()
        
        # Start idle manager - should keep mutations disabled (not idle yet)
        idle_manager.start()
        time.sleep(0.1)  # Allow callback to process
        assert not mutation_engine.are_mutations_enabled()
        
        # Force idle mode - should enable mutations
        idle_manager.force_idle()
        time.sleep(0.1)  # Allow callback to process
        assert mutation_engine.are_mutations_enabled()
        
        # Exit idle mode - should disable mutations
        idle_manager.force_active()
        time.sleep(0.1)  # Allow callback to process
        assert not mutation_engine.are_mutations_enabled()
        
        # Clean up
        idle_manager.stop()
        mutation_engine.stop()
    
    def test_mutation_blocking_when_not_idle(self, state, idle_config):
        """Test that mutations are blocked when not in idle mode."""
        from config import MutationConfig
        
        mutation_config = MutationConfig(
            interval_min_s=1,
            interval_max_s=1,
            max_changes_per_cycle=1
        )
        
        idle_manager = create_idle_manager(idle_config, state)
        mutation_engine = create_mutation_engine(mutation_config, state)
        mutation_engine.set_idle_manager(idle_manager)
        
        # Set up initial state
        original_density = 0.8
        state.set('density', original_density, source='test')
        
        # Start systems but don't go idle
        idle_manager.start()
        mutation_engine.start()
        
        try:
            # Force a mutation attempt when not idle
            mutation_engine.force_mutation()
            
            # Density should not have changed
            assert state.get('density') == original_density
            
            # Now force idle and try mutation
            idle_manager.force_idle()
            time.sleep(0.1)  # Allow callback
            mutation_engine.force_mutation()
            
            # Now density might have changed (mutation was allowed)
            # Note: We can't guarantee a change since mutation is random
            # but we can check that mutations are enabled
            assert mutation_engine.are_mutations_enabled()
            
        finally:
            idle_manager.stop()
            mutation_engine.stop()


class TestIdleStatePreservation:
    """Test state preservation and restoration during idle mode."""
    
    def test_complex_state_preservation(self, state, idle_config):
        """Test preservation of complex state during idle transitions."""
        idle_manager = create_idle_manager(idle_config, state)
        
        # Set up complex initial state
        initial_state = {
            'density': 0.85,
            'bpm': 125.0,
            'swing': 0.15,
            'scale_index': 3,
            'master_volume': 100,
            'reverb_mix': 50,
            'filter_cutoff': 80
        }
        
        for param, value in initial_state.items():
            state.set(param, value, source='test')
        
        # Enter idle mode
        idle_manager.force_idle()
        
        # Verify idle profile was applied
        assert state.get('density') == 0.3  # From slow_fade profile
        assert state.get('bpm') == 65.0
        
        # Exit idle mode
        idle_manager.force_active()
        
        # Verify all original state was restored
        for param, expected_value in initial_state.items():
            actual_value = state.get(param)
            assert actual_value == expected_value, f"Parameter {param}: expected {expected_value}, got {actual_value}"
    
    def test_partial_state_preservation(self, state, idle_config):
        """Test that only relevant parameters are preserved/restored."""
        idle_manager = create_idle_manager(idle_config, state)
        
        # Set parameters that are in the idle profile
        state.set('density', 0.9, source='test')
        state.set('bpm', 130.0, source='test')
        
        # Set parameter that is NOT in the idle profile
        state.set('sequence_length', 16, source='test')
        
        # Enter idle mode
        idle_manager.force_idle()
        
        # Parameters in idle profile should change
        assert state.get('density') == 0.3
        assert state.get('bpm') == 65.0
        
        # Parameter not in idle profile should remain unchanged
        assert state.get('sequence_length') == 16
        
        # Exit idle mode
        idle_manager.force_active()
        
        # Only parameters that were in the idle profile should be restored
        assert state.get('density') == 0.9
        assert state.get('bpm') == 130.0
        assert state.get('sequence_length') == 16  # Should still be unchanged


class TestIdleManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_multiple_idle_transitions(self, idle_manager, state):
        """Test multiple rapid idle transitions."""
        # Set initial state
        state.set('density', 0.7, source='test')
        
        # Multiple rapid transitions
        for _ in range(5):
            idle_manager.force_idle()
            assert idle_manager.is_idle
            idle_manager.force_active()
            assert not idle_manager.is_idle
        
        # State should be properly restored
        assert state.get('density') == 0.7
    
    def test_idle_with_missing_profile_params(self, state, idle_config):
        """Test idle mode when some profile parameters don't exist in state."""
        # Create idle manager with a custom profile
        idle_manager = create_idle_manager(idle_config, state)
        
        # Set only some of the parameters that the idle profile expects
        state.set('density', 0.8, source='test')
        # Don't set 'bpm' - it should get the default
        
        # Enter idle mode - should not crash
        idle_manager.force_idle()
        assert idle_manager.is_idle
        
        # Exit idle mode - should restore what was saved
        idle_manager.force_active()
        assert state.get('density') == 0.8
    
    def test_callback_exception_handling(self, idle_manager):
        """Test that callback exceptions don't break idle mode."""
        def bad_callback(is_idle):
            raise RuntimeError("Callback error")
        
        def good_callback(is_idle):
            good_callback.called = True
            good_callback.is_idle = is_idle
        
        good_callback.called = False
        
        idle_manager.add_idle_state_callback(bad_callback)
        idle_manager.add_idle_state_callback(good_callback)
        
        # Should not raise exception despite bad callback
        idle_manager.force_idle()
        assert idle_manager.is_idle
        assert good_callback.called
        assert good_callback.is_idle


def test_create_idle_manager_factory():
    """Test the factory function for creating idle managers."""
    state = State()
    config = IdleConfig(timeout_ms=5000, ambient_profile="minimal")
    
    manager = create_idle_manager(config, state)
    
    assert isinstance(manager, IdleManager)
    assert manager.config == config
    assert manager.state == state
    assert manager.timeout_seconds == 5.0
    assert manager.current_profile.name == "minimal"
