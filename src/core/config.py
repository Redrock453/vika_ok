"""Configuration loader for Vika_Ok."""
import os
import logging
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

        # Models
        self.model_do: str = os.getenv("MODEL_DO", "openai-gpt-oss-120b")
        self.model_groq: str = os.getenv("MODEL_FAST", "llama-3.3-70b-versatile")
        self.model_gemini: str = os.getenv("MODEL_GEMINI", "gemini-1.5-pro")

        # Qdrant
        self.qdrant_host: str = os.getenv("QDRANT_HOST", "vika_qdrant")
        self.qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
        self.qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "vika_knowledge")

        # Paths
        self.history_file: str = os.getenv("HISTORY_FILE", "/app/history.json")
        self.tasks_file: str = os.getenv("TASKS_FILE", "/app/tasks.json")
        self.log_file: str = os.getenv("LOG_FILE", "/app/bot.log")
        self.audio_temp_dir: str = os.getenv("AUDIO_TEMP_DIR", "/tmp/vika_audio")

        # Limits
        self.max_history: int = int(os.getenv("MAX_HISTORY", "30"))
        self.max_history_storage: int = int(os.getenv("MAX_HISTORY_STORAGE", "60"))
        self.web_search_timeout: int = int(os.getenv("WEB_SEARCH_TIMEOUT", "15"))

        # Retry config
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delays: list[int] = self._parse_delays(os.getenv("RETRY_DELAYS", "1,3,5"))

        # Rate limiting
        self.rate_limit: int = int(os.getenv("RATE_LIMIT", "5"))
        self.rate_limit_period: int = int(os.getenv("RATE_LIMIT_PERIOD", "1"))

        # Create temp directories
        Path(self.audio_temp_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parse_ids(raw: str) -> list[int]:
        """Parse comma-separated IDs, ignoring empty values."""
        return [int(x.strip()) for x in raw.split(",") if x.strip() and x.strip().isdigit()]

    @staticmethod
    def _parse_delays(raw: str) -> list[int]:
        """Parse comma-separated retry delays."""
        try:
            return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        except Exception:
            return [1, 3, 5]

    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration and return (is_valid, errors)."""
        errors = []

        if not self.telegram_token:
            errors.append("TELEGRAM_BOT_TOKEN не установлен")
        if not self.allowed_ids:
            errors.append("ALLOWED_IDS не установлен или пустой")
        if not self.do_api_key and not self.groq_api_key and not self.gemini_api_key:
            errors.append("Ни один LLM провайдер не настроен (DO_AI_API_KEY, GROQ_API_KEY, GEMINI_API_KEY)")

        return len(errors) == 0, errors


config = Config()
