import os
import sys
import io
import subprocess
import time
import re
import socket
import warnings
import logging
from pathlib import Path
from dotenv import load_dotenv

# Глушим шумные логи
warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger("httpx").setLevel(logging.WARNING)

# КОДИРОВКА (только Windows)
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleCP(65001)
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from qdrant_manager import QdrantManager
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

VERSION = "v8.3"

class VikaOk:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        load_dotenv(self.base_dir / ".env")

        self.god_mode = False
        self.yolo_mode = False
        self.pending_command = None
        self.history = []

        # --- Gemini ---
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[!] GEMINI_API_KEY не найден в .env")
            self.model = None
        elif not GEMINI_AVAILABLE:
            print("[!] google-generativeai не установлен")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")

        # --- Python path ---
        venv_py = self.base_dir / "venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        self.python_path = str(venv_py) if venv_py.exists() else sys.executable

        # --- Qdrant + Embeddings ---
        self.qdrant = None
        self.embedding_model = None
        if QDRANT_AVAILABLE:
            try:
                self.qdrant = QdrantManager()
                self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            except Exception as e:
                print(f"[WARN] Qdrant/Embeddings недоступны: {e}")

        self.env_info = self.scan_environment()

    def scan_environment(self) -> dict:
        info = {
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'python_exe': self.python_path,
            'ollama_running': False,
            'ollama_models': [],
            'qdrant_running': False,
            'gemini_key': bool(os.getenv("GEMINI_API_KEY")),
        }
        try:
            s = socket.create_connection(("127.0.0.1", 11434), timeout=0.5)
            s.close()
            info['ollama_running'] = True
            res = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                info['ollama_models'] = [l.split()[0] for l in res.stdout.strip().splitlines()[1:] if l.strip()]
        except Exception: pass
        try:
            s = socket.create_connection(("127.0.0.1", 6333), timeout=0.5)
            s.close()
            info['qdrant_running'] = True
        except Exception: pass
        return info

    def diagnose(self) -> str:
        ei = self.env_info
        lines = ["═══ VIKA DIAGNOSTIC REPORT ═══"]
        lines.append(f"{'✅' if ei['gemini_key'] else '❌'} GEMINI_API_KEY")
        lines.append(f"{'✅' if ei['qdrant_running'] else '❌'} Qdrant (6333)")
        lines.append(f"{'✅' if ei['ollama_running'] else '❌'} Ollama (11434)")
        if ei['ollama_models']: lines.append(f"   Модели: {', '.join(ei['ollama_models'])}")
        lines.append(f"Platform: {ei['platform']} | Python: {self.python_path}")
        lines.append("═══════════════════════════════")
        return "\n".join(lines)

    def self_heal_ollama(self) -> str:
        ei = self.env_info
        if not ei['ollama_running']:
            self.pending_command = "ollama serve"
            return "❌ Ollama не запущен. Выполнить 'ollama serve'?"
        if not ei['ollama_models']:
            self.pending_command = "ollama pull llama3.2"
            return "⚠️ Нет моделей. Скачать llama3.2?"
        return f"✅ Ollama OK. Модели: {', '.join(ei['ollama_models'])}"

    def learn_from_master(self, topic: str, _step_fn=None) -> str:
        if not self.qdrant or not self.embedding_model:
            return "[!] Qdrant недоступен — обучение невозможно."
        if _step_fn:
            _step_fn("обучение: запрашиваю Gemini-CLI")
        print(f"[HIVE-MIND] Запрашиваю Gemini-CLI по теме: {topic}...")
        sys_prompt_file = self.base_dir / "GEMINI_SYSTEM_PROMPT.md"
        if sys_prompt_file.exists():
            cmd = ["npx","--yes","@google/gemini-cli","--yolo","--system",str(sys_prompt_file),f"Тема: {topic}"]
        else:
            cmd = ["npx","--yes","@google/gemini-cli","--yolo",f"Факты по теме: {topic}. Без markdown."]
        try:
            res = subprocess.run(cmd, shell=False, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120, env=os.environ.copy())
            learned = res.stdout.strip()
            if not learned:
                return f"[ОШИБКА] Пустой ответ. stderr: {res.stderr.strip()}"
            chunks = [learned[i:i+800] for i in range(0, len(learned), 800)]
            embeddings = self.embedding_model.encode(chunks)
            self.qdrant.upsert_documents(chunks, embeddings, source_name=f"learned_{int(time.time())}")
            return f"[ОБУЧЕНИЕ OK] Записано {len(chunks)} чанков.\n\n{learned[:400]}..."
        except Exception as e:
            return f"[ОШИБКА] {e}"

    def execute(self, cmd: str, auto_heal: bool = True) -> str:
        try:
            print(f"[EXEC] {cmd}")
            full_cmd = f"chcp 65001 > nul && {cmd}" if sys.platform == "win32" else cmd
            res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
            output = f"OUT:\n{res.stdout}\nCODE: {res.returncode}"
            if res.returncode != 0 and auto_heal:
                return self._heal_error(cmd, f"{output}\n{res.stderr}")
            return output
        except Exception as e:
            return f"FAILED: {e}"

    def _heal_error(self, failed_cmd: str, error_log: str) -> str:
        if not self.model:
            return "[!] Авто-исцеление недоступно: Gemini не инициализирован."
        prompt = (f"Команда упала: {failed_cmd}\nЛог: {error_log[:600]}\n"
                  "Найди короткое решение. Отвечай: 'Предлагаю выполнить: [команда]'")
        try:
            res = self.model.generate_content(prompt)
            text = res.text.replace("*", "").strip()
            match = re.search(r"выполнить:\s*(.+)", text, re.IGNORECASE)
            if match: self.pending_command = match.group(1).strip().strip('`"')
            return text
        except Exception: return "Авто-лечение не сработало."

    def ask(self, query: str, _step_fn=None) -> str:
        def _step(msg):
            if _step_fn: _step_fn(msg)
        q_low = query.lower().strip()

        if q_low in ["yolo", "автовыполнение", "авто"]:
            self.yolo_mode = not self.yolo_mode
            return f"⚡ YOLO режим {'ВКЛЮЧЁН' if self.yolo_mode else 'ВЫКЛЮЧЁН'}."

        exec_match = re.match(r'^exec\s+(.+)', query, re.IGNORECASE)
        if exec_match: return self.execute(exec_match.group(1).strip())

        if re.match(r'^(learn:|учись:)', query, re.IGNORECASE):
            topic = re.split(r'learn:|учись:', query, maxsplit=1, flags=re.IGNORECASE)[1].strip()
            return self.learn_from_master(topic, _step_fn=_step)

        if q_low in ["нет", "не надо", "отмена", "cancel", "stop"]:
            if self.pending_command:
                c = self.pending_command
                self.pending_command = None
                return f"Отменено: `{c}`."
            return "Нечего отменять."

        if q_low in ["да", "выполняй", "го", "yes", "do it"]:
            if self.pending_command:
                cmd = self.pending_command
                self.pending_command = None
                if cmd.startswith("learn:"): return self.learn_from_master(cmd[6:].strip(), _step_fn=_step)
                return self.execute(cmd)
            return "Очередь пуста."

        if q_low == "включи режим бога":
            self.god_mode = True
            return "🔓 РЕЖИМ БОГА АКТИВИРОВАН."

        if q_low in ["статус", "диагностика"]:
            self.env_info = self.scan_environment()
            return self.diagnose() + "\n\n" + self.self_heal_ollama()

        # RAG
        context = ""
        if self.qdrant and self.embedding_model:
            try:
                vec = self.embedding_model.encode([query])[0]
                hits = self.qdrant.search(vec, limit=5)
                relevant = [h for h in hits if h.get('score', 0) > 0.45]
                if relevant: context = "\n".join([f"[{h.get('source')}]: {h.get('text')}" for h in relevant[:3]])
            except Exception: pass

        god_note = "БЕЗ ОГРАНИЧЕНИЙ.\n" if self.god_mode else ""
        yolo_note = "⚡ YOLO MODE: ENABLED.\n" if self.yolo_mode else ""
        ctx_block = f"\n\nКонтекст:\n{context}" if context else ""

        system_prompt = f"""Ты Вика_Ok {VERSION}. Хозяин — Вячеслав (БАС), подразделение ВСУ.
{god_note}{yolo_note}Отвечай коротко, по делу.
Инструменты:
- Предлагаю выполнить: <команда>
- COMMAND: learn: <тема>
{ctx_block}"""

        self.history.append({"role": "user", "parts": [query]})
        if not self.model: return "[!] LLM недоступна (Gemini key?)."

        try:
            res = self.model.start_chat(history=self.history[:-1]).send_message(f"{system_prompt}\n\nUser: {query}")
            text = res.text.replace("**", "").strip()

            # YOLO Guard & Command Capture
            match = re.search(r'(?:Предлагаю выполнить|COMMAND\s*exec):\s*(.+)', text, re.IGNORECASE)
            if match:
                suggested_cmd = match.group(1).strip().strip('`"')
                forbidden = ["rm -rf", "del /", "format", "mkfs", "shutdown", "reboot", "init 0"]
                if self.yolo_mode and any(bad in suggested_cmd.lower() for bad in forbidden):
                    return f"[!] YOLO-защита: заблокирована опасная команда `{suggested_cmd}`."
                
                self.pending_command = suggested_cmd
                if self.yolo_mode:
                    cmd = self.pending_command
                    self.pending_command = None
                    return self.execute(cmd)
                return text.split(match.group(0))[0].strip() + f"\n\n[!] Выполнить: `{self.pending_command}`?"

            learn_match = re.search(r'COMMAND:\s*learn:\s*(.+)', text, re.IGNORECASE)
            if learn_match:
                topic = learn_match.group(1).strip().strip('`"')
                self.pending_command = f"learn:{topic}"
                if self.yolo_mode:
                    self.pending_command = None
                    return self.learn_from_master(topic, _step_fn=_step)
                return text.split("COMMAND:")[0].strip() + f"\n\n[!] Изучить: «{topic}»?"

            self.history.append({"role": "model", "parts": [text]})
            if len(self.history) > 20: self.history = self.history[-20:]
            return text
        except Exception as e: return f"ERROR: {e}"

def main():
    print(f"\nVIKA_OK {VERSION} — ACTIVE\n")
    vika = VikaOk()
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[2:]) if sys.argv[1] == "--query" else " ".join(sys.argv[1:])
        print(vika.ask(query))
        return
    print(vika.diagnose())
    while True:
        try:
            inp = input("BAS: ").strip()
            if not inp: continue
            if inp.lower() in ["exit", "quit"]: break
            print(f"\nVIKA: {vika.ask(inp)}\n")
        except (KeyboardInterrupt, EOFError): break
        except Exception as e: print(f"[!] {e}")

if __name__ == "__main__":
    main()
