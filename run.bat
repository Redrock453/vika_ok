@echo off
chcp 65001 >nul
title Vika Agent

echo ========================================
echo    Vika - Personal AI Agent
echo ========================================
echo.

cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ollama not found!
    echo Download: https://ollama.com
    pause
    exit /b 1
)

echo [1/3] Checking Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | findstr /i "ollama.exe" >nul
if %errorlevel% neq 0 (
    echo [Ollama not running, starting...]
    start /b ollama serve >nul 2>&1
    timeout /t 3 /nobreak >nul
)

echo [2/3] Starting Vika Agent...
echo.

python agent.py

echo.
echo Vika closed. Press any key to exit...
pause >nul
