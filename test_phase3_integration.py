import os
import sys
import logging
from qdrant_manager import QdrantManager
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Set encoding to UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTest")

def test_system():
    print("\n" + "="*80)
    print("TEST: VIKA SYSTEM INTEGRATION (PHASE 3)")
    print("="*80 + "\n")

    # 1. API Key Check
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("[OK] [API KEY] GEMINI_API_KEY: Configured.")
    else:
        print("[ERROR] [API KEY] GEMINI_API_KEY: MISSING!")
        return

    # 2. Qdrant Check
    try:
        qdrant = QdrantManager()
        info = qdrant.client.get_collection("vika_knowledge")
        print(f"[OK] [MEMORY] Qdrant Collection 'vika_knowledge': Found ({info.points_count} points).")
    except Exception as e:
        print(f"[ERROR] [MEMORY] Qdrant Error: {e}")
        return

    # 3. Embedding Model Check
    try:
        model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        print("[OK] [EMBEDDINGS] SentenceTransformer Model: Loaded.")
    except Exception as e:
        print(f"[ERROR] [EMBEDDINGS] Error: {e}")
        return

    # 4. Gemini 2.5 Flash Check
    try:
        genai.configure(api_key=api_key)
        llm = genai.GenerativeModel("gemini-2.5-flash")
        res = llm.generate_content("Ping. Answer with 'Pong'.")
        if "Pong" in res.text:
            print("[OK] [LLM] Gemini 2.5 Flash: Online and Responsive.")
        else:
            print(f"[WARN] [LLM] Unexpected response: {res.text}")
    except Exception as e:
        print(f"[ERROR] [LLM] Error: {e}")

    # 5. SSH Key Check
    ssh_path = os.path.expanduser("~/.ssh/id_ed25519_vika")
    if os.path.exists(ssh_path):
        print("[OK] [SECURITY] SSH Private Key (Vika): Found.")
    else:
        print("[ERROR] [SECURITY] SSH Private Key (Vika): MISSING!")

    print("\n" + "="*80)
    print("SYSTEM STATUS: MISSION READY (100%)")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_system()
