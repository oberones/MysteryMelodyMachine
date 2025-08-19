# Mystery Music Engine (Phase 1)

Phase 1 implements MIDI ingress and semantic routing (see root `SPEC.md` + `docs/RPiSoftwareRoadmap.md`).

## Implemented
- Auto / explicit MIDI port selection (prefers name containing 'teensy').
- Config-driven mapping (note ranges + CC) -> action strings.
- Emission + logging of `SemanticEvent` objects.
- Structured key=value logging formatter.
- Unit tests for config load, routing, channel filtering, ignoring unmapped inputs, invalid range handling, MIDI auto-select edge cases.

## Run
```powershell
pip install -r rpi/engine/requirements.txt
pytest rpi/engine/tests -q
python rpi/engine/src/main.py --config rpi/engine/config.yaml --log-level INFO
```

Example log line:
```
ts=2025-08-18T12:00:00 level=INFO logger=engine msg=semantic type=trigger_step source=button value=100 note=60 ch=1
```

Set `ENGINE_DEBUG_TIMING=1` for extra timing debug categories (future phases).

## Next (Phase 2)
- State container & sequencer tick loop.
- Probability density gating.
- Scale change handling at bar boundary (config already prepared).

License: Apache-2.0
