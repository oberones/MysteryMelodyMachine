# Mystery Generative Melody Console — Full Project Plan (Teensy 4.1)

This document is a **build-ready plan** for your interactive, mysterious music station. It includes the concept, bill of materials, wiring, software mapping, cabinet construction, panel layouts, and testing checklist.

---

## 1) System Overview
```
[Buttons/Knobs/Joystick/Switches] → [Teensy 4.1 USB-MIDI] → [Raspberry Pi: Sequencer Engine] → [External Hardware Synths (MIDI)]
                                                                      ↓
                                            [RGB LED Infinity Portal] ← [Animation Cues]
```
- **Teensy 4.1** reads inputs, sends MIDI Notes/CC to Pi, and drives RGB LED infinity portal
- **Raspberry Pi 4** runs generative sequencer engine with configurable MIDI CC profiles
- **External Hardware Synths** (flagship: Korg NTS1 MK2) receive MIDI for synthesis
- **RGB LED Infinity Portal** provides visual feedback with generative animations

---

## 2) Wiring Diagram
![Teensy wiring](./teensy_wiring_diagram.png)

**Pin map** (Updated for infinity portal)
- **Buttons B1–B10 → D2–D11** (INPUT_PULLUP), send MIDI Notes 60–69  
- **Knobs K1–K6 → A0–A5** (10k linear pots), send MIDI CC 20–25  
- **Joystick U/D/L/R → D22–D25** (INPUT_PULLUP), send MIDI CC 50–53  
- **Switches S1–S3 → D26–D28** (INPUT_PULLUP), send MIDI CC 60–62  
- **Portal LEDs → D14** (RGB data to infinity portal LED strips)
- **Portal Power → 5V** from Teensy or dedicated 5V supply

**Audio Chain**
- **Pi MIDI Out → External Synths** (USB-MIDI or DIN MIDI interface)
- **Synth Audio Out → Mixer/Speakers**

---

## 3) Control Panel (Drill Guide)
![Control panel layout](./control_panel_layout.png)

**Panel size:** 24″ × 12″, mounted at ~30–35° tilt.  
**Layout:** RGB LED infinity portal centered, joystick and buttons arranged in front
Holes: **Buttons Ø1.2″**, **Knobs Ø1.0″**, **Switches 0.6″×0.3″**, **Joystick 2″ square**, **Portal mounting ~8″ circle**

---

## 4) Cabinet (Dimension Sketch)
![Cabinet views](./cabinet_front_side.png)

- **Height:** ~42″ overall, **Depth:** ~18″, **Width:** ~24″  
- ¾″ Baltic birch plywood, pocket-screw + glue  
- **Portal Integration:** Central mounting for infinity portal with clear viewing window
- Back door with **foam gasket**; filtered vent for electronics cooling
- **Synth Bay:** Internal rack space for external hardware synths
- Rubber leveling feet; single **locking IEC** AC inlet to internal power distribution

---

## 5) Bill of Materials (Updated)
**Core Electronics:**
- Teensy 4.1 + USB cable  
- Raspberry Pi 4 (2–4 GB) + SD card + PSU  
- **Existing RGB LED Infinity Portal** (from ~/Projects/coding/arduino/uno/arduino-infinity-portal)

**Controls:**
- 10× LED arcade buttons + harnesses  
- 6× 10k linear potentiometers + knobs  
- 8-way arcade joystick  
- 3× SPST/SPDT toggle switches  

**Audio Hardware:**
- **Korg NTS1 MK2** (flagship synth)
- Additional external synths (optional)
- MIDI interface (USB-MIDI or DIN MIDI)
- Audio mixer + speakers/amp
- MIDI cables, audio cables

**Mechanical:**
- ¾″ plywood, ¼″ acrylic/polycarbonate panel cover
- Portal mounting hardware and clear viewing window
- Internal synth rack/mounting
- Wiring, connectors, heatshrink, grommets, gasket foam

---

## 6) Software Mapping (Teensy → MIDI → Synths)
**Input Mapping:**
- **Buttons (B1–B10):** MIDI Notes 60–69 → sequencer triggers + portal animation cues
- **Knobs (K1–K6):** MIDI CC 20–25 → configurable synth parameters (Korg NTS1 MK2 profile default)
- **Joystick (U/D/L/R):** MIDI CC 50–53 → sequence control (length, scale, pattern, etc.)
- **Switches (S1–S3):** MIDI CC 60–62 → mode/profile/effects

**Korg NTS1 MK2 Default CC Profile:**
- CC 20: Oscillator Type
- CC 21: Filter Cutoff  
- CC 22: Filter Resonance
- CC 23: EG Attack
- CC 24: EG Decay/Release
- CC 25: LFO Rate

