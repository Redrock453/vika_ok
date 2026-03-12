@echo off
chcp 65001 >nul
title Vika - Desktop

echo ========================================
echo    Vika - Personal AI Agent [Desktop]
echo ========================================
echo.

echo [1/3] Checking Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo [!] Ollama not running. Starting...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
)

echo [2/3] Checking model llama3.2:3b...
ollama list | findstr "llama3.2" >nul 2>&1
if errorlevel 1 (
    echo [!] Model llama3.2:3b not found. Pulling...
    ollama pull llama3.2:3b
)

echo [3/3] Starting Vika Agent (Native Tool Calling)...
echo.
python agent.py

pause
