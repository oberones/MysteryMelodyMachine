"""Fugue mode implementation for the generative sequencer.

Implements contrapuntal fugue generation based on the fugue_mode_spec.md specification.
Generates mini-fugues with exposition, episodes, and optional stretto sections.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, TypedDict
from dataclasses import dataclass
import time
import random
import logging
import math
from state import State
from scale_mapper import ScaleMapper

log = logging.getLogger(__name__)


class Note(TypedDict):
    """Note representation for fugue generation."""
    pitch: int    # MIDI note number
    dur: float    # Duration in quarter notes
    vel: int      # Velocity (1-127)


# Type aliases
Phrase = List[Note]
Score = List[Phrase]  # List of voices


@dataclass
class FugueParams:
    """Parameters for fugue generation."""
    n_voices: int = 3
    key_root: int = 60                    # Tonic MIDI note
    mode: str = "minor"
    entry_gap_beats: Optional[float] = None  # Default: subject length
    stretto_overlap: float = 0.0          # 0..1
    use_tonal_answer: bool = True
    allow_inversion: bool = False
    allow_retrograde: bool = False
    allow_augmentation: bool = False
    allow_diminution: bool = False
    episode_density: float = 0.5          # 0..1
    cadence_every_measures: int = 4
    # Counterpoint weights
    w_parallel: float = 5.0
    w_direct: float = 2.5
    w_disson: float = 3.0
    w_cross: float = 1.0
    w_smooth: float = -1.0                # Negative rewards (lower is better)
    # Voice ranges (relative to tonic)
    ranges: Optional[List[Tuple[int, int]]] = None


@dataclass
class Entry:
    """Represents a subject/answer entry in the fugue."""
    voice_index: int
    start_time: float  # In quarter notes
    material: Phrase
    is_subject: bool = True  # True for subject, False for answer


class FugueEngine:
    """Engine for generating fugues according to the specification."""
    
    def __init__(self, scale_mapper: ScaleMapper):
        self.scale_mapper = scale_mapper
        self._generate_seed_for_determinism()
    
    def _generate_seed_for_determinism(self):
        """Generate a seed for deterministic fugue generation."""
        self._seed = random.randint(0, 2**31 - 1)
        log.debug(f"fugue_seed={self._seed}")
    
    def generate_subject(self, params: FugueParams, bars: int = 1) -> Phrase:
        """Generate a fugue subject using melodic principles.
        
        Creates a 4-beat subject in the current key following Bach-like principles:
        - Clear melodic contour
        - Intervallic variety
        - Distinctive rhythm
        - Cadential closure
        """
        random.seed(self._seed)
        
        # Convert bars to quarter notes (assuming 4/4 time)
        total_duration = bars * 4.0
        
        # Generate melodic contour using Bach-like patterns
        notes = []
        current_time = 0.0
        
        # Start on tonic or dominant
        start_degree = random.choice([0, 4])  # Tonic or dominant
        current_degree = start_degree
        
        # Rhythmic patterns typical of Bach subjects
        rhythm_patterns = [
            [0.5, 0.5, 1.0, 2.0],      # Short-short-quarter-half
            [1.0, 0.5, 0.5, 2.0],      # Quarter-short-short-half
            [0.25, 0.25, 0.5, 1.0, 2.0],  # Quick opening
            [1.0, 1.0, 1.0, 1.0],      # Even quarters
        ]
        
        # Choose rhythm pattern based on mode and style
        durations = random.choice(rhythm_patterns)
        
        # Ensure durations fit within total_duration
        duration_sum = sum(durations)
        if duration_sum > total_duration:
            # Scale down durations proportionally
            scale_factor = total_duration / duration_sum
            durations = [d * scale_factor for d in durations]
        
        # Generate melodic intervals following Bach principles
        intervals = []
        for i in range(len(durations) - 1):
            # Prefer steps and small leaps
            if random.random() < 0.6:  # 60% steps
                interval = random.choice([-1, 1])
            elif random.random() < 0.3:  # 30% small leaps
                interval = random.choice([-2, 2, -3, 3])
            else:  # 10% larger leaps
                interval = random.choice([-4, 4, -5, 5])
            
            # Avoid too many consecutive leaps in same direction
            if len(intervals) >= 2 and all(x > 0 for x in intervals[-2:]) and interval > 0:
                interval = -interval
            elif len(intervals) >= 2 and all(x < 0 for x in intervals[-2:]) and interval < 0:
                interval = -interval
            
            intervals.append(interval)
        
        # Create the subject
        for i, duration in enumerate(durations):
            # Get the note from scale mapper
            try:
                pitch = self.scale_mapper.get_note(current_degree, octave=0)
                velocity = 96  # Standard forte
                
                notes.append(Note(pitch=pitch, dur=duration, vel=velocity))
                current_time += duration
                
                # Move to next degree if not the last note
                if i < len(intervals):
                    current_degree += intervals[i]
                    # Keep within reasonable range
                    current_degree = max(-7, min(14, current_degree))
                    
            except Exception as e:
                log.warning(f"Error generating subject note at degree {current_degree}: {e}")
                # Fallback to simpler note
                pitch = params.key_root + (current_degree * 2)  # Whole tone approximation
                notes.append(Note(pitch=pitch, dur=duration, vel=velocity))
        
        log.info(f"subject_generated length={len(notes)} total_duration={sum(n['dur'] for n in notes):.2f}")
        return notes
    
    def transpose(self, phrase: Phrase, semitones: int) -> Phrase:
        """Transpose a phrase by the given number of semitones."""
        return [
            Note(pitch=note['pitch'] + semitones, dur=note['dur'], vel=note['vel'])
            for note in phrase
        ]
    
    def invert(self, phrase: Phrase, axis_pitch: int) -> Phrase:
        """Invert a phrase around the given axis pitch."""
        return [
            Note(pitch=2 * axis_pitch - note['pitch'], dur=note['dur'], vel=note['vel'])
            for note in phrase
        ]
    
    def retrograde(self, phrase: Phrase) -> Phrase:
        """Reverse the time order of a phrase."""
        return list(reversed(phrase))
    
    def time_scale(self, phrase: Phrase, scale_factor: float) -> Phrase:
        """Scale the duration of all notes by the given factor."""
        return [
            Note(pitch=note['pitch'], dur=note['dur'] * scale_factor, vel=note['vel'])
            for note in phrase
        ]
    
    def shift_time(self, phrase: Phrase, offset_quarters: float) -> Phrase:
        """Add a time offset to the phrase (for later processing)."""
        # Note: This doesn't modify the phrase itself, just marks the offset
        # The actual timing will be handled during playback
        return phrase.copy()
    
    def slice_by_time(self, phrase: Phrase, t0: float, t1: float) -> Phrase:
        """Extract a time slice from a phrase."""
        result = []
        current_time = 0.0
        
        for note in phrase:
            note_start = current_time
            note_end = current_time + note['dur']
            
            # Check if this note overlaps with the slice
            if note_start < t1 and note_end > t0:
                # Calculate the overlap
                slice_start = max(t0, note_start)
                slice_end = min(t1, note_end)
                slice_duration = slice_end - slice_start
                
                if slice_duration > 0:
                    result.append(Note(
                        pitch=note['pitch'],
                        dur=slice_duration,
                        vel=note['vel']
                    ))
            
            current_time = note_end
        
        return result
    
    def tonal_answer(self, subject: Phrase, key_root: int) -> Phrase:
        """Generate a tonal answer by adjusting the first tonic->dominant motion."""
        if not subject:
            return []
        
        # Start on the dominant (perfect 5th up)
        answer = self.transpose(subject, 7)
        
        # Look for the first +7 semitone leap in the subject and correct it to +5
        if len(subject) >= 2:
            first_interval = subject[1]['pitch'] - subject[0]['pitch']
            if first_interval == 7:  # Perfect 5th up (tonic to dominant)
                # Adjust the answer to use +5 instead of +7 for tonal answer
                answer[1] = Note(
                    pitch=answer[0]['pitch'] + 5,
                    dur=answer[1]['dur'],
                    vel=answer[1]['vel']
                )
        
        return answer
    
    def real_answer(self, subject: Phrase) -> Phrase:
        """Generate a real answer (exact transposition to dominant)."""
        return self.transpose(subject, 7)
    
    def make_entry_plan(self, subject: Phrase, params: FugueParams) -> List[Entry]:
        """Create the entry plan for the exposition."""
        subject_length = sum(note['dur'] for note in subject)
        gap = params.entry_gap_beats or subject_length * (1 - params.stretto_overlap)
        
        entries = []
        for v in range(params.n_voices):
            start_time = v * gap
            
            if v % 2 == 0:  # Even voices get subject
                material = subject
                is_subject = True
            else:  # Odd voices get answer
                if params.use_tonal_answer:
                    material = self.tonal_answer(subject, params.key_root)
                else:
                    material = self.real_answer(subject)
                is_subject = False
            
            entries.append(Entry(
                voice_index=v,
                start_time=start_time,
                material=material,
                is_subject=is_subject
            ))
        
        return entries
    
    def generate_episode(self, subject: Phrase, length_beats: float = 8.0) -> Phrase:
        """Generate an episode based on subject fragments with sequences."""
        if not subject:
            return []
        
        # Choose the most distinctive fragment from the subject
        subject_length = sum(note['dur'] for note in subject)
        
        # Try different fragment positions to find the most interesting one
        fragment_candidates = [
            self.slice_by_time(subject, 0.0, min(2.0, subject_length / 2)),  # Opening
            self.slice_by_time(subject, subject_length / 3, min(subject_length / 3 + 2.0, subject_length)),  # Middle
            self.slice_by_time(subject, max(0, subject_length - 2.0), subject_length),  # Ending
        ]
        
        # Choose the fragment with the most intervallic variety
        best_fragment = max(fragment_candidates, key=lambda f: len(set(n['pitch'] for n in f)) if f else 0)
        
        if not best_fragment:
            best_fragment = subject[:2]  # Fallback to first two notes
        
        # Create a sequence through related keys using circle of fifths
        # Pattern: I -> vi -> ii -> V -> I (or similar)
        sequence_pattern = [0, -3, 2, 7, 0, -5, 2]  # More sophisticated key progression
        
        episode = []
        current_time = 0.0
        
        for i, transpose_amount in enumerate(sequence_pattern):
            if current_time >= length_beats:
                break
            
            # Apply transformation based on position in sequence
            transformed_fragment = self.transpose(best_fragment, transpose_amount)
            
            # Add rhythmic variation
            if i % 3 == 1:  # Every third entry
                # Add some diminution (faster notes)
                transformed_fragment = self.time_scale(transformed_fragment, 0.75)
            elif i % 4 == 3:  # Every fourth entry  
                # Add some augmentation (slower notes)
                transformed_fragment = self.time_scale(transformed_fragment, 1.25)
            
            episode.extend(transformed_fragment)
            current_time += sum(note['dur'] for note in transformed_fragment)
            
            # Add small connecting passages between fragments
            if i < len(sequence_pattern) - 1 and current_time < length_beats - 0.5:
                # Add a connecting note (stepwise motion)
                if episode:
                    last_pitch = episode[-1]['pitch']
                    connecting_note = Note(
                        pitch=last_pitch + random.choice([-2, -1, 1, 2]),
                        dur=0.25,
                        vel=70
                    )
                    episode.append(connecting_note)
                    current_time += 0.25
        
        return episode
    
    def generate_countersubject(self, subject: Phrase) -> Phrase:
        """Generate a countersubject that works contrapuntally with the subject."""
        if not subject:
            return []
        
        # Create a countermelody with complementary rhythm and contour
        countersubject = []
        subject_duration = sum(note['dur'] for note in subject)
        
        # Use opposite rhythmic pattern (if subject has long notes, use short ones)
        subject_avg_duration = subject_duration / len(subject)
        
        if subject_avg_duration > 0.75:  # Subject has long notes
            # Use shorter, more active rhythm
            rhythms = [0.5, 0.5, 0.25, 0.25, 0.5, 1.0]
        else:  # Subject has short notes
            # Use longer, more sustained rhythm
            rhythms = [1.0, 1.0, 2.0]
        
        # Generate complementary pitch contour
        current_time = 0.0
        degree = 2  # Start on scale degree 2 (supertonic)
        
        for duration in rhythms:
            if current_time >= subject_duration:
                break
                
            try:
                pitch = self.scale_mapper.get_note(degree, octave=0)
                countersubject.append(Note(pitch=pitch, dur=duration, vel=80))
                current_time += duration
                
                # Move by step or small leap, preferring contrary motion to subject
                degree += random.choice([-2, -1, 1, 2])
                degree = max(-5, min(10, degree))  # Keep in reasonable range
                
            except Exception:
                # Fallback to simple harmonic interval
                base_pitch = subject[0]['pitch'] if subject else 60
                pitch = base_pitch + random.choice([3, 4, 7, 10])  # 3rd, 4th, 5th, 7th
                countersubject.append(Note(pitch=pitch, dur=duration, vel=80))
        
        return countersubject
    
    def distribute_episode_canonically(self, voices: Score, episode: Phrase, start_time: float):
        """Distribute an episode across voices with canonic imitation."""
        if not episode or not voices:
            return
        
        # Add episode to first voice
        voices[0].extend(episode)
        
        # Add imitations in other voices with time delays
        for voice_idx in range(1, min(len(voices), 3)):  # Max 3 voices for canon
            delay_beats = voice_idx * 2.0  # 2-beat canon
            
            # Choose transformation: transposition or inversion
            if voice_idx % 2 == 1:
                # Transpose up a 4th or 5th
                transformed_episode = self.transpose(episode, random.choice([5, 7]))
            else:
                # Transpose down a 3rd
                transformed_episode = self.transpose(episode, -3)
            
            voices[voice_idx].extend(transformed_episode)
    
    def generate_stretto_section(self, subject: Phrase, params: FugueParams) -> List[Entry]:
        """Generate a stretto section with overlapping subject entries."""
        entries = []
        subject_length = sum(note['dur'] for note in subject)
        overlap_time = subject_length * params.stretto_overlap
        
        # Create 3-4 overlapping entries
        for i in range(min(4, params.n_voices)):
            start_time = i * (subject_length - overlap_time)
            voice_idx = i % params.n_voices
            
            # Alternate between subject and answer
            if i % 2 == 0:
                material = subject
            else:
                material = self.tonal_answer(subject, params.key_root) if params.use_tonal_answer else self.real_answer(subject)
            
            # Apply transformations for variety
            if i >= 2:
                if params.allow_inversion and random.random() < 0.4:
                    axis_pitch = subject[0]['pitch']
                    material = self.invert(material, axis_pitch)
                elif random.random() < 0.3:
                    # Transpose to different octave
                    material = self.transpose(material, random.choice([-12, 12]))
            
            entries.append(Entry(
                voice_index=voice_idx,
                start_time=start_time,
                material=material,
                is_subject=(i % 2 == 0)
            ))
        
        return entries
    
    def generate_complex_episode(self, subject: Phrase, length_beats: float) -> List[Phrase]:
        """Generate a complex episode with multiple voice parts."""
        if not subject:
            return []
        
        # Extract multiple fragments from different parts of the subject
        subject_length = sum(note['dur'] for note in subject)
        fragment1 = self.slice_by_time(subject, 0.0, min(2.0, subject_length / 2))
        fragment2 = self.slice_by_time(subject, subject_length / 2, subject_length)
        
        # Create sequences in different keys (circle of fifths progression)
        key_sequence = [0, 7, 2, -5, 0]  # I-V-ii-IV-I progression
        
        # Generate material for each voice
        voice_parts = []
        current_time = 0.0
        
        # Voice 1: Original fragments in sequence
        voice1 = []
        for i, key_shift in enumerate(key_sequence):
            if current_time >= length_beats:
                break
            fragment = fragment1 if i % 2 == 0 else fragment2
            transposed = self.transpose(fragment, key_shift)
            voice1.extend(transposed)
            current_time += sum(note['dur'] for note in transposed)
        voice_parts.append(voice1)
        
        # Voice 2: Inverted fragments with delay
        voice2 = []
        if fragment1:
            axis_pitch = fragment1[0]['pitch']
            for i, key_shift in enumerate(key_sequence[1:]):  # Start one step later
                if len(voice2) * 0.5 >= length_beats:
                    break
                fragment = fragment2 if i % 2 == 0 else fragment1
                inverted = self.invert(fragment, axis_pitch)
                transposed = self.transpose(inverted, key_shift)
                voice2.extend(transposed)
        voice_parts.append(voice2)
        
        # Voice 3: Augmented fragments (longer note values)
        voice3 = []
        if fragment1:
            augmented_fragment = self.time_scale(fragment1, 2.0)  # Double note values
            for key_shift in [0, 7, -5]:  # Simpler progression for augmented material
                transposed = self.transpose(augmented_fragment, key_shift)
                voice3.extend(transposed)
                if sum(note['dur'] for note in voice3) >= length_beats:
                    break
        voice_parts.append(voice3)
        
        return voice_parts
    
    def generate_cadence(self, subject: Phrase, key_root: int) -> Phrase:
        """Generate a cadential passage to conclude the fugue."""
        try:
            # Simple authentic cadence: V-I motion
            cadence = [
                Note(pitch=self.scale_mapper.get_note(4, octave=0), dur=1.0, vel=90),  # Dominant
                Note(pitch=self.scale_mapper.get_note(0, octave=0), dur=2.0, vel=96),  # Tonic
            ]
            return cadence
        except Exception:
            # Fallback cadence
            return [
                Note(pitch=key_root + 7, dur=1.0, vel=90),  # G in C major/minor
                Note(pitch=key_root, dur=2.0, vel=96),      # C in C major/minor
            ]
    
    def render_fugue(self, subject: Phrase, params: FugueParams) -> Score:
        """Render a complete fugue according to the specification."""
        log.info("Starting fugue generation")
        
        # Step 1: Build entry plan (exposition)
        entries = self.make_entry_plan(subject, params)
        
        # Calculate total fugue length (max 5 minutes as per requirements)
        max_duration_beats = 5 * 60 * (120 / 60) * (1/4)  # 5 min at 120 BPM in quarter notes
        subject_length = sum(note['dur'] for note in subject)
        exposition_end = max(e.start_time + sum(n['dur'] for n in e.material) for e in entries)
        
        # Step 2: Initialize voices with timed events
        voices = [[] for _ in range(params.n_voices)]
        current_time = 0.0
        
        # Step 3: Place exposition entries
        for entry in entries:
            voice = voices[entry.voice_index]
            # Add the material - we'll track timing separately
            voice.extend(entry.material)
        
        # Track the current position in the fugue for additional sections
        current_time = exposition_end
        
        # Step 4: Generate countersubject if not provided
        countersubject = self.generate_countersubject(subject)
        
        # Step 5: Add first episode (developmental passage)
        if current_time < max_duration_beats - 32.0:
            episode1_length = min(16.0, max_duration_beats - current_time - 24.0)
            episode1 = self.generate_episode(subject, episode1_length)
            if episode1:
                # Distribute episode across voices with canonic imitation
                self.distribute_episode_canonically(voices, episode1, current_time)
                current_time += episode1_length
        
        # Step 6: Subject re-entries in related keys (circle of fifths)
        related_keys = [7, -5, 2, -10]  # Dominant, subdominant, supertonic, etc.
        for i, key_shift in enumerate(related_keys):
            if current_time >= max_duration_beats - 16.0:
                break
                
            # Add subject entry in related key
            entry_voice = i % params.n_voices
            transposed_subject = self.transpose(subject, key_shift)
            voices[entry_voice].extend(transposed_subject)
            
            # Add countersubject in another voice
            if len(voices) > 1:
                counter_voice = (entry_voice + 1) % params.n_voices
                voices[counter_voice].extend(countersubject)
            
            current_time += subject_length + 2.0  # 2 beats gap
            
            # Add a short episode between entries
            if i < len(related_keys) - 1 and current_time < max_duration_beats - 20.0:
                mini_episode = self.generate_episode(subject, 8.0)
                if mini_episode:
                    episode_voice = (entry_voice + 2) % params.n_voices
                    voices[episode_voice].extend(mini_episode)
                    current_time += 8.0
        
        # Step 7: Add stretto section if overlap parameter allows
        if params.stretto_overlap > 0.1 and current_time < max_duration_beats - 20.0:
            stretto_entries = self.generate_stretto_section(subject, params)
            for entry in stretto_entries:
                if entry.voice_index < len(voices):
                    voices[entry.voice_index].extend(entry.material)
            current_time += 12.0  # Stretto section length
        
        # Step 8: Final episode with increased complexity
        if current_time < max_duration_beats - 16.0:
            final_episode_length = min(12.0, max_duration_beats - current_time - 8.0)
            final_episode = self.generate_complex_episode(subject, final_episode_length)
            if final_episode:
                # Use multiple voices for richer texture
                for i, voice_part in enumerate(final_episode[:params.n_voices]):
                    voices[i].extend(voice_part)
                current_time += final_episode_length
        
        # Step 9: Final subject statement in home key (tonic)
        if current_time < max_duration_beats - subject_length:
            # Add final subject in tonic with full harmonic support
            voices[0].extend(subject)
            if len(voices) > 1:
                voices[1].extend(countersubject)
            
            # Add cadential material
            cadence = self.generate_cadence(subject, params.key_root)
            if cadence and len(voices) > 2:
                voices[2].extend(cadence)
        
        log.info(f"fugue_generated voices={len(voices)} exposition_entries={len(entries)} total_duration={current_time:.1f}")
        return voices


class FugueSequencer:
    """Handles fugue playback within the main sequencer framework."""
    
    def __init__(self, state: State, scale_mapper: ScaleMapper):
        self.state = state
        self.scale_mapper = scale_mapper
        self.fugue_engine = FugueEngine(scale_mapper)
        
        # Fugue state
        self._active_fugue: Optional[Score] = None
        self._fugue_start_time: float = 0.0
        self._fugue_params: Optional[FugueParams] = None
        self._last_fugue_end: float = 0.0
        self._rest_duration: float = 10.0  # 10 seconds between fugues (reduced from 10)
        
        # Musical timing state (tracks the fugue's internal musical time)
        self._fugue_musical_time: float = 0.0  # Current time in quarter notes
        self._voice_next_times: List[float] = []  # Next note time for each voice
        self._voice_positions: List[int] = []     # Current note index per voice
        
        log.info("fugue_sequencer_initialized")
    
    def start_new_fugue(self):
        """Start a new fugue generation and playback."""
        # Generate parameters from current state
        self._fugue_params = FugueParams(
            n_voices=min(4, max(2, self.state.get('sequence_length', 8) // 4)),
            key_root=self.state.get('root_note', 60),
            mode=self.state.get('scale_mode', 'minor'),
            entry_gap_beats=2.0,
            stretto_overlap=self.state.get('density', 0.5) * 0.5,  # Higher density = more stretto
            use_tonal_answer=True,
            episode_density=self.state.get('density', 0.5),
        )
        
        # Generate subject
        subject = self.fugue_engine.generate_subject(self._fugue_params, bars=1)
        
        # Generate complete fugue
        self._active_fugue = self.fugue_engine.render_fugue(subject, self._fugue_params)
        self._fugue_start_time = time.perf_counter()
        
        # Initialize musical timing
        self._fugue_musical_time = 0.0
        
        # Calculate when each voice's first note should play
        entries = self.fugue_engine.make_entry_plan(subject, self._fugue_params)
        self._voice_next_times = [entry.start_time for entry in entries]
        self._voice_positions = [0] * len(self._active_fugue)
        
        log.info(f"fugue_started voices={len(self._active_fugue)} entry_times={self._voice_next_times} total_notes={sum(len(v) for v in self._active_fugue)}")
    
    def should_start_new_fugue(self) -> bool:
        """Check if it's time to start a new fugue."""
        current_time = time.perf_counter()
        
        # If no active fugue and rest period has passed
        if self._active_fugue is None:
            if current_time - self._last_fugue_end >= self._rest_duration:
                log.info(f"starting_new_fugue rest_period_elapsed={current_time - self._last_fugue_end:.1f}s")
                return True
            else:
                log.debug(f"waiting_for_rest_period remaining={self._rest_duration - (current_time - self._last_fugue_end):.1f}s")
                return False
        
        # If current fugue has been running for more than 5 minutes
        if current_time - self._fugue_start_time >= 300.0:  # 5 minutes
            self._active_fugue = None
            self._last_fugue_end = current_time
            log.info("fugue_completed max_duration_reached")
            return False
        
        return False
    
    def get_next_step_note(self, step: int) -> Optional[Tuple[int, int, float]]:
        """Get the next note for the current step in fugue mode.
        
        This method is called on each sequencer step and determines if any
        fugue voices should play notes at this moment based on sequencer timing.
        
        Returns:
            Tuple of (pitch, velocity, duration) or None if no note
        """
        if not self._active_fugue:
            if self.should_start_new_fugue():
                self.start_new_fugue()
            else:
                return None
        
        if not self._active_fugue:
            return None
        
        # Calculate musical time progression based on sequencer steps
        # Each step represents a 16th note (1/4 quarter note)
        bpm = self.state.get('bpm', 110.0)
        quarter_note_duration = 60.0 / bpm
        step_duration = quarter_note_duration / 4  # 16th note duration
        
        # Update musical time based on step progression
        # Each call advances by one 16th note (0.25 quarter notes)
        self._fugue_musical_time += 0.25
        
        # Check each voice to see if it's time to play its next note
        for voice_idx in range(len(self._active_fugue)):
            voice = self._active_fugue[voice_idx]
            
            # Skip if this voice is exhausted
            if self._voice_positions[voice_idx] >= len(voice):
                continue
            
            # Check if it's time for this voice's next note
            if self._fugue_musical_time >= self._voice_next_times[voice_idx]:
                note = voice[self._voice_positions[voice_idx]]
                
                # Schedule next note for this voice
                self._voice_next_times[voice_idx] += note['dur']
                self._voice_positions[voice_idx] += 1
                
                # Convert duration to seconds
                duration_seconds = note['dur'] * quarter_note_duration
                
                log.debug(f"fugue_note voice={voice_idx} musical_time={self._fugue_musical_time:.2f} "
                         f"note={note['pitch']} dur={duration_seconds:.3f}s")
                
                return (note['pitch'], note['vel'], duration_seconds)
        
        # Check if all voices are exhausted
        all_exhausted = all(
            pos >= len(voice) 
            for pos, voice in zip(self._voice_positions, self._active_fugue)
        )
        
        if all_exhausted:
            self._active_fugue = None
            self._last_fugue_end = time.perf_counter()
            log.info(f"fugue_completed all_voices_exhausted musical_time={self._fugue_musical_time:.2f}")
        
        return None


def create_fugue_sequencer(state: State, scale_mapper: ScaleMapper) -> FugueSequencer:
    """Factory function to create a fugue sequencer instance."""
    return FugueSequencer(state, scale_mapper)
