@echo off
REM Build runner — runs in FOREGROUND (for debugging)
REM Shows output in console in real-time

cd /d "%~dp0..\.."

echo BuzzReach Build Runner (Foreground, console output)
echo.

python scripts\build-runner\run.py --model claude-opus-4-6 %*
