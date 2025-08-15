# Teensy Firmware Software Roadmap

Target MCU: Teensy 4.1  (USB Type: MIDI)
Primary Role: Scan physical controls, generate debounced + smoothed event state, emit MIDI (Notes + CC), drive LED feedback animations, expose diagnostic + configuration hooks.
Stretch Role: Light-weight rule hooks (ONLY if round‑trip to Pi causes unacceptable latency for a subset of interactions).

---
## 1. Goals & Non‑Goals
### Core Goals
- Reliable low‑latency input → MIDI event pipeline (≤3 ms scan → send typical worst case)
- Deterministic LED feedback patterns (press, latch, idle, ambient fades)
- Stable over multi‑hour soak (memory, timing, heat)
- Easily extensible mapping layer (table/data‑driven vs. hard coded switch blocks)
- Resilient to switch bounce & pot jitter
- Simple field debugging (serial diagnostics, optional MIDI debug CC channel)

### Non‑Goals (Handled on Pi)
- Generative logic, scale/pitch selection, probability engine
- Long‑term state persistence (beyond optional calibration constants)
- Complex LED scene choreography (advanced patterns can move to Pi LED controller later)

---
## 2. High‑Level Architecture
```
+------------------+
|   Main Loop      |
|  (1 kHz tick)    |
+---------+--------+
          |
          v
+------------------+     +------------------+     +------------------+
| Input Sampler     |--> | State Manager     |--> | MIDI Dispatcher   |
| (GPIO/ADC read)   |    | (debounce, delta) |    | (usbMIDI.* calls) |
+------------------+     +------------------+     +------------------+
          |                                              ^
          v                                              |
+------------------+       +--------------------+        |
| Analog Filter    |-----> | Mapping Tables     |--------+
| (pots smoothing) |       | (Notes/CC cfg)     |
+------------------+       +--------------------+
          |
          v
+------------------+
| LED Controller    |
| (state-driven)    |
+------------------+
          |
          v
+------------------+
| Diagnostics (USB) |
+------------------+
```

---
## 3. Module Breakdown
| Module | Responsibility | Key Techniques | Deliverables |
|--------|----------------|----------------|--------------|
| `pins.h` | Central pin & message maps | `constexpr` arrays | Header file |
| `InputScanner` | Periodic read of digital & analog | Direct register read (optional), bounce window | `scan()` function |
| `Debouncer` | Edge detection for buttons/joystick/switches | Time-based (e.g., 5–8 ms) | Utility class |
| `AnalogSmoother` | Pot noise reduction & 10-bit→7-bit mapping | Exponential / median filter + deadband | `filter(channel)` |
| `Mapping` | Physical index → MIDI note/CC/channel | Tables; easily edited | Config struct + arrays |
| `MidiOut` | Encapsulation of usbMIDI sends | Throttle identical repeats | `sendNoteOn/Off`, `sendCC` |
| `LedFx` | Patterns: idle, press pulse, sustain glow | Frame delta approach | `tick()` & pattern registry |
| `Scheduler` | Fixed timestep tick (1 ms or 2 ms) | `elapsedMicros` | Main loop timing |
| `Diagnostics` | Serial prints & optional CC echo | Rate-limited | `dumpState()` |
| `ConfigStore` (future) | (Optional) store calibration | EEPROM / LittleFS | Accessors |

---
## 4. Development Phases & Milestones
### Phase 0: Bootstrap (Day 1)
- [ ] Create `teensy/firmware/` structure
- [ ] Basic blink / Serial Hello
- [ ] Confirm USB Type = MIDI enumerates

### Phase 1: Raw Input + MIDI (Day 1–2)
- [ ] Define pin & mapping tables
- [ ] Poll buttons → send NoteOn/NoteOff (no debounce)
- [ ] Poll pots → send CC on value change (raw 0–127 mapping)
- [ ] Poll joystick & switches → send CC (edge triggered naive)

