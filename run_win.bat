@echo off

:: Wrapper script for audio_leveler.py for Sonarr/Radarr on Windows

:: Help Menu
if "%1"=="" (goto help)
if "%1"=="--help" (goto help)
if "%1"=="-h" (goto help)
if "%1"=="!h" (goto help)
if "%1"=="?" (goto help)


:: Debugging - Log environment variables to a temp file
echo Sonarr Event: %sonarr_eventtype% >> C:\Users\Andrew\.gemini\tmp\ac8bc5a5b84159c50864181aa1cb926baae455557a80c01cfde6950793a1f6b2\wrapper.log
echo Radarr Event: %radarr_eventtype% >> C:\Users\Andrew\.gemini\tmp\ac8bc5a5b84159c50864181aa1cb926baae455557a80c01cfde6950793a1f6b2\wrapper.log

:: Handle the Test event from Sonarr/Radarr
if "%sonarr_eventtype%"=="Test" (
	set SCRIPT_DIR=%~dp0
	set PYTHON_CMD=python
	if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
		set PYTHON_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe
	)
	"%PYTHON_CMD%" "%SCRIPT_DIR%audio_leveler.py" --arr-test "Sonarr"
    exit /b 0
)

if "%radarr_eventtype%"=="Test" (
	set SCRIPT_DIR=%~dp0
	set PYTHON_CMD=python
	if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
		set PYTHON_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe
	)
	"%PYTHON_CMD%" "%SCRIPT_DIR%audio_leveler.py" --arr-test "Radarr"
    exit /b 0
)

:: Get the directory of this script
set SCRIPT_DIR=%~dp0
set PYTHON_CMD=python

:: Check if a venv exists and set the python command accordingly
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set PYTHON_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe
)

:: Execute the python script, passing all arguments.
"%PYTHON_CMD%" "%SCRIPT_DIR%audio_leveler.py" %*
goto:eof

:help
echo.
echo Media Audio Leveler
echo.
echo   A professional-grade Python automation suite for audio normalization.
echo.
echo Usage:
echo   run_win.bat [options]
echo.
echo Options:
echo.
echo   --file ^<file^>             Process a single media file.
echo   --batch ^<directory^>       Run in batch mode on a directory.
echo   --cleanup                  Scan for and remove orphaned temporary files.
echo   --no-update-check          Skip the GitHub update check.
echo   --update                   Check for updates and exit.
echo   --help, -h, /?, ?          Show this help message.
echo.
echo Integration:
echo   The script auto-detects Sonarr and Radarr environments.
echo.
exit /b 0
