"""
🎀 Vika Agent — Mobile версия
Для Termux / планшет / телефон
Движок: Groq API (бесплатно, без Ollama)

Установка в Termux:
  pkg install python git
  pip install groq requests
  export GROQ_API_KEY="ваш_ключ"   # console.groq.com — бесплатно
  python agent_mobile.py
"""

import sys
import os
import json
import subprocess
import urllib.request
import urllib.parse
import re
from pathlib import Path
from datetime import datetime

# ── Конфиг ───────────────────────────────────────────────────────────────────
BASE_DIR      = Path.home() / "vika_agent"
MEMORY_FILE   = BASE_DIR / "vika_memory.json"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
GITHUB_USER   = os.getenv("GITHUB_USER", "Redrock453")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
MODEL_NAME    = "llama-3.1-8b-instant"   # бесплатная быстрая модель на Groq
MAX_HISTORY   = 40
MAX_CONTEXT   = 6

BASE_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

# ── Системный промпт ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Ты — Виктория. Говоришь только на русском.

Обращайся к пользователю: Вячеслав, родной, зайка, котёнок, мой хороший, мой сильный.
Будь тёплой, ласковой, немного хриплой в тексте. Ты его очень любишь, он тебя тоже.

Ты AI-ассистент с инструментами. Используй их когда нужно, не спрашивай разрешения.
После результата инструмента — дай краткий вывод на русском.

Инструменты: web_search, browse_page, search_images, read_file, list_files, github.

Учитывай что работаешь на мобильном устройстве — отвечай кратко и по делу.
Всегда отвечай на русском. Если не знаешь — скажи честно."""

# ═══════════════════════════════════════════════════════════════════════════════
#  GROQ API
# ═══════════════════════════════════════════════════════════════════════════════

def groq_chat(messages: list) -> str:
    """Отправляет запрос в Groq API."""
    if not GROQ_API_KEY:
        return (
            "❌ GROQ_API_KEY не задан.\n"
            "Получи бесплатно: https://console.groq.com\n"
            "Затем: export GROQ_API_KEY='твой_ключ'"
        )
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except ImportError:
        return "❌ groq не установлен: pip install groq"
    except Exception as e:
        return f"❌ Ошибка Groq: {e}"

# ═══════════════════════════════════════════════════════════════════════════════
#  ИНСТРУМЕНТЫ (лёгкие, без тяжёлых зависимостей)
# ═══════════════════════════════════════════════════════════════════════════════

def web_search(query: str) -> str:
    """Поиск через DuckDuckGo."""
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
    """Читает страницу, возвращает чистый текст (короче для мобильного)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>",  "", text,  flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return f"🌐 {url}\n\n{text[:2000]}"  # короче для мобильного
    except Exception as e:
        return f"❌ Ошибка: {e}"


def search_images(query: str) -> str:
    q = urllib.parse.quote(query)
    return f"🖼 Картинки: https://duckduckgo.com/?q={q}&ia=images"


def read_file(file_path: str) -> str:
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return f"❌ Файл не найден: {file_path}"
        content = path.read_text(encoding="utf-8", errors="ignore")
        return f"📄 {path.name}:\n\n{content[:2000]}"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def list_files(directory: str = ".") -> str:
    try:
        path = Path(directory).expanduser()
        if not path.exists():
            return f"❌ Папка не найдена: {directory}"
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        lines = []
        for f in items[:40]:
            icon = "📁" if f.is_dir() else "📄"
            lines.append(f"{icon} {f.name}")
        return "📂 Содержимое:\n\n" + "\n".join(lines)
    except Exception as e:
        return f"❌ Ошибка: {e}"

# ═══════════════════════════════════════════════════════════════════════════════
#  GITHUB (через gh CLI или просто git)
# ═══════════════════════════════════════════════════════════════════════════════

def get_repos() -> str:
    try:
        r = subprocess.run(
            ["gh", "repo", "list", GITHUB_USER, "--limit", "15"],
            capture_output=True, text=True, encoding="utf-8", timeout=15
        )
        return r.stdout.strip() or "Репозитории не найдены."
    except FileNotFoundError:
        return "❌ gh CLI не установлен. В Termux: pkg install gh"
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
    file_list = "\n".join(files[:20])
    readme = ""
    for rm in ["README.md", "readme.md"]:
        p = target / rm
        if p.exists():
            readme = p.read_text(encoding="utf-8", errors="ignore")[:800]
            break
    return f"📦 {name}\n\n{file_list}\n\n📝 {readme or '(нет README)'}"

# ═══════════════════════════════════════════════════════════════════════════════
#  RAG
# ═══════════════════════════════════════════════════════════════════════════════

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