> **Configurable Profiles:** Pi engine supports multiple CC mapping profiles for different external synths

---

## 7) Teensy Firmware Outline (Arduino)
```cpp
// USB Type: MIDI (set in Tools menu)
#include <FastLED.h>
// Include infinity portal code from ~/Projects/coding/arduino/uno/arduino-infinity-portal

const int buttonPins[10] = {2,3,4,5,6,7,8,9,10,11};
const int knobPins[6]    = {A0,A1,A2,A3,A4,A5};
const int joyPins[4]     = {22,23,24,25};
const int switchPins[3]  = {26,27,28};
const int PORTAL_LED_PIN = 14;

// Portal animation variables
int portalProgram = 0;
float animationRate = 1.0;

void setup(){
  // Initialize inputs
  for(int i=0;i<10;i++) pinMode(buttonPins[i], INPUT_PULLUP);
  for(int i=0;i<4;i++)  pinMode(joyPins[i], INPUT_PULLUP);
  for(int i=0;i<3;i++)  pinMode(switchPins[i], INPUT_PULLUP);
  
  // Initialize portal LEDs
  initPortalLEDs();
}

void loop(){
  // Input scanning and MIDI output
  scanButtons();   // -> usbMIDI.sendNoteOn/Off(60+i, ...)
  scanKnobs();     // -> usbMIDI.sendControlChange(20+k, value, 1)
  scanJoystick();  // -> usbMIDI.sendControlChange(50+d, 127, 1)
  scanSwitches();  // -> usbMIDI.sendControlChange(60+s, state?127:0, 1)
  
  // Handle incoming portal animation cues from Pi
  handlePortalCues();
  
  // Update portal animation
  updatePortalAnimation();
}
```

---

## 8) Pi Sequencer Engine (Python)
**Core Functions:**
- **MIDI Input:** From Teensy → semantic event routing
- **Sequencer Core:** Step-based generative sequencing with probability, swing, mutation
- **Scale Mapping:** Real-time scale changes with musical quantization
- **CC Profile Management:** Configurable mappings for different external synths
- **MIDI Output:** To external hardware synths via MIDI interface
- **Portal Control:** Send animation cues back to Teensy for portal effects
- **Idle Mode:** Ambient sequencing and portal animations during inactivity

**Supported Synth Profiles:**
- **Korg NTS1 MK2** (default)
- **Generic Analog** (filter, envelope, LFO)
- **FM Synth** (operators, algorithms)
- **Custom** (user-defined CC mappings)

---

## 9) Build Sequence
1. **Portal Integration:** Adapt existing infinity portal code for Teensy 4.1
2. **Bench test** Teensy inputs + MIDI + portal LEDs on laptop  
3. **Pi sequencer** prototype; verify MIDI routing to external synths
4. **Cabinet modification** for portal mounting and synth bay
5. Cut and drill panel with portal viewing window and control layout
6. Wire control harnesses to Teensy, install portal
7. Mount Pi, MIDI interface, and external synths in cabinet
8. **Audio chain setup:** MIDI → synths → mixer → speakers
9. **Integration test:** Full system with portal animations and audio
10. **Soak test** 4–6 hrs; verify thermal and stability performance

---

## 10) Safety & Reliability
- IEC inlet with fuse; secure all PSU terminals
- **Portal Power:** Ensure adequate 5V supply for LED animations
- **MIDI Isolation:** Proper MIDI grounding and isolation where needed
- **Synth Ventilation:** Adequate cooling for internal synth rack
- Keep audio lines isolated from digital control signals
- Bring spare fuses, MIDI cables, and toolkit for field maintenance

---

## 11) Appendix — Updated Pin/Message Map
| Control | Teensy Pin | MIDI Message | Synth Parameter (NTS1 MK2) |
|---|---|---|---|
| B1–B10 | D2–D11 | Note 60–69 | Sequencer Triggers |
| K1–K6 | A0–A5 | CC 20–25 | Osc/Filter/EG/LFO |
| Joystick U/D/L/R | D22–D25 | CC 50–53 | Seq Control |
| Switch S1–S3 | D26–D28 | CC 60–62 | Mode/Profile/FX |
| Portal LEDs | D14 | - | Visual Feedback |

**Portal Animation Cues (Pi → Teensy):**
- Program change (different visual patterns)
- Rate control (sync with BPM/activity)
- Idle mode (ambient/low-intensity patterns)

---

**Files referenced in this plan:**  
- Portal source code: `~/Projects/coding/arduino/uno/arduino-infinity-portal`
- Wiring diagram: `teensy_wiring_diagram.png` (to be updated)
- Control panel layout: `control_panel_layout.png` (to be updated)
- Cabinet sketch: `cabinet_front_side.png` (to be updated)