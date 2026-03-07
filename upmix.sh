#!/bin/bash

# Upmix 2.0 Stereo to 3.1 Audio

# --- Configuration ---
LOG_FILE="upmix.log"

# --- Functions ---

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# --- Main Script ---

# Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    log "ERROR: ffmpeg could not be found. Please install it."
    exit 1
fi

# Check for arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file> | -r <directory>"
    exit 1
fi

process_file() {
    local file="$1"
    local temp_file="${file%.*}_temp.${file##*.}"

    log "Processing file: $file"

    # Upmix to 3.1 using a custom filtergraph
    ffmpeg -i "$file" \
    -map 0:v -c:v copy \
    -map 0:a -c:a copy \
    -filter_complex "[0:a:m:language:eng]surround=3.1:level_in=1:level_out=1[31]" \
    -map "[31]" -c:a:2 ac3 \
    -metadata:s:a:2 title="English 3.1 Upmix" \
    -metadata:s:a:2 language=eng \
    -disposition:a:0 0 \
    -disposition:a:1 0 \
    -disposition:a:2 default \
    "$temp_file"

    if [ $? -eq 0 ]; then
        mv "$temp_file" "$file"
        log "Successfully processed: $file"
    else
        log "ERROR: FFmpeg failed for: $file"
        rm -f "$temp_file"
    fi
}

# Mode selection
if [ "$1" == "-r" ]; then
    # Batch mode
    if [ -d "$2" ]; then
        find "$2" -type f -name "*.mkv" -o -name "*.mp4" | while read -r file; do
            process_file "$file"
        done
    else
        echo "ERROR: Directory not found: $2"
        exit 1
    fi
else
    # Single file mode
    if [ -f "$1" ]; then
        process_file "$1"
    else
        echo "ERROR: File not found: $1"
        exit 1
    fi
fi
