#!/bin/bash
# Raspberry Pi startup script for Mystery Music Engine
# This script handles common ALSA and MIDI setup issues on Raspberry Pi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/startup.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

log "Starting Mystery Music Engine setup for Raspberry Pi"
log "Script directory: $SCRIPT_DIR"
log "Log file: $LOG_FILE"

# Check if we're running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    log "WARNING: This script is designed for Raspberry Pi systems"
fi

# Check and load ALSA sequencer module
log "Checking ALSA sequencer module..."
if ! lsmod | grep -q snd_seq; then
    log "ALSA sequencer module not loaded, attempting to load..."
    if sudo modprobe snd-seq 2>&1 | tee -a "$LOG_FILE"; then
        log "Successfully loaded ALSA sequencer module"
    else
        log "ERROR: Failed to load ALSA sequencer module"
        log "You may need to install ALSA utilities: sudo apt-get install alsa-utils"
    fi
else
    log "ALSA sequencer module already loaded"
fi

# Check user groups
log "Checking user groups..."
CURRENT_USER=$(whoami)
if ! groups "$CURRENT_USER" | grep -q audio; then
    log "WARNING: User $CURRENT_USER is not in 'audio' group"
    log "Add to group with: sudo usermod -a -G audio $CURRENT_USER"
    log "Then logout and login again"
fi

if ! groups "$CURRENT_USER" | grep -q dialout; then
    log "WARNING: User $CURRENT_USER is not in 'dialout' group"
    log "Add to group with: sudo usermod -a -G dialout $CURRENT_USER"
fi

# Check ALSA sequencer status
log "Checking ALSA sequencer status..."
if command_exists aconnect; then
    if aconnect -l &>"$LOG_FILE.alsa"; then
        log "ALSA sequencer is working, clients listed in $LOG_FILE.alsa"
    else
        log "ERROR: ALSA sequencer not responding properly"
    fi
else
    log "WARNING: aconnect command not found, install alsa-utils"
fi

# Check for USB MIDI devices
log "Checking for USB MIDI devices..."
if command_exists lsusb; then
    USB_MIDI=$(lsusb | grep -i -E "(midi|audio|teensy|arduino)" || true)
    if [ -n "$USB_MIDI" ]; then
        log "Found potential MIDI devices:"
        echo "$USB_MIDI" | while read -r line; do
            log "  $line"
        done
    else
        log "No obvious USB MIDI devices found"
        log "Full USB device list written to $LOG_FILE.usb"
        lsusb > "$LOG_FILE.usb"
    fi
fi

# Check Python virtual environment
log "Checking Python virtual environment..."
if [ -d "$SCRIPT_DIR/.venv" ]; then
    log "Virtual environment found at $SCRIPT_DIR/.venv"
    source "$SCRIPT_DIR/.venv/bin/activate"
    log "Activated virtual environment"
    
    # Check mido installation
    if python -c "import mido; print(f'mido version: {mido.__version__}')" 2>&1 | tee -a "$LOG_FILE"; then
        log "mido is properly installed"
    else
        log "ERROR: mido is not properly installed"
        log "Install with: pip install mido python-rtmidi"
    fi
else
    log "WARNING: Virtual environment not found at $SCRIPT_DIR/.venv"
    log "Create with: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

# Test MIDI functionality
log "Testing MIDI functionality..."
if [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    if python "$SCRIPT_DIR/test_rpi_midi.py" 2>&1 | tee -a "$LOG_FILE.midi_test"; then
        log "MIDI test completed successfully"
    else
        log "WARNING: MIDI test had issues, check $LOG_FILE.midi_test"
    fi
fi

# Function to start the engine
start_engine() {
    log "Starting Mystery Music Engine..."
    
    # Ensure we're in the right directory and virtual environment
    cd "$SCRIPT_DIR"
    source .venv/bin/activate
    
    # Choose between robust and standard MIDI handling
    if [ "$1" = "--robust-midi" ]; then
        log "Using robust MIDI handling for Raspberry Pi"
        python main_rpi.py --use-robust-midi --config config.yaml 2>&1 | tee -a "$LOG_FILE.engine"
    else
        log "Using standard MIDI handling"
        python src/main.py --config config.yaml 2>&1 | tee -a "$LOG_FILE.engine"
    fi
}

# Parse command line arguments
case "${1:-}" in
    "start")
        start_engine "${2:-}"
        ;;
    "start-robust")
        start_engine "--robust-midi"
        ;;
    "test")
        log "Running diagnostic tests..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate"
            python "$SCRIPT_DIR/debug_rpi_midi.py" 2>&1 | tee -a "$LOG_FILE.diagnostics"
        else
            log "ERROR: Virtual environment not found"
            exit 1
        fi
        ;;
    "setup")
        log "Setup completed. Check logs above for any issues."
        log "Next steps:"
        log "  - To test MIDI: $0 test"
        log "  - To start engine: $0 start"
        log "  - To start with robust MIDI: $0 start-robust"
        ;;
    *)
        echo "Usage: $0 {setup|start|start-robust|test}"
        echo "  setup        - Check system setup and dependencies"
        echo "  start        - Start the engine with standard MIDI"
        echo "  start-robust - Start the engine with Raspberry Pi optimized MIDI"
        echo "  test         - Run comprehensive MIDI diagnostics"
        echo ""
        echo "Log files are written to $SCRIPT_DIR/"
        exit 1
        ;;
esac

log "Script completed"
