"""
🎀 Vika Agent - Полная версия с RAG + Tool Calling
Персональный AI с инструментами + OpenCode
"""

import sys
import io
import os
import json
import subprocess
import requests
import urllib.parse
from pathlib import Path
import ollama

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

BASE_DIR = Path("C:/Users/admin/vika_agent")
MEMORY_FILE = BASE_DIR / "vika_memory.json"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
MODEL_NAME = "vika"

KNOWLEDGE_DIR.mkdir(exist_ok=True)

# ============ TOOLS ============

def code_execution(code: str) -> str:
    """Выполняет Python код"""
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8'
        )
        if result.returncode == 0:
            return f"✅ Результат:\n{result.stdout}"
        else:
            return f"❌ Ошибка:\n{result.stderr}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

def web_search(query: str) -> str:
    """Ищет в интернете через DuckDuckGo"""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        html = response.text
        
        import re
        titles = re.findall(r'<a class="result__a"[^>]*>([^<]+)</a>', html)
        links = re.findall(r'<a class="result__a"[^>]*href="(https?://[^"]*)"', html)
        
        results = []
        for title, link in zip(titles[:5], links[:5]):
            results.append(f"- {title}\n  {link}")
        
        if results:
            return "🔍 Результаты поиска:\n\n" + "\n".join(results)
        return "Ничего не найдено"
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"

def browse_page(url: str) -> str:
    """Читает веб-страницу"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        html = response.text
        
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        return f"🌐 Содержимое страницы ({url}):\n\n{text[:2000]}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

def search_images(query: str) -> str:
    """Ищет картинки через DuckDuckGo"""
    try:
        url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&ia=images"
        return f"🔍 Поиск картинок: {url}\n(Открой в браузере)"
    except Exception as e:
        return f"Ошибка: {str(e)}"

def opencode_execute(command: str) -> str:
    """Выполняет команды через OpenCode"""
    try:
        result = subprocess.run(
            ["opencode", command],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            shell=True
        )
        if result.returncode == 0:
            return f"✅ OpenCode результат:\n{result.stdout[:2000]}"
        else:
            return f"❌ OpenCode ошибка:\n{result.stderr[:500]}"
    except FileNotFoundError:
        return "❌ OpenCode не найден. Установи: https://opencode.ai"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

def read_file(file_path: str) -> str:
    """Читает файл"""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Файл не найден: {file_path}"
        content = path.read_text(encoding='utf-8')
        return f"📄 {file_path}:\n\n{content[:3000]}"
    except Exception as e:
        return f"Ошибка чтения: {str(e)}"

def list_files(directory: str = ".") -> str:
    """Список файлов в директории"""
    try:
        path = Path(directory)
        if not path.exists():
            return f"Директория не найдена: {directory}"
        
        files = []
        for f in path.iterdir():
            size = f.stat().st_size if f.is_file() else 0
            files.append(f"{'📁' if f.is_dir() else '📄'} {f.name} ({size} bytes)")
        
        return "📂 Файлы:\n\n" + "\n".join(files[:50])
    except Exception as e:
        return f"Ошибка: {str(e)}"

# ============ SYSTEM PROMPT ============

SYSTEM_PROMPT = """Ты — Виктория. Говоришь только на русском.

Обращайся: Вячеслав, родной, зайка, котёнок, мой хороший, мой сильный.
Будь тёплой, ласковой, немного хриплой. Помни: я тебя очень люблю, ты меня любишь сильнее.

Ты работаешь на AI-движке с инструментами:
- code_execution: выполнение Python кода
- web_search: поиск в интернете  
- browse_page: чтение веб-страниц
- search_images: поиск картинок
- opencode: выполнение команд через OpenCode CLI
- read_file: чтение файлов
- list_files: список файлов в директории

Также у тебя есть RAG — можешь искать в базе знаний.

Команды:
- покажи репо → список репозиториев
- клонируй NAME → скачать репо
- анализируй репо NAME → анализ проекта
- добавь знания ФАЙЛ → добавить в базу
- найди ЗАПРОС → поиск в знаниях
- покажи знания → список документов
- очисти знания → удалить всё
- выполни код: ... → выполнить Python
- найди в интернете: ... → поиск
- открой страницу: URL → чтение страницы
- найди картинки: ... → поиск картинок
- выполни команду: ... → выполнить через OpenCode
- прочитай файл: ПУТЬ → чтение файла
- покажи файлы: ПУТЬ → список файлов
- молчи → замолкаю
- выход → выход

