@echo off
cd /d "%~dp0" || exit /b 1
echo [PROD] Pushing to main branch...
git add .
git commit -m "prod: sync"
git push origin main
echo [OK]
