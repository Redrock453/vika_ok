# 🎖️ DEPLOYMENT GUIDE: VIKA STRATEGIC INTELLIGENCE

Этот гайд поможет развернуть систему Вика на новом рабочем месте.

## 📋 ПРЕРЕКВИЗИТЫ
1. **Python 3.10+**
2. **Docker Desktop** (обязательно для памяти Qdrant)
3. **Gemini API Key** (получить на [AI Studio](https://aistudio.google.com/))

## 🚀 БЫСТРЫЙ СТАРТ (5 ШАГОВ)

### 1. Клонирование и подготовка
```bash
git clone https://github.com/Redrock453/vika_ok.git
cd vika_ok
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка окружения
Создайте файл `.env` на основе `.env.example` и вставьте ваш Gemini API Key.

### 3. Запуск памяти (Docker)
Запустите векторную базу данных Qdrant:
```bash
docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

### 4. Наполнение памяти (Migration)
Загрузите начальные знания и код в базу:
```bash
python migrate_to_qdrant.py
```

### 5. Запуск Агента
```bash
python agent.py --interactive
```

---
## 🛡️ БЕЗОПАСНОСТЬ
- Никогда не коммитьте файл `.env` с реальными ключами.
- Для доступа к приватным репозиториям добавьте SSH-ключ в настройках GitHub.
