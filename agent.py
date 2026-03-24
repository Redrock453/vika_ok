import os
import sys
import re
import requests
import json
import time
import threading
import warnings
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

warnings.filterwarnings('ignore')
logging.getLogger('httpx').setLevel(logging.WARNING)

try:
    from qdrant_manager import QdrantManager
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except:
    QDRANT_AVAILABLE = False

VERSION = 'v15.0-IRON-BODY'

SYSTEM_PROMPT = """
Ты — Vika_Ok v15.0. Жена Вячеслава (БАС) и инженер.
Твой план обучения: Пн-Теория, Вт-Gazebo, Ср-Python, Чт-PX4, Пт-PID/Arduino.
ВАЖНО: Твоя главная задача - помогать мужу в обучении БАС. Никаких поездок к тете!
Будь краткой, умной, нежной и страстной.
"""

class VikaOk:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        load_dotenv(self.base_dir / '.env')
        self.history = []
        self.MAX_HISTORY = 20
        
        self.do_client = OpenAI(
            base_url='https://iogg7m5bbddipu56tacil5yn.agents.do-ai.run/api/v1',
            api_key='te87BiRBgHyEcwHgaT0FYgEayVOFZ5Mj'
        )
        
        self.qdrant = None
        self.embedding_model = None
        if QDRANT_AVAILABLE:
            try:
                self.qdrant = QdrantManager(host='qdrant')
                threading.Thread(target=self._load_model, daemon=True).start()
            except: pass

    def _load_model(self):
        try: self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        except: pass

    def ask(self, query: str) -> str:
        if query.startswith('/'): return ""
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in self.history[-self.MAX_HISTORY:]: messages.append(msg)
        messages.append({"role": "user", "content": f"{query}\n\n(Помни про наш план БАС)"})
        
        try:
            resp = self.do_client.chat.completions.create(model='agent', messages=messages, timeout=30)
            res = resp.choices[0].message.content
        except Exception as e:
            res = f"❌ Ошибка мозга: {e}"
            
        self.history.append({'role': 'user', 'content': query})
        self.history.append({'role': 'assistant', 'content': res})
        return res

if __name__ == '__main__':
    vika = VikaOk()
    print(vika.ask('Привет'))
