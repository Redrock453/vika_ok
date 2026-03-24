"""
Улучшенное исследование через Groq с интернет-поиском
"""
import os
import requests
from pathlib import Path
from typing import Optional
from openai import OpenAI

# Загрузка .env
BASE_DIR = Path(__file__).parent.absolute()
if (BASE_DIR / '.env').exists():
    import dotenv
    dotenv.load_dotenv(BASE_DIR / '.env')

def search_web(query: str) -> str:
    """Поиск через Serper.dev или DuckDuckGo с обработкой"""
    try:
        # Пробуем Serper (если есть ключ)
        serper_key = os.getenv('SERPER_API_KEY')
        if serper_key:
            url = "https://google.serper.dev/search"
            headers = {'X-API-KEY': serper_key, 'Content-Type': 'application/json'}
            data = {'q': query}
            response = requests.post(url, headers=headers, json=data, timeout=15)

            if response.status_code == 200:
                results = response.json()
                if 'organic' in results and len(results['organic']) > 0:
                    # Собираем сниппеты
                    snippets = []
                    for item in results['organic'][:10]:
                        title = item.get('title', '')
                        link = item.get('link', '')
                        snippet = item.get('snippet', '')
                        if snippet:
                            snippets.append(f"{title}\nURL: {link}\n{snippet}")
                    return '\n\n'.join(snippets)
    except Exception as e:
        print(f"[!] Serper error: {e}")

        # Fallback через DDG (без капчи)
        try:
            url = "https://duckduckgo.com/html/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
            }

            params = {'q': query, 'kl': 'wt-wt'}

            session = requests.Session()
            session.headers.update(headers)
            response = session.get(url, params=params, timeout=15, allow_redirects=True)

            if response.status_code == 200:
                # Извлекаем заголовки результатов
                import re
                links = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]*)"[^>]*><h3[^>]*><span[^>]*>([^<]*)</span>', response.text)

                if links:
                    snippets = []
                    for url, title in links[:10]:
                        snippets.append(f"{title}\nURL: {url}")
                    return '\n\n'.join(snippets)

                # Если нет ссылок, вернем текст страницы
                text = re.sub(r'<[^>]+>', ' ', response.text)
                text = re.sub(r'\s+', ' ', text).strip()[:5000]
                return text
        except Exception as e:
            print(f"[!] DuckDuckGo error: {e}")

    except Exception as e:
        print(f"[!] Search error: {e}")

    return f"Поиск {query}: результаты ограничены (нет доступа к интернету)"


def research_with_llm(query: str, llm_client: OpenAI) -> str:
    """
    Исследование через LLM с интернет-поиском (один запрос к Groq)
    """
    print(f"[INFO] Researching: {query}")

    # Шаг 1: Получаем результаты поиска
    search_results = search_web(query)

    if "результаты ограничены" in search_results or "нет доступа" in search_results:
        # Fallback: делаем запрос напрямую к Groq
        print("[INFO] Using direct LLM call instead of web search")
        prompt = f"""Ты — аналитический субагент Vika. Твоя задача — проанализировать тему: {query}

Сформируй подробный технический отчет за 2025-2026 годы.

Требования:
1. Будь аналитиком — не просто перечисляй, а объясняй
2. Приведи конкретные факты, даты, цифры
3. Если нет данных, честно напиши "нет информации"
4. Структурируй отчет: введение, ключевые моменты, выводы

Напиши детальный отчет."""

        response = llm_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Ты — аналитический субагент Vika. Пиши детальные технические отчеты."},
                       {"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=120
        )
        return response.choices[0].message.content

    # Шаг 2: Анализируем через LLM с учетом результатов поиска
    prompt = f"""Ты — аналитический субагент Vika. Проанализируй тему: {query}

РЕЗУЛЬТАТЫ ПОИСКА:
{search_results}

Твоя задача:
1. Проанализируй и обобщи найденную информацию
2. Выдели ключевые факты и даты
3. Объясни технологические аспекты
4. Если информации мало, честно скажи об этом
5. Приведи свой вывод

Напиши детальный технический отчет за 2025-2026 годы."""

    response = llm_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "Ты — аналитический субагент Vika. Пиши подробные технические отчеты."},
                   {"role": "user", "content": prompt}],
        temperature=0.7,
        timeout=120
    )
    return response.choices[0].message.content


def research(query: str) -> str:
    """Улучшенное исследование"""
    try:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            return "❌ GROQ_API_KEY не установлен"
        print(f"[INFO] Using Groq API for research")
        llm_client = OpenAI(base_url='https://api.groq.com/openai/v1', api_key=api_key)
        return research_with_llm(query, llm_client)
    except Exception as e:
        print(f"[!] Research error: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Ошибка исследования: {e}"


if __name__ == '__main__':
    # Тест
    query = "artificial intelligence"
    report = research(query)
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    print(report)
