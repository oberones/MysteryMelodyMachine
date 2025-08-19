# Project Specification (SPEC.md)

Title: Mystery Music Station (Interactive Generative Music Console)
Version: 0.1.0 (Spec)
Status: Living document (update alongside roadmap changes)
License: Apache-2.0

---
## 1. Purpose & Vision
Create a durable, low-latency, arcade-style generative music installation where physical interaction (buttons, knobs, joystick, switches) influences evolving musical structures and ambient LED feedback. The Teensy firmware provides deterministic, reliable hardware → MIDI translation + LED animation; the Raspberry Pi engine provides generative logic, synthesis (SuperCollider), mutation, and high-level reaction to performer input.

Primary Goals:
- Immediate tactile response (<10 ms perceptual latency for button notes)
- Long-running stability (≥8 hr daily operation)
- Modular generative layer (swap/extend rules without reflashing firmware)
- Clear separation of responsibilities (hardware vs. composition logic)

Non-Goals (v1):
- Streaming LED frame control from Pi
- Remote dynamic firmware reconfiguration (beyond compile-time constants)
- Complex visual UI

---
## 2. Hardware Summary (v1)
| Element | Count | Notes |
|---------|-------|-------|
| Arcade Buttons | 10 (B1–B10) | Digital, INPUT_PULLUP, MIDI Notes 60–69 |
| Pots | 6 (K1–K6) | Analog A0–A5 → CC 20–25 |
| Joystick | 4 directions | D22–D25 → CC 50–53 (edge pulse 127) |
| Toggles | 3 (S1–S3) | D26–D28 → CC 60–62 (latching 0/127) |
| LED Strip | 60 pixels | Data D14 (WS2812B/SK6812) |

Spare Pins Freed: D12, D13 (reserved future features)

---
## 3. MIDI Mapping (Canonical)
| Control | MIDI Type | Range / Value Semantics |
|---------|-----------|-------------------------|
| Buttons B1–B10 | NoteOn/NoteOff | Notes 60–69, fixed velocity 100, proper NoteOff (velocity 0) |
| Pots K1–K6 | ControlChange | CC 20–25, 0–127 after smoothing & deadband (≥2) |
| Joystick U/D/L/R | ControlChange | CC 50–53, single 127 pulse per actuation (no trailing 0) |
| Switches S1–S3 | ControlChange | CC 60–62, 127 on ON, 0 on OFF |
| Panic (future) | ControlChange or SysEx | TBD (deferred) |

Channel: 1 (Channel 2 reserved for future alternate semantic layer).

---
## 4. Latency & Performance Targets
| Path | Target |
|------|--------|
| Button press → MIDI dispatch | ≤5 ms typical, ≤10 ms worst |
| Pot move → CC emitted (above deadband) | ≤20 ms |
| Sequencer tick jitter (Pi) | <2 ms |
| MIDI → Synth onset (Pi) | <10 ms typical |
| MCU main loop time | <1000 µs worst at 1 kHz |
| LED frame update cadence | 60–100 Hz |

---
## 5. Teensy Firmware Responsibilities
1. Scan inputs at 1 kHz.
2. Debounce digital inputs (5–8 ms window typical).
3. Smooth analog (EMA α≈0.25) + deadband (±2) + rate limiting (≥15 ms unless large delta).
4. Emit only state changes (no redundant CC / Note spam).
5. Provide LED animations:
   - Button Press Pulse
   - Pot Nudge Flash
   - Mode / Switch Glow
   - Idle Ambient (≤15% brightness cap after 30s inactivity)
   - Startup Self-Test (chase + color sweep + success blink)
6. Maintain deterministic timing (avoid dynamic allocation in loop).
7. Offer minimal diagnostics (serial if DEBUG=1).

Out of Scope (v1): Config protocol, dynamic palette streaming, velocity sensing, SysEx control.