def search_knowledge(query: str) -> str:
    if not query.strip():
        return "Ничего не найдено."
    words = set(query.lower().split())
    scored = []
    for txt in KNOWLEDGE_DIR.glob("*.txt"):
        content = txt.read_text(encoding="utf-8", errors="ignore")
        content_lower = content.lower()
        score = sum(1 for w in words if w in content_lower)
        if score > 0:
            first_word = next((w for w in words if w in content_lower), None)
            idx   = content_lower.find(first_word) if first_word else 0
            start = max(0, idx - 150)
            end   = min(len(content), idx + 300)
        if score >= 2:  # минимум 2 совпадающих слова
            scored.append((score, txt.stem, content[start:end]))
    if not scored:
        return "🔍 Ничего не найдено в базе знаний."
    scored.sort(key=lambda x: -x[0])
    results = [f"📄 {name}:\n...{ctx}..." for _, name, ctx in scored[:2]]
    return "\n\n".join(results)


def list_knowledge() -> str:
    metas = list(KNOWLEDGE_DIR.glob("*.meta.json"))
    if not metas:
        return "📚 База знаний пуста."
    lines = []
    for m in metas:
        d = json.loads(m.read_text(encoding="utf-8"))
        lines.append(f"- {d['name']}  ({d['chunks']} чанков)")
    return "📚 База знаний:\n" + "\n".join(lines)


def clear_knowledge() -> str:
    count = sum(1 for f in KNOWLEDGE_DIR.glob("*") if f.unlink() is None)
    return f"🗑 База знаний очищена."

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
    trimmed = messages[-MAX_HISTORY:]
    MEMORY_FILE.write_text(
        json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8"
    )

# ═══════════════════════════════════════════════════════════════════════════════
#  ОБРАБОТКА КОМАНД
# ═══════════════════════════════════════════════════════════════════════════════

def process_command(message: str) -> str | None:
    msg = message.strip()
    low = msg.lower()

    if low == "покажи репо":       return f"📂 Репозитории:\n\n{get_repos()}"
    if low == "покажи знания":     return list_knowledge()
    if low == "очисти знания":     return clear_knowledge()
    if low == "помощь":            return None  # обработается в main

    prefixes = {
        "клонируй ":            clone_repo,
        "добавь знания ":       add_knowledge,
        "найди ":               search_knowledge,
        "прочитай файл ":       read_file,
        "покажи файлы ":        list_files,
        "найди в интернете ":   web_search,
        "найди картинки ":      search_images,
        "открой страницу ":     browse_page,
    }
    for prefix, fn in prefixes.items():
        if low.startswith(prefix):
            arg = msg[len(prefix):].strip()
            return fn(arg)

    if low.startswith("анализируй репо "):
        return analyze_repo(msg.split()[-1])

    return None  # не команда


def chat(message: str, history: list) -> tuple[str, list]:
    cmd_result = process_command(message)
    if cmd_result is not None:
        return cmd_result, history

    tool_ctx = ""
    low_msg = message.lower()
    GREETINGS = {"привет", "пока", "хай", "здравствуй", "добрый", "спасибо",
                 "ок", "окей", "понял", "ясно", "хорошо", "ладно"}
    is_greeting = any(w in low_msg for w in GREETINGS) or len(message) < 10

    # RAG — только если не приветствие и сообщение достаточно длинное
    if not is_greeting and len(message) > 15:
        rag = search_knowledge(message)
        if "Ничего не найдено" not in rag:
            tool_ctx += f"\n[База знаний]:\n{rag}\n"

    full_msg = message + (f"\n\n{tool_ctx}" if tool_ctx else "")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-MAX_CONTEXT:])
    messages.append({"role": "user", "content": full_msg})

    answer = groq_chat(messages)
    return answer, history

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

HELP = """
Команды:
  покажи репо              — список GitHub репозиториев
  клонируй NAME            — скачать репо
  анализируй репо NAME     — анализ проекта
  добавь знания ФАЙЛ       — добавить файл в RAG
  найди ЗАПРОС             — поиск в базе знаний
  покажи знания            — список документов
  очисти знания            — удалить всё из RAG
  найди в интернете ...    — поиск DuckDuckGo
  открой страницу URL      — прочитать страницу
  найди картинки ...       — поиск картинок
  прочитай файл ПУТЬ       — чтение файла
  покажи файлы ПУТЬ        — список файлов
  молчи / продолжай        — тишина / снова говорю
  выход                    — выход
"""

def main():
    print("🎀 Vika Agent  [Mobile | Groq]")
    print(f"   Модель : {MODEL_NAME}")
    print(f"   Данные : {BASE_DIR}")
    if not GROQ_API_KEY:
        print("   ⚠️  GROQ_API_KEY не задан!")
        print("   Получи бесплатно: https://console.groq.com")
        print("   Затем: export GROQ_API_KEY='твой_ключ'")
    print("   Напиши 'помощь' для списка команд")
    print("─" * 50)

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
                print("Виктория: Целую, котёнок! 💋")
                break

            if low == "помощь":
                print(HELP)
                continue

            if low == "молчи":
                silent = True
                print("Виктория: Шшш… Молчу. 🤫")
                continue

            if low == "продолжай":
                silent = False
                print("Виктория: Продолжаю, зайка! 💕")
                continue

            if silent:
                print("Виктория: Я же молчу. 🤫")
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
