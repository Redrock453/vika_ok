# Vika_Ok 🇺🇦

AI-асистент Баса — Telegram бот з RAG, голосовими повідомленнями та fallback-ланцюжком LLM.

## Архітектура

```
src/
  core/
    config.py      ← Конфігурація (.env)
    agent.py       ← Головний агент
    llm.py         ← LLM провайдери з retry + fallback
    history.py     ← Історія чатів (JSON)
  handlers/
    telegram.py    ← Telegram handlers
  services/
    rag.py         ← Qdrant векторний пошук
    search.py      ← DuckDuckGo пошук
    tasks.py       ← Нагадування
run.py             ← Entrypoint
```

## LLM Fallback ланцюжок

DO Agent → Groq → Gemini (3 спроби з exponential backoff кожного)

## Швидкий старт

### Docker (рекомендовано)

```bash
# 1. Клонувати
git clone https://github.com/Redrock453/vika_ok.git
cd vika_ok
git checkout dev

# 2. Створити .env
cp .env.example .env
# Заповнити ключі

# 3. Запустити
docker compose up -d
```

### Без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

## Змінні середовища

| Змінна | Опис | Обов'язкова |
|--------|------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | ✅ |
| `ALLOWED_IDS` | Telegram ID через кому | ✅ |
| `DO_AI_API_KEY` | DO Agent API ключ | Ні |
| `DO_AI_BASE_URL` | DO Agent URL | Ні |
| `GROQ_API_KEY` | Groq API ключ + Whisper STT | Рекомендовано |
| `GEMINI_API_KEY` | Google Gemini API ключ | Рекомендовано |
| `QDRANT_HOST` | Qdrant хост (default: `vika_qdrant`) | Ні |
| `QDRANT_PORT` | Qdrant порт (default: `6333`) | Ні |

## Можливості

- 💬 Чат з контекстом (історія 30 повідомлень)
- 🎤 Голосові повідомлення → транскрипція (Whisper) → відповідь
- 🔍 RAG пошук по базі знань (Qdrant + sentence-transformers)
- 🌐 Web пошук (DuckDuckGo)
- 📋 Нагадування / задачі
- 🔄 Автоматичний fallback між LLM провайдерами

## Версія

**v13.0-PRODUCTION** — модульна архітектура, Docker, retry/fallback

## Ліцензія

Приватний проєкт Баса ❤️
