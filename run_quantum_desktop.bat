@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo   QUANTUM - Autonomous Trading & Governance Desktop Launcher (Phase 6B)
echo   Avalonia UI MVVM (.NET 9) + FastAPI WebSocket Telemetry Server
echo ===============================================================================

REM Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)

REM Check if dotnet is available
where dotnet >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] .NET SDK not found in PATH.
    pause
    exit /b 1
)

REM Execute master python orchestrator
python "%~dp0run_quantum_desktop.py" %*

if %ERRORLEVEL% neq 0 (
    echo [LAUNCHER] Exited with code %ERRORLEVEL%.
)
