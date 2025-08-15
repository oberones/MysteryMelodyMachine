import time
import logging
from config import load_config

CONFIG_PATH = "config.yaml"


def setup_logging(level: str):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main():
    cfg = load_config(CONFIG_PATH)
    setup_logging(cfg.logging.level)
    log = logging.getLogger("engine")
    log.info("Mystery Music Engine starting (SuperCollider backend placeholder)")
    log.debug("Loaded config: %s", cfg.json())

    # TODO: Initialize MIDI, Sequencer, SuperCollider connection, LED cue emitter
    try:
        while True:
            # Placeholder main loop (will integrate clock & event handling)
            time.sleep(1.0)
    except KeyboardInterrupt:
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
