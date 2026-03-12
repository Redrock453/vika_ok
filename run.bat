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
    echo WARNING: Ollama not found! Make sure it's installed.
    echo Download: https://ollama.com
    echo.
)

echo Starting Vika Agent...
echo.

python my_engine_agent.py

pause
