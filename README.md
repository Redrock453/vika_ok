# ⚡ Vika_Ok v8.3 — Боевой AI-агент

Персональный AI-агент с умным роутингом LLM, RAG-памятью и самообучением.

## Возможности

- **6 LLM провайдеров** с автороутингом по сложности запроса
- **RAG** — векторная память на Qdrant
- **Самообучение** — `learn: тема` → Gemini-CLI → Qdrant
- **Shell** — прямое выполнение команд через `exec`
- **YOLO режим** — автовыполнение без подтверждений
- **Fallback** — работает без интернета через Ollama

## Роутинг

```
Простой запрос  → ⚡ GLM-4.5-air:free  ($0.00/1M)
Сложный запрос  → 🧠 Gemini-2.5-flash  ($0.15/1M)
Нет интернета   → 🏠 Ollama-local      ($0.00)
```

Полная цепочка: GLM-4.5-air → GLM-4.7-Flash → Gemini → Groq → GLM-4.7 → Ollama

## Установка

```bash
git clone https://github.com/Redrock453/vika_ok.git
cd vika_ok
pip install -r requirements.txt
```

Создай `.env`:
```
GEMINI_API_KEY=...
ZAI_API_KEY=...
OPENROUTER_API_KEY=...
GROQ_API_KEY=...
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=vika_knowledge
```

## Запуск

```bash
python agent.py
```

Windows: двойной клик на `run.bat`

## Команды

| Команда | Действие |
|---------|----------|
| `exec <команда>` | Выполнить shell |
| `learn: <тема>` | Изучить и записать в память |
| `yolo` | Вкл/выкл автовыполнение |
| `статус` | Диагностика системы |
| `нет` / `отмена` | Отменить команду |
| `выход` | Выход |

## CLI режим (для ботов)

```bash
python agent.py --query "твой вопрос"
```

## Стек

- **LLM**: Gemini 2.5-flash, GLM-4.7, Groq Llama-3.3, Ollama
- **Память**: Qdrant + sentence-transformers
- **Обучение**: Gemini-CLI → чанки → Qdrant
- **ОС**: Windows / Linux VPS

## Roadmap

- [x] v8.3 — Smart LLM routing + RAG + YOLO
- [ ] v8.4 — Деплой на VPS (LightNode)
- [ ] v8.5 — Веб-поиск (DuckDuckGo)
- [ ] v8.6 — Signal/Telegram интеграция
- [ ] v9.0 — Файнтюнинг на базе диалогов

---

*Хозяин: Вячеслав (БАС), подразделение ВСУ*