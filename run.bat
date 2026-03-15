@echo off
chcp 65001 >nul
set PYTHONPATH=%CD%
start /b ollama serve >nul 2>&1
.\venv\Scripts\python.exe agent.py
pause