### Phase 2: Robust Input Layer (Day 3)
- [ ] Implement time-based debounce (per control configurable)
- [ ] Add analog smoothing: EMA (α ≈ 0.25) + deadband (Δ≥2 -> send)
- [ ] Implement change compression (only send CC after stable for 4 ms OR threshold exceeded)
- [ ] Unit-like serial test mode: dump values each second

### Phase 3: LED Feedback Core (Day 4)
- [ ] Integrate FastLED (NUM_LEDS constant, brightness limit)
- [ ] Press pulse animation (short decay)
- [ ] Pot activity highlight (e.g., index pixel brightness flash)
- [ ] Idle detector (≥30 s no events) → ambient slow breathe pattern

### Phase 4: Performance Hardening (Day 5)
- [ ] Measure loop time histogram (micros min/avg/max over 10k cycles)
- [ ] Ensure worst-case loop < 1000 µs (if 1 kHz target)
- [ ] Replace slow operations (avoid floating point in hot path where possible)
- [ ] Add conditional compilation `#define DEBUG 0`

### Phase 5: Diagnostics & Safety (Day 6)
- [ ] Rate-limited serial debug command handler (list: `?` help)
- [ ] Runtime toggle of LED brightness / debug prints
- [ ] MIDI panic handler (all notes off) bound to a hidden combo

### Phase 6: Refinements / Polish (Day 7+)
- [ ] Per-input configurable debounce via table
- [ ] Optional calibration (store pot min/max into EEPROM)
- [ ] LED pattern theming (array of palettes)
- [ ] Add version string & semantic version bump policy

### Stretch (Future)
- [ ] Lightweight scripting hook (e.g., simple rule DSL for LED tie-ins) – only if needed
- [ ] USB Vendor SysEx channel for remote config from Pi
- [ ] Boot self-test (flash each LED, read each input once)

---
## 5. Timing & Rates
| Element | Target | Notes |
|---------|--------|-------|
| Main scan tick | 1 kHz (1 ms) | Enough for responsive buttons & LED updates |
| LED refresh | 60–100 Hz | Decouple from scan using modulus (e.g., every 10th tick) |
| Pot CC emission | ≤20 Hz per channel when moving | Apply deadband & min interval (e.g., 15 ms) |
| Idle detection window | 30,000 ms | Configurable constant |

---
## 6. Debounce & Filtering Strategy
- Digital (buttons/joystick/switches): store last stable state + timestamp; require `stableFor >= DEBOUNCE_MS` (default 5 ms) before signaling change.
- Analog (pots):
  - Raw 10-bit read (0–1023)
  - EMA: `filtered = filtered + α*(raw - filtered)`
  - Quantize to 0–127 after filtering
  - Deadband: ignore if |new - lastSent| < 2 (tunable)
  - Rate limit: enforce ≥15 ms between sends unless delta ≥8

---
## 7. Data Structures (Proposed)
```cpp
struct ButtonCfg { uint8_t pin; uint8_t note; };
struct PotCfg { uint8_t pin; uint8_t cc; };
struct AxisCfg { uint8_t pin; uint8_t cc; };
struct SwitchCfg { uint8_t pin; uint8_t cc; };

extern const ButtonCfg BUTTONS[10];
extern const PotCfg    POTS[6];
extern const AxisCfg   JOY[4];
extern const SwitchCfg SWITCHES[3];
```

Runtime state arrays mirror configs for last raw, filtered, and timing metadata.

---
## 8. LED Pattern System (MVP)
LED Inventory: 60 LEDs in a single linear strip (index 0..59). Initial mapping (suggestion):
- Indices 0–9: Button feedback (one per button)
- Indices 10–15: Knob feedback (one per pot)
- Indices 16–19: Joystick cardinal indicators / directional pulses
- Indices 20–22: Switch state indicators
- Remaining 23–59: Ambient / mode / idle effects band

Brightness Policy:
- Global max brightness limited (e.g. `LED_BRIGHTNESS_MAX = 160` out of 255)
- Idle brightness cap: 15% of max (≈24) to reduce glare in ambient mode

