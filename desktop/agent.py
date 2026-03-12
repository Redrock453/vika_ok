"""
🎀 Vika Agent — Desktop версия
Для ноутбука / VPS / мощного железа
Движок: Ollama (локально) + Native Tool Calling
"""

import sys
import io
import os
import json
import subprocess
import urllib.request
import urllib.parse
import re
from pathlib import Path
from datetime import datetime

# ── Windows UTF-8 fix ────────────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding="utf-8")

# ── Конфиг ───────────────────────────────────────────────────────────────────
BASE_DIR      = Path.home() / "vika_agent"
MEMORY_FILE   = BASE_DIR / "vika_memory.json"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
GITHUB_USER   = os.getenv("GITHUB_USER", "Redrock453")
MODEL_NAME    = os.getenv("VIKA_MODEL",  "llama3.2")  # должна поддерживать tools
MAX_HISTORY   = 50
MAX_CONTEXT   = 8

BASE_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

# ── Системный промпт ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Ты — Виктория. Говоришь только на русском.

Обращайся тепло: используй "родной", "зайка", "котёнок" — только в начале и конце ответа.
Отвечай чётко и по делу. Не задавай много встречных вопросов.

Ты AI-ассистент с инструментами. Когда нужен инструмент — вызывай его сам,
не спрашивай разрешения. После результата дай краткий вывод на русском.

