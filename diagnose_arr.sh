#!/bin/bash

# Diagnostic script for Sonarr/Radarr custom script integration.

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
LOG_FILE="$SCRIPT_DIR/diagnostics.log"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
TEST_ENV_SCRIPT="$SCRIPT_DIR/test_env.py"

# --- Functions ---
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_divider() {
    echo "--------------------------------------------------" >> "$LOG_FILE"
}

# --- Start Diagnostics ---
# Clear previous log file
> "$LOG_FILE"

log_message "Starting diagnostics..."
log_divider

# Log Trigger Event
EVENT_TYPE=${sonarr_eventtype:-$radarr_eventtype}
if [ -n "$EVENT_TYPE" ]; then
    log_message "Trigger Event: $EVENT_TYPE"
else
    log_message "Trigger Event: Manual execution"
fi
log_divider

# Log Environment Variables
log_message "Dumping Arr environment variables:"
env | grep -E '^(sonarr_|radarr_|lidarr_|readarr_)' >> "$LOG_FILE"
log_divider

# Log User and Context
log_message "User and context:"
echo -n "User: " >> "$LOG_FILE"
whoami >> "$LOG_FILE"
echo -n "Groups: " >> "$LOG_FILE"
groups >> "$LOG_FILE"
echo -n "Current Directory: " >> "$LOG_FILE"
pwd >> "$LOG_FILE"
log_divider

# --- Checks ---
CHECKS_FAILED=0

# Check for Virtual Environment
log_message "Checking for Python virtual environment..."
if [ -x "$VENV_PYTHON" ]; then
    log_message "SUCCESS: Virtual environment found and executable at '$VENV_PYTHON'."
else
    log_message "ERROR: Python virtual environment not found or not executable at '$VENV_PYTHON'."
    echo "ERROR: Python virtual environment not found or not executable." >&2
    CHECKS_FAILED=1
fi
log_divider

# Check for FFmpeg and FFprobe
log_message "Checking for FFmpeg and FFprobe..."
FFMPEG_PATH="/usr/bin/ffmpeg"
FFPROBE_PATH="/usr/bin/ffprobe"

if ls -l "$FFMPEG_PATH" &>/dev/null; then
    log_message "SUCCESS: ffmpeg found at '$FFMPEG_PATH'."
else
    log_message "ERROR: ffmpeg not found or no permissions at '$FFMPEG_PATH'."
    echo "ERROR: ffmpeg not found or no permissions at '$FFMPEG_PATH'." >&2
    CHECKS_FAILED=1
fi

if ls -l "$FFPROBE_PATH" &>/dev/null; then
    log_message "SUCCESS: ffprobe found at '$FFPROBE_PATH'."
else
    log_message "ERROR: ffprobe not found or no permissions at '$FFPROBE_PATH'."
    echo "ERROR: ffprobe not found or no permissions at '$FFPROBE_PATH'." >&2
    CHECKS_FAILED=1
fi
log_divider

# Run Companion Python Script if 'Test' event
if [ "$EVENT_TYPE" = "Test" ]; then
    log_message "Test event detected. Running companion Python script..."
    if [ -f "$TEST_ENV_SCRIPT" ]; then
        "$VENV_PYTHON" "$TEST_ENV_SCRIPT"
        if [ $? -eq 0 ]; then
            log_message "SUCCESS: Companion Python script executed successfully."
        else
            log_message "ERROR: Companion Python script failed to execute."
            echo "ERROR: Companion Python script failed." >&2
            CHECKS_FAILED=1
        fi
    else
        log_message "ERROR: Companion script 'test_env.py' not found."
        echo "ERROR: 'test_env.py' not found." >&2
        CHECKS_FAILED=1
    fi
    log_divider
fi

# --- Final Result ---
if [ $CHECKS_FAILED -eq 0 ]; then
    log_message "All checks passed."
    exit 0
else
    log_message "One or more checks failed."
    exit 1
fi
