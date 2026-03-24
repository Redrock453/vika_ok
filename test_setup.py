#!/usr/bin/env python3
"""
🧪 ТЕСТ НАСТРОЙКИ И СВЯЗИ
Проверяет все API ключи и компоненты
"""
import os
import sys
from dotenv import load_dotenv

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_env():
    """Проверка .env файла"""
    print_section("1. ENVIRONMENT VARIABLES")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(BASE_DIR, '.env')

    if not os.path.exists(env_file):
        print("❌ .env файл не найден!")
        print(f"   Создай его: cp .env.example .env")
        return False

    load_dotenv(env_file)

    checks = []
    checks.append(("GEMINI_API_KEY", os.getenv('GEMINI_API_KEY') is not None))
    checks.append(("GROQ_API_KEY", os.getenv('GROQ_API_KEY') is not None))
    checks.append(("OPENROUTER_API_KEY", os.getenv('OPENROUTER_API_KEY') is not None))
    checks.append(("TELEGRAM_BOT_TOKEN", os.getenv('TELEGRAM_BOT_TOKEN') is not None))
    checks.append(("QDRANT_URL", os.getenv('QDRANT_URL') is not None))

    for name, found in checks:
        status = "✅" if found else "❌"
        print(f"{status} {name}: {'***' if found else 'NOT SET'}")

    return all(found for _, found in checks)

def test_gemini():
    """Тест Gemini API"""
    print_section("2. GEMINI API TEST")
    try:
        import google.generativeai as genai

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY не установлен")
            return False

        genai.configure(api_key=api_key)
        print("✅ Gemini configured")

        # Список моделей
        try:
            models = genai.list_models()
            gemini_models = [m.name for m in models if 'generateContent' in m.name]
            print(f"✅ Available models: {len(gemini_models)}")
            # Показываем первые несколько
            for m in gemini_models[:5]:
                print(f"   - {m}")
        except Exception as e:
            print(f"⚠️  Could not list models: {e}")

        # Простой запрос
        print("✅ Testing connection...")
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Привет! Напиши 'тест успешно'")
        print(f"✅ Gemini works: {response.text[:50]}...")

        return True

    except ImportError:
        print("❌ google-generativeai не установлен")
        return False
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return False

def test_groq():
    """Тест Groq API"""
    print_section("3. GROQ API TEST")
    try:
        from openai import OpenAI

        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("❌ GROQ_API_KEY не установлен")
            return False

        client = OpenAI(base_url='https://api.groq.com/openai/v1', api_key=api_key)
        print("✅ Groq client configured")

        # Простой запрос
        print("✅ Testing connection...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Привет! Напиши 'тест успешно'"}]
        )
        print(f"✅ Groq works: {response.choices[0].message.content[:50]}...")

        return True

    except ImportError:
        print("❌ openai package not installed")
        return False
    except Exception as e:
        print(f"❌ Groq error: {e}")
        return False

def test_qdrant():
    """Тест Qdrant"""
    print_section("4. QDRANT TEST")
    try:
        from qdrant_client import QdrantClient

        url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        print(f"Connecting to {url}...")

        client = QdrantClient(url=url)
        print("✅ Qdrant connected")

        # Проверка коллекции
        collection_name = "vika_knowledge"
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if collection_name in collection_names:
            print(f"✅ Collection '{collection_name}' exists")
        else:
            print(f"⚠️  Collection '{collection_name}' not found")
            print("   Create it: python init_qdrant.py")

        return True

    except ImportError:
        print("❌ qdrant-client not installed")
        return False
    except Exception as e:
        print(f"⚠️  Qdrant error: {e}")
        print("   Qdrant не обязателен, это опционально")
        return True

def main():
    print("\n🧪 VIKA OK SETUP TEST")
    print("="*60)

    # Проверка env
    env_ok = check_env()

    # Тесты
    gemini_ok = test_gemini()
    groq_ok = test_groq()
    qdrant_ok = test_qdrant()

    # Итог
    print_section("FINAL RESULTS")

    all_ok = env_ok and gemini_ok and groq_ok and qdrant_ok

    if all_ok:
        print("✅ ALL TESTS PASSED!")
        print("\n🚀 Запуск бота:")
        print("   python telegram_bot.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nПроверьте:")
        print("1. API ключи в .env")
        print("2. Установите пакеты: pip install -r requirements.txt")
        print("3. Проверьте доступность сервисов")

    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
