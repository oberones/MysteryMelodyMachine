# Raspberry Pi Generative Engine Software Roadmap

Target Platform: Raspberry Pi 4 (2–4 GB RAM)
Primary Role: Receive USB MIDI from Teensy, apply mapping + transformation + generative logic, synthesize / route audio, emit minimal LED cue messages to Teensy, expose logging.

Decided Tech Stack (per clarifications):
- Core Language: Python 3.11 (supervision, logic, routing)
- MIDI I/O: `mido` + `python-rtmidi`
- Audio Synthesis Backend: SuperCollider (`scsynth`) driven via OSC (`python-osc`)
- LED Control: Firmware (Teensy) owns animations; Pi sends only abstract cue events (note, param, mode, idle enter/exit)
- Optional future backends (PD/pyo) deferred

---
## 1. Goals & Non-Goals
### Core Goals
- Deterministic real-time mapping from incoming MIDI events to generative engine state changes.
- Layered generative architecture (input layer, state model, sequencer, probability & mutation, scale mapper, synthesis drivers, LED event bus).
- Hot-reload / rapid iteration of rules & mappings (editable config / YAML / JSON / Python plugin modules).
- Robust logging + introspection (metrics & state snapshot endpoints).
- Idle detection & adaptive behavior (ambient mode after 30 s inactivity).
- Modular audio backend abstraction (swap PD, SuperCollider, Python-native synthesis).

### Non-Goals (Push to Firmware or Future)
- Physical input scanning (Teensy handles low-level hardware)
- Heavy GUI (maybe a lightweight status endpoint later)
- Persistent user content management (beyond simple presets / JSON state)
- High-bandwidth LED frame streaming (handled by Teensy animations)

---
## 2. High-Level Architecture
```
                +---------------------------+
USB MIDI  --->  |  MIDI In Adapter          |
                +------------+--------------+
                             |
                             v
                +---------------------------+
                |  Event Router / Mapper    |  (maps raw Notes/CC -> semantic intents)
                +------------+--------------+
                             |
                             v
                +---------------------------+
                |  State Model / Parameter  |  (tempo, scale, density, modes, flags)
                +------------+--------------+
                             | (queries)
                             v
                +---------------------------+
                | Sequencer Core (steps)    |  (probability, drift, mutation)
                +------------+--------------+
                             |
                  +----------+-----------+
                  |                      |
                  v                      v
        +----------------+      +-------------------+
        | Scale Mapper   |      | Mutation Engine   |
        +--------+-------+      +---------+---------+
                 |                        |
                 v                        |
        +----------------+                |
        | Note Stream    |<---------------+
        +--------+-------+
                 |
                 v
        +----------------+        +------------------+
        | Synth Adapter  |  --->  | Audio Backend(s) |
        +----------------+        +------------------+
                 |
                 v
        +----------------+
        | LED Event Bus  |  (emit abstract LED cues -> Teensy or local LEDs)
        +----------------+

        +----------------+
        | Monitoring API | (web / CLI / OSC / metrics)
        +----------------+
```

---
## 3. Module Breakdown
| Module | Responsibility | Key Concepts | Deliverables |
|--------|----------------|--------------|--------------|
| `midi_in` | Open and parse MIDI events | Port discovery, event queue | Python module / PD patch gateway |
| `router` | Map raw Note/CC -> semantic actions | Config-driven rules | YAML/JSON + Python loader |
| `state` | Central parameter store | Observable pattern, version stamping | Class + getter/setter events |
| `sequencer` | Step timing, probability gating | Clock, drift, density factors | Tick driver + pattern abstraction |
| `scale_mapper` | Map pitch -> scale | Scale definitions, transposition | Library module |
| `mutation` | Periodic param changes | Weighted random scheduling | Scheduler + rule registry |
| `synth_adapter` | Uniform interface to backend | Strategy pattern | `play_note`, `set_param` |
| `backend_pd/sc/pyo` | Concrete audio generation | OSC, direct API | Backend drivers |
| `led_bus` | Publish LED intents | JSON messages, OSC, serial | Pluggable endpoint |
| `idle_manager` | Detect inactivity & trigger mode | Event timestamps | Idle state transitions |
| `config` | Load + validate structured config | Schema validation (`pydantic`) | Config objects |
| `logging/metrics` | Structured logs + counters | `logging`, `prometheus_client` | Exposed metrics endpoint |
| `api` | Optional web/OSC interface | FastAPI / aiohttp + OSC server | Control + introspection |
| `persistence` | Preset save/load (optional) | JSON snapshot | Save/restore functions |
| `cli` | Launch / manage processes | Argparse / Typer | `main.py` |
| `tests` | Unit/integration tests | Pytest | Test suite |

