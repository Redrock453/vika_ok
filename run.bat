@echo off
chcp 65001 >nul
title Vika - Personal AI Agent [Mobile]

echo ========================================
echo    Vika - Personal AI Agent [Mobile]
echo ========================================
echo.

:: Проверяем Python
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

:: Проверяем GROQ_API_KEY
echo [1/2] Checking Groq API Key...
if "%GROQ_API_KEY%"=="" (
    echo [!] GROQ_API_KEY не задан!
    echo Получи бесплатно: https://console.groq.com
    echo Затем: set GROQ_API_KEY=твой_ключ
    echo.
    pause
)

:: Запускаем агента
echo [2/2] Starting Vika Agent (Mobile)...
echo.
python agent_mobile.py

pause
