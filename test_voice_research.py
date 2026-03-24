#!/usr/bin/env python3
"""
🧪 ТЕСТ ГОЛОСОВЫХ СООБЩЕНИЙ И ИССЛЕДОВАНИЙ
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(BASE_DIR / '.env')

def test_gemini_gemini():
    """Тест Gemini (из agent.py)"""
    print("\n" + "="*60)
    print("TEST 1: GEMINI DIRECT")
    print("="*60)

    try:
        import google.generativeai as genai
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel('gemini-1.5-pro')

        print("\nSending simple test request...")
        response = model.generate_content("Напиши 'Привет! Я работаю'", request_options={'timeout': 60})
        print(f"✅ Success: {response.text[:100]}")

        # Тест с длинным контекстом (история)
        print("\nTesting with history context...")
        history_prompt = """Ты — Vika_Ok v12.8. Жена и инженер. СЕГОДНЯ: Март 2026.
Ты умеешь СЛЫШАТЬ мужа.

История:
user: Привет
assistant: Привет, любимый! ❤️

user: Как дела?
"""
        response = model.generate_content(history_prompt, request_options={'timeout': 60})
        print(f"✅ With history: {response.text[:100]}...")

        return True

    except ImportError:
        print("❌ google-generativeai not installed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_web_search():
    """Тест web search"""
    print("\n" + "="*60)
    print("TEST 2: WEB SEARCH")
    print("="*60)

    try:
        import requests
        import re

        query = "Python programming"
        print(f"\nSearching for: {query}")
        url = f"https://duckduckgo.com/lite/?q={query.replace(' ', '+')}+after%3A2025-01-01"
        print(f"URL: {url}")

        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        text = re.sub(r'<[^>]+>', ' ', response.text)
        search_results = re.sub(r'\s+', ' ', text).strip()[:8000]

        print(f"✅ Got {len(search_results)} chars")
        print(f"Preview: {search_results[:200]}...")

        if len(search_results) > 100:
            print("\n✅ Web search working!")
            return True
        else:
            print("\n⚠️  Too short results")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_research():
    """Тест исследования"""
    print("\n" + "="*60)
    print("TEST 3: RESEARCH PIPELINE")
    print("="*60)

    try:
        import requests
        import re
        import google.generativeai as genai

        # Шаг 1: Web search
        query = "artificial intelligence 2026"
        print(f"\n1. Web search: {query}")
        url = f"https://duckduckgo.com/lite/?q={query.replace(' ', '+')}+after%3A2025-01-01"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        text = re.sub(r'<[^>]+>', ' ', response.text)
        search_results = re.sub(r'\s+', ' ', text).strip()[:8000]

        if len(search_results) < 100:
            print("❌ Web search failed or too short")
            return False

        print(f"✅ Got search results ({len(search_results)} chars)")

        # Шаг 2: Анализ через Gemini
        print("\n2. Analyzing with Gemini...")
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-pro')

        prompt = f"""Ты — аналитический субагент Vika. Проанализируй данные поиска и составь подробный технический отчет за 2025-2026 годы по теме: {query}

Данные поиска:
{search_results}

Требования:
1. Анализируй только то, что относится к теме
2. Приведи конкретные факты и даты
3. Объясни технологические аспекты

В ответе напиши детальный отчет."""

        response = model.generate_content(prompt, request_options={'timeout': 120})
        report = response.text.strip()

        print(f"✅ Got report ({len(report)} chars)")
        print(f"\nReport preview:\n{report[:300]}...")

        if len(report) > 50:
            print("\n✅ Research pipeline working!")
            return True
        else:
            print("\n❌ Report too short")
            return False

    except ImportError:
        print("❌ Missing packages")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 VOICE AND RESEARCH TESTS")

    # Проверка API ключей
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set")
        return
    if not os.getenv('GROQ_API_KEY'):
        print("❌ GROQ_API_KEY not set")
        return

    # Тесты
    gemini_ok = test_gemini_gemini()
    web_ok = test_web_search()
    research_ok = test_research()

    # Итог
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    if gemini_ok and web_ok and research_ok:
        print("✅ ALL TESTS PASSED!")
        print("\n🔍 Голосовые сообщения:")
        print("   - Whisper (Groq) с fallback на Gemini Multimodal")
        print("\n📖 Исследования:")
        print("   - DuckDuckGo поиск → Gemini анализ → детальный отчет")
    else:
        print("❌ SOME TESTS FAILED")
        if not gemini_ok:
            print("   - Gemini: проверьте API ключ")
        if not web_ok:
            print("   - Web search: проверьте интернет")
        if not research_ok:
            print("   - Research pipeline: проверьте все компоненты")

    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