---
## 4. Configuration Model (Draft)
`config.yaml` example snippet (updated for SuperCollider + bar-quantized scale changes):
```yaml
midi:
  input_port: auto
  channel: 1
mapping:
  buttons:
    60-71: trigger_step   # map notes range to generic trigger action
  ccs:
    20: tempo
    21: filter_cutoff
    22: reverb_mix
    23: swing
    24: density
    25: master_volume
    50: sequence_length
    51: scale_select
    52: chaos_lock
    53: reserved
    60: mode
    61: palette
    62: drift
sequencer:
  steps: 8
  bpm: 110
  swing: 0.12
  density: 0.85
  quantize_scale_changes: bar   # enforce at bar boundary
scales: [major, minor, pentatonic]
mutation:
  interval_min_s: 120
  interval_max_s: 240
  max_changes_per_cycle: 2
idle:
  timeout_ms: 30000
  ambient_profile: slow_fade
  fade_in_ms: 4000
  fade_out_ms: 800
synth:
  backend: supercollider
  voices: 8   # adjustable; TBD if higher polyphony needed
logging:
  level: INFO
api:
  enabled: true
  port: 8080
```

---
## 5. Data Flow (Event Lifecycle)
1. MIDI event arrives (Note/CC).
2. Router consults mapping config → emits semantic action (e.g., `ACTION_SET_TEMPO`, `ACTION_TRIGGER_GATE`).
3. State updates value (with validation + range clamp) OR sequencer receives trigger.
4. Sequencer generates note events on tick boundaries (honoring probability, density, drifted clock).
5. Scale mapper adjusts pitch set.
6. Synth adapter schedules audio backend calls.
7. LED bus receives summarised cues (e.g., `pot_move`, `mode_change`, `note_trigger`).
8. Metrics/logging record event latencies & counts.

---
## 6. Clock & Timing Strategy
- Master clock derived from BPM → tick interval = 60000 / (BPM * PPQ).
- Use high-resolution monotonic timer & drift correction (accumulate fractional remainder).
- Swing: alter timing of even/odd beats by ± swing factor.
- Drift parameter: Slowly modulate BPM within ±X% envelope.

---
## 7. Mutation Engine
- Scheduler picks random time in `[interval_min_s, interval_max_s]`.
- Select up to `max_changes_per_cycle` parameters based on weighted categories.
- Apply small bounded delta (e.g., density ±0.05) with clamp.
- Emit event log + LED cue.

---
## 8. Idle Mode
- Track last interaction timestamp (any incoming semantic action).
- If `now - last_interaction >= idle.timeout_ms`: switch to ambient profile (e.g., reduce density, shift scale to pentatonic airy pad, enable long reverb, LED slow fade).
- Exit idle on any new interaction; revert to saved active profile.

---
## 9. LED Event Abstraction (If Pi Contributes)
Define a minimal schema (Teensy renders patterns, so keep lean):
```json
{ "type": "note", "velocity": 100, "pitch": 64 }
{ "type": "param", "name": "tempo", "value": 128 }
{ "type": "mode", "mode": "mystic" }
{ "type": "idle", "state": true }
```
Transport options:
- Serial back to Teensy (if Teensy owns LEDs) (pack as small binary messages)
- UDP/OSC if Pi owns LEDs

MVP chooses only the messages required for existing animations.

---
## 10. Logging & Metrics
- Structured logging: JSON lines (`timestamp`, `event`, `detail`).
- Metrics: Prometheus endpoint `/metrics` (event counts, queue sizes, tick latency histogram, mutation count, idle transitions).
- Performance budget: MIDI → synth call latency target < 10 ms typical.

