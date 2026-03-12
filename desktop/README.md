# 🎀 Vika Agent — Desktop

Для ноутбука / VPS / мощного ПК.

## Быстрый старт

```
1. Дважды кликни run.bat
2. Готово — Виктория ждёт тебя ❤️
```

## Требования

- Python 3.10+
- Ollama
- Модель vika

## Установка

```bash
pip install -r requirements.txt
ollama create vika -f Modelfile
```

## Запуск

```bash
run.bat
```

или

```bash
python agent.py
```

## Модель

По умолчанию: `vika` (создаётся из Modelfile)

Изменить: `set VIKA_MODEL=модель`

## База знаний

Файлы RAG хранятся локально в папке `knowledge/`.

Добавить: `добавь директорию: ПУТЬ`

## Версии

- **Desktop**: https://github.com/Redrock453/vika_ok (Ollama)
- **Mobile**: https://github.com/Redrock453/vika-mobile (Groq API)
