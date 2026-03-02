#!/bin/bash

# Dynamic Directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Path Expansion
export PATH="$SCRIPT_DIR/bin:$PATH"

# Venv Enforcement
PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"

# Arr Detection & Failure Handling
if [[ "$sonarr_eventtype" == "Test" || "$radarr_eventtype" == "Test" ]]; then
    if [ ! -x "$PYTHON_CMD" ]; then
        echo "ERROR: Python virtual environment not found at '$PYTHON_CMD'. Please run the setup script." >&2
        exit 1
    fi
    "$PYTHON_CMD" "$SCRIPT_DIR/audio_leveler.py"
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
-update                   Check for updates and exit."
    echo "  --help, -h                 Show this help message."
    echo ""
    echo "Integration:"
    echo "  The script auto-detects Sonarr and Radarr environments."
    echo ""
    exit 0
fi

# Execute the python script, passing all arguments.
"$PYTHON_CMD" "$SCRIPT_DIR/audio_leveler.py" "$@"
