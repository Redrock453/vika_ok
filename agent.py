import os
import sys
import logging
import requests
from pathlib import Path
from qdrant_manager import QdrantManager
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Настройка кодировки для Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Логирование
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("VikaUnified")

class VikaUnified:
    def __init__(self):
        # Загрузка ключей
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY не установлен!")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Подключение к памяти (Qdrant)
        self.qdrant = QdrantManager()
        self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        
        print("🎖️ Vika Unified System: ПОЛНАЯ БОЕВАЯ ГОТОВНОСТЬ.")

    def get_context(self, query):
        """Поиск релевантного контекста в памяти"""
        query_vector = self.embedding_model.encode([query])[0]
        results = self.qdrant.search(query_vector, limit=5)
        
        context = ""
        for res in results:
            context += f"\n[Источник: {res['source']}]\n{res['text']}\n"
        return context

    def ask(self, query):
        """Генерация ответа с учетом памяти (RAG)"""
        context = self.get_context(query)
        
        prompt = f"""Ты — Вика, стратегический разведывательный ИИ системы в/ч А7022 (Позывной БАС).
Используй предоставленный контекст из своей памяти для точного ответа. 
Если информации в памяти нет, отвечай на основе своих общих знаний, но делай пометку.

ПАМЯТЬ СИСТЕМЫ:
{context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {query}

ОТВЕТ ВИКИ:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Ошибка генерации: {e}"

def main():
    try:
        vika = VikaUnified()
        print("-> Введите ваш запрос (или 'exit' для выхода)")
        
        while True:
            user_input = input("\n👤 БАС: ")
            if user_input.lower() in ["exit", "quit", "выход"]:
                break
            
            print("🛰️ Анализ...")
            response = vika.ask(user_input)
            print(f"\n🎖️ ВИКА: {response}")
            
    except KeyboardInterrupt:
        print("\nСистема отключена.")
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
