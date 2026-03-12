# TODO - Vika Agent

## Приоритет 1: Native Tool Calling
- [ ] Перейти на модель с нативным tool_calls (llama3.2:3b, gemma2:9b)
- [ ] Парсить tool_calls из Ollama API
- [ ] Интегрировать текущие инструменты (code_execution, web_search, browse_page)
- [ ] Тестирование

## Приоритет 2: Векторный RAG
- [ ] Добавить sentence-transformers или ollama embeddings
- [ ] Создать векторную базу знаний
- [ ] Семантический поиск вместо простого text matching
- [ ] Интеграция с agent.py

## Приоритет 3: Улучшения
- [ ] Проверка готовности Ollama в run.bat
- [ ] Логирование
- [ ] Поддержка нескольких моделей через .env
- [ ] README с quick start

---

## Notes

### Native Tool Calling
Модели с tool_calls:
- llama3.2:3b (требует 16GB RAM)
- gemma2:9b
- qwen2.5-coder:7b

### RAG
Варианты:
- ollama embeddings + chromadb
- sentence-transformers + qdrant
- Простой: ollama embed

---

Обновлено: 12.03.2026
