# Mystery Music Engine (Phase 5.5)

Phase 5.5 implements enhanced probability & rhythm patterns with per-step control (see root `SPEC.md` + `docs/ROADMAP.md`).

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
- **Complete configuration logging** - All settings logged at startup for transparency.

### Phase 3 (Scale Mapping & Probability)
- Scale mapping with real-time scale changes and quantized transitions.
- Probability density gating for step events.
- Basic note probability per step.

### Phase 4 (Integration & Polish)
- Full integration of scale mapping with sequencer.
- Enhanced probability gating with density control.
- Quantized parameter changes on bar boundaries.

### Phase 5 (Mutation Engine)
- Automated parameter mutations with configurable schedules.
- BPM drift envelopes for organic tempo variation.
- Mutation logging and state tracking.

### Phase 5.5 (Enhanced Probability & Rhythm Patterns) ✨ **NEW**
- **Per-step probability arrays** - Individual probability control for each step.
- **Configurable step patterns** - Flexible rhythm patterns beyond hardcoded sequences.
- **Direction patterns** - Multiple sequencer playback directions (forward, backward, ping-pong, random).
- **Velocity variation** - Dynamic velocity based on probability values with randomness.
- **Pattern & probability presets** - Ready-to-use rhythm and probability templates.
- **Backward compatibility** - All existing configurations continue to work unchanged.

## Run

**IMPORTANT**: All Python operations must be performed within the virtual environment.

```bash
# Activate virtual environment (from engine directory)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests -q

# Run engine
python src/main.py --config config.yaml --log-level INFO

# Run Phase 5.5 demo (shows new features)
python demo_phase5_5.py

# Run direction patterns demo (detailed direction pattern showcase)
python demo_direction_patterns.py

# Run configuration logging demo
python demo_config_logging.py
```

Example log lines:
```
ts=2025-08-20T12:00:00 level=INFO logger=engine msg=semantic type=trigger_step source=button value=100 note=60 ch=1
ts=2025-08-20T12:00:00 level=INFO logger=engine msg=note_event note=60 velocity=100 step=0
ts=2025-08-20T12:00:01 level=DEBUG logger=sequencer msg=step_advance step=1 length=8
ts=2025-08-20T12:00:01 level=INFO logger=sequencer msg=step_probabilities_set length=8 values=[1.0, 0.8, 0.6, 0.4, 0.2, 0.6, 0.8, 1.0]
ts=2025-08-20T12:00:01 level=INFO logger=sequencer msg=step_pattern_set length=8 pattern=[True, False, True, True, False, False, True, False]
ts=2025-08-20T12:00:01 level=DEBUG logger=sequencer msg=note_generated step=0 note=60 velocity=95 step_prob=1.00
```

Set `ENGINE_DEBUG_TIMING=1` for extra timing debug categories (future phases).

## Architecture (Phase 5.5)

```
MIDI Input → Router → Action Handler → State Container
                           ↓              ↓
                    Note Events    State Changes
                           ↓              ↓
                    Audio Backend   Sequencer Clock
                                         ↓
                              Step Events → Pattern Gate
                                         ↓
                              Probability Gate (Per-Step)
                                         ↓
                              Scale Mapper → Note Generation
                                         ↓
                              Velocity Variation → Audio Output
```

## Key Components

- **State**: Observable parameter store with validation and change notifications
- **Sequencer**: High-resolution clock with step management and enhanced note generation
- **ActionHandler**: Bridges semantic events to state changes and sequencer operations
- **HighResClock**: Precise timing with swing support and drift correction
- **Pattern System**: Configurable step activation patterns with presets ✨
- **Probability Engine**: Per-step probability control with preset templates ✨
- **Direction Engine**: Multiple sequencer playback directions (forward, backward, ping-pong, random) ✨
- **Velocity Engine**: Dynamic velocity variation based on probability values ✨

## Current Capabilities

- Real-time tempo changes (60-200 BPM)
- Swing adjustment (0-50%)
- Sequence length control (1-32 steps)
- Manual step triggering via button presses
- Automatic step advancement with configurable timing
- Parameter validation and clamping
- Structured logging of all events
- Scale mapping with multiple scales and real-time switching
- Probability density gating for overall sparseness control
- Per-step probability arrays for fine-grained control
- Configurable step patterns for flexible rhythm creation
- Dynamic velocity variation based on probability values
- Automated parameter mutations for evolving soundscapes

## Configuration Parameters

### Core Sequencer Parameters
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `bpm` | float | 60.0-200.0 | 110.0 | Beats per minute |
| `swing` | float | 0.0-0.5 | 0.12 | Swing amount (0=straight, 0.5=max swing) |
| `density` | float | 0.0-1.0 | 0.85 | Overall probability gate for all steps |
| `sequence_length` | int | 1-32 | 8 | Number of steps in the sequence |

### Legacy Probability (Backward Compatibility)
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `note_probability` | float | 0.0-1.0 | 0.9 | Global note probability (used when step_probabilities is None) |

