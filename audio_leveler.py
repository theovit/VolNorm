#!/usr/bin/env python3
"""
Media-Audio-Leveler: A professional-grade Python automation suite for audio normalization.

This script uses FFmpeg to perform two-pass audio normalization based on EBU R128 standards.
It's designed for integration with media servers like Sonarr and Radarr (WIP), and can also be run in batch mode.
"""

import os
import sys
import subprocess
import json
import argparse
import logging
import re
from pathlib import Path
import time
import shutil
import urllib.request

# --- Configuration ---
VERSION = "1.2.1"
GITHUB_REPO_URL = "https://api.github.com/repos/theovit/VolNorm/releases/latest"
FFMPEG_PATH = shutil.which('ffmpeg')
FFPROBE_PATH = shutil.which('ffprobe')
LOUDNESS_TARGETS = {
    "I": -24.0,
    "LRA": 13.0,
    "TP": -2.0
}
LOUDNESS_TOLERANCE = 0.5
SUPPORTED_EXTENSIONS = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
FORMAT_MAP = {
    '.mkv': 'matroska',
    '.mp4': 'mp4',
    '.avi': 'avi',
    '.mov': 'mov',
    '.wmv': 'asf',
    '.flv': 'flv',
    '.webm': 'webm'
}
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_FILE = Path(__file__).parent / 'leveler.log'

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, handlers=[
    logging.FileHandler(LOG_FILE, encoding='utf-8'),
    logging.StreamHandler(sys.stdout)
])

def check_for_updates():
    """Checks for a new version and attempts to auto-update if in a git repo."""
    logging.info("Checking for updates...")
    
    script_dir = Path(__file__).parent
    git_dir = script_dir / ".git"

    if git_dir.is_dir():
        try:
            # Check if git is installed
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            
            logging.info("Git repository detected. Attempting to auto-update...")
            
            # Fetch latest changes from remote
            subprocess.run(['git', 'fetch'], cwd=script_dir, capture_output=True, check=True)
            
            # Check if local is behind remote
            status_result = subprocess.run(['git', 'status', '-uno'], cwd=script_dir, capture_output=True, text=True, check=True)
            
            if "Your branch is behind" in status_result.stdout:
                logging.warning("A new version is available. Pulling changes from remote...")
                pull_result = subprocess.run(['git', 'pull'], cwd=script_dir, capture_output=True, text=True, check=True)
                logging.info("Update successful. Please restart the script.")
                logging.info(f"Git output:\n{pull_result.stdout}")
                sys.exit(0)
            else:
                logging.info("You are running the latest version.")
                
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.warning("Git command failed or git is not installed. Falling back to GitHub release check.")
            check_for_updates_fallback()
    else:
        check_for_updates_fallback()

def check_for_updates_fallback():
    """Fallback to checking for a new version on GitHub via API."""
    if "YOUR_USERNAME" in GITHUB_REPO_URL:
        logging.warning("Update check skipped: GitHub repository URL is not configured. Please edit 'audio_leveler.py' and set the GITHUB_REPO_URL variable.")
        return
        
    try:
        with urllib.request.urlopen(GITHUB_REPO_URL) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            if latest_version > VERSION:
                logging.warning(f"A new version ({latest_version}) is available. Please update your script by running 'git pull'.")
            else:
                logging.info("You are running the latest version.")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logging.error(f"Could not check for updates: The configured GitHub repository URL was not found (404). Please verify the URL in 'audio_leveler.py'.")
        else:
            logging.error(f"Could not check for updates: {e}")
    except Exception as e:
        logging.error(f"Could not check for updates: {e}")

def get_media_files(directory):
    """Recursively finds all supported media files in a directory."""
    files = []
    for p in Path(directory).rglob('*'):
        if p.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(p)
    return files

