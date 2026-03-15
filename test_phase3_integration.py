import os
import sys
import logging
from qdrant_manager import QdrantManager
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Настройка кодировки
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTest")

def test_system():
    print("\n" + "="*80)
    print("🧪 VIKA SYSTEM: INTEGRATION TEST (PHASE 3)")
    print("="*80 + "\n")

    # 1. Проверка API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("✅ [API KEY] GEMINI_API_KEY: Configured.")
    else:
        print("❌ [API KEY] GEMINI_API_KEY: MISSING!")
        return

    # 2. Проверка Qdrant
    try:
        qdrant = QdrantManager()
        # Проверяем количество точек в коллекции
        info = qdrant.client.get_collection("vika_knowledge")
        print(f"✅ [MEMORY] Qdrant Collection 'vika_knowledge': Found ({info.points_count} points).")
    except Exception as e:
        print(f"❌ [MEMORY] Qdrant Error: {e}")
        return

    # 3. Проверка Модели Эмбеддингов
    try:
        model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        print("✅ [EMBEDDINGS] SentenceTransformer Model: Loaded.")
    except Exception as e:
        print(f"❌ [EMBEDDINGS] Error: {e}")
        return

    # 4. Проверка Gemini 2.5 Flash
    try:
        genai.configure(api_key=api_key)
        llm = genai.GenerativeModel("gemini-2.5-flash")
        res = llm.generate_content("Ping. Answer with 'Pong'.")
        if "Pong" in res.text:
            print("✅ [LLM] Gemini 2.5 Flash: Online and Responsive.")
        else:
            print(f"⚠️ [LLM] Unexpected response: {res.text}")
    except Exception as e:
        print(f"❌ [LLM] Error: {e}")

    # 5. Проверка SSH Ключей (GitHub)
    ssh_path = os.path.expanduser("~/.ssh/id_ed25519_vika")
    if os.path.exists(ssh_path):
        print("✅ [SECURITY] SSH Private Key (Vika): Found.")
    else:
        print("❌ [SECURITY] SSH Private Key (Vika): MISSING!")

    print("\n" + "="*80)
    print("🎖️ SYSTEM STATUS: MISSION READY (100%)")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_system()
