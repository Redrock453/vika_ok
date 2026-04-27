"""LLM provider clients with retry + fallback chain."""
import logging
import time
from typing import Optional, Callable, List, Dict

from openai import OpenAI

from src.core.config import config

logger = logging.getLogger("vika.llm")

MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 5]


class LLMProvider:
    """Manages LLM clients with automatic retry and fallback."""

    def __init__(self):
        self.do_client: Optional[OpenAI] = None
        self.groq_client: Optional[OpenAI] = None
        self.gemini_model = None

        self._init_do()
        self._init_groq()
        self._init_gemini()

        # Fallback chain: DO → Groq → Gemini
        self.chain: List[tuple[str, Callable]] = [
            ("do", self._call_do),
            ("groq", self._call_groq),
            ("gemini", self._call_gemini),
        ]

    def _init_do(self):
        if not config.do_api_key:
            logger.info("DO Agent: API key not set, skipping")
            return
        try:
            self.do_client = OpenAI(
                base_url=config.do_base_url,
                api_key=config.do_api_key,
            )
            logger.info("DO Agent initialized")
        except Exception as e:
            logger.warning(f"DO init failed: {e}")

    def _init_groq(self):
        if not config.groq_api_key:
            logger.info("Groq: API key not set, skipping")
            return
        try:
            self.groq_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=config.groq_api_key,
            )
            logger.info("Groq initialized")
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")

    def _init_gemini(self):
        if not config.gemini_api_key:
            logger.info("Gemini: API key not set, skipping")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(config.model_gemini)
            logger.info("Gemini initialized")
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    def _call_do(self, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.do_client:
            return None
        resp = self.do_client.chat.completions.create(
            model=config.model_do,
            messages=messages,
        )
        return resp.choices[0].message.content

    def _call_groq(self, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.groq_client:
            return None
        resp = self.groq_client.chat.completions.create(
            model=config.model_groq,
            messages=messages,
        )
        return resp.choices[0].message.content

    def _call_gemini(self, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.gemini_model:
            return None
        # Flatten messages to single prompt for Gemini
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        res = self.gemini_model.generate_content(prompt, request_options={"timeout": 90})
        return res.text.strip()

    def ask(self, messages: List[Dict[str, str]]) -> str:
        """Try each provider in chain with retries."""
        for name, caller in self.chain:
            for attempt in range(config.max_retries):
                try:
                    result = caller(messages)
                    if result:
                        logger.info(f"Response from {name} (attempt {attempt + 1})")
                        return result
                except Exception as e:
                    delay = config.retry_delays[min(attempt, len(config.retry_delays) - 1)]
                    logger.warning(f"[{name}] attempt {attempt+1}/{config.max_retries} failed: {e}, retry in {delay}s")
                    if attempt < config.max_retries - 1:
                        time.sleep(delay)
            logger.error(f"[{name}] all retries exhausted, falling back")

        return "❌ Всі провайдери недоступні. Спробуй пізніше."

    def transcribe_audio(self, file_path: str) -> Optional[str]:
        """Transcribe audio via Groq Whisper."""
        if not self.groq_client:
            logger.warning("Groq client not available for transcription")
            return None
        try:
            with open(file_path, "rb") as f:
                result = self.groq_client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=f,
                    response_format="text",
                )
            return result.text.strip() if hasattr(result, 'text') else str(result)
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return None
