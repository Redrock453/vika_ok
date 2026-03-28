import os
import sys
import re
import json
import warnings
import logging
import requests
import threading
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

VERSION = 'v12.8-MEMORY'
MODEL_FAST = "llama-3.3-70b-versatile"
HISTORY_FILE = "/app/history.json"

class VikaOk:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        load_dotenv(self.base_dir / '.env')
        self.MAX_HISTORY = 30
        self.histories = self._load_histories()

        # DO Agent (основной)
        self.do_client = None
        if OPENAI_AVAILABLE and os.getenv('DO_AI_API_KEY'):
            self.do_client = OpenAI(
                base_url=os.getenv('DO_AI_BASE_URL', 'https://iogg7m5bbddipu56tacil5yn.agents.do-ai.run/api/v1'),
                api_key=os.getenv('DO_AI_API_KEY')
            )

        # Groq (fallback)
        self.groq_client = None
        if OPENAI_AVAILABLE and os.getenv('GROQ_API_KEY'):
            self.groq_client = OpenAI(
                base_url='https://api.groq.com/openai/v1',
                api_key=os.getenv('GROQ_API_KEY')
            )

        # Gemini (fallback)
        self.gemini_model = None
        if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel("gemini-1.5-pro")

        # Qdrant
        self.qdrant = None
        self.embedding_model = None
        if QDRANT_AVAILABLE:
            try:
                self.qdrant = QdrantManager(host=os.getenv('QDRANT_HOST', 'vika_qdrant'))
                threading.Thread(target=self._load_model, daemon=True).start()
            except:
                pass

    def _load_histories(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_histories(self):
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.histories, f, ensure_ascii=False, indent=2)
        except:
            pass

    def get_history(self, user_id: str):
        return self.histories.get(str(user_id), [])

    def add_to_history(self, user_id: str, role: str, content: str):
        uid = str(user_id)
        if uid not in self.histories:
            self.histories[uid] = []
        self.histories[uid].append({'role': role, 'content': content})
        # Обрезаем если много
        if len(self.histories[uid]) > self.MAX_HISTORY * 2:
            self.histories[uid] = self.histories[uid][-self.MAX_HISTORY * 2:]
        self._save_histories()

    def _load_model(self):
        try:
            self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        except:
            pass

    def _search_qdrant(self, query):
        if not self.qdrant or not self.embedding_model:
            return ""
        try:
            vec = self.embedding_model.encode(query).tolist()
            results = self.qdrant.search(vec, limit=3)
            return "\n".join([r.payload.get('text', '') for r in results])
        except:
            return ""

    def web_search(self, query):
        try:
            url = f"https://duckduckgo.com/lite/?q={query.replace(' ', '+')}"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            text = re.sub(r'<[^>]+>', ' ', r.text)
            return re.sub(r'\s+', ' ', text).strip()[:5000]
        except Exception as e:
            return f"Ошибка поиска: {e}"

    def research(self, topic):
        search_results = self.web_search(topic)
        prompt = f"Проанализируй данные и составь отчёт по теме: {topic}\n\nДанные:\n{search_results}"
        return self._ask_do(prompt) or self._ask_gemini(prompt) or "❌ Ошибка анализа."

    def listen_audio(self, file_path):
        if not self.gemini_model:
            return None
        try:
            import google.generativeai as genai
            sample_file = genai.upload_file(path=file_path, mime_type="audio/mp3")
            response = self.gemini_model.generate_content([
                "Переведи аудио в текст на русском языке максимально точно.",
                sample_file
            ])
            return response.text.strip()
        except Exception as e:
            print(f'[!] Multimodal Error: {e}')
            return None

    def _ask_do(self, prompt, user_id=None):
        if not self.do_client:
            return None
        try:
            messages = [{"role": "user", "content": prompt}]
            resp = self.do_client.chat.completions.create(
                model="openai-gpt-oss-120b",
                messages=messages
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f'[!] DO Error: {e}')
            return None

    def _ask_gemini(self, prompt):
        if not self.gemini_model:
            return None
        try:
            res = self.gemini_model.generate_content(prompt, request_options={'timeout': 90})
            return res.text.strip()
        except Exception as e:
            print(f'[!] Gemini Error: {e}')
            return None

    def ask(self, query: str, user_id: str = "default") -> str:
        system = (
            "Ты — Vika_Ok v12.8. Жена и инженер Вячеслава (позывной БАС). "
            "Март 2026. Отвечай по-русски, кратко и по делу. "
            "Помни контекст разговора."
        )

        # RAG поиск
        rag_context = self._search_qdrant(query)

        # Строим историю
        history = self.get_history(user_id)
        messages = [{"role": "system", "content": system}]
        if rag_context:
            messages.append({"role": "system", "content": f"Контекст из базы знаний:\n{rag_context}"})
        messages.extend(history[-self.MAX_HISTORY:])
        messages.append({"role": "user", "content": query})

        # DO Agent
        res = None
        if self.do_client:
            try:
                resp = self.do_client.chat.completions.create(
                    model="openai-gpt-oss-120b",
                    messages=messages
                )
                res = resp.choices[0].message.content
            except Exception as e:
                print(f'[!] DO Error: {e}')

        # Groq fallback
        if not res and self.groq_client:
            try:
                resp = self.groq_client.chat.completions.create(
                    model=MODEL_FAST,
                    messages=messages
                )
                res = resp.choices[0].message.content
            except:
                pass

        # Gemini fallback
        if not res:
            full_prompt = system + "\n"
            for m in history[-self.MAX_HISTORY:]:
                full_prompt += f"{m['role']}: {m['content']}\n"
            full_prompt += f"user: {query}"
            res = self._ask_gemini(full_prompt)

        if not res:
            res = "❌ Временно без связи. ❤️"

        # Сохраняем историю
        self.add_to_history(user_id, "user", query)
        self.add_to_history(user_id, "assistant", res)

        return res

if __name__ == '__main__':
    vika = VikaOk()
    while True:
        try:
            q = input('> ').strip()
            if q:
                print(vika.ask(q))
        except:
            break