---
## 6. Raspberry Pi Engine Responsibilities
1. Receive and interpret MIDI events (mido + python-rtmidi).
2. Translate raw events → semantic actions (tempo, density, mode, scale change requests, etc.).
3. Sequencer core (steps, probability, density, swing, drift, bar-aligned scale changes).
4. Mutation engine: scheduled mild parameter perturbations every 2–4 minutes.
5. Scale mapping: major/minor/pentatonic (extensible) – changes quantized to bar boundary.
6. Synthesis via SuperCollider (`scsynth`) over OSC (play notes, set params).
7. Idle mode detection (30s inactivity) → ambient parameter profile & LED idle cue.
8. Emit minimal LED cues (JSON or simple tokens) if/when needed (note, param, mode, idle transitions). Teensy interprets; Pi does not push raw LED frames.
9. Structured logging + (future) metrics endpoint.

---
## 7. LED Index Allocation (Firmware)
| Range | Purpose |
|-------|---------|
| 0–9 | Buttons B1–B10 |
| 10–15 | Pots K1–K6 |
| 16–19 | Joystick directions |
| 20–22 | Switches S1–S3 |
| 23–59 | Ambient / mode / idle band |

Global brightness cap: 160/255. Idle brightness cap: 15% of cap.

---
## 8. Code Style & Conventions
### C++ (Teensy)
- Use `constexpr` arrays for pin & mapping definitions in `pins.h`.
- No dynamic allocation inside `loop()`.
- Prefix internal (file-static) helpers with `_` or place in anonymous namespace.
- Avoid floating point in hot paths; precompute scales / use integer math where feasible.
- Naming: `CamelCase` for types, `snake_case` for functions/variables, ALL_CAPS for tunable compile-time constants.
- Keep ISR usage minimal (prefer polling at 1 kHz unless a true interrupt is necessary—none planned v1).

### Python (Pi)
- **Virtual Environment**: All Python development and execution must be done within the `.venv` virtual environment in the project root.
- **Dependency Management**: Use `pip install -r rpi/engine/requirements.txt` within the activated virtual environment.
- Use type hints (PEP484) & `pydantic` for config validation.
- Module naming: `snake_case.py`; classes `PascalCase`; constants `UPPER_SNAKE`.
- Prefer composition over inheritance; inject dependencies through constructors.
- Logging: `logging.getLogger(__name__)`; structured messages `key=value` style.
- Avoid blocking calls in timing loop—use non-blocking I/O / scheduling.

---
## 9. Configuration
Primary runtime config: `rpi/engine/config.yaml` (validated by `config.py`). Editable fields include sequencer parameters, mutation intervals, idle timings, voice count, logging level.

Firmware compile-time configuration: `config.h` (to be created) with constants specified in roadmap (e.g., `SCAN_HZ`, `DEBOUNCE_MS`).

---
## 10. Error Handling Policies
| Layer | Condition | Policy |
|-------|----------|--------|
| Teensy | Stuck button (held >5s) | Force NoteOff + log (DEBUG) |
| Teensy | Rapid pot jitter | Increase smoothing temporarily |
| Teensy | LED refresh overrun | Drop frame / reduce update rate |
| Pi | MIDI port disconnect | Retry with exponential backoff |
| Pi | Backend (scsynth) crash | Restart process; escalate after N failures |
| Pi | Clock drift | Adjust next tick via accumulated error |

---
## 11. Testing Strategy Summary
Firmware:
- Manual serial diagnostics + logic analyzer spot checks
- Soak test 4 hr bench (simulate button & pot activity)

Pi Engine:
- **Environment**: All testing must be performed within the activated `.venv` virtual environment
- **Test Execution**: `source .venv/bin/activate && pytest rpi/engine/tests/`
- Unit tests (mapping, scale mapper, mutation bounds)
- Integration: simulated MIDI feed → expected synth event count / ordering
- Performance: tick jitter histogram logging
- Soak test 6–10 hr (target memory stability)

