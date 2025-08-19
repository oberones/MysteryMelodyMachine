# Mystery Music Engine (Phase 2)

Phase 2 implements state management and basic sequencer functionality (see root `SPEC.md` + `docs/RPiSoftwareRoadmap.md`).

## Implemented

### Phase 1 (MIDI & Routing)
- Auto / explicit MIDI port selection (prefers name containing 'teensy').
- Config-driven mapping (note ranges + CC) -> action strings.
- Emission + logging of `SemanticEvent` objects.
- Structured key=value logging formatter.
- Unit tests for config load, routing, channel filtering, ignoring unmapped inputs, invalid range handling, MIDI auto-select edge cases.

### Phase 2 (State & Sequencer)
- Observable state container with parameter validation and change listeners.
- High-resolution clock with drift correction and swing support.
- Basic sequencer with step management and configurable sequence length.
- Action handler translating semantic events to state changes and sequencer operations.
- Manual step triggering via button presses with immediate note generation.
- Real-time parameter updates (tempo, swing, density, sequence length, etc.).
- Comprehensive test suite for all Phase 2 components.

## Run

**IMPORTANT**: All Python operations must be performed within the virtual environment.

```bash
# Activate virtual environment (from project root)
source .venv/bin/activate

# Install dependencies
pip install -r rpi/engine/requirements.txt

# Run tests
pytest rpi/engine/tests -q

# Run engine
python rpi/engine/src/main.py --config rpi/engine/config.yaml --log-level INFO
```

Example log lines:
```
ts=2025-08-19T12:00:00 level=INFO logger=engine msg=semantic type=trigger_step source=button value=100 note=60 ch=1
ts=2025-08-19T12:00:00 level=INFO logger=engine msg=note_event note=60 velocity=100 step=0
ts=2025-08-19T12:00:01 level=DEBUG logger=sequencer msg=step_advance step=1 length=8
```

Set `ENGINE_DEBUG_TIMING=1` for extra timing debug categories (future phases).

## Architecture (Phase 2)

```
MIDI Input → Router → Action Handler → State Container
                           ↓              ↓
                    Note Events    State Changes
                           ↓              ↓
                    Audio Backend   Sequencer Clock
                                         ↓
                                  Step Events → Note Generation
```

## Key Components

- **State**: Observable parameter store with validation and change notifications
- **Sequencer**: High-resolution clock with step management and note generation
- **ActionHandler**: Bridges semantic events to state changes and sequencer operations
- **HighResClock**: Precise timing with swing support and drift correction

## Current Capabilities

- Real-time tempo changes (60-200 BPM)
- Swing adjustment (0-50%)
- Sequence length control (1-32 steps)
- Manual step triggering via button presses
- Automatic step advancement with configurable timing
- Parameter validation and clamping
- Structured logging of all events

## Next (Phase 3)
- Probability density gating for step events.
- Scale mapping with real-time scale changes.
- Note probability per step with configurable patterns.

License: Apache-2.0
