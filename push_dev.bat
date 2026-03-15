@echo off
cd /d "%~dp0" || exit /b 1
git add -A
git commit -m "🚀 auto-push dev"
git push origin dev
