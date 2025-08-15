# Mystery Music Station

An interactive, arcade‑inspired generative music console. A **Teensy 4.1** scans buttons, knobs, joystick directions, and toggles, sending USB MIDI to a **Raspberry Pi** which runs a mutable generative synthesis / sequencing engine (Pure Data, SuperCollider, or Python). LED feedback and evolving sound create a mysterious, exploratory instrument / art piece.

> For full mechanical, wiring, and detailed design info see: `docs/ProjectPlan.md` (includes BOM, wiring diagram, panel & cabinet drawings).

---
## ✨ Core Concept
Physical controls → Teensy (USB MIDI) → Raspberry Pi engine → Audio + LEDs.

Keep the *mystery*: Physical inputs map to conventional MIDI messages; the Pi layer holds the secret logic (scales, probability, mutations, hidden modes) so you can iterate without rewiring.

---
## 🧩 Features (Initial Scope)
- 10 illuminated arcade buttons (MIDI Notes 60–69)
- 6 knobs (CC 20–25) for tempo, filter, density, swing, mix, volume (or remapped)
- 4-way joystick (CC 50–53) for sequence length, scale, chaos, etc.
- 3 toggle switches (CC 60–62) for mode / palette / drift
- Addressable LED strip(s) (WS2812B / SK6812) for state + ambient animations
- Swappable / pluggable Pi generative engine (PD / SC / Python)
- Soft idle state (ambient pads + slow LED fades after inactivity)

---
## 🛠 Hardware Summary
| Subsystem | Parts |
|-----------|-------|
| Controller | Teensy 4.1 (USB MIDI) |
| Host | Raspberry Pi 4 (2–4 GB) + SD + PSU |
| Inputs | 10x arcade buttons, 6x 10k linear pots, joystick, 3x toggles |
| LEDs | 60–100 addressable pixels (5V) + 330–470 Ω data resistor + 1000 µF cap |
| Power | 5V LED PSU (10–15 A) + shared ground, fused IEC inlet |
| Enclosure | 24"×12" angled panel, ~42" high cabinet (birch plywood) |

See `docs/` images for pin map & layouts.

---
## 🎛 Pin / MIDI Mapping (Teensy)
| Control | Pins | MIDI |
|---------|------|------|
| Buttons B1–B10 | D2–D11 | Notes 60–69 |
| Knobs K1–K6 | A0–A5 | CC 20–25 |
| Joystick U/D/L/R | D22–D25 | CC 50–53 |
| Switches S1–S3 | D26–D28 | CC 60–62 |
| LED Data | D14 | LED strip |

---
## 📁 Repository Layout
```
/README.md              ← (this file)
/docs/                  ← Project plan + diagrams
/teensy/                ← Firmware (to be added)
/rpi/                   ← Generative engine code (to be added)
```

---
## 🚀 Quick Start
### 1. Teensy Firmware (Arduino IDE / PlatformIO)
1. Install Teensyduino (set USB Type = MIDI).  
2. Create firmware under `teensy/` using the outline in the project plan.  
3. Implement scanning loop: debounce buttons, read pots (map 0–1023 → 0–127), detect edge changes for joystick & switches, send MIDI (channel 1).  
4. Add LED driver (e.g., FastLED) for feedback.

Minimal skeleton:
```cpp
#include <FastLED.h>
const int buttonPins[10]={2,3,4,5,6,7,8,9,10,11}; // D12,D13 free for future expansion
const int knobPins[6]={A0,A1,A2,A3,A4,A5};
const int joyPins[4]={22,23,24,25};
const int switchPins[3]={26,27,28};
#define LED_PIN 14
void setup(){
  for(int i=0;i<10;i++) pinMode(buttonPins[i], INPUT_PULLUP);
  for(int i=0;i<4;i++) pinMode(joyPins[i], INPUT_PULLUP);
  for(int i=0;i<3;i++) pinMode(switchPins[i], INPUT_PULLUP);
  // init LEDs & MIDI
}
void loop(){
  // scan + send usbMIDI events
}
```

### 2. Raspberry Pi Engine
Choose a stack (pick one to start):
- Pure Data: `sudo apt install puredata` — build a patch that listens to Notes 60–71 & CCs, maps to synth voices & parameters, adds probabilistic mutation.
- SuperCollider: Install `supercollider` + write a MIDIdef-based pattern engine.
- Python: `mido` / `python-rtmidi` + `scamp` / `pyo` / `supercollider via sc3nb` for synthesis.

Suggested architecture:
```
[MIDI In] -> [Router + Hidden Rules] -> [Sequencer Core] -> [Scale Mapper] -> [Synth Voices] -> [Audio]
                                            |-> [LED Event Bus]
```

### 3. Link & Test
1. Plug Teensy into Pi (shows as USB MIDI device).  
2. Run your engine, confirm incoming messages (e.g., `aseqdump -p <client:port>` on Linux).  
3. Verify each control changes expected sonic or visual state.  
4. Implement idle detection (e.g., timestamp last interaction).  

---
## 🧪 Testing Checklist
- All buttons register distinct Notes
- Pots sweep smoothly (no jitter > ±2 after smoothing)
- Joystick / switches send single edge-triggered CC values
- LED animations survive 4–6 hr soak (no brownouts)
- Audio engine stable under parameter spam
- Idle mode triggers after ~30 s no input

---
## 🔌 Power & Safety Notes
- Common ground between Teensy, Pi, and LED PSU
- 1000 µF cap across first LED strip segment
- Series data resistor 330–470 Ω
- Fuse + strain relief on AC inlet; ferrules on PSU terminals
- Separate audio wiring away from high-current LED runs

---
## 🗺 Roadmap (Proposed)
- [ ] Commit baseline Teensy firmware
- [ ] Add LED feedback patterns (press, pulse, idle fade)
- [ ] Implement first Pi engine (pick PD or Python)
- [ ] Add scale & mode system + random mutation timer
- [ ] Introduce secret combo sequences (easter eggs)
- [ ] Logging & performance profiling
- [ ] Package enclosure cutting template (DXF)

---
## 🤝 Contributing
Early-stage personal build; PRs / issues welcome once firmware & engine skeletons are pushed. Until then, use issues for ideas / feature discussion.

---
## 📄 License
(Choose a license; e.g., MIT, CC BY-SA, or leave private. Add `LICENSE` file.)

---
## 🙏 Acknowledgments / Inspiration
- DIY arcade & generative art installations
- Open-source MIDI / synthesis communities
- FastLED / SuperCollider / Pure Data ecosystems

---
## 🧭 Next Steps for You
1. Add initial firmware under `teensy/`.
2. Decide engine platform (PD vs Python vs SC) and scaffold in `rpi/`.
3. Commit wiring/panel DXF/printable drill guide if available.
4. Pick a license.

Enjoy building the mystery! 🎶
