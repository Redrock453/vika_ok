# Code Review Report: vika_ok v13.1
**Дата:** 2026-04-27
**Репозиторий:** https://github.com/Redrock453/vika_ok

---

## Сводка

| Критичность | Количество |
|-------------|------------|
| 🔴 Критические | 4 |
| 🟠 Высокие | 5 |
| 🟡 Средние | 6 |
| 🔵 Низкие | 3 |
| **Всего** | **18** |

---

## 🔴 Критические проблемы

### 1. AttributeError в ToolExecutor - opencode не инициализирован
**Файл:** `src/services/tools.py:57, 59, 63, 67`

```python
# В методе _execute():
elif action == "opencode":
    return self.opencode.run(task)  # ❌ self.opencode не существует!
```

**Проблема:** В `__init__` создается только `self.ssh`, но `self.opencode` не создан. При вызове любого opencode action будет `AttributeError`.

**Решение:**
```python
def __init__(self):
    self.ssh = SSHExecutor()
    self.opencode = OpenCodeExecutor()  # Добавить
```

---

### 2. Дублирующийся небезопасный файл telegram_bot.py
**Файл:** `telegram_bot.py:78-79`

```python
local_path = f"/tmp/{file_id}"  # ❌ Path traversal уязвимость!
```

**Проблема:** Это старый файл, который не используется (используется `src/handlers/telegram.py`), но он содержит ту же уязвимость path traversal, что была исправлена в новой версии.

**Решение:** Удалить файл `telegram_bot.py` или перенести в `archive/`.

---

### 3. SSH ключ захардкожен
**Файл:** `src/services/ssh.py:21`

```python
def __init__(self):
    self.key_path = "/root/.ssh/id_ed25519"  # ❌ Не configurable
```

**Проблема:** Путь к SSH ключу зашит в коде. Невозможно использовать другой ключ.

**Решение:**
```python
def __init__(self, key_path: str = None):
    self.key_path = key_path or os.getenv("SSH_KEY_PATH", "/root/.ssh/id_ed25519")
```

---

### 4. Race condition в tasks.json
**Файл:** `src/services/tasks.py:18-33`

```python
def _load(self) -> list[dict]:
    try:
        with open(config.tasks_file, "r") as f:  # ❌ No file locking!
            return json.load(f)
```

**Проблема:** При одновременной записи и чтении файл может быть поврежден. Та же проблема, что была в `history.py`.

**Решение:** Добавить file locking с `fcntl.flock()` как в `history.py`.

---

## 🟠 Высокие проблемы

### 5. Ошибка в get_collection_info - name = vector_size
**Файл:** `qdrant_manager.py:163`

```python
return {
    "name": info.config.params.vectors.size,  # ❌ Дублирует vector_size!
    "vector_size": info.config.params.vectors.size,
```

**Проблема:** Ключ `name` содержит то же значение что и `vector_size`, а должно быть имя коллекции.

**Решение:**
```python
return {
    "name": info.config.params.vectors,  # или info.status
    "vector_size": info.config.params.vectors.size,
```

---

### 6. Небезопасная SSH конфигурация
**Файл:** `src/services/ssh.py:28-36`

```python
cmd = [
    "ssh",
    "-o", "StrictHostKeyChecking=no",  # ❌ Уязвимость MITM
    "-o", "ConnectTimeout=10",
    "-o", f"ServerAliveInterval={timeout}",  # ❌ Неправильное использование
```

**Проблемы:**
- `StrictHostKeyChecking=no` уязвим для MITM атак
- `ServerAliveInterval` не должен равняться timeout

**Решение:**
```python
cmd = [
    "ssh",
    "-o", "StrictHostKeyChecking=accept-new",  # Лучше
    "-o", "ConnectTimeout=10",
    "-o", "ServerAliveInterval=5",  # Фиксированное значение
    "-o", f"ServerAliveCountMax={timeout // 5}",
```

---

