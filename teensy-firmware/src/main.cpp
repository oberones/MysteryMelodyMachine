#include <Arduino.h>
#include <FastLED.h>
#include "pins.h"
#include "config.h"

// Forward declarations
void portalStartupSequence();
void scanInputs();
void updatePortal();

// ===== GLOBAL VARIABLES =====
CRGB leds[LED_COUNT];
elapsedMicros mainLoopTimer;
elapsedMicros portalFrameTimer;
elapsedMillis blinkTimer;
bool builtinLedState = false;

// ===== SETUP FUNCTION =====
void setup() {
    // Initialize Serial for debugging
    Serial.begin(115200);
    delay(1000);  // Give time for serial to initialize
    
    Serial.println("=== Mystery Melody Machine Teensy Firmware ===");
    Serial.println("Phase 0: Bootstrap");
    Serial.printf("Firmware compiled: %s %s\n", __DATE__, __TIME__);
    Serial.println("USB Type: MIDI");
    
    // Initialize built-in LED for blink test
    pinMode(BUILTIN_LED_PIN, OUTPUT);
    digitalWrite(BUILTIN_LED_PIN, LOW);
    
    // Initialize all button pins as inputs with pullups
    for (int i = 0; i < BUTTON_COUNT; i++) {
        pinMode(BUTTON_PINS[i], INPUT_PULLUP);
        Serial.printf("Button %d: Pin %d configured\n", i, BUTTON_PINS[i]);
    }
    
    // Initialize joystick pins
    pinMode(JOY_UP_PIN, INPUT_PULLUP);
    pinMode(JOY_DOWN_PIN, INPUT_PULLUP);
    pinMode(JOY_LEFT_PIN, INPUT_PULLUP);
    pinMode(JOY_RIGHT_PIN, INPUT_PULLUP);
    Serial.println("Joystick pins configured");
    
    // Initialize switch pins
    for (int i = 0; i < SWITCH_COUNT; i++) {
        pinMode(SWITCH_PINS[i], INPUT_PULLUP);
        Serial.printf("Switch %d: Pin %d configured\n", i, SWITCH_PINS[i]);
    }
    
    // Initialize FastLED for portal
    FastLED.addLeds<WS2812B, LED_DATA_PIN, GRB>(leds, LED_COUNT);
    FastLED.setBrightness(LED_BRIGHTNESS_MAX);
    FastLED.clear();
    FastLED.show();
    Serial.printf("FastLED initialized: %d LEDs on pin %d\n", LED_COUNT, LED_DATA_PIN);
    
    // Test MIDI functionality (only if MIDI is available)
    Serial.println("Testing MIDI enumeration...");
    #ifdef USB_MIDI
    usbMIDI.sendNoteOn(60, 64, MIDI_CHANNEL);  // Test note
    delay(100);
    usbMIDI.sendNoteOff(60, 0, MIDI_CHANNEL);
    Serial.println("MIDI test note sent (C4)");
    #else
    Serial.println("MIDI not available in this USB mode");
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

// ===== BASIC INPUT SCANNING =====
void scanInputs() {
    // This is a placeholder for Phase 1
    // For now, just scan one button for basic MIDI test
    static bool lastButton0State = true;  // pullup = true when not pressed
    
    bool currentButton0State = digitalRead(BUTTON_PINS[0]);
    if (currentButton0State != lastButton0State) {
        if (!currentButton0State) {  // Button pressed (pullup inverted)
            #ifdef USB_MIDI
            usbMIDI.sendNoteOn(BUTTON_NOTES[0], MIDI_VELOCITY, MIDI_CHANNEL);
            #endif
            Serial.printf("Button 0 pressed - Note On: %d\n", BUTTON_NOTES[0]);
        } else {  // Button released
            #ifdef USB_MIDI
            usbMIDI.sendNoteOff(BUTTON_NOTES[0], 0, MIDI_CHANNEL);
            #endif
            Serial.printf("Button 0 released - Note Off: %d\n", BUTTON_NOTES[0]);
        }
        lastButton0State = currentButton0State;
    }
}

// ===== BASIC PORTAL ANIMATION =====
void updatePortal() {
    // Simple breathing effect for Phase 0
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
        
        // Basic input scanning
        scanInputs();
        
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
        Serial.printf("Heartbeat - System running normally\n");
        #endif
    }
}
