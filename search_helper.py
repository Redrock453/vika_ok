"""
Улучшенный поиск без капчи
"""
import requests
import re
from typing import Optional
from urllib.parse import quote

def search_google(query: str, num_results: int = 10) -> str:
    """
    Поиск через Google Custom Search API (если ключ есть)
    Или через DDG без капчи
    """
    # Попробуем Google если ключ есть
    cse_key = __import__('os').environ.get('GOOGLE_CSE_KEY')
    cse_id = __import__('os').environ.get('GOOGLE_CSE_ID')

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

    # Fallback через DuckDuckGo с headers
    try:
        url = "https://duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        params = {
            'q': query,
            'kl': 'wt-wt',  # worldwide
            'k7': 'search'
        }

        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, params=params, timeout=15, allow_redirects=True)

        if response.status_code == 200:
            # Парсим HTML
            text = response.text
            # Извлекаем текст между тегами a с классом result__a или __link
            links = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]*)"[^>]*><h3 class="result__a-title"><span class="result__a-title-text">([^<]*)</span>', text)

            results = []
            for url, title in links:
                # Парсим URL для получения сниппета
                snippet_url = f"https://duckduckgo.com/html/?q={quote(url)}"
                try:
                    snippet_resp = requests.get(snippet_url, headers=headers, timeout=10, allow_redirects=True)
                    if snippet_resp.status_code == 200:
                        snippet_text = re.sub(r'<[^>]+>', ' ', snippet_resp.text)
                        snippet_text = re.sub(r'\s+', ' ', snippet_text).strip()
                        if len(snippet_text) > 50:
                            results.append(f"{title}\nURL: {url}\nPreview: {snippet_text[:200]}...")
                except:
                    results.append(f"{title}\nURL: {url}")

            if results:
                return '\n\n'.join(results)

            # Если ничего не нашли, вернем текст страницы
            text = re.sub(r'<[^>]+>', ' ', text)
            return re.sub(r'\s+', ' ', text).strip()[:8000]

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