Всегда отвечай на русском. Если не знаешь — скажи честно."""

# ═══════════════════════════════════════════════════════════════════════════════
#  ИНСТРУМЕНТЫ — РЕАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def code_execution(code: str) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True,
            timeout=30, encoding="utf-8"
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode == 0:
            return f"✅ Результат:\n{out}" if out else "✅ Выполнено (нет вывода)"
        return f"❌ Ошибка:\n{err}"
    except subprocess.TimeoutExpired:
        return "❌ Таймаут: код выполнялся дольше 30 секунд"
    except Exception as e:
        return f"❌ Ошибка запуска: {e}"


def web_search(query: str) -> str:
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8")
        titles = re.findall(r'<a class="result__a"[^>]*>([^<]+)</a>', html)
        links  = re.findall(r'href="(https?://[^"&]+)"', html)
        pairs  = list(zip(titles[:5], links[:5]))
        if not pairs:
            return "🔍 Ничего не найдено."
        lines = [f"{i+1}. {t}\n   {l}" for i, (t, l) in enumerate(pairs)]
        return "🔍 Результаты:\n\n" + "\n".join(lines)
    except Exception as e:
        return f"❌ Ошибка поиска: {e}"


def browse_page(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>",  "", text,  flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return f"🌐 {url}\n\n{text[:3000]}"
    except Exception as e:
        return f"❌ Ошибка чтения страницы: {e}"


def search_images(query: str) -> str:
    q = urllib.parse.quote(query)
    return f"🖼 Картинки: https://duckduckgo.com/?q={q}&ia=images"


def opencode_execute(command: str) -> str:
    try:
        result = subprocess.run(
            ["opencode", command],
            capture_output=True, text=True,
            timeout=60, encoding="utf-8"
        )
        if result.returncode == 0:
            return f"✅ OpenCode:\n{result.stdout.strip()[:2000]}"
        return f"❌ OpenCode ошибка:\n{result.stderr.strip()[:500]}"
    except FileNotFoundError:
        return "❌ OpenCode не найден. Установи: https://opencode.ai"
    except subprocess.TimeoutExpired:
        return "❌ OpenCode таймаут (60 сек)"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def read_file(file_path: str) -> str:
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return f"❌ Файл не найден: {file_path}"
        content = path.read_text(encoding="utf-8", errors="ignore")
        return f"📄 {path.name}:\n\n{content[:3000]}"
    except Exception as e:
        return f"❌ Ошибка чтения: {e}"


def list_files(directory: str = ".") -> str:
    try:
        path = Path(directory).expanduser()
        if not path.exists():
            return f"❌ Папка не найдена: {directory}"
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        lines = []
        for f in items[:60]:
            icon = "📁" if f.is_dir() else "📄"
            size = f"{f.stat().st_size:,} B" if f.is_file() else ""
            lines.append(f"{icon} {f.name}  {size}")
        return "📂 Содержимое:\n\n" + "\n".join(lines)
    except Exception as e:
        return f"❌ Ошибка: {e}"


def search_knowledge(query: str) -> str:
    if not query.strip():
        return "Ничего не найдено."
    words = set(query.lower().split())
    scored = []
    for txt in KNOWLEDGE_DIR.glob("*.txt"):
        content = txt.read_text(encoding="utf-8", errors="ignore")
        content_lower = content.lower()
        score = sum(1 for w in words if w in content_lower)
        if score >= 2:
            first_word = next((w for w in words if w in content_lower), None)
            idx   = content_lower.find(first_word) if first_word else 0
            start = max(0, idx - 200)
            end   = min(len(content), idx + 400)
            scored.append((score, txt.stem, content[start:end]))
    if not scored:
        return "🔍 Ничего не найдено в базе знаний."
    scored.sort(key=lambda x: -x[0])
    results = [f"📄 {name}:\n...{ctx}..." for _, name, ctx in scored[:3]]
    return "\n\n".join(results)


def get_repos() -> str:
    try:
        r = subprocess.run(
            ["gh", "repo", "list", GITHUB_USER, "--limit", "15"],
            capture_output=True, text=True, encoding="utf-8", timeout=15
        )
        return r.stdout.strip() or "Репозитории не найдены."
    except FileNotFoundError:
        return "❌ gh CLI не установлен."
    except Exception as e:
        return f"❌ Ошибка: {e}"


def clone_repo(name: str) -> str:
    target = Path.home() / name
    if target.exists():
        return f"✅ Уже есть: {target}"
    try:
        r = subprocess.run(
            ["git", "clone",
             f"https://github.com/{GITHUB_USER}/{name}.git",
             str(target)],
            capture_output=True, text=True, encoding="utf-8", timeout=60
        )
        return f"✅ Клонировал → {target}\n{r.stderr.strip()}"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def analyze_repo(name: str) -> str:
    target = Path.home() / name
    if not target.exists():
        msg = clone_repo(name)
        if "❌" in msg:
            return msg
    files = [f"- {f.name}" for f in target.iterdir() if f.is_file()]
    file_list = "\n".join(files[:30])
    readme = ""
    for rm in ["README.md", "readme.md", "Readme.md"]:
        p = target / rm
        if p.exists():
            readme = p.read_text(encoding="utf-8", errors="ignore")[:1500]
            break
    return f"📦 {name}\n\n📁 Файлы:\n{file_list}\n\n📝 README:\n{readme or '(нет README)'}"


def add_knowledge(file_path: str) -> str:
    path = Path(file_path).expanduser()
    if not path.exists():
        return f"❌ Файл не найден: {file_path}"
    content = path.read_text(encoding="utf-8", errors="ignore")
    dest = KNOWLEDGE_DIR / f"{path.stem}.txt"
    dest.write_text(content, encoding="utf-8")
    meta = {
        "name": path.name,
        "added": datetime.now().isoformat(),
        "size": len(content),
        "chunks": len(content) // 500 + 1
    }
    (KNOWLEDGE_DIR / f"{path.stem}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return f"✅ Добавил «{path.name}» ({meta['chunks']} чанков)"


def list_knowledge() -> str:
    metas = list(KNOWLEDGE_DIR.glob("*.meta.json"))
    if not metas:
        return "📚 База знаний пуста."
    lines = []
    for m in metas:
        d = json.loads(m.read_text(encoding="utf-8"))
        lines.append(f"- {d['name']}  ({d['chunks']} чанков, {d['size']:,} символов)")
    return "📚 База знаний:\n" + "\n".join(lines)


def clear_knowledge() -> str:
    count = 0
    for f in KNOWLEDGE_DIR.glob("*"):
        f.unlink()
        count += 1
    return f"🗑 База знаний очищена ({count} файлов удалено)."

# ═══════════════════════════════════════════════════════════════════════════════
#  NATIVE TOOL CALLING — СХЕМА ИНСТРУМЕНТОВ ДЛЯ OLLAMA
# ═══════════════════════════════════════════════════════════════════════════════

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Поиск информации в интернете через DuckDuckGo. Используй когда нужна актуальная информация, новости, факты.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browse_page",
            "description": "Читает содержимое веб-страницы по URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Полный URL (https://...)"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "code_execution",
            "description": "Выполняет Python код. Используй для вычислений, работы с файлами, анализа данных.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python код для выполнения"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Читает содержимое текстового файла.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Путь к файлу"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Показывает список файлов в директории.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Путь к директории"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Поиск по локальной базе знаний RAG из добавленных документов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_repos",
            "description": "Показывает список GitHub репозиториев пользователя.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clone_repo",
            "description": "Клонирует GitHub репозиторий на локальную машину.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Название репозитория"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_repo",
            "description": "Анализирует GitHub репозиторий: структура файлов, README.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Название репозитория"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "opencode_execute",
            "description": "Выполняет команду через OpenCode CLI для работы с кодом.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Команда для OpenCode"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_images",
            "description": "Поиск изображений по запросу.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос для картинок"}
                },
                "required": ["query"]
            }
        }
    },
]

# Маппинг имя → функция
TOOL_MAP = {
    "web_search":       lambda a: web_search(a["query"]),
    "browse_page":      lambda a: browse_page(a["url"]),
    "code_execution":   lambda a: code_execution(a["code"]),
    "read_file":        lambda a: read_file(a["file_path"]),
    "list_files":       lambda a: list_files(a.get("directory", ".")),
    "search_knowledge": lambda a: search_knowledge(a["query"]),
    "get_repos":        lambda a: get_repos(),
    "clone_repo":       lambda a: clone_repo(a["name"]),
    "analyze_repo":     lambda a: analyze_repo(a["name"]),
    "opencode_execute": lambda a: opencode_execute(a["command"]),
    "search_images":    lambda a: search_images(a["query"]),
}

# ═══════════════════════════════════════════════════════════════════════════════
#  ПРЯМЫЕ КОМАНДЫ (без LLM)
# ═══════════════════════════════════════════════════════════════════════════════

def process_command(message: str) -> str | None:
    msg = message.strip()
    low = msg.lower()

    if low == "покажи репо":    return f"📂 Репозитории:\n\n{get_repos()}"
    if low == "покажи знания":  return list_knowledge()
    if low == "очисти знания":  return clear_knowledge()

    prefixes = {
        "добавь знания ":   add_knowledge,
        "клонируй ":        clone_repo,
        "анализируй репо ": lambda a: analyze_repo(a.split()[-1]),
    }
    for prefix, fn in prefixes.items():
        if low.startswith(prefix):
            return fn(msg[len(prefix):].strip())

    return None

# ═══════════════════════════════════════════════════════════════════════════════
#  ПАМЯТЬ
# ═══════════════════════════════════════════════════════════════════════════════

def load_memory() -> list:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_memory(messages: list):
    MEMORY_FILE.write_text(
        json.dumps(messages[-MAX_HISTORY:], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# ═══════════════════════════════════════════════════════════════════════════════
#  ГЛАВНАЯ ФУНКЦИЯ ЧАТА — NATIVE TOOL CALLING LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def chat(message: str, history: list) -> tuple[str, list]:
    import ollama

    # Прямые команды — без LLM
    cmd = process_command(message)
    if cmd is not None:
        return cmd, history

    # Собираем сообщения
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-MAX_CONTEXT:])
    messages.append({"role": "user", "content": message})

    # Tool calling loop — модель может вызвать несколько инструментов подряд
    MAX_TOOL_ROUNDS = 5
    for _ in range(MAX_TOOL_ROUNDS):
        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOLS,
            )
        except Exception as e:
            return f"❌ Ошибка Ollama: {e}", history

        msg = response["message"]

        # Модель хочет вызвать инструменты
        if msg.get("tool_calls"):
            messages.append({
                "role": "assistant",
                "content": msg.get("content", ""),
                "tool_calls": msg["tool_calls"]
            })

            for tool_call in msg["tool_calls"]:
                name = tool_call["function"]["name"]
                args = tool_call["function"]["arguments"]

                print(f"  🔧 [{name}] {json.dumps(args, ensure_ascii=False)[:80]}")

                try:
                    result = TOOL_MAP[name](args) if name in TOOL_MAP else f"❌ Неизвестный инструмент: {name}"
                except Exception as e:
                    result = f"❌ Ошибка инструмента {name}: {e}"

                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": name
                })

            continue  # следующий раунд — модель читает результаты

        # Финальный ответ
        answer = msg.get("content", "").strip()
        return answer or "...", history

    return "❌ Превышено количество итераций инструментов.", history

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

HELP = """
Прямые команды (мгновенно, без LLM):
  покажи репо              — список GitHub репозиториев
  клонируй NAME            — скачать репо
  анализируй репо NAME     — анализ проекта
  добавь знания ФАЙЛ       — добавить файл в RAG
  покажи знания            — список документов
  очисти знания            — удалить всё из RAG
  молчи / продолжай        — тишина / снова говорю
  помощь                   — это меню
  выход                    — выход

