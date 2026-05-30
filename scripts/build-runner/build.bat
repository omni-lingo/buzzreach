@echo off
REM Build runner for BuzzReach — runs in background on Windows
REM Usage: build.bat [options]
REM   build.bat                    - Build all atoms, stop on error
REM   build.bat --max-atoms 5      - Build 5 atoms then stop
REM   build.bat --dry-run          - Show wave plan
REM   build.bat --status           - Show build progress
REM   build.bat --health           - Run health checks

setlocal enabledelayedexpansion

cd /d "%~dp0..\.."

echo BuzzReach Build Runner (Windows Background)
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ and add to PATH.
    pause
    exit /b 1
)

REM Check Claude CLI
claude --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Claude CLI not found. Run: npm install -g @anthropic-ai/claude-code
    pause
    exit /b 1
)

REM Run build runner
echo Starting build runner...
echo Log: logs\build-runner.log
echo.

REM Run in background (no console window)
if "%1"=="" (
    REM Default: full build in background
    start "" /b pythonw.exe scripts\build-runner\run.py --model claude-opus-4-6
    echo Build started in background. Monitor progress with:
    echo   tail -f logs\build-runner.log  (or: Get-Content logs\build-runner.log -Wait)
) else (
    REM Specific command (shown in console for --status, --dry-run, etc.)
    python scripts\build-runner\run.py %*
)
