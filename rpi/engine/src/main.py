import time
import logging
import argparse
from typing import Optional
from config import load_config
from router import Router
from midi_in import MidiInput
from events import SemanticEvent
from logging_utils import configure_logging
from state import get_state, reset_state
from sequencer import create_sequencer, NoteEvent
from action_handler import ActionHandler


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
    log.info("engine_start phase=2 version=0.2.0")
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
    
    # Set up note callback for sequencer-generated notes
    def handle_note_event(note_event: NoteEvent):
        log.info(f"note_event note={note_event.note} velocity={note_event.velocity} step={note_event.step}")
        # TODO Phase 3+: Send to synthesis backend
    
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
            midi.close()
        except Exception:  # noqa: broad-except
            log.exception("shutdown_error")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
