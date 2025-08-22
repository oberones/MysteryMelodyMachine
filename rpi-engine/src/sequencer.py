"""Sequencer core for the generative engine.

Phase 4: Adds scale mapping, probability, and density gating.
Provides high-resolution clock with drift correction and step management.
"""

from __future__ import annotations
from typing import Callable, Optional, Generator, List
from dataclasses import dataclass
import time
import threading
import logging
import random
from state import State, StateChange
from scale_mapper import ScaleMapper

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
        self._start_time = time.perf_counter()
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
            current_time = time.perf_counter()
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
                actual_time = time.perf_counter()
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
    
    Phase 4: Implements scale mapping, probability, and density.
    Phase 5.5: Enhanced with direction patterns, per-step probability, and velocity variation.
    """
    
    def __init__(self, state: State, scales: List[str]):
        self.state = state
        self.available_scales = scales
        self.scale_mapper = ScaleMapper()
        self.clock = HighResClock()
        self._note_callback: Optional[Callable[[NoteEvent], None]] = None
        self._current_step = 0
        self._steps_per_beat = 4  # 16th notes
        self._ticks_per_step = 0
        self._tick_counter = 0
        
        # Direction pattern state
        self._direction = 1  # 1 for forward, -1 for backward
        self._ping_pong_direction = 1  # For ping-pong mode
        
        # For quantizing scale changes
        self._pending_scale_index: Optional[int] = None
        self._quantize_on_bar = True # From config eventually

        # Listen for state changes
        self.state.add_listener(self._on_state_change)
        
        # Initialize clock and scale from state
        self._update_clock_from_state()
        self._update_scale_from_state(force=True)  # Force immediate application during init
        
        # Set up clock callback
        self.clock.set_tick_callback(self._on_tick)
        
        log.info("sequencer_initialized")
    
    def set_step_probabilities(self, probabilities: List[float]):
        """Set per-step probability array.
        
        Args:
            probabilities: List of probability values (0.0-1.0) for each step
        """
        # Validate probabilities
        validated_probs = []
        for i, prob in enumerate(probabilities):
            if not isinstance(prob, (int, float)):
                log.warning(f"Invalid probability at step {i}: {prob}, using 0.5")
                validated_probs.append(0.5)
            else:
                validated_probs.append(max(0.0, min(1.0, float(prob))))
        
        self.state.set('step_probabilities', validated_probs, source='sequencer')
        log.info(f"step_probabilities_set length={len(validated_probs)} values={validated_probs}")
    
    def set_step_pattern(self, pattern: List[bool]):
        """Set step activation pattern.
        
        Args:
            pattern: List of boolean values indicating which steps are active
        """
        # Validate pattern
        validated_pattern = []
        for i, active in enumerate(pattern):
            if not isinstance(active, bool):
                log.warning(f"Invalid pattern value at step {i}: {active}, using False")
                validated_pattern.append(False)
            else:
                validated_pattern.append(active)
        
        self.state.set('step_pattern', validated_pattern, source='sequencer')
        log.info(f"step_pattern_set length={len(validated_pattern)} pattern={validated_pattern}")
    
    def set_velocity_params(self, base_velocity: int = 80, velocity_range: int = 40):
        """Set velocity variation parameters.
        
        Args:
            base_velocity: Base velocity value (1-127)
            velocity_range: Range for velocity variation (+/- from base)
        """
        base_velocity = max(1, min(127, base_velocity))
        velocity_range = max(0, min(127, velocity_range))
        
        self.state.set('base_velocity', base_velocity, source='sequencer')
        self.state.set('velocity_range', velocity_range, source='sequencer')
        log.info(f"velocity_params_set base={base_velocity} range={velocity_range}")
    
    def get_pattern_preset(self, preset_name: str) -> List[bool]:
        """Get a predefined step pattern.
        
        Args:
            preset_name: Name of the preset pattern
            
        Returns:
            List of boolean values for the pattern
        """
        presets = {
            'four_on_floor': [True, False, False, False, True, False, False, False],
            'offbeat': [False, True, False, True, False, True, False, True],
            'every_other': [True, False, True, False, True, False, True, False],
            'syncopated': [True, False, True, True, False, True, False, False],
            'dense': [True, True, False, True, True, False, True, True],
            'sparse': [True, False, False, False, False, False, True, False],
            'all_on': [True] * 8,
            'all_off': [False] * 8
        }
        
        if preset_name in presets:
            return presets[preset_name]
        else:
            log.warning(f"Unknown pattern preset: {preset_name}, using 'every_other'")
            return presets['every_other']
    
    def get_probability_preset(self, preset_name: str, length: int = 8) -> List[float]:
        """Get a predefined probability pattern.
        
        Args:
            preset_name: Name of the preset
            length: Length of the pattern to generate
            
        Returns:
            List of probability values
        """
        presets = {
            'uniform': [0.9] * length,
            'crescendo': [0.3 + (i * 0.6 / (length - 1)) for i in range(length)],
            'diminuendo': [0.9 - (i * 0.6 / (length - 1)) for i in range(length)],
            'peaks': [0.9 if i % 4 == 0 else 0.4 for i in range(length)],
            'valleys': [0.3 if i % 4 == 0 else 0.8 for i in range(length)],
            'random_low': [random.uniform(0.2, 0.6) for _ in range(length)],
            'random_high': [random.uniform(0.6, 1.0) for _ in range(length)],
            'alternating': [0.9 if i % 2 == 0 else 0.3 for i in range(length)]
        }
        
        if preset_name in presets:
            return presets[preset_name]
        else:
            log.warning(f"Unknown probability preset: {preset_name}, using 'uniform'")
            return presets['uniform']
    
    def get_direction_preset(self, preset_name: str) -> str:
        """Get a direction pattern preset name.
        
        Args:
            preset_name: Name of the direction preset
            
        Returns:
            Valid direction pattern name
        """
        valid_directions = {'forward', 'backward', 'ping_pong', 'random'}
        
        if preset_name in valid_directions:
            return preset_name
        else:
            log.warning(f"Unknown direction preset: {preset_name}, using 'forward'")
            return 'forward'
    
    def set_direction_pattern(self, direction: str):
        """Set the sequencer direction pattern.
        
        Args:
            direction: Direction pattern ('forward', 'backward', 'ping_pong', 'random')
        """
        valid_directions = {'forward', 'backward', 'ping_pong', 'random'}
        
        if direction not in valid_directions:
            log.warning(f"Invalid direction pattern: {direction}, using 'forward'")
            direction = 'forward'
        
        self.state.set('direction_pattern', direction, source='sequencer')
        
        # Reset direction state when changing patterns
        if direction == 'forward':
            self._direction = 1
            self._ping_pong_direction = 1
        elif direction == 'backward':
            self._direction = -1
            self._ping_pong_direction = -1
        elif direction == 'ping_pong':
            self._direction = 1
            self._ping_pong_direction = 1
        # For random, we don't reset anything - it's calculated per step
        
        log.info(f"direction_pattern_set pattern={direction}")
    
    def _get_next_step(self, current_step: int, sequence_length: int) -> int:
        """Calculate the next step based on the current direction pattern.
        
        Args:
            current_step: Current step position (0-based)
            sequence_length: Total number of steps in sequence
            
        Returns:
            Next step position (0-based)
        """
        direction_pattern = self.state.get('direction_pattern', 'forward')
        
        if direction_pattern == 'forward':
            return (current_step + 1) % sequence_length
        
        elif direction_pattern == 'backward':
            return (current_step - 1) % sequence_length
        
        elif direction_pattern == 'ping_pong':
            # Ping-pong bounces at sequence boundaries
            next_step = current_step + self._ping_pong_direction
            
            # Check for boundaries and reverse direction
            if next_step >= sequence_length:
                self._ping_pong_direction = -1
                next_step = sequence_length - 2  # Bounce back
            elif next_step < 0:
                self._ping_pong_direction = 1
                next_step = 1  # Bounce forward
            
            return max(0, min(sequence_length - 1, next_step))
        
        elif direction_pattern == 'random':
            # Choose a random step, but avoid staying on the same step
            possible_steps = [i for i in range(sequence_length) if i != current_step]
            if possible_steps:
                return random.choice(possible_steps)
            else:
                # Fallback if sequence length is 1
                return current_step
        
        else:
            # Fallback to forward
            return (current_step + 1) % sequence_length
    
    def set_note_callback(self, callback: Callable[[NoteEvent], None]):
        """Set callback for generated note events."""
        self._note_callback = callback
    
    def start(self):
        """Start the sequencer."""
        # Generate note for the initial step (step 0)
        self._generate_step_note(self._current_step)
        
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
        
        self._ticks_per_step = self.clock.ppq // self._steps_per_beat
        
        self.clock.update_params(bpm=bpm, swing=swing)

    def _update_scale_from_state(self, force: bool = False):
        """Update the scale mapper from the current state."""
        scale_index = self.state.get('scale_index', 0)
        
        if self._quantize_on_bar and not force:
            # Defer the change until the next bar boundary
            self._pending_scale_index = scale_index
            log.debug(f"scale_change_pending index={scale_index}")
        else:
            # Apply immediately
            self._apply_scale_change(scale_index)

    def _apply_scale_change(self, scale_index: int):
        """Apply the scale change to the scale mapper."""
        if 0 <= scale_index < len(self.available_scales):
            scale_name = self.available_scales[scale_index]
            root_note = self.state.get('root_note', 60)  # Default to C4
            try:
                self.scale_mapper.set_scale(scale_name, root_note=root_note)
                log.info(f"scale_set name='{scale_name}' root={self.scale_mapper.root_note}")
            except ValueError as e:
                log.error(f"Failed to set scale: {e}")
        else:
            log.warning(f"Invalid scale_index {scale_index}, max is {len(self.available_scales)-1}")
        self._pending_scale_index = None

    def _on_state_change(self, change: StateChange):
        """Handle state parameter changes."""
        if change.parameter in ('bpm', 'swing'):
            self._update_clock_from_state()
        elif change.parameter in ('scale_index', 'root_note'):
            self._update_scale_from_state()
        elif change.parameter == 'sequence_length':
            log.debug(f"sequence_length_changed new_length={change.new_value}")
        elif change.parameter == 'step_position':
            self._current_step = change.new_value
        elif change.parameter == 'direction_pattern':
            # Reset direction state when pattern changes
            direction = change.new_value
            if direction == 'forward':
                self._direction = 1
                self._ping_pong_direction = 1
            elif direction == 'backward':
                self._direction = -1
                self._ping_pong_direction = -1
            elif direction == 'ping_pong':
                self._direction = 1
                self._ping_pong_direction = 1
            log.debug(f"direction_pattern_changed pattern={direction}")
    
    def _on_tick(self, tick: TickEvent):
        """Handle clock tick events."""
        self._tick_counter += 1
        
        if self._tick_counter >= self._ticks_per_step:
            self._tick_counter = 0
            self._advance_step()
    
    def _advance_step(self):
        """Advance to the next step using the current direction pattern and generate events."""
        sequence_length = self.state.get('sequence_length', 8)
        
        # Calculate next step using direction pattern
        next_step = self._get_next_step(self._current_step, sequence_length)
        self._current_step = next_step
        
        # Bar boundary check for quantized changes (check if we're at step 0)
        is_bar_boundary = self._current_step == 0
        if is_bar_boundary and self._pending_scale_index is not None:
            self._apply_scale_change(self._pending_scale_index)
        
        self.state.set('step_position', self._current_step, source='sequencer')
        
        self._generate_step_note(self._current_step)
        
        direction_pattern = self.state.get('direction_pattern', 'forward')
        log.debug(f"step_advance step={self._current_step} length={sequence_length} direction={direction_pattern}")
    
    def _generate_step_note(self, step: int):
        """
        Generate a note event for the given step, considering density and probability.
        Phase 5.5: Enhanced with per-step probabilities, configurable patterns, and velocity variation.
        """
        if not self._note_callback:
            return

        density = self.state.get('density', 0.85)

        # Density acts as a gate for the entire step's activity
        if random.random() > density:
            return

        # Phase 5.5: Get per-step probability array
        step_probabilities = self.state.get('step_probabilities', None)
        if step_probabilities is None:
            # Fallback to global note_probability for backward compatibility
            note_prob = self.state.get('note_probability', 0.9)
            step_probabilities = [note_prob] * self.state.get('sequence_length', 8)
        
        # Get probability for this specific step
        sequence_length = len(step_probabilities)
        step_prob = step_probabilities[step % sequence_length]

        # Phase 5.5: Get configurable step pattern
        step_pattern = self.state.get('step_pattern', None)
        if step_pattern is None:
            # Fallback to hardcoded even-step pattern for backward compatibility
            is_active_step = step % 2 == 0
        else:
            # Use configurable pattern (array of booleans)
            pattern_length = len(step_pattern)
            is_active_step = step_pattern[step % pattern_length]
        
        if is_active_step and random.random() < step_prob:
            # Use scale mapper to get the note
            # Simple mapping: step number maps to scale degree
            degree = step // 2 
            note = self.scale_mapper.get_note(degree, octave=0)
            
            # Phase 5.5: Velocity variation based on probability values
            base_velocity = self.state.get('base_velocity', 80)
            velocity_range = self.state.get('velocity_range', 40)  # +/- range
            
            # Scale velocity based on step probability (higher prob = higher velocity)
            # Also add some randomness based on the probability
            velocity_factor = 0.5 + (step_prob * 0.5)  # 0.5 to 1.0 range
            velocity_random = random.uniform(-0.2, 0.2) * step_prob  # More randomness for higher probs
            
            final_velocity_factor = max(0.1, min(1.0, velocity_factor + velocity_random))
            velocity = int(base_velocity + (velocity_range * (final_velocity_factor - 0.5)))
            velocity = max(1, min(127, velocity))  # Clamp to MIDI range
            
            bpm = self.state.get('bpm', 110.0)
            step_duration = 60.0 / (bpm * self._steps_per_beat)
            gate_length_factor = self.state.get('gate_length', 0.8)
            gate_length = step_duration * gate_length_factor
            
            note_event = NoteEvent(
                note=note,
                velocity=velocity,
                timestamp=time.perf_counter(),
                step=step,
                duration=gate_length
            )
            
            try:
                self._note_callback(note_event)
                log.debug(f"note_generated step={step} note={note} velocity={velocity} step_prob={step_prob:.2f}")
            except Exception as e:
                log.error(f"Note callback error: {e}")


def create_sequencer(state: State, scales: list[str]) -> Sequencer:
    """Factory function to create a sequencer instance."""
    return Sequencer(state, scales)
