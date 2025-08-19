"""Sequencer core for the generative engine.

Phase 2: Basic step timing and playback without probability gating.
Provides high-resolution clock with drift correction and step management.
"""

from __future__ import annotations
from typing import Callable, Optional, Generator
from dataclasses import dataclass
import time
import threading
import logging
from state import State, StateChange

log = logging.getLogger(__name__)


@dataclass
class TickEvent:
    """Represents a sequencer tick."""
    step: int  # 0-based step number
    timestamp: float
    swing_adjusted: bool = False


@dataclass
class NoteEvent:
    """Represents a note to be played."""
    note: int  # MIDI note number
    velocity: int
    timestamp: float
    step: int  # Step that generated this note
    duration: float = 0.1  # Duration in seconds (for note off timing)


class HighResClock:
    """High-resolution clock with drift correction.
    
    Provides accurate timing for sequencer steps with swing support.
    """
    
    def __init__(self, bpm: float = 110.0, ppq: int = 24, swing: float = 0.0):
        self.bpm = bpm
        self.ppq = ppq  # Pulses per quarter note
        self.swing = swing
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tick_callback: Optional[Callable[[TickEvent], None]] = None
        self._start_time = 0.0
        self._tick_count = 0
        self._drift_accumulator = 0.0
    
    def set_tick_callback(self, callback: Callable[[TickEvent], None]):
        """Set the callback for tick events."""
        self._tick_callback = callback
    
    def start(self):
        """Start the clock."""
        if self._running:
            return
        
        self._running = True
        self._start_time = time.time()
        self._tick_count = 0
        self._drift_accumulator = 0.0
        
        self._thread = threading.Thread(target=self._clock_thread, daemon=True)
        self._thread.start()
        log.info(f"clock_started bpm={self.bpm} ppq={self.ppq} swing={self.swing}")
    
    def stop(self):
        """Stop the clock."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        log.info("clock_stopped")
    
    def update_params(self, bpm: Optional[float] = None, swing: Optional[float] = None):
        """Update clock parameters on the fly."""
        if bpm is not None:
            self.bpm = bpm
        if swing is not None:
            self.swing = swing
        log.debug(f"clock_params_updated bpm={self.bpm} swing={self.swing}")
    
    def _clock_thread(self):
        """Main clock thread with drift correction."""
        while self._running:
            tick_interval = 60.0 / (self.bpm * self.ppq)
            
            # Calculate target time for this tick
            target_time = self._start_time + (self._tick_count * tick_interval)
            
            # Apply swing to odd-numbered 16th note ticks
            # Swing affects every other ppq/4 tick (assuming ppq=24, every 6th tick)
            swing_adjusted = False
            if self.swing > 0.0 and self.ppq >= 4:
                swing_tick_interval = self.ppq // 4
                if swing_tick_interval > 0 and (self._tick_count // swing_tick_interval) % 2 == 1:
                    swing_offset = tick_interval * self.swing
                    target_time += swing_offset
                    swing_adjusted = True
            
            # Add accumulated drift compensation
            target_time += self._drift_accumulator
            
            # Sleep until target time
            current_time = time.time()
            sleep_time = target_time - current_time
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # We're behind - accumulate the drift
                self._drift_accumulator += sleep_time
                # Limit drift accumulation to prevent runaway
                self._drift_accumulator = max(-0.01, min(0.01, self._drift_accumulator))
            
            # Emit tick event
            if self._tick_callback:
                actual_time = time.time()
                tick_event = TickEvent(
                    step=self._tick_count % self.ppq,
                    timestamp=actual_time,
                    swing_adjusted=swing_adjusted
                )
                try:
                    self._tick_callback(tick_event)
                except Exception as e:
                    log.error(f"Tick callback error: {e}")
            
            self._tick_count += 1


class Sequencer:
    """Main sequencer with step management and note generation.
    
    Phase 2: Basic step playback with configurable length.
    Future phases will add probability, density, and mutation.
    """
    
    def __init__(self, state: State, scales: list[str]):
        self.state = state
        self.scales = scales
        self.clock = HighResClock()
        self._note_callback: Optional[Callable[[NoteEvent], None]] = None
        self._current_step = 0
        self._steps_per_beat = 4  # 16th notes
        self._ticks_per_step = 0
        self._tick_counter = 0
        
        # Listen for state changes
        self.state.add_listener(self._on_state_change)
        
        # Initialize clock parameters from state
        self._update_clock_from_state()
        
        # Set up clock callback
        self.clock.set_tick_callback(self._on_tick)
        
        log.info("sequencer_initialized")
    
    def set_note_callback(self, callback: Callable[[NoteEvent], None]):
        """Set callback for generated note events."""
        self._note_callback = callback
    
    def start(self):
        """Start the sequencer."""
        self.clock.start()
        log.info("sequencer_started")
    
    def stop(self):
        """Stop the sequencer."""
        self.clock.stop()
        log.info("sequencer_stopped")
    
    def _update_clock_from_state(self):
        """Update clock parameters from current state."""
        bpm = self.state.get('bpm', 110.0)
        swing = self.state.get('swing', 0.0)
        
        # Calculate ticks per step based on PPQ and step subdivision
        # PPQ=24 means 24 ticks per quarter note
        # For 16th note steps: 24/4 = 6 ticks per step
        self._ticks_per_step = self.clock.ppq // self._steps_per_beat
        
        self.clock.update_params(bpm=bpm, swing=swing)
    
    def _on_state_change(self, change: StateChange):
        """Handle state parameter changes."""
        if change.parameter in ('bpm', 'swing'):
            self._update_clock_from_state()
        elif change.parameter == 'sequence_length':
            log.debug(f"sequence_length_changed new_length={change.new_value}")
        elif change.parameter == 'step_position':
            # External step position change (e.g., from UI)
            self._current_step = change.new_value
    
    def _on_tick(self, tick: TickEvent):
        """Handle clock tick events."""
        self._tick_counter += 1
        
        # Check if it's time for a new step
        if self._tick_counter >= self._ticks_per_step:
            self._tick_counter = 0
            self._advance_step()
    
    def _advance_step(self):
        """Advance to the next step and generate events."""
        sequence_length = self.state.get('sequence_length', 8)
        self._current_step = (self._current_step + 1) % sequence_length
        
        # Update state with current step position
        self.state.set('step_position', self._current_step, source='sequencer')
        
        # Generate note event for this step
        # Phase 2: Simple note generation (C major scale, deterministic)
        self._generate_step_note(self._current_step)
        
        log.debug(f"step_advance step={self._current_step} length={sequence_length}")
    
    def _generate_step_note(self, step: int):
        """Generate a note event for the given step.
        
        Phase 2: Simple deterministic note generation.
        Future phases will add probability, density, and scale mapping.
        """
        if not self._note_callback:
            return
        
        # Simple pattern: play notes on steps 0, 2, 4, 6 (every other step)
        if step % 2 == 0:
            # Simple C major scale pattern
            scale_notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 to C5
            note = scale_notes[step % len(scale_notes)]
            velocity = 80
            
            # Calculate note duration based on tempo
            bpm = self.state.get('bpm', 110.0)
            # Default gate length of 80% of step duration
            step_duration = 60.0 / (bpm * self._steps_per_beat)
            gate_length = step_duration * 0.8
            
            note_event = NoteEvent(
                note=note,
                velocity=velocity,
                timestamp=time.time(),
                step=step,
                duration=gate_length
            )
            
            try:
                self._note_callback(note_event)
                log.debug(f"note_generated step={step} note={note} velocity={velocity} duration={gate_length:.3f}")
            except Exception as e:
                log.error(f"Note callback error: {e}")


def create_sequencer(state: State, scales: list[str]) -> Sequencer:
    """Factory function to create a sequencer instance."""
    return Sequencer(state, scales)
