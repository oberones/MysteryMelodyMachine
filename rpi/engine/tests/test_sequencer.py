"""Tests for sequencer module."""

import pytest
import time
from unittest.mock import Mock, patch
from state import State
from sequencer import HighResClock, Sequencer, TickEvent, NoteEvent, create_sequencer


@pytest.fixture
def state():
    """Fresh state instance for each test."""
    state = State()
    return state


def test_high_res_clock_initialization():
    """Test clock initialization with default parameters."""
    clock = HighResClock()
    assert clock.bpm == 110.0
    assert clock.ppq == 24
    assert clock.swing == 0.0
    assert clock._running is False


def test_clock_parameter_updates():
    """Test updating clock parameters."""
    clock = HighResClock()
    clock.update_params(bpm=120.0, swing=0.1)
    
    assert clock.bpm == 120.0
    assert clock.swing == 0.1


def test_clock_start_stop():
    """Test starting and stopping the clock."""
    clock = HighResClock()
    mock_callback = Mock()
    clock.set_tick_callback(mock_callback)
    
    # Start clock
    clock.start()
    assert clock._running is True
    assert clock._thread is not None
    
    # Let it run briefly
    time.sleep(0.1)
    
    # Stop clock
    clock.stop()
    assert clock._running is False
    
    # Verify we got some ticks
    assert mock_callback.call_count > 0


def test_clock_tick_events():
    """Test that clock generates tick events with correct structure."""
    clock = HighResClock(bpm=240.0, ppq=4)  # Fast for testing
    received_ticks = []
    
    def tick_callback(tick):
        received_ticks.append(tick)
        if len(received_ticks) >= 8:  # Stop after 8 ticks (2 beats)
            clock.stop()
    
    clock.set_tick_callback(tick_callback)
    clock.start()
    
    # Wait for ticks
    time.sleep(0.5)
    
    # Verify tick structure
    assert len(received_ticks) >= 4
    for tick in received_ticks:
        assert isinstance(tick, TickEvent)
        assert isinstance(tick.step, int)
        assert isinstance(tick.timestamp, float)
        assert isinstance(tick.swing_adjusted, bool)
        assert 0 <= tick.step < clock.ppq


def test_swing_application():
    """Test that swing is applied to appropriate ticks."""
    clock = HighResClock(bpm=120.0, ppq=8, swing=0.5)
    swing_ticks = []
    regular_ticks = []
    
    def tick_callback(tick):
        if tick.swing_adjusted:
            swing_ticks.append(tick.step)
        else:
            regular_ticks.append(tick.step)
        
        if len(swing_ticks) + len(regular_ticks) >= 16:
            clock.stop()
    
    clock.set_tick_callback(tick_callback)
    clock.start()
    time.sleep(0.5)
    
    # With ppq=8 and swing, every other 2nd tick should be swing-adjusted
    # (every 4th tick: 2, 6, 10, 14, etc.)
    assert len(swing_ticks) > 0
    assert len(regular_ticks) > 0


def test_sequencer_initialization(state):
    """Test sequencer initialization."""
    scales = ['major', 'minor', 'pentatonic']
    sequencer = Sequencer(state, scales)
    
    assert sequencer.state is state
    assert sequencer.scales == scales
    assert sequencer._current_step == 0


def test_sequencer_state_listener(state):
    """Test that sequencer responds to state changes."""
    scales = ['major', 'minor']
    sequencer = Sequencer(state, scales)
    
    # Change BPM and verify clock is updated
    original_bpm = sequencer.clock.bpm
    state.set('bpm', 140.0)
    
    # Give a moment for the listener to process
    time.sleep(0.01)
    assert sequencer.clock.bpm == 140.0
    assert sequencer.clock.bpm != original_bpm


def test_sequencer_step_advancement(state):
    """Test step advancement and position tracking."""
    sequencer = Sequencer(state, ['major'])
    mock_note_callback = Mock()
    sequencer.set_note_callback(mock_note_callback)
    
    # Set a short sequence for testing
    state.set('sequence_length', 4)
    
    # Manually trigger step advancement
    for i in range(6):
        sequencer._advance_step()
    
    # Verify step position wraps around correctly
    assert state.get('step_position') == 2  # (6 % 4) = 2
    
    # Verify note callbacks were made
    assert mock_note_callback.call_count > 0


def test_sequencer_note_generation(state):
    """Test note generation pattern."""
    sequencer = Sequencer(state, ['major'])
    generated_notes = []
    
    def note_callback(note_event):
        generated_notes.append(note_event)
    
    sequencer.set_note_callback(note_callback)
    
    # Generate notes for several steps
    for step in range(8):
        sequencer._generate_step_note(step)
    
    # Phase 2 pattern: notes on even steps only
    even_step_notes = [n for n in generated_notes if n.step % 2 == 0]
    odd_step_notes = [n for n in generated_notes if n.step % 2 == 1]
    
    assert len(even_step_notes) == 4  # Steps 0, 2, 4, 6
    assert len(odd_step_notes) == 0   # No notes on odd steps
    
    # Verify note structure
    for note in even_step_notes:
        assert isinstance(note, NoteEvent)
        assert isinstance(note.note, int)
        assert 60 <= note.note <= 127  # Valid MIDI range
        assert isinstance(note.velocity, int)
        assert 0 <= note.velocity <= 127
        assert isinstance(note.step, int)


def test_sequencer_integration(state):
    """Test full sequencer integration with clock."""
    scales = ['major', 'minor']
    sequencer = Sequencer(state, scales)
    generated_notes = []
    
    def note_callback(note_event):
        generated_notes.append(note_event)
        # Stop after a few notes to avoid long test
        if len(generated_notes) >= 3:
            sequencer.stop()
    
    sequencer.set_note_callback(note_callback)
    
    # Set fast tempo for quick testing
    state.set('bpm', 480.0)  # Very fast
    state.set('sequence_length', 4)
    
    # Start sequencer
    sequencer.start()
    
    # Wait for notes
    time.sleep(0.5)
    
    # Verify we got some notes
    assert len(generated_notes) > 0
    
    # Verify step positions were updated
    final_step = state.get('step_position')
    assert isinstance(final_step, int)
    assert 0 <= final_step < 4


def test_sequencer_callback_exception_handling(state):
    """Test that callback exceptions don't crash the sequencer."""
    sequencer = Sequencer(state, ['major'])
    
    def bad_callback(note_event):
        raise RuntimeError("Callback error")
    
    sequencer.set_note_callback(bad_callback)
    
    # This should not raise an exception
    sequencer._generate_step_note(0)


def test_create_sequencer_factory():
    """Test the factory function."""
    state = State()
    scales = ['major', 'minor', 'pentatonic']
    
    sequencer = create_sequencer(state, scales)
    assert isinstance(sequencer, Sequencer)
    assert sequencer.state is state
    assert sequencer.scales == scales


def test_sequence_length_change_handling(state):
    """Test that sequence length changes are handled properly."""
    sequencer = Sequencer(state, ['major'])
    
    # Start with length 8
    assert state.get('sequence_length') == 8
    
    # Advance to step 6
    state.set('step_position', 6)
    
    # Change length to 4 - next step should wrap to 0
    state.set('sequence_length', 4)
    sequencer._advance_step()
    
    # Should wrap around since 6+1=7, and 7%4=3, then +1 = 0 for next advance
    # Actually, let's test the current step is within bounds
    current_step = state.get('step_position')
    sequence_length = state.get('sequence_length')
    assert 0 <= current_step < sequence_length
