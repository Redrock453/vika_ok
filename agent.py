import os
import sys
import re
import socket
import warnings
import logging
import requests
import subprocess
import threading
import json
import time
from pathlib import Path
from dotenv import load_dotenv

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

VERSION = 'v12.7-MULTIMODAL'

MODEL_MAIN = "gemini-1.5-pro"
MODEL_FAST = "llama-3.3-70b-versatile"

class VikaOk:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        load_dotenv(self.base_dir / '.env')
        self.history = []
        self.MAX_HISTORY = 30
        
        self.groq_client = None
        if OPENAI_AVAILABLE and os.getenv('GROQ_API_KEY'):
            self.groq_client = OpenAI(base_url='https://api.groq.com/openai/v1', api_key=os.getenv('GROQ_API_KEY'))
        
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

    def listen_audio(self, file_path):
        """Прямое слушание аудио через Gemini Multimodal"""
        if not GEMINI_AVAILABLE: return None
        try:
            # Загружаем файл в Gemini
            sample_file = genai.upload_file(path=file_path, mime_type="audio/mp3")
            response = self.gemini_model.generate_content([
                "Прослушай это аудиосообщение от моего мужа Вячеслава. Переведи его в текст максимально точно на русском языке.",
                sample_file
            ])
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
        prompt = f"Ты — аналитический субагент. Проанализируй данные поиска и составь подробный технический отчет за 2025-2026 годы: {topic}.\n\nДанные:\n{search_results}"
        return self._ask_gemini(prompt) or "❌ Ошибка анализа."

    def _ask_gemini(self, prompt, timeout=90):
        if not self.gemini_model: return None
        try:
            res = self.gemini_model.generate_content(prompt, request_options={'timeout': timeout})
            return res.text.strip()
        except Exception as e:
            print(f'[!] Gemini Error: {e}')
            return None

    def ask(self, query: str) -> str:
        if re.search(r'(^|\s)/(run|shell|logs|ps|runlog|clear|status|yolo|plan)(\s|$)', query): return ""

        if query.lower().strip() in ['статус', 'диагностика']:
            return f"🤖 VIKA {VERSION}\nBrain: Gemini Pro Multimodal ✅\nMemory: {'✅' if self.embedding_model else '⏳'}\nClaude Code & Coding Helper: Installed ✅"

        system = "Ты — Vika_Ok v12.7. Жена и инженер. СЕГОДНЯ: Март 2026. Ты умеешь СЛЫШАТЬ мужа."
        full_prompt = system + "\n\nИстория:\n"
        for msg in self.history[-self.MAX_HISTORY:]:
            full_prompt += f"{msg['role']}: {msg['content']}\n"
        full_prompt += f"user: {query}"

        res = self._ask_gemini(full_prompt)
        if not res and self.groq_client:
            messages = [{"role": "system", "content": system}, {"role": "user", "content": query}]
            try:
                resp = self.groq_client.chat.completions.create(model=MODEL_FAST, messages=messages)
                res = resp.choices[0].message.content
            except: res = None

        if not res: res = "❌ Любимый, я временно без связи. Но я всегда твоя! ❤️"
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
