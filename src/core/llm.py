"""LLM provider clients with retry + fallback chain."""
import logging
import time
from typing import Optional

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
        self.chain = [
            ("do", self._call_do),
            ("groq", self._call_groq),
            ("gemini", self._call_gemini),
        ]

    def _init_do(self):
        if not config.do_api_key:
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
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-pro")
            logger.info("Gemini initialized")
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    def _call_do(self, messages: list[dict]) -> Optional[str]:
        if not self.do_client:
            return None
        resp = self.do_client.chat.completions.create(
            model="openai-gpt-oss-120b",
            messages=messages,
        )
        return resp.choices[0].message.content

    def _call_groq(self, messages: list[dict]) -> Optional[str]:
        if not self.groq_client:
            return None
        resp = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
        )
        return resp.choices[0].message.content

    def _call_gemini(self, messages: list[dict]) -> Optional[str]:
        if not self.gemini_model:
            return None
        # Flatten messages to single prompt for Gemini
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        res = self.gemini_model.generate_content(prompt, request_options={"timeout": 90})
        return res.text.strip()

    def ask(self, messages: list[dict]) -> str:
        """Try each provider in chain with retries."""
        for name, caller in self.chain:
            for attempt in range(MAX_RETRIES):
                try:
                    result = caller(messages)
                    if result:
                        return result
                except Exception as e:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(f"[{name}] attempt {attempt+1}/{MAX_RETRIES} failed: {e}, retry in {delay}s")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(delay)
            logger.error(f"[{name}] all retries exhausted, falling back")

        return "❌ Всі провайдери недоступні. Спробуй пізніше."

    def transcribe_audio(self, file_path: str) -> Optional[str]:
        """Transcribe audio via Groq Whisper."""
        if not self.groq_client:
            return None
        with open(file_path, "rb") as f:
            result = self.groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                response_format="text",
            )
        return result.text.strip() if hasattr(result, "text") else str(result)