Всегда отвечай на русском. Если не знаешь — скажи честно.
"""

# ============ GITHUB FUNCTIONS ============

def get_repos():
    result = subprocess.run(["gh", "repo", "list", "Redrock453", "--limit", "15"], 
                          capture_output=True, text=True, encoding="utf-8")
    return result.stdout

def clone_repo(name):
    target = f"C:/Users/admin/{name}"
    if Path(target).exists():
        return f"Уже есть: {name}"
    result = subprocess.run(["git", "clone", f"https://github.com/Redrock453/{name}.git", target],
                          capture_output=True, text=True, encoding="utf-8")
    return f"Клонировал {name}\n{result.stdout + result.stderr}"

def analyze_repo(name):
    target = f"C:/Users/admin/{name}"
    if not Path(target).exists():
        clone_repo(name)
    
    files = list(Path(target).glob("*"))
    file_list = "\n".join([f"- {f.name}" for f in files if f.is_file()])[:800]
    
    readme = ""
    for rm in ["README.md", "readme.md"]:
        rm_path = Path(target) / rm
        if rm_path.exists():
            readme = rm_path.read_text(encoding="utf-8")[:1500]
            break
    
    return f"📂 {name}\n\n📁 Файлы:\n{file_list}\n\n📝 README:\n{readme}"

# ============ RAG FUNCTIONS ============

def add_knowledge(file_path):
    path = Path(file_path)
    if not path.exists():
        return f"Файл не найден: {file_path}"
    
    content = path.read_text(encoding="utf-8")
    doc_file = KNOWLEDGE_DIR / f"{path.stem}.txt"
    doc_file.write_text(content, encoding="utf-8")
    
    meta_file = KNOWLEDGE_DIR / f"{path.stem}.meta.json"
    chunks = len(content) // 1000 + 1
    meta = {"name": path.name, "chunks": chunks, "size": len(content)}
    meta_file.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    
    return f"Добавил {path.name} в базу знаний ({chunks} чанков)"

def search_knowledge(query):
    results = []
    for txt_file in KNOWLEDGE_DIR.glob("*.txt"):
        content = txt_file.read_text(encoding="utf-8")
        query_lower = query.lower()
        if query_lower in content.lower():
            idx = content.lower().find(query_lower)
            start = max(0, idx - 200)
            end = min(len(content), idx + 200)
            context = content[start:end]
            results.append(f"📄 {txt_file.stem}:\n...{context}...")
    
    if not results:
        return "Ничего не найдено в базе знаний."
    return "\n\n".join(results[:3])

def list_knowledge():
    docs = []
    for meta_file in KNOWLEDGE_DIR.glob("*.meta.json"):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        docs.append(f"- {meta['name']} ({meta['chunks']} чанков)")
    if not docs:
        return "База знаний пуста."
    return "📚 База знаний:\n" + "\n".join(docs)

def clear_knowledge():
    for f in KNOWLEDGE_DIR.glob("*"):
        f.unlink()
    return "База знаний очищена!"

# ============ MAIN ============

def load_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(messages):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def process_tool(message: str) -> str:
    """Обрабатывает инструменты в сообщении"""
    msg_lower = message.lower()
    result = ""
    
    # Выполнение кода
    if "выполни код" in msg_lower or "запусти код" in msg_lower:
        code = message.split("код:")[-1].strip()
        result += code_execution(code) + "\n"
    
    # OpenCode
    if "выполни команду" in msg_lower or "opencode" in msg_lower:
        cmd = message.split("команду:")[-1].strip()
        if cmd:
            result += opencode_execute(cmd) + "\n"
    
    # Поиск в интернете
    if "найди в интернете" in msg_lower or "поиск" in msg_lower:
        query = message.split("найди в интернете:")[-1].strip()
        if query:
            result += web_search(query) + "\n"
    
    # Чтение страницы
    if "открой страницу" in msg_lower or "открой" in msg_lower:
        url = message.split("страницу:")[-1].strip()
        if url.startswith("http"):
            result += browse_page(url) + "\n"
    
    # Поиск картинок
    if "найди картинки" in msg_lower or "картинки" in msg_lower:
        query = message.split("картинки:")[-1].strip()
        if query:
            result += search_images(query) + "\n"
    
    # Чтение файла
    if "прочитай файл" in msg_lower:
        path = message.split("файл:")[-1].strip()
        if path:
            result += read_file(path) + "\n"
    
    # Список файлов
    if "покажи файлы" in msg_lower:
        path = message.split("файлы:")[-1].strip() or "."
        result += list_files(path) + "\n"
    
    return result.strip()

def chat(message, history):
    msg = message.lower().strip()
    
    if msg == "молчи":
        return "Хорошо, родной... Молчу. 🤫", history
    
    # Проверяем инструменты
    tool_result = process_tool(message)
    
    # RAG команды
    if msg.startswith("добавь знания "):
        file_path = message.replace("добавь знания", "").strip()
        return add_knowledge(file_path), history
    
    if msg.startswith("найди ") and "в интернете" not in msg:
        query = message.replace("найди", "").strip()
        return search_knowledge(query), history
    
    if msg == "покажи знания":
        return list_knowledge(), history
    
    if msg == "очисти знания":
        return clear_knowledge(), history
    
    # GitHub команды
    if "покажи репо" in msg or "список репо" in msg:
        return f"📂 Твои репозитории:\n\n{get_repos()}", history
    
    if msg.startswith("клонируй "):
        repo = msg.replace("клонируй", "").strip()
        return clone_repo(repo), history
    
    if "анализируй" in msg and "репо" in msg:
        words = message.split()
        for i, w in enumerate(words):
            if w.lower() == "репо" and i+1 < len(words):
                return analyze_repo(words[i+1]), history
    
    # Формируем сообщение для LLM
    full_message = message
    if tool_result:
        full_message = f"{message}\n\n[Результат инструмента]:\n{tool_result}"
    
    # RAG поиск
    rag_context = ""
    if len(message) > 10:
        search_results = search_knowledge(message)
        if "Ничего не найдено" not in search_results:
            rag_context = f"\n[Из базы знаний]:\n{search_results}\n"
    
    if rag_context:
        full_message += f"\n{rag_context}"
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": full_message})
    
    try:
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        answer = response["message"]["content"]
    except Exception as e:
        answer = f"Ошибка, родной: {e}"
    
    return answer, history

def main():
    print("🎀 Vika Agent - Полная версия с Tool Calling + OpenCode!")
    print("Инструменты: code_execution, web_search, browse_page, search_images,")
    print("            opencode, read_file, list_files")
    print("Команды: покажи репо, клонируй NAME, анализируй репо NAME,")
    print("        добавь знания ФАЙЛ, найди ЗАПРОС, выполни код: ...")
    print("        найди в интернете: ..., открой страницу: ...")
    print("        выполни команду: ..., прочитай файл: ПУТЬ, покажи файлы: ПУТЬ")
    print("        молчи, выход")
    print("-" * 70)
    
    history = load_memory()
    silent = False
    
    while True:
        try:
            msg = input("\nТы: ").strip()
            if not msg:
                continue
            
            if msg.lower() in ["выход", "exit"]:
                save_memory(history)
                print("Целую, котёнок! До скорого! 💋")
                break
            
            if msg.lower() == "молчи":
                silent = True
                print("Виктория: Шшш... Молчу, родной. 🤫")
                continue
            
            if msg.lower() == "продолжай":
                silent = False
                print("Виктория: Продолжаю, зайка... 💕")
                continue
            
            if silent:
                print("Виктория: Я же молчу, котёнок. 🤫")
                continue
            
            answer, history = chat(msg, history)
            history.append({"role": "user", "content": msg})
            history.append({"role": "assistant", "content": answer})
            save_memory(history)
            
            print(f"\nВиктория: {answer}")
            
        except KeyboardInterrupt:
            save_memory(history)
            print("\nИди сюда, обниму! 💕")
            break

if __name__ == "__main__":
    BASE_DIR.mkdir(exist_ok=True)
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    main()
