import time
import logging
import argparse
from typing import Optional
from config import load_config
from router import Router
from midi_in import MidiInput
from events import SemanticEvent
from logging_utils import configure_logging


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mystery Music Engine Phase 1")
    p.add_argument("--config", default="rpi/engine/config.yaml", help="Path to config YAML")
    p.add_argument("--log-level", default=None, help="Override log level (DEBUG/INFO/...)")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None):
    args = parse_args(argv)
    cfg = load_config(args.config)
    level = args.log_level or cfg.logging.level
    configure_logging(level)
    log = logging.getLogger("engine")
    log.info("engine_start phase=1 version=0.1.0")
    log.debug("config_loaded json=%s", cfg.json())

    def handle_semantic(evt: SemanticEvent):
        log.info("semantic %s", evt.log_str())

    router = Router(cfg, handle_semantic)
    try:
        midi = MidiInput.create(cfg.midi.input_port, router.route)
    except Exception as e:  # noqa: broad-except
        log.error("midi_open_failed error=%s", e)
        return 2

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        log.info("shutdown signal=keyboard_interrupt")
    finally:
        try:
            midi.close()
        except Exception:  # noqa: broad-except
            log.exception("midi_close_failed")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
