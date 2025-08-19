#!/bin/bash
# Virtual Environment Setup Verification Script
# Run this to verify your Python virtual environment is properly configured

echo "Mystery Music Engine - Virtual Environment Setup Verification"
echo "=============================================================="

# Check if we're in the project root
if [ ! -f "SPEC.md" ] || [ ! -d ".venv" ]; then
    echo "❌ ERROR: Please run this script from the project root directory"
    echo "   Expected files: SPEC.md, .venv/ directory"
    exit 1
fi

echo "✓ Project root directory confirmed"

# Check if virtual environment exists
if [ ! -f ".venv/bin/activate" ]; then
    echo "❌ ERROR: Virtual environment not found at .venv/"
    echo "   Please create it with: python3 -m venv .venv"
    exit 1
fi

echo "✓ Virtual environment found"

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "✓ Python version: $PYTHON_VERSION"

# Check if requirements are installed
echo "Checking dependencies..."
if python -c "import mido, pydantic, yaml" 2>/dev/null; then
    echo "✓ Core dependencies available"
else
    echo "⚠️  Installing dependencies..."
    pip install -r rpi/engine/requirements.txt
    if [ $? -eq 0 ]; then
        echo "✓ Dependencies installed successfully"
    else
        echo "❌ ERROR: Failed to install dependencies"
        exit 1
    fi
fi

# Test Phase 2 module imports
echo "Testing Phase 2 module imports..."
if python -c "import sys; sys.path.insert(0, 'rpi/engine/src'); import state, sequencer, action_handler" 2>/dev/null; then
    echo "✓ Phase 2 modules import successfully"
else
    echo "❌ ERROR: Phase 2 modules failed to import"
    exit 1
fi

# Test basic functionality
echo "Testing basic functionality..."
if python -c "
import sys
sys.path.insert(0, 'rpi/engine/src')
from state import get_state, reset_state
from sequencer import HighResClock
from action_handler import ActionHandler

# Test state
reset_state()
state = get_state()
state.set('bpm', 120.0)
assert state.get('bpm') == 120.0

# Test clock
clock = HighResClock(bpm=120.0)
assert clock.bpm == 120.0

# Test action handler
handler = ActionHandler(state)
print('Basic functionality test passed')
" 2>/dev/null; then
    echo "✓ Basic functionality test passed"
else
    echo "❌ ERROR: Basic functionality test failed"
    exit 1
fi

echo ""
echo "🎉 Virtual environment setup verification PASSED!"
echo ""
echo "You can now run:"
echo "  source .venv/bin/activate"
echo "  python rpi/engine/src/main.py --config rpi/engine/config.yaml --log-level INFO"
echo ""
echo "Or run tests with:"
echo "  source .venv/bin/activate"
echo "  pytest rpi/engine/tests/ -v"
