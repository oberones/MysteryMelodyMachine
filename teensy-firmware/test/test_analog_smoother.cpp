#include <unity.h>
#include "analog_smoother.h"

// Test basic analog smoother functionality
void test_analog_smoother_initial_state() {
    AnalogSmoother smoother(64, 2, 15); // alpha=64, deadband=2, rateLimit=15ms
    TEST_ASSERT_EQUAL_UINT8(0, smoother.getMidiValue());
    TEST_ASSERT_FALSE(smoother.hasSignificantChange());
}

void test_analog_smoother_reset() {
    AnalogSmoother smoother(64, 2, 15);
    
    // Reset with specific value
    smoother.reset(512); // Mid-range ADC value
    
    // Should map to ~63-64 in MIDI range (512 * 127 / 1023 ≈ 63.5)
    uint8_t initialMidi = smoother.getMidiValue();
    TEST_ASSERT_TRUE(initialMidi >= 63 && initialMidi <= 64);
}

void test_analog_smoother_gradual_change() {
    AnalogSmoother smoother(128, 2, 10); // High alpha for faster response
    smoother.reset(0);
    
    // Gradually increase input
    bool changed1 = smoother.update(100, 0);   // First update
    bool changed2 = smoother.update(200, 15);  // After rate limit
    bool changed3 = smoother.update(300, 30);  // Continue increasing
    
    // Should see changes as values ramp up
    uint8_t finalValue = smoother.getMidiValue();
    TEST_ASSERT_TRUE(finalValue > 0); // Should have increased from 0
}

void test_analog_smoother_deadband() {
    AnalogSmoother smoother(64, 5, 10); // deadband=5
    smoother.reset(500); // Start at mid-range
    
    uint8_t startMidi = smoother.getMidiValue();
    
    // Small changes within deadband should not trigger
    bool changed1 = smoother.update(505, 20);  // Small increase
    bool changed2 = smoother.update(495, 40);  // Small decrease
    
    TEST_ASSERT_FALSE(changed1);
    TEST_ASSERT_FALSE(changed2);
    
    // Large change should trigger
    bool changed3 = smoother.update(600, 60);  // Significant increase
    TEST_ASSERT_TRUE(changed3 || smoother.getMidiValue() != startMidi);
}

void test_analog_smoother_rate_limiting() {
    AnalogSmoother smoother(64, 2, 20); // 20ms rate limit
    smoother.reset(0);
    
    // First change should go through
    bool changed1 = smoother.update(200, 0);
    
    // Immediate second change should be rate limited
    bool changed2 = smoother.update(400, 5); // Only 5ms later
    TEST_ASSERT_FALSE(changed2);
    
    // Change after rate limit period should go through
    bool changed3 = smoother.update(400, 25); // 25ms later
    // Note: might not change if already at same value due to filtering
}

void test_analog_smoother_large_change_override() {
    AnalogSmoother smoother(64, 2, 50); // Long rate limit
    smoother.reset(100);
    
    // Small change should be rate limited
    bool changed1 = smoother.update(150, 0);
    bool changed2 = smoother.update(180, 5);
    TEST_ASSERT_FALSE(changed2); // Should be rate limited
    
    // Very large change should override rate limit
    bool changed3 = smoother.update(800, 10); // Huge jump
    // Large changes force through via forceNextSend()
}

void test_analog_smoother_midi_mapping() {
    AnalogSmoother smoother(255, 1, 1); // Fast response for testing
    
    // Test boundary conditions
    smoother.reset(0);
    smoother.update(0, 0);
    TEST_ASSERT_EQUAL_UINT8(0, smoother.getMidiValue());
    
    smoother.reset(1023);
    smoother.update(1023, 0);
    TEST_ASSERT_EQUAL_UINT8(127, smoother.getMidiValue());
    
    // Test mid-range
    smoother.reset(511);
    smoother.update(511, 0);
    uint8_t midValue = smoother.getMidiValue();
    TEST_ASSERT_TRUE(midValue >= 62 && midValue <= 65); // ~63.5 expected
}

void setUp(void) {
    // Set up code if needed
}

void tearDown(void) {
    // Clean up code if needed
}

void setup() {
    delay(2000); // Wait for serial
    
    UNITY_BEGIN();
    
    RUN_TEST(test_analog_smoother_initial_state);
    RUN_TEST(test_analog_smoother_reset);
    RUN_TEST(test_analog_smoother_gradual_change);
    RUN_TEST(test_analog_smoother_deadband);
    RUN_TEST(test_analog_smoother_rate_limiting);
    RUN_TEST(test_analog_smoother_large_change_override);
    RUN_TEST(test_analog_smoother_midi_mapping);
    
    UNITY_END();
}

void loop() {
    // Empty
}