### Phase 5.5: Enhanced Patterns & Probability ✨
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `step_probabilities` | array | [0.0-1.0, ...] | None | Per-step probability values (overrides note_probability) |
| `step_pattern` | array | [bool, ...] | None | Per-step activation pattern (overrides hardcoded even-step pattern) |
| `direction_pattern` | string | See Direction Patterns | 'forward' | Sequencer playback direction |
| `base_velocity` | int | 1-127 | 80 | Base MIDI velocity for notes |
| `velocity_range` | int | 0-127 | 40 | Range for velocity variation (+/- from base) |

### Scale & Mapping
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `scale_index` | int | 0-N | 0 | Index into available scales list |
| `root_note` | int | 0-127 | 60 | Root note for scale (MIDI note number) |

## Pattern Presets 🎵

Use `sequencer.get_pattern_preset(preset_name)` to get predefined step patterns:

| Preset Name | Pattern | Description |
|-------------|---------|-------------|
| `four_on_floor` | `[T,F,F,F,T,F,F,F]` | Classic 4/4 kick pattern |
| `offbeat` | `[F,T,F,T,F,T,F,T]` | Emphasis on off-beats |
| `every_other` | `[T,F,T,F,T,F,T,F]` | Alternating on/off pattern |
| `syncopated` | `[T,F,T,T,F,T,F,F]` | Syncopated rhythm with emphasis shifts |
| `dense` | `[T,T,F,T,T,F,T,T]` | High-density pattern with occasional rests |
| `sparse` | `[T,F,F,F,F,F,T,F]` | Minimal pattern with long gaps |
| `all_on` | `[T,T,T,T,T,T,T,T]` | Every step active |
| `all_off` | `[F,F,F,F,F,F,F,F]` | Every step inactive |

*T=True (step active), F=False (step inactive)*

## Direction Patterns 🎯

Use `sequencer.set_direction_pattern(pattern_name)` to control sequencer playback direction:

| Pattern Name | Description | Behavior |
|-------------|-------------|-----------|
| `forward` | Standard left-to-right playback | Steps advance 0→1→2→3...→N→0 |
| `backward` | Right-to-left playback | Steps advance N→...→3→2→1→0→N |
| `ping_pong` | Bouncing back and forth | Steps advance 0→1→2→3→2→1→0→1... |
| `random` | Random step selection | Each step chooses randomly from all other steps |

**Default**: `forward` (maintains backward compatibility)

## Probability Presets 🎲

Use `sequencer.get_probability_preset(preset_name, length)` to get predefined probability patterns:

| Preset Name | Description | Example (8 steps) |
|-------------|-------------|-------------------|
| `uniform` | Equal probability for all steps | `[0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]` |
| `crescendo` | Gradually increasing probability | `[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.9]` |
| `diminuendo` | Gradually decreasing probability | `[0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3]` |
| `peaks` | High probability every 4th step | `[0.9, 0.4, 0.4, 0.4, 0.9, 0.4, 0.4, 0.4]` |
| `valleys` | Low probability every 4th step | `[0.3, 0.8, 0.8, 0.8, 0.3, 0.8, 0.8, 0.8]` |
| `alternating` | High/low alternating pattern | `[0.9, 0.3, 0.9, 0.3, 0.9, 0.3, 0.9, 0.3]` |
| `random_low` | Random values in low range | `[0.2-0.6 random values]` |
| `random_high` | Random values in high range | `[0.6-1.0 random values]` |

## Usage Examples

### Setting Custom Step Probabilities
```python
# Set individual probabilities for each step
sequencer.set_step_probabilities([1.0, 0.8, 0.6, 0.4, 0.2, 0.6, 0.8, 1.0])

# Or use a preset
probs = sequencer.get_probability_preset('crescendo', length=8)
sequencer.set_step_probabilities(probs)
```

### Setting Custom Step Patterns
```python
# Set a custom pattern
sequencer.set_step_pattern([True, False, True, True, False, False, True, False])

# Or use a preset
pattern = sequencer.get_pattern_preset('syncopated')
sequencer.set_step_pattern(pattern)
```

### Setting Direction Patterns
```python
# Set direction pattern
sequencer.set_direction_pattern('ping_pong')

# Or use a preset (validates the name)
direction = sequencer.get_direction_preset('backward')
sequencer.set_direction_pattern(direction)
```

### Configuring Velocity Variation
```python
# Set base velocity and variation range
sequencer.set_velocity_params(base_velocity=100, velocity_range=30)
# Results in velocities ranging roughly from 70-130 based on step probability
```

### Backward Compatibility
```python
# Old-style configuration still works
state.set('note_probability', 0.7)  # Applied to all steps when step_probabilities is None
# Hardcoded even-step pattern used when step_pattern is None
```

## Next (Phase 6)
- Idle mode detection and handling.
- Additional scale mapping enhancements.
- LED control integration with Teensy firmware.

License: Apache-2.0
