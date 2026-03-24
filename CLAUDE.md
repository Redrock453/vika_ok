# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Vika_Ok** — персональный AI-агент-помощник (v12.7-MULTIMODAL) с мультипровайдерным роутингом LLM, RAG-памятью на Qdrant, поддержкой мультимодального ввода (голос/аудио) и веб-поиска. Создан как "жена и инженер" для личного использования с конкретной системой промптов и личностью.

## Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run main agent (CLI mode)
python agent.py

# Run Telegram bot
python telegram_bot.py

# Run Signal bot
python signal_bot_vika.py

# Run tests (Phase 1-2 functional tests)
python test_phase1_2.py

# Quick tests only
python test_phase1_2.py --quick

# Docker deployment
docker compose up -d --build

# Restart services
docker restart vika_bot
docker restart vika_qdrant

# Check bot status
python -c "from agent import VikaOk; vika = VikaOk(); print(vika.ask('статус'))"
```

### Cleanup

```bash
# Clear agent history
python -c "from agent import VikaOk; vika = VikaOk(); print('History cleared')"  # (via /clear command)

# Check logs
tail -f /app/bot.log  # For Telegram bot
```

## Architecture

### Core Components

```
Telegram Bot (telegram_bot.py) → VikaOk (agent.py) → LLM Routing
                                    ↓
                            Qdrant RAG + History
                                    ↓
                          Groq / Gemini / OpenRouter
```

**agent.py** - Main agent class (`VikaOk`) with:
- Multi-provider LLM routing (Groq → Gemini → OpenRouter fallback)
- RAG integration via Qdrant (optional, uses Sentence Transformers)
- Multimodal audio input (Whisper + Gemini Multimodal fallback)
- Web search via DuckDuckGo Lite
- Conversation history management (max 30 messages)

**telegram_bot.py** - Telegram interface (aiogram 3.0):
- Commands: `/start`, `/help`, `/status`, `/plan`
- Voice/audio transcription (Groq Whisper + Gemini fallback)
- Research tasks (async background processing)
- Proactive task notifications
- Allowed user filtering via `ALLOWED_IDS` env var

**qdrant_manager.py** - Vector database manager:
- Collection: `vika_knowledge`
- Embedding model: `distiluse-base-multilingual-cased-v2` (512-dim)
- CRUD operations for documents and vector search

**signal_bot_vika.py** - Alternative Signal bot:
- Uses `signal-cli` binary for encrypted messaging
- Audit logging with Fernet encryption
- Bridge between Signal and Vika agent

### LLM Routing Chain

1. **Primary**: Gemini 1.5 Pro (`gemini-1.5-pro`)
2. **Fallback 1**: Groq Llama-3.3-70b-versatile
3. **Fallback 2**: OpenRouter (via OpenAI client)
4. **Offline**: Ollama (if available locally)

Complex/structured queries → Gemini, simple queries → Groq, no internet → Ollama

### Memory & RAG

- **Conversation history**: In-memory list in `VikaOk` (max 30 messages)
- **Knowledge base**: Qdrant vector database (optional)
- **Document source**: `docs/` directory (soft link to `knowledge`)
- **Embeddings**: Sentence Transformers (multilingual)

### Data Flow

**Voice input**:
```
Telegram voice → Telegram bot → ffmpeg conversion → Groq Whisper
                                                      ↓
                                               (if fails) → Gemini Multimodal
```

**Research tasks**:
```
Telegram message (research keywords) → run_research() → web search
→ Gemini analysis → save to tasks.json → proactive notification
```

## Configuration

**Environment variables** (`.env`):
- `GEMINI_API_KEY` — Primary LLM provider
- `GROQ_API_KEY` — Fallback provider
- `OPENROUTER_API_KEY` — Additional fallback
- `QDRANT_URL` — Vector DB endpoint (default: localhost:6333)
- `TELEGRAM_BOT_TOKEN` — Telegram bot authentication
- `ALLOWED_IDS` — Comma-separated allowed user IDs

## Testing

**test_phase1_2.py** - Comprehensive functional test suite:
- Import validation for all components
- Document parsing (PDF/DOCX/OCR)
- OSINT query handling
- API integrations
- RAG pipeline
- Tests can be run with `--quick` flag for critical tests only

## Known Limitations

- Voice transcription currently uses Whisper (Groq) with Gemini fallback
- No persistent conversation history across restarts (memory-only)
- Research tasks use DuckDuckGo Lite (limited functionality)
- Qdrant integration is optional (falls back gracefully)
- System prompt enforces specific persona and language patterns
