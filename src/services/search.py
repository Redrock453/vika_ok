"""Web search via DuckDuckGo."""
import logging
import re

import requests

from src.core.config import config

logger = logging.getLogger("vika.search")


def web_search(query: str) -> str:
    """Search DuckDuckGo and return cleaned text."""
    try:
        url = f"https://duckduckgo.com/lite/?q={query.replace(' ', '+')}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=config.web_search_timeout)
        text = re.sub(r"<[^>]+>", " ", r.text)
        return re.sub(r"\s+", " ", text).strip()[:5000]
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"❌ Помилка пошуку: {e}"
