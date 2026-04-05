"""
Улучшенный поиск через duckduckgo-search library
"""
import os
import requests
from typing import Optional
from urllib.parse import quote

def search_google(query: str, num_results: int = 10) -> str:
    """
    Поиск через Google Custom Search API (если ключ есть)
    Или через DuckDuckGo через библиотеку
    """
    cse_key = os.environ.get('GOOGLE_CSE_KEY')
    cse_id = os.environ.get('GOOGLE_CSE_ID')

    if cse_key and cse_id:
        try:
            url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                'key': cse_key,
                'cx': cse_id,
                'q': query,
                'num': num_results,
                'lr': 'lang_ru'
            }
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    return '\n'.join([item['snippet'] for item in data['items']])
        except Exception as e:
            print(f"[!] Google CSE error: {e}")

    # Fallback через duckduckgo-search library
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
        if results:
            return '\n\n'.join([
                f"{r['title']}\n{r['href']}\n{r['body'][:200]}"
                for r in results
            ])
    except ImportError:
        print("[!] duckduckgo-search не установлен. pip install duckduckgo-search")
    except Exception as e:
        print(f"[!] DuckDuckGo error: {e}")

    return f"Ошибка поиска: {query}"


def get_search_results(query: str) -> Optional[str]:
    """
    Получить результаты поиска с обработкой ошибок
    """
    try:
        results = search_google(query)
        if len(results) < 100:
            return f"Поиск {query}: слишком короткие результаты"
        return results
    except Exception as e:
        print(f"[!] Search error: {e}")
        return f"Ошибка поиска: {e}"


if __name__ == '__main__':
    # Тест
    query = "artificial intelligence"
    results = get_search_results(query)
    print(f"\nQuery: {query}\n")
    print(results[:1000] if len(results) > 1000 else results)
