@echo off
chcp 65001 >nul
title Vika - Finetuning Setup

echo ========================================
echo    Vika Agent - Finetuning Setup
echo ========================================
echo.

cd /d "%~dp0"

:: Проверка Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

:: Проверка CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PyTorch not installed!
    echo Run: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    pause
    exit /b 1
)

echo [1/5] Checking CUDA...
python -c "import torch; assert torch.cuda.is_available(), 'No CUDA'; print(f'GPU: {torch.cuda.get_device_name(0)}')"
if %errorlevel% neq 0 (
    echo ERROR: CUDA not available!
    pause
    exit /b 1
)

echo [2/5] Installing dependencies...
pip install unsloth --quiet
pip install transformers accelerate peft --quiet

echo [3/5] Checking dataset...
if not exist dataset.jsonl (
    echo ERROR: dataset.jsonl not found!
    pause
    exit /b 1
)
echo    Dataset: OK

echo [4/5] Checking VRAM...
python -c "import torch; vram = torch.cuda.get_device_properties(0).total_memory / 1024**3; print(f'VRAM: {vram:.1f} GB'); assert vram >= 4, 'Not enough VRAM'"
if %errorlevel% neq 0 (
    echo WARNING: Less than 4GB VRAM. Using lighter model.
)

echo [5/5] Starting training...
echo.
echo ========================================
echo    TRAINING STARTED
echo    Estimated time: 30-60 minutes
echo    Press Ctrl+C to stop
echo ========================================
echo.

python train.py

echo.
echo ========================================
echo    TRAINING COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. ollama create vika-ft -f Modelfile.ft
echo 2. ollama run vika-ft
echo.

pause