def get_stream_info(file_path):
    """Uses ffprobe to get media file stream information."""
    command = [
        FFPROBE_PATH,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        str(file_path)
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
    return json.loads(result.stdout)

def format_loudness_info(i, lra, tp, source):
    """Formats loudness information for logging."""
    return f"{source} Loudness:\n" \
           f"  Integrated Loudness (I): {i:.2f} LUFS\n" \
           f"  Loudness Range (LRA):    {lra:.2f} LU\n" \
           f"  True Peak (TP):          {tp:.2f} dBTP"

def process_file(file_path):
    """Processes a single media file for audio normalization."""
    file_path = Path(file_path)
    tmp_path = file_path.with_suffix(file_path.suffix + '.tmp')
    
    if tmp_path.exists():
        logging.warning(f"Orphaned temp file found: {tmp_path}. Deleting.")
        os.remove(tmp_path)

    try:
# --- Pass 1: Analyze Loudness for ALL audio tracks ---
        logging.info(f"Pass 1: Analyzing '{file_path.name}'")
        start_time = time.time()
        
        try:
            stream_info = get_stream_info(file_path)
            audio_streams = [s for s in stream_info['streams'] if s['codec_type'] == 'audio']
            if not audio_streams:
                logging.error(f"No audio streams found in {file_path.name}")
                return "failed", 0
        except Exception as e:
            logging.error(f"Could not get stream info for {file_path.name}: {e}")
            return "failed", 0

        measured_tracks = []
        skip_file = True

        for idx, stream in enumerate(audio_streams):
            stream_index = stream['index']
            logging.info(f"Analyzing audio track {idx} (stream index {stream_index})")
            
            ffmpeg_cmd_pass1 = [
                FFMPEG_PATH, '-hide_banner', '-i', str(file_path),
                '-vn', '-sn', '-dn', '-map', f'0:a:{idx}',
                '-af', f"loudnorm=I={LOUDNESS_TARGETS['I']}:LRA={LOUDNESS_TARGETS['LRA']}:tp={LOUDNESS_TARGETS['TP']}:print_format=json",
                '-f', 'null', '-'
            ]
            
            result_pass1 = subprocess.run(ffmpeg_cmd_pass1, capture_output=True, text=True, encoding='utf-8')
            
            if result_pass1.returncode != 0:
                logging.error(f"FFmpeg Pass 1 failed for track {idx} of {file_path.name}.")
                return "failed", 0

            stderr_output = result_pass1.stderr
            json_start_index = stderr_output.rfind('{')
            json_end_index = stderr_output.rfind('}')
            
            if json_start_index == -1 or json_end_index == -1:
                logging.error(f"Could not find JSON stats for track {idx} in {file_path.name}.")
                return "failed", 0

            try:
                measured = json.loads(stderr_output[json_start_index:json_end_index+1])
                measured_tracks.append(measured)
            except json.JSONDecodeError:
                return "failed", 0
            
            input_i = float(measured['input_i'])
            input_lra = float(measured['input_lra'])
            input_tp = float(measured['input_tp'])
            logging.info(format_loudness_info(input_i, input_lra, input_tp, f"TRACK {idx} BEFORE"))

            # If even ONE track needs normalization, we do not skip the file
            if not ((LOUDNESS_TARGETS['I'] - LOUDNESS_TOLERANCE) <= input_i <= (LOUDNESS_TARGETS['I'] + LOUDNESS_TOLERANCE) and input_lra <= LOUDNESS_TARGETS['LRA']):
                skip_file = False

        # --- Efficiency Gate ---
        if skip_file:
            time_saved = time.time() - start_time
            logging.info(f"SKIP: All audio tracks in '{file_path.name}' are already within targets. Time saved: {time_saved:.2f}s")
            return "skipped", time_saved

        # --- Pass 2: Apply Normalization to ALL tracks dynamically ---
        logging.info(f"Pass 2: Normalizing '{file_path.name}'")
        
        output_format = FORMAT_MAP.get(file_path.suffix.lower())
        if not output_format:
            logging.error(f"Unsupported file extension: {file_path.suffix}")
            return "failed", 0

        # Build dynamic arguments for video, subtitles, data, and audio tracks
        ffmpeg_cmd_pass2 = [
            FFMPEG_PATH, '-y', '-hide_banner', '-i', str(file_path),
            '-map', '0:v', '-c:v', 'copy'
        ]
        
        # Safely copy subtitles and data streams if they exist
        if any(s['codec_type'] == 'subtitle' for s in stream_info['streams']):
            ffmpeg_cmd_pass2.extend(['-map', '0:s', '-c:s', 'copy'])
        if any(s['codec_type'] == 'data' for s in stream_info['streams']):
            ffmpeg_cmd_pass2.extend(['-map', '0:d', '-c:d', 'copy'])

        # Construct specific mapping and filters for each individual audio stream
        filter_complex_parts = []
        for idx, stream in enumerate(audio_streams):
            m = measured_tracks[idx]
            codec = stream.get('codec_name', 'opus')
            
            # Map this specific track out
            ffmpeg_cmd_pass2.extend(['-map', f'[out_a{idx}]', f'-c:a:{idx}', codec])
            
            # Add explicit audio property definitions per track if available
            if stream.get('sample_fmt'):
                ffmpeg_cmd_pass2.extend([f'-sample_fmt:{idx}', stream['sample_fmt']])
            if stream.get('sample_rate'):
                ffmpeg_cmd_pass2.extend([f'-ar:{idx}', stream['sample_rate']])
                
            # Append complex filter segment for this track
            filter_complex_parts.append(
                f"[0:a:{idx}]loudnorm=I={LOUDNESS_TARGETS['I']}:LRA={LOUDNESS_TARGETS['LRA']}:tp={LOUDNESS_TARGETS['TP']}:"
                f"measured_I={m['input_i']}:measured_LRA={m['input_lra']}:measured_tp={m['input_tp']}:"
                f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}[out_a{idx}]"
            )

        ffmpeg_cmd_pass2.extend(['-filter_complex', ';'.join(filter_complex_parts)])
        ffmpeg_cmd_pass2.extend(['-strict', '-2', '-f', output_format, str(tmp_path)])
        
        result_pass2 = subprocess.run(ffmpeg_cmd_pass2, capture_output=True, text=True, encoding='utf-8')        
        if result_pass2.returncode != 0:
            logging.error(f"FFmpeg Pass 2 failed for {file_path.name}. Error:\n{result_pass2.stderr}")
            return "failed", 0
            
        # --- Verification ---
        original_duration = float(get_stream_info(file_path)['format']['duration'])
        new_duration = float(get_stream_info(tmp_path)['format']['duration'])

        if abs(original_duration - new_duration) > 1.0: # 100ms tolerance
            logging.error(f"VERIFICATION FAILED: Duration mismatch for '{file_path.name}'. Original: {original_duration}s, New: {new_duration}s")
            return "failed", 0
        
        # --- Atomic Swap ---
        logging.info(f"Verification successful. Replacing original file for '{file_path.name}'")
        os.replace(tmp_path, file_path)

        logging.info(format_loudness_info(LOUDNESS_TARGETS['I'], LOUDNESS_TARGETS['LRA'], LOUDNESS_TARGETS['TP'], "AFTER"))
        
        total_time = time.time() - start_time
        logging.info(f"SUCCESS: Processed '{file_path.name}' in {total_time:.2f}s")
        return "processed", total_time

    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {file_path.name}: {e}")
        return "failed", 0
    finally:
        # --- Cleanup ---
        if tmp_path.exists():
            os.remove(tmp_path)

