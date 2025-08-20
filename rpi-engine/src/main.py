import time
import logging
import argparse
import threading
from typing import Optional
from dataclasses import dataclass
from config import load_config
from router import Router
from midi_in import MidiInput
from midi_out import MidiOutput, NullMidiOutput
from events import SemanticEvent
from logging_utils import configure_logging
from state import get_state, reset_state
from sequencer import create_sequencer, NoteEvent
from action_handler import ActionHandler


@dataclass
class ScheduledNoteOff:
    """Represents a scheduled note off event."""
    note: int
    channel: int
    timestamp: float


class NoteScheduler:
    """Handles scheduling of note off events for proper MIDI note timing."""
    
    def __init__(self, midi_output):
        self.midi_output = midi_output
        self._scheduled_notes: list[ScheduledNoteOff] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the note scheduler thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_thread, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the note scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def schedule_note_off(self, note: int, channel: int, delay: float):
        """Schedule a note off event after the specified delay."""
        timestamp = time.time() + delay
        scheduled = ScheduledNoteOff(note, channel, timestamp)
        
        with self._lock:
            self._scheduled_notes.append(scheduled)
            # Keep list sorted by timestamp for efficiency
            self._scheduled_notes.sort(key=lambda x: x.timestamp)
    
    def _scheduler_thread(self):
        """Main scheduler thread that processes note off events."""
        while self._running:
            current_time = time.time()
            notes_to_remove = []
            
            with self._lock:
                # Process all notes that are due
                for scheduled in self._scheduled_notes:
                    if scheduled.timestamp <= current_time:
                        # Send note off
                        self.midi_output.send_note_off(scheduled.note, 0, scheduled.channel)
                        notes_to_remove.append(scheduled)
                    else:
                        # List is sorted, so we can break here
                        break
                
                # Remove processed notes
                for note in notes_to_remove:
                    self._scheduled_notes.remove(note)
            
            # Sleep for a short time to avoid busy waiting
            time.sleep(0.001)  # 1ms resolution


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mystery Music Engine Phase 2")
    p.add_argument("--config", default="rpi/engine/config.yaml", help="Path to config YAML")
    p.add_argument("--log-level", default=None, help="Override log level (DEBUG/INFO/...)")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None):
    args = parse_args(argv)
    cfg = load_config(args.config)
    level = args.log_level or cfg.logging.level
    configure_logging(level)
    log = logging.getLogger("engine")
    log.info("engine_start phase=3 version=0.3.0")
    log.debug("config_loaded json=%s", cfg.json())

    # Initialize state and sequencer
    state = get_state()
    
    # Initialize state from config
    state.update_multiple({
        'bpm': cfg.sequencer.bpm,
        'swing': cfg.sequencer.swing,
        'density': cfg.sequencer.density,
        'sequence_length': cfg.sequencer.steps,
    }, source='config')
    
    # Create sequencer
    sequencer = create_sequencer(state, cfg.scales)
    
    # Create action handler
    action_handler = ActionHandler(state, sequencer)
    
    # Initialize MIDI output (optional)
    midi_output = MidiOutput.create(cfg.midi.output_port, cfg.midi.output_channel)
    if midi_output:
        log.info(f"MIDI output enabled on port: {cfg.midi.output_port}")
    else:
        midi_output = NullMidiOutput()
        log.info("MIDI output disabled")
    
    # Initialize note scheduler for proper note off timing
    note_scheduler = NoteScheduler(midi_output)
    note_scheduler.start()
    
    # Set up note callback for sequencer-generated notes
    def handle_note_event(note_event: NoteEvent):
        log.info(f"note_event note={note_event.note} velocity={note_event.velocity} step={note_event.step} duration={note_event.duration:.3f}")
        
        # Send MIDI output if enabled
        if midi_output.is_connected:
            # Send note on immediately
            midi_output.send_note_on(note_event.note, note_event.velocity, cfg.midi.output_channel)
            # Schedule note off after duration
            note_scheduler.schedule_note_off(note_event.note, cfg.midi.output_channel, note_event.duration)
        
        # TODO Phase 4+: Send to synthesis backend
    
    sequencer.set_note_callback(handle_note_event)
    action_handler.set_note_callback(handle_note_event)
    
    # Set up semantic event handling
    def handle_semantic(evt: SemanticEvent):
        log.info("semantic %s", evt.log_str())
        action_handler.handle_semantic_event(evt)

    router = Router(cfg, handle_semantic)
    try:
        midi = MidiInput.create(cfg.midi.input_port, router.route)
    except Exception as e:  # noqa: broad-except
        log.error("midi_open_failed error=%s", e)
        return 2

    # Start sequencer
    sequencer.start()
    log.info("sequencer_started")

    try:
        while True:
            time.sleep(1.0)
            # Log current state periodically for debugging
            if log.isEnabledFor(logging.DEBUG):
                current_state = state.get_all()
                log.debug(f"state_snapshot {current_state}")
    except KeyboardInterrupt:
        log.info("shutdown signal=keyboard_interrupt")
    finally:
        try:
            sequencer.stop()
            note_scheduler.stop()
            midi.close()
            if midi_output:
                midi_output.close()
        except Exception:  # noqa: broad-except
            log.exception("shutdown_error")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
