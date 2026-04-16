@echo off
REM
REM Setup script for yt2mp3 utility
REM Supports: Windows (PowerShell/CMD)
REM
setlocal enabledelayedexpansion

REM Colors (ANSI escape codes for Windows 10+)
set "BLUE=[94m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

echo %BLUE%[INFO]%NC% Starting yt2mp3 setup for Windows...
echo.

REM Check Python
echo %BLUE%[INFO]%NC% Checking Python 3...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%[✗]%NC% Python is not installed or not in PATH
    echo %BLUE%[INFO]%NC% Please install Python 3.8 or higher from: https://www.python.org/downloads/
    echo %BLUE%[INFO]%NC% Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%[✓]%NC% Python found: %PYTHON_VERSION%
echo.

REM Check pip
echo %BLUE%[INFO]%NC% Checking pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%[✗]%NC% pip is not available
    echo %BLUE%[INFO]%NC% Please reinstall Python with pip included
    pause
    exit /b 1
)
echo %GREEN%[✓]%NC% pip found
echo.

REM Check yt-dlp
echo %BLUE%[INFO]%NC% Checking yt-dlp...
yt-dlp --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%[!]%NC% yt-dlp not found, installing...
    pip install --user yt-dlp
    if %errorlevel% neq 0 (
        echo %RED%[✗]%NC% Failed to install yt-dlp
        pause
        exit /b 1
    )
    echo %GREEN%[✓]%NC% yt-dlp installed successfully
) else (
    for /f "tokens=*" %%i in ('yt-dlp --version 2^>^&1') do set YT_DLP_VERSION=%%i
    echo %GREEN%[✓]%NC% yt-dlp found: %YT_DLP_VERSION%
)
echo.

REM Check ffmpeg
echo %BLUE%[INFO]%NC% Checking ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%[!]%NC% ffmpeg not found
    echo %BLUE%[INFO]%NC% Installing ffmpeg via winget...
    
    winget --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo %RED%[✗]%NC% winget is not available
        echo %BLUE%[INFO]%NC% Please install ffmpeg manually:
        echo   1. Download from: https://www.gyan.dev/ffmpeg/builds/
        echo   2. Extract to C:\ffmpeg
        echo   3. Add C:\ffmpeg\bin to PATH
        echo.
        echo %BLUE%[INFO]%NC% Or install via chocolatey (if available):
        echo   choco install ffmpeg
        pause
        exit /b 1
    )
    
    winget install --id Gyan.FFmpeg -e --silent
    if %errorlevel% neq 0 (
        echo %YELLOW%[!]%NC% winget installation failed, trying alternative...
        echo %BLUE%[INFO]%NC% You may need to install ffmpeg manually (see above)
    ) else (
        echo %GREEN%[✓]%NC% ffmpeg installed via winget
        echo %BLUE%[INFO]%NC% You may need to restart your terminal for ffmpeg to be available
    )
) else (
    for /f "tokens=1-3" %%i in ('ffmpeg -version 2^>^&1 ^| findstr /i "ffmpeg version"') do set FFMPEG_VERSION=%%i %%j %%k
    echo %GREEN%[✓]%NC% ffmpeg found: %FFMPEG_VERSION%
)
echo.

REM Create cache directory
echo %BLUE%[INFO]%NC% Creating cache directory...
set "SCRIPT_DIR=%~dp0"
set "CACHE_DIR=%SCRIPT_DIR%yt2mp3\.cache"
if not exist "%CACHE_DIR%" (
    mkdir "%CACHE_DIR%"
    echo %GREEN%[✓]%NC% Cache directory created: %CACHE_DIR%
) else (
    echo %GREEN%[✓]%NC% Cache directory already exists
)
echo.

REM Verify installations
echo %BLUE%[INFO]%NC% Verifying installations...
set "ERRORS=0"

yt-dlp --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%[✗]%NC% yt-dlp verification failed
    set /a ERRORS+=1
)

ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%[✗]%NC% ffmpeg verification failed
    set /a ERRORS+=1
)

if %ERRORS% gtr 0 (
    echo.
    echo %RED%[✗]%NC% Setup completed with %ERRORS% error(s)
    echo %BLUE%[INFO]%NC% Please install the missing dependencies manually
    pause
    exit /b 1
)

REM Success message
echo.
echo %GREEN%[✓]%NC% Setup completed successfully!
echo.
echo You can now use yt2mp3:
echo   python yt2mp3\yt_to_mp3.py "^<youtube-url^>"
echo   python yt2mp3\yt_to_mp3.py "^<youtube-url^>" 1m30s 2m45s  REM Trimmed clip
echo.
echo For help:
echo   python yt2mp3\yt_to_mp3.py --help
echo.
pause