def cleanup_directory(directory):
    """Scans for and removes orphaned .tmp or .normalized files."""
    logging.info(f"Scanning '{directory}' for orphaned files...")
    orphaned_files = list(Path(directory).rglob('*.tmp')) + list(Path(directory).rglob('*.normalized'))
    
    if not orphaned_files:
        logging.info("No orphaned files found.")
        return

    for f in orphaned_files:
        try:
            os.remove(f)
            logging.info(f"Removed orphaned file: {f}")
        except OSError as e:
            logging.error(f"Error removing orphaned file {f}: {e}")
            
def main():
    """Main execution function."""
    # Test Detection
    if os.environ.get('sonarr_eventtype') == 'Test' or os.environ.get('radarr_eventtype') == 'Test':
        logging.info("Diagnostic: Success")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Media Audio Leveler")
    parser.add_argument('--file', dest='single_file', type=str, help='Process a single media file.')
    parser.add_argument('--batch', dest='batch_dir', type=str, help='Run in batch mode on a directory.')
    parser.add_argument('--cleanup', action='store_true', help='Scan for and remove orphaned temporary files.')
    parser.add_argument('--no-update-check', action='store_true', help='Skip the GitHub update check.')
    parser.add_argument('--update', action='store_true', help='Check for updates and exit.')
    
    args = parser.parse_args()

    if args.update:
        check_for_updates()
        sys.exit(0)

    if not args.no_update_check:
        check_for_updates()
        
    file_to_process = None
    
    # --- Mode Detection ---
    if os.environ.get('sonarr_episodefile_path'):
        file_to_process = os.environ.get('sonarr_episodefile_path')
        logging.info(f"Sonarr integration detected (WIP). Processing file: {file_to_process}")
    elif os.environ.get('radarr_moviefile_path'):
        file_to_process = os.environ.get('radarr_moviefile_path')
        logging.info(f"Radarr integration detected (WIP). Processing file: {file_to_process}")
    elif args.single_file:
        file_to_process = args.single_file
        logging.info(f"Single file mode: processing '{file_to_process}'")
    elif args.batch_dir:
        logging.info(f"Batch mode activated for directory: {args.batch_dir}")
        if args.cleanup:
            cleanup_directory(args.batch_dir)
        
        files = get_media_files(args.batch_dir)
        logging.info(f"Found {len(files)} media files to process.")
        
        summary = {"processed": 0, "skipped": 0, "failed": 0, "time_saved": 0, "total_time": 0}
        
        for f in files:
            status, duration = process_file(f)
            summary[status] += 1
            if status == 'skipped':
                summary['time_saved'] += duration
            summary['total_time'] += duration
        
        logging.info("--- Batch Processing Summary ---")
        logging.info(f"Files Processed: {summary['processed']}")
        logging.info(f"Files Skipped: {summary['skipped']}")
        logging.info(f"Files Failed: {summary['failed']}")
        logging.info(f"Total Time Saved by Skipping: {summary['time_saved']:.2f}s")
        logging.info(f"Total Processing Time: {summary['total_time']:.2f}s")
        sys.exit(0) # Exit after batch processing
        
    elif args.cleanup:
         cleanup_directory(args.batch_dir or '.')
         sys.exit(0)
         
    else:
        logging.info("No media file path provided via environment variables, --file, or --batch flag. Exiting.")
        parser.print_help()
        sys.exit(1)

    if file_to_process:
        process_file(file_to_process)

if __name__ == "__main__":
    main()
