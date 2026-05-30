@echo off
REM Setup script for Windows: install dependencies and configure environment

cd /d "%~dp0..\.."

echo BuzzReach Build Runner — Windows Setup
echo.

REM Check Python
echo Checking Python 3.11+...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed. Download from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip not available.
    pause
    exit /b 1
)

REM Install Python dependencies
echo.
echo Installing Python dependencies...
pip install pyyaml

REM Check Claude CLI
echo.
echo Checking Claude CLI...
claude --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Claude CLI not installed.
    echo Install with: npm install -g @anthropic-ai/claude-code
    echo Then run setup-windows.bat again.
    pause
    exit /b 1
)

REM Check Git
echo.
echo Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Git not installed.
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Set up environment
echo.
echo Creating directories...
mkdir state >nul 2>&1
mkdir logs >nul 2>&1
mkdir data >nul 2>&1

REM Test health
echo.
echo Running health checks...
python scripts\build-runner\run.py --health

echo.
echo ✓ Setup complete!
echo.
echo Next steps:
echo   1. Review product.yaml (tech stack, modules)
echo   2. Check atoms/ directory (30 atom specs)
echo   3. Run: build.bat
echo.
pause
