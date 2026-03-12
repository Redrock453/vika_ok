#!/usr/bin/env python3
"""
🎀 Vika Agent - Файнтюнинг
Обучение модели на RTX 3050 (6GB VRAM)
"""

import os
import sys
from pathlib import Path

# Проверка CUDA
import torch
print(f"🔍 CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"🔍 GPU: {torch.cuda.get_device_name(0)}")
    print(f"🔍 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# Установка Unsloth
try:
    from unsloth import FastLanguageModel
except ImportError:
    print("📦 Installing Unsloth...")
    os.system("pip install unsloth")
    from unsloth import FastLanguageModel

# Конфигурация
MODEL_NAME = "unsloth/Llama-3.2-1B-Instruct"  # Легкая модель для 6GB VRAM
MAX_SEQ_LENGTH = 2048
OUTPUT_DIR = Path("vika-lora")
DATASET_FILE = Path("dataset.jsonl")

# Параметры LoRA
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

# Параметры обучения
BATCH_SIZE = 2
GRADIENT_ACCUMULATION = 4
EPOCHS = 3
LEARNING_RATE = 2e-4
LOGGING_STEPS = 10
SAVE_STEPS = 100

print("=" * 50)
print("🎀 Vika Agent - Файнтюнинг")
print("=" * 50)

# Загрузка модели
print("\n📥 Загрузка модели...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,  # Авто
    load_in_4bit=True,  # Для 6GB VRAM
)

# Настройка LoRA
print("⚙️ Настройка LoRA...")
model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    use_rslora=True,
    use_gradient_checkpointing="unsloth",
)

# Загрузка датасета
print(f"📂 Загрузка датасета: {DATASET_FILE}")

from unsloth.trainer import UnslothTrainingArguments, UnslothTrainer

trainer = UnslothTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=None,  # Загрузим ниже
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=4,
    packing=True,
)

# Запуск обучения
print("\n🚀 Запуск обучения...")
print(f"   Модель: {MODEL_NAME}")
print(f"   batch_size: {BATCH_SIZE}")
print(f"   gradient_accumulation: {GRADIENT_ACCUMULATION}")
print(f"   epochs: {EPOCHS}")
print(f"   lr: {LEARNING_RATE}")
print(f"   output: {OUTPUT_DIR}")

trainer.train()

# Сохранение
print(f"\n💾 Сохранение модели в {OUTPUT_DIR}...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# Экспорт в GGUF
print("\n📦 Экспорт в GGUF (Q4_K_M)...")
os.system(f"python -m unsloth.export_to_gguf {OUTPUT_DIR} --quantization Q4_K_M")

print("\n✅ Готово!")
print(f"   Модель сохранена в: {OUTPUT_DIR}")
print("   Создай Modelfile и запусти: ollama create vika-ft")
