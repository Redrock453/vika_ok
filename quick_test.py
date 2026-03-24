#!/usr/bin/env python3
"""
🧪 QUICK TEST - Весь функционал в одном скрипте
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')

print("="*70)
print("🧪 VIKA v12.9 QUICK TEST")
print("="*70)

results = []

# Test 1: API Keys
print("\n1️⃣ CHECKING API KEYS")
print("-" * 70)
gemini_key = os.getenv('GEMINI_API_KEY')
groq_key = os.getenv('GROQ_API_KEY')
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')

results.append(("GEMINI_API_KEY", gemini_key is not None))
results.append(("GROQ_API_KEY", groq_key is not None))
results.append(("TELEGRAM_BOT_TOKEN", telegram_token is not None))

for name, ok in results:
    print(f"   {'✅' if ok else '❌'} {name}")

# Test 2: Gemini
print("\n2️⃣ TESTING GEMINI API")
print("-" * 70)
try:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content("Напиши 'Привет! Работает'", request_options={'timeout': 60})
    print(f"   ✅ Gemini работает: {response.text[:50]}...")
    results.append(("GEMINI_DIRECT", True))
except Exception as e:
    print(f"   ❌ Gemini ошибка: {e}")
    results.append(("GEMINI_DIRECT", False))

# Test 3: Groq
print("\n3️⃣ TESTING GROQ API")
print("-" * 70)
try:
    from openai import OpenAI
    client = OpenAI(base_url='https://api.groq.com/openai/v1', api_key=groq_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Напиши 'Привет! Работает'"}],
        timeout=30
    )
    print(f"   ✅ Groq работает: {response.choices[0].message.content[:50]}...")
    results.append(("GROQ_DIRECT", True))
except Exception as e:
    print(f"   ❌ Groq ошибка: {e}")
    results.append(("GROQ_DIRECT", False))

# Test 4: Research
print("\n4️⃣ TESTING RESEARCH")
print("-" * 70)
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("research_helper", "improved_research.py")
    research_helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(research_helper)

    print("   Запуск исследования...")
    report = research_helper.research("Python programming")
    if report and len(report) > 50:
        print(f"   ✅ Исследование работает!")
        print(f"   Длина отчета: {len(report)} символов")
        print(f"   Превью: {report[:150]}...")
        results.append(("RESEARCH", True))
    else:
        print(f"   ❌ Исследование слишком короткое")
        results.append(("RESEARCH", False))
except Exception as e:
    print(f"   ❌ Исследование ошибка: {e}")
    results.append(("RESEARCH", False))

# Test 5: Agent
print("\n5️⃣ TESTING AGENT")
print("-" * 70)
try:
    from agent import VikaOk
    vika = VikaOk()

    status = vika.ask('статус')
    print(f"   ✅ Агент работает!")
    print(f"   Статус:\n{status}")

    # Тест исследования через агента
    print("\n   Тест исследования через агента...")
    report = vika.research("artificial intelligence")
    if report and len(report) > 100:
        print(f"   ✅ Исследование через агента работает!")
        print(f"   Длина отчета: {len(report)} символов")
        results.append(("AGENT_RESEARCH", True))
    else:
        print(f"   ❌ Исследование через агента слишком короткое")
        results.append(("AGENT_RESEARCH", False))
except Exception as e:
    print(f"   ❌ Агент ошибка: {e}")
    import traceback
    traceback.print_exc()
    results.append(("AGENT", False))

# Final
print("\n" + "="*70)
print("📋 RESULTS")
print("="*70)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"Passed: {passed}/{total}")

if passed == total:
    print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    print("\n🚀 ЗАПУСК БОТА:")
    print("   python telegram_bot.py")
else:
    print(f"\n⚠️  {total - passed} test(s) failed")
    print("\nПроверьте:")
    print("1. API ключи в .env")
    print("2. Интернет-соединение")
    print("3. Нет конфликтов с другими процессами")

print("\n" + "="*70 + "\n")