| Pattern | Trigger | Behavior |
|---------|---------|----------|
| Press Pulse | Button note-on | Assigned pixel set to palette color at full brightness (capped) then exponential fade |
| Pot Nudge | Pot value delta above threshold | Pixel flash (white or accent) proportional to delta magnitude |
| Active Mode Glow | Switch toggled | Switch pixels latch to mode color palette entry |
| Idle Ambient | No events 30 s | Low-brightness (≤15% cap) slow hue rotate / gentle breathe over ambient band |
| Startup Self-Test | On boot before normal loop | Sequential chase over all 60 LEDs, color wheel sweep, then success blink |

Implementation: Maintain per-pixel `uint16_t energy`; each LED frame: `energy = max(0, energy - decay)`; brightness = `min(maxBrightness, (energy * scale) >> shift)`, and clamp to idle cap if idle.

---
## 9. MIDI Policy
- Channel: 1 (single channel sufficient). Channel 2 reserved future.
- Notes: 60–71 fixed velocity 100 (constant for v1; velocity variation deferred).
- CC: 7-bit standard values. Debounced / smoothed. Deadband + rate limit to keep within latency budget.
- Joystick: Single 127 pulse (edge) per direction actuation (no trailing 0) — firmware enforces a minimum re-arm time to avoid chatter.
- Switches: Send 127 on ON edge, 0 on OFF edge (latched state needed for mode).
- Panic: Send NoteOff for 60–71 if error condition or explicit command.

---
## 10. Error Handling & Fault Modes
| Fault | Detection | Response |
|-------|-----------|----------|
| Stuck button (never releases 5 s) | Timer since press | Force note-off + mark flagged in diagnostics |
| ADC noise storm | Excessive jitter detections | Temporarily increase smoothing α or lock channel |
| LED driver hang | Frame time > 5 ms repeatedly | Drop LED frame rate / set warning pattern |
| USB MIDI stall | Queue full (rare) | Skip low-priority CC until queue clears |

---
## 11. Testing Plan
### Bench Tests
- Button bounce capture (logic analyzer or serial timestamps) to validate debounce constant
- Pot sweep linearity & jitter (log min/max, std dev at rest)
- Loop timing (collect 10k cycles, compute worst-case)

### Automated (Lightweight)
- Add a compile-time `#define TEST_MODE` that simulates deterministic input patterns and asserts transitions via serial output (manually verified first, could parse on Pi later).

### Soak
- 6 hr run with periodic scripted MIDI input simulation (optional) verifying no memory growth (inspect free RAM) & no stuck states.

---
## 12. Configuration & Build Flags
```cpp
#define SCAN_HZ 1000
#define DEBOUNCE_MS 5
#define POT_DEADBAND 2            // ±2 -> ignore; tuned for <=20 ms latency target
#define POT_RATE_LIMIT_MS 15       // ensures worst-case <20 ms perceived response
#define IDLE_TIMEOUT_MS 30000
#define DEBUG 0
#define LED_BRIGHTNESS_MAX 160     // global max (out of 255)
#define IDLE_BRIGHTNESS_CAP_PCT 15 // percent of max during idle ambient
#define JOYSTICK_REARM_MS 120      // min time between pulses per direction
```
Use `#if DEBUG` blocks for serial prints to keep hot path lean.

---
## 13. Memory & Performance Budget (Estimates)
| Item | Estimate |
|------|----------|
| State arrays (inputs, metadata) | < 2 KB |
| LED buffer (100 LEDs × 3 bytes) | 300 B (FastLED internal adds overhead) |
| Stack (main) | < 4 KB typical |
| Total headroom (Teensy 4.1 has 1 MB RAM) | Abundant |

CPU: Input + LED + MIDI expected << 5% @ 600 MHz.

---
## 14. Versioning & Release Process
- Semantic style: MAJOR.MINOR.PATCH (e.g. 0.1.0 initial public firmware)
- Tag builds after soak test pass: `teensy-v0.1.0`
- Maintain `CHANGELOG.md` in `teensy/`

