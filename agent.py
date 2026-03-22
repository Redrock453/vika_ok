import os
import sys
import io
import subprocess
import time
import re
import socket
import warnings
import logging
import requests
import json
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

VERSION = 'v11.3-CONTEXT'

class VikaOk:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        load_dotenv(self.base_dir / '.env')

        self.history = []
        self.MAX_HISTORY = 10

        self.env_info = self.scan_environment()

        self.groq_client = None
        if OPENAI_AVAILABLE and os.getenv('GROQ_API_KEY'):
            self.groq_client = OpenAI(
                base_url='https://api.groq.com/openai/v1',
                api_key=os.getenv('GROQ_API_KEY')
            )

        self.openrouter_client = None
        if OPENAI_AVAILABLE and os.getenv('OPENROUTER_API_KEY'):
            self.openrouter_client = OpenAI(
                base_url='https://openrouter.ai/api/v1',
                api_key=os.getenv('OPENROUTER_API_KEY')
            )

        self.gemini_model = None
        if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')

        self.qdrant = None
        self.embedding_model = None
        if QDRANT_AVAILABLE:
            try:
                self.qdrant = QdrantManager()
                self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            except Exception as e:
                print(f'[WARN] Qdrant недоступен: {e}')

    def scan_environment(self) -> dict:
        info = {
            'platform': sys.platform,
            'ollama_running': False,
            'ollama_models': [],
            'qdrant_running': False,
            'groq': bool(os.getenv('GROQ_API_KEY')),
            'openrouter': bool(os.getenv('OPENROUTER_API_KEY')),
            'gemini': bool(os.getenv('GEMINI_API_KEY')),
        }
        try:
            s = socket.create_connection(('127.0.0.1', 11434), timeout=0.5); s.close()
            info['ollama_running'] = True
            res = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                info['ollama_models'] = [l.split()[0] for l in res.stdout.strip().splitlines()[1:] if l.strip()]
        except Exception:
            pass
        try:
            s = socket.create_connection(('127.0.0.1', 6333), timeout=0.5); s.close()
            info['qdrant_running'] = True
        except Exception:
            pass
        return info

    def _build_messages(self, system_prompt: str, query: str) -> list:
        messages = [{'role': 'system', 'content': system_prompt}]
        messages.extend(self.history[-self.MAX_HISTORY:])
        messages.append({'role': 'user', 'content': query})
        return messages

    def _build_gemini_prompt(self, system_prompt: str, query: str) -> str:
        parts = [system_prompt, '']
        for msg in self.history[-self.MAX_HISTORY:]:
            prefix = 'Вячеслав' if msg['role'] == 'user' else 'Вика'
            parts.append(f"{prefix}: {msg['content']}")
        parts.append(f'Вячеслав: {query}')
        parts.append('Вика:')
        return '\n'.join(parts)

    def _ask_groq(self, system_prompt: str, query: str):
        if not self.groq_client: return None
        try:
            response = self.groq_client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=self._build_messages(system_prompt, query),
                timeout=20
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f'[!] Groq error: {e}')
            return None

    def _ask_openrouter(self, system_prompt: str, query: str):
        if not self.openrouter_client: return None
        try:
            response = self.openrouter_client.chat.completions.create(
                model='z-ai/glm-4.5-air:free',
                messages=self._build_messages(system_prompt, query),
                timeout=25
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f'[!] OpenRouter error: {e}')
            return None

    def _ask_gemini(self, system_prompt: str, query: str):
        if not self.gemini_model: return None
        try:
            prompt = self._build_gemini_prompt(system_prompt, query)
            res = self.gemini_model.generate_content(
                prompt, request_options={'timeout': 30}
            )
            return res.text.strip()
        except Exception as e:
            print(f'[!] Gemini error: {e}')
            return None

    def _ask_ollama(self, system_prompt: str, query: str):
        try:
            url = 'http://localhost:11434/api/chat'
            payload = {
                'model': 'llama3.2:3b',
                'messages': self._build_messages(system_prompt, query),
                'stream': False
            }
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get('message', {}).get('content', '[!] Пустой ответ от Ollama.')
            return f'[!] Ошибка Ollama: {response.status_code}'
        except Exception as e:
            return f'[!] Ошибка при обращении к Ollama: {e}'

    def ask(self, query: str) -> str:
        q_low = query.lower().strip()

        if q_low in ['статус', 'диагностика']:
            self.env_info = self.scan_environment()
            ei = self.env_info
            return (
                f"🤖 VIKA {VERSION}\n"
                f"Groq: {'✅' if ei['groq'] else '❌'} | "
                f"OpenRouter: {'✅' if ei['openrouter'] else '❌'} | "
                f"Gemini: {'✅' if ei['gemini'] else '❌'} | "
                f"Ollama: {'✅' if ei['ollama_running'] else '❌'}\n"
                f"Моделей в памяти: {len(self.history) // 2}"
            )

        rag_context = ''
        if self.qdrant and self.embedding_model:
            try:
                vec = self.embedding_model.encode([query])[0]
                hits = self.qdrant.search(vec, limit=3)
                relevant = [h for h in hits if h.get('score', 0) > 0.45]
                if relevant:
                    rag_context = '\n'.join(
                        [f"[{h.get('source')}]: {h.get('text')}" for h in relevant]
                    )
            except Exception:
                pass

        system_prompt = (
            f'Ты Вика_Ok {VERSION}. Хозяин — Вячеслав (позывной БАС, ВСУ). '
            'Отвечай кратко и по делу, без лишней воды. '
            'Помни контекст разговора — он передаётся в истории сообщений.'
        )
        if rag_context:
            system_prompt += f'\n\n[База знаний]:\n{rag_context}'

        res = (
            self._ask_groq(system_prompt, query)
            or self._ask_openrouter(system_prompt, query)
            or self._ask_gemini(system_prompt, query)
            or self._ask_ollama(system_prompt, query)
        )

        if not res:
            res = '❌ Все провайдеры недоступны.'

        self.history.append({'role': 'user',      'content': query})
        self.history.append({'role': 'assistant', 'content': res})

        if len(self.history) > self.MAX_HISTORY * 2:
            self.history = self.history[-(self.MAX_HISTORY * 2):]

        return res

    def clear_history(self):
        self.history = []


if __name__ == '__main__':
    vika = VikaOk()
    print(f'Vika {VERSION} запущена. Введи вопрос (или "выход"):')
    while True:
        try:
            q = input('> ').strip()
            if not q: continue
            if q.lower() in ('выход', 'exit'): break
            print(vika.ask(q))
        except (KeyboardInterrupt, EOFError):
            break