---
## 12. Versioning
- Firmware tags: `teensy-vMAJOR.MINOR.PATCH`
- Engine tags: `engine-vMAJOR.MINOR.PATCH`
- Increment PATCH for fixes, MINOR for new non-breaking features, MAJOR for breaking mappings/protocols.
- Keep `CHANGELOG.md` per component.

---
## 13. Security & Safety Considerations
- Run engine under non-root user; restrict network exposure (loopback or LAN only initially).
- Validate all config inputs; reject unknown keys.
- Avoid unbounded logs (rotate or size limit planned future step).
- Electrically: follow power best practices (handled in mechanical plan; included here for completeness).

---
## 14. Future Extensibility (Reserved)
- Channel 2 secret mode
- SysEx configuration or small binary protocol
- Palette streaming & cross-fade scenes
- External clock sync (Ableton Link / MIDI clock)
- Higher voice polyphony (config) & dynamic voice allocation
- Additional sensors (freed pins D12,D13)

---
## 15. AI Agent Collaboration Guidelines
This spec exists to make automated assistance consistent.

When extending firmware:
- Do NOT change pin allocations unless spec updated.
- Preserve public headers (`pins.h`, upcoming `config.h`) structure; append rather than reorder unless necessary.
- When adding constants, group by function (timing, LED, MIDI).
- Add tests or diagnostic notes for new behavior.

When extending Pi engine:
- **CRITICAL**: Always activate the virtual environment first: `source .venv/bin/activate`
- **Dependencies**: Install/update requirements within venv: `pip install -r rpi/engine/requirements.txt`
- **Testing**: Run tests within venv: `pytest rpi/engine/tests/`
- **Execution**: Run engine within venv: `python rpi/engine/src/main.py --config rpi/engine/config.yaml`
- Keep config schema backward compatible (add new keys with defaults).
- Any new semantic action must map cleanly from existing MIDI ranges or use reserved CC after discussion (prefer Pi-side remapping before modifying firmware mapping).
- Maintain separation: mapping layer should not contain direct synthesis logic.

General:
- Confirm impact footprint (lines touched, behavioral changes) in PR summary.
- Avoid introducing heavy dependencies; prefer standard library or listed allowed libs.
- Ensure latency targets still met (mention measurement if timing path changed).

Ask for Clarification If:
- New hardware peripherals proposed.
- MIDI mapping expansion collides with existing note/CC usage.
- Memory usage for LED features expands beyond originally assumed footprint.

Assumptions Allowed Without Asking:
- Minor refactors improving readability (no behavior change).
- Adding lightweight inline helper functions.
- Expanding scale list (non-breaking) if triggered by existing scale_select mechanism.

---
## 16. Commit & PR Conventions
- Conventional Commit style recommended: `feat(fw): add joystick pulse handling` / `fix(engine): clamp density`.
- Reference spec section for structural changes (e.g., "Spec §8 LED mapping updated").
- Include latency or CPU impact note if touching timing-critical code.

---
## 17. Glossary
| Term | Definition |
|------|------------|
| Density | Global probability scaler (0–1) applied to step triggers |
| Drift | Slow BPM modulation parameter |
| Ambient Mode | Reduced-intensity idle behavior after inactivity |
| Mutation Cycle | Scheduled batch of automatic parameter tweaks |
| Semantic Action | Logical intent derived from raw MIDI (e.g., set_tempo) |

---
## 18. Acceptance Checklist (Spec Compliance)
Firmware v1 must:
- Emit only defined MIDI set (Notes 60–69, CC 20–25, 50–53, 60–62)
- Obey latency & brightness caps
- Provide startup self-test

Engine v1 must:
- Honor bar-aligned scale changes
- Produce generative notes with probability & mutation
- Enforce idle profile after 30s inactivity

---
## 19. Change Management
Update this file when:
- Hardware count changes (buttons, LEDs, controls) -> Section 2/7
- Mapping changes -> Sections 3/5/7
- Performance targets revised -> Section 4
- New protocols or backends added -> Sections 6/14

---
End of SPEC.md
