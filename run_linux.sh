#!/bin/bash

# Wrapper script for audio_leveler.py for Sonarr/Radarr on Linux

# Help Menu
if [ -z "$1" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo ""
    echo "Media Audio Leveler"
    echo ""
    echo "  A professional-grade Python automation suite for audio normalization."
    echo ""
    echo "Usage:"
    echo "  run_linux.sh [options]"
    echo ""
    echo "Options:"
    echo ""
    echo "  --file <file>             Process a single media file."
    echo "  --batch <directory>       Run in batch mode on a directory."
    echo "  --cleanup                  Scan for and remove orphaned temporary files."
    echo "  --no-update-check          Skip the GitHub update check."
    echo "  --update                   Check for updates and exit."
    echo "  --help, -h                 Show this help message."
    echo ""
    echo "Integration:"
    echo "  The script auto-detects Sonarr and Radarr environments."
    echo ""
    exit 0
fi

# Handle the Test event from Sonarr/Radarr
if [ "$sonarr_eventtype" = "Test" ]; then
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PYTHON_CMD="python3"
    if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
        PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
    fi
    "$PYTHON_CMD" "$SCRIPT_DIR/audio_leveler.py" --arr-test "Sonarr"
    exit 0
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON_CMD="python3"

# Check if a venv exists and set the python command accordingly
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
fi

# Execute the python script, passing all arguments.
"$PYTHON_CMD" "$SCRIPT_DIR/audio_leveler.py" "$@"
