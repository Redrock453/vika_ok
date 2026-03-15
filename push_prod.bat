@echo off
cd /d "%~dp0" || exit /b 1
git add -A
git commit -m "🚀 auto-push prod"
git push origin dev
git checkout main
git merge dev --no-edit
git push origin main
git checkout dev