---
## 11. Error Handling & Resilience
| Error | Detection | Handling |
|-------|-----------|----------|
| MIDI port disconnect | Exception on read | Attempt re-open (exponential backoff) |
| Backend crash (PD/SC process) | Process exit code | Supervisor restarts backend; if >N failures escalate |
| Clock overruns | Tick latency log > threshold | Adaptive degrade (reduce voice polyphony) |
| Config parse error | Validation fail | Abort with actionable message |
| High CPU > 85% sustained | Periodic system stats | Throttle mutation & LED events |

---
## 12. Testing Strategy
### Unit
- Mapping resolution from sample config
- Scale mapping correctness (expected pitch sets)
- Mutation rule boundaries

### Integration
- Simulated MIDI stream → verify resulting synth calls & state changes
- Idle transition & recovery
- Clock accuracy over 10 min (<0.1% drift)

### Performance
- Stress test CC spam (simulate rapid pot moves) → ensure bounded queue size
- Measure end-to-end latency (timestamp injection & audio callback scheduling)

### Soak
- 6 hr run with random event injection; ensure no memory leak (monitor RSS), stable CPU usage.

---
## 13. Development Phases & Milestones
### Phase 0: Scaffold
- [ ] Create `rpi/engine/` structure, `pyproject.toml` or `requirements.txt`.
- [ ] Implement config loader & logging skeleton.

### Phase 1: MIDI Input & Routing
- [ ] Open port, map raw Note/CC to semantic events (print logs).

### Phase 2: State Model + Sequencer Skeleton
- [ ] Core state container with change listeners.
- [ ] Sequencer tick with static BPM & step playback (no probability yet).

### Phase 3: Scale & Probability
- [ ] Add probability per step, density gating.
- [ ] Implement scale mapper & switch scales via mapped CC.

### Phase 4: Mutation & Drift
- [ ] Add BPM drift envelope + mutation scheduler.
- [ ] Logging of each mutation.

### Phase 5: Backend Synthesis Integration
- [ ] Implement simple synth backend (pyo or fluidsynth) for note triggering.
- [ ] Parameter mapping (filter cutoff, reverb mix, volume).

### Phase 6: LED Event Emission
- [ ] Basic LED cue emitter (note, param, mode).
- [ ] Idle mode LED event.

### Phase 7: API & Metrics
- [ ] HTTP/JSON endpoint for current state & mutation history.
- [ ] Prometheus metrics endpoint.

### Phase 8: Hardening & Soak
- [ ] Reconnect logic, CPU/memory monitors.
- [ ] Long-run soak test & performance tuning.

### Phase 9: Polish
- [ ] Preset save/load.
- [ ] Config hot-reload (SIGHUP or file watcher).
- [ ] CLI flags for overrides.

---
## 14. Directory Structure (Proposed)
```
rpi/
  engine/
    src/
      main.py
      config.py
      midi_in.py
      router.py
      state.py
      sequencer.py
      scale_mapper.py
      mutation.py
      synth_adapter.py
      backend_pyo.py
      backend_pd.py
      backend_sc.py
      led_bus.py
      idle.py
      logging_setup.py
      metrics.py
      api.py
      util/time.py
    tests/
      test_mapping.py
      test_scale.py
      test_mutation.py
      test_sequencer.py
    config.yaml (sample)
  requirements.txt or pyproject.toml
```

---
## 15. Sample Pseudocode (Core Loop)
```python
class Engine:
    def __init__(self, cfg):
        self.clock = HighResClock(cfg.sequencer.bpm, ppq=24, swing=cfg.sequencer.swing)
        self.seq = Sequencer(cfg)
        self.router = Router(cfg, self.handle_action)
        self.synth = SynthAdapter(cfg)
        self.mutation = MutationEngine(cfg, self.state)
        self.idle = IdleManager(cfg.idle.timeout_ms, self.on_idle_state)
        self.led = LedBus(cfg)

    def handle_action(self, action):
        self.idle.touch()
        # update state or trigger events
        ...

    def run(self):
        for tick in self.clock.run():
            events = self.seq.tick(tick, self.state)
            for evt in events:
                note = self.scale.map(evt.pitch, self.state.scale)
                self.synth.play_note(note, evt.velocity, evt.duration)
                self.led.note(note, evt.velocity)
            self.mutation.maybe_mutate()
            self.idle.check()
```

