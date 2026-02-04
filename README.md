# VolNorm

A professional-grade Python automation suite for audio normalization, designed for seamless integration with Sonarr and Radarr. This tool standardizes the audio loudness of your media library to EBU R128 compliance, ensuring a consistent listening experience.

## Technical Standards

This script uses FFmpeg's `loudnorm` filter to perform a two-pass normalization. The target values are:

- **Integrated Loudness (I):** -24 LUFS
- **Loudness Range (LRA):** 13 LU
- **True Peak (TP):** -2.0 dBTP

These values provide a balanced and dynamic audio experience suitable for a home theater environment, preventing dialogue from being too quiet or explosions from being too loud.

## Features

- **Two-Pass Normalization:** Ensures accurate loudness targeting.
- **Efficiency Gate:** Skips normalization if a file is already within ±0.5 LU of the target, saving significant processing time.
- **Cross-Platform:** Wrapper scripts for both Windows and Linux.
- **Stream Preservation:** Video, subtitle, and all other streams are copied without re-encoding.
- **Atomic Operations:** Uses a temporary file and an atomic `os.replace()` to prevent data corruption.
- **'Arr Integration:** Automatically detects and processes files when triggered by Sonarr or Radarr.
- **Batch Processing:** A `--batch` mode to scan and process your entire library.
- **Safety & Cleanup:** Includes a `try...finally` block and a `--cleanup` flag to manage temporary files.
- **Update Checker:** Notifies you when a new version is available on GitHub.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/theovit/VolNorm.git
    cd VolNorm
    ```

2.  **Install FFmpeg:**
    This script requires `ffmpeg` and `ffprobe` to be installed and available in your system's PATH.
    -   **Windows:** Download the latest binaries from [FFmpeg's website](https://ffmpeg.org/download.html) and add the `bin` folder to your system's PATH.
    -   **Linux (Debian/Ubuntu):**
        ```bash
        sudo apt update && sudo apt install ffmpeg
        ```

3.  **Set up a Python virtual environment:**
    ```bash
    # For Windows
    python -m venv .venv
    .venv\Scripts\activate

    # For Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

4.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Use the wrapper scripts to run the audio leveler.

-   **Windows:** `run_win.bat`
-   **Linux:** `run_linux.sh`

### Sonarr & Radarr Setup (Custom Script)

1.  Navigate to `Settings > Connect > Add Notification`.
2.  Select `Custom Script`.
3.  Configure the script settings:
    -   **On Grab:** Disabled
    -   **On Import:** Enabled
    -   **On Upgrade:** Enabled
    -   **On Rename:** Disabled
    -   **Path:** Enter the absolute path to the `run_win.bat` or `run_linux.sh` script.

The script will automatically use the environment variables provided by Sonarr/Radarr (`sonarr_episodefile_path` or `radarr_moviefile_path`) to find and process the media file.

### Command-Line Flags (CLI)

The wrapper scripts accept all the arguments of `audio_leveler.py`.

| Flag                  | Description                                                                                               |
| --------------------- | --------------------------------------------------------------------------------------------------------- |
| `--file [FILE]`       | Process a single media file.                                                                              |
| `--batch [DIRECTORY]` | Recursively scans the specified directory for media files and processes them.                             |
| `--cleanup`           | Used with `--batch`, this scans for and removes any orphaned `.tmp` or `.normalized` files from prior runs. |
| `--no-update-check`   | Skips the automatic check for new versions on GitHub.                                                     |
| `--update`            | Checks for updates and exits.                                                                             |
| `--help`              | Shows the help menu.                                                                                      |

**Example: Batch Processing an Entire Library**

```bash
# On Windows
run_win.bat --batch "D:\path\to\your\media"

# On Linux
./run_linux.sh --batch /path/to/your/media
```

## Logging

All operations are logged to both the console and a `leveler.log` file in the script's directory. The log includes summaries of files processed, skipped, and time saved.