### 7. Локальный импорт qdrant_manager
**Файл:** `src/services/rag.py:13`

```python
from qdrant_manager import QdrantManager  # ❌ Может не работать из других директорий
```

**Проблема:** Импортирует как локальный модуль. При запуске из другой директории будет `ImportError`.

**Решение:**
```python
try:
    from qdrant_client import QdrantClient
    from sentence_transformers import SentenceTransformer
    # QdrantManager должен быть в пакете
    try:
        from qdrant_manager import QdrantManager
    except ImportError:
        from ..qdrant_manager import QdrantManager  # Альтернативный путь
```

---

### 8. Дублирование валидации в run.py
**Файл:** `run.py:27-42`

```python
is_valid, errors = config.validate()  # Строка 27-33
if not is_valid:
    ...

if not config.telegram_token:  # Строка 35-41 - дублирует выше!
    logger.error("TELEGRAM_BOT_TOKEN not set!")
```

**Проблема:** Валидация повторяется дважды. Первая уже проверяет токен.

**Решение:** Удалить дублирующие проверки (строки 35-41).

---

### 9. Несоответствие версии в SYSTEM_PROMPT
**Файл:** `src/core/agent.py:15`

```python
SYSTEM_PROMPT = (
    "Ти — Vika_Ok v13.0. ..."  # ❌ Должно быть v13.1
```

**Проблема:** Версия в промpte устарела. Проект уже v13.1.

**Решение:** Обновить до v13.1.

---

## 🟡 Средние проблемы

### 10. Нет проверки существования SSH ключа
**Файл:** `src/services/ssh.py:23-52`

**Проблема:** Ключ не проверяется на существование перед использованием. Ошибка только при выполнении команды.

**Решение:** Добавить проверку в `__init__`:
```python
if not os.path.exists(self.key_path):
    raise FileNotFoundError(f"SSH key not found: {self.key_path}")
```

---

### 11. Общий User-Agent в web_search
**Файл:** `src/services/search.py:16`

```python
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, ...)
```

**Проблема:** Слишком общий User-Agent может быть заблокирован.

**Решение:** Использовать более реалистичный UA:
```python
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
```

---

### 12. Задержка в RAG - модель грузится в фоне
**Файл:** `src/services/rag.py:46-55`

```python
def _load_model(self):
    try:
        self.embedding_model = SentenceTransformer("...")
        self._ready = True
```

**Проблема:** Первые запросы после запуска вернут пустой результат, пока модель грузится. Нет индикации прогресса.

**Решение:** Добавить timeout или ждать загрузки:
```python
def wait_ready(self, timeout: int = 30):
    start = time.time()
    while not self._ready and (time.time() - start) < timeout:
        time.sleep(0.5)
```

---

### 13. Не обрабатывается исключение в _convert_to_mp3
**Файл:** `src/handlers/telegram.py:51-70`

**Проблема:** При ошибке ffmpeg логируется только stderr, но не stdout. Потенциально полезная информация теряется.

**Решение:** Логировать оба потока:
```python
logger.error(f"FFmpeg failed: stdout={result.stdout}, stderr={result.stderr}")
```

---

### 14. tasks.json может стать очень большим
**Файл:** `src/services/tasks.py:42-54`

```python
def due(self) -> list[dict]:
    ...
    for task in self._tasks:
        if ... and not task.get("done", False):
            task["done"] = True
            due_tasks.append(task)
        else:
            remaining.append(task)
    self._tasks = remaining  # Выполненные удаляются
```

**Проблема:** Все выполненные задачи сохраняются в файл через `save_tasks()`. Со временем файл может содержать только выполненные, что странно. Логика кажется перепутанной.

**Решение:** Проверить логику - возможно должно удалять выполненные, а не сохранять их.

---

### 15. Нет reconnect логики для Qdrant
**Файл:** `qdrant_manager.py:38-43`

