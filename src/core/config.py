"""Configuration loader for Vika_Ok."""
import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Centralized configuration with defaults."""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        load_dotenv(self.base_dir / ".env")

        # Telegram
        self.telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.allowed_ids: list[int] = self._parse_ids(os.getenv("ALLOWED_IDS", ""))
        self.admin_id: int = self.allowed_ids[0] if self.allowed_ids else 0

        # LLM providers
        self.do_api_key: str = os.getenv("DO_AI_API_KEY", "")
        self.do_base_url: str = os.getenv("DO_AI_BASE_URL", "https://iogg7m5bbddipu56tacil5yn.agents.do-ai.run/api/v1")
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

        # Qdrant
        self.qdrant_host: str = os.getenv("QDRANT_HOST", "100.68.33.14")
        self.qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))

        # Paths
        self.history_file: str = os.getenv("HISTORY_FILE", "/app/history.json")
        self.tasks_file: str = os.getenv("TASKS_FILE", "/app/tasks.json")

        # Limits
        self.max_history: int = int(os.getenv("MAX_HISTORY", "30"))
        self.web_search_timeout: int = int(os.getenv("WEB_SEARCH_TIMEOUT", "15"))

    @staticmethod
    def _parse_ids(raw: str) -> list[int]:
        return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


config = Config()
