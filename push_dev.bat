@echo off
cd /d "%~dp0" || exit /b 1
echo [DEV] Pushing to dev branch...
git add .
git commit -m "dev: sync"
git push origin dev
echo [OK]