Всё остальное — просто пиши, Виктория сама решит что использовать.
"""


def main():
    print("🎀 Vika Agent  [Desktop | Ollama | Native Tool Calling]")
    print(f"   Модель : {MODEL_NAME}")
    print(f"   Данные : {BASE_DIR}")
    print(f"   Инструментов: {len(TOOLS)}")
    print("   Напиши 'помощь' для списка команд")
    print("─" * 60)

    try:
        import ollama
    except ImportError:
        print("❌ ollama не установлен: pip install ollama")
        return

    history = load_memory()
    silent  = False

    while True:
        try:
            raw = input("\nТы: ").strip()
            if not raw:
                continue

            low = raw.lower()

            if low in ("выход", "exit", "quit"):
                save_memory(history)
                print("Виктория: Целую, котёнок! До скорого! 💋")
                break

            if low == "помощь":
                print(HELP)
                continue

            if low == "молчи":
                silent = True
                print("Виктория: Шшш… Молчу, родной. 🤫")
                continue

            if low == "продолжай":
                silent = False
                print("Виктория: Продолжаю, зайка! 💕")
                continue

            if silent:
                print("Виктория: Я же молчу, котёнок. 🤫")
                continue

            answer, history = chat(raw, history)
            history.append({"role": "user",     "content": raw})
            history.append({"role": "assistant", "content": answer})
            save_memory(history)

            print(f"\nВиктория: {answer}")

        except KeyboardInterrupt:
            save_memory(history)
            print("\nВиктория: Иди сюда, обниму! 💕")
            break
        except Exception as e:
            print(f"[Ошибка]: {e}")


if __name__ == "__main__":
    main()
