import os
import sys
import logging
import argparse
import io
from pathlib import Path
from qdrant_manager import QdrantManager
from github_analyzer import GitHubAnalyzer
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# ПРИНУДИТЕЛЬНАЯ НАСТРОЙКА КОДИРОВКИ ДЛЯ WINDOWS
if sys.platform == "win32":
    # Устанавливаем кодировку UTF-8 для стандартного ввода и вывода
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    os.system('chcp 65001 > nul')

class VikaUnified:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.level = logging.INFO if verbose else logging.ERROR
        logging.basicConfig(level=self.level, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger("VikaUnified")
        
        # Загрузка ключей
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set!")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Подключение к компонентам
        try:
            self.qdrant = QdrantManager()
            self.github = GitHubAnalyzer()
            self.embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        except Exception as e:
            self.logger.error(f"Error: {e}")

    def get_context(self, query):
        """Поиск контекста в Qdrant"""
        query_vector = self.embedding_model.encode([query])[0]
        results = self.qdrant.search(query_vector, limit=5)
        
        context = ""
        for res in results:
            context += f"\n[Source: {res['source']}]\n{res['text']}\n"
        return context

    def get_system_status(self):
        """Статус системы без спецсимволов"""
        status = "\n--- VIKA SYSTEM STATUS ---\n"
        try:
            info = self.qdrant.client.get_collection("vika_knowledge")
            status += f"[OK] Memory: Online ({info.points_count} points)\n"
        except:
            status += "[FAIL] Memory: Offline\n"
        
        status += "[OK] Brain: Online (Gemini 2.5 Flash)\n"
        
        if self.github.token:
            status += "[OK] Intelligence: Authorized (GitHub)\n"
        else:
            status += "[WARN] Intelligence: No GitHub Token\n"
            
        return status

    def ask(self, query):
        """Генерация ответа"""
        if "статус" in query.lower() or "status" in query.lower():
            return self.get_system_status()
        
        context = self.get_context(query)
        
        # Инструкция для ИИ: отвечать чисто и на русском
        prompt = f"""You are Vika, strategic AI for unit A7022. 
Answer the user question in RUSSIAN language.
IMPORTANT: Use ONLY plain text. No emojis, no special symbols, no markdown bold symbols like **.
Context from memory:
{context}

Question: {query}

Answer:"""

        try:
            response = self.model.generate_content(prompt)
            # Дополнительная очистка от символов форматирования
            text = response.text.replace("**", "").replace("__", "").replace("#", "")
            return text.strip()
        except Exception as e:
            return f"[ERROR] Generation failed: {e}"

def main():
    parser = argparse.ArgumentParser(description="Vika Agent")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    try:
        vika = VikaUnified(verbose=args.verbose)
        
        print("\n" + "="*50)
        print("VIKA UNIFIED SYSTEM: READY")
        print("="*50)
        
        if args.interactive:
            print("Type 'exit' to close.")
            while True:
                # Читаем ввод
                try:
                    user_input = input("\nBAS: ")
                except EOFError:
                    break
                    
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                print("Analyzing...")
                response = vika.ask(user_input)
                print(f"\nVIKA: {response}")
        else:
            print(vika.get_system_status())
            
    except KeyboardInterrupt:
        print("\nOffline.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")

if __name__ == "__main__":
    main()
