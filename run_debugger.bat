@echo off
title Antigravity Pulse Debugger
cls

echo ============================================================
echo               Antigravity Pulse Debugger
echo ============================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system PATH.
    echo Please install Python 3.8+ and try again.
    echo.
    pause
    exit /b 1
)

:: Run script
python -m src.main

if %errorlevel% neq 0 (
    echo.
    echo [WARNING] The debugger exited with an error code.
)
echo.
echo Process complete. Press any key to close.
pause >nul