---
## 15. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Excessive CC spam | MIDI congestion / Pi CPU | Deadband + rate limit |
| LED EMI / audio noise | Audible hum | Twist data+ground, add series resistor, filtering |
| Future mapping changes require flash | Slow iteration | Keep remap on Pi where possible; only static physical indexes in firmware |
| Hidden mode latency (if added on Pi) | Perceived delay | Only offload *non-time-critical* transforms |

---
## 16. Decisions (Previously Open Questions)
1. LEDs: 60 in single strip; mapping established (see §8). Potential future expansion reserved.
2. Palette: Fixed palette in firmware for v1; Pi will not push palette changes.
3. Joystick: Single 127 pulse per press (edge), no 0 release message.
4. Buttons: Fixed velocity for v1 (no dynamic velocity / aftertouch).
5. Startup Self-Test: Implement chase + color sweep + success blink before entering normal loop.
6. Remote Config Protocol: Deferred (no SysEx / config channel v1).
7. Pot Latency Budget: ≤20 ms acceptable → current smoothing & rate limit chosen accordingly.
8. LED Frames: Pi will NOT stream full frames; only minimal cue messages; Teensy fully owns LED rendering.
9. Idle Brightness: Cap at 15% of max brightness (see flags) to reduce glare.
10. License: Apache 2.0 (aligns with overall project license).

---
## 17. Immediate Next Actions
- [ ] Confirm answers to open questions (esp. LED count & joystick semantics)
- [ ] Scaffold directory + headers (`pins.h`, `config.h`, `main.cpp`)
- [ ] Implement Phase 1 MVP & commit
- [ ] Start loop timing instrumentation before adding LED complexity

---
## 18. Directory Skeleton (Proposed)
```
teensy/
  firmware/
    src/
      main.cpp
      pins.h
      config.h
      input_scanner.cpp
      input_scanner.h
      debounce.h
      analog_smoother.cpp
      analog_smoother.h
      mapping.h
      midi_out.cpp
      midi_out.h
      led_fx.cpp
      led_fx.h
      diagnostics.cpp
      diagnostics.h
    include/ (optional if using PlatformIO)
    platformio.ini (if using PlatformIO instead of Arduino IDE)
  CHANGELOG.md
```

---
## 19. Example Pseudocode Main Loop
```cpp
void loop() {
  static elapsedMicros tick;
  if (tick >= 1000) { // ~1 kHz
    tick -= 1000;
    scanInputs();              // read raw states
    processButtons();          // debounce & note events
    processJoystick();
    processSwitches();
    processPots();             // smoothing + CC
    updateIdleTimer();
    scheduleLedFrame();
  }
  if (shouldRenderLedFrame()) {
    renderLedFrame();
    FastLED.show();
  }
  while (usbMIDI.read()) { /* handle incoming (future config) */ }
}
```

---
## 20. Acceptance Criteria for v0.1.0
- All 10 buttons produce correct NoteOn/NoteOff (no duplicates, <10 ms worst-case latency)
- Pots produce monotonic CC ramps on slow sweep; jitter ≤ ±1 when still; event latency ≤20 ms
- Joystick directions emit a single 127 pulse per actuation (re-arm enforced)
- Switches latch ON (127) / OFF (0) correctly
- LED press feedback, pot nudge, mode glow, idle ambient (≤15% brightness), startup self-test all functional
- CPU headroom > 90%; no memory fragmentation (no dynamic alloc in loop)
- Soak test 4 hr: no stuck notes, no crash, loop time stable

---
## 21. Future Enhancements (Backlog)
- SysEx config channel
- Input event batching (pack multiple changes in a millisecond bucket)
- HID composite device (MIDI + Serial + Custom) for config UI
- Palette streaming from Pi
- MIDI clock in (from Pi) to flash tempo LED group

---

Provide clarifications for open questions (#16) to refine this roadmap before coding Phase 2.
