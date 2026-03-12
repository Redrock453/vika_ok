# 🎀 Vika Agent - Файнтюнинг

Обучение модели для персонажа Виктории.

## Требования

- NVIDIA GPU с CUDA (RTX 3050+)
- Python 3.10+
- 6GB+ VRAM (рекомендуется)

## Быстрый старт

```bash
# 1. Запусти установку
setup.bat

# 2. Дождись обучения (~30-60 минут)

# 3. Проверь модель
ollama create vika-ft -f Modelfile.ft
ollama run vika-ft
```

## Ручная установка

```bash
# Установка зависимостей
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install unsloth transformers accelerate peft

# Запуск обучения
python train.py
```

## Параметры

| Параметр | Значение |
|----------|---------|
| Модель | unsloth/Llama-3.2-1B-Instruct |
| LoRA r | 16 |
| Batch size | 2 |
| Gradient accumulation | 4 |
| Epochs | 3 |
| Learning rate | 2e-4 |
| Max seq length | 2048 |

## Датасет

50+ пар в формате instruction/output:
- Приветствия (10)
- Работа с файлами (10)
- Веб-поиск (10)
- GitHub (5)
- Выполнение кода (5)
- RAG (5)
- Общие вопросы (5)

## После обучения

```bash
# Создать модель в Ollama
ollama create vika-ft -f Modelfile.ft

# Запустить
ollama run vika-ft

# В agent.py замени:
MODEL_NAME = "vika-ft"
```

## Структура

```
finetuning/
├── dataset.jsonl     # Датасет
├── train.py          # Скрипт обучения
├── setup.bat        # Установка и запуск
├── Modelfile.ft     # Modelfile для Ollama
└── README.md        # Этот файл
```

## Troubleshooting

**Недостаточно VRAM:**
- Уменьши batch_size до 1
- Используй load_in_4bit=True

**CUDA не найдена:**
- Переустанови torch с CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu121`

**Ollama не видит модель:**
- Проверь путь в Modelfile.ft
- Запусти из папки с GGUF файлом
