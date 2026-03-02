#!/usr/bin/env python3
# The shebang above is a portable option.
# The user-requested shebang was: #!/home/northmainave/scripts/VolNorm/.venv/bin/python

import sys
import subprocess
import os

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "diagnostics.log")

# --- Functions ---
def log_message(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"PYTHON: {message}\n")

# --- Start Diagnostics ---
try:
    log_message(f"Python Version: {sys.version}")
    log_message(f"Python Executable: {sys.executable}")

    log_message("Testing write permissions...")
    with open(LOG_FILE, "a") as f:
        f.write("PYTHON: Python Write Test: Success\n")
    log_message("SUCCESS: Write test successful.")

    log_message("Checking ffmpeg version...")
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
    log_message("SUCCESS: ffmpeg -version command succeeded.")
    log_message(f"FFmpeg output:\n{result.stdout.splitlines()[0]}")

except FileNotFoundError:
    log_message("ERROR: 'ffmpeg' command not found.")
    sys.exit(1)
except subprocess.CalledProcessError as e:
    log_message(f"ERROR: 'ffmpeg -version' command failed with exit code {e.returncode}.")
    log_message(f"FFmpeg output:\n{e.stderr}")
    sys.exit(1)
except Exception as e:
    log_message(f"An unexpected error occurred: {e}")
    sys.exit(1)