---
## 16. Performance Targets
| Metric | Target |
|--------|--------|
| MIDI event handling latency | < 5 ms avg |
| Sequencer jitter | < 2 ms |
| CPU usage (normal) | < 30% |
| Memory footprint (RSS) | < 300 MB (Python + SC bridge) |
| Continuous uptime stability | ≥ 10 hr soak (>= 8 hr requirement + margin) |

---
## 17. Security / Safety Considerations
- Run engine as non-root.
- Validate config input (schema) before applying.
- Rate-limit external API mutation endpoints.
- Avoid blocking calls in audio scheduling path.

---
## 18. Deployment & Operation
- Systemd service file (`mystery_engine.service`) to auto-start.
- Log rotation with `logrotate` or built-in max-size rotation.
- Optional watchdog (systemd Restart=on-failure).

---
## 19. Versioning & Release
- Semantic versioning (engine separate from firmware).
- Tag: `engine-v0.1.0` once Phase 5 complete & stable.
- CHANGELOG entries by feature area.

---
## 20. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Python GC pauses cause jitter | Audio glitches | Keep audio real-time work minimal; offload synthesis to external engine (PD/SC) |
| Excessive MIDI -> event backlog | Latency | Bounded queue + drop lowest priority param spam |
| Mutation produces unpleasant extremes | Bad UX | Clamp ranges + weighted selection |
| Scale changes mid-phrase sound harsh | Disjoint feel | Option: quantize scale changes at bar boundaries |
| Idle mode flaps | Visual/audio noise | Hysteresis (exit only after 1s active) |

---
## 21. Decisions & Remaining Open Points
Resolved Decisions:
1. Backend: SuperCollider (primary)
2. Polyphony: Required (initial provision: 8 voices)
3. Scale Changes: Quantized at bar boundary
4. LEDs: Teensy-only animations; Pi sends minimal cues
5. Idle Fade: Use 4 s fade-in, 0.8 s fade-out (tunable)
6. External Clock Sync: Not needed v1
7. Mutation Persistence: Not needed v1
8. Remote Live Editing (Web/OSC): Deferred post-v1
9. Runtime Expectation: ≥ 8 hr daily (design for 10+ hr soak)
10. License: Align with firmware (TBD – please choose e.g., MIT/Apache-2.0)

Remaining Clarifications Needed:
A. Exact target voice count (is 8 sufficient or prefer 12/16?).
B. Acceptable CPU ceiling under load (retain 30% or adjust?).
C. Preferred license (MIT vs Apache-2.0) to document.

---
## 22. Immediate Next Steps
- [ ] Decide backend & language layering choice (#1).
- [ ] Answer open questions (#21).
- [ ] Scaffold repo structure & sample `config.yaml`.
- [ ] Implement Phase 0–1 (MIDI input + logging) and measure baseline latency.

---
## 23. Acceptance Criteria v0.1.0
- Configurable via `config.yaml` (loaded & validated)
- Receives MIDI from Teensy & logs semantic events
- Basic sequencer producing timed note events (8 steps) with density & probability
- Scale mapping functional (≥3 scales switchable by CC)
- Mutation engine periodically altering at least one parameter
- Idle mode transitions to ambient profile and back reliably
- Synth backend plays audible notes with <10 ms latency
- LED cue messages emitted (schema stable) or deferred by decision
- 2 hr soak test passes (no unbounded growth, stable performance)

---
All clarifications resolved (A–C). Proceed to scaffold codebase (Phase 0–1) with SuperCollider OSC integration and baseline sequencer.

Updates Applied:
- Voice count locked at 8 (expand via config later)
- CPU budget target refined: aim <25% typical, alarm >40%
- License: Apache-2.0 (align with firmware) — add `LICENSE` file at repo root
