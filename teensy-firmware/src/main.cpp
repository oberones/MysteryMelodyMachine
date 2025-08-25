#include <Arduino.h>
#include <FastLED.h>
#include "pins.h"
#include "config.h"
#include "input_scanner.h"
#include "midi_out.h"
#include "input_midi_mapper.h"

// Forward declarations
void portalStartupSequence();
void updatePortal();

// ===== GLOBAL VARIABLES =====
CRGB leds[LED_COUNT];
elapsedMicros mainLoopTimer;
elapsedMicros portalFrameTimer;
elapsedMillis blinkTimer;
bool builtinLedState = false;

// Phase 1: Input system modules
InputScanner inputScanner;
MidiOut midiOut;
InputMidiMapper inputMapper(inputScanner, midiOut);

// ===== SETUP FUNCTION =====
void setup() {
    // Initialize Serial for debugging
    Serial.begin(115200);
    delay(1000);  // Give time for serial to initialize
    
    Serial.println("=== Mystery Melody Machine Teensy Firmware ===");
    Serial.println("Phase 1: Raw Input + MIDI");
    Serial.printf("Firmware compiled: %s %s\n", __DATE__, __TIME__);
    #ifdef USB_MIDI
    Serial.println("USB Type: MIDI");
    #else
    Serial.println("USB Type: Serial (Debug Mode)");
    #endif
    
    // Initialize built-in LED for blink test
    pinMode(BUILTIN_LED_PIN, OUTPUT);
    digitalWrite(BUILTIN_LED_PIN, LOW);
    
    // Initialize Phase 1 input system
    Serial.println("Initializing input scanner...");
    inputScanner.begin();
    
    Serial.println("Initializing MIDI output...");
    midiOut.begin();
    
    Serial.printf("Input mapping: %d buttons, %d pots, %d switches, 4-way joystick\n", 
                  BUTTON_COUNT, POT_COUNT, SWITCH_COUNT);
    
    // Initialize FastLED for portal
    FastLED.addLeds<WS2812B, LED_DATA_PIN, GRB>(leds, LED_COUNT);
    FastLED.setBrightness(LED_BRIGHTNESS_MAX);
    FastLED.clear();
    FastLED.show();
    Serial.printf("FastLED initialized: %d LEDs on pin %d\n", LED_COUNT, LED_DATA_PIN);
    
    // Test MIDI functionality (only if MIDI is available)
    Serial.println("Testing MIDI enumeration...");
    #ifdef USB_MIDI
    midiOut.sendNoteOn(60, 64, MIDI_CHANNEL);  // Test note
    delay(100);
    midiOut.sendNoteOff(60, 0, MIDI_CHANNEL);
    Serial.println("MIDI test note sent (C4)");
    #else
    Serial.println("MIDI not available - debug mode active");
    #endif
    
    // Portal startup sequence
    Serial.println("Starting portal initialization sequence...");
    portalStartupSequence();
    
    Serial.println("=== Setup Complete ===");
    Serial.printf("Main loop target: %d Hz\n", SCAN_HZ);
    Serial.printf("Portal target: %d Hz\n", PORTAL_FPS);
    Serial.println("Entering main loop...");
}

// ===== PORTAL STARTUP SEQUENCE =====
void portalStartupSequence() {
    // Simple startup animation: sweep colors around the ring
    for (int cycle = 0; cycle < 3; cycle++) {
        for (int i = 0; i < LED_COUNT; i++) {
            // Clear all LEDs
            FastLED.clear();
            
            // Set current LED to a rotating hue
            uint8_t hue = (i * 255 / LED_COUNT) + (cycle * 85);
            leds[i] = CHSV(hue, 255, 128);
            
            // Set a few trailing LEDs for a comet effect
            for (int j = 1; j <= 3 && i - j >= 0; j++) {
                leds[i - j] = CHSV(hue, 255, 128 / (j + 1));
            }
            
            FastLED.show();
            delay(30);  // 30ms per step
        }
    }
    
    // Fade to black
    for (int brightness = 128; brightness >= 0; brightness -= 4) {
        FastLED.setBrightness(brightness);
        FastLED.show();
        delay(20);
    }
    
    FastLED.setBrightness(LED_BRIGHTNESS_MAX);
    FastLED.clear();
    FastLED.show();
    
    Serial.println("Portal startup sequence complete");
}

// ===== BASIC PORTAL ANIMATION =====
void updatePortal() {
    // Simple breathing effect for Phase 1
    static uint32_t animationPhase = 0;
    animationPhase += 2;
    
    uint8_t brightness = (sin8(animationPhase / 4) / 4) + 32;  // Gentle breathing
    
    for (int i = 0; i < LED_COUNT; i++) {
        // Gentle blue breathing
        leds[i] = CHSV(160, 200, brightness);
    }
    
    FastLED.show();
}

// ===== MAIN LOOP =====
void loop() {
    // Main scan loop at ~1kHz
    if (mainLoopTimer >= (1000000 / SCAN_HZ)) {
        mainLoopTimer -= (1000000 / SCAN_HZ);
        
        // Phase 1: Full input scanning and MIDI output
        inputScanner.scan();
        inputMapper.processInputs();
        
        // Handle any incoming MIDI (for future portal cues)
        #ifdef USB_MIDI
        while (usbMIDI.read()) {
            // Placeholder for portal cue handling
        }
        #endif
    }
    
    // Portal animation at ~60Hz
    if (portalFrameTimer >= PORTAL_FRAME_INTERVAL_US) {
        portalFrameTimer -= PORTAL_FRAME_INTERVAL_US;
        updatePortal();
    }
    
    // Built-in LED blink every second to show we're alive
    if (blinkTimer >= 1000) {
        blinkTimer -= 1000;
        builtinLedState = !builtinLedState;
        digitalWrite(BUILTIN_LED_PIN, builtinLedState);
        
        #if DEBUG
        // Simple memory check for Teensy 4.1
        Serial.printf("Heartbeat - Phase 1 system running\n");
        #endif
    }
}
