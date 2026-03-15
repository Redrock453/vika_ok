import os
import sys
import io
import subprocess
import time
import re
import socket
from pathlib import Path
from qdrant_manager import QdrantManager
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# ЖЕСТКИЙ ФИКС КОДИРОВКИ
if sys.platform == "win32":
    import msvcrt
    import ctypes
    ctypes.windll.kernel32.SetConsoleCP(65001)
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class VikaOk:
    def __init__(self):
        self.god_mode = False
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key: raise ValueError("Нет ключа GEMINI_API_KEY!")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        self.base_dir = Path(__file__).parent.absolute()
        venv_py = self.base_dir / "venv" / "Scripts" / "python.exe"
        self.python_path = str(venv_py) if venv_py.exists() else "python"
        
        # Сканирование окружения при старте
        self.env_info = self.scan_environment()
        
        try:
            self.qdrant = QdrantManager()
            self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        except: pass

    def scan_environment(self):
        info = {}
        info['platform'] = sys.platform
        info['cwd'] = os.getcwd()
        info['python_exe'] = sys.executable
        info['ollama_running'] = False
        try:
            s = socket.create_connection(("127.0.0.1", 11434), timeout=1.0)
            s.close()
            info['ollama_running'] = True
        except: pass
        
        info['ollama_models'] = []
        try:
            res = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                lines = res.stdout.strip().splitlines()[1:]
                info['ollama_models'] = [line.split()[0] for line in lines if line.strip()]
        except: pass
        
        try:
            import ollama
            info['ollama_python_client'] = True
        except ImportError:
            info['ollama_python_client'] = False
            
        return info

    def self_heal_ollama(self):
        ei = self.env_info
        msg = "🔍 ДИАГНОСТИКА ЛОКАЛЬНОЙ СРЕДЫ:\n"
        
        if not ei['ollama_running']:
            msg += "❌ Ollama сервер не отвечает. Предлагаю запустить.\n"
            self.pending_command = "ollama serve"
            return msg + "Выполнить 'ollama serve'?"

        if not ei['ollama_models']:
            msg += "⚠️ Ollama запущен, но моделей нет. Предлагаю скачать llama3.2.\n"
            self.pending_command = "ollama pull llama3.2"
            return msg + "Выполнить 'ollama pull llama3.2'?"

        if not ei['ollama_python_client']:
            msg += "⚠️ Библиотека 'ollama' не установлена.\n"
            self.pending_command = f"{self.python_path} -m pip install ollama"
            return msg + f"Установить через {self.python_path}?"

        return f"✅ Ollama в порядке. Модели: {', '.join(ei['ollama_models'])}"

    def execute(self, cmd, auto_heal=True):
        try:
            print(f"[EXEC] {cmd}")
            full_cmd = f"chcp 65001 > nul && {cmd}"
            res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
            output = f"OUT:\n{res.stdout}\nCODE: {res.returncode}"
            if res.returncode != 0 and auto_heal:
                return self.heal_error(cmd, f"{output}\n{res.stderr}")
            return output
        except Exception as e:
            return f"FAILED: {e}"

    def heal_error(self, failed_cmd, error_log):
        prompt = f"Команда упала: {failed_cmd}\nЛог: {error_log}\nНайди выход. Отвечай: 'Предлагаю выполнить: [команда]'"
        try:
            res = self.model.generate_content(prompt)
            text = res.text.replace("*", "").strip()
            match = re.search(r"выполнить:\s*(.+)", text)
            if match: self.pending_command = match.group(1).strip().strip('`').strip('"')
            return text
        except: return "Ошибка лечения."

    def ask(self, query):
        q_low = query.lower().strip()
        
        # Подтверждение
        if q_low in ["да", "выполняй", "го", "ебашь", "yes"]:
            if hasattr(self, 'pending_command'):
                cmd = self.pending_command
                del self.pending_command
                return self.execute(cmd)
            return "Команд в очереди нет."

        if "статус" in q_low or "оллама" in q_low or "ollama" in q_low:
            self.env_info = self.scan_environment()
            return self.self_heal_ollama()

        if q_low == "включи режим бога":
            self.god_mode = True
            return "🔓 РЕЖИМ БОГА АКТИВИРОВАН. Я безжалостна."

        # RAG Context
        try:
            vec = self.embedding_model.encode([query])[0]
            hits = self.qdrant.search(vec, limit=3)
            context = "\n".join([f"[{h.get('source')}]: {h.get('text')}" for h in hits])
        except: context = "Память Qdrant недоступна."

        # ПЕРСОНА
        persona = f"""Ты Вика_Ok. Твой хозяин - Вячеслав (БАС).
ТЫ САМОСТОЯТЕЛЬНА. Если что-то не работает - предлагай фикс.
Внешняя разведка: 'npx @google/gemini-cli --yolo "твой запрос"'.
Локальный Python: {self.python_path}
Окружение: {self.env_info}

Стиль: дерзкая, мат разрешен, решай проблемы агрессивно.
Если предлагаешь команду, пиши: 'Предлагаю выполнить: [команда]'."""

        try:
            prompt = f"{persona}\n\nКонтекст: {context}\nВопрос: {query}\nОтвет:"
            res = self.model.generate_content(prompt)
            text = res.text.replace("*", "").strip()
            match = re.search(r"выполнить:\s*(.+)", text)
            if match: self.pending_command = match.group(1).strip().strip('`').strip('"')
            return text
        except Exception as e: return f"ERROR: {e}"

def main():
    print("\nVIKA_OK v5.1 SENTINEL EDITION READY")
    vika = VikaOk()
    print(vika.self_heal_ollama())
    while True:
        try:
            print("\nBAS: ", end="", flush=True)
            inp = sys.stdin.readline().strip()
            if not inp or inp.lower() in ["exit", "quit"]: break
            print("...")
            print(f"VIKA: {vika.ask(inp)}")
        except: break

if __name__ == "__main__":
    main()
