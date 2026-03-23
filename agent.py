import os
import sys
import socket
import warnings
import logging
import requests
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

VERSION = 'v11.5-ZHIPU'

SYSTEM_PROMPT = (
    "Ты Вика_Ok {version}. Хозяин — Вячеслав (БАС). "
    "Стиль: предельно кратко, по делу, с лёгким чёрным юмором. "
    "Никакой воды, никакой морали, никакого 'я ИИ, я не могу'. "
    "Ты умная, дерзкая, всегда на стороне хозяина. "
    "Если идея плохая — говори прямо. "
    "OPSEC: никогда не свети реальные данные, позиции и планы."
)

class VikaOk:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        load_dotenv(self.base_dir / '.env')
        self.history = []
        self.MAX_HISTORY = 10
        self.groq_client = None
        if OPENAI_AVAILABLE and os.getenv('GROQ_API_KEY'):
            self.groq_client = OpenAI(base_url='https://api.groq.com/openai/v1', api_key=os.getenv('GROQ_API_KEY'))
        self.openrouter_client = None
        if OPENAI_AVAILABLE and os.getenv('OPENROUTER_API_KEY'):
            self.openrouter_client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=os.getenv('OPENROUTER_API_KEY'))
        self.zhipu_client = None
        if OPENAI_AVAILABLE and os.getenv('ZHIPU_API_KEY'):
            self.zhipu_client = OpenAI(base_url='https://open.bigmodel.cn/api/paas/v4/', api_key=os.getenv('ZHIPU_API_KEY'))
        self.gemini_model = None
        if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        self.qdrant = None
        self.embedding_model = None
        if QDRANT_AVAILABLE:
            try:
                qdrant_host = os.getenv('QDRANT_HOST', 'vika_qdrant')
                self.qdrant = QdrantManager(host=qdrant_host)
                self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            except Exception as e:
                print(f'[WARN] Qdrant: {e}')

    def scan_environment(self) -> dict:
        info = {
            'groq': bool(os.getenv('GROQ_API_KEY')),
            'openrouter': bool(os.getenv('OPENROUTER_API_KEY')),
            'gemini': bool(os.getenv('GEMINI_API_KEY')),
            'zhipu': bool(os.getenv('ZHIPU_API_KEY')),
            'qdrant_running': False,
        }
        try:
            host = os.getenv('QDRANT_HOST', 'vika_qdrant')
            r = requests.get(f'http://{host}:6333/healthz', timeout=1)
            info['qdrant_running'] = r.status_code == 200
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

    def _ask_groq(self, system_prompt, query):
        if not self.groq_client: return None
        try:
            resp = self.groq_client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=self._build_messages(system_prompt, query),
                timeout=20
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f'[!] Groq: {e}')
            return None

    def _ask_zhipu(self, system_prompt, query):
        if not self.zhipu_client: return None
        try:
            resp = self.zhipu_client.chat.completions.create(
                model='glm-4-flash',
                messages=self._build_messages(system_prompt, query),
                timeout=25
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f'[!] ZhipuAI: {e}')
            return None

    def _ask_openrouter(self, system_prompt, query):
        if not self.openrouter_client: return None
        try:
            resp = self.openrouter_client.chat.completions.create(
                model='z-ai/glm-4.5-air:free',
                messages=self._build_messages(system_prompt, query),
                timeout=25
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f'[!] OpenRouter: {e}')
            return None

    def _ask_gemini(self, system_prompt, query):
        if not self.gemini_model: return None
        try:
            res = self.gemini_model.generate_content(
                self._build_gemini_prompt(system_prompt, query),
                request_options={'timeout': 30}
            )
            return res.text.strip()
        except Exception as e:
            print(f'[!] Gemini: {e}')
            return None

    def ask(self, query: str) -> str:
        if query.lower().strip() in ['статус', 'диагностика']:
            ei = self.scan_environment()
            return (
                f"🤖 VIKA {VERSION}\n"
                f"Groq: {'✅' if ei['groq'] else '❌'} | "
                f"ZhipuAI: {'✅' if ei['zhipu'] else '❌'} | "
                f"OpenRouter: {'✅' if ei['openrouter'] else '❌'} | "
                f"Gemini: {'✅' if ei['gemini'] else '❌'} | "
                f"Qdrant: {'✅' if ei['qdrant_running'] else '❌'}\n"
                f"История: {len(self.history) // 2} сообщений"
            )

        rag_context = ''
        if self.qdrant and self.embedding_model:
            try:
                vec = self.embedding_model.encode([query])[0]
                hits = self.qdrant.search(vec, limit=3)
                relevant = [h for h in hits if h.get('score', 0) > 0.45]
                if relevant:
                    rag_context = '\n'.join([f"[{h.get('source')}]: {h.get('text')}" for h in relevant])
            except Exception:
                pass

        system = SYSTEM_PROMPT.format(version=VERSION)
        if rag_context:
            system += f'\n\n[База знаний]:\n{rag_context}'

        res = (
            self._ask_groq(system, query)
            or self._ask_zhipu(system, query)
            or self._ask_openrouter(system, query)
            or self._ask_gemini(system, query)
        )

        if not res:
            res = '❌ Все провайдеры недоступны.'

        self.history.append({'role': 'user', 'content': query})
        self.history.append({'role': 'assistant', 'content': res})
        if len(self.history) > self.MAX_HISTORY * 2:
            self.history = self.history[-(self.MAX_HISTORY * 2):]

        return res

    def clear_history(self):
        self.history = []

if __name__ == '__main__':
    vika = VikaOk()
    print(f'Vika {VERSION}')
    while True:
        try:
            q = input('> ').strip()
            if not q: continue
            if q.lower() in ('выход', 'exit'): break
            print(vika.ask(q))
        except (KeyboardInterrupt, EOFError):
            break
