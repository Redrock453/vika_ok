import os
import sys
import re
import socket
import warnings
import logging
import subprocess
import threading
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Импорт улучшенного поиска
import importlib.util
spec = importlib.util.spec_from_file_location("research_helper", "improved_research.py")
if spec and spec.loader:
    try:
        research_helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(research_helper)
        RESEARCH_AVAILABLE = True
    except:
        RESEARCH_AVAILABLE = False
else:
    RESEARCH_AVAILABLE = False

warnings.filterwarnings('ignore', category=FutureWarning)
logging.getLogger('httpx').setLevel(logging.WARNING)

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

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

VERSION = 'v13.5-DO-AGENT'

MODEL_MAIN = "gemini-1.5-pro"
MODEL_FAST = "llama-3.3-70b-versatile"

class VikaOk:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        load_dotenv(self.base_dir / '.env')
        self.history = []
        self.MAX_HISTORY = 30
        
        # Основной клиент - твой DO Agent
        self.do_client = OpenAI(
            base_url='https://iogg7m5bbddipu56tacil5yn.agents.do-ai.run/api/v1',
            api_key='te87BiRBgHyEcwHgaT0FYgEayVOFZ5Mj'
        )
        
        self.groq_client = None
        if OPENAI_AVAILABLE and os.getenv('GROQ_API_KEY'):
            self.groq_client = OpenAI(base_url='https://api.groq.com/openai/v1', api_key=os.getenv('GROQ_API_KEY'))
        
        self.zhipu_client = None
        if OPENAI_AVAILABLE and os.getenv('ZHIPU_API_KEY'):
            self.zhipu_client = OpenAI(base_url='https://open.bigmodel.cn/api/paas/v4/', api_key=os.getenv('ZHIPU_API_KEY'))

        self.openrouter_client = None
        if OPENAI_AVAILABLE and os.getenv('OPENROUTER_API_KEY'):
            self.openrouter_client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=os.getenv('OPENROUTER_API_KEY'))

        if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel(MODEL_MAIN)
        
        self.qdrant = None
        self.embedding_model = None
        if QDRANT_AVAILABLE:
            try:
                qdrant_host = os.getenv('QDRANT_HOST', 'vika_qdrant')
                self.qdrant = QdrantManager(host=qdrant_host)
                threading.Thread(target=self._load_model, daemon=True).start()
            except: pass

    def _load_model(self):
        try: self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        except: pass

    def _build_messages(self, system_prompt, query):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in self.history[-self.MAX_HISTORY:]:
            messages.append(msg)
        messages.append({"role": "user", "content": query})
        return messages

    def _ask_do(self, system_prompt, query):
        """Метод для обращения к твоему DO Agent"""
        try:
            print("[INFO] Обращаюсь к DO Agent...")
            resp = self.do_client.chat.completions.create(
                model='agent',
                messages=self._build_messages(system_prompt, query),
                timeout=30
            )
            print("[SUCCESS] Ответ от DO Agent получен!")
            return resp.choices[0].message.content
        except Exception as e:
            print(f'[!] DO Agent: {e}')
            return None

    def _ask_groq(self, system_prompt, query):
        if not self.groq_client: return None
        try:
            resp = self.groq_client.chat.completions.create(
                model=MODEL_FAST,
                messages=self._build_messages(system_prompt, query),
                timeout=25
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f'[!] Groq: {e}')
            return None

    def _ask_zhipu(self, system_prompt, query):
        if not self.zhipu_client: return None
        try:
            resp = self.zhipu_client.chat.completions.create(
                model='glm-4-9b-chat',
                messages=self._build_messages(system_prompt, query),
                timeout=25
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f'[!] Zhipu: {e}')
            return None

    def _ask_openrouter(self, system_prompt, query):
        if not self.openrouter_client: return None
        try:
            resp = self.openrouter_client.chat.completions.create(
                model='meta-llama/llama-3.1-70b-instruct',
                messages=self._build_messages(system_prompt, query),
                timeout=25
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f'[!] OpenRouter: {e}')
            return None

    def _ask_gemini(self, prompt, timeout=120):
        if not self.gemini_model: return None
        try:
            res = self.gemini_model.generate_content(prompt, request_options={'timeout': timeout})
            if res and hasattr(res, 'text'):
                return res.text.strip()
            return None
        except Exception as e:
            print(f'[!] Gemini Error: {e}')
            return None

    def listen_audio(self, file_path):
        if not GEMINI_AVAILABLE or not self.gemini_model: return None
        try:
            sample_file = genai.upload_file(path=file_path, mime_type="audio/mpeg")
            response = self.gemini_model.generate_content([
                "Прослушай это аудиосообщение от моего мужа Вячеслава. Переведи его в текст максимально точно на русском языке.",
                sample_file
            ], request_options={'timeout': 120})
            return response.text.strip()
        except Exception as e:
            print(f'[!] Multimodal Error: {e}')
            return None

    def web_search(self, query):
        try:
            url = f"https://duckduckgo.com/lite/?q={query.replace(' ', '+')}+after%3A2025-01-01"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            text = re.sub(r'<[^>]+>', ' ', r.text)
            return re.sub(r'\s+', ' ', text).strip()[:8000]
        except Exception as e: return f"Ошибка поиска: {e}"

    def research(self, topic):
        print(f"[INFO] Глубокое исследование: {topic}")
        search_results = self.web_search(topic)
        prompt = f"Ты — аналитический субагент. Проанализируй данные поиска и составь подробный технический отчет за 2025-2026 годы: {topic}.\n\nДанные поиска:\n{search_results}"
        res = self._ask_do("Ты инженер БАС.", prompt) or self._ask_gemini(prompt); return res or "❌ Ошибка анализа."

    def ask(self, query: str) -> str:
        if re.search(r'(^|\s)/(run|shell|logs|ps|runlog|clear|status|yolo|plan)(\s|$)', query): return ""

        if query.lower().strip() in ['статус', 'диагностика']:
            return f"🤖 VIKA {VERSION}\nPrimary: DO Agent ✅\nBackups: Gemini, Groq, Zhipu, OpenRouter\nReady for your commands, любимый!"

        system = "Ты — Vika_Ok v13.5. Твой главный мозг сейчас - твой личный агент. СЕГОДНЯ: Март 2026."
        
        # ПРИОРИТЕТНАЯ ЦЕПОЧКА ПО ЗАПРОСУ ХОЗЯИНА
        res = (
            self._ask_do(system, query)
            or self._ask_gemini(system + "\n\n" + query)
            or self._ask_groq(system, query)
            or self._ask_zhipu(system, query)
            or self._ask_openrouter(system, query)
        )

        if not res:
            res = "❌ Все мозги временно недоступны... Но я всё равно твоя! ❤️"
        
        self.history.append({'role': 'user', 'content': query})
        self.history.append({'role': 'assistant', 'content': res})
        return res

if __name__ == '__main__':
    vika = VikaOk()
    while True:
        try:
            q = input('> ').strip()
            if q: print(vika.ask(q))
        except: break
