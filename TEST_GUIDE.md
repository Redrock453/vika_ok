# 🧪 PHASE 1-2 FUNCTIONAL TESTING GUIDE

## Як запустити тести функціональності

После того як закончиться установка зависимостей, запусти тесты:

---

## 📋 QUICK START

### Шаг 1: Убедись что установка закончилась
```bash
# Подожди пока завершится pip install в терминале
# Ты должен увидеть "Successfully installed..."
```

### Шаг 2: Запусти тесты
```bash
# Перейди в папку с проектом
cd C:\Users\admin\vika_ok

# Запусти тесты
python test_phase1_2.py

# или быстрые тесты (только критичные)
python test_phase1_2.py --quick
```

---

## 🎯 ЧТО БУДУТ ПРОВЕРЯТЬ ТЕСТЫ

### ✓ Imports (Импорты)
- FastAPI
- PDF/DOCX парсеры
- Gemini API
- Qdrant
- LangChain
- Ollama

### ✓ Document AI Pipeline
- Text chunking (разбиение текста)
- Embedding generation (создание векторов)
- Knowledge base directory (папка документов)

### ✓ Gemini API
- API ключ сконфигурирован
- Соединение с API работает
- Генерация текста работает

### ✓ Ollama Fallback
- Ollama сервис доступен
- Локальная модель может генерировать текст

### ✓ OSINT
- URL fetching (загрузка страниц)
- HTML parsing (парсинг HTML)

### ✓ RAG Pipeline
- Chunking документов
- Embedding chunks
- Query embedding
- Retrieval (поиск релевантных документов)

### ✓ FastAPI
- Health endpoint
- Document upload endpoint
- RAG query endpoint
- OSINT search endpoint

### ✓ Integration
- Все компоненты работают вместе
- Environment variables сконфигурены

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

Если всё установилось правильно, ты должен увидеть:

```
🧪 PHASE 1-2 FUNCTIONAL TEST SUITE
════════════════════════════════════════

✅ 1. TESTING IMPORTS
✓ FastAPI import [PASS]
✓ PyPDF2 import [PASS]
✓ python-docx import [PASS]
✓ Google Generative AI (Gemini) import [PASS]
... и т.д.

✅ 2. TESTING GEMINI 2.5 FLASH API
✓ Gemini API Key [PASS] — Configured
✓ Gemini API call [PASS] — Response: Vika is ready...

✅ 3. TESTING DOCUMENT AI PIPELINE
✓ Text chunking [PASS] — 15 chunks created
✓ Embedding generation [PASS] — Shape: (384,)
... и т.д.

════════════════════════════════════════
TEST SUMMARY
════════════════════════════════════════

Results:
  ✓ Passed: 25/28
  ✗ Failed: 2/28
  ⊗ Skipped: 1
  Success rate: 89%
  Time: 45.3s

COMPONENT STATUS SUMMARY
✓ Imports       READY
✓ Document AI   READY
✓ Gemini API    READY
⚠ Ollama        NEEDS WORK (service not running)
✓ OSINT         READY
✓ RAG Pipeline  READY
✓ FastAPI       READY
✓ Integration   READY
```

---

## ⚠️ ЕСЛИ ТЕСТЫ НЕ ПРОХОДЯТ

### Проблема: "ImportError: No module named 'fastapi'"
```bash
# Решение: подожди пока закончится установка
# Если всё установилось, пересоздай venv:
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Проблема: "GEMINI_API_KEY not found"
```bash
# Решение: установи переменную окружения
# На Windows (PowerShell):
$env:GEMINI_API_KEY = "sk-..."

# Или на Windows (CMD):
set GEMINI_API_KEY=sk-...

# Или создай .env файл:
# GEMINI_API_KEY=sk-...
```

### Проблема: "Ollama connection refused"
```bash
# Это нормально! Ollama опциональный fallback
# Ты можешь использовать систему без Ollama
# Просто используй Gemini API
```

### Проблема: "Qdrant service not running"
```bash
# Это ожидается для Phase 1-2
# Qdrant нужен только для Phase 3
# Сейчас используется локальное хранилище
```

---

## 📈 ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ

### Success Rate 90%+ → ✅ ОТЛИЧНО
Система готова к использованию. Phase 1-2 работает.

### Success Rate 70-89% → ⚠️  ХОРОШО
Основной функционал работает, но есть проблемы с опциональными компонентами.

### Success Rate <70% → ❌ ПРОБЛЕМЫ
Есть критичные проблемы. Проверь логи и установку.

---

## 🚀 ПОСЛЕ УСПЕШНЫХ ТЕСТОВ

Если success rate >80%, ты можешь:

1. **Загружать документы** для анализа
2. **Делать OSINT запросы** по URL
3. **Общаться с Викой** через Gemini API
4. **Использовать RAG** для поиска в знаниях

---

## 📝 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Загрузить документ
```python
# Положи PDF в папку knowledge/
# Система автоматически распарсит и embeddings создаст
```

### Пример 2: OSINT запрос
```python
# POST /osint/search
# {
#   "url": "https://example.com",
#   "query": "company information"
# }
```

### Пример 3: RAG поиск
```python
# POST /rag/query
# {
#   "query": "Что это?",
#   "top_k": 5
# }
```

### Пример 4: Chat с Викой
```python
# Используй Gemini напрямую
# import google.generativeai as genai
# model = genai.GenerativeModel("gemini-2.5-flash")
# response = model.generate_content("Hello Vika!")
```

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ (Phase 3)

После успешных тестов Phase 1-2, ты готов к Phase 3:

1. **Qdrant setup** (4-6 часов)
   - Долгосрочная память для документов
   - Быстрый поиск

2. **Signal Bot** (6-8 часов)
   - Зашифровані команди через Signal

3. **GitHub Analyzer** (3-4 часа)
   - Аналіз репозиторіїв

---

## 📞 ЕСЛИ НУЖНА ПОМОЩЬ

1. **Проверь логи:**
   ```bash
   python test_phase1_2.py --verbose
   ```

2. **Запусти отдельный тест:**
   ```bash
   # Создай small test script для debugging
   ```

3. **Прочитай документацию:**
   - PHASE_3_ROADMAP.md
   - FINAL_VERDICT.md

---

## ✅ ГОТОВО!

После успешного прохождения тестов ты имеешь:

- ✓ Document AI pipeline
- ✓ OSINT automation
- ✓ Gemini 2.5 Flash integration
- ✓ Ollama fallback (если нужен)
- ✓ RAG retrieval
- ✓ FastAPI endpoints

**Тебе остаток добавить Phase 3 (Qdrant, Signal Bot, GitHub) и система полностью готова к боевому использованию! 🚀**

---

## 🎓 КРАТКОЕ РЕЗЮМЕ

```
Test Status: 🧪 Functional Test Suite
Components: 8 major + 25+ individual tests
Expected Pass Rate: 80-90%
Time to Complete: ~1 minute
Next Steps: Phase 3 implementation
```

**Удачи! Пошли тестировать! 💪**

---

*Created 14 березня 2026*
*For в/ч А7022 | Позывной БАС*
