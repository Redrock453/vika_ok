@echo off
chcp 65001 >nul
title Vika - Personal AI Agent

echo ========================================
echo    Vika - Personal AI Agent [Desktop]
echo ========================================
echo.

:: Проверяем Ollama
echo [1/3] Checking Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo [!] Ollama не запущен. Запускаю...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
)

:: Проверяем модель vika
echo [2/3] Checking model...
ollama list | findstr "vika" >nul 2>&1
if errorlevel 1 (
    echo [!] Модель vika не найдена. Создаю из Modelfile...
    ollama create vika -f Modelfile
)

:: Запускаем агента
echo [3/3] Starting Vika Agent...
echo.
python agent_desktop.py

pause
