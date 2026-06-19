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
    echo [!] Python is not installed or not found on your system PATH.
    echo [i] I can automatically install Python 3 for you using Windows Package Manager (winget).
    echo.
    set /p install_choice="Would you like to install Python now? (Y/N): "
    if /i "%install_choice%"=="Y" (
        echo [i] Installing Python 3... Please accept any Windows permission prompts.
        winget install --id Python.Python.3 --silent --accept-source-agreements --accept-package-agreements
        if %errorlevel% equ 0 (
            echo.
            echo [OK] Python has been successfully installed!
            echo [i] Since this is a new installation, please close this window and
            echo     double-click run_debugger.bat again to start.
            echo.
            pause
            exit /b 0
        ) else (
            echo [ERR] Failed to install Python via winget.
            echo Please install Python manually from https://www.python.org/
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo [ERR] Python is required to run the debugger. Exiting.
        pause
        exit /b 1
    )
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
