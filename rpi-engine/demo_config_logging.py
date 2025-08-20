#!/usr/bin/env python3
"""Demo script to show the comprehensive configuration logging feature.

This script loads the configuration and shows how all values are logged
during initialization for complete transparency.
"""

import sys
import logging
sys.path.insert(0, 'src')

from config import load_config
from logging_utils import configure_logging

def demo_config_logging():
    """Demonstrate the comprehensive configuration logging."""
    print("=== Configuration Logging Demo ===")
    print("\nThis shows how the engine logs all configuration values at startup")
    print("for complete transparency about what settings are being used.\n")
    
    # Load config and set up logging
    cfg = load_config('config.yaml')
    configure_logging('INFO')
    log = logging.getLogger("demo")
    
    # Simulate the configuration logging from main.py
    log.info("=== CONFIGURATION SUMMARY ===")
    log.info(f"config_file=config.yaml")
    log.info(f"log_level=INFO")
    
    # MIDI Configuration
    log.info(f"midi_input_port={cfg.midi.input_port}")
    log.info(f"midi_output_port={cfg.midi.output_port}")
    log.info(f"midi_input_channel={cfg.midi.input_channel}")
    log.info(f"midi_output_channel={cfg.midi.output_channel}")
    
    # Sequencer Configuration
    log.info(f"sequencer_steps={cfg.sequencer.steps}")
    log.info(f"sequencer_bpm={cfg.sequencer.bpm}")
    log.info(f"sequencer_swing={cfg.sequencer.swing}")
    log.info(f"sequencer_density={cfg.sequencer.density}")
    log.info(f"sequencer_quantize_scale_changes={cfg.sequencer.quantize_scale_changes}")
    
    # Phase 5.5 Sequencer Features
    log.info(f"sequencer_step_pattern={cfg.sequencer.step_pattern}")
    log.info(f"sequencer_direction_pattern={cfg.sequencer.direction_pattern}")
    
    # Scales
    log.info(f"available_scales={cfg.scales}")
    
    # Mutation Configuration
    log.info(f"mutation_interval_min_s={cfg.mutation.interval_min_s}")
    log.info(f"mutation_interval_max_s={cfg.mutation.interval_max_s}")
    log.info(f"mutation_max_changes_per_cycle={cfg.mutation.max_changes_per_cycle}")
    
    # Idle Configuration
    log.info(f"idle_timeout_ms={cfg.idle.timeout_ms}")
    log.info(f"idle_ambient_profile={cfg.idle.ambient_profile}")
    log.info(f"idle_fade_in_ms={cfg.idle.fade_in_ms}")
    log.info(f"idle_fade_out_ms={cfg.idle.fade_out_ms}")
    
    # Synth Configuration
    log.info(f"synth_backend={cfg.synth.backend}")
    log.info(f"synth_voices={cfg.synth.voices}")
    
    # API Configuration
    log.info(f"api_enabled={cfg.api.enabled}")
    log.info(f"api_port={cfg.api.port}")
    
    # Mapping Configuration Summary
    button_mappings = list(cfg.mapping.get('buttons', {}).keys()) if cfg.mapping else []
    cc_mappings = list(cfg.mapping.get('ccs', {}).keys()) if cfg.mapping else []
    log.info(f"button_mappings={button_mappings}")
    log.info(f"cc_mappings={cc_mappings}")
    log.info("=== END CONFIGURATION ===")
    
    print("\n=== Summary ===")
    print("✓ All configuration values are now logged at startup")
    print("✓ No ambiguity about what settings are being used")
    print("✓ Easy to debug configuration issues")
    print("✓ Clear audit trail of all parameters")
    
    print(f"\nKey settings from your config:")
    print(f"  • Direction pattern: {cfg.sequencer.direction_pattern}")
    print(f"  • Step pattern: {cfg.sequencer.step_pattern}")
    print(f"  • Sequence length: {cfg.sequencer.steps} steps")
    print(f"  • BPM: {cfg.sequencer.bpm}")
    print(f"  • Available scales: {len(cfg.scales)} scales")

if __name__ == '__main__':
    demo_config_logging()