```python
try:
    self.client = QdrantClient(host=self.host, port=self.port)
    logger.info(f"Connected to Qdrant...")
except Exception as e:
    logger.error(f"Failed to connect to Qdrant: {e}")
    raise
```

**Проблема:** При потере соединения нет автоматического reconnect. Бот может перестать работать с RAG.

**Решение:** Добавить retry wrapper для всех методов.

---

## 🔵 Низкие проблемы

### 16. Дублирующиеся сообщения в логах
**Файл:** `run.py:44`

```python
logger.info(f"Vika_Ok v13.1 starting... (log level: {config.log_level})")
```

**Файл:** `src/handlers/telegram.py:184`

```python
logger.info("Bot started successfully")
```

**Проблема:** Два сообщения о старте могут запутать.

**Решение:** Оставить только одно информативное сообщение.

---

### 17. Жестко заданный интервал в proactive_heart
**Файл:** `src/handlers/telegram.py:173`

```python
await asyncio.sleep(20)  # ❌ Not configurable
```

**Проблема:** Интервал проверки задач захардкожен.

**Решение:** Добавить в конфиг: `TASK_CHECK_INTERVAL = 20`

---

### 18. Пустой except в transcribe_audio
**Файл:** `telegram_bot.py:92-102` (старый файл)

**Проблема:** В старом файле есть голые `except:` без логирования.

**Решение:** Удалить файл (см. проблему #2).

---

## Статистика по файлам

| Файл | Проблемы |
|------|----------|
| `src/services/tools.py` | 1 (критическая) |
| `telegram_bot.py` | 1 (критическая) + 1 (низкая) |
| `src/services/ssh.py` | 2 (критическая, высокая) |
| `src/services/tasks.py` | 1 (критическая) + 1 (средняя) |
| `qdrant_manager.py` | 1 (высокая) + 1 (средняя) |
| `src/services/rag.py` | 1 (высокая) + 1 (средняя) |
| `run.py` | 1 (высокая) + 1 (низкая) |
| `src/core/agent.py` | 1 (высокая) |
| `src/handlers/telegram.py` | 1 (средняя) + 1 (низкая) |
| `src/services/search.py` | 1 (средняя) |

---

## Приоритет исправления

1. **Срочно (до деплоя):**
   - #1: Добавить `self.opencode` в `ToolExecutor.__init__`
   - #2: Удалить `telegram_bot.py`
   - #4: Добавить file locking в `tasks.py`

2. **В ближайшее время:**
   - #5: Исправить `get_collection_info`
   - #6: Улучшить SSH безопасность
   - #7: Исправить импорт `qdrant_manager`

3. **Позже:**
   - #8-#18: Остальные улучшения

---

## Рекомендации по архитектуре

1. **Единый entrypoint:** Оставить только `run.py` и `src/handlers/telegram.py`. Удалить все старые файлы уровня корня (`telegram_bot.py`, `agent.py` и т.д.).

2. **Конфигурация:** Вынести все magic numbers в `config.py` (интервалы, timeouts, пути).

3. **Модульность:** Переместить `qdrant_manager.py` в `src/core/` или `src/services/`.

4. **Тесты:** Добавить unit тесты для критических компонент (`ToolExecutor`, `SSHExecutor`, `TaskScheduler`).

5. **Мониторинг:** Добавить метрики для:
   - Количество успешных/неудачных SSH подключений
   - Время ответа LLM по провайдерам
   - Размер history.json и tasks.json

---

## Заключение

Проект значительно улучшен по сравнению с v13.0:
- ✅ Добавлен rate limiting
- ✅ Исправлен path traversal в новых файлах
- ✅ Добавлено file locking для history.json
- ✅ Добавлен health check API
- ✅ Улучшено логирование

Однако остались критические проблемы, особенно:
- Неинициализированный `opencode` в `ToolExecutor`
- Небезопасная SSH конфигурация
- Отсутствие file locking для tasks.json

Рекомендуется исправить все критические и высокие проблемы перед релизом.
