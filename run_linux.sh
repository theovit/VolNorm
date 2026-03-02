#!/bin/bash

# Wrapper script for audio_leveler.py for Sonarr/Radarr on Linux

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Set the python command
PYTHON_CMD="python3"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

# Verify that the venv exists
if [ -f "$VENV_PYTHON" ]; then
    PYTHON_CMD="$VENV_PYTHON"
else
    # If venv is missing and we're not in a test environment, exit with an error.
    # The 'Test' event from *arrs does not require the venv.
    if [ "$sonarr_eventtype" != "Test" ] && [ "$radarr_eventtype" != "Test" ]; then
        echo "ERROR: Python virtual environment not found at '$VENV_PYTHON'" >&2
        echo "Please run the setup script to create the virtual environment." >&2
        exit 1
    fi
fi

# Handle the Test event from Sonarr/Radarr
if [ "$sonarr_eventtype" = "Test" ] || [ "$radarr_eventtype" = "Test" ]; then
    EVENT_TYPE=${sonarr_eventtype:-$radarr_eventtype}
    APP_NAME=${sonarr_eventtype:+Sonarr}
    APP_NAME=${radarr_eventtype:+Radarr}
    
    echo "$APP_NAME Event: $EVENT_TYPE" >> "$SCRIPT_DIR/wrapper.log"
    "$PYTHON_CMD" "$SCRIPT_DIR/audio_leveler.py" --arr-test "$APP_NAME"
    exit 0
fi

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

# Execute the python script, passing all arguments.
"$PYTHON_CMD" "$SCRIPT_DIR/audio_leveler.py" "$@"
